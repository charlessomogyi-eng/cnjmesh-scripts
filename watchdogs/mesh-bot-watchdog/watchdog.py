#!/usr/bin/env python3
"""
mesh-bot-watchdog -- alerts when the Meshtastic bot (meshing-around, mesh_bot.service)
is down, or when the daily 07:00 report did not run.

Why this exists (Oct 30 2026): the 7 AM CentralNJ weather report is sent by
mesh_bot.service on cnjmesh1 through CJG1 (TCP 10.0.0.18:4403). It has missed
silently before (Aug 4: service down; Oct 15: cause never found) and nothing
alerted. Charlie also now stops the bot on purpose to use the app on CJG1 (the node
allows only one TCP client), so a forgotten stop would cost him the next report.
There was no watchdog for this bot (meshcore-bot-watchdog covers the MeshCore bot only).

What it checks (every run, read-only):
  1. Is mesh_bot.service active?
     - Down for less than DOWN_GRACE_SECONDS: silence (covers a planned
       `stop` + `systemd-run ... start` pause of 20 minutes).
     - Down longer: ONE Discord message, then a reminder every
       DOWN_REMINDER_SECONDS while it stays down.
     - Back up after an alert: a short "back up" message.
  2. Did the 07:00 scheduled job run today? The bot logs its scheduler state
     as `... (last run: YYYY-MM-DD HH:MM:SS, next run: ...)`. If today's date has
     not appeared in the journal by REPORT_DEADLINE (09:30 local), ONE message
     "could not confirm" per day. This proves the scheduler fired, not that the
     radio transmitted it (no log line proving transmission has been verified).

Discord posts are retried on the next run if they fail: state is only updated
after Discord accepts the message (the older meshcore-bot-watchdog swallowed failures).

Modes:
  python3 watchdog.py --check     read-only status print, no alerts, state untouched
  DRY_RUN=1 python3 watchdog.py   full logic, prints instead of posting, state untouched

Deploy on cnjmesh1 only, run as root (reads the journal). Run via systemd timer.
Webhook: the unit file keeps CNJ_DISCORD_WEBHOOK=REPLACE_ME; the real URL goes in a
systemd drop-in (never committed). See README.md.
"""

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

STATE_FILE = os.environ.get("STATE_FILE", "/opt/mesh-bot-watchdog/state.json")
SERVICE = "mesh_bot.service"
DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")

DOWN_GRACE_SECONDS = 25 * 60        # planned pauses (20 min) stay silent
DOWN_REMINDER_SECONDS = 12 * 60 * 60
REPORT_TIME = "07:00:00"            # scheduler `time =` in meshing-around config.ini
REPORT_DEADLINE = (9, 30)           # local time; check is silent before this

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
CHECK_ONLY = "--check" in sys.argv

LAST_RUN_RE = re.compile(r"last run: (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})")


def get_hostname():
    return os.environ.get("NODE_LABEL", socket.gethostname())


def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout
    except Exception as e:  # noqa: BLE001 - a watchdog must never crash on a helper
        return 1, f"{type(e).__name__}: {e}"


def default_state():
    return {
        "down_since": None,        # epoch seconds when first seen not active
        "down_alerted_at": None,   # epoch seconds of the last DOWN message accepted by Discord
        "ok_day": "",              # YYYY-MM-DD for which today's 07:00 run was confirmed
        "missed_alerted_day": "",  # YYYY-MM-DD for which the "could not confirm" message went out
    }


def load_state():
    if not os.path.exists(STATE_FILE):
        return default_state()
    try:
        with open(STATE_FILE) as f:
            merged = default_state()
            merged.update(json.load(f))
            return merged
    except Exception:  # noqa: BLE001
        return default_state()


def save_state(state):
    if DRY_RUN or CHECK_ONLY:
        return
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def send_discord(message):
    """Returns True only if Discord accepted the post (or in dry-run)."""
    if CHECK_ONLY:
        print("[check] would consider sending:", message)
        return False
    if DRY_RUN:
        print("[dry-run] would send to Discord:", message)
        return True
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "REPLACE_ME":
        print("Discord webhook not configured; NOT marking as sent:", message, file=sys.stderr)
        return False
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=json.dumps({"content": message}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "cnjmesh-watchdog/1.0"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"Failed to post to Discord: {e}", file=sys.stderr)
        return False


def service_active():
    """True / False, or None if systemctl itself failed (inconclusive, never alert on it)."""
    rc, out = run(["systemctl", "is-active", SERVICE], timeout=10)
    word = out.strip()
    if word in ("active", "inactive", "failed", "activating", "deactivating"):
        return word == "active"
    return None


def todays_last_runs(today):
    """Return list of 'HH:MM:SS' last-run times for `today`, or None if the journal could not be read."""
    rc, out = run(
        ["journalctl", "-u", SERVICE, "--since", f"{today} {REPORT_TIME}", "--no-pager", "-o", "cat"],
        timeout=60,
    )
    if rc != 0:
        return None
    return [m.group(2) for m in LAST_RUN_RE.finditer(out) if m.group(1) == today]


def main():
    host = get_hostname()
    state = load_state()
    now = time.time()
    now_dt = datetime.fromtimestamp(now)
    today = now_dt.strftime("%Y-%m-%d")

    # ---- 1. is the bot running?
    active = service_active()
    if active is None:
        print(f"{host}: {SERVICE} check inconclusive (systemctl failed); skipping")
        return

    if not active:
        if state["down_since"] is None:
            state["down_since"] = now
        down_for = now - state["down_since"]
        last = state["down_alerted_at"]
        due = down_for >= DOWN_GRACE_SECONDS and (last is None or now - last >= DOWN_REMINDER_SECONDS)
        if due:
            mins = int(down_for // 60)
            msg = (f"\U0001F534 CNJMESH {host}: {SERVICE} has been DOWN for about {mins} min. "
                   f"The 7 AM Meshtastic report and NWS alerts depend on it. "
                   f"Start it with: sudo systemctl start {SERVICE}")
            if send_discord(msg):
                state["down_alerted_at"] = now
    else:
        if state["down_alerted_at"] is not None:
            if send_discord(f"CNJMESH {host}: {SERVICE} is back up and running"):
                state["down_since"] = None
                state["down_alerted_at"] = None
        else:
            state["down_since"] = None

    # ---- 2. did today's 07:00 run happen?
    if state["ok_day"] != today:
        runs = todays_last_runs(today)
        if runs is None:
            print(f"{host}: could not read the journal; skipping the 07:00 check")
        elif runs:
            state["ok_day"] = today
        elif ((now_dt.hour, now_dt.minute) >= REPORT_DEADLINE
              and state["missed_alerted_day"] != today and active):
            msg = (f"\U0001F7E0 CNJMESH {host}: could not confirm today's 07:00 Meshtastic report ran "
                   f"(no `last run: {today}` in the {SERVICE} journal by "
                   f"{REPORT_DEADLINE[0]:02d}:{REPORT_DEADLINE[1]:02d}). "
                   f"Check the CentralNJ channel and `systemctl status {SERVICE}`.")
            if send_discord(msg):
                state["missed_alerted_day"] = today

    save_state(state)
    print(f"{host}: {SERVICE}={'active' if active else 'not-active'} "
          f"down_since={state['down_since']} ok_day={state['ok_day']!r} "
          f"missed_alerted_day={state['missed_alerted_day']!r}")


if __name__ == "__main__":
    main()
