# H9 Toolbox for the TIDRADIO TD-H9 (hobby, look-into item)

Charlie asked on Nov 15 2026 to have this written down so it is not forgotten. This file is the living copy; the original Nov 11 todo text is frozen in `docs/todos-full-2026-11-12.md` (item 5, line 25) and is summarised here. Nothing has been installed or changed on any radio.

## What it is
- A free, open-source toolset for the TD-H9 made by someone else: site `h9toolbox.com`, code on GitHub as `melidosian/h9toolbox`. The same person posts in the "TIDRADIO H9 - USERS" Facebook group under a name matching that username (Nov 19 screenshot), and the Nov 15 commenter addressed him as the developer, so he appears to be the developer; the match is by name only.
- Site menu (Nov 15 screenshot): Home, Programmer, Firmware, App Manager, GitHub.
- **Programmer:** a Web Bluetooth page for desktop Chrome or Edge (not a phone browser). Flow shown on the site: 1 Connect Bluetooth, 2 Read and save the original (`.img` backup), 3 Edit and write. Edits channels and mapped settings; CSV/JSON import and export. No account needed.
- **Firmware ("H9 Toolbox Firmware"):** described on the site as stock v1.0.38 plus apps, flashed from the browser over USB-C, with a main-flash backup and a "one-click restore to stock" advertised.
- **App Manager:** adds apps to the radio over Bluetooth.
- The site says it was "entirely and responsibly AI generated under human direction" and uses Google Analytics (it says radio data is not sent). The programmer's JSON export contains callsigns and relay passwords, so do not post an export anywhere public.

## The satellite pass app (why it caught Charlie's eye)
- Seen only in Facebook posts in the "TIDRADIO H9 - USERS" group, not on the site's own pages.
- Runs on the radio itself with its GPS: lists upcoming FM satellite passes, sky plot, Doppler-corrected up/down frequencies, can set the VFO frequency and access tone and restore them afterwards.
- Nov 15 photo of a radio running it (posted by another user): screen "SAT PASS", "GPS OK", orbital data (TLE) dated 2026-11-14, a list with columns SAT / AOS / MAX / DUR / IN showing AO-123 (now), AO-91, PO-101, ISS and ISS-TV, and soft keys LIST, PLOT, TRACK. My reading of the columns: AOS = rise time, MAX = peak elevation in degrees, DUR = minutes, IN = time until the pass. This is evidence the app works on a real radio.
- The same post says the user downloaded "the H9 box" and asks for two features: an **APRS mute**, and a **BLE bridge to a phone to pass packets**. Both are requests to the developer, not existing features.

## Nov 19 2026: experimental packet / WinLink build (teaser)
- Post by the developer in the same group, about 16 hours old when Charlie screenshotted it (Nov 19 4:20 PM). Headline: **"Full AX.25 Packet KISS TNC sends WinLink email via PAT over Bluetooth."**
- Claims: this was not possible on stock firmware; it also supports "all the other packet stuff like BBS servers"; still an experimental build, expected to be available in a couple more days; he is asking for beta testers.
- The attached video (not watched by me, only the still frame) shows a laptop running the Pat Winlink client with a message in its outbox and a TD-H9 on a VHF frequency (145.610 MHz on the radio's screen).
- Why it matters here: the stock TD-H9 does APRS over Bluetooth but not general packet. If this works it would add Winlink email and packet BBS use from a handheld, which fits Charlie's emergency-communications interest (RACES/AUXCOMM plans). That is my reading; the post does not say it.
- Open questions: how stable it is, whether it can coexist with APRS use, whether the Bluetooth KISS link works from Windows/Linux/Android, what a Winlink account and license-class limits mean for use, and how to restore stock firmware.

## Nov 19 evening: Charlie is in as a beta tester
- Charlie replied to the developer, agreed to beta test the KISS TNC firmware, and **ordered a second TD-H9 to test with** (Nov 19). The developer sent a private message with `https://dev.h9toolbox.com/firmware/` and a PDF, `H9-KISS-TNC-Beta-Instructions.pdf` (76 KB, not seen by me yet). He says it only needs a laptop or desktop, a USB-C cable and Chrome or Edge, and offered a walkthrough if Charlie hits snags.
- What the firmware page says (read Nov 19, not the PDF):
  - It is for the **Type-C TD-H9** only. **Confirm the new radio is the Type-C version when it arrives.**
  - "H9 Toolbox Firmware" is the main experimental build (APRS station list and messaging, FM satellite pass tracking, GPS tools, app menu; saved channels are kept). The **KISS TNC** is an optional APRS modem update, v0.1.5: after the updater stages it, an "Optional: Unlock KISS TNC" choice appears, and compatible packet software such as Pat or Paracon connects over Bluetooth. The page does not call it beta; the developer did.
  - Install is guided in the browser: connect, **save a recovery backup**, install. Keep that backup.
  - **Revert:** pick "Stock Type-C v1.0.38" in the same updater.
  - **If an install is interrupted:** hold **PTT + 2** while powering on to reconnect in update mode, then follow the TD-H9 recovery guide.
  - USB-C connection to App Manager is labeled experimental. APRS transmitting needs an amateur licence.
  - A separate joke/experimental "Doom" firmware exists; avoid it on a radio you need.

## The developer's beta instructions (PDF, 2 pages, read Nov 19 8:33 PM)
Summary only; the PDF itself is not in the repo. Needs a charged **Type-C** TD-H9, a USB-C **data** cable, a laptop or desktop with Chrome or Edge, Python 3.11+, Bluetooth on the computer, and Pat with a Winlink login.
1. **Install H9 Toolbox Firmware v0.1.5** at `dev.h9toolbox.com/firmware-update/` (the dev updater). Radio off, plug in, hold side PTT + keypad 2 while powering on (screen stays blank, top light green). Connect, choose "USB Composite Device", Load v0.1.5, Install. **Leave the backup option on and keep the `.h9hid` file it downloads.** First install can take **up to 45 minutes**; keep the radio on and plugged in until the updater says finished.
2. **Unlock the TNC on the radio.** After the reboot: off, then hold PTT + 7 while powering on until "APRS Update" shows. Menu once, "APRS STAGE READY", Menu again, wait for "APRS BOOT VERIFIED", power cycle normally. In APRS Info the version should read V1.0.15X. If it keeps saying "Querying..." or APRS was never staged, message the developer before retrying.
3. **Bridge:** download `h9-kiss-bridge.zip` from the dev site, unzip, make a Python virtual environment, `pip install -r requirements.txt`, then run `bridge.py --scan` to get the radio's Bluetooth ID. Radio Bluetooth on, on the normal channel screen, App Manager and other apps closed.
4. **Start the bridge and Pat together** with `run_pat.py --device <ID> --pat-config <path from "pat env"> --gateway <GATEWAY-SSID> --open-browser --allow-tx`. Tune the radio to the Winlink packet gateway's published frequency first. `--allow-tx` lets the radio transmit: only use it where licensed.
5. **Test connect** in Pat (entry starting with "H9" plus the gateway callsign, Pat at `http://127.0.0.1:8080/`). **Check Pat's Outbox first: anything queued may send on connect.**

My notes on it:
- The bridge is a Python program from the developer's site that Charlie would run on a computer. Run it only on the **laptop**, never on cnjmesh1/2/3 or any Pi in the mesh setup. I could not download or read the bridge code from here (the download host is blocked in my session), so it is unreviewed. The site says the source is on GitHub; read it before running, or ask me to once GitHub access to it is enabled.
- Still needed before step 4: a Winlink account, Pat installed and configured, and a **Winlink packet gateway in range of Kendall Park** with its frequency and callsign (not yet researched; Pat can transmit mail, so use a short test message).
- Step 2 and step 1 both depend on the Type-C radio; stop and ask the developer if the new radio's updater step says anything else.

## Test project idea (fun, not urgent)
Charlie suggested on Nov 19 making this a hobby test project. Sketch, to refine when the build is out:
1. Use the **second TD-H9 Charlie ordered** (never K2GIA-7). Back up its `.img` and keep the updater's recovery backup first.
2. Flash the experimental build from the browser tool once released; confirm restore-to-stock works before relying on it.
3. Pair the radio to a laptop over Bluetooth KISS and run Pat in a local-only test: no on-air Winlink until a gateway on a nearby VHF packet frequency is confirmed (check which Winlink gateways are in range first).
4. Try a short test message; log what worked in this file.
5. Optional later: try a BBS or APRS messaging on the same build and report findings to the developer.

## Not verified
- Whether the firmware or apps change the stock Bluetooth KISS behavior that K2GIA-7 depends on (KISSLink / TD-H9 APRS Messenger). Nothing says they do; nothing says they don't.
- Whether the restore-to-stock works if a flash fails; license; compatibility beyond firmware 1.0.38. K2GIA-7's own firmware is a separate question: the Oct 21 decision item about updating it to 1.0.38 is still open in `todos.md` (an Aug 2026 screenshot showed its APRS firmware as v1.0.15).
- Neither the site pages nor the repo were re-read on Nov 15; this update comes from Charlie's two screenshots.

## Rules for trying it
- **Do not install on K2GIA-7** (dedicated APRS radio, listed as do-not-reprogram in `radio/ht/README.md`). A second TD-H9 is the safe place to try it.
- Before any write: read and save the original `.img` and keep it somewhere safe.
- Only one app can hold the TD-H9's Bluetooth link at a time (see `known-issues.md`).

## Possible next steps (hobby, whenever Charlie wants)
1. Read the GitHub repo and the Firmware page for the restore procedure and the license (read-only).
2. Decide whether to get or borrow a second TD-H9 to try the App Manager and the satellite app.
3. If it works, consider asking the developer about the APRS mute and BLE-bridge requests, since APRS is Charlie's main use of the radio.

## Related lead: H9 OPS (Android APRS dashboard) — noted Nov 25 2026
Source: two Facebook posts in the TIDRADIO H9 - USERS group (Nov 23 and Nov 25 screenshots from Charlie); nothing here was verified on the GitHub page.
- **What the posts show [S, screenshots]:** an Android app called H9 OPS that connects to a TD-H9 over Bluetooth (PIN locked) and shows a live dashboard: both VFOs, battery, a Stations list tagged DIRECT or VIA a digipeater, Messages, Log and Map tabs, plus Weather, Tracks, Objects and Alerts. The screenshots use NOCALL placeholder callsigns, so they look like demo data.
- **Requirement [S, the poster's text, Nov 25]:** it "does require a firmware patch", named `TD-H9-V1.0.38.P2.fw`. The poster gave a GitHub address (`Deadly447/H9-OPS`). I could not open it from the assistant's session.
- **From a commenter's review [S, one person's opinion, Nov 25]:** H9 OPS replaces H9 Toolbox rather than adding to it (he would have to uninstall Toolbox and "revert back to a modified stock firmware"); he calls it an APRS messaging app, a map that needs multi-stage setup and is not linked to Google/Open Maps, and weather limited to heard stations, and says Toolbox already gives him advanced APRS messaging and satellite tools. So the two look like separate projects that cannot share one radio.
- **Unknown:** who wrote it, what the patched firmware changes, how to flash it and go back, and the license.
- **Rule:** the patched firmware would replace the stock APRS firmware, so it is not for K2GIA-7 (do-not-reprogram). Same rule as above: use the second TD-H9. The Oct 21 decision on updating K2GIA-7 to 1.0.38 is a separate open item in `todos.md`.

## Nov 26 2026: firmware page re-read
- `dev.h9toolbox.com/firmware/` now shows H9 Toolbox Firmware **v0.1.8** (the Nov 19 instructions describe v0.1.5), still called experimental, Type-C only. Apps include FM Satellite Passes (next five passes, path plot, Doppler tuning, live tracking). In v0.1.8 an app opens with Menu on the channel screen. No release date or changelog on the page. Second TD-H9 due Dec 1 [S].
