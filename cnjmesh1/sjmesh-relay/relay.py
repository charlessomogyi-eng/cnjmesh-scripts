#!/usr/bin/env python3
"""
SJMesh <-> local broker relay (CentralNJ only).

INBOUND (always on): subscribes to SJMesh's broker for CentralNJ topics, drops
known bad nodes' packets and echoes of our own gateways, republishes the rest
to the local broker. Replaces the native Mosquitto sjmesh bridge (kept
permanently disabled; never re-enable it while this service runs).

OUTBOUND (opt-in, OUTBOUND_ENABLED=1): subscribes to the local broker and
publishes ONLY packets uploaded by our own gateways (OUTBOUND_GATEWAYS) to
SJMesh's broker, on the same topic. Loop safety: (1) only our gateways' topics
go out; (2) the inbound side drops any topic from our gateways, so the echo
SJMesh's broker sends back to our own subscription cannot re-enter the local
broker and be sent out again; (3) a per-minute cap and kill switch.
Design notes: docs/mqtt-topology-and-landmines.md section 5.
"""
import collections
import os
import logging
import threading
import time
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("sjmesh-relay")

HEARTBEAT_FILE = "/opt/sjmesh-relay/heartbeat"
HEARTBEAT_INTERVAL_SECONDS = 60

SUBSCRIBE_TOPICS = [
    ("msh/US/2/e/CentralNJ/#", 0),
    ("msh/US/NJ/2/e/CentralNJ/#", 0),
]

# Local topics the outbound side listens to (one topic level = a gateway id).
LOCAL_OUTBOUND_TOPICS = [
    ("msh/US/2/e/CentralNJ/+", 0),
    ("msh/US/NJ/2/e/CentralNJ/+", 0),
]

BLOCKED_TOPICS = {
    "msh/US/2/e/CentralNJ/!699a9390",
    "msh/US/NJ/2/e/CentralNJ/!699a9390",
    "msh/US/2/e/CentralNJ/!698574b0",
    "msh/US/NJ/2/e/CentralNJ/!698574b0",
    "msh/US/2/e/CentralNJ/!db51bb30",
    "msh/US/NJ/2/e/CentralNJ/!db51bb30",
}

# Our own gateways: CJG2, KPN6, CJG1. Override with OUTBOUND_GATEWAYS.
DEFAULT_OUR_GATEWAYS = "!9ea3e8d4,!69841fe0,!0aca423c"
OUR_GATEWAYS = {
    g.strip()
    for g in os.environ.get("OUTBOUND_GATEWAYS", DEFAULT_OUR_GATEWAYS).split(",")
    if g.strip()
}
OUTBOUND_ENABLED = os.environ.get("OUTBOUND_ENABLED", "0") == "1"
OUTBOUND_MAX_PER_MINUTE = int(os.environ.get("OUTBOUND_MAX_PER_MINUTE", "120"))

CENTRALNJ_PREFIXES = ("msh/US/2/e/CentralNJ/", "msh/US/NJ/2/e/CentralNJ/")


def gateway_of(topic):
    """Last topic level, e.g. '!9ea3e8d4'."""
    return topic.rsplit("/", 1)[-1]


def is_ours(topic):
    """True for a CentralNJ packet topic published by one of our gateways."""
    return topic.startswith(CENTRALNJ_PREFIXES) and gateway_of(topic) in OUR_GATEWAYS


def should_forward_outbound(topic):
    """Outbound filter: ours, and not blocked."""
    return is_ours(topic) and topic not in BLOCKED_TOPICS


class RateLimiter:
    def __init__(self, max_per_minute, clock=time.monotonic):
        self.max = max_per_minute
        self.clock = clock
        self.stamps = collections.deque()

    def allow(self):
        now = self.clock()
        while self.stamps and now - self.stamps[0] > 60:
            self.stamps.popleft()
        if len(self.stamps) >= self.max:
            return False
        self.stamps.append(now)
        return True


class Relay:
    def __init__(self, local_client, remote_client, limiter=None):
        self.local = local_client
        self.remote = remote_client
        self.limiter = limiter or RateLimiter(OUTBOUND_MAX_PER_MINUTE)
        self.blocked_count = 0
        self.relayed_count = 0
        self.echo_count = 0
        self.outbound_count = 0
        self.outbound_dropped = 0

    # ---- inbound: SJMesh -> local ----
    def on_remote_message(self, client, userdata, msg):
        if msg.topic in BLOCKED_TOPICS:
            self.blocked_count += 1
            if self.blocked_count % 100 == 1:
                log.info("Blocked bad-node packet #%d on %s", self.blocked_count, msg.topic)
            return
        if is_ours(msg.topic):
            # Our own packet coming back from SJMesh's broker. Never republish
            # it locally: that is what would close a loop with the outbound side.
            # It also proves their broker accepted our publish.
            self.echo_count += 1
            if self.echo_count % 50 == 1:
                log.info("SJMesh broker echoed our packet #%d (publish accepted): %s",
                         self.echo_count, msg.topic)
            return
        self.local.publish(msg.topic, msg.payload, qos=msg.qos, retain=msg.retain)
        self.relayed_count += 1
        if self.relayed_count % 500 == 1:
            log.info("Relayed packet #%d (last topic: %s)", self.relayed_count, msg.topic)

    # ---- outbound: local -> SJMesh (our gateways only) ----
    def on_local_message(self, client, userdata, msg):
        if not OUTBOUND_ENABLED:
            return
        if not should_forward_outbound(msg.topic):
            return
        if not self.limiter.allow():
            self.outbound_dropped += 1
            if self.outbound_dropped % 20 == 1:
                log.warning("Outbound rate cap hit; dropped #%d (cap %d/min)",
                            self.outbound_dropped, OUTBOUND_MAX_PER_MINUTE)
            return
        # retain is always False outbound, so nothing sticky lands on their broker.
        self.remote.publish(msg.topic, msg.payload, qos=0, retain=False)
        self.outbound_count += 1
        if self.outbound_count <= 20 or self.outbound_count % 100 == 0:
            log.info("Outbound #%d to SJMesh: %s (%d bytes)",
                     self.outbound_count, msg.topic, len(msg.payload))


def main():
    sjmesh_host = os.environ["SJMESH_HOST"]
    sjmesh_port = int(os.environ.get("SJMESH_PORT", "1883"))
    sjmesh_user = os.environ["SJMESH_USER"]
    sjmesh_pass = os.environ["SJMESH_PASS"]

    local_host = os.environ.get("LOCAL_HOST", "localhost")
    local_port = int(os.environ.get("LOCAL_PORT", "1883"))
    local_user = os.environ["LOCAL_USER"]
    local_pass = os.environ["LOCAL_PASS"]

    local_client = mqtt.Client(client_id="cnjmesh1-sjmesh-relay-local")
    local_client.username_pw_set(local_user, local_pass)
    remote_client = mqtt.Client(client_id="cnjmesh1-sjmesh-relay-remote")
    remote_client.username_pw_set(sjmesh_user, sjmesh_pass)

    relay = Relay(local_client, remote_client)

    def on_local_connect(client, userdata, flags, rc):
        if rc == 0:
            log.info("Connected to local broker %s:%s", local_host, local_port)
            if OUTBOUND_ENABLED:
                client.subscribe(LOCAL_OUTBOUND_TOPICS)
                log.info("Outbound ENABLED for gateways %s (cap %d/min); subscribed locally: %s",
                         sorted(OUR_GATEWAYS), OUTBOUND_MAX_PER_MINUTE,
                         [t for t, _ in LOCAL_OUTBOUND_TOPICS])
            else:
                log.info("Outbound disabled (set OUTBOUND_ENABLED=1 to turn on)")
        else:
            log.error("Local broker connect failed, rc=%s", rc)

    def on_remote_connect(client, userdata, flags, rc):
        if rc == 0:
            log.info("Connected to SJMesh broker %s:%s", sjmesh_host, sjmesh_port)
            client.subscribe(SUBSCRIBE_TOPICS)
            log.info("Subscribed: %s", [t for t, _ in SUBSCRIBE_TOPICS])
        else:
            log.error("SJMesh broker connect failed, rc=%s", rc)

    def on_remote_disconnect(client, userdata, rc):
        log.warning("Disconnected from SJMesh broker, rc=%s (will auto-reconnect)", rc)

    local_client.on_connect = on_local_connect
    local_client.on_message = relay.on_local_message
    local_client.reconnect_delay_set(min_delay=1, max_delay=30)
    local_client.connect(local_host, local_port, keepalive=60)
    local_client.loop_start()

    remote_client.on_connect = on_remote_connect
    remote_client.on_message = relay.on_remote_message
    remote_client.on_disconnect = on_remote_disconnect
    remote_client.reconnect_delay_set(min_delay=1, max_delay=30)
    remote_client.connect(sjmesh_host, sjmesh_port, keepalive=60)

    def heartbeat_loop():
        """Touches HEARTBEAT_FILE periodically as proof this process is alive
        and its MQTT loop is actually running -- independent of whether any
        real SJMesh traffic has arrived, since CentralNJ traffic is naturally
        bursty and can go quiet for hours during normal operation."""
        while True:
            try:
                with open(HEARTBEAT_FILE, "w") as f:
                    f.write(str(time.time()))
            except Exception as e:
                log.error("Heartbeat write failed: %s", e)
            time.sleep(HEARTBEAT_INTERVAL_SECONDS)

    threading.Thread(target=heartbeat_loop, daemon=True).start()

    remote_client.loop_forever()


if __name__ == "__main__":
    main()
