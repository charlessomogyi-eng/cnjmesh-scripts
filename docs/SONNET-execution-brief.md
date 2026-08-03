# EXECUTION BRIEF — for Sonnet 5 (get-well plan for Charles's mesh/Pi environment)

Opus 4.8 did the diagnosis (Aug 1-3, 2026). This brief tells you (Sonnet) how to EXECUTE the fixes. The thinking is done and documented — your job is careful, methodical execution following the existing plans. Do NOT re-diagnose or improvise; follow the docs.

## STEP 0 — ALWAYS load context first (every session)
Charles's standing rule: at the start of any CNJ Mesh session, pull context via bash (NOT web search):
```
curl -s https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/CLAUDE_CONTEXT.md
```
Then read these in the repo (fetch raw from GitHub): `todos.md`, `session-log.md`, and the plan docs referenced below. The `todos.md` top section has the current priority order.

## HARD RULES (Charles's, non-negotiable)
- **Every command block MUST name its target host explicitly** (cnjmesh1 / cnjmesh2 / cnjmesh3). Charles has said this repeatedly.
- **Before ANY step-by-step instructions for a third-party app/website/bot, web-search current official docs FIRST.** Never answer from memory for those.
- **Never present a command then correct it mid-response** ("wait/oh wait"). Get it right the first time, correct execution order.
- **For code edits on the Pis, use a Python-script approach** (`cat > /tmp/fix.py`), never sed for complex replacement.
- **Charles never runs git add/commit/push himself.** YOU push doc updates using the token he provides in-session. Track changes proactively, update docs, push without being asked. (Token is provided per-session and revoked after — ask for it when you need to push if not already given.)
- **Never remove/disable meshview or Malla on cnjmesh1** (protected services) unless Charles explicitly says so.
- No "good night"/pleasantries. Professional, direct. Concise.
- Charles is an expert (25+ yrs IT/backup). Don't over-explain or remind him you lack SSH access — he runs the commands, you guide + track.

## THE GET-WELL PLAN — execute in THIS ORDER

### Framing to keep in mind (don't treat "is it the hardware" as one yes/no)
Problems predate all board swaps → likely BOTH: (A) carried-over data/config issues (being fixed) + (B) new-board regressions (cgroups/networking/tooling, unaddressed). Attribute cause by watching which fix reduces outages. See `docs/` + session-log Aug 3.

### PHASE 1 — Malla fix on cnjmesh1 (biggest daily pain, low-risk config)
Follow `docs/malla-fix-plan-cnjmesh1.md` EXACTLY, in order:
- Step 0: fresh DB backup (don't skip).
- Step 1: show current compose files (ask Charles to cat them) — get exact layout before editing.
- Step 2: enable `MALLA_DATA_RETENTION_HOURS` (recommend 1440=60d) on malla-capture. Back up file first. `docker compose up -d malla-capture`. Verify raw-topic override preserved (`MALLA_MQTT_TOPIC_PREFIX=msh`, `SUFFIX=/US/#`) + retention picked up.
- Step 3: `MALLA_WEB_COMMAND=/app/.venv/bin/malla-web-gunicorn` on malla-web (start `MALLA_GUNICORN_WORKERS=2`, `THREADS=2` — memory-tight box). Back up file. `docker compose up -d malla-web`. Verify gunicorn running (no dev-server warning). Test 2 concurrent curls don't block.
- Step 4: public check malla.cnjmesh.me + reassess whether `malla-warmcache.timer` is still needed with gunicorn.
- Step 5: document + push (re-run collect-inventory.sh on cnjmesh1, update session-log/install-map).

### PHASE 2 — cnjmesh1 deliberate reboot (clears 9+ days memory pressure)
Only after Phase 1 verified stable. Charles wants to watch services come back (16 containers + systemd). Reboot, then verify all containers + systemd services recovered, USB serial radios enumerated, WiFi/gateway good.

### PHASE 3 — Full health-check sweep
Follow `docs/health-check-plan-aug2026.md` + `docs/pre-tilly-master-checklist.md`. Covers all 3 Pis + Malla/Meshview/APRS/Graywolf/LoRa APRS/Observer/KPR2/Meshomatic/CoreScope/MeshCore Hub. Also diagnose the NEW issue: **MeshCore Discord new-node relay not working** (`mesh-discord-shim`, cnjmesh1 — check container/logs/webhook validity). Also check the **Tilly/KPR1 bridge log volume + docker stats** (rule out as resource contributor).

### PHASE 4 — new-board regressions (Layer B, from Jul 31 findings)
- Add Docker log rotation on cnjmesh1 (`/etc/docker/daemon.json` json-file 10m x3) — needs `systemctl restart docker` (bounces containers; do watched). This is belt-and-suspenders now the mqtt-filter flood is gone.
- Add `cgroup_enable=memory cgroup_memory=1` to `/boot/firmware/cmdline.txt` (needs reboot — can combine with Phase 2 reboot if sequenced). Restores per-container memory limits/accounting.
- Restore tooling baseline: `apt install dnsutils` etc.
- Clean up leftover cruft in /opt/stacks/mqtt: `mosquitto.env2`, `config/mossquitto.conf2`, `docker-compose.override.yaml1`.

### PHASE 5 — cnjmesh1 OS/kernel update (its OWN session)
Follow `docs/cnjmesh1-os-update-plan.md`. `apt upgrade` (NOT full-upgrade), reviewed, full backup first, watched reboot, health sweep after. Only after Phases 1-4 stable.

### PHASE 6 — Finalize Tilly's fork on KPR1 (LAST — the pre-Tilly gate)
Only after everything in `docs/pre-tilly-master-checklist.md` is 100% green. Then diagnose/complete the KPR1→Tilly AWS broker connection.

## ONGOING — monitor the outage question
Charles has UptimeRobot (meshview + maybe others) + Fing. Watch whether the Aug-2 disk fix reduces the 530 outages over coming days. If they stop → disk was the driver. If they persist → residual is new-board regression or network/DHCP flap → investigate via `journalctl` on cnjmesh1 for the exact incident window (the Pi's own logs are the only real cause source — the 530 code alone tells you nothing about why).

## DEFERRED (don't do unless Charles asks)
- Anubis / malla2 changes (prove Malla fix on cnjmesh1 first).
- Moving Fing off cnjmesh1 (keep it as outage canary until overnight-drop solved).
- Malla XSS/upgrade decision (undecided; separate).
- Any cloud-hosting (Hetzner attempt was abandoned; do NOT restart without Charles explicitly asking).

## Bottom line for Sonnet
Everything is planned and documented. Go phase by phase, host-labeled commands, verify between steps, push doc updates as you go. Ask Charles for the git token when you first need to push. If something genuinely doesn't match the plan or a real new decision arises, surface it to Charles rather than improvising.
