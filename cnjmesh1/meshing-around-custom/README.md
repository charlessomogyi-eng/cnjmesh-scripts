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
- modules/locationdata.py (patch `locationdata-eas-filter.diff`, found Nov 12 2026, **drafted, not yet applied on the Pi**):
  in `alertBrodcastNOAA()` the `elif currentAlert[0] not in wxAlertCacheNOAA:` belongs to
  `if my_settings.ignoreEASenable:`, so with `ignoreEASenable = True` (our config) the function
  checks the ignore words and then falls through to `return False`: it never returns an alert and
  the bot never broadcasts an NWS alert to the mesh. The patch changes that `elif` to `if`, so the
  ignore words still filter and everything else is broadcast once (the cache still de-dupes).
  [V, the function's source as printed from the Pi Nov 12 2026; behavior tested offline with
  stand-in settings: original returns False for a Tornado Watch with the filter on, patched returns
  the alert and still drops "advisory" alerts.] Apply on the Pi:
      cd /opt/meshing-around && sudo git apply --check ~/cnjmesh-scripts/cnjmesh1/meshing-around-custom/locationdata-eas-filter.diff
      cd /opt/meshing-around && sudo git apply ~/cnjmesh-scripts/cnjmesh1/meshing-around-custom/locationdata-eas-filter.diff
      sudo systemctl restart mesh_bot.service
  Upstream is pinned at the commit in upstream-commit.txt; whether a later upstream commit already
  fixes this has not been checked (GitHub was not readable from the session).
