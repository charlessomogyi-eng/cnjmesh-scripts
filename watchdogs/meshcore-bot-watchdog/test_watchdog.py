#!/usr/bin/env python3
"""Offline tests for meshcore-bot-watchdog. No Pi, no Discord, no radio needed.

Run:  python3 test_watchdog.py     (finishes on its own)
"""
import os
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

TMP = tempfile.mkdtemp()
os.environ["STATE_FILE"] = os.path.join(TMP, "state.json")
os.environ["PAUSE_FILE"] = os.path.join(TMP, "paused")
os.environ["MESHCORE_DEVICE"] = os.path.join(TMP, "kpc1")
os.environ["RECOVER_SETTLE_SECONDS"] = "0"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import watchdog as w  # noqa: E402

NOW = 1793200000.0


def reset():
    for p in (w.PAUSE_FILE, w.DEVICE, w.STATE_FILE):
        if os.path.exists(p):
            os.remove(p)


def device_present():
    open(w.DEVICE, "w").close()


class Send(unittest.TestCase):
    def test_sends_user_agent_header(self):
        with mock.patch.object(w, "DISCORD_WEBHOOK_URL", "https://example.invalid/hook"), \
                mock.patch("urllib.request.urlopen") as uo:
            self.assertTrue(w.send_discord("hi"))
            req = uo.call_args[0][0]
            self.assertTrue(req.get_header("User-agent"))  # the Nov 2026 403 was a missing UA

    def test_403_returns_false(self):
        err = urllib.error.HTTPError("u", 403, "Forbidden", {}, None)
        with mock.patch.object(w, "DISCORD_WEBHOOK_URL", "https://example.invalid/hook"), \
                mock.patch("urllib.request.urlopen", side_effect=err):
            self.assertFalse(w.send_discord("hi"))

    def test_placeholder_webhook_returns_false(self):
        with mock.patch.object(w, "DISCORD_WEBHOOK_URL", "REPLACE_ME"):
            self.assertFalse(w.send_discord("hi"))


class Caps(unittest.TestCase):
    def setUp(self):
        reset()

    def test_first_allowed(self):
        self.assertEqual(w.recovery_allowed(w.default_state(), NOW), (True, ""))

    def test_repeat_inside_hour_blocked(self):
        s = w.default_state()
        s["recoveries"] = [NOW - 600]
        self.assertFalse(w.recovery_allowed(s, NOW)[0])

    def test_third_in_24h_blocked(self):
        s = w.default_state()
        s["recoveries"] = [NOW - 5 * 3600, NOW - 2 * 3600]
        ok, why = w.recovery_allowed(s, NOW)
        self.assertFalse(ok)
        self.assertIn("2 times in 24 h", why)

    def test_pause_file(self):
        open(w.PAUSE_FILE, "w").close()
        self.assertIn("paused", w.recovery_allowed(w.default_state(), NOW)[1])

    def test_switch_off(self):
        with mock.patch.object(w, "AUTO_RECOVER", False):
            self.assertIn("AUTO_RECOVER=0", w.recovery_allowed(w.default_state(), NOW)[1])


class Main(unittest.TestCase):
    def setUp(self):
        reset()
        self.sent = []
        self.ok_post = True

        def fake_send(msg):
            self.sent.append(msg)
            return self.ok_post

        self.patches = [
            mock.patch.object(w, "send_discord", side_effect=fake_send),
            mock.patch.object(w.time, "time", return_value=NOW),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])

    def run_main(self, states, restart=(True, "")):
        """states: successive systemctl is-active results (first = initial check)."""
        seq = iter(states)
        with mock.patch.object(w, "service_state", side_effect=lambda *a: next(seq)), \
                mock.patch.object(w, "restart_service", return_value=restart) as rs:
            w.main()
        return rs

    def state(self):
        return w.load_state()

    def test_failed_with_device_restarts_and_reports(self):
        device_present()
        rs = self.run_main(["failed"])
        rs.assert_called_once()
        self.assertIn("restarted it automatically", self.sent[0])
        self.assertEqual(self.state()["recoveries"], [NOW])

    def test_inactive_also_restarts(self):
        device_present()
        self.run_main(["inactive"]).assert_called_once()

    def test_activating_is_left_alone(self):
        device_present()
        rs = self.run_main(["activating"])
        rs.assert_not_called()
        self.assertEqual(self.sent, [])

    def test_device_missing_alerts_once_no_restart(self):
        rs = self.run_main(["failed"])
        rs.assert_not_called()
        self.assertIn("is missing", self.sent[0])
        self.run_main(["failed"])  # same instant: reminder not due
        self.assertEqual(len(self.sent), 1)

    def test_discord_failure_is_retried_next_run(self):
        self.ok_post = False
        self.run_main(["failed"])
        self.assertIsNone(self.state()["device_alerted_at"])  # not saved as sent
        self.run_main(["failed"])
        self.assertEqual(len(self.sent), 2)

    def test_repeat_failure_inside_hour_alerts_and_leaves_alone(self):
        device_present()
        s = w.default_state()
        s["recoveries"] = [NOW - 600]
        w.save_state(s)
        rs = self.run_main(["failed"])
        rs.assert_not_called()
        self.assertIn("did not restart it", self.sent[0])

    def test_pause_leaves_alone(self):
        device_present()
        open(w.PAUSE_FILE, "w").close()
        rs = self.run_main(["failed"])
        rs.assert_not_called()
        self.assertIn("paused", self.sent[0])

    def test_restart_that_fails_asks_for_help(self):
        device_present()
        rs = self.run_main(["failed"], restart=(False, "it stopped again within a minute"))
        rs.assert_called_once()
        self.assertIn("Needs you", self.sent[0])

    def test_back_up_message_only_after_an_alert(self):
        self.run_main(["active"])
        self.assertEqual(self.sent, [])
        s = w.default_state()
        s["down_alerted_at"] = NOW - 3600
        w.save_state(s)
        self.run_main(["active"])
        self.assertIn("back up", self.sent[0])
        self.assertIsNone(self.state()["down_alerted_at"])

    def test_old_format_state_file_is_accepted(self):
        with open(w.STATE_FILE, "w") as f:
            f.write('{"service_state": "active", "last_alert": 1794438676.7}')
        self.run_main(["active"])
        self.assertEqual(self.sent, [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
