# Install Map — `cnjmesh3`

_Generated 2026-07-26 17:01:27 EDT by `scripts/collect-inventory.sh`. Re-run to refresh — do not hand-edit._

## Docker containers

### `meshcore-mqtt-bridge`  _(state: running, restart: unless-stopped)_

- **Image:** `meshcore-mqtt:local`
- **Devices:** `/dev/ttyACM1 `
- **Config env (secrets omitted):**
    - `MQTT_BROKER=10.0.0.181`
    - `MQTT_TOPIC_PREFIX=meshcore`
    - `MESHCORE_EVENTS=CONTACT_MSG_RECV,CHANNEL_MSG_RECV,CONNECTED,DISCONNECTED,LOGIN_SUCCESS,LOGIN_FAILED,MESSAGES_WAITING,DEVICE_INFO,BATTERY,NEW_CONTACT,ADVERTISEMENT`
    - `MQTT_PORT=1883`
    - `PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `PYTHONPATH=/app`

### `meshcore-packet-capture`  _(state: running, restart: unless-stopped)_

- **Image:** `ghcr.io/agessaman/meshcore-packet-capture:latest`
- **Host bind mounts (config/data on disk):**
    - `/opt/meshcore-packet-capture/config.d -> /etc/meshcore-packet-capture/config.d`
- **Devices:** `/dev/ttyACM0 `
- **Config env (secrets omitted):**
    - `PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `PACKETCAPTURE_DATA_DIR=/app/data`


## systemd services & timers (user-installed)

_Only units whose file lives under `/etc/systemd/system` (i.e. you/we installed them) — OS/vendor units under /lib and /usr/lib are excluded._

### `disk-temp-watchdog.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/disk-temp-watchdog.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/disk-temp-watchdog/watchdog.py ; ignore_errors=no ; start_time=[Sun 2026-07-26 16:59:11 EDT] ; stop_time=[Sun 2026-07-26 16:59:12 EDT] ; pid=688595 ; code=exited ; status=0 }`

### `disk-temp-watchdog.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/disk-temp-watchdog.timer`

### `meshcore-mqtt-watchdog.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/meshcore-mqtt-watchdog.service`
- **ExecStart:** `{ path=/opt/meshcore-mqtt-watchdog/watchdog.sh ; argv[]=/opt/meshcore-mqtt-watchdog/watchdog.sh ; ignore_errors=no ; start_time=[Sun 2026-07-26 17:00:21 EDT] ; stop_time=[Sun 2026-07-26 17:00:21 EDT] ; pid=688698 ; code=exited ; status=0 }`

### `meshcore-mqtt-watchdog.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/meshcore-mqtt-watchdog.timer`

### `peer-check.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/peer-check.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/peer-check/peer-check.py ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`

### `peer-check.timer`  _(enabled/inactive
?)_

- **Unit file:** `/etc/systemd/system/peer-check.timer`

### `userconfig.service`  _(masked
?/inactive
?)_

- **Unit file:** `/etc/systemd/system/userconfig.service`


## Notes

- **Config location tip:** for services, the config is usually a path in the ExecStart args (e.g. Graywolf's `-config /var/lib/graywolf/graywolf.db`) or an EnvironmentFile above. For containers, it's the host bind mounts.
- Secrets (PASSWORD/TOKEN/SECRET/KEY) are intentionally omitted from env output — safe to commit.
- Re-run and re-commit after any install/move so this never drifts from reality.
