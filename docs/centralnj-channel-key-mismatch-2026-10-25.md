# CentralNJ channel key mismatch on CJG2: found and fixed (Oct 25 2026)

**Status: FIXED Oct 25 2026, 4:20 PM.** Found while investigating why not everything shows up in the Discord #mesh-relay (MeshBridge). Meshtastic only, not MeshCore.
Tags: [V] seen directly (screenshot, Malla row, config file), [S] Charlie said it, [I] Claude's inference.

## BLUF

CJG2 (Central Jersey GW2, `!9ea3e8d4`) had a **different copy of the CentralNJ channel key** than every other node, the website and Malla. It was effectively on its own channel that happened to share the name. Nothing warned about it, because Meshtastic never checks a key against other nodes. It was found on Oct 25 and corrected after three attempts. Afterwards, tests from CJG2 and from KPN6 both reached #mesh-relay and got bot replies.

## The terminology (Charlie's wording, agreed Oct 25)

The key belongs to the **channel**, not to a node. A node needs the channel **name and the channel's key** to talk on it. "A wrong key on CJG2" means CJG2's stored copy of the CentralNJ key differed. Malla (software, no radio) holds its own copy to decrypt what it receives.

| Copy of the CentralNJ channel key | Value |
|---|---|
| **Correct (published on cnjmesh.me; KPN6; Malla `default_channel_key`)** | `f+WQoPgd06tk0n3Kl2bUmNVGO7TcPkxchPD6QqMkYRg=` |
| **Wrong copy found on CJG2 (origin unknown, appears nowhere else in the repo)** | `kpKQLDIsINsKGdeC+p152lNeOkU50y+Gp86/wCORDMw=` |

Charlie says the CentralNJ key has not changed since day one [S]. Keys here are public by design, so both are recorded in full.

## Symptoms that led here

- Test #1 (3:02 PM, KPN6, "Testing 1-2") and Test #2 (3:08 PM, CJG2, "Testing 3-4") never appeared in #mesh-relay. [V]
- CJG2's 3:08 PM message was missing from Malla's text messages. [V]
- Several oddities in #mesh-relay (Unknown sender names, a blank post, missing bot replies) turned out to be MeshBridge's own behavior, not ours.

## Timeline (Oct 25, EDT)

| Time | Event |
|---|---|
| 3:02 | KPN6 test. Malla: KPN6 itself (2 rows), plus `!b03be2ac` at 5 hops. **No CJG2 row.** Not in Discord. |
| 3:08 | CJG2 test. Not in Malla as text, not in Discord. |
| 3:41-3:47 | Node settings read from both nodes. **CJG2's CentralNJ key differs from KPN6's and the website's.** |
| 3:55 | First change on CJG2 in the app. Test "5-6": reached cnjmesh1 but stored as `UNKNOWN_APP`, payload length 0 (undecodable). Packet's channel-hash byte began `\xc`, matching the old key (0xC9), not the published one (0x10). |
| 4:13 | After a reboot, "7-8": still undecodable. The app had shown the new key, but it never reached the node; after the reboot the app re-read `kpKQLD...`. |
| 4:19-4:20 | Third attempt: paste key, **Save**, **Send** on the Channels screen, reboot. |
| 4:31 | "Testing 9-10" from CJG2: a bot replied on RF, and the message appeared in #mesh-relay (`!9ea3e8d4 · SJMesh · direct`). |
| 4:37 | "Testing 11-12" from KPN6: appeared in #mesh-relay (`SBNJ Kendall Park Roof N · 3 hops`), and Rak Roof Bot KD2QED replied. |

## What the data showed

- **A wrong-key node is deaf and mute for that channel [I].** At 3:02 CJG2 uploaded nothing for KPN6's packet. At 4:37, with the right key, CJG2 heard KPN6 directly (0 hops, RSSI -71, SNR 6.25) and uplinked it. Likely cause: a gateway only uplinks packets it can match to one of its own channels.
- **The Discord arrivals came through RF, not through our broker.** The 4:37 post matches a different gateway, `!a6965300`, which heard KPN6 at 3 hops on a very weak link (-111 dBm, SNR -19). CJG2's 4:31 post was tagged "direct". There is still no outbound path from cnjmesh1 to `mqtt.sjmesh.net` (see "Still open"). [I]
- **Malla's copy of the key is correct** (checked Oct 25 4:41 PM). So an undecodable CentralNJ packet in Malla means the *sender's* key is off. [V]
- **KPN6 publishes already-decoded packets** (its MQTT "Encryption enabled" is off), so Malla reads them without needing the key. CJG2 publishes encrypted packets (encryption on), so Malla must have the right key. [V settings, I effect]

## Lessons

1. **Meshtastic does not validate keys.** Any valid-length key is accepted; a mismatch silently creates a different channel with the same name. No error anywhere.
2. **Changing a channel key in the Android app:** edit CentralNJ, paste the key, tap **Save** in the dialog, then tap **Send** on the main Channels screen, wait for the node to reboot, reconnect, re-open the channel and check the key. Backing out loses the edit. Do **not** tap the circular arrow beside the PSK (it generates a random key).
3. **The app showing the new key is not proof.** The check that counts is after the reboot, when the app has re-read the config from the node.
4. **"Delivered to mesh" proves nothing about reach.** It only means the radio sent it.
5. **Do not assume a node is configured right because it "feeds Malla".** CJG2 appeared in Malla with metadata, but its CentralNJ content was undecodable.

## How to verify or detect this later (cnjmesh1, finishes on its own)

Malla table `packet_history` (container `mqtt-malla-web-1`, DB `/app/data/meshtastic_history.db`, 30-day retention). Signs of a key problem on a packet: `portnum_name = 'UNKNOWN_APP'`, `payload_length = 0`, `message_type = 'e'`, and a channel-hash byte that differs from the others. The expected channel-hash byte is XOR of all bytes of the channel name and all bytes of the key: **16** for CentralNJ with the published key, **201** (0xC9) with the wrong CJG2 copy.

Per-gateway view of decode status and channel byte for the last 3 hours (see the investigation doc for the exact command, run Oct 25 as a diagnostic). Quick check of one test message: select rows with `topic like '%CentralNJ%'` in a window around the send time (epoch seconds), showing `gateway_id, portnum_name, payload_length, hop_start - hop_limit, relay_node, rssi, snr`.

Handy identifiers: CJG2 = `!9ea3e8d4` (decimal 2661542100, relay byte 212); KPN6 = `!69841fe0` (decimal 1770266592, relay byte 224).

## Still open (see `todos.md`)

1. **Troubleshoot connectivity to SJMesh** (restore an outbound path). Not caused by the key problem; it predates it. Details in the todo.
2. **Why Malla showed CJG2's copy of KPN6's 4:37 packet as `UNKNOWN_APP`** even though Malla's key is right. Needs the per-gateway decode query; possibly a one-packet fluke.
3. **KPN6's MQTT is on** (client proxy off, address `10.0.0.181`), contradicting the Aug 9/18 "off by decision" notes. Find out when and why.
4. **KPN6 shares precise location on CentralNJ**, a channel with a published key bridged to the public broker. Charlie's call.
5. **Live `relay.py` lacks the `!db51bb30` block** that the repo copy has; check whether that node floods.
6. **Who runs MeshBridge/SJMesh**: Badwolf or Compy/KD2QED?

## Related

- `docs/centralnj-discord-relay-investigation.md`: the full investigation, evidence and plan.
- `docs/meshtastic-gateway-mqtt-settings.md`: both nodes' settings, the key registry and the test log.
- `docs/mqtt-topology-and-landmines.md`: bridge topology and rules (never un-comment `#connection sjmesh` while `sjmesh-relay` runs).
