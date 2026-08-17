# APRS 2m (Graywolf) Reference — cnjmesh1

**Last updated:** 2026-08-17

## Hardware & Software
- Radio: UV-5R M, dedicated to APRS, USB-C powered
- Interface: Digirig (black cable), USB to cnjmesh1
- Audio: C-Media USB Audio Device (ALSA card 3, name "Device"), CM108AH USB Audio
- Antenna: **Roof dual-band VHF/UHF antenna** (as of Aug 17 2026 — previously a Nagoya-style whip)
- Software: Graywolf 0.13.13, web UI on cnjmesh1 port 8082
- Config storage: SQLite `/var/lib/graywolf/graywolf.db`, set via web UI only — no flat config file
- DB owned by `graywolf` user — needs `sudo` to query; WAL mode, run `PRAGMA wal_checkpoint(FULL)` before querying for latest data

## Station Identity
- **Callsign:** `K2GIA-1` (changed 2026-08-17 from bare `K2GIA` — digi+iGate combo SSID convention)
- Full K2GIA SSID map:
  - `K2GIA` — Charles personally (portable/voice/OTA)
  - `K2GIA-1` — Graywolf/UV-5R M fixed digi+iGate (this station)
  - `K2GIA-5` — APRSdroid (phone-based)
  - `K2GIA-7` — planned TidRadio TD-H9 handheld (mobile APRS)
  - `K2GIA-9` — planned LoRa APRS tracker (on order)
  - `K2GIA-10` — existing LoRa APRS fixed station (see separate LoRa APRS reference doc)
- Coordinates: 40.4187/-74.5607 (fixed position)

## iGate
- Server: `rotate.aprs2.net:14580`
- Passcode: 16025 (generated from base callsign `K2GIA`, SSID-independent — does not need regenerating if SSID changes)
- Server filter: `r/40.4187/-74.5607/150` (150km radius) — this filter governs general/passive traffic pulled from APRS-IS only. Messages **addressed directly to K2GIA-1** always deliver regardless of this filter or distance (confirmed empirically Aug 17 2026 receiving directed messages from Germany, Manitoba, Nevada via APRS OTA).
- Login: meshdev

## Digipeater
- WIDE1-1
- Uses station callsign (K2GIA-1)
- Dedupe window: 30s (APRS convention)

## Beacon
- Interval: 30 min
- Input gain: -11.5dB

## Messages DB schema (for troubleshooting)
`messages` table columns: id, direction, our_call, peer_call, from_call, to_call, text, msg_id, ack_state, is_ack, is_rej, attempts, failure_reason, path, via, created_at, sent_at, received_at, acked_at

## KNOWN UNRESOLVED ISSUE — cpal/ALSA POLLERR (audio capture)
**Status as of 2026-08-17: unresolved, confirmed NOT blocking core APRS function**

**Symptom:** Graywolf's Rust/cpal audio backend repeatedly throws `cpal input stream error: A backend-specific error has occurred: alsa::poll() returned POLLERR`, sometimes thousands of times per minute, followed by "cpal input stream failed, rebuilding." While actively erroring, the audio device is locked (`arecord` fails with "Device or resource busy") even with PipeWire/wireplumber/pipewire-pulse confirmed masked and dead — this is NOT the old PipeWire contention issue.

**Root cause research (2026-08-17):**
- Matches known open cpal GitHub bug [RustAudio/cpal#730](https://github.com/RustAudio/cpal/issues/730) — ALSA capture overrun (XRUN) triggers POLLERR that cpal doesn't cleanly handle, causing a tight error loop instead of clean recovery/reset.
- Related: [RustAudio/cpal#913](https://github.com/RustAudio/cpal/issues/913) suggests cpal's default ALSA buffer math may be too thin (period_size = buffer_size/4).
- Confirmed via `/proc/asound/card3/pcm0c/sub0/hw_params`: `period_size: 241`, `buffer_size: 482` frames at 48kHz — roughly **10ms total buffer**, very tight margin for a Pi 4 running 15 Docker containers.
- `audio_devices` table in graywolf.db has NO buffer/period/latency column — only `sample_rate`, `channels`, `format`, `gain_db`. No config-level fix available; buffer size is hardcoded in the compiled cpal binary.

**Fixes attempted, ruled out:**
- Switched `source_path` from `plughw:CARD=Device,DEV=0` to `hw:CARD=Device,DEV=0` (bypassing ALSA plug layer) — **no effect**, error rate unchanged, buffer size unchanged (confirms buffer is cpal-controlled regardless of hw/plughw).
- PipeWire/wireplumber/pipewire-pulse all confirmed masked and dead — not the cause.
- Checked for resource contention via `fuser`/`lsof`/`docker stats` — nothing else holding the device; Docker container CPU load normal/idle during error bursts.

**Timing correlation:** Error rate appears to have gotten dramatically worse coinciding with the Aug 17 antenna swap (whip → roof antenna). Theory: roof antenna increases RX signal activity significantly, meaning Graywolf's demodulator is doing continuous decode work far more often than with the quieter whip — more sustained load against the thin buffer = more XRUN opportunities. NOT confirmed as sole cause — per Charles, "this POLLERR has been addressed several times since starting APRS 2m" — session-log.md (Jul 11-12 2026) previously concluded "POLLERR errors are cosmetic — APRS works through them," suggesting this is a long-standing intermittent bug that the antenna change turned from occasional/self-healing into continuous/device-locking.

**Also relevant:** A `graywolf-watchdog.timer`/`.service` was disabled months ago (was restarting every 5 min, breaking PTT) — that watchdog's frequent restarts may have been incidentally clearing POLLERR lockups before they accumulated. Do NOT re-enable per existing hard rule (see cnjmesh1-operations.md).

**Confirmed NOT blocking:**
- TX/beacon function fully unaffected — multiple successful RF beacons and full APRS OTA host/chase sessions completed successfully on 2026-08-17 despite continuous POLLERR errors.
- iGate message delivery via APRS-IS unaffected — ack/PONG/QSL messages received cleanly over the direct APRS-IS TCP connection regardless of RX/audio-capture state.
- Only affects: your own station's ability to *self-hear* its own RF traffic / decode incoming RF packets reliably. Dashboard shows elevated "Bad FCS" count on RX consistent with corrupted demodulation during error bursts.

**Next diagnostic step when resuming (not yet tried):**
Real-time process scheduling — standard fix for Linux ALSA XRUN issues in pro-audio contexts. Add a systemd override for `graywolf.service`:
```
[Service]
CPUSchedulingPolicy=rr
CPUSchedulingPriority=50
LimitRTPRIO=60
```
Prerequisite check before applying: confirm `graywolf` user's current `ulimit -r` (likely 0, needs LimitRTPRIO grant). Fully reversible — delete the override file to revert. Not yet attempted as of session end 2026-08-17; OTA testing succeeded despite the bug being present, lowering urgency.

**Decision:** Charles has a stated preference not to reach out to the Graywolf developer prematurely (pattern of finding issues resolve themselves before outreach was needed). This bug is documented, low-priority (proven non-blocking), and safe to revisit later — no rush to escalate.

## APRS OTA — session results (2026-08-17)
First live test of APRS OTA (aprsota.org) via K2GIA-1:
- PONG confirmed "heard on RF" — proved rooftop antenna + new SSID working end-to-end
- Hosted first op (K2GIA-1 op 1, FN20rk, "testing rooftop antenna"): **8 QSOs, 13 pts, 2 unanswered**
- Chased K0TFU-6 (Jared, the APRS OTA developer, live from DBARA monthly meeting) and K9CMP-9 — both confirmed
- Full handbook reference saved in Claude's persistent memory (all pages read and cited)
- Correction learned: QSL confirmations must be sent `@chasercallsign QSL ...` addressed to **OTA**, never directly to the chaser — direct messages to chasers do not register as confirmed contacts
