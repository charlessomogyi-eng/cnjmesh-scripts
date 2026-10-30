# CJG1 settings capture (Oct 30 2026)

CJG1 = "Central Jersey GW1 | cnjmesh.me (MQTT)", Heltec V4, node `!0aca423c`, 10.0.0.18. Feeds **cnjmesh2** (anonymous). Also the TCP target (port 4403) for meshing-around on cnjmesh1. Settings had never been recorded before this date.

Source: [V] Charlie's screenshots of the Meshtastic web client (client.meshtastic.org, Settings, Radio Config) on Oct 30 2026, 7:03-7:05 PM ET, laptop over USB. Read-only; nothing was saved or changed. Firmware version: not yet read.

## Radio Config, LoRa tab [V screenshots]

| Setting | Value | Note |
|---|---|---|
| Region | US | |
| Hop Limit | **7** | Default is 3, 7 is the maximum. No record that this was deliberate. CJG1 originates the 7 AM report and NWS alerts, so those floods go up to 7 hops. NYME-sh also runs 7 on some nodes (docs/nyme-sh-summary.md). Decide on purpose. |
| Frequency Slot | 0 | Slot derived from the primary channel's name. Gives the normal Long Fast frequency only if channel 0 is named LongFast. Check on Channels tab. |
| Ignore MQTT | off | Default. |
| OK to MQTT | on | Needed for our uplink to be accepted. |
| Use Preset | on | |
| Modem Preset | Long Fast | Bandwidth 250 kHz, SF 11, CR 5 (greyed, derived from the preset). |
| Transmit Enabled | on | |
| Transmit Power | **30 dBm** | Meshtastic docs: 0 means "default max legal continuous power". A manual 30 is not the default. Not verified what firmware does with 30 on a V4. One MeshCore measurement says the V4 hardware cannot reach 30 dBm at 915 MHz regardless of setting (MeshCore issue 1708, different firmware). Candidate to set to 0 once reviewed; no record of who chose 30. |
| Override Duty Cycle | off | |
| Frequency Offset | 0 Hz | |
| Boosted RX Gain | on | |
| Override Frequency | 0 MHz | Not overriding. |
| FEM/LNA Mode | [?] not captured yet | V4 has a front-end module. |
| Serial HAL Only | [?] not captured yet | |

## Still to capture
Channels tab (names, roles, uplink/downlink, key first and last characters only), Security tab (public key only; never the private key), Device Config (Device, Network, Position, Bluetooth), Module Config (MQTT, Telemetry, Serial), firmware version.
