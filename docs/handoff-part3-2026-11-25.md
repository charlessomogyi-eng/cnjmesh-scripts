# CNJ Mesh handoff, Part 3. Written Wed Nov 25 2026, about 1:30 PM ET

Purpose: let a fresh Claude chat pick up exactly where this one stopped, with the same working style, the same facts and no lost todos. This follows `docs/new-chat-handoff-2026-10-23.md` (Part 2). This chat ran from that handoff to Nov 25; the Nov 13 to Nov 25 stretch is in the most detail below because the repo's `session-log.md` stops at Nov 4.

**What this file is not:** it is not the todo list. The todo list is `todos.md` (live) and `docs/todos-full-2026-11-12.md` (frozen word-for-word copy). Section 7 below indexes every item in `todos.md` so you can see nothing is missing, but read `todos.md` itself before acting on any item.

Evidence tags used in this repo: **[V]** verified from output, a file or a source read this session; **[S]** secondhand (Charlie said it, or a screenshot/post); **[I]** inference; **[UNKNOWN]** nobody checked. Keep using them.

---

## 1. How to access, update and review the repo (read this first, do not guess)

**The repo:** `github.com/charlessomogyi-eng/cnjmesh-scripts`, branch `main`, **public**. Cloned on cnjmesh1 at `~/cnjmesh-scripts` (a second clone also exists at `/opt/cnjmesh-scripts`, which services may read; do not assume the two match). Charlie only ever runs `git pull` on a Pi. He never runs `git add`, `commit` or `push` and does not want a handoff step for it.

**Reading it (any chat with a web or shell tool).** These URLs work; do not reason about whether the repo "might be private", just fetch. If one comes back empty, retry once before concluding anything.
```
curl -s https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/CLAUDE_CONTEXT.md
curl -s https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/todos.md
curl -s https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/known-issues.md
curl -s https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/cnjmesh1-operations.md
curl -s https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/docs/handoff-part3-2026-11-25.md
```
Rendered GitHub pages (`github.com/...`) may be blocked from a sandbox; `raw.githubusercontent.com` is the one that has worked. Other sites this chat's sandbox could not reach: `dev.h9toolbox.com`, `jonadams.com`, `cdme.sh` pages, the CA2RXU iGate GitHub page and the `Deadly447/H9-OPS` repo page. When a fetch is refused, say so and ask Charlie to paste the page text; do not retry through mirrors.

**Updating it (Claude Code session).** Charlie expects you to write changes and push them yourself:
1. If the repo is not already in the session, attach it with the `add_repo` tool (owner `charlessomogyi-eng`, repo `cnjmesh-scripts`, access `push`), run the clone command it returns, then register it with `register_repo_root`. Do not pre-check the repo with curl or `gh` first; the tool does the real check.
2. **`git pull` before every edit session.** Other chats (ham radio, HT programming, weather, backups) also push to this repo. Example: the NIFOG notes in `radio/ht/` arrived Nov 24 from another chat.
3. Edit, then `git add -A && git commit && git push origin main`. After pushing, run `git log --oneline | head -1` and tell Charlie the commit.
4. Every commit message ends with these two lines:
   - `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`
   - `Claude-Session: <the session URL your harness gives you>` (the URL in this chat's commits was `https://claude.ai/code/session_01YDdBLfvaEFK5cZ4d1UqRnj`; a new chat will have its own, use the one in your own system reminder)
5. If the push is refused or the repo is not attached: say so plainly, do not claim a push happened, and tell Charlie what is needed (attach the repo to the chat or session). Do not ask him to paste a token as a first step and do not lecture him about tokens; he rotates them himself.
6. A plain claude.ai chat without the repo cannot push. In that case write exact file text for him and say clearly that nothing was saved.

**Reviewing before you answer (do this instead of guessing).**
- `git log --oneline | head -40` for what changed recently; `git log -p -- todos.md | head -200` for how an item evolved; `git log --all --oneline -S"<text>"` to find when something was added.
- `grep -rn -i "<term>" --include=*.md .` (skip `website/` and `CLAUDE_CONTEXT-backup-2026-07-24.md`, which are noisy) before saying "the repo does not mention X". Nov 21 example of what not to do: I said I could not find anything on RXT while `docs/lora-aprs-reference.md` already had a Sep 22 note on it. Nov 25 example: I said KPR3's firmware version was unknown while Charlie's own earlier chat had it (v1.17.1). Search the repo, then search his past chats (`conversation_search`), then the web, and only then say "unknown".
- Check `known-issues.md` before calling any configuration correct from a screenshot; a filled-in field is not a working connection.
- Notes go in the right file: live work in `todos.md`; facts about infrastructure in `cnjmesh1-operations.md`; per-topic findings in `docs/`; narrative in `session-log.md` (append-only, newest at the end, about 2,900 lines, never re-read in full). When an item is finished it moves to `docs/todos-archive.md` with a one-line reason.
- End-of-session routine (from `CLAUDE_CONTEXT.md`): update `todos.md`; update `cnjmesh1-operations.md` if infrastructure changed; if anything was installed, moved or reconfigured on a Pi, have Charlie run `scripts/collect-inventory.sh` there and commit the refreshed `install-map-<host>.md`; append a dated `session-log.md` entry; push.

**Read order for a new chat:** `CLAUDE_CONTEXT.md`, this file, `todos.md`, `known-issues.md`, `cnjmesh1-operations.md`, then the `docs/` file for whatever topic Charlie raises (section 8 lists them). Skim `docs/lessons-learned-get-well-plan.md` once.

---

## 2. Working agreement (how Charlie wants Claude to behave)

- **Names:** Charlie (K2GIA), never Charles. Use his name rarely ("here and there"); he has had to tell several chats to stop.
- **Tone:** partnership. Direct, bottom line first, natural, not sheepish. Own a mistake in one line and move on. When he says he is tired or busy, keep replies short and shrink the plan to the fewest steps.
- **Plain chat.** Do not use multiple-choice or checkbox prompts (do not use AskUserQuestion). He also dislikes the numbered step-card widgets; write steps as plain text.
- **Commands:** every shell command in its own fenced code block, one command per block, each preceded by the host it runs on (cnjmesh1, cnjmesh2, cnjmesh3 or his Windows laptop), and say whether it finishes on its own or needs Ctrl+C (tailing commands like `journalctl -f`). He has several SSH sessions open at once; read the prompt in pasted output to confirm he ran it on the right host. He runs every command himself; never remind him you lack SSH. Do not wait for permission to hand over a command (restarts included), and end replies with what is still pending when you have been working on Pis.
- **Nothing changes on a Pi, broker, node or service without his OK.** Commands are handed over freely; state-changing steps need his go-ahead and must name the host. Never change a host he did not name. Do not run heavy jobs on cnjmesh2.
- **Do not guess.** Search the web and check the repo and docs before suggesting anything or calling something a problem (he and Claude spent a lot of time making the setup secure). Tag verified versus inferred.
- **Stay on the question he asked.** On Nov 23 to Nov 24 I wandered (guessing what a friend meant, inventing "a service you sign up for", putting words in his mouth in a drafted message). Before drafting anything he will send as himself, restate in one line what you understand and fix it if he corrects you. If the evidence runs out, say what you know, what you do not, and ask the one question that settles it.
- **Do not send him off to contact other people as a first step** (broker operators, bot owners). Work it out ourselves first; outreach only when it is the sole route.
- **Public repo hygiene.** Never put these in the repo or print them in chat unprompted: webhook URLs, real passwords (except openly published community-broker ones, which he does not mind), private keys, the n2yo key, the MeshOMatic website password, exact home coordinates, anything about a neighbor's equipment or node locations, his personal email addresses (including the MeshOMatic sign-up address and his calendar accounts), and the names of family members and some friends (when unsure whether a name belongs in the repo, leave it out and ask). Do not remind him about pasting GitHub tokens.
- **Calendar:** personal entries go on his personal Google calendar, never on the shared ASCONJ calendar (members and others can see that one). If you need the exact account, check your memory or ask him; it is deliberately not written here.
- **Firearms** material stays out of radio and mesh chats and out of the repo.
- **Downloads:** if he wants a document on his phone, send a real `.docx` file (he struggles with in-app docs).
- **Duplicate detail:** he keeps separate chats by topic and dislikes the same detail repeated across them. Keep each chat to what it needs.
- **Patch pattern:** exact-match-or-abort Python script, `--dry-run`, timestamped backup, compile check, restart as a separate step.
- **He uses** the Android Meshtastic and MeshCore apps, Windows PowerShell, and Facebook Messenger/Facebook for the TIDRADIO H9 group and Discord for the mesh groups.

---

## 3. The network (stable facts)

Target MeshCore settings for every CNJ node: **910.525 MHz, 500 kHz BW, SF10, CR5** (moved from 62.5 kHz/SF7 on Oct 11 to 14). **KPR1 is the only MeshCore node still on 62.5.**

- **cnjmesh1** 10.0.0.181, Pi 4B, user `somog`: meshcore-bot (`/opt/meshcore-bot`, radio KPC1 on `/dev/kpc1`), mesh-discord-shim (`/opt/stacks/mesh-discord-shim`, Docker; its `app.py` is baked into the image so changes need `sudo docker compose up -d --build`; the shim's own app code is not in the repo, only patches), MeshCore Hub (`meshcorehub.cnjmesh.me`), CoreScope (`/home/somog/meshcore-data`), Meshview 4.0.0 (`/home/somog/meshview`, `meshview.cnjmesh.me`, Fahrenheit patch applied Nov 13), a Malla copy, Mosquitto (Docker; bridges: meshtastic_public, liamcottle, meshomatic), Graywolf (2 m APRS on K2GIA-1, web UI port 8082), Postgres, MySQL, watchdogs, Fing agent.
- **cnjmesh2** 10.0.0.91, Pi Zero 2 W, Wi-Fi only, user `somogyic`, 416 MB RAM: malla2 (`malla2.cnjmesh.me`), Mosquitto (Docker), cloudflared. Has reset by itself several times since Oct 16 (see 5a). Never run heavy jobs here.
- **cnjmesh3** 10.0.0.186, Pi 3B+, user `somog`: the **Observer** (RAK4631 companion firmware v1.16.0) and **KPR2** (Heltec V4 repeater, `/dev/ttyACM*`), Docker containers `meshcore-packet-capture` (config in `/opt/meshcore-packet-capture/config.d`, publishes to 4 brokers including local, LetsMesh and MeshOMatic) and `meshcore-mqtt-bridge`. Observer IATA code is **EWR**.
- Pis are never wired; the house has no Ethernet drops. Do not propose wired fixes.
- **Nodes:** KPC1 (weather-bot companion, cnjmesh1), KPC2 (T-Deck Plus companion; swollen battery, board "fried" per Charlie Nov 10), KPC3 (Heltec T096, battery splice open), KPR1 (Tilly bridge, 62.5), KPR2 (Heltec V4 repeater, cnjmesh3), **KPR3** (backyard solar repeater, RAK4630 on a RAK19003, LiPo, 13 ft mast with a 9-element Yagi, flashed Oct 2026 with MeshCore Repeater v1.17.1 per Charlie's flashing chat; formerly the Meshtastic node KPN1), **Observer** (public key starts `a8c40bf3`), Meshtastic nodes KPN6, KPN8, KPN9 (2.8 test builds), gateways CJG1 and CJG2.
- **APRS:** `K2GIA-1` = 2 m Graywolf station (UV-5RM plus Digirig, whip in the garage, digi WIDE1-1 plus iGate, TX low); `K2GIA-5` = APRSdroid phone; `K2GIA-7` = TD-H9 (dedicated APRS radio, do not reprogram); `K2GIA-9` = LoRa APRS tracker (LilyGo T3 V1.6.1, 433.775); `K2GIA-10` = LoRa APRS fixed node (CA2RXU iGate v3.2.4, web page at `http://10.0.0.74`). Do not mix up K2GIA-1 (2 m) and K2GIA-10 (LoRa); this was the most frequent mistake in earlier chats.
- **Discord channels:** `#centralnj-mc-channel-relay`, `#cnj-new-node-relay` (the "Node heard: name" posts, built by the shim from the MeshCore Hub), `#cnj-infrastructure-alerts` (private watchdog alerts), `#aprs-rf-nj` and `#aprs-internet-nj` (Graywolf bridge).
- **Other facts:** the Cloudflare account for `cnjmesh.me` login is not "Sign in with Google"; see `CLAUDE_CONTEXT.md` for the details. The Icom 2730 owns the roof dual-band antenna. KPR3's remote-admin login on 500 kHz fails while packets relay (`known-issues.md`).

---

## 4. What happened in this chat, Nov 13 to Nov 25 (newest last)

All times America/New_York. Anything not marked pushed was a chat answer only.

- **Nov 13: MeshOMatic account.** Web username is `user_somog` (free, Limited access). The sign-up address was confirmed from the Oct 26 email header and is not recorded in the repo on purpose. The password reset email was not arriving. The "Fix clock" button on MeshOMatic needs a login. Charlie has not confirmed he got back in.
- **Nov 13: Observer clock (27 h ahead).** Read upstream MeshCore source: the companion's set-time command refuses to go backwards (matches the Oct error), and on every boot it sets the clock to the newest stored contact timestamp plus one second. Hypothesis [I, untested]: a contact with a future timestamp drags the clock forward again on every reboot. Candidate fix [untested]: clear the Observer's stored contacts, reboot, then `clock sync` forward. Not done. Pushed to `todos.md`.
- **Nov 13: Wern/Eern bug.** NWS alert text on the Meshtastic bot said "Wern Monmouth / Eern Monmouth": `abbreviate_noaa()` replaces words as substrings. Fix: whole-word replacement. Charlie said yes. Nothing written or applied yet; the Pi's copy of `case_insensitive_replace()` has not been read. Pushed to `todos.md`.
- **Nov 13: swap-drive blurb** answered in chat; the `free -h; swapon --show` check on cnjmesh1 is still Charlie's to run if he cares.
- **Nov 13: SJMesh nodes missing from the Meshview graph.** Cause found in the repo: the Aug 14 swap to `sjmesh-relay.service` dropped the SJMesh channel topic. Meshview keeps its own topic list in `~/meshview/config.ini` and retains 14 days. Charlie confirmed they used to show as disconnected dots. Not restored; two questions to him are unanswered.
- **Nov 14: shim "no events" alerts.** The repo threshold is 90 minutes (since Nov 11) but alerts still say 30, so the deployed copy at `/opt/mesh-discord-shim-watchdog/watchdog.py` is probably the old one [unverified]. The shim logs adverts too (12 to 62 events per hour on the one day measured, longest gap 45 min). Charlie suggested a 24-hour no-activity rule because the 7 AM forecast is the only regular traffic; no change made. Nov 19 the same alert appeared again.
- **Nov 14: CoreScope coverage idea.** Charlie asked whether other observers can feed ours; "let's research in a bit". Todo exists (always set `iataFilter`; Aug 4 flood risk; do not expose the private Mosquitto).
- **Nov 15 / 19: H9 Toolbox** documented in `docs/h9-toolbox.md` (satellite pass app, packet/WinLink KISS TNC beta, second TD-H9 ordered, beta instructions PDF summarized). Do not install on K2GIA-7.
- **Nov 18: curiosity Q&A, no repo change:** 433 MHz sensors, ISM bands, what Home Assistant uses (software; radios are Zigbee/Thread/Z-Wave/Wi-Fi/Bluetooth), a LetsMesh analyzer view defaulting to EWR (he wants it), how to read a Meshtastic traceroute (dB values are per-hop SNR), his LoRa APRS board is a LilyGo T3 V1.6.1 and can be tuned to other 433 MHz frequencies (he was only learning).
- **Nov 19: MeshOMatic repeated the Observer clock email;** the offset is steady (about 26 h 52 min), not drifting.
- **Nov 20 to 21: LoRa APRS.** The KE2BSB EMAIL-2 message was explained (interactive APRS email gateway); the `#aprs-rf-nj` channel is quiet because it only carries RF-heard messages. An Arizona operator's RXT page prompted a question; my first answer wrongly said nothing was known. **Correction (pushed):** the repo already documents RXT in `docs/lora-aprs-reference.md` (Oct 13 update: Graywolf plus LoRa APRS via RXT, two unmerged experimental forks, "watched, not adopted"). **Decision recorded Nov 21:** K2GIA-10 goes upstairs, powered from a cnjmesh3 USB port, on an indoor 433 MHz antenna; trackers (K2GIA-9) stay mobile. Charlie then said "I have 2 lora aprs boards" and asked how to tell which is which; my answer was the `http://10.0.0.74` unplug test (the board that answers there is K2GIA-10), then label with tape. Whether the screen shows the node name is unknown (the repo says he does not use the screens).
- **Nov 21 and Nov 24: malla2 UptimeRobot emails** (DOWN 4:59 AM, UP 5:04 AM, stacked three deep; DOWN 6:46 PM, UP 6:51 PM). Matches the known cnjmesh2 self-reset problem. I gave four read-only diagnostic commands (see 5a); Charlie has not reported results.
- **Nov 23: KPR3 brownout post.** A Susquehanna Valley Mesh post says recent RAK4631 repeater builds dropped the `NRF52_POWER_MANAGEMENT` build flag, so a solar repeater that runs its battery flat can get stuck in a brownout loop. [V, upstream tags] `repeater-v1.17.0` and `v1.17.1` enable the flag; `repeater-v1.18.0` does not. KPR3 should still be fine on v1.17.1. Rule recorded: do not update KPR3 to 1.18.0 until the flag is back; do not flash the poster's Drive `.uf2`. Pushed.
- **Nov 23: H9 OPS** (Android APRS dashboard for the TD-H9) needs patched firmware `TD-H9-V1.0.38.P2.fw`; a commenter says it replaces H9 Toolbox rather than adding to it. Noted in `docs/h9-toolbox.md`. Not for K2GIA-7.
- **Nov 23 to 24: Tck (a friend and local MeshCore admin) and the 62.5 test.** What he wants, from his own words [S, Discord screenshots]: his group has new users as far south as Bordentown, Trenton and Princeton, they struggle even with a repeater at 550 ft on the Sourlands, and they want to move from 500 to 62.5 and "see if we can talk". He also asked how to set up a CoreScope observer on 62.5 (he has two idle Heltec V3s and will not buy a Pi). I advised (all in chat, nothing pushed): a Heltec V3 can be a Wi-Fi observer with community observer firmware (a separate community build, not necessarily on the official flasher; I could not open the flasher pages); the LetsMesh Analyzer is hosted so nothing needs hosting; CoreScope itself must be hosted by someone; for the test, everyone switches at the same time with the same settings (910.525 / 62.5 / SF7 / CR5), then each sends a zero-hop advert and checks who heard it directly. Unverified: that LetsMesh shows a 62.5 observer; that any public CoreScope takes outside feeds. Charlie's own CoreScope, per a Sep 2 repo note, already reads sources `local`, `letsmesh-us`, `letsmesh-eu` and `meshomatic`; I gave a read-only command to list the sources and filters but Charlie has not run it. If a LetsMesh observer's IATA code is not in our source's `iataFilter` it would be dropped. Offer to Tck (not confirmed by Charlie): add his IATA code to our filter, which is a config edit on cnjmesh1 needing Charlie's OK.
- **Nov 24: a second node named "CNJ Mesh Observer"** appeared in `#cnj-new-node-relay` at 4:55 AM with key `101afe5e056bbae0...`, which is **not** Charlie's Observer (`a8c40bf3...`). Charlie says he has not touched the Observer since building it and switching to 500, so its identity almost certainly did not change. Tck says it is not his; he guessed it belongs to someone in the Princeton area. Unresolved and harmless. Optional confirmation when Charlie can: read the Observer's own key in the MeshCore app.
- **Nov 24: NIFOG.** Charlie shared CISA's National Interoperability Field Operations Guide v2.0 (Aug 2021). I read the intro, contents and amateur pages (103 to 108) and summarized. A 2.01 edition and an eNIFOG app exist per CISA's factsheet. Another chat had already committed `radio/ht/nifog.md` and CHIRP CSVs on Nov 24 (commit 4698c4d). Reminder: the national public-safety interoperability channels are not for ham transmit; do not add transmit-enabled entries.
- **Nov 24: a TD-H9 user's post** (hears two digipeaters, not mobiles) prompted Charlie's new test idea; see 5i and the new todo (pushed Nov 25).

**Repo commits made by this chat since Nov 13 (all on `main`):** MeshOMatic and Observer clock notes (`9340159`, `1eaed09`, `976fef8`, `b7d6c05`), Wern/Eern todo (`28a9224`), CoreScope research todo (`6403f6e`), H9 Toolbox docs (`70c6997`, `4c8f1a9`, `8707668`, `d02ef86`, `2e8b1a7`, `19db2de`, `433d16c`), Meshview Fahrenheit patch (`72bdef2`, `2b9d952`), RXT and LoRa APRS decision (`3e5ae9d`, `619538e`, `70a789d`), KPR3 brownout (`c865022`, `8813589`), plus the Nov 25 commit that adds the 2 m mobile test todo and this file.

---

## 5. Threads in flight: exact state and the next step

**a. cnjmesh2 resets and malla2 alerts.** State: UptimeRobot DOWN/UP pairs about 5 minutes apart on Nov 21 (twice) match the known self-resets (`known-issues.md`: cnjmesh2 reliability; watchdog resets it in about a minute). Cause still unconfirmed. Whether the Oct 23 power-supply-and-cable swap was ever done is **not recorded**; Charlie has not answered. Next: Charlie runs these on cnjmesh2, each finishes on its own: `uptime -s`; `journalctl --list-boots --no-pager | tail -15`; `cat /sys/class/watchdog/watchdog0/bootstatus`; `journalctl -b -1 -t flight-recorder --no-pager | tail -5`. Read the results: boot times matching the alert times mean a reset; no matching boot means the Pi stayed up and the cause is cloudflared or the network. Plan if resets continue: swap PSU and cable, then USB Wi-Fi dongle, then replace. Rule agreed earlier: if it ever needs a hand reset again, stop investing.

**b. Observer clock fix.** Not started. Needs: the exact `meshcore-cli` command to clear contacts (unresearched), whether the Observer needs its contacts, a plan to pause the `meshcore-packet-capture` container on cnjmesh3 during the work, and a MeshOMatic login for the "Fix clock" button as an alternative. After any fix, nodes that heard future-dated adverts may ignore the Observer's newer adverts for about a day.

**c. MeshOMatic bridge loop.** `meshomatic` bridge on cnjmesh1 sends CONNECT about every 71 seconds and never gets a CONNACK (also seen Jul 4). Five read-only checks are written out in `todos.md`. Hypothesis [unverified]: the `user_somog` login is limited to 2 simultaneous connections and shared by three clients. Password reset still unconfirmed.

**d. Wern/Eern patch.** Next: read-only look at the Pi's `case_insensitive_replace()` (Charlie runs the command), write the patch in `cnjmesh1/meshing-around-custom/` following the patch pattern, hand over the dry-run, then apply on his OK.

**e. Shim watchdog threshold.** Next: Charlie greps the deployed `/opt/mesh-discord-shim-watchdog/watchdog.py` for its threshold (read-only; confirm whether it still says 30). If it does, deploy the repo copy (90 minutes) as a separate OK step. Optional later: find the longest quiet gap over several days before deciding on a longer rule.

**f. SJMesh in Meshview.** Next: Charlie runs on cnjmesh1 `grep -n -i topic ~/meshview/config.ini` (read-only) to confirm the SJMesh channel topic is missing, and answers whether he wants it back and whether the Channel dropdown matters. Restoring is a config change needing his OK; the dots-and-lines look was how SJMesh always appeared.

**g. Duplicate "CNJ Mesh Observer" node.** Nothing needed. If Charlie wants closure: read the Observer's own public key in the app (`a8c40bf3` expected); ask the owner (Tck guessed a Princeton-area user) to rename theirs; I recommended no action.

**h. Tck's 62.5 test and CoreScope.** Done in chat: explanation and draft messages (Charlie chose his own wording and sent his own replies). Open: the read-only CoreScope `mqttSources` check (command given, not run), whether to offer Tck an IATA-code addition, and Tck's answer on what his observer publishes to and what code he would use. Do not build anything for it until Charlie says what he wants. Do not describe CoreScope as "a service you sign up for"; it is software someone hosts.

**i. 2 m mobile reception test (K2GIA-1 and the TD-H9).** New todo is in `todos.md`. Open question to Charlie: which direction to measure first. Before the test: confirm K2GIA-7's beacon interval and path on the radio; check K2GIA-1's Graywolf receive level (the -11.5 dB gain was tuned for the old radio).

**j. LoRa APRS upstairs move.** Decision recorded. Open: which of his two boards is K2GIA-10 (unplug test at `http://10.0.0.74`); whether the second board is the RX-only unit or the tracker; antenna choice and connector type; cnjmesh3 USB power budget (it already runs the Observer and KPR2); whether the roof antenna can be released (it is reserved for the Icom 2730). After any move, retest K2GIA-9 to K2GIA-10 digipeating.

**k. H9 Toolbox / H9 OPS / second TD-H9.** Waiting on the second TD-H9. Open: read the GitHub README and patch instructions for both (Charlie pastes the page text), Winlink gateway lookup near Kendall Park, review of the KISS bridge code if he enables read access to `melidosian/h9toolbox`. Never on K2GIA-7.

**l. KPR3.** Optional: confirm it still reports v1.17.1 (app or remote CLI; its remote-admin login on 500 is a known problem, see `known-issues.md`). Do not update to 1.18.0 until the flag is back. Unknown: whether it has ever run flat.

**m. 7 AM / 7:05 AM weather bots.** Both watchdogs deployed. Whether the Nov 14 and later 7:05 MeshCore forecasts posted was never confirmed. The wide-area alert patch (`locationdata-alert-wide.diff`) is on hold (Charlie said maybe not).

**n. Spreadsheet review.** `CNJ-mesh-todo-review-2026-11-12.xlsx`: Charlie said he would upload the marked file later. Reading rules for his marks and the consolidation of the private-repo tasks are written at the top of `todos.md`.

**o. K2GIA-1 follow-ups.** Spare UV-5RM swapped Nov 11; clean at last check; still to do: kernel USB log check, confirm aprs.fi, add ferrite chokes on a separate day, a few more clean days; Graywolf health-watchdog auto-recovery upgrade written but not deployed.

---

## 6. Decisions waiting on Charlie (ask only when relevant, one at a time)

1. Move cnjmesh2's alerts and reliability forward (swap PSU/cable)?
2. Offer Tck an IATA-code addition to our CoreScope?
3. Which direction to measure first in the 2 m mobile test?
4. Which LoRa APRS board goes upstairs and what antenna?
5. Fix the Observer clock (needs contact-clearing research and a pause of the capture container)?
6. Restore the SJMesh feed in Meshview?
7. Keep or remove the Graywolf RT-scheduling override; K2GIA-7 firmware 1.0.38 update decision (Oct 21 item).
8. The marked spreadsheet and the consolidation of old todos.

---

## 7. Index of everything in `todos.md` (about 255 lines as of Nov 25; read the file for the full text)

**Top of file:** housekeeping rule; layout note; pending spreadsheet review with how to read his marks.

**Active now (14 items):** K2GIA-1 PTT/USB loss (todo 17); weather bots 7:00 and 7:05 (todo 20); Wern/Eern fix; MeshOmatic bridge CONNECT loop; CoreScope subscription research; RXT (play); `mesh-discord-shim` no-events alert (todo 18); watchdog audit (todos 14 and 16); Sourland ridge repeater "Beef Sourland 500 NJ-Me" (todo 19; keep operator details out of the repo); MeshCore Hub "Network Info" box showing old radio settings (todo 21); router reservations (KPN6 10.0.0.202, CJG1 10.0.0.19, CJG2 10.0.0.234); cloudflared upgrade (cnjmesh3 check, delete `.bak`); KPR3 brownout check; **new Nov 24: 2 m mobile reception test.**

**Everything else (one line each, pointers into the frozen file):**
- Plan: make the repo private and prove Claude can still push (6 steps).
- Play list (8 items): Winlink APRS gateway WLNK-1; learn APRS by playing; learn how MQTT works; KPN9 Long Turbo listen; H9 Toolbox satellite predictor; Tab5 with OrcSDR; MeshCore regions vs scopes (background); TD-H9 drive test; K2GIA-7 not showing on aprs.fi.
- Nov 3 to 4 pick-up list: KPN9, KPN8 and its test plan, Tab5 build steps, carried-over items (KPC2 cell, KPN6 reservation, website deploy).
- Oct 28 to 31 list: MQTT Explorer session; Graywolf 0.13.13 to 0.14.14; MQTT broker health review; Meshtastic 2.8 upgrade plan; export every MeshCore node's private key (identity backup); CJG1 TCP 4403 conflict; clean up the CentNJ-MQTT channel; 7 AM / mesh_bot watchdog; KPN6 noise floor (-94 dBm); website buttons that turn red when a tool is down; maintenance pause for watchdogs; leftovers (cloudflared check, About-page note on what Malla collects).
- Two watchdogs planned: SJMesh outbound health; CentralNJ key-mismatch canary.
- SJMesh outbound path (live since Oct 26): kill switch, what is unknown, CJG1 pointer.
- Tilly's fork on KPR1 (blocked on one fact: what makes the device push companion LOG_DATA frames over serial); Tilly's endpoint also cycles.
- Future: SATA SSD for cnjmesh1. Reference docs: RESILIENCE-PLAN, PREVENTION runbook, lessons learned, pre-Tilly master checklist.
- Smaller items: Graywolf cpal/ALSA POLLERR; APRStastic experiment; `whorepeated.sh`; CoreScope `local` source instability; per-source freshness watchdog; radio tuning (KPR2, Observer); MeshCore regioning talking points; LetsMesh map discrepancy; KB2EAR-2 missing from the CNJ feed; mr-tbot mesh-api pointer; workshop organization; service-level heartbeat; Fing Agent stale alerts; missing CentralNJ messages on KPN6 (Aug 18); resilience/security review ideas; port `ingest-rate-watchdog` to cnjmesh2.
- Aug 18 to 30 carried: LoRa APRS message packets to Discord (blocked on hardware); retry old LoRa APRS bot queries; doc consolidation once K2GIA-9 is done; point K2GIA-10's syslog at `lora-aprs.live`; FTRN hot-node alert; K2GIA-9 `RFONLY,NOGATE`.
- Oct 13 handoff merge: coordinated RF test for K2GIA-10 (possible test partner N2ZAV); K2GIA-9 BLE KISS question; ODmaster/Graywolf version checks; the public-repo decision on the APRS passcode and K2GIA-1 coordinates; meshcore-bot alert truncation fix awaiting a real alert; Oct 23 frost advisory text mismatch; RXT watch; weekly APRS check-in nets; Graywolf RT-override decision; diff the live Graywolf Discord bridge against the repo copy; KPR3 remote-admin login on 500; **Observer clock** (with the Nov 13 and Nov 19 findings); KPR1 holdout on 62.5; `path.hash.mode` on KPR1/KPR2; KPR3 health check Nov 8; confirm KPR3 reaches Tck's area via the Yagi (and the TX-power/grant caution in `cnjmesh1-operations.md`); community notice of the cutover; confirm the Observer model (WisMesh Pocket v2 vs Mini).
- Heltec T096 (KPC3) battery splice; `meshcore-mqtt-bridge` and KPR2 question; Oct 14 weather-bot items (alert test result, watchdog improvement pending approval, radio-offline alerts, label KPC1 and KPR1).
- Future: SP0LND balloons; LoRa APRS physical work checklist (upstairs node DECIDED Nov 21; hardware status; antenna; button and IO15 for K2GIA-9; retest after any move).
- Ideas and carried (Oct 16 to 22): Meshnology W12; Malla CARTO watermark; new-node wording; new-node announcements from decoded packets; 350-contact limit research; TD-H9 1.0.38 decision; EHN gateway idea; Nooelec SDR plus OrcSDR; LV Mesh 62.5 vs 500 bridge watch; cnjmesh1 wlan0 promiscuous toggling; cnjmesh2 resets and reliability decision; cnjmesh2 OS and firmware update; Pi health-checks brainstorm; test-restore of backups; backup open items (`docs/backup-guide.md` section 7); inventory refresh; spare microSD cards; automatic backups to laptop/OneDrive; Retivis RT27V MURS radios (time-sensitive).
- KPC2 swollen battery (replace cell, disposal, size findings); KPC3 channel keys to confirm; narrow weather alerts to NJ-only (Oct 24).

If you add or finish an item, change `todos.md` and, if it matters for the next chat, the matching line in section 5 of a newer handoff, not this one.

---

## 8. Where things are documented (docs map)

APRS 2 m: `docs/aprs-2m-graywolf-reference.md`, `docs/aprs-bulletins-and-bridging-reference.md`, `docs/k2gia-5-aprsdroid-reference.md`. LoRa APRS: `docs/lora-aprs-reference.md`. TD-H9: `docs/td-h9-app-field-reference.md`, `docs/td-h9-radio-manual-condensed.md`, `docs/td-h9-odmaster-aprs-messaging-bug.md`, `docs/kisslink-*.md`, `docs/h9-toolbox.md`. Handhelds and HT programming: `radio/ht/` (README, `nifog.md`, `local-repeaters.md`, `W2NJR.md`, `whiting-path.md`, `codeplugs/`). MeshCore: `docs/meshcore-repeater-settings.md`, `docs/node-inventory-2026-11-01.md`, `docs/letsmesh-and-ozneteast-notes.md`, `docs/centralnj-*.md`. MQTT: `docs/mqtt-topology-and-landmines.md`, `docs/mosquitto-bridge-flood-fix.md`, `docs/ports-quick-reference.md`. Meshtastic: `docs/meshtastic-2.8-explained.md`, `docs/meshtastic-gateway-mqtt-settings.md`. Weather bots: `docs/nws-weather-bot-reference.md`, `docs/coverage-area-counties.md`. Backups and resilience: `docs/backup-guide.md`, `docs/backup-runbook.md`, `docs/RESILIENCE-PLAN.md`, `docs/PREVENTION-AND-INCIDENT-RUNBOOK.md`, `docs/cnjmesh1-recovery-checklist.md`. Watchdogs: `watchdogs/`. Per-host installs: `install-map-cnjmesh1.md`, `-2.md`, `-3.md`. Website: `docs/website-update-howto.md`. Old handoffs: `docs/new-chat-handoff-2026-10-23.md`, `docs/sjmesh-duplicate-block-handoff-2026-08-14.md`, `docs/AUG4-SESSION-SUMMARY.md`.

---

## 9. Traps and lessons from this chat

- Do not answer "nothing found" before searching the repo, Charlie's past chats and the web (RXT, KPR3 version).
- A MeshCore node's name is free text; identity is the public key. Two nodes can share a name.
- CoreScope is software that someone hosts; an observer feeds MQTT; a CoreScope shows only the sources and airport codes its owner configured. LetsMesh Analyzer is a hosted viewer. Do not mix these up when advising Tck or anyone else.
- A 62.5 node cannot hear a 500 node. Any frequency test needs everyone switched together and a fallback time.
- K2GIA-9 (LoRa, 433.775) cannot be heard by K2GIA-1 (2 m, 144.390).
- Do not put words in Charlie's mouth when drafting messages he sends as himself; check his wording first.
- Sandbox network: `raw.githubusercontent.com` works for reading; many other sites are blocked. Say so and ask for pasted text.
- Public repo: scrub before every commit (list in section 2).
