# K2GIA-5 (APRSdroid) Reference

**Last updated:** 2026-08-23

## Purpose
K2GIA-5 is Charles's always-on phone-based APRS node — carried on his person as a mobile tracker when K2GIA-7 (TD-H9) isn't on him, and also used to scan APRS traffic while stationary. No RF hardware involved — internet/APRS-IS only. This is intentional: Charles already has two RF stations (K2GIA-1 home/Graywolf, K2GIA-10 LoRa iGate) and doesn't want a third radio or a Bluetooth/cable TNC setup just for this node. See `td-h9-app-field-reference.md` for the RF-capable TD-H9/K2GIA-7 setup, which is the separate, RF-first counterpart to this node.

## App: APRSdroid
Note: the app is **APRSdroid**, not "androidaprs" (easy to mistype/mishear from a video).

### Connection Protocol — the key setting
Options under Connection Protocol:
- **Internet (APRS-IS)** — internet-only, no radio/TNC. **This is what K2GIA-5 uses.**
- **Audio (AFSK)** — phone mic/speaker to an external TNC via audio cable.
- **TNC (KISS)** — TCP or classic Bluetooth SPP TNC. This is the mode used if bridging to the TD-H9 via Kelvin Hill's separate BLE KISS TCP Bridge app (see `td-h9-app-field-reference.md` — not used for K2GIA-5, only relevant if ever wanting APRSdroid's own UI on the TD-H9 instead of KISSLink/TD-H9 APRS Messenger).
- **TNC (plaintext TNC2)** — different framing, not used.
- **Kenwood (NMEA waypoint)** — specific Kenwood radios, not used.

**Important limitation:** APRSdroid's native Bluetooth support is **classic Bluetooth SPP only** — it cannot talk to BLE-only devices like the TD-H9 directly. That's why Kelvin's bridge app exists as a separate, optional layer.

### APRS-IS (Internet) connection fields
| Field | Value |
|---|---|
| APRS-IS Passcode | `16025` (same K2GIA base-callsign passcode used everywhere else) |
| Server | `rotate.aprs2.net` (recommend changing from whatever default like `euro.aprs2.net` shows — use the same server as other K2GIA stations for consistency) |
| Connection Type | TCP connection |
| Port | 14580 |
| Neighbor radius | 50km default — packets shown from stations within this range of your position |
| Packet filter | optional APRS-IS server-side filter string (see Filter syntax below) — blank means server default, which may show little/nothing without one |
| TCP socket timeout | 120s default — time before resetting a stalled connection |
| Connection Logging | leave off (verbose status output, only useful for troubleshooting) |

### APRS-IS filter syntax (for the Packet filter field)
Filters combine short codes with slashes/spaces to limit what the server sends:
- `b/CALLSIGN` — "buddy" filter, only packets from specific callsign(s) — e.g. `b/K2GIA*`
- `o/OBJECTNAME` — only packets for a specific named object
- `r/lat/lon/radius` — radius filter around a point, e.g. `r/40.4187/-74.5607/50` (K2GIA-1's coordinates, 50km radius)
- `m/radius` — radius around your own login position (good for a mobile/carried node like K2GIA-5 since it moves)
- `t/type` — filter by packet type (positions, messages, weather, etc.)
- `p/prefix` — by callsign prefix, e.g. `p/K2`

For K2GIA-5 specifically, `m/50` (radius around current position) is likely the most useful choice since the phone moves with Charles — a fixed `r/lat/lon/radius` filter would need manual updating as location changes.

### Location Source
**SmartBeaconing™** — correct choice for a mobile/carried node (adjusts beacon rate based on speed/movement, unlike a fixed interval).

## CRITICAL: messages don't send until Tracking is started
**Found 2026-08-23, this cost a long troubleshooting session — read this first if messages seem to silently vanish.** APRSdroid does not send composed messages immediately, even with a correctly configured and apparently-connected APRS-IS setup. Messages sit queued locally — visible in your own sent-message list, giving the false impression they went out — until you tap **Start Tracking**. Only then does APRSdroid actually establish its APRS-IS connection and flush the queue. The UI gives no real warning about this beyond a small toast message ("The message will be sent as soon as you start tracking.") that's easy to miss if you're not watching for it right after hitting send.

**Symptoms this causes if missed:**
- Message appears in APRSdroid's own conversation thread as if sent
- Exported connection log shows RX traffic (background APRS-IS chatter) but **no TX line at all** for the message
- A "delivery counter" style field (seen as `0/7` next to the recipient) never advances
- Nothing arrives at the recipient (confirmed via Graywolf's own database — zero record of the message despite Graywolf's APRS-IS being reliable throughout this whole project)

**Fix:** tap **Start Tracking** (menu → Start Tracking, or the main toggle) after composing a message, or before, doesn't matter — as long as tracking is active when you want a send to actually go out. Once confirmed working (2026-08-23), two test messages ("Test aprsdroid to home station," "Test aprsdroid to mobile") both landed on Graywolf within a minute of starting tracking, tagged correctly as arriving via IS.

**Also corrected same day:** APRS-IS server field had drifted to `euro.aprs2.net` (likely a stale default from initial setup/tutorial) instead of `rotate.aprs2.net` used everywhere else. Changed to match. Unclear whether this alone would have blocked delivery (APRS-IS is one global network, any entry point should work) — the Tracking toggle was the actual confirmed fix, but worth keeping server consistent regardless.

**Practical implication:** if you're using K2GIA-5 to send a message and want it to actually go out, always confirm Tracking is on first — don't assume "message appears sent" means "message was sent."

### SmartBeaconing values (reviewed/changed 2026-08-23)
| Setting | Value | Notes |
|---|---|---|
| Fast Speed | 25 km/h (~15 mph) | Changed from default 100 km/h — appropriate for phone-in-pocket/walking-pace use, not vehicle-mounted |
| Fast Rate | 60s | Beacon interval once at/above Fast Speed |
| Slow Speed | 5 km/h | Below this = considered "stopped" |
| Slow Rate | 1200s (20 min) | Beacon interval when stationary — good for battery life |
| Min Turn Angle | 10° | Corner-pegging trigger; less relevant for phone-carry use (more relevant for vehicle tracking) |
| Turn Slope | 240 | Speed-dependent turn angle modifier |
| Min Turn Time | 15s | Floor between turn-triggered beacons |

### Known app limitation
**APRSdroid has no metric/imperial toggle** (confirmed via open GitHub issues #98 and #133) — all speed/distance fields are locked to km/h and km regardless of phone locale settings. The Fast Speed value above (25 km/h) was chosen with this in mind.

## Open items / not yet covered
- Whether to revisit APRS-IS server for consistency — resolved 2026-08-23, now set to `rotate.aprs2.net`.
- Whether to set a packet filter (currently likely blank/default) — `m/50` recommended per above.
- **Cross-node messaging caveat identified 2026-08-23, partially resolved:** K2GIA-5 is Internet/APRS-IS-only — it cannot transmit or receive over RF at all, and (see above) requires Tracking to be active for sends to actually go out. K2GIA-5 → K2GIA-1 (Graywolf) confirmed working end-to-end same day. **K2GIA-5 → K2GIA-7 (TD-H9) not yet re-confirmed** with Tracking properly enabled — earlier attempts all predate discovering the Tracking requirement, so they don't count as valid tests. Worth a fresh attempt next APRS session: enable Tracking on K2GIA-5, send to K2GIA-7, then check on either KISSLink or TD-H9 APRS Messenger's Msgs tab (with that app's own APRS-IS connected) to confirm receipt.
