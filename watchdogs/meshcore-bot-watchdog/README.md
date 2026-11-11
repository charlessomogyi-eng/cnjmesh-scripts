# meshcore-bot-watchdog (cnjmesh1)

Keeps `meshcore-bot.service` (the CentralNJ-MC 7:05 AM weather bot, talking through `/dev/kpc1`)
running, and posts to Discord when it has to act or cannot. Drafted Nov 11 2026, **not yet deployed**.
The Meshtastic bot has its own watchdog: `mesh-bot-watchdog`.

## Why it was rewritten (Nov 11 2026)
The bot died Oct 31 13:06:56 EDT (systemd start-limit-hit) and nobody was told for 11 days.
The old watchdog was running. Its journal showed `Discord post failed: HTTP Error 403: Forbidden`.
Discord rejects posts that have no User-Agent header (the repo's session-log already records this
bug for the other watchdogs), the old script swallowed the failure, and it saved its state anyway,
so it never retried. [V, Charlie's journal output Nov 11; the Oct 31 failure itself is not in the
3-day journal, so that it failed the same way then is an inference.]

## What it does (timer, every 15 minutes)
- Bot `failed` or `inactive` and `/dev/kpc1` exists: `reset-failed`, `start`, wait, verify, post
  "restarted automatically". At most once per hour and 2 per 24 h. Over the limit it leaves the bot
  alone and says so.
- Bot down and `/dev/kpc1` missing: no restart, one message, reminder every 12 hours.
- Bot `activating` (systemd is already restarting it): left alone.
- Active again after an alert: one "back up" message.
- A post only counts as sent after Discord accepts it, so a failed post is retried next run.
- `sudo touch /opt/meshcore-bot-watchdog/paused` pauses restarts (alerts continue);
  `sudo rm /opt/meshcore-bot-watchdog/paused` resumes. `AUTO_RECOVER=0` turns restarts off.
- Not covered yet: a bot that is running but did not post the 7:05 forecast. To be added once the
  first real run (Nov 12) shows what the bot logs when it posts.

## Install (cnjmesh1)
Each block finishes on its own. The unit on the Pi already has a webhook in it that Discord
rejects, so leave the unit alone and override it with a drop-in that reuses the private channel
`cnj-infrastructure-alerts` webhook without printing it:

    cd ~/cnjmesh-scripts && git pull
    sudo cp watchdogs/meshcore-bot-watchdog/watchdog.py /opt/meshcore-bot-watchdog/watchdog.py
    sudo mkdir -p /etc/systemd/system/meshcore-bot-watchdog.service.d
    sudo cp /etc/systemd/system/graywolf-health-watchdog.service.d/webhook.conf /etc/systemd/system/meshcore-bot-watchdog.service.d/webhook.conf
    sudo systemctl daemon-reload

Check the override took, counting only (should print 1):

    sudo systemctl show meshcore-bot-watchdog.service -p Environment | grep -o "CNJ_DISCORD_WEBHOOK=https" | wc -l

Read-only status (posts nothing, changes nothing):

    sudo CNJ_DISCORD_WEBHOOK=REPLACE_ME python3 /opt/meshcore-bot-watchdog/watchdog.py --check

Offline tests (no Pi needed): `python3 watchdogs/meshcore-bot-watchdog/test_watchdog.py`
