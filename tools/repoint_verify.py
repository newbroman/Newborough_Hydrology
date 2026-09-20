#!/usr/bin/env python3
"""
repoint_verify.py — did the renumber move every reference exactly once?

WHY THIS EXISTS

  On 2026-09-19 a figure renumber moved 12 references TWO places instead of one.
  The recipe ran a default repoint_refs pass and then `--abbrev-only`; since
  repoint_refs 1.6.0 the default FIG pattern already matches "Fig N", so the
  second pass moved the abbreviated form again. "report Fig 68" for Script 32
  became "Fig 70" when Figure 69 was correct.

  Every gate in check_all read green. reference_lint compares typed references
  against CAPTIONS, and every caption was right — a reference moved twice still
  points at a caption that exists, just the wrong one. section_ref_audit is
  about sections. Only ref_audit saw it, and only for the 4 of the 12 whose
  surrounding text names a script output; the other 8 were invisible.

  What found them was not a gate but a question nothing was asking: for each
  reference, is the difference between its value NOW and its value BEFORE THE
  PASS exactly what the plan said it should be? That question needs the plan and
  the pre-pass text, so it can only be asked at renumber time — which is why it
  is a tool you run after a pass, not a line in check_all.

WHAT IT CHECKS

  For every Figure/Table reference in every text file the working tree has
  changed, the pre-pass value is read from git and the post-pass value from
  disk. The plan gives the expected mapping. Three verdicts:

    MOVED WRONG   the reference changed, but not to what the plan says.
                  Double-application looks like this.
    NOT MOVED     the plan renumbers this figure and the reference did not
                  follow. An incomplete pass looks like this.
    ADDED/LOST    the file gained or lost references, so the two sequences
                  cannot be aligned position by position. Usually benign — new
                  prose written in the same session — but it is reported,
                  because an unalignable file is one this check cannot vouch
                  for, and silence there would be the same failure again.

  A reference the plan does not mention must not move at all.

  The mirrors are checked, not the ODTs: repoint_refs writes both, the mirror is
  the text the lints read, and a mirror out of step with its ODT is
  refresh_mirrors' job to catch, not this one's. Run refresh_mirrors first.

WHEN TO RUN IT

  Immediately after the repoint pass and BEFORE any hand repair, with --since
  pointing at the last commit. It compares each reference against THE PLAN, so
  a hand correction that also fixes pre-existing drift — a reference that was
  already wrong by six places before the pass — reads as MOVED WRONG. That is
  the tool being literal, not a fault: the plan said +1 and the value moved by
  five. Verify first, repair second, and the repair is then the only thing the
  next run has to explain.

Usage:
    python3 tools/repoint_verify.py --plan tools/renumber_plan.csv
    python3 tools/repoint_verify.py --plan <csv> --since HEAD~1
    python3 tools/repoint_verify.py --plan <csv> --kind table

Exit 0 if every reference moved exactly as planned, 1 otherwise.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-19. First issue, the day
#   after nothing in check_all could see a reference that had been moved twice.

import argparse
import csv
import pathlib
import re
import subprocess
import sys

# The same two forms repoint_refs rewrites: the full word and the abbreviation.
# Kept deliberately separate from repoint_refs' own patterns — a verifier that
# imports the matcher it is verifying cannot see a matcher bug.
PAT = {
    "figure": re.compile(r"(?i)\bfig(?:ure)?s?\.?\s+(\d{1,3})(?!\d)(?!\.\d)"),
    "table":  re.compile(r"(?i)\btab(?:le)?s?\.?\s+(\d{1,3})(?!\d)(?!\.\d)"),
}


def _git(*args) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout


def _refs(text: str, kind: str):
    """[(value, start_of_digits, end_of_digits)] in document order."""
    out = []
    for m in PAT[kind].finditer(text):
        out.append((int(m.group(1)), m.start(1), m.end(1)))
    return out


def _load_plan(path: pathlib.Path, kind: str) -> dict[int, int]:
    mapping = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if (row.get("kind") or kind).strip() != kind:
                continue
            mapping[int(row["old"])] = int(row["new"])
    return mapping


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="the renumber plan CSV that was applied")
    ap.add_argument("--kind", default="figure", choices=sorted(PAT))
    ap.add_argument("--since", default="HEAD",
                    help="the commit holding the PRE-pass text (default HEAD)")
    ap.add_argument("--quiet", action="store_true", help="print only faults")
    args = ap.parse_args()

    plan = _load_plan(pathlib.Path(args.plan), args.kind)
    if not plan:
        print(f"  ABORT: {args.plan} has no {args.kind} rows")
        return 1

    changed = [f for f in _git("diff", "--name-only", args.since).split()
               if f.endswith(".md")]
    if not changed:
        print(f"  no changed .md file against {args.since} — nothing to verify")
        return 0

    faults = unalignable = checked = 0
    print("=" * 78)
    print(f"REPOINT VERIFY — {args.kind} references against {args.plan}")
    print("=" * 78)
    for f in changed:
        before = _git("show", f"{args.since}:{f}")
        if not before:
            continue
        try:
            after = pathlib.Path(f).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        o, n = _refs(before, args.kind), _refs(after, args.kind)
        if len(o) != len(n):
            unalignable += 1
            print(f"\n── {f}")
            print(f"   ADDED/LOST  {len(o)} reference(s) before, {len(n)} after — "
                  f"not alignable, so not verified")
            continue
        bad = []
        for (ov, _, _), (nv, a, _) in zip(o, n):
            checked += 1
            exp = plan.get(ov, ov)
            if nv != exp:
                verdict = "NOT MOVED " if nv == ov else "MOVED WRONG"
                bad.append((verdict, ov, nv, exp,
                            after[max(0, a - 65):a + 25].replace("\n", " ")))
        if bad:
            faults += len(bad)
            print(f"\n── {f}")
            for verdict, ov, nv, exp, ctx in bad:
                print(f"   {verdict}  was {ov} -> is {nv}, plan says {exp}")
                print(f"       ...{ctx}...")
        elif not args.quiet:
            print(f"  ok    {f}  ({len(n)} reference(s))")

    print()
    tail = f"; {unalignable} file(s) not alignable" if unalignable else ""
    if faults:
        print(f"repoint_verify: FAIL — {faults} reference(s) did not move as "
              f"planned, of {checked} checked{tail}")
        return 1
    print(f"repoint_verify: OK — {checked} reference(s) moved exactly as "
          f"planned{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
