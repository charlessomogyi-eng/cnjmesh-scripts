#!/usr/bin/env python3
"""
CNJ Mesh peer-check watchdog.

Each Pi pings the OTHER Pis (not itself) and alerts to Discord if one
stops responding. No central monitoring server, no third-party tool,
no cost -- each Pi covers the others, so one Pi being down doesn't
blind you to the rest.

Deploy on cnjmesh1, cnjmesh2, cnjmesh3 -- each with a PEERS list that
excludes its own IP (see .service file for how to set this per-host).

Alert-only on state change, same pattern as disk-temp-watchdog.
"""

import json
import os
import socket
import subprocess
import sys
import urllib.request

STATE_FILE = "/opt/peer-check/state.json"

DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")
NODE_LABEL = os.environ.get("NODE_LABEL", socket.gethostname())

# Comma-separated "label:ip" pairs, e.g. "Node 1:10.0.0.181,Node 3:10.0.0.186"
# Set per-host in the .service file -- each Pi should list the OTHER Pis, not itself.
PEERS_RAW = os.environ.get("PEERS", "")


def parse_peers(raw):
    peers = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        label, ip = entry.split(":", 1)
        peers.append((label.strip(), ip.strip()))
    return peers


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


def send_discord(message):
    if DISCORD_WEBHOOK_URL == "REPLACE_ME":
        print("Discord webhook not configured, would have sent:", message)
        return
    payload = json.dumps({"content": message}).encode()
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Failed to post to Discord: {e}", file=sys.stderr)


def main():
    peers = parse_peers(PEERS_RAW)
    if not peers:
        print("No PEERS configured, nothing to check.", file=sys.stderr)
        return

    state = load_state()

    for label, ip in peers:
        is_up = ping(ip)
        current = "up" if is_up else "down"
        prev = state.get(ip, "up")  # assume up on first run, don't alert on startup

        if current != prev:
            if current == "down":
                send_discord(f"\U0001F534 CNJMESH {label} appears OFFLINE (checked from {NODE_LABEL})")
            else:
                send_discord(f"CNJMESH {label} back ONLINE (checked from {NODE_LABEL})")

        state[ip] = current
        print(f"{label} ({ip}): {current}")

    save_state(state)


if __name__ == "__main__":
    main()
