#!/usr/bin/env python3
"""
meshcore-bot watchdog (cnjmesh1) -- keeps the CentralNJ-MC weather bot running and says so.

History:
  Aug 19-28 2026: meshcore-bot crashed, hit systemd's start-limit-hit and sat dead for 9 days.
  Oct 31 - Nov 11 2026: the same thing again (failed Oct 31 13:06:56 EDT, found Nov 11).
  This watchdog existed the second time and said nothing. Found Nov 11: its Discord posts were
  rejected with HTTP 403 (the request had no User-Agent header, the same bug the repo already
  fixed in the other watchdogs), the script swallowed the failure and saved its state anyway,
  so it never retried. Fixed here: a User-Agent header, a send that reports success, and state
  that only changes after Discord accepts the post.

What it does now (run by a systemd timer, every 15 minutes):
  - Bot failed or inactive and /dev/kpc1 is present: `systemctl reset-failed` then `start`,
    wait, verify, post "restarted automatically". At most once per hour and twice per 24 h;
    over the limit it leaves the bot alone and says so.
  - Bot down and /dev/kpc1 missing: no restart (it would only fail again); one message, then a
    reminder every 12 hours.
  - Bot active again after an alert: one short "back up" message.
  - `touch /opt/meshcore-bot-watchdog/paused` stops automatic restarts (alerts still go out);
    AUTO_RECOVER=0 does the same permanently.
  - Never touches the bot while systemd is already restarting it ("activating").
  - After 07:30 local, reads the bot's own log (/etc/meshcore-bot/meshcore_bot.log) for today's
    "Daily weather forecast sent to CentralNJ-MC" line; if it is missing, ONE message that day.

Switches: --check (read-only, posts nothing), DRY_RUN=1 (full logic, prints instead of posting,
state untouched).

Deploy on cnjmesh1 only (where meshcore-bot runs, tied to /dev/kpc1). The webhook goes in a
systemd drop-in, never in the repo (see README.md).
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

STATE_FILE = os.environ.get("STATE_FILE", "/opt/meshcore-bot-watchdog/state.json")
PAUSE_FILE = os.environ.get("PAUSE_FILE", "/opt/meshcore-bot-watchdog/paused")
DEVICE = os.environ.get("MESHCORE_DEVICE", "/dev/kpc1")
SERVICE_NAME = "meshcore-bot"

DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")
AUTO_RECOVER = os.environ.get("AUTO_RECOVER", "1") == "1"
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
CHECK_ONLY = "--check" in sys.argv

# "Did the 7:05 forecast actually go out?" The bot writes its own log (not the journal). Verified Nov 12 2026
# from the real log: 07:05:00 "Sending daily weather forecast at 07:05:00", one "Sending channel message to
# CentralNJ-MC" + "Channel message sent" pair per chunk, then 07:05:12 "Daily weather forecast sent to CentralNJ-MC".
LOG_FILE = os.environ.get("MESHCORE_LOG", "/etc/meshcore-bot/meshcore_bot.log")
FORECAST_DEADLINE = (7, 30)  # local time; the check stays silent before this
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
FORECAST_STARTED = "Sending daily weather forecast"
FORECAST_SENT = "Daily weather forecast sent to CentralNJ-MC"

RECOVER_MIN_GAP = 60 * 60
RECOVER_MAX_PER_DAY = 2
RECOVER_SETTLE_SECONDS = int(os.environ.get("RECOVER_SETTLE_SECONDS", "20"))
REMINDER_SECONDS = 12 * 60 * 60


def get_hostname():
    return socket.gethostname()


def default_state():
    return {
        "down_alerted_at": None,    # epoch seconds of the last DOWN-type message Discord accepted
        "limit_alerted_at": None,   # last "restart limit / paused" message accepted
        "device_alerted_at": None,  # last "KPC1 missing" message accepted
        "recoveries": [],           # epoch seconds of automatic restarts in the last 24 h
        "forecast_ok_date": None,       # YYYY-MM-DD the log showed the forecast was sent (stops re-reading the log)
        "forecast_alerted_date": None,  # YYYY-MM-DD a "forecast did not go out" message was accepted
    }


def load_state():
    state = default_state()
    try:
        with open(STATE_FILE) as f:
            state.update(json.load(f))
    except Exception:  # noqa: BLE001 - a missing or old-format file just means defaults
        pass
    return state


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
        data=json.dumps({"content": message}).encode("utf-8"),
        # Discord answers 403 to requests with no User-Agent (this was the Nov 2026 failure).
        headers={"Content-Type": "application/json", "User-Agent": "cnjmesh-watchdog/1.0"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"Failed to post to Discord: {e}", file=sys.stderr)
        return False


def service_state(name=SERVICE_NAME):
    """systemctl is-active text: active, inactive, failed, activating, ... None if unreadable."""
    try:
        r = subprocess.run(["systemctl", "is-active", name], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or None
    except Exception as e:  # noqa: BLE001
        print(f"systemctl check failed: {e}", file=sys.stderr)
        return None


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
    """reset-failed, start, verify. Returns (ok, detail)."""
    if CHECK_ONLY or DRY_RUN:
        print(f"[{'check' if CHECK_ONLY else 'dry-run'}] would run: systemctl reset-failed + start {SERVICE_NAME}")
        return True, "dry run"
    try:
        subprocess.run(["systemctl", "reset-failed", SERVICE_NAME], capture_output=True, text=True, timeout=15)
        r = subprocess.run(["systemctl", "start", SERVICE_NAME], capture_output=True, text=True, timeout=60)
    except Exception as e:  # noqa: BLE001
        return False, f"systemctl failed: {e}"
    if r.returncode != 0:
        return False, f"systemctl start failed: {(r.stderr or r.stdout).strip()[:200]}"
    time.sleep(RECOVER_SETTLE_SECONDS)
    if service_state() != "active":
        return False, "it stopped again within a minute"
    return True, ""


def due(last, now):
    return last is None or now - last >= REMINDER_SECONDS


def forecast_status(today):
    """Look for today's forecast in the bot's log (the newest file, plus .1 in case it rotated mid-morning).

    Returns 'sent', 'started' (began but never logged the finish), 'none', or None if the log cannot be read."""
    started = sent = False
    for path, required in ((LOG_FILE + ".1", False), (LOG_FILE, True)):
        try:
            with open(path, "r", errors="replace") as f:
                for line in f:
                    line = ANSI_RE.sub("", line)  # the bot colours its log lines: "\x1b[32m2026-11-12 07:05:12 - ..."
                    if not line.startswith(today):
                        continue
                    if FORECAST_SENT in line:
                        sent = True
                    elif FORECAST_STARTED in line:
                        started = True
        except FileNotFoundError:
            if required:
                return None
        except Exception as e:  # noqa: BLE001
            print(f"could not read {path}: {e}", file=sys.stderr)
            if required:
                return None
    return "sent" if sent else ("started" if started else "none")


def check_forecast(host, state, st, now):
    """After FORECAST_DEADLINE, make sure the log shows today's forecast went out. One message per day."""
    lt = time.localtime(now)
    today = time.strftime("%Y-%m-%d", lt)
    if state["forecast_ok_date"] == today or state["forecast_alerted_date"] == today:
        return
    if (lt.tm_hour, lt.tm_min) < FORECAST_DEADLINE:
        return
    res = forecast_status(today)
    if res == "sent":
        state["forecast_ok_date"] = today
        return
    hh, mm = FORECAST_DEADLINE
    if res is None:
        msg = (f"\U0001F7E1 CNJMESH {host}: I could not read {LOG_FILE}, so I cannot tell whether today's 7:05 AM "
               f"CentralNJ-MC forecast went out. Check that the file exists and the watchdog (root) can read it.")
    elif res == "started":
        msg = (f"\U0001F534 CNJMESH {host}: today's 7:05 AM CentralNJ-MC forecast STARTED but never finished "
               f"(no 'Daily weather forecast sent' line in {LOG_FILE} by {hh:02d}:{mm:02d}). {SERVICE_NAME} is {st}. "
               f"Check: `tail -60 {LOG_FILE}`.")
    else:
        msg = (f"\U0001F534 CNJMESH {host}: today's 7:05 AM CentralNJ-MC forecast did NOT go out "
               f"(no forecast lines in {LOG_FILE} by {hh:02d}:{mm:02d}). {SERVICE_NAME} is {st}. "
               f"Check: `journalctl -u {SERVICE_NAME} -n 30 --no-pager` and `tail -60 {LOG_FILE}`.")
    if send_discord(msg):
        state["forecast_alerted_date"] = today


def main():
    host = get_hostname()
    state = load_state()
    now = time.time()

    st = service_state()
    if st is None:
        print(f"{host}: {SERVICE_NAME} check inconclusive (systemctl itself failed)")
        return

    if st == "active":
        if state["down_alerted_at"] is not None:
            if send_discord(f"CNJMESH {host}: {SERVICE_NAME} is back up and running"):
                state["down_alerted_at"] = None
                state["limit_alerted_at"] = None
                state["device_alerted_at"] = None
        else:
            state["limit_alerted_at"] = None
            state["device_alerted_at"] = None
    elif st == "activating":
        print(f"{host}: {SERVICE_NAME} is starting/restarting under systemd; leaving it alone")
    else:
        # failed, inactive, deactivating, or anything else that is not running
        if not os.path.exists(DEVICE):
            if due(state["device_alerted_at"], now):
                msg = (f"\U0001F534 CNJMESH {host}: {SERVICE_NAME} is {st} and {DEVICE} (KPC1, the radio "
                       f"it talks through) is missing, so I did NOT restart it. Check the USB cable and "
                       f"that the radio is powered. The 7:05 AM CentralNJ-MC forecast is stopped until then.")
                if send_discord(msg):
                    state["device_alerted_at"] = now
        else:
            ok, why = recovery_allowed(state, now)
            if ok:
                if not (CHECK_ONLY or DRY_RUN):
                    state["recoveries"].append(now)
                    save_state(state)  # record the attempt first so a crash cannot loop
                good, detail = restart_service()
                if good:
                    send_discord(f"✅ CNJMESH {host}: {SERVICE_NAME} was {st}; I restarted it automatically "
                                 f"and it is running. It will not auto-restart again for an hour.")
                    state["down_alerted_at"] = None  # the message above replaces a separate "back up"
                    state["limit_alerted_at"] = None
                    state["device_alerted_at"] = None
                else:
                    if send_discord(f"\U0001F534 CNJMESH {host}: {SERVICE_NAME} was {st}; I restarted it "
                                    f"automatically but {detail}. Needs you: "
                                    f"`journalctl -u {SERVICE_NAME} -n 30 --no-pager`."):
                        state["down_alerted_at"] = now
            elif due(state["limit_alerted_at"], now):
                msg = (f"\U0001F534 CNJMESH {host}: {SERVICE_NAME} is {st} and {DEVICE} is present, but I did "
                       f"not restart it: {why}. Needs you: `sudo systemctl reset-failed {SERVICE_NAME} && "
                       f"sudo systemctl start {SERVICE_NAME}`, then check "
                       f"`journalctl -u {SERVICE_NAME} -n 30 --no-pager`.")
                if send_discord(msg):
                    state["limit_alerted_at"] = now
                    state["down_alerted_at"] = now

    check_forecast(host, state, st, now)

    save_state(state)
    print(f"{host}: {SERVICE_NAME}={st} recoveries_24h={len(prune_recoveries(state, now))}")


if __name__ == "__main__":
    main()
