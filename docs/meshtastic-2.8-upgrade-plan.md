# Meshtastic 2.8 upgrade plan (stay on Long Fast)

Written Fri Oct 30 2026 from a full repo pass plus web research. Goal: move CNJ's three Meshtastic gateways to 2.8.x **once it is beta and the tools are ready**, without changing the radio preset (Long Fast, 906.875 MHz, slot 20) and without breaking what reads our data.

Tags: [V] verified from repo or pasted output · [S] from a web source (listed at the bottom) · [I] inference, not tested · [?] unknown, must be checked.

**Nothing here has been done yet.** No node, broker or tool was touched when this was written.

---

## 1. Bottom line

1. **Do not upgrade anything to 2.8 today.** The newest build is 2.8.1, labeled Alpha; Meshtastic's own post says it "isn't ready for wide deployment", and 2.8.0 was revoked over a signing flaw. [S]
2. **2.8 does not move us off Long Fast on its own.** A node upgraded from 2.7 keeps its preset. The Long Turbo default only hits a brand-new US node set up from its own screen (and the Android app 2.8.3 does the same for factory-fresh nodes). [S] The risk is in a full erase and reflash, where the node comes back "fresh". Section 6 covers that.
3. **The biggest breakage is node IDs, not the preset.** From 2.8 the node number comes from the public key instead of the MAC. An upgraded node gets a **new ID**, and nothing links it to the old one. [S] Our gateways are hard-coded by ID in several places (section 4).
4. **JSON uplink is gone in 2.8** (release notes: JSON library removed from firmware builds). We found nothing local that reads the JSON topic. [S, V grep]
5. **Order of work:** fix and update the tools first (safe on 2.7 today), then wait for a beta, then bench, then one gateway at a time with a soak week between.

---

## 2. What we actually have [V unless tagged]

Only Meshtastic is in scope. **MeshCore is untouched by 2.8:** CoreScope, MeshCore Hub, mesh-discord-shim, KPR1/2/3, KPC1/2, the Observer, the weather bot (`meshcore-bot`, and `nws_mesh_broadcast.py`, which uses `meshcore-cli` on `/dev/kpc1`). So are Graywolf/APRS, K2GIA-10 and cloudflared.

| Node | Hardware | Node ID | Where / how it connects | Notes |
|---|---|---|---|---|
| **CJG1** | Heltec V4 | `!0aca423c` | 10.0.0.18, Wi-Fi. Uploads to **cnjmesh2** (anonymous). TCP 4403 is used by `meshing-around` (`mesh_bot.service`, cnjmesh1). | Carries the 7 AM report and NWS alerts on CentralNJ via the bot. Wi-Fi flapping history (Sep). Firmware [?] |
| **CJG2** | Heltec V3 | `!9ea3e8d4` | 10.0.0.234, Wi-Fi. Uploads to **cnjmesh1**. | Encryption on, JSON on, channels LongFast (uplink), CentralNJ and SJMesh (up+down). Firmware **2.7.24.472b14c** [V, app Oct 30; app offers stable 2.7.26] |
| **KPN6** | ESP32-S3 (exact board not recorded) [?] | `!69841fe0` | Roof node, USB to cnjmesh1 (`/dev/ttyACM1`, by-id `usb-Espressif_USB_JTAG_serial_debug_unit_90:70:69:84:1F:E0-if00`). MQTT on, client proxy off. | Encryption off (publishes decoded), JSON on, map reporting with consent on, precise position on CentralNJ. **2.7.25.104df5f** [V, app Oct 30], on Wi-Fi at **10.0.0.202** [V], on external power at 4.35 V (app shows a plug icon and no battery percent; Charlie says it also has a battery). Has Wi-Fi (Charlie, Oct 30: he recently changed this; older notes saying otherwise are out of date), so it can be reached over the network: record its IP. |

Retired from Meshtastic (not in scope): KPN2 (now MeshCore KPC2), KPN1 (now MeshCore KPR3). A spare Heltec V4 is mentioned in the Aug session log and todos (APRStastic idea) [?: confirm it still exists; it would be the bench node].

Radio on all three [V Oct 25]: 906.875 MHz, slot 20 (auto), Long Fast. CentralNJ key `f+WQoPgd06tk0n3Kl2bUmNVGO7TcPkxchPD6QqMkYRg=`. Full MQTT and channel settings per node: `docs/meshtastic-gateway-mqtt-settings.md`.

**History worth knowing:** on Aug 28 and again Sep 2 we looked at 2.8.0 and decided to stay on 2.7.x (node-ID change, opt-in telemetry and position, bootloop risk). Nothing in the 2.8 picture has gotten simpler since; what has changed is that 2.8.1 fixes the signing flaw and the tool ecosystem is starting to add 2.8 support.

---

## 3. What 2.8 changes that touches us

| Change | Source | Effect on us |
|---|---|---|
| Node number = `crc32(public key)`, adopted on first 2.8 boot. Not reversible by downgrading. | meshmonitor.org identity page, 2.8.1 notes [S] | New ID for every upgraded node; old ID goes silent. See section 4. |
| Preset: fresh US setup from the device screen defaults to LongTurbo. Upgrades keep the old preset. CLI setup stays LongFast. | 2.8.1 notes, NoDak, Android PR #7244 [S] | Safe on upgrade. Dangerous only after a full erase if region is set from the screen or the Android app. |
| Position and telemetry broadcasts are **off after upgrade**; precise position not allowed on public (known-key) channels, capped near 700 m. | NoDak, 2.8.1 notes [S] | Telemetry/position graphs for our gateways go flat. KPN6's precise position on CentralNJ will be coarsened. Whether our published CentralNJ key counts as "known-key" [?]. |
| MQTT JSON library removed from firmware builds; `json_enabled` ignored. | 2.8.1 notes, Camillia ticket [S] | `msh/US/2/json/CentralNJ/#` goes quiet. Our `json/CentralNJ` bridge line becomes dead (harmless). |
| XEdDSA packet signing. Default policy Compatible: unsigned packets accepted. 2.7 nodes cannot sign. 2.8.1 also signs the OK-to-MQTT flag. | NoDak signing page [S] | Mixed 2.7/2.8 works. **Do not set Strict or Balanced** while any relay is still 2.7. |
| Pre-hop drop: packets with missing or invalid `hop_start` (very old firmware) are blocked. | 2.8.1 notes [S] | Only affects neighbors on ancient firmware; may shrink what we hear slightly. |
| Filesystem format changed; reconfigure expected; bootloop means full erase + flash. | NoDak, 2.8.1 notes [S] | Have every setting written down before flashing (section 6). |
| Long names capped at 24 bytes; NodeInfo MAC shows `00:00:00:00:00:00` for others. | NoDak, MeshMonitor [S] | Cosmetic. CJG2's long name (`Central Jersey GW2 \| cnjmesh.me (MQTT)`) is over 24 bytes and will be cut; CJG1's (`Central Jersey GW1 \| cnj`) is exactly 24 characters. |
| "Zero-hopping all MQTT downlinking" is on the 2.8.X later list. | 2.8 punchlist [S] | Could change how SJMesh and public traffic is retransmitted on our RF through CJG1/CJG2 downlink. Watch for it; effect unverified. |

**Why the ID now comes from the key [S, added Oct 30]:** no single official explanation exists. The pieces: (1) the original request (firmware discussion #5007, Oct 2024) said a MAC-based ID causes key mismatches when a node is reset without its key backed up, and proposed tying the ID to the key; (2) Meshtastic's security page says deriving the node number from the key and signing broadcasts narrows identity-spoofing risk, and a signed first-contact NodeInfo must have `crc32(public key)` equal to the sender's node number. Maintainers disagreed in the thread ("likely to cause more issues"; stale NodeDB entries others cannot reconcile; later "in discussion for 2.8"). **Consequence: a new key means a new node number** (security page; docs PR #2732). A factory reset, full erase or key regeneration therefore changes a node's ID, which the old MAC-based ID did not. A normal firmware update should keep the key [I].

2.8 status [S]: 2.8.1 is the newest tagged build (Alpha, Oct 1). A 2.8.2 exists as nightly. The punchlist (issue #10462) lists packet signing, regions and presets as "implemented but not yet tested", and gives no beta date. Recent bugs show the MQTT uplink path is still being fixed: issue #12115 (PKI direct messages from RF clients not uplinked to MQTT in 2.8.2, closed Oct 14 as fixed by #12110).

---

## 4. What breaks, and the fix

Severity: **High** = silently stops doing its job. **Med** = wrong or empty data. **Low** = cosmetic.

| # | What | Where | Why it breaks | Fix | When |
|---|---|---|---|---|---|
| 1 | **sjmesh-relay outbound allowlist** | cnjmesh1, `/opt/sjmesh-relay/relay.py`; repo `cnjmesh1/sjmesh-relay/relay.py`; `test_relay_logic.py` | Outbound only forwards topics ending in `!9ea3e8d4,!69841fe0,!0aca423c` (`DEFAULT_OUR_GATEWAYS`). An upgraded gateway publishes as a new ID, so its CentralNJ traffic stops reaching SJMesh and the #mesh-relay Discord, with no error. **High**, but it fails safe (no loop). | After each upgrade add the new ID to the list (the `OUTBOUND_GATEWAYS` env var overrides it; check `systemctl cat sjmesh-relay.service` on cnjmesh1 for where it is set) and restart the service. Keep the old ID in the list for a week (harmless). Update the repo copy and test file. | Same day as each node |
| 2 | **Blocked flood nodes escape the blocklist** | same file, `BLOCKED_TOPICS` (`!699a9390`, `!698574b0`, `!db51bb30`) | If any of those nodes upgrades to 2.8, it gets a new ID and the block no longer matches. | Nothing to do now. `ingest-rate-watchdog` ("one node over 50% of an hour's traffic") is the net that catches it; add the new ID to the block list if it floods. | Ongoing |
| 3 | **Malla (both hosts)** | cnjmesh1 (`mqtt-malla-*`, port 5008) and cnjmesh2 (`malla-*`, port 8080), image `ghcr.io/zenitram/malla:latest` | Keys on node ID: upgraded gateway shows as a brand-new node, old one ages out, history splits, gateway-diversity count wobbles. I found no merge feature in Malla and no statement of 2.8 support in what I could read [?]. **Med** | Update Malla first (already planned for the maps watermark and CVE-2026-43980) so any 2.8 fixes ride along; test on the bench (section 5) before trusting it. Accept the split history; it ages out under retention. | Phase 0 (update), Phase 1 (test) |
| 4 | **Meshview** | cnjmesh1 `~/meshview` (units `meshview-db`, `meshview-web`), v3.0.5 [V Sep] | Same ID problem, plus it was behind as of September (running 3.0.5 while 3.0.7 was current); its protobufs get refreshed upstream. Update needs Alembic and about 1.2x the DB size free. **Med** | Update to the current release first (DB backup, then `git pull`, `pip install alembic`, restart both units). Check `[mqtt] topics` in `config.ini`. | Phase 0 |
| 5 | **meshing-around bot** (07:00 report, NWS alerts on CentralNJ) | cnjmesh1 `/opt/meshing-around`, connects to CJG1 over TCP 10.0.0.18:4403; pinned to upstream commit `4dc6bef` (Mar 25) with our `scheduler.py.diff` | Talks to CJG1 through the Python `meshtastic` library. A library older than 2.8 may fail or misread a 2.8 node [?]; I found that the library's protobufs-v2.8.0 PR exists but could not confirm it is released. `favoriteNodeList`, ignore lists and sentry lists are empty in our config, so no ID entries to fix. **High for the morning report** | Before CJG1 moves: update the bot's Meshtastic library, re-apply `scheduler.py.diff`, and test against a bench node on 2.8. **CJG1 goes last.** | Phase 0 prep, test in Phase 1 |
| 6 | **MeshMonitor** | cnjmesh1 (docker volume `meshmonitor_meshmonitor-data` is in the backup script; port 8081 per notes) | The repo does not say which node it connects to or whether it is still running [?]. Upstream has 2.8 handling (v4.16.0-rc3: flags renumbered nodes, "Merge history…" with dry run, warns when a 2.8 node goes silent). | Check `docker ps` for it. If running, move to a 2.8-aware release first; after each upgrade use its merge to keep history. | Phase 0 |
| 7 | **Telemetry and position go flat** | Malla, Meshview graphs, nodes list | Defaults are off after upgrade. | Re-enable on purpose per node (device telemetry; position on the channels you want). Decide KPN6's position policy again, since precise is no longer allowed on public channels. | Day of each upgrade |
| 8 | **JSON topic** | cnjmesh1 bridge `msh/US/2/json/CentralNJ/# out`; MQTT Explorer plan | Dead once all three are on 2.8. No local reader found. Anyone on the public broker reading our JSON loses it [?]. | Leave the bridge line until all three are on 2.8, then remove it in a deliberate, backed-up change (OK first). MQTT Explorer: do the JSON exercise now, while it works. | After last node |
| 9 | **Hard-coded IDs in docs** | `docs/*`, `todos.md` canary item (`!9ea3e8d4`, `!0aca423c`, `!69841fe0`), Malla queries, MQTT client IDs | They name gateways by ID. | Keep a small old-to-new ID table in section 9 of this file and note the change in `docs/meshtastic-gateway-mqtt-settings.md`. | Day of each node |
| 10 | **Public website** | `website/cnjmesh-me/getting-started.html` says "flash the latest firmware", then OK to MQTT and CentralNJ | Once 2.8 is stable, newcomers who set the region from the screen or Android get LongTurbo and hear nothing. | Add one sentence: CNJ uses Long Fast; if you hear nobody, set the preset to Long Fast. Also say node names are cut to 24 bytes. | When 2.8 goes stable |
| 11 | **Meshtastic public map** | KPN6 map reporting | One third-party ticket says 2.8 sends anonymous presence only [S, single source, [?]]. | Look at KPN6's map entry after it upgrades. | Phase 2 |
| 12 | **Gateway diversity and node counts** | Malla/Meshview stats | Neighbors and SJMesh upgrading at their own pace will create new IDs and ghost entries. | Expect noise; do not chase it. | Ongoing |

**Not affected [V]:** Mosquitto itself (no protocol change; client ID is the node ID, credentials unchanged), `mqtt-filter` (retired on cnjmesh1; stopped on cnjmesh2), cloudflared, MeshCore tooling, APRS tooling. `mesh-mqtt-pg-collector` and Grafana: which topics the collector subscribes to is not in the repo [?]; check `config.yaml` in `/home/somog/mesh-mqtt-pg-collector` on cnjmesh1 and see if it reads Meshtastic topics.

---

## 5. Timeline: gates, not dates

Meshtastic has not published a beta date. The plan below is keyed to events. Charlie's hope (wait for 2.8.x to reach beta and let fixes land) is the right trigger.

### Phase 0 — prep, safe on 2.7 (start this weekend, about 2 weeks, one change at a time)
Nothing here needs 2.8. All of it is a good idea anyway.

| Step | Host | What |
|---|---|---|
| 0.1 | Phone | Read the firmware version on CJG1, CJG2 and KPN6 (device Config / About). Write them in section 9. |
| 0.2 | Phone | Screenshot every settings screen per node (device, LoRa, MQTT, network, all channels with uplink/downlink icons). Export config from the app if your version offers it. Same as the Oct 25 captures in the gateway settings doc. |
| 0.3 | cnjmesh1 | Back up before touching tools (`scripts/cnjmesh1-backup.sh` and `cnjmesh1-extra-backup.sh` per `docs/backup-guide.md`). |
| 0.4 | cnjmesh2 then cnjmesh1 | Update Malla (existing plan in todos: note image digest, back up DB, pull, watch for migration errors). cnjmesh2 first. |
| 0.5 | cnjmesh1 | Update Meshview to current. |
| 0.6 | cnjmesh1 | Find out whether MeshMonitor runs, what it connects to, and update it. |
| 0.7 | cnjmesh1 | Check what `mesh-mqtt-pg-collector` subscribes to. |
| 0.8 | cnjmesh1 | `systemctl cat sjmesh-relay.service` to see where `OUTBOUND_GATEWAYS` is set, so changing it later is a one-line edit. |
| 0.9 | Phone/PC | Optional: move all three to **2.7.26** (newest 2.7, Beta-labeled) so every node starts from the same known baseline. KPN6 first, 2.7.25 to 2.7.26. |
| 0.10 | PC | MQTT Explorer session on `msh/US/2/json/CentralNJ/#` while JSON still exists. |
| 0.11 | Repo | Confirm the bench node (spare Heltec V4?). If none, decide whether to buy one cheap board. |

### Gate A — go/no-go to start Phase 1 (all must be true)
- A 2.8.x release is labeled **Beta** (not Alpha) on the firmware releases page.
- It has been out at least **2 weeks** with no revoke or "do not use" note.
- No open firmware issue about MQTT uplink or downlink regressions on ESP32 gateways (search "2.8 MQTT" on `meshtastic/firmware`).
- Malla, Meshview and MeshMonitor are on their latest, and none lists a known 2.8 problem.
- The Python `meshtastic` library has a release with the 2.8 protobufs.

### Phase 1 — bench (1 to 2 weeks)
Flash the bench node with the Beta; set it **LongFast on the primary channel with uplink to cnjmesh1**. Leave the CentralNJ channel off so nothing from the bench leaves the building (only CentralNJ is bridged out; LongFast uplink stays on the local broker). Pass/fail list:

1. After flashing, LoRa shows **Long Fast, 906.875 MHz, slot 20**. Note the new node ID.
2. Bench node and a 2.7 node exchange text both ways over RF.
3. Bench packets appear in **Malla (cnjmesh1 and 2)** and **Meshview** as decoded text, not `UNKNOWN_APP`.
4. Uplink works with both Encryption on and off (CJG2 is on, KPN6 is off).
5. A PKI direct message from an RF node to the bench node is uplinked (issue #12115 class of bug).
6. With JSON enabled in the node, confirm nothing appears on the json topic (expected).
7. Telemetry and position are off by default; re-enable and confirm they show up in Malla.
8. `meshing-around` (a test instance or a short supervised run) connects to the bench node over TCP 4403 and answers a command.
9. **Key and ID behavior:** note the node ID, export config, erase and restore it, and check whether the ID comes back. This shows whether a config restore preserves the key. Then the **recovery drill:** erase, reflash 2.7.26, restore settings. Does the node get its **old MAC-based ID back**? The identity page says downgrading does not restore the old number [S], but I have not seen what a full erase does [?]. This decides whether rollback is clean.
10. **Erase-and-restore on 2.8:** set the preset to LongFast explicitly and confirm it did not land on LongTurbo.

### Phase 2 — canary: KPN6 (1 week soak)
Why first: USB-attached to cnjmesh1 for power and serial, no bot depends on it, easy to reach. Do it in the evening, not near an active NWS alert. Section 6 runbook. After: update relay list, check Malla/Meshview, look at the map entry, watch `ingest-rate-watchdog` and relay logs for 7 days.

### Phase 3 — CJG2 (1 week soak)
Feeds cnjmesh1, carries CentralNJ and SJMesh downlink. Same runbook. Verify a CJG2 test message reaches #mesh-relay (it did on Oct 25 after the key fix).

### Phase 4 — CJG1 (last)
Feeds cnjmesh2 and carries the bot connection. Update the bot first (item 5), schedule it outside 6:30 to 7:30 AM and outside severe weather, and test the next 7 AM report.

### Phase 5 — cleanup (after all three)
Remove the dead `json/CentralNJ` bridge line (OK first, backup, Python edit, as in `docs/mqtt-topology-and-landmines.md` section 6). Update the website sentence. Remove old IDs from the relay list. Update docs and `CLAUDE_CONTEXT.md`.

**Stop rules:** any build revoked or replaced mid-soak, relay outbound count drops to 0 after a node is back up, Malla shows the node with `UNKNOWN_APP`, or a gateway's uplink goes quiet more than 30 minutes: stop, do not proceed to the next node.

Rough elapsed time from Gate A if all goes well: bench 1 to 2 weeks, then 3 nodes at a week each, about 5 to 6 weeks.

---

## 6. Per-node upgrade runbook

Same steps for each node; the order is in section 5. Every command block names its host and says whether it finishes by itself.

**Before (about 15 minutes)**
1. Gate passed; soak criteria met for the previous node.
2. Phone: settings screenshots done (0.2), current node ID noted. **Back up the node's key too:** the ID follows the key, so a saved key is what lets a rebuilt node keep its identity. Whether the app's config export includes the private key is [?]; confirm on the bench (Phase 1) before relying on it, and never put an exported key in the repo.
3. Choose the time: evening; not during an active NWS alert; CJG1 not within an hour of 7:00 AM.
4. Know the rollback: reflash 2.7.26 with full erase and restore settings from the screenshots. Expect the node may keep a new ID [?].

**Flash**
5. Use the Web Flasher (`flasher.meshtastic.org`) in Chrome on the laptop; pick the exact board (CJG1 Heltec V4, CJG2 Heltec V3, KPN6 confirm the model) and the 2.8 Beta build.
6. Choose **update**, not full erase, the first time. Expect the node to come back needing reconfiguration because the filesystem format changed.
7. KPN6: it is plugged into cnjmesh1. For the laptop route, unplug, flash, and put it back in the **same port** (as on Aug 28). Afterward confirm the by-id path is unchanged: on **cnjmesh1**, `ls -l /dev/serial/by-id/ | grep Espressif` (finishes on its own).

**If the node is erased or comes back blank (this is where Long Turbo bites)**
8. Do **not** set the region from the device screen and do not use a fresh-setup flow in the Android app (2.8.3 picks LongTurbo for fresh nodes). Restore from the saved config, or set region to US and preset to **Long Fast** by hand.
9. Confirm Long Fast, slot 20, 906.875 MHz on the LoRa screen before leaving.

**After**
10. Read the **new node ID** (app node screen, `!xxxxxxxx`). Record it in section 9.
11. Re-check MQTT (address, `meshdev`, root topic `msh/US`, encryption setting as before), the CentralNJ key `f+WQoP...`, each channel's uplink/downlink icons, OK to MQTT on, Wi-Fi SSID `C4Somogyi-24` (2.4 GHz). Values: `docs/meshtastic-gateway-mqtt-settings.md`.
12. Re-enable telemetry and position as decided.
13. Update the relay allowlist with the new ID (item 1), restart the relay, and watch its log. On **cnjmesh1**: `journalctl -u sjmesh-relay -n 30 --no-pager` (finishes on its own); look for outbound lines for the new ID.
14. Send "Testing" on CentralNJ from the node. Confirm in Malla (decoded text, gateway = new ID), in Meshview, and for CJG nodes in #mesh-relay.
15. Do the Malla check again after an hour and next morning; compare gateway rows with the old ID.
16. Update the ID table (section 9), `docs/meshtastic-gateway-mqtt-settings.md`, the todos canary entry, `todos.md`, and push.

---

## 7. Watch list during the wait

- Firmware releases page (`meshtastic/firmware`): look for a build whose title says **Beta**; read its release notes in full each time.
- Meshtastic blog post "Let's talk about 2.8" (promised livestream announcement).
- Punchlist issue #10462 for the untested items (signing, regions and presets).
- Open firmware issues that mention MQTT: #12089 (an ESP32-S3 Cardputer node that connects to the public broker and never publishes, 2.7.26 and 2.8.1) is an example of the kind of thing to check against our boards before Phase 1.
- Malla, Meshview, MeshMonitor, meshing-around and the Python library releases for 2.8 support.
- NoDak Mesh's "Should you update" post, which says "For most people, not yet."

---

## 8. Decisions that are Charlie's

1. Bench node: use the spare Heltec V4, or buy a cheap board?
2. Whether to step all three to **2.7.26** first (0.9).
3. KPN6 position policy once precise position is no longer allowed on public channels.
4. When (not if) to remove the dead JSON bridge line.
5. How long to wait after the first Beta before starting: this plan says 2 weeks.

---

## 9. Record while doing the work

| Node | Firmware now | Date checked | Old ID | New ID | Upgrade date | Relay list updated | Notes |
|---|---|---|---|---|---|---|---|
| CJG1 | [?] | | `!0aca423c` | | | | |
| CJG2 | 2.7.24.472b14c | Oct 30 | `!9ea3e8d4` | | | | |
| KPN6 | 2.7.25.104df5f | Oct 30 | `!69841fe0` | | | | |
| Bench | | | | | | | |

---

## 10. Sources

- Meshtastic, "Let's talk about 2.8": https://meshtastic.org/blog/lets-talk-about-2-8/
- Firmware 2.8.1 release notes: https://github.com/meshtastic/firmware/releases/tag/v2.8.1.8e6a88d
- 2.8 punchlist, issue #10462: https://github.com/meshtastic/firmware/issues/10462
- Bug #12115 (PKI DMs not uplinked, fixed by #12110): https://github.com/meshtastic/firmware/issues/12115
- Bug #12089 (node never publishes): https://github.com/meshtastic/firmware/issues/12089
- NoDak Mesh, "Meshtastic 2.8: What's New and Should You Update?": https://nodakmesh.org/blog/meshtastic-2-8-whats-new
- NoDak Mesh, "LongTurbo vs LongFast": https://nodakmesh.org/blog/meshtastic-longturbo-vs-longfast
- NoDak Mesh, packet signing: https://nodakmesh.org/blog/meshtastic-packet-signing-explained
- MeshMonitor, node number changes: https://meshmonitor.org/features/node-identity-changes.html
- MeshMonitor v4.16.0-rc3: https://github.com/Yeraze/meshmonitor/releases/tag/v4.16.0-rc3
- Meshtastic-Android PR #7244 (LongTurbo on fresh US setup): https://github.com/meshtastic/Meshtastic-Android/pull/7244
- Camillia 2.8 impact ticket (pre-hop drop, bitfield, JSON, map reports): https://github.com/oumike/camillia-mt/issues/60
- Meshtastic Python protobufs v2.8.0 PR #980 (merge status not confirmed): https://github.com/meshtastic/python/pull/980

Not readable from this session (blocked): Malla and Meshview GitHub release pages. Their 2.8 status is therefore [?]; check them directly during Phase 0.
