# CLAUDE_CONTEXT.md — CNJ Mesh
**For AI assistants:** Fetch this file at the start of every session. It is the authoritative current-state summary of Charles's infrastructure. Do not ask him to re-explain anything documented here. Treat him as an experienced operator. When presenting the todo list, always show ALL items including medium and longer projects — never summarize or truncate. Ask which todo item to start on and get to work.

Last updated: 2026-07-17

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

---

### cnjmesh3 REPLACEMENT hardware live -- July 16, 2026

Original cnjmesh3 Pi 3B+ unit was faulty (kernel panics), returned to vendor. Replacement Pi 3B+ arrived and is now up.

- New IP: 10.0.0.186 (DHCP-assigned, reserved) -- NOT 10.0.0.133 as the old context entry says. New hardware has a new MAC (B8:27:EB:62:6C:5A), old .133 reservation was bound to the dead unit's MAC and is now orphaned/irrelevant.
- Freshly flashed via Raspberry Pi Imager (Pi OS Lite 64-bit), hostname cnjmesh3, user somog, SSH enabled w/ password auth, WiFi C4Somogyi-24 configured during imaging.
- SSH login confirmed working: ssh somog@10.0.0.186
- Nothing installed yet -- clean slate. Note: initial flash attempts stalled repeatedly at 7-10% (bad state on the laptop, not the SD cards/reader/hardware -- confirmed by testing 2 different cards, 2 different USB ports, with and without caddy, all failing identically). Laptop reboot fixed it; root cause was likely memory pressure (86% RAM used, 115 background processes) rather than anything card/reader-related. If this recurs, reboot the laptop before troubleshooting hardware.

### cnjmesh3 role (per existing plan, item 19 -- confirmed correct, reaffirmed 2026-07-16)
cnjmesh3 = upstairs RF hardware hub. Physically local to where the 2nd-story window antenna feeds are, so it can serially connect: MeshCore Observer, KPR2 repeater, and (new) the second LoRa APRS iGate node (once that hardware arrives -- ordered 2026-07-15, see LoRa APRS section above).

General principle for the cnjmesh1/cnjmesh3 split going forward: things that need a physical/serial connection to RF hardware in the upstairs room move to cnjmesh3. Pure software/dashboard services that don't need to be physically near any radio can stay on cnjmesh1. Corescope, MeshCore Hub, and MeshOmatic all need to stay in mind during this migration -- not yet decided which of these move vs. stay; MeshCore Hub in particular likely needs to move to cnjmesh3 since it talks to the Observer over USB serial, but this needs confirming, not assumed. Not yet decided whether KPR2 needs an actual serial/USB connection to cnjmesh3 (it's a repeater -- typically standalone RF-only, no host connection needed) or whether Charles means something else by "serially connect... kpr2" -- clarify next session before doing this migration work.

Not yet planned/built: actual list of what to install on cnjmesh3 (Docker, MeshCore Hub stack, etc.) -- next session's starting task.

### 2nd LoRa APRS node -- antenna placement decided
K2GIA-10 currently runs an Abree dual-band whip (~$20, decent rated antenna -- corrected from earlier note that called it a "stock/stub" antenna, which was inaccurate) -- not connected to the good grounded roof UHF/VHF feed (that's dedicated to graywolf/UV-5R M).

Decision: the new 2nd LoRa APRS RX-only iGate will use an indoor antenna for now, likely placed in the garage. Reasoning: its only job is to hear K2GIA-10 within the same house (a short indoor hop), not reach distant stations -- a much lower bar than K2GIA-10's own long-range iGate duty. Charles already has extensive antenna infrastructure on the house (roof UHF/VHF + Meshtastic antennas via grounded bus-bar project box, 2 Meshtastic gateway antennas + KPR2 antenna out 2nd-story windows, Observer antenna to be added upstairs too) and does not have unlimited space/desire for more outdoor penetrations right now. Test indoor-to-indoor first once both nodes are running; if the new node can't hear K2GIA-10 reliably, fall back to the already-planned roof-antenna swap test for K2GIA-10 (see earlier LoRa APRS section -- coax loss math already confirmed clean for that swap).

### Clarified: 2nd LoRa node does NOT fix APRSdroid
Important distinction Charles raised and worth keeping straight: the 2nd LoRa iGate solves the self-gating problem (messages reaching APRS-IS), but does NOT change APRSdroid's fundamental limitation -- APRSdroid still cannot speak TCP/IP KISS at all (only Bluetooth-Serial TNC, direct APRS-IS, AFSK, Kenwood). K2GIA-10 has no Bluetooth, only TCP KISS. These are two unrelated problems. aprs-tnc-web (browser tool) remains the way to compose/send LoRa APRS messages from a computer; a dedicated tracker board (e.g. T-Deck Plus) remains the option for phone-free standalone messaging, per the original July 14 handoff doc.

---

### New to-dos -- July 16, 2026 (end of session)

**KPR1 retirement.** Charles doesn't want to run 2 MeshCore repeaters going forward, especially with KPR1 stuck in the garage (worse location than KPR2). Plan: retire/decommission KPR1. Not yet scheduled -- needs a session to actually pull it down and update any docs/dashboards referencing it (CoreScope, MeshCore Hub node list, this context file's KPR1 entry, etc.).

**Replace Kendall Park Client 1 (currently old/junked Heltec V3).** This is the device the meshcore-mqtt bridge on cnjmesh1 connects to via /dev/ttyUSB2 -- already flagged as having a serial flapping issue, already planned for replacement with a Heltec V4 or second WisMesh Pocket (see meshcore-mqtt bridge notes above). New idea from Charles: check if the V3's old case still exists and is intact -- if so, could reuse the V3 itself (not junk it) as a portable/movable MeshCore client rather than buying new hardware for that role. Worth checking case condition before deciding whether to buy new hardware or refurbish the V3.

**Correction logged this session:** MeshCore tooling (Observer, KPR1/KPR2, meshcore-mqtt bridge, CoreScope) does NOT feed Malla or meshview -- those are Meshtastic-only tools fed by CJG1/CJG2 via Mosquitto MQTT. MeshCore has its own separate toolchain (CoreScope, MeshCore Hub, mesh-discord-shim's MeshCore relays). Keep these two ecosystems straight going forward -- don't conflate them.

### New to-dos — July 17, 2026 (from sidebar chat: MeshCore regioning, radio tuning, CoreScope incident, watchdog)

**Radio tuning (KPR1, KPR2, Observer):** Apply the Capital District Mesh radio-tuning whitepaper (cdme.sh/repeaters/radio-tuning-whitepaper) §9.4.2 table to CNJ Mesh repeaters. First step: gather each repeater's current SNR-positive neighbor count (via CoreScope or CLI), then generate the specific `set txdelay` / `set direct.txdelay` / `set rxdelay` values per repeater based on that count. Paper's proposed new static defaults if not doing per-repeater tuning: `txdelay=1.1`, `direct.txdelay=0.5`, `rxdelay=2`. Not yet started — neighbor counts not yet gathered.

**CoreScope data-pipeline outage — diagnosed, not resolved.** Dashboard showing 0 Transmissions/Nodes/Last-24h while historical counts (37 Observers) persist — points to a live ingest failure (MQTT broker connection or CoreScope-side), not the "No packets from meshomatic" banner (confirmed a red herring, Meshomatic contact isn't a CoreScope dependency). Diagnostic commands to run:
```bash
docker ps | grep corescope
docker logs corescope --tail 150 | grep -iE "mqtt|connect|disconnect|error"
mosquitto_sub -h localhost -p 1883 -t '#' -v -C 10
docker logs $(docker ps -qf name=mosquitto) --tail 200
```
If `mosquitto_sub` shows no traffic, problem is upstream (broker/publishers). If traffic's present but dashboard still zeroed, try `docker restart corescope`.

**Deploy cnj-watchdog.** Built in a separate session (files in that session's outputs: `watchdog.py`, `.env.example`, `cnj-watchdog.service`, `cnj-watchdog.timer`, `README.md`) — a custom Python watchdog that listens briefly on the MQTT broker each run, tracks idle time across runs via `state.json`, checks configured Docker containers, and alerts to Discord only on state change (down→alert, recovered→alert). Chosen over Uptime Kuma specifically because CoreScope's own incident showed its web server stayed up even while the data pipeline was dead — a simple port/HTTP check would have missed it; this watchdog checks the real MQTT data path instead. Not yet deployed. Deployment steps: copy files to `/opt/cnj-watchdog` on cnjmesh1, configure `.env` (real Discord webhook URL + actual container names, confirm via `docker ps --format '{{.Names}}'`), enable systemd timer, verify via `systemctl list-timers` + `journalctl`.

**MeshCore regioning — talking points to bring back to NY/NE Mesh Discord.** Not yet actioned. Key points to raise: (1) push for nested region hierarchy, not flat namespace; (2) geography should win over political boundaries where real communities overlap; (3) don't let a short Discord poll lock in long-term technical naming/hierarchy without seeing a full proposal doc; (4) CNJ Mesh (300+ nodes) is positioned to propose its own regional naming convention (e.g. `us` → `nj` → `cnj`/`nnj`/`snj` → local metro) rather than just adopting another region's scheme; (5) explicit ask for a cross-border NJ/PA tag (e.g. `lv-cnj`) so LVMesh (Pennsylvania, in RF range of CNJ Mesh) doesn't get isolated by a state-line-drawn region boundary. Background: MeshCore's protocol-level regions are sender-chosen, opt-in, non-enforced tags (up to ~32 per repeater) — separate and distinct from MeshMapper's own unrelated "regions" concept (administrative coverage-map boundaries, doesn't affect routing). MeshMapper itself evaluated and deemed not needed for CNJ Mesh — it's a wardriving/drive-tested-coverage tool, different niche than CoreScope/MeshCore Hub/Meshomatic's live monitoring.


### cnjmesh3 upstairs RF hub — Observer + KPR2 migration COMPLETE — July 17, 2026

**Completed:**
- Docker installed on cnjmesh3 (v29.6.2, arm64), confirmed working without sudo (docker group applied).
- **Observer (WisMesh Pocket v2, RAK4631)** physically relocated upstairs to cnjmesh3, connected via USB at `/dev/ttyACM0` (confirmed via dmesg: `Product: WisCore RAK4631 Board`, serial `06308D8BE14915FD`). `meshcore-packet-capture` deployed via docker run (privileged, --group-add dialout, --device /dev/ttyACM0), config.d copied directly from cnjmesh1 (`10-letsmesh.toml`, `20-meshomatic.toml`, `30-local.toml` — all unchanged, since `30-local.toml` already targeted `10.0.0.181:1883`, which is correct for cnjmesh3 too). Confirmed live: connected to all 4 brokers (letsmesh-us, letsmesh-eu, meshomatic, local), actively capturing real packets with SNR/RSSI data.
- **KPR2 (Heltec V4 MeshCore repeater)** physically relocated upstairs to cnjmesh3, connected via USB at `/dev/ttyACM1` (confirmed via dmesg: `heltec_wifi_lora_32 v4`, serial `E8F60AC9DEB4`). `meshcore-mqtt` bridge built from source (`git clone https://github.com/ipnet-mesh/meshcore-mqtt.git` → `docker build -t meshcore-mqtt:local .`) since the running instance on cnjmesh1 is a custom local build, not the public ghcr.io image. Deployed via docker run pointed at `/dev/ttyACM1`, MQTT_BROKER=10.0.0.181, using the actual working credentials from cnjmesh1's live container (`meshdev`/`large4cats` — note: this differs from what's in cnjmesh1's `.env.docker` file on disk, which says `meshuser` — the live container was evidently started a different way; `meshdev`/`large4cats` is the confirmed-working pair). Confirmed live: connected to MQTT broker, serial connection to `/dev/ttyACM1` established, subscribed to all configured events.

**Architecture decision (locked in):** Mosquitto broker, MeshCore Hub, and CoreScope all **stay on cnjmesh1** — no reason to run a second broker or move the dashboard/hub services, since cnjmesh3's two new containers just publish outward to cnjmesh1's existing broker over the LAN (`10.0.0.181:1883`). cnjmesh3's role is purely: physically host devices that need a local USB/serial connection (Observer, KPR2), nothing else.

**K2GIA-10 explicitly NOT moved to cnjmesh3** — stays connected to cnjmesh1 via USB for now. Separate, not-yet-started task: physically relocate K2GIA-10 upstairs for antenna height (it's WiFi-based/standalone, no serial dependency on any Pi, so this is purely a placement/antenna task, independent of the cnjmesh3 serial migration).

**Also completed this session (quick hits):**
- K2GIA-10 web UI admin password set (was blank since initial setup — fixed via toggling "Web interface authentication" off/on to unstick a frozen password field, then setting a real password).
- graywolf-discord-bridge watchdog confirmed working end-to-end via an actual timer fire (not just a manual script run) — stopped the bridge, waited for the 5-min timer, confirmed both auto-restart and the Discord alert landed correctly.

### New to-dos — July 17, 2026 (post-cnjmesh3-migration)

**Verify CoreScope, MeshCore Hub, and Meshomatic still working correctly after the Observer/KPR2 move.** Charles flagged that Observer was previously registered with Meshomatic and wasn't sure if anything about that registration is tied to Observer's prior physical host (cnjmesh1). Working theory: Observer's Meshomatic/letsmesh registration is tied to the Observer's own identity (IATA code "CNJ", pubkey A8C40BF3) via the packet-capture config, not to which Pi it's physically plugged into — so this should be unaffected by the move. Not yet confirmed live — check next session.

**Add monitoring/watchdogs to cnjmesh3.** Charles uses **UptimeRobot** (not Uptime Kuma) for cnjmesh1's existing monitoring. Neither new cnjmesh3 container (meshcore-packet-capture, meshcore-mqtt-bridge) exposes a web UI/HTTP endpoint, so there's nothing for UptimeRobot's normal pull-based checks to hit. Recommended approach: UptimeRobot **push/heartbeat monitoring** (cnjmesh3 pings UptimeRobot periodically via a cron job) rather than extending the Cloudflare Tunnel to cnjmesh3 — no need to build a fake HTTP endpoint just to satisfy a pull-based checker. Not yet built.

**Cloudflare Tunnel exposure for cnjmesh3 — resolved as not needed for now.** Neither current cnjmesh3 service needs public/Cloudflare access. Revisit only if a future service on cnjmesh3 needs one.

**K2GIA-10 upstairs relocation for antenna height** — not yet started, separate task from the cnjmesh3 serial migration (see above).


---

## Session — July 17, 2026 (evening/night): CoreScope root-cause fix, watchdogs, cnjmesh3 completion, community outreach

### CONFIRMED WORKING — Meshomatic, LetsMesh, MeshCore Hub verification after cnjmesh3 migration
Verified via CoreScope logs that Observer's move to cnjmesh3 did NOT break anything:
- `[local]` MQTT source connects and subscribes cleanly to the real broker
- `[meshomatic]` source connected, actively receiving status/foreign-advert traffic
- Both `letsmesh-us` and `letsmesh-eu` confirmed connected with JWT on-device auth in meshcore-packet-capture logs on cnjmesh3
- MeshCore Hub (3 containers: collector, web, api) all healthy on cnjmesh1, unaffected

### MAJOR FIND — CoreScope 8+ day data outage: ROOT CAUSE FOUND AND FIXED

**Symptom:** CoreScope dashboard showing 0 Transmissions/0 Nodes/0 Last-24h for 8+ days (12883+ min per the "No packets from meshomatic" banner), while historical counts (37 Observers) persisted. This was the same unresolved issue flagged in an earlier sidebar chat — now actually fixed.

**Root cause:** CoreScope's `local` MQTT source in `/home/somog/meshcore-data/config.json` was configured as `mqtt://localhost:1883`. CoreScope runs its **own embedded MQTT broker** inside its own container (confirmed via `docker exec corescope netstat -tlnp` showing something listening on container-internal port 1883, and the container's port mapping `1884->1883/tcp`). Because CoreScope's container runs in Docker's default `bridge` network mode (isolated network namespace), `localhost:1883` inside that container resolved to **its own internal broker**, not cnjmesh1's real Mosquitto. It was talking to itself — clean connects, clean subscribes, zero real messages, forever. `allow_anonymous false` on the real broker meant an anonymous connection (which is what `local` source was using, no credentials configured) would have failed outright if it had ever actually reached the real broker — it never did, so no auth error ever surfaced either.

**Fix applied:**
1. Backed up original config: `docker exec corescope cat /app/data/config.json > /tmp/corescope-config-backup.json` (on cnjmesh1)
2. Confirmed the Docker bridge gateway IP from inside the container: `docker exec corescope ip route | grep default` → `172.17.0.1`
3. Edited `/home/somog/meshcore-data/config.json` (host-side bind-mounted file) via Python: changed the `local` mqttSources entry's `broker` from `mqtt://localhost:1883` to `mqtt://172.17.0.1:1883`, added `username: meshdev`, `password: large4cats` (same creds already used by other services)
4. `docker restart corescope`
5. **Confirmed fixed** — logs show `MQTT [local] connected to tcp://172.17.0.1:1883`, followed by real `foreign advert` and `status` messages flowing in, `[broadcast] sending N packets to N clients` events firing. Dashboard should now show live Transmissions/Nodes/Last-24h counts climbing instead of stuck at zero. This fix persisted through a container restart, confirming it's not just an in-memory fluke.

**Note on the also-broken `lincomatic` and `wsmqtt` mqttSources entries in the same config file:** these are leftover example/template entries with fake credentials (`your-username`/`your-password`, `wsmqtt.example.com`) — NOT real Charles infrastructure, safe to ignore or clean up later, not part of tonight's outage.

### cnj-corescope-watchdog — BUILT AND DEPLOYED (on cnjmesh1)
New monitoring specifically for the failure mode just found — checks CoreScope's own `[ingestor] [stats] tx_inserted=N ...` log line (printed roughly every 5 min) and alerts if `tx_inserted` stops climbing, which is a genuine "is data actually flowing" check (unlike a port/HTTP check, which would have shown "healthy" the whole 8-day outage since CoreScope's web server stayed up throughout).

Files:
- `/opt/corescope-watchdog/watchdog.sh`
- `/opt/corescope-watchdog/state.json` (auto-created, tracks last_value/stall_count/alerted)
- `/etc/systemd/system/corescope-watchdog.service`
- `/etc/systemd/system/corescope-watchdog.timer` (OnBootSec=2min, OnUnitActiveSec=5min)

**Alerts post to a NEW dedicated Discord webhook/channel** — `#cnjmesh` in the "CNJ Mesh various meshes" server, webhook created 2026-07-17 by somogyic. This channel is intended going forward as the general home for CNJ-MeshCore-related alerts (not just CoreScope). Webhook URL is in the watchdog script itself (`/opt/corescope-watchdog/watchdog.sh`) — do not lose track of this webhook if that script is ever rebuilt.

**Three real bugs found and fixed while building this script tonight — same watchdog script, three separate root causes, all now resolved:**
1. `--tail 200` was too shallow — CoreScope logs so many Meshomatic status lines (~1/sec) that 200 lines only covered ~3 min, but `[stats]` only prints every ~5 min. Fixed: bumped to `--tail 2000`.
2. `2>/dev/null` on the `docker logs corescope` command was discarding almost the entire log stream. **CoreScope logs almost everything to stderr, not stdout** — confirmed via `docker logs corescope --tail 2000 2>/dev/null | wc -l` (32 lines) vs `docker logs corescope --tail 2000 | wc -l` (thousands). Fixed: removed the `2>/dev/null` suppression.
3. Even after removing `2>/dev/null`, `$LATEST` still came back empty — because bash's `$(...)` command substitution only captures **stdout**, not stderr, by default; removing a redirect just let stderr flow to the terminal instead of being captured. Fixed: added `2>&1` inside the substitution specifically (`docker logs corescope --tail 2000 2>&1 | grep ...`) so stderr gets merged into stdout *before* being captured.

**Confirmed working end to end:** manual run produced a real `state.json` (`{"last_value": 12, "stall_count": 0, "alerted": false}`), timer installed and fired its first scheduled run cleanly.

### cnjmesh3 — Observer + KPR2 migration: FULLY COMPLETE (carried over from earlier tonight, now also verified downstream)
See the earlier same-day entry above for full build detail (Docker install, physical USB moves, meshcore-packet-capture and meshcore-mqtt-bridge deployment). Tonight's additional confirmation: the whole downstream chain (Meshomatic, LetsMesh, MeshCore Hub, and now CoreScope once its unrelated pre-existing bug was fixed) all correctly receive data that originates from cnjmesh3, proving the "cnjmesh3 publishes outward to cnjmesh1's broker over the LAN" architecture decision was sound.

### Quick hits completed tonight
- K2GIA-10 web UI real password set (was blank) — required toggling "Web interface authentication" off/on first to unstick a frozen password field
- graywolf-discord-bridge watchdog: confirmed firing correctly via the actual systemd timer (not just manual script execution) — stopped the bridge, waited for the real 5-min timer, confirmed both auto-restart and Discord alert landed
- graywolf-discord-bridge watchdog: hostname `cnjmesh1` removed from the alert message text (Charles doesn't want the Pi hostname published to the Discord community) — logic unchanged, `sed` edit only

### Community outreach — Tilly message drafted (NOT YET SENT)
Charles wants to reach out to Tilly (MeshOmatic admin, based in Old Bridge NJ — east of Kendall Park) about testing MQTT connectivity to `mqtt.cnjmesh.me`. Final drafted message (ready to send, Charles has not sent yet):

> "Hey Tilly — following up on the MQTT bridging convo from a while back. Since you mentioned that goes against MeshCore's core design, I didn't pursue a bridge — but I did make my broker (mqtt.cnjmesh.me) publicly reachable over WSS/port 443 via Cloudflare Tunnel, no port forwarding or VPN needed on your end.
>
> If you're up for it: point CoreScope (or an observer) at:
> Broker: mqtt.cnjmesh.me
> Port: 443
> Transport: WebSocket Secure (wss)
>
> I'll send credentials whenever's good. If we tie in both ways — you pulling from my broker and me pulling from yours — you'd see what my observer sees and I'd see what your observer sees, so we'd both get a wider combined picture in CoreScope than either of us has alone.
>
> None of this is urgent or important — just floating it. No worries at all if you're not up for it or don't want to go down this path right now."

**Important scope-setting established this session, worth remembering for any future community outreach:** MQTT connectivity to `mqtt.cnjmesh.me` (or LetsMesh) provides **shared visibility/analytics only** — it does NOT enable actual cross-network messaging or a real RF bridge. This is architectural in MeshCore (Tilly's own prior confirmation: "goes against the core of MC"), not a config limitation. The only theoretical path to real MQTT-to-RF bridging is the agessaman MQTT firmware fork, which is NOT yet merged upstream and would require non-standard firmware on repeaters. Similarly clarified tonight: if Charles and ozneteast both report into LetsMesh as observers, they get a shared benefit through **LetsMesh's own global map/analyzer tools** (seeing both coverage areas together) — but this does NOT unlock direct messaging between them either; same architectural ceiling applies regardless of which broker/aggregator is used.

**⚠️ Still outstanding before sending outreach messages to Tilly/ozneteast/y0gurt:** credentials (`meshuser`/`meshdev` + `large4cats` password) need rotating before being shared further externally — this was already flagged as overdue back in the July 12-13 session ("rotate meshuser/large4cats... now that mqtt.cnjmesh.me is publicly reachable over WSS") and remains undone. Sharing the current credentials with three more external people makes this more urgent, not less.

### New to-dos — July 17, 2026 (end of session)

1. **Rotate `meshuser`/`meshdev` MQTT credentials** on cnjmesh1's Mosquitto before sending the Tilly (or any future ozneteast/y0gurt) outreach message — carried-over overdue item, now higher priority given external sharing is imminent.
2. **Send the drafted Tilly message** (see above) once credentials are rotated — get his CoreScope/observer pointed at `mqtt.cnjmesh.me:443` (wss), confirm two-way visibility works.
3. **Clean up the fake/template `lincomatic` and `wsmqtt` entries** in CoreScope's `mqttSources[]` config (`/home/somog/meshcore-data/config.json`) — not real infrastructure, currently generating harmless but noisy repeated connection-attempt log spam every ~30s.
4. **Confirm CoreScope dashboard is now actually showing live data** (Transmissions/Nodes/Last-24h counts climbing) from the browser/UI itself, not just from log evidence — quick visual sanity check, not yet done.
5. Everything else carried over from the earlier July 17 entries above (radio tuning, KPR1 retirement, Client 1 replacement, MeshCore regioning talking points, K2GIA-10 upstairs relocation) remains open and untouched tonight.


---

## Session addendum — July 17, 2026 (LetsMesh investigation + reference tools)

### LetsMesh map/observer investigation — findings, unresolved
- Confirmed via `analyzer.letsmesh.net/status/observers?region=CNJ`: "CNJ Mesh Observer" (pubkey A8C40BF3...3A26B975) shows **ONLINE**, region correctly tagged **CNJ** (not JVI — resolves earlier ambiguity from the same-day entry above).
- LetsMesh map (`analyzer.letsmesh.net/map`) zoomed to NJ shows solid statewide node density — NW corner near Sparta down through Trenton/Philly-Camden area, coastal presence from Sandy Hook down to Atlantic City. Good shareable content for Discord if desired.
- **Packets page** (`analyzer.letsmesh.net/packets` or similar route) initially showed "0 packets" / "No packets found" with a "Reconnect" button showing red — this was a **disconnected live WebSocket feed**, not a real data problem. Mobile browsers commonly suspend background WebSocket connections when a tab isn't in the foreground; hitting "Reconnect" is the fix, not a config issue on Charles's end.
- After reconnecting: **Latest 500 Packets, all tagged region CNJ, real current timestamps (~3:40-3:47 PM same day)** — Adverts, TextMessages, GroupText, Responses all actively flowing. This contradicts the earlier-noted "38+ days since last heard a station directly" from Observer's own local syslog — **not reconciled**, worth investigating next session which figure is actually accurate (stale old log line vs. genuinely fresh CNJ regional activity Observer is now hearing).
- **Still NOT showing on the map itself** despite packets clearly flowing on the Packets page — unresolved, Charles chose not to dig further tonight. Worth checking next session: map-specific filters/toggles, data lag between packets feed and map rendering, or whether map only plots certain packet/node types.
- **KB2EAR-2 (known-nearby MeshCore repeater, ~772m from Charles per existing notes) is NOT appearing** in the CNJ packet feed — genuinely odd given the very close range. Not urgent, but flagged as worth checking: whether it's simply not advertising in the observed window, a "Group by Hash" deduplication/display quirk, or an "All Observers" filter scoping issue (the packets page may only be showing what Charles's own Observer heard, not what *any* observer heard — needs confirming next session).
- **Clarified: packet/map data is per-Observer, not a directory of "everyone in the region."** A node only appears if it was actually heard on RF by *some* observer within the displayed dataset — it's not self-reported/opt-in the way a directory listing would be.

### GitHub tools for future MQTT/bridging reference — SAVED, not yet evaluated in depth
Three projects flagged across earlier sessions as relevant if Charles wants to revisit "open up MQTT communications" further:

1. **agessaman's MQTT firmware fork** — modified MeshCore *repeater* firmware with MQTT support built directly in. This is the only one of the three that could theoretically enable genuine two-way MQTT-to-RF bridging (message in via MQTT, real LoRa transmission out) — the capability stock MeshCore firmware doesn't have. **Status: NOT yet merged upstream.** Would require flashing non-standard firmware onto a repeater, no official community support.
2. **mr-tbot's mesh-api** — cross-mesh bridging, AI-on-mesh, emergency alerts. Broader scope, not yet actually investigated in any session — only named/filed.
3. **MeshCoreDiscordBridge (Hude06)** — bidirectional Discord bridge via serial connection. Different problem than MQTT-to-RF bridging (this connects MeshCore directly to Discord, not to another MQTT-based mesh network) — most directly relevant to the new to-do below.

None of these three have been cloned, tested, or evaluated for current maturity/viability — purely reference pointers for a future session.

### New to-do — tinkering project, explicitly low priority
Charles wants to test: **sending MeshCore messages to a Discord channel and vice versa** (Discord → MeshCore). Explicitly framed as "not important, worth a test for the sake of tinkering" — no urgency, casual experiment. **MeshCoreDiscordBridge (Hude06)** above is the most obviously relevant starting point for this, given it's specifically a bidirectional Discord↔MeshCore bridge via serial — worth looking at first when Charles wants to pick this up.


---

## New to-dos — July 21, 2026 (cnjmesh1 hardware failure, pending recovery)

**cnjmesh1 hardware failure — CONFIRMED, board replacement ordered.**
- Root cause chain: root filesystem hit 100% (disk-full), followed by a manual hard power cycle mid-write while services were crash-looping. This is the suspected trigger for corrupting the Pi 4's bootloader EEPROM.
- Diagnosis fully ruled out: SD card (tested 3 different cards — original, old backup, fresh Pi OS Lite 64-bit flash — all showed zero green LED), official power supply (confirmed correct 5.1V/3A unit), monitor/cable (tested on 2 different monitors, both showed no signal), and EEPROM corruption (attempted official `rpi-eeprom-recovery` SD card process — zero green LED even during recovery attempt, meaning the board itself has a genuine hardware fault, not a recoverable EEPROM issue).
- **Replacement Pi 4 board ordered July 21.** Original SD card (last confirmed good backup July 12-13, plus subsequent config changes) is intact and should boot normally once the new board arrives — no reimaging needed.
- **When new board arrives:** (1) insert original SD card, boot, verify services come up; (2) restore SJMesh bridge config into `/opt/stacks/mqtt/config/mosquitto.conf` on cnjmesh1 from `docs/sjmesh-bridge-backup.md` (already committed to this repo); (3) manually redo CoreScope's `config.json` local MQTT source fix (`mqtt://172.17.0.1:1883`, `meshdev`/`large4cats` creds) — NOT backed up anywhere, was lost with the dead board; (4) corescope-watchdog's `state.json` — not backed up, safe to lose/regenerate; (5) confirm SJMesh bridge, CoreScope, MeshCore Hub, meshview, Malla, mesh-discord-shim, Graywolf APRS all come back healthy.
- **What stayed up during the outage (confirmed via git 2026-07-20 notes):** MeshOmatic and LetsMesh (both US and EU) — cnjmesh3's Observer/KPR2 connect to these directly, independent of cnjmesh1's broker. Everything else (Mosquitto/MQTT, MeshCore Hub, CoreScope, mesh-discord-shim, meshview, Malla, Graywolf) was fully down for the duration.

**New: build and deploy a disk + temperature watchdog for all three Pis.**
- Purpose: directly prevents recurrence of the July 19-20 disk-full → hard power cut → dead board failure chain.
- Design (matching existing watchdog pattern — Python + systemd timer, alert-only on state change, posts to `#cnjmesh` Discord webhook):
  - Disk usage: warning at 80%, urgent at 90% (via `shutil.disk_usage('/')`)
  - Temperature: warning at 70°C, urgent at 80°C (via `vcgencmd measure_temp`) — Pi 4/3 throttle around 80°C
- Deployable to cnjmesh2 and cnjmesh3 immediately (both currently up); add to cnjmesh1 once the new board is stable.
- Not yet built.


**KPR1 retirement — now confirmed, queued for cleanup once cnjmesh1 is back.**
- MC companion reconnected to wall power July 21, back on MC network — unrelated to cnjmesh1 outage.
- KPR1 will NOT be reconnected once cnjmesh1's new board is up. Effectively retired as of this outage.
- Cleanup needed once cnjmesh1 is back and stable (documentation only, nothing urgent/destructive):
  1. Mark KPR1 row in this file's device table as retired/decommissioned
  2. Flip KPR1 to ARCHIVED status in the `whorepeated` tool
  3. Mark KPR1 as retired/offline in CoreScope's node list, if it has that concept
  4. Mark KPR1 as retired/offline in MeshCore Hub's node list, if applicable
  5. `/dev/ttyUSB1` on cnjmesh1 becomes free once KPR1's physically disconnected — relevant if that port gets reused later
- No community Discord announcement planned — Charles's call, not considered necessary for this repeater.


---

## Antenna inventory and placement constraints — July 21, 2026

Full picture logged for future reference, since antenna real estate is now fully allocated and any new hardware placement decisions need to work around this.

**Fixed constraint (top priority, non-negotiable):** Icom 2730 requires a rooftop UHF/VHF antenna at all times. This is Charles's primary radio and takes precedence over any other device competing for the same roof position.

**Current allocation:**

| Antenna / Location | Device(s) | Notes |
|---|---|---|
| Comet GP3 (roof, UHF/VHF) | Icom 2730 | Dedicated, not shared — this is the fixed constraint above |
| Separate roof antenna | KPN6 (LoRa Meshtastic node) | |
| Alfa antenna (2nd floor, out window) | CJG1, CJG2 | Both Meshtastic gateways |
| 2nd floor, out window | MC Observer, KPR2 | MeshCore hardware |

**Graywolf APRS (K2GIA-M, UV-5R M + Digirig) — decision made this session:**
- Previously used the good rooftop UHF/VHF feed shared conceptually with the Icom 2730 setup — but Charles has decided this is not sustainable; the rooftop antenna needs to stay fully dedicated to the Icom 2730.
- **Plan:** move Graywolf (UV-5R M + Digirig) upstairs to cnjmesh3's location, on a whip antenna — not rooftop.
- **Accepted tradeoff:** meaningfully reduced RF range/coverage for APRS digipeating and iGate traffic vs. rooftop gain. Considered acceptable given the roof antenna's higher-priority use.
- **What's needed:** UV-5R M + Digirig physically relocate to cnjmesh3, connected via USB same as today (RTS-line PTT dependency, so this is a physical move, not just a software/config change). A new whip antenna needed for this location.
- K2GIA-10 (the separate WiFi-based LoRa APRS iGate board, not Graywolf) has no serial/antenna dependency tied to this move — already flagged separately as a second, RX-only board with its own antenna placement (indoor/garage, decided July 16).

**Why this matters:** every existing "good" antenna position (roof x2, Alfa out the 2nd floor window) is already spoken for by higher-priority gear. Any future hardware needing a strong outdoor position will need to either share/timeshare an existing feed or accept an indoor/whip compromise like Graywolf is now doing.


---

## Session — July 21, 2026 (evening): disk/temp + peer-check watchdogs built and deployed to cnjmesh2/cnjmesh3

### New watchdogs — BUILT, DEPLOYED to cnjmesh2 and cnjmesh3, CONFIRMED WORKING

**`watchdogs/disk-temp-watchdog/`** — checks root filesystem usage and CPU temp on the host it runs on.
- Thresholds: disk warning 80%/urgent 90%, temp warning 70°C/urgent 80°C.
- Alert-only on state change (ok→warning→urgent→ok), same pattern as corescope-watchdog.
- Deployed to cnjmesh2 (`Node 2`) and cnjmesh3 (`Node 3`). Confirmed clean output on both, e.g. `Node 3: disk=15.7% (ok) temp=40.2C (ok)`.

**`watchdogs/peer-check/`** — each Pi pings the OTHER two Pis' IPs and alerts if one stops responding. No third-party tool, no cost. Solves the "is a Pi itself online/offline" gap that disk/temp alone doesn't cover (a dead Pi can't self-report). Deliberately NOT a central monitor — each Pi checks the others independently, so one Pi being down doesn't blind you to the rest; only fails if two Pis go down simultaneously.
- Deployed to cnjmesh2 (checks Node 1 + Node 3) and cnjmesh3 (checks Node 1 + Node 2).
- Confirmed working: both cnjmesh2 and cnjmesh3 independently alerted `CNJMESH Node 1 appears OFFLINE` when cnjmesh1's outage was detected — correct behavior, not a duplicate bug, since each Pi alerts independently.
- Alerts once on down, once on recovery — no repeat spam while state is unchanged, confirmed in practice (checked every 5 min, only 1 alert per actual transition).

**Both post to the existing `#cnjmesh` Discord channel/webhook** (same one corescope-watchdog and graywolf's watchdogs already use — confirmed appropriate to share, not a new channel).

**Node label scheme adopted (privacy — hostnames not posted publicly):** cnjmesh1 = "Node 1", cnjmesh2 = "Node 2", cnjmesh3 = "Node 3" in all Discord-facing alert text, via `NODE_LABEL` env var per host. Real hostnames never appear in alerts.

**Two real bugs found and fixed during deployment (both pushed to git, affects all hosts going forward):**
1. `systemd` `Environment=NODE_LABEL=Node 2` (no quotes) silently truncated at the space, dropping the number — fixed by quoting: `Environment="NODE_LABEL=Node 2"`. Hit on both cnjmesh2 and cnjmesh3 deploys, same fix applied both times.
2. Discord webhook posts returned `HTTP Error 403: Forbidden` — root cause: missing `User-Agent` header, which Discord's endpoint requires. Fixed in both `watchdog.py` and `peer-check.py` by adding `User-Agent: cnjmesh-watchdog/1.0` to the request headers. This means the corescope-watchdog-style webhook POST pattern should be checked for the same issue if ever rebuilt from scratch.

### Full inventory of what posts to #cnjmesh, going forward (once cnjmesh1's back)
- **corescope-watchdog** (cnjmesh1 only) — CoreScope data-pipeline stall detection
- **graywolf-discord-bridge watchdog** (cnjmesh1 only) — auto-restarts the Discord bridge
- **graywolf.service watchdog** (cnjmesh1 only) — alert-only, no auto-restart (PTT risk)
- **aprs_monitor.py** (cnjmesh1 only) — 48hr dead-air + service crash checks
- **disk-temp-watchdog** (all 3 Pis) — disk % and CPU temp
- **peer-check** (all 3 Pis) — online/offline detection between Pis

### To-do when cnjmesh1's new board is stable
Deploy disk-temp-watchdog and peer-check to cnjmesh1 too, same steps as cnjmesh2/cnjmesh3:
- `NODE_LABEL=Node 1`
- peer-check `PEERS=Node 2:10.0.0.91,Node 3:10.0.0.186`
- Confirmed no naming/path conflicts with existing cnjmesh1 watchdogs (corescope-watchdog, graywolf x2, aprs_monitor) — separate folders (`/opt/disk-temp-watchdog/`, `/opt/peer-check/`) and separate systemd unit names, safe to coexist.


### Undervoltage detection added to disk-temp-watchdog — confirmed deployed to cnjmesh2 and cnjmesh3
Discussed and deliberately scoped down: added undervoltage (relevant given tonight's board failure — undervoltage during a write can cause similar corruption to a hard power cut). Skipped RAM monitoring (no history of RAM issues, not evidence-based). Held USB device presence checks until Graywolf's move to cnjmesh3 stabilizes the expected device list.
- Confirmed working on both: `Node 2: disk=17.9%(ok) temp=45.6C(ok) undervolt=ok`, `Node 3: disk=15.7%(ok) temp=39.7C(ok) undervolt=ok`
- No alerts fired (power supplies clean on both, as expected)
- Same alert-on-change pattern, same #cnjmesh channel


### Future consideration — switch watchdog alerts from Discord to email
Charles raised a concern: Discord dependency (platform could go away) and alerts being visible to the whole community rather than private. Decided to stick with Discord (#cnjmesh) for now, but revisit later. Planned approach when ready: Gmail SMTP with an app password (no server to run), convert disk-temp-watchdog.py and peer-check.py to use Python's built-in smtplib instead of/alongside the Discord webhook. Not started.


### Service-to-node mapping — confirmed for peer-check SERVICES alerts
- **cnjmesh1 hosts:** meshview, Malla, MeshCore Hub, CoreScope, MQTT broker, mesh-discord-shim, LoRa APRS (Graywolf/K2GIA-10, 2m)
- **cnjmesh2 hosts:** malla2.cnjmesh.me (new info, not previously documented — confirmed by Charles 2026-07-21)
- **cnjmesh3 hosts:** Observer + KPR2, feeding MeshOmatic and LetsMesh directly — if cnjmesh3 goes down, MeshOmatic/LetsMesh stop receiving CNJ Mesh data (not a locally-hosted service, but an outbound feed that stops)

peer-check's SERVICES env var (added 2026-07-21) uses this mapping so down-alerts say what's actually affected, not just "node down":
- cnjmesh2 config: `Node 1:meshview,malla,meshcorehub,mqtt,LoRa APRS 2m;Node 3:MeshOmatic feed,LetsMesh feed`
- cnjmesh3 config: `Node 1:meshview,malla,meshcorehub,mqtt,LoRa APRS 2m;Node 2:malla2.cnjmesh.me`
- cnjmesh1 config (once back): `Node 2:malla2.cnjmesh.me;Node 3:MeshOmatic feed,LetsMesh feed`


### Cross-posting to Meshtastic Discord — CONFIRMED WORKING on cnjmesh2 and cnjmesh3
Charles created a new "cnjmesh general" channel in the "Central & South New Jersey Meshtastic" Discord server specifically for this. Webhook: `https://discord.com/api/webhooks/1529297959987183659/o1jPNQaxa67uK5-9tmbUfOCoKny6IFaWsHy9nIFCyNLFdlkJ95RMflxn21ZUf-9l8J0Z` (webhook name "Spidey Bot", channel #cnjmesh in that server).

peer-check now cross-posts Node 1 and Node 2 alerts (meshview/malla/malla2 — Meshtastic-relevant) to both #cnjmesh (CNJ server) AND the new Meshtastic server channel. Node 3 (MeshOmatic/LetsMesh feed, MeshCore-specific) stays CNJ-only, correctly not cross-posted — not relevant to that audience.

Confirmed via live test on both cnjmesh2 and cnjmesh3: Node 1 down-alert (with services listed: meshview, malla, meshcorehub, mqtt, LoRa APRS 2m) appeared correctly in both Discord servers.

**Config per host (peer-check.service env vars):**
- cnjmesh2: `SERVICES=Node 1:meshview,malla,meshcorehub,mqtt,LoRa APRS 2m;Node 3:MeshOmatic feed,LetsMesh feed` / `CROSS_POST_LABELS=Node 1,Node 2`
- cnjmesh3: `SERVICES=Node 1:meshview,malla,meshcorehub,mqtt,LoRa APRS 2m;Node 2:malla2.cnjmesh.me` / `CROSS_POST_LABELS=Node 1,Node 2`
- cnjmesh1 (once back): `SERVICES=Node 2:malla2.cnjmesh.me;Node 3:MeshOmatic feed,LetsMesh feed` / `CROSS_POST_LABELS=Node 2` (no Node 1 self-reference needed once it's the one running this)


### SERVICES mapping corrected — full domain names, CoreScope nuance clarified
Charles requested full domain names (e.g. `malla.cnjmesh.me`) instead of generic tool names (`malla`) — more actionable, matches what you'd type into a browser. Also clarified: CoreScope is hosted ON cnjmesh1, not cnjmesh3, so the two nodes affect it differently:
- **cnjmesh1 down** → `corescope.cnjmesh.me` itself is unreachable (fully down)
- **cnjmesh3 down** → `corescope.cnjmesh.me` stays reachable but its DATA goes stale, since Observer/KPR2 (physically on cnjmesh3) stop publishing — same symptom as the original 8-day CoreScope outage, different root cause

**Corrected SERVICES per node:**
- Node 1 (cnjmesh1): `malla.cnjmesh.me, meshview.cnjmesh.me, mqtt.cnjmesh.me, meshcorehub.cnjmesh.me, corescope.cnjmesh.me, LoRa APRS 2m`
- Node 2 (cnjmesh2): `malla2.cnjmesh.me`
- Node 3 (cnjmesh3): `MeshOmatic feed, LetsMesh feed, corescope.cnjmesh.me data going stale (Observer/KPR2 offline)`


### Full-domain SERVICES mapping — CONFIRMED DEPLOYED and tested on cnjmesh2 and cnjmesh3
Live, tested, and confirmed working in Discord (both #cnjmesh and the Meshtastic cross-post channel) as of 2026-07-21:

**cnjmesh2's peer-check config (reports on Node 1 and Node 3 going down):**
```
SERVICES=Node 1:malla.cnjmesh.me,meshview.cnjmesh.me,mqtt.cnjmesh.me,meshcorehub.cnjmesh.me,corescope.cnjmesh.me,LoRa APRS 2m;Node 3:MeshOmatic feed,LetsMesh feed,corescope.cnjmesh.me data going stale
```

**cnjmesh3's peer-check config (reports on Node 1 and Node 2 going down):**
```
SERVICES=Node 1:malla.cnjmesh.me,meshview.cnjmesh.me,mqtt.cnjmesh.me,meshcorehub.cnjmesh.me,corescope.cnjmesh.me,LoRa APRS 2m;Node 2:malla2.cnjmesh.me
```

**TO-DO when cnjmesh1's new board is back online:** deploy the equivalent config, reporting on Node 2 and Node 3 going down (cnjmesh1 doesn't need to report on itself):
```
SERVICES=Node 2:malla2.cnjmesh.me;Node 3:MeshOmatic feed,LetsMesh feed,corescope.cnjmesh.me data going stale
```
Plus the standard `CROSS_POST_WEBHOOK` and `CROSS_POST_LABELS=Node 2` (Node 3/MeshCore-only doesn't cross-post to the Meshtastic server, same logic as the other two hosts).


### SERVICES wording corrected again — "not reporting into" vs "down", CoreScope nuance refined
Charles flagged: MeshOmatic/LetsMesh themselves don't go down if cnjmesh3 does — only CNJ's OWN feed into them stops. Corrected wording to make that distinction clear. Also refined CoreScope: it pulls from 4 sources (local Observer/KPR2 via cnjmesh3, plus community-wide meshomatic/letsmesh-us/letsmesh-eu from OTHER people's observers). If cnjmesh3 goes down, only the `local` source stops — CoreScope's dashboard stays partially live with community data, just missing CNJ's own nodes' contribution. Not full staleness.

**Corrected Node 3 SERVICES text (needs deploying to cnjmesh2 and cnjmesh3's peer-check config, not yet done):**
```
Not reporting into MeshOmatic,Not reporting into LetsMesh,corescope.cnjmesh.me: your own Observer/KPR2 data stops updating (community data from others continues)
```
Note: semicolons separate different NODEs in the SERVICES format, commas separate items within one node's list — this replacement string uses commas only since it's all one node's (Node 3's) item list.


### Node 1 SERVICES corrected — "LoRa APRS 2m" was wrong, split into two real distinct services
Charles caught: "LoRa APRS 2m" doesn't exist — Graywolf (UV-5R M + Digirig) is standard AFSK APRS on the 2m band, no LoRa involved. LoRa APRS is a completely separate thing on the 70cm band (K2GIA-10, 433.775 MHz). Also found while fixing: there's a SECOND APRS-related service on cnjmesh1 not previously in the SERVICES list — the LoRa APRS Discord bridge (`/opt/lora-aprs-discord/lora-aprs-discord-bridge-v2.py`), which relays K2GIA-10's LoRa APRS messages to Discord, listens on cnjmesh1 UDP 1514, posts to `lora-aprs-70cm` channel in both the Meshtastic and MeshCore-NJ Discord servers.

**Corrected Node 1 SERVICES (needs deploying to cnjmesh2 and cnjmesh3, config-only, deliberately NOT test-fired to avoid more alert spam tonight):**
```
malla.cnjmesh.me,meshview.cnjmesh.me,mqtt.cnjmesh.me,meshcorehub.cnjmesh.me,corescope.cnjmesh.me,APRS 2m (Graywolf),LoRa APRS 70cm relay (K2GIA-10)
```


### Decision — container-level watchdog deferred, Pi-level peer-check is sufficient for now
Discussed building a local container-watchdog on cnjmesh1 (checking actual `docker ps` status per service — malla, meshview, meshcorehub, corescope — since peer-check only confirms the Pi itself responds to ping, not that every container is genuinely healthy). Decided to defer this — peer-check's existing Pi-level online/offline detection (with full service list in the alert) is good enough for now. Can build per-service container checks later if a specific service turns out to need closer monitoring.


### TO-DO tomorrow: rename "APRS 2m (Graywolf)" to "Graywolf APRS 2M" in peer-check SERVICES config
Charles's preferred naming. Update on cnjmesh2 and cnjmesh3's peer-check.service files (find/replace `APRS 2m (Graywolf)` -> `Graywolf APRS 2M`). Not urgent, cosmetic wording only.



---

## What Was Done — July 22-23, 2026 (cnjmesh1 new Pi 4 board bring-up — extended session)

### Context
Original cnjmesh1 board died from disk-full + hard power cycle mid-write (see prior session). New Pi 4 board physically installed, original SD card (last good backup) inserted and booted fine. This session covered bringing the new board fully back online — network, disk, WiFi link quality, and physical hardware reconnection.

### Root cause #1 — disk filled to 100%, twice
- **First occurrence:** `/var/lib/docker/containers/f0b305a3.../[id]-json.log` (the `mosquitto` container's Docker log file) had grown to **37GB** with zero log rotation ever configured. This had accumulated slowly over the ~5 months the container has existed, not a sudden spike. Cleared via `sudo truncate -s 0 [logfile]`, freeing 35GB.
- **Permanent fix applied:** `/etc/docker/daemon.json` created with `{"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}`, then `sudo systemctl restart docker`. This caps ALL containers' logs at 30MB total going forward — but **only applies to newly-created/recreated containers**, not retroactively to already-running ones. Mosquitto specifically was recreated via `cd /opt/stacks/mqtt && sudo docker compose up -d --force-recreate mosquitto` to pick up the new limit — confirmed via `docker inspect mosquitto --format '{{.HostConfig.LogConfig}}'` showing `max-file:3 max-size:10m`.
- **TO-DO:** the other 11 containers on cnjmesh1 still have unlimited logging (only Mosquitto was recreated so far). Should recreate the rest of the stacks (`docker compose up -d --force-recreate` per stack) to close this gap fleet-wide, not just for the one container that already caused a problem.
- **Separately found, NOT yet fixed:** Malla's `data_retention_hours` is commented out in `/opt/stacks/malla/config.yaml` (defaults to `0` = never delete). Malla's SQLite DB (`/var/lib/docker/volumes/mqtt_malla_data/_data/meshtastic_history.db`) is already 624MB and will grow forever uncapped. **TO-DO:** decide on a retention window (90 days / 2160 hours suggested but not agreed) and uncomment+set `data_retention_hours` in that config, then `docker compose restart` the malla stack. Deliberately deferred this session to focus on the more urgent disk-full issue.

### Root cause #2 — wrong WiFi network (5GHz instead of 2.4GHz)
- Router has two separate SSIDs: **`C4Somogyi-24`** (2.4GHz — what ALL Meshtastic/MeshCore hardware requires, since ESP32-based gear has no 5GHz support) and **`C4Somogyi`** (5GHz, no `-24` suffix — for phones/laptops/etc). This distinction was not previously documented in this context file for cnjmesh1 itself (was documented for CJG1/CJG2's mode issues but not that cnjmesh1's own WiFi must be on the `-24` network specifically).
- Mid-session, an assistant editing mistake (edited the wrong Netplan-generated NetworkManager profile — the one named after the 5GHz `C4Somogyi` AP) combined with a later revert left cnjmesh1 connected to the 5GHz network for a period. Confirmed and fixed via `sudo nmcli con up "C4Somogyi-24"` — the pre-existing correct 2.4GHz connection profile.
- **Lesson for future sessions:** always verify actual connected SSID with `nmcli -f active,ssid,chan dev wifi | grep yes` before assuming which Netplan/NetworkManager profile is "the" WiFi config — there can be multiple saved profiles (one per SSID) and NetworkManager doesn't always pick the intended one automatically after a profile edit/revert.

### Root cause #3 — static IP setup, and Raspberry Pi OS network stack notes
- cnjmesh1's SD card is running **Debian Trixie** (confirmed via `VERSION_CODENAME`), which is newer than Bookworm. Both Bookworm and Trixie have **fully replaced dhcpcd with NetworkManager** — `/etc/dhcpcd.conf` edits have zero effect on these OS versions (the file either doesn't exist or isn't read). On Trixie specifically, **Netplan is the intended source of truth**, rendering to NetworkManager underneath — but the actual live WiFi connection this session turned out to be a **native NetworkManager connection file** at `/etc/NetworkManager/system-connections/C4Somogyi-24.nmconnection`, NOT a Netplan-managed one (no matching Netplan YAML existed for the `-24` SSID, only for the unused 5GHz one).
- **Static IP correctly set via:** `sudo nmcli con mod "C4Somogyi-24" ipv4.addresses 10.0.0.181/24 ipv4.gateway 10.0.0.1 ipv4.dns "10.0.0.1,8.8.8.8" ipv4.method manual`, then `sudo nmcli con up "C4Somogyi-24"` to activate.
- Router's Xfinity gateway (10.0.0.1) Reserved IP for `cnjmesh1` (MAC `88:A2:9E:FE:3F:9A`) confirmed correctly pointing to `10.0.0.181` — same known "stuck reservation" Xfinity bug from the original board-swap session eventually resolved itself / accepted the new binding once the Pi claimed the static IP directly (exact mechanism unconfirmed, but end state is correct and stable across a reboot).
- **cnjmesh1 static IP `10.0.0.181` confirmed persistent across a full `sudo reboot`** — verified via `ip addr show wlan0` post-reboot.

### Root cause #4 — degraded WiFi link (retries/bitrate), largely resolved by a clean reboot
- Before reboot: `iwconfig wlan0` showed severe degradation — **~74,000-100,000+ Tx excessive retries, bitrate stuck at 5.5 Mb/s**, vs. cnjmesh3 (healthy reference) showing ~964 retries and 72.2 Mb/s on the same router/SSID.
- Tried and did NOT fix it alone: `sudo iwconfig wlan0 power off` (power management was already off by the time retries were still climbing — ruled out as the cause).
- Also found via `dmesg -T | grep wlan0`: cnjmesh1's wlan0 was cycling in/out of promiscuous mode every ~4 seconds continuously — cnjmesh3 showed ZERO such messages. Cause not fully identified (not caused by NetworkManager auto-scan or any running iwlist/nmcli scan process — checked and ruled out).
- **`sudo reboot` resolved the vast majority of the degradation**: post-reboot, bitrate recovered to 52 Mb/s, retries dropped to 319 (both now comparable to cnjmesh3's healthy numbers). Promiscuous mode toggling reduced in frequency (every ~9-10 sec instead of ~4 sec) but did not fully disappear — likely low-priority/cosmetic given performance is now healthy.
- **Kernel version mismatch found, not yet acted on:** cnjmesh1 is on kernel `6.12.62+rpt-rpi-v8`, cnjmesh3 is on `6.18.34+rpt-rpi-v8` (same `brcmfmac` driver, different kernel version). **TO-DO:** `sudo apt update && sudo apt full-upgrade` on cnjmesh1 to bring it in line with cnjmesh3 — may also resolve the residual promiscuous-mode toggling as a side effect.

### Root cause #5 (separate, unrelated) — HDMI hotplug interrupt storm from crash-cart monitor
- While troubleshooting the above with a physical crash-cart monitor/keyboard attached, `uptime` showed load average 19-21 (severe, on what should be a lightly-loaded Pi 4). `top` identified `irq/45-` and `irq/46-` kernel interrupt threads pinning two CPU cores near 100%.
- `cat /proc/interrupts | grep -E "45:|46:"` identified these as **`vc4 hdmi hpd connected` / `disconnected`** — i.e., the physical HDMI cable to the crash-cart monitor was rapidly flickering connect/disconnect (loose cable/connector), firing ~30,000 interrupts each in ~14 minutes.
- **Fix: unplugged the HDMI cable** (SSH access via `.181` was already working by this point, monitor no longer needed) — load average dropped from ~20 back to normal within a couple minutes. This was a real, separate contributor to session-long sluggishness (console responsiveness, apparent WiFi slowness, web service slowness) — worth remembering for any FUTURE crash-cart sessions: check `uptime` / `top` early if things feel unexpectedly slow, don't assume it's the network.

### Hardware reconnection — physical devices at permanent location
- Per the previously-documented USB device map, `/dev/ttyACM0` (Observer) and by extension KPR2 were already relocated to cnjmesh3 in an earlier session — correctly NOT reconnected to cnjmesh1.
- **KPR1 (MeshCore repeater) — retired, will NOT be reconnected to cnjmesh1 going forward.** This confirms/finalizes the "queued for cleanup" status noted in the prior board-failure session. `/dev/ttyUSB1` is now permanently free on cnjmesh1.
- **Reconnected to cnjmesh1 at its permanent location, via a powered USB 3.0 hub (blue port on the Pi):**
  - Digirig (Graywolf APRS PTT)
  - Client 1 / KPC1 (MeshCore companion) — note: same device previously flagged as having a serial-flapping issue, replacement still planned but not yet done
  - K2GIA-10 (LoRa APRS node, separate WiFi-based board, not directly USB-dependent on the Pi but was included in the same physical relocation/hub setup)
- **TO-DO:** run `dmesg | tail -30` and `ls -l /dev/ttyUSB* /dev/ttyACM*` after next boot at the permanent location to confirm all three devices enumerate on their expected ports through the hub (not yet verified as of end of this session — hub was just connected).
- **TO-DO — KPR1 cleanup, still not done (carried over from prior session):** mark retired in this repo's context file (this entry now serves that purpose), flip to ARCHIVED in the `whorepeated` tool, mark retired in CoreScope/MeshCore Hub node lists if applicable.

### Session process notes (for future assistant sessions)
- This was a very long, high-friction session (12+ hours) with significant back-and-forth, including real mistakes (editing the wrong WiFi profile, premature "this is fixed" claims that weren't fully verified, losing track of an already-identified WiFi retry problem while chasing IP/SSID confusion). Worth reading this whole entry carefully before assuming state, rather than re-verifying from scratch.
- Charles was working from a crash-cart (monitor+keyboard physically on the Pi, no copy/paste, no mouse initially) for a large portion of this session — commands given during that period were kept to single-line/no-typing-heavy where possible; this constraint should be checked for at the start of future sessions if Charles mentions "crash cart" again.
- Standing rule reinforced this session: **before giving ANY step-by-step command, be explicit about which node it runs on** ("Run this on cnjmesh1" / "Run this on cnjmesh2", etc.) — Charles has multiple SSH/PuTTY sessions open simultaneously across cnjmesh1/2/3 and ambiguity here caused real confusion.


### Late-session addendum — July 23, 2026 (post-reboot hardware reconnect + verification)

- **Digirig USB path changed after hub reconnection:** was `/dev/ttyUSB2`, now `/dev/ttyUSB1` (confirmed via `udevadm info` serial match `beb31e2f...`). **Graywolf's PTT config in `/var/lib/graywolf/graywolf.db` (`ptt_configs` table) updated to match** via direct SQL UPDATE. `graywolf.service` restarted successfully on the corrected path — confirmed active/running.
- **Client 1/KPC1 also shifted path:** was `/dev/ttyUSB3`, now `/dev/ttyUSB0` (CP2102, serial `0001`).
- **K2GIA-10 (LoRa APRS board) enumerates as `/dev/ttyACM0`** (CH340-family USB-serial chip, distinct from the CP2102 devices) — not previously documented which device path it uses.
- All three devices now connect to cnjmesh1 via a **powered USB 3.0 hub**, plugged into one of the Pi's blue (USB 3.0) ports. KPR1 intentionally NOT reconnected — confirmed retired, `/dev/ttyUSB1`'s old KPR1 slot is now free/reused by Digirig.
- **cnjmesh1 ↔ cnjmesh3 MQTT dependency verified working post-reboot:** `meshcore-packet-capture` on cnjmesh3 actively capturing live packets with `MQTT: 3/3` (all three configured brokers, including local `10.0.0.181:1883`, succeeding). `meshcore-mqtt-bridge` on cnjmesh3 showed occasional brief disconnect/reconnect cycles (with a `Timeout queueing message` warning) but self-recovers each time — not a hard failure, flagged as worth monitoring if it persists, not urgent.
- **Post-reboot load average ran persistently high (9-11) for at least 30+ min** — NOT the HDMI interrupt issue (that was already resolved/unplugged by this point). Identified as legitimate backlog processing: `mqtt_filter.py` (meshtastic-oktomqtt-filter), Meshview's `startdb.py`, `mosquitto`, and `dockerd` all showing real, sustained CPU use post-restart, RAM nearly exhausted (down to ~37MB free, 1GB+ in swap) on this Pi's 1.8GB total RAM. All Docker containers remained "Up"/healthy throughout — nothing crashed or looped. Not fully resolved/explained by end of session — **TO-DO:** check `uptime`/`top` again fresh next session; if load has NOT settled down after a full period of normal operation (not just tens of minutes post-reboot), investigate `mqtt_filter.py` specifically for a possible backlog/stuck-reprocessing issue given it was pegged at 50-64% CPU continuously.
- **Backup run and pulled successfully** at end of session: `cnjmesh1-backup-2026-07-23_2112.tar.gz` (57MB), via `sudo ./scripts/cnjmesh1-backup.sh` (note: script needs `sudo` to read root-owned `graywolf.db` — running without sudo fails partway through with a permission error, worth fixing the script itself to check for/require sudo upfront rather than failing mid-run). Pulled to laptop via `pull-cnjmesh1-backup.ps1`, saved to OneDrive, auto-syncing.

### Confirmed working end-of-session state (July 23, 2026, ~21:15 EDT)
- cnjmesh1: static IP `10.0.0.181` on `C4Somogyi-24` (2.4GHz), survived a full reboot, WiFi link healthy (52 Mb/s, low retries), disk 36GB free with Mosquitto's log capped permanently, all 12 Docker containers up.
- All USB hardware (Digirig, Client 1, K2GIA-10) reconnected via hub, correctly identified, Graywolf verified working on corrected path.
- cnjmesh1 ↔ cnjmesh3 data flow (MQTT broker dependency) confirmed live and working.
- Fresh backup taken and safely pulled off-Pi.
- **Open items carried forward:** Malla retention not yet set (624MB, growing forever), only Mosquitto (not the other 11 containers) has picked up the new Docker log-rotation limit, cnjmesh1 kernel behind cnjmesh3's, elevated post-reboot load average not fully explained, backup script should require sudo upfront rather than failing partway through.


### TO-DO — expanded fleet health check (proposed July 23, 2026, not yet built)
Idea raised after tonight's session, where several real problems (RAM/swap exhaustion, elevated load average, unbounded container logs) went completely unmonitored until they caused visible symptoms. Proposed additions, either as new checks in `disk-temp-watchdog` or a new dedicated `health-check` watchdog (not yet decided which):
- Load average (1/5/15 min) — not currently monitored at all; tonight's HDMI interrupt storm and post-reboot backlog both would have been caught early by this.
- RAM/swap usage % — tonight's Malla/Meshview slowness traced directly to swap exhaustion (zram at 1.1GB/1.8GB used); not currently monitored.
- Docker container status — count of expected vs. actually running/healthy containers per host; current watchdogs only check Pi-level reachability (peer-check), not per-service health.
- Largest Docker container log file size — early-warning version of tonight's 37GB Mosquitto log-fill incident; would alert well before disk actually fills, rather than after.
Existing disk-temp-watchdog already covers: disk %, CPU temp, undervoltage. Not yet scoped: alert thresholds for the new checks, whether to consolidate into disk-temp-watchdog or build separate, deployment to all 3 hosts (cnjmesh1/2/3).

### Swap mechanism change note — Trixie uses zram (rpi-swap), not dphys-swapfile
Confirmed both cnjmesh1 and cnjmesh3 are running Debian Trixie, which replaces the old `dphys-swapfile` swap mechanism entirely with `rpi-swap` (zram-based). `/etc/dphys-swapfile` does not exist on this OS version — any old swap-size tuning from a prior OS version would not carry forward, not because of the board swap specifically, but because the underlying swap mechanism itself changed with the OS. Current config lives at `/etc/rpi/swap.conf` (all defaults) with overrides in `/etc/rpi/swap.conf.d/`. **cnjmesh1's zram swap increased from 1.8GB to 3GB tonight** via `/etc/rpi/swap.conf.d/override.conf` (`[Zram]` / `FixedSizeMiB=3072`) — done in response to observed RAM/swap pressure (52MB RAM free, 1.1GB/1.8GB swap used) coinciding with slow response times on malla.cnjmesh.me and meshview.cnjmesh.me. **Important: applying an `rpi-swap` config change required a full reboot to take effect** — `sudo systemctl restart rpi-swap` alone triggered a reboot (not a graceful in-place restart), which is worth expecting/warning about before running this again on cnjmesh2 or cnjmesh3 if the same tuning is ever needed there.


### TO-DO — cnjmesh1 OS/kernel upgrade (not urgent, whenever convenient)
cnjmesh1 is on an older Trixie image (kernel `6.12.62+rpt-rpi-v8`) than cnjmesh3 (`6.18.34+rpt-rpi-v8`). This is a software/SD-card-image age difference only — NOT a hardware issue, and unrelated to the new Pi 4 board purchase. Everything is working fine as-is; this is purely a "bring it current" cleanup task, no ticking clock. To do whenever convenient:
```
sudo apt update && sudo apt full-upgrade
sudo reboot
```


### TO-DO — check Malla for a known XSS vulnerability (CVE-2026-43980), upgrade if affected
Found while checking upstream repos for updates (July 23, 2026 session). **Malla has a real, moderate-severity (CVSS 6.3) stored XSS vulnerability**: node names (long_name/short_name) received via MQTT are stored without sanitization and rendered unescaped into the DOM. Any participant on a public Meshtastic MQTT broker (which CNJ Mesh's Malla instance pulls from) could set a malicious node name containing JavaScript that executes in every dashboard visitor's browser — phishing overlays, redirects, arbitrary script injection, dashboard DoS. Published May 30, 2026 (GHSA-ch57-39q2-4crm / CVE-2026-43980). Affected: all commits up through `c8a2ed3ce9365c58fd357f66d7fc1b16bbf9b43c`. **Patched**: commits from `4086e2b5f61615a813b70b25bc76095083552135` onward.

**To check if currently affected, run on cnjmesh1:**
```
docker inspect mqtt-malla-web-1 --format '{{.Created}}'
docker inspect mqtt-malla-web-1 --format '{{.Config.Image}}'
```
If the container was created/pulled before May 30, 2026, it's very likely still running the vulnerable version. Fix: pull the patched image and recreate — `cd /opt/stacks/mqtt && sudo docker compose pull && sudo docker compose up -d` (adjust stack path/command if Malla lives in a different compose project — not yet confirmed which compose file governs `mqtt-malla-web-1` specifically, worth checking with `docker inspect mqtt-malla-web-1 --format '{{.Config.Labels}}'` first, same approach used earlier tonight to locate Mosquitto's actual compose file).

Also checked Meshview (pablorevilla-meshtastic/meshview) for comparison — no security advisories or notable version-gap concerns found as of this session.


### IMPORTANT — peer-check watchdog DISABLED tonight (July 23, 2026, ~22:20 EDT) — must re-enable next session
Stopped on BOTH cnjmesh2 and cnjmesh3 (`sudo systemctl stop peer-check.timer` + `sudo systemctl stop peer-check.service` on each) to stop Discord alert spam while cnjmesh1's recurring high-load issue (see below) was still unresolved late at night. **Config untouched, nothing lost — just paused.** To re-enable on each host: `sudo systemctl start peer-check.timer`.

### TO-DO — cnjmesh1 recurring high load average, cause NOT YET confirmed (carried over, needs fresh investigation)
Pattern seen twice tonight: shortly after a reboot, cnjmesh1 develops sustained load average in the 9-12 range along with severe (100-600ms) but NON-lossy ping latency to/from cnjmesh2 and cnjmesh3 (0% packet loss, just very slow). Two different reboots produced this same pattern.
- **First occurrence** was conclusively explained: a flaky crash-cart HDMI cable was firing ~30,000 `vc4 hdmi hpd connected/disconnected` interrupts in ~14 minutes, pinning 2 CPU cores. Fixed by unplugging the monitor.
- **Second occurrence (end of this session)**, load was elevated again (10.20) after the swap-size-change reboot, monitor status at the time uncertain (Charles believes it may still have been connected or just unplugged) — did NOT get to confirm whether this was the same HDMI cause recurring, or a different cause (e.g. legitimate post-reboot Docker/MQTT backlog processing, same pattern separately observed and explained earlier in the session with `mqtt_filter.py`/`meshview startdb.py` pegged at high CPU). Ran out of session time before running `top`/`cat /proc/interrupts` to check — **this is the first thing to check next session**:
```
top -bn1 | head -12
cat /proc/interrupts | grep -E "45:|46:"
```
If interrupts 45/46 are climbing again, it's the monitor (confirm physically disconnected, not just powered off — check the actual HDMI cable). If not, look at `mqtt_filter.py`/`startdb.py`/`mosquitto` CPU usage per the earlier session pattern — may just be normal backlog catch-up that takes longer than expected to settle, worth timing how long it actually takes to normalize on a clean, monitor-free boot.


### Philosophy note — keep monitoring simple, don't over-engineer (Charles, July 23, 2026)
Explicit guidance: peer-check (ping-based) stays as-is, no new parallel service-level check system. The "expanded fleet health check" TO-DO above (load avg, RAM/swap, container status, log size) and any service-vs-ping distinction should stay LOW PRIORITY / someday-maybe, not something to actively build unless a specific real missed outage justifies it later. Goal is these environments working reliably enough that Charles can focus on actual radio contacts, not on tooling. Default to the simplest fix that closes a real, already-experienced problem — avoid speculative monitoring architecture.


### IMPORTANT correction — do NOT recommend a hardware/RAM upgrade for cnjmesh1
Charles explicitly corrected this assumption: cnjmesh1 is a 2GB Pi 4 (confirmed via `free -h` showing ~1.8Gi total usable). The OLD board (before it died) ran this exact same workload/service stack fine on the same 2GB spec for months. So the RAM/swap pressure seen the night of the new-board bring-up (July 22-23, 2026) is NOT a hardware capacity ceiling — something changed or is temporarily elevated (likely post-reboot backlog catch-up on Malla/Meshview/MQTT after being down for days), not an inherent under-spec. **Do not suggest upgrading to a 4GB/8GB Pi as a fix** — Charles has explicitly ruled this out as unnecessary spending ($150-200) for a workload that's proven itself fine on this exact hardware before. If RAM/swap pressure persists after a full quiet settling period post-reboot, investigate for a specific bug/leak/backlog cause in one of the containers (Malla, Meshview, mqtt_filter.py) rather than defaulting to "needs more RAM."


### General maintenance practice — regular apt upgrades on all 3 Pis (not just cnjmesh1)
Established July 23, 2026, after tonight's session revealed cnjmesh1 had drifted out of sync with the current OS networking model (dhcpcd → NetworkManager/Netplan/rpi-swap changes) simply from not being updated in a while, causing real confusion mid-session. Going forward: run on each Pi (cnjmesh1, cnjmesh2, cnjmesh3) roughly monthly, not just as a one-off fix:
```
sudo apt update && sudo apt full-upgrade
sudo reboot
```
Nothing urgent/bleeding-edge needed — just avoid letting any one Pi's OS drift far out of date relative to the others, since that mismatch itself caused real troubleshooting confusion tonight (assuming dhcpcd config would work, when it had been silently replaced).

### IMPORTANT — Mosquitto log-fill theory challenged by Charles, needs real investigation (not settled)
Charles pushed back on the "slow accumulation over ~5 months" explanation given earlier tonight for the 37GB Mosquitto log: **he reports the disk filled to 100% again overnight** after being cleared, which directly contradicts a slow-trickle theory. The only actual growth-rate measurement taken tonight (~2KB per 30 seconds, via `ls -lh` before/after a `sleep 30`) would take many days to refill 30GB, not overnight — so either that 30-second sample happened to catch a quiet moment while something else spikes intermittently, or the real cause of rapid refill is something other than steady Mosquitto logging (e.g., a specific error condition, a reconnect storm, some other container spiking, or a burst of legitimate high-volume MQTT traffic). **Do not treat "slow accumulation, one-time historical buildup" as a settled conclusion** — this needs real investigation next session: monitor disk usage and `docker logs`/log file sizes across all containers over a longer continuous window (not a single 30-second spot check) to actually catch what's growing and how fast, especially watching for anything correlating with a spike rather than assuming steady growth.
