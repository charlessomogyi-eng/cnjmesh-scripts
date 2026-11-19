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

## Test project idea (fun, not urgent)
Charlie suggested on Nov 19 making this a hobby test project. Sketch, to refine when the build is out:
1. Get a **second TD-H9** (never K2GIA-7). Back up its `.img` first.
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
