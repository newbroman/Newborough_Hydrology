r"""
====================================================================================
10a — THREE-COUNTERFACTUAL ANCOVA-BACI ANALYSIS
====================================================================================
Purpose
-------
Primary clearfell result.  Runs the same ANCOVA model three times with
different control centroids (forest, climate, combined), applied to both
the impact and edge tiers, yielding six ANCOVA results.  Distance-weighted
scraping (exponential decay, λ = 300 m) replaces the binary scraping dummy.
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

__version__ = "1.0.0"  # Hollingham (2026) — 2026-05-04

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.clearfell_common import (
    load_clearfell_data,
    IMPACT_WELLS, EDGE_WELLS,
    FOREST_CONTROL_WELLS, COASTAL_CONTROL_WELLS, CLIMATE_CONTROL_WELLS,
    TIERS, ALL_NETWORK_WELLS,
    INTERVENTION_DATE, SCRAPING_DATE, SCRAPING_DATE_2, FELLING_YEAR,
    SCRAPING_DECAY_LAMBDA,
    compute_baci_displacement, compute_control_centroid,
    compute_cwb,
    build_scraping_covariate_centroid,
    distance_from_ceh36, scraping_weight, distance_weighted_scraping,
    TIER_COLOURS, ReportNumbers, print_network_summary,
    CEH36_EASTING, CEH36_NORTHING,
)
from utils.paths import make_all_dirs, DIR_10
from utils.config import DRAINAGE_DATUM
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
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
OUT_FIG_IMPACT    = DIR_10 / "10a_04_baci_timeseries_impact.png"
OUT_FIG_EDGE      = DIR_10 / "10a_05_baci_timeseries_edge.png"
OUT_FIG_SCATTER   = DIR_10 / "10a_06_climate_sensitivity.png"

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
print("=" * 72)
print("SCRIPT 10a — THREE-COUNTERFACTUAL ANCOVA-BACI")
print("=" * 72)

print("\n1. Loading data...")
wells, climate, master, well_locations, valid_tiers = load_clearfell_data()
print_network_summary(valid_tiers)

# ============================================================================
# BUILD BACI DISPLACEMENT TIME-SERIES (for each control)
# ============================================================================
print("2. Building BACI displacement time-series...")

CONTROLS = {
    'Forest':   FOREST_CONTROL_WELLS,                    # C4 only (5 wells)
    'Climate':  CLIMATE_CONTROL_WELLS,                   # C3 (5 wells)
    'Combined': (FOREST_CONTROL_WELLS +                  # All 12 controls
                 COASTAL_CONTROL_WELLS +
                 CLIMATE_CONTROL_WELLS),
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
    df['D_fell'] = (df.index >= INTERVENTION_DATE).astype(float)

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
    df['has_easting'] = False
    if easting_range > 200:
        target_eastings = [well_locations[w]['easting'] for w in target_wells
                           if w in well_locations]
        control_eastings = [well_locations[w]['easting'] for w in control_wells
                            if w in well_locations]
        if target_eastings and control_eastings:
            delta_easting = np.mean(target_eastings) - np.mean(control_eastings)
            # Time trend: months since start of record
            t0 = df.index.min()
            months_since = ((df.index - t0).days / 30.4375)
            df['easting_x_time'] = delta_easting * months_since
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
# RUN THREE-COUNTERFACTUAL ANCOVA
# ============================================================================
print("3. Running three-counterfactual ANCOVA...")

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
            print("SKIPPED (insufficient data)")
            continue

        ancova_frames[key] = df

        # Easting interaction: include for Climate and Combined controls only
        use_easting = (ctrl_label in ('Climate', 'Combined')
                       and df['has_easting'].iloc[0])

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
# SENSITIVITY: scraping decay length
# ============================================================================
print("\n4. Scraping decay sensitivity (λ = 200 m, 500 m)...")
sensitivity_rows = []
for lam in [200, 500]:
    for ctrl_label, ctrl_wells in CONTROLS.items():
        for zone_label, zone_wells in ZONES.items():
            df = build_ancova_frame(
                wells, climate, zone_wells, ctrl_wells,
                well_locations, lambda_m=lam)
            if df is None:
                continue
            use_easting = (ctrl_label in ('Climate', 'Combined')
                           and df['has_easting'].iloc[0])
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
print("\n5. Exporting comparison table...")

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
        'Clearfell_step_m': round(fit['clearfell_step'], 4),
        'Clearfell_CI_lo_m': round(fit['clearfell_ci'][0], 4),
        'Clearfell_CI_hi_m': round(fit['clearfell_ci'][1], 4),
        'Clearfell_p': fit['clearfell_p'],
        'Clearfell_sig': p_to_sig(fit['clearfell_p']),
        'Scraping_step_m': round(fit['scraping_step'], 4),
        'Scraping_p': fit['scraping_p'],
        'Easting_coef': easting_coef if not np.isnan(easting_coef) else '',
        'Easting_p': easting_p if not np.isnan(easting_p) else '',
        'R2': round(fit['r2'], 4),
        'N': fit['n'],
        'Oct2023_step_m': round(fit['m3_scrape2_coef'], 4) if not np.isnan(fit['m3_scrape2_coef']) else '',
        'Oct2023_p': fit['m3_scrape2_p'] if not np.isnan(fit['m3_scrape2_p']) else '',
        'dAIC_M3_M2': round(fit['daic'], 2) if not np.isnan(fit['daic']) else '',
    })

comp_df = pd.DataFrame(comp_rows)
comp_df.to_csv(OUT_COMPARISON, index=False)
print(f" -> Saved: {OUT_COMPARISON.name} ({len(comp_df)} rows)")

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
            'Value': round(fit['b'][i], 6),
            'SE': round(fit['se'][i], 6),
            'p': fit['p'][i],
            'Sig': p_to_sig(fit['p'][i]),
        })

coeff_df = pd.DataFrame(coeff_rows)
coeff_df.to_csv(OUT_FULL_COEFFS, index=False)
print(f" -> Saved: {OUT_FULL_COEFFS.name} ({len(coeff_df)} rows)")

# ============================================================================
# EXPORT: BACI TIMESERIES DATA
# ============================================================================
print("6. Exporting BACI time-series data...")

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
print(f" -> Saved: {OUT_TIMESERIES.name} ({len(ts_df)} rows)")

# ============================================================================
# FIGURE: BACI TIMESERIES (IMPACT)
# ============================================================================
print("7. Generating BACI time-series figures...")


def _vlines(ax):
    """Add intervention date lines."""
    ax.axvline(SCRAPING_DATE, color='#999999', ls='--', lw=0.8, zorder=1)
    ax.axvline(INTERVENTION_DATE, color='#333333', ls='-', lw=1.2, zorder=1)
    ax.axvline(SCRAPING_DATE_2, color='#999999', ls=':', lw=0.8, zorder=1)


def _shade(ax, ymin=None, ymax=None):
    """Shade the pre-scraping and post-felling eras."""
    if ymin is None:
        ymin, ymax = ax.get_ylim()
    ax.axvspan(ax.get_xlim()[0], mdates.date2num(SCRAPING_DATE),
               alpha=0.04, color='blue', zorder=0)
    ax.axvspan(mdates.date2num(INTERVENTION_DATE), ax.get_xlim()[1],
               alpha=0.04, color='red', zorder=0)


def plot_baci_timeseries(zone_label, out_path):
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

        # Era means — computed from the corrected series itself.
        # NOTE: We cannot use intercept + b_scrape for the post-scraping
        # era because D_scrape is distance-weighted (fractional, not 0/1).
        # The raw coefficient b_scrape corresponds to D_scrape=1, but the
        # actual D_scrape value depends on well geometry.  Computing means
        # directly from the corrected series avoids this mismatch.
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
    fig.savefig(out_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f" -> Saved: {out_path.name}")


plot_baci_timeseries('Impact', OUT_FIG_IMPACT)
plot_baci_timeseries('Edge', OUT_FIG_EDGE)

# ============================================================================
# FIGURE: CLIMATE SENSITIVITY SCATTER
# ============================================================================
print("8. Generating climate sensitivity scatter...")

fig, axes = plt.subplots(2, 3, figsize=(16, 10), dpi=300)
fig.subplots_adjust(hspace=0.35, wspace=0.30)

for j, zone_label in enumerate(ZONES.keys()):
    for i, (ctrl_label, colour) in enumerate(CONTROL_COLOURS.items()):
        ax = axes[j, i]
        key = (ctrl_label, zone_label)

        if key not in ancova_frames or key not in results:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                    transform=ax.transAxes)
            continue

        df = ancova_frames[key]
        fit = results[key]

        pre = df[df.index < INTERVENTION_DATE]
        post = df[df.index >= INTERVENTION_DATE]

        ax.scatter(pre['cwb'], pre['baci_disp'] * 1000,
                   color=colour, alpha=0.4, s=20, label='Pre-felling')
        ax.scatter(post['cwb'], post['baci_disp'] * 1000,
                   color=colour, marker='x', s=30, label='Post-felling')

        # Regression lines
        for subset, ls in [(pre, '--'), (post, '-')]:
            if len(subset) > 5:
                slope, intercept = np.polyfit(subset['cwb'], subset['baci_disp'] * 1000, 1)
                x_line = np.linspace(subset['cwb'].min(), subset['cwb'].max(), 50)
                ax.plot(x_line, slope * x_line + intercept, color='grey',
                        ls=ls, lw=1)

        ax.set_xlabel('Cumulative water balance (mm)')
        ax.set_ylabel(f'{zone_label} BACI disp. (mm)')
        ax.set_title(f'{ctrl_label} control', fontsize=11)
        if j == 0 and i == 0:
            ax.legend(loc='best', frameon=False, fontsize=8)

fig.suptitle('Climate sensitivity: CWB vs BACI displacement', fontsize=13, y=0.98)
fig.savefig(OUT_FIG_SCATTER, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f" -> Saved: {OUT_FIG_SCATTER.name}")

# ============================================================================
# EXPORT: REPORT NUMBERS
# ============================================================================
print("\n9. Exporting report numbers...")
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

    # Oct 2023 re-scraping test
    if not np.isnan(fit['m3_scrape2_coef']):
        rpt.add(f"{prefix}_Oct2023_step", fit['m3_scrape2_coef'],
                well=zone_label, era="Oct2023",
                note=f"p={format_p(fit['m3_scrape2_p'])}, dAIC={fit['daic']:.2f}")

# Sensitivity results
for _, row in sensitivity_df.iterrows():
    rpt.add(f"Sensitivity_lambda{row['Lambda_m']:.0f}_{row['Control']}_{row['Zone']}_clearfell",
            row['Clearfell_step_m'],
            well=row['Zone'],
            note=f"p={format_p(row['Clearfell_p'])}, R²={row['R2']:.3f}")

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
print(f" -> Saved: {OUT_REPORT.name} ({n_saved} rows)")

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
