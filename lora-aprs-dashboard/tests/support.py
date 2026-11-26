import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parent / "app"
sys.path.insert(0, str(APP))
sys.path.insert(0, str(HERE))

FIXTURES = json.loads((HERE / "fixtures" / "samples.json").read_text())
SAMPLES = FIXTURES["samples"]


def syslog(name):
    return SAMPLES[name]["syslog"].encode("latin-1")


def mqtt(name):
    """(last topic level, payload bytes)"""
    s = SAMPLES[name]
    return s["mqtt_topic"].rsplit("/", 1)[1], s["mqtt_payload"].encode("latin-1")
