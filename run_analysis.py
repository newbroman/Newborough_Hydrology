"""
run_analysis.py — Newborough Warren Groundwater Analysis Pipeline
Interactive orchestrator for the Hollingham (2026) analytical pipeline.

Usage
-----
  python run_analysis.py              # interactive menu
  python run_analysis.py --full       # non-interactive: run all default-tier steps
  python run_analysis.py --full --with-supplementary  # ... plus every opt-in diagnostic step
  python run_analysis.py --full --clusters 5          # set the clustering target K (default 5)
  python run_analysis.py --full --log # ... and record all console output to a log file
  python run_analysis.py --from N     # non-interactive: resume from step N
  python run_analysis.py --viewer     # non-interactive: build scenario viewer only
  python run_analysis.py --greyscale  # non-interactive: convert figures to B&W
  python run_analysis.py --manifest-only  # write outputs/pipeline_manifest.json and exit
  python run_analysis.py --explain     # print the in-app help page and exit
  python run_analysis.py --deps        # print the down-pipeline dependency audit and exit
  python run_analysis.py --no-colour   # disable coloured output

Pipeline structure
------------------
Step numbering and totals are DERIVED, never hard-typed — every step is
registered once as a Step(script, desc, tier, exec, n_substeps) record
below; "{i}/{total}" is rendered at runtime from enumeration position, and
the committed outputs/pipeline_manifest.json (emitted on every run, or
standalone via --manifest-only) is the citable source for the current
totals. Do not cite a fixed step/phase count in the report, supplement,
or elsewhere in code — cite the manifest.

Each step carries a tier for reporting purposes:
  "A" analytical   — the numbered analytical core (Scripts 01–26 excluding
                      26c, plus 22–24, 26/26b, the Phase 15 steps 32/33/35/
                      36/37/37b, and the Phase 16 steps 34/38).
  "D" display/utility — Scripts 26c, 09f, 09g, 27 only.
  "X" diagnostic   — every other registered step (Phase 14, which runs by
                      default, and the Phase 16 remainder 24b/31/31b, which
                      does not).

There is no separate "analytical headline" count. Every figure the report,
Methods Supplement, readme and index.html quote is a field of the manifest,
computed here from the step table: total_registered, total_phases, the tier
breakdown, and the exec breakdown. The tier and exec breakdowns are two
independent partitions of the SAME registered steps and must never be added
to one another — a sentence of the form "N registered, of which A analytical
plus D display/utility" mixes the axes and will not sum. See the note above
_DOCUMENTED_COUNTS.

  Tier "A" analytical steps are those cited with a reproducible figure or
  number in the main report (for example Script 38: §4.8.3 coast-to-inland
  δ₀; Script 34: §5.7.5 window-sensitivity envelope). Tier "X" steps are
  opt-in diagnostics that appear only in the methods enumeration.

Each step also carries an exec flag: "default" (part of a normal --full
run) or "optin" (runs only with --with-supplementary / the menu option 1
prompt). Adding or removing any step moves the manifest counts on the next
run and trips the document-drift guard in build_manifest(), which names
every field that no longer matches what the documents currently state.

Phases 1–11 produce the main analytical results documented in the report.
Phase 12 runs supplementary diagnostics (Scripts 22–24); Phase 16 runs
further standalone diagnostics (Scripts 24b, 31, 31b, 34, 38) before
greyscale conversion. Phase 13 runs the van Willegen et al. (2025) MSL
analyses — observational 5-year MSL aggregation (Script 26), UKCP18 RCP8.5
climate projections (Script 26b), and report-format figures (Script 26c,
for §4.8.4 and §4.10.1) — paired tools documented in §3.7.5 of the report.
Phase 14 runs the post-review cluster framework diagnostics — the C3
detrend check (Script 28, validating the aquifer-architecture framing
of §5.1) and the within-C3 variance attribution (Script 29, characterising
the spatial structure within C3) and the C4 drainage identifiability
diagnostic (Script 30, testing directly whether C4's low β₃ is a β₂/β₃
degeneracy artefact and finding it is not — the centroid β₃ is cleanly
identified and the low value is real) — documented in §5.1.1 and §4.2.2 of
the report and §S.19 of the Methods Supplement.
Phase 15 is wholly analytical-default (Scripts 32, 33, 35, 36, 37, 37b all
run by default). Phase 16 runs Scripts 34, 38 and 39 by default plus a
supplementary opt-in remainder — Scripts
24b, 31, 31b — which still runs only with --with-supplementary (or the menu
option 1 prompt). Phase 17 runs the synthesis figures (Script 09f, and
Script 09g — the §5.8 mechanism grid + coastal reach,
which reads the 09f reach profile emitted moments earlier in the same pass —
both auto-run as part of a normal full run) and the greyscale figure-conversion
utility (Script 27, which never auto-runs — it's a callable utility step,
run separately via menu option 6 / --greyscale).

Two-pass execution (RECOMMENDED for new datasets)
-------------------------------------------------
Two scripts in Phase 3 use Specific-Yield (Sy) values that are produced
later in the pipeline (Phase 6 / Phase 8):

    09b_scraping_propagation     reads OUT_17_SY_TABLE  (produced by Script 17,
                                  see pipeline_manifest.json for its current step index)
    09d_scenario_comparison      reads INT_WTF_WELL_SY  (produced by Script 18,
                                  see pipeline_manifest.json for its current step index)

On a fresh first-pass full-pipeline run those files do not yet exist,
and Phase 3 falls back to documented Newborough-2026 Sy defaults
(0.20 cluster, 0.30 CEH36) with console warnings. The scientific
analyses themselves are unaffected — these scripts use Sy only for a
volumetric scenario-comparison conversion in their figures.

Script 09f (Phase 17, a display/utility synthesis figure) similarly reads
outputs produced earlier in the SAME pass — Scripts 20, 25, 09d and 10a
(see pipeline_manifest.json for their current step indices). It runs last,
so on a normal full run all of these already exist; only on a partial or
interrupted run does it fall back to documented defaults (centralised in
pipeline_params._DEFAULTS, read via default_value()) with warnings. The
figure it produces re-presents existing modelled fields and adds no new
analysis, so first-pass defaults do not affect any analytical result.
Script 09g (also Phase 17, display/utility) reads the 09f_01 reach profile,
the 10m WMC3 BACI and the 10a clearfell steps, all produced earlier in the
same pass, with the same pipeline_params fallback pattern for partial runs.

Script 10a (D-111, from 2026-09-02) reads OUT_25_CORRECTION_DIAGNOSTIC — the
Script 25 coastal donor — which is produced LATER in the pass, not earlier.
It is the first entry in this note that runs BEFORE its source rather than
after, and the first to reach its source through a shared helper
(clearfell_common.coastal_differential_mm_yr) rather than by naming the path
in the script. `pipeline_lint --check deps` scans the numbered scripts for
path symbols and so does not see this read; it is registered here instead,
and the four differentials have rows in tools/defaults_basis.csv so that
defaults_lint checks the fallbacks against the CSV they mirror.

ON A FIRST PASS THIS MATTERS MORE THAN THE Sy CASES ABOVE. The drift
covariate is part of the published clearfell model, not a figure's
volumetric conversion, so a first pass takes the documented differentials
rather than the run's own. On a complete run — Script 25 having been run at
least once before — the live CSV is read and the defaults are never touched.
A first-pass 10a result is therefore provisional until the pipeline has been
round-tripped, which is the same rule the Sy cases carry, applied to a
number that reaches the headline.

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
import json
import os
import re
import time
import uuid
from collections import namedtuple
from pathlib import Path

__version__ = "2.8.0"  # 2026-08-31: Sets NRG_RUN_ID at the top of main(), so
#   every subprocess this run launches carries one token identifying the pass.
#   utils/site_observations.py stamps it into pipeline_site_observations.csv,
#   which is RUN-SCOPED: Script 01 resets it to placeholders and seven producers
#   overwrite their own rows, so a producer run OUTSIDE a pass silently makes the
#   file a mixture of two runs. The token has to come from HERE and not from the
#   file: a producer that read the existing token and wrote it back would make a
#   standalone write indistinguishable from an in-run one, which is the whole
#   defect. No step count or phase count changes. See D-101.
#
# v2.7.0  # 2026-08-29: Script 41 registered in Phase 16 (tier A,
#   default). _DOCUMENTED_COUNTS moves deliberately: registered 51 -> 52,
#   analytical top-level 41 -> 42, default 49. Phases unchanged at 17. The
#   version bump is part of the guard (D-088): registering a step without it
#   leaves a stale manifest indistinguishable from a current one.
# v2.6.0  # 2026-08-29: Script 40 registered in Phase 16 (tier A,
#   default). _DOCUMENTED_COUNTS moves deliberately: registered 50 -> 51,
#   analytical top-level 40 -> 41, default 47 -> 48. Phase count unchanged.
#   THIS BUMP IS PART OF A FIX, not bookkeeping. Script 40 was registered earlier
#   the same day WITHOUT bumping this, and a pipeline run from a tree predating
#   the registration then rewrote pipeline_manifest.json back to 50 steps with
#   Script 40 absent. Nothing noticed, because the manifest records
#   pipeline_version and the version had not moved: a stale manifest and a
#   current one were indistinguishable. build_manifest() now warns when it is
#   about to write an OLDER orchestrator version over a newer one, and
#   tools/manifest_lint.py gates the committed manifest against the live
#   orchestrator. Registering a step without bumping this is now a gate failure.
#
# v2.5.0  # 2026-08-21: Script 39 registered in Phase 16 (tier A,
#   default) — the SSM hindcast against the 1989-96 CCW record, the pipeline's
#   first out-of-sample validation. _DOCUMENTED_COUNTS moves deliberately:
#   registered 49 -> 50, analytical top-level 39 -> 40, default 46 -> 47.
#   Phase count unchanged. Script 39 skips cleanly if the CCW raw inputs are
#   absent, so a checkout without them still completes a full run.

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR  = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
OUT_DIR  = ROOT_DIR / "outputs"
# Mirrors utils.paths.pipeline_manifest() — this orchestrator does not import
# utils.paths (it keeps its own copies of the root path constants above), so
# the literal filename is kept in sync with that accessor by hand; both name
# the same physical file, outputs/pipeline_manifest.json.
OUT_MANIFEST = OUT_DIR / "pipeline_manifest.json"

# The manifest is a REGISTRY of what the pipeline contains, written on every run
# and by --manifest-only, so its `generated` field records when the registry was
# emitted and not that anything executed. On 2026-08-28 tools/output_lag.py read
# it as a run log and reported every script current while six sat edited and
# unrun. This is the run log the manifest was never claiming to be: one entry per
# step, written as each finishes, carrying the status the manifest cannot.
OUT_RUN_LOG = OUT_DIR / "pipeline_run_log.json"

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
# Every step is registered exactly once as a Step record. No step or phase
# TOTAL is ever typed in source — numbering is rendered at runtime from
# enumeration position over ALL_PHASES (see _build_all_steps() below), and
# outputs/pipeline_manifest.json is the citable artefact for current totals.
#
#   tier: "A" analytical | "D" display/utility | "X" opt-in diagnostic
#   exec: "default" (part of a normal --full run) | "optin" (--with-supplementary only)
#   n_substeps: 1, except the two sub-runner suites (run_09, run_10), whose
#               constituent module counts are read from MODULES / SUBSCRIPTS
#               in run_09_scraping.py / run_10_clearfell.py at manifest-build
#               time — see _substep_count() below.
Step = namedtuple("Step", "script desc tier exec n_substeps extra_args")
Step.__new__.__defaults__ = ("default", 1, ())

PHASE_1 = [
    Step("01_data_prep.py",              "Data preparation",                       "A"),
    Step("02_clustering.py",             "Behavioural clustering",                 "A"),
    Step("03_state_space_model.py",      "State-space regression + LCSC",          "A"),
    Step("04_cluster_visualisations.py", "Core cluster visualisation",             "A"),
]
PHASE_2 = [
    Step("05_pearson_affinity.py",  "Pearson membership audit",                    "A"),
    Step("06_pearson_extended.py",  "Pearson extended network integration",        "A"),
]
PHASE_3 = [
    Step("07_spatial_coefficients.py",     "Spatial coefficient mapping",                                          "A"),
    Step("08_model_benchmarking.py",       "Model benchmarking (LCSC vs Traditional)",                             "A"),
    Step("run_09_scraping.py",             "Scraping analysis suite (09a\u201309e)",                               "A"),
    Step("run_10_clearfell.py",            "Clear-fell BACI analysis suite (10a\u201310m)",                        "A"),
    Step("11_forecasting_thresholds.py",   "Forecasting and critical thresholds",                                  "A"),
    Step("11b_spatial_thresholds.py",      "Spatial eco-hydrological threshold maps",                              "A"),
    Step("11c_pflood_achievability.py",    "P_flood achievability categorical map (\u00a75.9 / Conclusion 4)",     "A"),
]
PHASE_4 = [
    Step("00_climate_summary.py",            "Climate summary outputs",                                                    "A"),
    Step("14_climate_projections.py",        "Figure: Climate trajectory projections",                                     "A"),
    Step("14b_year_of_crossing.py",          "Bootstrap year-of-crossing for Curreli thresholds (\u00a77 Conclusion 11)",  "A"),
    Step("12_figure_site_overview.py",       "Figure: DEM site overview",                                                  "A"),
    Step("13_figure_experimental_design.py", "Figure: Experimental design GIS map",                                        "A"),
]
PHASE_5 = [
    Step("15_depth_dependent_pet.py", "Depth-dependent PET analysis", "A"),
]
PHASE_6 = [
    Step("17_wtf_specific_yield.py", "WTF cluster Sy estimation", "A"),
]
PHASE_7 = [
    Step("16_water_bal.py", "Water balance decomposition", "A"),
]
PHASE_8 = [
    Step("18_wtf_spatial.py", "WTF spatial analysis and Sy mapping", "A"),
]
PHASE_9 = [
    Step("19_spatial_groundwater.py", "Spatial groundwater analysis", "A"),
    Step("20_spatial_figures.py",     "Spatial paper figures",        "A"),
]
PHASE_10 = [
    Step("21_forestry_scenarios.py", "Forestry scenarios and management figures", "A"),
]
PHASE_11 = [
    Step("25_coastal_gradient.py",   "Coastal-retreat gradient analysis", "A"),
]
PHASE_12 = [
    Step("22_residual_lag_analysis.py",    "Residual lag structure analysis",     "A"),
    Step("23_ridge_recharge_lag_test.py",  "Ridge recharge lag hypothesis test",  "A"),
    Step("24_residual_seasonality.py",     "Residual seasonality diagnostics",    "A"),
]
PHASE_13 = [
    Step("26_van_willegen_msl.py",              "Van Willegen (2025) 5-year MSL aggregation",                        "A"),
    Step("26b_van_willegen_msl_projections.py", "UKCP18 MSL5 climate projections (Tool B)",                          "A"),
    Step("26c_msl5_report_figures.py",          "MSL5 report-format figures (Figures for \u00a74.8.4 / \u00a74.10.1)", "D"),
]
PHASE_14 = [
    Step("28_c3_detrend_check.py",         "Cluster framework diagnostic: C3 detrend check (H0)",                                     "X"),
    Step("29_c3_within_variance_check.py", "Cluster framework diagnostic: within-C3 spatial structure",                               "X"),
    Step("30_c4_drainage_identifiability.py", "Cluster framework diagnostic: C4 drainage identifiability (tests \u03b22/\u03b23 separability; reports two sensitivities)", "X"),
]
PHASE_15 = [
    Step("32_differential_movement.py",  "Figure: secular differential water-table drift (report Fig 59)",                                                                        "A"),
    Step("33_envelope_amplification.py", "Figure: climate-swing amplification + drought-floor (report Fig 60)",                                                                    "A"),
    Step("35_per_well_amplification.py", "Figure+table: per-well climate-sensitivity coefficient (Paper 1; co-temporal, SSM-calibrated)",                                          "A"),
    Step("36_absolute_climate_trend.py", "Figure: absolute climate-removed per-well secular trend map (spring CWB detrended)",                                                     "A"),
    Step("37_driver_validation.py",      "Validation: predicted-vs-observed driver-change map (scatter + residual map)",                                                          "A"),
    Step("37b_driver_footing.py",        "Part B: comparative driver footing \u2014 forest \u00b7 scrape \u00b7 coast on common currencies (peak / area-integrated / ecological-threshold)", "A"),
]
PHASE_16 = [
    Step("24b_residual_climatology.py",         "Cluster-stratified residual climatology (supplementary diagnostic)",   "X", "optin"),
    Step("31_cluster_validation.py",            "Independent k=5 partition validation (supplementary diagnostic)",      "X", "optin"),
    Step("31b_separation_vs_recoverability.py", "Cluster separation vs recoverability (supplementary diagnostic)",      "X", "optin"),
    Step("34_window_sensitivity.py",            "MSL5 two-window sensitivity demonstration figure (\u00a75.7.5)",       "A"),
    Step("38_coastal_transect.py",              "Coast-to-inland MAM transect \u2014 observational delta_0 diagnostic (\u00a75.7)", "A"),
    Step("39_ccw_hindcast.py",                  "SSM hindcast against the 1989\u201396 CCW record \u2014 out-of-sample validation (\u00a75.7.8)", "A"),
    Step("40_shoreline_retreat.py",             "Shoreline retreat from the digitised coastline epochs \u2014 signed shore-normal displacement; WITHHOLDS its own headline until the gate passes (D-085)", "A"),
    Step("41_canopy_cover.py",                  "Canopy and forest-cover texture index from the dated aerial series \u2014 registration fitted from the dipwell placemarks; WITHHOLDS a value whose frame is unregistered. Skips when the imagery is absent, which is its normal state in a clone (D-081)", "A"),
]
PHASE_17 = [
    Step("09f_management_effects.py",  "Figure: management-interventions + coastal-retreat spatial reach (\u00a75.8; two-pass, reads Scripts 20/25/09d/10a)",   "D"),
    Step("09g_mechanism_diagrams.py",  "Figure: mechanism grid + coastal reach (\u00a75.8 conceptual; display only, reads 09f/10m/10a)", "D"),
    Step("27_greyscale_figures.py",    "Greyscale figure conversion (journal-ready B&W)",                                                                       "D"),
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
    ("PHASE 15 \u2014 Observed Differential Change, Envelope, and Driver Validation (Scripts 32, 33, 35, 36, 37, 37b)", PHASE_15),
    ("PHASE 16 \u2014 Window Sensitivity, Coastal Transect, and Supplementary Cluster Diagnostics (Scripts 34, 38 default; 24b, 31, 31b opt-in)", PHASE_16),
    ("PHASE 17 \u2014 Synthesis Figures and Greyscale Conversion (Scripts 09f, 09g, 27)",  PHASE_17),
]

# ── Document-drift guard ─────────────────────────────────────────────────────
# NOTHING here feeds an output. Every count in the manifest is computed from
# ALL_PHASES in build_manifest(). This table records only what the report,
# Methods Supplement, readme.md, PIPELINE_README.md and index.html currently
# STATE, so that changing the step table warns which documents now need
# re-editing, naming the field that moved.
#
# Design note: there is deliberately no single hand-maintained "analytical
# headline" constant. Earlier revisions declared one and it drifted from the
# step table in two ways at once — it was carried across a redefinition of the
# tier categories without re-derivation, and it collided numerically with an
# unrelated count on a different axis, so document sentences mixing the two
# read plausibly and were wrong. Every count below is checked against a value
# recomputed from ALL_PHASES. Documents cite manifest fields; the short-form
# headline is the total registered count.
# 2026-08-21: Script 39 registered (Phase 16, tier A, default). This is a
# DELIBERATE change to the analytical core, so analytical_toplevel and the
# registered total both move; the guard below is what makes that visible rather
# than silent. Script 39 is the first out-of-sample validation of the SSM in
# this pipeline and is cited in the report, which is what puts it in tier A
# rather than among the opt-in diagnostics.
_DOCUMENTED_COUNTS = {
    "total_registered":            52,
    "total_phases":                17,
    "by_tier.analytical_toplevel": 42,
    "by_tier.display_utility":      4,
    "by_tier.optin_diagnostic":     6,
    "by_exec.default":             49,
    "by_exec.optin":                3,
    "analytical_phases":           15,   # phases carrying >=1 tier-A step; emitted
                                         # for completeness, NOT cited in any document
}

RenderedStep = namedtuple(
    "RenderedStep",
    "index total script desc tier exec n_substeps phase_label extra_args label"
)


def _substep_count(script: str) -> int:
    """Constituent-module count for the two sub-runner suites, read from
    their own MODULES / SUBSCRIPTS registries rather than typed here."""
    try:
        if str(SRC_DIR) not in sys.path:
            sys.path.insert(0, str(SRC_DIR))
        if script == "run_09_scraping.py":
            import run_09_scraping
            return len(run_09_scraping.MODULES)
        if script == "run_10_clearfell.py":
            import run_10_clearfell
            return len(run_10_clearfell.SUBSCRIPTS)
    except Exception:
        pass
    return 1


def _build_all_steps() -> list:
    """Flatten ALL_PHASES into RenderedStep records with runtime-computed
    index/total/label — the single place step numbering is derived."""
    flat = []
    for _phase_label, _phase_entries in ALL_PHASES:
        for _st in _phase_entries:
            flat.append((_phase_label, _st))
    total = len(flat)
    width = len(str(total))
    out = []
    for i, (_phase_label, _st) in enumerate(flat, start=1):
        n_sub = _st.n_substeps
        if _st.script in ("run_09_scraping.py", "run_10_clearfell.py") and n_sub == 1:
            n_sub = _substep_count(_st.script)
        label = f"{i:>{width}}/{total}  {_st.desc}"
        out.append(RenderedStep(i, total, _st.script, _st.desc, _st.tier, _st.exec,
                                 n_sub, _phase_label, list(_st.extra_args), label))
    return out


_ALL_STEPS: list = _build_all_steps()

# Legacy-compatible {index: (script, label, extra_args)} lookup — kept in
# this exact shape because utils/pipeline_deps.py and the menu_run_from() /
# menu_run_single() helpers below consume it directly.
_STEP_MAP: dict[int, tuple[str, str, list]] = {
    rs.index: (rs.script, rs.label, rs.extra_args) for rs in _ALL_STEPS
}
_STEP_BY_SCRIPT: dict[str, "RenderedStep"] = {rs.script: rs for rs in _ALL_STEPS}
_STEPS_BY_PHASE: dict[str, list] = {}
for _rs in _ALL_STEPS:
    _STEPS_BY_PHASE.setdefault(_rs.phase_label, []).append(_rs)


def _compress_ranges(indices: list) -> str:
    """Compress a sorted-or-not list of ints into 'a–b, c, d–e' form."""
    if not indices:
        return ""
    idx = sorted(indices)
    ranges = []
    start = prev = idx[0]
    for n in idx[1:]:
        if n == prev + 1:
            prev = n
            continue
        ranges.append((start, prev))
        start = prev = n
    ranges.append((start, prev))
    return ", ".join(f"{a}" if a == b else f"{a}\u2013{b}" for a, b in ranges)


def _ver_tuple(v: str) -> tuple:
    """Dotted version as a comparable tuple; unparseable parts sort as 0."""
    out = []
    for part in str(v).split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out)


def build_manifest(write: bool = True) -> dict:
    """Build (and, by default, write) outputs/pipeline_manifest.json — the
    committed, machine-readable source of truth for step/phase totals and
    per-step tags. Also runs the analytical-count drift guard."""
    by_tier = {"analytical_toplevel": 0, "display_utility": 0, "optin_diagnostic": 0}
    by_exec = {"default": 0, "optin": 0}
    steps_out = []
    for rs in _ALL_STEPS:
        if rs.tier == "A":
            by_tier["analytical_toplevel"] += 1
        elif rs.tier == "D":
            by_tier["display_utility"] += 1
        elif rs.tier == "X":
            by_tier["optin_diagnostic"] += 1
        by_exec[rs.exec] = by_exec.get(rs.exec, 0) + 1
        steps_out.append({
            "index": rs.index, "total": rs.total, "script": rs.script,
            "desc": rs.desc, "tier": rs.tier, "exec": rs.exec,
        })
    # Phase counts, derived. total_phases is the citable figure; analytical_phases
    # counts phases carrying at least one tier-"A" step (Phase 14 is all tier X and
    # Phase 17 all tier D, so it is not the same as total_phases).
    analytical_phases = sum(
        1 for _label, _steps in ALL_PHASES if any(s.tier == "A" for s in _steps)
    )
    manifest = {
        "pipeline_version": __version__,
        "total_registered": len(_ALL_STEPS),
        "total_phases": len(ALL_PHASES),
        "by_tier": by_tier,
        "by_exec": by_exec,
        "analytical_phases": analytical_phases,
        "scraping_substeps": _STEP_BY_SCRIPT["run_09_scraping.py"].n_substeps,
        "clearfell_substeps": _STEP_BY_SCRIPT["run_10_clearfell.py"].n_substeps,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "steps": steps_out,
    }
    if write:
        # Refuse to downgrade SILENTLY. A run from a tree older than the one that
        # last wrote this file reverted it to 50 steps on 2026-08-29, dropping a
        # registered script, and nothing noticed until a git status looked odd.
        try:
            prior = json.loads(OUT_MANIFEST.read_text(encoding="utf-8"))
            pv = str(prior.get("pipeline_version", ""))
            if pv and _ver_tuple(pv) > _ver_tuple(__version__):
                print(f"  [WARNING] the manifest on disk was written by orchestrator "
                      f"{pv}, which is NEWER than this one ({__version__}). Writing "
                      f"it anyway would be a DOWNGRADE — check you are on the "
                      f"current tree before trusting the result.")
            elif pv and _ver_tuple(pv) == _ver_tuple(__version__) and \
                    prior.get("total_registered") != manifest["total_registered"]:
                print(f"  [WARNING] same orchestrator version ({pv}) but the step "
                      f"count moved {prior.get('total_registered')} -> "
                      f"{manifest['total_registered']}. Bump __version__ when the "
                      f"registry changes, or a stale manifest cannot be told from "
                      f"a current one.")
        except Exception:
            pass
        OUT_DIR.mkdir(exist_ok=True)
        with open(OUT_MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
    _check_documented_counts(manifest)
    _check_version_guard()
    return manifest


def _check_version_guard() -> None:
    """Report the pipeline release this run belongs to.

    The release string in utils.config is a RELEASE identifier and moves only at
    a release; every script, this orchestrator included, carries its own module
    __version__ and bumps on any edit — adding an output to one script bumps that
    script and nothing else. A module version ahead of the release string is
    therefore the normal state between releases and is not reported as a fault.
    Lazy import keeps the orchestrator runnable standalone if utils is
    unavailable.
    """
    try:
        if str(SRC_DIR) not in sys.path:
            sys.path.insert(0, str(SRC_DIR))
        from utils.config import PIPELINE_VERSION as _rel
        from utils.config import PIPELINE_RELEASE_DATE as _rel_date
    except Exception:
        return
    say_info(f"pipeline release {_rel} ({_rel_date}); "
             f"orchestrator module v{__version__}")


def _manifest_field(manifest: dict, dotted: str):
    """Fetch a manifest value by dotted key ('by_tier.display_utility')."""
    value = manifest
    for part in dotted.split("."):
        value = value[part]
    return value


def _check_documented_counts(manifest: dict) -> None:
    """Warn for every manifest count that has drifted from what the documents
    currently state (see _DOCUMENTED_COUNTS). Recomputed from the step table on
    every build — no count is ever taken from the table below."""
    drifted = []
    for key, stated in _DOCUMENTED_COUNTS.items():
        try:
            actual = _manifest_field(manifest, key)
        except (KeyError, TypeError):
            drifted.append(f"{key}: no longer present in the manifest")
            continue
        if actual != stated:
            drifted.append(f"{key}: documents say {stated}, manifest now {actual}")
    if not drifted:
        return
    say_warn(
        f"Pipeline counts have drifted from the documents ({len(drifted)} field"
        f"{'s' if len(drifted) != 1 else ''}) \u2014 update the documents and "
        "_DOCUMENTED_COUNTS together:"
    )
    for line in drifted:
        say_info(f"    {line}")
    say_info("    cite outputs/pipeline_manifest.json; never add the tier and "
             "exec breakdowns together.")

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
    (_STEP_BY_SCRIPT["04_cluster_visualisations.py"].index + 1, REQUIRED_PHASE1_OUTPUTS,
     f"Phase 1 (steps {_compress_ranges([rs.index for rs in _STEPS_BY_PHASE[ALL_PHASES[0][0]]])})"),
    (_STEP_BY_SCRIPT["run_10_clearfell.py"].index + 1, REQUIRED_PHASE3_OUTPUTS,
     f"Phase 3 (steps {_compress_ranges([rs.index for rs in _STEPS_BY_PHASE[ALL_PHASES[2][0]]])})"),
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


def _record_run(script_name: str, status: str, seconds: float, label: str) -> None:
    """Append one step's outcome to outputs/pipeline_run_log.json.

    Written AS EACH STEP FINISHES, not at the end, so a run that dies at step 30
    still records the twenty-nine that completed — which is the whole difference
    between this and the manifest's single `generated` stamp.

    Records `status`, so a script that ran and failed is distinguishable from one
    that ran and succeeded. `tools/output_lag.py` needs exactly that: a failed
    step has not produced current outputs however recently it executed.

    Wrapped so that nothing here can stop a pipeline run. A run record is a
    convenience; losing it must never cost an hour of compute.
    """
    try:
        import json as _json
        from datetime import datetime as _dt
        log = {}
        if OUT_RUN_LOG.exists():
            try:
                log = _json.loads(OUT_RUN_LOG.read_text(encoding="utf8"))
            except (ValueError, OSError):
                log = {}
        log.setdefault("scripts", {})[script_name] = {
            "last_run": _dt.now().isoformat(timespec="seconds"),
            "status":   status,
            "seconds":  round(float(seconds), 1),
            "step":     label,
        }
        log["updated"] = _dt.now().isoformat(timespec="seconds")
        OUT_RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
        OUT_RUN_LOG.write_text(_json.dumps(log, indent=1, sort_keys=True) + "\n",
                               encoding="utf8")
    except Exception:                                     # noqa: BLE001
        pass


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
        _record_run(script_name, "failed", time.time() - t0, step_txt)
        raise
    dt = time.time() - t0
    _record_run(script_name, "ok", dt, step_txt)
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

def run_phase(phase_label: str, from_step: int = 1, include_optin: bool = False,
              exclude_scripts: tuple = ()) -> None:
    """Run every registered step in a phase, in enumeration order.

    A step is skipped (with a console note) if: its index is below
    from_step; its exec=="optin" and include_optin is False; or its script
    is named in exclude_scripts (used for Script 27, which never auto-runs
    even though it's tier D like Script 09f — see run_full_pipeline()).
    """
    steps = _STEPS_BY_PHASE.get(phase_label, [])
    print()
    print(paint("━" * 70, _Ansi.CYAN))
    print("  " + paint(phase_label, _Ansi.BCYAN, _Ansi.BOLD))
    print(paint("━" * 70, _Ansi.CYAN))
    for rs in steps:
        if rs.script in exclude_scripts:
            continue
        if rs.exec == "optin" and not include_optin:
            print("  " + paint(
                f"{GLYPH_SKIP} skip step {rs.label.strip()}  (opt-in — use --with-supplementary)",
                _Ansi.GREY))
            continue
        if rs.index < from_step:
            print("  " + paint(f"{GLYPH_SKIP} skip step {rs.label.strip()}", _Ansi.GREY))
            continue
        run_script(rs.script, rs.label, rs.extra_args)

# ── Pipeline runners ──────────────────────────────────────────────────────────

def run_full_pipeline(from_step: int = 1, include_supplementary: bool = False) -> None:
    ensure_paths()
    build_manifest(write=True)
    _t_start = time.time()

    _PHASE17_LABEL = ALL_PHASES[-1][0]
    for phase_label, _phase_entries in ALL_PHASES:
        if phase_label == _PHASE17_LABEL:
            continue  # handled below — 09f auto-runs, greyscale never does
        run_phase(phase_label, from_step, include_optin=include_supplementary)
        # Post-phase validation checkpoints, keyed off a specific step's
        # script name (not a typed step number) so they track automatically
        # if a phase's step range shifts.
        if phase_label == ALL_PHASES[0][0] and from_step <= _STEP_BY_SCRIPT["04_cluster_visualisations.py"].index:
            validate_outputs(REQUIRED_PHASE1_OUTPUTS, "Phase 1")
        if phase_label == ALL_PHASES[2][0] and from_step <= _STEP_BY_SCRIPT["run_10_clearfell.py"].index:
            validate_outputs(REQUIRED_PHASE3_OUTPUTS, "Phase 3")
        if phase_label == ALL_PHASES[8][0] and from_step <= _STEP_BY_SCRIPT["20_spatial_figures.py"].index:
            # Derived from the step table rather than hard-typed, so it
            # survives phase reordering.
            validate_outputs(REQUIRED_PHASE9_OUTPUTS, "Phase 9")
        if phase_label == ALL_PHASES[9][0]:
            validate_outputs(REQUIRED_PHASE10_OUTPUTS, "Phase 10")

    # Phase 17 — the synthesis figure (Script 09f) auto-runs as part of a
    # normal full run (its upstream inputs already exist by this point in
    # the pass); greyscale (Script 27) never auto-runs — it's invoked on
    # demand via run_greyscale() (menu option 6 / --greyscale).
    run_phase(_PHASE17_LABEL, from_step, include_optin=include_supplementary,
              exclude_scripts=("27_greyscale_figures.py",))

    executed = [rs.index for rs in _ALL_STEPS
                if rs.index >= from_step
                and rs.script != "27_greyscale_figures.py"
                and (rs.exec == "default" or include_supplementary)]
    last_step = max(executed) if executed else from_step - 1

    _elapsed = (time.time() - _t_start) / 60.0
    print()
    _banner(f"PIPELINE COMPLETE  \u00b7  steps 1\u2013{last_step} written to outputs/", _Ansi.BGREEN)
    optin_steps = [rs for rs in _ALL_STEPS if rs.exec == "optin"]
    if not include_supplementary and optin_steps:
        idx_range = _compress_ranges([rs.index for rs in optin_steps])
        scripts = ", ".join(rs.script for rs in optin_steps)
        say_info(f"opt-in diagnostics (steps {idx_range}: {scripts}) NOT run "
                 "\u2014 add --with-supplementary (or choose it in menu option 1) to include them")
    _grey = _STEP_BY_SCRIPT["27_greyscale_figures.py"]
    say_info(f"greyscale (step {_grey.index}) runs separately (menu option 6 / --greyscale)")
    say_info(f"pipeline_manifest.json written to {OUT_MANIFEST}")
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

    # Script 19 needs all upstream Phase 1-8 outputs to exist.
    if not warn_missing_upstream(_STEP_BY_SCRIPT[VIEWER_SCRIPT].index):
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
    _default_idx = [rs.index for rs in _ALL_STEPS if rs.exec == "default"
                     and rs.script != "27_greyscale_figures.py"]
    _optin_idx   = [rs.index for rs in _ALL_STEPS if rs.exec == "optin"]
    _phase12_idx = [rs.index for rs in _STEPS_BY_PHASE[ALL_PHASES[11][0]]]
    out = [
        "",
        hint("  First run / new dataset → option 1 (full pipeline). For canonical"),
        hint("  scenario figures, run the full pipeline twice. Options 2–6 require the"),
        hint("  full pipeline to have completed at least once."),
        "",
        "  " + rule,
        "  " + grp("RUN"),
        f"    {num('1')}   Full pipeline             " + hint(
            f"steps {_compress_ranges(_default_idx)} "
            f"(+{_compress_ranges(_optin_idx)} opt-in) · run twice for new data"),
        f"    {num('2')}   Resume from a step        " + hint("pick up mid-pipeline"),
        f"    {num('3')}   Run a single step",
        "",
        "  " + grp("TOOLS"),
        f"    {num('4')}   Build scenario viewer     " + hint("standalone HTML"),
        f"    {num('5')}   Supplementary diagnostics " + hint(
            f"steps {_compress_ranges(_phase12_idx)} (Scripts 22–24)"),
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
    for phase_label, _phase_entries in ALL_PHASES:
        print("\n  " + paint(phase_label, _Ansi.BCYAN, _Ansi.BOLD))
        for rs in _STEPS_BY_PHASE.get(phase_label, []):
            present = (SRC_DIR / rs.script).exists()
            tag = paint(GLYPH_OK, _Ansi.GREEN) if present else paint(GLYPH_FAIL, _Ansi.BRED)
            optin_tag = paint(" [opt-in]", _Ansi.YELLOW) if rs.exec == "optin" else ""
            print(f"    {tag}  " + paint(f"step {rs.index:>2}", _Ansi.BOLD)
                  + f"  {rs.script}{optin_tag}")
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
            run_script(_STEP_BY_SCRIPT["27_greyscale_figures.py"].script, _STEP_BY_SCRIPT["27_greyscale_figures.py"].label)
            bw_dir = ROOT_DIR / "outputs_bw"
            if bw_dir.exists():
                n_figs = len(list(bw_dir.rglob("*.png"))) + len(list(bw_dir.rglob("*.jpg")))
                print(f"  [OK] {n_figs} figures in outputs_bw/")

def run_supplementary() -> None:
    """Run supplementary diagnostic scripts 22–24."""
    ensure_paths()
    _phase12_label = ALL_PHASES[11][0]
    _first_idx = _STEPS_BY_PHASE[_phase12_label][0].index
    if not warn_missing_upstream(_first_idx):
        print("  Aborted.")
        return
    run_phase(_phase12_label)
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
        _n_bw = len([rs for rs in _ALL_STEPS
                     if rs.exec == "default"
                     and rs.script != "27_greyscale_figures.py"])
        print(f"  This will re-run all {_n_bw} steps with BW_MODE=True,")
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
        run_script(_STEP_BY_SCRIPT["27_greyscale_figures.py"].script, _STEP_BY_SCRIPT["27_greyscale_figures.py"].label)

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

    print("\n" + H("  Pipeline structure")
          + D(f"   ({len(_ALL_STEPS)} steps registered across {len(ALL_PHASES)} phases; "
              f"see outputs/pipeline_manifest.json)"))
    for phase_label, _phase_entries in ALL_PHASES:
        idxs = [rs.index for rs in _STEPS_BY_PHASE.get(phase_label, [])]
        rng = f"step {idxs[0]}" if len(idxs) == 1 else f"steps {idxs[0]}\u2013{idxs[-1]}" if idxs else ""
        print("    " + paint(phase_label, _Ansi.CYAN) + D(f"   ({rng})"))
    _default_idx = [rs.index for rs in _ALL_STEPS if rs.exec == "default"
                     and rs.script != "27_greyscale_figures.py"]
    _optin_idx   = [rs.index for rs in _ALL_STEPS if rs.exec == "optin"]
    _grey_idx    = _STEP_BY_SCRIPT["27_greyscale_figures.py"].index
    print(D(f"\n  A full run executes steps {_compress_ranges(_default_idx)}. The opt-in"))
    print(D(f"  diagnostic tier (steps {_compress_ranges(_optin_idx)}) runs only with"))
    print(D("  --with-supplementary or the option 1 prompt; greyscale (step "
            f"{_grey_idx}) runs separately via option 6 / --greyscale."))

    print("\n" + H("  Menu options"))
    opts = [
        ("1", "Full pipeline", f"runs steps {_compress_ranges(_default_idx)} (opt-in diagnostics available); offers to save a console log"),
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
    print("  by Scripts 17/18 (see pipeline_manifest.json for their current step")
    print("  indices). On a first pass they fall back to documented Newborough")
    print("  defaults (0.20 cluster, 0.30 CEH36) with warnings — results are")
    print("  unaffected. For canonical scenario figures, run again from the scraping")
    print("  suite's step (Script run_09_scraping.py, which contains 09b/09d):")
    idx9 = _STEP_BY_SCRIPT["run_09_scraping.py"].index
    print(D(f"     pass 1: option 1     pass 2: option 2 \u2192 step {idx9}"))

    print("\n" + H("  Console logging"))
    print("  Option 1 (and --full --log) can mirror everything printed — the")
    print("  orchestrator and every child script — to a timestamped log:")
    print(D("     outputs/logs/run_<YYYYMMDD_HHMMSS>.log"))

    print("\n" + H("  Command line"))
    cli = [
        (f"--full [--log [PATH]]", f"run steps {_compress_ranges(_default_idx)} (optionally log to file)"),
        ("--with-supplementary", f"with --full/--from: also run the opt-in diagnostic tier (steps {_compress_ranges(_optin_idx)})"),
        ("--clusters N", "clustering target K for the partition (default 5)"),
        ("--from N", "resume from step N"),
        ("--viewer", "build the scenario viewer only"),
        ("--supplementary", "run Scripts 22–24 only"),
        ("--greyscale", "quick pixel greyscale convert"),
        ("--greyscale-full", "full B&W pipeline re-run (best quality)"),
        ("--manifest-only", "write outputs/pipeline_manifest.json without running any steps"),
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
            _idx17 = _STEP_BY_SCRIPT["17_wtf_specific_yield.py"].index
            _idx18 = _STEP_BY_SCRIPT["18_wtf_spatial.py"].index
            _idx9  = _STEP_BY_SCRIPT["run_09_scraping.py"].index
            print(
                "\n  NOTE: Two scripts in Phase 3 (09b, 09d) read Sy values\n"
                f"  produced later in the pipeline (steps {_idx17} and {_idx18}). On a fresh\n"
                "  first-pass run they will use documented fallbacks with\n"
                "  console warnings — this does not break the pipeline.\n\n"
                "  For canonical scenario figures on a new dataset, run twice:\n"
                "    pass 1: this option (full pipeline)\n"
                f"    pass 2: option 2, resume from step {_idx9}\n"
                "  See module docstring for details."
            )
            _default_idx = [rs.index for rs in _ALL_STEPS if rs.exec == "default"
                             and rs.script != "27_greyscale_figures.py"]
            ans = input(f"\n  Run the full pipeline (steps {_compress_ranges(_default_idx)}) "
                        "from the beginning? [y/N] ").strip().lower()
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
                _optin_idx = [rs.index for rs in _ALL_STEPS if rs.exec == "optin"]
                _optin_scripts = ", ".join(rs.script for rs in _ALL_STEPS if rs.exec == "optin")
                supp = input(
                    "  Also run the opt-in diagnostic tier\n"
                    f"  (steps {_compress_ranges(_optin_idx)}: {_optin_scripts})? [y/N] "
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
    _default_idx = [rs.index for rs in _ALL_STEPS if rs.exec == "default"
                     and rs.script != "27_greyscale_figures.py"]
    _optin_idx   = [rs.index for rs in _ALL_STEPS if rs.exec == "optin"]
    _optin_scripts = ", ".join(rs.script for rs in _ALL_STEPS if rs.exec == "optin")
    parser = argparse.ArgumentParser(
        description="Newborough Warren analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Run without arguments for the interactive menu.
            Use --full, --from, --viewer, --supplementary, or --greyscale for non-interactive execution.
            Add --log to a --full run to record all console output to a log file.
            --manifest-only writes outputs/pipeline_manifest.json without running any steps.
            --explain prints the in-app help page; --no-colour disables coloured output.
            --deps prints the down-pipeline (backward) dependency audit and exits.
        """)
    )
    parser.add_argument("--full",   action="store_true",
                        help=f"Run all {len(_default_idx)} default-tier steps "
                             f"(steps {_compress_ranges(_default_idx)}) non-interactively")
    parser.add_argument("--with-supplementary", dest="with_supplementary",
                        action="store_true",
                        help="With --full/--from: also run every opt-in "
                             f"diagnostic step (steps {_compress_ranges(_optin_idx)}: "
                             f"{_optin_scripts})")
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
    parser.add_argument("--manifest-only", dest="manifest_only", action="store_true",
                        help="Write outputs/pipeline_manifest.json and exit "
                             "(no steps are run)")
    parser.add_argument("--no-colour", "--no-color", dest="no_colour",
                        action="store_true", help="Disable coloured console output")
    parser.add_argument("--explain", action="store_true",
                        help="Print the in-app help page and exit")
    parser.add_argument("--deps", action="store_true",
                        help="Print the down-pipeline dependency audit and exit")
    args = parser.parse_args()

    _init_colour(disable=args.no_colour)

    # ONE token per pass, set before anything is launched so every child
    # inherits it (steps run as subprocesses via _run_subprocess, and the
    # sub-runners' own children inherit in turn). Idiomatic here: NRG_N_CLUSTERS
    # below and NRG_BW_MODE already travel the same way.
    #
    # It is set unconditionally, including on the paths that return early
    # without running a step (--manifest-only, --explain, --deps) and on the
    # interactive menu, because the menu runs steps too and a token set only on
    # --full would leave interactive runs looking standalone.
    #
    # THE POINT IS WHERE IT COMES FROM. utils/site_observations.py reads this
    # from the environment and never from the file it is writing. A script run
    # on its own inherits no token, so its row is marked standalone and both the
    # console warning and tools/pipeline_lint.py --check runid can see it. If
    # producers took the token from the existing file instead, a standalone run
    # would copy the previous pass's token forward and the pollution would be
    # invisible — which is exactly the failure this guards (D-101).
    os.environ["NRG_RUN_ID"] = (
        f"run:{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}"
        f"-{uuid.uuid4().hex[:6]}")

    if args.manifest_only:
        _manifest = build_manifest(write=True)
        say_ok(f"Wrote {OUT_MANIFEST} "
               f"({_manifest['total_registered']} steps registered)")
        return

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
