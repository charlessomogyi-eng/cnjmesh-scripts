#!/usr/bin/env python3
"""Offline test: outgoing messages go to Discord only after Graywolf has sent them.

Run:  python3 test_bridge_poll.py     (finishes on its own; needs aiohttp installed, like the bridge)
"""
import importlib.util, os, sqlite3, sys, types, unittest

sys.modules.setdefault("aiohttp", types.ModuleType("aiohttp"))  # the bridge imports it; these tests do not need it

spec = importlib.util.spec_from_file_location("bridge", os.path.join(os.path.dirname(os.path.abspath(__file__)), "graywolf-discord-bridge.py"))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

# Column order copied from the live Graywolf database (Nov 8 2026, `SELECT *` header).
COLS = ("id direction our_call peer_call from_call to_call text msg_id created_at updated_at received_at sent_at "
        "acked_at ack_state source channel path via raw_tnc2 unread attempts next_retry_at failure_reason reply_ack_id "
        "is_ack is_rej is_bulletin is_nws prefer_is deleted_at thread_kind thread_key received_by_call kind "
        "invite_tactical invite_accepted_at").split()
SCHEMA = "CREATE TABLE messages (id INTEGER PRIMARY KEY, " + ", ".join(
    c + (" INTEGER DEFAULT 0" if c in ("is_ack", "is_rej") else "") for c in COLS[1:]) + ")"

class Poll(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(":memory:"); self.c.row_factory = sqlite3.Row; self.c.execute(SCHEMA)

    def add(self, direction, sent_at=None, **kw):
        cur = self.c.execute("INSERT INTO messages (direction, from_call, to_call, text, sent_at, source, path, is_ack) VALUES (?,?,?,?,?,?,?,?)",
                             (direction, "K2GIA-1", "K2GIA-7", "Test to K2GIA-7", sent_at, kw.get("source", ""), "", kw.get("is_ack", 0)))
        return cur.lastrowid

    def test_outgoing_waits_for_sent_at_then_posts_once(self):
        mid = self.add("out")
        ready, last, pending = b.select_ready(self.c, 0, {})
        self.assertEqual(ready, []); self.assertIn(mid, pending)       # queued, not sent: nothing posted
        ready, last, pending = b.select_ready(self.c, last, pending)
        self.assertEqual(ready, [])                                    # still waiting
        self.c.execute("UPDATE messages SET sent_at='2026-11-08 23:18:04' WHERE id=?", (mid,))
        ready, last, pending = b.select_ready(self.c, last, pending)
        self.assertEqual([r["id"] for r in ready], [mid]); self.assertEqual(pending, {})
        ready, last, pending = b.select_ready(self.c, last, pending)
        self.assertEqual(ready, [])                                    # never posted twice

    def test_outgoing_already_sent_posts_immediately(self):
        mid = self.add("out", sent_at="2026-11-08 23:18:04")
        ready, _, pending = b.select_ready(self.c, 0, {})
        self.assertEqual([r["id"] for r in ready], [mid]); self.assertEqual(pending, {})

    def test_incoming_posts_immediately_and_in_id_order(self):
        a = self.add("in", source="rf"); o = self.add("out"); c = self.add("in", source="is")
        ready, last, pending = b.select_ready(self.c, 0, {})
        self.assertEqual([r["id"] for r in ready], [a, c]); self.assertIn(o, pending); self.assertEqual(last, c)

    def test_acks_are_ignored(self):
        self.add("out", is_ack=1)
        ready, _, pending = b.select_ready(self.c, 0, {})
        self.assertEqual(ready, []); self.assertEqual(pending, {})

    def test_never_sent_message_is_dropped_after_an_hour(self):
        mid = self.add("out")
        old = {mid: b.time.time() - b.PENDING_OUT_MAX_AGE - 5}
        ready, _, pending = b.select_ready(self.c, mid, old)
        self.assertEqual(ready, []); self.assertEqual(pending, {})

    def test_discord_text_is_built_from_the_right_columns(self):
        mid = self.add("out", sent_at="2026-11-08 23:18:04")
        row = self.c.execute("SELECT * FROM messages WHERE id=?", (mid,)).fetchone()
        payload, channel = b.format_db_message(row)
        self.assertEqual(channel, "rf")
        self.assertIn("**From:** K2GIA-1", payload["content"])
        self.assertIn("**To:** K2GIA-7", payload["content"])
        self.assertIn("Test to K2GIA-7", payload["content"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
