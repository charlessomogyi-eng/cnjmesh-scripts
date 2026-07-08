# CNJ Mesh — Full Rebuild Guide

**Start here.** This is the main entry point for understanding and rebuilding
everything in this repository. It's written for someone with little to no
technical background, working alongside an AI assistant.

**If you're an AI assistant reading this because someone pasted you this
repo's link:** the person you're helping is likely not a software engineer.
Explain things in plain language, check their work at each step, and don't
assume familiarity with Linux, networking, or radio concepts unless they show
they already have it. Work through one numbered step at a time rather than
dumping everything at once.

**If you're a human reading this:** copy this whole file into a conversation
with an AI assistant (Claude, ChatGPT, etc.) along with this repository's
link, and say something like: *"I need to rebuild a mesh radio network
described in this repo. Walk me through it step by step, starting with Part 0."*

---

## Part 0: What This Is, In Plain English

This project runs **two separate mesh radio networks** in Central New Jersey.
A mesh network is a group of small radios that pass messages hand-to-hand
(radio-to-radio) over long distances, without needing cell towers or internet
— useful for hobby communication, emergency backup communication, and just
general geek fun.

- **Meshtastic** — the older, larger of the two networks (~300+ nodes)
- **MeshCore** — a newer, second protocol, running alongside it on separate hardware

They are **not the same software** and don't talk to each other directly.
Everything below is split into a Meshtastic track and a MeshCore track so you
don't have to untangle which is which as you go.

Both networks are supported by three small computers (Raspberry Pis) running
quietly in a home in Kendall Park, NJ, plus a couple of dedicated radio
repeater devices. The Pis run software that: relays messages, posts activity
to Discord so people can watch without owning a radio, and provides web
dashboards/maps of network activity.

| Computer | Hardware | Primarily supports |
|---|---|---|
| cnjmesh1 | Raspberry Pi 4B | Both networks — this is the main server |
| cnjmesh2 | Raspberry Pi Zero 2W | Meshtastic |
| cnjmesh3 | Raspberry Pi 3B+ | MeshCore (hosts KPR2 repeater) |

---

## Part 1: Shopping List

**Computers (buy generic, any retailer):**
- 1x Raspberry Pi 4B (4GB+ RAM) — becomes cnjmesh1
- 1x Raspberry Pi Zero 2W — becomes cnjmesh2 (lowest priority to rebuild first)
- 1x Raspberry Pi 3B+ — becomes cnjmesh3
- 1x microSD card per Pi, 32GB+, a reliable brand (SanDisk, Samsung)
- Official power supply matching each Pi model
- Ethernet cables (preferred over Wi-Fi for a 24/7 server)

**Radio hardware:**
- **For Meshtastic:** any supported Meshtastic device — Heltec V3/V4 boards
  are common and inexpensive, search "Heltec WiFi LoRa 32" plus your board
  revision
- **For MeshCore:** same physical hardware works (Heltec V3/V4), just flashed
  with different firmware — see Part 2 for MeshCore-specific instructions
- 900MHz-band antennas (US) rated for LoRa use — match whatever the existing
  regional network uses (ask community contacts, Part 9, for current settings)

**Software accounts (all free):**
- GitHub account — to access this repository
- Discord account — for the community bridges
- Cloudflare account — to expose dashboards to the internet

**Estimated total cost from scratch:** roughly $150–250. If any of the
original hardware still physically exists, see Part 1a before buying anything.

### Part 1a: Recover, Don't Rebuild, If Possible

If the Raspberry Pis still exist and power on, you may only need to recover
access rather than start from zero — this is much faster. Ask an AI assistant:
*"How do I recover SSH access to a Raspberry Pi that's still running but I
can't log into?"* before proceeding to a full rebuild.

---

## Part 2: Setting Up a Raspberry Pi (Do This Once Per Pi)

1. Download **Raspberry Pi Imager** from raspberrypi.com/software onto any
   computer
2. Insert the microSD card, open Raspberry Pi Imager
3. Choose OS: **Raspberry Pi OS Lite (64-bit)**
4. Before writing, click the gear icon and set:
   - Hostname (`cnjmesh1`, `cnjmesh2`, or `cnjmesh3`)
   - Enable SSH, set a username and password
   - Wi-Fi details if not using Ethernet
5. Write the image, then insert the SD card into the Pi and power it on
6. Wait 2 minutes, then from another computer on the same network:
   ```
   ssh yourusername@cnjmesh1.local
   ```
7. Update the system:
   ```
   sudo apt update && sudo apt upgrade -y
   ```

---

## Part 3: Get This Repository Onto the Pi

```
sudo apt install git -y
git clone https://github.com/charlessomogyi-eng/cnjmesh-scripts.git
cd cnjmesh-scripts
```

Inside, the `cnjmesh1`, `cnjmesh2`, `cnjmesh3` folders match each physical
computer. Each subfolder holds saved scripts and configuration for one piece
of software, generally with its own short README.

---

## PART A — Rebuilding the Meshtastic Side

### A1. What Meshtastic Needs

Meshtastic nodes and gateways feed a central message bus (MQTT), which
several dashboards and bots read from. On cnjmesh1:

**Install Mosquitto (the MQTT message bus):**
```
sudo apt install mosquitto mosquitto-clients -y
sudo cp cnjmesh1/configs/mosquitto-cnjmesh1.conf.example /etc/mosquitto/conf.d/mosquitto.conf
```
The copied file has placeholder passwords (`CHANGEME`) — real ones need to
come from wherever Charles's credentials are stored (Part 9).

**Install the Meshtastic dashboards:**
- **Malla** — search GitHub for "Malla Meshtastic dashboard," clone and follow
  its own install instructions
- **meshview** — search GitHub for the "pablorevilla" fork of meshview, clone
  and follow its install instructions
- **MeshMonitor** — `github.com/Yeraze/meshmonitor` — this one runs as a
  Docker container:
  ```
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker $USER
  ```
  (log out/in or reboot after this), then follow MeshMonitor's own Docker
  Compose instructions from its README, pointing it at a Meshtastic gateway
  node's IP address

**Install meshing-around (the automated bot):**
```
git clone https://github.com/SpudGunMan/meshing-around.git
cd meshing-around
```
Follow its own `INSTALL.md`. Once installed, apply Charles's customizations:
```
git apply /home/yourusername/cnjmesh-scripts/cnjmesh1/meshing-around-custom/scheduler.py.diff
cp /home/yourusername/cnjmesh-scripts/cnjmesh1/meshing-around-custom/config.ini .
```
(Check `cnjmesh1/meshing-around-custom/upstream-commit.txt` — if the patch
doesn't apply cleanly, it may need adjusting for however far the upstream
project has moved since; ask an AI assistant for help resolving conflicts.)

### A2. Meshtastic Repeater/Gateway Hardware

Meshtastic gateway nodes (referred to as CJG1/CJG2 in the original build) are
Heltec boards flashed with standard Meshtastic firmware, connected to a Pi via
USB or WiFi, feeding MQTT. Flash any Heltec board using the official
Meshtastic web flasher at flasher.meshtastic.org, then configure it to point
at your Mosquitto broker's IP address as its MQTT server.

### A3. Meshtastic Discord Bridges

The `cnjmesh1/graywolf-discord/` and `cnjmesh1/weather-bot/` folders contain
custom Python scripts that post Meshtastic/APRS activity to Discord. For each:
```
cd cnjmesh1/graywolf-discord    # or weather-bot
pip install -r requirements.txt --break-system-packages   # if a requirements file exists; otherwise ask an AI assistant to read the script and list needed packages
cp .env.example .env
nano .env      # fill in real Discord webhook URLs — see Part 9
```
Then set each script up as a systemd service (ask an AI assistant to write
one for you — it needs the script path and Python location).

---

## PART B — Rebuilding the MeshCore Side

### B1. What MeshCore Needs

MeshCore uses a completely different firmware and a different, newer software
ecosystem. The core pattern: a physical repeater relays radio traffic, an
"observer" device captures that traffic and feeds it to MQTT, and dashboards
read from MQTT.

**Flash MeshCore firmware onto a Heltec board:**
Go to the official MeshCore flasher (search "MeshCore firmware flasher" or
check `github.com/meshcore-dev/MeshCore` for current links) and flash the
**Repeater** firmware variant for a permanent relay, or **Companion** firmware
for a device meant to pair with a phone/computer.

**Install meshcore-cli** (a command-line tool for configuring and querying
MeshCore devices):
```
pip install meshcore-cli --break-system-packages
```

**Install meshcore-mqtt** (bridges MeshCore serial traffic into MQTT):
Search GitHub for "meshcore-mqtt" (a Python project) — clone it, then use
`cnjmesh1/meshcore-mqtt/meshcore-mqtt.env.example` as your configuration
template, filling in real values.

**Install CoreScope** (MeshCore network dashboard/map):
```
git clone https://github.com/Kpa-clawbot/CoreScope.git
cd CoreScope
./manage.sh setup
```
The setup wizard will ask about your domain and MQTT connection — point it at
your local Mosquitto broker (`mqtt://localhost:1883`).

**Install MeshCore Hub** (a second, more full-featured MeshCore monitoring
and collection platform):
```
git clone https://github.com/ipnet-mesh/meshcore-hub.git
cd meshcore-hub
npm install
npm run build
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
meshcore-hub db upgrade
```
Then run its collector, api, and web components as described in its own
README (each typically needs to run as its own always-on service).

### B2. MeshCore Repeaters (KPR1, KPR2)

1. Flash a Heltec board with MeshCore **Repeater** firmware (see B1)
2. Configure frequency/spreading factor/power via `meshcore-cli` or the web
   config tool that appears when you plug the board in via USB — match
   whatever the current regional MeshCore network uses (ask community
   contacts, Part 9, since these settings can change as the network evolves)
3. Connect via USB to whichever Pi will host it

### B3. whorepeated (Custom Tool)

This repo includes a custom tool that resolves which repeater relayed a
message, working around MeshCore's 350-contact memory limit. To set it up:
```
mkdir -p /opt/whorepeated
cp cnjmesh1/whorepeated/*.py /opt/whorepeated/
sudo cp cnjmesh1/whorepeated/whorepeated.sh /usr/local/bin/whorepeated
sudo chmod +x /usr/local/bin/whorepeated
```
Full explanation of what it does and why is in `cnjmesh1/whorepeated/` if a
README exists there, or ask an AI assistant to read `path_lookup.py` and
`merge_contacts.py` and explain them.

---

## Part 4: Exposing Dashboards to the Internet (Cloudflare Tunnel)

Both Meshtastic and MeshCore dashboards were made accessible from anywhere
(not just the home network) using Cloudflare Tunnel. This is optional — the
network functions fine without it, it's just a convenience for viewing
dashboards remotely.

1. Create a free Cloudflare account, add your domain (or get a new one)
2. Install `cloudflared` on cnjmesh1 (search "cloudflared install Raspberry
   Pi" for current instructions)
3. Use `cnjmesh1/configs/cloudflared-config.yml` as your reference for which
   local service (Malla, meshview, CoreScope, etc.) maps to which public
   subdomain

---

## Part 5: Glossary

- **Node** — any single device on a mesh network
- **Repeater** — a node that receives and retransmits messages to extend range
- **LoRa** — the long-range, low-power radio technology both networks use
- **Mesh network** — messages hop device-to-device instead of through one central tower
- **MQTT** — lightweight protocol used to move data between software pieces
- **Observer** — a MeshCore device that listens to radio traffic and reports it, without participating as a repeater
- **Bridge** — software connecting two different systems (e.g., radio mesh to Discord)
- **SSH** — remotely controlling a computer using only text commands
- **Docker / container** — a way of packaging software to install and run it in an isolated, predictable way
- **Repository (repo) / git** — a system for saving and tracking versions of code and configuration
- **systemd service** — tells Linux "run this program automatically, restart if it crashes"
- **Webhook** — a URL that, when messaged, automatically posts content somewhere (e.g. a Discord channel)

---

## Part 6: If You Get Stuck

Copy the exact error you're seeing, paste it to an AI assistant along with
this document, and ask: *"I'm on Part [X], step [Y], and got this error. What
do I do?"* This is the same iterative process used to build the entire system
originally — nobody expects you to know it all going in.

---

## Part 7: Priority Order If Time/Resources Are Limited

1. **Keep the repeaters (KPR1, KPR2) powered and on the air** — this is the
   actual radio service the community depends on; everything else is support
   infrastructure around it
2. **Discord bridges** — this is how the community sees mesh activity without
   owning a radio
3. **Dashboards** (Malla, meshview, CoreScope, MeshCore Hub, Grafana,
   MeshMonitor) — genuinely useful, but lowest priority under time pressure

---

## Part 8: Where to Find Real Credentials

**[Charles: fill this in — where is your password manager or vault? Do not
write actual passwords into this file.]**

---

## Part 9: People Who Can Help

- **SGA** and **Tck** — already have Discord admin access on both community
  servers, and GitHub collaborator access to this repository, specifically so
  they can assist with recovery
- **Tilly** — MeshOmatic/AOI sponsor, familiar with the broader mesh mapping ecosystem
- **AkkerKid** — MeshOmatic admin
- **KB2EAR** — nearby ham radio operator, familiar with the regional repeater landscape
- **Compy (KD2QED)** — runs similar mesh infrastructure in Atlantic County

---

*Maintained alongside this repository. Last updated [DATE — update when revised].*
