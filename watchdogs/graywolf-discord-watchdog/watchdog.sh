#!/bin/bash
source /opt/graywolf-discord/.env
if ! systemctl is-active --quiet graywolf-discord.service; then
    systemctl restart graywolf-discord.service
    curl -s -H "Content-Type: application/json" \
         -d "{\"content\":\"⚠️ graywolf-discord.service was found DOWN and has been auto-restarted by watchdog.\"}" \
         "$DISCORD_WEBHOOK_INTERNET"
fi
