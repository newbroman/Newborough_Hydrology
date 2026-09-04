#!/usr/bin/env python3
"""
build_doc_ledger.py — the document ledger, derived rather than written.

WHY DERIVED

  notes/ledgers/README.md listed DOC_LEDGER.md as a proposed ledger tracking the
  "ODT bumped, PDF lags" state that "currently lives only in people's heads".
  tools/export_lag.py already answers the live-lag question directly, so a
  hand-maintained doc ledger would be a stale second copy of it. This ledger is
  the published-PDF <- source-ODT <- built map (from docs/PDF_MANIFEST.txt), with
  each row's live lag state filled in by calling export_lag.py at generation time.

WHAT IT ANSWERS

  For each published PDF: the source ODT it was built from, when it was built,
  and whether it is current or lagging its live source right now. The
  "document -> current version -> companion PDF status -> pending regeneration"
  lookup.

  export_lag.py version-checks only PDFs with a VERSIONED ODT source (the
  "_vN_M" families build_pdfs.sh tracks). PDFs whose source carries no version —
  the public summaries and the web-tools notes — cannot be version-checked, and
  git does not preserve the mtimes export_lag would otherwise fall back on, so
  they are shown as "unversioned" rather than given a false current/stale verdict.

  Seeded from docs/PDF_MANIFEST.txt and tools/export_lag.py. Pure stdlib.
  The lag column is a snapshot at generation time; export_lag.py is the live
  authority (and report.pdf is deliberately outside the manifest — see the
  project working rules).

  Regenerate with: python3 tools/build_doc_ledger.py
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import datetime

__version__ = "1.0.0"

REPO = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = REPO / "docs" / "PDF_MANIFEST.txt"
EXPORT_LAG = REPO / "tools" / "export_lag.py"
DEFAULT_OUT = REPO / "notes" / "ledgers" / "DOC_LEDGER.md"

BANNER = (
    "<!-- GENERATED LEDGER — do not edit.\n"
    "     Regenerate with: python3 tools/build_doc_ledger.py -->\n\n"
)

LAGGING = {"STALE", "STALE?", "MISSING", "UNBUILT"}

# leading verdict keyword -> line naming a .pdf, in export_lag's output
_VERDICT = re.compile(r"^\s*(current|STALE\?|STALE|MISSING|UNBUILT)\s+(\S+\.pdf)")


def _manifest_rows() -> list[tuple[str, str, str]]:
    rows = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "<-" not in line:
            continue
        pdf, rest = line.split("<-", 1)
        odt, built = (rest.split("|", 1) + [""])[:2]
        rows.append((pdf.strip(), odt.strip(), built.strip()))
    return rows


def _live_states() -> tuple[dict[str, str], list[str]]:
    """Map pdf -> verdict word, plus the NO-SOURCE pdf list, from export_lag."""
    try:
        out = subprocess.run([sys.executable, str(EXPORT_LAG)],
                             capture_output=True, text=True, timeout=90).stdout
    except Exception as e:  # noqa: BLE001 — the ledger still builds without lag
        return {}, [f"(export_lag unavailable: {e})"]
    states, no_source, in_ns = {}, [], False
    for line in out.splitlines():
        m = _VERDICT.match(line)
        if m:
            states[m.group(2)] = m.group(1)
            continue
        if "NO SOURCE" in line:
            in_ns = True
            continue
        if in_ns:
            s = line.strip()
            if s.endswith(".pdf"):
                no_source.append(s)
            elif s and not s.startswith("docs/"):
                in_ns = False
    return states, no_source


def _classify(pdf: str, odt: str, states: dict[str, str]) -> str:
    st = states.get(pdf)
    if st is not None:
        return st
    # export_lag version-checks only versioned-source PDFs; an unversioned source
    # has no version signal and git does not preserve mtimes, so it is neither
    # "current" nor "stale" but simply not version-tracked.
    return "unversioned" if "_v" not in odt else "unknown"


def build() -> str:
    rows = _manifest_rows()
    states, no_source = _live_states()
    classified = [(pdf, odt, built, _classify(pdf, odt, states))
                  for pdf, odt, built in sorted(rows)]
    n_cur = sum(1 for *_, st in classified if st == "current")
    n_lag = sum(1 for *_, st in classified if st in LAGGING)
    n_unv = sum(1 for *_, st in classified if st == "unversioned")

    out = [BANNER.rstrip("\n"), "",
           "# DOC_LEDGER — published PDFs, their source ODTs, and lag state",
           "",
           "*Generated from `docs/PDF_MANIFEST.txt` with the live lag state from "
           "`tools/export_lag.py`. Living current-state; regenerate, do not "
           "hand-edit. `tools/export_lag.py` is the live authority.*",
           "",
           f"**{len(rows)} published PDFs** — {n_cur} version-current, "
           f"{n_lag} lagging, {n_unv} unversioned (mtime-only, not "
           f"version-tracked).",
           "",
           "| Published PDF | Source ODT (recorded) | Built (UTC) | State |",
           "|---|---|---|---|"]
    for pdf, odt, built, st in classified:
        mark = st if st in ("current", "unversioned") else f"**{st}**"
        out.append(f"| `{pdf}` | `{odt}` | {built} | {mark} |")
    out.append("")

    if no_source:
        out.append("## Authored directly (no source ODT)")
        out.append("")
        out.append("*Published PDFs with no ODT to rebuild from — export_lag "
                   "declares these authored directly.*")
        out.append("")
        for q in no_source:
            out.append(f"- `{q}`")
        out.append("")

    out.append("> `report.pdf` is deliberately **absent** from `PDF_MANIFEST.txt` "
               "and from this ledger: it is built from the `report.odm` master via "
               "`tools/export_master_pdf.py`, not `build_pdfs.sh`. See the project "
               "working rules.")
    out.append("")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    out.append(f"*Generated {stamp} by `tools/build_doc_ledger.py` "
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
