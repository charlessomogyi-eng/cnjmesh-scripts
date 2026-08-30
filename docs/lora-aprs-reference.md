# LoRa APRS Reference — CNJ Mesh

**Last updated:** 2026-08-28

## K2GIA-10 — Existing Fixed Station (APRS-IS DISABLED Aug 28, 2026 — now pure RF digipeater + local MQTT)
- Hardware: LilyGo LoRa APRS board
- Web UI: `http://10.0.0.74` (admin login required)
- Firmware: CA2RXU LoRa_APRS_iGate
- LoRa: 433.775 MHz, SF12, BW125
- Do NOT use `screen` against this device's serial port for monitoring — the web UI's "Received Packets" page is the correct/supported monitoring method.
- Known limitation: **KISS TNC confirmed TX-injection only** — station has a documented self-gating limitation (cannot reliably hear/gate its own outgoing transmissions). A second RX-only board has been ordered to address this.

### DECISION (Aug 28, 2026): APRS-IS connection disabled entirely, by Charles's choice
Reasoning: K2GIA-1 (2m) already provides APRS-IS access for Charles's own traffic. Since APRS-IS makes every packet equivalent regardless of origin once gated, a second device also gating to IS added nothing for his own traffic — but he still wants K2GIA-10 digipeating for the benefit of the local LoRa mesh as it grows. Net effect: **pure RF digipeater now, zero path to the internet.**

Changed via WebUI:
- **"Enable APRS-IS connection"** → OFF (master switch, was ON)
- **"Send beacon via APRS-IS"** → OFF (was ON)
- **"Send beacon via RF"** → stays ON (unchanged)
- **Beacon Path** (under Station section, not Beaconing) → set to **`WIDE1-1,WIDE2-1,RFONLY,NOGATE`** — belt-and-suspenders; protects K2GIA-10's own beacon from being gated by ANY iGate that ever hears it (not just itself) as the local mesh grows and other operators' iGates might be nearby someday. Both `RFONLY` and `NOGATE` are legitimate, functionally similar APRS conventions per aprs.fi's own docs — using both is deliberate redundancy, not a mistake.
- **Digipeating → Repeater Mode**: confirmed already set to **"WIDE2 (+WIDE1) Digi"** — this settles a previously-unconfirmed question; K2GIA-10's digipeat function (separate from the now-disabled iGate function) was genuinely active the whole time.

**Same protection needed on K2GIA-9's own path if it's ever reconfigured** — its path (`WIDE1-1,WIDE2-1`) doesn't currently have RFONLY/NOGATE added, meaning any *other* iGate that hears K2GIA-9 directly could still gate it to IS even though K2GIA-10 won't. Not yet done (blocked on K2GIA-9's WiFi config AP being closed — needs re-flash or the still-unconfirmed-safe IO15/GND pad trick to get back in).

### MQTT enabled (local broker only — does NOT reopen the IS connection)
Separate from APRS-IS — this talks to cnjmesh1's own local Mosquitto broker, not the internet.
- Server: `10.0.0.181`, Port `1883`
- Username: `somog` (password: existing broker credential)
- Topic: `aprs-k2gia-10`
- "Send (also) iGate Beacon" left OFF, consistent with the RFONLY/NOGATE decision

Live-test the feed on cnjmesh1: `mosquitto_sub -h localhost -u somog -P <password> -t "aprs-k2gia-10/#" -v`

### CONFIRMED: real local LoRa APRS neighbors exist — overturns the "nearest station is 30+ miles" assumption
Watching the MQTT feed above (with APRS-IS off, so everything seen is confirmed genuine RF, not internet-sourced) turned up real local traffic:
- **W2MMD-10** — repeatedly beaconing "GCARC Clubhouse," relaying Winlink gateway bulletins (145.030, 220.000 VARA FM, 223.580 MHz) and a net announcement (147.180, Sun 8pm)
- **K2ZA-10** — its packets show `W2MMD-10*` as a digipeat hop, i.e. a real multi-hop local LoRa relay already happening nearby
- **AC2F-10** — another real LoRa APRS station, beaconing "LoRa APRS 433.775"

Worth revisiting the earlier "nearest known station is KD2ZHO-2, ~30 miles" assumption — there's clearly a closer, active local cluster. lora.ham-radio-op.net (shared by Innismir/N1WBV) and this MQTT feed are the two best ways to keep discovering who's actually nearby.

## K2GIA-9 — Mobile Tracker (flashed + configured Aug 26, 2026, digipeat CONFIRMED WORKING)
- Hardware: LilyGo T3 V1.6.1 (LoRa32 V2.1/1.6.1 family). **No onboard GPS module** — this board is bare, not the GPS-equipped variant.
- Firmware: `richonguzman/LoRa_APRS_Tracker`, flashed via Tracker WebFlasher as **"LoRa32 V2.1/1.6.1 TNC (433MHz)"** — the non-GPS build (NOT the "+ GPS (DIY)" build, which expects GPS hardware and will misbehave without it). Version 2026-04-22, V2.4.3.2, "First flash or Factory reset."
- USB: confirmed data-capable cable enumerates as `USB-Enhanced-SERIAL CH9102`. Many micro USB cables are charge-only — verify a COM port actually appears before trusting a cable for flashing.
- Power switch on this board only controls the LiPo battery path, not USB — switch position is irrelevant whenever USB is connected.

### Confirmed working config (as saved, Aug 26 2026)
- Callsign: `K2GIA-9` (all 3 beacon profile slots set to this, not left at default `NOCALL-9`, to prevent accidental beaconing under a placeholder callsign if the button/profile-switch is ever used)
- Path: `WIDE1-1,WIDE2-1` (no space after comma)
- LoRa: 433775000 Hz / SF12 / CR4:5 / BW125000 — matches K2GIA-10 exactly (confirmed correct via lora-aprs.org: this is the standard US/global LoRa APRS config)
- **Disable GPS: ON** — required since this board has no GPS hardware; position instead comes from the paired phone's GPS via Bluetooth (APRSdroid). This is a documented, first-class use case in the firmware, not a workaround.
- **Smart Beacon Active: OFF** — SmartBeaconing depends on GPS speed data that doesn't exist with GPS disabled; falls back to Fixed Beacon Rate (15 min) instead.
- **Enable Bluetooth: ON**, BT Classic (not BLE) — correct for Android/APRSdroid. Bluetooth Device Name set to `LoRaAPRSTracker`.
- Battery/Telemetry sections: left off/default (no BME sensor attached).
- Email (GPS position) field: intentionally left blank — meaningless with GPS disabled, nothing to send.

### CONFIRMED: K2GIA-9 → K2GIA-10 digipeat working end-to-end (Aug 26, 2026)
Serial console log evidence (via WebFlasher's Logs & Console over USB, K2GIA-9 side):
```
[22:14:36][INFO][Bluetooth] Client connected!
[22:14:41][INFO][LoRa Tx] ---> K2GIA-9>APDR16,WIDE1-1,WIDE2-1:=4025.45N/07433.45W$/A=000080 https://aprsdroid.org/
[22:14:52][INFO][LoRa Rx] ---> K2GIA-9>APDR16,K2GIA-10*,WIDE2-1:=4025.45N/07433.45W$/A=000080 https://aprsdroid.org/
```
The `K2GIA-10*` in the return path (asterisk = "used") is direct proof K2GIA-10 heard K2GIA-9's beacon over real 433.775 MHz RF and digipeated it — not just gated it to APRS-IS. This also appeared in the `aprs-internet-nj` Discord bridge as an "Internet Message" — that's just the *second* leg (K2GIA-10's iGate function re-uploading the heard packet to APRS-IS); the first leg (K2GIA-9 → K2GIA-10) was genuine RF the whole way. Confirms **K2GIA-10 runs stationMode 2 (iGate+Digipeater combined)** per the firmware's own changelog ("Added iGate Mode to also repeat packets (like a iGate+Digipeater) in stationMode 2 and 5") — not iGate-only as had been unconfirmed before tonight.

**Addressed message test also now CONFIRMED (overnight, Aug 26→27):** a real addressed message (not just a beacon) went K2GIA-9 → K2GIA-10 and back:
```
[22:20:45][INFO][LoRa Tx] ---> K2GIA-9>APDR16,WIDE1-1,WIDE2-1::K2GIA-10 :Test message from K2GIA-9 to K2GIA-10{2
[22:21:02][INFO][LoRa Rx] ---> K2GIA-10>APLRG1,RFONLY,WIDE1-1::K2GIA-9  :ack2
```
Note K2GIA-10's ACK came back with `RFONLY` in its own path — its reply stayed RF-only, didn't get gated to APRS-IS, which is expected/correct behavior for a direct ACK.

### CONFIRMED: real contacts reached K2GIA-9 overnight, unattended
Two additional real stations messaged K2GIA-9 overnight with no one watching, both auto-ACKed cleanly:
- **N2YDC-1** — sent a signal report (`UR 599 de N2YDC FN30ar`), a standard ham "you're readable" exchange
- **N2YDC-5** — sent `73` (standard sign-off/goodbell)

Both came in via `K2GIA-10>APLRG1,...:}<callsign>>...,TCPIP,K2GIA-10*::K2GIA-9  :...` — i.e., gated in from APRS-IS through K2GIA-10, same pattern as KC2BPP-1 the night before. Confirms K2GIA-9 is now a real, findable, working station attracting organic contact — not just a one-off test.

### CORRECTION: "CQ" as a literal message address is not universally ignored — some clients see it and explicitly reject it
Previously documented as simply having "no special meaning" and going nowhere. Overnight log shows this needs a caveat: two real stations, **WA1PLE-4** and **N1DWM**, DID receive Charles's message addressed to `CQ` and sent back explicit `rej` (reject) responses:
```
[23:29:46][INFO][LoRa Rx] ---> K2GIA-10>APLRG1,WIDE1-1:}WA1PLE-4>APK102,TCPIP,K2GIA-10*::K2GIA-9  :rej3
[23:30:00][INFO][LoRa Rx] ---> K2GIA-10>APLRG1,WIDE1-1:}N1DWM>APK102,TCPIP,K2GIA-10*::K2GIA-9  :rej3
```
So "CQ" isn't silently dropped everywhere — some client software actively parses it as an invalid/malformed addressee and replies with a reject, rather than ignoring it outright. Net effect (goes nowhere useful) is the same, but the mechanism is different than originally documented. Use `ANSRVR`/`CQSRVR` (see below) for genuine broadcast-style CQ, not a literal "CQ" address.

### CONFIRMED: Bluetooth Classic connection does NOT auto-reconnect after dropping — this is the real explanation for "had to walk close to the tracker" the next morning
```
[09:05:29][INFO][Bluetooth] Client disconnected!
```
No further Bluetooth activity in the log for the next 10+ hours (through 19:38 when the log was pulled) — meaning the connection stayed dead the entire time, with no automatic retry from either the tracker firmware or APRSdroid. This is the actual root cause of the "I had to walk close to the node for a message to go green" observation from the next morning — **not a range/antenna issue at all.** Once dropped, the link stays dropped until something (walking closer and re-opening the app, likely re-triggering a fresh connection attempt) manually re-establishes it. Worth remembering: if messages aren't going through, check whether Bluetooth actually shows as connected before assuming it's a range problem.

### K2GIA-9 plugged into cnjmesh1 (Aug 27, 2026) — temporary, for stable power/testing
Physically connected via USB to cnjmesh1's powered hub, same pattern as K2GIA-10. Landed on `/dev/ttyACM2`, stable path `/dev/serial/by-id/usb-1a86_USB_Single_Serial_58EF088583-if00`. Confirmed via `udevadm` to have its own distinct unique serial (`58EF088583`) — same CH340/QinHeng chip family as K2GIA-10 (`58EF089845`) but NOT the same ambiguous-serial situation as KPC1/KPR1; no risk of confusing the two. No existing service on cnjmesh1 reads this serial connection (same as K2GIA-10) — this is purely for stable power while parked, not tied into any logging pipeline yet. K2GIA-9 was originally intended as a *mobile* tracker — this is a temporary/testing placement, not its permanent home.

### APRSdroid Bluetooth config (K2GIA-9 pairing)
APRSdroid has no multi-profile support — this REUSES/OVERWRITES the same config previously used for K2GIA-5 (Internet/APRS-IS mode). Switching back to Internet mode is required to restore K2GIA-5 functionality.
- Connection Protocol: TNC (KISS)
- Connection Type: Bluetooth SPP
- Client Mode: checked (APRSdroid establishes the connection — keep this on)
- TNC Bluetooth Device: `LoRaAPRSTracker`
- Callsign: `K2GIA`, SSID: `9` (must change SSID from whatever K2GIA-5 was using, or packets transmit under the wrong identity)

### KNOWN ISSUE: Bluetooth Classic pairing via Android Settings does not work reliably on modern Android
Attempted OS-level pairing (Settings → Bluetooth → scan → select `LoRaAPRSTracker`) repeatedly failed silently on a Pixel 7 — device visible/selectable, but tapping it produced no pairing prompt, no notification, nothing in the board's serial log. Confirmed NOT a board-health issue (clean boot logs every time, Bluetooth Classic init confirmed in firmware logs).

This matches a **known, unresolved upstream issue**: `richonguzman/LoRa_APRS_Tracker` GitHub Issue #275 ("switched the BT on, but I am not able to see it on my phone, so I cannot pair. No luck whatever I do") — open, no fix, different board (T-Beam) but same firmware family and symptom. Also matches a documented pattern elsewhere of ESP32 Bluetooth Classic SPP devices failing to pair specifically on newer Android versions (works fine on old Android 6.0 hardware, fails on Android 12+) — likely an Android-side Bluetooth Classic stack compatibility gap with lightweight ESP32 BT implementations, not something fixable from the tracker's config.

**Workaround that DID work:** skip OS-level pairing entirely. Go directly into APRSdroid → Connection Preferences → TNC Bluetooth Device — the device picker there showed `LoRaAPRSTracker` as selectable even though it was never OS-paired. Selecting it there and toggling Start Tracking eventually produced a real connection (`[INFO][Bluetooth] Client connected!`), though this took several minutes with zero indication on the phone side that anything had happened — no toast, no status change visible in APRSdroid's UI. **If this connection method is used again, expect a long, silent delay before it actually connects — do not assume failure just because nothing visibly happens for several minutes.**

### CAUTION: IO15-to-GND pad-touch (button workaround) triggered unexpected "going into deep sleep" instead of reopening config AP
This directly contradicts the expected behavior (documented in this file above) of triple-touching IO15-to-GND reopening `LoRaTracker-AP`. Actual result: board printed a deep-sleep message and stopped responding normally; recovered fine after a full USB unplug/replug power cycle, no lasting harm. Root cause NOT confirmed — possible that IO15 has a different function on this specific board/firmware build than assumed, or pin-count-miscounting during the physical touch. **Do not trust the IO15 pad-touch method as confirmed-safe until this is re-verified.** The documented fallback (full re-flash, which also re-triggers the AP on next boot) remains the safer option if config access is needed again.

## K2GIA SSID Map (full, cross-reference)
- `K2GIA` — Charles personally (portable/voice/OTA)
- `K2GIA-1` — Graywolf/UV-5R M fixed 2m digi+iGate (see separate 2m APRS reference doc)
- `K2GIA-5` — APRSdroid (phone-based)
- `K2GIA-7` — planned TidRadio TD-H9 handheld (mobile 2m APRS)
- `K2GIA-9` — LoRa APRS mobile tracker (this doc) — flashed, configured, confirmed working Aug 26, 2026
- `K2GIA-10` — existing LoRa APRS fixed station (this doc)

## Community outreach (Aug 26, 2026)
Sent a CQ-style "Looking for a copy, k2gia-9" message via K2GIA-9 into the NJ LoRa APRS Discord (#general). Innismir/N1WBV responded and pointed to `lora.ham-radio-op.net/?center=40.4957,-73.8259&zoom=8` for other NJ LoRa stations. Charles shared current config (433.775MHz/SF12/CR4:5/BW125kHz) and confirmed location (South Brunswick NJ) — this matches the US/global standard config, not a regional variant. Live conversation in progress as of this writing; a real cross-station RF contact may follow.

## Open item: lora-aprs.live syslog feed not yet configured (now lower priority)
K2GIA-10's syslog currently points only to `10.0.0.181` (cnjmesh1, local). The public `lora-aprs.live` aggregator (a separate, syslog-fed — NOT APRS-IS-fed — tracker/iGate map and analysis tool) requires its own syslog destination to be added. **Important consequence of the Aug 28 APRS-IS disable above: K2GIA-9 will no longer show up on aprs.fi at all either now**, since that required K2GIA-10 actively gating to APRS-IS — which is now off by decision. The community-contact pattern from Aug 26/27 (KC2BPP-1, N2YDC-1, N2YDC-5 — all reached via `TCPIP` gating) is not currently reproducible under the new pure-RF-only setup, unless K2GIA-10's APRS-IS is deliberately re-enabled for a specific occasion. lora-aprs.live would still be worth adding as a syslog fan-out destination if wider RF-only visibility (SNR, real digipeat path data, no internet requirement) is wanted — arguably now MORE relevant given the pure-RF philosophy, not less.

### Physical button — REQUIRED, install before or immediately after first flash
**Why it's needed (not just for on-screen menu/display — Charles doesn't use the screen on any of his 10 LoRa nodes, controls via app/Bluetooth instead):** the tracker's WiFi config AP (`LoRaTracker-AP`) only auto-creates itself on the very first boot after flashing. Once settings are saved and it reboots, there is no automatic way back into that setup screen. Normally a triple-press of the physical user button reopens the CONFIG menu → "Config WiFi AP." **This T3 V1.6.1 board does not have that button populated** (only a reset button) — without wiring one, the only way to change any setting later (callsign, SmartBeaconing values, frequency, etc.) is a full re-flash from scratch.

**Workaround until the button is soldered on:** you don't need the actual button to trigger it — just briefly connect IO15 to GND, three times in a row (jumper wire, tweezers, or a paperclip touched across the two pads three quick times = same as three button presses). Re-flashing the firmware also works as a fallback (re-triggers the AP automatically on first boot) but is slower and not needed if the pad-touch trick works.

**Button install instructions (2-lead momentary button, IO15 to GND, no polarity):**
1. Locate the IO15 pad and any GND pad on the underside of the T3 V1.6.1 (GND is broken out in multiple places — any one works).
2. Cut two ~2–3" lengths of thin stranded wire (30 AWG is easy to work with). Strip and tin both ends of each.
3. Pre-tin both legs of the 2-lead momentary button.
4. Solder one wire to each leg of the button.
5. Solder the free end of one wire to the IO15 pad, the free end of the other to a GND pad. Doesn't matter which wire goes where.
6. Add a small dab of hot glue where each wire meets the board (strain relief) so flexing doesn't crack the pad or lift the trace.
7. Test before mounting: power up, triple-press, confirm the display shows CONFIG mode and "Config WiFi AP" is reachable. Fix any bad joints now while still accessible.
8. Wrap the switch body and legs in tape or heat-shrink so nothing can bridge to an exposed pad or a metal case.
9. Once tested, mount the button to the underside of the board with hot glue or double-sided foam tape, positioned to clear the case (check actuator height vs. standoff clearance).

## Related / Not Yet Built
**APRStastic** (afourney/aprstastic on GitHub) — bidirectional Meshtastic↔APRS gateway, TODO/experiment item, not yet built. Would run on a dedicated spare Pi + dedicated Meshtastic node (NOT CJG1/CJG2). Two open decisions before building:
1. OK with CNJ mesh node positions appearing on the public aprs.fi map?
2. Which spare node + which Pi (keep off cnjmesh1's crowded USB bus)?

Full detail in `todos.md` / Claude's memory — this is Meshtastic-adjacent, not part of the LoRa APRS (K2GIA-9/-10) build itself; kept as a separate consideration.

**APRS-Agent** (map.aprsagent.com) — self-hostable APRS-IS bridge/automation platform with AI Gateway, repeater/silence monitoring, propagation detection. Reference only, not yet involved with — plan is to revisit once both 2m APRS (Graywolf) and LoRa APRS builds are fully stable. Would run on a separate VPS/spare Pi, not cnjmesh1. Charles has ruled out German hosting providers (Contabo, Hetzner) specifically due to ID-verification friction — would need a non-German alternative (DigitalOcean, Linode, Vultr) if pursued.
