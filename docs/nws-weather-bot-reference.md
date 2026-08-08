# NWS Weather Bot — Technical Reference

Built in a Gemini-assisted session on Aug 8, 2026 (Charles ran out of Claude tokens mid-session, continued with Gemini, then brought the results back here). This doc preserves that session's technical handoff. **Known bug: see the note at the bottom before trusting this as fully working.**

## Node inventory (as of Aug 8, 2026)

- **cnjmesh1** — gateway host, runs the script + cron, Kendall Park NJ (40.4134°N, -74.5625°W)
- **KPC1** — stationary base station radio, USB serial to cnjmesh1 at `/dev/kpc1`, firmware `v1.16.0-07a3ca9`. Reflashed Aug 8 from BLE to serial-companion firmware specifically to enable this bot (see session-log.md Aug 8 entry — this is why Charles's personal messaging moved off KPC1).
- **KPC2** — Charles's LilyGo T-Deck, standalone mobile field unit. Untethered, screen+keyboard+battery, does direct RF messaging with KPC1 (shared channel keys). **Note:** the repo's existing "KPN2" designation (from July 14, `10.0.0.140`) refers to this same physical T-Deck — KPC2 appears to be how it's referred to in its new MeshCore role specifically. Worth reconciling these two names so future notes don't treat them as different devices.

## Channel mapping

- **Channel 0** — Public. Explicitly excluded from automated broadcasts.
- **Channel 2** — `CentralNJ-MC`. PSK: `dcc94b369feeee309800ee15a12403ed`. This is the intended target for the weather bot.

## meshcore-cli syntax (confirmed working commands)

```bash
# Broadcast to a channel:
meshcore-cli -s <SERIAL_PORT> chan <CHANNEL_INDEX> "<MESSAGE>"

# List configured channels on a device:
meshcore-cli -s /dev/ttyACM0 get_channels

# Explicitly (re)assign a channel slot:
meshcore-cli -s /dev/ttyACM0 set_channel 2 CentralNJ-MC dcc94b369feeee309800ee15a12403ed

# Add a channel if not already present:
meshcore-cli -s /dev/ttyACM0 add_channel CentralNJ-MC dcc94b369feeee309800ee15a12403ed
```
**Gotchas already diagnosed:** `-c` toggles color output, not channel selection. A bare `msg` targets a specific node, not a channel — use `chan` for broadcasts.

## The script

`cnjmesh1/nws-weather-bot/nws_mesh_broadcast.py` in this repo (copy of the working version). Two modes:
- `forecast` — fetches `https://api.weather.gov/gridpoints/PHI/65,95/forecast`, sends period[0]'s short forecast + temp + wind
- `alert` (default) — fetches `https://api.weather.gov/alerts/active?zone=NJZ018`, de-dupes against `/tmp/last_nws_alert.txt` by alert ID, sends only new alerts

Both call `send_to_mesh()`, which shells out to `meshcore-cli -s /dev/kpc1 chan 2 "<message>"`.

## ⚠️ KNOWN BUG — read before trusting this

**Despite the code targeting channel index 2, Charles observed the actual test broadcast land on the Public channel** (seen directly on his T-Deck/KPC2). This has NOT been root-caused yet. The code as written looks correct on inspection — `CHANNEL_INDEX = "2"` is passed as a distinct argv element to `subprocess.run()` (no shell interpretation issues). Suspected causes, not yet confirmed:
1. Channel index 2 on KPC1 may not actually be `CentralNJ-MC` right now — re-run `get_channels` fresh before assuming the mapping from this session still holds
2. Consider using `set_channel 2 CentralNJ-MC dcc94b369feeee309800ee15a12403ed` explicitly to force the correct assignment, removing any ambiguity, before retesting
3. Possible `meshcore-cli` behavior where an unrecognized/out-of-range channel index silently falls back to Public — worth checking `meshcore-cli --help` for the `chan` subcommand's documented behavior

**Do not schedule (cron) this again until a fresh test message is sent and confirmed by Charles to land on CentralNJ-MC specifically — not Public.**

## Automation status
Cron entries were tested (`0 7 * * *` for forecast, `*/10 * * * *` for alerts) then deliberately removed (`crontab -r`) — **no automated broadcasts are currently running.** Two things must happen before re-enabling: (1) the channel bug above must be fixed and verified, (2) per the original plan, Charles should confirm channel-etiquette/ownership comfort with a scheduled bot on this private community channel.
