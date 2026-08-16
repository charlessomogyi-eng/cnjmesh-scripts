# CNJ Mesh — Open To-Dos

### [ACTIVE — low-risk test running, decision pending] Meshview LongFast visibility test on liamcottle bridge
Aug 15, 2026: added `msh/US/2/e/LongFast/#` + `msh/US/NJ/2/e/LongFast/#` to the `liamcottle` bridge only, to see if it closes the node-graph gap vs. MTX1's SBNJ instance. Malla isolation confirmed clean (zero LongFast rows reaching Malla's DB). Full detail in session-log.md, Aug 15 entry.

**Still open:**
1. Check `meshview.cnjmesh.me/nodegraph` after several hours/days for new nodes.
2. Decide: keep the LongFast topics on liamcottle permanently, or revert (`cp mosquitto.conf.bak-longfasttest-20260815 mosquitto.conf && docker restart mosquitto`).
3. If not worth it, fallback plan (isolated second broker + second Meshview instance) discussed but not started.
4. Meshview is v3.0.5, current release is 3.0.7 — worth a version bump eventually, though it won't close the node-graph gap by itself (relevant upstream issues #150/#151 still open).
5. Meshview runs as ad-hoc background Python processes, not a systemd service — won't auto-restart on crash/reboot. Worth converting at some point, not urgent.

### [INVESTIGATE — root cause found, no code change made] CJG1/mesh_bot Meshtastic weather broadcast — fragmentation/missing delivery
Aug 8 incident: 3 users reported issues with the 7am weather broadcast (one fragmented, one got nothing). Root cause found: message hit 341 chars vs. Meshtastic's 200-char limit, forcing a fragile 4-packet split. **Decision: not changing code based on one occurrence** — watching for recurrence before treating this as confirmed. If it recurs, fix is a hard length cap or shorter template.

### [BUG — still open] Weather bot (agessaman/meshcore-bot) alert formatting garbled
Forecast sending is fully fixed and confirmed working in production (07:05 daily, CentralNJ-MC + Discord relay). Alerts specifically still show garbled truncation (e.g. "Severe Thunders Watch Kent til 9PM by NWS MOUN") — the alert-send path likely still uses old single-message truncation instead of the chunked-send fix already applied to forecasts. Needs its own patch in the alert-sending function.

### [PARTIALLY DONE] Weather bot schedule: 7am → 7:05am
MeshCore side (KPC1) — ✅ done, confirmed in production since Aug 11. **Meshtastic side (CJG1) — still not done** — `mesh_bot.service` needs the same change whenever next touched.

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
- **Whip message-reach test** — re-run against KB2EAR (<1 mi, confirmed iGate) instead of Compy/KD2QED-7 (40+ mi, unfair test for a whip).
- **Confirm whether the 2m station is digipeating or only iGating** — iGate confirmed; Digipeater is a separate toggle, status unconfirmed.
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

---

**For AI assistants:** This is the current, lean action list. Fetch this alongside `cnjmesh1-operations.md` at the start of a session — both are short. Only fetch `session-log.md` (long, narrative, full history) if you need the backstory on *why* something is the way it is.

**Housekeeping rule:** when an item is finished, delete it from this file — don't mark it "done" and leave it. If the fact that it's finished matters for later reference, a one-line note goes in `session-log.md` instead, not here.

*Last cleaned up 2026-08-16 (Sonnet session) — removed ~20 fully-resolved/superseded items and archived a 66K-character Tilly/KPR1 debugging narrative to session-log.md, trimming this file from 505 lines to a genuinely current list. Prior cleanup was 2026-07-24.*
