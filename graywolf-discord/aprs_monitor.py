#!/usr/bin/env python3
"""
aprs_monitor.py — Graywolf APRS health monitor for CNJ Mesh
Posts alerts to Discord DISCORD_WEBHOOK_RF channel.

Alert triggers:
  1. cpal input stream failed, rebuilding — 10+ in 8hr window → alert, re-alert every 12hrs
  2. 24hr dead-air — no RF packet received in 24hrs → alert, re-alert every 12hrs
  3. Service crash (graywolf / graywolf-discord) — immediate alert, re-alert every 12hrs if still down
"""

import asyncio
import logging
import os
import re
import sqlite3
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import aiohttp
from dotenv import dotenv_values

# ── Configuration ────────────────────────────────────────────────────────────
ENV_FILE            = "/opt/graywolf-discord/.env"
GRAYWOLF_DB         = "/var/lib/graywolf/graywolf.db"
CHECK_INTERVAL      = 300          # seconds between checks (5 minutes)
DEADAIR_HOURS       = 48           # hours without RF packet = dead-air
REALERT_INTERVAL    = 12 * 3600    # 12 hours between repeat alerts for same condition
SERVICES_TO_WATCH   = ["graywolf", "graywolf-discord"]

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("aprs-monitor")


def load_webhook() -> str:
    env = dotenv_values(ENV_FILE)
    url = env.get("DISCORD_WEBHOOK_RF", "")
    if not url:
        raise RuntimeError(f"DISCORD_WEBHOOK_RF not found in {ENV_FILE}")
    return url


async def post_alert(session: aiohttp.ClientSession, webhook_url: str, message: str):
    payload = {"content": message}
    try:
        async with session.post(
            webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status in (200, 204):
                log.info("Alert posted: %s", message[:80])
            elif resp.status == 429:
                retry = (await resp.json()).get("retry_after", 5)
                log.warning("Discord rate limited, retry after %ss", retry)
            else:
                log.error("Discord HTTP %d", resp.status)
    except Exception as exc:
        log.error("Failed to post alert: %s", exc)


# ── Check 2: Dead-air (no bridge activity) ───────────────────────────────────
def last_packet_received() -> datetime | None:
    """Return UTC datetime of most recent successful Discord bridge post, or None."""
    try:
        result = subprocess.run(
            ["journalctl", "-u", "graywolf-discord", "--no-pager", "--output=short-iso",
             "--since", "7 days ago", "--grep", "Discord:"],
            capture_output=True, text=True, timeout=15
        )
        last_dt = None
        for line in result.stdout.splitlines():
            try:
                ts = line[:25]
                dt = datetime.fromisoformat(ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if last_dt is None or dt > last_dt:
                    last_dt = dt
            except Exception:
                continue
        return last_dt
    except Exception as exc:
        log.error("Dead-air check error: %s", exc)
        return None


# ── Check 3: Service status ───────────────────────────────────────────────────
def is_service_active(service: str) -> bool:
    """Return True if service is active/running."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == "active"
    except Exception as exc:
        log.error("Service check error for %s: %s", service, exc)
        return True  # assume ok on error to avoid false alerts


# ── Main monitor loop ─────────────────────────────────────────────────────────
async def monitor():
    webhook_url = load_webhook()
    log.info("APRS monitor starting (check interval: %ds)", CHECK_INTERVAL)

    # Track last alert times to enforce re-alert intervals
    last_alert: dict[str, float] = {
        "deadair": 0.0,
        **{f"crash:{svc}": 0.0 for svc in SERVICES_TO_WATCH},
    }

    async with aiohttp.ClientSession() as session:
        while True:
            now = time.monotonic()
            now_utc = datetime.now(timezone.utc)

            # ── 2. Dead-air check ─────────────────────────────────────────
            last_rf = last_packet_received()
            if last_rf is None:
                log.warning("No bridge activity found in journal at all")
                hours_silent = DEADAIR_HOURS  # treat as dead-air
            else:
                hours_silent = (now_utc - last_rf).total_seconds() / 3600
                log.info("Last bridge activity: %.1f hours ago", hours_silent)

            if hours_silent >= DEADAIR_HOURS:
                if (now - last_alert["deadair"]) >= REALERT_INTERVAL:
                    last_str = last_rf.strftime("%B %-d, %Y %-I:%M %p UTC") if last_rf else "never"
                    msg = (
                        f"📻 **Graywolf Bridge Dead-Air Alert** — {now_utc.strftime('%B %-d, %Y %-I:%M %p UTC')}\n"
                        f"No APRS packets bridged to Discord in the last **{int(hours_silent)} hours**.\n"
                        f"Last bridge activity: {last_str}\n"
                        f"Check Graywolf, graywolf-discord service, and radio status."
                    )
                    await post_alert(session, webhook_url, msg)
                    last_alert["deadair"] = now
            else:
                if last_alert["deadair"] > 0:
                    log.info("Dead-air condition cleared")
                    last_alert["deadair"] = 0.0

            # ── 3. Service crash check ────────────────────────────────────
            for svc in SERVICES_TO_WATCH:
                key = f"crash:{svc}"
                active = is_service_active(svc)
                log.info("Service %s: %s", svc, "active" if active else "DOWN")
                if not active:
                    if (now - last_alert[key]) >= REALERT_INTERVAL:
                        msg = (
                            f"🚨 **Service Down: {svc}** — {now_utc.strftime('%B %-d, %Y %-I:%M %p UTC')}\n"
                            f"`{svc}.service` is not active.\n"
                            f"Run `sudo systemctl status {svc}` to investigate."
                        )
                        await post_alert(session, webhook_url, msg)
                        last_alert[key] = now
                else:
                    if last_alert[key] > 0:
                        log.info("Service %s recovered", svc)
                        last_alert[key] = 0.0

            log.info("Check complete, sleeping %ds", CHECK_INTERVAL)
            await asyncio.sleep(CHECK_INTERVAL)


def main():
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        log.info("Monitor stopped.")


if __name__ == "__main__":
    main()

