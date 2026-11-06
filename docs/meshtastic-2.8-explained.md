# Meshtastic 2.8 and Long Turbo, explained (Nov 3 2026)

Written the evening of Tue Nov 3 2026 for Charlie (K2GIA) when he flashed a new Heltec V3 (**KPN9**) with a 2.8 build. This is a plain-language companion to `docs/meshtastic-2.8-upgrade-plan.md` (the gateway upgrade plan, written Oct 30). Nothing here touched a Pi, broker or gateway.

Tags: [V] verified on a page I read · [S] single/secondary source · [?] not verified.

---

## 1. Bottom line

1. **2.8 is still not stable.** 2.8.0 was pulled (startup bug), then revoked (packet-signing flaw). 2.8.1 was Alpha. The newest tag I could read, v2.8.2.4c89b69 (Nov 2), is labeled **Alpha / Pre-release** on GitHub [V]. The Nov 3 tag **v2.8.2.d5f1619 is also labeled Alpha** [V, release notes Charlie pasted Nov 4] and is a **re-release of 2.8.2 to fix a stack-exhaustion bug in environmental telemetry**, so it supersedes 4c89b69. This is the build on Charlie's new V3 bench nodes (KPN8 for sure; KPN9 to confirm). Latest **stable** is 2.7.26 [S, NoDak]. 2.7 and 2.8 nodes can talk to each other [S].
2. **Long Fast is still the normal default. Long Turbo applies in one setup path.** Meshtastic's 2.8 docs say a new node's preset is "Long Fast, or Long Turbo when the region is first set to US on the device screen"; setting the region "from a client or the CLI leaves it on Long Fast" [V: docs "Joining your local mesh" and blog "Finding your local mesh"]. The blog adds that two identical nodes set up the same day can end up almost 2 MHz apart. Turbo cannot hear Long Fast (different bandwidth and frequency), so a screen-set node on the default will not hear CNJ Mesh. Earlier sources (NoDak, Android PR #7244) said the Android app 2.8.3 also picks Turbo for fresh nodes; the official docs say clients leave Long Fast, so treat the Android claim as [?] until tested. **First-hand test, Nov 6 2026 [V, Charlie]:** a fresh 2.8 flash (2.8.2-series alpha) on a Heltec V3 came up on **Long Fast** before the region was set and stayed on Long Fast after he set the region to US **from a client** (not on the device screen). He configured the first node (KPN9) from the laptop client config GUI and the second (KPN8) from the Android app, because the laptop GUI would not save his changes. Which node the first-boot observation was about is still to be confirmed [?]. Either way, a client-set region did not pick Turbo. KPN9 is on **Long Turbo** (Charlie's choice, for testing).
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

**When the Turbo default hits** [V, official docs]:
- Region set to US for the first time on the **device screen**: Long Turbo.
- Region set from a phone app or the CLI: Long Fast. Factory reset: LongFast per the radio-settings page. Upgrade from 2.7: keeps the existing preset.
- Older sources said Android app 2.8.3 first-time setup picks Turbo. Not confirmed by the official docs, and **not borne out by Charlie's Nov 6 test** (fresh flash, region set to US from a client, stayed on Long Fast; whether that was the laptop client or the Android app is still to be confirmed, app version not recorded). The device-screen path was not tried: the screen is tiny and he does not use it.
- The Camillia ticket notes the screen change is menu-only and "a pinned userpref or a moved preset outranks it".

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
- 2.8.2 (alpha; re-released as d5f1619 on Nov 3 to fix an environmental-telemetry stack-exhaustion bug) adds: MQTT gateways now uplink PKI DMs they relay but cannot decrypt (still end-to-end encrypted, #12110); smarter Listen Before Talk; new boards. Bug fixes include an ESP32 light-sleep crash and a Store & Forward crash [V].
- Android app 2.8.3 needs firmware 2.5.14 or newer [S].

---

## 5. What this means for CNJ Mesh

- **KPN9 (new V3, 2.8 build):** set to **Long Turbo** on purpose (Nov 3), so it will NOT hear CNJ Mesh (Long Fast). Charlie set a fixed position at Kendall Park town-center level (40.42, -74.56, not his house), enabled Wi-Fi access, and left it to sit for 48 hours (Nov 3 9:44 PM to about Nov 5 9:44 PM). During that window it only hears other Turbo nodes, so an empty node list means no Turbo nodes in range, not no mesh. Keep it off MQTT/CentralNJ.
- **Gateways (CJG1, CJG2, KPN6) stay on 2.7.x.** The Oct 30 plan stands: wait for a **Beta**, two quiet weeks, Malla/Meshview/MeshMonitor ready, then bench, then one at a time. KPN9 can serve as an early bench node for Phase 1 if it stays off the bridged channels.
- Hard-coded IDs that would break on a gateway upgrade: `sjmesh-relay` allowlist `!9ea3e8d4,!69841fe0,!0aca423c`, blocked flood nodes, Malla/Meshview history, JSON uplink topic. All in the upgrade plan.
- Website: `getting-started.html` has a new "Setting up on Meshtastic 2.8" section in the repo (held for the weekend combined deploy; NOT live).

---

## 6. Things to test on KPN9 (cheap, answers the [?] items)

1. Which preset did it come up on, and how did you set the region (screen or app)? **Answered Nov 6:** Long Fast before and after, region set from a client (laptop config GUI on KPN9, Android app on KPN8); which node the observation was about is to be confirmed [?].
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
