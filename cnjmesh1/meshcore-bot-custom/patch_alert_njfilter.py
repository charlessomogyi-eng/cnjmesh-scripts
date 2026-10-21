#!/usr/bin/env python3
"""Patch the LIVE meshcore-bot weather_service.py so only real Mount Holly alerts are relayed.

Usage (on cnjmesh1):  sudo python3 patch_alert_njfilter.py TARGET [--dry-run]
  TARGET = /opt/meshcore-bot/modules/service_plugins/weather_service.py  (the copy the service runs)

Why: on Oct 20 2026 a TEST tsunami warning for Texas ("by NWS NATI") was relayed to the
#centralnj-mc-channel-relay Discord channel. Upstream has no test or sender filter.

What it adds (inside the alert polling loop, right after the alert entry is parsed):
  - skip any alert whose title contains the word TEST
  - skip any alert whose issuing office (the text after "by" in the ATOM title) is not NWS Mount Holly
  - remember skipped alert ids (so they are logged once, not every poll) and log
    "Weather alert skipped (CNJ filter): <title>" at INFO level

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

if "CNJ filter" in t:
    sys.exit("ABORT: already patched (found 'CNJ filter').")

ANCHOR = (
"                    alert_dict = self._parse_alert_entry(entry, alert_id)\n"
"                    if not alert_dict:\n"
"                        continue\n"
)
ADD = (
"\n"
"                    # CNJ filter: only real NWS Mount Holly alerts (no tests, no other offices)\n"
"                    _cnj_title = alert_dict.get('title') or ''\n"
"                    _cnj_office = (alert_dict.get('office') or '').lower()\n"
"                    if re.search(r'\\btest\\b', _cnj_title, re.IGNORECASE) or 'mount holly' not in _cnj_office:\n"
"                        self.seen_alert_ids.add(alert_id)\n"
"                        self.logger.info(f\"Weather alert skipped (CNJ filter): {_cnj_title}\")\n"
"                        continue\n"
)
if t.count(ANCHOR) != 1:
    sys.exit(f"ABORT: parse anchor found {t.count(ANCHOR)} times (need exactly 1). Send the output of: "
             f"sudo grep -n -A3 '_parse_alert_entry(entry' {target}")
if "\nimport re\n" not in t and "\nimport re," not in t and "import re\n" not in t:
    sys.exit("ABORT: 're' does not appear to be imported in the target")
t = t.replace(ANCHOR, ANCHOR + ADD)
compile(t, target, "exec")

if dry:
    print("DRY RUN OK: anchor found once, result compiles, nothing written.")
    sys.exit(0)
bak = f"{target}.bak-njfilter-{time.strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(target, bak)
open(target, "w", encoding="utf-8").write(t)
print("OK: patched", target, "| backup:", bak)
print("Restart is separate: sudo systemctl restart meshcore-bot  (only when ready)")
