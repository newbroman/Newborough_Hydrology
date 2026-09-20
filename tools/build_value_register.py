#!/usr/bin/env python3
"""
build_value_register.py — every cited quantity and symbol, keyed by its output file.

WHY

  The provenance ledger answers "which EXHIBIT renders this output". This answers
  the same question one level down: which NUMBERS and which SYMBOLS come out of
  this output, and which documents quote them. Between the two, a changed script
  output names everything downstream that has to be re-read — tables, figures,
  cited values and the glyphs that carry them — without a single grep.

  tools/citation_index.csv already holds key -> source_csv -> document for 2,200
  committed values, and tools/symbol_register.csv holds the glyph senses. Neither
  was ever presented output-first, so neither could answer that question.

  The symbol half is the weaker of the two, deliberately so. A glyph is defined
  in prose, not in a CSV; what this does is bind each glyph to the output columns
  whose names carry it, and say plainly which glyphs it could not bind. An
  unbound glyph is not automatically a fault — many are pure notation — but a
  glyph that ought to carry pipeline values and binds to nothing is exactly the
  case that goes stale unseen.

Usage:
    python3 tools/build_value_register.py
    python3 tools/build_value_register.py --check
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-19.

import argparse
import csv as _csv
import pathlib
import re
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "notes/ledgers/VALUE_REGISTER.md"


def _rows(path: pathlib.Path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(_csv.DictReader(fh))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    cites = _rows(REPO / "tools/citation_index.csv")
    by_src: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for r in cites:
        src = pathlib.Path(r.get("source_csv") or "").name or "(no source)"
        key = (r.get("key") or "").strip()
        doc = pathlib.Path(r.get("document") or "").name
        if key:
            by_src[src][key].add(doc)

    # column names available per output, for binding glyphs
    cols: dict[str, set[str]] = {}
    for p in (REPO / "outputs").rglob("*.csv"):
        try:
            with p.open(newline="", encoding="utf-8") as fh:
                cols[p.name] = set(next(_csv.reader(fh), []))
        except (OSError, UnicodeDecodeError, StopIteration):
            continue

    syms = _rows(REPO / "tools/symbol_register.csv")
    bound, unbound = [], []
    for s in syms:
        glyph = (s.get("glyph") or "").strip()
        form = (s.get("form") or "").strip()
        if not glyph:
            continue
        # `form` is a SHAPE ("bare", "subscripted"), not the symbol's text — the
        # first version matched on it and bound 0 of 43. The identifiers live in
        # sense_id and in the pipe-separated context_any tokens.
        cands = {(s.get("sense_id") or "").strip()}
        cands |= {t for t in re.split(r"\|", s.get("context_any") or "")
                  if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,}", t.strip())
                  for t in [t.strip()]}
        cands = {c.lower() for c in cands if len(c) >= 3}
        hits = sorted({f for f, cs in cols.items()
                       if any(c in col.lower() for col in cs for c in cands)})
        (bound if hits else unbound).append(
            (glyph, (s.get("sense_id") or form).strip(),
             s.get("meaning", "")[:60], hits))

    L = ["<!-- GENERATED LEDGER — do not edit.",
         "     Regenerate with: python3 tools/build_value_register.py -->", "",
         "# VALUE_REGISTER — cited quantities and symbols, keyed by output file", "",
         "*Derived live from `tools/citation_index.csv` and `tools/symbol_register.csv`. "
         "Companion to `PROVENANCE_LEDGER.md`, which keys EXHIBITS by output file; "
         "this keys VALUES and SYMBOLS by output file.*", "",
         f"**{len(by_src)} output file(s)** supply **{sum(len(v) for v in by_src.values())} "
         f"cited quantity(ies)**; **{len(syms)} symbol sense(s)** registered, "
         f"{len(bound)} bound to an output column, {len(unbound)} not.", "",
         "## Cited quantities by output file", "",
         "| Output file | Quantity (citation key) | Cited in |", "|---|---|---|"]
    for src in sorted(by_src):
        for i, key in enumerate(sorted(by_src[src])):
            docs = ", ".join(sorted(by_src[src][key]))
            L.append(f"| {'`'+src+'`' if i == 0 else ''} | {key[:70]} | {docs} |")

    L += ["", "## Symbols bound to output columns", "",
          "| Glyph | Sense | Meaning | Output file(s) carrying it |", "|---|---|---|---|"]
    for glyph, form, meaning, hits in sorted(bound):
        L.append(f"| {glyph} | `{form}` | {meaning} | "
                 f"{', '.join('`'+h+'`' for h in hits[:6])}"
                 f"{' …' if len(hits) > 6 else ''} |")
    L += ["", f"## Symbols with no output column ({len(unbound)})", "",
          "*Notation rather than data for most of these. Worth a look when a glyph "
          "here is one the pipeline is supposed to compute.*", "",
          "| Glyph | Sense | Meaning |", "|---|---|---|"]
    for glyph, form, meaning, _ in sorted(unbound):
        L.append(f"| {glyph} | `{form}` | {meaning} |")
    text = "\n".join(L) + "\n"

    if args.check:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if cur != text:
            print("build_value_register: STALE — regenerate")
            return 1
        print("build_value_register: OK — register matches the index")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  ({len(by_src)} output(s), "
          f"{len(syms)} symbol sense(s), {len(unbound)} unbound)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
