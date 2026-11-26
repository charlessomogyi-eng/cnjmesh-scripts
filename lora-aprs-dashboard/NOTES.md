# Notes: verified facts and open items (Nov 25 2026)

## Sources

| What | Version |
|---|---|
| `richonguzman/LoRa_APRS_iGate` | tag V3.2.4, commit `305c5b7` |
| `jgromes/RadioLib` | 7.6.0 |
| `knolleary/PubSubClient` | 2.8 |
| `richonguzman/APRSPacketLib` | 1.0.4 |
| `mikalhart/TinyGPSPlus` | v1.0.3 |
| `espressif/arduino-esp32` (WString) | 2.0.17 |
| Model page | `jonadams.com/rxt/` |

## Verified from the source, and with the compiled firmware code where marked (*)

"Compiled" means the unchanged upstream `syslog_utils`, `mqtt_utils`,
`gps_utils` and `digi_utils` files built for the PC (`tests/harness/`). The
radio, WiFi and network layers are stand-ins. It is not a test on the board.

- (*) Syslog header: `<165>1 - K2GIA-10 CA2RXU_LoRa_iGate_3.2.4 - - - `.
  Received lines end ` / <rssi>dBm / <snr>dB / <freq error>Hz`
  (`syslog_utils.cpp`; called from `lora_utils.cpp`).
- (*) Position lines add ` / <lat>N / <lon>E / <km>km`, then the comment if
  there is one, or ` _ / _ / _ `. South and west stay negative with N and E.
- (*) Message, status, Mic-E, object and telemetry lines have **no path**.
  Position lines containing `WIDE1-1` show only the destination call and
  `WIDE1-1`. Other position lines show the whole path. Other packet types are
  logged raw, including the 3 byte LoRa header.
- (*) `TX / MESSAGE` lines drop the first 3 characters of the sender
  (`K2GIA-10` appears as `IA-10`).
- (*) The MQTT payload is the packet without the LoRa header, on
  `<topic>/<sender>`. A packet is not published if
  5 + 2 + topic length + payload length is over 256 bytes (PubSubClient 2.8).
- Order in one pass of the main loop (`LoRa_APRS_iGate.cpp`): receive and send
  the syslog line, then APRS-IS, then digipeat (only queued, see
  `digi_utils.cpp`), then KISS, then the MQTT publish. Transmitting happens
  later, in `processOutputPacketBuffer`. So both feeds leave the iGate
  milliseconds apart, well inside the 4 second join window. Blacklisted
  stations get neither.
- The iGate's MQTT client ID is its callsign, so nothing else may use that ID.
- (*) A digipeater marks the path with `*`, for example
  `...,N0DIGI-10,K2GIA-10*`, or `K2GIA-10*,WIDE2-1`.
- Packet text ends at the first zero byte, so an RXT binary block never
  reaches syslog or MQTT.
- With "log beacon over TCP/IP" on, the iGate's own internet beacon is logged
  as `RX` with 0 / 0 / 0 (`utils.cpp`). The collector ignores those.
- RadioLib 7.6.0, SX1278 below 868 MHz: packet RSSI is -164 + register, plus
  SNR when SNR is negative.

## Choices made here

- Map positions are the latitude and longitude the iGate itself decoded and put
  in the syslog line, so Mic-E, objects and stations without position packets
  are not placed. Position 0, 0 is ignored. A position belongs to the sender,
  even if the packet came through a digipeater.

- Feeds are joined when the packet text agrees and the arrival times are within
  4 seconds. A MQTT message under the iGate's own callsign only completes a
  syslog record and never creates one.
- Length (for airtime) is exact when MQTT or a raw line gives the whole packet,
  otherwise a lower bound, marked `≈`.
- Noise estimate: total = RSSI - min(SNR, 0), then
  noise = total - 10 log10(1 + 10^(SNR/10)), only for SNR under +8 dB. It is
  derived from the formula above, not calibrated against any measurement.
- Channel load "incl. CRC est.": a CRC error line gives no usable length, so
  each one is counted as the median airtime of good received packets from the
  last 24 hours. With no good packet to go by, no estimate is shown. How the
  model page works this figure out is not known.
- SNR colours: decode limit = -7.5 - 2.5 x (SF - 7) dB; red under limit + 1.5,
  amber under limit + 10.5. At SF7 this gives the model page's -6 and +3.

## Test status

41 tests pass on Python 3.13: parsing, storage, 20,000 random packets compared
with the compiled firmware code, and a full run through a local mosquitto
broker (paho-mqtt 1.6.1 and 2.2.0). All sample packets use placeholder calls
and positions. **No real captured line has been tested.**

## Not yet checked (needs the Pi)

0. Host: cnjmesh3 is planned (K2GIA-10 is moving there); see README.

1. What holds UDP 1514 on cnjmesh1, and whether the Discord bridge runs.
2. Real syslog lines from K2GIA-10, compared with the formats above.
3. That the running firmware still reports 3.2.4 (the page warns if not).
4. K2GIA-10's radio settings: SF12 / BW125 / CR4/5 assumed.
5. Port 8090 free (no use found in the repo docs).
6. How often packets are "Path unknown" in practice.

## Firmware V4 (read from source Nov 26 2026, not built or tested)

Upstream tags go up to V4.0.4. K2GIA-10 runs 3.2.4, so nothing here affects
tomorrow's install, but it matters before any firmware upgrade. Compared
`src/syslog_utils.cpp` at V3.2.4 and V4.0.4 (`src/mqtt_utils.cpp` differs only
in the copyright year):

- RX line shape is the same: `RX / <TYPE> / ... / <rssi>dBm / <snr>dB / <ferr>Hz`.
- MIC-E lines now carry only the indicator character (`` ` `` or `'`) after
  the sender, no packet text. Matching a MIC-E syslog line to its MQTT packet
  by content will fail on V4.
- CRC errors keep the same `CRC / CRC-ERROR / <packet>` line.
- Unrecognized packets log the full uncut packet.
- Position lines are built from parsed fields and the path text may differ
  slightly.

Before upgrading: run `tests/harness/build.sh` against V4.0.4 and rerun
`tests/test_firmware.py`.

From a third-party write-up (hamradio.my, not checked in source): V4.0.0
(Aug 16 2026) changes the transmit defaults to SF9 and CR 4/7, adds channel
activity detection before transmit, and adds a web page with a live map.

## Seen in `lora-aprs-discord-bridge/` (not changed, outside this folder)

Tested the bridge's patterns against lines from the compiled firmware code:

- `RX_MESSAGE_RE` and `TX_MESSAGE_RE` need a single space before the colon, so
  they match only an 8 character addressee. `CQ`, `ANSRVR` and 9 character
  calls such as `N0DIGI-10` do not match.
- The script's "confirmed" `TX / MESSAGE` example shows a full sender call, but
  the 3.2.4 source cuts 3 characters off it. One captured line would settle
  which is right.
