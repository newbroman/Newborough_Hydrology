"""
====================================================================================
22_residual_lag_analysis.py — SSM Residuals, AR(1) Diagnostics, and Alpha-Phi Scatter
====================================================================================
Purpose:
    Stage 1 of the ridge-subsidy lag analysis (see Section 11 further work).

    Refits Model B (SSM with intercept, lag-1 rainfall, displacement formulation)
    for every reference well with >= 140 months of data on the FULL record, then:
        1. Saves the per-well Model B residual series e_B(t).
           The intercept absorbs the constant (mean) part of the residual so e_B(t)
           represents only the time-varying component — the only part that can
           legitimately carry a lag signal against past rainfall.
        2. Computes AR(1) diagnostics on e_B(t) to decide which wells will need
           pre-whitening before cross-correlation in Stage 2.
        3. Produces an alpha vs AR(1)-phi scatter to test whether the wells with
           the largest persistent subsidies are also the wells with the most
           time-structured residuals — the physical expectation if ridge-derived
           lateral flux is both high in mean and variable in time.

Outputs:
    INT_22_RESIDUALS_WIDE    — wide CSV, rows = months, cols = wells, values = e_B(t)
    INT_22_FITS_TABLE        — per-well: alpha, betas, R2, n, ar1_phi, ar1_p, etc.
    OUT_22_AR1_HIST          — histogram of AR(1) coefficients by cluster
    OUT_22_AR1_MAP           — spatial map of AR(1) coefficient per well
    OUT_22_ALPHA_PHI_SCATTER — scatter of alpha vs AR(1)-phi, coloured by cluster
    OUT_22_EXAMPLE_SERIES    — one residual time series per cluster

Window choice:
    Script 07 uses the most recent 100 months. This script uses the FULL record
    per well to maximise statistical power at long lags and to support the
    rolling-window analysis planned for stage 3. The trade-off is that betas
    here are fitted across the whole record rather than on the recent window used
    in the report's Table 2 and Figure 15a. The two should be similar but will
    not be identical (e.g. CEH14 alpha may differ between full-record and 100-mo
    window). Table 2 / Figure 15a remain authoritative for the main report; this
    script is an analytical companion.

Well exclusions (EXCLUDED_WELLS_NORM):
    ceh7, ceh8, ceh37 — upstream exclusions carried over from Script 07
    ceh3              — tidal boundary; outside SSM operational domain (report S4.4.2)
    ceh4              — coastal erosion drift plus post-2017 clearfell drawdown
                        (report S4.5 notes CEH4 itself has been drawn down by the
                        felling pulse); these confound any lag signal.
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.paths import (
    make_all_dirs,
    INT_WELLS_CLEAN, INT_CLIMATE, INT_LOCATIONS, INT_CLUSTER_STATS,
    INT_MASTER_DATA,
    # New Script 22 paths — added to paths.py by accompanying patch:
    INT_22_RESIDUALS_WIDE, INT_22_FITS_TABLE,
    OUT_22_AR1_HIST, OUT_22_AR1_MAP, OUT_22_ALPHA_PHI_SCATTER,
    OUT_22_EXAMPLE_SERIES,
)
from utils.data_utils import normalize_well_name
from utils.map_utils import add_kml_features
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS
from utils.model_utils import fit_ssm_intercept


# ==========================================
# CONFIGURATION
# ==========================================
MIN_MONTHS = 140
AR1_WHITE_THRESHOLD = 0.3  # |phi| below this is treated as effectively white
AR1_DIAG_PVAL = 0.05

# Lag and displacement handled by fit_ssm_intercept() from model_utils.

# Wells excluded from the lag analysis. See docstring for rationale per well.
EXCLUDED_WELLS_NORM = {'ceh7', 'ceh8', 'ceh37', 'ceh3', 'ceh4'}

# CLUSTER_LABELS and CLUSTER_COLOURS imported from utils.config (k=5 partition).

plt.rcParams.update({
    'font.family': 'sans-serif',
    'axes.labelsize': 12, 'axes.titlesize': 14,
    'xtick.labelsize': 10, 'ytick.labelsize': 10,
    'legend.fontsize': 10,
})


# ==========================================
# CORE COMPUTATION
# ==========================================

def fit_model_b(well_series, climate):
    """Fit Model B (SSM with intercept) via shared model_utils function.

    Uses full record (no windowing), MIN_MONTHS threshold.
    Returns dict with alpha, betas, R2, n, resid — or None.
    """
    return fit_ssm_intercept(well_series, climate, min_obs=MIN_MONTHS)


def ar1_diagnostic(residuals):
    """
    Fit AR(1) to the residual series via OLS on lag-1. Returns (phi, p, sigma).
    """
    r = residuals.dropna().values
    if len(r) < 30:
        return np.nan, np.nan, np.nan
    r_t   = r[1:]
    r_tm1 = r[:-1]
    X = sm.add_constant(r_tm1)
    try:
        m = sm.OLS(r_t, X).fit()
        return float(m.params[1]), float(m.pvalues[1]), float(np.std(m.resid, ddof=1))
    except Exception:
        return np.nan, np.nan, np.nan


# ==========================================
# PLOTTING
# ==========================================

def plot_ar1_hist(fits_df, output_path):
    """Histogram of AR(1) coefficients by cluster."""
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    bins = np.linspace(-0.3, 0.7, 25)

    for cid, col in CLUSTER_COLOURS.items():
        sub = fits_df[fits_df['Cluster'] == cid]['ar1_phi'].dropna()
        if len(sub):
            ax.hist(sub, bins=bins, alpha=0.65, color=col,
                    label=f"{CLUSTER_LABELS[cid]} (n={len(sub)})",
                    edgecolor='black', linewidth=0.5)

    ax.axvline(0, color='black', lw=1.2, ls='--', alpha=0.7)
    ax.axvspan(-AR1_WHITE_THRESHOLD, AR1_WHITE_THRESHOLD,
               alpha=0.1, color='green',
               label=f'|phi| < {AR1_WHITE_THRESHOLD}: near-white')
    ax.set_xlabel('AR(1) coefficient of Model B residuals')
    ax.set_ylabel('Number of wells')
    ax.set_title('Autocorrelation of SSM Model B residuals\n'
                 f"(Full record, n = {fits_df['ar1_phi'].notna().sum()} wells)",
                 fontweight='bold')
    ax.legend(loc='upper right', frameon=True, edgecolor='black', fontsize=9)
    ax.grid(axis='y', ls='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


def plot_ar1_map(fits_df, output_path):
    """Spatial map of AR(1) coefficient per well."""
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    valid = fits_df.dropna(subset=['Easting', 'Northing', 'ar1_phi'])
    if valid.empty:
        print(" -> Skipped AR(1) map (no valid coordinates).")
        return

    vmax = max(abs(valid['ar1_phi'].quantile(0.05)),
               abs(valid['ar1_phi'].quantile(0.95)),
               AR1_WHITE_THRESHOLD)
    sc = ax.scatter(valid['Easting'], valid['Northing'],
                    c=valid['ar1_phi'], cmap='RdBu_r',
                    vmin=-vmax, vmax=vmax,
                    s=90, edgecolor='black', linewidth=0.8, zorder=5)
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label('AR(1) coefficient', fontsize=11)

    try:
        add_kml_features(ax)
    except Exception as e:
        print(f"  [note] KML overlay skipped: {e}")

    ax.set_xlabel('Easting (m, OSGB36)')
    ax.set_ylabel('Northing (m, OSGB36)')
    ax.set_title('Residual autocorrelation across the network\n'
                 f"(wells with |phi| >= {AR1_WHITE_THRESHOLD} need pre-whitening "
                 'before lag analysis)',
                 fontweight='bold')
    ax.set_aspect('equal')
    ax.grid(ls='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


def plot_alpha_phi_scatter(fits_df, output_path):
    """Scatter of intercept alpha vs residual AR(1) coefficient."""
    fig, ax = plt.subplots(figsize=(9, 7), dpi=300)
    valid = fits_df.dropna(subset=['alpha', 'ar1_phi'])

    for cid, col in CLUSTER_COLOURS.items():
        sub = valid[valid['Cluster'] == cid]
        if len(sub):
            ax.scatter(sub['alpha'], sub['ar1_phi'],
                       color=col, s=70, edgecolor='black', linewidth=0.7,
                       label=f"{CLUSTER_LABELS[cid]} (n={len(sub)})",
                       alpha=0.85, zorder=3)

    # Label ridge-adjacent and notable wells
    for well_to_label in ['ceh14', 'ceh34', 'ceh13', 'ceh2', 'nw10', 'nw1']:
        row = valid[valid['Well_Normalized'] == well_to_label]
        if not row.empty:
            ax.annotate(well_to_label.upper(),
                        xy=(row['alpha'].iloc[0], row['ar1_phi'].iloc[0]),
                        xytext=(6, 6), textcoords='offset points',
                        fontsize=9, fontweight='bold', zorder=4)

    ax.axhline(0, color='grey', lw=0.8, ls='-', alpha=0.5)
    ax.axvline(0, color='grey', lw=0.8, ls='-', alpha=0.5)
    ax.axhspan(-AR1_WHITE_THRESHOLD, AR1_WHITE_THRESHOLD,
               color='green', alpha=0.08, zorder=0)

    # Correlation coefficient as annotation
    if len(valid) > 3:
        r = valid[['alpha', 'ar1_phi']].corr().iloc[0, 1]
        ax.text(0.02, 0.98, f'Pearson r = {r:+.2f}\nn = {len(valid)}',
                transform=ax.transAxes, va='top', ha='left',
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white',
                          edgecolor='black', alpha=0.8))

    ax.set_xlabel('Model B intercept alpha (m / month)')
    ax.set_ylabel('AR(1) coefficient of Model B residuals (phi)')
    ax.set_title('Persistent subsidy vs residual autocorrelation\n'
                 'Wells with large alpha AND large phi have unmodelled input '
                 'that is both high in mean and variable in time',
                 fontweight='bold')
    ax.legend(loc='lower right', frameon=True, edgecolor='black', fontsize=9)
    ax.grid(ls='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


def plot_example_residuals(residuals_wide, fits_df, output_path):
    """One example residual time series per cluster (longest record with valid AR1)."""
    present_clusters = sorted(c for c in CLUSTER_LABELS
                              if (fits_df['Cluster'] == c).any())
    n_panels = max(1, len(present_clusters))

    fig, axes = plt.subplots(n_panels, 1, figsize=(13, 2.4 * n_panels),
                             dpi=300, sharex=True)
    if n_panels == 1:
        axes = [axes]

    for ax, cid in zip(axes, present_clusters):
        sub = fits_df[(fits_df['Cluster'] == cid) & fits_df['ar1_phi'].notna()]
        if sub.empty:
            ax.text(0.5, 0.5, f'{CLUSTER_LABELS[cid]}: no eligible wells',
                    ha='center', va='center', transform=ax.transAxes)
            continue
        pick = sub.sort_values('n', ascending=False).iloc[0]
        well = pick['Well_Normalized']

        if well not in residuals_wide.columns:
            ax.text(0.5, 0.5, f'{well}: residual series not found',
                    ha='center', va='center', transform=ax.transAxes)
            continue

        s = residuals_wide[well].dropna()
        ax.plot(s.index, s.values, color=CLUSTER_COLOURS[cid], lw=1.0)
        ax.axhline(0, color='black', lw=0.8, ls='--', alpha=0.7)
        ax.set_ylabel('e_B(t) (m)', fontsize=10)
        ax.set_title(f"{CLUSTER_LABELS[cid]}  |  {well.upper()}  |  "
                     f"n = {int(pick['n'])} mo  |  phi = {pick['ar1_phi']:+.3f}  |  "
                     f"alpha = {pick['alpha']:+.3f} m/mo",
                     fontsize=11, loc='left')
        ax.grid(ls='--', alpha=0.4)

    axes[-1].set_xlabel('Date')
    fig.suptitle('Example SSM Model B residuals by cluster\n'
                 '(constant part absorbed by alpha; shown series is time-varying part only)',
                 fontweight='bold', y=1.00)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


# ==========================================
# MAIN
# ==========================================

def main():
    make_all_dirs()
    print("Starting 22: SSM Residual and AR(1) Diagnostics...")

    wells      = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    climate    = pd.read_csv(INT_CLIMATE,    index_col=0, parse_dates=True)
    locations  = pd.read_csv(INT_LOCATIONS)
    cluster_df = pd.read_csv(INT_CLUSTER_STATS)

    cluster_df['_norm'] = cluster_df['Match_ID'].apply(normalize_well_name)
    cluster_lookup = dict(zip(cluster_df['_norm'], cluster_df['Cluster']))

    locations['_norm'] = locations['Name'].apply(normalize_well_name)
    coords_lookup = {r['_norm']: (r['E'], r['N']) for _, r in locations.iterrows()}

    # Candidate wells: everything in wells_clean not in the exclusion set
    candidate_wells = [c for c in wells.columns
                       if normalize_well_name(c) not in EXCLUDED_WELLS_NORM]
    print(f" -> Candidate wells: {len(candidate_wells)} "
          f"(excluded: {sorted(EXCLUDED_WELLS_NORM)})")

    fits = []
    residuals_dict = {}
    for well_col in candidate_wells:
        norm = normalize_well_name(well_col)
        result = fit_model_b(wells[well_col], climate)
        if result is None:
            continue

        phi, p, sigma = ar1_diagnostic(result['resid'])
        residuals_dict[norm] = result['resid']

        fits.append({
            'Well':            well_col,
            'Well_Normalized': norm,
            'Cluster':         cluster_lookup.get(norm, np.nan),
            'Easting':         coords_lookup.get(norm, (np.nan, np.nan))[0],
            'Northing':        coords_lookup.get(norm, (np.nan, np.nan))[1],
            'n':               result['n'],
            'alpha':           result['alpha'],
            'pvalue_alpha':    result['pvalue_alpha'],
            'beta_1':          result['beta_1'],
            'beta_2':          result['beta_2'],
            'beta_3':          result['beta_3'],
            'R2':              result['R2'],
            'mean_resid':      float(result['resid'].mean()),
            'std_resid':       float(result['resid'].std()),
            'ar1_phi':         phi,
            'ar1_pvalue':      p,
            'ar1_sigma':       sigma,
        })

    fits_df = pd.DataFrame(fits)
    print(f" -> Fitted Model B for {len(fits_df)} wells "
          f"(>= {MIN_MONTHS} months of data).")

    if not residuals_dict:
        print(" -> No residuals to save (all wells filtered out).")
        return

    residuals_wide = pd.DataFrame(residuals_dict).sort_index()
    residuals_wide.to_csv(INT_22_RESIDUALS_WIDE)
    print(f" -> Saved: {INT_22_RESIDUALS_WIDE.name} "
          f"({residuals_wide.shape[0]} months x {residuals_wide.shape[1]} wells)")

    fits_df.to_csv(INT_22_FITS_TABLE, index=False)
    print(f" -> Saved: {INT_22_FITS_TABLE.name}")

    # Diagnostics summary
    ar1 = fits_df['ar1_phi'].dropna()
    print("\n" + "=" * 62)
    print("  AR(1) DIAGNOSTICS SUMMARY")
    print("=" * 62)
    print(f"  Wells with AR(1) fit:          {len(ar1)}")
    print(f"  Mean phi:                      {ar1.mean():+.3f}")
    print(f"  Median phi:                    {ar1.median():+.3f}")
    print(f"  Wells with |phi| <  {AR1_WHITE_THRESHOLD}:       "
          f"{(ar1.abs() <  AR1_WHITE_THRESHOLD).sum()} / {len(ar1)}")
    print(f"  Wells with |phi| >= {AR1_WHITE_THRESHOLD}:       "
          f"{(ar1.abs() >= AR1_WHITE_THRESHOLD).sum()} / {len(ar1)}")
    print(f"  Wells with significant AR(1) (p < {AR1_DIAG_PVAL}): "
          f"{(fits_df['ar1_pvalue'] < AR1_DIAG_PVAL).sum()} / {len(ar1)}")
    print("\n  Per-cluster mean phi:")
    print(fits_df.groupby('Cluster')['ar1_phi'].mean().round(3).to_string())
    print("=" * 62)

    # Plots
    plot_ar1_hist(fits_df, OUT_22_AR1_HIST)
    plot_ar1_map(fits_df, OUT_22_AR1_MAP)
    plot_alpha_phi_scatter(fits_df, OUT_22_ALPHA_PHI_SCATTER)
    plot_example_residuals(residuals_wide, fits_df, OUT_22_EXAMPLE_SERIES)

    print("\n22 complete. Next: cross-correlation stage (22b).")


if __name__ == "__main__":
    main()
