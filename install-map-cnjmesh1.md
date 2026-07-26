# Install Map — `cnjmesh1`

_Generated 2026-07-26 17:00:48 EDT by `scripts/collect-inventory.sh`. Re-run to refresh — do not hand-edit._

## Docker containers

### `corescope`  _(state: running, restart: unless-stopped)_

- **Image:** `ghcr.io/kpa-clawbot/corescope:latest`
- **Ports:** `3001->80/tcp 1884->1883/tcp `
- **Host bind mounts (config/data on disk):**
    - `/home/somog/meshcore-data -> /app/data`
- **Config env (secrets omitted):**
    - `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`

### `meshcore-hub-api`  _(state: running, restart: unless-stopped)_

- **Image:** `ghcr.io/ipnet-mesh/meshcore-hub:latest`
- **Compose project:** `meshcore-hub`
- **Compose working dir:** `/opt/stacks/meshcore-hub`  ← compose file lives here
- **Ports:** `8000->8000/tcp `
- **Config env (secrets omitted):**
    - `REDIS_HOST=redis`
    - `MQTT_PORT=1883`
    - `DATABASE_PORT=5432`
    - `API_HOST=0.0.0.0`
    - `DATABASE_HOST=postgres`
    - `MQTT_HOST=10.0.0.181`
    - `REDIS_PORT=6379`
    - `MQTT_WS_PATH=/`
    - `API_PORT=8000`
    - `MQTT_TRANSPORT=tcp`
    - `PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `WEB_HOST=0.0.0.0`
    - `WEB_PORT=8080`
    - `API_BASE_URL=http://api:8000`

### `meshcore-hub-web`  _(state: running, restart: unless-stopped)_

- **Image:** `ghcr.io/ipnet-mesh/meshcore-hub:latest`
- **Compose project:** `meshcore-hub`
- **Compose working dir:** `/opt/stacks/meshcore-hub`  ← compose file lives here
- **Ports:** `8083->8080/tcp `
- **Host bind mounts (config/data on disk):**
    - `/opt/stacks/meshcore-hub/content -> /content`
- **Config env (secrets omitted):**
    - `WEB_HOST=0.0.0.0`
    - `OIDC_DISCOVERY_URL=`
    - `OIDC_REDIRECT_URI=`
    - `FEATURE_RADIO_CONFIG=true`
    - `OIDC_POST_LOGOUT_REDIRECT_URI=`
    - `API_BASE_URL=http://api:8000`
    - `WEB_PORT=8080`
    - `PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `MQTT_HOST=mqtt`
    - `MQTT_PORT=1883`
    - `API_HOST=0.0.0.0`
    - `API_PORT=8000`

### `mesh-discord-shim`  _(state: running, restart: unless-stopped)_

- **Image:** `mesh-discord-shim-mesh-discord-shim`
- **Compose project:** `mesh-discord-shim`
- **Compose working dir:** `/opt/stacks/mesh-discord-shim`  ← compose file lives here
- **Ports:** `8084->8084/tcp `
- **Host bind mounts (config/data on disk):**
    - `/opt/stacks/mesh-discord-shim/data -> /data`
- **Config env (secrets omitted):**
    - `DB_PATH=/data/seen_nodes.db`
    - `PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`

### `mesh-mqtt-pg-collector-collector-1`  _(state: running, restart: unless-stopped)_

- **Image:** `mesh-mqtt-pg-collector-collector`
- **Compose project:** `mesh-mqtt-pg-collector`
- **Compose working dir:** `/home/somog/mesh-mqtt-pg-collector`  ← compose file lives here
- **Host bind mounts (config/data on disk):**
    - `/home/somog/mesh-mqtt-pg-collector/config.yaml -> /app/config.yaml`
- **Config env (secrets omitted):**
    - `COLLECTOR_POSTGRES_HOST=postgres`
    - `COLLECTOR_POSTGRES_PORT=5432`
    - `PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `COLLECTOR_CONFIG_FILE=/app/config.yaml`

### `mesh-mqtt-pg-collector-postgres-1`  _(state: running, restart: unless-stopped)_

- **Image:** `postgres:17-alpine`
- **Compose project:** `mesh-mqtt-pg-collector`
- **Compose working dir:** `/home/somog/mesh-mqtt-pg-collector`  ← compose file lives here
- **Ports:** `5432->5432/tcp `
- **Config env (secrets omitted):**
    - `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`

### `mosquitto`  _(state: running, restart: unless-stopped)_

- **Image:** `eclipse-mosquitto`
- **Compose project:** `mqtt`
- **Compose working dir:** `/opt/stacks/mqtt`  ← compose file lives here
- **Ports:** `1883->1883/tcp 9001->9001/tcp `
- **Host bind mounts (config/data on disk):**
    - `/opt/stacks/mqtt/config -> /mosquitto/config`
    - `/opt/stacks/mqtt/data -> /mosquitto/data`
    - `/opt/stacks/mqtt/log -> /mosquitto/log`
- **Config env (secrets omitted):**
    - `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`

### `mqtt-filter`  _(state: running, restart: unless-stopped)_

- **Image:** `meshtastic-oktomqtt-filter:latest`
- **Compose project:** `mqtt`
- **Compose working dir:** `/opt/stacks/mqtt`  ← compose file lives here
- **Config env (secrets omitted):**
    - `MQTT_PORT=1883`
    - `INPUT_TOPIC=msh/US/#`
    - `OUTPUT_TOPIC=filtered/msh/US`
    - `MQTT_BROKER=mosquitto`
    - `PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`

### `mqtt-malla-capture-1`  _(state: running, restart: unless-stopped)_

- **Image:** `ghcr.io/zenitram/malla:latest`
- **Compose project:** `mqtt`
- **Compose working dir:** `/opt/stacks/mqtt`  ← compose file lives here
- **Config env (secrets omitted):**
    - `MALLA_MQTT_TOPIC_PREFIX=msh`
    - `MALLA_MQTT_TOPIC_SUFFIX=/US/#`
    - `MALLA_MQTT_BROKER_ADDRESS=mosquitto`
    - `MALLA_MQTT_PORT=1883`
    - `PATH=/app/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `UV_TOOL_BIN_DIR=/usr/local/bin`
    - `MALLA_HOST=0.0.0.0`
    - `MALLA_PORT=5008`

### `mqtt-malla-web-1`  _(state: running, restart: unless-stopped)_

- **Image:** `ghcr.io/zenitram/malla:latest`
- **Compose project:** `mqtt`
- **Compose working dir:** `/opt/stacks/mqtt`  ← compose file lives here
- **Ports:** `5008->5008/tcp `
- **Config env (secrets omitted):**
    - `MALLA_HOST=0.0.0.0`
    - `MALLA_PORT=5008`
    - `PATH=/app/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
    - `UV_TOOL_BIN_DIR=/usr/local/bin`

### `mysql_database`  _(state: running, restart: unless-stopped)_

- **Image:** `mysql:8.0`
- **Compose project:** `aprs-tnc-web`
- **Compose working dir:** `/opt/aprs-tnc-web`  ← compose file lives here
- **Config env (secrets omitted):**
    - `DB_PORT=3306`
    - `DB_HOST=mysql_db`
    - `PORT=8085`
    - `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`

### `nextjs_app`  _(state: running, restart: unless-stopped)_

- **Image:** `aprs-tnc-web-local:latest`
- **Compose project:** `aprs-tnc-web`
- **Compose working dir:** `/opt/aprs-tnc-web`  ← compose file lives here
- **Ports:** `8085->8000/tcp `
- **Host bind mounts (config/data on disk):**
    - `/opt/aprs-tnc-web/data -> /app/data`
- **Config env (secrets omitted):**
    - `PORT=8000`
    - `DB_PORT=3306`
    - `DB_HOST=mysql_db`
    - `MYSQL_HOST=mysql_db`
    - `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`


## systemd services & timers (user-installed)

_Only units whose file lives under `/etc/systemd/system` (i.e. you/we installed them) — OS/vendor units under /lib and /usr/lib are excluded._

### `aprs-monitor.service`  _(disabled
?/inactive
?)_

- **Unit file:** `/etc/systemd/system/aprs-monitor.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/graywolf-discord/aprs_monitor.py ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`
- **WorkingDirectory:** `/opt/graywolf-discord`

### `cloudflared.service`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/cloudflared.service`
- **ExecStart:** `{ path=/usr/local/bin/cloudflared ; argv[]=/usr/local/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`

### `cloudflared-update.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/cloudflared-update.service`
- **ExecStart:** `{ path=/bin/bash ; argv[]=/bin/bash -c /usr/local/bin/cloudflared update; code=$?; if [ $code -eq 11 ]; then systemctl restart cloudflared; exit 0; fi; exit $code ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`

### `cloudflared-update.timer`  _(disabled
?/inactive
?)_

- **Unit file:** `/etc/systemd/system/cloudflared-update.timer`

### `corescope-watchdog.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/corescope-watchdog.service`
- **ExecStart:** `{ path=/opt/corescope-watchdog/watchdog.sh ; argv[]=/opt/corescope-watchdog/watchdog.sh ; ignore_errors=no ; start_time=[Sun 2026-07-26 16:57:22 EDT] ; stop_time=[Sun 2026-07-26 16:57:23 EDT] ; pid=1862634 ; code=exited ; status=0 }`

### `corescope-watchdog.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/corescope-watchdog.timer`

### `graywolf-discord.service`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/graywolf-discord.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/graywolf-discord/graywolf-discord-bridge.py ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`
- **WorkingDirectory:** `/opt/graywolf-discord`

### `graywolf-discord-watchdog.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/graywolf-discord-watchdog.service`
- **ExecStart:** `{ path=/opt/graywolf-discord/watchdog.sh ; argv[]=/opt/graywolf-discord/watchdog.sh ; ignore_errors=no ; start_time=[Sun 2026-07-26 16:57:22 EDT] ; stop_time=[Sun 2026-07-26 16:57:22 EDT] ; pid=1862637 ; code=exited ; status=0 }`

### `graywolf-discord-watchdog.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/graywolf-discord-watchdog.timer`

### `graywolf-watchdog.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/graywolf-watchdog.service`
- **ExecStart:** `{ path=/opt/graywolf-discord/graywolf-watchdog.sh ; argv[]=/opt/graywolf-discord/graywolf-watchdog.sh ; ignore_errors=no ; start_time=[Sun 2026-07-26 16:57:22 EDT] ; stop_time=[Sun 2026-07-26 16:57:22 EDT] ; pid=1862638 ; code=exited ; status=0 }`

### `graywolf-watchdog.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/graywolf-watchdog.timer`

### `mesh_bot_reporting.service`  _(disabled
?/failed
?)_

- **Unit file:** `/etc/systemd/system/mesh_bot_reporting.service`
- **ExecStart:** `{ path=python3 ; argv[]=python3 etc/report_generator5.py ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`
- **WorkingDirectory:** `/opt/meshing-around`

### `mesh_bot_reporting.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/mesh_bot_reporting.timer`

### `mesh_bot.service`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/mesh_bot.service`
- **ExecStart:** `{ path=/usr/bin/bash ; argv[]=/usr/bin/bash launch.sh mesh ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`
- **WorkingDirectory:** `/opt/meshing-around`

### `meshview-db.service`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/meshview-db.service`
- **ExecStart:** `{ path=/home/somog/meshview/env/bin/python ; argv[]=/home/somog/meshview/env/bin/python startdb.py --config /home/somog/meshview/config.ini ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`
- **WorkingDirectory:** `/home/somog/meshview`

### `meshview-web.service`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/meshview-web.service`
- **ExecStart:** `{ path=/home/somog/meshview/env/bin/python ; argv[]=/home/somog/meshview/env/bin/python main.py --config /home/somog/meshview/config.ini ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`
- **WorkingDirectory:** `/home/somog/meshview`

### `nj-regional-weather-conditions.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/nj-regional-weather-conditions.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/weather-bot/nj_regional_weather.py conditions ; ignore_errors=no ; start_time=[Sun 2026-07-26 13:00:02 EDT] ; stop_time=[Sun 2026-07-26 13:00:12 EDT] ; pid=1507240 ; code=exited ; status=0 }`

### `nj-regional-weather-conditions.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/nj-regional-weather-conditions.timer`

### `nj-regional-weather-forecast.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/nj-regional-weather-forecast.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/weather-bot/nj_regional_weather.py forecast ; ignore_errors=no ; start_time=[Sun 2026-07-26 07:05:00 EDT] ; stop_time=[Sun 2026-07-26 07:05:02 EDT] ; pid=975871 ; code=exited ; status=0 }`

### `nj-regional-weather-forecast.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/nj-regional-weather-forecast.timer`

### `snap.fing-agent.fingagent.service`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/snap.fing-agent.fingagent.service`
- **ExecStart:** `{ path=/usr/bin/snap ; argv[]=/usr/bin/snap run fing-agent.fingagent ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }`
- **WorkingDirectory:** `/var/snap/fing-agent/21`

### `userconfig.service`  _(masked
?/inactive
?)_

- **Unit file:** `/etc/systemd/system/userconfig.service`

### `weather-bot-alerts.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/weather-bot-alerts.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/weather-bot/weather_bot.py alerts ; ignore_errors=no ; start_time=[Sun 2026-07-26 16:49:17 EDT] ; stop_time=[Sun 2026-07-26 16:49:17 EDT] ; pid=1850564 ; code=exited ; status=0 }`

### `weather-bot-alerts.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/weather-bot-alerts.timer`

### `weather-bot-conditions.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/weather-bot-conditions.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/weather-bot/weather_bot.py conditions ; ignore_errors=no ; start_time=[Sun 2026-07-26 13:00:02 EDT] ; stop_time=[Sun 2026-07-26 13:00:05 EDT] ; pid=1507241 ; code=exited ; status=0 }`

### `weather-bot-conditions.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/weather-bot-conditions.timer`

### `weather-bot-forecast.service`  _(static/inactive
?)_

- **Unit file:** `/etc/systemd/system/weather-bot-forecast.service`
- **ExecStart:** `{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/weather-bot/weather_bot.py forecast ; ignore_errors=no ; start_time=[Sun 2026-07-26 07:05:00 EDT] ; stop_time=[Sun 2026-07-26 07:05:02 EDT] ; pid=975872 ; code=exited ; status=0 }`

### `weather-bot-forecast.timer`  _(enabled/active)_

- **Unit file:** `/etc/systemd/system/weather-bot-forecast.timer`


## Notes

- **Config location tip:** for services, the config is usually a path in the ExecStart args (e.g. Graywolf's `-config /var/lib/graywolf/graywolf.db`) or an EnvironmentFile above. For containers, it's the host bind mounts.
- Secrets (PASSWORD/TOKEN/SECRET/KEY) are intentionally omitted from env output — safe to commit.
- Re-run and re-commit after any install/move so this never drifts from reality.
