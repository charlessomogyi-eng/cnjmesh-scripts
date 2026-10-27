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

cnjmesh2 is a **separate** stack (own Mosquitto + Malla in `~/meshtastic-mqtt`, own broker; malla2 reads `mosquitto` inside its own compose project, not cnjmesh1). Live config verified Oct 25: one connection `meshtastic_centnj` to `mqtt.meshtastic.org` (clientid `cnjmesh2-bridge`, same connection both directions, so loop protection applies):
- **in:** `msh/US/2/e/CentralNJ/#`, `msh/US/NJ/2/e/CentralNJ/#`, plus `CentNJ-MQTT` (both root variants). CentNJ-MQTT is a channel Charlie said to drop on cnjmesh1 (Aug 4); it is still pulled on cnjmesh2.
- **out:** `msh/US/2/e/CentralNJ/#` (CentralNJ only), **plus a dormant path:** `topic # out 0 filtered/msh/US/ msh/US/NJ/`. By Mosquitto's prefix syntax (as I understand it, not tested) this publishes anything on the *local* topic `filtered/msh/US/...` to the public broker as `msh/US/NJ/...`. The only thing that writes `filtered/msh/US/...` is the **oktomqtt filter, currently stopped** (`docker stop`, restart policy `unless-stopped`). **If oktomqtt is ever restarted** (it was kept as a "volume-reduction safety valve", and a full `docker compose up -d` in `~/meshtastic-mqtt` revives it), it would begin publishing filtered traffic to the public broker. Know that before running a bare `compose up -d` on cnjmesh2. [I]

---

## 2. Repo copies now match live (synced Oct 25 2026 15:30) [V]

Before Oct 25 the committed `cnjmesh1/configs/mosquitto-cnjmesh1.conf` was stale: it had an active `connection sjmesh` and a trailing `connection sjmesh-bridge` with `topic msh/US/2/# out 0`, and lacked the LongFast lines. Restoring it would have re-created the Aug 5 loop. **Both configs in the repo are now verbatim copies of what is live** (cnjmesh1 file mtime Aug 15 21:48; cnjmesh2 as pasted). Only `oceancounty` and `meshomatic` passwords are redacted (see below). `docs/sjmesh-bridge-backup.md` is marked STALE.

**Still a trap inside the live file:** the commented-out `#connection sjmesh` block (it includes `#topic msh/US/2/e/SJMesh/# both 0`). **Do not un-comment it while `sjmesh-relay.service` is running.** The native bridge would send local CentralNJ traffic to SJMesh while the relay pulls it back in = the Aug 5 loop again. It is also the obvious-looking way to "restore the outbound path", which is why it is a trap.

**Credentials:** shared/public community logins are committed as-is (`meshdev`/public Meshtastic, `uplink`/Liam Cottle, `meshuser`/SJMesh: also published on cnjmesh.me). The MeshOmatic one is a personal per-account token and the Ocean County one is not shown published anywhere; both stay `REDACTED` because a public repo cannot be un-leaked cheaply (the Aug 30 webhook incident needed `git filter-repo`). Charlie can flip that.

**Backups on cnjmesh1, `/opt/stacks/mqtt/config/` (listing Oct 25):** `mosquitto.conf.bak-20260719`, `bak-preNJscope-20260804`, `bak-preloopfix-20260805`, `bak-presjmeshtopic-20260809`, `bak-sjmesh-test` (Aug 12), `bak-active-sjmesh` (Aug 14, **SJMesh enabled**, despite the name), `bak-preACL`, `bak-before-3bridge-acl`, `bak-longfasttest-20260815` (the last config before LongFast was added), plus `pwfile.bak-before-acl` and a stray `mossquitto.conf2` (typo, Jan 2026, 338 bytes). Live has no `acl_file`, no `local_username`, no `sjmesh-bridge`. The 3 bridge-identity users and the `aclfile` mentioned in the Aug 14 handoff were not in this listing (no `aclfile` file in the directory); `pwfile` was last touched Aug 14 17:37, so those users may still be inside it. [V listing, I for pwfile contents]

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
- No permission gate: `mqtt.sjmesh.net` uses the published community login (it is on cnjmesh.me), the old bridge published to it for months, and `sjmesh-relay` already holds a session there. Nobody asked us to stop (the Aug 12 contact with the SJMesh operator only confirmed the flood was on our side). A courtesy heads-up after it works is enough. [Corrected Oct 26 2026: this line used to say "Ask Badwolf first"; that was caution, not a request from anyone.]
- **Built Oct 26 2026 (`cnjmesh1/sjmesh-relay/relay.py`, off by default, `OUTBOUND_ENABLED=1` turns it on):** outbound forwards only our gateways' topics (CJG2 `!9ea3e8d4`, KPN6 `!69841fe0`, CJG1 `!0aca423c`), never retained; inbound drops those same topics, so SJMesh's echo of our own publish cannot re-enter the local broker; 120/min cap; kill switch = remove the variable and restart. Offline loop test: `cnjmesh1/sjmesh-relay/test_relay_logic.py` (200 packets give exactly 200 outbound, 0 republished locally). The echo from SJMesh's broker is also the proof that it accepted the publish (logged as "echoed our packet").
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

## 6b. Relay drift found Oct 25 (open)

`diff` of live `/opt/sjmesh-relay/relay.py` against the repo copy: the **repo blocks 3 nodes, live blocks 2.** Live is missing both `!db51bb30` topic entries (`msh/US/2/e/CentralNJ/!db51bb30` and the `msh/US/NJ/...` variant); everything else differs only by blank lines. `!db51bb30` (decimal 3679566640) is one of the three Aug flood/loop nodes. Git history cannot say which side is right (repo history is a single squashed commit). Either the live file never got the third entry, or the repo copy was written from notes. **Check** whether that node is flooding now (Malla query in `known-issues.md`); if so, add the two lines to live `relay.py` and restart `sjmesh-relay`. Do not just overwrite the repo with live before deciding.

## 7. Related files

`cnjmesh1/sjmesh-relay/relay.py` · `cnjmesh1/configs/mosquitto-cnjmesh1.conf` (stale, §2) · `cnjmesh2/config/mosquitto.conf` · `docs/mosquitto-bridge-flood-fix.md` (Aug 4) · `docs/sjmesh-duplicate-block-handoff-2026-08-14.md` (ACL dead end) · `docs/sjmesh-bridge-backup.md` (stale, §2) · `docs/centralnj-discord-relay-investigation.md` (the live Oct 25 issue) · `watchdogs/sjmesh-relay-watchdog/` · session-log Aug 2, Aug 4-5, Aug 12-15, Aug 18, Sep 2-3.
