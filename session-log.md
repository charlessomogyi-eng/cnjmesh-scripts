# CNJ Mesh — Session Log (full narrative history)
**For AI assistants:** This is the full, append-only narrative history — every session, in order, unedited. It is long and NOT meant to be re-read in full each session. Fetch `todos.md` and `cnjmesh1-operations.md` first; only pull this file when you need backstory on WHY something is configured a certain way, or the detailed story behind an open to-do. New entries always get appended to the end — never edit or delete past entries.

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


### TO-DO — stale Fing Agent alerting on old (dead) cnjmesh1 board, needs cleanup
Fing monitoring app is generating repeated "Fing Agent 'Home' is offline" alerts for `AGENT-88:A2:9E:3E:0E:7E` — this is the OLD, now-dead cnjmesh1 board's MAC address, not the new board's. Fing was installed/activated on the original board before it died; MAC addresses are hardware-specific (burned into the NIC), so the replacement Pi 4 has a genuinely different MAC (`88:a2:9e:fe:3f:9a`, confirmed on wlan0) and was never registered as a Fing agent. The alert is technically correct (that specific old hardware really is gone), just stale/no-longer-relevant.
**Fix (low priority, whenever convenient):**
1. In the Fing app/dashboard, delete or deactivate the old agent entry (`AGENT-88:A2:9E:3E:0E:7E`) to stop the alerts.
2. If Fing monitoring on cnjmesh1 is still wanted going forward, install/activate a fresh Fing Agent on the new board — it will register under its current real MAC automatically.
Confirmed: cnjmesh1 (new board) has no wired network connection, WiFi-only — so `eth0` MAC lookup isn't relevant here, the mismatch is purely old-hardware-vs-new-hardware, not a misconfiguration.


### RECURRING ISSUE — cnjmesh1 WiFi silently "stuck" despite looking healthy (2 nights in a row, July 23-24, 2026)
**Pattern:** WiFi interface (`wlan0`) reports normal/healthy stats (`iwconfig` shows good bitrate, reasonable signal, TX packet counter actively incrementing) and the router's own device list shows cnjmesh1 as online with a correct ARP entry (confirmed on a separate device on the network too) — yet ALL actual traffic fails completely, including ping to the router's own gateway one hop away. Not a DNS issue, not a routing table issue, not an IP addressing issue, not Tailscale (was ruled out and disabled July 24 morning), not a Cloudflare/tunnel-specific issue (general internet, e.g. `ping 1.1.1.1`, fails too). Every individual diagnostic layer looks correct in isolation; only actual packet flow is broken.

**Occurrence 1 (night of July 22-23):** Manifested as severe but non-zero packet loss/latency (100-600ms, degraded but partially working) plus 74k-100k+ WiFi retry counts and a bitrate collapsed to 5.5 Mb/s. **Fixed by:** full `sudo reboot`.

**Occurrence 2 (morning of July 24, before work):** Manifested as complete/total traffic failure (0% of pings getting through at all) despite `iwconfig` showing a genuinely healthy link (72.2 Mb/s, -58dBm, reasonable retry count for uptime). Diagnosed Tailscale as a red herring — coincidentally also broken (couldn't reach its own coordination server) but not the actual cause once ruled out via DNS/route checks. **Fixed by:** a lighter-weight fix this time — `sudo nmcli con down "C4Somogyi-24" && sudo nmcli con up "C4Somogyi-24"` (no full reboot needed) — restored connectivity within seconds.

**Not yet identified:** the actual root cause. Both occurrences were "fixed" by forcing NetworkManager to fully renegotiate the WiFi association (either via full reboot, or via down/up), which clears whatever state is broken, but doesn't explain WHY it breaks in the first place. Worth considering for next investigation:
- Whether this is specific to THIS Pi 4 board's WiFi chip/antenna (hardware quality issue with the replacement unit specifically) vs. a software/driver quirk affecting any Pi similarly positioned
- Whether it correlates with anything time-based (both occurrences happened several hours after a prior WiFi state change — first after initial setup, second ~10 hours after the swap-config-triggered reboot) — could suggest a slow-building driver/firmware issue that accumulates over hours rather than being present from boot
- Whether cnjmesh2/cnjmesh3 have ever shown similar symptoms (not confirmed either way — worth asking/checking historically)
- Consider building a lightweight recurring check (NOT over-engineered — see the "keep monitoring simple" philosophy note above) that specifically tests actual gateway reachability (not just interface stats) and can alert/auto-recover via the same `nmcli con down/up` fix, if this keeps recurring.

**Also cleaned up as part of this investigation:** Tailscale (`tailscaled`) was found running on cnjmesh1, in a broken/non-functional state (couldn't reach its own coordination server). Charles confirmed it was likely installed at some point for casual remote SSH access, never fully vetted/used, and no other services depend on it. **Stopped AND disabled permanently** (`sudo systemctl stop tailscaled && sudo systemctl disable tailscaled`) — will not start on future reboots.


### Update to Fing Agent TO-DO (July 24, 2026 morning) — timing suggests it may be a LIVE process, not just stale/dead hardware
A second "back online" alert for the same old MAC (`AGENT-88:A2:9E:3E:0E:7E`) fired at 8:48 AM — right around the same time cnjmesh1's WiFi connectivity was restored (see recurring WiFi issue entry above, fixed ~8:44 AM via `nmcli con down/up`). Charles flagged the timing as suspicious, and it's a fair point: this could mean the Fing Agent SOFTWARE is still actually installed and running as a live process on the NEW board (since it's the same reused SD card), just still reporting under the OLD registered agent ID/identity string it generated back when first set up on the original dead hardware — rather than this being purely a stale/coincidental alert about hardware that's truly gone. Not yet confirmed either way. **To check when picking this up:**
```
ps aux | grep -i fing
sudo systemctl list-units | grep -i fing
```
If Fing Agent IS found running live on cnjmesh1, the fix is different than previously assumed: don't just delete the old cloud-side agent entry — also may need to re-register/reset the local agent's identity so it reports under a fresh ID matching the new hardware, not just clean up the dashboard side.

### RESOLVED: Fing Agent confirmed running LIVE on cnjmesh1 (July 25-26 health check)
Full system health check (temp, RAM, swap, disk, USB, containers, systemd services) came back clean across the board — 43.8°C, throttled=0x0, disk 39% used, all 12 docker containers + Meshview (systemd, not docker) all up since last boot with no gaps. **`fingagent.bin` was found actively running as PID 100151**, confirming the suspicion above: the Fing Agent software is genuinely live on the new board, not a stale/coincidental cloud alert. Per the note above, cleanup needs to both stop/remove the live process AND handle the cloud-side old-MAC entry, not just one or the other. Not yet actioned — still open.

### K2GIA (2m Graywolf, whip antenna) range test — NEGATIVE result
Charles moved the UV-5R M off the roof dual-band antenna to a small whip (documented tradeoff — roof feed is dedicated to the Icom 2730) and sent a CQ test at 4:57 PM ET ("test after moving station to a small whip. SB NJ. Any copy?"). Verified via aprs.fi raw packets for K2GIA: last packet before/at the antenna swap was a routine beacon at 16:31:47 EDT; the CQ never appears anywhere in aprs.fi's log. **Nothing heard it** — no digipeater, no iGate. Consistent with expected whip vs. roof-antenna performance difference.

### K2GIA-10 (LoRa APRS, roof antenna) range test — INCONCLUSIVE (not negative)
K2GIA-10 relocated to the roof dual-band antenna (powered/data via cnjmesh1, /dev/ttyACM0). Sent a CQ via aprs-tnc-web (port 8085) — app confirmed "CQ Sent Successfully." Checked aprs.fi through 22:37 EDT same night: only routine 15-min position beacons appear, all via TCPIP*/qAC (internet path), no RF-digipeated packets, and the CQ message itself never appears (expected — K2GIA-10's firmware doesn't self-gate its own outgoing messages, a previously-known limitation, not new). **Result is inconclusive, not a negative**, because self-confirmation isn't possible without either (a) another station's iGate hearing it, or (b) the second RX-only board (in transit, LILYGO-83352) being installed. Suggested next step, not yet done: coordinate a live test window via CNJ Mesh/MeshCore NJ Discord and ask a nearby operator to actively watch their iGate/aprs.fi during the test, rather than passively hoping a random iGate catches it.

### Meshview coverage regression — see todos.md for full writeup and next steps
Confirmed real (not imagined): used to see NYC/distant nodes regularly, now rarely. Confirmed via comparison with a neighboring MTX1 Meshview instance that the missing distant nodes are RF-connected on his map (not MQTT-bridged), meaning the gap is on the RF-hearing side, not a Meshview bridging config issue. CJG1/CJG2 WiFi itself confirmed solid (past "flapping" concern was phone↔app only, not node↔WiFi — corrected assumption from earlier sessions). **Same night, independently, Malla's Gateway Diversity metric was observed to have dropped from "much higher" historically to 1** — strong corroborating signal that a mosquitto bridge or upstream broker (not a local feeder) is the actual cause, since a bridge dying would explain losing "everyone else's" gateways while your own local one survives as the "1." Full details and the exact diagnostic commands to run next are in todos.md. Also decided: KPN6 (roof node) MQTT stays disabled per Charles's preference for all-RF operation, even though enabling it (uplink only) would likely help — this is a deliberate tradeoff, not an oversight.

### USPS/LilyGO shipment (order LILYGO-83352, tracking 9214490422577101899358) — still stalled
"Package Acceptance Pending" in Los Angeles since July 16, no movement for 8+ days as of July 24. Filed a USPS Missing Mail Search request — **ID: MRC 26 2611 5622**. LilyGO support email drafted (not yet confirmed sent). This shipment likely contains the second RX-only ESP32 LoRa board needed to resolve K2GIA-10's self-gating limitation above.

### Misc this session
- Claude Code installed and working on Charles's Windows laptop (v2.1.219, C:\Users\charl\.local\bin\claude.exe, PATH configured, logged in).
- Graywolf API auth mechanics documented: session cookie `graywolf_session`, login via `POST /api/auth/login` with JSON `{"username","password"}` (meshdev/large4cats). Packet log ring buffer is capped at ~1000 packets / 30 min — not useful for anything older than that; use aprs.fi for historical checks instead.


---

### Session — July 25, 2026 (evening/overnight) — APRS hub outage root-caused, Graywolf put behind Cloudflare Access, MeshCore audit
Long session. Three real outcomes.

**1. The "dead antenna" mystery was a dead USB hub.** Days of K2GIA looking deaf (69 RX packets in 37h, nothing heard on TX, "no signal" from the whip) turned out NOT to be the antenna. `lsusb` on cnjmesh1 showed only hubs, no Digirig; `dmesg` had zero USB events for it this boot — the Digirig had fallen off the bus entirely, behind a powered USB hub that stopped driving its downstream ports (failed/unplugged brick behavior). Moving the Digirig to a direct Pi USB port brought the whole bus back at once (CP2102N on ttyUSB0 = Digirig PTT, C-Media USB audio, plus a second CP210x on ttyUSB2). Confirmed the whip was working all along: the aprs.fi log showed K2GIA gating through KB2EAR-13 every 30 min all day until it hard-stopped at exactly 16:31:47 on 7-24 — the moment the hub died. Clean cliff = interface drop, not a fading antenna. Lesson logged: check the USB/interface chain before theorizing about RF.

**2. Graywolf PTT device-pinning — dead end (see operations note).** Tried to pin the Digirig to a stable `/dev/serial/by-id/...` path so a future USB reshuffle can't renumber PTT (it had renumbered ttyUSB0->ttyUSB1). The by-id symlink exists and is permanent, but the PTT/serial device field could not be found in the Graywolf 0.13.13 web UI (not in Channels edit, not in Audio Devices edit — config is in the SQLite DB, set via UI only). Parked; revisit after confirming the exact UI page via the Graywolf Discord/handbook. No custom udev rule was left behind.

**3. Graywolf now behind Cloudflare Access.** Added `graywolf.cnjmesh.me` to the cloudflared ingress (-> localhost:8082) and a DNS route, then created a Zero Trust self-hosted Access app with an email + PIN policy (same MFA model as the existing Malla app, ~24h session). Graywolf is TX-capable, so this closes the "open to the internet" hole — anyone hitting the hostname now gets the Cloudflare login wall first. Gotcha encountered: typing an address into the Private IP field triggered a stuck `use_clientless_isolation_app_launcher_url` error (known Cloudflare bug) — fixed by recreating the app cleanly via the "Public DNS" path and never touching the Private IP field. Note: activating the app required (re-)confirming the Zero Trust Free plan ($0).

**4. Confirmed-done housekeeping:** the ACK/REJ Discord filter TODO is DONE (three filter layers already present in graywolf-discord-bridge.py at message-match and SQL levels).

**5. MeshCore audit (done via another AI) reviewed.** Correct root cause on the meshcore-mqtt-bridge queue-fill (broker restart severed it, no auto-recover). Feedback given: the real finding is the bridge can't self-heal after a broker restart — needs a restart policy check, reconnect-logic check, and ideally a watchdog (same pattern as CoreScope/graywolf). Also flagged a hardware-mapping conflict: audit says ttyACM0=Heltec V4 observer / ttyACM1=RAK4631, standing notes say the reverse — verify on cnjmesh3. Both captured in todos.

**Also discussed (no action):** ISS-via-APRS (possible but wants a directional/Arrow antenna, not the fixed setup); antenna-contention planning for getting the Icom back on the roof (one mast at the eave can't cleanly hold 2x 2m + LoRa — the two 2m radios can't share an antenna since they're same-band; leaning toward UV-5R/APRS on the good antenna since it's the always-on job and the Icom is occasional).


---

### July 26, 2026 — meshcore-mqtt-bridge watchdog DEPLOYED (urgent hardening item, DONE)
Closed the highest-priority hardening item from the July 25/26 audit. The bridge (`meshcore-mqtt:local` on cnjmesh3) has `restart: unless-stopped` but that only covers a crash — the real failure is it stays running while going deaf after a Mosquitto restart (fills its 1000-msg queue, never reconnects), silently killing the MeshCore Hub feed on any routine cnjmesh1 maintenance. Confirmed the container config has NO reconnect/keepalive env var (`MQTT_BROKER=10.0.0.181`, `MQTT_PORT=1883`, QOS 1, retain true — nothing to flip), so a watchdog was the correct fix.

Deployed on cnjmesh3:
- `/opt/meshcore-mqtt-watchdog/watchdog.sh` — greps `docker logs --tail 40 meshcore-mqtt-bridge` for the unhealthy signature (last MQTT status line = `MQTT: stopped`, and/or `Queue: 1000/1000` with no later `MQTT: connected`) and issues `docker restart`. Healthy line format confirmed: `MQTT: connected | Queue: 0/1000 | Dropped: 0`. Optional Discord alert via `DISCORD_WEBHOOK` var (currently empty = silent auto-heal).
- `meshcore-mqtt-watchdog.service` (oneshot) + `.timer` (OnBootSec=2min, OnUnitActiveSec=3min) — runs every 3 min, enabled at boot. Verified `active (running)` with a real NEXT trigger and a first successful fire; dry-run correctly reported healthy.

Follow-ups (optional, not blocking): (1) paste the #cnjmesh webhook into the script for restart pings; (2) end-to-end proof by deliberately restarting Mosquitto on cnjmesh1 and watching the watchdog heal the bridge within 3 min (same validation approach used for the graywolf watchdog).


---

### July 26, 2026 — CoreScope "no packets from meshomatic in 64h" — FIXED (dead template sources were starving the ingestor)
The persistent CoreScope banner ("No packets from meshomatic in 3841 min" ≈ 64 h) was NOT a meshomatic-side outage. Root cause: two leftover template mqttSources in `/home/somog/meshcore-data/config.json` — `lincomatic` (ssl://mqtt.lincomatic.com:8883, not Charles's server) and `wsmqtt` (wss://wsmqtt.example.com/mqtt, a literal RFC-2606 placeholder domain with `your-username`/`your-password` creds) — were jamming the ingestor's connection loop with endless 30-second connect timeouts and retries (attempt #6000+). This starved the real `meshomatic` source of a clean connection slot. (These were previously logged as "harmless/cosmetic log spam" — that was WRONG; they were actively degrading ingest.)

Fix: removed both by name via a backup-first Python edit, then `docker restart corescope`. Result: `MQTT [meshomatic] connected ... attempt #1` in ~1 second, `Running — 2 MQTT source(s) connected`, and live status packets flooding in (incl. "CNJ Mesh Observer (EWR)" — Charles's own observer echoing back through the meshomatic cloud). Remaining sources: `local` + `meshomatic`. The banner clears on its own as fresh packets age in.

MeshOmatic MQTT access confirmed (screenshots): user `user_somog`, WebSocket host `mqtt.meshomatic.net:443` topic `meshcore/#`, TCP direct `us-east.meshomatic.net:31883`. **Access level is "Limited": max 2 simultaneous connections per account, and SNR/RSSI signal fields are filtered** unless you request Full Access from an admin. (Another reason the dead sources hurt — they were burning connection slots against that cap.)

Follow-up (see todos): immediately after the restart the Observers page showed the `local` source disconnected and the CNJ Mesh Observer row reading "6d ago / 0/hr" — but that snapshot was ~3 min post-restart, so likely restart-settling artifacts, not a real local-path outage. Needs a recheck after 10+ min of clean uptime before treating as real. Also captured a monitor idea: a per-source freshness watchdog so a stale CoreScope source pings Discord instead of relying on eyeballing the UI (this whole thing went unnoticed for 64 h precisely because nothing alerted).


---

### July 26, 2026 (evening quick-wins) — peer-check re-enabled + 1-hour down-delay
- **Re-enabled peer-check on cnjmesh2 and cnjmesh3** — both timers had been `inactive (dead) since July 23 22:24` (stopped during the cnjmesh1 WiFi troubleshooting and never restarted). So there was NO peer monitoring on 2/3 for ~2.5 days. `sudo systemctl start peer-check.timer` on each; both now active (waiting) with next-fire confirmed.
- **Raised down-alert delay to 1 hour** — added `Environment="DOWN_THRESHOLD=12"` to the peer-check.service on cnjmesh2 and cnjmesh3 (12 checks × 5-min interval = 60 min down before alerting). Purpose: no alert for planned reboots or carrying a Pi between rooms. Default was 3 (15 min). Committed service template updated to document this. Tradeoff accepted: a genuinely dead Pi also won't alert for an hour.
- **Confirmed cnjmesh1 does NOT run peer-check** — the "deploy to cnjmesh1 too" step from an earlier session was never done. cnjmesh1-down is still detected (both peers watch it + UptimeRobot), but cnjmesh2/3 each have only one watcher instead of two. Logged as a todo to close the redundancy gap (deploy on cnjmesh1 with DOWN_THRESHOLD=12), not urgent.

**Design confirmed (answering Charles's questions):** peer-check is edge-triggered — it sends exactly ONE down alert per outage (when the debounce threshold is crossed) and ONE "back online" on recovery; it does NOT re-alert every interval while down. It also lists affected services in the down alert and cross-posts Node 1/2 alerts to the Meshtastic community server. Note surfaced: there is NO periodic "still down" reminder — if the single down alert is missed, nothing repeats it. A daily still-down reminder could be added if wanted (not built).

---

### July 26, 2026 (night) — cnjmesh3 ACM device pinning — CLOSED (urgent hardening item)
Resolved the hardware-mapping conflict first: dmesg evidence from the original relocation session (confirmed in this repo) already had it right — `/dev/ttyACM0` = Observer (RAK4631/WisMesh Pocket, serial `06308D8BE14915FD`), `/dev/ttyACM1` = KPR2 (Heltec V4, serial `E8F60AC9DEB4`). The July 25 audit that flagged a conflict had it backwards; it was a secondhand review, not a fresh device check. Confirmed live via `udevadm info` on cnjmesh3 — matches standing notes exactly.

Discovered the OS had already auto-generated stable `/dev/serial/by-id/` symlinks for both boards (standard udev behavior for USB serial devices with unique serial numbers) — no custom udev rule needed. Recreated both containers to bind to those by-id paths instead of the raw ACM numbers, container-internal path kept identical (`/dev/ttyACM0`/`/dev/ttyACM1`) so no TOML config or env var changes were needed:

- `meshcore-packet-capture`: `--device /dev/serial/by-id/usb-RAKwireless_WisCore_RAK4631_Board_06308D8BE14915FD-if00:/dev/ttyACM0`
- `meshcore-mqtt-bridge`: `--device /dev/serial/by-id/usb-Espressif_Systems_heltec_wifi_lora_32_v4__16_MB_FLASH__2_MB_PSRAM__E8F60AC9DEB4-if00:/dev/ttyACM1`

Both verified healthy post-recreate with real traffic, not just container-up: packet-capture logs show live captured packets from the Observer (SNR/RSSI data, MQTT 3/3 → connected to local as 4th), and the bridge log shows `Serial Connection started`, MeshCore CONNECTED event on `/dev/ttyACM1`, and `MQTT: connected`. A future reboot or cable reshuffle can no longer cross-wire the Observer and KPR2 containers — each is now bound to a specific USB serial number, not an enumeration slot.

---

### July 27, 2026 (early AM) — CoreScope `local`/Observer feed recheck — CONFIRMED HEALTHY, item closed
Hours after the meshomatic config fix and the ACM by-id pinning work, rechecked whether the `local` source (Observer feed, tcp://172.17.0.1:1883) had genuinely settled or was still stuck disconnected as briefly seen right after the CoreScope restart.

Confirmed healthy two independent ways:
1. `meshcore-packet-capture` logs on cnjmesh3 show continuous live packet captures with `MQTT: 4/4` — all 4 configured brokers (letsmesh-us, letsmesh-eu, meshomatic, local) successfully receiving every packet, varying SNR/RSSI confirming real RF traffic, not stale data.
2. Mosquitto's own broker log on cnjmesh1 independently confirms it: `meshcore_client_A8C40BF_4` (the Observer's packet-capture client) is seen publishing to `meshcore/EWR/A8C40BF.../packets` roughly every 15 seconds, and the broker is actively forwarding those messages to subscribed clients in real time.

Note for future sessions: an initial `mosquitto_sub -t 'meshcore/#'` run through `docker exec` + `timeout` appeared to return nothing, which looked like a red flag — but cross-checking the broker's own log for that exact client ID showed the subscribed client (`auto-C4937B9B-...`) WAS receiving live PUBLISH messages the whole time. The empty terminal output was a display/buffering artifact of piping `mosquitto_sub` through `docker exec`+`timeout` in this terminal environment, not a real absence of data. **If a `mosquitto_sub` check ever again shows unexpected silence, cross-check `docker logs mosquitto` for the subscribing client's ID before concluding data isn't flowing** — the broker log is the more reliable source of truth than the terminal's own display in this setup.

Item removed from `todos.md` — fully resolved, no further action needed.

---

### July 27, 2026 (early AM, cont'd) — CoreScope local source: attempted IP fix, made things worse, reverted
Tried switching CoreScope's `local` mqttSource from the Docker bridge gateway (`172.17.0.1:1883`) to the LAN IP (`10.0.0.181:1883`), reasoning it was the same class of fragility as the original 8-day CoreScope outage. Backed up config first (`config.json.bak-20260726-2211`).

Result: worse, not better. On the new address, connection attempts climbed to #6 with zero successful "connected" log lines — previously (old address) it did eventually connect, just with instability. Reverted to the backup and restarted; confirmed both `mqttSources` broker lines back to `172.17.0.1:1883`.

While investigating, found the real symptom via Mosquitto's own broker log (not CoreScope's log, which doesn't show enough detail): CoreScope's client connects successfully (CONNACK accepted, auth fine) under a fresh random client ID, then closes ~15 seconds later with `disconnected due to protocol error` — a protocol-level issue, not a timeout or auth failure. This repeats continuously with a new client ID each cycle. Root cause NOT identified — added as a proper open investigation item in `todos.md` with suggested next steps (version compatibility check, packet capture, topic-subscribe syntax review) rather than guessing further tonight.

Confirmed CoreScope's config also has a `meshomatic` mqttSource, connecting via `wss://mqtt.meshomatic.net:443/mqtt` — this is a legitimate, separate national community relay CoreScope was configured to also pull from, unrelated to and not requiring anything from the original meshomatic.net account signup. Worth remembering this distinction came up as a point of confusion tonight.

---

### July 27, 2026 (early AM, cont'd) — CoreScope Observer confirmed healthy in UI; note on Observers vs Nodes search
Verified via the CoreScope Observers page (not the home-screen node search, which doesn't index observers) that CNJ Mesh Observer is Online: last status update and last packet observation both ~1 min ago, 33,936 total packets, 10 pkts/hr, 6d5h uptime, battery 4075 mV, no anomalies. Confirms the `local` source's periodic reconnect cycling (documented above) isn't currently causing meaningfully stale data in practice — it recovers fast enough that CoreScope's home screen shows no "no packets" warning for either `local` or `meshomatic`.

Noted for future reference: CoreScope's home-screen search box ("Find your nodes to start monitoring them") only indexes **Nodes** (claimable mesh devices), not **Observers** (listening stations like the RAK4631). Searching an observer's name there will always return "No nodes found" — this isn't a bug, just an unlabeled category split in the UI. Observers must be found via the dedicated **Observers** tab in the top nav instead.

---

### July 27, 2026 (late night, Opus) — Tilly packet_bridge: CNJ side built & deployed, bridge-subscribe not yet active
Full detail is in todos.md under the cross-mesh bridge item. Summary:
- Confirmed KPR2 firmware v1.16.0-07a3ca9 (06-Jun-2026) supports CMD_SEND_RAW_PACKET (cmd 65, added v1.15.0). Method: `docker stop meshcore-mqtt-bridge` on cnjmesh3 to free /dev/ttyACM1, then `pipx install meshcore-cli` and `~/.local/bin/meshcli -r -s /dev/ttyACM1 ver` (the `-r` repeater flag is required).
- Built Tilly's fork (github.com/Tilton53/meshcore-mqtt) as a NEW image `meshcore-mqtt:bridge` on cnjmesh3, leaving the working `meshcore-mqtt:local` untouched.
- Recreated the container from the new image with packet_bridge env vars (endpoint b, peer a, link backhaul-1). Container healthy; KPR2's normal capture/status feed fully working on the new image.
- Config loads perfectly and a hand-built worker gets `_bridge_topics={'meshcore/bridge/v1/backhaul-1/a/tx':'a'}` — BUT the running process never logs `Subscribed to bridge topic:` and its MQTT client connects as `meshcore-mqtt-8da2a76f` (random suffix) instead of the `meshcore-mqtt-backhaul-1-b` bridge naming. So packet_bridge is NOT active in the live process yet.
- Next step (cheapest first): `docker ps -a | grep meshcore` on cnjmesh3 to check for a stale/duplicate OLD container still running — the random client ID suggests the old `:local` instance may still be up alongside the new one. Then LOG_LEVEL=DEBUG restart, then trace the on_connect callback. A "queue 1000 vs 128" lead was a confirmed red herring — do not rechase it.
- Meta note: this diagnosis burned a lot of tokens on source-diving that a `docker ps -a` and a DEBUG restart should have short-circuited. Next session: check for duplicate containers and turn on DEBUG logging FIRST before reading source.

---

### July 28, 2026 — Tilly packet_bridge: LOCAL subscribe bug RESOLVED (was pre-fix code)
Last night's "bridge not subscribing" bug is fixed. Root cause: we built from Tilly's pre-fix code. He pushed a fix adding a `topic_root` field (env: `PACKET_BRIDGE_TOPIC_ROOT=meshcore/bridge`) — without it, the bridge silently never subscribed. Fixed by: git pull in ~/meshcore-mqtt-tilly, docker build -t meshcore-mqtt:bridge . (rebuild REQUIRED after pull), recreate container with the new TOPIC_ROOT env var + persistent dedup volume (-v ~/meshcore-bridge-data:/data, dedup_db=/data/packet-bridge-b.sqlite3) + LOG_LEVEL=DEBUG. Verified: client ID now `meshcore-mqtt-backhaul-1-b`, and `Subscribed to bridge topic: meshcore/bridge/v1/backhaul-1/a/tx` fires. CNJ endpoint b is fully live. The queue-1000 and duplicate-container theories from last night were both red herrings.

Remaining blocker for end-to-end: broker reachability. Tilly can't reach mqtt.cnjmesh.me (Cloudflare tunnel = WSS not raw TCP 1883). Both endpoints need a shared reachable broker before any packets actually cross.

---

### July 28, 2026 — Two investigations: CoreScope local-source lead found, Mosquitto WS listener bug found (neither fixed yet — both documented for pickup)

**CoreScope `local` source ("No packets from local in 2049 min" recurring bug):** Found a strong candidate root cause via web search — eclipse-mosquitto GitHub issue #2681 describes a client disconnecting with "protocol error" due to sending a zero packet identifier on SUBSCRIBE/QoS>0 PUBLISH, which Mosquitto 2.0.11+ (you're on 2.0.22) strictly rejects per MQTT spec. Matches the connect→subscribe→protocol-error pattern logged July 26-27 almost exactly. NOT YET CONFIRMED — attempted a tcpdump capture (had to install tcpdump first) but the 20s window only caught keepalives, missed a real connect cycle. Also discovered: `local` has now fully stopped retrying (zero mentions in a 2-hour log window) rather than cycling — container's been up since July 27 02:20. Next session: restart CoreScope first (likely fixes it short-term), then re-run tcpdump right after restart to catch and inspect a real SUBSCRIBE packet's identifier bytes.

**Tilly bridge — Cloudflare/WSS investigation:** Confirmed cloudflared itself is healthy (ruled out Tilly's "tunnel is dead" guess with evidence — 2 days uptime, no crash loop) and the tunnel config correctly points mqtt.cnjmesh.me at localhost:9001 (Mosquitto's websockets listener). But found a real bug: port 9001's WS handshake never completes, even tested purely locally bypassing Cloudflare — curl WS-upgrade attempts hang and return empty/0 bytes. Ruled out: wrong Mosquitto version, missing config line, port not published, stale config. Suspected: the WS listener's accept loop may be stuck in the long-running Mosquitto process (zero "New connection" log lines for port 9001 vs. instant logging for 1883). NOT YET DONE: `docker restart mosquitto` — deliberately held off since it's a live broker every service depends on; next session should do the restart then immediately retest the WS handshake locally and via the public hostname.

Both threads are real, active leads — not guesses — but require the next session to actually execute the restarts/captures to confirm.

---

### July 28, 2026 (evening) — EMERGENCY: cnjmesh1 root disk hit 100% full, root cause found and resolved
SGA reported Malla stuck loading. Traced through mqtt-malla-capture-1 logs (`OSError: No space left on device`) to `df -h` showing cnjmesh1's root filesystem at 100% full, 0 bytes free. Found the actual culprit via a full container-log-size scan: **mqtt-filter had a 35GB unrotated Docker log** (Malla's own capture log was a comparatively minor 1.1GB). This matches a previously-flagged suspect from months ago ("leak/backlog cause in mqtt_filter.py") — now confirmed as the real, dominant cause. Truncated both log files (`sudo truncate -s 0 <path>` — safe, doesn't touch the running container). Disk recovered from 100%/0 free to 43%/32GB free immediately.

This is the second time an unrotated container log has filled the root disk (first was the 37GB Mosquitto log tied to the original board failure months ago). Log rotation is still only applied to Mosquitto — mqtt-filter and ~10 other containers remain unbounded. This needs to actually get finished, not firefought container-by-container as each one happens to hit the ceiling. Also worth investigating separately why mqtt-filter specifically produces so much log volume (35GB is a lot for a filtering service — possible verbose logging or an error retry loop).

---

### July 30-31, 2026 — Malla emergency: disk-full root cause fixed, retention set, current status = reachable but slow (not resolved)
Continuation of the disk-full incident logged earlier. Summary of everything done and current confirmed state:

**Fixed:** cnjmesh1 root disk (was 100% full due to mqtt-filter's 35GB unrotated log) truncated back to 32GB free. Malla's own 1.1GB log also truncated. Both mqtt-malla-capture-1 and mqtt-malla-web-1 restarted and confirmed healthy/ingesting live data (real packets flowing, e.g. AgentFourtyTwo, Rak Roof Bot, Sense Card).

**Set:** `data_retention_hours: 2160` (90 days) uncommented in `/opt/stacks/malla/config.yaml` (was `0` = never delete). Restarted both malla containers to pick it up.

**NOT confirmed:** whether retention pruning actually shrinks the existing 1.7GB database — checked immediately after restart and size was unchanged (still 1.7GB). No prune/retention/delete log lines found in either container's logs. Likely explanation: pruning may only apply going forward, or run on a delayed/scheduled basis rather than immediately at startup — Malla's exact retention-enforcement mechanics are NOT understood, only the config option's existence is confirmed. Worth checking again after some real time has passed (a day+) to see if the DB has actually shrunk.

**Root cause of ongoing slowness:** confirmed via mqtt-malla-web-1 logs — a single "Gateway statistics" query took 50 seconds to compute, directly consistent with querying a 1.7GB unpruned SQLite database. This explains: SGA's original "stuck loading" report, a direct local `curl` to port 5008 timing out at both 5s and 8s windows, and tonight's final confirmed state.

**CURRENT STATE as of end of session:** Malla is reachable, Cloudflare Access (email+PIN login) works fine — but the site itself loads very slowly due to the large, still-unpruned database. This is NOT the disk-full problem (that's fixed) — it's a separate, ongoing performance issue tied to dataset size. Cloudflare Access itself was investigated as a possible culprit for an "totally down" report mid-session but self-resolved before a root cause was found — worth noting Access wasn't confirmed broken, may have been transient or related to the same backend slowness (a login redirect timing out while the backend was still catching up).

**Next session:** (1) check if DB size has dropped after retention had time to run; (2) if not, investigate Malla's actual retention/pruning mechanism (check its GitHub docs/source for how `data_retention_hours` is enforced — scheduled job vs on-write vs manual trigger); (3) if pruning genuinely isn't happening, may need a manual one-time cleanup query against the SQLite DB directly, or check for a Malla CLI/admin command that triggers it.

---

### July 31, 2026 — cnjmesh2: removed malla2 from the oktomqtt filter, pointed it at the raw topic (matches cnjmesh1's Malla)
**Goal (Charles):** make `malla2.cnjmesh.me` on cnjmesh2 run the same as `malla.cnjmesh.me` on cnjmesh1 — i.e. drop the oktomqtt filter dependency. Temporary for now, possibly permanent.

**Why this works / what was confirmed first:** cnjmesh1's Malla (`mqtt-malla-capture-1`) never used its filter either — it subscribes directly to raw `msh/US/#` (`MALLA_MQTT_TOPIC_PREFIX=msh`, `MALLA_MQTT_TOPIC_SUFFIX=/US/#`). cnjmesh2's Malla (`malla-capture`) was instead downstream of oktomqtt, subscribed to `filtered/msh/+/+/+/#`. oktomqtt's own INPUT was already `msh/US/#`, so the raw topic is present on cnjmesh2's local broker — pointing Malla straight at it means the same data with no gap. Confirmed both configs against the install-maps before touching anything.

**Change made (cnjmesh2, `~/meshtastic-mqtt/docker-compose.yml`):** edited `malla-capture`'s two topic env vars:
- `MALLA_MQTT_TOPIC_PREFIX`: `filtered/msh` → `msh`
- `MALLA_MQTT_TOPIC_SUFFIX`: `/+/+/+/#` → `/US/#`
Edit was done via a Python script (`/tmp/malla_topic_fix.py`) that required each old line to appear exactly once before touching anything, backed up the file, and printed a diff. **Backup on the Pi: `~/meshtastic-mqtt/docker-compose.yml.bak-preoktomqtt`.**

Then `cd ~/meshtastic-mqtt && docker compose up -d malla-capture` (had to be `up -d`, not `restart`, to pick up the env change; named the service so oktomqtt was untouched at this step). Verified in `docker logs malla-capture`: connected to `mosquitto:1883`, **subscribed to `msh/US/#`** (raw, not filtered), existing DB intact (661 nodes / 151,200 packets carried over), live packets flowing, and a real decrypt succeeded on its own (SBNJ Kendall Park Roof Node 6, key 1/1) — so Malla is decoding the raw stream itself with no oktomqtt in the path. Active-node count ticked up across stats lines = stable ongoing ingest.

**Then disabled the filter (cnjmesh2):** `docker stop oktomqtt`. Because its restart policy is `unless-stopped`, a manual `docker stop` keeps it down across Docker daemon restarts AND full host reboots. The ONLY thing that revives it is an explicit full-stack `docker compose up -d` (no service named) from `~/meshtastic-mqtt`, which reconciles against the compose files (both still define oktomqtt) and would recreate it.

**Note on file layout:** cnjmesh2's compose is split across TWO files that Compose auto-merges — `docker-compose.yml` (main, all four services) and `docker-compose.override.yml` (an oktomqtt-only block with extra env vars: `CHANNEL_KEYS`, `NO_DECRYPT_DEFAULT`, `ALLOW_NO_BITFIELD`, `REJECT_LOG_FILE`, `EXEMPT_NODES`, `SHOW_STATS`, `DEBUG`). Both carry an obsolete `version: '3.8'` line (harmless Compose warning). If oktomqtt is ever made permanent-removed, it has to come out of BOTH files.

**HOW TO REVERSE (temporary → back to filtered):**
1. `docker start oktomqtt` (cnjmesh2) — brings the filter back.
2. Revert the two env lines in `~/meshtastic-mqtt/docker-compose.yml` back to `MALLA_MQTT_TOPIC_PREFIX=filtered/msh` and `MALLA_MQTT_TOPIC_SUFFIX=/+/+/+/#` (or just restore `docker-compose.yml.bak-preoktomqtt` over it).
3. `cd ~/meshtastic-mqtt && docker compose up -d malla-capture` to re-point Malla at the filtered topic.

**IF MADE PERMANENT instead:** remove the `oktomqtt` service block from BOTH `docker-compose.yml` and `docker-compose.override.yml` (with backups), then re-run `collect-inventory.sh` on cnjmesh2 and this gets pushed. Left as a todo until Charles decides.

**Pi Zero 2 W caution (512MB RAM board) — flagged, not yet a problem:** malla2 now eats the raw firehose instead of oktomqtt's validated/deduped output, so more volume + it does its own per-packet decrypt. Three gauges to watch on cnjmesh2 over the next day: (1) RAM/swap (`free -h`, `docker stats`) — 512MB shared across malla-capture + malla-web + mosquitto; (2) DB/SD growth — raw stream writes more rows to `meshtastic_history.db`, confirm Malla retention/cleanup is actually bounding it (same disk-fill risk that hit cnjmesh1 twice); (3) Docker log rotation — malla-capture logs per-packet, confirm cnjmesh2's `/etc/docker/daemon.json` has the 10MB×3 cap so the container log can't balloon. If any get tight, re-enabling oktomqtt is the quickest volume-reduction safety valve — another reason it was left stoppable rather than deleted.

**Housekeeping still due:** `install-map-cnjmesh2.md` needs a `collect-inventory.sh` regen to reflect oktomqtt's stopped state + the new malla-capture topic values (the committed map still shows the old `filtered/msh` config and oktomqtt running). Not a reversal risk — full reversal detail is captured above.

---

### July 31, 2026 (cont.) — cnjmesh2: added Docker log rotation (was completely unbounded)
Follow-up to the oktomqtt/malla2 change above. While checking whether the raw-firehose switch created any resource risk on the Pi Zero 2 W (512MB), found cnjmesh2 had **NO `/etc/docker/daemon.json` at all** and all containers running with `{json-file map[]}` — i.e. zero log rotation, unbounded growth. This is the exact setup that filled cnjmesh1's root disk twice (37GB Mosquitto log, 35GB mqtt-filter log). cnjmesh2 had plenty of headroom (45G free / 19% used, Malla DB only 68M, RAM tight-but-stable at ~198Mi avail + 197Mi swap, not thrashing) so nothing was failing — this was preventive.

**Fix applied (cnjmesh2):** created `/etc/docker/daemon.json` with `json-file` driver, `max-size: 10m`, `max-file: 3` (matches cnjmesh1's pattern — 30MB cap per container). Validated the JSON, `sudo systemctl restart docker` to load the default, then `docker compose up -d --force-recreate malla-capture malla-web mosquitto` (daemon defaults only apply to newly-created containers). Named those three explicitly so oktomqtt stayed stopped — confirmed via the compose output (only the three recreated) and inspect. All three now show `{json-file map[max-file:3 max-size:10m]}`. oktomqtt (still stopped) will only get the cap if/when it's ever recreated — moot while stopped, and it's slated for removal if the change goes permanent.

Note: both cnjmesh2 compose files still carry an obsolete `version: '3.8'` line (harmless Compose warning) — optional future cleanup, not done.

---

### July 31, 2026 (cont.) — cnjmesh1: full outage post-mortem (ROOT CAUSE: Xfinity bill) + 6 chronic findings
**Reported symptom:** malla.cnjmesh.me and meshview appeared down; Charles felt "something very off" with cnjmesh1 since the post-death board replacement, and asked about an OS upgrade. Started as OS-upgrade + diagnose-root-cause, became a live outage investigation.

**ROOT CAUSE OF THE OUTAGE: Xfinity/Comcast service was suspended for non-payment.** The uplink was blackholed at the gateway. Everything downstream failed as symptoms:
- `apt update` → `Temporary failure resolving` on every mirror (couldn't reach DNS).
- cloudflared → `failed to dial to edge with quic: timeout: no recent network activity`, retrying endlessly; then `systemctl restart cloudflared` hit a **start timeout** because a startup DNS lookup (`cfd-features.argotunnel.com`) blocked >10s.
- Malla/Meshview "down" publicly = tunnel down, not the apps.
Resolved the moment Charles paid the bill: gateway ping recovered (0% loss), internet + DNS restored, `systemctl reset-failed cloudflared && restart` came up clean, tunnel re-registered edge connections and **stabilized** (no flapping after link settled), and **`https://malla.cnjmesh.me/` confirmed reachable end-to-end (302 in 6.5s)**. Meshview was healthy locally the whole time (302 on localhost:8080).

**DIAGNOSTIC PATH (for the runbook):** the tell that isolated it to the gateway (not the Pi) — `ip route` showed correct `default via 10.0.0.1`, wlan0 UP/associated to C4Somogyi-24, NetworkManager `connected`, signal healthy (-63 dBm), ARP resolved the router MAC — i.e. **every layer on the Pi was correct**, yet `ping 10.0.0.1` = 100% loss and `10.0.0.1:53` unreachable. Config perfect + gateway won't pass traffic = problem is upstream of the Pi. **>> RUNBOOK: when cnjmesh1 loses all outbound (apt/tunnel/DNS all failing at once) and the Pi's own route/WiFi/ARP check out, CHECK THE XFINITY UPLINK / BILL FIRST before rabbit-holing into DNS, IPv6, cloudflared, or memory. This cost ~2 hours of symptom-chasing.**

**SIX CHRONIC FINDINGS (real, none are emergencies, all deferred to a clear-headed session — NOT to be done post-outage/tired):**

1. **[PRIORITY — DATA LOSS RISK] Malla DB is 2.0GB on a Docker NAMED VOLUME, likely NOT backed up.** Actual path: `/var/lib/docker/volumes/mqtt_malla_data/_data/meshtastic_history.db` (2.0G + 77M uncheckpointed WAL). The PowerShell DR backup-pull targets bind-mount paths under stack dirs; a named volume under `/var/lib/docker/volumes/` is almost certainly NOT covered. If cnjmesh1's SD card dies (this is the REPLACEMENT board, no track record), the entire Meshtastic history is lost. **FIX: extend backup to cover the named volume (or `docker run --rm -v mqtt_malla_data:/v -v ...:/backup ... tar` it). Verify before any DB prune.** NOTE: cnjmesh2's Malla is a bind mount (`~/meshtastic-mqtt/malla`) — inconsistent between boxes.

2. **`collect-inventory.sh` doesn't resolve named-volume source paths.** The 2GB DB was invisible in install-map-cnjmesh1.md because the script surfaces bind mounts but not named-volume `/var/lib/docker/volumes/...` sources. **FIX: enhance the script to resolve named volumes to their host paths + sizes.**

3. **Malla slowness root cause = 2GB DB + uncheckpointed 77MB WAL.** The 24h gateway-stats aggregation takes **58.3s** (logged: "Gateway statistics computed in 58.278s"), cached only 300s — so every cold-cache page load times out browsers. App is healthy (returns 200), just grinding a huge DB on a starved box. **FIX: WAL checkpoint + retention/prune on the DB (after backup is confirmed). CoreScope's own project added an hourly WAL checkpoint for exactly this class of problem (v3.8.2 release note).**

4. **Docker memory cgroup accounting/limits DISABLED.** `docker stats` shows `0B / 0B` for ALL containers = kernel memory cgroup controller not enabled (missing `cgroup_enable=memory cgroup_memory=1` in `/boot/firmware/cmdline.txt`). Means NO per-container memory limits are enforceable → no guardrail against one container eating all RAM → contributes to the swap pressure/fragility. Likely a post-swap regression (fresh Trixie install never had the line re-added). **FIX: add to cmdline.txt — REQUIRES REBOOT, plan it, watch it come back up (16 containers slow to recover under swap).**

5. **Tooling baseline not restored post-swap.** No `dig`, `nslookup` installed (had to diagnose DNS with getent/ping/bash-/dev/tcp). Another "replacement board never brought to original's baseline" item. **FIX: `apt install dnsutils` + audit what else the original had.**

6. **Xfinity link up but jittery post-restore.** Gateway ping 175–313ms, cloudflared briefly flapped connections while settling. Common after suspend-clear. **FIX (optional, when convenient): power-cycle the Comcast gateway to force clean re-provision. NOT a Pi action.**

**CAPACITY VERDICT (answers Charles's opening "something feels off"):** it wasn't one thing. The OUTAGE was purely Xfinity (Pi was healthy). The chronic "off" feeling = the replacement board was never restored to baseline (findings 4,5) AND the box is over-subscribed (16 containers, 1.8GB RAM, ~40-90MB free, 1.5GB swap, no memory guardrails) with a bloated Malla DB. NO OOM kills observed (kernel isn't reaping) so it's fragile/slow, not actively crashing. The offload-vs-headroom-vs-rebuild decision from the top of session is still open — now with data behind it — and deliberately deferred to a fresh session, not decided tired post-outage.

**Confirmed NOT problems (ruled out this session):** OS is current Trixie (kernel 6.12.62, nothing to upgrade to). WiFi power-save correctly off. resolv.conf correct. Disk fine (54% / 26G free). Meshview healthy (systemd services meshview-db/meshview-web, NOT docker). Route/WiFi/ARP config all correct.

---

### July 31, 2026 (cont.) — cnjmesh1: manual Malla DB backup taken; session closed
Took a manual consistency-safe snapshot of the Malla DB while addressing the backup-gap finding above: `docker exec mqtt-malla-web-1 python3 -c "...sqlite3 .backup..."` inside the container (in-place page-copy, `sqlite3` CLI not present in the image so used Python's `sqlite3.backup()` API), then copied the resulting snapshot out of the Docker named volume to the host. **Result: `/home/somog/backups/malla-backup-20260731.db`, 2.0G, confirmed present.** This is a one-time manual backup, NOT yet automated — `cnjmesh1-backup.sh` still does not cover the named volume (see todos.md). Still needs to be copied off-Pi (scp to laptop / OneDrive) — not yet done as of session close.

Noted during this: the ~5-8 min it took to copy 2GB visibly degraded cnjmesh1 further (Charles reported malla.cnjmesh.me giving a Cloudflare "host error" on his phone during the copy) — consistent with the box's chronic memory/swap pressure (finding #4 above), not a new problem. Should clear once the box is idle.

**Session closed here at Charles's request (token budget).** Malla's slowness is NOT resolved — explicitly deferred, not forgotten. Do not assume DB size is the confirmed root cause of the 58s query; verify via query plan/indexes (read-only) before any VACUUM next session.

---

### July 31, 2026 (cont.) — CORRECTION: malla.cnjmesh.me confirmed DOWN, not just slow. Session stopped here (credit budget).
Earlier same-session entries said Malla was "healthy, just slow on cold cache" — that was true at the time it was checked (58s query, then returned 200) but is **NOT the current state**. After the manual 2GB DB backup copy, Charles reported a Cloudflare "host error" on his phone. Follow-up local checks confirmed a real outage, not cache coldness:
- `curl localhost:5008` (local, bypassing tunnel): **timeout, 0 bytes, 15s and 20s** — consistent failure, not a one-off.
- `docker restart mqtt-malla-web-1`: container restarted, but **still not serving 30+ seconds later** (still timing out at 20s).
- Container `docker ps` shows `Up`, but the Flask process inside is not accepting/responding to requests.

**Root cause NOT confirmed.** Leading hypothesis, not verified: the box's chronic memory/swap pressure (findings #4 in the outage post-mortem above) was pushed over the edge by the 2GB backup-copy I/O load, and malla-web can't fully start/serve under current memory conditions even after a restart. Not proven — could also be the 2GB DB itself blocking startup (e.g. WAL recovery, index load) rather than memory. **DO NOT ASSUME CAUSE — diagnose fresh next session with `docker logs mqtt-malla-web-1` (was not captured before session end) and `free -h` (was not captured after the failed restart).**

**STATUS AT SESSION CLOSE: malla.cnjmesh.me / mqtt-malla-web-1 is DOWN — confirmed via local curl, not just tunnel/public access.** This is NOT resolved. Stopped here at Charles's request due to session credit budget, not because the issue was fixed. Next session: start with `docker logs --tail 30 mqtt-malla-web-1` and `free -h` on cnjmesh1 before any further action.

---

### Aug 1, 2026 — cnjmesh1: Malla DB pruned to 30 days + VACUUMed (speed fix FAILED); gateway-unreachable pattern recurred 3rd time
**Malla DB work (continuation of July 31 outage session):** Confirmed via Malla's own upstream repo (`github.com/zenitraM/malla`, `AI.md`) that the project is explicitly "vibe coded" by its author with scalability/maintainability NOT a priority — corroborates that the slow query is an application-code issue, not a DB-tunable one. Investigated actual ingestion rate before pruning: DB spans Jan 19 - Jul 31 (193 days); rate has climbed steadily and accelerated sharply (~3,160 rows/day in the oldest ~90-day slice vs ~172,000 rows/day in the most recent 30 days) — consistent with cnjmesh1 progressively picking up meshcore-hub, KPR1 bridge, CoreScope, and more Meshtastic gateway/bridge traffic over these months. This is real traffic growth, not DB-age artifact.

Given the 6-month history, chose 30-day retention (not 90/60, which barely reduced volume; not 7/14, to preserve more history). **Executed: deleted 689,299 rows older than 30 days, then VACUUM (813.3s / ~13.5 min).** DB shrank 2.0GB → 1.7GB — a real, confirmed reduction. Restarted malla-capture/malla-web.

**RESULT: DID NOT FIX THE SPEED PROBLEM.** Query time before any DB work: ~45-48s. After VACUUM+ANALYZE+690K-row-delete+VACUUM (2 full VACUUM passes total across the session): **still ~41s.** Conclusively rules out DB size/bloat/missing-index/stale-stats as the cause — three separate remediation attempts, minimal effect. **Root cause is very likely in Malla's application code** (single-threaded Flask dev server + likely inefficient Python-side stats computation), not the database. This needs a source-code-level look, not further DB operations. DO NOT run further VACUUM/prune cycles expecting a speed fix — that avenue is exhausted.

Also installed `malla-warmcache.service` + `.timer` (curl to :5008 every 4 min via systemd) to keep the 5-min Flask cache warm so real visitors don't hit the ~41-48s cold path. **Testing was inconclusive/failed** — a curl immediately after a confirmed-successful warm-up run still timed out at 10s. Timer is left installed and enabled, but its effectiveness is UNVERIFIED. Do not assume it's working.

**Net Malla DB outcome: database is smaller, cleaner, backed up (see below) — but malla.cnjmesh.me speed is NOT fixed. This was the wrong root-cause tree; next session needs to look at Malla's actual Python code (gateway_service.py or similar), not more DB tuning.**

---

**SEPARATE, MORE URGENT: gateway-unreachable pattern recurred a 3rd time, this time affecting reachability from OTHER LAN hosts (not just cnjmesh1's own uplink).**

Roughly a day after the July 31 outage (which was root-caused to the Xfinity bill and resolved), Charles reported cnjmesh1 alerting as down again (Malla AND fing both alerting). Diagnosed: disk usage had jumped 54%→85% (8.4G free) in one day — plausibly from the 1.7-2GB Malla backup snapshot + DB rewrite churn left on the Pi overnight; inodes fine (12%), no filesystem corruption in dmesg, so NOT a disk-health issue.

Attempted to scp the Malla backup off cnjmesh1 to Charles's laptop to reclaim space — **failed: laptop could not reach cnjmesh1 at all.** `ping 10.0.0.181` failed (expected — Windows blocks ICMP by default, not conclusive) but critically **`Test-NetConnection -ComputerName 10.0.0.181 -Port 22` also failed (`TcpTestSucceeded: False`)** — a real, non-ICMP failure. Charles's existing SSH session to cnjmesh1 (opened earlier) remained alive and responsive throughout (TCP connections can survive a routing blip that blocks new connections). From inside that live session: `wlan0` UP, correctly addressed (`10.0.0.181/24`), but **`ping 10.0.0.1` (gateway) = 100% loss** — the IDENTICAL signature from the July 31 outage (Pi-side config perfect, gateway unreachable), now observed a 3rd time.

**THIS TIME the fix was NOT executed** — Charles needs to be physically home to power-cycle the Comcast gateway (unplug 60s, plug back in, wait 3-5 min), and had to step away. **>> PENDING ACTION: power-cycle the Xfinity/Comcast gateway when Charles is home. Verify after with `Test-NetConnection -ComputerName 10.0.0.181 -Port 22` from the laptop — `TcpTestSucceeded: True` = fixed.**

**PATTERN NOTE for runbook:** "Pi config correct, WiFi associated, gateway unreachable" has now happened 3x in ~36 hours (July 31 outage, and twice more Aug 1). The July 31 instance was confirmed caused by an Xfinity billing suspension and resolved by payment — but recurrence AFTER payment/restoration suggests either (a) the link genuinely destabilized and needs the deferred gateway reboot, or (b) something router-side (possibly related to the replacement Pi's new WiFi MAC — flagged July 31, never fully investigated) is causing intermittent drops. **If the gateway power-cycle does not produce a lasting fix, escalate to investigating the MAC-address/router-config angle rather than re-diagnosing from the Pi side again — the Pi's own config has now checked out clean 3 times in a row.**

**Charles's assessment, worth preserving verbatim in spirit:** frustration that this is recurring "every day" and questioning whether the hardware is worth continuing to troubleshoot vs. replacing. Noted for the offload/rebuild capacity decision still pending from July 31 (see prior entries) — this recurring connectivity issue is a separate axis from the memory/capacity issue, and should be evaluated separately (network/gateway problem vs. Pi capacity problem) rather than conflated.

---

### Aug 2, 2026 (~5am) — Malla root cause CONFIRMED: single-threaded Flask dev server, not DB size. Gunicorn fix identified but NOT completed.

**CORRECTION to earlier same-session entries:** a 3.2s query time was observed and mistakenly reported as the pruning fix working. It was NOT — a later request in the same session logged `Gateway statistics computed in 42.999s`, confirming the query cost is essentially UNCHANGED from before any pruning/VACUUM work. The 3.2s reading was luck (landed on a warm cache), not a fix.

**Real root cause, confirmed:** Malla runs on Flask's single-threaded dev server (`/app/.venv/bin/malla-web`, confirmed via `docker inspect`). While the ~40s dashboard stats computation runs, other request types (packets page, API endpoints) DO get served (different code path), but concurrent/dashboard requests queue or time out behind it. This is what produces the "up and down" experience Charles reported — not truly down, but effectively unusable because whether any given request lands during the ~40s window is unpredictable.

**Fix identified: run Malla under gunicorn (multi-worker) instead of the Flask dev server.**
- Confirmed factory function: `create_app()` at line 68 of `/app/src/malla/web_ui.py` — NOT a module-level `app` object (an `from malla.web_ui import app` import fails). Correct gunicorn target string: `"malla.web_ui:create_app()"`.
- `pip install gunicorn` inside `mqtt-malla-web-1` succeeded cleanly (gunicorn 23.0.0 installed, confirmed via error banner on next run — no image rebuild needed, base image already has what gunicorn needs).
- Test run on port 5009 (side-by-side, NOT touching live 5008): result was inconsistent/unresolved — gunicorn logged "Address already in use" on a second attempt (implying an earlier `-d` backgrounded instance WAS running), but curl to that port got instant "Connection refused" rather than a real response. Did not get this fully working before stopping for the night — this discrepancy needs to be understood before proceeding (worker startup timing? a stale/orphaned process? needs clean investigation, not more live trial-and-error at 5am).

**NEXT SESSION — do this first, in order:**
1. `docker exec mqtt-malla-web-1 ps aux | grep gunicorn` — check for orphaned/stuck gunicorn processes from tonight's testing; kill any found.
2. Retest gunicorn on port 5009 cleanly (foreground, watch full startup output, confirm each of the 3 workers actually binds — don't background with `-d` until confirmed working foreground first).
3. Once confirmed serving on 5009: make it permanent by editing the `mqtt-malla-web-1` service `command:` in `/opt/stacks/mqtt/docker-compose.yml` to launch gunicorn (`gunicorn -w 3 -b 0.0.0.0:5008 "malla.web_ui:create_app()"`) instead of the default entrypoint, then `docker compose up -d --force-recreate malla-web`.
4. NOTE: `pip install gunicorn` done via `docker exec` tonight is NOT persistent — it lives only in the running container's writable layer and will be LOST on next recreate/restart. The permanent fix needs gunicorn baked in properly: either add it via a custom Dockerfile layer, or reinstall as part of an entrypoint override/init script in compose. Do not just flip the `command:` without re-solving the gunicorn-install-persistence problem first, or the container will fail to start post-recreate.

**CoreScope: confirmed healthy tonight** — 200 response in 0.7s, clean ingest logs, no errors, no action needed.

**Session ended here (~5am) at Charles's judgment — mid-fix, deliberately not pushed further live. This is the correct stopping point: root cause is finally understood and correct, fix is scoped and partially validated, remaining work is clear and bounded for next session.**

---

### Aug 2, 2026 — ROOT CAUSE FOUND & RESOLVED: cnjmesh1 daily disk-fill = unrotated mqtt-filter log (30GB/day). Filter retired.

**The recurring daily disk-full problem on cnjmesh1 is finally root-caused and fixed** — not just cleared-and-recurring as it had been.

**Symptom:** cnjmesh1 hits 100% disk daily; Charles clears space, it refills next day, making the environment unreliable. (This session it was found AT 100% full, load avg 12.6, 54MB free RAM — Docker daemon so wedged that `docker inspect`/`docker logs` hung for 30+ min.)

**Root cause (confirmed, not inferred):** the `mqtt-filter` container (image `meshtastic-oktomqtt-filter:latest`) was writing a SINGLE json.log file that reached **30GB** — over half the 58GB disk — because (a) cnjmesh1 has NO Docker log rotation configured, and (b) the filter runs with `SHOW_STATS=true` + per-packet processing, emitting a huge volume of log lines continuously. Confirmed via `du` on `/var/lib/docker/containers/*/*-json.log`: the 30GB file mapped to container `mqtt-filter`; second-largest was mqtt-malla-capture-1 at 787MB.

**What mqtt-filter does (confirmed via its on-disk README at `/opt/stacks/mqtt/meshtastic-oktomqtt-filter/README.md`):** enforces the Meshtastic "Ok to MQTT" firmware-2.5+ privacy opt-in bitfield + decrypts packets, republishing only authorized packets from INPUT `msh/US/#` to OUTPUT `filtered/msh/US`. Defined in `/opt/stacks/mqtt/compose.override.yaml` (NOT the main compose.yaml — that's why an earlier grep of compose.yaml missed it; same override-file pattern as cnjmesh2's oktomqtt).

**Why stopping it is safe (confirmed, not assumed):**
- Malla-capture on cnjmesh1 subscribes to RAW `msh/US/#` (`MALLA_MQTT_TOPIC_PREFIX=msh`, `SUFFIX=/US/#`) — confirmed via live `docker inspect` AND the compose.override.yaml. It does NOT read the filter's output.
- Grep of `/opt/stacks/` + `/home/somog/` for `filtered/msh` found NO consumer — only the filter's own config files reference it. Nothing subscribes to `filtered/msh`.
- Therefore the filter was producing a consent-filtered topic that NOTHING consumed = pure overhead + the log flood.

**Charles's decision:** retire the OkToMqtt filter permanently. Rationale: the broader Meshtastic ecosystem (maps, public brokers, tools) largely does not honor the OkToMqtt flag anyway, so enforcing it locally into a topic nobody reads is effort without payoff.

**Actions taken this session:**
1. `sudo truncate -s 0` on the 30GB mqtt-filter json.log → disk 100% → 51% instantly (emergency space recovery to un-wedge the Docker daemon).
2. `cd /opt/stacks/mqtt && docker compose stop mqtt-filter` → stopped the flood source. Disk stable at 52% afterward, confirmed NOT climbing → proves the filter was the daily-growth source.

**REMAINING TO-DO (do next, when box is calmer):**
1. **Make the filter retirement permanent** — it's only `stop`ped; a future `docker compose up -d` (no service named) would restart it and reintroduce the flood. Remove/comment the `mqtt-filter` service block from `/opt/stacks/mqtt/compose.override.yaml` (with a backup) so it can't come back. Also clean up the leftover duplicate config files noticed in that dir: `mosquitto.env2`, `config/mossquitto.conf2`, `docker-compose.override.yaml1` (odd numeric-suffixed backups/cruft — verify they're unused, then remove).
2. **Add Docker log rotation on cnjmesh1** (it has NONE — this is the amplifier that let one container reach 30GB unbounded, and protects EVERY other container going forward). Create `/etc/docker/daemon.json` with json-file + max-size 10m + max-file 3 (same as we did on cnjmesh2 Aug 1), then `sudo systemctl restart docker`. NOTE: the restart bounces all 16 containers and will be SLOW on this loaded box — do it when it can be watched, not at end of a session. This is the belt-and-suspenders that permanently prevents ANY container from refilling the disk.
3. Re-run `collect-inventory.sh` on cnjmesh1 after the above to refresh install-map (it currently shows mqtt-filter as running).

**Also confirmed healthy this session:** CoreScope (200 in 0.7s, clean ingest). KPR1 bridge (`meshcore-mqtt-kpr1-bridge`) shows MESHCORE connected but MQTT DISCONNECTED — flagged, likely downstream of the disk emergency (Mosquitto struggling at 100% disk); recheck now that disk is recovered. cnjmesh3 health check was started but not completed (KPR2 `meshcore-mqtt-bridge` + Observer `meshcore-packet-capture` publishing to 10.0.0.181:1883) — finish next session.

---

### Aug 2, 2026 (cont.) — mqtt-filter PERMANENTLY REMOVED (not just stopped)
Followed through on the permanent removal:
1. Backed up `/opt/stacks/mqtt/compose.override.yaml` → `.bak-preremove` (sudo).
2. Rewrote compose.override.yaml to contain ONLY the `malla-capture` topic override (`MALLA_MQTT_TOPIC_PREFIX=msh`, `SUFFIX=/US/#`) — removed the entire `mqtt-filter` service block. Malla's raw-topic settings preserved.
3. `docker rm mqtt-filter` — deleted the stopped container object.

Result: mqtt-filter cannot return on reboot OR on `docker compose up -d` (no longer defined in compose). Image `meshtastic-oktomqtt-filter:latest` and source repo `/opt/stacks/mqtt/meshtastic-oktomqtt-filter/` remain on disk if ever wanted again. **Daily disk-fill root cause is now PERMANENTLY resolved.**

Remaining (lower priority now that the flood source is gone): (1) Docker log rotation on cnjmesh1 still absent — worth adding as belt-and-suspenders for any future container, but no longer urgent; needs the docker-daemon restart, do when box is calm. (2) Re-run collect-inventory.sh on cnjmesh1 to refresh install-map (no longer shows mqtt-filter). (3) Clean up leftover cruft files in /opt/stacks/mqtt: mosquitto.env2, config/mossquitto.conf2, docker-compose.override.yaml1.

---

### Aug 3, 2026 (~1:25am) — KPR1 "MQTT disconnected" DIAGNOSED: it's the external Tilly AWS broker, not local infra
Rechecked KPR1 (`meshcore-mqtt-kpr1-bridge` on cnjmesh1) after the disk fix — still `MESHCORE: connected | MQTT: disconnected`, so NOT a side effect of the disk-100% emergency (that theory ruled out). Dug into its config:

**Root cause: KPR1's bridge points at `MQTT_BROKER=mqtt.aws.tillyandthefish.com` (Tilly's EXTERNAL AWS broker), NOT the local Mosquitto.** So the disconnect is an OUTBOUND connection to someone else's internet-hosted broker failing — has nothing to do with cnjmesh1's local Mosquitto, disk, or network. This matches the git note that KPR1 is the "experimental cross-network packet_bridge" publishing outward to Tilly's AWS broker (a separate MQTT relationship from everything else). Local infra (CoreScope, Hub, Malla) is UNAFFECTED — they use the local broker.

Credentials in use: `meshdev`/`large4cats`, topic prefix `meshcore`, port 1883, QOS 1, retain true. Serial side healthy (`/dev/ttyUSB3` — note: install-map says ttyUSB1, path has shifted; docs stale on that detail).

**Assessment:** low concern. Could be down because Tilly's AWS broker is offline, their creds changed, or an AWS network path issue — all outside Charles's control. AND KPR1 is already flagged for RETIREMENT (Charles didn't want 2 repeaters; KPR1 is in the garage, worse location than KPR2). So this experimental external bridge failing is not worth a fix — either ping Tilly to ask if their AWS broker is up (if keeping the experiment alive), or let it fold into the KPR1 retirement. NOT a late-night fix; captured for the health-check sweep.

---

### Aug 3, 2026 — CORRECTION on KPR1: it's being REPURPOSED to Tilly's fork, not retired
Previous entry framed KPR1's MQTT-disconnect as "ties to retirement" — that's WRONG per Charles. KPR1 is being dedicated to **Tilly's fork** (which is why its bridge points at `mqtt.aws.tillyandthefish.com`). This is an IN-PROGRESS integration that isn't working yet, NOT a node winding down. The MQTT-disconnect means the Tilly-fork integration is incomplete/broken and needs to be finished — this is an active TODO, not something to let lapse.

**TODO (keep on list): Get Tilly's fork up and running on KPR1.** The bridge connects to the radio fine (serial /dev/ttyUSB3, MESHCORE connected) but can't reach Tilly's AWS broker (`mqtt.aws.tillyandthefish.com`, user meshdev, port 1883). Next steps to diagnose: (1) confirm with Tilly whether the AWS broker is up + creds current, (2) test reachability from cnjmesh1 to that host:port, (3) check whether it needs TLS/8883 vs plain 1883, (4) confirm what "Tilly's fork" specifically requires vs the standard meshcore-mqtt bridge config. Reference Tilly's fork repo (git.meshworks.ru / nytera meshworks-malla was a different thing — confirm the correct Tilly fork repo) and coordinate with Tilly directly.

---

### Aug 2, 2026 — dracoling follow-up: two refinements to the Malla diagnosis

**1. "Suddenly hit a wall a couple weeks ago" is a diagnostic signal, not just frustration.** Charles told dracoling things were "humming until a couple weeks ago, then suddenly hit a wall." SUDDEN onset (vs gradual slowdown) points to a THRESHOLD being crossed — DB crossing a size where the gateway-stats query no longer fits in the 2GB Pi's RAM/cache and starts constantly paging through swap/disk. Aligns with: the DB crossing ~2GB, and/or the mqtt-filter disk-fill starting to bite around the same time. The timing correlation with mqtt-filter's log growth is worth checking.

**2. dracoling's key leads:**
- Runs Malla on a MEDIUM VIRTUAL SERVER, not a Pi. Explicitly flagged: "on a pi you might be running into disk lag trying to keep the whole thing loaded." = confirms our swap-bound-Pi finding. A 2GB Pi with DB too big to stay resident = constant disk paging during the query.
- Their fix history: "had to do a serious database cleanup at one point." Offered to dig up those cleanup notes TOMORROW — **take them up on it.**
- **CRITICAL LEAD: "if you're on a recent-ish version it should be clearing out old records regularly."** i.e. RECENT MALLA VERSIONS AUTO-PRUNE. If Charles is on an OLDER version, that's WHY the DB grew unbounded (we confirmed it wasn't auto-pruning — retention setting did nothing). This means the REAL root-cause fix may be **upgrading Malla to a self-pruning version**, NOT gunicorn. Reframes the shelved upgrade question: the upgrade may BE the fix, not optional polish.

**Revised next-session priority order for Malla:**
1. Check what Malla VERSION cnjmesh1 is running vs latest (does current version auto-prune? when was that feature added?). If we're old and newer auto-prunes -> upgrading is the root-cause fix.
2. Check access logs for bot/scraper load (dracoling's first lead) — esp. on public malla2. Cheap to verify.
3. Get dracoling's database-cleanup notes.
4. THEN decide gunicorn vs upgrade vs both, informed by 1-3. Gunicorn addresses concurrency/blocking; a self-pruning upgrade addresses DB growth; bot-blocking addresses load. These are THREE different levers for what may be overlapping causes — don't fixate on one.
Note the XSS/security angle (CVE-2026-43980, all versions <=0.1.7) also argues for upgrading — but confirm a newer version actually fixes it AND doesn't break our raw-topic/config setup before pulling.

---

### Aug 2, 2026 — KEY timeline ambiguity to resolve (from dracoling thread)

Charles noted to dracoling: **"I started to see issues, then the pi died, I replaced it, so unsure if due to the replacement or just a continuation of what I was observing before the old pi died."**

This is an important open question that NARROWS the diagnosis if resolved:
- If the slowdown PREDATED the board swap (issues seen before the original Pi died) -> argues AGAINST the replacement board being the cause, and FOR something that carried over. The Malla DB persists on a Docker named volume (`mqtt_malla_data`) across the hardware swap, so if the problem followed the DATA not the hardware, it reinforces dracoling's DB-size / Malla-version angle over any hardware explanation.
- If it started only AFTER the swap -> points more at the new board / its config regressions (cgroups disabled, tooling baseline, etc. — see July 31 findings).

**Resolvable next session:** line up (a) when the Malla slowdown actually began (its logs / the DB's own record timestamps / when the DB crossed ~2GB) against (b) when the board was physically replaced. This dates the onset and tells us which side of the swap it started — turning "unsure" into a fact.

Charles also told dracoling he's rebooting cnjmesh1 tomorrow "when I have time to actually monitor services starting" — consistent with the deliberate-reboot guidance already logged. Do the health-check sweep after that reboot.

**Status of the dracoling thread:** productive. Leads captured (bot/scraper load + Anubis; auto-pruning in recent Malla versions; DB cleanup notes coming; medium-VM vs Pi RAM/disk-lag angle; this timeline question). All folded into the revised Malla next-session plan above. dracoling offered to dig up their DB-cleanup notes tomorrow.

---

### Aug 2, 2026 — RESOLVED via Malla README: no version upgrade needed; three CONFIG features fix everything

Read the full Malla README (github.com/zenitraM/malla). Definitive answers:

**Charles was RIGHT that there's nothing to "upgrade" version-wise:** "No releases published" — no tags, no version numbers, no changelog. Rolling `main` / `:latest` only (105 commits). Only "upgrade" = pull a newer `:latest`.

**BUT all three of dracoling's leads are REAL, DOCUMENTED features — and they're CONFIG, not version-gated. This is the fix, and it's low-risk (config, not migration):**

1. **Auto-pruning = `data_retention_hours` config (THIS is what dracoling meant by "clears out old records").** Set `MALLA_DATA_RETENTION_HOURS` to a positive number -> deletes packet_history + node_info older than that, every hour, in background. Default `0` = disabled. **Charles's DB grew unbounded simply because this was never enabled — NOT because of an old version.** Fix: set e.g. `MALLA_DATA_RETENTION_HOURS=720` (30d) or `1440` (60d). Permanent self-pruning, ends the manual-prune cycle. (Note: this deletes rows but per SQLite won't shrink the file without a VACUUM — but ongoing it caps growth.)

2. **Gunicorn = officially supported, the RIGHT way (supersedes our 5am manual pip-install fumble).** Set env `MALLA_WEB_COMMAND=/app/.venv/bin/malla-web-gunicorn`. There's a `malla-web-gunicorn` script AND a `docker-compose.prod.yml` for it. Auto-detects workers from CPU cores. Also tunable: `MALLA_GUNICORN_WORKERS`, `MALLA_GUNICORN_THREADS`. This is the proper fix for the single-threaded-Flask blocking problem — via env var, no manual install, no image hacking. NOTE: our Aug-2-5am manual `pip install gunicorn` in the container was NON-persistent and the wrong approach — use MALLA_WEB_COMMAND instead.

3. **Anubis (bot-blocking, dracoling's first lead) = officially supported.** README has `trusted_proxy_client_ip_header: X-Real-IP` explicitly "Recommended for Anubis," plus `trusted_proxy_ips`. So putting Anubis in front to block AI/scrapers is a documented, supported integration.

**REVISED PLAN (all config changes, low-risk, do together next session):**
1. Set `MALLA_DATA_RETENTION_HOURS` (decide window — 30 or 60d) — stops unbounded DB growth permanently.
2. Set `MALLA_WEB_COMMAND=/app/.venv/bin/malla-web-gunicorn` — fixes the single-threaded blocking (the "up and down").
3. Optionally pull a fresh `:latest` while at it (gets any recent fixes incl. possibly the XSS CVE — verify) — but NOT required for the above two, which work on current image.
4. Bot-check the public malla2 access logs; add Anubis if scraper load is heavy there.
These are env-var/config changes in the compose files — far lower risk than the migration/gunicorn-hacking we were contemplating. Remember to preserve the raw-topic override (`MALLA_MQTT_TOPIC_PREFIX=msh`, `SUFFIX=/US/#`) on cnjmesh1.

**This supersedes earlier hedged notes** about "upgrade may be the fix" and the 5am manual-gunicorn approach. The real answer: enable retention + gunicorn via config. Charles's skepticism about upgrades was correct.

---

### Aug 3, 2026 — RECURRING OVERNIGHT OUTAGE PATTERN (Fing alerts) — needs dedicated investigation

**Charles flagged a real, recurring, TIMED pattern via Fing agent alerts:**
- Aug 2, 11:03 PM — Fing Agent "Home" (AGENT-88:A2:9E:3E:0E:7E) went OFFLINE — soon after we finished the session.
- Aug 3, 3:56 AM — came BACK ONLINE.
- ~5 hour overnight outage. Charles says this has been a COMMON/recurring thing.

**Why this matters:** recurring + overnight + roughly same times = points at something SCHEDULED, not random flakiness. This may be behind a lot of the "it was down when I checked" frustration across the whole week. This is a DISTINCT investigation from the disk-fill (already fixed) and the Malla slowness — a separate axis.

**Suspects to investigate (do NOT guess — verify each next session):**
1. **Scheduled jobs / cron / systemd timers running overnight** — check `crontab -l`, `sudo crontab -l`, `systemctl list-timers --all` on cnjmesh1 (and other Pis). Look for anything firing in the 11pm / late-night window. Candidates: Charles's own backup scripts, logrotate, **apt unattended-upgrades** (runs early-AM, can restart network/services), any watchdog doing aggressive restarts.
2. **DHCP lease renewal / networking flap** — ties directly to the recurring "nmcli connection down/up fixes it" gateway issue we saw MULTIPLE times this week. If the router's lease expires overnight and the Pi's renewal flaps, the Pi drops off the network at lease-expiry and recovers later. Check DHCP lease time on the router + NetworkManager renewal behavior. THIS IS LIKELY CONNECTED to the gateway-unreachable pattern (Pi config perfect, gateway unreachable, fixed by nmcli bounce — that's a DHCP/L2 renewal signature).
3. **WHICH device is the Fing agent** — MAC 88:A2:9E:3E:0E:7E. Determine if the Fing agent runs on cnjmesh1 (fing-agent.service is in cnjmesh1's install-map) or elsewhere, AND whether "offline" = just the Fing agent process died vs. the whole Pi/network dropped. Different problems. (cnjmesh1 install-map lists `fing-agent` — so this is very likely cnjmesh1 itself or its network dropping.)
4. Cross-reference: do the overnight outage times correlate with anything in `journalctl` on cnjmesh1 for that window? `journalctl --since "2026-08-02 22:45" --until "2026-08-03 04:15"` — look for network down/up, service restarts, OOM, scheduled job execution, cloudflared drops.

**Priority: HIGH.** A nightly scheduled event knocking the box/network offline would explain the recurring "down when I check it" experience and possibly the recurring gateway issue. Investigate as its own focused item. Likely the same root as the gateway-unreachable pattern — treat them as possibly-one-problem until proven otherwise.

### Aug 3 — SECOND monitor corroborates the overnight outage (UptimeRobot)
Independent confirmation of the Aug 2-3 overnight outage from a SECOND monitor:
- **UptimeRobot: meshview.cnjmesh.me DOWN at 10:33 PM Aug 2** (alert@uptimerobot.com).
- Fing: agent offline 11:03 PM Aug 2; back online ~3:56 AM Aug 3.
Two independent monitors, two services, same window = REAL outage, not a flaky sensor. Rules out monitor error.

**Refinements this adds:**
1. **Outage START is ~10:30-11:00 PM** (UptimeRobot fired 10:33, earlier than Fing's 11:03). Tighter window for log search: `journalctl --since "2026-08-02 22:20" --until "2026-08-03 04:15"` on cnjmesh1. Note 10:30pm is close to when we FINISHED working — check whether something we did, or a post-that-hour scheduled job, is implicated (vs coincidence).
2. **Charles already has real uptime monitoring** — UptimeRobot (meshview.cnjmesh.me, likely other endpoints too) + Fing (network). CRITICAL NEXT STEP: pull UptimeRobot's INCIDENT HISTORY — it logs every past down/up event with timestamps. If past incidents CLUSTER at consistent times (e.g. always ~10:30-11pm, back ~4am) → confirms a SCHEDULED cause and gives exact times to correlate against cron/timers. If scattered → different story. This historical data likely answers "is it scheduled?" faster than anything else. Also check what OTHER endpoints UptimeRobot monitors (malla? corescope?) — tells us if the outage is whole-box or per-service.

### Aug 3 — UptimeRobot INCIDENT HISTORY analyzed (meshview.cnjmesh.me, back to Mar 2026)
Charles pasted the full incident list (free tier, no export). Key analysis:

**1. STATUS CODES are the biggest tell — overwhelmingly 530 (a few 502, one T/O):**
- **530 = Cloudflare-specific "can't reach origin"** = the TUNNEL to cnjmesh1 was DOWN = network/connectivity problem, NOT meshview crashing. The VAST MAJORITY of incidents are 530. This strongly supports the network/tunnel/DHCP theory over any app-level cause.
- 502 (a few) = origin reached but bad gateway = service-level failure (different, rarer).
- This means: most "meshview is down" alerts = Cloudflare couldn't reach the box, i.e. cnjmesh1's outbound/tunnel dropped. Consistent with the recurring gateway-unreachable pattern + the nmcli-fixes-it signature.

**2. NO clean daily rhythm — but a clear ESCALATION / change-point ~July 20-22:**
- Mar/Apr: sporadic clusters. **May: almost nothing (system was healthy).** June: a couple.
- **July 20 onward: CONSTANT** — multiple incidents most days, several VERY long (Jul 20: 1d20h; Jul 23: 12h+9h; Jul 31: 12.5h; Aug 1: 14h; Aug 2: 5h).
- This escalation matches Charles's "humming until a couple weeks ago then hit a wall." SOMETHING CHANGED ~July 20-22. Correlate with: board swap timing, when mqtt-filter disk-fill started compounding, or a config/load change. **The May-healthy / July-broken contrast is a strong diagnostic anchor — find what changed between.**

**3. Recent long outages are NOT clockwork (varying start times: 10:33pm, 10:42am, 5:42am) →** NOT a simple nightly cron. More likely CONDITION-TRIGGERED (disk full / memory exhaustion / network flap) hitting at varying times. Fits the disk-fill root cause we JUST fixed — the long July 20-Aug 2 outages could largely BE the mqtt-filter disk saturation. **IMPORTANT: since mqtt-filter/disk is now fixed (Aug 2), watch whether these 530 outages STOP. If they do → disk was the cause. If they continue → separate network/DHCP issue remains.**

**REVISED read on the overnight-outage investigation:** it's very likely NOT a scheduled job (times vary). It's condition-triggered — and the leading condition (disk-full from mqtt-filter) is now resolved. So: MONITOR UptimeRobot over the next few days. If 530s stop → solved by the disk fix. If they persist → the residual is the network/tunnel/DHCP flap (the nmcli-bounce pattern), investigate that next. Fing move-off-cnjmesh1 still fine as a side project once stable.

### Aug 3 — TWO corrections from Charles (important, refine the outage analysis)

**CORRECTION 1 — I over-read the 530 codes.** Charles is right: UptimeRobot only sees Cloudflare + the URL; it has ZERO visibility into the Pi. So a 530 ("Cloudflare can't reach origin") appears whenever the Pi is unreachable FOR ANY REASON — network drop, disk full, memory exhaustion, crash, power, OR one of our own reboots. All look identical (530) from the outside. So 530 does NOT specifically indicate a network/tunnel cause — I incorrectly narrowed it to that. 530 = "origin unreachable, cause unknown from UptimeRobot's vantage." The actual cause must come from the PI'S OWN logs (journalctl for the incident windows), not the HTTP code. Walking back the "530s = network problem" inference.

**CORRECTION 2 — July 20 escalation aligns with the NEW PI DELIVERY.** Charles: the ~July 20 change-point ≈ when the replacement Pi arrived. This is a STRONG signal — the "healthy May → constant outages from July 20" timeline now has a concrete candidate: **the board swap introduced the instability.** Connects directly to the July 31 findings already logged (replacement board regressions: memory cgroups DISABLED, missing tooling baseline, Trixie dhcpcd→NetworkManager networking change). Reframes from "mystery escalation" to "what did the new Pi bring/fail-to-restore that the old one had right." Much more investigable.

**Revised synthesis:** The outages are real, escalated at the board swap (~Jul 20), and are condition-triggered (varying times). 530 codes are just the outside symptom, not a cause-pointer. Leading candidate causes, in order: (a) mqtt-filter disk-fill — NOW FIXED Aug 2, so watch if outages drop; (b) new-board regressions (cgroups/networking) from the July 31 findings — still unaddressed; (c) the network/DHCP flap (nmcli-bounce signature) — real but frequency unknown. To actually diagnose next incident: pull `journalctl` on cnjmesh1 for the exact UptimeRobot incident window and read what the PI says happened — that's the only source that knows the real cause. MONITOR whether the disk fix reduces frequency in the meantime.

### Aug 3 — CENTRAL FRAMING QUESTION (Charles, level-set) — put at TOP of the whole investigation

**Timeline (Charles's high-level account):**
1. Problems BEGAN while the ORIGINAL Pi was still running.
2. Original Pi DIED ~1 day after problems first appeared.
3. New Pi #1 — tried, didn't work out, replaced within 1-2 days.
4. New Pi #2 — current board, in place now.
**Critical fact: the problems PREDATE every board swap. They started on the original hardware.**

**The organizing question:** Are we seeing NEW problems with the new Pi, or are the ORIGINAL problems FOLLOWING US across hardware?

**Two hypotheses:**
- **(A) Problem follows the DATA/CONFIG, not hardware.** Issues started on original Pi + persisted across TWO swaps → most likely the cause traveled with what was CARRIED OVER and restored onto each board: Docker volumes (2GB Malla DB), compose configs, images, service defs. New hardware can't fix a problem that lives in restored state. Evidence FOR: Malla DB grew unbounded regardless of hardware; mqtt-filter log flood was a config issue that restores onto any board; disk-fill is data-driven not hardware-driven. These don't care what Pi they run on.
- **(B) Original problem killed original Pi; new Pis have SEPARATE issues.** Requires two unrelated causes overlapping (less parsimonious) but not impossible — e.g., original had failing SD card AND new board has cgroups/networking regressions.

**Most likely answer: BOTH, in layers.**
- Layer A (carried-over): DB bloat, mqtt-filter, service configs → would plague ANY board. **We've already been fixing these** (disk-fill RESOLVED Aug 2; retention+gunicorn PLANNED). This is probably the ORIGINAL problem, and it followed via the data.
- Layer B (new-board-specific): memory cgroups DISABLED, missing tooling, Trixie dhcpcd→NetworkManager networking baseline (the July 31 findings) → these are genuinely new-hardware regressions, STILL UNADDRESSED.

**Why this framing helps:** the two layers have DIFFERENT fixes and can be attributed separately. Don't conflate them. As we fix Layer A (disk done, Malla config next) and Layer B (cgroups/networking/tooling restore), watch which fixes actually reduce the outages — that TELLS us which layer was driving what. The UptimeRobot "healthy May → broken ~July 20 (new Pi arrival)" data is consistent with Layer B adding on top of a pre-existing Layer A.

**Practical upshot:** stop thinking "is it the hardware" as a single yes/no. It's "what carried over that we keep restoring (fix the data/config)" + "what did the new board fail to match from the original (restore the baseline: cgroups, tooling, networking)." Both tracks proceed; attribute by observing which fix moves the needle.

### Aug 3 — Open question: could the Tilly/KPR1 fork be contributing to the outages? (low prob, keep in mind)
Charles raised this, doesn't think so, wants it held loosely. Assessment:
- **Unlikely to be a DRIVER.** Timing: problems started on the ORIGINAL Pi (~mid-July) + escalated at the ~Jul 20 swap; the KPR1/Tilly bridge is one contained container. Its failure mode = stuck retrying an EXTERNAL broker (mqtt.aws.tillyandthefish.com), logging "MQTT: disconnected" — a self-contained symptom, doesn't inherently take down the Pi/network. A failed outbound connection is more likely a VICTIM of the network dropping than a cause of it (like Fing, it may be another symptom/detector, not a driver).
- **BUT one plausible minor-CONTRIBUTOR path, worth ruling out:** if the KPR1 bridge retries the failed external connection AGGRESSIVELY, it could (1) generate high-volume retry/error logs → with cnjmesh1 having NO log rotation, feeds the disk-fill pressure (same class as mqtt-filter/oktomqtt); (2) burn CPU/mem on retry loops on a memory-tight box. Neither = root cause, but either could add to resource pressure.
- **How to rule out (during health sweep):** check the KPR1 bridge's LOG VOLUME (is its json.log large / growing fast?) and its CPU/MEM footprint (`docker stats`). Quiet modest retrying = exonerated. Hammering + spewing logs = throttle or disable it until the Tilly integration is actually finished.
- **Weight: LOW probability driver; possible minor contributor; easy to check. Hold loosely, verify during sweep, don't fixate.**

---

### Aug 3-4, 2026 (Sonnet, Phase 1 Malla fix — IN PROGRESS, safe stopping point)

Executed Phase 1 of the get-well plan (docs/malla-fix-plan-cnjmesh1.md). Status:

**DONE + verified:**
- **Fresh DB backup taken** (Step 0): `/home/somog/backups/malla-backup-20260803.db` (2.7GB). Note DB had grown from 1.7GB (post-Tue VACUUM) to 2.7GB in ~1.5 days — confirms high ingestion rate.
- **Gunicorn IS working** (Step 3): after a detour to find the right mechanism. Key learnings documented below. Banner confirms Workers: 2 / Threads: 2, two worker PIDs booted (gthread worker type). Concurrency fix is in place.
- **Retention IS working** (Step 2): log confirmed "Data cleanup started for retention hours: N" firing hourly. Initially set 1440 (60d), then changed to **720 (30d)** after discovering the table is 8.4M rows and growing ~2.5M rows/4 days — 60d was too generous to help query speed.

**CONFIG MECHANICS LEARNED (important for future edits):**
- `MALLA_WEB_COMMAND` is consumed via Docker Compose variable substitution `${MALLA_WEB_COMMAND:-...}` in compose.yaml's `command:` line → must go in `/opt/stacks/mqtt/.env` (created it there). `.env` values do YAML substitution but are NOT auto-injected into containers.
- `MALLA_GUNICORN_WORKERS` / `MALLA_GUNICORN_THREADS`: Malla reads env vars as `MALLA_` + uppercased dataclass field name (confirmed in /app/src/malla/config.py line ~156). But these have NO `${...}` reference in compose.yaml, so putting them in `.env` did NOTHING (defaulted to 1 worker). FIX: added them to the `malla-web` service `environment:` list in compose.override.yaml — THAT injects them into the container. Now correctly 2 workers/2 threads.
- Current /opt/stacks/mqtt/.env: MALLA_WEB_COMMAND + (redundant) MALLA_GUNICORN_* lines. The gunicorn worker/thread values that ACTUALLY work are in compose.override.yaml.
- Backups made this session: compose.override.yaml.bak-preretention, .bak-pregunicorn, .bak-30day.

**KEY FINDING — gunicorn alone does NOT fix the slowness:**
- Post-gunicorn concurrency test: TWO concurrent requests + one single request all TIMED OUT. Logs show `Gateway statistics computed in 148.976s` — the query jumped from ~40-58s (earlier this week) to **149s**. Two gunicorn workers ran the same uncached heavy query in parallel, competing for CPU/disk, making BOTH slower.
- Root cause confirmed: **packet_history is now 8,419,912 rows** (up from 5.86M), oldest row Jul 2 (33 days — so 60d retention had deleted nothing). The query is slow because it aggregates over 8.4M rows on a memory-starved Pi. Gunicorn fixes concurrency but CANNOT fix a 149s query; it exposed/worsened it.

**RESOLUTION IN PROGRESS: 30-day retention (720h) now set** to cap the table smaller. BUT retention deletion + VACUUM not yet completed — that's the remaining work.

**STOPPED HERE (safe).** State is stable: retention 30d active (will auto-prune hourly overnight), gunicorn 2-worker running, backup safe, Malla still serving (slow on cold cache = the existing issue being fixed, nothing broken).

**PICK UP TOMORROW (Step remaining):**
1. Confirm overnight hourly retention started deleting rows >30d (check `docker logs mqtt-malla-capture-1 | grep cleanup` + row count via the python one-liner; expect < 8.4M and oldest row ~30d).
2. **Manual VACUUM to reclaim space + speed the query** (retention deletes rows but SQLite won't shrink the 2.8GB file or speed scans until VACUUM). Procedure: `cd /opt/stacks/mqtt && docker compose stop malla-capture malla-web`, then VACUUM via `docker run --rm -v mqtt_malla_data:/app/data ghcr.io/zenitram/malla:latest python3 -c "import sqlite3,time; c=sqlite3.connect('/app/data/meshtastic_history.db'); t=time.time(); c.execute('VACUUM'); c.close(); print(f'done {time.time()-t:.1f}s')"`, then `docker compose up -d`.
3. **Re-test query speed** (`curl -m 120 localhost:5008`). If 30d still too slow (still multi-minute), go SHORTER (14d/7d) — the plan anticipated this; the Pi may simply not handle 30d of this ingestion rate. Measure, then decide.
4. If satisfactory: verify public malla.cnjmesh.me, reassess malla-warmcache.timer (may be redundant/counterproductive with gunicorn), re-run collect-inventory.sh, update install-map.

---

### Aug 4, 2026 — ROOT CAUSE FIX APPLIED AND VERIFIED: mosquitto inbound bridge flood

**FIX APPLIED on cnjmesh1.** The three inbound bridges (oceancounty, liamcottle, sjmesh) that were pulling the entire US/global Meshtastic firehose (`msh/US/# in 0` / `msh/# in 0`) were rescoped to CentralNJ + NJ only:
```
topic msh/US/2/e/CentralNJ/# in 0
topic msh/US/NJ/2/e/CentralNJ/# in 0
```
Outbound bridges (meshtastic_public, meshomatic, sjmesh-bridge) left unchanged. Backup of pre-fix config preserved at `/opt/stacks/mqtt/config/mosquitto.conf.bak-preNJscope-20260804`. Sanitized (password-redacted) real config now committed to git at `cnjmesh1/configs/mosquitto-cnjmesh1.conf` — this is the first time the REAL bridge config (not just the generic .example) has been in git.

**Applied via:** Python script edit (not sed) → `docker compose restart mosquitto`. Restart initially showed ALL bridges failing ("Error creating bridge: Try again") — INCLUDING untouched ones (meshtastic_public, meshomatic) — which correctly signaled this was NOT a config problem but the SAME recurring cnjmesh1-local network/gateway issue (confirmed: `ping 10.0.0.1` = 100% loss). Fixed via the known remedy: `sudo nmcli connection down/up "C4Somogyi-24"` (NOT a router reboot — local to cnjmesh1's own connection state). After that, all bridges connected cleanly.

**VERIFIED WORKING — dramatic, immediate result:**
- Before: ~68,000 packets/hour, 99.5% foreign UNKNOWN_APP junk (GraveYard, SJMesh-wildcard, etc.)
- After fix: 1,849 packets in 5 min (~22,000/hr) — a ~3x reduction — and **100% of it is legitimate CentralNJ traffic** (confirmed via live topic query: all `msh/US/2/e/CentralNJ/...`, one `LongFast` packet, zero foreign channels).
- **This is the real root cause of the whole multi-week saga** — Malla slowness (149s queries), disk-fill, DB bloat (9.4M rows), and very likely the recurring outages/530s were all downstream of this flood. Gunicorn (working, 2 workers) and retention tuning (30d) were correct improvements but were treating symptoms of this.

**HOW WE FOUND IT:** Charles's insistence on finding "the offender" rather than just reducing retention led to querying top packet senders + portnum breakdown + topic breakdown by actual data (not assumption) — revealed 99.5% UNKNOWN_APP + foreign channel names (GraveYard) neither of us recognized. Traced to the 3 inbound bridge topic lines in mosquitto.conf. Cross-referenced against cnjmesh2's disciplined narrow-topic config as the "done right" template. Charles correctly pushed back multiple times on premature conclusions (git is NOT ground truth, only ~4 weeks old; don't guess at causes; find the actual offender not just cut packets) — this discipline is what got to the real root cause instead of another band-aid.

**NEXT STEPS (remaining):**
1. Monitor packet rate over the next hour+ to confirm it stays low and stable (not a temporary lull).
2. **VACUUM the DB** to reclaim space from weeks of foreign-junk accumulation (9.4M rows / 3.1GB) — Malla stopped, same procedure as before. This is now MORE valuable since the flood won't refill it.
3. Retention (currently 720h/30d) — now that the flood is stopped, 30d of REAL CentralNJ traffic will be tiny. Can stay at 30d or be extended; no longer urgent to shorten.
4. Re-test Malla query speed after VACUUM — expect dramatic improvement now that both the flood is stopped AND the table will shrink.
5. Watch UptimeRobot/Fing over coming days — if the recurring 530 outages/overnight drops STOP, this flood was very likely also the driver of those (broker/CPU/disk overload cascading into instability), not just Malla's slowness.
6. Update install-map-cnjmesh1.md to reflect the new bridge topic scoping.

---

### Aug 4, 2026 (cont.) — Junk purge + VACUUM COMPLETE. Malla speed DRAMATICALLY improved. Session summary.

**Precise junk removal (not waiting on retention aging):**
- Counted the split: 9,460,284 total rows, only 4,218,232 (45%) legitimate CentralNJ, **5,242,052 (55%) foreign junk** (GraveYard/SJMesh-wildcard/etc. accumulated before the bridge fix).
- `corruptedstack` (Discord) correctly predicted a first VACUUM (972.1s) would do little — confirmed: file stayed at 3.1GB, because almost none of the junk had aged past 30-day retention yet, so nothing had actually been deleted for VACUUM to reclaim.
- Deleted the 5,242,052 junk rows DIRECTLY by topic (`WHERE NOT (topic LIKE CentralNJ patterns)`) rather than waiting for retention — exact match to the pre-counted number.
- Second VACUUM: 531.5s. **File shrank 3.1GB -> 1.4GB** (confirms deletion + VACUUM approach works when there's real data to reclaim).

**FINAL SPEED VERIFICATION — dramatic improvement, confirms this was the real root cause:**
- Cold-cache query: **149s (pre-fix) -> 24.2s (post-fix)** — ~6x faster.
- Concurrent requests (warm cache): two simultaneous curls both returned in ~11-12s, running in PARALLEL (not blocking each other) — confirms gunicorn's 2-worker concurrency fix is genuinely effective now that the underlying query is faster too.
- 24s cold-cache is still not "fast" by normal web standards, but it's the best result all week and reflects the DB's HONEST size (4.2M real rows) rather than being inflated by the flood.

**SESSION SUMMARY — everything accomplished today, in order:**
1. Enabled Malla data retention (finally set to 30d after starting at 60d — see earlier entries).
2. Fixed gunicorn properly via `MALLA_GUNICORN_WORKERS`/`THREADS` in compose.override.yaml environment (not `.env` — that only works for `MALLA_WEB_COMMAND` via `${...}` substitution). 2 workers/2 threads confirmed running.
3. Investigated WHY gunicorn alone didn't fix things (149s query) -> led to root-causing the mosquitto inbound bridge flood via top-sender/portnum/topic breakdown -> found 3 bridges pulling `msh/US/#`/`msh/#` (entire US/global firehose).
4. Root-caused via comparison with cnjmesh2 (disciplined narrow-topic bridges) as the "done right" reference.
5. Rescoped all 3 inbound bridges to CentralNJ+NJ only. Verified with live data: packet rate dropped ~3x, topics went from majority-foreign to 100% legitimate.
6. Hit + fixed a RECURRING cnjmesh1 network issue mid-session (gateway unreachable, same nmcli-bounce fix as before) — confirms this pattern is still live and separate from tonight's fix.
7. Purged the pre-existing junk (5.24M rows) directly + VACUUMed -> DB 3.1GB -> 1.4GB.
8. Verified end-to-end: query 149s -> 24.2s, concurrency working correctly.
9. Charles observed Fing came back online unprompted after the fix — a good sign the flood was straining more than just Malla, though not yet proven causally.

**STILL TO WATCH / DO:**
- Monitor UptimeRobot/Fing over the next several days — if the recurring 530 outages stop, this flood was very likely the main driver of the whole-box instability, not just Malla slowness.
- 24s cold-cache is good but not great — if further speed is wanted later, the `data_retention_hours` could be tightened further now that it's ONLY real traffic (no rush, no longer urgent).
- Re-run collect-inventory.sh / update install-map to reflect the bridge topology fix.
- Consider whether corruptedstack's DB-cleanup notes (offered Aug 2) are still worth getting — may be redundant now given we found the actual flood, but could still contain useful Malla-specific tips.
- The recurring cnjmesh1 gateway-unreachable pattern happened AGAIN this session (network dropped mid-restart) — still unresolved as a standalone issue; the flood fix does not explain this specific symptom (bridges failed to connect due to genuine network loss, confirmed via ping). Keep this on the investigation list separately.

---

### Aug 4, 2026 (cont.) — PHASE 2 COMPLETE: deliberate cnjmesh1 reboot, full verification

Executed the deliberate reboot (Phase 2 of the get-well plan) with full pre/post verification.

**Pre-reboot baseline:** 11 days uptime, load avg 8.49, 1.8GB swap in use, 16 containers.

**Post-reboot checklist — full results:**
- **12 Docker containers:** all confirmed Up/healthy. `meshcore-hub-migrate` exited(0) is expected (one-shot migration container).
- **Systemd — zero failed units** (after fix, see below).
- **14 documented services** (cloudflared, graywolf-discord, meshview-db/web, Fing agent, all watchdog timers, weather bots, mesh_bot) — ALL confirmed active/running or correctly waiting on their timers.
- **Network/gateway:** confirmed working after initial recurring drop mid-session (see below).
- **Mosquitto bridges:** confirmed reconnecting correctly post-reboot — the CentralNJ/NJ scoping fix from earlier tonight persisted through the reboot (bind-mounted config file, as expected).
- **Web services:** meshview 302 (healthy), corescope 200, aprs-tnc-web 200, **Malla 200 in 11.1s** (even better than the 24.2s post-VACUUM result earlier — genuinely fast now).

**TWO real issues found and handled:**

1. **FIXED: `cloud-init-network.service` failing on EVERY boot since July 20** (matches the new-Pi-delivery date again). Root cause: `/etc/hosts` had the immutable (`i`) attribute set, so cloud-init's `cc_update_etc_hosts` module got `PermissionError: Operation not permitted` every single boot. Fixed: `sudo chattr -i /etc/hosts`. Origin of the immutable flag is UNKNOWN — not documented anywhere, no evidence it was deliberate. Verified NOT related to the recurring gateway/network-drop issue (cloud-init's own log explicitly stated network config was "unnecessary" for this stage — this was purely an /etc/hosts write failure, unrelated to actual network connectivity). Resolved via `systemctl reset-failed` + confirmed `systemctl --failed` now empty.

2. **DIAGNOSED, LOW PRIORITY, NOT YET FIXED: `meshcore-mqtt-kpr1-bridge` (Tilly integration) exited (143) after reboot, would not restart.** Root cause: hardcoded to `/dev/ttyUSB3`, which doesn't exist post-reboot — the device now enumerates as `/dev/ttyACM0` (confirmed via `lsusb -t` showing a `cdc_acm` driver device, and `dmesg` showing a `1a86_USB_Single_Serial` device on replug). This is a DIFFERENT USB serial chip/driver (CDC-ACM, native USB) than the CP210x bridge chips used by Digirig/KPC1 — explains why it never showed as ttyUSB. Stable `/dev/serial/by-id/usb-1a86_USB_Single_Serial_58EF089845-if00` path now confirmed to exist and point to ttyACM0 — should be used in the container's device mapping instead of the hardcoded ttyUSB3, so future reboots don't break it. NOT YET APPLIED (Charles deprioritized — KPR1/Tilly is the least important device right now). Do this whenever picking KPR1/Tilly back up: find its device mapping in the meshcore-mqtt-kpr1-bridge compose/run config, swap to the by-id path.

**USB inventory confirmed correct (Digirig + KPC1, both non-KPR1 devices fine):**
- Digirig (Graywolf PTT): serial `beb31e2f...` → `/dev/ttyUSB2` — confirmed via clean disconnect/reconnect in dmesg during manual replug test.
- KPC1/Client 1 (MeshCore companion): serial `0001` → `/dev/ttyUSB0` — confirmed via clean disconnect/reconnect in dmesg during manual replug test.
- KPR1 (Tilly integration): now on `/dev/ttyACM0` (see above) — was on `/dev/ttyUSB3` before reboot (unstable numbering, exactly the failure mode this class of bug produces).
- LoRa APRS (K2GIA-10): NOT a USB device — separate standalone LilyGO board on the network at 10.0.0.74, feeds cnjmesh1 via UDP syslog 1514, no physical connection to check.
- Powered USB hub: CONFIRMED WORKING CORRECTLY. Initial suspicion it was faulty was WRONG — traced via lsusb/dmesg that it cleanly detected and re-enumerated both devices actually connected to it (Digirig, KPC1) on manual replug. KPR1 connects DIRECTLY to the Pi, not through this hub, so the hub was never involved in the KPR1 issue.

**LESSON for future USB troubleshooting on this Pi:** any container/service with a hardcoded `/dev/ttyUSB*` or `/dev/ttyACM*` path is fragile across reboots on this box (multiple devices, enumeration order not guaranteed). ALWAYS use `/dev/serial/by-id/...` stable paths instead. Digirig and KPC1 already happened to land on stable-seeming numbers this time, but that's not guaranteed either — worth eventually migrating ALL device mappings (Graywolf PTT config, KPC1 bridge, KPR1 bridge) to by-id paths as a durability improvement, not just fixing KPR1 in isolation.

**Recurring network issue ALSO occurred mid-verification tonight** (separate from the reboot itself — happened during the mosquitto-bridge-fix testing, before the reboot): gateway unreachable, fixed via the known `nmcli connection down/up` remedy. Still unresolved as a standalone root cause — occurred AGAIN even after tonight's other fixes, so it is NOT solely caused by the mosquitto flood or the disk-fill (both already fixed). Remains an open, separate investigation.

**PHASE 2 STATUS: COMPLETE.** cnjmesh1 fully verified healthy post-reboot except the two items above (cloud-init fixed; KPR1 diagnosed but deprioritized). Ready for Phase 3 (full health-check sweep across all 3 Pis) next session.

---

### Aug 4, 2026 (cont.) — Health sweep continued: cnjmesh3 fully healthy + LoRa APRS bridge fixed (partially) + Graywolf/aprs-tnc-web confirmed

**cnjmesh3 (Part 1-3 of health-check plan): FULLY HEALTHY.**
- General health: load avg 0.03 (idle), 610Mi available RAM, 27Mi swap used, disk 18%. 15 days uptime, clean.
- Observer (`meshcore-packet-capture`): healthy, connected to all 4 brokers (letsmesh-us, letsmesh-eu, meshomatic, local@10.0.0.181), actively capturing.
- KPR2 (`meshcore-mqtt-bridge`): healthy, confirmed BOTH MeshCore AND MQTT connected ("MeshCore status update: connected - connected") — this CONFIRMS the KPR1 MQTT-disconnect issue is bridge/config-specific (Tilly's external broker), NOT a problem with cnjmesh1's local Mosquitto, since KPR2 connects to the same local broker fine.
- **PROACTIVE FIX: cnjmesh3 had NO Docker log rotation** (same unbounded-log risk that caused cnjmesh1's 30GB mqtt-filter disaster). Caught it BEFORE it became a problem — current logs were small (13MB, 39MB). Added `/etc/docker/daemon.json` (10m x3, same as cnjmesh1/cnjmesh2), `systemctl restart docker`, both containers recovered cleanly within 13 seconds, still healthy.
- cnjmesh3->cnjmesh1 ping: reachable (0% loss) but unusually high latency (440-827ms vs normal <10ms local LAN). Not investigated further — noted as an anomaly to watch, likely cnjmesh1 still settling from tonight's heavy work (reboot, VACUUM x2, bridge restarts). Not urgent.

**Part 5 (APRS, cnjmesh1): CONFIRMED HEALTHY.**
- graywolf-discord.service: active/running, 43min uptime clean, no errors (no recent log entries = normal, quiet channel, not a problem).
- aprs-tnc-web (nextjs_app + mysql_database): both up, 200 response in 53ms.

**Part 6 (LoRa APRS, cnjmesh1): PARTIALLY FIXED, end-to-end NOT confirmed — DEPRIORITIZED per Charles.**
- K2GIA-10 iGate (10.0.0.74): confirmed alive (401 on web UI = auth-required, working correctly; ping fails but that's expected, ICMP likely disabled on this embedded board — not a real problem).
- **REAL BUG FOUND AND FIXED: the lora-aprs-discord-bridge-v2.py script reads `os.environ.get(...)` directly with NO dotenv-loading logic** — the `.env` file in `/opt/lora-aprs-discord/` was never actually being read by anything. It's pure documentation unless manually sourced. This is why it failed with "DISCORD_WEBHOOK_LORA not set" on direct launch. FIX: must `set -a; source .env; set +a` before running the script (or wrap in a proper systemd unit with EnvironmentFile= directive — NOT YET DONE, would be the durable fix).
- Started the bridge manually this session (`nohup ... &`, disowned) — running, listening cleanly on UDP 1514, no errors.
- **Confirmed K2GIA-10's syslog config is CORRECT**: Server 10.0.0.181, Port 1514, Syslog enabled — verified via screenshot of K2GIA-10's own web UI. This rules out the config-mismatch theory that was the leading suspect.
- Attempted live end-to-end test via aprs-tnc-web ("Testing from k2gia" CQ message) — **INCONCLUSIVE.** No traffic appeared in the bridge log after send, but it's unclear whether the message was actually sent before the terminal/tail was interrupted, or genuinely didn't arrive. NOT resolved either way.
- **Charles's call: deprioritize LoRa APRS entirely for tonight** — reasonable, it's not core infrastructure. 

**CURRENT STATE if picking this back up:** bridge is running (manually started, NOT persistent across reboot — no systemd unit), env var bug is understood and fixable, K2GIA-10 config confirmed correct. Remaining unknowns: whether end-to-end delivery actually works (never conclusively tested), and building a proper systemd service so it survives reboots. Low priority — revisit only if/when Charles wants to circle back.
