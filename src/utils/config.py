"""
utils/config.py
Shared constants for cluster colours, labels, and DEM rendering scale.
All scripts import from here so that palette and scale changes propagate everywhere.

The current partition is k=5 (see 02_clustering.py CLUSTER_PARTITIONING_CONFIG
docstring for the rationale). CLUSTER_COLOURS and CLUSTER_MARKERS keep a C6
entry reserved for future extension, but CLUSTER_LABELS is authoritative for
which cluster IDs are currently in use — downstream code that needs to iterate
over "all clusters" should iterate over CLUSTER_LABELS.keys().
"""

# ── Pipeline version ─────────────────────────────────────────────────────────
# Single canonical version string for the analysis pipeline. build_manifest()
# stamps it into outputs/pipeline_manifest.json, so the manifest, the Methods
# Supplement / SI and the Zenodo release all pin to one string.
#
# This is a RELEASE identifier and moves only at a release. Individual scripts —
# including run_analysis.py — carry their own module __version__ and bump on any
# edit, so a script version ahead of this string is the normal state between
# releases and is not a defect. Adding an output to a script bumps that script
# and nothing else.
#
# Releases are dated. PIPELINE_RELEASE_DATE is the date this release string was
# cut, in ISO form, and travels with it into the manifest so a reader can tell
# which vintage of the pipeline produced a figure without reading a changelog.
PIPELINE_VERSION = "2.3.0"
PIPELINE_RELEASE_DATE = "2026-08-13"    # ISO date this release string was cut

# ── Module version ───────────────────────────────────────────────────────────
# Version of this config module itself (distinct from PIPELINE_VERSION, the
# release-level string above). Introduced 2026-08-13; pre-1.1.0 history via
# CHANGELOG_delta files. Bump on ANY edit, as for pipeline scripts.
# v1.1.0 (2026-08-13): __version__ introduced; no functional change.
# v1.2.0 (2026-08-16): LCSC_DATA_LIMIT centralised here from three independent
#   module-local declarations (model_utils, Scripts 03 and 08). Value unchanged
#   at 100; see D-016.
# v1.3.0 (2026-08-16): month-wise cluster-stability parameters added (D-030).
# v1.4.2 (2026-08-18): the CEH14 entry in MSL5_EXCLUDED_WELLS carried a pipeline
#   result as a literal — "NSE -3.21" — against the no-hardcoded-values rule,
#   and it had drifted. The reason string now names the condition without the
#   number; the value lives in 08_perwell_nse.csv. Behaviour unchanged.
__version__ = "1.28.1"  # Hollingham (2026) - 2026-09-04. W66: BL_CANOPY_FRACTION_2005
#   basis corrected - 0.4 is confirmed against the aerial photography at the
#   2005/2006 baseline (observation-anchored), not a seasons-since-restock
#   judgement, so the D-082 restock-year change (1998->1995) does not move it.
#   Comment only; value unchanged; no figure regenerated.
#
# v1.28.0  # Hollingham (2026) — 2026-09-02. COVARIATE_SWEEP_HALF_LIVES_MO,
#   the memory half-lives of Script 25's climate-covariate specification sweep
#   (25_15, W136). Additive only; no existing constant changes.
#
# v1.27.0  # Hollingham (2026) — 2026-08-31. CANOPY_MAX_GSD_M, the
#   resolution gate. Recovering the site* frames worked and produced numbers that
#   measure nothing: r = +0.089 against the aerial index of the same region on
#   the same day. Checking a number badly is worse than not checking it, so the
#   coarse viewpoints are now WITHHELD with the reason, on a measured ground
#   sampling distance rather than a list of filenames.

# v1.26.0  # Hollingham (2026) — 2026-08-31. Script 41 v2.1.0:
#   the registration constants. The frames fall into five constellation groups
#   and every one of them was being seeded from the first frame's affine, which
#   is why the site* viewpoint (91 px away) and the 2026 aerial frame (49 px
#   from its own group, against a 45 px radius) could not register however well
#   their markers were detected. Also corrects the v1.25.0 crop fractions, which
#   assumed a 1200 x 1920 frame when the frames are 1920 x 1080.

# v1.25.0  # Hollingham (2026) — 2026-08-31. Script 41 v2.0.0:
#   marker-detection, framing and change-grid constants lifted out of the script
#   (they were literals tuned to the large marker symbol, and rejected every
#   small one), plus the four LEAF_*_MONTHS classes. The leaf classes are named
#   for leaf state rather than season under D-100, because they answer a
#   different question from any seasonal window and merging them would be a
#   methodological change, not a tidy-up.

# v1.24.0  # Hollingham (2026) — 2026-08-31. Detectability
#   settings are named for the QUANTITY, not for the script that first needed
#   them: DETECTABILITY_ALPHA / DETECTABILITY_POWER, with Script 32's
#   DIFF_POWER_ALPHA / DIFF_POWER_TARGET kept as aliases so nothing that imports
#   them changes and no value moves. Script 09a's BACI detectability floor needs
#   the same two numbers, and a second copy of 0.05 and 0.80 is the duplication
#   this file exists to prevent. Adds BACI_DETECT_MIN_ERA_MONTHS and
#   BACI_DETECT_HORIZON_YEARS. See D-103.
#
# v1.23.0  # Hollingham (2026) — 2026-08-31. THE FOUR SUMMERS.
#   Batch two of the seasonal-windows spec: SUMMER_MINIMUM_MONTHS,
#   SUMMER_DROUGHT_MONTHS, SUMMER_DRY_CLIMATE_MONTHS and
#   SUMMER_METEOROLOGICAL_MONTHS, replacing nine per-script locals across
#   five distinct month-sets. Summer was the larger duplication and the
#   quieter one: SUMMER_MINIMUM_MONTHS alone was written out seven times.
#   No window's months change and no committed value moves. Script 02's
#   AMP_SUMMER_MONTHS and Script 29's WINTER_MONTHS are deliberately NOT
#   folded in — same months, different questions. See D-100.
#
# v1.22.0  # Hollingham (2026) — 2026-08-30. THE FOUR WINTERS.
#   Batch one of the seasonal-windows spec: WINTER_RECHARGE_MONTHS,
#   WINTER_WET_CLIMATE_MONTHS, WINTER_RECESSION_MONTHS and
#   WINTER_METEOROLOGICAL_MONTHS, replacing seven per-script locals all
#   called WINTER_MONTHS and meaning four different things. Named for what
#   each window IS FOR, not for the season, because the season name is
#   exactly what made four incompatible definitions look interchangeable.
#   Summer and spring are batch two. See D-100.
#
# v1.21.0  # Hollingham (2026) — 2026-08-30. Adds the BREAK_*
#   block: the detection parameters for the northern break in slope measured by
#   Script 12, and the two gate tolerances that withhold it. Every number in the
#   block is a PARAMETER of the detector; the results live in
#   12_02_break_in_slope.csv. See D-099.
#
# v1.20.0  # Hollingham (2026) — 2026-08-29. COAST_RETREAT_RATE is
#   SUPERSEDED (D-090): no script divides by it any more. The divisor in the
#   coastal edge-drawdown construction is now measured by Script 40 over a window
#   matched to delta_0's fit span, read live by utils.coastal_utils, with the
#   first-pass fallback in pipeline_params where D-075 says a fitted value
#   belongs. h0 moves 22.65 -> 81.00 mm. The constant is retained only for
#   Script 40's comparison row and for the documents still citing it.
# v1.19.0  # Hollingham (2026) — 2026-08-29. The two Script 40 gate
#   tolerances are SET, from observation rather than guess (D-089): a blind
#   second tracing of the 1/1/2006 imagery gives an independent
#   digitising-plus-registration error of 2.34 m median / 5.53 m p95, so
#   SHORE_CONTROL_TOLERANCE_M = 6.0; the measured sagitta bound is 3.829 m, so
#   SHORE_GENERALISATION_TOLERANCE_M = 5.0. Both can fail on real data.
# v1.18.0  # Hollingham (2026) — 2026-08-29. Constants for Script 40,
#   the shoreline-retreat measurement (spec signed off). SHORE_NORMAL_SPACING_M,
#   SHORE_NORMAL_MAX_RANGE_M and PUBLISHED_MAX_PROFILE_RATE (Pye & Blott 2024,
#   carrying its dune-toe indicator with it). The two gate tolerances are
#   declared as None on purpose: the spec forbids choosing them before the
#   distributions they judge exist, and Script 40 treats None as failing.
# v1.17.0  # Hollingham (2026) — 2026-08-29. COAST_RETREAT_EFFECTIVE_M
#   (105 m) WITHDRAWN (W80). It was an input to a Script 37 construction that the
#   script no longer performs, and the successor — a fitted coastal scale factor
#   of 0.51, CI −0.10 to 1.12 — disagrees with it by a factor of about four and
#   does not resolve from zero. Read by nothing; quoted by one report sentence,
#   which is rewritten in the same batch. COAST_RETREAT_2005_2025_M is KEPT: it
#   is an external observation, and D-075 puts inputs in this file.
# v1.16.0  # Hollingham (2026) — 2026-08-29. Coastal-retreat
#   commentary corrected (W77). THREE defects, all in comments, no value changed.
#   (1) One Forgrave ≈50 m was cited to two incompatible windows — "2014–2020"
#   for COAST_RETREAT_RATE (50/6 ≈ 8.3) and "since 2006" for
#   COAST_RETREAT_2005_2025_M (50/14 ≈ 3.6). No window is asserted now; the
#   dispute is recorded (D-085) rather than settled by picking one.
#   (2) COAST_RETREAT_2005_2025_M and COAST_RETREAT_EFFECTIVE_M each named a
#   consumer that does not import them (Script 20's driver-change map, whose
#   coastal field is 5×δ₀ and rate-independent; and Script 37). They are read by
#   NO script and are documentation anchors for numbers report9 §4.10 types —
#   now labelled as such rather than deleted.
#   (3) COAST_RETREAT_RATE did not say that it DIVIDES, so h0 scales inversely
#   with it. Now stated with the three candidate values and its call sites.
#   Comment-only: verified by re-running 09f (byte-identical) and Script 20
#   Figures 3, 4 and 6 (byte-identical).
# v1.15.0  # Hollingham (2026) — 2026-08-29. commentary follows the CLEARFELL_DATE rename (T-17).
#   No value changes; verified by re-run against the 2026-08-29 pipeline outputs.
# v1.14.0  # Hollingham (2026) — 2026-08-29. Intervention dates
#   centralised here as ISO strings (D-084); they were declared independently in
#   clearfell_common, scraping_common and 09b. No value changes.
# v1.13.0  # Hollingham (2026) — 2026-08-29. Broadleaf restock year
#   corrected 1998 -> 1995 in the BL_CANOPY_FRACTION commentary (comment only; no
#   constant changed). Flags that f_2005 = 0.4 was judged on seven growing seasons
#   and the corrected year gives ten. See D-082.
# v1.12.0  # Hollingham (2026) — 2026-08-22. Adds
#   FULL_HINDCAST_MIN_MODERN_MONTHS and FULL_HINDCAST_SMOOTH_MONTHS for the
#   Script 39 full-record panel: the admission threshold for a well's modern
#   baseline, and the display smoothing for the rendered curve. Additive; no
#   existing constant changes and no committed output moves.
#
# v1.11.0  # Hollingham (2026) — 2026-08-22. Adds
#   REACH_QUOTE_NEAREST_M, the display granularity for the modelled forest and
#   scrape reach. The reach is a scaling argument, not a calibrated length —
#   the report states it to the nearest tens of metres — but Script 20 rendered
#   it to the metre on the figure while every document quoted the rounded form,
#   so the plot and the prose disagreed and neither was wrong. Rounding is a
#   rendering decision: the stored value in 20_report_numbers.csv is unchanged
#   and the field is computed from the unrounded length.
#
# v1.10.0  # Hollingham (2026) — 2026-08-21. Adds
#   PIPELINE_RELEASE_DATE and rewrites the PIPELINE_VERSION note: the release
#   string is decoupled from script module versions, which bump on any edit, so
#   a script ahead of the release is normal rather than a mismatch. Releases are
#   dated (M18, Martin 2026-08-21).
#
# v1.9.0  # Hollingham (2026) — 2026-08-21. Adds the CCW_* block
#   used by the standalone 1989-96 hindcast (Script 39): the dipwell pipe base
#   at which the historic readings are left-censored, the beta_1 scalings the
#   hindcast reports its envelope over, the initial-condition probe offsets and
#   the censoring admission threshold. Additive only.
#
# v1.8.0  # Hollingham (2026) — 2026-08-21. Adds
#   DIFF_SITE_MEAN_BASES, DIFF_POWER_ALPHA and DIFF_POWER_TARGET, supporting
#   Script 32's emission of the interannual residual spread and the smallest
#   site-wide rate the record can distinguish from zero. The two power
#   parameters are the test's alpha and target power; the multiplier they imply
#   is derived in the script from the normal quantiles, never typed. Additive
#   only; no existing constant changes.
#
# v1.7.0  # Hollingham (2026) — 2026-08-21. Adds
#   FAR_FIELD_REACH_MULTIPLE, the admission threshold for the far-field BACI
#   control tier, carried as a multiple of the FITTED cross-shore reach rather
#   than as a distance in metres so the criterion tracks the fit. Additive only;
#   no existing constant changes.
#
# v1.6.0  # Hollingham (2026) — 2026-08-20. Adds
#   ROLLING_WINDOW_YEARS and ROLLING_WINDOW_STEP_MONTHS, the window lengths and
#   the step of Script 25's fixed-length rolling-window sweep (25_13). Additive
#   only; no existing constant changes.
#
# v1.5.0  # Hollingham (2026) — 2026-08-19. Adds
#   CLUSTER_MONTH_DEGENERACY_GAP, the alert threshold on the divergence between
#   the two month-wise cluster-stability statistics Script 02 publishes. Both
#   are reported; the constant is what lets the script say when they disagree
#   by enough that the co-assignment figure is being inflated by cluster
#   merging rather than measuring reproducibility.
#
# v1.4.1  # Hollingham (2026) — 2026-08-18. SSM_BOOT_SEED added;
#   earlier UKCP18_SCENARIOS added:
#   Scripts 19 and 26b each carried their own copy of the same four seasonal
#   multipliers per epoch.
#
# v1.3.0  # Hollingham (2026) — 2026-08-16

# ── Journal B&W mode ─────────────────────────────────────────────────────────
# Toggle to produce journal-ready greyscale figures.
# When True, scripts use CLUSTER_COLOURS_BW, apply BW_HATCHES to bar charts,
# use BW_LINESTYLES for multi-series line plots, and call load_dem_auto()
# (which routes to hillshade) for map basemaps.
#
# Can be activated three ways:
#   1. Set BW_MODE = True here (permanent)
#   2. Set environment variable NRG_BW_MODE=1 before running (temporary)
#   3. Use run_analysis.py menu option 6 or --greyscale (sets env var)
import os as _os
BW_MODE = _os.environ.get("NRG_BW_MODE", "").strip().lower() in ("1", "true", "yes")
if BW_MODE:
    print("  [config.py] BW_MODE=True (NRG_BW_MODE env var detected)")

CLUSTER_COLOURS = {
    1: "#1a6faf",   # C1 Lake — old C1 blue
    2: "#2ca02c",   # C2 Dune — old C2 green
    3: "#d62728",   # C3 Western Residual — old C3 red
    4: "#7f77dd",   # C4 Main Forest — old C4 purple
    5: "#8B4513",   # C5 Coastal Forest — brown (saddlebrown)
    6: "#0072B2",   # reserved
}

# Greyscale equivalents — chosen for maximum perceptual separation.
# These map to luminance values spaced ~40 units apart on a 0–255 scale,
# ensuring distinguishability even when printed on a low-quality laser.
CLUSTER_COLOURS_BW = {
    1: "#2a2a2a",   # C1 — near-black (L ≈ 42)
    2: "#808080",   # C2 — mid-grey   (L ≈ 128)
    3: "#b8b8b8",   # C3 — light grey (L ≈ 184)
    4: "#545454",   # C4 — dark grey  (L ≈ 84)
    5: "#a0a0a0",   # C5 — grey       (L ≈ 160)
    6: "#d0d0d0",   # reserved
}

# Bar chart hatching patterns — used when BW_MODE is True.
# Index by cluster ID or by series index for non-cluster bar charts.
BW_HATCHES = {
    1: "",       # C1 — solid fill (no hatch)
    2: "///",    # C2 — diagonal lines
    3: "...",    # C3 — dots
    4: "xxx",    # C4 — crosses
    5: "\\\\\\",   # C5 — back-diagonal
    6: "+++",    # reserved
}

# General-purpose bar hatches for non-cluster series (e.g. P vs PET,
# climate vs forest management scenarios).
BW_BAR_HATCHES = ["", "///", "...", "xxx", "\\\\\\", "+++", "---", "ooo"]

# Line styles for multi-series plots — cycle through these when BW_MODE
# is True so lines are distinguishable without colour.
BW_LINESTYLES = [
    {"linestyle": "-",  "linewidth": 2.0},   # solid thick
    {"linestyle": "--", "linewidth": 1.8},   # dashed
    {"linestyle": ":",  "linewidth": 2.0},   # dotted
    {"linestyle": "-.", "linewidth": 1.8},   # dash-dot
    {"linestyle": (0, (5, 1)), "linewidth": 2.0},  # dense dash
    {"linestyle": (0, (3, 1, 1, 1)), "linewidth": 1.8},  # dash-dot-dot
]

# Greyscale line tones — pair with BW_LINESTYLES for maximum contrast.
# Darker lines for primary series, lighter for secondary/reference.
BW_LINE_COLOURS = ["#000000", "#555555", "#888888", "#333333", "#aaaaaa", "#666666"]

CLUSTER_LABELS = {
    1: "C1 (Lake Edge)",
    2: "C2 (Dune)",
    3: "C3 (Western Residual)",
    4: "C4 (Main Forest)",
    5: "C5 (Coastal Forest)",
}

# SSM displacement reference datum. The state-space model fits β₃ on
# displacement above this depth (h_disp = DRAINAGE_DATUM + h_depth, where
# h_depth is negative-convention depth below ground surface). β₃ > 0 then
# means "higher head above the drainage base drives faster drainage" —
# Darcy-consistent.
#
# Value selected by sensitivity analysis (Script 03, output 03_08): 3.7 m
# is the minimum reference depth at which all five clusters produce positive
# AND significant (p < 0.05) β₃. See HANDOVER_SCRIPT03_DATUM.md.
DRAINAGE_DATUM = 3.7  # metres below ground surface

# Headline rainfall lag applied in the SSM and all per-well OLS regressions.
# All scripts import this value rather than defining their own copy.
#
# History: originally set to 1 to compensate for a bucketing convention that
# assigned end-of-month / start-of-next-month field readings to the FOLLOWING
# calendar month (e.g. a reading on 01/09 representing August's water level
# was bucketed to September). With lag-1 rainfall, September's model row used
# August's rainfall — giving the correct physical pairing despite the
# mislabelled month.
#
# After fixing the bucketing in Script 01 (day ≤ 15 → previous month), the
# well data is correctly labelled and lag-0 gives the correct physical pairing.
#
# The pairing is NOT unchanged for the whole record, and an earlier version of
# this comment said it was. Of the 278 reading dates in
# Newborough_Cleaned_For_Model.csv, 160 (57.6%) fall on day ≤ 15: their bucket
# moves back a month, the lag drops to zero, and the rainfall they pair with is
# the same as before. The other 118 (42.4%) fall after the 15th, so their bucket
# does NOT move and dropping the lag pairs them one month later. Under the old
# scheme a 31 October reading — an October change — was regressed against
# September rainfall; lag-0 fixes that. A fit spans the whole record, so
# coefficients from before and after the fix are not comparable.
HEADLINE_LAG = 0

# ── UKCP18 seasonal climate-change multipliers ───────────────────────────────
# Applied to the OBSERVED P and PET series; neither is recomputed from projected
# temperature. Scripts 19 (scenario viewer) and 26b (MSL5 projections) each held
# their own copy of these four numbers per epoch until 2026-08-18, which is the
# mirrored-local pattern this file exists to prevent.
#
# Note on basis: the PET multipliers derive from UKCP18 projections computed on a
# physically-based (Penman-Monteith family) footing, while the baseline they
# scale is Thornthwaite. The two do not respond proportionally to warming -
# Thornthwaite carries its heat index in the denominator and damps its own
# response, measured at an elasticity of 0.42 over the RAF Valley record
# (00_05_pet_warming_response.csv). Applying a physically-based fractional change
# to a Thornthwaite baseline is therefore an assumption, and a conservative one:
# the scenario is more aggressive than Thornthwaite would generate from the same
# warming.
UKCP18_SCENARIOS = {
    "2050s": {"sP_w": 1.10, "sP_s": 0.85, "sPET_w": 1.05, "sPET_s": 1.20},
    "2080s": {"sP_w": 1.20, "sP_s": 0.70, "sPET_w": 1.10, "sPET_s": 1.35},
}

# Canopy interception fraction for Corsican pine (Freeman, 2008).
# Measured at C5 (Coastal Forest) throughfall gauge, applied to all forested
# clusters (C4 and C5). Interception is a PARTITION of the atmospheric energy
# budget, not a term additive to PET: it is subtracted from rainfall exactly
# once, and only where the term it modifies was not itself fitted on gross
# rainfall. Script 03 fits the SSM on gross P and above-canopy PET, so the
# canopy loss is already inside the fitted β — reducing P̄ again double-counts.
#
# (This block sat 21 lines above, separated from its constant by the whole
#  UKCP18 scenario section; moved here 2026-08-25 so the value meets its reason.)
#
# See INTERCEPTION_TREATMENT.md for the full derivation.
FOREST_INTERCEPTION = 0.24

# Cluster IDs carrying forest canopy (Corsican pine). These receive the
# interception correction in water-balance, WTF, and scenario scripts.
# Under k=5: C4 (Main Forest) and C5 (Coastal Forest).
FOREST_CIDS = (4, 5)

# --- WTF Approach C: rapid-recharge-event method (Script 17) -------------------
# Third, methodologically independent Sy estimator after Crosbie et al. (2005).
# Where Approach A corrects for drainage mechanistically (via β₃) and Approach B
# applies no correction (bias-low), Approach C selects episodes in which the
# drainage contribution to the observed rise is negligible *by construction* —
# short, sharply-rising events following a multi-month drainage baseline. The
# naïve Sy = ΣR / Δh is then approximately unbiased without a β₃ term.
# A candidate episode requires C_DRY_BASELINE prior months of Δh ≤ 0 (drainage-
# only quasi-steady state), starts on the first month with Δh > 0, runs until
# Δh ≤ 0 or the C_MAX_DURATION cap (whichever first), and must accumulate a
# cumulative head rise ≥ C_MIN_RISE_M. Per-episode Sy is filtered to the
# physical range [WTF_C_SY_MIN, WTF_C_SY_MAX]; the cluster estimate is the
# median with a WTF_C_BOOTSTRAP_N-resample 95 % CI (seed WTF_RAPID_BOOT_SEED).
# Approach C is a *reported* triangulation only — it does NOT propagate
# downstream; the event-based per-well Sy (Approach B, Script 18) remains the
# pipeline-consumed canonical. See Methods Supplement §S.12.
WTF_C_DRY_BASELINE   = 2       # consecutive prior months of Δh ≤ 0 required
WTF_C_MIN_RISE_M     = 0.05    # minimum cumulative episode head rise (m)
WTF_C_MAX_DURATION   = 2        # maximum episode length (months) — "rapid" cap
WTF_C_SY_MIN         = 0.01    # per-episode Sy physical-plausibility floor
WTF_C_SY_MAX         = 0.50    # per-episode Sy physical-plausibility ceiling
WTF_C_BOOTSTRAP_N    = 1000    # median-CI bootstrap resamples
WTF_RAPID_BOOT_SEED  = 20260611  # fixed seed — Approach C median-CI bootstrap

# --- Forest drawdown-propagation model (Script 20, plot_drawdown_propagation) -
# Steady-state drawdown around the forest block is modelled as a cone
# H0·exp(-d/λ), where the e-folding length λ = sqrt(K·b / (Sy·β₃_daily)) is
# derived live from the C3 propagation-medium Sy (WTF, Script 17) and β₃
# (SSM, Script 03); only the fixed model inputs are centralised here.
# ── BACI drift design (D-111, M14) ────────────────────────────────────────────
# Which covariate carries the differential drift between the Impact well and its
# controls in the paired clearfell BACI (Script 10a).
#
#   "easting"        delta_easting x months_since. The design every committed
#                    number before 2026-09-02 was produced under. Kept reachable
#                    so the equivalence below can be DEMONSTRATED, not asserted.
#   "coastal_free"   the coastal differential x months_since, coefficient FITTED.
#                    D-111's adopted design. With s_coast free this is the
#                    easting design re-parameterised - identical step, p-value
#                    and AIC to machine precision - so no published number moves.
#   "coastal_fixed1" the same column SUBTRACTED FROM y as an offset, not fitted,
#                    which is what "fixed at 1" has to mean. Reported as D-111's
#                    stated sensitivity (+77.2 mm against the published +113),
#                    NOT as the headline.
#
# 10k is deliberately NOT switched by this flag: its per-well easting term is a
# genuine spatial interaction rather than a rescaled time trend, so the
# equivalence does not carry and the same substitution there is a real design
# change with its own answer (D-111 Revisit-if).
BACI_DRIFT_DESIGN = "coastal_free"

# Which row of 25_14_correction_diagnostic.csv donates the coastal amplitude.
# The all-season canopy fit, per M14's decision-4 note: 10a's BACI displacement
# is a monthly all-season centroid difference, not a summer minimum, so the
# MAM-fitted gradient is the wrong donor.
BACI_COASTAL_DONOR_FIT = "full_lincap_canopy"

#   DRAWDOWN_H0_MM : forest interception deficit at the felling edge (mm).
#   DRAWDOWN_K_MDAY: aquifer hydraulic conductivity (m/day; Betson 2002).
#   DRAWDOWN_B_M   : saturated aquifer thickness used for λ (m; estimate).
# Previously hardcoded as in-function locals in Script 20.
DRAWDOWN_H0_MM  = 150.0
DRAWDOWN_K_MDAY = 6.0
DRAWDOWN_B_M    = 5.0

# Display granularity for the modelled reach. λ is derived from an assumed
# hydraulic conductivity and saturated thickness, so it carries roughly a factor
# of two of input uncertainty and is quoted to the nearest tens of metres
# throughout the corpus. This constant is the rounding applied where the reach is
# WRITTEN ON A FIGURE OR PRINTED; it is never applied to the value used to build
# the drawdown field, nor to the value stored in 20_report_numbers.csv.
REACH_QUOTE_NEAREST_M = 10.0

# --- Scrape rise-zone + coastal-retreat geometry (Scripts 20, 09d, 09f) --------
# Shared geometry constants for the scrape drain-cone and coastal-erosion fields.
# Previously declared as in-function or module locals in Script 20 and mirrored
# in Scripts 09d/09f; centralised here so all three read one definition.
#   SCRAPE_RISE_BUFFER_M : radius of the scrape rise (slack) zone (m); the
#                          drawdown cone is measured from this buffer outward.
#   COAST_RETREAT_M      : single-event shoreline retreat visualised (m;
#                          Storm-Brendan-scale exemplar, Pye & Blott 2024).
#   COAST_RETREAT_RATE   : SUPERSEDED 2026-08-29 (D-090). NO SCRIPT DIVIDES BY
#                          THIS ANY MORE. It was the normaliser converting a
#                          retreat event to an edge drawdown, and it was a
#                          SIX-YEAR window (2014-2020, from a newspaper report)
#                          divided into a delta_0 fitted over the WHOLE record —
#                          so the ratio was never a sensitivity. The divisor is
#                          now MEASURED by Script 40 over 2006-2026, a window
#                          matched to delta_0's own span to 99 %, and read live
#                          by utils.coastal_utils. The measured rate is 2.321
#                          m/yr, so h0 went from 22.65 mm to 81.00 mm.
#                          RETAINED only so Script 40 can emit the old
#                          construction beside the new one for comparison, and
#                          because the documents still cite it while they are
#                          brought up to date. Do not reintroduce it as a
#                          divisor; and per D-075 the replacement does not
#                          belong in this file, being a fitted result.
SCRAPE_RISE_BUFFER_M = 10.0
COAST_RETREAT_M      = 6.0
COAST_RETREAT_RATE   = 8.3

# --- Shoreline-retreat measurement (Script 40) ---------------------------------
# The measurement that makes the retreat series a pipeline output rather than a
# session computation (D-085, D-086). Its estimator is SIGNED shore-normal
# displacement: nearest distance is always positive and so cannot see
# progradation, a sign change, or a floor, which is why a field with no
# progradation anywhere once read as a clean rate.
#
#   SHORE_NORMAL_SPACING_M   : spacing of shore normals along the later line (m).
#   SHORE_NORMAL_MAX_RANGE_M : bound on the ray search; beyond it, no hit -> NaN,
#                              never zero.
SHORE_NORMAL_SPACING_M   = 25.0
SHORE_NORMAL_MAX_RANGE_M = 400.0

# Highest independently surveyed retreat rate on this frontage (m/yr).
# Pye & Blott (2024), NRW Evidence Report 787: 16.3 m over 2013-2022 at the most
# active point of the Twyni Penrhos profile. THE INDICATOR TRAVELS WITH THE
# NUMBER and is the whole point of the comparison: theirs is a DUNE-TOE sequence,
# while the digitised lines are the warren's seaward EDGE, which sits 20-34 m
# landward of the 3-4 m AOD toe band and 5-6 m higher up the profile (measured
# against the LiDAR DTM, 2026-08-29). The two agree only if the profile
# translates without changing shape. Used by Script 40's floor test, where a
# whole-frontage MINIMUM at or above this most-active-point MAXIMUM is taken as
# evidence that the field is not a measurement of a shoreline.
PUBLISHED_MAX_PROFILE_RATE = 1.8

# Gate tolerances for Script 40 — DELIBERATELY UNSET (None).
# Per the signed-off spec, these are not chosen before the distributions they
# judge are known: a threshold guessed ahead of the data is a guess dressed as a
# gate. Script 40 reports the measured control displacement and sagitta bound and
# treats None as FAILING, so the headline stays withheld until they are set from
# observation. The acceptance criterion for whichever values are chosen is that
# they must be CAPABLE OF FAILING on the committed lines - a tolerance that would
# not flag the present ~25 m offset is decoration - and Script 40 asserts that
# at run time rather than leaving it to the reader.
# SET FROM OBSERVATION 2026-08-29, not guessed ahead of it (D-089).
#
# SHORE_CONTROL_TOLERANCE_M. The 1/1/2006 imagery was traced twice, the second
# time BLIND. The two independent lines differ by |offset| median 2.34 m, p90
# 5.14, p95 5.53, max 11.57 - that IS the digitising-plus-registration error of
# this process, measured rather than assumed. The tolerance is the p95 rounded
# up. It is capable of failing and would have: the sparse 14-vertex 2026-08-28
# line differs from the blind trace at p95 36.98 m, and the 7-8 m systematic
# displacement of the withdrawn coast2020 line also exceeds it.
SHORE_CONTROL_TOLERANCE_M        = 6.0
#
# SHORE_GENERALISATION_TOLERANCE_M. Measured chord-sagitta bound on the current
# series is 3.829 m (26/36/41/86 vertices). Set at 5.0 m: the current lines pass
# with margin, and the old sparse series - whose bound was 7.467 m - would not.
SHORE_GENERALISATION_TOLERANCE_M = 5.0

# --- Coastal-gradient reference distance (Script 25) ---------------------------
# The distance at which the headline coast-edge trend is quoted (m).
#
# The decay fit's delta_0 is the amplitude at d = 0, the shoreline, where no
# well sits — so it is an extrapolation beyond the network, and it is the one
# place the linear-capped and exponential forms disagree materially. Quoting the
# headline at a distance the network actually covers gives a number the data
# constrains and makes the functional-form choice a methods footnote rather than
# a headline decision (D-047).
#
# 150 m is the nearest round distance inside the observed range, so the headline
# is interpolated, not extrapolated. Script 25 checks this against the panel's
# own minimum distance on every run and warns if a change to the well set ever
# leaves the reference outside the data — the value must not be trusted blind
# if the near-shore wells change.
COASTAL_REFERENCE_DISTANCE_M = 150.0

# --- Wells outside the coastal-gradient population (Script 25) -----------------
# Excluded from EVERY coastal-retreat gradient specification, on the grounds that
# they cannot respond to the mechanism being fitted — not on how they behave.
#
# ceh12 sits on the northern bedrock ridge. Its ground elevation is roughly 20 m
# above the next-highest well in the network and far above the dune aquifer the
# decay model describes, so a shoreline 1.1 km away cannot drain it. Whatever
# trend it carries is governed by something the model does not represent, and
# including it lets that trend be attributed to distance from the coast.
#
# It was already absent from the forest-free headline, but only incidentally:
# its in_forest flag is true, so the land-cover filter removed it as a CANOPY
# well. That is the wrong reason, and it is fragile — the well would silently
# re-enter if the canopy flag changed, and it was still inside the
# canopy-controlled fit, where a bedrock well was contributing to the estimate
# of extra drift under pine. Naming the exclusion geologically makes it durable
# and scopes it correctly (D-048).
#
# Scope is deliberately the coastal gradient alone. This says nothing about the
# well's validity elsewhere in the pipeline.
COASTAL_GRADIENT_EXCLUDED_WELLS = ["ceh12"]

# --- Fixed-length rolling-window sweep (Script 25, 25_13) ----------------------
# Window lengths (yr) at which the cross-shore decay fit is re-estimated on a
# window of FIXED length slid along the record.
#
# Script 25's other window sweep (25_12) pins the window END at the last month of
# the panel and moves only its START, so the window necessarily shortens as the
# start moves later. Where the window sits in the record and how much record it
# contains therefore move together, and a parameter that moves across that sweep
# cannot be attributed to either one. Holding the length constant and sliding the
# whole window separates the two axes.
#
# Several lengths are swept rather than one because the LENGTH is the axis under
# test. Whether the spread in a fitted parameter across windows is a property of
# where the window sits or of how long it is cannot be answered inside a single
# length — it needs the same slide repeated at different lengths and the spreads
# compared. The shortest length here is deliberately shorter than the minimum
# Script 25 will fit in 25_12, so that short-window behaviour is visible rather
# than excluded; the longest is bounded by the record itself, since a window
# approaching the panel's full span has almost nowhere left to slide.
ROLLING_WINDOW_YEARS = (10.0, 12.0, 15.0, 18.0)

# Step (months) by which the fixed-length window is advanced along the record.
# Quarterly rather than monthly: consecutive monthly windows differ by two months
# out of well over a hundred and their fits are near-duplicates, so a monthly step
# multiplies the fitting cost roughly threefold while adding almost nothing to the
# sampled spread. Quarterly still gives tens of windows at every length in
# ROLLING_WINDOW_YEARS.
ROLLING_WINDOW_STEP_MONTHS = 3

# --- Script 25: climate-covariate specification sweep (25_15, W136) ----------
# Memory half-lives, in months, of the exponentially-decayed water-balance
# accumulators the coastal panel fit is re-estimated against. The published
# covariate is the UNdecayed cumulative water balance, which is the half-life
# = infinity limit of the same column; this family brackets it on the finite
# side, and the spread of the fitted delta_0 and L across the family is what
# 25_15 publishes.
#
# The set is a bracket, not a search. It spans from well inside the panel's
# fitted memory optimum to well outside it, at roughly doubling steps, so the
# range it reports is bounded by covariates that are demonstrably worse
# predictors on both sides rather than by a fine grid around the best one. A
# finer or wider grid would narrow nothing and would invite the covariate to
# be selected on the fit rather than fixed in advance.
COVARIATE_SWEEP_HALF_LIVES_MO = (2.0, 4.0, 8.0, 12.0, 24.0)

# --- Far-field BACI control tier: distance criterion --------------------------
# Admission threshold for the far-field clearfell control tier
# (clearfell_common.FAR_FIELD_CONTROL_WELLS), expressed as a MULTIPLE of the
# fitted cross-shore decay reach L rather than as a distance in metres.
#
# Why a multiple and not a distance. The criterion the tier exists to satisfy is
# "far enough from the shore that the control cannot itself be carrying the
# gradient it is being used to measure". That condition is defined relative to
# the reach, which is a fitted quantity (Script 25, forest-free linear-capped
# panel; live value in 25_01_panel_fit_parameters.csv, first-pass fallback
# pipeline_params default_value("coast_reach_L_m")). A metre threshold typed
# here would be a pipeline result restated as a literal, and would go stale
# silently the first time the reach is re-estimated. As a multiple the threshold
# moves with the fit and the tier can be re-screened without editing this file.
#
# The multiple is set far enough above 1 that the threshold clears the reach's
# upper 95 % confidence bound with margin. A control admitted inside that bound
# may carry a gradient component of its own, which biases the measured contrast
# toward zero and makes the corroboration test conservative by an amount the
# test cannot quantify.
FAR_FIELD_REACH_MULTIPLE = 1.6

# --- Coastal-retreat magnitudes: DOCUMENTATION ANCHORS, not pipeline inputs ---
# Both constants below are read by NO script. They are the traceable home for two
# numbers the report types — report9 §4.10 quotes them together: "the retreat
# treated as effective over 2005–2025 is 105 m against a physical shoreline
# measurement of about 50 m". Kept for that reason; their earlier comments each
# named a consumer that does not import them (Script 20's driver-change map and
# Script 37's validation respectively), which is the same defect as a comment
# describing a relationship the code does not have. Corrected 2026-08-29 (W77).
#
# THE PROVENANCE DEFECT, recorded rather than resolved (D-085). Forgrave (2020)
# reports ONE figure of ≈50 m of retreat, and this file has cited that same
# ≈50 m to two incompatible windows: as "2014–2020" for COAST_RETREAT_RATE above
# (50/6 ≈ 8.3 m/yr) and as "since 2006" here (50/14 ≈ 3.6 m/yr). One quantity
# cannot have accrued over both, so at most one of those readings is right and
# neither is established. The note immediately below already objected to the
# 2014–2020 reading from the other side — it declines to extrapolate 8.3 over
# twenty years because ~166 m would overstate the accumulation — and that
# objection was left unacted on. NO WINDOW IS ASSERTED HERE until the shoreline
# measurement is scripted; see working/updates/ NRG_coast_retreat_rate_exposure
# and NRG_script40_retreat_spec (2026-08-29).
#
# Forgrave (2020) is a newspaper report of then-ongoing Bangor measurements and
# is the ONLY external source these constants have. Pye & Blott (2024), the only
# other measurement of this frontage, is a DUNE-TOE sequence giving ≈1.8 m/yr at
# its most active point — a different indicator from the seaward-edge lines the
# project digitised, which sit 20–34 m landward of the 3–4 m AOD toe band.
#
# Cumulative shoreline retreat over the 2005→2025 study window (m). Physical
# shoreline measurement, ≈50 m (Forgrave 2020 / Pye & Blott 2024), window
# disputed as above. NOT derived from COAST_RETREAT_RATE × 20, which would give
# ~166 m and overstate the accumulation.
COAST_RETREAT_2005_2025_M = 50.0
# COAST_RETREAT_EFFECTIVE_M (105.0 m) WAS HERE AND IS WITHDRAWN, 2026-08-29
# (Martin's ruling, W80). It was a real INPUT, not a stray: at commit 01db41d
# (2026-07-06) Script 37 drove its coastal field with
#     h0_mm = COAST_RETREAT_EFFECTIVE_M * (T_yr / REF_WINDOW_YR) * δ₀ / rate
# Script 37 was then rewritten to FIT that quantity rather than assume it, and
# the constant was orphaned by its own consumer being improved. The successor
# disagrees with it: the fitted coastal scale factor over 2005–2025 is 0.51,
# 95% CI −0.10 to 1.12 (outputs/37_driver_validation/37_scale_factors_by_window.csv),
# which spans zero and unity, where 105 m against a physical 50 m would need
# ≈2.1. Its comment also described an n=24 single-parameter fit that the current
# script does not perform. The one document sentence that quoted it — report9
# §4.10.6 — is rewritten to say what §4.12.1 already said: the record does not
# resolve whether the hydraulic boundary moved further than the dune toe.
# Do not reinstate a calibrated effective retreat here: per D-075 a fitted value
# in a constants file is a hard-coded result that drifts from the fit that made
# it, which is precisely what happened.

# Chronic coastal-drawdown accumulation window (yr) — the near-term horizon over
# which the fitted coastal-decline rate δ₀ is accumulated to a source drawdown
# (h0 = COAST_CHRONIC_YEARS × |δ₀|), linearly capped to zero at the reach L.
# Shared by Script 20 (driver-change map coastal field) and Script 09f
# (management-vs-coastal spatial-reach synthesis, 5-yr coastal curve). Coincides
# numerically with the SLR near-term horizon (Script 20 SLR_WINDOW_YEARS = 5 yr)
# but is a DISTINCT quantity — a chronic linear accumulation of δ₀, not the SLR
# erfc transient — so it is named separately and the two can diverge in future.
COAST_CHRONIC_YEARS = 5.0

# Mechanism-figure accumulation horizon (yr) — the horizon over which the
# spatially-uniform climate term c and the coastal decline rate δ₀ are
# accumulated to an equivalent depth for the public-summary mechanism figures
# and the Script 09f reach panel's 20-yr comparison column (climate_20yr =
# c × MECHANISM_HORIZON_YEARS = -127 mm; coastal shore = δ₀ × horizon). A
# LONGER, distinct horizon from COAST_CHRONIC_YEARS (5 yr): the 5-yr basis is
# the near-term chronic curve drawn on the reach panel, the 20-yr basis is the
# site-footing horizon the mechanism grid uses. Kept here as the single source
# so the reach column and the mechanism figures cannot drift apart.
# ── Site reference points (OSGB36 / EPSG:27700) ──────────────────────────────
# Fixed physical locations on the site, shared by several scripts. Each was
# previously duplicated as a module-local literal in three to five places; they
# are consolidated here so a correction cannot land in some consumers and not
# others. Values are unchanged from those duplicates, which all agreed.
#
# Ridge reference point — the northern bedrock-ridge datum against which
# ridge-distance and recharge-lag analyses are measured (Scripts 10c, 23, 24,
# 24b).
RIDGE_REF_E = 241750.0
RIDGE_REF_N = 364500.0

# Maximum well-to-ridge separation admitted to ridge-distance analyses (m).
RIDGE_MAX_DISTANCE_M = 3000.0

# Minimum record length admitted to the residual-field diagnostics (Scripts 23,
# 24). 140 months is approximately half the 21-year record; in practice the
# binding minimum among eligible wells is 151 months, so the threshold excludes
# only ceh40, ceh41 and ceh42. Previously duplicated as a bare MIN_MONTHS local
# in both scripts.
RESIDUAL_DIAG_MIN_MONTHS = 140

# Wells excluded from the residual-field diagnostics (Scripts 23, 24), as
# normalised names. ceh3, ceh7, ceh8 and ceh37 carry tidal, coastal-erosion or
# upstream-drop artefacts; ceh4 is retained in the reference network but its
# record is too short for these tests. llynrhos is the Llyn Rhos-Ddu lake gauge,
# which is a surface-water level record and not one of the 88 classified
# dipwells, so it has no water-balance residual in the SSM sense.
RESIDUAL_DIAG_EXCLUDED_WELLS = {'ceh3', 'ceh4', 'ceh7', 'ceh8', 'ceh37', 'llynrhos'}

# Bootstrap settings for the per-cluster summer-minus-winter contrast reported by
# Script 24. The contrast and its p-values are quoted in the Paper 1 SI (S9.2), so
# the tests are emitted by the pipeline rather than computed ad hoc.
RESIDUAL_DIAG_SW_BOOT_N    = 10000
RESIDUAL_DIAG_SW_BOOT_SEED = 20260809

# Minimum observations for a per-well SSM fit, applied after differencing and
# dropna. This is the permissive floor used by the general model_utils fitters;
# the residual-field diagnostics impose the stricter RESIDUAL_DIAG_MIN_MONTHS
# above. Previously a module-local in model_utils.py.
SSM_MIN_OBS = 30

# Length of the most-recent-months window used for PER-WELL SSM fits, in months.
# This is the equal-record comparison window: every well is fitted over the same
# number of its own most recent months, so per-well coefficients, the SSM-vs-TLM
# benchmark and the spatial coefficient fields are not confounded by wells that
# joined the network at different dates. CLUSTER-CENTROID fits deliberately do
# NOT use it — they pass window=None and take the full record, because there the
# quantity being identified is a single coefficient rather than a comparison
# between records of unequal length (D-006).
#
# Named for the LCSC (Lumped Catchment Storage Coefficient = 100/beta_1) analysis
# that first used it; the window itself is generic. Consumed by Script 03
# (per-well fits and the per-well datum sweep), Script 08 (benchmarking, which
# writes 08_lcsc_model_stats.csv) and Script 30 (the C4 identifiability
# diagnostic, which reports it against the full record as a sensitivity).
#
# Distinct from MIN_MONTHS_THRESH, which is an admission threshold for the
# reference network, not a fitting window. Previously declared independently in
# model_utils.py and in Scripts 03 and 08 (D-016).
LCSC_DATA_LIMIT = 100

# Reference date for the centroid composition sensitivity (Script 03, output
# 03_13). Cluster centroids are the mean of their member wells, and members came
# online between 2005 and 2014, so early centroid months are the mean of a
# growing subset. This is the date report8 §3.4.1 cites for its stable-membership
# check: every cluster's full membership reports from here (the last to
# stabilise is C3, 2014-07). Script 03 also reports each cluster's own derived
# stable-membership start alongside it. Added 2026-08-16.
CENTROID_COMPOSITION_REF_DATE = "2015-01-01"

# CEH36 — the documented April 2015 dune-scrape site, used as a distance origin
# for scraping-propagation analyses and as the default scrape centre on the
# Script 20 scenario map (Scripts 09b, 20, 29, clearfell_common).
CEH36_E = 241161.0
CEH36_N = 363306.0

MECHANISM_HORIZON_YEARS = 20.0

# ── Sea-level-rise transient (Script 20 SLR head-response figure) ────────────
# Scenario inputs for the gradual mean-sea-level-rise head response, modelled as
# a finite-window erfc transient (NOT steady state) diffusing inland from the
# Caernarfon Bay boundary over the diffusivity D = K·b/Sy, with K and b taken
# from DRAWDOWN_K_MDAY / DRAWDOWN_B_M and Sy read live from the C3 WTF estimates.
#
# SLR_WINDOW_YEARS is DISTINCT from COAST_CHRONIC_YEARS despite both currently
# being 5.0 (see the note at COAST_CHRONIC_YEARS): that constant accumulates the
# fitted coastal decline rate δ₀ linearly, this one sets the horizon t of an erfc
# transient. They were deliberately decoupled in Script 20 v1.31.0 and must not
# be merged — either can move without the other.
SLR_WINDOW_YEARS  = 5.0    # yr — response window t, near-term horizon
SLR_RISE_M        = 0.02   # m accumulated over the window ≈ 4 mm/yr relative SLR
                           # (north Wales current-rate central estimate, UKCP18)
SLR_SHORE_LEVEL_M = 0.0    # m AOD — SLR head is referenced to MEAN sea level, not
                           # the erosion dune-toe front (COAST_SHORE_LEVEL_M); the
                           # water table is pinned to MSL at the coast.

# --- Mechanism-diagram schematic constants (Script 09g; utils/mechanism_fig_utils) -
# FIGURE-DESIGN geometry for the §5.8 public-summary mechanism diagrams — NOT
# physical amplitudes (those are read live from committed CSVs: 09f_01 reach
# profile row 0 + the 10m WMC3 BACI, with pipeline_params first-pass fallbacks).
# These constants define the shared schematic cross-section: a vertically
# exaggerated, not-to-scale dune profile, so they do not "trace to a CSV" — they
# are drawing coordinates, centralised here per the 2026-07-17 09g sign-off.
#   MECH_FIG_PX_PER_MM   : shared vertical amplitude scale (px per mm of head)
#                          across ALL four mechanisms, so their relative
#                          magnitudes compare on one figure. Reduced from the
#                          raw 09f scale so the largest amplitude (forest
#                          -150 mm) just clips the schematic slack floors;
#                          09f RATIOS between mechanisms are preserved.
#   MECH_FIG_PROFILE_GX/GY : shared ground-profile nodes (fore-dune back shelf
#                          210 contains the seaward pond; inter-slack ridge 182
#                          keeps ponds separate; slack floors 218 / 197).
#   MECH_FIG_SLACK_CENTRES : seaward / inland slack centres on the profile.
#   MECH_FIG_RETREAT_SHORE/HIN : coastal-retreat states — retreated shoreline x
#                          and inland-head parameter per state (storm / 5 yr /
#                          20 yr; qualitative, horizontal not to scale).
#   MECH_FIG_ERODE_LIGHTEN / MECH_FIG_SEA_LIGHTEN : ghosting fractions for the
#                          eroded-dune and advancing-sea fills per retreat state.
#   MECH_FIG_INLAND_GROUND_PTS / MECH_FIG_INLAND_UND_PTS : reach-figure inland
#                          dune body (two ridges + two flat-bottomed slacks) and
#                          undisturbed-table nodes, (distance_m, y_px) pairs over
#                          the compressed 330–900 m inland tail.
MECH_FIG_PX_PER_MM = 0.10
MECH_FIG_PROFILE_GX = [110, 138, 170, 206, 215, 285, 300, 340, 370, 400, 440, 478, 520, 640]
MECH_FIG_PROFILE_GY = [250, 200, 210, 210, 218, 218, 218, 196, 182, 196, 197, 197, 178, 160]
MECH_FIG_SLACK_CENTRES = [257.0, 459.0]
MECH_FIG_RETREAT_SHORE = {"storm": 150.0, "5yr": 196.0, "20yr": 270.0}
MECH_FIG_RETREAT_HIN   = {"storm": 74.0,  "5yr": 66.0,  "20yr": 40.0}
MECH_FIG_ERODE_LIGHTEN = {"storm": 0.72, "5yr": 0.50, "20yr": 0.28}
MECH_FIG_SEA_LIGHTEN   = {"storm": 0.18, "5yr": 0.42, "20yr": 0.66}
MECH_FIG_INLAND_GROUND_PTS = [(330, 160), (380, 172), (480, 172), (540, 140),
                              (600, 160), (720, 160), (790, 138), (850, 156), (900, 150)]
MECH_FIG_INLAND_UND_PTS    = [(330, 172), (520, 164), (720, 157), (900, 150)]

# --- Post-intervention equilibration (decay) characterisation (Scripts 09c, 10d) -
# Parameters for the summer-minimum equilibration/decay-slope characterisation:
# the scraped-slack relaxation transient at CEH36 (09c) and its clearfell
# no-decay comparator at WMC3 (10d). The decay is characterised as a plain OLS
# slope on the annual summer-minimum gap series (no AR(1): annual points, n≈9,
# where AR(1) would be unstable). The residual plateau is the mean of the final
# EQUIL_RESIDUAL_WINDOW_YEARS summer years; a slope is only reported where at
# least EQUIL_MIN_FIT_POINTS annual points are available.  These are
# characterisations of management-relevant trajectories, reported soft: the
# literature supplies mechanism, direction and timescale, not a matching rate.
EQUIL_RESIDUAL_WINDOW_YEARS = 5   # residual plateau = mean of final N summer years
EQUIL_MIN_FIT_POINTS        = 3   # minimum annual points required for an OLS slope

CLUSTER_MARKERS = {
    1: "o",
    2: "s",
    3: "^",
    4: "D",
    5: "P",
    6: "*",  # reserved
}

# Shared recency cutoff used for reference-network selection across scripts.
REFERENCE_CUTOFF_DATE = "2026-02-01"

# ── Site geography ────────────────────────────────────────────────────────────
# RAF Valley climate station, Anglesey — latitude for Thornthwaite day-length
# correction. Confirmed 53°14′32″N → 53.242° ≈ 53.25.
RAF_VALLEY_LAT_DEG = 53.25

# ── Ecological thresholds — Curreli et al. (2013) ────────────────────────────
# Dune slack community viability limits, expressed as depth below ground
# surface (m, positive downward). Applied in threshold forecasting (11, 11b),
# climate projections (14), spatial viewer (19), and forestry scenarios (21).
SD15b     = 0.61   # m — wet slack viability
SD15b_REC = 0.75   # m — wet slack recovery / excavation limit
SD16      = 0.98   # m — dry slack threshold
SD16_REC  = 1.20   # m — dry slack recovery / excavation limit

# Winter thresholds used in climate projections (negative = below ground
# in the sign convention of Script 14's depth axis).
SD15b_WINTER = 0.10  # m — winter flooding limit for wet slack
SD16_WINTER  = 0.25  # m — winter flooding limit for dry slack

# ── Ecological metric — van Willegen et al. (2025) ────────────────────────────
# Five-year mean spring water level (MSL) — best-performing hydrology metric
# for dune slack vegetation response (Ellenberg EbF), per van Willegen et al.
# 2025 Ecological Indicators 170, 113016. Used by Script 26.
#
# Definitions (van Willegen 2025, paper's "hydrology year B"):
#   * Spring window  : 1 March – 31 May  (calendar months 3, 4, 5)
#   * Hydrology year : 1 June (y-1) to 31 May (y)
#   * Annual MSL_y   : unweighted mean of {Mar, Apr, May} levels in hy y
#   * 5-year MSL5(y) : unweighted mean of {MSL_{y-4} ... MSL_y}
#
# Strictness (orchestrator decision 2026-05-20):
#   * 3 of 3 spring months required for a valid annual MSL
#   * 5 of 5 annual MSLs required for a valid 5-year mean
#
# These match van Willegen's "3 months per spring as a minimum requirement"
# recommendation; the 5/5 rule eliminates ambiguous partial windows.
MSL_SPRING_MONTHS          = (3, 4, 5)
MSL_HYDRO_YEAR_START_MONTH = 6
MSL_DEFAULT_WINDOW_YEARS   = 5
MSL_MIN_MONTHS_PER_SPRING  = 3
MSL_MIN_YEARS_IN_WINDOW    = 5

# Plot-presentation: trajectory figures restricted to window-ends ≥ this year.
# The reference + extended network expanded materially between 2007 and 2010
# as CEH instrumentation came online; pre-2010 windows are dominated by ~10
# NW wells whereas from 2010 the network exceeds 60 wells. The first 5-year
# window drawn entirely from the post-2010 network is end-year 2014 (covering
# 2010–2014). Per-well CSVs retain the full record; only the cluster
# trajectory and quadrat-wells figures are clipped.
# Consistent with van Willegen's 2010–2019 analysis period.
MSL_TRAJECTORY_START_YEAR = 2014

# Van Willegen et al. (2025) used these 17 piezometers with co-located
# permanent vegetation quadrats (their Table 1). MSL5 at these wells is
# directly tied to a calibrated EbF response; at all other wells it is a
# hydrological metric only. Used by Script 26's quadrat-wells figure and
# by the map figure's yellow-diamond annotation.
VW_QUADRAT_WELLS = (
    "ceh8", "ceh24", "wmc2", "ceh23", "ceh26", "nw3",
    "ceh9", "ceh22", "nw4", "t41",
    "ceh4", "ceh5", "nw5", "nw6",
    "ceh1", "nw2", "nw7",
)

# ── Intervention marker colours ───────────────────────────────────────────────
# Used by Script 26's trajectory plots; reserved for re-use by any future
# script that wants to overlay scrape / clearfell event lines.
# Colours chosen to be print-safe and to read distinctly from the
# CLUSTER_COLOURS palette above.
INTERVENTION_COLOUR_SCRAPE   = "#7b3294"  # purple — CEH36 scrape (2015) and CEH18/21 re-scrape (2023)
INTERVENTION_COLOUR_CLEARFELL = "#e66101"  # orange — December 2017 pine clearfell

# Spatial scrape-footprint overlay colour, used by map_utils.add_kml_features()
# to draw the GPS-traced scrape outlines as a shared site feature. Distinct from
# INTERVENTION_COLOUR_SCRAPE (a temporal event-line colour); navy reads clearly
# against the dodgerblue water features. BW-mode falls back to black dotted in
# add_kml_features().
FEATURE_COLOUR_SCRAPE = "navy"

# Canonical list of GPS-traced scrape footprint KMLs (basenames, resolved under
# data/geo/ via paths.data_geo). Single source of truth for both the shared
# add_kml_features() outline layer and Script 20's scrape-drawdown registry.
SCRAPE_KML_FILES = [
    "ceh36_scrape.kml",
    "CEH18_scrape.kml",
    "CEH21_scrape.kml",
    "CEH40_scrape.kml",
    "CEH41_scrape.kml",
    "CEH42_Scape.kml",   # preserved upstream "Scape" spelling
    "Scrape_A.kml",
    "Scrape_B.kml",
]

# ── Canonical site map extent (OSGB36 / EPSG:27700) ───────────────────────────
# THE single source of truth for the frame of every publication-quality spatial
# figure in the pipeline EXCEPT scripts 12 and 13 (which keep their own bespoke
# overview/experimental-design extents). All other map functions read these
# constants via map_utils.add_en_axes() — no hardcoded extents anywhere else.
# Chosen to crop the site to the dune Special Area of Conservation footprint and
# forest block while excluding empty sea and inland farmland.
#
# Extent contains all 99 measuring points (E 240339–243602, N 362615–364821)
# and the full site boundary (N max 365096) with margin. The northern edge sits
# ~400 m above the site boundary, leaving headroom for top-anchored legends.
# Background Features.kml / streams.kml that extend further north are cropped at
# the frame edge, which is intended.
SITE_MAP_EAST_MIN  = 240100
SITE_MAP_EAST_MAX  = 243900
SITE_MAP_NORTH_MIN = 362200
SITE_MAP_NORTH_MAX = 365500

# ── Broadleaf interception ────────────────────────────────────────────────────
# Deciduous annual-mean interception fraction — Komatsu et al. (2011).
# Approximates summer (~25 %, leafed) and winter (~0 %, leafless) averaged
# over the year. Used in replanting scenarios (scripts 19, 21).
BROADLEAF_INTERCEPTION = 0.15

# ── Intervention dates — the site's event history ─────────────────────────────
# SINGLE SOURCE OF TRUTH. Until 2026-08-29 these were declared independently in
# utils/clearfell_common.py, utils/scraping_common.py and 09b_scraping_
# propagation.py (as FELL_DATE) — three copies of a date that defines the
# before/after split of the clearfell BACI, consumed by twelve modules. Same
# defect D-016 fixed for LCSC_DATA_LIMIT. See D-084.
#
# ISO STRINGS, not pd.Timestamp, on purpose: this module imports only `os` and
# is imported almost everywhere, so it must not pull pandas into every import
# chain. The util modules build Timestamps from these.
#
# NAMING. The clearfell constant is exported downstream as CLEARFELL_DATE,
# which reads ambiguously inside scraping_common — it is the CLEARFELL, never a
# scraping event. Named unambiguously here; the util modules also export
# CLEARFELL_DATE as the preferred alias for new code.
#
# PROVENANCE: Martin's recollection (D-083), with one exception — the April 2015
# CEH36 scrape is documented. This is a stated limitation of the study, not an
# oversight, and belongs in the methods text.
CLEARFELL_DATE_ISO  = "2017-12-01"   # December 2017 pine clearfell
SCRAPING_DATE_0_ISO = "2013-02-01"   # February 2013 — CEH40/41/42 unmonitored cuts
SCRAPING_DATE_ISO   = "2015-04-01"   # April 2015 — CEH36 scrape (documented)
SCRAPING_DATE_2_ISO = "2023-10-01"   # October 2023 — re-scraping

# ── Broadleaf restock canopy-establishment fractions (2005→2025 driver map) ────
# The broadleaf restock block (data/geo/broadleaf_restock.kml) was felled 1993,
# restocked 1995, and reaches full canopy by 2025.
# RESTOCK YEAR CORRECTED 2026-08-29 from 1998 to 1995 (Martin's ruling). The
# corpus carried three different years - 1995 in the KML's own layer name
# (Broadleaf_conversion_1995), 1996 in report10 and the Supplementary Material,
# 1998 here and in report9 - and 1995 is now used throughout.
# f_2005 CONFIRMED 2026-09-04 (Martin): the 0.4 baseline was checked against the
# aerial photography, which reads about 0.4 broadleaf canopy at the 2005/2006
# baseline. It is an OBSERVATION-anchored value, not a seasons-since-restock
# judgement, so the D-082 restock-year correction (1998 -> 1995) does NOT move it.
# (An earlier note flagged 0.4 as "likely low" on a ten-growing-season basis; that
# concern is discharged - the aerial photography sets the value, not a growth curve.)
# For the 2005→2025 modelled
# driver-CHANGE map (Script 20 plot_driver_change_2005_2025) only the INCREMENT
# of interception developed over the window contributes:
#     Δh_BL = (BL_CANOPY_FRACTION_2025 − BL_CANOPY_FRACTION_2005) × H0_BL_full
# where H0_BL_full = DRAWDOWN_H0_MM × (BROADLEAF_INTERCEPTION / FOREST_INTERCEPTION)
#                  = 150 × (0.15 / 0.24) ≈ 94 mm at full canopy.
# f_2005 = 0.4 (Martin 2026-07-05, confirmed against the aerial photography 2026-09-04) → increment 0.6 × 94 ≈ 56 mm at
# source. This is the least-constrained field on the map; the caption flags the
# BL patch as modelled/indicative. Stored here (not hardcoded) so the basis is
# auditable and the sensitivity can be varied.
BL_CANOPY_FRACTION_2005 = 0.4
BL_CANOPY_FRACTION_2025 = 1.0

# ── Script 41 — canopy / forest-cover texture index from the aerial series ────
# The index is a TEXTURE POSITION BETWEEN TWO IN-FRAME REFERENCES, not a canopy
# fraction. Its upper anchor is mature conifer, so a closed BROADLEAF canopy
# legitimately reads below 1 and the index cannot speak to full closure at all.
# Script 41 states that in its own output; it is repeated here because a reader
# who finds these constants first will otherwise assume a percentage.
CANOPY_TEXTURE_WINDOW   = 5      # px; local sd window, ~5-7 m at the series scale
CANOPY_MIN_REGION_PX    = 400    # below this a region is too small to texture
CANOPY_MIN_REF_SEPARATION = 0.02 # (conifer - open) floor; below it the
                                 # normalisation divides by noise and is withheld
CANOPY_MAX_RESIDUAL_M   = 25.0   # registration residual (p95) tolerance, metres.
                                 # Set from the observed placemark spread, not
                                 # chosen first - the D-089 discipline.
CANOPY_CHANGE_PCTL      = 98.5   # change-detection threshold percentile
CANOPY_REF_BUFFER_M     = 40.0   # buffer excluded around the managed blocks when
                                 # building the conifer reference from the forest
                                 # polygon, so an edge is never a reference

# ── Script 41: marker detection, framing and change grid (v2.0.0, 2026-08-31)
# The first issue carried these as literals inside _fit_from_placemarks() and
# _affine_from_control(), calibrated to the LARGE marker symbol of the `aerial`
# captures. The `site*m` captures render the same markers much smaller, so a
# 120 px floor rejected every one of them and 60 region-frame values were
# withheld as "0 placemark(s) matched" — 2021 was lost entirely (W112).
CANOPY_MARKER_MIN_PX    = 12     # smallest accepted marker blob, AFTER dilation.
                                 # Sized for the small blue `m`-frame symbol, not
                                 # the large one; the matching radius and the
                                 # >= 6-pair requirement do the rejecting, which
                                 # is what they are for.
CANOPY_MARKER_MAX_PX    = 1500   # largest accepted blob (unchanged)
CANOPY_MARKER_DILATE    = False  # MEASURED OFF, 2026-08-31. The idea was that a
                                 # small symbol is mostly anti-aliased edge and a
                                 # per-pixel colour test would fragment it. It
                                 # does not: the small markers label cleanly at
                                 # 30-56 px undilated. What dilation DOES do is
                                 # merge adjacent large markers - blobs of 336
                                 # and 400 px where singles are ~230 - losing a
                                 # control point and putting the merged tip
                                 # between two wells. Off is better on every
                                 # frame tested (37 vs 36, 40 vs 38, 97 vs 96).
# Framing margins as FRACTIONS of the frame, never pixels. The 2026 capture is a
# different size because the window shifts when the historic imagery is toggled
# off (Martin, 2026-08-31), and absolute margins mask the wrong region on it.
CANOPY_CROP_FRAC_TOP    = 0.0833   # 90 / 1080
CANOPY_CROP_FRAC_LEFT   = 0.112    # 215 / 1920
CANOPY_CROP_FRAC_RIGHT  = 0.961    # 1845 / 1920
CANOPY_CROP_FRAC_BOTTOM = 0.9259   # 1000 / 1080
# CORRECTED 2026-08-31, same day, before anything was committed. The first
# values assumed a 1200 x 1920 frame; the frames are 1920 x 1080, measured
# directly. The vertical pair therefore cropped rows 81-900 instead of 90-1000
# and cut 100 rows of usable frame off every capture. The fractions above
# reproduce v1.0.0's pixel literals exactly at 1920 x 1080 - which is the test
# any replacement must pass, and which the first pair silently failed.
# ── Registration: constellation groups and the seed (v2.1.0, 2026-08-31) ────
# Martin: "they are all in the same location in all images, and the same size."
# Measured true, and it is the key to the whole problem. The 29 frames fall into
# FIVE constellation groups; within a group the detected marker positions agree
# to 0.0 px, and between groups they differ by a small rigid offset because the
# view was nudged between capture sessions.
#
# v2.0.0 seeded EVERY frame from the FIRST frame's affine. The site* frames are
# a different viewpoint 91 px away and could never match from there; the 2026
# aerial frame sits 49 px from its own group against a 45 px first radius.
# Fixing the marker SIZE was necessary and not sufficient: site24-3-2021m
# yielded 97 marker blobs and still matched four.
CANOPY_CONSTELLATION_TOL_PX = 3.0   # two frames are the same viewpoint when
                                    # their marker tips agree within this
CANOPY_GROUP_MIN_FRACTION   = 0.6   # ...for at least this fraction of tips
CANOPY_CHAIN_MIN_TIPS       = 15    # tips that must coincide before one group's
                                    # solution may seed another. Measured: the
                                    # two site groups share 20, so they chain;
                                    # site-to-aerial shares 3, so they do not -
                                    # the guard that stops a seed being carried
                                    # across genuinely different viewpoints.
CANOPY_MIN_CONTROL_POINTS   = 8     # below this a registration is not accepted,
                                    # whatever its residual. Six is the least an
                                    # affine needs and is not a measurement.
CANOPY_MATCH_RADII_NARROW = (45.0, 30.0, 22.0, 18.0)
CANOPY_MATCH_RADII_WIDE   = (140.0, 90.0, 60.0, 40.0, 28.0, 18.0)
CANOPY_MATCH_MAX_ITER     = 5       # refits at each radius, stopping when the
                                    # match count stops growing. v1.0.0 did
                                    # exactly two passes, which cannot bootstrap
                                    # from a seed that starts with a handful.
# ── Resolution gate (v2.2.0, 2026-08-31) ───────────────────────────────────
# MEASURED, and it closes the 2021 question rather than leaving it open. Once
# the site* and seabed frames registered, they produced plausible-looking index
# values that measure nothing: pooled across the managed regions their index
# correlates with the aerial index of the SAME region on the SAME day at
# r = +0.089 (n = 33), and for the broadleaf restock at -0.513 - the wrong sign.
# The decisive case is the clearfell. The aerial view goes 1.235 (2017-04) to
# 0.141 (2018-06) across the December 2017 fell; the site view goes 0.016 to
# -0.048, and was already near zero in 2009, eight years before.
#
# The mechanism is resolution, not registration - those frames now register at
# 2.7-4.4 m median residual. The site captures are a wider view at roughly
# 2.9 x 3.3 m/px against the aerial 1.35 x 1.59, so a CANOPY_TEXTURE_WINDOW of
# 5 px spans about 15 m of ground rather than about 7 m, and averages over
# several crowns instead of resolving them.
#
# So the gate is on GROUND SAMPLING DISTANCE, derived per frame from its own
# fitted transform - not on a list of filenames, which would not survive the
# next capture session.
CANOPY_MAX_GSD_M        = 2.0    # metres per pixel. Above this the texture
                                 # window spans more than about 10 m and cannot
                                 # resolve a crown. The aerial captures sit at
                                 # ~1.5 and pass; the site and seabed captures
                                 # sit at ~3 and are withheld.
CANOPY_CHANGE_GRID_M    = 2.0    # ground resolution for change detection. Frames
                                 # are differenced on a common OSGB grid, never
                                 # pixel-to-pixel: they differ in size and
                                 # viewpoint, so a pixel difference is dominated
                                 # by perspective rather than by the ground.

# ── Leaf state, for the deciduous regions in Script 41 ──────────────────────
# Named for LEAF STATE, not for season (the D-100 rule): these classify a frame
# by what the canopy is doing when it was captured, which is a different
# question from any of the seasonal windows above and must not be merged with
# them. Set by Martin, 2026-08-31, from the series itself: "1-1-2006 is clearly
# winter no leaf. Photos in March and April are the leaves coming out. May, June,
# July are full leaf out."
#
# This matters more than it looks. On the in-frame ratio to the conifer control,
# the full-leaf class is stable to 3.6% across 2012-2019 while the emerging class
# scatters five times as much - stratifying is what makes the series usable.
LEAF_OFF_MONTHS       = (11, 12, 1, 2)   # bare
LEAF_EMERGING_MONTHS  = (3, 4)           # leaves coming out
LEAF_FULL_MONTHS      = (5, 6, 7)        # full leaf out - the comparison basis
LEAF_SENESCING_MONTHS = (8, 9, 10)       # turning

# Broadleaf summer β₂ multiplier — deciduous phenology effect on ET.
# Derived from Script 21's monthly β₂ profile (Hollingham, 2026), averaged
# over the canopy-on phenological window:
#   May=0.98, Jun=1.08, Jul=1.12, Aug=1.15, Sep=1.10, Oct=1.02 → mean = 1.0750
# Seasonal window choice — May–Oct (six months, canopy-on / β₂ ≥ ~1.0).
# Aligns with the broadleaf canopy state: by May the canopy is essentially
# functional; through October the canopy is still operative even as leaves
# turn. April and November are assigned to winter because β₂ < 1 there.
# This is a phenologically-aligned window choice specific to broadleaf β₂;
# other seasonal-window definitions in the pipeline (Script 17 PET-negligible
# Nov–Mar, Script 11b summer-minimum Jun–Sep) are unchanged — they reflect
# different physical questions and retain their own justifications.
# In full leaf, broadleaf transpiration exceeds pine transpiration despite
# lower interception. This only applies to summer scenario bars; the
# annual-mean effect is approximately ×1.0 (seasonal pattern cancels).
BROADLEAF_B2_SUMMER = 1.0750

# Broadleaf winter β₂ multiplier — leafless dormancy reduces ET draw.
# Derived from Script 21's monthly β₂ profile (Hollingham, 2026), averaged
# over the canopy-off phenological window:
#   Nov=0.92, Dec=0.87, Jan=0.85, Feb=0.85, Mar=0.88, Apr=0.92 → mean ≈ 0.8817
# Seasonal window choice — Nov–Apr (six months, canopy-off / β₂ < 1.0).
# Pairs with the May–Oct summer window above; together they span all 12
# months at the canopy-functional boundary. Leafless broadleaf canopy has
# negligible transpiration; value < 1.0 reflects the reduced atmospheric
# draw relative to evergreen pine.
BROADLEAF_B2_WINTER = 0.8817

# ── DEM colour scale ─────────────────────────────────────────────────────────
# TwoSlopeNorm anchors used across all map products
DEM_VMIN = 0.0
DEM_VCENTER = 12.0
DEM_VMAX = 35.0

# ── UKCP18 RCP8.5 Wales central estimates ────────────────────────────────────
# Seasonal precipitation and PET scaling factors for climate scenarios.
# Source: UKCP18 probabilistic projections, 50th percentile, 2050s (2040-2069),
# RCP8.5, Wales region. Applied as multipliers to the monitoring-period
# climatology in Scripts 09d, 19, and 21.
UKCP18_DRY_P_WINTER  = 1.05   # +5% winter P
UKCP18_DRY_P_SUMMER  = 0.83   # −17% summer P
UKCP18_DRY_PET_WINTER = 1.05  # +5% winter PET
UKCP18_DRY_PET_SUMMER = 1.12  # +12% summer PET
UKCP18_WET_P_WINTER  = 1.15   # +15% winter P
UKCP18_WET_P_SUMMER  = 1.10   # +10% summer P
UKCP18_WET_PET_WINTER = 0.98  # −2% winter PET
UKCP18_WET_PET_SUMMER = 0.95  # −5% summer PET


# ── BW-mode convenience functions ────────────────────────────────────────────

def get_cluster_colours():
    """Return the active cluster colour dict (colour or BW depending on mode)."""
    return CLUSTER_COLOURS_BW if BW_MODE else CLUSTER_COLOURS


def get_cluster_colour(cid: int):
    """Return the colour for a single cluster (respects BW_MODE)."""
    src = CLUSTER_COLOURS_BW if BW_MODE else CLUSTER_COLOURS
    return src.get(cid, "#888888")


def get_bar_hatch(index: int):
    """Return a bar hatching pattern for series `index` (empty string if colour mode)."""
    if not BW_MODE:
        return ""
    return BW_BAR_HATCHES[index % len(BW_BAR_HATCHES)]


def get_line_style(index: int):
    """Return a dict of linestyle + linewidth for series `index`.

    In colour mode returns a default solid line; in BW mode cycles through
    distinct dash patterns.

    Usage: ax.plot(x, y, color=..., **get_line_style(i))
    """
    if not BW_MODE:
        return {"linestyle": "-", "linewidth": 1.5}
    return BW_LINESTYLES[index % len(BW_LINESTYLES)]


def get_line_colour(index: int):
    """Return a greyscale tone for series `index` (in BW mode).

    In colour mode returns None (caller should use their own colour).
    """
    if not BW_MODE:
        return None
    return BW_LINE_COLOURS[index % len(BW_LINE_COLOURS)]


def get_cmap(colour_cmap: str, bw_cmap: str = "Greys") -> str:
    """Return the appropriate colormap name for the current mode.

    Parameters
    ----------
    colour_cmap : str
        Colormap to use in colour mode (e.g. "viridis", "RdYlGn").
    bw_cmap : str
        Colormap to use in BW mode (default "Greys" — linear light→dark).
        Use "Greys_r" for dark→light if that better matches the semantics.

    In BW mode, returns a truncated Greys colormap (light grey → black)
    so the minimum value is distinguishable from a white background.

    Usage: cmap = get_cmap("RdYlGn")
    """
    if not BW_MODE:
        return colour_cmap
    if bw_cmap == "Greys":
        import matplotlib.pyplot as plt
        from matplotlib.colors import LinearSegmentedColormap
        base = plt.cm.Greys
        # Truncate: start from 5% grey (near-white but distinguishable) to 100% black
        colours = base(_import_numpy().linspace(0.05, 1.0, 256))
        return LinearSegmentedColormap.from_list("Greys_trunc", colours)
    return bw_cmap


def _import_numpy():
    """Lazy numpy import for get_cmap."""
    import numpy as np
    return np


# ── Observation-state classification (Script 01 / coverage figure) ────────────
# Field comments in the raw .ods records sheet encode WHY a monthly reading is
# absent or special. utils.comment_states.classify_comment() maps each comment
# to one of these states using the keyword lists below, tested in priority order
# (first match wins). Keep vocabulary here, never in the parser. Added 2026-06-15.
OBSERVATION_STATE_RULES = [
    ("flooded",      ["flood", "over wel", "welly height",
                      "water surface across", "site flooded"]),
    ("not_found",    ["not found", "not located", "lost", "locate"]),
    ("inaccessible", ["buried", "blocked", "ant", "dug up",
                      "access to measuring point"]),
    ("dry",          ["dry", "damp"]),
]

# CEH24/CEH34 level-surface flood estimates name the partner well rather than
# using a flood keyword (e.g. "infered from CEH 24 level 0.12m lower"). A comment
# referencing this paired level is treated as flooded.
OBSERVATION_FLOOD_LEVEL_HINTS = ["ceh 24", "ceh24"]

# Months treated as the dry season for INFERRED dry. A within-record blank with
# no comment in these months -- or any blank inside a missing-run that contains
# at least one recorded-dry month -- is marked dry_inferred.
DRY_SEASON_MONTHS = (7, 8, 9, 10)


# ── The four winters ──────────────────────────────────────────────────────────
#
# Seven scripts each carried a local called `WINTER_MONTHS`, and between them
# they held FOUR different sets of months. None was wrong. Each is the right
# window for the question its script asks, and the shared name is what made them
# look interchangeable — a reader who checked one and moved on would have been
# misled about the other six.
#
# So these are named for WHAT THE WINDOW IS FOR, never for the season. A constant
# called WINTER_MONTHS in config.py would have re-created the defect at a wider
# scope, and would have invited the tidy-up that merges two of them. **Merging
# any two of these is a methodological change, not housekeeping**: two are fixed
# by parties outside this project, and a third is defined by the exclusion that
# makes its metric work. See D-100.
#
# Seasonal-year convention, recorded here because it is otherwise only in a
# reader's head: Martin's seasonal year runs Spring, Summer, Autumn, Winter, so
# winter CLOSES the year rather than opening it. That convention is what makes
# Script 40's `winter2019_20` tag denote December 2019 to February 2020. It sits
# alongside, and does not replace, MSL_HYDRO_YEAR_START_MONTH = 6 (the van
# Willegen MSL hydrological year) and 00_climate_summary.py's October-start
# hydrological year used for the winter-maximum extraction. Three year
# conventions coexist in this project on purpose; each is stated where it is used.

# Recharge and flood season, Oct-Mar. The wet half-year: the window over which
# the water table refills and over which Curreli's SD15b_WINTER / SD16_WINTER
# flooding limits are evaluated. Rationale is 00_climate_summary.py's, moved here
# with the constant rather than reworded — the winter maximum is taken over these
# months, grouped into an October-start hydrological year, because a slack that
# floods does so somewhere in the refill half-year and not reliably inside DJF.
# Six months, and its complement (Apr-Sep) is the drought/recession half-year.
WINTER_RECHARGE_MONTHS       = (10, 11, 12, 1, 2, 3)   # Oct-Mar

# Wet-season climate, Nov-Mar. THIS WINDOW IS NOT OURS TO CHANGE. The UKCP18
# seasonal multipliers in this file — UKCP18_DRY_P_WINTER, UKCP18_WET_PET_WINTER
# and the rest — are published against these months, so redefining the window
# without re-deriving the multipliers would silently apply a correction to a
# season it was not measured for. Also the window over which Script 17 treats PET
# as negligible for the water-table-fluctuation method, which is a physical claim
# about these five months and not about October.
WINTER_WET_CLIMATE_MONTHS    = (11, 12, 1, 2, 3)       # Nov-Mar — UKCP18

# Hydrograph recession, Nov-Feb. The narrowest of the four, and deliberately so:
# March is excluded as transitional. The metric measures a consistent recession
# limb, and a month in which recharge and recession alternate between years adds
# variance without adding signal. The exclusion IS the metric — widening this
# window to match either of the two above would change what Script 16 reports.
WINTER_RECESSION_MONTHS      = (11, 12, 1, 2)          # Nov-Feb

# Meteorological winter, DJF. The standard climatological season, used where the
# quantity being compared is a season-mean in the ordinary sense and pairs with a
# JJA summer. External convention, like the UKCP18 window, but a universal one.
WINTER_METEOROLOGICAL_MONTHS = (12, 1, 2)              # DJF

# ── The four summers ─────────────────────────────────────────────────────────
# Batch two of the same migration, and the mirror image of the winters above:
# four windows named for the QUESTION each answers, not for the season, because
# "summer" alone does not say which of them is meant. Each is paired with a
# winter, and the pairing is the check on both.

# Summer-minimum window, Jun-Sep. The window in which the annual MINIMUM head is
# sought — the driest four months, when a slack that dries does so. This is the
# most duplicated definition in the pipeline: it was written out separately in
# SEVEN places (Scripts 02, 10a, 16, 21, 29 and the clearfell and scraping
# helper modules) and nobody ever disagreed about it, because unlike winter it
# had no contested name to argue over. Silent agreement across seven copies is
# not the same as one definition, which is why it is here.
SUMMER_MINIMUM_MONTHS        = (6, 7, 8, 9)           # Jun-Sep

# Drought and recession season, Apr-Sep. The COMPLEMENT of
# WINTER_RECHARGE_MONTHS: the two partition the year, six months each, and
# changing either without the other would leave months belonging to both seasons
# or to neither. The dry half-year over which the water table draws down.
SUMMER_DROUGHT_MONTHS        = (4, 5, 6, 7, 8, 9)     # Apr-Sep

# Dry-season climate, May-Sep. THIS WINDOW IS NOT OURS TO CHANGE, for the same
# reason as WINTER_WET_CLIMATE_MONTHS: the UKCP18 seasonal multipliers are
# published against these months. It is NOT the complement of the Nov-Mar wet
# window — April and October fall in neither, and are handled explicitly as
# shoulder months by Scripts 19 and 26b, which give them the mean of the two
# seasonal multipliers. That gap is deliberate and the shoulder logic depends on
# it; widening this window to close the gap would double-count April and October.
SUMMER_DRY_CLIMATE_MONTHS    = (5, 6, 7, 8, 9)        # May-Sep — UKCP18

# Meteorological summer, JJA. The standard climatological season, paired with
# WINTER_METEOROLOGICAL_MONTHS wherever the quantity is a season-mean in the
# ordinary sense. External convention, and a universal one.
SUMMER_METEOROLOGICAL_MONTHS = (6, 7, 8)              # JJA

# NOT here, and deliberately: CV_AMPLITUDE_MONTHS (utils/pipeline_params.py) is
# the summer-AMPLITUDE window and shares these months by coincidence of the
# calendar, not because it answers the same question; Script 02's
# AMP_SUMMER_MONTHS belongs with it rather than with SUMMER_MINIMUM_MONTHS. See
# D-100's note for the reasoning and what is owed.

# "dry at X" depths: values above this are centimetres and divided by 100 to give
# metres (e.g. "dry at 110" -> 1.10 m); at or below are already metres.
DRY_DEPTH_CM_THRESHOLD = 10.0


# ── Observation-state figure palette (Script 01 coverage figure) ──────────────
# Kept here (not in the script) alongside CLUSTER_COLOURS, with a BW variant and
# hatches so the coverage figure is greyscale-safe under BW_MODE. Added 2026-06-15.
OBS_STATE_COLOURS = {
    "interpolated":   "#E0529C",
    "dry_recorded":   "#E8A33D",
    "dry_inferred":   "#F6D9A0",
    "flooded":        "#2C7FB8",
    "not_found":      "#CFCFCF",
    "inaccessible":   "#8A8A8A",
    "not_read":       "#FFFFFF",
    "outside_record": "#FFFFFF",
}
OBS_STATE_COLOURS_BW = {
    "dry_recorded":   "#4a4a4a",
    "dry_inferred":   "#b0b0b0",
    "flooded":        "#000000",
    "not_found":      "#d8d8d8",
    "inaccessible":   "#8a8a8a",
    "not_read":       "#FFFFFF",
    "outside_record": "#FFFFFF",
}
# Hatches always applied to the obstruction states (so they read in colour AND
# greyscale); interpolated cells keep their cluster colour but gain a dot hatch
# so single-month bridges are visible. In BW_MODE, dry/flooded also gain a hatch
# for separation from the cluster greys of measured cells.
OBS_STATE_HATCH    = {"not_found": "////", "inaccessible": "xxxx",
                      "interpolated": ".."}
OBS_STATE_HATCH_BW = {"dry_recorded": "..", "flooded": "\\\\",
                      "not_found": "////", "inaccessible": "xxxx",
                      "interpolated": ".."}


def get_obs_state_colours():
    """Active observation-state palette (respects BW_MODE)."""
    return OBS_STATE_COLOURS_BW if BW_MODE else OBS_STATE_COLOURS


def get_obs_state_hatches():
    """Active observation-state hatch dict (respects BW_MODE)."""
    return OBS_STATE_HATCH_BW if BW_MODE else OBS_STATE_HATCH


# Canonical display start for the data-coverage figure. The lone 13/04/2005
# pre-system reading buckets to March 2005 under the field convention; the
# report's canonical record start is April 2005, so the figure axis starts here
# and that single March 2005 cell is dropped from the display. Added 2026-06-15.
RECORD_START_DISPLAY = "2005-04-01"


# Study-area dipwells that are monitored but excluded from the classified
# network, with the reason each is excluded. Shown as a grey presence-only block
# at the foot of the coverage figure. Off-system points (the NF series on the
# far side of the ridge, the Aberffraw wells, and temporary pool/slack markers)
# are deliberately NOT listed here — they are not part of the Newborough study
# area and do not appear in the figure. Added 2026-06-15 (author-supplied
# reasons).
EXCLUDED_STUDY_AREA_WELLS = {
    "d29":  "short record",
    "d29b": "short record",
    "d31":  "short record",
    "d33":  "short record",
    "d34":  "short record",
    "d39":  "short record",
    "d45":  "short record",
    "l4":   "short record",
    "t29":  "short record",
    "pdfs": "short record + tidal influence",
}
# The Llyn Rhos-Ddu lake gauge: a measuring point but not a dipwell and not
# classified. It is the "+1" that makes 88 classified dipwells into 89 measuring
# points. Shown in the grey block beneath the excluded dipwells.
LAKE_GAUGE_REASON = "lake gauge — non-network measuring point"

# MSL5-specific exclusions. Wells whose SSM drainage coefficient is near-zero or
# negative (ridge-flank forest wells) carry strong within-window autocorrelation
# over the 5-year MSL window, making their MSL5 change values and IDW-map
# contribution unreliable. Excluded from the MSL5 ANALYSIS ONLY (Script 26:
# Method A cluster trajectory, latest-per-well, IDW map); they remain valid for
# every other analysis (clustering, levels, BACI). Rows are retained, flagged,
# in 26_msl_5yr_per_well.csv. Mirrors the Script 18 beta_3 <= 0 exclusion. Keys
# lowercase to match the normalised well column. Added 2026-06-25.
MSL5_EXCLUDED_WELLS = {
    "ceh13": "near-zero SSM beta_3 - MSL5 unreliable over the 5yr window",
    "ceh14": "negative SSM beta_3 (SSM failure) - MSL5 unreliable over the 5yr window",
}


# === Differential-movement (Script 32) & envelope (Script 33) analyses ===
# Standalone figures: Fig 59 (secular differential drift) and Fig 60 (climate-swing
# amplification + drought-floor surface). Spring season uses MSL_SPRING_MONTHS.
# Spec-locked 2026-06-26; see CHANGELOG deltas for scripts 32 and 33.
DIFF_PANEL_MIN_FRACTION = 13.0 / 15.0       # site-mean reference-panel coverage threshold
DIFF_PER_WELL_MIN_YEARS = 8                 # min spring-years for a per-well trend
DIFF_PERIODS = {"2011_2025": (2011, 2025), "2005_2025": (2005, 2025)}
DIFF_PRIMARY_PERIOD = "2011_2025"
DIFF_IDW_POWER = 2
DIFF_IDW_GRID_M = 50.0                       # project convention (not 10b's 40 m)
DIFF_IDW_MASK_M = 450.0
DIFF_BOOT_N = 2000
DIFF_BOOT_BLOCK = 3
DIFF_BOOT_SEED = 20260626

# Site-mean trend bases (Script 32). The per-well anomaly map is a SPRING metric
# and is unaffected by this setting; what the bases govern is the site-mean
# trajectory whose trend Script 32 publishes. Two are emitted because prose that
# says "the site mean" is read as the annual level, while the committed figure
# cited in the spatial chapter is the spring one — naming the basis in the CSV is
# what stops the two being quoted interchangeably. None = every month.
DIFF_SITE_MEAN_BASES = {"spring_mam": MSL_SPRING_MONTHS, "annual_all_month": None}
DIFF_SITE_MEAN_CITED_BASIS = "spring_mam"   # the basis downstream scripts read

# Detectability of a site-wide rate. Script 32 reports, alongside each site-mean
# trend, the interannual residual spread about that trend and the smallest slope
# the period could distinguish from zero at these settings. The two-sided test's
# multiplier is derived from these quantiles in the script, not typed here, so
# changing the target power changes the reported figure.
# The settings themselves are NOT Script 32's. Every "what is the smallest
# effect this record could have seen?" calculation in the pipeline uses the same
# two, and the DIFF_ prefix named a script rather than a quantity. Defined once
# here; DIFF_POWER_ALPHA / DIFF_POWER_TARGET remain as aliases so Script 32 is
# untouched and no committed value moves (D-103).
DETECTABILITY_ALPHA = 0.05                   # two-sided significance level
DETECTABILITY_POWER = 0.80                   # target power
DIFF_POWER_ALPHA = DETECTABILITY_ALPHA
DIFF_POWER_TARGET = DETECTABILITY_POWER

# --- Script 09a: the BACI step reported with its own detection floor ---------
# BACI_DETECT_MIN_ERA_MONTHS. A step estimated from less than one annual cycle
# is confounded with season: the pre and post windows would sample different
# months, and the difference between them would carry the seasonal cycle as
# well as the intervention. Twelve months is the smallest window in which that
# cannot happen by construction. It is a real gate, not decoration - the
# shortest window in the current registry is the 27-month CEH21 post-window, so
# it sits at a factor of 2.25 and would fire on a pair added a year after its
# event. A pair failing it is WITHHELD WITH A REASON (D-085), never dropped.
BACI_DETECT_MIN_ERA_MONTHS = 12

# BACI_DETECT_HORIZON_YEARS. Extra years of post-intervention record the floor
# is reported against. Zero is the record as it stands; the rest answer "how
# much longer would this have to run?". Twenty is included because it is where
# the answer stops being about fieldwork: for a pair whose PRE-window is the
# binding constraint the floor barely moves across the whole span, and no
# amount of future monitoring collects more of the past.
BACI_DETECT_HORIZON_YEARS = (0, 2, 5, 10, 20)


# === CCW 1989-96 historic record (standalone Script 39) ===
# The CCW dipwells were 2 m deep and the record holds readings pinned at exactly
# that depth: they are left-censored, not measurements, and are dropped from
# every metric rather than compared against a prediction.
CCW_PIPE_BASE_M = -2.000                     # dipwell base, m below ground
CCW_MAX_CENSORED_FRACTION = 0.25             # a code censored more often is not admitted

# The hindcast applies coefficients fitted 2005-2026 to 1989-96. The site-wide
# beta_1 decline means the historic value was plausibly higher, so the result is
# reported as an envelope over these scalings rather than as a point estimate.
# Unity must be present: it is the fitted value and anchors the headline.
CCW_BETA1_SCALINGS = (1.00, 1.03, 1.06, 1.10)

# Restarts used to demonstrate that the spin-up has forgotten the initial
# condition before the comparison window opens, rather than assuming it.
CCW_H0_PROBE_OFFSETS_M = (-1.0, +1.0)

# --- Full-record hindcast panel (Script 39) ---
# The full-record run drives the same recurrence over the whole committed
# climate record and reports each well as an anomaly against its own modern
# mean, so a well needs enough modern record for that mean to be meaningful.
FULL_HINDCAST_MIN_MODERN_MONTHS = 60

# Rolling window used to render the panel curve. A display choice: the stored
# series is monthly and unsmoothed.
FULL_HINDCAST_SMOOTH_MONTHS = 12

# Bootstrap seeds relocated here from per-script module locals so every fixed
# seed lives in config.py (house rule: shared constants are imported, never
# mirrored). Values are unchanged from their original per-script definitions —
# relocation only, so no committed output moves.
CLUSTER_BOOT_SEED       = 20260424   # Script 02 cluster bootstrap (was module-local)
SSM_BOOT_SEED           = 20260424   # Script 03 centroid-fit bootstrap. Same VALUE as
                                     # CLUSTER_BOOT_SEED and deliberately a separate
                                     # constant: they seed different resamplings, and
                                     # importing one for the other would couple two
                                     # analyses that have no reason to move together.
                                     # Was module-local in Script 03 until 2026-08-18.

# Month-wise partition stability (Script 02, D-030). The long-standing cluster
# bootstrap resamples WELLS and answers "does the partition depend on which
# wells are in it?" (median 0.938 — it does not). These parameters drive the
# separate question "does it depend on which MONTHS are in it?", which is much
# weaker and was previously unmeasured and unreported.
#
# Months are resampled in contiguous blocks, not independently: an i.i.d. month
# resample destroys the seasonal cycle that dominates these series and would
# return a flatteringly high stability. CLUSTER_MONTH_BLOCK_MONTHS = 12 keeps
# one full cycle intact per block.
CLUSTER_MONTH_BOOT_N      = 1000       # moving-block bootstrap replicates
CLUSTER_MONTH_BLOCK_MONTHS = 12        # block length, months (one seasonal cycle)
CLUSTER_MONTH_SPLIT_N     = 200        # disjoint split-half replicates for the ARI
CLUSTER_MONTH_BOOT_SEED   = 20260816   # fixed seed - month-wise stability

# Both month-wise statistics are published, because they answer different
# questions: median co-assignment asks whether a well keeps its neighbours, the
# split-half ARI asks whether the whole partition reproduces on another period.
# They can diverge sharply, and the direction is diagnostic. Median
# co-assignment is blind to two reference clusters collapsing into one - every
# within-cluster pair still co-assigns - so whole-cluster merging pushes it UP
# while the ARI falls. A gap wider than this between them means the
# co-assignment figure is being carried by merging and must not be read as
# reproducibility. It is an alert threshold on a diagnostic, not a test
# criterion, and nothing downstream branches on it.
CLUSTER_MONTH_DEGENERACY_GAP = 0.25    # median co-assignment minus mean split-half ARI
RESIDUAL_CLIM_BOOT_SEED = 42         # Script 24b residual-climatology bootstrap (was module-local)

# === Absolute climate-removed trend (Script 36) ===
# Method: per-well OLS regression of spring level on spring CWB removes
# climate-attributable variance; secular trend fitted on residual.
# Bootstrap / AR-correction shares DIFF_BOOT_* settings (same estimator).
ACT_PER_WELL_MIN_YEARS  = DIFF_PER_WELL_MIN_YEARS   # min spring-years for a trend
ACT_PERIODS             = {                            # 2005_2025 first = primary
    "2005_2025": (2005, 2025),
    "2011_2025": (2011, 2025),
    # Driver calibration windows for Script 37. Coverage filter legitimately
    # thins short windows; 2015–2017 may survive only CEH36/CEH18/CEH21 +
    # close neighbours.
    "2006_2012": (2006, 2012),   # pre-everything: clean coastal + background signal
    "2015_2017": (2015, 2017),   # scrape window (Apr 2015) — NOT regressed by v3.0.0;
                                 # unidentifiable at 3 points, owned by BACI evidence
    "2017_2025": (2017, 2025),   # legacy clearfell window (Script 37 v2.x Stage 3);
                                 # retained for the committed CSV/changelog trail
    "2018_2025": (2018, 2025),   # NEW 2026-07-06: clearfell-isolated window for
                                 # Script 37 v3.0.0 — starts the year after the
                                 # Dec-2017 clearfell so no pre-clearfell spring
                                 # observation falls inside the endpoint groups
    # NEW 2026-07-06: expanding windows for Script 37 v3.0.0's independent
    # (falsifiable) δ₀(t) trajectory test — coast-only regression re-run on
    # each window; implied δ₀ = s_coast × δ₀_assumed, plotted vs window end.
    "2005_2010": (2005, 2010),
    "2005_2013": (2005, 2013),
    "2005_2016": (2005, 2016),
    "2005_2019": (2005, 2019),
    "2005_2022": (2005, 2022),
}
ACT_PRIMARY_PERIOD      = "2005_2025"               # 2011_2025 is robustness; see R1 fix 2026-07-05
ACT_COVERAGE_FRACTION   = 0.80                      # well must span ≥ 80 % of window
ACT_PRE_WINDOW_CUTOFF   = 2011                      # well must have ≥ 1 spring obs before this year
                                                    # (start of the shorter 2011–2025 window); fixed
                                                    # regardless of which window is being fitted so that
                                                    # short-record wells are excluded from both windows

# Climate-corrected endpoint-difference method (Script 36 → Script 37 v2.1.0).
# The short calibration windows (2006–2012, 2015–2017) are too brief for a
# per-window secular-trend fit — a 2–3-point joint fit overfits and returns
# inter-annual climate noise as spurious huge "trends" (2015–2017 gave a
# +864 mm/yr median). Instead, each well's climate sensitivity b̂ (CWB loading)
# is fit ONCE on a long pre-clearfell window, then the driver-attributable
# change over any calibration window is read as the endpoint difference of the
# climate-corrected series h_corr(t) = h(t) − b̂·CWB(t).
ACT_BHAT_WINDOW         = (2005, 2017)              # pre-clearfell window for fitting b̂ (CWB loading);
                                                    # ends before the Dec-2017 clearfell so b̂ is not
                                                    # contaminated by the post-clearfell mound. Applied
                                                    # to ALL calibration windows (single consistent rule).
ACT_ENDPOINT_FRACTION   = 1.0 / 3.0                 # fraction of window length averaged at each end for
                                                    # the endpoint difference; groups are non-overlapping
                                                    # (2 yr → 1 vs 1, 6 yr → 2 vs 2, 9 yr → 3 vs 3).

# Script 37 v3.1.0 (2026-07-06, ADDENDUM 1) — negative control C1 → C2, and
# excluding sluice-controlled C1 (Lake Edge) from the regression fit. C1 is
# buffered by Llyn Rhos-Ddu, whose level is management-set by a sluice, so
# its dh_corr reflects management rather than natural forcing — it cannot
# validate the climate correction and marginally contaminates the fit. C2
# (Dune) is driver-free and unbiased on this network (see ADDENDUM 1).
# Cluster membership is resolved at runtime via CLUSTER_LABELS — never a
# literal well list.
ACT_NEG_CONTROL_CLUSTER  = "C2"                          # negative-control cluster (reporting only)
ACT_FIT_EXCLUDE_CLUSTERS = ("C1",)                       # dropped from the regression fit
ACT_FIT_EXCLUDE_REASON   = "management-controlled lake level (sluice)"

ENVELOPE_DRY_YEARS = [2011, 2012, 2019]      # antecedent-dry deep springs


# === MSL5 two-window sensitivity (Script 34; §5.7.5 demonstration figure) ===
# Script 34 differences every admissible pair of five-year spring windows to show
# how strongly an absolute "site-mean change" depends on WHICH two windows are
# compared. It is a deliberate cautionary demonstration ("what the wrong pair of
# windows would say"), so ALL admissible pairs are retained — including those whose
# current window contains the freak-wet 2024 spring, which is the point. Window
# length reuses MSL_DEFAULT_WINDOW_YEARS (=5).
#   * MSL5_WINDOW_MIN_PANEL — a pair is admissible only if at least this many wells
#     are common to both windows (held FIXED across the pair, so composition change
#     cannot inflate the difference). 40 also auto-excludes the thin 7-well
#     2005-2009 baseline (every pair touching window-end 2009 has <=7 common wells).
#   * MSL5_WINDOW_ANCHOR — the §4.12 comparison (window-ends), validated against the
#     committed -96.8 mm (n=59) headline.
# Spec-locked 2026-06-27 (all-pairs demonstration); supersedes the wet-2024-excluded
# variant. See CHANGELOG delta for Script 34 v0.3.0.
MSL5_WINDOW_MIN_PANEL = 40
MSL5_WINDOW_ANCHOR    = (2017, 2023)
ENVELOPE_WET_YEARS = [2014, 2016, 2021, 2024]  # antecedent-wet shallow springs (2006 excluded;
#   2016 added 2026-06-27: Oct-Mar antecedent 697 mm = wettest recharge season on record, the
#   mirror of why 2006 is excluded. Recovers CEH8/CEH15 into the panel with proper multi-year
#   wet states. Network-mean swing shifts 752 -> 735 mm; forest/lake anchor unchanged (1.25x/0.59x).)
ENVELOPE_MIN_YEARS_PER_EXTREME = 2           # of N must be present (per extreme side)
# Recent (extended-network) window: a deliberately separate, more recent envelope that the
# 2014-2017-installed wells (CEH40/41/42, FE1/2/3, NW8b) actually observed. Its dry extreme is
# milder than 2011/12, so the recent panel is NOT magnitude-comparable to the canonical panel
# and is captioned as a conservative recent lower bound. Spec-locked 2026-06-27.
ENVELOPE_RECENT_DRY_YEARS = [2019, 2020, 2025]   # driest recent springs all late wells observed
ENVELOPE_RECENT_WET_YEARS = [2021, 2024]         # the two genuinely antecedent-wet recent springs
# Wells admitted to the per-well CSV + shown as a distinct flagged marker, but EXCLUDED from both
# the interpolated surface and the network-mean denominator (single dry-extreme year, n_dry=1).
# Empty: CEH7 was dropped 2026-06-27 (Martin's call) — its single 2011 dry year carried ~160 mm
# noise and it added little beyond an isolated eastern marker. Mechanism retained for future use.
ENVELOPE_FLAGGED_SINGLE_DRY = set()
ENVELOPE_ECO_THRESHOLDS_MM = [-1000.0 * SD15b, -1000.0 * SD16]  # SD15b wet-slack 0.61 m, SD16 dry-slack 0.98 m (Curreli 2013)
ENVELOPE_ECO_THRESHOLD_LABELS = {-1000.0 * SD15b: "SD15b (wet slack)", -1000.0 * SD16: "SD16 (dry slack)"}
# Wells excluded from the Figure 60b dry-year spring-depth SURFACE interpolation only
# (kept as distinctly-marked points). CEH10 was sited (winter 2006) on a raised piece of
# ground BETWEEN slacks; it floods only when the neighbouring slack overtops, so it
# measures the raised inter-slack ground / slack edge, not the slack-floor water table.
# Its genuinely deep dry-year reading therefore must not be interpolated into the
# surrounding slacks (it would smear a false deep zone). Shown as a slack-edge marker.
ENVELOPE_DEPTH_INTERP_EXCLUDE = {"ceh10"}

# === Per-well climate-sensitivity coefficient (Script 35; Paper 1 aquifer characterisation) ===
# A frame-independent per-well amplification coefficient on the SPRING water table
# (MSL_SPRING_MONTHS), co-temporally normalised so wells measured on different extreme-year
# subsets stay comparable, and extended to short/inconsistent-record wells the matched surface
# and the SSM cannot reach. Spec-locked 2026-06-27 (SPEC_script35_per_well_amplification_metric.md).
#   * Pools are antecedent-screened supersets of the canonical + recent extreme sets.
#   * Reference core = wells with FULL dry coverage (all DRY_POOL years) and >=2 wet years; the
#     co-temporal reference swing is this core's mean swing recomputed over each target well's
#     own extreme years.
#   * Tiers by record completeness: A (>=2 dry & >=2 wet), B (>=1 each, not A), C (1 dry & 1 wet).
ENVELOPE_METRIC_DRY_POOL = [2011, 2012, 2019, 2020, 2025]
ENVELOPE_METRIC_WET_POOL = [2014, 2016, 2021, 2024]
ENVELOPE_METRIC_REF_CORE = "full_dry_coverage"   # core = all DRY_POOL years present & >=2 wet
ENVELOPE_METRIC_REF_MIN_WET = 2
ENVELOPE_METRIC_CI = "jackknife_90"              # delete-one-year jackknife; 90% (=1.645 SE)
ENVELOPE_METRIC_CI_Z = 1.645
# Blanket include (2026-06-27): the amplification coefficient is OBSERVATIONAL and does not use
# the SSM, so the SSM-failure exclusion (MSL5_EXCLUDED_WELLS = CEH13/CEH14) does NOT apply to it.
# CEH13/CEH14 have clean, complete spring records and are the two most extreme slow-drainage wells
# (highest amplification) — the SSM failed for them BECAUSE they barely drain, which is the very
# signal the coefficient measures directly. They are therefore included in the amplification
# coefficient + surface; only the lake gauge is excluded. The MSL5 exclusion is retained
# elsewhere (Scripts 20/26) where it is justified. The amp-vs-β CALIBRATION regression, however,
# drops the SSM-unreliable wells (their β is the untrustworthy axis) — a property of that
# validation, not a caveat on the coefficient.
ENVELOPE_METRIC_EXCLUDE = set()                  # amplification coefficient: lake gauge only (dropped at load)
ENVELOPE_METRIC_CALIB_EXCLUDE = set(MSL5_EXCLUDED_WELLS)  # SSM-unreliable: drop from the β regression only

# Lake-gauge column keys to drop from well analyses (Llyn Rhos-Ddu is a lake gauge,
# not a dipwell). Lowercase to match the normalised well column.
LAKE_GAUGE_KEYS = {"llyn rhos", "llyn rhos-ddu", "llyn rhos ddu"}

# ── Figure sizing for A4 report placement ────────────────────────────────────
# Target on-paper geometry for report figures. utils/render_utils.render_figure
# uses these to cap the save dpi so every figure lands at FIG_TARGET_PRINT_DPI
# at its placed size, regardless of the figsize a script used. Changing the
# target here + rerunning the pipeline resizes all outputs; no per-script edits.
FIG_TARGET_WIDTH_MM = 160.0    # A4 text-block width (210 mm − side margins)
FIG_TARGET_HEIGHT_MM = 247.0   # A4 text-block height for full-page figures
FIG_TARGET_PRINT_DPI = 300     # DPI ceiling at placed size

# Font legibility at placed size. render_figure scales every text element of a
# figure up (post-layout, pre-save) so the smallest tick label prints at
# >= FIG_MIN_PLACED_PT once the figure is placed at FIG_TARGET_WIDTH_MM. The
# enlargement is capped at FIG_MAX_FONT_SCALE to limit collision risk in dense
# figures; figures still below the minimum at the cap are flagged on the
# console as the residual hand-re-authoring list. (Cap 1.7 auto-fixes placed
# sizes down to FIG_MIN_PLACED_PT/1.7 = 3.82 pt — everything in the 2026-07-19
# candidate list except the sub-3.8 pt core of the severe tier.)
# Autoscaling is opt-in per call (autoscale_fonts=True); see render_utils
# v1.4.0. Callers may override the target via min_placed_pt=.
FIG_MIN_PLACED_PT = 6.5        # smallest acceptable printed label size (pt)
FIG_MAX_FONT_SCALE = 1.7       # ceiling on the automatic text enlargement


# ── Northern break in slope — detection parameters (Script 12, D-099) ────────
#
# WHAT IS BEING FOUND. The northern physiographic boundary of the site: the
# southern edge of the dune massif, where it gives way to the low Malltraeth
# plain. Llyn Rhos-Ddu sits at its foot. It is a CANDIDATE landward limit for
# the sand aquifer and is reported as modelled and unconfirmed — nothing here
# establishes it as the aquifer limit.
#
# THIS IS THE NORTHERN BOUNDARY ONLY. The window deliberately excludes most of
# the site. It is not a site-wide product and must not be read as one.
#
# The window. Chosen to contain the massif-to-plain transition and nothing else;
# a wider window admits the coastal frontage and the southern scrapes, which are
# different features and would be found by the same rule.
BREAK_WINDOW_E_MIN = 241000.0   # m OSGB36
BREAK_WINDOW_E_MAX = 243800.0   # m OSGB36 — 1400 columns of the 2 m DEM
BREAK_WINDOW_N_MIN = 364100.0   # m OSGB36
BREAK_WINDOW_N_MAX = 365600.0   # m OSGB36

# Along-profile smoothing, in DEM samples. 21 samples of a 2 m DEM is 42 m — long
# enough to average out individual dune faces, short enough to keep the massif
# edge. Padded by edge repetition so the ends are not dragged toward zero.
BREAK_SMOOTH_SAMPLES = 21

# The plain reference. The 10th percentile of the smoothed column, not its
# minimum: a minimum is one pixel and follows any hollow. Everything else in the
# rule is measured RELATIVE to this, which is what makes the detector work where
# absolute-elevation and slope-based rules fail (see D-099).
BREAK_PLAIN_PERCENTILE = 10

# Column admission. A column with no low ground in it has no plain to measure
# from; a column with no high ground in it has no massif to find the edge of.
BREAK_MAX_PLAIN_ELEV_M = 12.0   # skip if the plain reference is above this
BREAK_MIN_RELIEF_M     = 6.0    # skip if smoothed max minus plain is below this

# The break itself: walking NORTH to SOUTH, the first sample within this height
# of the plain reference. That is the southern edge of the northern massif.
BREAK_RELATIVE_M = 3.0

# A break found in the first few samples means the column began on the plain
# already, so there was no massif edge inside the window to find.
BREAK_MIN_INDEX = 5

# Alongshore outlier rejection: a median filter across easting columns, applied
# to the break northings after sorting by easting. 61 columns of a 2 m DEM is
# 122 m.
BREAK_MEDIAN_COLUMNS = 61

# ── Gate tolerances (D-085 / D-089 shape: withhold with a reason) ────────────
#
# BREAK_ELEV_SD_TOL_M. An incoherent line means the rule found DIFFERENT
# features in different columns, and averaging those gives a plausible-looking
# number that describes nothing. That must fail loudly rather than emit.
#
# The bound is not chosen as a number; it is set equal to BREAK_RELATIVE_M, the
# vertical band that DEFINES the feature. The reasoning: columns declared to be
# on one surface are, by construction, within that band of their own plain
# reference, so a scatter of break elevations wider than the band is evidence
# the columns are not on one surface at all. Measured against the record it has
# to discriminate: the accepted rule scatters at sd 1.68 m (56 % of the bound),
# and the two rejected rules — first-flattening-walking-south, which catches an
# upper bench, and steepest-sustained-descent, which catches individual dune
# faces — scatter at sd 8.00 m, 2.7x outside it. It would have caught both
# without being tuned to pass the third.
BREAK_ELEV_SD_TOL_M = BREAK_RELATIVE_M

# BREAK_MIN_COLUMNS. Columns legitimately fail at the ends of the window, where
# there is no massif — that is the detector working, not failing, so this is not
# a high fraction of the window. It is set to five times the median-filter width
# instead: a run shorter than a few filter widths is mostly the filter's own
# edge handling, not a boundary. 5 x 61 = 305 columns = 610 m.
BREAK_MIN_COLUMNS = 5 * BREAK_MEDIAN_COLUMNS
