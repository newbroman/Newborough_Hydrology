"""
====================================================================================
08_model_benchmarking.py — Model Benchmarking (SSM vs Traditional)
====================================================================================
Purpose:
    Runs dual-panel model showdown plots and exports full-well performance metrics.

    Top panel:
        Diagnostic Fit (One-Step) with R².
    Bottom panel:
        Forecasting Stability (Iterative) with NSE, RMSE, and R².

    Model formulations:
        Traditional (TLM):
            Δh(t) = α + β₁·P(t) − β₂·PET(t)
        State-Space (SSM, Model B since 2.0.0 / D-332, displacement formulation):
            Δh(t) = α + β₁·P(t) − β₂·PET(t) − β₃·h_disp_prev(t)
            where h_disp = DRAINAGE_DATUM + h_depth
        Tested alternatives on the same rows: Model A (α = 0, DRAINAGE_DATUM) and
        the MHW form (α = 0, datum = the well's depth to mean high water).

    Both models use HEADLINE_LAG from config (= 0 after bucketing fix).

    Outputs:
        - One-row-per-well metrics table for all wells in cleaned data.
        - Map 1: Iterative R² Improvement (Deep Storage vs Constrained Buckets).
        - Map 2: Iterative NSE Improvement (Water Balance Residuals & Anomalies).
====================================================================================
"""

# Revision note:
#   2026-06-21 — Benchmarking maps now call add_kml_features(..., include_scrapes=False).
#     The shared feature overlay draws the GPS-traced scrape footprints by default;
#     here they clutter the well markers, so they are suppressed. Figures only;
#     model formulations and metrics unchanged.

__version__ = "2.0.0"  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b). The headline SSM is Model B: every
#   *_StateSpace column (one-step and iterative R2/NSE/RMSE, betas, p-values, R2_StateSpace_fit; new Alpha_StateSpace)
#   and every *_SSM / dNSE report number (benchmark_{median,positive,negative}_NSE_SSM, benchmark_median_dNSE,
#   benchmark_wells_SSM_worse, C*_median_SSM_NSE, C*_positive_SSM_NSE, C*_median_dNSE, dNSE_vs_beta*) now carries
#   Model B, free-run and one-step with its alpha. Model A moves to *_model_a: per-well *_StateSpace_model_a /
#   *_Improvement_model_a, 08_perwell_nse SSM_NSE_model_a / dNSE_model_a, cluster medians median_SSM_NSE_model_a /
#   median_dNSE_model_a / positive_SSM_NSE_model_a, keys benchmark_{median,positive,negative}_NSE_SSM_model_a,
#   benchmark_median_dNSE_model_a, benchmark_wells_SSM_worse_model_a, C*_{median,positive}_SSM_NSE_model_a,
#   C*_median_dNSE_model_a, dNSE_vs_beta{2,3}_{r,p}_model_a. The 1.7.0 *_ModelB columns and keys are kept and equal the SSM ones. Table 5 (08_lcsc_04)
#   columns are now TLM, SSM_Model_B, Model_A, MHW, Delta_SSM_minus_TLM (was Traditional_Model_A,
#   StateSpace_Model_B, Delta_B_minus_A, an older naming in which "Model B" was today's Model A). Figures 08_lcsc_01-03
#   show Model B; the showdown legends sit outside the axes.
# 1.9.0  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2a). The benchmark gains the MHW form:
#   Model A at each well's depth to mean high water (ground_elev_m, Script 01, less tide_mhw_m, Script 01b; Script
#   48's form M), fitted on the same window rows as the other three and free-run at that datum. Per well:
#   Iterative_NSE_MHW, Iterative_NSE_Improvement_MHW, Datum_MHW_m, Beta_3_MHW, pvalue_beta_3_MHW (08_perwell_nse
#   gains MHW_NSE, dNSE_MHW, Datum_MHW_m); cluster medians gain median_MHW_NSE / positive_MHW_NSE; report numbers
#   benchmark_{median,positive}_NSE_MHW, benchmark_median_dNSE_MHW, benchmark_n_wells_MHW, C*_{median,positive}_MHW_NSE.
#   Model B's beta_3 is now bounded below (model_utils 1.14.0): Beta_3_bound_binds_ModelB per well and
#   benchmark_n_beta3_bound_ModelB. The "CSV 2" comment that called Model A "Model B" is corrected. Additive:
#   no existing column or key is renamed; Model B values move only where the bound binds.
# 1.8.0  # Hollingham (2026) — 2026-10-28 (D-288; Martin 04:47). A well is kept with at least
#   BENCHMARK_MIN_WINDOW_MONTHS fitted months in the comparison window, not exactly LCSC_DATA_LIMIT: since D-281 the
#   window is a fixed calendar span and the exact-count test dropped every well with a gap or dry month (66 -> 48).
#   The TLM, Model A and Model B are still fitted on the same rows; Months_Used records the count.
# 1.7.0  # Hollingham (2026) — 2026-10-08 (D-244). The benchmark gains Model B, the
#   free-intercept form (model_utils.fit_ssm(intercept=True)), fitted on the same 100-month window and
#   free-run with the shared recurrence (simulate_ssm alpha=). The TLM is Model B with beta_3 = 0, so
#   TLM -> Model B isolates the drainage term, where TLM -> Model A also swaps a free constant for the
#   datum-fixed -beta_3*z0. Per well: Iterative_NSE_ModelB, Iterative_NSE_Improvement_ModelB,
#   Alpha_ModelB, Beta_3_ModelB, pvalue_beta_3_ModelB. 08_nse_cluster_medians.csv gains the median
#   iterative NSE and positive-NSE count under each of TLM, Model A and Model B; report numbers
#   benchmark_*_ModelB and C*_median_{TLM,SSM,ModelB}_NSE, C*_positive_{TLM,SSM,ModelB}_NSE.
#   Additive: no existing column or key changes (Martin: "Approved, build it").
# 1.6.0  # Hollingham (2026) — 2026-09-29. T-96: emits
#   benchmark_negative_NSE_SSM and benchmark_negative_NSE_TLM, the counts of wells
#   with a negative iterative NSE under each model (report12 §7, Conclusions),
#   from the per-well frame already built. Additive; no existing output changes.
# 1.5.1  # Hollingham (2026) — 2026-09-03. Comment-only: the CEH6
#   showcase comment carried stale literals (-1.15/+0.63/+1.78) and wrongly called it
#   the largest on-site NSE improvement; corrected to the committed -1.885/+0.674/+2.559
#   (CEH27 is largest at +2.865). No behaviour, output or figure change.
# v1.5.0  # Hollingham (2026) — 2026-08-18. Two changes to
#   08_lcsc_04_table3_benchmark_summary.csv (report Table 5), both authorised
#   by Martin 2026-08-18.
#   (a) Store-time rounding removed. The six summary rows were written through
#       round(x, 2), so the store carried a display decision and the one-step
#       R2 delta persisted as "0.0" when the value is 0.0032. Per D-035 the
#       store now carries what the pipeline computed; rounding happens where
#       the number is rendered (values 3 dp, deltas 4 dp in the report).
#   (b) A generated "CEH14 iterative NSE" row added beside the CEH6 row. The
#       report has carried a CEH14 line in Table 5 for some time, typed rather
#       than emitted, and it had drifted to -3.21 against a live -6.42. It is
#       now produced from 08_lcsc_model_stats.csv like every other row.
#   No change to any figure, to per-well outputs, or to the report-number keys
#   added in 1.4.3.
#
# v1.4.3  # Hollingham (2026) — 2026-08-16. Exports the SSM fit
#   columns that v1.4.0 computed: model_stats_df selects a fixed column list, so
#   the coefficients and p-values were built onto each row and then dropped
#   before the file was written. The metrics are unaffected - the acceptance
#   diff against the previous committed CSV is 0.000e+00 on every shared column,
#   66 wells - but the stated purpose (a benchmark SSM diffable against
#   03_master_data.csv) needed the columns to actually be in the file.
#
# v1.4.1  # Hollingham (2026) — 2026-08-16. Hotfix: the new
#   R2_StateSpace_fit column read ssm['r_squared']; the key fit_ssm returns is
#   'R2'. Raised KeyError at the first well. The v1.4.0 acceptance test compared
#   the two fitting paths' coefficients and did not execute the row-building
#   code around them, so it proved the numerical claim and missed the typo.
#
# v1.4.0  # Hollingham (2026) — 2026-08-16. The benchmark's SSM
#   is now fitted by model_utils.fit_ssm() instead of a local sm.OLS on a
#   hand-assembled design matrix. Arithmetically the same fit on today's
#   settings - the acceptance test is that every metric reproduces
#   byte-identically - but the script no longer carries a second copy of the
#   specification, and the fitted coefficients and their p-values are now
#   emitted so they can be diffed against 03_master_data.csv. Prerequisite for
#   any change to the fitting window (D-033 step zero).
#
# v1.3.0  # Hollingham (2026) — 2026-08-16. LCSC_DATA_LIMIT is
#   imported from config.py rather than declared module-locally; value unchanged
#   at 100, no change to any fit, metric or figure. See D-016.
#
# v1.2.0  # Hollingham (2026) — 2026-06-21
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    INT_WELLS_CLEAN,
    INT_WELLS_REFERENCE,
    INT_CLIMATE,
    INT_MASTER_DATA,
    INT_CLUSTER_STATS,
    INT_LCSC_MODEL_STATS,
    OUT_08_SHOWDOWN,
    OUT_08_R2_MAP,
    OUT_08_NSE_MAP,
    OUT_08_TABLE3_SUMMARY,
    OUT_08_PERWELL_NSE,
    OUT_08_CLUSTER_NSE_MEDIANS,
    OUT_08_REPORT_NUMBERS,
    INT_WELL_ELEVATIONS,
    OUT_01B_REPORT_NUMBERS,
)
from utils.data_utils import normalize_well_name
from utils.report_numbers_utils import ReportNumbers
from utils.model_utils import (get_metrics, get_r2, build_ssm_frame, simulate_ssm,
                              fit_ssm)
from utils.map_utils import add_kml_features, load_dem_layer, add_en_axes
from utils.config import (
    CLUSTER_LABELS, CLUSTER_MARKERS, DRAINAGE_DATUM, HEADLINE_LAG, BW_MODE,
    LCSC_DATA_LIMIT, BENCHMARK_MIN_WINDOW_MONTHS,
)
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from scipy import stats as _spstats
import statsmodels.api as sm

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import render_figure

# ==========================================
# CONFIGURATION & PATHS
# ==========================================

WELLS_PATH = INT_WELLS_CLEAN
REFERENCE_NETWORK_PATH = INT_WELLS_REFERENCE
CLIMATE_PATH = INT_CLIMATE
MASTER_PATH = INT_MASTER_DATA

# LCSC_DATA_LIMIT is imported from config.py — this script is the equal-window
# SSM-vs-TLM comparison, so the window is load-bearing here: both models are
# refitted on the same capped frame and a well is only benchmarked if it fills
# the window. See the config.py comment for the policy.
EXCLUDED_WELLS_NORM = {'ceh7', 'ceh8', 'ceh37'}

# HEADLINE_LAG imported from config.py (= 0 after bucketing fix).

# ==========================================
# AESTHETICS & PUBLICATION SETTINGS
# ==========================================
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


def mhw_datums() -> dict:
    """1.9.0 (D-332): each well's depth from ground to mean high water (m), the datum of the MHW form:
    ground_elev_m (Script 01) less tide_mhw_m (Script 01b), as Script 48's form M takes it."""
    if not (OUT_01B_REPORT_NUMBERS.exists() and INT_WELL_ELEVATIONS.exists()):
        warn("01b report numbers or 01 well elevations absent - the MHW form is skipped")
        return {}
    rn = pd.read_csv(OUT_01B_REPORT_NUMBERS)
    v = rn.loc[rn["Parameter"] == "tide_mhw_m", "Value"]
    if not len(v):
        warn("tide_mhw_m not in 01b's report numbers - the MHW form is skipped")
        return {}
    mhw = float(v.iloc[0])
    el = pd.read_csv(INT_WELL_ELEVATIONS)
    g = pd.to_numeric(el["ground_elev_m"], errors="coerce")
    return {normalize_well_name(str(n)): float(x) - mhw for n, x in zip(el["Name"], g) if np.isfinite(x)}


def compute_showdown_metrics(target_well_name, df_clean, df_climate, mhw_datum=None):
    """Compute one-step and iterative showdown metrics for a single well.

    Uses the displacement formulation (h_disp = DRAINAGE_DATUM + h_depth)
    for the SSM drainage predictor and HEADLINE_LAG rainfall (= 0 currently),
    matching Script 03. 2.0.0 (D-332): the SSM is Model B (free intercept alpha,
    carried into the one-step and free-run series); Model A is fitted beside it.

    1.9.0 (D-332): with `mhw_datum` (the well's depth to mean high water, m), Model A is also fitted
    and free-run at that datum on the same window rows (the MHW form).
    """
    target_norm = normalize_well_name(target_well_name)

    target_col = next(
        (c for c in df_clean.columns if normalize_well_name(c) == target_norm),
        None,
    )

    base_row = {
        'Well': target_norm.upper(),
        'Well_Normalized': target_norm,
        'Source_Column': str(target_col) if target_col is not None else np.nan,
        'Status': 'ok',
        'Months_Used': np.nan,
        'OneStep_R2_Traditional': np.nan,
        'OneStep_R2_StateSpace': np.nan,
        'OneStep_R2_Improvement': np.nan,
        'Iterative_NSE_Traditional': np.nan,
        'Iterative_NSE_StateSpace': np.nan,
        'Iterative_NSE_Improvement': np.nan,
        'Iterative_RMSE_Traditional': np.nan,
        'Iterative_RMSE_StateSpace': np.nan,
        'Iterative_RMSE_Improvement': np.nan,
        'Iterative_R2_Traditional': np.nan,
        'Iterative_R2_StateSpace': np.nan,
        'Iterative_R2_Improvement': np.nan,
        'Beta_P_Traditional': np.nan,
        'Beta_PET_Traditional': np.nan,
        'Intercept_Traditional': np.nan,
        'Beta_P_StateSpace': np.nan,
        'Beta_PET_StateSpace': np.nan,
        'Beta_hdisp_StateSpace': np.nan,
        'Iterative_NSE_ModelB': np.nan,
        'Iterative_NSE_Improvement_ModelB': np.nan,
        'Alpha_ModelB': np.nan,
        'Beta_3_ModelB': np.nan,
        'pvalue_beta_3_ModelB': np.nan,
        'Beta_3_bound_binds_ModelB': np.nan,
        'Iterative_NSE_MHW': np.nan,
        'Iterative_NSE_Improvement_MHW': np.nan,
        'Datum_MHW_m': np.nan,
        'Beta_3_MHW': np.nan,
        'pvalue_beta_3_MHW': np.nan,
        'OneStep_R2_MHW': np.nan,                 # 2.0.0 (D-332): for Table 5's MHW column
        'Iterative_R2_MHW': np.nan,
        'Alpha_StateSpace': np.nan,               # 2.0.0: the headline SSM is Model B
        'OneStep_R2_StateSpace_model_a': np.nan,  # 2.0.0: Model A, the tested alternative
        'OneStep_R2_Improvement_model_a': np.nan,
        'Iterative_NSE_StateSpace_model_a': np.nan,
        'Iterative_NSE_Improvement_model_a': np.nan,
        'Iterative_RMSE_StateSpace_model_a': np.nan,
        'Iterative_R2_StateSpace_model_a': np.nan,
        'Iterative_R2_Improvement_model_a': np.nan,
        'Beta_P_StateSpace_model_a': np.nan,
        'Beta_PET_StateSpace_model_a': np.nan,
        'Beta_hdisp_StateSpace_model_a': np.nan,
        'pvalue_beta_3_StateSpace_model_a': np.nan,
        'R2_StateSpace_fit_model_a': np.nan,
    }

    if target_col is None:
        base_row['Status'] = 'missing_column'
        return base_row, None

    well_series = pd.to_numeric(df_clean[target_col], errors='coerce')
    well_series.index = pd.to_datetime(well_series.index).to_period('M')

    climate = df_climate.copy()
    climate.index = pd.to_datetime(climate.index).to_period('M')

    # Use shared build_ssm_frame for alignment, lag, displacement
    df = build_ssm_frame(well_series, climate, window=LCSC_DATA_LIMIT)

    # 1.8.0 (D-288): the window is a fixed calendar span since D-281, so a gap or dry month leaves fewer rows;
    # keep the well with at least BENCHMARK_MIN_WINDOW_MONTHS of them (all three forms fit the same rows).
    if len(df) < BENCHMARK_MIN_WINDOW_MONTHS:
        base_row['Status'] = 'insufficient_data'
        base_row['Months_Used'] = len(df)
        return base_row, None

    # Traditional model: Δh = α + β₁·P(t-lag) - β₂·PET(t). The TLM is this
    # script's own comparator and has no counterpart in model_utils, so it is
    # fitted here.
    x_trad = sm.add_constant(pd.DataFrame({'P': df['P'], 'PET': -df['PET']}), has_constant='add')
    y_fit = df['Delta_h']
    model_trad = sm.OLS(y_fit, x_trad).fit()

    # State-space model: the CANONICAL fitter, not a local copy (v1.4.0). The frame is already built (and
    # windowed) above, so pre_built_frame is passed through and fit_ssm does no realignment of its own.
    # 2.0.0 (D-332, J-9 phase 2b): the headline SSM is Model B, the free-intercept form
    # (fit_ssm(intercept=True)), free-run with its alpha; every *_StateSpace column and *_SSM key carries it.
    # Model A (no intercept, DRAINAGE_DATUM) is kept beside it as the tested alternative, in *_model_a
    # columns; the MHW form (1.9.0) is Model A at each well's depth to mean high water.
    p_arr = df['P'].values
    pet_arr = df['PET'].values
    h_obs = df['h'].values

    def _run(fit, datum, alpha):
        """One-step (observed h_prev) and iterative (free-run) series for one SSM form, and their scores."""
        b1, b2, b3 = (float(fit['beta_1_recharge']), float(fit['beta_2_atmospheric_draw']),
                      float(fit['beta_3_drainage']))
        one = np.full(len(h_obs), np.nan)
        one[0] = h_obs[0]
        for t in range(1, len(h_obs)):
            one[t] = h_obs[t - 1] + alpha + b1 * p_arr[t] - b2 * pet_arr[t] - b3 * (datum + h_obs[t - 1])
        it = np.concatenate([[h_obs[0]], simulate_ssm(
            h0=h_obs[0], P=p_arr[1:], PET=pet_arr[1:], b1=b1, b2=b2, b3=b3,
            drainage_datum=datum, alpha=alpha)])
        nse, rmse, _ = get_metrics(h_obs, it)
        return {'one': one, 'iter': it, 'r2_one': get_r2(h_obs, one), 'nse': nse, 'rmse': rmse,
                'r2_iter': get_r2(h_obs, it), 'b1': b1, 'b2': b2, 'b3': b3}

    ssm = fit_ssm(pre_built_frame=df, intercept=True)          # Model B: the headline SSM
    if ssm is None:
        base_row['Status'] = 'ssm_fit_failed'
        base_row['Months_Used'] = len(df)
        return base_row, None
    alpha_b = float(ssm['alpha'])
    rb = _run(ssm, DRAINAGE_DATUM, alpha_b)

    ssm_a = fit_ssm(pre_built_frame=df)                          # Model A at DRAINAGE_DATUM (alternative)
    ra = _run(ssm_a, DRAINAGE_DATUM, 0.0) if ssm_a is not None else None

    # The MHW form - Model A with each well's depth to mean high water as its datum, on the same window
    # rows (the datum moves h_disp only, never which months are in the frame).
    rm, ssm_m = None, None
    if mhw_datum is not None and np.isfinite(mhw_datum):
        df_m = build_ssm_frame(well_series, climate, window=LCSC_DATA_LIMIT, drainage_datum=float(mhw_datum))
        if not df_m.index.equals(df.index):
            raise ValueError(f"{target_norm}: the MHW frame's rows differ from the benchmark window's")
        ssm_m = fit_ssm(pre_built_frame=df_m)
        if ssm_m is not None:
            rm = _run(ssm_m, float(mhw_datum), 0.0)

    # ---- TLM: one-step and iterative (no h_prev feedback, just accumulates dh from climate) ----
    def _dh_trad(t):
        return (model_trad.params['const'] + model_trad.params['P'] * p_arr[t]
                - model_trad.params['PET'] * pet_arr[t])
    h_trad_one = np.full(len(h_obs), np.nan)
    h_trad_iter = np.full(len(h_obs), np.nan)
    h_trad_one[0] = h_trad_iter[0] = h_obs[0]
    for t in range(1, len(h_obs)):
        h_trad_one[t] = h_obs[t - 1] + _dh_trad(t)
        h_trad_iter[t] = h_trad_iter[t - 1] + _dh_trad(t)
    r2_trad_one = get_r2(h_obs, h_trad_one)
    nse_trad, rmse_trad, _ = get_metrics(h_obs, h_trad_iter)
    r2_trad_iter = get_r2(h_obs, h_trad_iter)

    def _g(r, k):
        return r[k] if r is not None else np.nan

    base_row.update({
        'Months_Used': len(df),
        'OneStep_R2_Traditional': r2_trad_one,
        'OneStep_R2_StateSpace': rb['r2_one'],
        'OneStep_R2_Improvement': rb['r2_one'] - r2_trad_one,
        'Iterative_NSE_Traditional': nse_trad,
        'Iterative_NSE_StateSpace': rb['nse'],
        'Iterative_NSE_Improvement': rb['nse'] - nse_trad,
        'Iterative_RMSE_Traditional': rmse_trad,
        'Iterative_RMSE_StateSpace': rb['rmse'],
        'Iterative_RMSE_Improvement': rmse_trad - rb['rmse'],
        'Iterative_R2_Traditional': r2_trad_iter,
        'Iterative_R2_StateSpace': rb['r2_iter'],
        'Iterative_R2_Improvement': rb['r2_iter'] - r2_trad_iter,
        'Beta_P_Traditional': model_trad.params['P'],
        'Beta_PET_Traditional': model_trad.params['PET'],
        'Intercept_Traditional': model_trad.params['const'],
        'Beta_P_StateSpace': rb['b1'],
        'Beta_PET_StateSpace': rb['b2'],
        'Beta_hdisp_StateSpace': rb['b3'],
        # Emitted so the benchmark's SSM is checkable against 03_master_data.csv
        # rather than merely assumed to agree with it (D-033 step zero).
        'pvalue_beta_1_StateSpace': float(ssm['pvalue_beta_1']),
        'pvalue_beta_2_StateSpace': float(ssm['pvalue_beta_2']),
        'pvalue_beta_3_StateSpace': float(ssm['pvalue_beta_3']),
        'R2_StateSpace_fit': float(ssm['R2']),
        'Alpha_StateSpace': alpha_b,
        # 1.7.0 (D-244) Model B columns: since 2.0.0 the same fit as *_StateSpace, kept under their own names
        'Iterative_NSE_ModelB': rb['nse'],
        'Iterative_NSE_Improvement_ModelB': rb['nse'] - nse_trad,
        'Alpha_ModelB': alpha_b,
        'Beta_3_ModelB': rb['b3'],
        'pvalue_beta_3_ModelB': float(ssm['pvalue_beta_3']),
        # 1.9.0 (D-332): model_utils 1.14.0 holds Model B's beta_3 at MODEL_B_BETA3_MIN where it would fall below
        'Beta_3_bound_binds_ModelB': bool(ssm.get('beta_3_bound_binds', False)),
        # 2.0.0 (D-332): Model A, the tested alternative (until 2.0.0 these were the *_StateSpace columns)
        'OneStep_R2_StateSpace_model_a': _g(ra, 'r2_one'),
        'OneStep_R2_Improvement_model_a': _g(ra, 'r2_one') - r2_trad_one,
        'Iterative_NSE_StateSpace_model_a': _g(ra, 'nse'),
        'Iterative_NSE_Improvement_model_a': _g(ra, 'nse') - nse_trad,
        'Iterative_RMSE_StateSpace_model_a': _g(ra, 'rmse'),
        'Iterative_R2_StateSpace_model_a': _g(ra, 'r2_iter'),
        'Iterative_R2_Improvement_model_a': _g(ra, 'r2_iter') - r2_trad_iter,
        'Beta_P_StateSpace_model_a': _g(ra, 'b1'),
        'Beta_PET_StateSpace_model_a': _g(ra, 'b2'),
        'Beta_hdisp_StateSpace_model_a': _g(ra, 'b3'),
        'pvalue_beta_3_StateSpace_model_a': float(ssm_a['pvalue_beta_3']) if ssm_a is not None else np.nan,
        'R2_StateSpace_fit_model_a': float(ssm_a['R2']) if ssm_a is not None else np.nan,
        'Iterative_NSE_MHW': _g(rm, 'nse'),
        'Iterative_NSE_Improvement_MHW': _g(rm, 'nse') - nse_trad,
        'OneStep_R2_MHW': _g(rm, 'r2_one'),
        'Iterative_R2_MHW': _g(rm, 'r2_iter'),
        'Datum_MHW_m': float(mhw_datum) if (mhw_datum is not None and np.isfinite(mhw_datum)) else np.nan,
        'Beta_3_MHW': float(ssm_m['beta_3_drainage']) if ssm_m is not None else np.nan,
        'pvalue_beta_3_MHW': float(ssm_m['pvalue_beta_3']) if ssm_m is not None else np.nan,
    })

    h_lcsc_one, h_lcsc_iter = rb['one'], rb['iter']
    r2_lcsc_one, nse_lcsc, rmse_lcsc, r2_lcsc_iter = rb['r2_one'], rb['nse'], rb['rmse'], rb['r2_iter']

    payload = {
        'index': df.index.to_timestamp(),
        'h_obs': h_obs,
        'h_trad_one': h_trad_one,
        'h_lcsc_one': h_lcsc_one,
        'h_trad_iter': h_trad_iter,
        'h_lcsc_iter': h_lcsc_iter,
        'r2_trad_one': r2_trad_one,
        'r2_lcsc_one': r2_lcsc_one,
        'nse_trad': nse_trad,
        'nse_lcsc': nse_lcsc,
        'rmse_trad': rmse_trad,
        'rmse_lcsc': rmse_lcsc,
        'r2_trad_iter': r2_trad_iter,
        'r2_lcsc_iter': r2_lcsc_iter,
        'well_label': target_norm.upper(),
    }
    return base_row, payload


def plot_showdown(output_path, payload):
    """Dual-panel TLM vs SSM (Model B since 2.0.0) showdown for a target well."""
    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(14, 10), dpi=300, sharex=True)
    well_label = payload.get('well_label', 'TARGET')

    # Top Panel: Diagnostic Fit (One-Step)
    ax_top.plot(payload['index'], payload['h_obs'], color='black', lw=2.8, label='Observed')
    ax_top.plot(payload['index'], payload['h_trad_one'], color='#D55E00', lw=2.2, ls=':', label=f"TLM (R\u00b2={payload['r2_trad_one']:.3f})")
    ax_top.plot(payload['index'], payload['h_lcsc_one'], color='#0072B2', lw=2.2, ls='--', label=f"SSM, Model B (R\u00b2={payload['r2_lcsc_one']:.3f})")
    ax_top.set_title(f'{well_label}: Diagnostic Fit (One-Step)', fontweight='bold')
    ax_top.set_ylabel('Water Depth (m below surface)')
    ax_top.grid(True, ls='--', alpha=0.5)
    ax_top.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), frameon=True, edgecolor='black')  # off the data (2.0.0)

    # Bottom Panel: Forecasting Stability (Iterative)
    ax_bottom.plot(payload['index'], payload['h_obs'], color='black', lw=2.8, label='Observed')
    ax_bottom.plot(
        payload['index'],
        payload['h_trad_iter'],
        color='#D55E00',
        lw=2.2,
        ls=':',
        label=(
            f"TLM (NSE={payload['nse_trad']:.3f}, "
            f"RMSE={payload['rmse_trad']:.3f}, R²={payload['r2_trad_iter']:.3f})"
        ),
    )
    ax_bottom.plot(
        payload['index'],
        payload['h_lcsc_iter'],
        color='#0072B2',
        lw=2.2,
        ls='--',
        label=(
            f"SSM, Model B (NSE={payload['nse_lcsc']:.3f}, "
            f"RMSE={payload['rmse_lcsc']:.3f}, R²={payload['r2_lcsc_iter']:.3f})"
        ),
    )
    ax_bottom.set_title(f'{well_label}: Forecasting Stability (Iterative)', fontweight='bold')
    ax_bottom.set_xlabel('Date')
    ax_bottom.set_ylabel('Water Depth (m below surface)')
    ax_bottom.grid(True, ls='--', alpha=0.5)
    ax_bottom.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), frameon=True, edgecolor='black')  # off the data (2.0.0)
    ax_bottom.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    plt.tight_layout()
    render_figure(plt.gcf(), output_path)
    plt.close()


def plot_metric_map(map_df, value_col, title, output_path, cmap, vmin=None, vmax=None):
    """Create easting/northing scatter map for a metric, using marker shape for cluster."""
    # BW mode: override colourmap to linear greyscale
    if BW_MODE:
        cmap = "Greys"
    map_df = map_df.copy()
    required_cols = ['Easting', 'Northing', value_col]
    missing_required = [c for c in required_cols if c not in map_df.columns]
    if missing_required:
        warn(f"Missing required columns for map: {missing_required}. Skipping {output_path.name}")
        return

    # Fallback: keep plotting with a single default marker when cluster ids are unavailable.
    if 'Cluster_ID' not in map_df.columns:
        map_df['Cluster_ID'] = 1

    valid = map_df.dropna(subset=['Easting', 'Northing', value_col]).copy()
    if 'Cluster_ID' not in valid.columns:
        valid['Cluster_ID'] = 1
    valid['Cluster_ID'] = pd.to_numeric(valid['Cluster_ID'], errors='coerce').fillna(1).astype(int)
    if valid.empty:
        warn(f"No mappable data for {value_col}. Skipping {output_path.name}")
        return

    import geopandas as gpd
    import contextily as ctx
    import matplotlib.colors as mcolors
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from pathlib import Path

    def _safe_read_kml(path_obj):
        try:
            return gpd.read_file(str(path_obj), driver="KML")
        except Exception as exc:
            warn(f"Skipping {Path(path_obj).name}: KML unavailable ({exc})")
            return None

    dem_layer = None
    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)

    # --- DEM Layer ---
    dem_layer, dem_loaded = load_dem_layer(ax, DATA_DIR)

    # --- Fallback to OSM ---
    if not dem_loaded:
        gdf_tmp = gpd.GeoDataFrame(valid, geometry=gpd.points_from_xy(valid.Easting, valid.Northing), crs="EPSG:27700")
        ctx.add_basemap(ax, crs=gdf_tmp.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik, zorder=1, alpha=0.7)

    # --- KML Features (via map_utils — includes broadleaf restock block) ---
    site_feature_handles = add_kml_features(ax, DATA_DIR, include_scrapes=False)

    # --- Plot Wells by Cluster Shape ---
    handles = []
    # For NSE metrics, prefer robust scaling so low-end improvements remain visible
    # even when a few high outliers stretch the full range.
    if 'nse' in value_col.lower() or 'penalty' in value_col.lower():
        # Clip improvement columns to ±1.5 before scaling: CEH3 sits at -8.16 and
        # would otherwise collapse the diverging scale. Raw values are preserved in
        # the CSV output.
        NSE_IMPROVEMENT_CLIP = 1.5
        if 'improvement' in value_col.lower():
            valid = valid.copy()
            valid[value_col] = pd.to_numeric(valid[value_col], errors='coerce').clip(
                -NSE_IMPROVEMENT_CLIP, NSE_IMPROVEMENT_CLIP
            )
        vals = pd.to_numeric(valid[value_col], errors='coerce').dropna().to_numpy(dtype=float)
        if vals.size == 0:
            scatter_kwargs = {'cmap': cmap, 'vmin': vmin, 'vmax': vmax, 'norm': None}
        else:
            data_min = float(np.nanmin(vals))
            data_max = float(np.nanmax(vals))

            if data_min < 0 < data_max:
                # Signed metrics crossing zero
                if BW_MODE:
                    # BW: 3 clear bands
                    div_edges = np.linspace(data_min, data_max, 4)
                    div_colors = ["#d0d0d0", "#808080", "#2a2a2a"]
                    cmap_obj = mcolors.ListedColormap(div_colors)
                    norm = mcolors.BoundaryNorm(div_edges, cmap_obj.N, clip=True)
                    scatter_kwargs = {'cmap': cmap_obj, 'vmin': None, 'vmax': None, 'norm': norm}
                else:
                    norm = mcolors.TwoSlopeNorm(vmin=data_min, vcenter=0.0, vmax=data_max)
                    scatter_kwargs = {'cmap': 'RdYlBu', 'vmin': None, 'vmax': None, 'norm': norm}
            else:
                if BW_MODE:
                    # BW mode: 3 clear bands
                    _lo = float(np.nanmin(vals)) if vmin is None else float(vmin)
                    _hi = float(np.nanmax(vals)) if vmax is None else float(vmax)
                    _hi = max(_hi, 0.2)
                    bw_edges = np.linspace(_lo, _hi, 4)
                    bw_colors = ["#d0d0d0", "#808080", "#2a2a2a"]
                    cmap_obj = mcolors.ListedColormap(bw_colors)
                    norm = mcolors.BoundaryNorm(bw_edges, cmap_obj.N, clip=True)
                    scatter_kwargs = {'cmap': cmap_obj, 'vmin': None, 'vmax': None, 'norm': norm}
                else:
                    # Positive-only (or negative-only) metrics: use discrete bins so
                    # 0.2+ is visually distinct from near-zero values.
                    lo = 0.0
                    hi = float(np.nanmax(vals))
                    if not np.isfinite(lo):
                        lo = data_min
                    if not np.isfinite(hi):
                        hi = data_max
                    hi = max(hi, 0.2)
                    if hi <= lo:
                        lo, hi = data_min, data_max
                    if hi <= lo:
                        hi = lo + 1e-6

                    unique_vals = np.unique(np.sort(vals))
                    if unique_vals.size > 1:
                        # Put only the very highest well(s) in the top class.
                        top_split = max(0.75, float(unique_vals[-2]) + 1e-6)
                    else:
                        top_split = max(0.75, hi - 1e-6)
                    if top_split >= hi:
                        top_split = max(0.75, hi - 1e-6)

                    # Explicit class breaks: orange starts at 0.75; top class is unique.
                    base_edges = np.array([0.00, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, top_split, hi], dtype=float)
                    edges = np.unique(np.clip(base_edges, lo, hi))
                    if edges.size < 2 or edges[-1] <= edges[0]:
                        edges = np.array([lo, hi], dtype=float)

                    # Stronger discrete palette with dedicated top-end class color.
                    colors = []
                    for i in range(len(edges) - 1):
                        start = edges[i]
                        if start >= top_split - 1e-12:
                            colors.append("#ffffff")  # top class (single highest well)
                        elif start >= 0.75 - 1e-12:
                            colors.append("#f16913")  # orange class starts at 0.75
                        elif start >= 0.50 - 1e-12:
                            colors.append("#d94801")
                        elif start >= 0.35 - 1e-12:
                            colors.append("#fe9929")
                        elif start >= 0.20 - 1e-12:
                            colors.append("#fec44f")
                        elif start >= 0.10 - 1e-12:
                            colors.append("#fee391")
                        else:
                            colors.append("#fff7bc")

                    cmap_obj = mcolors.ListedColormap(colors)
                    norm = mcolors.BoundaryNorm(edges, cmap_obj.N, clip=True)
                scatter_kwargs = {'cmap': cmap_obj, 'vmin': None, 'vmax': None, 'norm': norm}
    else:
        scatter_kwargs = {'cmap': cmap, 'vmin': vmin, 'vmax': vmax, 'norm': None}

    for cluster_id in sorted(valid['Cluster_ID'].dropna().unique()):
        marker = CLUSTER_MARKERS.get(int(cluster_id), 'o')
        cluster_points = valid[valid['Cluster_ID'] == cluster_id]
        sc = ax.scatter(
            cluster_points['Easting'],
            cluster_points['Northing'],
            c=cluster_points[value_col],
            cmap=scatter_kwargs['cmap'],
            s=120,
            marker=marker,
            edgecolor='black',
            linewidth=0.6,
            alpha=0.9,
            norm=scatter_kwargs.get('norm', None),
            vmin=scatter_kwargs.get('vmin', None),
            vmax=scatter_kwargs.get('vmax', None),
            label=CLUSTER_LABELS.get(int(cluster_id), f"C{int(cluster_id)}")
        )
        handles.append(
            plt.Line2D([0], [0], marker=marker, color='w', label=CLUSTER_LABELS.get(int(cluster_id), f"C{int(cluster_id)}"),
                       markerfacecolor='gray', markeredgecolor='black', markersize=12, linestyle='None')
        )

    divider = make_axes_locatable(ax)
    cax_metric = divider.append_axes("right", size="2.75%", pad=0.598)
    cbar = fig.colorbar(sc, cax=cax_metric)
    cbar.set_label(value_col.replace('_', ' '), rotation=270, labelpad=32, fontsize=14)

    # Place DEM scale to the right of the metric scale.
    if dem_layer is not None and not BW_MODE:
        cax_dem = divider.append_axes("right", size="2.75%", pad=1.306)
        cbar_dem = fig.colorbar(dem_layer, cax=cax_dem, extend="both")
        cbar_dem.set_label("Elevation (m AOD)", rotation=270, labelpad=32, fontsize=14)

    ax.set_title(title, fontweight='bold')
    add_en_axes(ax)
    ax.grid(True, linestyle='--', alpha=0.4)

    # Add cluster shape legend
    cluster_legend = ax.legend(handles=handles, title="Core Cluster Assignments", loc='lower left', frameon=True)
    ax.add_artist(cluster_legend)
    if site_feature_handles:
        dedup = {}
        for handle in site_feature_handles:
            dedup[handle.get_label()] = handle
        ax.legend(handles=list(dedup.values()), loc='upper right', title="Site Features", frameon=True)

    # Keep both legends and two colorbars fully visible.
    plt.subplots_adjust(left=0.08, right=0.99, top=0.93, bottom=0.08)
    render_figure(plt.gcf(), output_path)
    plt.close()


def export_nse_diagnostics(ok_df: pd.DataFrame, master_path: Path,
                           perwell_path: Path, medians_path: Path,
                           report_path: Path) -> None:
    """§4.9.1 traceability: per-well ΔNSE/TLM-NSE, per-cluster medians, and the
    ΔNSE↔coefficient correlations, all written to committed CSVs.

    ΔNSE       = Iterative_NSE_Improvement (SSM minus TLM; the SSM is Model B since 2.0.0, D-332)
    TLM NSE    = Iterative_NSE_Traditional
    Cluster, β₂, β₃ are joined from 03_master_data.csv (Model B since Script 03 1.31.0).
    Model A, the tested alternative, is in the *_model_a columns and keys.
    """
    if ok_df.empty:
        warn("No valid SSM08 rows. Skipping NSE diagnostics export.")
        return
    if not master_path.exists():
        warn(f"Master file {master_path.name} absent — skipping NSE diagnostics.")
        return

    master = pd.read_csv(master_path)
    master = master.copy()
    master["Well_Normalized"] = master["Name_Original"].apply(normalize_well_name)
    keep = ["Well_Normalized", "Cluster",
            "beta_2_atmospheric_draw", "beta_3_drainage"]
    keep = [c for c in keep if c in master.columns]

    pw = ok_df[["Well", "Well_Normalized",
                "Iterative_NSE_Traditional",
                "Iterative_NSE_StateSpace",
                "Iterative_NSE_Improvement",
                "Iterative_NSE_ModelB",
                "Iterative_NSE_Improvement_ModelB",
                "Iterative_NSE_MHW",
                "Iterative_NSE_Improvement_MHW",
                "Datum_MHW_m",
                "Iterative_NSE_StateSpace_model_a",
                "Iterative_NSE_Improvement_model_a"]].merge(
        master[keep], on="Well_Normalized", how="left")
    pw = pw.rename(columns={
        "Iterative_NSE_Traditional": "TLM_NSE",
        "Iterative_NSE_StateSpace":  "SSM_NSE",
        "Iterative_NSE_Improvement": "dNSE",
        "Iterative_NSE_ModelB": "ModelB_NSE",
        "Iterative_NSE_Improvement_ModelB": "dNSE_ModelB",
        "Iterative_NSE_MHW": "MHW_NSE",                    # 1.9.0 (D-332)
        "Iterative_NSE_Improvement_MHW": "dNSE_MHW",
        "Iterative_NSE_StateSpace_model_a": "SSM_NSE_model_a",   # 2.0.0 (D-332): Model A
        "Iterative_NSE_Improvement_model_a": "dNSE_model_a",
    })
    # 1.9.0: the MHW columns go after every existing column, so positional readers are undisturbed;
    # 2.0.0 (D-332): SSM_NSE / dNSE now carry Model B (= ModelB_NSE / dNSE_ModelB); Model A appended last
    _new = ["MHW_NSE", "dNSE_MHW", "Datum_MHW_m", "SSM_NSE_model_a", "dNSE_model_a"]
    pw = pw[[c for c in pw.columns if c not in _new] + _new]
    pw.to_csv(perwell_path, index=False)
    saved(f"{perwell_path.name} ({len(pw)} wells)")

    # Per-cluster median ΔNSE and median TLM NSE
    med_rows = []
    for cid, grp in pw.dropna(subset=["Cluster"]).groupby("Cluster"):
        med_rows.append({
            "Cluster": f"C{int(cid)}",
            "n": int(len(grp)),
            "median_dNSE": float(pd.to_numeric(grp["dNSE"], errors="coerce").median()),
            "median_TLM_NSE": float(pd.to_numeric(grp["TLM_NSE"], errors="coerce").median()),
            # 1.7.0 (D-244): each form's own median and positive-NSE count, for Paper M's table
            "median_SSM_NSE": float(pd.to_numeric(grp["SSM_NSE"], errors="coerce").median()),
            "median_ModelB_NSE": float(pd.to_numeric(grp["ModelB_NSE"], errors="coerce").median()),
            "median_dNSE_ModelB": float(pd.to_numeric(grp["dNSE_ModelB"], errors="coerce").median()),
            "positive_TLM_NSE": int((pd.to_numeric(grp["TLM_NSE"], errors="coerce") > 0).sum()),
            "positive_SSM_NSE": int((pd.to_numeric(grp["SSM_NSE"], errors="coerce") > 0).sum()),
            "positive_ModelB_NSE": int((pd.to_numeric(grp["ModelB_NSE"], errors="coerce") > 0).sum()),
            # 1.9.0 (D-332): the MHW form (Model A at each well's depth to mean high water)
            "median_MHW_NSE": float(pd.to_numeric(grp["MHW_NSE"], errors="coerce").median()),
            "positive_MHW_NSE": int((pd.to_numeric(grp["MHW_NSE"], errors="coerce") > 0).sum()),
            "n_MHW": int(pd.to_numeric(grp["MHW_NSE"], errors="coerce").notna().sum()),
            # 2.0.0 (D-332): the *_SSM_* columns above carry Model B; Model A, the tested alternative, here
            "median_SSM_NSE_model_a": float(pd.to_numeric(grp["SSM_NSE_model_a"], errors="coerce").median()),
            "median_dNSE_model_a": float(pd.to_numeric(grp["dNSE_model_a"], errors="coerce").median()),
            "positive_SSM_NSE_model_a": int((pd.to_numeric(grp["SSM_NSE_model_a"], errors="coerce") > 0).sum()),
        })
    med_df = pd.DataFrame(med_rows).sort_values("Cluster")
    med_df.to_csv(medians_path, index=False)
    saved(f"{medians_path.name} ({len(med_df)} clusters)")

    # ΔNSE ↔ coefficient correlations (site-wide, reference network)
    rpt = ReportNumbers()

    # Network-wide benchmark headlines. These are the figures §4.4 of the report
    # actually quotes - the two median NSEs, the median gain and the two
    # positive-NSE counts - and until 2026-08-18 none of them was emitted, so
    # none was in the citation index and all five drifted silently across the
    # August reruns. Emitted here so cite_check can watch them.
    # 2.0.0 (D-332): the SSM in every *_SSM / dNSE key is Model B (free intercept); Model A's values are in
    # the *_model_a keys below. The *_ModelB keys (1.7.0) are kept and carry the same Model B values.
    rpt.add("benchmark_median_NSE_SSM", pw["SSM_NSE"].median(), unit="",
            note=f"median iterative NSE, state-space model (Model B, free intercept), n={len(pw)}")
    rpt.add("benchmark_median_NSE_TLM", pw["TLM_NSE"].median(), unit="",
            note=f"median iterative NSE, traditional linear model, n={len(pw)}")
    rpt.add("benchmark_median_dNSE", pw["dNSE"].median(), unit="",
            note=f"median gain in iterative NSE, SSM (Model B) over TLM, n={len(pw)}")
    rpt.add("benchmark_positive_NSE_SSM", int((pw["SSM_NSE"] > 0).sum()), unit="wells",
            note=f"wells with positive iterative NSE under the SSM (Model B), of {len(pw)}")
    rpt.add("benchmark_positive_NSE_TLM", int((pw["TLM_NSE"] > 0).sum()), unit="wells",
            note=f"wells with positive iterative NSE under the TLM, of {len(pw)}")
    # 1.7.0 (D-244): Model B against the TLM - the comparison that isolates the drainage term
    rpt.add("benchmark_median_NSE_ModelB", pw["ModelB_NSE"].median(), unit="",
            note=f"median iterative NSE, Model B (free intercept), n={len(pw)}")
    rpt.add("benchmark_median_dNSE_ModelB", pw["dNSE_ModelB"].median(), unit="",
            note=f"median gain in iterative NSE, Model B over TLM, n={len(pw)}")
    rpt.add("benchmark_positive_NSE_ModelB", int((pw["ModelB_NSE"] > 0).sum()), unit="wells",
            note=f"wells with positive iterative NSE under Model B, of {len(pw)}")
    rpt.add("benchmark_n_wells", int(len(pw)), unit="wells",
            note="reference wells entering the benchmark")
    # 2.0.0 (D-332): Model A at DRAINAGE_DATUM, the tested alternative (until 2.0.0 the *_SSM keys carried it)
    _a = pd.to_numeric(pw["SSM_NSE_model_a"], errors="coerce")
    _da = pd.to_numeric(pw["dNSE_model_a"], errors="coerce")
    _na = int(_a.notna().sum())
    rpt.add("benchmark_median_NSE_SSM_model_a", _a.median(), unit="",
            note=f"median iterative NSE, Model A (no intercept, datum {DRAINAGE_DATUM} m), n={_na}")
    rpt.add("benchmark_median_dNSE_model_a", _da.median(), unit="",
            note=f"median gain in iterative NSE, Model A over TLM, n={_na}")
    rpt.add("benchmark_positive_NSE_SSM_model_a", int((_a > 0).sum()), unit="wells",
            note=f"wells with positive iterative NSE under Model A, of {_na}")
    _neg_a = pw[_a < 0]
    rpt.add("benchmark_negative_NSE_SSM_model_a", int(len(_neg_a)), unit="wells",
            note=(f"wells with negative iterative NSE under Model A, of {_na}: "
                  + (", ".join(str(w) for w in _neg_a["Well"]) if len(_neg_a) else "none")))
    _worse_a = pw[_da < 0]
    rpt.add("benchmark_wells_SSM_worse_model_a", int(len(_worse_a)), unit="wells",
            note=("wells where Model A scores below the TLM: "
                  + (", ".join(str(w) for w in _worse_a["Well"]) if len(_worse_a) else "none")))
    # 1.9.0 (D-332): the MHW form, Model A at each well's depth to mean high water (a tested alternative)
    _m = pd.to_numeric(pw["MHW_NSE"], errors="coerce")
    rpt.add("benchmark_median_NSE_MHW", _m.median(), unit="",
            note=f"median iterative NSE, Model A at each well's depth to mean high water, n={int(_m.notna().sum())}")
    rpt.add("benchmark_median_dNSE_MHW", pd.to_numeric(pw["dNSE_MHW"], errors="coerce").median(), unit="",
            note=f"median gain in iterative NSE, Model A at mean high water over TLM, n={int(_m.notna().sum())}")
    rpt.add("benchmark_positive_NSE_MHW", int((_m > 0).sum()), unit="wells",
            note=f"wells with positive iterative NSE, Model A at mean high water, of {int(_m.notna().sum())}")
    rpt.add("benchmark_n_wells_MHW", int(_m.notna().sum()), unit="wells",
            note="benchmark wells with a ground level, so a depth to mean high water (the MHW form)")
    # 1.9.0 (D-332): wells where Model B's beta_3 is held at the bound MODEL_B_BETA3_MIN (model_utils 1.14.0)
    _bd = ok_df["Beta_3_bound_binds_ModelB"].fillna(False).astype(bool) if "Beta_3_bound_binds_ModelB" in ok_df else pd.Series(dtype=bool)
    rpt.add("benchmark_n_beta3_bound_ModelB", int(_bd.sum()), unit="wells",
            note=("wells where Model B's beta_3 is held at its lower bound (not identified): "
                  + (", ".join(str(w) for w in ok_df.loc[_bd, "Well"]) if _bd.any() else "none")))
    # T-96: the negative-NSE counts report12 §7 quotes directly ("1 of 66 SSM
    # wells ... compared with 11 of 66 for the TLM"), counted rather than left
    # to the reader as n minus the positive counts above.
    for _m in ("SSM", "TLM"):
        _neg = pw[pw[f"{_m}_NSE"] < 0]
        rpt.add(f"benchmark_negative_NSE_{_m}", int(len(_neg)), unit="wells",
                note=(f"wells with negative iterative NSE under the {_m}, of {len(pw)}: "
                      + (", ".join(str(w) for w in _neg["Well"]) if len(_neg) else "none")))

    # Wells where the SSM (Model B since 2.0.0) loses to the linear model. Under Model A the cause was a
    # non-positive beta_3, which makes the free run diverge; Model B's beta_3 is bounded below
    # (model_utils 1.14.0), so a loss here is a fit that free-runs worse, not a divergent recursion.
    _worse = pw[pw["dNSE"] < 0]
    rpt.add("benchmark_wells_SSM_worse", int(len(_worse)), unit="wells",
            note=("wells where the SSM (Model B) scores below the TLM: "
                  + (", ".join(str(w) for w in _worse["Well"]) if len(_worse) else "none")))

    for _, r in med_df.iterrows():
        rpt.add(f"{r['Cluster']}_median_dNSE", r["median_dNSE"], unit="",
                note=f"median ΔNSE (SSM−TLM; the SSM is Model B), {r['Cluster']}, n={int(r['n'])}")
        rpt.add(f"{r['Cluster']}_median_TLM_NSE", r["median_TLM_NSE"], unit="",
                note=f"median TLM iterative NSE, {r['Cluster']}, n={int(r['n'])}")
        for _m, _lbl in (("SSM", "the SSM (Model B, free intercept)"), ("ModelB", "Model B (free intercept)")):
            rpt.add(f"{r['Cluster']}_median_{_m}_NSE", r[f"median_{_m}_NSE"], unit="",
                    note=f"median iterative NSE, {_lbl}, {r['Cluster']}, n={int(r['n'])}")
        for _m in ("TLM", "SSM", "ModelB"):
            rpt.add(f"{r['Cluster']}_positive_{_m}_NSE", int(r[f"positive_{_m}_NSE"]), unit="wells",
                    note=f"wells with positive iterative NSE under {_m}, {r['Cluster']}, of {int(r['n'])}")
        # 2.0.0 (D-332): Model A at DRAINAGE_DATUM, the tested alternative
        rpt.add(f"{r['Cluster']}_median_SSM_NSE_model_a", r["median_SSM_NSE_model_a"], unit="",
                note=f"median iterative NSE, Model A (no intercept, datum {DRAINAGE_DATUM} m), {r['Cluster']}, "
                     f"n={int(r['n'])}")
        rpt.add(f"{r['Cluster']}_median_dNSE_model_a", r["median_dNSE_model_a"], unit="",
                note=f"median ΔNSE (Model A − TLM), {r['Cluster']}, n={int(r['n'])}")
        rpt.add(f"{r['Cluster']}_positive_SSM_NSE_model_a", int(r["positive_SSM_NSE_model_a"]), unit="wells",
                note=f"wells with positive iterative NSE under Model A, {r['Cluster']}, of {int(r['n'])}")
        # 1.9.0 (D-332): the MHW form
        rpt.add(f"{r['Cluster']}_median_MHW_NSE", r["median_MHW_NSE"], unit="",
                note=f"median iterative NSE, Model A at each well's depth to mean high water, {r['Cluster']}, "
                     f"n={int(r['n_MHW'])}")
        rpt.add(f"{r['Cluster']}_positive_MHW_NSE", int(r["positive_MHW_NSE"]), unit="wells",
                note=f"wells with positive iterative NSE, Model A at mean high water, {r['Cluster']}, of {int(r['n_MHW'])}")
    for coef, key in [("beta_3_drainage", "beta3"),
                      ("beta_2_atmospheric_draw", "beta2")]:
        if coef in pw.columns:
            sub = pw.dropna(subset=["dNSE", coef])
            if len(sub) >= 3:
                r, p = _spstats.pearsonr(sub["dNSE"], sub[coef])
                rpt.add(f"dNSE_vs_{key}_r", r, unit="",
                        note=f"Pearson r, ΔNSE vs {coef}, n={len(sub)}")
                rpt.add(f"dNSE_vs_{key}_p", p, unit="",
                        note=f"p-value, ΔNSE vs {coef}, n={len(sub)}")
    # 2.0.0 (D-332): the same correlations for Model A - its ΔNSE against its own master coefficients
    # (03_master_data *_model_a); the keys above now pair Model B's ΔNSE with Model B's coefficients.
    _ma = [c for c in ("beta_3_drainage_model_a", "beta_2_atmospheric_draw_model_a") if c in master.columns]
    _pa = pw[["Well_Normalized", "dNSE_model_a"]].merge(master[["Well_Normalized"] + _ma],
                                                       on="Well_Normalized", how="left")
    for coef, key in [("beta_3_drainage_model_a", "beta3"), ("beta_2_atmospheric_draw_model_a", "beta2")]:
        if coef in _pa.columns:
            sub = _pa.dropna(subset=["dNSE_model_a", coef])
            if len(sub) >= 3:
                r, p = _spstats.pearsonr(sub["dNSE_model_a"], sub[coef])
                rpt.add(f"dNSE_vs_{key}_r_model_a", r, unit="",
                        note=f"Pearson r, Model A's ΔNSE vs {coef}, n={len(sub)}")
                rpt.add(f"dNSE_vs_{key}_p_model_a", p, unit="",
                        note=f"p-value, Model A's ΔNSE vs {coef}, n={len(sub)}")
    n_saved = rpt.save(report_path)
    saved(f"{report_path.name} ({n_saved} report numbers)")


def export_table3_summary(ok_df: pd.DataFrame, output_path: Path) -> None:
    """Export manuscript Table 3 (report Table 5) benchmark summary from per-well model metrics.

    2.0.0 (D-332): columns TLM, SSM_Model_B (the SSM), Model_A (DRAINAGE_DATUM), MHW (Model A at each
    well's depth to mean high water) and Delta_SSM_minus_TLM. Until 2.0.0 the columns used an older
    naming in which "Model A" was the TLM and "Model B" the no-intercept SSM (today's Model A).
    The MHW column is over the wells with a ground level (n in the positive-count cell).
    """
    if ok_df.empty:
        warn("No valid SSM08 rows. Skipping Table 3 summary export.")
        return

    def _median(col: str) -> float:
        return float(pd.to_numeric(ok_df[col], errors='coerce').median())

    def _pos(col: str) -> str:
        v = pd.to_numeric(ok_df[col], errors='coerce')
        return f'{int((v > 0).sum())} / {int(v.notna().sum())}'

    # Manuscript convention: exclude lake sentinel well from the max-improvement row.
    best_pool = ok_df[ok_df['Well_Normalized'].astype(str).str.lower() != 'llynrhos']
    if best_pool.empty:
        best_pool = ok_df
    best_idx = pd.to_numeric(best_pool['Iterative_NSE_Improvement'], errors='coerce').idxmax()
    best_row = best_pool.loc[best_idx]
    best_well = str(best_row.get('Well', 'NA')).upper()

    def _well_row(well_norm: str):
        rows = ok_df[ok_df['Well_Normalized'].astype(str).str.lower() == well_norm]
        return rows.iloc[0] if len(rows) else None

    def _nse_row(label, r):
        if r is None:
            return {'Metric': label, 'TLM': np.nan, 'SSM_Model_B': np.nan, 'Model_A': np.nan,
                    'MHW': np.nan, 'Delta_SSM_minus_TLM': np.nan}
        return {'Metric': label,
                'TLM': float(r['Iterative_NSE_Traditional']),
                'SSM_Model_B': float(r['Iterative_NSE_StateSpace']),
                'Model_A': float(r['Iterative_NSE_StateSpace_model_a']),
                'MHW': float(r['Iterative_NSE_MHW']),
                'Delta_SSM_minus_TLM': float(r['Iterative_NSE_Improvement'])}

    def _med_row(label, trad, ssm, mod_a, mhw, delta):
        return {'Metric': label, 'TLM': _median(trad), 'SSM_Model_B': _median(ssm),
                'Model_A': _median(mod_a), 'MHW': _median(mhw), 'Delta_SSM_minus_TLM': _median(delta)}

    rows = [
        _med_row('Median one-step R2', 'OneStep_R2_Traditional', 'OneStep_R2_StateSpace',
                 'OneStep_R2_StateSpace_model_a', 'OneStep_R2_MHW', 'OneStep_R2_Improvement'),
        _med_row('Median iterative R2', 'Iterative_R2_Traditional', 'Iterative_R2_StateSpace',
                 'Iterative_R2_StateSpace_model_a', 'Iterative_R2_MHW', 'Iterative_R2_Improvement'),
        _med_row('Median iterative NSE', 'Iterative_NSE_Traditional', 'Iterative_NSE_StateSpace',
                 'Iterative_NSE_StateSpace_model_a', 'Iterative_NSE_MHW', 'Iterative_NSE_Improvement'),
        {
            'Metric': 'Wells with iterative NSE > 0',
            'TLM': _pos('Iterative_NSE_Traditional'),
            'SSM_Model_B': _pos('Iterative_NSE_StateSpace'),
            'Model_A': _pos('Iterative_NSE_StateSpace_model_a'),
            'MHW': _pos('Iterative_NSE_MHW'),
            'Delta_SSM_minus_TLM': '\u2014',
        },
        _nse_row(f'Max NSE improvement ({best_well})', best_row),
        _nse_row('CEH6 iterative NSE', _well_row('ceh6')),
        _nse_row('CEH14 iterative NSE', _well_row('ceh14')),
    ]

    pd.DataFrame(rows).to_csv(output_path, index=False)
    step(f"Saved manuscript Table 3 summary: {output_path.name}")


if __name__ == '__main__':
    make_all_dirs()
    print('Starting SSM08 Model Showdown Pipeline...')
    print(f'  Displacement formulation: DRAINAGE_DATUM = {DRAINAGE_DATUM} m; SSM = Model B (free intercept)')
    print(f'  Rainfall lag: {HEADLINE_LAG} month(s)')

    wells_clean = pd.read_csv(WELLS_PATH, index_col=0, parse_dates=True)
    climate = pd.read_csv(CLIMATE_PATH, index_col=0, parse_dates=True)

    reference_wells = pd.read_csv(REFERENCE_NETWORK_PATH, index_col=0, parse_dates=True).columns.tolist()
    reference_wells_norm = [normalize_well_name(w) for w in reference_wells]
    wells_to_run = [
        c for c in wells_clean.columns
        if normalize_well_name(c) in reference_wells_norm and normalize_well_name(c) not in EXCLUDED_WELLS_NORM
    ]
    excluded_non_reference = sum(1 for c in wells_clean.columns if normalize_well_name(c) not in reference_wells_norm)
    excluded_by_rule = sum(1 for c in wells_clean.columns if normalize_well_name(c) in EXCLUDED_WELLS_NORM)
    print(
        f" -> Restricting to {len(wells_to_run)} reference network wells "
        f"(excluded {excluded_non_reference} non-reference + {excluded_by_rule} by rule: CEH7/CEH8/CEH37)"
    )

    mhw_d = mhw_datums()        # 1.9.0 (D-332): the MHW form's per-well datum
    all_rows = []
    for well_col in wells_to_run:
        row, _ = compute_showdown_metrics(well_col, wells_clean, climate,
                                          mhw_datum=mhw_d.get(normalize_well_name(well_col)))
        all_rows.append(row)

    perf_df = pd.DataFrame(all_rows).sort_values('Well_Normalized').reset_index(drop=True)
    ok_df = perf_df[perf_df['Status'] == 'ok'].copy().reset_index(drop=True)

    # CSV 2: the SSM's performance and its improvement over the TLM. Since 2.0.0 (D-332) the SSM is
    # Model B (free intercept); Model A (no intercept, DRAINAGE_DATUM) is appended in *_model_a columns.
    # (Until 1.9.0 this comment called the SSM "Model B (State-Space)" and the TLM "Model A", an older
    # naming; Model A and Model B are the no-intercept and free-intercept forms.)
    model_stats_df = ok_df[
        [
            'Well',
            'Well_Normalized',
            'Months_Used',
            'OneStep_R2_Traditional',
            'OneStep_R2_StateSpace',
            'OneStep_R2_Improvement',
            'Iterative_R2_Traditional',
            'Iterative_R2_StateSpace',
            'Iterative_R2_Improvement',
            'Iterative_NSE_Traditional',
            'Iterative_NSE_StateSpace',
            'Iterative_NSE_Improvement',
            # The benchmark's own SSM fit, exported from v1.4.2 so it can be
            # diffed against 03_master_data.csv. Computed since v1.4.0 but
            # dropped here by the fixed column list - the coefficients existed
            # on the row and never reached the file, so "checkable" was a claim
            # rather than a fact. Appended, not interleaved, so existing column
            # order is untouched for anything reading positionally.
            'Beta_P_StateSpace',
            'Beta_PET_StateSpace',
            'Beta_hdisp_StateSpace',
            'pvalue_beta_1_StateSpace',
            'pvalue_beta_2_StateSpace',
            'pvalue_beta_3_StateSpace',
            'R2_StateSpace_fit',
            # 2.0.0 (D-332): Model B's intercept, then Model A, appended
            'Alpha_StateSpace',
            'Beta_3_bound_binds_ModelB',
            'OneStep_R2_StateSpace_model_a',
            'Iterative_R2_StateSpace_model_a',
            'Iterative_NSE_StateSpace_model_a',
            'Iterative_NSE_Improvement_model_a',
            'Beta_P_StateSpace_model_a',
            'Beta_PET_StateSpace_model_a',
            'Beta_hdisp_StateSpace_model_a',
            'pvalue_beta_3_StateSpace_model_a',
            'R2_StateSpace_fit_model_a',
        ]
    ].copy()
    stats_csv = INT_LCSC_MODEL_STATS
    model_stats_df.to_csv(stats_csv, index=False)
    print(f"\n -> Exported SSM08 SSMvTLM stats table (includes NSE): {stats_csv.name}")
    export_table3_summary(ok_df, OUT_08_TABLE3_SUMMARY)
    export_nse_diagnostics(ok_df, INT_MASTER_DATA,
                           OUT_08_PERWELL_NSE, OUT_08_CLUSTER_NSE_MEDIANS,
                           OUT_08_REPORT_NUMBERS)

    # Generate detailed dual-panel plots for selected manuscript wells

    # CEH6 dual-panel showdown: TLM vs SSM (Model B since 2.0.0, D-332)
    # CEH6 chosen as showcase (under Model A, 2026-09-03: TLM drifted to NSE = -1.885 while the SSM held
    # at +0.674); its current values are the "CEH6 iterative NSE" row of 08_lcsc_04.
    _, ceh6_payload = compute_showdown_metrics('ceh6', wells_clean, climate)
    if ceh6_payload is not None:
        showdown_path = OUT_08_SHOWDOWN
        plot_showdown(showdown_path, ceh6_payload)
        step(f"Saved CEH6 showdown: {showdown_path.name}")
    else:
        warn("Could not build CEH6 showdown (missing CEH6 payload).")

    # Join metrics with coordinates for map visualizations
    if MASTER_PATH.exists():
        master_df = pd.read_csv(MASTER_PATH)
        master_coords = master_df[['Name_Original', 'Easting', 'Northing']].copy()
        master_coords['Well_Normalized'] = master_coords['Name_Original'].apply(normalize_well_name)

        # Merge in cluster assignments
        cluster_stats_path = INT_CLUSTER_STATS
        if cluster_stats_path.exists():
            cluster_df = pd.read_csv(cluster_stats_path)
            if 'Match_ID' in cluster_df.columns:
                cluster_df['Match_ID'] = cluster_df['Match_ID'].apply(normalize_well_name)
            elif 'Name_Original' in cluster_df.columns:
                cluster_df['Match_ID'] = cluster_df['Name_Original'].apply(normalize_well_name)
            else:
                cluster_df['Match_ID'] = pd.Series(dtype=str)

            cluster_col = 'Cluster_ID' if 'Cluster_ID' in cluster_df.columns else ('Cluster' if 'Cluster' in cluster_df.columns else None)
            if cluster_col is not None:
                cluster_df = cluster_df[['Match_ID', cluster_col]].rename(columns={cluster_col: 'Cluster_ID'})
            else:
                cluster_df = pd.DataFrame(columns=['Match_ID', 'Cluster_ID'])
        else:
            cluster_df = None

        map_df = perf_df.merge(master_coords[['Well_Normalized', 'Easting', 'Northing']], on='Well_Normalized', how='left')
        if cluster_df is not None:
            map_df = map_df.merge(cluster_df, left_on='Well_Normalized', right_on='Match_ID', how='left')

        # Normalize possible merge suffixes into a single Cluster_ID column.
        if 'Cluster_ID' not in map_df.columns:
            for candidate in ['Cluster_ID_x', 'Cluster_ID_y', 'Cluster']:
                if candidate in map_df.columns:
                    map_df['Cluster_ID'] = map_df[candidate]
                    break

        # MAP 1: Delta R2 (Deep Sponge vs. Shallow Bucket Diagnostic)
        improvement_map_path = OUT_08_R2_MAP
        r2_vmin = map_df['Iterative_R2_Improvement'].min()
        r2_vmax = map_df['Iterative_R2_Improvement'].max()
        r2_center = 0 if r2_vmin < 0 < r2_vmax else (r2_vmin + r2_vmax) / 2
        plot_metric_map(
            map_df,
            value_col='Iterative_R2_Improvement',
            title='Structural Memory: Iterative R² Improvement (State-Space Gain, Model B)',
            output_path=improvement_map_path,
            cmap='RdYlBu',
            vmin=r2_vmin,
            vmax=r2_vmax,
        )

        # MAP 2: Delta NSE (Anomaly and Water Balance Residual Detection)
        nse_anomaly_map_path = OUT_08_NSE_MAP
        plot_metric_map(
            map_df,
            value_col='Iterative_NSE_Improvement',
            title='Water Balance Residuals: Iterative NSE Improvement, Model B (Anomaly Detection)',
            output_path=nse_anomaly_map_path,
            cmap='plasma',
            vmin=0.0,
            vmax=2.5,
        )

        step(f"Saved diagnostic map 1: {improvement_map_path.name}")
        step(f"Saved diagnostic map 2: {nse_anomaly_map_path.name}")
    else:
        warn(f"Master coordinate file not found: {MASTER_PATH.name}. Skipping metric maps.")

    print('\nSSM08 Model Showdown Complete!')
