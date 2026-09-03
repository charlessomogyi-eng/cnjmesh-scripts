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
   operation — so 30 minutes of total silence is a much stronger signal.
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
