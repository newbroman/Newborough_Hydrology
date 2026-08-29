#!/usr/bin/env python3
"""
geo_provenance — every file in data/geo/ is accounted for in GEO_PROVENANCE.md.

Why this exists.

  The vector layers under `data/geo/` underpin published figures and at least one
  published number — D-060's long-run coastal retreat rate, measured by hand in
  QGIS from `coast1899.kml` and `DCoast_2015.kml`, neither of which any script
  reads. A layer nothing regenerates is a layer nothing re-checks, so an error in
  it surfaces at review rather than at run time.

  This does not attempt to verify provenance, which is a human fact. It verifies
  that provenance was *written down*: a file with no entry is invisible, and an
  entry naming a file that has gone is the same rot `context_for.py --audit`
  looks for in the decision log.

Usage:
    python3 tools/geo_provenance.py            # report
    python3 tools/geo_provenance.py --strict   # non-zero exit on any gap
    python3 tools/geo_provenance.py --todo     # list the TO CONFIRM fields only
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-08-28.

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GEO = REPO / "data" / "geo"
DOC = GEO / "GEO_PROVENANCE.md"
# Sidecars travel with their layer and are covered by that layer's entry.
SIDECAR_SUFFIXES = {".qmd"}
SELF = {"GEO_PROVENANCE.md"}


def main(argv: list[str]) -> int:
    if not DOC.is_file():
        print(f"MISSING  {DOC.relative_to(REPO)} — no provenance record at all")
        return 1
    text = DOC.read_text(encoding="utf-8")

    if "--todo" in argv:
        todos = re.findall(r"\*\*TO CONFIRM[^*]*\*\*|TO CONFIRM[^.\n]*", text)
        print(f"# Open provenance questions — {len(todos)}\n")
        for line in text.splitlines():
            if "TO CONFIRM" in line or "TO RESOLVE" in line:
                print("  " + line.strip().lstrip("-|* ")[:150])
        return 0

    # Recursive: historic sheets live in data/geo/histmaps/ by the .gitignore
    # convention, and a top-level-only scan reported the restored 1899 raster as
    # missing the moment it was filed correctly.
    on_disk = {p.name for p in GEO.rglob("*")
               if p.is_file() and p.name not in SELF
               and p.suffix.lower() not in SIDECAR_SUFFIXES}
    named = {n for n in on_disk if f"`{n}`" in text}
    # A sidecar is fine either named explicitly or covered by its layer.
    unlisted = sorted(on_disk - named)
    # Entries pointing at something no longer present.
    referenced = set(re.findall(r"`([A-Za-z0-9 _.-]+\.(?:kml|geojson|tif|qmd))`", text))
    present = {p.name for p in GEO.rglob("*") if p.is_file()}
    gone = sorted(r for r in referenced
                  if not (GEO / r).exists() and Path(r).name not in present)

    todo_count = text.count("TO CONFIRM") + text.count("TO RESOLVE")
    print(f"# data/geo provenance — {len(on_disk)} files\n")
    print(f"{len(named)} of {len(on_disk)} have an entry.")
    if unlisted:
        print(f"\n## No entry in GEO_PROVENANCE.md ({len(unlisted)})")
        print("Undocumented, so unreviewable.\n")
        for n in unlisted:
            print(f"  {n}")
    if gone:
        print(f"\n## Named in the record but not on disk ({len(gone)})\n")
        for n in gone:
            print(f"  {n}")
    if todo_count:
        print(f"\n{todo_count} field(s) still marked TO CONFIRM / TO RESOLVE "
              f"— `--todo` lists them.")
    if not unlisted and not gone:
        print("\nEvery file is accounted for.")
    bad = bool(unlisted or gone)
    return 1 if (bad and "--strict" in argv) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
