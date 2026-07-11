# CLAUDE_CONTEXT.md — CNJ Mesh
**For AI assistants:** Fetch this file at the start of every session. It is the authoritative current-state summary of Charles's infrastructure. Do not ask him to re-explain anything documented here. Treat him as an experienced operator. Ask which todo item to start on and get to work.

Last updated: 2026-07-11

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
| cnjmesh3 | Pi 3B+, case installed | 10.0.0.133 | somog | Awaiting replacement Pi — original unit faulty (kernel panic/boot loop). SD card re-imaged with Pi OS 64-bit full is ready. After boot: immediately run `sudo raspi-config` → Localisation Options → WLAN Country → US → reboot. Then install Docker. |

### Services on cnjmesh1
- Mosquitto MQTT — `/opt/stacks/mqtt/`, config `/opt/stacks/mqtt/config/mosquitto.conf`
- Malla — port 5008 (**never remove**)
- Meshview — port 8080, pablorevilla fork at `~/meshview/` (**never remove**)
- Grafana — port 3000
- MeshMonitor — port 8081
- CoreScope — port 3001, public at `corescope.cnjmesh.me`
- MeshCore Hub — ports 8083/8000, public at `meshcorehub.cnjmesh.me`
- mesh-discord-shim — port 8084, `/opt/stacks/mesh-discord-shim/`, posts new-node welcomes and CentralNJ-MC messages to MeshCore NJ Discord. Uses docker-compose. Rebuild with `cd /opt/stacks/mesh-discord-shim && sudo docker compose down && sudo docker compose up -d --build`
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

### meshcore-packet-capture
- Container recreate command:
```
docker run -d \
  --name meshcore-packet-capture \
  --restart unless-stopped \
  --privileged \
  --group-add dialout \
  --device /dev/ttyACM0:/dev/ttyACM0 \
  -v /opt/meshcore-packet-capture/config.d:/etc/meshcore-packet-capture/config.d \
  ghcr.io/agessaman/meshcore-packet-capture:latest
```
- Config files now bind-mounted to host at `/opt/meshcore-packet-capture/config.d/`

### mesh-discord-shim
- Location: `/opt/stacks/mesh-discord-shim/`
- Env file: `/opt/stacks/mesh-discord-shim/.env`
- Webhooks:
  - `NEW_NODE_WEBHOOK` → MeshCore NJ Discord `#cnj-new-node-relay`
  - `PUBLIC_CHAT_WEBHOOK` → MeshCore NJ Discord `#centralnj-mc-channel-relay`
- Posts new node alerts and CentralNJ-MC channel messages to Discord
- Deduplicates by packet_hash to prevent duplicate posts
- Only posts CentralNJ-MC channel messages — Public channel intentionally excluded (community voted against it)
- Discord category: `mesh-to-discord-relays-no-public`

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
- **Code edits:** always use Python script approach (`cat > /tmp/fix.py`), never sed for complex edits
- **MeshOmatic** — their MQTT broker goes down periodically (AkkerKid runs 9 servers on one UPS). Not a CNJ Mesh problem. Bridge reconnects automatically when they come back.

---

## What Was Done — July 11, 2026
- meshcore-packet-capture bind-mount completed ✅ — config files now on host at `/opt/meshcore-packet-capture/config.d/`
- mesh-discord-shim updated:
  - NEW_NODE_WEBHOOK → `#cnj-new-node-relay` (renamed from old #new-node-relay)
  - PUBLIC_CHAT_WEBHOOK → `#centralnj-mc-channel-relay` (new channel)
  - Added CentralNJ-MC channel filter — only posts CentralNJ-MC messages, not Public channel
  - Added packet_hash deduplication — prevents 3x posts from multi-path reception
  - Discord category `mesh-to-discord-relays-no-public` created
- cnjmesh3 original Pi unit faulty — returning to vendor, replacement Pi 3B+ needed

---

## Todo List (Priority Order) — Last updated 2026-07-11

### Quick Wins
1. Verify #cnj-new-node-relay posts when next new node appears
2. NWS alerts for MeshCore NJ Discord — verify on next real alert
3. NWS Middlesex County focused forecasts for north/south channels
4. Add meshcore-packet-capture health check / auto-restart on Observer disconnect

### Back Burner — Verify Before Touching
- Remove dead MeshOmatic section from `mosquitto.conf` — MeshOmatic goes down periodically, may not actually be dead
- Remove dead `meshshadow` section from cloudflared config — verify first
- Rotate Discord webhook URLs — low priority for hobby project
- Rotate MeshOmatic password — low priority

### Medium Projects
5. y0gurt MQTT feed — accept his offer, add observer to hub
6. Node tagging in hub (KPR1, KPR2, Observer)
7. KPR1 retirement decision (path-byte data accumulating)
8. Discord server security review
9. APRS Discord silent-alert monitor (no posts in X hours → alert)
10. T096 + Alfa mobile setup (needs SMA→RP-SMA adapter)
11. LoRa APRS 433MHz node arriving July 14: configure 433.775/62.5kHz

### Longer Projects
12. cnjmesh3 full setup — awaiting replacement Pi 3B+ (vendor refund in progress, reorder from Amazon)
13. cnjmesh3 becomes upstairs RF hub — Observer + KPR2 + LoRa APRS node co-located at elevation
14. Client 1 replacement with RAK/WisMesh
15. Cross-mesh bridge via mesh-api (after Client 1 replaced)
16. MeshOmatic relay script
17. KPR2 watchdog (adverts as heartbeats)
18. Recruit distributed observers across Central NJ to feed meshcorehub.cnjmesh.me

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
