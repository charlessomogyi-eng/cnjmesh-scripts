"""Compare the Python port against the compiled firmware on many random packets.
Skipped unless tests/harness/build.sh has been run."""
import random
import unittest

from support import FIXTURES
import aprs
import firmware
import make_fixtures

CALLS = ["N0CALL-7", "N0CALL", "AB1CDE-15", "N0DIGI-10", "W1AW-1"]
PATHS = ["", ",WIDE1-1", ",WIDE1-1,WIDE2-1", ",N0DIGI-10*", ",N0DIGI-10*,WIDE2-1",
         ",WIDE2-2", ",A1BC-1,WIDE1*", ",N0DIGI-10*,WIDE1-1", ",RFONLY,NOGATE"]
STARTS = [":", "!", "=", "@", ">", "`", ";", "}", "_", "T#", "'", "/", "?"]
PIECES = ["4015.00N/07430.00W>", "092345z4015.00N/07430.00W>", "K2GIA-10 :",
          " / ", "-90dBm / 3.00dB / 5Hz", ":T#", "WIDE1-1", ":=/", "{12", "abc",
          " ", ">", ",", "::", "é"]


@unittest.skipUnless(firmware.BINARY.exists(), "harness not built")
class AgainstFirmware(unittest.TestCase):
    def test_committed_fixtures_are_current(self):
        self.assertEqual(make_fixtures.build(), FIXTURES)

    def test_random_packets(self):
        rng = random.Random(1)
        cases = []
        for _ in range(20000):
            info = rng.choice(STARTS) + "".join(
                rng.choice(PIECES) for _ in range(rng.randint(0, 5)))
            raw = "%s>APLRT1%s:%s" % (rng.choice(CALLS), rng.choice(PATHS), info)
            frame = firmware.HEADER + raw.encode("utf-8")[:250]
            cases.append(("rx", rng.randint(-140, -40),
                          rng.randint(-80, 48) / 4, rng.randint(-20000, 20000) or 1,
                          frame))
        for case, (line, topic, payload, _) in zip(cases, firmware.run(cases)):
            raw = case[4][3:]
            e = aprs.parse_syslog(line)
            self.assertIsNotNone(e, line)
            self.assertEqual((e["rssi"], e["snr"], e["freq_err"]), case[1:4], line)
            self.assertEqual(e["sender"], raw.split(b">")[0].decode(), line)
            if payload is not None:
                self.assertEqual(payload, raw)
                self.assertEqual(aprs.expected_content(raw.decode("latin-1")),
                                 e["content"], line)


if __name__ == "__main__":
    unittest.main()
