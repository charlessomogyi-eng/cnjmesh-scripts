#!/usr/bin/env python3
"""Write fixtures/samples.json from the compiled firmware code.

Run tests/harness/build.sh first. All callsigns other than K2GIA-10 are
placeholders (N0CALL, N0DIGI); nothing here was received over the air.
"""
import json
from pathlib import Path

import firmware

H = firmware.HEADER
POS = b"!4015.00N/07430.00W>"


def base91(value):
    out = ""
    for power in (91 ** 3, 91 ** 2, 91, 1):
        digit, value = divmod(value, power)
        out += chr(digit + 33)
    return out.encode()


# APRS compressed position for 40.25 N, 74.5 W (symbol L/a, type byte G)
PACKED = (b"L" + base91(int(380926 * (90 - 40.25))) +
          base91(int(190463 * (180 - 74.5))) + b"a  G")

# name, op, rssi, snr, freq error, frame
CASES = [
    ("position_wide1", "rx", -97, 9.5, 120, H + b"N0CALL-7>APLRT1,WIDE1-1,WIDE2-1:" + POS + b"direct"),
    ("position_via_digi", "rx", -112, -6.25, -410, H + b"N0CALL-7>APLRT1,N0DIGI-10*,WIDE2-1:" + POS + b"via digi"),
    ("position_no_path", "rx", -104, 1.0, 75, H + b"N0CALL-3>APLRT1:=4015.00N/07430.00W>no path"),
    ("position_timestamp", "rx", -104, 1.0, 75, H + b"N0CALL-3>APLRT1:@092345z4015.00N/07430.00W>timed"),
    ("position_compressed", "rx", -108, -2.0, 310, H + b"N0DIGI-10>APLRG1:=" + PACKED + b"base91 beacon"),
    ("message", "rx", -118, -12.25, -2300, H + b"N0CALL-9>APLRT1,WIDE1-1::K2GIA-10 :hello there{12"),
    ("message_fake_signal", "rx", -101, 4.0, 15, H + b"N0CALL-9>APLRT1::K2GIA-10 :x / -1dBm / 1.00dB / 2Hz{13"),
    ("status", "rx", -110, -3.5, 40, H + b"N0DIGI-10>APLRG1:>status text"),
    ("mic_e", "rx", -110, -3.5, 40, H + b"N0CALL-5>T0RS2P,WIDE1-1:`(_fn\"Oj/]comment"),
    ("object", "rx", -110, -3.5, 40, H + b"N0DIGI-10>APLRG1:;OBJNAME  *111111z4015.00N/07430.00Wr object"),
    ("telemetry", "rx", -110, -3.5, 40, H + b"N0CALL-5>APRS:T#005,199,000,255,073,123,01101001"),
    ("weather", "rx", -110, -3.5, 40, H + b"N0CALL-5>APRS:_10090556c220s004g005t077"),
    ("third_party", "rx", -110, -3.5, 40, H + b"N0DIGI-10>APLRG1:}N0CALL-1>APRS,TCPIP,N0DIGI-10*::N0CALL-7 :third party"),
    ("utf8_comment", "rx", -99, 6.0, 10, H + b"N0CALL-3>APLRT1:" + POS + "café 73".encode()),
    # RXT style: text, a zero byte, then binary. Stock firmware stops at the zero.
    ("zero_byte_tail", "rx", -99, 6.0, 10, H + b"N0DIGI-10>APLRG1:>rxt digi\x00\x01\x02\x03"),
    # Too long for PubSubClient's 256 byte buffer: syslog only, no MQTT.
    ("too_long_for_mqtt", "rx", -99, 6.0, 10, H + b"N0CALL-3>APLRT1:>" + b"L" * 225),
    ("crc_error", "crc", -125, -19.75, -900, H + b"N0C\x91\x02ALL>garb"),
    ("own_internet_beacon", "rx", 0, 0.0, 0, b"tcpK2GIA-10>APLRG1,qAC:=" + PACKED + b"beacon"),
    ("tx_own_beacon", "tx", 0, 0.0, 0, b"K2GIA-10>APLRG1,WIDE1-1,WIDE2-1,RFONLY,NOGATE:=" + PACKED + b"CNJ Mesh"),
    ("tx_message", "tx", 0, 0.0, 0, b"K2GIA-10>APLRG1,WIDE1-1::K2GIA-10 :test 10{89"),
    ("tx_digipeat", "tx", 0, 0.0, 0, b"N0CALL-7>APLRT1,K2GIA-10*:" + POS + b"digipeated"),
]

DIGI_CASES = [      # name, frame heard by a "WIDE2 (+WIDE1)" digipeater
    ("wide1_first_hop", H + b"N0CALL-7>APLRT1,WIDE1-1,WIDE2-1:" + POS + b"x"),
    ("wide2_second_hop", H + b"N0CALL-7>APLRT1,N0DIGI-10*,WIDE2-1:" + POS + b"x"),
    ("wide2_2", H + b"N0CALL-7>APLRT1,WIDE2-2:" + POS + b"x"),
]


def text(value):
    return None if value is None else value.decode("latin-1")


def build():
    results = firmware.run([c[1:] for c in CASES])
    samples = {}
    for (name, op, rssi, snr, ferr, data), (syslog, topic, payload, _) in zip(CASES, results):
        if name == "own_internet_beacon":
            topic = payload = None      # logged only; never an MQTT message
        samples[name] = {"op": op, "rssi": rssi, "snr": snr, "freq_err": ferr,
                         "frame": text(data), "syslog": text(syslog),
                         "mqtt_topic": text(topic), "mqtt_payload": text(payload)}
    digi = firmware.run([("digi", 0, 0, 0, frame) for _, frame in DIGI_CASES])
    return {
        "firmware": "CA2RXU LoRa_APRS_iGate V3.2.4",
        "samples": samples,
        "digipeats": {name: {"heard": text(frame), "sent": text(out[3])}
                      for (name, frame), out in zip(DIGI_CASES, digi)},
    }


if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "fixtures" / "samples.json"
    target.write_text(json.dumps(build(), indent=1) + "\n")
    print("wrote", target)
