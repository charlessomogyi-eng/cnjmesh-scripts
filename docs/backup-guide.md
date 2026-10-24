# CNJ Mesh backup guide

**Last updated:** 2026-10-23 (written after the Oct 23 backup audit of cnjmesh1 and cnjmesh3)
**Owner:** Charlie (K2GIA). This is the one place that explains what is backed up, how, and how to keep it honest.

> **PRIVATE DATA WARNING.** Backup archives contain secrets (container environment variables, `.env` files,
> database dumps, the weather bot config). They live only on the Pis, Charlie's laptop and OneDrive.
> **Never commit an archive to this public repo.** The scripts themselves contain no secrets and are safe in git.

---

## 1. The three layers of protection

| Layer | What it protects | Where it lives | Status |
|---|---|---|---|
| **Git repo** (this repo, public) | Scripts, patches, docs, install maps, redacted configs | GitHub `charlessomogyi-eng/cnjmesh-scripts` | Active. Contains **no** secrets or live data. |
| **Backup archives** (this guide) | Live configs with secrets, databases, container run-state, systemd units | Pi `~/backups` then laptop `Documents\cnjmesh-backups` then OneDrive | Manual runs; see section 3 |
| **SD-card image** | The whole Pi, bootable | OneDrive: `cnjmesh1-sdcard-20260902.img.gz` (2.4 GB) | Exists; **integrity not verified**; cnjmesh2/cnjmesh3 have none |

Radio settings and identity keys live **on the radios** (Observer RAK4631, KPR repeaters, bot radio), not on any Pi.
No Pi backup contains them. Keep a written record of their settings separately.

## 2. The scripts (with versions)

Version = date of the last change in git. Check the current one with `git log -1 --format=%ad --date=short -- <file>`.

| Script | Runs on | What it makes | Version |
|---|---|---|---|
| `scripts/cnjmesh1-backup.sh` | **cnjmesh1** | `~/backups/cnjmesh1-backup-<date>.tar.gz` (~180 MB), with a built-in verification step | 2026-08-11 (verification added; created 2026-07-12) |
| `scripts/cnjmesh1-extra-backup.sh` | **cnjmesh1** | `~/backups/cnjmesh1-extra-<date>.tar.gz` (~125 MB, mode 600, owned by somog) | 2026-10-23 (created) |
| `scripts/cnjmesh-backup.sh` | **cnjmesh3** (host-aware; **never run on cnjmesh2**) | `~/backups/cnjmesh3-backup-<date>.tar.gz` (~0.6 MB) | 2026-10-23 (bridge data + Tilly fork added; created 2026-07-26) |
| `scripts/pull-cnjmesh1-backup.ps1` | **Charlie's Windows laptop** | Copies the latest archives from the Pis into `Documents\cnjmesh-backups` | 2026-10-23 (extra archive + real Documents folder; created 2026-07-12) |

**cnjmesh2 has no backup archive, by design.** A full backup overloaded the Pi Zero 2 W on 2026-07-26 (load above 11,
unresponsive). Its config is in git under `cnjmesh2/config/`. A small config-only script is still a to-do (section 7).

### What each archive contains

**`cnjmesh1-backup` (main):** `/opt/stacks` (compose files, configs, `.env`), `/opt/meshing-around`, `/opt/graywolf-discord`,
`/etc/cloudflared/config.yml`, Graywolf DB (plain copy, see section 5), mesh-discord-shim `seen_nodes.db` (plain copy),
Postgres (`pg_dumpall`), **Malla DB** and **CoreScope DB** (SQLite online backup), aprs-tnc-web MySQL (`mysqldump --single-transaction`),
Grafana if present. Step 10 checks every expected piece is in the archive and the DB files are not suspiciously small;
on failure the archive is renamed `.FAILED-VERIFICATION`.

**`cnjmesh1-extra`:** every other live SQLite database copied with SQLite's online-backup API and checked with
`PRAGMA quick_check` (Graywolf, shim `seen_nodes.db`, meshing-around, Meshview `packets.db`, **MeshCore Hub collector DB**
inside Docker volume `meshcore-hub_data`, any DB under `/opt/meshcore-bot`); the weather bot folder `/opt/meshcore-bot`
(patched code) plus any config named in its systemd unit (**the live bot config is `/etc/meshcore-bot/config.ini`, outside `/opt`**);
Meshview folder; CoreScope `/home/somog/meshcore-data` config (the DB itself is in the main archive); Hub MQTT/observer volumes
(size-guarded); systemd units, the journald drop-in, crontabs, OS and Docker lists.

**`cnjmesh3-backup`:** user-installed systemd units, `docker inspect` of every container (this is how the bridge is recreated,
its image `meshcore-mqtt:local` is built locally), `/etc/cloudflared`, watchdog and peer-check dirs, `/opt/meshcore-packet-capture`,
`/opt/meshcore-mqtt`, `/home/somog/meshcore-bridge-data` (bridge SQLite + WAL, idle since Jul 28),
`/home/somog/meshcore-mqtt-tilly` (Tilly's bridge fork with our changes).

## 3. How to run a backup (all Pis, then pull to the laptop)

Run before risky changes and roughly monthly. Each command says whether it finishes on its own.

**cnjmesh1** (finishes on its own, a few minutes; ~20 GB free needed is comfortable, the extra script aborts under ~3 GB):

    cd ~/cnjmesh-scripts && git pull && sudo bash scripts/cnjmesh1-backup.sh 2>&1 | tail -40
    sudo bash scripts/cnjmesh1-extra-backup.sh 2>&1 | tail -50
    ls -lh ~/backups | tail -5

Look for "Backup complete and verified" (main) and "Extra backup complete and verified" (extra). Any `FAILED`, `MISSING` or
`WARNING` line means do not trust that archive until it is explained.

**cnjmesh3** (finishes on its own, under a minute; downloads the current script so a stale local clone cannot matter):

    curl -fsSL https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/scripts/cnjmesh-backup.sh -o /tmp/cnjmesh-backup.sh && sudo bash /tmp/cnjmesh-backup.sh 2>&1 | tail -40; ls -lh ~/backups | tail -3

This script has no verification step: check that the output lists every folder in the cnjmesh3 list above.

**Then pull to the laptop** (section 4).

## 4. The laptop pull script (`pull-cnjmesh1-backup.ps1`)

- **Location on the laptop:** `C:\Users\charl\Documents\scripts\pull-cnjmesh1-backup.ps1`, run from the desktop shortcut
  "pull-cnjmesh1-backup - Shortcut".
- **Destination:** the real Documents folder `Documents\cnjmesh-backups` (OneDrive-synced, so it uploads automatically).
  Since 2026-10-23 the script finds Documents with `[Environment]::GetFolderPath("MyDocuments")`; before that it assumed
  `%USERPROFILE%\OneDrive\Documents`.
- **What it pulls:** for each entry in its `$Pis` list it finds the **newest** file matching `<prefix>-*.tar.gz` and copies it
  with `scp`: `cnjmesh1-backup`, `cnjmesh1-extra`, `cnjmesh3-backup`. If the newest file is already in the folder it skips it.
  cnjmesh2 is not in the list (nothing to pull).
- **Passwords:** it asks for the Pi login password for every `ssh` and `scp` step (about two per archive). It does not store them.
  (Setting up SSH keys would make it unattended; not done.)
- **Execution Policy prompt:** the shortcut shows "Execution Policy Change ... Do you want to change the execution policy?".
  Answer **Y**. It is Charlie's own script. If it ever refuses ("blocked", "not digitally signed"), run once in PowerShell:
  `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\charl\Documents\scripts\pull-cnjmesh1-backup.ps1"`
- **Refresh the laptop copy from the repo** (the laptop does not update itself; do this after any change to the script), in PowerShell:
  `Invoke-WebRequest https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/scripts/pull-cnjmesh1-backup.ps1 -OutFile "C:\Users\charl\Documents\scripts\pull-cnjmesh1-backup.ps1"`
- **Check it worked:** the end-of-run summary should list one "pulled" line per archive, and the files should show a green check
  (synced) in Explorer. Sizes should match `ls -lh ~/backups` on the Pi.
- **Limits:** it pulls only the latest archive per prefix, never deletes anything, and does not verify the copy. The main
  archive filename (`cnjmesh1-backup-*`) deliberately does not match `cnjmesh1-extra-*`, so each needs its own entry.

## 5. How to check what is actually on a Pi and whether it is protected

**The repo can be stale. Always ask the live Pi.** On Oct 23 this found: an old script comment claiming the cnjmesh3 bridge had
no bind mount (it has one), a whole Hub database and the Meshview database not backed up, the bot config living outside `/opt`,
and Graywolf's WAL file being missed. Do this audit after any install, move, or new service, and at least quarterly.

**Audit block** (read-only, finishes on its own; run on each Pi, change nothing):

    echo "== containers + mounts"; for c in $(sudo docker ps -aq); do sudo docker inspect $c --format '{{.Name}}: {{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}; {{end}}'; done
    echo "== docker volumes"; sudo docker volume ls
    echo "== databases"; sudo find /opt /home/somog /var/lib /usr/local /etc -xdev \( -name '*.db' -o -name '*.sqlite*' \) -not -path '*/containerd/*' -not -path '*/.mozilla/*' -not -path '*/.config/*' -not -path '*/.cache/*' -not -path '*/docker/*' 2>/dev/null | head -60
    echo "== our units"; ls /etc/systemd/system/*.service /etc/systemd/system/*.timer 2>/dev/null
    echo "== listening ports"; sudo ss -tlnp | awk 'NR>1{print $4, $6}'
    echo "== home + opt"; ls -la /home/somog | head -40; ls /opt
    echo "== cron"; sudo crontab -l 2>&1 | head -5; ls /etc/cron.d
    echo "== config paths named in services"; sudo systemctl cat <service-name> | grep -E "WorkingDirectory|ExecStart"
    echo "== journal persistent?"; ls -d /var/log/journal/*/ 2>&1; journalctl --list-boots --no-pager | tail -2

(Docker volume data lives under `/var/lib/docker/volumes/<name>/_data`; the `find` above skips `/var/lib/docker`, so look inside the
named volumes with `sudo find /var/lib/docker/volumes -name '*.db' -o -name '*.sqlite*'`.)

**For every path and database the audit shows, answer three questions:**
1. Is it named in a backup script (`grep -n "<path>" scripts/*backup*.sh`)?
2. If it is a live database, is it copied **safely** (table below)?
3. Is it in the newest archive (`tar -tzf <archive> | grep <name>`)?

**Safe vs unsafe copies of a running database:**

| Database type | Safe method | Unsafe |
|---|---|---|
| SQLite (Malla, CoreScope, Meshview, Hub, Graywolf, bot, shim) | SQLite online backup (`sqlite3.Connection.backup()` or `.backup`), then `PRAGMA quick_check` | plain `cp` of the `.db` file while the service runs |
| Postgres | `pg_dumpall` | copying the data directory live |
| MySQL | `mysqldump --single-transaction` | copying the data directory live |

**WAL clue:** if the `.db` file has `-wal` and `-shm` files next to it, the database is in WAL mode and recent committed
changes live in the `-wal` file. A plain copy of only the `.db` **loses them**. Graywolf is like this (found Oct 23);
the main script's plain copy of it is superseded by the correct copy in the extra archive.

**Prove a database copy is good (do this at least once per DB, "test restore"):** copy it to a scratch folder, open it
and count rows, for example:
`python3 -c "import sqlite3;d=sqlite3.connect('/tmp/scratch.db');print(d.execute('PRAGMA quick_check').fetchone(), d.execute('select count(*) from <table>').fetchone())"`
For Postgres/MySQL, restore the dump into a throwaway container and run a count. **No test restore has been done yet.**

## 6. Restoring (outline; details in `docs/backup-runbook.md` and `docs/cnjmesh1-recovery-checklist.md`)

1. Extract: `tar -xzf <archive>` into a scratch folder (never straight over live paths).
2. Copy the needed folder back to its original path (the archive layout mirrors the paths; `sqlite/` holds the DB snapshots).
3. SQLite: stop the owning service, copy the snapshot over the `.db` file, **delete any stale `-wal`/`-shm`**, start the service.
4. Postgres: `cat pg_dumpall.sql | docker exec -i <postgres-container> psql -U postgres`. MySQL: `mysql < dump.sql` in the container.
5. cnjmesh3 containers: recreate from `docker/inspect-<name>.json` (image, env, devices, mounts); the bridge image is built from `meshcore-mqtt`/`meshcore-mqtt-tilly`.
6. Restart services, check logs and public hostnames.
Fastest whole-Pi recovery for cnjmesh1 is the SD image plus the newest archives; cnjmesh2 recovers from git.

## 7. Known gaps and to-dos (keep this list current)

- [ ] **Test restore** of at least one SQLite DB, Postgres and MySQL; verify the Sep 2 SD image (`gzip -t`, or write it to a spare card).
- [ ] **cnjmesh2 config-only backup** (compose, mosquitto.conf, cloudflared config, systemd units incl. `wifi-selfheal` and `flight-recorder`); no `docker inspect`, no data tar. Audit the live Pi first.
- [ ] Fold `cnjmesh1-extra-backup.sh` into the main script (one archive).
- [ ] Hub volume `meshcore-hub_data`: non-database files (~68 MB, probably the WAL) were skipped by the 400 MB size guard; the DB itself is saved.
- [ ] Which database the live weather bot uses is unconfirmed (only the home-clone `/home/somog/meshcore-bot/meshcore_bot.db` was found; both are in the extra archive).
- [ ] Add a verification step to `cnjmesh-backup.sh` (cnjmesh3).
- [ ] Retention and cleanup: `~/backups` on cnjmesh1 holds about 4.7 GB of old Malla snapshots (Jul 31, Aug 3); also `~/meshcore-data-bak-20261017` and the CoreScope rollback image. Decide before deleting anything.
- [ ] Schedule it (weekly systemd timer with `nice`/`ionice`) and set up SSH keys so the laptop pull can run unattended.
- [ ] Record radio settings and identity-key handling for the Observer, repeaters and the bot radio.
- [ ] SD images for cnjmesh2 and cnjmesh3; use high-endurance cards from a reputable seller.

## 8. Change log

- **2026-10-23** Audit prompted by Charlie asking whether running databases were captured safely. Added `cnjmesh1-extra-backup.sh`;
  fixed `cnjmesh-backup.sh` (cnjmesh3 bridge bind mount and Tilly fork were never backed up); pull script now pulls the extra archive
  and finds the real Documents folder. First verified runs: cnjmesh1 main 188 MB, extra 129 MB (14 components, all DB copies passed `quick_check`),
  cnjmesh3 620 KB. Journald made persistent on cnjmesh1 and cnjmesh3 so logs survive reboots.
- **2026-08-11** Main script step 10 (archive verification).
- **2026-08-06** Malla, CoreScope and MySQL added to the main script.
- **2026-07-26** `cnjmesh-backup.sh` (host-aware) created; cnjmesh2 deliberately excluded after it overloaded the Pi.
- **2026-07-12** Main script and pull script first created.
