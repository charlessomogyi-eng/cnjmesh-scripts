# LoRa APRS receive dashboard

A local web page showing what K2GIA-10 hears: per-station packet counts, last
heard, SNR, RSSI, noise estimate, frequency offset, airtime and distance.
Modeled on the local-receiver table of `jonadams.com/rxt/`.

**Status (Nov 25 2026): stage 1 written and tested against sample packets built
from the firmware source. Not installed on any Pi. No real packet has been
through it yet.** Installing needs Charlie's OK.

Facts behind the design, and what is still unknown: [NOTES.md](NOTES.md).

**To install it, follow [INSTALL.md](INSTALL.md)** (cnjmesh3, step by step).

## How it works

```
K2GIA-10 --syslog (UDP 1514): signal figures-----> dashboard.py --> SQLite
K2GIA-10 --MQTT (aprs-k2gia-10/<sender>): path---> dashboard.py --> web page :8090
```

The two feeds are joined per packet. Without MQTT it still runs, but many
packets then have no known path and are listed under "Path unknown".

Totals for 10 minutes, 1 hour and 24 hours sit above four tabs: **Stations**,
**Map**, **Recent packets** and **Local setup**. A filter box narrows the stations and
packets shown.

- **Overview:** this receiver and each digipeater it heard relaying.
- **Heard directly by this receiver:** one row per station whose transmitter was
  heard. A digipeated packet counts for the digipeater, since the signal
  figures are the digipeater's.
- **Arrived through a digipeater:** who each digipeater passed on.
- **Path unknown:** syslog-only packets whose path the firmware left out.
- **Map:** each station at the last position it reported, with a line to the
  receiver coloured by average SNR, and dashed lines to the digipeater that
  passed it on. Set `OWN_LAT` / `OWN_LON` in the `.env` on the Pi for the
  receiver's own marker. Map tiles come from OpenStreetMap over the internet;
  the map library (Leaflet 1.9.4, BSD licence) is served from `app/static/leaflet/`.
- **Channel load incl. CRC est.:** each CRC error counted as a typical good
  packet. An estimate only.

Before showing the page to others: the distance column can help someone work out
where the receiver is, and Recent packets shows message text. There is no
setting yet that hides them.

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

## Where it runs

Planned host: **cnjmesh3** (Pi 3B+, 10.0.0.186), where K2GIA-10 is moving. Not
decided until the checks below are back. cnjmesh1 already carries many services.

- K2GIA-10 sends syslog to cnjmesh3 (its web page, Syslog section).
- The dashboard reads MQTT from the broker on cnjmesh1 (10.0.0.181:1883).
- `SYSLOG_FORWARD=10.0.0.181:1514` passes every line on to the Discord bridge
  on cnjmesh1, so the bridge needs no change. The bridge then depends on
  cnjmesh3 being up.

## Before installing: look first (read-only)

On **cnjmesh3**. None of these change anything, and each ends on its own.

```bash
free -h
```

```bash
sudo ss -lntup
```

```bash
python3 -c 'import paho.mqtt; print(paho.mqtt.__version__)'
```

```bash
vcgencmd get_throttled
```

On **cnjmesh1**: who holds UDP 1514 now.

```bash
sudo ss -lunp 'sport = :1514'
```

Capture real syslog lines, on whichever host K2GIA-10 sends to. Stops by itself
after 20 datagrams or 30 minutes:

```bash
sudo timeout 1800 tcpdump -i any -n -A -c 20 udp port 1514
```

## Installing (later, only with Charlie's OK)

1. Point K2GIA-10's syslog at the dashboard host, and set `SYSLOG_FORWARD` so
   the Discord bridge still gets every line. The program refuses a forward
   target that is its own port, which would loop forever.
2. Copy `app/` to `/opt/lora-aprs-dashboard/app/`.
3. Copy `deploy/env.example` to `/opt/lora-aprs-dashboard/.env`, fill in the
   MQTT login, and make it readable by root only (`chmod 600`).
4. Check that system Python can import paho (`python3-paho-mqtt` package). A
   copy installed with pip for one user is not visible to the service.
5. Install `deploy/lora-aprs-dashboard.service`, enable it, and check
   `journalctl -u lora-aprs-dashboard`.

The page has no login. It is for the home network; do not publish it through
the Cloudflare tunnel without deciding that on purpose.
