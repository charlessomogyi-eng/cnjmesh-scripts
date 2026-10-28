# graywolf-health-watchdog

Detects a deaf/mute K2GIA-1 (Graywolf + UV-5R M + Digirig on cnjmesh1) and tries
one cautious, rate-limited fix. Built Oct 28 2026 after the Digirig's USB audio
chip dropped off the bus: Graywolf stayed "active" while logging
`ptt_key: TIOCMGET: EIO` and `start_audio failed`, and K2GIA-1 could neither hear
nor transmit for 9+ hours with no alert.

Deployed on **cnjmesh1 only**. Complements `graywolf-watchdog` (service-down
alert, never restarts) and `graywolf-discord-watchdog` (Discord relay).

## What it checks (every 5 min, read-only)
1. Digirig sound card present (`/proc/asound/cards`, card name `Device`).
2. No `start_audio failed` in Graywolf's journal in the last 10 min.
3. No `ptt_key ... EIO` since Graywolf's last start.
4. A beacon sent in the last 50 min (only after 1 h of uptime).

If `graywolf.service` itself is down it does nothing (graywolf-watchdog covers that).

## What it does about it
- **Card missing:** soft-reset only the Digirig's own 2-port hub (`0424:2412`, found
  by the CP2102N serial number; it refuses to touch anything else), wait up to 20 s for
  the card, then restart graywolf.
- **Card present but audio/PTT errors:** restart graywolf once.
- **No beacon / anything else:** alert only.
- Limits: one automatic fix per hour, three per 24 h. It never restarts in a loop (the
  old every-5-minute watchdog broke PTT).
- A soft reset may not revive a wedged chip (Oct 28 needed a physical replug and a port
  change). If it fails, the alert tells Charlie what to do.

## Discord (kept quiet)
- One message when a new problem is found, saying what was tried.
- Silence while that problem persists.
- A second message only if the problem comes back after an automatic fix.
- A short "healthy again" message when a human-fixed problem clears
  (`RECOVERY_NOTICE=0` in the service file turns it off).
- The same problem is never announced twice within 6 hours.

Webhook: leaves `CNJ_DISCORD_WEBHOOK=REPLACE_ME` and falls back to
`DISCORD_WEBHOOK_INTERNET` in `/opt/graywolf-discord/.env` (not committed).

## Install (cnjmesh1)
Each block finishes on its own.

    cd ~/cnjmesh-scripts && git pull
    sudo mkdir -p /opt/graywolf-health-watchdog
    sudo cp watchdogs/graywolf-health-watchdog/watchdog.py /opt/graywolf-health-watchdog/
    sudo cp watchdogs/graywolf-health-watchdog/graywolf-health-watchdog.{service,timer} /etc/systemd/system/
    sudo systemctl daemon-reload

Test read-only first (prints status, sends nothing, changes nothing):

    sudo python3 /opt/graywolf-health-watchdog/watchdog.py --check

Then rehearse the full logic without acting (prints what it would send/do):

    sudo DRY_RUN=1 python3 /opt/graywolf-health-watchdog/watchdog.py

Turn it on:

    sudo systemctl enable --now graywolf-health-watchdog.timer

## Tests
`python3 test_watchdog.py` (offline, no Pi needed; finishes on its own).

## Turn off / undo
    sudo systemctl disable --now graywolf-health-watchdog.timer
