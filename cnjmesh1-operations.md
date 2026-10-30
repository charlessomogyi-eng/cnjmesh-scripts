# CNJ Mesh — Operations Runbook
**For:** Anyone keeping CNJ Mesh running when Charles is unavailable.
**Last updated:** 2026-10-13 (header date bumped; some content dates from 2026-07-24 and later)

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
| /dev/ttyACM1 (or via `/dev/serial/by-id/usb-Espressif...`) | **KPN6 (roof-antenna MeshCore/Meshtastic node) — USB power/serial connection to cnjmesh1 (this row). **CORRECTION Oct 30 2026 [S, Charlie]: KPN6 DOES have Wi-Fi.** The older "no WiFi by design, network-unreachable" wording is out of date: Charlie says he recently changed this (exact date not recorded; it was accurate in Aug). It explains why KPN6 uploads to cnjmesh1's broker by itself (MQTT on, client proxy off, seen Oct 25). **Its IP is 10.0.0.202 [V, Meshtastic app Network list, Oct 30 2026]** (not yet reserved in the router). Firmware 2.7.25.104df5f, USB-powered** | Espressif native USB (JTAG + serial interface, NOT a CH340/CP2102 bridge chip), unique serial `90:70:69:84:1F:E0` | Not behind the powered hub — sits one level off the Pi's own built-in hub structure, same tier as the powered hub itself |
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
| mesh-discord-shim | **MeshCore** new-node/advertisement events → Discord (confirmed Sep 2, 2026: subscribes to MeshCore Observer pubkey `a8c40bf3`, logs `advertisement`/`channel_msg_recv` events — NOT Meshtastic, NOT APRS) |
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
2. **Watchdogs → Discord (service-level)** — is a specific critical service actually alive, independent of host reachability. Alert-on-state-change only (no repeat spam). Seven active: `disk-temp-watchdog` (disk/CPU-temp/undervoltage, all 3 Pis), `ingest-rate-watchdog` (packet-flood/loop-node detection, cnjmesh1), `meshcore-bot-watchdog` (cnjmesh1), `sjmesh-relay-watchdog` (heartbeat-file based, cnjmesh1), `graywolf-watchdog` (alert-only, PTT risk, cnjmesh1), `graywolf-discord-watchdog` (auto-restart, cnjmesh1), `mesh-discord-shim-watchdog` (container-state + log-freshness, MeshCore-specific, cnjmesh1). See `watchdogs/` in this repo.
3. **peer-check** — retired Sep 2, 2026. Pi-to-Pi LAN ping was structurally unreliable (a router reboot makes every Pi look down at once, indistinguishable from a real outage). Fully superseded by Fing for host-level detection.

**Known gaps, not yet covered by any layer:** none as of Sep 2, 2026 — every service identified as unwatched (`graywolf-discord-bridge`, `graywolf.service`, `mesh-discord-shim`) now has a working, git-committed watchdog. `aprs_monitor.py`'s 48hr dead-air check is CLOSED/rejected (Sep 2, 2026) — APRS traffic volume isn't a reliable health signal, so this stays permanently disabled; `graywolf-watchdog` (service-up check) is sufficient. CoreScope's `local` source instability is unmonitored (root cause is known, see `todos.md` and session-log Aug 4 entry — no auto-heal built yet). See `todos.md` for current priority.

---


## Public URLs (via Cloudflare tunnel)
| URL | What it is |
|---|---|
| meshcorehub.cnjmesh.me | MeshCore Hub — node map |
| corescope.cnjmesh.me | CoreScope — packet map |
| grafana.cnjmesh.me | Grafana dashboards |
| malla.cnjmesh.me | Malla mesh map (public, no login since Oct 28 2026; only graywolf.cnjmesh.me still sits behind Cloudflare Access) |

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
- Interface: Digirig — check current path with `ls -l /dev/serial/by-id/` rather than assuming a fixed `/dev/ttyUSBx`. A clean same-port replug normally keeps the same index; renumbering happens on reboot, hub power-cycle, another device on the bus also down, or a process holding the device open at unplug. The by-id path is the durable reference.
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
  - **Update 2026-10-13 (apparent contradiction, flagged — not resolved):** this entry, "Common Problems" item 5 and `docs/aprs-2m-graywolf-reference.md` all say the Graywolf watchdog is disabled / must not be re-enabled, but the "Monitoring — Current State" section above lists `graywolf-watchdog` as one of seven **active alert-only** watchdogs, `watchdogs/graywolf-watchdog/` is in git, and `todos.md` (Sep 2 decision) calls the timer active. Likely reading ([I] per the ops handoff): the *old auto-restart* watchdog was disabled because its restarts broke PTT; the Sep 2 `graywolf-watchdog` is alert-only (never restarts) and is active. Never add a restart action. Confirm on **cnjmesh1**: `systemctl status graywolf-watchdog.timer`.
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


---

## Update 2026-10-13 — notes appended from the handoff merge (old text above left in place)
- **USB map (Sep 24, [V] `ls -l /dev/serial/by-id/` 16:25):** the table above has K2GIA-10 (`58EF089845`) = ttyACM0 and K2GIA-9 (`58EF088583`) = ttyACM2. On Sep 24 it was the reverse: `58EF088583` -> ttyACM0, `58EF089845` -> ttyACM2; KPN6 (Espressif `90:70:69:84:1F:E0`) = ttyACM1; Digirig CP2102N (`beb31e2f...`) = ttyUSB3; CP2102 serial `0001` = ttyUSB2. Same-port replug normally keeps a number; renumbering happens on reboot, hub power-cycle, another device dropping, or a device being held open [I]. Prefer by-id paths. `ttyUSB2` references in "Common Problems" above are therefore unreliable for Digirig.
- **Digirig line in "APRS Reference" — corrected 2026-10-13:** the original line said "check current path with `udevadm`, don't assume `/dev/ttyUSB2` (paths shift after USB reconnects)". An attached `.patch` (local commit `45ca39f`) in the aprs-github handoff was meant to correct it but was never provided; Charles supplied the corrected wording directly and the line was replaced (see the USB-map note above for the Sep 24 evidence).
- **Graywolf PTT:** `ptt_configs` already uses the by-id path (see `known-issues.md` update). The "UPDATE ... device='/dev/ttyUSB2'" fix in "Common Problems" is the *old* approach — use the by-id path shown under "USB Devices" instead.
- **Graywolf RX loss recovery (Sep 24):** if RX is dead while TX works (DCD dark, POLLERR flood), replugging the Digirig restored RX. Unproven whether hub power-cycle or Digirig replug alone did it. Check `ls -l /dev/serial/by-id/` afterward — the Digirig may come back on a new ttyUSB number.
- **KPR1/KPC1 serial `0001`:** only one `0001` by-id entry shows (ttyUSB2). Check `ls -l /dev/kpc1 /dev/kpr1` on cnjmesh1 to see which board is present. (Done Oct 14: `/dev/kpc1 -> ttyUSB2`, `/dev/kpr1 -> ttyUSB0`; see the Oct 14 KPC1 update at the end of this file.)
- **Graywolf Discord bridge BLOCKLIST** (`cnjmesh1/graywolf-discord/graywolf-discord-bridge.py` in this repo): `ANSRVR`, `9W2KEY-12`, `CT7AQH-5`, `OTA`; any message whose from or to call is listed is skipped in both the journal and DB-poller paths, so ANSRVR traffic never reaches Discord by design (reason per Charles: automated-reply spam). The bridge logs only on post success/error, so an empty journal is not evidence of silence. Whether the live `/opt/graywolf-discord/` copy matches the repo copy is unverified — compare with `md5sum` on cnjmesh1. Four webhooks (`aprs-rf-nj`, `aprs-internet-nj`, and the `-mc` MeshCore-server copies); the same channel names exist in both Discord servers.


## Update 2026-10-13 — MeshCore Node Reference additions (from KPR3 / 500 kHz cutover handoff; old table above left in place)
Tags: [V] = user showed or said it explicitly, [S] = secondhand, [I] = inference. Hardware and pubkey prefixes below come from the handoff's chat record.

| Node | Hardware | Public Key Prefix | Location / role |
|---|---|---|---|
| **KPR3** | RAK4630 + RAK19003, solar-charged | `29dda9e3` | Backyard/outside, ~13 ft mast, 9-element Yagi (N-female; N-male to RP-SMA pigtail), vertical polarization [S]. Repeater. **First node moved to 500 kHz (Oct 11).** TX power setting unknown — never shown in that chat. |
| **KPC2** | LilyGo T-Deck (companion, personal) | `e14166b8` | House, phone-app/standalone. On 500 kHz as of Oct 11. **Same physical device as "KPN2"** — see conflict note below. |

**Settings used on the 500 kHz cutover [V]:** 910.525 MHz, BW 500 kHz, SF10, CR5 (values supplied by community admin Tck). Previous KPR3 values were not recorded in that chat. Procedure that worked [V]: change repeater (App: Repeater Admin -> Radio Settings -> check mark, "OK - reboot to apply"), reboot, then change companion and reboot. The app's reboot gives no confirmation; the first KPR3 reboot probably did not apply and a second was needed [I].

**Status of the rest [S] (updated Oct 14):** only KPR1 is still on 62.5 kHz; the Observer moved to 500 kHz on Oct 13, KPR2 (confirmed ~12:00 PM by a "Heard 3 Repeats" screenshot showing it repeating a KPC2 message) and KPC1 on Oct 14 (see below). Nodes on different BW/SF/frequency cannot hear each other or be remotely administered across the split.

**Conflicts flagged between the KPR3 handoff and this repo (not silently resolved):**
- The handoff says the repo has no KPR3, 910.525, 62.5 or KPC2 anywhere. **Not true:** 910.525/62.5/SF7/CR5 are in `docs/meshcore-repeater-settings.md` and `docs/nyme-sh-summary.md`; KPC2 is in `docs/nws-weather-bot-reference.md`; session-log Aug 8 says KPN2 and KPC2 are the same T-Deck. KPR3 and 500 kHz really are new.
- **KPN2 vs KPC2 — RESOLVED Oct 23, 2026 [V, Charlie]:** one physical LilyGo T-Deck Plus. **KPN2** was its name while running Meshtastic firmware (its Jul 14 WiFi/IP designation, `10.0.0.140`, MAC `80:b5:4e:ce:c3:14`). When it was reflashed to MeshCore, it became **KPC2**. Use KPC2 going forward for its current (MeshCore) identity; KPN2 is the historical Meshtastic-era name for the same hardware, kept in older notes for context only.
- **KPR1 status:** the table above says "RETIRED" while this file's USB table says KPR1 is NOT retired and dedicated to the Tilly integration, and `todos.md` says KPR1 is active (CNJ endpoint `b`). The handoff's user statement treats KPR1 as live on 62.5 kHz. Pre-existing repo inconsistency; flagged, not edited.
- **Observer model:** "WisMesh Pocket v2, RAK4631" vs "WisMesh Pocket RAK4631" in the tables here; the handoff's chat summary calls it "WisMesh Pocket Mini". Unknown which is right — Charles to confirm.
- **Regulatory caution ([S]/[I], from a pasted groups.io thread; not legal advice, CFR not verified here):** Part 15.247 treats 500 kHz bandwidth as necessary but not sufficient for 1 W; EIRP cap 36 dBm; module grant may not cover a gain antenna. Charles to decide whether the KPR3 Yagi setup and TX power are within the module's grant; record the actual TX power once known.


## Update 2026-10-13 — Meshtastic node reference: KPN2 (from KPN2 WiFi/T-Deck handoff; [V] unless noted)
The MeshCore tables above don't cover the T-Deck. (`session-log.md` has carried a KPN2 row since July; this file never did.)

| Node | Hardware | IP / hostname | MAC | Notes |
|---|---|---|---|---|
| KPN2 (= KPC2 in its MeshCore role; same physical device, see Aug 8 session-log) | LilyGo T-Deck Plus | 10.0.0.140 (DHCP reservation in the Xfinity router), `esp32s3-CEC314` | `80:b5:4e:ce:c3:14` | WiFi SSID `C4Somogyi-24` (2.4 GHz). Firmware `2.7.15.567b8ea` is a dev build; stable was `2.7.19.bb3d6d5` when checked — reflash target in flasher.meshtastic.org is **T-Deck** (not T-Deck Pro) [I]. |

Also identified on Oct 9 via `arp -a` on cnjmesh2: CJG1 = `esp32s3-CA423C` at 10.0.0.18, MAC `e8:f6:0a:ca:42:3c` (matches MQTT client ID `!0aca423c`); CJG2 = `esp32s3-A3E8D4` at 10.0.0.234 (Charles confirmed; shows as `Meshtastic` in the phone app's discovered devices).

**MQTT — flagged, not resolved:** the handoff states KPN2 uses `meshuser` credentials and "does NOT connect to cnjmesh1/cnjmesh2 Mosquitto", but its only evidence is that `docker logs mosquitto` on **cnjmesh2** showed no `meshuser` hits. Nothing was checked on cnjmesh1, and the `MQTT Brokers` table above lists `meshuser` on `mqtt.cnjmesh.me` (CNJ's own public broker, which terminates on cnjmesh1). So "external broker" is unverified; KPN2 may well use `mqtt.cnjmesh.me`. Check KPN2's MQTT settings (web client over USB) and cnjmesh1's Mosquitto logs before relying on the handoff's statement. Credential rotation dependency: any rotation of `meshuser` on whichever broker KPN2 uses requires reconfiguring KPN2 too.

## Update 2026-10-14 — Observer moved to 500 kHz (cnjmesh3); runbook (from the Observer handoff; [V] = pasted command output)
**Node reference addition (old tables above left in place):**

| Node | Hardware | Public Key Prefix | Location / radio |
|---|---|---|---|
| Observer ("CNJ Mesh Observer") | RAK4631 (WisMesh Pocket; exact revision still unconfirmed — see model conflict above), **companion firmware v1.16.0-07a3ca9, USB serial** | `a8c40bf3` | `/dev/ttyACM0` on cnjmesh3 (by-id `*RAK4631*`). **Cut over Oct 13, 2026 to 910.525 MHz / 500 kHz / SF10 / CR5** (was 910.525 / 62.5 / SF7 / CR5); tx_power 22. |

Capture log after the change: "Radio info: 910.525,500.0,10,5", 4/4 MQTT brokers connected (letsmesh-us, letsmesh-eu, meshomatic, local 10.0.0.181:1883), packets captured within ~5 s, SNR ~7–8 dB at RSSI -90 to -50. Observer clock problem: see `known-issues.md`.

**Runbook — change the Observer's radio settings** (worked Oct 13; the `meshcore-cli` path is `/home/somog/.local/bin/meshcore-cli`). `meshcore-packet-capture` holds the serial port, so stop it first; the cnjmesh3 watchdog does not touch that container (`grep -n -i packet /opt/meshcore-mqtt-watchdog/watchdog.sh` returned nothing).

Run this on **cnjmesh3**:
```bash
docker stop meshcore-packet-capture
D=$(ls /dev/serial/by-id/*RAK4631*)
meshcore-cli -s $D infos
```
Still on **cnjmesh3** (example values; use the network's current ones):
```bash
meshcore-cli -s $D set radio 910.525,500,10,5
meshcore-cli -s $D infos
```
`set radio` replied `ok` and applied immediately on this firmware; the read-back showed the new values. A `reboot` test (wait ~20 s, `infos` again) still showed them, but the output did not show uptime, so the reboot itself is not proven [I]. Then, still on **cnjmesh3**:
```bash
docker start meshcore-packet-capture
docker logs meshcore-packet-capture --tail 20
```
Expect the new "Radio info" line, 4/4 brokers, and "Waiting for packets...". After the change the Observer hears only the new settings, so nodes still on the old ones disappear from the feeds.

## Update 2026-10-14 — KPR2 moved to 500 kHz (cnjmesh3); repeater-console runbook (from the KPR2 handoff; [V] = pasted output/screenshots, [I] = inference)
**KPR2 entry update (old MeshCore table above left in place — it still shows KPR2 with the old location text):** Heltec WiFi LoRa 32 V4 (16 MB flash / 2 MB PSRAM), MeshCore **repeater** firmware 1.16.0-07a3ca9 (Build 06-Jun-2026), advertised as "Kendall Park Repeater 2", `/dev/ttyACM1` on cnjmesh3 (by-id `*heltec*`). Radio was 910.525 / 62.5 kHz / SF7 / CR5; set to **910.525 MHz / 500 kHz / SF10 / CR5 on Oct 14, 2026** (`get radio` prints `910.5250244,…` — float rounding of 910.525). [V] for the commands and read-backs, **[I] for the radio actually running 500 kHz**: the Observer (next to KPR2, on 500 kHz) logged a type-4 advert at -25 dBm the moment `advert` was sent, plus relayed copies at -53/-115/-91 dBm. Whether KPR2 rebooted is unknown (the console did not drop on `reboot`, twice).

**Runbook — change KPR2's radio settings (repeater console).** The `meshcore-mqtt-bridge` container holds KPR2's serial port, so stop it first (its KPR2 feed has a gap meanwhile; it was ~25 min on Oct 14). Run this on **cnjmesh3**:
```bash
docker stop meshcore-mqtt-bridge
K=$(ls /dev/serial/by-id/*heltec*)
timeout 300 meshcore-cli -s $K -r
```
Inside that console (on **cnjmesh3**; use the network's current values): `get radio`, then `set radio 910.525,500,10,5` (answers "OK - reboot to apply"), then `reboot`. Plain `meshcore-cli infos` does not work on repeater firmware ("To connect to a repeater, use -r"). **`get radio` is not proof** — it shows the saved value even before a reboot. If the console does not drop after `reboot`, treat the reboot as unconfirmed and power-cycle KPR2 (USB, plus battery if connected; the bare V4 has no power switch and its buttons did not behave as expected). Verify with a real packet: in the console run `advert` (replies "OK - Advert sent") and look for a new strong type-4 packet in the Observer's log, still on **cnjmesh3**:
```bash
docker logs meshcore-packet-capture --tail 40
```
Then restart the bridge, still on **cnjmesh3**:
```bash
docker restart meshcore-mqtt-bridge
docker ps
```
Expect the bridge "Up ... (healthy)" and a log line "MeshCore CONNECTED ... /dev/ttyACM1". After a power cycle of the Observer, `docker restart meshcore-packet-capture` is a cheap precaution.

## Update 2026-10-14 — KPC1 moved to 500 kHz; weather bot restarted; runbooks (from the KPC1 handoff; [V] = pasted output)
**KPC1 row update (old USB-table row above left in place):** Heltec V3 companion, board name **"CNJWeatherBot"**, companion firmware v1.16.0-07a3ca9, tx_power 22/22, public-key prefix `df8a4432`, `/dev/kpc1 -> ttyUSB2` as of Oct 14 (KPR1: `/dev/kpr1 -> ttyUSB0`; both symlinks dated Sep 24 15:52). **Radio changed Oct 14 from 910.525 / 62.5 / SF7 / CR5 to 910.525 MHz / 500 kHz / SF10 / CR5.** KPC1 sits on the powered hub, KPR1 directly on the Pi, matching the table above. KPR1 was not touched; `/dev/kpr1` is held by the healthy `meshcore-mqtt-kpr1-bridge` container. Because KPC1 and KPR1 share serial `0001`, the symlinks name USB *ports* — only `infos` says which board is which.

**Which bot is which:** the CentralNJ-MC weather bot is **`meshcore-bot.service`** (agessaman/meshcore-bot, config `/etc/meshcore-bot/config.ini`, `serial_port = /dev/kpc1`, runs `/opt/meshcore-bot/meshcore_bot.py`). `meshing-around` (`/opt/meshing-around/`) is the separate `mesh_bot.service`. Any text in this repo that calls the weather bot "meshing-around" is wrong.

**Runbook — change KPC1's radio settings.** KPC1 is a companion, so `meshcore-cli ... infos` and `set radio` work (unlike the KPR2 repeater console). The bot holds `/dev/kpc1` while it runs, so stop it first (the port was already free on Oct 14 because the bot was down). Run this on **cnjmesh1**:
```bash
sudo systemctl stop meshcore-bot.service
meshcore-cli -s /dev/kpc1 infos
```
Still on **cnjmesh1** (example values; use the network's current ones):
```bash
meshcore-cli -s /dev/kpc1 set radio 910.525,500,10,5
meshcore-cli -s /dev/kpc1 infos
sudo systemctl start meshcore-bot.service
```
`set radio` answered `ok` and the read-back showed the new values immediately (name "CNJWeatherBot" confirms it is KPC1, not KPR1).

**Runbook — weather bot recovery (`start-limit-hit`).** Run this on **cnjmesh1**:
```bash
systemctl status meshcore-bot.service
sudo systemctl reset-failed meshcore-bot.service
sudo systemctl start meshcore-bot.service
systemctl is-active meshcore-bot.service
journalctl -u meshcore-bot.service -n 30
```
Make sure KPC1 is actually present first (`ls -l /dev/kpc1`), otherwise the bot exits again. Detail and the watchdog's design gaps: `known-issues.md`.

## Update 2026-10-23 — logging, backups, alert text, cnjmesh2 resets ([V] = pasted command output)

- **Journals are now persistent on all three Pis** (drop-in `/etc/systemd/journald.conf.d/50-persistent.conf`; cnjmesh1 at 19:22 [V], cnjmesh3 at 21:10 [V], cnjmesh2 active since its Oct 22 reboot [V]). Before this, cnjmesh1 and cnjmesh3 kept logs in RAM only (Raspberry Pi OS default). History is capped by `SystemMaxUse=100M` and `MaxRetentionSec=3day` in `/etc/systemd/journald.conf` on cnjmesh1.
- **cnjmesh2 (Pi Zero 2 W) resets on its own:** Oct 22 ~20:30 (hung until power-cycled), 20:54 (Wi-Fi SDIO errors then freeze; auto-reset), Oct 23 ~01:00 (healthy then abrupt stop; auto-reset). Hardware watchdog (`RuntimeWatchdogSec=15`) is active [V]. A **flight recorder** (`flight-recorder.timer`, script `/usr/local/bin/flight-recorder.sh`, source `cnjmesh2/flight-recorder/`) logs one health line a minute to the journal (tag `flight-recorder`). After any reset read `journalctl -b -1 -t flight-recorder | tail` and `journalctl -b -1 | tail -40`. Plan: swap power supply/cable, then try a USB Wi-Fi dongle; wired Ethernet is not possible (Pis sit by their antennas). Optional `cnjmesh1/ping-watch/` (logs cnjmesh2 up/down on cnjmesh1) is written but NOT installed. Details: `known-issues.md`.
- **Weather bot (`meshcore-bot.service`, `/opt/meshcore-bot`, config `/etc/meshcore-bot/config.ini`):** NJ filter live since Oct 20 20:23 (confirmed by a real Mount Holly frost advisory Oct 23); `patch_office_full_name.py` applied Oct 23 20:07 (backup `weather_service.py.bak-officename-20261023-200714`), bot restarted 20:13 [V] (active, 910.525/500/SF10/CR5, receiving RF). The bot keeps already-sent alert ids in memory, so a restart can re-announce an active alert once.
- **Backups:** scripts, archives and the laptop pull are described in `docs/backup-guide.md`. Archives made Oct 23: `cnjmesh1-backup-2026-10-23_2029.tar.gz` (180M), `cnjmesh1-extra-2026-10-23_2043.tar.gz` (123M, mode 600), `cnjmesh3-backup-2026-10-23_2110.tar.gz` (620K); all three pulled to `C:\Users\charl\OneDrive\Documents\cnjmesh-backups` via the desktop shortcut for `pull-cnjmesh1-backup.ps1` (answer Y to the Execution Policy prompt). `~/backups` on cnjmesh1 still holds ~4.7 GB of old Malla snapshots (not cleaned).
- **cnjmesh3 facts found Oct 23 [V]:** only SSH listens; containers `meshcore-mqtt-bridge` (bind `/home/somog/meshcore-bridge-data -> /data`, SQLite `packet-bridge-b.sqlite3` idle since Jul 28) and `meshcore-packet-capture` (bind `/opt/meshcore-packet-capture/config.d`); `~/meshcore-mqtt-tilly` is Tilly's bridge fork; `iata = "EWR"` in `20-meshomatic.toml`; no cron jobs, no Docker volumes.
