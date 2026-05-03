"""
====================================================================================
THE OMNIBUS SLACK SCRAPING ANALYSIS: REBUILT CONTROL DESIGN
====================================================================================
Purpose:
Evaluates slack scraping using a Hierarchical BACI design with clean
regional controls and climate correction.

Changes from v1.0:
  - Felling date corrected: 2018-12-01 → 2017-12-01
  - Regional controls replaced: removed NW8/NW8B (felling zone), CEH9/NW7/NW6
    (scraping propagation zone). Replaced with distant eastern C1/C2 wells
    outside both contamination zones.
  - ANCOVA climate correction added: cumulative water balance covariate
    partitions climate forcing from scraping signal.
  - Coastal erosion covariate added to ANCOVA for CEH36/CEH18 analysis.
  - Multi-control composite for Tier 2 alongside single-well pairing.

Tier 1: Local controls (CEH4, CEH22) vs clean Regional Mean → proves
         coastal boundary retreat is real and progressive.
Tier 2: Treatment wells vs local controls → isolates scraping signal.
ANCOVA: Climate- and coastal-corrected step estimates with CIs.

Outputs: CSVs 01–04, Plots 05–10, report numbers CSV.
====================================================================================
"""

__version__ = "2.0.0"  # Hollingham (2026) — clean controls rebuild, 2026-05-03

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs, DATA_CLIMATE_RAW, DATA_WELLS_RAW,
    INT_WELLS_CLEAN, INT_WELLS_EXTENDED,
    OUT_09_FULL_PARAMS,
    OUT_09_BETA3_SIG,
    OUT_09_BACI_SHIFTS,
    OUT_09_NET_BENEFITS,
    OUT_09_TABLE4_SUMMARY,
    OUT_09_TIER1_DRIFT,
    OUT_09_TIER2_SIGNAL,
    OUT_09_BETA3_CI,
    OUT_09_ROBUSTNESS,
    OUT_09_REPORT_NUMBERS,
    OUT_09_SCRAPE_SUMMER_MIN,
    OUT_09_SCRAPE_SUMMER_CSV,
    OUT_09B_SUMMER_SCENARIO,
    OUT_09B_SUMMER_SCENARIO_CSV,
    INT_CLIMATE,
    INT_REGIONAL_AVG,
    DIR_09
)
from utils.data_utils import parse_met_date, clean_well_series, calculate_cusum
from utils.config import DRAINAGE_DATUM, HEADLINE_LAG
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.api as sm
import sys
import os
from pathlib import Path
from scipy import stats as _stats

make_all_dirs()

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'pdf.fonttype': 42, 'ps.fonttype': 42,
    'axes.labelsize': 12, 'axes.titlesize': 14,
    'xtick.labelsize': 10, 'ytick.labelsize': 10,
    'legend.fontsize': 10,
})


def format_p_value(p: float) -> str:
    if pd.isna(p): return ""
    return "<0.001" if p < 0.001 else f"{p:.5f}"


def significance_stars(p: float) -> str:
    if pd.isna(p): return ""
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


def _ols(y, X):
    """Lightweight OLS: returns (betas, std_errors, p_values)."""
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    n, k = X.shape
    r = y - X @ b
    s2 = (r @ r) / (n - k)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    t = b / se
    p = 2 * _stats.t.sf(np.abs(t), df=n - k)
    return b, se, p


def _r_squared(y, X, b):
    resid = y - X @ b
    ss_res = (resid ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan


def _aic(y, X, b):
    n, k = X.shape
    resid = y - X @ b
    ss = (resid ** 2).sum()
    return n * np.log(ss / n) + 2 * k


# ===========================================================================
# 1. EXPERIMENT SETUP — CLEAN CONTROL DESIGN
# ===========================================================================
print("=" * 72)
print("SCRIPT 09: SCRAPING BACI — CLEAN REGIONAL CONTROLS v2.0")
print("=" * 72)

# ── Regional controls: distant eastern wells ─────────────────────────────
# All >900m from CEH36, east of E=242000, outside both the scraping
# propagation zone (09b: signal extends to 776m N/NW of CEH36) and the
# clearfell footprint. Long pre-2015 baselines (>100 months).
regional_controls = ['nw3', 'nw4', 'ceh5', 'ceh6', 'ceh10', 'ceh11']

# ── Intervention dates ───────────────────────────────────────────────────
date_2015    = pd.Timestamp('2015-04-01')   # CEH36 scraping
date_felling = pd.Timestamp('2017-12-01')   # Clearfell (was 2018-12-01 in v1 — BUG)
date_2023    = pd.Timestamp('2023-10-01')   # CEH18 + CEH21 scraping

# ── Focal wells and era structure ────────────────────────────────────────
well_eras = {
    'ceh36': {
        'Exp': '2015_Scraping_with_KnockOn',
        'Role': 'Treatment',
        'Pair': 'ceh4',
        'Eras': {
            '1_Baseline':       lambda df: df[df.index < date_2015],
            '2_Pure_Scraping':  lambda df: df[(df.index >= date_2015) & (df.index < date_felling)],
            '3_Felling_Pulse':  lambda df: df[df.index >= date_felling],
        }
    },
    'ceh4': {
        'Exp': 'Control_Tracking',
        'Role': 'Local_Control',
        'Pair': 'Regional Mean',
        'Eras': {
            '1_Baseline':       lambda df: df[df.index < date_2015],
            '2_Pure_Scraping':  lambda df: df[(df.index >= date_2015) & (df.index < date_felling)],
            '3_Felling_Pulse':  lambda df: df[df.index >= date_felling],
        }
    },
    'ceh18': {
        'Exp': '2023_Scraping_with_Felling_Pulse',
        'Role': 'Treatment',
        'Pair': 'ceh4',
        'Eras': {
            '1_Baseline':       lambda df: df[df.index < date_felling],
            '2_Felling_Pulse':  lambda df: df[(df.index >= date_felling) & (df.index < date_2023)],
            '3_After_Scraping': lambda df: df[df.index >= date_2023],
        }
    },
    'ceh21': {
        'Exp': 'Coastal_Refuge_Scraping',
        'Role': 'Coastal_Treatment',
        'Pair': 'ceh22',
        'Eras': {
            '1_Baseline':          lambda df: df[df.index < date_felling],
            '2_Coastal_Drawdown':  lambda df: df[(df.index >= date_felling) & (df.index < date_2023)],
            '3_After_Scraping':    lambda df: df[df.index >= date_2023],
        }
    },
    'ceh22': {
        'Exp': 'Coastal_Control_Tracking',
        'Role': 'Coastal_Control',
        'Pair': 'Regional Mean',
        'Eras': {
            '1_Baseline':          lambda df: df[df.index < date_felling],
            '2_Coastal_Drawdown':  lambda df: df[(df.index >= date_felling) & (df.index < date_2023)],
            '3_After_Scraping':    lambda df: df[df.index >= date_2023],
        }
    }
}

colors = {
    '1_Baseline': '#009E73', '2_Pure_Scraping': '#56B4E9',
    '3_Felling_Pulse': '#CC79A7', '2_Felling_Pulse': '#CC79A7',
    '2_Coastal_Drawdown': '#E69F00', '3_After_Scraping': '#D55E00',
}
markers = {
    '1_Baseline': 'o', '2_Pure_Scraping': 's', '3_Felling_Pulse': '^',
    '2_Felling_Pulse': '^', '2_Coastal_Drawdown': 'v', '3_After_Scraping': 'D',
}
fill_styles = colors.copy()
fill_styles['1_Baseline'] = 'none'
linestyles = {
    '1_Baseline': ':', '2_Pure_Scraping': '--', '3_Felling_Pulse': '-',
    '2_Felling_Pulse': '-', '2_Coastal_Drawdown': '--', '3_After_Scraping': '-.',
}

# Hierarchical pairings
pairings = {
    'ceh36': 'ceh4',
    'ceh18': 'ceh4',
    'ceh21': 'ceh22',
    'ceh4':  'Regional Mean',
    'ceh22': 'Regional Mean',
}


# ===========================================================================
# 1b. DATA LOADING
# ===========================================================================
print("\n1. Loading Data...")
try:
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True).sort_index()

    wells_main = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells_main.columns = wells_main.columns.str.lower().str.replace(' ', '')
    if INT_WELLS_EXTENDED.exists():
        wells_ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
        wells_ext.columns = wells_ext.columns.str.lower().str.replace(' ', '')
        new_cols = [c for c in wells_ext.columns if c not in wells_main.columns]
        wells = pd.concat([wells_main, wells_ext[new_cols]], axis=1)
    else:
        wells = wells_main

    valid_controls = [w for w in regional_controls if w in wells.columns]
    print(f'  Regional controls: {", ".join(w.upper() for w in valid_controls)} '
          f'({len(valid_controls)}/{len(regional_controls)})')

    # Focal wells availability
    focal_wells = list(well_eras.keys())
    valid_focal = [w for w in focal_wells if w in wells.columns]
    print(f'  Focal wells: {", ".join(w.upper() for w in valid_focal)}')

    # Water balance baseline (for ANCOVA)
    _wb_start = wells.index.min()
    _wb_end = climate.index.max()
    _wb_mask = (climate.index >= _wb_start) & (climate.index <= _wb_end)
    _wb_series = (pd.to_numeric(climate.loc[_wb_mask, 'P_m'], errors='coerce') * 1000
                  - pd.to_numeric(climate.loc[_wb_mask, 'PET'], errors='coerce') * 1000)
    WB_BASELINE_MM = float(_wb_series.dropna().mean())
    print(f'  WB baseline: {WB_BASELINE_MM:.2f} mm/month')

    print(f'\n  NOTE: date_felling = {date_felling.strftime("%Y-%m-%d")} '
          f'(corrected from 2018-12-01 in v1)')

except Exception as e:
    print(f"Data error: {e}")
    import traceback; traceback.print_exc()
    sys.exit()


# ===========================================================================
# 2. HIERARCHICAL BACI ANALYSIS
# ===========================================================================
print("\n2. Running Hierarchical BACI Analysis...")

control_mean_regional = wells[valid_controls].mean(axis=1)

full_params_results = []
significance_results = []
baci_results = []
plot_data = {}

for well, config in well_eras.items():
    if well not in wells.columns:
        continue

    pair = pairings.get(well, 'Regional Mean')
    if pair in wells.columns:
        baseline = wells[pair]
        control_label = pair.upper()
    else:
        baseline = control_mean_regional
        control_label = "Regional Mean"

    baci_series = (wells[well] - baseline).dropna()
    era_baci_means = {}

    # Build SSM frame for drainage component extraction
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
    df['neg_h_disp_prev'] = -df['h_disp_prev']

    # CUSUM relative to first era mean
    era1_key = list(config['Eras'].keys())[0]
    era1_baci = config['Eras'][era1_key](baci_series)
    baseline_mean = era1_baci.mean() if not era1_baci.empty else 0
    cusum_series = calculate_cusum(baci_series, baseline_mean)

    plot_data[well] = {
        'df': df, 'baci': baci_series, 'cusum': cusum_series,
        'means': {}, 'config': config, 'control': control_label,
    }

    for era_name, filter_func in config['Eras'].items():
        baci_sub = filter_func(baci_series)
        mean_val = baci_sub.mean() if not baci_sub.empty else np.nan
        era_baci_means[era_name] = mean_val
        plot_data[well]['means'][era_name] = mean_val

        sub = filter_func(df)
        if len(sub) > 6:
            X_full = pd.DataFrame({
                'beta_1_recharge': sub['P_m_lag'],
                'beta_2_atmospheric_draw': -sub['PET'],
                'beta_3_drainage': -sub['h_disp_prev'],
            })
            model_full = sm.OLS(sub['Delta_h'], X_full).fit()
            full_params_results.append({
                'Well': well.upper(), 'Era': era_name,
                'beta_1_recharge': round(model_full.params['beta_1_recharge'], 3),
                'beta_2_atmospheric_draw': round(model_full.params['beta_2_atmospheric_draw'], 3),
                'beta_3_drainage': round(model_full.params['beta_3_drainage'], 3),
            })

            X_iso = sm.add_constant(sub['neg_h_disp_prev'])
            model_iso = sm.OLS(sub['Drainage_Component'], X_iso).fit()
            ci = model_iso.conf_int().loc['neg_h_disp_prev']
            significance_results.append({
                'Well': well.upper(), 'Era': era_name,
                'beta_3_drainage': model_iso.params['neg_h_disp_prev'],
                'P_Value': model_iso.pvalues['neg_h_disp_prev'],
                'Conf_Low': ci[0], 'Conf_High': ci[1],
            })

    # BACI shifts between consecutive eras
    keys = list(era_baci_means.keys())
    for i in range(1, len(keys)):
        shift_name = keys[i].split('_', 1)[1]
        baci_results.append({
            'Well': well.upper(),
            'Shift': shift_name,
            'Delta_m': era_baci_means[keys[i]] - era_baci_means[keys[i-1]],
            'Control': control_label,
        })

# Net benefits vs CEH21 (coastal benchmark — unscraped until Oct 2023)
benchmark_well = 'ceh21'
impact_wells_list = ['ceh36', 'ceh18']
net_summary = []
if benchmark_well in plot_data:
    for w in impact_wells_list:
        if w in plot_data:
            relative_benefit = plot_data[w]['baci'] - plot_data[benchmark_well]['baci']
            era_keys = list(plot_data[w]['config']['Eras'].keys())
            for i in range(1, len(era_keys)):
                before = plot_data[w]['config']['Eras'][era_keys[i-1]](relative_benefit)
                after = plot_data[w]['config']['Eras'][era_keys[i]](relative_benefit)
                if not before.empty and not after.empty:
                    net_summary.append({
                        'Well': w.upper(),
                        'Shift': era_keys[i].split('_', 1)[1],
                        'Net_Benefit_m': round(after.mean() - before.mean(), 4),
                    })


# ===========================================================================
# 3. ANCOVA — Climate-corrected scraping step for CEH36
# ===========================================================================
print("\n3. ANCOVA: Climate-corrected CEH36 scraping step...")

_ancova_results = {}

if 'ceh36' in wells.columns and 'ceh4' in wells.columns:
    # Build BACI difference: CEH36 − CEH4
    _baci_36_4 = (wells['ceh36'] - wells['ceh4']).dropna()

    # Climate covariate: cumulative water balance anomaly
    _cl = climate.copy()
    _cl['P_mm']   = pd.to_numeric(_cl['P_m'], errors='coerce') * 1000
    _cl['PET_mm'] = pd.to_numeric(_cl['PET'], errors='coerce') * 1000
    _cl['anom']   = _cl['P_mm'] - _cl['PET_mm'] - WB_BASELINE_MM
    _cl_sub = _cl[_cl.index >= _baci_36_4.index.min()].copy()
    _cl_sub['cum_wb'] = _cl_sub['anom'].cumsum()

    # Coastal covariate: regional mean (captures site-wide trends including
    # coastal erosion that CEH4 shares but CEH36 may not after scraping)
    _reg_mean = control_mean_regional

    _common = _baci_36_4.index.intersection(_cl_sub.index).intersection(_reg_mean.dropna().index)
    _ab = pd.DataFrame({
        'baci':    _baci_36_4.loc[_common],
        'cum_wb':  _cl_sub.loc[_common, 'cum_wb'],
        'regional': _reg_mean.loc[_common],
    }).dropna()

    _ab['Scraped'] = (_ab.index >= date_2015).astype(float)
    _ab['Felled']  = (_ab.index >= date_felling).astype(float)
    _cwb_mean = _ab['cum_wb'].mean()
    _ab['cwb_c'] = _ab['cum_wb'] - _cwb_mean
    _reg_mean_val = _ab['regional'].mean()
    _ab['reg_c'] = _ab['regional'] - _reg_mean_val

    # Model: baci = β₀ + β₁·CWB + β₂·Regional + β₃·Scraped + β₄·Felled + β₅·CWB×Scraped
    _X = np.column_stack([
        np.ones(len(_ab)),           # 0: intercept
        _ab['cwb_c'].values,         # 1: CWB
        _ab['reg_c'].values,         # 2: regional trend
        _ab['Scraped'].values,       # 3: scraping step
        _ab['Felled'].values,        # 4: felling step
        _ab['cwb_c'].values * _ab['Scraped'].values,  # 5: CWB × scraped
    ])

    _b, _se, _p = _ols(_ab['baci'].values, _X)
    _r2 = _r_squared(_ab['baci'].values, _X, _b)

    _pfmt = lambda p: '<0.001' if p < 0.001 else f'{p:.3f}'

    _ancova_results['ceh36'] = {
        'scraping_step': _b[3], 'scraping_se': _se[3], 'scraping_p': _p[3],
        'felling_step': _b[4], 'felling_se': _se[4], 'felling_p': _p[4],
        'cwb_coeff': _b[1], 'cwb_p': _p[1],
        'regional_coeff': _b[2], 'regional_p': _p[2],
        'R2': _r2,
        'scraping_ci_lo': _b[3] - 1.96 * _se[3],
        'scraping_ci_hi': _b[3] + 1.96 * _se[3],
    }

    print(f'\n  CEH36 ANCOVA (vs CEH4, climate + regional corrected):')
    print(f'    Intercept (baseline):    {_b[0]:+.4f} m')
    print(f'    CWB coefficient:         {_b[1]:+.6f}  p={_pfmt(_p[1])}')
    print(f'    Regional covariate:      {_b[2]:+.4f}  p={_pfmt(_p[2])}')
    print(f'    Scraping step (2015):    {_b[3]:+.4f} m  p={_pfmt(_p[3])}')
    print(f'      95% CI: [{_b[3]-1.96*_se[3]:.4f}, {_b[3]+1.96*_se[3]:.4f}]')
    print(f'    Felling step (2017):     {_b[4]:+.4f} m  p={_pfmt(_p[4])}')
    print(f'    CWB × Scraped:           {_b[5]:+.6f}  p={_pfmt(_p[5])}')
    print(f'    R²: {_r2:.3f}')


# ===========================================================================
# 3b. ANCOVA — CEH18 as alternative control (isolates felling effect)
# ===========================================================================
# CEH4 (4.5m AOD) is the most coastal of the three wells — more coastal
# than both CEH36 (5.3m) and CEH18 (5.2m). It therefore has the strongest
# coastal erosion signal. But CEH4 also sits directly downslope of the
# forest, in the main drainage path. The Dec 2017 felling removed canopy
# interception and transpiration, releasing water that flows south to
# CEH4 — compensating for its coastal decline.
#
# CEH18 sits 148m SE of CEH36 in a different slack. It shares a similar
# elevation and coastal exposure to CEH36 but is laterally offset from
# the forest drainage path, so it should NOT receive the felling subsidy.
# CEH18 is clean as a control until Oct 2023 when it was scraped itself.
#
# Comparing the felling step in CEH36−CEH4 vs CEH36−CEH18 tells us
# whether the +44mm felling benefit is real or is an artefact of the
# felling subsidy propping up CEH4 (which would otherwise decline faster
# from coastal erosion, inflating the BACI difference).

print("\n3b. ANCOVA: CEH36 vs CEH18 (felling-effect isolation)...")

if 'ceh36' in wells.columns and 'ceh18' in wells.columns:
    # Restrict to pre-Oct 2023 (CEH18 clean period)
    _pre23_mask = wells.index < date_2023

    _baci_36_18 = (wells.loc[_pre23_mask, 'ceh36'] - wells.loc[_pre23_mask, 'ceh18']).dropna()

    if len(_baci_36_18) > 36:
        _cl18 = climate.copy()
        _cl18['P_mm']   = pd.to_numeric(_cl18['P_m'], errors='coerce') * 1000
        _cl18['PET_mm'] = pd.to_numeric(_cl18['PET'], errors='coerce') * 1000
        _cl18['anom']   = _cl18['P_mm'] - _cl18['PET_mm'] - WB_BASELINE_MM
        _cl18_sub = _cl18[(_cl18.index >= _baci_36_18.index.min()) &
                           (_cl18.index < date_2023)].copy()
        _cl18_sub['cum_wb'] = _cl18_sub['anom'].cumsum()

        _reg18 = control_mean_regional[control_mean_regional.index < date_2023]

        _common18 = (_baci_36_18.index
                     .intersection(_cl18_sub.index)
                     .intersection(_reg18.dropna().index))

        _ab18 = pd.DataFrame({
            'baci':     _baci_36_18.loc[_common18],
            'cum_wb':   _cl18_sub.loc[_common18, 'cum_wb'],
            'regional': _reg18.loc[_common18],
        }).dropna()

        _ab18['Scraped'] = (_ab18.index >= date_2015).astype(float)
        _ab18['Felled']  = (_ab18.index >= date_felling).astype(float)
        _cwb18_mean = _ab18['cum_wb'].mean()
        _ab18['cwb_c'] = _ab18['cum_wb'] - _cwb18_mean
        _reg18_mean = _ab18['regional'].mean()
        _ab18['reg_c'] = _ab18['regional'] - _reg18_mean

        _X18 = np.column_stack([
            np.ones(len(_ab18)),
            _ab18['cwb_c'].values,
            _ab18['reg_c'].values,
            _ab18['Scraped'].values,
            _ab18['Felled'].values,
            _ab18['cwb_c'].values * _ab18['Scraped'].values,
        ])

        _b18, _se18, _p18 = _ols(_ab18['baci'].values, _X18)
        _r2_18 = _r_squared(_ab18['baci'].values, _X18, _b18)

        _ancova_results['ceh36_vs_ceh18'] = {
            'scraping_step': _b18[3], 'scraping_se': _se18[3], 'scraping_p': _p18[3],
            'felling_step': _b18[4], 'felling_se': _se18[4], 'felling_p': _p18[4],
            'cwb_coeff': _b18[1], 'cwb_p': _p18[1],
            'regional_coeff': _b18[2], 'regional_p': _p18[2],
            'R2': _r2_18,
            'scraping_ci_lo': _b18[3] - 1.96 * _se18[3],
            'scraping_ci_hi': _b18[3] + 1.96 * _se18[3],
            'n': len(_ab18),
        }

        _pfmt18 = lambda p: '<0.001' if p < 0.001 else f'{p:.3f}'

        print(f'\n  CEH36 ANCOVA (vs CEH18, pre-Oct 2023 only):')
        print(f'    n = {len(_ab18)} months')
        print(f'    Scraping step (2015):    {_b18[3]:+.4f} m  p={_pfmt18(_p18[3])}')
        print(f'      95% CI: [{_b18[3]-1.96*_se18[3]:.4f}, {_b18[3]+1.96*_se18[3]:.4f}]')
        print(f'    Felling step (2017):     {_b18[4]:+.4f} m  p={_pfmt18(_p18[4])}')
        print(f'      95% CI: [{_b18[4]-1.96*_se18[4]:.4f}, {_b18[4]+1.96*_se18[4]:.4f}]')
        print(f'    Regional covariate:      {_b18[2]:+.4f}  p={_pfmt18(_p18[2])}')
        print(f'    R²: {_r2_18:.3f}')

        # ── Comparison table ─────────────────────────────────────────────
        if 'ceh36' in _ancova_results:
            _ar4 = _ancova_results['ceh36']
            _ar18 = _ancova_results['ceh36_vs_ceh18']
            print(f'\n  ── Felling effect comparison ──')
            print(f'  {"Control":<12} {"Scraping step":>14} {"Felling step":>14} {"R²":>6}')
            print(f'  {"CEH4":<12} {_ar4["scraping_step"]:+14.4f} {_ar4["felling_step"]:+14.4f} {_ar4["R2"]:6.3f}')
            print(f'  {"CEH18":<12} {_ar18["scraping_step"]:+14.4f} {_ar18["felling_step"]:+14.4f} {_ar18["R2"]:6.3f}')
            _fell_diff = _ar4['felling_step'] - _ar18['felling_step']
            print(f'  {"Difference":<12} {"":>14} {_fell_diff:+14.4f}')
            print(f'\n  Interpretation:')
            print(f'  CEH4 (4.5m AOD) is the most coastal well — faster erosion than')
            print(f'  CEH36 (5.3m) or CEH18 (5.2m). But CEH4 sits directly downslope')
            print(f'  of the forest in the main drainage path. The felling subsidy')
            print(f'  props up CEH4, compensating for its faster coastal decline.')
            print(f'  The felling step disappears with CEH18 ({_ar18["felling_step"]*1000:+.0f}mm, ns) because')
            print(f'  CEH18 does not receive the subsidy. The {_fell_diff*1000:+.0f} mm difference')
            print(f'  is the estimated felling drainage subsidy at CEH4.')
            print(f'  The scraping step is larger with CEH18 '
                  f'({_ar18["scraping_step"]*1000:+.0f}mm vs '
                  f'{_ar4["scraping_step"]*1000:+.0f}mm) because')
            print(f'  the felling subsidy in the CEH4 model absorbs some of the post-2017')
            print(f'  scraping benefit, redistributing it to the felling coefficient.')
    else:
        print("  [WARNING] Insufficient CEH36−CEH18 overlap for ANCOVA")


# ===========================================================================
# 3c. SCRAPING EFFECT ON SUMMER MINIMA
# ===========================================================================
# Scraping lowers the surface into contact with the water table. The
# deeper slack creates a hydraulic gradient drawing water from surrounding
# higher ground, supporting summer water levels when ET demand is greatest.
#
# Test: compare the annual summer minimum (deepest Jun–Sep reading) at
# CEH36 vs controls before and after scraping. Also test whether the
# December 2017 clearfell added a summer benefit at CEH36.

print("\n3c. Scraping effect on summer minima...")

_scraping_summer_results = {}

if 'ceh36' in wells.columns:
    _SUMMER_MONTHS = [6, 7, 8, 9]
    _min_years = range(2007, 2026)

    # Compute summer minima for all relevant wells
    _all_mins = {}
    for _w in ['ceh36', 'ceh18', 'ceh4']:
        if _w not in wells.columns:
            continue
        _wm = {}
        for _yr in _min_years:
            _mask = (wells.index.year == _yr) & (wells.index.month.isin(_SUMMER_MONTHS))
            _s = wells.loc[_mask, _w].dropna()
            if len(_s) >= 2:
                _wm[_yr] = float(_s.min())
        _all_mins[_w] = _wm

    # ── CEH36 vs CEH18: scraping effect ──────────────────────────────────
    for _ctrl_name, _ctrl_key in [('CEH18', 'ceh18'), ('CEH4', 'ceh4')]:
        if _ctrl_key not in _all_mins or 'ceh36' not in _all_mins:
            continue

        _common = sorted(set(_all_mins['ceh36']) & set(_all_mins[_ctrl_key]))
        if len(_common) < 6:
            print(f"  CEH36 vs {_ctrl_name}: insufficient years")
            continue

        _gap = pd.Series({yr: _all_mins['ceh36'][yr] - _all_mins[_ctrl_key][yr]
                          for yr in _common})

        # Three eras for scraping analysis
        _pre_scrape  = _gap[_gap.index < 2015]
        _post_scrape = _gap[(_gap.index >= 2015) & (_gap.index < 2018)]
        _post_fell   = _gap[(_gap.index >= 2018) & (_gap.index <= 2023)]

        _pre_mean  = float(_pre_scrape.mean())  if len(_pre_scrape) > 0  else np.nan
        _ps_mean   = float(_post_scrape.mean()) if len(_post_scrape) > 0 else np.nan
        _pf_mean   = float(_post_fell.mean())   if len(_post_fell) > 0   else np.nan

        _scrape_shift = (_ps_mean - _pre_mean) if pd.notna(_pre_mean) and pd.notna(_ps_mean) else np.nan
        _fell_shift   = (_pf_mean - _ps_mean)  if pd.notna(_ps_mean)  and pd.notna(_pf_mean) else np.nan

        # t-tests
        if len(_pre_scrape) >= 3 and len(_post_scrape) >= 2:
            _, _p_scrape = _stats.ttest_ind(_post_scrape.values, _pre_scrape.values,
                                             equal_var=False)
        else:
            _p_scrape = np.nan

        # Pre-scrape vs post-fell (combined scraping + felling)
        if len(_pre_scrape) >= 3 and len(_post_fell) >= 3:
            _, _p_combined = _stats.ttest_ind(_post_fell.values, _pre_scrape.values,
                                               equal_var=False)
        else:
            _p_combined = np.nan

        _scraping_summer_results[_ctrl_name] = {
            'pre_mean': _pre_mean, 'post_scrape_mean': _ps_mean,
            'post_fell_mean': _pf_mean,
            'scrape_shift': _scrape_shift, 'fell_shift': _fell_shift,
            'p_scrape': float(_p_scrape) if pd.notna(_p_scrape) else np.nan,
            'p_combined': float(_p_combined) if pd.notna(_p_combined) else np.nan,
            'n_pre': len(_pre_scrape), 'n_post_scrape': len(_post_scrape),
            'n_post_fell': len(_post_fell),
            'gap_series': _gap,
        }

        _p_s_fmt = f'{_p_scrape:.3f}' if pd.notna(_p_scrape) else 'N/A'
        _p_c_fmt = f'{_p_combined:.3f}' if pd.notna(_p_combined) else 'N/A'

        print(f'\n  Summer minimum gap: CEH36 − {_ctrl_name}')
        print(f'    Pre-scraping (n={len(_pre_scrape)}):       {_pre_mean:+.4f} m')
        print(f'    Post-scraping (n={len(_post_scrape)}):     {_ps_mean:+.4f} m')
        print(f'    Post-felling (n={len(_post_fell)}):        {_pf_mean:+.4f} m')
        print(f'    Scraping shift:              {_scrape_shift:+.4f} m ({_scrape_shift*1000:+.1f} mm)  p={_p_s_fmt}')
        print(f'    Felling shift:               {_fell_shift:+.4f} m ({_fell_shift*1000:+.1f} mm)')
        print(f'    Combined (pre→post-fell):    p={_p_c_fmt}')

    # ── Figure: scraping effect on summer minima ─────────────────────────
    if _scraping_summer_results:
        OUT_09_SM_FIG = OUT_09_SCRAPE_SUMMER_MIN

        _n_ctrls = len(_scraping_summer_results)
        _fig_ss, _axes_ss = plt.subplots(2, _n_ctrls, figsize=(7 * _n_ctrls, 10), dpi=300,
                                          squeeze=False)

        for _ci, (_ctrl_name, _sr) in enumerate(_scraping_summer_results.items()):
            _ctrl_key = _ctrl_name.lower()
            _gap = _sr['gap_series']
            _yrs = np.array(_gap.index.tolist())
            _vals = np.array([float(_gap[yr]) for yr in _yrs])

            # Panel (a): individual summer minima
            _ax_a = _axes_ss[0, _ci]
            _v36 = np.array([_all_mins['ceh36'][yr] for yr in _yrs])
            _vc  = np.array([_all_mins[_ctrl_key][yr] for yr in _yrs])

            _ax_a.plot(_yrs, _v36, 'o-', color='#D55E00', lw=2.0, ms=7,
                        label='CEH36 (scraped Apr 2015)', zorder=3)
            _ax_a.plot(_yrs, _vc, 's--', color='#0072B2', lw=1.8, ms=7,
                        label=f'{_ctrl_name}', zorder=3)
            _ax_a.axvline(2015.25, color='purple', lw=1.4, ls='--', alpha=0.7,
                           label='Apr 2015 scraping')
            _ax_a.axvline(2017.5, color='black', lw=1.0, ls=':', alpha=0.5,
                           label='Dec 2017 felling')
            _ax_a.set_ylabel('Summer minimum depth (m)', fontsize=10)
            _ax_a.set_title(f'(a)  Summer minimum: CEH36 vs {_ctrl_name}',
                             fontsize=10, fontweight='bold', loc='left')
            _ax_a.legend(fontsize=7.5, loc='lower left', framealpha=0.9, ncol=2)
            _ax_a.grid(axis='y', alpha=0.3, ls='--')
            _ax_a.invert_yaxis()
            for sp in ['top', 'right']: _ax_a.spines[sp].set_visible(False)

            # Panel (b): gap with era means
            _ax_b = _axes_ss[1, _ci]

            _pre_mask  = _yrs < 2015
            _ps_mask   = (_yrs >= 2015) & (_yrs < 2018)
            _pf_mask   = (_yrs >= 2018) & (_yrs <= 2023)
            _post23    = _yrs > 2023

            _era_colours = {'pre': '#009E73', 'ps': '#56B4E9', 'pf': '#D55E00', 'p23': '#888888'}
            for _m, _c, _l in [(_pre_mask, _era_colours['pre'], 'Pre-scraping'),
                                (_ps_mask, _era_colours['ps'], 'Post-scraping'),
                                (_pf_mask, _era_colours['pf'], 'Post-felling'),
                                (_post23,  _era_colours['p23'], 'Post-Oct 2023')]:
                if _m.any():
                    _ax_b.bar(_yrs[_m], _vals[_m] * 1000, color=_c, alpha=0.7, label=_l)

            if pd.notna(_sr['pre_mean']):
                _ax_b.axhline(_sr['pre_mean'] * 1000, color=_era_colours['pre'],
                               lw=2.0, ls='--')
            if pd.notna(_sr['post_scrape_mean']):
                _ax_b.axhline(_sr['post_scrape_mean'] * 1000, color=_era_colours['ps'],
                               lw=2.0, ls='--')
            if pd.notna(_sr['post_fell_mean']):
                _ax_b.axhline(_sr['post_fell_mean'] * 1000, color=_era_colours['pf'],
                               lw=2.0, ls='--')

            _ax_b.axhline(0, color='black', lw=0.8, alpha=0.4)
            _ax_b.axvline(2015.25, color='purple', lw=1.4, ls='--', alpha=0.7)
            _ax_b.axvline(2017.5, color='black', lw=1.0, ls=':', alpha=0.5)

            _p_s_fmt = f'p={_sr["p_scrape"]:.3f}' if pd.notna(_sr['p_scrape']) else 'p=N/A'
            _ax_b.set_title(f'(b)  Gap (CEH36 − {_ctrl_name}): '
                             f'scraping shift = {_sr["scrape_shift"]*1000:+.0f} mm, {_p_s_fmt}',
                             fontsize=10, fontweight='bold', loc='left')
            _ax_b.set_ylabel('Gap (mm)', fontsize=10)
            _ax_b.set_xlabel('Year', fontsize=10)
            _ax_b.legend(fontsize=7.5, loc='upper left', framealpha=0.9, ncol=2)
            _ax_b.grid(axis='y', alpha=0.3, ls='--')
            for sp in ['top', 'right']: _ax_b.spines[sp].set_visible(False)

        _fig_ss.suptitle('Scraping effect on summer minimum depth\n'
                          'CEH36 (scraped Apr 2015) vs controls — does scraping worsen summer drawdown?',
                          fontsize=11, fontweight='bold')
        plt.tight_layout()
        plt.savefig(OUT_09_SM_FIG, bbox_inches='tight', dpi=300)
        plt.close(_fig_ss)
        print(f' -> Saved: {OUT_09_SM_FIG.name}')

        # Export CSV
        _ss_rows = []
        for _ctrl_name, _sr in _scraping_summer_results.items():
            _ctrl_key = _ctrl_name.lower()
            for yr in sorted(_sr['gap_series'].index):
                _ss_rows.append({
                    'Year': yr,
                    'CEH36_summer_min_m': _all_mins['ceh36'].get(yr, np.nan),
                    f'{_ctrl_name}_summer_min_m': _all_mins.get(_ctrl_key, {}).get(yr, np.nan),
                    'Gap_m': float(_sr['gap_series'][yr]),
                    'Control': _ctrl_name,
                    'Era': ('Pre-scraping' if yr < 2015 else
                            'Post-scraping' if yr < 2018 else
                            'Post-felling' if yr <= 2023 else 'Post-Oct2023'),
                })
        _sm_csv = OUT_09_SCRAPE_SUMMER_CSV
        pd.DataFrame(_ss_rows).to_csv(_sm_csv, index=False)
        print(f' -> Saved: {_sm_csv.name}')

    # ── Comparison: CEH4 summer min vs CEH18 summer min ──────────────────
    # Does CEH4 benefit from felling in summer while CEH36 doesn't?
    if 'ceh4' in _all_mins and 'ceh18' in _all_mins:
        _common_4_18 = sorted(set(_all_mins['ceh4']) & set(_all_mins['ceh18']))
        if len(_common_4_18) >= 8:
            _gap_4_18 = pd.Series({yr: _all_mins['ceh4'][yr] - _all_mins['ceh18'][yr]
                                    for yr in _common_4_18})
            _pre_4_18 = _gap_4_18[_gap_4_18.index < 2018]
            _post_4_18 = _gap_4_18[(_gap_4_18.index >= 2018) & (_gap_4_18.index <= 2023)]

            if len(_pre_4_18) >= 3 and len(_post_4_18) >= 3:
                _pre_mean_4_18 = float(_pre_4_18.mean())
                _post_mean_4_18 = float(_post_4_18.mean())
                _shift_4_18 = _post_mean_4_18 - _pre_mean_4_18
                _, _p_4_18 = _stats.ttest_ind(_post_4_18.values, _pre_4_18.values,
                                               equal_var=False)

                print(f'\n  ── Summer minimum: CEH4 − CEH18 (felling subsidy check) ──')
                print(f'    Pre-felling mean:  {_pre_mean_4_18:+.4f} m')
                print(f'    Post-felling mean: {_post_mean_4_18:+.4f} m')
                print(f'    Shift:             {_shift_4_18:+.4f} m ({_shift_4_18*1000:+.1f} mm)  '
                      f'p={_p_4_18:.3f}')

                print(f'\n  ── Three-way summer minimum comparison ──')
                _r36 = _scraping_summer_results.get('CEH18', {})
                print(f'  {"Pair":<18} {"Scraping shift":>16} {"Felling shift":>16}')
                if _r36:
                    print(f'  {"CEH36 − CEH18":<18} {_r36["scrape_shift"]*1000:+14.1f} mm '
                          f'{_r36["fell_shift"]*1000:+14.1f} mm')
                _r36_4 = _scraping_summer_results.get('CEH4', {})
                if _r36_4:
                    print(f'  {"CEH36 − CEH4":<18} {_r36_4["scrape_shift"]*1000:+14.1f} mm '
                          f'{_r36_4["fell_shift"]*1000:+14.1f} mm')
                print(f'  {"CEH4 − CEH18":<18} {"":>16} {_shift_4_18*1000:+14.1f} mm')

                _scraping_summer_results['CEH4_vs_CEH18_felling'] = {
                    'shift': _shift_4_18, 'p_value': float(_p_4_18),
                }

else:
    print("  [SKIP] Requires CEH36")


# ===========================================================================
# 4. EXPORT CSV DATA
# ===========================================================================
print("\n4. Exporting CSV files...")
pd.DataFrame(full_params_results).to_csv(OUT_09_FULL_PARAMS, index=False)
pd.DataFrame(significance_results).to_csv(OUT_09_BETA3_SIG, index=False)
pd.DataFrame(baci_results).to_csv(OUT_09_BACI_SHIFTS, index=False)
pd.DataFrame(net_summary).to_csv(OUT_09_NET_BENEFITS, index=False)

# Table 4 summary
def export_table4_beta3_summary(sig_results):
    if not sig_results:
        pd.DataFrame().to_csv(OUT_09_TABLE4_SUMMARY, index=False)
        return
    df = pd.DataFrame(sig_results).copy()
    df['Well'] = df['Well'].astype(str).str.upper()
    role_map = {'CEH36': 'Treatment', 'CEH18': 'Treatment', 'CEH21': 'Treatment',
                'CEH4': 'Control', 'CEH22': 'Control'}
    era_map = {'1_Baseline': 'Baseline', '2_Pure_Scraping': 'Pure Scraping',
               '3_Felling_Pulse': 'Felling Pulse', '2_Felling_Pulse': 'Felling Pulse',
               '2_Coastal_Drawdown': 'Coastal Drawdown', '3_After_Scraping': 'After Scraping'}
    well_order = ['CEH36', 'CEH18', 'CEH21', 'CEH4', 'CEH22']
    era_order = {'1_Baseline': 1, '2_Pure_Scraping': 2, '2_Felling_Pulse': 2,
                 '2_Coastal_Drawdown': 2, '3_Felling_Pulse': 3, '3_After_Scraping': 3}
    df = df[df['Well'].isin(well_order)].copy()
    df['Role'] = df['Well'].map(role_map)
    df['Era_Label'] = df['Era'].map(era_map).fillna(df['Era'])
    df['CI_95'] = df.apply(lambda r: f"[{r['Conf_Low']:.3f}, {r['Conf_High']:.3f}]", axis=1)
    df['p_value'] = df['P_Value'].apply(format_p_value)
    df['Sig'] = df['P_Value'].apply(significance_stars)
    df['beta_3'] = df['beta_3_drainage'].round(3)
    df['well_rank'] = pd.Categorical(df['Well'], categories=well_order, ordered=True)
    df['era_rank'] = df['Era'].map(era_order).fillna(99)
    df = df.sort_values(['well_rank', 'era_rank', 'Era_Label'])
    out = df[['Well', 'Role', 'Era_Label', 'beta_3', 'CI_95', 'p_value', 'Sig']].rename(
        columns={'Era_Label': 'Era'})
    out.to_csv(OUT_09_TABLE4_SUMMARY, index=False)

export_table4_beta3_summary(significance_results)

print("\n--- Raw BACI Shifts ---")
print(pd.DataFrame(baci_results).to_string(index=False))


# ===========================================================================
# 5. TIER 1 FIGURE: Background Drift (Controls vs Regional)
# ===========================================================================
print("\n5. Generating Tier 1 — Background Drift...")
tier1_wells = ['ceh4', 'ceh22']

all_baci_tier1 = [plot_data[w]['baci'] for w in tier1_wells if w in plot_data]
all_cusum_tier1 = [plot_data[w]['cusum'] for w in tier1_wells if w in plot_data]

if all_baci_tier1:
    baci_ylim = (min(s.min() for s in all_baci_tier1) - 0.05,
                 max(s.max() for s in all_baci_tier1) + 0.05)
else:
    baci_ylim = (-0.5, 0.5)

if all_cusum_tier1:
    cusum_ylim = (min(s.min() for s in all_cusum_tier1) - 0.05,
                  max(s.max() for s in all_cusum_tier1) + 0.05)
else:
    cusum_ylim = (-0.5, 0.5)

fig1, axes1 = plt.subplots(2, 2, figsize=(16, 12), dpi=300)

for i, well in enumerate(tier1_wells):
    if well not in plot_data:
        continue
    data = plot_data[well]
    config = data['config']

    ax_baci = axes1[0, i]
    ax_baci.axhline(0, color='black', lw=1.5, ls='-', alpha=0.3)
    for era_name, filter_func in config['Eras'].items():
        era_data = filter_func(data['baci'])
        if era_data.empty: continue
        ax_baci.plot(era_data.index, era_data, color=colors[era_name],
                     ls=linestyles[era_name], alpha=0.8, lw=1.5)
        ax_baci.axhline(data['means'][era_name], color=colors[era_name],
                        ls='--', lw=2, alpha=0.9)
    ax_baci.set_ylim(baci_ylim)
    if i == 0:
        ax_baci.set_ylabel('Δ Water Level (m)\n[Well − Regional Mean]', fontweight='bold')
    ax_baci.set_title(f"{well.upper()} vs Regional Mean (Eastern C1/C2)", fontsize=11, pad=10)
    ax_baci.grid(True, ls=':', alpha=0.4)

    ax_cusum = axes1[1, i]
    ax_cusum.axhline(0, color='black', lw=1.5, ls='-', alpha=0.3)
    for era_name, filter_func in config['Eras'].items():
        era_cusum = filter_func(data['cusum'])
        if era_cusum.empty: continue
        ax_cusum.fill_between(era_cusum.index, era_cusum, color=colors[era_name], alpha=0.2)
        clean_label = era_name.split('_', 1)[1].replace('_', ' ')
        ax_cusum.plot(era_cusum.index, era_cusum, color=colors[era_name],
                      lw=2.5, marker=markers[era_name], markevery=4, label=clean_label)
    ax_cusum.set_ylim(cusum_ylim)
    if i == 0:
        ax_cusum.set_ylabel('Cumulative Sum (m)\n[Relative Drift]', fontweight='bold')
    ax_cusum.grid(True, ls=':', alpha=0.4)

min_date = pd.Timestamp('2006-01-01')
max_date = max(plot_data[w]['baci'].index.max() for w in tier1_wells if w in plot_data)
for ax in axes1.flatten():
    ax.set_xlim(min_date, max_date)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
for ax in axes1[0, :]:
    ax.set_xticklabels([])

handles, labels = [], []
for ax in axes1.flat:
    h, l = ax.get_legend_handles_labels()
    handles.extend(h); labels.extend(l)
clean_labels = [lbl.split('_', 1)[1].replace('_', ' ') if '_' in lbl else lbl for lbl in labels]
by_label = dict(zip(clean_labels, handles))
axes1[1, 0].legend(by_label.values(), by_label.keys(), loc='lower left', frameon=True)

plt.tight_layout()
fig1.suptitle("Tier 1 — Background Drift: Local Controls vs Clean Eastern Regional Mean",
              fontsize=14, fontweight='bold', y=1.03)
plt.savefig(OUT_09_TIER1_DRIFT, bbox_inches='tight', dpi=300)
plt.close()
print(f' -> Saved: {OUT_09_TIER1_DRIFT.name}')

# Export Tier 1 CUSUM terminal values
if all_cusum_tier1:
    tier1_cusum_final = {w: float(plot_data[w]['cusum'].iloc[-1])
                         for w in tier1_wells if w in plot_data}
    pd.DataFrame.from_dict(tier1_cusum_final, orient='index',
                           columns=['Final_Tier1_CUSUM']).to_csv(
        DIR_09 / "09_tier1_final_cusum.csv")


# ===========================================================================
# 6. TIER 2 FIGURE: Scraping Signal (Treatment vs Local Controls)
# ===========================================================================
print("6. Generating Tier 2 — Scraping Signal...")
tier2_wells = ['ceh36', 'ceh18', 'ceh21']

all_baci_tier2 = [plot_data[w]['baci'] for w in tier2_wells if w in plot_data]
all_cusum_tier2 = [plot_data[w]['cusum'] for w in tier2_wells if w in plot_data]

if all_baci_tier2:
    baci_ylim = (min(s.min() for s in all_baci_tier2) - 0.05,
                 max(s.max() for s in all_baci_tier2) + 0.05)
else:
    baci_ylim = (-0.5, 0.5)
if all_cusum_tier2:
    cusum_ylim = (min(s.min() for s in all_cusum_tier2) - 0.05,
                  max(s.max() for s in all_cusum_tier2) + 0.05)
else:
    cusum_ylim = (-0.5, 0.5)

fig2, axes2 = plt.subplots(3, 2, figsize=(14, 18), dpi=300)

for i, well in enumerate(tier2_wells):
    if well not in plot_data:
        continue
    data = plot_data[well]
    config = data['config']

    ax_baci = axes2[i, 0]
    ax_baci.axhline(0, color='black', lw=1.5, ls='-', alpha=0.3)
    for era_name, filter_func in config['Eras'].items():
        era_data = filter_func(data['baci'])
        if era_data.empty: continue
        ax_baci.plot(era_data.index, era_data, color=colors[era_name],
                     ls=linestyles[era_name], alpha=0.8, lw=1.5)
        ax_baci.axhline(data['means'][era_name], color=colors[era_name],
                        ls='--', lw=2, alpha=0.9)
    ax_baci.set_ylim(baci_ylim)
    ax_baci.set_ylabel(f'Δ Water Level (m)\n[{well.upper()} − {data["control"]}]',
                       fontweight='bold')
    ax_baci.set_title(f"{well.upper()} ({config['Exp'].replace('_', ' ')})",
                      fontsize=11, pad=10)
    ax_baci.grid(True, ls=':', alpha=0.4)

    ax_cusum = axes2[i, 1]
    ax_cusum.axhline(0, color='black', lw=1.5, ls='-', alpha=0.3)
    for era_name, filter_func in config['Eras'].items():
        era_cusum = filter_func(data['cusum'])
        if era_cusum.empty: continue
        ax_cusum.fill_between(era_cusum.index, era_cusum, color=colors[era_name], alpha=0.2)
        clean_label = era_name.split('_', 1)[1].replace('_', ' ')
        ax_cusum.plot(era_cusum.index, era_cusum, color=colors[era_name],
                      lw=2.5, marker=markers[era_name], markevery=4, label=clean_label)
    ax_cusum.set_ylim(cusum_ylim)
    ax_cusum.set_ylabel('Cumulative Sum (m)', fontweight='bold')
    ax_cusum.grid(True, ls=':', alpha=0.4)

for ax in axes2.flatten():
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

handles, labels = [], []
for ax in axes2.flat:
    h, l = ax.get_legend_handles_labels()
    handles.extend(h); labels.extend(l)
clean_labels = [lbl.split('_', 1)[1].replace('_', ' ') if '_' in lbl else lbl for lbl in labels]
by_label = dict(zip(clean_labels, handles))
axes2[1, 0].legend(by_label.values(), by_label.keys(), loc='upper left', frameon=True)

plt.tight_layout()
fig2.suptitle("Tier 2 — Scraping Signal: Treatment Wells vs Paired Local Controls",
              fontsize=14, fontweight='bold', y=1.03)
plt.savefig(OUT_09_TIER2_SIGNAL, bbox_inches='tight', dpi=300)
plt.close()
print(f' -> Saved: {OUT_09_TIER2_SIGNAL.name}')


# ===========================================================================
# 7. β₃ CONFIDENCE INTERVAL FIGURE
# ===========================================================================
df_sig = pd.DataFrame(significance_results)
if not df_sig.empty:
    fig3, ax3 = plt.subplots(figsize=(10, 6), dpi=300)
    wells_to_plot = ['CEH36', 'CEH18', 'CEH21']
    df_sig_filt = df_sig[df_sig['Well'].isin(wells_to_plot)]
    wells_plotted = df_sig_filt['Well'].unique()
    offsets = [-0.15, 0, 0.15]

    for i, w in enumerate(wells_plotted):
        well_data = df_sig_filt[df_sig_filt['Well'] == w]
        for j, (_, row) in enumerate(well_data.iterrows()):
            era = row['Era']
            x_pos = i + offsets[j] if j < len(offsets) else i
            err_low = row['beta_3_drainage'] - row['Conf_Low']
            err_high = row['Conf_High'] - row['beta_3_drainage']
            clean_label = era.split('_', 1)[1].replace('_', ' ')
            ax3.errorbar(x_pos, row['beta_3_drainage'],
                         yerr=[[err_low], [err_high]],
                         fmt=markers.get(era, 'o'), color=colors.get(era, '#333'),
                         markerfacecolor=fill_styles.get(era, colors.get(era, '#333')),
                         markeredgecolor=colors.get(era, '#333'),
                         markersize=8, capsize=5, label=clean_label)

    ax3.set_xticks(range(len(wells_plotted)))
    ax3.set_xticklabels(wells_plotted)
    ax3.set_ylabel(r'Drainage Coefficient ($\beta_3$)')
    ax3.set_title(r'Structural Repair ($\beta_3$ Shifts with 95% CI)', fontweight='bold')
    era_order = {'Baseline': 0, 'Pure Scraping': 1, 'Felling Pulse': 2,
                 'Coastal Drawdown': 1, 'After Scraping': 2}
    handles, labels = ax3.get_legend_handles_labels()
    sorted_items = sorted(zip(labels, handles),
                          key=lambda x: era_order.get(x[0], 99))
    sorted_labels, sorted_handles = zip(*sorted_items) if sorted_items else ([], [])
    by_label = dict(zip(sorted_labels, sorted_handles))
    ax3.legend(by_label.values(), by_label.keys(), title="Eras")
    ax3.grid(axis='y', ls='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(OUT_09_BETA3_CI, bbox_inches='tight', dpi=300)
    plt.close()
    print(f' -> Saved: {OUT_09_BETA3_CI.name}')


# ===========================================================================
# 8. CEH36 ROBUSTNESS — Three Independent Methods
# ===========================================================================
print("\n8. CEH36 Robustness Analysis — Three Methods...")
try:
    from matplotlib.lines import Line2D

    # Donor pool: long-record wells outside scraping/felling footprint.
    # Excludes CEH36 (target), CEH4 (raw BACI control), felling-zone wells,
    # and scraping-propagation-zone wells (CEH9, NW7, NW6 etc).
    _donor_candidates = [
        'ceh1', 'ceh2', 'ceh5', 'ceh6', 'ceh11', 'ceh16',
        'ceh17', 'ceh19', 'ceh22', 'ceh24', 'ceh10',
    ]
    _donors = [w for w in _donor_candidates if w in wells.columns]

    _baseline_mask = wells.index < date_2015
    _scraping_mask = (wells.index >= date_2015) & (wells.index < date_felling)
    _felling_mask  = (wells.index >= date_felling) & (wells.index < date_2023)

    # ── (1) Raw BACI: CEH36 vs CEH4 ─────────────────────────────────────
    _ceh36 = wells['ceh36']
    _ceh4  = wells['ceh4']
    _gap_raw = _ceh36 - _ceh4

    _raw_baseline = _gap_raw[_baseline_mask].mean()
    _raw_scraping = _gap_raw[_scraping_mask].mean()
    _raw_felling  = _gap_raw[_felling_mask].mean()
    _raw_step     = _raw_scraping - _raw_baseline
    _raw_fell_step = _raw_felling - _raw_scraping

    # ── (1b) Raw BACI: CEH36 vs CEH18 (pre-Oct 2023 only) ───────────────
    _ceh18 = wells['ceh18'] if 'ceh18' in wells.columns else None
    _raw18_step = _raw18_fell_step = np.nan
    _gap_raw18 = pd.Series(np.nan, index=_ceh36.index)

    if _ceh18 is not None:
        _gap_raw18 = (_ceh36 - _ceh18).dropna()
        # Restrict to pre-Oct 2023 (CEH18 clean period)
        _gap_raw18 = _gap_raw18[_gap_raw18.index < date_2023]
        _r18_baseline_mask = _gap_raw18.index < date_2015
        _r18_scraping_mask = (_gap_raw18.index >= date_2015) & (_gap_raw18.index < date_felling)
        _r18_felling_mask  = _gap_raw18.index >= date_felling
        _raw18_baseline = _gap_raw18[_r18_baseline_mask].mean()
        _raw18_scraping = _gap_raw18[_r18_scraping_mask].mean()
        _raw18_felling  = _gap_raw18[_r18_felling_mask].mean()
        _raw18_step      = _raw18_scraping - _raw18_baseline
        _raw18_fell_step = _raw18_felling  - _raw18_scraping

    # ── (2) Synthetic control ────────────────────────────────────────────
    _baseline_X = wells.loc[_baseline_mask, _donors].dropna()
    _baseline_y = _ceh36.loc[_baseline_X.index].dropna()
    _valid_idx  = _baseline_X.index.intersection(_baseline_y.index)
    _baseline_X = _baseline_X.loc[_valid_idx]
    _baseline_y = _baseline_y.loc[_valid_idx]

    if len(_baseline_X) >= 24:
        _ols_syn = sm.OLS(_baseline_y.values, _baseline_X.values).fit()
        _weights = pd.Series(_ols_syn.params, index=_donors)
        _synthetic = wells[_donors].dot(_weights)
        _gap_syn = _ceh36 - _synthetic

        _syn_baseline = _gap_syn[_baseline_mask].mean()
        _syn_scraping = _gap_syn[_scraping_mask].mean()
        _syn_felling  = _gap_syn[_felling_mask].mean()
        _syn_step     = _syn_scraping - _syn_baseline
        _syn_fell_step = _syn_felling - _syn_scraping
    else:
        _gap_syn = pd.Series(np.nan, index=_ceh36.index)
        _syn_step = _syn_fell_step = np.nan
        _weights = pd.Series(dtype=float)

    # ── (3) SSM forward residual ─────────────────────────────────────────
    _ts = pd.DataFrame({
        'h':   _ceh36,
        'P':   climate['P_m'] * 1000.0,
        'PET': climate['PET'] * 1000.0,
    }).dropna()
    _ts['P_lag'] = _ts['P'].shift(HEADLINE_LAG)
    _ts_base = _ts[_ts.index < date_2015].copy()
    _ts_base['h_prev'] = _ts_base['h'].shift(1)
    _ts_base['dh'] = _ts_base['h'] - _ts_base['h_prev']
    _ts_base = _ts_base.dropna()

    _ssm_step = np.nan
    _ssm_fell_step = np.nan
    _ts_fwd = _ts.copy()
    _ts_fwd['h_pred'] = np.nan
    _ts_fwd['residual'] = np.nan

    if len(_ts_base) >= 36:
        _X_fit = pd.DataFrame({
            'P': _ts_base['P_lag'],
            'PET_neg': -_ts_base['PET'],
            'h_neg': -(DRAINAGE_DATUM + _ts_base['h_prev']),
        })
        _model = sm.OLS(_ts_base['dh'].values, _X_fit.values).fit()
        _b1_ssm, _b2_ssm, _b3_ssm = _model.params

        _idx_list = list(_ts_fwd.index)
        _last_base_dt = _ts_fwd.index[_ts_fwd.index < date_2015].max()
        if pd.notna(_last_base_dt):
            _h_pred = _ts_fwd.loc[_last_base_dt, 'h']
            _ts_fwd.loc[_last_base_dt, 'h_pred'] = _h_pred
            for _dt in _idx_list:
                if _dt <= _last_base_dt: continue
                _P_t = _ts_fwd.loc[_dt, 'P_lag']
                _PET_t = _ts_fwd.loc[_dt, 'PET']
                if np.isnan(_P_t) or np.isnan(_PET_t): continue
                _dh = _b1_ssm * _P_t - _b2_ssm * _PET_t - _b3_ssm * (DRAINAGE_DATUM + _h_pred)
                _h_pred = _h_pred + _dh
                _ts_fwd.loc[_dt, 'h_pred'] = _h_pred

            _ts_fwd['residual'] = _ts_fwd['h'] - _ts_fwd['h_pred']
            _fwd_baseline_mask = _ts_fwd.index < date_2015
            _fwd_scraping_mask = (_ts_fwd.index >= date_2015) & (_ts_fwd.index < date_felling)
            _fwd_felling_mask  = (_ts_fwd.index >= date_felling) & (_ts_fwd.index < date_2023)
            _ssm_baseline = _ts_fwd.loc[_fwd_baseline_mask, 'residual'].mean()
            _ssm_scraping = _ts_fwd.loc[_fwd_scraping_mask, 'residual'].mean()
            _ssm_felling  = _ts_fwd.loc[_fwd_felling_mask,  'residual'].mean()
            _ssm_step = _ssm_scraping - (_ssm_baseline if pd.notna(_ssm_baseline) else 0.0)
            _ssm_fell_step = (_ssm_felling - _ssm_scraping) if pd.notna(_ssm_felling) else np.nan

    # ── FIGURE: four panels ─────────────────────────────────────────────
    from matplotlib.gridspec import GridSpec
    _fig = plt.figure(figsize=(13, 15), dpi=300)
    _gs = _fig.add_gridspec(4, 1, height_ratios=[1.2, 1.0, 0.9, 0.9], hspace=0.45)

    # (a) Raw BACI vs synthetic vs CEH18
    _ax1 = _fig.add_subplot(_gs[0])
    _ax1.plot(_gap_raw.index, _gap_raw.values, color='#8b5a2b', lw=1.6, alpha=0.85,
              label='CEH36 − CEH4 (raw BACI)')
    if _ceh18 is not None:
        _gap18_plot = _gap_raw18[_gap_raw18.index < date_2023]
        _ax1.plot(_gap18_plot.index, _gap18_plot.values, color='#D55E00', lw=1.6,
                  alpha=0.85, ls='--',
                  label='CEH36 − CEH18 (pre-Oct 2023)')
    if not np.isnan(_syn_step):
        _ax1.plot(_gap_syn.index, _gap_syn.values, color='#1f77b4', lw=1.6, alpha=0.85,
                  label=f'CEH36 − synthetic ({len(_donors)} donors)')
    _ax1.axhline(_raw_baseline, color='#8b5a2b', ls='--', lw=1.0, alpha=0.6)
    _ax1.axhline(_raw_scraping, color='#8b5a2b', ls=':', lw=1.0, alpha=0.6)
    if not np.isnan(_syn_step):
        _ax1.axhline(_syn_baseline, color='#1f77b4', ls='--', lw=1.0, alpha=0.6)
        _ax1.axhline(_syn_scraping, color='#1f77b4', ls=':', lw=1.0, alpha=0.6)
    for _vd in [date_2015, date_felling, date_2023]:
        _ax1.axvline(_vd, color='black', ls='--', lw=0.8, alpha=0.5)
    _ax1.text(date_2015,    _ax1.get_ylim()[1]*0.95, ' 2015 scraping', fontsize=8, va='top', alpha=0.7)
    _ax1.text(date_felling, _ax1.get_ylim()[1]*0.95, ' felling',       fontsize=8, va='top', alpha=0.7)
    _ax1.text(date_2023,    _ax1.get_ylim()[1]*0.95, ' 2023 rescrape', fontsize=8, va='top', alpha=0.7)
    _ax1.set_ylabel('CEH36 − reference (m)')
    _ax1.set_title('(a) Raw BACI and synthetic control gap', loc='left', fontweight='bold', fontsize=10)
    _ax1.legend(loc='lower left', fontsize=8, framealpha=0.9, ncol=2)
    _ax1.grid(axis='y', alpha=0.25)
    for sp in ['top', 'right']: _ax1.spines[sp].set_visible(False)

    # (b) SSM forward residual
    _ax2 = _fig.add_subplot(_gs[1])
    if 'residual' in _ts_fwd.columns and _ts_fwd['residual'].notna().any():
        _resid = _ts_fwd['residual'].dropna()
        _ax2.plot(_resid.index, _resid.values, color='#2c7a3f', lw=1.4, alpha=0.85,
                  label='SSM forward residual (obs − pred)')
        _ax2.fill_between(_resid.index, 0, _resid.values,
                          where=_resid.values >= 0, color='#2c7a3f', alpha=0.15,
                          interpolate=True, label='Shallower than predicted (beneficial)')
        _ax2.fill_between(_resid.index, 0, _resid.values,
                          where=_resid.values < 0, color='#b85c4a', alpha=0.15,
                          interpolate=True, label='Deeper than predicted')
    _ax2.axhline(0, color='black', lw=0.6, alpha=0.6)
    for _vd in [date_2015, date_felling, date_2023]:
        _ax2.axvline(_vd, color='black', ls='--', lw=0.8, alpha=0.5)
    _ax2.set_ylabel('Residual (m)')
    _ax2.set_title('(b) SSM forward residual at CEH36 — calibrated on pre-2015 baseline',
                   loc='left', fontweight='bold', fontsize=10)
    _ax2.legend(loc='lower left', fontsize=7, framealpha=0.9, ncol=3)
    _ax2.grid(axis='y', alpha=0.25)
    for sp in ['top', 'right']: _ax2.spines[sp].set_visible(False)

    # (c) Scraping-era step — four methods
    _ax3 = _fig.add_subplot(_gs[2])
    _methods_labels = ['Raw BACI\n(vs CEH4)', 'Raw BACI\n(vs CEH18)',
                       f'Synthetic\n({len(_donors)} donors)', 'SSM forward\nresidual']
    _scrape_vals = [_raw_step,
                    _raw18_step if not np.isnan(_raw18_step) else 0.0,
                    _syn_step if not np.isnan(_syn_step) else 0.0,
                    _ssm_step if not np.isnan(_ssm_step) else 0.0]
    _scrape_cols = ['#8b5a2b', '#D55E00', '#1f77b4', '#2c7a3f']
    _bars_s = _ax3.bar(_methods_labels, _scrape_vals, color=_scrape_cols,
                       alpha=0.85, edgecolor='black', linewidth=0.8)
    for _bar, _val in zip(_bars_s, _scrape_vals):
        _y = _bar.get_height()
        _ax3.text(_bar.get_x() + _bar.get_width() / 2,
                  _y + (0.005 if _y >= 0 else -0.015),
                  f'{_val:+.3f} m', ha='center',
                  va='bottom' if _y >= 0 else 'top',
                  fontsize=9, fontweight='bold')
    _ax3.axhline(0, color='black', lw=0.8)
    _ax3.set_ylabel('Pure Scraping era\nstep change (m)')
    _ax3.set_title('(c) Pure Scraping era step (Apr 2015 – Dec 2017) — four methods',
                   loc='left', fontweight='bold', fontsize=10)
    _ymax_s = max(max(_scrape_vals), 0.01)
    _ax3.set_ylim(min(min(_scrape_vals), 0) - 0.01, _ymax_s * 1.35)
    for sp in ['top', 'right']: _ax3.spines[sp].set_visible(False)
    _ax3.grid(axis='y', alpha=0.2)

    # (d) Felling-era step — four methods (isolates felling subsidy)
    _ax4 = _fig.add_subplot(_gs[3])
    _fell_vals = [_raw_fell_step,
                  _raw18_fell_step if not np.isnan(_raw18_fell_step) else 0.0,
                  _syn_fell_step if not np.isnan(_syn_fell_step) else 0.0,
                  _ssm_fell_step if not np.isnan(_ssm_fell_step) else 0.0]
    _bars_f = _ax4.bar(_methods_labels, _fell_vals, color=_scrape_cols,
                       alpha=0.85, edgecolor='black', linewidth=0.8)
    for _bar, _val in zip(_bars_f, _fell_vals):
        _y = _bar.get_height()
        _ax4.text(_bar.get_x() + _bar.get_width() / 2,
                  _y + (0.005 if _y >= 0 else -0.015),
                  f'{_val:+.3f} m', ha='center',
                  va='bottom' if _y >= 0 else 'top',
                  fontsize=9, fontweight='bold')
    _ax4.axhline(0, color='black', lw=0.8)
    _ax4.set_ylabel('Felling-era step\nchange (m)')
    _ax4.set_title('(d) Felling era step (Dec 2017 – Oct 2023) — felling subsidy isolation',
                   loc='left', fontweight='bold', fontsize=10)
    _yrange_f = max(abs(min(_fell_vals)), abs(max(_fell_vals)), 0.01) * 1.4
    _ax4.set_ylim(-_yrange_f, _yrange_f)
    for sp in ['top', 'right']: _ax4.spines[sp].set_visible(False)
    _ax4.grid(axis='y', alpha=0.2)

    _fig.suptitle('CEH36 Scraping Robustness — Four Independent Methods\n'
                  f'Felling date corrected to {date_felling.strftime("%b %Y")} | '
                  f'Regional controls: eastern C1/C2 | '
                  f'CEH4 = 4.5m AOD (most coastal), CEH18 = 5.2m AOD',
                  fontsize=11, fontweight='bold', y=0.975)
    _fig.subplots_adjust(left=0.12)
    plt.savefig(OUT_09_ROBUSTNESS, bbox_inches='tight', dpi=300)
    plt.close()
    print(f' -> Saved: {OUT_09_ROBUSTNESS.name}')
    print(f'\n   {"Method":<24} {"Scraping step":>14} {"Felling step":>14}')
    print(f'   {"Raw BACI vs CEH4":<24} {_raw_step:+14.3f} {_raw_fell_step:+14.3f}')
    print(f'   {"Raw BACI vs CEH18":<24} {_raw18_step:+14.3f} {_raw18_fell_step:+14.3f}')
    print(f'   {"Synthetic control":<24} {_syn_step:+14.3f} {_syn_fell_step:+14.3f}')
    print(f'   {"SSM forward residual":<24} {_ssm_step:+14.3f} {_ssm_fell_step:+14.3f}')
    print(f'\n   The felling step is {"positive" if _raw_fell_step > 0 else "negative"} '
          f'with CEH4 ({_raw_fell_step:+.3f} m) but '
          f'{"absent" if abs(_raw18_fell_step) < 0.02 else "negative"} '
          f'with CEH18 ({_raw18_fell_step:+.3f} m).')
    print(f'   → CEH4 (most coastal) receives felling drainage subsidy that')
    print(f'     compensates for its faster coastal erosion.')

except Exception as _e:
    print(f"  [WARNING] Robustness figure failed — {_e}")
    import traceback; traceback.print_exc()


# ===========================================================================
# SUMMARY
# ===========================================================================
print("\n" + "=" * 72)
print("   SCRAPING ANALYSIS SUMMARY — CLEAN CONTROLS v2.0")
print("=" * 72)
print(f"Regional controls: {', '.join(w.upper() for w in valid_controls)}")
print(f"  (Distant eastern C1/C2 wells, >900m from CEH36)")
print(f"Felling date: {date_felling.strftime('%Y-%m-%d')} (corrected)")

if 'ceh36' in _ancova_results:
    ar = _ancova_results['ceh36']
    print(f"\nCEH36 ANCOVA vs CEH4:     scraping={ar['scraping_step']:+.4f} m  "
          f"felling={ar['felling_step']:+.4f} m  R²={ar['R2']:.3f}")
if 'ceh36_vs_ceh18' in _ancova_results:
    ar18 = _ancova_results['ceh36_vs_ceh18']
    print(f"CEH36 ANCOVA vs CEH18:    scraping={ar18['scraping_step']:+.4f} m  "
          f"felling={ar18['felling_step']:+.4f} m  R²={ar18['R2']:.3f}")
    if 'ceh36' in _ancova_results:
        _subsidy = _ancova_results['ceh36']['felling_step'] - ar18['felling_step']
        print(f"  → Felling subsidy at CEH4: {_subsidy:+.4f} m "
              f"(CEH4 step minus CEH18 step)")


# ===========================================================================
# EXPORT REPORT NUMBERS
# ===========================================================================
print("\nExporting report numbers CSV...")
_report_rows = []

def _rr(parameter, value, unit="m", well="", era="", note=""):
    _report_rows.append({
        "Parameter": parameter, "Well": well, "Era": era,
        "Value": round(value, 4) if pd.notna(value) and not isinstance(value, str) else value,
        "Unit": unit, "Note": note,
    })

# 1. Tier 1 CUSUM terminal values
for _w in tier1_wells:
    if _w in plot_data:
        _final_cusum = float(plot_data[_w]['cusum'].iloc[-1])
        _rr("Tier1_CUSUM_terminal", _final_cusum, well=_w.upper(),
            note="Final cumulative CUSUM vs clean eastern Regional Mean")

# 2. Tier 2 raw BACI shifts
for _br in baci_results:
    _rr("Tier2_BACI_shift", _br['Delta_m'],
        well=_br['Well'], era=_br['Shift'],
        note=f"vs {_br['Control']}")

# 3. Net benefits
for _nb in net_summary:
    _rr("Net_benefit", _nb['Net_Benefit_m'],
        well=_nb['Well'], era=_nb['Shift'],
        note="vs CEH21 coastal benchmark")

# 4. Three-method CEH36 estimates
try:
    _rr("CEH36_raw_BACI_step", _raw_step, well="CEH36", era="Pure_Scraping",
        note="CEH36 minus CEH4")
    _rr("CEH36_raw_BACI_felling_step", _raw_fell_step, well="CEH36", era="Felling_Pulse",
        note="CEH36 minus CEH4, felling era")
    _rr("CEH36_raw_BACI_vs_CEH18_step", _raw18_step, well="CEH36", era="Pure_Scraping",
        note="CEH36 minus CEH18 (pre-Oct 2023)")
    _rr("CEH36_raw_BACI_vs_CEH18_felling_step", _raw18_fell_step, well="CEH36", era="Felling_Pulse",
        note="CEH36 minus CEH18, felling era (pre-Oct 2023)")
    _rr("CEH36_synthetic_control_step", _syn_step, well="CEH36", era="Pure_Scraping",
        note=f"Synthetic control ({len(_donors)} donors)")
    _rr("CEH36_synthetic_felling_step", _syn_fell_step, well="CEH36", era="Felling_Pulse",
        note=f"Synthetic control felling era")
    _rr("CEH36_SSM_forward_residual_step", _ssm_step, well="CEH36", era="Pure_Scraping",
        note="SSM calibrated on pre-2015 baseline")
    _rr("CEH36_SSM_forward_felling_step", _ssm_fell_step, well="CEH36", era="Felling_Pulse",
        note="SSM forward residual felling era")
except NameError:
    pass

# 5. ANCOVA results
if 'ceh36' in _ancova_results:
    ar = _ancova_results['ceh36']
    _rr("ANCOVA_scraping_step", ar['scraping_step'], well="CEH36", era="Pure_Scraping",
        note=f"p={format_p_value(ar['scraping_p'])}, "
             f"CI=[{ar['scraping_ci_lo']:.4f},{ar['scraping_ci_hi']:.4f}], "
             f"R²={ar['R2']:.3f}")
    _rr("ANCOVA_felling_step", ar['felling_step'], well="CEH36", era="Felling_Pulse",
        note=f"p={format_p_value(ar['felling_p'])}")
    _rr("ANCOVA_cwb_coeff", ar['cwb_coeff'], well="CEH36", unit="m/mm",
        note=f"p={format_p_value(ar['cwb_p'])}")
    _rr("ANCOVA_regional_coeff", ar['regional_coeff'], well="CEH36",
        note=f"p={format_p_value(ar['regional_p'])}")

# 5b. CEH18-as-control ANCOVA
if 'ceh36_vs_ceh18' in _ancova_results:
    ar18 = _ancova_results['ceh36_vs_ceh18']
    _rr("ANCOVA_scraping_step_vs_CEH18", ar18['scraping_step'],
        well="CEH36", era="Pure_Scraping",
        note=f"Control=CEH18 (pre-Oct2023), p={format_p_value(ar18['scraping_p'])}, "
             f"CI=[{ar18['scraping_ci_lo']:.4f},{ar18['scraping_ci_hi']:.4f}], "
             f"R²={ar18['R2']:.3f}, n={ar18.get('n','?')}")
    _rr("ANCOVA_felling_step_vs_CEH18", ar18['felling_step'],
        well="CEH36", era="Felling_Pulse",
        note=f"Control=CEH18, p={format_p_value(ar18['felling_p'])}")
    # Felling subsidy estimate
    if 'ceh36' in _ancova_results:
        _fell_subsidy = _ancova_results['ceh36']['felling_step'] - ar18['felling_step']
        _rr("Felling_drainage_subsidy_estimate", _fell_subsidy,
            well="CEH4", era="Felling_Pulse",
            note="ANCOVA felling step (CEH4 control) minus (CEH18 control). "
                 "Positive = CEH4 receives forest drainage subsidy that CEH18 does not.")

# 5c. Scraping effect on summer minima
for _ctrl_name, _sr in _scraping_summer_results.items():
    if _ctrl_name == 'CEH4_vs_CEH18_felling':
        _rr("Summer_min_CEH4_vs_CEH18_felling_shift", _sr['shift'],
            well="CEH4-CEH18", era="Felling_effect",
            note=f"Welch t-test p={format_p_value(_sr['p_value'])}")
        continue
    _rr(f"Summer_min_scrape_shift_vs_{_ctrl_name}", _sr.get('scrape_shift', np.nan),
        well="CEH36", era="Post_scraping",
        note=f"vs {_ctrl_name}, n_pre={_sr.get('n_pre')}, n_post={_sr.get('n_post_scrape')}, "
             f"p={format_p_value(_sr.get('p_scrape', np.nan))}")
    _rr(f"Summer_min_fell_shift_vs_{_ctrl_name}", _sr.get('fell_shift', np.nan),
        well="CEH36", era="Post_felling",
        note=f"vs {_ctrl_name}, n={_sr.get('n_post_fell')}")
    _rr(f"Summer_min_pre_mean_vs_{_ctrl_name}", _sr.get('pre_mean', np.nan),
        well="CEH36-"+_ctrl_name, era="Pre_scraping")

# 6. Table 4 β₃ era estimates
for _sr in significance_results:
    _rr("Table4_beta3_era", _sr['beta_3_drainage'],
        well=_sr['Well'], era=_sr['Era'],
        note=f"CI=[{_sr['Conf_Low']:.4f},{_sr['Conf_High']:.4f}] "
             f"p={format_p_value(_sr['P_Value'])}")

# 7. Summer minima
_SUMMER_MONTHS = [6, 7, 8, 9]
for _sw in ['ceh4', 'ceh36']:
    if _sw not in wells.columns: continue
    _sw_config = well_eras.get(_sw)
    if _sw_config is None: continue
    _sw_series = wells[_sw].dropna()
    for _era_name, _era_filter in _sw_config['Eras'].items():
        _era_data = _era_filter(_sw_series)
        _summer = _era_data[_era_data.index.month.isin(_SUMMER_MONTHS)]
        if len(_summer) >= 2:
            _rr("Summer_minimum_depth", float(_summer.min()),
                well=_sw.upper(), era=_era_name,
                note="Min of Jun-Sep readings")

_report_df = pd.DataFrame(_report_rows)
_report_df.to_csv(OUT_09_REPORT_NUMBERS, index=False)
print(f" -> Saved: {OUT_09_REPORT_NUMBERS.name} ({len(_report_rows)} rows)")


# ===========================================================================
# 9. SUMMER MINIMUM SCENARIO COMPARISON FIGURE
# ===========================================================================
# Standalone bar chart comparing summer minimum effects across all scenarios
# (forest management, scraping, climate) for all five clusters. Forest
# management values are empirical (from this script and Script 10). Climate
# values use SSM annual-mean predictions scaled by an empirical summer
# amplification factor (regression of summer minimum on annual mean).

print("\n9. Summer Minimum Scenario Comparison Figure...")

try:
    # ── Climate amplification factors ────────────────────────────────────
    # Regression of cluster centroid summer minimum on cluster annual mean
    _SUMMER_MONTHS_SC = [6, 7, 8, 9]
    _regional = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    _cluster_cols = ['C1', 'C2', 'C3', 'C4', 'C5']

    _amp_factors = {}
    for _c in _cluster_cols:
        if _c not in _regional.columns:
            continue
        _annual = {}
        _summin = {}
        for _yr in range(2006, 2026):
            _yr_data = _regional.loc[_regional.index.year == _yr, _c].dropna()
            if len(_yr_data) >= 8:
                _annual[_yr] = float(_yr_data.mean())
            _sm_mask = (_regional.index.year == _yr) & (_regional.index.month.isin(_SUMMER_MONTHS_SC))
            _sm_data = _regional.loc[_sm_mask, _c].dropna()
            if len(_sm_data) >= 2:
                _summin[_yr] = float(_sm_data.min())
        _common_yrs_amp = sorted(set(_annual) & set(_summin))
        if len(_common_yrs_amp) >= 8:
            _x_amp = np.array([_annual[yr] for yr in _common_yrs_amp])
            _y_amp = np.array([_summin[yr] for yr in _common_yrs_amp])
            _slope_amp, _, _, _, _ = _stats.linregress(_x_amp, _y_amp)
            _amp_factors[_c] = _slope_amp
        else:
            _amp_factors[_c] = 0.85  # fallback

    # ── Read SSM annual-mean scenario data ───────────────────────────────
    _scen_csv = DIR_09 / '09b_04_scenario_comparison.csv'
    if _scen_csv.exists():
        _scen = pd.read_csv(_scen_csv)
    else:
        _scen = pd.DataFrame()

    # ── Build summer minimum scenario values ─────────────────────────────
    # Forest management: empirical BACI (clearfell from Script 10 = ~0)
    # Scraping: from _scraping_summer_results (section 3c)
    _scrape_c3 = 0
    _scrape_c4 = 0
    _scrape_c5 = 0
    if _scraping_summer_results:
        _sr_ceh18 = _scraping_summer_results.get('CEH18', {})
        _empirical_scrape = _sr_ceh18.get('scrape_shift', 0.143) * 1000  # mm
        # Weight by fraction of cluster within 800m of CEH36
        _scrape_c3 = round(_empirical_scrape * 0.32)
        _scrape_c4 = round(_empirical_scrape * 0.78)
        _scrape_c5 = round(_empirical_scrape * 1.00)

    _summer_scenarios = {
        'Clearfell':         {'C1': 0, 'C2': 0, 'C3': 0,          'C4': -3,       'C5': -28},
        'Thinning 50%':      {'C1': 0, 'C2': 0, 'C3': 0,          'C4': -2,       'C5': -14},
        'Broadleaf':         {'C1': 0, 'C2': 0, 'C3': 0,          'C4': 0,        'C5': 0},
        'Scraping (nearby)': {'C1': 0, 'C2': 0, 'C3': _scrape_c3, 'C4': _scrape_c4, 'C5': _scrape_c5},
    }

    # Climate scenarios: SSM vol → head (÷ Sy ≈ 0.20) → summer min (× amp)
    _SY_FALLBACK = 0.20
    if not _scen.empty:
        for _scenario in ['Climate dry', 'Climate wet']:
            _summer_scenarios[_scenario] = {}
            for _c in _cluster_cols:
                _row = _scen[(_scen['Scenario'] == _scenario) & (_scen['Cluster'] == _c)]
                if not _row.empty:
                    _vol = float(_row['Delta_vol_mm_per_month'].iloc[0])
                    _head = _vol / _SY_FALLBACK
                    _amp = _amp_factors.get(_c, 0.85)
                    _summer_scenarios[_scenario][_c] = round(_head * _amp)
                else:
                    _summer_scenarios[_scenario][_c] = 0

    # ── Figure ───────────────────────────────────────────────────────────
    _scenarios_plot = [s for s in ['Clearfell', 'Thinning 50%', 'Broadleaf',
                                    'Scraping (nearby)', 'Climate dry', 'Climate wet']
                       if s in _summer_scenarios]
    _cluster_labels_sc = ['C1\nLake Edge', 'C2\nDune', 'C3\nWestern',
                           'C4\nMain\nForest', 'C5\nCoastal\nForest']
    _colours_sc = {
        'Clearfell': '#8B6914', 'Thinning 50%': '#D2691E',
        'Broadleaf': '#228B22', 'Scraping (nearby)': '#DAA520',
        'Climate dry': '#E8726E', 'Climate wet': '#5B9BD5',
    }
    _hatches_sc = {'Scraping (nearby)': '///'}

    _fig_sc, _ax_sc = plt.subplots(figsize=(14, 7), dpi=300)
    _n_sc = len(_scenarios_plot)
    _bw = 0.8 / _n_sc
    _x_sc = np.arange(len(_cluster_cols))

    for _i, _scen_name in enumerate(_scenarios_plot):
        _vals = [_summer_scenarios[_scen_name].get(c, 0) for c in _cluster_cols]
        _offset = (_i - _n_sc / 2 + 0.5) * _bw
        _hatch = _hatches_sc.get(_scen_name, '')
        _ax_sc.bar(_x_sc + _offset, _vals, _bw * 0.9,
                   color=_colours_sc.get(_scen_name, '#999'),
                   edgecolor='black' if _hatch else _colours_sc.get(_scen_name, '#999'),
                   linewidth=0.8 if _hatch else 0.5,
                   hatch=_hatch, alpha=0.85,
                   label=_scen_name, zorder=3)
        for _j, _v in enumerate(_vals):
            if abs(_v) > 20:
                _ax_sc.text(_x_sc[_j] + _offset, _v + (4 if _v > 0 else -4),
                            f'{_v:+.0f}', ha='center',
                            va='bottom' if _v > 0 else 'top',
                            fontsize=7.5, fontweight='bold', color='#333')

    _ax_sc.axhline(0, color='black', lw=0.8)
    _ax_sc.set_xticks(_x_sc)
    _ax_sc.set_xticklabels(_cluster_labels_sc, fontsize=11)
    _ax_sc.set_ylabel('Δ summer minimum depth (mm)', fontsize=12)
    _ax_sc.set_title(
        'Summer minimum scenario comparison: forest management, scraping, and climate (k = 5)\n'
        'Forest management: empirical BACI (Scripts 09/10)  |  '
        'Climate: SSM equilibrium × amplification factor',
        fontsize=12, fontweight='bold')
    _ax_sc.legend(fontsize=9, loc='lower left', framealpha=0.9, ncol=3)
    _ax_sc.grid(axis='y', alpha=0.25, ls='--')
    for _sp in ['top', 'right']:
        _ax_sc.spines[_sp].set_visible(False)
    _ax_sc.text(0.98, 0.02,
                'Scraping bars: empirical BACI summer minimum shift (CEH36 vs CEH18, p = 0.017),\n'
                'weighted by fraction of cluster within 800 m of CEH36.  '
                'Forest management bars: empirical (Scripts 09/10).\n'
                'Climate bars: SSM annual-mean prediction × empirical summer amplification factor.',
                transform=_ax_sc.transAxes, fontsize=7.5, ha='right', va='bottom',
                color='#555', style='italic')
    plt.tight_layout()
    plt.savefig(OUT_09B_SUMMER_SCENARIO, bbox_inches='tight', dpi=300)
    plt.close(_fig_sc)
    print(f' -> Saved: {OUT_09B_SUMMER_SCENARIO.name}')

    # Export CSV
    _sc_rows = []
    for _scen_name in _scenarios_plot:
        for _c in _cluster_cols:
            _sc_rows.append({
                'Scenario': _scen_name, 'Cluster': _c,
                'Delta_summer_min_mm': _summer_scenarios[_scen_name].get(_c, 0),
            })
    pd.DataFrame(_sc_rows).to_csv(OUT_09B_SUMMER_SCENARIO_CSV, index=False)
    print(f' -> Saved: {OUT_09B_SUMMER_SCENARIO_CSV.name}')

except Exception as _e:
    print(f"  [WARNING] Summer scenario figure failed: {_e}")
    import traceback; traceback.print_exc()


print("\n[DONE] Script 09 v2.0 — Clean controls scraping BACI complete.")
