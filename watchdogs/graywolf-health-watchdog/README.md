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

## Where alerts go (cnjmesh1, set Oct 29 2026)
A systemd drop-in sets the webhook for a private Discord channel (`cnj-infrastructure-alerts`),
so the committed unit file keeps `REPLACE_ME`. The URL is never committed. To change it:

    sudo mkdir -p /etc/systemd/system/graywolf-health-watchdog.service.d
    printf '[Service]\nEnvironment=CNJ_DISCORD_WEBHOOK=%s\n' 'PASTE_URL' | sudo tee /etc/systemd/system/graywolf-health-watchdog.service.d/webhook.conf >/dev/null
    sudo systemctl daemon-reload

## Tests
`python3 test_watchdog.py` (offline, no Pi needed; finishes on its own).

## Turn off / undo
    sudo systemctl disable --now graywolf-health-watchdog.timer

## Stuck-transmitter guard (added Oct 31 2026)

Why: on Oct 31 2026 a transmit-triggered USB glitch made `ptt_unkey: TIOCMGET: EPROTO` fail, so the key release never reached the radio and the UV-5R M stayed keyed (red TX light) until Charlie powered it off. A failed `ptt_unkey` is now treated as an emergency:

- `graywolf-ptt-guard.service` runs `watchdog.py --guard` (long-running), follows the graywolf journal and reacts within about a second: `systemctl stop graywolf`, then pause `graywolf-watchdog.timer` and `graywolf-discord-watchdog.timer` (see below), soft-reset the Digirig's own hub (same guarded helper as the normal fix), and post a loud alert ("look at the radio, turn it off if the red TX light is on"). It does not restart graywolf at once (see guarded auto-recovery below). The alert carries ONE resume command for a human to run after looking at the radio: `sudo systemctl start graywolf.service graywolf-discord.service graywolf-watchdog.timer graywolf-discord-watchdog.timer`.
- **Why it pauses the two older timers (Nov 3 2026):** `graywolf-discord.service` has `Requires=graywolf.service`, and `graywolf-discord-watchdog` restarts the bridge every 5 minutes if it is down, so after the guard's stop it would start graywolf (a transmitter) again within minutes. It did exactly that on Oct 31 at 21:48. `PAUSE_TIMERS` (space-separated, in the service environment) overrides the list. The paused timers also come back by themselves at reboot. If a pause fails the alert says so ("could NOT pause ...").
- **Guarded auto-recovery (written Nov 8 2026, Charlie asked "why not automate the restart"; repo and offline tests only until deployed):** a restart clears the fault, but twice on Oct 31 a restart was followed by a beacon about 30 s later that faulted again (20:30:56 then stuck at 20:31:27; reproduced 21:45:15). So the guard restarts only under caps. After its emergency stop it waits `RECOVER_WAIT_SECONDS` (180; the radio's TOT is 30 s), waits up to 5 min for the Digirig's sound card to be back, then starts graywolf, the bridge and both timers ONCE and posts a "started again automatically" notice. If the fault repeats within an hour, or it has already done this twice in 24 h, or the card is missing, everything stays stopped and the alert gives the one resume command. A human who resumes first is left alone. The count is kept in `RECOVERY_FILE` (`/opt/graywolf-health-watchdog/guard-recovery.json`), so a guard restart cannot reset it. Worst case per day: two extra transmissions of at most the radio's TOT. Switch off with a drop-in `Environment=AUTO_RECOVER=0` on `graywolf-ptt-guard.service`, then `daemon-reload` and restart the guard. The 5-minute timer run never does this, only the guard. 10 tests in `GuardedRecovery`.
- The 5-minute timer run does the same if it ever finds an unkey error the guard missed (stop and alert only).
- Any errno on `ptt_key` (EIO, EPROTO, ...) now counts as the ordinary `ptt-error` problem; `--check` prints `ptt_unkey_err=`.
- Backstop outside software: set the radio's TOT (time-out timer) to its shortest option (15 or 30 s). Classic UV-5R: TOT is menu 9 (15-600 s); some newer models list OFF and 15-180 s. Menu numbers vary by model, so scroll until the display shows TOT.

Install on cnjmesh1 (after `git pull`):
1. `sudo cp watchdog.py /opt/graywolf-health-watchdog/watchdog.py`
2. `sudo cp graywolf-ptt-guard.service /etc/systemd/system/`
3. Webhook drop-in: copy `/etc/systemd/system/graywolf-health-watchdog.service.d/webhook.conf` to `/etc/systemd/system/graywolf-ptt-guard.service.d/webhook.conf`.
4. Dry-run check (touches nothing): `sudo python3 /opt/graywolf-health-watchdog/watchdog.py --guard-selftest`
5. `sudo systemctl daemon-reload && sudo systemctl enable --now graywolf-ptt-guard.service`

Already installed? Copy the new `watchdog.py` over the old one, then restart the guard so the long-running process loads it (each finishes on its own):

    sudo cp watchdog.py /opt/graywolf-health-watchdog/watchdog.py
    sudo systemctl restart graywolf-ptt-guard.service

Offline tests: `python3 test_watchdog.py` (35 tests, finishes on its own).
