#!/bin/bash
# graywolf-discord-watchdog: restarts the Discord bridge (graywolf-discord.service) if it died.
# SAFETY (Oct 31 2026): graywolf-discord.service has Requires=graywolf.service, so starting the
# bridge also STARTS GRAYWOLF, which keys the radio unattended. This script therefore does
# nothing while graywolf is down (stopped by the PTT guard or by hand); graywolf-watchdog
# alerts about that. Webhook: CNJ_DISCORD_WEBHOOK (drop-in) else DISCORD_WEBHOOK_INTERNET.
source /opt/graywolf-discord/.env
HOOK="${CNJ_DISCORD_WEBHOOK:-$DISCORD_WEBHOOK_INTERNET}"
if ! systemctl is-active --quiet graywolf.service; then
    exit 0
fi
if ! systemctl is-active --quiet graywolf-discord.service; then
    systemctl restart graywolf-discord.service
    curl -s -H "Content-Type: application/json" \
         -d "{\"content\":\"⚠️ graywolf-discord.service was found DOWN and has been auto-restarted by watchdog.\"}" \
         "$HOOK"
fi
