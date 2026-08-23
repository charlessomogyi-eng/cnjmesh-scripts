# known-issues.md — ALWAYS FETCH THIS

Short list of **active, currently-true gotchas** across the whole project (mesh infra and APRS/radio side). Written bluntly, in checkable terms, specifically so a fresh session catches these before declaring something "configured correctly." Delete an entry once it's actually resolved — this file is for what's *currently* true, not a history (that's `session-log.md`'s job).

**Rule for reviewing any screenshot or config claim:** a filled-in field is not the same as an active/working feature. Always check the actual status indicator, connection banner, or "connected/disconnected" label shown on screen — not just whether the input fields look populated/correct. Cross-check against this file before confirming anything is "fine."

---

## APRS / TD-H9 / K2GIA stations

- **K2GIA-7 (TD-H9, via KISSLink app): APRS-IS Companion tab shows Disconnected**, even though all its fields (server `rotate.aprs2.net`, port `14580`, callsign `K2GIA-7`, passcode `16025`) are filled in correctly. **A screenshot showing correct field values on this tab is NOT evidence that APRS-IS is connected — check for the word "Connected"/"disconnected" explicitly.** Effect: K2GIA-7 currently receives over RF only, not APRS-IS. This means a message sent from an Internet-only node (K2GIA-5/APRSdroid) will not reliably reach K2GIA-7 while this is disconnected. Full detail: `docs/aprs-bulletins-and-bridging-reference.md`, `docs/td-h9-app-field-reference.md`.
- **K2GIA-5 (APRSdroid) is Internet/APRS-IS only, by design — it has no RF path at all.** Don't assume a message from K2GIA-5 reached anyone over RF; it can only ever reach APRS-IS-connected stations. Detail: `docs/k2gia-5-aprsdroid-reference.md`.
- **APRS "CQ" is not a broadcast address.** It has no special meaning in APRS — the correct broadcast convention is `BLN1`-`BLN9` (bulletins). Confirmed via Graywolf source review + live RF test. Detail: `docs/aprs-bulletins-and-bridging-reference.md`.
- **K2GIA-10 (LoRa iGate) has a documented self-gating limitation** — its KISS TNC is TX-injection only, it cannot reliably hear/gate its own outgoing transmissions. A second RX-only board was ordered to address this (status: check `todos.md` / `docs/lora-aprs-reference.md` for current state).
- **Graywolf (K2GIA-1) has a known intermittent cpal/ALSA POLLERR audio bug** (RustAudio/cpal#730) — confirmed non-blocking (TX/beacon/iGate all unaffected), only degrades Graywolf's own RF self-hearing. Do not treat this as a functional outage if seen in logs. Detail: `docs/aprs-2m-graywolf-reference.md`.
- **Only one app (KISSLink OR TD-H9 APRS Messenger) can hold the BLE connection to the TD-H9 at a time.** If a connection attempt fails and the other app was recently used, check whether it's still holding the BLE link first.

## Mesh infra (cnjmesh1/2/3)
See `cnjmesh1-operations.md`'s own "Known Issues / Don't Touch" section — not duplicated here to avoid drift between two copies. Always fetch that file too.

---

*(This file is new as of 2026-08-23, created after a fresh session reviewed a KISSLink screenshot, saw correctly-filled-in IS fields, and incorrectly declared APRS-IS "configured fine" without checking the actual connection status — the K2GIA-7 entry above is that exact issue. Purpose of this file is to make that class of mistake structurally harder: known gotchas live in one short, always-fetched place instead of being buried in long-form reference docs a session might not think to open.)*
