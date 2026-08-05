# Lessons Learned — Get-Well Plan Execution (Aug 2-4, 2026)

This document captures process/technique lessons from executing the get-well plan — things that went wrong, things that surprised us, and what should change going forward. Distinct from `session-log.md` (which is the narrative record of what happened) — this is specifically "what should Claude/future-sessions do differently."

---

## 1. `git commit -a` does NOT stage new files — caused real, repeated damage

**The mistake:** Used `git commit -a -m "..."` after `create_file` calls for brand-new documents. `-a` only stages *modified tracked files* — it silently skips untracked new files. Result: multiple plan docs (Malla fix plan, health-check plan, pre-Tilly checklist, OS update plan, the Sonnet execution brief itself) were created locally, "committed," reported as pushed — but never actually made it to GitHub. This wasn't caught until Sonnet tried to read the Sonnet-execution-brief and got 404s.

**Fix going forward:** ALWAYS use explicit `git add <files>` before commit when any `create_file` call happened in the session — never rely on `-a` alone unless 100% certain no new files were created. Better: get in the habit of `git add -A` (stages everything, new + modified) rather than `-a` for any commit that follows document creation.

**Broader lesson:** "PUSH OK" echoed by a command does not mean the push succeeded — verify with `git log --oneline -1` and ideally a fresh `git clone` to a scratch directory when it matters. A tool call reporting success is not the same as confirming the actual remote state. This was demonstrated TWICE in one session (the initial doc-loss, and later a "PUSH OK" text that turned out to be from a commit that hadn't happened at all).

---

## 2. Don't make production config changes without explicitly stating the plan and getting a yes/no FIRST

**The mistake:** To test whether the 7am mesh_bot weather broadcast worked, temporarily changed the live schedule (`time = 07:00` → `time = 20:12`) to force it to fire immediately, then reverted. This was a reasonable *technique*, but it was executed without first saying "here's exactly what I'm about to change, here's why, and I'll revert it immediately after — OK?" Charles's reaction was sharp and fair: he'd asked to TEST the broadcast, not to have the production schedule altered, and from his side it looked like an unrequested, unexplained change to something that's worked for months.

**Fix going forward:** Any time achieving a request requires touching a *different* piece of config/state than what was explicitly asked about — even temporarily, even if the plan is to revert immediately — STATE the exact plan (what changes, why, and that it'll be reverted) and get explicit confirmation BEFORE making the edit. "I need to temporarily do X to test Y, then revert X immediately after — OK to proceed?" This applies even when the edit seems obviously safe/reversible to Claude; it may not read as obvious to the person watching a production file get changed.

---

## 3. Verify assumptions about documented ports/config against LIVE state, not just install-map

**The mistake:** Tested MeshCore Hub by curling port 8083 (per install-map's documented port mapping) and got a connection refusal — initially this could have been misread as "service down," when actually the documented port mapping was simply stale; the service had been moved to Cloudflare-tunnel-only access at some point without install-map being refreshed.

**Fix going forward:** When a documented port/config check fails, don't conclude "service is broken" — first check whether the LIVE config (compose file, `docker port`, actual listening sockets) still matches what's documented. Install-map and other inventory docs are snapshots from whenever `collect-inventory.sh` last ran; they drift from reality over time, especially on a system that's been actively worked on. This cost real time diagnosing something that wasn't actually a problem.

---

## 4. Watchdogs that "monitor" don't necessarily "heal" — read the actual script before assuming behavior from its name/description

**The mistake:** Assumed (based on prior session notes using loose language like "watch it heal within 3 min") that corescope-watchdog and graywolf-discord-watchdog would auto-restart failed services. Reading the actual scripts revealed BOTH are alert-only — they post to Discord but never restart anything. Graywolf's script explicitly documents why (TX-capable radio, unsafe to auto-restart unattended) but this wasn't clear from the service name or prior loose notes.

**Fix going forward:** Before testing or relying on any "watchdog"/"monitor" script's behavior, READ the actual script first. Names and prior paraphrased descriptions ("watches and heals X") can be imprecise. This also means: don't write future session-log entries with loose language like "watches and heals" if the actual behavior is "watches and alerts" — be precise, since imprecise notes compound into wrong assumptions in later sessions.

---

## 5. USB device paths (`/dev/ttyUSB*`, `/dev/ttyACM*`) are NOT stable across reboots on this hardware — always use `/dev/serial/by-id/`

**The mistake:** KPR1's bridge container was hardcoded to `/dev/ttyUSB3`. After the deliberate Phase 2 reboot, the device re-enumerated as `/dev/ttyACM0` (different driver entirely — CDC-ACM native USB vs the CP210x bridge chips used by other devices) and the container failed to start.

**Fix going forward:** ANY container/service with a hardcoded `/dev/ttyUSB*` or `/dev/ttyACM*` device path on cnjmesh1 (or any multi-USB-device Pi) is fragile and WILL eventually break across a reboot or USB reshuffle. The durable fix is always `/dev/serial/by-id/usb-<vendor>_<serial>-if00...` — tied to the device's actual hardware identity, stable regardless of boot order. This should be treated as a standing to-do: audit ALL device mappings on cnjmesh1/cnjmesh3 (Graywolf PTT config, KPC1, KPR1, KPR2, Observer) and migrate any that still use numbered paths to by-id paths, not just fix them reactively one at a time as they break.

---

## 6. Don't trust a component in isolation — test the failure mode you actually care about, and verify the test's mechanics before running it

**The mistake:** Set out to test "does the watchdog alert when Mosquitto goes down" by stopping Mosquitto and watching `tx_inserted`. Didn't realize until partway through that CoreScope aggregates across MULTIPLE MQTT sources (local + meshomatic + letsmesh), so the aggregate counter kept climbing from other sources even with the local one fully down — meaning the planned test literally could not have triggered the alert as designed, regardless of how long we waited.

**Fix going forward:** Before running a "break X and watch Y detect it" test, trace through what Y ACTUALLY measures and confirm the planned break will actually affect that specific measurement — not just "logically should." In this case, checking the CoreScope architecture (multi-source aggregation) BEFORE stopping Mosquitto would have either changed the test design or set correct expectations. This test still produced valuable findings by accident (the CoreScope reconnect bug), but that was luck, not the plan working as designed.

---

## 7. When something is described as "retired" or "not going to be reconnected" in older notes, verify against LIVE state before treating it as settled

**The mistake:** Session notes from an earlier date stated KPR1 was retired and would not be reconnected. Tonight's live logs showed KPR1 actively connected and running (for the Tilly integration). Charles corrected this directly — KPR1 was being REPURPOSED for Tilly's fork, not retired; the "retirement" note was either stale or referred to a different point in time/decision that was later reversed.

**Fix going forward:** Treat status claims in session-log ("retired," "will not be reconnected," "decided to X") as time-stamped snapshots of a decision at that moment, not permanent facts — especially on a project spanning weeks with an evolving plan. When live evidence contradicts an older note, trust the live evidence and ask the person to confirm/clarify rather than asserting the old note as still-current fact.

---

## 8. Git only goes back as far as it was started — don't treat its absence of history as evidence of anything

**The mistake (from earlier in this saga, worth restating here):** Repeatedly cited "git shows X was always configured this way" as if git were a complete historical record, when git for this project only started ~4 weeks before some of these questions came up. Charles had to correct this explicitly more than once.

**Fix going forward:** Always state git's actual starting point when using it as evidence about "how something has always been" or "when something changed." Git's silence about a time period is not evidence that nothing happened, or that something was always configured a certain way — it just means git wasn't watching yet.

---

## 9. Don't conflate two different services — when a specific thing is asked about, stay on THAT thing

**The mistake:** Charles asked specifically about the `cnj-new-node-relay` Discord relay (the `mesh-discord-shim` container). Mid-diagnosis, the thread drifted into fixing the `meshcore-hub-web` 502 (a completely unrelated web-dashboard service) because both surfaced around the same time. This made Charles feel the actual question wasn't being answered, and he had to repeatedly redirect ("I wasn't asking about meshcore-hub"). The two share nothing — different containers, different purposes, different failure modes.

**Fix going forward:** When the person names a specific service/symptom, keep every step tied to THAT service until it's resolved or explicitly parked. If a second unrelated issue surfaces during diagnosis, name it, note it as separate, and ask whether to switch — don't silently fold it into the current thread. Interleaving two investigations makes both feel unresolved and is a fast path to the person feeling like they're going in circles.

## 10. Break the loop with the ONE definitive test — stop waiting on unpredictable events

**The mistake:** For the new-node relay, the approach became "restart it and wait for a real new node to appear to confirm the fix," which is an unpredictable, potentially hours-long wait that left the question perpetually open and the person frustrated. There was a direct test available the whole time (POST directly to the webhook URL and read the HTTP status) that would have settled "is the webhook valid" in seconds, independent of whether a new node happened to show up.

**Fix going forward:** When diagnosis stalls into "wait for an organic trigger," stop and ask: is there a way to *force* the exact code path or *directly test the dependency* right now? A direct webhook POST, a synthetic event, a manual invocation — these break the circle. Waiting on real-world events to confirm a fix is a last resort, not a first one, and it reads as going in circles to the person watching.

---

## General theme across all of these
Most of tonight's real mistakes were **process/communication failures, not technical ones** — moving too fast from "diagnose" to "act" without checking in, trusting stale documentation or paraphrased prior notes instead of live state, and not stating a plan clearly before executing something that touches production config. The technical diagnosis work tonight was strong (the bridge flood, the CoreScope reconnect bug, the cloud-init/etc-hosts bug were all genuinely well-found). The lesson is about slowing down at the handoff points between "I understand the problem" and "I am now changing something," not about diagnostic skill.
