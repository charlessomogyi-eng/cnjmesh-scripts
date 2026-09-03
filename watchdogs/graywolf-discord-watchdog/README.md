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
