# ping-watch (cnjmesh1)
Logs the exact time cnjmesh2 goes down / comes back (cnjmesh1 has a reliable clock).

Install (cnjmesh1, finishes on its own; adds one small service):

    cd ~/cnjmesh-scripts && git pull
    sudo install -m 755 cnjmesh1/ping-watch/ping-watch-cnjmesh2.sh /usr/local/bin/
    sudo install -m 644 cnjmesh1/ping-watch/ping-watch.service /etc/systemd/system/
    sudo systemctl daemon-reload && sudo systemctl enable --now ping-watch.service

Read it:  journalctl -t ping-watch --no-pager | tail
