# Prevention Framework & Catastrophic-Issue Runbook

**Purpose:** Never go through the Jul-Aug 2026 saga again. That incident dragged on for WEEKS because (a) nothing caught the root cause (mosquitto bridge flood) early, (b) there was no baseline to notice drift against, and (c) there was no triage order — we chased symptoms (Malla slowness, disk fill) for days before finding the actual cause (foreign traffic flooding the broker).

This document is two things: **prevention** (stop it happening) and a **runbook** (what to do when something IS wrong, in what order).

---

## PART 1 — WHY THE LAST ONE WAS SO BAD (so we prevent the actual failure modes)

The root cause was ONE thing (3 mosquitto inbound bridges pulling the entire US/global Meshtastic firehose into the local broker). But it cascaded into MANY visible symptoms:
- Malla DB bloated to 9.4M rows / 3.1GB → 149s queries
- Disk filled repeatedly
- CPU/memory pressure → gateway drops, service instability
- Downstream relays (Discord) failed on transient DNS during the strain

**The lesson: a single upstream problem produced a dozen downstream symptoms, and we spent days treating symptoms.** Prevention must catch the UPSTREAM cause early, and the runbook must force checking upstream causes FIRST.

The three failure classes that actually hurt:
1. **Unbounded ingestion** (foreign traffic flood) — no cap on what enters the broker.
2. **Unbounded growth** (DB rows, log files) — no retention/rotation → disk fills.
3. **Silent failures** (Discord relay down 16 days, weather bot missed, cloud-init failing every boot) — no monitoring → problems invisible until noticed by luck.

---

## PART 2 — PREVENTION (the standing safeguards)

### 2A. Catch unbounded ingestion (the actual root cause)
- **Broker topic scope is a first-class config.** Mosquitto inbound bridges must ALWAYS be scoped to specific named channels (CentralNJ, NJ, and explicitly-chosen neighbor channels) — NEVER `msh/US/#` or `msh/#`. cnjmesh2's config is the reference for "done right." The sanitized correct config is committed at `cnjmesh1/configs/mosquitto-cnjmesh1.conf`.
- **New monitoring to build (TODO): a broker ingest-rate watchdog.** Alert if packets/hour into the local broker exceeds a sane threshold (normal CentralNJ is a few thousand/hr; the flood was ~68,000/hr). This would have caught the entire saga on DAY ONE. HIGH VALUE — build this next.
  - Implementation sketch: periodically query Malla's packet_history for count in the last hour; if > threshold (e.g. 15,000/hr), alert to #cnjmesh Discord. Same watchdog pattern as the others.
  - Even better: alert on the % of UNKNOWN_APP or non-CentralNJ topics — the flood was 99.5% foreign. A "foreign traffic %" alert is an even more direct signal.

### 2B. Catch unbounded growth
- **Docker log rotation is MANDATORY on every Pi.** `/etc/docker/daemon.json` with `max-size: 10m, max-file: 3`. CONFIRMED on cnjmesh2, cnjmesh3. VERIFY on cnjmesh1 (was never explicitly confirmed — the mqtt-filter fix was removal, not rotation). Any new Pi gets this on day one.
- **Malla retention is set** (`MALLA_DATA_RETENTION_HOURS`, currently 720/30d). Keep it set. Now that the flood is gone, the DB should stay small.
- **New monitoring to build (TODO): disk-space watchdog.** Alert at 75% and again at 90% disk on every Pi. Disk-full was a repeated symptom all week — a simple `df` check every 15 min catching it at 75% would have prevented every disk emergency. HIGH VALUE, trivial to build.

### 2C. Catch silent failures (the "invisible for 16 days" problem)
The single biggest lesson: **things failed silently for days/weeks because nothing was watching.** Every critical service needs a watchdog that alerts on failure. Current state:
- ✅ corescope-watchdog (alert-only, has a known multi-source blind spot)
- ✅ graywolf-watchdog / graywolf-discord-watchdog (alert-only, deliberately no auto-restart)
- ✅ mesh-discord-shim-watchdog (NEW — alerts on Discord post failures every 15 min)
- ✅ **broker ingest-rate watchdog** (2A above) — DEPLOYED Aug 15-16, 2026 on cnjmesh1. `/opt/ingest-rate-watchdog/`, `ingest-rate-watchdog.timer` (every 15 min). Checks pkts/hr against Malla's DB directly (not via docker exec) plus whether any single node dominates ingest (the exact signature of every loop-node incident found so far). Alert thresholds: 1000/hr warn, 5000/hr urgent, single-node ≥50% share warn. Tested end-to-end including real Discord delivery to #cnjmesh — confirmed working. See session-log.md Aug 15-16 entry for full detail. Source: `watchdogs/ingest-rate-watchdog/` in this repo.
- ✅ **disk-space watchdog** (2B above) — this was actually `disk-temp-watchdog` (also covers CPU temp + undervoltage), built earlier but never deployed. DEPLOYED Aug 15-16, 2026 on cnjmesh1 (`disk-temp-watchdog.timer`, every 5 min) — was sitting finished in `watchdogs/disk-temp-watchdog/` in this repo for weeks with nothing ever installing it. Tested working (disk=58.5%, temp=46.2°C, undervolt=ok at deploy time). **Still TODO: deploy the same script to cnjmesh2 and cnjmesh3** — it's already written to be host-agnostic (just needs `NODE_LABEL` set per host), just needs the same deploy steps repeated there.
- ❌ **TODO: a per-Pi "heartbeat" / uptime self-report** — cnjmesh1 going offline overnight was only caught by external Fing/UptimeRobot. A lightweight self-heartbeat to a monitor would make outages obvious immediately.
- ❌ **TODO: weather-broadcast success monitor** — the 7am mesh_bot weather silently missed; nothing noticed. Alert if the daily broadcast doesn't fire.

**Watchdog design principles (learned this session):**
- Detecting FAILURES (error in logs) is easy but has a blind spot: total SILENCE / a hung process logs no error. Where it matters, check "time since last SUCCESS," not just "presence of errors."
- Alert-only is the safe default. Auto-restart only for LOW-RISK services (data ingestion containers — safe) NOT high-risk ones (TX-capable radios like Graywolf — unsafe to key up unattended).

### 2D. Keep a known-good baseline
- **`collect-inventory.sh` should be run regularly** (e.g. weekly or after any significant change) so `install-map-*.md` reflects reality. This session hit multiple cases where documented ports/paths were STALE (meshcore-hub port, KPR1 device path) and cost real diagnosis time. A current baseline makes "what changed?" answerable.
- **Capture a healthy-state snapshot:** normal packets/hour, normal Malla query time, normal load average, normal disk %. Without a baseline, you can't tell "degraded" from "normal." (Tonight's numbers are a start: healthy Malla cold query ~11-24s, load should settle well below 7-8, normal CentralNJ traffic a few thousand packets/hr.)

### 2E. Durability hygiene (so reboots don't break things)
- **All USB device mappings must use `/dev/serial/by-id/` paths, never `/dev/ttyUSB*`/`/dev/ttyACM*`.** Numbered paths reshuffle on reboot (this broke KPR1 tonight). Standing TODO: audit ALL device mappings across cnjmesh1/cnjmesh3.
- **Every Docker-compose stack needs a systemd unit** that starts it correctly (with the right `-f` override files and `--profile` flags). meshcore-hub broke tonight because NO systemd unit managed it and a plain `docker compose up` dropped the port override. Any stack without a unit is a reboot landmine.
- **After ANY reboot, run the post-reboot checklist** (`docs/health-check-plan-aug2026.md` + the Phase 2 verification in session-log): all containers, all systemd services, USB devices, network, mosquitto bridges, web services.

---

## PART 3 — CATASTROPHIC-ISSUE RUNBOOK (what to do WHEN something is wrong)

When multiple things seem broken at once, or the system is unstable, DO NOT start fixing the first symptom you see. That's what cost days last time. Work this order:

### STEP 0 — Stabilize, don't thrash
If the box is at 100% disk or unresponsive: free just enough space to make it workable (truncate the biggest log/file), then STOP and diagnose. Do not start restarting random services.

### STEP 1 — Check UPSTREAM causes first, in this order:
1. **Ingestion rate** — is the broker being flooded? Query packets/hour and topic breakdown:
   ```
   docker exec mqtt-malla-web-1 python3 -c "import sqlite3,time; c=sqlite3.connect('/app/data/meshtastic_history.db'); h=time.time()-3600; print('pkts/hr:', c.execute('SELECT COUNT(*) FROM packet_history WHERE timestamp>?',(h,)).fetchone()[0]); [print(r[1],r[0]) for r in c.execute('SELECT topic,COUNT(*) ct FROM packet_history WHERE timestamp>? GROUP BY topic ORDER BY ct DESC LIMIT 10',(h,))]"
   ```
   If pkts/hr is huge or topics are foreign (GraveYard, SJMesh-wildcard, non-CentralNJ) → THIS IS THE ROOT CAUSE. Check mosquitto.conf inbound bridge topic scopes. Do not chase Malla/disk symptoms.
2. **Disk** — `df -h /`. If filling, find what's growing: `sudo du -sh /var/lib/docker/containers/*/*-json.log | sort -rh | head` and check the Malla DB size.
3. **Memory/load** — `free -h && uptime`. High swap + load = resource exhaustion, often downstream of #1.
4. **Network** — `ping -4 -c3 10.0.0.1`. If gateway unreachable → the recurring nmcli-bounce issue: `sudo nmcli connection down/up "C4Somogyi-24"`.

### STEP 2 — Only after upstream is clear, check individual services
Containers (`docker ps -a`), systemd (`systemctl --failed`), web endpoints (curl the ports/hostnames). The health-check plan has the full list.

### STEP 3 — Fix at the SOURCE, not the symptom
The recurring theme: cutting Malla retention, adding gunicorn, VACUUMing — all treated symptoms. The fix was stopping the foreign traffic at the broker. Always ask: "is this the cause, or a downstream effect of something upstream?"

### STEP 4 — Standing rules while fixing (from lessons-learned)
- State the plan and get explicit OK BEFORE changing any production config — even reversibly.
- Back up any file before editing (`cp file file.bak-<reason>-<date>`).
- Use Python scripts, not sed, for complex config edits.
- Every command names its target host.
- Claude pushes all git changes; verify pushes with a fresh clone, don't trust "PUSH OK".
- After a fix, VERIFY with data (before/after numbers), don't assume.

---

## PART 4 — THE HIGH-VALUE TODO LIST (build these to prevent a repeat)
In priority order — each of these would have caught the last saga early:
1. **Broker ingest-rate + foreign-traffic-% watchdog** — would have caught the root cause on day one. HIGHEST VALUE.
2. **Disk-space watchdog (75%/90%)** on all 3 Pis — would have caught every disk emergency. Trivial to build.
3. **Verify/confirm Docker log rotation on cnjmesh1** (Phase 4).
4. **Per-Pi heartbeat monitor** — make overnight outages immediately visible.
5. **Audit all USB mappings → by-id paths** (Phase 4 / durability).
6. **systemd units for any compose stack lacking one** (meshcore-hub at minimum).
7. **Regular `collect-inventory.sh` runs** to keep the baseline current.
8. **Capture a documented healthy-state baseline** (normal pkts/hr, query time, load, disk) so drift is detectable.

Building #1 and #2 alone would have turned a WEEKS-LONG saga into a same-day fix. That is the entire point of this document.
