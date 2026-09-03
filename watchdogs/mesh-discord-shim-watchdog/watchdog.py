#!/usr/bin/env python3
"""
mesh-discord-shim health watchdog.

mesh-discord-shim is a Docker container (NOT systemd) that watches MeshCore
Observer events (pubkey a8c40bf3 -- advertisement / channel_msg_recv) and
posts them to Discord. Confirmed MeshCore-specific, unrelated to Meshtastic
or APRS (verified via live logs, Sep 2 2026).

Two independent checks, same "alert only on state change" pattern as the
other watchdogs in this repo:

1. CONTAINER STATE -- is the container actually running at all (Docker
   equivalent of `systemctl is-active`). Hard down/up signal.

2. LOG FRESHNESS -- has it logged ANY event in the lookback window. This is
   a heuristic, not a heartbeat file (mesh-discord-shim doesn't have one) --
   unlike the APRS dead-air check we deliberately rejected (message *volume*
   isn't a reliable Graywolf health signal), MeshCore advertisement events
   are frequent/automatic (observed multiple per minute during normal
   operation), so total silence for the full window is a much stronger
   signal than APRS silence ever was. Threshold is intentionally generous
   to avoid false alarms -- tune STALE_THRESHOLD_SECONDS up if it ever
   fires during genuinely normal quiet periods.

Deploy on cnjmesh1 only (where this container runs).
Run via systemd timer, not a long-running daemon.
Requires the invoking user to have docker access (same user that runs
`docker ps`/`docker logs` interactively on cnjmesh1).
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

STATE_FILE = "/opt/mesh-discord-shim-watchdog/state.json"
CONTAINER_NAME = "mesh-discord-shim"
ALERT_COOLDOWN_SECONDS = 24 * 60 * 60  # never re-alert the same condition more than once/day

DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")

# Generous on purpose -- see module docstring. Advertisement events were
# observed multiple times per minute during normal operation Sep 2 2026,
# so 30 minutes of total silence is a strong signal, not routine quiet.
STALE_THRESHOLD_SECONDS = 30 * 60


def get_hostname():
    return os.environ.get("NODE_LABEL", socket.gethostname())


def default_state():
    return {"container_state": "ok", "log_state": "ok", "log_last_alert": 0, "container_last_alert": 0}


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


def check_container_running():
    """Returns (running: bool, error: str|None)."""
    try:
        out = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0:
            return False, "container not found (docker inspect failed -- may not exist or Docker unreachable)"
        return out.stdout.strip() == "true", None
    except Exception as e:
        return False, f"docker inspect error: {e}"


def check_log_freshness():
    """Returns (has_recent_activity: bool, error: str|None). Counts log
    lines within the lookback window -- any line at all counts as fresh."""
    lookback_min = STALE_THRESHOLD_SECONDS // 60
    try:
        out = subprocess.run(
            ["docker", "logs", "--since", f"{lookback_min}m", CONTAINER_NAME],
            capture_output=True, text=True, timeout=15,
        )
        if out.returncode != 0:
            return False, "docker logs failed (container not found or Docker unreachable)"
        lines = [l for l in (out.stdout + out.stderr).splitlines() if l.strip()]
        return len(lines) > 0, None
    except Exception as e:
        return False, f"docker logs error: {e}"


def main():
    host = get_hostname()
    state = load_state()
    summary_parts = []

    # --- Container running state ---
    running, err = check_container_running()
    container_state = "ok" if running else "down"
    if container_state != state["container_state"] and cooldown_ok(state, "container_last_alert"):
        if container_state == "ok":
            send_discord(f"CNJMESH {host}: mesh-discord-shim container back up")
        else:
            detail = f" ({err})" if err else ""
            send_discord(f"\U0001F534 CNJMESH {host}: mesh-discord-shim container is DOWN{detail} -- MeshCore new-node/advertisement alerts to Discord have stopped. Check `docker ps` / `docker logs {CONTAINER_NAME}`.")
        state["container_last_alert"] = time.time()
    state["container_state"] = container_state
    summary_parts.append(f"container={container_state}")

    # --- Log freshness (only meaningful if container is actually running) ---
    if running:
        fresh, log_err = check_log_freshness()
        log_state = "ok" if fresh else "stale"
        if log_state != state["log_state"] and cooldown_ok(state, "log_last_alert"):
            if log_state == "ok":
                send_discord(f"CNJMESH {host}: mesh-discord-shim activity resumed")
            else:
                detail = f" ({log_err})" if log_err else ""
                send_discord(f"\U0001F7E1 CNJMESH {host}: mesh-discord-shim has logged NO events in {STALE_THRESHOLD_SECONDS // 60} min{detail} -- container is up but may be stuck (e.g. lost connection to MeshCore Observer/MQTT). Check `docker logs {CONTAINER_NAME}`.")
            state["log_last_alert"] = time.time()
        state["log_state"] = log_state
        summary_parts.append(f"log={log_state}")
    else:
        # Don't double-alert on log staleness when we already know the container is down.
        state["log_state"] = "ok"
        summary_parts.append("log=skipped(container down)")

    save_state(state)
    print(f"{host}: " + " ".join(summary_parts))


if __name__ == "__main__":
    main()
