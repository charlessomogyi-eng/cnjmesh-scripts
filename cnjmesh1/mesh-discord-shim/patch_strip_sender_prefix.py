#!/usr/bin/env python3
"""Patch mesh-discord-shim app.py so channel messages don't show the sender name twice.

Usage (on cnjmesh1):  sudo python3 patch_strip_sender_prefix.py /opt/stacks/mesh-discord-shim/app.py [--dry-run]

Why: MeshCore channel messages arrive as text "Name: message", and the shim posts
f"💬 **{sender}**: {text}", so Discord shows "CNJWeatherBot: CNJWeatherBot: Daily Weather ...".

Change: just before the channel routing in handle_channel_message(), if text starts with
"<sender>: " (case-insensitive), remove that prefix. If the sender name does not match, nothing changes.
Exact-match-or-abort; compiles the result; --dry-run writes nothing; timestamped backup before a write.
app.py is COPIED into the container image (Dockerfile: COPY app.py .), so the change only takes effect
after:  cd /opt/stacks/mesh-discord-shim && sudo docker compose up -d --build   (separate step, not done here)
No secrets involved.
"""
import shutil, sys, time

args = [a for a in sys.argv[1:] if not a.startswith("--")]
dry = "--dry-run" in sys.argv
if len(args) != 1:
    sys.exit(__doc__)
target = args[0]
t = open(target, encoding="utf-8").read()
if "strip leading sender prefix" in t:
    sys.exit("ABORT: already patched.")

ANCHOR = (
'    if channel == "CentralNJ-MC":\n'
'        log.info("Channel message on CentralNJ-MC from %s", sender)\n'
)
ADD = (
'    # strip leading sender prefix: MeshCore text is already "Name: message"\n'
'    _pfx = f"{sender}: "\n'
'    if sender != "unknown" and text.lower().startswith(_pfx.lower()):\n'
'        text = text[len(_pfx):]\n'
'\n'
)
if t.count(ANCHOR) != 1:
    sys.exit(f"ABORT: routing anchor found {t.count(ANCHOR)} times (need exactly 1)")
t = t.replace(ANCHOR, ADD + ANCHOR)
compile(t, target, "exec")
if dry:
    print("DRY RUN OK: anchor found once, result compiles, nothing written.")
    sys.exit(0)
bak = f"{target}.bak-stripprefix-{time.strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(target, bak)
open(target, "w", encoding="utf-8").write(t)
print("OK: patched", target, "| backup:", bak)
print("Takes effect only after: cd /opt/stacks/mesh-discord-shim && sudo docker compose up -d --build")
