"""
====================================================================================
run_09_scraping.py — SCRAPING ANALYSIS SUITE RUNNER
====================================================================================
Orchestrates the full scraping analysis:

  09a   Hierarchical paired BACI (core analysis, β₃ testing, tier figures)
  09b   CEH36 robustness (raw BACI, synthetic control, SSM residual)
  09bp  Scraping propagation (split-window SSM, centroid summaries)
  09c   Summer minima (dual-control BACI, ecological threshold analysis)
  09d   Scenario comparison (monthly equilibrium + summer minimum bars)

09bp must run before 09d because 09d reads 09b_02_centroid_summaries.csv.

Usage
-----
Run all:   python run_09_scraping.py
Selective: python run_09_scraping.py --only 09a 09c
====================================================================================
"""

import sys
import importlib
import argparse

# Ordered dict — execution order matters (09bp before 09d)
MODULES = {
    "09a":  "09a_paired_baci",
    "09b":  "09b_robustness",
    "09bp": "09b_scraping_propagation",
    "09c":  "09c_summer_minima",
    "09d":  "09d_scenario_comparison",
}


def main():
    parser = argparse.ArgumentParser(
        description="Run the Script 09 scraping analysis suite")
    parser.add_argument("--only", nargs="+", choices=list(MODULES.keys()),
                        help="Run only specified modules")
    args = parser.parse_args()

    to_run = args.only if args.only else list(MODULES.keys())

    # Enforce dependency: if 09d is requested, 09bp must run first
    if "09d" in to_run and "09bp" not in to_run:
        idx = to_run.index("09d")
        to_run.insert(idx, "09bp")
        print("  [NOTE] Added 09bp (propagation) — required by 09d")

    print("=" * 72)
    print("SCRAPING ANALYSIS SUITE")
    print(f"Modules: {', '.join(to_run)}")
    print("=" * 72)

    for key in to_run:
        mod_name = MODULES[key]
        print(f"\n{'─' * 72}")
        print(f"Running {key}: {mod_name}")
        print(f"{'─' * 72}")
        try:
            mod = importlib.import_module(mod_name)
            mod.main()
        except Exception as e:
            print(f"  [ERROR] {mod_name} failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 72)
    print("SCRAPING ANALYSIS SUITE COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
