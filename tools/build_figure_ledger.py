#!/usr/bin/env python3
"""
build_figure_ledger.py — the figure ledger, derived rather than written.

WHY DERIVED

  notes/ledgers/README.md listed FIGURE_LEDGER.md as one of three ledgers "to
  build", seeded from tools/figure_table_manifest.csv. A hand-maintained figure
  ledger would go stale the first time a figure was renumbered or a PNG moved —
  exactly the decay the ledgers exist to prevent. So it is generated from the
  manifest, which the figure/table pipeline already keeps current.

WHAT IT ANSWERS

  For each report figure: which document carries it, its number there, the
  source file (script output / PNG), and whether that output resolves on disk or
  is flagged. This is the "figure no. -> source -> PNG -> regen state" lookup.

  Global caption titles live in tools/reference_index_figure.csv under a
  different (sequential) numbering; the cross-reference that once bridged the two
  schemes (NRG_report_figure_xref_2026-08-13.csv) was lost and could not be
  recovered under T-10, so titles are listed in their own section rather than
  joined row-by-row. The join is a future enhancement if the xref is rebuilt.

  Seeded from tools/figure_table_manifest.csv (type == Figure) and, for the
  caption index, tools/reference_index_figure.csv. Pure stdlib.

  Regenerate with: python3 tools/build_figure_ledger.py
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import datetime

__version__ = "1.0.0"

REPO = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = REPO / "tools" / "figure_table_manifest.csv"
INDEX = REPO / "tools" / "reference_index_figure.csv"
DEFAULT_OUT = REPO / "notes" / "ledgers" / "FIGURE_LEDGER.md"

KIND = "Figure"
BANNER = (
    "<!-- GENERATED LEDGER — do not edit.\n"
    "     Regenerate with: python3 tools/build_figure_ledger.py -->\n\n"
)


def _numkey(s: str):
    """Sort '1.10' after '1.2' by splitting into integer parts where possible."""
    parts = []
    for p in str(s).replace("-", ".").split("."):
        parts.append((0, int(p)) if p.isdigit() else (1, p))
    return parts


def _resolves(status: str) -> bool:
    """A manifest cell that names a path resolves iff that path exists."""
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
           "# FIGURE_LEDGER — figures by document, source, and resolution",
           "",
           "*Generated from `tools/figure_table_manifest.csv` (Figure rows). "
           "Living current-state; regenerate, do not hand-edit.*",
           "",
           f"**{n_total} figures** across {len(by_doc)} documents — "
           f"{n_ok} resolve on disk, {n_flag} flagged (status shown).",
           ""]

    for doc in sorted(by_doc):
        out.append(f"## {doc}")
        out.append("")
        out.append("| Figure | Source file | Resolved path / status | On disk |")
        out.append("|---|---|---|---|")
        for r in sorted(by_doc[doc], key=lambda x: _numkey(x["number"])):
            status = (r.get("resolved_path_or_status", "") or "").strip()
            ok = "yes" if _resolves(status) else "—"
            src = (r.get("source_file", "") or "").strip()
            out.append(f"| {r['number']} | `{src}` | `{status}` | {ok} |")
        out.append("")

    # Caption index (separate scheme — see module docstring)
    if INDEX.exists():
        idx = list(csv.DictReader(INDEX.open(encoding="utf-8")))
        out.append("## Caption index (global numbering)")
        out.append("")
        out.append("*From `tools/reference_index_figure.csv`. Numbered globally, "
                   "not per-document; the xref bridging this to the manifest "
                   "numbers above was lost under T-10.*")
        out.append("")
        out.append("| No. | Document | Title |")
        out.append("|---|---|---|")
        for r in idx:
            title = (r.get("title", "") or "").replace("|", "\\|").strip()
            out.append(f"| {r['number']} | {r['document']} | {title} |")
        out.append("")

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    out.append(f"*Generated {stamp} by `tools/build_figure_ledger.py` "
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
    print(f"wrote {dest.relative_to(REPO)}: "
          f"{text.count(chr(10))} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
