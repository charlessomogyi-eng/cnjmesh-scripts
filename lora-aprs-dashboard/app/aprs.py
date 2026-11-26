"""Parsing for the two feeds a CA2RXU LoRa APRS iGate (3.2.4) provides.

Everything here follows the firmware source (tag V3.2.4):
  src/syslog_utils.cpp  format of the UDP syslog lines
  src/mqtt_utils.cpp    MQTT topic and payload
  src/lora_utils.cpp    what gets logged, and when
  src/digi_utils.cpp    how a digipeater marks the path

Packet text is held as latin-1 strings so that every byte survives unchanged.
Use show() before putting any of it in front of a person.
"""
import math
import re

LORA_HEADER = "<\xff\x01"          # 0x3C 0xFF 0x01, in front of every on-air frame
TESTED_FIRMWARE = "3.2.4"

_SYSLOG = re.compile(
    r"^<\d+>1 - (\S+) CA2RXU_LoRa_iGate_(\S+) - - - (.*)\Z", re.S)
# The firmware builds this in a 35 byte buffer, so a very long one loses its tail.
_SIGNAL = r" / (-?\d+)dBm / (-?\d+\.\d+)dB / (-?\d+)(?:Hz?)?"
# Position lines carry the distance text after the signal figures.
_SIGNAL_POSITION = re.compile(
    _SIGNAL + r"(?= / (?: _ / _ / _ |-?\d+\.\d+N / ))")
_SIGNAL_LAST = re.compile(_SIGNAL + r"\Z")
_POSITION = re.compile(
    r"^ / (-?\d+\.\d+)N / (-?\d+\.\d+)E / (\d+\.\d+)km(?: / (.*))?\Z", re.S)
_CALL = re.compile(r"^[A-Za-z0-9]{1,7}(?:-[A-Za-z0-9]{1,2})?\Z")
_ALIAS = re.compile(
    r"^(?:WIDE\d*(?:-\d+)?|TRACE\d*(?:-\d+)?|RELAY|TCPIP|TCPXX|NOGATE|RFONLY|qA.)\Z",
    re.I)
_TAGGED = ("MESSAGE", "STATUS", "MIC-E", "OBJECT", "TELEMETRY")


def show(text):
    """Latin-1 held bytes -> readable text."""
    if text is None:
        return None
    return text.encode("latin-1", "replace").decode("utf-8", "replace")


def is_callsign(text):
    return bool(text) and bool(_CALL.match(text))


def split_tnc2(raw):
    """'SRC>TOCALL,PATH:info' -> (sender, 'TOCALL,PATH', info), or None."""
    gt = raw.find(">")
    colon = raw.find(":", gt + 1)
    if gt <= 0 or colon < 0:
        return None
    sender = raw[:gt]
    if not is_callsign(sender):
        return None
    return sender, raw[gt + 1:colon], raw[colon + 1:]


def transmitter(sender, header):
    """Who put this packet on the air, judged from the path.

    header is 'TOCALL,P1,P2*,...'. Returns (via, callsign):
      ('direct', sender)   no hop is marked as used
      ('digi', call)       the last used hop is a named station
      ('relayed', None)    something relayed it but did not name itself
    """
    hops = header.split(",")[1:]
    used = [i for i, hop in enumerate(hops) if hop.endswith("*")]
    if not used:
        return "direct", sender
    for i in range(used[-1], -1, -1):
        call = hops[i].rstrip("*")
        if not _ALIAS.match(call) and is_callsign(call):
            return "digi", call
    return "relayed", None


def expected_content(raw):
    """The text between 'RX / ' and the signal figures that the firmware logs
    for a received packet. raw is the MQTT payload (no LoRa header).

    This mirrors SYSLOG_Utils::log case 1, quirks included, and is checked
    against the compiled firmware code in tests/test_firmware.py.
    """
    packet = LORA_HEADER + raw
    colon = packet.find(":")
    nxt = packet[colon + 1:colon + 2]
    gt = packet.find(">")
    sender = packet[3:gt] if gt >= 3 else None
    if sender is None:
        return None
    tail = packet[colon + 2:]
    if nxt == ":":
        return "MESSAGE / %s ---> %s" % (sender, tail)
    if nxt in ("!", "=", "@"):
        if packet.find("WIDE1-1") > 10:
            comma = packet.find(",")
            if comma < 0:       # the firmware then logs the rest of the packet
                comma = len(packet)
            return "GPS / %s / %s / WIDE1-1" % (sender, packet[gt + 1:comma])
        return "GPS / %s / %s / -" % (sender, packet[gt + 1:colon])
    if nxt == ">":
        return "STATUS / %s ---> %s" % (sender, tail)
    if nxt == "`":
        return "MIC-E / %s ---> %s" % (sender, tail)
    if nxt == ";":
        return "OBJECT / %s ---> %s" % (sender, tail)
    tele = packet.find(":T#")
    if tele >= 10 and packet.find(":=/") == -1:
        return "TELEMETRY / %s ---> %s" % (sender, packet[tele + 3:])
    return packet


def parse_syslog(datagram):
    """One UDP datagram -> dict, or None if it is not an iGate line we use.

    kind is 'rx', 'crc', 'tx' or 'other'.
    """
    m = _SYSLOG.match(datagram.decode("latin-1"))
    if not m:
        return None
    igate, firmware, body = m.groups()
    event = {"igate": igate, "firmware": firmware, "kind": "other"}

    if body.startswith("RX / "):
        rest = body[5:]
        is_position = rest.startswith("GPS / ")
        sig = (_SIGNAL_POSITION if is_position else _SIGNAL_LAST).search(rest)
        if not sig:
            return None
        content = rest[:sig.start()]
        event.update(kind="rx", content=content, rssi=int(sig.group(1)),
                     snr=float(sig.group(2)), freq_err=int(sig.group(3)))
        _describe_rx(event, content)
        if is_position:
            pos = _POSITION.match(rest[sig.end():])
            if pos:
                event.update(lat=float(pos.group(1)), lon=float(pos.group(2)),
                             dist_km=float(pos.group(3)), comment=pos.group(4))
        return event if event.get("sender") else None

    if body.startswith("CRC / CRC-ERROR / "):
        sig = _SIGNAL_LAST.search(body)
        if not sig:
            return None
        event.update(kind="crc", rssi=int(sig.group(1)), snr=float(sig.group(2)),
                     freq_err=int(sig.group(3)))
        return event

    if body.startswith("TX / "):
        rest = body[5:]
        event.update(kind="tx", type="packet", raw=None, info=rest)
        if rest.startswith("RFONLY / "):
            event.update(raw=rest[9:], info=rest[9:])
        elif rest.startswith("MESSAGE / "):
            # 3.2.4 cuts the first three characters off the sender in this line
            # (it skips a LoRa header that transmit strings do not have).
            event.update(type="message", info=rest[10:])
        else:
            event.update(raw=rest)
        return event

    return event


def _describe_rx(event, content):
    """Fill sender, type, info, header (path) from the content of an RX line."""
    event.update(sender=None, header=None, raw=None, info=None, type="other")
    if content.startswith(LORA_HEADER):
        parts = split_tnc2(content[3:])
        if parts:
            sender, header, info = parts
            event.update(sender=sender, header=header, info=info,
                         raw=content[3:], type=packet_type(info))
        return
    if content.startswith("GPS / "):
        fields = content.split(" / ")
        if len(fields) >= 4 and is_callsign(fields[1]):
            event.update(sender=fields[1], type="position")
            # With '-' the whole path is there. With 'WIDE1-1' it was cut off.
            if fields[-1] == "-":
                event["header"] = " / ".join(fields[2:-1])
        return
    for tag in _TAGGED:
        prefix = tag + " / "
        if content.startswith(prefix):
            sender, sep, rest = content[len(prefix):].partition(" ---> ")
            if sep and is_callsign(sender):
                event.update(sender=sender, info=rest, type=tag.lower())
            return


def packet_type(info):
    first = info[:1]
    if first == ":":
        return "message"
    if first in ("!", "=", "@", "/"):
        return "position"
    if first in ("`", "'"):
        return "mic-e"
    if first == ">":
        return "status"
    if first == ";":
        return "object"
    if first == "}":
        return "third-party"
    if first == "_":
        return "weather"
    if info.startswith("T#"):
        return "telemetry"
    return "other"


def minimum_length(event):
    """Lower bound for the on-air length of a packet known only from syslog."""
    if event.get("raw"):
        return 3 + len(event["raw"])
    header = event.get("header") or "XXXXXX"       # tocall is usually 6 characters
    body = len(event.get("info") or "")
    if event["type"] == "position":
        body = 14 + len(event.get("comment") or "")   # compressed position is 14
    elif event["type"] in ("message",):
        body += 2
    elif event["type"] == "telemetry":
        body += 3
    else:
        body += 1
    return 3 + len(event["sender"]) + 1 + len(header) + 1 + body


def airtime(length, sf=12, bw=125000, cr=5, preamble=8):
    """Seconds on air for a LoRa frame with explicit header and CRC
    (Semtech SX127x datasheet formula). cr is the denominator: 5 means 4/5."""
    symbol = (2 ** sf) / bw
    low_rate = 1 if symbol >= 0.016 else 0
    bits = 8 * length - 4 * sf + 28 + 16
    payload = 8 + max(math.ceil(bits / (4 * (sf - 2 * low_rate))) * cr, 0)
    return (preamble + 4.25 + payload) * symbol


def noise_estimate(rssi, snr):
    """Noise floor in dBm as seen by an SX127x board (K2GIA-10 is an SX1278).

    RadioLib 7.6.0 reports packet RSSI, plus SNR when SNR is below zero. Taking
    that back out gives total power (signal + noise); then remove the signal's
    share. Not used above +8 dB, where the SNR reading saturates.
    """
    if rssi is None or snr is None or snr >= 8:
        return None
    total = rssi - min(snr, 0.0)
    return total - 10 * math.log10(1 + 10 ** (snr / 10))
