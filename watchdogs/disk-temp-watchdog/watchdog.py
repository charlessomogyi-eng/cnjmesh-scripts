#!/usr/bin/env python3
"""
CNJ Mesh disk + temperature watchdog.

Checks root filesystem usage and CPU temperature, alerts to Discord
only on state change (ok -> warning -> urgent -> ok), matching the
pattern used by corescope-watchdog and the graywolf watchdogs.

Deploy identically to cnjmesh1, cnjmesh2, cnjmesh3 -- no host-specific
config beyond the HOSTNAME env var / system hostname used in alert text.

Run via systemd timer, not a long-running daemon (see disk-temp-watchdog.timer).
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.request

STATE_FILE = "/opt/disk-temp-watchdog/state.json"

# Discord webhook URL for #cnjmesh channel.
# Pull the real value from /opt/corescope-watchdog/watchdog.sh once cnjmesh1
# is back up, or from Discord: Server Settings -> Integrations -> Webhooks.
DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")

DISK_WARN_PCT = 80
DISK_URGENT_PCT = 90

TEMP_WARN_C = 70.0
TEMP_URGENT_C = 80.0


def get_hostname():
    """
    Returns a friendly, non-identifying label for Discord alerts (e.g. 'Node 1')
    instead of the real hostname, per preference: don't publish Pi hostnames
    to the community. Set via NODE_LABEL env var, one per host, in the
    .service file. Falls back to the real hostname only if NODE_LABEL is unset,
    so this is never silently blank -- but NODE_LABEL should always be set.
    """
    return os.environ.get("NODE_LABEL", socket.gethostname())


def get_disk_pct(path="/"):
    total, used, free = shutil.disk_usage(path)
    return round((used / total) * 100, 1)


def get_temp_c():
    """Returns CPU temp in Celsius via vcgencmd, or None if unavailable."""
    try:
        out = subprocess.run(
            ["vcgencmd", "measure_temp"],
            capture_output=True, text=True, timeout=5,
        )
        # Output format: temp=52.3'C
        raw = out.stdout.strip()
        val = raw.split("=")[1].split("'")[0]
        return float(val)
    except Exception:
        return None


def classify(value, warn, urgent):
    if value >= urgent:
        return "urgent"
    if value >= warn:
        return "warning"
    return "ok"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"disk_state": "ok", "temp_state": "ok"}
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {"disk_state": "ok", "temp_state": "ok"}


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
    host = get_hostname()
    state = load_state()

    disk_pct = get_disk_pct("/")
    disk_state = classify(disk_pct, DISK_WARN_PCT, DISK_URGENT_PCT)

    temp_c = get_temp_c()
    temp_state = classify(temp_c, TEMP_WARN_C, TEMP_URGENT_C) if temp_c is not None else "ok"

    prev_disk = state.get("disk_state", "ok")
    prev_temp = state.get("temp_state", "ok")

    if disk_state != prev_disk:
        if disk_state == "ok":
            send_discord(f"CNJMESH {host}: Disk usage back to normal ({disk_pct}%)")
        else:
            icon = "\U0001F534" if disk_state == "urgent" else "\U0001F7E1"
            send_discord(f"{icon} CNJMESH {host}: Disk usage {disk_state.upper()} ({disk_pct}% used, root filesystem)")

    if temp_c is not None and temp_state != prev_temp:
        if temp_state == "ok":
            send_discord(f"CNJMESH {host}: Temperature back to normal ({temp_c}\u00b0C)")
        else:
            icon = "\U0001F525" if temp_state == "urgent" else "\U0001F7E1"
            send_discord(f"{icon} CNJMESH {host}: Temperature {temp_state.upper()} ({temp_c}\u00b0C)")

    save_state({"disk_state": disk_state, "temp_state": temp_state})

    print(f"{host}: disk={disk_pct}% ({disk_state}) temp={temp_c}C ({temp_state})")


if __name__ == "__main__":
    main()
