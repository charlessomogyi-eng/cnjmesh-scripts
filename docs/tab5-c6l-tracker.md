# M5Stack Tab5 + Unit C6L — Tracker

**Owner:** Charlie (K2GIA) · **Created:** 2026-10-22 · **Last researched:** 2026-10-22

Living tracker for the M5Stack **Tab5** (ESP32-P4 tablet) and **Unit C6L** (ESP32-C6 + SX1262 LoRa node).
Update the status board and checklist as things arrive and get tested. Facts below come from the linked
sources; anything I could not confirm is marked **(unverified)**. Re-check version numbers on GitHub before
installing, because several of these projects move weekly.

---

## 1. Status board

| Item | Status | Notes |
|---|---|---|
| M5Stack Tab5 | Shipped, in the mail (as of 2026-10-22) | **Kit with battery** (K145, includes NP-F550), confirmed by owner 2026-10-22. See power notes. |
| M5Stack Unit C6L (U202) | Shipped, in the mail | Ships with two SMA whips (868 MHz LoRa + 2.4 GHz). |
| Tab5 Keyboard (A164) | Ordered, expected a few weeks out | 70-key, plugs into Tab5 Ext.Port1. |
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
- [ ] Get a microSD card for the Tab5 (OrcSDR uses it for captures and data packs).
- [ ] Short USB-A extension cable for the dongle (recommended by the 9a3zi tab5-SDR project).
- [ ] Decide on an HF antenna (long wire plus 9:1 unun is the usual start) and a 1090 MHz antenna for ADS-B.
- [ ] V5 tips from the OrcSDR FT8 notes: tighten the SMA antenna connection firmly, and use manual gain if auto-gain clips.

### On arrival
- [ ] Check the sticker on the back of the Tab5 for the display driver revision (ST7121 expected for a late-2026 unit, **unverified**).
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
- **C6L as the actual radio**: standalone node. The Tab5 and C6L do not connect directly. A Tab5 Bluetooth Meshtastic client was mentioned in the device-ui thread but I did not find its repo.

---

## 7. Other Tab5 projects (non-RF)

- [loadout-tab5](https://github.com/katinadelgado74/loadout-tab5): firmware launcher that boots .bin files from the SD card with OTA rollback.
- [Launcher by bmorcelli](https://github.com/bmorcelli/Launcher) [S: README/changelog read Oct 22, not tested]: multi-firmware launcher; Tab5 support since 2.6.0 (2.6.7 added USB mass-storage and Launcher self-update on Tab5; 2.10.0 fixed OTA crashes). Menu: SD (install .bin from card), OTA (install from M5Burner or GitHub links), WUI (web interface), USB (mass storage), PMan (partition manager), CFG, OFF. Charlie saw it in a YouTube Short by @Valleytechsolutions on Oct 22 (video itself not readable by Claude; only screenshots). [I] Caveat: unknown whether OrcSDR (needs its own partition layout and ESP-Hosted C6 firmware) runs from Launcher; for the first OrcSDR install use the documented M5Burner path, and treat Launcher as a later experiment (flashing OrcSDR with M5Burner writes at 0x0 and would replace Launcher).
  Could be handy for switching between OrcSDR and other firmware. Very early (3 commits). MIT.
- [dmatking/m5stack-tab5-gps](https://github.com/dmatking/m5stack-tab5-gps): handheld GPS with offline maps, needs M5Stack GPS Module v2.1 on the M-Bus. Apache-2.0, ESP-IDF 6.0.1.
- [esp-cpp/tab5-emu](https://github.com/esp-cpp/tab5-emu) (game emulation), [Paqurin/tab5-apps](https://github.com/Paqurin/tab5-apps),
  [Jasionf/M5Stack-Tab5](https://github.com/Jasionf/M5Stack-Tab5) (UI demos).
- GitHub topic: [m5stack-tab5](https://github.com/topics/m5stack-tab5).

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
| | | |

## 11. Changelog

- 2026-10-22: Created from first research pass (Tab5, C6L, OrcSDR, Trail Mate, accessories, community).
- 2026-10-22: Owner confirmed Tab5 Kit with battery (Q1) and dongle is a Nooelec NESDR SMArt v5 from photos (Q2).
- 2026-10-22: Added section 9b (repo-informed C6L role, recommendation and project ideas) after reading the CNJ Mesh repo.
- 2026-10-22: Owner says the C6L is his mobile node (either protocol); KPN6 is the main fixed Meshtastic node; EHN gateway is only being evaluated. Section 9b updated.
- 2026-10-22: Q4 resolved: C6L starts on Meshtastic (mobile node).
- 2026-10-22: Added Launcher (bmorcelli) note after Charlie shared a YouTube Short about Tab5 updates.
