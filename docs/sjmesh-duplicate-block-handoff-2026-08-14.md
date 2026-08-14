# Handoff: Blocking a duplicate-packet-flooding node on cnjmesh1's Mosquitto broker

**Status as of Aug 14, 2026, ~17:40:** Problem NOT solved. Currently in a SAFE state (SJMesh bridge disabled, no ACL complexity active). An attempted fix (Mosquitto ACL) was tried thoroughly and confirmed NOT to work. Read this fully before attempting anything — it documents a real dead end so it isn't repeated.

---

## The original problem

One specific packet from an unrecognized node keeps getting endlessly republished into cnjmesh1's local Mosquitto broker via the **SJMesh bridge** (and, we later confirmed, also via the liamcottle and oceancounty bridges — they all subscribe to the same topic pattern). This has caused **93.3% of Malla's database (6,055,298 of 6,487,440 rows) to be duplicate bloat.**

- **Offending packet:** `mesh_packet_id 2144644198`
- **Originating node:** `!699a9390` (decimal `1771738000`) — not a locally-recognized node, confirmed by Charles and local community members
- **Gateway relaying it:** `!3c0b7b6e`
- **Topic:** `msh/US/2/e/CentralNJ/!699a9390` (and the `msh/US/NJ/2/e/CentralNJ/!699a9390` variant)
- **Rate:** ~once every 3.6 seconds, continuously, for at least 30 days (traced back further: confirmed present since **July 14, 2026**, predating the July 21 old-Pi disk-full crash — likely a minor contributing factor to that crash, not the dominant cause, which was a separate unrotated 37GB Mosquitto log)

**Confirmed via a real controlled test:** disabling the SJMesh bridge stops the duplicate. Re-enabling it resumes the duplicate. This has been proven multiple times tonight.

## The goal

Charles wants: (1) all three inbound bridges (sjmesh, liamcottle, oceancounty) to stay fully enabled — do NOT want to lose legitimate community mesh traffic — and (2) this ONE specific node's traffic blocked/filtered so it stops flooding the local broker and Malla's database.

## What was tried tonight — Mosquitto ACL approach (DID NOT WORK, do not repeat blindly)

**The theory (per Mosquitto's own official documentation):** give each bridge a `local_username` (bridges have no local identity by default, so per-user ACL rules can't apply to their traffic without one), then write an ACL file with `topic deny <bad-topic>` for that bridge's local identity, alongside `topic readwrite #` to preserve all other access. Per Mosquitto docs, `deny` rules always take precedence over broader allow rules regardless of file order — confirmed via official docs and GitHub issue discussion.

**What was actually built (all still technically present in config, but currently disabled/inactive):**
- `pwfile` has 3 new bridge-identity users: `sjmesh-bridge-local`, `liamcottle-bridge-local`, `oceancounty-bridge-local` (passwords generated randomly, stored only in the live pwfile — not in git, not written down elsewhere)
- Each bridge's connection block in `mosquitto.conf` had `local_username <bridge>-bridge-local` added
- `/opt/stacks/mqtt/config/aclfile` was created with `user` blocks for all 4 pre-existing local users (full access preserved) plus the 3 bridge identities (full access + explicit deny on the two bad topic variants)
- `acl_file /mosquitto/config/aclfile` was added to `mosquitto.conf` (currently REMOVED again — see current state below)

**Result: it did not work, tested twice.**
1. First test: only `sjmesh-bridge-local` had the ACL treatment. The bad packet still came through. Initially suspected this was because `liamcottle` (which also subscribes to the same CentralNJ topic) was still open and unfiltered — a plausible, reasonable theory.
2. **Second test, after applying the identical `local_username` + deny treatment to ALL THREE bridges (sjmesh, liamcottle, oceancounty):** the bad packet STILL came through — and critically, it was confirmed coming through **`sjmesh` itself**, the exact bridge that had its own `local_username` and matching deny rule correctly configured and verified with no config parse errors. This rules out "another open bridge" as the explanation. **This is real, doubly-confirmed evidence that Mosquitto's ACL deny mechanism does not apply to content arriving via a bridge's internal subscription, even with `local_username` set correctly per the documentation.** This may be a version-specific behavior or a genuine gap between Mosquitto's documentation and real implementation — not confirmed which, and not investigated further tonight.

Both tests used a full `docker compose up -d --force-recreate mosquitto` (not just restart) to rule out a config-reload caching issue. Neither worked.

**One real config mistake made and already fixed along the way, worth knowing about if picking through old backups:** a Python script used to uncomment the sjmesh block at one point had a boundary-detection bug that also stripped the `#` from an unrelated comment line ("# Bridge to MeshOmatic...") immediately following the sjmesh block, causing a Mosquitto config parse error ("Unknown configuration variable 'Bridge'"). This was caught and fixed in the same session by manually restoring that one `#`. If restoring from any `.bak` file below, check for this class of issue.

## Current live state (confirmed as of last check, Aug 14 ~17:40)

- **SJMesh bridge: DISABLED** (commented out in the live `mosquitto.conf`) — confirmed via `grep "^#*connection sjmesh$"` showing `#connection sjmesh`
- **`acl_file` directive: NOT currently active** in `mosquitto.conf` (`grep -c "acl_file"` returned `0`) — the ACL file still exists on disk but isn't being loaded
- **liamcottle and oceancounty bridges:** still have `local_username` lines added to their config blocks (harmless/inert since acl_file isn't active) — NOT reverted, still present
- **The 3 new bridge-identity users** (`sjmesh-bridge-local`, `liamcottle-bridge-local`, `oceancounty-bridge-local`) still exist in `pwfile` — harmless or unused currently
- **The `aclfile`** still exists on disk at `/opt/stacks/mqtt/config/aclfile` with all the deny rules built — just not currently referenced/active

**Backup files available on cnjmesh1** at `/opt/stacks/mqtt/config/`, in case a clean revert to any prior state is needed:
- `mosquitto.conf.bak-sjmesh-test` (Aug 12 21:54) — original working config, SJMesh enabled, no ACL complexity, no local_username lines
- `mosquitto.conf.bak-active-sjmesh` (Aug 14 16:51) — SJMesh enabled, taken right before an earlier disable — **do not assume this is a "disabled" backup, it is NOT, this caused confusion once already tonight**
- `mosquitto.conf.bak-preACL` (Aug 14 17:00) and `mosquitto.conf.bak-before-3bridge-acl` (Aug 14 17:38) — intermediate states during tonight's ACL attempts
- `pwfile.bak-before-acl` (Aug 14 17:00) — password file before the 3 bridge-identity users were added
- Older, unrelated-to-tonight backups also present: `.bak-20260719`, `.bak-preloopfix-20260805`, `.bak-preNJscope-20260804`, `.bak-presjmeshtopic-20260809`

**Recommended clean starting point for the next session:** restore `mosquitto.conf.bak-sjmesh-test`, which is the last known-good config with SJMesh enabled and zero ACL/local_username complexity — then decide fresh which approach to pursue (see options below). This wipes out tonight's incomplete ACL experiment cleanly.

## Real options going forward (none executed successfully tonight)

1. **A custom relay script (not yet built, most promising untried option):** instead of using Mosquitto's built-in bridge feature for SJMesh (and possibly liamcottle/oceancounty too), run a small script (Python, using `paho-mqtt` or similar) that connects to each remote broker as a normal client, receives every message, explicitly skips/drops the one bad topic in code, and republishes everything else to the local broker. Since this would be custom code fully under control, there's no dependency on Mosquitto's undocumented bridge-ACL behavior. This is genuinely buildable — has NOT been attempted yet tonight, was proposed but the session ended before building it.
2. **File a bug report / ask in the Mosquitto community** about whether `local_username` + ACL deny is expected to work for bridge-injected content — if this is a known limitation or a bug, there may be a different documented workaround (e.g., a different Mosquitto version, or a different directive) not found in tonight's research.
3. **Malla-side filtering** (previously considered, explicitly rejected by Charles) — would only protect Malla's database, not other tools sharing the same broker (Meshview, mesh-discord-shim, etc.), which Charles correctly flagged as insufficient given the flood hits the whole broker, not just Malla.
4. **Leave SJMesh permanently disabled** — explicitly rejected by Charles, contradicts the goal of community mesh reach.
5. **Accept the flood as a bounded, known cost** — floated once tonight in frustration, not a real endorsed plan; retention caps the damage but doesn't stop the underlying waste.

## Other context, for completeness

- Charles reached out to SJMesh's operator (Discord user DeadGuise) as a courtesy on Aug 12 — he checked his side, doesn't see the node or bad packets in his own logs/list. Confirms the fix needs to happen on cnjmesh1's end regardless of anything on SJMesh's side.
- A separate, unrelated fix WAS successfully completed tonight (Aug 12) and IS working: Malla's `default_channel_key` was missing entirely, causing ~99.9% of CentralNJ channel traffic to be logged but undecodable (`UNKNOWN_APP`). The real PSK was added to `/opt/stacks/malla/config.yaml`, confirmed live in logs (`✅ Successfully decrypted...`). This is unrelated to tonight's ACL problem and does not need to be redone.
- Full narrative history of the original duplicate-packet discovery (root-causing, the live tests that identified SJMesh as the source, etc.) is in `session-log.md`, Aug 12 entry "MAJOR FINDING."

## Guardrails to follow (Charles's standing rules, several relevant lessons from tonight specifically)

- Every command names its target host (cnjmesh1).
- Python scripts for complex config edits, NOT sed — sed has caused real, hard-to-spot bugs tonight (partial multi-line comment blocks, boundary-detection errors).
- **Verify before trusting any `.bak` filename's implied meaning** — a misleadingly-named backup (`mosquitto.conf.bak-active-sjmesh`, which contained the ENABLED state despite being restored as if it were a "safe/disabled" checkpoint) caused real confusion and wasted a full test cycle tonight. Always confirm actual file contents, don't infer from the name.
- Test with a live, continuous `mosquitto_sub` watcher on the specific bad topic (`msh/US/2/e/CentralNJ/!699a9390`) after any config change — this has been the one fully reliable verification method all along. Always let it run a full 30-60 seconds before concluding silence = success.
- State the plan and get explicit approval before production changes.
- Claude authors and pushes all git commits.
