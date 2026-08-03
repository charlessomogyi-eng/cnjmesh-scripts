# cnjmesh1 OS / Kernel Update Plan (drafted Aug 2, 2026 — SEPARATE dedicated session)

## Recommendation: `apt upgrade` (security + kernel patches), NOT `apt full-upgrade`
Rationale: cnjmesh1 is a critical always-on server. Patch for security/bug fixes; do NOT chase "latest" for its own sake. `full-upgrade` does aggressive dependency changes + package removals = more risk for no benefit on a working box. Same lesson as the Malla-version question: "latest" isn't automatically better, and every bump is a regression chance.

## FIRST — confirm there's even anything to upgrade (don't assume)
As of July 31, cnjmesh1 was already on CURRENT Trixie, kernel 6.12.62 (Dec 2025). There may be little/nothing newer. Confirm before planning further:
```
cat /etc/os-release
uname -a
sudo apt update
apt list --upgradable 2>/dev/null | wc -l
apt list --upgradable 2>/dev/null | grep -iE 'linux-image|raspberrypi-kernel|linux-headers'
```
If no kernel packages are upgradable, the "kernel upgrade" is moot — you're current. Decide then whether the other pending updates are worth it.

## WHY this is its own session (higher risk than the Malla config work)
- Requires a REBOOT to activate a new kernel — on a memory-tight box with 16 containers + many systemd services (meshview, graywolf, weather bots, aprs-tnc-web, meshcore stacks). Slow recovery; must be watched.
- Kernel changes can (low prob, non-zero) affect: USB serial enumeration (KPR1 radio, /dev/serial/by-id paths), WiFi driver behavior (cnjmesh1 has had networking gremlins), Docker.
- If it fails mid-upgrade, can leave a box that won't boot cleanly. cnjmesh1 is the main server — don't do this without time + reliable access.

## PRECONDITIONS (all must be true before starting)
1. Malla fix DONE and cnjmesh1 confirmed stable first (do NOT combine sessions).
2. Full backup taken (run `scripts/cnjmesh1-backup.sh`) AND the Malla DB backed up (named-volume — see backup-gap todo) AND ideally an image/SD backup if feasible.
3. A solid uninterrupted time block + reliable access to the Pi (physical or confidently-remote). NOT late at night after a long session.
4. Disk has healthy free space (post-mqtt-filter-fix it's ~52% — good). Confirm again.
5. Note current kernel version (`uname -r`) so you can confirm the change / roll back reasoning.

## PROCEDURE (once preconditions met)
```
# 1. Refresh package lists
sudo apt update

# 2. REVIEW what will change BEFORE applying — don't blind-upgrade
apt list --upgradable 2>/dev/null | less
#   (note the kernel packages specifically; sanity-check nothing alarming is being removed)

# 3. Apply standard upgrades (security + kernel). NOT full-upgrade.
sudo apt upgrade
#   Review the summary it prints (esp. any packages to be REMOVED — if it wants to remove
#   something important, STOP and reconsider; that's full-upgrade-like behavior).

# 4. Deliberate reboot — with time to watch it come back
sudo reboot
```

## AFTER REBOOT — verify everything recovered
```
uname -r                    # confirm new kernel (or same, if nothing changed)
uptime && free -h && df -h /
docker ps -a --format 'table {{.Names}}\t{{.Status}}'   # all 16 containers back up?
systemctl --failed          # any failed services?
ls -l /dev/serial/by-id/    # USB radio devices still enumerated correctly?
ping -4 -c 3 10.0.0.1       # WiFi/gateway still good?
```
Then run the full health-check sweep (`docs/health-check-plan-aug2026.md`) — Observer/KPR2/KPR1/APRS/LoRa APRS/Malla — to confirm nothing regressed. Pay special attention to USB serial (radios) and WiFi, the two things a kernel change is most likely to disturb.

## ROLLBACK
- Debian keeps the previous kernel installed by default — if the new kernel misbehaves, you can boot the old one (via /boot config or GRUB-equivalent; on Pi it's the previous `linux-image` still present). Confirm the old kernel package wasn't autoremoved.
- Full config/data restore from the backup taken in preconditions if needed.

## SEQUENCING (locked in with Charles Aug 2)
- Malla config fix (retention + gunicorn) = FIRST, separate.
- This OS/kernel update = its own dedicated session AFTER, with the safeguards above.
- Do NOT bundle them.
