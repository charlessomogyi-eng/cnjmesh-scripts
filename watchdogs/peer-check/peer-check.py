#!/usr/bin/env python3
"""
CNJ Mesh peer-check watchdog.

Each Pi pings the OTHER Pis (not itself) and alerts to Discord if one
stops responding. No central monitoring server, no third-party tool,
no cost -- each Pi covers the others, so one Pi being down doesn't
blind you to the rest.

DEBOUNCED: a peer must fail DOWN_THRESHOLD consecutive checks (default 3,
i.e. 15 minutes at the standard 5-minute timer interval) before it's
declared truly down and alerted. This avoids false alarms from brief
blips -- a router reboot, a few minutes of bad WiFi, a short power flicker
-- and avoids the mismatched "back online with no prior offline alert"
problem that happens when a real outage coincides with the ALERTING
Pi's own network being briefly down too (the down-alert can't be
delivered in that split second, but the recovery alert goes through fine
once things are back -- debouncing means short coincidental blips like
that don't get treated as a real down event in the first place).

Optionally lists known services hosted on a peer when it goes down,
so the alert says what's actually affected, not just "node down".

Optionally cross-posts specific peers' up/down alerts to a second
Discord webhook (e.g. the Meshtastic community server), for peers whose
services are relevant to that audience (meshview/malla are Meshtastic
tools; MeshCore-only outages stay CNJ-only).

Deploy on cnjmesh1, cnjmesh2, cnjmesh3 -- each with a PEERS list that
excludes its own IP (see .service file for how to set this per-host).
"""

import json
import os
import socket
import subprocess
import sys
import urllib.request

STATE_FILE = "/opt/peer-check/state.json"

DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "https://discord.com/api/webhooks/1527750520138367156/pn4PUcrUNQ7CMMOkuE-BIWyT0l4NOE1TeA54pXsiaBcsC19JKaPLnWDdciZJdz6pry7x")
NODE_LABEL = os.environ.get("NODE_LABEL", socket.gethostname())

# Comma-separated "label:ip" pairs, e.g. "Node 1:10.0.0.181,Node 3:10.0.0.186"
PEERS_RAW = os.environ.get("PEERS", "")

# Optional: what services live on each peer, shown in the down-alert.
# Format: "Node 1:meshview,malla,meshcorehub,mqtt,APRS 2m;Node 3:Observer,KPR2"
# Semicolon between peers, colon after label, comma-separated service list.
SERVICES_RAW = os.environ.get("SERVICES", "")

# Optional second webhook (e.g. Meshtastic community server) for cross-posting.
CROSS_POST_WEBHOOK = os.environ.get("CROSS_POST_WEBHOOK", "https://discord.com/api/webhooks/1529297959987183659/o1jPNQaxa67uK5-9tmbUfOCoKny6IFaWsHy9nIFCyNLFdlkJ95RMflxn21ZUf-9l8J0Z")
# Comma-separated labels whose alerts should ALSO go to CROSS_POST_WEBHOOK,
# e.g. "Node 1,Node 2" -- only peers whose services matter to that audience.
CROSS_POST_LABELS = set(
    l.strip() for l in os.environ.get("CROSS_POST_LABELS", "").split(",") if l.strip()
)

# Number of consecutive failed checks required before declaring a peer
# truly down and alerting. Default 3 = 15 minutes at the standard 5-min
# timer interval. Set DOWN_THRESHOLD env var to override.
DOWN_THRESHOLD = int(os.environ.get("DOWN_THRESHOLD", "3"))


def parse_peers(raw):
    peers = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        label, ip = entry.split(":", 1)
        peers.append((label.strip(), ip.strip()))
    return peers


def parse_services(raw):
    """Returns {label: [service, ...]}"""
    services = {}
    for entry in raw.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        label, svc_list = entry.split(":", 1)
        services[label.strip()] = [s.strip() for s in svc_list.split(",") if s.strip()]
    return services


def ping(ip, timeout=3):
    """Returns True if the host responds to a single ping, False otherwise."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), ip],
            capture_output=True, timeout=timeout + 2,
        )
        return result.returncode == 0
    except Exception:
        return False


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def _post(webhook_url, message):
    if not webhook_url or webhook_url == "REPLACE_ME":
        print("Webhook not configured, would have sent:", message)
        return
    payload = json.dumps({"content": message}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "cnjmesh-watchdog/1.0",
        },
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Failed to post to Discord: {e}", file=sys.stderr)


def send_discord(message, label=None):
    """Sends to the primary #cnjmesh webhook, and cross-posts to the
    secondary webhook if this peer's label is in CROSS_POST_LABELS."""
    _post(DISCORD_WEBHOOK_URL, message)
    if label and label in CROSS_POST_LABELS and CROSS_POST_WEBHOOK:
        _post(CROSS_POST_WEBHOOK, message)


def build_down_message(label, services_map):
    svc_list = services_map.get(label, [])
    if svc_list:
        svc_text = ", ".join(svc_list)
        return (
            f"\U0001F534 CNJMESH {label} appears OFFLINE (checked from {NODE_LABEL})\n"
            f"Services likely affected: {svc_text}"
        )
    return f"\U0001F534 CNJMESH {label} appears OFFLINE (checked from {NODE_LABEL})"


def build_up_message(label, services_map):
    svc_list = services_map.get(label, [])
    if svc_list:
        svc_text = ", ".join(svc_list)
        return (
            f"CNJMESH {label} back ONLINE (checked from {NODE_LABEL})\n"
            f"Restored: {svc_text}"
        )
    return f"CNJMESH {label} back ONLINE (checked from {NODE_LABEL})"


def main():
    peers = parse_peers(PEERS_RAW)
    services_map = parse_services(SERVICES_RAW)
    if not peers:
        print("No PEERS configured, nothing to check.", file=sys.stderr)
        return

    state = load_state()

    for label, ip in peers:
        is_up = ping(ip)

        # Per-peer state: {"alert_state": "up"/"down", "fail_count": N}
        peer_state = state.get(ip, {"alert_state": "up", "fail_count": 0})
        # Back-compat: older state files stored a bare string ("up"/"down")
        if isinstance(peer_state, str):
            peer_state = {"alert_state": peer_state, "fail_count": 0}

        alert_state = peer_state.get("alert_state", "up")
        fail_count = peer_state.get("fail_count", 0)

        if is_up:
            if alert_state == "down":
                # Was in a confirmed-down alert state -- now recovered, alert immediately.
                send_discord(build_up_message(label, services_map), label=label)
            alert_state = "up"
            fail_count = 0
            status_text = "up"
        else:
            fail_count += 1
            if alert_state == "up" and fail_count >= DOWN_THRESHOLD:
                # Crossed the debounce threshold -- now genuinely alert as down.
                send_discord(build_down_message(label, services_map), label=label)
                alert_state = "down"
            status_text = f"down (fail_count={fail_count}/{DOWN_THRESHOLD})"

        state[ip] = {"alert_state": alert_state, "fail_count": fail_count}
        print(f"{label} ({ip}): {status_text}")

    save_state(state)


if __name__ == "__main__":
    main()
