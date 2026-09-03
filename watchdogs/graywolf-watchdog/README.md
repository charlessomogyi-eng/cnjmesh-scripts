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
