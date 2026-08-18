#!/usr/bin/env python3
"""
record_basis_lint.py
====================
Check that `tools/record_basis.csv` still describes the code.

Methods Supplement §F.6 tells the reader which record each analysis is fitted on.
That paragraph has been wrong before — for months the supplement attributed a
100-month fitting window to Script 07, which performs no fit at all — and prose
describing code is exactly the thing that drifts silently. This makes the
description mechanically checkable.

Three verification modes, declared per row in the `verify` column:

  ast_window   The named script must contain, among its fit_ssm /
               fit_ssm_intercept / build_ssm_frame calls, the window expression
               the row declares. `window=None` and `window=LCSC_DATA_LIMIT` are
               matched literally; `window_absent` means the call omits the
               argument and therefore takes fit_ssm's default of the full
               record. Multiple expectations are separated by ';' and ALL must
               be present — that is how a row like Script 30's "both bases" is
               enforced.

  no_fit       The named script must contain NO such call. This is the check
               that would have caught the Script 07 claim.

  OK*          A declared window that reaches the fit through a helper rather
               than appearing at the call. Verified only as "this constant is
               handed to something in this module", which is weaker than the
               direct check and is printed differently so it cannot be mistaken
               for one.

  manual       Not mechanically checkable — era windows, aggregation windows,
               admission rules. Reported, never silently passed.

Usage:
    python3 tools/record_basis_lint.py
    python3 tools/record_basis_lint.py --quiet
"""
from __future__ import annotations

import argparse
import ast
import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
TABLE = REPO / "tools" / "record_basis.csv"
FIT_CALLS = {"fit_ssm", "fit_ssm_intercept", "build_ssm_frame"}
G, Y, R, B, N = "\033[0;32m", "\033[1;33m", "\033[0;31m", "\033[1m", "\033[0m"


def call_arg_names(tree) -> set[str]:
    """Identifiers passed as arguments to ANY call in the module.

    Needed because a script may route the window through a helper —
    `_panel_fit(series, climate, LCSC_DATA_LIMIT)` — so the literal never appears
    at the fit call itself. Seeing the identifier handed to something is weaker
    evidence than seeing it at the call, and is reported as such.
    """
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for a in list(node.args) + [k.value for k in node.keywords if k.arg]:
                for sub in ast.walk(a):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
    return names


def window_exprs(path: Path) -> list[str]:
    """Every fit call's window argument, as source text; 'window_absent' if omitted."""
    out = []
    tree = ast.parse(path.read_text(encoding="utf8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
        if name not in FIT_CALLS:
            continue
        kw = {k.arg: k.value for k in node.keywords if k.arg}
        # A pre-built frame carries its own windowing; the call cannot re-window.
        if "pre_built_frame" in kw:
            continue
        if "window" in kw:
            out.append("window=" + ast.unparse(kw["window"]))
        else:
            out.append("window_absent")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if not TABLE.exists():
        print(f"FAIL  no {TABLE.relative_to(REPO)}")
        return 1

    rows = list(csv.DictReader(open(TABLE, encoding="utf8")))
    fail = manual = 0
    if not args.quiet:
        print(f"{B}record_basis{N} — does §F.6 still describe the code? "
              f"({len(rows)} rows)\n")

    for row in rows:
        rid, mode = row["id"], row["verify"].strip()
        scripts = [s.strip() for s in row["scripts"].split(";") if s.strip()]
        if mode == "manual":
            manual += 1
            if not args.quiet:
                print(f"  {Y}manual{N} {rid}  {row['analysis']} — {row['notes'][:60]}")
            continue

        for s in scripts:
            p = SRC / s
            if not p.exists():
                print(f"  {R}FAIL{N}   {rid}  {s} does not exist")
                fail += 1
                continue
            found = window_exprs(p)

            if mode == "no_fit":
                if found:
                    print(f"  {R}FAIL{N}   {rid}  {s} declares no fit, but calls one "
                          f"({', '.join(sorted(set(found)))})")
                    fail += 1
                elif not args.quiet:
                    print(f"  {G}OK{N}     {rid}  {s} performs no fit, as declared")

            elif mode == "ast_window":
                want = [w.strip() for w in row["expect"].split(";") if w.strip()]
                missing = [w for w in want if w not in found]
                # A window routed through a helper shows up as window=<local>.
                # Fall back to: is the declared constant handed to anything in
                # this module? Weaker, and labelled weaker.
                indirect = [f for f in found
                            if f.startswith("window=") and f not in want
                            and f != "window_absent"]
                soft = []
                if missing and indirect:
                    names = call_arg_names(ast.parse(p.read_text(encoding="utf8")))
                    for w in list(missing):
                        ident = w.split("=", 1)[1]
                        if ident in names:
                            missing.remove(w)
                            soft.append(w)
                if missing:
                    print(f"  {R}FAIL{N}   {rid}  {s} declares {', '.join(want)} "
                          f"but its fit calls use {', '.join(sorted(set(found))) or 'none'}"
                          f"  (missing: {', '.join(missing)})")
                    fail += 1
                elif soft:
                    if not args.quiet:
                        print(f"  {Y}OK*{N}    {rid}  {s} fits on "
                              f"{', '.join(w for w in want if w not in soft) or '-'}; "
                              f"{', '.join(soft)} reached indirectly "
                              f"(passed through a helper, verified only as an argument)")
                elif not args.quiet:
                    print(f"  {G}OK{N}     {rid}  {s} fits on {', '.join(want)}")
            else:
                print(f"  {R}FAIL{N}   {rid}  unknown verify mode {mode!r}")
                fail += 1

    if not args.quiet:
        print(f"\n  {manual} row(s) not mechanically checkable — era windows, "
              "aggregation windows and admission rules are read by eye")
    print("record_basis_lint: FAIL" if fail else "record_basis_lint: OK")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
