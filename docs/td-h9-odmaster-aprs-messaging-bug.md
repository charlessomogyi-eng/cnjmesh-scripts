# TD-H9 / ODmaster APRS Messaging Bug — Reference (Aug 20-23, 2026)

## Bottom line — RESOLVED Aug 23, 2026
K2GIA-7 (TD-H9) beaconing and now **messaging are both fully working.** APRS messaging via the ODmaster app remains confirmed broken (reported to TidRadio, still open with them) — but the fix in practice is **Kelvin Hill's KISSLink BLE APRS Console** app, which connects directly to the TD-H9's onboard BLE KISS TNC and builds correct addressed APRS messages, bypassing ODmaster entirely. Full RF round-trip (TX → digipeat → ACK) confirmed working via diagnostic log, see "Resolution" section below.

---

## Radio config (confirmed working, stable — do not need to revisit)
- Radio firmware: V1.0.32
- APRS firmware: V1.0.15
- PTT Linkage: OFF, Timed Beacon: ON, Timing: 600s (10 min) — undocumented firmware bug: both ON simultaneously silently kills timed beaconing entirely
- Site Type: GPS Coordinates (not Fix Coordinates)
- Power Save: OFF
- Squelch Level: 1
- APRS passcode for callsign K2GIA: **16025** (deterministic/permanent, verified via two independent calculators)
- K2GIA-7 confirmed live on aprs.fi, beaconing correctly via KB2EAR-13 digipeater

## The core bug: ODmaster "Send Message" screen
**Symptom:** Messages sent via ODmaster (both Network Transmit and Bluetooth Transmit tabs) show "Requested successfully!" in-app, but the destination station never acks, and the message never appears on aprs.fi's "messages" tab.

**Root cause confirmed via raw packet inspection on aprs.fi:** ODmaster encodes the message as a **position report with the text appended as a comment**, not as a proper colon-delimited addressed APRS message.

Broken packet ODmaster actually produces:
```
K2GIA-7>K2GIA-1,TCPIP*,qAS,K2GIA:!4025.46N/07433.44W!testing mobile to home station
```
(data type identifier `!` = position report, not `:` = message)

Correct/expected format:
```
K2GIA-7>APTDH9,WIDE1-1,WIDE2-1::K2GIA-1  :testing mobile to home station{01
```

**Smoking gun:** ODmaster's own Settings screen has a field labeled **"Postscript"** that showed the test message text after sending. Strong evidence the app is internally writing the "MESSAGE/SEND" field into a beacon comment/postscript field, rather than constructing a real APRS message packet.

**Confirmed to happen identically regardless of:**
- Network Transmit vs. Bluetooth Transmit
- Full phone + radio reboot and fresh BLE re-pairing
- Radio's SMS>APRS mode enabled or not
- Correct APRS passcode entered and verified (16025)

## Proof the radio itself is NOT the problem
Sent a test message using the **TD-H9's own native keypad SMS menu** (not ODmaster) — selected APRS as transport, addressed K2GIA-1 directly. Produced a perfectly formed, standards-compliant packet:

Outbound:
```
K2GIA-7>APTDH9,qAR,KB2EAR-13::k2gia-1  :test{1
```
Ack received back from K2GIA-1 (Graywolf):
```
K2GIA-1>APGRWO,TCPIP*,qAC,T2UKRAINE::K2GIA-7  :ack1
```
Also visible correctly in Graywolf's own message dashboard (proper DM thread, unread badge) and in the `#aprs-internet-nj` Discord bridge channel (parsed cleanly as an "Internet Message" with From/To/Message/Via fields, same as legitimate messages from other stations).

**Conclusion: radio firmware/TNC is fully capable of correct message encoding. The bug is isolated to ODmaster's app code specifically.**

## TidRadio support interaction (ongoing)
- Contacted odmaster@tid-china.com with full bug report, packet evidence, order info (Amazon order 111-1614976-3750661, Charles R Somogyi)
- Support rep "Gideon" responded, asked for Android version + more logs; mentioned Android version 2.6.4 is in beta prep
- Sent follow-up: Android version 16, device Pixel 7 Pro, ODmaster 2.6.3 confirmed current on Play Store (lagging behind iOS's 2.6.8)
- Sent further follow-up with the native-SMS-menu proof (radio works, app doesn't) and the "Postscript" field finding — should let their dev team pinpoint the exact bug in code
- **Status as of Aug 22: awaiting further reply / the 2.6.4 Android beta**

## Other findings / context
- **APRSdroid (stock, Play Store version) CANNOT connect to the TD-H9 directly.** TD-H9 only exposes Bluetooth Low Energy (BLE); stock APRSdroid's Bluetooth TNC mode expects classic Bluetooth SPP. Confirmed by other TD-H9 owners hitting the same wall in forums ("the radio only sees the TV, not the phone").
- K2GIA-1 (Graywolf) is unaffected by any of this — it's the custom Python station on cnjmesh1 using Digirig Mobile + Baofeng UV-5R M + serial RTS PTT, unrelated to the TD-H9/ODmaster problem.
- Charles separately owns/uses a Digirig (personal, not the cnjmesh1 unit) successfully with a Baofeng.
- **Digirig Lite (~$55)** vs **Mobilinkd TNC3 (~$110-130)** both confirmed to work with APRSdroid:
  - Digirig Lite: wired USB-C, no onboard AFSK (does it in software per-app), APRSdroid officially listed as supported software (https://digirig.net/digirig-lite-setup-manual/), PTT priority GPIO3/HID > tone > VOX
  - Mobilinkd TNC3: wireless Bluetooth classic SPP, onboard AFSK, simpler APRSdroid pairing, pricier
- **Kelvin Hill (VA3KJH)** — ham radio developer, admin of FB group "Bluetooth (Low Energy) KISS TNC Console & APRS Messenger" (174 members). Built free BLE-to-KISS bridge tools specifically for BLE-only radios like the TD-H9:
  - **BLE-Bridge-W11** (Windows) — bridges a BLE KISS TNC connection to TCP so other software (Direwolf, Graywolf-style apps, APRSdroid via network KISS) can use it
  - Confirmed directly by Kelvin in FB comments: his BLE-Bridge **does allow APRSdroid to work with the TD-H9** ("it does... Use my BLE-Bridge")
  - Also updated a version specifically to handle RT-950 peculiarities (BLE KISS frames arriving in segments/out of order) — worth checking if TD-H9 has similar quirks
  - Kelvin is the same person referenced in the CHIRP GitHub issue (#12216) working on unofficial TD-H9 channel/settings programming support — separate effort, APRS data area (0x3000) writes still broken as of that thread, channel writes work
  - **OPEN THREAD — not yet resolved:** need to find out if there's an Android-compatible version of the BLE-Bridge (not just Windows), get the manual (BLE-Bridge-W11_User_Manual.pdf was referenced in the FB group), and evaluate whether this is a viable free path to real APRS messaging via APRSdroid, bypassing ODmaster's bug entirely.

## Resolution (Aug 23, 2026) — KISSLink BLE APRS Console

**BLE-Bridge-W11 ruled out.** Confirmed via Kelvin's own PDF manual: Windows-11-only desktop utility, bridges a BLE KISS radio to a local loopback TCP port (127.0.0.1:8001) for Windows APRS clients like PinPoint. No Android build, not usable for a phone-only field setup. (Useful nugget from the manual: confirmed TD-H9's BLE KISS GATT profile is service `AF00`, characteristic `AF01` (write, TX) and `AF02` (notify, RX) — matches what KISSLink auto-detected in practice below.)

**Kelvin's actual app portfolio** (all distributed via Google Play **closed/early-access testing** links posted in his FB group "Bluetooth (Low Energy) KISS TNC Console & APRS Messenger" — not publicly searchable on Play Store, no GitHub presence found):
- Tidradio-specific: `TD-H9 BLE KISS Tester`, `TD-H9 APRS Messenger`
- Radtel-specific: `RT-950 BLE KISS Tester`, `RT-950 APRS Messenger`
- General/radio-agnostic (Kelvin's stated future development priority — "easier to manage three than seven"): `BLE KISS TCP Bridge`, `KISSLink BLE APRS Console`, `BLE APRS Messenger`

Access: emailed Kelvin the Google Play Store account email, he added it to the tester list. Direct package-ID links (from Kelvin's May 20/June 3 FB post) work when opened in Chrome (tapping links directly in some apps didn't trigger the Play Store redirect — Chrome address bar worked reliably):
- `https://play.google.com/store/apps/details?id=com.bughunter.kisslink` (KISSLink, installed and tested)
- `https://play.google.com/store/apps/details?id=com.tdh9.aprsmessenger` (TD-H9 APRS Messenger, not yet tried)

**KISSLink BLE APRS Console — installed and verified working, Aug 23, 2026.** Full user manual obtained (`KISSLink_BLE_APRS_Console_User_Manual-v0.5.0.pdf`, package `com.bughunter.kisslink`, min Android 8.0/API 26). Setup: Settings tab → source callsign `K2GIA`, SSID `7`, digipeater path `WIDE1-1,WIDE2-1` (destination tocall left at app default `APKJH2`, harmless). Control tab → scanned, found `TD-H9-7867(BLE)`, connected — auto-detected as "Known split BLE KISS profile (AF01 TX / AF02 RX)," matching the BLE-Bridge-W11 manual's documented TD-H9 profile.

**Confirmed full RF message round-trip via diagnostic log share (Basic mode):**
```
11:53:42 — TX: sendAprsInfo: K2GIA-7>APKJH2,WIDE1-1,WIDE2-1  info=':K2GIA-1  :Test from KISSLink{001'
11:53:42 — BLE write to af01: OK ✓ (66-byte KISS frame)
11:53:45 — RX ACK from K2GIA-1 (via KB2EAR-13 digipeater), 3-second round trip
```
APRS-IS was disconnected in-app the entire time, confirming the message went out over RF through the TD-H9 exclusively — not via internet. (A message also appeared in the `aprs-internet-nj` Discord bridge labeled "Via: APRS-IS" — this is expected and not a contradiction: that channel is fed by IGates that heard the RF transmission and relayed it to APRS-IS, labeling it from *that* leg of the journey, not the original TX path.)

**Net result:** proper `:ADDRESSEE:text{msgid` formatted APRS messages, correct ACK handling, all built and sent from a phone app with no ODmaster involvement. This closes the practical need — ODmaster's Send Message bug no longer blocks APRS messaging on K2GIA-7.

**Still open / optional follow-ups:**
1. TidRadio (Gideon) ODmaster bug report — no obligation to keep chasing this now that a working alternative exists, but the underlying report was solid and reproducible; a brief closing note to their support thread would be courteous (confirmed working alternative found, bug still valid for other users, keep it as a bug not a feature-request per its earlier discussion — the existing UI element genuinely malfunctions, doesn't just lack a feature).
2. `TD-H9 APRS Messenger` (Kelvin's TD-H9-specific, presumably leaner messaging-only app) — not yet installed/tried; KISSLink already meets the need, so this is optional exploration only, not a blocker.
3. ODmaster app itself is still useful for TD-H9 channel/radio programming (separate from APRS messaging) — no reason to uninstall it.

## Key identifiers
- Callsign: K2GIA (General class)
- TD-H9 radio: K2GIA-7
- Home station (Graywolf, Pi): K2GIA-1
- APRS passcode: 16025
- Phone: Google Pixel 7 Pro, Android 16
- ODmaster version: 2.6.3 (Android, current per Play Store as of Aug 21 2026)
