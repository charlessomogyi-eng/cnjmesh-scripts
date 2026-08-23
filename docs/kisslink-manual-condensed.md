# KISSLink BLE APRS Console — Condensed Manual Reference

**Last updated:** 2026-08-23. Source: KISSLink BLE APRS Console official user manual v0.5.0 (package `com.bughunter.kisslink`, by Kelvin Hill/VA3KJH). This is a condensed, plain-language reference for quick lookup — for tab-by-tab field values already confirmed working for K2GIA-7, see `td-h9-app-field-reference.md` first; this doc is for deeper "how does this feature actually work" detail the field reference doesn't cover.

## What it is, in one paragraph
KISSLink connects to any BLE KISS-capable radio (TD-H9, RT-950, or generic) over Bluetooth Low Energy, decodes AX.25/APRS packets locally on the phone, and provides APRS messaging, decode/display, an APRS-IS internet connection, and a station map — all from one app, no bridge or separate hardware needed. It's an "operator tool": it can genuinely transmit over RF and send APRS-IS traffic, so normal amateur radio operating rules and responsibilities apply.

## Screen-by-screen concepts (beyond the raw field list)

### Control tab — the BLE/KISS radio link console
- **Automatic BLE profile detection order**: (1) a complete manual override if all 4 UUID fields are filled and match discovered characteristics, (2) a previously-saved profile for that specific BLE address, (3) known split profile (AF00 service, AF01 TX/AF02 RX — this is the TD-H9), (4) known single-characteristic profile (FFE0 service, FFE1 for both — this is the RT-950), (5) generic single characteristic with both notify+write, (6) generic split notify/write in a non-standard service.
- **Manual override requires all four fields** (RX service, RX characteristic, TX service, TX characteristic) — a partially-filled manual profile is ignored entirely rather than partially applied.
- **BLE/KISS dashboard fields explained**: `malformed` = KISS frames that failed to parse (should stay 0 — non-zero means bad framing or an incompatible device); `non-data` = KISS frames whose command byte isn't a data frame (counted but not APRS-decoded, normal background noise from some devices); `drops` = BLE notification drops from buffer/state issues (should stay 0).
- **KISS TX port**: normally leave at 0. Only relevant for multi-port KISS TNCs — sets the high nibble of the outbound KISS command byte. The TD-H9 doesn't need this changed.

### Settings tab
- **BLE scan filter** is a real regex, not a wildcard pattern — use `H9` not `*H9*`. Matches against device name, MAC address, or advertised service UUIDs.
- **Destination callsign (tocall)**: this is KISSLink's own app identifier riding in the AX.25 header of every packet you send — analogous to a browser's User-Agent string. It has nothing to do with who receives your message. Safe to leave at the app default (`APKJH2`).

### Msgs tab
- **Send method (RF vs APRS-IS) is independent of what's connected** — you can have both BLE and APRS-IS connected simultaneously and explicitly pick which path a given message goes out on.
- **Message path here is separate from the Settings-tab beacon/experimental path** — changing one does not change the other. "Use Saved Path" button copies the Settings-tab path into the message-specific field; "Direct" clears it for a no-digipeater send.
- **Message IDs, ACK/REJ matching, and duplicate suppression** are all handled automatically — you don't need to manage message numbering yourself.
- **Queries and group addresses sent without ACK requests automatically**: any message starting with `?`, or addressed to `ALL`, `QST`, or `CQ`, is sent without a message number and without requesting an ACK — this is standard APRS convention, not a bug (and per this project's research, `CQ` specifically isn't a recognized broadcast address anyway — use `BLN1`-`BLN9` for genuine broadcasts, see `aprs-bulletins-and-bridging-reference.md`).
- **"Show all heard APRS messages"** is purely a display toggle — when on, it shows message/ACK/REJ traffic *between other stations* that KISSLink happens to overhear, but this observed traffic is never auto-ACKed and never affects your own outbound message state. Safe to leave on or off depending on whether you want that extra visibility.

### IS tab (APRS-IS Companion)
- **"This panel does not create general internet-to-RF gating"** — explicitly stated in the app's own UI. Even with APRS-IS connected and receiving, KISSLink will never automatically retransmit internet traffic out over RF. The only way RF gets involved is the separate, explicitly opt-in "Upload RF-heard packets to APRS-IS" checkbox, which only goes the *other* direction (RF → internet), making K2GIA-7 act as a mobile IGate when checked.
- **RF-heard upload, when enabled, only uploads packets actually received through the RF/KISS path** — it does not re-upload things KISSLink already received via APRS-IS, avoiding a feedback loop.
- **Filter field** uses standard APRS-IS server-side filter syntax (same system documented in depth in `k2gia-5-aprsdroid-reference.md`) — e.g. `m/100` for a 100km radius around your live position, or `r/lat/lon/radius` for a fixed point.

### APRS tab (decode/display)
- Shows **both RF-decoded and APRS-IS-received packets in one list**, each origin-tagged so you can tell them apart.
- **Source/destination regex filters on this tab are purely a local display filter** — they don't affect what's captured, logged, mapped, or affect messaging state. Safe to experiment with freely; clearing the filter always brings back the full picture.
- Recognizes and decodes: Position Reports, Mic-E, Object/Item, Message, Status, Weather, Telemetry, and Third-party (nested/relayed) packet types — the same type vocabulary covered in the APRS-IS filter documentation.

### Map tab
- Uses OpenStreetMap via osmdroid — no API key needed, but does need internet for live tile loading (tiles cache during normal use, but there's no deliberate bulk offline-download feature).
- **Generic "Rings" vs "APRS range overlay" are different things**: Rings are just operator-drawn measuring circles around the selected point (not derived from any packet data). APRS range overlay is a real value decoded *from* a station's packet (RNG field, compressed range, or PHG-derived estimate) — representing something that station actually reported about itself.
- **Course/PHG/DFS/DF overlays are all data-driven** — if no currently-displayed packets contain that specific kind of data, enabling the overlay will appear to do nothing. That's expected, not a bug.
- **Trails only apply to stations** (repeated real position reports over time) — objects and items don't form trails, since they're not a station's own movement, just something a station is reporting about.

### Log tab
- **Basic mode** is meant to be readable by a human operator during normal use — permission checks, connection state changes, packet summaries, warnings, errors.
- **Verbose mode** adds full byte-level detail — raw BLE notification hex, KISS frame hex, AX.25 field breakdown, raw APRS payload — useful for diagnosing a specific problem (this is exactly the level of detail used throughout this project's troubleshooting sessions), but noisy for routine use.
- **"Share" (from the Log screen) bundles more than just the log text** — it includes app version, Android/device info, current BLE and protocol state, APRS-IS state, selected device/profile, and live counters, all packaged together. This is the preferred format if ever reporting a bug to Kelvin.

## Where to look for more detail
This covers the conceptual "why does this work this way" material beyond the field-by-field reference. If something about KISSLink's behavior doesn't make sense and isn't covered here or in `td-h9-app-field-reference.md`, ask Claude to look at the full manual content again — it's substantial (15 sections) and this condensed version deliberately leaves out most illustrative screenshots/examples in favor of the underlying mechanics.
