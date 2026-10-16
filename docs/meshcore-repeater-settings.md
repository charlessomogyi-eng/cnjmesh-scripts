# MeshCore Repeater Settings — Community Recommendations

**Source:** Lbibass, Discord `#meshcore-repeater-settings` channel — experienced
operator managing ~6 repeaters in NC (RDU area). Shared 2026-07-11.

## Settings

| Setting | Command | Value | Why |
|---|---|---|---|
| Flood Advert Interval | (repeater config) | 47 hours | Reduces mesh congestion as the mesh grows |
| Zero-hop Advert Interval | (repeater config) | 120 min minimum | Not repeated, so lowers congestion — but still costs airtime as a large packet |
| Path Hash Size | `set path.hash.mode 1` (2 bytes) or `set path.hash.mode 2` (3 bytes) | 1 or 2 | Prevents repeater ID collisions. Mode 1 caps max hops at 32, mode 2 at 21. Lbibass reports rarely seeing >20 hops even across long distances (Atlanta→RDU NC), so 21-hop cap is generally sufficient |
| RX Delay | `set rxdelay 6` | 6 | Scales with signal strength — strong signal repeats sooner, weak signal delays longer so closer/stronger repeaters get priority to retransmit first, reducing collisions |
| TX Delay | `set txdelay 2` | 2 (max allowed) | Sets the maximum number of repeat slots |
| Direct TX Delay | `set direct.txdelay 1` | 1 | Applies to direct messages (repeater admin commands, traces) — keeps those snappy/quick while still reducing collision risk vs. no delay |

## Why delays matter
By default there's a very short interval between a repeater receiving a packet
and retransmitting it. On busy/dense meshes this causes fewer transmission
windows, which can lead to two repeaters transmitting simultaneously —
packet collisions and dropped packets. Increasing the repeat delay windows
(rxdelay/txdelay above) reduces this.

## IMPORTANT — Reset path after changing settings
Per Bob_is_Digital/NJ-Mesh (2026-07-12): after changing repeater settings,
**reset your path**. He was locked out of remote admin until doing this —
resetting the path fixed it.

## Applicability to CNJ Mesh
Not yet applied to KPR1/KPR2. Worth evaluating against current settings
(910.525 MHz / BW 62.5 / SF7 / CR5 / TX22) next time repeater config is
touched — see todo #8 (node tagging) and #9 (KPR1 retirement decision) in
CLAUDE_CONTEXT.md for related upcoming work.


## Update 2026-10-13: 500 kHz cutover started Oct 11, 2026 (from KPR3 handoff; **[S]**, unverified)
The "Applicability to CNJ Mesh" values above (910.525 / BW 62.5 / SF7 / CR5 / TX22) are no longer universal. On Oct 11 Charles moved **KPR3** (and the T-Deck companion KPC2) to **910.525 MHz, BW 500 kHz, SF10, CR5**, using numbers from community admin Tck; he reports most of NJ has moved except some near the south Jersey shore. The Observer followed on Oct 13 (cnjmesh3, via `meshcore-cli`) and KPR2 and KPC1 on Oct 14 (KPR2 via repeater console, confirmed on 500 kHz later that day, see `known-issues.md`); only KPR1 remains on 62.5 kHz (waiting on Tilly), so nodes on different settings cannot hear each other or be remotely administered. See `cnjmesh1-operations.md` for details.

CLI notes from the handoff (MeshCore 1.17.1, **[S]**, not tested remotely): `set radio <freq>,<bw>,<sf>,<cr>` needs a reboot; `tempradio <freq>,<bw>,<sf>,<cr>,<mins>` reverts automatically and isn't saved; `set flood.advert.interval` valid range is 3-168 h (0 is invalid — an earlier chat said otherwise); no documented "disable TX" command for repeater firmware (workarounds: `set repeat off`, `tempradio`, lower `set tx`). A stale saved "Out Path" on a contact may break remote login after a bandwidth change [S]; the page above already says to reset the path after changing settings.

## Update 2026-10-16: LV Mesh and 500 kHz — Discord notes (from a "KP COMMS" Discord screenshot; **[S]** secondhand, nothing verified directly with LV Mesh)
Charles shared a private Discord exchange with Tck (Tilly) about Lehigh Valley (LV) Mesh and the 500 kHz move. Recorded as relayed, with tags:
- Tck, 6:31 PM: "Doing some 62.5 testing with lv mesh. They are working on a bridge to use both bandwidths." **[S]**
- Tck, 6:51 PM: LV Mesh "didn't want to move to 500", but plans to run their towers on 500 kHz and "run some kind of bridge to make them mesh" **[S]** — so LV Mesh is (per Tck) staying on 62.5 kHz for now and working on a bridge between 62.5 and 500 kHz. No details, no timeline.
- Charles, 6:55 PM: a person from LV Mesh told him they were happy CNJ "pushed back" and to "be aware of snakes" **[S]**; Tck replied that they are nice and "have big plans".
- Context: CNJ's 500 kHz move was driven by a possible FCC compliance concern about 62.5 kHz (**[S]**, unverified); some in the community say 500 kHz raises the noise floor.
- Practical meaning for CNJ: nodes on 62.5 kHz and nodes on 500 kHz cannot hear each other over RF, so a bridge (MQTT or other) is the only link between the two groups. KPR1 is still on 62.5 kHz (Tilly's tests) — see `todos.md`. The existing Tilly/LVMesh packet-bridge work is in `session-log.md` (Jul 27, 2026).
- Charles, Oct 16 2026 [stated]: after moving to 500 kHz he now sees hundreds of MeshCore nodes; at 62.5 kHz he was "on an island" once everyone else left it. (Observation only, no counts recorded. A node count from CoreScope before/after would make this measurable.)
