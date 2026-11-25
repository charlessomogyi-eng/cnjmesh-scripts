# NIFOG Reference Notes

Source: CISA National Interoperability Field Operations Guide (NIFOG) v2.0, August 2021
(cisa.gov/safecom/field-operations-guides). Page numbers below are the printed NIFOG pages.
Frequencies are stable but the guide is five years old; re-check anything critical.

Added 2026-11-24. This is the standard national reference for emergency and
interoperability channels, useful alongside the Middlesex County RACES/AUXCOMM goal.

## What we use it for

- CHIRP files built from its tables: `codeplugs/ham_calling_simplex_NIFOG_CHIRP.csv`,
  `codeplugs/GMRS_NIFOG_CHIRP.csv`, `codeplugs/MURS_NIFOG_CHIRP.csv`
- HF reference for when an HF rig exists (below)
- It also lists public-safety and federal interoperability channels (VCALL, UCALL, etc., pp. 24+).
  These are NOT programmed for transmit anywhere in this repo: a ham license does not
  authorize transmitting on them (NIFOG p.2 and the "Conditions for Use" pages 19-22 explain
  who may). A ham HT may listen to them, but do not add transmit-enabled entries.

## Amateur calling frequencies (p.106)

FM simplex calling uses carrier squelch (no tone).

| Band | MHz | Mode |
|---|---|---|
| 2 m | 146.520 | FM simplex (national calling) |
| 2 m | 144.200 | SSB |
| 70 cm | 446.000 | FM simplex (national calling) |
| 70 cm | 432.100 | CW/SSB |
| 6 m | 50.125 SSB, 52.525 and 52.540 FM simplex, 50.620 digital | |
| 1.25 m | 222.100 | CW/SSB |

HF: 3.885 AM (80 m), 7.290 AM (40 m), 14.286 AM (20 m).

## Amateur emergency / HF (pp.104-105)

Not available to public safety agencies; a valid ham license is required to transmit.

- Emergency Center of Activity (stations gather within +/-20 kHz): 3750 or 3985 LSB, 7060,
  7240 or 7290 LSB, 14300 USB, 18160 USB, 21360 USB
- Hurricane Watch Net: 14325 kHz USB. Maritime Mobile Service Net: 14300 kHz USB
- National Hurricane Center (W4EHW) during hurricanes: 14325 USB primary, 7268 LSB alternate
- 60 m channels (General, Advanced, Extra; secondary basis; 100 W ERP; USB; one signal at a
  time): carrier 5330.5, 5346.5, 5357.0, 5371.5, 5403.5 kHz (center 5332.0, 5348.0, 5358.5,
  5373.0, 5405.0)
- ALE voice channels (netcall HFL) and text channels (netcall HFN) are listed on p.105

General class (Charlie) has privileges on all of the above HF channels.

## GMRS / FRS / MURS (pp.114-117), for the Retivis RT76P GMRS radios

- **GMRS needs an FCC license; FRS and MURS do not.** GMRS and FRS share channels 1-22.
- GMRS: ch 1-7 (462.5625-462.7125) 5 W max; ch 8-14 (467.5625-467.7125) 0.5 W max, handheld
  only; ch 15-22 (462.550-462.725) main channels, 50 W max, repeater input is +5 MHz (467.xxx).
  GMRS equipment must be certified under FCC Part 95, Subpart E.
- FRS: ch 1-22 same frequencies; 2 W max (0.5 W on 8-14). Equipment must be FRS certified.
- MURS (no license): 151.820, 151.880, 151.940 (11.25 kHz wide) and 154.570, 154.600
  (20 kHz wide); 2 W max; Part 95 certified radios only. A ham radio such as a UV-5R is
  not MURS-certified, so receive only.
- NIFOG tip for travelers on GMRS ch 20: nationwide travel assistance, and if CTCSS is
  required, try 141.3 Hz.
- None of these channels may be used by the NMAC on wildfire incidents.

Do not transmit on GMRS with a ham-only radio, or load ham repeaters into a Part 95 GMRS radio.

## Power limits (p.113)

47 CFR 97.313: use the minimum power needed; never over 1.5 kW PEP. 60 m is 100 W PEP ERP;
30 m is 200 W PEP.
