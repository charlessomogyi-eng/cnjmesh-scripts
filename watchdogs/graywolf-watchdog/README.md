# graywolf-watchdog

Alert-only watchdog for `graywolf.service` (the 2m APRS/radio core, K2GIA-1).
Checks every 5 minutes via systemd timer. **Deliberately does NOT auto-restart** —
Graywolf controls PTT (radio transmit), and an unattended restart mid-transmit
or during a bad state was judged too risky. Posts to Discord on detection only,
manual restart is on Charles.

Deployed on cnjmesh1 only. Lives at `/opt/graywolf-discord/graywolf-watchdog.sh`,
sourcing `/opt/graywolf-discord/.env` for `DISCORD_WEBHOOK_INTERNET` (not committed,
per secrets policy).

Companion to `graywolf-discord-watchdog` (watches the separate Discord bridge
process, not Graywolf itself — that one DOES auto-restart, since restarting a
Discord relay carries none of Graywolf's PTT risk).

## Alerts to the private channel and rehearsal (Nov 3 2026)
Alerts go to the private `#cnj-infrastructure-alerts` channel through a systemd drop-in (the URL is never in the repo); without the drop-in the script falls back to the old public webhook. The "already told you" flag is only set once Discord answers 2xx, so a failed post is retried on the next run.

Drop-in (copies the webhook from the health watchdog's drop-in without printing it; finishes on its own):

    sudo install -D -m 600 /etc/systemd/system/graywolf-health-watchdog.service.d/webhook.conf /etc/systemd/system/graywolf-watchdog.service.d/webhook.conf
    sudo systemctl daemon-reload

Rehearse the webhook route without taking Graywolf down (posts one TEST message; the journal line should say 204):

    sudo touch /var/tmp/graywolf-watchdog.test
    sudo systemctl start graywolf-watchdog.service
    sudo journalctl -u graywolf-watchdog.service -n 3 --no-pager
