#!/usr/bin/env python3
"""Offline tests for graywolf-health-watchdog. No Pi, no Discord, no USB needed.

Run:  python3 test_watchdog.py     (finishes on its own)
"""
import os
import sys
import tempfile
import time
import unittest

os.environ["STATE_FILE"] = os.path.join(tempfile.mkdtemp(), "state.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import watchdog as w  # noqa: E402

NOW = 1793200000.0


def line(ts, msg):
    return f"{ts:.6f} cnjmesh1 graywolf[111]: {msg}"


BEACON = 'time=2026-10-28T17:50:42.456-04:00 level=INFO msg="beacon sent" component=beacon id=1'
EIO = "graywolf-modem: TransmitFrame: ptt_key: TIOCMGET: EIO: I/O error"
AUDIO_FAIL = "graywolf-modem: start_audio failed: input device not found: hw:CARD=Device,DEV=0"
READY = 'time=2026-10-28T18:33:39.522-04:00 level=INFO msg="modem ready" version=v0.13.13 pid=1'


def events(*pairs):
    return w.parse_journal("\n".join(line(ts, m) for ts, m in pairs))


class Analyze(unittest.TestCase):
    def test_healthy(self):
        ev = events((NOW - 3000, READY), (NOW - 600, BEACON))
        f = w.analyze(ev, NOW)
        self.assertEqual(w.problems_from(True, f, NOW), [])

    def test_ptt_eio_after_start_is_a_problem(self):
        ev = events((NOW - 3000, READY), (NOW - 600, BEACON), (NOW - 599, EIO))
        f = w.analyze(ev, NOW)
        self.assertEqual(w.problems_from(True, f, NOW), ["ptt-error"])

    def test_eio_before_restart_is_history(self):
        # the real Oct 28 situation after the 18:33 restart
        ev = events((NOW - 5000, BEACON), (NOW - 4999, EIO), (NOW - 3000, READY))
        f = w.analyze(ev, NOW)
        self.assertEqual(w.problems_from(True, f, NOW), [])

    def test_audio_failure_recent_vs_old(self):
        recent = w.analyze(events((NOW - 3000, READY), (NOW - 30, AUDIO_FAIL)), NOW)
        self.assertIn("audio-start-failed", w.problems_from(True, recent, NOW))
        old = w.analyze(events((NOW - 3000, READY), (NOW - 2000, AUDIO_FAIL)), NOW)
        self.assertNotIn("audio-start-failed", w.problems_from(True, old, NOW))

    def test_card_missing(self):
        f = w.analyze(events((NOW - 3000, READY), (NOW - 600, BEACON)), NOW)
        self.assertIn("audio-card-missing", w.problems_from(False, f, NOW))

    def test_no_beacon_only_after_uptime(self):
        fresh = w.analyze(events((NOW - 600, READY)), NOW)  # just restarted
        self.assertEqual(w.problems_from(True, fresh, NOW), [])
        stale = w.analyze(events((NOW - 9000, READY), (NOW - 4000, BEACON)), NOW)
        self.assertEqual(w.problems_from(True, stale, NOW), ["no-beacon"])


class Harness(unittest.TestCase):
    """Drive main() with fake system probes and capture Discord messages."""

    def setUp(self):
        if os.path.exists(w.STATE_FILE):
            os.remove(w.STATE_FILE)
        self.sent = []
        self.card = True
        self.ev = events((NOW - 3000, READY), (NOW - 600, BEACON))
        self.fix_result = (["restarted graywolf (ok)"], True)
        self.fixes = 0
        w.send_discord = lambda m: self.sent.append(m)
        w.service_active = lambda: True
        w.card_present = lambda: self.card
        w.read_journal = lambda: self.ev

        def fake_fix(problems, state, now):
            self.fixes += 1
            state["fix_attempts"].append(now)
            return self.fix_result
        w.attempt_fix = fake_fix
        self._now = NOW
        w.time.time = lambda: self._now  # main() reads the clock via time.time()

    def run_main(self, advance=300):
        self._now += advance
        w.main([])

    def test_healthy_is_silent(self):
        self.run_main()
        self.assertEqual(self.sent, [])

    def test_one_alert_per_incident_then_silence(self):
        self.card = False
        self.fix_result = (["could not locate hub"], False)
        for _ in range(6):  # six 5-minute runs of a persistent fault
            self.run_main()
        self.assertEqual(len(self.sent), 1)
        self.assertIn("Needs you", self.sent[0])
        self.assertEqual(self.fixes, 1)  # never keeps retrying

    def test_successful_fix_sends_single_quiet_notice(self):
        self.card = False
        self.run_main()  # problem found, fix "works"
        self.card = True
        for _ in range(4):
            self.run_main()
        self.assertEqual(len(self.sent), 1)
        self.assertIn("Automatic fix", self.sent[0])

    def test_problem_returns_after_fix_sends_second_message_then_silence(self):
        self.card = False
        self.run_main()                      # message 1 (fixed)
        self.card = True
        self.run_main()
        self.card = False
        for _ in range(5):                   # fault returns and stays
            self.run_main()
        self.assertEqual(len(self.sent), 2)
        self.assertIn("returned after an automatic fix", self.sent[1])
        self.assertEqual(self.fixes, 1)

    def test_recovery_notice_once_after_human_fix(self):
        self.card = False
        self.fix_result = (["could not locate hub"], False)
        self.run_main()
        self.run_main()
        self.card = True
        self.run_main()
        self.run_main()
        self.assertEqual(len(self.sent), 2)
        self.assertIn("healthy again", self.sent[1])

    def test_service_down_is_not_our_job(self):
        w.service_active = lambda: False
        self.card = False
        self.run_main()
        self.assertEqual(self.sent, [])

    def test_check_mode_never_acts(self):
        self.card = False
        self._now += 300
        w.main(["--check"])
        self.assertEqual(self.sent, [])
        self.assertEqual(self.fixes, 0)


class FixLimits(unittest.TestCase):
    def test_fix_rate_limits(self):
        st = w.default_state()
        ok, _ = w.fix_allowed(st, NOW)
        self.assertTrue(ok)
        st["fix_attempts"] = [NOW - 600]
        ok, why = w.fix_allowed(st, NOW)
        self.assertFalse(ok)
        st["fix_attempts"] = [NOW - 7200, NOW - 14400, NOW - 21600]
        ok, why = w.fix_allowed(st, NOW)
        self.assertFalse(ok)


class HubSafety(unittest.TestCase):
    def test_refuses_unknown_parent(self):
        calls = {}

        def fake_listdir(_):
            return ["1-1.3.1", "1-1.3", "1-1"]
        attrs = {
            ("1-1.3.1", "serial"): w.DIGIRIG_SERIAL, ("1-1.3.1", "idVendor"): "10c4",
            ("1-1.3", "idVendor"): "2109", ("1-1.3", "idProduct"): "3431",  # NOT the Digirig hub
        }
        orig_listdir, orig_sysfs = os.listdir, w._sysfs
        os.listdir = fake_listdir
        w._sysfs = lambda n, a: attrs.get((n, a))
        try:
            self.assertIsNone(w.find_digirig_hub())
            attrs[("1-1.3", "idVendor")], attrs[("1-1.3", "idProduct")] = "0424", "2412"
            self.assertEqual(w.find_digirig_hub(), "1-1.3")
        finally:
            os.listdir, w._sysfs = orig_listdir, orig_sysfs


if __name__ == "__main__":
    unittest.main(verbosity=2)
