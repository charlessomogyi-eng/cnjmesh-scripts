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
  Upstream is pinned at the commit in upstream-commit.txt. Checked Nov 12 2026: upstream's latest
  (`92280b7`, Nov 9 2026) still has the same `elif`, so the patch is still needed on a newer pin.
- modules/locationdata.py (patch `locationdata-alert-area.diff`, written Nov 12 2026, **not yet applied on the Pi**;
  apply AFTER `locationdata-eas-filter.diff`): NWS alerts to the mesh name the issuing office but not
  the county. Upstream already has a switch, `enableExtraLocationWx`, but with it on it appends the
  whole county list from the feed (a watch can list many counties) with the spaces stripped. This
  patch adds `format_alert_areas()`: at most 3 areas per alert (`ALERT_AREA_MAX`), the home area
  first, then `+N` for the rest, e.g. `Middlesex, Salem, Cumberland +2` or `New Castle DE, Salem NJ, Kent DE +4`.
  Config (`[location]` in the Pi's config.ini; the repo copy is NOT changed until it is deployed):
      enableExtraLocationWx = True
      alertAreaHome = Middlesex
  `alertAreaHome` is optional, comma separated, matched anywhere in the area name; without it the
  areas appear in the order NWS lists them. [V: applies cleanly on top of the first patch against the pinned commit,
  compiles, and the helper was tested offline with both NWS name styles (`Middlesex; Mercer` and
  `New Castle, DE; Salem, NJ`). **Verified live Nov 12 2026 4:30 PM** on cnjmesh1: a Tornado Watch went out as
  `...by NWS Mount Holly NJ. Middlesex, Burlington, Camden +8` in one message (145 bytes). Still unverified: how the bot splits an alert
  that would be longer than one Meshtastic message.]
  Apply on the Pi:
      cd /opt/meshing-around && sudo git apply --check ~/cnjmesh-scripts/cnjmesh1/meshing-around-custom/locationdata-alert-area.diff
      cd /opt/meshing-around && sudo git apply ~/cnjmesh-scripts/cnjmesh1/meshing-around-custom/locationdata-alert-area.diff
  (`--check` fails if the first patch has not been applied; it has been on cnjmesh1 since Nov 12.)
- modules/locationdata.py (patch `locationdata-alert-wide.diff`, written Nov 12 2026, **ON HOLD by Charlie: not applied, may never be**;
  would go on after the other two): also broadcasts NWS alerts for Middlesex and the counties south of it
  (Somerset, Mercer, Monmouth, Ocean, Burlington, Camden, Gloucester, Salem, Cumberland, Atlantic, Cape May).
  The bot's alert query is the single home point, so alerts that miss that point never reach the mesh. The patch keeps that
  query and adds a second one for the whole state (`?area=NJ`), keeping alerts whose six-digit county codes match a configured
  list. Only the scheduled broadcast does this (`wide=True`); the bot's user commands are unchanged. Config would be
  `alertStateArea = NJ` and `alertFIPS = 34023,34035,34025,34029,34021,34005,34007,34015,34033,34011,34001,34009`
  (codes from NWS's list, weather.gov/media/pimar/FIPS/nj_cnty.pdf); with neither set, nothing changes.
  [V offline with stand-in feeds: applies after the other two, compiles, adds matching alerts, drops other counties and alerts
  with no county code, keeps the point alert if the statewide fetch fails. Unverified: the real feed's geocode element names
  (the patch takes any six-digit number in `cap:geocode`) and message volume. The bot's repeat-check compares the combined text
  of the first two alerts, so a wider net would re-send more often.]
