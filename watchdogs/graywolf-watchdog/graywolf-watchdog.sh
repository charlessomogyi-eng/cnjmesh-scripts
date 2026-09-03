#!/bin/bash
source /opt/graywolf-discord/.env
if ! systemctl is-active --quiet graywolf.service; then
    curl -s -H "Content-Type: application/json" \
         -d "{\"content\":\"🚨 graywolf.service (radio/APRS core) is DOWN. NOT auto-restarted — check PTT before restarting manually.\"}" \
         "$DISCORD_WEBHOOK_INTERNET"
fi
