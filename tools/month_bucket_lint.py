#!/usr/bin/env python3
"""month_bucket_lint — the bucketing rule has ONE implementation, and it is right.

Two checks, both cheap, both gates:

  A. EQUIVALENCE, exhaustively. `model_utils.month_bucket` is compared against
     every correct variant this tree has carried, on EVERY DAY from 1990 to 2040.
     An exhaustive sweep is possible here because the function's whole input
     domain is dates, so this is a proof rather than a sample: if it passes, no
     script moved onto the helper can have changed its output.

  B. NO REGRESSION. No live line of Python may bucket with
     `- pd.offsets.MonthBegin(1)`, which is a no-op for days 2-15 and is the
     defect of T-32 — fixed once on 2026-09-13 and reintroduced two days later.
     Comments and docstrings that WARN about the form are allowed; code is not.

Written 2026-09-16 (T-32). `python3 tools/month_bucket_lint.py`
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from utils.buckets import month_bucket                         # noqa: E402

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-16. New, for T-32.

SPAN = ("1990-01-01", "2040-12-31")
SKIP_DIRS = {"venv", ".git", ".git-working", "_to_delete", "scratch", "outputs"}


def _v_script01(d):
    """src/01_data_prep.py bucket(), the scalar form."""
    d = pd.Timestamp(d)
    if d.day > 15:
        return pd.Timestamp(d.year, d.month, 1)
    b = d.replace(day=1) - pd.offsets.MonthBegin(1)
    return pd.Timestamp(b.year, b.month, 1)


def _v_comment_states(d):
    """src/utils/comment_states.py _bucket_to_month()."""
    d = pd.Timestamp(d)
    m = (d.replace(day=1) if d.day > 15
         else d.replace(day=1) - pd.offsets.MonthBegin(1))
    return pd.Timestamp(m.year, m.month, 1)


def _v_well_levels(d):
    """warren_flood_prep._well_levels, the day-before-the-first form."""
    d = pd.Timestamp(d)
    if d.day <= 15:
        prev = d.replace(day=1) - pd.Timedelta(days=1)
        return pd.Timestamp(prev.year, prev.month, 1)
    return pd.Timestamp(d.year, d.month, 1)


def _v_day_subtraction(d):
    """warren_flood_prep._pflood_bucket / _month_of, the day-subtraction form."""
    d = pd.Timestamp(d)
    b = d if d.day > 15 else d - pd.Timedelta(days=int(d.day))
    return pd.Timestamp(b.year, b.month, 1)


def _v_period(d):
    """src/01_data_prep.py line 929, the vectorised period form."""
    di = pd.DatetimeIndex([pd.Timestamp(d)])
    per = di.to_period("M")
    return pd.DatetimeIndex(np.where(di.day <= 15, (per - 1).to_timestamp(),
                                     per.to_timestamp()))[0]


VARIANTS = {"01_data_prep.bucket": _v_script01,
            "01_data_prep vectorised period form": _v_period,
            "comment_states._bucket_to_month": _v_comment_states,
            "warren_flood_prep._well_levels": _v_well_levels,
            "warren_flood_prep day-subtraction": _v_day_subtraction}

fails = []
days = pd.date_range(*SPAN, freq="D")
print(f"month_bucket_lint {__version__}")
print(f"\nA. equivalence over every day from {SPAN[0]} to {SPAN[1]} "
      f"({len(days):,} dates)")

got = month_bucket(days)
if not isinstance(got, pd.DatetimeIndex) or len(got) != len(days):
    fails.append("month_bucket did not return one bucket per input date")
else:
    # the vectorised path must equal the scalar path on itself, first
    spot = pd.date_range("2019-01-01", "2022-12-31", freq="D")
    scal = pd.DatetimeIndex([month_bucket(x) for x in spot])
    same = bool((scal == month_bucket(spot)).all())
    print(f"  {'PASS' if same else 'FAIL'}  scalar and vector paths agree "
          f"({len(spot):,} dates)")
    if not same:
        fails.append("month_bucket's scalar and vector paths disagree")
    for name, fn in VARIANTS.items():
        ref = pd.DatetimeIndex([fn(x) for x in days])
        bad = int((ref != got).sum())
        print(f"  {'PASS' if not bad else 'FAIL'}  {name:38} "
              f"{'identical on every date' if not bad else f'{bad:,} disagreement(s)'}")
        if bad:
            i = int(np.flatnonzero((ref != got).to_numpy())[0])
            print(f"        first: {days[i]:%Y-%m-%d} -> helper "
                  f"{got[i]:%Y-%m} vs variant {ref[i]:%Y-%m}")
            fails.append(f"month_bucket disagrees with {name}")

# the rule itself, stated independently of every variant
checks = [("2021-03-24", "2021-03"), ("2021-04-01", "2021-03"),
          ("2021-04-02", "2021-03"), ("2021-04-15", "2021-03"),
          ("2021-04-16", "2021-04"), ("2021-01-05", "2020-12"),
          ("2020-12-31", "2020-12"), ("2005-01-10", "2004-12")]
print("\n   the rule, stated directly:")
for d, want in checks:
    g = month_bucket(d).strftime("%Y-%m")
    print(f"     {'PASS' if g == want else 'FAIL'}  {d} -> {g}"
          + ("" if g == want else f"  (want {want})"))
    if g != want:
        fails.append(f"month_bucket({d}) = {g}, want {want}")

print("\nB. no live code buckets with MonthBegin")
offenders = []
for py in sorted(REPO.rglob("*.py")):
    if any(part in SKIP_DIRS for part in py.relative_to(REPO).parts):
        continue
    try:
        src = py.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue
    if "MonthBegin" not in src:
        continue
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    # only ATTRIBUTE ACCESS in real code counts; prose is invisible to the AST
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "MonthBegin":
            line = src.splitlines()[node.lineno - 1]
            if "- pd.offsets.MonthBegin" in line or "-pd.offsets.MonthBegin" in line:
                rel = py.relative_to(REPO)
                # the helper's own reference variants are the sanctioned copies
                if rel == Path("tools/month_bucket_lint.py"):
                    continue
                offenders.append(f"{rel}:{node.lineno}: {line.strip()[:70]}")
print(f"  {'PASS' if not offenders else 'FAIL'}  "
      f"{len(offenders)} live MonthBegin subtraction(s) outside this lint")
for o in offenders:
    print(f"        {o}")
    fails.append(f"MonthBegin bucketing at {o.split(':')[0]}")

print()
if fails:
    print(f"month_bucket_lint: FAIL ({len(fails)} problem(s))")
    sys.exit(1)
print("month_bucket_lint: OK")
