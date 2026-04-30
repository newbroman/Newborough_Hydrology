"""
run_analysis.py — Newborough Warren Groundwater Analysis Pipeline
Interactive orchestrator for the Hollingham (2026) analytical pipeline.

Usage
-----
  python run_analysis.py              # interactive menu
  python run_analysis.py --full       # non-interactive: run all 28 steps
  python run_analysis.py --from N     # non-interactive: resume from step N
  python run_analysis.py --viewer     # non-interactive: build scenario viewer only
"""

import subprocess
import sys
import textwrap
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR  = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
OUT_DIR  = ROOT_DIR / "outputs"

# ── Phase / step definitions ──────────────────────────────────────────────────

PHASE_1 = [
    ("01_data_prep.py",              " 1/28  Data preparation"),
    ("02_clustering.py",             " 2/28  Behavioural clustering"),
    ("03_state_space_model.py",      " 3/28  State-space regression + LCSC"),
    ("04_cluster_visualisations.py", " 4/28  Core cluster visualisation"),
]
PHASE_2 = [
    ("05_pearson_affinity.py",  " 5/28  Pearson membership audit"),
    ("06_pearson_extended.py",  " 6/28  Pearson extended network integration"),
]
PHASE_3 = [
    ("07_spatial_coefficients.py",     " 7/28  Spatial coefficient mapping"),
    ("08_model_benchmarking.py",      " 8/28  Model benchmarking (LCSC vs Traditional)"),
    ("09_scraping_intervention.py",   " 9/28  Scraping intervention BACI"),
    ("10_clearfell_baci.py",          "10/28  Clear-fell BACI analysis"),
    ("10b_spatial_step_maps.py",       "11/28  Spatial step-change maps (scraping + clearfell)"),
    ("11_forecasting_thresholds.py",  "12/28  Forecasting and critical thresholds"),
    ("11b_spatial_thresholds.py",     "13/28  Spatial eco-hydrological threshold maps"),
]
PHASE_4 = [
    ("00_climate_summary.py",            "14/28  Climate summary outputs", ["--profile", "full"]),
    ("14_climate_projections.py",        "15/28  Figure: Climate trajectory projections"),
    ("12_figure_site_overview.py",       "16/28  Figure: DEM site overview"),
    ("13_figure_experimental_design.py", "17/28  Figure: Experimental design GIS map"),
]
PHASE_5 = [
    ("15_depth_dependent_pet.py", "18/28  Depth-dependent PET analysis"),
]
PHASE_6 = [
    ("17_wtf_specific_yield.py", "19/28  WTF cluster Sy estimation"),
]
PHASE_7 = [
    ("16_water_bal.py", "20/28  Water balance decomposition"),
]
PHASE_8 = [
    ("18_wtf_spatial.py", "21/28  WTF spatial analysis and Sy mapping"),
]
PHASE_9 = [
    ("19_spatial_groundwater.py", "22/28  Spatial groundwater analysis"),
    ("20_spatial_figures.py",     "23/28  Spatial paper figures"),
]
PHASE_10 = [
    ("21_forestry_scenarios.py", "24/28  Forestry scenarios and management figures"),
]
PHASE_11 = [
    ("22_residual_lag_analysis.py",    "25/28  Residual lag structure analysis"),
    ("23_ridge_recharge_lag_test.py",  "26/28  Ridge recharge lag hypothesis test"),
    ("24_residual_seasonality.py",     "27/28  Residual seasonality diagnostics"),
    ("25_forest_zone_analysis.py",     "28/28  Forest zone spatial analysis"),
]

ALL_PHASES = [
    ("PHASE 1  — Core LCSC Chain",                              PHASE_1),
    ("PHASE 2  — Pearson Membership Audit",                     PHASE_2),
    ("PHASE 3  — Model Diagnostics and Intervention Analysis",  PHASE_3),
    ("PHASE 4  — Climate Projections and Figure Generation",    PHASE_4),
    ("PHASE 5  — Depth-Dependent PET Analysis",                 PHASE_5),
    ("PHASE 6  — WTF Cluster Sy Estimation",                    PHASE_6),
    ("PHASE 7  — Water Balance Decomposition",                  PHASE_7),
    ("PHASE 8  — WTF Spatial Analysis and Sy Mapping",          PHASE_8),
    ("PHASE 9  — Spatial Groundwater Analysis",                 PHASE_9),
    ("PHASE 10 — Forestry Scenario Analysis",                   PHASE_10),
    ("PHASE 11 — Supplementary Diagnostics (Scripts 22–25)",   PHASE_11),
]

# Build step -> (script, label, extra_args) lookup at import time
_STEP_MAP: dict[int, tuple[str, str, list]] = {}
for _phase_label, _phase_entries in ALL_PHASES:
    for _entry in _phase_entries:
        _script, _label = _entry[0], _entry[1]
        _extra = list(_entry[2]) if len(_entry) > 2 else []
        try:
            _step = int(_label.strip().split("/")[0])
        except (ValueError, IndexError):
            continue
        _STEP_MAP[_step] = (_script, _label, _extra)

# ── Validation checkpoints ────────────────────────────────────────────────────

REQUIRED_DATA = [
    "Newborough_Cleaned_For_Model.csv",
    "RAF_Valley_Climate.csv",
    "Well_locations_height.csv",
]
REQUIRED_PHASE1_OUTPUTS = [
    "01_wells_reference.csv",
    "01_wells_extended.csv",
    "02_cluster_stats.csv",
]
REQUIRED_PHASE3_OUTPUTS = [
    "03_master_data.csv",
    "10_clearfell_baci/10_cfell_07_coefficient_slopes.csv",
]
REQUIRED_PHASE9_OUTPUTS = [
    "19_spatial_groundwater/scenario_viewer.html",
    "19_spatial_groundwater/19_scenario_summary.csv",
]
REQUIRED_PHASE10_OUTPUTS = [
    "21_forestry_scenarios/21_forestry_01_hydrograph.png",
    "21_forestry_scenarios/21_forestry_02_distributions.png",
    "21_forestry_scenarios/21_forestry_03_scraping_eras.png",
    "21_forestry_scenarios/21_forestry_04_baci_zone_violin.png",
]

# ── Upstream dependency map ──────────────────────────────────────────────────
# Each entry: (step_threshold, required_files, phase_label)
# If the user selects a step >= step_threshold and any required_files are
# missing, a warning is printed before proceeding. This catches the most
# common case: running a mid-pipeline script before the upstream phases
# have produced the intermediate CSVs it needs.

_UPSTREAM_DEPS = [
    (5,  REQUIRED_PHASE1_OUTPUTS,  "Phase 1 (steps 1–4)"),
    (13, REQUIRED_PHASE3_OUTPUTS,  "Phase 3 (steps 7–12)"),
]

# Core intermediate: 01_climate.csv is needed by almost every script from
# step 2 onwards. It's the single most common import-time failure when
# running a script before the pipeline has run at all.
_CORE_INTERMEDIATES = [
    "01_climate.csv",
    "01_wells_clean.csv",
]

# Viewer is now generated directly by script 19 — no separate runner needed.
# Kept as a separate menu option to allow rebuilding the viewer without
# re-running the full pipeline (useful after parameter changes in script 19).
VIEWER_SCRIPT = "19_spatial_groundwater.py"
VIEWER_OUTPUT = OUT_DIR / "19_spatial_groundwater" / "scenario_viewer.html"

# ── Low-level helpers ─────────────────────────────────────────────────────────

def _hr(char="─", width=70):
    print(char * width)

def _banner(title: str):
    _hr("═")
    print(f"  {title}")
    _hr("═")

def ensure_paths() -> None:
    if not SRC_DIR.exists():
        raise FileNotFoundError(f"Missing src/ directory: {SRC_DIR}")
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Missing data/ directory: {DATA_DIR}")
    OUT_DIR.mkdir(exist_ok=True)
    missing = [n for n in REQUIRED_DATA if not (DATA_DIR / n).exists()]
    if missing:
        raise FileNotFoundError("Missing required data files: " + ", ".join(missing))

def run_script(script_name: str, label: str, extra_args: list = None) -> None:
    script_path = SRC_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    _hr()
    print(f"  STEP {label.strip()}")
    print(f"  Script: {script_path.name}")
    _hr()
    cmd = [sys.executable, str(script_path)] + (extra_args or [])
    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)

def validate_outputs(required: list, phase_name: str) -> None:
    missing = [n for n in required if not (OUT_DIR / n).exists()]
    if missing:
        raise FileNotFoundError(f"{phase_name} outputs missing: " + ", ".join(missing))
    print(f"\n  [OK] {phase_name} validation passed.")


def warn_missing_upstream(step: int, interactive: bool = True) -> bool:
    """Check for upstream intermediate files and warn if missing.

    Parameters
    ----------
    step : int
        The pipeline step number to check dependencies for.
    interactive : bool
        If True (menu mode), prompt the user to confirm. If False (CLI
        mode), print the warning and return True (proceed with warning).

    Returns True if the user confirms they want to proceed despite warnings,
    or if no warnings are needed. Returns False if the user aborts.
    """
    warnings = []

    # Core intermediates — needed by almost every script from step 2 onwards
    if step >= 2:
        missing_core = [f for f in _CORE_INTERMEDIATES if not (OUT_DIR / f).exists()]
        if missing_core:
            warnings.append(
                f"  Core pipeline intermediates not found:\n"
                f"    {', '.join(missing_core)}\n"
                f"  These are produced by step 1 (01_data_prep.py) and are\n"
                f"  required by nearly every downstream script."
            )

    # Phase-level dependencies
    for threshold, required, phase_label in _UPSTREAM_DEPS:
        if step >= threshold:
            missing = [f for f in required if not (OUT_DIR / f).exists()]
            if missing:
                warnings.append(
                    f"  {phase_label} outputs not found:\n"
                    f"    {', '.join(missing)}"
                )

    if not warnings:
        return True

    _hr("!")
    print("  WARNING: Upstream pipeline outputs are missing.\n")
    for w in warnings:
        print(w)
    print()
    print("  This step may fail if it depends on these files.")
    print("  If this is your first run, use option 1 (full pipeline) or")
    print("  option 2 (resume from step 1) to generate all intermediates.")
    _hr("!")

    if not interactive:
        # CLI mode: warn but proceed
        print("  (Proceeding — use --full for a clean run if this fails.)\n")
        return True

    ans = input("\n  Proceed anyway? [y/N] ").strip().lower()
    return ans == "y"

def run_phase(phase: list, phase_name: str, from_step: int = 1) -> None:
    print(f"\n{'─'*70}\n  {phase_name}\n{'─'*70}")
    for entry in phase:
        script_name, label = entry[0], entry[1]
        extra_args = entry[2] if len(entry) > 2 else None
        try:
            step_num = int(label.strip().split("/")[0])
        except (ValueError, IndexError):
            step_num = 0
        if step_num < from_step:
            print(f"  [SKIP] Step {label.strip()}")
            continue
        run_script(script_name, label, extra_args)

# ── Pipeline runners ──────────────────────────────────────────────────────────

def run_full_pipeline(from_step: int = 1) -> None:
    ensure_paths()
    run_phase(PHASE_1,  "PHASE 1  — Core LCSC Chain",                             from_step)
    if from_step <= 4:
        validate_outputs(REQUIRED_PHASE1_OUTPUTS, "Phase 1")
    run_phase(PHASE_2,  "PHASE 2  — Pearson Membership Audit",                    from_step)
    run_phase(PHASE_3,  "PHASE 3  — Model Diagnostics and Intervention Analysis", from_step)
    if from_step <= 12:
        validate_outputs(REQUIRED_PHASE3_OUTPUTS, "Phase 3")
    run_phase(PHASE_4,  "PHASE 4  — Climate Projections and Figure Generation",   from_step)
    run_phase(PHASE_5,  "PHASE 5  — Depth-Dependent PET Analysis",                from_step)
    run_phase(PHASE_6,  "PHASE 6  — WTF Cluster Sy Estimation",                   from_step)
    run_phase(PHASE_7,  "PHASE 7  — Water Balance Decomposition",                 from_step)
    run_phase(PHASE_8,  "PHASE 8  — WTF Spatial Analysis and Sy Mapping",         from_step)
    run_phase(PHASE_9,  "PHASE 9  — Spatial Groundwater Analysis",                from_step)
    if from_step <= 22:
        validate_outputs(REQUIRED_PHASE9_OUTPUTS, "Phase 9")
    run_phase(PHASE_10, "PHASE 10 — Forestry Scenario Analysis",                  from_step)
    validate_outputs(REQUIRED_PHASE10_OUTPUTS, "Phase 10")
    run_phase(PHASE_11, "PHASE 11 — Supplementary Diagnostics (Scripts 22–25)",  from_step)
    _banner("PIPELINE COMPLETE — all 28 steps written to outputs/")

def build_viewer() -> None:
    """Run script 19 to generate the self-contained scenario viewer HTML."""
    print()
    _hr()
    print("  Hydrological Scenario Viewer")
    _hr()
    print()

    script_path = SRC_DIR / VIEWER_SCRIPT
    status = "found" if script_path.exists() else "NOT FOUND"
    print(f"  This will run: {VIEWER_SCRIPT}  [{status}]")
    print()

    if not script_path.exists():
        print(f"  [ERROR] Script not found: {script_path}")
        return

    print(f"  Running {VIEWER_SCRIPT} ...")
    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT_DIR), check=True,
    )

    if VIEWER_OUTPUT.exists():
        size_kb = VIEWER_OUTPUT.stat().st_size / 1024
        print(f"\n  [OK] Viewer ready: {VIEWER_OUTPUT}")
        print(f"       File size: {size_kb:.1f} KB")
        print("       Open in any browser — no server required.")
    else:
        print(f"\n  [!] Viewer not found at expected path: {VIEWER_OUTPUT}")

# ── Interactive menu ──────────────────────────────────────────────────────────

INTRO = """\
  97-well dipwell network · Newborough Warren NNR (Isle of Anglesey SAC)
  Monitoring period 2005–2026 · State Space Model with β₁/β₂/β₃ coefficients
  Five hydrogeological clusters (C1–C5) · Ward's linkage hierarchical clustering
  Hollingham (2026) · Journal of Hydrology: Regional Studies
"""

MENU = """
  ┌──────────────────────────────────────────────────┐
  │  Main Menu                                       │
  ├──────────────────────────────────────────────────┤
  │  1  Run full pipeline  (all 28 steps)            │
  │  2  Resume from a specific step                  │
  │  3  Run a single step                            │
  │  4  Prepare the scenario viewer                  │
  │  5  Run supplementary diagnostics (22–25)        │
  │  6  Show pipeline step list                      │
  │  q  Quit                                         │
  └──────────────────────────────────────────────────┘"""

def show_step_list() -> None:
    print()
    _hr()
    print("  Pipeline Step List")
    _hr()
    for phase_label, phase_entries in ALL_PHASES:
        print(f"\n  {phase_label}")
        for entry in phase_entries:
            script, label = entry[0], entry[1]
            try:
                step = int(label.strip().split("/")[0])
            except (ValueError, IndexError):
                step = 0
            found = "OK" if (SRC_DIR / script).exists() else "!!"
            print(f"    [{found}] Step {step:>2}  {script}")
    print()

def _prompt_step(prompt: str) -> int | None:
    show_step_list()
    raw = input(f"  {prompt}: ").strip()
    try:
        n = int(raw)
    except ValueError:
        print("  Invalid input — returning to menu.")
        return None
    if n not in _STEP_MAP:
        print(f"  Step {n} not recognised — returning to menu.")
        return None
    return n

def menu_run_from() -> None:
    n = _prompt_step("Enter step number to resume from")
    if n is None:
        return
    script, label, _ = _STEP_MAP[n]
    print(f"\n  Resume from step {n}: {script}")
    if not warn_missing_upstream(n):
        print("  Aborted.")
        return
    ans = input("  Confirm? [y/N] ").strip().lower()
    if ans == "y":
        run_full_pipeline(from_step=n)

def menu_run_single() -> None:
    n = _prompt_step("Enter step number to run")
    if n is None:
        return
    script, label, extra = _STEP_MAP[n]
    print(f"\n  Run step {n}: {script}")
    if not warn_missing_upstream(n):
        print("  Aborted.")
        return
    ans = input("  Confirm? [y/N] ").strip().lower()
    if ans == "y":
        ensure_paths()
        run_script(script, label, extra)
        print(f"\n  [OK] Step {n} complete.")

def run_supplementary() -> None:
    """Run supplementary diagnostic scripts 22–25."""
    ensure_paths()
    if not warn_missing_upstream(24):
        print("  Aborted.")
        return
    run_phase(PHASE_11, "PHASE 11 — Supplementary Diagnostics (Scripts 22–25)")
    print("\n  [OK] Supplementary diagnostics complete.")

def interactive_menu() -> None:
    _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
    print()
    print(INTRO)

    while True:
        print(MENU)
        choice = input("\n  Enter choice: ").strip().lower()

        if choice == "1":
            ans = input("\n  Run all 28 steps from the beginning? [y/N] ").strip().lower()
            if ans == "y":
                run_full_pipeline(from_step=1)

        elif choice == "2":
            menu_run_from()

        elif choice == "3":
            menu_run_single()

        elif choice == "4":
            build_viewer()

        elif choice == "5":
            run_supplementary()

        elif choice == "6":
            show_step_list()

        elif choice in ("q", "quit", "exit"):
            print("\n  Exiting.\n")
            break

        else:
            print("  Unrecognised option.")

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Newborough Warren analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Run without arguments for the interactive menu.
            Use --full, --from, --viewer, or --supplementary for non-interactive execution.
        """)
    )
    parser.add_argument("--full",   action="store_true",
                        help="Run all 28 steps non-interactively")
    parser.add_argument("--from",   dest="from_step", type=int, metavar="N",
                        help="Resume from step N non-interactively")
    parser.add_argument("--viewer", action="store_true",
                        help="Build the scenario viewer only")
    parser.add_argument("--supplementary", action="store_true",
                        help="Run supplementary diagnostics (scripts 22–25) only")
    args = parser.parse_args()

    try:
        if args.viewer:
            build_viewer()
        elif args.supplementary:
            _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
            run_supplementary()
        elif args.full:
            _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
            run_full_pipeline(from_step=1)
        elif args.from_step is not None:
            _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
            warn_missing_upstream(args.from_step, interactive=False)
            run_full_pipeline(from_step=args.from_step)
        else:
            interactive_menu()
    except KeyboardInterrupt:
        print("\n\n  Interrupted.\n")
        sys.exit(0)
    except Exception as exc:
        print(f"\n  [ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
