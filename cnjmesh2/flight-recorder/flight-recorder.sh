#!/bin/bash
# Runs once a minute (timer). Writes one health line to the persistent journal, then flushes it
# to disk, so after a hang the LAST line shows the Pi's state just before it died.
GW=$(ip route | awk '/default/ {print $3; exit}')
up=$(cut -d' ' -f1 /proc/uptime)
load=$(cut -d' ' -f1-3 /proc/loadavg)
memavail=$(awk '/MemAvailable/ {printf "%d", $2/1024}' /proc/meminfo)
swapused=$(awk '/SwapTotal/ {t=$2} /SwapFree/ {f=$2} END {printf "%d", (t-f)/1024}' /proc/meminfo)
temp=$(vcgencmd measure_temp 2>/dev/null | cut -d= -f2)
thr=$(vcgencmd get_throttled 2>/dev/null | cut -d= -f2)
sig=$(iw dev wlan0 link 2>/dev/null | awk '/signal:/ {print $2" dBm"}')
if ping -c1 -W2 "$GW" >/dev/null 2>&1; then gw=ok; else gw=FAIL; fi
mmcerr=$(dmesg 2>/dev/null | grep -c -i -E 'mmc.*(error|timeout)|I/O error')
echo "up=${up}s load=${load} memavail=${memavail}MB swapused=${swapused}MB temp=${temp} throttled=${thr} wifi=${sig:-none} gw=${gw} mmc_errs=${mmcerr}" | systemd-cat -t flight-recorder -p info
journalctl --sync
