# APRS Bulletins, Broadcast Messaging, and Cross-Band Bridging Reference

**Last updated:** 2026-08-23

## Bulletins vs. CQ — how to message "anyone listening"
Confirmed via review of Graywolf's own source code (not guessing/assuming):

- **APRS bulletins (`BLN1` through `BLN9`) are the correct addressing convention for a general broadcast message** — not `CQ`. `CQ` has no special meaning in APRS message addressing; it's a voice/CW convention that doesn't carry over.
- Graywolf **will** transmit a message addressed to `CQ` without complaint (the `to` field is free text, no validation blocks it) — but no receiving station or software treats `CQ` as a broadcast/bulletin address. It just looks like a message addressed to a station named "CQ," which doesn't exist.
- **Live-tested both `BLN1` and `CQ` from K2GIA-1 on 2026-08-23** — both transmitted fine over RF. Neither got an ACK, which is expected and correct for both: bulletins are inherently unacknowledged (there's no single recipient to ACK), and `CQ` predictably got nothing back since no real station is listening for that address.

**Takeaway:** if the goal is ever a general "hello, testing, anyone receiving" broadcast from K2GIA-1 (or K2GIA-7 once relevant), address it to `BLN1` (or another `BLN`-numbered bulletin slot), not `CQ`.

## Open issue: K2GIA-7's KISSLink APRS-IS Companion won't connect
Found 2026-08-23: on K2GIA-7 (TD-H9via KISSLink), the **IS tab / APRS-IS Companion shows "Disconnected"** even though all fields — server (`rotate.aprs2.net`), port (`14580`), callsign (`K2GIA-7`), passcode (`16025`) — are filled in correctly and match what works fine on other K2GIA stations. Not yet root-caused. Practical implication: **K2GIA-7 currently only receives over RF, not APRS-IS**, until this is resolved or reconnected successfully.

This matters for cross-node testing: a message sent to K2GIA-7 from an Internet-only node (like K2GIA-5/APRSdroid) will not arrive while this is disconnected, since there's no RF path from an internet-only sender and no APRS-IS path into K2GIA-7 either. For a reliable test in the meantime, send from K2GIA-1 (Graywolf), which transmits over RF regardless of this issue. See `k2gia-5-aprsdroid-reference.md` for the fuller cross-node messaging caveat.

**Next step when revisited:** re-check KISSLink's IS tab on K2GIA-7 — retry Connect, check Basic/Verbose log for a connection error, confirm no typo crept into the passcode/callsign fields specifically on that screen (separate from the Settings tab identity fields).

## Cross-band bridging: 2m APRS (K2GIA-1) ↔ 433MHz LoRa APRS (K2GIA-10)
Evaluated 2026-08-23 whether Reticulum could bridge K2GIA-1 (2m/VHF AFSK APRS) and K2GIA-10 (433MHz LoRa APRS) into one unified network.

**Ruled out: Reticulum does not understand APRS packets at all.** It's a mesh networking stack with its own packet format and addressing scheme — it can carry arbitrary data (including APRS payloads if manually wrapped), but it has no native APRS awareness, no digipeating logic compatible with APRS conventions, and no path to bridging two APRS-speaking stations transparently. Using it here would mean building a custom encapsulation layer on both ends, not using an off-the-shelf bridge.

**Real options, if this is ever pursued (not implemented, reference only):**
- **APRX** — a well-established APRS digipeater/igate/bridge software package, explicitly designed for exactly this kind of multi-port bridging (already referenced as the bridge tool in the earlier VHF↔LoRa bridge article found during the CA2RXU research, `f4fxl.org` — see `td-h9-odmaster-aprs-messaging-bug.md` background research). Would need its own dedicated host/Pi.
- **HAM-router** — another APRS-aware routing/bridge tool, less explored than APRX.
- **APRStac** — mentioned as a third option; not evaluated in detail this session.

None of these are set up or scheduled — this is a "worth knowing the landscape" entry, not an active project. If pursued later, worth deciding (same as the previously-noted APRStastic Meshtastic↔APRS bridge decision in `lora-aprs-reference.md`): which spare Pi to dedicate, and whether combining multiple bridge/gateway roles on one small host makes sense versus keeping them separate.
