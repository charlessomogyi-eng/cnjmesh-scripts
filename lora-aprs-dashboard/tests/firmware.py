"""Python side of the C++ harness (tests/harness)."""
import subprocess
from pathlib import Path

BINARY = Path(__file__).resolve().parent / "harness" / "build" / "harness"
HEADER = b"<\xff\x01"
OWN = ("K2GIA-10", "40.0", "-74.5")     # round numbers, not a real station position


def run(cases):
    """cases: [(op, rssi, snr, freq_err, bytes)] -> [(syslog, topic, payload, digi)]."""
    text = "".join("%s %d %s %d %s\n" % (op, rssi, snr, ferr, data.hex())
                   for op, rssi, snr, ferr, data in cases)
    out = subprocess.run([str(BINARY), *OWN], input=text.encode(),
                         capture_output=True, check=True).stdout.decode().split()
    values = [None if v == "-" else bytes.fromhex(v) for v in out]
    assert len(values) == 4 * len(cases), "harness output does not line up"
    return [tuple(values[i:i + 4]) for i in range(0, len(values), 4)]
