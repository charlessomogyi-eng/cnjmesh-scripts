# STALE / HISTORICAL: DO NOT DEPLOY (marked Oct 25 2026)
# This stanza (`topic msh/US/2/# out 0`, a second connection to mqtt.sjmesh.net) is the one that
# caused the Aug 5 republish loop. It is NOT in the live config and must not be restored.
# Live config: cnjmesh1/configs/mosquitto-cnjmesh1.conf. Rules: docs/mqtt-topology-and-landmines.md
# SJMesh MQTT Bridge Config — Backup
# Added to /opt/stacks/mqtt/config/mosquitto.conf on cnjmesh1, 2026-07-19

connection sjmesh-bridge
address mqtt.sjmesh.net:1883
remote_username meshuser
remote_password mesh4life
topic msh/US/2/# out 0
