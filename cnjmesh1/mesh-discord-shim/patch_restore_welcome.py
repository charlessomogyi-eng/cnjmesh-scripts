#!/usr/bin/env python3
"""Patch mesh-discord-shim app.py: put "Welcome to NJ MeshCore 🎉" back under the "Node heard" line.

Usage (on cnjmesh1):  sudo python3 patch_restore_welcome.py /opt/stacks/mesh-discord-shim/app.py [--dry-run]

Context: patch_new_node_wording.py replaced the whole first line ("We see you, {name}! Welcome to NJ MeshCore")
with "Node heard: {name}". Charles (Oct 20 2026, 23:34) only wanted "We see you" gone and wanted the welcome kept.

Result in #cnj-new-node-relay:
    📡 Node heard: **{name}**
    Welcome to NJ MeshCore 🎉
    `<key prefix>...`
    -# heard by <FOOTER>

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
NEW = OLD + '            f"Welcome to NJ MeshCore 🎉\\n"\n'
if "Welcome to NJ MeshCore" in t:
    sys.exit("ABORT: 'Welcome to NJ MeshCore' already present in the target.")
if t.count(OLD) != 1:
    sys.exit(f"ABORT: 'Node heard' line found {t.count(OLD)} times (need exactly 1)")
t = t.replace(OLD, NEW)
compile(t, target, "exec")
if dry:
    print("DRY RUN OK: line found once, result compiles, nothing written.")
    sys.exit(0)
bak = f"{target}.bak-welcome-{time.strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(target, bak)
open(target, "w", encoding="utf-8").write(t)
print("OK: patched", target, "| backup:", bak)
print("Takes effect only after: cd /opt/stacks/mesh-discord-shim && sudo docker compose up -d --build")
