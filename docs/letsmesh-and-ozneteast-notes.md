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

## Confirmed Connection Details (found 2026-07-12, evening)
- **Host:** `mqtt-us-v1.letsmesh.net`
- **Port:** `443`
- **Transport:** WebSockets (WSS), TLS enabled — same pattern as mqtt.cnjmesh.me
- **Auth:** JWT/token-based, tied to your node's own public key — **not** a shared username/password like `meshdev`/`large4cats`. The bridge software (meshcore-packet-capture or meshcoretomqtt) generates/signs this automatically; may require installing `meshcore-decoder` (npm package) on cnjmesh1 if not already present — check before assuming this is a zero-install task.
- **Topic structure** (auto-handled by bridge software):
  ```
  meshcore/{IATA}/{PUBLIC_KEY}/status
  meshcore/{IATA}/{PUBLIC_KEY}/packets
  meshcore/{IATA}/{PUBLIC_KEY}/debug
  ```
- **IATA code:** **EWR (Newark, US) — confirmed 2026-07-12.** Searching "nj" returns false matches (CNJ = Cloncurry Australia, etc. — coincidental letter match, not NJ). EWR is the correct, verified match for the Central NJ region on the LetsMesh region selector. Not yet checked whether another operator is already using EWR — worth a quick look before committing (not a blocker either way; shared regional code is fine).

Charles signed up for both `analyzer.letsmesh.net` (the map/dashboard) and `forum.letsmesh.net` (community forum) on 2026-07-12 — account exists, ready to use tomorrow.

## Two Paths to Get On the Map
1. **Software bridge (likely path — matches existing infra):** `meshcore-packet-capture` (already running on cnjmesh1, feeding the Observer's serial data to mqtt.cnjmesh.me) reportedly supports adding LetsMesh as a second simultaneous broker target — a single observer can publish to multiple brokers at once. This would be a config change, not new infrastructure.
2. **Firmware-level (alternative, not needed given #1 exists):** Flash "observer-uplink-native-dev" firmware directly onto a Heltec board via the LetsMesh onboarding page, which bakes in WiFi + LetsMesh upload support natively. Per Idaho Mesh's guide (`idahomesh.org/add-a-letsmesh-observer`), you set the IATA code via CLI command, optionally link to your LetsMesh account via email, optionally link to a companion node's public key for public ownership display. This is a from-scratch route — not needed since we already have a working observer/capture pipeline.

## Before/After Verification Checklist
**Before (baseline, check first):**
1. `docker logs meshcore-packet-capture --tail 30` on cnjmesh1 — confirm only your own broker connection shows, no LetsMesh mention
2. Check `analyzer.letsmesh.net/map` filtered to your future NJ region — confirm nothing shows there yet (baseline = empty)

**After implementing:**
1. Same log command — look for a new connection line to `mqtt-us-v1.letsmesh.net`, ideally "connected"/"subscribed"
2. `analyzer.letsmesh.net/map` (or the Packets feed, filtered by region and packet type = **Advert**) — your node's advertisement should appear within ~5 minutes of first successful connection (per official onboarding docs: "Your node must have an advertisement heard before it will show up in the map or dropdown, but packet data will still be recorded in the meantime")
3. Regional observer list (once NJ IATA code is known), same pattern as: `analyzer.letsmesh.net/status/observers?region=BOS` (Boston's version) — check for an NJ-equivalent URL

## Precedent: Regional Communities Running Dual-Broker (LetsMesh + Local)
**Greater Boston Mesh** is doing exactly the dual-broker pattern being considered for CNJ Mesh — upload to LetsMesh globally *and* their own regional MQTT broker simultaneously, with a public region-filtered observer view. Their setup doc: `bostonme.sh/docs/MeshCore/meshcore-mqtt`. Worth reading as a working example of the exact end-state CNJ Mesh may end up at (LetsMesh + mqtt.cnjmesh.me both running).

## Forum Threads Flagged for Reading (not yet fetched — forum blocks automated access)
- `forum.letsmesh.net` thread: "Not able to connect to US LM Broker" (General category, ~2 days old as of 2026-07-12) — worth reading in case it surfaces a common connection issue we'd otherwise hit blind
- `forum.letsmesh.net` thread: "How do I put my self on the mash analyzer map?" (Pacific Northwest category, ~2 days old) — same question we'll have tomorrow; attempted to fetch directly but the forum blocks bot/automated requests (returns a block page) — Charles will need to open these manually in-browser if the answers are needed

## Packet Type Reference (from live Analyzer feed UI)
Available filter types on the Packets feed: Request, Response, TextMessage, Ack, **Advert** (the one that matters for map visibility), GroupText, GroupData, AnonRequest, Path, Trace, Multipart, Control, RawCustom, Unknown.


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
