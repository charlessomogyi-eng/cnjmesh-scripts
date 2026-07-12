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

set -euo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H%M)
BACKUP_DIR="/home/somog/backups"
STAGING_DIR="/tmp/cnjmesh1-backup-${TIMESTAMP}"
ARCHIVE_NAME="cnjmesh1-backup-${TIMESTAMP}.tar.gz"

echo "=== CNJ Mesh cnjmesh1 backup starting: ${TIMESTAMP} ==="

mkdir -p "${BACKUP_DIR}"
mkdir -p "${STAGING_DIR}"

# --- 1. Docker Compose stacks (configs, compose files, .env files) ---
echo "[1/6] Copying /opt/stacks/ ..."
if [ -d /opt/stacks ]; then
    mkdir -p "${STAGING_DIR}/opt-stacks"
    cp -a /opt/stacks/. "${STAGING_DIR}/opt-stacks/" 2>/dev/null || true
fi

# --- 2. meshing-around and graywolf-discord ---
echo "[2/6] Copying meshing-around and graywolf-discord ..."
for dir in /opt/meshing-around /opt/graywolf-discord; do
    if [ -d "$dir" ]; then
        name=$(basename "$dir")
        mkdir -p "${STAGING_DIR}/${name}"
        cp -a "${dir}/." "${STAGING_DIR}/${name}/" 2>/dev/null || true
    fi
done

# --- 3. Cloudflare tunnel config ---
echo "[3/6] Copying Cloudflare tunnel config ..."
if [ -f /etc/cloudflared/config.yml ]; then
    mkdir -p "${STAGING_DIR}/cloudflared"
    cp /etc/cloudflared/config.yml "${STAGING_DIR}/cloudflared/"
fi

# --- 4. Graywolf APRS database ---
echo "[4/6] Copying Graywolf database ..."
if [ -f /var/lib/graywolf/graywolf.db ]; then
    mkdir -p "${STAGING_DIR}/graywolf-db"
    cp /var/lib/graywolf/graywolf.db "${STAGING_DIR}/graywolf-db/"
fi

# --- 5. mesh-discord-shim seen-nodes database ---
echo "[5/6] Copying mesh-discord-shim seen_nodes.db ..."
if [ -f /opt/stacks/mesh-discord-shim/data/seen_nodes.db ]; then
    mkdir -p "${STAGING_DIR}/mesh-discord-shim-db"
    cp /opt/stacks/mesh-discord-shim/data/seen_nodes.db "${STAGING_DIR}/mesh-discord-shim-db/"
fi

# --- 6. Postgres dump (mesh-mqtt-pg-collector) ---
echo "[6/6] Dumping Postgres database ..."
PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i postgres || true)
if [ -n "${PG_CONTAINER}" ]; then
    mkdir -p "${STAGING_DIR}/postgres-dump"
    docker exec "${PG_CONTAINER}" pg_dumpall -U postgres > "${STAGING_DIR}/postgres-dump/pg_dumpall.sql" 2>/dev/null \
        || echo "  WARNING: pg_dumpall failed - check Postgres container name/credentials"
else
    echo "  No Postgres container found running - skipping"
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
echo "Pull it to your laptop with:"
echo "  scp somog@10.0.0.181:${BACKUP_DIR}/${ARCHIVE_NAME} ."
