# mesh-bot-watchdog (cnjmesh1)

Alerts Discord when `mesh_bot.service` (meshing-around, the Meshtastic bot that sends the
7 AM CentralNJ report and NWS alerts through CJG1) is down, or when today's 07:00 job
cannot be confirmed. Drafted Oct 30 2026. **Not yet deployed.** The older
`meshcore-bot-watchdog` covers the MeshCore bot only.

## What it does
- Service down under 25 minutes: silent (so a planned pause for the CJG1 app test is fine).
- Down 25 minutes or more: one Discord message, then a reminder every 12 hours.
- Back up after an alert: one short "back up" message.
- After 09:30 local, if no `last run: <today>` line has appeared in the bot's journal:
  one "could not confirm" message per day. This shows the scheduler fired, not that the
  radio transmitted (no log line proving transmission has been verified).
- A failed Discord post is retried on the next run (state only changes after Discord accepts it).

## Check before enabling (read-only, finishes on its own)
The 07:00 check assumes the bot logs its `Scheduled Tasks ... (last run: ...)` line often
enough that one lands between 07:00 and 09:30. Run on cnjmesh1:

    journalctl -u mesh_bot.service --since today --no-pager -o cat | grep "last run" | tail -8

Expect lines with `last run: 2026-MM-DD 07:00:0x` (today's date). Note how often they
appear. If they are rarer than every ~hour, tell Claude and the deadline moves.

## Install (cnjmesh1)
Each block finishes on its own.

    cd ~/cnjmesh-scripts && git pull
    sudo mkdir -p /opt/mesh-bot-watchdog
    sudo cp watchdogs/mesh-bot-watchdog/watchdog.py /opt/mesh-bot-watchdog/
    sudo cp watchdogs/mesh-bot-watchdog/mesh-bot-watchdog.{service,timer} /etc/systemd/system/
    sudo systemctl daemon-reload

Reuse the webhook the Graywolf watchdog already uses (private channel
`cnj-infrastructure-alerts`, set Oct 29) without printing it:

    sudo mkdir -p /etc/systemd/system/mesh-bot-watchdog.service.d
    sudo cp /etc/systemd/system/graywolf-health-watchdog.service.d/webhook.conf /etc/systemd/system/mesh-bot-watchdog.service.d/webhook.conf
    sudo systemctl daemon-reload

Read-only status (prints, posts nothing, changes nothing):

    sudo python3 /opt/mesh-bot-watchdog/watchdog.py --check

Rehearse the full logic without posting (state untouched):

    sudo DRY_RUN=1 python3 /opt/mesh-bot-watchdog/watchdog.py

Turn it on:

    sudo systemctl enable --now mesh-bot-watchdog.timer

## Test the alert path once
Stop the bot for longer than the grace period, confirm Discord gets the message, start it
again (finishes on its own; remember the 7 AM report depends on it):

    sudo systemctl stop mesh_bot.service

Wait about 30 minutes (the timer runs every 5 minutes), then:

    sudo systemctl start mesh_bot.service
