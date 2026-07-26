# CNJ Mesh — Install Map (Index)

**What this is:** a generated, always-current answer to *"where does X live and how is it launched"* across all three Pis — so nobody (human or AI) has to trial-and-error hunt for a config path, container, or service again.

**For AI assistants / session start:** if you need to find where a service, container, config file, or port lives, read the relevant per-host map below **before** grepping around the filesystem. These are generated from the live system, so they reflect reality (as of each file's timestamp).

## Per-host maps

| Host | File | Role |
|------|------|------|
| cnjmesh1 | [`install-map-cnjmesh1.md`](install-map-cnjmesh1.md) | Central broker + web apps + 2m/LoRa APRS |
| cnjmesh2 | [`install-map-cnjmesh2.md`](install-map-cnjmesh2.md) | Secondary Mosquitto / OkToMqtt (Meshtastic) |
| cnjmesh3 | [`install-map-cnjmesh3.md`](install-map-cnjmesh3.md) | MeshCore RF hardware hub (Observer + KPR2) |

Each map lists, per host: every Docker container (image, ports, **host bind mounts = where config/data lives on disk**, devices, config env with secrets stripped) and every user-installed systemd service/timer (ExecStart, WorkingDirectory, EnvironmentFile).

## Regenerating (do this after ANY install / move / config change)

The maps are **generated, not hand-edited** — don't edit them by hand, re-run the collector. On the Pi that changed:

```bash
cd ~/cnjmesh-scripts && git pull -q
sudo ./scripts/collect-inventory.sh > install-map-$(hostname).md
git add install-map-$(hostname).md && git commit -m "Refresh install map: $(hostname)" && git push
```

The collector (`scripts/collect-inventory.sh`) is read-only — it inspects, never modifies — and omits secrets (PASSWORD/TOKEN/SECRET/KEY env vars) so the output is safe to commit to this public repo.

**Rule of thumb:** if you install, move, or reconfigure anything on a Pi, re-run the collector on that Pi before ending the session — same discipline as updating `todos.md`/`session-log.md`. Stale maps are worse than none because they mislead.
