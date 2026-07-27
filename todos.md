# CNJ Mesh — Open To-Dos

**For AI assistants:** This is the current, lean action list. Fetch this alongside `cnjmesh1-operations.md` at the start of a session — both are short. Only fetch `session-log.md` (long, narrative, full history) if you need the backstory on *why* something is the way it is.

**Housekeeping rule:** when an item is finished, delete it from this file — don't mark it "done" and leave it. If the fact that it's finished matters for later reference, a one-line note goes in `session-log.md` instead, not here.

*Split out from CLAUDE_CONTEXT.md on 2026-07-24. Items below were pulled forward from roughly two weeks of session notes — most are still genuinely open, but this was a first-pass triage, not a perfect one. Worth a skim to confirm nothing's stale or already done.*

---

### Active / Recent (July 27, 2026 session)

- **CoreScope `local` source (Observer feed) is genuinely unstable — root cause NOT found, needs real investigation, not a quick fix.** CoreScope's UI showed "No packets from local in 101 min" hours after the meshomatic fix + ACM pinning work, despite the underlying MQTT broker being fully healthy (independently confirmed: `meshcore-packet-capture` on cnjmesh3 was successfully publishing `MQTT: 4/4` to all brokers including `local`, and Mosquitto's own broker log on cnjmesh1 showed it actively receiving and forwarding those exact packets to subscribers in real time). So the packets ARE reaching the broker — CoreScope's own ingestor client just isn't maintaining a stable subscription to receive them.
  - **What was ruled out:** not a DNS/addressing issue in the simple sense. CoreScope's `local` mqttSource uses `mqtt://172.17.0.1:1883` (the Docker bridge gateway) instead of the LAN IP `10.0.0.181:1883` that the stable cnjmesh3 packet-capture client uses — this looked like the obvious fix (same category as the original 8-day CoreScope outage root cause), but switching CoreScope's config to `10.0.0.181:1883` and restarting made things WORSE, not better: connection attempts climbed to #6 with zero successful connects logged (previously it did eventually connect on the old address, just with instability). **Reverted back to `172.17.0.1:1883`** (backup used: `config.json.bak-20260726-2211`) — do not re-attempt the IP swap without a different theory first.
  - **What the actual failure looks like (on the OLD/current 172.17.0.1 address):** Mosquitto's log shows CoreScope's client connecting successfully (`CONNACK ... (0, 0)` = accepted, auth fine) under a fresh random client ID each time (`auto-XXXXXXXX`), then ~15 seconds later closing with **`disconnected due to protocol error`** — not a timeout, not an auth failure, a protocol-level issue. This repeats continuously with a brand new client ID each cycle. This smells like a bug or version mismatch between CoreScope's Go MQTT client library and this Mosquitto version/config, possibly related to QoS/keepalive negotiation — but this is a guess, not confirmed.
  - **Suggested next steps (not yet done):** (1) check CoreScope's own GitHub issues/changelog for "protocol error" or Mosquitto compatibility reports; (2) check Mosquitto's version (`docker inspect mosquitto --format '{{.Config.Image}}'`) against CoreScope's tested/supported broker versions; (3) try capturing a raw packet trace (`tcpdump` on port 1883 during a connect cycle) to see exactly which MQTT control packet triggers the protocol error; (4) consider whether the `meshcore/#` + `meshcore/+/+/packets` dual-topic subscribe in CoreScope's config is itself malformed in a way Mosquitto rejects only after the first PINGREQ cycle.
  - **Do not confuse this with the July 23 issue** (pingresp-not-received disconnect/reconnect loop) — that was a different symptom (timeout, not protocol error) from before this session's meshomatic config fix; whether they're the same underlying cause or two different bugs is unknown.



- **Audit `whorepeated` / path-lookup scripts for 2-char hex truncation** — KPR2's short path prefix `97` collides with WSMZ997-Fence, so the full `977f` is required to disambiguate. Confirm `/opt/whorepeated/merge_contacts.py` and `path_lookup.py` aren't truncating to 2 hex chars anywhere and misattributing KPR2-relayed packets. (Audit-flagged July 26.)
- **Explicit K2GIA-10 mobile RF-reach test** — CA2RXU firmware doesn't self-gate its own outgoing packets, so aprs.fi only ever shows `TCPIP*, qAC` (internet) and real over-the-air reach is unproven. Until the stuck RX board arrives, confirm reach with a mobile test: take a 433.775 LoRa APRS RX out and see if K2GIA-10 is actually heard, or arrange a cooperating listener. (Independent of the USPS-stuck RX board.)
- **Graywolf PTT device pinning (Digirig stable path)** — point Graywolf at `/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_beb31e2f33c6ef1186b171527a5e3baa-if00-port0` so PTT survives ttyUSB renumbering. Field could NOT be found in the 0.13.13 web UI (config lives in SQLite `/var/lib/graywolf/graywolf.db`). **Approach: (1) ask Graywolf Discord / check handbook for the correct 0.13.13 UI page FIRST, and confirm the app actually honors a by-id symlink; (2) direct SQLite edit is a LAST RESORT only** — the live service writes that DB, the schema is undocumented, and an edit can be overwritten or corrupt config. Do not lead with DB surgery.
- **Whip message-reach test (next APRS session)** — tonight's "did my message get out over the whip" was never cleanly answered because it was tested against Compy/KD2QED-7 in South Jersey (40+ mi, too far for a whip to fairly ack). Re-run it against **KB2EAR** (<1 mi, confirmed iGate KB2EAR-13): send a message, watch for the ACK in the Graywolf thread, and cross-check aprs.fi for the message packet carrying a `qAR,KB2EAR-13` path. That's the clean round-trip confirmation.
- **Is the 2m station digipeating, or only iGating?** iGate is confirmed (qAR paths + IGATED counter). Digipeater is a SEPARATE toggle on Graywolf's Digipeater page and its status is unconfirmed. Check the Digipeater page; if enabling, use fill-in (WIDE1-1 only) for a home whip — full WIDE2-2 keys too much and competes with the Icom for airtime.
- **APRStastic experiment (Meshtastic<->APRS gateway)** — afourney/aprstastic on GitHub. Needs a DEDICATED spare Meshtastic node (NOT CJG1/CJG2 — they're live MQTT feeders), ideally the spare Heltec V4, and probably its own Pi to stay off cnjmesh1's crowded USB bus. Two decisions before building: (1) OK with CNJ mesh node positions appearing on the public aprs.fi map? (2) which node + which Pi. Alpha software (0.0.1aXX) — hobby project, not production.

## Active / Recent (July 22-24, 2026 sessions)

- **Malla data retention not set** — `data_retention_hours` is commented out (defaults to 0/never) in `/opt/stacks/malla/config.yaml`. Database already 624MB and growing forever. Decide on a window (90 days / 2160 hours suggested) and set it.
- **Docker log-rotation cap only applied to Mosquitto** — the other 11 containers on cnjmesh1 still have unbounded logs. `/etc/docker/daemon.json` sets the default for *new* containers, but each existing one needs `docker compose up -d --force-recreate <service>` to actually pick it up.
- **cnjmesh1 kernel/OS upgrade** — running an older Trixie build than cnjmesh3. Not urgent, whenever convenient: `sudo apt update && sudo apt full-upgrade && sudo reboot`. (Also: do this roughly monthly on all 3 Pis going forward, not just cnjmesh1 — see cnjmesh1-operations.md's maintenance note.)
- **Malla CVE-2026-43980 (stored XSS)** — check if the running image predates the May 30, 2026 patch (`docker inspect mqtt-malla-web-1 --format '{{.Created}}'`), pull/recreate if so.
- **[OPTIONAL] peer-check symmetric debounce / maintenance-mode toggle** — recovery ("back online") currently fires immediately with no debounce, so a peer flapping right at the threshold can still emit down/up alert pairs (bit us mildly during the cnjmesh1 board swap). Options if it ever becomes a nuisance: (a) require N stable-up checks before declaring recovery, or (b) a maintenance toggle (e.g. `touch /opt/peer-check/silence-<ip>`) to mute a peer while deliberately working on it. Low priority — flapping only really happens during planned hardware work.
- **cnjmesh1 recurring WiFi "stuck" issue — root cause still unknown.** Two occurrences (night of July 22-23, morning of July 24) where the interface looks completely healthy (good bitrate/signal, TX counter incrementing, router shows it online, correct ARP on other devices) but zero traffic actually passes, including to the gateway. Fixed both times by forcing a reconnect (full reboot, or `nmcli con down/up`) — but why it happens isn't understood. Worth a lightweight recurring check if it keeps happening (see philosophy note in cnjmesh1-operations.md re: not over-building this).
- **Mosquitto log-fill rate — genuinely unresolved, don't trust the "slow accumulation" explanation.** Charles reports the disk filled to 100% again overnight after being cleared once — that's inconsistent with the ~2KB/30sec growth rate actually measured. Needs real sustained monitoring next time it happens, not a single spot-check.
- **Stale Fing Agent alerts** — Fing is alerting on the OLD (dead) cnjmesh1 board's MAC (`88:A2:9E:3E:0E:7E`), not the new board's. Deactivate/delete that old agent entry in the Fing app. Possible wrinkle: timing of a July 24 alert suggests Fing Agent software might still be a *live process* on the new board reporting under the old ID — worth checking with `ps aux | grep -i fing` before assuming it's purely stale/coincidental.
- **Fing Agent for the NEW board** — if still wanted, install/activate fresh (will register under the new correct MAC).
- **rename "APRS 2m (Graywolf)" → "Graywolf APRS 2M"** in peer-check's SERVICES config on cnjmesh2 and cnjmesh3 (Charles's preferred wording, cosmetic only).
- **cnjmesh1's own peer-check deployment** — confirmed NOT installed on cnjmesh1 (July 26). Only cnjmesh2 + cnjmesh3 run peer-check. cnjmesh1-down IS still detected (both peers watch it, plus UptimeRobot), but cnjmesh2/3 are each watched by only ONE peer instead of two — minor redundancy gap (a cnjmesh2 outage goes unreported only if cnjmesh3 is also down at that moment). To close: deploy peer-check on cnjmesh1 with PEERS=Node 2 + Node 3, NODE_LABEL=Node 1, and DOWN_THRESHOLD=12 to match the others. Small new install, not urgent.
- **USB drive for swap (optional, only if RAM pressure recurs)** — Charles is looking for an old spare thumb drive to test rpi-swap's file-based/hybrid swap mode as a lower-risk alternative to pushing zram size further. Not urgent, not needed unless the RAM pressure issue comes back.
- **Second RX-only ESP32 LoRa board** — ordered, in transit. Needed because K2GIA-10's iGate firmware doesn't self-gate its own outgoing messages to APRS-IS. **Also on order/in transit (as of July 27): 433MHz antennas for LoRa APRS, and cases for the LoRa APRS nodes** — once all three arrive, this is ready for final assembly/deployment.

## Carried over from mid-July sessions (status uncertain — verify before assuming still open)

- **CJG1 (Heltec V4) WiFi flapping** — was still actively flapping after a Mode change that fixed CJG2. Next test ideas noted: power supply/cable check, physical position, router channel (Auto → fixed 1/6/11).
- **Client 1 replacement** — known CP210x serial flapping issue, replacement with a RAK/WisMesh planned. Side idea: check if the old V3's case is intact — could refurbish instead of buying new.
- **Radio tuning (KPR1→ now N/A since retired, KPR2, Observer)** — apply the Capital District Mesh whitepaper §9.4.2 txdelay/rxdelay tuning. Neighbor counts never gathered, nothing started.
- **MeshCore regioning talking points** — prepared but never actually brought back to the NY/NE Mesh Discord.
- **Meshview coverage regression since July 21 Pi swap — confirmed RF-side, not bridging.** Used to see NYC/distant nodes (Rockefeller Center, Mt Kemble, etc.) regularly on meshview.cnjmesh.me; now rarely. Confirmed via comparison with MTX1's map (sbnj.meshview.comfx.com, ~1 mile away) that those distant nodes are RF-connected (neighbor/traceroute lines), not MQTT-bridged dots — so the gap is in what my own feeders (CJG1/CJG2) hear vs. before, not a bridge issue on the Meshview side. CJG1/CJG2 WiFi itself was confirmed NOT flapping (only phone↔node app connection flapped in the past — corrected assumption). **Corroborating evidence found same night: Malla's Gateway Diversity metric dropped from "much higher" historically to 1** — meaning almost all previously-diverse gateway sources (beyond my own local feeder) have stopped arriving at the broker. This points at a dead mosquitto bridge stanza or upstream broker outage rather than a feeder RF problem. **Next step:** check bridge connection status and configured stanzas: `docker logs mosquitto --tail 100 | grep -iE "bridge|connecting|connected|disconnect"` and `grep -iE "connection|address|topic|bridge" /opt/stacks/mqtt/config/mosquitto.conf` on cnjmesh1. Also verify which single gateway is the surviving "1" and confirm Malla's MQTT source didn't narrow after a restart.
- **KPN6 (roof-antenna node) MQTT is pre-configured for cnjmesh1 (10.0.0.181, user meshdev) but currently disabled (module toggle off).** Decision made: **leave it off** — Charles wants KPN6 to stay pure-RF, no internet uplink, even though enabling it (uplink-only, without touching downlink) would likely improve Meshview's distant-node coverage. Channels 3-7 (CentralNJ, CNJ-MQTT, SJMesh, CNJTest, CentNJ-MQTT) have MQTT downlink enabled too (MQTT→RF), which is the more RF-philosophy-relevant setting if this is ever revisited. Open sub-question, not yet answered: was KPN6 ever an active feeder during the period when more distant nodes were visible? If yes, its being turned off (separate from the Pi swap) may be the real explanation for reduced coverage, independent of the Malla bridge finding above.
- **Rotate `meshuser`/`meshdev` MQTT credentials** — flagged as overdue multiple times since mid-July (broker is public over WSS). Still appears unrotated.
- **Send the drafted Tilly outreach message** (LetsMesh/observer invite) — was blocked on credential rotation above; unclear if ever sent.
- **[MONITOR idea] Per-source freshness watchdog for CoreScope.** The meshomatic outage went unnoticed for ~64 h because nothing alerted on a stale *source*. Consider a watchdog (cnjmesh1, same pattern as the meshcore-mqtt-bridge + CoreScope ingest-stall watchdogs) that checks each CoreScope MQTT source's "last packet" age and pings #cnjmesh Discord if any source (local, meshomatic) goes stale past a threshold. CoreScope already surfaces this on the Observers page and via the in-app banner — the watchdog would just push it to Discord so it's not dependent on eyeballing the UI.
- **LetsMesh map discrepancy** — CNJ packets clearly flowing on the Packets page but node not appearing on the map itself. Never resolved, not investigated further.
- **KB2EAR-2 not appearing in CNJ packet feed** despite being ~772m away — flagged as odd, not investigated.
- **K2GIA-10 physical relocation upstairs** for antenna height — decided, not yet done (unrelated to any Pi migration, it's WiFi-based).
- **Tinkering project (explicitly low priority):** MeshCore ↔ Discord bidirectional bridge test, via MeshCoreDiscordBridge (Hude06).
- **mr-tbot's mesh-api** — flagged as a reference pointer for future cross-mesh bridging, never actually evaluated.

## Older items, likely stale or superseded — sanity-check before acting on any of these

*(These are from the July 13 session and predate several major changes — cnjmesh3's full setup, the KPR1 retirement, and K2GIA-10's arrival all happened since. Listed here only so nothing's silently lost; several are probably already done or no longer relevant.)*

- **[SOMEDAY, after software/config todos are closed out] Physical workshop organization.** Charles wants to get the physical workshop organized — cables, boards, adapters, cases currently scattered vs. a real system (labeling scheme, parts bins, inventory sheet). Explicitly deferred until after the current CNJ Mesh software/infrastructure todo list is closed out (per July 27, 2026 session) — logged here specifically so it isn't forgotten, per Charles's own request to "keep me honest."

- Explore deeper LetsMesh.net integration (see `docs/letsmesh-and-ozneteast-notes.md`)
- Invite more NJ MeshCore operators to the meshcore-nj-mqtt channel
- **Cross-mesh bridge with Tilly/LVMesh — UPDATE July 27, 2026 (afternoon): Tilly built a real raw packet bridge mode, reversing the earlier "not possible" finding above.** He forked/extended `meshcore-mqtt` at `https://github.com/Tilton53/meshcore-mqtt` (see `README.md` for full docs) and added a `packet_bridge` config block that solves every concern from the earlier investigation:
  - Genuine loop prevention via `dedup_ttl_ms` + a per-instance `dedup_db` (packet hash tracking, not just topic naming)
  - Hop-limited via `max_bridge_hops` so even multi-link chains can't loop forever
  - `tx_delay_min_ms`/`tx_delay_max_ms` (his config: 3000–5000ms) intentionally delays bridged retransmission so a faster native RF repeater path wins and the bridge copy gets deduped as redundant — bridge is a fallback, not competing with real hops
  - Behaves like an actual repeater retransmission, not a new packet under your own node identity — addresses the earlier "identity spoofing" concern
  - Observer/analytics functionality (the old visibility-only approach) is unchanged/unaffected — this is additive

  **Tilly's config (his side, "endpoint a"):**
  ```yaml
  packet_bridge:
    enabled: true
    link_id: backhaul-1
    endpoint_id: a
    peer_ids: [b]
    envelope_ttl_ms: 30000
    dedup_ttl_ms: 120000
    dedup_db: packet-bridge-a.sqlite3
    max_queue: 128
    max_bridge_hops: 2
    transmit_priority: 0
    tx_delay_min_ms: 3000
    tx_delay_max_ms: 5000
  ```

  **Mechanism clarification from Tilly (2:28 PM):** this does direct raw packet transmission between the two bridged nodes/devices themselves — NOT injection into the wider mesh directly. His suggestion: set the bridge node's own TX power LOW, so the effect is: bridge node receives via MQTT → transmits at low power → your actual repeater (KPR2/etc.) hears that low-power transmission locally and rebroadcasts it for real at normal power. Framed by Tilly as "an MQTT replacement for a repeater-to-repeater RF link" specifically for cases where two repeaters can't hear each other directly over RF — i.e. this is meant to patch a *specific missing RF link between two repeaters that should logically connect*, not a general internet-wide relay. Good conceptual model to keep in mind when configuring TX power on whichever device ends up running the CNJ-side bridge.

  **Strategic framing from Tilly (2:29 PM):** he sees this as a temporary stopgap for connecting separated mesh "islands" across the state while real RF repeater links get filled in over time — not a permanent replacement for RF. Notably self-obsoleting by design: because bridged packets always carry the tx_delay, once a real (faster) RF path exists between two areas, the mesh will naturally prefer that lower-latency native link over the bridge without anyone needing to manually retire the bridge config.

  **Confirmed from full README read (July 27, 2026):**
  - **✅ CRITICAL REQUIREMENT — RESOLVED July 27, 2026 (Opus session): KPR2 firmware CONFIRMED to support command 65.** KPR2's firmware is **`v1.16.0-07a3ca9` (Build: 06-Jun-2026)**. The raw-packet capability (`CMD_SEND_RAW_PACKET`, MeshCore PR #2543) was introduced in **v1.15.0** (released 2026-04-19); KPR2 is one full minor version newer, so command 65 is supported. **The firmware prerequisite for Tilly's packet_bridge is met.** How this was checked (for future reference — took several wrong turns first): the version comes from the repeater's serial text CLI, NOT the companion binary API. Steps that worked, all on cnjmesh3: (1) `docker stop meshcore-mqtt-bridge` to free `/dev/ttyACM1`; (2) `sudo apt-get install -y pipx && pipx install meshcore-cli`; (3) `~/.local/bin/meshcli -r -s /dev/ttyACM1 ver` — the **`-r` flag is REQUIRED** (repeater serial mode); without it meshcli tries companion-API mode and fails with "Are you sure your node is a serial companion?". Note also: plain `picocom`/raw-terminal `ver` returns "Unknown command" because the raw text needs the meshcli repeater-mode framing; and `infos` is a companion-mode command, not repeater — use `ver`/`board`/`role` for repeaters. **Remember to `docker start meshcore-mqtt-bridge` when done reading, or KPR2's normal MQTT feed stays down.**

  - Topic structure confirmed exactly: endpoint `a` (Tilly) publishes to `meshcore/bridge/v1/backhaul-1/a/tx`; endpoint `b` (CNJ) subscribes to that exact topic and publishes to its own `meshcore/bridge/v1/backhaul-1/b/tx`.
  - Bridge messages always force `QoS 1` and `retain=False` internally, regardless of the instance's general MQTT QoS/retain settings — not a configurable choice.
  - Confirmed stronger than Tilly's chat summary: *"Native RF arrival during delay cancels MQTT injection"* — if the real RF packet arrives before the jitter window (tx_delay) expires, the MQTT-injected copy is cancelled outright, not merely deduped after transmission.
  - This is a genuinely separate code path from the existing bridge's normal event/command topics (`meshcore/message/...`, `meshcore/command/...`) — packet_bridge is additive, doesn't change or risk the existing working setup.

  **=== IMPLEMENTATION PROGRESS — July 27, 2026 (late night Opus session) — CNJ side BUILT and DEPLOYED, but packet_bridge not yet confirmed ACTIVE in the running process. Pick up here. ===**

  **DONE this session:**
  1. KPR2 firmware confirmed `v1.16.0-07a3ca9` (06-Jun-2026) → supports command 65 (see resolved item above). Firmware prereq met.
  2. Built Tilly's fork into a NEW local image, WITHOUT touching the working one. On cnjmesh3: `cd ~ && git clone https://github.com/Tilton53/meshcore-mqtt.git meshcore-mqtt-tilly && cd meshcore-mqtt-tilly && docker build -t meshcore-mqtt:bridge .` — build succeeded. Confirmed the fork contains real packet_bridge code (`packet_bridge.py` module + integration in mqtt_worker.py, bridge_coordinator.py, config.py, main.py).
  3. Recreated the `meshcore-mqtt-bridge` container from the new `meshcore-mqtt:bridge` image, preserving ALL existing env vars and ADDING the packet_bridge block as env vars. Full working `docker run` is captured below. Endpoint=`b`, peer=`a`, link=`backhaul-1`, dedup_db=`packet-bridge-b.sqlite3`, all timing values matched to Tilly's (envelope_ttl 30000, dedup_ttl 120000, max_hops 2, tx_delay 3000–5000).
  4. **ROLLBACK path proven:** the old image `meshcore-mqtt:local` is untouched and still present. To revert to the pre-bridge state, re-run the container with `meshcore-mqtt:local` and drop all `-e PACKET_BRIDGE_*` args. (Full rollback command was worked out this session.)

  **CONFIRMED WORKING after deploy:**
  - Container comes up healthy on the new image. Serial to KPR2 (`/dev/ttyACM1`) connects, MQTT connects, KPR2's normal packet capture + status/event publishing all flow normally (verified live in mosquitto log: `meshcore/EWR/.../packets` streaming, `meshcore/status` + `meshcore/events/connection` publishing).
  - Config loads perfectly: `docker exec meshcore-mqtt-bridge python -c "from meshcore_mqtt.config import Config; c=Config.from_env(); print(c.packet_bridge)"` returns `enabled=True endpoint_id='b' peer_ids=['a']` etc. Validation passes. Instantiating a worker by hand (`MQTTWorker(Config.from_env())`) builds `_bridge_enabled=True` and `_bridge_topics={'meshcore/bridge/v1/backhaul-1/a/tx': 'a'}` correctly.

  **⚠️ OPEN BUG — packet_bridge NOT active in the actual running process (this is the thing to fix next):**
  - The `Subscribed to bridge topic:` log line (mqtt_worker.py ~line 767, fires in the on_connect callback right after the `meshcore/command/+` subscribe) NEVER appears in the running container's logs, even after a clean restart. So the live process is NOT subscribing to `meshcore/bridge/v1/backhaul-1/a/tx` — meaning it would not receive Tilly's packets.
  - Corroborating evidence: in mosquitto's log the bridge client connects as **`meshcore-mqtt-8da2a76f`** (random-suffix client ID) — NOT the `meshcore-mqtt-backhaul-1-b` bridge-naming pattern that mqtt_worker.py lines 211-212 construct when `_bridge_enabled` is true. So the *running* process built its MQTT client with bridge DISABLED, even though a fresh `Config.from_env()` in the same container returns bridge ENABLED.
  - The contradiction (config-loads-enabled vs process-ran-disabled) is NOT yet explained. Ruled out this session: env vars ARE present in the container (`PACKET_BRIDGE_ENABLED=true`, `PACKET_BRIDGE_PEER_IDS=a` confirmed via `docker exec ... printenv`-style check); launch cmd IS `python -m meshcore_mqtt.main --env` (confirmed via `/proc/1/cmdline`, no stray `--config-file`); no config file present in `/app`; installed package source matches the cloned source (`inspect.getsource` matched); `from_env()` path in main.py is clean (`elif env: config = Config.from_env()`, no mutation). A queue-size "1000 vs 128" lead was a RED HERRING (the 1000 was the MESHCORE component's queue in the status line, not the MQTT bridge inbox — do not chase that again).
  - **NEXT STEP to try:** the divergence means the running process's Config differs from a fresh `from_env()` despite identical inputs. Prime suspects not yet checked: (a) is there a stale `meshcore-mqtt-8da2a76f` client / an OLD container instance still running alongside the new one? `docker ps -a | grep meshcore` to check for duplicates — the random client ID pattern is suspicious and might be the OLD `:local` container that wasn't fully removed, still holding the feed while the new one's bridge half is what's silent. (b) Add `LOG_LEVEL=DEBUG` to the run and restart to see if on_connect logs anything about bridge setup being skipped. (c) Check whether the on_connect callback in the running mqtt_worker actually reaches the bridge-subscribe loop or returns early — add a temporary debug print. Start with (a); it's the cheapest and the random client ID strongly hints at a duplicate/stale container.

  **The full working `docker run` deployed this session (on cnjmesh3) — for reference / redeploy:**
  ```
  docker stop meshcore-mqtt-bridge && docker rm meshcore-mqtt-bridge && docker run -d --name meshcore-mqtt-bridge --restart unless-stopped \
    --device /dev/serial/by-id/usb-Espressif_Systems_heltec_wifi_lora_32_v4__16_MB_FLASH__2_MB_PSRAM__E8F60AC9DEB4-if00:/dev/ttyACM1 \
    -e MQTT_QOS=1 -e MQTT_RETAIN=true -e MESHCORE_ADDRESS=/dev/ttyACM1 -e MQTT_BROKER=10.0.0.181 -e MESHCORE_BAUDRATE=115200 \
    -e "MESHCORE_EVENTS=CONTACT_MSG_RECV,CHANNEL_MSG_RECV,CONNECTED,DISCONNECTED,LOGIN_SUCCESS,LOGIN_FAILED,MESSAGES_WAITING,DEVICE_INFO,BATTERY,NEW_CONTACT,ADVERTISEMENT" \
    -e MQTT_USERNAME=meshdev -e MQTT_PASSWORD=large4cats -e MQTT_TOPIC_PREFIX=meshcore -e MESHCORE_CONNECTION=serial -e MESHCORE_TIMEOUT=30 -e LOG_LEVEL=INFO -e MQTT_PORT=1883 \
    -e PACKET_BRIDGE_ENABLED=true -e PACKET_BRIDGE_LINK_ID=backhaul-1 -e PACKET_BRIDGE_ENDPOINT_ID=b -e PACKET_BRIDGE_PEER_IDS=a \
    -e PACKET_BRIDGE_ENVELOPE_TTL_MS=30000 -e PACKET_BRIDGE_DEDUP_TTL_MS=120000 -e PACKET_BRIDGE_DEDUP_DB=packet-bridge-b.sqlite3 \
    -e PACKET_BRIDGE_MAX_QUEUE=128 -e PACKET_BRIDGE_MAX_HOPS=2 -e PACKET_BRIDGE_TRANSMIT_PRIORITY=0 -e PACKET_BRIDGE_TX_DELAY_MIN_MS=3000 -e PACKET_BRIDGE_TX_DELAY_MAX_MS=5000 \
    meshcore-mqtt:bridge
  ```
  Note: `PACKET_BRIDGE_DEDUP_DB=packet-bridge-b.sqlite3` is currently INSIDE the container (ephemeral — wiped on recreate). For permanent use, add a `-v` mount to a host path so dedup state persists. Deferred until the bridge is confirmed active. Also: `PACKET_BRIDGE_PEER_IDS` is comma-separated (code does `.split(",")`); single peer `a` is correct for the 2-endpoint CNJ↔LVMesh link.

  **Firmware check attempted July 27, 2026 (evening) — inconclusive, stopped due to a newly-discovered SEPARATE instability.** Tried triggering a fresh `device_query` command via MQTT to get KPR2's firmware version/build. Command was published successfully but no response ever came back on `meshcore/device_info`. Root cause investigation found: KPR2's **serial connection itself** (not the MQTT side) is cycling — `docker logs meshcore-mqtt-bridge` showed a full stale→disconnected→recovery→reconnected cycle taking ~40 seconds, right around the time the query was sent. Command likely got dropped mid-recovery. **This is a different, previously undocumented instability from the earlier CoreScope `local` source issue** — that one was MQTT-broker-side; this is the bridge's serial link to KPR2 itself going stale periodically. Not yet root-caused. **Next attempt should either:** (a) retry the device_query a few times in a row to beat the timing window, or (b) connect directly to KPR2 via a MeshCore CLI/BLE session (bypassing the MQTT bridge entirely) to read firmware version, sidestepping this instability altogether. Stopped for the night rather than continuing to fight two separate flaky layers back-to-back.



  1. Requires a serial MeshCore connection (per README: "Requires serial MeshCore connection") — confirm which physical companion node on CNJ's side will run this (likely reuses the existing cnjmesh3 MeshCore companion setup, or a dedicated one — TBD).
  2. Mirror Tilly's config with these changes: `endpoint_id: b`, `peer_ids: [a]`, and a **unique** `dedup_db` filename (e.g. `packet-bridge-b.sqlite3` — must NOT match Tilly's filename/instance). `link_id: backhaul-1` must match exactly on both sides. `envelope_ttl_ms`, `dedup_ttl_ms`, `max_bridge_hops`, `tx_delay_min/max_ms` should also match Tilly's values (or be explicitly agreed if changed) since they govern shared behavior between both ends.
  3. Add this `packet_bridge` block to the relevant `config.yaml` (likely on cnjmesh3, alongside the existing `meshcore-mqtt-bridge` config — needs confirming whether this is the same container/config or a separate instance).
  4. Test with both sides live, watch for: successful cross-link message delivery, no duplicate/looping messages, and confirm RF-preferred routing behavior (i.e. a message that arrives via real RF repeater hop suppresses the bridged copy as expected).
  5. Read `https://github.com/Tilton53/meshcore-mqtt/blob/main/README.md` in full before implementing — this summary is based on what Tilly pasted in chat, not a full read of the repo's docs.



- NWS alerts — verify behavior on a real/live alert
- meshcore-packet-capture health check / auto-restart on Observer disconnect
- Node tagging in MeshCore Hub (KPR2, Observer)
- Discord server security review
- APRS Discord silent-alert monitor
- **Alfa antennas (2x, in transit as of July 27):** one for the **T-Deck** (KPN2, LilyGo T-Deck Plus, hasn't been used in a while — this revives that item), one for a **MeshCore companion** node. Still needs an SMA→RP-SMA adapter for at least one of these (was the original blocker on the old "T096 + Alfa mobile setup" note — confirm if still needed once antennas arrive and connector types are checked).
- Broker-to-broker bridging with LV Mesh / SJ Mesh for meshcore-nj-mqtt
- Cross-mesh bridge via mesh-api (duplicate of the item above, kept for visibility)
- MeshOmatic relay script
- KPR2 watchdog
- Remove dead MeshOmatic section from mosquitto.conf (verify first)
- Remove dead meshshadow section from cloudflared config (verify first)
- Rotate Discord webhook URLs (low priority)
- Rotate MeshOmatic password (low priority)
