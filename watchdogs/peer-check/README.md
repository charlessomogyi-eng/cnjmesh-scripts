# CNJ Mesh peer-check

Each Pi pings the OTHER two Pis and alerts to Discord (#cnjmesh) if one stops
responding. No third-party tool, no cost, no central point of failure --
if one Pi goes down, the other two still notice and alert.

## Why this instead of a central monitor

A single "monitoring Pi" checking the other two has one flaw: if the
monitoring Pi itself goes down, you lose visibility on everyone. With
peer-check, every Pi checks every OTHER Pi, so coverage only fails if
two Pis go down at the same time.

## Debouncing (avoids false alarms from brief blips)

A peer must fail 3 CONSECUTIVE checks (15 minutes, at the standard 5-min
timer interval) before it's declared truly down and alerted. This means
a router reboot, a few minutes of bad WiFi, or a short power flicker
won't trigger an alert at all -- only sustained outages do.

This also fixes a real problem: if a genuine outage happens to coincide
with the checking Pi's OWN network being briefly down (e.g. during a
router reboot), the down-alert can fail to send in that instant, but the
later recovery alert goes through fine once things are back -- producing
a confusing "back online" message with no prior "offline" one. Debouncing
means these brief coincidental blips don't get treated as a real down
event in the first place, so this mismatch mostly goes away.

Override the threshold via the `DOWN_THRESHOLD` env var (default `3`).

## Deploy (repeat on each Pi, with different PEERS per host)

```bash
sudo mkdir -p /opt/peer-check
sudo cp peer-check.py /opt/peer-check/
sudo cp peer-check.service peer-check.timer /etc/systemd/system/
```

Edit `/etc/systemd/system/peer-check.service` (use python, not sed/nano, per
preference) and set values:
- `CNJ_DISCORD_WEBHOOK` -- the real #cnjmesh webhook URL
- `NODE_LABEL` -- this Pi's own label (e.g. "Node 2")
- `PEERS` -- the OTHER two Pis' labels and IPs, comma-separated, e.g.:
  `Node 1:10.0.0.181,Node 3:10.0.0.186`
- `SERVICES` (optional) -- what services live on each peer, listed in the
  down-alert so it says what's actually affected, not just "node down".
  Format: semicolon between peers, colon after label, comma-separated
  services, e.g.:
  `Node 1:meshview,malla,meshcorehub,mqtt,APRS 2m;Node 3:Observer,KPR2`
- `CROSS_POST_WEBHOOK` (optional) -- a second Discord webhook URL to also
  post to, for peers whose services matter to a different audience (e.g.
  the Meshtastic community server, since meshview/malla are Meshtastic
  tools -- MeshCore-only outages shouldn't cross-post there).
- `CROSS_POST_LABELS` (optional) -- comma-separated peer labels whose
  alerts should ALSO go to `CROSS_POST_WEBHOOK`, e.g. `Node 1,Node 2`.
  Only listed labels cross-post; everything else stays #cnjmesh-only.

Example python one-liner (adjust values per host):
```bash
sudo python3 -c "
path = '/etc/systemd/system/peer-check.service'
with open(path) as f:
    c = f.read()
c = c.replace('REPLACE_ME_NODE_LABEL', 'Node 2')
c = c.replace('REPLACE_ME_PEERS', 'Node 1:10.0.0.181,Node 3:10.0.0.186')
c = c.replace('REPLACE_ME', 'https://discord.com/api/webhooks/...')
with open(path, 'w') as f:
    f.write(c)
"
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now peer-check.timer
sudo systemctl start peer-check.service
sudo journalctl -u peer-check.service -n 10
```

Should show each peer as `up` or `down`. First run never alerts (assumes
peers were up before monitoring started) -- alerts only fire on a state
CHANGE from that point forward.
