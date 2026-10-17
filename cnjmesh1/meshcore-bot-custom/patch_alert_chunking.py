#!/usr/bin/env python3
"""Patch the LIVE meshcore-bot weather_service.py so NWS alerts are sent like the forecast.

Usage (on cnjmesh1):  sudo python3 patch_alert_chunking.py TARGET SOURCE
  TARGET = /opt/meshcore-bot/modules/service_plugins/weather_service.py  (the copy the service runs)
  SOURCE = ~/meshcore-bot/modules/service_plugins/weather_service.py     (home clone with the Sep 1 formatter)

Two changes, each exact-match-or-abort (nothing is written unless both succeed and the result compiles):
 1. Replace _format_alert_compact in TARGET with the SOURCE version (full text, no event[:15] / office[:10] cuts).
 2. In the alert send loop, split the text with split_text_into_utf8_chunks(text, 140) and send it with
    send_channel_messages_chunked, exactly as _send_daily_forecast_async does.
A timestamped backup of TARGET is made first. No secrets are involved.
"""
import re, shutil, sys, time

target, source = sys.argv[1], sys.argv[2]
FUNC = re.compile(r"(    async def _format_alert_compact\(.*?)(?=\n    (?:async )?def )", re.S)

t = open(target, encoding="utf-8").read()
s = open(source, encoding="utf-8").read()

mt, ms = FUNC.findall(t), FUNC.findall(s)
if len(mt) != 1 or len(ms) != 1:
    sys.exit(f"ABORT: expected exactly one _format_alert_compact in each file (target {len(mt)}, source {len(ms)})")
if "event[:15]" not in mt[0]:
    sys.exit("ABORT: target formatter does not contain the old truncation; already patched?")
if "event[:15]" in ms[0] or "office[:10]" in ms[0]:
    sys.exit("ABORT: source formatter still contains truncation")
t = t.replace(mt[0], ms[0])

OLD = (
"                    alert_text = await self._format_alert_compact(alert, include_details=True)\n"
"\n"
"                    await self.bot.command_manager.send_channel_message(\n"
"                        self.alerts_channel,\n"
"                        alert_text,\n"
"                        scope=self.get_mesh_flood_scope(),\n"
"                    )\n"
)
NEW = (
"                    alert_text = await self._format_alert_compact(alert, include_details=True)\n"
"\n"
"                    # Send like the daily forecast: split into <=140-char chunks, then send all chunks.\n"
"                    _al_chunks = self.bot.command_manager.split_text_into_utf8_chunks(alert_text, 140)\n"
"                    await self.bot.command_manager.send_channel_messages_chunked(\n"
"                        self.alerts_channel,\n"
"                        _al_chunks,\n"
"                        scope=self.get_mesh_flood_scope(),\n"
"                    )\n"
)
if t.count(OLD) != 1:
    sys.exit(f"ABORT: alert send block found {t.count(OLD)} times (need exactly 1)")
t = t.replace(OLD, NEW)

compile(t, target, "exec")  # syntax check before touching anything

bak = f"{target}.bak-alertchunk-{time.strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(target, bak)
open(target, "w", encoding="utf-8").write(t)
print("OK: patched", target, "| backup:", bak)
