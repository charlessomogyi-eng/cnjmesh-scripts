import socket
import unittest

import support  # noqa: F401  (puts app/ on the path)
from dashboard import is_local, open_syslog_socket, settings


class Forwarding(unittest.TestCase):
    def cfg(self, forward, port=15140):
        return settings({"SYSLOG_BIND": "127.0.0.1", "SYSLOG_PORT": str(port),
                         "SYSLOG_FORWARD": forward})

    def test_local_addresses(self):
        self.assertTrue(is_local("127.0.0.1"))
        self.assertTrue(is_local("localhost"))
        self.assertFalse(is_local("192.0.2.1"))      # documentation range
        self.assertFalse(is_local("no-such-host.invalid"))

    def test_loop_to_own_port_is_refused(self):
        own = socket.gethostbyname(socket.gethostname())
        for target in ("127.0.0.1:15140", "localhost:15140", own + ":15140"):
            with self.subTest(target), self.assertRaises(ValueError):
                open_syslog_socket(self.cfg(target))

    def test_other_port_or_host_is_allowed(self):
        for target in ("127.0.0.1:15150", "192.0.2.1:15140"):
            with self.subTest(target):
                open_syslog_socket(self.cfg(target)).close()

    def test_bad_target(self):
        with self.assertRaises(ValueError):
            self.cfg("just-a-host")


if __name__ == "__main__":
    unittest.main()
