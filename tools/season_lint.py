#!/usr/bin/env python3
"""
season_lint.py
==============
A seasonal month-window must be DEFINED ONCE, in config.py, and imported.

Why this exists.

  Before D-100 the pipeline held nine seasonal windows as per-script locals
  across five distinct month-sets. `SUMMER_MONTHS = [6, 7, 8, 9]` appeared
  SEVEN times. Nobody ever disagreed about it, and that is precisely what made
  it dangerous: seven copies that happen to agree are not one definition, and
  the day one of them is edited the disagreement is silent. Winter was worse,
  because its four month-sets were genuinely different windows wearing the same
  name -- Oct-Mar, Nov-Mar, Nov-Feb and DJF -- and a reader meeting
  `WINTER_MONTHS` in a script had no way to know which.

  D-100 moved all of them into `config.py`, named for the QUESTION each answers
  rather than for the season. This lint is what stops them coming back. It is
  the same argument as `pipeline_lint --check literals`, applied to a kind of
  constant that lint does not see: a list of small integers is not a scientific
  literal by that lint's test, but it is exactly as load-bearing.

What it flags.

  A module-level assignment whose target name ends in `_MONTHS` and whose
  right-hand side is a literal list or tuple of integers in 1..12. That is the
  shape of a seasonal window. Anything else -- a name built from an import, a
  slice, a comprehension, a call -- is already sourced and is not flagged.

Exemptions.

  EXEMPT holds the windows that are legitimately local, each with the reason.
  An exemption is not a way to quiet the lint: it is a claim, in writing, that
  the window answers a question no shared constant answers, and it should be
  argued in the decision log before it is added here. Adding one to avoid
  moving a constant is the failure this file exists to prevent.

Usage:
    python3 tools/season_lint.py            # report, non-zero exit on a fault
    python3 tools/season_lint.py --quiet    # only faults
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-31. First issue, D-100.

import argparse
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# The one file allowed to define seasonal windows as literals: that is its job.
DEFINING_FILE = REPO / "src" / "utils" / "config.py"

# (relative path, variable name) -> why this one is legitimately local.
# Each entry is a claim that has been argued, not a silencer.
EXEMPT: dict[tuple[str, str], str] = {
    ("src/utils/pipeline_params.py", "CV_AMPLITUDE_MONTHS"):
        "the summer-AMPLITUDE window, canonical in its own module and imported "
        "by Scripts 31 and 31b. Shares months with SUMMER_MINIMUM_MONTHS by "
        "coincidence of the calendar, not because it answers the same question "
        "(D-100 note).",
    ("src/02_clustering.py", "AMP_SUMMER_MONTHS"):
        "the clustering amplitude descriptor's window. It belongs with "
        "CV_AMPLITUDE_MONTHS above, NOT with SUMMER_MINIMUM_MONTHS; whether "
        "those two are one quantity is an open question and folding it into "
        "the summer-minimum window on the strength of matching months is the "
        "error D-100 exists to prevent. Owed, not settled.",
    ("src/29_c3_within_variance_check.py", "WINTER_MONTHS"):
        "the window in which the annual winter MAXIMUM head is sought, not a "
        "climatological season. It coincides with DJF but is paired with a "
        "JJAS summer, whereas 24b's DJF is a season-mean against a symmetric "
        "JJA; and the project's own winter-maximum extraction uses Oct-Mar. "
        "Same months, different quantity (D-100, Revisit-if (d)).",
    ("src/11_forecasting_thresholds.py", "WINTER_TO_SPRING_MONTHS"):
        "an eight-month antecedent forcing window (October of year y-1 through "
        "May of year y), not a season. It spans two of the shared windows and "
        "is not expressible as any of them.",
    ("src/19_spatial_groundwater.py", "SHOULDER_MONTHS"):
        "April and October, the transitional months falling in NEITHER the "
        "Nov-Mar wet nor the May-Sep dry UKCP18 window. They exist because "
        "that gap is deliberate; they are the handling of a gap, not a season.",
    ("src/26b_van_willegen_msl_projections.py", "SHOULDER_MONTHS"):
        "as Script 19 above, and deliberately identical to it: the two scripts "
        "must project the seasonal multipliers onto the calendar the same way.",
}


def month_window(node: ast.AST) -> list[int] | None:
    """The RHS as a month list, or None if it is not a literal month window."""
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    vals = []
    for el in node.elts:
        if not (isinstance(el, ast.Constant) and isinstance(el.value, int)
                and not isinstance(el.value, bool)):
            return None
        vals.append(el.value)
    if not vals or not all(1 <= v <= 12 for v in vals):
        return None
    return vals


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    faults, exempt_seen = [], []
    for f in sorted((REPO / "src").rglob("*.py")):
        if "venv" in f.parts or f == DEFINING_FILE:
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf8"))
        except (OSError, SyntaxError):
            continue
        rel = f.relative_to(REPO).as_posix()
        for node in tree.body:            # module level only
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            tgt = node.targets[0]
            if not (isinstance(tgt, ast.Name) and tgt.id.endswith("_MONTHS")):
                continue
            months = month_window(node.value)
            if months is None:
                continue
            key = (rel, tgt.id)
            (exempt_seen if key in EXEMPT else faults).append(
                (rel, tgt.id, node.lineno, months))

    stale = sorted(set(EXEMPT) - {(r, v) for r, v, _, _ in exempt_seen})

    if not args.quiet:
        print(f"# seasonal windows — {len(exempt_seen)} exempt, "
              f"{len(faults)} local definition(s)\n")
        for rel, var, ln, months in exempt_seen:
            print(f"  exempt  {rel}:{ln}  {var} = {months}")
            print(f"          {EXEMPT[(rel, var)]}")
    if stale:
        print(f"\n## Stale exemption(s) ({len(stale)})")
        print("  Listed as exempt but no longer present. Remove the entry — a "
              "stale exemption is a claim about code that is gone.\n")
        for rel, var in stale:
            print(f"    {rel}:{var}")
    if faults:
        print(f"\n## Seasonal window defined locally ({len(faults)})")
        print("  Define it in src/utils/config.py and import it, or add an "
              "argued exemption to season_lint.EXEMPT.\n")
        for rel, var, ln, months in faults:
            print(f"    {rel}:{ln}  {var} = {months}")

    bad = bool(faults or stale)
    print(f"\nseason_lint: {'FAIL' if bad else 'OK'}"
          + ("" if bad else " — every seasonal window comes from config.py "
                            "or carries an argued exemption"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
