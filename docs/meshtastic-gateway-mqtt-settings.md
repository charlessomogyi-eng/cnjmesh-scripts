# Meshtastic gateway nodes: MQTT and channel settings (as read from the app)

One section per node, each from Charlie's app screenshots. Tags: [V] seen on screen, [I] inference (not tested). Why this exists: the Oct 25 2026 CentralNJ → Discord investigation (`docs/centralnj-discord-relay-investigation.md`). Broker side is in `docs/mqtt-topology-and-landmines.md`.

## CentralNJ channel key registry (both keys kept on purpose, Oct 25 2026)

Keys are public by design here, so they are recorded in full. Charlie asked to keep both so he can ask for them later.

| Label | PSK (base64, 32 bytes) | Where seen | Status |
|---|---|---|---|
| **Published key** | `f+WQoPgd06tk0n3Kl2bUmNVGO7TcPkxchPD6QqMkYRg=` | cnjmesh.me (index and getting-started pages, copied verbatim from the repo copy); KPN6 channel 3 (3:46 PM) | **The key to use.** Charlie says the CentralNJ key has not changed since day one. |
| **CJG2's key** | `kpKQLDIsINsKGdeC+p152lNeOkU50y+Gp86/wCORDMw=` | CJG2 channel 3, screen read Oct 25 3:45 PM | Origin unknown; appears nowhere else in the repo or its history. **Replaced with the published key on Oct 25 (4:20 PM).** |

**Test log**
- **Oct 25 3:55 PM, "Testing 5-6" from CJG2, sent right after Charlie changed the key in the app [V Malla].** Two rows at 15:55:35 (epoch 1792958135.78 and .87, same packet id 2014653383), topic `msh/US/2/e/CentralNJ/!9ea3e8d4`, gateway and sender both `!9ea3e8d4`, portnum 0 `UNKNOWN_APP`, payload length 0, message_type `e`. So **CJG2 -> cnjmesh1 uplink works, but Malla could not decrypt the packet.** No other gateway uploaded it (consistent with other nodes being unable to decode it too).
- **The packet's channel-hash byte starts with `\xc`, and the old key gives 0xC9 while the published key gives 0x10 [I, computed from name+key].** So at 3:55:35 CJG2 was most likely still transmitting with the OLD key. Likely cause: the key change was not saved/applied on the node yet (node reboots after a channel change), or it was edited in a different slot. To confirm, print the first 16 bytes of `raw_service_envelope` for the row.
- **CJG2's node id = `!9ea3e8d4` (decimal 2661542100)**, matching its hostname `esp32s3-A3E8D4`.
- **4:13 PM "Testing 7-8": still undecodable** (`UNKNOWN_APP`, length 0). The first attempt had reverted: the app showed the new key, but it was never written to the node, and after a reboot CJG2 showed `kpKQLD...` again.
- **How the change finally stuck [V]:** edit CentralNJ, paste the key, tap **Save** in the dialog, then tap **Send** on the main Channels screen, wait for the node to reboot, then re-open and check. (Do not tap the circular arrow beside the PSK; it generates a random key.)
- **4:31 PM "Testing 9-10" from CJG2 after the fix [V screenshots]:** a bot ("Meshtastic 6021") replied on RF, and #mesh-relay showed `Unknown · !9ea3e8d4 · SJMesh · Testing 9-10 · direct`. Malla check of the 4:31 row (epoch 1792960230-1792960350) still to confirm.
- Two copies of one packet 0.1 s apart from one gateway: FYI, not yet explained (double publish or a second path).

After the change: send a test message from CJG2, then look in Malla for it (decoded text, gateway = CJG2's node id). Record the result here. Meshtastic does not validate keys, so a different PSK silently makes a different channel with the same name.

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
**Updated 3:45 PM:** the CentralNJ PSK differs from the published one (see above), which is now the leading suspect. **Confirmed 3:46 PM against KPN6: KPN6 uses the published key, so CJG2 is the one that differs.** Aug 18 notes say CJG1/CJG2 uploaded CentralNJ traffic back then, so something may have changed on CJG2 since (a key change?). Before that: nothing looked misconfigured. CentralNJ uplink is on and the address is the right broker, so the toggles alone do **not** explain why the 3:08 PM "Testing 3-4" (sent from CJG2) is missing from Malla. Next checks: tap **Test connection** on the MQTT screen, and run the broader Malla query (all packets 3:07:30-3:09:30 PM plus per-gateway counts) from the relay investigation doc.

Not captured yet for CJG2: LoRa settings (region, preset, "OK to MQTT"), Network (Wi-Fi), and the LongFast and SJMesh channel detail screens.

## KPN6 (roof node, MAC 90:70:69:84:1F:E0, node `!69841fe0`) (read Oct 25 2026, 3:46-3:47 PM)

**MQTT module** [V]
| Setting | Value |
|---|---|
| MQTT enabled | **on** |
| Address | `10.0.0.181` |
| Username / password | `meshdev` / hidden (10 characters) |
| Encryption enabled | **off** (CJG2: on) |
| JSON output | on |
| TLS | off |
| Root topic | `msh/US` |
| MQTT client proxy | **off** |
| Map reporting | on, consent "I agree" **on**, position precision about ±1.8 mi, publish every 3 hours |

**Radio** [V]: 906.875 MHz, slot 20 (auto), same as CJG2.

**Channels** [V icons]
| # | Name | Icons shown | Key |
|---|---|---|---|
| 0 (primary) | LongFast | position pin, uplink | default (orange lock) |
| 1 | KPTESTING | uplink | custom |
| 2 | KPCOMMS | none | custom |
| 3 | CentralNJ | uplink + downlink | custom |
| 4 | CNJ-MQTT | uplink | custom |
| 5 | SJMesh | uplink + downlink | custom |
| 6 | CNJTest | uplink | custom |
| 7 | CentNJ-MQTT | uplink | custom |

**CentralNJ detail (3:46 PM) [V]:** Uplink on, Downlink on, **Position on, Precise location on**. **PSK `f+WQoPgd06tk0n3Kl2bUmNVGO7TcPkxchPD6QqMkYRg=` = the key published on cnjmesh.me.** So KPN6 is on the published key and **CJG2 is the odd one out** (`kpKQLD...`).

### What this means
- **Icon reading holds:** KPCOMMS shows no icons (both off), KPTESTING/CNJ-MQTT/CNJTest/CentNJ-MQTT show uplink only, and CentralNJ's two icons matched two "on" toggles on both nodes. LongFast uplink-only on **both** nodes is therefore very likely right (downlink off). Not toggled-checked for LongFast itself. [I]
- **Contradiction with the repo:** Aug 9 and Aug 18 entries say KPN6's MQTT was **turned off on purpose** (no Wi-Fi by design, "pure RF, no internet uplink"). Today it is **on**, client proxy is off, and Malla shows KPN6 uploading its own 3:02 PM message as its own gateway. So KPN6 now reaches `10.0.0.181` by itself (Wi-Fi?), and my earlier "phone proxy" guess is wrong. Open: when and why it was turned on, and whether Wi-Fi is now enabled. [V settings, V Malla row]
- **KPN6 is also a downlink transmitter** for CentralNJ and SJMesh (like CJG2): anything arriving for those channels on cnjmesh1's broker can be sent out over its RF.
- **Encryption enabled is off** on KPN6 and on on CJG2. On newer firmware the effect of this setting may differ; KPN6's 3:02 message still arrived on an encrypted-style `/e/` topic. Worth remembering as a difference, not a known problem. [I]
- **Privacy FYI:** KPN6 shares **precise** position on CentralNJ. That key is published on the website and CentralNJ is bridged to the public broker, so the exact roof position is effectively public. Charlie's call.
- The four legacy/test channels (KPTESTING, CNJ-MQTT, CNJTest, CentNJ-MQTT) upload to cnjmesh1 but only `CentralNJ` is bridged out, so they stay local.

## CJG1 (`!0aca423c`, "Central Jersey GW1 | cnj")
Not read. The node stays online but Charlie's management connection to it keeps dropping.
