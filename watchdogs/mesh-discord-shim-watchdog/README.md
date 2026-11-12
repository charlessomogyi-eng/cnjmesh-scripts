# mesh-discord-shim-watchdog

Watchdog for `mesh-discord-shim`, a Docker container (not systemd) that
watches **MeshCore** Observer events (pubkey `a8c40bf3` — `advertisement`
and `channel_msg_recv`) and posts them to Discord. Confirmed MeshCore-only,
unrelated to Meshtastic or APRS (verified via live container logs, Sep 2
2026 — the protocol scope was previously undocumented anywhere).

Two checks, alert-only-on-state-change (24hr cooldown per condition, same
pattern as `sjmesh-relay-watchdog`):

1. **Container running** — hard down/up signal via `docker inspect`.
2. **Log freshness** — has the container logged *any* event in the last 30
   minutes. This is a heuristic, not a real heartbeat file (the container
   doesn't have one). Unlike the APRS dead-air check (rejected Sep 2, 2026 —
   message *volume* isn't a reliable Graywolf signal), MeshCore advertisement
   events are frequent/automatic — several per minute observed during normal
   operation — so a long stretch of total silence is a much stronger signal. **Threshold raised from 30 to 90 minutes Nov 11 2026** [V, Charlie's command output]: the shim's log for the previous 24 h had a longest gap of 2714 s (45 min, ending 18:30 UTC) and every hour had events (12 to 62), so 30 minutes false-alarmed on normal quiet.
   **If this ever false-alarms during genuinely normal quiet periods, raise
   `STALE_THRESHOLD_SECONDS` in `watchdog.py` rather than disabling the check.**

Deploy on cnjmesh1 only (where the container runs). Needs the invoking user
to have Docker access. Discord webhook via `CNJ_DISCORD_WEBHOOK` env var
(same shared webhook as the other watchdogs, sourced from
`/opt/mesh-discord-shim-watchdog/.env` — not committed, per secrets policy).

## Deploy
```bash
sudo mkdir -p /opt/mesh-discord-shim-watchdog
sudo cp watchdog.py /opt/mesh-discord-shim-watchdog/
echo 'CNJ_DISCORD_WEBHOOK=<webhook_url>' | sudo tee /opt/mesh-discord-shim-watchdog/.env
sudo cp mesh-discord-shim-watchdog.service mesh-discord-shim-watchdog.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mesh-discord-shim-watchdog.timer
```

## Send alerts to the private channel (Nov 11 2026)
The original deploy used a `.env` file with the public channel's webhook, so the
service file's `EnvironmentFile=` line feeds the public webhook. To move to the
private `cnj-infrastructure-alerts` channel without printing the webhook, reuse
the Graywolf watchdog's drop-in and clear the `EnvironmentFile=` list so the old
`.env` cannot supply a second value:
```bash
sudo mkdir -p /etc/systemd/system/mesh-discord-shim-watchdog.service.d
sudo cp /etc/systemd/system/graywolf-health-watchdog.service.d/webhook.conf /etc/systemd/system/mesh-discord-shim-watchdog.service.d/webhook.conf
printf '[Service]\nEnvironmentFile=\n' | sudo tee /etc/systemd/system/mesh-discord-shim-watchdog.service.d/no-env.conf
sudo systemctl daemon-reload
```
Verify without printing the webhook (the first prints nothing if the list is
cleared; the second prints a count of 1):
```bash
systemctl show mesh-discord-shim-watchdog.service -p EnvironmentFiles
systemctl show mesh-discord-shim-watchdog.service -p Environment | grep -c CNJ_DISCORD_WEBHOOK
```
Deployed on cnjmesh1 Nov 11 2026 5:57 PM and verified there: `EnvironmentFiles` printed empty and the webhook count was 1, so the empty `EnvironmentFile=` assignment did reset the list. (Not checked against systemd's documentation from the session.) The 30-minute no-events rule is a separate open
question (todo 18).

