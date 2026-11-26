# LoRa APRS receive dashboard

A local web page showing what K2GIA-10 hears: per-station packet counts, last
heard, SNR, RSSI, noise estimate, frequency offset, airtime and distance.
Modeled on the local-receiver table of `jonadams.com/rxt/`.

**Status (Nov 25 2026): stage 1 written and tested against sample packets built
from the firmware source. Not installed on any Pi. No real packet has been
through it yet.** Installing needs Charlie's OK.

Facts behind the design, and what is still unknown: [NOTES.md](NOTES.md).

## How it works

```
K2GIA-10 --syslog (UDP 1514): signal figures-----> dashboard.py --> SQLite
K2GIA-10 --MQTT (aprs-k2gia-10/<sender>): path---> dashboard.py --> web page :8090
```

The two feeds are joined per packet. Without MQTT it still runs, but many
packets then have no known path and are listed under "Path unknown".

- **Heard directly by this receiver:** one row per station whose transmitter was
  heard. A digipeated packet counts for the digipeater, since the signal
  figures are the digipeater's.
- **Arrived through a digipeater:** who each digipeater passed on.
- **Path unknown:** syslog-only packets whose path the firmware left out.

## What is here

| Path | What |
|---|---|
| `app/dashboard.py` | the program (collector and web server) |
| `app/aprs.py` | firmware formats, path logic, airtime, noise estimate |
| `app/store.py` | database, joining the feeds, figures |
| `app/static/index.html` | the page (no outside scripts or fonts) |
| `deploy/` | example settings and systemd unit, **not installed** |
| `tests/` | tests, firmware harness, sample packets, demo |

Needs Python 3 (tested on 3.13) and, for MQTT only, `paho-mqtt`
(tested with 1.6.1 and 2.2.0).

## Test it (on a PC or build machine, not needed on the Pi)

Run from this folder. The first command downloads the pinned firmware sources
and compiles the harness (needs git and g++). Each command ends on its own.

```bash
tests/harness/build.sh
```

```bash
python3 -m unittest discover -s tests
```

Tests that need the harness, mosquitto or paho-mqtt are skipped if missing.

To look at the page with simulated traffic on `http://127.0.0.1:8090` (runs
until Ctrl+C):

```bash
python3 tests/demo.py
```

## Before installing: look first (read-only)

All on **cnjmesh1**. None of these change anything. Each ends on its own unless
noted.

Who holds UDP 1514, and is port 8090 free:

```bash
sudo ss -lunp 'sport = :1514'; sudo ss -ltnp 'sport = :8090'
```

Is the Discord bridge running:

```bash
pgrep -af lora-aprs-discord; systemctl is-active lora-aprs-discord-bridge
```

Capture real syslog lines without taking the port. Stops by itself after 20
datagrams or 30 minutes:

```bash
sudo timeout 1800 tcpdump -i any -n -A -c 20 udp port 1514
```

## Installing (later, only with Charlie's OK)

1. Settle UDP 1514. Only one program can listen on it. If the Discord bridge is
   in use: set `SYSLOG_PORT=1515` in the bridge's `.env`, restart it, and set
   `SYSLOG_FORWARD=127.0.0.1:1515` here. The bridge code does not change.
2. Copy `app/` to `/opt/lora-aprs-dashboard/app/`.
3. Copy `deploy/env.example` to `/opt/lora-aprs-dashboard/.env`, fill in the
   MQTT login, and make it readable by root only (`chmod 600`).
4. Check that system Python can import paho (`python3-paho-mqtt` package). A
   copy installed with pip for one user is not visible to the service.
5. Install `deploy/lora-aprs-dashboard.service`, enable it, and check
   `journalctl -u lora-aprs-dashboard`.

The page has no login. It is for the home network; do not publish it through
the Cloudflare tunnel without deciding that on purpose.
