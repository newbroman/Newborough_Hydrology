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

__version__ = "1.4.0"  # Hollingham (2026) — 2026-08-23. Second batch: the
#   eleven figure references in PIPELINE_README.md and readme.md that name the
#   script producing the figure. Those two documents are on an older baseline
#   than the report, so the 2026-08-23 permutation moved several of them from
#   one wrong number to another; the corrections below are derived by
#   tools/ref_audit.py from figure_table_sources.csv, not judged.

import argparse
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from odt_edit import edit_spans                                   # noqa: E402
from repoint_refs import _text_view, _xml_edits, _versioned      # noqa: E402

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

    (_versioned("Newborough_Methods_Supplement"),
     r"the supplementary forest-zone analysis \(Table (16)\)",
     "19",
     "names the forest-zone table in the same clause"),

    (_versioned("Newborough_Methods_Supplement"),
     r"The outputs feed Table (16) in the main report",
     "19",
     "10c's outputs are the forest-zone table"),

    (_versioned("Newborough_Methods_Supplement"),
     r"Its outputs feed Table (17) but the",
     "19",
     "10c again, by a third different number"),

    (_versioned("Newborough_Methods_Supplement"),
     r"Table (17)\s*(?:—|---|–)\s*Forest zone spatial predictors",
     "19",
     "the caption is quoted in the clause, so the intent is not in doubt"),

    ("PIPELINE_README.md",
     r"\| Table (16) \| Forest zone spatial predictors",
     "19",
     "same table, in the pipeline output index"),

    (_versioned("academic_Summary"),
     r"20_msl5_change_2017_2023\.png; Report Figure (58)",
     "55",
     "the MSL5-change map is Figure 55; 58 is the SSM water-balance residual"),
]


# ---------------------------------------------------------------------------
# SECOND BATCH — PIPELINE_README.md and readme.md, 2026-08-23
#
# These two documents cite the SCRIPT beside the figure number, so the number is
# checkable without judgement: figure_table_sources.csv maps a sub-figure id to
# its source PNG and figure_map.csv maps it to a global number. Chained:
#
#     32_differential_movement_2011_2025.png  -> 1.60 -> Figure 56
#     36_absolute_climate_trend_2005_2025.png -> 1.61 -> Figure 57
#     33_amplification_field.png              -> 1.62 -> Figure 58
#     33_dry_spring_depth.png                 -> 1.63 -> Figure 59
#
# Both files called Script 36's map "Figure 63" — one off the number Script 32's
# map had — so the permutation sent it to 56, which IS Script 32's map. The
# error was pre-existing; the permutation made it look deliberate.
#
# Script 33 is not a renumber at all. Both files cite ONE "Fig 60" for "the
# amplification field and drought-floor surface", and cite panels "60a" and
# "60b". Those are two separate figures in the report and always were — two
# PNGs, two sub-figure ids. So the correction is a rewrite, not a number.
FIXES += [
    ("PIPELINE_README.md",
     r"secular differential water-table drift \(Script 32, step 36, report (Fig 59)\)",
     "Fig 56", "Script 32 -> 1.60 -> Figure 56"),
    ("PIPELINE_README.md",
     r"`32_differential_movement\.py` \(step 36, report (Fig 59)\)",
     "Fig 56", "same, in the script index"),
    ("PIPELINE_README.md",
     r"differential drift of the spring water table \(report (Fig 59)\)",
     "Fig 56", "same, in the step narrative"),
    ("PIPELINE_README.md",
     r"secular trend map \(Script 36, step 39, (Figure 56)\)",
     "Figure 57", "Script 36 -> 1.61 -> Figure 57"),
    ("PIPELINE_README.md",
     r"per-well secular trend map, (Figure 56)\), `37_driver_validation",
     "Figure 57", "same, in the script index"),
    ("PIPELINE_README.md",
     r"per-well secular trend map \(report (Figure 56)\)\. Unlike",
     "Figure 57", "same, in the step narrative"),
    ("PIPELINE_README.md",
     r"drought-floor surface \(Script 33, step 37, report (Fig 60)\)",
     "Figs 58 and 59", "Script 33 produces BOTH 1.62 (58) and 1.63 (59)"),
    ("PIPELINE_README.md",
     r"`33_envelope_amplification\.py` \(step 37, report (Fig 60)\)",
     "Figs 58 and 59", "same, in the script index"),
    ("PIPELINE_README.md",
     r"amplification field and drought-floor surface \(report (Fig 60)\)",
     "Figs 58 and 59", "same, in the step narrative"),
    ("PIPELINE_README.md",
     r"The amplification panel \((Fig 60a)\)",
     "Fig 58", "the amplification field is 1.62 -> 58, a figure and not a panel"),
    ("PIPELINE_README.md",
     r"The drought-floor \((Fig 60b)\)",
     "Fig 59", "the dry-spring-depth surface is 1.63 -> 59, likewise"),

    ("readme.md",
     r"Secular differential water-table drift \(32, report (Fig 59)\)",
     "Fig 56", "Script 32 -> 1.60 -> Figure 56"),
    ("readme.md",
     r"differential water-table drift \(Script 32, step 36, report (Fig 59)\)",
     "Fig 56", "same, in the phase narrative"),
    ("readme.md",
     r"drought-floor surface \(33, report (Fig 60)\)",
     "Figs 58 and 59", "Script 33 produces both 58 and 59"),
    ("readme.md",
     r"drought-floor surface \(Script 33, step 37, report (Fig 60)\)",
     "Figs 58 and 59", "same, in the phase narrative"),
    ("readme.md",
     r"per-well secular trend \(36, (Figure 56)\)",
     "Figure 57", "Script 36 -> 1.61 -> Figure 57"),
    ("readme.md",
     r"secular trend map \(Script 36, step 39, (Figure 56)\)",
     "Figure 57", "same, in the phase narrative"),
]



# ---------------------------------------------------------------------------
# THIRD BATCH — one reference that must be taken out of the way before the
# 2026-08-23 plan correction runs, 2026-08-23.
#
# renumber_plan.csv carried two wrong rows: 4.8.3 was mapped to 4.10.5 and
# 4.9.4 to 4.10.6, one subsection too far in each case, because the plan was
# computed BEFORE 4.10.4 was folded into 4.10.2 and never recomputed. Sixteen
# references were re-pointed through those rows. Fifteen of them are a clean
# shift back by one, handled by tools/renumber_plan_correction.csv.
#
# This is the sixteenth. Pre-move it read "(Section 4.8.3, Figure 45)" — but
# old Figure 45 is current Figure 43, and Figure 43 sits in §4.8.3, not in the
# transect subsection that old §4.8.3 named. So the reference was ALREADY stale
# before the move and must not be shifted with the other fifteen; its answer
# comes from the figure it cites.
FIXES += [
    ("report_edits/odt/report10.odt",
     r"across the monitoring record \(Section (4\.10\.5), Figure 43\)",
     "4.8.3",
     "cites Figure 43, which figure_map puts in §4.8.3; was stale before the move"),
]


# ---------------------------------------------------------------------------
# FOURTH BATCH — PIPELINE_README.md's four "§4.9.8" references, 2026-08-23.
#
# The other stale section numbers in PIPELINE_README/readme move as a group,
# because each number means one thing throughout
# (tools/renumber_plan_pipeline_docs.csv). §4.9.8 does not: three of its four
# uses mean the MSL5 monitoring metric — the trajectory and spatial-pattern
# figures, 1.40 and 1.41, global 41 and 42, both in §4.8.3 — while the fourth
# means the single 2017->2023 MSL5 comparison, figure 1.59, global 55, in
# §4.9.7. One number, two sections, so no permutation can carry it.
FIXES += [
    ("PIPELINE_README.md",
     r"observational MSL5 aggregation, the report's (§4\.9\.8) monitoring metric",
     "§4.8.3",
     "Script 26's metric is the MSL5 section, 4.8.3"),
    ("PIPELINE_README.md",
     r"cited in (§4\.9\.8) of the report \(cluster trajectories and spatial MSL5 map\)",
     "§4.8.3",
     "the trajectory and spatial-pattern figures, 41 and 42, are in 4.8.3"),
    ("PIPELINE_README.md",
     r"used in the (§4\.9\.8) trajectory figure and spatial map",
     "§4.8.3",
     "same two figures"),
    ("PIPELINE_README.md",
     r"the single 2017→2023 MSL5 comparison \(the (§4\.9\.8) headline",
     "§4.9.7",
     "the 2017-vs-2023 comparison is figure 55, in 4.9.7"),
]


# ---------------------------------------------------------------------------
# FIFTH BATCH — the four references the 2026-08-23 pass could not SEE, 2026-08-23.
#
# _text_view stripped tags without putting anything in their place, so the end
# of a heading ran straight into the start of the next paragraph: the corpus
# really contained "movementFigure 63 shows the secular differential movement",
# and \bfigure\b cannot match where the preceding character is a letter. Four
# references were therefore invisible to every pass, and no check could see
# them either — a reference nothing matches is a reference nothing reports.
#
# _text_view now emits a newline at each block boundary (repoint_refs 1.5.0), so
# a future pass sees them. These four are the ones the broken view missed, each
# confirmed against what the sentence describes.
FIXES += [
    ("report_edits/odt/report9.odt",
     r"movement\s*(Figure 63) shows the secular differential movement",
     "Figure 56",
     "secular differential movement is 1.60 -> Figure 56"),
    ("report_edits/odt/report9.odt",
     r"Summary of pattern\s*(Figure 60) predicts a large net loss",
     "Figure 53",
     "the net-state parametric combination is 1.57 -> Figure 53"),
    (_versioned("Newborough_Methods_Supplement"),
     r"Motivation\s*(Section 4\.10\.2) of the main report quantifies",
     "Section 4.11.2",
     "clearfell / thinning / broadleaf is Forest Management Scenarios, 4.11.2"),
    # REMOVED 2026-08-26. This entry was wrong twice over and would have
    # damaged a correct document if it had ever fired.
    #
    #   ("docs/report/Supplementary_Material_v1_18.odt",
    #    r"units\s*(Figure 63) — Differential movement",
    #    "Figure 56",
    #    "Script 32's differential movement is Figure 56"),
    #
    # 1. The target was wrong. Script 32's differential-movement map is
    #    Figure 64, not 56 — the Supplementary Material says so itself at
    #    mirror line 521, "Figure 64 --- Differential movement (Script 32)",
    #    and report10:368 agrees. Firing this would have replaced a correct
    #    number with an incorrect one.
    # 2. The anchor no longer matches anything; the passage was rewritten.
    # 3. The path was hard-coded to v1_18 while every sibling entry uses
    #    _versioned(). The Supplement is now v1_20, so the entry pointed at a
    #    stale file as well.
    #
    # The near-miss is the point: a queued fix is a claim about a document,
    # and it ages exactly as badly as the document's own numbers. Anything
    # added here should use _versioned() and should be re-checked against the
    # live text before it is trusted, not just before it is written.
]


def _applied_form(anchor: str, new: str) -> str:
    """The anchor as it reads AFTER the fix — capture group replaced by `new`.

    Only the first UNESCAPED capture group is substituted. Escapes are tracked
    rather than assumed away: every anchor here contains `\\(` for a literal
    parenthesis, and a naive scan finds that one first and splices the new
    value in behind a backslash, producing a pattern that raises rather than
    one that lies.
    """
    i, n, start = 0, len(anchor), -1
    while i < n:
        if anchor[i] == "\\":
            i += 2
            continue
        if anchor[i] == "(" and not anchor.startswith("(?", i):
            start = i
            break
        i += 1
    if start < 0:
        return r"(?!)"
    depth, i = 1, start + 1
    while i < n and depth:
        if anchor[i] == "\\":
            i += 2
            continue
        depth += (anchor[i] == "(") - (anchor[i] == ")")
        i += 1
    return anchor[:start] + re.escape(new) + anchor[i:]

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
            if not ms:
                # IDEMPOTENCE. Once a fix is applied its anchor stops matching,
                # and a tool that then aborts can never be re-run — which is
                # exactly when you want to re-run it, to prove the corpus still
                # holds. The applied form is derived from the anchor itself by
                # substituting the new value for the capture group, so this is
                # not a second hand-written pattern to keep in step.
                done = _applied_form(anchor, new)
                n_done = len(re.findall(done, text))
                if n_done == 1:
                    print(f"      already {new} — nothing to do ({why})")
                    continue
                raise SystemExit(
                    f"    anchor matches 0 times and the corrected form matches "
                    f"{n_done} time(s), needs exactly 1 of one or the other:\n"
                    f"      {anchor}")
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
