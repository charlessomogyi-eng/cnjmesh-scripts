# CNJ Mesh disk + temperature + undervoltage watchdog

Alerts to the `#cnjmesh` Discord webhook (same one used by corescope-watchdog
and the graywolf watchdogs) when a Pi's root filesystem, CPU temperature,
or power supply crosses a threshold. Alert-only on state change, matching
the existing watchdog pattern -- no repeated spam every 5 minutes.

Checks:
- **Disk:** warning at 80%, urgent at 90%
- **Temperature:** warning at 70C, urgent at 80C (Pi 4/3 throttle around 80C)
- **Undervoltage:** flags immediately if the Pi detects a bad power supply
  or cable right now -- a plausible contributing cause to the cnjmesh1
  board failure (undervoltage during a write can cause the same kind of
  corruption as a hard power cut)

## Deploy (same steps on cnjmesh1, cnjmesh2, cnjmesh3)

```bash
sudo mkdir -p /opt/disk-temp-watchdog
sudo cp watchdog.py /opt/disk-temp-watchdog/
sudo cp disk-temp-watchdog.service disk-temp-watchdog.timer /etc/systemd/system/
```

Edit the webhook URL in `/etc/systemd/system/disk-temp-watchdog.service`
(replace `REPLACE_ME` with the real #cnjmesh webhook URL -- pull it from
`/opt/corescope-watchdog/watchdog.sh` on cnjmesh1, or from Discord:
Server Settings -> Integrations -> Webhooks).

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now disk-temp-watchdog.timer
sudo systemctl list-timers | grep disk-temp
```

## Verify

```bash
sudo systemctl start disk-temp-watchdog.service
sudo journalctl -u disk-temp-watchdog.service -n 20
cat /opt/disk-temp-watchdog/state.json
```

Requires `vcgencmd` (present on Raspberry Pi OS by default). If temperature
reads unavailable (e.g. running in a non-Pi environment), the script skips
temp alerting and only checks disk.
