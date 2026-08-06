# Aug 2-5, 2026 Get-Well Session — Top-Level Summary

## ✅ UPDATE AUG 5 ~23:30 EDT — Malla investigated and closed out for tonight
**Malla confirmed NOT broken, and measurably improved.** Following the sjmesh loop fix (below), Malla was still slow. Investigated same evening: loop confirmed fully stopped (verified via packet-rate data, not just assumed); ~56K rows of loop residue found and cleaned from Malla's DB + VACUUMed; gateway-stats query improved **96.274s → 39.819s**. Root-caused the remaining gap vs. the 11-24s post-reboot baseline to Malla's upstream cache design (in-process, not shared across gunicorn's 2 workers) — understood, not fixed (not worth forking a third-party image for a cosmetic dashboard-stat issue); most likely explanation for the residual gap is ongoing memory/swap pressure, which is Phase 4's job. `mesh_bot_reporting.service` also fixed (two real bugs: group-permissions + an upstream script `UnboundLocalError`, plus one systemd cosmetic issue). Full writeup: `todos.md` (Aug 5 evening entry) + `session-log.md` (search "Malla cleanup + mesh_bot_reporting fix").

## ⚠️ ORIGINAL STATE AS OF AUG 5 ~18:30 EDT (superseded by the update above, kept for narrative continuity)
**Malla is NOT confirmed recovered.** A NEW incident (sjmesh bridge republish loop — a different bug than Aug 4's flood, but a side effect of Aug 4's own fix) was found via a 24h pre-check, root-caused, and fixed live: packet rate dropped from 68,763/hr back to a healthy 1 packet/60s, confirmed. But Malla itself was STILL timing out (30s, 0 bytes) even after a direct container restart — though NOT crash-looping, logs show it alive and grinding on a genuinely slow query ("Computing gateway statistics," still running 60+ seconds in). **FIRST THING to do in a new session: re-test Malla (give it up to 60s this time), check if it recovered on its own once the underlying pressure eased over time, and follow the numbered next-steps at the bottom of the Aug 5 session-log entry** (search session-log.md for "sjmesh bridge republish LOOP"). Also uninvestigated: a new `mesh_bot_reporting.service` failure found in the same pre-check.

Read this first for the full arc. Details are in `session-log.md` (chronological) and `lessons-learned-get-well-plan.md` (process lessons). This file is the map.

## THE HEADLINE RESULT
**Found and fixed the real root cause of weeks of instability:** three Mosquitto inbound bridges on cnjmesh1 were pulling the ENTIRE US/global Meshtastic MQTT firehose (`msh/US/#`, `msh/#`) into the local broker — 99.5% of all traffic was foreign junk (other networks' encrypted packets Malla couldn't even decode). This flooded the database, filled the disk, strained the whole Pi, and was very likely behind the recurring outages, Malla's 149-second queries, and cascading instability across CoreScope/Discord relays/everything else on the box.

**Fixed by rescoping the 3 inbound bridges to CentralNJ+NJ only.** Verified with data: packet rate dropped ~3x and went from 99.5% foreign to 100% legitimate traffic. Purged 5.24M pre-existing junk rows, VACUUMed the DB (3.1GB → 1.4GB). Malla query time: 149s → 24.2s → 11.1s (post-reboot, warm).

## EVERYTHING FIXED THIS SESSION
1. **Mosquitto bridge flood** (the root cause) — `docs/mosquitto-bridge-flood-fix.md`
2. **Malla performance** — retention (30d) + gunicorn (2 workers) properly configured, junk purged, DB VACUUMed
3. **cloud-init-network.service** — failing every boot since Jul 20 (immutable flag on /etc/hosts), fixed
4. **cnjmesh3 missing Docker log rotation** — same disk-fill risk as cnjmesh1 had, fixed proactively before it caused damage
5. **CoreScope chronic local-source instability** — root cause CONFIRMED (client-side reconnect bug, half-open socket); fix = restart CoreScope (not just Mosquitto) whenever Mosquitto restarts
6. **LoRa APRS Discord bridge** — found the script never actually loaded its own .env file (no dotenv logic); fixed the invocation, K2GIA-10 config confirmed correct (end-to-end delivery still unconfirmed, deprioritized)
7. **mesh_bot 7am weather broadcast** — confirmed the mechanism works, schedule verified correct for next run
8. **meshcore-hub-web 502** — found the stack's local port-override file wasn't being loaded (no systemd unit enforces `-f docker-compose.local.yml`), fixed live
9. **mesh-discord-shim relays** (new-node + CentralNJ channel + NJ MQTT) — root cause was DNS resolution failure during the Jul 30 instability window; LIVE CONFIRMED working again (first message in #centralnj-mc-channel-relay in 16 days). **New watchdog deployed** (`mesh-discord-shim-watchdog`, 15-min timer) so a recurrence gets caught in minutes, not weeks.
10. **KPR1/Tilly bridge** — diagnosed (stale hardcoded `/dev/ttyUSB3`, device now enumerates as `/dev/ttyACM0`; stable by-id path identified). NOT yet applied — deprioritized, low stakes.

## THE GET-WELL PLAN PHASES — STATUS
- ✅ Phase 1 (Malla fix) — DONE, exceeded scope
- ✅ Phase 2 (deliberate reboot) — DONE, fully verified
- ✅ Phase 3 (health sweep) — FULLY DONE as of Aug 6 ~01:22 EDT (KPR1 device-path fixed using a stable by-id mapping, closing the last open item). Full record in `session-log.md`.
- ✅ Phase 4 (new-board regressions: cgroups, tooling baseline, cruft cleanup) — FULLY DONE as of Aug 6 ~00:30 EDT (log rotation on all 14 containers + a real network_mode bug caught along the way, dnsutils installed, memory cgroups enabled + reboot verified, 3 orphaned images + build cache removed ~1GB reclaimed). Full record in `session-log.md`.
- ⬜ Phase 5 (OS/kernel update) — NOT started, its own dedicated session. Note: 410 packages showed upgradable on cnjmesh1 as of Aug 5 — relevant context for this phase.
- ⬜ Phase 6 (finalize Tilly's fork on KPR1) — NOT started, gated behind everything above

## WATCHDOGS THAT EXIST NOW (as of tonight)
- `corescope-watchdog.timer` — alert-only, checks aggregate tx_inserted (has a known blind spot: multi-source aggregation can mask a single dead source)
- `graywolf-watchdog.timer` / `graywolf-discord-watchdog.timer` — alert-only, deliberately NOT auto-restart (TX-capable radio)
- `mesh-discord-shim-watchdog.timer` — NEW tonight, alert-only, checks for Discord post failures every 15 min

**None of these auto-heal anything except by alerting a human.** That's a deliberate, mostly-correct design (auto-restarting things unattended has real risk) but worth remembering when reasoning about "will this recover on its own."

## WHAT TO WATCH OVER THE COMING DAYS
- **UptimeRobot / Fing:** did the recurring 530 outages and overnight drops STOP now that the bridge flood is fixed? This is the real test of whether that was the root cause of the outage pattern too, not just Malla's slowness.
- **mesh-discord-shim-watchdog:** should stay quiet. If it fires, that's real signal.

## STILL OPEN / NOT DONE
- Malla XSS vuln (CVE-2026-43980) / upgrade decision — undecided, revisit
- Phase 4 (cgroups, tooling, cruft cleanup) and Phase 5 (OS update) — not started
- KPR1/Tilly device-path fix — diagnosed, not applied
- LoRa APRS end-to-end delivery — unconfirmed, deprioritized
- The recurring cnjmesh1 gateway-unreachable network issue — happened AGAIN this session (nmcli fix applied each time) — still not root-caused as its own standalone issue, separate from everything else fixed tonight

## READ THIS TOO: `docs/lessons-learned-get-well-plan.md`
10 process lessons from tonight — the `git commit -a` bug that lost several docs, a production-config-change-without-clear-confirmation incident, stale documentation causing false alarms, watchdogs not being what their names implied, USB path instability, and more. The honest theme: most of tonight's real mistakes were about communication and verification discipline at the moment of taking action, not diagnostic skill. Worth a read at the start of the next session so the same mistakes aren't repeated.
