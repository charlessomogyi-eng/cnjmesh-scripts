# CNJ Mesh — Open To-Dos

### [NEXT UP — Sep 3, 2026] SJMesh nodes missing from Meshview node graph — root cause found, fix not yet applied
**Root cause identified Sep 2/3:** when `sjmesh-relay.service` (standalone Python relay) permanently replaced the native Mosquitto `sjmesh` bridge on Aug 14, the SJMesh **channel** topic did not get carried over. The native bridge had `topic msh/US/2/e/SJMesh/# both 0` — added deliberately on Aug 9 after tracking down why KPN6 test messages weren't reaching SJMesh's community. The relay's `SUBSCRIBE_TOPICS` only has the two CentralNJ patterns (`msh/US/2/e/CentralNJ/#`, `msh/US/NJ/2/e/CentralNJ/#`). **This was an omission during the swap, NOT a deliberate anti-flood decision** — important distinction, since the flood/dedup work (Aug 4-15) was about three specific loop nodes on CentralNJ topics, unrelated to the SJMesh channel.

**Why re-adding it is low-risk:** `BLOCKED_TOPICS` in `relay.py` is surgical — exactly three node IDs (`!699a9390`, `!698574b0`, `!db51bb30`), each on their two CentralNJ topic paths only. Those are the loop/flood nodes. Re-adding the SJMesh channel topic doesn't touch those blocks or widen anything toward `msh/US/#` (the original over-broad scope that caused problems).

**Planned fix (two small edits to `/opt/sjmesh-relay/relay.py`, also in git at `cnjmesh1/sjmesh-relay/relay.py`):**
1. Add `("msh/US/2/e/SJMesh/#", 0)` to `SUBSCRIBE_TOPICS`
2. Defensively add SJMesh-path variants of the three blocked node IDs to `BLOCKED_TOPICS`, in case they ever publish on that channel

**Must also verify:** Meshview maintains its OWN independent MQTT topic subscription list in `~/meshview/config.ini` (`[mqtt]` section, `topics = [...]`). Getting SJMesh traffic into the local broker only helps if Meshview is also subscribed to it. Check with `grep -A 10 "\[mqtt\]" ~/meshview/config.ini` before assuming the relay fix alone is sufficient.

**Also noted from upstream README while investigating:** Meshview 3.0.4+ has a native configurable skip-node list + secondary decryption keys in its MQTT reader — a Meshview-level way to drop specific bad nodes at ingestion (protects Meshview's DB only, not Mosquitto/Malla). Not needed for this fix, but worth knowing it exists. Also: running 3.0.5, current upstream is 3.0.7.


### [NEW — Sep 2/3, 2026] CoreScope "No packets from meshomatic" banner — months-recurring nuisance, decision needed
Charles reports this banner has been popping up for months (latest instance: 22,127 min / ~15.4 days silent, seen on the live map view at `corescope.cnjmesh.me`). Important nuance from a much earlier session: this exact banner was once explicitly flagged as a **red herring** — MeshOmatic is not a CNJ Mesh dependency (CoreScope also pulls from `local`, `letsmesh-us`, `letsmesh-eu` independently), so a quiet/broken MeshOmatic feed doesn't mean CNJ's own data pipeline is unhealthy. However, that same historical outage (the real `local`-source-misconfigured-to-localhost bug, root-caused and fixed once already — see the "MAJOR FIND" entry in session-log.md) also happened to show this same banner with a similar large minute-count at the time, so the two have been genuinely hard to tell apart at a glance in the past.

**Decision not yet made — two options on the table, Charles's choice:**
1. **Remove the `meshomatic` mqttSource entirely** from `/home/somog/meshcore-data/config.json` (CoreScope, on cnjmesh1) — permanently kills the banner, no functional loss since CNJ doesn't depend on it. Simple, clean.
2. **Contact the MeshOmatic owner** to find out why the feed itself has been quiet for 15+ days — might surface a genuine upstream issue worth knowing about (or might just confirm it's abandoned/not worth keeping).

**Also raised, not decided:** whether a dedicated watchdog for this specific banner/condition is worth building — probably moot if option 1 (removal) is chosen.

**Next step:** get `docker exec corescope cat /app/data/config.json | python3 -m json.tool` output to see the actual current source list before editing anything.

Aug 15, 2026: added `msh/US/2/e/LongFast/#` + `msh/US/NJ/2/e/LongFast/#` to the `liamcottle` bridge only, to see if it closes the node-graph gap vs. MTX1's SBNJ instance. Malla isolation confirmed clean (zero LongFast rows reaching Malla's DB) — safe to leave running.

**Aug 16 investigation, findings:** compared CNJ Mesh's nodegraph directly against SBNJ's side by side. Real gap still exists (SBNJ ~26 nodes vs. CNJ ~18), but root-caused to NOT be about the LongFast bridge topic at all:
- Checked whether nyme.sh (NYC-area mesh) offers any MQTT bridge to connect through — confirmed via their own published guide (`nyme.sh/mqtt`) that they've deliberately disabled cross-mesh relaying by design (community wants radio-only). Not a technical gap, a closed door on their end. Charles's counterpoint (fair, noted): nyme.sh can afford RF-only because they have thousands of operators giving organic mesh density over a much smaller area; a smaller group like CNJ spread over more geography doesn't have that density and genuinely needs MQTT as a substitute, so this isn't a like-for-like comparison — the reasoning doesn't transfer, it's just still a locked door regardless.
- The isolated dots on both graphs (nodes with no connecting line, e.g. Rockefeller Center on SBNJ's own graph) are most likely a known Meshview rendering limitation (upstream issue #151 — neighbor-info packets not reflected on the mesh graph), not proof of no real connection either way.
- **Real answer, confirmed by Charles directly:** SBNJ/FTRN are physically sited on high ground specifically for line-of-sight to NYC — Charles personally saw a real RF line from SBNJ to Madison Square Garden. This is a genuine engineered LOS/elevation advantage, not an MQTT scope or bridge-config difference. CJG1/CJG2's antenna siting is the actual lever for closing this gap, not anything in Mosquitto config.

**Decision: keep the LongFast topics on liamcottle running indefinitely** — confirmed safe, zero cost, and may still surface other genuinely-new local-ish nodes over time even though it was never going to manufacture NYC-specific reach.

**Still open, lower priority:**
1. Meshview is v3.0.5, current release is 3.0.7 — worth a version bump eventually.
2. Meshview runs as ad-hoc background Python processes, not a systemd service — won't auto-restart on crash/reboot. Worth converting at some point.

### [UPDATE — Aug 10, 2026] oceancounty MQTT bridge still failing to connect
Persistent connect-then-immediately-close loop on `mqtt.oceancountyme.sh:8883`, since Aug 9, no successful connection. Details sent to the operator (Discord: takinglives3) on Aug 9 — awaiting his follow-up on his own broker/logs. No action needed on our side until he responds.

### [ACTIVE — blocked on one fact only Tilly has] Get Tilly's fork running on KPR1 (cross-mesh packet bridge)
Full multi-week debugging narrative archived in session-log.md (Aug 16 entry) — this is just the current status. KPR1 is dedicated to this project (CNJ endpoint `b`), fully built and connected to Tilly's AWS broker. Root cause of the connection flapping fully traced to source: the bridge needs `RX_LOG_DATA` companion-protocol frames, which neither KPR1 nor KPR2 (both repeaters) ever emit — confirmed via meshcore library source, not a guess.

**The one remaining blocker:** what makes a MeshCore device start pushing companion-protocol LOG_DATA frames over serial — a firmware build, a device setting, or a specific command? Tilly's endpoint does this successfully; ours doesn't. This is a question only Tilly can answer from his own working config. Everything else (container, config, broker connection, topic subscribe) is confirmed working.

**Also still open:** Tilly's own endpoint was independently observed cycling too (~105 sec) — worth flagging to him that his side may need the same kind of timeout fix once the main blocker is resolved.

### [FUTURE IDEA — not decided or scheduled] SATA SSD upgrade for cnjmesh1
Pi SD cards are a known long-term failure point, and given cnjmesh1's disk-fill history, more headroom + reliability could help. No decision made, revisit when there's bandwidth for a hardware project.

### [REFERENCE] `docs/RESILIENCE-PLAN.md` and `docs/PREVENTION-AND-INCIDENT-RUNBOOK.md`
Both built Aug 5 in response to "I never want to go through this again." **The two highest-value items from both docs — broker ingest-rate watchdog and disk-space watchdog — are now DONE** (deployed Aug 15-16, all 3 Pis have disk-temp, cnjmesh1 has ingest-rate; full detail in session-log.md). Remaining lower-priority items from these docs, not yet built: per-Pi heartbeat/uptime self-report, memory/load watchdog, scheduled-job success monitors for the weather bots, self-healing auto-restarts for low-risk services, finishing the Docker log-rotation rollout to every container (still the actual disk-to-zero mechanism from the original saga, not fully closed).

### [READ] Lessons learned from get-well plan execution — `docs/lessons-learned-get-well-plan.md`
Process/technique lessons worth a fresh read at the start of future sessions on this project: git commit -a not staging new files, schedule changes needing explicit confirmation, stale docs causing false alarms, watchdogs being alert-only vs. self-healing, USB device path instability (`/dev/serial/by-id/`), verifying "retired" status against live state.

### [MASTER GATE] Pre-Tilly health checklist — everything 100% before finalizing Tilly
Charles's requirement: confirm all of cnjmesh1/2/3, Malla, Meshview, APRS/Graywolf, LoRa APRS, MeshCore Observer/repeaters/Hub healthy before finalizing Tilly's-fork-on-KPR1. Full checklist: `docs/pre-tilly-master-checklist.md`. Given KPR1 itself is the Tilly work (see entry above), this checklist is really just standing verification for everything else — worth a fresh pass before the Tilly blocker resolves, not urgent until then.

### [REVISIT] Malla upgrade / security
Malla has an unpatched public XSS vuln (CVE-2026-43980, all versions ≤ 0.1.7) via Meshtastic node names — relevant since malla.cnjmesh.me is public. No formal releases (rolling `:latest`). A maintained fork exists (`nytera/meshworks-malla`). Undecided — options: check if latest fixes it / evaluate the fork / restrict public access / leave as-is.

### peer-check — RETIRED, superseded by Fing (Sep 2, 2026)
Pi-to-Pi LAN ping approach abandoned for good — root cause of its false alerts (router reboots make every Pi look "down" simultaneously, indistinguishable from a real outage) makes plain ping-based peer monitoring a dead end. Host-offline detection is now handled by Fing (per-device alerts configured and confirmed working Sep 2 — see session-log.md). Service/timer files still exist on cnjmesh2/cnjmesh3 if ever needed for something else, but the peer-check approach itself is not coming back.


### cnjmesh1 WiFi dropout — likely root cause found (wlan0 power-save), validation ongoing
Third occurrence pattern (July 22-23, July 24, July 30) — Pi looks healthy from its own side but is 100% unreachable from the LAN. Power-save fix applied July 30 (`iw dev wlan0 set power_save off` + permanent NetworkManager setting). **Watch for recurrence** — if dropouts stop, confirmed cause; if they recur despite power-save being off, next layer to check is AP-side/L2 or DHCP lease drift.

### LoRa APRS Tracker button wiring — confirmed, not yet installed
Fix for boards with no physical config button confirmed against real firmware source (`richonguzman/LoRa_APRS_Tracker`, `BUTTON_PIN 15`): wire a simple momentary pushbutton, one leg to IO15, other to any GND, no resistor needed. Not yet installed on any physical board — waiting on the tracker board(s)/antennas/cases to arrive (see in-transit hardware item below).

### Smaller open items, roughly in priority order
- **Rotate `meshuser`/`meshdev` MQTT credentials** — overdue since mid-July (broker is public over WSS, and these are well-known Meshtastic public-broker defaults, shared with Tilly's bridge too).
- **In-transit hardware, ready for final assembly once all arrive:** second RX-only ESP32 LoRa board (K2GIA-10 iGate doesn't self-gate its own outgoing packets), 433MHz antennas, LoRa APRS node cases, 2x Alfa antennas (one for the T-Deck/KPN2, one for a MeshCore companion node — may still need an SMA→RP-SMA adapter, unconfirmed).
- **K2GIA-10 physical relocation upstairs** for antenna height — decided, not yet done.
- **Explicit K2GIA-10 mobile RF-reach test** — CA2RXU firmware doesn't self-gate outgoing packets, so real over-the-air reach is unproven via aprs.fi alone. Take a 433.775 LoRa APRS RX out, or arrange a cooperating listener.
- **Graywolf PTT device pinning to a stable path** — field not found in the 0.13.13 web UI; approach should be asking the Graywolf Discord/handbook first, direct SQLite edit is a last resort only.
- **[RESOLVED Aug 17]** ~~Whip message-reach test~~ — superseded: UV-5R M moved from whip to roof dual-band antenna Aug 17, extensively tested via APRS OTA (K2GIA-1 heard "on RF" by OTA bot, multiple confirmed digipeat paths via KB2EAR-1/-13, KC2MDN-2, KM2ARC-15). Roof antenna reach confirmed good.
- **[RESOLVED Aug 17]** ~~Confirm whether the 2m station is digipeating or only iGating~~ — confirmed both enabled: Digipeater page shows enabled, WIDE1-1, using station callsign K2GIA-1.
- **[NEW Aug 17 — investigate when time allows]** Graywolf cpal/ALSA POLLERR audio capture bug — confirmed NOT blocking core function (TX, iGate, APRS OTA all worked fine despite it), but unresolved. Full root-cause research in `docs/aprs-2m-graywolf-reference.md`. Next step not yet tried: systemd `CPUSchedulingPolicy=rr` real-time priority override for graywolf.service. Low priority — proven cosmetic/non-blocking tonight, no rush.
- **APRStastic experiment** (Meshtastic↔APRS gateway) — needs a dedicated spare node (not CJG1/CJG2) and ideally its own Pi. Two decisions pending: OK with CNJ node positions on public aprs.fi, and which node/Pi to use. Alpha software, hobby-tier.
- **`whorepeated.sh`** — back-burner, now technically unblocked (KPR1 working), no urgency assigned.
- **CoreScope `local` source instability** — genuinely unresolved. Best lead: a Mosquitto protocol-error disconnect possibly tied to a zero packet-identifier bug (Mosquitto 2.0.11+ enforcement). Needs a real tcpdump capture timed right after a `docker restart corescope` to confirm/rule out — not yet successfully captured.
- **Per-source freshness watchdog idea for CoreScope** — a stale MQTT source (e.g. meshomatic) can go unnoticed for days since nothing currently alerts on it; CoreScope's own UI shows this already, just not pushed to Discord.
- **Radio tuning** (KPR2, Observer) — apply Capital District Mesh whitepaper §9.4.2 txdelay/rxdelay tuning; neighbor counts never gathered.
- **MeshCore regioning talking points** — prepared, never brought back to the NY/NE Mesh Discord.
- **LetsMesh map discrepancy** — CNJ packets flowing on the Packets page but not appearing on the map itself. Not investigated.
- **KB2EAR-2 not appearing in CNJ packet feed** despite being ~772m away — flagged as odd, not investigated.
- **mr-tbot's mesh-api** — reference pointer for future cross-mesh bridging, never evaluated.
- **[SOMEDAY, after software/config todos are closed out] Physical workshop organization** — cables/boards/adapters/cases need a real system (labeling, bins, inventory sheet). Explicitly deferred by Charles's own request until the software todo list is closed out — logged here so it isn't forgotten.
- **Cosmetic, now moot:** the "APRS 2m (Graywolf)" rename item in peer-check's SERVICES config no longer applies — peer-check is retired (see above), not just disabled.
- **Service-level heartbeat idea — still open, separate from peer-check/Fing.** Fing (host-offline detection) and the retired peer-check (also host-level) never covered this: a Pi can be fully online/pingable while a specific critical service on it (mosquitto, a bridge, etc.) has silently died. Same pattern as `sjmesh-relay`'s existing heartbeat file — candidate for Healthchecks.io (free tier) or self-hosted Uptime Kuma on a 4th, separate device (not one of the 3 mesh Pis). Not scheduled, needs real design time, low priority.
- **Fing Agent — old dead board's MAC still shows stale alerts.** Deprioritized Sep 1: confirmed only one legitimate `fingagent.bin` process running on cnjmesh1 (PID stable since Aug 11, no duplicates), and Charles confirmed Fing is working fine for him in practice day-to-day — this is purely cosmetic (one extra dead entry in the cloud dashboard), not urgent. Leave alone unless it starts actually causing confusing alerts.
- **[NEW Aug 18]** UV-5R M needs to move back to whip antenna — roof dual-band antenna (used for APRS since Aug 17) is needed back for voice (Icom 2730). When done: re-run POLLERR frequency check (`journalctl -u graywolf --since "5 minutes ago" --no-pager | grep -c "cpal input stream error"`) to see if error rate drops — would help confirm/rule out the antenna-load theory from the Aug 17 cpal investigation. Update `docs/aprs-2m-graywolf-reference.md` once done.
- **[NEW Aug 18 — still open, narrowed]** Original question — Charles not seeing certain CentralNJ messages on KPN6 (app) / Discord that he used to see — is STILL UNRESOLVED, but now narrowed: confirmed the SJMesh relay, mosquitto broker, and Malla ingestion are all healthy and actively receiving CentralNJ traffic in real time (verified via direct DB query — see session-log.md Aug 18 for the resolved false-alarm investigation and the correct Malla DB path/schema). So the actual gap, if still present, is downstream of ingestion — either in the Discord bridge logic or in KPN6's RF downlink reception specifically (KPN6's own MQTT module is intentionally disabled, so it only ever hears this traffic as plain rebroadcast RF from CJG1/CJG2's downlink — that link was never directly tested this session). Next step: compare a specific live timestamp from Malla's DB against what actually shows up in Discord/KPN6 at the same moment, rather than general sampling.

---

**[NEW Aug 18 — resilience/security review]** A handful of ideas surfaced from an end-of-session environment review, worth working through over a few nights:
- **Port `ingest-rate-watchdog` to cnjmesh2** — it runs Malla capture on the raw (unfiltered) firehose too, same flood/loop-node exposure that caused the original cnjmesh1 disk-fill saga, currently unwatched there.
- **`peer-check` RETIRED (Sep 2, 2026)** — ping-based Pi-to-Pi monitoring abandoned for good, superseded by Fing's per-device alerting. See `todos.md`.

### [DECIDED Sep 2, 2026 — CLOSED] aprs_monitor.py dead-air check — rejected, not just deferred
Decision, not a gap: APRS message traffic/silence is not a reliable signal of Graywolf's health (a quiet channel doesn't mean anything's wrong), so a 48hr-dead-air check is the wrong approach and won't be built or re-enabled. `graywolf.service` being up (already confirmed via active `graywolf-watchdog.timer`) is sufficient. `aprs_monitor.py` stays disabled permanently.
- **Rotate `meshuser`/`[REDACTED - broker password, scrubbed Aug 30 2026]` on your own `mqtt.cnjmesh.me`** — distinct from SJMesh's own `meshuser` credential (not yours to rotate); this one is genuinely yours and still pending.
- **Apply the Malla CVE-2026-43980 fix** — real upstream patch exists (commits >=4086e2b5f6161...), just needs the careful pull-and-verify process (note current image digest first, back up DB, pull, check for migration errors) given custom DB state from the Aug 15 dedup rebuild.
**For AI assistants:** This is the current, lean action list. Fetch this alongside `cnjmesh1-operations.md` at the start of a session — both are short. Only fetch `session-log.md` (long, narrative, full history) if you need the backstory on *why* something is the way it is.


**Housekeeping rule:** when an item is finished, delete it from this file — don't mark it "done" and leave it. If the fact that it's finished matters for later reference, a one-line note goes in `session-log.md` instead, not here.

*Last cleaned up 2026-08-16 (Sonnet session) — removed ~20 fully-resolved/superseded items and archived a 66K-character Tilly/KPR1 debugging narrative to session-log.md, trimming this file from 505 lines to a genuinely current list. Prior cleanup was 2026-07-24.*

- **[NEW Aug 18 — BLOCKED on hardware]** LoRa APRS message-type packets (not just position beacons) should relay to the LoRa APRS Discord channel — same pattern as the Graywolf 2m bridge (`graywolf-discord-bridge.py`), but for K2GIA-10 / `lora-aprs-discord`. **Deliberately holding off until the LoRa APRS tracker board arrives** — want real message traffic to test against rather than building it blind. Note: `/opt/lora-aprs-discord/` (v2, syslog-based) is not yet in git — pull the live script off cnjmesh1 and commit it first before making any changes, same discipline as tonight's sjmesh-relay/graywolf-discord fixes. Need to check whether it currently only relays position/telemetry packets or already handles message-type traffic before deciding what to change.
- **[NEW Aug 18]** Retry old unsuccessful LoRa APRS bot queries (WHO-IS, CQ, ISS, WXBOT — all attempted Jul 26-30, before the K2GIA-1 rename, roof antenna, and OTA validation work) now that the RF/iGate chain is proven working end-to-end. First step: query Graywolf's messages table for their prior `ack_state`/`failure_reason` to understand what actually happened before just resending blind — `SELECT id, direction, from_call, to_call, text, ack_state, attempts, failure_reason, datetime(created_at) FROM messages WHERE to_call IN ('WHO-IS','CQ','ISS','WXBOT') OR from_call IN ('WHO-IS','CQ','ISS','WXBOT') ORDER BY created_at DESC LIMIT 20;`
- **[NEW Aug 23]** Once the LoRa APRS tracker board (K2GIA-9, on order) arrives and is configured, Charles considers active RF projects "done" aside from break/fix — worth a light doc consolidation pass at that point given the repo has grown large.
- **[NEW Aug 23]** K2GIA-5 (APRSdroid) → K2GIA-7 (TD-H9) message delivery via APRS-IS not yet re-confirmed with APRSdroid's Tracking properly enabled (see `known-issues.md` for the Tracking-gates-sending finding). K2GIA-5 → K2GIA-1 already confirmed working same day. Next APRS session: enable Tracking, send K2GIA-5 → K2GIA-7, check receipt on KISSLink or TD-H9 APRS Messenger's Msgs tab.
- **[NEW Aug 26]** Point K2GIA-10's syslog at the public `lora-aprs.live` aggregator in addition to the existing cnjmesh1 target — needed for K2GIA-9/K2GIA-10 to show up on that site's tracker/iGate maps and RF analytics (SNR, real digipeat path data). Currently only feeds cnjmesh1, so K2GIA-9 shows on aprs.fi (APRS-IS-driven) but not lora-aprs.live (syslog-driven, separate data source).
- **[NEW Aug 26]** Investigate `0xfab1a80c` (shortname FTRN) hot-node alert from ingest-rate-watchdog (57% of traffic in 1hr) — likely legitimate, since Charles confirmed SGA was actively field-testing with FTRN (an elevated relay node) the same evening, matching the pattern of a real high-traffic relay rather than a loop (same class of check that cleared CJG1 previously: verify packet diversity, not just volume). If confirmed legitimate, add FTRN to the watchdog's known-legitimate list so this doesn't false-alarm again.
- **[NEW Aug 28, not urgent]** Get K2GIA-9 fully off IS too — add `RFONLY,NOGATE` to its digipeater path (currently `WIDE1-1,WIDE2-1`, no protection). K2GIA-10's own APRS-IS gate is already off (Aug 28), but K2GIA-9's path itself has no RFONLY/NOGATE, so any *other* future/nearby iGate that hears K2GIA-9 directly could still gate it to IS. Blocked on getting back into K2GIA-9's WebUI (its config AP is closed since the last Save) — three options: (1) IO15-to-GND pad touch, flagged unconfirmed-safe after last triggering unexpected deep sleep; (2) full re-flash, confirmed safe but wipes everything, full reconfig needed; (3) solder the physical button (instructions already in this doc) — probably the best long-term move since K2GIA-9's config will likely need touching again, turns this into a non-issue permanently rather than a recurring hassle.

- **[NEW Aug 30 — HIGH PRIORITY] Rotate leaked, confirmed-exposed credentials.** Aug 30 incident: a leaked Discord webhook (added to `CLAUDE_CONTEXT.md` same day, for the LoRa APRS 70cm relay) was found and actively abused within hours by an automated attacker (`@everyone` spam + inappropriate images, citing the exact repo/commit as the source). Both affected Discord channels were deleted immediately, killing those two webhooks — no rotation needed for those specifically, they're already dead. That incident triggered a broader audit which found more real, still-live exposure:
  - **corescope-watchdog Discord webhook** — confirmed leaked in git history (now scrubbed via `git filter-repo`, force-pushed Aug 30), but the credential itself is still live and unrotated. Used by `disk-temp-watchdog`, deployed on **cnjmesh1, cnjmesh2, AND cnjmesh3** — rotating means updating all three. This is the top-priority one: internet-facing webhook, same exposure class as the one that was actually abused.
  - **meshdev/large4cats MQTT broker password** — confirmed leaked in git history (also scrubbed Aug 30), still live and unrotated. Lower urgency than the webhook: confirmed scoped to a local-only (not internet-facing) Mosquitto broker, and MQTT creds only grant pub/sub access, not shell/system access — worst case is local-network-only data visibility/spoofing, not infrastructure compromise. Worth rotating eventually, just not urgent.
  - **"Spidey Bot" webhook** — was in the original leaked-credential list from old notes, but a full audit of both Discord servers' Integrations pages (Aug 30) shows it no longer exists at all — likely already replaced/renamed at some point (there's a `cnjmesh alerts` webhook on the same #cnjmesh channel now, created Jul 21). Nothing to rotate here; was chasing a stale reference.
  - **Full webhook inventory captured Aug 30** (13 webhooks Charles created, across MeshCore-NJ and Central & South NJ Meshtastic servers — see session-log.md for full list with channel/creation-date detail). Two additional webhooks exist that Charles did NOT create (`Meshmonitor - Roof dd2680e7` and `snj-wx-bot`, both created by "compywiz" — Compy) — explicitly NOT to be touched without talking to him first.
  - **Process agreed for actually rotating each one, whenever time is scheduled for this:** (1) grep every host (`cnjmesh1`, `cnjmesh2`, `cnjmesh3` — separately, each is an independent filesystem) for the webhook's numeric ID under `/opt`, `/home/somog`, `/etc/systemd/system` to find every real reference, don't rely on documentation/memory alone since that's already been proven incomplete tonight (KPN6 sat undocumented for an unknown period; "Spidey Bot" was stale); (2) regenerate the webhook in Discord; (3) Charles pastes the new URL directly in chat (not into any git-tracked file); (4) update each found script/service file directly on its host via a live command (e.g. `sed`), confirm the service picks it up and post a test; (5) never commit the real value to git at any point in this process.




---

## Items added by the 2026-10-13 handoff merge
*(Source: six handoff files from separate chats. Tags: [V] verified, [S] secondhand, [I] inference. Old items above are untouched; these are additions/update notes.)*

### From the Jul 24-25 K2GIA / K2GIA-10 range-test + Meshview/Malla handoff
- **Update 2026-10-13 on the "Meshview runs as ad-hoc background Python processes" item above:** that wording is stale. Meshview runs as systemd units `meshview-db` and `meshview-web` ([V] `install-map-cnjmesh1.md`, `docs/pre-tilly-master-checklist.md:24`, session-log Jul 31 health check). Left in place per the no-rewrite rule; treat the systemd description as correct.
- **[OPEN] Malla "gateway diversity" dropped to 1 (observed Jul 25).** Cause unknown. The "dead Mosquitto bridge" theory was proposed but no diagnostic output was ever seen — unproven. The Aug 14 SJMesh topic omission (see top of this file) began *after* Jul 25, so it cannot explain the Jul 25 drop. Next step (unrun): check Mosquitto bridge status and `mosquitto.conf` on cnjmesh1.
- **[OPEN] Coordinated RF test for K2GIA-10 still not done** — ask a nearby operator to watch their iGate while a CQ is sent on 433.775. K2GIA-10 non-self-gating means aprs.fi alone can't prove reach.
- **[OPEN] Where is the UV-5R M antenna now?** Repo says roof dual-band antenna since Aug 17, and the Aug 18 item above says it should go back to a whip; Jul 24 chat had it on a whip. Current (Oct 13) location unknown — Charles to confirm, then close or keep the Aug 18 item.
- **[OPEN] Oct 8 APRSThursday net:** K2GIA was not seen on page 1 of the net log; full log not checked [S]. Confirm whether K2GIA checked in.
- **[OPEN] Fing Agent:** live `fingagent.bin` process on cnjmesh1 (PID 100151 on Jul 25) — already covered by the "Fing Agent" item above; decision to keep or uninstall still pending.


### From the Aug 20-24 / Oct 5-13 APRS messaging (TD-H9 / KISSLink / APRSdroid / Graywolf) handoff
- **Update 2026-10-13 on the Aug 23 "K2GIA-9, on order" item above:** stale — `known-issues.md` and `docs/lora-aprs-reference.md` show K2GIA-9 arrived, was flashed Aug 26 and is configured as Bluetooth Classic. Old item left in place.
- **[OPEN] Enter the corrected APRSdroid filter** (`t/moi/K2GIA-1/150` or `/K2GIA-5/` — Charles to choose the anchor), then Stop/Start Tracking. Unverified — see `known-issues.md`.
- **[OPEN] Verify/uncheck "Upload RF-heard packets to APRS-IS" on K2GIA-7** (Charles said it was checked [S]; repo's recommended default is unchecked; he leaned RF-only for the mobile).
- **[OPEN] Retest K2GIA-5 to K2GIA-7 over APRS-IS** with Tracking on (already listed above, Aug 23).
- **[OPEN] Unknown: what the 438.800 / 433.250 MHz items in Charles's feed refer to** — probably beacon comments or a gateway frequency [I]; screenshots never shared.
- **[OPEN] Does K2GIA-9 firmware offer BLE KISS?** Repo has it on Bluetooth Classic; "tracker supports BLE KISS" came from the CA2RXU wiki and is untested for this board. Don't plan KISSLink with K2GIA-9 until confirmed.
- **[OPEN, low]** Check ODmaster for Android 2.6.5; check Graywolf version/update; decide whether to try Ramble / PocketCHIRP (no commitment made).
- **[DECISION NEEDED — public repo]** (a) APRS-IS passcode is committed in many files (APRS passcodes derive from the callsign by a public algorithm, so low risk, but it conflicts with the "no passwords" rule); (b) K2GIA-1 coordinates appear in `docs/k2gia-5-aprsdroid-reference.md`; (c) `docs/td-h9-odmaster-aprs-messaging-bug.md` contained a retailer order number and full name — **DONE 2026-10-13: removed** (also the full name in the session-log and CLAUDE_CONTEXT-backup headers). **Passcode: deliberately left** — it is derived from the callsign by a public algorithm, so Charles decided not to scrub it. **(b) coordinates: still OPEN.** Nothing was scrubbed in the Oct 13 handoff merge itself.


### From the Sep 2 - Oct 13 ops / APRS / backups / GitHub handoff
- **[OPEN] Confirm the `graywolf-watchdog` timer state on cnjmesh1** and reconcile the wording in `cnjmesh1-operations.md` (see the update note there; old text left in place).
- **[OPEN] SD-card image backup:** is the `.gz` image on the laptop, complete, and where? Document the sudoers rule that was added (`/etc/sudoers.d/` on cnjmesh1) and decide whether to keep it. Then buy a new 64 GB (or larger) card and plan the swap. See `docs/backup-runbook.md`. (Related existing item: SATA SSD idea above.)
- **[OPEN] cnjmesh3 backup was dated 2026-07-26** as of Sep 2 — over a month old; current state unknown.
- **[OPEN, carried]** SJMesh relay topic fix (top of this file) — handoff shows it still not applied as of the Sep 6 repo state; status afterward unknown. Credential rotation items above — nothing in this handoff shows any rotation; a Discord webhook pasted Sep 2 matched the known unrotated leaked one by string match [S].
- **[OPEN, carried]** meshcore-bot weather-alert truncation fix lives only on cnjmesh1's filesystem (not in git); real confirmation (a live NWS alert) was pending [S].
- **[WATCH] Graywolf "RXT" LoRa APRS fork** — no action; check upstream for merges before revisiting (`docs/lora-aprs-reference.md`).
- **[OPTIONAL]** weekly APRS check-in nets table saved in `docs/aprs-bulletins-and-bridging-reference.md`; add a reminder only if Charles wants one, and decide whether to test a check-in through K2GIA-1.


### From the Sep 24 / Oct 13 APRS RX recovery + GitHub push investigation handoff
- **[DECISION] Keep or remove the Graywolf RT-scheduling override** (`graywolf.service.d/override.conf`) — it showed no benefit. POLLERR root cause unresolved; the Digirig replug is a workaround.
- **[OPEN] What was physically unplugged ~15:51-15:55 on Sep 24** — hub power-cycle or Digirig only?
- **[OPEN] Diff the live Graywolf Discord bridge script against the repo copy** (`md5sum` both, on cnjmesh1).
- **[DONE Oct 14, [V]] `/dev/kpc1` / `/dev/kpr1` mapping on cnjmesh1:** `/dev/kpc1 -> ttyUSB2`, `/dev/kpr1 -> ttyUSB0` (symlinks dated Sep 24 15:52); `meshcore-cli -s /dev/kpc1 infos` names the board "CNJWeatherBot" (prefix `df8a4432`). Because both boards share serial `0001`, the symlinks only name USB *ports*; only `infos` says which board is which.
- **Update on the "Graywolf PTT device pinning" item above:** `ptt_configs` already holds the by-id path (date unknown). Item can be closed once Charles agrees; old wording left in place.
- **Update on the Aug 17 POLLERR item above:** "proven cosmetic" is too strong — see `known-issues.md` update. The RT override was tried Sep 24 with no effect.
- **[OPEN] GitHub push from cloud chats:** unresolved on the platform side per the aprs-github handoff (reports similar to anthropics/claude-code issues #84581 and #96609, [S] unverified here). Charles's timeline: pushes worked ~6 months and stopped after about Sep 8. The Claude GitHub App was installed on `charlessomogyi-eng` Oct 13 (repo selection unconfirmed). The repo owner account is `charlessomogyi-eng`; make sure that account is the one logged in.


### From the Oct 4-13 KPR3 / KPC2 500 kHz cutover handoff
- **[OPEN] KPR3 remote-admin login on 500 kHz fails** while packets relay (see `known-issues.md`). Ideas, none tested: reset the contact's Out Path; re-enter admin password; check status/uptime from KPC2.
- **[DONE Oct 14, pending one confirmation] KPR2 to 500 kHz** (910.525 / 500 / SF10 / CR5; Heltec V4, cnjmesh3, `/dev/ttyACM1`, repeater console via `meshcore-cli -r`; runbook in `cnjmesh1-operations.md`). [I] strong but unproven: the Observer logged a strong type-4 advert (-25 dBm) right when KPR2 sent `advert`; whether/when KPR2 rebooted is unknown. **To confirm:** send another `advert` from its console and look for a new strong type 4 packet in the Observer log, or check CoreScope; optionally power-cycle KPR2 (USB, plus battery if connected). Old planning text for this item, kept: either reach it from inside the house on 62.5 first (phone app), or use `meshcore-cli` on **cnjmesh3**; the `meshcore-mqtt-bridge` container holds its port and has to be stopped first. Either reach it from inside the house on 62.5 first (phone app), or use `meshcore-cli` on **cnjmesh3**; per `install-map-cnjmesh3.md` the `meshcore-mqtt-bridge` container holds its port and would have to be stopped first. Method not yet chosen.
- **[DONE Oct 13, [V]] Observer moved to 910.525 / 500 / SF10 / CR5** (companion firmware v1.16.0-07a3ca9, via `meshcore-cli` over USB on cnjmesh3; procedure in `cnjmesh1-operations.md`). Replaces the earlier open item "Observer: Charles doesn't know how to change it".
- **[OPEN] Confirm in the CoreScope UI** that the CNJ Mesh Observer row is updating and KPR3/KPC2 now appear — not yet checked in the UI (capture logs show packets going to all four brokers, which is strong evidence but not the UI).
- **[OPEN] Observer clock ~27 h ahead** (see `known-issues.md`): a power cycle on Oct 14 did NOT reset it (still ~96,700 s ahead), so that test is done and failed; firmware refuses to set it backwards. Just documented unless a fix is found — if it gets fixed, record how.
- **[DONE Oct 14, [V]] KPC1 (weather bot companion, "CNJWeatherBot", Heltec V3, cnjmesh1) moved to 500 kHz** (was 910.525 / 62.5 / SF7 / CR5; now 910.525 / 500 / SF10 / CR5; firmware v1.16.0-07a3ca9; runbook in `cnjmesh1-operations.md`). Replaces the earlier open item about moving it so the bot is not deaf.
- **[OPEN] KPR1** (Tilly bridge) — now the **only** MeshCore node still on 62.5 kHz. Blocked on the RX_LOG_DATA/LOG_DATA question above; per Charles, Tilly plans to move to 500 kHz when he gets home [S], so KPR1 follows Tilly. Oct 14 evidence that KPR1 is physically connected to cnjmesh1 [V]: `/dev/kpr1 -> ttyUSB0`, and the `meshcore-mqtt-kpr1-bridge` container healthy, up 2 months (KPR1 itself was not touched). The "KPR1 RETIRED" row in the Node Reference table of `cnjmesh1-operations.md` still contradicts this; left unedited pending Charles confirming its status.
- **[OPEN] path.hash.mode** on KPR1/KPR2: unchanged, decision pending.
- **[OPEN] Confirm KPR3 reaches Tck's area via the Yagi** (send one advert from KPR3 on 500); record KPR3's actual TX power; decide whether the Yagi setup is within the module's grant (see `cnjmesh1-operations.md` caution).
- **[OPEN] Community notice** of the cutover (Discord/Facebook).
- **[OPEN] Confirm Observer model** (WisMesh Pocket v2 vs Mini) and fix the KPR1 "retired" row in `cnjmesh1-operations.md`.


### From the Oct 9-13 KPN2 (T-Deck Plus) WiFi / IP reservation handoff
- **[OPEN] KPN2 phone/WiFi (TCP) management not working — BaseUI switch unconfirmed.** TCP from the phone app to 10.0.0.140 fails while MUI is running (MUI holds the single client slot). BaseUI switch attempted Oct 9, result ambiguous [I]. Likely fix (unverified): reflash to stable firmware (2.7.19+; current is dev build 2.7.15.567b8ea) and retry. Until resolved, USB + web client is the only confirmed management path.
- **[OPEN] KPN2 WiFi U.FL antenna keeps popping loose** — consider a drop of clear nail polish or kapton tape over the seated connector once the correct socket is confirmed.
- **[OPEN] Which broker does KPN2 actually use?** See the MQTT flag in `cnjmesh1-operations.md` (only cnjmesh2's Mosquitto was checked).
- **Update on the `meshuser` credential rotation item above:** KPN2 uses `meshuser`; rotating it on whichever broker KPN2 connects to means reconfiguring KPN2 as well. Original item unchanged.
- **Update on the "In-transit hardware ... 2x Alfa antennas (one for the T-Deck/KPN2 ...)" item above:** KPN2's WiFi now works, but that is separate from RF range; confirm whether the Alfa antennas arrived and whether the T-Deck one is still wanted. Status unknown.
- **[OPEN] Heltec Mesh Node T096 battery splice not done.** T096 is a Heltec product (nRF52840), not LilyGo. It uses a JST SH 1.25 mm (1.25-2P) battery connector; Charles has a 10,000 mAh battery with a PH2.0 connector. Splice plan [S]: verify polarity with a multimeter first, cut/splice one wire at a time, solder + heat shrink. Charging a 10,000 mAh pack through the T096's USB-C will be very slow (charger designed for small cells) [S].

### [OPEN — needs a live check on the Pi] KPR1 status and Graywolf watchdog state (added Oct 13, 2026)
Two repo conflicts can only be settled by looking at the real hardware. Walk through them with Charles when he is at the terminal (commands to be given then, each with the host named):
1. **KPR1 "retired" vs "not retired":** the MeshCore Node Reference table in `cnjmesh1-operations.md` says RETIRED; the USB table in the same file and `todos.md` (Tilly integration) say it is active. Settle what is actually plugged in and running, including `/dev/kpr1` vs `/dev/kpc1` (both share serial `0001`), then fix the wrong row.
2. **Graywolf watchdog:** the "Known Issues / Don't Touch" section, "Common Problems" item 5 and `docs/aprs-2m-graywolf-reference.md` say it is disabled; the "Monitoring — Current State" section and `watchdogs/graywolf-watchdog/README.md` say it is an active alert-only watchdog on cnjmesh1. Confirm the real timer state on cnjmesh1, then reconcile the wording.
- **[OPEN, low] What does `meshcore-mqtt-bridge` actually get from KPR2?** The bridge sends a companion handshake (`appstart`) to KPR2, a repeater, which did not answer companion commands when `meshcore-cli infos` tried (Oct 14). The bridge still logs "CONNECTED" at the serial level and publishes its connection event. Whether it forwards any useful KPR2 data is unclear [I]; predates today (Aug 4 health sweep called KPR2 "both connected"). No change made.
- **[NOTE Oct 14]** `meshcore-mqtt-bridge` on cnjmesh3 was stopped ~10:28-10:53 AM Eastern for the KPR2 change, so KPR2's MQTT feed through that bridge has a gap. After an Observer power cycle, restarting `meshcore-packet-capture` is a cheap precaution [I].

### From the Oct 14 KPC1 / weather-bot outage / watchdog handoff
- **[OPEN] Confirm the weather bot transmits on 500 kHz** — Oct 15 7:05 AM forecast, or a `test` message from KPC2. Received on 500 already ([V], live Public message). The earlier bot log noise ("NO RF DATA found for channel message after all correlation attempts" right after startup, many `[62B blob data]` lines) was not investigated.
- **[OPEN] Watchdog alert test result.** Restarting the bot flipped the `meshcore-bot-watchdog` state dead -> active, which should post "CNJMESH cnjmesh1: meshcore-bot back up and running" at its next run (~11:18 AM Oct 14). Record whether it appeared in Discord. Also search the alerts channel for "meshcore-bot is DOWN" around Sep 24, 3:50 PM to learn whether the original alert ever arrived.
- **[PENDING APPROVAL] Improve `watchdogs/meshcore-bot-watchdog/watchdog.py`** (nothing built or deployed): retry the Discord post until accepted before saving state; reminder (e.g. daily) while dead; fix the cooldown swallowing the "back up" message; one limited recovery attempt (`systemctl reset-failed meshcore-bot && systemctl start meshcore-bot`, a few times a day at most) reporting success/failure; keep the webhook as `REPLACE_ME` in the repo. Needs Charles's go-ahead; deploy steps would name cnjmesh1.
- **[OPEN, low] Consider enabling the bot's own radio-offline alerts** (`radio_offline_alert_enabled` / `radio_zombie_alert_enabled` are `false`) — or deliberately leave off.
- **[OPEN, low] Physically label the KPC1 and KPR1 boards** (identical USB serial; Charles was confused on the bench; `infos` is the only software way to tell them apart).
- **Still open from earlier today:** KPR2 confirmation advert, KPR3 admin login from KPC2 on 500 kHz, Observer clock, CoreScope UI check, bridge/KPR2 data question, Graywolf watchdog state check on the Pi.
