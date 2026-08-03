# Malla Fix Implementation Plan — cnjmesh1 (drafted Aug 2, 2026, for execution Aug 3)

## Goal
Fix malla.cnjmesh.me's slowness/instability using the TWO documented config features (Anubis deferred):
1. **`data_retention_hours`** — auto-prune old records hourly, permanently caps DB growth (the real root cause of the bloat).
2. **`MALLA_WEB_COMMAND=malla-web-gunicorn`** — multi-worker WSGI server, fixes the single-threaded-Flask blocking that causes the "up and down."

## Design principles (why the order matters)
- Fresh DB backup FIRST (the July 31 backup is stale; DB changed since).
- Retention BEFORE gunicorn — enable pruning, let it run one cycle, so gunicorn starts against a smaller settling DB.
- ONE change at a time, VERIFY between each — if something breaks, you know which change did it.
- PRESERVE the raw-topic override every edit: `MALLA_MQTT_TOPIC_PREFIX=msh` + `MALLA_MQTT_TOPIC_SUFFIX=/US/#`. If these get dropped, Malla stops seeing data.
- Do this on cnjmesh1 (gated instance) FIRST. Prove it here before touching public malla2 (Pi Zero) another day.
- All Malla config on cnjmesh1 lives in `/opt/stacks/mqtt/` (compose.yaml + compose.override.yaml). Malla data volume: `mqtt_malla_data` -> `/var/lib/docker/volumes/mqtt_malla_data/_data/meshtastic_history.db`.

---

## PRE-STEP — Reboot first? (Charles said he'd reboot cnjmesh1 tomorrow)
If doing the planned reboot, do it BEFORE this Malla work (clean baseline), watch all containers + systemd services come back, then run the health-check sweep (`docs/health-check-plan-aug2026.md`), THEN start below. If not rebooting, just proceed.

---

## STEP 0 — Fresh backup of the Malla DB (cnjmesh1)
The safety net. Do NOT skip — Steps 2+ enable deletion of old rows.
```
docker exec mqtt-malla-web-1 python3 -c "import sqlite3; s=sqlite3.connect('/app/data/meshtastic_history.db'); d=sqlite3.connect('/app/data/malla-backup-$(date +%Y%m%d).db'); s.backup(d); d.close(); s.close(); print('backup done')"
sudo cp /var/lib/docker/volumes/mqtt_malla_data/_data/malla-backup-$(date +%Y%m%d).db /home/somog/backups/
sudo chown somog:somog /home/somog/backups/malla-backup-$(date +%Y%m%d).db
ls -lh /home/somog/backups/malla-backup-*.db
df -h /   # confirm room — backup is ~1.7GB
```
Verify: a ~1.7GB `malla-backup-YYYYMMDD.db` exists in /home/somog/backups/. (Also: still move an older copy OFF-Pi when convenient — the backup gap todo.)

---

## STEP 1 — See current compose config (cnjmesh1)
```
cat /opt/stacks/mqtt/compose.yaml
echo "=== override ==="
cat /opt/stacks/mqtt/compose.override.yaml
```
Confirm where the `malla-web` and `malla-capture` services + their env live. The override currently should have ONLY the malla-capture topic settings (we cleaned it Aug 2). Paste both to Claude before editing so the exact edit is correct for the actual file layout.

---

## STEP 2 — Enable data retention (auto-prune) — capture service (cnjmesh1)
`data_retention_hours` is honored by the CAPTURE process (it runs the hourly cleanup). Add the env var to the `malla-capture` service. Decide window first:
- 30 days = `720`
- 60 days = `1440`
(Recommend 60d/1440 — matches the retention discussion Aug 1; keeps 2 months of history.)

Add to malla-capture's environment (via override.yaml, alongside the existing topic vars). Example resulting `/opt/stacks/mqtt/compose.override.yaml`:
```
services:
  malla-capture:
    environment:
      - MALLA_MQTT_TOPIC_PREFIX=msh
      - MALLA_MQTT_TOPIC_SUFFIX=/US/#
      - MALLA_DATA_RETENTION_HOURS=1440
```
(Claude will supply the exact tee/edit command once Step 1 output confirms the file. BACK UP the override first: `sudo cp .../compose.override.yaml .../compose.override.yaml.bak-preretention`.)

Apply (recreate capture only, preserves web):
```
cd /opt/stacks/mqtt && docker compose up -d malla-capture
```
Verify it started clean and picked up retention:
```
docker logs --tail 20 mqtt-malla-capture-1 2>&1 | tail -20
```
Look for: connects to broker, subscribes to `msh/US/#` (raw — confirms override preserved), and ideally a data-cleanup / retention log line. The cleanup runs hourly in the background — first prune may take up to an hour to fire.

**LET RETENTION RUN before Step 3** — ideally give it an hour (or just proceed; not strictly required). Optional: after it has run, a one-time VACUUM (Malla stopped) will reclaim the freed space and shrink the file (same procedure as Aug 1: stop capture+web, VACUUM via docker run against the volume, restart). VACUUM is optional now — retention caps GROWTH regardless; VACUUM just reclaims existing slack.

---

## STEP 3 — Switch web UI to gunicorn (cnjmesh1)
The documented, supported way — an env var on the `malla-web` service. NOT the manual pip-install we did at 5am (that was non-persistent and wrong).

Add to the `malla-web` service environment:
```
MALLA_WEB_COMMAND=/app/.venv/bin/malla-web-gunicorn
```
Optional tuning (cnjmesh1 is a 4-core Pi but memory-tight — start conservative):
```
MALLA_GUNICORN_WORKERS=2
MALLA_GUNICORN_THREADS=2
```
(2 workers x 2 threads is a reasonable start on a RAM-constrained box — more workers = more RAM. Claude will confirm exact placement from Step 1's compose layout. BACK UP the file being edited first.)

Apply (recreate web only):
```
cd /opt/stacks/mqtt && docker compose up -d malla-web
```
Verify gunicorn is actually running (not the Flask dev server):
```
docker logs --tail 25 mqtt-malla-web-1 2>&1 | tail -25
```
Look for: gunicorn startup lines / worker boot messages, and NO "development server" warning. Then test locally:
```
sleep 10 && curl -sS -m 60 -o /dev/null -w "malla: %{http_code} in %{time_total}s\n" http://localhost:5008/
```
First cold load may still be slow (the stats query itself), BUT the win is: a second concurrent request now WON'T block behind it. Test that — fire two curls at once and confirm neither hangs indefinitely:
```
curl -sS -m 60 -o /dev/null -w "A: %{http_code} %{time_total}s\n" http://localhost:5008/ &
curl -sS -m 60 -o /dev/null -w "B: %{http_code} %{time_total}s\n" http://localhost:5008/ &
wait
```

---

## STEP 4 — Confirm public access + warm-cache interaction (cnjmesh1)
```
curl -sS -m 60 -o /dev/null -w "public malla: %{http_code} in %{time_total}s\n" https://malla.cnjmesh.me/
```
Also: the `malla-warmcache.timer` we installed Aug 1 may now be REDUNDANT or even counterproductive with gunicorn (multiple workers + warmcache could cause concurrent recompute). Reassess: with gunicorn handling concurrency, decide whether to keep or remove the warmcache timer. Check `systemctl status malla-warmcache.timer`.

---

## STEP 5 — Document + push (Claude does this)
Once verified: update session-log + install-map (re-run collect-inventory.sh on cnjmesh1), note retention window chosen, gunicorn worker/thread counts, and warmcache decision. Push with the in-session token.

---

## ROLLBACK (if anything breaks)
- Backups of both edited files exist (`.bak-preretention`, etc.) — restore and `docker compose up -d malla-capture malla-web`.
- Fresh DB backup from Step 0 exists if data is ever affected (retention only deletes OLD rows, so risk is low, but the backup is there).
- Reverting gunicorn = remove `MALLA_WEB_COMMAND` env, recreate malla-web (falls back to Flask dev server = current behavior).

## NOT doing tomorrow (deferred)
- Anubis (bot-blocking) — deferred per Charles. Revisit for the PUBLIC malla2 after checking its access logs for scraper load.
- malla2 (Pi Zero) changes — prove the fix on cnjmesh1 first.
- Docker log rotation on cnjmesh1 — still a good idea (needs daemon restart) but separate from this.
