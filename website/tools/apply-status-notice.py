#!/usr/bin/env python3
"""Add the "Currently unavailable" notice to the CNJ Mesh home page.

Usage:  python3 apply-status-notice.py path/to/index.html

What it does (safe to run more than once, it replaces its own block):
  * adds a small CSS block just before the first </style>
  * adds a small script just before </body>

What the script on the page does:
  * fetches STATUS_URL (a status.json written by the status checker)
  * if the file is missing, unreadable, malformed, or older than 15 minutes,
    it does NOTHING, so the buttons look normal (fail safe)
  * otherwise, for every link button whose host is listed with "up": false,
    it adds a red "Currently unavailable" tag. The link still works.

status.json format (the checker writes this):
  {"generated": "2026-11-06T23:00:00Z",
   "services": {"malla.cnjmesh.me": {"up": true},
                "malla2.cnjmesh.me": {"up": false}}}
Keys are hostnames exactly as they appear in the button links.
"""
import re
import sys

STATUS_URL = "https://status.cnjmesh.me/status.json"

CSS = """/* status-notice:start */
.is-down { border-color: var(--red) !important; }
.link-btn.is-down { color: var(--red); }
.down-note {
  font-family: 'JetBrains Mono', monospace; font-size: .62rem; font-weight: 500;
  letter-spacing: .08em; text-transform: uppercase; line-height: 1.3;
  color: var(--red); border: 1px solid var(--red); padding: 2px 7px;
  animation: down-pulse 2.4s ease-in-out infinite;
}
.btn-primary.is-down .down-note { color: #fff; border-color: #fff; }
@keyframes down-pulse { 50% { opacity: .45; } }
@media (prefers-reduced-motion: reduce) { .down-note { animation: none; } }
/* status-notice:end */
"""

JS = """<!-- status-notice:start -->
<script>
(function () {
  var STATUS_URL = "__STATUS_URL__";
  var MAX_AGE_MS = 15 * 60 * 1000;
  try {
    fetch(STATUS_URL, { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error("status " + r.status); return r.json(); })
      .then(function (d) {
        var t = d && Date.parse(d.generated);
        if (!isFinite(t) || Math.abs(Date.now() - t) > MAX_AGE_MS) return;
        if (!d.services || typeof d.services !== "object") return;
        var links = document.querySelectorAll(".link-btn, .watch-btns a");
        for (var i = 0; i < links.length; i++) {
          var a = links[i], host;
          try { host = new URL(a.href).hostname; } catch (e) { continue; }
          var s = d.services[host];
          if (!s || s.up !== false || a.querySelector(".down-note")) continue;
          var note = document.createElement("span");
          note.className = "down-note";
          note.textContent = "Currently unavailable";
          a.insertBefore(note, a.querySelector(".arrow") || null);
          a.classList.add("is-down");
          a.title = "Our status check could not reach this tool at " + d.generated;
        }
      })
      .catch(function () {});
  } catch (e) {}
})();
</script>
<!-- status-notice:end -->
""".replace("__STATUS_URL__", STATUS_URL)


def main(path):
    s = open(path, encoding="utf-8").read()
    # remove any earlier copy of our blocks
    s = re.sub(r"/\* status-notice:start \*/.*?/\* status-notice:end \*/\n?", "", s, flags=re.S)
    s = re.sub(r"<!-- status-notice:start -->.*?<!-- status-notice:end -->\n?", "", s, flags=re.S)
    assert s.count("</style>") >= 1, "no </style> found"
    assert s.count("</body>") == 1, "expected exactly one </body>"
    s = s.replace("</style>", CSS + "</style>", 1)
    s = s.replace("</body>", JS + "</body>", 1)
    open(path, "w", encoding="utf-8").write(s)
    print("status notice applied to", path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
