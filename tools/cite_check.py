#!/usr/bin/env python3
"""
cite_check.py
=============
Standing check that the document corpus still agrees with the committed
pipeline outputs.

tools/audit_number_drift.py is CHANGE-triggered: it diffs two git refs and
hunts for renderings of the value that just changed. It cannot see a number
that went stale before anyone was watching — which is how report9 and Paper 1
both carried five superseded cluster coefficients for weeks while the tooling
reported clean.

This tool is STANDING: it asks, of every value the pipeline currently publishes,
whether the corpus still quotes it — and, where it does not, whether the corpus
quotes a NEAR MISS instead. A near miss is the signature of a stale citation:
0.090 where the CSV now says 0.088, VIF 1.11 where it says 1.09.

It also evaluates a small register of CLAIMS — the assertions that carry no
number and so no numeric tool can check. "C4 has the lowest VIF in the network"
is either true of the committed CSV or it is not; the register makes that
machine-decidable and names every document asserting it.

Usage:
    python3 tools/cite_check.py                  # numbers + claims
    python3 tools/cite_check.py --claims-only
    python3 tools/cite_check.py --dp 2 3 4 --near 2
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]

# Mirrors only — never the ODTs. Keep in step with refresh_mirrors.py.
DOC_GLOBS = [
    "report_edits/text/report*.md",
    "docs/report/text/*.md",
    "docs/papers/**/text/*.md",
]

# Headline tables whose values are cited directly rather than via a
# report-numbers key. (csv path, key column, value columns).
HEADLINE_TABLES = [
    ("outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv",
     "Cluster_Label",
     ["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage", "R2"]),
]

# Claims register. rule is evaluated against the named CSV.
#   argmin:<col>  / argmax:<col>  -> `expect` must be the value of `key_col`
# Extend this rather than restating a claim in prose.
CLAIMS_REGISTER = "tools/claims_register.csv"

# Archived output trees produced by no live script — their values are history,
# not current publications, so they must not drive a staleness verdict.
EXCLUDE_OUTPUT_DIRS = ("30_c4_constrained_fit",)

# A rendering is searchable only if it carries enough significant digits to be
# distinctive. "0.02" matches thousands of unrelated places; "0.0183" does not.
MIN_SIG_DIGITS = 3


def _sig_digits(s: str) -> int:
    return len(re.sub(r"[^1-9]", "", s.lstrip("-0.").replace(".", "")) or "") + \
        len(re.findall(r"(?<=[1-9])0", s.replace(".", "")))


def searchable(s: str) -> bool:
    digits = re.sub(r"[^0-9]", "", s).lstrip("0")
    return len(digits) >= MIN_SIG_DIGITS


def load_documents() -> dict[str, str]:
    docs: dict[str, str] = {}
    for g in DOC_GLOBS:
        for p in REPO.glob(g):
            try:
                docs[str(p.relative_to(REPO))] = p.read_text(encoding="utf8")
            except OSError:
                pass
    return docs


def render(v: float, dp: int) -> str:
    return f"{v:.{dp}f}"


def near_misses(v: float, dp: int, span: int) -> list[str]:
    """Renderings within `span` units of the last decimal place, excluding v."""
    step = 10 ** -dp
    out = []
    for k in range(-span, span + 1):
        if k == 0:
            continue
        out.append(render(v + k * step, dp))
    return out


def collect_values() -> list[tuple[str, str, float]]:
    """[(source, label, value)] from report-numbers files and headline tables."""
    vals: list[tuple[str, str, float]] = []
    for p in sorted(REPO.glob("outputs/**/*report_numbers*.csv")):
        if any(d in p.parts for d in EXCLUDE_OUTPUT_DIRS):
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = {c.lower(): c for c in df.columns}
        kcol = cols.get("key") or df.columns[0]
        vcol = cols.get("value")
        if vcol is None:
            num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if not num:
                continue
            vcol = num[0]
        for _, r in df.iterrows():
            try:
                vals.append((str(p.relative_to(REPO)), str(r[kcol]), float(r[vcol])))
            except (TypeError, ValueError):
                continue
    for rel, kcol, vcols in HEADLINE_TABLES:
        p = REPO / rel
        if not p.exists():
            continue
        df = pd.read_csv(p)
        for _, r in df.iterrows():
            for c in vcols:
                try:
                    vals.append((rel, f"{r[kcol]} · {c}", float(r[c])))
                except (TypeError, ValueError, KeyError):
                    continue
    return vals


def check_numbers(docs, dps, span) -> int:
    print("=" * 78)
    print("NUMBERS — every published value vs the corpus")
    print("=" * 78)
    stale, uncited, ok = [], [], 0
    for source, label, v in collect_values():
        if not (abs(v) > 0):
            continue
        hit_dp = None
        for dp in dps:
            s = render(v, dp)
            if not searchable(s):
                continue
            if any(s in t for t in docs.values()):
                hit_dp = dp
                break
        if hit_dp is not None:
            ok += 1
            continue
        found = []
        for dp in sorted(dps, reverse=True):   # most precise first
            if not searchable(render(v, dp)):
                continue
            for nm in near_misses(v, dp, span):
                if not searchable(nm):
                    continue
                where = [d for d, t in docs.items() if nm in t]
                if where:
                    found.append((nm, dp, where))
            if found:
                break                          # one precision level is enough
        if found:
            stale.append((source, label, v, found))
        else:
            uncited.append((source, label, v))

    for source, label, v, found in stale:
        print(f"\n  STALE?  {label}")
        print(f"          committed {v:g}   ({source})")
        for nm, dp, where in found[:3]:
            print(f"          corpus has {nm} at {dp}dp in: {', '.join(sorted(where))}")
    print(f"\n  {ok} value(s) cited and current; {len(stale)} possible stale "
          f"citation(s); {len(uncited)} not cited anywhere (informational).")
    return len(stale)


def check_claims(docs) -> int:
    reg = REPO / CLAIMS_REGISTER
    print()
    print("=" * 78)
    print("CLAIMS — assertions with no number, checked against the CSV")
    print("=" * 78)
    if not reg.exists():
        print(f"  no register at {CLAIMS_REGISTER} — skipped")
        return 0
    bad = 0
    for row in csv.DictReader(open(reg, encoding="utf8")):
        p = REPO / row["csv"]
        if not p.exists():
            print(f"  SKIP   {row['claim_id']}: {row['csv']} missing")
            continue
        df = pd.read_csv(p)
        kind, _, col = row["rule"].partition(":")
        if kind not in {"argmin", "argmax"} or col not in df.columns:
            print(f"  SKIP   {row['claim_id']}: unsupported rule {row['rule']!r}")
            continue
        idx = df[col].idxmin() if kind == "argmin" else df[col].idxmax()
        actual = str(df.loc[idx, row["key_col"]])
        holds = actual == row["expect"]
        if not holds:
            bad += 1
        print(f"  {'HOLDS ' if holds else 'FALSE '} {row['claim_id']}: "
              f"{row['assertion']}")
        if not holds:
            print(f"          {row['rule']} is {actual!r}, not {row['expect']!r}")
        # where is it asserted?
        needle = row.get("phrase", "").strip()
        if needle:
            where = [d for d, t in docs.items() if needle in t]
            if where:
                print(f"          asserted in: {', '.join(sorted(where))}")
            elif not holds:
                print("          phrase not found in the corpus (already fixed?)")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dp", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--near", type=int, default=2,
                    help="near-miss span in units of the last decimal place")
    ap.add_argument("--claims-only", action="store_true")
    args = ap.parse_args()

    docs = load_documents()
    if not docs:
        print("No mirrors found — run tools/refresh_mirrors.py first.")
        return 1
    print(f"corpus: {len(docs)} mirror(s)\n")

    rc = 0
    if not args.claims_only:
        rc += check_numbers(docs, args.dp, args.near)
    rc += check_claims(docs)
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
