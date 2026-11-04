# Meshtastic 2.8 and Long Turbo, explained (Nov 3 2026)

Written the evening of Tue Nov 3 2026 for Charlie (K2GIA) when he flashed a new Heltec V3 (**KPN9**) with a 2.8 build. This is a plain-language companion to `docs/meshtastic-2.8-upgrade-plan.md` (the gateway upgrade plan, written Oct 30). Nothing here touched a Pi, broker or gateway.

Tags: [V] verified on a page I read · [S] single/secondary source · [?] not verified.

---

## 1. Bottom line

1. **2.8 is still not stable.** 2.8.0 was pulled (startup bug), then revoked (packet-signing flaw). 2.8.1 was Alpha. The newest tag I could read, v2.8.2.4c89b69 (Nov 2), is labeled **Alpha / Pre-release** on GitHub [V]. A later tag (v2.8.2.d5f1619, Nov 3) exists; its label is [?]. Latest **stable** is 2.7.26 [S, NoDak]. 2.7 and 2.8 nodes can talk to each other [S].
2. **A fresh US node set up from its own screen defaults to Long Turbo, which cannot hear Long Fast.** CNJ Mesh is on Long Fast. A new KPN9 on the default will hear nothing from us until it is switched. The Meshtastic docs still say a factory reset gives LongFast [V], so the Turbo default is a setup-flow behavior, not a firmware-wide default [S].
3. **The node ID now comes from the public key, not the MAC.** Charlie's "last few digits of the key" is close in spirit but not literally right: sources say the node number is `crc32(public_key)`, a checksum of the 32-byte key [S: MeshMonitor, meshflow-api #439, Camillia #60]. Which exact bytes become the `!xxxxxxxx` text, and how the default short name relates, I could not confirm [?]. Best check: read KPN9's ID and short name in the app and compare after a key regeneration.

---

## 2. Long Turbo vs Long Fast

Official presets table (meshtastic.org radio settings) [V]:

| Preset | Bandwidth | SF | Coding rate | Data rate |
|---|---|---|---|---|
| Long Fast | 250 kHz | 11 | 4/5 | 1.07 kbps |
| **Long Turbo** | **500 kHz** | 11 | **4/8** | 1.34 kbps |
| Long Moderate | 125 kHz | 11 | 4/8 | 0.34 kbps |
| Medium Fast | 250 kHz | 9 | 4/5 | 3.52 kbps |
| Medium Turbo | 500 kHz | 9 | 4/5 | 7.03 kbps |
| Short Fast | 250 kHz | 7 | 4/5 | 10.94 kbps |
| Short Turbo | 500 kHz | 7 | 4/5 | 21.88 kbps |

New narrow presets (Lite Fast/Slow, Narrow Fast/Slow, Tiny Fast/Slow) exist for certain regions; Turbo presets are unavailable in EU_868 and in the narrowband regions [V].

US defaults [S, NoDak]: Long Fast = 906.875 MHz, slot 20 of 104. Long Turbo = **908.750 MHz, slot 14 of 52**. Different bandwidth **and** different frequency means the two presets cannot hear each other. The frequency slot is derived from the channel name hash [S]; the docs page I read did not explain the hash [?].

Costs and benefits [S]: doubling bandwidth costs about 3 dB of receive sensitivity (less range) and shortens airtime roughly 25 to 40 percent. Stated reason for the change: FCC Part 15.247's 500 kHz minimum for full-power operation in 902 to 928 MHz.

**When the Turbo default hits** [S]:
- New or freshly erased US node, region set from the **device screen**: Long Turbo.
- Android app 2.8.3 first-time setup: same. iPhone app 2.7.25: not [S].
- Meshtastic CLI setup: stays Long Fast.
- Upgrade from 2.7: keeps the existing preset.
- The Camillia ticket notes the screen change is menu-only and "a pinned userpref or a moved preset outranks it" [V on that page; the "cannot hear each other" analysis is the ticket's own and untested on hardware].

**Check which preset a node is on:** device screen (Turbo shows 908.750 MHz / 500 kHz), or `meshtastic --get lora`.
**Switch to Long Fast (what CNJ uses):** app: Radio configuration, LoRa, Region US, Modem preset Long Fast. CLI: `meshtastic --set lora.region US --set lora.modem_preset LONG_FAST`. LoRa changes apply without a reboot in 2.8 [S].

---

## 3. Node ID change

- Before: the node number came from the MAC address. In 2.8 it is `crc32(public_key)` [S: MeshMonitor identity page; meshflow-api #439 cites `NodeDB.cpp:543`; "crc32 of the 32-byte key"].
- The keypair and the long/short names are unchanged on upgrade, but the **number and `!hex` ID change on first 2.8 boot, and downgrading does not restore the old number** [S].
- A new key means a new ID: erase, factory reset or key regeneration changes the ID [S: Meshtastic security page, docs PR #2732].
- A node with no public key keeps its MAC-derived number until keys exist; on a fresh device keys are created once the LoRa region is set [S].
- NodeInfo's MAC field now shows all zeros for other nodes [S].
- Hardening in 2.8.2: spoofed own-node-number packets are rejected (#12270) [V]. Signed first-contact NodeInfo must have `crc32(public key) == sender's number` [S].
- **Unverified:** truncation, CRC variant, mapping to the `!xxxxxxxx` text and default short name [?]. meshflow-api's example `!da545c78 -> !4396524c` is marked unverified by its own author.

Tool impact [S]: history splits across old and new numbers, ghost entries appear, anything keyed to the old ID (favourites, MQTT topics, dashboards, our relay allowlist) goes stale. See upgrade plan section 4.

---

## 4. Other 2.8 changes

- **Packet signing (XEdDSA)** with policies Compatible (default), Balanced, Strict. In 2.8.2 the policy changed again: in Compatible mode nodes no longer sign packets and AES-CCM takes precedence; Strict gains exemptions; the release says to review signing settings after updating [V]. Ham mode refuses key verification [V].
- Position and telemetry broadcasts **off by default**, including after upgrade. Precise position is not sent on public channels (about 729 m cap) [S].
- Long names capped at 24 bytes (was 39) [S].
- NodeDB rebuilt (records 196 to 112 bytes, warm tier; favorites, ignored and verified nodes never evicted) [S]. Filesystem format changed: expect to reconfigure; after a bootloop, full erase and flash, then restore config. **Back up the config first** [S].
- New presets (above); Ham Mode with 2 m, 1.25 m and 70 cm regions; receive-only mode; automatic hop-limit reduction (traffic management) [S].
- Pre-hop drop on by default: packets with `hop_start < hop_limit` are dropped before decryption; very old firmware that does not set hop info is not relayed [S: Camillia #60].
- JSON library removed from firmware builds [S]. Removed: nRF52832 target, UA_868 region, ATAK unishox2 compression [S].
- 2.8.2 (alpha) adds: MQTT gateways now uplink PKI DMs they relay but cannot decrypt (still end-to-end encrypted, #12110); smarter Listen Before Talk; new boards. Bug fixes include an ESP32 light-sleep crash and a Store & Forward crash [V].
- Android app 2.8.3 needs firmware 2.5.14 or newer [S].

---

## 5. What this means for CNJ Mesh

- **KPN9 (new V3, 2.8 build):** set it to US / Long Fast by hand. Until then it is on an island. Record its firmware tag, its new `!ID`, and whether it came up on Turbo. Keep it off the CentralNJ MQTT uplink and public bridging until we know what it publishes (the 2.8.2 MQTT path is still being fixed).
- **Gateways (CJG1, CJG2, KPN6) stay on 2.7.x.** The Oct 30 plan stands: wait for a **Beta**, two quiet weeks, Malla/Meshview/MeshMonitor ready, then bench, then one at a time. KPN9 can serve as an early bench node for Phase 1 if it stays off the bridged channels.
- Hard-coded IDs that would break on a gateway upgrade: `sjmesh-relay` allowlist `!9ea3e8d4,!69841fe0,!0aca423c`, blocked flood nodes, Malla/Meshview history, JSON uplink topic. All in the upgrade plan.
- Website: `getting-started.html` has a new "Setting up on Meshtastic 2.8" section in the repo (held for the weekend combined deploy; NOT live).

---

## 6. Things to test on KPN9 (cheap, answers the [?] items)

1. Which preset did it come up on, and how did you set the region (screen or app)?
2. Note the `!ID` and short name before and after a key regeneration to see how they relate.
3. Does it hear CNJ Mesh after switching to Long Fast?
4. Does a config export contain the key? (never commit one)

---

## 7. Sources

- Meshtastic, "Let's talk about 2.8" (Oct 8 2026): https://meshtastic.org/blog/lets-talk-about-2-8/
- Meshtastic radio settings (presets table): https://meshtastic.org/docs/about/overview/radio-settings/
- Firmware v2.8.2.4c89b69 release (Alpha): https://github.com/meshtastic/firmware/releases/tag/v2.8.2.4c89b69
- NoDak Mesh, 2.8 and LongTurbo vs LongFast: https://nodakmesh.org/blog/meshtastic-2-8-whats-new and https://nodakmesh.org/blog/meshtastic-longturbo-vs-longfast
- MeshMonitor, node number changes: https://meshmonitor.org/features/node-identity-changes.html
- meshflow-api #439: https://github.com/pskillen/meshflow-api/issues/439
- Camillia 2.8 ticket: https://github.com/oumike/camillia-mt/issues/60
- Docs PR #2732 (encryption/security pages for 2.8): https://github.com/meshtastic/meshtastic/pull/2732
- Android PR #7244 (Turbo on fresh US setup): https://github.com/meshtastic/Meshtastic-Android/pull/7244
