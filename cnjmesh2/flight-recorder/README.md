# cnjmesh2 flight recorder

Once a minute, logs one line (uptime, load, free memory, swap, CPU temp, throttle flags,
Wi-Fi signal, gateway ping, SD-card error count) to the persistent journal and flushes it to disk.
After the next hang/reboot, the last `flight-recorder` line before the gap shows the state just
before it died.

Install (cnjmesh2, finishes on its own; adds one timer, restarts nothing):

    cd ~/cnjmesh-scripts && git pull
    sudo apt-get install -y iw    # only if `which iw` prints nothing
    sudo install -m 755 cnjmesh2/flight-recorder/flight-recorder.sh /usr/local/bin/
    sudo install -m 644 cnjmesh2/flight-recorder/flight-recorder.service cnjmesh2/flight-recorder/flight-recorder.timer /etc/systemd/system/
    sudo systemctl daemon-reload && sudo systemctl enable --now flight-recorder.timer

Read the log after an outage (finishes on its own):

    journalctl -t flight-recorder --no-pager | tail -30
    journalctl --list-boots
    journalctl -b -1 -t flight-recorder --no-pager | tail -20   # the boot BEFORE the reboot

Note: the Pi has no RTC, so timestamps just after a boot can be wrong; compare the `up=` field.
