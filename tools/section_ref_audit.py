#!/usr/bin/env python3
"""
section_ref_audit.py — check a "§4.9.6" reference against evidence, not a permutation.

THE PROBLEM

  `repoint_refs.py` matches the literal words "Figure", "Section" and "Table".
  It has never seen a § reference, so all 97 of them in this corpus are in
  pre-move numbering. But pre-move is not the same as CORRECT: report8 and
  PIPELINE_README place the MSL5 report figures in §4.8.4 while the Methods
  Supplement places the same figures in §4.8.5, and both cannot be right.
  Applying the permutation blind would preserve whichever error is there.

THE EVIDENCE

  Two independent sources, in order of strength:

  1. A FIGURE OR TABLE CITED IN THE SAME BREATH. "main report §4.9.6, Figure
     50" — every figure reference in the corpus has been re-pointed and
     verified, and `figure_map.csv` records which section owns each figure. So
     the figure names the section, and the § number is checkable against it.

  2. THE SECTION HEADING'S OWN WORDS. Where no figure is cited, the sentence is
     scored against every heading in `section_map.csv` on shared content words.
     This is weaker and is reported as a suggestion with its score, never as a
     verdict.

  Nothing is written. Each row prints its evidence so the call is made by
  reading.

Usage:
    python3 tools/section_ref_audit.py
    python3 tools/section_ref_audit.py --window 140
"""
from __future__ import annotations

__version__ = "1.3.0"  # Hollingham (2026) — 2026-08-23. The first run reported
#   35 disagreements and most were the heuristic's fault, not the corpus's:
#     - "§4.2 ... Figure 11" is not a conflict. §4.2 is the ANCESTOR of §4.2.3,
#       and a reference to a whole section is a normal thing to write.
#     - "§3.4.5 / §5.4.2 (Figure 68)" pairs a METHODS section with a RESULTS
#       figure on purpose. Comparing across chapters compares two different
#       things.
#     - A figure named in the NEXT sentence is not evidence about this one.
#   So: ancestors agree, only same-chapter pairs are compared, and the figure
#   must be inside the same sentence.

import argparse
import csv
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repoint_refs import _text_view, ODTS, TEXTS                   # noqa: E402

REPO = Path(__file__).resolve().parents[1]
FIGMAP = REPO / "tools/figure_map.csv"
SECMAP = REPO / "tools/section_map.csv"

SYM = re.compile(r"§\s?(\d+\.\d+(?:\.\d+){0,2})(?!\d)")
NEAR_FIG = re.compile(r"(?i)\b(figures?|tables?)\s+(\d{1,3})(?!\d)(?!\.\d)")

STOP = set("""the a an and or of to in on for by with from at as is are was were
be been that this these those it its their which what when where how why not
report main see also section figure table using used use than then there here
per within across between over under about into onto out up down all any each
both same other another new old more most less least very much many few one two
three both step steps script scripts""".split())


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z0-9-]{3,}", s.lower())} - STOP



# Which reference FORMS exist, and which tools can read them. The 2026-08-23
# renumber shipped with 15 references stranded and 109 in forms nothing read,
# and every gate reported success throughout (D-068). A count is the minimum
# honest thing a reference check can say about the corpus it did not read.
FORMS = [
    ("Section 4.9.6", r"(?i)\bsections?\s+\d+\.\d+(?:\.\d+){0,2}", "repoint_refs, section_map"),
    ("§4.9.6",        r"§\s?\d+\.\d+(?:\.\d+){0,2}",                 "repoint_refs --symbol-only"),
    ("Sect./Sec. 4.9.6", r"(?i)\bsec(?:t)?\.\s*\d+\.\d+",            "NOTHING"),
    ("Figure 62",     r"(?i)\bfigures?\s+\d{1,3}(?!\d)(?!\.\d)",      "repoint_refs, figure_map"),
    ("Fig 62",        r"(?i)\bfigs?\.?\s*\d{1,3}(?!\d)(?!\.\d)",     "ref_audit only"),
    ("Table 20",      r"(?i)\btables?\s+\d{1,3}(?!\d)(?!\.\d)",       "repoint_refs, reference_lint"),
    ("Tab. 20",       r"(?i)\btab\.\s*\d{1,3}(?!\d)(?!\.\d)",        "NOTHING"),
]


def form_census() -> None:
    text = {}
    for name, rel in list(ODTS.items()) + [(t, t) for t in TEXTS]:
        p = REPO / rel
        text[name] = (
            _text_view(zipfile.ZipFile(p).read("content.xml").decode("utf-8"))[0]
            if p.suffix in (".odt", ".odm") else p.read_text(encoding="utf8"))
    joined = "\n".join(text.values())
    print("\n  reference forms present in the corpus, and what reads each:")
    for label, pat, reader in FORMS:
        n = len(re.findall(pat, joined))
        flag = "   <-- UNREAD" if reader == "NOTHING" and n else ""
        print(f"      {label:<18} {n:>5}   read by: {reader}{flag}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=90,
                    help="characters either side searched for a figure/table cite")
    args = ap.parse_args()

    fig_section = {}
    for r in csv.DictReader(FIGMAP.open(encoding="utf-8")):
        fig_section[("figure", int(r["number"]))] = (r["section"], r["caption"])

    headings = []
    for r in csv.DictReader(SECMAP.open(encoding="utf-8")):
        headings.append((r["number"], r["heading"]))
    head_words = {n: words(h) for n, h in headings}
    head_text = dict(headings)

    ok = wrong = weak = 0
    rows = []
    for name, rel in list(ODTS.items()) + [(t, t) for t in TEXTS]:
        p = REPO / rel
        t = (_text_view(zipfile.ZipFile(p).read("content.xml").decode("utf-8"))[0]
             if p.suffix in (".odt", ".odm") else p.read_text(encoding="utf8"))
        for m in SYM.finditer(t):
            cited = m.group(1)
            lo, hi = max(0, m.start() - args.window), m.end() + args.window
            ctx = t[lo:hi]
            here = m.start() - lo

            # 1. a figure cited alongside
            best = None
            for fm in NEAR_FIG.finditer(ctx):
                if fm.group(1).lower().startswith("table"):
                    continue
                # "script figures 21-03" is a PIPELINE output and its number is
                # a script id. repoint_refs excludes them; so must this.
                if re.search(r"(?i)\bscript\s*$", ctx[:fm.start()]):
                    continue
                key = ("figure", int(fm.group(2)))
                if key not in fig_section:
                    continue
                a, b = sorted((here, fm.start()))
                # ODF text has no space after a full stop where the next
                # paragraph begins, so "…Figure 48.§4.10.2 Forest Management…"
                # is two sentences with nothing between them. Treat a stop
                # followed by whitespace, § or a capital as a boundary.
                if re.search(r"[.;](\s|§|[A-Z])", ctx[a:b + 1]):
                    continue
                # "the figure 14b_year_crossing.csv" is a FILENAME, not a cite.
                if re.match(r"[a-z_0-9]", ctx[fm.end():fm.end() + 1]):
                    continue
                if fig_section[key][0].split(".")[0] != cited.split(".")[0]:
                    continue                       # methods section vs results figure
                d = abs(fm.start() - here)
                if best is None or d < best[0]:
                    best = (d, fm.group(0), *fig_section[key])
            if best:
                _, cite, sec, cap = best
                # An ancestor is not a contradiction: §4.2 legitimately names
                # the section that contains §4.2.3.
                agrees = sec == cited or sec.startswith(cited + ".") \
                    or cited.startswith(sec + ".")
                verdict = "AGREES" if agrees else "DISAGREES"
                ok += verdict == "AGREES"
                wrong += verdict == "DISAGREES"
                rows.append((name, verdict, cited, sec, f"{cite} lives in §{sec}",
                             cap[:64], t[max(0, m.start() - 78):m.end() + 40]))
                continue

            # 2. heading words
            w = words(t[max(0, m.start() - 160):m.end() + 160])
            scored = sorted(((len(w & hw), n) for n, hw in head_words.items()
                             if hw), reverse=True)
            top = [(s, n) for s, n in scored[:3] if s >= 2]
            weak += 1
            rows.append((name, "no figure cited", cited,
                         top[0][1] if top else "?",
                         "; ".join(f"§{n} “{head_text[n][:30]}” ({s} words)"
                                   for s, n in top) or "no heading scored",
                         "", t[max(0, m.start() - 78):m.end() + 40]))

    for verdict in ("DISAGREES", "AGREES", "no figure cited"):
        sel = [r for r in rows if r[1] == verdict]
        if not sel:
            continue
        print(f"\n{'═' * 74}\n{verdict}  ({len(sel)})\n{'═' * 74}")
        for name, _v, cited, sug, why, cap, near in sel:
            print(f"\n  {name}   §{cited}"
                  + (f"  ->  §{sug}" if verdict == "DISAGREES" else ""))
            print(f"      evidence: {why}")
            if cap:
                print(f"      caption:  {cap}")
            print(f"      ...{near.strip()}...")

    print(f"\n  {ok} agree with a figure cited alongside; {wrong} disagree; "
          f"{weak} cite no figure and are scored on heading words only")
    form_census()
    print("section_ref_audit: " + ("OK" if not wrong else
                                   f"FAIL — {wrong} § reference(s) contradict "
                                   f"the figure cited alongside"))
    return 1 if wrong else 0


if __name__ == "__main__":
    raise SystemExit(main())
