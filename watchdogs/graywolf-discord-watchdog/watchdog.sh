#!/bin/bash
# graywolf-discord-watchdog: restarts the Discord bridge (graywolf-discord.service) if it died.
# SAFETY (Oct 31 2026): graywolf-discord.service has Requires=graywolf.service, so starting the
# bridge also STARTS GRAYWOLF, which keys the radio unattended. This script therefore does
# nothing while graywolf is down (stopped by the PTT guard or by hand); graywolf-watchdog
# alerts about that. Webhook: CNJ_DISCORD_WEBHOOK (drop-in) else DISCORD_WEBHOOK_INTERNET.
# Rehearsal (restarts nothing): `sudo touch /var/tmp/graywolf-discord-watchdog.test`, then
# `sudo systemctl start graywolf-discord-watchdog.service`: posts one TEST message through the
# same webhook route and logs the HTTP status (204 = accepted) to the unit's journal.
source /opt/graywolf-discord/.env
HOOK="${CNJ_DISCORD_WEBHOOK:-$DISCORD_WEBHOOK_INTERNET}"
TESTFLAG=/var/tmp/graywolf-discord-watchdog.test

post() {   # prints the HTTP status Discord answered with
    curl -s -o /dev/null -w '%{http_code}' -H "Content-Type: application/json" \
         -d "{\"content\":\"$1\"}" "$HOOK"
}

if [ -e "$TESTFLAG" ]; then
    rm -f "$TESTFLAG"
    echo "test post status: $(post "🧪 TEST from graywolf-discord-watchdog on $(hostname): rehearsal only, nothing was restarted.")"
    exit 0
fi

if ! systemctl is-active --quiet graywolf.service; then
    exit 0
fi
if ! systemctl is-active --quiet graywolf-discord.service; then
    systemctl restart graywolf-discord.service
    post "⚠️ graywolf-discord.service was found DOWN and has been auto-restarted by watchdog." >/dev/null
fi
