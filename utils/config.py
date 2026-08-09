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
# Single canonical version string for the analysis pipeline. run_analysis.py
# sets its __version__ from this value, and build_manifest() stamps it into
# outputs/pipeline_manifest.json, so the manifest, the Methods Supplement / SI,
# and the Zenodo release all pin to one string. Bump on any release.
PIPELINE_VERSION = "2.3.0"

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
# well data is correctly labelled and lag-0 gives the same physical pairing.
# All regression coefficients are numerically identical.
HEADLINE_LAG = 0

# Canopy interception fraction for Corsican pine (Freeman, 2008).
# Measured at C5 (Coastal Forest) throughfall gauge, applied to all
# forested clusters (C4 and C5). The interception is a partition of the
# PET energy budget: ET_at_WT = PET − I, so I is NOT additive to PET.
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
#   DRAWDOWN_H0_MM : forest interception deficit at the felling edge (mm).
#   DRAWDOWN_K_MDAY: aquifer hydraulic conductivity (m/day; Betson 2002).
#   DRAWDOWN_B_M   : saturated aquifer thickness used for λ (m; estimate).
# Previously hardcoded as in-function locals in Script 20.
DRAWDOWN_H0_MM  = 150.0
DRAWDOWN_K_MDAY = 6.0
DRAWDOWN_B_M    = 5.0

# --- Scrape rise-zone + coastal-retreat geometry (Scripts 20, 09d, 09f) --------
# Shared geometry constants for the scrape drain-cone and coastal-erosion fields.
# Previously declared as in-function or module locals in Script 20 and mirrored
# in Scripts 09d/09f; centralised here so all three read one definition.
#   SCRAPE_RISE_BUFFER_M : radius of the scrape rise (slack) zone (m); the
#                          drawdown cone is measured from this buffer outward.
#   COAST_RETREAT_M      : single-event shoreline retreat visualised (m;
#                          Storm-Brendan-scale exemplar, Pye & Blott 2024).
#   COAST_RETREAT_RATE   : long-term storm-inclusive retreat rate (m/yr;
#                          ≈50 m / 2014–2020, Forgrave 2020) — the normaliser
#                          converting a retreat event to an edge drawdown.
SCRAPE_RISE_BUFFER_M = 10.0
COAST_RETREAT_M      = 6.0
COAST_RETREAT_RATE   = 8.3
# Cumulative shoreline retreat over the 2005→2025 study window (m). Observed
# figure (≈50 m since 2006, Forgrave 2020 / Pye & Blott 2024), used by the
# 2005→2025 driver-change map (Script 20 plot_driver_change_2005_2025). Not
# derived from COAST_RETREAT_RATE × 20 (which would give ~166 m and overstate
# the accumulation); the observed 20-year retreat is the smaller ~50 m.
COAST_RETREAT_2005_2025_M = 50.0
# Effective hydraulic coastal retreat calibrated from Script 37 groundwater validation
# (n=24 clean wells, 2005–2025 window, single-parameter OLS with SLR fixed at 4 mm/yr).
# Distinct from COAST_RETREAT_2005_2025_M (50 m; physical shoreline measurement, Pye &
# Blott 2024).  The larger effective value reflects integrated hydraulic response across
# the full bay frontage vs the reference transect.  Scales linearly with window duration.
COAST_RETREAT_EFFECTIVE_M = 105.0

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

# ── Broadleaf restock canopy-establishment fractions (2005→2025 driver map) ────
# The broadleaf restock block (data/geo/broadleaf_restock.kml) was felled 1993,
# restocked 1998, and reaches full canopy by 2025. For the 2005→2025 modelled
# driver-CHANGE map (Script 20 plot_driver_change_2005_2025) only the INCREMENT
# of interception developed over the window contributes:
#     Δh_BL = (BL_CANOPY_FRACTION_2025 − BL_CANOPY_FRACTION_2005) × H0_BL_full
# where H0_BL_full = DRAWDOWN_H0_MM × (BROADLEAF_INTERCEPTION / FOREST_INTERCEPTION)
#                  = 150 × (0.15 / 0.24) ≈ 94 mm at full canopy.
# f_2005 = 0.4 (Martin's judgement, 2026-07-05) → increment 0.6 × 94 ≈ 56 mm at
# source. This is the least-constrained field on the map; the caption flags the
# BL patch as modelled/indicative. Stored here (not hardcoded) so the basis is
# auditable and the sensitivity can be varied.
BL_CANOPY_FRACTION_2005 = 0.4
BL_CANOPY_FRACTION_2025 = 1.0

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
    "ceh14": "negative SSM beta_3 (SSM failure, NSE -3.21) - MSL5 unreliable over the 5yr window",
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

# Bootstrap seeds relocated here from per-script module locals so every fixed
# seed lives in config.py (house rule: shared constants are imported, never
# mirrored). Values are unchanged from their original per-script definitions —
# relocation only, so no committed output moves.
CLUSTER_BOOT_SEED       = 20260424   # Script 02 cluster bootstrap (was module-local)
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
#   * MSL5_WINDOW_ANCHOR — the §4.9.8 comparison (window-ends), validated against the
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
