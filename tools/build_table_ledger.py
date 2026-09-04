#!/usr/bin/env python3
"""
build_table_ledger.py — the table ledger, derived rather than written.

WHY DERIVED

  notes/ledgers/README.md listed TABLE_LEDGER.md as one of three ledgers "to
  build", seeded from tools/figure_table_manifest.csv. Generated for the same
  reason as the figure ledger: a hand-maintained table index goes stale the first
  time a table is renumbered or its source CSV moves.

WHAT IT ANSWERS

  For each report table: which document carries it, its number there, the source
  file (generating script / CSV), and whether that source resolves on disk. The
  "table no. -> source CSV -> document + location" lookup.

  Global caption titles are in tools/reference_index_table.csv under a separate
  sequential numbering and are listed in their own section (as for figures).

  Seeded from tools/figure_table_manifest.csv (type == Table) and
  tools/reference_index_table.csv. Pure stdlib.

  Regenerate with: python3 tools/build_table_ledger.py
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import datetime

__version__ = "1.0.0"

REPO = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = REPO / "tools" / "figure_table_manifest.csv"
INDEX = REPO / "tools" / "reference_index_table.csv"
DEFAULT_OUT = REPO / "notes" / "ledgers" / "TABLE_LEDGER.md"

KIND = "Table"
BANNER = (
    "<!-- GENERATED LEDGER — do not edit.\n"
    "     Regenerate with: python3 tools/build_table_ledger.py -->\n\n"
)


def _numkey(s: str):
    parts = []
    for p in str(s).replace("-", ".").split("."):
        parts.append((0, int(p)) if p.isdigit() else (1, p))
    return parts


def _resolves(status: str) -> bool:
    s = (status or "").strip()
    if "/" in s and not s.lower().startswith(("missing", "pending", "unbuilt")):
        return (REPO / s).exists()
    return False


def build() -> str:
    rows = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8"))
            if r.get("type", "").strip().lower() == KIND.lower()]
    by_doc: dict[str, list[dict]] = {}
    for r in rows:
        by_doc.setdefault(r["document"].strip(), []).append(r)

    n_total = len(rows)
    n_ok = sum(1 for r in rows if _resolves(r.get("resolved_path_or_status", "")))
    n_flag = n_total - n_ok

    out = [BANNER.rstrip("\n"), "",
           "# TABLE_LEDGER — tables by document, source, and resolution",
           "",
           "*Generated from `tools/figure_table_manifest.csv` (Table rows). "
           "Living current-state; regenerate, do not hand-edit.*",
           "",
           f"**{n_total} tables** across {len(by_doc)} documents — "
           f"{n_ok} resolve on disk, {n_flag} flagged (status shown).",
           ""]

    for doc in sorted(by_doc):
        out.append(f"## {doc}")
        out.append("")
        out.append("| Table | Source file | Resolved path / status | On disk |")
        out.append("|---|---|---|---|")
        for r in sorted(by_doc[doc], key=lambda x: _numkey(x["number"])):
            status = (r.get("resolved_path_or_status", "") or "").strip()
            ok = "yes" if _resolves(status) else "—"
            src = (r.get("source_file", "") or "").strip()
            out.append(f"| {r['number']} | `{src}` | `{status}` | {ok} |")
        out.append("")

    if INDEX.exists():
        idx = list(csv.DictReader(INDEX.open(encoding="utf-8")))
        out.append("## Caption index (global numbering)")
        out.append("")
        out.append("*From `tools/reference_index_table.csv`. Numbered globally, "
                   "not per-document.*")
        out.append("")
        out.append("| No. | Document | Title |")
        out.append("|---|---|---|")
        for r in idx:
            title = (r.get("title", "") or "").replace("|", "\\|").strip()
            out.append(f"| {r['number']} | {r['document']} | {title} |")
        out.append("")

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    out.append(f"*Generated {stamp} by `tools/build_table_ledger.py` "
               f"v{__version__}.*")
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stdout", action="store_true", help="print, write nothing")
    ap.add_argument("--out", help="write somewhere other than the default")
    a = ap.parse_args()
    text = build()
    if a.stdout:
        print(text)
        return 0
    dest = pathlib.Path(a.out) if a.out else DEFAULT_OUT
    dest.write_text(text, encoding="utf-8")
    print(f"wrote {dest.relative_to(REPO)}: {text.count(chr(10))} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
