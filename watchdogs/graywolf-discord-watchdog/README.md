# graywolf-discord-watchdog

Auto-healing watchdog for `graywolf-discord.service` (the Discord relay bridge
for Graywolf/K2GIA-1 traffic — separate process from Graywolf itself). Checks
every 5 minutes via systemd timer. Unlike `graywolf-watchdog` (which is
alert-only due to PTT risk), this one auto-restarts on detection, since
restarting a Discord relay carries no radio-transmit risk. Posts to Discord
either way.

Deployed on cnjmesh1 only. Lives at `/opt/graywolf-discord/watchdog.sh`,
sourcing `/opt/graywolf-discord/.env` for `DISCORD_WEBHOOK_INTERNET` (not
committed, per secrets policy).

## Alerts to the private channel and rehearsal (Nov 3 2026)
Alerts go to the private `#cnj-infrastructure-alerts` channel through a systemd drop-in (the URL is never in the repo); without the drop-in the script falls back to the old public webhook. It restarts the bridge only while Graywolf is up (the bridge Requires Graywolf, so restarting it while Graywolf is down would start the transmitter).

Drop-in (copies the webhook from the health watchdog's drop-in without printing it; finishes on its own):

    sudo install -D -m 600 /etc/systemd/system/graywolf-health-watchdog.service.d/webhook.conf /etc/systemd/system/graywolf-discord-watchdog.service.d/webhook.conf
    sudo systemctl daemon-reload

Rehearse the webhook route without restarting anything (posts one TEST message; the journal line should say 204):

    sudo touch /var/tmp/graywolf-discord-watchdog.test
    sudo systemctl start graywolf-discord-watchdog.service
    sudo journalctl -u graywolf-discord-watchdog.service -n 3 --no-pager
