#!/usr/bin/env python3
"""
SJMesh -> local broker relay.
Subscribes to SJMesh's broker for CentralNJ topics, drops the one known
bad node's packets, republishes everything else to the local broker.
Replaces the native Mosquitto sjmesh bridge (kept permanently disabled).
"""
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

SJMESH_HOST = os.environ["SJMESH_HOST"]
SJMESH_PORT = int(os.environ.get("SJMESH_PORT", "1883"))
SJMESH_USER = os.environ["SJMESH_USER"]
SJMESH_PASS = os.environ["SJMESH_PASS"]

LOCAL_HOST = os.environ.get("LOCAL_HOST", "localhost")
LOCAL_PORT = int(os.environ.get("LOCAL_PORT", "1883"))
LOCAL_USER = os.environ["LOCAL_USER"]
LOCAL_PASS = os.environ["LOCAL_PASS"]

HEARTBEAT_FILE = "/opt/sjmesh-relay/heartbeat"
HEARTBEAT_INTERVAL_SECONDS = 60

SUBSCRIBE_TOPICS = [
    ("msh/US/2/e/CentralNJ/#", 0),
    ("msh/US/NJ/2/e/CentralNJ/#", 0),
]

BLOCKED_TOPICS = {
    "msh/US/2/e/CentralNJ/!699a9390",
    "msh/US/NJ/2/e/CentralNJ/!699a9390",
    "msh/US/2/e/CentralNJ/!698574b0",
    "msh/US/NJ/2/e/CentralNJ/!698574b0",
    "msh/US/2/e/CentralNJ/!db51bb30",
    "msh/US/NJ/2/e/CentralNJ/!db51bb30",
}

blocked_count = 0
relayed_count = 0

local_client = mqtt.Client(client_id="cnjmesh1-sjmesh-relay-local")
local_client.username_pw_set(LOCAL_USER, LOCAL_PASS)


def on_local_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("Connected to local broker %s:%s", LOCAL_HOST, LOCAL_PORT)
    else:
        log.error("Local broker connect failed, rc=%s", rc)


local_client.on_connect = on_local_connect
local_client.reconnect_delay_set(min_delay=1, max_delay=30)
local_client.connect(LOCAL_HOST, LOCAL_PORT, keepalive=60)
local_client.loop_start()


def on_remote_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("Connected to SJMesh broker %s:%s", SJMESH_HOST, SJMESH_PORT)
        client.subscribe(SUBSCRIBE_TOPICS)
        log.info("Subscribed: %s", [t for t, _ in SUBSCRIBE_TOPICS])
    else:
        log.error("SJMesh broker connect failed, rc=%s", rc)


def on_remote_message(client, userdata, msg):
    global blocked_count, relayed_count
    if msg.topic in BLOCKED_TOPICS:
        blocked_count += 1
        if blocked_count % 100 == 1:
            log.info("Blocked bad-node packet #%d on %s", blocked_count, msg.topic)
        return
    local_client.publish(msg.topic, msg.payload, qos=msg.qos, retain=msg.retain)
    relayed_count += 1
    if relayed_count % 500 == 1:
        log.info("Relayed packet #%d (last topic: %s)", relayed_count, msg.topic)


def on_remote_disconnect(client, userdata, rc):
    log.warning("Disconnected from SJMesh broker, rc=%s (will auto-reconnect)", rc)


remote_client = mqtt.Client(client_id="cnjmesh1-sjmesh-relay-remote")
remote_client.username_pw_set(SJMESH_USER, SJMESH_PASS)
remote_client.on_connect = on_remote_connect
remote_client.on_message = on_remote_message
remote_client.on_disconnect = on_remote_disconnect
remote_client.reconnect_delay_set(min_delay=1, max_delay=30)
remote_client.connect(SJMESH_HOST, SJMESH_PORT, keepalive=60)


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
