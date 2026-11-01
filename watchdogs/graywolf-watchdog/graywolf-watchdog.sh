#!/bin/bash
# graywolf-watchdog: ALERT-ONLY. Never restarts graywolf (a restart keys the radio unattended;
# PTT risk, see known-issues). Posts ONCE per outage, not every 5 minutes.
# Webhook: CNJ_DISCORD_WEBHOOK (set in a systemd drop-in, e.g. the private alerts channel);
# falls back to DISCORD_WEBHOOK_INTERNET from /opt/graywolf-discord/.env (the public APRS channel).
source /opt/graywolf-discord/.env
HOOK="${CNJ_DISCORD_WEBHOOK:-$DISCORD_WEBHOOK_INTERNET}"
FLAG=/var/tmp/graywolf-watchdog.down
if systemctl is-active --quiet graywolf.service; then
    rm -f "$FLAG"
elif [ ! -e "$FLAG" ]; then
    touch "$FLAG"
    curl -s -H "Content-Type: application/json" \
         -d "{\"content\":\"🚨 graywolf.service (radio/APRS core) is DOWN. NOT auto-restarted — check PTT before restarting manually. (If the PTT guard stopped it, the private alerts channel says why.)\"}" \
         "$HOOK"
fi
