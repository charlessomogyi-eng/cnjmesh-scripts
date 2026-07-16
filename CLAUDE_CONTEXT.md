# CLAUDE_CONTEXT.md — CNJ Mesh
**For AI assistants:** Fetch this file at the start of every session. It is the authoritative current-state summary of Charles's infrastructure. Do not ask him to re-explain anything documented here. Treat him as an experienced operator. When presenting the todo list, always show ALL items including medium and longer projects — never summarize or truncate. Ask which todo item to start on and get to work.

Last updated: 2026-07-12

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
| cnjmesh3 | Pi 3B+, case installed | 10.0.0.133 | somog | Awaiting replacement Pi — original unit faulty. SD card re-imaged with Pi OS 64-bit full is ready. After boot: immediately run `sudo raspi-config` → Localisation Options → WLAN Country → US → reboot. Then install Docker. |

### Services on cnjmesh1
- Mosquitto MQTT — `/opt/stacks/mqtt/`, config `/opt/stacks/mqtt/config/mosquitto.conf`
- Malla — port 5008 (**never remove**)
- Meshview — port 8080, pablorevilla fork at `~/meshview/` (**never remove**)
- Grafana — port 3000
- MeshMonitor — port 8081
- CoreScope — port 3001, public at `corescope.cnjmesh.me`
- MeshCore Hub — ports 8083/8000, public at `meshcorehub.cnjmesh.me`, config at `/opt/stacks/meshcore-hub/`
- mesh-discord-shim — port 8084, `/opt/stacks/mesh-discord-shim/`, docker-compose based. Rebuild: `cd /opt/stacks/mesh-discord-shim && sudo docker compose down && sudo docker compose up -d --build`
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
- Config files bind-mounted to host at `/opt/meshcore-packet-capture/config.d/`
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

### mesh-discord-shim
- Location: `/opt/stacks/mesh-discord-shim/`
- Env file: `/opt/stacks/mesh-discord-shim/.env`
- Webhooks:
  - `NEW_NODE_WEBHOOK` → MeshCore NJ Discord `#cnj-new-node-relay`
  - `PUBLIC_CHAT_WEBHOOK` → MeshCore NJ Discord `#centralnj-mc-channel-relay`
  - `NJ_MQTT_WEBHOOK` → MeshCore NJ Discord `#meshcore-nj-mqtt`
- Channel filtering: only CentralNJ-MC and meshcore-nj-mqtt messages posted — Public channel intentionally excluded
- Deduplicates by packet_hash to prevent duplicate posts
- Discord category: `mesh-to-discord-relays-no-public`

### MeshCore Hub Channels
- Public — key: `8b3387e9c5cdea6ac9e5edbaa115cd72`
- CentralNJ-MC — key: `dcc94b369feeee309800ee15a12403ed`
- meshcore-nj-mqtt — key: `90746153489710a870d23abb50cc9e42` ← new statewide NJ community channel

### MQTT Credentials
| Broker | Host | Credentials |
|---|---|---|
| Local (cnjmesh1) | localhost | meshdev / large4cats |
| CNJ Mesh public | mqtt.cnjmesh.me | meshuser / large4cats |
| SJMesh | mqtt.sjmesh.net:1883 | meshuser / mesh4life |
| MeshOmatic | us-east.meshomatic.net:31883 | user_somog / (in mosquitto.conf) |

### MQTT Public Access — IMPLEMENTED: Cloudflare Tunnel WSS ✅
**Completed 2026-07-12.** Public MQTT access on `mqtt.cnjmesh.me` uses **Cloudflare Tunnel with WebSocket Secure (WSS) over port 443** — no port forwarding, no public A record.

**What was configured:**
- DNS: CNAME `mqtt` → `a05e5efa-8c67-48f8-a71c-833f5258dfce.cfargotunnel.com` (Proxied), added via Cloudflare dashboard
- Ingress rule added to `/etc/cloudflared/config.yml`: `mqtt.cnjmesh.me` → `http://localhost:9001` (before the `http_status:404` catch-all)
- `cloudflared` restarted, confirmed active/running with registered tunnel connections
- Mosquitto's existing WebSocket listener on port 9001 (already present in `mosquitto.conf`, `allow_anonymous false` + password file) handles the traffic — no Mosquitto config changes were needed

**Verification performed:**
- Local WS test on cnjmesh1: `python3` + `paho-mqtt` (transport="websockets") connecting to `localhost:9001` → Success
- Public WSS test from cnjmesh1: same script pointed at `mqtt.cnjmesh.me:443` with `tls_set()` → Success (after fixing a `/etc/hosts` gotcha below)
- Phone test over cellular (WiFi off) using MyMQTT app to `mqtt.cnjmesh.me:443` — reached the server (got a PUBACK decode error, which is expected: MyMQTT doesn't support MQTT-over-WebSocket transport, so it can't complete the handshake — this was a client limitation, not a server problem)

**⚠️ `/etc/hosts` gotcha (fixed):** `/etc/hosts` on cnjmesh1 had a stale entry `172.18.0.2 mosquitto mosquitto.cnjmesh.me f7ae1469a8af mqtt.cnjmesh.me` — an old Docker-internal override that hijacked IPv4 resolution of `mqtt.cnjmesh.me` to a container-internal address (172.18.0.2, not a real Cloudflare IP), causing "connection refused" when testing from cnjmesh1's own shell. IPv6 resolution was unaffected and worked correctly the whole time via real DNS — this was not a general IPv6 problem, just an IPv4-only stale override. Fixed by removing `mqtt.cnjmesh.me` from that line (kept `mosquitto`/`mosquitto.cnjmesh.me` for internal container use). Note: `/etc/hosts` has the immutable attribute set (`chattr +i`, likely due to cloud-init's `manage_etc_hosts`) — future edits need `sudo chattr -i /etc/hosts` first, then `chattr +i` again after editing.

**Still to do:** rotate `meshuser`/`large4cats` (and/or `meshdev`/`large4cats`) credentials before/soon after this is announced publicly, since the broker is now internet-reachable.




- **Graywolf PTT:** `/dev/ttyUSB2`, `serial_rts`, stored in `/var/lib/graywolf/graywolf.db` table `ptt_configs` column `device`
- **Graywolf watchdog DISABLED** — was restarting every 5 min breaking PTT. Do NOT re-enable.
- **POLLERR errors are cosmetic** — APRS works through them
- **Code edits:** always use Python script approach (`cat > /tmp/fix.py`), never sed for complex edits
- **MeshOmatic** — their MQTT broker goes down periodically. Not a CNJ Mesh problem.

---

## What Was Done — July 11-12, 2026
- meshcore-packet-capture bind-mount completed ✅
- mesh-discord-shim updated — #cnj-new-node-relay and #centralnj-mc-channel-relay working ✅
- Fixed event type mismatch (`channel_message` vs `channel_msg_recv`) ✅
- Fixed duplicate message posting via packet_hash deduplication ✅
- Created `meshcore-nj-mqtt` channel — statewide NJ community channel for RF + MQTT users ✅
- Registered `meshcore-nj-mqtt` on MeshCore Hub ✅
- Added `#meshcore-nj-mqtt` Discord relay to mesh-discord-shim ✅
- Discord category `mesh-to-discord-relays-no-public` created ✅
- cnjmesh3 original Pi unit faulty — returning to vendor, replacement Pi 3B+ needed

## What Was Done — July 12, 2026 (later session)
- **SSH key auth set up for GitHub on cnjmesh1** ✅ — generated `~/.ssh/id_ed25519_github`, added to GitHub account, configured `~/.ssh/config`, switched `~/cnjmesh-scripts` remote from HTTPS to SSH. Token-free push/pull confirmed working end-to-end.
- **cnjmesh1 backup script created and tested** ✅ — `scripts/cnjmesh1-backup.sh`. Backs up `/opt/stacks/`, meshing-around, graywolf-discord, cloudflared config, graywolf.db, mesh-discord-shim seen_nodes.db, and a full `pg_dumpall` of the mesh-mqtt-pg-collector Postgres DB (container: `mesh-mqtt-pg-collector-postgres-1`, user/db: `meshtastic`). Fixed initial failure — script now reads `POSTGRES_USER`/`POSTGRES_PASSWORD` from the container's own env instead of assuming defaults. Verified dump output is non-empty (238k+ lines).
- **Backup runbook documented** ✅ — `docs/backup-runbook.md`. Covers what's backed up, what's not (SD card image, unmounted Docker volumes), when to run it (ad hoc, before risky changes), and manual restore steps.
- **PowerShell pull script created and tested** ✅ — `scripts/pull-cnjmesh1-backup.ps1`. Runs on Charles's laptop, finds latest backup via SSH, skips if already downloaded, pulls via `scp` into `OneDrive\Documents\cnjmesh-backups\` for automatic OneDrive sync. Confirmed working via right-click "Run with PowerShell" (direct `.\script.ps1` invocation blocked by an execution policy above CurrentUser scope, likely machine/Group Policy — not resolved, but right-click method works fine so not pursued further).
- **Note:** a GitHub PAT was pasted into chat during this session and used for a couple of pushes before SSH was fully working. It's still valid (Charles's policy: 90-day PATs are fine to let expire naturally) but should be considered exposed since it appeared in chat text.
- **Open item:** an uploaded status doc ("Part 96", from a prior chat) contained additional details not yet reconciled into this file — notably that Charles's session that day confirmed **Cloudflare Tunnel WSS** (not port-forwarding + DNS A record) as the plan for public MQTT access on `mqtt.cnjmesh.me`. This file's MQTT section below still describes the port-forward approach and needs updating. Also unreconciled: fuller KPR1 pubkey (`0acd65fb`), Digirig audio bus ID, community contact notes (Tilly, y0gurt, ozneteast, Tck, KB2EAR, OC, Compy), and GitHub repos found (MeshCoreDiscordBridge, agessaman MQTT firmware fork, mesh-api, docker-mqtt-mosquitto-cloudflare-tunnel).

## What Was Done — July 13, 2026 (CJG1/CJG2 firmware + flapping investigation)
- **CJG1 and CJG2 firmware upgraded via serial/USB** ✅ — done specifically to rule out old firmware as the cause of long-standing (months-old) intermittent WiFi flapping on these two Meshtastic gateway nodes. CJG1: `2.7.18.fb3bf78` → `2.7.24.472b14c`. CJG2: `2.7.15.567b8ea` → `2.7.24.472b14c`. **Firmware upgrade alone did NOT fix the flapping** — CJG1 flapped again after upgrade, confirming old firmware was not the (sole) cause.
- **DHCP reservations on the Xfinity gateway (10.0.0.1) were found missing for both nodes** despite Charles being fairly confident they were previously set — both showed as plain DHCP instead of Reserved IP. Re-added: `esp32s3-A3E8D4` (CJG2) → `10.0.0.234`, `esp32s3-CA423C` (CJG1) → `10.0.0.18`, both with comments set to their gateway names. Cause unconfirmed — possibly a router firmware update or reset event; both being missing simultaneously suggests a systemic event rather than two independent coincidences. Confirmed still holding as of later in the session.
- **Ruled out via investigation:** band steering (Split Bands is ON — `C4Somogyi-24` 2.4GHz and `C4Somogyi` 5GHz are genuinely separate SSIDs, not steered), MAC filtering (set to Allow-All), physical distance/signal (nodes are ~20 ft from router), USB/serial contention (both nodes were fully disconnected from laptop after flashing, flapping still occurred later).
- **Found and changed:** 2.4GHz WiFi Mode was set to `802.11 g/n/ax`. ESP32 (the chip in all Heltec boards, including CJG1/CJG2) has no 802.11ax support at all — mixed-mode APs including ax alongside older standards are a known source of intermittent-connect issues for legacy/simple WiFi chipsets. **Changed Mode to `802.11 g/n` only** (ax removed) as a single-variable test — saved and applied. Channel Selection was left on **Automatic** (not yet changed) so that if flapping stops, we know it was the Mode change specifically and not a combination of changes. Channel Bandwidth was already conservatively set to 20 (not 20/40) — left as is.
- **Confirmed unaffected by the Mode change:** the Pi 4B (cnjmesh1) and Pi Zero 2W (cnjmesh2) — neither supports 802.11ax regardless of band, so removing ax from the 2.4GHz mode list doesn't change how they connect. 5GHz devices (gaming consoles, TVs, etc. on `C4Somogyi`) are on a completely separate SSID/edit page, unaffected by this 2.4GHz-only change.
- **Xfinity gateway admin portal (10.0.0.1) notes for future reference:** contrary to widespread Xfinity forum reports that these settings are locked/greyed-out on modern gateways, **this particular gateway's `Gateway > Connection > Wi-Fi > Edit 2.4GHz` (and presumably Edit 5GHz) page DOES expose Mode, Channel Selection/Channel, Channel Bandwidth, and Security Mode as editable fields** — worth checking here directly rather than assuming they're locked based on general community reports.
- **Next step / open experiment:** monitor CJG1 and CJG2 over the next several days to see if the Mode change (ax removed) resolves the flapping. If flapping continues, the next single-variable test would be switching Channel Selection from Automatic to Manual (fixed channel — 1, 6, or 11) to rule out the router silently switching channels mid-connection as the cause. If neither router-side change resolves it, next escalation is a dedicated separate access point behind the Xfinity gateway, since Xfinity's automatic WiFi management is known to override/limit customer control in ways that can be difficult to fully diagnose from this admin portal alone.

### UPDATE — same day, ~2:25 PM: Live test results after Mode change
- **CJG2 (Heltec V3, 10.0.0.234) stabilized** — took about 5 minutes to settle after the Mode change/radio restart, then connected cleanly and stayed connected. No flapping observed since.
- **CJG1 (Heltec V4, 10.0.0.18) is still actively flapping** — directly observed cycling between "Not connected" and briefly-connected in the Meshtastic app in real time, confirmed via screenshots. This is a live, ongoing, rapid cycle — not just slow-to-settle like CJG2 was.
- **⚠️ CORRECTION to prior documentation:** earlier notes (and Charles's own recollection) had assumed CJG2 (the Heltec V3) was the historically flaky node. Based on today's direct observation, **it is CJG1 (the newer Heltec V4) that is currently flapping**, while CJG2 (V3) is now stable. This may mean: (a) CJG2's prior instability was genuinely fixed by today's firmware upgrade and/or Mode change, and CJG1 has a separate, previously-overshadowed or newer issue; (b) the two nodes are physically positioned differently in ways that matter (obstruction, power supply quality) independent of hardware generation; or (c) a V4-specific WiFi driver/hardware quirk not previously distinguished from V3 in past notes. Not yet determined which.
- **Mode change (ax removal) is confirmed NOT sufficient on its own to fix CJG1** — it fixed (or coincided with fixing) CJG2, but CJG1's flapping continued well after the change had time to settle.
- **Next steps for CJG1 specifically:** (1) check physical power supply quality/cable — brief brownouts can mimic this exact rapid connect/disconnect pattern; (2) check physical position/obstruction relative to router, even if raw distance is similar to CJG2's; (3) proceed with the already-planned Manual Channel Selection test (fixed channel 1/6/11) on the router, since Mode alone didn't resolve it.

**Power supply detail:** all nodes (CJG1, CJG2, and others) use SinitoAula 5V/1A (5W) USB wall adapters + etguuds braided USB-A→USB-C cables, both bought as multi-packs. Since CJG2 (now stable) is very likely on the same adapter/cable model as CJG1 (flapping), a model-wide power issue seems less likely — but an individual defective unit from the multi-pack (bad solder joint, worn connector, etc.) is still plausible and not yet ruled out. **Planned test (not yet done as of this session):** physically swap CJG1's specific adapter/cable with a different individual unit — ideally CJG2's — and observe whether flapping follows the node or stays with the original power hardware. If CJG1 stabilizes on different physical hardware, that confirms a bad individual unit. If it still flaps, power is likely not the cause and the Manual Channel Selection test is the next step.


- **Claude Code installed on cnjmesh1** ✅ — via npm (`npm install -g @anthropic-ai/claude-code`), v2.1.207, Node v24.14.0. Authenticated via OAuth to charles.somogyi@gmail.com (Claude Pro). Runs from `~/cnjmesh-scripts`, working folder trusted.
- **Public MQTT over Cloudflare Tunnel WSS — fully implemented and verified** ✅ — see "MQTT Public Access" section above for full detail. DNS CNAME added manually via Cloudflare dashboard (Charles's preference — avoids CLI Cloudflare auth), ingress rule added to cloudflared config.yml via direct bash/Python edit (not Claude Code — Charles opted for direct SSH commands for this one), cloudflared restarted cleanly. Verified working via local WS test, public WSS test, and phone-over-cellular test.
- **Found and fixed a stale `/etc/hosts` override** ✅ — was hijacking `mqtt.cnjmesh.me` IPv4 resolution to a stale Docker-internal IP, causing false "connection refused" when testing from cnjmesh1's own shell. Not a real IPv6 or DNS problem — see detail above. `/etc/hosts` has immutable attribute (`chattr +i`) due to cloud-init; remember to toggle it off/on around any future manual edits.
- **paho-mqtt installed** on cnjmesh1 (`pip install paho-mqtt --break-system-packages`) — useful for future MQTT testing/scripting since the packaged `mosquitto_sub` (v2.0.21) lacks WebSocket transport support.



### Quick Wins
1. **Explore LetsMesh.net integration** — see `docs/letsmesh-and-ozneteast-notes.md` for full research and starting point. Decided 2026-07-12 to pursue this path over (or alongside) the custom mqtt.cnjmesh.me broker for reaching other regional operators.
2. **CJG1 (Heltec V4) is still actively flapping** after the 2.4GHz Mode change (ax removed) — CJG2 (V3) stabilized from the same change, but CJG1 did not. Next test: check CJG1's power supply/cable and physical position, then try switching router Channel Selection from Automatic to Manual (fixed channel 1/6/11) if those don't explain it. See "UPDATE — same day, ~2:25 PM" under the July 13 investigation section above for full detail — note this corrects earlier assumption that CJG2/V3 was the flaky one; it's actually CJG1/V4.
3. Invite NJ MeshCore operators to join meshcore-nj-mqtt channel (share QR from meshcorehub.cnjmesh.me/channels)
4. Get Tilly and y0gurt to point their observers at mqtt.cnjmesh.me — or, per LetsMesh pivot, help them set up as LetsMesh observers with correct NJ IATA code instead
5. NWS alerts for MeshCore NJ Discord — verify on next real alert
6. NWS Middlesex focused forecasts for north/south channels
7. Add meshcore-packet-capture health check / auto-restart on Observer disconnect
8. Rotate the GitHub PAT that was pasted into chat this session (still valid, but exposed)
9. Reconcile remaining "Part 96" status doc details into this file — community contact notes and GitHub repos found (MeshCoreDiscordBridge, agessaman MQTT firmware fork, mesh-api)
10. Rotate meshuser/large4cats (and/or meshdev/large4cats) MQTT credentials now that mqtt.cnjmesh.me is publicly reachable over WSS

### Back Burner
- Remove dead MeshOmatic section from mosquitto.conf — verify first
- Remove dead meshshadow section from cloudflared config — verify first
- Rotate Discord webhook URLs — low priority
- Rotate MeshOmatic password — low priority

### Medium Projects
11. Node tagging in hub (KPR1, KPR2, Observer)
12. KPR1 retirement decision
13. Discord server security review
14. APRS Discord silent-alert monitor
15. T096 + Alfa mobile setup (needs SMA→RP-SMA adapter)
16. LoRa APRS 433MHz arriving July 14 — configure 433.775/62.5kHz
17. Broker-to-broker bridging with LV Mesh / SJ Mesh for meshcore-nj-mqtt
~~18. Upgrade Meshtastic gateway nodes CJG1 and CJG2 firmware~~ — **DONE 2026-07-13**, both upgraded to `2.7.24.472b14c` via serial. Did not resolve flapping on its own — see todo #2 above for the follow-up WiFi Mode investigation, which is the current active thread on this issue.

### Longer Projects
18. cnjmesh3 full setup — awaiting replacement Pi 3B+
19. cnjmesh3 becomes upstairs RF hub — Observer + KPR2 + LoRa APRS node
20. Client 1 replacement with RAK/WisMesh
21. Cross-mesh bridge via mesh-api
22. MeshOmatic relay script
23. KPR2 watchdog

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

## How to End Each Claude Session
At the end of every session, Claude must:
1. Update the todo list in this file with completed items and any new items
2. Update the "What Was Done" section with changes made this session
3. Push the updated file to GitHub using the token Charles provides
4. Remind Charles to provide his GitHub token if not already given

---

## LoRa APRS / K2GIA-10 — Session July 14-15, 2026

### Infrastructure
- **K2GIA-10**: LilyGO T3 LoRa32 V1.6.1, reserved IP `10.0.0.74`, firmware CA2RXU_LoRa_iGate v3.2.4. Web UI at `http://10.0.0.74`, login `admin` / blank password (still needs a real password set).
- **aprs-tnc-web**: browser-based APRS messaging UI, deployed at `/opt/aprs-tnc-web` on cnjmesh1, port 8085. Built as a **local arm64 image** (`aprs-tnc-web-local:latest`) — the upstream `ghcr.io/sq2cpa/aprs-tnc-web` image is amd64-only and fails on the Pi's arm64 with `exec format error`. To rebuild: `cd /opt/aprs-tnc-web/repo && docker build -t aprs-tnc-web-local:latest .`, then `docker-compose.yaml` image line already points at the local tag.
- **lora-aprs-discord bridge**: `/opt/lora-aprs-discord/`. `.env` holds `DISCORD_WEBHOOK_LORA`, `DISCORD_WEBHOOK_LORA_MESHCORE` (both post to `lora-aprs-70cm` channel in the Central/South NJ Meshtastic Discord and the MeshCore-NJ Discord respectively), `SYSLOG_PORT=1514`.

### KEY ARCHITECTURE FINDING — read before doing more KISS work
K2GIA-10's KISS TCP server (port 8001) is **TX-injection only**. It accepts frames from a connected KISS client and transmits them over LoRa, but it does **not** echo transmitted or received frames back to any connected client — confirmed via a raw unfiltered 60-second socket sniff during an active message send (zero frames received). The "Accept own frames via KISS" toggle does NOT control this — per the firmware's own wiki, that toggle only affects whether the iGate accepts inbound frames from a TNC app sharing the iGate's own callsign; it's unrelated to echo/monitoring.

**Do not build any future LoRa monitoring/relay tooling on the KISS TCP port.** Use the syslog feed instead (see below).

### Working data source: syslog TX feed
K2GIA-10's built-in Syslog feature (Configuration page, Syslog section) broadcasts real-time log lines over UDP, including actual TX events with full packet content. Confirmed real-world format for a message-type TX:
```
<165>1 - K2GIA-10 CA2RXU_LoRa_iGate_3.2.4 - - - TX / MESSAGE / <FROM> ---> <TO> :<text>{<msgid>
```
Beacon-type TX events use a different format (no `MESSAGE /` marker) and are correctly ignored by the current regex.

K2GIA-10's Syslog Server/Port is currently set to `10.0.0.181` (cnjmesh1) port `1514` — previously was `lora.link9.net:1514` (the public LoRa-APRS.live aggregator; that's still a legitimate destination, worth eventually running *both* if a fan-out is wanted).

`lora-aprs-discord-bridge-v2.py` is deployed at `/opt/lora-aprs-discord/lora-aprs-discord-bridge-v2.py`, listens on UDP 1514, parses the MESSAGE format above, posts to both webhooks. **Not yet fully confirmed posting to Discord end-to-end** — last test was interrupted by the ANSRVR/APRS-IS investigation below. Verify this first next session: run the bridge, send a test message via aprs-tnc-web, confirm it actually lands in both Discord channels.

The old KISS-based bridge (`lora-aprs-discord-bridge.py`, v1) is obsolete — left in place but should not be run; superseded by the v2 syslog-based script.

### K2GIA-10 does NOT self-gate its own outgoing messages to APRS-IS
Confirmed via aprs.fi raw packet history for K2GIA-10 (50+ packets over 24hrs): every single entry was the identical periodic position beacon via `TCPIP*` — none of tonight's test messages (multiple self-addressed tests, a CQ broadcast, and two messages to `ANSRVR` for #APRSThursday) appeared there at all, despite APRS-IS connection being enabled and confirmed connected (`rotate.aprs2.net:14580`, valid passcode, "Gate APRS-IS Messages to RF" also on).

Working theory (not yet verified against firmware source): an iGate's gate-to-IS logic triggers off *received/decoded RF packets*, not off self-originated TX. The periodic beacon is gated via a separate dedicated "send beacon to APRS-IS" path that bypasses RX entirely, which is why beacons reach IS but locally-composed messages don't.

**Open item for next session:** check `richonguzman/LoRa_APRS_iGate` firmware source on GitHub directly to confirm or rule this out before spending money on hardware. If confirmed, the fix is a second, cheap ($15-25) ESP32 LoRa board running the same firmware as an RX-only iGate elsewhere in the house — it would genuinely receive K2GIA-10's real RF transmission (unlike K2GIA-10 hearing itself) and gate it normally. Not yet purchased — Charles wants the source-code check done first given past experience sinking effort into MQTT bridging before verifying feasibility (see May-June 2026 history).

### LoRa RF confirmed genuinely working
- Radio settings confirmed FCC-compliant: 433.775 MHz, SF12 (RX+TX), CR 4/5, BW 125kHz (RX+TX), 20dBm. Verified via search: no numeric bandwidth cap applies to LoRa's "unspecified digital code" modulation on 70cm under 47 CFR §97.307(f) — the 100kHz limit some people cite only applies to Baudot/AMTOR/ASCII.
- Syslog TX log entries independently confirm real transmissions matching aprs-tnc-web's retry counts — e.g. a message retried twice showed two separate `TX / MESSAGE` syslog lines.
- The "Aborted" status on every test message in aprs-tnc-web is expected, not a failure: all tests were self-addressed (to K2GIA-10 itself) or to `ANSRVR` which never received them (see above) — no ACK was ever possible in either case. Not a sign of RF failure.
- Nearest visible LoRa APRS iGate on lora-aprs.live map: KD2ZHO-2 near Newark/Bloomfield NJ, ~30+ miles away. Realistic likely reason K2GIA-10 hasn't heard anyone in 38+ days: genuine lack of nearby users on this mode/band, not a config problem. Stock antenna range is more like 5-15 miles suburban.

### Also unsubscribed from #APRSThursday HOTG group tonight
Sent `CQ HOTG ...` test messages to `ANSRVR` (checked in), then sent `U HOTG` to unsubscribe once we determined the check-in likely never reached APRS-IS anyway (per the self-gating issue above). If the check-in silently succeeded despite that, the unsubscribe covers it either way.

### Not yet done (carried over from July 14 handoff, still pending)
- Roof UHF/VHF antenna swap test for K2GIA-10 (temporarily disconnect UV-5RM, connect K2GIA-10 via PL-259-to-SMA-male adapter) — still the best next real-world range test once/if a second iGate or the source-code check resolves the self-gating question.
- K2GIA-10 web UI admin password still not set (still `admin`/blank).

---

### CONFIRMED (post-session follow-up): self-gating is a genuine firmware limitation, not a missed setting

Checked richonguzman/LoRa_APRS_iGate wiki and GitHub discussions directly:
- Wiki, iGate Configuration page: "Enable APRS-IS Connection: to upload all Rx LoRa packets." -- RX only, explicit.
- Wiki, describing stationMode 2 (what K2GIA-10 runs): "Rx will be sent to APRS-IS, Messages will be sent via Lora." -- confirms the RX-to-IS / TX-to-RF split directly from the developer's own docs.
- GitHub Discussion #214 ("Add API to send APRS messages from igate") is an OPEN feature request asking the developer to add exactly this capability. Developer response: "sure can do! but give me a few days..." -- confirms this does not exist in the firmware as of the discussion. Not a config we missed; a feature that hasn't been built yet.

**Conclusion: the second RX-only iGate plan is correct and necessary, not a workaround for a misconfiguration.** Cheap ESP32 LoRa board (5-25), same firmware, same LoRa radio params (433.775MHz/SF12/BW125k/CR5) as K2GIA-10, own callsign/SSID, Enable LoRa TX OFF, Enable APRS-IS Connection ON with its own passcode. No KISS/TNC setup needed -- just RX + gate. Can sit anywhere in the house with WiFi/USB power; does not need to run on/through either Pi.
