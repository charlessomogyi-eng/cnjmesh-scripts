#!/bin/bash
#
# cnjmesh1-backup.sh
# Ad hoc backup of configs, compose files, and databases on cnjmesh1.
# Run manually before risky changes (config edits, upgrades, USB/hardware
# changes) or roughly monthly otherwise.
#
# Usage:
#   sudo ./cnjmesh1-backup.sh
#
# Output:
#   /home/somog/backups/cnjmesh1-backup-YYYY-MM-DD_HHMM.tar.gz
#
# After it runs, pull the archive to your laptop (scp) and upload to OneDrive.
# Example from your laptop:
#   scp somog@10.0.0.181:/home/somog/backups/cnjmesh1-backup-*.tar.gz .
#
# Coverage as of Aug 6, 2026: bind-mount configs (opt/stacks, meshing-around,
# graywolf-discord, cloudflared), Graywolf DB, mesh-discord-shim DB, Postgres
# (pg_dumpall), Grafana, Malla DB (SQLite, consistency-safe snapshot),
# CoreScope DB (SQLite, consistency-safe snapshot), aprs-tnc-web MySQL
# (mysqldump). Goal: if the SD card died today, everything needed to rebuild
# cnjmesh1's services and data is in this one archive.
#
# NOT covered (intentionally excluded, retired/uninstalled tools, volumes
# left behind with no owning container as of Aug 6 2026 audit):
#   meshmonitor_meshmonitor-data, meshshadow_meshprop-data
#
# Added Aug 11, 2026: step 10, archive verification. Several steps above only
# print a WARNING and continue on failure (e.g. pg_dumpall/mysqldump auth
# issues) - without verification, the script would still report "Backup
# complete" over a silently incomplete archive. Verification checks that
# every component this run actually attempted made it into the final tar,
# and that the DB/dump files specifically aren't suspiciously small (a
# 0-byte dump from a failed/auth-rejected command still "exists"). On
# failure, the archive is renamed with a .FAILED-VERIFICATION suffix so
# pull-cnjmesh1-backup.ps1's *.tar.gz glob can never silently grab a bad one.

set -euo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H%M)
BACKUP_DIR="/home/somog/backups"
# NOTE: staging MUST be on real disk, not /tmp. On cnjmesh1, /tmp is a
# tmpfs (RAM-backed) capped at ~925MB - a 2.3GB Malla snapshot alone
# blows through that. Learned the hard way Aug 6 2026: the script died
# mid-copy with "no space left on device" and briefly filled /tmp system-
# wide, blocking unrelated `docker exec` calls until cleaned up manually.
STAGING_DIR="${BACKUP_DIR}/staging-${TIMESTAMP}"
ARCHIVE_NAME="cnjmesh1-backup-${TIMESTAMP}.tar.gz"
TOTAL_STEPS=10

# Track container temp-file paths created during the run so cleanup() can
# always remove them, even if the script dies partway through (set -e will
# exit immediately on the next failing command - without this, a mid-run
# failure leaves a multi-GB snapshot stranded inside a live data volume,
# which happened on the Aug 6 2026 first run of this new script version).
MALLA_TMP_TO_CLEAN=""
CORESCOPE_TMP_TO_CLEAN=""

# Paths (relative to the staging dir) that MUST exist in the final archive.
# Populated as each applicable component is discovered below, then checked
# against the built archive before this script reports success.
declare -a EXPECTED_PATHS=()
declare -a CRITICAL_DATA_PATHS=()

cleanup() {
    if [ -n "${MALLA_TMP_TO_CLEAN}" ] && [ -n "${MALLA_CONTAINER:-}" ]; then
        docker exec "${MALLA_CONTAINER}" rm -f "${MALLA_TMP_TO_CLEAN}" 2>/dev/null || true
    fi
    if [ -n "${CORESCOPE_TMP_TO_CLEAN}" ] && [ -n "${CORESCOPE_CONTAINER:-}" ]; then
        docker exec "${CORESCOPE_CONTAINER}" rm -f "${CORESCOPE_TMP_TO_CLEAN}" 2>/dev/null || true
    fi
    rm -rf "${STAGING_DIR}"
}
trap cleanup EXIT

echo "=== CNJ Mesh cnjmesh1 backup starting: ${TIMESTAMP} ==="

mkdir -p "${BACKUP_DIR}"
mkdir -p "${STAGING_DIR}"

# --- 1. Docker Compose stacks (configs, compose files, .env files) ---
echo "[1/${TOTAL_STEPS}] Copying /opt/stacks/ ..."
if [ -d /opt/stacks ]; then
    mkdir -p "${STAGING_DIR}/opt-stacks"
    cp -a /opt/stacks/. "${STAGING_DIR}/opt-stacks/" 2>/dev/null || true
    EXPECTED_PATHS+=("opt-stacks")
fi

# --- 2. meshing-around and graywolf-discord ---
echo "[2/${TOTAL_STEPS}] Copying meshing-around and graywolf-discord ..."
for dir in /opt/meshing-around /opt/graywolf-discord; do
    if [ -d "$dir" ]; then
        name=$(basename "$dir")
        mkdir -p "${STAGING_DIR}/${name}"
        cp -a "${dir}/." "${STAGING_DIR}/${name}/" 2>/dev/null || true
        EXPECTED_PATHS+=("${name}")
    fi
done

# --- 3. Cloudflare tunnel config ---
echo "[3/${TOTAL_STEPS}] Copying Cloudflare tunnel config ..."
if [ -f /etc/cloudflared/config.yml ]; then
    mkdir -p "${STAGING_DIR}/cloudflared"
    cp /etc/cloudflared/config.yml "${STAGING_DIR}/cloudflared/"
    EXPECTED_PATHS+=("cloudflared/config.yml")
fi

# --- 4. Graywolf APRS database ---
echo "[4/${TOTAL_STEPS}] Copying Graywolf database ..."
if [ -f /var/lib/graywolf/graywolf.db ]; then
    mkdir -p "${STAGING_DIR}/graywolf-db"
    cp /var/lib/graywolf/graywolf.db "${STAGING_DIR}/graywolf-db/"
    EXPECTED_PATHS+=("graywolf-db/graywolf.db")
fi

# --- 5. mesh-discord-shim seen-nodes database ---
echo "[5/${TOTAL_STEPS}] Copying mesh-discord-shim seen_nodes.db ..."
if [ -f /opt/stacks/mesh-discord-shim/data/seen_nodes.db ]; then
    mkdir -p "${STAGING_DIR}/mesh-discord-shim-db"
    cp /opt/stacks/mesh-discord-shim/data/seen_nodes.db "${STAGING_DIR}/mesh-discord-shim-db/"
    EXPECTED_PATHS+=("mesh-discord-shim-db/seen_nodes.db")
fi

# --- 6. Postgres dump (mesh-mqtt-pg-collector) ---
echo "[6/${TOTAL_STEPS}] Dumping Postgres database ..."
PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i postgres || true)
if [ -n "${PG_CONTAINER}" ]; then
    PG_USER=$(docker inspect "${PG_CONTAINER}" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^POSTGRES_USER=' | cut -d= -f2)
    PG_USER=${PG_USER:-postgres}
    mkdir -p "${STAGING_DIR}/postgres-dump"
    EXPECTED_PATHS+=("postgres-dump/pg_dumpall.sql")
    CRITICAL_DATA_PATHS+=("postgres-dump/pg_dumpall.sql")
    docker exec -e PGPASSWORD="$(docker inspect "${PG_CONTAINER}" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^POSTGRES_PASSWORD=' | cut -d= -f2)" \
        "${PG_CONTAINER}" pg_dumpall -U "${PG_USER}" > "${STAGING_DIR}/postgres-dump/pg_dumpall.sql" 2>/dev/null \
        || echo "  WARNING: pg_dumpall failed - check Postgres container name/credentials"
else
    echo "  No Postgres container found running - skipping"
fi

# --- 7. Malla database (SQLite, consistency-safe snapshot via sqlite3.backup() API) ---
# Malla lives in a Docker NAMED VOLUME (mqtt_malla_data), not a bind-mounted path,
# so it's invisible to the /opt/stacks copy above. It's also actively written
# (WAL mode) by mqtt-malla-capture-1, so a plain file copy risks grabbing it
# mid-write. Use sqlite3's own backup API (no sqlite3 CLI in the image, hence
# python3) to a TEMP path inside the container, copy it out, then DELETE the
# temp file from the container afterward so we don't leave stale snapshots
# sitting in the live data volume (this happened before - see Aug 6 2026 cleanup).
echo "[7/${TOTAL_STEPS}] Backing up Malla database ..."
MALLA_CONTAINER=$(docker ps --format '{{.Names}}' | grep -m1 '^mqtt-malla-web' || true)
if [ -n "${MALLA_CONTAINER}" ]; then
    MALLA_TMP="/app/data/backup-tmp-${TIMESTAMP}.db"
    MALLA_TMP_TO_CLEAN="${MALLA_TMP}"
    EXPECTED_PATHS+=("malla-db/meshtastic_history.db")
    CRITICAL_DATA_PATHS+=("malla-db/meshtastic_history.db")
    if docker exec "${MALLA_CONTAINER}" python3 -c "
import sqlite3
src = sqlite3.connect('/app/data/meshtastic_history.db')
dst = sqlite3.connect('${MALLA_TMP}')
src.backup(dst)
dst.close()
src.close()
"; then
        mkdir -p "${STAGING_DIR}/malla-db"
        docker cp "${MALLA_CONTAINER}:${MALLA_TMP}" "${STAGING_DIR}/malla-db/meshtastic_history.db"
        docker exec "${MALLA_CONTAINER}" rm -f "${MALLA_TMP}"
        MALLA_TMP_TO_CLEAN=""
    else
        echo "  WARNING: Malla sqlite backup failed"
    fi
else
    echo "  No Malla web container found running - skipping"
fi

# --- 8. CoreScope database (SQLite, consistency-safe snapshot, same method as Malla) ---
echo "[8/${TOTAL_STEPS}] Backing up CoreScope database ..."
CORESCOPE_CONTAINER=$(docker ps --format '{{.Names}}' | grep -m1 '^corescope$' || true)
if [ -n "${CORESCOPE_CONTAINER}" ]; then
    CORESCOPE_TMP="/app/data/backup-tmp-${TIMESTAMP}.db"
    CORESCOPE_TMP_TO_CLEAN="${CORESCOPE_TMP}"
    EXPECTED_PATHS+=("corescope-db/meshcore.db")
    CRITICAL_DATA_PATHS+=("corescope-db/meshcore.db")
    if docker exec "${CORESCOPE_CONTAINER}" sh -c "
python3 -c \"
import sqlite3
src = sqlite3.connect('/app/data/meshcore.db')
dst = sqlite3.connect('${CORESCOPE_TMP}')
src.backup(dst)
dst.close()
src.close()
\" 2>/dev/null || (which sqlite3 >/dev/null 2>&1 && sqlite3 /app/data/meshcore.db \".backup '${CORESCOPE_TMP}'\")
"; then
        mkdir -p "${STAGING_DIR}/corescope-db"
        docker cp "${CORESCOPE_CONTAINER}:${CORESCOPE_TMP}" "${STAGING_DIR}/corescope-db/meshcore.db"
        docker exec "${CORESCOPE_CONTAINER}" rm -f "${CORESCOPE_TMP}"
        CORESCOPE_TMP_TO_CLEAN=""
    else
        echo "  WARNING: CoreScope db backup failed (no python3 sqlite3 module or sqlite3 CLI in image)"
    fi
else
    echo "  No CoreScope container found running - skipping"
fi

# --- 9. aprs-tnc-web MySQL dump ---
echo "[9/${TOTAL_STEPS}] Dumping aprs-tnc-web MySQL database ..."
MYSQL_CONTAINER=$(docker ps --format '{{.Names}}' | grep -m1 'mysql_database' || true)
if [ -n "${MYSQL_CONTAINER}" ]; then
    MYSQL_PW=$(docker inspect "${MYSQL_CONTAINER}" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^MYSQL_ROOT_PASSWORD=' | cut -d= -f2)
    MYSQL_DB=$(docker inspect "${MYSQL_CONTAINER}" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^MYSQL_DATABASE=' | cut -d= -f2)
    mkdir -p "${STAGING_DIR}/aprs-tnc-web-mysql-dump"
    EXPECTED_PATHS+=("aprs-tnc-web-mysql-dump/${MYSQL_DB}.sql")
    CRITICAL_DATA_PATHS+=("aprs-tnc-web-mysql-dump/${MYSQL_DB}.sql")
    if docker exec "${MYSQL_CONTAINER}" sh -c "mysqldump -uroot -p'${MYSQL_PW}' --single-transaction '${MYSQL_DB}'" > "${STAGING_DIR}/aprs-tnc-web-mysql-dump/${MYSQL_DB}.sql" 2>/dev/null; then
        :
    else
        echo "  WARNING: mysqldump failed - check mysql_database container name/credentials"
    fi
else
    echo "  No aprs-tnc-web MySQL container found running - skipping"
fi

# --- Grafana config/dashboards (if bind-mounted; adjust path if different) ---
if [ -d /opt/stacks/grafana ]; then
    mkdir -p "${STAGING_DIR}/grafana"
    cp -a /opt/stacks/grafana/. "${STAGING_DIR}/grafana/" 2>/dev/null || true
    EXPECTED_PATHS+=("grafana")
fi

# --- Package into archive ---
echo "Creating archive ${ARCHIVE_NAME} ..."
tar -czf "${BACKUP_DIR}/${ARCHIVE_NAME}" -C "${BACKUP_DIR}" "staging-${TIMESTAMP}"

# --- 10. Verify every expected component actually made it into the archive ---
echo "[10/${TOTAL_STEPS}] Verifying archive contents ..."
VERIFY_FAILED=0
ARCHIVE_LISTING=$(tar -tzf "${BACKUP_DIR}/${ARCHIVE_NAME}")
for f in "${EXPECTED_PATHS[@]}"; do
    if ! grep -qF "staging-${TIMESTAMP}/${f}" <<< "${ARCHIVE_LISTING}"; then
        echo "  MISSING FROM ARCHIVE: ${f}"
        VERIFY_FAILED=1
    fi
done
for f in "${CRITICAL_DATA_PATHS[@]}"; do
    SIZE=$(tar -xzf "${BACKUP_DIR}/${ARCHIVE_NAME}" -O "staging-${TIMESTAMP}/${f}" 2>/dev/null | wc -c)
    if [ "${SIZE}" -lt 1024 ]; then
        echo "  SUSPICIOUSLY SMALL (${SIZE} bytes, expected a real dump/db): ${f}"
        VERIFY_FAILED=1
    fi
done

# --- Cleanup staging (also runs automatically via trap on any early exit) ---
cleanup

if [ "${VERIFY_FAILED}" -eq 1 ]; then
    mv "${BACKUP_DIR}/${ARCHIVE_NAME}" "${BACKUP_DIR}/${ARCHIVE_NAME}.FAILED-VERIFICATION"
    echo "=== BACKUP VERIFICATION FAILED - archive is INCOMPLETE ==="
    echo "Renamed to ${ARCHIVE_NAME}.FAILED-VERIFICATION so it will NOT be picked up by pull-cnjmesh1-backup.ps1's *.tar.gz glob."
    echo "Re-run this script and check the WARNING/MISSING/SMALL lines above for the specific failing component."
    exit 1
fi

echo "  All ${#EXPECTED_PATHS[@]} expected component(s) confirmed present, all critical data files pass a minimum-size check."
echo "=== Backup complete and verified: ${BACKUP_DIR}/${ARCHIVE_NAME} ==="
ls -lh "${BACKUP_DIR}/${ARCHIVE_NAME}"
echo "Pull it to your laptop with:"
echo "  scp somog@10.0.0.181:${BACKUP_DIR}/${ARCHIVE_NAME} ."
