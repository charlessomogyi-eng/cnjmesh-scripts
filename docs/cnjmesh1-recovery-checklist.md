# cnjmesh1 Recovery Checklist

Run through this once the new board is booted with the original SD card
and network-reachable. Check items off in order — later steps assume
earlier ones are confirmed working.

## 1. Basic access
- [ ] SSH in: `ssh somog@10.0.0.181`
- [ ] `df -h /` — confirm disk usage, note starting percentage
- [ ] `docker ps -a` — see what came up vs. what's stopped/restarting

## 2. Core broker
- [ ] Mosquitto container running
- [ ] `mosquitto_sub -h localhost -p 1883 -t '#' -v -C 5` — confirm real traffic flowing
- [ ] SJMesh bridge restored — check `/opt/stacks/mqtt/config/mosquitto.conf`
      for the `sjmesh-bridge` block (backup at `docs/sjmesh-bridge-backup.md`
      in this repo — paste back in if missing)
- [ ] `docker compose restart` in `/opt/stacks/mqtt/` if the bridge was re-added

## 3. CoreScope (needs manual config fix — NOT backed up, was lost with the old board)
- [ ] CoreScope container running
- [ ] Re-apply the `local` MQTT source fix in
      `/home/somog/meshcore-data/config.json`:
      broker `mqtt://172.17.0.1:1883`, username `meshdev`, password `large4cats`
      (confirm gateway IP is still `172.17.0.1` via
      `docker exec corescope ip route | grep default` first — don't assume)
- [ ] `docker restart corescope`
- [ ] `docker logs corescope --tail 100 2>&1 | grep -i "local"` — confirm it
      connects to the REAL broker, not its own internal one
- [ ] Visit `corescope.cnjmesh.me` in a browser — confirm Transmissions/Nodes/
      Last-24h counts are climbing, not stuck at 0

## 4. Other web services
- [ ] `malla.cnjmesh.me` loads
- [ ] `meshview.cnjmesh.me` loads
- [ ] `meshcorehub.cnjmesh.me` loads (3 containers: collector, web, api —
      confirm all 3 in `docker ps`)
- [ ] UptimeRobot dashboard — confirm malla/meshview monitors flip to green

## 5. Discord relays
- [ ] mesh-discord-shim container running
- [ ] Post a test message somewhere it relays from, confirm it lands in Discord
- [ ] corescope-watchdog running — `state.json` will regenerate fresh, that's fine
- [ ] graywolf-discord-bridge watchdog running
- [ ] graywolf.service watchdog running (alert-only, confirm NOT auto-restarting)
- [ ] aprs_monitor.py running

## 6. Graywolf APRS (2m)
- [ ] Digirig connected, `/dev/ttyUSB2` present
- [ ] Graywolf iGate + digipeater actually transmitting/receiving
- [ ] Confirm PTT working (careful — do NOT re-enable the old graywolf watchdog
      that was disabled for breaking PTT)

## 7. LoRa APRS (70cm, K2GIA-10)
- [ ] K2GIA-10 web UI reachable at `10.0.0.74`
- [ ] `lora-aprs-discord-bridge-v2.py` running, listening on UDP 1514
- [ ] Send a test message via aprs-tnc-web, confirm it lands in both Discord
      channels (`lora-aprs-70cm` in Meshtastic Discord + MeshCore-NJ Discord)

## 8. Weather bots
- [ ] weather-bot timer active, posting PWS conditions
- [ ] nj_regional_weather timer active

## 9. New monitoring (deploy fresh, same as cnjmesh2/cnjmesh3)
- [ ] disk-temp-watchdog installed, `NODE_LABEL=Node 1`
- [ ] peer-check installed, `PEERS=Node 2:10.0.0.91,Node 3:10.0.0.186`,
      `SERVICES=Node 2:malla2.cnjmesh.me;Node 3:Not reporting into MeshOmatic,Not reporting into LetsMesh,corescope.cnjmesh.me: your own Observer/KPR2 data stops updating (community data from others continues)`,
      `CROSS_POST_LABELS=Node 2` (Node 3/MeshCore-only doesn't cross-post)
- [ ] Confirm both timers scheduled via `systemctl list-timers`
- [ ] Confirm cnjmesh2 and cnjmesh3's peer-check fired "back ONLINE" alerts
      with the restored-services list, in both #cnjmesh and the Meshtastic
      Discord channel

## 10. Cleanup / housekeeping
- [ ] KPR1 — do NOT reconnect (retired). Mark ARCHIVED in `whorepeated`,
      mark retired in CoreScope/MeshCore Hub node lists if applicable
- [ ] Run a fresh `cnjmesh1-backup.sh` to establish a new clean backup point
- [ ] Note: MQTT credential rotation (`meshuser`/`meshdev`) is still overdue
      from before the outage — consider doing it now while everything's
      already being touched
