#!/usr/bin/env python3
"""Patch mesh-discord-shim app.py: replace the "We see you, <name>! Welcome to NJ MeshCore" announcement.

Usage (on cnjmesh1):  sudo python3 patch_new_node_wording.py /opt/stacks/mesh-discord-shim/app.py [--dry-run]

Old first line of the #cnj-new-node-relay post:  👋 **We see you, {name}!** Welcome to NJ MeshCore 🎉
New first line:                                  📡 Node heard: **{name}**
The key line and the "heard by <FOOTER>" line are unchanged.

Why: Charles (Oct 19 2026): "we see you" doesn't sit well with private mesh operators; also the observer holds
only about 350 contacts, so a "new" node can just be a returning one, so the post should not claim it is new or welcome.

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

OLD = '            f"👋 **We see you, {name}!** Welcome to NJ MeshCore 🎉\\n"\n'
NEW = '            f"📡 Node heard: **{name}**\\n"\n'
if "Node heard:" in t:
    sys.exit("ABORT: already patched.")
if t.count(OLD) != 1:
    sys.exit(f"ABORT: old announcement line found {t.count(OLD)} times (need exactly 1)")
t = t.replace(OLD, NEW)
compile(t, target, "exec")
if dry:
    print("DRY RUN OK: line found once, result compiles, nothing written.")
    sys.exit(0)
bak = f"{target}.bak-nodewording-{time.strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(target, bak)
open(target, "w", encoding="utf-8").write(t)
print("OK: patched", target, "| backup:", bak)
print("Takes effect only after: cd /opt/stacks/mesh-discord-shim && sudo docker compose up -d --build")
