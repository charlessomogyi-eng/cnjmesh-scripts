# CNJ Mesh — cnjmesh1 Backup Runbook

> **Start with `docs/backup-guide.md`** (Oct 23 2026): the current, all-Pi guide with the audit method and the extra archive. This runbook is the older cnjmesh1-only detail.

**Last updated:** 2026-09-02

## Purpose
Ad hoc backup of cnjmesh1 configs, compose files, and databases so a bad
config edit, upgrade, or hardware change can be recovered from without
rebuilding the hub from scratch.

## What's Covered
- `/opt/stacks/` — mqtt, meshcore-hub, mesh-discord-shim compose files and configs
- `/opt/meshing-around/`
- `/opt/graywolf-discord/`
- `/etc/cloudflared/config.yml`
- `/var/lib/graywolf/graywolf.db` (Graywolf APRS PTT config + state)
- `/opt/stacks/mesh-discord-shim/data/seen_nodes.db`
- Postgres dump via `pg_dumpall` (mesh-mqtt-pg-collector's DB), if a Postgres
  container is running
- `/opt/stacks/grafana/` if present (dashboards/config)
- **Malla database** (`meshtastic_history.db`, Docker named volume, live
  WAL-mode SQLite) — consistency-safe snapshot via Python's `sqlite3.backup()`
  API, added Aug 6, 2026
- **CoreScope database** (`meshcore.db`, same named-volume/WAL situation as
  Malla) — added Aug 6, 2026
- **aprs-tnc-web MySQL database** via `mysqldump --single-transaction` —
  added Aug 6, 2026
- **Archive verification pass** (step 10) — confirms all expected components
  are actually present in the final archive and pass a minimum-size sanity
  check, added Aug 11, 2026 (several steps above only warn-and-continue on
  failure, e.g. a Postgres/MySQL auth issue, so this catches a silently
  incomplete backup rather than just a script exiting 0)

## What's NOT Covered (by design)
- Full SD card image — do this separately with `dd` or `rpi-clone` before
  major OS-level changes or roughly monthly. Not part of this script.
- Docker volumes not bind-mounted to `/opt/stacks/` — if a service stores
  data purely in an unmounted Docker volume, it won't be picked up here.
  Check `docker inspect <container>` if in doubt.

## Script
`cnjmesh1-backup.sh` — lives in this repo under `scripts/`.

Run manually on cnjmesh1:
```bash
sudo ./cnjmesh1-backup.sh
```

Output: `/home/somog/backups/cnjmesh1-backup-YYYY-MM-DD_HHMM.tar.gz`

## Pulling to Laptop / OneDrive
From your laptop:
```bash
scp somog@10.0.0.181:/home/somog/backups/cnjmesh1-backup-*.tar.gz .
```
Then upload the `.tar.gz` to OneDrive manually.

## When to Run
No fixed schedule — ad hoc is fine, but run it:
- Before editing configs (mosquitto.conf, cloudflared config, compose files)
- Before package/OS upgrades
- Before USB device or hardware changes
- Before any cnjmesh3 migration work (KPR2 serial move, etc.)
- Roughly monthly if nothing risky has happened otherwise

## Restore Process (manual)
1. Extract the archive: `tar -xzf cnjmesh1-backup-<timestamp>.tar.gz`
2. Copy relevant subfolder contents back to their original paths
   (e.g. `opt-stacks/mqtt/` → `/opt/stacks/mqtt/`)
3. For Postgres: `cat pg_dumpall.sql | docker exec -i <postgres_container> psql -U postgres`
4. Restart affected containers/services:
   `sudo docker compose up -d` in the relevant `/opt/stacks/*` directory
5. Verify service health (check logs, check public hostnames resolve)

## Known Gaps / Future Work
- Not yet automated as a cron job — intentional, ad hoc for now (see todo #5
  in CLAUDE_CONTEXT.md: "meshcore-packet-capture health check" is separate
  from this).
- No automated OneDrive upload — manual scp + upload for now.
- Full SD card image process not yet documented — add if this becomes routine.


## Update 2026-10-13: SD-card image — attempted Sep 2-3, completion UNCONFIRMED (from ops/APRS/GitHub handoff)
**[S]** On Sep 2-3 a full SD-card image of cnjmesh1 was started: `dd` of `/dev/mmcblk0` piped through `gzip` over SSH, streamed to Charles's laptop so the Pi's own disk isn't used, after a sudoers prep step on cnjmesh1. The PowerShell stream reached the SSH password prompt; **the output filename, location, size and whether it completed are unknown.** The exact sudoers rule text and file are also unknown and **not documented anywhere in the repo** — check `/etc/sudoers.d/` on cnjmesh1 before assuming what is there. Restore procedure: not written. Per the handoff, cnjmesh1's root filesystem was 58 G with 35 G used (63%) and Charles plans a new 64 GB card. The lines above ("not yet documented") remain accurate until this is confirmed.
