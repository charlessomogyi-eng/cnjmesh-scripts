#!/usr/bin/env python3
"""
CNJ Mesh system-health watchdog.

Checks disk usage, CPU temperature, and undervoltage (power supply issues).
Alerts to Discord only on state change per category, matching the pattern
used by corescope-watchdog and the graywolf watchdogs.

Deploy identically to cnjmesh1, cnjmesh2, cnjmesh3.

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

DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")

DISK_WARN_PCT = 80
DISK_URGENT_PCT = 90

TEMP_WARN_C = 70.0
TEMP_URGENT_C = 80.0


def get_hostname():
    """Friendly, non-identifying label for Discord alerts (e.g. 'Node 1')."""
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
        raw = out.stdout.strip()
        val = raw.split("=")[1].split("'")[0]
        return float(val)
    except Exception:
        return None


def get_undervoltage():
    """
    Returns True if the Pi is currently reporting undervoltage (bad power
    supply/cable -- can cause instability and corruption, plausibly related
    to the disk-full/hard-power-cut event that killed cnjmesh1's original
    board), False if fine, None if the check itself failed.
    """
    try:
        out = subprocess.run(
            ["vcgencmd", "get_throttled"],
            capture_output=True, text=True, timeout=5,
        )
        # Output format: throttled=0x50000
        raw = out.stdout.strip()
        val = int(raw.split("=")[1], 16)
        # Bit 0: under-voltage detected right now
        return bool(val & 0x1)
    except Exception:
        return None


def classify(value, warn, urgent):
    if value >= urgent:
        return "urgent"
    if value >= warn:
        return "warning"
    return "ok"


def default_state():
    return {"disk_state": "ok", "temp_state": "ok", "undervolt_state": "ok"}


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


def main():
    host = get_hostname()
    state = load_state()
    summary_parts = []

    # --- Disk ---
    disk_pct = get_disk_pct("/")
    disk_state = classify(disk_pct, DISK_WARN_PCT, DISK_URGENT_PCT)
    if disk_state != state["disk_state"]:
        if disk_state == "ok":
            send_discord(f"CNJMESH {host}: Disk usage back to normal ({disk_pct}%)")
        else:
            icon = "\U0001F534" if disk_state == "urgent" else "\U0001F7E1"
            send_discord(f"{icon} CNJMESH {host}: Disk usage {disk_state.upper()} ({disk_pct}% used, root filesystem)")
    state["disk_state"] = disk_state
    summary_parts.append(f"disk={disk_pct}%({disk_state})")

    # --- Temperature ---
    temp_c = get_temp_c()
    temp_state = classify(temp_c, TEMP_WARN_C, TEMP_URGENT_C) if temp_c is not None else "ok"
    if temp_c is not None and temp_state != state["temp_state"]:
        if temp_state == "ok":
            send_discord(f"CNJMESH {host}: Temperature back to normal ({temp_c}\u00b0C)")
        else:
            icon = "\U0001F525" if temp_state == "urgent" else "\U0001F7E1"
            send_discord(f"{icon} CNJMESH {host}: Temperature {temp_state.upper()} ({temp_c}\u00b0C)")
    state["temp_state"] = temp_state
    summary_parts.append(f"temp={temp_c}C({temp_state})")

    # --- Undervoltage ---
    undervolt = get_undervoltage()
    undervolt_state = "urgent" if undervolt else "ok"
    if undervolt is not None and undervolt_state != state["undervolt_state"]:
        if undervolt_state == "ok":
            send_discord(f"CNJMESH {host}: Power supply back to normal (undervoltage cleared)")
        else:
            send_discord(f"\U000026A1 CNJMESH {host}: UNDERVOLTAGE detected -- check power supply/cable, this can cause instability or corruption")
    state["undervolt_state"] = undervolt_state
    summary_parts.append(f"undervolt={undervolt_state}")

    save_state(state)
    print(f"{host}: " + " ".join(summary_parts))


if __name__ == "__main__":
    main()
