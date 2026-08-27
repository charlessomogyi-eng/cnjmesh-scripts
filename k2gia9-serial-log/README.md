# K2GIA-9 serial log

Continuously captures K2GIA-9's (LoRa APRS Tracker) serial console output to
`/var/log/k2gia9-serial.log` on cnjmesh1, so the `[LoRa Tx]`/`[LoRa Rx]`/
`[Bluetooth]` activity is visible without needing a laptop plugged in and a
browser tab open (the manual method used during initial testing on
2026-08-26/27).

Not tied into any other pipeline — this is a raw passive log, nothing more.
No Discord relay, no parsing, no alerting. If that's wanted later, build it
as a separate consumer of this log file rather than modifying this service.

## Why rotation is included from day one

cnjmesh1's original board died from a disk-full / hard-power-cycle failure
(see `session-log.md`, July 21 2026). This log is a continuous, unbounded
stream by nature (`cat` on a serial device) — rotation is not optional
here, it's a direct mitigation against repeating that failure.

## Deploy (on cnjmesh1)

```bash
sudo cp k2gia9-serial-log.service /etc/systemd/system/
sudo cp k2gia9-serial-log.logrotate /etc/logrotate.d/k2gia9-serial
sudo systemctl daemon-reload
sudo systemctl enable --now k2gia9-serial-log.service
```

Verify the serial path is correct first — confirm via:
```bash
udevadm info -q property -n /dev/ttyACM2 | grep ID_SERIAL_SHORT
```
Should show `58EF088583` (K2GIA-9's unique serial, distinct from K2GIA-10's
`58EF089845` — confirmed via `udevadm`, see `cnjmesh1-operations.md`). If
K2GIA-9 is ever unplugged and replugged into a different physical port, the
`ttyACM*` number may change, but the `/dev/serial/by-id/...` path used in
the service file will not — no service file edit needed after a replug,
only if the board itself is swapped for a different unit.

## Check it's working

```bash
sudo systemctl status k2gia9-serial-log
tail -f /var/log/k2gia9-serial.log
```

## Notes

- Uses `copytruncate` in logrotate (not the default rename-and-signal
  approach) because `cat` holds the file open continuously and has no way
  to be told to reopen it on rotation — `copytruncate` handles this without
  needing to restart the service on every rotation.
- `Restart=always` means if K2GIA-9 is ever unplugged, the service will
  keep retrying every 5s rather than dying — it'll pick back up
  automatically once replugged, no manual restart needed.
- This is temporary/testing infrastructure per `docs/lora-aprs-reference.md`
  — K2GIA-9 was originally meant to be a mobile tracker. If/when it's
  unplugged and taken mobile again, this service will just sit retrying
  harmlessly; disable it with `sudo systemctl disable --now
  k2gia9-serial-log.service` if that becomes annoying in logs/status
  checks.
