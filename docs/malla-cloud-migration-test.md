# Malla Cloud Migration — TEST with FALLBACK (started Aug 1, 2026)

## Why
cnjmesh1 has been unreliable (recurring gateway/Xfinity outages take malla.cnjmesh.me down; box is memory-starved; Malla dashboard query is ~41s regardless of DB tuning). Goal: get the **public-facing** Malla off the home connection so home-internet hiccups stop blanking the public site. This is **Option A** — migrate ONLY Malla (non-serial) first, leave everything radio/serial-bound on the Pis.

## Decision (Aug 1, 2026)
- **Provider:** Hetzner Cloud (chosen over Fly.io — Hetzner ~$4.90/mo FLAT vs Fly ~$9-13/mo metered/variable for same 2GB workload; single-metro user base means Fly's edge/Secaucus advantage is worth ~3-5ms, not 2x price).
- **Plan:** CPX11 (2 vCPU AMD / 2GB RAM / 40GB NVMe / 20TB egress) — 2GB RAM is MORE than cnjmesh1 has free today.
- **Location:** Ashburn, VA (US East) — Hetzner's only US region; ~200mi, fine latency for a web dashboard. (NOTE: the cheap CX/CAX plans are EU-only; must use CPX family for US.)
- **Image:** Ubuntu 24.04 LTS.
- **Promo:** new customers get €20/$20 free credit (valid thru Dec 31 2026, first 3 months) — effectively ~4 months free at CPX11 rate. Can test at zero real spend.

## CORE PRINCIPLE: non-destructive, parallel, reversible
**Nothing on cnjmesh1 gets stopped, moved, or deleted.** The Pi's Malla + live DB keep running the entire time. We stand up a SECOND Malla on Hetzner from a COPY of the DB, test it on a separate address, and only repoint the real domain IF Charles likes it. Fallback at every step = "just keep using the Pi; delete the Hetzner box (billing stops immediately, hourly, no contract)."

## The DB copy already exists
`/home/somog/backups/malla-backup-20260731.db` (2.0GB SQLite snapshot, consistency-safe, taken July 31). This is what gets uploaded to Hetzner — NOT the live Pi DB. (Still needs to be moved off-Pi anyway; scp was blocked by the Aug 1 gateway outage — retry once connectivity restored.)

## Domain / DNS strategy (keep cnjmesh.me entirely)
- Domain lives at the DNS provider (Cloudflare), NOT on the Pi. Hosting elsewhere = just pointing a subdomain at a different address. Domain ownership/control never changes.
- **During test:** `malla.cnjmesh.me` stays pointed at the Pi (via existing Cloudflare tunnel), UNTOUCHED. Add a NEW record `malla-test.cnjmesh.me` -> Hetzner IP (or a Cloudflare tunnel on Hetzner) for testing. Real site unaffected.
- **If Charles likes it:** repoint `malla.cnjmesh.me` -> Hetzner. Same URL for users. Instantly reversible (point back at Pi).
- **Open choice for later:** raw DNS A-record to Hetzner IP (simple) vs. run a Cloudflare tunnel on Hetzner too (hides IP, matches current setup). Decide at cutover.

## Step-by-step (execute next session — Sonnet or Claude Code is fine for all of this)
1. **Laptop:** create SSH key `ssh-keygen -t ed25519 -C "hetzner-malla"`; copy the `.pub`.
2. **Hetzner:** sign up at hetzner.com/cloud (expect email + possible ID/payment verification). New Project `mesh-cloud`.
3. **Hetzner:** Add Server -> Ashburn / Ubuntu 24.04 / **CPX11** / paste SSH key / name `malla-cloud` / Create & Buy. NOTE: SSH key MUST be added during creation — cannot add via console after. Record the public IP.
4. **Secure the box:** create a Hetzner Cloud Firewall (allow SSH 22, plus 80/443 or the tunnel as needed); basic hardening (ufw, fail2ban, non-root user optional).
5. **Install Docker + compose** on the box.
6. **Copy Malla's compose config** up (the `mqtt` stack's malla-capture + malla-web service definitions — adapt: on Hetzner it needs its own broker to subscribe to, OR subscribe over the internet to the Pi's/public broker `mqtt.cnjmesh.me`). DECISION NEEDED: does cloud Malla ingest from the public MQTT (`mqtt.cnjmesh.me`, user `meshuser`) so it stays live-updating, or is it a static-history viewer? For a real replacement it should subscribe to live MQTT.
7. **Upload the DB copy** (`malla-backup-20260731.db`) into the Hetzner Malla data volume, renamed to `meshtastic_history.db`.
8. **Bring up cloud Malla**, point `malla-test.cnjmesh.me` at it, TEST. Compare speed/reliability vs Pi. (Reminder: the ~41s query is an app-code issue and MAY still be slow on the cloud box too — 2GB RAM + faster CPU may help but is NOT guaranteed to fix it. Manage expectations: the migration's main win is decoupling from home internet, not necessarily fixing the slow query.)
9. **Decision point:** like it -> repoint `malla.cnjmesh.me` to Hetzner (reversible). Don't like it -> delete the Hetzner server, keep using the Pi, nothing lost.

## Fallback summary
- Test address separate from production the whole time.
- cnjmesh1 Malla never touched.
- Cutover = one DNS change, instantly reversible.
- Abandon = delete Hetzner box, billing stops immediately.

## Open caveats / honest notes
- The slow-query problem may follow Malla to the cloud (it's app code, not hardware/DB). Cloud box's real, guaranteed win is reliability/decoupling from home internet, not speed. Verify speed on the test box before assuming it's fixed.
- If live MQTT ingest is wanted on the cloud box, confirm the public broker `mqtt.cnjmesh.me` is reachable and carries the needed topics; the cloud Malla subscribes to that.
- Consider Cloudflare tunnel on Hetzner (vs raw IP) to keep consistent with current no-exposed-IP posture.
