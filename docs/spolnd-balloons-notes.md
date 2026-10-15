# SP0LND balloons (Poland) — notes for the future LoRa APRS pivot

Filed Oct 15, 2026 from Charles's Discord screenshots (a `#general` channel, 40 online, most likely the LoRa APRS Discord, **[I]**: the server name is not visible in the screenshots). Everything below is what other people said in Discord, so it is hearsay (**[S]**, unverified by us). Screenshots are not stored in the repo.

## What was said

**SQ2CPA (Poland, grid JO83TI), Oct 14, ~8:53 AM:**
- Runs the "SP0LND" balloons and wants people to be aware of them and how they can help.
- The balloons support **two-way communication** with TX enabled and **messages from APRS-IS to RF**.
- They fly fairly regular routes, for example across North America.
- At that time: 4 balloons in the air with continuously known positions (an extra WSPR beacon on 15 m provides that), plus 6 older-generation balloons without the latest functionality.
- The balloons have a range of capabilities that can be **activated remotely via the APRS-IS network and via local stations with proper configuration (not RX-only iGates)**.

**SQ2CPA, Oct 14, ~11:36 AM:** hoped SP0LND-9 and SP0LND-1 would handshake, with SP0LND-9 beacons repeated via SP0LND-1. There was no network coverage in that region, so he has to wait until SP0LND-1 returns to Europe to fetch contact information from its local storage. He describes it as "a completely different kind of fun with balloons when you can manage them, redirect packets." A shared map showed SP0LND-9 and SP0LND-1 over northern Canada (Hudson Bay area).

**Oct 15 thread:**
- A US ham (N7UV) said he is planning a balloon-specific base station, and wondered about a link between two radios at a site so balloon packets get injected into the main LoRa network (SF settings differ).
- SQ2CPA: "Just one good station on **433.775 300bps** is enough," because he can then QSY the balloon to a local frequency/speed, and this "could be done automatically (and remotely)."
- N7UV asked: "Do you mean you will be able to control my station remotely?" (no answer visible in the screenshots).

Two of Charles's own earlier replies and one question from K0GR addressed to Charles were cut off in the screenshots, so their content is not recorded here.

## Why it might matter to CNJ Mesh (all [I], my reading, not decided)
- **433.775 MHz is the LoRa APRS frequency.** K2GIA-10 (LoRa APRS digipeater) is on it, and K2GIA-9 is the mobile tracker. A balloon passing over New Jersey on 433.775 could be heard by them. **Not tested.**
- **APRS-IS to RF needs an iGate that transmits.** K2GIA-10 currently has APRS-IS **disabled by design** (since Aug 28), so as configured it is not that kind of station. K2GIA-1 (Graywolf, 2 m) is the other iGate. Whether either should do more is Charles's decision.
- **Remote control raises a safety question** that N7UV already asked: what exactly could a remote operator change on a station, and who authorizes it? Understand that before opting any CNJ station in.

## Things to track / questions for later
- Follow SP0LND-1 and SP0LND-9 (and other SP0LND-* callsigns) on aprs.fi or similar for passes near the Northeast.
- Ask SQ2CPA what "remote activation" does on a ground station, which frequencies and modes it uses, and what proper iGate configuration means.
- Decide whether K2GIA-10 could ever safely contribute (needs a listen-only test first), and confirm any rules that apply to a ground station that transmits to a balloon.
