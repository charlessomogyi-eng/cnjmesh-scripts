#!/usr/bin/env python3
"""
CNJ Mesh broker ingest-rate watchdog.

Checks packets/hour landing in Malla's packet_history table. This is the
highest-value watchdog per docs/PREVENTION-AND-INCIDENT-RUNBOOK.md -- it
directly detects the failure class (unbounded ingestion / a flooding node)
that caused the Jul-Aug 2026 saga and the Aug 14-16 loop-node repeat.
Alerts to Discord only on state change, matching disk-temp-watchdog's pattern.

Deploy on cnjmesh1 only (where Malla's DB lives).
Run via systemd timer, not a long-running daemon.
"""

import json
import os
import socket
import sqlite3
import sys
import time
import urllib.request

STATE_FILE = "/opt/ingest-rate-watchdog/state.json"
ALERT_COOLDOWN_SECONDS = 24 * 60 * 60  # never re-alert the same condition more than once/day
DB_PATH = "/var/lib/docker/volumes/mqtt_malla_data/_data/meshtastic_history.db"

DISCORD_WEBHOOK_URL = os.environ.get("CNJ_DISCORD_WEBHOOK", "REPLACE_ME")

# Normal CentralNJ-area traffic observed Aug 15, 2026 (post-cleanup, steady
# state): ~50-70 pkts/hr overall. Flood incidents historically ran in the
# tens of thousands/hr (68,000/hr at the worst point). Thresholds set well
# above normal daily variance, well below any real flood.
WARN_PER_HOUR = 1000
URGENT_PER_HOUR = 5000

# A single node dominating ingest is the exact signature of every loop-node
# incident found so far (!699a9390, !698574b0, !db51bb30 all showed one
# node hugely over-represented vs. the rest of the mesh combined).
SINGLE_NODE_WARN_PCT = 50


def get_hostname():
    return os.environ.get("NODE_LABEL", socket.gethostname())


def classify(value, warn, urgent):
    if value >= urgent:
        return "urgent"
    if value >= warn:
        return "warning"
    return "ok"


def default_state():
    return {
        "rate_state": "ok", "hot_node_state": "ok",
        "rate_last_alert": 0, "hot_node_last_alert": 0,
    }


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
    """True if enough time has passed since the last alert of this kind."""
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


def query_db():
    """
    Returns (total_last_hour, top_node_id, top_node_count) or
    (None, None, None) if the DB can't be read (e.g. locked, missing).
    """
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=10)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM packet_history "
            "WHERE timestamp > strftime('%s', 'now', '-1 hour')"
        )
        total = cur.fetchone()[0]

        cur.execute(
            "SELECT from_node_id, COUNT(*) as cnt FROM packet_history "
            "WHERE timestamp > strftime('%s', 'now', '-1 hour') "
            "GROUP BY from_node_id ORDER BY cnt DESC LIMIT 1"
        )
        row = cur.fetchone()
        conn.close()
        top_node, top_count = (row[0], row[1]) if row else (None, 0)
        return total, top_node, top_count
    except Exception as e:
        print(f"DB read failed: {e}", file=sys.stderr)
        return None, None, None


def main():
    host = get_hostname()
    state = load_state()

    total, top_node, top_count = query_db()
    if total is None:
        print(f"{host}: ingest-rate check failed (DB unreadable)")
        return

    rate_state = classify(total, WARN_PER_HOUR, URGENT_PER_HOUR)
    if rate_state != state["rate_state"] and cooldown_ok(state, "rate_last_alert"):
        if rate_state == "ok":
            send_discord(f"CNJMESH {host}: Broker ingest rate back to normal ({total} pkts/hr)")
        else:
            icon = "\U0001F534" if rate_state == "urgent" else "\U0001F7E1"
            send_discord(f"{icon} CNJMESH {host}: Broker ingest rate {rate_state.upper()} ({total} pkts/hr, normal ~50-200/hr) -- check for a flooding/looping node")
        state["rate_last_alert"] = time.time()
    state["rate_state"] = rate_state

    top_pct = round((top_count / total) * 100, 1) if total > 0 else 0
    hot_node_state = "warning" if top_pct >= SINGLE_NODE_WARN_PCT and total >= 20 else "ok"
    if hot_node_state != state["hot_node_state"] and cooldown_ok(state, "hot_node_last_alert"):
        if hot_node_state == "ok":
            send_discord(f"CNJMESH {host}: No single node dominating ingest anymore")
        else:
            node_hex = hex(top_node) if top_node is not None else "unknown"
            send_discord(f"\U0001F7E1 CNJMESH {host}: Node {node_hex} accounts for {top_pct}% of last hour's traffic ({top_count}/{total}) -- possible loop/flood, same signature as prior loop-node incidents")
        state["hot_node_last_alert"] = time.time()
    state["hot_node_state"] = hot_node_state

    save_state(state)
    node_hex = hex(top_node) if top_node is not None else "none"
    print(f"{host}: rate={total}/hr({rate_state}) top_node={node_hex}({top_pct}%,{hot_node_state})")


if __name__ == "__main__":
    main()
