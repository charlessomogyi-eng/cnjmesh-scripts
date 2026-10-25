# MQTT topology and landmines — READ BEFORE CHANGING ANY MQTT/BRIDGE CONFIG

Built Oct 25 2026 from a full repo pass (session-log, todos, known-issues, ops, both committed mosquitto configs, `relay.py`, the flood-fix and ACL-dead-end docs) plus the **live** `mosquitto.conf` Charlie pasted that day. Purpose: stop re-deriving this, and stop repeating the Aug 4 / Aug 5 / Aug 14 mistakes.

Tags: [V] verified from repo or pasted live output · [S] someone said it · [I] inference.

---

## 1. The live picture (cnjmesh1, as pasted Oct 25 2026 15:14) [V]

Broker: Mosquitto in Docker, `/opt/stacks/mqtt/`, config bind-mounted from `/opt/stacks/mqtt/config/mosquitto.conf`. Listeners 1883 and 9001 (websockets). `allow_anonymous false`, `password_file`.

| Connection | Remote | Direction | Topics |
|---|---|---|---|
| `meshtastic_public` | `mqtt.meshtastic.org:1883` | **out** | `msh/US/2/e/CentralNJ/#`, `msh/US/2/json/CentralNJ/#` |
| `oceancounty` | `mqtt.oceancountyme.sh:8883` | **in** | `msh/US/2/e/CentralNJ/#`, `msh/US/NJ/2/e/CentralNJ/#` |
| `liamcottle` | `mqtt.meshtastic.liamcottle.net:1883` | **in** | CentralNJ ×2, **LongFast ×2** |
| `meshomatic` | `us-east.meshomatic.net:31883` | **out** | `meshcore/#` (MeshCore, not Meshtastic) |
| `sjmesh` | — | **GONE** | no SJMesh connection exists in the live file |
| `sjmesh-relay.service` | `mqtt.sjmesh.net:1883` | **in only** (Python, not a bridge) | CentralNJ ×2, minus 3 blocked node IDs |

So: **the only Meshtastic traffic leaving cnjmesh1 goes to the public Meshtastic broker, CentralNJ only.** Nothing we run publishes to SJMesh's broker. That is the Oct 25 Discord-relay finding, confirmed at the config level.

**Who reads the local broker:** Malla (`mqtt-malla-capture-1`, subscribes **raw `msh/US/#`** — so anything that lands locally gets stored), Meshview, mesh-discord-shim, bots. `mqtt-filter` / oktomqtt is **retired** (Aug 2, nothing consumed `filtered/msh`; its unrotated log hit 30GB and filled the disk).

cnjmesh2 is a separate, much smaller setup (its own Mosquitto + Malla, `~/meshtastic-mqtt`, oktomqtt stopped). Its committed config bridges to the public broker with `topic # out 0 filtered/msh/US/ msh/US/NJ/` plus a CentralNJ `out` — treat cnjmesh2's outbound as **unreviewed** before touching it. [V committed file, not re-verified live]

---

## 2. LANDMINE: the committed config does NOT match live [V]

`cnjmesh1/configs/mosquitto-cnjmesh1.conf` in this repo still contains **both**:
- `connection sjmesh` (inbound CentralNJ), and
- a trailing `connection sjmesh-bridge` with **`topic msh/US/2/# out 0`** — an extremely broad outbound.

Neither exists in the live file. **Restoring the committed config onto cnjmesh1 would re-create the exact Aug 5 republish loop** (see §3). The committed file is a stale snapshot, not a deployable artifact. Before any restore, diff it against live and strip both stanzas. Same for `docs/sjmesh-bridge-backup.md`, which documents that same broad `msh/US/2/# out 0` stanza.

---

## 3. The three incidents that shaped this config — do not re-create them

**Aug 4 — the firehose flood.** `oceancounty`, `liamcottle` and `sjmesh` were each pulling `msh/US/#` or `msh/#` **inbound**. 1.63M packets/24h, 99.5% foreign undecodable junk; Malla hit 9.4M rows / 3.1GB, queries 149s, disk filled, weeks of instability. Fix: scope every inbound bridge to named channels only. **Rule: never subscribe a bridge to `msh/#` or `msh/US/#` inbound.** [V]

**Aug 5 — the republish loop.** Two *separate* connections pointed at the same remote host (`sjmesh` in, `sjmesh-bridge` out `msh/US/2/#`). Different connection names mean Mosquitto's loop protection does not apply between them, so CentralNJ traffic went out, came back, went out again — 68,763 packets/hr. Fix at the time: merge into one connection using `both`. **Rule: one connection per remote host; if traffic must go both ways use `topic ... both` on a single connection with one clientid. Before editing any bridge, list every connection to that same host.** [V]

**Aug 14 — the ACL dead end.** Blocking one flooding node via `local_username` + `acl_file` deny **did not work**, tested twice, even with all three bridges treated. Mosquitto's ACL deny does not apply to bridge-injected content. The working answer was the standalone Python relay with an in-code topic blocklist. **Rule: do not re-attempt broker ACLs to filter bridge traffic.** Leftovers may still be on disk (3 bridge-identity users in `pwfile`, an `aclfile`, `local_username` lines) — inert, `acl_file` is not loaded. [V]

---

## 4. "Will this flood LongFast?" — the answer

**No, not as configured, and here is why.** LongFast appears exactly once: `liamcottle`, **inbound only** (`msh/US/2/e/LongFast/#` and the NJ variant, added Aug 15). It was verified safe — zero LongFast rows reached Malla — and Charles decided to keep it indefinitely. [V]

Every **outbound** topic in the live config is CentralNJ (or MeshCore for meshomatic). So nothing we publish can land on LongFast.

**What would actually cause a flood, in order of risk:**
1. Adding **any** `out` or `both` topic with a wildcard above a named channel (`msh/US/2/#`, `msh/US/#`). This both floods others and risks a loop.
2. Adding a second connection to a host we already bridge to (§3, Aug 5).
3. Enabling **uplink on the LongFast/primary channel** on a gateway node (CJG1/CJG2). That is a node-side setting, not Mosquitto — a gateway with LongFast uplink on will push LongFast traffic to whatever broker it points at. Check this before changing any node's channel settings.
4. Re-enabling an inbound firehose (§3, Aug 4) — floods us, not them.

**A safe change looks like:** one named channel, one direction, on an existing connection, with a backup taken first and a packet-rate check after.

---

## 5. If/when the outbound path to SJMesh is restored (the open Oct 25 item)

Design constraints, from the history above:
- Do **not** add a second connection to `mqtt.sjmesh.net` — `sjmesh-relay.service` already holds an inbound client session to that host. A new outbound Mosquitto bridge alongside it is structurally the Aug 5 bug. [I, but directly implied by §3]
- Safest shape: extend `relay.py` with a second, outbound direction that publishes **only packets whose topic ends in our own gateway IDs** (CJG1/CJG2), and have the inbound side skip those same IDs so nothing can echo. Code-level filtering is the pattern that already works here.
- Scope to CentralNJ (and `msh/US/2/e/SJMesh/#` only if the separate Sep 3 todo is also being closed).
- Ask Badwolf first — we would be publishing to his broker again.
- Verify: repeat the Oct 25 test, then check packet rate and Malla row growth for an hour.

---

## 6. Standing rules for any MQTT change (from Charles's own hard rules + lessons)

- Back up `mosquitto.conf` first, with a dated `.bak-<reason>-<date>` name. **Verify a `.bak` file's contents before trusting its name** — a misleadingly named backup burned a whole test cycle on Aug 14.
- Edit with a **Python script, never `sed`** — sed has twice produced subtle, hard-to-spot damage (a stripped `#` broke the config; a non-unique anchor edited the wrong bridge block).
- Anchor edits to the specific `connection <name>` block. Bridge stanzas look nearly identical.
- Show the before/after diff and get an explicit OK before applying.
- Apply with `cd /opt/stacks/mqtt && docker compose restart mosquitto`, then read `docker logs --tail 30 mosquitto` for parse errors and bridge connects.
- Verify with a live `mosquitto_sub` on the specific topic for a full 30-60s (this is the one method that has never lied), plus a packet-rate check.
- **Never commit real broker passwords.** The live file contains real credentials for four remotes; the committed copy is redacted and must stay that way.
- Docker log rotation: cnjmesh1 and cnjmesh2 have the 10MB×3 cap, but it only applies to containers created after it was set. Two unrotated container logs have filled cnjmesh1's disk (37GB Mosquitto, 30GB mqtt-filter).

## 7. Related files

`cnjmesh1/sjmesh-relay/relay.py` · `cnjmesh1/configs/mosquitto-cnjmesh1.conf` (stale, §2) · `cnjmesh2/config/mosquitto.conf` · `docs/mosquitto-bridge-flood-fix.md` (Aug 4) · `docs/sjmesh-duplicate-block-handoff-2026-08-14.md` (ACL dead end) · `docs/sjmesh-bridge-backup.md` (stale, §2) · `docs/centralnj-discord-relay-investigation.md` (the live Oct 25 issue) · `watchdogs/sjmesh-relay-watchdog/` · session-log Aug 2, Aug 4-5, Aug 12-15, Aug 18, Sep 2-3.
