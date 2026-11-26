"""SQLite storage, joining of the two feeds, and the figures the page shows."""
import sqlite3
import statistics
import threading
import time

import aprs

# The firmware sends the syslog line and the MQTT message for one packet within
# moments of each other. A digipeated copy of the same packet cannot follow
# this quickly at SF12 (it has to be sent again over the air).
MATCH_WINDOW = 4.0
DIM_BELOW = 3

SCHEMA = """
CREATE TABLE IF NOT EXISTS packets (
    id          INTEGER PRIMARY KEY,
    ts          REAL NOT NULL,
    kind        TEXT NOT NULL,      -- rx, crc, tx
    sender      TEXT,               -- station that wrote the packet
    transmitter TEXT,               -- station we actually heard, if known
    via         TEXT,               -- direct, digi, relayed, unknown
    type        TEXT,
    rssi        INTEGER,
    snr         REAL,
    freq_err    INTEGER,
    length      INTEGER,            -- bytes on air
    exact       INTEGER,            -- 0: length is only a lower bound
    header      TEXT,
    info        TEXT,
    dist_km     REAL,
    syslog      INTEGER NOT NULL DEFAULT 0,
    mqtt        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS packets_ts ON packets (ts);
"""


class Store:
    def __init__(self, path, own_call="K2GIA-10", sf=12, bw=125000, cr=5,
                 preamble=8):
        self.own_call = own_call
        self.radio = {"sf": sf, "bw": bw, "cr": cr, "preamble": preamble}
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.executescript(SCHEMA)
        self._waiting = {"syslog": [], "mqtt": []}   # (ts, key, row id)
        self.status = {
            "started": time.time(), "syslog_last": None, "mqtt_last": None,
            "mqtt_connected": None, "firmware": None, "matched": 0,
            "unparsed": 0, "last_unparsed": None, "ignored": 0,
        }

    def close(self):
        with self.lock:
            self.db.close()

    # ---- incoming ---------------------------------------------------------

    def on_syslog(self, datagram, ts=None):
        ts = time.time() if ts is None else ts
        event = aprs.parse_syslog(datagram)
        with self.lock:
            if event is None or event["igate"] != self.own_call:
                self.status["unparsed"] += 1
                self.status["last_unparsed"] = aprs.show(
                    datagram[:300].decode("latin-1"))
                return None
            self.status["syslog_last"] = ts
            self.status["firmware"] = event["firmware"]
            if event["kind"] == "rx":
                return self._syslog_rx(event, ts)
            if event["kind"] == "crc":
                return self._insert(ts=ts, kind="crc", rssi=event["rssi"],
                                    snr=event["snr"],
                                    freq_err=event["freq_err"], syslog=1)
            if event["kind"] == "tx":
                raw = event.get("raw")
                parts = aprs.split_tnc2(raw) if raw else None
                length = 3 + len(raw) if raw else 3 + len(event["info"]) + 20
                return self._insert(
                    ts=ts, kind="tx", sender=parts[0] if parts else None,
                    transmitter=self.own_call, via="direct", type=event["type"],
                    length=length, exact=1 if raw else 0,
                    header=parts[1] if parts else None,
                    info=parts[2] if parts else event["info"], syslog=1)
            return None

    def _syslog_rx(self, event, ts):
        # The iGate can log its own internet beacon as "RX" with zero figures.
        if event["rssi"] == 0 and event["snr"] == 0 and event["freq_err"] == 0:
            self.status["ignored"] += 1
            return None
        fields = dict(rssi=event["rssi"], snr=event["snr"],
                      freq_err=event["freq_err"], dist_km=event.get("dist_km"),
                      syslog=1)
        partner = self._take("mqtt", event["content"], ts)
        if partner is not None:
            self._update(partner, **fields)
            self.status["matched"] += 1
            return partner
        if event["header"] is not None:
            via, heard = aprs.transmitter(event["sender"], event["header"])
        else:
            via, heard = "unknown", None
        row = self._insert(
            ts=ts, kind="rx", sender=event["sender"], transmitter=heard,
            via=via, type=event["type"], header=event["header"],
            info=event["info"] if event["info"] is not None
            else event.get("comment"),
            length=aprs.minimum_length(event),
            exact=1 if event["raw"] else 0, **fields)
        self._wait("syslog", event["content"], ts, row)
        return row

    def on_mqtt(self, sender_topic, payload, ts=None):
        """sender_topic is the last level of the topic, payload is bytes."""
        ts = time.time() if ts is None else ts
        raw = payload.decode("latin-1")
        parts = aprs.split_tnc2(raw)
        with self.lock:
            if not parts or parts[0] != sender_topic:
                self.status["ignored"] += 1
                return None
            sender, header, info = parts
            via, heard = aprs.transmitter(sender, header)
            content = aprs.expected_content(raw)
            fields = dict(sender=sender, transmitter=heard, via=via,
                          type=aprs.packet_type(info), header=header, info=info,
                          length=3 + len(raw), exact=1, mqtt=1)
            partner = self._take("syslog", content, ts)
            if partner is not None:
                self.status["mqtt_last"] = ts
                self._update(partner, **fields)
                self.status["matched"] += 1
                return partner
            # A message under our own callsign's topic is not by itself proof
            # that the iGate heard anything, so it only ever completes a syslog
            # record. It never creates one.
            if sender_topic == self.own_call:
                self.status["ignored"] += 1
                return None
            self.status["mqtt_last"] = ts
            row = self._insert(ts=ts, kind="rx", **fields)
            self._wait("mqtt", content, ts, row)
            return row

    def _wait(self, source, key, ts, row):
        # Drop expired entries here too: if one feed is down, nothing else would.
        queue = [w for w in self._waiting[source] if ts - w[0] <= MATCH_WINDOW]
        queue.append((ts, key, row))
        self._waiting[source] = queue

    def _take(self, source, key, ts):
        """Find and remove the closest unmatched record from the other feed."""
        queue = [w for w in self._waiting[source]
                 if abs(ts - w[0]) <= MATCH_WINDOW]
        self._waiting[source] = queue
        best = min((w for w in queue if w[1] == key),
                   key=lambda w: abs(ts - w[0]), default=None)
        if best is None:
            return None
        queue.remove(best)
        return best[2]

    def _insert(self, **fields):
        names = ",".join(fields)
        marks = ",".join("?" * len(fields))
        with self.db:
            cur = self.db.execute(
                "INSERT INTO packets (%s) VALUES (%s)" % (names, marks),
                list(fields.values()))
        return cur.lastrowid

    def _update(self, row, **fields):
        sets = ",".join("%s=?" % k for k in fields)
        with self.db:
            self.db.execute("UPDATE packets SET %s WHERE id=?" % sets,
                            list(fields.values()) + [row])

    def purge(self, days, now=None):
        now = time.time() if now is None else now
        with self.lock, self.db:
            return self.db.execute("DELETE FROM packets WHERE ts < ?",
                                   (now - days * 86400,)).rowcount

    # ---- figures ----------------------------------------------------------

    def _air(self, row):
        return aprs.airtime(row["length"], **self.radio) if row["length"] else 0

    def summary(self, now=None):
        now = time.time() if now is None else now
        with self.lock:
            rows = [dict(r) for r in self.db.execute(
                "SELECT * FROM packets WHERE ts >= ? AND ts <= ? ORDER BY ts",
                (now - 86400, now))]
            status = dict(self.status)
            first = self.db.execute("SELECT MIN(ts) FROM packets").fetchone()[0]

        windows = []
        for label, seconds in (("10 min", 600), ("1 hour", 3600),
                               ("24 hours", 86400)):
            part = [r for r in rows if r["ts"] >= now - seconds]
            heard = [r for r in part if r["kind"] == "rx"]
            windows.append({
                "label": label,
                "packets": len(heard),
                "stations": len({r["transmitter"] for r in heard
                                 if r["transmitter"]}),
                "crc_errors": sum(r["kind"] == "crc" for r in part),
                "sent": sum(r["kind"] == "tx" for r in part),
                "busy_pct": 100 * sum(self._air(r) for r in part
                                      if r["kind"] != "crc") / seconds,
            })

        rx = [r for r in rows if r["kind"] == "rx"]
        local, relayed, unknown = {}, {}, {}
        for r in rx:
            if r["transmitter"]:
                local.setdefault(r["transmitter"], []).append(r)
                if r["via"] == "digi":
                    relayed.setdefault(r["transmitter"], {}).setdefault(
                        r["sender"], []).append(r)
            else:
                unknown.setdefault(r["sender"], []).append(r)

        tx = [r for r in rows if r["kind"] == "tx"]
        hour_tx = [r for r in tx if r["ts"] >= now - 3600]
        return {
            "now": now,
            "station": self.own_call,
            "radio": self.radio,
            "dim_below": DIM_BELOW,
            "data_since": first,
            "status": status,
            "tested_firmware": aprs.TESTED_FIRMWARE,
            "windows": windows,
            "local": [self._station(c, g, now) for c, g in local.items()],
            "relayed": [{
                "digi": digi,
                "stations": [{"call": c, "packets": len(g),
                              "last": g[-1]["ts"]} for c, g in senders.items()],
            } for digi, senders in sorted(relayed.items())],
            "unknown": [self._station(c, g, now) for c, g in unknown.items()],
            "own_tx": {
                "packets": len(tx),
                "toa_pct": 100 * sum(map(self._air, hour_tx)) / 3600,
                "estimated": any(not r["exact"] for r in hour_tx),
                "last": tx[-1]["ts"] if tx else None,
            },
        }

    def _station(self, call, group, now):
        signal = [r for r in group if r["snr"] is not None]
        noise = [n for n in (aprs.noise_estimate(r["rssi"], r["snr"])
                             for r in signal) if n is not None]
        hour = [r for r in group if r["ts"] >= now - 3600]
        # Distance belongs to whoever wrote the position, so only own packets.
        dist = [r["dist_km"] for r in group
                if r["dist_km"] is not None and r["sender"] == call]

        def mean(key):
            return statistics.fmean(r[key] for r in signal) if signal else None

        return {
            "call": call,
            "packets": len(group),
            "relayed": sum(r["via"] == "digi" for r in group),
            "with_signal": len(signal),
            "last": group[-1]["ts"],
            "snr": mean("snr"),
            "rssi": mean("rssi"),
            "noise": statistics.median(noise) if noise else None,
            "freq_err": statistics.median(r["freq_err"] for r in signal)
            if signal else None,
            "toa_pct": 100 * sum(map(self._air, hour)) / 3600,
            "estimated": any(not r["exact"] for r in hour),
            "dist_km": dist[-1] if dist else None,
        }

    def recent(self, limit=100):
        with self.lock:
            rows = [dict(r) for r in self.db.execute(
                "SELECT * FROM packets ORDER BY ts DESC, id DESC LIMIT ?",
                (max(1, min(int(limit), 500)),))]
        for r in rows:
            r["info"] = aprs.show(r["info"])
            r["header"] = aprs.show(r["header"])
        return rows
