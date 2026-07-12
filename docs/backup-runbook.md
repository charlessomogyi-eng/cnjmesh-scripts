# CNJ Mesh — cnjmesh1 Backup Runbook

**Last updated:** 2026-07-12

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
