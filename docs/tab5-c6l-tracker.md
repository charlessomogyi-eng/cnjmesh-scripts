# M5Stack Tab5 + Unit C6L — Tracker

**Owner:** Charlie (K2GIA) · **Created:** 2026-10-22 · **Last researched:** 2026-10-31

Living tracker for the M5Stack **Tab5** (ESP32-P4 tablet) and **Unit C6L** (ESP32-C6 + SX1262 LoRa node).
Update the status board and checklist as things arrive and get tested. Facts below come from the linked
sources; anything I could not confirm is marked **(unverified)**. Re-check version numbers on GitHub before
installing, because several of these projects move weekly.

---

## 0. Pick up here (written Sat 2026-10-31, 11 PM ET)

**Working style for this project (Charlie):** plain text, one step at a time, each shell command in its own code block saying which machine it runs on and whether it finishes on its own or needs Ctrl+C, no multiple-choice prompts, verify before suggesting, update and push this repo directly (never ask him to run git). He uses Windows PowerShell on his laptop; the Tab5 and C6L are on his bench; he uses the Android Meshtastic app but does **not** want to depend on a phone for the C6L.

**Goal:** the Tab5 with its keyboard is the screen and keyboard for the C6L (his mobile Meshtastic node, on the CentralNJ channel), and also runs OrcSDR, switching between them with M5 Launcher. The C6L is mobile, so it does not need to run 24/7.

**Where things stand**
- Tab5: factory flash **backed up** to `tab5-factory-backup.bin` in the laptop's Downloads (16 MB, sections 10 and 11). esptool 5.6.0 works through `py -3.13` (the default `py` is a free-threaded Python that cannot install it). Tab5 shows as **COM16** over USB-C (the number can change). **OrcSDR is NOT flashed**: Charlie chose to wait for the microSD cards so Launcher goes on first.
- `OrcSDR-Tab5-v0.5.0-beta.1.bin` is in Downloads and its SHA256 matched the release page. The M5Burner share link `JXFU4H` is stale (v0.3.0-beta.2); do not use it.
- Two 32 GB microSD cards arrive **Monday 2026-11-02** (one for the Tab5, one spare for the cnjmesh3 Pi). Cards must be FAT32 with an MBR partition table for Launcher.
- C6L: unboxed, both whips attached (the included LoRa whip is 868 MHz, wrong band for the US; swap for the Alfa 915 or a 915 stubby after a NanoVNA SWR check), Grove cable included, **USB-C port is on a long edge**. Not powered or flashed yet. No USB cable came in the box.
- Tab5 Meshtastic app: audited tpklge/Tab5-Meshtastic at fcdfe23 (section 6b). Build workflow `.github/workflows/build-tab5-meshtastic.yml` is pushed but **has not been run**: Charlie must press Run workflow in the repo's Actions tab (the session's `gh` token is invalid, so Claude cannot trigger it or read the logs). The artifact lasts 3 days.

**Next steps, in order**
1. Charlie presses **Run workflow** (GitHub, cnjmesh-scripts, Actions, "Build Tab5-Meshtastic"). If it fails, he pastes the tail of the log and Claude fixes the workflow. If it passes, he downloads the artifact (`tab5_meshtastic_v2.bin` plus SHA256SUMS.txt) and Claude checks the size against Launcher's 1,638,400-byte app limit.
2. **C6L first flash (independent of everything else):** antenna on first, USB-C data cable to the laptop, list serial ports with `Get-PnpDevice -PresentOnly | Where-Object { $_.Class -eq 'Ports' } | Format-Table FriendlyName, Status`, then follow section 5 (hold the side button about 3 s until the LED is red, Meshtastic web flasher in Chrome, M5Stack then Unit C6L, full erase, replug). Set region US, a name, the CentralNJ channel and key (from the laptop's Meshtastic web client over USB, no phone needed). For the Tab5 app over Bluetooth, note the C6L's Bluetooth PIN mode (the app's author used fixed PIN 123456).
3. **Monday, cards arrive:** put Launcher on the Tab5 (full flash at 0x0 from Launcher's release; stock 2.8.0 may not detect the Tab5 keyboard, and issue #440 describes Wi-Fi/keyboard problems after running custom apps, "Fixed on Beta"). Then install the Tab5 Meshtastic `.bin` and OrcSDR from the SD card and see whether OrcSDR runs under Launcher (unconfirmed). If OrcSDR will not run under Launcher, fall back to flashing it with `py -3.13 -m esptool -p COM16 write-flash 0x0 "$env:USERPROFILE\Downloads\OrcSDR-Tab5-v0.5.0-beta.1.bin"` (NESDR unplugged, battery in; this overwrites Launcher) and restore the factory image from the backup with the same command if ever needed.
4. Pair the Tab5 app with the C6L over Bluetooth and try a CentralNJ message from the keyboard. Known limits of that app: channel chat only (no direct messages, no radio configuration menus), no GPS on either device.
5. Later and optional: Grove UART or USB-host links, a car mount (1/4-20 male stud, section 3 and the Oct 30 note), the NESDR test with FM first (OrcSDR), checking antenna connector gender (Q3).

**Decisions made (Charlie)**
- C6L = mobile node on Meshtastic; MeshCore can be tried later.
- Wait for the microSD cards so Launcher is installed first, to avoid flashing OrcSDR twice.
- Tab5 + keyboard is the screen; no phone dependency for the C6L.
- Best-known link for the Tab5 app is Bluetooth (the author tested a Unit C6L that way). The C6L gets its own USB-C power (power bank or car); the Tab5's USB-A port does not power it with this app (section 6b power note).

**Open questions:** does the build compile; does OrcSDR run under Launcher; does stock Launcher work with the Tab5 keyboard; does the C6L accept power through its Grove pin (undocumented); the Tab5 app's TX/RX polarity for the Grove route (the project says verify before use).

## 1. Status board

| Item | Status | Notes |
|---|---|---|
| M5Stack Tab5 | **Arrived 2026-10-28**, still factory sealed in photo | **Kit with battery** (K145, includes NP-F550), confirmed by owner 2026-10-22. See power notes. |
| M5Stack Unit C6L (U202) | **Arrived 2026-10-28**, unboxed in photo | Ships with two SMA whips (868 MHz LoRa + 2.4 GHz). |
| Tab5 Keyboard (A164) | **Arrived 2026-10-30** (sealed box in photo) | 70-key, plugs into Tab5 Ext.Port1. |
| Nooelec **NESDR SMArt v5** | On hand | Confirmed from owner's photos 2026-10-22 (FCC ID 2A8GD-SMArt-V5, "v5" printed on case, SMA input). Listed as accepted for FT8 in OrcSDR v0.4.0-beta.1. |
| Antennas on hand | Muzi whip, Alfa 915 MHz (~6-7 in), SMA pigtails | Alfa connector type and gender not yet checked. |

---

## 2. Checklist and open questions

### Before it arrives
- [x] **Q1. Resolved 2026-10-22:** owner bought the Tab5 **with battery** (Kit, NP-F550). That matters because one
      Tab5-SDR author says the Tab5 browns out on USB power alone under the dongle's ~300 mA load and needs its
      internal battery connected. Keep the battery installed when running the SDR.
- [x] **Q2. Resolved 2026-10-22:** the dongle is a **Nooelec NESDR SMArt v5** (owner's photos). OrcSDR's documented
      receivers are the RTL-SDR Blog V4, V4L and V3c, plus the NESDR SMArt V5. The V5 passed FT8 acceptance in
      v0.4.0-beta.1 (40 m, 7.074 MHz, MLA-30+ antenna; valid decodes after tightening the antenna connection).
      Earlier beta7 notes called V5 support experimental, so expect rough edges. Note that the Blog V4's built-in
      HF upconverter (used by the 9a3zi project) is a V4 feature and is not described for the V5.
- [ ] **Q3.** Alfa 915 MHz antenna connector: SMA or RP-SMA? Check against the C6L's LoRa port and the
      pigtails. Sources conflict on the C6L's own antenna connector (M5Stack's page and OpenELAB say RP-SMA,
      retailer listings say SMA with female pin), so check the gender with the hardware in hand.
- [x] **Q4.** RESOLVED Oct 22 (Charlie): C6L starts on Meshtastic, as his mobile node. MeshCore can be revisited later (reflash is cheap).
- [x] microSD for the Tab5 (OrcSDR uses it for captures and data packs; also for Launcher): **two 32 GB cards ordered 2026-10-31** (one for the Tab5, one as a spare for the cnjmesh3 Pi). M5Stack's Tab5 microSD page says format FAT32; Windows only formats FAT32 natively up to 32 GB, so 32 GB was chosen. [I] reasoning, not a documented size limit.
- [ ] Short USB-A extension cable for the dongle (recommended by the 9a3zi tab5-SDR project).
- [ ] Decide on an HF antenna (long wire plus 9:1 unun is the usual start) and a 1090 MHz antenna for ADS-B.
- [ ] V5 tips from the OrcSDR FT8 notes: tighten the SMA antenna connection firmly, and use manual gain if auto-gain clips.

### On arrival
- [x] Display driver revision: back-panel diagram in Charlie's Oct 28 photo is labeled ST7121 (1280x720), matching the newest revision. [S: read from a photo]
- [ ] Boot the factory firmware first and confirm the screen, touch, battery and charging work.
- [ ] Install OrcSDR (section 4). Test FM first, then the other dashboards.
- [ ] Flash the C6L (section 5). Attach antennas **before** powering it.
- [ ] Set region to **US** on the C6L (915 MHz).
- [ ] Log results and problems in section 9.

---

## 3. Tab5 reference

**Docs:** [M5Stack Tab5 page](https://docs.m5stack.com/en/core/Tab5)

### Hardware
- ESP32-P4 (dual RISC-V at 360 MHz + LP core), 16 MB flash, 32 MB octal PSRAM.
- ESP32-C6-MINI-1U coprocessor for Wi-Fi 6 (over SDIO), also Thread/Zigbee per the spec table.
- 5 in IPS, 1280x720, MIPI-DSI. 2 MP camera. ES8388 codec, dual mics with echo cancellation, 1 W speaker, 3.5 mm jack.
- BMI270 IMU, RX8130CE RTC (supercap backup), INA226 power monitor.
- **USB-A host** (5 V output, switchable) and **USB-C OTG** (also charging and download).
- microSD slot, RS-485, M-Bus rear connector, side GPIO header, HY2.0-4P Grove port.
- External Wi-Fi antenna port (MMCX). The spec table says 2 ports, the feature list says 1. **(unverified)**
- 128 x 80 x 12 mm, ~120.9 g. Kit with battery is 26.7 mm thick and ~217.6 g. Tripod nut (1/4-20) on the side.
- Built-in antenna is switchable to external.

### Display and touch revisions
| Date | Change |
|---|---|
| 2025-05-09 | Initial release (ILI9881C display + GT911 touch) |
| 2025-10-14 | Display changed to integrated ST7123 |
| 2026-04-28 | Display driver IC changed from ST7123 to ST7121 |

Older firmware may not work on newer units. Rebuild with M5Unified 0.2.23+ and M5GFX 0.2.30+ per M5Stack.
ESPHome did not support the newer display parts in the review I found.

### Power and USB gotchas (from M5Stack docs unless noted)
- Shut down before removing power or the battery. If power is cut abruptly, wait 5 seconds before powering on or
  the IMU may fail to initialize.
- The charger (IP2326) charges only while the Tab5 is powered on. Below 6 V the battery enters protection mode:
  remove the battery, reset, reinstall, then charge via USB-C. Charging starts with a low trickle current.
- Battery runtime is about 6 hours under M5Stack's test conditions (50% brightness, Wi-Fi on).
- With no battery attached, USB/VBUS can read about 4.3 V and show a false 0% battery
  (per the [M5Dashboard reference](https://github.com/XueshiQiao/M5Dashboard/blob/main/docs/M5Stack-Tab5-Reference.md)).
- M5Unified once reported battery current with the sign inverted; check
  [issue #173](https://github.com/m5stack/M5Unified/issues/173) for the fix version.
- Bottom of the unit gets warm (about 39 C after 30 minutes in one review).
- Download mode: hold Reset about 2 seconds until the green LED flashes rapidly.
- **The Tab5 has no LoRa radio.** Its M-Bus and stamp pads are for add-on modules.
  See the [Meshtastic device-ui request](https://github.com/meshtastic/device-ui/issues/309): no LoRa stamp
  existed at the time, a UART AT-command LoRaWAN module won't work with Meshtastic (needs an SPI-connected LoRa chip),
  and one user reported the discontinued LoRa868 module worked. **(forum claim, unverified)**

### Firmware and development
- Restore factory firmware: [guide](https://docs.m5stack.com/en/guide/tab5/restore_factory) (M5Burner, download mode).
- Restore the C6 Wi-Fi firmware: [guide](https://docs.m5stack.com/en/guide/tab5/c6_wifi_restore). Needs a USB-TTL
  downloader (M5Stack's ESP32 Downloader). The page gives no version number.
- ESP-IDF factory demo: [M5Tab5-UserDemo](https://github.com/m5stack/M5Tab5-UserDemo),
  [build guide](https://docs.m5stack.com/en/esp_idf/m5tab5/userdemo).
- Arduino: [M5Unified](https://github.com/m5stack/M5Unified) and [M5GFX](https://github.com/m5stack/M5GFX),
  [quick start](https://docs.m5stack.com/en/arduino/m5tab5/program).
- UIFlow2 (block/MicroPython): [quick start](https://docs.m5stack.com/en/uiflow2/Tab5/program).
- Board support packages: [Espressif BSP](https://components.espressif.com/components/espressif/m5stack_tab5),
  [ESPP BSP](https://components.espressif.com/components/espp/m5stack-tab5).
- ESPHome / Home Assistant: [device page](https://devices.esphome.io/devices/M5Stack-Tab5/),
  [HA community thread](https://community.home-assistant.io/t/m5stack-tab5/888543).
- Apache NuttX port (partial): [NuttX docs](https://nuttx.apache.org/docs/latest/platforms/risc-v/esp32p4/boards/esp32p4-tab5/index.html).
- CAD / structure files: [M5_Hardware repo](https://github.com/m5stack/M5_Hardware/tree/master/Products/C145_Tab5/Structures).
- M5Burner is Intel-only on Mac per one review. Not an issue on a Windows laptop.

### Reviews
- [CNX Software part 1 (teardown)](https://www.cnx-software.com/2025/05/14/m5stack-tab5-review-part-1-unboxing-teardown-and-first-try-of-the-esp32-p4-and-esp32-c6-5-inch-iot-devkit/)
  and [part 2 (ESP-IDF, Arduino)](https://www.cnx-software.com/2025/05/18/m5stack-tab5-review-getting-started-esp32-p4-esp-idf-framework-arduino-ide/)
- [Tao of Mac review](https://taoofmac.com/space/reviews/2026/07/18/1920): good value for prototyping, USB-A host
  can run a UVC capture device as a field monitor, ESP-IDF recommended over Arduino.

### Keyboard (A164)
[Docs](https://docs.m5stack.com/en/tab5/Tab5_Keyboard) · [product page](https://docs.m5stack.com/en/products/sku/A164)
- 70 keys (14x5 matrix), multi-key press, STM32F030 MCU, two WS2812 RGB LEDs.
- Modes: Normal (row/column), HID (reports forwarded over Tab5 USB or BLE), Character (key names).
- Plugs directly into Tab5 Ext.Port1 over I2C (address 0x6D, SDA G0, SCL G1, INT G50). 128 x 59.4 x 13.1 mm, 65.2 g.
- Libraries: Arduino M5Unit-KEYBOARD, plus an ESP-IDF demo repo. **Whether OrcSDR or Trail Mate use it is unknown.**

---

## 4. SDR on the Tab5: OrcSDR and others

### OrcSDR (main project)
- Repo: [hardcoreerik/OrcSDR](https://github.com/hardcoreerik/OrcSDR) · [wiki](https://github.com/hardcoreerik/OrcSDR/wiki) ·
  [user guide](https://hardcoreerik.github.io/OrcSDR/) · [releases](https://github.com/hardcoreerik/OrcSDR/releases)
- Forks seen: s53zo/OrcSDR, Garthnesss/OrcSDR. License AGPL-3.0-only.
- Press: [rtl-sdr.com, 2026-09-08](https://www.rtl-sdr.com/orcsdr-running-rtl-sdr-directly-on-an-esp32-p4/),
  [Notebookcheck](https://www.notebookcheck.net/OrcSDR-Why-folks-no-longer-need-a-650-SDR.1390941.0.html).
- Beta software. The developer separates working features from experimental ones. The code was written with AI assistance (per rtl-sdr.com).

**Latest release I found:** v0.4.0-beta.1 (2026-10-10). Re-check the releases page, since an older page I fetched showed older numbers.

| Capability | Status (as of v0.4.0-beta.1 and recent betas) |
|---|---|
| Spectrum / waterfall, RF Lab | Implemented |
| FM broadcast, stereo, RDS | Implemented |
| Shortwave dashboard, AM | Added in beta7 |
| FT8 / FT4 receive | Native on-device (v0.4.0-beta.1). Receive only. Needs correct clock. FT4/JS8 Hunter not yet enabled. |
| JS8 | Experimental, limited |
| ADS-B 1090 MHz | Implemented, depends on antenna and location |
| P25 Phase 1 (clear voice) | Added in beta4. Encrypted voice is not decoded. |
| POCSAG | Native receiver added in beta5 |
| LoRa monitor | Passive, receive-only Meshtastic monitor, regional plans (US 902-928 MHz). **MeshCore not mentioned.** |
| 2.4 GHz Wi-Fi survey | Via Tab5's C6 |
| APRS | **Not mentioned anywhere I found** |
| Transmit | None (receive only) |

**Receivers:** RTL-SDR Blog V4 (reference), V4L, V3c, and Nooelec NESDR SMArt V5 (FT8 accepted 2026-10-09 with an MLA-30+ antenna;
earlier beta7 notes called V5 support experimental). V4 needed manual gain after auto-gain clipped in the FT8 test.

**Install gotchas:**
- Install via M5Burner (search for OrcSDR) or the web flasher. The full image writes at address `0x0`, **resets saved settings
  including Wi-Fi profiles**, and requests a full erase. To keep settings, use the separate-region method documented in the
  release's M5BURNER_RELEASE.md guide.
- The P4 package does **not** flash the Tab5's C6. Use Settings > Firmware & Updates if the C6 needs ESP-Hosted 3.0.6
  (2.12.6 and 3.0.6 are accepted in v0.4.0-beta.1). If the C6 is unreachable, follow the recovery docs rather than
  retrying the in-app updater.
- Earlier beta7 note: a manual `.bin` was republished after the original was application-only and could leave a blank screen.
  Verify hashes and avoid withdrawn packages.
- Keep Wi-Fi auto-connect off and connect manually (beta5 notes call auto-connect still unstable; check whether fixed).
- Leave the dongle unplugged while flashing. Unplug the PC USB cable before regular use (brownout risk).
- Developer builds: native ESP-IDF 5.5.4 only. PlatformIO and Arduino IDE are unsupported.
- Report problems using the issue template (release, receiver, antenna, band, steps). Discussions is for setup questions.

### OrcSDR release status as of 2026-10-31 [S: Charlie's copy of the GitHub releases page]
- Latest stable-ish: **v0.5.0-beta.1** (about 5 days old): guided first-run wizard (Welcome, Network, Location, Offline Maps), OrcMaps offline maps, Dead Air dashboard, SSTV, ACARS, shortwave USB/LSB. Assets: `OrcSDR-Tab5-v0.5.0-beta.1.bin` (complete image for 0x0, 7.14 MB), a local M5Burner zip, an M5Burner upload bundle, SHA256SUMS.txt. **No Windows settings-safe installer listed for 0.5.0** (it existed for 0.3.0-beta.1/beta.2). The M5Burner path uses fresh settings, so the wizard runs; it does not format the SD card.
- Nightly builds exist (pre-release, may have bugs); browser installer at theorc.dev/sdr/nightly (keeps settings unless Erase is ticked).
- Receive-only. v0.4.0-beta.1 notes: FT8 decoded on a Nooelec NESDR SMArt V5 (40 m, 7.074 MHz, active MLA-30+ antenna, bias tee off) after tightening the antenna connection, so the V5 is accepted and can receive HF in that test.
- C6 note (v0.3.0-beta.2 notes): C6 firmware 2.12.6 and 3.0.6 are both accepted; the 3.0.6 update is optional, and applying it **breaks M5Launcher's Wi-Fi/OTA**. If Launcher matters, do not apply the C6 update. Earlier advice here to always confirm the C6 update was wrong for Launcher users.

### Other Tab5 SDR projects
- [9a3zi/tab5-SDR](https://github.com/9a3zi/tab5-SDR) (GPL-2.0+): the HF-focused one. AM/USB/LSB/CW, FT8, WSPR (with PSKReporter upload),
  RS41 radiosonde decoder, WFM/NFM. Uses the V4's built-in upconverter for HF. ESP-IDF 5.4+ build. **Battery must be connected.**
  No APRS.
- [hardparking/tab5-sdr](https://github.com/hardparking/tab5-sdr): simpler FM/NFM receiver with NYC-area bookmarks. Clean architecture, good to read.
- Related hardware, same idea: LILYGO T-Display P4 projects, see [LakeShark (rtl-sdr.com, 2026-09-17)](https://www.rtl-sdr.com/lakeshark-p25-phase-1-fm-pocsag-ads-b-and-sub-ghz-with-an-rtl-sdr-on-the-lilygo-t-display-p4-esp32-p4/),
  its [2026-10-16 update using an LR2021 LoRa chip as the SDR](https://www.rtl-sdr.com/lakeshark-update-using-an-lr2021-lora-chip-as-an-sdr-for-portable-p25-pocsag-and-fm-reception-on-the-esp32-p4/),
  and [jstockdale's T-Display-P4 ADS-B firmware](https://github.com/jstockdale/T-Display-P4/tree/adsb) (RTL-SDR plus Meshtastic-compatible SX1262). None of these mention the Tab5.

---

## 5. Unit C6L reference

**Docs:** [M5Stack Unit C6L](https://docs.m5stack.com/en/unit/Unit_C6L) · [Meshtastic setup](https://docs.m5stack.com/en/guide/unit_c6l/meshtastic) ·
[Meshtastic.org device page](https://meshtastic.org/docs/hardware/devices/m5stack/unit-c6l/) ·
[M5 shop](https://shop.m5stack.com/products/m5stack-c6l-unit-for-meshtastic-sx1262-esp32-c6) ·
[RobotShop](https://www.robotshop.com/products/m5stack-unit-c6l) (about $24 when I looked, **verify**)

### Hardware
- ESP32-C6 (160 MHz + 20 MHz LP core), 16 MB flash, 2.4 GHz Wi-Fi 6, BLE 5, Zigbee/Thread.
- SX1262 LoRa, 868-923 MHz range (covers US 915), +22 dBm max TX, -147 dBm sensitivity.
- 0.66 in SSD1306 OLED (64x48), WS2812 RGB LED, buzzer, one user button.
- Two SMA-style antenna ports: 2.4 GHz and LoRa. Included antennas are 3 dBi: LoRa whip is **868 MHz**, 108 mm; Wi-Fi whip 84 mm.
  Use the Alfa 915 MHz antenna on the LoRa port for the US band (confirm connector first, Q3).
- USB-C 5 V power only. **No battery, no GPS.** HY2.0-4P Grove port. 62 x 24 x 8 mm, 13.6 g. LEGO-compatible mounting holes.
- Power per M5Stack: sleep about 0.7-0.9 mA, LoRa RX standby about 85 mA, continuous max TX about 80 mA (M5Stack lists TX below RX and does not explain; treat as given).
- Treat it as a fixed node, not a handheld (per the UKSN review).

### Pin map (from M5Stack docs; the page lists G20/G21 for both SX1262 and OLED, so verify against the schematic before wiring or coding)
- SX1262: MOSI G21, MISO G22, SCK G20, CS G23, BUSY G19, IRQ G7. NRST, ANT_SW and LNA_EN go through the PI4IOE5V6408 I/O expander (I2C SCL G8, SDA G10).
- OLED: CS G6, DC G18, RST G15. Buzzer G11, RGB LED G2. Grove: yellow G5, white G4.

### Flashing and setup (Meshtastic)
1. Connect a USB-C **data** cable. Hold the side button about 3 seconds until the green LED turns red (download mode).
2. Open the official Meshtastic web flasher (linked from the [M5Stack guide](https://docs.m5stack.com/en/guide/unit_c6l/meshtastic)) in Chrome, pick M5Stack, then Unit C6L.
   First install: full erase and install. Unplug and replug USB afterward.
3. First boot: choose region (US for 915 MHz) with the front button, pair with the phone app over Bluetooth, set names.
- **Bluetooth and Wi-Fi cannot run at the same time** on the C6 Meshtastic firmware. Bluetooth is default. Enabling Wi-Fi drops phone pairing;
  recover over USB with the web client.
- No GPS: location can come from the phone.
- Always attach the antenna before powering a LoRa radio.
- The M5Stack EasyLoader demo is older firmware, only for checking the unit works.
- Guides: [OpenELAB setup](https://openelab.io/blogs/learn/m5stack-unit-c6l-meshtastic-setup-firmware-lora-network-configuration),
  [UKSN review, 4/5](https://www.uksn.org.uk/post/m5stack-c6l-review-the-ideal-static-node-for-your-meshtastic-network)
  (suggests a 3-6 dBi N-type antenna with an SMA-to-N cable for static installs).

### MeshCore on the C6L (relevant to CNJ Mesh)
- MeshCore firmware has a C6L board entry with four environments: companion_radio_ble, companion_radio_usb, repeater, room_server
  ([MeshCore repo](https://github.com/meshcore-dev/MeshCore), [web flasher](https://meshcore.co.uk/flasher.html)). **I could not confirm the flasher lists it.**
- Known issue: boot loop on the C6L caused by QIO flash mode. [PR #3098](https://github.com/meshcore-dev/MeshCore/pull/3098)
  switches it to DIO and was **not merged** when I checked. A related C6 fix was merged 2026-06-26.
  Users also reported display and Bluetooth PIN problems on the companion_radio_ble v1.17.1 build. If pairing was previously used with Meshtastic, clear old Bluetooth pairings.
- Official M5Stack docs for the C6L cover only Meshtastic. MeshCore support is community-maintained.

### Other firmware
- Zephyr: [board docs](https://docs.zephyrproject.org/latest/boards/m5stack/m5stack_unitc6l/doc/index.html) (SX1262, OLED, RGB LED, buzzer, button supported).
- Arduino IDE / UIFlow2 / PlatformIO (board esp32-c6-devkitc-1, RadioLib) per the M5Stack docs.

---

## 6. Tab5 + LoRa mesh: what exists

- **Trail Mate** ([repo](https://github.com/CardputerZero/trail-mate), [wiki](https://github.com/vicliu624/trail-mate/wiki), AGPLv3, [CNX article](https://www.cnx-software.com/2026/04/13/trail-mate-open-source-firmware-leverages-meshtastic-and-meshcore-for-esp32-off-grid-handhelds/)):
  Meshtastic + MeshCore text chat, offline maps, Sub-GHz energy sweep, Reticulum/LXMF bridge, APRS/iGate-oriented host link.
  The Tab5 is a **bring-up target** (shared shell runs, hardware work in progress). The wiki does not say how the Tab5 gets a LoRa radio.
  Primary validated devices are the LILYGO T-Deck and T-LoRa Pager. Code is stated to be 100% AI-generated under human guidance.
- **PURR-OS-ESP32** ([repo](https://github.com/PastorCatto/PURR-OS-ESP32)): earlier release notes mentioned Tab5 and MeshCore plans, but the README now says development was reset. Not usable to rely on.
- **OrcSDR LoRa monitor**: passive Meshtastic receive only. Could monitor the CNJ Mesh channel from the Tab5 with the Alfa 915 MHz antenna.
- **C6L as the actual radio**: standalone Meshtastic node. CORRECTION Oct 30 (Charlie was right that the Tab5 can be its screen; earlier note said no software existed). Community projects found, all early and unverified on this hardware [S, read from repo pages]:
  - [tpklge/Tab5-Meshtastic](https://github.com/tpklge/Tab5-Meshtastic) (fork of hardparking/Tab5-Meshtastic): Meshtastic client for the Tab5; the Tab5 is the touchscreen UI and the radio is external, over **BLE or Grove UART** (only RAK3172H named; C6L not mentioned). Node list, channel chat, channel editing, QR import. Direct messages and radio-config menus not implemented. Build with ESP-IDF 5.4.x; a prebuilt-style `tab5_meshtastic_v2.bin` can go in through a launcher OTA flow. License not stated.
  - [Its-ze/tabforge-cyberdeck](https://github.com/Its-ze/tabforge-cyberdeck) (MIT): Tab5 "cyberdeck" for C6L Meshtastic and MeshCore; connects the C6L by **USB host** (also Grove UART RX preview). Early scaffold, ESP-IDF build, config on SD, OTA with rollback; says keep the C6L on official Meshtastic first and back up before switching to MeshCore.
  - [m5stack/meshtastic-device-ui](https://github.com/m5stack/meshtastic-device-ui): M5Stack's fork of the Meshtastic UI library (not read in detail).
  Open: does either work with the C6L over Grove UART (needs the Meshtastic serial module on the C6L) or BLE? Untested.

---

## 6b. Tab5 as the Meshtastic screen for the C6L over Grove, plus Launcher (researched Oct 31 2026)

Tags: [V] read on the page this session; [I] inference; [?] could not verify. Nothing here is tested.

**Goal (Charlie, Oct 31):** two main Tab5 apps, OrcSDR and a Meshtastic GUI, switched with Launcher; the C6L stays a Meshtastic node and connects to the Tab5 with the 4-wire Grove cable.

**Does the C6L keep running when the Tab5 is in another app?** [I] Yes: the C6L is its own computer (ESP32-C6 + SX1262, own firmware). The Tab5 app is only a client screen/keyboard. Power is the catch: the Tab5's Grove red wire is 5 V on a rail shared with the M-Bus and side header, switched by software (EXT5V_EN) [V, M5Stack Tab5 docs], so the C6L would go dark whenever the running app leaves that rail off. For real use power the C6L from its own USB-C (power bank). [?] Whether connecting the Grove red wire while the C6L is also on USB-C is safe (two 5 V sources) is not documented: do not do both until checked.

**Grove pins:** Tab5 PORT.A: red 5V, black GND, yellow G53, white G54 (functions not labeled TX/RX) [V]. C6L Grove: yellow G5, white G4 [V, section 5]. A Grove cable is straight-through, so Tab5 TX/RX must land on the C6L's opposite pins: [I] if Tab5 TX = G53 then the C6L needs rxd=5 and txd=4. The Tab5-Meshtastic wiring doc (docs/RAK3172_GROVE.md) could not be read, so the Tab5's TX/RX assignment is [?].

**Radio side [V, meshtastic.org Serial module docs]:** Serial module mode PROTO "exposes the Meshtastic Protobuf Client API on the serial port", the same protocol the phone apps and Python CLI use; set rxd/txd, baud, enabled. Docs example uses pogo pins 16/17; they do not confirm arbitrary pins work, whether the C6 Meshtastic build honors it, or whether PROTO coexists with the phone over Bluetooth [?]. [I] A Bluetooth client route for the Tab5 would compete with the phone for the C6L's single BLE connection; UART avoids that.

**Tab5 Meshtastic GUI projects (all early, none tested):**
- tpklge/Tab5-Meshtastic: BLE or Grove UART client; only the RAK3172H is named as tested (C6L not mentioned); node list, channel chat, channel editing, QR import, keyboard input. No direct messages, no general radio config menus. **No release binaries**: build with ESP-IDF v5.4.x, `build/tab5_meshtastic_v2.bin` is the file for Launcher OTA/app flow. Battery must be connected when flashing. [V]
- Its-ze/tabforge-cyberdeck: C6L via **USB host** (Grove UART is only a passive RX counter), Meshtastic node status and messenger, MeshCore as a selectable C6L image; self-described scaffold, no releases, ESP-IDF build, Windows/PowerShell tooling. [V]
- m5stack/meshtastic-device-ui: supports UART to an external radio but Tab5 is not a listed device. [V] M5Stack's Meshtastic guide covers only the C6L, not the Tab5. [V]
- Trail Mate: page could not be read this session; earlier note (section 6) says Tab5 is a bring-up target only.
- No Tab5 MeshCore client found.

**Launcher [V, wiki + releases + issue #440]:**
- Tab5 supported (2.6.5 to 2.8.0, latest Jul 31). Apps install from SD (or OTA/WUI) into their own OTA partitions and sit side by side; the boot screen shows a card per app. Only one runs at a time.
- Wiki documents choosing the app at boot, not a way to exit a running app: [I] switching apps = reboot and pick again; exact Tab5 gesture [?].
- SD card must be **FAT32 and MBR**. App-only `.bin` or merged images both accepted; Launcher can extract app and supported data partitions from merged files "when possible". Avoid images needing custom flashing steps.
- OrcSDR under Launcher: unconfirmed (its image has a separate world-map data partition; see section 4). A fallback is a full flash.
- **Issue #440 (open, "Fixed on Beta", no stable release named):** after a custom ESP-IDF app runs, Launcher may lose Wi-Fi (esp-hosted) and not detect the Tab5 keyboard; reflashing Launcher restores Wi-Fi temporarily. SD installs do not need Wi-Fi. A second reporter's unit had C6 firmware 2.12.6 and a host/co-processor version mismatch; OrcSDR's Wi-Fi worked on that same unit.
- Launcher keeps the Grove 5 V rail powered from boot (for the keyboard).

**Other Tab5 apps found (none flashed):** SDR: hardcoreerik/OrcSDR (main, releases), 9a3zi/tab5-SDR (HF, V4 upconverter), hardparking/systemrok tab5-sdr (FM/NFM), nullbeing/tab5sa (spectrum analyzer + WFM/NFM/AM, 24 to 1766 MHz, ESP-IDF 5.5, no releases). Non-RF: hey-its-brian/tab5-cyberdeck (DECK//OS, web flasher, full image at 0x0 so it would replace Launcher), M5TabOS. C6L side: siem84 MeshCore + Meshtastic DualBoot (pick on the OLED, one at a time) and MeshCore C6L UI; Tab5 not mentioned. All tagged [V] from project pages, maturity low (a few stars).

**Source audit of tpklge/Tab5-Meshtastic at fcdfe23 (2026-10-09), read Oct 31 [V, cloned and read; not built or run]:**
- Network use in the first-party code: Wi-Fi scan/connect (user enters credentials), SNTP to pool.ntp.org, and one plain-HTTP lookup to ip-api.com that sends the Tab5's approximate position to the mesh, triggered by a button in Settings. No OTA, no phone-home, no hardcoded credentials found. Vendored Espressif components (esp_ipa has a prebuilt .a). Upstream chain is hardparking (no license) -> tpklge; the fork's UPSTREAM.md says it was meant to stay unpublished, so treat the binary as personal-use only.
- **The author's own test radio was a Unit C6L over BLE** (name `Meshtastic_0be4`, fixed PIN 123456) [V, repo CLAUDE.md, third-party text]; the README names only the RAK3172H, and the BLE rows of its test matrix are unchecked. UART is documented only for a RAK3172H.
- **Grove UART pins:** Tab5 TX = GPIO53 (yellow), RX = GPIO54 (white), UART2, 115200 8N1; the project's own doc says TX/RX polarity is assumed and should be verified [V]. Straight-through Grove cable, so the C6L would need Serial module PROTO with rxd=5 (yellow), txd=4 (white), baud 115200 [I from the C6L pin map].
- **Power (corrected Oct 31 23:10):** [V, read in code; not tested on hardware] the board bring-up leaves **EXT5V_EN HIGH** (Grove/external 5 V rail ON) while the app runs, and the app switches it off only when you press Exit. The UART transport's own `GROVE_ENABLE_5V` flag (default 0) is a separate unfinished option and does not decide this. **USB5V_EN (the USB-A host port's 5 V) is LOW (off) by default and the app never calls `usb5v_enable`**, so with this app the Tab5's USB-A port gives the C6L no power. [?] Whether the C6L accepts 5 V through its Grove red pin is undocumented (M5Stack lists USB-C as its power input). The project warns not to feed 5 V to a bare 3.3 V module. An earlier version of this note said the Grove rail is off; that was wrong.
- **Launcher:** the author's Launcher gave the app a 1600 KiB partition (limit 1,638,400 bytes); the size-optimized build is 1,604,192 bytes, so it barely fits [V]. The app's EXIT button puts the Tab5 into deep sleep and a physical reset starts Launcher again; switching back is launching the app from Launcher's App Manager; settings and history persist in a `storage` partition [V]. The author runs a **patched Launcher 2.8.0** (keyboard bring-up order, Wi-Fi retry) because stock 2.8.0 does not detect the Tab5 keyboard; the app itself handles the keyboard in its own run, so stock Launcher is probably usable by touch [I].
- A prebuilt `newversion/tab5_meshtastic_v2.bin` is committed in the repo (1,604,192 bytes, sha256 7f4507635955dd1266336db11a93d269e23db281859014eb523c9ded76154be8); not verified to match the source, so we build our own.
- Build: `.github/workflows/build-tab5-meshtastic.yml` (manual run; pinned to fcdfe23; Espressif `idf:release-v5.4` image; artifact kept 3 days). The session's `gh` token is invalid, so Charlie must press Run workflow in the Actions tab and the log/artifact must be read by him; the first run is untested.

**Open decisions:** run the build and see if it compiles; BLE vs UART link to the C6L (BLE is the one the author tested with a C6L; UART untested with a C6L); C6L power source (own USB-C in the car); whether stock Launcher is enough or the patched one is needed.

## 7. Other Tab5 projects (non-RF)

- [loadout-tab5](https://github.com/katinadelgado74/loadout-tab5): firmware launcher that boots .bin files from the SD card with OTA rollback.
- [Launcher by bmorcelli](https://github.com/bmorcelli/Launcher) [S: README/changelog read Oct 22, not tested]: multi-firmware launcher; Tab5 support since 2.6.0 (2.6.7 added USB mass-storage and Launcher self-update on Tab5; 2.10.0 fixed OTA crashes). Menu: SD (install .bin from card), OTA (install from M5Burner or GitHub links), WUI (web interface), USB (mass storage), PMan (built-in partition manager: view, create, delete, format, back up, restore, resize partitions), CFG, OFF. Charlie saw it in a YouTube Short by @Valleytechsolutions on Oct 22 (video itself not readable by Claude; only screenshots). [I] Caveat: unknown whether OrcSDR (needs its own partition layout and ESP-Hosted C6 firmware) runs from Launcher; for the first OrcSDR install use the documented M5Burner path, and treat Launcher as a later experiment. [I] Idea: use PMan to back up the factory partitions before flashing OrcSDR, so there is a way back (unverified on Tab5) (flashing OrcSDR with M5Burner writes at 0x0 and would replace Launcher).
  Could be handy for switching between OrcSDR and other firmware. Very early (3 commits). MIT.
- [dmatking/m5stack-tab5-gps](https://github.com/dmatking/m5stack-tab5-gps): handheld GPS with offline maps, needs M5Stack GPS Module v2.1 on the M-Bus. Apache-2.0, ESP-IDF 6.0.1.
- [esp-cpp/tab5-emu](https://github.com/esp-cpp/tab5-emu) (game emulation), [Paqurin/tab5-apps](https://github.com/Paqurin/tab5-apps),
  [Jasionf/M5Stack-Tab5](https://github.com/Jasionf/M5Stack-Tab5) (UI demos).
- GitHub topic: [m5stack-tab5](https://github.com/topics/m5stack-tab5).
- **Added Oct 31 (fun, not part of the plan) [V, project pages]:** [M5MusicTab5](https://hackaday.io/project/206549-m5musictab5) (music studio: 8-track sequencer, SF2 synth, piano, MIDI recorder; browser flasher, MIT); [tobozo/M5Tab5-Game-and-Watch](https://github.com/tobozo/M5Tab5-Game-and-Watch) (31 Game & Watch titles, bring your own ROMs, source build only, GPL-3.0); [hey-its-brian/tab5-cyberdeck](https://github.com/hey-its-brian/tab5-cyberdeck) (DECK//OS: SSH terminal, notes, file portal, music; web flasher, full image at 0x0, would replace Launcher). Title only, unread: MU-Software/m5stack-tab5-ssh-client, GalusPeres/Tab5-HomeAssistant-Display. Browser-flasher apps write a full image and probably replace Launcher; whether Launcher can extract them from SD is unconfirmed.

---

## 8. Community

- GitHub: OrcSDR Discussions and Issues; Trail Mate has a Discord (link in its README).
- M5Stack community forum (community.m5stack.com) and the Home Assistant thread above.
- Reddit: r/M5Stack exists (about 22k members per a third-party listing, **unverified directly**; no Tab5 threads seen there).
  Also worth watching: r/RTLSDR, r/meshtastic, r/amateurradio.
- News sources that covered Tab5 SDR work: rtl-sdr.com (tag: [esp32-p4](https://www.rtl-sdr.com/tag/esp32-p4/)), CNX Software.

---

## 9. Gaps, ideas and watchlist

**Gaps I found (nothing exists yet, or I could not find it):**
- No Tab5 APRS decoder (144.390 MHz or LoRa APRS) in any project I found.
- No Tab5-native LoRa radio, so no standalone Tab5 Meshtastic or MeshCore node.
- OrcSDR's LoRa monitor does not mention MeshCore.
- Nooelec NESDR SMArt V5 support in OrcSDR is recent (FT8 accepted 2026-10-09). Results on other bands and the V5's HF
  route are not documented beyond that test.
- OrcSDR's HF support was only recently added; 9a3zi's project is the other HF option.

**Watch:**
- OrcSDR releases (APRS, MeshCore monitoring, FT4, settings backup to SD, PSK Reporter).
- MeshCore PR #3098 (C6L boot loop) and whether the C6L appears in the MeshCore flasher.
- Trail Mate Tab5 status and any LoRa module for the Tab5.
- A Tab5 LoRa stamp from M5Stack (raised in the device-ui thread).

**Ideas:**
- Tab5 + SDR as a portable receiver: FM first, then ADS-B, then 915 MHz LoRa monitor with the Alfa antenna, then HF FT8 with a wire antenna.
- C6L as a small fixed node on CNJ Mesh (MeshCore repeater or Meshtastic node) once the connector question is settled.
- Compare passive Tab5 LoRa monitoring against the Pi-based capture already documented in `docs/sdrangel-lora-reference.md`.

---

## 9b. Repo-informed plan (added Oct 22, 2026 after reading the CNJ Mesh repo)

Tags: [V] read in this repo; [I] Claude's inference; nothing here is tested.

**Why the C6L's job is not "one more MeshCore repeater" [I]:** MeshCore already has KPR2 (Heltec V4, cnjmesh3), KPR3 (RAK4630, 9-el Yagi) and the Observer; KPR1 is the Tilly bridge on 62.5 kHz. A fourth indoor repeater adds little. The C6L is USB-C 5 V only (no battery), so it suits a fixed, powered job.

**Charlie's decision (Oct 22) [stated]:** the C6L is his **mobile node**, whichever protocol it runs. KPN6 is his main Meshtastic node (indoors, fed by LMR400 to a roof antenna), so a fixed gateway role is not needed. EHN-style gateway: very experimental, only being evaluated, nothing bought.

**What "mobile" means for this board [V from M5Stack specs]:** USB-C 5 V only, no battery, no GPS. Needs a USB power bank, the included 108 mm whip, and a phone for the interface (and for position, if the app can share phone location, to be verified on the chosen firmware).

**Protocol for a mobile node [I]:** the phone link is Bluetooth, and the MeshCore C6L companion_radio_ble build had reported PIN/display problems on v1.17.1, so Meshtastic is the lower-risk first flash. Meshtastic cannot use Bluetooth and Wi-Fi at once. Reflashing is cheap (download mode), so try Meshtastic first and revisit MeshCore after PR #3098 and the BLE issues are sorted. A real GPS-equipped mobile node already exists (T-Deck Plus, KPC2/KPN2).

**Parked ideas (not decided, nothing bought):** APRStastic (afourney/aprstastic, Meshtastic to APRS gateway) and the EHN/MTMC-Bridge gateway would need a fixed, USB-attached node and are not C6L jobs now; see `todos.md` and `docs/ehn-gateway-project.md`.

**If MeshCore anyway:** USB companion for a Pi (not BLE, because of the reported BLE PIN/display problems on v1.17.1), radio 910.525 / BW 500 / SF10 / CR5 (only the settings in `cnjmesh1-operations.md`; nodes on other settings cannot hear each other). Part 15.247 caution for 500 kHz applies as for KPR3; the C6L module's FCC grant is unknown.

**Antenna:** connector gender of the Alfa 915 MHz and the C6L LoRa port still unverified (Q3).

**Fun projects that fit this network [I]:**
1. OrcSDR passive Meshtastic monitor on 902-928 MHz, compared against what CJG1/CJG2 report to MQTT (is the RF picture the same as the broker's?).
2. OrcSDR FT8 / Shortwave dashboard as a first step into HF (check what the NESDR SMArt v5 can receive below ~24 MHz before promising anything; an upconverter may be needed).
3. OrcSDR ADS-B and POCSAG: easy wins on the dongle.
4. Tab5 plus `docs/sdrangel-lora-reference.md`: OrcSDR does not mention MeshCore, so MeshCore 500 kHz packet-presence checks still go through SDRangel on the laptop.
5. C6L as a pocket mobile node on the CNJ meshes (above): range tests against KPR2/KPR3 (MeshCore) or KPN6/CJG1/CJG2 (Meshtastic).
6. Trail Mate on the Tab5 as a field chat screen (Meshtastic + MeshCore), once the keyboard arrives.

## 10. Test log (fill in as you go)

| Date | What | Result |
|---|---|---|
| 2026-10-28 | Tab5 first boot on battery (factory test screen) | OK: display works (screen reports LCD IC ST7121), battery 7.69 V, Wi-Fi/C6 status icon shown, RTC not set (shows 2132). Not yet flashed. |
| 2026-10-31 | esptool 5.6.0 installed on Windows laptop; `flash-id` over USB-C | OK: ESP32-P4 rev v1.3, COM16, 16 MB flash, USB-Serial/JTAG. Needed the **regular** Python 3.13 (`py -3.13`): the default `py` was the free-threaded 3.13t, where cryptography/cffi fail to build. |
| 2026-10-31 | SHA256 of `OrcSDR-Tab5-v0.5.0-beta.1.bin` in Downloads | OK: matches the release page (2ae609e1...f77bb1). |
| 2026-10-31 | Full 16 MB flash backup of the factory state with esptool `read-flash` | OK: 16,777,216 bytes in 159 s, saved as `tab5-factory-backup.bin` in Downloads on the laptop. Restore path if needed: `esptool write-flash 0x0` of that file. **OrcSDR not flashed yet** (paused 12:45). |

## 11. Changelog

- 2026-10-22: Created from first research pass (Tab5, C6L, OrcSDR, Trail Mate, accessories, community).
- 2026-10-22: Owner confirmed Tab5 Kit with battery (Q1) and dongle is a Nooelec NESDR SMArt v5 from photos (Q2).
- 2026-10-22: Added section 9b (repo-informed C6L role, recommendation and project ideas) after reading the CNJ Mesh repo.
- 2026-10-22: Owner says the C6L is his mobile node (either protocol); KPN6 is the main fixed Meshtastic node; EHN gateway is only being evaluated. Section 9b updated.
- 2026-10-22: Q4 resolved: C6L starts on Meshtastic (mobile node).
- 2026-10-22: Added Launcher (bmorcelli) note after Charlie shared a YouTube Short about Tab5 updates.
- 2026-10-28: Tab5 Kit (sealed, box shows NP-F550 2000 mAh included) and C6L arrived; a StickS3 NTAG215 NFC card came with the order. Keyboard not yet.
- 2026-10-28: Photos of the unsealed Tab5 (front, back, NP-F550 battery out of its bay). Back diagram shows ST7121 display. Not yet powered on.
- 2026-10-28: Tab5 first boot OK (factory test screen).
- 2026-10-30: Tab5 Keyboard arrived, earlier than expected. Not yet attached.
- 2026-10-30: Owner idea: Tab5 + C6L as one mobile Meshtastic unit in the car. Findings: no known software links a Tab5 UI to a C6L radio (see section 6); Tab5 Kit has a 1/4-20 tripod socket on one edge for mounting; Kit weighs about 218 g. Not decided.
- 2026-10-30: Corrected section 6: Tab5-as-UI projects for an external Meshtastic radio exist (Tab5-Meshtastic, TabForge). Untested.
- 2026-10-31: Added OrcSDR v0.5.0-beta.1 release status and C6/Launcher caveat.
- 2026-10-31: **M5Burner share link JXFU4H is stale (v0.3.0-beta.2); do not use it for 0.5.0.** The OrcSDR wiki Getting-Started page also still describes v0.3.0-beta.1 (Windows installer, no 0.5.0 steps). Install route chosen instead: flash the SHA-verified `OrcSDR-Tab5-v0.5.0-beta.1.bin` (complete image for 0x0) with `py -3.13 -m esptool -p COM16 write-flash 0x0 <file>`, NESDR unplugged. Factory backup taken first (see test log).
- 2026-10-31: Launcher + OrcSDR coexistence is **unconfirmed**: in OrcSDR discussion #64 a tester installed it through Launcher from SD and the maintainer asked whether it was app-only or a full flash; no answer. Plan: flash OrcSDR now to test the NESDR; try Launcher once the 32 GB card arrives (Launcher replaces OrcSDR at 0x0; OrcSDR would then be tried from the SD card). Goal: one Tab5 for OrcSDR plus a screen for the C6L (Tab5-Meshtastic, untested).
- 2026-10-31: Two 32 GB microSD cards ordered.
- 2026-10-31 (late): Decision (Charlie): hold the Tab5 flash until the 32 GB microSD cards arrive Monday 2026-11-02, so Launcher goes on first and OrcSDR is then tried from the card (avoids flashing OrcSDR and reinstalling). Launcher confirmed maintained for Tab5 [V, releases page]: 2.6.5 SDMMC driver, 2.6.7 USB mass storage, 2.6.8 Wi-Fi scan/AP fix, 2.8.0 (Jul 31) Tab5 keyboard support. OrcSDR-under-Launcher still unconfirmed. Factory backup and verified OrcSDR .bin already on the laptop.
- 2026-10-31 (late): C6L photo: Grove cable (red/black/yellow/white, HY2.0-4P) came with the unit and is plugged in; no USB cable in the photo. USB-C port is on a long edge, found by Charlie. Antennas on both ports. Not powered or flashed yet.
- 2026-10-31 (late): Added section 6b (Tab5 as Meshtastic screen over Grove, Launcher details, other Tab5 apps). Research only, nothing flashed.
- 2026-10-31 (late): Charlie: the C6L (and hopefully the Tab5) is a **mobile** node, so it does not need to run 24/7. That makes Tab5-powered operation acceptable (C6L off when Tab5 off). Preferred rig to test: one USB-A to USB-C cable from the Tab5 USB-A host port to the C6L (power + data; only TabForge is known to use USB host, and OrcSDR needs that port for the NESDR, so they cannot share it without a hub). Still to test: whether each app keeps the USB-A / Grove 5 V rail on. Power the Tab5 from a car USB-C charger (it charges only while on). No GPS on either device; phone supplies position. Plan unchanged: C6L on plain Meshtastic with the phone first.
- 2026-10-31 (late): Audited tpklge/Tab5-Meshtastic (section 6b), pinned fcdfe23, added a manual GitHub Actions build workflow. Charlie decided he wants the Tab5 + keyboard as the interface and not use a phone with the C6L.
- 2026-10-31 (23:05): Added section 0 (pick-up-here summary with ordered next steps and decisions).
- 2026-10-31 (23:58): From M5Stack's C6L UIFlow2 video (Charlie's screenshots): the LoRa whip has a **blue** collar and the Wi-Fi whip a **red** one [V, video frame]; the **USB-C port is on the right long edge near the Grove end** (screen facing you, antennas up) [V, video frame]; download mode confirmed again (hold the side button about 3 s, LED green to red). M5Burner's UNITC6L list also shows community MeshCore builds for the C6L: Companion Radio (BLE) 1.11.0 and Repeater 1.11.0, both 'Experimental', US/Canada 910.525 MHz preset, published 2026-02-03 by TheRealHaoLiu; the repeater listing says the default admin password is 'password' [V, screenshot]. Version 1.11.0 is far behind the 1.17/1.18 builds used on CNJ nodes, so prefer MeshCore's own flasher when MeshCore is tried. UIFlow2 firmware is not wanted (it replaces Meshtastic).
- 2026-11-01 (00:05): Read M5Stack's C6L Meshtastic guide [V, docs.m5stack.com/en/guide/unit_c6l/meshtastic]: flasher is https://flasher.meshtastic.org/ in Chrome (M5Stack, then Unit C6L), baud 115200, tick Full Erase and Install; the guide says to pick the **latest Alpha**; region is chosen on the C6L's own screen with the front button (short press scrolls, long press confirms); Bluetooth pairing shows a six-digit code on the unit (random PIN, unlike the fixed 123456 the Tab5-app author's test radio used). Caution [I, from docs/meshtastic-2.8-upgrade-plan.md]: 2.8 alpha defaults a new US node to **Long Turbo** and derives a new node ID; CentralNJ is Long Fast and the gateways are on 2.7.x, so check whether a 2.7.x build lists the C6L, otherwise set Long Fast manually after flashing. The video Charlie shared is M5Stack's generic UIFlow2 one; only its download-mode steps apply.
- 2026-11-01 (00:15): Charlie's screenshots of a YouTube Short by @LWL-ProTechTor (title 'M5Stack Unit-C6L LoRa WiFi Module Meshtastic...'): on-screen text says the C6L is 'powered by Cardputer ADV' and 'can be powered by Grove port or USB-C' [S, creator's claim in a video, not a datasheet]. That is the first evidence that the C6L runs from 5 V on its Grove pin; together with the Tab5 app keeping EXT5V on while it runs (section 6b) it makes Tab5-over-Grove power plausible, still to be tested on the bench (current limit of the Tab5 rail undocumented; do not connect USB-C and Grove power at the same time until checked). The video does not show a data link between the Cardputer and the C6L [I]. Context [V, Meshtastic docs, NodakMesh]: M5Stack's Cardputer Mesh Kit is a Cardputer ADV (keyboard, 1.14 in screen) plus a Cap LoRa-1262 (SX1262 + GNSS), Meshtastic preinstalled, i.e. a self-contained keyboard Meshtastic terminal with its own radio, not an external-radio client. A 'LoRaWAN US915' M5 module is a different thing (LoRaWAN/AT-command add-on, not usable for Meshtastic).
