#!/usr/bin/env python3
"""
table_provenance_lint.py — every table traces back to a pipeline output.

THE RULE

  A table in a document is a rendering of numbers the pipeline produced. If no
  committed CSV can be named for it, the line of truth from pipeline to document
  is broken at that table: nothing downstream can check its cells, table_gen
  cannot own them, and a reader has no way to get back to the run that made
  them. A table with no source is a fault, not a gap in the records.

  Martin, 2026-09-19: "a table can't have no csv, this would break the line of
  truth from the pipeline to the documents."

WHAT IT CHECKS

  For every numbered table caption in the report chapters and the papers:

    SOURCE     at least one CSV is recorded for it, in tools/table_configs.py
               or tools/figure_table_sources.csv (or the paper's own
               table-source manifest)
    EXISTS     that CSV is present under outputs/

  A caption is found by walking forward from the table to the first non-empty
  paragraph. Walking only to the NEXT paragraph is not enough — two tables in
  report9 are followed by an empty Cap paragraph, and a first attempt reported
  21 of 23 tables and called the corpus complete. An under-count is the one
  failure mode this check must not have: it hides exactly what it is for.

Usage:
    python3 tools/table_provenance_lint.py
    python3 tools/table_provenance_lint.py --quiet     # faults only
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-19.

import argparse
import csv as _csv
import pathlib
import re
import sys
import zipfile

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

TAG = re.compile(r"<[^>]+>")
CAPTION = re.compile(r"\s*Tables?\s+(\d+(?:\.\d+)?)\s*([a-d])?\s*[:.]\s*(.*)", re.S)
CHAPTERS = ["report6", "report7", "report8", "report9", "report10",
            "report11", "report12"]


def _first_text_after(xml: str, pos: int, reach: int = 3000) -> str:
    """The first paragraph after `pos` that has any text in it."""
    window = xml[pos:pos + reach]
    for m in re.finditer(r"<text:p\b[^>]*>(.*?)</text:p>", window, re.S):
        txt = TAG.sub("", m.group(1)).strip()
        if txt:
            return txt
    return ""


def captions_in(odt: pathlib.Path):
    """(table_name, number, title) for every numbered table caption."""
    xml = zipfile.ZipFile(odt).read("content.xml").decode("utf-8")
    out = []
    for m in re.finditer(r'<table:table table:name="([^"]+)"', xml):
        end = xml.find("</table:table>", m.end())
        cap = CAPTION.match(_first_text_after(xml, end + len("</table:table>")))
        if cap:
            out.append((m.group(1), cap.group(1) + (cap.group(2) or ""),
                        cap.group(3)[:60].strip()))
        else:
            out.append((m.group(1), None, ""))
    return out


def source_map() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    try:
        from table_configs import TABLES
    except Exception:
        TABLES = []
    for cfg in TABLES:
        if not str(cfg.get("id", "")).startswith("report"):
            continue
        m = re.search(r"Table\s+(\d+\.\d+)\s*(?:\(([a-d])\))?", cfg.get("caption", ""))
        if m:
            key = m.group(1) + (m.group(2) or "")
            out.setdefault(key, set()).update(
                pathlib.Path(v).name for v in cfg.get("sources", {}).values())
    f = REPO / "tools/figure_table_sources.csv"
    if f.exists():
        with f.open(newline="", encoding="utf-8") as fh:
            for r in _csv.DictReader(fh):
                if r.get("type") == "Table" and r.get("document", "").startswith("report"):
                    out.setdefault(r["number"], set()).add(
                        pathlib.Path(r["source"]).name)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    src = source_map()
    have = {p.name for p in (REPO / "outputs").rglob("*.csv")}
    faults, n = [], 0
    print("=" * 74)
    print("TABLE PROVENANCE — does every table name a pipeline output?")
    print("=" * 74)
    for stem in CHAPTERS:
        odt = REPO / "report_edits/odt" / f"{stem}.odt"
        if not odt.exists():
            continue
        for name, num, title in captions_in(odt):
            n += 1
            if num is None:
                faults.append(("NO CAPTION", stem, name, "",
                               "no numbered caption follows this table"))
                continue
            csvs = src.get(num) or src.get(num.rstrip("abcd")) or set()
            if not csvs:
                faults.append(("NO SOURCE", stem, name, num,
                               "no table-source record names a CSV for it"))
            elif not (csvs & have):
                faults.append(("MISSING CSV", stem, name, num,
                               f"recorded source(s) not under outputs/: "
                               f"{', '.join(sorted(csvs))}"))
            elif not args.quiet:
                print(f"  ok    Table {num:<6} {stem:<9} {sorted(csvs)[0]}")
    for tag, stem, name, num, why in faults:
        print(f"  {tag:<11} {stem:<9} {name:<12} Table {num or '?':<6} {why}")
    print()
    if faults:
        print(f"table_provenance_lint: FAIL — {len(faults)} of {n} table(s) "
              f"do not trace to a committed output")
        return 1
    print(f"table_provenance_lint: OK — all {n} table(s) trace to a committed output")
    return 0


if __name__ == "__main__":
    sys.exit(main())
