#!/usr/bin/env python3
"""
artefact_lint — is a committed output a truthful record of what the pipeline computed?

The other gates check documents against outputs, scripts against config.py,
mirrors against ODTs and claims against CSVs. NOTHING CHECKED AN OUTPUT AGAINST
ITSELF, and two failures on 2026-09-01 both sat in that gap, both survived a
full check_all, and both were found by a person reading a file.

  W124  40_01_epoch_series.csv carried median_m 69.021, years 116.0 and
        rate_m_yr 0.645058. The rate was computed over 107 and was right; the
        years literal was a leftover from the pre-D-087 basis. Recomputing the
        rate from the row's own two columns gave 0.595 - 7.7% out. It sat in a
        committed output for three days.

  W128  _dtm_profile() caught an ImportError, warned, returned an empty frame,
        and main() wrote it over the good committed file, announcing
        "Saved: 40_05_dtm_profile.csv (0 rows)". Five rows became a bare header.

ONE IDEA JOINS THEM: an artefact that LOOKS like a measurement and is not one.
In the first the row contradicts its own arithmetic; in the second the file
contradicts the run that wrote it. Hence one tool, two checks.

CHECK A - ROW ARITHMETIC. Where a committed CSV carries a quantity and the
columns that define it, the columns must reproduce the quantity. Relationships
are DECLARED in tools/row_arithmetic.csv, never discovered by a name heuristic:
the project already has one heuristic gate and twenty-two rows of adjudication
to show for it, and a second would earn a second adjudication table.

  THE TOLERANCE IS DERIVED, NOT PICKED. A fixed epsilon is wrong in both
  directions - too tight and stored rounding fires it, too loose and it stops
  being a check. So it comes from the stored precision of the components: read
  each component's decimal places AS STORED IN THE FILE TEXT, re-evaluate the
  expression with each moved by half a unit in its last place, and require the
  stored result to lie in the widest interval that produces. No symbolic
  differentiation, works for any admitted expression, 2n extra evaluations.

  Measured on the motivating row: `years` is stored to one decimal place, giving
  a relative envelope of 4.7e-4 against the bug's 7.7e-2 error - a margin of 160
  times - and the corrected row reproduces exactly.

CHECK B - AN ARTEFACT NO SCRIPT COMPUTED. No committed CSV under outputs/ may be
header-only or blank unless declared in tools/empty_outputs_allowed.csv. This
checks the CONSEQUENCE rather than hunting the defective code shape by dataflow
analysis, which is brittle and evadable by a refactor. Measured 2026-09-01: 0 of
270 committed CSVs are header-only, so the allowlist starts empty and the gate
goes red the first time this recurs - at the moment the file is written.

Both checks read only committed CSVs and source text. No pipeline run, no ODT,
no network, so this gate works in a bare clone and over the desktop bridge.

Usage:
    python3 tools/artefact_lint.py             # both checks
    python3 tools/artefact_lint.py --arithmetic
    python3 tools/artefact_lint.py --empty
    python3 tools/artefact_lint.py --quiet     # verdict lines only
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-01. First issue, from
#   NRG_spec_artefact_lint_2026-09-01.md, built to the derived-tolerance option.
#   The envelope carries TWO terms, not one. The spec described only the
#   components; writing its own verification test 2 showed that a result
#   legitimately stored to two decimals sits up to 0.005 from any recomputation
#   and would fail a components-only envelope. Half a unit in the RESULT's last
#   stored place is added. The bug the gate exists for is unaffected: its stored
#   rate carries 16 decimals, so that term is ~5e-17 against an 8.4e-2 gap.

import argparse
import ast
import csv
import io
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
RULES = ROOT / "tools" / "row_arithmetic.csv"
ALLOWED_EMPTY = ROOT / "tools" / "empty_outputs_allowed.csv"
SRC = ROOT / "src"

GREEN, YELLOW, RED, DIM, RESET = (
    "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[0m")

# Columns whose NAME suggests a defined quantity. Used ONLY to list undeclared
# candidates as an advisory - never to invent a rule. A gate that guesses the
# relationship would be the second heuristic this project does not want.
CANDIDATE_RE = re.compile(r"(rate|_pct|percent|fraction|_per_|share)", re.I)

# An expression may contain column names, numeric literals, + - * / and
# parentheses. Nothing else: no attribute access, no calls, no dunder.
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+\.?\d*|[-+*/()\s.]")


def _validate(expr: str, columns) -> str | None:
    """Return None if the expression is admissible, else why it is not."""
    if not expr.strip():
        return "empty expression"
    pos, names = 0, []
    for m in _TOKEN_RE.finditer(expr):
        if m.start() != pos:
            return f"illegal character at {pos}: {expr[pos]!r}"
        pos = m.end()
        tok = m.group(0)
        if tok[:1].isalpha() or tok[:1] == "_":
            names.append(tok)
    if pos != len(expr):
        return f"illegal character at {pos}: {expr[pos]!r}"
    unknown = [n for n in names if n not in columns]
    if unknown:
        return f"not a column of this file: {', '.join(sorted(set(unknown)))}"
    if not names:
        return "expression names no column"
    return None


def _decimals(text: str) -> int | None:
    """Decimal places AS STORED. None when the cell is not a plain number."""
    t = (text or "").strip()
    if not re.fullmatch(r"[-+]?\d*\.?\d+([eE][-+]?\d+)?", t):
        return None
    if "e" in t.lower():             # scientific notation carries no ulp we can read
        return None
    return len(t.split(".")[1]) if "." in t else 0


def _cells(path: Path) -> list[dict]:
    """Rows as TEXT, so stored precision survives. pandas would cast it away."""
    with io.open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def _evaluate(expr: str, row: dict, names) -> float | None:
    env = {}
    for n in names:
        try:
            env[n] = float(row[n])
        except (TypeError, ValueError, KeyError):
            return None
    try:
        return float(eval(compile(ast.parse(expr, mode="eval"), "<rule>", "eval"),
                          {"__builtins__": {}}, env))
    except Exception:
        return None


def _envelope(expr: str, row: dict, names, result_txt: str) -> tuple[float, float] | None:
    """The admissible interval, from the stored precision of BOTH sides.

    Two terms, and leaving either out makes the gate wrong in a different way:

      the COMPONENTS   each moved +/- half a unit in its last stored place, one
                       at a time, taking the widest excursion. An upper bound on
                       the true interval for a monotone expression and never
                       tighter than it, which is the direction a gate should err.

      the RESULT       half a unit in ITS last stored place. Omitting this was a
                       real defect, caught by writing the test the spec asked
                       for: a quantity legitimately stored to two decimals sits
                       up to 0.005 from any recomputation of it, and a gate that
                       does not admit that fires on correct rounding. Measured
                       while building: a/b stored to 2 dp read 0.27 against a
                       recomputed 0.269146, outside a components-only envelope
                       of 0.26877-0.26952.

    D-035 keeps stores at full computed precision, so this term is usually
    negligible. It is not always, and a gate should not depend on a convention
    holding everywhere.
    """
    base = _evaluate(expr, row, names)
    if base is None:
        return None
    lo = hi = base
    for n in names:
        dp = _decimals(row.get(n, ""))
        if dp is None:
            return None
        half = 0.5 * 10.0 ** (-dp)
        for delta in (+half, -half):
            probe = dict(row)
            probe[n] = repr(float(row[n]) + delta)
            v = _evaluate(expr, probe, names)
            if v is None:
                return None
            lo, hi = min(lo, v), max(hi, v)
    rdp = _decimals(result_txt)
    if rdp is None:
        return None
    slack = 0.5 * 10.0 ** (-rdp)
    return lo - slack, hi + slack


def check_arithmetic(quiet: bool = False) -> int:
    if not RULES.exists():
        print(f"  {RED}FAULT{RESET}  {RULES.relative_to(ROOT)} is missing — the "
              f"register IS the gate; an absent one is not a pass")
        return 1
    rules = [r for r in _cells(RULES) if (r.get("csv") or "").strip()]
    faults, failures, checked, rows_checked = [], [], 0, 0

    for r in rules:
        rel = r["csv"].strip()
        path = ROOT / rel
        col = (r.get("result_col") or "").strip()
        expr = (r.get("expression") or "").strip()
        where = (r.get("rows") or "").strip()
        override = (r.get("tolerance_rel") or "").strip()
        if not path.exists():
            faults.append(f"{rel}: file does not exist")
            continue
        rows = _cells(path)
        if not rows:
            faults.append(f"{rel}: no data rows to check")
            continue
        columns = set(rows[0].keys())
        if col not in columns:
            faults.append(f"{rel}: result column {col!r} is not in the file")
            continue
        why = _validate(expr, columns)
        if why is not None:
            # A rule nobody can evaluate is a rule nobody is enforcing. FAULT,
            # never SKIP - cite_check 1.13.0 converted every one of its own for
            # exactly this reason.
            faults.append(f"{rel} · {col}: expression rejected — {why}")
            continue
        names = sorted({t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr)})
        sel_col, sel_val = (where.split("=", 1) + [""])[:2] if "=" in where else (None, None)
        checked += 1

        for i, row in enumerate(rows, start=2):        # 2 = first data line
            if sel_col and (row.get(sel_col.strip()) or "").strip() != sel_val.strip():
                continue
            stored_txt = (row.get(col) or "").strip()
            if stored_txt == "":
                continue                                # an absent value is not a claim
            stored = _evaluate(col, row, [col])
            if stored is None:
                faults.append(f"{rel} L{i} · {col}: stored value {stored_txt!r} "
                              f"is not numeric")
                continue
            got = _evaluate(expr, row, names)
            if got is None:
                continue                                # a component is blank here
            rows_checked += 1
            if override:
                tol = abs(float(override) * got)
                lo, hi = got - tol, got + tol
                basis = f"declared tolerance_rel {override}"
            else:
                env = _envelope(expr, row, names, stored_txt)
                if env is None:
                    faults.append(f"{rel} L{i} · {col}: cannot derive a tolerance — "
                                  f"a component is blank, non-numeric or in "
                                  f"scientific notation; declare tolerance_rel")
                    continue
                lo, hi = env
                basis = "derived from stored precision"
            if not (lo <= stored <= hi):
                rel_gap = abs(stored - got) / abs(got) if got else float("inf")
                failures.append(
                    (rel, i, col, expr, stored, got, lo, hi, rel_gap, basis,
                     {n: row.get(n) for n in names}))

    for f in faults:
        print(f"  {RED}FAULT{RESET}  {f}")
    for (rel, i, col, expr, stored, got, lo, hi, gap, basis, comps) in failures:
        print(f"\n  {RED}FAIL{RESET}  {rel}  line {i}")
        print(f"        {col} = {stored!r}, but {expr} = {got!r}")
        print(f"        components: " +
              ", ".join(f"{k}={v}" for k, v in comps.items()))
        print(f"        admissible {lo!r} to {hi!r}  ({basis})")
        print(f"        relative gap {gap:.2e}")

    if faults or failures:
        print(f"\nartefact_lint (arithmetic): FAIL — {len(failures)} row(s) "
              f"contradict their own columns, {len(faults)} fault(s).")
        print("  A row that does not reproduce its own quantity is not a record of")
        print("  a measurement. Fix the value or the rule — never widen the")
        print("  tolerance to make a real gap fit.")
        return 1

    if not quiet:
        undeclared = []
        declared = {(r["csv"].strip(), (r.get("result_col") or "").strip())
                    for r in rules}
        for p in sorted(OUTPUTS.rglob("*.csv")):
            rel = str(p.relative_to(ROOT))
            try:
                cols = pd.read_csv(p, nrows=0).columns.tolist()
            except Exception:
                continue
            for c in cols:
                if CANDIDATE_RE.search(str(c)) and (rel, str(c)) not in declared:
                    undeclared.append((rel, str(c)))
        print(f"  {GREEN}OK{RESET}    {rows_checked} row(s) reproduce their own "
              f"quantity across {checked} declared rule(s)")
        if undeclared:
            files = len({u[0] for u in undeclared})
            print(f"  {DIM}·     {len(undeclared)} column(s) in {files} file(s) look "
                  f"like a defined quantity and carry no rule (advisory){RESET}")
            print(f"  {DIM}      python3 tools/artefact_lint.py --candidates "
                  f"lists them{RESET}")
    print("artefact_lint (arithmetic): OK")
    return 0


def check_empty(quiet: bool = False) -> int:
    allowed = {}
    if ALLOWED_EMPTY.exists():
        for r in _cells(ALLOWED_EMPTY):
            if (r.get("csv") or "").strip():
                allowed[r["csv"].strip()] = (r.get("reason") or "").strip()
    bad, ok_allowed, total = [], [], 0
    for p in sorted(OUTPUTS.rglob("*.csv")):
        total += 1
        rel = str(p.relative_to(ROOT))
        with io.open(p, encoding="utf-8", errors="replace") as fh:
            lines = sum(1 for line in fh if line.strip())
        if lines > 1:
            continue
        (ok_allowed if rel in allowed else bad).append(rel)

    for rel in bad:
        print(f"  {RED}EMPTY{RESET}  {rel} — header only or blank")
    if bad:
        print(f"\nartefact_lint (empty): FAIL — {len(bad)} committed output(s) "
              f"carry no data.")
        print("  A step that could not run must LEAVE ITS COMMITTED FILE ALONE")
        print("  (see _write_or_preserve in 40_shoreline_retreat.py). If the")
        print("  emptiness is genuinely the finding, declare it in")
        print(f"  {ALLOWED_EMPTY.relative_to(ROOT)} with a reason and a date.")
        return 1
    if not quiet:
        print(f"  {GREEN}OK{RESET}    {total} committed CSV(s), none header-only"
              + (f"; {len(ok_allowed)} declared empty" if ok_allowed else ""))
    print("artefact_lint (empty): OK")
    return 0


def advise_source(quiet: bool = False) -> None:
    """Advisory: an empty container returned from inside an `except`.

    The shape that caused W128. It ADVISES rather than gates, because the shape
    is only a hazard when the value reaches a write, and proving that it does is
    the dataflow analysis check B declines to do.
    """
    hits = []
    for p in sorted(SRC.rglob("*.py")):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and sub.value is not None:
                    src = ast.unparse(sub.value)
                    if "DataFrame()" in src or src.strip() in ("{}", "[]"):
                        hits.append((p.name, sub.lineno, src))
    if hits and not quiet:
        print(f"  {DIM}·     {len(hits)} site(s) return an empty container from "
              f"an except handler (advisory){RESET}")
        for name, ln, src in hits:
            print(f"  {DIM}      {name}:{ln}  return {src}{RESET}")
        print(f"  {DIM}      return None instead, so a skip cannot be mistaken "
              f"for a result{RESET}")


def list_candidates() -> int:
    rules = _cells(RULES) if RULES.exists() else []
    declared = {(r["csv"].strip(), (r.get("result_col") or "").strip())
                for r in rules if (r.get("csv") or "").strip()}
    n = 0
    for p in sorted(OUTPUTS.rglob("*.csv")):
        rel = str(p.relative_to(ROOT))
        try:
            cols = pd.read_csv(p, nrows=0).columns.tolist()
        except Exception:
            continue
        hit = [str(c) for c in cols
               if CANDIDATE_RE.search(str(c)) and (rel, str(c)) not in declared]
        if hit:
            n += len(hit)
            print(f"  {rel}")
            for c in hit:
                print(f"      {c}")
    print(f"\n{n} undeclared candidate column(s). A row in "
          f"{RULES.relative_to(ROOT)} is a claim about what the quantity MEANS, "
          f"so read the file before adding one.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--arithmetic", action="store_true", help="check A only")
    ap.add_argument("--empty", action="store_true", help="check B only")
    ap.add_argument("--candidates", action="store_true",
                    help="list undeclared candidate columns and exit")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    if a.candidates:
        return list_candidates()
    both = not (a.arithmetic or a.empty)
    rc = 0
    if a.arithmetic or both:
        rc |= check_arithmetic(a.quiet)
    if a.empty or both:
        rc |= check_empty(a.quiet)
        advise_source(a.quiet)
    return rc


if __name__ == "__main__":
    sys.exit(main())
