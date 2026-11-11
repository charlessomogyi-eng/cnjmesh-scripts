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

Guarded automatic recovery (added Nov 11 2026, switch off with AUTO_RECOVER=0):
  Found Nov 11: CJG1 stopped answering, the bot's Meshtastic interface became None, and
  the bot kept "running" while logging `Scheduler loop exception: 'NoneType' ...` every
  second, so systemd never restarted it and the 07:00 report silently could not run.
  Now, when the bot is down for DOWN_GRACE_SECONDS, or active but stuck in that error
  loop, the watchdog first asks "does CJG1 answer on its TCP port?":
     - CJG1 answers: restart mesh_bot.service (at most once per RECOVER_MIN_GAP and
       RECOVER_MAX_PER_DAY per 24 h), wait, verify, and say so in Discord.
     - CJG1 does not answer: do NOT restart (the bot would only quit again); ONE message
       says the gateway is unreachable, with a reminder every GATEWAY_REMINDER_SECONDS.
  A repeat inside the hour, or a third in 24 h, leaves the bot alone and says so.
  `touch /opt/mesh-bot-watchdog/paused` disables recovery (alerts continue) for the
  times Charlie uses the CJG1 app on purpose; remove the file to re-enable.

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

# ---- guarded automatic recovery (Nov 11 2026)
AUTO_RECOVER = os.environ.get("AUTO_RECOVER", "1") == "1"
CONFIG_FILE = os.environ.get("MESH_BOT_CONFIG", "/opt/meshing-around/config.ini")
GATEWAY_DEFAULT_HOST = "10.0.0.18"   # CJG1 (DHCP reservation)
GATEWAY_PORT = 4403
PAUSE_FILE = os.environ.get("PAUSE_FILE", "/opt/mesh-bot-watchdog/paused")
ERR_LOOP_MIN = 20                    # matching lines in ERR_LOOP_WINDOW means the loop is on
ERR_LOOP_WINDOW = "3 minutes ago"
ERR_LOOP_RE = re.compile(r"Scheduler loop exception: 'NoneType'")
RECOVER_MIN_GAP = 60 * 60
RECOVER_MAX_PER_DAY = 2
RECOVER_SETTLE_SECONDS = int(os.environ.get("RECOVER_SETTLE_SECONDS", "45"))
GATEWAY_REMINDER_SECONDS = 12 * 60 * 60

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
        "recoveries": [],          # epoch seconds of automatic restarts in the last 24 h
        "gw_down_alerted_at": None,  # epoch seconds of the last "gateway unreachable" message accepted
        "limit_alerted_at": None,  # epoch seconds of the last "auto-recovery limit reached" message
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


def gateway_host():
    """CJG1's address: GATEWAY_HOST env, else `hostname =` in the bot's config.ini, else the default."""
    env = os.environ.get("GATEWAY_HOST")
    if env:
        return env
    try:
        with open(CONFIG_FILE) as f:
            for line in f:
                m = re.match(r"\s*hostname\s*=\s*([^\s#;]+)", line)
                if m:
                    return m.group(1).split(":")[0]
    except Exception:  # noqa: BLE001
        pass
    return GATEWAY_DEFAULT_HOST


def gateway_reachable(host=None, port=GATEWAY_PORT, timeout=4):
    """True if a TCP connection to CJG1's API port opens. Opening and closing it is harmless."""
    try:
        with socket.create_connection((host or gateway_host(), port), timeout=timeout):
            return True
    except OSError:
        return False


def scheduler_error_loop():
    """True if the bot is in the 'interface is None' error loop. None if the journal is unreadable."""
    rc, out = run(["journalctl", "-u", SERVICE, "--since", ERR_LOOP_WINDOW, "--no-pager", "-o", "cat"], timeout=30)
    if rc != 0:
        return None
    return sum(1 for ln in out.splitlines() if ERR_LOOP_RE.search(ln)) >= ERR_LOOP_MIN


def prune_recoveries(state, now):
    state["recoveries"] = [t for t in state.get("recoveries", []) if now - t < 24 * 60 * 60]
    return state["recoveries"]


def recovery_allowed(state, now):
    """(ok, why-not)."""
    if not AUTO_RECOVER:
        return False, "automatic restart is switched off (AUTO_RECOVER=0)"
    if os.path.exists(PAUSE_FILE):
        return False, f"automatic restart is paused ({PAUSE_FILE} exists)"
    times = prune_recoveries(state, now)
    if times and now - max(times) < RECOVER_MIN_GAP:
        return False, "it was already restarted automatically less than an hour ago, so this is a repeat"
    if len(times) >= RECOVER_MAX_PER_DAY:
        return False, f"it was already restarted automatically {RECOVER_MAX_PER_DAY} times in 24 h"
    return True, ""


def restart_service():
    """Restart the bot and verify. Returns (ok, detail)."""
    if CHECK_ONLY or DRY_RUN:
        print(f"[{'check' if CHECK_ONLY else 'dry-run'}] would run: systemctl reset-failed + restart {SERVICE}")
        return True, "dry run"
    run(["systemctl", "reset-failed", SERVICE], timeout=15)
    rc, out = run(["systemctl", "restart", SERVICE], timeout=60)
    if rc != 0:
        return False, f"systemctl restart failed: {out.strip()[:200]}"
    time.sleep(RECOVER_SETTLE_SECONDS)
    if service_active() is not True:
        return False, "it stopped again within a minute"
    if scheduler_error_loop():
        return False, "it is running but the error loop came back"
    return True, ""


def try_recover(state, host, now, why_needed):
    """Gateway check, caps, restart, message. Mutates state; returns True if the bot was restarted OK."""
    gw = gateway_host()
    if not gateway_reachable(gw):
        last = state.get("gw_down_alerted_at")
        if last is None or now - last >= GATEWAY_REMINDER_SECONDS:
            msg = (f"\U0001F534 CNJMESH {host}: {SERVICE} {why_needed}, and CJG1 ({gw}:{GATEWAY_PORT}) is not "
                   f"answering, so I did NOT restart the bot (it would only quit again). "
                   f"Check that CJG1 is powered and on Wi-Fi. The 7 AM Meshtastic report and NWS alerts are "
                   f"stopped until it is back.")
            if send_discord(msg):
                state["gw_down_alerted_at"] = now
        return False
    ok, why = recovery_allowed(state, now)
    if not ok:
        last = state.get("limit_alerted_at")
        if last is None or now - last >= GATEWAY_REMINDER_SECONDS:
            msg = (f"\U0001F534 CNJMESH {host}: {SERVICE} {why_needed}; CJG1 answers, but I did not restart it: "
                   f"{why}. Needs you: `sudo systemctl restart {SERVICE}` and check `journalctl -u {SERVICE} -n 30`.")
            if send_discord(msg):
                state["limit_alerted_at"] = now
        return False
    if not (CHECK_ONLY or DRY_RUN):
        state["recoveries"].append(now)
        save_state(state)  # record the attempt before acting so a crash cannot loop
    good, detail = restart_service()
    if good:
        send_discord(f"\u2705 CNJMESH {host}: {SERVICE} {why_needed}; CJG1 answers, so I restarted it automatically "
                     f"and it is running cleanly. It will not auto-restart again for an hour.")
        state["down_since"] = None
        state["down_alerted_at"] = None
        state["gw_down_alerted_at"] = None
        return True
    send_discord(f"\U0001F534 CNJMESH {host}: {SERVICE} {why_needed}; I restarted it automatically but {detail}. "
                 f"Needs you: check `journalctl -u {SERVICE} -n 30`.")
    return False


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

    # ---- 0. guarded automatic recovery (down past the grace period, or stuck in the error loop)
    if not active and state["down_since"] is None:
        state["down_since"] = now
    if not active and now - state["down_since"] >= DOWN_GRACE_SECONDS:
        if try_recover(state, host, now, "has been down"):
            active = True
    elif active and scheduler_error_loop():
        if try_recover(state, host, now, "is running but stuck (its connection to CJG1 is gone)"):
            active = True
    if active and state.get("gw_down_alerted_at") is not None and gateway_reachable():
        if send_discord(f"CNJMESH {host}: CJG1 is answering again"):
            state["gw_down_alerted_at"] = None

    if not active:
        if state["down_since"] is None:
            state["down_since"] = now
        down_for = now - state["down_since"]
        last = state["down_alerted_at"]
        due = down_for >= DOWN_GRACE_SECONDS and (last is None or now - last >= DOWN_REMINDER_SECONDS)
        if state.get("gw_down_alerted_at") is not None:
            due = False  # the "CJG1 is not answering" message already explains it; don't double up
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
