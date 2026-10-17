# SDRangel ChirpChat (LoRa) Demodulator — Quick Reference for CNJ

Created 2026-10-16. Condensed in my own words from the plugin's README (github.com/f4exb/sdrangel, `plugins/channelrx/demodchirpchat/readme.md`). Tags: **[V]** = taken from that README or from Charles's screenshot; **[S]** = my suggestion, untested on Charles's setup. Charles's machine: Windows 10 laptop, SDRangel 7.22.9, Nooelec RTL-SDR (model not yet confirmed).

## What this is
SDRangel's **ChirpChat Demodulator** is its LoRa decoder (the plugin is "LoRa-inspired" with LoRa-compatible decoding from community reverse engineering) **[V]**. The README says it is meant for experimentation, not production, and that it was verified mostly at SF11/SF12 with DE=2 (RN2483 transmitters; not tested with SX127x) **[V]** — so expect it to need tuning, and SF10 at 500 kHz is outside what the author verified.

## What Charles's Oct 16 screenshot showed [V]
- Source: **FileInput** (playing a recorded file at 48k), not a live RTL-SDR. For live reception a Rx device (RTL-SDR) must be added.
- ChirpChat settings: BW **3125 Hz**, SF **7**, DE **0**, Pre **8**, scheme LoRa, HDR ticked, FFTW Rec, waterfall around 434.98–435.02 MHz. These are leftover/generic values, nowhere near CNJ's.

## Target values for CNJ MeshCore
| Control | CNJ value | Note |
|---|---|---|
| Device centre frequency | 910.525 MHz | set on the RTL-SDR device, not the demod |
| Device sample rate | >= 1 MS/s (try 1.0–2.4 MS/s) | README: baseband must be at least 2x the chirp bandwidth [V]; RTL-SDR tops out near 2.4 MS/s [S] |
| BW | **500 kHz** | slider has fixed steps; its maximum depends on the sample rate [V] |
| SF | **10** | |
| DE (distance enhancement) | try **2** first, then 0 | README recommends non-zero DE [V]; DE=2 with SF10 is the safe first try [S] |
| FEC parity (coding rate) | **1** (CR 4/5) | mapping: 4/5=1, 4/6=2, 4/7=3, 4/8=4 [V] |
| Expect header (HDR) | on | LoRa explicit header [S] |
| Payload CRC | on | [S] |
| Preamble chirps (Pre) | unknown — default 8 may be wrong | Meshtastic uses 16; MeshCore value **not verified** [S] |
| Sync word | unknown for MeshCore | Meshtastic is 0x2B per the README [V]; MeshCore's value not verified |
| FFT window | Rec (rectangular) | default for frequency detection [V]; Kaiser is the suggested alternative [V] |
| Coding scheme | LoRa | |

For comparison, README Meshtastic presets: LONG_FAST SF11 4/8 250 kHz DE on; MEDIUM_SLOW SF10 4/7 250 kHz DE on; SHORT_FAST SF9 4/7 250 kHz DE off [V]. LoRa APRS (433.775 MHz, SF12, BW 125 kHz, per `lora-aprs-reference.md`) is closer to what the author tested (SF12) — a good first target to prove the setup works.

## Other useful controls [V]
- **Frequency shift (Delta f):** offset in Hz from the device centre; nudge it until the "de-chirped" power rises.
- **De-chirped power / SNR readouts:** a rise in channel power means a LoRa signal is detected. Decode errors become likely below ~4 dB SNR.
- **De-chirped spectrum (bottom):** a sharp vertical stripe pattern means chirps are lining up; a smear means wrong SF/BW.
- **Message window:** LoRa lines show timestamp, sync word, levels, header/payload FEC and CRC status (green good, red bad), and a hex dump with a "TXT" translation.
- **UDP output:** can forward decoded packets to another program (127.0.0.1, port 9999 in the screenshot).
- **Invert chirp ramps:** only if the signal is down-chirped (standard LoRa is up-chirp).

## Caveats
- MeshCore and Meshtastic payloads are encrypted; a decoder shows that packets exist (timing, level, header) but normally not readable text. LoRa APRS packets are unencrypted text.
- A nearby node (your own KPR/KPC) will be far stronger than a distant one: test with your own transmitter close to the SDR, with its antenna attached and the gain not maxed.

## Other write-ups (not tested by me)
- rtl-sdr.com, "Decoding the LoRa IoT Protocol with an RTL-SDR": https://www.rtl-sdr.com/decoding-the-iot-lora-protocol-with-an-rtl-sdr/
- rtl-sdr.com, "Decoding Meshtastic in Realtime with an RTL-SDR and GNU Radio": https://www.rtl-sdr.com/decoding-meshtastic-in-realtime-with-an-rtl-sdr-and-gnu-radio/
- rtl-sdr.com, "Transmitting and Receiving Meshtastic with SDR": https://www.rtl-sdr.com/transmitting-and-receiving-meshtastic-with-sdr/
