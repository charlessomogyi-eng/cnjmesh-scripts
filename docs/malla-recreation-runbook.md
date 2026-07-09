# CNJ Mesh — Malla Recreation Runbook
**Purpose:** If Charles is unavailable (health emergency, incapacitation, etc.), this document gives a technically capable person (e.g. SGA) everything needed to recreate malla.cnjmesh.me from scratch, on the existing Pi or new hardware.

Last updated: <!-- UPDATE THIS DATE EACH TIME YOU EDIT -->

---

## 1. What Malla Is and Why It Exists

Malla is a web dashboard that visualizes Meshtastic mesh network traffic — nodes, packets, gateways, traceroutes. CNJ Mesh runs a private instance on cnjmesh1, fed by an MQTT broker (Mosquitto) that receives packets from local gateway nodes and (optionally) bridged public networks.

**Public URL:** malla.cnjmesh.me (or corescope.cnjmesh.me — confirm which is live)
**Runs on:** cnjmesh1 (Raspberry Pi 4B Rev 1.5, static IP 10.0.0.181, SSH user: somog)

---

## 2. Where Access Lives (DO NOT put actual secrets in this file or in GitHub)

| What | Where to find it |
|---|---|
| SSH access to cnjmesh1 | e.g. "SSH key on Gia's laptop" or "password in password manager" |
| Router / network admin access | (fill in) |
| Domain registrar (cnjmesh.me) login | (fill in) |
| Cloudflare account (tunnel + DNS) | (fill in) |
| MQTT broker credentials | See credentials-reference.md (kept OUTSIDE GitHub — see Section 6) |
| GitHub account for cnjmesh-scripts | (fill in) |

**Recommendation:** Put actual credentials in a password manager (Bitwarden, 1Password) and share a single emergency-access note with Gia and/or SGA, referencing this runbook. GitHub holds the structure, not the secrets.

---

## 3. Physical / Network Prerequisites

- cnjmesh1 is a Raspberry Pi 4B physically located at Charles's house (Kendall Park / South Brunswick, NJ)
- Runs Raspberry Pi OS, Docker + Docker Compose
- Connected to home network at static IP 10.0.0.181
- Exposed to the internet via a Cloudflare Tunnel (tunnel ID: a05e5efa-8c67-48f8-a71c-833f5258dfce), config at /etc/cloudflared/config.yml
- If the physical Pi is lost/destroyed, a new Pi (or any Docker-capable Linux host) can be provisioned — see Section 5

---

## 4. Software Stack Overview

```
Meshtastic gateway nodes (CJG1, CJG2, KPR1, KPR2, etc.)
        |  (uplink via WiFi/LoRa)
        v
Mosquitto MQTT broker (local, port 1883)
        |
        v
mqtt-filter container  --filters/re-publishes-->  filtered/msh/US/#
        |
        v
Malla (malla-capture container, subscribes to filtered/msh/US/#)
        |
        v
Malla web UI (port 5008) --> Cloudflare Tunnel --> malla.cnjmesh.me
```

**Key config files (locations on cnjmesh1):**
- /opt/stacks/mqtt/compose.yaml — base Docker Compose stack
- /opt/stacks/mqtt/compose.override.yaml — local overrides (filter env vars, Malla topic prefix/suffix)
- /opt/stacks/mqtt/config/mosquitto.conf — broker config, auth
- /etc/cloudflared/config.yml — tunnel routing to expose Malla publicly

---

## 5. Step-by-Step Recreation (from bare metal / new Pi)

1. Install base OS — Raspberry Pi OS (64-bit) on new hardware, or use existing cnjmesh1 if intact
2. Install Docker + Docker Compose:
   curl -sSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   sudo apt install docker-compose-plugin
3. Clone the cnjmesh-scripts repo:
   git clone https://github.com/charlessomogyi-eng/cnjmesh-scripts.git
   cd cnjmesh-scripts
4. Restore the stack directory — copy /opt/stacks/mqtt/ structure from this repo's configs/mqtt/ folder (see Section 6) to /opt/stacks/mqtt/ on the new host
5. Fill in real credentials — retrieve MQTT broker username/password and any API tokens from the password manager (NOT from GitHub) and place them in compose.override.yaml and mosquitto.conf
6. Bring up the stack:
   cd /opt/stacks/mqtt
   sudo docker compose up -d
7. Verify Mosquitto is receiving packets:
   mosquitto_sub -h localhost -u meshdev -P <password> -t 'msh/#' -v
8. Verify Malla is capturing filtered packets — check Malla web UI at http://<host-ip>:5008
9. Restore Cloudflare Tunnel — either reuse the existing tunnel ID (requires Cloudflare account access) or create a new tunnel and update DNS for malla.cnjmesh.me
10. Confirm public access — visit https://malla.cnjmesh.me and confirm live data is populating

---

## 6. What Goes in GitHub vs. What Doesn't

**Safe to commit to cnjmesh-scripts (public or private repo):**
- This runbook
- compose.yaml (base, no secrets)
- mosquitto.conf with credentials replaced by placeholders (e.g. password_file /etc/mosquitto/passwd)
- cloudflared/config.yml (tunnel ID is not a secret by itself, but treat cautiously)
- Any setup/health-check scripts

**NEVER commit:**
- Actual MQTT usernames/passwords
- Cloudflare API tokens
- SSH private keys
- Any .env files with real values

**Recommended repo structure:**
```
cnjmesh-scripts/
  docs/
    malla-recreation-runbook.md   (this file)
  configs/
    mqtt/
      compose.yaml
      compose.override.yaml.template   (placeholders, not real creds)
      mosquitto.conf.template
  scripts/
    (existing scripts)
```

---

## 7. Who to Contact if SGA Needs Help

- Community members familiar with this setup: AkkerKid (MeshOmatic admin), Tilly (MeshOmatic/AOI), KB2EAR
- Charles's ham callsign: K2GIA (for identifying the operator in any regulatory context)

---

## 8. Open Gaps To Fill In

- [ ] Confirm whether malla.cnjmesh.me or corescope.cnjmesh.me is the canonical public URL
- [ ] Document exact Cloudflare Tunnel recreation steps if tunnel ID can't be reused
- [ ] Decide where the master password manager vault lives and who has emergency access
- [ ] Add cnjmesh2 and cnjmesh3 equivalents if they also need disaster-recovery docs
- [ ] Confirm with SGA whether he's willing to be the designated recovery contact
