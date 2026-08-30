# LoRa APRS → Discord bridge

Relays K2GIA-10's LoRa APRS message-type traffic (not positions/beacons) to
the `lora-aprs-70cm-relay` channel in two Discord servers, by listening to
K2GIA-10's own syslog stream (UDP 1514) — not the KISS TCP port, which is
confirmed TX-injection-only and never echoes anything back (see the script's
own docstring).

**Since K2GIA-10's APRS-IS connection was disabled Aug 28, 2026, everything
this bridge now sees is inherently RF-only** — no filtering needed to
separate RF from internet-sourced traffic anymore, the source itself only
produces RF.

## What it captures

Both `TX / MESSAGE` and `RX / MESSAGE` events from K2GIA-10's syslog —
i.e. anything K2GIA-10 **sends, receives, or digipeats**, per Charles's
explicit scope (Aug 30, 2026). Text messages only — **beacons and telemetry
are never matched at all**, since those don't appear as `MESSAGE`-type
syslog lines in the first place. ack/rej packets and non-printable garbage
are filtered out automatically. Each Discord post is labeled "Sent/Relayed"
or "Received" so the direction is clear.

**Important caveat:** the `RX / MESSAGE` line format is NOT yet confirmed
against a real captured example — only the `TX` format has been directly
seen. The RX pattern was added by analogy (same firmware, same "TYPE /
CATEGORY / FROM ---> TO :text{msgid" convention). If received messages
never show up in Discord despite K2GIA-10 obviously hearing local traffic
(W2MMD-10, K2ZA-10, AC2F-10 etc.), capture a real line with `nc -ul 1514`
during an actual receive and fix `RX_MESSAGE_RE` in the script to match
what's actually there.

## Flood protection already built in

- Rate limit: 20 posts/minute per webhook
- Dedup: 120-second window, keyed on direction+sender+text+message-ID — so
  a station retrying the same message several times (common — APRS clients
  often retry 3-7x waiting for an ACK) only posts once, not once per retry

## The bug this fixes

The script itself reads Discord webhook URLs via plain `os.environ.get(...)`
with no dotenv-loading logic — running it directly (`python3
lora-aprs-discord-bridge-v2.py`) fails with "DISCORD_WEBHOOK_LORA not set"
unless the `.env` file is manually sourced first (`set -a; source .env; set
+a`). This was never turned into a proper always-on service before. The
`EnvironmentFile=` directive in the `.service` file below fixes this cleanly
— **no code changes needed**, just correct deployment.

## Deploy (on cnjmesh1)

The script already lives at `/opt/lora-aprs-discord/` — this repo copy is
for backup/version-control, not a fresh install. `.env` (with the real
webhook URLs — see `CLAUDE_CONTEXT.md` for the current values) already
exists there too; don't overwrite it, just confirm it has:
```
DISCORD_WEBHOOK_LORA=<MeshCore-NJ webhook>
DISCORD_WEBHOOK_LORA_MESHCORE=<Meshtastic-NJ webhook>
SYSLOG_PORT=1514
```

Then:
```bash
sudo cp lora-aprs-discord-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now lora-aprs-discord-bridge.service
sudo systemctl status lora-aprs-discord-bridge
```

## Verify K2GIA-10 is actually pointed here

WebUI (`http://10.0.0.74`) → Syslog section → Server should be `10.0.0.181`
(cnjmesh1), Port `1514`. Confirmed correct as of Aug 2026 — worth a quick
glance if the bridge seems to receive nothing.

## Test end-to-end

Send a message via aprs-tnc-web (`http://10.0.0.181:8085`), then:
```bash
journalctl -u lora-aprs-discord-bridge -f
```
Should show `LoRa APRS -> Discord: ...` on a successful post. Check both
Discord channels directly to confirm — this was flagged as "not yet fully
confirmed posting end-to-end" in earlier notes; worth actually watching a
real test through rather than assuming.
