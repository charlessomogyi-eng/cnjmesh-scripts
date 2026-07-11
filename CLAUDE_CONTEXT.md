# CLAUDE_CONTEXT.md — CNJ Mesh
**For AI assistants:** Fetch this file at the start of every session. It is the authoritative current-state summary of Charles's infrastructure. Do not ask him to re-explain anything documented here. Treat him as an experienced operator. Ask which todo item to start on and get to work.

Last updated: 2026-07-10

---

## Who You're Talking To
- **Charles Somogyi**, K2GIA — experienced operator, ~25 years IT/backup/recovery background (Dell Technologies SE)
- Based in Kendall Park / South Brunswick, NJ
- Built CNJ Mesh from scratch into a 300+ node Meshtastic network, later expanded to dual-protocol (Meshtastic + MeshCore)
- Not a software developer but highly technical — explain things plainly, don't over-explain basics he clearly already knows

---

## Infrastructure Quick Reference

### Hosts
| Host | Hardware | IP | User | Role |
|---|---|---|---|---|
| cnjmesh1 | Pi 4B Rev 1.5 | 10.0.0.181 | somog | Main hub — all primary services |
| cnjmesh2 | Pi Zero 2W | 10.0.0.91 | somogyic | Meshtastic gateway (CJG1) |
| cnjmesh3 | Pi 3B+, case installed | 10.0.0.133 | somog | Being set up — re-imaged July 10 with Pi OS 64-bit full. After boot run raspi-config → L5 Localisation → L4 WLAN Country → US → reboot. Then install Docker. |

### Services on cnjmesh1
- Mosquitto MQTT — `/opt/stacks/mqtt/`, config `/opt/stacks/mqtt/config/mosquitto.conf`
- Malla — port 5008 (**never remove**)
- Meshview — port 8080, pablorevilla fork at `~/meshview/` (**never remove**)
- Grafana — port 3000
- MeshMonitor — port 8081
- CoreScope — port 3001, public at `corescope.cnjmesh.me`
- MeshCore Hub — ports 8083/8000, public at `meshcorehub.cnjmesh.me`
- mesh-discord-shim — port 8084, `/opt/stacks/mesh-discord-shim/`, posts new-node welcomes to MeshCore NJ Discord
- meshing-around — `/opt/meshing-around/`, weather/EAS bot
- Graywolf APRS — K2GIA, iGate + WIDE1-1 digipeater, Digirig serial ID beb31e2f → `/dev/ttyUSB2`, port 8082
- mesh-mqtt-pg-collector, meshcore-packet-capture, meshcore-mqtt-bridge
- Cloudflare tunnel: `a05e5efa-8c67-48f8-a71c-833f5258dfce`, config `/etc/cloudflared/config.yml`

### Services on cnjmesh2
- Mosquitto MQTT — config at `~/meshtastic-mqtt/mosquitto/config/mosquitto.conf`
- OkToMqtt filter
- Always `cd ~/meshtastic-mqtt` before docker compose commands

### Nodes / Radio Hardware
| Node | Hardware | ID / Address | Notes |
|---|---|---|---|
| CJG1 | Heltec V4 | !0aca423c, 10.0.0.18 | Feeds cnjmesh2, TCP enabled |
| CJG2 | Heltec V3 | !9ea3e8d4, 10.0.0.234 | Feeds cnjmesh1, WiFi instability history |
| KPR1 | Heltec V3 MeshCore repeater | pubkey prefix 0a | /dev/ttyUSB1 on cnjmesh1 |
| KPR2 | Heltec V4 MeshCore repeater | pubkey prefix 97 | Upstairs Alfa antenna, 910.525/62.5/SF7/CR5/TX22 |
| Client 1 | Heltec V3 MeshCore companion | — | /dev/ttyUSB3, serial flapping, RAK replacement planned |
| Observer | WisMesh Pocket v2, RAK4631 | pubkey A8C40BF3, prefix A8 | /dev/ttyACM0, 910.525/BW62.5/SF7/CR5 |
| KPN2 | LilyGo T-Deck Plus | 10.0.0.140 | MAC 80:b5:4e:ce:c3:14 |
| KB2EAR-2 | Neighbor repeater | pubkey prefix 60 | 772m away, close neighbor |

### USB Device Map on cnjmesh1
| Device | What it is |
|---|---|
| /dev/ttyACM0 | Observer (WisMesh Pocket RAK4631) |
| /dev/ttyUSB1 | KPR1 (CP2102, serial 0001) |
| /dev/ttyUSB2 | Digirig (unique serial beb31e2f) — APRS PTT |
| /dev/ttyUSB3 | Client 1 (CP2102, serial 0001) |

After any USB changes always restart meshcore-packet-capture: `docker restart meshcore-packet-capture`

### MQTT Credentials
| Broker | Host | Credentials |
|---|---|---|
| Local (cnjmesh1) | localhost | meshdev / large4cats |
| CNJ Mesh public | mqtt.cnjmesh.me | meshuser / large4cats |
| SJMesh | mqtt.sjmesh.net:1883 | meshuser / mesh4life |
| MeshOmatic | us-east.meshomatic.net:31883 | user_somog / (in mosquitto.conf) |

### MeshCore Channel Keys
- Public: `8b3387e9c5cdea6ac9e5edbaa115cd72`
- CentralNJ-MC: `dcc94b369feeee309800ee15a12403ed`

### Key Config Notes
- **Graywolf PTT:** `/dev/ttyUSB2`, `serial_rts`, stored in `/var/lib/graywolf/graywolf.db` table `ptt_configs` column `device`
- **Graywolf watchdog DISABLED** — was restarting every 5 min breaking PTT. Files at `/etc/systemd/system/graywolf-watchdog.timer/.service`. Do NOT re-enable without PTT verification.
- **POLLERR errors are cosmetic** — APRS works through them, not a failure indicator
- meshcore-packet-capture TOML configs live INSIDE container (fragile — bind-mount pending, todo item #4)
- **Code edits:** always use Python script approach (`cat > /tmp/fix.py`), never sed for complex edits
- **MeshOmatic** — their MQTT broker goes down periodically (AkkerKid runs 9 servers on one UPS). Not a CNJ Mesh problem. Bridge reconnects automatically when they come back.

---

## What Was Fixed — July 9, 2026
- Powered USB hub installed — all 4 devices on hub. Digirig serial unique ID `beb31e2f` → `/dev/ttyUSB2`
- Graywolf PTT fixed: corrected device path via sqlite3
- Graywolf watchdog disabled (was breaking PTT every 5 min)
- APRSThursday check-in confirmed working end-to-end RF→Discord
- Weather alerts fixed: `EnvironmentFile` was missing from `weather-bot-alerts.service` (silent crash). Zone corrected `NJZ107→NJZ012` (Middlesex County). `Persistent=true` added to timer. All 4 Discord webhooks now receiving alerts.
- CLAUDE_CONTEXT.md created and pushed to GitHub
- All changes committed to GitHub

## What Was Done — July 10, 2026
- meshcore-packet-capture restarted after USB hub change — Observer reconnected ✅
- MeshOmatic confirmed down on their end (AkkerKid server outage) — not our problem
- MeshOmatic MQTT broker still not passing traffic even after website came back up
- NWS alerts confirmed running correctly — no active alerts today to test MeshCore NJ Discord posting
- Weather bot was NOT running July 9 during flooding — fixed before next event
- cnjmesh1-operations.md DR runbook written and pushed to GitHub ✅
- cnjmesh3 case (Geekworm P252) installed
- cnjmesh3 WiFi never worked — root cause: WiFi country code never set, wlan0 interface completely disabled
- Re-imaged cnjmesh3 with Raspberry Pi OS 64-bit (full, not Lite) — still in progress at session end
- **CRITICAL for next session:** After cnjmesh3 boots, immediately run `sudo raspi-config` → Localisation Options → WLAN Country → US → finish → `sudo reboot`. Then install Docker.

---

## Todo List (Priority Order) — Last updated 2026-07-10

### Quick Wins
1. ~~Commit cnjmesh1-operations.md runbook to GitHub~~ ✅ DONE
2. Complete cnjmesh3 setup — set WiFi country, confirm SSH, install Docker
3. NWS alerts not posting to MeshCore NJ Discord — verify on next real alert
4. Bind-mount packet-capture `config.d` to host
5. Rotate Discord webhook URL (accidentally posted in chat)
6. Rotate MeshOmatic password (exposed in mosquitto.conf paste)
7. Public-chat-relay (one webhook + one `.env` line away)
8. NWS Middlesex County focused forecasts for north/south channels
9. Add meshcore-packet-capture health check / auto-restart on Observer disconnect

### Back Burner — Verify Before Touching
- Remove dead MeshOmatic section from `mosquitto.conf` (`us-east.meshomatic.net:31883`) — MeshOmatic goes down periodically, may not actually be dead
- Remove dead `meshshadow` section from cloudflared config — verify first

### Medium Projects
10. y0gurt MQTT feed — accept his offer, add observer to hub
11. Node tagging in hub (KPR1, KPR2, Observer)
12. KPR1 retirement decision (path-byte data accumulating)
13. Discord server security review
14. APRS Discord silent-alert monitor (no posts in X hours → alert)
15. T096 + Alfa mobile setup (needs SMA→RP-SMA adapter)
16. LoRa APRS 433MHz node arriving July 14: configure 433.775/62.5kHz

### Longer Projects
17. cnjmesh3 becomes upstairs RF hub — Observer + KPR2 + LoRa APRS node co-located at elevation, feeding data back to cnjmesh1 over WiFi
18. Client 1 replacement with RAK/WisMesh
19. Cross-mesh bridge via mesh-api (after Client 1 replaced) — MeshCore Public → private Meshtastic channel
20. MeshOmatic relay script
21. KPR2 watchdog (adverts as heartbeats)
22. Recruit distributed observers across Central NJ to feed meshcorehub.cnjmesh.me

---

## GitHub Repo
`github.com/charlessomogyi-eng/cnjmesh-scripts`
Cloned on cnjmesh1 at `~/cnjmesh-scripts`

## How to Start Each Claude Session
Say **"read my GitHub context file"** and Claude will run:
```
curl -s https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/CLAUDE_CONTEXT.md
```
No re-explaining needed.
