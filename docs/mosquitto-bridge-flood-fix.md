# cnjmesh1 Mosquitto Bridge Flood Fix — EXECUTION PLAN (for Sonnet)
# Drafted Aug 4, 2026. ROOT CAUSE FOUND for the whole multi-week instability.

## THE ROOT CAUSE (confirmed with live data — this supersedes the "cut Malla retention" approach)
cnjmesh1's Mosquitto has THREE inbound bridges pulling the ENTIRE US/global Meshtastic firehose into the local broker:
- `oceancounty`: `topic msh/US/# in 0`  (all US)
- `liamcottle`:  `topic msh/# in 0`      (ENTIRE GLOBAL Meshtastic MQTT)
- `sjmesh`:      `topic msh/US/# in 0`  (all US)

Evidence: 1.63M packets/24h, 99.5% (1.62M) are UNKNOWN_APP (foreign encrypted packets Malla can't decode but stores anyway). Top senders / topics show foreign channels flooding in: `msh/US/2/e/SJMesh/...`, `msh/US/2/e/GraveYard/...` (a network Charles doesn't even recognize), etc. This is why: (a) Malla DB exploded to 9.4M rows / 3.1GB and queries hit 149s; (b) disk kept filling; (c) the whole environment got unstable "in the past few weeks." NOTE: git only goes back ~4 weeks so it is NOT authoritative on how/when these broad topics were added — do not claim git proves history. Charles does not recall ever setting `msh/#`/`msh/US/#` inbound and it doesn't match cnjmesh2's disciplined scoping.

## THE REFERENCE: cnjmesh2 does it RIGHT (narrow, named channels)
cnjmesh2's mosquitto.conf subscribes only to named channels, e.g. `msh/US/2/e/CentralNJ/#`, `msh/US/NJ/2/e/CentralNJ/#` — never a wildcard firehose. That's why cnjmesh2 stays lean (68MB DB). We bring cnjmesh1's INBOUND bridges in line with this discipline.

## CHARLES'S DECISION (locked in)
- **KEEP** the 3 inbound bridges (oceancounty, liamcottle, sjmesh) but **SCOPE them to CentralNJ + NJ only** — replace each broad `msh/US/#`/`msh/#` inbound line with:
  ```
  topic msh/US/2/e/CentralNJ/# in 0
  topic msh/US/NJ/2/e/CentralNJ/# in 0
  ```
- **Ignore/DROP** any CentNJ-MQTT topics (Charles said drop that channel).
- Do NOT add SJMesh/OceanCounty-specific channel topics for now (Charles: "leave it alone" — if their named topics aren't there naturally, fine). Bridges are kept (not removed) so the structure exists if he wants to add specific neighbor channels later.
- **LEAVE OUTBOUND BRIDGES UNCHANGED:** `meshtastic_public` (out CentralNJ), `meshomatic` (out meshcore), and the bottom `sjmesh-bridge` (out `msh/US/2/#`). These publish OUT, are not the flood, don't touch them.
- Everything else (listeners, allow_anonymous, password_file, per-bridge creds/clientid/insecure flags) UNCHANGED.

## EXACT EDIT — the 3 inbound bridge topic lines change as follows:
- oceancounty: `topic msh/US/# in 0`  ->  two CentralNJ lines above (keep its `bridge_insecure true`)
- liamcottle:  `topic msh/# in 0`     ->  two CentralNJ lines above
- sjmesh:      `topic msh/US/# in 0`  ->  two CentralNJ lines above
Preserve each bridge's other lines exactly (connection/address/remote_username/remote_password/clientid/cleansession/try_private/notifications/bridge_attempt_unsubscribe/bridge_protocol_version/restart_timeout, and oceancounty's bridge_insecure).

## EXECUTION STEPS (Sonnet — host = cnjmesh1)
1. Backup already exists: `/opt/stacks/mqtt/config/mosquitto.conf.bak-preNJscope-20260804`. Confirm it's there before editing.
2. Build the new mosquitto.conf. Use a Python script approach (cat > /tmp/fix.py) NOT sed — per Charles's hard rule. Read the file, replace ONLY the three inbound `topic ... in 0` lines with the two-line CentralNJ+NJ block each, write it back. Show Charles the full before/after (or a diff) and get explicit OK before applying.
3. Apply: the config is bind-mounted into the mosquitto container (`./config:/mosquitto/config`). Restart mosquitto to reload:
   `cd /opt/stacks/mqtt && docker compose restart mosquitto`
   (restart is fine here — mosquitto reads config on start. Verify it comes back: `docker logs --tail 30 mosquitto` — watch for bridge connection lines and NO config parse errors.)
4. VERIFY THE FLOOD STOPPED (the payoff): after ~5-10 min, re-run the 24h ingest check:
   ```
   docker exec mqtt-malla-web-1 python3 -c "
   import sqlite3, time
   c = sqlite3.connect('/app/data/meshtastic_history.db')
   hr_ago = time.time() - 3600
   print('packets last 1h:', c.execute('SELECT COUNT(*) FROM packet_history WHERE timestamp > ?',(hr_ago,)).fetchone()[0])
   print('=== topics last 1h ===')
   for row in c.execute('SELECT topic, COUNT(*) ct FROM packet_history WHERE timestamp > ? GROUP BY topic ORDER BY ct DESC LIMIT 15',(hr_ago,)):
       print(f'{row[1]:>7,}  {row[0]}')
   c.close()"
   ```
   SUCCESS = packets/hour drops massively (from ~68K/hr toward a few hundred/hr of real CentralNJ traffic), and topics are almost all CentralNJ, no more GraveYard/SJMesh/foreign firehose.

## THEN — clean up the Malla-side aftermath (the flood already bloated the DB)
The DB is 9.4M rows / 3.1GB from weeks of flooding. Now the flood is stopped, retention will actually catch up. Two things:
5. Retention is currently set to 720h (30 days) via compose.override.yaml. With the flood gone, revisit: 30d of REAL CentralNJ traffic will be tiny, so 30d (or even longer) is now totally fine — the flood was the problem, not the retention window. Consider setting retention back to a comfortable value (Charles can decide; 30-90d all fine now).
6. VACUUM the DB ONCE to reclaim the ~3GB and speed queries, now that the junk will age out. Procedure (Malla stopped):
   ```
   cd /opt/stacks/mqtt && docker compose stop malla-capture malla-web
   docker run --rm -v mqtt_malla_data:/app/data ghcr.io/zenitram/malla:latest python3 -c "import sqlite3,time; c=sqlite3.connect('/app/data/meshtastic_history.db'); t=time.time(); c.execute('VACUUM'); c.close(); print(f'done {time.time()-t:.1f}s')"
   cd /opt/stacks/mqtt && docker compose up -d
   ```
   (VACUUM on 3GB will take a while — was ~13-24 min in prior sessions. Let it run.)
   NOTE: retention deletes rows but the old foreign junk (rows already stored) only ages out over the retention window OR can be deleted directly by topic. If Charles wants the foreign junk GONE immediately rather than aging out, an option is a targeted DELETE of non-CentralNJ topics before the VACUUM — but confirm with him first; simplest is just let retention age it out + VACUUM reclaims as it goes.
7. Re-test query speed: `curl -sS -m 120 -o /dev/null -w "malla: %{http_code} in %{time_total}s\n" http://localhost:5008/` — should now be dramatically faster once the table shrinks.

## DOCUMENT + PUSH (Sonnet does this)
- Commit the SANITIZED current + new mosquitto.conf to git (redact passwords — replace remote_password values with REDACTED, like the existing example file). This finally gets the real bridge config into git (only a sanitized example was there before).
- Update session-log with: root cause found (inbound firehose bridges), the fix applied, before/after packet rates, retention/VACUUM outcome.
- Update install-map if bridge topology description changed.

## GUARDRAILS (Charles's hard rules — Sonnet must follow)
- Every command block names its host (cnjmesh1).
- Python not sed for the config edit.
- Show before/after and get explicit OK before applying the config change.
- Claude pushes git (Charles provides token per session).
- Don't touch protected services (Malla/meshview) beyond the documented restart/VACUUM steps.
- NEVER commit real passwords to git — redact.

## WHY THIS IS THE REAL FIX (context for Sonnet)
Everything we chased for days (Malla slowness, disk-fill, gunicorn, retention tuning, the overnight outages/530s) is very likely DOWNSTREAM of this one thing: three bridges inhaling the entire US/global Meshtastic firehose into a Pi-hosted broker. Gunicorn + retention were treating symptoms. THIS is the offender Charles asked us to find ("I want to remove the offender, not just reduce packets"). Fix this first, then confirm whether the outages/slowness resolve — they very likely will.
