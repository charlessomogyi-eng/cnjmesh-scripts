#!/usr/bin/env bash
#
# cnjmesh-backup.sh — host-aware disaster-recovery backup for any CNJ Mesh Pi.
#
# Detects which Pi it's running on and backs up THAT host's real config, data,
# databases, systemd units, and — critically — the Docker container run-state
# (image + env + mounts + devices) so containers with no compose/bind-mount
# (e.g. cnjmesh3's meshcore-mqtt-bridge) can still be recreated. Goal: recover
# fast, not rebuild from memory.
#
# Usage:   sudo ./cnjmesh-backup.sh
# Output:  ~/backups/<host>-backup-YYYY-MM-DD_HHMM.tar.gz
#
# Then pull to laptop + OneDrive:
#   scp <user>@<host-ip>:~/backups/<host>-backup-*.tar.gz .
#
# Pairs with: git repo (scripts/configs/install-maps) + the per-host recovery
# runbook (see RECOVERY.md — TODO). Backup + git + runbook = full bus-proof recovery.

set -uo pipefail

HOST="$(hostname)"
TS="$(date +%Y-%m-%d_%H%M)"
HOME_DIR="$(getent passwd "${SUDO_USER:-$USER}" | cut -d: -f6)"
HOME_DIR="${HOME_DIR:-$HOME}"
BACKUP_DIR="${HOME_DIR}/backups"
STAGING="/tmp/${HOST}-backup-${TS}"
ARCHIVE="${BACKUP_DIR}/${HOST}-backup-${TS}.tar.gz"

echo "=== ${HOST} backup starting: ${TS} ==="
mkdir -p "${BACKUP_DIR}" "${STAGING}"

# ---- helper: copy a path if it exists ----
copy_if() {  # $1 = source path, $2 = label (subdir under staging)
  if [ -e "$1" ]; then
    mkdir -p "${STAGING}/$2"
    cp -a "$1"/. "${STAGING}/$2/" 2>/dev/null || cp -a "$1" "${STAGING}/$2/" 2>/dev/null || true
    echo "  + $1"
  fi
}

# ---- ALWAYS: user-installed systemd units (all hosts have these) ----
echo "[systemd] user-installed units from /etc/systemd/system ..."
mkdir -p "${STAGING}/systemd"
find /etc/systemd/system -maxdepth 1 -type f \( -name '*.service' -o -name '*.timer' \) \
  -exec cp -a {} "${STAGING}/systemd/" \; 2>/dev/null || true

# ---- ALWAYS: Docker container run-state (image/env/mounts/devices/ports) ----
# This is the key to recreating containers that have NO compose file or bind mount
# (their config lives in the run command itself). Secrets ARE included here since
# this archive is private (goes to your laptop/OneDrive, NOT git).
# SKIPPED on cnjmesh2 (Pi Zero 2W, 416MB RAM) — the inspect loop + tar overloaded
# it into unresponsiveness on 2026-07-26. cnjmesh2 recovers from git, not a backup.
if [ "${HOST}" = "cnjmesh2" ]; then
  echo "[docker] skipped on cnjmesh2 (Pi Zero 2W — too memory-constrained; config is in git)."
elif command -v docker >/dev/null 2>&1; then
  echo "[docker] capturing container run-state + compose files ..."
  mkdir -p "${STAGING}/docker"
  docker ps -a --format '{{.Names}}' > "${STAGING}/docker/container-list.txt" 2>/dev/null || true
  while IFS= read -r c; do
    [ -z "$c" ] && continue
    nice -n 19 docker inspect "$c" > "${STAGING}/docker/inspect-${c}.json" 2>/dev/null || true
  done < "${STAGING}/docker/container-list.txt"
  docker image ls > "${STAGING}/docker/images.txt" 2>/dev/null || true
fi

# ---- ALWAYS: cloudflared tunnel config (if present) ----
copy_if /etc/cloudflared "cloudflared"

# ---- ALWAYS: peer-check + any watchdog script dirs (if present) ----
for d in /opt/peer-check /opt/disk-temp-watchdog /opt/meshcore-mqtt-watchdog /opt/corescope-watchdog /opt/graywolf-watchdog; do
  copy_if "$d" "opt$(echo "$d" | tr '/' '-')"
done

# ==========================================================================
# HOST-SPECIFIC
# ==========================================================================
case "${HOST}" in

  cnjmesh1)
    echo "[cnjmesh1] stacks, graywolf, meshing-around, databases ..."
    copy_if /opt/stacks "opt-stacks"
    copy_if /opt/meshing-around "meshing-around"
    copy_if /opt/graywolf-discord "graywolf-discord"
    copy_if /var/lib/graywolf/graywolf.db "graywolf-db"
    copy_if /home/somog/meshcore-data "meshcore-data"        # CoreScope config
    # Postgres dump (mesh-mqtt-pg-collector)
    PG=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -i postgres || true)
    if [ -n "${PG}" ]; then
      echo "  dumping Postgres (${PG}) ..."
      mkdir -p "${STAGING}/postgres-dump"
      PGPW=$(docker inspect "${PG}" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^POSTGRES_PASSWORD=' | cut -d= -f2)
      PGUSER=$(docker inspect "${PG}" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^POSTGRES_USER=' | cut -d= -f2)
      docker exec -e PGPASSWORD="${PGPW}" "${PG}" pg_dumpall -U "${PGUSER:-postgres}" \
        > "${STAGING}/postgres-dump/pg_dumpall.sql" 2>/dev/null \
        || echo "  WARNING: pg_dumpall failed"
    fi
    ;;

  cnjmesh2)
    # cnjmesh2 is a Pi Zero 2W (416MB RAM). The full tar/gzip/docker-inspect
    # backup OVERLOADED it into unresponsiveness on 2026-07-26 (load avg hit 11+,
    # tripped a false peer-check alert). It is NOT worth backing up here:
    #   - its config (mosquitto.conf, docker-compose.override.yml) is committed to
    #     git under cnjmesh2/config/ (mosquitto password redacted there — real value
    #     is the standard MQTT pw, see Charles)
    #   - oktomqtt is an upstream git clone (re-clonable), malla's DB is transient
    #   - it's the lowest-priority host to rebuild (per README)
    # So: recover cnjmesh2 from git, not from a backup archive. Nothing captured here
    # beyond the generic systemd/docker/cloudflared items above (which are light).
    echo "[cnjmesh2] Pi Zero 2W — heavy backup intentionally skipped (config is in git; see cnjmesh2/config/). Only light generic items captured."
    ;;

  cnjmesh3)
    echo "[cnjmesh3] meshcore packet-capture + bridge configs ..."
    copy_if /opt/meshcore-packet-capture "meshcore-packet-capture"
    copy_if /opt/meshcore-mqtt "meshcore-mqtt"
    # NOTE: meshcore-mqtt-bridge has no bind mount — its config is in the
    # container run-state captured above (docker/inspect-meshcore-mqtt-bridge.json).
    ;;

  *)
    echo "  WARNING: unrecognized host '${HOST}' — only generic (systemd/docker/cloudflared) items backed up."
    ;;
esac

# ---- manifest ----
{
  echo "host: ${HOST}"
  echo "created: ${TS}"
  echo "hostname -I: $(hostname -I 2>/dev/null)"
  echo "os: $(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-unknown}")"
  echo "contents:"
  ( cd "${STAGING}" && find . -maxdepth 2 -type d | sort | sed 's/^/  /' )
} > "${STAGING}/MANIFEST.txt"

# ---- package (low priority so it can't spike load on small Pis) ----
echo "Creating archive ..."
nice -n 19 ionice -c3 tar -czf "${ARCHIVE}" -C /tmp "${HOST}-backup-${TS}" 2>/dev/null \
  || tar -czf "${ARCHIVE}" -C /tmp "${HOST}-backup-${TS}"
rm -rf "${STAGING}"

SIZE=$(du -h "${ARCHIVE}" | cut -f1)
echo "=== Backup complete: ${ARCHIVE} (${SIZE}) ==="
echo
echo "⚠  This archive contains secrets (container env, .env files, DB dumps)."
echo "   It is for your laptop/OneDrive — do NOT commit it to git."
echo
echo "Pull it to your laptop:"
echo "  scp ${SUDO_USER:-$USER}@$(hostname -I 2>/dev/null | awk '{print $1}'):${ARCHIVE} ."
