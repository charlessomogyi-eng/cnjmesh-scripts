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

set -euo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H%M)
BACKUP_DIR="/home/somog/backups"
STAGING_DIR="/tmp/cnjmesh1-backup-${TIMESTAMP}"
ARCHIVE_NAME="cnjmesh1-backup-${TIMESTAMP}.tar.gz"
TOTAL_STEPS=9

echo "=== CNJ Mesh cnjmesh1 backup starting: ${TIMESTAMP} ==="

mkdir -p "${BACKUP_DIR}"
mkdir -p "${STAGING_DIR}"

# --- 1. Docker Compose stacks (configs, compose files, .env files) ---
echo "[1/${TOTAL_STEPS}] Copying /opt/stacks/ ..."
if [ -d /opt/stacks ]; then
    mkdir -p "${STAGING_DIR}/opt-stacks"
    cp -a /opt/stacks/. "${STAGING_DIR}/opt-stacks/" 2>/dev/null || true
fi

# --- 2. meshing-around and graywolf-discord ---
echo "[2/${TOTAL_STEPS}] Copying meshing-around and graywolf-discord ..."
for dir in /opt/meshing-around /opt/graywolf-discord; do
    if [ -d "$dir" ]; then
        name=$(basename "$dir")
        mkdir -p "${STAGING_DIR}/${name}"
        cp -a "${dir}/." "${STAGING_DIR}/${name}/" 2>/dev/null || true
    fi
done

# --- 3. Cloudflare tunnel config ---
echo "[3/${TOTAL_STEPS}] Copying Cloudflare tunnel config ..."
if [ -f /etc/cloudflared/config.yml ]; then
    mkdir -p "${STAGING_DIR}/cloudflared"
    cp /etc/cloudflared/config.yml "${STAGING_DIR}/cloudflared/"
fi

# --- 4. Graywolf APRS database ---
echo "[4/${TOTAL_STEPS}] Copying Graywolf database ..."
if [ -f /var/lib/graywolf/graywolf.db ]; then
    mkdir -p "${STAGING_DIR}/graywolf-db"
    cp /var/lib/graywolf/graywolf.db "${STAGING_DIR}/graywolf-db/"
fi

# --- 5. mesh-discord-shim seen-nodes database ---
echo "[5/${TOTAL_STEPS}] Copying mesh-discord-shim seen_nodes.db ..."
if [ -f /opt/stacks/mesh-discord-shim/data/seen_nodes.db ]; then
    mkdir -p "${STAGING_DIR}/mesh-discord-shim-db"
    cp /opt/stacks/mesh-discord-shim/data/seen_nodes.db "${STAGING_DIR}/mesh-discord-shim-db/"
fi

# --- 6. Postgres dump (mesh-mqtt-pg-collector) ---
echo "[6/${TOTAL_STEPS}] Dumping Postgres database ..."
PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i postgres || true)
if [ -n "${PG_CONTAINER}" ]; then
    PG_USER=$(docker inspect "${PG_CONTAINER}" --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^POSTGRES_USER=' | cut -d= -f2)
    PG_USER=${PG_USER:-postgres}
    mkdir -p "${STAGING_DIR}/postgres-dump"
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
    else
        echo "  WARNING: Malla sqlite backup failed"
        docker exec "${MALLA_CONTAINER}" rm -f "${MALLA_TMP}" 2>/dev/null || true
    fi
else
    echo "  No Malla web container found running - skipping"
fi

# --- 8. CoreScope database (SQLite, consistency-safe snapshot, same method as Malla) ---
echo "[8/${TOTAL_STEPS}] Backing up CoreScope database ..."
CORESCOPE_CONTAINER=$(docker ps --format '{{.Names}}' | grep -m1 '^corescope$' || true)
if [ -n "${CORESCOPE_CONTAINER}" ]; then
    CORESCOPE_TMP="/app/data/backup-tmp-${TIMESTAMP}.db"
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
    else
        echo "  WARNING: CoreScope db backup failed (no python3 sqlite3 module or sqlite3 CLI in image)"
        docker exec "${CORESCOPE_CONTAINER}" rm -f "${CORESCOPE_TMP}" 2>/dev/null || true
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
fi

# --- Package into archive ---
echo "Creating archive ${ARCHIVE_NAME} ..."
tar -czf "${BACKUP_DIR}/${ARCHIVE_NAME}" -C /tmp "cnjmesh1-backup-${TIMESTAMP}"

# --- Cleanup staging ---
rm -rf "${STAGING_DIR}"

echo "=== Backup complete: ${BACKUP_DIR}/${ARCHIVE_NAME} ==="
ls -lh "${BACKUP_DIR}/${ARCHIVE_NAME}"
echo "Pull it to your laptop with:"
echo "  scp somog@10.0.0.181:${BACKUP_DIR}/${ARCHIVE_NAME} ."
