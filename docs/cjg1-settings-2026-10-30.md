# CJG1 settings capture (Oct 30 2026)

CJG1 = "Central Jersey GW1 | cnjmesh.me (MQTT)", Heltec V4, node `!0aca423c`, 10.0.0.18. Feeds **cnjmesh2** (anonymous). Also the TCP target (port 4403) for meshing-around on cnjmesh1. Settings had never been recorded before this date.

Source: [V] Charlie's screenshots of the Meshtastic web client (client.meshtastic.org, Settings, Radio Config) on Oct 30 2026, 7:03-7:05 PM ET, laptop over USB. Read-only; nothing was saved or changed. Firmware version: not yet read.

## Radio Config, LoRa tab [V screenshots]

| Setting | Value | Note |
|---|---|---|
| Region | US | |
| Hop Limit | **7** | Default is 3, 7 is the maximum. No record that this was deliberate. CJG1 originates the 7 AM report and NWS alerts, so those floods go up to 7 hops. NYME-sh also runs 7 on some nodes (docs/nyme-sh-summary.md). **Decision Oct 30 7:07 PM [S, Charlie]: keep 7 for now.** |
| Frequency Slot | 0 | Slot derived from the primary channel's name. Gives the normal Long Fast frequency only if channel 0 is named LongFast. Check on Channels tab. |
| Ignore MQTT | off | Default. |
| OK to MQTT | on | Needed for our uplink to be accepted. |
| Use Preset | on | |
| Modem Preset | Long Fast | Bandwidth 250 kHz, SF 11, CR 5 (greyed, derived from the preset). |
| Transmit Enabled | on | |
| Transmit Power | **30 dBm** | Meshtastic docs: 0 means "default max legal continuous power". A manual 30 is not the default. Not verified what firmware does with 30 on a V4. One MeshCore measurement says the V4 hardware cannot reach 30 dBm at 915 MHz regardless of setting (MeshCore issue 1708, different firmware). **Charlie Oct 30 7:07 PM [S]: leaving it; 30 is the maximum the setting allows and he says the node can only do 22 dBm.** The 22 dBm figure is unverified here: the V4 has a front-end amplifier and one MeshCore measurement shows about 27-28 dBm conducted at high settings. Revisit later (0 = firmware default). |
| Override Duty Cycle | off | |
| Frequency Offset | 0 Hz | |
| Boosted RX Gain | on | |
| Override Frequency | 0 MHz | Not overriding. |
| FEM/LNA Mode | [?] not captured yet | V4 has a front-end module. |
| Serial HAL Only | [?] not captured yet | |

## Channels tab [V screenshots, 7:08 PM]

Channel tabs, in order: **Primary, CentralNJ, CNJTest, KPCOMMS, KPTESTING, CentNJ-MQTT, Ch 6, Ch 7**. (Ch 6 and Ch 7 are empty slots.) **There is no SJMesh channel on CJG1**; CJG2 and KPN6 have one. Slot order differs from KPN6's table in docs/meshtastic-gateway-mqtt-settings.md.

**Primary** [V]: Role PRIMARY. Name blank (so it is called LongFast under the Long Fast preset, consistent with Frequency Slot 0 giving slot 20). Pre-shared key shown as 4 dots with the **8 bit** option selected, which is the short default-key form (the same default key every LongFast node uses). **Uplink on, Downlink off** (correct for LongFast: never downlink other regions' traffic onto our RF). Location precision: "Within 1.8 miles".

**CentralNJ** [V screenshots 7:09 PM]: Role SECONDARY. Name `CentralNJ`. Key length 256 bit; **key text was masked, so not yet compared to the published `f+WQoP...`** (this is the check that found CJG2's wrong key on Oct 25). **Uplink on, Downlink on.** Location precision: "Within 15 miles" (coarser than KPN6, which shares precise position on CentralNJ).

Other channels: not captured yet (CNJTest, KPCOMMS, KPTESTING, CentNJ-MQTT).

## Still to capture
Channels tab detail for CentralNJ, CNJTest, KPCOMMS, KPTESTING, CentNJ-MQTT (role, name, uplink, downlink, location; CentralNJ key against the published one), Security tab (public key only; never the private key), Device Config (Device, Network, Position, Bluetooth), Module Config (MQTT, Telemetry, Serial), firmware version.
