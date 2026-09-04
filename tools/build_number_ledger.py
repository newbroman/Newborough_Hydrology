#!/usr/bin/env python3
"""
build_number_ledger.py — the pipeline's numbers, unified into one queryable file.

WHY

  The pipeline already emits every citable number as a named row in an
  `outputs/**/*report_numbers*.csv`, all on one schema
  (Parameter, Well, Era, Value, Unit, Note) — ~1,700 rows across 33 files. But
  they are SCATTERED: nothing lets you look a number up in one place, diff the
  set between two runs, or notice that the same named quantity was emitted with
  two different values by two scripts. `cite_check` globs them, matches, and
  throws the result away.

  This concatenates them into ONE ledger — `outputs/number_ledger.csv` — keyed by
  (Parameter, Well, Era), carrying the value, unit, note, and the SOURCE script
  each came from. It is the machine value-layer that complements the hand-curated
  `notes/ledgers/NUMBER_LEDGER.md` (which deliberately holds no values — only which
  numbers are load-bearing, their provenance and volatility, and who cites them).

  It is GENERATED. Regenerate, never hand-edit. It is the single place to look up
  any pipeline number and the foundation the forward citation check reads.

WHAT IT FLAGS

  A COLLISION is one (Parameter, Well, Era) key emitted with materially different
  values by two or more sources. That is a real integrity fault — the same named
  quantity cannot have two values — and it is exactly what a scattered ledger
  hides. Collisions are printed and, with --gate, make the tool exit non-zero.

Usage:
    python3 tools/build_number_ledger.py            # write outputs/number_ledger.csv
    python3 tools/build_number_ledger.py --gate     # non-zero exit if a collision exists
    python3 tools/build_number_ledger.py --stdout    # print, write nothing
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sys
from collections import defaultdict

__version__ = "1.0.0"

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC_GLOB = "outputs/**/*report_numbers*.csv"
OUT = REPO / "outputs" / "number_ledger.csv"
FIELDS = ["Parameter", "Well", "Era", "Value", "Unit", "Note", "Source", "SourceFile"]

# same value if within this relative tolerance (Martin: 0.01 absolute is acceptable
# error, but the same named quantity must render the same). We flag anything that
# differs beyond a hair of floating-point noise; the report shows the magnitude so
# a rounding-only difference is visible as such.
_REL_TOL = 1e-6


def _source_of(path: pathlib.Path, row: dict) -> str:
    if row.get("Source", "").strip():          # 10_consolidated already carries it
        return row["Source"].strip()
    stem = path.stem.replace("_report_numbers", "").replace("report_numbers", "")
    stem = stem.strip("_")
    if stem:
        return stem
    m = re.match(r"(\d+[a-z]?)", path.parent.name)   # e.g. 38_coastal_transect -> 38
    return m.group(1) if m else path.parent.name


def _fval(s: str):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return None


def collect() -> tuple[list[dict], list[tuple]]:
    rows: list[dict] = []
    for p in sorted(REPO.glob(SRC_GLOB)):
        rel = p.relative_to(REPO).as_posix()
        for r in csv.DictReader(p.open(encoding="utf-8", errors="replace")):
            rows.append({
                "Parameter": (r.get("Parameter") or "").strip(),
                "Well": (r.get("Well") or "").strip(),
                "Era": (r.get("Era") or "").strip(),
                "Value": (r.get("Value") or "").strip(),
                "Unit": (r.get("Unit") or "").strip(),
                "Note": (r.get("Note") or "").strip(),
                "Source": _source_of(p, r),
                "SourceFile": rel,
            })
    # collisions: one key, materially different values across DIFFERENT source files
    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["Parameter"], r["Well"], r["Era"])].append(r)
    collisions = []
    for key, rs in by_key.items():
        vals = {}
        for r in rs:
            fv = _fval(r["Value"])
            if fv is not None:
                vals.setdefault(r["SourceFile"], fv)
        distinct = sorted(set(vals.values()))
        if len(distinct) > 1:
            lo, hi = distinct[0], distinct[-1]
            rel = abs(hi - lo) / max(abs(hi), abs(lo), 1e-12)
            if rel > _REL_TOL:
                collisions.append((key, distinct, rel, sorted(vals.items())))
    return rows, collisions


def build() -> tuple[str, list, int]:
    rows, collisions = collect()
    rows.sort(key=lambda r: (r["Source"], r["Parameter"], r["Well"], r["Era"]))
    buf = []
    w = csv.DictWriter(_Sink(buf), fieldnames=FIELDS)
    w.writeheader()
    for r in rows:
        w.writerow(r)
    n_keys = len({(r["Parameter"], r["Well"], r["Era"]) for r in rows})
    return "".join(buf), collisions, n_keys


class _Sink:
    def __init__(self, buf): self.buf = buf
    def write(self, s): self.buf.append(s); return len(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true", help="non-zero exit on any collision")
    ap.add_argument("--stdout", action="store_true", help="print CSV, write nothing")
    a = ap.parse_args()
    text, collisions, n_keys = build()
    n_rows = text.count("\n") - 1
    if a.stdout:
        print(text)
    else:
        OUT.write_text(text, encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}: {n_rows} rows, {n_keys} distinct keys")
    if collisions:
        print(f"\n  {len(collisions)} COLLISION(S) — one named quantity, two values:")
        for (param, well, era), distinct, rel, srcs in sorted(collisions, key=lambda c: -c[2]):
            tag = " ".join(x for x in (param, well, era) if x)
            print(f"      {tag}: {distinct}  (rel {rel:.3%})")
            for sf, v in srcs:
                print(f"          {v}  <- {sf}")
    else:
        print("  no collisions — every named quantity is emitted consistently")
    return 1 if (a.gate and collisions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
