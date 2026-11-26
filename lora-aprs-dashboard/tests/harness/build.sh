#!/usr/bin/env bash
# Fetch the pinned upstream sources (not stored in this repo) and build the harness.
#   usage: tests/harness/build.sh [upstream-dir]     (default: tests/harness/.upstream)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
up="${1:-$here/.upstream}"
mkdir -p "$up" "$here/build"
up="$(cd "$up" && pwd)"

fetch() {   # dir url ref
    [ -d "$up/$1/.git" ] || git clone -q --depth 1 --branch "$3" "$2" "$up/$1"
}
fetch fw324   https://github.com/richonguzman/LoRa_APRS_iGate V3.2.4
fetch aprslib https://github.com/richonguzman/APRSPacketLib 1.0.4
if [ ! -d "$up/esp32core/.git" ]; then
    git clone -q --depth 1 --branch 2.0.17 --filter=blob:none --sparse \
        https://github.com/espressif/arduino-esp32 "$up/esp32core"
    git -C "$up/esp32core" sparse-checkout set cores/esp32
fi
fetch tinygps https://github.com/mikalhart/TinyGPSPlus v1.0.3

core="$up/esp32core/cores/esp32"
b="$here/build"
# Copy only the headers needed, so the rest of the ESP32 core cannot shadow host headers.
cp "$core/WString.h" "$core/WString.cpp" "$core/pgmspace.h" "$core/stdlib_noniso.h" "$core/stdlib_noniso.c" "$b/"
cp "$up/fw324/include/"{syslog_utils.h,mqtt_utils.h,digi_utils.h,gps_utils.h} "$b/"
inc=(-I "$here/shim" -I "$b" -I "$up/aprslib/include" -I "$up/aprslib/src" -I "$up/tinygps/src")

gcc -O1 -w -I "$here/shim" -I "$b" -c "$b/stdlib_noniso.c" -o "$b/stdlib_noniso.o"
g++ -std=gnu++17 -O1 -w -fpermissive -DARDUINO=10812 -ffunction-sections -fdata-sections \
    "${inc[@]}" -include Arduino.h \
    "$here/harness.cpp" "$b/WString.cpp" "$b/stdlib_noniso.o" \
    "$up/fw324/src/syslog_utils.cpp" "$up/fw324/src/mqtt_utils.cpp" \
    "$up/fw324/src/gps_utils.cpp" "$up/fw324/src/digi_utils.cpp" \
    "$up/aprslib/src/APRSPacketLib.cpp" "$up/tinygps/src/TinyGPS++.cpp" \
    -Wl,--gc-sections -o "$b/harness"
echo "built $b/harness"
