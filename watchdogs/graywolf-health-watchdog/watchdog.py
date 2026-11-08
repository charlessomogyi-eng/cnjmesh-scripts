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

Stuck-transmitter guard (added Oct 31 2026): a failed `ptt_unkey` means the
release of the transmit key may never have reached the radio, and the radio
stays keyed (it happened: red TX light non-stop after `ptt_unkey: TIOCMGET:
EPROTO`). So a failed `ptt_unkey` is treated as an emergency, not a normal
problem: graywolf is STOPPED at once (never restarted: a restart sends a beacon
30 s later, which can repeat the fault), the Digirig's hub is soft-reset so its
serial chip drops the key line, and a loud alert says to look at the radio.
  - `--guard` runs forever (own systemd service, graywolf-ptt-guard.service),
    follows the graywolf journal and reacts within about a second.
  - The 5-minute timer run does the same if it ever finds an unkey error the
    guard missed (belt and braces).
  - It also pauses graywolf-watchdog.timer and graywolf-discord-watchdog.timer
    (PAUSE_TIMERS): the second restarts the Discord bridge, which Requires
    graywolf, so it would start the transmitter again within 5 minutes (it did
    on Oct 31 at 21:48). The alert gives ONE resume command that starts
    graywolf, the bridge and both timers once a human has looked at the radio.
Guarded auto-recovery (added Nov 8 2026, guard only; the 5-minute check never does it): after the
emergency stop the guard waits RECOVER_WAIT_SECONDS (180), confirms the Digirig's sound card is back,
then starts graywolf, the bridge and the two timers ONCE and tells Discord. A repeat fault inside an
hour, or a third in 24 h, keeps everything stopped with the one resume command (the Oct 31 restarts
that beacon-and-faulted again are why this is capped). A human who resumes first is respected.
AUTO_RECOVER=0 (drop-in) switches it off. Counters live in RECOVERY_FILE.
Backstop outside software: set the radio's time-out timer (TOT) to its shortest option.

Modes:
  python3 watchdog.py --check   read-only status print, no alerts, no fixes
  DRY_RUN=1 python3 watchdog.py   full logic, but prints instead of acting
  python3 watchdog.py --guard   long-running stuck-transmitter guard (systemd service)
  python3 watchdog.py --guard-selftest   dry-run the guard's matching and actions, touches nothing

Deploy on cnjmesh1 only, run as root (systemctl restart + sysfs writes).
Run via systemd timer, not a long-running daemon.
"""

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request

STATE_FILE = os.environ.get("STATE_FILE", "/opt/graywolf-health-watchdog/state.json")
SERVICE = "graywolf"
BRIDGE_SERVICE = "graywolf-discord.service"  # Requires=graywolf.service, so it goes down with it
# Older timers that could undo an emergency stop: graywolf-discord-watchdog restarts the Discord
# bridge every 5 min, and because the bridge Requires=graywolf, that restarts graywolf (a
# transmitter) too (it undid the stop on Oct 31 at 21:48). The emergency stop pauses both.
PAUSE_TIMERS = os.environ.get(
    "PAUSE_TIMERS", "graywolf-watchdog.timer graywolf-discord-watchdog.timer").split()
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
# Graywolf logs e.g. "graywolf-modem: TransmitFrame: ptt_key: TIOCMGET: EIO: I/O error"
# and "graywolf-modem: TransmitFrame: ptt_unkey: TIOCMGET: EPROTO: Protocol error".
# Any errno name counts (EIO, EPROTO, ENODEV, ...). "ptt_key" does not match "ptt_unkey".
PTT_KEY_ERR_RE = re.compile(r"ptt_key: [^\n]*?\b(E[A-Z0-9]{2,})\b")
PTT_UNKEY_ERR_RE = re.compile(r"ptt_unkey: [^\n]*?\b(E[A-Z0-9]{2,})\b")
GUARD_DEBOUNCE_SECONDS = 60
# Guarded auto-recovery (added Nov 8 2026). After the guard has stopped graywolf it waits, checks the
# Digirig is back, and starts graywolf ONCE. Capped so a radio that keeps faulting is never keyed
# in a loop: at most one automatic start per RECOVER_MIN_GAP and RECOVER_MAX_PER_DAY per 24 h,
# counted across guard restarts (RECOVERY_FILE). Switch off with AUTO_RECOVER=0.
AUTO_RECOVER = os.environ.get("AUTO_RECOVER", "1") == "1"
RECOVER_WAIT_SECONDS = int(os.environ.get("RECOVER_WAIT_SECONDS", "180"))   # radio TOT is 30 s
RECOVER_CARD_WAIT_SECONDS = int(os.environ.get("RECOVER_CARD_WAIT_SECONDS", "300"))
RECOVER_MIN_GAP = 60 * 60
RECOVER_MAX_PER_DAY = 2
RECOVERY_FILE = os.environ.get("RECOVERY_FILE", "/opt/graywolf-health-watchdog/guard-recovery.json")
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
    ptt_eio = [ts for ts, msg in events if ts >= start_ts and PTT_KEY_ERR_RE.search(msg)]
    unkey = []
    for ts, msg in events:
        m = PTT_UNKEY_ERR_RE.search(msg) if ts >= start_ts else None
        if m:
            unkey.append((ts, m.group(1)))
    audio_fail = [ts for ts, msg in events
                  if ts >= now - AUDIO_FAIL_WINDOW and "start_audio failed" in msg]
    beacons = [ts for ts, msg in events if 'msg="beacon sent"' in msg]
    return {
        "start_ts": start_ts,
        "ptt_eio_count": len(ptt_eio),
        "ptt_unkey_error_count": len(unkey),
        "ptt_unkey_errno": unkey[-1][1] if unkey else "",
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
    if facts.get("ptt_unkey_error_count", 0) > 0:
        problems.append("ptt-unkey-error")
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


def stop_graywolf():
    if DRY_RUN:
        print("[dry-run] would run: systemctl stop graywolf")
        return True
    rc, _ = run(["systemctl", "stop", SERVICE], timeout=60)
    return rc == 0


def pause_timers():
    """Stop the older watchdog timers so nothing restarts graywolf behind the stop.

    Returns [(unit, ok)]. They also come back by themselves at reboot, or through
    resume_command()."""
    results = []
    for unit in PAUSE_TIMERS:
        if DRY_RUN:
            print(f"[dry-run] would run: systemctl stop {unit}")
            results.append((unit, True))
            continue
        rc, _ = run(["systemctl", "stop", unit], timeout=30)
        results.append((unit, rc == 0))
    return results


def resume_command():
    """The ONE command that undoes an emergency stop, for a human to run after looking at the radio.

    Starts graywolf, the Discord bridge (stopped with it, because it Requires graywolf)
    and the paused timers."""
    return "sudo systemctl start " + " ".join([f"{SERVICE}.service", BRIDGE_SERVICE] + PAUSE_TIMERS)


def emergency_stop(host, errno_name, source, recover_note=None):
    """Stuck-transmitter safeguard: stop graywolf, pause the timers that could restart it,
    reset the Digirig hub, alert loudly.

    Never restarts graywolf: a restart sends a beacon within 30 s, which can repeat
    the fault. A human restarts it after looking at the radio, or (guard only, capped, see
    recovery_allowed) recover_graywolf() starts it once after a wait. recover_note is the
    sentence the alert uses to say which of the two applies."""
    actions = []
    ok = stop_graywolf()
    actions.append(f"stopped graywolf ({'ok' if ok else 'FAILED'})")
    paused = pause_timers()
    failed = [u for u, ok_ in paused if not ok_]
    if failed:
        actions.append(f"could NOT pause {', '.join(failed)} (it may restart graywolf: stop it by hand)")
    elif paused:
        actions.append(f"paused {', '.join(u for u, _ in paused)} so nothing restarts graywolf behind the stop")
    hub = find_digirig_hub()
    if hub is None:
        actions.append("could not locate the Digirig's USB hub, so no USB reset")
    else:
        ok2 = soft_reset_hub(hub)
        actions.append(f"reset the Digirig USB hub {hub} ({'ok' if ok2 else 'failed'})")
    send_discord(
        f"\U0001F6A8 CNJMESH {host}: K2GIA-1 could not release PTT ({errno_name or 'error'}; {source}), "
        f"so the radio may be stuck transmitting. Automatic action: {'; '.join(actions)}. "
        f"Look at the radio now: if its red TX light is on, turn it off. "
        + (f"{recover_note} To resume right now, after looking at the radio: `{resume_command()}`"
           if recover_note else
           f"Graywolf stays stopped (no automatic restart). Once you have looked at the radio, "
           f"this one command resumes everything: `{resume_command()}`"))
    return actions


def load_recoveries(now):
    """Epoch seconds of automatic starts in the last 24 h. Unreadable file = none."""
    try:
        with open(RECOVERY_FILE) as f:
            return [t for t in json.load(f) if isinstance(t, (int, float)) and now - t < 24 * 3600]
    except Exception:  # noqa: BLE001
        return []


def save_recoveries(times):
    if DRY_RUN:
        return
    try:
        os.makedirs(os.path.dirname(RECOVERY_FILE), exist_ok=True)
        with open(RECOVERY_FILE, "w") as f:
            json.dump(times, f)
    except Exception as e:  # noqa: BLE001
        print(f"could not save {RECOVERY_FILE}: {e}", file=sys.stderr, flush=True)


def recovery_allowed(now):
    """(ok, why-not). One automatic start per hour, two per day, and only if switched on."""
    if not AUTO_RECOVER:
        return False, "automatic restart is switched off (AUTO_RECOVER=0)"
    times = load_recoveries(now)
    if times and now - max(times) < RECOVER_MIN_GAP:
        return False, "it was already restarted automatically less than an hour ago, so this is a repeat"
    if len(times) >= RECOVER_MAX_PER_DAY:
        return False, f"it was already restarted automatically {RECOVER_MAX_PER_DAY} times in 24 h"
    return True, ""


def recovery_note(now):
    ok, why = recovery_allowed(now)
    if ok:
        return (f"Graywolf will be started again automatically in about {RECOVER_WAIT_SECONDS // 60} "
                f"minutes if the Digirig is back (at most once an hour, {RECOVER_MAX_PER_DAY} a day; "
                f"a repeat fault inside the hour keeps it stopped)."), True
    return f"Graywolf stays stopped (no automatic restart: {why}).", False


def recover_graywolf(host):
    """Wait, check the Digirig is back, start graywolf once, tell Charlie. Never loops.

    Runs in a thread started by the guard right after emergency_stop. If the fault comes back
    the guard stops graywolf again and recovery_allowed() then refuses, so it stays stopped."""
    if not DRY_RUN:
        time.sleep(RECOVER_WAIT_SECONDS)
    if service_active():
        return "someone already started graywolf"  # a human got there first: do nothing
    if not wait_for_card(RECOVER_CARD_WAIT_SECONDS):
        send_discord(f"\u26A0\uFE0F CNJMESH {host}: K2GIA-1 is still stopped. The Digirig's sound card did "
                     f"not come back after the USB reset, so no automatic restart. Check the Digirig USB "
                     f"and radio, then: `{resume_command()}`")
        return "digirig missing"
    now = time.time()
    ok, why = recovery_allowed(now)  # re-check: the counters may have changed while we waited
    if not ok:
        send_discord(f"\u26A0\uFE0F CNJMESH {host}: K2GIA-1 stays stopped ({why}). "
                     f"After looking at the radio: `{resume_command()}`")
        return "not allowed"
    save_recoveries(load_recoveries(now) + [now])  # count it before starting, so a crash cannot loop
    if DRY_RUN:
        print("[dry-run] would run:", " ".join(["systemctl", "start"] + _recover_units()))
        ok_start = True
    else:
        rc, _ = run(["systemctl", "start"] + _recover_units(), timeout=60)
        time.sleep(8)
        ok_start = rc == 0 and service_active()
    if ok_start:
        send_discord(f"\u2705 CNJMESH {host}: K2GIA-1 was started again automatically after the PTT fault "
                     f"(Digirig back). The guard is still armed: if the fault repeats within the hour "
                     f"graywolf is stopped again and stays stopped.")
        return "started"
    send_discord(f"\u26A0\uFE0F CNJMESH {host}: automatic restart of graywolf FAILED. After looking at "
                 f"the radio: `{resume_command()}`")
    return "start failed"


def _recover_units():
    return [f"{SERVICE}.service", BRIDGE_SERVICE] + PAUSE_TIMERS


_recovery_thread = None


def start_recovery_thread(host):
    """Start recover_graywolf in the background unless one is already waiting."""
    global _recovery_thread
    if _recovery_thread is not None and _recovery_thread.is_alive():
        return
    _recovery_thread = threading.Thread(target=recover_graywolf, args=(host,), daemon=True)
    _recovery_thread.start()


def guard_match(text):
    """Return the errno name if this journal line is a failed ptt_unkey, else None."""
    m = PTT_UNKEY_ERR_RE.search(text)
    return m.group(1) if m else None


def guard_loop():
    """Long-running: follow the graywolf journal and react to a failed PTT release."""
    host = get_hostname()
    last = 0.0
    print(f"{host}: ptt-guard watching {SERVICE} for failed PTT release", flush=True)
    while True:
        try:
            proc = subprocess.Popen(
                ["journalctl", "-u", SERVICE, "-f", "-n", "0", "-o", "cat", "--no-pager", "-q"],
                stdout=subprocess.PIPE, text=True, bufsize=1)
            for text in proc.stdout:
                errno_name = guard_match(text)
                if errno_name and time.time() - last >= GUARD_DEBOUNCE_SECONDS:
                    last = time.time()
                    note, allowed = recovery_note(last)
                    emergency_stop(host, errno_name, "seen live by the ptt guard", recover_note=note)
                    if allowed:
                        start_recovery_thread(host)
            proc.wait()
        except Exception as e:  # noqa: BLE001 - the guard must keep running
            print(f"guard error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        time.sleep(2)


def guard_selftest():
    """Dry run: shows what the guard would match and do. Touches nothing."""
    global DRY_RUN
    DRY_RUN = True
    samples = [
        ("graywolf-modem: TransmitFrame: ptt_unkey: TIOCMGET: EPROTO: Protocol error", True),
        ("graywolf-modem: TransmitFrame: ptt_unkey: TIOCMGET: EIO: I/O error", True),
        ("graywolf-modem: TransmitFrame: ptt_key: TIOCMGET: EIO: I/O error", False),
        ('level=INFO msg="beacon sent" component=beacon id=1', False),
    ]
    ok = True
    for text, expect in samples:
        got = guard_match(text)
        good = bool(got) == expect
        ok = ok and good
        print(f"{'OK ' if good else 'BAD'} match={got!r:10} {text}")
    print("--- what the guard would do on a failed ptt_unkey:")
    emergency_stop(get_hostname(), "EPROTO", "self-test")
    return 0 if ok else 1


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
        "ptt-unkey-error": "PTT release failed, the radio may have been left transmitting",
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

    if "--guard" in argv:
        guard_loop()
        return 0
    if "--guard-selftest" in argv:
        return guard_selftest()

    if not service_active():
        print(f"{host}: {SERVICE} is not active; graywolf-watchdog handles that. Nothing to do.")
        return 0

    present, facts, problems = evaluate(now)
    print(f"{host}: card_present={present} ptt_eio={facts['ptt_eio_count']} "
          f"ptt_unkey_err={facts['ptt_unkey_error_count']} "
          f"audio_fail_recent={facts['audio_fail_recent']} "
          f"last_beacon_age={int(now - facts['last_beacon_ts']) if facts['last_beacon_ts'] else 'none'}s "
          f"problems={problems or 'none'}")
    if "--check" in argv:
        return 0

    state = load_state()
    key = ",".join(sorted(problems))

    if "ptt-unkey-error" in problems:
        # Stuck-transmitter risk: stop and alert, never restart (see emergency_stop).
        emergency_stop(host, facts.get("ptt_unkey_errno", ""), "found by the periodic check")
        state["state"] = "degraded"
        state["reasons"] = problems
        save_state(state)
        return 0

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
