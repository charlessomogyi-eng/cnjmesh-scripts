# New-chat handoff — written 2026-10-23 21:45 ET (full version)

Purpose: let a fresh Claude chat pick up CNJ Mesh work with the same working style, the same context, and no lost history.
Read order for the new chat: `CLAUDE_CONTEXT.md`, this file, `todos.md`, `known-issues.md`, `cnjmesh1-operations.md`, `docs/backup-guide.md`, tail of `session-log.md`.

---------------------------------------------------------------------
## 1. Working agreement (how Charlie wants Claude to behave)
- Charlie (K2GIA, Systems Engineer at a data-protection vendor, runs CNJ Mesh in Central NJ). Call him Charlie, never Charles. Use his name rarely ("here and there"); he has had to tell several chats to stop.
- It is a partnership: direct, natural, confident. Never sheepish, tentative or over-apologetic. Own mistakes in one line and move on.
- Claude acts as Claude Code on the public repo `charlessomogyi-eng/cnjmesh-scripts`: clone, edit, commit, push yourself as work finishes. Charlie never runs git and does not want a handoff step for it.
- Charlie runs every command himself on the Pis and pastes the output. Never remind him you lack SSH access. Never wait for permission to give or suggest a command, restarts included; he is not tracking every step, so proactively say what to do next and end replies with a short Pending list.
- Every command block must name the host (cnjmesh1/2/3 or laptop) and say whether it finishes on its own or needs Ctrl+C. Read the prompt in pasted output to confirm he ran it on the right host (tonight a cnjmesh2 command was run on cnjmesh1).
- Plain chat only. He dislikes checkbox/multiple-choice prompts (do not use AskUserQuestion).
- Public repo: never commit passwords, tokens, webhook URLs, private keys, the CARTO key or the home address. Backup archives hold secrets and are never committed (they live on the Pis, the laptop and OneDrive only). Do not remind him about pasting GitHub tokens.
- Never change infrastructure/auth on a host he did not explicitly name. Do not run heavy jobs on cnjmesh2.
- Be honest about evidence. Tag what was verified from pasted output vs inferred. Tonight's self-corrections: calling Wi-Fi the "root cause" of cnjmesh2 resets (overconfident), wrongly retracting the journald-volatile finding, calling "MOUN" cosmetic, guessing NWS reissued the advisory.
- Patch pattern: exact-match-or-abort Python script, `--dry-run`, timestamped backup, compile check, restart as a separate step.
- Commit trailers: `Co-Authored-By: Claude <noreply@anthropic.com>` plus the session URL line the harness provides.
- End-of-session routine (also in CLAUDE_CONTEXT.md): update `todos.md`; update `cnjmesh1-operations.md` if infrastructure changed; re-run `scripts/collect-inventory.sh` on any Pi where something was installed/moved/reconfigured and commit `install-map-<host>.md`; append a dated `session-log.md` entry; push.
- Charlie's context: time is his scarcest resource. Daily operational issues keep eating the time meant for todos; he wants the list down to 1-2 active items. He lost cnjmesh1 once (weeks of nights to rebuild) and treats backups as "really important stuff".

---------------------------------------------------------------------
## 2. The network (stable facts)
Target MeshCore settings for every CNJ node: 910.525 MHz / 500 kHz BW / SF10 / CR5 (moved from 62.5 kHz/SF7 on Oct 11-14; KPR1 is the lone holdout until Tilly moves).

- **cnjmesh1** 10.0.0.181, Raspberry Pi 4 Model B, 58.9G card (36G used), user somog, ~77 days uptime. Main server: `meshcore-bot.service` (`/opt/meshcore-bot`, config `/etc/meshcore-bot/config.ini`, radio KPC1 "CNJWeatherBot" on `/dev/kpc1`), mesh-discord-shim (`/opt/stacks/mesh-discord-shim`, Docker; app.py baked into the image so changes need `sudo docker compose up -d --build`), MeshCore Hub, CoreScope (`/home/somog/meshcore-data`), Meshview (`/home/somog/meshview`, `meshview.cnjmesh.me`), Malla copy, Mosquitto, Graywolf (2 m APRS, Digirig), Postgres, MySQL (aprs-tnc-web), watchdogs, Fing agent.
- **cnjmesh2** 10.0.0.91, Raspberry Pi Zero 2 W, Wi-Fi only, 59.6 GiB card (16.8% used), user somogyic, kernel 6.12.47+rpt-rpi. malla-web, malla-capture, Mosquitto (Docker), cloudflared (malla2.cnjmesh.me). Memory-tight (416 MB): never run backups/inventory casually here.
- **cnjmesh3** 10.0.0.186, Raspberry Pi 3 Model B+, 29.1G card (5.3G used), user somog. Observer (RAK4631 companion, v1.16.0) and KPR2 (Heltec V4 repeater) radios; Docker containers `meshcore-packet-capture` (config `/opt/meshcore-packet-capture/config.d`, publishes to 4 brokers) and `meshcore-mqtt-bridge` (bind `~/meshcore-bridge-data`); `~/meshcore-mqtt-tilly` is Tilly's bridge fork. Only SSH listens.
- Pis are never wired: they sit next to radios/antennas, and the house has no Ethernet drops. Do not propose wired fixes.
- Radios/nodes: KPC1 (weather bot companion), KPC2 (Charlie's companion), KPR1 (Tilly bridge, still 62.5 kHz), KPR2, KPR3, Observer, KPN2 (T-Deck Plus), LoRa APRS nodes K2GIA-9/-10, TD-H9 (K2GIA-7), UV-5R M (K2GIA-1 roof antenna).
- Discord channels: `#centralnj-mc-channel-relay` (mesh to Discord relay incl. bot forecasts/alerts), `#cnj-new-node-relay` (new node announcements), `#cnjmesh` (watchdog alerts).

---------------------------------------------------------------------
## 3. What this chat did (chronology, newest details last)
**Oct 13-14: handoff merges.** Seven earlier chats' findings were merged into the repo: K2GIA/K2GIA-10 range tests and Meshview/Malla coverage; APRS messaging (TD-H9/KISSLink/APRSdroid/Graywolf); backups and GitHub push breakage; APRS RX recovery; KPR3/KPC2 500 kHz cutover; KPN2 WiFi/IP work; Observer to 500 kHz (Oct 13); KPR2 to 500 kHz (Oct 14); KPC1 to 500 kHz and a bot outage (Oct 14). Findings: Observer clock ~27 h ahead (firmware refuses to set it back; a power cycle did not fix it); `meshcore-bot.service` had been dead 19 days after a Sep 24 USB event (start-limit-hit), restarted Oct 14; watchdog design gaps recorded. Repo cleanup: order number/personal name removed from docs.
**Oct 14-16: housekeeping.** LoRa APRS Discord nickname ("Charlie K2GIA", done). Website review: `getting-started.html` updated for 500 kHz and deployed Oct 16. CARTO "API KEY REQUIRED" watermark on CoreScope (fixed Oct 17) and Malla (open). SP0LND balloon notes filed. Website live-tiles idea dropped. Weather alert truncation: Sep 1 patch had hit the wrong copy (`~/meshcore-bot` instead of `/opt/meshcore-bot`); fixed with `patch_alert_chunking.py` Oct 16 (lesson: patch `/opt/meshcore-bot`). Oct 16 night: cnjmesh2 found unreachable (2nd time); mitigations applied (persistent journald, `RuntimeWatchdogSec=15`, Wi-Fi power-save off); `wifi-selfheal` timer installed Oct 17.
**Oct 17-19:** Meshview "See Everything" menu restored; LetsMesh Analyzer notes; Retivis RT27V MURS radios question; shim silence alert; website edit for "Central & South New Jersey" prepared (not deployed).
**Oct 20:** a TEST tsunami alert (Texas, "NWS NATI") reached the mesh relay. Fixed: `patch_alert_njfilter.py` (only NWS Mount Holly, no TEST titles), applied 20:23. Shim fixes: strip duplicate sender prefix (confirmed), new-node wording now "📡 Node heard: **name**". Emoji variant `patch_node_heard_party.py` ("... 🎉") written and tested, NOT applied. Charlie wants to learn APRS in depth later.
**Oct 21-22:** Orange Pi compatibility questions answered; EmergencyHam Network gateway idea researched into `docs/ehn-gateway-project.md` (continues in a separate chat); contact-form guidance for cnjmesh.me (Google Form, notifications); CalliesFarm duplicate announcements explained (two keys); MeshCore 350-contact limit researched and a "shadow mode new-node detection" test logged; TD-H9 firmware 1.0.38 decision pending; todo triage started (no restructure done).
**Oct 22 evening - Oct 23:** see section 4 (cnjmesh2 outage series, journald, alert office name, backups).

---------------------------------------------------------------------
## 4. Detail of the last 24 hours (Oct 22 20:30 ET to Oct 23 21:30 ET)
### cnjmesh2 instability (UNRESOLVED)
- Four unclean events in about a week. Oct 22 ~20:30: hung until power-cycled (20:40). Oct 22 20:54: Wi-Fi SDIO errors (`mmc1: Controller never released inhibit bit(s)`, `brcmf_sdio_read_control: read 2048 control bytes failed: -5`) then total freeze; watchdog reset it in about a minute. Oct 23 ~01:00: healthy right up to the last line, no error, abrupt stop, auto-reset. Matches upstream raspberrypi/firmware issue #1962 (6.12.47+rpt reported bad, 6.6.74+rpt OK); cause unconfirmed. `bootstatus`=0 is ambiguous. No RTC: use `up=` fields, not early-boot timestamps.
- Findings: the Oct 16 journald/watchdog fixes only took effect at the Oct 22 reboot (so earlier logs were lost); watchdog works (`bcm2835-wdt`, 15 s) and recovers it in ~1 minute.
- Installed: `cnjmesh2/flight-recorder/` (timer logs `up= load= memavail= swapused= temp= throttled= wifi= gw= mmc_errs=` once a minute to the persistent journal, tag `flight-recorder`). After any reset: `journalctl -b -1 -t flight-recorder | tail` and `journalctl -b -1 | tail -40`. Written but NOT installed: `cnjmesh1/ping-watch/`.
- Plan: (1) swap power supply and cable (ask what it uses), (2) USB Wi-Fi dongle with onboard Wi-Fi disabled, (3) replace the Pi. Agreed rule: if it ever needs a hand reset again, stop investing. Moving its jobs to cnjmesh1/3 was rejected (no headroom).
- Clue: Charlie keeps PuTTY sessions open; cnjmesh2's was dropped, which tipped him off.

### Journals were RAM-only
- Raspberry Pi OS ships `/usr/lib/systemd/journald.conf.d/40-rpi-volatile-storage.conf` (`Storage=volatile`): ~37 MB cap on cnjmesh1, lost at reboot. This is why alert log lines (e.g., the 2:07 PM frost message) and forecast logs vanished. Fixed with `/etc/systemd/journald.conf.d/50-persistent.conf` on cnjmesh1 (19:22) and cnjmesh3 (21:10); cnjmesh2 already effective. Lesson: after changing journald/watchdog settings, confirm they are active. Check: `systemd-analyze cat-config systemd/journald.conf | grep ^Storage`.

### Weather bot alerts
- Real Mount Holly Frost Advisory delivered Oct 23 (2:07 PM and 5:37 PM): NJ filter confirmed working.
- Bug found: office name rendered "MOUN" because the formatter used only the second word cut to 4 letters (`office_parts[1]`). Fixed by `cnjmesh1/meshcore-bot-custom/patch_office_full_name.py`, applied 20:07 (backup `weather_service.py.bak-officename-20261023-200714`), bot restarted 20:13, active on 910.525/500/SF10/CR5. Awaiting the next real alert to confirm "by NWS Mount Holly".
- Open observations: Discord said "til 7AM" while the log said "until Oct 24 9:00AM" (possible CAP `expires` overwrite, unverified); an unexplained 2:07 PM message; the bot keeps seen-alert ids in RAM so a restart may re-announce an active alert once.

### Backups (big piece of work)
- Audit from live commands found gaps: main `cnjmesh1-backup.sh` was safe for Malla/CoreScope (SQLite online backup), Postgres (`pg_dumpall`) and MySQL (`--single-transaction`) but plain-copied Graywolf (WAL mode, loses recent changes) and the shim DB, and missed the MeshCore Hub DB (422 MB, Docker volume), Meshview `packets.db`, `/opt/meshcore-bot`, `/etc/meshcore-bot/config.ini`, CoreScope config, units, journald drop-in, crontabs. cnjmesh3's script missed `~/meshcore-bridge-data` and `~/meshcore-mqtt-tilly`.
- Built/updated: `scripts/cnjmesh1-extra-backup.sh` (new), `scripts/cnjmesh-backup.sh` (cnjmesh3 additions), `scripts/cnjmesh1-backup.sh` (comment), `scripts/pull-cnjmesh1-backup.ps1` (pulls the extra archive too, real Documents folder), `scripts/verify-archive-sqlite.sh` (new light test restore), `docs/backup-guide.md` (new), `docs/backup-runbook.md` pointer.
- Runs Oct 23: `cnjmesh1-backup-2026-10-23_2029` 180M, `cnjmesh1-extra-2026-10-23_2043` 123M (14 components, all `quick_check` OK), `cnjmesh3-backup-2026-10-23_2110` 620K. All pulled to `C:\Users\charl\OneDrive\Documents\cnjmesh-backups` via the desktop shortcut for `C:\Users\charl\Documents\scripts\pull-cnjmesh1-backup.ps1` (answer Y to the Execution Policy prompt, or run with `-ExecutionPolicy Bypass`).
- cnjmesh2 deliberately has no archive (Jul 26 overload); a config-only backup after a live audit is still to do. Sep 2 SD image `cnjmesh1-sdcard-20260902.img.gz` (2.4 GB) exists on OneDrive, unverified. NO TEST RESTORE HAS BEEN DONE YET.

### Spare SD cards (plan)
- Charlie wants a new card per Pi, imaged from the live card, so a swap replaces weeks of rebuild. Sizes: cnjmesh1 58.9G, cnjmesh2 59.6 GiB, cnjmesh3 29.1G. A spare must be at least as large as the source, so 64 GB nominal is too tight for cnjmesh1/2: suggest 128 GB high-endurance (Samsung PRO Endurance or SanDisk MAX Endurance) for cnjmesh1 and cnjmesh2, 64 GB for cnjmesh3. Prices unchecked. Buy new from the manufacturer or Amazon sold-and-shipped, test with f3/h2testw, image with the Pi shut down (Win32 Disk Imager + Raspberry Pi Imager), refresh quarterly. Still need: does he own a USB microSD reader?

### Repo commits tonight
f60030e ... b114836, 8065be4 (end-of-session docs), then this handoff. `session-log.md` has the detailed entry "2026-10-22 (evening) to 2026-10-23 (evening)".

---------------------------------------------------------------------
## 5. Key technical knowledge worth keeping
- Two copies of meshcore-bot exist: the live one is `/opt/meshcore-bot` (service); `~/meshcore-bot` is a git clone. Always patch `/opt/meshcore-bot`; check `ls -l` dates on both. Config is `/etc/meshcore-bot/config.ini`.
- mesh-discord-shim: `app.py` is baked into the image; rebuild with `cd /opt/stacks/mesh-discord-shim && sudo docker compose up -d --build`. A DOWN alert in `#cnjmesh` during a rebuild is expected.
- MeshCore tooling: `meshcore-cli` over USB (`/dev/kpc1`, `/dev/kpr1`), repeaters via `meshcore-cli -r`; `set radio 910.525,500,10,5`; repeater `get radio` shows the saved value before a reboot. Do not touch the Observer serial port while the capture container holds it.
- SQLite in WAL mode: a plain `cp` of the `.db` misses changes (`-wal`/`-shm`); use the online backup API and `PRAGMA quick_check`.
- Raspberry Pi OS journald is volatile by default (fix above). Pis have no RTC: early-boot timestamps are unreliable.
- MeshCore 350-contact limit (companion `MAX_CONTACTS`, RAK4631 builds): the Observer overwrites oldest non-favourites; shadow-mode detection from the decoded packet stream is a logged test idea.
- Meshtastic MQTT: root `msh/US`, broker topic `msh/US/2/e/CentralNJ/+`.
- Cloudflare Error 1033 on malla2.cnjmesh.me means cloudflared on cnjmesh2 is down (usually the whole Pi).
- Some web sources are blocked from the sandbox (Facebook, YouTube, api.weather.gov); the shell cannot reach NWS.

---------------------------------------------------------------------
## 6. To-do digest (full text in `todos.md`; 108 items, triage never restructured it)
**A. Do first (this week)**
1. Test restore (todo added Oct 23): run `bash scripts/verify-archive-sqlite.sh ~/backups/cnjmesh1-extra-2026-10-23_2043.tar.gz` on cnjmesh1 and then the main archive; then Postgres/MySQL throwaway-container restores, newest-data check, cnjmesh3 config dry run, laptop copy `gzip -t`/7-Zip, Sep 2 image check; real proof by booting a spare-card image. Record results in `docs/backup-guide.md`.
2. Spare microSD cards: answer USB reader question, then shopping list.
3. cnjmesh2 power supply/cable swap; then dongle plan if it keeps resetting.
4. Inventory refresh (`scripts/collect-inventory.sh`) for cnjmesh1, cnjmesh3, then cnjmesh2 with care.
5. Confirm "by NWS Mount Holly" on the next real alert (passive).
**B. Backups follow-ups:** cnjmesh2 config-only backup; fold extra script into main; verification step for cnjmesh3 script; clean ~4.7 GB of old Malla snapshots in cnjmesh1 `~/backups` (decide first); schedule weekly timers + SSH keys so the laptop pull is unattended; record radio settings and identity-key handling; SD images for cnjmesh2/cnjmesh3.
**C. Security/hygiene:** rotate leaked credentials (Aug 30 Discord webhook incident, HIGH priority, still open); decide on committing APRS-IS passcode / coordinates; private-repo test (GitHub integration); Fing agent keep/remove.
**D. Mesh/infra:** SJMesh nodes missing from Meshview graph (relay topic omission; root cause known, fix not applied); CoreScope "No packets from meshomatic" banner decision; Tilly fork on KPR1 (blocked on Tilly) and KPR1 still 62.5 kHz; KPR3 admin login on 500 kHz fails; Observer clock ~27 h ahead; confirm Observer in CoreScope UI; Malla update + CVE-2026-43980 + CARTO watermark on Malla; KPN2 TCP/WiFi and antenna; cnjmesh1 wlan0 promiscuous toggling; health-check plan ("Pi Health Checks"); mesh-discord-shim silence alert (Oct 17) follow-up; optional ping-watch; improve `meshcore-bot-watchdog` (retry/reminders, approval pending); SATA SSD idea for cnjmesh1; Pre-Tilly master checklist.
**E. Bot/relay wording:** emoji patch `patch_node_heard_party.py` (unapplied); re-examine `#cnj-new-node-relay` wording (low); 2:07 PM frost message origin and 7AM vs 9AM mismatch; plain-English alert wording; forecast "Tonight" message missing Oct 21 (undiagnosed, logs lost to volatile journal); shadow-mode new-node test; CalliesFarm two-keys hub query; cnjmesh3 `iata` check (answered: `EWR`).
**F. Website:** deploy "Central & South New Jersey" edits to Netlify; broken News nav link (`/network-news.html`); Google Form email notifications + reply-address field.
**G. APRS/RF:** coordinated K2GIA-10 RF test (partner idea: N2ZAV near Easton PA); where is the UV-5R M antenna (roof vs whip); Oct 8 APRSThursday check-in; APRSdroid filter and K2GIA-5 to K2GIA-7 retest; K2GIA-9 `RFONLY,NOGATE`; K2GIA-10 syslog to lora-aprs.live; FTRN hot-node alert; Graywolf POLLERR/RT-override decisions; LoRa APRS physical work (not started, Charlie not ready); TD-H9 firmware 1.0.38 decision (lean: wait); heltec T096 battery splice; label KPC1/KPR1 boards; MURS RT27V test/replace; physical workshop organization (someday).
**H. Goals/ideas parked:** learn APRS in depth with hands-on tests (after housekeeping); EHN gateway (separate chat, `docs/ehn-gateway-project.md`); Nooelec/OrcSDR idea; Meshnology W12; SP0LND balloons; Tab5/C6L tracker (separate project chat); Amateur Extra study (separate chat).
**I. The triage restructure Charlie wanted (never finished):** split `todos.md` into active-only, `docs/ideas-and-someday.md`, `docs/todos-archive.md` (delete nothing), aiming for 1-2 active items. Pending answers on the first batch: close Malla "gateway diversity dropped to 1"; park the K2GIA-10 coordinated RF test; where the UV-5R M antenna is; close the Oct 8 APRSThursday item.

---------------------------------------------------------------------
## 7. Suggested first moves for the new chat
1. Read the files above and give Charlie a 4-line status.
2. Get the `verify-archive-sqlite.sh` output from cnjmesh1 and log the first test-restore result.
3. Ask the USB-reader question and deliver the SD shopping list.
4. Check whether cnjmesh2 stayed up (`uptime` and the flight recorder), and ask about the power supply.
5. Offer the todo triage in batches of ~5, plain chat, to reach the 1-2 item goal.
