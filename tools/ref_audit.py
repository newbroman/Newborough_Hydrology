#!/usr/bin/env python3
"""
ref_audit.py — check a figure reference against the pipeline output it names.

THE PROBLEM THIS SOLVES

  A cross-reference can be wrong in a way no resolution check can see. "report
  Figure 63" resolves — there is a Figure 63 — but if the sentence around it
  describes Script 36's output and Figure 63 is Script 32's, the reference is
  wrong and every gate in the project reports success.

  `PIPELINE_README.md` and `readme.md` are the documents where this is
  detectable without judgement, because they cite the SCRIPT or the PNG in the
  same breath as the figure number. So the number is checkable against the
  thing it claims to be:

      figure_table_sources.csv   sub-figure id  ->  source PNG
      figure_map.csv             sub-figure id  ->  global number

  Chain those and a script name yields the figure number it must be cited by.

WHAT IT DOES NOT DO

  It proposes; it does not write. A disagreement can mean the reference is
  stale, or that the sentence mentions a script incidentally, or that two
  figures come from one script and the nearest mention is the wrong one. Every
  row is printed with its evidence so the call is made by reading, not by
  trusting a proximity heuristic.

Usage:
    python3 tools/ref_audit.py                      # the two pipeline docs
    python3 tools/ref_audit.py --paths a.md b.md
    python3 tools/ref_audit.py --window 250
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-08-23. Two corrections after
#   the first run: a script named WITHOUT its extension ("#### Step 17 —
#   12_figure_site_overview") is a script mention too, and the candidate set is
#   taken from the NEAREST mention rather than everything inside the window. The
#   first run reported "Figure 1" as disagreeing because a script named 260
#   characters earlier, in the previous step's section, was in scope.
#
#   1.2.0: nearest is not enough either. In a script INDEX — "`32_x.py` (step
#   36, report Fig 56), `33_y.py` (step 37, ...)" — the nearest mention to the
#   number is the NEXT entry, not the one it belongs to. The governing script
#   always PRECEDES its own figure number, in every construction these two
#   documents use, so precedence is the rule and a following mention is used
#   only when nothing precedes.

import argparse
import csv
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repoint_refs import _text_view                                # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / "tools/figure_table_sources.csv"
FIGMAP = REPO / "tools/figure_map.csv"
DEFAULT = ["PIPELINE_README.md", "readme.md"]

REF = re.compile(r'(?i)\b(figs?\.?|figures?)\s*(\d{1,3})([ab])?(?!\d)(?!\.\d)')
# 32_differential_movement.py / 33_amplification_field.png / "Script 36"
SCRIPT_FILE = re.compile(r'\b(\d{2}[a-z]?)_([a-z0-9_]+?)(?:\.(?:py|png|jpg))?\b')
SCRIPT_NUM = re.compile(r'(?i)\bscript\s+(\d{2}[a-z]?)\b')


def truth() -> tuple[dict, dict]:
    """(png stem -> global number, script id -> {global numbers})."""
    sub_to_png = {}
    for r in csv.DictReader(SOURCES.open(encoding="utf-8")):
        sub_to_png[(r["document"], r["number"])] = r["source"]

    png_to_global, script_to_global = {}, {}
    for r in csv.DictReader(FIGMAP.open(encoding="utf-8")):
        n = int(r["number"])
        # figure_map's caption carries the sub-figure id it was rendered with
        m = re.match(r"\s*Figure\s+([\d.]+)\s*:", r["caption"])
        if not m:
            continue
        png = sub_to_png.get((r["document"], m.group(1)))
        if not png:
            continue
        png_to_global[png] = n
        sm = re.match(r"(\d{2}[a-z]?)_", png)
        if sm:
            script_to_global.setdefault(sm.group(1), set()).add(n)
    return png_to_global, script_to_global


def read(p: Path) -> str:
    if p.suffix in (".odt", ".odm"):
        return _text_view(zipfile.ZipFile(p).read("content.xml").decode("utf-8"))[0]
    return p.read_text(encoding="utf8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="*", default=DEFAULT)
    ap.add_argument("--window", type=int, default=250,
                    help="characters either side searched for a script/PNG name")
    args = ap.parse_args()

    png_to_global, script_to_global = truth()
    if not png_to_global:
        raise SystemExit("no figure source could be resolved — check figure_map "
                         "captions still carry their sub-figure id")
    print(f"  {len(png_to_global)} figure(s) resolved to a pipeline output; "
          f"{len(script_to_global)} script(s) produce one\n")

    agree = disagree = unevidenced = 0
    for rel in args.paths:
        p = REPO / rel
        if not p.exists():
            print(f"  MISSING {rel}")
            continue
        t = read(p)
        print(f"══ {rel}")
        for m in REF.finditer(t):
            cited = int(m.group(2))
            panel = m.group(3) or ""
            lo, hi = max(0, m.start() - args.window), m.end() + args.window
            ctx = t[lo:hi]
            # NEAREST mention wins. A pipeline document is a list of steps and
            # the step before this one is inside any window wide enough to be
            # useful, so "everything in the window" is not a candidate set — it
            # is the neighbours' answers mixed in with this one's.
            here = m.start() - lo
            best: tuple[tuple[int, int], set[int]] | None = None

            def offer(pos: int, vals: set[int]):
                nonlocal best
                if not vals:
                    return
                before = pos <= here
                # (0, distance) sorts every preceding mention ahead of every
                # following one, so a following mention is reached only when
                # nothing precedes.
                key = (0 if before else 1, abs(pos - here))
                if best is None or key < best[0]:
                    best = (key, set(vals))

            for fm in SCRIPT_FILE.finditer(ctx):
                png = f"{fm.group(1)}_{fm.group(2)}"
                exact = {v for k, v in png_to_global.items()
                         if k.rsplit(".", 1)[0] == png}
                offer(fm.end(), exact or script_to_global.get(fm.group(1), set()))
            for sm in SCRIPT_NUM.finditer(ctx):
                offer(sm.end(), script_to_global.get(sm.group(1), set()))

            cands = best[1] if best else set()
            if not cands:
                unevidenced += 1
                continue
            if cited in cands:
                agree += 1
                continue
            disagree += 1
            near = t[max(0, m.start() - 105):m.end() + 40].replace("\n", " ")
            print(f"\n   DISAGREES  cited {m.group(0)!r}; the surrounding text "
                  f"names output(s) that are Figure {sorted(cands)}")
            print(f"       ...{near}...")

    print(f"\n  {agree} reference(s) agree with the output they name; "
          f"{disagree} disagree; {unevidenced} name no output and are not "
          f"checkable this way")
    # GATES. A figure reference that contradicts the script named beside it is
    # wrong in the one way no resolution check can see (D-068), and this is the
    # only tool in the chain that can see it.
    print("ref_audit: " + ("OK" if not disagree else
                           f"FAIL — {disagree} reference(s) contradict the "
                           f"output they name"))
    return 1 if disagree else 0


if __name__ == "__main__":
    raise SystemExit(main())
