#!/usr/bin/env python3
"""
pipeline_lint.py
================
Three checks on whether the SCRIPTS are working from the right numbers.

tools/cite_check.py answers "do the documents quote the pipeline correctly?".
This answers the question underneath it: is the pipeline itself importing what
it claims to, or has a value been silently substituted somewhere upstream?

  defaults   Is any committed parameter still a first-pass DEFAULT?
             pipeline_scenario_params.csv marks every parameter `pipeline` or
             `defaults`. A default that survives into the outputs looks exactly
             like a measurement, and today the only signal is a console print
             that scrolls past in a long run. This makes it fail.

  deps       Does any script read an output produced LATER in the run?
             utils/pipeline_deps.py finds these statically. UNGUARDED cases
             hard-fail on a fresh run — or worse, silently pick up a stale file
             from the previous one. Guarded cases fall back to a default, which
             is the `defaults` check above waiting to happen.

  literals   Does a script hard-code a number that should come from config.py
             or an upstream CSV? The project rule is that it must not: shared
             constants live in config.py and are imported. A pasted 3.7 or
             0.0566 is either a duplicated constant that will drift, or a
             result frozen at the moment someone read it.

Usage:
    python3 tools/pipeline_lint.py                 # all three
    python3 tools/pipeline_lint.py --check literals
    python3 tools/pipeline_lint.py --check literals --min-sig 4
"""
from __future__ import annotations

import argparse
import ast
import csv
import glob
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
PARAMS = REPO / "outputs" / "01_data_prep" / "pipeline_scenario_params.csv"
MANIFEST = REPO / "outputs" / "pipeline_manifest.json"

G, Y, R, B, N = "\033[0;32m", "\033[1;33m", "\033[0;31m", "\033[1m", "\033[0m"

# Literals that are structural rather than scientific: plotting geometry, axis
# limits, percentages, seeds. A match on one of these means nothing.
SKIP_KWARGS = {
    "figsize", "dpi", "fontsize", "labelsize", "titlesize", "alpha", "lw",
    "linewidth", "ms", "markersize", "markeredgewidth", "mew", "pad", "labelpad",
    "bins", "zorder", "rotation", "s", "capsize", "elinewidth", "wspace",
    "hspace", "left", "right", "top", "bottom", "width", "height", "x", "y",
    "vmin", "vmax", "ncol", "nrows", "ncols", "seed", "random_state", "n_init",
    "framealpha", "title_fontsize", "aspect", "shrink", "fraction", "extend",
    "expand", "force_text", "force_points", "pad_inches", "borderpad",
}
# Files that are allowed to hold constants by definition.
SKIP_FILES = {"config.py", "paths.py", "pipeline_params.py"}

# Positional arguments to these carry plot geometry. A scenario multiplier that
# happens to equal an axis limit is a coincidence — ax.set_ylim(0, P*1.12) is
# headroom, not UKCP18_DRY_PET_SUMMER. But a MAP/FIG constant matched inside one
# of them is the real thing: the canonical map extent typed out by hand.
PLOT_CALLS = {
    "set_xlim", "set_ylim", "set_zlim", "axvspan", "axhspan", "axvline",
    "axhline", "set_xticks", "set_yticks", "set_position", "text", "annotate",
    "set_clim", "margins", "set_xbound", "set_ybound",
}
GEOMETRY_PREFIXES = ("SITE_MAP_", "MAP_", "FIG_", "GRID_", "CANON_")

# A literal only FAILs if it is long enough that matching a config constant is
# unlikely to be chance. Three significant figures collide constantly - a plot
# padding of 1.05 is not a re-typed UKCP18 multiplier, and before this rule the
# check failed on a dozen such coincidences and was therefore ignored. Six or
# eight figures do not collide: 240100 and 20260424 are the constant. Shorter
# matches still print, as warnings, so a real one is visible if you look.
FAIL_MIN_SIG = 4


def is_year(v: float) -> bool:
    return float(v).is_integer() and 1900 <= v <= 2100


def sig_digits(x: float) -> int:
    s = repr(float(x))
    if "e" in s or "E" in s:
        s = f"{x:.10f}"
    return len(re.sub(r"[^0-9]", "", s).lstrip("0").rstrip("0")) or 1


# ───────────────────────── defaults ──────────────────────────────────────────
def check_defaults() -> int:
    print(f"{B}defaults{N} — is any committed parameter still a first-pass default?")
    if not PARAMS.exists():
        print(f"  {Y}skip{N}: {PARAMS.relative_to(REPO)} not present")
        return 0
    with open(PARAMS, encoding="utf8") as fh:
        rows = list(csv.DictReader(fh))
    src_cols = [c for c in rows[0] if c.startswith("source_")]
    bad = [(r.get("Cluster", "?"), c) for r in rows for c in src_cols
           if str(r[c]).strip().lower() == "defaults"]
    n = len(rows) * len(src_cols)
    if bad:
        print(f"  {R}FAIL{N}: {len(bad)} of {n} parameter(s) are still defaults:")
        for cl, c in bad:
            print(f"        {cl}  {c.replace('source_', '')}")
        print("        Run the full pipeline twice so the producing scripts fill them.")
        return len(bad)
    print(f"  {G}OK{N}: all {n} parameter provenance cells read 'pipeline'")
    return 0


# ───────────────────────── deps ──────────────────────────────────────────────
def check_deps() -> int:
    print(f"\n{B}deps{N} — does any script read an output produced later in the run?")
    if not MANIFEST.exists():
        print(f"  {Y}skip{N}: no committed manifest")
        return 0
    sys.path.insert(0, str(SRC))
    try:
        from utils.pipeline_deps import build_dependencies
    except Exception as e:
        print(f"  {Y}skip{N}: could not import pipeline_deps ({e})")
        return 0
    # Take the step map from the committed manifest. pipeline_deps' own
    # standalone path looks for run_analysis.py inside src/, where it does not
    # live, so it only ever worked when the orchestrator passed a map in.
    steps = json.load(open(MANIFEST, encoding="utf8"))["steps"]
    step_map = {s["script"]: s["index"] for s in steps}
    deps = build_dependencies(SRC, step_map=step_map)
    unguarded, guarded = [], []
    for d in deps:
        (guarded if getattr(d, "guarded", False) else unguarded).append(d)
    for d in guarded:
        print(f"  {Y}warn{N}  {getattr(d, 'reader', '?')} reads "
              f"{getattr(d, 'const', '?')} (produced later; guarded fallback)")
    for d in unguarded:
        print(f"  {R}FAIL{N}  {getattr(d, 'reader', '?')} reads "
              f"{getattr(d, 'const', '?')} (produced later; UNGUARDED)")
    if not deps:
        print(f"  {G}OK{N}: no down-pipeline dependencies")
    elif not unguarded:
        print(f"  {G}OK{N}: {len(guarded)} guarded fallback(s), none unguarded "
              "— but a fallback that fires becomes a 'defaults' failure above")
    return len(unguarded)


# ───────────────────────── literals ──────────────────────────────────────────
def config_constants() -> dict[float, list[str]]:
    """Module-level numeric constants in config.py, by value."""
    out: dict[float, list[str]] = {}
    p = SRC / "utils" / "config.py"
    if not p.exists():
        return out
    tree = ast.parse(p.read_text(encoding="utf8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        v = node.value
        if isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.USub) \
                and isinstance(v.operand, ast.Constant):
            val = -v.operand.value
        elif isinstance(v, ast.Constant):
            val = v.value
        else:
            continue
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            continue
        for t in node.targets:
            if isinstance(t, ast.Name):
                out.setdefault(float(val), []).append(t.id)
    return out


def committed_values() -> dict[float, list[str]]:
    """Values published in committed report-numbers CSVs, by value."""
    out: dict[float, list[str]] = {}
    for p in glob.glob(str(REPO / "outputs/**/*report_numbers*.csv"), recursive=True):
        try:
            with open(p, encoding="utf8") as fh:
                for row in csv.DictReader(fh):
                    vals = list(row.values())
                    key = vals[0]
                    for cell in vals[1:]:
                        try:
                            f = float(cell)
                        except (TypeError, ValueError):
                            continue
                        out.setdefault(f, []).append(f"{Path(p).name}:{key}")
                        break
        except Exception:
            pass
    return out


ALLOW_PATH = Path(__file__).with_name("pipeline_lint_literals_allow.csv")


def load_allowlist() -> dict:
    """
    Deliberate re-typings, keyed (script, literal, config constant) so that a
    line edit cannot silently drop an exemption.

    Two kinds live here. Some are settled decisions: the map extents in Scripts
    07, 11b and 20 are pinned inline by D-013 and must NOT be repointed at
    config. Others are collisions - a plot axis limit that happens to equal a
    UKCP18 multiplier is not a re-typed constant. Before this file the check
    failed on every run, and a check that always fails is a check nobody reads.
    """
    if not ALLOW_PATH.exists():
        return {}
    out = {}
    with open(ALLOW_PATH, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            script = (row.get("script") or "").strip()
            if not script or script.startswith("#"):
                continue
            lit = (row.get("literal") or "").strip()
            try:                      # normalise so 20260424 and 2.02604e+07 agree
                lit = f"{float(lit):g}"
            except ValueError:
                pass
            out[(script, lit, (row.get("constant") or "").strip())] = (
                (row.get("reason") or "").strip())
    return out


def check_literals(min_sig: int) -> int:
    allowed = load_allowlist()
    print(f"\n{B}literals{N} — does a script hard-code a config constant or a "
          f"published value?")
    cfg, pub = config_constants(), committed_values()
    hits = 0
    for path in sorted(SRC.glob("*.py")):
        if path.name in SKIP_FILES:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf8"))
        except SyntaxError:
            continue
        skip_nodes, plot_nodes = set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg in SKIP_KWARGS:
                        for sub in ast.walk(kw.value):
                            skip_nodes.add(id(sub))
                fn = node.func
                name = fn.attr if isinstance(fn, ast.Attribute) else \
                    (fn.id if isinstance(fn, ast.Name) else "")
                if name in PLOT_CALLS:
                    for a in node.args:
                        for sub in ast.walk(a):
                            plot_nodes.add(id(sub))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or id(node) in skip_nodes:
                continue
            val = node.value
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                continue
            f = float(val)
            if abs(f) < 1e-12 or sig_digits(f) < min_sig:
                continue
            if f in cfg:
                cname = cfg[f][0]
                geometry = cname.startswith(GEOMETRY_PREFIXES)
                in_plot = id(node) in plot_nodes
                # Coincidence classes, reported but not failed:
                #   a non-geometry constant inside a plotting call (axis limits)
                #   a year matching a year-valued constant (2011 is just 2011)
                soft = ((in_plot and not geometry) or is_year(f)
                        or sig_digits(f) < FAIL_MIN_SIG)
                key = (path.name, f"{f:g}", cname)
                if key in allowed:
                    print(f"  {G}ok{N}    {path.name}:{node.lineno}  {f:g} "
                          f"vs config.{cname} — allowed: {allowed[key]}")
                elif soft:
                    why = ("plot geometry" if in_plot else
                           "a year" if is_year(f) else
                           f"only {sig_digits(f)} significant figures")
                    print(f"  {Y}warn{N}  {path.name}:{node.lineno}  {f:g} "
                          f"equals config.{cname} — likely coincidence ({why})")
                else:
                    print(f"  {R}FAIL{N}  {path.name}:{node.lineno}  {f:g} "
                          f"== config.{cname}  — import it, do not retype it")
                    hits += 1
            elif f in pub:
                print(f"  {Y}warn{N}  {path.name}:{node.lineno}  {f:g} "
                      f"matches {pub[f][0]} — a published result frozen in code?")
    if not hits:
        print(f"  {G}OK{N}: no script re-types a config constant "
              f"(at ≥{min_sig} significant digits)")
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", default="all",
                    choices=["all", "defaults", "deps", "literals"])
    ap.add_argument("--min-sig", type=int, default=3,
                    help="ignore literals with fewer significant digits")
    args = ap.parse_args()
    rc = 0
    if args.check in {"all", "defaults"}:
        rc += check_defaults()
    if args.check in {"all", "deps"}:
        rc += check_deps()
    if args.check in {"all", "literals"}:
        rc += check_literals(args.min_sig)
    print(f"\npipeline_lint: {'FAIL' if rc else 'OK'}")
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
