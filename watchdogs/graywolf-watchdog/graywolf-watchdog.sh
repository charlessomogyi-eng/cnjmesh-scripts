#!/bin/bash
# graywolf-watchdog: ALERT-ONLY. Never restarts graywolf (a restart keys the radio unattended;
# PTT risk, see known-issues). Posts ONCE per outage, not every 5 minutes.
# Webhook: CNJ_DISCORD_WEBHOOK (set in a systemd drop-in, e.g. the private alerts channel);
# falls back to DISCORD_WEBHOOK_INTERNET from /opt/graywolf-discord/.env (the public APRS channel).
# The "already told you" flag is only set after Discord accepted the post (2xx), so a failed
# post is retried on the next run instead of the outage going unreported.
# Rehearsal (no downtime): `sudo touch /var/tmp/graywolf-watchdog.test`, then
# `sudo systemctl start graywolf-watchdog.service`: posts one TEST message through the same
# webhook route and logs the HTTP status (204 = accepted) to the unit's journal.
source /opt/graywolf-discord/.env
HOOK="${CNJ_DISCORD_WEBHOOK:-$DISCORD_WEBHOOK_INTERNET}"
FLAG=/var/tmp/graywolf-watchdog.down
TESTFLAG=/var/tmp/graywolf-watchdog.test

post() {   # prints the HTTP status Discord answered with
    curl -s -o /dev/null -w '%{http_code}' -H "Content-Type: application/json" \
         -d "{\"content\":\"$1\"}" "$HOOK"
}

if [ -e "$TESTFLAG" ]; then
    rm -f "$TESTFLAG"
    echo "test post status: $(post "🧪 TEST from graywolf-watchdog on $(hostname): rehearsal only, graywolf is fine.")"
    exit 0
fi

if systemctl is-active --quiet graywolf.service; then
    rm -f "$FLAG"
elif [ ! -e "$FLAG" ]; then
    case "$(post "🚨 graywolf.service (radio/APRS core) is DOWN. NOT auto-restarted — check PTT before restarting manually. (If the PTT guard stopped it, the private alerts channel says why.)")" in
        2??) touch "$FLAG" ;;
    esac
fi
