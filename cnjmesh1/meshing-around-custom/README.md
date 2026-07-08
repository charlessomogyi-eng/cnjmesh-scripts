# meshing-around customizations (cnjmesh1)

Upstream: https://github.com/SpudGunMan/meshing-around
Patch applies against commit: see upstream-commit.txt

## To rebuild from scratch:
1. Clone upstream: git clone https://github.com/SpudGunMan/meshing-around.git
2. Check out the commit in upstream-commit.txt (or apply patch to latest and resolve conflicts)
3. Apply the scheduler patch:
     cd meshing-around
     git apply /path/to/scheduler.py.diff
4. Copy config.ini into place
5. Re-run install/systemd setup (see /opt/meshing-around/etc/ in original repo for service files)

## What's customized:
- modules/scheduler.py: disabled tell_joke import, fixed late-binding closure bug
  in the weather scheduler lambda (all scheduled calls were referencing the same
  handle_wxc binding instead of capturing it per-call), trailing newline fix.
- config.ini: live bot configuration (radio interface, scheduler timing, channels)
