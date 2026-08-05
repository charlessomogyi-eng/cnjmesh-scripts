# Aug 2-4, 2026 Get-Well Session — Top-Level Summary

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
- 🟡 Phase 3 (health sweep) — DONE except KPR1 device-path fix (deprioritized)
- 🟡 Phase 4 (new-board regressions: cgroups, tooling baseline, cruft cleanup) — NOT started
- ⬜ Phase 5 (OS/kernel update) — NOT started, its own dedicated session
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
