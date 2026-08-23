#!/usr/bin/env python3
"""
table_renumber_plan.py — derive the Table permutation from the captions themselves.

WHY IT IS NOT HAND-ENTERED

  A move inside the report renumbers tables the same way it renumbers figures,
  and the numbers that change are not a contiguous block: the §4.10 relocation
  turned 16 -> 20 while 17,18,19,20 each stepped down one. Typing that mapping
  out is one transposition away from silently re-pointing a reference at the
  wrong table.

  reference_lint already pins WHAT EACH NUMBER MEANT in
  tools/reference_index_table.csv, keyed on the caption's own words. So the
  permutation is recoverable with no judgement at all: for each snapshot row,
  find the position that caption occupies NOW. That is the new number.

  The plan is refused if any caption is unmatched or if two snapshot rows land
  on the same new number, because either means the caption text itself changed
  and the mapping is then a guess.

Usage:
    python3 tools/table_renumber_plan.py            # print, write plan
    python3 tools/table_renumber_plan.py --dry-run  # print only
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23.

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_lint import captions                              # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SNAP = REPO / "tools/reference_index_table.csv"
OUT = REPO / "tools/renumber_plan_table.csv"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not SNAP.exists():
        raise SystemExit(f"no snapshot at {SNAP} — nothing to compare against")

    with SNAP.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # snapshot columns are written by reference_lint --snapshot
    key_n = "number" if "number" in rows[0] else list(rows[0])[0]
    key_t = "title" if "title" in rows[0] else list(rows[0])[-1]

    caps = captions("table")
    now = {t: n for _doc, n, _cached, t in caps}
    if len(now) != len(caps):
        raise SystemExit("two tables share a caption — permutation not derivable")

    plan, unmatched, seen = [], [], {}
    for r in rows:
        old, title = str(r[key_n]), r[key_t]
        new = now.get(title)
        if new is None:
            unmatched.append((old, title))
            continue
        new = str(new)
        if new in seen:
            raise SystemExit(f"two old numbers ({seen[new]}, {old}) map to {new}")
        seen[new] = old
        plan.append((old, new, title))

    if unmatched:
        print("  CAPTION TEXT CHANGED — cannot derive a mapping for:")
        for old, title in unmatched:
            print(f"      Table {old}  {title[:70]}")
        raise SystemExit("refusing to write a partial plan")

    moved = [p for p in plan if p[0] != p[1]]
    print(f"  {len(plan)} caption(s) matched; {len(moved)} number(s) move\n")
    for old, new, title in moved:
        print(f"      Table {old:>3} -> {new:<3}  {title[:62]}")

    if args.dry_run:
        print("\n  dry run — nothing written")
        return 0
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "old", "new", "title"])
        for old, new, title in moved:
            w.writerow(["table", old, new, title])
    print(f"\n  written: {OUT.relative_to(REPO)} ({len(moved)} row(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
