#!/usr/bin/env python3
"""
table_source_lint — the config, the source map and the caption agree on
(number -> source) for every generated table.

Why this exists (D-128). A table's caption NUMBER is not stable across the
chapter ODT and the master ODM (and the papers), so a table is identified by its
SOURCE together with its number, never by number alone. This gate holds the three
places a generated table's identity is written to one story:

  * tools/table_configs.py         the engine's per-table config (its source CSV)
  * tools/figure_table_sources.csv the declared (document, number) -> source map
  * the ODT caption                "Table N.M"

For every configured table whose caption carries a "Table N.M" number, the
config's source CSV must be one of the sources figure_table_sources.csv declares
for that (document, number), and that declaration must not be blank. It would
have caught the report9 1.16-1.20 off-by-one on its first run.

Configs whose caption carries no "Table N.M" number (the Methods Supplement
tables, captioned by name) are reported as not-cross-checked, not failed: their
identity is the ms document plus name, outside the number-shift this gate guards.
"""
from __future__ import annotations
import csv
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import table_configs as C   # noqa: E402

FTS = REPO / "tools" / "figure_table_sources.csv"
_NUM = re.compile(r"Table\s+(\d+\.\d+)")


def _document(doc):
    """Config 'doc' -> the document name figure_table_sources uses, or None
    when the config names the document by glob (the Methods Supplement), which
    this number-keyed gate does not cross-check."""
    if isinstance(doc, int):
        return f"report{doc}.odt"
    return None


def _load_map():
    m = {}
    with open(FTS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("type") != "Table":
                continue
            key = (row["document"], row["number"])
            m.setdefault(key, set())
            src = (row.get("source") or "").strip()
            if src:
                m[key].add(os.path.basename(src))
    return m


def main() -> int:
    fts = _load_map()
    fails, skipped, ok = [], [], 0
    for t in C.TABLES:
        doc = _document(t.get("doc"))
        cap = t.get("caption", "")
        mnum = _NUM.search(cap)
        src_alias = t.get("rows", {}).get("source")
        srcs = t.get("sources", {})
        primary = srcs.get(src_alias) if src_alias else next(iter(srcs.values()), None)
        pbase = os.path.basename(primary) if primary else None
        if doc is None or not mnum:
            skipped.append(t["id"])
            continue
        num = mnum.group(1)
        declared = fts.get((doc, num))
        if not declared:
            fails.append(f"{t['id']}: no non-blank source in figure_table_sources.csv "
                         f"for ({doc}, {num})")
        elif pbase not in declared:
            fails.append(f"{t['id']}: config source {pbase} not among "
                         f"figure_table_sources {sorted(declared)} for ({doc}, {num})")
        else:
            ok += 1
    for line in fails:
        print(f"  FAIL  {line}")
    if skipped:
        print(f"  (not cross-checked, caption carries no 'Table N.M': {', '.join(skipped)})")
    print(f"table_source_lint: {ok} table(s) agree; {len(fails)} mismatch(es); "
          f"{len(skipped)} not cross-checked")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
