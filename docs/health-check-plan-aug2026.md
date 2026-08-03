# Health Check Plan — cnjmesh3 + cnjmesh1 RF/APRS services (drafted Aug 2, 2026)

Run through these in order next session. All commands are read-only diagnostics unless noted. Each host is labeled explicitly.

---

## PART 1 — cnjmesh3 general health

**On cnjmesh3:**
```
uptime && free -h && df -h /
```
Watch for: load average (cnjmesh3 is a Pi 3B, 1GB RAM — less headroom than cnjmesh1), disk %, swap usage.

```
docker ps -a --format 'table {{.Names}}\t{{.Status}}'
```
Expect running: `meshcore-mqtt-bridge` (KPR2), `meshcore-packet-capture` (Observer). Both should be `Up ... (healthy)` or at least `Up`.

**Check cnjmesh3 → cnjmesh1 broker reachability (the "reporting in OK" link):**
```
ping -4 -c 3 -W 2 10.0.0.181
```
Both cnjmesh3 containers publish to `10.0.0.181:1883` (cnjmesh1's Mosquitto). If this fails, nothing from cnjmesh3 reaches CoreScope/Hub regardless of container health.

**Docker log rotation check (cnjmesh3) — same disk-fill risk we just fixed on cnjmesh1:**
```
cat /etc/docker/daemon.json 2>/dev/null || echo "NO daemon.json - logs UNBOUNDED"
sudo du -sh /var/lib/docker/containers/*/*-json.log 2>/dev/null | sort -rh | head -5
```
If no daemon.json, cnjmesh3 has the same unbounded-log exposure cnjmesh1 had. Worth fixing proactively (10m x3, then docker restart).

---

## PART 2 — Observer health (cnjmesh3, RAK4631, /dev/ttyACM0)

Container: `meshcore-packet-capture` (image `ghcr.io/agessaman/meshcore-packet-capture:latest`), USB device bound via `/dev/serial/by-id/usb-RAKwireless_WisCore_RAK4631_Board_06308D8BE14915FD-if00`.

**On cnjmesh3:**
```
docker logs --tail 30 meshcore-packet-capture 2>&1 | tail -30
```
Looking for: serial connection to the RAK4631 established, actively capturing packets with SNR/RSSI, and connections to its 4 brokers (letsmesh-us, letsmesh-eu, meshomatic, local=10.0.0.181). config.d files at `/opt/meshcore-packet-capture/config.d` (`10-letsmesh.toml`, `20-meshomatic.toml`, `30-local.toml`).

**Confirm the USB serial device is still present (board didn't drop off the bus):**
```
ls -l /dev/serial/by-id/ | grep RAK4631
```

---

## PART 3 — KPR2 repeater health (cnjmesh3, Heltec V4, /dev/ttyACM1)

Container: `meshcore-mqtt-bridge` (image `meshcore-mqtt:local`, a local build — NOT the public ghcr image). USB device: `/dev/serial/by-id/usb-Espressif_Systems_heltec_wifi_lora_32_v4_..._E8F60AC9DEB4-if00`. Credentials `meshdev`/`large4cats`.

**On cnjmesh3:**
```
docker logs --tail 30 meshcore-mqtt-bridge 2>&1 | tail -30
```
Looking for the bridge status line: it prints `=== Bridge System Status ===` with `MESHCORE: connected` and `MQTT: connected`. **IMPORTANT — compare against KPR1's known issue below:** the cnjmesh1 KPR1 bridge was showing `MQTT: disconnected` while MESHCORE connected. Verify KPR2 shows BOTH connected. If MQTT is disconnected here too, it points at a broker-side problem on cnjmesh1 (Mosquitto), not the individual bridges.

**Confirm KPR2's USB serial device present:**
```
ls -l /dev/serial/by-id/ | grep heltec
```

---

## PART 4 — KPR1 repeater health (cnjmesh1, Heltec V3, /dev/ttyUSB1)

Container: `meshcore-mqtt-kpr1-bridge`. **KNOWN ISSUE as of Aug 2:** logs showed `MESHCORE: connected | MQTT: disconnected` repeatedly. Suspected downstream of the disk-100%-full emergency (Mosquitto struggling) — RECHECK now that disk is recovered to 52%.

**On cnjmesh1:**
```
docker logs --tail 30 meshcore-mqtt-kpr1-bridge 2>&1 | tail -30
```
If MQTT is STILL disconnected after the disk fix: check whether Mosquitto is healthy and accepting connections:
```
docker logs --tail 20 mosquitto 2>&1 | tail -20
```
Also relevant: KPR1 retirement is a pending decision in the long-term notes (Charles didn't want to run 2 repeaters; KPR1 is in the garage, worse location than KPR2). If KPR1's bridge is chronically broken, that may just accelerate the retirement decision rather than being worth fixing.

**Confirm KPR1 USB serial present (cnjmesh1):**
```
ls -l /dev/serial/by-id/ 2>/dev/null | grep -i cp210
```

---

## PART 5 — APRS health (cnjmesh1)

### 5a. Graywolf APRS + Discord bridge
Services: `graywolf-discord.service` (enabled/active, `/opt/graywolf-discord/graywolf-discord-bridge.py`), plus watchdog timers.

**On cnjmesh1:**
```
systemctl status graywolf-discord --no-pager -l | head -12
journalctl -u graywolf-discord --no-pager -n 20 --since "-1 hour"
```
Note: `aprs-monitor.service` is intentionally DISABLED (per install-map) — that's expected, not a problem.

### 5b. aprs-tnc-web (browser APRS messaging UI, port 8085)
Containers: `nextjs_app` + `mysql_database` (compose project `aprs-tnc-web`, `/opt/aprs-tnc-web`, local arm64 image `aprs-tnc-web-local:latest`).

**On cnjmesh1:**
```
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'nextjs|mysql|NAMES'
curl -sS -m 10 -o /dev/null -w "aprs-tnc-web(8085): %{http_code} in %{time_total}s\n" http://localhost:8085/
```

---

## PART 6 — LoRa APRS health (K2GIA-10 iGate + bridge)

K2GIA-10: LilyGO T3 LoRa32 V1.6.1, reserved IP `10.0.0.74`, firmware CA2RXU_LoRa_iGate v3.2.4. Web UI `http://10.0.0.74`. Radio: 433.775 MHz, SF12, CR 4/5, BW 125kHz, 20dBm. Syslog → cnjmesh1 (10.0.0.181) UDP 1514.

**From cnjmesh1 — is the iGate node reachable on the network:**
```
ping -4 -c 3 -W 2 10.0.0.74
curl -sS -m 10 -o /dev/null -w "K2GIA-10 web UI: %{http_code}\n" http://10.0.0.74/
```

### LoRa APRS → Discord bridge
`lora-aprs-discord-bridge-v2.py` at `/opt/lora-aprs-discord/`, listens UDP 1514, parses MESSAGE-format syslog, posts to Discord. **KNOWN OPEN ITEM: was never fully confirmed posting to Discord end-to-end** (last test interrupted). 

**On cnjmesh1 — is the bridge running and listening on 1514:**
```
ps aux | grep lora-aprs-discord | grep -v grep
sudo ss -ulnp | grep 1514
```
If running: end-to-end test = send a test message via aprs-tnc-web, confirm it lands in Discord.

**Known open item (do NOT re-investigate blindly):** K2GIA-10 does NOT self-gate its own outgoing messages to APRS-IS (confirmed via aprs.fi). The planned fix is a second cheap RX-only ESP32 LoRa board — but Charles wanted the `richonguzman/LoRa_APRS_iGate` firmware source checked FIRST before buying hardware. That source check is still pending.

---

## REBOOT CONSIDERATION (cnjmesh1)
After today's work (mqtt-filter removed, 30GB log cleared, lots of Docker churn), a reboot of cnjmesh1 is REASONABLE to clear 9+ days of accumulated swap/memory pressure and get a clean baseline. BUT: do it deliberately with 15-20 min to watch all 16 containers + systemd services (meshview, graywolf, weather bots, etc.) recover, on a memory-tight box — NOT as the last action before walking away. The mqtt-filter removal IS persistent, so a reboot won't undo today's fix. If rebooting, run this whole health-check plan afterward to confirm everything came back.
