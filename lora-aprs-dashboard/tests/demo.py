#!/usr/bin/env python3
"""Serve the page filled with SIMULATED traffic, to look at the layout.

Needs tests/harness/build.sh first (packets come from the firmware code).
Listens on 127.0.0.1:8090 only, uses a temporary database, no radio, no broker.
"""
import random
import sys
import tempfile
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

from support import APP  # noqa: F401  (puts app/ on the path)
import firmware
from dashboard import make_handler
from store import Store


def traffic(now, seed=7):
    """24 hours of made-up receptions: [(ts, op, rssi, snr, ferr, frame)]."""
    rng = random.Random(seed)
    # station, packets in 24 h, SNR, frequency offset, kind of packet
    stations = [("N0DIGI-10", 96, 4.0, -350, "beacon"), ("N0DIGI-3", 70, -9.0, 820, "beacon"),
                ("N0CALL-7", 140, -4.0, 150, "position"), ("N0CALL-9", 25, -14.0, -2100, "message"),
                ("N0CALL-5", 40, -18.5, 430, "position"), ("N0FAR", 2, -19.5, 90, "status")]
    # Made-up places around the harness's made-up receiver at 40.0 N, 74.5 W.
    where = {"N0DIGI-10": "4018.00N/07418.00W", "N0DIGI-3": "4033.00N/07445.00W",
             "N0CALL-7": "4007.20N/07437.20W", "N0CALL-5": "3951.00N/07412.00W"}
    events = []
    for call, count, snr0, ferr0, kind in stations:
        for _ in range(count):
            ts = now - rng.uniform(1, 86000)
            via = ""
            heard_snr, heard_ferr = snr0, ferr0
            if call in ("N0CALL-7", "N0CALL-9") and rng.random() < 0.4:
                via, heard_snr, heard_ferr = ",N0DIGI-10*", 4.0, -350
            snr = round((heard_snr + rng.gauss(0, 1.5)) * 4) / 4
            snr = max(-20.0, min(10.0, snr))
            noise = -113 + rng.gauss(0, 1.5)
            rssi = int(noise + snr if snr > 0 else noise + snr + 0.5)
            path = "APLRT1" + (via or ",WIDE1-1")
            spot = where.get(call, "4015.00N/07430.00W")
            body = {"beacon": "!%s#simulated digipeater" % spot,
                    "position": "!%s>simulated" % spot,
                    "message": ":N0CALL-7 :simulated message{%d" % rng.randint(1, 99),
                    "status": ">simulated status"}[kind]
            raw = "%s>%s:%s" % (call, path, body)
            events.append((ts, "rx", rssi, snr, heard_ferr + rng.randint(-60, 60),
                           firmware.HEADER + raw.encode()))
    for i in range(48):
        events.append((now - 1800 * i - 5, "tx", 0, 0.0, 0,
                       b"K2GIA-10>APLRG1,WIDE1-1,WIDE2-1,RFONLY,NOGATE:>simulated beacon"))
    for _ in range(9):
        events.append((now - rng.uniform(1, 86000), "crc", -128, -19.5, 900,
                       firmware.HEADER + b"N0??garbled"))
    return sorted(events)


def fill(store, now):
    events = traffic(now)
    results = firmware.run([e[1:] for e in events])
    for (ts, op, *_), (line, topic, payload, _digi) in zip(events, results):
        store.on_syslog(line, ts)
        if op == "rx" and payload is not None:
            store.on_mqtt(topic.decode().rsplit("/", 1)[1], payload, ts + 0.1)
    store.status.update(mqtt_connected=True, syslog_last=now, mqtt_last=now)


def main():
    if not firmware.BINARY.exists():
        sys.exit("Run tests/harness/build.sh first.")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8090
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(str(Path(tmp) / "demo.db"), setup={
            "Hardware": "simulated receiver", "Antenna": "simulated antenna"},
            home=(40.0, -74.5))
        now = time.time()
        fill(store, now)
        server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(store, lambda: now))
        print("SIMULATED data on http://127.0.0.1:%d  (Ctrl+C stops it)" % port, flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
