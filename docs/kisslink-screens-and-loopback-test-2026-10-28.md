# KISSLink BLE APRS Console v0.5.3: screens, options, and the K2GIA-7 to K2GIA-1 test (Oct 28 2026)

Screenshot-based reference for the KISSLink app (Kelvin Hill, VA3KJH; package `com.bughunter.kisslink`) as used with the TD-H9 (K2GIA-7), plus the end-to-end test against Graywolf (K2GIA-1) on Oct 28 2026. Screenshots are in `docs/images/kisslink-2026-10-28/` (downscaled copies of Charlie's phone captures). Tags: **[V]** seen on a screen or in a log, **[S]** Charlie said it, **[I]** inference.

Companion docs: `docs/td-h9-app-field-reference.md` (fast field guide), `docs/td-h9-odmaster-aprs-messaging-bug.md` (backstory), `docs/aprs-2m-graywolf-reference.md` (K2GIA-1 station).

## BLUF
- KISSLink v0.5.3 **came up with its identity fields back at defaults** on Oct 28: Settings > Source callsign `NOCALL`, SSID `0`, digipeater path empty, and IS tab > APRS-IS callsign `NOCALL`, passcode empty. Anything sent in that state goes out as `NOCALL`. **Check these before every first send, especially after an app update.**
- With `K2GIA` / `7` / `WIDE1-1,WIDE2-1` saved, the TD-H9 reached Graywolf both ways: over RF (heard "RF Direct" by K2GIA-1) and over the internet (APRS-IS), and the internet send was ACKed within the same second.
- Also proved the same evening: K2GIA-1 transmits and receives again after the Digirig audio fault (see `todos.md`, Oct 28 entry).

## Known-good values for K2GIA-7
| Where | Field | Value |
|---|---|---|
| Settings > Beacon Identity | Source callsign | `K2GIA` |
| | Source SSID | `7` |
| | Destination callsign (tocall) | `APKJH2` (app's own id, not a recipient; leave) |
| | Destination SSID | `0` |
| | Digipeater path | `WIDE1-1,WIDE2-1` |
| IS tab > Server login | APRS-IS server / port | `rotate.aprs2.net` / `14580` |
| | APRS-IS callsign | `K2GIA-7` |
| | APRS-IS passcode | `16025` (computed from base callsign `K2GIA`) |
| | APRS-IS filter | blank |
| | Upload RF-heard packets to APRS-IS | unchecked (normal) |
| Control | Device to select | `TD-H9-7867(BLE)` (MAC `A8:BE:13:BC:17:B0`) |

## Screen by screen

The header shows the app name and version, with a subtitle that changes per tab (Control: "Industrial BLE console"; Settings: "Protocol parameters"; Msgs: "Two-way APRS messaging"; IS: "APRS-IS companion"). Under it, a green banner and two chips: **"Operational: RF/KISS ready"** (it gains **" · APRS-IS connected"** once the IS tab is connected), **BLE: READY** and **Proto: READY**. All green is required before anything works. Tabs: CONTROL, LOG, SETTINGS, APRS, MSGS, IS, MAP.

### CONTROL tab [V] ([screenshot](images/kisslink-2026-10-28/01-control-tab.jpg))
**Radio Link**: scan, select and attach to a BLE KISS device.
- *Selected Device* box: name, MAC, last RSSI (seen: `TD-H9-7867(BLE)`, `A8:BE:13:BC:17:B0`, -53 dBm). Tap to change.
- *Scan Results*: count of BLE devices found (12 that evening), with an optional regex filter (blank = show all; matches name, MAC and services).
- Buttons: **Scan / Select**, **Stop Scan**, **Connect**, **Disconnect**.
- *Last device* line, **Start Last** (reconnect to the last device that completed BLE discovery), **Auto-start last** checkbox (only runs when enabled).
- Only one app can hold the radio's Bluetooth link at a time (KISSLink or TD-H9 APRS Messenger).

**Advanced BLE KISS Profile**: button "Show Advanced BLE Profile". For unknown radios, forces RX/TX GATT service and characteristic UUIDs. Leave blank for auto-detect (TD-H9 auto-detects fine).

**KISS TNC**: selected data path, beacon transmission and received frames, with TX PATH and RX PATH counters (below the fold in the capture; per the field guide, the first troubleshooting stop).

### SETTINGS tab [V] (screenshots: [top](images/kisslink-2026-10-28/02-settings-top-protocol-and-write-options.jpg), [Beacon Identity at defaults](images/kisslink-2026-10-28/03-settings-beacon-identity-defaults-NOCALL.jpg))
**Protocol Parameters**: "BLE scan regex filter, timing values, and write behavior for the BLE KISS transport."
- BLE device filter: placeholder "Blank = all; use H9, RT-950, direwolf|tnc". Matches anywhere in name, MAC or service UUIDs; use `H9` rather than `*H9*`. Optional.
- After connect (before discovery): `600` ms. After service discovery: `300` ms. Defaults, leave.

**Write Options**:
- Write-with-response: **unchecked** (unchecked = write command; TD-H9 uses write-without-response).
- KISS TX port (0-15): `0` (only for multi-port TNCs).
- [OPTIONAL] Enable FF01 notifications: **unchecked**.

**Beacon Identity**: AX.25 source, destination and path parameters.
- Source callsign (1-6 chars), Source SSID (0-15), Destination callsign (tocall), Destination SSID (0-15), Digipeater path ("e.g. WIDE1-1,WIDE2-1 or empty"; shows `(no path)` when empty). Values in the table above.

**Display**: Dark mode checkbox. Then **Save Settings**, which must be tapped after any change.

### MSGS tab [V] (screenshots: [path shows WIDE2-2](images/kisslink-2026-10-28/04-msgs-tab-rf-path-wide2-2.jpg), [ready to send](images/kisslink-2026-10-28/05-msgs-tab-ready-to-send-rf.jpg), [APRS-IS send grayed out](images/kisslink-2026-10-28/08-msgs-tab-aprs-is-send-grayed-out.jpg), [message state cards](images/kisslink-2026-10-28/10-msgs-tab-message-state-acks.jpg))
- Note at the top: "The message path below is local to this page. It does not change the saved beacon/experimental transmit path in Settings." The Msgs path box can therefore show a different value from Settings (it showed `WIDE1-1, WIDE2-2` once). The space after the comma is the app's own formatting.
- **Send method**: RF (default) or APRS-IS. APRS-IS "sends as a client-originated TCPIP* packet for this app's configured callsign. The app does not gate APRS-IS messages to RF." **Send Message is grayed out until the IS tab is connected.**
- **Message destination**: the recipient callsign-SSID (e.g. `K2GIA-1`).
- **Message digipeater path**: buttons **Use Saved Path** (pulls the Settings path) and **Direct** (no path).
- **Message text**, **Request ACK / retry when appropriate** (checked; queries starting with `?` and group addressees ALL, QST or CQ go out without message numbers or ACK requests).
- Buttons: **Send Message**, **Cancel Pending**, **Clear**.
- **Conversation / message state**: "ACKs and REJs are matched to outbound message numbers. Numbered inbound messages addressed to this station are ACKed automatically."
- **Show all heard APRS messages** (unchecked): also shows other stations' message, ACK and REJ traffic, display-only, never auto-ACKed.
- The log box starts as "[idle] no APRS messaging traffic yet".

**Reading the message cards** (screenshot 10): each card is `OUT` (what you sent) or `ACK` (what came back), with a status (`ACKNOWLEDGED`, `CANCELLED`), `msg #nnn`, `tx attempts n`, `via RF` or `via APRS-IS`, and the path plus the raw packet text (`:K2GIA-1  :text{003`, where `{003` is the message number).

### IS tab [V] ([screenshot](images/kisslink-2026-10-28/09-is-tab-disconnected-nocall.jpg))
**APRS-IS Companion**: "Internet APRS receive/display plus optional RF-heard upload. When connected, APRS-IS runs as a foreground service so Android keeps the TCP session alive in the background. This panel does not create general internet-to-RF gating." A status chip (`disconnected`) and a status line.
- **Server login**: APRS-IS server, Port, APRS-IS callsign, APRS-IS passcode (placeholder "issued passcode"), APRS-IS filter (placeholder "e.g. m/100 or r/43.4/-80.5/100").
- **Upload RF-heard packets to APRS-IS** (unchecked): when enabled, only packets actually received through the RF/KISS path are uploaded; "APRS-IS packets are never automatically retransmitted over RF."
- Buttons: **Save**, **Connect**, **Disconnect**, then a "Last APRS-IS line" box.
- After saving valid values and tapping Connect, the main banner reads "Operational: RF/KISS ready · APRS-IS connected".

## The Oct 28 test (times: app local EDT; Discord text shows UTC, 4 h ahead)
| App time | Msg | How | Result |
|---|---|---|---|
| 20:05:29 | #001 | RF, WIDE1-1,WIDE2-1, **sent as NOCALL** (settings at defaults) | `ACKNOWLEDGED`, 1 attempt; ACK from K2GIA-1 at 20:05:33, "via RF, path direct", addressed to NOCALL. Discord #aprs-rf-nj showed "RF Direct ... From: NOCALL To: K2GIA-1 ... Via: WIDE1-1 WIDE2-1" and a second copy "Via: APRS-IS" [V] ([screenshot](images/kisslink-2026-10-28/06-discord-aprs-rf-nj-from-nocall.jpg)). |
| 20:10:43 | #002 | RF, after saving `K2GIA`/`7` | Discord #aprs-rf-nj: "RF Direct ... **From: K2GIA-7** To: K2GIA-1" plus a second copy via APRS-IS [V] ([screenshot](images/kisslink-2026-10-28/07-discord-aprs-rf-nj-from-k2gia-7.jpg)). In the app the card is `CANCELLED`, 2 tx attempts, **no ACK recorded** [V]. |
| 20:15:10 | #003 | APRS-IS (after fixing the IS tab callsign/passcode and connecting) | `ACKNOWLEDGED`, 1 attempt; ACK "via APRS-IS, path TCPIP*,QAC,T2PANAMA" in the same second [V]. Discord **#aprs-internet-nj**: "Internet Message ... From: K2GIA-7 To: K2GIA-1 ... Via: APRS-IS" at 8:15 PM [V] ([screenshot](images/kisslink-2026-10-28/11-discord-aprs-internet-nj-from-k2gia-7.jpg)). |

What it proves: K2GIA-1 hears the TD-H9 over RF (direct), K2GIA-1's transmitter reached the TD-H9 for #001's ACK, and K2GIA-1's iGate receives APRS-IS messages addressed to it and answers over APRS-IS.

## Gotchas found
1. **Identity fields reset to defaults** (Settings and IS tab). Symptom: `From: NOCALL` in Discord, and APRS-IS Send grayed out. Fix: set the values in the table, tap **Save Settings** (Settings) and **Save** (IS), then Connect. [V]
2. **Msgs path box is page-local**; tap Use Saved Path after fixing Settings. It once showed `WIDE1-1, WIDE2-2` (wrong last digit). [V]
3. **APRS-IS send is gated on the IS connection**: no connection, no Send button. [V]
4. **Discord channels**: RF traffic goes to **#aprs-rf-nj**, internet traffic to **#aprs-internet-nj**. A packet may appear twice in #aprs-rf-nj (RF copy, then an APRS-IS copy of the same message). [V]; why the second copy appears is not confirmed [I: the upload of Graywolf's own iGate coming back].
5. The message text on #003 said "K2GIA-2" while the destination was K2GIA-1; only the destination field matters. [V]
6. One app at a time holds the TD-H9's BLE link. [per field guide]

## Open items
- #002 shows no ACK in the app although Graywolf received it (Discord proves that). Unknown whether Charlie cancelled it before the ACK, the ACK was not heard by the TD-H9, or the app missed it. Worth one clean retest over RF with nothing cancelled. [I]
- Why the identity fields reset (app update vs cleared settings) is unknown. [I]
- Not yet tested in this session: the APRS and MAP tabs, the LOG tab, and the KISS TNC dashboard counters.
