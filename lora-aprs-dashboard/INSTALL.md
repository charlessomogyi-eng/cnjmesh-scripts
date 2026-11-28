# Install the LoRa APRS dashboard on cnjmesh3

Written Nov 26 2026 for Nov 27. About 45 minutes. Every command says which
host it runs on and whether it ends on its own. Paste anything that looks
wrong into the chat before going on.

**Order:** install the dashboard **before** moving K2GIA-10 upstairs, and let
it collect a few days. Then the move shows up as a before-and-after
comparison. The dashboard does not care where the board sits: K2GIA-10 talks
to it over Wi-Fi.

## What you need

- SSH to cnjmesh3 (`somog@10.0.0.187`) and cnjmesh1 (`somog@10.0.0.181`).
- A browser on the home network for K2GIA-10's settings page,
  `http://10.0.0.74` (user `admin`).
- The broker password for the `somog` login. It is the one K2GIA-10 already
  uses (K2GIA-10 settings page, MQTT section).
- K2GIA-10's latitude and longitude (settings page, Beacon section). They
  put your receiver on the map.

## How it will be wired

```
K2GIA-10 --syslog UDP 1514--> cnjmesh3 dashboard --forwards every line--> cnjmesh1 Discord bridge (1514)
K2GIA-10 --MQTT--> cnjmesh1 broker --read only--> cnjmesh3 dashboard
You --browser--> http://10.0.0.187:8090
```

Nothing changes on cnjmesh1. The broker gets one more reader, using the
existing `somog` login.

---

## Step 1: checks on cnjmesh3 (read-only)

Run this on **cnjmesh3**. Ends on its own.

```bash
free -h
```

Fine if the `available` column shows 200 MB or more.

Still on **cnjmesh3**. Ends on its own.

```bash
sudo ss -lntup
```

Fine if nothing is listening on port `1514` or `8090`.

Still on **cnjmesh3**. Ends on its own.

```bash
python3 -c 'import paho.mqtt; print(paho.mqtt.__version__)'
```

A version number means paho is there: skip Step 2. `ModuleNotFoundError`
means do Step 2.

Still on **cnjmesh3**. Ends on its own.

```bash
vcgencmd get_throttled
```

`throttled=0x0` means no power trouble since boot.

## Step 2: install paho (only if Step 1 said ModuleNotFoundError)

Run this on **cnjmesh3**. Ends on its own.

```bash
sudo apt update
```

Still on **cnjmesh3**. Ends on its own.

```bash
sudo apt install -y python3-paho-mqtt
```

Repeat the paho check from Step 1; it should print a version now.

## Step 3: get the code

Run this on **cnjmesh3**. Ends on its own. It updates the repo copy if there is
one, or downloads it if not.

```bash
git -C ~/cnjmesh-scripts pull || git clone https://github.com/charlessomogyi-eng/cnjmesh-scripts.git ~/cnjmesh-scripts
```

## Step 4: copy the program into place

Run these on **cnjmesh3**, one at a time. Each ends on its own.

```bash
sudo mkdir -p /opt/lora-aprs-dashboard
```

```bash
sudo cp -r ~/cnjmesh-scripts/lora-aprs-dashboard/app /opt/lora-aprs-dashboard/
```

```bash
sudo cp ~/cnjmesh-scripts/lora-aprs-dashboard/deploy/env.example /opt/lora-aprs-dashboard/.env
```

```bash
sudo chmod 600 /opt/lora-aprs-dashboard/.env
```

## Step 5: fill in the settings

Run this on **cnjmesh3**. It opens the editor.

```bash
sudo nano /opt/lora-aprs-dashboard/.env
```

Change only these lines (the rest is already set for this setup):

```
MQTT_USER=somog
MQTT_PASSWORD=the broker password
OWN_LAT=K2GIA-10's latitude, e.g. 40.123
OWN_LON=K2GIA-10's longitude, west is negative, e.g. -74.456
SETUP_HARDWARE=LilyGO T3 V1.6.1, CA2RXU iGate 3.2.4
SETUP_ANTENNA=whatever antenna it has today
```

No quotes needed. If the password contains a backslash or a quote mark, ask in
the chat first. Save with Ctrl+O, Enter, then leave with Ctrl+X.

Already set, for reference: syslog only accepted from `10.0.0.74`, every line
forwarded to the bridge at `10.0.0.181:1514`, broker `10.0.0.181:1883`, page
on port 8090, 90 days kept.

This file stays on the Pi. It is not in the repo.

## Step 6: start the service

Run these on **cnjmesh3**, one at a time. Each ends on its own.

```bash
sudo cp ~/cnjmesh-scripts/lora-aprs-dashboard/deploy/lora-aprs-dashboard.service /etc/systemd/system/
```

```bash
sudo systemctl daemon-reload
```

```bash
sudo systemctl enable --now lora-aprs-dashboard
```

Check it. Still on **cnjmesh3**. Ends on its own.

```bash
journalctl -u lora-aprs-dashboard -n 20 --no-pager
```

Good looks like two lines:
`syslog on udp 0.0.0.0:1514, web page on http://0.0.0.0:8090` and
`MQTT connected, subscribed to aprs-k2gia-10/#`.
A line starting `MQTT connection refused` (with a code such as `5`,
`Not authorized` or `Bad user name or password`) means the user or password
in Step 5 is wrong: fix the file, then
`sudo systemctl restart lora-aprs-dashboard`.

## Step 7: open the page

On your phone or PC, on the home network:

```
http://10.0.0.187:8090
```

Open the **Local setup** tab. `MQTT` should say `connected`. Stations start
appearing from MQTT as K2GIA-10 hears them, but without signal figures until
Step 8.

## Step 8: point K2GIA-10's syslog at cnjmesh3

In the browser, open `http://10.0.0.74`, find the **Syslog** section:

- **Enable syslog:** leave on.
- **Server:** change `10.0.0.181` to `10.0.0.187`. (Write down the old value.)
- **Port:** leave `1514`.

Press **Save** at the top. The board restarts by itself; give it a minute.

## Step 9: confirm everything still flows

LoRa traffic is slow at SF12, so the first packet can take 10 to 30 minutes.

On the dashboard's **Local setup** tab, once a packet has arrived:

- `Last syslog line` shows a recent time.
- `iGate firmware` says `3.2.4`.
- `Unreadable lines` says `0`.

The Discord bridge should still get every line. Run this on **cnjmesh1**. It
ends on its own after 2 packets, or after 30 minutes if none come. (If it says
`command not found`, skip it and watch the Discord channel instead.)

```bash
sudo timeout 1800 tcpdump -i any -n -c 2 udp port 1514
```

Lines from `10.0.0.187` mean the forwarding works.

## Step 10: send me real packets

After an hour or so, run this on **cnjmesh3** and paste the output into the
chat. Ends on its own. I will check the parsing against real traffic, which
is the one thing not yet tested.

```bash
curl -s 'http://127.0.0.1:8090/api/packets?limit=15'
```

---

## If something goes wrong: put it back

1. K2GIA-10 settings page, **Syslog**, **Server** back to `10.0.0.181`, Save.
2. Then run this on **cnjmesh3**. Ends on its own.

```bash
sudo systemctl disable --now lora-aprs-dashboard
```

That is the whole rollback. Nothing else was changed.

## Updating later

When I push a new version: run these on **cnjmesh3**, one at a time. Each ends
on its own.

```bash
git -C ~/cnjmesh-scripts pull
```

```bash
sudo cp -r ~/cnjmesh-scripts/lora-aprs-dashboard/app /opt/lora-aprs-dashboard/
```

```bash
sudo systemctl restart lora-aprs-dashboard
```

## Optional, later: share with lora-aprs.live

The firmware's own default syslog target is `lora.link9.net` (the public
lora-aprs.live site). The dashboard can pass every line there too, so
K2GIA-10 shows up on that site while staying RF-only. This makes what
K2GIA-10 hears public. Port `1514` is from our August notes and not
re-checked. To do it, add it to `SYSLOG_FORWARD` in the `.env`, separated
by a space, then restart the service:

```
SYSLOG_FORWARD=10.0.0.181:1514 lora.link9.net:1514
```
