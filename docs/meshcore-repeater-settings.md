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
