#!/usr/bin/env python3
"""
fix_stale_refs.py — correct cross-references that were WRONG BEFORE the move.

WHY THESE CANNOT GO THROUGH repoint_refs.py

  repoint_refs applies a permutation: it assumes a reference reads the number
  the thing HAD, and rewrites it to the number the thing HAS. That assumption
  fails for a reference that was already pointing at the wrong table before
  anything moved. Feeding it to the permutation turns a wrong number into a
  differently wrong number, and the result then looks deliberate.

  Nine such references were found on 2026-08-23 while extending the re-pointer
  to tables. Eight of them cite the forest-zone spatial-predictor table — the
  one report9 itself calls Table 20 — by the numbers 16, 17 or 18. One cites
  the MSL5-change map as report Figure 58 when that map is Figure 55. They are
  corrected here BY MEANING, one at a time, each against a text anchor unique
  in its document, and each with the reason recorded beside it.

  The tenth finding is NOT here. report10 contains the phrase "the water
  Table 16 never rises", present since the first commit of the mirrors. That is
  not a reference to anything and is not a number to re-point; it is a defect
  in the sentence, and changing an author's prose is not a lint's job.

Usage:
    python3 tools/fix_stale_refs.py --dry-run
    python3 tools/fix_stale_refs.py --apply
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23.

import argparse
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from odt_edit import edit_spans                                   # noqa: E402
from repoint_refs import _text_view, _xml_edits                   # noqa: E402

REPO = Path(__file__).resolve().parents[1]

# (document, anchor — must be unique in the document, group 1 = the digits,
#  new value, why)
FIXES = [
    ("report_edits/odt/report8.odt",
     r"Results are reported in Section 4\.9\.4 \(Table (18)\)",
     "19",
     "cites the forest-zone spatial-predictor table, which report9 numbers 20"),

    ("report_edits/odt/report10.odt",
     r"spans nearly the full site-wide range \(Section 4\.9\.4; Table (18)\)",
     "19",
     "same table; same pre-existing error"),

    ("docs/report/Newborough_Methods_Supplement_v1_9_45.odt",
     r"the supplementary forest-zone analysis \(Table (16)\)",
     "19",
     "names the forest-zone table in the same clause"),

    ("docs/report/Newborough_Methods_Supplement_v1_9_45.odt",
     r"The outputs feed Table (16) in the main report",
     "19",
     "10c's outputs are the forest-zone table"),

    ("docs/report/Newborough_Methods_Supplement_v1_9_45.odt",
     r"Its outputs feed Table (17) but the",
     "19",
     "10c again, by a third different number"),

    ("docs/report/Newborough_Methods_Supplement_v1_9_45.odt",
     r"Table (17)\s*(?:—|---|–)\s*Forest zone spatial predictors",
     "19",
     "the caption is quoted in the clause, so the intent is not in doubt"),

    ("PIPELINE_README.md",
     r"\| Table (16) \| Forest zone spatial predictors",
     "19",
     "same table, in the pipeline output index"),

    ("docs/academic_summaries/academic_Summary_v1_9.odt",
     r"20_msl5_change_2017_2023\.png; Report Figure (58)",
     "55",
     "the MSL5-change map is Figure 55; 58 is the SSM water-balance residual"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.apply or args.dry_run):
        ap.error("choose --dry-run or --apply")

    by_doc: dict[str, list] = {}
    for rel, anchor, new, why in FIXES:
        by_doc.setdefault(rel, []).append((anchor, new, why))

    total = 0
    for rel, jobs in by_doc.items():
        p = REPO / rel
        is_odt = p.suffix in (".odt", ".odm")
        raw = (zipfile.ZipFile(p).read("content.xml").decode("utf-8") if is_odt
               else p.read_text(encoding="utf8"))
        text, idx = _text_view(raw) if is_odt else (raw, list(range(len(raw))))

        payload = []
        print(f"\n  {rel}")
        for anchor, new, why in jobs:
            ms = list(re.finditer(anchor, text))
            if len(ms) != 1:
                raise SystemExit(
                    f"    anchor matched {len(ms)} time(s), needs exactly 1: {anchor}")
            m = ms[0]
            old = m.group(1)
            if old == new:
                print(f"      already {new} — nothing to do ({why})")
                continue
            print(f"      {old} -> {new}   {why}")
            print(f"        ...{text[max(0, m.start() - 55):m.end() + 12]}...")
            payload += _xml_edits(idx, m.start(1), m.end(1), new)
            total += 1

        if not payload or not args.apply:
            continue
        payload.sort(key=lambda t: t[0])
        if is_odt:
            if not edit_spans(p, p, payload, expect=len(payload)):
                raise SystemExit(f"    FAILED writing {rel}")
            print(f"      wrote {rel}")
        else:
            out = raw
            for a, b, val in reversed(payload):
                out = out[:a] + val + out[b:]
            p.write_text(out, encoding="utf8")
            print(f"      wrote {rel}")

    print(f"\n  {total} stale reference(s) corrected"
          + ("" if args.apply else " — dry run, nothing written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
