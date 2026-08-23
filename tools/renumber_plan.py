#!/usr/bin/env python3
"""
renumber_plan.py — compute the §4.10 relocation as a permutation, not a shift.

WHY THIS IS NOT A FIND-AND-REPLACE

  The new §4.10 "Coastal erosion and the cross-shore section" is assembled by
  RELOCATION: the coastal material now split across §4.8 and §4.9.4 moves into
  one section placed after §4.9. Figures 41, 42 and 52-56 move forward; 43-68
  close up behind them by seven; Scenario Analysis becomes §4.11.

  That is a PERMUTATION. Some numbers rise, some fall, and the domain and range
  overlap. A sequence of find-and-replace corrupts it silently: rewrite 43 -> 41
  first, and the later 41 -> 63 catches the number a second time. There is no
  ordering of the substitutions that avoids this, because the permutation has
  cycles. The only safe apply is a SINGLE SIMULTANEOUS PASS — tokenise every
  "Figure N" and "Section N.N", map each occurrence once, write once — which is
  what --emit prepares and what any applier must honour.

  234 typed figure references and up to 155 typed section references are in play
  across six documents. Hand-editing them is how a wrong cross-reference reaches
  a submitted paper.

WHAT IT TRUSTS

  `figure_map.csv` and `section_map.csv`, both generated from the ODTs' own
  sequence fields and outline levels. The figure map is self-validating: it maps
  74 figures and the highest typed reference in the corpus is exactly 74.

Usage:
    python3 tools/renumber_plan.py            # show the permutation
    python3 tools/renumber_plan.py --emit     # write tools/renumber_plan.csv
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23.

import argparse
import collections
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figure_map as fm                                     # noqa: E402

OUT = Path(__file__).resolve().parent / "renumber_plan.csv"

# ---------------------------------------------------------------------------
# The move plan, as approved 2026-08-23.
# ---------------------------------------------------------------------------
# Blocks are named by the heading that owns them in the CURRENT document. The
# new §4.10's contents are listed in the order they will appear; "NEW:" entries
# are subsections that carry a new figure and have no source block.
#
# Pye & Blott's retreat-rate figure is NOT included — the project does not own
# it (Martin, 2026-08-23). §4.10.7 therefore carries no figure.
MOVED_INTO_410 = [
    # §4.10.1 carries NO figure. Script 01 emits no figure for the cross-shore
    # coordinate, and the figure that would illustrate it already exists: the
    # trend profile (old Figure 41) plots per-well slope AGAINST that coordinate
    # and sits in the very next subsection. A separate coordinate map would
    # duplicate the axis.
    ("Network-scale partition of the summer-minimum decline.", 0),
    ("NEW:4.10.3",  1),   # the far-field asymptote is not a rate — 1 new figure
    ("Independent transect estimate of the coastal drawdown rate", 0),
    ("Coastal-Margin Processes and the Easting Gradient", 0),
]
# Where §4.10 is inserted: immediately before this heading.
INSERT_BEFORE = "Climate Scenario Projections"


def plan():
    rows = fm.build()
    r9 = [r for r in rows if r["document"] == "report9.odt"]
    moved_heads = {h for h, _ in MOVED_INTO_410 if not h.startswith("NEW:")}

    # figures that stay in report9, in document order, minus the moved blocks
    stay = [r for r in r9 if r["section_heading"] not in moved_heads]
    ins_at = next(i for i, r in enumerate(stay)
                  if r["section_heading"] == INSERT_BEFORE)

    new_seq: list[tuple] = []
    for r in rows:
        if r["document"] != "report9.odt":
            continue
        break
    # rebuild the whole corpus order
    before9 = [r for r in rows if r["document"] in ("report7.odt", "report8.odt")]
    after9 = [r for r in rows if r["document"] == "report10.odt"]

    seq: list[tuple[str, object]] = []
    seq += [("old", r) for r in before9]
    seq += [("old", r) for r in stay[:ins_at]]
    for head, n_new in MOVED_INTO_410:
        if head.startswith("NEW:"):
            for k in range(n_new):
                seq.append(("new", head))
        else:
            seq += [("old", r) for r in r9 if r["section_heading"] == head]
    seq += [("old", r) for r in stay[ins_at:]]
    seq += [("old", r) for r in after9]

    fig_map: dict[int, int] = {}
    new_figs: list[tuple[int, str]] = []
    for i, (kind, r) in enumerate(seq, start=1):
        if kind == "old":
            fig_map[r["number"]] = i
        else:
            new_figs.append((i, r))
    return rows, fig_map, new_figs, len(seq)


# Section renumbering. Only chapter 4 is affected.
#   §4.8 loses two subsections -> those after them close up
#   §4.9 loses 4.9.4          -> 4.9.5..4.9.8 close up by one
#   §4.10 Scenario Analysis   -> §4.11
SECTION_MAP = {
    # Verified against tools/section_map.csv, not against the mirror. My first
    # attempt put the two coastal subsections at 4.8.3/4.8.4; they are 4.8.2 and
    # 4.8.3. The map is generated from the ODT outline levels and is the
    # authority — reading section numbers off a mirror is guesswork, which is
    # the whole reason section_map.py exists.
    #
    # §4.8 loses 4.8.2 (trend profile) and 4.8.3 (transect); the rest close up.
    "4.8.4": "4.8.2", "4.8.5": "4.8.3", "4.8.6": "4.8.4",
    # §4.9 loses 4.9.4 (coastal-margin processes); the rest close up.
    "4.9.5": "4.9.4", "4.9.6": "4.9.5", "4.9.7": "4.9.6", "4.9.8": "4.9.7",
    "4.9.8.1": "4.9.7.1",
    # Scenario Analysis becomes §4.11.
    "4.10": "4.11", "4.10.1": "4.11.1", "4.10.2": "4.11.2",
    # The relocated blocks, by their new home in §4.10. Martin folded the
    # cluster-partition subsection into the trend profile (2026-08-23), so §4.10
    # has SIX subsections, not seven, and the transect and reach each move up one.
    "4.8.2": "4.10.2", "4.8.3": "4.10.4", "4.9.4": "4.10.5",
}


def typed_counts():
    import cite_check as cc
    figs, secs = collections.Counter(), collections.Counter()
    figd, secd = collections.defaultdict(set), collections.defaultdict(set)
    for d, t in cc.load_documents().items():
        for m in re.finditer(r"(?i)\bfigures?\s+(\d{1,3})\b", t):
            figs[int(m.group(1))] += 1; figd[int(m.group(1))].add(Path(d).name)
        for m in re.finditer(r"(?i)\bsection\s+(4\.\d+(?:\.\d+){0,2})\b", t):
            secs[m.group(1)] += 1; secd[m.group(1)].add(Path(d).name)
    return figs, figd, secs, secd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args()

    rows, fig_map, new_figs, total = plan()
    figs, figd, secs, secd = typed_counts()

    moves = {o: n for o, n in fig_map.items() if o != n}
    cycles = sum(1 for o, n in moves.items() if n in moves and moves[n] != n)
    print(f"  figures: {len(rows)} -> {total}  ({len(new_figs)} new)")
    print(f"  {len(moves)} figure number(s) change; "
          f"{sum(figs.get(o, 0) for o in moves)} typed reference(s) affected")
    print(f"  {cycles} of them map onto another moving number — "
          f"**a sequential find-and-replace would corrupt these**")
    print(f"  new figure slot(s): {[n for n, _ in new_figs]}")

    print("\n  FIGURES (old -> new, typed refs, documents)")
    for o in sorted(moves):
        d = ", ".join(sorted(figd.get(o, [])))
        print(f"      {o:>3} -> {moves[o]:<4} x{figs.get(o,0):<3} {d}")

    print("\n  SECTIONS (old -> new, typed refs, documents)")
    tot_s = 0
    for o in sorted(SECTION_MAP, key=lambda s: [int(p) for p in s.split(".")]):
        c = secs.get(o, 0); tot_s += c
        d = ", ".join(sorted(secd.get(o, [])))
        print(f"      {o:<8} -> {SECTION_MAP[o]:<8} x{c:<3} {d}")
    print(f"      total typed section references to re-point: {tot_s}")
    print(f"\n  TOTAL RE-POINTS: {sum(figs.get(o,0) for o in moves) + tot_s}")

    if args.emit:
        with OUT.open("w", newline="", encoding="utf8") as fh:
            wr = csv.writer(fh); wr.writerow(["kind", "old", "new", "typed_refs", "documents"])
            for o in sorted(moves):
                wr.writerow(["figure", o, moves[o], figs.get(o, 0),
                             ";".join(sorted(figd.get(o, [])))])
            for o in sorted(SECTION_MAP, key=lambda s: [int(p) for p in s.split(".")]):
                wr.writerow(["section", o, SECTION_MAP[o], secs.get(o, 0),
                             ";".join(sorted(secd.get(o, [])))])
        print(f"  wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
