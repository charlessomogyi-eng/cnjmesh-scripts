#!/usr/bin/env python3
"""LoRa APRS receive dashboard: collector and web page in one program.

Listens to a CA2RXU iGate's syslog (UDP) and, optionally, to the MQTT topic it
publishes. Read-only toward the station: it only subscribes to MQTT and never
publishes anything.

Settings come from environment variables; see deploy/env.example.
"""
import json
import logging
import os
import signal
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from store import Store

log = logging.getLogger("lora-aprs-dashboard")
STATIC = Path(__file__).resolve().parent / "static"
# The only files served besides the page itself (no directory browsing).
FILES = {
    "/leaflet/leaflet.js": ("leaflet/leaflet.js", "text/javascript; charset=utf-8"),
    "/leaflet/leaflet.css": ("leaflet/leaflet.css", "text/css; charset=utf-8"),
}


def parse_home(lat, lon):
    """Receiver position from OWN_LAT / OWN_LON, or None if not set."""
    if not lat and not lon:
        return None
    home = (float(lat), float(lon))
    if not (-90 <= home[0] <= 90 and -180 <= home[1] <= 180):
        raise ValueError("OWN_LAT / OWN_LON out of range")
    return home


def settings(env=os.environ):
    def get(name, default):
        value = env.get(name, "").strip()
        return value if value else default

    return {
        "own_call": get("OWN_CALL", "K2GIA-10"),
        "home": parse_home(get("OWN_LAT", ""), get("OWN_LON", "")),
        "syslog_bind": get("SYSLOG_BIND", "0.0.0.0"),
        "syslog_port": int(get("SYSLOG_PORT", "1514")),
        "syslog_allow": [a for a in get("SYSLOG_ALLOW", "").replace(",", " ").split()],
        "forward": [parse_target(t) for t in
                    get("SYSLOG_FORWARD", "").replace(",", " ").split()],
        "mqtt_host": get("MQTT_HOST", ""),
        "mqtt_port": int(get("MQTT_PORT", "1883")),
        "mqtt_user": get("MQTT_USER", ""),
        "mqtt_password": env.get("MQTT_PASSWORD", ""),
        "mqtt_topic": get("MQTT_TOPIC", "aprs-k2gia-10").rstrip("/"),
        "http_bind": get("HTTP_BIND", "0.0.0.0"),
        "http_port": int(get("HTTP_PORT", "8090")),
        "db": get("DB_PATH", "lora-aprs.db"),
        "retention_days": float(get("RETENTION_DAYS", "90")),
        "setup": {label: get(name, "") for label, name in (
            ("Hardware", "SETUP_HARDWARE"), ("Antenna", "SETUP_ANTENNA"),
            ("Notes", "SETUP_NOTES")) if get(name, "")},
        "sf": int(get("LORA_SF", "12")),
        "bw": int(get("LORA_BW", "125000")),
        "cr": int(get("LORA_CR", "5")),
        "preamble": int(get("LORA_PREAMBLE", "8")),
    }


def parse_target(text):
    host, sep, port = text.rpartition(":")
    if not sep or not host:
        raise ValueError("SYSLOG_FORWARD entries look like host:port, got %r" % text)
    return host, int(port)


def syslog_loop(sock, store, cfg, stop):
    out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    while not stop.is_set():
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        except OSError:
            break
        if cfg["syslog_allow"] and addr[0] not in cfg["syslog_allow"]:
            continue
        for target in cfg["forward"]:
            try:
                out.sendto(data, target)
            except OSError as exc:
                log.warning("forward to %s:%d failed: %s", *target, exc)
        try:
            store.on_syslog(data)
        except Exception:
            log.exception("could not handle a syslog line from %s", addr[0])
    out.close()


def is_local(host):
    """True if host is an address of this machine (binding to it works)."""
    try:
        ip = socket.gethostbyname(host)
    except OSError:
        return False
    if ip.startswith("127.") or ip == "0.0.0.0":
        return True
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.bind((ip, 0))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def open_syslog_socket(cfg):
    for host, port in cfg["forward"]:
        if port == cfg["syslog_port"] and is_local(host):
            # Each line would come straight back and be sent again, forever.
            raise ValueError("SYSLOG_FORWARD %s:%d points back at our own port"
                             % (host, port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((cfg["syslog_bind"], cfg["syslog_port"]))
    return sock


def start_mqtt(store, cfg):
    import paho.mqtt.client as mqtt     # only needed when MQTT_HOST is set

    client_id = "lora-aprs-dash-%d" % os.getpid()   # never the iGate's callsign
    if hasattr(mqtt, "CallbackAPIVersion"):         # paho-mqtt 2.x
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    else:                                           # paho-mqtt 1.x
        client = mqtt.Client(client_id=client_id)
    prefix = cfg["mqtt_topic"] + "/"

    # The extra arguments differ between paho-mqtt 1.x and 2.x.
    def on_connect(c, userdata, flags, rc, *extra):
        store.status["mqtt_connected"] = rc == 0
        if rc == 0:
            c.subscribe(prefix + "#")
            log.info("MQTT connected, subscribed to %s#", prefix)
        else:
            log.error("MQTT connection refused, code %s", rc)

    def on_disconnect(c, userdata, *args):
        rc = args[1] if len(args) > 1 else args[0]
        store.status["mqtt_connected"] = False
        log.warning("MQTT disconnected, code %s", rc)

    def on_message(c, userdata, msg):
        if msg.retain or not msg.topic.startswith(prefix):
            return      # a retained message is old, not something just heard
        try:
            store.on_mqtt(msg.topic[len(prefix):], msg.payload)
        except Exception:
            log.exception("could not handle MQTT topic %s", msg.topic)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    if cfg["mqtt_user"]:
        client.username_pw_set(cfg["mqtt_user"], cfg["mqtt_password"])
    store.status["mqtt_connected"] = False
    client.connect_async(cfg["mqtt_host"], cfg["mqtt_port"], keepalive=60)
    client.loop_start()
    return client


def make_handler(store, clock=None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "lora-aprs-dashboard"

        def do_GET(self):
            url = urlsplit(self.path)
            try:
                if url.path in ("/", "/index.html"):
                    self.reply((STATIC / "index.html").read_bytes(),
                               "text/html; charset=utf-8")
                elif url.path in FILES:
                    name, kind = FILES[url.path]
                    self.reply((STATIC / name).read_bytes(), kind, cache=True)
                elif url.path == "/api/summary":
                    self.json(store.summary(clock() if clock else None))
                elif url.path == "/api/packets":
                    limit = parse_qs(url.query).get("limit", ["100"])[0]
                    self.json(store.recent(int(limit) if limit.isdigit() else 100))
                else:
                    self.send_error(404)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def json(self, value):
            self.reply(json.dumps(value).encode(), "application/json")

        def reply(self, body, kind, cache=False):
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "max-age=86400" if cache else "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            log.debug("%s %s", self.address_string(), fmt % args)

    return Handler


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = settings()
    store = Store(cfg["db"], cfg["own_call"], cfg["sf"], cfg["bw"], cfg["cr"],
                  cfg["preamble"], cfg["setup"], cfg["home"])
    # Open both ports before starting anything, so a busy port fails loudly.
    sock = open_syslog_socket(cfg)
    web = ThreadingHTTPServer((cfg["http_bind"], cfg["http_port"]),
                              make_handler(store))
    stop = threading.Event()
    threading.Thread(target=syslog_loop, args=(sock, store, cfg, stop),
                     daemon=True).start()
    threading.Thread(target=web.serve_forever, daemon=True).start()
    client = start_mqtt(store, cfg) if cfg["mqtt_host"] else None
    log.info("syslog on udp %s:%d, web page on http://%s:%d",
             cfg["syslog_bind"], cfg["syslog_port"], cfg["http_bind"],
             cfg["http_port"])
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    while not stop.is_set():
        removed = store.purge(cfg["retention_days"])
        if removed:
            log.info("removed %d old packets", removed)
        stop.wait(3600)
    if client:
        client.disconnect()
        client.loop_stop()
    web.shutdown()
    sock.close()
    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
