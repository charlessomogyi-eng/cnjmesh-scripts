# LetsMesh Integration — Research Notes (2026-07-12)

## Why This Is Being Considered
After building a custom public MQTT broker (`mqtt.cnjmesh.me` over Cloudflare
Tunnel WSS — see CLAUDE_CONTEXT.md), it became clear there's already an
established community-standard alternative: **LetsMesh.net**. Rather than
asking every regional operator to trust/configure a CNJ-specific broker,
other regions already just point their tools at LetsMesh.

## What LetsMesh Is
- Global MeshCore MQTT aggregation broker + analyzer/map: `analyzer.letsmesh.net`
- Uses **IATA airport codes** to tag regions (e.g. `ORD` for Chicago) — find
  the right one for Central NJ at `https://analyzer.letsmesh.net/map/iata`
- CoreScope's broker config already has "Letsmesh" as a built-in Format
  option (this is what ozneteast was already trying to use)
- Authentication is often automatic via the node's own MeshCore auth token —
  **no shared username/password needs to be distributed**, unlike our current
  `meshdev`/`large4cats` setup

## How Other Regions Use It (Precedent)
- **ChiMesh (Chicago):** operators point observers at LetsMesh (global) *and*
  a regional ChiMesh broker for redundancy/regional identity. Uses
  `meshcoretomqtt` (Cisien's tool) with dual-broker config — see
  `github.com/Cisien/meshcoretomqtt`
- **EastMesh (Brisbane):** same dual pattern — LetsMesh globally, EastMesh
  broker regionally, both feeding CoreScope

## Setup Methods (per wiki.meshmapper.net and chicagolandmesh.org)
Four ways to run a MeshCore MQTT observer feeding LetsMesh:
1. Dedicated companion device (Raspberry Pi) + Python service — same pattern
   as what's already running on cnjmesh1 (`meshcore-packet-capture`)
2. Home Assistant integration (if already running HA)
3. Native firmware on Heltec V3/V4 with MQTT-enabled build — no companion
   device needed, simplest hardware setup, but "documentation in progress"
   per meshmapper wiki as of this search
4. `meshcoretomqtt` (Cisien's script) — explicit LetsMesh + regional preset
   support built in, NixOS module available, systemd service on Linux

## Tradeoff: Own Broker vs. LetsMesh
| | mqtt.cnjmesh.me (built today) | LetsMesh.net |
|---|---|---|
| Setup effort | Built and maintained by us | Already exists |
| Operator friction | Everyone needs our specific host/creds | Standard, IATA-based, tools already default to it |
| Data control | Fully ours | Shared with global community pool |
| Redundancy | Single point of failure (our Pi/tunnel) | Established, presumably more robust |
| Regional identity | NJ-specific, curated | Global, NJ nodes as a small piece |

**Not mutually exclusive** — likely approach is to do both: feed CNJ data
into LetsMesh (for community reach, matches what other operators' tools
already expect) while keeping mqtt.cnjmesh.me for CNJ-specific tooling
(CoreScope, own dashboards). Needs research into whether meshcore-hub
supports dual-broker publishing, or whether `meshcore-packet-capture` can
publish to both mqtt.cnjmesh.me and LetsMesh simultaneously.

## Next Session — Starting Point
1. Find the correct IATA code for Central NJ: `https://analyzer.letsmesh.net/map/iata`
2. Check if `meshcore-packet-capture` (already running on cnjmesh1) supports
   publishing to multiple brokers simultaneously, or if a second instance /
   `meshcoretomqtt` install is needed
3. Register/configure observer on LetsMesh per their onboarding flow:
   `https://analyzer.letsmesh.net/observer/onboard`
4. Decide: keep mqtt.cnjmesh.me running alongside LetsMesh, or treat it as
   CNJ-internal only going forward

---

# ozneteast — Conversation Context (Discord, #meshcore-nj-mqtt)

## Who He Is
Active MeshCore operator, interested in bridging his local mesh to CNJ's,
eventually hoping to reach South Jersey nodes. Runs his own local CoreScope
instance successfully (`192.168.4.10x`, no auth needed — proves his software
stack works fine).

## Key Technical Notes From His Messages
- **He knows how to get MeshCore packets INTO MQTT, but not how to take an
  MQTT packet and retransmit it back OVER MeshCore RF.** This is a real
  capability gap — even once connected to mqtt.cnjmesh.me, he may only be
  able to *publish* his local traffic outward, not relay CNJ traffic back
  out over his own RF, unless this gets solved separately.
- Mentioned **map.lvmesh.com** (Lehigh Valley Mesh) — another regional
  community worth being aware of, possibly a future bridging target
- His prior connection attempts to `mqtt.cnjmesh.me` all failed because the
  broker **had no working public path at all yet** — not a config or format
  issue on his end. This is now fixed (see MQTT WSS section in
  CLAUDE_CONTEXT.md).
- CoreScope's broker editor has two separate settings worth getting right
  together: **Format** (Meshcoretomqtt / Letsmesh / Waev / openHop — the
  packet/topic schema) and **Transport** (TCP vs WS). He had Format set to
  "Letsmesh" — unconfirmed whether that's actually the right format for
  connecting to a CNJ-specific broker vs. the real LetsMesh service.
- CoreScope's UI already hints at the exact setup built today: the Port
  field literally shows placeholder text "443 WS, 1883 TCP".

## Open Follow-Up (for tomorrow or whenever LetsMesh work resumes)
Given the LetsMesh pivot being considered, the right move may be to tell him
to skip a CNJ-specific broker connection entirely and instead help him get
his own observer set up as a proper LetsMesh observer with an NJ IATA code —
which is likely a smoother, more standard path for him than any custom CNJ
broker config.
