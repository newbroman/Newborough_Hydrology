"""
run_10_clearfell.py — Clearfell BACI Analysis Suite Runner
Runs the modular Script 10 sub-scripts (10a–10m) in order and
consolidates report numbers.

Usage
-----
  Called by run_analysis.py as a single pipeline step, or directly:
    python src/run_10_clearfell.py            # run all sub-scripts
    python src/run_10_clearfell.py --only 10a # run one sub-script
    python src/run_10_clearfell.py --from 10d # resume from a sub-script

Execution order
---------------
Prerequisite (must run first; produces the CEH34 hindcast CSV that
10a/10b/10e/10h consume via clearfell_common.apply_ceh34_hindcast):
  10i  CEH34 donor-regression hindcast (CEH9 donor)

Main (primary report results):
  10a  Three-counterfactual ANCOVA-BACI (primary result)
  10b  Spatial step-change maps
  10d  Summer minima analysis (dual control)
  10e  SSM coefficient decomposition
  10f  Robustness analyses (SSM residual, synthetic control)
  10g  Diagnostics (NW10 trend, transect, rolling coefficients)
  10h  Synthetic FE well extension BACI (donor regression)
  10j  Direct Impact-vs-Edge contrast (no external control)
  10k  Four-zone pooled-panel BACI (primary §4.6 result)
  10l  Four-zone summer-minima BACI (Phase 2 — annual Jun-Sep)

Display figure (runs last; not a primary report result):
  10m  WMC3-vs-forest-control dual-panel intervention figure

Supplementary (additional spatial diagnostic, not in the main report
results chain):
  10c  Forest zone spatial analysis

The supplementary sub-script runs in pipeline order but its outputs are
treated as supplementary material rather than primary findings.

Dependencies
------------
  10i is a prerequisite for 10a, 10b, 10e, 10h (CEH34 hindcast).
       10d and 10f intentionally do not consume the hindcast.
       10j does not consume the hindcast.
  10b and 10c read from Script 03 outputs (independent of 10a).
  10d and 10e are independent of 10a. (Script 10e no longer consumes
  10a report numbers — the predicted-vs-observed comparison was
  removed in 10e v1.4.0; 10e is now a coefficient-shift direction
  diagnostic.)
  10f reads 10a outputs for the ANCOVA comparison.
  10g is standalone diagnostics.
  10h reads 10a outputs for the FE-well synthetic-extension corroboration.
  10j reads 10d's summer-minima output for the annual-resolution contrast.
  10k is a standalone pooled-panel fit; it does not consume the hindcast.
       It optionally reads 10j's monthly-contrast output for a built-in
       cross-check (the four-zone Impact-Edge contrast should reproduce
       10j's two-zone estimate); the cross-check is skipped gracefully if
       10j has not run.
  10l reads 10d's summer-minima output (10d_01) for the Forest/Edge/
       Impact zones and computes the C3/Warren zone's summer minima
       itself.  It optionally reads 10j's summer-contrast output for a
       cross-check.  10d is therefore a prerequisite for 10l.
  10m reads 10a's report numbers (10a_report_numbers.csv) for the
       climate-corrected clearfell headline used in its on-figure
       reconciliation note; 10a is therefore a prerequisite for 10m.
       It is a display figure and runs last in the suite.
"""

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-12
#
# This module previously carried no __version__ constant; 1.0.0 marks its
# introduction, not the start of the module's history. Prior revisions are the
# dated notes and changelog entries elsewhere in the repository.


import subprocess
import sys
import argparse
from pathlib import Path

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)

# ── Paths ────────────────────────────────────────────────────────────────────
_THIS_DIR = Path(__file__).resolve().parent
ROOT_DIR = _THIS_DIR.parent if _THIS_DIR.name == "src" else _THIS_DIR
SRC_DIR  = ROOT_DIR / "src"
OUT_DIR  = ROOT_DIR / "outputs"
DIR_10   = OUT_DIR / "10_clearfell_baci"

# ── Sub-script definitions ───────────────────────────────────────────────────
# (script_filename, short_id, description)
# 10i runs FIRST as a prerequisite for 10a/10b/10e/10h (CEH34 hindcast).
SUBSCRIPTS = [
    ("10i_ceh34_hindcast.py",            "10i", "CEH34 donor-regression hindcast (CEH9 donor) — prerequisite"),
    ("10a_ancova_baci.py",               "10a", "Three-counterfactual ANCOVA-BACI (primary)"),
    ("10b_spatial_step_maps.py",         "10b", "Spatial step-change maps"),
    ("10c_forest_zone_analysis.py",      "10c", "Forest zone spatial analysis (supplementary)"),
    ("10d_summer_minima.py",             "10d", "Summer minima (dual control)"),
    ("10e_coefficient_decomposition.py", "10e", "SSM coefficient decomposition"),
    ("10f_robustness.py",               "10f", "Robustness analyses"),
    ("10g_diagnostics.py",              "10g", "Diagnostics"),
    ("10h_synthetic_impact_baci.py",    "10h", "Synthetic FE well extension BACI"),
    ("10j_impact_edge_contrast.py",     "10j", "Direct Impact-vs-Edge contrast (monthly + summer)"),
    ("10k_four_zone_baci.py",           "10k", "Four-zone pooled-panel BACI (primary §4.6 result)"),
    ("10l_four_zone_summer_minima.py",  "10l", "Four-zone summer-minima BACI (Phase 2)"),
    ("10m_wmc3_baci_dual.py",           "10m", "WMC3-vs-forest-control dual-panel intervention figure (display)"),
    # 10n must follow 10f: it reads 10f's donor pool from that module so the
    # two cannot drift, and its whole purpose is to normalise 10f's gross
    # synthetic-control step against unfelled forest.
    ("10n_synthetic_did.py",            "10n", "Forest-normalised synthetic control (difference-in-differences)"),
]




def run_subscript(script_name, label, description):
    """Run a single sub-script via subprocess."""
    script_path = SRC_DIR / script_name
    if not script_path.exists():
        skipped(f"{script_name} — not found")
        return False
    hr()
    print(f"  {label}  {description}")
    print(f"  Script: {script_path.name}")
    hr()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT_DIR),
    )
    if result.returncode != 0:
        error(f"\n  [ERROR] {script_name} exited with code {result.returncode}")
        return False
    return True


def consolidate_report_numbers():
    """Merge per-sub-script report numbers into a single CSV.

    Includes report numbers from sub-scripts that produce a `*_report_numbers.csv`
    summary table.  10b emits a per-well spatial CSV (not a citable-values table)
    and 10c is supplementary, so neither is included in the consolidation.
    10i emits citable values for the CEH34 hindcast (donor identity, fit r²/RMSE,
    prediction interval) which belong in the consolidated report numbers table.
    """
    import pandas as pd

    pattern_prefixes = ["10a_", "10d_", "10e_", "10f_", "10g_", "10h_", "10i_",
                        "10k_", "10l_", "10m_", "10n_"]
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
                warn(f"Could not read {rpt_path.name}: {e}")

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
        skipped("No report numbers found to consolidate.")


def main():
    banner("10", "Clearfell Pipeline Orchestrator", version=__version__)
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
    hr("═")
    print("  SCRIPT 10 — CLEARFELL BACI ANALYSIS SUITE")
    hr("═")
    print()

    # Determine which sub-scripts to run
    if args.only:
        targets = [(s, sid, d) for s, sid, d in SUBSCRIPTS
                   if sid == args.only.lower()]
        if not targets:
            error(f"Unknown sub-script ID: {args.only}")
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
            error(f"Unknown sub-script ID: {args.from_id}")
            sys.exit(1)
    else:
        targets = list(SUBSCRIPTS)

    # Print plan
    print(f"  Running {len(targets)} sub-script(s):")
    for script_name, sid, desc in targets:
        status = "ready" if (SRC_DIR / script_name).exists() else "NOT FOUND"
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
        hr()
        print("  Consolidating report numbers...")
        hr()
        try:
            consolidate_report_numbers()
        except Exception as e:
            warn(f"Consolidation failed: {e}")

    # Summary
    print()
    hr("═")
    n_ok = len(targets) - len(failed)
    if failed:
        print(f"  SCRIPT 10 COMPLETE — {n_ok}/{len(targets)} sub-scripts succeeded")
        print(f"  Failed: {', '.join(failed)}")
    else:
        print(f"  SCRIPT 10 COMPLETE — all {n_ok} sub-scripts succeeded")
    hr("═")
    print()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
