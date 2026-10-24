# New-chat handoff — written 2026-10-23 21:30 ET

Purpose: let a fresh Claude chat continue CNJ Mesh work with the same working style and no lost context.
Read order for the new chat: `CLAUDE_CONTEXT.md`, then this file, then `todos.md`, `known-issues.md`, `docs/backup-guide.md`, tail of `session-log.md`.

## Who / how to work
- Charlie (K2GIA, Systems Engineer, runs CNJ Mesh in Central NJ). Call him Charlie, use his name rarely. Partnership tone: direct, natural, never sheepish or hedgy.
- Claude acts as Claude Code: clone the public repo `charlessomogyi-eng/cnjmesh-scripts`, edit, commit, push yourself as work finishes. Charlie never runs git. Commit trailers: `Co-Authored-By: Claude <noreply@anthropic.com>` plus the session URL line the harness gives.
- Charlie runs every command himself on the Pis and pastes output. Do not remind him you lack SSH access. Do not wait for permission to give or suggest commands (including restarts). Proactively say what is next and end replies with a short Pending list.
- Every command block: name the host (cnjmesh1/2/3 or laptop) and say whether it finishes on its own or needs Ctrl+C. Check the prompt in pasted output to confirm he ran it on the right host.
- No checkbox or multiple-choice prompts. Plain chat.
- Public repo: never commit passwords, tokens, webhook URLs, private keys, the CARTO key or the home address. Backup archives hold secrets and are never committed.
- Do not remind him about pasting GitHub tokens.
- Never change infrastructure or auth on a host he did not explicitly name.
- Be honest about evidence: mark what was verified from pasted output vs guessed. Tonight's corrections: "Wi-Fi is the root cause" of cnjmesh2 was overconfident; journald was volatile and a wrong retraction in between; "MOUN" is a bug, not cosmetic.
- End-of-session routine (in CLAUDE_CONTEXT.md): update `todos.md`, `cnjmesh1-operations.md` if infrastructure changed, re-run `scripts/collect-inventory.sh` on changed Pis and commit `install-map-<host>.md`, append dated `session-log.md` entry, push.
- Patch pattern: exact-match-or-abort Python script with `--dry-run`, timestamped backup, compile check, separate restart step.
- Target MeshCore settings for all CNJ nodes: 910.525 MHz / 500 kHz / SF10 / CR5.

## Hosts
- cnjmesh1 10.0.0.181, Pi 4 Model B, 58.9G card (36G used), user somog. Main server: meshcore-bot (`/opt/meshcore-bot`, config `/etc/meshcore-bot/config.ini`), mesh-discord-shim, MeshCore Hub, CoreScope (`/home/somog/meshcore-data`), Meshview, Graywolf, Postgres, MySQL (aprs-tnc-web).
- cnjmesh2 10.0.0.91, Pi Zero 2 W, Wi-Fi only, 59.6 GiB card, user somogyic. malla-web, malla-capture, mosquitto (Docker), cloudflared. Memory-tight: never run heavy jobs or the backup script on it.
- cnjmesh3 10.0.0.186, Pi 3 Model B+, 29.1G card (5.3G used), user somog. Observer + KPR2 radios; containers meshcore-mqtt-bridge and meshcore-packet-capture.
- None of the Pis can be wired (they sit near radios/antennas). Charlie keeps PuTTY sessions open; a dropped cnjmesh2 session was an early clue.

## State at end of this chat
Done Oct 22-23: journald persistent on all three Pis; cnjmesh2 flight recorder installed; NJ alert filter confirmed live by a real Mount Holly frost advisory; office-name patch applied and bot restarted (awaiting next real alert to see "by NWS Mount Holly"); full backup audit; new `cnjmesh1-extra-backup.sh`, fixed `cnjmesh-backup.sh`, updated `pull-cnjmesh1-backup.ps1`, new `verify-archive-sqlite.sh`, new `docs/backup-guide.md`; first complete backup set (cnjmesh1 main 180M, extra 123M, cnjmesh3 620K) pulled to `C:\Users\charl\OneDrive\Documents\cnjmesh-backups` via the desktop shortcut. Repo latest commit 8065be4 plus this file.

cnjmesh2: four unclean resets in about a week (Oct 22 ~20:30 needed a power cycle; 20:54 Wi-Fi SDIO errors then freeze; Oct 23 ~01:00 healthy then abrupt stop). Hardware watchdog recovers it in about a minute. Cause unresolved (Wi-Fi brcmfmac suspect, power not excluded). Plan: swap power supply and cable (ask what it uses), then USB Wi-Fi dongle with onboard Wi-Fi disabled, then replace. After any reset: `journalctl -b -1 -t flight-recorder | tail` and `journalctl -b -1 | tail -40`. Rule agreed: if it ever needs a hand reset again, stop investing time.

## Next actions, in order
1. Test restore step 1 on cnjmesh1: `cd ~/cnjmesh-scripts && git pull && bash scripts/verify-archive-sqlite.sh ~/backups/cnjmesh1-extra-2026-10-23_2043.tar.gz` (finishes on its own), then the same on `cnjmesh1-backup-2026-10-23_2029.tar.gz`. Record results in `docs/backup-guide.md` and `todos.md`. Remaining test-restore steps are in `todos.md`.
2. Spare microSD cards: sizes read Oct 23 (cnjmesh1 58.9G, cnjmesh2 59.6 GiB, cnjmesh3 29.1G). Spare must be at least as large as the source; 64 GB nominal is too tight for cnjmesh1/2, so suggest 128 GB high-endurance (Samsung PRO Endurance or SanDisk MAX Endurance) for cnjmesh1 and cnjmesh2, 64 GB for cnjmesh3. Buy from the manufacturer or Amazon-sold-and-shipped, test with f3/h2testw. Prices unchecked. Still ask whether he owns a USB microSD reader. Image with the Pi shut down; refresh quarterly. Sep 2 image `cnjmesh1-sdcard-20260902.img.gz` (2.4 GB) is on OneDrive, unverified.
3. cnjmesh2 power supply and cable swap.
4. Inventory refresh: `scripts/collect-inventory.sh` on cnjmesh1 and cnjmesh3 (then carefully cnjmesh2), commit refreshed `install-map-*.md`.
5. Passive: confirm "by NWS Mount Holly" on the next real alert; the 2:07 PM frost message origin and 7AM vs 9AM end-time mismatch (low priority).
6. Backup follow-ups: cnjmesh2 config-only backup (audit live first), fold extra script into main, verification step for cnjmesh3 script, cleanup of ~4.7 GB old Malla snapshots in cnjmesh1 `~/backups` (decide before deleting), scheduling and SSH keys for unattended laptop pull, radio settings and identity-key record.
7. Low priority: cnjmesh1 wlan0 promiscuous toggling every ~3 s (`sudo ss -0 -p | head -20`); optional `cnjmesh1/ping-watch/` (written, not installed); emoji patch `patch_node_heard_party.py` still unapplied.
8. Older backlog in `todos.md`: website deploy, Malla update, credential rotation, TD-H9 firmware decision, APRS learning, EHN gateway (`docs/ehn-gateway-project.md`), KPR1/Tilly bridge.
