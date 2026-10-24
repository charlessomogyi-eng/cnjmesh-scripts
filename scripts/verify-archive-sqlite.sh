#!/bin/bash
# Script version: 2026-10-23. See docs/backup-guide.md (section 5).
#
# verify-archive-sqlite.sh -- "light test restore": unpack the SQLite databases from a backup archive into a scratch
# folder, run PRAGMA quick_check on each and count tables/rows, then delete the scratch folder.
# Reads only the archive; touches nothing live. Works on any archive that has a sqlite/ folder
# (cnjmesh1-extra-*.tar.gz). For the main cnjmesh1 archive it also checks the database files it contains (malla, corescope, graywolf...).
#
# Usage (finishes on its own; needs python3 and enough disk for the unpacked DBs, ~1 GB for cnjmesh1-extra):
#   bash scripts/verify-archive-sqlite.sh ~/backups/cnjmesh1-extra-YYYY-MM-DD_HHMM.tar.gz
ARCHIVE="${1:-}"
[ -f "$ARCHIVE" ] || { echo "Usage: $0 <backup.tar.gz>"; exit 1; }
SCRATCH="$(mktemp -d "${HOME}/restore-test.XXXXXX")" || exit 1
trap 'rm -rf "$SCRATCH"' EXIT
echo "Unpacking databases from $(basename "$ARCHIVE") into scratch space ..."
tar -xzf "$ARCHIVE" -C "$SCRATCH" --wildcards '*.db' '*.sqlite' '*.sqlite3' 2>/dev/null
FOUND=0; BAD=0
while IFS= read -r f; do
  FOUND=$((FOUND+1))
  out=$(python3 - "$f" <<'PY'
import sqlite3, sys
p = sys.argv[1]
try:
    d = sqlite3.connect("file:" + p + "?mode=ro", uri=True)
    qc = d.execute("PRAGMA quick_check").fetchone()[0]
    tabs = [r[0] for r in d.execute("select name from sqlite_master where type='table'")]
    rows = sum(d.execute('select count(*) from "%s"' % t.replace('"','""')).fetchone()[0] for t in tabs)
    print("%s | tables=%d rows=%d" % (qc, len(tabs), rows))
    sys.exit(0 if qc == "ok" else 1)
except Exception as e:
    print("ERROR %s" % e); sys.exit(1)
PY
)
  rc=$?
  short="${f#"$SCRATCH"/}"; short="${short#*/}"
  printf '  %-70s %s\n' "$short" "$out"
  [ $rc -eq 0 ] || BAD=$((BAD+1))
done < <(find "$SCRATCH" -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) | sort)
echo "Checked $FOUND database(s); $BAD problem(s)."
if [ "$FOUND" -gt 0 ] && [ "$BAD" -eq 0 ]; then echo "RESULT: all databases in the archive open and pass quick_check."; exit 0; fi
echo "RESULT: PROBLEM, see above."; exit 1
