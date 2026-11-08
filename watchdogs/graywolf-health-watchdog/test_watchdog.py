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


UNKEY_EPROTO = "graywolf-modem: TransmitFrame: ptt_unkey: TIOCMGET: EPROTO: Protocol error"
KEY_EPROTO = "graywolf-modem: TransmitFrame: ptt_key: TIOCMGET: EPROTO: Protocol error"


class StuckTransmitter(unittest.TestCase):
    """The Oct 31 2026 event: ptt_unkey failed and the radio stayed keyed."""

    def test_unkey_error_is_its_own_problem(self):
        f = w.analyze(events((NOW - 3000, READY), (NOW - 600, BEACON), (NOW - 598, UNKEY_EPROTO)), NOW)
        self.assertEqual(f["ptt_unkey_error_count"], 1)
        self.assertEqual(f["ptt_unkey_errno"], "EPROTO")
        probs = w.problems_from(True, f, NOW)
        self.assertIn("ptt-unkey-error", probs)
        self.assertNotIn("ptt-error", probs)

    def test_any_errno_on_ptt_key_counts_as_ptt_error(self):
        f = w.analyze(events((NOW - 3000, READY), (NOW - 600, KEY_EPROTO)), NOW)
        self.assertEqual(w.problems_from(True, f, NOW), ["ptt-error"])

    def test_unkey_error_before_restart_is_history(self):
        f = w.analyze(events((NOW - 5000, UNKEY_EPROTO), (NOW - 3000, READY), (NOW - 600, BEACON)), NOW)
        self.assertEqual(w.problems_from(True, f, NOW), [])

    def test_guard_match(self):
        self.assertEqual(w.guard_match(UNKEY_EPROTO), "EPROTO")
        self.assertEqual(w.guard_match("graywolf-modem: TransmitFrame: ptt_unkey: TIOCMGET: EIO: I/O error"), "EIO")
        self.assertIsNone(w.guard_match("graywolf-modem: TransmitFrame: ptt_key: TIOCMGET: EIO: I/O error"))
        self.assertIsNone(w.guard_match(BEACON))


RESUME = ("sudo systemctl start graywolf.service graywolf-discord.service "
          "graywolf-watchdog.timer graywolf-discord-watchdog.timer")


class EmergencyPath(Harness):
    def setUp(self):
        super().setUp()
        self._saved = (w.stop_graywolf, w.find_digirig_hub, w.soft_reset_hub, w.pause_timers, w.run)
        # Never touch real units, even if these tests are run on cnjmesh1 itself.
        self.pauses = []
        w.pause_timers = lambda: self.pauses.append(1) or [(u, True) for u in w.PAUSE_TIMERS]
        w.run = lambda cmd, timeout=30: (1, "blocked by test")

    def tearDown(self):
        (w.stop_graywolf, w.find_digirig_hub, w.soft_reset_hub, w.pause_timers, w.run) = self._saved

    def test_periodic_check_stops_graywolf_once_and_never_restarts(self):
        stops = []
        w.stop_graywolf = lambda: stops.append(1) or True
        w.find_digirig_hub = lambda: None
        self.ev = events((NOW - 3000, READY), (NOW - 600, BEACON), (NOW - 598, UNKEY_EPROTO))
        self.run_main()
        self.assertEqual(len(stops), 1)
        self.assertEqual(len(self.pauses), 1)           # the older timers are paused too
        self.assertEqual(self.fixes, 0)                 # no automatic restart
        self.assertEqual(len(self.sent), 1)
        self.assertIn("stuck transmitting", self.sent[0])
        self.assertIn("TX light", self.sent[0])
        # graywolf is now stopped, so later runs stay quiet
        w.service_active = lambda: False
        self.run_main()
        self.assertEqual(len(self.sent), 1)

    def test_emergency_stop_resets_hub_when_found(self):
        w.stop_graywolf = lambda: True
        w.find_digirig_hub = lambda: "1-1.3"
        resets = []
        w.soft_reset_hub = lambda hub: resets.append(hub) or True
        w.emergency_stop("cnjmesh1", "EPROTO", "test")
        self.assertEqual(resets, ["1-1.3"])
        self.assertIn("reset the Digirig USB hub 1-1.3", self.sent[0])

    def test_alert_gives_exactly_one_resume_command(self):
        w.stop_graywolf = lambda: True
        w.find_digirig_hub = lambda: None
        w.emergency_stop("cnjmesh1", "EPROTO", "test")
        msg = self.sent[0]
        self.assertEqual(msg.count("sudo systemctl start"), 1)
        self.assertIn(f"`{RESUME}`", msg)
        self.assertIn("paused graywolf-watchdog.timer, graywolf-discord-watchdog.timer", msg)
        self.assertNotIn("systemctl restart", msg)

    def test_order_is_stop_then_pause_then_hub_reset(self):
        order = []
        w.stop_graywolf = lambda: order.append("stop") or True
        w.pause_timers = lambda: order.append("pause") or [(u, True) for u in w.PAUSE_TIMERS]
        w.find_digirig_hub = lambda: "1-1.3"
        w.soft_reset_hub = lambda hub: order.append("reset") or True
        w.emergency_stop("cnjmesh1", "EPROTO", "test")
        self.assertEqual(order, ["stop", "pause", "reset"])

    def test_failed_pause_is_reported_loudly(self):
        w.stop_graywolf = lambda: True
        w.find_digirig_hub = lambda: None
        w.pause_timers = lambda: [("graywolf-watchdog.timer", True), ("graywolf-discord-watchdog.timer", False)]
        w.emergency_stop("cnjmesh1", "EPROTO", "test")
        self.assertIn("could NOT pause graywolf-discord-watchdog.timer", self.sent[0])
        self.assertIn("stop it by hand", self.sent[0])


class PauseTimers(unittest.TestCase):
    def setUp(self):
        self._run, self._dry = w.run, w.DRY_RUN
        self.calls = []

    def tearDown(self):
        w.run, w.DRY_RUN = self._run, self._dry

    def test_stops_each_timer_with_systemctl_stop(self):
        w.DRY_RUN = False
        w.run = lambda cmd, timeout=30: self.calls.append(cmd) or (0, "")
        res = w.pause_timers()
        self.assertEqual(self.calls, [["systemctl", "stop", "graywolf-watchdog.timer"],
                                      ["systemctl", "stop", "graywolf-discord-watchdog.timer"]])
        self.assertEqual(res, [("graywolf-watchdog.timer", True), ("graywolf-discord-watchdog.timer", True)])

    def test_failure_is_returned_not_raised(self):
        w.DRY_RUN = False
        w.run = lambda cmd, timeout=30: (5, "Unit not loaded.")
        self.assertTrue(all(not ok for _, ok in w.pause_timers()))

    def test_dry_run_touches_nothing(self):
        w.DRY_RUN = True
        w.run = lambda cmd, timeout=30: self.calls.append(cmd) or (0, "")
        w.pause_timers()
        self.assertEqual(self.calls, [])

    def test_resume_command_is_one_line_with_all_four_units(self):
        self.assertEqual(w.resume_command(), RESUME)
        self.assertNotIn("\n", w.resume_command())


class GuardedRecovery(unittest.TestCase):
    """Nov 8 2026: the guard restarts graywolf once, capped, instead of leaving it stopped."""

    def setUp(self):
        self._now = NOW
        self.sent = []
        self._send, self._time = w.send_discord, w.time.time
        w.send_discord = lambda m: self.sent.append(m)
        w.time.time = lambda: self._now
        self._saved = (w.run, w.wait_for_card, w.service_active, w.RECOVERY_FILE, w.AUTO_RECOVER,
                       w.RECOVER_WAIT_SECONDS, w.time.sleep, w.stop_graywolf, w.find_digirig_hub, w.pause_timers)
        w.RECOVERY_FILE = os.path.join(tempfile.mkdtemp(), "rec.json")
        w.AUTO_RECOVER = True
        w.time.sleep = lambda s: None
        self.cmds = []
        w.run = lambda cmd, timeout=30: self.cmds.append(cmd) or (0, "")
        w.wait_for_card = lambda seconds: self.card
        self.active = [False, True]   # stopped when checked first, active after the start
        w.service_active = lambda: self.active.pop(0) if self.active else True
        self.card = True

    def tearDown(self):
        (w.run, w.wait_for_card, w.service_active, w.RECOVERY_FILE, w.AUTO_RECOVER,
         w.RECOVER_WAIT_SECONDS, w.time.sleep, w.stop_graywolf, w.find_digirig_hub, w.pause_timers) = self._saved
        w.send_discord, w.time.time = self._send, self._time

    def test_first_fault_is_allowed_and_note_says_so(self):
        note, ok = w.recovery_note(NOW)
        self.assertTrue(ok)
        self.assertIn("started again automatically", note)

    def test_recovery_starts_all_four_units_once_and_counts_it(self):
        self.assertEqual(w.recover_graywolf("cnjmesh1"), "started")
        self.assertEqual(self.cmds, [["systemctl", "start", "graywolf.service", "graywolf-discord.service",
                                      "graywolf-watchdog.timer", "graywolf-discord-watchdog.timer"]])
        self.assertEqual(len(w.load_recoveries(self._now)), 1)
        self.assertIn("started again automatically", self.sent[0])

    def test_second_fault_within_the_hour_stays_stopped(self):
        w.recover_graywolf("cnjmesh1")
        ok, why = w.recovery_allowed(self._now + 600)
        self.assertFalse(ok)
        self.assertIn("less than an hour", why)
        note, allowed = w.recovery_note(self._now + 600)
        self.assertFalse(allowed)
        self.assertIn("stays stopped", note)

    def test_allowed_again_after_an_hour_but_capped_per_day(self):
        w.save_recoveries([self._now - 7200, self._now - 3700])
        ok, why = w.recovery_allowed(self._now)
        self.assertFalse(ok)
        self.assertIn("2 times in 24 h", why)
        w.save_recoveries([self._now - 7200])
        self.assertTrue(w.recovery_allowed(self._now)[0])
        w.save_recoveries([self._now - 90000])  # older than 24 h is forgotten
        self.assertEqual(w.load_recoveries(self._now), [])

    def test_missing_digirig_means_no_start(self):
        self.card = False
        self.assertEqual(w.recover_graywolf("cnjmesh1"), "digirig missing")
        self.assertEqual(self.cmds, [])
        self.assertEqual(len(self.sent), 1)
        self.assertIn(RESUME, self.sent[0])
        self.assertEqual(w.load_recoveries(self._now), [])

    def test_human_who_resumed_first_is_left_alone(self):
        self.active = [True]
        self.assertEqual(w.recover_graywolf("cnjmesh1"), "someone already started graywolf")
        self.assertEqual(self.cmds, [])
        self.assertEqual(self.sent, [])

    def test_switched_off_never_restarts(self):
        w.AUTO_RECOVER = False
        ok, why = w.recovery_allowed(NOW)
        self.assertFalse(ok)
        self.assertIn("switched off", why)

    def test_failed_start_is_reported(self):
        w.run = lambda cmd, timeout=30: (1, "boom")
        self.assertEqual(w.recover_graywolf("cnjmesh1"), "start failed")
        self.assertIn("FAILED", self.sent[0])
        self.assertIn(RESUME, self.sent[0])

    def test_corrupt_counter_file_means_zero_not_a_crash(self):
        with open(w.RECOVERY_FILE, "w") as f:
            f.write("not json")
        self.assertEqual(w.load_recoveries(NOW), [])

    def test_alert_with_recover_note_still_has_exactly_one_resume_command(self):
        w.stop_graywolf = lambda: True
        w.find_digirig_hub = lambda: None
        w.pause_timers = lambda: [(u, True) for u in w.PAUSE_TIMERS]
        note, _ = w.recovery_note(self._now)
        w.emergency_stop("cnjmesh1", "EPROTO", "test", recover_note=note)
        msg = self.sent[0]
        self.assertEqual(msg.count("sudo systemctl start"), 1)
        self.assertIn("started again automatically", msg)
        self.assertNotIn("no automatic restart)", msg.split("To resume")[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
