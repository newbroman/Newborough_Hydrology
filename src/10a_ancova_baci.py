r"""

====================================================================================
10a — THREE-COUNTERFACTUAL ANCOVA-BACI ANALYSIS
====================================================================================
Purpose
-------
Primary clearfell result.  Runs the same ANCOVA model three times with
different control centroids (forest, climate, combined), applied to both
the impact and edge tiers, yielding six ANCOVA results.  Distance-weighted
scraping (exponential decay, λ = clearfell_common.SCRAPING_DECAY_LAMBDA)
replaces the binary scraping dummy.
An easting × post-felling interaction captures coastal erosion trends for
the climate and combined controls (dropped for the forest control where
easting range is insufficient).

Outputs
-------
CSV:
  10a_01_ancova_comparison_table.csv   — 6-row summary: 3 controls × 2 zones
  10a_02_ancova_full_coefficients.csv  — full model coefficients for all 6 runs
  10a_03_baci_timeseries.csv           — BACI displacement time-series data
  10a_report_numbers.csv               — all citable values

Figures:
  10a_04_baci_timeseries_impact.png    — 3-panel: displacement, corrected, CUSUM
  10a_05_baci_timeseries_edge.png      — same for edge zone
  10a_06_climate_sensitivity.png       — CWB vs BACI scatter (pre/post) per control

References
----------
Hollingham (2026), §4.6.  Part of the Script 10 clearfell analysis suite.
====================================================================================
"""

__version__ = "1.9.0"  # Hollingham (2026) - 2026-08-31. SUMMER_MONTHS now imported from config.SUMMER_MINIMUM_MONTHS.
#   Batch two of the seasonal-windows migration (D-100): the window's
#   MONTHS ARE UNCHANGED and the constant is asserted equal to the literal it
#   replaced, in value and in type, read mechanically out of git HEAD. No
#   committed value moves.
#
# v1.8.0  # Hollingham (2026) — 2026-08-29. the clearfell date constant is now named CLEARFELL_DATE (T-17).
#   No value changes; verified by re-run against the 2026-08-29 pipeline outputs.
# v1.7.0  # Hollingham (2026) -- 2026-08-28. s_coast derived from psi
#   (M14 / D-076) and the fixed-at-1 sensitivity committed.
# 1.6.0  # Hollingham (2026) -- 2026-08-21. Far-field control tier added
#   to CONTROLS, plus the per-control-well spread refits behind
#   10a_09_control_well_spread.csv.
#
#   The far-field tier is a control set chosen for DISTANCE CONTRAST against
#   the impact zone rather than for matching its setting, so the BACI
#   easting x time covariate can be tested against the Script 25 coastal-
#   gradient model on a contrast large enough to carry the test. Membership,
#   its admission criterion and the reason NW4 is excluded from it all live in
#   clearfell_common.
#
#   'Combined' is deliberately NOT extended to include the new tier: folding it
#   in would move a published number and buys nothing analytically, since the
#   far-field tier is reported in its own right. See the CONTROLS comment.
#
#   The tier spans a wide band of distances and its members need not respond
#   alike, so the tier estimate is not reported alone: every control tier is
#   also refit one control well at a time and the resulting spread is emitted
#   beside it, for the new tier and the existing ones on the same footing.
#   Additive only -- the six published control x zone fits are untouched.
#
# v1.5.1  # Hollingham (2026) -- 2026-08-18. Store-time rounding removed (D-035): these values
#   are written to CSV at the precision they were computed, and rounding
#   happens where they are displayed. Three decimals is a display rule for
#   quantities of order one; applied at storage it costs a significant
#   figure on the small ones - beta_3 ~ 0.018, Sy ~ 0.31 - and the loss
#   compounds through every statistic taken afterwards.
#
# v1.5.0  # Hollingham (2026) — 2026-07-03
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)

from utils.clearfell_common import (
    load_clearfell_data, apply_ceh34_hindcast, IMPACT_WELLS, EDGE_WELLS,
    FOREST_CONTROL_WELLS, COASTAL_CONTROL_WELLS, CLIMATE_CONTROL_WELLS,
    FAR_FIELD_CONTROL_WELLS, FAR_FIELD_CONTROL_LABEL,
    ALL_NETWORK_WELLS, CLEARFELL_DATE, SCRAPING_DATE, SCRAPING_DATE_2,
    PRE_FELL_START, SCRAPING_DECAY_LAMBDA, compute_baci_displacement,
    compute_cwb, build_scraping_covariate_centroid, distance_from_ceh36,
    coastal_drift_differential,
    scraping_weight, ReportNumbers, print_network_summary,
    well_distances_to_coast, tier_distance_stats, far_field_tier_audit,
)
from utils.paths import make_all_dirs, DIR_10, OUT_10A_CONTROL_WELL_SPREAD
from utils.render_utils import render_figure
from utils.config import SUMMER_MINIMUM_MONTHS
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats as sp_stats
import warnings
warnings.filterwarnings('ignore')

make_all_dirs()

# ============================================================================
# OUTPUT PATHS
# ============================================================================
OUT_COMPARISON    = DIR_10 / "10a_01_ancova_comparison_table.csv"
OUT_FULL_COEFFS   = DIR_10 / "10a_02_ancova_full_coefficients.csv"
OUT_TIMESERIES    = DIR_10 / "10a_03_baci_timeseries.csv"
OUT_REPORT        = DIR_10 / "10a_report_numbers.csv"
OUT_WELL_SPREAD   = OUT_10A_CONTROL_WELL_SPREAD   # paths.py — Script 25 reads it
OUT_COASTAL_SCALE = DIR_10 / "10a_09_coastal_scale_factor.csv"
OUT_COASTAL_FIXED1= DIR_10 / "10a_10_coastal_fixed1_sensitivity.csv"
# Primary figures (Forest control only — for report)
OUT_FIG_IMPACT    = DIR_10 / "10a_04_baci_timeseries_impact.png"
OUT_FIG_EDGE      = DIR_10 / "10a_05_baci_timeseries_edge.png"
OUT_FIG_SCATTER   = DIR_10 / "10a_06_climate_sensitivity.png"
OUT_FIG_CUSUM_IMP = DIR_10 / "10a_07_cusum_impact.png"
OUT_FIG_CUSUM_EDGE= DIR_10 / "10a_08_cusum_edge.png"
# Supplementary figures (three-panel, all controls)
OUT_FIG_IMPACT_3P = DIR_10 / "10a_S1_baci_timeseries_impact_3panel.png"
OUT_FIG_EDGE_3P   = DIR_10 / "10a_S2_baci_timeseries_edge_3panel.png"
OUT_FIG_SCATTER_3P= DIR_10 / "10a_S3_climate_sensitivity_3panel.png"

# ============================================================================
# MATPLOTLIB DEFAULTS
# ============================================================================
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
})

# Colour-blind-safe palette
CB_FOREST  = '#4DAC26'
CB_CLIMATE = '#4575B4'
CB_COMBINED = '#7570B3'  # muted purple
CB_IMPACT  = '#D73027'
CB_EDGE    = '#F46D43'
# The controls the FIGURES plot. This is deliberately narrower than CONTROLS:
# the supplementary three-panel figures are the three published counterfactuals
# and their panel geometry is fixed to that set. The far-field tier is a
# distance-contrast diagnostic feeding the Script 25 corroboration and is
# reported through the CSVs, so adding it here would change published figures
# for no analytical gain.
CONTROL_COLOURS = {
    'Forest':   CB_FOREST,
    'Climate':  CB_CLIMATE,
    'Combined': CB_COMBINED,
}


# ============================================================================
# UTILITY: OLS WITH SE, P, R², AIC
# ============================================================================

def ols_fit(y, X):
    """OLS fit returning coefficients, standard errors, p-values, R², AIC.

    Parameters
    ----------
    y : 1-D array
    X : 2-D array with intercept column included

    Returns
    -------
    dict with keys: b, se, p, r2, aic, n, k, resid
    """
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    n, k = X.shape
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ b
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    s2 = ss_res / (n - k) if n > k else np.nan
    try:
        cov = s2 * np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(k, np.nan)
    t_stat = b / se
    p_vals = 2 * sp_stats.t.sf(np.abs(t_stat), df=n - k)
    aic = n * np.log(ss_res / n) + 2 * k if n > 0 and ss_res > 0 else np.nan
    return dict(b=b, se=se, p=p_vals, r2=r2, aic=aic,
                n=n, k=k, resid=resid)


def format_p(p):
    """Format p-value for console output."""
    if pd.isna(p):
        return "NA"
    if p < 0.001:
        return "<0.001"
    return f"{p:.4f}"


def p_to_sig(p):
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


# ============================================================================
# LOAD DATA
# ============================================================================
banner("10a", "THREE-COUNTERFACTUAL ANCOVA-BACI", version=__version__)

phase(1, "Loading data")
wells, _wells_prov, climate, master, well_locations, valid_tiers = load_clearfell_data()
wells = apply_ceh34_hindcast(wells)
print_network_summary(valid_tiers)

# The far-field tier states its own geometry rather than a comment asserting
# it: distances come from the committed well metadata and the admission
# threshold is config.FAR_FIELD_REACH_MULTIPLE x the fitted cross-shore reach,
# read live from Script 25's panel-fit table.
_ff_audit = far_field_tier_audit()
if not _ff_audit.empty:
    _r0 = _ff_audit.iloc[0]
    info(f"Far-field control tier: {len(_ff_audit)} wells, "
         f"mean {_r0['tier_mean_dist_m']:.0f} m from the coast, "
         f"span {_r0['tier_span_m']:.0f} m, "
         f"contrast {_r0['contrast_vs_impact_m']:.0f} m against the impact "
         f"zone at {_r0['impact_dist_m']:.0f} m")
    info(f"  admission threshold {_r0['admission_threshold_m']:.0f} m "
         f"= {_r0['admission_threshold_m'] / _r0['reach_L_m']:.2f} x the "
         f"fitted reach {_r0['reach_L_m']:.0f} m ({_r0['reach_source']}); "
         f"members clearing it: "
         f"{int(_ff_audit['clears_threshold'].sum())}/{len(_ff_audit)}")
    for _, _rw in _ff_audit.iterrows():
        print(f"     {_rw['well']:<8}  d = {_rw['dist_coast_m']:7.1f} m"
              f"   {'clears' if _rw['clears_threshold'] else 'BELOW'} "
              f"threshold")

# ============================================================================
# BUILD BACI DISPLACEMENT TIME-SERIES (for each control)
# ============================================================================
phase(2, "Building BACI displacement time-series")
# NOTE on 'Combined'.  It is the union of the three tiers it names and NOTHING
# ELSE.  The far-field tier is a separate entry below and is deliberately NOT
# folded into 'Combined': doing so would change a published clearfell step for
# no analytical gain, since the far-field result is reported in its own right
# and its value lies in the distance contrast that pooling would dilute.
CONTROLS = {
    'Forest':   FOREST_CONTROL_WELLS,                    # C4 only (5 wells)
    'Climate':  CLIMATE_CONTROL_WELLS,                   # C3 (5 wells)
    'Combined': (FOREST_CONTROL_WELLS +                  # All 12 controls
                 COASTAL_CONTROL_WELLS +
                 CLIMATE_CONTROL_WELLS),
    # Chosen for distance contrast, not for matching the impact zone's
    # setting — see clearfell_common.FAR_FIELD_CONTROL_WELLS for the
    # admission criteria and for why NW4 is excluded from it.
    FAR_FIELD_CONTROL_LABEL: FAR_FIELD_CONTROL_WELLS,
}

ZONES = {
    'Impact': IMPACT_WELLS,
    'Edge':   EDGE_WELLS,
}


def build_ancova_frame(wells, climate, target_wells, control_wells,
                       well_locations, lambda_m=SCRAPING_DECAY_LAMBDA):
    """Build the ANCOVA design matrix for one zone × one control.

    Returns a DataFrame with columns:
      baci_disp, cwb_c, D_scrape, D_fell, cwb_x_fell,
      easting_x_fell (optional — only if eastings span > 200 m among
      the union of target + control wells)
    plus metadata columns: Post, Scraped.
    """
    # ── BACI displacement ────────────────────────────────────────────
    baci = compute_baci_displacement(wells, target_wells, control_wells)

    # ── CWB ──────────────────────────────────────────────────────────
    cwb = compute_cwb(climate)
    common = baci.index.intersection(cwb.index)
    df = pd.DataFrame({
        'baci_disp': baci.loc[common],
        'cwb':       cwb.loc[common],
    }).dropna()

    # ── Record-length-balance cutoff ─────────────────────────────────
    # Pooled BACI inference requires that target and control centroids
    # are aggregated over a period in which all wells contribute equally.
    # See clearfell_common.py docstring for the principle.
    df = df.loc[df.index >= PRE_FELL_START]

    if len(df) < 20:
        return None

    # Centre CWB on its own mean
    df['cwb_c'] = df['cwb'] - df['cwb'].mean()

    # ── Scraping covariate (distance-weighted) ───────────────────────
    # The BACI displacement is target_centroid − control_centroid, so
    # the scraping covariate for the BACI should also be a differential:
    # target scraping weight − control scraping weight.
    target_scrape = build_scraping_covariate_centroid(
        df.index, SCRAPING_DATE, well_locations, target_wells, lambda_m)
    control_scrape = build_scraping_covariate_centroid(
        df.index, SCRAPING_DATE, well_locations, control_wells, lambda_m)
    df['D_scrape'] = target_scrape.loc[df.index] - control_scrape.loc[df.index]

    # ── Re-scraping (Oct 2023) ───────────────────────────────────────
    target_scrape2 = build_scraping_covariate_centroid(
        df.index, SCRAPING_DATE_2, well_locations, target_wells, lambda_m)
    control_scrape2 = build_scraping_covariate_centroid(
        df.index, SCRAPING_DATE_2, well_locations, control_wells, lambda_m)
    df['D_scrape2'] = target_scrape2.loc[df.index] - control_scrape2.loc[df.index]

    # ── Clearfell dummy ──────────────────────────────────────────────
    df['D_fell'] = (df.index >= CLEARFELL_DATE).astype(float)

    # ── CWB × clearfell interaction ──────────────────────────────────
    df['cwb_x_fell'] = df['cwb_c'] * df['D_fell']

    # ── Easting interaction (coastal erosion gradient) ────────────────
    # Compute the mean easting of each well in the combined set, then
    # check whether the easting range > 200 m (otherwise the term is
    # uninformative).
    all_wells_in_model = list(set(target_wells + control_wells))
    eastings = []
    for w in all_wells_in_model:
        if w in well_locations:
            eastings.append(well_locations[w]['easting'])
    easting_range = max(eastings) - min(eastings) if len(eastings) >= 2 else 0

    # For the BACI displacement, the easting signal enters as the
    # difference between target centroid easting and control centroid
    # easting, interacted with post-felling time.  If the easting range
    # among all wells < 200 m (i.e. forest control wells all clustered
    # together), we drop this term.
    # Months since the start of the frame, kept as a COLUMN rather than a
    # local. It was local until 2026-08-28 and computed only inside the easting
    # branch, so the elapsed-time axis every drift term shares was reachable
    # only through a term that may not exist. The s_coast fixed-at-1 sensitivity
    # (D-076) needs the same axis, and rebuilding it downstream from df.index
    # would be one more place for the epoch to disagree.
    t0 = df.index.min()
    df['months_since'] = (df.index - t0).days / 30.4375

    df['has_easting'] = False
    if easting_range > 200:
        target_eastings = [well_locations[w]['easting'] for w in target_wells
                           if w in well_locations]
        control_eastings = [well_locations[w]['easting'] for w in control_wells
                            if w in well_locations]
        if target_eastings and control_eastings:
            delta_easting = np.mean(target_eastings) - np.mean(control_eastings)
            df['easting_x_time'] = delta_easting * df['months_since']
            df['has_easting'] = True

    return df


def run_ancova(df, include_easting=None, include_scrape2=False):
    """Run ANCOVA on a prepared DataFrame.

    Parameters
    ----------
    df : DataFrame from build_ancova_frame()
    include_easting : bool or None
        If None, auto-detect from df['has_easting'].
    include_scrape2 : bool
        If True, add Oct 2023 re-scraping term and compare AIC.

    Returns
    -------
    dict with full results
    """
    if include_easting is None:
        include_easting = df['has_easting'].iloc[0] if 'has_easting' in df else False

    # Build design matrix
    cols = ['cwb_c', 'D_scrape', 'D_fell', 'cwb_x_fell']
    col_names = ['intercept', 'cwb', 'scraping', 'clearfell', 'cwb_x_fell']
    if include_easting and 'easting_x_time' in df.columns:
        cols.append('easting_x_time')
        col_names.append('easting_x_time')

    X = np.column_stack([np.ones(len(df))] + [df[c].values for c in cols])
    y = df['baci_disp'].values

    fit = ols_fit(y, X)
    fit['col_names'] = col_names

    # CI for clearfell step
    fell_idx = col_names.index('clearfell')
    ci_lo = fit['b'][fell_idx] - 1.96 * fit['se'][fell_idx]
    ci_hi = fit['b'][fell_idx] + 1.96 * fit['se'][fell_idx]
    fit['clearfell_step'] = fit['b'][fell_idx]
    fit['clearfell_p'] = fit['p'][fell_idx]
    fit['clearfell_ci'] = (ci_lo, ci_hi)

    # Scraping step
    scr_idx = col_names.index('scraping')
    fit['scraping_step'] = fit['b'][scr_idx]
    fit['scraping_p'] = fit['p'][scr_idx]

    # Oct 2023 re-scraping test (Model 3)
    if include_scrape2 and 'D_scrape2' in df.columns:
        cols2 = cols + ['D_scrape2']
        X2 = np.column_stack([np.ones(len(df))] + [df[c].values for c in cols2])
        fit2 = ols_fit(y, X2)
        fit['m3_scrape2_coef'] = fit2['b'][-1]
        fit['m3_scrape2_p'] = fit2['p'][-1]
        fit['m3_aic'] = fit2['aic']
        fit['m2_aic'] = fit['aic']
        fit['daic'] = fit2['aic'] - fit['aic']
    else:
        fit['m3_scrape2_coef'] = np.nan
        fit['m3_scrape2_p'] = np.nan
        fit['daic'] = np.nan

    return fit


# ============================================================================
# RUN THREE-COUNTERFACTUAL ANCOVA
# ============================================================================
phase(3, "Running three-counterfactual ANCOVA")
results = {}       # keyed by (control_label, zone_label)
ancova_frames = {} # keyed the same way

for ctrl_label, ctrl_wells in CONTROLS.items():
    for zone_label, zone_wells in ZONES.items():
        key = (ctrl_label, zone_label)
        print(f"   {ctrl_label} control × {zone_label}...", end=" ")

        df = build_ancova_frame(
            wells, climate, zone_wells, ctrl_wells,
            well_locations, lambda_m=SCRAPING_DECAY_LAMBDA)

        if df is None or len(df) < 20:
            skipped("(insufficient data)")
            continue

        ancova_frames[key] = df

        # Easting interaction: auto-detect from data (easting range > 200 m)
        use_easting = df['has_easting'].iloc[0]

        fit = run_ancova(df, include_easting=use_easting,
                         include_scrape2=True)
        results[key] = fit

        step_mm = fit['clearfell_step'] * 1000
        ci_mm = (fit['clearfell_ci'][0] * 1000, fit['clearfell_ci'][1] * 1000)
        print(f"step = {step_mm:+.0f} mm  "
              f"CI = [{ci_mm[0]:+.0f}, {ci_mm[1]:+.0f}]  "
              f"p = {format_p(fit['clearfell_p'])}  "
              f"R² = {fit['r2']:.3f}")

# ============================================================================
# DIRECT SUMMER FIT (Jun-Sep) — Forest × Impact only
# ============================================================================
# Replaces the arithmetic SUMMER_SCALING_RATIO construct in Script 21
# (Defect 14).  Re-fits the same ANCOVA specification on the Jun-Sep
# subset of the existing Forest × Impact ANCOVA frame; emits the
# directly-fitted summer clearfell step plus a no-CWB sensitivity
# variant.  Only the Forest × Impact case is fit because:
#   (a) the summer band in Script 21 is constructed only for the
#       headline forecaster preset (Forest control, Impact zone);
#   (b) other control × zone combinations are reported as annual-only
#       in the comparison table and not used in any seasonal scenario.
# ============================================================================
print("\n3a. Direct summer (Jun-Sep) ANCOVA — Forest × Impact...")

summer_results = {}
SUMMER_MONTHS = list(SUMMER_MINIMUM_MONTHS)
SUMMER_KEY = ('Forest', 'Impact')

if SUMMER_KEY in ancova_frames:
    df_summer = ancova_frames[SUMMER_KEY].loc[
        ancova_frames[SUMMER_KEY].index.month.isin(SUMMER_MONTHS)
    ].copy()
    n_pre  = int((df_summer['D_fell'] == 0).sum())
    n_post = int((df_summer['D_fell'] == 1).sum())
    print(f"   Summer panel: N = {len(df_summer)}  (pre-fell {n_pre}, post-fell {n_post})")

    # --- Fit A: full spec (mirrors annual model) ---
    use_easting = bool(df_summer['has_easting'].iloc[0])
    summer_fit_full = run_ancova(df_summer, include_easting=use_easting,
                                 include_scrape2=False)
    summer_results['full'] = summer_fit_full

    step_mm = summer_fit_full['clearfell_step'] * 1000
    ci_mm = (summer_fit_full['clearfell_ci'][0] * 1000,
             summer_fit_full['clearfell_ci'][1] * 1000)
    print(f"   Full spec  : step = {step_mm:+.0f} mm  "
          f"CI = [{ci_mm[0]:+.0f}, {ci_mm[1]:+.0f}]  "
          f"p = {format_p(summer_fit_full['clearfell_p'])}  "
          f"R² = {summer_fit_full['r2']:.3f}  "
          f"AIC = {summer_fit_full['aic']:.2f}")

    # --- Fit B: CWB dropped (sensitivity variant) ---
    # Reuses the design-matrix construction from run_ancova but with
    # cwb_c and cwb_x_fell columns omitted.
    cols_noCWB = ['D_scrape', 'D_fell']
    names_noCWB = ['intercept', 'scraping', 'clearfell']
    if use_easting and 'easting_x_time' in df_summer.columns:
        cols_noCWB.append('easting_x_time')
        names_noCWB.append('easting_x_time')
    X_noCWB = np.column_stack([np.ones(len(df_summer))]
                              + [df_summer[c].values for c in cols_noCWB])
    y_summer = df_summer['baci_disp'].values
    fit_noCWB = ols_fit(y_summer, X_noCWB)
    fit_noCWB['col_names'] = names_noCWB
    fell_idx = names_noCWB.index('clearfell')
    ci_lo = fit_noCWB['b'][fell_idx] - 1.96 * fit_noCWB['se'][fell_idx]
    ci_hi = fit_noCWB['b'][fell_idx] + 1.96 * fit_noCWB['se'][fell_idx]
    fit_noCWB['clearfell_step'] = fit_noCWB['b'][fell_idx]
    fit_noCWB['clearfell_p'] = fit_noCWB['p'][fell_idx]
    fit_noCWB['clearfell_ci'] = (ci_lo, ci_hi)
    summer_results['noCWB'] = fit_noCWB

    step_mm = fit_noCWB['clearfell_step'] * 1000
    ci_mm = (ci_lo * 1000, ci_hi * 1000)
    print(f"   No-CWB     : step = {step_mm:+.0f} mm  "
          f"CI = [{ci_mm[0]:+.0f}, {ci_mm[1]:+.0f}]  "
          f"p = {format_p(fit_noCWB['clearfell_p'])}  "
          f"R² = {fit_noCWB['r2']:.3f}  "
          f"AIC = {fit_noCWB['aic']:.2f}")

    # ΔAIC: full vs no-CWB
    daic = summer_fit_full['aic'] - fit_noCWB['aic']
    print(f"   ΔAIC (full − no-CWB) = {daic:+.2f}  "
          f"({'CWB retained' if daic < 0 else 'CWB dropped'} preferred)")
else:
    skipped("Forest × Impact ANCOVA frame unavailable")

# ============================================================================
# 3b. CURVATURE (CWB² × felling) SENSITIVITY VARIANT — Forest Impact + Edge
# ============================================================================
# The headline ANCOVA fits a LINEAR CWB × felling interaction, which tests
# whether felling changed the *linear* climate sensitivity of the water
# table.  That interaction is non-significant (the linear buffering test is
# null).  A linear slope is, however, a blunt instrument for a hypothesis
# about climate *extremes*: a buffering effect concentrated at the wet/dry
# tails can average to zero across the full CWB range.
#
# This block fits a non-linear extension — the headline design matrix plus
# a centred CWB² main effect and a CWB² × felling interaction — on the
# full-data Forest control frames for the Impact and Edge zones.  It is a
# REPORTED SENSITIVITY VARIANT only: the headline clearfell step and the
# linear model are unchanged.  The variant exists so §4.6 can cite the
# curvature result (and its ΔAIC against the linear model) from a pipeline
# output rather than an external diagnostic.
#
# Interpretation note for the report: a significant cwb2_x_fell term
# indicates the felling response is CWB-state-dependent (concave — larger
# uplift in dry/low-CWB conditions).  This is consistent with — but not on
# its own proof of — a dry-period canopy-buffering mechanism; state
# dependence has alternative explanations (post-felling non-stationary
# drift, the coastal-erosion gradient).  Report neutrally and as
# preliminary.  See FINDING_canopy_buffering_consolidated.md.
print("\n3b. Curvature (CWB² × felling) variant — Forest × Impact, Edge...")

curvature_results = {}
for zone_label in ZONES.keys():
    ckey = ('Forest', zone_label)
    if ckey not in ancova_frames:
        print(f"   {zone_label}: SKIPPED — Forest ANCOVA frame unavailable")
        continue

    df_c = ancova_frames[ckey].copy()
    use_easting = bool(df_c['has_easting'].iloc[0])

    # Centred CWB² main effect and its interaction with the felling dummy.
    # cwb_c is already mean-centred in build_ancova_frame(); squaring it
    # keeps the curvature term on the same centred basis as the linear term.
    df_c['cwb2_c'] = df_c['cwb_c'] ** 2
    df_c['cwb2_x_fell'] = df_c['cwb2_c'] * df_c['D_fell']

    # Linear (headline-shape) model — refit here so the ΔAIC comparison is
    # on the identical row set as the curvature model.
    lin_cols = ['cwb_c', 'D_scrape', 'D_fell', 'cwb_x_fell']
    lin_names = ['intercept', 'cwb', 'scraping', 'clearfell', 'cwb_x_fell']
    if use_easting and 'easting_x_time' in df_c.columns:
        lin_cols.append('easting_x_time')
        lin_names.append('easting_x_time')
    y_c = df_c['baci_disp'].values
    X_lin = np.column_stack([np.ones(len(df_c))]
                            + [df_c[c].values for c in lin_cols])
    fit_lin = ols_fit(y_c, X_lin)

    # Curvature model — headline design + cwb2_c + cwb2_x_fell
    cur_cols = lin_cols + ['cwb2_c', 'cwb2_x_fell']
    cur_names = lin_names + ['cwb2_c', 'cwb2_x_fell']
    X_cur = np.column_stack([np.ones(len(df_c))]
                            + [df_c[c].values for c in cur_cols])
    fit_cur = ols_fit(y_c, X_cur)
    fit_cur['col_names'] = cur_names

    # Clearfell step CI (re-referenced under the curvature model)
    fell_idx = cur_names.index('clearfell')
    ci_lo = fit_cur['b'][fell_idx] - 1.96 * fit_cur['se'][fell_idx]
    ci_hi = fit_cur['b'][fell_idx] + 1.96 * fit_cur['se'][fell_idx]
    fit_cur['clearfell_step'] = fit_cur['b'][fell_idx]
    fit_cur['clearfell_p'] = fit_cur['p'][fell_idx]
    fit_cur['clearfell_ci'] = (ci_lo, ci_hi)

    # ΔAIC: curvature vs linear (negative = curvature preferred)
    fit_cur['daic_vs_linear'] = fit_cur['aic'] - fit_lin['aic']

    # Joint F-test for the two added curvature terms
    n, k_cur = fit_cur['n'], fit_cur['k']
    rss_lin = float(fit_lin['resid'] @ fit_lin['resid'])
    rss_cur = float(fit_cur['resid'] @ fit_cur['resid'])
    f_stat = ((rss_lin - rss_cur) / 2.0) / (rss_cur / (n - k_cur))
    fit_cur['joint_F'] = f_stat
    fit_cur['joint_F_p'] = float(sp_stats.f.sf(f_stat, 2, n - k_cur))

    curvature_results[zone_label] = fit_cur

    c2_idx = cur_names.index('cwb2_x_fell')
    print(f"   {zone_label}: cwb2_x_fell = {fit_cur['b'][c2_idx]:+.3e}  "
          f"p = {format_p(fit_cur['p'][c2_idx])}  "
          f"ΔAIC = {fit_cur['daic_vs_linear']:+.2f}  "
          f"joint F = {f_stat:.2f} (p = {format_p(fit_cur['joint_F_p'])})  "
          f"step {fit_lin['b'][lin_names.index('clearfell')]*1000:+.0f}→"
          f"{fit_cur['clearfell_step']*1000:+.0f} mm")

# ============================================================================
# PER-CONTROL-WELL SPREAD
# ============================================================================
# A control tier's ANCOVA is fitted against the tier CENTROID, so the result is
# a tier mean and says nothing about whether the tier's members agree.  That
# matters most for a tier selected on distance rather than on setting: its
# members can sit a long way apart and need not respond alike, in which case
# the tier mean is the less meaningful summary and a reader has to be able to
# see it.
#
# The spread is measured by refitting the SAME specification with each control
# well used singly as the control set, and reporting the resulting range beside
# the tier estimate.  It is computed for EVERY control tier, not only the new
# one: a spread is only interpretable against the spread the established tiers
# show, and quoting it for one tier alone would invite the reader to judge it
# against zero.
#
# These are diagnostics.  None of them replaces a tier fit, and the tier fits
# above are untouched by this section.
print("\n3c. Per-control-well spread — refitting each tier one control well "
      "at a time...")

_coast_dists = well_distances_to_coast()
spread_rows = []

for ctrl_label, ctrl_wells in CONTROLS.items():
    tier_stats = tier_distance_stats(ctrl_wells, _coast_dists)
    for zone_label, zone_wells in ZONES.items():
        tier_fit = results.get((ctrl_label, zone_label))
        if tier_fit is None:
            continue

        tier_east = np.nan
        if 'easting_x_time' in tier_fit['col_names']:
            tier_east = float(
                tier_fit['b'][tier_fit['col_names'].index('easting_x_time')])

        per_well = []
        for cw in ctrl_wells:
            df_w = build_ancova_frame(
                wells, climate, zone_wells, [cw],
                well_locations, lambda_m=SCRAPING_DECAY_LAMBDA)
            if df_w is None or len(df_w) < 20:
                skipped(f"{ctrl_label} × {zone_label}: {cw.upper()} "
                        f"(insufficient data)")
                continue
            fit_w = run_ancova(
                df_w, include_easting=bool(df_w['has_easting'].iloc[0]))
            e_coef = e_se = e_p = np.nan
            if 'easting_x_time' in fit_w['col_names']:
                _k = fit_w['col_names'].index('easting_x_time')
                e_coef = float(fit_w['b'][_k])
                e_se = float(fit_w['se'][_k])
                e_p = float(fit_w['p'][_k])
            per_well.append({
                'Control': ctrl_label,
                'Zone': zone_label,
                'Control_well': cw.upper(),
                'Control_dist_coast_m': _coast_dists.get(cw, np.nan),
                'Clearfell_step_m': float(fit_w['clearfell_step']),
                'Clearfell_p': float(fit_w['clearfell_p']),
                'Easting_coef': e_coef,
                'Easting_se': e_se,
                'Easting_p': e_p,
                'R2': float(fit_w['r2']),
                'N': int(fit_w['n']),
            })

        if not per_well:
            continue

        steps = np.array([r['Clearfell_step_m'] for r in per_well], dtype=float)
        easts = np.array([r['Easting_coef'] for r in per_well], dtype=float)
        for r in per_well:
            r.update({
                'N_control_wells': len(per_well),
                'Tier_mean_dist_coast_m': tier_stats['mean_m'],
                'Tier_dist_span_m': tier_stats['span_m'],
                'Tier_clearfell_step_m': float(tier_fit['clearfell_step']),
                'Tier_easting_coef': tier_east,
                'Spread_step_min_m': float(np.nanmin(steps)),
                'Spread_step_max_m': float(np.nanmax(steps)),
                'Spread_step_sd_m': (float(np.nanstd(steps, ddof=1))
                                     if len(steps) > 1 else np.nan),
                'Spread_easting_min': (float(np.nanmin(easts))
                                       if np.isfinite(easts).any() else np.nan),
                'Spread_easting_max': (float(np.nanmax(easts))
                                       if np.isfinite(easts).any() else np.nan),
                'Spread_easting_sd': (float(np.nanstd(easts, ddof=1))
                                      if np.isfinite(easts).sum() > 1
                                      else np.nan),
            })
        spread_rows.extend(per_well)

        if len(steps) > 1:
            detail = (f"per-well steps {np.nanmin(steps) * 1000:+.0f} to "
                      f"{np.nanmax(steps) * 1000:+.0f} mm "
                      f"(n={len(per_well)}, "
                      f"SD={np.nanstd(steps, ddof=1) * 1000:.0f} mm)")
        else:
            detail = "single control well — no spread to report"
        print(f"   {ctrl_label:<10} × {zone_label:<7} "
              f"tier step = {tier_fit['clearfell_step'] * 1000:+.0f} mm   "
              f"{detail}")

spread_df = pd.DataFrame(spread_rows)

# ============================================================================
# SENSITIVITY: scraping decay length
# ============================================================================
phase(4, "Scraping decay sensitivity (λ = 200 m, 500 m)")
sensitivity_rows = []
for lam in [200, 500]:
    for ctrl_label, ctrl_wells in CONTROLS.items():
        for zone_label, zone_wells in ZONES.items():
            df = build_ancova_frame(
                wells, climate, zone_wells, ctrl_wells,
                well_locations, lambda_m=lam)
            if df is None:
                continue
            use_easting = df['has_easting'].iloc[0]
            fit = run_ancova(df, include_easting=use_easting)
            sensitivity_rows.append({
                'Lambda_m': lam,
                'Control': ctrl_label,
                'Zone': zone_label,
                'Clearfell_step_m': fit['clearfell_step'],
                'Clearfell_p': fit['clearfell_p'],
                'R2': fit['r2'],
            })

sensitivity_df = pd.DataFrame(sensitivity_rows)
if not sensitivity_df.empty:
    print("   Clearfell steps by λ:")
    for _, row in sensitivity_df.iterrows():
        print(f"     λ={row['Lambda_m']:.0f}  {row['Control']:<10} {row['Zone']:<8}  "
              f"step = {row['Clearfell_step_m']*1000:+.0f} mm  p = {format_p(row['Clearfell_p'])}")

# ============================================================================
# EXPORT: COMPARISON TABLE
# ============================================================================
phase(5, "Exporting comparison table")
comp_rows = []
for (ctrl_label, zone_label), fit in results.items():
    easting_coef = np.nan
    easting_p = np.nan
    if 'easting_x_time' in fit['col_names']:
        idx = fit['col_names'].index('easting_x_time')
        easting_coef = fit['b'][idx]
        easting_p = fit['p'][idx]

    comp_rows.append({
        'Control': ctrl_label,
        'Zone': zone_label,
        'Clearfell_step_m': float(fit['clearfell_step']),
        'Clearfell_CI_lo_m': float(fit['clearfell_ci'][0]),
        'Clearfell_CI_hi_m': float(fit['clearfell_ci'][1]),
        'Clearfell_p': fit['clearfell_p'],
        'Clearfell_sig': p_to_sig(fit['clearfell_p']),
        'Scraping_step_m': float(fit['scraping_step']),
        'Scraping_p': fit['scraping_p'],
        'Easting_coef': easting_coef if not np.isnan(easting_coef) else '',
        'Easting_p': easting_p if not np.isnan(easting_p) else '',
        'R2': float(fit['r2']),
        'N': fit['n'],
        'Oct2023_step_m': float(fit['m3_scrape2_coef']) if not np.isnan(fit['m3_scrape2_coef']) else '',
        'Oct2023_p': fit['m3_scrape2_p'] if not np.isnan(fit['m3_scrape2_p']) else '',
        'dAIC_M3_M2': float(fit['daic']) if not np.isnan(fit['daic']) else '',
    })

comp_df = pd.DataFrame(comp_rows)

# Net clearfell effect: step minus Climate background step (per zone)
# The Climate control step represents background climate shift at the
# felling date. Subtracting it isolates the clearfell-attributable component.
for zone in comp_df['Zone'].unique():
    mask_zone = comp_df['Zone'] == zone
    climate_step = comp_df.loc[mask_zone & (comp_df['Control'] == 'Climate'),
                               'Clearfell_step_m']
    if len(climate_step) == 1:
        bg = climate_step.iloc[0]
        comp_df.loc[mask_zone, 'Climate_background_m'] = float(bg)
        comp_df.loc[mask_zone, 'Net_clearfell_m'] = (
            comp_df.loc[mask_zone, 'Clearfell_step_m'] - bg)
    else:
        comp_df.loc[mask_zone, 'Climate_background_m'] = np.nan
        comp_df.loc[mask_zone, 'Net_clearfell_m'] = np.nan

comp_df.to_csv(OUT_COMPARISON, index=False)
saved(f"{OUT_COMPARISON.name} ({len(comp_df)} rows)")

# ============================================================================
# EXPORT: FULL COEFFICIENTS TABLE
# ============================================================================
coeff_rows = []
for (ctrl_label, zone_label), fit in results.items():
    for i, cname in enumerate(fit['col_names']):
        coeff_rows.append({
            'Control': ctrl_label,
            'Zone': zone_label,
            'Coefficient': cname,
            'Value': float(fit['b'][i]),
            'SE': float(fit['se'][i]),
            'p': fit['p'][i],
            'Sig': p_to_sig(fit['p'][i]),
        })

coeff_df = pd.DataFrame(coeff_rows)
coeff_df.to_csv(OUT_FULL_COEFFS, index=False)
saved(f"{OUT_FULL_COEFFS.name} ({len(coeff_df)} rows)")

# ── Per-control-well spread (see the section that built it) ──────────────
spread_df.to_csv(OUT_WELL_SPREAD, index=False)
saved(f"{OUT_WELL_SPREAD.name} ({len(spread_df)} rows)")

# ============================================================================
# EXPORT: BACI TIMESERIES DATA
# ============================================================================
phase(6, "Exporting BACI time-series data")
ts_frames = []
for (ctrl_label, zone_label), df in ancova_frames.items():
    if (ctrl_label, zone_label) not in results:
        continue
    fit = results[(ctrl_label, zone_label)]
    # Climate-corrected BACI: remove CWB and interaction effects
    cwb_idx = fit['col_names'].index('cwb')
    cwb_fell_idx = fit['col_names'].index('cwb_x_fell')
    corrected = (df['baci_disp']
                 - fit['b'][cwb_idx] * df['cwb_c']
                 - fit['b'][cwb_fell_idx] * df['cwb_c'] * df['D_fell'])

    # Also remove easting if present
    if 'easting_x_time' in fit['col_names']:
        east_idx = fit['col_names'].index('easting_x_time')
        corrected = corrected - fit['b'][east_idx] * df['easting_x_time']

    ts_out = pd.DataFrame({
        'Date': df.index,
        'Control': ctrl_label,
        'Zone': zone_label,
        'BACI_raw': df['baci_disp'].values,
        'BACI_corrected': corrected.values,
        'CWB': df['cwb'].values,
    })
    ts_frames.append(ts_out)

ts_df = pd.concat(ts_frames, ignore_index=True)
ts_df.to_csv(OUT_TIMESERIES, index=False)
saved(f"{OUT_TIMESERIES.name} ({len(ts_df)} rows)")

# ============================================================================
# FIGURES
# ============================================================================
phase(7, "Generating figures")
CB_FOREST = '#4DAC26'


def _vlines(ax):
    """Add intervention date lines."""
    ax.axvline(SCRAPING_DATE, color='#999999', ls='--', lw=0.8, zorder=1)
    ax.axvline(CLEARFELL_DATE, color='#333333', ls='-', lw=1.2, zorder=1)
    ax.axvline(SCRAPING_DATE_2, color='#999999', ls=':', lw=0.8, zorder=1)


def _compute_corrected(df, fit):
    """Compute climate-corrected BACI displacement."""
    cwb_idx = fit['col_names'].index('cwb')
    cwb_fell_idx = fit['col_names'].index('cwb_x_fell')
    corrected = (df['baci_disp']
                 - fit['b'][cwb_idx] * df['cwb_c']
                 - fit['b'][cwb_fell_idx] * df['cwb_c'] * df['D_fell'])
    if 'easting_x_time' in fit['col_names']:
        east_idx = fit['col_names'].index('easting_x_time')
        corrected = corrected - fit['b'][east_idx] * df['easting_x_time']
    return corrected


def _plot_era_means(ax, df, corrected_mm, color=None):
    """Draw era mean horizontal lines from the corrected series.

    Parameters
    ----------
    color : str or None
        Line colour matched to the series being plotted.
        Falls back to '#555555' if None.
    """
    line_color = color if color is not None else '#555555'
    for mask, x0, x1 in [
        (df.index < SCRAPING_DATE,
         df.index[0], SCRAPING_DATE),
        ((df.index >= SCRAPING_DATE) & (df.index < CLEARFELL_DATE),
         SCRAPING_DATE, CLEARFELL_DATE),
        (df.index >= CLEARFELL_DATE,
         CLEARFELL_DATE, df.index[-1]),
    ]:
        era_data = corrected_mm[mask]
        if len(era_data) > 0:
            ax.hlines(era_data.mean(), x0, x1,
                      colors=line_color, ls='--', lw=1.8, alpha=0.85,
                      zorder=3)


# ── Primary figures: Forest control only (for report) ────────────────────────

def plot_forest_timeseries(zone_label, out_path):
    """Single-panel Forest control BACI timeseries."""
    key = ('Forest', zone_label)
    if key not in ancova_frames or key not in results:
        skipped(f"Forest × {zone_label} not available")
        return

    df = ancova_frames[key]
    fit = results[key]

    fig, ax = plt.subplots(figsize=(14, 5), dpi=300)

    ax.plot(df.index, df['baci_disp'] * 1000, color=CB_FOREST, alpha=0.4,
            lw=0.8, label='Raw')

    corrected = _compute_corrected(df, fit)
    ax.plot(df.index, corrected * 1000, color=CB_FOREST, lw=1.5,
            label='Climate-corrected')

    _plot_era_means(ax, df, corrected * 1000, color=CB_FOREST)
    _vlines(ax)

    ax.set_ylabel('BACI displacement (mm)')
    fell_step = fit['clearfell_step'] * 1000
    ci_mm = (fit['clearfell_ci'][0] * 1000, fit['clearfell_ci'][1] * 1000)
    ax.set_title(
        f'Forest control — {zone_label} zone   |   '
        f'Clearfell = {fell_step:+.0f} mm  '
        f'[{ci_mm[0]:+.0f}, {ci_mm[1]:+.0f}]  '
        f'p = {format_p(fit["clearfell_p"])}  '
        f'R² = {fit["r2"]:.3f}',
        fontsize=12)
    ax.legend(loc='upper left', frameon=False, fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    fig.tight_layout()
    render_figure(fig, out_path, facecolor='white')
    plt.close(fig)
    saved(f"{out_path.name}")


plot_forest_timeseries('Impact', OUT_FIG_IMPACT)
plot_forest_timeseries('Edge', OUT_FIG_EDGE)


# ── Climate sensitivity scatter: Forest control, Impact + Edge ───────────────
#
# The trend lines are the ANCOVA-FITTED climate-response lines, NOT free
# per-period polyfits.  A free polyfit per era diverges unconstrained and
# visually implies a slope change that the (non-significant) linear
# cwb_x_fell interaction does not support — i.e. it plots a different model
# than the panel title's step.  The fitted lines below are drawn from the
# headline ANCOVA: for each era, BACI displacement vs CWB holding the
# scraping and easting covariates at their era-mean values, so the vertical
# gap between the two lines IS the fitted clearfell step in the title.

print("   Climate sensitivity (Forest control)...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
fig.subplots_adjust(wspace=0.30)

for j, zone_label in enumerate(ZONES.keys()):
    ax = axes[j]
    key = ('Forest', zone_label)
    if key not in ancova_frames:
        continue

    df = ancova_frames[key]
    fit = results[key]
    pre = df[df.index < CLEARFELL_DATE]
    post = df[df.index >= CLEARFELL_DATE]

    ax.scatter(pre['cwb'], pre['baci_disp'] * 1000,
               color=CB_FOREST, alpha=0.4, s=20, label='Pre-felling (data)')
    ax.scatter(post['cwb'], post['baci_disp'] * 1000,
               color=CB_FOREST, marker='x', s=30, label='Post-felling (data)')

    # ANCOVA-fitted climate-response lines.  The model is fitted on centred
    # CWB (cwb_c); convert back to raw CWB for the x-axis.  Other covariates
    # (scraping, easting) are held at their era-mean so the line is the pure
    # CWB response and the pre/post vertical offset is the fitted step.
    cn = fit['col_names']
    b = fit['b']
    cwb_mean = df['cwb'].mean()
    b_int  = b[cn.index('intercept')]
    b_cwb  = b[cn.index('cwb')]
    b_fell = b[cn.index('clearfell')]
    b_cxf  = b[cn.index('cwb_x_fell')]
    b_scr  = b[cn.index('scraping')]
    has_e  = 'easting_x_time' in cn
    b_east = b[cn.index('easting_x_time')] if has_e else 0.0

    for subset, ls, lbl, d_fell in [
            (pre,  '--', 'Pre-felling (ANCOVA fit)',  0.0),
            (post, '-',  'Post-felling (ANCOVA fit)', 1.0)]:
        if len(subset) <= 5:
            continue
        x_raw = np.linspace(subset['cwb'].min(), subset['cwb'].max(), 50)
        x_c = x_raw - cwb_mean
        scr_mean = subset['D_scrape'].mean()
        east_mean = subset['easting_x_time'].mean() if has_e else 0.0
        y_fit = (b_int
                 + b_cwb * x_c
                 + b_fell * d_fell
                 + b_cxf * x_c * d_fell
                 + b_scr * scr_mean
                 + b_east * east_mean) * 1000
        ax.plot(x_raw, y_fit, color='grey', ls=ls, lw=1.4, label=lbl)

    ax.set_xlabel('Cumulative water balance (mm)')
    ax.set_ylabel(f'{zone_label} BACI disp. (mm)')
    fell_step = fit['clearfell_step'] * 1000
    ax.set_title(f'{zone_label} zone   |   step = {fell_step:+.0f} mm  '
                 f'p = {format_p(fit["clearfell_p"])}', fontsize=11)
    if j == 0:
        ax.legend(loc='best', frameon=False, fontsize=8)

fig.suptitle('Climate sensitivity: CWB vs BACI displacement — Forest control',
             fontsize=13, y=1.02)
render_figure(fig, OUT_FIG_SCATTER, facecolor='white')
plt.close(fig)
saved(f"{OUT_FIG_SCATTER.name}")


# ── CUSUM: Forest control, Impact + Edge ─────────────────────────────────────

print("   CUSUM (Forest control)...")

for zone_label, out_path in [('Impact', OUT_FIG_CUSUM_IMP),
                              ('Edge', OUT_FIG_CUSUM_EDGE)]:
    key = ('Forest', zone_label)
    if key not in ancova_frames or key not in results:
        skipped(f"Forest × {zone_label} not available for CUSUM")
        continue

    df = ancova_frames[key]
    fit = results[key]
    corrected = _compute_corrected(df, fit)

    # CUSUM: demeaned on pre-felling baseline
    pre_fell_mean = corrected[corrected.index < CLEARFELL_DATE].mean()
    detrended = corrected - pre_fell_mean
    cusum = detrended.cumsum() * 1000  # mm

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), dpi=300,
                             gridspec_kw={'height_ratios': [2, 1]})
    fig.subplots_adjust(hspace=0.25)

    # Top: climate-corrected timeseries
    ax = axes[0]
    ax.plot(df.index, df['baci_disp'] * 1000, color=CB_FOREST, alpha=0.4,
            lw=0.8, label='Raw')
    ax.plot(corrected.index, corrected * 1000, color=CB_FOREST, lw=1.5,
            label='Climate-corrected')
    _plot_era_means(ax, df, corrected * 1000, color=CB_FOREST)
    _vlines(ax)
    ax.set_ylabel('BACI displacement (mm)')
    fell_step = fit['clearfell_step'] * 1000
    ci_mm = (fit['clearfell_ci'][0] * 1000, fit['clearfell_ci'][1] * 1000)
    ax.set_title(
        f'Forest control — {zone_label} zone   |   '
        f'Clearfell = {fell_step:+.0f} mm  '
        f'[{ci_mm[0]:+.0f}, {ci_mm[1]:+.0f}]  '
        f'p = {format_p(fit["clearfell_p"])}',
        fontsize=11)
    ax.legend(loc='upper left', frameon=False, fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Bottom: CUSUM
    ax = axes[1]
    ax.fill_between(cusum.index, 0, cusum.values, color=CB_FOREST, alpha=0.3)
    ax.plot(cusum.index, cusum.values, color=CB_FOREST, lw=1.5)
    ax.axhline(0, color='grey', lw=0.5)
    _vlines(ax)

    cusum_at_fell = cusum.loc[cusum.index >= CLEARFELL_DATE]
    if len(cusum_at_fell) > 0:
        ax.annotate(f'At clearfell: {cusum_at_fell.iloc[0]:.0f} mm',
                    xy=(CLEARFELL_DATE, cusum_at_fell.iloc[0]),
                    fontsize=9, ha='left', va='bottom',
                    xytext=(10, 5), textcoords='offset points')
    cusum_final = cusum.iloc[-1]
    ax.annotate(f'Final: {cusum_final:.0f} mm',
                xy=(cusum.index[-1], cusum_final),
                fontsize=9, ha='right', va='bottom',
                xytext=(-10, 5), textcoords='offset points')

    ax.set_ylabel('CUSUM (mm)')
    ax.set_title('Climate-corrected CUSUM (demeaned on pre-felling baseline)',
                 fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    fig.suptitle(f'CUSUM — {zone_label} zone vs Forest Control',
                 fontsize=13, y=0.98)
    render_figure(fig, out_path, facecolor='white')
    plt.close(fig)
    saved(f"{out_path.name}")


# ── Supplementary figures: three-panel (all controls) ────────────────────────

print("   Supplementary three-panel figures...")


def plot_baci_timeseries_3panel(zone_label, out_path):
    """Plot 3-panel BACI timeseries for one zone, all three controls."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), dpi=300)
    fig.subplots_adjust(hspace=0.30)

    for i, (ctrl_label, colour) in enumerate(CONTROL_COLOURS.items()):
        key = (ctrl_label, zone_label)
        ax = axes[i]

        if key not in ancova_frames or key not in results:
            ax.text(0.5, 0.5, f'No data for {ctrl_label} × {zone_label}',
                    ha='center', va='center', transform=ax.transAxes)
            continue

        df = ancova_frames[key]
        fit = results[key]

        ax.plot(df.index, df['baci_disp'] * 1000, color=colour, alpha=0.4,
                lw=0.8, label='Raw')

        corrected = _compute_corrected(df, fit)
        ax.plot(df.index, corrected * 1000, color=colour, lw=1.5,
                label='Climate-corrected')

        _plot_era_means(ax, df, corrected * 1000, color=colour)
        _vlines(ax)
        ax.set_ylabel('BACI displacement (mm)')
        fell_step = fit['clearfell_step'] * 1000
        ci_mm = (fit['clearfell_ci'][0] * 1000, fit['clearfell_ci'][1] * 1000)
        ax.set_title(
            f'{ctrl_label} control — {zone_label} zone   |   '
            f'Clearfell = {fell_step:+.0f} mm  '
            f'[{ci_mm[0]:+.0f}, {ci_mm[1]:+.0f}]  '
            f'p = {format_p(fit["clearfell_p"])}  '
            f'R² = {fit["r2"]:.3f}',
            fontsize=11)
        ax.legend(loc='upper left', frameon=False, fontsize=9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    fig.suptitle(
        f'ANCOVA-BACI: {zone_label} zone — three counterfactuals\n'
        f'Distance-weighted scraping (λ = {SCRAPING_DECAY_LAMBDA:.0f} m)',
        fontsize=13, y=0.98)
    render_figure(fig, out_path, facecolor='white', full_page=True)
    plt.close(fig)
    saved(f"{out_path.name}")


plot_baci_timeseries_3panel('Impact', OUT_FIG_IMPACT_3P)
plot_baci_timeseries_3panel('Edge', OUT_FIG_EDGE_3P)

# Supplementary scatter (all controls)
fig, axes = plt.subplots(2, 3, figsize=(16, 10), dpi=300)
fig.subplots_adjust(hspace=0.35, wspace=0.30)
for j, zone_label in enumerate(ZONES.keys()):
    for i, (ctrl_label, colour) in enumerate(CONTROL_COLOURS.items()):
        ax = axes[j, i]
        key = (ctrl_label, zone_label)
        if key not in ancova_frames:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                    transform=ax.transAxes)
            continue
        df = ancova_frames[key]
        fit = results[key]
        pre = df[df.index < CLEARFELL_DATE]
        post = df[df.index >= CLEARFELL_DATE]
        ax.scatter(pre['cwb'], pre['baci_disp'] * 1000,
                   color=colour, alpha=0.4, s=20, label='Pre-felling')
        ax.scatter(post['cwb'], post['baci_disp'] * 1000,
                   color=colour, marker='x', s=30, label='Post-felling')
        for subset, ls in [(pre, '--'), (post, '-')]:
            if len(subset) > 5:
                slope, intercept = np.polyfit(subset['cwb'],
                                             subset['baci_disp'] * 1000, 1)
                x_line = np.linspace(subset['cwb'].min(),
                                     subset['cwb'].max(), 50)
                ax.plot(x_line, slope * x_line + intercept, color='grey',
                        ls=ls, lw=1)
        ax.set_xlabel('Cumulative water balance (mm)')
        ax.set_ylabel(f'{zone_label} BACI disp. (mm)')
        ax.set_title(f'{ctrl_label} control', fontsize=11)
        if j == 0 and i == 0:
            ax.legend(loc='best', frameon=False, fontsize=8)
fig.suptitle('Climate sensitivity: CWB vs BACI displacement',
             fontsize=13, y=0.98)
render_figure(fig, OUT_FIG_SCATTER_3P, facecolor='white')
plt.close(fig)
saved(f"{OUT_FIG_SCATTER_3P.name}")

# ============================================================================
# EXPORT: REPORT NUMBERS
# ============================================================================
phase(9, "Exporting report numbers")
# ============================================================================
# COASTAL SCALE FACTOR s_coast  (M14 / D-076)
# ============================================================================
# WHY THIS IS A DERIVATION AND NOT A REFIT.
#
# D-050 withdrew the reading of psi -- the easting x time coefficient -- as a
# measurement of coastal retreat, because within this panel easting carries no
# information about distance to the shore (r = +0.022 across the fifteen
# clearfell wells) and the term is a nuisance control nobody could interpret.
# M14 asked whether replacing it with the fitted coastal decay evaluated at
# each well's own distance would make it interpretable.
#
# In a PAIRED BACI the answer is that the two are the same column. Both are one
# scalar times elapsed months -- `delta_easting x months` and
# `delta_delta x months / 12000` -- so they span the same one-dimensional space
# and the two designs are the same model: same clearfell step, same p, same
# AIC to machine precision. Measured, not assumed (M14_RESULT_2026-08-28.md).
#
# So refitting would be work with risk and no information: it would change the
# name of a column that Script 25's baci_corroboration() matches on, and return
# the numbers already committed. What the re-parameterisation actually buys is
# a MEANING, and a meaning can be derived exactly:
#
#     s_coast = psi * delta_easting * 12 * 1000 / delta_delta
#     se      = se_psi * |delta_easting| * 12 * 1000 / |delta_delta|
#
# s_coast = 1 means the pair feels precisely the amplitude Script 25 fitted.
# The departure from 1 is the finding, and unlike psi it has a scale.
#
# READ THE DENOMINATOR BEFORE READING THE RATIO. Where a control tier sits at
# nearly the impact zone's distance from the shore, delta_delta is near zero,
# s_coast is a small denominator rather than a measurement, and the row says so
# in its `identified` column instead of leaving the reader to notice.
print("\n3d. Coastal scale factor s_coast (M14 / D-076) ...")

# IDENTIFICATION IS JUDGED ON THE SCALE FACTOR'S OWN SE, NOT ON A DISTANCE.
#
# A threshold on |delta_delta| looks like the natural guard and is the wrong
# one: it asks whether the tiers are far apart, when the question is whether
# the ratio is determined. The two hypotheses this quantity exists to separate
# are s = 1 (the pair feels exactly the fitted field) and s = 0 (it feels none
# of it), and they are ONE APART -- so an estimate whose standard error exceeds
# 1 cannot distinguish them, and one whose SE exceeds 2 is not evidence about
# either. That is a statement about the estimate, and it holds whatever the
# geometry that produced it.
#
# On the committed panel this separates the rows the way reading them by hand
# does: the Climate pairs, whose differentials are -0.94 and +0.26 mm/yr,
# return SEs of 3.3 and 15.3 and are excluded; the Combined pairs, at -3.74 and
# -2.54 mm/yr, return 0.61 and 0.67 and are kept. A distance floor set anywhere
# high enough to exclude the first would have taken the second with it.
S_COAST_MAX_SE = 2.0
S_COAST_MIN_DIFFERENTIAL = 0.5   # mm/yr — only to keep the division honest

coastal_rows = []
for (ctrl_label, zone_label), fit in results.items():
    if 'easting_x_time' not in fit['col_names']:
        continue
    zone_wells = ZONES[zone_label]
    ctrl_wells = CONTROLS[ctrl_label]
    d_delta, d0, L, prov = coastal_drift_differential(
        zone_wells, ctrl_wells, verbose=False)
    df_k = ancova_frames[(ctrl_label, zone_label)]
    te = [well_locations[w]['easting'] for w in zone_wells if w in well_locations]
    ce = [well_locations[w]['easting'] for w in ctrl_wells if w in well_locations]
    dE = np.mean(te) - np.mean(ce)
    i = fit['col_names'].index('easting_x_time')
    absorbed = fit['b'][i] * dE * 12 * 1000.0          # mm/yr
    absorbed_se = fit['se'][i] * abs(dE) * 12 * 1000.0
    if np.isfinite(d_delta) and abs(d_delta) >= S_COAST_MIN_DIFFERENTIAL:
        s = absorbed / d_delta
        s_se = absorbed_se / abs(d_delta)
        t1 = (s - 1.0) / s_se
        p1 = 2 * sp_stats.t.sf(abs(t1), df=fit['n'] - fit['k'])
    else:
        s = s_se = p1 = np.nan
    identified = bool(np.isfinite(s_se) and s_se <= S_COAST_MAX_SE)
    coastal_rows.append({
        'control_tier': ctrl_label, 'zone': zone_label,
        'coastal_differential_mm_yr': d_delta,
        'delta_0_mm_yr': d0, 'reach_L_m': L, 'donor': prov,
        'delta_easting_m': dE,
        'absorbed_drift_mm_yr': absorbed,
        'absorbed_drift_se_mm_yr': absorbed_se,
        's_coast': s, 's_coast_se': s_se,
        'p_vs_zero': fit['p'][i],      # identical to psi's: a ratio by a constant
        'p_vs_one': p1,
        'identified': identified,
        'n_months': fit['n'],
    })
    if identified:
        print(f"   {ctrl_label:<9} {zone_label:<7} "
              f"Δδ={d_delta:+6.2f} mm/yr  absorbed={absorbed:+6.2f}  "
              f"s_coast={s:+.3f} ± {s_se:.3f}  "
              f"(p vs 0 {format_p(fit['p'][i])}, p vs 1 {format_p(p1)})")
    else:
        print(f"   {ctrl_label:<9} {zone_label:<7} "
              f"Δδ={d_delta:+6.2f} mm/yr  s_coast={s:+.2f} ± {s_se:.2f}  "
              f"— NOT IDENTIFIED (SE > {S_COAST_MAX_SE}: cannot separate "
              f"s = 1 from s = 0; these tiers sit at nearly the same distance "
              f"from the shore)")

coastal_df = pd.DataFrame(coastal_rows)
coastal_df.to_csv(OUT_COASTAL_SCALE, index=False)
saved(f"{OUT_COASTAL_SCALE.name} ({len(coastal_df)} rows)")

# --- the fixed-at-1 sensitivity ---------------------------------------------
# D-076 keeps s_coast FREE as canonical and reports fixed-at-1 as a sensitivity.
# Fixing it is NOT a re-parameterisation -- it is a different model, because the
# term stops being fitted and becomes an offset subtracted from the response.
# That is the variant that moves the headline step, and it is committed here so
# the number is a pipeline output rather than a figure in a working note.
sens_rows = []
for row in coastal_rows:
    if not row['identified']:
        continue
    key = (row['control_tier'], row['zone'])
    df_k = ancova_frames[key]
    off = (row['coastal_differential_mm_yr'] / 12.0 / 1000.0) \
        * df_k['months_since'].values if 'months_since' in df_k.columns else None
    if off is None:
        continue
    cols = ['cwb_c', 'D_scrape', 'D_fell', 'cwb_x_fell']
    X = np.column_stack([np.ones(len(df_k))] + [df_k[c].values for c in cols])
    f1 = ols_fit(df_k['baci_disp'].values - off, X)
    j = 3   # D_fell, with the intercept prepended
    sens_rows.append({
        'control_tier': row['control_tier'], 'zone': row['zone'],
        'clearfell_step_free_m': results[key]['clearfell_step'],
        'clearfell_step_free_p': results[key]['clearfell_p'],
        's_coast_fitted': row['s_coast'],
        'clearfell_step_fixed1_m': f1['b'][j],
        'clearfell_step_fixed1_se_m': f1['se'][j],
        'clearfell_step_fixed1_p': f1['p'][j],
        'shift_mm': (f1['b'][j] - results[key]['clearfell_step']) * 1000.0,
    })
    print(f"   {row['control_tier']:<9} {row['zone']:<7} "
          f"step {results[key]['clearfell_step']*1000:+.1f} mm (s free) -> "
          f"{f1['b'][j]*1000:+.1f} mm (s fixed at 1, "
          f"p={format_p(f1['p'][j])})")
sens_df = pd.DataFrame(sens_rows)
sens_df.to_csv(OUT_COASTAL_FIXED1, index=False)
saved(f"{OUT_COASTAL_FIXED1.name} ({len(sens_df)} rows)")

rpt = ReportNumbers()

for (ctrl_label, zone_label), fit in results.items():
    prefix = f"ANCOVA_{ctrl_label}_{zone_label}"

    rpt.add(f"{prefix}_clearfell_step", fit['clearfell_step'],
            well=zone_label, era="Post_felling",
            note=f"p={format_p(fit['clearfell_p'])}, "
                 f"CI=[{fit['clearfell_ci'][0]:.4f},{fit['clearfell_ci'][1]:.4f}]")

    rpt.add(f"{prefix}_scraping_step", fit['scraping_step'],
            well=zone_label, era="Post_scraping",
            note=f"p={format_p(fit['scraping_p'])}")

    rpt.add(f"{prefix}_R2", fit['r2'], unit="",
            well=zone_label, note="Model R²")

    rpt.add(f"{prefix}_N", fit['n'], unit="months",
            well=zone_label, note="Sample size")

    # Full model coefficients
    for i, cname in enumerate(fit['col_names']):
        rpt.add(f"{prefix}_coeff_{cname}", fit['b'][i],
                well=zone_label,
                note=f"SE={fit['se'][i]:.6f}, p={format_p(fit['p'][i])}")

    # s_coast (M14 / D-076) — the interpretable form of the drift coefficient.
    # Emitted per pair so a document can cite the scale factor rather than psi,
    # and always with `identified` in the note, because the ratio is meaningless
    # where the two tiers sit at the same distance from the shore.
    _cs = [r for r in coastal_rows
           if r['control_tier'] == ctrl_label and r['zone'] == zone_label]
    if _cs:
        _r = _cs[0]
        if _r['identified']:
            rpt.add(f"{prefix}_s_coast", _r['s_coast'], unit="",
                    well=zone_label,
                    note=(f"SE={_r['s_coast_se']:.4f}, "
                          f"p vs 0={format_p(_r['p_vs_zero'])}, "
                          f"p vs 1={format_p(_r['p_vs_one'])}; "
                          f"the amplitude of the Script 25 coastal gradient "
                          f"this pair feels, 1 = exactly the fitted field. "
                          f"Differential {_r['coastal_differential_mm_yr']:+.2f} "
                          f"mm/yr from {_r['donor']}"))
        else:
            rpt.add(f"{prefix}_s_coast_identified", 0.0, unit="",
                    well=zone_label,
                    note=(f"NOT IDENTIFIED: s_coast = {_r['s_coast']:+.2f} "
                          f"± {_r['s_coast_se']:.2f}, and an SE above "
                          f"{S_COAST_MAX_SE} cannot separate s = 1 from "
                          f"s = 0. The coastal differential here is "
                          f"{_r['coastal_differential_mm_yr']:+.2f} mm/yr — "
                          f"these tiers sit at nearly the same distance from "
                          f"the shore, so the ratio is a small denominator, "
                          f"not a measurement"))
    _sn = [r for r in sens_rows
           if r['control_tier'] == ctrl_label and r['zone'] == zone_label]
    if _sn:
        _s = _sn[0]
        rpt.add(f"{prefix}_clearfell_step_s_fixed1", _s['clearfell_step_fixed1_m'],
                well=zone_label, era="Post_felling",
                note=(f"SENSITIVITY, not the headline (D-076): the clearfell "
                      f"step with the coastal correction imposed at the fitted "
                      f"amplitude (s_coast = 1) instead of estimated. "
                      f"p={format_p(_s['clearfell_step_fixed1_p'])}; moves the "
                      f"headline by {_s['shift_mm']:+.1f} mm"))

    # Oct 2023 re-scraping test
    if not np.isnan(fit['m3_scrape2_coef']):
        rpt.add(f"{prefix}_Oct2023_step", fit['m3_scrape2_coef'],
                well=zone_label, era="Oct2023",
                note=f"p={format_p(fit['m3_scrape2_p'])}, dAIC={fit['daic']:.2f}")

# Summer (Jun-Sep) ANCOVA — Forest × Impact (Defect 14 fix)
# These rows are consumed by Script 21's _load_baci_params() to construct
# the seasonal BACI band on the forestry scenario hydrograph.
if 'full' in summer_results:
    sf = summer_results['full']
    prefix = "ANCOVA_Forest_Impact"
    rpt.add(f"{prefix}_clearfell_step_summer", sf['clearfell_step'],
            well="Impact", era="Post_felling_Jun-Sep",
            note=f"p={format_p(sf['clearfell_p'])}, "
                 f"CI=[{sf['clearfell_ci'][0]:.4f},{sf['clearfell_ci'][1]:.4f}], "
                 f"Jun-Sep subset, full ANCOVA spec")
    rpt.add(f"{prefix}_summer_R2", sf['r2'], unit="",
            well="Impact", era="Jun-Sep",
            note="Summer model R² (full spec)")
    rpt.add(f"{prefix}_summer_N", sf['n'], unit="months",
            well="Impact", era="Jun-Sep",
            note="Summer sample size (Jun-Sep months only)")
    for i, cname in enumerate(sf['col_names']):
        rpt.add(f"{prefix}_coeff_{cname}_summer", sf['b'][i],
                well="Impact", era="Jun-Sep",
                note=f"SE={sf['se'][i]:.6f}, p={format_p(sf['p'][i])}")

if 'noCWB' in summer_results:
    sn = summer_results['noCWB']
    prefix = "ANCOVA_Forest_Impact"
    rpt.add(f"{prefix}_clearfell_step_summer_noCWB", sn['clearfell_step'],
            well="Impact", era="Post_felling_Jun-Sep",
            note=f"p={format_p(sn['clearfell_p'])}, "
                 f"CI=[{sn['clearfell_ci'][0]:.4f},{sn['clearfell_ci'][1]:.4f}], "
                 f"Jun-Sep subset, CWB dropped (sensitivity variant)")
    rpt.add(f"{prefix}_summer_noCWB_R2", sn['r2'], unit="",
            well="Impact", era="Jun-Sep",
            note="Summer model R² (CWB dropped)")
    rpt.add(f"{prefix}_summer_noCWB_N", sn['n'], unit="months",
            well="Impact", era="Jun-Sep",
            note="Summer sample size (CWB dropped fit, Jun-Sep only)")

# Curvature (CWB² × felling) variant — Forest Impact + Edge (§4.6 buffering).
# Reported SENSITIVITY VARIANT — the headline clearfell_step rows above are
# the linear model and are unchanged.  cwb2_x_fell is the buffering-relevant
# term; the clearfell_step_curv row is the step RE-REFERENCED under the
# curvature model (it differs from the headline step — see the note).
#
# The cwb2 coefficients are O(1e-6) in native units (m per mm²), which the
# ReportNumbers 4-dp Value rounding would collapse to 0.0 (the same display
# limitation already affects the cwb and easting_x_time rows).  The curvature
# coefficient IS the citable number for §4.6, so it is stored here SCALED to
# mm of displacement per (100 mm CWB)² — a readable O(10) magnitude — with the
# unit string recording the scaling.  The native-unit value and SE are also
# given in the note for completeness.  Scale factor: native (m/mm²) × 1000
# (m→mm) × 100² (per-mm² → per-(100mm)²) = ×1e7.
CWB2_SCALE = 1.0e7  # native m/mm²  ->  mm per (100 mm CWB)²
for zone_label, fc in curvature_results.items():
    prefix = f"ANCOVA_Forest_{zone_label}"
    c2_idx = fc['col_names'].index('cwb2_x_fell')
    c2m_idx = fc['col_names'].index('cwb2_c')
    rpt.add(f"{prefix}_coeff_cwb2_x_fell", fc['b'][c2_idx] * CWB2_SCALE,
            unit="mm per (100mm CWB)^2",
            well=zone_label,
            note=f"native={fc['b'][c2_idx]:.6e} m/mm^2, "
                 f"SE_native={fc['se'][c2_idx]:.6e}, "
                 f"p={format_p(fc['p'][c2_idx])}, "
                 f"curvature variant — buffering term")
    rpt.add(f"{prefix}_coeff_cwb2_c", fc['b'][c2m_idx] * CWB2_SCALE,
            unit="mm per (100mm CWB)^2",
            well=zone_label,
            note=f"native={fc['b'][c2m_idx]:.6e} m/mm^2, "
                 f"SE_native={fc['se'][c2m_idx]:.6e}, "
                 f"p={format_p(fc['p'][c2m_idx])}, "
                 f"curvature variant — CWB² main effect")
    rpt.add(f"{prefix}_curv_clearfell_step", fc['clearfell_step'],
            well=zone_label, era="Post_felling",
            note=f"p={format_p(fc['clearfell_p'])}, "
                 f"CI=[{fc['clearfell_ci'][0]:.4f},{fc['clearfell_ci'][1]:.4f}], "
                 f"clearfell step re-referenced under curvature model "
                 f"(NOT the headline step)")
    rpt.add(f"{prefix}_curv_R2", fc['r2'], unit="",
            well=zone_label, note="Curvature model R²")
    rpt.add(f"{prefix}_curv_dAIC", fc['daic_vs_linear'], unit="",
            well=zone_label,
            note="AIC(curvature) − AIC(linear); negative = curvature preferred")
    rpt.add(f"{prefix}_curv_jointF", fc['joint_F'], unit="",
            well=zone_label,
            note=f"joint F-test, cwb2_c + cwb2_x_fell, p={format_p(fc['joint_F_p'])}")

# Sensitivity results
for _, row in sensitivity_df.iterrows():
    rpt.add(f"Sensitivity_lambda{row['Lambda_m']:.0f}_{row['Control']}_{row['Zone']}_clearfell",
            row['Clearfell_step_m'],
            well=row['Zone'],
            note=f"p={format_p(row['Clearfell_p'])}, R²={row['R2']:.3f}")

# Far-field tier geometry — derived, so a document can cite the contrast the
# corroboration test rests on without any script typing a distance.
if not _ff_audit.empty:
    _r0 = _ff_audit.iloc[0]
    rpt.add("FarField_tier_mean_dist_coast", _r0['tier_mean_dist_m'],
            unit="m", well="FarField",
            note=f"n_wells={len(_ff_audit)}, "
                 f"span={_r0['tier_span_m']:.1f} m, "
                 f"members={', '.join(_ff_audit['well'])}")
    rpt.add("FarField_contrast_vs_impact", _r0['contrast_vs_impact_m'],
            unit="m", well="FarField",
            note=f"impact zone at {_r0['impact_dist_m']:.1f} m; the "
                 f"distance contrast the Script 25 BACI corroboration is "
                 f"tested on")
    rpt.add("FarField_admission_threshold", _r0['admission_threshold_m'],
            unit="m", well="FarField",
            note=f"FAR_FIELD_REACH_MULTIPLE x fitted reach "
                 f"{_r0['reach_L_m']:.1f} m (source: {_r0['reach_source']})")

# Per-control-well spread — the range each tier's members give when used
# singly, emitted so no tier estimate is quoted without it.
_spread_groups = ([] if spread_df.empty
                  else list(spread_df.groupby(['Control', 'Zone'])))
for (_c, _z), _g in _spread_groups:
    _row = _g.iloc[0]
    rpt.add(f"Spread_{_c}_{_z}_step_range",
            _row['Spread_step_max_m'] - _row['Spread_step_min_m'],
            well=_z,
            note=f"single-control-well refits: "
                 f"[{_row['Spread_step_min_m']:.4f}, "
                 f"{_row['Spread_step_max_m']:.4f}] m over "
                 f"{int(_row['N_control_wells'])} wells; "
                 f"tier step {_row['Tier_clearfell_step_m']:.4f} m")

# Scraping distance weights for network wells
print("   Scraping distance weights:")
for w in ALL_NETWORK_WELLS:
    if w in well_locations:
        loc = well_locations[w]
        d = distance_from_ceh36(loc['easting'], loc['northing'])
        wt = scraping_weight(d)
        rpt.add("Scraping_distance_weight", wt, unit="",
                well=w.upper(), note=f"d={d:.0f}m, λ={SCRAPING_DECAY_LAMBDA:.0f}m")
        print(f"     {w.upper():<8}  d = {d:6.0f} m   weight = {wt:.3f}")

n_saved = rpt.save(OUT_REPORT)
saved(f"{OUT_REPORT.name} ({n_saved} rows)")

# ============================================================================
# CONSOLE SUMMARY
# ============================================================================
print("\n" + "=" * 72)
print("ANCOVA-BACI SUMMARY")
print("=" * 72)

for zone_label in ZONES.keys():
    print(f"\n  {zone_label} zone:")
    print(f"  {'Control':<12} {'Step (mm)':>10} {'CI':>20} {'p':>10} {'R²':>6}")
    print(f"  {'-'*60}")
    for ctrl_label in CONTROLS.keys():
        key = (ctrl_label, zone_label)
        if key in results:
            fit = results[key]
            step_mm = fit['clearfell_step'] * 1000
            ci_mm = (fit['clearfell_ci'][0] * 1000, fit['clearfell_ci'][1] * 1000)
            print(f"  {ctrl_label:<12} {step_mm:>+10.0f} "
                  f"[{ci_mm[0]:>+7.0f}, {ci_mm[1]:>+7.0f}] "
                  f"{format_p(fit['clearfell_p']):>10} "
                  f"{fit['r2']:>6.3f}")

print(f"\n  Scraping decay λ = {SCRAPING_DECAY_LAMBDA:.0f} m")
print("=" * 72)
print("Script 10a complete.\n")
