# cnjmesh.me website

The public-facing site at cnjmesh.me. Rebuilt from scratch (Sept 2026) to replace the old Google Sites page, which couldn't host custom design or content beyond Google's own block editor.

Source of truth for the live files: `website/cnjmesh-me/` in this repo. That folder is a straight backup of whatever's actually deployed — if you need to rebuild the site or recover from a lost laptop, start there.

## What it is

Four static HTML pages, no build system, no framework, no dependencies:

- `index.html` — homepage: hero, "Get on the mesh" (Meshtastic/MeshCore cards), live network maps, coverage, Discords, friends/resources
- `about.html` — network identity, protocols, coverage story, partner networks
- `getting-started.html` — quick-start for both protocols + advanced node-config reference
- `contact.html` — Discord/Reddit links + embedded Google Form

Each page is fully self-contained — CSS is inlined in a `<style>` block in every file rather than pulled from a shared `styles.css`. This was a deliberate tradeoff: a shared stylesheet is cleaner to maintain, but broke when opened as a local file (browsers don't reliably load a sibling CSS file from a `file://` path, and this became a real problem during development). Self-contained pages always render correctly regardless of how they're opened. Cost: a sitewide style change means editing the `<style>` block in all four files, not one.

Design: light editorial theme — paper white (`#f6f6f2`), near-black ink, "signal red" accent (`#c42b3d`). Fonts: Barlow Condensed (display), Public Sans (body), JetBrains Mono (data/config readouts). Hero includes a hand-plotted NJ outline (not a live map — static SVG path) showing the CNJ core and rough links to Jersey City, Morristown, Trenton, Toms River, and the Lehigh Valley.

Branding: header reads "CNJ & South Jersey Mesh" on desktop, shortens to "CNJ Mesh" below 640px width to avoid wrapping/clipping in the nav bar.

## Hosting & DNS

- **Host:** Netlify, project name `tranquil-palmier-f6462b` (netlify.app subdomain), under Charles's personal Netlify account (signed up via Google after starting as an anonymous Netlify Drop).
- **Deploy method:** manual — drag the local project folder onto the Netlify project's "deploy new changes" drop zone. **There is no Git-based deploy set up yet** (see To Do below); this is a meaningful gap given the repo's usual pattern of Claude-driven git commits.
- **DNS:** at Cloudflare (same zone as the rest of cnjmesh.me infra).
  - `cnjmesh.me` — A record → `75.2.60.5` (Netlify's load balancer IP; used instead of the ALIAS/ANAME option since a plain A record was simpler to execute correctly under the circumstances — see gotcha below)
  - `www.cnjmesh.me` — CNAME → `tranquil-palmier-f6462b.netlify.app`
  - Both records replaced old Google Sites entries (four A records: `198.185.159.144`, `198.49.23.145`, `198.49.23.144`, `198.185.159.145`, plus a `www` CNAME to `ghs.googlehosted.com`). All were deleted/replaced, not left in place — Google Sites is no longer authoritative for this domain.

## Known gotchas

- **The manual folder-drag deploy has no diffing and no version history.** Every deploy re-uploads all four files as a full folder. If even one file in the local folder is stale (an old copy sitting there from an earlier download), it silently overwrites the live version with old content — this happened twice during the initial build (About and Contact reverted to pre-"Central & South" copy, then index.html reverted separately) and wasn't caught until manually spot-checking the live pages afterward. **Always verify all four pages after any deploy, not just the one you meant to change** — don't trust that only your intended file changed.
- **The live site's actual current content is not guaranteed to match this repo** until someone re-syncs `website/cnjmesh-me/` after each deploy. Treat this folder as best-effort backup, not automatically authoritative — check `https://cnjmesh.me` itself for ground truth, or diff against it, before assuming a file here is current.
- Netlify Drop's free anonymous links expire in 1 hour unless claimed with an account. This project has been claimed (see Hosting above), so this no longer applies — but if a *new* Netlify Drop is ever created from scratch, remember to claim it before the countdown ends or the link dies.

## To do / open items

- **Migrate to Git-based Netlify deploy.** Connect this repo (or a dedicated one) to Netlify so pushes here auto-deploy, instead of manually dragging a folder from a laptop. This would fix the stale-file class of bug above entirely and matches how the rest of this project already works (Claude commits/pushes, Charles doesn't run git by hand).
- MeshCore channel list for the Getting Started page — not yet written; ask Charles for exact channel names + region scoping before adding.
- Full MeshCore repeater config section (advert intervals, `region put`/`region allowf` setup) — not yet written; needs CNJ-specific region codes from Charles first.
- Consider adding a lightweight "Network Status / Updates" section (not a full blog) if there's a recurring stream of newsworthy events worth surfacing to visitors — discussed but not decided as of this writing.
