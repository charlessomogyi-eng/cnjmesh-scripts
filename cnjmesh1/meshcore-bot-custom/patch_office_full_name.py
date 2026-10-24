#!/usr/bin/env python3
"""Patch the LIVE meshcore-bot weather_service.py so alerts say "by NWS Mount Holly", not "by NWS MOUN".

Usage (on cnjmesh1):  sudo python3 patch_office_full_name.py TARGET [--dry-run]
  TARGET = /opt/meshcore-bot/modules/service_plugins/weather_service.py  (the copy the service runs)

Why: on Oct 23 2026 a real frost advisory showed "by NWS MOUN". The formatter takes only the SECOND word of the
office name ("NWS Mount Holly NJ" -> "Mount"), then cuts it to 4 letters. "Holly" is thrown away.

What it changes (inside _format_alert_compact, the "Add office if available" block):
  old:  city = office_parts[1] ...;  city_abbrev = self._abbreviate_city_name(city)
  new:  city = every word after "NWS", minus a trailing 2-letter state code (NJ), spelled out in full.
        "NWS Mount Holly NJ" -> "by NWS Mount Holly".  "NWS Philadelphia PA" -> "by NWS Philadelphia".
Nothing else changes. Alerts are already sent in chunks, so the longer text is fine.

Exact-match-or-abort: nothing is written unless the anchor is found exactly once and the result compiles.
--dry-run checks all of that and writes nothing. A timestamped backup is made before a real write.
Restart of meshcore-bot is a separate step and is NOT done by this script. No secrets involved.
"""
import shutil, sys, time

args = [a for a in sys.argv[1:] if not a.startswith("--")]
dry = "--dry-run" in sys.argv
if len(args) != 1:
    sys.exit(__doc__)
target = args[0]
t = open(target, encoding="utf-8").read()

if "CNJ office name" in t:
    sys.exit("ABORT: already patched (found 'CNJ office name').")

OLD = (
"                    city = office_parts[1] if len(office_parts) > 1 else \"\"\n"
"                    city_abbrev = self._abbreviate_city_name(city)\n"
)
NEW = (
"                    # CNJ office name: keep the whole city name, drop a trailing 2-letter state code\n"
"                    _cnj_city_parts = office_parts[1:]\n"
"                    if len(_cnj_city_parts) > 1 and len(_cnj_city_parts[-1]) == 2 and _cnj_city_parts[-1].isupper():\n"
"                        _cnj_city_parts = _cnj_city_parts[:-1]\n"
"                    city_abbrev = \" \".join(_cnj_city_parts)\n"
)
n = t.count(OLD)
if n != 1:
    sys.exit(f"ABORT: office anchor found {n} times (need exactly 1). Send the output of: "
             f"sudo grep -n -B3 -A8 'office_parts = office.split' {target}")
t = t.replace(OLD, NEW)
compile(t, target, "exec")

if dry:
    print("DRY RUN OK: anchor found once, result compiles, nothing written.")
    sys.exit(0)
bak = f"{target}.bak-officename-{time.strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(target, bak)
open(target, "w", encoding="utf-8").write(t)
print("OK: patched", target, "| backup:", bak)
print("Restart is separate: sudo systemctl restart meshcore-bot  (only when ready)")
