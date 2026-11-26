import tempfile
import unittest
from pathlib import Path

from support import SAMPLES, mqtt, syslog
import aprs
from dashboard import settings
from store import Store

T = 1_000_000.0


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(str(Path(self.tmp.name) / "t.db"))

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def rows(self):
        return list(reversed(self.store.recent(500)))

    def feed(self, name, ts, order=("syslog", "mqtt")):
        for source in order:
            if source == "syslog":
                self.store.on_syslog(syslog(name), ts)
            elif SAMPLES[name]["mqtt_payload"]:
                self.store.on_mqtt(*mqtt(name), ts=ts + 0.05)
            ts += 0.01


class Joining(Base):
    def test_both_orders_give_one_complete_row_per_packet(self):
        names = [n for n, s in SAMPLES.items()
                 if s["op"] == "rx" and s["mqtt_payload"]]
        for order in (("syslog", "mqtt"), ("mqtt", "syslog")):
            with self.subTest(order):
                self.tearDown()
                self.setUp()
                for i, name in enumerate(names):
                    self.feed(name, T + 10 * i, order)
                rows = self.rows()
                self.assertEqual(len(rows), len(names))
                for name, row in zip(names, rows):
                    self.assertEqual((row["syslog"], row["mqtt"]), (1, 1), name)
                    self.assertEqual(row["snr"], SAMPLES[name]["snr"], name)
                    self.assertEqual(row["length"],
                                     3 + len(SAMPLES[name]["mqtt_payload"]), name)
                    self.assertNotEqual(row["via"], "unknown", name)

    def test_syslog_only_does_not_guess_a_path(self):
        self.store.on_syslog(syslog("position_wide1"), T)
        row, = self.rows()
        self.assertEqual((row["via"], row["transmitter"], row["exact"]),
                         ("unknown", None, 0))

    def test_syslog_only_uses_a_path_that_is_there(self):
        self.store.on_syslog(syslog("position_via_digi"), T)
        row, = self.rows()
        self.assertEqual((row["via"], row["transmitter"]), ("digi", "N0DIGI-10"))

    def test_mqtt_only_has_path_but_no_signal(self):
        self.store.on_mqtt(*mqtt("message"), ts=T)
        row, = self.rows()
        self.assertEqual((row["via"], row["rssi"]), ("direct", None))

    def test_late_partner_is_not_joined(self):
        self.store.on_syslog(syslog("message"), T)
        self.store.on_mqtt(*mqtt("message"), ts=T + 20)
        self.assertEqual(len(self.rows()), 2)

    def test_same_packet_twice_pairs_with_the_nearest(self):
        self.store.on_syslog(syslog("status"), T)
        self.store.on_syslog(syslog("status"), T + 3)
        self.store.on_mqtt(*mqtt("status"), ts=T + 3.1)
        first, second = self.rows()
        self.assertEqual((first["mqtt"], second["mqtt"]), (0, 1))

    def test_one_feed_down_does_not_pile_up_memory(self):
        for source in ("syslog", "mqtt"):
            for i in range(200):
                if source == "syslog":
                    self.store.on_syslog(syslog("status"), T + 10 * i)
                else:
                    self.store.on_mqtt(*mqtt("message"), ts=T + 10 * i)
            self.assertLessEqual(len(self.store._waiting[source]), 1)

    def test_own_topic_never_creates_a_row(self):
        # A message under our own call alone is not counted as heard.
        self.store.on_mqtt("K2GIA-10", b"K2GIA-10>APLRG1::N0CALL-7 :hi", ts=T)
        self.assertEqual(self.rows(), [])

    def test_topic_must_agree_with_sender(self):
        self.store.on_mqtt("N0CALL-1", mqtt("message")[1], ts=T)
        self.assertEqual(self.rows(), [])

    def test_ignored_and_unreadable_lines(self):
        self.store.on_syslog(syslog("own_internet_beacon"), T)
        self.store.on_syslog(b"not an iGate line", T)
        self.store.on_syslog(syslog("status").replace(b"K2GIA-10", b"N0ELSE-10"), T)
        self.assertEqual(self.rows(), [])
        self.assertEqual((self.store.status["ignored"],
                          self.store.status["unparsed"]), (1, 2))

    def test_purge(self):
        self.store.on_syslog(syslog("status"), T)
        self.store.on_syslog(syslog("message"), T + 40 * 86400)
        self.assertEqual(self.store.purge(30, now=T + 40 * 86400), 1)
        self.assertEqual(len(self.rows()), 1)


class Figures(Base):
    def test_tables_and_windows(self):
        self.feed("position_wide1", T - 7200)       # outside the 1 h window
        self.feed("position_wide1", T - 1800)
        self.feed("position_via_digi", T - 300)
        self.feed("status", T - 120)                # N0DIGI-10's own packet
        self.feed("object", T - 90)
        self.store.on_syslog(syslog("crc_error"), T - 60)
        self.store.on_syslog(syslog("tx_own_beacon"), T - 30)
        self.store.on_syslog(syslog("message"), T - 20)      # path unknown
        s = self.store.summary(T)

        self.assertEqual([w["packets"] for w in s["windows"]], [4, 5, 6])
        self.assertEqual([w["crc_errors"] for w in s["windows"]], [1, 1, 1])
        self.assertEqual([w["sent"] for w in s["windows"]], [1, 1, 1])

        local = {r["call"]: r for r in s["local"]}
        self.assertEqual(set(local), {"N0CALL-7", "N0DIGI-10"})
        direct, digi = local["N0CALL-7"], local["N0DIGI-10"]
        # the copy heard from the digipeater is not counted as N0CALL-7's signal
        self.assertEqual((direct["packets"], direct["snr"], direct["rssi"]),
                         (2, 9.5, -97))
        self.assertIsNone(direct["noise"])          # SNR too high to estimate
        self.assertEqual(direct["dist_km"], 27.8)
        # digipeater row: one relayed packet, its own status and object
        self.assertEqual((digi["packets"], digi["relayed"]), (3, 1))
        self.assertAlmostEqual(digi["snr"], (-6.25 - 3.5 - 3.5) / 3)
        self.assertIsNone(digi["dist_km"])          # relayed position is not its own
        length = 3 + len(SAMPLES["position_wide1"]["mqtt_payload"])
        self.assertAlmostEqual(direct["toa_pct"],
                               100 * aprs.airtime(length) / 3600)

        self.assertEqual(s["relayed"][0]["digi"], "N0DIGI-10")
        self.assertEqual(s["relayed"][0]["stations"][0]["call"], "N0CALL-7")
        self.assertEqual([r["call"] for r in s["unknown"]], ["N0CALL-9"])
        self.assertEqual(s["own_tx"]["packets"], 1)

    def test_channel_load_with_crc_estimate(self):
        self.feed("status", T - 120)
        w = self.store.summary(T)["windows"][0]
        self.assertEqual(w["busy_crc_pct"], w["busy_pct"])      # no CRC errors
        self.store.on_syslog(syslog("crc_error"), T - 60)
        self.store.on_syslog(syslog("crc_error"), T - 30)
        w = self.store.summary(T)["windows"][0]
        one = aprs.airtime(3 + len(SAMPLES["status"]["mqtt_payload"]))
        self.assertAlmostEqual(w["busy_pct"], 100 * one / 600)
        self.assertAlmostEqual(w["busy_crc_pct"], 100 * 3 * one / 600)

    def test_crc_errors_alone_give_no_estimate(self):
        self.store.on_syslog(syslog("crc_error"), T - 60)
        w = self.store.summary(T)["windows"][0]
        self.assertEqual((w["crc_errors"], w["busy_crc_pct"]), (1, None))

    def test_setup_text_is_passed_through(self):
        store = Store(str(Path(self.tmp.name) / "s.db"), setup={"Antenna": "whip"})
        self.assertEqual(store.summary(T)["setup"], {"Antenna": "whip"})
        store.close()

    def test_setup_settings(self):
        self.assertEqual(settings({})["setup"], {})
        self.assertEqual(
            settings({"SETUP_ANTENNA": " whip on the sill ", "SETUP_NOTES": ""})["setup"],
            {"Antenna": "whip on the sill"})

    def test_positions(self):
        self.feed("position_wide1", T - 600)
        self.feed("position_via_digi", T - 300)    # relayed: still N0CALL-7's own
        self.feed("status", T - 200)               # no position
        e = aprs.parse_syslog(syslog("position_via_digi"))
        s = self.store.summary(T)
        self.assertEqual(set(s["positions"]), {"N0CALL-7"})
        p = s["positions"]["N0CALL-7"]
        self.assertEqual((p["lat"], p["lon"]), (e["lat"], e["lon"]))
        self.assertIsNone(s["home"])

    def test_position_from_syslog_survives_join_in_either_order(self):
        self.feed("position_wide1", T, order=("mqtt", "syslog"))
        row, = self.rows()
        self.assertEqual((row["lat"], row["lon"]), (40.25, -74.5))

    def test_older_database_gets_new_columns(self):
        import sqlite3
        path = str(Path(self.tmp.name) / "old.db")
        old = sqlite3.connect(path)
        old.execute("CREATE TABLE packets (id INTEGER PRIMARY KEY, ts REAL NOT NULL,"
                    " kind TEXT NOT NULL, sender TEXT, transmitter TEXT, via TEXT,"
                    " type TEXT, rssi INTEGER, snr REAL, freq_err INTEGER,"
                    " length INTEGER, exact INTEGER, header TEXT, info TEXT,"
                    " dist_km REAL, syslog INTEGER NOT NULL DEFAULT 0,"
                    " mqtt INTEGER NOT NULL DEFAULT 0)")
        old.commit()
        old.close()
        store = Store(path)
        store.on_syslog(syslog("position_wide1"), T)
        self.assertIn("N0CALL-7", store.summary(T)["positions"])
        store.close()

    def test_home_setting(self):
        self.assertIsNone(settings({})["home"])
        self.assertEqual(settings({"OWN_LAT": "40.1", "OWN_LON": "-74.6"})["home"],
                         (40.1, -74.6))
        with self.assertRaises(ValueError):
            settings({"OWN_LAT": "140", "OWN_LON": "0"})
        store = Store(str(Path(self.tmp.name) / "h.db"), home=(40.1, -74.6))
        self.assertEqual(store.summary(T)["home"], {"lat": 40.1, "lon": -74.6})
        store.close()

    def test_empty(self):
        s = self.store.summary(T)
        self.assertEqual((s["local"], s["data_since"]), ([], None))


if __name__ == "__main__":
    unittest.main()
