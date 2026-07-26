# Install Map — `cnjmesh3`

_Generated 2026-07-26 19:17:34 EDT by `scripts/collect-inventory.sh`. Re-run to refresh — do not hand-edit._

## Docker containers

### `meshcore-mqtt-bridge`  _(state: running, restart: unless-stopped)_

- **Image:** `meshcore-mqtt:local`
- **Devices:** `/dev/serial/by-id/usb-Espressif_Systems_heltec_wifi_lora_32_v4__16_MB_FLASH__2_MB_PSRAM__E8F60AC9DEB4-if00 `
- **Config env (secrets omitted):**
    - `MQTT_BROKER=10.0.0.181`
    - `MESHCORE_EVENTS=CONTACT_MSG_RECV,CHANNEL_MSG_RECV,CONNECTED,DISCONNECTED,LOGIN_SUCCESS,LOGIN_FAILED,MESSAGES_WAITING,DEVICE_INFO,BATTERY,NEW_CONTACT,ADVERTISEMENT`
    - `MQTT_TOPIC_PREFIX=meshcore`
    - `MQTT_PORT=1883`
    - `PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `PYTHONPATH=/app`

### `meshcore-packet-capture`  _(state: running, restart: unless-stopped)_

- **Image:** `ghcr.io/agessaman/meshcore-packet-capture:latest`
- **Host bind mounts (config/data on disk):**
    - `/opt/meshcore-packet-capture/config.d -> /etc/meshcore-packet-capture/config.d`
- **Devices:** `/dev/serial/by-id/usb-RAKwireless_WisCore_RAK4631_Board_06308D8BE14915FD-if00 `
- **Config env (secrets omitted):**
    - `PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `PACKETCAPTURE_DATA_DIR=/app/data`


## systemd services & timers (user-installed)

_Only units whose file lives under `/etc/systemd/system` (i.e. you/we installed them) — OS/vendor units under /lib and /usr/lib are excluded._

### `disk-temp-watchdog.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/disk-temp-watchdog.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/disk-temp-watchdog/watchdog.py ; ignore_errors=no ; start_time=[Sun 2026-07-26 19:15:42 EDT] ; stop_time=[Sun 2026-07-26 19:15:42 EDT] ; pid=702363 ; code=exited ; status=0 }`

### `disk-temp-watchdog.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/disk-temp-watchdog.timer`

### `meshcore-mqtt-watchdog.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/meshcore-mqtt-watchdog.service`
- **ExecStart:** `{ path=/opt/meshcore-mqtt-watchdog/watchdog.sh ; argv[]=/opt/meshcore-mqtt-watchdog/watchdog.sh ; ignore_errors=no ; start_time=[Sun 2026-07-26 19:14:42 EDT] ; stop_time=[Sun 2026-07-26 19:14:42 EDT] ; pid=702258 ; code=exited ; status=0 }`

### `meshcore-mqtt-watchdog.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/meshcore-mqtt-watchdog.timer`

### `peer-check.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/peer-check.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/peer-check/peer-check.py ; ignore_errors=no ; start_time=[Sun 2026-07-26 19:16:42 EDT] ; stop_time=[Sun 2026-07-26 19:16:43 EDT] ; pid=703111 ; code=exited ; status=0 }`

### `peer-check.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/peer-check.timer`

### `userconfig.service`  _(masked
?/inactive
?)_

- **Unit file:** `/etc/systemd/system/userconfig.service`


## Notes

- **Config location tip:** for services, the config is usually a path in the ExecStart args (e.g. Graywolf's `-config /var/lib/graywolf/graywolf.db`) or an EnvironmentFile above. For containers, it's the host bind mounts.
- Secrets (PASSWORD/TOKEN/SECRET/KEY) are intentionally omitted from env output — safe to commit.
- Re-run and re-commit after any install/move so this never drifts from reality.
