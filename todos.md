# CNJ Mesh — Open To-Dos

### [DECIDED Aug 16 — keeping permanently] Meshview LongFast visibility test on liamcottle bridge
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

### peer-check — DISABLED on cnjmesh2 and cnjmesh3, root cause never diagnosed
Disabled July 28 after Charles reported unwanted/wrong Discord alerts — root cause never actually investigated (false flapping? wrong service list? wrong peer IP? — unclear which). Service/timer files still present, re-enable anytime with `sudo systemctl enable --now peer-check.timer` once the underlying issue is understood. **Also:** peer-check was never installed on cnjmesh1 itself — minor redundancy gap (cnjmesh2/3 currently watched by only one peer each instead of two).

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
- **Cosmetic:** rename "APRS 2m (Graywolf)" → "Graywolf APRS 2M" in peer-check's SERVICES config on cnjmesh2/cnjmesh3.
- **Fing Agent** — old dead board's MAC still shows stale alerts; deactivate that entry. Worth double-checking `ps aux | grep -i fing` isn't still running under the old identity before assuming it's purely a stale UI entry.
- **[NEW Aug 18]** UV-5R M needs to move back to whip antenna — roof dual-band antenna (used for APRS since Aug 17) is needed back for voice (Icom 2730). When done: re-run POLLERR frequency check (`journalctl -u graywolf --since "5 minutes ago" --no-pager | grep -c "cpal input stream error"`) to see if error rate drops — would help confirm/rule out the antenna-load theory from the Aug 17 cpal investigation. Update `docs/aprs-2m-graywolf-reference.md` once done.
- **[NEW Aug 18 — still open, narrowed]** Original question — Charles not seeing certain CentralNJ messages on KPN6 (app) / Discord that he used to see — is STILL UNRESOLVED, but now narrowed: confirmed the SJMesh relay, mosquitto broker, and Malla ingestion are all healthy and actively receiving CentralNJ traffic in real time (verified via direct DB query — see session-log.md Aug 18 for the resolved false-alarm investigation and the correct Malla DB path/schema). So the actual gap, if still present, is downstream of ingestion — either in the Discord bridge logic or in KPN6's RF downlink reception specifically (KPN6's own MQTT module is intentionally disabled, so it only ever hears this traffic as plain rebroadcast RF from CJG1/CJG2's downlink — that link was never directly tested this session). Next step: compare a specific live timestamp from Malla's DB against what actually shows up in Discord/KPN6 at the same moment, rather than general sampling.

---

**[NEW Aug 18 — resilience/security review]** A handful of ideas surfaced from an end-of-session environment review, worth working through over a few nights:
- **Port `ingest-rate-watchdog` to cnjmesh2** — it runs Malla capture on the raw (unfiltered) firehose too, same flood/loop-node exposure that caused the original cnjmesh1 disk-fill saga, currently unwatched there.
- **Confirm Docker log rotation is actually configured on cnjmesh3** — cnjmesh1 and cnjmesh2 both got the `daemon.json` fix after the 37GB/35GB log-fill incident; cnjmesh3 was never checked. Quick: `cat /etc/docker/daemon.json` on cnjmesh3.
- **`peer-check` is disabled on cnjmesh2/cnjmesh3 and was never installed on cnjmesh1** — currently nobody is watching anybody. Revisit once the original false-alert root cause (never diagnosed) is understood, or reconsider the whole approach.
- **Reuse the sjmesh-relay heartbeat-file pattern for other bridges that only report "service is active," not "is actually doing useful work"** — candidates: `mesh-discord-shim`, `graywolf-discord-bridge`, `aprs_monitor.py`. Tonight proved "systemd says active" isn't sufficient to know a bridge is actually relaying anything.
- **Rotate `meshuser`/`[REDACTED - broker password, scrubbed Aug 30 2026]` on your own `mqtt.cnjmesh.me`** — distinct from SJMesh's own `meshuser` credential (not yours to rotate); this one is genuinely yours and still pending.
- **Apply the Malla CVE-2026-43980 fix** — real upstream patch exists (commits >=4086e2b5f6161...), just needs the careful pull-and-verify process (note current image digest first, back up DB, pull, check for migration errors) given custom DB state from the Aug 15 dedup rebuild.
- **Remove leftover `hello-world` container on cnjmesh2** (`zealous_joliot`, exited) — pure cruft from testing, harmless, quick `docker rm` whenever convenient.

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


