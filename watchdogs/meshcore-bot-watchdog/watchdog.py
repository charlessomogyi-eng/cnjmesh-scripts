#!/usr/bin/env python3
"""
meshcore-bot health watchdog.

Directly detects the failure class that caused the Aug 19-28, 2026 incident:
meshcore-bot (CentralNJ-MC weather reports, agessaman/meshcore-bot) crashed
and hit systemd's start-limit-hit, silently going dead for 9 days with no
alert anywhere. Nobody noticed until Charles happened to check the channel's
message history and saw the 7:05am forecast had stopped.

Checks `systemctl is-active meshcore-bot` -- alerts to Discord only on a
state change (dead -> alive is reported too, so a manual fix is confirmed
without needing to check by hand), same pattern as ingest-rate-watchdog and
disk-temp-watchdog. Cheap, simple check on purpose: the failure mode itself
(service just isn't running) doesn't need anything fancier than "is it up."

Deploy on cnjmesh1 only (where meshcore-bot runs, tied to /dev/kpc1).
Run via systemd timer, not a long-running daemon.
"""
import json
import os
import socket
import subprocess
import time
import urllib.request

STATE_FILE = "/opt/meshcore-bot-watchdog/state.json"
ALERT_COOLDOWN_SECONDS = 24 * 60 * 60  # never re-alert the same condition more than once/day

DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")
SERVICE_NAME = "meshcore-bot"


def get_hostname():
    return socket.gethostname()


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {"service_state": "unknown", "last_alert": 0}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def cooldown_ok(state, key):
    last = state.get(key, 0)
    return (time.time() - last) >= ALERT_COOLDOWN_SECONDS


def send_discord(message):
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "REPLACE_ME":
        print(f"[no webhook configured] {message}")
        return
    payload = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL, data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Discord post failed: {e}")


def check_service_active(name):
    """Returns True if the unit is active, False otherwise (failed, inactive,
    or any other non-active state)."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() == "active"
    except Exception as e:
        print(f"systemctl check failed: {e}")
        return None  # unknown, not a confirmed failure -- don't alert on this


def main():
    host = get_hostname()
    state = load_state()

    is_active = check_service_active(SERVICE_NAME)
    if is_active is None:
        print(f"{host}: {SERVICE_NAME} check inconclusive (systemctl itself failed)")
        return

    service_state = "active" if is_active else "dead"

    if service_state != state["service_state"] and cooldown_ok(state, "last_alert"):
        if service_state == "active":
            send_discord(f"CNJMESH {host}: {SERVICE_NAME} back up and running")
        else:
            send_discord(
                f"\U0001F534 CNJMESH {host}: {SERVICE_NAME} is DOWN -- "
                f"check `systemctl status {SERVICE_NAME}`. "
                f"(This is the CentralNJ-MC weather bot -- last time this "
                f"happened it went undetected for 9 days.)"
            )
        state["last_alert"] = time.time()

    state["service_state"] = service_state
    save_state(state)
    print(f"{host}: {SERVICE_NAME}={service_state}")


if __name__ == "__main__":
    main()
