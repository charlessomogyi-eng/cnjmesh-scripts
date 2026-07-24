# CNJ Mesh — Open To-Dos

**For AI assistants:** This is the current, lean action list. Fetch this alongside `cnjmesh1-operations.md` at the start of a session — both are short. Only fetch `session-log.md` (long, narrative, full history) if you need the backstory on *why* something is the way it is.

**Housekeeping rule:** when an item is finished, delete it from this file — don't mark it "done" and leave it. If the fact that it's finished matters for later reference, a one-line note goes in `session-log.md` instead, not here.

*Split out from CLAUDE_CONTEXT.md on 2026-07-24. Items below were pulled forward from roughly two weeks of session notes — most are still genuinely open, but this was a first-pass triage, not a perfect one. Worth a skim to confirm nothing's stale or already done.*

---

## Active / Recent (July 22-24, 2026 sessions)

- **Malla data retention not set** — `data_retention_hours` is commented out (defaults to 0/never) in `/opt/stacks/malla/config.yaml`. Database already 624MB and growing forever. Decide on a window (90 days / 2160 hours suggested) and set it.
- **Docker log-rotation cap only applied to Mosquitto** — the other 11 containers on cnjmesh1 still have unbounded logs. `/etc/docker/daemon.json` sets the default for *new* containers, but each existing one needs `docker compose up -d --force-recreate <service>` to actually pick it up.
- **cnjmesh1 kernel/OS upgrade** — running an older Trixie build than cnjmesh3. Not urgent, whenever convenient: `sudo apt update && sudo apt full-upgrade && sudo reboot`. (Also: do this roughly monthly on all 3 Pis going forward, not just cnjmesh1 — see cnjmesh1-operations.md's maintenance note.)
- **Malla CVE-2026-43980 (stored XSS)** — check if the running image predates the May 30, 2026 patch (`docker inspect mqtt-malla-web-1 --format '{{.Created}}'`), pull/recreate if so.
- **peer-check watchdog — confirm it's currently ENABLED.** Was manually stopped on cnjmesh2 and cnjmesh3 during the night of July 23-24 (to silence alerts while cnjmesh1's WiFi issue was being worked) and re-enabling wasn't explicitly confirmed since. Check: `sudo systemctl status peer-check.timer` on both. If stopped: `sudo systemctl start peer-check.timer`.
- **cnjmesh1 recurring WiFi "stuck" issue — root cause still unknown.** Two occurrences (night of July 22-23, morning of July 24) where the interface looks completely healthy (good bitrate/signal, TX counter incrementing, router shows it online, correct ARP on other devices) but zero traffic actually passes, including to the gateway. Fixed both times by forcing a reconnect (full reboot, or `nmcli con down/up`) — but why it happens isn't understood. Worth a lightweight recurring check if it keeps happening (see philosophy note in cnjmesh1-operations.md re: not over-building this).
- **Mosquitto log-fill rate — genuinely unresolved, don't trust the "slow accumulation" explanation.** Charles reports the disk filled to 100% again overnight after being cleared once — that's inconsistent with the ~2KB/30sec growth rate actually measured. Needs real sustained monitoring next time it happens, not a single spot-check.
- **Stale Fing Agent alerts** — Fing is alerting on the OLD (dead) cnjmesh1 board's MAC (`88:A2:9E:3E:0E:7E`), not the new board's. Deactivate/delete that old agent entry in the Fing app. Possible wrinkle: timing of a July 24 alert suggests Fing Agent software might still be a *live process* on the new board reporting under the old ID — worth checking with `ps aux | grep -i fing` before assuming it's purely stale/coincidental.
- **Fing Agent for the NEW board** — if still wanted, install/activate fresh (will register under the new correct MAC).
- **rename "APRS 2m (Graywolf)" → "Graywolf APRS 2M"** in peer-check's SERVICES config on cnjmesh2 and cnjmesh3 (Charles's preferred wording, cosmetic only).
- **cnjmesh1's own peer-check deployment** — currently only cnjmesh2 and cnjmesh3 run peer-check (watching each other + cnjmesh1). cnjmesh1 itself doesn't watch anyone. Config for this was prepped in an earlier session but never deployed — decide if still wanted.
- **USB drive for swap (optional, only if RAM pressure recurs)** — Charles is looking for an old spare thumb drive to test rpi-swap's file-based/hybrid swap mode as a lower-risk alternative to pushing zram size further. Not urgent, not needed unless the RAM pressure issue comes back.
- **Second RX-only ESP32 LoRa board** — ordered, in transit. Needed because K2GIA-10's iGate firmware doesn't self-gate its own outgoing messages to APRS-IS.

## Carried over from mid-July sessions (status uncertain — verify before assuming still open)

- **CJG1 (Heltec V4) WiFi flapping** — was still actively flapping after a Mode change that fixed CJG2. Next test ideas noted: power supply/cable check, physical position, router channel (Auto → fixed 1/6/11).
- **Client 1 replacement** — known CP210x serial flapping issue, replacement with a RAK/WisMesh planned. Side idea: check if the old V3's case is intact — could refurbish instead of buying new.
- **Radio tuning (KPR1→ now N/A since retired, KPR2, Observer)** — apply the Capital District Mesh whitepaper §9.4.2 txdelay/rxdelay tuning. Neighbor counts never gathered, nothing started.
- **MeshCore regioning talking points** — prepared but never actually brought back to the NY/NE Mesh Discord.
- **Rotate `meshuser`/`meshdev` MQTT credentials** — flagged as overdue multiple times since mid-July (broker is public over WSS). Still appears unrotated.
- **Send the drafted Tilly outreach message** (LetsMesh/observer invite) — was blocked on credential rotation above; unclear if ever sent.
- **Clean up fake/template CoreScope mqttSources entries** (`lincomatic`, `wsmqtt` in `/home/somog/meshcore-data/config.json`) — harmless log spam, cosmetic.
- **LetsMesh map discrepancy** — CNJ packets clearly flowing on the Packets page but node not appearing on the map itself. Never resolved, not investigated further.
- **KB2EAR-2 not appearing in CNJ packet feed** despite being ~772m away — flagged as odd, not investigated.
- **K2GIA-10 physical relocation upstairs** for antenna height — decided, not yet done (unrelated to any Pi migration, it's WiFi-based).
- **Tinkering project (explicitly low priority):** MeshCore ↔ Discord bidirectional bridge test, via MeshCoreDiscordBridge (Hude06).
- **mr-tbot's mesh-api** — flagged as a reference pointer for future cross-mesh bridging, never actually evaluated.

## Older items, likely stale or superseded — sanity-check before acting on any of these

*(These are from the July 13 session and predate several major changes — cnjmesh3's full setup, the KPR1 retirement, and K2GIA-10's arrival all happened since. Listed here only so nothing's silently lost; several are probably already done or no longer relevant.)*

- Explore deeper LetsMesh.net integration (see `docs/letsmesh-and-ozneteast-notes.md`)
- Invite more NJ MeshCore operators to the meshcore-nj-mqtt channel
- Get Tilly/y0gurt pointed at mqtt.cnjmesh.me or set up as LetsMesh observers
- NWS alerts — verify behavior on a real/live alert
- meshcore-packet-capture health check / auto-restart on Observer disconnect
- Node tagging in MeshCore Hub (KPR2, Observer)
- Discord server security review
- APRS Discord silent-alert monitor
- T096 + Alfa mobile setup (needs SMA→RP-SMA adapter)
- Broker-to-broker bridging with LV Mesh / SJ Mesh for meshcore-nj-mqtt
- Cross-mesh bridge via mesh-api (duplicate of the item above, kept for visibility)
- MeshOmatic relay script
- KPR2 watchdog
- Remove dead MeshOmatic section from mosquitto.conf (verify first)
- Remove dead meshshadow section from cloudflared config (verify first)
- Rotate Discord webhook URLs (low priority)
- Rotate MeshOmatic password (low priority)
