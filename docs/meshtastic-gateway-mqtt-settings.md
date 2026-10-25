# Meshtastic gateway nodes: MQTT and channel settings (as read from the app)

One section per node, each from Charlie's app screenshots. Tags: [V] seen on screen, [I] inference (not tested). Why this exists: the Oct 25 2026 CentralNJ → Discord investigation (`docs/centralnj-discord-relay-investigation.md`). Broker side is in `docs/mqtt-topology-and-landmines.md`.

## CJG2: "Central Jersey GW2 | cnjmesh.me (MQTT)" (read Oct 25 2026, 3:40-3:41 PM)

Hostname `esp32s3-A3E8D4`, 10.0.0.234 per `cnjmesh1-operations.md`.

**MQTT module** [V]
| Setting | Value |
|---|---|
| MQTT enabled | on |
| Address | `10.0.0.181` (cnjmesh1's Mosquitto) |
| Username / password | `meshdev` / hidden (10 characters) |
| Encryption enabled | on |
| JSON output | **on** |
| TLS | off |
| Root topic | `msh/US` |
| MQTT client proxy | off (the node connects by itself over Wi-Fi) |
| Map reporting | on, but the "I agree" consent switch under it is **off** |

**Radio** [V]: 906.875 MHz, slot 20 (auto), the US LongFast default.

**Channels** [V icons, I meaning]
| # | Name | Icons shown | Key |
|---|---|---|---|
| 0 (primary) | LongFast | position pin, **uplink** cloud, *no downlink cloud* | default (orange lock) |
| 1 | CentralNJ | uplink + downlink | custom (green lock) |
| 2 | SJMesh | uplink + downlink | custom (green lock) |

**CentralNJ detail screen (3:45 PM) [V]:** MQTT Uplink **on**, MQTT Downlink **on**, Position **off**. This confirms that for CentralNJ, "two cloud icons" = both toggles on. LongFast and SJMesh rows still need the same check (LongFast shows only the up cloud; I read downlink as off, unconfirmed).

**CentralNJ PSK on this node [V]:** `kpKQLDIsINsKGdeC+p152lNeOkU50y+Gp86/wCORDMw=`. **The key published on cnjmesh.me is different:** `f+WQoPgd06tk0n3Kl2bUmNVGO7TcPkxchPD6QqMkYRg=` (`website/cnjmesh-me/index.html` and `getting-started.html`). Same channel name, different key = a different channel as far as the radios are concerned. If this screen was CJG2's, then CJG2's CentralNJ is not on the published key. That could explain the missing 3:08 PM test (Malla would store it as undecodable, not as a text message, and my text-only query would not have shown it) and means CJG2 may not be relaying or uploading other people's CentralNJ traffic. Unconfirmed: whether this dialog was CJG2's, and which key KPN6 uses.

### What this means [I]
- CJG2 publishes to cnjmesh1's local broker as `msh/US/2/e/<channel>/!<its id>` for all three channels, plus `msh/US/2/json/...` because JSON is on.
- Of those, the live bridge sends only `msh/US/2/e/CentralNJ/#` and `msh/US/2/json/CentralNJ/#` out (to `mqtt.meshtastic.org`). LongFast and SJMesh uploads stay on cnjmesh1 (Malla stores them). **Nothing goes to SJMesh's broker.**
- **Downlink = what CJG2 transmits on our RF.** With downlink on for CentralNJ and SJMesh, any message that reaches the local broker for those channels is sent over the air by CJG2. That is how SJMesh's CentralNJ traffic (pulled in by `sjmesh-relay`) becomes RF. It is also why the relay's flood-node block list matters: a flood node getting through gets transmitted.
- **LongFast downlink appears off, and it must stay off.** The `liamcottle` bridge pulls LongFast traffic *into* the local broker. If CJG2 downlinked LongFast, it would re-transmit other regions' LongFast onto our RF. This is the setting that actually protects LongFast from being flooded by us.
- If the Sep 3 todo is done (add `msh/US/2/e/SJMesh/#` to `relay.py`), SJMesh-channel traffic would enter the local broker and CJG2's SJMesh downlink would put it on our RF. Decide that deliberately.
- JSON on is why the bridge has a `json/CentralNJ` line. Extra volume, not a problem.
- Map reporting on with consent off: probably no map reports are being sent. Harmless, noted.

### Verdict so far
**Updated 3:45 PM:** the CentralNJ PSK differs from the published one (see above), which is now the leading suspect. Before that: nothing looked misconfigured. CentralNJ uplink is on and the address is the right broker, so the toggles alone do **not** explain why the 3:08 PM "Testing 3-4" (sent from CJG2) is missing from Malla. Next checks: tap **Test connection** on the MQTT screen, and run the broader Malla query (all packets 3:07:30-3:09:30 PM plus per-gateway counts) from the relay investigation doc.

Not captured yet for CJG2: LoRa settings (region, preset, "OK to MQTT"), Network (Wi-Fi), and the LongFast and SJMesh channel detail screens.

## KPN6 (roof node, MAC 90:70:69:84:1F:E0, node `!69841fe0`)
Pending: Charlie is sending screenshots.

## CJG1 (`!0aca423c`, "Central Jersey GW1 | cnj")
Not read. The node stays online but Charlie's management connection to it keeps dropping.
