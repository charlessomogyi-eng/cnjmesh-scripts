#!/usr/bin/env python3
"""Patch mesh-discord-shim app.py: add a celebratory emoji to the new-node post.

Usage (on cnjmesh1):  sudo python3 patch_node_heard_party.py /opt/stacks/mesh-discord-shim/app.py [--dry-run]

Changes the first line of the #cnj-new-node-relay post from
    📡 Node heard: **{name}**
to
    📡 Node heard: **{name}** 🎉
(Charles, Oct 21 2026: wants it fun, not robotic, but not intrusive; no region wording.)

Exact-match-or-abort; compiles the result; --dry-run writes nothing; timestamped backup before a write.
app.py is COPIED into the image, so it takes effect only after:
  cd /opt/stacks/mesh-discord-shim && sudo docker compose up -d --build   (separate step)
No secrets involved.
"""
import shutil, sys, time

args = [a for a in sys.argv[1:] if not a.startswith("--")]
dry = "--dry-run" in sys.argv
if len(args) != 1:
    sys.exit(__doc__)
target = args[0]
t = open(target, encoding="utf-8").read()

OLD = '            f"📡 Node heard: **{name}**\\n"\n'
NEW = '            f"📡 Node heard: **{name}** 🎉\\n"\n'
if NEW in t:
    sys.exit("ABORT: already patched.")
if t.count(OLD) != 1:
    sys.exit(f"ABORT: 'Node heard' line found {t.count(OLD)} times (need exactly 1)")
t = t.replace(OLD, NEW)
compile(t, target, "exec")
if dry:
    print("DRY RUN OK: line found once, result compiles, nothing written.")
    sys.exit(0)
bak = f"{target}.bak-party-{time.strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(target, bak)
open(target, "w", encoding="utf-8").write(t)
print("OK: patched", target, "| backup:", bak)
print("Takes effect only after: cd /opt/stacks/mesh-discord-shim && sudo docker compose up -d --build")
