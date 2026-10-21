# EHN-style gateway project: MeshCore <-> Meshtastic <-> SMS (idea stage)

**Status:** idea only, started Oct 21 2026 (Charles saw the EmergencyHam.net demo post in the MeshCore - New Jersey Facebook group). Nothing ordered, nothing built, nothing tested. Do after the housekeeping todos in `todos.md`.
**Tags:** [S] = read on a web page or screenshot (not tested by us); [I] = Claude's inference.

## What it is
A basestation that lets one text conversation cross between a MeshCore mesh, a Meshtastic mesh and phone SMS/RCS. The demo post (screenshot [S]) shows: a MeshCore gateway board, a Meshtastic gateway radio, an Android phone as the SMS gateway, a Raspberry Pi 4 basestation, and a UPS/power supply.

## The EmergencyHam Network (EHN) design [S: emergencyham.net, read Oct 21 2026]
- Alpha announced Oct 14 2026. They call it experimental and not qualified for emergency use.
- Basestation core (Raspberry Pi preferred; also tested on Windows): messaging software, local user directory, routing logic, store-and-forward queue (accepting a message is separate from confirming delivery), and a browser "Operator Workbench" for gateway status, message activity, directory, config and diagnostics. It can run as a self-contained island without a central server.
- Alpha gateways: a MeshCore radio on USB, a Meshtastic node on USB, a dedicated Android phone running the "EHN Relay Link" app (SMS/RCS). Planned later: APRS, JS8Call, Winlink.
- Addressing: `@name` = person, `&name` = group. Common internal format: Emergency Message Protocol (EMP v2.1; message types TXT, CMD, ACK, TLM; duplicate suppression, retries, fragmentation).
- Not published: bill of materials, device models, prices, Pi setup steps.

## What is public
- GitHub organization: https://github.com/emergencyhamnet (found repos: `meshtastic-android-bridge-alpha-public` = Meshtastic <-> phone SMS gateway; `meshcore-pi-port` = a Raspberry Pi port of MeshCore; two unrelated ones).
- Specs and user guides (PDFs) on https://emergencyham.net/downloads/ : gateway user guide, EHN overview ("Start Here"), Directory, EMP v2.1, Routing, Transport Interface, Federation, Provisioning, Scenario Pack, and more.
- No public repo for the basestation core software was found. The alpha program asks clubs and operators to make contact: https://emergencyham.net/contact-us/
- Alpha write-up: https://emergencyham.net/emergencyham-network-our-first-working-alpha-is-ready-for-testing/ ; EMP gateway article: https://emergencyham.net/building-a-resilient-emergency-messaging-bridge/

## Other open-source options found [S, not tested]
- MTMC-Bridge (https://sourceforge.net/p/mtmc-bridge/): GPLv3, Rust, Windows and Linux, web UI; relays public-channel text between MeshCore (USB companions) and Meshtastic (TCP or USB); keeps sender names; anti-loop; beta; last updated Aug 8 2026. No SMS.
- mesh-api (https://github.com/mr-tbot/mesh-api): AI and API router for Meshtastic and MeshCore; lists Twilio SMS and Discord routing (Twilio is a paid service).
- MeshCore-Meshtastic-RaspberryPi-Bridge (https://github.com/CryptoJones/MeshCore-Meshtastic-RaspberryPi-Bridge): two USB LoRa nodes plus one Pi relaying between the two meshes (not read in detail).
- Mesh-Bridge (https://github.com/IceNet-01/Mesh-Bridge): Meshtastic only, so it does not bridge MeshCore.

## Shopping list [I: from the described architecture; prices NOT checked; nothing ordered]
- Raspberry Pi 4 (or an existing spare), power supply, case, good microSD or an SSD; optional UPS HAT or small UPS.
- A MeshCore companion radio on USB (a separate one, not the Observer), set to the CNJ profile 910.525 MHz / 500 kHz / SF10 / CR5.
- A Meshtastic node on USB (the M5Stack Unit C6L on order, due about Oct 27 to Nov 6, might serve; unverified).
- A 915 MHz antenna for each radio; data-capable USB cables; maybe a powered USB hub.
- A dedicated Android phone with a SIM and a texting plan.

## Concerns to settle before building
- A bridge doubles traffic on both meshes; loops and floods can hurt both. Anti-loop and rate limits are essential.
- Channel members' consent: many mesh operators value privacy. Decide which channels (if any) cross.
- SMS: phone-number privacy, carrier filtering and cost, who may send texts into the mesh.
- Which Meshtastic and MeshCore channels and settings would be used, and where the gateway physically lives.

## Suggested next steps
1. Read the EHN gateway user guide and the High-Level Overview PDFs.
2. Decide: join the EHN alpha (contact them), or use open-source pieces (MTMC-Bridge for mesh-to-mesh first, SMS later), or wait.
3. Only then decide on hardware and place any order.

## Context about Charles's setup (for a fresh chat)
- Charles (K2GIA) runs CNJ Mesh in Central NJ: MeshCore on 910.525 MHz / 500 kHz / SF10 / CR5, plus a Meshtastic mesh. Three Raspberry Pis: cnjmesh1 (main server, 10.0.0.181), cnjmesh2 (Pi Zero 2 W), cnjmesh3 (Observer host). There is already a MeshCore Observer (RAK4631) with MQTT feeds and Discord relays (mesh-discord-shim on cnjmesh1).
- Working style (repo rules): this repo is public, so never include passwords, tokens, webhook URLs, keys or his home address. Every command block must say which host it runs on and whether it finishes on its own or needs Ctrl+C. Claude has no direct access to his Pis; he runs commands and pastes output. Do not restart anything without his OK. Update `todos.md` and push repo changes as work finishes.
