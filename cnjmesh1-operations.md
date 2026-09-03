# CNJ Mesh — Operations Runbook
**For:** Anyone keeping CNJ Mesh running when Charles is unavailable.
**Last updated:** 2026-07-24

If you are an AI assistant, this file plus `todos.md` are the two short files to fetch at the start of a session. Only fetch `session-log.md` (long, narrative) if you need the backstory behind something. This document focuses on current-state reference facts, day-to-day operations, common problems, and who to contact.

**Philosophy — keep this simple, don't over-engineer.** Charles has been explicit about this: he wants tools that work reliably so he can focus on actual radio contacts, not on managing tooling. Default to the simplest fix that closes a real, already-experienced problem. Don't build speculative monitoring/architecture for problems that haven't happened yet — see "Known Issues" below for a specific example (container-level watchdog, deliberately deferred).

---

## Who to Contact First
| Person | Role | Where to Find |
|---|---|---|
| KB2EAR | Closest neighbor, local repeater operator, APRS user | MeshCore NJ Discord |
| SGA | Weather station KD2EEWX, mesh analysis, Discord admin | CNJ Mesh Discord |
| Tck | MeshCore NJ Discord admin | MeshCore NJ Discord |
| Compy / KD2QED | South Jersey, SJMesh operator | SJMesh Discord |

---

## The Three Pis

| Host | IP | User | SSH Command |
|---|---|---|---|
| cnjmesh1 | 10.0.0.181 (static) | somog | `ssh somog@10.0.0.181` |
| cnjmesh2 | 10.0.0.91 | somogyic | `ssh somogyic@10.0.0.91` |
| cnjmesh3 | 10.0.0.186 | somog | `ssh somog@10.0.0.186` |

**cnjmesh1 is the main server.** All critical services run here. cnjmesh2 is the Meshtastic gateway (Pi Zero 2W). cnjmesh3 is the upstairs MeshCore RF hub (Pi 3B+, hosts Observer + KPR2).

**cnjmesh1 is currently a REPLACEMENT board** (original died from a disk-full/hard-power-cycle failure July 21, 2026 — see session-log.md for full story). Same SD card, same config, static IP `.181` confirmed working. WiFi network must be `C4Somogyi-24` (2.4GHz) — mesh hardware doesn't support 5GHz, and there's a separate `C4Somogyi` (5GHz, no suffix) SSID on the same router that's easy to mistake for it.

**cnjmesh1's OS is Debian Trixie.** Important: Trixie replaced `dphys-swapfile` entirely with `rpi-swap` (zram-based). `/etc/dphys-swapfile` does not exist on this OS — don't reference it. Swap config lives at `/etc/rpi/swap.conf` + `/etc/rpi/swap.conf.d/`. Also, `dhcpcd.conf` is not read on this OS — static IPs are set via `nmcli con mod`, not by editing that file. **Applying an `rpi-swap` config change triggers a full reboot**, not a graceful in-place restart — expect that.

---

## USB Devices on cnjmesh1

Run this to see what's connected:
```bash
ls -l /dev/ttyACM* /dev/ttyUSB*
```

**As of Aug 28, 2026** (KPN6 added — confirmed via full `lsusb -t` + `udevadm` audit; had never been documented before despite being a live, currently-connected device):
| Device | What it is | Identifying signature | Connection |
|---|---|---|---|
| /dev/ttyACM0 (or via `/dev/serial/by-id/usb-1a86_...`) | K2GIA-10 / LoRa APRS board (ESP32-S3) | CH340-family chip, vendor 1a86, unique serial `58EF089845` | Powered hub |
| /dev/ttyACM1 (or via `/dev/serial/by-id/usb-Espressif...`) | **KPN6 (roof-antenna MeshCore/Meshtastic node) — no WiFi by design, deliberately network-unreachable; this is its USB power/serial connection only** | Espressif native USB (JTAG + serial interface, NOT a CH340/CP2102 bridge chip), unique serial `90:70:69:84:1F:E0` | Not behind the powered hub — sits one level off the Pi's own built-in hub structure, same tier as the powered hub itself |
| /dev/ttyACM2 (or via `/dev/serial/by-id/usb-1a86_USB_Single_Serial_58EF088583-if00`) | K2GIA-9 / LoRa APRS Tracker board (plugged in Aug 27, 2026, temporary — for stable power, not mobile use while connected here) | CH340-family chip, vendor 1a86, unique serial `58EF088583` — same chip family as K2GIA-10 but a DISTINCT serial, no KPC1/KPR1-style ambiguity | Powered hub |
| **KPC1 (MeshCore companion — as of Aug 8, dedicated to cnjmesh1's weather-bot integration, reflashed to `companion_radio_usb`; no longer Charles's personal device — see T-Deck/KPN2 below)** | Heltec V3 | CP2102, generic serial `0001` (shared with KPR1 — cannot be told apart by serial) | Powered hub, stable symlink `/dev/kpc1` |
| **KPR1 (MeshCore repeater, dedicated to Tilly integration — NOT retired, this doc was wrong)** | Heltec V3 | CP2102, generic serial `0001` (shared with KPC1) | **Direct to Pi**, stable symlink `/dev/kpr1` |
| Digirig — APRS PTT + audio | — | CP2102N, unique serial `beb31e2f...`; audio side is C-Media USB Audio (ALSA card name "Device") | Direct to Pi |

**KPN6 has a genuinely unique factory serial** (unlike KPC1/KPR1's shared `0001`), so a stable `/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_90:70:69:84:1F:E0-if00`-style path auto-generates via standard udev behavior — no custom port-keyed rule needed, and its identity should survive being moved to a different physical port. **Not yet verified: whether anything currently references KPN6 via the raw `ttyACM1` path instead of the by-id path** — worth checking before assuming full port-independence, given the exact same class of mistake (raw path instead of by-id) caused the July 28 KPR1/K2GIA-10 mislabeling incident below. Note: KPN6 was briefly unplugged from cnjmesh1 on Aug 28 to do a firmware upgrade (2.7.23→2.7.25) on a laptop, then replugged into the **same physical port** — not moved, so this wasn't tested as a live port-change scenario.

**KPR1 and KPC1 share an identical generic factory serial (`0001`) and can NEVER be distinguished by serial number/by-id.** Custom udev rules create permanent `/dev/kpr1` and `/dev/kpc1` symlinks keyed to physical USB port instead:
```
# /etc/udev/rules.d/99-meshcore-boards.rules
SUBSYSTEM=="tty", KERNELS=="1-1.4", SYMLINK+="kpr1"
SUBSYSTEM=="tty", KERNELS=="1-1.2.4", SYMLINK+="kpc1"
```
**Caveat:** this ties identity to physical port — if either board moves to a different port, edit the `KERNELS==` value to match (find the new port via `lsusb -t` or `dmesg`). The `meshcore-mqtt-kpr1-bridge` container uses `--device /dev/kpr1:/dev/ttyUSB3`.

For the LoRa board and Digirig (both have unique serials), use `/dev/serial/by-id/` paths, which ARE safe across reboots. USB raw paths (`ttyUSB0`, `ttyACM0`, etc.) are NEVER guaranteed stable — always verify current mapping with `udevadm info -q property -n /dev/ttyUSBx | grep -E "ID_SERIAL|ID_MODEL"` rather than trusting any cached table, including this one. If Digirig's path changes, update Graywolf's PTT config to match:
```bash
sqlite3 /var/lib/graywolf/graywolf.db "SELECT * FROM ptt_configs;"   # check current
sqlite3 /var/lib/graywolf/graywolf.db "UPDATE ptt_configs SET device='/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_beb31e2f33c6ef1186b171527a5e3baa-if00-port0' WHERE id=1;"
systemctl restart graywolf
```

If devices are missing, check physical connections and the powered USB hub.

### cnjmesh3 (Observer + KPR2)
Both physically relocated upstairs to cnjmesh3 (confirmed via `dmesg`):
| Device | What it is |
|---|---|
| /dev/ttyACM0 | Observer (WisMesh Pocket v2, RAK4631) |
| /dev/ttyACM1 | KPR2 (Heltec V4 MeshCore repeater) |

Architecture: Mosquitto broker, MeshCore Hub, and CoreScope all stay on **cnjmesh1**. cnjmesh3's `meshcore-packet-capture` and `meshcore-mqtt-bridge` just publish outward to cnjmesh1's broker at `10.0.0.181:1883` over the LAN — cnjmesh3's only job is hosting the physical USB devices.

---

## Checking What's Running

### Docker containers (most services):
```bash
docker ps
```

Key containers to look for:
| Container | What it does |
|---|---|
| mosquitto | MQTT broker — heart of the system |
| meshcore-packet-capture | Observer → CoreScope/MeshOmatic data feed |
| meshcore-mqtt-bridge | MeshCore → MQTT bridge |
| meshcore-hub | meshcorehub.cnjmesh.me |
| mesh-discord-shim | New node welcome messages to Discord |
| mesh-mqtt-pg-collector | Packet storage to PostgreSQL |

### Systemd services (run as system services, not Docker):
```bash
systemctl status graywolf
systemctl status cloudflared
systemctl status weather-bot-conditions.timer
systemctl status weather-bot-alerts.timer
systemctl status nj-regional-weather-conditions.timer
systemctl status k2gia9-serial-log
```
K2GIA-9's serial output logs continuously to `/var/log/k2gia9-serial.log` (rotated daily, 7 days kept). Setup/deploy: `k2gia9-serial-log/README.md`.

---

## PROTECTED SERVICES — DO NOT REMOVE OR DISABLE
- **Malla** (port 5008) — mesh network map, critical
- **Meshview** (port 8080) — packet viewer, critical
- Do not uninstall, stop, or disable these unless Charles explicitly authorizes it

---

## Monitoring — Current State (as of Sep 2, 2026)

Three layers, no known gaps as of this writing:

1. **Fing (host-level)** — is a Pi reachable on the network at all. Configured for cnjmesh1, cnjmesh2, and cnjmesh3 under Fing's `Home` network (not the stale manual-scan networks like `C4Somogyi-24`, which don't alert). `Notify on State Change` enabled per-device; account-level email format set to "Single email for each event" (`Manage Account → Notifications → Network alerts`), so an offline Pi sends an immediate individual email, not a bundled digest.
2. **Watchdogs → Discord (service-level)** — is a specific critical service actually alive, independent of host reachability. Alert-on-state-change only (no repeat spam). Four active: `disk-temp-watchdog` (disk/CPU-temp/undervoltage, all 3 Pis), `ingest-rate-watchdog` (packet-flood/loop-node detection, cnjmesh1), `meshcore-bot-watchdog` (cnjmesh1), `sjmesh-relay-watchdog` (heartbeat-file based, cnjmesh1). See `watchdogs/` in this repo.
3. **peer-check** — retired Sep 2, 2026. Pi-to-Pi LAN ping was structurally unreliable (a router reboot makes every Pi look down at once, indistinguishable from a real outage). Fully superseded by Fing for host-level detection.

**Known gaps, not yet covered by any layer:** `mesh-discord-shim`, `graywolf-discord-bridge`, and `aprs_monitor.py` don't have their own service-level watchdog yet (candidates, same pattern as `meshcore-bot-watchdog`). CoreScope's `local` source instability is unmonitored. See `todos.md` for current priority.

---


## Public URLs (via Cloudflare tunnel)
| URL | What it is |
|---|---|
| meshcorehub.cnjmesh.me | MeshCore Hub — node map |
| corescope.cnjmesh.me | CoreScope — packet map |
| grafana.cnjmesh.me | Grafana dashboards |
| malla.cnjmesh.me | Malla mesh map |

---

## Common Problems and Fixes

### APRS not working / Graywolf silent
1. Check Graywolf is running: `systemctl status graywolf`
2. Check PTT device: `ls -l /dev/ttyUSB2` — must exist
3. Check logs: `journalctl -u graywolf -n 50`
4. POLLERR errors in logs are **cosmetic** — APRS still works through them
5. **DO NOT re-enable the Graywolf watchdog** — it was disabled intentionally, it was breaking PTT
6. If Digirig moved ports after USB changes, update PTT device in database:
```bash
sqlite3 /var/lib/graywolf/graywolf.db "UPDATE ptt_configs SET device='/dev/ttyUSB2';"
systemctl restart graywolf
```

### Observer not feeding CoreScope / MeshOmatic
1. Check container: `docker ps | grep packet-capture`
2. Check logs: `docker logs meshcore-packet-capture --tail 20`
3. If showing "No such device /dev/ttyACM0": `docker restart meshcore-packet-capture`
4. Verify Observer is on /dev/ttyACM0: `ls -l /dev/ttyACM0`

### Weather alerts not posting to Discord
1. Check service ran: `journalctl -u weather-bot-alerts.service -n 20`
2. Check timer: `systemctl status weather-bot-alerts.timer`
3. Check .env loaded: `systemctl cat weather-bot-alerts.service` — must show EnvironmentFile line
4. Check zone is NJZ012 (Middlesex County) in `/opt/weather-bot/weather_bot.py`

### MQTT broker down
```bash
cd /opt/stacks/mqtt/
docker compose ps
docker compose restart
```

### Cloudflare tunnel down (public URLs not working)
```bash
systemctl status cloudflared
systemctl restart cloudflared
journalctl -u cloudflared -n 30
```

### meshcore-packet-capture lost Observer after USB change
After any USB hub changes, always run:
```bash
docker restart meshcore-packet-capture
docker logs meshcore-packet-capture --tail 10
```

---

## Key File Locations

| File | Location |
|---|---|
| Mosquitto config | `/opt/stacks/mqtt/config/mosquitto.conf` |
| Cloudflare tunnel config | `/etc/cloudflared/config.yml` |
| Weather bot scripts | `/opt/weather-bot/` |
| Weather bot environment | `/opt/weather-bot/.env` |
| Graywolf APRS database | `/var/lib/graywolf/graywolf.db` |
| Graywolf Discord bridge | `/opt/graywolf-discord/` |
| Graywolf Discord .env | `/opt/graywolf-discord/.env` |
| meshing-around bot | `/opt/meshing-around/` |
| Mesh Discord shim | `/opt/stacks/mesh-discord-shim/` |
| Meshview | `~/meshview/` |
| CNJ Mesh scripts repo | `~/cnjmesh-scripts/` |

---

## MQTT Brokers

| Broker | Host | Port | Username | Password |
|---|---|---|---|---|
| Local (cnjmesh1) | localhost | 1883 | meshdev | see Charles |
| CNJ Mesh public | mqtt.cnjmesh.me | 1883 | meshuser | see Charles |
| SJMesh | mqtt.sjmesh.net | 1883 | meshuser | see Compy/KD2QED |

---

## MeshCore Node Reference

| Node | Hardware | Public Key Prefix | Location |
|---|---|---|---|
| KPR1 | Heltec V3 | 0a | **RETIRED — not reconnected, no longer in service** |
| KPR2 | Heltec V4 | 97 | /dev/ttyACM1, cnjmesh3, Alfa antenna |
| Observer | WisMesh Pocket RAK4631 | A8 | /dev/ttyACM0, cnjmesh3 |
| KB2EAR-2 | — | 60 | Neighbor, 772m away |

### MeshCore Channel Keys
- Public channel key: see Charles or MeshCore NJ Discord admins (Tck)
- CentralNJ-MC channel key: see Charles

---

## APRS Reference
**Full detail (config, SSID map, known cpal/POLLERR issue, APRS OTA results): see `docs/aprs-2m-graywolf-reference.md`**
- Callsign: **K2GIA-1** (changed Aug 17 2026 from bare K2GIA — digi+iGate combo SSID convention)
- Runs on **cnjmesh1** (Graywolf web UI port 8082)
- Radio: UV-5R M, **roof dual-band VHF/UHF antenna** (as of Aug 17 2026 — was whip)
- Interface: Digirig — check current path with `udevadm`, don't assume `/dev/ttyUSB2` (paths shift after USB reconnects)
- iGate server: `rotate.aprs2.net:14580`
- Passcode: 16025 (generated from base callsign K2GIA — SSID-independent, unaffected by K2GIA-1 change)
- Digipeater: WIDE1-1, confirmed enabled
- Beacon: every 30 minutes
- **QRX (APRS Missed Message Mailbox)** — free, no-account APRS-IS service. Register by sending an APRS message to `QRX` with text `REG`. Once registered, holds missed messages (up to 7 days / 100 messages) and notifies on your next beacon. Works fine over LoRa APRS too (K2GIA-10), since it operates at the APRS-IS layer, not tied to a specific RF path.

---

## Docker Command Reference

Always run Docker commands for cnjmesh1 from `/opt/stacks/mqtt/`:
```bash
cd /opt/stacks/mqtt/
docker compose ps
docker compose restart
docker compose logs -f
```

For cnjmesh2, always `cd ~/meshtastic-mqtt` first before any docker compose commands.

---

## Known Issues / Don't Touch

- **Graywolf watchdog** — DISABLED intentionally. Files exist at `/etc/systemd/system/graywolf-watchdog.timer` and `.service`. Do not re-enable.
- **meshcore-packet-capture TOML configs** — live inside the container, not on the host. If the container is recreated these configs will be lost. Do not recreate the container without backing up the configs first.
- **Client 1 serial flapping** — Kendall Park Client 1 (Heltec V3) has known CP210x serial instability. This is a known issue, replacement with RAK/WisMesh is planned.
- **MeshOmatic bridge** — configured in mosquitto.conf but MeshOmatic's MQTT broker goes down periodically. This is their problem, not ours. The bridge will reconnect automatically.
- **cnjmesh1 WiFi can silently "stick"** — the interface can report fully healthy stats (good bitrate/signal, TX counter incrementing) while zero traffic actually passes, including to the gateway. Happened twice (July 22-23 and July 24, 2026). Root cause unknown. Fix: `sudo nmcli con down "C4Somogyi-24" && sudo nmcli con up "C4Somogyi-24"` (try this before a full reboot — it's lighter-weight and has worked). See `todos.md` — this is flagged as an open item to actually root-cause if it keeps recurring.
- **Tailscale was found running on cnjmesh1** (July 24, 2026), apparently installed at some point for casual remote access, never fully used, no other services depend on it. Was broken (couldn't reach its own coordination server) and unrelated to that day's actual connectivity issue — ruled out as a red herring. Stopped and disabled permanently. If it reappears or a "why is this here" question comes up again, this is why.
- **Container-level watchdog was deliberately deferred** — peer-check only checks "is the Pi reachable," not "is each Docker container healthy." Considered and explicitly NOT built, per the simplicity philosophy at the top of this file. Don't build it preemptively; revisit only if a specific missed outage justifies it.
- **Malla has a known CVE (stored XSS, CVE-2026-43980)** — node names from public MQTT are rendered unescaped. Check if patched; see `todos.md`.

---

## GitHub Repo
`github.com/charlessomogyi-eng/cnjmesh-scripts`

Full rebuild guide: `README.md`
AI session context: `CLAUDE_CONTEXT.md`
This runbook: `cnjmesh1-operations.md`
