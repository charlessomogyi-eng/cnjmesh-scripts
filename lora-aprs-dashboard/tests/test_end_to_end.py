"""Run the real program: UDP syslog in, a local test MQTT broker, HTTP out.
Skipped if mosquitto or paho-mqtt is not installed. Uses only 127.0.0.1."""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from support import APP, SAMPLES, syslog

MOSQUITTO = shutil.which("mosquitto") or (
    "/usr/sbin/mosquitto" if os.path.exists("/usr/sbin/mosquitto") else None)
try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


def free_port(kind=socket.SOCK_STREAM):
    with socket.socket(socket.AF_INET, kind) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for(check, seconds=10):
    end = time.time() + seconds
    while time.time() < end:
        try:
            value = check()
            if value:
                return value
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.1)
    raise AssertionError("timed out")


@unittest.skipUnless(MOSQUITTO and mqtt, "needs mosquitto and paho-mqtt")
class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        broker, self.udp, web = (free_port(), free_port(socket.SOCK_DGRAM),
                                 free_port())
        # Password protected like the real broker; throwaway test credentials.
        pw = d / "pw"
        subprocess.run(["mosquitto_passwd", "-b", "-c", str(pw), "tester",
                        "test-only"], check=True, capture_output=True)
        os.chmod(pw, 0o644)
        os.chmod(d, 0o755)
        (d / "m.conf").write_text(
            "listener %d 127.0.0.1\nallow_anonymous false\npassword_file %s\n"
            "log_dest file %s\nlog_type all\n" % (broker, pw, d / "m.log"))
        (d / "m.log").touch()
        os.chmod(d / "m.log", 0o666)
        self.log = d / "m.log"
        self.procs = [subprocess.Popen([MOSQUITTO, "-c", str(d / "m.conf")],
                                       stderr=subprocess.DEVNULL)]
        wait_for(lambda: socket.create_connection(("127.0.0.1", broker), 1).close() or True)

        self.forwarded = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.forwarded.bind(("127.0.0.1", 0))
        self.forwarded.settimeout(5)
        env = dict(os.environ, SYSLOG_BIND="127.0.0.1",
                   SYSLOG_PORT=str(self.udp), SYSLOG_ALLOW="127.0.0.1",
                   SYSLOG_FORWARD="127.0.0.1:%d" % self.forwarded.getsockname()[1],
                   MQTT_HOST="127.0.0.1", MQTT_PORT=str(broker),
                   MQTT_USER="tester", MQTT_PASSWORD="test-only",
                   HTTP_BIND="127.0.0.1", HTTP_PORT=str(web),
                   DB_PATH=str(d / "e2e.db"))
        self.app = subprocess.Popen([sys.executable, str(APP / "dashboard.py")],
                                    env=env, stderr=subprocess.PIPE, text=True)
        self.procs.append(self.app)
        self.url = "http://127.0.0.1:%d/" % web
        wait_for(lambda: self.get("api/summary")["status"]["mqtt_connected"])
        wait_for(lambda: "aprs-k2gia-10/#" in self.log.read_text())

        if hasattr(mqtt, "CallbackAPIVersion"):
            self.pub = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                   client_id="fake-igate")
        else:
            self.pub = mqtt.Client(client_id="fake-igate")
        self.pub.username_pw_set("tester", "test-only")
        self.pub.connect("127.0.0.1", broker)
        self.pub.loop_start()

    def tearDown(self):
        self.pub.loop_stop()
        self.forwarded.close()
        for p in reversed(self.procs):
            p.terminate()
            p.wait(10)
        if self.app.stderr:
            self.app.stderr.close()
        self.tmp.cleanup()

    def get(self, path):
        with urllib.request.urlopen(self.url + path, timeout=5) as r:
            body = r.read()
        return json.loads(body) if path.startswith("api") else body.decode()

    def test_whole_path(self):
        names = [n for n, s in SAMPLES.items() if n != "own_internet_beacon"]
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for name in names:
            s = SAMPLES[name]
            udp.sendto(syslog(name), ("127.0.0.1", self.udp))
            self.assertEqual(self.forwarded.recv(4096), syslog(name))
            if s["mqtt_payload"]:
                self.pub.publish(s["mqtt_topic"],
                                 s["mqtt_payload"].encode("latin-1")).wait_for_publish()
            time.sleep(0.08)
        udp.close()
        joined = sum(bool(SAMPLES[n]["mqtt_payload"]) for n in names)
        summary = wait_for(lambda: (
            lambda s: s if s["status"]["matched"] == joined else None)(
                self.get("api/summary")))
        packets = self.get("api/packets?limit=500")
        self.assertEqual(len(packets), len(names))
        self.assertEqual(summary["status"]["unparsed"], 0)
        self.assertEqual(summary["status"]["firmware"], "3.2.4")
        self.assertEqual(summary["windows"][0]["crc_errors"], 1)
        self.assertEqual(summary["windows"][0]["sent"], 3)
        self.assertTrue(any("café" in (p["info"] or "") for p in packets))
        self.assertIn("receive dashboard", self.get(""))
        with urllib.request.urlopen(self.url + "leaflet/leaflet.js", timeout=5) as r:
            self.assertGreater(len(r.read()), 100000)
        for bad in ("nothing", "../dashboard.py", "static/index.html",
                    "leaflet/LICENSE", "leaflet/../dashboard.py"):
            with self.assertRaises(urllib.error.HTTPError):
                self.get(bad)
        # The collector must never publish anything to the broker.
        self.assertNotIn("Received PUBLISH from lora-aprs-dash",
                         self.log.read_text())
        self.assertIn("Received PUBLISH from fake-igate", self.log.read_text())

    def test_busy_port_fails_loudly(self):
        env = dict(os.environ, SYSLOG_BIND="127.0.0.1",
                   SYSLOG_PORT=str(self.udp), HTTP_PORT="0",
                   DB_PATH=str(Path(self.tmp.name) / "second.db"))
        second = subprocess.run([sys.executable, str(APP / "dashboard.py")],
                                env=env, capture_output=True, text=True, timeout=20)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("Address already in use", second.stderr)


if __name__ == "__main__":
    unittest.main()
