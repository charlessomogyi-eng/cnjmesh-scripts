# CJG1 settings capture (Oct 30 2026)

CJG1 = "Central Jersey GW1 | cnjmesh.me (MQTT)", Heltec V4, node `!0aca423c`, 10.0.0.18. Feeds **cnjmesh2** (anonymous). Also the TCP target (port 4403) for meshing-around on cnjmesh1. Settings had never been recorded before this date.

Source: [V] Charlie's screenshots of the Meshtastic web client (client.meshtastic.org, Settings, Radio Config) on Oct 30 2026, 7:03-7:05 PM ET, laptop over USB. Read-only; nothing was saved or changed. Firmware: updated by Charlie to **2.7.26.54e0d8d** the same evening (see Update record below).

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

**CentralNJ** [V screenshots 7:09 PM]: Role SECONDARY. Name `CentralNJ`. Key length 256 bit; **Key revealed 7:10 PM [V screenshot]: reads `f+WQoPgd06tk0n3K?2bUmNVGO7TcPkxchPD6QqMkYRg=`, same length and every character matches the published key except one that the web client's font shows as I or l (published has lowercase l).** **Confirmed 7:10 PM [V, Charlie pasted the key from the copy button]: exactly equal to the published key (checked by string comparison against the repo copy). CJG1's CentralNJ key is correct.** **Uplink on, Downlink on.** Location precision: "Within 15 miles" (coarser than KPN6, which shares precise position on CentralNJ).

**Leftover channels** (CNJTest, KPCOMMS, KPTESTING, CentNJ-MQTT) [S, Charlie 7:11 PM]: left over from experimenting. Uplink/downlink state not captured. Candidate for later cleanup, not during a firmware update. Check that none has downlink on.

**SJMesh channel ADDED by Charlie Oct 30 7:15-7:17 PM** [V screenshots before and after save]: slot Ch 6, Role SECONDARY, Name `SJMesh`, 128-bit key `0DXa/9pTEZURzZ9sWEHOWg==` (from the Aug 9 session log, shared by the SJMesh admin in Discord; not yet compared with CJG2's or KPN6's copy), Uplink on, Downlink off, Location within 15 miles. Reopened after the save and it persisted. Purpose: "to have", since CJG1 is hard to reach. Effect: SJMesh packets heard by CJG1 now upload to cnjmesh2 only (it carries no SJMesh bridge, so they stay local, visible in cnjmesh2's Malla); nothing reaches SJMesh's broker from here. CJG1 had no SJMesh channel before this.

## Device Config, Position (partial) [V screenshot 7:18 PM]

GPS Mode NOT_PRESENT. **Fixed Position on.** Latitude is entered as `40.4` (one decimal place, so it looks rounded or truncated); longitude has six decimals. The exact coordinates are deliberately not written in this public repo. **Intervals [V screenshot 7:24 PM]:** Broadcast Interval 3600 s (hourly), GPS Update Interval 120 s (irrelevant, no GPS), Smart Position Minimum Distance 100 m and Minimum Interval 300 s (greyed out, so smart broadcast is off). Someone told Charlie he might be broadcasting too often. Assessment: hourly is not aggressive for a fixed node (about 24 small packets a day). Arizona Mesh's recommended settings page suggests 43200 s (12 h) for stationary nodes, device metrics 3600 s, node info 43200 s, map report 21600 s [V, azmsh.net/docs/recommended-settings.html Oct 30]. I believe the firmware default is 900 s but did not confirm it today [?]. Hop limit 7 multiplies the cost of every broadcast more than the interval does. **Changed by Charlie Oct 30 7:27 PM: Broadcast Interval 3600 -> 43200 s** [V screenshot shows 43200; Charlie confirmed at 7:28 PM that he saved it]. In 2.8, position and telemetry are turned off after the upgrade anyway.

Still not captured: the top of the Position page (position flags) and the rest.

## Module Config, MQTT [V screenshots 7:20 PM]

| Setting | Value | Note |
|---|---|---|
| Enabled | on | |
| MQTT Server Address | `10.0.0.91` | = cnjmesh2 (Pi Zero 2 W), per cnjmesh1-operations.md. |
| MQTT Username | `meshdev` | cnjmesh2's Mosquitto has `allow_anonymous true`, so the login is ignored there. |
| MQTT Password | set (masked, 10 characters, not recorded) | |
| Encryption Enabled | **on** | Same as CJG2; KPN6 has it off. |
| JSON Enabled | on | JSON is removed from 2.8 firmware builds (see 2.8 plan); harmless on 2.7. |
| TLS Enabled | off | Local plain MQTT on port 1883. |
| Root topic | `msh/US` | |
| MQTT Client Proxy | off | CJG1 reaches the broker by its own Wi-Fi. |
| Map Reporting | on | Reports go to cnjmesh2's broker. |
| Map Report Publish Interval | 3600 s | KPN6 publishes every 3 hours. |
| Approximate Location (map report precision) | within 1.8 miles [V 7:21 PM] | Same as KPN6. |
| Map-reporting consent ("I agree") toggle | [?] not shown by the web client's page | The page ends at Approximate Location. Check in the Android app if it matters. |

Nothing here conflicts with what the repo records for CJG1 (feeds cnjmesh2, anonymous).

## Still to capture
Channels tab detail for CentralNJ, CNJTest, KPCOMMS, KPTESTING, CentNJ-MQTT (role, name, uplink, downlink, location; CentralNJ key against the published one), Security tab (public key only; never the private key), Device Config (Device, Network, Position, Bluetooth), Module Config (MQTT, Telemetry, Serial), firmware version.

## Update record (Oct 30 2026, evening)

- Charlie flashed CJG1 (Heltec V4) with the Web Flasher over USB, update option, stable 2.7.26. Before the flash the version was **not read**; the repo's July 13 entry says it was `2.7.24.472b14c` at that time [I, probably unchanged].
- **Version after flash: 2.7.26.54e0d8d [V, meshing-around's own telemetry line on cnjmesh1, 7:33 PM and 7:43 PM, `Firmware:2.7.26.54e0d8d`].** Uptime 11 min at 7:43:53 PM, so it booted about 7:32 PM.
- **meshing-around recovered by itself [V, `journalctl -u mesh_bot.service`]:** at 7:31:25 PM "timed out waiting for an acknowledgment", 7:31:45 PM broken pipe, 7:32:00 PM "Retrying Interface1 TCP on hostname: 10.0.0.18", 7:32:01 PM "Interface1 Opened!", then normal telemetry at 7:33:43 and 7:43:53 PM (totalNodes 250, Online 18). The 7 AM schedule is intact (next run Oct 31 07:00). No restart of `mesh_bot.service` was needed.
- Not yet re-checked after the flash: channels, MQTT settings, region/preset (should be unchanged; no full erase was used).

## App connectivity symptom (Oct 30 7:36-7:44 PM) [S, Charlie]
Over Network (10.0.0.18) the Android app connects for about 3 seconds, drops, waits a long time, connects again for 3 seconds, repeating. He says this happens only for the app. Hypothesis: the firmware allows one TCP client at a time (firmware issues 3618 and 7582 describe a force-close of the previous connection and clients fighting), and meshing-around holds a permanent TCP connection to 10.0.0.18:4403. Weak counter-evidence: the bot's log shows no reconnect events between 7:32 and 7:44 PM and its 7:43:53 PM poll succeeded, though the bot only notices a lost socket when it next sends. Decisive test (not yet run): stop `mesh_bot.service` on cnjmesh1, connect the app, then start the bot again.
