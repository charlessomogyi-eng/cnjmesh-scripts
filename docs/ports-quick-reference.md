# Ports quick reference (host port -> what it is)

Compiled Oct 26 2026 from `install-map-cnjmesh1.md`, `install-map-cnjmesh2.md`, `cnjmesh1-operations.md` and `CLAUDE_CONTEXT.md`. Those install maps are snapshots, so **the live truth is `docker ps` and `docker port <container>` on the host** (both finish on their own). Check there before any command that names a port. Written because Claude once suggested `localhost:5008` on cnjmesh2, where Malla is published on **8080**.

## cnjmesh1 (10.0.0.181)

| Host port | Service | Notes |
|---|---|---|
| 1883 | `mosquitto` (the CNJ broker) | MQTT; password file, no anonymous |
| 9001 | `mosquitto` WebSocket listener | same container |
| 5008 | Malla (`mqtt-malla-web-1`) | public as malla.cnjmesh.me via Cloudflare tunnel |
| 8080 | Meshview (systemd `meshview-web`) | not Docker; protected service |
| 3001 -> 80 | CoreScope (`corescope`) | corescope.cnjmesh.me |
| 1884 -> 1883 | CoreScope's **own embedded MQTT broker** | NOT the Mosquitto above; do not confuse |
| 8000 | `meshcore-hub-api` | |
| 8083 -> 8080 | `meshcore-hub-web` | meshcorehub.cnjmesh.me |
| 8084 | `mesh-discord-shim` | |
| 5432 | Postgres (`mesh-mqtt-pg-collector-postgres-1`) | |
| 8085 -> 8000 | `nextjs_app` (APRS TNC web) | |

## cnjmesh2 (10.0.0.91)

| Host port | Service | Notes |
|---|---|---|
| **8080 -> 5008** | Malla (`malla-web`, container port is 5008) | public as malla2.cnjmesh.me; **use 8080 on this host** |
| 1883 | `mosquitto` (cnjmesh2's own broker, separate from cnjmesh1) | anonymous allowed; bridges `meshtastic_centnj` to mqtt.meshtastic.org |

## cnjmesh3 (10.0.0.186)

Nothing recorded in `install-map-cnjmesh3.md`; check `docker ps` and the cnjmesh3 README before assuming.

## Traps

- **8080 means two different things:** Meshview on cnjmesh1, Malla on cnjmesh2.
- **1883 vs 1884 on cnjmesh1:** Mosquitto vs CoreScope's embedded broker.
- A refused connection on a documented port can mean the mapping changed, not that the service is down (see `docs/lessons-learned-get-well-plan.md`).
