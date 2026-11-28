# CNJ Mesh — Open To-Dos

**For AI assistants:** This is the current, lean action list. Fetch this alongside `cnjmesh1-operations.md` at the start of a session — both are short. Only fetch `session-log.md` (long, narrative, full history) if you need the backstory on *why* something is the way it is.

**Housekeeping rule:** when an item is finished, move it to `docs/todos-archive.md` with a one-line reason — don't mark it "done" and leave it here. Anything worth a narrative goes in `session-log.md`.

**Layout (tidied 2026-11-12 at Charlie's request):** the top section is what is alive now, with current status. Below it, every older open item is one line (its title and tag) with a pointer like *(L57)*. The pointers are line numbers in `docs/todos-full-2026-11-12.md`, a frozen word-for-word copy of this file from before the tidy, which holds the full text, the long histories and every sub-update. Nothing was deleted. When you work on an older item, read its full text there first, then keep the status line here short. Items marked `[status unclear]` could not be settled from the repo (Nov 4 triage).

**Closed Nov 12 2026:** items moved to `docs/todos-archive.md` today are the Wi-Fi dropout, PTT pinning, APRSdroid filter, meshuser/meshdev rotation, leaked webhooks, SJMesh graph, Ocean County bridge, Meshview upgrade, and the n2yo/satpass thread.

**Pending: Charlie's spreadsheet review (sent Nov 12 2026 8:17 PM; he will upload the marked file later).** File: `CNJ-mesh-todo-review-2026-11-12.xlsx`, rows keyed by *Row* and by the line pointer into `docs/todos-full-2026-11-12.md`. How to read his marks (his words, Nov 12 8:36 PM): **"admin"** = an administrative task we need to look at (keep it, in an Admin section); **"play"** = hobby and experimenting, not administration (keep in a separate Play list; his call to me was to keep them separate); **"unsure what this is"** or **"didn't we do this already"** = explain it and check the repo for evidence before acting, do not archive on those marks alone; Drop and Done go to `docs/todos-archive.md` with his note as the reason; blank = keep. He also noticed the many tasks about testing the repo being private and suggested **consolidating them into one item**; do that when the file comes back (the plan is L9–L17 of the full file).

## Active now (status as of Nov 12 2026, evening)
- **PICK UP HERE (Nov 27 2026, 8:33 PM): login trouble, paused for the night.** cnjmesh3 answers ping at `.186` (static on the Pi). Next, one at a time: (1) on cnjmesh3 check method `manual` and both containers `Up`; (2) check the router list and make it match `.186`; (3) why cnjmesh2 login fails; (4) why cnjmesh3's address changed, and its Wi-Fi power save; then the shim watchdog threshold (alerts still say 30 min) and the Observer clock runbook.
- **K2GIA-1 APRS station (todo 17): the UV-5R M + Digirig kept losing PTT because its own transmissions broke the Digirig USB link.** Spare UV-5RM swapped in Nov 11 8:48 PM; about 19 h later (Nov 12 3:56 PM) all six Graywolf units were active with no PTT, EIO or "No such device" errors, 17 beacons sent and packets still decoding. One day is not proof. **To do:** kernel USB log check (`sudo dmesg -T | grep -i -E "usb.*(disconnect|error -71)"`), confirm aprs.fi shows K2GIA-1, add the ferrite chokes on a separate day (one change at a time), a few more clean days before calling it fixed. Written but not deployed: the Graywolf health-watchdog auto-recovery upgrade. The Nov 10 "ready to give up" was not carried out. *(L36–L37, L57–L60)*
- **Weather bots, 7:00 AM Meshtastic and 7:05 AM MeshCore (todo 20).** Done and live: both bots' watchdogs (guarded restart, private channel), the MeshCore "did the forecast post" check (Nov 12), county names in NWS alerts (area patch, verified 4:30 PM), the alert-filter fix, and the radio-pass mode for `!satpass` (ISS works). Nov 12 morning reports both posted. **Next:** tomorrow's 7:00 and 7:05 are the first runs since the Nov 12 evening restarts; the watchdogs should stay silent. On hold: the wide-area alert patch (`locationdata-alert-wide.diff`), Charlie said maybe not. Optional: per-alert ignore-word filter. County list: `docs/coverage-area-counties.md`. *(L67, L69, L71, L73)*
- **NEW Nov 13 (quick win): NWS alert text on the Meshtastic bot says "Wern Monmouth, Eern Monmouth" (should be Western / Eastern Monmouth).** Seen in the CentralNJ channel at 7:00 AM from CJG1 (Coastal Flood Advisory). Cause (read in upstream `modules/locationdata.py`, `abbreviate_noaa()` and `case_insensitive_replace()`): the shortening list replaces words as plain substrings, so `west`→`W` and `east`→`E` also hit inside "Western"/"Eastern" (and "Northern"→"Nern", "Southern"→"Sern"). Fix: a new patch in `cnjmesh1/meshing-around-custom/` making the replacement whole-word only (regex `\b`), written against the Pi's own copy (first get a read-only look at the Pi's `case_insensitive_replace`; the Pi's file may differ from upstream main). Charlie said yes Nov 13; nothing applied on the Pi yet.
- **MeshOmatic bridge on cnjmesh1: tabled by Charlie for tomorrow (Nov 13).** The `meshomatic` bridge (out only, MeshCore to `us-east.meshomatic.net:31883`) sends `CONNECT` about every 71 s and never gets a reply, before and after the Nov 12 broker restart. **Not new:** the same symptom (CONNECT, no CONNACK, retry about every 71 s) was seen on Jul 4 2026 when the bridge was first set up, and a message to the MeshOmatic admin was drafted then; no answer is recorded in the repo. Charlie's web account there is `user_somog` (free, Limited access; the sign-up asks for an email or a Discord handle, which one he used is not recorded; the website password is whatever he chose and is not in the repo). **Unverified guess:** the `user_somog` login is limited to 2 simultaneous connections and may be shared by this bridge, the cnjmesh3 Observer and CoreScope's meshomatic source. Five read-only checks were prepared: on cnjmesh1 `timeout 6 bash -c '</dev/tcp/us-east.meshomatic.net/31883' && echo OPEN || echo "CLOSED or TIMED OUT"`, `grep -i -B3 -A10 meshomatic ~/meshcore-data/config.json | sed -E 's/("pass[a-z]*" *: *")[^"]*/\1***/I'`, `docker logs corescope --since 15m 2>&1 | grep -i meshomatic | tail -8`; on cnjmesh3 `sudo grep -i -v -E "pass|token|secret" /opt/meshcore-packet-capture/config.d/20-meshomatic.toml`, `docker logs meshcore-packet-capture --tail 40 2>&1 | grep -i -E "meshomatic|connect"`. Options afterwards: leave it, ask the MeshOmatic admin, or remove the bridge like Ocean County. Nothing changed. *(L108)*
- **NEW Nov 14 (research, Charlie: "let's research in a bit"): get more MeshCore coverage into CoreScope by subscribing to other people's observers.** Prompted by Capital District Mesh's CoreScope (live.cdme.sh, 1337 nodes, NY and New England; their pages don't say how many observers or which feeds). CoreScope can subscribe to several outside brokers through `mqttSources` (name, broker, topics, username/password, `iataFilter`); observers publish to `meshcore/<IATA>/<pubkey>/packets`. To find out: (1) which public MeshCore brokers allow subscribing without being an observer yourself (LetsMesh is not covered by CoreScope's README; MeshOMatic's feed is the broken bridge item above); (2) which IATA codes cover NJ (our Observer uses EWR); (3) read-only look at our CoreScope's current sources in `~/meshcore-data/config.json` (mask passwords). Rule: always set `iataFilter`; an unscoped subscription repeats the Aug 4 flood on a 2 GB Pi 4. The other route (neighbors publish to our broker) means exposing the private Mosquitto and is not recommended. Nothing changed on the Pi.
- **NEW Nov 21 (play, look at when curious): RXT ("Remote Receive Telemetry") for LoRa APRS digipeaters.** An Arizona operator posted in the Discord #general (Nov 21) about a live RXT view at `jonadams.com/rxt/`: digipeaters running RXT-enabled firmware let operators see how well each digi hears the others and how well a digi hears its own stations. His network is 433.775 MHz, BW 125 kHz, **SF7** (about 5 kbps), which is not the standard SF12 that K2GIA-10 uses, so it is a separate network. **Correction the same day:** this was already researched Sep 22 and recorded in `docs/lora-aprs-reference.md` ("Update 2026-10-13: Graywolf + LoRa APRS via RXT"): RXT is Remote Receiver Telemetry, a JSON-over-HTTP path that feeds already-decoded LoRa packets plus signal data (RSSI, SNR, frequency offset) into Graywolf from a separate LoRa iGate, built on two experimental forks (a CA2RXU iGate firmware branch `feature/aprs-json-producer` and a Graywolf branch `feature/rxt-telemetry`). Watched, not adopted; whether either branch has been released since is unknown, so check upstream before acting. The Arizona operator's page is a live example from digipeaters with RXT-enabled firmware. Still not read: `jonadams.com/rxt/` (not reachable from the assistant's session; ask Charlie for the page text). A Google group `ham-radio-LoRa-APRS` was also mentioned. Nothing changed.
- **`mesh-discord-shim` "no events" alert (todo 18): mostly done, watch it.** Alert moved to the private channel Nov 11 5:57 PM; threshold raised from 30 to 90 min Nov 11 8:23 PM after the shim proved alive (it was false-alarming on normal quiet, longest gap 45 min). Only one day of data; confirm no false alarm over the next days. *(L62–L63)*
- **Watchdog audit (todo 14, plus the item 16 maintenance-pause idea):** send every watchdog's alerts to the private `#cnj-infrastructure-alerts`. Done: Graywolf, mesh-bot, meshcore-bot and mesh-discord-shim. Still listed as open in the item text (not re-checked; two of its names have since been done): ingest-rate, sjmesh-relay, disk-temp, peer-check, corescope. Also open: the maintenance pause (item 16, not built) and whether the Graywolf health watchdog's one automatic restart should be alert-only. *(L39, L54)*
- **Sourland ridge repeater "Beef Sourland 500 NJ-Me" (todo 19): watch and judge it** (MeshCore, 500 kHz; first seen by the Observer Nov 10). Open: repeater or room server (check CoreScope), whether `6B` in the path collides with other nodes (prefer 2-byte paths), the Reach page for `6B` and KPR3, which of our nodes hear `0912` and how often. Keep the operator and personal details out of the repo. *(L65)*
- **MeshCore Hub "Network Info" box shows old radio settings (todo 21).** Shows 62.5 kHz, SF7, 22 dBm; the network has been 910.525 MHz, 500 kHz, SF10, CR5 since Oct 11–14. Likely a label in the Hub's own config. Read-only check: `grep -n -i -E "NETWORK_|RADIO" /opt/stacks/meshcore-hub/.env`; the fix needs Charlie's OK. *(L75)*
- **Router reservations:** KPN6 is at 10.0.0.202 but not yet reserved in the router (todo 9); CJG1 was reserved at 10.0.0.19 but the screen was not re-checked after saving (confirm the list shows Reserved IP); CJG2 should be 10.0.0.234. *(L48, L69)*
- **cloudflared upgrade (Oct 27 email):** upgraded to 2026.10.5 on cnjmesh1 and cnjmesh2. **Left:** check cnjmesh3 (`which cloudflared`), delete the `.bak` files after a few clean days. *(L77–L78)*
- **[Added Nov 23 2026, Charlie] KPR3 (solar, nRF52, Yagi) brownout-protection check.** A Susquehanna Valley Mesh post (Joel Deutscher, Nov 22) says the latest MeshCore RAK4631 builds dropped the `NRF52_POWER_MANAGEMENT` build flag, so a solar repeater that runs its battery flat can get stuck in a brownout loop and need a physical reset even after the panel recharges it. [V, upstream `main` read Nov 23] `variants/rak4631/variant.h` still sets `PWRMGT_VOLTAGE_BOOTLOCK 3300` (mV), but neither `variants/rak4631/platformio.ini` nor `arch/nrf52/platformio.ini` defines `-D NRF52_POWER_MANAGEMENT`; MeshCore's nRF52 power-management doc lists RAK4631 as supported and says the flag enables it. [V, upstream tags read Nov 23] `repeater-v1.17.0` and `repeater-v1.17.1` RAK4631 builds DO enable `-D NRF52_POWER_MANAGEMENT`; `repeater-v1.18.0` does not. [S, Charlie's Oct 2026 KPN1 flashing chat, not in the repo] KPR3 was flashed by UF2 with MeshCore Repeater v1.17.1 (RAK4630 on a RAK19003, LiPo pack), so it should still have the protection as long as nobody has updated it since; this fits the post, which blames the newest release. [UNKNOWN] whether KPR3 was ever updated after that, and whether it has ever run flat. Next: confirm KPR3's version (app or remote CLI) once, and do NOT update it to 1.18.0 until the flag is back (low sun this winter). Do not flash the poster's Google Drive `.uf2` (unreviewed third-party binary). Applies only to nRF52 boards (KPR3, Observer, T096), not the Heltec V4 repeater (KPR2).

- **[Added Nov 24 2026, Charlie wants to test this] 2 m mobile reception test: K2GIA-1 (home Graywolf station) and the TD-H9 (K2GIA-7).** Prompted by a TD-H9 user's Facebook post (he hears two digipeaters but no mobile stations). Charlie's wording: test with "my home station of -1 and my tracker / TD-H9". Note K2GIA-9 (LoRa, 433.775 MHz) cannot be heard by K2GIA-1 (2 m, 144.390); the 2 m mobile is the TD-H9 (K2GIA-7). Proposed method [I, not yet agreed in detail]: K2GIA-7 beacons while Charlie moves to farther and farther points, noting time and rough place; afterward compare with Graywolf's heard list (web UI on cnjmesh1 port 8082) and the K2GIA-7 track on aprs.fi (direct vs via a digipeater); reverse direction: does the TD-H9 hear K2GIA-1's 30-minute beacon (a manual beacon from K2GIA-1 speeds this up). Before starting, check on the radio K2GIA-7's current beacon interval and path (the repo only records APRS firmware v1.0.15 from an Aug screenshot). K2GIA-1 facts [V, `docs/aprs-2m-graywolf-reference.md`]: digipeats WIDE1-1, iGate on, TX power LOW since Nov 8, input gain -11.5 dB (tuned for the old radio; re-check receive level after the radio swap). Open question for Charlie: measure how far K2GIA-1 hears the TD-H9 (the better match for the Facebook post) or how far the TD-H9 hears K2GIA-1. Related older item: "TD-H9 drive test" and "K2GIA-7 not showing on aprs.fi" in the Play list below.
- **[Added Nov 25 2026, from the Part 3 handoff; details in `docs/handoff-part3-2026-11-25.md` section 5] Items that were only in chat until now:**
  - **cnjmesh2 / malla2 UptimeRobot DOWN/UP pairs (Nov 21, about 5 min each).** Matches the known self-resets; cause unconfirmed; whether the Oct 23 PSU/cable swap happened is not recorded. Next: Charlie runs `uptime -s`, `journalctl --list-boots --no-pager | tail -15`, the watchdog `bootstatus` and the flight-recorder tail on cnjmesh2.
  - **Shim "no events" alert still said 30 minutes on Nov 14 and Nov 19** although the repo threshold is 90: the deployed `/opt/mesh-discord-shim-watchdog/watchdog.py` is probably the old copy [unverified]. Next: read-only grep of the deployed threshold, then deploy the repo copy on his OK. He also floated a 24-hour no-activity rule.
  - **SJMesh nodes missing from the Meshview graph:** the Aug 14 swap to `sjmesh-relay.service` dropped the SJMesh topic from `~/meshview/config.ini`. Next: `grep -n -i topic ~/meshview/config.ini` (read-only); restoring is a config change needing his OK.
  - **Tck's 62.5 test and CoreScope.** Tck's group wants to switch from 500 to 62.5 together (910.525 / 62.5 / SF7 / CR5) and see who hears whom. Open: read-only check of our CoreScope `mqttSources` and `iataFilter`; whether to add his IATA code; whether LetsMesh accepts a 62.5 observer (unverified). CoreScope is software someone hosts, not a service you sign up for.
  - **A second node named "CNJ Mesh Observer"** (key starts `101afe5e`, not our `a8c40bf3`). Harmless; no action unless Charlie wants the owner to rename.
  - **[Resolved Nov 26] K2GIA-1 antenna:** NA-771 whip on the Baofeng, not the roof [S]. `cnjmesh1-operations.md` corrected too.
- **[Added Nov 25 2026] Pick up here (on hold until Charlie says he is ready):**
  - On cnjmesh2 (both finish on their own), paste the output into the chat: `uptime -s`, then `journalctl --list-boots --no-pager | tail -15`. Purpose: see whether the malla2 DOWN/UP alerts line up with cnjmesh2 resets.
- **[Added Nov 25 2026] LoRa APRS pager (wanted):** LilyGO T-LoRa Pager, 433 MHz SX1262, with the alpha firmware `radiohound/lora-aprs-pager`. Next: find 433 stock and decide on buying; check for newer releases before flashing. Details in `docs/lora-aprs-reference.md`.
- **[Added Nov 25 2026] RXT-style LoRa APRS dashboard (wanted):** stage 1 uses K2GIA-10's existing syslog and MQTT feeds, no reflash. Plan and checks in `docs/lora-aprs-reference.md`. Code can be written offline; installing on cnjmesh1 needs Charlie's OK.

- **[Nov 26 2026] 2 m APRS now has its own chat.** Its live list is `docs/aprs-2m-start-here.md` (K2GIA-1, K2GIA-7, the second TD-H9 due Dec 1, satellite/packet firmware, learning APRS). Update status there; the older 2 m items in this file are kept for history.

## Everything else that is still open (one line each; full text in `docs/todos-full-2026-11-12.md`)

### [PLAN — make the repo private and prove Claude can still push (Charlie's preference, Nov 4 2026 3:04 PM)]

- Why it should work: write access comes from the account access attached to the session, not from the repo being public. [I, to be proven by step 4.] What depends on it being public [V, grep Nov 4]: the Pi's `git pull` (plain HTTPS, no… *(L10)*
1. Charlie, cnjmesh1 (finishes on its own): `git -C ~/cnjmesh-scripts remote -v`. If the URL starts with `https://github.com/`, it has no login. *(L11)*
2. Pi read-only key (needs Charlie's OK, changes only the Pi's git setup): make an ed25519 key with no passphrase in `~/.ssh/`, add its public half in GitHub repo Settings, Deploy keys, **write access left unticked**, point the clone's remote… *(L12)*
3. Charlie: GitHub repo Settings, bottom, Change visibility, Make private. *(L13)*
4. Claude: push a tiny test commit (one line in session-log.md) and confirm it landed. If the push fails: Charlie flips the repo back to public; nothing is lost; Claude diagnoses. *(L14)*
5. Charlie: `git pull` on cnjmesh1; it should fetch the test commit. *(L15)*
6. Claude: replace the raw-link instructions in the docs listed above with the private-repo way (git over the deploy key on the Pi; for the Windows puller, a different download route), and note that other chats must have the repo attached… *(L16)*
- Rollback at any point: make the repo public again. *(L17)*

### [PLAY LIST — hobby time, nothing here is broken (started Wed Nov 4 2026, Charlie)]

- Charlie, Nov 4 2:31 PM: he spends his days fixing infrastructure and rarely gets to just play with the hobby. He wants to learn and play with **APRS** and learn **how MQTT works**, and hopes the fixing is winding down. Items here are for… *(L20)*
1. **Winlink APRS gateway WLNK-1 (look into and play with).** From a post in the APRSThursday Facebook group (John Madden, Nov 4 2026): he asked who maintains the Winlink server on APRS (WLNK-1) and said it seems to have been down for about 2… *(L21)*
2. **Learn APRS by playing:** hands-on with 2 m APRS, LoRa APRS, Digirig, TD-H9 and the LilyGo nodes (his stated goal, Oct 2026). Candidate starters: message another station, watch packets on aprs.fi, try an APRS "query" or weather request, try… *(L22)*
3. **Learn how MQTT works:** guided, read-only first. Candidate: the MQTT Explorer session already listed in the handoff items (watch `msh/US/2/json/CentralNJ/#` while JSON still exists on 2.7 nodes), plus a walk through how our own broker, the… *(L23)*
4. **KPN9 Long Turbo listen test** (running to about 9:44 PM Nov 5): see what Turbo nodes are out there. Hobby-flavored, not a repair. *(L24)*
5. **[Added Nov 11 2026 9:54 PM, Charlie: "this looks interesting"] H9 Toolbox satellite pass predictor for the TD-H9 (look into, hobby).** Living notes now in `docs/h9-toolbox.md` (updated Nov 15 with a photo of the app on a real radio, and Nov 19 with the developer's teaser of an experimental packet/WinLink KISS TNC build, beta testers wanted; test-project sketch is in the doc; needs a second TD-H9); do not install on K2GIA-7. *(L25)*
5. **Tab5 with OrcSDR** (cards arrived): see the pick-up list below and `docs/tab5-c6l-tracker.md`. *(L26)*
6. **MeshCore regions vs scopes (learned Nov 4 2026 from the MeshCore public-map Discord thread; background, no action needed).** *(L27)*
7. **TD-H9 drive test: how far does it reach over RF only? (Charlie, Nov 4 2026 9:05 PM.)** *(L28)*
8. **[OPEN — troubleshoot, Charlie Nov 4 2026 9:13 PM] K2GIA-7 (TD-H9) is not showing on aprs.fi, and K2GIA-1 should be hearing it.** *(L29)*

### Nov 3–4 pick-up list (old heading: "PICK UP HERE", Nov 4)

- **Added 9:20 PM Nov 3 (Meshtastic 2.8 / KPN9):** Charlie flashed a new Heltec V3 with a 2.8 build and named it **KPN9**. Explainer: `docs/meshtastic-2.8-explained.md` (Long Turbo vs Long Fast, node ID = crc32 of public key, alpha status… *(L32)*
- **KPN9 update, 9:44 PM Nov 3:** KPN9 (Heltec V3, 2.8 build) is fully set up: it is on **Long Turbo** (set on purpose to test), fixed position at Kendall Park town level, Wi-Fi access on. Charlie is leaving it to sit… *(L33)*
- **KPN8 (Nov 4 7:58 PM, Charlie):** second new Heltec V3, being flashed with a 2.8 build on **Long Fast**. The name KPN8 was free (suggested for the Tab5's C6L radio on Nov 1, but Charlie kept KPNM there). Intended as the 2.8 bench node on Long… *(L34)*
- **KPN8 test plan (Nov 4 8:45 PM, proposed to Charlie; Stage 2 and 3 need his OK):** *(L35)*
4. **Tab5 can move forward** (cards arrived): follow `docs/tab5-c6l-tracker.md` section 0 and its Nov 3 log line. Press Run workflow "Build Tab5-Meshtastic" if it has not run, card FAT32 with an MBR table, Launcher full flash at 0x0, then the Tab5… *(L38)*
6. **Carried over from the handoff** (details in the items below): KPC2 swollen cell (call Middlesex County Solid Waste, measure the empty bay, photo of the plug), reserve 10.0.0.202 for KPN6 in the router, weekend website deploy plus status… *(L40)*

### Oct 28–31 list (old heading: "PRIORITY TOMORROW", Oct 29)

1. **MQTT Explorer session (Charlie wants to learn MQTT).** On his Windows PC: install MQTT Explorer (mqtt-explorer.com). Connect to host `10.0.0.181` (cnjmesh1), port `1883`, user `meshdev`, password from his password manager, no TLS. Subscribe… *(L43)*
4. **[Added Oct 29 2026 8:35 PM, Charlie] Graywolf upgrade, 0.13.13 to 0.14.14 (read notes, then decide; not urgent).** *(L44)*
6. **[Added Oct 30 2026 9:35 AM, Charlie] MQTT broker health review (cnjmesh1 and cnjmesh2 Mosquitto).** *(L45)*
7. **[Added Oct 30 2026 10:20 AM, Charlie] Meshtastic 2.8 upgrade plan written, nothing upgraded.** *(L46)*
8. **[Added Oct 30 2026 10:25 AM, Charlie] Export and safely store the private key of every MeshCore node (identity backup).** *(L47)*
11. **[Added Oct 30 2026 7:50 PM, Charlie] CJG1: the app and meshing-around cannot both use TCP 4403.** *(L49)*
12. **[Added Oct 30 2026 8:11 PM, Charlie] Clean up the CentNJ-MQTT channel (nobody uses it).** *(L50)*
13. **[Added Oct 30 2026 8:45 PM, Charlie asked for it] 7 AM / mesh_bot watchdog: DEPLOYED on cnjmesh1 Oct 30 2026 8:41 PM [V, Charlie's terminal].** *(L51)*
10. **[Added Oct 30 2026 5:10 PM, Charlie] KPN6 noise floor is high: -94 dBm, flat all day.** *(L52)*
- Also still open tonight's leftovers: check cnjmesh3 for cloudflared; delete the cloudflared `.bak` files after a few clean days; About-page note on what Malla collects. *(L53)*
15. **[Idea, Oct 30 2026 11:24 PM, Charlie] Website buttons that turn red / show "unavailable" when the linked tool is down.** *(L55)*
16. **[Added Oct 31 2026 1:10 PM, from a real alert] Maintenance pause for the watchdogs.** *(L56)*

### [PLANNED — Oct 27 2026, Charlie asked Oct 26 8:40 PM "should we put a watchdog on it?"] Two watchdogs for what we fixed Oct 25-26

- Build after a day of baseline numbers (the relay's 10-minute `Stats since start` line), so thresholds are not guesses. Pattern: existing `watchdogs/` services, alert to Discord on state change only. *(L81)*
1. **SJMesh outbound health.** The current `sjmesh-relay-watchdog` only checks the heartbeat file (process alive). New failure to catch: SJMesh's broker stops accepting our publishes (ACL change, disconnect), which is silent for QoS 0. Signal… *(L82)*
2. **CentralNJ key-mismatch canary** (would have caught CJG2's wrong key months ago). Hourly Malla query per our gateway (`!9ea3e8d4` CJG2, `!0aca423c` CJG1, `!69841fe0` KPN6): share of CentralNJ rows that are `UNKNOWN_APP` with `payload_length`… *(L83)*

### [OPEN — low] SJMesh outbound path (LIVE since Oct 26 2026): what is left

- **Kill switch (cnjmesh1):** `sudo rm /etc/systemd/system/sjmesh-relay.service.d/outbound.conf && sudo systemctl daemon-reload && sudo systemctl restart sjmesh-relay`. *(L86)*
- **Still unknown:** whether SJMesh gateways downlink CentralNJ to their RF (only they can tell us; observable by asking someone in Cape May to watch for our messages). **KPN6 caveat:** its MQTT Encryption setting is off, so it publishes decoded… *(L87)*
- **[Pointer, Oct 26 gap, low priority]** CJG1 uploads to cnjmesh2's broker, so the SJMesh outbound path (which runs on cnjmesh1) does not cover CJG1's messages (for example the 7:00 AM NWS weather); options if wanted: outbound from cnjmesh2, or… *(L88)*

### [ACTIVE — blocked on one fact only Tilly has] Get Tilly's fork running on KPR1 (cross-mesh packet bridge)

- Full multi-week debugging narrative archived in session-log.md (Aug 16 entry) — this is just the current status. KPR1 is dedicated to this project (CNJ endpoint `b`), fully built and connected to Tilly's AWS broker. Root cause of the… *(L91)*
- **The one remaining blocker:** what makes a MeshCore device start pushing companion-protocol LOG_DATA frames over serial — a firmware build, a device setting, or a specific command? Tilly's endpoint does this successfully; ours doesn't. This is… *(L92)*
- **Also still open:** Tilly's own endpoint was independently observed cycling too (~105 sec) — worth flagging to him that his side may need the same kind of timeout fix once the main blocker is resolved. *(L93)*

### [FUTURE IDEA — not decided or scheduled] SATA SSD upgrade for cnjmesh1

- Pi SD cards are a known long-term failure point, and given cnjmesh1's disk-fill history, more headroom + reliability could help. No decision made, revisit when there's bandwidth for a hardware project. *(L96)*

### [REFERENCE] `docs/RESILIENCE-PLAN.md` and `docs/PREVENTION-AND-INCIDENT-RUNBOOK.md`

- Both built Aug 5 in response to "I never want to go through this again." **The two highest-value items from both docs — broker ingest-rate watchdog and disk-space watchdog — are now DONE** (deployed Aug 15-16, all 3 Pis have disk-temp… *(L99)*

### [READ] Lessons learned from get-well plan execution — `docs/lessons-learned-get-well-plan.md`

- Process/technique lessons worth a fresh read at the start of future sessions on this project: git commit -a not staging new files, schedule changes needing explicit confirmation, stale docs causing false alarms, watchdogs being alert-only… *(L102)*

### [MASTER GATE] Pre-Tilly health checklist — everything 100% before finalizing Tilly

- Charles's requirement: confirm all of cnjmesh1/2/3, Malla, Meshview, APRS/Graywolf, LoRa APRS, MeshCore Observer/repeaters/Hub healthy before finalizing Tilly's-fork-on-KPR1. Full checklist: `docs/pre-tilly-master-checklist.md`. Given KPR1… *(L105)*

### Smaller open items, roughly in priority order

- **[NEW Aug 17 — investigate when time allows]** Graywolf cpal/ALSA POLLERR audio capture bug — confirmed NOT blocking core function (TX, iGate, APRS OTA all worked fine despite it), but unresolved. Full root-cause research in… *(L109)*
- **APRStastic experiment** (Meshtastic↔APRS gateway) — needs a dedicated spare node (not CJG1/CJG2) and ideally its own Pi. Two decisions pending: OK with CNJ node positions on public aprs.fi, and which node/Pi to use. Alpha software, hobby-tier. *(L110)*
- **`whorepeated.sh`** — back-burner, now technically unblocked (KPR1 working), no urgency assigned. *(L111)*
- **CoreScope `local` source instability** — genuinely unresolved. Best lead: a Mosquitto protocol-error disconnect possibly tied to a zero packet-identifier bug (Mosquitto 2.0.11+ enforcement). Needs a real tcpdump capture timed right after a… *(L112)*
- **Per-source freshness watchdog idea for CoreScope** — a stale MQTT source (e.g. meshomatic) can go unnoticed for days since nothing currently alerts on it; CoreScope's own UI shows this already, just not pushed to Discord. *(L113)*
- **Radio tuning** (KPR2, Observer) — apply Capital District Mesh whitepaper §9.4.2 txdelay/rxdelay tuning; neighbor counts never gathered. **[status unclear: the repo cannot tell]** *(L114)*
- **MeshCore regioning talking points** — prepared, never brought back to the NY/NE Mesh Discord. *(L115)*
- **LetsMesh map discrepancy** — CNJ packets flowing on the Packets page but not appearing on the map itself. Not investigated. *(L116)*
- **KB2EAR-2 not appearing in CNJ packet feed** despite being ~772m away — flagged as odd, not investigated. *(L117)*
- **mr-tbot's mesh-api** — reference pointer for future cross-mesh bridging, never evaluated. *(L118)*
- **[SOMEDAY, after software/config todos are closed out] Physical workshop organization** *(L119)*
- **Service-level heartbeat idea — still open, separate from peer-check/Fing.** *(L120)*
- **Fing Agent — old dead board's MAC still shows stale alerts.** Deprioritized Sep 1: confirmed only one legitimate `fingagent.bin` process running on cnjmesh1 (PID stable since Aug 11, no duplicates), and Charles confirmed Fing is working fine… *(L121)*
- **[NEW Aug 18 — still open, narrowed]** Original question — Charles not seeing certain CentralNJ messages on KPN6 (app) / Discord that he used to see — is STILL UNRESOLVED, but now narrowed: confirmed the SJMesh relay, mosquitto broker, and… *(L122)*
- **[NEW Aug 18 — resilience/security review]** A handful of ideas surfaced from an end-of-session environment review, worth working through over a few nights: *(L123)*
- **Port `ingest-rate-watchdog` to cnjmesh2** — it runs Malla capture on the raw (unfiltered) firehose too, same flood/loop-node exposure that caused the original cnjmesh1 disk-fill saga, currently unwatched there.… *(L124)*

### Carried items from Aug 18 – Aug 30 2026

- **[NEW Aug 18 — BLOCKED on hardware]** LoRa APRS message-type packets (not just position beacons) should relay to the LoRa APRS Discord channel — same pattern as the Graywolf 2m bridge (`graywolf-discord-bridge.py`), but for K2GIA-10 /… *(L127)*
- **[NEW Aug 18]** Retry old unsuccessful LoRa APRS bot queries (WHO-IS, CQ, ISS, WXBOT — all attempted Jul 26-30, before the K2GIA-1 rename, roof antenna, and OTA validation work) now that the RF/iGate chain is proven working end-to-end. First… *(L128)*
- **[NEW Aug 23]** Once the LoRa APRS tracker board (K2GIA-9, on order) arrives and is configured, Charles considers active RF projects "done" aside from break/fix — worth a light doc consolidation pass at that point given the repo has grown… *(L129)*
- **[NEW Aug 26]** Point K2GIA-10's syslog at the public `lora-aprs.live` aggregator in addition to the existing cnjmesh1 target — needed for K2GIA-9/K2GIA-10 to show up on that site's tracker/iGate maps and RF analytics (SNR, real digipeat path… *(L130)*
- **[NEW Aug 26]** Investigate `0xfab1a80c` (shortname FTRN) hot-node alert from ingest-rate-watchdog (57% of traffic in 1hr) — likely legitimate, since Charles confirmed SGA was actively field-testing with FTRN (an elevated relay node) the same… *(L131)*
- **[NEW Aug 28, not urgent]** Get K2GIA-9 fully off IS too — add `RFONLY,NOGATE` to its digipeater path (currently `WIDE1-1,WIDE2-1`, no protection). K2GIA-10's own APRS-IS gate is already off (Aug 28), but K2GIA-9's path itself has no… *(L132)*

## Items added by the 2026-10-13 handoff merge

- *(Source: six handoff files from separate chats. Tags: [V] verified, [S] secondhand, [I] inference. Old items above are untouched; these are additions/update notes.)* *(L135)*

### From the Jul 24-25 K2GIA / K2GIA-10 range-test + Meshview/Malla handoff

- **[OPEN] Coordinated RF test for K2GIA-10 still not done** — ask a nearby operator to watch their iGate while a CQ is sent on 433.775. K2GIA-10 non-self-gating means aprs.fi alone can't prove reach. **Possible test partner (Oct 14):** N2ZAV, on… *(L138)*

### From the Aug 20-24 / Oct 5-13 APRS messaging (TD-H9 / KISSLink / APRSdroid / Graywolf) handoff

- **[OPEN] Does K2GIA-9 firmware offer BLE KISS?** Repo has it on Bluetooth Classic; "tracker supports BLE KISS" came from the CA2RXU wiki and is untested for this board. Don't plan KISSLink with K2GIA-9 until confirmed. *(L141)*
- **[OPEN, low]** Check ODmaster for Android 2.6.5; check Graywolf version/update; decide whether to try Ramble / PocketCHIRP (no commitment made). *(L142)*
- **[DECISION NEEDED — public repo]** (a) APRS-IS passcode is committed in many files (APRS passcodes derive from the callsign by a public algorithm, so low risk, but it conflicts with the "no passwords" rule); (b) K2GIA-1 coordinates appear in… *(L143)*

### From the Sep 2 - Oct 13 ops / APRS / backups / GitHub handoff

- **[APPLIED Oct 16 2026 20:52 — awaiting a real alert to confirm]** meshcore-bot weather-alert truncation. Root cause [V]: the Sep 1 patch was applied to the git clone `~/meshcore-bot/` (Sep 1 19:00), but the service runs `/opt/meshcore-bot/`… *(L146–L148)*
- **[LOW] Oct 23 frost advisory text: 'til 7AM' in Discord vs 'until October 24 at 9:00AM' in the bot log [V both].** *(L149)*
- **[WATCH] Graywolf "RXT" LoRa APRS fork** — no action; check upstream for merges before revisiting (`docs/lora-aprs-reference.md`). *(L150)*
- **[OPTIONAL]** weekly APRS check-in nets table saved in `docs/aprs-bulletins-and-bridging-reference.md`; add a reminder only if Charles wants one, and decide whether to test a check-in through K2GIA-1. *(L151)*

### From the Sep 24 / Oct 13 APRS RX recovery + GitHub push investigation handoff

- **[DECISION] Keep or remove the Graywolf RT-scheduling override** (`graywolf.service.d/override.conf`) — it showed no benefit. POLLERR root cause unresolved; the Digirig replug is a workaround. *(L154)*
- **[OPEN] Diff the live Graywolf Discord bridge script against the repo copy** *(L155)*
- **Update on the Aug 17 POLLERR item above:** "proven cosmetic" is too strong — see `known-issues.md` update. The RT override was tried Sep 24 with no effect. *(L156)*

### From the Oct 4-13 KPR3 / KPC2 500 kHz cutover handoff

- **[OPEN] KPR3 remote-admin login on 500 kHz fails** while packets relay (see `known-issues.md`). Ideas, none tested: reset the contact's Out Path; re-enter admin password; check status/uptime from KPC2.… *(L159)*
- **[OPEN] Observer clock ~27 h ahead** (see `known-issues.md`): a power cycle on Oct 14 did NOT reset it (still ~96,700 s ahead), so that test is done and failed; firmware refuses to set it backwards. Just documented unless a fix is found — if… *(L160–L161)* **Nov 13:** MeshOMatic emailed Charlie on Oct 26 about this same clock ("1 day 2 hours ahead", consistent with the ~27 h) and suggested a fix: the `clkreboot` command (reboot with the clock reset to 15 May 2024, then set clock to now), or its Devices > Repeater Mgmt > Actions > "Fix clock" button. The MeshCore CLI docs list `clkreboot` under the Repeater/Room Server/Sensor commands; whether the Observer's companion firmware accepts it is untested. Try the site's button once Charlie is logged in to MeshOMatic. Plain reboot and power cycle already failed. **Nov 19:** the same MeshOMatic email came again (7:19 AM; Observer clock read Nov 20 15:11 UTC, about 26 h 52 min ahead), so the offset is steady, not drifting, and MeshOMatic is still receiving the Observer. The email warns that nodes which heard its future-dated adverts may ignore its newer ones until real time passes the clock it showed, so expect a day or so of that after any fix. Still waiting on Charlie getting back into his MeshOMatic account (password reset email had not arrived Nov 13). **Nov 19 finding [V, read in upstream MeshCore `main` source: `examples/companion_radio/MyMesh.cpp` and `src/helpers/BaseChatMesh.cpp`]:** (1) the companion firmware's set-time command only accepts a time at or after the current clock (anything earlier returns `ERR_CODE_ILLEGAL_ARG`, exactly what we saw); an upstream pull request to allow setting backwards (meshcore-dev/MeshCore #1349) is not in `main` as read today. (2) On every boot the companion firmware calls `bootstrapRTCfromContacts()`, which sets the clock to the newest stored contact timestamp plus one second. **Likely reason the reboot and the power cycle did not fix it:** a stored contact carries a timestamp from the future, and boot pulls the clock straight back to it. This is a hypothesis from reading the code, not tested on the Observer. **Possible fix to research and test (nothing done):** clear the Observer's stored contacts (so the bootstrap finds nothing), reboot so the clock falls back to its default, then `clock sync` forward to now. Open: the exact `meshcore-cli` command to clear contacts, whether the Observer needs them, and how to re-add anything it needs. `clkreboot` is a repeater/room-server command and is not in the companion code.
  - **Nov 27 2026 source check [V: upstream tag `companion-v1.16.0`, commit 07a3ca9]:** fix method now researched, untried: delete the Observer's contacts file from the CLI Rescue console. Steps and limits: `cnjmesh1-operations.md`, "Runbook - fix the Observer clock". Needs a button press on the device and Charlie's OK. Supersedes the "exact contact-clearing command is unresearched" note.
- **[OPEN] KPR1** (Tilly bridge) — now the **only** MeshCore node still on 62.5 kHz.… *(L162)*
- **[OPEN] path.hash.mode** on KPR1/KPR2: unchanged, decision pending. *(L163)*
- **[OPEN] KPR3 health check, Nov 8 2026 evening [V, CoreScope screenshots Charlie sent, 9:48-9:53 PM]:** *(L164)*
- **[OPEN] Confirm KPR3 reaches Tck's area via the Yagi** (send one advert from KPR3 on 500); record KPR3's actual TX power; decide whether the Yagi setup is within the module's grant (see `cnjmesh1-operations.md` caution). *(L165)*
- **[OPEN] Community notice** of the cutover (Discord/Facebook). **[status unclear: the repo cannot tell]** *(L166)*
- **[OPEN] Confirm Observer model** (WisMesh Pocket v2 vs Mini) and fix the KPR1 "retired" row in `cnjmesh1-operations.md`. *(L167)*

### [OPEN] Heltec T096 (KPC3) battery splice, carried from the Oct 9-13 handoff

- **[OPEN] Heltec Mesh Node T096 battery splice not done.** T096 is a Heltec product (nRF52840), not LilyGo. It uses a JST SH 1.25 mm (1.25-2P) battery connector; Charles has a 10,000 mAh battery with a PH2.0 connector. Splice plan [S]: verify… *(L170)*

### [OPEN, low] meshcore-mqtt-bridge and KPR2 (Oct 14)

- **[OPEN, low] What does `meshcore-mqtt-bridge` actually get from KPR2?** The bridge sends a companion handshake (`appstart`) to KPR2, a repeater, which did not answer companion commands when `meshcore-cli infos` tried (Oct 14). The bridge still… *(L173)*

### From the Oct 14 KPC1 / weather-bot outage / watchdog handoff

- **[OPEN] Watchdog alert test result.** Restarting the bot flipped the `meshcore-bot-watchdog` state dead -> active, which should post "CNJMESH cnjmesh1: meshcore-bot back up and running" at its next run (~11:18 AM Oct 14). Record whether it… *(L176)*
- **[PENDING APPROVAL] Improve `watchdogs/meshcore-bot-watchdog/watchdog.py`** *(L177)*
- **[OPEN, low] Consider enabling the bot's own radio-offline alerts** (`radio_offline_alert_enabled` / `radio_zombie_alert_enabled` are `false`) — or deliberately leave off. *(L178)*
- **[OPEN, low] Physically label the KPC1 and KPR1 boards** (identical USB serial; Charles was confused on the bench; `infos` is the only software way to tell them apart). *(L179)*

### [FUTURE — APRS pivot] SP0LND balloons (Poland): track them and consider LoRa APRS involvement (added Oct 15, 2026)

- Charles wants to keep an eye on this and revisit it when he returns to the LoRa APRS project. Notes and open questions are in `docs/spolnd-balloons-notes.md` (statements by SQ2CPA and others in Discord, unverified). Short version: balloons… *(L182)*

### [NOT STARTED — Charles is not ready yet] LoRa APRS physical work: upstairs node, antenna, button (added Oct 15, 2026)

- Full reconciliation is in `docs/lora-aprs-reference.md` ("Update 2026-10-15: physical work reconciliation"). Checklist, all open: *(L185)*
- [ ] **[Nov 8 10:15 PM, Charlie] A LoRa APRS node is on the roof antenna now (he is not sure why; he hasn't had time to play with it).** *(L186)*
- [ ] **[Nov 8 10:16 PM, Charlie, decision] The LoRa APRS node now on the roof antenna should move upstairs, onto the indoor 433 MHz antenna, connected to cnjmesh3.** *(L187)*
- [x] **DECIDED Nov 21 2026 (Charlie): the main LoRa APRS node, K2GIA-10, goes upstairs, powered from a cnjmesh3 USB port, on an indoor 433 MHz antenna; the trackers (K2GIA-9) stay mobile.** Still open: whether the second RX-only board ever arrived and whether it is still wanted, the antenna choice, and a check of cnjmesh3's USB power budget (Pi 3B+ already runs the Observer and KPR2). Original question, now answered: K2GIA-10 (antenna height; WiFi unit, USB power only) or the second RX-only board (plugs into cnjmesh3, indoor antenna). The repo has both plans; Charles remembers a mix. Answer to "which is on the roof… *(L188)*
- [ ] **Confirm the hardware status:** did the second RX-only board, 433 MHz antennas, cases, and the two Alfa antennas arrive? (Existing "in-transit hardware" item is stale or unknown.) *(L189)*
- [ ] **Choose and place the upstairs antenna** (433 MHz capable; whip or indoor; connector type SMA vs RP-SMA unconfirmed). Power from a cnjmesh3 USB port; K2GIA-10 needs no serial there. *(L190–L191)*
- [ ] **Button for K2GIA-9** (LilyGo T3 V1.6.1, no user button): buy a 2-pin momentary switch (example link in the reference doc), then solder IO15 to GND per the steps in the reference doc. *(L192–L194)*
- [x] **Pin is confirmed: IO15** (source-confirmed in the Jul 31 / Aug 30 chat for both `ttgo-t-lora32-v2_1_TNC` and `_GPS` variants; see QUICK ANSWER in `docs/lora-aprs-reference.md`). Remaining caveat only: the Sep 2 IO15 pad-touch gave "deep… *(L195)*
- [ ] **Locate IO15 and a GND on K2GIA-9 (updated Oct 15 after checking a pinout Charles pasted from another AI):** *(L196)*
- [ ] After any move: test K2GIA-9 to K2GIA-10 digipeat again, and decide whether the Jul 24 roof-antenna test is still wanted. *(L197)*
- Related existing items: UV-5R M antenna location (Oct 13 item), K2GIA-10 reach test, SP0LND balloon notes. *(L198)*

### Ideas and carried items (Oct 18 – Oct 22 2026)

- **[IDEA, Oct 18 2026] Meshnology W12 (LR2021) as another MeshCore node / Observer?** *(L201)*
- **[OPEN, Oct 18 2026 18:56] Malla maps show the CARTO "API KEY REQUIRED" watermark** *(L202–L205)*
- **[OPEN, low; added Oct 21 2026 09:48] Re-examine the `#cnj-new-node-relay` wording later.** *(L206)*
- **[TO TEST, medium-low; Charlie agreed Oct 22 15:34] New-node announcements from the decoded packet stream instead of the radio's contact list.** *(L207)*
- **[RESEARCH, Oct 22 2026 15:30, Charlie] MeshCore 350-contact limit and the Observer.** *(L208)*
- **[DECISION, Oct 21 2026 09:16] TD-H9 (K2GIA-7) firmware 1.0.38 update: upgrade or not?** *(L209)*

### Ideas, parking lot and carried items (added Oct 16 2026)

- **[IDEA, Oct 21 2026 18:26, Charles interested] EmergencyHam Network (EHN) basestation: MeshCore <-> Meshtastic <-> SMS/RCS gateway.** *(L212)*
- **[IDEA — not started] Nooelec SDR + OrcSDR:** Charles owns a Nooelec NESDR SMArt v5 SDR (confirmed Oct 16). https://theorc.dev/nooelec/ is a compatibility page for **OrcSDR**, standalone receiver software for the M5Stack Tab5 (no PC needed).… *(L213–L225)*
- **[WATCH — LV Mesh / 62.5 vs 500 kHz bridge, Oct 16 2026, secondhand [S]]** *(L226)*
- **[LOW] cnjmesh1: something toggles wlan0 promiscuous mode every ~3 s (seen in dmesg Oct 22, ~77 days uptime, signal -54 dBm, no SD/ext4 errors).** *(L227)*
- **[OPEN] cnjmesh2: 2 resets in ~4 h (Oct 22 20:54, Oct 23 ~01:00); both self-recovered in ~1 min. Only the first showed Wi-Fi SDIO errors; the 01:00 one stopped abruptly from a healthy state with no error. Next: swap power supply/cable (cheapest test), then USB Wi-Fi dongle, then replace. See**… *(L228)*
- **[OPEN, 3rd outage Oct 22 2026 ~20:30 ET; power-cycled 20:40, back up; cause unknown; details in `known-issues.md`] cnjmesh2 reliability: decide whether to keep, fix at the root, or move its jobs (malla2, mosquitto, cloudflared). Journald persistence and the watchdog are now confirmed active; wait**… *(L229)*
- **[Pointer from the Oct 17 list]** cnjmesh2 OS and Wi-Fi firmware update (`sudo apt update && apt list --upgradable ...`, then watch `journalctl -t wifi-selfheal`); no result is recorded in the repo. **[status unclear: the repo cannot tell]** *(L230)*
- **[OPEN — BRAINSTORM] "CNJ Mesh Pi Health Checks" (added Oct 16 2026 22:53, Charles's idea):** *(L231)*
- **[TO DO — TEST RESTORE, added Oct 23 2026 21:25 at Charlie's request] Prove the backups actually restore (nobody has tested a restore yet).** *(L232–L240)*
- **[TO DO — backups, open items from the Oct 23 audit; full list in `docs/backup-guide.md` section 7]** *(L241)*
- **[TO DO — inventory refresh]** Per the end-of-session rule, re-run `scripts/collect-inventory.sh` and commit the refreshed `install-map-<host>.md` for cnjmesh1 (journald drop-in, bot patch), cnjmesh2 (flight-recorder timer, journald… *(L242)*
- **[PLAN Oct 23 2026, Charlie asked] Buy spare microSD cards for all three Pis (cold spares imaged from each live card).** *(L243)*
- **[OPEN — PLAN] Backups for every Pi, automatically copied to the laptop/OneDrive (raised Oct 16 2026 23:35):** *(L244)*
- **[OPEN — TIME-SENSITIVE] Retivis RT27V MURS radios: test them and decide on a replacement (added Oct 17 2026 13:05):** *(L245)*

### [OPEN — Oct 23 2026] KPC2 (T-Deck Plus) swollen battery — replace cell

- **UPDATE Nov 10 2026 11:02 PM [S, Charlie]: KPC2 is 'fried' because of the swollen battery.** *(L248)*
- Oct 23 ~22:00 Charlie found KPC2's battery puffed; removed it and put it outside on a rock. Old cell: Tewaycell 405070, 3.7 V, 2000 mAh, dated 2025-08-02, with the usual PCM under Kapton tape. Pouch had point dents (something in the case… *(L249)*
- Board looked clean (no scorching). KPC2 runs on USB with no battery until the new cell arrives. *(L250)*
- BAT socket: 2-pin, plastic body 4.44 mm wide (Charlie's caliper, tabs excluded) = **1.25 mm MX1.25 / PicoBlade** (not 2.0 mm PH). The usual "T-Deck" 2000 mAh packs (MakerNova, Rokland, MakerFocus) are 10 mm thick and will NOT fit; bay… *(L251)*
- To do: order a 405070 3.7 V ~2000 mAh cell with protection board and 1.25 mm plug (or add a 1.25 mm pigtail); meter-check BAT socket polarity with USB in and no battery before connecting (seller wiring varies); dry-fit the case and… *(L252)*
- Old cell: tape leads, keep in a metal can with sand outdoors; Middlesex County HHW drop-off Sun Nov 15 2026, 8-2, Middlesex College, Edison (call 732-745-4170 to confirm they take a swollen lithium pack). *(L253)*
- UPDATE Nov 1-2 2026 (Charlie, this chat): [V, Amazon message screenshot Nov 1 5:40 PM] LilyGO's Amazon seller will not ship a battery on its own (international shipping rules), only together with other items in an order; so buy from a US… *(L254)*

### [OPEN — status unclear] KPC3 (Heltec T096): channel keys still to confirm

- Not yet done: channel key(s) added (CentralNJ-MC etc., to match KPC1/KPC2) — confirm this happened before relying on KPC3 for channel messaging, not just node-heard visibility. Physical case/mounting not addressed.… *(L257)*

### [OPEN — Oct 24 2026] Narrow weather alerts to NJ-only, not all of NWS Mount Holly's coverage

- Oct 24 08:54 AM: a "Frost Adv New Castle" (New Castle County, DE) alert came through `#centralnj-mc-channel-relay` — correct behavior under the current filter, but not what Charlie wants. Cause: `patch_alert_njfilter.py` (Oct 20) only… *(L260)*
