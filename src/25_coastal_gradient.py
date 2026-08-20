"""
25_coastal_gradient.py — Coastal-Retreat Gradient Analysis

Coastal-retreat gradient analysis
=================================

Fits a network-scale, physics-based non-linear regression to per-well
water-table trends against perpendicular distance to the eroding
Caernarfon Bay shoreline. Two functional forms are fitted:

    Linear-with-cutoff (Dupuit–Forchheimer strip aquifer):
        δ(d) = max(δ_0 · (1 − d/L), 0) + c

    Exponential decay (diffusive / transient response):
        δ(d) = δ_0 · exp(−d/L) + c

where δ(d) is the rate of water-table change (mm/yr) at distance d (m)
from the western foreshore, δ_0 is the coast-edge anomaly above climate,
L is the inland reach, and c is the far-field climate background.

The fits are produced at three increasingly stringent specifications to
test the forest-cover confound:

    [1] Full network        — all clusters, clearfell-zone wells dropped
    [2] Forest-free network — C1 + C2 + C3 only (drops C4 + C5 entirely)
    [3] C3 only             — single non-forested cluster, c held to the
                              network value because C3 contains no well
                              at d → 0 and a 3-parameter fit on this
                              restricted distance range is under-identified

The script then applies the headline (forest-free linear-capped) fit to:

    - Each cluster's observed seasonal-metric decline, producing a
      coastal-gradient / climate-CWB / far-field-offset / unexplained
      partition on a declared balanced observed basis
    - The BACI ANCOVA (Script 10a) easting × time absorption, producing
      a corroboration check showing whether the BACI's spatial
      covariate is absorbing the gradient signal the model predicts

This is a stand-alone analytic step — it reads pipeline intermediates
and a versioned distance-to-coast CSV (data/well_distance_to_coast.csv)
but does not feed downstream pipeline scripts.

Inputs
------
data/well_distance_to_coast.csv        OS perpendicular distances
outputs/01_wells_clean.csv             Reference network water levels
outputs/01_wells_extended.csv          Extended-network water levels
outputs/01_locations.csv               Well coordinates
outputs/01_climate.csv                 RAF Valley P, PET
outputs/03_master_data.csv             Cluster assignments
outputs/14_climate_projections/14_summer_trend_stats.csv
                                       Cluster-centroid summer-min slopes
outputs/10_clearfell_baci/10a_02_ancova_full_coefficients.csv
                                       BACI ANCOVA coefficients
outputs/20_spatial_figures/20_msl5_change_perwell.csv
                                       Raw 2017→2023 MSL5 change per well
                                       (for the §5.7.5 Check 2 correlation;
                                       Script 20 runs earlier in the pipeline)

Outputs
-------
25_01_panel_fit_parameters.csv         All fits (3 specs × 2 forms)
25_02_per_well_summer_min_slopes.csv   Per-well OLS slopes
25_03_cluster_partition.csv            Cluster attribution table — the
                                       balanced annual-mean observed decline
                                       decomposed into coastal gradient,
                                       climate (CWB trend), far-field offset
                                       and unexplained remainder, with
                                       per-component %-of-basis columns.  The
                                       observed centroid and per-well-mean
                                       slopes are retained as context columns;
                                       decomposition_basis names the column the
                                       decomposition is computed against
25_04_baci_corroboration.csv           BACI absorption vs model prediction
25_05_fit_diagnostic.jpg               Two-panel figure (a) per-well + fits,
                                       (b) cluster stacked bars
25_06_baci_corroboration_chart.jpg     Forest plot of corroboration
25_07_cluster_decomposition.png        Horizontal stacked-bar figure of the
                                       per-cluster decomposition (folded in
                                       from standalone Script 30, 2026-05-29)
25_10_record_length_composition.csv    Per-cluster record-length composition
                                       diagnostic — why a far-field decline
                                       appears in the per-well mean
25_11_matched_window_sensitivity.csv   REPORTED ONLY: headline spec refitted on
                                       the long-record well subset and on its
                                       complement.  Not adopted; delta_0 and L
                                       in 25_01 are unchanged
25_report_numbers.csv                  Headline numbers in standard format
                                       (incl. §5.7.5 Check 2: raw MSL5-change
                                       vs summer-min-slope Pearson/Spearman)

Provenance of well_distance_to_coast.csv
----------------------------------------
Computed once out-of-pipeline from OS Open Map Local TidalBoundary
(SH_TidalBoundary.shp), using the full Caernarfon Bay MHW (High Water
Mark) classification — two connected lines forming the 15.0 km eroding
shoreline. Menai Strait and Llanddwyn Island HWM excluded. Perpendicular
distance computed via shapely.geometry.Point.distance(LineString) in
EPSG:27700. See data/COASTLINE_PROVENANCE.md.
"""

from __future__ import annotations

__version__ = "1.8.0"  # Hollingham (2026) — 2026-08-20.  Adds the fit-window
#         sensitivity sweep (25_12) and an optional canopy x time regressor.
#         WINDOW SWEEP.  25_11 varies the WELL SET; 25_12 varies the WINDOW
#         with the well set held fixed, which is the axis that actually moves
#         the far-field constant.  Sweeping the first month from 2005-03 to
#         2014-02 on the forest-free panel moves c from -0.17 to +24.18 mm/yr
#         while delta_0 stays negative throughout — c is a property of the fit
#         window, not a rate, and is not quoted as one anywhere.  Each row
#         carries the OBSERVED far-field trend over the same window
#         (balanced annual mean, wells beyond WINDOW_SWEEP_FAR_FIELD_M), so
#         the constant is judged against an observable rather than asserted
#         meaningless: it tracks that trend (r about +0.5) but is biased high
#         by roughly 6 mm/yr and swings several times as far.  Fits sitting on
#         a parameter bound are written out with usable=False rather than
#         dropped silently.
#         CANOPY TERM.  fit_panel(forest_term=True) adds a canopy x time
#         regressor keyed on the in_forest LAND-COVER flag Script 01 v1.12.0
#         writes, so the full network can be fitted with forest cover
#         controlled explicitly instead of testing the confound by dropping
#         the forested clusters and comparing subsets.  load_panel falls back
#         to the C4/C5 cluster proxy with a warning until Script 01 is rerun;
#         the proxy disagrees with the footprint at six wells, so the fallback
#         is a degraded answer, not an equivalent one.
#
# 1.7.0 — Hollingham (2026) — 2026-08-20.  Two defects in the
#         panel well-set, both of which biased the headline coast-edge anomaly.
#         (a) EXTENDED-WELL CLUSTERS.  load_panel() took cluster from
#         03_master_data, which covers the reference network only, so all 18
#         extended wells arrived as NaN.  exclude_forested filters on cluster
#         and NaN.isin(FOREST_CIDS) is False, so no extended well was ever
#         excluded: the "forest-free" panel silently kept ceh3 and nw8
#         (best-match C5) and ceh15, lis1, nw12 (best-match C4), with ceh3 at
#         176 m one of the three nearest wells to the shore.  Cluster is now
#         filled from the sitewide Pearson audit, the same source Script 18
#         uses for extended wells (S.12).  Four wells best-matching C3
#         (ceh38, nw8b, p1, pe) correspondingly join the C3-only fit.
#         (b) SCRAPE EXCLUSION.  SCRAPED_WELLS = ["ceh36"] was a per-script
#         local contradicting config.SCRAPE_KML_FILES, which names six wells
#         inside scrape footprints.  Treatment now comes from
#         scraping_common.apply_scrape_treatment(): ceh40/41/42 were installed
#         after their scrape and are dropped; ceh18/ceh21 were scraped in
#         October 2023 only and are censored at that date, keeping 87% and 85%
#         of their records rather than losing two near-shore anchors.
#         Effect on the forest-free linear-capped fit: delta_0 -29.22 -> -26.42
#         (SE 1.91 -> 2.25), L 900.7 -> 963.9, c +0.18 -> -0.17, 68 -> 60
#         wells.  L is unmoved within one SE; delta_0 moves by 2.8 mm/yr.
#
# 1.6.2 — Hollingham (2026) — 2026-08-19.  Console/comment text
#         only: 25_11's "nothing downstream reads it" is true again — Script 09f
#         read it for one afternoon and no longer does (D-043).  The 1.6.1 text
#         is reverted; the module comment records the round trip so the next
#         reader does not have to.
#
# 1.6.1 — said 09f reads identified_sum_mm_yr for its far-field band (D-042).
#         Superseded by 1.6.2 the same day; the band was withdrawn.
#
# 1.6.0 — Cluster attribution rebuilt onto a declared, balanced observed basis.
#         25_03 previously subtracted (gradient + c) from the Script-14
#         cluster-CENTROID slope and called the remainder "residual", so three
#         different bases met in one table: the panel δ(d) is CWB-adjusted and
#         all-season, the 25_02 per-well slopes are raw annual seasonal-metric
#         OLS, and the observed column was a centroid slope.  The decomposition
#         is now computed against observed_balanced_annual_mean_mm_yr — the
#         slope of the annual cross-well mean of the per-well seasonal metric,
#         which uses the per-well well-set but is not an average of
#         differently-windowed fits — and decomposition_basis names that column
#         in the file.  c is NOT separately identified: it trades off against
#         the CWB covariate's trend contribution, so the fitted constant is
#         carried as far_field_offset_mm_yr (its literal meaning) beside a new
#         climate_cwb_mm_yr = 1000·β_cwb·d(CWB)/dt, and only their sum is
#         recoverable.  predicted_climate_mm_yr → far_field_offset_mm_yr,
#         predicted_total_mm_yr → modelled_total_mm_yr, residual_mm_yr →
#         unexplained_mm_yr, *_pct_of_observed → *_pct_of_basis: every rename is
#         a column whose meaning or basis changed, so a stale reader gets a
#         KeyError rather than a silently different quantity.  δ₀ and L are
#         untouched — no refit of the headline model.  New: 25_10 record-length
#         composition (why the old table looked plausible) and 25_11
#         matched-window sensitivity (REPORTED ONLY, not adopted).  fit_panel()
#         additionally returns the absorbed CWB coefficient; its search, popt,
#         perr and AIC are unchanged, so 25_01/25_02/25_04/25_09 reproduce.
#         Store-time rounding removed from 25_03 (D-035).
# 1.5.1 — Added fit_season_interaction(): a full-panel single-model test of
#         whether the coastal-retreat gradient is itself seasonal —
#         δ(d)·t·(1 + γ·spring), H0 γ=0 — emitting 25_09_season_interaction_test.csv
#         (forest-free lin-cap + exp).  fit_panel() is untouched (byte-identical).
#         Also moved the 25_08 comparison legend outside to the right.
# 1.5.0 — Added the spring mean (Mar–May) as a second per-well seasonal metric,
#         run through the identical partition code path as the summer minimum.
#         The panel fit / coastal-retreat gradient is ALL-SEASON
#         (metric-independent) and remains the headline; it is applied to BOTH
#         metrics.  compute_per_well_slopes() gains a metric argument (spring:
#         Mar–May calendar-year mean, strict 3-of-3 guard) and cluster_partition
#         is run per metric against the matching Script 14 CSV (summer vs the new
#         14_spring_trend_stats.csv).  main() runs both metrics in one pass
#         (optional --metric flag for ad-hoc single-metric runs).  New outputs:
#         25_02_per_well_spring_mean_slopes, 25_03_cluster_partition_spring,
#         25_05/25_07 spring figure analogues, and 25_08 spring-vs-summer
#         comparison (CSV + figure).  25_01 gains six MAM-only panel refits as
#         sensitivity rows beside the all-season rows.  25_04 (BACI
#         corroboration) is metric-independent and is NOT re-emitted.  All
#         committed summer outputs (25_01 prefix, 25_02, 25_03, 25_04, 25_05,
#         25_06, 25_07, 25_report_numbers) reproduce byte-identically.  Mirrors
#         the 09c/10d/10l/14 seasonal refactor; spring season/rule from config.
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import least_squares
from scipy.stats import t as t_dist
from scipy.stats import pearsonr, spearmanr

# ── Pipeline imports ──────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils import paths  # noqa: E402
from utils.config import (  # noqa: E402
    CLUSTER_COLOURS, CLUSTER_LABELS, FOREST_CIDS,
    MSL_SPRING_MONTHS, MSL_MIN_MONTHS_PER_SPRING,
)
from utils.clearfell_common import (  # noqa: E402
    IMPACT_WELLS, EDGE_WELLS, FOREST_CONTROL_WELLS,
    COASTAL_CONTROL_WELLS, CLIMATE_CONTROL_WELLS,
)
from utils.scraping_common import apply_scrape_treatment  # noqa: E402
from utils.render_utils import render_figure

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


# ── Constants ────────────────────────────────────────────────────────────────
# Wells excluded from the panel regression because they are subject to
# direct intervention effects that would contaminate the gradient signal.
FE_WELLS = ["fe1", "fe2", "fe3", "fe4"]
# CEH36 is the scraping study's own impact well and is dropped outright.
# The other five wells inside a scrape footprint are handled by
# scraping_common.apply_scrape_treatment(), which drops the three
# installed after their scrape and censors the two installed before it
# at the scrape date, rather than discarding their clean record.
SCRAPED_WELLS = ["ceh36"]
NON_DIPWELLS = ["llyn rhos"]

# BACI clearfell-zone wells (Impact + Edge + Forest controls + Coastal
# controls) — dropped from the full and forest-free panel fits so that
# the felling-induced water-table rise does not appear as a residual.
# These lists are imported from clearfell_common so any update to the
# BACI design propagates automatically.
CLEARFELL_ZONE = list(set(
    IMPACT_WELLS + EDGE_WELLS + FOREST_CONTROL_WELLS + COASTAL_CONTROL_WELLS
))

# Within the C3-only fit, only WMC3 (BACI Impact) is in C3 AND in the
# clearfell zone — drop it. CEH36 is also in C3 but already in
# SCRAPED_WELLS. All other C3 wells are retained.
CLEARFELL_ZONE_IN_C3 = list(
    (set(CLEARFELL_ZONE) & {"wmc3", "ceh19", "ceh17"}) | {"wmc3"}
)

PANEL_OBS_MIN_YEARS = 8  # per-well seasonal slopes require ≥8 years

# ── Fit-window sensitivity sweep (25_12) ─────────────────────────────────────
# The far-field constant c is not a rate. Holding the well set fixed and
# moving only the first month of the fit window moves c across tens of
# mm/yr and changes its sign, while δ₀ stays negative throughout. The sweep
# measures that directly, and carries the OBSERVED far-field trend over the
# same window beside it — the quantity c is implicitly estimating — so the
# fitted constant can be judged against an observable rather than asserted
# to be meaningless.
WINDOW_SWEEP_MIN_YEARS   = 12.0    # shorter windows do not identify L
WINDOW_SWEEP_FAR_FIELD_M = 950.0   # "far field" = beyond the fitted reach
WINDOW_SWEEP_BOUND_TOL   = 0.01    # fraction of a bound's range; at-bound fits
                                   # are reported but flagged unusable

# Matched-window sensitivity (v1.6.0) — REPORTED ONLY, never adopted.  The
# panel's record-start distribution has a twelve-month break between the last
# early-start well and the next one; this cutoff sits inside that break and so
# separates the long-record wells from those added later without splitting a
# cohort.  The refit it drives moves δ₀ and L, which are published results, so
# it is emitted to 25_11 for inspection and nothing downstream reads it
# (D-040).  Script 09f briefly did, for a far-field band that is now withdrawn
# (D-042 superseded by D-043); 25_11 is once again read by nothing.
MATCHED_WINDOW_RECORD_START = "2007-01-01"

# Spring (MAM) per-well metric, v1.5.0.  Season and 3-of-3 strictness come from
# config so "spring" has one definition across the pipeline.  The summer minimum
# is indexed by the Oct-start hydrological year; the spring mean sits wholly
# inside a calendar year and is indexed by calendar year (as Script 36 does).
SPRING_MONTHS = list(MSL_SPRING_MONTHS)          # (3, 4, 5)
SPRING_MIN_MONTHS = MSL_MIN_MONTHS_PER_SPRING    # 3-of-3

# ── Figure label sets (per metric) ─────────────────────────────────────────────
# The summer strings are the committed ones and must render unchanged; the
# figure functions default to _SUMMER_FIG so their existing call sites reproduce
# byte-identically.
_SUMMER_FIG = {
    "slope_ylabel": "Summer-minimum slope (mm yr⁻¹)",
    "diag_a_title": "(a) Per-well summer-minimum slopes vs distance to coast",
    "decomp_xlabel": "Summer-minimum slope (mm/yr)",
    "decomp_title": (
        "Per-cluster decomposition of the observed summer-minimum decline\n"
        "Balanced annual mean = coastal gradient + climate (CWB) "
        "+ far-field offset + unexplained"),
}
_SPRING_FIG = {
    "slope_ylabel": "Spring-mean slope (mm yr⁻¹)",
    "diag_a_title": "(a) Per-well spring-mean slopes vs distance to coast",
    "decomp_xlabel": "Spring-mean slope (mm/yr)",
    "decomp_title": (
        "Per-cluster decomposition of the observed spring-mean change\n"
        "Balanced annual mean = coastal gradient + climate (CWB) "
        "+ far-field offset + unexplained"),
}

# ── Per-metric specs ───────────────────────────────────────────────────────────
# Only the per-well metric and the Script-14 observed-centroid CSV differ; the
# panel fit / gradient is all-season (metric-independent) and is applied to both
# metrics as the headline.  25_04 (BACI corroboration) is metric-independent and
# is emitted once (summer only).
_METRICS = [
    {
        "key": "summer_min",
        "label": "summer-min",
        "s14_csv": paths.OUT_14_SUMMER_TREND_CSV,
        "out_per_well": paths.OUT_25_PER_WELL_SLOPES,
        "out_partition": paths.OUT_25_CLUSTER_PARTITION,
        "out_diag": paths.OUT_25_FIT_DIAGNOSTIC,
        "out_decomp": paths.OUT_25_CLUSTER_DECOMP_FIG,
        "out_composition": paths.OUT_25_RECORD_LENGTH_COMPOSITION,
        "figlabels": _SUMMER_FIG,
    },
    {
        "key": "spring_mean",
        "label": "spring-mean",
        "s14_csv": paths.OUT_14_SPRING_TREND_CSV,
        "out_per_well": paths.OUT_25_PER_WELL_SLOPES_SPRING,
        "out_partition": paths.OUT_25_CLUSTER_PARTITION_SPRING,
        "out_diag": paths.OUT_25_FIT_DIAGNOSTIC_SPRING,
        "out_decomp": paths.OUT_25_CLUSTER_DECOMP_FIG_SPRING,
        "out_composition": paths.OUT_25_RECORD_LENGTH_COMPOSITION_SPRING,
        "figlabels": _SPRING_FIG,
    },
]


# ── Models ────────────────────────────────────────────────────────────────────

def model_exp(d, delta_0, L, c):
    """Exponential decay: δ(d) = δ_0 · exp(−d/L) + c."""
    return delta_0 * np.exp(-d / L) + c


def model_linear_capped(d, delta_0, L, c):
    """Linear-with-cutoff (Dupuit–Forchheimer strip):

        δ(d) = max(δ_0 · (1 − d/L), 0) + c    if δ_0 > 0
        δ(d) = min(δ_0 · (1 − d/L), 0) + c    if δ_0 < 0

    The clamp ensures the gradient does not change sign at d > L; it
    simply asymptotes to the climate background c.
    """
    inner = delta_0 * (1.0 - d / L)
    inner = np.where(delta_0 < 0, np.minimum(inner, 0), np.maximum(inner, 0))
    return inner + c


# ── Data loading ──────────────────────────────────────────────────────────────

def load_panel(distances: pd.DataFrame, exclude_forested: bool = False,
                restrict_cluster: int | None = None) -> pd.DataFrame:
    """Build the long-form monthly panel with all needed covariates.

    Parameters
    ----------
    distances : DataFrame with columns [well, dist_coast_m]
    exclude_forested : if True, drop C4 and C5 wells entirely
        (the forest-free network specification)
    restrict_cluster : if set, restrict to a single cluster only
        (the C3-only specification expects 3)
    """
    wc = pd.read_csv(paths.INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    we = pd.read_csv(paths.INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
    wc.columns = [c.strip().lower() for c in wc.columns]
    we.columns = [c.strip().lower() for c in we.columns]
    common = set(wc.columns) & set(we.columns)
    we_only = we[[c for c in we.columns if c not in common]]
    wells = pd.concat([wc, we_only], axis=1, sort=False)

    long = wells.reset_index()
    long = long.rename(columns={long.columns[0]: "date"})
    long = long.melt(id_vars="date", var_name="well", value_name="h_depth")
    long = long.dropna(subset=["h_depth"])

    locs = pd.read_csv(paths.INT_LOCATIONS)
    locs["well"] = locs["Name"].str.strip().str.lower()
    # in_forest is LAND COVER, written by Script 01 from the committed
    # plantation outline. Until Script 01 has been rerun the column is
    # absent, so fall back to the C4/C5 cluster proxy with a warning — the
    # same first-pass convention the Sy and lambda loaders use. The proxy
    # disagrees with the footprint at six wells, so the fallback is a
    # degraded answer, not an equivalent one.
    if "in_forest" not in locs.columns:
        warn("01_locations.csv carries no in_forest column (Script 01 predates "
             "v1.12.0); falling back to the C4/C5 cluster proxy for canopy.")
        _cols = ["well", "E", "N"]
    else:
        _cols = ["well", "E", "N", "in_forest"]
    locs = locs[_cols].rename(columns={"E": "easting", "N": "northing"})

    master = pd.read_csv(paths.INT_MASTER_DATA)
    master["well"] = master["Name_Original"].str.strip().str.lower()
    master = master[["well", "Cluster"]].rename(columns={"Cluster": "cluster"})

    long = long.merge(locs, on="well", how="left")
    long = long.merge(master, on="well", how="left")
    long = long.merge(distances[["well", "dist_coast_m"]], on="well", how="left")

    # 03_master_data covers the REFERENCE network only, so every
    # extended-network well arrives here with cluster = NaN.  That matters
    # because the forest-free specification below filters on cluster, and
    # NaN.isin(FOREST_CIDS) is False — so before this fill, no extended
    # well was ever excluded and the "forest-free" panel silently retained
    # ceh3 and nw8 (best-match C5) and ceh15, lis1, nw12 (best-match C4).
    # ceh3 sits 176 m from the shore, inside the fitted reach.  Extended
    # assignments come from the sitewide Pearson audit, which is the same
    # source Script 18 uses for its extended wells (S.12).
    audit = pd.read_csv(paths.INT_PEAR_AUDIT_SITEWIDE)
    audit["well"] = audit["Well_Normalised"].str.strip().str.lower()
    ext_cluster = dict(zip(audit["well"], audit["Best_Match_Cluster"]))
    long["cluster"] = long["cluster"].fillna(long["well"].map(ext_cluster))

    # Exclusions
    long = long[~long["well"].isin(NON_DIPWELLS + FE_WELLS + SCRAPED_WELLS)]
    long = apply_scrape_treatment(long)
    if restrict_cluster is not None:
        long = long[long["cluster"] == restrict_cluster]
        if restrict_cluster == 3:
            long = long[~long["well"].isin(CLEARFELL_ZONE_IN_C3)]
    else:
        long = long[~long["well"].isin(CLEARFELL_ZONE)]
        if exclude_forested:
            long = long[~long["cluster"].isin(FOREST_CIDS)]
    long = long[long["easting"].notna() & long["dist_coast_m"].notna()].copy()
    if "in_forest" not in long.columns:
        long["in_forest"] = long["cluster"].isin(FOREST_CIDS)
    long["in_forest"] = long["in_forest"].fillna(False).astype(float)
    return long


def load_cwb() -> pd.Series:
    """Centred cumulative water balance (P − PET anomaly cumsum), mm."""
    cl = pd.read_csv(paths.INT_CLIMATE, index_col=0, parse_dates=True).sort_index()
    cl = cl[(cl.index.year >= 2004) & (cl.index.year <= 2026)]
    P_mm = pd.to_numeric(cl["P_m"], errors="coerce") * 1000
    PET_mm = pd.to_numeric(cl["PET"], errors="coerce") * 1000
    wb = (P_mm - PET_mm).dropna()
    cwb = (wb - wb.mean()).cumsum()
    cwb.name = "cwb"
    return cwb


def build_design(long: pd.DataFrame, cwb: pd.Series) -> pd.DataFrame:
    """Merge CWB and add t_years / month covariates."""
    df = long.merge(cwb.to_frame(), left_on="date", right_index=True, how="inner")
    df = df.dropna(subset=["h_depth", "cwb", "dist_coast_m"]).copy()
    df["t_years"] = (df["date"] - df["date"].min()).dt.days / 365.25
    df["month"] = df["date"].dt.month
    return df


# ── Panel fits ───────────────────────────────────────────────────────────────

def _within_demeaned_design(df: pd.DataFrame):
    """Construct the within-well-demeaned linear part of the design
    (CWB + month FE). Returns (h_dm, cwb_dm, M_dm, df_index).
    """
    grp = df.groupby("well")
    h_dm = (df["h_depth"] - grp["h_depth"].transform("mean")).values
    cwb_dm = (df["cwb"] - grp["cwb"].transform("mean")).values
    month_dums = pd.get_dummies(df["month"], prefix="m", drop_first=True)
    month_cols = []
    for c in month_dums.columns:
        dm = (month_dums[c].astype(float)
              - month_dums[c].astype(float).groupby(df["well"]).transform("mean"))
        month_cols.append(dm.values)
    M_dm = np.column_stack(month_cols)
    return h_dm, cwb_dm, M_dm


def fit_panel(df: pd.DataFrame, decay_func, p0, bounds,
              c_fixed: float | None = None, label: str = "",
              forest_term: bool = False) -> dict:
    """Fit a 3-parameter (or 2-parameter, if c_fixed) decay model to the
    panel by profile non-linear least squares.

    The well + month fixed effects and the CWB slope are absorbed by
    within-well demeaning (Frisch–Waugh–Lovell). The decay covariate
    δ(d_w) · t enters as a constrained term whose coefficient is fixed
    at 1; non-linear search runs over the parameters of δ(d_w).
    """
    h_dm, cwb_dm, M_dm = _within_demeaned_design(df)
    d_w = df["dist_coast_m"].values
    t = df["t_years"].values

    # Optional canopy x time regressor. Lets the FULL network be fitted with
    # forest cover controlled explicitly, rather than testing the confound by
    # dropping the forested clusters and comparing subsets. It keys on land
    # cover (in_forest), not on cluster membership.
    if forest_term:
        _ft = pd.Series(df["in_forest"].values * t, index=df.index)
        lin_extra = [(_ft - _ft.groupby(df["well"]).transform("mean")).values]
    else:
        lin_extra = []

    def residuals(theta):
        if c_fixed is None:
            delta_0, L, c = theta
        else:
            delta_0, L = theta
            c = c_fixed
        delta_d = decay_func(d_w, delta_0, L, c)
        decay_t = delta_d * t / 1000.0  # mm/yr → m, since h_depth is in m
        decay_t_ser = pd.Series(decay_t, index=df.index)
        decay_t_dm = (decay_t_ser
                      - decay_t_ser.groupby(df["well"]).transform("mean")).values
        y = h_dm - decay_t_dm
        X = np.column_stack([cwb_dm, M_dm] + lin_extra)
        try:
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        except np.linalg.LinAlgError:
            return np.full(len(y), 1e6)
        return y - X @ beta

    result = least_squares(residuals, p0, bounds=bounds,
                            method="trf", max_nfev=5000)

    # Absorbed CWB slope at the solution, in m per mm of CWB.  The FWL step
    # inside residuals() forms it and throws it away; the cluster attribution
    # needs it, because the trend the CWB covariate carries is precisely the
    # quantity the constant c trades off against.  Recomputed here rather than
    # captured from the closure, so the search itself is untouched.
    if c_fixed is None:
        _d0_s, _L_s, _c_s = result.x
    else:
        _d0_s, _L_s = result.x
        _c_s = c_fixed
    _decay_t_s = pd.Series(decay_func(d_w, _d0_s, _L_s, _c_s) * t / 1000.0,
                            index=df.index)
    _decay_t_s_dm = (_decay_t_s
                      - _decay_t_s.groupby(df["well"]).transform("mean")).values
    _beta_s, *_ = np.linalg.lstsq(np.column_stack([cwb_dm, M_dm] + lin_extra),
                                    h_dm - _decay_t_s_dm, rcond=None)

    n = len(result.fun); k = len(result.x)
    rss = float(np.sum(result.fun ** 2))
    sigma2 = rss / max(n - k, 1)
    J = result.jac
    try:
        cov = sigma2 * np.linalg.inv(J.T @ J)
        perr = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        perr = np.full(k, np.nan)
    t_crit = t_dist.ppf(0.975, df=max(n - k, 1))
    ci = np.column_stack([result.x - t_crit * perr,
                            result.x + t_crit * perr])
    return {
        "label": label,
        "popt": result.x,
        "perr": perr,
        "ci": ci,
        "rss": rss,
        "n": n,
        "k": k,
        "aic": n * np.log(rss / n) + 2 * k,
        "c_fixed": c_fixed,
        "forest_term": forest_term,
        "beta_cwb_m_per_mm": float(_beta_s[0]),
        "date_min": df["date"].min(),
        "date_max": df["date"].max(),
        "n_wells": int(df["well"].nunique()),
    }


def cwb_trend(cwb: pd.Series, start, end) -> float:
    """OLS trend in the centred cumulative water balance over a date span,
    in mm of CWB per year.

    Evaluated on every month of the CWB series between ``start`` and ``end``
    inclusive rather than only the months a particular panel happens to
    observe, so the number describes the covariate and not the sampling.  Over
    its own full span the CWB carries essentially no trend by construction — it
    is the cumulative sum of a CENTRED anomaly — but over a sub-span it can
    carry a substantial one, and it is that sub-span trend which the panel's
    fitted CWB coefficient converts into a drift rate.
    """
    seg = cwb.loc[start:end]
    t_yr = np.asarray((seg.index - seg.index[0]).days, dtype=float) / 365.25
    beta, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(seg)), t_yr]),
                                seg.values.astype(float), rcond=None)
    return float(beta[1])


# ── Season × δ(d)·t interaction test ─────────────────────────────────────────

def fit_season_interaction(df: pd.DataFrame, decay_func, p0, bounds,
                           c_fixed: float | None = None,
                           label: str = "") -> dict:
    """Full-panel single-model test of whether the coastal-retreat gradient is
    itself SEASONAL — the clean alternative to comparing two subset fits.

    Adds a spring modulation γ to the gradient drift term:

        δ(d)·t·(1 + γ·S) / 1000,     S = 1 if month ∈ Mar–May, else 0

    so γ is the fractional change in the distance-weighted drift RATE in spring
    relative to the rest of the year.  H0: γ = 0 (the gradient is
    season-independent — the headline all-season assumption).  Same FWL
    within-well demeaning and CWB + month-FE absorption as ``fit_panel``; the
    δ(d) parameters and γ are searched jointly by profile non-linear least
    squares, and γ's SE (hence t and p) come from the Jacobian covariance.  One
    model, the full panel — an actual p-value, not two overlapping CIs.
    """
    h_dm, cwb_dm, M_dm = _within_demeaned_design(df)
    d_w = df["dist_coast_m"].values
    t = df["t_years"].values
    spring = df["month"].isin(SPRING_MONTHS).astype(float).values

    def residuals(theta):
        if c_fixed is None:
            delta_0, L, c, gamma = theta
        else:
            delta_0, L, gamma = theta
            c = c_fixed
        delta_d = decay_func(d_w, delta_0, L, c)
        decay_t = delta_d * t * (1.0 + gamma * spring) / 1000.0
        decay_t_ser = pd.Series(decay_t, index=df.index)
        decay_t_dm = (decay_t_ser
                      - decay_t_ser.groupby(df["well"]).transform("mean")).values
        y = h_dm - decay_t_dm
        X = np.column_stack([cwb_dm, M_dm])
        try:
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        except np.linalg.LinAlgError:
            return np.full(len(y), 1e6)
        return y - X @ beta

    result = least_squares(residuals, p0, bounds=bounds,
                           method="trf", max_nfev=5000)
    n = len(result.fun); k = len(result.x)
    rss = float(np.sum(result.fun ** 2))
    sigma2 = rss / max(n - k, 1)
    J = result.jac
    try:
        cov = sigma2 * np.linalg.inv(J.T @ J)
        perr = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        perr = np.full(k, np.nan)
    gamma = float(result.x[-1])
    gamma_se = float(perr[-1])
    dfree = max(n - k, 1)
    tstat = gamma / gamma_se if gamma_se and np.isfinite(gamma_se) else np.nan
    pval = float(2 * t_dist.sf(abs(tstat), df=dfree)) if np.isfinite(tstat) else np.nan
    return {
        "label": label, "popt": result.x, "perr": perr,
        "gamma": gamma, "gamma_se": gamma_se, "gamma_t": tstat,
        "gamma_p": pval, "n": n, "k": k, "rss": rss, "c_fixed": c_fixed,
    }


# ── Per-well summer-min slopes ───────────────────────────────────────────────

def annual_metric_by_well(long: pd.DataFrame,
                          metric: str = "summer_min") -> tuple[pd.DataFrame, str]:
    """Annual per-well seasonal-metric values, and the name of the year column.

    Split out of ``compute_per_well_slopes`` at v1.6.0 so the same annual
    values can serve two purposes: the per-well OLS slopes written to 25_02,
    and the balanced annual cross-well mean the cluster attribution is now
    computed against.  Both therefore rest on one aggregation rather than two
    that could drift apart.

    ``metric="summer_min"``: annual minimum over the Script-14 summer window
    (Apr-Sep) indexed by HYDROLOGICAL year.  ``metric="spring_mean"``: annual
    Mar-May mean indexed by CALENDAR year, carrying ``n_months`` so the strict
    3-of-3 completeness guard can be applied.
    """
    df = long.copy()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    if metric == "summer_min":
        SUMMER = [4, 5, 6, 7, 8, 9]
        df["hydro_year"] = df["year"] + (df["month"] >= 10).astype(int)
        df = df[df["month"].isin(SUMMER)]
        agg = df.groupby(["well", "hydro_year"]).agg(
            value=("h_depth", "min"),
            easting=("easting", "first"),
            northing=("northing", "first"),
            cluster=("cluster", "first"),
            dist_coast_m=("dist_coast_m", "first"),
        ).reset_index()
        agg = agg[(agg["hydro_year"] >= 2004) & (agg["hydro_year"] <= 2025)]
        year_col = "hydro_year"
    elif metric == "spring_mean":
        df = df[df["month"].isin(SPRING_MONTHS)]
        agg = df.groupby(["well", "year"]).agg(
            value=("h_depth", "mean"),
            n_months=("month", "nunique"),
            easting=("easting", "first"),
            northing=("northing", "first"),
            cluster=("cluster", "first"),
            dist_coast_m=("dist_coast_m", "first"),
        ).reset_index()
        # Strict 3-of-3 rule: keep only well-years with all Mar-May months.
        agg = agg[agg["n_months"] >= SPRING_MIN_MONTHS]
        agg = agg[(agg["year"] >= 2004) & (agg["year"] <= 2025)]
        year_col = "year"
    else:
        raise ValueError(f"annual_metric_by_well: unknown metric {metric!r}")
    return agg, year_col


def compute_per_well_slopes(long: pd.DataFrame,
                            metric: str = "summer_min") -> pd.DataFrame:
    """Per-well annual seasonal-metric OLS slope.

    Both metrics use the same OLS, the same PANEL_OBS_MIN_YEARS guard, and the
    same output columns; they differ only in the annual aggregation, which
    ``annual_metric_by_well`` supplies.  Note that each well is fitted over its
    OWN record window, so a mean of these slopes mixes windows — which is why
    the cluster attribution uses the balanced annual mean instead.
    """
    agg, year_col = annual_metric_by_well(long, metric)

    out = []
    for well, g in agg.groupby("well"):
        if g[year_col].nunique() < PANEL_OBS_MIN_YEARS:
            continue
        x = g[year_col].astype(float).values
        y = g["value"].astype(float).values
        try:
            res = sm.OLS(y, sm.add_constant(x)).fit()
            out.append({
                "well": well,
                "easting": g["easting"].iloc[0],
                "northing": g["northing"].iloc[0],
                "cluster": (int(g["cluster"].iloc[0])
                             if pd.notna(g["cluster"].iloc[0]) else None),
                "dist_coast_m": g["dist_coast_m"].iloc[0],
                "slope_m_yr": float(res.params[1]),
                "slope_se": float(res.bse[1]),
                "slope_p": float(res.pvalues[1]),
                "r2": float(res.rsquared),
                "n_years": int(len(g)),
            })
        except Exception:
            continue
    return pd.DataFrame(out)


# ── Cluster partition ────────────────────────────────────────────────────────

# The observed column the decomposition is computed against.  It is written
# into every row as `decomposition_basis` so the basis travels with the table
# and a reader never has to infer which of the three observed columns the
# components were subtracted from.
DECOMPOSITION_BASIS_COLUMN = "observed_balanced_annual_mean_mm_yr"


def balanced_annual_mean_slope(annual: pd.DataFrame, year_col: str,
                               wells: set) -> float:
    """Slope of the annual cross-well MEAN of the per-well seasonal metric,
    mm/yr, for a given set of wells.

    This is the declared basis of the cluster decomposition (v1.6.0).  It uses
    the same well-set as the per-well slopes, but it is a single OLS on one
    annual series rather than an average of per-well fits taken over different
    record windows — so it cannot inherit the record-length composition effect
    that makes a mean of per-well slopes swing by more than 10 mm/yr depending
    on which wells happen to be long (see ``record_length_composition``).
    """
    a = annual[annual["well"].isin(wells)]
    ann = a.groupby(year_col)["value"].mean().sort_index()
    if len(ann) < 2:
        return np.nan
    res = sm.OLS(ann.values.astype(float),
                 sm.add_constant(ann.index.values.astype(float))).fit()
    return float(res.params[1]) * 1000.0


def cluster_partition(per_well: pd.DataFrame,
                      annual: pd.DataFrame,
                      year_col: str,
                      fit_headline: dict,
                      script14_slopes: pd.DataFrame,
                      cwb_trend_mm_yr: float) -> pd.DataFrame:
    """Decompose each cluster's observed decline under the headline
    (forest-free linear-capped) fit.

    Rebuilt at v1.6.0.  The previous table subtracted (gradient + c) from the
    Script-14 cluster-CENTROID slope and called the remainder a residual, which
    put three different bases in one subtraction: the panel δ(d) is
    CWB-adjusted and all-season, the 25_02 per-well slopes are raw annual
    seasonal-metric OLS, and the observed column was a centroid slope.  The
    decomposition is now computed against ``DECOMPOSITION_BASIS_COLUMN`` — the
    balanced annual cross-well mean over the per-well well-set — and the
    centroid and per-well-mean slopes are retained beside it as context, not as
    the basis.

    The far-field constant is reported for what it is.  ``c`` is NOT separately
    identified in this panel: the CWB covariate carries its own trend over the
    fitted span, and a constant drift and that trend contribution trade off, so
    only their SUM is recovered.  The table therefore carries the fitted
    constant as ``far_field_offset_mm_yr`` — its literal meaning, an offset —
    beside ``climate_cwb_mm_yr`` = 1000·β_cwb·d(CWB)/dt, the drift the climate
    covariate actually contributes.  Neither number should be read on its own.
    """
    d0, L, c = fit_headline["popt"]
    beta_cwb = fit_headline["beta_cwb_m_per_mm"]
    # β_cwb is m of water table per mm of CWB and d(CWB)/dt is mm of CWB per
    # year, so the product is m/yr; ×1000 puts it in the mm/yr of every other
    # column in this table.
    climate_cwb = 1000.0 * beta_cwb * cwb_trend_mm_yr

    s14 = {}
    for _, r in script14_slopes.iterrows():
        cnum = int(str(r["Cluster"]).replace("C", ""))
        s14[cnum] = float(r["Slope_m_per_yr"])

    rows = []
    for cn, lbl in CLUSTER_LABELS.items():
        sub = per_well[per_well["cluster"] == cn]
        if sub.empty:
            continue
        wells = set(sub["well"])
        mean_d = float(sub["dist_coast_m"].mean())
        per_well_mean = float(sub["slope_m_yr"].mean() * 1000)      # mm/yr
        observed_s14 = s14.get(cn, np.nan) * 1000                   # mm/yr
        basis = balanced_annual_mean_slope(annual, year_col, wells)  # mm/yr

        grad_only = float(model_linear_capped(mean_d, d0, L, 0))
        modelled_total = grad_only + climate_cwb + c
        unexplained = basis - modelled_total

        def pct(x):
            return 100.0 * x / basis if (basis and not np.isnan(basis)) else np.nan

        rows.append({
            "cluster_id": cn,
            "cluster_label": lbl,
            "n_wells": int(len(sub)),
            "mean_dist_coast_m": mean_d,
            "observed_centroid_mm_yr": observed_s14,
            "observed_per_well_mean_mm_yr": per_well_mean,
            DECOMPOSITION_BASIS_COLUMN: basis,
            "decomposition_basis": DECOMPOSITION_BASIS_COLUMN,
            "coastal_gradient_mm_yr": grad_only,
            "climate_cwb_mm_yr": climate_cwb,
            "far_field_offset_mm_yr": c,
            "modelled_total_mm_yr": modelled_total,
            "unexplained_mm_yr": unexplained,
            "coastal_gradient_pct_of_basis": pct(grad_only),
            "climate_cwb_pct_of_basis": pct(climate_cwb),
            "far_field_offset_pct_of_basis": pct(c),
            "unexplained_pct_of_basis": pct(unexplained),
        })
    return pd.DataFrame(rows)


# ── Record-length composition diagnostic ─────────────────────────────────────

def record_length_composition(per_well: pd.DataFrame,
                              annual: pd.DataFrame,
                              year_col: str) -> pd.DataFrame:
    """Why a far-field background of several mm/yr appears in a mean of
    per-well slopes when the panel constant is ~0.

    Each per-well slope is fitted over that well's own record, and the wells
    with the longest records decline much faster than the wells added later.
    A mean over per-well slopes therefore reports a composition of record
    lengths as if it were a rate, and the deficit it carries relative to the
    balanced annual mean is the size of that artefact.

    The long/short split is taken at the widest gap in the cluster's own sorted
    record lengths — a natural break in the data rather than a threshold — and
    the break is written into the table so the split is auditable.  Where a
    cluster's wells all share one record length there is no break and the short
    side is empty.
    """
    rows = []
    for cn, lbl in CLUSTER_LABELS.items():
        sub = per_well[per_well["cluster"] == cn]
        if sub.empty:
            continue
        slopes = sub["slope_m_yr"].values * 1000.0
        n_years = sub["n_years"].values.astype(float)
        uniq = np.unique(n_years)
        if uniq.size >= 2:
            gaps = np.diff(uniq)
            brk = float(uniq[int(np.argmax(gaps)) + 1])
        else:
            brk = float(uniq[0])
        long_m = n_years >= brk
        short_m = ~long_m
        if len(uniq) >= 3:
            fit = sm.OLS(slopes, sm.add_constant(n_years)).fit()
            slope_vs_len = float(fit.params[1])
            slope_vs_len_p = float(fit.pvalues[1])
        else:
            slope_vs_len = slope_vs_len_p = np.nan
        per_well_mean = float(slopes.mean())
        basis = balanced_annual_mean_slope(annual, year_col, set(sub["well"]))
        rows.append({
            "cluster_id": cn,
            "cluster_label": lbl,
            "n_wells": int(len(sub)),
            "n_years_min": float(n_years.min()),
            "n_years_median": float(np.median(n_years)),
            "n_years_max": float(n_years.max()),
            "record_length_break_years": brk,
            "n_wells_long": int(long_m.sum()),
            "n_years_long_min": (float(n_years[long_m].min())
                                 if long_m.any() else np.nan),
            "n_years_long_max": (float(n_years[long_m].max())
                                 if long_m.any() else np.nan),
            "mean_slope_long_mm_yr": (float(slopes[long_m].mean())
                                      if long_m.any() else np.nan),
            "n_wells_short": int(short_m.sum()),
            "n_years_short_min": (float(n_years[short_m].min())
                                  if short_m.any() else np.nan),
            "n_years_short_max": (float(n_years[short_m].max())
                                  if short_m.any() else np.nan),
            "mean_slope_short_mm_yr": (float(slopes[short_m].mean())
                                       if short_m.any() else np.nan),
            "slope_vs_record_length_mm_yr_per_year": slope_vs_len,
            "slope_vs_record_length_p": slope_vs_len_p,
            "observed_per_well_mean_mm_yr": per_well_mean,
            DECOMPOSITION_BASIS_COLUMN: basis,
            "composition_gap_mm_yr": per_well_mean - basis,
        })
    return pd.DataFrame(rows)


# ── Matched-window sensitivity (REPORTED ONLY) ───────────────────────────────

def matched_window_sensitivity(df_panel: pd.DataFrame, cwb: pd.Series,
                               decay_func, p0, bounds) -> pd.DataFrame:
    """Refit the headline specification on the long-record wells and on their
    complement, and report what that does to δ₀, L and c.

    REPORTED ONLY.  Nothing downstream reads this table: δ₀ and L in 25_01 and
    the gradient used in 25_03 remain the full-panel values.  The point of the
    table is that the fitted constant c moves by well over 10 mm/yr between the
    two subsets while β_cwb·d(CWB)/dt barely moves — the far-field constant is
    tracking which wells are in the panel, not a background climate rate — and
    that δ₀ and L move too, which is why a matched-window refit is a decision
    to be taken deliberately rather than a correction to be applied quietly.
    """
    cutoff = pd.Timestamp(MATCHED_WINDOW_RECORD_START)
    starts = df_panel.groupby("well")["date"].min()
    subsets = [
        ("full_panel", set(starts.index)),
        ("long_record", set(starts[starts <= cutoff].index)),
        ("short_record", set(starts[starts > cutoff].index)),
    ]
    rows = []
    for name, wells in subsets:
        sub = df_panel[df_panel["well"].isin(wells)].copy()
        if sub["well"].nunique() < 2:
            continue
        fit = fit_panel(sub, decay_func, p0=p0, bounds=bounds, label=name)
        d0, L, c = fit["popt"]
        trend = cwb_trend(cwb, fit["date_min"], fit["date_max"])
        cwb_term = 1000.0 * fit["beta_cwb_m_per_mm"] * trend
        rows.append({
            "subset": name,
            "record_start_cutoff": MATCHED_WINDOW_RECORD_START,
            "n_wells": fit["n_wells"],
            "n_obs": fit["n"],
            "span_start": fit["date_min"].strftime("%Y-%m"),
            "span_end": fit["date_max"].strftime("%Y-%m"),
            "delta_0_mm_yr": float(d0),
            "delta_0_se": float(fit["perr"][0]),
            "L_m": float(L),
            "L_se": float(fit["perr"][1]),
            "c_mm_yr": float(c),
            "c_se": float(fit["perr"][2]),
            "beta_cwb_m_per_mm": fit["beta_cwb_m_per_mm"],
            "cwb_trend_mm_per_yr": trend,
            "climate_cwb_mm_yr": cwb_term,
            "identified_sum_mm_yr": cwb_term + float(c),
            "status": "reported_only_not_adopted",
        })
    return pd.DataFrame(rows)


# ── BACI corroboration ──────────────────────────────────────────────────────


def window_sweep(specs: dict, cwb: pd.Series, decay_func, p0, bounds) -> pd.DataFrame:
    """Refit each specification over a moving window start, well set fixed.

    ``specs`` maps a label to the long-form panel for that specification. The
    window END is held at the panel's last month throughout; only the first
    month moves, one month at a time, until fewer than
    ``WINDOW_SWEEP_MIN_YEARS`` remain. Nothing about the well set changes, so
    a parameter that moves across the sweep is responding to the window and
    to nothing else — which is what separates this from
    ``matched_window_sensitivity``, where the well set is what varies.

    Each row also carries ``far_field_observed_mm_yr``: the balanced annual
    cross-well mean slope of the wells beyond WINDOW_SWEEP_FAR_FIELD_M over
    the same window, computed through ``balanced_annual_mean_slope`` so it
    rests on the same annual aggregation as the cluster decomposition.

    ``usable`` is False where any fitted parameter sits within
    WINDOW_SWEEP_BOUND_TOL of its search bound, or where the covariance is
    not finite. Such fits are written out rather than dropped silently.
    """
    lo, hi = np.asarray(bounds[0], dtype=float), np.asarray(bounds[1], dtype=float)
    span = hi - lo
    rows = []

    for label, long in specs.items():
        design = build_design(long, cwb)
        if design.empty:
            continue
        annual, year_col = annual_metric_by_well(long)
        far_wells = set(
            long.loc[long["dist_coast_m"] > WINDOW_SWEEP_FAR_FIELD_M, "well"].unique())
        end = design["date"].max()
        starts = pd.date_range(design["date"].min(), end, freq="MS")

        for start in starts:
            years = (end - start).days / 365.25
            if years < WINDOW_SWEEP_MIN_YEARS:
                continue
            sub = design[design["date"] >= start]
            if sub.empty or sub["well"].nunique() < 3:
                continue
            try:
                fit = fit_panel(sub, decay_func, p0=p0, bounds=bounds,
                                label=f"{label}@{start:%Y-%m}")
            except Exception:                        # a window that will not fit
                continue
            popt, perr = np.asarray(fit["popt"]), np.asarray(fit["perr"])
            at_bound = bool(np.any((np.abs(popt - lo) <= WINDOW_SWEEP_BOUND_TOL * span)
                                   | (np.abs(popt - hi) <= WINDOW_SWEEP_BOUND_TOL * span)))
            bad_cov = bool(not np.all(np.isfinite(perr)))
            obs = balanced_annual_mean_slope(
                annual[annual[year_col] >= start.year + 1], year_col, far_wells)
            rows.append({
                "spec": label,
                "window_start": f"{start:%Y-%m}",
                "window_end": f"{end:%Y-%m}",
                "window_years": years,
                "n_obs": int(fit["n"]),
                "n_wells": int(sub["well"].nunique()),
                "delta_0_mm_yr": float(popt[0]), "delta_0_se": float(perr[0]),
                "L_m": float(popt[1]),           "L_se": float(perr[1]),
                "c_mm_yr": float(popt[2]),       "c_se": float(perr[2]),
                "far_field_observed_mm_yr": obs,
                "n_far_field_wells": len(far_wells),
                "at_bound": at_bound,
                "usable": bool(not (at_bound or bad_cov)),
            })

    out = pd.DataFrame(rows)
    if not out.empty:
        n_bad = int((~out["usable"]).sum())
        info(f"window sweep: {len(out)} fits, {len(out) - n_bad} usable, "
             f"{n_bad} rejected at a parameter bound")
        for label, g in out.groupby("spec"):
            u = g[g["usable"]]
            if len(u):
                info(f"  {label}: c {u['c_mm_yr'].min():+.2f} to "
                     f"{u['c_mm_yr'].max():+.2f}  |  delta_0 "
                     f"{u['delta_0_mm_yr'].min():.2f} to "
                     f"{u['delta_0_mm_yr'].max():.2f} mm/yr")
    return out


def plot_window_sweep(sweep: pd.DataFrame, fig_path: Path) -> None:
    """Three stacked panels: δ₀, L and c against the window's first month.

    The well set is identical in every fit, so any movement is the window's
    doing. Panel (c) overlays the OBSERVED far-field trend, which is what c is
    implicitly estimating — the gap between the two lines is the fitted
    constant's bias, and their differing spread is its over-dispersion.
    At-bound fits are drawn as open markers rather than dropped.
    """
    if sweep.empty:
        warn("window sweep is empty; figure not drawn.")
        return

    sweep = sweep.copy()
    sweep["x"] = pd.to_datetime(sweep["window_start"] + "-01")
    specs = list(dict.fromkeys(sweep["spec"]))
    colours = ["#1f4e79", "#c1440e", "#3f7a3f"]
    panels = [
        ("delta_0_mm_yr", "delta_0_se", r"$\delta_0$  (mm yr$^{-1}$)",
         "(a) coast-edge anomaly"),
        ("L_m", "L_se", r"$L$  (m)", "(b) inland reach"),
        ("c_mm_yr", "c_se", r"$c$  (mm yr$^{-1}$)",
         "(c) far-field constant, against the observed far-field trend"),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(9.6, 9.8), sharex=True)
    for ax, (key, se_key, ylab, title) in zip(axes, panels):
        for colour, spec in zip(colours, specs):
            g = sweep[(sweep["spec"] == spec) & sweep["usable"]].sort_values("x")
            if g.empty:
                continue
            ax.fill_between(g["x"], g[key] - 1.96 * g[se_key],
                            g[key] + 1.96 * g[se_key],
                            color=colour, alpha=0.16, lw=0)
            ax.plot(g["x"], g[key], color=colour, lw=1.9, label=spec)
            bad = sweep[(sweep["spec"] == spec) & ~sweep["usable"]]
            if len(bad):
                ax.plot(bad["x"], bad[key], "o", ms=7, mfc="none",
                        mec="k", mew=1.3, zorder=5)
        if key == "c_mm_yr":
            ax.axhline(0, color="k", lw=0.9, alpha=0.45)
            obs = (sweep[sweep["usable"]]
                   .dropna(subset=["far_field_observed_mm_yr"])
                   .groupby("x")["far_field_observed_mm_yr"].mean().sort_index())
            if len(obs):
                ax.plot(obs.index, obs.values, color="#444", lw=2.0, ls="--",
                        label="observed far-field trend")
        ax.set_ylabel(ylab)
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
        ax.grid(alpha=0.25)
        ax.margins(x=0.03)

    axes[0].legend(loc="lower left", frameon=True, fontsize=9.5)
    axes[2].legend(loc="upper left", frameon=True, fontsize=9.5)
    axes[2].set_xlabel("first month included in the fit "
                       "(the window end and the well set are held fixed)")
    n_bad = int((~sweep["usable"]).sum())
    fig.suptitle("Window sensitivity of the cross-shore decay fit",
                 x=0.05, ha="left", fontsize=14, fontweight="bold", y=0.985)
    fig.text(0.05, 0.947,
             "same wells throughout; only the first month of the fit window moves",
             ha="left", fontsize=10, color="#666")
    fig.text(0.05, 0.012,
             f"Bands are 95% Wald intervals. Open markers: {n_bad} fit(s) rejected "
             f"for sitting on a parameter bound. Windows shorter than "
             f"{WINDOW_SWEEP_MIN_YEARS:.0f} years are not fitted.",
             ha="left", fontsize=8.6, color="#444")
    fig.tight_layout(rect=[0, 0.04, 1, 0.935])
    render_figure(fig, fig_path)
    plt.close(fig)

def baci_corroboration(distances: pd.DataFrame,
                        fit_headline: dict,
                        baci_csv_path: Path) -> pd.DataFrame:
    """Compare the BACI easting × time coefficient absorption to the
    gradient model's predicted differential between each impact zone
    and each control tier.

    The BACI fits `delta_easting × months_since` as a covariate; its
    coefficient (m per m-easting per month) implies an absorbed
    differential deepening rate of  coef × ΔE × 12 × 1000 mm/yr.

    The gradient model predicts a differential of
        δ(d_impact) − δ(d_control)
    where δ is the headline linear-capped form.

    If the two agree, the BACI's easting × time correction is
    accounting for coastal-retreat drift consistently with the
    independently-fitted gradient. If the BACI absorbs much more,
    its easting × time term is doing more than just coastal-retreat
    correction (likely absorbing other monotonic spatial drift).
    """
    d0_h, L_h, c_h = fit_headline["popt"]
    dists = distances.set_index("well")["dist_coast_m"].to_dict()

    def mean_d(wells):
        return float(np.mean([dists[w] for w in wells if w in dists]))

    def grad_only(d):
        return float(model_linear_capped(d, d0_h, L_h, 0))

    d_imp = mean_d(IMPACT_WELLS)
    d_edge = mean_d(EDGE_WELLS)
    d_forest = mean_d(FOREST_CONTROL_WELLS)
    d_climate = mean_d(CLIMATE_CONTROL_WELLS)

    # Easting too (BACI uses easting, not distance to coast)
    locs = pd.read_csv(paths.INT_LOCATIONS)
    locs["well"] = locs["Name"].str.strip().str.lower()
    E = dict(zip(locs["well"], locs["E"]))

    def mean_E(wells):
        return float(np.mean([E[w] for w in wells if w in E]))

    E_imp = mean_E(IMPACT_WELLS)
    E_edge = mean_E(EDGE_WELLS)
    E_forest = mean_E(FOREST_CONTROL_WELLS)
    E_climate = mean_E(CLIMATE_CONTROL_WELLS)

    # BACI coefficients
    baci = pd.read_csv(baci_csv_path)
    baci = baci[baci["Coefficient"] == "easting_x_time"].copy()

    rows = []
    pairs = [
        ("Forest", "Impact", d_imp, E_imp, d_forest, E_forest),
        ("Forest", "Edge",   d_edge, E_edge, d_forest, E_forest),
        ("Climate", "Impact", d_imp, E_imp, d_climate, E_climate),
        ("Climate", "Edge",   d_edge, E_edge, d_climate, E_climate),
    ]
    for ctl_name, zone_name, d_tgt, E_tgt, d_ctl, E_ctl in pairs:
        # Gradient-model differential (target − control), gradient only
        grad_tgt = grad_only(d_tgt)
        grad_ctl = grad_only(d_ctl)
        model_pred = grad_tgt - grad_ctl  # mm/yr
        # BACI coefficient
        match = baci[(baci["Control"] == ctl_name) & (baci["Zone"] == zone_name)]
        if match.empty:
            continue
        coef = float(match["Value"].iloc[0])  # m / (m_easting × month)
        coef_se = float(match["SE"].iloc[0])
        coef_p = float(match["p"].iloc[0])
        dE = E_tgt - E_ctl
        # Absorbed differential = coef × ΔE × 12 (months/yr) × 1000 (m → mm)
        baci_absorb = coef * dE * 12 * 1000
        baci_absorb_se = coef_se * abs(dE) * 12 * 1000
        # z-test against model prediction (treating model pred as known)
        z = ((baci_absorb - model_pred) / baci_absorb_se
              if baci_absorb_se > 0 else np.nan)
        rows.append({
            "control_tier": ctl_name,
            "impact_zone": zone_name,
            "d_target_m": round(d_tgt, 0),
            "d_control_m": round(d_ctl, 0),
            "delta_E_m": round(dE, 0),
            "baci_coef": coef,
            "baci_coef_se": coef_se,
            "baci_coef_p": coef_p,
            "baci_absorbs_mm_yr": round(baci_absorb, 1),
            "baci_absorbs_se_mm_yr": round(baci_absorb_se, 1),
            "model_predicts_mm_yr": round(model_pred, 1),
            "z_test_baci_vs_model": (round(z, 2)
                                      if not np.isnan(z) else None),
            "consistent": ("yes" if (not np.isnan(z)) and abs(z) < 2
                            else "no"),
        })
    return pd.DataFrame(rows)


# ── Figures ──────────────────────────────────────────────────────────────────

def plot_fit_diagnostic(per_well: pd.DataFrame,
                          fit_full_l: dict, fit_ff_l: dict, fit_c3_l: dict,
                          cluster_partition_df: pd.DataFrame,
                          fig_path: Path,
                          fit_ff_e: dict | None = None,
                          figlabels: dict | None = None) -> None:
    """Two-panel diagnostic:
        (a) per-well summer-min slope vs distance, with the three lin-cap
            fits (full network, forest-free, C3 only) overlaid; if the
            forest-free exponential fit (fit_ff_e) is supplied it is also
            overlaid (dashed) to show the two functional forms are near-
            indistinguishable over the observed distance range
        (b) per-cluster stacked decomposition: the balanced annual-mean
            observed decline against coastal gradient + climate (CWB) +
            far-field offset + unexplained
    """
    if figlabels is None:
        figlabels = _SUMMER_FIG
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.0))
    ax1, ax2 = axes

    # ── Panel (a) — per-well scatter and fitted curves ──
    for cn, lbl in CLUSTER_LABELS.items():
        sub = per_well[per_well["cluster"] == cn]
        if sub.empty:
            continue
        ax1.errorbar(sub["dist_coast_m"], sub["slope_m_yr"] * 1000,
                      yerr=sub["slope_se"] * 1000,
                      fmt="o", color=CLUSTER_COLOURS[cn], markersize=6,
                      capsize=2, elinewidth=0.5,
                      markeredgecolor="black", markeredgewidth=0.3,
                      label=lbl, alpha=0.9, zorder=3)
    unc = per_well[per_well["cluster"].isna()]
    if not unc.empty:
        ax1.errorbar(unc["dist_coast_m"], unc["slope_m_yr"] * 1000,
                      yerr=unc["slope_se"] * 1000,
                      fmt="o", color="lightgrey", markersize=4,
                      capsize=2, elinewidth=0.4, alpha=0.6,
                      markeredgecolor="grey", markeredgewidth=0.3,
                      label="Unclustered", zorder=2)

    d_grid = np.linspace(0, 2400, 300)

    # Full network
    y_full = model_linear_capped(d_grid, *fit_full_l["popt"])
    d0, L, c = fit_full_l["popt"]
    ax1.plot(d_grid, y_full, "-", color="#222222", linewidth=2.0,
              label=f"Full network: δ₀={d0:+.1f}, L={L:.0f}, c={c:+.1f}",
              zorder=6)
    # Forest-free
    y_ff = model_linear_capped(d_grid, *fit_ff_l["popt"])
    d0, L, c = fit_ff_l["popt"]
    ax1.plot(d_grid, y_ff, "-", color="#2ca02c", linewidth=2.4,
              label=f"Forest-free: δ₀={d0:+.1f}, L={L:.0f}, c={c:+.1f}",
              zorder=7)
    # C3 only (c fixed)
    y_c3 = model_linear_capped(d_grid, fit_c3_l["popt"][0],
                                  fit_c3_l["popt"][1], fit_c3_l["c_fixed"])
    d0, L = fit_c3_l["popt"]
    ax1.plot(d_grid, y_c3, "--", color="#d62728", linewidth=1.8,
              label=f"C3 only (c fixed): δ₀={d0:+.1f}, L={L:.0f}",
              zorder=5)

    # Forest-free exponential (alternative functional form) — overlaid to
    # show the two forms are near-indistinguishable over the data range.
    if fit_ff_e is not None:
        y_ff_e = model_exp(d_grid, *fit_ff_e["popt"])
        d0, L, c = fit_ff_e["popt"]
        ax1.plot(d_grid, y_ff_e, ":", color="#7f4fbf", linewidth=2.0,
                  label=f"Forest-free (exp): δ₀={d0:+.1f}, L={L:.0f}, c={c:+.1f}",
                  zorder=6)
        delta_aic = fit_ff_e["aic"] - fit_ff_l["aic"]
        ax1.text(0.015, 0.97,
                  f"forest-free ΔAIC (exp − lin-cap) = {delta_aic:+.1f}",
                  transform=ax1.transAxes, ha="left", va="top",
                  fontsize=8,
                  bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                            edgecolor="grey", alpha=0.85), zorder=8)

    ax1.axhline(0, color="black", linewidth=0.4, alpha=0.6)
    ax1.set_xlabel("Perpendicular distance to Caernarfon Bay MHW (m)")
    ax1.set_ylabel(figlabels["slope_ylabel"])
    ax1.set_title(figlabels["diag_a_title"],
                   fontsize=11, loc="left")
    ax1.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax1.grid(alpha=0.3)

    # ── Panel (b) — cluster decomposition ──
    p = cluster_partition_df.sort_values("mean_dist_coast_m").reset_index(drop=True)
    x = np.arange(len(p))
    obs = p[DECOMPOSITION_BASIS_COLUMN].values
    grad = p["coastal_gradient_mm_yr"].values
    cli = p["climate_cwb_mm_yr"].values
    off = p["far_field_offset_mm_yr"].values
    unx = p["unexplained_mm_yr"].values

    width = 0.38
    ax2.bar(x - width / 2, obs, width,
             color="#333333", alpha=0.9,
             label="Observed (balanced annual mean)",
             edgecolor="black", linewidth=0.5)
    ax2.bar(x + width / 2, cli, width,
             color="#4488cc", alpha=0.85, label="Climate (CWB trend)",
             edgecolor="black", linewidth=0.5)
    ax2.bar(x + width / 2, grad, width, bottom=cli,
             color="#cc5500", alpha=0.85, label="Coastal-retreat gradient",
             edgecolor="black", linewidth=0.5)
    ax2.bar(x + width / 2, off, width, bottom=cli + grad,
             color="#7f4fbf", alpha=0.85, label="Far-field offset (c)",
             edgecolor="black", linewidth=0.5)
    ax2.bar(x + width / 2, unx, width, bottom=cli + grad + off,
             color="#bbbbbb", alpha=0.85, label="Unexplained",
             edgecolor="black", linewidth=0.5)

    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.set_xticks(x)
    short_labels = p["cluster_label"].str.extract(r"^(C\d+)")[0]
    ax2.set_xticklabels(short_labels, fontsize=10)
    ax2.set_xlabel("Cluster (coastal → inland)")
    ax2.set_ylabel(figlabels["slope_ylabel"])
    ax2.set_title("(b) Per-cluster decomposition under forest-free lin-cap fit",
                   fontsize=11, loc="left")
    ax2.legend(loc="lower right", fontsize=8.5, framealpha=0.9)
    ax2.grid(alpha=0.3, axis="y")

    fig.tight_layout()
    render_figure(fig, fig_path, pil_kwargs={"quality": 85})
    plt.close(fig)


def plot_baci_corroboration(baci_df: pd.DataFrame, fig_path: Path) -> None:
    """Forest plot of BACI easting × time absorption vs gradient-model
    prediction, per impact-zone × control-tier comparison.
    """
    fig, ax = plt.subplots(figsize=(10, 4.5))
    labels = [f"{r.control_tier} {r.impact_zone}"
              for r in baci_df.itertuples()]
    y_pos = np.arange(len(baci_df))[::-1]
    for i, r in enumerate(baci_df.itertuples()):
        # BACI absorbed (with SE)
        ax.errorbar(r.baci_absorbs_mm_yr, y_pos[i],
                     xerr=r.baci_absorbs_se_mm_yr,
                     fmt="o", color="#1f77b4", markersize=8, capsize=4,
                     linewidth=1.5,
                     label="BACI easting × time absorbs"
                     if i == 0 else None)
        # Model predicts (point, no error bar)
        ax.scatter(r.model_predicts_mm_yr, y_pos[i],
                    marker="D", color="#cc5500", s=80, zorder=5,
                    edgecolor="black", linewidth=0.5,
                    label="Gradient model predicts" if i == 0 else None)
        # Verdict
        ax.text(0.99, y_pos[i],
                 f"  z = {r.z_test_baci_vs_model:+.2f}  ({r.consistent})",
                 transform=ax.get_yaxis_transform(),
                 va="center", fontsize=9, family="monospace")

    ax.axvline(0, color="grey", linewidth=0.5, alpha=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Differential deepening rate at target zone "
                   "vs control tier (mm yr⁻¹)")
    ax.set_title("BACI easting × time absorption vs coastal-retreat gradient prediction",
                  fontsize=11, loc="left")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.3, axis="x")

    fig.tight_layout()
    render_figure(fig, fig_path, pil_kwargs={"quality": 85})
    plt.close(fig)


def plot_cluster_decomposition(partition: pd.DataFrame, fig_path: Path,
                               figlabels: dict | None = None) -> None:
    """Stacked-bar figure decomposing each cluster's balanced annual-mean
    seasonal-metric decline into climate (CWB trend) + coastal-retreat gradient
    + far-field offset + unexplained remainder.  The offset and the CWB term
    are drawn as separate bars because they are not separately identified: only
    their sum is recovered by the panel fit, and showing one alone would invite
    exactly the reading the rebuild removed.
    Folded in from the standalone ``30_cluster_slope_decomposition.py``
    (2026-05-29) so the decomposition lives alongside the partition it
    visualises. Reads the same cluster-partition columns this script writes —
    no new data, only a new view of it.
    """
    if figlabels is None:
        figlabels = _SUMMER_FIG
    df = partition.sort_values("cluster_id").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10.5, 5.5))

    clusters = df["cluster_label"].tolist()
    y        = np.arange(len(clusters))
    clim     = df["climate_cwb_mm_yr"].values
    coast    = df["coastal_gradient_mm_yr"].values
    offset   = df["far_field_offset_mm_yr"].values
    unexpl   = df["unexplained_mm_yr"].values
    obs      = df[DECOMPOSITION_BASIS_COLUMN].values

    COLOURS = {
        "climate":  "#5b8bce",
        "coastal":  "#d62728",
        "offset":   "#7f4fbf",
        "unexpl":   "#888888",
    }
    bar_h = 0.55
    running = np.zeros(len(clusters))
    c_label = (f"Climate (CWB trend, {clim[0]:+.1f} mm/yr)"
               if len(clim) else "Climate (CWB trend)")
    o_label = (f"Far-field offset c ({offset[0]:+.1f} mm/yr; "
               f"not separately identified from the CWB trend)"
               if len(offset) else "Far-field offset c")
    ax.barh(y, clim,  height=bar_h, color=COLOURS["climate"],
            label=c_label, edgecolor="white", linewidth=0.6)
    running += clim
    ax.barh(y, coast, height=bar_h, color=COLOURS["coastal"],
            label="Coastal-retreat gradient", left=running,
            edgecolor="white", linewidth=0.6)
    running += coast
    ax.barh(y, offset, height=bar_h, color=COLOURS["offset"],
            label=o_label, left=running, edgecolor="white", linewidth=0.6)
    running += offset
    ax.barh(y, unexpl, height=bar_h, color=COLOURS["unexpl"],
            label="Unexplained", left=running,
            edgecolor="white", linewidth=0.6)

    ax.scatter(obs, y, marker="D", color="black", s=85, zorder=5,
                label="Observed balanced annual mean")

    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(clusters, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel(figlabels["decomp_xlabel"], fontsize=10.5)
    ax.set_title(figlabels["decomp_title"],
                  fontsize=11)
    ax.grid(axis="x", alpha=0.3, linewidth=0.4)
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95)

    # Right-side per-cluster annotation: mean dist_coast and n
    for i, r in df.iterrows():
        ax.text(1.02, i,
                 f"  ⌀d = {r['mean_dist_coast_m']:.0f} m   (n = {r['n_wells']})",
                 transform=ax.get_yaxis_transform(),
                 va="center", fontsize=8.5, color="#333")

    fig.tight_layout()
    render_figure(fig, fig_path)
    plt.close(fig)


# ── Spring-vs-summer comparison ────────────────────────────────────────────────

def build_spring_vs_summer_comparison(summer_partition: pd.DataFrame,
                                      spring_partition: pd.DataFrame) -> pd.DataFrame:
    """Merge the summer and spring cluster partitions into a side-by-side
    comparison table.  Both partitions apply the SAME all-season gradient fit;
    they differ in the observed centroid slope (Script 14 summer vs spring) and
    in each cluster's per-well set (different wells clear the ≥8-year guard in
    each season), so the mean distance and predicted gradient can differ
    slightly between seasons.  The climate (CWB) term and the far-field offset
    are the same all-season values in both.
    """
    keep = ["cluster_id", "cluster_label", "n_wells", "mean_dist_coast_m",
            "observed_centroid_mm_yr", DECOMPOSITION_BASIS_COLUMN,
            "coastal_gradient_mm_yr", "climate_cwb_mm_yr",
            "far_field_offset_mm_yr", "unexplained_mm_yr",
            "coastal_gradient_pct_of_basis"]
    s = summer_partition[keep].copy()
    p = spring_partition[keep].copy()
    merged = s.merge(p, on=["cluster_id", "cluster_label"],
                     suffixes=("_summer", "_spring"), how="outer")
    merged = merged.sort_values("cluster_id").reset_index(drop=True)
    return merged


def plot_spring_vs_summer(comparison: pd.DataFrame, fig_path: Path) -> None:
    """Grouped-bar comparison of the observed centroid slope, summer minimum vs
    spring mean, by cluster, with each season's predicted coastal-retreat
    gradient marked."""
    df = comparison.sort_values("mean_dist_coast_m_summer").reset_index(drop=True)
    x = np.arange(len(df))
    width = 0.38

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(x - width / 2, df["observed_centroid_mm_yr_summer"], width,
           color="#cc5500", alpha=0.9, edgecolor="black", linewidth=0.5,
           label="Observed summer minimum (Script 14)")
    ax.bar(x + width / 2, df["observed_centroid_mm_yr_spring"], width,
           color="#4488cc", alpha=0.9, edgecolor="black", linewidth=0.5,
           label="Observed spring mean (Script 14)")
    # Predicted all-season gradient markers (same fit, per-season mean dist).
    ax.scatter(x - width / 2, df["coastal_gradient_mm_yr_summer"],
               marker="D", color="black", s=42, zorder=5,
               label="Predicted coastal gradient (all-season fit)")
    ax.scatter(x + width / 2, df["coastal_gradient_mm_yr_spring"],
               marker="D", color="black", s=42, zorder=5)

    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x)
    short = df["cluster_label"].str.extract(r"^(C\d+)")[0]
    ax.set_xticklabels(short, fontsize=10)
    ax.set_xlabel("Cluster (coastal → inland)")
    ax.set_ylabel("Observed centroid slope (mm yr⁻¹)")
    ax.set_title("Observed centroid slope by cluster: summer minimum vs spring mean\n"
                 "same all-season coastal-retreat gradient applied to both metrics",
                 fontsize=11, loc="left")
    # Legend inside, lower-right — sits under the rightmost (C1, most inland)
    # column, where the bars are small.
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.9)
    ax.grid(alpha=0.3, axis="y")

    fig.tight_layout()
    render_figure(fig, fig_path)
    plt.close(fig)


# ── Output assembly ──────────────────────────────────────────────────────────

def build_fit_parameters_table(fits: dict) -> pd.DataFrame:
    """Assemble all six fits into a tidy parameter table."""
    rows = []
    for key, fit in fits.items():
        source, model = key
        d0, L = fit["popt"][0], fit["popt"][1]
        d0_se, L_se = fit["perr"][0], fit["perr"][1]
        ci = fit["ci"]
        if fit["c_fixed"] is None:
            c_val = float(fit["popt"][2])
            c_se = float(fit["perr"][2])
        else:
            c_val = float(fit["c_fixed"])
            c_se = np.nan
        rows.append({
            "source": source,
            "model": model,
            "n_obs": fit["n"],
            "AIC": round(fit["aic"], 1),
            "delta_0_mm_yr": round(float(d0), 2),
            "delta_0_se": round(float(d0_se), 2),
            "delta_0_ci_lo": round(float(ci[0, 0]), 2),
            "delta_0_ci_hi": round(float(ci[0, 1]), 2),
            "L_m": round(float(L), 0),
            "L_se": round(float(L_se), 0),
            "L_ci_lo": round(float(ci[1, 0]), 0),
            "L_ci_hi": round(float(ci[1, 1]), 0),
            "c_mm_yr": round(c_val, 2),
            "c_se": (round(c_se, 2) if not np.isnan(c_se) else None),
        })
    return pd.DataFrame(rows)


def _check2_correlation_rows(per_well: pd.DataFrame) -> list[dict]:
    """§5.7.5 Check 2 (raw): correlate the raw 2017→2023 MSL5 change (Script 20)
    with the per-well summer-minimum slope computed in this script.

    Returns rows in the project-standard report-numbers format (Pearson r/p,
    Spearman r/p), or an empty list if Script 20's change CSV is not yet on disk
    (Script 20 runs earlier in the pipeline, so on a full run it is present).
    """
    chg_path = paths.OUT_20_MSL5_CHANGE_PERWELL
    if not Path(chg_path).exists():
        note(f"Check 2 skipped: {chg_path.name} not found "
             f"(run Script 20 first); no correlation rows emitted")
        return []
    chg = pd.read_csv(chg_path)
    chg["well"] = chg["well"].astype(str).str.lower().str.strip()
    slp = per_well.copy()
    slp["well"] = slp["well"].astype(str).str.lower().str.strip()
    slp["slope_mm_yr"] = slp["slope_m_yr"] * 1000.0
    m = (chg[["well", "raw_change_mm"]]
         .merge(slp[["well", "slope_mm_yr"]], on="well", how="inner")
         .dropna(subset=["raw_change_mm", "slope_mm_yr"]))
    n = len(m)
    if n < 3:
        note(f"Check 2 skipped: only {n} wells common to MSL5 change and "
             f"summer-min slope; no correlation rows emitted")
        return []
    pr, pp = pearsonr(m["raw_change_mm"], m["slope_mm_yr"])
    sr, sp = spearmanr(m["raw_change_mm"], m["slope_mm_yr"])
    note(f"Check 2 (raw): Pearson r={pr:+.3f} (p={pp:.4f}), "
         f"Spearman r={sr:+.3f} (p={sp:.4f}), n={n}")
    base_note = (f"§5.7.5 Check 2: raw 2017→2023 MSL5 change "
                 f"(20_msl5_change_perwell.csv) vs summer-min slope; n={n} wells")
    return [
        {"Parameter": "Check2_msl5raw_vs_summermin_pearson_r",
         "Well": "", "Era": "2017-2023 vs full record",
         "Value": round(float(pr), 3), "Unit": "r", "Note": base_note},
        {"Parameter": "Check2_msl5raw_vs_summermin_pearson_p",
         "Well": "", "Era": "2017-2023 vs full record",
         "Value": round(float(pp), 4), "Unit": "p", "Note": base_note},
        {"Parameter": "Check2_msl5raw_vs_summermin_spearman_r",
         "Well": "", "Era": "2017-2023 vs full record",
         "Value": round(float(sr), 3), "Unit": "r", "Note": base_note},
        {"Parameter": "Check2_msl5raw_vs_summermin_spearman_p",
         "Well": "", "Era": "2017-2023 vs full record",
         "Value": round(float(sp), 4), "Unit": "p", "Note": base_note},
    ]


def build_report_numbers(fits: dict,
                          partition: pd.DataFrame,
                          baci_corr: pd.DataFrame,
                          per_well: pd.DataFrame) -> pd.DataFrame:
    """Headline numbers in the project-standard
    `Parameter, Well, Era, Value, Unit, Note` format.
    """
    rows = []
    # Headline fit (forest-free linear-capped)
    ff = fits[("forest_free", "linear_capped")]
    rows.append({"Parameter": "Headline_fit_delta_0",
                  "Well": "", "Era": "2005-2026",
                  "Value": round(float(ff["popt"][0]), 2),
                  "Unit": "mm/yr",
                  "Note": (f"Forest-free linear-capped, "
                            f"SE={ff['perr'][0]:.2f}, "
                            f"95% CI [{ff['ci'][0, 0]:.1f}, "
                            f"{ff['ci'][0, 1]:.1f}]")})
    rows.append({"Parameter": "Headline_fit_L",
                  "Well": "", "Era": "2005-2026",
                  "Value": round(float(ff["popt"][1]), 0),
                  "Unit": "m",
                  "Note": (f"Forest-free linear-capped, "
                            f"SE={ff['perr'][1]:.0f}")})
    rows.append({"Parameter": "Headline_fit_c",
                  "Well": "", "Era": "2005-2026",
                  "Value": round(float(ff["popt"][2]), 2),
                  "Unit": "mm/yr",
                  "Note": (f"Forest-free linear-capped climate background, "
                            f"SE={ff['perr'][2]:.2f}")})
    # AIC comparison
    fe = fits[("forest_free", "exponential")]
    rows.append({"Parameter": "Headline_DeltaAIC_lincap_vs_exp",
                  "Well": "", "Era": "2005-2026",
                  "Value": round(fe["aic"] - ff["aic"], 1),
                  "Unit": "",
                  "Note": "exp − lin-cap; positive favours lin-cap"})
    # C5 attribution
    c5 = partition[partition["cluster_id"] == 5]
    if not c5.empty:
        r = c5.iloc[0]
        rows.append({"Parameter": "C5_gradient_pct_of_basis",
                      "Well": "", "Era": "2005-2026",
                      "Value": float(r["coastal_gradient_pct_of_basis"]),
                      "Unit": "%",
                      "Note": (f"basis = {r['decomposition_basis']} "
                                f"{r[DECOMPOSITION_BASIS_COLUMN]:+.1f} mm/yr; "
                                f"coastal gradient "
                                f"{r['coastal_gradient_mm_yr']:+.1f}, "
                                f"climate (CWB) {r['climate_cwb_mm_yr']:+.1f}, "
                                f"far-field offset "
                                f"{r['far_field_offset_mm_yr']:+.1f} "
                                f"(offset and CWB trend not separately "
                                f"identified), unexplained "
                                f"{r['unexplained_mm_yr']:+.1f}")})
    # BACI corroboration headline (Forest Impact)
    fi = baci_corr[(baci_corr["control_tier"] == "Forest")
                   & (baci_corr["impact_zone"] == "Impact")]
    if not fi.empty:
        r = fi.iloc[0]
        rows.append({"Parameter": "BACI_corroboration_Forest_Impact_z",
                      "Well": "", "Era": "BACI window",
                      "Value": float(r["z_test_baci_vs_model"]),
                      "Unit": "z",
                      "Note": (f"BACI absorbs {r['baci_absorbs_mm_yr']:+.1f} "
                                f"mm/yr, model predicts "
                                f"{r['model_predicts_mm_yr']:+.1f} mm/yr; "
                                f"consistent={r['consistent']}")})
    # §5.7.5 Check 2 (raw): MSL5 raw change vs summer-min slope correlation
    rows.extend(_check2_correlation_rows(per_well))
    return pd.DataFrame(rows)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    banner("25", "Coastal Gradient Analysis", version=__version__)
    paths.make_all_dirs()
    paths.DIR_25.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 72)
    print(" Script 25 — Coastal-retreat gradient analysis")
    print("=" * 72)

    # ── Load distance CSV ──
    if not paths.DATA_DIST_COAST.exists():
        raise FileNotFoundError(
            f"Distance-to-coast CSV not found: {paths.DATA_DIST_COAST}\n"
            "See data/COASTLINE_PROVENANCE.md for how to regenerate from "
            "OS Open Map Local TidalBoundary.")
    distances = pd.read_csv(paths.DATA_DIST_COAST).rename(columns={"Name": "well"})
    distances["well"] = distances["well"].str.strip().str.lower()
    print(f"\n  Distance source: {paths.DATA_DIST_COAST.name}  "
          f"({len(distances)} wells, "
          f"d range {distances['dist_coast_m'].min():.0f}–"
          f"{distances['dist_coast_m'].max():.0f} m)")

    cwb = load_cwb()

    # ── Fits ──
    print("\n  Fitting [1/3] Full network ...")
    long_full = load_panel(distances, exclude_forested=False)
    df_full = build_design(long_full, cwb)
    fit_full_l = fit_panel(df_full, model_linear_capped,
                            p0=[-30.0, 1000.0, -5.0],
                            bounds=([-200, 100, -30], [50, 10000, 30]),
                            label="full_lincap")
    fit_full_e = fit_panel(df_full, model_exp,
                            p0=[-40.0, 600.0, -5.0],
                            bounds=([-200, 50, -30], [50, 5000, 30]),
                            label="full_exp")

    print("  Fitting [2/3] Forest-free network ...")
    long_ff = load_panel(distances, exclude_forested=True)
    df_ff = build_design(long_ff, cwb)
    fit_ff_l = fit_panel(df_ff, model_linear_capped,
                          p0=[-30.0, 1000.0, -5.0],
                          bounds=([-200, 100, -30], [50, 10000, 30]),
                          label="ff_lincap")
    fit_ff_e = fit_panel(df_ff, model_exp,
                          p0=[-40.0, 600.0, -5.0],
                          bounds=([-200, 50, -30], [50, 5000, 30]),
                          label="ff_exp")

    print("  Fitting [3/3] C3 only (c fixed to forest-free network) ...")
    long_c3 = load_panel(distances, restrict_cluster=3)
    df_c3 = build_design(long_c3, cwb)
    c_fix_l = float(fit_ff_l["popt"][2])
    c_fix_e = float(fit_ff_e["popt"][2])
    fit_c3_l = fit_panel(df_c3, model_linear_capped,
                          p0=[-30.0, 1000.0],
                          bounds=([-200, 100], [50, 10000]),
                          c_fixed=c_fix_l, label="c3_lincap_cfix")
    fit_c3_e = fit_panel(df_c3, model_exp,
                          p0=[-40.0, 600.0],
                          bounds=([-200, 50], [50, 5000]),
                          c_fixed=c_fix_e, label="c3_exp_cfix")

    # ── Print summary to console ──
    print("\n  Fitted parameters (linear-capped form):")
    print(f"    {'Source':<14} {'δ₀ (mm/yr)':>14} {'L (m)':>10} {'c (mm/yr)':>14}")
    for name, fit in [("Full",         fit_full_l),
                       ("Forest-free",  fit_ff_l),
                       ("C3 only",      fit_c3_l)]:
        d0 = fit["popt"][0]; L = fit["popt"][1]
        c = (fit["c_fixed"] if fit["c_fixed"] is not None
              else fit["popt"][2])
        print(f"    {name:<14} {d0:>+7.2f} ± {fit['perr'][0]:.2f}"
              f"   {L:>4.0f} ± {fit['perr'][1]:.0f}"
              f"   {c:>+7.2f}")

    delta_aic = fit_ff_e["aic"] - fit_ff_l["aic"]
    print(f"\n  ΔAIC (forest-free, exp − lin-cap) = {delta_aic:+.1f}  "
          f"({'lin-cap preferred' if delta_aic > 0 else 'exp preferred'})")

    # ── Matched-window sensitivity — REPORTED ONLY, NOT ADOPTED ──
    # The headline δ₀ and L above are the published values and are not
    # refitted here.  This table exists so the effect of a matched-window
    # refit on them is visible before anyone decides to take one.
    print("\n  Matched-window sensitivity (reported only, not adopted) ...")
    mw = matched_window_sensitivity(
        df_ff, cwb, model_linear_capped,
        p0=[-30.0, 1000.0, -5.0],            # as the headline fit above
        bounds=([-200, 100, -30], [50, 10000, 30]))
    mw.to_csv(paths.OUT_25_MATCHED_WINDOW_SENS, index=False)
    for _, r in mw.iterrows():
        print(f"    {r['subset']:<13} n_wells={r['n_wells']:>3d}  "
              f"δ₀={r['delta_0_mm_yr']:+7.2f} ± {r['delta_0_se']:.2f}  "
              f"L={r['L_m']:6.0f} ± {r['L_se']:.0f}  "
              f"c={r['c_mm_yr']:+6.2f} ± {r['c_se']:.2f}  "
              f"β_cwb·dCWB/dt={r['climate_cwb_mm_yr']:+5.2f}  "
              f"sum={r['identified_sum_mm_yr']:+6.2f}")
    warn("25_11 is a sensitivity: nothing downstream reads it and the "
         "published δ₀ / L are unchanged")

    # ── Fit-window sensitivity sweep (25_12) ──
    # 25_11 varies the WELL SET; this varies the WINDOW with the well set
    # held fixed, which is the axis that actually moves c. Reported beside
    # the observed far-field trend so the constant can be judged against an
    # observable instead of being asserted meaningless.
    step("Fit-window sensitivity sweep")
    sweep = window_sweep(
        {"forest_free": long_ff, "c3_only": long_c3},
        cwb, model_linear_capped,
        p0=[-30.0, 1000.0, -5.0],
        bounds=([-200, 100, -30], [50, 10000, 30]))
    sweep.to_csv(paths.OUT_25_WINDOW_SWEEP, index=False)
    saved(paths.OUT_25_WINDOW_SWEEP.name)
    plot_window_sweep(sweep, paths.OUT_25_WINDOW_SWEEP_FIG)
    saved(paths.OUT_25_WINDOW_SWEEP_FIG.name)
    _usable = sweep[sweep["usable"]] if not sweep.empty else sweep
    if len(_usable):
        _ff = _usable[_usable["spec"] == "forest_free"]
        if len(_ff):
            warn(f"c spans {_ff['c_mm_yr'].min():+.2f} to "
                 f"{_ff['c_mm_yr'].max():+.2f} mm/yr on the forest-free panel "
                 "with the well set unchanged — it is a property of the fit "
                 "window, not a rate, and is not quoted as one")

    # ── MAM-only sensitivity fits (panel refit on Mar–May rows only) ──
    # The HEADLINE gradient is the all-season fit above; these MAM-restricted
    # refits are a SENSITIVITY, appended to 25_01 beside the all-season rows.
    # Restricting to Mar–May drops the panel to ≈¼ of its rows and collapses the
    # month fixed effects from 11 dummies to 2, so δ₀ SE roughly doubles and L
    # loosens considerably — expected sampling behaviour, not a seasonal finding.
    # (Whether the gradient is genuinely seasonal is better answered by a
    # season × δ(d)·t interaction on the full panel — see the build design; not
    # in this build.)
    print("\n  Fitting MAM-only sensitivity (Mar–May rows) ...")
    df_full_mam = df_full[df_full["month"].isin(SPRING_MONTHS)].copy()
    df_ff_mam = df_ff[df_ff["month"].isin(SPRING_MONTHS)].copy()
    df_c3_mam = df_c3[df_c3["month"].isin(SPRING_MONTHS)].copy()
    fit_full_l_mam = fit_panel(df_full_mam, model_linear_capped,
                               p0=[-30.0, 1000.0, -5.0],
                               bounds=([-200, 100, -30], [50, 10000, 30]),
                               label="full_lincap_mam")
    fit_full_e_mam = fit_panel(df_full_mam, model_exp,
                               p0=[-40.0, 600.0, -5.0],
                               bounds=([-200, 50, -30], [50, 5000, 30]),
                               label="full_exp_mam")
    fit_ff_l_mam = fit_panel(df_ff_mam, model_linear_capped,
                             p0=[-30.0, 1000.0, -5.0],
                             bounds=([-200, 100, -30], [50, 10000, 30]),
                             label="ff_lincap_mam")
    fit_ff_e_mam = fit_panel(df_ff_mam, model_exp,
                             p0=[-40.0, 600.0, -5.0],
                             bounds=([-200, 50, -30], [50, 5000, 30]),
                             label="ff_exp_mam")
    c_fix_l_mam = float(fit_ff_l_mam["popt"][2])
    c_fix_e_mam = float(fit_ff_e_mam["popt"][2])
    fit_c3_l_mam = fit_panel(df_c3_mam, model_linear_capped,
                             p0=[-30.0, 1000.0],
                             bounds=([-200, 100], [50, 10000]),
                             c_fixed=c_fix_l_mam, label="c3_lincap_cfix_mam")
    fit_c3_e_mam = fit_panel(df_c3_mam, model_exp,
                             p0=[-40.0, 600.0],
                             bounds=([-200, 50], [50, 5000]),
                             c_fixed=c_fix_e_mam, label="c3_exp_cfix_mam")
    print(f"    forest-free lin-cap MAM: δ₀={fit_ff_l_mam['popt'][0]:+.2f} "
          f"± {fit_ff_l_mam['perr'][0]:.2f} mm/yr, "
          f"L={fit_ff_l_mam['popt'][1]:.0f} ± {fit_ff_l_mam['perr'][1]:.0f} m "
          f"(all-season headline: δ₀={fit_ff_l['popt'][0]:+.2f} "
          f"± {fit_ff_l['perr'][0]:.2f}, L={fit_ff_l['popt'][1]:.0f})")

    # ── Parameters table (all-season headline + MAM-only sensitivity) ──
    # All-season rows first (byte-identical to the committed table); the six
    # MAM-only sensitivity rows are appended after them.
    fits = {
        ("full", "linear_capped"):         fit_full_l,
        ("full", "exponential"):           fit_full_e,
        ("forest_free", "linear_capped"):  fit_ff_l,
        ("forest_free", "exponential"):    fit_ff_e,
        ("c3_only", "linear_capped_cfix"): fit_c3_l,
        ("c3_only", "exponential_cfix"):   fit_c3_e,
        ("full_mam", "linear_capped"):         fit_full_l_mam,
        ("full_mam", "exponential"):           fit_full_e_mam,
        ("forest_free_mam", "linear_capped"):  fit_ff_l_mam,
        ("forest_free_mam", "exponential"):    fit_ff_e_mam,
        ("c3_only_mam", "linear_capped_cfix"): fit_c3_l_mam,
        ("c3_only_mam", "exponential_cfix"):   fit_c3_e_mam,
    }
    params = build_fit_parameters_table(fits)
    params.to_csv(paths.OUT_25_FIT_PARAMETERS, index=False)

    # ── Season × δ(d)·t interaction test (is the gradient itself seasonal?) ──
    # One model on the full forest-free panel: δ(d)·t·(1 + γ·spring).  γ is the
    # fractional change in the gradient drift rate in Mar–May; H0: γ = 0
    # (season-independent, the headline assumption).  This is the clean single-
    # model test the build design flagged — an actual p-value, not two subset
    # fits with overlapping CIs.
    print("\n  Season × gradient interaction test (forest-free panel) ...")
    si_lincap = fit_season_interaction(
        df_ff, model_linear_capped,
        p0=[fit_ff_l["popt"][0], fit_ff_l["popt"][1], fit_ff_l["popt"][2], 0.0],
        bounds=([-200, 100, -30, -3.0], [50, 10000, 30, 3.0]),
        label="forest_free_lincap")
    si_exp = fit_season_interaction(
        df_ff, model_exp,
        p0=[fit_ff_e["popt"][0], fit_ff_e["popt"][1], fit_ff_e["popt"][2], 0.0],
        bounds=([-200, 50, -30, -3.0], [50, 5000, 30, 3.0]),
        label="forest_free_exp")
    si_rows = []
    for si, model in [(si_lincap, "linear_capped"), (si_exp, "exponential")]:
        seasonal = (np.isfinite(si["gamma_p"]) and si["gamma_p"] < 0.05)
        si_rows.append({
            "source": "forest_free",
            "model": model,
            "n_obs": si["n"],
            "delta_0_mm_yr": round(float(si["popt"][0]), 2),
            "L_m": round(float(si["popt"][1]), 0),
            "c_mm_yr": round(float(si["popt"][2]), 2),
            "gamma_spring_modulation": round(si["gamma"], 3),
            "gamma_se": round(si["gamma_se"], 3),
            "gamma_t": (round(si["gamma_t"], 2)
                        if np.isfinite(si["gamma_t"]) else None),
            "gamma_p": (round(si["gamma_p"], 4)
                        if np.isfinite(si["gamma_p"]) else None),
            "gradient_seasonal_at_0.05": ("yes" if seasonal else "no"),
            "interpretation": (
                "gamma = fractional change in the coastal-gradient drift rate "
                "in Mar-May vs the rest of the year; H0: gamma=0 "
                "(season-independent). gamma>0 = steeper gradient in spring."),
        })
    pd.DataFrame(si_rows).to_csv(paths.OUT_25_SEASON_INTERACTION, index=False)
    for si, model in [(si_lincap, "lin-cap"), (si_exp, "exp")]:
        print(f"    [{model}] γ = {si['gamma']:+.3f} ± {si['gamma_se']:.3f}  "
              f"(t = {si['gamma_t']:+.2f}, p = {si['gamma_p']:.4f})  →  "
              f"gradient {'IS' if (np.isfinite(si['gamma_p']) and si['gamma_p']<0.05) else 'is NOT'} "
              f"seasonal at 0.05")

    # ── BACI corroboration (all-season gradient; metric-independent) ──
    # 25_04 is not re-emitted per metric — the BACI easting × time coefficient
    # it reads is the same regardless of the seasonal response variable.
    print("\n  Running BACI corroboration check ...")
    baci_corr = baci_corroboration(distances, fit_ff_l,
                                     paths.OUT_10A_FULL_COEFFS)
    baci_corr.to_csv(paths.OUT_25_BACI_CORROBORATION, index=False)
    print(baci_corr[["control_tier", "impact_zone",
                       "baci_absorbs_mm_yr", "model_predicts_mm_yr",
                       "z_test_baci_vs_model", "consistent"]].to_string(index=False))
    plot_baci_corroboration(baci_corr, paths.OUT_25_BACI_CHART)

    # ── Per-metric: per-well slopes, cluster partition, diagnostic figures ──
    # The all-season gradient (fit_ff_l) is the headline and is applied to BOTH
    # seasonal metrics; only the per-well response and the Script-14 observed
    # centroid CSV differ.  --metric {summer_min,spring_mean} runs a single
    # metric for ad-hoc use; the default (both) is what the pipeline runs.
    requested = None
    for _i, _a in enumerate(sys.argv):
        if _a == "--metric" and _i + 1 < len(sys.argv):
            requested = sys.argv[_i + 1]
        elif _a.startswith("--metric="):
            requested = _a.split("=", 1)[1]
    valid_keys = {m["key"] for m in _METRICS}
    if requested is not None and requested not in valid_keys:
        warn(f"--metric {requested!r} not in {sorted(valid_keys)}; "
             f"running all metrics")
        requested = None
    metrics_to_run = [m for m in _METRICS
                      if requested is None or m["key"] == requested]

    # The trend the CWB covariate carries over the headline panel's span.
    # β_cwb from the fit and this trend give the drift the climate covariate
    # contributes; the fitted constant c trades off against it, so 25_03
    # carries both and neither alone.
    cwb_trend_ff = cwb_trend(cwb, fit_ff_l["date_min"], fit_ff_l["date_max"])
    print(f"\n  CWB trend over the headline panel span "
          f"({fit_ff_l['date_min']:%Y-%m}–{fit_ff_l['date_max']:%Y-%m}): "
          f"{cwb_trend_ff:+.3f} mm/yr; β_cwb = "
          f"{fit_ff_l['beta_cwb_m_per_mm']:.4e} m per mm  →  climate term "
          f"{1000 * fit_ff_l['beta_cwb_m_per_mm'] * cwb_trend_ff:+.2f} mm/yr "
          f"(c = {fit_ff_l['popt'][2]:+.2f}; only the sum is identified)")

    partitions = {}
    per_wells = {}
    for m in metrics_to_run:
        print(f"\n  [{m['label']}] Computing per-well slopes ...")
        pw = compute_per_well_slopes(long_full, m["key"])
        pw.to_csv(m["out_per_well"], index=False)
        info(f"{len(pw)} wells with ≥{PANEL_OBS_MIN_YEARS} years "
             f"({m['out_per_well'].name})")

        print(f"  [{m['label']}] Computing per-cluster attribution "
              f"(all-season gradient × balanced annual mean; "
              f"{m['s14_csv'].name} retained as context) ...")
        s14 = pd.read_csv(m["s14_csv"])
        annual, year_col = annual_metric_by_well(long_full, m["key"])
        part = cluster_partition(pw, annual, year_col, fit_ff_l, s14,
                                 cwb_trend_ff)
        part.to_csv(m["out_partition"], index=False)
        print(part[["cluster_label", "mean_dist_coast_m",
                     "observed_centroid_mm_yr",
                     "observed_per_well_mean_mm_yr",
                     DECOMPOSITION_BASIS_COLUMN,
                     "coastal_gradient_mm_yr",
                     "climate_cwb_mm_yr",
                     "far_field_offset_mm_yr",
                     "unexplained_mm_yr",
                     "coastal_gradient_pct_of_basis"]]
              .round(2).to_string(index=False))

        comp = record_length_composition(pw, annual, year_col)
        comp.to_csv(m["out_composition"], index=False)
        info(f"record-length composition → {m['out_composition'].name}")
        print(comp[["cluster_label", "n_wells", "record_length_break_years",
                     "n_wells_long", "mean_slope_long_mm_yr",
                     "n_wells_short", "mean_slope_short_mm_yr",
                     "observed_per_well_mean_mm_yr",
                     DECOMPOSITION_BASIS_COLUMN,
                     "composition_gap_mm_yr"]]
              .round(2).to_string(index=False))

        plot_fit_diagnostic(pw, fit_full_l, fit_ff_l, fit_c3_l,
                            part, m["out_diag"], fit_ff_e=fit_ff_e,
                            figlabels=m["figlabels"])
        plot_cluster_decomposition(part, m["out_decomp"],
                                   figlabels=m["figlabels"])
        partitions[m["key"]] = part
        per_wells[m["key"]] = pw

    # ── Spring-vs-summer comparison (needs both metrics) ──
    if "summer_min" in partitions and "spring_mean" in partitions:
        print("\n  Building spring-vs-summer comparison ...")
        comp = build_spring_vs_summer_comparison(
            partitions["summer_min"], partitions["spring_mean"])
        comp.to_csv(paths.OUT_25_SPRING_VS_SUMMER_CSV, index=False)
        plot_spring_vs_summer(comp, paths.OUT_25_SPRING_VS_SUMMER_FIG)

    # ── Report numbers (all-season headline fit + summer attribution) ──
    # Emitted from the summer metric (the report headline); unchanged.
    if "summer_min" in partitions:
        report = build_report_numbers(
            fits, partitions["summer_min"], baci_corr, per_wells["summer_min"])
        report.to_csv(paths.OUT_25_REPORT_NUMBERS, index=False)

    print(f"\n  Outputs written to: {paths.DIR_25}/")
    print("    25_01_panel_fit_parameters.csv  (all-season + MAM sensitivity)")
    print("    25_02_per_well_summer_min_slopes.csv / _spring_mean_slopes.csv")
    print("    25_03_cluster_partition.csv / _spring.csv")
    print("    25_04_baci_corroboration.csv")
    print("    25_05_fit_diagnostic.jpg / _spring.jpg")
    print("    25_06_baci_corroboration_chart.jpg")
    print("    25_07_cluster_decomposition.png / _spring.png")
    print("    25_08_spring_vs_summer_comparison.csv + .png")
    print("    25_09_season_interaction_test.csv")
    print("    25_10_record_length_composition.csv / _spring.csv")
    print("    25_11_matched_window_sensitivity.csv  (reported only)")
    print("    25_report_numbers.csv")
    info("Script 25 complete.\n")


if __name__ == "__main__":
    main()
