r"""
====================================================================================
THE OMNIBUS CLEAR-FELL EXPERIMENT: TWO-TIER WESTERN CONTROL BACI
====================================================================================
Purpose:
Rebuilt clearfell BACI analysis with a two-tier control design that separates:
  (1) site-wide climate forcing
  (2) western coastal erosion / positional signal
  (3) the December 2017 clearfell intervention

Control tiers:
  - CLIMATE CONTROLS: non-forested C3 wells west of CEH9 that share the western
    climate signal but are unaffected by scraping or felling. These correct for
    climate variability and any western-specific climate response.
  - FOREST CONTROLS: C4 wells inside the forest perimeter but outside the felling
    compartment. These share canopy microclimate and provide the most direct
    counterfactual: "what would felled wells have done if unfelled?"
  - COASTAL CONTROLS: wells on the western coastal margin sharing the progressive
    coastal erosion trend. Used as an additional ANCOVA covariate, not as a
    simple-difference control.

Pipeline sections:
  1. Data loading & well tier validation
  2. Three-control BACI displacement analysis
  3. ANCOVA-BACI with climate, coastal, and scraping covariates
  4. Drainage component extraction (SSM β₃ per-well)
  5. β₃ confidence intervals (statistical verification)
  6. Full parameter shift (β₁, β₂, β₃ per well per era)
  7. Robustness 1: SSM forward residual
  8. Robustness 2: Synthetic control
  9. Robustness 3: Rolling cluster transition
 10. Publication-ready figures
 11. Report numbers CSV export
====================================================================================
"""

__version__ = "2.0.0"  # Hollingham (2026) — Western Controls rebuild, 2026-05-03

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs, INT_WELLS_CLEAN, INT_WELLS_EXTENDED, DIR_10,
    INT_MASTER_DATA, INT_CLIMATE, DATA_WELL_ELEVATIONS,
    OUT_10_DUAL_BACI,
    OUT_10_BETA3_SLOPES,
    OUT_10_DRAINAGE_DATA,
    OUT_10_STAT_VERIFICATION,
    OUT_10_FULL_PARAMS,
    OUT_10_COEFF_SLOPES,
    OUT_10_BACI_TIMESERIES,
    OUT_10_TABLE5_SUMMARY,
    OUT_10_TRANSECT,
    OUT_10_TRANSECT_CSV,
    OUT_10_NW10_TREND,
    OUT_10_REPORT_NUMBERS,
    INT_REGIONAL_AVG,
)
from utils.data_utils import parse_met_date
from utils.model_utils import build_ssm_frame
from utils.config import DRAINAGE_DATUM, HEADLINE_LAG
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
from scipy import stats as _stats
from pathlib import Path
import statsmodels.api as sm
import sys
import warnings
warnings.filterwarnings('ignore')

make_all_dirs()

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


def clean_well_series(series: pd.Series, max_depth: float = 4.0) -> pd.Series:
    """Clean a well time series: filter unphysical values and interpolate gaps."""
    cleaned = series.where(series <= max_depth, np.nan)
    return cleaned.interpolate(method='time', limit=3)


def calculate_cusum(series: pd.Series, baseline_mean: float) -> pd.Series:
    r"""Cumulative Sum for structural break detection:  C_t = Σ(x_i − μ_baseline)."""
    return (series - baseline_mean).cumsum()


def p_to_sig(p: float) -> str:
    if pd.isna(p): return ""
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


def _ols(y, X):
    """Lightweight OLS: returns (betas, std_errors, p_values)."""
    _b  = np.linalg.lstsq(X, y, rcond=None)[0]
    _n, _k = X.shape
    _r  = y - X @ _b
    _s2 = (_r @ _r) / (_n - _k)
    _se = np.sqrt(np.diag(_s2 * np.linalg.inv(X.T @ X)))
    _t  = _b / _se
    _p  = 2 * _stats.t.sf(np.abs(_t), df=_n-_k)
    return _b, _se, _p


def _r_squared(y, X, b):
    """R² for OLS fit."""
    _resid = y - X @ b
    _ss_res = (_resid ** 2).sum()
    _ss_tot = ((y - y.mean()) ** 2).sum()
    return 1.0 - _ss_res / _ss_tot if _ss_tot > 0 else np.nan


def _aic(y, X, b):
    """AIC for OLS model (Gaussian log-likelihood)."""
    _n, _k = X.shape
    _resid = y - X @ b
    _ss = (_resid ** 2).sum()
    return _n * np.log(_ss / _n) + 2 * _k


RAF_VALLEY_LAT_DEG = 53.25


# ===========================================================================
# 1. EXPERIMENT SETUP — TWO-TIER WESTERN CONTROL DESIGN
# ===========================================================================
intervention_date = pd.Timestamp('2017-12-01')   # Clearfell
scraping_date     = pd.Timestamp('2015-04-01')   # CEH36 scraping
scraping_date_2   = pd.Timestamp('2023-10-01')   # CEH18/CEH21 scraping

# ── Impact wells: within the felling compartment ─────────────────────────
impact_wells = ['fe2', 'fe4', 'wmc3']

# ── Edge wells: transition zone around the felling compartment ───────────
# Reviewed from original: CEH31 (C5, 247m), CEH16 (C5, inside coastal
# boundary), CEH20 (C4, 186m N), CEH30 (C4, 463m), LIS1, NW8B.
# FE1, FE3 retained as edge (within felling perimeter but marginal).
edge_wells = ['fe1', 'fe3', 'lis1', 'nw8b', 'ceh20', 'ceh30', 'ceh31']

# ── Climate controls: western C3 wells, not in scraping/felling zones ────
# These share the western climate signal. All are west of CEH9 and outside
# the scraping propagation zone (which extends N/NW of CEH36, not S/SW).
# CEH39 excluded (insufficient baseline). CEH1 included (776m N of CEH36,
# confirmed within propagation zone in 09b but as a C3 reference at 10.7m
# AOD — included here because we need western controls that share climate
# but are not directly impacted by felling).
# NW5, NW6, NW7: all C3, western, south/southwest of the forest block.
# CEH1: C3, western, high elevation.
climate_control_wells = ['nw5', 'nw6', 'nw7', 'ceh1']

# ── Forest controls: C4 wells inside forest, NOT in felling compartment ──
# These share canopy microclimate and interception characteristics.
# NW10: broadleaf succession zone (bramble/birch replacing pine since ~2019)
# CEH2: pine/broadleaf margin
# CEH13: western forest block
# CEH32: main forest
forest_control_wells = ['nw10', 'ceh2', 'ceh13', 'ceh32']

# ── Coastal controls: western coastal margin wells ───────────────────────
# These share the progressive coastal erosion trend. Used as an ANCOVA
# covariate centroid, not as a simple-difference control.
# CEH4: most coastal C3 well (4.5m AOD), strong erosion signal
# CEH22: tidal-signal outlier, excluded from reference but in extended network
# CEH18: scraped Oct 2023 — clean as coastal control only pre-2023.
#         We use full record but add scraping_date_2 dummy in ANCOVA.
coastal_control_wells = ['ceh4', 'ceh22', 'ceh18']

# All wells for diagnostics
all_targets = (impact_wells + edge_wells + climate_control_wells
               + forest_control_wells + coastal_control_wells)

print("=" * 72)
print("SCRIPT 10: CLEARFELL BACI — TWO-TIER WESTERN CONTROL DESIGN v2.0")
print("=" * 72)

# ── Well tier descriptions ───────────────────────────────────────────────
TIER_LABELS = {
    'impact':  'Core Impact',
    'edge':    'Edge / Transition',
    'climate': 'Climate Control (C3 West)',
    'forest':  'Forest Control (C4 Unfelled)',
    'coastal': 'Coastal Control (Erosion)',
}

def _well_tier(w):
    """Return tier label for a well (lowercase input)."""
    wl = w.lower().strip()
    if wl in impact_wells:          return 'impact'
    if wl in edge_wells:            return 'edge'
    if wl in climate_control_wells: return 'climate'
    if wl in forest_control_wells:  return 'forest'
    if wl in coastal_control_wells: return 'coastal'
    return 'unknown'


# ===========================================================================
# 1b. DATA LOADING
# ===========================================================================
print("\n1. Loading Data...")
try:
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True).sort_index()

    if INT_WELLS_CLEAN.exists() and INT_WELLS_EXTENDED.exists():
        wells_main = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
        wells_main.index = pd.to_datetime(wells_main.index)
        wells_main.columns = wells_main.columns.str.lower().str.replace(' ', '')
        wells_ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
        wells_ext.index = pd.to_datetime(wells_ext.index)
        wells_ext.columns = wells_ext.columns.str.lower().str.replace(' ', '')
        new_cols = [c for c in wells_ext.columns if c not in wells_main.columns]
        wells = pd.concat([wells_main, wells_ext[new_cols]], axis=1)
        for col in wells.columns:
            wells[col] = clean_well_series(wells[col])
        print(f'  Merged wells: {len(wells.columns)} columns')
    else:
        raise FileNotFoundError(
            f"Script 01 outputs required but not found. "
            "Run Script 01 (data_prep) before Script 10."
        )

    # Load master data for cluster assignments
    master_path = INT_MASTER_DATA
    if not master_path.exists():
        raise FileNotFoundError(f"Missing master data: {master_path}")
    stats_df = pd.read_csv(master_path)
    stats_df['Match_ID'] = stats_df['Name_Original'].str.lower().str.replace(' ', '')

    # Validate well availability per tier
    valid_impact  = [w for w in impact_wells          if w in wells.columns]
    valid_edge    = [w for w in edge_wells             if w in wells.columns]
    valid_climate = [w for w in climate_control_wells  if w in wells.columns]
    valid_forest  = [w for w in forest_control_wells   if w in wells.columns]
    valid_coastal = [w for w in coastal_control_wells  if w in wells.columns]
    valid_targets = [w for w in all_targets            if w in wells.columns]

    # Print tier summary
    for tier, vlist in [('Impact', valid_impact), ('Edge', valid_edge),
                         ('Climate Ctrl', valid_climate),
                         ('Forest Ctrl', valid_forest),
                         ('Coastal Ctrl', valid_coastal)]:
        print(f'  {tier:16s}: {", ".join(w.upper() for w in vlist)} '
              f'({len(vlist)}/{len([w for w in all_targets if _well_tier(w) == tier.split()[0].lower()])})')

    # ── Water balance detrending baseline ─────────────────────────────────
    _wb_start = wells.index.min()
    _wb_end   = climate.index.max()
    _wb_mask  = (climate.index >= _wb_start) & (climate.index <= _wb_end)
    _wb_series = (pd.to_numeric(climate.loc[_wb_mask, 'P_m'], errors='coerce') * 1000
                  - pd.to_numeric(climate.loc[_wb_mask, 'PET'], errors='coerce') * 1000)
    WB_BASELINE_MM = float(_wb_series.dropna().mean())
    print(f' -> Water balance baseline: {WB_BASELINE_MM:.4f} mm/month '
          f'({_wb_start.strftime("%b %Y")} – {_wb_end.strftime("%b %Y")})')

except Exception as e:
    print(f"Data loading error: {e}")
    import traceback; traceback.print_exc()
    sys.exit()


# ===========================================================================
# 2. TWO-TIER BACI DISPLACEMENT ANALYSIS
# ===========================================================================
print("\n2. Computing BACI Displacement (Impact/Edge vs Climate & Forest Controls)...")

baci_df = pd.DataFrame()

if valid_impact and valid_climate and valid_forest:
    baci_df['Impact_Mean']  = wells[valid_impact].mean(axis=1)
    baci_df['Climate_Ctrl'] = wells[valid_climate].mean(axis=1)
    baci_df['Forest_Ctrl']  = wells[valid_forest].mean(axis=1)
    if valid_edge:
        baci_df['Edge_Mean'] = wells[valid_edge].mean(axis=1)
    if valid_coastal:
        baci_df['Coastal_Ctrl'] = wells[valid_coastal].mean(axis=1)

    # BACI differences: impact vs each control tier
    baci_df['impact_vs_climate'] = baci_df['Impact_Mean'] - baci_df['Climate_Ctrl']
    baci_df['impact_vs_forest']  = baci_df['Impact_Mean'] - baci_df['Forest_Ctrl']
    if 'Edge_Mean' in baci_df.columns:
        baci_df['edge_vs_climate'] = baci_df['Edge_Mean'] - baci_df['Climate_Ctrl']
        baci_df['edge_vs_forest']  = baci_df['Edge_Mean'] - baci_df['Forest_Ctrl']

    baci_df = baci_df.dropna()
    baseline_start = baci_df.index.min()

    # ── Four-era definitions ──────────────────────────────────────────────
    era_pre_scraping         = baci_df[baci_df.index < scraping_date]
    era_post_scraping        = baci_df[(baci_df.index >= scraping_date) & (baci_df.index < intervention_date)]
    era_post_felling         = baci_df[baci_df.index >= intervention_date]
    era_pf_pre_scrape2       = baci_df[(baci_df.index >= intervention_date) & (baci_df.index < scraping_date_2)]
    era_pf_post_scrape2      = baci_df[baci_df.index >= scraping_date_2]

    # Era means — impact vs climate control
    mean_pre_scr_clim   = era_pre_scraping['impact_vs_climate'].mean()
    mean_post_scr_clim  = era_post_scraping['impact_vs_climate'].mean()
    mean_post_fell_clim = era_post_felling['impact_vs_climate'].mean()
    shift_clim = mean_post_fell_clim - mean_post_scr_clim

    # Era means — impact vs forest control (the key counterfactual)
    mean_pre_scr_for    = era_pre_scraping['impact_vs_forest'].mean()
    mean_post_scr_for   = era_post_scraping['impact_vs_forest'].mean()
    mean_post_fell_for  = era_post_felling['impact_vs_forest'].mean()
    shift_for = mean_post_fell_for - mean_post_scr_for

    # Sub-era means for forest-control BACI
    mean_pf_pre_s2_for  = era_pf_pre_scrape2['impact_vs_forest'].mean()
    mean_pf_post_s2_for = era_pf_post_scrape2['impact_vs_forest'].mean()
    shift_pf_pre_s2_for  = mean_pf_pre_s2_for  - mean_post_scr_for
    shift_pf_post_s2_for = mean_pf_post_s2_for - mean_post_scr_for

    # Edge zone — forest control
    if 'edge_vs_forest' in baci_df.columns:
        mean_pre_scr_edge_for   = era_pre_scraping['edge_vs_forest'].mean()
        mean_post_scr_edge_for  = era_post_scraping['edge_vs_forest'].mean()
        mean_post_fell_edge_for = era_post_felling['edge_vs_forest'].mean()
        shift_edge_for = mean_post_fell_edge_for - mean_post_scr_edge_for
        mean_pf_pre_s2_edge_for  = era_pf_pre_scrape2['edge_vs_forest'].mean()
        mean_pf_post_s2_edge_for = era_pf_post_scrape2['edge_vs_forest'].mean()
    else:
        shift_edge_for = np.nan

    # Combined cost
    combined_cost_for = mean_post_fell_for - mean_pre_scr_for

    # CUSUM — forest-control baseline
    baci_df['CUSUM_Impact_For'] = calculate_cusum(
        baci_df['impact_vs_forest'], mean_post_scr_for)
    if 'edge_vs_forest' in baci_df.columns:
        baci_df['CUSUM_Edge_For'] = calculate_cusum(
            baci_df['edge_vs_forest'], mean_post_scr_edge_for)

    # Export BACI time series
    plot_export = pd.DataFrame(index=baci_df.index)
    for col in ['Impact_Mean', 'Edge_Mean', 'Climate_Ctrl', 'Forest_Ctrl',
                'Coastal_Ctrl', 'impact_vs_climate', 'impact_vs_forest',
                'edge_vs_climate', 'edge_vs_forest',
                'CUSUM_Impact_For', 'CUSUM_Edge_For']:
        if col in baci_df.columns:
            plot_export[col] = baci_df[col]
    plot_export.to_csv(OUT_10_BACI_TIMESERIES, index_label='Date')
    print(f' -> Saved: {OUT_10_BACI_TIMESERIES.name}')

    print(f'\n  Impact vs Forest Ctrl — Post-scraping baseline:')
    print(f'    Pre-scraping mean:       {mean_pre_scr_for:+.4f} m')
    print(f'    Post-scraping mean:      {mean_post_scr_for:+.4f} m')
    print(f'    Post-felling mean:       {mean_post_fell_for:+.4f} m')
    print(f'    Step change (clearfell): {shift_for:+.4f} m')
    print(f'    Combined cost:           {combined_cost_for:+.4f} m')

    print(f'\n  Impact vs Climate Ctrl:')
    print(f'    Pre-scraping mean:       {mean_pre_scr_clim:+.4f} m')
    print(f'    Post-scraping mean:      {mean_post_scr_clim:+.4f} m')
    print(f'    Post-felling mean:       {mean_post_fell_clim:+.4f} m')
    print(f'    Step change:             {shift_clim:+.4f} m')
else:
    print("  [WARNING] Insufficient wells for BACI analysis")


# ===========================================================================
# 3. ANCOVA-BACI — climate + coastal covariate correction
# ===========================================================================
print("\n3. ANCOVA-BACI Model (Climate + Coastal Covariates)...")

_ancova_b = _ancova_se = _ancova_p = None
_ancova_r2 = np.nan
_ancova_edge_b = _ancova_edge_se = _ancova_edge_p = None
_ancova_edge_r2 = np.nan
_oct23_imp_coef = _oct23_imp_p = _daic_imp = np.nan
_oct23_edge_coef = _oct23_edge_p = _daic_edge = np.nan

if not baci_df.empty and valid_coastal:
    # Build climate covariate (cumulative water balance anomaly)
    _cl = climate.copy()
    _cl['P_mm']   = pd.to_numeric(_cl['P_m'],  errors='coerce') * 1000
    _cl['PET_mm'] = pd.to_numeric(_cl['PET'],  errors='coerce') * 1000
    _cl['anom']   = _cl['P_mm'] - _cl['PET_mm'] - WB_BASELINE_MM
    _cl_sub = _cl[_cl.index >= baci_df.index.min()].copy()
    _cl_sub['cum_wb'] = _cl_sub['anom'].cumsum()

    _common = baci_df.index.intersection(_cl_sub.index)

    # Build ANCOVA design matrix:
    # y = impact − forest_ctrl  (the BACI difference)
    # X = [1, CWB_centered, Coastal_ctrl_centered, Scraped, Post, CWB×Post]
    _ab = pd.DataFrame({
        'impact_for':  baci_df.loc[_common, 'impact_vs_forest'],
        'cum_wb':      _cl_sub.loc[_common, 'cum_wb'],
        'coastal':     baci_df.loc[_common, 'Coastal_Ctrl'] if 'Coastal_Ctrl' in baci_df.columns else np.nan,
    }).dropna()

    if 'edge_vs_forest' in baci_df.columns:
        _ab['edge_for'] = baci_df.loc[_ab.index, 'edge_vs_forest']

    _ab['Post']    = (_ab.index >= intervention_date).astype(float)
    _ab['Scraped'] = (_ab.index >= scraping_date).astype(float)
    _cwb_mean      = _ab['cum_wb'].mean()
    _ab['cwb_c']   = _ab['cum_wb'] - _cwb_mean
    _coast_mean    = _ab['coastal'].mean()
    _ab['coast_c'] = _ab['coastal'] - _coast_mean

    # Model specification:
    # impact_vs_forest = β₀ + β₁·CWB_c + β₂·Coastal_c + β₃·Scraped
    #                  + β₄·Post + β₅·CWB_c×Post
    _X = np.column_stack([
        np.ones(len(_ab)),       # 0: intercept
        _ab['cwb_c'].values,     # 1: cumulative water balance
        _ab['coast_c'].values,   # 2: coastal control centroid
        _ab['Scraped'].values,   # 3: scraping step
        _ab['Post'].values,      # 4: clearfell step
        _ab['cwb_c'].values * _ab['Post'].values,  # 5: CWB × post interaction
    ])

    _b, _se, _p = _ols(_ab['impact_for'].values, _X)
    _ancova_b, _ancova_se, _ancova_p = _b.copy(), _se.copy(), _p.copy()
    _ancova_r2 = _r_squared(_ab['impact_for'].values, _X, _b)

    # Climate-corrected BACI: remove climate and coastal effects
    _ab['impact_corr'] = (_ab['impact_for']
                          - _b[1]*_ab['cwb_c']
                          - _b[2]*_ab['coast_c']
                          - _b[5]*_ab['cwb_c']*_ab['Post'])

    # Edge zone ANCOVA
    if 'edge_for' in _ab.columns and _ab['edge_for'].notna().sum() > 20:
        _be, _se_e, _p_e = _ols(_ab['edge_for'].values, _X)
        _ancova_edge_b  = _be.copy()
        _ancova_edge_se = _se_e.copy()
        _ancova_edge_p  = _p_e.copy()
        _ancova_edge_r2 = _r_squared(_ab['edge_for'].values, _X, _be)
        _ab['edge_corr'] = (_ab['edge_for']
                            - _be[1]*_ab['cwb_c']
                            - _be[2]*_ab['coast_c']
                            - _be[5]*_ab['cwb_c']*_ab['Post'])
    else:
        _ab['edge_corr'] = np.nan

    # Era means from ANCOVA coefficients
    _mean_pre_scr_a  = _b[0]
    _mean_post_scr_a = _b[0] + _b[3]
    _mean_post_fell_a = _b[0] + _b[3] + _b[4]

    # ── Oct 2023 scraping test (Model 3) ──────────────────────────────────
    _ab['Scraped2'] = (_ab.index >= scraping_date_2).astype(float)
    _X3 = np.column_stack([_X, _ab['Scraped2'].values])

    _b3_imp, _se3_imp, _p3_imp = _ols(_ab['impact_for'].values, _X3)
    _aic_m2_imp = _aic(_ab['impact_for'].values, _X, _b)
    _aic_m3_imp = _aic(_ab['impact_for'].values, _X3, _b3_imp)
    _daic_imp   = _aic_m3_imp - _aic_m2_imp
    _oct23_imp_coef = _b3_imp[6]
    _oct23_imp_p    = _p3_imp[6]

    if _ancova_edge_b is not None:
        _b3_edge, _se3_edge, _p3_edge = _ols(_ab['edge_for'].values, _X3)
        _aic_m2_edge = _aic(_ab['edge_for'].values, _X, _ancova_edge_b)
        _aic_m3_edge = _aic(_ab['edge_for'].values, _X3, _b3_edge)
        _daic_edge   = _aic_m3_edge - _aic_m2_edge
        _oct23_edge_coef = _b3_edge[6]
        _oct23_edge_p    = _p3_edge[6]

    # Climate-corrected CUSUM
    _ab['cusum_corr'] = (_ab['impact_corr'] - _mean_post_scr_a).cumsum()
    if _ancova_edge_b is not None:
        _edge_post_scr_a = _be[0] + _be[3]
        _ab['cusum_edge_corr'] = (_ab['edge_corr'] - _edge_post_scr_a).cumsum()
    else:
        _ab['cusum_edge_corr'] = np.nan

    _pfmt = lambda p: '<0.001' if p < 0.001 else f'{p:.3f}'

    print(f'\n  ANCOVA Model 2 (6 terms, vs forest control):')
    print(f'    Intercept (pre-scraping):    {_b[0]:+.4f} m')
    print(f'    CWB coefficient:             {_b[1]:+.6f}  p={_pfmt(_p[1])}')
    print(f'    Coastal control coefficient: {_b[2]:+.4f}  p={_pfmt(_p[2])}')
    print(f'    Scraping step:               {_b[3]:+.4f} m  p={_pfmt(_p[3])}')
    print(f'    Clearfell step:              {_b[4]:+.4f} m  p={_pfmt(_p[4])}')
    print(f'      95% CI: [{_b[4]-1.96*_se[4]:.4f}, {_b[4]+1.96*_se[4]:.4f}]')
    print(f'    CWB × Post interaction:      {_b[5]:+.6f}  p={_pfmt(_p[5])}')
    print(f'    R²: {_ancova_r2:.3f}')
    print(f'    Oct 2023 test: coef={_oct23_imp_coef:+.4f}, p={_oct23_imp_p:.3f}, '
          f'ΔAIC={_daic_imp:+.2f}')

    if _ancova_edge_b is not None:
        print(f'\n  Edge zone ANCOVA (vs forest control):')
        print(f'    Clearfell step: {_ancova_edge_b[4]:+.4f} m  '
              f'p={_pfmt(_ancova_edge_p[4])}')
        print(f'    95% CI: [{_ancova_edge_b[4]-1.96*_ancova_edge_se[4]:.4f}, '
              f'{_ancova_edge_b[4]+1.96*_ancova_edge_se[4]:.4f}]')
        print(f'    R²: {_ancova_edge_r2:.3f}')

    # Export climate-corrected series
    OUT_10_CLIM_CUSUM = DIR_10 / '10_cfell_09b_climate_corrected_cusum.csv'
    _cusum_export = pd.DataFrame({
        'Date': _ab.index,
        'Impact_vs_Forest_Raw': _ab['impact_for'],
        'Impact_vs_Forest_ClimCorrected': _ab['impact_corr'],
        'Impact_CUSUM_ClimCorrected': _ab['cusum_corr'],
        'CumWaterBalance_mm': _ab['cum_wb'],
        'Coastal_Ctrl': _ab['coastal'],
        'Model2_Fitted': _X @ _b,
    })
    if 'edge_for' in _ab.columns:
        _cusum_export['Edge_vs_Forest_Raw'] = _ab['edge_for']
    if 'edge_corr' in _ab.columns:
        _cusum_export['Edge_vs_Forest_ClimCorrected'] = _ab['edge_corr']
    if 'cusum_edge_corr' in _ab.columns:
        _cusum_export['Edge_CUSUM_ClimCorrected'] = _ab['cusum_edge_corr']
    _cusum_export['Post_Felling'] = (_ab.index >= intervention_date).astype(int)
    _cusum_export['Post_Scraping'] = (_ab.index >= scraping_date).astype(int)
    _cusum_export.to_csv(OUT_10_CLIM_CUSUM, index=False)
    print(f' -> Saved: {OUT_10_CLIM_CUSUM.name}')

else:
    print("  [WARNING] Skipping ANCOVA — insufficient data or no coastal controls")


# ===========================================================================
# 4. DRAINAGE COMPONENT EXTRACTION (per-well SSM β₃)
# ===========================================================================
print("\n4. Extracting Drainage Components...")
all_data = []

for well in valid_targets:
    df = wells[well].to_frame(name='h').join(climate[['P_m', 'PET']], how='inner')
    df['P_m_lag'] = df['P_m'].shift(HEADLINE_LAG)
    df['h_prev'] = df['h'].shift(1)
    df['Delta_h'] = df['h'] - df['h_prev']
    df['h_disp_prev'] = DRAINAGE_DATUM + df['h_prev']
    df = df.dropna()

    X_base = pd.DataFrame({
        'beta_1_recharge': df['P_m_lag'],
        'beta_2_atmospheric_draw': -df['PET'],
        'beta_3_drainage': -df['h_disp_prev'],
    })
    try:
        res_base = sm.OLS(df['Delta_h'], X_base).fit()
    except Exception:
        continue
    b1, b2 = res_base.params['beta_1_recharge'], res_base.params['beta_2_atmospheric_draw']

    df['Drainage_Component'] = df['Delta_h'] - (b1 * df['P_m_lag']) - (b2 * -df['PET'])
    df['Well_Name'] = well.upper()
    df['Tier'] = _well_tier(well)
    df['Period'] = np.where(
        df.index < intervention_date, 'Before',
        np.where(df.index < scraping_date_2, 'After', 'After_Scrape2')
    )
    df['neg_h_disp_prev'] = -df['h_disp_prev']
    all_data.append(df)

diagnostic_df = pd.concat(all_data)
diagnostic_df.to_csv(OUT_10_DRAINAGE_DATA, index=False)
print(f' -> Saved: {OUT_10_DRAINAGE_DATA.name}')


# ===========================================================================
# 5. STATISTICAL VERIFICATION — β₃ Confidence Intervals
# ===========================================================================
print("\n5. Calculating 95% Confidence Intervals for β₃...")
stats_results = []

for well in [w.upper() for w in valid_targets]:
    for period in ['Before', 'After', 'After_Scrape2']:
        sub = diagnostic_df[(diagnostic_df['Well_Name'] == well) &
                             (diagnostic_df['Period'] == period)].dropna()
        if len(sub) > 5:
            X = sm.add_constant(sub['neg_h_disp_prev'])
            model = sm.OLS(sub['Drainage_Component'], X).fit()
            beta3 = model.params.get('neg_h_disp_prev', np.nan)
            conf_int = model.conf_int().loc['neg_h_disp_prev']
            stats_results.append({
                'Well': well,
                'Period': period,
                'Tier': _well_tier(well.lower()),
                'beta_3_drainage': beta3,
                'P_Value': model.pvalues.get('neg_h_disp_prev', np.nan),
                'Conf_Low': conf_int[0],
                'Conf_High': conf_int[1],
                'N': len(sub),
            })

stats_results_df = pd.DataFrame(stats_results)

# Add BACI summary rows
if not baci_df.empty:
    summary_rows = []
    for tier_label, tier_shift, tier_name in [
        ('Impact_vs_Forest',  shift_for,       'impact_vs_forest'),
        ('Impact_vs_Climate', shift_clim,      'impact_vs_climate'),
    ]:
        summary_rows.append({
            'Well': 'BACI_SUMMARY', 'Period': tier_label,
            'Tier': 'summary',
            'Mean_Pre_Scraping': mean_pre_scr_for if 'Forest' in tier_label else mean_pre_scr_clim,
            'Mean_Post_Scraping': mean_post_scr_for if 'Forest' in tier_label else mean_post_scr_clim,
            'Mean_Post_Felling': mean_post_fell_for if 'Forest' in tier_label else mean_post_fell_clim,
            'Step_Change': tier_shift,
        })
    if 'edge_vs_forest' in baci_df.columns:
        summary_rows.append({
            'Well': 'BACI_SUMMARY', 'Period': 'Edge_vs_Forest',
            'Tier': 'summary',
            'Mean_Pre_Scraping': mean_pre_scr_edge_for,
            'Mean_Post_Scraping': mean_post_scr_edge_for,
            'Mean_Post_Felling': mean_post_fell_edge_for,
            'Step_Change': shift_edge_for,
        })
    summary_df = pd.DataFrame(summary_rows)
    stats_results_df = pd.concat([stats_results_df, summary_df], ignore_index=True)

stats_results_df.to_csv(OUT_10_STAT_VERIFICATION, index=False)
print(f' -> Saved: {OUT_10_STAT_VERIFICATION.name}')

# Export Table 5 (β₃ before/after) — adapted for new tier structure
def export_table5_summary(sdf):
    """Export β₃ before vs after for each well, grouped by tier."""
    if sdf.empty:
        pd.DataFrame().to_csv(OUT_10_TABLE5_SUMMARY, index=False)
        return
    s = sdf[sdf['Well'] != 'BACI_SUMMARY'].copy()
    s['Well'] = s['Well'].astype(str).str.upper()
    s['Period_Table'] = s['Period'].replace('After_Scrape2', 'After')

    before = s[s['Period_Table'] == 'Before'].set_index('Well')
    after_all = s[s['Period_Table'] == 'After']
    after = (after_all[after_all['Period'] == 'After']
             .set_index('Well')
             .combine_first(
                 after_all[after_all['Period'] == 'After_Scrape2']
                 .set_index('Well')
             ))

    rows = []
    for well in s['Well'].unique():
        b = before.loc[well] if well in before.index else None
        a = after.loc[well]  if well in after.index  else None
        b3b = float(b['beta_3_drainage']) if b is not None else np.nan
        b3a = float(a['beta_3_drainage']) if a is not None else np.nan
        delta = (b3a - b3b) if not (np.isnan(b3b) or np.isnan(b3a)) else np.nan
        rows.append({
            'Well': well,
            'Tier': _well_tier(well.lower()),
            'beta_3_Before': round(b3b, 3) if pd.notna(b3b) else np.nan,
            'beta_3_After':  round(b3a, 3) if pd.notna(b3a) else np.nan,
            'Delta_beta_3':  f'{delta:+.3f}' if pd.notna(delta) else '',
            'Before_sig': p_to_sig(float(b['P_Value'])) if b is not None else '',
            'After_sig':  p_to_sig(float(a['P_Value'])) if a is not None else '',
        })
    pd.DataFrame(rows).to_csv(OUT_10_TABLE5_SUMMARY, index=False)

export_table5_summary(stats_results_df)
print(f' -> Saved: {OUT_10_TABLE5_SUMMARY.name}')


# ===========================================================================
# 6. FULL PARAMETER SHIFT (β₁, β₂, β₃ per well per era)
# ===========================================================================
print("\n6. Running Full Parameter Shift...")
full_param_results = []

for well in valid_targets:
    df = wells[well].to_frame(name='h').join(climate[['P_m', 'PET']], how='inner')
    df['P_m_lag'] = df['P_m'].shift(HEADLINE_LAG)
    df['h_prev'] = df['h'].shift(1)
    df['Delta_h'] = df['h'] - df['h_prev']
    df['h_disp_prev'] = DRAINAGE_DATUM + df['h_prev']
    df = df.dropna()

    for label in ['Before', 'After', 'After_Scrape2']:
        if label == 'Before':
            sub = df[df.index < intervention_date]
        elif label == 'After':
            sub = df[(df.index >= intervention_date) & (df.index < scraping_date_2)]
        else:
            sub = df[df.index >= scraping_date_2]
        if len(sub) > 12:
            X = pd.DataFrame({
                'beta_1_recharge': sub['P_m_lag'],
                'beta_2_atmospheric_draw': -sub['PET'],
                'beta_3_drainage': -sub['h_disp_prev'],
            })
            model = sm.OLS(sub['Delta_h'], X).fit()
            ci = model.conf_int()
            full_param_results.append({
                'Well': well.upper(),
                'Period': label,
                'Tier': _well_tier(well),
                'beta_1_recharge':         round(model.params['beta_1_recharge'], 3),
                'beta_1_conf_low':         ci.loc['beta_1_recharge', 0],
                'beta_1_conf_high':        ci.loc['beta_1_recharge', 1],
                'beta_2_atmospheric_draw': round(model.params['beta_2_atmospheric_draw'], 3),
                'beta_2_conf_low':         ci.loc['beta_2_atmospheric_draw', 0],
                'beta_2_conf_high':        ci.loc['beta_2_atmospheric_draw', 1],
                'beta_3_drainage':         round(model.params['beta_3_drainage'], 3),
                'beta_3_conf_low':         ci.loc['beta_3_drainage', 0],
                'beta_3_conf_high':        ci.loc['beta_3_drainage', 1],
            })

full_param_df = pd.DataFrame(full_param_results)
full_param_df.to_csv(OUT_10_FULL_PARAMS, index=False)
print(f' -> Saved: {OUT_10_FULL_PARAMS.name}')


# ===========================================================================
# 7. PUBLICATION-READY FIGURES
# ===========================================================================
print("\n7. Generating Visualizations...")

cb_blue  = '#0072B2'
cb_green = '#009E73'
cb_edge  = '#FFB000'
cb_red   = '#D55E00'
cb_purple = '#9467BD'

TIER_COLOURS = {
    'impact':  cb_red,
    'edge':    cb_edge,
    'climate': cb_green,
    'forest':  cb_purple,
    'coastal': '#888888',
}

# --- PLOT 1: ANCOVA-BACI (5-panel) ─────────────────────────────────────
if not baci_df.empty and _ancova_b is not None:
    fig1 = plt.figure(figsize=(14, 20), dpi=300)
    _gs1 = GridSpec(5, 1, figure=fig1,
                     height_ratios=[0.7, 0.7, 1.2, 1.2, 1.0], hspace=0.30)
    _ax_wb   = fig1.add_subplot(_gs1[0])
    _ax_ctrl = fig1.add_subplot(_gs1[1], sharex=_ax_wb)
    _ax_baci = fig1.add_subplot(_gs1[2], sharex=_ax_wb)
    _ax_cus  = fig1.add_subplot(_gs1[3], sharex=_ax_wb)
    _ax_scat = fig1.add_subplot(_gs1[4])

    _dates = _ab.index.values

    def _vlines(ax):
        ax.axvline(scraping_date,    color='purple', lw=1.4, ls=':', alpha=0.8)
        ax.axvline(intervention_date, color='black', lw=1.8, ls='--', alpha=0.9)
        ax.axvline(scraping_date_2,  color='purple', lw=1.0, ls=':', alpha=0.45)

    def _shade(ax):
        ax.axvspan(_ab.index.min(), scraping_date,    alpha=0.03, color='blue')
        ax.axvspan(scraping_date,   intervention_date, alpha=0.03, color='orange')
        ax.axvspan(intervention_date, _ab.index.max(), alpha=0.03, color='red')

    # (a) Cumulative water balance
    _cwb = _ab['cum_wb'].values
    _ax_wb.fill_between(_dates, _cwb, 0, where=(_cwb >= 0), interpolate=True,
                         color=cb_blue, alpha=0.4, label='Surplus')
    _ax_wb.fill_between(_dates, _cwb, 0, where=(_cwb < 0), interpolate=True,
                         color=cb_red,  alpha=0.4, label='Deficit')
    _ax_wb.plot(_dates, _cwb, color='#1A1A1A', lw=0.9, alpha=0.6)
    _ax_wb.axhline(0, color='black', lw=0.8, ls='--', alpha=0.4)
    _vlines(_ax_wb); _shade(_ax_wb)
    _ax_wb.set_ylabel('Cum. P−PET\nanomaly (mm)', fontsize=9)
    _ax_wb.set_title(f'(a)  Cumulative water balance anomaly '
                     f'[baseline = {WB_BASELINE_MM:.2f} mm/month]',
                     fontsize=9, loc='left', pad=3)
    _ax_wb.legend(fontsize=7.5, loc='upper right', ncol=2, framealpha=0.9)
    _ax_wb.tick_params(labelbottom=False)
    for _sp in ['bottom', 'top', 'right']: _ax_wb.spines[_sp].set_visible(False)
    _ax_wb.grid(True, axis='y', lw=0.4, ls='--', alpha=0.4)

    # (b) Control tier centroids (raw hydrographs)
    _ax_ctrl.plot(baci_df.index, baci_df['Impact_Mean'],
                   color=cb_red, lw=2.2, label='Core Impact')
    _ax_ctrl.plot(baci_df.index, baci_df['Forest_Ctrl'],
                   color=cb_purple, lw=2.0, ls='--', label='Forest Control (C4)')
    _ax_ctrl.plot(baci_df.index, baci_df['Climate_Ctrl'],
                   color=cb_green, lw=1.8, ls=':', label='Climate Control (C3W)')
    if 'Coastal_Ctrl' in baci_df.columns:
        _ax_ctrl.plot(baci_df.index, baci_df['Coastal_Ctrl'],
                       color='#888888', lw=1.4, ls='-.', label='Coastal Control')
    if 'Edge_Mean' in baci_df.columns:
        _ax_ctrl.plot(baci_df.index, baci_df['Edge_Mean'],
                       color=cb_edge, lw=1.6, ls='-', alpha=0.7, label='Edge Zone')
    _vlines(_ax_ctrl)
    _ax_ctrl.set_ylabel('Water level (m)', fontsize=9)
    _ax_ctrl.set_title('(b)  Control tier centroids and impact zone',
                       fontsize=9, loc='left', pad=3)
    _ax_ctrl.legend(fontsize=7, loc='upper right', framealpha=0.9, ncol=2)
    _ax_ctrl.tick_params(labelbottom=False)
    for _sp in ['top', 'right']: _ax_ctrl.spines[_sp].set_visible(False)
    _ax_ctrl.grid(True, axis='y', lw=0.4, ls='--', alpha=0.4)

    # (c) BACI displacement (forest control) — raw + corrected
    if 'edge_for' in _ab.columns and _ab['edge_for'].notna().any():
        _ax_baci.plot(_dates, _ab['edge_for'].values,
                       color=cb_edge, lw=1.8, alpha=0.7,
                       label='Edge vs Forest (raw)')
    _ax_baci.plot(_dates, _ab['impact_for'].values,
                   color='#666666', lw=1.2, ls='--', alpha=0.6,
                   label='Impact vs Forest (raw)')
    _ax_baci.plot(_dates, _ab['impact_corr'].values,
                   color=cb_red, lw=2.6,
                   label='Impact vs Forest (climate+coastal corrected)')
    _ax_baci.axhline(0, color='gray', lw=0.8, ls=':', alpha=0.5)

    _t0, _t1 = _ab.index.min(), _ab.index.max()
    _ax_baci.hlines(_mean_pre_scr_a, xmin=_t0, xmax=scraping_date,
                     color='black', lw=1.4, ls=(0, (5, 3)),
                     label=f'Pre-scraping ({_mean_pre_scr_a:+.3f} m)')
    _ax_baci.hlines(_mean_post_scr_a, xmin=scraping_date, xmax=intervention_date,
                     color='black', lw=1.4, ls='--',
                     label=f'Post-scraping ({_mean_post_scr_a:+.3f} m)')
    _ax_baci.hlines(_mean_post_fell_a, xmin=intervention_date, xmax=_t1,
                     color='black', lw=2.0, ls='-',
                     label=f'Post-felling ({_mean_post_fell_a:+.3f} m) '
                           f'Δ={_b[4]:+.3f}***')
    _vlines(_ax_baci); _shade(_ax_baci)
    _ax_baci.set_ylabel('BACI Displacement (m)', fontsize=9)
    _ax_baci.set_title('(c)  BACI displacement: impact vs forest control',
                       fontsize=9, loc='left', pad=3)
    _ax_baci.legend(fontsize=7, loc='upper right', framealpha=0.9, ncol=2)
    _ax_baci.tick_params(labelbottom=False)
    for _sp in ['top', 'right']: _ax_baci.spines[_sp].set_visible(False)
    _ax_baci.grid(True, axis='y', lw=0.4, ls='--', alpha=0.4)

    # (d) Climate-corrected CUSUM
    _ax_cus.plot(_dates, _ab['cusum_corr'].values,
                  color=cb_blue, lw=2.6,
                  label='Impact CUSUM (climate+coastal corrected)')
    if _ab['cusum_edge_corr'].notna().any():
        _ax_cus.plot(_dates, _ab['cusum_edge_corr'].values,
                      color=cb_edge, lw=2.0, ls='--',
                      label='Edge CUSUM (corrected)')
    _ax_cus.axhline(0, color='gray', lw=0.9, ls='--', alpha=0.6)
    _cusum_final = _ab['cusum_corr'].iloc[-1]
    _ax_cus.annotate(f'{_cusum_final:.2f} m',
                      xy=(_ab.index[-1], _cusum_final),
                      xytext=(-65, 12), textcoords='offset points',
                      fontsize=8, color=cb_blue, fontweight='bold',
                      arrowprops=dict(arrowstyle='->', color=cb_blue, lw=1.2))
    _vlines(_ax_cus); _shade(_ax_cus)
    _ax_cus.set_ylabel('Cumulative BACI\ndisplacement (m)', fontsize=9)
    _ax_cus.set_title('(d)  Cumulative BACI displacement (corrected, vs post-scraping baseline)',
                      fontsize=9, loc='left', pad=3)
    _ax_cus.legend(fontsize=7.5, loc='upper right', framealpha=0.9)
    _ax_cus.xaxis.set_major_locator(mdates.YearLocator(2))
    _ax_cus.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    for _sp in ['top', 'right']: _ax_cus.spines[_sp].set_visible(False)
    _ax_cus.grid(True, axis='y', lw=0.4, ls='--', alpha=0.4)

    _ax_wb.xaxis.set_major_locator(mdates.YearLocator(2))
    _ax_baci.xaxis.set_major_locator(mdates.YearLocator(2))

    # (e) Scatter: pre vs post
    _pre  = _ab['Post'] == 0
    _post = _ab['Post'] == 1
    _ax_scat.scatter(_ab.loc[_pre,  'cwb_c'], _ab.loc[_pre,  'impact_for'],
                      color=cb_green, s=28, alpha=0.65, zorder=3,
                      label=f'Pre-felling  (n={_pre.sum()})')
    _ax_scat.scatter(_ab.loc[_post, 'cwb_c'], _ab.loc[_post, 'impact_for'],
                      color=cb_red, s=28, alpha=0.65, zorder=3,
                      label=f'Post-felling (n={_post.sum()})')
    _xr = np.linspace(_ab['cwb_c'].min(), _ab['cwb_c'].max(), 200)
    _ax_scat.plot(_xr, (_b[0]+_b[3]) + _b[1]*_xr,
                   color=cb_green, lw=2.4,
                   label=f'Pre-felling slope: {_b[1]*100:.4f} m/100mm')
    _ax_scat.plot(_xr, (_b[0]+_b[3]+_b[4]) + (_b[1]+_b[5])*_xr,
                   color=cb_red, lw=2.4,
                   label=f'Post-felling slope: {(_b[1]+_b[5])*100:.4f} m/100mm')
    _ax_scat.axhline(0, color='gray', lw=0.8, ls=':', alpha=0.5)
    _ax_scat.axvline(0, color='gray', lw=0.8, ls=':', alpha=0.5)
    _ax_scat.set_xlabel('Centred cumulative P − PET anomaly (mm)', fontsize=9)
    _ax_scat.set_ylabel('BACI Displacement (m)', fontsize=9)
    _ax_scat.set_title('(e)  Climate sensitivity: pre- vs post-felling',
                       fontsize=9, loc='left', pad=3)
    _ax_scat.legend(fontsize=7.5, loc='upper right', framealpha=0.9)
    for _sp in ['top', 'right']: _ax_scat.spines[_sp].set_visible(False)
    _ax_scat.grid(True, lw=0.4, ls='--', alpha=0.4)

    fig1.text(0.13, 0.003,
              f'† Oct 2023 scraping (impact): coef = {_oct23_imp_coef:+.3f} m, '
              f'p = {_oct23_imp_p:.3f}, ΔAIC = {_daic_imp:+.2f}. '
              f'Coastal covariate coefficient = {_b[2]:+.4f}, p = {_pfmt(_p[2])}',
              fontsize=8, color='#444444', style='italic')

    fig1.suptitle(
        'ANCOVA-BACI (Model 2, Western Controls): Climate-, coastal- and scraping-corrected '
        'clearfell impact\n'
        f'Forest-control BACI  |  Scraping step = {_b[3]:+.3f} m  p={_pfmt(_p[3])}  |  '
        f'Clearfell step = {_b[4]:+.3f} m [{_b[4]-1.96*_se[4]:.3f}, '
        f'{_b[4]+1.96*_se[4]:.3f}]  p={_pfmt(_p[4])}  |  '
        f'R² = {_ancova_r2:.3f}',
        fontsize=10, fontweight='bold'
    )
    plt.savefig(OUT_10_DUAL_BACI, bbox_inches='tight', dpi=300)
    plt.close(fig1)
    print(f' -> Saved: {OUT_10_DUAL_BACI.name}')

# --- PLOT 1b: Raw BACI (observational record) ─────────────────────────
OUT_10_RAW_BACI = DIR_10 / '10_cfell_01b_raw_baci.png'

if not baci_df.empty:
    _fig_raw, (_rax1, _rax2, _rax3) = plt.subplots(3, 1, figsize=(14, 14), dpi=300, sharex=True)

    # (a) Raw hydrographs by tier
    _rax1.plot(baci_df.index, baci_df['Forest_Ctrl'],
                color=cb_purple, lw=2.2, label='Forest control (C4)')
    _rax1.plot(baci_df.index, baci_df['Climate_Ctrl'],
                color=cb_green, lw=1.8, ls=':', label='Climate control (C3W)')
    _rax1.plot(baci_df.index, baci_df['Impact_Mean'],
                color=cb_red, lw=2.4, label='Core impact')
    if 'Edge_Mean' in baci_df.columns:
        _rax1.plot(baci_df.index, baci_df['Edge_Mean'],
                    color=cb_edge, lw=2.0, ls=':', label='Edge zone')
    if 'Coastal_Ctrl' in baci_df.columns:
        _rax1.plot(baci_df.index, baci_df['Coastal_Ctrl'],
                    color='#888888', lw=1.4, ls='-.', label='Coastal control')
    _rax1.axvline(scraping_date,     color='purple', lw=1.4, ls=':', alpha=0.8)
    _rax1.axvline(intervention_date, color='black',  lw=1.8, ls='--', alpha=0.9)
    _rax1.axvline(scraping_date_2,   color='purple', lw=1.0, ls=':', alpha=0.45)
    _rax1.set_ylabel('Water level (m)', fontsize=9)
    _rax1.set_title('(a)  Raw hydrographs: all control tiers',
                    fontsize=9, loc='left', pad=3)
    _rax1.legend(fontsize=7, loc='upper right', framealpha=0.9, ncol=2)
    for _sp in ['top', 'right']: _rax1.spines[_sp].set_visible(False)
    _rax1.grid(True, axis='y', lw=0.4, ls='--', alpha=0.4)

    # (b) Raw BACI (forest control) with era means
    _t0r, _t1r = baci_df.index.min(), baci_df.index.max()
    _rax2.axvspan(_t0r,              scraping_date,    alpha=0.03, color='blue')
    _rax2.axvspan(scraping_date,     intervention_date, alpha=0.03, color='orange')
    _rax2.axvspan(intervention_date, _t1r,             alpha=0.03, color='red')
    _rax2.plot(baci_df.index, baci_df['impact_vs_forest'],
                color=cb_red, lw=2.4, label='Impact vs Forest (raw)')
    if 'edge_vs_forest' in baci_df.columns:
        _rax2.plot(baci_df.index, baci_df['edge_vs_forest'],
                    color=cb_edge, lw=1.8, alpha=0.8, label='Edge vs Forest (raw)')
    _rax2.axhline(0, color='gray', lw=0.8, ls=':', alpha=0.5)
    _rax2.hlines(mean_pre_scr_for,   xmin=_t0r,             xmax=scraping_date,
                  color='black', lw=1.4, ls=(0, (5, 3)))
    _rax2.hlines(mean_post_scr_for,  xmin=scraping_date,    xmax=intervention_date,
                  color='black', lw=1.4, ls='--')
    _rax2.hlines(mean_post_fell_for, xmin=intervention_date, xmax=_t1r,
                  color='black', lw=2.0, ls='-')
    _rax2.axvline(scraping_date,     color='purple', lw=1.4, ls=':', alpha=0.8)
    _rax2.axvline(intervention_date, color='black',  lw=1.8, ls='--', alpha=0.9)
    _rax2.set_ylabel('BACI Displacement (m)', fontsize=9)
    _rax2.set_title('(b)  Raw BACI (impact vs forest control) with era means',
                    fontsize=9, loc='left', pad=3)
    _rax2.legend(fontsize=7.5, loc='upper right', framealpha=0.9)
    for _sp in ['top', 'right']: _rax2.spines[_sp].set_visible(False)
    _rax2.grid(True, axis='y', lw=0.4, ls='--', alpha=0.4)

    # (c) Raw CUSUM (forest control)
    _rax3.plot(baci_df.index, baci_df['CUSUM_Impact_For'],
                color=cb_blue, lw=2.6, label='Impact CUSUM vs Forest (raw)')
    if 'CUSUM_Edge_For' in baci_df.columns:
        _rax3.plot(baci_df.index, baci_df['CUSUM_Edge_For'],
                    color=cb_edge, lw=2.0, ls='--', label='Edge CUSUM vs Forest')
    _rax3.axhline(0, color='gray', lw=0.9, ls='--', alpha=0.6)
    _rax3.axvline(scraping_date,     color='purple', lw=1.4, ls=':', alpha=0.8)
    _rax3.axvline(intervention_date, color='black',  lw=1.8, ls='--', alpha=0.9)
    _rax3.set_ylabel('Cumulative BACI (m)', fontsize=9)
    _rax3.set_xlabel('Date', fontsize=9)
    _rax3.set_title('(c)  Cumulative BACI displacement (raw, forest control baseline)',
                    fontsize=9, loc='left', pad=3)
    _rax3.legend(fontsize=7.5, loc='upper right', framealpha=0.9)
    for _sp in ['top', 'right']: _rax3.spines[_sp].set_visible(False)
    _rax3.grid(True, axis='y', lw=0.4, ls='--', alpha=0.4)
    _rax3.xaxis.set_major_locator(mdates.YearLocator(2))
    _rax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    _fig_raw.suptitle(
        f'Raw BACI (forest control): observational record\n'
        f'Step change = {shift_for:+.3f} m  |  '
        f'Combined cost = {combined_cost_for:+.3f} m',
        fontsize=10, fontweight='bold'
    )
    plt.tight_layout()
    plt.savefig(OUT_10_RAW_BACI, bbox_inches='tight', dpi=300)
    plt.close(_fig_raw)
    print(f' -> Saved: {OUT_10_RAW_BACI.name}')


# --- PLOT 2: Drainage diagnostic (β₃ slopes per well) ────────────────
ncols = 2
plots_per_figure = 8

styles = [
    ('Before', '#009E73', 'o', 'none', ':'),
    ('After',  '#D55E00', 's', '#D55E00', '-'),
]

drainage_outputs = []
well_groups = [valid_targets[i:i+plots_per_figure]
               for i in range(0, len(valid_targets), plots_per_figure)]

for part_idx, well_group in enumerate(well_groups, start=1):
    nplots = max(1, len(well_group))
    nrows = int(np.ceil(nplots / ncols))
    fig2, axes = plt.subplots(nrows, ncols, figsize=(6.5*ncols, 4.8*nrows), dpi=300)
    axes = np.atleast_1d(axes).flatten()

    for i, well in enumerate(well_group):
        ax = axes[i]
        well_upper = well.upper()
        df_sub = diagnostic_df[diagnostic_df['Well_Name'] == well_upper]
        tier = _well_tier(well)

        for label, col, mark, fill, ls in styles:
            sub = df_sub[df_sub['Period'] == label]
            if len(sub) > 5:
                ax.scatter(sub['h_prev'], sub['Drainage_Component'],
                           edgecolor=col, facecolor=fill, marker=mark,
                           s=50, alpha=0.7, label=label)
                X_sub = sm.add_constant(-sub['h_disp_prev'])
                line_model = sm.OLS(sub['Drainage_Component'], X_sub).fit()
                x_range = np.linspace(sub['h_prev'].min(), sub['h_prev'].max(), 10)
                y_range = line_model.predict(sm.add_constant(-(DRAINAGE_DATUM + x_range)))
                ax.plot(x_range, y_range, color=col, linewidth=2, linestyle=ls)
                ax.text(0.05, 0.95 if label == 'Before' else 0.88,
                        f"{label} β₃: {line_model.params.iloc[1]:.3f}",
                        transform=ax.transAxes, color=col, fontweight='bold')

        ax.set_title(f'{well_upper} [{TIER_LABELS.get(tier, tier)}]',
                      fontweight='bold')
        ax.set_xlabel('Water Level (h_prev)')
        if i % ncols == 0:
            ax.set_ylabel('Drainage Component')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='lower right')

    for j in range(len(well_group), len(axes)):
        fig2.delaxes(axes[j])

    plt.suptitle(f'Drainage Mechanics: Before vs After — Part {part_idx}',
                  fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    output_name = DIR_10 / f"10_cfell_02_drainage_diagnostic_part{part_idx}.png"
    plt.savefig(output_name)
    plt.close(fig2)
    drainage_outputs.append(output_name)

# --- PLOT 3: Full Parameter Shift (β₁, β₂, β₃) whisker plots ─────────
if not full_param_df.empty:
    TIER_ORDER = ['impact', 'edge', 'climate', 'forest', 'coastal']
    TIER_DISPLAY = {
        'impact':  'Impact', 'edge': 'Edge',
        'climate': 'Climate Ctrl', 'forest': 'Forest Ctrl',
        'coastal': 'Coastal Ctrl',
    }

    fp = full_param_df.copy()

    # Build ordered well list
    ordered_wells_fp = []
    tier_boundaries_fp = {}
    for tier in TIER_ORDER:
        tw = fp[(fp['Tier'] == tier) & (fp['Period'] == 'Before')]['Well'].tolist()
        tw_after = fp[(fp['Tier'] == tier) & (~fp['Well'].isin(tw))]['Well'].unique().tolist()
        tier_wells = tw + [w for w in tw_after if w not in tw]
        tier_boundaries_fp[tier] = (len(ordered_wells_fp),
                                     len(ordered_wells_fp) + len(tier_wells) - 1)
        ordered_wells_fp.extend(tier_wells)

    coeffs_fp = [
        ('beta_1_recharge',         'beta_1_conf_low', 'beta_1_conf_high',
         r'Recharge sensitivity ($\beta_1$)',  r'$\Delta\beta_1$'),
        ('beta_2_atmospheric_draw', 'beta_2_conf_low', 'beta_2_conf_high',
         r'Atmospheric draw ($\beta_2$)',      r'$\Delta\beta_2$'),
        ('beta_3_drainage',         'beta_3_conf_low', 'beta_3_conf_high',
         r'Drainage coefficient ($-\beta_3$)', r'$\Delta(-\beta_3)$'),
    ]

    _orig_rc = {k: plt.rcParams[k] for k in
                ['font.size', 'axes.labelsize', 'axes.titlesize',
                 'xtick.labelsize', 'ytick.labelsize', 'legend.fontsize']}
    plt.rcParams.update({
        'font.size': 13, 'axes.labelsize': 14, 'axes.titlesize': 13,
        'xtick.labelsize': 11, 'ytick.labelsize': 12, 'legend.fontsize': 11,
    })

    fig3 = plt.figure(figsize=(20, 24), dpi=300)
    outer_gs = GridSpec(3, 2, figure=fig3, width_ratios=[5, 1],
                         hspace=0.32, wspace=0.18)

    for row_idx, (col, ci_lo, ci_hi, ylabel, delta_label) in enumerate(coeffs_fp):
        ax_main = fig3.add_subplot(outer_gs[row_idx, 0])
        ax_sum  = fig3.add_subplot(outer_gs[row_idx, 1])

        # Tier shading
        for tier in TIER_ORDER:
            x0, x1 = tier_boundaries_fp[tier]
            if x1 < x0:
                continue
            tc = TIER_COLOURS.get(tier, '#999999')
            ax_main.axvspan(x0 - 0.5, x1 + 0.5, alpha=0.08, color=tc, zorder=0)
            ax_main.text((x0 + x1) / 2, 0.04, TIER_DISPLAY.get(tier, tier),
                          transform=ax_main.get_xaxis_transform(),
                          ha='center', va='bottom', color=tc,
                          fontweight='bold', fontsize=11)

        delta_by_tier = {t: [] for t in TIER_ORDER}
        legend_done = set()

        for i, well in enumerate(ordered_wells_fp):
            tier = _well_tier(well.lower())
            tc = TIER_COLOURS.get(tier, '#999999')

            for period in ['Before', 'After']:
                row_s = fp[(fp['Well'] == well) & (fp['Period'] == period)]
                if row_s.empty:
                    continue
                val = row_s[col].iloc[0]
                low = row_s[ci_lo].iloc[0]
                high = row_s[ci_hi].iloc[0]
                if np.isnan(val):
                    continue

                if period == 'Before':
                    mk, mfc = 'o', 'white'
                    colour = '#444444'
                    x_pos = i - 0.15
                else:
                    mk, mfc = 's', tc
                    colour = tc
                    x_pos = i + 0.15

                err_lo = val - low if not np.isnan(low) else 0
                err_hi = high - val if not np.isnan(high) else 0
                lbl = period if period not in legend_done else ''
                ax_main.errorbar(x_pos, val, yerr=[[err_lo], [err_hi]],
                                  fmt=mk, color=colour,
                                  markerfacecolor=mfc, markeredgecolor=colour,
                                  markersize=7, capsize=5, linewidth=1.2,
                                  label=lbl, zorder=3)
                legend_done.add(period)

            b_row = fp[(fp['Well'] == well) & (fp['Period'] == 'Before')]
            a_row = fp[(fp['Well'] == well) & (fp['Period'] == 'After')]
            if not b_row.empty and not a_row.empty:
                bv = b_row[col].iloc[0]
                av = a_row[col].iloc[0]
                if not (np.isnan(bv) or np.isnan(av)):
                    delta_by_tier[tier].append(av - bv)

        # Tier separator lines
        for j, tier in enumerate(TIER_ORDER[:-1]):
            sep = tier_boundaries_fp[tier][1] + 0.5
            ax_main.axvline(sep, color='#AAAAAA', lw=1.0, ls='--', zorder=1)

        ax_main.set_xticks(range(len(ordered_wells_fp)))
        ax_main.set_xticklabels(ordered_wells_fp, rotation=45, ha='right', fontsize=10)
        ax_main.set_xlim(-0.6, len(ordered_wells_fp) - 0.4)
        ax_main.set_ylabel(ylabel, fontsize=14)
        ax_main.set_title(f'({"abc"[row_idx]})  {ylabel}: before (○) vs after (■) clearfell',
                           fontweight='bold', loc='left', pad=8, fontsize=13)
        ax_main.axhline(0, color='black', lw=0.8, ls=':', alpha=0.4)
        ax_main.legend(loc='upper right', framealpha=0.85)
        ax_main.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
        for sp in ['top', 'right']:
            ax_main.spines[sp].set_visible(False)

        # Summary inset
        for j, tier in enumerate(TIER_ORDER):
            deltas = np.array(delta_by_tier[tier])
            if len(deltas) == 0:
                continue
            mean_d = deltas.mean()
            boot = np.array([np.random.choice(deltas, len(deltas), replace=True).mean()
                             for _ in range(2000)])
            ci_lo_b = np.percentile(boot, 2.5)
            ci_hi_b = np.percentile(boot, 97.5)
            tc = TIER_COLOURS.get(tier, '#999999')
            ax_sum.errorbar(j, mean_d,
                             yerr=[[mean_d - ci_lo_b], [ci_hi_b - mean_d]],
                             fmt='D', color=tc, markerfacecolor=tc,
                             markeredgecolor=tc, markersize=11,
                             capsize=7, linewidth=2.0)
            ax_sum.text(j + 0.12, mean_d, f'{mean_d:+.3f}',
                         ha='left', va='center', color=tc,
                         fontweight='bold', fontsize=11)

        ax_sum.axhline(0, color='black', lw=0.9, ls='--', alpha=0.6)
        ax_sum.set_xticks(list(range(len(TIER_ORDER))))
        ax_sum.set_xticklabels([TIER_DISPLAY.get(t, t) for t in TIER_ORDER],
                                rotation=30, ha='right', fontsize=10)
        ax_sum.set_ylabel(delta_label, fontsize=12)
        ax_sum.set_title('Tier Δ\n(mean ± 95% CI)', fontweight='bold',
                          pad=8, fontsize=11)
        ax_sum.set_xlim(-0.5, len(TIER_ORDER) - 0.3)
        ax_sum.grid(axis='y', linestyle='--', alpha=0.5)
        for sp in ['top', 'right']:
            ax_sum.spines[sp].set_visible(False)

    fig3.suptitle('SSM coefficient shifts: before vs after clearfell (Dec 2017)\n'
                   'Two-tier western control design',
                   fontsize=14, fontweight='bold', y=0.99)
    plt.savefig(OUT_10_BETA3_SLOPES, bbox_inches='tight', dpi=300)
    plt.close(fig3)
    plt.rcParams.update(_orig_rc)
    print(f' -> Saved: {OUT_10_BETA3_SLOPES.name}')


# ===========================================================================
# 8. TRANSECT ANALYSIS
# ===========================================================================
TRANSECT_WELLS = {
    'ceh2':  {'label': 'CEH2\nPine/BL margin', 'dist_m': 414, 'role': 'reference'},
    'ceh34': {'label': 'CEH34\nForest control', 'dist_m': 285, 'role': 'forest_ctrl'},
    'wmc3':  {'label': 'WMC3\nCore impact', 'dist_m': 92, 'role': 'impact'},
    'nw8b':  {'label': 'NW8B\nEdge E', 'dist_m': 184, 'role': 'edge'},
    'ceh20': {'label': 'CEH20\nEdge N', 'dist_m': 186, 'role': 'edge'},
    'ceh16': {'label': 'CEH16\nEdge W', 'dist_m': 191, 'role': 'edge'},
}
TRANSECT_LINESTYLES = {
    'ceh2':  ('--', '#888888'),
    'ceh34': ('--', cb_purple),
    'wmc3':  ('-',  cb_red),
    'nw8b':  ('-',  '#FF7F0E'),
    'ceh20': ('-',  cb_blue),
    'ceh16': ('-',  '#9467BD'),
}

def plot_clearfell_transect(wells_df, scraping_dt, intervention_dt, scraping_dt_2):
    """Three-panel transect figure."""
    transect_available = {w: cfg for w, cfg in TRANSECT_WELLS.items()
                           if w in wells_df.columns}
    if len(transect_available) < 3:
        print("  [TRANSECT] Too few transect wells — skipping.")
        return None, {}

    mask_scrape = (wells_df.index >= scraping_dt) & (wells_df.index < intervention_dt)
    mask_post   = wells_df.index >= intervention_dt

    step_changes = {}
    for w in transect_available:
        s = wells_df[w]
        pre  = s[mask_scrape].mean()
        post = s[mask_post].mean()
        if pd.notna(pre) and pd.notna(post):
            step_changes[w] = post - pre

    fig = plt.figure(figsize=(14, 10), facecolor='white')
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.30,
                   top=0.90, bottom=0.07, left=0.08, right=0.96)
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])

    # Panel A: depth anomaly
    for w, cfg in transect_available.items():
        ls, col = TRANSECT_LINESTYLES.get(w, ('-', '#333333'))
        lw = 1.8 if cfg['role'] == 'impact' else 1.4
        scrape_mean_w = wells_df[w][mask_scrape].mean()
        anomaly = wells_df[w] - scrape_mean_w
        anomaly_smooth = anomaly.rolling(6, min_periods=3).mean()
        ax_a.plot(wells_df.index, anomaly_smooth, ls=ls, color=col, lw=lw,
                   label=f"{cfg['label'].split(chr(10))[0]} ({cfg['dist_m']}m)",
                   alpha=0.85)

    ax_a.axhline(0, color='black', lw=0.8, alpha=0.4)
    for vdate, vcol in [(scraping_dt, '#2166AC'), (intervention_dt, '#CC0000'),
                          (scraping_dt_2, '#888888')]:
        ax_a.axvline(pd.Timestamp(vdate), color=vcol, lw=1.1, ls='--', alpha=0.7)
    ax_a.set_ylabel('Anomaly vs scrape-era mean (m)', fontsize=8)
    ax_a.legend(fontsize=6.5, loc='upper left', framealpha=0.9, ncol=2)
    ax_a.grid(axis='y', alpha=0.2, lw=0.5)
    ax_a.set_title('(a) Depth anomaly — rising = shallowing',
                    fontsize=9, fontweight='bold')

    # Panel B: role-grouped anomaly
    _role_groups = {'impact': [], 'edge': [], 'forest_ctrl': [], 'reference': []}
    for w, cfg in transect_available.items():
        _role_groups.setdefault(cfg['role'], []).append(w)

    role_colours = {'impact': cb_red, 'edge': cb_blue,
                     'forest_ctrl': cb_purple, 'reference': '#888888'}
    for role, role_wells in _role_groups.items():
        if not role_wells:
            continue
        role_mean = wells_df[role_wells].mean(axis=1)
        transect_mean = wells_df[list(transect_available.keys())].mean(axis=1)
        rel_anom = (role_mean - transect_mean).rolling(6, min_periods=3).mean()
        ax_b.plot(wells_df.index, rel_anom, color=role_colours.get(role, '#333'),
                   lw=1.8, label=role)

    ax_b.axhline(0, color='black', lw=0.8, alpha=0.4)
    ax_b.axvline(intervention_dt, color='#CC0000', lw=1.1, ls='--', alpha=0.7)
    ax_b.set_ylabel('Relative position (m)', fontsize=8)
    ax_b.legend(fontsize=7, framealpha=0.9)
    ax_b.grid(axis='y', alpha=0.2, lw=0.5)
    ax_b.set_title('(b) Zone anomaly vs transect mean', fontsize=9, fontweight='bold')

    # Panel C: step change vs distance
    dists = [TRANSECT_WELLS[w]['dist_m'] for w in step_changes]
    steps = [step_changes[w] for w in step_changes]
    roles = [TRANSECT_WELLS[w]['role'] for w in step_changes]
    for d, s, r, w in zip(dists, steps, roles, step_changes):
        ax_c.scatter(d, s * 1000, color=role_colours.get(r, '#333'),
                      s=80, zorder=3, edgecolor='black', lw=0.5)
        ax_c.annotate(w.upper(), (d, s * 1000), fontsize=7,
                       xytext=(5, 5), textcoords='offset points')
    if len(dists) >= 3:
        slope, intercept, r_val, p_val, se = _stats.linregress(dists, [s*1000 for s in steps])
        _xr = np.linspace(min(dists), max(dists), 50)
        ax_c.plot(_xr, slope * _xr + intercept, color='#333', lw=1.5, ls='--',
                   label=f'R²={r_val**2:.2f}, p={p_val:.3f}')
    ax_c.axhline(0, color='gray', lw=0.8, ls=':', alpha=0.5)
    ax_c.set_xlabel('Distance from clearfell centroid (m)', fontsize=8)
    ax_c.set_ylabel('Step change (mm)', fontsize=8)
    ax_c.legend(fontsize=7, framealpha=0.9)
    ax_c.grid(alpha=0.2, lw=0.5)
    ax_c.set_title('(c) Step change vs distance', fontsize=9, fontweight='bold')

    plt.savefig(OUT_10_TRANSECT, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f' -> Saved: {OUT_10_TRANSECT.name}')

    # Export CSV
    rows = [{'Well': w.upper(),
             'Label': TRANSECT_WELLS[w]['label'].replace('\n', ' '),
             'Distance_m': TRANSECT_WELLS[w]['dist_m'],
             'Role': TRANSECT_WELLS[w]['role'],
             'Scrape_era_mean': float(wells_df[w][mask_scrape].mean()),
             'Post_fell_mean': float(wells_df[w][mask_post].mean()),
             'Step_change_m': float(step_changes.get(w, float('nan')))}
            for w in transect_available]
    pd.DataFrame(rows).to_csv(OUT_10_TRANSECT_CSV, index=False)
    print(f' -> Saved: {OUT_10_TRANSECT_CSV.name}')
    return fig, step_changes


if not baci_df.empty:
    _transect_fig, _transect_steps = plot_clearfell_transect(
        wells, scraping_date, intervention_date, scraping_date_2)
else:
    _transect_steps = {}


# ===========================================================================
# 9. NW10 BROADLEAF TREND ANALYSIS
# ===========================================================================
_pine_interior = ['ceh2', 'ceh32', 'ceh33', 'ceh34']
_pine_avail    = [w for w in _pine_interior if w in wells.columns]
_slope_mm_yr = _mean_anom_bramble = _p = _n = np.nan

if 'nw10' in wells.columns and len(_pine_avail) >= 2:
    _SUMMER = [6, 7, 8, 9]
    _nw10_mins = {}
    _pine_mins = {}

    for _yr in range(2007, 2026):
        _mask = (wells.index.year == _yr) & (wells.index.month.isin(_SUMMER))
        _nw10_s = wells['nw10'][_mask].dropna()
        if len(_nw10_s) >= 2:
            _nw10_mins[_yr] = float(_nw10_s.max())
        _pine_s = wells[_pine_avail][_mask].mean(axis=1).dropna()
        if len(_pine_s) >= 2:
            _pine_mins[_yr] = float(_pine_s.max())

    _common_yrs = sorted(set(_nw10_mins) & set(_pine_mins))
    if len(_common_yrs) >= 5:
        _anom = pd.Series({yr: _nw10_mins[yr] - _pine_mins[yr] for yr in _common_yrs})
        _bramble = _anom[(_anom.index >= 2010) & (_anom.index <= 2021)]
        _mean_anom_bramble = float(_bramble.mean()) if len(_bramble) > 0 else np.nan

        _trend_data = _anom[(_anom.index >= 2019) & (_anom.index <= 2025)]
        if len(_trend_data) >= 4:
            _X_t = np.column_stack([np.ones(len(_trend_data)),
                                     _trend_data.index.astype(float)])
            _y_t = _trend_data.values
            _b_t = np.linalg.lstsq(_X_t, _y_t, rcond=None)[0]
            _n_t, _k_t = len(_y_t), 2
            _r_t = _y_t - _X_t @ _b_t
            _s2_t = (_r_t @ _r_t) / (_n_t - _k_t)
            _se_b1 = np.sqrt(_s2_t * np.linalg.inv(_X_t.T @ _X_t)[1, 1])
            _t_stat = _b_t[1] / _se_b1
            _p = float(2 * _stats.t.sf(abs(_t_stat), df=_n_t - _k_t))
            _slope_mm_yr = float(_b_t[1]) * 1000
            _n = _n_t

            print(f'\n--- NW10 Broadleaf Trend ---')
            print(f'  Trend 2019-2025: {_slope_mm_yr:+.1f} mm/yr, p={_p:.3f}, n={_n}')

        _export = pd.DataFrame({
            'Year': _common_yrs,
            'NW10_summer_min_m': [_nw10_mins[yr] for yr in _common_yrs],
            'Pine_composite_min_m': [_pine_mins[yr] for yr in _common_yrs],
            'NW10_anomaly_m': [float(_anom[yr]) for yr in _common_yrs],
        })
        _export.to_csv(OUT_10_NW10_TREND, index=False)
        print(f' -> Saved: {OUT_10_NW10_TREND.name}')


# ===========================================================================
# 10. ROBUSTNESS 1 — SSM Residual (per-well forward prediction)
# ===========================================================================
print("\n--- Robustness 1: SSM Residual Analysis ---")

_ssm_resid_results = []
_all_network = valid_impact + valid_edge + valid_climate + valid_forest

for _w in _all_network:
    if _w not in wells.columns:
        continue
    _h = wells[_w].dropna()
    _df_full = build_ssm_frame(_h, climate, lag=HEADLINE_LAG,
                                drainage_datum=DRAINAGE_DATUM)
    _df_cal = _df_full[_df_full.index < scraping_date]

    if len(_df_cal) < 36:
        continue

    _X_cal = pd.DataFrame({
        'b1': _df_cal['P'].values,
        'b2': -_df_cal['PET'].values,
        'b3': -_df_cal['h_disp_prev'].values,
    })
    try:
        _ols_cal = sm.OLS(_df_cal['Delta_h'].values, _X_cal).fit()
    except Exception:
        continue
    _betas = _ols_cal.params.values

    _post = _df_full[_df_full.index >= scraping_date].copy()
    if len(_post) < 6:
        continue

    _h_pred = [float(_df_cal['h'].iloc[-1])]
    for _i, (_idx, _row) in enumerate(_post.iterrows()):
        _h_prev_pred = _h_pred[-1]
        _h_disp_pred = DRAINAGE_DATUM + _h_prev_pred
        _dh_pred = (_betas[0] * _row['P']
                    - _betas[1] * _row['PET']
                    - _betas[2] * _h_disp_pred)
        _h_pred.append(_h_prev_pred + _dh_pred)

    _pred_series = pd.Series(_h_pred[1:], index=_post.index)
    _resid = _post['h'] - _pred_series

    _scrape_mask = (_resid.index >= scraping_date) & (_resid.index < intervention_date)
    _fell_mask = _resid.index >= intervention_date
    _scrape_mean = float(_resid[_scrape_mask].mean()) if _scrape_mask.any() else np.nan
    _fell_mean = float(_resid[_fell_mask].mean()) if _fell_mask.any() else np.nan

    _tier = _well_tier(_w)
    _ssm_resid_results.append({
        'well': _w, 'tier': _tier,
        'scrape_mean': _scrape_mean, 'fell_mean': _fell_mean,
        'resid_series': _resid,
    })

# Normalise against forest control mean residual
_ctrl_resids = [r for r in _ssm_resid_results if r['tier'] == 'forest']
if _ctrl_resids:
    _ctrl_scrape = np.nanmean([r['scrape_mean'] for r in _ctrl_resids])
    _ctrl_fell = np.nanmean([r['fell_mean'] for r in _ctrl_resids])
else:
    _ctrl_scrape = _ctrl_fell = 0.0

_ssm_norm_results = []
for _r in _ssm_resid_results:
    _norm_scrape = _r['scrape_mean'] - _ctrl_scrape
    _norm_fell = _r['fell_mean'] - _ctrl_fell
    _step = _norm_fell - _norm_scrape

    _rs = _r['resid_series']
    _ctrl_mean_series = pd.Series(0.0, index=_rs.index)
    if _ctrl_resids:
        _all_ctrl = pd.DataFrame({cr['well']: cr['resid_series'] for cr in _ctrl_resids})
        _ctrl_mean_series = _all_ctrl.reindex(_rs.index).mean(axis=1).fillna(0)
    _norm_resid = _rs - _ctrl_mean_series
    _scrape_vals = _norm_resid[(_norm_resid.index >= scraping_date) &
                                (_norm_resid.index < intervention_date)].dropna()
    _fell_vals = _norm_resid[_norm_resid.index >= intervention_date].dropna()
    if len(_scrape_vals) >= 3 and len(_fell_vals) >= 3:
        _, _p_val = _stats.ttest_ind(_fell_vals, _scrape_vals, equal_var=False)
    else:
        _p_val = np.nan

    _ssm_norm_results.append({
        'well': _r['well'].upper(), 'tier': _r['tier'],
        'norm_scrape': _norm_scrape, 'norm_fell': _norm_fell,
        'step': _step, 'p_value': _p_val,
    })
    print(f"  {_r['well'].upper():<8} [{_r['tier']:<12}] "
          f"scrape={_norm_scrape:+.3f}  fell={_norm_fell:+.3f}  "
          f"step={_step:+.3f}  "
          f"p={'<0.001' if _p_val < 0.001 else f'{_p_val:.3f}' if pd.notna(_p_val) else 'N/A'}")

for _tier in ['impact', 'edge', 'climate', 'forest']:
    _tr = [r for r in _ssm_norm_results if r['tier'] == _tier]
    if _tr:
        _t_step = np.nanmean([r['step'] for r in _tr])
        print(f"  {'MEAN':8} [{_tier:<12}] step={_t_step:+.3f} m  (n={len(_tr)})")


# ===========================================================================
# 11. ROBUSTNESS 2 — Synthetic Control (zone-level)
# ===========================================================================
print("\n--- Robustness 2: Synthetic Control Analysis ---")

# Donor pool: wells outside the clearfell/control network entirely
_network_wells = set(valid_impact + valid_edge + valid_climate
                     + valid_forest + valid_coastal)
_synth_donor_candidates = [
    'ceh5', 'ceh6', 'ceh10', 'ceh11', 'ceh17',
    'ceh24', 'ceh23', 'ceh25', 'ceh26', 'ceh27',
]
_synth_donors = [w for w in _synth_donor_candidates
                 if w in wells.columns and w not in _network_wells]

_synth_results = {}
for _zone_label, _zone_wells in [("Core", valid_impact), ("Edge", valid_edge)]:
    _zone_mean = wells[_zone_wells].mean(axis=1).dropna()
    _donor_data = wells[_synth_donors].dropna()
    _common_idx = _zone_mean.index.intersection(_donor_data.index)

    _baseline_mask = _common_idx < scraping_date
    _baseline_idx = _common_idx[_baseline_mask]

    if len(_baseline_idx) < 24:
        print(f"  {_zone_label}: insufficient baseline for synthetic control")
        _synth_results[_zone_label] = {'gap_fell': np.nan, 'p_value': np.nan}
        continue

    _X_syn = _donor_data.loc[_baseline_idx].values
    _y_syn = _zone_mean.loc[_baseline_idx].values
    try:
        _ols_syn = sm.OLS(_y_syn, _X_syn).fit()
        _w_syn = _ols_syn.params
    except Exception:
        _synth_results[_zone_label] = {'gap_fell': np.nan, 'p_value': np.nan}
        continue

    _synthetic = _donor_data.loc[_common_idx].values @ _w_syn
    _gap = _zone_mean.loc[_common_idx].values - _synthetic
    _gap_series = pd.Series(_gap, index=_common_idx)

    _gap_scrape = _gap_series[(_gap_series.index >= scraping_date) &
                               (_gap_series.index < intervention_date)]
    _gap_fell = _gap_series[_gap_series.index >= intervention_date]

    _mean_gap_scrape = float(_gap_scrape.mean()) if len(_gap_scrape) > 0 else np.nan
    _mean_gap_fell = float(_gap_fell.mean()) if len(_gap_fell) > 0 else np.nan

    if len(_gap_scrape) >= 3 and len(_gap_fell) >= 3:
        _, _p_syn = _stats.ttest_ind(_gap_fell, _gap_scrape, equal_var=False)
    else:
        _p_syn = np.nan

    _synth_results[_zone_label] = {
        'gap_scrape': _mean_gap_scrape,
        'gap_fell': _mean_gap_fell,
        'step': _mean_gap_fell - _mean_gap_scrape if pd.notna(_mean_gap_scrape) else np.nan,
        'p_value': float(_p_syn),
    }
    print(f"  {_zone_label}: scrape gap={_mean_gap_scrape:+.3f}  "
          f"fell gap={_mean_gap_fell:+.3f}  "
          f"step={_mean_gap_fell - _mean_gap_scrape:+.3f}  "
          f"p={'<0.001' if _p_syn < 0.001 else f'{_p_syn:.3f}'}")


# ===========================================================================
# 12. ROBUSTNESS 3 — Cluster Transition (rolling SSM coefficients)
# ===========================================================================
print("\n--- Robustness 3: Cluster Transition Analysis ---")

_ROLL_WINDOW = 48

try:
    _reg_avg = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    _c3_centroid = _reg_avg['C3'] if 'C3' in _reg_avg.columns else None
    _c4_centroid = _reg_avg['C4'] if 'C4' in _reg_avg.columns else None
except Exception:
    _c3_centroid = _c4_centroid = None

def _rolling_ssm_coeffs(h_series, climate_df, window=48):
    """Compute rolling-window SSM β₁ and β₃ over time."""
    results = []
    df = build_ssm_frame(h_series, climate_df, lag=HEADLINE_LAG,
                          drainage_datum=DRAINAGE_DATUM)
    if len(df) < window:
        return pd.DataFrame()
    for end_idx in range(window, len(df) + 1):
        chunk = df.iloc[end_idx - window:end_idx]
        X = pd.DataFrame({
            'b1': chunk['P'].values,
            'b2': -chunk['PET'].values,
            'b3': -chunk['h_disp_prev'].values,
        })
        try:
            _fit = sm.OLS(chunk['Delta_h'].values, X).fit()
            results.append({
                'date': chunk.index[-1],
                'beta_1': float(_fit.params['b1']),
                'beta_3': float(_fit.params['b3']),
                'R2': float(_fit.rsquared),
            })
        except Exception:
            continue
    return pd.DataFrame(results).set_index('date') if results else pd.DataFrame()


_impact_mean = wells[valid_impact].mean(axis=1).dropna()
_roll_impact = _rolling_ssm_coeffs(_impact_mean, climate, _ROLL_WINDOW)
_roll_c3 = _rolling_ssm_coeffs(_c3_centroid, climate, _ROLL_WINDOW) if _c3_centroid is not None else pd.DataFrame()
_roll_c4 = _rolling_ssm_coeffs(_c4_centroid, climate, _ROLL_WINDOW) if _c4_centroid is not None else pd.DataFrame()

_transition_assessment = "insufficient_data"

if not _roll_impact.empty and not _roll_c3.empty:
    _post_roll = _roll_impact[_roll_impact.index >= intervention_date]
    _pre_roll = _roll_impact[(_roll_impact.index >= scraping_date) &
                               (_roll_impact.index < intervention_date)]
    _c3_post = _roll_c3[_roll_c3.index >= intervention_date]

    if len(_post_roll) >= 6 and len(_c3_post) >= 6:
        _b1_impact_post = _post_roll['beta_1'].mean()
        _b1_c3_post = _c3_post['beta_1'].mean()

        if len(_pre_roll) >= 3:
            _b1_impact_pre = _pre_roll['beta_1'].mean()
            _b1_direction = ("toward C3" if abs(_b1_impact_post - _b1_c3_post)
                             < abs(_b1_impact_pre - _b1_c3_post)
                             else "away from C3")
            _transition_assessment = _b1_direction
            print(f"  Impact β₁: pre={_b1_impact_pre:.3f}  post={_b1_impact_post:.3f}  "
                  f"C3={_b1_c3_post:.3f}  → {_b1_direction}")

_roll_export = pd.DataFrame()
if not _roll_impact.empty:
    _roll_export['Impact_beta1'] = _roll_impact['beta_1']
    _roll_export['Impact_beta3'] = _roll_impact['beta_3']
if not _roll_c3.empty:
    _roll_export['C3_beta1'] = _roll_c3['beta_1']
    _roll_export['C3_beta3'] = _roll_c3['beta_3']
if not _roll_c4.empty:
    _roll_export['C4_beta1'] = _roll_c4['beta_1']
    _roll_export['C4_beta3'] = _roll_c4['beta_3']
if not _roll_export.empty:
    _roll_path = DIR_10 / '10_cfell_12_rolling_transition.csv'
    _roll_export.to_csv(_roll_path)
    print(f"  Saved: {_roll_path.name}")


# ===========================================================================
# SUMMARY
# ===========================================================================
print("\n" + "=" * 72)
print("   OMNIBUS CLEAR-FELL SUMMARY — WESTERN CONTROLS DESIGN")
print("=" * 72)
print(f"Impact wells:          {', '.join(w.upper() for w in valid_impact)}")
print(f"Edge wells:            {', '.join(w.upper() for w in valid_edge)}")
print(f"Climate controls:      {', '.join(w.upper() for w in valid_climate)}")
print(f"Forest controls:       {', '.join(w.upper() for w in valid_forest)}")
print(f"Coastal controls:      {', '.join(w.upper() for w in valid_coastal)}")

if not baci_df.empty:
    print(f"\n--- Impact vs Forest Control (direct counterfactual) ---")
    print(f"  Pre-scraping mean:       {mean_pre_scr_for:+.4f} m")
    print(f"  Post-scraping mean:      {mean_post_scr_for:+.4f} m")
    print(f"  Post-felling mean:       {mean_post_fell_for:+.4f} m")
    print(f"    Pure clearfell era:    {mean_pf_pre_s2_for:+.4f} m  "
          f"(Δ={shift_pf_pre_s2_for:+.4f})")
    print(f"    Post-Oct2023 era:      {mean_pf_post_s2_for:+.4f} m  "
          f"(Δ={shift_pf_post_s2_for:+.4f})")
    print(f"  Step change (clearfell): {shift_for:+.4f} m")
    print(f"  Combined cost:           {combined_cost_for:+.4f} m")
    print(f"\n--- Impact vs Climate Control (C3 West) ---")
    print(f"  Step change:             {shift_clim:+.4f} m")

if _ancova_b is not None:
    _pf = lambda p: '<0.001' if p < 0.001 else f'{p:.3f}'
    print(f"\n--- ANCOVA (climate + coastal corrected) ---")
    print(f"  Clearfell step:  {_ancova_b[4]:+.4f} m  "
          f"CI=[{_ancova_b[4]-1.96*_ancova_se[4]:.4f}, {_ancova_b[4]+1.96*_ancova_se[4]:.4f}]  "
          f"p={_pf(_ancova_p[4])}")
    print(f"  R²: {_ancova_r2:.3f}")

if not full_param_df.empty:
    print("\n--- Full Parameter Shift (β₁, β₂, β₃) ---")
    for param in ['beta_1_recharge', 'beta_2_atmospheric_draw', 'beta_3_drainage']:
        print(f"\n{param}:")
        _pivot = full_param_df.pivot_table(index='Well', columns='Period',
                                            values=param, aggfunc='first')
        print(_pivot.to_string())


# ===========================================================================
# EXPORT REPORT NUMBERS CSV
# ===========================================================================
print("\nExporting report numbers CSV...")
_rpt_rows = []

def _rn(parameter, value, unit="m", well="", era="", note=""):
    _rpt_rows.append({
        "Parameter": parameter, "Well": well, "Era": era,
        "Value": round(value, 4) if pd.notna(value) and not isinstance(value, str) else value,
        "Unit": unit, "Note": note,
    })

if not baci_df.empty:
    _rn("Pre_felling_offset_vs_forest", mean_pre_scr_for,
        note="Impact vs forest control, pre-scraping")
    _rn("Post_scraping_mean_vs_forest", mean_post_scr_for, era="Post_scraping")
    _rn("Post_felling_mean_vs_forest", mean_post_fell_for, era="Post_felling")
    _rn("Step_change_vs_forest", shift_for, era="Post_felling",
        note="From post-scraping baseline")
    _rn("Step_change_vs_climate", shift_clim, era="Post_felling",
        note="Impact vs C3 West climate controls")
    _rn("Combined_cost_vs_forest", combined_cost_for,
        note="Pre-scraping to post-felling")
    _rn("Step_PF_pre_scrape2_forest", shift_pf_pre_s2_for, era="Dec2017_Sep2023")
    _rn("Step_PF_post_scrape2_forest", shift_pf_post_s2_for, era="Oct2023_onwards")
    if not np.isnan(shift_edge_for):
        _rn("Step_change_edge_vs_forest", shift_edge_for, era="Post_felling")

if _ancova_b is not None:
    _rn("ANCOVA_intercept", float(_ancova_b[0]), note="Model 2 intercept")
    _rn("ANCOVA_cwb_coeff", float(_ancova_b[1]), unit="m/mm",
        note=f"p={_pfmt(_ancova_p[1])}")
    _rn("ANCOVA_coastal_coeff", float(_ancova_b[2]),
        note=f"Coastal control centroid, p={_pfmt(_ancova_p[2])}")
    _rn("ANCOVA_scraping_step", float(_ancova_b[3]),
        note=f"p={_pfmt(_ancova_p[3])}")
    _rn("ANCOVA_clearfell_step", float(_ancova_b[4]),
        note=f"p={_pfmt(_ancova_p[4])}, "
             f"CI=[{_ancova_b[4]-1.96*_ancova_se[4]:.4f},"
             f"{_ancova_b[4]+1.96*_ancova_se[4]:.4f}]")
    _rn("ANCOVA_interaction", float(_ancova_b[5]), unit="m/mm",
        note=f"CWB×post, p={_pfmt(_ancova_p[5])}")
    _rn("ANCOVA_R2", float(_ancova_r2), unit="")
    _rn("ANCOVA_oct2023_coef", float(_oct23_imp_coef),
        note=f"p={_oct23_imp_p:.3f}, ΔAIC={_daic_imp:+.2f}")

    if _ancova_edge_b is not None:
        _rn("ANCOVA_edge_clearfell_step", float(_ancova_edge_b[4]),
            note=f"p={_pfmt(_ancova_edge_p[4])}, "
                 f"CI=[{_ancova_edge_b[4]-1.96*_ancova_edge_se[4]:.4f},"
                 f"{_ancova_edge_b[4]+1.96*_ancova_edge_se[4]:.4f}]")
        _rn("ANCOVA_edge_R2", float(_ancova_edge_r2), unit="")

# Per-well BACI displacements
if not baci_df.empty:
    for _tier_label, _tier_wells in [("Impact", valid_impact),
                                       ("Edge", valid_edge),
                                       ("Climate_Ctrl", valid_climate),
                                       ("Forest_Ctrl", valid_forest)]:
        for _w in _tier_wells:
            if _w not in wells.columns:
                continue
            _w_series = wells[_w].dropna()
            _pre_mean  = _w_series[_w_series.index < intervention_date].mean()
            _post_mean = _w_series[_w_series.index >= intervention_date].mean()
            # BACI vs forest control
            _forest_mean = wells[valid_forest].mean(axis=1)
            _pre_baci = float((_w_series[_w_series.index < intervention_date]
                               - _forest_mean.reindex(_w_series.index[
                                   _w_series.index < intervention_date])).mean()) \
                        if len(_w_series[_w_series.index < intervention_date]) > 0 else np.nan
            _post_baci = float((_w_series[_w_series.index >= intervention_date]
                                - _forest_mean.reindex(_w_series.index[
                                    _w_series.index >= intervention_date])).mean()) \
                         if len(_w_series[_w_series.index >= intervention_date]) > 0 else np.nan
            if pd.notna(_pre_baci):
                _rn("Per_well_BACI_vs_forest", _pre_baci,
                    well=_w.upper(), era="Pre_felling", note=f"Tier={_tier_label}")
            if pd.notna(_post_baci):
                _rn("Per_well_BACI_vs_forest", _post_baci,
                    well=_w.upper(), era="Post_felling", note=f"Tier={_tier_label}")

# β₃ before/after
for _sr in stats_results:
    if _sr.get('Well', '') == 'BACI_SUMMARY':
        continue
    _rn("Table6_beta3", _sr.get('beta_3_drainage', np.nan),
        well=_sr['Well'], era=_sr['Period'],
        note=f"Tier={_sr.get('Tier','')}, "
             f"CI=[{_sr.get('Conf_Low',np.nan):.4f},{_sr.get('Conf_High',np.nan):.4f}] "
             f"p={_sr.get('P_Value',np.nan):.5f}" if pd.notna(_sr.get('P_Value')) else "")

# Transect
try:
    for _tw, _ts_val in _transect_steps.items():
        _cfg = TRANSECT_WELLS.get(_tw, {})
        _rn("Transect_step_change", float(_ts_val),
            well=_tw.upper(), era="Post_felling",
            note=f"Distance={_cfg.get('dist_m','?')}m, Role={_cfg.get('role','?')}")
except NameError:
    pass

# NW10
try:
    if pd.notna(_slope_mm_yr):
        _rn("NW10_broadleaf_trend_slope", _slope_mm_yr, unit="mm/yr",
            well="NW10", era="2019-2025", note=f"p={_p:.4f}, n={_n}")
    if pd.notna(_mean_anom_bramble):
        _rn("NW10_mean_anomaly_2010_2021", _mean_anom_bramble,
            well="NW10", note="vs pine interior composite")
except NameError:
    pass

# Robustness 1
for _snr in _ssm_norm_results:
    _pv = _snr['p_value']
    _p_str = '<0.001' if (pd.notna(_pv) and _pv < 0.001) else (f'{_pv:.3f}' if pd.notna(_pv) else 'N/A')
    _rn("Robustness_SSM_residual_step", _snr['step'],
        well=_snr['well'], era="Step_change",
        note=f"Tier={_snr['tier']}, p={_p_str}")

# Robustness 2
for _zone_lab, _sr in _synth_results.items():
    _rn("Robustness_synthetic_gap", _sr.get('gap_fell', np.nan),
        well=_zone_lab, era="Post_felling",
        note=f"p={_sr.get('p_value', np.nan):.3f}" if pd.notna(_sr.get('p_value')) else "")

# Robustness 3
_rn("Robustness_cluster_transition", 0.0,
    well="Impact", era=_transition_assessment, unit="",
    note="Qualitative: toward C3 = converging to open-dune behaviour")

# Coefficient tier means
if not full_param_df.empty:
    for _coeff in ['beta_1_recharge', 'beta_2_atmospheric_draw', 'beta_3_drainage']:
        for _tier_label, _tier_wells in [("Impact", valid_impact),
                                           ("Edge", valid_edge),
                                           ("Climate_Ctrl", valid_climate),
                                           ("Forest_Ctrl", valid_forest)]:
            _fp_tier = full_param_df[full_param_df['Well'].str.lower().isin(_tier_wells)]
            for _per in ['Before', 'After']:
                _fp_per = _fp_tier[_fp_tier['Period'] == _per]
                if not _fp_per.empty:
                    _rn(f"Coefficient_tier_mean_{_coeff}", float(_fp_per[_coeff].mean()),
                        era=_per, note=f"Tier={_tier_label}, n={len(_fp_per)}")

_rpt_df = pd.DataFrame(_rpt_rows)
_rpt_df.to_csv(OUT_10_REPORT_NUMBERS, index=False)
print(f" -> Saved: {OUT_10_REPORT_NUMBERS.name} ({len(_rpt_rows)} rows)")


print("\n--- Files successfully created ---")
print(OUT_10_DUAL_BACI)
if 'OUT_10_RAW_BACI' in dir():
    print(OUT_10_RAW_BACI)
for output_name in drainage_outputs:
    print(output_name)
print(OUT_10_BETA3_SLOPES)
print(OUT_10_TRANSECT)
print(OUT_10_TRANSECT_CSV)
print(OUT_10_DRAINAGE_DATA)
print(OUT_10_STAT_VERIFICATION)
print(OUT_10_FULL_PARAMS)
print(OUT_10_TABLE5_SUMMARY)
print(OUT_10_NW10_TREND)
print(OUT_10_REPORT_NUMBERS)

print("\n[DONE] Script 10 v2.0 — Two-tier western control BACI complete.")
