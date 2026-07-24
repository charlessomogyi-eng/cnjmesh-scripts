# CLAUDE_CONTEXT.md — CNJ Mesh — START HERE

**For AI assistants:** This repo's context is split into three files. Fetch in this order:

1. **`todos.md`** — short, current, open action items only. Always fetch this.
2. **`cnjmesh1-operations.md`** — short, current-state reference (hosts, ports, credentials, USB maps, known issues, philosophy notes). Always fetch this too.
3. **`session-log.md`** — long, full narrative history, append-only. Only fetch this if you need backstory on *why* something is the way it is, or detail behind a specific open to-do. Not meant to be re-read in full each session.

```bash
curl -s https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/todos.md
curl -s https://raw.githubusercontent.com/charlessomogyi-eng/cnjmesh-scripts/main/cnjmesh1-operations.md
```

Do not ask Charles to re-explain anything documented in those files. Treat him as an experienced operator — ~25 years IT/backup/recovery background (Dell Technologies SE), built CNJ Mesh from scratch into a 300+ node dual-protocol (Meshtastic + MeshCore) network. Not a software developer but highly technical — explain plainly, don't over-explain basics.

**Always name which host a command runs on** ("Run this on cnjmesh1") — Charles regularly has multiple SSH sessions open across cnjmesh1/2/3 simultaneously.

**Philosophy:** keep things simple. Charles wants tools that work reliably so he can focus on actual radio contacts, not on managing tooling. Default to the simplest fix for a real, already-experienced problem — don't build speculative monitoring/architecture ahead of an actual need.

---

## How to End Each Session
1. Update `todos.md` — delete finished items, add new ones. Keep it lean.
2. If facts about current infrastructure changed (IPs, ports, USB paths, credentials, what's running where), update `cnjmesh1-operations.md`.
3. Append a dated entry to `session-log.md` for what happened this session — narrative is fine there, it's never re-read in full.
4. Push all changed files to GitHub using the token Charles provides.
5. Remind Charles to provide his GitHub token if not already given, and to revoke it after use if it was pasted in chat.

---

## GitHub Repo
`github.com/charlessomogyi-eng/cnjmesh-scripts`
Cloned on cnjmesh1 at `~/cnjmesh-scripts`

Other files in this repo:
- `README.md` — full rebuild-from-scratch guide (disaster recovery, not day-to-day reference)
- `docs/` — supporting research notes referenced from the files above

*(This file replaces the old single-file CLAUDE_CONTEXT.md, split on 2026-07-24 for readability. The full pre-split history is preserved verbatim in `session-log.md` and in this file's git history — nothing was deleted, only reorganized. A backup of the pre-split file also exists at `CLAUDE_CONTEXT-backup-2026-07-24.md`.)*
