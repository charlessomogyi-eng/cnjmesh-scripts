#!/bin/bash
# Script version: 2026-10-23. See docs/backup-guide.md.
#
# cnjmesh1-extra-backup.sh  --  SECOND archive for what cnjmesh1-backup.sh does not cover.
# Run it in addition to cnjmesh1-backup.sh (that one stays unchanged).
#
# Covers (found by the Oct 23 2026 audit):
#   * every live SQLite database, copied with SQLite's online-backup API (consistent even while the service
#     writes) and then checked with PRAGMA quick_check: Graywolf (WAL mode; the plain copy in the main script
#     misses its -wal file), mesh-discord-shim seen_nodes.db, meshing-around DBs, Meshview packets.db,
#     MeshCore Hub collector DB (Docker volume meshcore-hub_data), any DB found under /opt/meshcore-bot
#   * the weather bot folder /opt/meshcore-bot (code with our patches, config; no caches/.bak/logs) and any
#     config file named in its systemd unit
#   * Meshview folder (config + code, no venv), CoreScope /home/somog/meshcore-data (config, no DB: the main
#     script snapshots that DB), Hub MQTT/observer volumes (size-guarded)
#   * systemd units, the journald drop-in, crontabs, docker container/volume lists, OS info
#
# Usage:   sudo bash cnjmesh1-extra-backup.sh
# Output:  /home/somog/backups/cnjmesh1-extra-YYYY-MM-DD_HHMM.tar.gz   (mode 600: it contains PRIVATE configs;
#          keep it on the laptop/OneDrive only, never in the public repo)
# Nothing is stopped or restarted. Staging is on real disk (not /tmp, which is RAM here).

BACKUP_DIR="/home/somog/backups"
TS="$(date +%Y-%m-%d_%H%M)"
STAGE="${BACKUP_DIR}/extra-staging-${TS}"
ARCHIVE_NAME="cnjmesh1-extra-${TS}.tar.gz"
ARCHIVE="${BACKUP_DIR}/${ARCHIVE_NAME}"
NEED_MB=3000
VOL=/var/lib/docker/volumes
FAIL=0
declare -a EXPECT=()

# snap SRC DESTNAME : consistent SQLite copy + quick_check
snap() {
  local src="$1" dest="${STAGE}/sqlite/$2"
  [ -f "$src" ] || { echo "  skip (not found): $src"; return 0; }
  mkdir -p "$(dirname "$dest")"
  if python3 - "$src" "$dest" <<'PY'
import os, sqlite3, sys
src, dest = sys.argv[1], sys.argv[2]
def attempt(uri, use_uri):
    if os.path.exists(dest):
        os.remove(dest)
    s = sqlite3.connect(uri, uri=use_uri)
    d = sqlite3.connect(dest)
    s.backup(d)
    r = d.execute("PRAGMA quick_check").fetchone()[0]
    d.close(); s.close()
    return r
try:
    r = attempt("file:" + src + "?mode=ro", True)     # read-only open: cannot disturb the live DB
except Exception:
    r = attempt(src, False)                            # fallback (e.g. no -shm available)
if r != "ok":
    sys.exit("quick_check says: " + r)
PY
  then echo "  ok: $src ($(du -h "$dest" | cut -f1))"; EXPECT+=("sqlite/$2")
  else echo "  FAILED: $src"; FAIL=1; fi
}

# copy_tree NAME SRCDIR [extra tar exclude patterns...] : files, minus databases/caches/logs
copy_tree() {
  local name="$1" src="$2"; shift 2
  [ -d "$src" ] || { echo "  skip (not found): $src"; return 0; }
  local ex=(--exclude='*.db' --exclude='*.db-wal' --exclude='*.db-shm' --exclude='*.sqlite' --exclude='*.sqlite-wal' \
            --exclude='*.sqlite-shm' --exclude='__pycache__' --exclude='*.pyc' --exclude='*.bak*' --exclude='*.log' \
            --exclude='venv' --exclude='.venv' --exclude='node_modules')
  local p; for p in "$@"; do ex+=(--exclude="$p"); done
  mkdir -p "${STAGE}/files/${name}"
  tar -C "$src" "${ex[@]}" -cf - . 2>/dev/null | tar -C "${STAGE}/files/${name}" -xf - 2>/dev/null
  EXPECT+=("files/${name}")
  echo "  ok: $src ($(du -sh "${STAGE}/files/${name}" | cut -f1))"
}

# snap_all_in NAMEPREFIX DIR MAXDEPTH [skip-name-glob]
snap_all_in() {
  local prefix="$1" dir="$2" depth="$3" skip="${4:-__none__}" f rel
  [ -d "$dir" ] || return 0
  while IFS= read -r f; do
    rel="${f#${dir}/}"
    snap "$f" "${prefix}/${rel}"
  done < <(find "$dir" -maxdepth "$depth" -type f \( -name '*.db' -o -name '*.sqlite' \) -not -name "$skip" 2>/dev/null)
}

main() {
  [ "$(id -u)" -eq 0 ] || { echo "Run with sudo."; exit 1; }
  umask 077
  command -v python3 >/dev/null || { echo "ABORT: python3 not found"; exit 1; }
  trap 'rm -rf "${STAGE}"' EXIT
  mkdir -p "${BACKUP_DIR}" "${STAGE}"
  local free_mb; free_mb=$(( $(df -Pk "${BACKUP_DIR}" | awk 'NR==2{print $4}') / 1024 ))
  echo "=== cnjmesh1 EXTRA backup ${TS} (free space in ${BACKUP_DIR}: ${free_mb} MB) ==="
  [ "${free_mb}" -ge "${NEED_MB}" ] || { echo "ABORT: need about ${NEED_MB} MB free; old files in ${BACKUP_DIR} may need cleanup first."; exit 1; }

  echo "[1/7] SQLite: Graywolf, mesh-discord-shim, meshing-around"
  snap /var/lib/graywolf/graywolf.db graywolf/graywolf.db
  snap /opt/stacks/mesh-discord-shim/data/seen_nodes.db mesh-discord-shim/seen_nodes.db
  snap_all_in meshing-around /opt/meshing-around/data 2

  echo "[2/7] Weather bot (/opt/meshcore-bot)"
  copy_tree meshcore-bot /opt/meshcore-bot
  snap_all_in meshcore-bot /opt/meshcore-bot 3 'aqi_http_cache*'
  snap /home/somog/meshcore-bot/meshcore_bot.db meshcore-bot-homeclone/meshcore_bot.db
  local unit p; unit="$(systemctl cat meshcore-bot 2>/dev/null)"
  mkdir -p "${STAGE}/files/meshcore-bot-unit"; printf '%s\n' "$unit" > "${STAGE}/files/meshcore-bot-unit/meshcore-bot.service.txt"
  for p in $(printf '%s\n' "$unit" | grep -o '/[A-Za-z0-9_./-]*\.\(ini\|yaml\|yml\|toml\|json\)' | sort -u); do
    if [ -f "$p" ]; then mkdir -p "${STAGE}/files/meshcore-bot-unit-configs$(dirname "$p")"; cp -a "$p" "${STAGE}/files/meshcore-bot-unit-configs${p}"; echo "  config named in unit: $p"; fi
  done

  echo "[3/7] Meshview and CoreScope config"
  copy_tree meshview /home/somog/meshview
  snap_all_in meshview /home/somog/meshview 2
  copy_tree meshcore-data /home/somog/meshcore-data 'backup-tmp*'

  echo "[4/7] MeshCore Hub volumes"
  snap_all_in hub-data "${VOL}/meshcore-hub_data/_data" 4
  local v kb
  for v in meshcore-hub_data meshcore-hub_mqtt_data meshcore-hub_observer_data; do
    kb=$(du -sk "${VOL}/${v}/_data" 2>/dev/null | cut -f1)
    if [ -n "$kb" ] && [ "$kb" -lt 400000 ]; then copy_tree "volume-${v}" "${VOL}/${v}/_data"
    else echo "  skip/too big or missing: ${v} (${kb:-?} KB)"; fi
  done

  echo "[5/7] systemd units, journald, cron, system info"
  mkdir -p "${STAGE}/files/system/systemd"
  cp -a /etc/systemd/system/*.service /etc/systemd/system/*.timer "${STAGE}/files/system/systemd/" 2>/dev/null
  [ -d /etc/systemd/journald.conf.d ] && cp -a /etc/systemd/journald.conf.d "${STAGE}/files/system/"
  crontab -l > "${STAGE}/files/system/crontab-root.txt" 2>&1
  crontab -l -u somog > "${STAGE}/files/system/crontab-somog.txt" 2>&1
  { uname -a; cat /etc/os-release; echo; docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}'; echo; docker volume ls; } \
      > "${STAGE}/files/system/info.txt" 2>&1
  EXPECT+=("files/system/systemd" "files/system/info.txt")

  echo "[6/7] Creating archive ${ARCHIVE_NAME}"
  tar -czf "${ARCHIVE}" -C "${BACKUP_DIR}" "extra-staging-${TS}"
  chmod 600 "${ARCHIVE}"
  chown "${SUDO_USER:-somog}:" "${ARCHIVE}" 2>/dev/null   # so scp (as somog) can read it; still private (mode 600)

  echo "[7/7] Verifying"
  local listing e; listing="$(tar -tzf "${ARCHIVE}")"
  for e in "${EXPECT[@]}"; do
    grep -qF "extra-staging-${TS}/${e}" <<< "$listing" || { echo "  MISSING FROM ARCHIVE: ${e}"; FAIL=1; }
  done
  if [ "$FAIL" -ne 0 ]; then
    mv "${ARCHIVE}" "${ARCHIVE}.FAILED-VERIFICATION"
    echo "=== EXTRA BACKUP INCOMPLETE: renamed to ${ARCHIVE_NAME}.FAILED-VERIFICATION. See FAILED/MISSING lines above. ==="
    exit 1
  fi
  echo "  ${#EXPECT[@]} component(s) present; every SQLite copy passed quick_check."
  echo "=== Extra backup complete and verified: ${ARCHIVE} ==="
  ls -lh "${ARCHIVE}"
  echo "Pull it to your laptop with:  scp somog@10.0.0.181:${ARCHIVE} ."
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then main "$@"; fi
