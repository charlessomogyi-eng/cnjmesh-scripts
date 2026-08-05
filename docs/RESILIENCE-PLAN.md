# CNJ Mesh Resilience Plan

**Goal:** Get to "lay back and let it run." Never repeat the weeks-long Jul-Aug 2026 saga. When something breaks, the system should either fix itself, or alert with the exact problem in minutes — never turn into a multi-week archaeology dig again.

**Three pillars.** A resilient environment needs all three; you currently have fragments of each:
1. **EARLY WARNING** — catch problems in minutes, not weeks (partial: some watchdogs exist)
2. **SELF-HEALING** — routine problems fix themselves without you (minimal today)
3. **FAST REBUILD** — if a Pi/SD dies, restore in an hour, not days (partial: backup scripts exist but have gaps)

Build order below is by value-per-effort. Do them roughly in this order.

---

## PILLAR 1 — EARLY WARNING (highest value, do first)

The entire saga happened because problems were INVISIBLE. This pillar is what turns "weeks" into "minutes." Each item is a small watchdog on the same pattern as the working ones (corescope-watchdog, mesh-discord-shim-watchdog): a script + systemd timer, alerts to the shared #cnjmesh Discord webhook.

### 1.1 — Broker ingest-rate + foreign-traffic watchdog ⭐ THE ONE THAT WOULD HAVE CAUGHT EVERYTHING
This single watchdog would have caught the entire saga on day one.
- Every 15 min, query Malla for packets/hour AND the % that are non-CentralNJ.
- Alert if pkts/hr > ~15,000 (normal is a few thousand) OR foreign-% > 5%.
- This directly detects the root-cause failure class (unbounded/foreign ingestion) that no other monitor sees.

### 1.2 — Disk-space watchdog ⭐ (trivial, high value)
- Every 15 min, `df` on each Pi. Alert at 75%, alert again (louder) at 90%.
- Disk-full was a repeated symptom all through the saga. This catches it while there's still time to act calmly.
- Deploy on ALL THREE Pis.

### 1.3 — Per-Pi heartbeat / uptime self-report
- Each Pi posts a lightweight "I'm alive" ping to a monitor (or a simple last-seen file the others check) every few minutes.
- cnjmesh1's overnight outages were only caught by EXTERNAL tools (Fing, UptimeRobot). A self-heartbeat makes an outage obvious immediately and from inside.
- Keep the external UptimeRobot/Fing monitors too (defense in depth) — they catch the case where the whole Pi is down and can't self-report.

### 1.4 — Memory/load watchdog
- Alert if swap usage or load average stays above a threshold for N consecutive checks (cnjmesh1 runs hot — currently load ~7-8, swap 2GB+).
- Catches the gradual resource-exhaustion degradation we watched happen tonight (Malla 11s→20s as swap climbed).

### 1.5 — Scheduled-job success monitors
- Weather broadcast (7am mesh_bot), and any other scheduled task: alert if it DOESN'T fire when expected.
- The 7am weather silently missed for who-knows-how-long; nothing noticed.

**Coverage after Pillar 1:** every failure class that hurt you (ingestion flood, disk fill, Pi outage, resource exhaustion, silent scheduled-job failure) becomes visible within 15 minutes. This alone is the difference between the saga and a same-day fix.

---

## PILLAR 2 — SELF-HEALING (medium value, do second)

Warning is good; not needing to act at all is better. But be surgical — auto-restart is SAFE for some things and DANGEROUS for others (learned this session).

### 2.1 — Safe auto-restarts (low risk — DO these)
- **CoreScope local-source stall:** we PROVED tonight that `docker restart corescope` fixes the chronic half-open-socket bug, and that Mosquitto-restart alone does NOT. Upgrade corescope-watchdog: when it detects the local source stalled (watch the `[local]` log line specifically, not just aggregate tx_inserted), auto-restart the corescope container. Data-ingestion container = safe to bounce.
- **Any pure-software container in a crash loop / unhealthy state:** auto-restart is generally safe for stateless ingestion/web containers. (NOT for anything driving a radio.)
- **Standing rule already learned:** whenever Mosquitto is restarted, ALSO restart corescope. Could be automated as a systemd dependency/hook.

### 2.2 — DO NOT auto-restart (high risk — leave alert-only)
- **Graywolf / anything TX-capable** — keying a radio unattended is unsafe. Alert only. (Its watchdog already correctly refuses to auto-restart.)
- Anything where an unattended restart could cause real-world side effects.

### 2.3 — Auto-recovery from the known network drop
- The recurring cnjmesh1 gateway-unreachable issue has a known fix (`nmcli connection down/up "C4Somogyi-24"`). Consider a watchdog that detects gateway-unreachable (ping 10.0.0.1 fails 3x) and auto-runs the nmcli bounce, then alerts that it did so.
- CAVEAT: this treats the symptom. The ROOT cause of that network drop is still unknown (separate open investigation). Auto-healing it is fine as a stopgap but shouldn't replace finding why it happens.

### 2.4 — Log rotation everywhere (prevents the #1 growth failure)
- Already done on cnjmesh2, cnjmesh3. VERIFY/confirm on cnjmesh1. Any new Pi gets `/etc/docker/daemon.json` (10m×3) on day one. This is passive self-protection against the 30GB-log disaster.

---

## PILLAR 3 — FAST REBUILD (do third — it's insurance, not daily-use)

If a Pi or SD card dies (cnjmesh1 is a REPLACEMENT board with no track record — this is a real risk), you want a 1-hour restore, not a multi-day rebuild from memory. You have backup SCRIPTS but with GAPS.

### 3.1 — Close the known backup gaps (PRIORITY — data-loss risk today)
- **Malla DB (named volume) is NOT in the automated backup.** `cnjmesh1-backup.sh` covers bind-mount paths under stack dirs, but Malla lives in a Docker NAMED volume (`/var/lib/docker/volumes/mqtt_malla_data/`). If cnjmesh1's SD dies right now, ALL Meshtastic history is lost. FIX: extend the backup to snapshot the named volume (`docker run --rm -v mqtt_malla_data:/v -v ~/backups:/b alpine tar czf /b/malla-vol.tgz /v`, or the sqlite3.backup() approach used manually on Jul 31).
- **CoreScope's config** (local MQTT source fix: `mqtt://172.17.0.1:1883`) — documented as NOT backed up anywhere, was LOST with the last dead board and had to be manually redone. Get it into the backup or into git.
- **Config consistency:** cnjmesh2's Malla is a bind mount, cnjmesh1's is a named volume — inconsistent. Worth standardizing so backup logic is uniform.

### 3.2 — Automate + verify backups (not just have scripts)
- Schedule `cnjmesh1-backup.sh` (and the others) via systemd timer — daily. Right now backups appear to be manual/ad-hoc.
- **CRITICAL: copies must go OFF the Pi.** A backup sitting on the same SD card that dies is worthless. The `pull-cnjmesh1-backup.ps1` pulls to your laptop — automate/schedule that, or push to OneDrive/cloud. The Jul 31 Malla backup was noted as "not yet copied off-Pi" — that gap is the difference between recoverable and not.
- **A backup you haven't tested restoring is not a backup.** Once a quarter (or after big changes), actually restore a backup to a spare SD/Pi and confirm services come up. Untested backups fail exactly when you need them.

### 3.3 — Keep the rebuild runbook current
- `session-log.md` line ~485 already has a "when new board arrives" checklist. Keep it current. It should be a complete, followable "bare SD → fully working cnjmesh1" procedure.
- `collect-inventory.sh` run regularly keeps `install-map` accurate so the rebuild reference isn't stale (stale docs cost real time this session — meshcore-hub port, KPR1 path).
- Everything reproducible should be in git (configs, compose files, scripts) so a rebuild is "clone the repo + restore data volumes," not "remember what I did."

---

## THE PATH TO "LAY BACK AND LET IT RUN"

You're not there yet, but the path is concrete:

**Phase A (do first — a few short sessions):** Build Pillar 1 items 1.1 and 1.2 (ingest-rate + disk watchdogs). These two ALONE would have prevented the entire saga. After this, you get PAGED with the exact problem instead of discovering it weeks later.

**Phase B:** Close the Pillar 3.1 backup gaps (Malla volume, off-Pi copies). This removes the current data-loss risk. Small effort, high stakes.

**Phase C:** The rest of Pillar 1 (heartbeat, memory, scheduled-job monitors) + Pillar 2.1 (safe auto-restarts). Now routine problems self-heal or alert cleanly.

**Phase D:** Automate + test backups (3.2), finish the get-well Phases 4-6 (cgroups/resource tuning is what stops cnjmesh1 running hot), standardize configs.

**After all four:** the environment genuinely runs itself — self-heals the routine stuff, pages you with specifics for the rest, and rebuilds fast if hardware dies. That's "lay back and let it run" — not because nothing breaks, but because breakage is visible, bounded, and recoverable.

**Single highest-leverage next action:** build the broker ingest-rate watchdog (1.1) and disk watchdog (1.2). Everything else is important; those two are what turn "weeks" into "minutes."
