# 2 m APRS: start here

Written Nov 26 2026 for a chat dedicated to 2 m APRS (K2GIA-1, the two TD-H9 radios, learning APRS). This file is the live 2 m APRS to-do list. Read it first, and open other files only when a topic needs them.

Tags: **[V]** verified from output, a file or a source read at the time; **[S]** Charlie said it, or a screenshot or post; **[I]** inference or suggestion; **[?]** unknown or not checked.

## 1. How to read and update the repo

- Repo: `github.com/charlessomogyi-eng/cnjmesh-scripts`, branch `main`, **public**.
- Reading with a web tool: `https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/<path>`. Retry once if a fetch comes back empty.
- Updating (session with repo tools):
  1. Attach it with `add_repo` (owner `charlessomogyi-eng`, repo `cnjmesh-scripts`, access `push`), run the clone command it returns, then `register_repo_root`.
  2. `git pull --ff-only` before every edit. Other chats push to this repo.
  3. Edit, commit, `git pull --rebase`, `git push origin main`. End commit messages with the attribution lines from your own session. Tell Charlie the commit.
  4. If a push fails or the repo is not attached, say so. Never claim a push that did not happen.
- A chat without the repo cannot save anything: give him the exact text and say it was not saved.
- Charlie only runs `git pull` on a Pi. He does not commit or push, and does not want a handoff step for it.
- Search before saying something is unknown: `grep -rn -i "<term>" --include=*.md .` (skip `website/` and the `CLAUDE_CONTEXT-backup` file), then his past chats, then the web.
- Public repo: no passwords, APRS-IS passcode, webhooks, private keys, exact home coordinates, personal email or anything about a neighbor's equipment in new text.

**Which chat edits what**

| Chat | Files |
|---|---|
| 2 m APRS (you) | this file, `docs/aprs-2m-graywolf-reference.md`, `docs/aprs-bulletins-and-bridging-reference.md`, `docs/k2gia-5-aprsdroid-reference.md`, `docs/td-h9-*.md`, `docs/kisslink-*.md`, `docs/h9-toolbox.md`, `radio/ht/`, `watchdogs/graywolf-*`, `cnjmesh1/graywolf-discord/` |
| LoRa APRS | `lora-aprs-dashboard/`, LoRa APRS notes. Leave these alone |
| Mesh operations | everything else |

`todos.md`, `known-issues.md` and `session-log.md` are shared: change only 2 m APRS lines, and append to the session log (newest at the end; never re-read it whole).

## 2. Working with Charlie

- Plain, direct, partnership tone. Phone-sized replies. Use his name rarely. No multiple-choice prompts.
- Each shell command in its own code block, naming the host and whether it finishes on its own or needs Ctrl+C.
- Hand over commands freely, but nothing is changed on a Pi without his OK.
- Don't guess: check the repo and the web. Work things out before suggesting he contact someone.
- Push repo changes yourself as work finishes.
- APRS terms (KISS, TNC, BLE) have lost him before [S]. Explain them in everyday language.

## 3. Stations

| Call | What it is |
|---|---|
| K2GIA | him, portable and voice |
| **K2GIA-1** | home 2 m station on cnjmesh1: Graywolf (web UI port 8082), UV-5RM + Digirig, digipeater WIDE1-1 + iGate, 30 min beacon, 144.390, TX low, 30 s time-out |
| K2GIA-5 | APRSdroid on his phone, internet (APRS-IS) only |
| **K2GIA-7** | first TD-H9, mobile. **Dedicated APRS radio: do not reprogram or flash.** Apps: KISSLink, TD-H9 APRS Messenger (only one can hold Bluetooth at a time) |
| second TD-H9 | arriving **Tue Dec 1** [S]. No callsign-SSID chosen yet |
| K2GIA-9, K2GIA-10 | LoRa APRS, 433 MHz (LoRa chat). K2GIA-1 cannot hear them |

## 4. Pending: second TD-H9 (arrives Dec 1)

Full notes: `docs/h9-toolbox.md`.
1. Confirm it is the **Type-C** version. The H9 Toolbox firmware is only for that.
2. Note the shipped radio and APRS firmware versions, and save the original `.img` backup.
3. Pick an unused callsign-SSID before any APRS transmission.
4. Before flashing, re-read the developer's pages: his Nov 19 instructions describe v0.1.5, and the firmware page showed **v0.1.8** on Nov 26 [V].
5. Keep the recovery backup the updater saves. Restore choice: "Stock Type-C v1.0.38". Interrupted install: hold PTT + 2 while powering on.

## 5. Pending: satellite and packet firmware (second radio only)

- **H9 Toolbox firmware** (experimental; Charlie agreed to beta test the KISS TNC) [S]. Includes FM satellite passes (next five, path plot, Doppler tuning, live tracking), APRS station list and messaging, GPS tools [V, page read Nov 26].
- **KISS TNC** option: Bluetooth packet for Pat (Winlink email) or Paracon. Needs a laptop with Bluetooth and Chrome or Edge, a USB-C data cable, Python 3.11+, Pat and a Winlink account.
- Still to do: check for a Winlink account [?]; find a Winlink packet gateway in range [?]; review the Bluetooth bridge code before running it (unreviewed; laptop only, never a Pi). `--allow-tx` lets it transmit; check Pat's Outbox first.
- Unknown: whether it affects APRS use.
- **H9 OPS** (separate Android dashboard) needs its own patched firmware; a commenter says it replaces H9 Toolbox [S]. Unreviewed.

## 6. Pending: K2GIA-1

- **Antenna: NA-771 whip on the Baofeng, not the roof** [S, Nov 26; matches Nov 4]. A Nov 8 note puts the whip in the garage [S].
- **PTT / Digirig USB dropouts.** Spare UV-5RM swapped Nov 11; clean at the Nov 12 check. Left: kernel USB log check (command below), confirm aprs.fi shows it, add ferrite chokes on their own day, see more clean days.

  cnjmesh1, finishes on its own:
  ```
  sudo dmesg -T | grep -i -E "usb.*(disconnect|error -71)"
  ```
- Re-check Graywolf receive level: the -11.5 dB input gain was tuned for the old radio.
- Health watchdog auto-recovery upgrade: written, not deployed (`watchdogs/graywolf-health-watchdog/`).
- POLLERR audio bug unresolved. A Sep 24 flood coincided with lost receive; a Digirig replug restored it. Decide whether to keep the real-time scheduling override (no benefit seen).
- Graywolf upgrade 0.13.13 to 0.14.14: read notes, decide, back up the database first. Newer releases not checked since Nov 25.
- Compare the live Discord bridge with the repo copy (`md5sum`) [?]. The repo copy has a Nov 8 fix (outgoing messages post only once actually sent), recorded then as not deployed.

Never add an automatic Graywolf restart to a watchdog beyond the health watchdog's single one (`cnjmesh1-operations.md`).

## 7. Pending: K2GIA-7 and range testing

- **2 m mobile reception test** (added Nov 24): beacon from K2GIA-7 at increasing distances, compare Graywolf's heard list and aprs.fi (direct or digipeated); also check whether the TD-H9 hears K2GIA-1. K2GIA-1 is on the whip, so results describe that setup, not a roof antenna. Before it: check receive level, check K2GIA-7's beacon interval and path. Ask which direction first. Includes the older Nov 4 drive-test idea.
- K2GIA-7 not showing on aprs.fi (Nov 4); no resolution recorded [?]. Last sighting then: Oct 28 19:25, path `WIDE1-1,WIDE2-2`, heard by KB2EAR-13 [V, Nov 4 screenshot]. App notes use `WIDE1-1,WIDE2-1`, so check the radio's own path.
- Radio's timed beacon last recorded as 600 s, 10 min (`docs/td-h9-odmaster-aprs-messaging-bug.md`, Aug). Confirm on the radio.
- Firmware 1.0.38 update: undecided (stated change is Morse only). Lean: wait.
- Clean KISSLink message/ACK retest over RF, nothing cancelled (`docs/kisslink-screens-and-loopback-test-2026-10-28.md`).
- Low priority: check ODmaster for Android 2.6.5 (promised messaging fix).
- Last recorded settings: GPS site type, Timed Beacon on, PTT Linkage **off** (both on stops timed beacons), squelch 1. Check on the radio.

## 8. Learning APRS (his goal since Oct 20)

He wants to learn APRS in depth from Claude and become expert at it [S]. Format proposed then: one piece per session, a short explanation, a hands-on test with a clear pass or fail, results written into the docs.

Suggested order [I]:
1. The big picture: radio, TNC, app, internet (KISS and TNC in plain words). Test: name each link in his own setup.
2. Follow one beacon from the TD-H9 to aprs.fi and read the path.
3. Messages and ACKs between his own stations.
4. Digipeaters and paths (WIDE1-1, WIDE2-1).
5. iGates and APRS-IS filters.
6. Nets and services: APRSThursday (`CQ HOTG` to `ANSRVR`, worked from K2GIA-1 Nov 12 [V]), WLNK-1, QRX mailbox.
7. Packet and Winlink on the second TD-H9.

A beginner primer ("aprs-connection-primer.md") was written Oct 8 in the chat "Tidradio td-h9 chat continuation" and never committed; search past chats for it.

## 9. Play and ideas

- WLNK-1 (Winlink over APRS): reported down Nov 4 [S]; test it.
- Weekly check-in nets: `docs/aprs-bulletins-and-bridging-reference.md`.
- **APRS Connect** app: the developer posted Nov 25 that Android Auto was approved [S]. Free over APRS-IS, paid tier for radios. Give it its own SSID.
- APRStastic (Meshtastic to APRS gateway): needs a spare node.
- Ramble and PocketCHIRP: optional, no commitment.

## 10. Housekeeping decision

Exact home coordinates are already in older public files (including `docs/aprs-2m-graywolf-reference.md` and `docs/k2gia-5-aprsdroid-reference.md`). Open since Oct 13: whether to blank them. Editing the files does not remove them from git history.

## 11. Where things are

| Topic | File |
|---|---|
| K2GIA-1 hardware and settings | `docs/aprs-2m-graywolf-reference.md` |
| cnjmesh1 services, USB devices, fixes | `cnjmesh1-operations.md` |
| Known traps (APRS section) | `known-issues.md` |
| TD-H9 buttons and menus | `docs/td-h9-radio-manual-condensed.md` |
| TD-H9 phone apps | `docs/td-h9-app-field-reference.md`, `docs/kisslink-*.md` |
| ODmaster bug history | `docs/td-h9-odmaster-aprs-messaging-bug.md` |
| Satellite and packet firmware | `docs/h9-toolbox.md` |
| APRSdroid | `docs/k2gia-5-aprsdroid-reference.md` |
| Programming the radios, codeplugs | `radio/ht/` |
| Graywolf Discord bridge | `cnjmesh1/graywolf-discord/` (posts to `#aprs-rf-nj` and `#aprs-internet-nj`) |
| Watchdogs | `watchdogs/graywolf-*` |
| Full text of older to-dos | `docs/todos-full-2026-11-12.md` |
| History | `session-log.md` (search it) |
