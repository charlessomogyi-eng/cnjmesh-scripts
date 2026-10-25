# CentralNJ → Discord relay ("MeshBridge") — something looks off

**Opened:** Sun Oct 25 2026, ~3:00 PM, from Charlie's screenshots. **Status:** documented, not investigated. **Protocol:** Meshtastic only (not MeshCore).

Tags: [V] = seen directly in the screenshots or the repo. [S] = someone said it. [I] = Claude's inference, not checked.

## TL;DR (Oct 25, 3:40 PM): read this first, the rest is evidence

**Red flags**
1. **No path from CNJ's broker to SJMesh's broker since Aug 14** (`sjmesh-relay` is inbound-only). CNJ messages reach the MeshBridge Discord only if an SJMesh gateway happens to hear them over RF. [V config, I conclusion]
2. **CJG2's 3:08 PM test is missing from Malla**, so CJG2's uplink may not be working. Unverified: need CJG2's settings. [V absence, I cause]
3. **Live `relay.py` lacks the `!db51bb30` block that the repo copy has.** That node may be flooding. One-line check in `known-issues.md`. [V diff]

**FYI (not problems)**
- Messages still go out over RF. "Delivered to mesh" means a nearby node rebroadcast it, and KPN6's 3:02 message was picked up by a gateway 5 hops away. People in RF range of the mesh get it; the gap is the SJMesh-broker / Discord audience.
- SJMesh → CNJ works (their messages show in the app).
- "Unknown" names, the blank post and the missing Rak Roof Bot replies are MeshBridge's own behavior, not ours.
- KPN6 uploads to MQTT today (likely via the phone's MQTT proxy) although the repo says its MQTT is off.
- LongFast is inbound-only on liamcottle: no flood risk. oktomqtt is retired on cnjmesh1 (Aug 2); on cnjmesh2 it is stopped but still defined in compose.

**Plan**
1. Read CJG2 and KPN6 MQTT and channel settings (what to look at is in the checklist below).
2. Lowest-risk fix: ask the MeshBridge operator to add our broker (`mqtt.cnjmesh.me`) as a read-only source. Nothing changes on our side, so no loop or flood risk.
3. Fallback: loop-safe outbound path in `relay.py` (design in `docs/mqtt-topology-and-landmines.md` §5), after asking Badwolf.

## What this is

- A Discord bot/webhook named **MeshBridge** (shows the "APP" tag) posts Meshtastic **CentralNJ** channel messages into a Discord channel **#mesh-relay** (59-64 online). [V]
- **Charlie does not own or run it.** He thinks he gave the webhook to Compy. [S] Compy's own webhooks found in the Aug 30 inventory were `Meshmonitor - Roof dd2680e7` and `snj-wx-bot`; MeshBridge was not in that list as one of his, so it may be one of the 13 that Charlie created and handed over. [I]
- Every post is labelled **"SJMesh"** and has a cloud icon, so it is almost certainly reading from SJMesh's broker `mqtt.sjmesh.net`, not from cnjmesh1. [I]
- CentralNJ is the channel CNJ's NWS weather alerts go out on (`Central Jersey GW1 | cnj`, `!0aca423c`). [V]

**Who runs SJMesh?** Charlie wrote "sjmesh (badwolf)". `cnjmesh1-operations.md` lists **Compy / KD2QED** as the SJMesh operator. Settle which is right (maybe both: one runs the broker, one runs the bots).

## What looked off (screenshots, Oct 25, 2:07-2:53 PM EDT)

Phone app (CentralNJ channel) compared with Discord #mesh-relay for the same messages:

| Time | Sender (as the app shows it) | Text | Discord shows | Notes |
|---|---|---|---|---|
| 7:00 AM | Central Jersey GW1 \| cnj `!0aca423c` | Freeze Warning (NWS) | posted, **"SJMesh"**, 3 hops | Our own weather alert is labelled SJMesh and arrived after 3 hops |
| 2:07 PM | MeshChat Mobile `!e05567ac` | testing | posted, **"Unknown"**, **"? hops"** | App shows 3 hops |
| 2:07 PM | Rak Roof Bot KD2QED (MQTT) | "@MeshChat Mobile Test transmission: Crystal clear! [GW]" | **not posted** | App shows cloud icon, 0 hops (came in over MQTT) |
| 2:13 PM | MeshChat Mobile `!e05567ac` | "anyone hear me�?" | **posted with an empty body** (only "3 hops · 2:13 PM") | App shows a `�` replacement character: the text had bytes that are not valid UTF-8 |
| 2:13 PM | Rak Roof Bot KD2QED (MQTT) | received! | **not posted** | cloud icon, 0 hops |
| 2:52 PM | PwnMonger Base 16a4 `!0acb16a4` | Yes / Two hops | posted, **"Unknown"**, 4 hops | App knows the name |
| 2:53 PM | MeshChat Mobile `!e05567ac` | thanks / k | posted, "Unknown", 3 hops | |
| 2:53 PM | SGA V4 `!1ba18c30` | Anytime! | posted, name shown, 4 hops | |

**Test #1, 3:02 PM (Charlie):** sent "Testing 1-2" on CentralNJ from the Meshtastic app. The app showed "Delivered to mesh" (at least one node rebroadcast it). By 3:03 PM it had **not** appeared in #mesh-relay; the last Discord post was still SGA V4 "Anytime!" at 2:53. [V] Sent from **KPN6** (Charlie, 3:07 PM). This fits oddity 4 below: it reached the mesh near Kendall Park, but no SJMesh-connected gateway seems to have heard it. To confirm in the Malla lookup (step 3): did CJG1/CJG2 upload it to cnjmesh1? If yes, it reached *our* broker but never *SJMesh's*. [I]

**Test #2, 3:08 PM (Charlie):** sent "Testing 3-4" on CentralNJ **from CJG2 itself** (Central Jersey Gateway 2). The app showed "Delivered to mesh". By 3:11 PM it had **not** appeared in #mesh-relay. [V] Charlie is fairly confident CJG2's MQTT is set up correctly, because it is one of the gateways that feeds cnjmesh1's broker and Malla. [S] I expected it to be on cnjmesh1 within seconds. **The Malla check (below) found it is NOT there**, so Test #2 does not support the outbound-path theory; it points at a second problem upstream (CJG2's own uplink). Open.

CJG1 was not tested: the node itself stays online, but Charlie's management connection to it (to change settings) keeps dropping. [S]

Reactions (🔢5, 🤝, 🤦) appear on the same messages in **both** Discord and the app. [V]

## The five oddities, with first guesses

1. **Names show "Unknown"** for nodes the app knows. [V] Guess: the bot never sees those nodes' NodeInfo packets. NodeInfo goes out on a node's *primary* channel; if CentralNJ is a secondary channel and only CentralNJ is uplinked, the bot only ever sees the text. [I]
2. **One message posted blank** (2:13 PM). [V] The sender's text contained a broken character; the bot seems to fail to decode it and posts nothing instead of the text with a `�`. Bot bug on Compy's side. [I]
3. **Rak Roof Bot replies never reach Discord.** [V] The roof bot is KD2QED, i.e. Compy's. Possible reasons: MeshBridge deliberately skips MQTT-injected packets or its own bot's messages, or the roof bot publishes to a different broker/topic than MeshBridge reads. [I]
4. **Everything is labelled "SJMesh"**, including CNJ's own weather alert, and that alert shows 3 hops. [V] "SJMesh" is probably the bot's name for its source broker, not where the message started. [I] But it also means CNJ traffic only reaches that Discord when some SJMesh-connected gateway happens to hear it over RF (see "How the brokers connect"), so CNJ messages can silently go missing there. [I]
5. **Reactions are mirrored.** [V] Either the bot turns mesh tapbacks into Discord reactions (one-way, harmless), or it sends Discord reactions back onto the mesh (two-way: then a Discord user can transmit into CentralNJ). Which one matters. [I]

Side note: the CentralNJ key is published on cnjmesh.me, so posting the channel to a public Discord exposes nothing that is not already public. Users may still assume the 🔒 channel is private. [V for the website; I for user expectations]

## How the brokers connect (the confusing part, written down once)

**An MQTT topic is just an address.** For Meshtastic it reads:

```
msh / US / 2 / e / CentralNJ / !0aca423c
 |     |   |   |      |           └ the gateway node that uploaded this copy
 |     |   |   |      └ channel name
 |     |   |   └ "e" = encrypted packet
 |     |   └ protocol version
 |     └ region (part of the "root topic", e.g. msh/US or msh/US/NJ)
 └ always "msh"
```

The same radio packet can show up several times, once per gateway that heard it, each under its own `!gateway` ending. A `#` in a subscription means "everything below here".

**The three brokers in play:**

| Broker | Who runs it | What feeds it (per repo) | Who reads it |
|---|---|---|---|
| `mqtt.meshtastic.org` (public; `meshdev`/`large4cats` is Meshtastic's well-known public login) | Meshtastic project | CNJ users who follow the cnjmesh.me instructions | anyone |
| `mqtt.sjmesh.net` | SJMesh (Badwolf/Compy, see above) | SJMesh gateways, plus anyone who follows the "also bridging with SJMesh" box on cnjmesh.me (root topic `msh/US`) | **MeshBridge (Discord)**, and cnjmesh1's `sjmesh-relay` |
| cnjmesh1 Mosquitto (`mqtt.cnjmesh.me`) | Charlie | CJG1/CJG2 uplinks; `sjmesh-relay`; `liamcottle` bridge; `oceancounty` bridge (last known failing, Aug 10) | Malla, Meshview, bots |

**Direction matters:** `sjmesh-relay` (`cnjmesh1/sjmesh-relay/relay.py`) is **one-way, SJMesh → cnjmesh1**, for `msh/US/2/e/CentralNJ/#` and `msh/US/NJ/2/e/CentralNJ/#` only, with three flood nodes blocked. The old native bridge that also sent traffic *out* to SJMesh was replaced on Aug 14. [V, repo] So, as far as the repo knows, **nothing CJG1/CJG2 hear is pushed to SJMesh's broker by our infrastructure.** That fits the weather alert arriving at MeshBridge after 3 RF hops. [I] Check the live `mosquitto.conf` before relying on this.

## Update Oct 25, 3:07 PM: Charlie's hunch, and the repo agrees

Charlie: "SJMesh kinda works correctly and my side, from an MQTT perspective, does not." The repo history backs this up [V, session-log]:
- **Aug 5:** the cnjmesh1 ↔ SJMesh Mosquitto bridge was set to `both` directions on CentralNJ (fix for a loop).
- **Aug 9:** `msh/US/2/e/SJMesh/# both 0` added so KPN6's SJMesh-channel messages reached SJMesh's community.
- **Aug 14:** that two-way bridge was replaced by `sjmesh-relay.py`, which is **inbound only** (SJMesh → cnjmesh1, CentralNJ topics), to stop the flood nodes.

So since Aug 14, **nothing CJG1/CJG2 upload goes to SJMesh's broker**. That's a missing outbound path left over from the flood fix, not a broken service. It explains Test #1 and the weather alert that only arrived after 3 RF hops. The "Unknown" names and the blank post are still MeshBridge's own issues. [I for the conclusion]

Also from the Aug 9 entry: Badwolf shared the SJMesh channel key in Discord, so Badwolf likely runs the SJMesh broker. Compy (KD2QED) runs the bots (Rak Roof Bot, likely MeshBridge). [I]

**Likely fix (design only, not built):** add an outbound path cnjmesh1 → `mqtt.sjmesh.net` that sends **only packets our own gateways uploaded** (topics ending in CJG1/CJG2's `!id`) on CentralNJ (and maybe SJMesh). It must not echo back anything the inbound relay pulled from SJMesh; that echo is exactly what caused the Aug 5 loop. Simplest is probably a second small function in `sjmesh-relay.py` (local → SJMesh, gateway-ID allowlist) and the inbound side skipping our own gateway IDs. Check with Badwolf that he's OK with us publishing to his broker again. Prove it with a repeat of Test #1.

### Config checklist: "is my side set up right for MQTT?" (Meshtastic app, per node)

Repo history on KPN6 conflicts: Aug 9 says its MQTT module was enabled (server `10.0.0.181`); Aug 18 says it is **intentionally disabled**, so it only reaches MQTT through CJG1/CJG2 hearing it over RF. Check which is true today.

For **KPN6**, **CJG1** and **CJG2**, write down:
1. Settings → Modules → **MQTT**: enabled? server address (expect `10.0.0.181` for anything that should feed cnjmesh1), username, root topic (`msh/US` or `msh/US/NJ`), "encryption enabled" (should stay on), "JSON" (normally off).
2. Settings → Network: is Wi-Fi on (a node needs internet/LAN to reach a broker)?
3. Channels → **CentralNJ**: **Uplink enabled** and **Downlink enabled** switches. Uplink = "send what I hear on this channel to MQTT". Downlink = "transmit what MQTT sends me on this channel over the air".
4. Same for the **primary channel** (where NodeInfo goes) if we want names to show up downstream.

Expected healthy picture [I]: CJG1/CJG2 have MQTT on, server `10.0.0.181`, CentralNJ uplink on. KPN6 can stay MQTT-off. Even if all of that is correct, nothing reaches SJMesh's broker until the outbound path above exists, so a correct config alone will **not** make Test #1 show up in Discord.

## Findings Oct 25, 3:14 PM: Mosquitto config and Malla lookup (Charlie ran both on cnjmesh1) [V]

**`mosquitto.conf` bridges (credentials omitted):** `meshtastic_public` → `mqtt.meshtastic.org:1883`, **out** only, `msh/US/2/e/CentralNJ/#` and `msh/US/2/json/CentralNJ/#` (clientid `cnjmesh1-CJG2-bridge`); `oceancounty` and `liamcottle` are **in** only (CentralNJ, NJ, plus LongFast on liamcottle); `meshomatic` → MeshCore out. **There is no `sjmesh` connection**, and `sjmesh-relay` is `active`. So the outbound gap to SJMesh is confirmed. Our broker pushes CentralNJ out only to the public Meshtastic broker, and not the `msh/US/NJ/...` topics.

**Malla, text messages 3:00-3:10 PM (all of them):**

| Time | From | Uploaded by (gateway) | Topic | hop_start / hop_limit |
|---|---|---|---|---|
| 15:02:31 | `!69841fe0` | `!69841fe0` | `msh/US/2/e/CentralNJ/!69841fe0` | 7 / 7 |
| 15:02:31 | `!69841fe0` | `!69841fe0` | same | 7 / 0 |
| 15:02:47 | `!69841fe0` | `!b03be2ac` | `msh/US/NJ/2/e/CentralNJ/!b03be2ac` | 7 / 2 |

- `!69841fe0` is **KPN6** (its MAC `90:70:69:84:1F:E0` is in `cnjmesh1-operations.md`). That is the 3:02 "Testing 1-2". [V]
- KPN6 uploaded its own message, so its MQTT uplink is working today even though the repo says it has no Wi-Fi and its MQTT was "intentionally disabled" (Aug 18). Likely explanation: the **phone app's MQTT proxy** (node uses the phone's connection while connected over Bluetooth), pointed at `10.0.0.181` as on Aug 9. [I, unchecked] This only works while the phone is connected.
- 16 seconds later a different gateway, `!b03be2ac`, uploaded the same message after **5 hops** (7 → 2). It came in on an `NJ` topic, so it reached our broker through a bridge or relay, not from our own gateways. [I]
- **No row for "Testing 3-4" (CJG2, 3:08 PM).** Nothing from CJG2 at all in this window.

**What this changes:** Test #1 (KPN6) is consistent with "reached our broker, never reached SJMesh's". Test #2 is not explained by that: the message never showed up on our own broker as a text message. Possible reasons, none checked: CJG2 isn't uploading right now; it uploads under another gateway ID or topic; the row is stored with a different portnum; or CJG2 doesn't uplink messages sent from a phone connected to it. **Next query:** list *all* packets and the per-gateway counts around 3:08 PM (see the chat that follows) to find CJG2's node ID and see whether it uploads anything.

## Do we need to capture anything now?

No. Nothing here is likely to vanish before we come back:
- The Discord messages stay in #mesh-relay.
- Malla on cnjmesh1 keeps raw packets for **30 days** (`MALLA_DATA_RETENTION_HOURS=720`), so today's packets are queryable until about **Nov 24 2026**. Do step 3 below before then.
- This file records what the screenshots showed. (The screenshots themselves are not committed: they show other people's messages and this repo is public.)

## Plan (when there is time; nothing here is urgent)

1. **Discord, 5 minutes.** In the server that has #mesh-relay: Server Settings → Integrations → Webhooks (and Bots). Find what posts as MeshBridge: creator, creation date, channel. If Charlie created it, add it to the webhook inventory and the rotation list. Also long-press the 🔢5 reaction on the 2:07 "testing" post to see who added it (MeshBridge itself = mesh tapback mirrored one-way).
2. **cnjmesh1, read-only, confirms the broker picture.** Run on cnjmesh1:
   ```bash
   grep -n -A8 "^connection" /opt/stacks/mqtt/config/mosquitto.conf
   systemctl status sjmesh-relay --no-pager | head -5
   ```
   Both finish on their own. Expect: no `sjmesh` connection with `out` or `both`; relay active.
3. **cnjmesh1, Malla lookup for the blank message and Test #1** (before Nov 24). Also find Charlie's "Testing 1-2" (3:02 PM EDT, KPN6, epoch ~`1792954920`) and "Testing 3-4" (3:08 PM EDT, sent from CJG2, epoch ~`1792955280`) and list which gateways uploaded each. Look up `!e05567ac` (decimal `3763693484`) between 2:00 and 2:20 PM EDT Oct 25 (epoch `1792951200`-`1792952400`): which gateways uploaded it, `via_mqtt`, `hop_start`/`hop_limit`, and whether Malla decoded the text. Exact command to be written at that time against the live schema (`packet_history`, see session-log Aug 18).
4. **Ask Compy** (it's his bot), one message: what broker and topics MeshBridge reads; whether it is one-way or two-way (reactions); whether it skips MQTT-origin or its own roof bot on purpose; the blank post on bad UTF-8; "Unknown" names. Offer the 2:13 PM example.
5. **Decide what CNJ actually wants.** If the goal is "CNJ weather alerts and CentralNJ traffic reliably show in a Discord", options are: (a) leave it to Compy's bot and accept gaps; (b) have CentralNJ gateways also uplink to `mqtt.sjmesh.net`; (c) CNJ runs its own CentralNJ → Discord relay from cnjmesh1's broker, which already gets CJG1/CJG2 traffic directly. Pick after steps 1-4.

## Related

- `cnjmesh1/sjmesh-relay/relay.py`, `docs/sjmesh-bridge-backup.md`, `docs/sjmesh-duplicate-block-handoff-2026-08-14.md`
- `docs/nws-weather-bot-reference.md` (the weather alerts on CentralNJ)
- todos.md: Aug 18 "not seeing certain CentralNJ messages on KPN6 / Discord" (may be the same family of problem); Aug 30 webhook inventory and rotation
