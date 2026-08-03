# MASTER PRE-TILLY HEALTH CHECKLIST (Charles, Aug 2, 2026)

## The gate
**Everything below must be confirmed 100% healthy BEFORE finalizing the Tilly's-fork-on-KPR1 work.** Don't layer a new integration onto an unstable base. This is the master list; individual diagnostic steps live in `docs/health-check-plan-aug2026.md`.

## Recommended order of operations (context from Aug 2 session)
1. **Malla config fix** (retention + gunicorn) — `docs/malla-fix-plan-cnjmesh1.md`. Fixes the daily pain.
2. **cnjmesh1 reboot** (deliberate, watch recovery) — clears 9+ days of memory pressure, clean baseline.
3. **Full health sweep** (this checklist) — after reboot, confirm everything came back.
4. **cnjmesh1 OS/kernel update** — `docs/cnjmesh1-os-update-plan.md`, its own session, only after 1-3 stable.
5. **THEN finalize Tilly's fork on KPR1.**

---

## CHECKLIST — confirm each is 100% before Tilly

### Infrastructure — all 3 Pis
- [ ] **cnjmesh1** health — uptime, load, `free -h`, `df -h /` (should stay well under 100% now mqtt-filter is gone), no failed systemd units. Watch: memory pressure (it's the heavy box).
- [ ] **cnjmesh2** (Pi Zero 2 W, 512MB) health — load/RAM/disk. Runs the public malla2. Check Docker log rotation is holding (we set it Aug 1).
- [ ] **cnjmesh3** (Pi 3B, 1GB) health — load/RAM/disk. Hosts Observer + KPR2. Check if it has Docker log rotation (may NOT — same disk-fill risk we fixed on cnjmesh1).

### Meshtastic web tools (cnjmesh1)
- [ ] **Malla** (malla.cnjmesh.me, gated; malla2.cnjmesh.me, public/Pi-Zero) — after the retention+gunicorn fix, confirm fast + stable, not the "up and down." Test concurrent requests.
- [ ] **Meshview** (systemd: meshview-db + meshview-web, port 8080, `/home/somog/meshview/`) — confirm both services active + serving. (Was healthy Jul 31 — 302 local. Protected service, never remove.)

### APRS (cnjmesh1)
- [ ] **Graywolf APRS + Discord bridge** (`graywolf-discord.service` + watchdog timers) — active, posting. (aprs-monitor.service intentionally disabled — expected.)
- [ ] **aprs-tnc-web** (nextjs_app + mysql_database, port 8085) — UI reachable.

### LoRa APRS
- [ ] **K2GIA-10 iGate** (LilyGO T3, 10.0.0.74, CA2RXU firmware, 433.775) — node reachable, web UI up, hearing/gating traffic.
- [ ] **LoRa APRS → Discord bridge** (`/opt/lora-aprs-discord/`, UDP 1514) — running, listening, posting to Discord. KNOWN OPEN: end-to-end Discord posting never fully confirmed. Also open: K2GIA-10 doesn't self-gate its own TX (RX-only board planned — check richonguzman/LoRa_APRS_iGate firmware source first).

### MeshCore ecosystem
- [ ] **Observer** (cnjmesh3, `meshcore-packet-capture`, RAK4631 /dev/ttyACM0) — serial connected, capturing, publishing to its 4 brokers (letsmesh-us/eu, meshomatic, local 10.0.0.181).
- [ ] **KPR2 repeater** (cnjmesh3, `meshcore-mqtt-bridge`, Heltec V4 /dev/ttyACM1) — confirm BOTH MESHCORE + MQTT connected (contrast: KPR1 shows MQTT disconnected — see Tilly item).
- [ ] **KPR1 repeater** (cnjmesh1, `meshcore-mqtt-kpr1-bridge`, Heltec V3) — NOTE: this one IS the Tilly integration (points at mqtt.aws.tillyandthefish.com, currently MQTT-disconnected). Its health = the Tilly work itself, so it's the LAST thing, not a precondition.
- [ ] **Meshomatic** — confirm Observer's outbound bridge to us-east.meshomatic.net (correct host, NOT the us-east subdomain that times out) is connected + publishing. Coordinate w/ Tilly (Meshomatic admin) if needed.
- [ ] **CoreScope** (cnjmesh1, corescope.cnjmesh.me, port 3001) — was HEALTHY Aug 2 (200 in 0.7s, clean ingest). Reconfirm after reboot. Also the long-standing `local` MQTT-source instability (protocol-error disconnect loop) — verify current state.
- [ ] **MeshCore Hub** (cnjmesh1, `meshcore-hub` stack: api/web/collector/redis/mqtt/migrate) — all containers up + healthy; hub web reachable.

### NEW ISSUE flagged Aug 2 — needs diagnosis
- [ ] **MeshCore Discord new-node relay NOT working.** Service: `mesh-discord-shim` (cnjmesh1, port 8084, `/opt/stacks/mesh-discord-shim/`, `.env` has `NEW_NODE_WEBHOOK` -> MeshCore NJ Discord `#cnj-new-node-relay`). Was working when set up (session-log confirms ✅), so it REGRESSED — likely a casualty of the disk-100% period, or the webhook/config changed. Diagnose next session:
  1. `docker ps -a | grep mesh-discord-shim` — is it up?
  2. `docker logs --tail 40 mesh-discord-shim` — errors? posting attempts? webhook failures (401/404 = webhook deleted/changed in Discord)?
  3. Confirm the `NEW_NODE_WEBHOOK` in `/opt/stacks/mesh-discord-shim/.env` still matches a live Discord webhook (webhooks break if the channel/webhook was deleted or regenerated).
  4. Note it also handles `#centralnj-mc-channel-relay` and `#meshcore-nj-mqtt` — check if those still work (isolates whether it's the whole shim down vs just the new-node piece).
  Rebuild if needed: `cd /opt/stacks/mesh-discord-shim && sudo docker compose down && sudo docker compose up -d --build`.

---

## Only after ALL boxes above are checked:
- **Finalize Tilly's fork on KPR1** — `docs/` Tilly notes + the KPR1/Tilly-AWS-broker connectivity work. See the [ACTIVE] Tilly todo.
