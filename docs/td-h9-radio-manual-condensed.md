# TidRadio TD-H9 Radio — Condensed Manual Reference

**Last updated:** 2026-08-23. Source: TidRadio's official TD-H9 User Manual (71 pages, GMRS/Ham version, distributed via tidradio.com and mirrored on ManualsLib). This is a condensed, plain-language reference for K2GIA-7 — covers the physical radio itself (buttons, menu system, APRS radio-side setup). For the phone apps (KISSLink, TD-H9 APRS Messenger) that connect to this radio over BLE, see `td-h9-app-field-reference.md` and `kisslink-manual-condensed.md` instead — this doc is radio-only.

## Known-good values already confirmed working for K2GIA-7
- APRS passcode: `16025`
- Callsign: K2GIA, SSID 7
- Digipeater path: WIDE1-1,WIDE2-1
- APRS firmware: V1.0.15, radio firmware V1.0.32 (as of last check)
- Squelch Level: **1** (not 0 — 0 is fully open and sounds like broken static; see `known-issues.md`)
- Native BLE name: `TD-H9-XXXX` — **do not** connect to the `(BLE)` suffix version from the radio's own Bluetooth menu if trying to use a Bluetooth headset (that suffix is for the apps/KISS data path, not audio)

## Basic controls
- **Power/Volume knob**: rotate clockwise to power on, adjusts volume.
- **[VFO/MR] key**: toggles between VFO (Frequency) mode and MR (Channel/Memory) mode.
- **[A/B] key**: switches which display (upper/lower) is active/selected.
- **[MENU] key**: enters the menu system.
- **[Back] key**: exits menu/functions.
- **PTT**: red LED lights while transmitting; green LED lights while receiving.
- Programmable side keys (PF1 short/long press, etc.): can be set to FM Radio, Lamp, TONE, Alarm, Weather, PTT2, or OD PTT.

## VFO (Frequency) vs MR (Channel) mode
- **VFO mode**: tune by frequency directly, using the encoder or arrow keys. Required for saving a frequency into a memory channel.
- **MR mode**: select from pre-programmed channels (display shows `CH-XXX`). Requires channels to already be programmed (via manual entry or programming software).
- To save a VFO frequency into a channel: set the frequency in VFO mode, then follow the channel-write procedure (channel number selection + confirm).

## Scanning
- **Frequency Scanning**: sweeps across a frequency range looking for active signals.
- **Channel Scanning**: scans through programmed memory channels only.
- **CTCSS/DCS Scanning** ("SEEK"): MENU → Scan → SEEK DCS — auto-detects the tone/code a signal is using. Only works in VFO mode, not Channel mode.
- Two scan resume behaviors:
  - **CO (Carrier-operated Scan)**: stops on any detected signal, resumes scanning once the signal clears.
  - **SE (Search Scan)**: stops on a detected signal and stays stopped (doesn't auto-resume).

## Repeater / TX offset
- **TX Repeater Tone / Offset**: set frequency offset direction — Off (no offset/simplex), Positive, or Negative — matched to whichever repeater you're using. Different repeaters use different standard offsets; check the specific repeater's published info.
- **1750Hz Tone**: used to access certain repeaters (more common in Europe than the US) — accessible via a programmable key.

## Other radio features
- **Emergency Alert**: configurable alert tone/behavior — options include On Site (local flashlight alarm only) or TX Alarm (transmits a 10-second alarm tone, pauses 2 seconds, repeats).
- **FM Radio**: built-in broadcast FM receiver, separate from the ham/GMRS transmit bands.
- **NOAA Weather Radio**: dedicated orange Weather key — press to enter NOAA weather channel mode, use up/down to select a specific NOAA channel, press again to exit.
- **AM mode**: MENU item 38 enables AM demodulation, but only valid on the 108-136 MHz airband range (for listening to aviation traffic) — has no effect outside that band.
- **VOX**: voice-activated transmit, 5 sensitivity levels (1 = most sensitive/highest gain, 5 = least). Off disables VOX entirely. Cannot be adjusted in Channel mode.
- **Battery Save**: adjustable RX sleep-cycle levels — higher level number = longer battery life but higher chance of missing the first syllable of an incoming transmission when it wakes from sleep to receive.
- **MIC GAIN**: adjustable 0-9.
- **PTT-ID / ANI-ID**: can transmit an identifying signaling code when PTT is pressed, timing configurable (8 groups of codes, programmed via computer software).

## Bluetooth (radio-side menu, separate from the apps)
- **BT ON/OFF** — Menu #1
- **BT Mode** — Menu #2: Receiver (radio passively waits, e.g. for a Bluetooth headset use) vs Transmit-capable modes
- **BT Pin Code** — Menu #11, for pairing PIN
- **Important naming distinction**: for a Bluetooth **audio headset**, connect to the plain `TD-H9-XXXX` Bluetooth name — do NOT use the `(BLE)` suffix version, that's reserved for the data/KISS path used by KISSLink, TD-H9 APRS Messenger, and similar apps. Confusing the two is a common setup mistake.
- **OD PTT / Odmaster PTT-over-cellular function**: lets the radio do PTT calling over the Odmaster app/network rather than RF — separate feature from standard APRS, requires setting OD PTT to "OD" or "OD+Analog" mode and joining a group in the Odmaster app first.

## APRS radio-side menu (MENU → APRS submenu, exact number varies by firmware)
This is the radio's own native APRS beaconing/digipeating configuration — distinct from any phone app.

- **Site Type**: Fix Coordinates (manually entered lat/lon, for a stationary station) vs GPS Coordinates (uses the radio's built-in GPS, for mobile use — this is what K2GIA-7 uses). **Known gotcha**: PTT Linkage and Timed Beacon both being ON simultaneously silently kills timed beaconing — confirmed bug, keep only one enabled at a time.
- **PTT Linkage**: sends a beacon automatically every time PTT is pressed and released.
- **Timed Beacon**: sends a beacon at a scheduled interval (e.g. every 600 seconds/10 min) — this is what K2GIA-7 uses for regular position updates.
- **APRS RX CH / APRS TX CH**: assigns which display channel (A or B) handles APRS receive/transmit — A/B channels can each independently be set to APRS or normal voice. Supported combos include: RX on A/TX on A, RX on A/TX on B (cross-channel), RX-only on A, or simultaneous TX on both A and B.
- **APRS Digital Relay (DIGI)**: the radio can itself act as a digipeater, relaying other stations' packets. Configurable relay names (default `WIDE1`), up to 6 characters, digits/uppercase letters only.
- **Fixed Coordinates use case**: when Site Type is set to Fixed Coordinates, the radio calculates and can display relative distance, true bearing, and direction to other heard stations — useful context info even without GPS lock.
- **Position display precision**: Deg / Deg.min / Deg.min.sec — how coordinates are formatted on-screen.
- **Time Zone**: UTC-12 to UTC+12, needed for correct APRS timestamps.
- **MIC-E status/icon options**: the radio supports MIC-E encoded status types (M0 Off Duty, M1 En Route, M2 In Service, M3 Returning, M4 Committed, M5 Special, M6...) — sets what your beacon's status field shows.
- **Recommended APRS tracking/map services**: Odmaster (web.odmaster.net) or aprs.fi — same site you've used throughout this project to verify K2GIA-7's beacons.

## Firmware upgrade
1. Log into web.odmaster.net
2. Click Remote Control Program → Upgrade Firmware
3. Follow on-screen steps

## Quick troubleshooting
- **Radio keeps transmitting / stuck TX**: check that headphones/mic accessory (if any) are properly seated in the jack — a loose accessory jack is a known cause.
- **General**: if the manual's troubleshooting section doesn't resolve it, contact TidRadio support directly (support@tidradio.com) — the manual notes this as the standard fallback.

## Where to look for more detail
This condensed doc covers what's most likely to come up day-to-day. The full manual (71 pages) has complete step-by-step illustrated instructions, the full DCS/CTCSS code tables (Appendix C/D), full FCC/RF exposure/regulatory text, and complete technical specifications (Appendix B) if ever needed — ask Claude to pull a specific section again rather than guessing if something here doesn't cover it.
