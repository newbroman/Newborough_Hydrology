"""
run_analysis.py — Newborough Warren Groundwater Analysis Pipeline
Interactive orchestrator for the Hollingham (2026) analytical pipeline.

Usage
-----
  python run_analysis.py              # interactive menu
  python run_analysis.py --full       # non-interactive: run all 46 steps
  python run_analysis.py --full --with-supplementary  # ... plus Phase 16 (24b,31,31b,34)
  python run_analysis.py --full --clusters 5          # set the clustering target K (default 5)
  python run_analysis.py --full --log # ... and record all console output to a log file
  python run_analysis.py --from N     # non-interactive: resume from step N
  python run_analysis.py --viewer     # non-interactive: build scenario viewer only
  python run_analysis.py --greyscale  # non-interactive: convert figures to B&W
  python run_analysis.py --explain     # print the in-app help page and exit
  python run_analysis.py --deps        # print the down-pipeline dependency audit and exit
  python run_analysis.py --no-colour   # disable coloured output

Pipeline structure
------------------
The pipeline comprises 46 steps across 17 phases:

  Phases 1–11 produce the main analytical results documented in the report.
  Phase 12 runs supplementary diagnostics (Scripts 22–24); Phase 16 runs further
  standalone diagnostics (Scripts 24b, 31, 31b, 34) before greyscale conversion.
  Phase 13 runs the van Willegen et al. (2025) MSL analyses — observational
  5-year MSL aggregation (Script 26), UKCP18 RCP8.5 climate projections
  (Script 26b), and report-format figures (Script 26c, for §4.8.4 and
  §4.10.1) — paired tools documented in §3.7.5 of the report.
  Phase 14 runs the post-review cluster framework diagnostics — the C3
  detrend check (Script 28, validating the aquifer-architecture framing
  of §5.1) and the within-C3 variance attribution (Script 29, characterising
  the spatial structure within C3) and the C4 constrained-β₃ triangulation
  sensitivity (Script 30, recovering a physically admissible forest drainage
  coefficient where the unconstrained monthly fit is degenerate) — documented
  in §5.1.1 and §4.2.2 of the report and §S.19 of the Methods Supplement.
  Phase 16 runs the supplementary standalone diagnostics (Scripts 24b, 31,
  31b, 34); it is opt-in on a full run (--with-supplementary, or the menu
  option 1 prompt). Phase 17 runs the greyscale figure-conversion utility
  (Script 27), retained as a callable utility step rather than an analytical
  phase, and runs separately (menu option 6 / --greyscale).

Two-pass execution (RECOMMENDED for new datasets)
-------------------------------------------------
Two scripts in Phase 3 use Specific-Yield (Sy) values that are produced
later in the pipeline (Phase 6 / Phase 8):

    09b_scraping_propagation     reads OUT_17_SY_TABLE  (produced step 18)
    09d_scenario_comparison      reads INT_WTF_WELL_SY  (produced step 20)

On a fresh first-pass full-pipeline run those files do not yet exist,
and Phase 3 falls back to documented Newborough-2026 Sy defaults
(0.20 cluster, 0.30 CEH36) with console warnings. The scientific
analyses themselves are unaffected — these scripts use Sy only for a
volumetric scenario-comparison conversion in their figures.

Script 09f (Phase 17, a display/utility synthesis figure) similarly reads
outputs produced earlier in the SAME pass — Scripts 20 (step 24), 25
(step 26), 09d (step 9) and 10a (step 10). It runs last, so on a normal
full run all of these already exist; only on a partial or interrupted run
does it fall back to documented defaults (centralised in
pipeline_params._DEFAULTS, read via default_value()) with warnings. The
figure it produces re-presents existing modelled fields and adds no new
analysis, so first-pass defaults do not affect any analytical result.

For the most accurate scenario figures on a NEW dataset:

    1. python run_analysis.py --full          # first pass
    2. python run_analysis.py --from 9        # second pass — re-run 09b/09d
                                              # with canonical Sy from 17/18

Or accept the documented fallbacks for the first pass (recommended for
the Newborough dataset where the fallbacks are tuned).
"""

import subprocess
import sys
import textwrap
import datetime
import os
import re
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR  = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
OUT_DIR  = ROOT_DIR / "outputs"

# ── Console styling (ANSI colour, auto-detected) ──────────────────────────────
# Colour is enabled only when stdout is a real terminal and not disabled via
# the NO_COLOR env var or --no-colour. When output is piped or logged, colour
# is suppressed; the log file is additionally stripped of any escape codes
# (see _AnsiStripper) so logs stay clean even if a child script emits colour.


class _Ansi:
    RESET = "\x1b[0m"; BOLD = "\x1b[1m"; DIM = "\x1b[2m"
    RED = "\x1b[31m"; GREEN = "\x1b[32m"; YELLOW = "\x1b[33m"
    BLUE = "\x1b[34m"; MAGENTA = "\x1b[35m"; CYAN = "\x1b[36m"; GREY = "\x1b[90m"
    BRED = "\x1b[91m"; BGREEN = "\x1b[92m"; BYELLOW = "\x1b[93m"
    BBLUE = "\x1b[94m"; BCYAN = "\x1b[96m"


# Status glyphs (unicode; the pipeline already relies on a UTF-8 console)
GLYPH_OK   = "\u2713"   # ✓
GLYPH_FAIL = "\u2717"   # ✗
GLYPH_RUN  = "\u25b6"   # ▶
GLYPH_WARN = "\u26a0"   # ⚠
GLYPH_INFO = "\u2139"   # ℹ
GLYPH_SKIP = "\u2014"   # —


def _enable_windows_ansi() -> bool:
    """Enable ANSI escape processing on Windows 10+ consoles. No-op elsewhere."""
    if os.name != "nt":
        return True
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not k.GetConsoleMode(h, ctypes.byref(mode)):
            return False
        k.SetConsoleMode(h, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return True
    except Exception:
        return False


def _detect_colour() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    try:
        if not sys.stdout.isatty():
            return False
    except Exception:
        return False
    return _enable_windows_ansi()


USE_COLOUR = _detect_colour()


def _init_colour(disable: bool = False) -> None:
    """Recompute colour support (called from main once CLI args are known)."""
    global USE_COLOUR
    USE_COLOUR = False if disable else _detect_colour()


def paint(text: str, *codes: str) -> str:
    """Wrap text in ANSI codes when colour is enabled, else return it plain."""
    if not USE_COLOUR or not codes:
        return text
    return "".join(codes) + text + _Ansi.RESET


def say_ok(msg: str) -> None:
    print("  " + paint(f"{GLYPH_OK} {msg}", _Ansi.GREEN))


def say_warn(msg: str) -> None:
    print("  " + paint(f"{GLYPH_WARN} {msg}", _Ansi.BYELLOW))


def say_err(msg: str) -> None:
    print("  " + paint(f"{GLYPH_FAIL} {msg}", _Ansi.BRED))


def say_info(msg: str) -> None:
    print("  " + paint(f"{GLYPH_INFO} {msg}", _Ansi.GREY))

# ── Phase / step definitions ──────────────────────────────────────────────────

PHASE_1 = [
    ("01_data_prep.py",              " 1/44  Data preparation"),
    ("02_clustering.py",             " 2/44  Behavioural clustering"),
    ("03_state_space_model.py",      " 3/44  State-space regression + LCSC"),
    ("04_cluster_visualisations.py", " 4/44  Core cluster visualisation"),
]
PHASE_2 = [
    ("05_pearson_affinity.py",  " 5/44  Pearson membership audit"),
    ("06_pearson_extended.py",  " 6/44  Pearson extended network integration"),
]
PHASE_3 = [
    ("07_spatial_coefficients.py",     " 7/44  Spatial coefficient mapping"),
    ("08_model_benchmarking.py",      " 8/44  Model benchmarking (LCSC vs Traditional)"),
    ("run_09_scraping.py",            " 9/44  Scraping analysis suite (09a–09e)"),
    ("run_10_clearfell.py",           "10/44  Clear-fell BACI analysis suite (10a–10m)"),
    ("11_forecasting_thresholds.py",  "11/44  Forecasting and critical thresholds"),
    ("11b_spatial_thresholds.py",     "12/44  Spatial eco-hydrological threshold maps"),
    ("11c_pflood_achievability.py",   "13/44  P_flood achievability categorical map (§5.9 / Conclusion 4)"),
]
PHASE_4 = [
    ("00_climate_summary.py",            "14/44  Climate summary outputs"),
    ("14_climate_projections.py",        "15/44  Figure: Climate trajectory projections"),
    ("14b_year_of_crossing.py",          "16/44  Bootstrap year-of-crossing for Curreli thresholds (§7 Conclusion 11)"),
    ("12_figure_site_overview.py",       "17/44  Figure: DEM site overview"),
    ("13_figure_experimental_design.py", "18/44  Figure: Experimental design GIS map"),
]
PHASE_5 = [
    ("15_depth_dependent_pet.py", "19/44  Depth-dependent PET analysis"),
]
PHASE_6 = [
    ("17_wtf_specific_yield.py", "20/44  WTF cluster Sy estimation"),
]
PHASE_7 = [
    ("16_water_bal.py", "21/44  Water balance decomposition"),
]
PHASE_8 = [
    ("18_wtf_spatial.py", "22/44  WTF spatial analysis and Sy mapping"),
]
PHASE_9 = [
    ("19_spatial_groundwater.py", "23/44  Spatial groundwater analysis"),
    ("20_spatial_figures.py",     "24/44  Spatial paper figures"),
]
PHASE_10 = [
    ("21_forestry_scenarios.py", "25/44  Forestry scenarios and management figures"),
]
PHASE_11 = [
    ("25_coastal_gradient.py",   "26/44  Coastal-retreat gradient analysis"),
]
PHASE_12 = [
    ("22_residual_lag_analysis.py",    "27/44  Residual lag structure analysis"),
    ("23_ridge_recharge_lag_test.py",  "28/44  Ridge recharge lag hypothesis test"),
    ("24_residual_seasonality.py",     "29/44  Residual seasonality diagnostics"),
]
PHASE_13 = [
    ("26_van_willegen_msl.py",             "30/44  Van Willegen (2025) 5-year MSL aggregation"),
    ("26b_van_willegen_msl_projections.py", "31/44  UKCP18 MSL5 climate projections (Tool B)"),
    ("26c_msl5_report_figures.py",          "32/44  MSL5 report-format figures (Figures for §4.8.4 / §4.10.1)"),
]
PHASE_14 = [
    ("28_c3_detrend_check.py",          "33/44  Cluster framework diagnostic: C3 detrend check (H0)"),
    ("29_c3_within_variance_check.py",  "34/44  Cluster framework diagnostic: within-C3 spatial structure"),
    ("30_c4_constrained_fit.py",         "35/44  Cluster framework diagnostic: C4 constrained-β₃ triangulation sensitivity"),
]
PHASE_15 = [
    ("32_differential_movement.py",    "36/46  Figure: secular differential water-table drift (report Fig 59)"),
    ("33_envelope_amplification.py",   "37/46  Figure: climate-swing amplification + drought-floor (report Fig 60)"),
    ("35_per_well_amplification.py",    "38/46  Figure+table: per-well climate-sensitivity coefficient (Paper 1; co-temporal, SSM-calibrated)"),
    ("36_absolute_climate_trend.py",    "39/46  Figure: absolute climate-removed per-well secular trend map (spring CWB detrended)"),
    ("37_driver_validation.py",         "40/46  Validation: predicted-vs-observed driver-change map (scatter + residual map)"),
]
PHASE_16 = [
    ("24b_residual_climatology.py",        "41/46  Cluster-stratified residual climatology (supplementary diagnostic)"),
    ("31_cluster_validation.py",           "42/46  Independent k=5 partition validation (supplementary diagnostic)"),
    ("31b_separation_vs_recoverability.py", "43/46  Cluster separation vs recoverability (supplementary diagnostic)"),
    ("34_window_sensitivity.py",           "44/46  MSL5 two-window sensitivity demonstration figure (\u00a75.7.5)"),
]
PHASE_17 = [
    ("09f_management_effects.py",     "45/46  Figure: management-interventions + coastal-retreat spatial reach (\u00a75.8; two-pass, reads Scripts 20/25/09d/10a)"),
    ("27_greyscale_figures.py",        "46/46  Greyscale figure conversion (journal-ready B&W)"),
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
    ("PHASE 11 \u2014 Coastal-Retreat Gradient Analysis (Script 25)", PHASE_11),
    ("PHASE 12 \u2014 Supplementary Diagnostics (Scripts 22\u201324)",   PHASE_12),
    ("PHASE 13 \u2014 Van Willegen MSL Analyses (Scripts 26, 26b, 26c)",    PHASE_13),
    ("PHASE 14 \u2014 Cluster Framework Diagnostics (Scripts 28\u201330)",   PHASE_14),
    ("PHASE 15 \u2014 Observed Differential Change, Envelope, and Validation (Scripts 32, 33, 35, 36, 37)", PHASE_15),
    ("PHASE 16 \u2014 Supplementary Standalone Diagnostics (Scripts 24b, 31, 31b, 34)", PHASE_16),
    ("PHASE 17 \u2014 Synthesis Figure and Greyscale Conversion (Scripts 09f, 27)",        PHASE_17),
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

# ── Down-pipeline dependency audit (optional helper) ─────────────────────────
# A *down-pipeline* (backward) dependency is a script that READS an output
# produced by a script running at a LATER execution step. On a fresh first
# pass that output does not yet exist, so the reader either falls back (if
# guarded) or fails. The static auditor lives in utils/pipeline_deps.py; the
# hooks below surface it via --deps and via per-step notes in run_script().
# Everything degrades silently if that helper module is not present, so the
# orchestrator runs unchanged without it.

_DEPS_FUNCS = None        # (build, print, notes) once imported, or False if absent
_DEPS_CACHE = None        # cached list of dependency records (built once per run)


def _load_deps_funcs():
    """Lazily import utils.pipeline_deps; return its 3 functions, or None."""
    global _DEPS_FUNCS
    if _DEPS_FUNCS is None:
        try:
            if str(SRC_DIR) not in sys.path:
                sys.path.insert(0, str(SRC_DIR))
            from utils.pipeline_deps import (
                build_dependencies, print_audit, notes_for_step)
            _DEPS_FUNCS = (build_dependencies, print_audit, notes_for_step)
        except Exception:
            _DEPS_FUNCS = False
    return _DEPS_FUNCS or None


def _dependencies():
    """Build (once) and cache the down-pipeline dependency list."""
    global _DEPS_CACHE
    if _DEPS_CACHE is None:
        funcs = _load_deps_funcs()
        if not funcs:
            _DEPS_CACHE = []
        else:
            try:
                # _STEP_MAP is {step: (script, label, extra)} — the auditor
                # accepts it directly, so the report uses true execution-step
                # order rather than script-file numbering.
                _DEPS_CACHE = funcs[0](SRC_DIR, step_map=_STEP_MAP)
            except Exception as exc:
                say_warn(f"dependency audit unavailable: {exc}")
                _DEPS_CACHE = []
    return _DEPS_CACHE


def show_dependency_audit() -> None:
    """Print the full down-pipeline dependency report (used by --deps / menu 'd')."""
    _banner("DOWN-PIPELINE DEPENDENCY AUDIT")
    funcs = _load_deps_funcs()
    if not funcs:
        say_warn("utils/pipeline_deps.py not found — cannot run the audit.")
        say_info("Place pipeline_deps.py in src/utils/ to enable this report.")
        print()
        return
    print()
    funcs[1](_dependencies())   # print_audit
    print()


def _emit_step_dep_notes(label: str) -> None:
    """Emit any down-pipeline dependency warnings relevant to this step."""
    funcs = _load_deps_funcs()
    if not funcs:
        return
    try:
        step = int(label.strip().split("/")[0])
    except (ValueError, IndexError):
        return
    for msg in funcs[2](step, _dependencies()):   # notes_for_step
        say_warn(msg)


# ── Validation checkpoints ────────────────────────────────────────────────────

REQUIRED_DATA = [
    "Newborough_Cleaned_For_Model.csv",
    "RAF_Valley_Climate.csv",
    "well_metadata.csv",          # consolidated; replaced Well_locations_height.csv + well_distance_to_coast.csv
]
REQUIRED_PHASE1_OUTPUTS = [
    "01_wells_reference.csv",
    "01_wells_extended.csv",
    "02_cluster_stats.csv",
]
REQUIRED_PHASE3_OUTPUTS = [
    "03_master_data.csv",
    "10_clearfell_baci/10a_01_ancova_comparison_table.csv",
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
    (11, REQUIRED_PHASE3_OUTPUTS,  "Phase 3 (steps 7–12)"),
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

def _hr(char="─", width=70, colour=None):
    print(paint(char * width, colour) if colour else char * width)

def _banner(title: str, colour: str = None):
    colour = colour or _Ansi.BCYAN
    bar = "═" * 70
    print(paint(bar, colour))
    print("  " + paint(title, colour, _Ansi.BOLD))
    print(paint(bar, colour))

def ensure_paths() -> None:
    if not SRC_DIR.exists():
        raise FileNotFoundError(f"Missing src/ directory: {SRC_DIR}")
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Missing data/ directory: {DATA_DIR}")
    OUT_DIR.mkdir(exist_ok=True)
    missing = [n for n in REQUIRED_DATA if not (DATA_DIR / n).exists()]
    if missing:
        raise FileNotFoundError("Missing required data files: " + ", ".join(missing))

# ── Console logging (full-pipeline runs) ──────────────────────────────────────
# When enabled, all console output for a full pipeline run is mirrored to a
# log file. The orchestrator's own prints are teed via sys.stdout/sys.stderr;
# child-script output (which writes straight to the terminal file descriptor
# and bypasses a sys.stdout tee) is captured by running each step through
# _run_subprocess(), which pipes the child and re-emits it line-by-line.

_LOG_FH = None
_REAL_STDOUT = None
_REAL_STDERR = None


class _Tee:
    """Write-through stream that mirrors to several underlying streams."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for s in self._streams:
            try:
                s.write(data)
            except Exception:
                pass
        return len(data)

    def flush(self):
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass

    def isatty(self):
        return getattr(self._streams[0], "isatty", lambda: False)()

    @property
    def encoding(self):
        return getattr(self._streams[0], "encoding", "utf-8")


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class _AnsiStripper:
    """Adapter that strips ANSI colour codes before writing to a stream.

    Wrapped around the log file handle so the console can stay colourful
    while the saved log remains plain text.
    """

    def __init__(self, stream):
        self._s = stream

    def write(self, data):
        self._s.write(_ANSI_RE.sub("", data))
        return len(data)

    def flush(self):
        self._s.flush()


def start_logging(path=None):
    """Begin mirroring console output to a log file. Returns the log path."""
    global _LOG_FH, _REAL_STDOUT, _REAL_STDERR
    if _LOG_FH is not None:
        return Path(_LOG_FH.name)
    if path in (None, "AUTO"):
        log_dir = OUT_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = log_dir / f"run_{stamp}.log"
    else:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
    _LOG_FH = open(path, "w", encoding="utf-8")
    _REAL_STDOUT, _REAL_STDERR = sys.stdout, sys.stderr
    _log_sink = _AnsiStripper(_LOG_FH)
    sys.stdout = _Tee(_REAL_STDOUT, _log_sink)
    sys.stderr = _Tee(_REAL_STDERR, _log_sink)
    _LOG_FH.write(
        "# Newborough Warren pipeline run log\n"
        f"# Started: {datetime.datetime.now().isoformat(timespec='seconds')}\n"
        f"# Command: {' '.join(sys.argv)}\n\n"
    )
    _LOG_FH.flush()
    print("  " + paint(f"{GLYPH_INFO} Recording console output to: {path}", _Ansi.CYAN))
    return path


def stop_logging():
    """Stop mirroring and close the log file."""
    global _LOG_FH, _REAL_STDOUT, _REAL_STDERR
    if _LOG_FH is None:
        return
    path = Path(_LOG_FH.name)
    print("\n  " + paint(f"{GLYPH_INFO} Console output saved to: {path}", _Ansi.CYAN))
    sys.stdout, sys.stderr = _REAL_STDOUT, _REAL_STDERR
    try:
        _LOG_FH.flush()
        _LOG_FH.close()
    finally:
        _LOG_FH = None
        _REAL_STDOUT = None
        _REAL_STDERR = None


def _prompt_logging():
    """Ask whether to record this full run. Returns log path or None."""
    if _LOG_FH is not None:
        return Path(_LOG_FH.name)
    ans = input("\n  Record full console output to a log file? [y/N] ").strip().lower()
    if ans != "y":
        return None
    custom = input(
        "  Log path (Enter for default outputs/logs/run_<timestamp>.log): "
    ).strip()
    return start_logging(custom or None)


def _run_subprocess(cmd, cwd):
    """Run a child process, teeing its output to the log file when active.

    When logging is off this is identical to the previous
    subprocess.run(..., check=True) behaviour (the child inherits the
    terminal directly). When logging is on, the child is piped and its
    output is re-emitted line-by-line through sys.stdout (the tee), so it
    appears live on screen AND in the log file.
    """
    if _LOG_FH is None:
        subprocess.run(cmd, cwd=cwd, check=True)
        return
    proc = subprocess.Popen(
        cmd, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.stdout.close()
    ret = proc.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, cmd)


def run_script(script_name: str, label: str, extra_args: list = None) -> None:
    script_path = SRC_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    step_txt = label.strip()
    print()
    print("  " + paint(f"{GLYPH_RUN} STEP {step_txt}", _Ansi.BBLUE, _Ansi.BOLD))
    print("  " + paint(f"    script: {script_path.name}", _Ansi.GREY))
    print("  " + paint("─" * 66, _Ansi.GREY))
    _emit_step_dep_notes(label)
    cmd = [sys.executable, str(script_path)] + (extra_args or [])
    t0 = time.time()
    try:
        _run_subprocess(cmd, cwd=str(ROOT_DIR))
    except Exception:
        print("  " + paint(f"{GLYPH_FAIL} FAILED", _Ansi.BRED, _Ansi.BOLD)
              + paint(f"  ({script_path.name})", _Ansi.GREY))
        raise
    dt = time.time() - t0
    print("  " + paint(f"{GLYPH_OK} done", _Ansi.BGREEN, _Ansi.BOLD)
          + paint(f"  ({dt:0.1f}s)", _Ansi.GREY))

def validate_outputs(required: list, phase_name: str) -> None:
    missing = [n for n in required if not (OUT_DIR / n).exists()]
    if missing:
        raise FileNotFoundError(f"{phase_name} outputs missing: " + ", ".join(missing))
    print()
    say_ok(f"{phase_name} validation passed.")


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
    print("  This step depends on these files and will likely fail.")
    print("  If this is your first run on this dataset, run the FULL")
    print("  pipeline first using option 1 of the main menu (or")
    print("  --full from the CLI). Partial runs only work once all")
    print("  upstream phases have completed at least once.")
    _hr("!")

    if not interactive:
        # CLI mode: warn but proceed
        print("  (Proceeding — use --full for a clean run if this fails.)\n")
        return True

    ans = input("\n  Proceed anyway? [y/N] ").strip().lower()
    return ans == "y"

def run_phase(phase: list, phase_name: str, from_step: int = 1) -> None:
    print()
    print(paint("━" * 70, _Ansi.CYAN))
    print("  " + paint(phase_name, _Ansi.BCYAN, _Ansi.BOLD))
    print(paint("━" * 70, _Ansi.CYAN))
    for entry in phase:
        script_name, label = entry[0], entry[1]
        extra_args = entry[2] if len(entry) > 2 else None
        try:
            step_num = int(label.strip().split("/")[0])
        except (ValueError, IndexError):
            step_num = 0
        if step_num < from_step:
            print("  " + paint(f"{GLYPH_SKIP} skip step {label.strip()}", _Ansi.GREY))
            continue
        run_script(script_name, label, extra_args)

# ── Pipeline runners ──────────────────────────────────────────────────────────

def run_full_pipeline(from_step: int = 1, include_supplementary: bool = False) -> None:
    ensure_paths()
    _t_start = time.time()
    run_phase(PHASE_1,  "PHASE 1  — Core LCSC Chain",                             from_step)
    if from_step <= 4:
        validate_outputs(REQUIRED_PHASE1_OUTPUTS, "Phase 1")
    run_phase(PHASE_2,  "PHASE 2  — Pearson Membership Audit",                    from_step)
    run_phase(PHASE_3,  "PHASE 3  — Model Diagnostics and Intervention Analysis", from_step)
    if from_step <= 10:
        validate_outputs(REQUIRED_PHASE3_OUTPUTS, "Phase 3")
    run_phase(PHASE_4,  "PHASE 4  — Climate Projections and Figure Generation",   from_step)
    run_phase(PHASE_5,  "PHASE 5  — Depth-Dependent PET Analysis",                from_step)
    run_phase(PHASE_6,  "PHASE 6  — WTF Cluster Sy Estimation",                   from_step)
    run_phase(PHASE_7,  "PHASE 7  — Water Balance Decomposition",                 from_step)
    run_phase(PHASE_8,  "PHASE 8  — WTF Spatial Analysis and Sy Mapping",         from_step)
    run_phase(PHASE_9,  "PHASE 9  — Spatial Groundwater Analysis",                from_step)
    if from_step <= 21:
        validate_outputs(REQUIRED_PHASE9_OUTPUTS, "Phase 9")
    run_phase(PHASE_10, "PHASE 10 — Forestry Scenario Analysis",                  from_step)
    validate_outputs(REQUIRED_PHASE10_OUTPUTS, "Phase 10")
    run_phase(PHASE_11, "PHASE 11 — Coastal-Retreat Gradient Analysis (Script 25)", from_step)
    run_phase(PHASE_12, "PHASE 12 — Supplementary Diagnostics (Scripts 22–24)",  from_step)
    run_phase(PHASE_13, "PHASE 13 — Van Willegen MSL Analyses (Scripts 26, 26b, 26c)", from_step)
    run_phase(PHASE_14, "PHASE 14 — Cluster Framework Diagnostics (Scripts 28–30)",  from_step)
    run_phase(PHASE_15, "PHASE 15 — Observed Differential Change, Envelope, and Validation (Scripts 32, 33, 35, 36, 37)", from_step)
    last_step = 40  # Phase 15 ends at step 40 (Script 37)
    if include_supplementary:
        run_phase(PHASE_16,
                  "PHASE 16 — Supplementary Standalone Diagnostics (Scripts 24b, 31, 31b, 34)",
                  from_step)
        last_step = 44  # Phase 16 ends at step 44 (Script 34)
    # Phase 17 synthesis figure (Script 09f, step 44) — a display/utility figure
    # that IS part of the full run (unlike the greyscale utility, step 45, which
    # is invoked on demand via run_greyscale()). Runs last so its upstream
    # inputs (Scripts 20/25/09d/10a) already exist; two-pass-safe otherwise.
    if from_step <= 45:
        run_phase([PHASE_17[0]],
                  "PHASE 17 — Synthesis Figure (Script 09f)", from_step)
        last_step = 45
    _elapsed = (time.time() - _t_start) / 60.0
    print()
    _banner(f"PIPELINE COMPLETE  ·  steps 1–{last_step} written to outputs/", _Ansi.BGREEN)
    if not include_supplementary:
        say_info("supplementary standalone diagnostics (Phase 16: steps 41–44, "
                 "Scripts 24b/31/31b/34) NOT run — add --with-supplementary "
                 "(or choose it in menu option 1) to include them")
    say_info("greyscale (step 46) runs separately (menu option 6 / --greyscale)")
    say_info(f"total run time: {_elapsed:0.1f} min")

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
        say_err(f"Script not found: {script_path}")
        return

    # Script 19 is step 21 — needs all upstream Phase 1-8 outputs to exist.
    if not warn_missing_upstream(21):
        print("  Aborted.")
        return

    print(f"  Running {VIEWER_SCRIPT} ...")
    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT_DIR), check=True,
    )

    if VIEWER_OUTPUT.exists():
        size_kb = VIEWER_OUTPUT.stat().st_size / 1024
        say_ok(f"Viewer ready: {VIEWER_OUTPUT}")
        print(paint(f"       File size: {size_kb:.1f} KB", _Ansi.GREY))
        print(paint("       Open in any browser — no server required.", _Ansi.GREY))
    else:
        say_warn(f"Viewer not found at expected path: {VIEWER_OUTPUT}")

# ── Interactive menu ──────────────────────────────────────────────────────────

def _intro_block() -> str:
    lines = [
        "88-dipwell network · Newborough Warren NNR (Isle of Anglesey SAC)",
        "Monitoring 2005–2026 · State-space model (β₁ recharge, β₂ draw, β₃ drainage)",
        "Five hydrogeological clusters C1–C5 · Ward's-linkage hierarchical clustering",
        "Hollingham (2026)",
    ]
    return "\n".join("  " + ln for ln in lines)


def render_menu() -> str:
    num  = lambda s: paint(s, _Ansi.BCYAN, _Ansi.BOLD)
    grp  = lambda s: paint(s, _Ansi.BOLD)
    hint = lambda s: s
    rule = "─" * 70
    out = [
        "",
        hint("  First run / new dataset → option 1 (full pipeline). For canonical"),
        hint("  scenario figures, run the full pipeline twice. Options 2–6 require the"),
        hint("  full pipeline to have completed at least once."),
        "",
        "  " + rule,
        "  " + grp("RUN"),
        f"    {num('1')}   Full pipeline             " + hint("steps 1–38 (+39–42 opt-in) · run twice for new data"),
        f"    {num('2')}   Resume from a step        " + hint("pick up mid-pipeline"),
        f"    {num('3')}   Run a single step",
        "",
        "  " + grp("TOOLS"),
        f"    {num('4')}   Build scenario viewer     " + hint("standalone HTML"),
        f"    {num('5')}   Supplementary diagnostics " + hint("steps 27–29 (Scripts 22–24)"),
        f"    {num('6')}   Greyscale figures         " + hint("6a quick · 6b full B&W · 6h help"),
        "",
        "  " + grp("INFO"),
        f"    {num('7')}   Show pipeline step list",
        f"    {num('d')}   Dependency audit          " + hint("backward (down-pipeline) reads"),
        f"    {num('h')}   Help — explain the pipeline & options",
        f"    {num('q')}   Quit",
        "  " + rule,
    ]
    return "\n".join(out)

def show_step_list() -> None:
    print()
    _banner("Pipeline Step List", _Ansi.CYAN)
    for phase_label, phase_entries in ALL_PHASES:
        print("\n  " + paint(phase_label, _Ansi.BCYAN, _Ansi.BOLD))
        for entry in phase_entries:
            script, label = entry[0], entry[1]
            try:
                step = int(label.strip().split("/")[0])
            except (ValueError, IndexError):
                step = 0
            present = (SRC_DIR / script).exists()
            tag = paint(GLYPH_OK, _Ansi.GREEN) if present else paint(GLYPH_FAIL, _Ansi.BRED)
            print(f"    {tag}  " + paint(f"step {step:>2}", _Ansi.BOLD) + f"  {script}")
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
    bw = input("  Run in B&W mode? [y/N] ").strip().lower() == "y"
    ans = input("  Confirm? [y/N] ").strip().lower()
    if ans == "y":
        import os
        if bw:
            os.environ["NRG_BW_MODE"] = "1"
            print("  [BW] Running with BW_MODE=True")
        ensure_paths()
        try:
            run_script(script, label, extra)
        finally:
            if bw:
                os.environ.pop("NRG_BW_MODE", None)
        print(f"\n  [OK] Step {n} complete.")
        if bw:
            print("  [BW] Copying figures to outputs_bw/ ...")
            run_script("27_greyscale_figures.py", "46/46  Greyscale figure conversion")
            bw_dir = ROOT_DIR / "outputs_bw"
            if bw_dir.exists():
                n_figs = len(list(bw_dir.rglob("*.png"))) + len(list(bw_dir.rglob("*.jpg")))
                print(f"  [OK] {n_figs} figures in outputs_bw/")

def run_supplementary() -> None:
    """Run supplementary diagnostic scripts 22–24."""
    ensure_paths()
    if not warn_missing_upstream(25):
        print("  Aborted.")
        return
    run_phase(PHASE_12, "PHASE 12 — Supplementary Diagnostics (Scripts 22–24)")
    print()
    say_ok("Supplementary diagnostics complete.")

def run_greyscale(full_rerun: bool = False) -> None:
    """Run greyscale figure generation.

    Parameters
    ----------
    full_rerun : bool
        If True, re-run the figure-producing pipeline (steps 1-37) with
        BW_MODE=True (native B&W rendering with hatching, line styles,
        hillshade DEMs); no separate greyscale sweep is required.
        If False, just run Script 27 pixel conversion on existing outputs.
    """
    print()
    _hr()
    print("  Greyscale Figure Generation")
    _hr()
    print()

    script_path = SRC_DIR / "27_greyscale_figures.py"
    if not script_path.exists():
        say_err(f"Script not found: {script_path}")
        return

    # Check that outputs/ exists and has figures
    if not OUT_DIR.exists() or not list(OUT_DIR.rglob("*.png")):
        say_err("No figures found in outputs/. Run the full pipeline first.")
        return

    if full_rerun:
        print("  Mode: Full B&W pipeline re-run")
        print("  This will re-run all 34 steps with BW_MODE=True,")
        print("  producing native greyscale figures with hatching, distinct")
        print("  line styles, and hillshade DEMs. No separate greyscale")
        print("  sweep is needed — every figure is rendered greyscale-native.")
        print()
        # Set env var so all subprocess scripts pick up BW_MODE=True
        import os
        os.environ["NRG_BW_MODE"] = "1"
        print(f"\n  [BW] NRG_BW_MODE set to: {os.environ.get('NRG_BW_MODE')}")
        print("  [BW] Child processes will inherit BW_MODE=True\n")
        try:
            run_full_pipeline(from_step=1)
        finally:
            os.environ.pop("NRG_BW_MODE", None)
        # In BW mode the figure steps (1-35) rendered natively in greyscale,
        # so the separate step-36 greyscale conversion (Script 27) is not needed.
    else:
        print("  Mode: Pixel conversion only (Script 27)")
        print("  This converts existing colour figures to greyscale using")
        print("  perceptual luminance weighting. Quick but some figures")
        print("  may be suboptimal — use 'Full B&W re-run' for best results.")
        print()
        run_script("27_greyscale_figures.py", "46/46  Greyscale figure conversion")

    bw_dir = ROOT_DIR / "outputs_bw"
    if bw_dir.exists():
        n_figs = len(list(bw_dir.rglob("*.png"))) + len(list(bw_dir.rglob("*.jpg")))
        print()
        say_ok(f"{n_figs} greyscale figures in: {bw_dir}/")
    print()

def show_help() -> None:
    """Print a structured, colour-coded explanation of the pipeline and menu."""
    H = lambda s: paint(s, _Ansi.BCYAN, _Ansi.BOLD)
    K = lambda s: paint(s, _Ansi.BOLD)
    D = lambda s: paint(s, _Ansi.GREY)

    print()
    _banner("HELP  ·  Newborough Warren Pipeline", _Ansi.BCYAN)

    print("\n" + H("  What this does"))
    print("  Runs the Hollingham (2026) groundwater analysis end to end — data")
    print("  preparation, behavioural clustering, the state-space model, BACI")
    print("  intervention analyses, spatial mapping, climate projections and")
    print("  journal figures for the 88-dipwell Newborough Warren network.")

    print("\n" + H("  Pipeline structure") + D("   (43 steps across 17 phases)"))
    for phase_label, phase_entries in ALL_PHASES:
        steps = [int(e[1].strip().split("/")[0]) for e in phase_entries
                 if e[1].strip().split("/")[0].isdigit()]
        if not steps:
            rng = ""
        elif len(steps) == 1:
            rng = f"step {steps[0]}"
        else:
            rng = f"steps {steps[0]}–{steps[-1]}"
        print("    " + paint(phase_label, _Ansi.CYAN) + D(f"   ({rng})"))
    print(D("\n  A full run executes steps 1–38. The Phase 16 standalone diagnostics"))
    print(D("  (steps 39–42) are opt-in via --with-supplementary or the option 1 prompt;"))
    print(D("  greyscale (Phase 17, step 43) runs separately via option 6 / --greyscale."))

    print("\n" + H("  Menu options"))
    opts = [
        ("1", "Full pipeline", "runs steps 1–38 (opt-in Phase 16); offers to save a console log"),
        ("2", "Resume from a step", "re-run from step N onward (after one full run)"),
        ("3", "Run a single step", "run one script; optional B&W mode"),
        ("4", "Build scenario viewer", "regenerate the standalone HTML viewer (Script 19)"),
        ("5", "Supplementary diagnostics", "Scripts 22–24 — residual lag, ridge recharge, seasonality"),
        ("6", "Greyscale figures", "6a quick convert · 6b full B&W re-run · 6h detail"),
        ("7", "Show step list", "list every step and whether its script is present"),
        ("h", "Help", "this page"),
        ("q", "Quit", ""),
    ]
    for key, name, desc in opts:
        print("    " + paint(f"{key:>2}", _Ansi.BCYAN, _Ansi.BOLD) + "  "
              + K(f"{name:<26}") + D(desc))

    print("\n" + H("  Two-pass run (new datasets)"))
    print("  Scripts 09b/09d in Phase 3 use Specific-Yield values produced later")
    print("  (steps 18/20). On a first pass they fall back to documented Newborough")
    print("  defaults (0.20 cluster, 0.30 CEH36) with warnings — results are")
    print("  unaffected. For canonical scenario figures, run again from step 9:")
    print(D("     pass 1: option 1     pass 2: option 2 → step 9"))

    print("\n" + H("  Console logging"))
    print("  Option 1 (and --full --log) can mirror everything printed — the")
    print("  orchestrator and every child script — to a timestamped log:")
    print(D("     outputs/logs/run_<YYYYMMDD_HHMMSS>.log"))

    print("\n" + H("  Command line"))
    cli = [
        ("--full [--log [PATH]]", "run steps 1–38 (optionally log to file)"),
        ("--with-supplementary", "with --full/--from: also run Phase 16 (steps 39–42)"),
        ("--clusters N", "clustering target K for the partition (default 5)"),
        ("--from N", "resume from step N"),
        ("--viewer", "build the scenario viewer only"),
        ("--supplementary", "run Scripts 22–24 only"),
        ("--greyscale", "quick pixel greyscale convert"),
        ("--greyscale-full", "full B&W pipeline re-run (best quality)"),
        ("--no-colour", "disable coloured output"),
        ("--deps", "audit down-pipeline (backward) dependencies"),
        ("--explain", "print this help page and exit"),
    ]
    for flag, desc in cli:
        print("    " + paint(f"{flag:<24}", _Ansi.BOLD) + D(desc))

    print("\n" + H("  Where outputs go"))
    print("    " + K("outputs/      ") + D("colour figures, tables, CSVs"))
    print("    " + K("outputs_bw/   ") + D("greyscale (journal-print) figures"))
    print("    " + K("outputs/logs/ ") + D("saved console logs"))
    print()


def interactive_menu() -> None:
    _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
    print()
    print(_intro_block())

    while True:
        print(render_menu())
        choice = input("\n  " + paint("Enter choice:", _Ansi.BOLD) + " ").strip().lower()

        if choice == "1":
            print(
                "\n  NOTE: Two scripts in Phase 3 (09b, 09d) read Sy values\n"
                "  produced later in the pipeline (steps 18 and 20). On a fresh\n"
                "  first-pass run they will use documented fallbacks with\n"
                "  console warnings — this does not break the pipeline.\n\n"
                "  For canonical scenario figures on a new dataset, run twice:\n"
                "    pass 1: this option (full pipeline)\n"
                "    pass 2: option 2, resume from step 9\n"
                "  See module docstring for details."
            )
            ans = input("\n  Run the full pipeline (steps 1–38) from the beginning? [y/N] ").strip().lower()
            if ans == "y":
                kc = input(
                    "  Clustering target k for the partition [5]\n"
                    "  (fixed at 5 by default; silhouette's trivial k=2 peak is not used): "
                ).strip()
                if kc:
                    try:
                        kc_n = int(kc)
                        if kc_n < 2:
                            raise ValueError
                        os.environ["NRG_N_CLUSTERS"] = str(kc_n)
                        say_info(f"Clustering target set to k={kc_n} for this run")
                    except ValueError:
                        say_warn("Not a valid integer >= 2 — using default k=5")
                supp = input(
                    "  Also run the supplementary standalone diagnostics\n"
                    "  (Phase 16, steps 39–42: Scripts 24b, 31, 31b, 34)? [y/N] "
                ).strip().lower() == "y"
                log_path = _prompt_logging()
                try:
                    run_full_pipeline(from_step=1, include_supplementary=supp)
                finally:
                    if log_path is not None:
                        stop_logging()

        elif choice == "2":
            menu_run_from()

        elif choice == "3":
            menu_run_single()

        elif choice == "4":
            build_viewer()

        elif choice == "5":
            run_supplementary()

        elif choice in ("6", "6a"):
            run_greyscale(full_rerun=False)

        elif choice == "6b":
            print(
                "\n  ┌─────────────────────────────────────────────────────────┐"
                "\n  │  WARNING: This will OVERWRITE your colour figures in   │"
                "\n  │  outputs/ with greyscale versions. To restore colour   │"
                "\n  │  figures afterwards, run option 1 again.               │"
                "\n  │                                                        │"
                "\n  │  Recommended workflow:                                 │"
                "\n  │    1. Run option 6b  → B&W figures in outputs/         │"
                "\n  │       Script 27 copies them to outputs_bw/             │"
                "\n  │    2. Run option 1   → colour figures restored in      │"
                "\n  │       outputs/                                         │"
                "\n  │                                                        │"
                "\n  │  After both runs you have:                             │"
                "\n  │    outputs/    → colour figures (screen/web)           │"
                "\n  │    outputs_bw/ → greyscale figures (journal print)     │"
                "\n  └─────────────────────────────────────────────────────────┘"
            )
            ans = input("\n  Proceed with B&W pipeline run? [y/N] ").strip().lower()
            if ans == "y":
                run_greyscale(full_rerun=True)

        elif choice == "6h":
            print(
                "\n  ── Greyscale / B&W Figure Help ──────────────────────────"
                "\n"
                "\n  The pipeline produces two sets of figures:"
                "\n"
                "\n    COLOUR (default)  — for screen, web, presentations."
                "\n      Generated by option 1 (full pipeline)."
                "\n      Stored in: outputs/"
                "\n"
                "\n    GREYSCALE (B&W)   — for journal print submission."
                "\n      Generated by option 6b (full B&W pipeline re-run)."
                "\n      Uses hatched bars, distinct line styles, hillshade"
                "\n      DEM basemaps, and linear grey colourscales."
                "\n      Stored in: outputs_bw/"
                "\n"
                "\n  Option 6a / 6  — Quick pixel conversion only. Converts"
                "\n    existing colour figures to greyscale without re-rendering."
                "\n    Fast but some figures may be suboptimal."
                "\n"
                "\n  Option 6b — Full B&W re-run. Re-runs the entire pipeline"
                "\n    with BW_MODE=True so scripts produce native B&W figures."
                "\n    Best quality. OVERWRITES outputs/ — run option 1 after"
                "\n    to restore colour figures."
                "\n"
                "\n  Recommended workflow for journal submission:"
                "\n    1. Run option 1   (colour pipeline)"
                "\n    2. Run option 6b  (B&W pipeline → outputs_bw/)"
                "\n    3. Run option 1   (restore colour figures)"
                "\n"
                "\n  CLI equivalents:"
                "\n    python run_analysis.py --full            # colour"
                "\n    python run_analysis.py --greyscale-full  # B&W"
                "\n    python run_analysis.py --full            # restore colour"
                "\n"
            )

        elif choice == "7":
            show_step_list()

        elif choice in ("d", "deps"):
            show_dependency_audit()

        elif choice in ("h", "?", "help"):
            show_help()

        elif choice in ("q", "quit", "exit"):
            print("\n  Exiting.\n")
            break

        else:
            say_warn("Unrecognised option.")

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Newborough Warren analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Run without arguments for the interactive menu.
            Use --full, --from, --viewer, --supplementary, or --greyscale for non-interactive execution.
            Add --log to a --full run to record all console output to a log file.
            --explain prints the in-app help page; --no-colour disables coloured output.
            --deps prints the down-pipeline (backward) dependency audit and exits.
        """)
    )
    parser.add_argument("--full",   action="store_true",
                        help="Run all 43 steps non-interactively")
    parser.add_argument("--with-supplementary", dest="with_supplementary",
                        action="store_true",
                        help="With --full/--from: also run the Phase 16 standalone "
                             "diagnostic tier (steps 39–42: Scripts 24b, 31, 31b, 34)")
    parser.add_argument("--clusters", dest="clusters", type=int, metavar="N",
                        default=None,
                        help="Clustering target K for the partition (Script 02). "
                             "Default 5 (analyst-fixed; silhouette's trivial k=2 "
                             "peak is not used). Sets NRG_N_CLUSTERS for the run.")
    parser.add_argument("--log", nargs="?", const="AUTO", default=None, metavar="PATH",
                        help="With --full: record all console output to a log file "
                             "(optional PATH; default outputs/logs/run_<timestamp>.log)")
    parser.add_argument("--from",   dest="from_step", type=int, metavar="N",
                        help="Resume from step N non-interactively")
    parser.add_argument("--viewer", action="store_true",
                        help="Build the scenario viewer only")
    parser.add_argument("--supplementary", action="store_true",
                        help="Run supplementary diagnostics (scripts 22–24) only")
    parser.add_argument("--greyscale", action="store_true",
                        help="Convert existing figures to greyscale (Script 27 only)")
    parser.add_argument("--greyscale-full", action="store_true",
                        help="Re-run full pipeline in B&W mode then convert (best quality)")
    parser.add_argument("--no-colour", "--no-color", dest="no_colour",
                        action="store_true", help="Disable coloured console output")
    parser.add_argument("--explain", action="store_true",
                        help="Print the in-app help page and exit")
    parser.add_argument("--deps", action="store_true",
                        help="Print the down-pipeline dependency audit and exit")
    args = parser.parse_args()

    _init_colour(disable=args.no_colour)

    # Clustering target K is a run parameter consumed by Script 02 (and the
    # cluster-validation diagnostics) via NRG_N_CLUSTERS. Setting it here means
    # every subprocess this run launches inherits it.
    if args.clusters is not None:
        if args.clusters < 2:
            say_err("--clusters must be >= 2"); sys.exit(1)
        os.environ["NRG_N_CLUSTERS"] = str(args.clusters)
        say_info(f"Clustering target set to k={args.clusters} for this run "
                 "(NRG_N_CLUSTERS)")

    if args.explain:
        show_help()
        return

    if args.deps:
        show_dependency_audit()
        return

    if args.log is not None and not args.full:
        say_warn("--log only applies to --full runs; ignoring.")

    try:
        if args.viewer:
            build_viewer()
        elif args.greyscale_full:
            _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
            run_greyscale(full_rerun=True)
        elif args.greyscale:
            _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
            run_greyscale(full_rerun=False)
        elif args.supplementary:
            _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
            run_supplementary()
        elif args.full:
            _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
            log_active = False
            if args.log is not None:
                start_logging(None if args.log == "AUTO" else args.log)
                log_active = True
            try:
                run_full_pipeline(from_step=1,
                                  include_supplementary=args.with_supplementary)
            finally:
                if log_active:
                    stop_logging()
        elif args.from_step is not None:
            _banner("NEWBOROUGH WARREN GROUNDWATER ANALYSIS PIPELINE")
            warn_missing_upstream(args.from_step, interactive=False)
            run_full_pipeline(from_step=args.from_step,
                              include_supplementary=args.with_supplementary)
        else:
            interactive_menu()
    except KeyboardInterrupt:
        print("\n\n  Interrupted.\n")
        sys.exit(0)
    except Exception as exc:
        print()
        say_err(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
