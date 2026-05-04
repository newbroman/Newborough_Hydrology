"""
run_10_clearfell.py — Clearfell BACI Analysis Suite Runner
Runs the modular Script 10 sub-scripts (10a–10g) in order and
consolidates report numbers.

Usage
-----
  Called by run_analysis.py as a single pipeline step, or directly:
    python src/run_10_clearfell.py            # run all sub-scripts
    python src/run_10_clearfell.py --only 10a # run one sub-script
    python src/run_10_clearfell.py --from 10d # resume from a sub-script

Execution order
---------------
  10a  Three-counterfactual ANCOVA-BACI (primary result)
  10b  Spatial step-change maps
  10c  Forest zone spatial analysis
  10d  Summer minima analysis (dual control)
  10e  SSM coefficient decomposition
  10f  Robustness analyses (SSM residual, synthetic control)
  10g  Diagnostics (NW10 trend, transect, rolling coefficients)

Dependencies
------------
  10b and 10c read from Script 03 outputs (independent of 10a).
  10d and 10e are independent of 10a but benefit from its report numbers
  for the predicted-vs-observed comparison in 10e.
  10f reads 10a outputs for the ANCOVA comparison.
  10g is standalone diagnostics.
"""

import subprocess
import sys
import argparse
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
_THIS_DIR = Path(__file__).resolve().parent
ROOT_DIR = _THIS_DIR.parent if _THIS_DIR.name == "src" else _THIS_DIR
SRC_DIR  = ROOT_DIR / "src"
OUT_DIR  = ROOT_DIR / "outputs"
DIR_10   = OUT_DIR / "10_clearfell_baci"

# ── Sub-script definitions ───────────────────────────────────────────────────
# (script_filename, short_id, description)
SUBSCRIPTS = [
    ("10a_ancova_baci.py",               "10a", "Three-counterfactual ANCOVA-BACI"),
    ("10b_spatial_step_maps.py",         "10b", "Spatial step-change maps"),
    ("10c_forest_zone_analysis.py",      "10c", "Forest zone spatial analysis"),
    ("10d_summer_minima.py",             "10d", "Summer minima (dual control)"),
    ("10e_coefficient_decomposition.py", "10e", "SSM coefficient decomposition"),
    ("10f_robustness.py",               "10f", "Robustness analyses"),
    ("10g_diagnostics.py",              "10g", "Diagnostics"),
]


def _hr(char="─", width=70):
    print(char * width)


def run_subscript(script_name, label, description):
    """Run a single sub-script via subprocess."""
    script_path = SRC_DIR / script_name
    if not script_path.exists():
        print(f"  [SKIP] {script_name} — not found")
        return False
    _hr()
    print(f"  {label}  {description}")
    print(f"  Script: {script_path.name}")
    _hr()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT_DIR),
    )
    if result.returncode != 0:
        print(f"\n  [ERROR] {script_name} exited with code {result.returncode}")
        return False
    return True


def consolidate_report_numbers():
    """Merge per-sub-script report numbers into a single CSV."""
    import pandas as pd

    pattern_prefixes = ["10a_", "10d_", "10e_", "10f_", "10g_"]
    frames = []

    for prefix in pattern_prefixes:
        rpt_path = DIR_10 / f"{prefix}report_numbers.csv"
        if rpt_path.exists():
            try:
                df = pd.read_csv(rpt_path)
                df['Source'] = prefix.rstrip('_')
                frames.append(df)
                print(f"  + {rpt_path.name} ({len(df)} rows)")
            except Exception as e:
                print(f"  [WARNING] Could not read {rpt_path.name}: {e}")

    # Also include the legacy report numbers if present
    legacy_path = DIR_10 / "10_cfell_report_numbers.csv"
    if legacy_path.exists():
        try:
            df = pd.read_csv(legacy_path)
            df['Source'] = '10_legacy'
            frames.append(df)
            print(f"  + {legacy_path.name} ({len(df)} rows, legacy)")
        except Exception:
            pass

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        out_path = DIR_10 / "10_consolidated_report_numbers.csv"
        combined.to_csv(out_path, index=False)
        print(f"\n  -> Consolidated: {out_path.name} ({len(combined)} rows)")
    else:
        print("  No report numbers found to consolidate.")


def main():
    parser = argparse.ArgumentParser(
        description="Run the Script 10 clearfell analysis suite")
    parser.add_argument("--only", type=str, metavar="ID",
                        help="Run only one sub-script (e.g. 10a, 10d)")
    parser.add_argument("--from", dest="from_id", type=str, metavar="ID",
                        help="Resume from a sub-script (e.g. 10d)")
    parser.add_argument("--skip-consolidate", action="store_true",
                        help="Skip report number consolidation")
    args = parser.parse_args()

    print()
    _hr("═")
    print("  SCRIPT 10 — CLEARFELL BACI ANALYSIS SUITE")
    _hr("═")
    print()

    # Determine which sub-scripts to run
    if args.only:
        targets = [(s, sid, d) for s, sid, d in SUBSCRIPTS
                   if sid == args.only.lower()]
        if not targets:
            print(f"  [ERROR] Unknown sub-script ID: {args.only}")
            print(f"  Valid IDs: {', '.join(sid for _, sid, _ in SUBSCRIPTS)}")
            sys.exit(1)
    elif args.from_id:
        found = False
        targets = []
        for s, sid, d in SUBSCRIPTS:
            if sid == args.from_id.lower():
                found = True
            if found:
                targets.append((s, sid, d))
        if not targets:
            print(f"  [ERROR] Unknown sub-script ID: {args.from_id}")
            sys.exit(1)
    else:
        targets = list(SUBSCRIPTS)

    # Print plan
    print(f"  Running {len(targets)} sub-script(s):")
    for _, sid, desc in targets:
        script_path = SRC_DIR / f"{sid}_{desc.split()[0].lower()}"
        status = "ready" if (SRC_DIR / [s for s, i, _ in SUBSCRIPTS if i == sid][0]).exists() else "NOT FOUND"
        print(f"    {sid}  {desc}  [{status}]")
    print()

    # Run
    DIR_10.mkdir(parents=True, exist_ok=True)
    failed = []
    for script_name, sid, desc in targets:
        ok = run_subscript(script_name, sid, desc)
        if not ok:
            failed.append(sid)
            # 10b and 10c are independent — continue even if 10a fails
            # But if 10a fails, downstream scripts that read its output
            # will handle missing files gracefully
            print(f"  Continuing despite {sid} failure...\n")

    # Consolidate report numbers
    if not args.skip_consolidate:
        print()
        _hr()
        print("  Consolidating report numbers...")
        _hr()
        try:
            consolidate_report_numbers()
        except Exception as e:
            print(f"  [WARNING] Consolidation failed: {e}")

    # Summary
    print()
    _hr("═")
    n_ok = len(targets) - len(failed)
    if failed:
        print(f"  SCRIPT 10 COMPLETE — {n_ok}/{len(targets)} sub-scripts succeeded")
        print(f"  Failed: {', '.join(failed)}")
    else:
        print(f"  SCRIPT 10 COMPLETE — all {n_ok} sub-scripts succeeded")
    _hr("═")
    print()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
