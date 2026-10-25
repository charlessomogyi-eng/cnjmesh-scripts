# HT Radio Programming (K2GIA)

Handheld radio programming notes, codeplugs and status. Kept separate from the
mesh/Pi documentation. Last updated: 2026-10-25.

## Folder layout

- `README.md` - this file: inventory, status, workflow, next steps
- `codeplugs/` - channel lists as CHIRP CSV files (one per radio, plus shared lists)
- `images/` - untouched CHIRP `.img` backups, read from each radio **before** any upload
- `W2NJR.md` - notes on the W2NJR linked repeater system and what changed

## Radio inventory

| Radio | CHIRP model | Role | Status |
|---|---|---|---|
| Baofeng UV-5R M (5RM) | 5RM | APRS: K2GIA-1 Graywolf home iGate (Digirig) | Dedicated, do not reprogram |
| TIDRADIO TD-H9 | TD-H9 | APRS: K2GIA-7 mobile | Dedicated, do not reprogram |
| Baofeng AR-5RM | 5RM | Candidate main voice HT | Cable connected 2026-10-25, first CHIRP read pending |
| Baofeng UV-5R (#1) | Baofeng UV-5R | Candidate backup voice HT | Condition unknown |
| Baofeng UV-5R (#2) | Baofeng UV-5R | Candidate backup voice HT | Condition unknown |

GMRS (not ham, separate from the ham pool above):

| Radio | CHIRP model | Role | Status |
|---|---|---|---|
| Retevis RT76P x2 (FCC ID 2ASNSRT76, BL43 7.4V 1400 mAh battery) | Retevis RT76P | GMRS handhelds | Not yet tested or read. Serial prefix 2103 suggests ~March 2021 manufacture, so inspect the batteries for swelling before charging. |

Do not load ham repeater lists (W2NJR etc.) into the GMRS radios. A ham license does not
cover GMRS; transmitting on GMRS needs its own FCC GMRS license.

Open question: one of the two 5RM units was reportedly replaced by the vendor after
a fault. Which one was faulty is not yet known. Check for a serial/date label under the
battery, then test read, charge hold and transmit. Do not trust the older unit as a voice
radio until it passes.

## Workflow (applies to every radio)

1. Charge to at least 50% and seat the programming cable fully (click-in).
2. Find the COM port in Device Manager, then in CHIRP-next: Radio > Download from Radio.
3. Immediately File > Save As an untouched backup into `images/`, named
   `<model>_<YYYY-MM-DD>_original.img`.
4. Export the channel list as CSV (File > Save As > CSV) into `codeplugs/`.
5. Review the CSV: tones, offsets, duplicates, stale repeaters, power and scan settings.
6. Merge in the shared lists, upload to the radio, and verify with a receive and transmit test.

Never upload to a radio before its original image is backed up.

## Software

- **CHIRP-next** (official, chirpmyradio.com): the only actively maintained CHIRP build.
  Use it for the first read and backup of every radio.
- **NewChirp** (newchirp.net, GitHub ricktek954/newchirp, led by Rick Lopez): separate
  community project that bundles CHIRP's drivers in a new interface, plus Android.
  Early and still seeking testers. Its write step is locked until the radio has been read in
  the same session. Plan: try it alongside CHIRP-next, fall back to CHIRP-next if it misbehaves.
  CSVs work in both.

## Shared codeplugs

- `codeplugs/W2NJR_analog_CHIRP.csv` - all 15 analog W2NJR system repeaters, built from
  w2njr.net on 2026-10-24. Tone 141.3 Hz on every machine (TX tone set). Includes
  the two W2LI Murray Hill repeaters (linked for nets only) and the W2FCC Springfield UHF.

## HF digital modes (reference, no radio yet)

Interest in FT8, JS8 and JTTY on 20 m (General class data segment covers all three).
Dial frequencies on 20 m: FT8 14.074, JS8 14.078, JTTY 14.090 (USB). Suggested JTTY
dials: 160 m 1.838, 80 m 3.575, 40 m 7.090, 6 m 50.160, 2 m 144.160 (preliminary).
JTTY is new (WSJT-X 3.2.0-rc1, announced 2026-09-23; 3.3.0 betas on github.com/WSJTX/wsjtx).
A candidate entry-level rig is the Pebble HF (20 m QRP kit; digital modes need an external
USB sound card adapter). No purchase decision made.

## Next steps

- [ ] Photograph UV-5R #1 label clearly and identify the model
- [ ] Charge and power-test all three candidate radios
- [ ] First CHIRP-next read of the AR-5RM, save `.img` backup, export CSV
- [ ] Review the AR-5RM CSV, merge W2NJR channels, upload, verify on Martinsville 147.285
- [ ] Repeat for the two UV-5Rs
- [ ] Remove stale W2NJR entries from any old images (e.g. West Orange 440.050)
