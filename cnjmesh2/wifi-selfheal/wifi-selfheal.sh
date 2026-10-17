#!/usr/bin/env bash
#
# wifi-selfheal.sh -- Wi-Fi self-heal for cnjmesh2 (Pi Zero 2 W).
#
# Runs once a minute from a systemd timer. Pings the default gateway.
# After consecutive failures it escalates:
#   STAGE1 (default 3 failures, about 3 min): turn Wi-Fi off and on, reconnect
#   STAGE2 (default 6 failures, about 6 min): reload the brcmfmac Wi-Fi driver
#   STAGE3 (default 10 failures, about 10 min): reboot, at most once per
#          REBOOT_COOLDOWN seconds (default 3600) so a dead router can't cause
#          a reboot loop
# The failure counter lives in /run (RAM), so it costs no SD-card writes.
# Everything is logged to the journal under the tag "wifi-selfheal".
#
# Test safely:  sudo DRY_RUN=1 TARGET=192.0.2.1 STATE_DIR=/tmp/wsh STAGE1=1 STAGE2=2 STAGE3=3 ./wifi-selfheal.sh
# (run it 3 times; DRY_RUN=1 only logs what it WOULD do.)

set -u

STATE_DIR="${STATE_DIR:-/run/wifi-selfheal}"
PERSIST_DIR="${PERSIST_DIR:-/var/lib/wifi-selfheal}"
DRY_RUN="${DRY_RUN:-0}"
STAGE1="${STAGE1:-3}"
STAGE2="${STAGE2:-6}"
STAGE3="${STAGE3:-10}"
REBOOT_COOLDOWN="${REBOOT_COOLDOWN:-3600}"
TARGET="${TARGET:-}"
IFACE="${IFACE:-wlan0}"

log() { logger -t wifi-selfheal -- "$*" 2>/dev/null; echo "wifi-selfheal: $*"; }

run() {
  if [ "$DRY_RUN" = "1" ]; then
    log "DRY-RUN would run: $*"
  else
    "$@" >/dev/null 2>&1 || log "command failed (continuing): $*"
  fi
}

mkdir -p "$STATE_DIR" "$PERSIST_DIR" 2>/dev/null
COUNT_FILE="$STATE_DIR/fails"
fails=0
[ -r "$COUNT_FILE" ] && fails="$(cat "$COUNT_FILE" 2>/dev/null)"
case "$fails" in ''|*[!0-9]*) fails=0 ;; esac

# Target: the default gateway unless TARGET is set.
if [ -z "$TARGET" ]; then
  TARGET="$(ip route show default 2>/dev/null | awk '/default/ {print $3; exit}')"
fi

ok=0
if [ -n "$TARGET" ] && ping -c 2 -W 2 -q "$TARGET" >/dev/null 2>&1; then
  ok=1
fi

if [ "$ok" = "1" ]; then
  if [ "$fails" -gt 0 ]; then
    log "link OK again (gateway $TARGET answered) after $fails failed checks"
  fi
  echo 0 > "$COUNT_FILE"
  exit 0
fi

fails=$((fails + 1))
echo "$fails" > "$COUNT_FILE"
log "no reply from gateway '${TARGET:-none}' (consecutive failures: $fails)"

if [ "$fails" -eq "$STAGE1" ]; then
  log "stage 1: toggling Wi-Fi and reconnecting"
  run nmcli radio wifi off
  [ "$DRY_RUN" = "1" ] || sleep 3
  run nmcli radio wifi on
  [ "$DRY_RUN" = "1" ] || sleep 8
  run nmcli device connect "$IFACE"
elif [ "$fails" -eq "$STAGE2" ]; then
  log "stage 2: reloading the brcmfmac Wi-Fi driver"
  run modprobe -r brcmfmac_wcc
  run modprobe -r brcmfmac
  [ "$DRY_RUN" = "1" ] || sleep 2
  run modprobe brcmfmac
  [ "$DRY_RUN" = "1" ] || sleep 8
  run nmcli radio wifi on
  run nmcli device connect "$IFACE"
elif [ "$fails" -ge "$STAGE3" ]; then
  now="$(date +%s)"
  last=0
  [ -r "$PERSIST_DIR/last-reboot" ] && last="$(cat "$PERSIST_DIR/last-reboot" 2>/dev/null)"
  case "$last" in ''|*[!0-9]*) last=0 ;; esac
  if [ $((now - last)) -ge "$REBOOT_COOLDOWN" ]; then
    log "stage 3: still no network after $fails checks; rebooting"
    if [ "$DRY_RUN" != "1" ]; then
      echo "$now" > "$PERSIST_DIR/last-reboot"
      sync
    fi
    run systemctl reboot
  else
    log "stage 3: reboot suppressed (last script reboot was less than ${REBOOT_COOLDOWN}s ago)"
    if [ $((fails % 5)) -eq 0 ]; then
      log "retrying stage 1 (Wi-Fi toggle)"
      run nmcli radio wifi off
      [ "$DRY_RUN" = "1" ] || sleep 3
      run nmcli radio wifi on
      [ "$DRY_RUN" = "1" ] || sleep 8
      run nmcli device connect "$IFACE"
    fi
  fi
fi
exit 0
