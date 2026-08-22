# TD-H9 / ODmaster APRS Messaging Bug — Reference (Aug 20-22, 2026)

## Bottom line
K2GIA-7 (TD-H9) beaconing is fully working. APRS **messaging via the ODmaster app is confirmed broken** — reported to TidRadio, in progress. The radio's own native SMS-via-APRS keypad menu **works perfectly**, proving the bug is app-side, not radio-side. Currently evaluating Kelvin Hill's third-party "BLE-Bridge" tool as a possible free workaround to use APRSdroid instead of ODmaster.

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

## Next steps
1. Investigate Kelvin Hill's BLE-Bridge tool(s) — Windows-only or Android-compatible? How would it integrate with the Pixel 7 Pro + TD-H9 setup?
2. Check for reply from TidRadio support (Gideon) re: 2.6.4 Android beta
3. Decide: free BLE-Bridge path vs. Mobilinkd/Digirig hardware purchase vs. just waiting on ODmaster fix
4. If pursuing BLE-Bridge: locate the PDF manual and download link referenced in the "Bluetooth (Low Energy) KISS TNC Console & APRS Messenger" FB group

## Key identifiers
- Callsign: K2GIA (General class)
- TD-H9 radio: K2GIA-7
- Home station (Graywolf, Pi): K2GIA-1
- APRS passcode: 16025
- Phone: Google Pixel 7 Pro, Android 16
- ODmaster version: 2.6.3 (Android, current per Play Store as of Aug 21 2026)
