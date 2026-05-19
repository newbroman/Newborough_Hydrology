r"""
====================================================================================
10h — SYNTHETIC-EXTENSION BACI: FE WELLS WITH DONOR-REGRESSION HINDCAST
====================================================================================
Purpose
-------
Robustness check for the Script 10a clearfell ANCOVA-BACI.  The primary 10a
analysis uses WMC3 as the sole impact well because it spans all three eras
(pre-scraping, post-scraping, post-felling).  The FE wells (FE1–FE4) sit
inside or at the immediate edge of the clearfell compartment but have no
pre-scraping data (FE1/FE2 start July 2015; FE3/FE4 start 2017).

This script extends FE1 and FE2 backwards using OLS donor regression
calibrated on the pre-clearfell overlap window.  Donors are Forest Control
wells (CEH34, CEH2, CEH33) — unaffected by clearfell and highly correlated
(r > 0.99) with the FE wells during the calibration window.  The synthetic
records are spliced with the actual FE observations to create a stable-
composition impact centroid spanning all three eras.

Three impact centroid variants are tested:
  A. WMC3 + FE1_synth + FE2_synth   (3-well centroid)
  B. WMC3 + FE2_synth               (2-well, excludes FE1 — see caveat)
  C. WMC3 alone                      (baseline, reproduces 10a Impact result)

Each is run against the same three control definitions (Forest, Climate,
Combined) using the identical ANCOVA framework as 10a.

Caveats
-------
- FE1 is technically outside the clearfell boundary (~20 m into standing
  forest).  It may represent an edge-of-impact response rather than a true
  within-compartment effect.  Variant B excludes it for this reason.
- The donor regression is fitted on only 29 months (July 2015 – November 2017).
  This is short but the R² > 0.99 indicates the relationship is very tight.
- The synthetic extension assumes the donor relationship was stationary before
  July 2015.  This is reasonable: all wells were under the same forest canopy
  before scraping, and the donors are nearby Forest Control wells under the
  same canopy conditions.
- FE well locations are not in the reference-network master data.  Locations
  are taken from Well_info.csv for scraping distance calculations.

Outputs
-------
CSV:
  10h_01_synthetic_calibration.csv      — regression diagnostics per FE well
  10h_02_ancova_comparison_table.csv    — ANCOVA results: variants × controls
  10h_03_ancova_full_coefficients.csv   — full model coefficients
  10h_04_baci_timeseries.csv            — BACI displacement time-series
  10h_report_numbers.csv                — all citable values

Figures:
  10h_05_donor_regression_validation.png — calibration scatter + hindcast
  10h_06_baci_timeseries_varA.png       — 3-panel BACI (WMC3+FE1+FE2)
  10h_07_baci_timeseries_varB.png       — 3-panel BACI (WMC3+FE2)
  10h_08_baci_timeseries_varC.png       — 3-panel BACI (WMC3 alone, baseline)

References
----------
Hollingham (2026), §4.6.  Part of the Script 10 clearfell analysis suite.
====================================================================================
"""

__version__ = "1.2.0"  # Hollingham (2026) — 2026-05-16
# 1.2.0 — Adopt CEH34 hindcast via apply_ceh34_hindcast().  Companion to
#         PRE_FELL_START = 2010-07-01 in clearfell_common v1.2.0.
# 1.1.0 — Apply PRE_FELL_START record-length-balance cutoff in
#         build_ancova_frame() — matches 10a v1.1.0.  Synthetic
#         extension of FE1/FE2 (donor regression) is unchanged; the
#         cutoff applies to the ANCOVA pooled inference only.
# 1.0.0 — Initial.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.clearfell_common import (
    load_clearfell_data,
    apply_ceh34_hindcast,
    IMPACT_WELLS, EDGE_WELLS,
    FOREST_CONTROL_WELLS, COASTAL_CONTROL_WELLS, CLIMATE_CONTROL_WELLS,
    INTERVENTION_DATE, SCRAPING_DATE, SCRAPING_DATE_2,
    PRE_FELL_START,
    SCRAPING_DECAY_LAMBDA,
    compute_baci_displacement, compute_cwb,
    build_scraping_covariate_centroid,
    TIER_COLOURS, ReportNumbers, print_network_summary,
    CEH36_EASTING, CEH36_NORTHING,
)
from utils.paths import make_all_dirs, DIR_10
from utils.config import DRAINAGE_DATUM
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
OUT_CALIBRATION   = DIR_10 / "10h_01_synthetic_calibration.csv"
OUT_COMPARISON    = DIR_10 / "10h_02_ancova_comparison_table.csv"
OUT_FULL_COEFFS   = DIR_10 / "10h_03_ancova_full_coefficients.csv"
OUT_TIMESERIES    = DIR_10 / "10h_04_baci_timeseries.csv"
OUT_REPORT        = DIR_10 / "10h_report_numbers.csv"
OUT_FIG_DONORS    = DIR_10 / "10h_05_donor_regression_validation.png"
OUT_FIG_VAR_A     = DIR_10 / "10h_06_baci_timeseries_varA.png"
OUT_FIG_VAR_B     = DIR_10 / "10h_07_baci_timeseries_varB.png"
OUT_FIG_VAR_C     = DIR_10 / "10h_08_baci_timeseries_varC.png"
OUT_FIG_CUSUM     = DIR_10 / "10h_09_cusum_varB.png"
OUT_FIG_SENSITIVITY = DIR_10 / "10h_10_climate_sensitivity_varB.png"

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

CB_FOREST   = '#4DAC26'
CB_CLIMATE  = '#4575B4'
CB_COMBINED = '#7570B3'
CONTROL_COLOURS = {
    'Forest':   CB_FOREST,
    'Climate':  CB_CLIMATE,
    'Combined': CB_COMBINED,
}

# ============================================================================
# FE WELL CONFIGURATION
# ============================================================================
# FE well locations from Well_info.csv (not in reference-network master data)
FE_LOCATIONS = {
    'fe1': {'easting': 241338.0, 'northing': 363744.0},
    'fe2': {'easting': 241135.0, 'northing': 363595.0},
}

# Donor wells: Forest Control wells unaffected by clearfell
DONOR_WELLS = ['ceh34', 'ceh2', 'ceh33']

# Wells to extend synthetically
FE_SYNTH_WELLS = ['fe1', 'fe2']


# ============================================================================
# UTILITY: OLS WITH SE, P, R², AIC  (identical to 10a)
# ============================================================================

def ols_fit(y, X):
    """OLS fit returning coefficients, standard errors, p-values, R², AIC."""
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
    if pd.isna(p):
        return "NA"
    return "<0.001" if p < 0.001 else f"{p:.4f}"


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
print("=" * 72)
print("SCRIPT 10h — SYNTHETIC-EXTENSION BACI (FE WELLS)")
print("=" * 72)

print("\n1. Loading data...")
wells, _wells_prov, climate, master, well_locations, valid_tiers = load_clearfell_data()
wells = apply_ceh34_hindcast(wells)
print_network_summary(valid_tiers)

# Add FE well locations to the well_locations dict
for fe_name, fe_loc in FE_LOCATIONS.items():
    well_locations[fe_name] = fe_loc

# ============================================================================
# DONOR REGRESSION: EXTEND FE1/FE2 BACKWARDS
# ============================================================================
print("\n2. Building synthetic FE well extensions...")

donor_data = {d: wells[d].dropna() for d in DONOR_WELLS}
calibration_rows = []
synthetic_wells = {}

for fe_name in FE_SYNTH_WELLS:
    fe = wells[fe_name].dropna()

    # Calibration window: pre-clearfell overlap
    cal_idx = fe.index[fe.index < INTERVENTION_DATE]
    common_cal = cal_idx
    for d in DONOR_WELLS:
        common_cal = common_cal.intersection(donor_data[d].index)

    n_cal = len(common_cal)
    if n_cal < 15:
        print(f"  WARNING: {fe_name.upper()} has only {n_cal} calibration months — skipping")
        continue

    # Build regression: FE = b0 + b1*CEH34 + b2*CEH2 + b3*CEH33
    X_cal = np.column_stack([np.ones(n_cal)] +
                            [donor_data[d].loc[common_cal].values for d in DONOR_WELLS])
    y_cal = fe.loc[common_cal].values
    b, _, _, _ = np.linalg.lstsq(X_cal, y_cal, rcond=None)

    y_pred_cal = X_cal @ b
    residuals = y_cal - y_pred_cal
    r2 = 1 - np.sum(residuals**2) / np.sum((y_cal - y_cal.mean())**2)
    rmse = np.sqrt(np.mean(residuals**2))

    # Hindcast: extend back to earliest common donor coverage
    all_donor_dates = donor_data[DONOR_WELLS[0]].index
    for d in DONOR_WELLS[1:]:
        all_donor_dates = all_donor_dates.intersection(donor_data[d].index)
    hind_dates = all_donor_dates[all_donor_dates < fe.index[0]]

    X_hind = np.column_stack([np.ones(len(hind_dates))] +
                             [donor_data[d].loc[hind_dates].values for d in DONOR_WELLS])
    y_hind = X_hind @ b

    # Splice: synthetic hindcast + actual observations
    hindcast = pd.Series(y_hind, index=hind_dates, name=fe_name)
    combined = pd.concat([hindcast, fe]).sort_index()
    combined = combined[~combined.index.duplicated(keep='last')]
    synthetic_wells[fe_name] = combined

    # Post-clearfell divergence (validation)
    post_dates = fe.index[fe.index >= INTERVENTION_DATE]
    common_post = post_dates
    for d in DONOR_WELLS:
        common_post = common_post.intersection(donor_data[d].index)

    X_post = np.column_stack([np.ones(len(common_post))] +
                             [donor_data[d].loc[common_post].values for d in DONOR_WELLS])
    y_actual_post = fe.loc[common_post].values
    y_counterfactual = X_post @ b
    divergence = y_actual_post - y_counterfactual

    t_stat = divergence.mean() / (divergence.std() / np.sqrt(len(divergence)))
    p_div = 2 * (1 - sp_stats.t.cdf(abs(t_stat), df=len(divergence) - 1))

    pre_scr_hind = hind_dates[hind_dates < SCRAPING_DATE]

    print(f"\n  {fe_name.upper()}:")
    print(f"    Donors: {', '.join(d.upper() for d in DONOR_WELLS)}")
    print(f"    Calibration: {common_cal[0].strftime('%Y-%m')} to "
          f"{common_cal[-1].strftime('%Y-%m')} (n={n_cal})")
    print(f"    R² = {r2:.4f}, RMSE = {rmse*1000:.1f} mm")
    print(f"    Hindcast: {hind_dates[0].strftime('%Y-%m')} to "
          f"{hind_dates[-1].strftime('%Y-%m')} ({len(hind_dates)} months)")
    print(f"    Pre-scraping months gained: {len(pre_scr_hind)}")
    print(f"    Post-clearfell divergence: {divergence.mean()*1000:+.1f} mm "
          f"(p={p_div:.4f}, n={len(divergence)})")
    print(f"    Synthetic record: {combined.index[0].strftime('%Y-%m')} to "
          f"{combined.index[-1].strftime('%Y-%m')} ({len(combined)} months)")

    calibration_rows.append({
        'Well': fe_name.upper(),
        'Donors': '+'.join(d.upper() for d in DONOR_WELLS),
        'Cal_start': common_cal[0].strftime('%Y-%m'),
        'Cal_end': common_cal[-1].strftime('%Y-%m'),
        'N_cal': n_cal,
        'R2_cal': round(r2, 6),
        'RMSE_mm': round(rmse * 1000, 1),
        'Hindcast_start': hind_dates[0].strftime('%Y-%m'),
        'Hindcast_months': len(hind_dates),
        'PreScraping_months_gained': len(pre_scr_hind),
        'PostFell_divergence_mm': round(divergence.mean() * 1000, 1),
        'PostFell_divergence_p': round(p_div, 6),
        'PostFell_divergence_n': len(divergence),
        'b_intercept': round(b[0], 6),
        **{f'b_{d}': round(b[i+1], 6) for i, d in enumerate(DONOR_WELLS)},
    })

# Save calibration diagnostics
cal_df = pd.DataFrame(calibration_rows)
cal_df.to_csv(OUT_CALIBRATION, index=False)
print(f"\n -> Saved: {OUT_CALIBRATION.name}")

# ============================================================================
# BUILD SYNTHETIC IMPACT CENTROIDS
# ============================================================================
print("\n3. Building impact centroid variants...")

# Inject synthetic wells into the wells DataFrame
wells_augmented = wells.copy()
for fe_name, synth in synthetic_wells.items():
    wells_augmented[fe_name + '_synth'] = synth

# Define variants
VARIANTS = {
    'A (WMC3+FE1+FE2)': ['wmc3', 'fe1_synth', 'fe2_synth'],
    'B (WMC3+FE2)':      ['wmc3', 'fe2_synth'],
    'C (WMC3 only)':     ['wmc3'],
}

# Check availability
for var_label, var_wells in VARIANTS.items():
    available = [w for w in var_wells if w in wells_augmented.columns]
    missing = [w for w in var_wells if w not in wells_augmented.columns]
    start_dates = []
    for w in available:
        s = wells_augmented[w].dropna()
        start_dates.append(s.index[0])
    earliest = min(start_dates) if start_dates else None
    print(f"  {var_label}: {len(available)} wells, "
          f"earliest={earliest.strftime('%Y-%m') if earliest else 'N/A'}"
          f"{', MISSING: ' + ','.join(missing) if missing else ''}")

# ============================================================================
# CONTROLS
# ============================================================================
CONTROLS = {
    'Forest':   FOREST_CONTROL_WELLS,
    'Climate':  CLIMATE_CONTROL_WELLS,
    'Combined': (FOREST_CONTROL_WELLS + COASTAL_CONTROL_WELLS +
                 CLIMATE_CONTROL_WELLS),
}

# ============================================================================
# ANCOVA FRAMEWORK (reused from 10a with minor adaptations)
# ============================================================================

def build_ancova_frame(wells_df, target_wells, control_wells,
                       wl, lambda_m=SCRAPING_DECAY_LAMBDA):
    """Build ANCOVA design matrix — identical logic to 10a."""
    baci = compute_baci_displacement(wells_df, target_wells, control_wells)
    cwb = compute_cwb(climate)
    common = baci.index.intersection(cwb.index)
    df = pd.DataFrame({
        'baci_disp': baci.loc[common],
        'cwb':       cwb.loc[common],
    }).dropna()

    # ── Record-length-balance cutoff ─────────────────────────────────
    # See clearfell_common.py docstring.  This script extends the impact
    # centroid backwards via donor regression — the cutoff applies AFTER
    # synthetic extension is complete (which happens upstream).  The
    # ANCOVA itself uses only the record-length-balanced window.
    df = df.loc[df.index >= PRE_FELL_START]

    if len(df) < 20:
        return None

    df['cwb_c'] = df['cwb'] - df['cwb'].mean()

    # Scraping covariate (distance-weighted differential)
    target_scrape = build_scraping_covariate_centroid(
        df.index, SCRAPING_DATE, wl, target_wells, lambda_m)
    control_scrape = build_scraping_covariate_centroid(
        df.index, SCRAPING_DATE, wl, control_wells, lambda_m)
    df['D_scrape'] = target_scrape.loc[df.index] - control_scrape.loc[df.index]

    # Re-scraping Oct 2023
    target_scrape2 = build_scraping_covariate_centroid(
        df.index, SCRAPING_DATE_2, wl, target_wells, lambda_m)
    control_scrape2 = build_scraping_covariate_centroid(
        df.index, SCRAPING_DATE_2, wl, control_wells, lambda_m)
    df['D_scrape2'] = target_scrape2.loc[df.index] - control_scrape2.loc[df.index]

    df['D_fell'] = (df.index >= INTERVENTION_DATE).astype(float)
    df['cwb_x_fell'] = df['cwb_c'] * df['D_fell']

    # Easting interaction
    all_wells_in_model = list(set(target_wells + control_wells))
    eastings = [wl[w]['easting'] for w in all_wells_in_model if w in wl]
    easting_range = max(eastings) - min(eastings) if len(eastings) >= 2 else 0

    df['has_easting'] = False
    if easting_range > 200:
        target_eastings = [wl[w]['easting'] for w in target_wells if w in wl]
        control_eastings = [wl[w]['easting'] for w in control_wells if w in wl]
        if target_eastings and control_eastings:
            delta_easting = np.mean(target_eastings) - np.mean(control_eastings)
            t0 = df.index.min()
            months_since = ((df.index - t0).days / 30.4375)
            df['easting_x_time'] = delta_easting * months_since
            df['has_easting'] = True

    return df


def run_ancova(df, include_easting=None, include_scrape2=False):
    """Run ANCOVA — identical to 10a."""
    if include_easting is None:
        include_easting = df['has_easting'].iloc[0] if 'has_easting' in df else False

    cols = ['cwb_c', 'D_scrape', 'D_fell', 'cwb_x_fell']
    col_names = ['intercept', 'cwb', 'scraping', 'clearfell', 'cwb_x_fell']
    if include_easting and 'easting_x_time' in df.columns:
        cols.append('easting_x_time')
        col_names.append('easting_x_time')

    X = np.column_stack([np.ones(len(df))] + [df[c].values for c in cols])
    y = df['baci_disp'].values

    fit = ols_fit(y, X)
    fit['col_names'] = col_names

    fell_idx = col_names.index('clearfell')
    ci_lo = fit['b'][fell_idx] - 1.96 * fit['se'][fell_idx]
    ci_hi = fit['b'][fell_idx] + 1.96 * fit['se'][fell_idx]
    fit['clearfell_step'] = fit['b'][fell_idx]
    fit['clearfell_p'] = fit['p'][fell_idx]
    fit['clearfell_ci'] = (ci_lo, ci_hi)

    scr_idx = col_names.index('scraping')
    fit['scraping_step'] = fit['b'][scr_idx]
    fit['scraping_p'] = fit['p'][scr_idx]

    if include_scrape2 and 'D_scrape2' in df.columns:
        cols2 = cols + ['D_scrape2']
        col_names2 = col_names + ['scraping_2023']
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
# RUN ANCOVA FOR ALL VARIANTS × CONTROLS
# ============================================================================
print("\n4. Running ANCOVA for all variants × controls...")

# We need augmented well_locations that include synthetic FE names
wl_aug = dict(well_locations)
for fe_name in FE_SYNTH_WELLS:
    if fe_name in FE_LOCATIONS:
        wl_aug[fe_name + '_synth'] = FE_LOCATIONS[fe_name]

all_results = {}      # (variant, control) -> fit
all_frames = {}       # (variant, control) -> df

comparison_rows = []
coeff_rows = []
ts_frames = []

for var_label, var_wells in VARIANTS.items():
    available = [w for w in var_wells if w in wells_augmented.columns]
    if not available:
        print(f"  {var_label}: no wells available — skipping")
        continue

    for ctrl_label, ctrl_wells in CONTROLS.items():
        df = build_ancova_frame(wells_augmented, available, ctrl_wells,
                                wl_aug)
        if df is None:
            print(f"   {ctrl_label:10s} × {var_label}: insufficient data")
            continue

        fit = run_ancova(df, include_scrape2=True)
        key = (var_label, ctrl_label)
        all_results[key] = fit
        all_frames[key] = df

        fell_mm = fit['clearfell_step'] * 1000
        ci_mm = (fit['clearfell_ci'][0] * 1000, fit['clearfell_ci'][1] * 1000)

        print(f"   {ctrl_label:10s} × {var_label}: "
              f"step = {fell_mm:+.0f} mm  "
              f"CI = [{ci_mm[0]:+.0f}, {ci_mm[1]:+.0f}]  "
              f"p = {format_p(fit['clearfell_p'])}  "
              f"R² = {fit['r2']:.3f}  n = {fit['n']}")

        comparison_rows.append({
            'Variant': var_label,
            'Control': ctrl_label,
            'Clearfell_step_m': round(fit['clearfell_step'], 6),
            'Clearfell_CI_lo_m': round(fit['clearfell_ci'][0], 6),
            'Clearfell_CI_hi_m': round(fit['clearfell_ci'][1], 6),
            'Clearfell_p': fit['clearfell_p'],
            'Clearfell_sig': p_to_sig(fit['clearfell_p']),
            'Scraping_step_m': round(fit['scraping_step'], 6),
            'Scraping_p': fit['scraping_p'],
            'R2': round(fit['r2'], 4),
            'N': fit['n'],
            'Oct2023_step_m': round(fit['m3_scrape2_coef'], 6)
                if not np.isnan(fit['m3_scrape2_coef']) else np.nan,
            'Oct2023_p': fit['m3_scrape2_p'],
            'dAIC_M3_M2': round(fit['daic'], 2) if not np.isnan(fit['daic']) else np.nan,
        })

        # Full coefficients
        for i, cname in enumerate(fit['col_names']):
            coeff_rows.append({
                'Variant': var_label,
                'Control': ctrl_label,
                'Coefficient': cname,
                'Value': round(fit['b'][i], 6),
                'SE': round(fit['se'][i], 6),
                'p': fit['p'][i],
                'Sig': p_to_sig(fit['p'][i]),
            })

        # Climate-corrected timeseries
        cwb_idx = fit['col_names'].index('cwb')
        cwb_fell_idx = fit['col_names'].index('cwb_x_fell')
        corrected = (df['baci_disp']
                     - fit['b'][cwb_idx] * df['cwb_c']
                     - fit['b'][cwb_fell_idx] * df['cwb_c'] * df['D_fell'])
        if 'easting_x_time' in fit['col_names']:
            east_idx = fit['col_names'].index('easting_x_time')
            corrected = corrected - fit['b'][east_idx] * df['easting_x_time']

        ts_frames.append(pd.DataFrame({
            'Date': df.index,
            'Variant': var_label,
            'Control': ctrl_label,
            'BACI_raw': df['baci_disp'].values,
            'BACI_corrected': corrected.values,
            'CWB': df['cwb'].values,
        }))

# ============================================================================
# SAVE CSVs
# ============================================================================
print("\n5. Saving CSV outputs...")

comp_df = pd.DataFrame(comparison_rows)

# Net clearfell effect: Forest step minus Climate background step
# The Climate control step represents the background climate shift at the
# felling date (unrelated to clearfell). Subtracting it from the Forest
# and Combined steps isolates the clearfell-attributable component.
for var_label in comp_df['Variant'].unique():
    mask_var = comp_df['Variant'] == var_label
    climate_step = comp_df.loc[mask_var & (comp_df['Control'] == 'Climate'),
                               'Clearfell_step_m']
    if len(climate_step) == 1:
        bg = climate_step.iloc[0]
        comp_df.loc[mask_var, 'Climate_background_m'] = round(bg, 6)
        comp_df.loc[mask_var, 'Net_clearfell_m'] = (
            comp_df.loc[mask_var, 'Clearfell_step_m'] - bg).round(6)
    else:
        comp_df.loc[mask_var, 'Climate_background_m'] = np.nan
        comp_df.loc[mask_var, 'Net_clearfell_m'] = np.nan

comp_df.to_csv(OUT_COMPARISON, index=False)
print(f" -> Saved: {OUT_COMPARISON.name} ({len(comp_df)} rows)")

coeff_df = pd.DataFrame(coeff_rows)
coeff_df.to_csv(OUT_FULL_COEFFS, index=False)
print(f" -> Saved: {OUT_FULL_COEFFS.name} ({len(coeff_df)} rows)")

ts_df = pd.concat(ts_frames, ignore_index=True)
ts_df.to_csv(OUT_TIMESERIES, index=False)
print(f" -> Saved: {OUT_TIMESERIES.name} ({len(ts_df)} rows)")

# ============================================================================
# FIGURE: DONOR REGRESSION VALIDATION
# ============================================================================
print("\n6. Generating donor regression validation figure...")

n_fe = len(synthetic_wells)
fig, axes = plt.subplots(n_fe, 3, figsize=(16, 4 * n_fe), dpi=300)
if n_fe == 1:
    axes = axes.reshape(1, -1)

for row, fe_name in enumerate(synthetic_wells):
    fe_actual = wells[fe_name].dropna()
    synth = synthetic_wells[fe_name]

    # Get the calibration info
    cal_info = [r for r in calibration_rows if r['Well'] == fe_name.upper()][0]
    cal_start = pd.Timestamp(cal_info['Cal_start'] + '-01')
    cal_end = pd.Timestamp(cal_info['Cal_end'] + '-01')

    # Panel 1: Full timeseries (actual + synthetic)
    ax = axes[row, 0]
    synth_only = synth[synth.index < fe_actual.index[0]]
    ax.plot(synth_only.index, synth_only.values * 1000,
            color='#E66101', lw=1.5, ls='--', label='Synthetic (hindcast)')
    ax.plot(fe_actual.index, fe_actual.values * 1000,
            color='#1B7837', lw=1.2, label='Actual observations')
    ax.axvline(SCRAPING_DATE, color='grey', ls='--', lw=0.8)
    ax.axvline(INTERVENTION_DATE, color='k', ls='-', lw=1)
    ax.set_ylabel('Depth (mm)')
    ax.set_title(f'{fe_name.upper()} — synthetic + actual', fontsize=11)
    ax.legend(fontsize=8, frameon=False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Panel 2: Calibration scatter
    ax = axes[row, 1]
    cal_mask = (fe_actual.index >= cal_start) & (fe_actual.index <= cal_end)
    fe_cal = fe_actual[cal_mask]

    # Recompute predicted for calibration window
    d_vals = {}
    for d in DONOR_WELLS:
        d_vals[d] = wells[d].loc[fe_cal.index]
    X_cal = np.column_stack([np.ones(len(fe_cal))] +
                            [d_vals[d].values for d in DONOR_WELLS])
    b_vec = np.array([cal_info['b_intercept']] +
                     [cal_info[f'b_{d}'] for d in DONOR_WELLS])
    y_pred = X_cal @ b_vec

    ax.scatter(y_pred * 1000, fe_cal.values * 1000,
               s=30, alpha=0.7, color='#1B7837', edgecolors='white', lw=0.5)
    lims = [min(y_pred.min(), fe_cal.min()) * 1000 - 50,
            max(y_pred.max(), fe_cal.max()) * 1000 + 50]
    ax.plot(lims, lims, 'k--', lw=0.8, alpha=0.5)
    ax.set_xlabel('Predicted (mm)')
    ax.set_ylabel('Observed (mm)')
    ax.set_title(f'Calibration: R²={cal_info["R2_cal"]:.4f}, '
                 f'RMSE={cal_info["RMSE_mm"]:.0f} mm', fontsize=10)

    # Panel 3: Post-clearfell divergence
    ax = axes[row, 2]
    post_mask = fe_actual.index >= INTERVENTION_DATE
    fe_post = fe_actual[post_mask]
    common_post = fe_post.index
    for d in DONOR_WELLS:
        common_post = common_post.intersection(wells[d].dropna().index)

    X_post = np.column_stack([np.ones(len(common_post))] +
                             [wells[d].loc[common_post].values for d in DONOR_WELLS])
    y_counterfactual = X_post @ b_vec
    y_actual = fe_actual.loc[common_post].values
    divergence = (y_actual - y_counterfactual) * 1000

    ax.bar(common_post, divergence, width=25, color='#D73027', alpha=0.6)
    ax.axhline(divergence.mean(), color='k', ls='--', lw=1,
               label=f'Mean: {divergence.mean():+.0f} mm (p={cal_info["PostFell_divergence_p"]:.4f})')
    ax.axhline(0, color='grey', lw=0.5)
    ax.set_ylabel('Divergence (mm)')
    ax.set_title(f'Post-clearfell: actual minus counterfactual', fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

fig.suptitle('Donor Regression Validation — FE Well Synthetic Extension',
             fontsize=13, y=1.01)
fig.tight_layout()
fig.savefig(OUT_FIG_DONORS, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f" -> Saved: {OUT_FIG_DONORS.name}")

# ============================================================================
# FIGURE: BACI TIMESERIES (one per variant)
# ============================================================================
print("\n7. Generating BACI time-series figures...")


def _vlines(ax):
    ax.axvline(SCRAPING_DATE, color='#999999', ls='--', lw=0.8, zorder=1)
    ax.axvline(INTERVENTION_DATE, color='#333333', ls='-', lw=1.2, zorder=1)
    ax.axvline(SCRAPING_DATE_2, color='#999999', ls=':', lw=0.8, zorder=1)


def plot_variant_timeseries(var_label, out_path):
    """3-panel BACI timeseries for one variant, all three controls."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), dpi=300)
    fig.subplots_adjust(hspace=0.30)

    for i, (ctrl_label, colour) in enumerate(CONTROL_COLOURS.items()):
        key = (var_label, ctrl_label)
        ax = axes[i]

        if key not in all_frames or key not in all_results:
            ax.text(0.5, 0.5, f'No data for {ctrl_label} × {var_label}',
                    ha='center', va='center', transform=ax.transAxes)
            continue

        df = all_frames[key]
        fit = all_results[key]

        # Raw BACI displacement
        ax.plot(df.index, df['baci_disp'] * 1000, color=colour, alpha=0.4,
                lw=0.8, label='Raw')

        # Climate-corrected
        cwb_idx = fit['col_names'].index('cwb')
        cwb_fell_idx = fit['col_names'].index('cwb_x_fell')
        corrected = (df['baci_disp']
                     - fit['b'][cwb_idx] * df['cwb_c']
                     - fit['b'][cwb_fell_idx] * df['cwb_c'] * df['D_fell'])
        if 'easting_x_time' in fit['col_names']:
            east_idx = fit['col_names'].index('easting_x_time')
            corrected = corrected - fit['b'][east_idx] * df['easting_x_time']

        ax.plot(df.index, corrected * 1000, color=colour, lw=1.5,
                label='Climate-corrected')

        # Era means from corrected series (same fix as 10a)
        corrected_mm = corrected * 1000

        pre_scr = df[df.index < SCRAPING_DATE]
        if len(pre_scr) > 0:
            era_mean = corrected_mm.loc[pre_scr.index].mean()
            ax.hlines(era_mean, pre_scr.index[0], SCRAPING_DATE,
                      colors='grey', ls=':', lw=1)

        scr_fell = df[(df.index >= SCRAPING_DATE) & (df.index < INTERVENTION_DATE)]
        if len(scr_fell) > 0:
            era_mean = corrected_mm.loc[scr_fell.index].mean()
            ax.hlines(era_mean, SCRAPING_DATE, INTERVENTION_DATE,
                      colors='grey', ls=':', lw=1)

        post_fell = df[df.index >= INTERVENTION_DATE]
        if len(post_fell) > 0:
            era_mean = corrected_mm.loc[post_fell.index].mean()
            ax.hlines(era_mean,
                      INTERVENTION_DATE, post_fell.index[-1],
                      colors='grey', ls=':', lw=1)

        _vlines(ax)
        ax.set_ylabel('BACI displacement (mm)')
        fell_step = fit['clearfell_step'] * 1000
        ci_mm = (fit['clearfell_ci'][0] * 1000, fit['clearfell_ci'][1] * 1000)
        ax.set_title(
            f'{ctrl_label} control — {var_label}   |   '
            f'Clearfell = {fell_step:+.0f} mm  '
            f'[{ci_mm[0]:+.0f}, {ci_mm[1]:+.0f}]  '
            f'p = {format_p(fit["clearfell_p"])}  '
            f'R² = {fit["r2"]:.3f}',
            fontsize=11)
        ax.legend(loc='upper left', frameon=False, fontsize=9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    fig.suptitle(
        f'ANCOVA-BACI: Synthetic impact — {var_label}\n'
        f'Distance-weighted scraping (λ = {SCRAPING_DECAY_LAMBDA:.0f} m)',
        fontsize=13, y=0.98)
    fig.savefig(out_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f" -> Saved: {out_path.name}")


VAR_FIGS = {
    'A (WMC3+FE1+FE2)': OUT_FIG_VAR_A,
    'B (WMC3+FE2)':      OUT_FIG_VAR_B,
    'C (WMC3 only)':     OUT_FIG_VAR_C,
}

for var_label, out_path in VAR_FIGS.items():
    plot_variant_timeseries(var_label, out_path)

# ============================================================================
# FIGURE: CUSUM — Variant B, Forest control
# ============================================================================
print("\n8. Generating CUSUM figure (Variant B, Forest control)...")

cusum_key = ('B (WMC3+FE2)', 'Forest')
if cusum_key in all_frames and cusum_key in all_results:
    df_cusum = all_frames[cusum_key]
    fit_cusum = all_results[cusum_key]

    # Climate-corrected BACI displacement
    cwb_idx = fit_cusum['col_names'].index('cwb')
    cwb_fell_idx = fit_cusum['col_names'].index('cwb_x_fell')
    corrected = (df_cusum['baci_disp']
                 - fit_cusum['b'][cwb_idx] * df_cusum['cwb_c']
                 - fit_cusum['b'][cwb_fell_idx] * df_cusum['cwb_c'] * df_cusum['D_fell'])
    if 'easting_x_time' in fit_cusum['col_names']:
        east_idx = fit_cusum['col_names'].index('easting_x_time')
        corrected = corrected - fit_cusum['b'][east_idx] * df_cusum['easting_x_time']

    # CUSUM of the climate-corrected series (demeaned on pre-felling baseline)
    pre_fell_mean = corrected[corrected.index < INTERVENTION_DATE].mean()
    detrended = corrected - pre_fell_mean
    cusum = detrended.cumsum() * 1000  # mm

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), dpi=300,
                             gridspec_kw={'height_ratios': [2, 1]})
    fig.subplots_adjust(hspace=0.25)

    # Top panel: climate-corrected BACI displacement
    ax = axes[0]
    ax.plot(df_cusum.index, df_cusum['baci_disp'] * 1000, color=CB_FOREST,
            alpha=0.4, lw=0.8, label='Raw')
    ax.plot(corrected.index, corrected * 1000, color=CB_FOREST, lw=1.5,
            label='Climate-corrected')

    # Era means
    corrected_mm = corrected * 1000
    for era_mask, x0, x1 in [
        (df_cusum.index < SCRAPING_DATE,
         df_cusum.index[0], SCRAPING_DATE),
        ((df_cusum.index >= SCRAPING_DATE) & (df_cusum.index < INTERVENTION_DATE),
         SCRAPING_DATE, INTERVENTION_DATE),
        (df_cusum.index >= INTERVENTION_DATE,
         INTERVENTION_DATE, df_cusum.index[-1]),
    ]:
        era_data = corrected_mm[era_mask]
        if len(era_data) > 0:
            ax.hlines(era_data.mean(), x0, x1, colors='grey', ls=':', lw=1)

    _vlines(ax)
    ax.set_ylabel('BACI displacement (mm)')
    ax.set_title('Forest control — B (WMC3+FE2): climate-corrected BACI displacement',
                 fontsize=11)
    ax.legend(loc='upper left', frameon=False, fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Bottom panel: CUSUM
    ax = axes[1]
    ax.fill_between(cusum.index, 0, cusum.values, color=CB_FOREST, alpha=0.3)
    ax.plot(cusum.index, cusum.values, color=CB_FOREST, lw=1.5)
    ax.axhline(0, color='grey', lw=0.5)
    _vlines(ax)

    # Annotate key values
    cusum_at_fell = cusum.loc[cusum.index >= INTERVENTION_DATE]
    if len(cusum_at_fell) > 0:
        ax.annotate(f'At clearfell: {cusum_at_fell.iloc[0]:.0f} mm',
                    xy=(INTERVENTION_DATE, cusum_at_fell.iloc[0]),
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

    fig.suptitle('CUSUM Analysis — Synthetic Impact B (WMC3+FE2) vs Forest Control',
                 fontsize=13, y=0.98)
    fig.savefig(OUT_FIG_CUSUM, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f" -> Saved: {OUT_FIG_CUSUM.name}")
else:
    print("   WARNING: Variant B Forest not available for CUSUM")

# ============================================================================
# FIGURE: CLIMATE SENSITIVITY SCATTER — All variants, Forest control
# ============================================================================
print("\n9. Generating climate sensitivity scatter (Forest control)...")

fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=300)
fig.subplots_adjust(wspace=0.30)

for i, (var_label, var_colour) in enumerate([
    ('A (WMC3+FE1+FE2)', '#999999'),
    ('B (WMC3+FE2)', CB_FOREST),
    ('C (WMC3 only)', '#2C7BB6'),
]):
    ax = axes[i]
    key = (var_label, 'Forest')

    if key not in all_frames:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                transform=ax.transAxes)
        continue

    df = all_frames[key]
    fit = all_results[key]

    pre = df[df.index < INTERVENTION_DATE]
    post = df[df.index >= INTERVENTION_DATE]

    ax.scatter(pre['cwb'], pre['baci_disp'] * 1000,
               color=var_colour, alpha=0.4, s=20, label='Pre-felling')
    ax.scatter(post['cwb'], post['baci_disp'] * 1000,
               color=var_colour, marker='x', s=30, label='Post-felling')

    # Regression lines (separate for pre/post)
    for subset, ls in [(pre, '--'), (post, '-')]:
        if len(subset) > 5:
            slope, intercept = np.polyfit(subset['cwb'],
                                         subset['baci_disp'] * 1000, 1)
            x_line = np.linspace(subset['cwb'].min(),
                                 subset['cwb'].max(), 50)
            ax.plot(x_line, slope * x_line + intercept, color='grey',
                    ls=ls, lw=1)

    ax.set_xlabel('Cumulative water balance (mm)')
    ax.set_ylabel('Impact BACI disp. (mm)')

    fell_step = fit['clearfell_step'] * 1000
    ax.set_title(f'{var_label}\nstep = {fell_step:+.0f} mm  '
                 f'p = {format_p(fit["clearfell_p"])}', fontsize=10)
    if i == 0:
        ax.legend(loc='best', frameon=False, fontsize=8)

fig.suptitle('Climate sensitivity: CWB vs BACI displacement — Forest control',
             fontsize=13, y=1.02)
fig.savefig(OUT_FIG_SENSITIVITY, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f" -> Saved: {OUT_FIG_SENSITIVITY.name}")

# ============================================================================
# REPORT NUMBERS
# ============================================================================
print("\n10. Exporting report numbers...")
rpt = ReportNumbers()

for _, row in cal_df.iterrows():
    prefix = f"synth_{row['Well']}"
    rpt.add(f"{prefix}_R2_cal", row['R2_cal'])
    rpt.add(f"{prefix}_RMSE_mm", row['RMSE_mm'], unit='mm')
    rpt.add(f"{prefix}_hindcast_months", row['Hindcast_months'])
    rpt.add(f"{prefix}_pre_scraping_months", row['PreScraping_months_gained'])
    rpt.add(f"{prefix}_postfell_divergence_mm", row['PostFell_divergence_mm'],
            unit='mm')
    rpt.add(f"{prefix}_postfell_divergence_p", row['PostFell_divergence_p'])

for _, row in comp_df.iterrows():
    prefix = f"ANCOVA_{row['Variant']}_{row['Control']}"
    prefix = prefix.replace(' ', '_').replace('(', '').replace(')', '')
    rpt.add(f"{prefix}_clearfell_step", row['Clearfell_step_m'], unit='m')
    rpt.add(f"{prefix}_clearfell_p", row['Clearfell_p'])
    rpt.add(f"{prefix}_R2", row['R2'])
    rpt.add(f"{prefix}_N", row['N'])
    if pd.notna(row.get('Net_clearfell_m')):
        rpt.add(f"{prefix}_net_clearfell", row['Net_clearfell_m'], unit='m',
                note='Forest/Combined step minus Climate background')

rpt.save(OUT_REPORT)
print(f" -> Saved: {OUT_REPORT.name}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 72)
print("SYNTHETIC-EXTENSION BACI SUMMARY")
print("=" * 72)

print(f"\n  Donor wells: {', '.join(d.upper() for d in DONOR_WELLS)} (Forest Control)")
for _, row in cal_df.iterrows():
    print(f"  {row['Well']}: R²={row['R2_cal']:.4f}, RMSE={row['RMSE_mm']:.0f} mm, "
          f"hindcast={row['Hindcast_months']} months, "
          f"divergence={row['PostFell_divergence_mm']:+.0f} mm (p={row['PostFell_divergence_p']:.4f})")

print(f"\n  {'Variant':<25s} {'Control':<10s} {'Step (mm)':>10s} {'CI':>20s} {'p':>10s} {'R²':>6s} {'Net (mm)':>10s}")
print("  " + "-" * 95)
for _, row in comp_df.iterrows():
    ci = f"[{row['Clearfell_CI_lo_m']*1000:+.0f}, {row['Clearfell_CI_hi_m']*1000:+.0f}]"
    net = row.get('Net_clearfell_m', np.nan)
    net_str = f"{net*1000:+.0f}" if pd.notna(net) else ""
    print(f"  {row['Variant']:<25s} {row['Control']:<10s} "
          f"{row['Clearfell_step_m']*1000:>+10.0f} {ci:>20s} "
          f"{format_p(row['Clearfell_p']):>10s} {row['R2']:>6.3f} {net_str:>10s}")

print(f"\n  Net clearfell = Forest (or Combined) step minus Climate background step")

print(f"\n  Scraping decay λ = {SCRAPING_DECAY_LAMBDA:.0f} m")
print("=" * 72)
print("Script 10h complete.\n")
