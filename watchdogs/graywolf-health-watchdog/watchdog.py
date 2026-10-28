#!/usr/bin/env python3
"""
graywolf-health-watchdog -- detects a deaf/mute K2GIA-1 and tries one cautious fix.

Why this exists (Oct 28 2026): Graywolf kept running ("active") while the
Digirig's USB audio chip had dropped off the bus and the PTT serial port threw
`ptt_key: TIOCMGET: EIO`. K2GIA-1 could neither hear nor transmit for 9+ hours
and nothing alerted. The older graywolf-watchdog only checks that the service is
up, and deliberately never restarts it (restarting every 5 min broke PTT).

What it checks (every run, read-only):
  1. The Digirig sound card is present in `arecord -l`.
  2. Graywolf has not logged `start_audio failed` in the last 10 minutes.
  3. Graywolf has not logged `ptt_key ... EIO` since its last start.
  4. A beacon was sent in the last 50 minutes (beacon interval is 30 min).

What it does about it (once per hour at most, 3 per day at most):
  - Sound card missing: soft-reset only the Digirig's own 2-port USB hub
    (unbind/bind in sysfs, guarded so it can never touch the Pi's own hubs),
    wait for the card, then restart graywolf so it reopens the devices.
  - Card present but audio/PTT errors: restart graywolf once.
  - Everything else (service down, no beacon, fix not allowed): alert only.
    Service-down stays the job of graywolf-watchdog.

Alerts (Discord), kept deliberately quiet:
  - ONE message when a new problem is found (it says what was tried).
  - Silence while the same problem persists.
  - A second message only if the problem comes back after an automatic fix
    ("did not work, needs you").
  - A short "recovered" message when a problem that needed a human clears
    (set RECOVERY_NOTICE=0 to disable).
  - The same reason set is never announced twice within ALERT_COOLDOWN_SECONDS.

Modes:
  python3 watchdog.py --check   read-only status print, no alerts, no fixes
  DRY_RUN=1 python3 watchdog.py   full logic, but prints instead of acting

Deploy on cnjmesh1 only, run as root (systemctl restart + sysfs writes).
Run via systemd timer, not a long-running daemon.
"""

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

STATE_FILE = os.environ.get("STATE_FILE", "/opt/graywolf-health-watchdog/state.json")
SERVICE = "graywolf"
ENV_FILE_WEBHOOK = "/opt/graywolf-discord/.env"  # holds DISCORD_WEBHOOK_INTERNET (never committed)

AUDIO_CARD_NAME = os.environ.get("AUDIO_CARD_NAME", "Device")
# The Digirig's serial chip (CP2102N). Its parent in sysfs is the Digirig's own hub.
DIGIRIG_SERIAL = os.environ.get("DIGIRIG_SERIAL", "beb31e2f33c6ef1186b171527a5e3baa")
DIGIRIG_SERIAL_VENDOR = "10c4"
DIGIRIG_HUB_ID = ("0424", "2412")  # Microchip/SMSC 2-port hub inside the Digirig

AUDIO_FAIL_WINDOW = 10 * 60        # audio errors older than this are history
BEACON_MAX_AGE = 50 * 60           # beacon interval is 30 min
MIN_UPTIME_FOR_BEACON_CHECK = 60 * 60
FIX_MIN_GAP = 60 * 60              # at most one fix attempt per hour
FIX_MAX_PER_DAY = 3
ALERT_COOLDOWN_SECONDS = 6 * 60 * 60
CARD_WAIT_SECONDS = 20

BEACON_CHECK = os.environ.get("BEACON_CHECK", "1") == "1"
RECOVERY_NOTICE = os.environ.get("RECOVERY_NOTICE", "1") == "1"
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")

CARD_RE = re.compile(r"^card \d+: " + re.escape(AUDIO_CARD_NAME) + r" \[", re.M)
PROC_CARD_RE = re.compile(r"\[\s*" + re.escape(AUDIO_CARD_NAME) + r"\s*\]")  # /proc/asound/cards


# ----------------------------------------------------------------- helpers

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
        "state": "ok",            # ok | degraded
        "reasons": [],
        "fix_attempts": [],       # epoch seconds
        "last_alert": {},         # reasons-key -> epoch seconds
        "post_fix_watch": False,  # a fix was attempted; a repeat means the fix failed
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
    if DRY_RUN:
        return
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def get_webhook():
    if DISCORD_WEBHOOK_URL and DISCORD_WEBHOOK_URL != "REPLACE_ME":
        return DISCORD_WEBHOOK_URL
    try:
        with open(ENV_FILE_WEBHOOK) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DISCORD_WEBHOOK_INTERNET="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:  # noqa: BLE001
        pass
    return None


def send_discord(message):
    if DRY_RUN:
        print("[dry-run] would send to Discord:", message)
        return
    url = get_webhook()
    if not url:
        print("Discord webhook not configured, would have sent:", message)
        return
    payload = json.dumps({"content": message}).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "cnjmesh-watchdog/1.0"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:  # noqa: BLE001
        print(f"Failed to post to Discord: {e}", file=sys.stderr)


# ------------------------------------------------------- journal analysis

def parse_journal(text):
    """Parse `journalctl -o short-unix` output into [(epoch, message)]."""
    events = []
    for line in text.splitlines():
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        try:
            ts = float(parts[0])
        except ValueError:
            continue
        events.append((ts, parts[1]))
    return events


def analyze(events, now):
    """Pure function: journal events -> facts about Graywolf's health."""
    start_ts = 0.0
    for ts, msg in events:
        if 'msg="modem ready"' in msg or 'msg="starting component"' in msg:
            start_ts = max(start_ts, ts)
    ptt_eio = [ts for ts, msg in events if ts >= start_ts and "ptt_key" in msg and "EIO" in msg]
    audio_fail = [ts for ts, msg in events
                  if ts >= now - AUDIO_FAIL_WINDOW and "start_audio failed" in msg]
    beacons = [ts for ts, msg in events if 'msg="beacon sent"' in msg]
    return {
        "start_ts": start_ts,
        "ptt_eio_count": len(ptt_eio),
        "audio_fail_recent": len(audio_fail),
        "last_beacon_ts": max(beacons) if beacons else 0.0,
    }


def problems_from(card_present, facts, now):
    problems = []
    if not card_present:
        problems.append("audio-card-missing")
    if facts["audio_fail_recent"] > 0:
        problems.append("audio-start-failed")
    if facts["ptt_eio_count"] > 0:
        problems.append("ptt-error")
    if BEACON_CHECK:
        uptime = now - facts["start_ts"] if facts["start_ts"] else 10 ** 9
        age = now - facts["last_beacon_ts"] if facts["last_beacon_ts"] else 10 ** 9
        if uptime > MIN_UPTIME_FOR_BEACON_CHECK and age > BEACON_MAX_AGE:
            problems.append("no-beacon")
    return problems


# -------------------------------------------------------- system probes

def service_active():
    rc, out = run(["systemctl", "is-active", SERVICE])
    return out.strip() == "active"


def card_present():
    """True if the Digirig's sound card is registered with ALSA.

    Reads /proc/asound/cards (no subprocess). Falls back to `arecord -l` only if
    that file cannot be read, so a missing tool can never look like a missing card
    and trigger a needless USB reset."""
    try:
        with open("/proc/asound/cards") as f:
            return bool(PROC_CARD_RE.search(f.read()))
    except Exception:  # noqa: BLE001
        rc, out = run(["arecord", "-l"])
        return bool(CARD_RE.search(out))


def read_journal():
    rc, out = run(["journalctl", "-u", SERVICE, "--since", "4 hours ago",
                   "-o", "short-unix", "--no-pager", "-q"], timeout=60)
    return parse_journal(out)


def _sysfs(name, attr):
    try:
        with open(f"/sys/bus/usb/devices/{name}/{attr}") as f:
            return f.read().strip()
    except Exception:  # noqa: BLE001
        return None


def find_digirig_hub():
    """Return the sysfs name of the Digirig's own hub (e.g. '1-1.3'), or None.

    Safety: found by the CP2102N serial number, and the parent must be the
    0424:2412 2-port hub. Anything else returns None, so we can never unbind
    the Pi's own hubs by mistake."""
    try:
        names = os.listdir("/sys/bus/usb/devices")
    except Exception:  # noqa: BLE001
        return None
    for name in names:
        if _sysfs(name, "serial") == DIGIRIG_SERIAL and _sysfs(name, "idVendor") == DIGIRIG_SERIAL_VENDOR:
            if "." not in name:
                return None
            hub = name.rsplit(".", 1)[0]
            if (_sysfs(hub, "idVendor"), _sysfs(hub, "idProduct")) == DIGIRIG_HUB_ID:
                return hub
            return None
    return None


# ------------------------------------------------------------- fix steps

def soft_reset_hub(hub):
    """Unbind and rebind the Digirig's hub in sysfs (a software 'replug')."""
    if DRY_RUN:
        print(f"[dry-run] would unbind/bind USB hub {hub}")
        return True
    try:
        with open("/sys/bus/usb/drivers/usb/unbind", "w") as f:
            f.write(hub)
        time.sleep(3)
        with open("/sys/bus/usb/drivers/usb/bind", "w") as f:
            f.write(hub)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"hub reset failed: {e}", file=sys.stderr)
        return False


def wait_for_card(seconds):
    if DRY_RUN:
        return True
    deadline = time.time() + seconds
    while time.time() < deadline:
        if card_present():
            return True
        time.sleep(2)
    return card_present()


def restart_graywolf():
    if DRY_RUN:
        print("[dry-run] would run: systemctl restart graywolf")
        return True
    rc, _ = run(["systemctl", "restart", SERVICE], timeout=60)
    time.sleep(8)
    return rc == 0 and service_active()


def fix_allowed(state, now):
    attempts = [t for t in state["fix_attempts"] if now - t < 24 * 3600]
    state["fix_attempts"] = attempts
    if attempts and now - max(attempts) < FIX_MIN_GAP:
        return False, "last automatic fix was less than an hour ago"
    if len(attempts) >= FIX_MAX_PER_DAY:
        return False, f"already tried {FIX_MAX_PER_DAY} automatic fixes in 24 h"
    return True, ""


def attempt_fix(problems, state, now):
    """Returns (actions_taken: [str], card_ok_after: bool)."""
    actions = []
    state["fix_attempts"].append(now)
    card_ok = card_present()
    if "audio-card-missing" in problems:
        hub = find_digirig_hub()
        if hub is None:
            actions.append("could not locate the Digirig's USB hub (serial chip also missing), so no soft reset")
            return actions, False
        ok = soft_reset_hub(hub)
        actions.append(f"soft-reset the Digirig USB hub {hub} ({'ok' if ok else 'failed'})")
        card_ok = wait_for_card(CARD_WAIT_SECONDS)
        actions.append("sound card came back" if card_ok else "sound card still missing")
        if not card_ok:
            return actions, False
    ok = restart_graywolf()
    actions.append(f"restarted graywolf ({'ok' if ok else 'failed'})")
    return actions, card_ok and ok


# ------------------------------------------------------------ messages

def reasons_text(problems):
    names = {
        "audio-card-missing": "Digirig sound card missing",
        "audio-start-failed": "Graywolf cannot open the audio device",
        "ptt-error": "PTT serial error (ptt_key EIO), radio likely not keying",
        "no-beacon": "no beacon sent in the last 50 minutes",
    }
    return "; ".join(names.get(p, p) for p in problems)


def cooldown_ok(state, key, now):
    return now - state["last_alert"].get(key, 0) >= ALERT_COOLDOWN_SECONDS


# ----------------------------------------------------------------- main

def evaluate(now):
    facts = analyze(read_journal(), now)
    present = card_present()
    return present, facts, problems_from(present, facts, now)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    host = get_hostname()
    now = time.time()

    if not service_active():
        print(f"{host}: {SERVICE} is not active; graywolf-watchdog handles that. Nothing to do.")
        return 0

    present, facts, problems = evaluate(now)
    print(f"{host}: card_present={present} ptt_eio={facts['ptt_eio_count']} "
          f"audio_fail_recent={facts['audio_fail_recent']} "
          f"last_beacon_age={int(now - facts['last_beacon_ts']) if facts['last_beacon_ts'] else 'none'}s "
          f"problems={problems or 'none'}")
    if "--check" in argv:
        return 0

    state = load_state()
    key = ",".join(sorted(problems))

    if not problems:
        if state["state"] == "degraded" and RECOVERY_NOTICE:
            send_discord(f"✅ CNJMESH {host}: K2GIA-1 (Graywolf) is healthy again.")
        state["state"] = "ok"
        state["reasons"] = []
        # A clean beacon after the last fix proves the fix held; a later problem is a fresh incident.
        if state["post_fix_watch"] and facts["last_beacon_ts"] > max(state["fix_attempts"] or [0]):
            state["post_fix_watch"] = False
        save_state(state)
        return 0

    if state["state"] == "degraded":
        # Same incident still open: already told Charlie, stay quiet.
        state["reasons"] = problems
        save_state(state)
        return 0

    # New incident (state was ok).
    allowed, why_not = fix_allowed(state, now)
    repeat_after_fix = state["post_fix_watch"]

    if allowed and not repeat_after_fix and any(p != "no-beacon" for p in problems):
        actions, healthy = attempt_fix(problems, state, now)
        state["post_fix_watch"] = True
        if healthy:
            msg = (f"\U0001F7E1 CNJMESH {host}: K2GIA-1 problem found ({reasons_text(problems)}). "
                   f"Automatic fix: {'; '.join(actions)}. Sound card and Graywolf look healthy; "
                   f"PTT will be confirmed at the next beacon. No action needed unless you get another alert.")
            if cooldown_ok(state, key, now):
                send_discord(msg)
                state["last_alert"][key] = now
            state["state"] = "ok"
        else:
            msg = (f"\U0001F534 CNJMESH {host}: K2GIA-1 problem ({reasons_text(problems)}). "
                   f"Automatic fix tried: {'; '.join(actions)} -- it did not clear the problem. "
                   f"Needs you: turn the UV-5R M off, replug the Digirig USB (try a different Pi port if it "
                   f"repeats), then `sudo systemctl restart graywolf`. K2GIA-1 is probably deaf and mute until then. "
                   f"No more alerts until it recovers.")
            send_discord(msg)
            state["last_alert"][key] = now
            state["state"] = "degraded"
    else:
        reason = ("the problem returned after an automatic fix" if repeat_after_fix
                  else (why_not or "no automatic fix applies to this problem"))
        msg = (f"\U0001F534 CNJMESH {host}: K2GIA-1 problem ({reasons_text(problems)}); {reason}. "
               f"Needs you: check the Digirig USB and radio, then `sudo systemctl restart graywolf`. "
               f"No more alerts until it recovers.")
        send_discord(msg)
        state["last_alert"][key] = now
        state["state"] = "degraded"

    state["reasons"] = problems
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
