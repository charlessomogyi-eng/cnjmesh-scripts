# LoRa APRS Reference — CNJ Mesh

**Last updated:** 2026-08-26

## K2GIA-10 — Existing Fixed Station
- Hardware: LilyGo LoRa APRS board
- Web UI: `http://10.0.0.74`
- Firmware: CA2RXU
- iGate: 433.775 MHz, SF12, BW125
- Confirmed receiving traffic (e.g. AC2F-10 beacons)
- Known limitation: **KISS TNC confirmed TX-injection only** — station has a documented self-gating limitation (cannot reliably hear/gate its own outgoing transmissions). A second RX-only board has been ordered to address this.
- Do NOT use `screen` against this device's serial port for monitoring — the web UI's "Received Packets" page is the correct/supported monitoring method.
- Confirmed solid RF reach: e.g. WB2EHG-7 packet relayed through KD2CIF-1 and KB2EAR-13 observed cleanly.

## K2GIA-9 — Mobile Tracker (board delivered Aug 26, 2026)
- Hardware: LilyGo T3 V1.6.1. Delivered Aug 26, 2026 — not yet flashed/configured as of this writing.
- SSID `-9` reserved per K2GIA SSID convention map (mobile/tracker use)
- Will need its own distinct callsign+SSID identity separate from K2GIA-10 (fixed station) once online
- Firmware: `richonguzman/LoRa_APRS_Tracker`. Flash via the Tracker WebFlasher (richonguzman.github.io/lora-tracker-web-flasher — NOT the iGate WebFlasher, easy to mix up) using Chrome (needs WebSerial). Select board, latest firmware, "Install as factory reset," connect board, Flash Firmware, select COM port. After flashing, board broadcasts WiFi AP `LoRaTracker-AP` (password `1234567890`) — connect and browse to `192.168.4.1` in Chrome for the WebUI config page.
- USB cable note: many micro USB cables are charge-only (2-wire). Confirm data capability by plugging in and checking that a COM port actually appears (Windows: Device Manager → Ports) before assuming a cable will work for flashing.

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

## K2GIA SSID Map (full, cross-reference)
- `K2GIA` — Charles personally (portable/voice/OTA)
- `K2GIA-1` — Graywolf/UV-5R M fixed 2m digi+iGate (see separate 2m APRS reference doc)
- `K2GIA-5` — APRSdroid (phone-based)
- `K2GIA-7` — planned TidRadio TD-H9 handheld (mobile 2m APRS)
- `K2GIA-9` — planned LoRa APRS tracker (this doc, on order)
- `K2GIA-10` — existing LoRa APRS fixed station (this doc)

## Related / Not Yet Built
**APRStastic** (afourney/aprstastic on GitHub) — bidirectional Meshtastic↔APRS gateway, TODO/experiment item, not yet built. Would run on a dedicated spare Pi + dedicated Meshtastic node (NOT CJG1/CJG2). Two open decisions before building:
1. OK with CNJ mesh node positions appearing on the public aprs.fi map?
2. Which spare node + which Pi (keep off cnjmesh1's crowded USB bus)?

Full detail in `todos.md` / Claude's memory — this is Meshtastic-adjacent, not part of the LoRa APRS (K2GIA-9/-10) build itself; kept as a separate consideration.

**APRS-Agent** (map.aprsagent.com) — self-hostable APRS-IS bridge/automation platform with AI Gateway, repeater/silence monitoring, propagation detection. Reference only, not yet involved with — plan is to revisit once both 2m APRS (Graywolf) and LoRa APRS builds are fully stable. Would run on a separate VPS/spare Pi, not cnjmesh1. Charles has ruled out German hosting providers (Contabo, Hetzner) specifically due to ID-verification friction — would need a non-German alternative (DigitalOcean, Linode, Vultr) if pursued.
