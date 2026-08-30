#!/usr/bin/env python3
"""
CNJ Mesh LoRa APRS -> Discord bridge (syslog-based).

K2GIA-10's KISS TCP server (port 8001) turned out to be TX-injection only --
it never echoes transmitted or received frames back to connected clients, so
there's no way to observe traffic that way (confirmed via direct testing on
2026-07-14/15).

Instead, this listens on a UDP syslog port for K2GIA-10's own log stream
(the same data source lora-aprs.live consumes). Confirmed real format for a
message-type TX event:

    <165>1 - K2GIA-10 CA2RXU_LoRa_iGate_3.2.4 - - - TX / MESSAGE / <FROM> ---> <TO> :<text>{<msgid>

RX (received) events are ALSO relayed, on the assumption they follow the
same convention with RX in place of TX. This has NOT been confirmed against
a real captured line as of Aug 30, 2026 — if RX messages never appear in
Discord despite K2GIA-10 clearly receiving traffic, capture raw syslog
(`nc -ul 1514`) during a real receive and check the actual line format,
then fix RX_MESSAGE_RE below to match.

K2GIA-10 must have its Syslog Server/Port setting pointed at this host's IP
and SYSLOG_PORT (Configuration page on http://10.0.0.74 -> Syslog section).
"""
import asyncio
import logging
import os
import re
import time
from datetime import datetime, timezone

import aiohttp

DISCORD_WEBHOOK_LORA          = os.environ.get("DISCORD_WEBHOOK_LORA", "")
DISCORD_WEBHOOK_LORA_MESHCORE = os.environ.get("DISCORD_WEBHOOK_LORA_MESHCORE", "")

SYSLOG_HOST = os.environ.get("SYSLOG_HOST", "0.0.0.0")
SYSLOG_PORT = int(os.environ.get("SYSLOG_PORT", "1514"))

MAX_POSTS_PER_MINUTE = 20
DEDUP_WINDOW = 120

BLOCKLIST = set()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("lora-aprs-discord")

# Matches confirmed real TX format:
# ... TX / MESSAGE / K2GIA-10 ---> K2GIA-10 :test 10{89
TX_MESSAGE_RE = re.compile(r"TX / MESSAGE / (\S+) ---> (\S+) :(.*?)\{(\S+)")

# RX format not yet directly confirmed from a live capture — inferred by
# analogy with the confirmed TX format above (same firmware, same "TYPE /
# CATEGORY / FROM ---> TO :text{msgid" convention, just RX instead of TX).
# Verify against a real captured line before fully trusting this in
# production; if it never matches anything, the format differs and this
# needs revisiting with an actual example.
RX_MESSAGE_RE = re.compile(r"RX / MESSAGE / (\S+) ---> (\S+) :(.*?)\{(\S+)")


def format_message(from_call, to_call, text, direction):
    text = text.strip()
    if not text or len(text) < 2:
        return None
    if re.match(r"^(ack|rej)[A-Za-z0-9]*$", text, re.IGNORECASE):
        return None
    printable = sum(1 for c in text if c.isprintable())
    if printable / len(text) < 0.7:
        return None

    icon = "\U0001f4e1"
    label = "Sent/Relayed" if direction == "TX" else "Received"
    ts = datetime.now(timezone.utc).strftime("%B %-d, %Y %-I:%M %p UTC")
    content = (
        f"{icon} **LoRa APRS Message ({label})** - {ts}\n"
        f"**From:** {from_call}\n"
        f"**To:** {to_call}\n"
        f"**Message:** {text[:200]}"
    )
    return {"content": content}


class WebhookPoster:
    def __init__(self, url, name):
        self.url = url
        self.name = name
        self._post_times = []

    def _prune(self):
        cutoff = time.monotonic() - 60
        self._post_times = [t for t in self._post_times if t > cutoff]

    def _rate_limited(self):
        self._prune()
        return len(self._post_times) >= MAX_POSTS_PER_MINUTE

    async def post(self, session, payload):
        if not self.url:
            return False
        if self._rate_limited():
            log.warning("[%s] rate limit", self.name)
            return False
        try:
            async with session.post(self.url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status in (200, 204):
                    self._post_times.append(time.monotonic())
                    return True
                elif resp.status == 429:
                    body = await resp.json()
                    await asyncio.sleep(body.get("retry_after", 5))
                    return False
                else:
                    log.error("[%s] HTTP %d", self.name, resp.status)
                    return False
        except Exception as exc:
            log.error("[%s] error: %s", self.name, exc)
            return False


class DedupeCache:
    def __init__(self):
        self._cache = {}

    def is_duplicate(self, key):
        now = time.monotonic()
        last = self._cache.get(key)
        if last and (now - last) < DEDUP_WINDOW:
            return True
        self._cache[key] = now
        if len(self._cache) > 2000:
            cutoff = now - DEDUP_WINDOW
            self._cache = {k: v for k, v in self._cache.items() if v > cutoff}
        return False


class SyslogProtocol(asyncio.DatagramProtocol):
    def __init__(self, queue):
        self.queue = queue

    def datagram_received(self, data, addr):
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            return
        self.queue.put_nowait(text)


async def run_bridge():
    if not DISCORD_WEBHOOK_LORA:
        log.error("DISCORD_WEBHOOK_LORA not set")
        return

    poster_main = WebhookPoster(DISCORD_WEBHOOK_LORA, "lora-aprs-nj")
    poster_mc = WebhookPoster(DISCORD_WEBHOOK_LORA_MESHCORE, "lora-aprs-nj-mc")
    dedupe = DedupeCache()
    queue = asyncio.Queue()

    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: SyslogProtocol(queue),
        local_addr=(SYSLOG_HOST, SYSLOG_PORT),
    )
    log.info("Listening for syslog on %s:%d", SYSLOG_HOST, SYSLOG_PORT)
    log.info("CNJ Mesh LoRa APRS -> Discord bridge starting")

    async with aiohttp.ClientSession() as http_session:
        while True:
            line = await queue.get()

            m = TX_MESSAGE_RE.search(line)
            direction = "TX"
            if not m:
                m = RX_MESSAGE_RE.search(line)
                direction = "RX"
            if not m:
                continue

            from_call, to_call, text, msgid = m.groups()
            if from_call in BLOCKLIST:
                continue

            dedup_key = f"{direction}:{from_call}:{text}:{msgid}"
            if dedupe.is_duplicate(dedup_key):
                continue

            payload = format_message(from_call, text=text, to_call=to_call, direction=direction)
            if payload is None:
                continue

            if await poster_main.post(http_session, payload):
                log.info("LoRa APRS -> Discord [%s]: %s -> %s: %s", direction, from_call, to_call, text)
            if DISCORD_WEBHOOK_LORA_MESHCORE:
                await poster_mc.post(http_session, payload)


def main():
    try:
        asyncio.run(run_bridge())
    except KeyboardInterrupt:
        log.info("Bridge stopped.")


if __name__ == "__main__":
    main()
