# CNJ Mesh node inventory (Meshtastic and MeshCore), Nov 1 2026

Compiled from the repo (cnjmesh1-operations.md, docs/meshtastic-2.8-upgrade-plan.md, todos.md, session-log.md) plus Charlie's statements on Nov 1 2026. [V] = from repo/Charlie, [?] = not confirmed. This is a lookup table, not a replacement for the detailed docs.

## Meshtastic (in service)

| Name | Hardware | Node ID | Where / role | Firmware (Oct 30) |
|---|---|---|---|---|
| CJG1 | Heltec V4 | `!0aca423c` | 10.0.0.18, Wi-Fi, uploads to cnjmesh2; meshing-around bot uses TCP 4403 | 2.7.26.54e0d8d |
| CJG2 | Heltec V3 | `!9ea3e8d4` | 10.0.0.234, Wi-Fi, uploads to cnjmesh1; CentralNJ + SJMesh up/down | 2.7.26.54e0d8d |
| KPN6 | Heltec V4 (Client Base) | `!69841fe0` | Roof antenna, Wi-Fi 10.0.0.202, also USB to cnjmesh1 (/dev/ttyACM1) | 2.7.25.104df5f |

Not Meshtastic but easy to confuse: K2GIA-10 (CA2RXU LoRa APRS iGate, 10.0.0.74) and K2GIA-9 (LoRa APRS tracker board).

## Meshtastic (retired, still visible in the node list)

| Name | What it was | What it is now |
|---|---|---|
| KPN2 | LilyGo T-Deck Plus (`!4ecec314`, last heard Aug 7) | Flashed to MeshCore, now **KPC2** |
| KPN1 | RAK4631 solar outdoor node | Flashed to MeshCore, now **KPR3** |
| KPN7 | Heltec V4 used to test a Yagi (`!0ac9deb4`, last heard Jul 4) | Flashed to MeshCore [Charlie, Nov 1]. **Its MeshCore name is not recorded anywhere in the repo [?]** |

Old Meshtastic entries stay in the app and map until they age out; they do not mean the hardware is lost.

## MeshCore

| Name | Hardware | Pubkey (start) | Where / role | Radio |
|---|---|---|---|---|
| Observer | WisMesh Pocket Mini (RAK4631) | A8C40BF3 | cnjmesh3, 2nd floor, feeds letsmesh + CoreScope | 500 kHz since Oct 13 |
| KPR1 | Heltec V3 repeater | 0acd65fb | Garage, small antenna, cnjmesh1 (Tilly/LVMesh integration). Repo disagrees on retired vs active; todos.md and Charlie say active [?] | 62.5 kHz (last one) |
| KPR2 | Heltec V4 repeater | 977f8ae4 | cnjmesh3, 2nd floor, Alfa antenna | 500 kHz since Oct 14 |
| KPR3 | RAK4630 + RAK19003, solar (ex-KPN1) | 29dda9e3 | Backyard, 13 ft mast, 9-element Yagi | 500 kHz since Oct 11 |
| KPC1 | Heltec V3 companion (CNJWeatherBot) | not recorded | cnjmesh1 /dev/kpc1, garage | 500 kHz since Oct 14 |
| KPC2 | LilyGo T-Deck Plus (ex-KPN2) | e14166b8 | Charlie's personal companion, moves around the house | 500 kHz since Oct 11 |
| KPC3-Bot | T096 (Heltec) + Alfa antenna | n/a | Planned test bot (agessaman/meshcore-bot) next to cnjmesh3. Not confirmed built [?] | n/a |

Radio for the 500 kHz set: 910.525 MHz, BW 500, SF10, CR5.

## Open questions
- Which MeshCore node is the old KPN7 Heltec V4? KPR2 is also a Heltec V4 but the repo has no link between the two.
- KPR1 status (retired vs active).
- Three Heltec V3 boards arriving by mail for Meshtastic (stated Nov 1). Planned names not set; KPN2 and KPN7 are free names.
