# CNJ Mesh — Open To-Dos

**For AI assistants:** This is the current, lean action list. Fetch this alongside `cnjmesh1-operations.md` at the start of a session — both are short. Only fetch `session-log.md` (long, narrative, full history) if you need the backstory on *why* something is the way it is.

**Housekeeping rule:** when an item is finished, delete it from this file — don't mark it "done" and leave it. If the fact that it's finished matters for later reference, a one-line note goes in `session-log.md` instead, not here.

*Split out from CLAUDE_CONTEXT.md on 2026-07-24. Items below were pulled forward from roughly two weeks of session notes — most are still genuinely open, but this was a first-pass triage, not a perfect one. Worth a skim to confirm nothing's stale or already done.*

---

### Active / Recent (July 25, 2026 session)

- **Audit `whorepeated` / path-lookup scripts for 2-char hex truncation** — KPR2's short path prefix `97` collides with WSMZ997-Fence, so the full `977f` is required to disambiguate. Confirm `/opt/whorepeated/merge_contacts.py` and `path_lookup.py` aren't truncating to 2 hex chars anywhere and misattributing KPR2-relayed packets. (Audit-flagged July 26.)
- **Explicit K2GIA-10 mobile RF-reach test** — CA2RXU firmware doesn't self-gate its own outgoing packets, so aprs.fi only ever shows `TCPIP*, qAC` (internet) and real over-the-air reach is unproven. Until the stuck RX board arrives, confirm reach with a mobile test: take a 433.775 LoRa APRS RX out and see if K2GIA-10 is actually heard, or arrange a cooperating listener. (Independent of the USPS-stuck RX board.)
- **Graywolf PTT device pinning (Digirig stable path)** — point Graywolf at `/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_beb31e2f33c6ef1186b171527a5e3baa-if00-port0` so PTT survives ttyUSB renumbering. Field could NOT be found in the 0.13.13 web UI (config lives in SQLite `/var/lib/graywolf/graywolf.db`). **Approach: (1) ask Graywolf Discord / check handbook for the correct 0.13.13 UI page FIRST, and confirm the app actually honors a by-id symlink; (2) direct SQLite edit is a LAST RESORT only** — the live service writes that DB, the schema is undocumented, and an edit can be overwritten or corrupt config. Do not lead with DB surgery.
- **Whip message-reach test (next APRS session)** — tonight's "did my message get out over the whip" was never cleanly answered because it was tested against Compy/KD2QED-7 in South Jersey (40+ mi, too far for a whip to fairly ack). Re-run it against **KB2EAR** (<1 mi, confirmed iGate KB2EAR-13): send a message, watch for the ACK in the Graywolf thread, and cross-check aprs.fi for the message packet carrying a `qAR,KB2EAR-13` path. That's the clean round-trip confirmation.
- **Is the 2m station digipeating, or only iGating?** iGate is confirmed (qAR paths + IGATED counter). Digipeater is a SEPARATE toggle on Graywolf's Digipeater page and its status is unconfirmed. Check the Digipeater page; if enabling, use fill-in (WIDE1-1 only) for a home whip — full WIDE2-2 keys too much and competes with the Icom for airtime.
- **APRStastic experiment (Meshtastic<->APRS gateway)** — afourney/aprstastic on GitHub. Needs a DEDICATED spare Meshtastic node (NOT CJG1/CJG2 — they're live MQTT feeders), ideally the spare Heltec V4, and probably its own Pi to stay off cnjmesh1's crowded USB bus. Two decisions before building: (1) OK with CNJ mesh node positions appearing on the public aprs.fi map? (2) which node + which Pi. Alpha software (0.0.1aXX) — hobby project, not production.

## Active / Recent (July 22-24, 2026 sessions)

- **Malla data retention not set** — `data_retention_hours` is commented out (defaults to 0/never) in `/opt/stacks/malla/config.yaml`. Database already 624MB and growing forever. Decide on a window (90 days / 2160 hours suggested) and set it.
- **Docker log-rotation cap only applied to Mosquitto** — the other 11 containers on cnjmesh1 still have unbounded logs. `/etc/docker/daemon.json` sets the default for *new* containers, but each existing one needs `docker compose up -d --force-recreate <service>` to actually pick it up.
- **cnjmesh1 kernel/OS upgrade** — running an older Trixie build than cnjmesh3. Not urgent, whenever convenient: `sudo apt update && sudo apt full-upgrade && sudo reboot`. (Also: do this roughly monthly on all 3 Pis going forward, not just cnjmesh1 — see cnjmesh1-operations.md's maintenance note.)
- **Malla CVE-2026-43980 (stored XSS)** — check if the running image predates the May 30, 2026 patch (`docker inspect mqtt-malla-web-1 --format '{{.Created}}'`), pull/recreate if so.
- **[OPTIONAL] peer-check symmetric debounce / maintenance-mode toggle** — recovery ("back online") currently fires immediately with no debounce, so a peer flapping right at the threshold can still emit down/up alert pairs (bit us mildly during the cnjmesh1 board swap). Options if it ever becomes a nuisance: (a) require N stable-up checks before declaring recovery, or (b) a maintenance toggle (e.g. `touch /opt/peer-check/silence-<ip>`) to mute a peer while deliberately working on it. Low priority — flapping only really happens during planned hardware work.
- **cnjmesh1 recurring WiFi "stuck" issue — root cause still unknown.** Two occurrences (night of July 22-23, morning of July 24) where the interface looks completely healthy (good bitrate/signal, TX counter incrementing, router shows it online, correct ARP on other devices) but zero traffic actually passes, including to the gateway. Fixed both times by forcing a reconnect (full reboot, or `nmcli con down/up`) — but why it happens isn't understood. Worth a lightweight recurring check if it keeps happening (see philosophy note in cnjmesh1-operations.md re: not over-building this).
- **Mosquitto log-fill rate — genuinely unresolved, don't trust the "slow accumulation" explanation.** Charles reports the disk filled to 100% again overnight after being cleared once — that's inconsistent with the ~2KB/30sec growth rate actually measured. Needs real sustained monitoring next time it happens, not a single spot-check.
- **Stale Fing Agent alerts** — Fing is alerting on the OLD (dead) cnjmesh1 board's MAC (`88:A2:9E:3E:0E:7E`), not the new board's. Deactivate/delete that old agent entry in the Fing app. Possible wrinkle: timing of a July 24 alert suggests Fing Agent software might still be a *live process* on the new board reporting under the old ID — worth checking with `ps aux | grep -i fing` before assuming it's purely stale/coincidental.
- **Fing Agent for the NEW board** — if still wanted, install/activate fresh (will register under the new correct MAC).
- **rename "APRS 2m (Graywolf)" → "Graywolf APRS 2M"** in peer-check's SERVICES config on cnjmesh2 and cnjmesh3 (Charles's preferred wording, cosmetic only).
- **cnjmesh1's own peer-check deployment** — confirmed NOT installed on cnjmesh1 (July 26). Only cnjmesh2 + cnjmesh3 run peer-check. cnjmesh1-down IS still detected (both peers watch it, plus UptimeRobot), but cnjmesh2/3 are each watched by only ONE peer instead of two — minor redundancy gap (a cnjmesh2 outage goes unreported only if cnjmesh3 is also down at that moment). To close: deploy peer-check on cnjmesh1 with PEERS=Node 2 + Node 3, NODE_LABEL=Node 1, and DOWN_THRESHOLD=12 to match the others. Small new install, not urgent.
- **USB drive for swap (optional, only if RAM pressure recurs)** — Charles is looking for an old spare thumb drive to test rpi-swap's file-based/hybrid swap mode as a lower-risk alternative to pushing zram size further. Not urgent, not needed unless the RAM pressure issue comes back.
- **Second RX-only ESP32 LoRa board** — ordered, in transit. Needed because K2GIA-10's iGate firmware doesn't self-gate its own outgoing messages to APRS-IS.

## Carried over from mid-July sessions (status uncertain — verify before assuming still open)

- **CJG1 (Heltec V4) WiFi flapping** — was still actively flapping after a Mode change that fixed CJG2. Next test ideas noted: power supply/cable check, physical position, router channel (Auto → fixed 1/6/11).
- **Client 1 replacement** — known CP210x serial flapping issue, replacement with a RAK/WisMesh planned. Side idea: check if the old V3's case is intact — could refurbish instead of buying new.
- **Radio tuning (KPR1→ now N/A since retired, KPR2, Observer)** — apply the Capital District Mesh whitepaper §9.4.2 txdelay/rxdelay tuning. Neighbor counts never gathered, nothing started.
- **MeshCore regioning talking points** — prepared but never actually brought back to the NY/NE Mesh Discord.
- **Meshview coverage regression since July 21 Pi swap — confirmed RF-side, not bridging.** Used to see NYC/distant nodes (Rockefeller Center, Mt Kemble, etc.) regularly on meshview.cnjmesh.me; now rarely. Confirmed via comparison with MTX1's map (sbnj.meshview.comfx.com, ~1 mile away) that those distant nodes are RF-connected (neighbor/traceroute lines), not MQTT-bridged dots — so the gap is in what my own feeders (CJG1/CJG2) hear vs. before, not a bridge issue on the Meshview side. CJG1/CJG2 WiFi itself was confirmed NOT flapping (only phone↔node app connection flapped in the past — corrected assumption). **Corroborating evidence found same night: Malla's Gateway Diversity metric dropped from "much higher" historically to 1** — meaning almost all previously-diverse gateway sources (beyond my own local feeder) have stopped arriving at the broker. This points at a dead mosquitto bridge stanza or upstream broker outage rather than a feeder RF problem. **Next step:** check bridge connection status and configured stanzas: `docker logs mosquitto --tail 100 | grep -iE "bridge|connecting|connected|disconnect"` and `grep -iE "connection|address|topic|bridge" /opt/stacks/mqtt/config/mosquitto.conf` on cnjmesh1. Also verify which single gateway is the surviving "1" and confirm Malla's MQTT source didn't narrow after a restart.
- **KPN6 (roof-antenna node) MQTT is pre-configured for cnjmesh1 (10.0.0.181, user meshdev) but currently disabled (module toggle off).** Decision made: **leave it off** — Charles wants KPN6 to stay pure-RF, no internet uplink, even though enabling it (uplink-only, without touching downlink) would likely improve Meshview's distant-node coverage. Channels 3-7 (CentralNJ, CNJ-MQTT, SJMesh, CNJTest, CentNJ-MQTT) have MQTT downlink enabled too (MQTT→RF), which is the more RF-philosophy-relevant setting if this is ever revisited. Open sub-question, not yet answered: was KPN6 ever an active feeder during the period when more distant nodes were visible? If yes, its being turned off (separate from the Pi swap) may be the real explanation for reduced coverage, independent of the Malla bridge finding above.
- **Rotate `meshuser`/`meshdev` MQTT credentials** — flagged as overdue multiple times since mid-July (broker is public over WSS). Still appears unrotated.
- **Send the drafted Tilly outreach message** (LetsMesh/observer invite) — was blocked on credential rotation above; unclear if ever sent.
- **[MONITOR idea] Per-source freshness watchdog for CoreScope.** The meshomatic outage went unnoticed for ~64 h because nothing alerted on a stale *source*. Consider a watchdog (cnjmesh1, same pattern as the meshcore-mqtt-bridge + CoreScope ingest-stall watchdogs) that checks each CoreScope MQTT source's "last packet" age and pings #cnjmesh Discord if any source (local, meshomatic) goes stale past a threshold. CoreScope already surfaces this on the Observers page and via the in-app banner — the watchdog would just push it to Discord so it's not dependent on eyeballing the UI.
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
