#!/usr/bin/env python3
"""
figure_placement.py — how far is each figure from the text that first cites it?

WHY

  A figure that lands pages away from the sentence introducing it makes the
  reader hold a number in their head and go looking. After the 2026-08-23
  relocations the report's figures sit in blocks at the end of their sections
  rather than beside their discussion, and the question "which are the worst"
  had no answer short of reading the whole thing.

WHAT IT MEASURES

  In the markdown mirror, the distance in words between the FIRST typed
  reference to a figure and that figure's own caption. Positive means the
  caption comes after the reference, which is normal; negative means the figure
  appears BEFORE anything mentions it, which is worse than a long gap because
  the reader meets a picture with no reason to look at it yet.

  Words, not characters, because a word count is roughly comparable across
  sections; and the mirror rather than the ODT, because the mirror is what
  `refresh_mirrors` guarantees reproduces the document.

WHAT IT IS NOT

  It is not a layout measure. The rendered page decides where a frame actually
  falls, and a caption two paragraphs downstream in the source can print on the
  same page. Read it as a triage list, worst first, not as a page count.

Usage:
    python3 tools/figure_placement.py
    python3 tools/figure_placement.py --worst 15
    python3 tools/figure_placement.py --csv outputs/figure_placement.csv
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23.

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_lint import master_order                            # noqa: E402

REPO = Path(__file__).resolve().parents[1]
MIRROR_DIR = REPO / "report_edits/text"
FIGMAP = REPO / "tools/figure_map.csv"
CAPTION_LEAD = re.compile(r"^\s*\*?\*?Figure\s", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worst", type=int, default=20)
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()

    owner = {}
    for r in csv.DictReader(FIGMAP.open(encoding="utf-8")):
        owner[int(r["number"])] = (r["document"], r["section"], r["caption"][:60])

    rows = []
    for name in master_order():
        mirror = MIRROR_DIR / (Path(name).stem + ".md")
        if not mirror.exists():
            continue
        text = mirror.read_text(encoding="utf-8")
        # word offset of every position we care about
        words = list(re.finditer(r"\S+", text))
        def word_at(pos):
            lo, hi = 0, len(words)
            while lo < hi:
                mid = (lo + hi) // 2
                if words[mid].start() < pos:
                    lo = mid + 1
                else:
                    hi = mid
            return lo

        for n, (doc, sec, cap) in owner.items():
            if doc != name:
                continue
            # the caption: a line that opens with "Figure" and carries this
            # figure's own rendered number
            # The caption is found by its OWN WORDS, not by a number. pandoc
            # renders the sequence field empty — "![**Figure : **Independent
            # test of…]" — so there is no "Figure 57" caption line in the
            # mirror to match, and a matcher looking for one measures four
            # figures out of seventy-five and calls the rest unmeasurable.
            body = re.sub(r"^\s*Figure\s+[\d.]*[a-z]?\s*:\s*", "", cap).strip()
            probe = body[:44]
            cap_pos = text.find(probe) if len(probe) > 12 else -1
            cap_pos = None if cap_pos < 0 else cap_pos
            # the first reference that is NOT the caption line
            ref_pos = None
            for m in re.finditer(rf"(?<![\d.])\bFigures?\s+{n}\b", text, re.I):
                line_start = text.rfind("\n", 0, m.start()) + 1
                if CAPTION_LEAD.match(text[line_start:line_start + 40]):
                    continue
                ref_pos = m.start()
                break
            if cap_pos is None or ref_pos is None:
                rows.append((n, sec, None, cap, name))
                continue
            rows.append((n, sec, word_at(cap_pos) - word_at(ref_pos), cap, name))

    known = [r for r in rows if r[2] is not None]
    unknown = [r for r in rows if r[2] is None]
    before = [r for r in known if r[2] < 0]
    known.sort(key=lambda r: (-abs(r[2])))

    print(f"  {len(known)} figure(s) measured, {len(unknown)} not measurable\n")
    print(f"  {len(before)} figure(s) appear BEFORE any reference to them "
          f"(negative gap)\n")
    print(f"  {'fig':>4}  {'§':<9} {'gap (words)':>11}  caption")
    for n, sec, gap, cap, _doc in known[:args.worst]:
        flag = "  BEFORE its first mention" if gap < 0 else ""
        print(f"  {n:>4}  {sec:<9} {gap:>11}  {cap[:52]}{flag}")
    if unknown:
        print(f"\n  not measurable (no caption line, or cited nowhere):")
        for n, sec, _g, cap, _d in unknown:
            print(f"  {n:>4}  {sec:<9}              {cap[:52]}")

    if args.csv:
        out = REPO / args.csv
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["figure", "section", "gap_words", "document", "caption"])
            for n, sec, gap, cap, doc in sorted(rows, key=lambda r: r[0]):
                w.writerow([n, sec, "" if gap is None else gap, doc, cap])
        print(f"\n  written {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
