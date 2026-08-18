#!/usr/bin/env python3
"""
rounding_lint — stop new store-time rounding creeping back in (D-035).

D-035 settled that stores carry what the pipeline computed and rounding happens
where a number is displayed. Three decimals is a display rule for quantities of
order one; applied at storage it costs a significant figure on the small ones
(C4's beta_3 is 0.0183, which is 0.018 at 3 dp) and the loss compounds through
every statistic taken afterwards.

The sweep that implemented D-035 cleared the highest-leverage files -
report_numbers_utils (which rounded EVERY value entering *_report_numbers.csv),
pipeline_params, and Scripts 17, 18, 09a, 10a, 10h. It did not clear the rest,
and clearing them all at once would move several hundred published numbers in
one step. So this lint holds the line rather than drawing it: it counts the
store-time rounding in each file and fails when a count goes UP.

What counts as store-time rounding: round(x, n) or .round(n) appearing as
  * a value in a dict literal
  * a keyword argument to dict()
  * the right-hand side of an assignment into a subscript (a DataFrame column)
in a module that also writes CSV or builds ReportNumbers. Display rounding -
inside an f-string, a print, a plot label, a printed groupby - is not matched
and is correct where it is.

Usage:
    python3 tools/rounding_lint.py             # check against the baseline
    python3 tools/rounding_lint.py --baseline  # rewrite the baseline (after a
                                               # deliberate sweep, never to
                                               # silence a new hit)
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASELINE = Path(__file__).with_name("rounding_lint_baseline.json")
SCAN_GLOBS = ("src/*.py", "src/utils/*.py")


def _is_round(node) -> bool:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id == "round" and len(node.args) == 2
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr == "round" and len(node.args) >= 1
    return False


def stored_rounds(path: Path) -> list[int]:
    """Line numbers of store-time rounding in one file."""
    src = io.open(path, encoding="utf-8").read()
    if "to_csv" not in src and "ReportNumbers" not in src:
        return []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    hits: list[int] = []
    for node in ast.walk(tree):
        candidates = []
        if isinstance(node, ast.Dict):
            candidates = list(node.values)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == "dict"):
            candidates = [kw.value for kw in node.keywords]
        elif (isinstance(node, ast.Assign)
              and any(isinstance(t, ast.Subscript) for t in node.targets)):
            candidates = [node.value]
        for value in candidates:
            branches = ([value] if not isinstance(value, ast.IfExp)
                        else [value.body, value.orelse])
            for branch in branches:
                if _is_round(branch):
                    hits.append(branch.lineno)
    return sorted(set(hits))


def scan() -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for pattern in SCAN_GLOBS:
        for path in sorted(REPO.glob(pattern)):
            hits = stored_rounds(path)
            if hits:
                out[str(path.relative_to(REPO))] = hits
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", action="store_true",
                    help="rewrite the baseline from the current tree")
    args = ap.parse_args()

    current = scan()
    total = sum(len(v) for v in current.values())

    if args.baseline:
        BASELINE.write_text(
            json.dumps({k: len(v) for k, v in sorted(current.items())}, indent=1) + "\n",
            encoding="utf-8")
        print(f"  baseline written: {len(current)} file(s), {total} site(s)")
        return 0

    if not BASELINE.exists():
        print("  no baseline — run with --baseline once, deliberately")
        return 1

    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    worse, better = [], []
    for name, hits in sorted(current.items()):
        was = base.get(name, 0)
        if len(hits) > was:
            worse.append((name, was, len(hits), hits))
        elif len(hits) < was:
            better.append((name, was, len(hits)))
    for name, was in sorted(base.items()):
        if name not in current and was:
            better.append((name, was, 0))

    for name, was, now in better:
        print(f"  cleared  {name}: {was} -> {now}")
    for name, was, now, hits in worse:
        print(f"  NEW      {name}: {was} -> {now}  (lines {hits})")

    if worse:
        print("\nrounding_lint: FAIL — new store-time rounding (D-035).")
        print("  Store what the pipeline computed; round where the number is shown.")
        print("  If the new site is genuinely a display value, it is in the wrong place;")
        print("  move the rounding to the point of rendering rather than rebaselining.")
        return 1

    print(f"\n  {total} known store-time rounding site(s) in {len(current)} file(s); "
          "none new")
    if better:
        print("  (some files improved — rerun with --baseline to lock the gain in)")
    print("rounding_lint: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
