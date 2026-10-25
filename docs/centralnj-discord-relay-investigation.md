# CentralNJ → Discord relay ("MeshBridge") — something looks off

**Opened:** Sun Oct 25 2026, ~3:00 PM, from Charlie's screenshots. **Status:** documented, not investigated. **Protocol:** Meshtastic only (not MeshCore).

Tags: [V] = seen directly in the screenshots or the repo. [S] = someone said it. [I] = Claude's inference, not checked.

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

**Test #1, 3:02 PM (Charlie):** sent "Testing 1-2" on CentralNJ from the Meshtastic app. The app showed "Delivered to mesh" (at least one node rebroadcast it). By 3:03 PM it had **not** appeared in #mesh-relay; the last Discord post was still SGA V4 "Anytime!" at 2:53. [V] Which of Charlie's nodes sent it was not recorded. This fits oddity 4 below: it reached the mesh near Kendall Park, but no SJMesh-connected gateway seems to have heard it. To confirm in the Malla lookup (step 3): did CJG1/CJG2 upload it to cnjmesh1? If yes, it reached *our* broker but never *SJMesh's*. [I]

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
3. **cnjmesh1, Malla lookup for the blank message and Test #1** (before Nov 24). Also find Charlie's "Testing 1-2" (3:02 PM EDT, epoch ~`1792954920`) and list which gateways uploaded it. Look up `!e05567ac` (decimal `3763693484`) between 2:00 and 2:20 PM EDT Oct 25 (epoch `1792951200`-`1792952400`): which gateways uploaded it, `via_mqtt`, `hop_start`/`hop_limit`, and whether Malla decoded the text. Exact command to be written at that time against the live schema (`packet_history`, see session-log Aug 18).
4. **Ask Compy** (it's his bot), one message: what broker and topics MeshBridge reads; whether it is one-way or two-way (reactions); whether it skips MQTT-origin or its own roof bot on purpose; the blank post on bad UTF-8; "Unknown" names. Offer the 2:13 PM example.
5. **Decide what CNJ actually wants.** If the goal is "CNJ weather alerts and CentralNJ traffic reliably show in a Discord", options are: (a) leave it to Compy's bot and accept gaps; (b) have CentralNJ gateways also uplink to `mqtt.sjmesh.net`; (c) CNJ runs its own CentralNJ → Discord relay from cnjmesh1's broker, which already gets CJG1/CJG2 traffic directly. Pick after steps 1-4.

## Related

- `cnjmesh1/sjmesh-relay/relay.py`, `docs/sjmesh-bridge-backup.md`, `docs/sjmesh-duplicate-block-handoff-2026-08-14.md`
- `docs/nws-weather-bot-reference.md` (the weather alerts on CentralNJ)
- todos.md: Aug 18 "not seeing certain CentralNJ messages on KPN6 / Discord" (may be the same family of problem); Aug 30 webhook inventory and rotation
