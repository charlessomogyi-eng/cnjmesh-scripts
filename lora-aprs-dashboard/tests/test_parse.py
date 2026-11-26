import unittest

from support import FIXTURES, SAMPLES, mqtt, syslog
import aprs


class Syslog(unittest.TestCase):
    def test_every_received_sample_keeps_its_signal_figures(self):
        for name, s in SAMPLES.items():
            if s["op"] not in ("rx", "crc"):
                continue
            with self.subTest(name):
                e = aprs.parse_syslog(syslog(name))
                self.assertEqual(
                    (e["kind"], e["rssi"], e["snr"], e["freq_err"]),
                    (s["op"], s["rssi"], s["snr"], s["freq_err"]))

    def test_sender_and_type(self):
        want = {
            "position_wide1": ("N0CALL-7", "position"),
            "position_via_digi": ("N0CALL-7", "position"),
            "position_timestamp": ("N0CALL-3", "position"),
            "message": ("N0CALL-9", "message"),
            "message_fake_signal": ("N0CALL-9", "message"),
            "status": ("N0DIGI-10", "status"),
            "mic_e": ("N0CALL-5", "mic-e"),
            "object": ("N0DIGI-10", "object"),
            "telemetry": ("N0CALL-5", "telemetry"),
            "weather": ("N0CALL-5", "weather"),
            "third_party": ("N0DIGI-10", "third-party"),
            "too_long_for_mqtt": ("N0CALL-3", "status"),
        }
        for name, expected in want.items():
            with self.subTest(name):
                e = aprs.parse_syslog(syslog(name))
                self.assertEqual((e["sender"], e["type"]), expected)

    def test_where_the_path_survives(self):
        header = lambda n: aprs.parse_syslog(syslog(n))["header"]
        self.assertIsNone(header("position_wide1"))
        self.assertIsNone(header("message"))
        self.assertEqual(header("position_via_digi"), "APLRT1,N0DIGI-10*,WIDE2-1")
        self.assertEqual(header("position_no_path"), "APLRT1")
        self.assertEqual(header("weather"), "APRS")

    def test_distance_and_comment(self):
        e = aprs.parse_syslog(syslog("position_wide1"))
        self.assertEqual((e["lat"], e["lon"], e["dist_km"], e["comment"]),
                         (40.25, -74.5, 27.8, "direct"))

    def test_transmit_lines(self):
        beacon = aprs.parse_syslog(syslog("tx_own_beacon"))
        self.assertTrue(beacon["raw"].startswith("K2GIA-10>APLRG1,WIDE1-1"))
        digi = aprs.parse_syslog(syslog("tx_digipeat"))
        self.assertTrue(digi["raw"].startswith("N0CALL-7>APLRT1,K2GIA-10*:"))
        message = aprs.parse_syslog(syslog("tx_message"))
        self.assertEqual((message["type"], message["raw"]), ("message", None))

    def test_firmware_cuts_tx_message_sender(self):
        self.assertIn("TX / MESSAGE / IA-10 --->", SAMPLES["tx_message"]["syslog"])

    def test_unrelated_traffic_is_rejected(self):
        for junk in (b"", b"hello", b"<13>Nov 25 pi sshd[1]: x",
                     b"<165>1 - K2GIA-10 CA2RXU_LoRa_iGate_3.2.4 - - - RX / cut"):
            self.assertIsNone(aprs.parse_syslog(junk))


class Matching(unittest.TestCase):
    def test_mqtt_payload_predicts_the_syslog_content(self):
        for name, s in SAMPLES.items():
            if s["op"] == "rx" and s["mqtt_payload"]:
                with self.subTest(name):
                    self.assertEqual(
                        aprs.expected_content(mqtt(name)[1].decode("latin-1")),
                        aprs.parse_syslog(syslog(name))["content"])


class Path(unittest.TestCase):
    def test_transmitter(self):
        t = lambda header: aprs.transmitter("SRC", header)
        self.assertEqual(t("APRS"), ("direct", "SRC"))
        self.assertEqual(t("APRS,WIDE1-1,WIDE2-1"), ("direct", "SRC"))
        self.assertEqual(t("APRS,DIGI-1*,WIDE2-1"), ("digi", "DIGI-1"))
        self.assertEqual(t("APRS,DIGI-1,DIGI-2*"), ("digi", "DIGI-2"))
        self.assertEqual(t("APRS,DIGI-1*,DIGI-2*,WIDE2-1"), ("digi", "DIGI-2"))
        self.assertEqual(t("APRS,DIGI-1,WIDE1*,WIDE2-1"), ("digi", "DIGI-1"))
        self.assertEqual(t("APRS,WIDE1*"), ("relayed", None))

    def test_paths_made_by_the_firmware_digipeater(self):
        want = {"wide1_first_hop": "K2GIA-10", "wide2_second_hop": "K2GIA-10",
                "wide2_2": "K2GIA-10"}
        for name, digi in want.items():
            with self.subTest(name):
                sender, header, _ = aprs.split_tnc2(
                    FIXTURES["digipeats"][name]["sent"])
                self.assertEqual(aprs.transmitter(sender, header), ("digi", digi))


class Radio(unittest.TestCase):
    def test_airtime_against_known_figures(self):
        # 13 byte frame, BW125, CR4/5, preamble 8: the usual published values
        self.assertAlmostEqual(aprs.airtime(13, sf=12), 1.155072, places=6)
        self.assertAlmostEqual(aprs.airtime(13, sf=7), 0.046336, places=6)

    def test_noise_estimate(self):
        self.assertIsNone(aprs.noise_estimate(-80, 9.5))
        # Far below the noise: RadioLib reports total + SNR, noise is about total
        self.assertAlmostEqual(aprs.noise_estimate(-130, -15.0), -115.14, places=2)
        # Equal signal and noise: each is 3 dB under the total
        self.assertAlmostEqual(aprs.noise_estimate(-100, 0.0), -103.01, places=2)


if __name__ == "__main__":
    unittest.main()
