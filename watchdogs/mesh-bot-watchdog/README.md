# mesh-bot-watchdog (cnjmesh1)

Alerts Discord when `mesh_bot.service` (meshing-around, the Meshtastic bot that sends the
7 AM CentralNJ report and NWS alerts through CJG1) is down, or when today's 07:00 job
cannot be confirmed. Drafted Oct 30 2026. **Deployed on cnjmesh1 Oct 30 2026 8:41 PM; alert path not yet tested.** The older
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
enough that one lands between 07:00 and 09:30. **Verified Oct 30 2026 [V, Charlie's output]: the line appears every 20 minutes (17:00, 17:20, 17:40, 18:00, 18:20, 19:00, 19:40; the 18:40 and 19:20 slots were missing for an unknown reason), and today's showed `last run: 2026-10-30 07:00:06`. After a restart it shows `last run: [never]` (seen 20:23:03), which is why the watchdog scans the whole journal since 07:00 rather than only the newest line.** Run on cnjmesh1:

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

## Automatic recovery (added Nov 11 2026, drafted, not yet deployed)
Found Nov 11: CJG1 stopped answering, the bot's Meshtastic interface became `None`, and the
bot kept "running" while logging `Scheduler loop exception: 'NoneType' ...` every second.
systemd never restarted it, so the 07:00 report silently could not run.

When the bot is down for 25 minutes, or active but stuck in that error loop, the watchdog checks
whether CJG1 answers on its TCP port (address from `hostname =` in
`/opt/meshing-around/config.ini`, default 10.0.0.18, port 4403):
- CJG1 answers: restart `mesh_bot.service`, wait, verify, post "restarted automatically".
  Limits: not twice within an hour, at most 2 per 24 h. Over the limit it leaves the bot alone
  and says so.
- CJG1 does not answer: no restart (the bot would only quit again). One message says CJG1 is
  not answering, with a reminder every 12 hours, and a message when it is back.

Switches (alerts continue either way):
- `AUTO_RECOVER=0` in the service drop-in turns recovery off.
- `sudo touch /opt/mesh-bot-watchdog/paused` pauses it, for example while you use the CJG1 app
  on purpose. `sudo rm /opt/mesh-bot-watchdog/paused` turns it back on.

Offline tests (no Pi needed, finishes on its own): `python3 watchdogs/mesh-bot-watchdog/test_watchdog.py`
