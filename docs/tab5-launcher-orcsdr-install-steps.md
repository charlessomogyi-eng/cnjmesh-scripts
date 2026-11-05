# Tab5: Launcher, OrcSDR and the Tab5 Meshtastic console, step by step (draft Nov 5 2026)

Written the morning of Thu Nov 5 2026 so Charlie can follow it this afternoon. Companion to `docs/tab5-c6l-tracker.md`. Nothing here has been flashed yet.

Tags: [V] verified on a page I read · [S] from the tracker or Charlie · [?] not documented, we find out on the day.

Working style: one step at a time, Charlie reports what the screen shows after each step. Every command says where it runs and whether it finishes on its own.

## What goes where

| Item | Where it is | Status |
|---|---|---|
| Tab5 factory backup `tab5-factory-backup.bin` | laptop, Downloads | done [S] |
| `OrcSDR-Tab5-v0.5.0-beta.1.bin` | laptop, Downloads, SHA256 matched the release page | ready [S] |
| Tab5 Meshtastic app `tab5_meshtastic_v2.bin` | built by the GitHub workflow "Build Tab5-Meshtastic" | **not built yet**, Charlie must press Run workflow |
| M5 Launcher for Tab5 | latest 2.10.0 [V, README changelog: Tab5 OTA crash fix in 2.10.0, keyboard support, mass storage 2.6.7] | not downloaded; Tab5 file name and flash address [?] |
| microSD cards (32 GB, two) | arrived Nov 3 [S] | not formatted |
| C6L (KPNM) | configured Nov 1 (US, Long Fast, four secondary channels, Bluetooth fixed PIN 123456) [S] | ready for pairing |

## Step A. Build the Tab5 Meshtastic app (GitHub, 2 minutes of work)

1. GitHub, repo `charlessomogyi-eng/cnjmesh-scripts`, tab **Actions**, workflow **Build Tab5-Meshtastic**, button **Run workflow**.
2. Wait for it to finish. Green check: download the artifact (`tab5_meshtastic_v2.bin` and `SHA256SUMS.txt`); it is kept 3 days. Red X: paste the last lines of the log and Claude fixes the workflow.
3. Claude checks the file size against Launcher's app limit (1,638,400 bytes; the app's size-optimized build was 1,604,192 [S, tracker]).

## Step B. Prepare the microSD card (laptop, Windows)

Launcher wants **SDHC, FAT32, MBR partition table (not GPT)** [V, Launcher README]. exFAT and larger cards are said to work since 2.8.0, but small FAT32 is recommended [V].

1. Put the card in the laptop. Identify it carefully (a wrong disk would be wiped). In PowerShell (finishes on its own, changes nothing):

```
Get-Disk | Format-Table Number, FriendlyName, Size, PartitionStyle
```

2. Charlie pastes the output. Claude says which line is the card and whether it is MBR or GPT **before** anything is formatted.
3. If it is MBR: File Explorer, right-click the card, Format, file system FAT32, Quick Format. If it is GPT, Claude gives the extra steps then (this step can erase the wrong disk, so it waits for Charlie's paste).
4. Copy `OrcSDR-Tab5-v0.5.0-beta.1.bin` and `tab5_meshtastic_v2.bin` onto the card. [?] Whether Launcher expects a particular folder; the docs say only that its OTA menu installs binaries "from your SD card". Put both files in the card's top level first.

## Step C. Put Launcher on the Tab5

1. Tab5 battery in, USB-C to the laptop, Chrome. Backup already exists (`tab5-factory-backup.bin`).
2. Easiest route [V that it exists]: the Launcher web flasher, https://bmorcelli.github.io/Launcher/ . [?] Whether it lists the Tab5 and what it flashes. Select the Tab5 entry, connect to the serial port (Tab5 showed as COM16 before; the number can change), flash.
3. Fallback with esptool if the web flasher does not list the Tab5 [S, tracker: full flash at 0x0 from the Launcher release; the README does not confirm 0x0, so Claude re-checks first]. From the laptop, finishes on its own (file name to be filled in after Charlie reads the Releases page):

```
py -3.13 -m esptool -p COM16 write-flash 0x0 "$env:USERPROFILE\Downloads\Launcher-TAB5-FILE-NAME.bin"
```

4. Unplug and replug, or reset. The Tab5 should boot into Launcher. Charlie describes the screen.
5. Rollback if anything goes wrong: restore the factory image (same esptool command with `tab5-factory-backup.bin`).

## Step D. Install OrcSDR from the card

1. Card in the Tab5. In Launcher choose the SD option, select `OrcSDR-Tab5-v0.5.0-beta.1.bin`, install, run it.
2. Plug in the NESDR if available, antenna on. First test: FM broadcast. [?] Whether OrcSDR runs under Launcher at all (unconfirmed); if it does not, fallback: flash OrcSDR directly with esptool at 0x0 (this overwrites Launcher), NESDR unplugged, battery in.
3. Known problem: after a custom app runs, Launcher may lose Wi-Fi or not detect the Tab5 keyboard (issue #440, "Fixed on Beta") [S, tracker]. SD installs do not need Wi-Fi.

## Step E. The Tab5 Meshtastic console (after OrcSDR)

1. Install `tab5_meshtastic_v2.bin` from the same card the same way. The app needs the battery connected when flashing [S, tracker].
2. C6L (KPNM) powered from its own USB-C supply, Bluetooth on, fixed PIN 123456. In the app, pair over Bluetooth and send a CentralNJ message from the keyboard. Limits [S]: channel chat only, no direct messages, no radio configuration menus.
3. Switching apps: the app's EXIT puts the Tab5 to sleep; reset brings Launcher back; launch the other app from Launcher [S, tracker]. [?] Launcher's own docs do not describe the way back.

## Later idea, not today

Make OrcSDR's LoRa Monitor read the private channels (CentralNJ, SJMesh, KPCOMMS, KPTESTING) by adding their keys. See the Nov 5 note in the tracker. The keys are not in the repo.
