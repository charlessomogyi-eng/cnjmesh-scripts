# How to update the cnjmesh.me website (manual Netlify deploy)

For when you rarely do this and forget the steps. The site is hosted on Netlify (project `tranquil-palmier-f6462b`, under Charles's personal Netlify account) and is **not** connected to Git, so changing a file in this repo does **not** change the live site. A person has to upload the folder.

## The one rule that prevents damage

A drag-and-drop deploy uploads a whole folder as the new version of the site. Netlify's docs do not say whether files missing from the folder are removed, so **assume they are.** The folder you drag must therefore contain **every page that should be live**, built from the *currently live* files, not from the repo backup. The repo backup (`website/cnjmesh-me/`) was found behind the live site on Oct 14, 2026 (missing the `CentralNJ-MC` how-to on the homepage and the `network-news.html` page).

## Steps

1. **Get the live files first (this is also your backup).**
   - Sign in at <https://app.netlify.com/> and open the project named **cnjmesh.me** in the Projects list (team "CommunityKitchen"; seen on screen Oct 16, 2026, last published Sep 5 via Netlify Drop). Do not touch the other projects in the list (communityoven.net and two others). The project's netlify.app subdomain may still be `tranquil-palmier-f6462b`.
   - Open **Deploys**, click the most recent *Published* deploy to open its detail page.
   - Download the deploy as a zip (a download arrow on the detail page, or the download link in the **Deploy file explorer** below the deploy log; Netlify has described both, and the button may be labeled differently in the current UI).
   - Unzip it into a new folder, for example `cnjmesh-live-2026-10-14`. Keep the original zip untouched as the backup.
2. **Replace only the files you are changing.** Copy the new file(s) over the same-named file(s) in that unzipped folder. For the Oct 14, 2026 change, that is one file: `getting-started.html` (staged at `website/pending/getting-started.html` in this repo; the unzipped folder also holds the other pages and any images).
3. **Check locally.** Double-click `getting-started.html` in the folder to open it in a browser. Confirm the page shows what you expect.
4. **Deploy.** Back on the project's **Deploys** page, scroll to the bottom and drag the whole unzipped folder (the folder itself, not a zip) onto the drop zone. Docs: <https://docs.netlify.com/deploy/create-deploys/>.
5. **Verify live.** Open <https://cnjmesh.me/getting-started> in a private/incognito window (avoids cached copies) and confirm the change. Also click through `/`, `/about`, `/contact` and `/network-news.html` to confirm nothing disappeared.
6. **If something broke:** on the Deploys list, open the previous good deploy and use **Publish deploy** to roll back. Netlify keeps old deploys.
7. **Tell Claude the deploy is done** so the repo backup (`website/cnjmesh-me/`) can be re-synced. Best: attach the downloaded zip (or the changed files) to the chat.

## Known limits

- Everything above about Netlify's buttons comes from Netlify's docs and blog posts, not from a live look at the dashboard; names can differ slightly.
- Claude's shell can't reach cnjmesh.me, so it can't fetch the raw live HTML. That is why step 1 is needed.
