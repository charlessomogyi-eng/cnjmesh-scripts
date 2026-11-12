#!/usr/bin/env python3
"""Offline tests for meshcore-bot-watchdog. No Pi, no Discord, no radio needed.

Run:  python3 test_watchdog.py     (finishes on its own)
"""
import os
import sys
import tempfile
import time
import unittest
import urllib.error
from unittest import mock

TMP = tempfile.mkdtemp()
os.environ["STATE_FILE"] = os.path.join(TMP, "state.json")
os.environ["PAUSE_FILE"] = os.path.join(TMP, "paused")
os.environ["MESHCORE_DEVICE"] = os.path.join(TMP, "kpc1")
os.environ["MESHCORE_LOG"] = os.path.join(TMP, "meshcore_bot.log")
os.environ["RECOVER_SETTLE_SECONDS"] = "0"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import watchdog as w  # noqa: E402

NOW = 1793200000.0


def reset():
    for p in (w.PAUSE_FILE, w.DEVICE, w.STATE_FILE, w.LOG_FILE, w.LOG_FILE + ".1"):
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
            mock.patch.object(w, "check_forecast"),  # covered by class Forecast below
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


def at(hour, minute, day=12):
    """Epoch seconds for local Nov <day> 2026 at hour:minute (the check works in local time)."""
    return time.mktime((2026, 11, day, hour, minute, 0, 0, 0, -1))


# The real log lines are wrapped in terminal colour codes (green INFO), which is what broke the first version
# of this check on Nov 12 2026: the line starts with "\x1b[32m", not with the date.
GREEN, RESET = "\x1b[32m", "\x1b[0m"
SENT_LINES = (
    GREEN + "2026-11-12 07:05:00 - MeshCoreBot - INFO - \U0001F4C5 Sending daily weather forecast at 07:05:00" + RESET + "\n"
    + GREEN + "2026-11-12 07:05:00 - MeshCoreBot - INFO - \u2705 Channel message sent to CentralNJ-MC (channel 2)" + RESET + "\n"
    + GREEN + "2026-11-12 07:05:12 - MeshCoreBot - INFO - Daily weather forecast sent to CentralNJ-MC" + RESET + "\n"
)
PLAIN_SENT = SENT_LINES.replace(GREEN, "").replace(RESET, "")
STARTED_LINES = SENT_LINES.rsplit(GREEN + "2026-11-12 07:05:12", 1)[0]


def write_log(text, path=None):
    with open(path or w.LOG_FILE, "w", encoding="utf-8") as f:
        f.write(text)


class Forecast(unittest.TestCase):
    def setUp(self):
        reset()
        self.sent = []
        self.ok_post = True

        def fake_send(msg):
            self.sent.append(msg)
            return self.ok_post

        p = mock.patch.object(w, "send_discord", side_effect=fake_send)
        p.start()
        self.addCleanup(p.stop)

    def check(self, state, now, st="active"):
        w.check_forecast("cnjmesh1", state, st, now)

    def test_sent_line_today_is_quiet_and_remembered(self):
        write_log(SENT_LINES)
        s = w.default_state()
        self.check(s, at(8, 0))
        self.assertEqual(self.sent, [])
        self.assertEqual(s["forecast_ok_date"], "2026-11-12")

    def test_uncoloured_log_lines_work_too(self):
        write_log(PLAIN_SENT)
        s = w.default_state()
        self.check(s, at(8, 0))
        self.assertEqual(s["forecast_ok_date"], "2026-11-12")

    def test_remembered_day_does_not_read_the_log_again(self):
        s = w.default_state()
        s["forecast_ok_date"] = "2026-11-12"
        with mock.patch.object(w, "forecast_status") as fs:
            self.check(s, at(9, 0))
        fs.assert_not_called()

    def test_silent_before_the_deadline(self):
        write_log("")
        self.check(w.default_state(), at(7, 20))
        self.assertEqual(self.sent, [])

    def test_missing_after_deadline_alerts_once(self):
        write_log("2026-11-12 06:00:00 - MeshCoreBot - INFO - something else\n")
        s = w.default_state()
        self.check(s, at(7, 45))
        self.assertEqual(len(self.sent), 1)
        self.assertIn("did NOT go out", self.sent[0])
        self.assertEqual(s["forecast_alerted_date"], "2026-11-12")
        self.check(s, at(8, 0))  # next 15-minute run, same day
        self.assertEqual(len(self.sent), 1)

    def test_started_but_never_finished_is_reported_as_such(self):
        write_log(STARTED_LINES)
        self.check(w.default_state(), at(7, 45))
        self.assertIn("STARTED but never finished", self.sent[0])

    def test_yesterdays_forecast_does_not_count(self):
        write_log(SENT_LINES.replace("2026-11-12", "2026-11-11"))
        self.check(w.default_state(), at(7, 45))
        self.assertIn("did NOT go out", self.sent[0])

    def test_new_day_alerts_again(self):
        s = w.default_state()
        s["forecast_alerted_date"] = "2026-11-12"
        write_log("")
        self.check(s, at(7, 45, day=13))
        self.assertEqual(len(self.sent), 1)

    def test_rotated_file_still_counts(self):
        write_log("2026-11-12 07:40:00 - MeshCoreBot - INFO - new file after rotation\n")
        write_log(SENT_LINES, w.LOG_FILE + ".1")
        self.check(w.default_state(), at(8, 0))
        self.assertEqual(self.sent, [])

    def test_missing_log_says_it_cannot_check(self):
        s = w.default_state()
        self.check(s, at(7, 45))
        self.assertIn("could not read", self.sent[0])
        self.assertEqual(s["forecast_alerted_date"], "2026-11-12")

    def test_discord_failure_is_retried_next_run(self):
        write_log("")
        s = w.default_state()
        self.ok_post = False
        self.check(s, at(7, 45))
        self.assertIsNone(s["forecast_alerted_date"])
        self.check(s, at(8, 0))
        self.assertEqual(len(self.sent), 2)

    def test_message_names_the_bot_state(self):
        write_log("")
        self.check(w.default_state(), at(7, 45), st="failed")
        self.assertIn("meshcore-bot is failed", self.sent[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
