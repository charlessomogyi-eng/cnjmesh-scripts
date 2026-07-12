# nyme.sh Reference Summary

Condensed from [nyme.sh](https://nyme.sh) — the NYC-metro Meshtastic/MeshCore community site. This is a reference for CNJ Mesh, not a duplicate of their wiki; link back to nyme.sh for anything not covered here.

---

## What nyme.sh Is

A group of Meshtastic/MeshCore enthusiasts centered on the NYC metro area, running independent wide-area mesh radio networks. Not affiliated with NYC Mesh (the WiFi mesh network) — separate project, similar name. Services:

| Tool | URL | Purpose |
|---|---|---|
| Discord | discord.nyme.sh | Main community hub |
| Meshview | meshview.nyme.sh | MQTT conversation feed, map, network graph |
| Malla | malla.nyme.sh | MQTT packet detail / link analysis |
| Coverage map | coverage.nyme.sh | Network coverage |
| hops | w2asm.com/hops | Traceroute/hop analysis tool |

---

## Meshtastic — Two Networks in NYC Area

**Primary (current) network:**
- Preset: **Medium Range - Slow** ("MediumSlow" / MS48)
- Frequency slot: **48**
- Channel name: `MediumSlow` (or blank)
- Channel key: `AQ==` (default 1-byte)
- Rationale: default LongFast settings cause congestion at city scale; MediumSlow reduces airtime overhead.

**Legacy network (for stragglers/travelers):**
- Preset: Long Range - Fast (LongFast)
- Frequency slot: 20 or 0
- Same default key `AQ==`
- Kept alive at reduced infrastructure to catch newcomers; more range but heavily congested.

**Good-citizen rule:** don't run high-traffic apps (Reticulum, TAK) on the shared network — they saturate airtime for everyone; encrypted flood traffic gets actively blocked by infrastructure.

---

## Meshtastic Node Roles & Config (by node type)

### Handheld / mobile personal node
- Role: **CLIENT_MUTE**
- Position: disabled, or smart position (30+ min interval, 100+ m distance), altitude disabled
- Telemetry: off
- Device info interval: 18 hrs+
- **Hop limit: 7** (yes, higher than infrastructure nodes — needed to punch through infill on a packet-resiliency network)

### Stationary personal node (desk/roof, but you message from it)
- Role: **CLIENT**
- Position: fixed position recommended, altitude enabled, 24 hr broadcast interval
- Telemetry: off
- Device info: 18 hrs+
- Hop limit: 7

### Infrastructure node (relay-only, not used to message from)
- Role: **CLIENT_BASE**
- Rebroadcast mode: **Core Portnums Only** (blocks TAK/custom app noise)
- Is Unmessagable: true
- Position: fixed, altitude enabled, 24 hr interval
- Telemetry: 6 hr interval min
- Device info: 48 hr interval
- **Hop limit: 2**
- Strongly recommend enabling remote admin

**Role selection quick rule:** portable/mobile → `CLIENT_MUTE`; home/rooftop base → `CLIENT_BASE`. Only run one `CLIENT`/`CLIENT_BASE` node per household — multiples nearby cause self-interference. Don't self-appoint as `ROUTER`/`ROUTER_LATE` without coordinating in Discord #infrastructure — a bad infrastructure node actively hurts the mesh.

### Alternate/simplified config reference (node_configuration page)
Slightly different phrasing of the same idea, worth noting for cross-check:
- Number of hops: 3–4 typical (not 7) for general clients — 7 recommended only for CLIENT_MUTE nodes having trouble, since higher hops in a dense metro area can leak packets 100+ miles out (over-hopping problem)
- RX Boosted Gain: Enabled (SX126x chip series)
- Node Info Broadcast Interval: 6 hours
- Time zone string: `EST5EDT,M3.2.0/2:00:00,M11.1.0/2:00:00`

---

## MeshCore Settings (NYC)

- Preset: US/Canada
- Frequency: **910.525 MHz**
- Bandwidth: **62.5 kHz**
- Spread Factor: **7**
- Coding Rate: **5**
- Increase coding rate if messages aren't landing (cross-compatible change)

**Repeaters:**
- Zero-hop auto advert interval: 360 min+
- Flood auto advert interval: 24 hrs+

*(Note: these MeshCore RF parameters — 910.525/62.5/SF7/CR5 — match what's already configured on the CNJ Mesh Observer node.)*

---

## MQTT

- Server: `mqtt.nyme.sh`
- Username: `meshdev` / Password: `large4cats` (Meshtastic default creds — same ones CNJ Mesh currently uses and is planning to rotate)
- Encryption: yes
- Root topic: `msh/US/NY`
- Relaying-between-sites function is **disabled** on nyme.sh's server — community prefers radio-only mesh; MQTT is used only for stats/visualization (Meshview, Malla), not as a network backbone.
- Server will **not** send packets back to your node even with channel Downlink enabled.
- To appear on the map: enable "OK to MQTT" in LoRa settings + enable position sharing on Primary channel. That's the whole requirement for casual users.

---

## Optional Secondary Channels

| Channel | Key | Purpose |
|---|---|---|
| Wx | `WQ==` | Local weather station messages |
| mesh-around | `mQ==` | Interact with meshing-around bots |

---

## FAQ Highlights

**Hardware recommendations** (nyme.sh-vetted):
- Handhelds: Muzi R1 Neo, Muzi H2T, Seeed Wio Tracker L1, SenseCAP T1000E, RAK WisMesh Tag
- Fixed/solar: Seeed SenseCAP Solar Node

**Antennas:**
- Personal: Muzi Whip (SMA), ZBM2 Mesh Whip V2 (needs BNC adapter)
- Fixed: Alfa 5 dBi (compact, good for lower mounts), Rokland 5.8 dBi (large, high performing)
- **Key insight: don't chase high gain in urban environments.** Above ~5 dBi, narrow beamwidth causes overshoot of nearby terrain in dense, multipath-heavy cities — a lower-gain antenna often hears more. Marketed gain numbers are frequently inflated versus lab-tested reality (e.g., Alfa "5 dBi" tests closer to 2–3 dBi).
- Never power on a node without an antenna attached — can permanently damage the radio.
- Watch SMA vs RP-SMA — physically mates but won't make contact; can damage radio if transmitted into.

**Common troubleshooting:**
- *Negative/zero hop counts:* caused by old firmware nodes lacking the `hop_start` field, zeroing it on relay.
- *`!ffffffff` in traceroutes:* a node in the path has outdated firmware, mismatched channel key, or Skip Decoding on, so it can't add itself — placeholder inserted instead.
- *No acks:* "Acknowledged" = implicit ack (you heard your own message repeated). "Max retransmission reached" ≠ nobody got it, just that you didn't hear a repeat. `CLIENT_MUTE` nodes never retransmit, so they'll never show this differently. Busy meshes can take minutes for clear airtime.
- *Excess NODEINFO/POSITION packets:* possible reboot loop (check power supply/reflash) or normal NODEINFO handshake churn when meeting many new nodes at once.

---

## Adjacent Meshes (regional directory)

nyme.sh maintains a list of neighboring/related mesh networks, including **Central NJ: cnjmesh.me** and Forest Edge (forest-edge.info) in New Jersey, plus multiple NY regions (Long Island, Catskills, Westchester, Capital Region, Rochester, Buffalo) and CT/MA/PA meshes. Full list: https://nyme.sh

---

## Glossary — Terms Worth Knowing (not already common in CNJ Mesh usage)

- **Backbone nodes** — key infrastructure nodes with reliable links forming a regional network core (towers/mountains)
- **Infill nodes** — second-layer infrastructure bridging street level to the backbone, typically high rooftops
- **Core Portnums Only** — rebroadcast mode limiting relay to NodeInfo/Text/Position/Telemetry/Routing packets only, blocking noisy custom apps
- **EIRP** — Effective Isotropic Radiated Power, the real-world output after TX power + feed line loss + antenna gain
- **VSWR** — Voltage Standing Wave Reflection; 1 = ideal antenna match, above 2 = poor
- **Tropospheric ducting (🌈🦆)** — atmospheric refraction that lets signals travel much farther than normal

Full glossary: https://nyme.sh/glossary/

---

## Source Pages Referenced

- https://nyme.sh/ (home)
- https://nyme.sh/getting-started/
- https://nyme.sh/faq/
- https://nyme.sh/glossary/
- https://nyme.sh/node_configuration/
- https://nyme.sh/node_configuration_adv/
- https://nyme.sh/build_resources/
- https://nyme.sh/mqtt/

*Summarized July 12, 2026 for CNJ Mesh reference. This is a condensed digest, not a replacement — check nyme.sh directly for anything not covered here or if settings may have changed.*
