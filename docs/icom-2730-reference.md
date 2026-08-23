# Icom IC-2730A Reference

**Last updated:** 2026-08-23. Source: Icom's official IC-2730A/IC-2730E instruction manual (English) and product page (icomamerica.com). This is a condensed, practical reference in plain language — for the full manual with every diagram, see the official PDF (search "IC-2730A instruction manual" on icomamerica.com's Manual Download page, or ask Claude to look it up again if this doc doesn't cover what you need).

## What it is
VHF/UHF dual-band mobile transceiver. 50W on both bands (144-148 MHz VHF, 430-450 MHz UHF, US amateur version), with wideband receive (118-174 MHz and 375-550 MHz — covers aviation, marine, weather, and other utility listening in addition to the amateur bands). Two physical pieces: a **main unit** (the actual radio, usually mounted out of sight) and a **controller** (the front panel with the display, knobs, and buttons, mounted where you can reach it) connected by a cable.

## Physical layout basics
- Each side of the controller (left/right) has its own tuning dial, volume knob, and squelch knob — the radio can display and control two independent bands/frequencies at once (dual watch), one on each side.
- **MAIN BAND** — whichever side is currently active for transmitting. You can only transmit on whichever side is set as MAIN. Push the MAIN BAND key on either side to make it the MAIN band.
- **[MENU]** button — enters the menu system. Push once to enter; navigate with the dial to move through options, use the left/right keys or ENTER to move between menu tree levels.
- **[V/MHz SCAN]** — switches to VFO (frequency-dial) mode; also starts scanning if held.
- **[MR CALL]** — switches to Memory mode (stored channels); hold for Call channel mode (two dedicated quick-recall channels, one per band).
- **[MW]** (Memory Write) — saves the current frequency into a memory channel.
- Squelch and volume are physical knobs, not menu settings — turn the squelch knob until background noise/hiss just disappears (same idea as the TD-H9).

## Basic operation
**Setting a frequency:** switch to VFO mode ([V/MHz SCAN]), then rotate the tuning dial. Push [V/MHz SCAN] again to toggle into 1 MHz-step tuning for fast changes across a wide range, then again to go back to normal fine-tuning steps.

**Tuning step:** the amount the frequency changes per dial click — adjustable in the menu (5, 6.25, 8.33, 10, 12.5, 15, 20, 25, 30, or 50 kHz, or Auto). Menu path: MENU → TS.

**Transmitting:** select output power (Low/Mid/High) with the power button, then hold PTT to talk, release to receive. It's good practice to listen to the frequency first to make sure it's clear before transmitting.

**Memory channels:** 1000 regular channels (organized into 10 banks, A-J, for organization) plus 2 dedicated Call channels (one per band) for instant recall of a favorite frequency. To save the current VFO frequency: push [MW], then either pick a specific channel number or hold [MW] for 1 second to auto-save into the next open channel.

## Repeater / duplex operation
A repeater receives on one frequency and re-transmits on another; your radio needs to transmit on the repeater's *input* frequency while listening on its *output* frequency, offset by a set amount (typically 0.6 MHz on 2m, 5 MHz on 70cm).

- Hold [MONI DUP] to bring up the duplex direction screen — choose OFF (simplex), DUP− (transmit below receive frequency), or DUP+ (transmit above).
- Set the actual offset amount separately in the menu (MENU → OFFSET), typically left at the band's standard default.
- **Auto Repeater function** (US/Korea versions only): when turned on, the radio automatically figures out the correct duplex direction based on which known repeater frequency range you've tuned into — handy so you don't have to remember it live. Menu path: MENU → EXMENU → FUNC → AUTORP.
- To check if you're within repeater range without needing the repeater (simplex check): hold [MONI DUP] to briefly listen on your own transmit frequency instead of the receive frequency.
- **1750 Hz tone burst** (needed for many European repeaters, not typically needed in the US): hold PTT and press the T-CALL-assigned key.

## Tone squelch (CTCSS/DTCS) — for quiet standby and repeater access
Most repeaters require a subaudible tone on your transmitted signal to open them up; some setups also let you filter what you hear the same way.

- Menu path: MENU → TONE, then choose a mode:
  - **TONE** — sends a subaudible tone on transmit only (most common for accessing a repeater)
  - **TSQL** — both sends a tone on transmit and requires a matching tone to open your squelch on receive (mutes everything except stations using your same tone — good for a quiet private-ish channel)
  - **DTCS** — same idea as TSQL but using digital codes instead of analog tones
  - Reverse/hybrid variants (TSQL-R, DTCS-R, etc.) exist for more specific noise-filtering scenarios — rarely needed for standard repeater use
- Once TONE or TSQL is selected, set the actual tone frequency separately: MENU → R TONE (for transmit/repeater access) or MENU → C TONE (for the squelch-matching tone on receive). 50 standard CTCSS tones available (67.0-254.1 Hz); a common example is 88.5 Hz.
- DTCS codes (104 available, 023-754) are set similarly via MENU → CODE, with a separate DTCS Polarity setting (MENU → DTCS-P) if a specific repeater or group requires reversed polarity on TX or RX.

## Scanning
Several scan types available depending on mode:
- **VFO scans**: Full (entire band), Band (selected band only), Program (a custom-defined frequency range you set up in advance), Program Link (multiple program ranges scanned in sequence)
- **Memory scans**: Full (all saved channels), Band (channels in the current band only), Mode (channels matching the current operating mode)
- **Bank scans**: Full (all banks) or a specific single bank
- Start a scan: hold [V/MHz SCAN] for 1 second to bring up the scan type menu, pick a type, then push [V/MHz SCAN] to start; push again to stop.
- **Skip channels**: mark specific frequencies/channels to be skipped during scans (useful for known-noisy or irrelevant frequencies) — set via the memory edit screen, or on-the-fly by holding [MW] while a scan is paused on an unwanted signal.
- **Priority Watch**: while sitting on a VFO frequency or scanning, the radio periodically (every 5 seconds) checks a separate priority channel/memory for activity — useful for keeping an ear on a specific repeater or calling frequency without leaving your main frequency.

## Weather channels (US version)
10 NOAA weather channels, selectable in Memory mode via [MR CALL]. Weather Alert function (MENU → WX-ALT) monitors the selected channel every 5 seconds in the background and beeps/displays an alert if NOAA transmits a severe weather alert tone.

## Bluetooth headset (requires optional UT-133/A unit installed)
If you ever add the optional Bluetooth module and VS-3 headset:
- Turn Bluetooth on: MENU → EXMENU → BT SET → BT → ON
- Pair: MENU → EXMENU → BT SET → PAIR, then follow the headset's own pairing steps
- VOX (hands-free, voice-activated transmit): MENU → EXMENU → BT SET → HS SET → VOX → VOX → ON, then set sensitivity via VOX LV in the same menu branch
- Auto-reconnect to a previously paired headset is on by default (AT CON setting)
- Bluetooth range is roughly 10 meters; can be affected by other 2.4GHz devices (WiFi, microwaves) nearby

## DTMF
Up to 16 saved 24-digit DTMF codes for autodial-style repeater/phone-patch access. Enter/save codes via holding the DTMF-assigned key, selecting Memory, then entering digits. Transmit a saved code the same way but selecting TX instead, or transmit ad-hoc via Direct Input without saving it.

## Cloning (copying settings between two radios, or to/from a PC)
- **Radio-to-radio**: connect two IC-2730A/E units via the optional OPC-474 cable to their SP2 jacks, set one to Clone (sub) mode and the other to Clone Master mode via MENU → EXMENU → OTHERS → CLONE, then confirm on the master to start the transfer.
- **PC cloning**: requires the free CS-2730 software (downloadable from Icom) plus the optional cloning cable — lets you build/edit memory channels and settings on a computer and upload them, which is generally much faster than programming channels by hand on the radio itself.

## Reset options
- **Partial reset** (MENU → EXMENU → OTHERS → RESET → PART): restores all settings to factory defaults but keeps your saved memory channels intact.
- **All reset** (MENU → EXMENU → OTHERS → RESET → ALL): wipes everything, memories included, back to factory defaults. Use with caution — memory content cannot be recovered once cleared.

## Quick specs reference
| Spec | Value (US version) |
|---|---|
| TX frequency | 144-148 MHz, 430-450 MHz |
| RX frequency | 118-174 MHz, 375-550 MHz |
| Output power | 50W / 15W / 5W |
| Memory channels | 1000 (banks A-J) + 2 Call channels |
| Power supply | 13.8V DC ±15% |
| TX current draw | ~13A |
| Antenna connector | SO-239 (50Ω) |
| Operating temp | -10°C to +60°C |

## Where to look for more detail
This doc covers the operations most likely to come up in normal use. For anything not covered here — detailed CI-V remote-control commands, full EXMENU item-by-item reference, exact wiring pinouts, troubleshooting error codes — the full official manual has it. If you hit something this doc doesn't answer, ask Claude to pull the relevant section from the manual again rather than guessing.
