#!/bin/bash
# Pings cnjmesh2 every 10 s and logs ONLY changes (up/down) to cnjmesh1's journal, which has a good clock.
HOST=10.0.0.91; old=""
while true; do
  if ping -c1 -W2 "$HOST" >/dev/null 2>&1; then new=up; else new=down; fi
  [ "$new" != "$old" ] && logger -t ping-watch "cnjmesh2 $new" && old=$new
  sleep 10
done
