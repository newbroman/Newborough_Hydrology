"""
====================================================================================
23_ridge_recharge_lag_test.py — Test the ridge-derived recharge hypothesis
====================================================================================

LIMITATION NOTE (2026-05-17):
    This diagnostic is retained for completeness but its result should not
    be cited as confirmation or refutation of ridge-derived recharge.

    The test design — peak-correlation lag of residuals against rainfall,
    Spearman-correlated with distance from a ridge reference point — was
    investigated in detail in May 2026 and found to be statistically
    degenerate against this dataset for three structural reasons:

      1. Monthly time resolution cannot resolve sub-monthly to ~2-month
         travel times across a ~2 km transect. 60+ of 64 wells peak at
         lag 1 or 2 regardless of distance from the ridge, even under a
         clean Box-Jenkins pre-whitened reformulation.

      2. Peak-lag is a poor summary of the cross-correlation function.
         It discards amplitude and shape information, and the argmax over
         a bounded discrete lag grid has no clean sampling distribution
         under standard statistical inference.

      3. The water-balance residual that the ridge mechanism would explain
         is ~2.5% of annual flux — at or below the per-well α uncertainty
         of the headline SSM. A signal of this magnitude is at the noise
         floor of the data regardless of test design.

    The ridge-recharge hypothesis is therefore neither confirmed nor
    refuted by the current monitoring design; this is a limitation of the
    data, not of the test. See §5.3 of the main report and §S.16 of the
    Methods Supplement for the final framing.

Purpose:
    Tests whether the water-balance residual attributed to ridge-derived recharge
    in the report (Section 4.4.2 / 5.3) behaves like genuine lateral recharge
    from the northern rock ridge, or whether it is more likely to be model
    misspecification absorbing under a common label.

    The physical hypothesis:
        If the residual is genuinely ridge-derived recharge, then water arriving
        at any given well had to travel from the ridge to that well. This travel
        has a time, and that time must increase with distance from the ridge.
        The lag structure of the residual series, cross-correlated against
        rainfall, should therefore show a peak-correlation lag that increases
        with distance from the ridge reference point.

        If no such distance-lag relationship exists, the residual cannot be
        attributed to ridge recharge on mechanistic grounds alone.

    Methodological note:
        Script 22 documents AR(1) persistence in the headline SSM residuals
        (Delta_h = a + b1*P(t) - b2*PET(t) - b3*h_disp_prev(t)) across the
        reference network. The positive AR(1) phi values are consistent with
        vadose-zone moisture memory and other second-order persistence not
        absorbed by the headline SSM — the headline model captures drainage
        proportional to start-of-month head via b3*h_disp_prev, but does not
        model storage-state memory in the unsaturated zone. This residual
        persistence is an expected hydrological feature, not a model defect,
        but it could mask any ridge-specific lag structure if present.

        This script refits with BOTH P(t) and P(t-1) as regressors. The
        residuals from this richer model are explicitly free of any generic
        first-order rainfall lag confound. Any remaining lag structure in
        the residuals is the candidate ridge signal.

    The report's fitted b1, b2, b3 and alpha values are UNCHANGED by this script
    and remain authoritative. This is a diagnostic analysis, not a revision.

    SSM specification note:
        The β₃ term uses the displacement formulation (h_disp = DRAINAGE_DATUM +
        h_depth), matching Script 03. This ensures the β₃ coefficient is on the
        same scale as the pipeline's headline fits.

        DESIGN NOTE: The extended model deliberately includes both P(t) and P(t-1)
        to absorb the generic vadose-zone lag that Script 22 demonstrated. Now
        that the headline model uses HEADLINE_LAG from config, an alternative
        would be to shift both terms accordingly. The current formulation
        (P(t) + P(t-1)) is retained pending a scientific review of whether
        the two-month spanning window serves the same absorb-the-generic-lag
        purpose regardless of the headline lag choice.
        See MODEL_SPECIFICATION_AUDIT.md, Scientific Question B.

Outputs:
    INT_23_RESIDUALS_WIDE      — cleaner residuals from the P(t)+P(t-1) model
    INT_23_FITS_TABLE          — per-well fits with b10, b11, alpha, R2, etc.
    OUT_23_CCF_HEADLINE        — CCFs overlaid for headline ridge wells
    OUT_23_LAG_VS_DISTANCE     — the KEY FIGURE: peak lag vs distance from ridge
    OUT_23_LAG_MAP             — spatial map of peak-correlation lag
    OUT_23_BETAS_BY_CLUSTER    — b10 vs b11 by cluster (diagnostic check)
    OUT_23_TEST_SUMMARY        — plain-text summary of the hypothesis test result

Ridge reference point: E = 241750, N = 364500 (OSGB36)
====================================================================================
"""

__version__ = "1.0.1"  # Hollingham (2026) — 2026-05-17
# 1.0.1 — Doc-sweep S.16: added prominent LIMITATION NOTE at top of
#         docstring documenting that the test design is statistically
#         degenerate against this dataset (monthly resolution cannot
#         resolve sub-monthly travel times; peak-lag is a poor CCF
#         summary; the 2.5% water-balance residual is at the noise floor
#         of per-well α uncertainty). Script retained for completeness;
#         results should not be cited. See §5.3 of main report and
#         §S.16 of Methods Supplement for final framing (S16-J).
#         Softened the "Script 22 demonstrated lag-1 rainfall signal at
#         every well" overstatement to "Script 22 documents AR(1)
#         persistence consistent with vadose-zone moisture memory" —
#         Script 22 tests residual-vs-own-past, not residual-vs-past-
#         rainfall, so the previous wording overstated what Script 22
#         actually shows (S16-C).  Fixed add_kml_features(ax) → 
#         add_kml_features(ax, DATA_DIR) bug — previously the KML
#         overlay silently failed inside the try/except, producing
#         maps without site features (S16-E).  Added __version__
#         (S16-H).  Patch — no functional change to numerical
#         outputs, KML overlays will now render on the lag-map figure.
# 1.0.x — Initial.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    INT_WELLS_CLEAN, INT_CLIMATE, INT_LOCATIONS, INT_CLUSTER_STATS,
    # New Script 23 paths — added to paths.py by accompanying patch:
    INT_23_RESIDUALS_WIDE, INT_23_FITS_TABLE,
    OUT_23_CCF_HEADLINE, OUT_23_LAG_VS_DISTANCE, OUT_23_LAG_MAP,
    OUT_23_BETAS_BY_CLUSTER, OUT_23_TEST_SUMMARY,
)
from utils.data_utils import normalize_well_name
from utils.map_utils import add_kml_features
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS, DRAINAGE_DATUM


# ==========================================
# CONFIGURATION
# ==========================================
MIN_MONTHS = 140
MAX_LAG    = 12

# Wells carried through from Script 22 (tidal, coastal-erosion, and upstream drops)
EXCLUDED_WELLS_NORM = {'ceh7', 'ceh8', 'ceh37', 'ceh3', 'ceh4'}

# Ridge reference point (OSGB36)
RIDGE_E = 241750.0
RIDGE_N = 364500.0

# Site extent filter to drop garbage coordinates (e.g. a 'pdfs' record at
# 300+ km from the site). Anything outside ~3 km of the ridge reference is
# not a real Newborough well.
MAX_RIDGE_DISTANCE_M = 3000.0

# CLUSTER_LABELS and CLUSTER_COLOURS imported from utils.config (k=5 partition).

# Wells highlighted in the headline CCF figure
HEADLINE_WELLS = ['ceh14', 'ceh34', 'ceh13', 'ceh2']

plt.rcParams.update({
    'font.family': 'sans-serif',
    'axes.labelsize': 12, 'axes.titlesize': 14,
    'xtick.labelsize': 10, 'ytick.labelsize': 10,
    'legend.fontsize': 10,
})


# ==========================================
# CORE COMPUTATION
# ==========================================

def ridge_distance(easting, northing):
    """Euclidean distance (m) from the ridge reference point."""
    return float(np.sqrt((easting - RIDGE_E) ** 2 + (northing - RIDGE_N) ** 2))


def fit_extended_model(well_series, climate,
                       drainage_datum=DRAINAGE_DATUM):
    """
    Fit the extended Model B:
        Delta_h(t) = alpha + b10*P(t) + b11*P(t-1)
                     - b2*PET(t) - b3*h_disp_prev(t)

    where h_disp_prev = DRAINAGE_DATUM + h_prev  (displacement formulation,
    matching Script 03).

    Including P(t-1) absorbs the generic vadose-zone lag that Script 22
    demonstrated contaminates the single-period SSM residuals everywhere.

    Returns dict with params and residual series, or None if the fit fails.
    """
    P_full = pd.to_numeric(climate['P_m'], errors='coerce')
    P_lag1 = P_full.shift(1)

    df = pd.DataFrame({
        'h':      pd.to_numeric(well_series, errors='coerce'),
        'P':      P_full,
        'P_lag1': P_lag1,
        'PET':    pd.to_numeric(climate['PET'], errors='coerce'),
    }).dropna()

    if len(df) < MIN_MONTHS:
        return None

    df['h_prev']  = df['h'].shift(1)
    df['Delta_h'] = df['h'] - df['h_prev']

    # Displacement above drainage datum for β₃ predictor
    df['h_disp_prev'] = drainage_datum + df['h_prev']

    df = df.dropna()

    if len(df) < MIN_MONTHS - 1:
        return None

    X = pd.DataFrame({
        'P':          df['P'].values,
        'P_lag1':     df['P_lag1'].values,
        'beta_2_atmospheric_draw': -df['PET'].values,
        'beta_3_drainage': -df['h_disp_prev'].values,
    }, index=df.index)
    X = sm.add_constant(X, has_constant='add')

    try:
        model = sm.OLS(df['Delta_h'].values, X).fit()
    except Exception:
        return None

    return {
        'alpha':   float(model.params['const']),
        'beta_10': float(model.params['P']),           # contemporaneous rainfall
        'beta_11': float(model.params['P_lag1']),      # one-month-lagged rainfall
        'beta_2':  float(model.params['beta_2_atmospheric_draw']),
        'beta_3':  float(model.params['beta_3_drainage']),  # positive = drainage increases with head
        'R2':      float(model.rsquared),
        'n':       int(len(df)),
        'resid':   pd.Series(model.resid, index=df.index, name='resid'),
        'pvalue_b11': float(model.pvalues['P_lag1']),
    }


def ar1_phi(x):
    """AR(1) coefficient via OLS."""
    x = pd.Series(x).dropna().values
    if len(x) < 30:
        return 0.0
    X = sm.add_constant(x[:-1])
    try:
        return float(sm.OLS(x[1:], X).fit().params[1])
    except Exception:
        return 0.0


def prewhiten(series, phi):
    """Apply filter y(t) = x(t) - phi*x(t-1)."""
    s = pd.Series(series)
    return s - phi * s.shift(1)


def crosscorr_at_lag(x, y, lag):
    """Pearson r between x(t) and y(t-lag). Series must share the same index."""
    y_lagged = y.shift(lag)
    merged = pd.DataFrame({'x': x, 'y': y_lagged}).dropna()
    if len(merged) < 30:
        return np.nan, len(merged)
    return float(np.corrcoef(merged['x'], merged['y'])[0, 1]), len(merged)


def compute_ccf(residual_pw, P_pw, max_lag=MAX_LAG):
    """Pre-whitened cross-correlation at lags 0..max_lag."""
    out = {}
    for lag in range(0, max_lag + 1):
        r, n = crosscorr_at_lag(residual_pw, P_pw, lag)
        out[f'r_lag{lag:02d}'] = r
        out[f'n_lag{lag:02d}'] = n
    return out


# ==========================================
# PLOTTING
# ==========================================

def plot_ccf_headline(ccf_df, output_path, sig_threshold):
    """Overlay CCF curves for the four headline ridge-adjacent wells."""
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)

    colours_headline = ['#D55E00', '#E69F00', '#CC79A7', '#009E73']
    for well, col in zip(HEADLINE_WELLS, colours_headline):
        row = ccf_df[ccf_df['Well_Normalized'] == well]
        if row.empty:
            continue
        r_vals = [row[f'r_lag{lag:02d}'].iloc[0] for lag in range(MAX_LAG + 1)]
        d = row['ridge_distance_m'].iloc[0]
        ax.plot(range(MAX_LAG + 1), r_vals, marker='o', lw=2.0,
                color=col, label=f"{well.upper()}  (d = {d:.0f} m from ridge)")

    ax.axhline(0, color='black', lw=0.8, ls='-', alpha=0.5)
    ax.axhspan(-sig_threshold, sig_threshold, color='grey', alpha=0.12,
               label=f'Bartlett 95% CI (|r| < {sig_threshold:.2f})')
    ax.set_xlabel('Lag N (months): correlation of residual(t) with P(t - N)')
    ax.set_ylabel('Pearson r (pre-whitened)')
    ax.set_title("Cross-correlation of extended-model residuals with past rainfall\n"
                 "Headline ridge-adjacent wells (after removing generic vadose-zone lag)",
                 fontweight='bold')
    ax.set_xticks(range(MAX_LAG + 1))
    ax.grid(ls='--', alpha=0.4)
    ax.legend(loc='upper right', frameon=True, edgecolor='black', fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


def plot_lag_vs_distance(ccf_df, output_path, sig_threshold, trend_stats):
    """
    The key hypothesis-test figure:
    x-axis = distance from ridge reference point
    y-axis = peak-correlation lag N*
    If ridge recharge has travel-time structure, a positive trend is expected.
    """
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)

    for cid, col in CLUSTER_COLOURS.items():
        sub = ccf_df[(ccf_df['Cluster'] == cid) & ccf_df['peak_significant']]
        if len(sub):
            ax.scatter(sub['ridge_distance_m'], sub['peak_lag'],
                       s=70 + 200 * sub['peak_r'].abs(),
                       color=col, edgecolor='black', linewidth=0.7,
                       alpha=0.85, zorder=3,
                       label=f"{CLUSTER_LABELS[cid]} (n={len(sub)})")

    # Non-significant wells (greyed out)
    sub_ns = ccf_df[~ccf_df['peak_significant']]
    if len(sub_ns):
        ax.scatter(sub_ns['ridge_distance_m'], sub_ns['peak_lag'],
                   s=35, color='lightgrey', edgecolor='grey', linewidth=0.4,
                   alpha=0.5, zorder=2,
                   label=f'No significant peak (n={len(sub_ns)})')

    # Label the key headline wells
    for target in HEADLINE_WELLS + ['nw10', 'nw1']:
        row = ccf_df[ccf_df['Well_Normalized'] == target]
        if not row.empty:
            ax.annotate(target.upper(),
                        xy=(row['ridge_distance_m'].iloc[0], row['peak_lag'].iloc[0]),
                        xytext=(6, 6), textcoords='offset points',
                        fontsize=8, fontweight='bold', zorder=5)

    ax.set_xlabel(f'Distance from ridge reference point ({RIDGE_E:.0f}, {RIDGE_N:.0f}) — metres')
    ax.set_ylabel('Peak-correlation lag N* (months)')
    ax.set_yticks(range(0, MAX_LAG + 1))
    ax.set_ylim(-0.5, MAX_LAG + 0.5)

    # Annotate the trend test result
    stats_text = (
        f"Spearman rho = {trend_stats['spearman_r']:+.3f}, p = {trend_stats['spearman_p']:.3f}\n"
        f"n = {trend_stats['n']} significant-peak wells"
    )
    verdict = ("TREND CONSISTENT WITH RIDGE TRANSPORT"
               if (trend_stats['spearman_r'] > 0 and trend_stats['spearman_p'] < 0.05)
               else "NO DISTANCE-LAG TREND (residual attribution not corroborated)")
    ax.text(0.02, 0.98, stats_text + "\n" + verdict,
            transform=ax.transAxes, va='top', ha='left',
            fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white',
                      edgecolor='black', alpha=0.9))

    ax.set_title('Hypothesis test: does peak lag increase with distance from ridge?',
                 fontweight='bold')
    ax.grid(ls='--', alpha=0.4)
    ax.legend(loc='center right', frameon=True, edgecolor='black', fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


def plot_lag_map(ccf_df, output_path):
    """Spatial map of peak-correlation lag."""
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)

    sig = ccf_df[ccf_df['peak_significant'] &
                 ccf_df['Easting'].notna() & ccf_df['Northing'].notna()]
    nsig = ccf_df[~ccf_df['peak_significant'] &
                  ccf_df['Easting'].notna() & ccf_df['Northing'].notna()]

    if len(nsig):
        ax.scatter(nsig['Easting'], nsig['Northing'],
                   s=35, color='lightgrey', edgecolor='grey', linewidth=0.4,
                   alpha=0.6, zorder=3, label=f'Not significant (n={len(nsig)})')

    if len(sig):
        sc = ax.scatter(sig['Easting'], sig['Northing'],
                        c=sig['peak_lag'], cmap='viridis',
                        vmin=0, vmax=MAX_LAG,
                        s=80 + 150 * sig['peak_r'].abs(),
                        edgecolor='black', linewidth=0.7, zorder=4,
                        label=f'Significant (n={len(sig)})')
        cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
        cbar.set_label('Peak lag N* (months)', fontsize=11)

    # Ridge reference point
    ax.scatter(RIDGE_E, RIDGE_N, marker='*', s=500, color='red',
               edgecolor='black', linewidth=1.2, zorder=5,
               label='Ridge reference')

    try:
        add_kml_features(ax, DATA_DIR)
    except Exception as e:
        print(f"  [note] KML overlay skipped: {e}")

    ax.set_xlabel('Easting (m, OSGB36)')
    ax.set_ylabel('Northing (m, OSGB36)')
    ax.set_title("Peak-correlation lag across the network\n"
                 "(after removing generic vadose-zone rainfall response)",
                 fontweight='bold')
    ax.set_aspect('equal')
    ax.grid(ls='--', alpha=0.4)
    ax.legend(loc='lower right', frameon=True, edgecolor='black', fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


def plot_betas_by_cluster(fits_df, output_path):
    """b10 vs b11 by cluster — diagnostic that the extended model is working."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    clusters_present = sorted(fits_df['Cluster'].dropna().unique())
    for cid in clusters_present:
        sub = fits_df[fits_df['Cluster'] == cid]
        col = CLUSTER_COLOURS.get(int(cid), '#777777')
        ax1.scatter(sub['beta_10'], sub['beta_11'],
                    color=col, s=60, edgecolor='black', linewidth=0.6,
                    label=f"{CLUSTER_LABELS.get(int(cid), f'C{int(cid)}')} (n={len(sub)})",
                    alpha=0.85)

    ax1.axhline(0, color='grey', lw=0.7, ls='--', alpha=0.6)
    ax1.axvline(0, color='grey', lw=0.7, ls='--', alpha=0.6)
    # Diagonal y = x
    lims = [min(fits_df['beta_10'].min(), fits_df['beta_11'].min()) - 0.1,
            max(fits_df['beta_10'].max(), fits_df['beta_11'].max()) + 0.1]
    ax1.plot(lims, lims, color='grey', lw=0.7, ls=':', alpha=0.7, label='y = x')
    ax1.set_xlabel('beta_10 (response to P(t))')
    ax1.set_ylabel('beta_11 (response to P(t-1))')
    ax1.set_title('Contemporaneous vs lagged rainfall coefficients', fontweight='bold')
    ax1.grid(ls='--', alpha=0.4)
    ax1.legend(loc='best', frameon=True, edgecolor='black', fontsize=9)

    # Bar chart of b11/(b10+b11) ratio by cluster — fraction of response that is lagged
    ratios = []
    for cid in clusters_present:
        sub = fits_df[fits_df['Cluster'] == cid]
        if (sub['beta_10'] + sub['beta_11']).abs().sum() > 0:
            # Use cluster-mean ratio
            total = sub['beta_10'].mean() + sub['beta_11'].mean()
            ratio = sub['beta_11'].mean() / total if total > 0 else np.nan
            ratios.append((cid, ratio, len(sub)))

    if ratios:
        cids = [r[0] for r in ratios]
        vals = [r[1] for r in ratios]
        ns   = [r[2] for r in ratios]
        colours = [CLUSTER_COLOURS.get(int(c), '#777777') for c in cids]
        labels = [f"{CLUSTER_LABELS.get(int(c), f'C{int(c)}')}\n(n={n})" for c, n in zip(cids, ns)]
        ax2.bar(labels, vals, color=colours, edgecolor='black', linewidth=0.8)
        ax2.axhline(0.5, color='grey', lw=0.8, ls='--', alpha=0.6,
                    label='50/50 split')
        ax2.set_ylabel('Mean b11 / (b10 + b11)')
        ax2.set_title('Fraction of rainfall response that is lagged (by cluster)',
                      fontweight='bold')
        ax2.grid(axis='y', ls='--', alpha=0.4)
        ax2.legend(loc='best', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


# ==========================================
# HYPOTHESIS TEST SUMMARY
# ==========================================

def write_test_summary(ccf_df, fits_df, trend_stats, output_path):
    """Plain-text summary of the hypothesis test."""
    from scipy import stats as scipy_stats

    sig = ccf_df[ccf_df['peak_significant']]

    lines = []
    lines.append("=" * 78)
    lines.append("  RIDGE-RECHARGE LAG HYPOTHESIS TEST — SUMMARY")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"  Ridge reference point: E = {RIDGE_E:.0f}, N = {RIDGE_N:.0f} (OSGB36)")
    lines.append(f"  Analysis model: Delta_h = alpha + b10*P(t) + b11*P(t-1)"
                 f" - b2*PET(t) - b3*h_disp_prev(t)")
    lines.append(f"  Displacement formulation: h_disp = {DRAINAGE_DATUM} + h_depth")
    lines.append(f"  Wells analysed: {len(fits_df)} with n >= {MIN_MONTHS} months")
    lines.append(f"  Excluded: {sorted(EXCLUDED_WELLS_NORM)}")
    lines.append("")
    lines.append("-" * 78)
    lines.append("  HYPOTHESIS")
    lines.append("-" * 78)
    lines.append("  H1: If the water-balance residual reflects genuine lateral recharge from")
    lines.append("      the northern rock ridge, then the peak-correlation lag N* between")
    lines.append("      extended-model residuals and rainfall should increase with distance")
    lines.append("      from the ridge (longer travel time = longer lag).")
    lines.append("")
    lines.append("  H0: If the residual is model error rather than ridge recharge, no such")
    lines.append("      distance-lag relationship will exist.")
    lines.append("")
    lines.append("-" * 78)
    lines.append("  RESULT")
    lines.append("-" * 78)
    lines.append(f"  Spearman rank correlation of peak lag vs ridge distance:")
    lines.append(f"     rho = {trend_stats['spearman_r']:+.4f}")
    lines.append(f"     p   = {trend_stats['spearman_p']:.4f}")
    lines.append(f"     n   = {trend_stats['n']} wells with significant peak")
    lines.append("")
    lines.append(f"  Mean peak lag (all sig wells):      {sig['peak_lag'].mean():.2f} months")
    lines.append(f"  Median peak lag (all sig wells):    {sig['peak_lag'].median():.1f} months")
    lines.append(f"  Peak lag standard deviation:        {sig['peak_lag'].std():.2f} months")
    lines.append("")
    lines.append("  By cluster (significant wells only):")
    if len(sig):
        for cid in sorted(sig['Cluster'].dropna().unique()):
            sub = sig[sig['Cluster'] == cid]
            label = CLUSTER_LABELS.get(int(cid), f'C{int(cid)}')
            lines.append(f"     {label:15s} n={len(sub):2d}  mean lag = {sub['peak_lag'].mean():.2f}  "
                         f"mean |r| = {sub['peak_r'].abs().mean():.3f}")
    lines.append("")
    lines.append("-" * 78)
    lines.append("  INTERPRETATION")
    lines.append("-" * 78)
    if trend_stats['spearman_r'] > 0 and trend_stats['spearman_p'] < 0.05:
        lines.append("  H1 SUPPORTED: peak lag increases significantly with ridge distance.")
        lines.append("  The residual behaves as ridge-derived lateral recharge would behave")
        lines.append("  on first-principles hydrogeology. Ridge-recharge attribution corroborated.")
    elif trend_stats['spearman_p'] < 0.05 and trend_stats['spearman_r'] < 0:
        lines.append("  UNEXPECTED RESULT: peak lag DECREASES with ridge distance. This is")
        lines.append("  inconsistent with the physical ridge-transport hypothesis and requires")
        lines.append("  further investigation before any interpretation is offered.")
    else:
        lines.append("  H0 NOT REJECTED: no significant distance-lag relationship detected.")
        lines.append("  The water-balance residual cannot be attributed to ridge-derived recharge")
        lines.append("  on lag-structure evidence. Either (a) the residual is largely model error")
        lines.append("  and should be reported as such, or (b) ridge recharge is delivered via a")
        lines.append("  mechanism that does not produce a month-scale distance-dependent lag")
        lines.append("  (e.g. a near-steady baseflow that is effectively smoothed in time by the")
        lines.append("  time it reaches the dune field).")
        lines.append("")
        lines.append("  Path (b) is not ruled out by a null result here; but it also cannot be")
        lines.append("  claimed from these data alone, because a steady baseflow is")
        lines.append("  observationally indistinguishable from a constant alpha, which is already")
        lines.append("  what Model B absorbs.")
    lines.append("")
    lines.append("=" * 78)

    output_path.write_text("\n".join(lines))
    print(f" -> Saved: {output_path.name}")
    # Also echo to stdout
    print("\n" + "\n".join(lines))


# ==========================================
# MAIN
# ==========================================

def main():
    from scipy import stats as scipy_stats
    make_all_dirs()
    print("Starting 23: Ridge-recharge lag hypothesis test...")

    wells      = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    climate    = pd.read_csv(INT_CLIMATE,    index_col=0, parse_dates=True)
    locations  = pd.read_csv(INT_LOCATIONS)
    cluster_df = pd.read_csv(INT_CLUSTER_STATS)

    cluster_df['_norm'] = cluster_df['Match_ID'].apply(normalize_well_name)
    cluster_lookup = dict(zip(cluster_df['_norm'], cluster_df['Cluster']))

    locations['_norm'] = locations['Name'].apply(normalize_well_name)
    coords_lookup = {r['_norm']: (r['E'], r['N']) for _, r in locations.iterrows()}

    # Pre-whiten rainfall once
    P = pd.to_numeric(climate['P_m'], errors='coerce')
    phi_P = ar1_phi(P)
    P_pw = prewhiten(P, phi_P)
    print(f" -> Rainfall AR(1) phi = {phi_P:+.3f}; pre-whitened series built.")

    # Fit extended model and compute CCFs
    candidate_wells = [c for c in wells.columns
                       if normalize_well_name(c) not in EXCLUDED_WELLS_NORM]
    print(f" -> Candidate wells: {len(candidate_wells)} "
          f"(excluded: {sorted(EXCLUDED_WELLS_NORM)})")

    fit_rows = []
    ccf_rows = []
    residuals_dict = {}

    for well_col in candidate_wells:
        norm = normalize_well_name(well_col)
        coords = coords_lookup.get(norm, (np.nan, np.nan))

        # Drop nonsense coords
        if pd.isna(coords[0]):
            continue
        d_ridge = ridge_distance(coords[0], coords[1])
        if d_ridge > MAX_RIDGE_DISTANCE_M:
            continue

        result = fit_extended_model(wells[well_col], climate)
        if result is None:
            continue

        residuals_dict[norm] = result['resid']

        fit_rows.append({
            'Well':            well_col,
            'Well_Normalized': norm,
            'Cluster':         cluster_lookup.get(norm, np.nan),
            'Easting':         coords[0],
            'Northing':        coords[1],
            'ridge_distance_m': d_ridge,
            'n':               result['n'],
            'alpha':           result['alpha'],
            'beta_10':         result['beta_10'],
            'beta_11':         result['beta_11'],
            'beta_2':          result['beta_2'],
            'beta_3':          result['beta_3'],
            'R2':              result['R2'],
            'pvalue_b11':      result['pvalue_b11'],
        })

        # Pre-whitened residual
        phi_resid = ar1_phi(result['resid'])
        resid_pw = prewhiten(result['resid'], phi_P)
        # If residual itself is strongly autocorrelated, apply additional pre-whitening
        if abs(phi_resid) >= 0.2:
            resid_pw = prewhiten(result['resid'] - phi_resid * result['resid'].shift(1), phi_P)

        ccf = compute_ccf(resid_pw, P_pw)
        # Peak lag and significance
        r_vals = np.array([ccf[f'r_lag{lag:02d}'] for lag in range(MAX_LAG + 1)])
        # Bartlett CI using the smallest n across the computed lags
        n_eff = min(ccf[f'n_lag{lag:02d}'] for lag in range(MAX_LAG + 1))
        sig_threshold = 1.96 / np.sqrt(max(n_eff, 30))

        peak_lag = int(np.nanargmax(np.abs(r_vals)))
        peak_r   = float(r_vals[peak_lag])
        peak_sig = abs(peak_r) >= sig_threshold

        ccf_rows.append({
            'Well_Normalized':   norm,
            'Cluster':           cluster_lookup.get(norm, np.nan),
            'Easting':           coords[0],
            'Northing':          coords[1],
            'ridge_distance_m':  d_ridge,
            'phi_resid':         phi_resid,
            'peak_lag':          peak_lag,
            'peak_r':            peak_r,
            'peak_significant':  peak_sig,
            'sig_threshold':     sig_threshold,
            **{f'r_lag{lag:02d}': ccf[f'r_lag{lag:02d}'] for lag in range(MAX_LAG + 1)},
        })

    fits_df = pd.DataFrame(fit_rows)
    ccf_df  = pd.DataFrame(ccf_rows)
    print(f" -> Extended-model fit + CCF for {len(fits_df)} wells.")

    # Save intermediates
    residuals_wide = pd.DataFrame(residuals_dict).sort_index()
    residuals_wide.to_csv(INT_23_RESIDUALS_WIDE)
    print(f" -> Saved: {INT_23_RESIDUALS_WIDE.name}")

    merged = fits_df.merge(ccf_df[['Well_Normalized', 'phi_resid', 'peak_lag',
                                   'peak_r', 'peak_significant', 'sig_threshold']],
                           on='Well_Normalized', how='left')
    merged.to_csv(INT_23_FITS_TABLE, index=False)
    print(f" -> Saved: {INT_23_FITS_TABLE.name}")

    # ------ Hypothesis test: Spearman rho of peak lag vs ridge distance ------
    sig = ccf_df[ccf_df['peak_significant']]
    if len(sig) >= 5:
        rho, p = scipy_stats.spearmanr(sig['ridge_distance_m'], sig['peak_lag'])
        trend_stats = {'spearman_r': float(rho), 'spearman_p': float(p), 'n': int(len(sig))}
    else:
        trend_stats = {'spearman_r': np.nan, 'spearman_p': np.nan, 'n': int(len(sig))}

    # Mean threshold for the headline plot
    mean_sig_threshold = float(ccf_df['sig_threshold'].mean())

    # Plots
    plot_ccf_headline(ccf_df, OUT_23_CCF_HEADLINE, mean_sig_threshold)
    plot_lag_vs_distance(ccf_df, OUT_23_LAG_VS_DISTANCE, mean_sig_threshold, trend_stats)
    plot_lag_map(ccf_df, OUT_23_LAG_MAP)
    plot_betas_by_cluster(fits_df, OUT_23_BETAS_BY_CLUSTER)

    # Summary
    write_test_summary(ccf_df, fits_df, trend_stats, OUT_23_TEST_SUMMARY)

    print("\n23 complete.")


if __name__ == "__main__":
    main()
