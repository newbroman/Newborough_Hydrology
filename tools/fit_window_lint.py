#!/usr/bin/env python3
"""fit_window_lint.py — every SSM fit states its window (D-349 (1)).

D-347 gave utils.model_utils.fit_ssm a default that cut every series at config.RECORD_FIT_START (January 2010). It
silently shortened fits whose callers lay out their own windows, and emptied Script 25's before-the-2009-step fits.
D-349 (1) withdrew the default: model_utils 1.16.0 raises at run time when a call omits start=. This lint finds the
same omission statically, so a call on a rarely-run path cannot wait for the day it runs.

    python3 tools/fit_window_lint.py            # FAIL lists every call to fit_ssm / fit_ssm_censored /
                                                # fit_ssm_intercept under src/ without a start= keyword
"""
import ast, pathlib, sys
__version__ = "1.0.0"  # 2026-11-27 (D-349 (1))
ROOT = pathlib.Path(__file__).resolve().parents[1]
NAMES = {"fit_ssm", "fit_ssm_censored", "fit_ssm_intercept"}
bad, n = [], 0
for f in sorted((ROOT / "src").rglob("*.py")):
    try:
        tree = ast.parse(f.read_text(encoding="utf-8"))
    except SyntaxError as e:
        bad.append(f"{f.relative_to(ROOT)}: does not parse ({e})"); continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
            if name in NAMES:
                n += 1
                kws = {k.arg for k in node.keywords}
                if "start" not in kws and None not in kws:      # None: a **kwargs pass-through, judged by its source
                    bad.append(f"{f.relative_to(ROOT)}:{node.lineno}  {name}(...) states no start=")
for b in bad:
    print("  " + b)
print(f"fit_window_lint: {'FAIL' if bad else 'OK'} - {n} fit call(s) under src/, {len(bad)} without a window")
sys.exit(1 if bad else 0)
