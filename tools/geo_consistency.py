#!/usr/bin/env python3
"""
geo_consistency.py — withdrawn geo values must not reappear in the PUBLISHED corpus.

WHY

  GEO_PROVENANCE.md gates coverage — every geo layer must be accounted for — but
  nothing checked that a value the geo work WITHDREW had actually left the
  published documents. On 2026-09-04 the "Settled position" box in
  GEO_PROVENANCE.md itself still declared the withdrawn 2006/2012/2020 coastline
  series and the contaminated 1.71 m repeatability figure a full screen above the
  section that superseded them (W90.3/.4). A withdrawn value that lingers in a
  published document is worse than a coverage gap: it reads as current.

  So this is the other half of the geo net. geo_provenance.py answers "is every
  layer accounted for?"; this answers "has every withdrawn value actually left
  the published corpus?".

WHAT IT DOES

  Reads tools/geo_withdrawn.csv (pattern, kind, reason, superseded_by) and scans
  the PUBLISHED corpus — the report, papers, supplements and summaries that
  cite_check already loads. A match is a FINDING unless its line also carries a
  withdrawal marker (superseded / withdrawn / retired / historical / former / no
  longer / replaced), which is how a document may legitimately name a withdrawn
  value in order to say it is gone.

  The internal working records (working/**: changelogs, the decision log, the
  register) are deliberately NOT scanned: a withdrawn value in a dated changelog
  is history, and rewriting history is the one thing this project does not do.

  Advisory by default (exit 0), like export_lag — a published-PDF export is slow
  and manual and a gate that fires between every edit gets switched off.
  --gate makes it fail (exit 1) for use before a release.

Usage:
    python3 tools/geo_consistency.py            # advisory scan
    python3 tools/geo_consistency.py --gate     # non-zero exit on any finding
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import pathlib
from pathlib import Path

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-04 (W73).

REPO = Path(__file__).resolve().parents[1]
REGISTER = Path(__file__).resolve().parent / "geo_withdrawn.csv"

# A line may name a withdrawn value in order to say it is withdrawn. These words
# on the same line mark that intent and exempt the match.
_MARKERS = re.compile(
    r"(?i)supersede|withdraw|retire|historical|former|no longer|replaced|"
    r"deleted|removed on evidence|contaminated|not a measurement|superseded")


def _matcher(pattern: str, kind: str) -> re.Pattern:
    return re.compile(pattern if kind == "regex" else re.escape(pattern))


def scan() -> list[tuple[str, str, int, str, str]]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import cite_check as cc  # its DOC_GLOBS ARE the published corpus
    # Internal history is out of scope: a withdrawn value in the decision log, a
    # ledger or any working/ record is a dated fact, not a live claim. Only the
    # published corpus is scanned.
    skip = set(cc.HISTORY_DOCS)
    rules = []
    for row in csv.DictReader(REGISTER.open(encoding="utf-8")):
        rules.append((_matcher(row["pattern"], row.get("kind", "literal")),
                      row["pattern"], row["reason"]))
    findings = []
    for doc, text in cc.load_documents().items():
        if pathlib.Path(doc).name in skip or "working/" in doc.replace("\\", "/"):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if _MARKERS.search(line):
                continue
            for rx, pat, reason in rules:
                if rx.search(line):
                    findings.append((Path(doc).name, doc, n, pat, reason))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true",
                    help="exit non-zero on any finding (default: advisory)")
    a = ap.parse_args()

    n_rules = sum(1 for _ in csv.DictReader(REGISTER.open(encoding="utf-8")))
    findings = scan()

    if not findings:
        print(f"  geo_consistency: OK — {n_rules} withdrawn value(s) checked, "
              f"none reappears in the published corpus")
        return 0

    print(f"  geo_consistency: {len(findings)} live occurrence(s) of a withdrawn "
          f"value in the published corpus")
    for name, doc, n, pat, reason in findings:
        print(f"      {name}:{n}  matches `{pat}` — {reason}")
    print("  Each is a value the geo work withdrew, appearing on a line that does "
          "not mark it as withdrawn. Correct the document, or mark the line if it "
          "is deliberately naming the withdrawn value as gone.")
    return 1 if a.gate else 0


if __name__ == "__main__":
    raise SystemExit(main())
