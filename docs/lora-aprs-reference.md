# LoRa APRS Reference — CNJ Mesh

**Last updated:** 2026-08-17

## K2GIA-10 — Existing Fixed Station
- Hardware: LilyGo LoRa APRS board
- Web UI: `http://10.0.0.74`
- Firmware: CA2RXU
- iGate: 433.775 MHz, SF12, BW125
- Confirmed receiving traffic (e.g. AC2F-10 beacons)
- Known limitation: **KISS TNC confirmed TX-injection only** — station has a documented self-gating limitation (cannot reliably hear/gate its own outgoing transmissions). A second RX-only board has been ordered to address this.
- Do NOT use `screen` against this device's serial port for monitoring — the web UI's "Received Packets" page is the correct/supported monitoring method.
- Confirmed solid RF reach: e.g. WB2EHG-7 packet relayed through KD2CIF-1 and KB2EAR-13 observed cleanly.

## K2GIA-9 — Planned Mobile Tracker (on order)
- Not yet built/deployed as of 2026-08-17
- SSID `-9` reserved per K2GIA SSID convention map (mobile/tracker use)
- Will need its own distinct callsign+SSID identity separate from K2GIA-10 (fixed station) once online

## K2GIA SSID Map (full, cross-reference)
- `K2GIA` — Charles personally (portable/voice/OTA)
- `K2GIA-1` — Graywolf/UV-5R M fixed 2m digi+iGate (see separate 2m APRS reference doc)
- `K2GIA-5` — APRSdroid (phone-based)
- `K2GIA-7` — planned TidRadio TD-H9 handheld (mobile 2m APRS)
- `K2GIA-9` — planned LoRa APRS tracker (this doc, on order)
- `K2GIA-10` — existing LoRa APRS fixed station (this doc)

## Related / Not Yet Built
**APRStastic** (afourney/aprstastic on GitHub) — bidirectional Meshtastic↔APRS gateway, TODO/experiment item, not yet built. Would run on a dedicated spare Pi + dedicated Meshtastic node (NOT CJG1/CJG2). Two open decisions before building:
1. OK with CNJ mesh node positions appearing on the public aprs.fi map?
2. Which spare node + which Pi (keep off cnjmesh1's crowded USB bus)?

Full detail in `todos.md` / Claude's memory — this is Meshtastic-adjacent, not part of the LoRa APRS (K2GIA-9/-10) build itself; kept as a separate consideration.

**APRS-Agent** (map.aprsagent.com) — self-hostable APRS-IS bridge/automation platform with AI Gateway, repeater/silence monitoring, propagation detection. Reference only, not yet involved with — plan is to revisit once both 2m APRS (Graywolf) and LoRa APRS builds are fully stable. Would run on a separate VPS/spare Pi, not cnjmesh1. Charles has ruled out German hosting providers (Contabo, Hetzner) specifically due to ID-verification friction — would need a non-German alternative (DigitalOcean, Linode, Vultr) if pursued.
