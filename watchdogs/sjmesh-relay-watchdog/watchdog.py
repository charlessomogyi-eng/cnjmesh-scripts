#!/usr/bin/env python3
"""
SJMesh relay heartbeat watchdog.

Checks that /opt/sjmesh-relay/heartbeat is being touched by the relay's
own background thread (see relay.py's heartbeat_loop). This checks the
relay process's actual health directly, rather than inferring it from
CentralNJ traffic volume in Malla's DB -- traffic-based inference doesn't
work here because CJG1/CJG2 also publish native CentralNJ traffic
independent of this relay, so the DB alone can't tell "relay is dead"
apart from "relay is fine, SJMesh is just quiet right now."

Deploy on cnjmesh1 only (where sjmesh-relay.service runs).
Run via systemd timer, not a long-running daemon.
"""

import json
import os
import socket
import sys
import time
import urllib.request

STATE_FILE = "/opt/sjmesh-relay-watchdog/state.json"
HEARTBEAT_FILE = "/opt/sjmesh-relay/heartbeat"
ALERT_COOLDOWN_SECONDS = 24 * 60 * 60  # never re-alert the same condition more than once/day

DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")

# Heartbeat writes every 60s (HEARTBEAT_INTERVAL_SECONDS in relay.py).
# This threshold is about the relay PROCESS being alive, not about
# CentralNJ traffic volume -- SJMesh traffic itself can go quiet for
# hours during normal operation (confirmed Aug 18 2026), but the
# heartbeat thread runs independent of any actual message traffic.
STALE_THRESHOLD_SECONDS = 10 * 60  # 10 min = several missed heartbeats


def get_hostname():
    return os.environ.get("NODE_LABEL", socket.gethostname())


def default_state():
    return {"heartbeat_state": "ok", "heartbeat_last_alert": 0}


def load_state():
    if not os.path.exists(STATE_FILE):
        return default_state()
    try:
        with open(STATE_FILE) as f:
            loaded = json.load(f)
        merged = default_state()
        merged.update(loaded)
        return merged
    except Exception:
        return default_state()


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def cooldown_ok(state, key):
    last = state.get(key, 0)
    return (time.time() - last) >= ALERT_COOLDOWN_SECONDS


def send_discord(message):
    if DISCORD_WEBHOOK_URL == "REPLACE_ME":
        print("Discord webhook not configured, would have sent:", message)
        return
    payload = json.dumps({"content": message}).encode()
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
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


def check_heartbeat():
    """Returns (age_seconds, error) -- error is a string if the file is
    missing or unreadable, else None."""
    if not os.path.exists(HEARTBEAT_FILE):
        return None, "heartbeat file missing entirely"
    try:
        mtime = os.path.getmtime(HEARTBEAT_FILE)
        return time.time() - mtime, None
    except Exception as e:
        return None, f"heartbeat file unreadable: {e}"


def main():
    host = get_hostname()
    state = load_state()

    age, error = check_heartbeat()

    if error is not None:
        heartbeat_state = "stale"
        detail = error
    elif age >= STALE_THRESHOLD_SECONDS:
        heartbeat_state = "stale"
        detail = f"last heartbeat {int(age)}s ago (threshold {STALE_THRESHOLD_SECONDS}s)"
    else:
        heartbeat_state = "ok"
        detail = f"last heartbeat {int(age)}s ago"

    if heartbeat_state != state["heartbeat_state"] and cooldown_ok(state, "heartbeat_last_alert"):
        if heartbeat_state == "ok":
            send_discord(f"CNJMESH {host}: sjmesh-relay heartbeat back to normal ({detail})")
        else:
            send_discord(f"\U0001F534 CNJMESH {host}: sjmesh-relay heartbeat STALE ({detail}) -- SJMesh CentralNJ traffic may not be reaching the local broker. Check `systemctl status sjmesh-relay` and `journalctl -u sjmesh-relay`.")
        state["heartbeat_last_alert"] = time.time()
    state["heartbeat_state"] = heartbeat_state

    save_state(state)
    print(f"{host}: sjmesh-relay heartbeat={heartbeat_state} ({detail})")


if __name__ == "__main__":
    main()
