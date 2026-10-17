# cnjmesh2 Wi-Fi self-heal

Why: cnjmesh2 (Pi Zero 2 W, Wi-Fi only) was found unreachable twice (Sep 22 and Oct 16 2026), and on Oct 17 its kernel log showed a Wi-Fi chip (brcmfmac SDIO) glitch that recovered by itself. The hardware watchdog cannot catch "Pi alive, Wi-Fi dead", so this script does.

What it does (once a minute, from a systemd timer):
1. Pings the default gateway.
2. After 3 failures in a row (about 3 min): turns Wi-Fi off and on and reconnects.
3. After 6 failures: reloads the brcmfmac driver.
4. After 10 failures: reboots, at most once an hour (no reboot loop if the router is down).
5. Logs everything to the journal with the tag `wifi-selfheal` (`journalctl -t wifi-selfheal`).
The failure counter is in RAM (`/run`), so no SD-card wear. The only file written to disk is the time of the last script-triggered reboot.

Files: `wifi-selfheal.sh`, `wifi-selfheal.service`, `wifi-selfheal.timer`. Installed to `/opt/wifi-selfheal/` and `/etc/systemd/system/`.

Safe test (only logs, changes nothing): `sudo DRY_RUN=1 TARGET=192.0.2.1 STATE_DIR=/tmp/wsh STAGE1=1 STAGE2=2 STAGE3=3 /opt/wifi-selfheal/wifi-selfheal.sh` three times.

Remove: `sudo systemctl disable --now wifi-selfheal.timer` and delete the files above.

Not covered: if the router itself is down, the script only reboots once an hour; it cannot fix the router.
