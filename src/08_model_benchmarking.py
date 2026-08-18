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
        State-Space (SSM, displacement formulation):
            Δh(t) = β₁·P(t) − β₂·PET(t) − β₃·h_disp_prev(t)
            where h_disp = DRAINAGE_DATUM + h_depth

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

__version__ = "1.5.0"  # Hollingham (2026) — 2026-08-18. Two changes to
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
)
from utils.data_utils import normalize_well_name
from utils.report_numbers_utils import ReportNumbers
from utils.model_utils import (get_metrics, get_r2, build_ssm_frame, simulate_ssm,
                              fit_ssm)
from utils.map_utils import add_kml_features, load_dem_layer, add_en_axes
from utils.config import (
    CLUSTER_LABELS, CLUSTER_MARKERS, DRAINAGE_DATUM, HEADLINE_LAG, BW_MODE,
    LCSC_DATA_LIMIT,
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


def compute_showdown_metrics(target_well_name, df_clean, df_climate):
    """Compute one-step and iterative showdown metrics for a single well.

    Uses the displacement formulation (h_disp = DRAINAGE_DATUM + h_depth)
    for the SSM drainage predictor and HEADLINE_LAG rainfall (= 0 currently),
    matching Script 03.
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

    if len(df) < LCSC_DATA_LIMIT:
        base_row['Status'] = 'insufficient_data'
        base_row['Months_Used'] = len(df)
        return base_row, None

    # Traditional model: Δh = α + β₁·P(t-lag) - β₂·PET(t). The TLM is this
    # script's own comparator and has no counterpart in model_utils, so it is
    # fitted here.
    x_trad = sm.add_constant(pd.DataFrame({'P': df['P'], 'PET': -df['PET']}), has_constant='add')
    y_fit = df['Delta_h']
    model_trad = sm.OLS(y_fit, x_trad).fit()

    # State-space model: the CANONICAL fitter, not a local copy. Until v1.4.0
    # this script assembled its own design matrix and called sm.OLS directly.
    # It was arithmetically the same fit, but it bypassed fit_ssm()'s min_obs
    # floor and sign handling, its coefficients were never comparable to
    # 03_master_data.csv by construction, and any future change to the canonical
    # specification would silently have left the benchmark behind. The frame is
    # already built (and windowed) above, so pre_built_frame is passed through
    # and fit_ssm does no realignment of its own.
    ssm = fit_ssm(pre_built_frame=df)
    if ssm is None:
        base_row['Status'] = 'ssm_fit_failed'
        base_row['Months_Used'] = len(df)
        return base_row, None
    b1_ssm = float(ssm['beta_1_recharge'])
    b2_ssm = float(ssm['beta_2_atmospheric_draw'])
    b3_ssm = float(ssm['beta_3_drainage'])

    p_arr = df['P'].values
    pet_arr = df['PET'].values
    h_obs = df['h'].values

    # ---- One-step simulation (uses observed h_prev at each step) ----
    h_trad_one = np.full(len(h_obs), np.nan)
    h_lcsc_one = np.full(len(h_obs), np.nan)
    h_trad_one[0] = h_obs[0]
    h_lcsc_one[0] = h_obs[0]

    for t in range(1, len(h_obs)):
        h_prev_obs = h_obs[t - 1]
        h_disp_prev_obs = DRAINAGE_DATUM + h_prev_obs

        dh_trad = (model_trad.params['const']
                   + model_trad.params['P'] * p_arr[t]
                   - model_trad.params['PET'] * pet_arr[t])
        dh_lcsc = (b1_ssm * p_arr[t]
                   - b2_ssm * pet_arr[t]
                   - b3_ssm * h_disp_prev_obs)
        h_trad_one[t] = h_prev_obs + dh_trad
        h_lcsc_one[t] = h_prev_obs + dh_lcsc

    # ---- Iterative (autonomous) simulation ----
    # TLM iterative: no h_prev feedback, just accumulates Δh from climate
    h_trad_iter = np.full(len(h_obs), np.nan)
    h_trad_iter[0] = h_obs[0]
    for t in range(1, len(h_obs)):
        dh_trad = (model_trad.params['const']
                   + model_trad.params['P'] * p_arr[t]
                   - model_trad.params['PET'] * pet_arr[t])
        h_trad_iter[t] = h_trad_iter[t - 1] + dh_trad

    # SSM iterative: use shared simulate_ssm (displacement recurrence)
    # Design matrix columns are already negated (-PET, -h_disp_prev), so the
    # fitted OLS params ARE the β values directly (positive = physically correct).
    # simulate_ssm expects: dh = b1*P - b2*PET - b3*(D+h), with b1,b2,b3 positive.
    h_lcsc_iter_raw = simulate_ssm(
        h0=h_obs[0], P=p_arr[1:], PET=pet_arr[1:],
        b1=b1_ssm,
        b2=b2_ssm,           # already β₂ (coeff on -PET)
        b3=b3_ssm,    # already β₃ (coeff on -h_disp)
    )
    h_lcsc_iter = np.concatenate([[h_obs[0]], h_lcsc_iter_raw])

    r2_trad_one = get_r2(h_obs, h_trad_one)
    r2_lcsc_one = get_r2(h_obs, h_lcsc_one)

    nse_trad, rmse_trad, _ = get_metrics(h_obs, h_trad_iter)
    nse_lcsc, rmse_lcsc, _ = get_metrics(h_obs, h_lcsc_iter)
    r2_trad_iter = get_r2(h_obs, h_trad_iter)
    r2_lcsc_iter = get_r2(h_obs, h_lcsc_iter)

    base_row.update({
        'Months_Used': len(df),
        'OneStep_R2_Traditional': r2_trad_one,
        'OneStep_R2_StateSpace': r2_lcsc_one,
        'OneStep_R2_Improvement': r2_lcsc_one - r2_trad_one,
        'Iterative_NSE_Traditional': nse_trad,
        'Iterative_NSE_StateSpace': nse_lcsc,
        'Iterative_NSE_Improvement': nse_lcsc - nse_trad,
        'Iterative_RMSE_Traditional': rmse_trad,
        'Iterative_RMSE_StateSpace': rmse_lcsc,
        'Iterative_RMSE_Improvement': rmse_trad - rmse_lcsc,
        'Iterative_R2_Traditional': r2_trad_iter,
        'Iterative_R2_StateSpace': r2_lcsc_iter,
        'Iterative_R2_Improvement': r2_lcsc_iter - r2_trad_iter,
        'Beta_P_Traditional': model_trad.params['P'],
        'Beta_PET_Traditional': model_trad.params['PET'],
        'Intercept_Traditional': model_trad.params['const'],
        'Beta_P_StateSpace': b1_ssm,
        'Beta_PET_StateSpace': b2_ssm,
        'Beta_hdisp_StateSpace': b3_ssm,
        # Emitted so the benchmark's SSM is checkable against 03_master_data.csv
        # rather than merely assumed to agree with it (D-033 step zero).
        'pvalue_beta_1_StateSpace': float(ssm['pvalue_beta_1']),
        'pvalue_beta_2_StateSpace': float(ssm['pvalue_beta_2']),
        'pvalue_beta_3_StateSpace': float(ssm['pvalue_beta_3']),
        'R2_StateSpace_fit': float(ssm['R2']),
    })

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
    """Dual-panel TLM vs SSM showdown for a target well."""
    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(14, 10), dpi=300, sharex=True)
    well_label = payload.get('well_label', 'TARGET')

    # Top Panel: Diagnostic Fit (One-Step)
    ax_top.plot(payload['index'], payload['h_obs'], color='black', lw=2.8, label='Observed')
    ax_top.plot(payload['index'], payload['h_trad_one'], color='#D55E00', lw=2.2, ls=':', label=f"TLM (R\u00b2={payload['r2_trad_one']:.3f})")
    ax_top.plot(payload['index'], payload['h_lcsc_one'], color='#0072B2', lw=2.2, ls='--', label=f"SSM (R\u00b2={payload['r2_lcsc_one']:.3f})")
    ax_top.set_title(f'{well_label}: Diagnostic Fit (One-Step)', fontweight='bold')
    ax_top.set_ylabel('Water Depth (m below surface)')
    ax_top.grid(True, ls='--', alpha=0.5)
    ax_top.legend(loc='upper left', frameon=True, edgecolor='black')

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
            f"SSM (NSE={payload['nse_lcsc']:.3f}, "
            f"RMSE={payload['rmse_lcsc']:.3f}, R²={payload['r2_lcsc_iter']:.3f})"
        ),
    )
    ax_bottom.set_title(f'{well_label}: Forecasting Stability (Iterative)', fontweight='bold')
    ax_bottom.set_xlabel('Date')
    ax_bottom.set_ylabel('Water Depth (m below surface)')
    ax_bottom.grid(True, ls='--', alpha=0.5)
    ax_bottom.legend(loc='upper left', frameon=True, edgecolor='black')
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

    ΔNSE       = Iterative_NSE_Improvement (SSM minus TLM)
    TLM NSE    = Iterative_NSE_Traditional
    Cluster, β₂, β₃ are joined from 03_master_data.csv (uniform DRAINAGE_DATUM).
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
                "Iterative_NSE_Improvement"]].merge(
        master[keep], on="Well_Normalized", how="left")
    pw = pw.rename(columns={
        "Iterative_NSE_Traditional": "TLM_NSE",
        "Iterative_NSE_StateSpace":  "SSM_NSE",
        "Iterative_NSE_Improvement": "dNSE",
    })
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
    rpt.add("benchmark_median_NSE_SSM", pw["SSM_NSE"].median(), unit="",
            note=f"median iterative NSE, state-space model, n={len(pw)}")
    rpt.add("benchmark_median_NSE_TLM", pw["TLM_NSE"].median(), unit="",
            note=f"median iterative NSE, traditional linear model, n={len(pw)}")
    rpt.add("benchmark_median_dNSE", pw["dNSE"].median(), unit="",
            note=f"median gain in iterative NSE, SSM over TLM, n={len(pw)}")
    rpt.add("benchmark_positive_NSE_SSM", int((pw["SSM_NSE"] > 0).sum()), unit="wells",
            note=f"wells with positive iterative NSE under the SSM, of {len(pw)}")
    rpt.add("benchmark_positive_NSE_TLM", int((pw["TLM_NSE"] > 0).sum()), unit="wells",
            note=f"wells with positive iterative NSE under the TLM, of {len(pw)}")
    rpt.add("benchmark_n_wells", int(len(pw)), unit="wells",
            note="reference wells entering the benchmark")

    # Wells where the SSM loses to the linear model. Worth a named number: the
    # cause is a non-positive beta_3, which makes the iterative recursion
    # divergent rather than decaying, so the deficit is arithmetic and should
    # not be read as the physical model failing.
    _worse = pw[pw["dNSE"] < 0]
    rpt.add("benchmark_wells_SSM_worse", int(len(_worse)), unit="wells",
            note=("wells where the SSM scores below the TLM: "
                  + (", ".join(str(w) for w in _worse["Well"]) if len(_worse) else "none")))

    for _, r in med_df.iterrows():
        rpt.add(f"{r['Cluster']}_median_dNSE", r["median_dNSE"], unit="",
                note=f"median ΔNSE (SSM−TLM), {r['Cluster']}, n={int(r['n'])}")
        rpt.add(f"{r['Cluster']}_median_TLM_NSE", r["median_TLM_NSE"], unit="",
                note=f"median TLM iterative NSE, {r['Cluster']}, n={int(r['n'])}")
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
    n_saved = rpt.save(report_path)
    saved(f"{report_path.name} ({n_saved} report numbers)")


def export_table3_summary(ok_df: pd.DataFrame, output_path: Path) -> None:
    """Export manuscript Table 3 benchmark summary from per-well model metrics."""
    if ok_df.empty:
        warn("No valid SSM08 rows. Skipping Table 3 summary export.")
        return

    def _median(col: str) -> float:
        return float(pd.to_numeric(ok_df[col], errors='coerce').median())

    n_wells = len(ok_df)
    trad_pos = int((pd.to_numeric(ok_df['Iterative_NSE_Traditional'], errors='coerce') > 0).sum())
    ss_pos = int((pd.to_numeric(ok_df['Iterative_NSE_StateSpace'], errors='coerce') > 0).sum())

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

    ceh6 = _well_row('ceh6')
    ceh14 = _well_row('ceh14')

    rows = [
        {
            'Metric': 'Median one-step R2',
            'Traditional_Model_A': _median('OneStep_R2_Traditional'),
            'StateSpace_Model_B': _median('OneStep_R2_StateSpace'),
            'Delta_B_minus_A': _median('OneStep_R2_Improvement'),
        },
        {
            'Metric': 'Median iterative R2',
            'Traditional_Model_A': _median('Iterative_R2_Traditional'),
            'StateSpace_Model_B': _median('Iterative_R2_StateSpace'),
            'Delta_B_minus_A': _median('Iterative_R2_Improvement'),
        },
        {
            'Metric': 'Median iterative NSE',
            'Traditional_Model_A': _median('Iterative_NSE_Traditional'),
            'StateSpace_Model_B': _median('Iterative_NSE_StateSpace'),
            'Delta_B_minus_A': _median('Iterative_NSE_Improvement'),
        },
        {
            'Metric': 'Wells with iterative NSE > 0',
            'Traditional_Model_A': f'{trad_pos} / {n_wells}',
            'StateSpace_Model_B': f'{ss_pos} / {n_wells}',
            'Delta_B_minus_A': '\u2014',
        },
        {
            'Metric': f'Max NSE improvement ({best_well})',
            'Traditional_Model_A': float(best_row['Iterative_NSE_Traditional']),
            'StateSpace_Model_B': float(best_row['Iterative_NSE_StateSpace']),
            'Delta_B_minus_A': float(best_row['Iterative_NSE_Improvement']),
        },
        {
            'Metric': 'CEH6 iterative NSE',
            'Traditional_Model_A': float(ceh6['Iterative_NSE_Traditional']) if ceh6 is not None else np.nan,
            'StateSpace_Model_B': float(ceh6['Iterative_NSE_StateSpace']) if ceh6 is not None else np.nan,
            'Delta_B_minus_A': float(ceh6['Iterative_NSE_Improvement']) if ceh6 is not None else np.nan,
        },
        {
            'Metric': 'CEH14 iterative NSE',
            'Traditional_Model_A': float(ceh14['Iterative_NSE_Traditional']) if ceh14 is not None else np.nan,
            'StateSpace_Model_B': float(ceh14['Iterative_NSE_StateSpace']) if ceh14 is not None else np.nan,
            'Delta_B_minus_A': float(ceh14['Iterative_NSE_Improvement']) if ceh14 is not None else np.nan,
        },
    ]

    pd.DataFrame(rows).to_csv(output_path, index=False)
    step(f"Saved manuscript Table 3 summary: {output_path.name}")


if __name__ == '__main__':
    make_all_dirs()
    print('Starting SSM08 Model Showdown Pipeline...')
    print(f'  Displacement formulation: DRAINAGE_DATUM = {DRAINAGE_DATUM} m')
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

    all_rows = []
    for well_col in wells_to_run:
        row, _ = compute_showdown_metrics(well_col, wells_clean, climate)
        all_rows.append(row)

    perf_df = pd.DataFrame(all_rows).sort_values('Well_Normalized').reset_index(drop=True)
    ok_df = perf_df[perf_df['Status'] == 'ok'].copy().reset_index(drop=True)

    # CSV 2: Model B (State-Space) performance and improvement over Model A
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

    # CEH6 dual-panel showdown: TLM vs SSM
    # CEH6 chosen as showcase: TLM drifts to NSE = -1.15 while SSM holds at +0.63,
    # the largest iterative NSE improvement on site (Δ = +1.78).
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
            title='Structural Memory: Iterative R² Improvement (State-Space Gain)',
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
            title='Water Balance Residuals: Iterative NSE Improvement (Anomaly Detection)',
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
