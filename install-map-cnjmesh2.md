# Install Map — `cnjmesh2`

_Generated 2026-07-31 16:10:57 EDT by `scripts/collect-inventory.sh`. Re-run to refresh — do not hand-edit._

## Docker containers

### `malla-capture`  _(state: running, restart: unless-stopped)_

- **Image:** `ghcr.io/zenitram/malla:latest`
- **Compose project:** `meshtastic-mqtt`
- **Compose working dir:** `/home/somogyic/meshtastic-mqtt`  ← compose file lives here
- **Host bind mounts (config/data on disk):**
    - `/home/somogyic/meshtastic-mqtt/malla -> /app/data`
- **Config env (secrets omitted):**
    - `MALLA_MQTT_TOPIC_SUFFIX=/US/#`
    - `MALLA_MQTT_BROKER_ADDRESS=mosquitto`
    - `MALLA_MQTT_PORT=1883`
    - `MALLA_MQTT_TOPIC_PREFIX=msh`
    - `PATH=/app/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `UV_TOOL_BIN_DIR=/usr/local/bin`
    - `MALLA_HOST=0.0.0.0`
    - `MALLA_PORT=5008`

### `malla-web`  _(state: running, restart: unless-stopped)_

- **Image:** `ghcr.io/zenitram/malla:latest`
- **Compose project:** `meshtastic-mqtt`
- **Compose working dir:** `/home/somogyic/meshtastic-mqtt`  ← compose file lives here
- **Ports:** `8080->5008/tcp `
- **Host bind mounts (config/data on disk):**
    - `/home/somogyic/meshtastic-mqtt/malla -> /app/data`
- **Config env (secrets omitted):**
    - `MALLA_HOST=0.0.0.0`
    - `MALLA_PORT=5008`
    - `PATH=/app/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `UV_TOOL_BIN_DIR=/usr/local/bin`

### `mosquitto`  _(state: running, restart: unless-stopped)_

- **Image:** `eclipse-mosquitto:latest`
- **Compose project:** `meshtastic-mqtt`
- **Compose working dir:** `/home/somogyic/meshtastic-mqtt`  ← compose file lives here
- **Ports:** `1883->1883/tcp `
- **Host bind mounts (config/data on disk):**
    - `/home/somogyic/meshtastic-mqtt/mosquitto/config -> /mosquitto/config`
    - `/home/somogyic/meshtastic-mqtt/mosquitto/data -> /mosquitto/data`
    - `/home/somogyic/meshtastic-mqtt/mosquitto/log -> /mosquitto/log`
- **Config env (secrets omitted):**
    - `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`

### `oktomqtt`  _(state: exited, restart: unless-stopped)_

- **Image:** `meshtastic-mqtt-oktomqtt`
- **Compose project:** `meshtastic-mqtt`
- **Compose working dir:** `/home/somogyic/meshtastic-mqtt`  ← compose file lives here
- **Config env (secrets omitted):**
    - `MQTT_BROKER=mosquitto`
    - `MQTT_PORT=1883`
    - `OUTPUT_TOPIC=filtered/msh/US`
    - `INPUT_TOPIC=msh/US/#`
    - `PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`

### `zealous_joliot`  _(state: exited, restart: no)_

- **Image:** `hello-world`
- **Config env (secrets omitted):**
    - `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`


## systemd services & timers (user-installed)

_Only units whose file lives under `/etc/systemd/system` (i.e. you/we installed them) — OS/vendor units under /lib and /usr/lib are excluded._

### `cloudflared.service`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/cloudflared.service`
- **ExecStart:** `{ path=/usr/bin/cloudflared ; argv[]=/usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`

### `cloudflared-update.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/cloudflared-update.service`
- **ExecStart:** `{ path=/bin/bash ; argv[]=/bin/bash -c /usr/bin/cloudflared update; code=$?; if [ $code -eq 11 ]; then systemctl restart cloudflared; exit 0; fi; exit $code ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`

### `cloudflared-update.timer`  _(disabled
?/inactive
?)_

- **Unit file:** `/etc/systemd/system/cloudflared-update.timer`

### `disk-temp-watchdog.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/disk-temp-watchdog.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/disk-temp-watchdog/watchdog.py ; ignore_errors=no ; start_time=[Fri 2026-07-31 16:08:57 EDT] ; stop_time=[Fri 2026-07-31 16:08:57 EDT] ; pid=16811 ; code=exited ; status=0 }`

### `disk-temp-watchdog.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/disk-temp-watchdog.timer`

### `peer-check.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/peer-check.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/peer-check/peer-check.py ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`

### `peer-check.timer`  _(disabled
?/inactive
?)_

- **Unit file:** `/etc/systemd/system/peer-check.timer`


## Notes

- **Config location tip:** for services, the config is usually a path in the ExecStart args (e.g. Graywolf's `-config /var/lib/graywolf/graywolf.db`) or an EnvironmentFile above. For containers, it's the host bind mounts.
- Secrets (PASSWORD/TOKEN/SECRET/KEY) are intentionally omitted from env output — safe to commit.
- Re-run and re-commit after any install/move so this never drifts from reality.
