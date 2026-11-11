#!/usr/bin/env python3
"""Offline tests for mesh-bot-watchdog auto-recovery. No Pi, no Discord, no CJG1 needed.

Run:  python3 test_watchdog.py     (finishes on its own)
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

TMP = tempfile.mkdtemp()
os.environ["STATE_FILE"] = os.path.join(TMP, "state.json")
os.environ["PAUSE_FILE"] = os.path.join(TMP, "paused")
os.environ["MESH_BOT_CONFIG"] = os.path.join(TMP, "config.ini")
os.environ["RECOVER_SETTLE_SECONDS"] = "0"
os.environ.pop("GATEWAY_HOST", None)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import watchdog as w  # noqa: E402

NOW = 1793200000.0


def fresh():
    s = w.default_state()
    return s


class Gateway(unittest.TestCase):
    def test_host_from_config(self):
        with open(w.CONFIG_FILE, "w") as f:
            f.write("[interface]\ntype = tcp\nhostname = 10.0.0.18\n")
        self.assertEqual(w.gateway_host(), "10.0.0.18")

    def test_host_with_port_and_comment(self):
        with open(w.CONFIG_FILE, "w") as f:
            f.write("hostname = 192.168.1.5:4403 # cjg1\n")
        self.assertEqual(w.gateway_host(), "192.168.1.5")

    def test_host_default_when_missing(self):
        if os.path.exists(w.CONFIG_FILE):
            os.remove(w.CONFIG_FILE)
        self.assertEqual(w.gateway_host(), w.GATEWAY_DEFAULT_HOST)

    def test_unreachable_is_false(self):
        with mock.patch("socket.create_connection", side_effect=OSError("no route")):
            self.assertFalse(w.gateway_reachable("10.0.0.18"))


class ErrorLoop(unittest.TestCase):
    def _journal(self, n):
        return (0, "\n".join(["Scheduler loop exception: 'NoneType' object has no attribute 'nodes'"] * n
                             + ["some other line"]))

    def test_loop_detected(self):
        with mock.patch.object(w, "run", return_value=self._journal(w.ERR_LOOP_MIN)):
            self.assertTrue(w.scheduler_error_loop())

    def test_a_few_lines_is_not_a_loop(self):
        with mock.patch.object(w, "run", return_value=self._journal(3)):
            self.assertFalse(w.scheduler_error_loop())

    def test_unreadable_journal_is_unknown(self):
        with mock.patch.object(w, "run", return_value=(1, "boom")):
            self.assertIsNone(w.scheduler_error_loop())


class Caps(unittest.TestCase):
    def setUp(self):
        if os.path.exists(w.PAUSE_FILE):
            os.remove(w.PAUSE_FILE)

    def test_first_restart_allowed(self):
        self.assertEqual(w.recovery_allowed(fresh(), NOW), (True, ""))

    def test_repeat_inside_an_hour_blocked(self):
        s = fresh()
        s["recoveries"] = [NOW - 600]
        ok, why = w.recovery_allowed(s, NOW)
        self.assertFalse(ok)
        self.assertIn("less than an hour", why)

    def test_second_after_an_hour_allowed_third_blocked(self):
        s = fresh()
        s["recoveries"] = [NOW - 2 * 3600]
        self.assertTrue(w.recovery_allowed(s, NOW)[0])
        s["recoveries"] = [NOW - 5 * 3600, NOW - 2 * 3600]
        ok, why = w.recovery_allowed(s, NOW)
        self.assertFalse(ok)
        self.assertIn("2 times in 24 h", why)

    def test_old_recoveries_expire(self):
        s = fresh()
        s["recoveries"] = [NOW - 30 * 3600, NOW - 26 * 3600]
        self.assertTrue(w.recovery_allowed(s, NOW)[0])

    def test_pause_file_blocks(self):
        open(w.PAUSE_FILE, "w").close()
        ok, why = w.recovery_allowed(fresh(), NOW)
        self.assertFalse(ok)
        self.assertIn("paused", why)

    def test_switch_off(self):
        with mock.patch.object(w, "AUTO_RECOVER", False):
            ok, why = w.recovery_allowed(fresh(), NOW)
        self.assertFalse(ok)
        self.assertIn("AUTO_RECOVER=0", why)


class TryRecover(unittest.TestCase):
    def setUp(self):
        if os.path.exists(w.PAUSE_FILE):
            os.remove(w.PAUSE_FILE)
        self.sent = []
        self.patches = [
            mock.patch.object(w, "send_discord", side_effect=lambda m: self.sent.append(m) or True),
            mock.patch.object(w, "save_state"),
            mock.patch.object(w, "gateway_host", return_value="10.0.0.18"),
        ]
        for p in self.patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patches])

    def test_gateway_down_alerts_once_and_does_not_restart(self):
        s = fresh()
        with mock.patch.object(w, "gateway_reachable", return_value=False), \
                mock.patch.object(w, "restart_service") as rs:
            self.assertFalse(w.try_recover(s, "cnjmesh1", NOW, "has been down"))
            self.assertFalse(w.try_recover(s, "cnjmesh1", NOW + 300, "has been down"))
            rs.assert_not_called()
        self.assertEqual(len(self.sent), 1)
        self.assertIn("did NOT restart", self.sent[0])
        self.assertEqual(s["recoveries"], [])

    def test_gateway_down_reminder_after_12_hours(self):
        s = fresh()
        with mock.patch.object(w, "gateway_reachable", return_value=False):
            w.try_recover(s, "cnjmesh1", NOW, "has been down")
            w.try_recover(s, "cnjmesh1", NOW + w.GATEWAY_REMINDER_SECONDS + 1, "has been down")
        self.assertEqual(len(self.sent), 2)

    def test_failed_discord_post_is_retried(self):
        s = fresh()
        with mock.patch.object(w, "send_discord", return_value=False) as sd, \
                mock.patch.object(w, "gateway_reachable", return_value=False):
            w.try_recover(s, "cnjmesh1", NOW, "has been down")
            self.assertIsNone(s["gw_down_alerted_at"])
            w.try_recover(s, "cnjmesh1", NOW + 300, "has been down")
            self.assertEqual(sd.call_count, 2)

    def test_gateway_up_restarts_and_reports(self):
        s = fresh()
        s["down_since"] = NOW - 3000
        with mock.patch.object(w, "gateway_reachable", return_value=True), \
                mock.patch.object(w, "restart_service", return_value=(True, "")) as rs:
            self.assertTrue(w.try_recover(s, "cnjmesh1", NOW, "has been down"))
            rs.assert_called_once()
        self.assertEqual(s["recoveries"], [NOW])
        self.assertIsNone(s["down_since"])
        self.assertIn("restarted it automatically", self.sent[0])

    def test_restart_that_does_not_stick_asks_for_help(self):
        s = fresh()
        with mock.patch.object(w, "gateway_reachable", return_value=True), \
                mock.patch.object(w, "restart_service", return_value=(False, "it stopped again within a minute")):
            self.assertFalse(w.try_recover(s, "cnjmesh1", NOW, "has been down"))
        self.assertIn("Needs you", self.sent[0])
        self.assertEqual(s["recoveries"], [NOW])  # counted, so it cannot loop

    def test_cap_hit_alerts_and_leaves_bot_alone(self):
        s = fresh()
        s["recoveries"] = [NOW - 600]
        with mock.patch.object(w, "gateway_reachable", return_value=True), \
                mock.patch.object(w, "restart_service") as rs:
            self.assertFalse(w.try_recover(s, "cnjmesh1", NOW, "has been down"))
            rs.assert_not_called()
        self.assertIn("did not restart it", self.sent[0])

    def test_paused_leaves_bot_alone(self):
        open(w.PAUSE_FILE, "w").close()
        s = fresh()
        with mock.patch.object(w, "gateway_reachable", return_value=True), \
                mock.patch.object(w, "restart_service") as rs:
            self.assertFalse(w.try_recover(s, "cnjmesh1", NOW, "has been down"))
            rs.assert_not_called()
        self.assertIn("paused", self.sent[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
