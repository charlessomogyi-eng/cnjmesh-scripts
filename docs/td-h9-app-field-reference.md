# TD-H9 BLE APRS Apps — Field Quick Reference (Aug 23, 2026)

Quick-lookup reference for the two working TD-H9 BLE messaging apps (both by Kelvin Hill / VA3KJH), meant for use in the field when mobile with the TD-H9 (K2GIA-7) and no time to dig through the full manual. Covers every screen/field actually seen in setup and use. See `td-h9-odmaster-aprs-messaging-bug.md` for the backstory on why these apps exist (ODmaster's Send Message bug) and how access was obtained (Google Play closed testing via Kelvin's tester list).

**Known-good values for K2GIA-7, for quick copy/paste in the field:**
- Callsign: `K2GIA`, SSID: `7`
- Digipeater path: `WIDE1-1,WIDE2-1`
- APRS-IS server: `rotate.aprs2.net`, port `14580`
- APRS-IS passcode: `16025`
- TD-H9 BLE name to scan for: `TD-H9-7867(BLE)`
- Home station to message: `K2GIA-1` (Graywolf)

---

## KISSLink BLE APRS Console
Package: `com.bughunter.kisslink`. Full-featured, radio-agnostic (works with TD-H9 and RT-950). Seven tabs: Control, Log, Settings, APRS, Msgs, IS, Map. Full manual (v0.5.0) also in this repo's context if deeper detail is ever needed — this doc is the fast-path version.

### Settings tab
| Field | What to set | Notes |
|---|---|---|
| BLE device filter | `H9` (optional) | Narrows scan list; blank shows all nearby BLE devices, which gets noisy (mesh nodes, earbuds, etc. all show up) |
| After connect / After service discovery (ms) | leave default (600 / 300) | Timing delays, no need to touch |
| Write-with-response | leave unchecked | TD-H9 uses write-without-response (AF01 char) |
| KISS TX port | leave `0` | Only matters for multi-port TNCs |
| Source callsign | `K2GIA` | |
| Source SSID | `7` | **Double check this — easy to fat-finger, see TD-H9 APRS Messenger gotcha below** |
| Destination callsign (tocall) | leave default `APKJH2` | This is KISSLink's own app identifier in the packet header, not a recipient — safe to leave |
| Destination SSID | leave `0` | |
| Digipeater path | `WIDE1-1,WIDE2-1` | |
| Dark mode | personal preference | |
| **Save Settings button** | tap after any change | Easy to forget |

### Control tab
| Element | What it means |
|---|---|
| Selected Device box | Shows currently selected BLE device; tap to change |
| Scan / Select button | Opens BLE scan; look for `TD-H9-7867(BLE)` in the list |
| Connect / Disconnect | Only one app (KISSLink OR TD-H9 APRS Messenger) can hold the BLE connection at a time — disconnect one before using the other |
| Start Last / Auto-start last | Reconnects to last successful device; auto-start only runs if explicitly enabled |
| BLE / Proto status chips | Both must show **READY** (green) before anything works. Banner should say "Operational: RF/KISS ready" |
| KISS TNC dashboard | Shows live BLE RX fragments, KISS frame counts, malformed count (should stay 0), TX write ok/failed counts — good first troubleshooting stop if something's not working |

### Msgs tab
| Field | What to set |
|---|---|
| Send method | RF (default) — use this unless deliberately testing APRS-IS |
| Message destination | Callsign of who you're messaging, e.g. `K2GIA-1` |
| Message digipeater path | Tap **Use Saved Path** to pull WIDE1-1,WIDE2-1 from Settings, or **Direct** for no path |
| Message text | Your message |
| Request ACK/retry | leave checked (default) |
| Show all heard APRS messages | optional — shows OTHER stations' message/ACK/REJ traffic too, display-only, doesn't affect your own send/receive |

### IS tab (APRS-IS — optional, RF-only is the default plan for mobile use)
| Field | What to set |
|---|---|
| APRS-IS server | `rotate.aprs2.net` |
| Port | `14580` |
| APRS-IS callsign | `K2GIA-7` |
| APRS-IS passcode | `16025` |
| APRS-IS filter | optional, e.g. `m/100` for 100km radius, blank is fine |
| Upload RF-heard packets to APRS-IS | leave unchecked normally — only enable if deliberately acting as a mobile IGate somewhere Graywolf can't reach |

**Status update (Aug 23, 2026, later same day):** confirmed IS Companion connects successfully when attempted — the earlier "Disconnected" observation was simply an untested state, not a persistent bug. Don't assume a disconnected screenshot means anything is broken; just try Connect and check the current status. Full detail in `known-issues.md` and `aprs-bulletins-and-bridging-reference.md`.

### APRS tab
Live decoded packet feed (position reports, weather, telemetry, messages, status, third-party) from whatever the TD-H9 hears over RF. Always active once BLE/KISS is READY, nothing to configure. Source/destination regex filters available if the list gets too busy.

### Map tab
OpenStreetMap display of heard stations/objects/items. Options (collapsed by default): Follow, Fade, Trails, Grid, Rings (generic range rings), and APRS overlays (Course, PHG/DFS, DF, APRS range). Not yet used in the field as of this writing — worth trying next time out with the radio.

---

## TD-H9 APRS Messenger
Package: `com.tdh9.aprsmessenger`. Simpler, TD-H9-specific, two tabs only: Setup, Messages. Faster to use for quick messaging than KISSLink.

### Setup tab
| Field | What to set | Notes |
|---|---|---|
| Callsign | `K2GIA` | |
| **SSID** | `7` | **CONFIRMED GOTCHA (Aug 23, 2026): this field silently held `1` instead of `7` on first setup and was never double-checked before first use.** Result: outbound messages were sent with source=K2GIA-1 (Graywolf's own callsign) instead of K2GIA-7, causing an apparent self-addressed message and 3 failed ACK retries over ~3.5 minutes before catching it. **Always verify this field explicitly before first use in the field, don't assume the default is right.** |
| Digipeater path | `WIDE1-1,WIDE2-1` | |
| Destination tocall | leave default `APKJH3` | App's own identifier, not a recipient, same idea as KISSLink's APKJH2 |
| APRS-IS server / port | `rotate.aprs2.net` / `14580` | |
| APRS-IS passcode | `16025` | |
| APRS-IS filter | optional | |
| Accept base callsign messages as mine | leave checked (default) | Accepts messages to bare `K2GIA` as well as `K2GIA-7` |
| Show heard messages not addressed to me | optional | Same idea as KISSLink's "show all heard" |
| Show app destination group messages | optional | |
| **Save settings button** | tap after any change | |
| Find TD-H9 / Stop scan | scan for the radio, filtered to TD-H9 specifically (may be faster/cleaner than KISSLink's generic scan) |
| Connect radio / Disconnect | same one-app-at-a-time BLE rule as KISSLink applies |

### Messages tab
| Field | What to set |
|---|---|
| To: | callsign or service, e.g. `K2GIA-1`, or `WHO-IS` for the WHO-IS service shortcut |
| Message text | up to 67 bytes shown live as you type |
| Send using | **Auto** (recommended — picks Radio automatically when BLE-connected, falls back to Internet/APRS-IS if not), or force Radio / Internet manually |
| Request ACK / retry | leave checked (default) |

Service shortcuts available: **WHO-IS** (query), **Path test**, **App group**, **Cancel retries**, **Copy all conversations**. Messages are grouped into per-contact conversation threads below the compose area, each showing sent/received counts and a running log with RF/Internet tag and message ID per entry (e.g. `RF {001}`).

---

## Two other apps in Kelvin's portfolio — reference only, not installed
- **BLE KISS TCP Bridge** (`com.bughunter.blekisstcpbridge`) — Android app (not the Windows-only BLE-Bridge-W11, different tool despite similar name) that bridges TD-H9's BLE KISS to a local TCP port (127.0.0.1:8001) so **stock APRSdroid** can connect to it as a normal KISS TCP TNC. Not needed since KISSLink and TD-H9 APRS Messenger both connect directly — documented here only in case APRSdroid's specific UI/feature set is ever wanted instead.
- **BLE-Bridge-W11** — Windows-only, ruled out for mobile/phone use, see `td-h9-odmaster-aprs-messaging-bug.md` for detail.

---

## Field troubleshooting quick-hits
- **Nothing shows up in BLE scan**: get physically closer to the powered-on TD-H9 (BLE range is short); set the BLE filter to `H9` to cut noise from other nearby BLE devices (mesh nodes, earbuds, etc. will otherwise flood the list).
- **Message sent but never ACKs**: check Setup/Settings SSID field first — a wrong SSID means the packet's source callsign is wrong, which can cause silent failures. Also possible: real RF conditions, digipeater unavailable, or (less likely) a message-ID collision if retrying the exact same text right after a failed send.
- **Only one app can hold the BLE connection to the TD-H9 at a time.** Disconnect in one app before connecting in the other.
- **Static/hiss on the radio itself when powered on**: check Squelch Level in the TD-H9's own radio menu — should be `1`. If it reads `0`, that's fully open squelch (passes all noise) and is not a fault.
