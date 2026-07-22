# CNJ Mesh peer-check

Each Pi pings the OTHER two Pis and alerts to Discord (#cnjmesh) if one stops
responding. No third-party tool, no cost, no central point of failure --
if one Pi goes down, the other two still notice and alert.

## Why this instead of a central monitor

A single "monitoring Pi" checking the other two has one flaw: if the
monitoring Pi itself goes down, you lose visibility on everyone. With
peer-check, every Pi checks every OTHER Pi, so coverage only fails if
two Pis go down at the same time.

## Deploy (repeat on each Pi, with different PEERS per host)

```bash
sudo mkdir -p /opt/peer-check
sudo cp peer-check.py /opt/peer-check/
sudo cp peer-check.service peer-check.timer /etc/systemd/system/
```

Edit `/etc/systemd/system/peer-check.service` (use python, not sed/nano, per
preference) and set THREE values:
- `CNJ_DISCORD_WEBHOOK` -- the real #cnjmesh webhook URL
- `NODE_LABEL` -- this Pi's own label (e.g. "Node 2")
- `PEERS` -- the OTHER two Pis' labels and IPs, comma-separated, e.g.:
  `Node 1:10.0.0.181,Node 3:10.0.0.186`

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
