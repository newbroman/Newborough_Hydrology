"""
====================================================================================
22_residual_lag_analysis.py — SSM Residuals, AR(1) Diagnostics, and Alpha-Phi Scatter
====================================================================================
Purpose:
    Stage 1 of the ridge-subsidy lag analysis (see Section 11 further work).

    Refits Model B (SSM with intercept, contemporaneous rainfall under
    HEADLINE_LAG = 0, displacement formulation) for every reference well
    with >= 140 months of data on the FULL record, then:
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
    INT_22_SSM_RESID_INFERENCE — per-well headline (Model A) residual-inference
                               diagnostics for the 66-well reference network:
                               Durbin–Watson, lag-1 φ, Ljung–Box(12), and
                               OLS-vs-HAC (Newey–West) coefficient p-values.
    INT_22_SSM_CLUSTER_INFERENCE — same battery applied to the five cluster
                               centroids that carry the headline β table (Report
                               Table 3): per-cluster DW, φ, Ljung–Box, OLS-vs-HAC.

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

__version__ = "1.2.0"  # Hollingham (2026) — 2026-07-21
# 1.2.0 (2026-07-21): added the headline Model A residual-inference diagnostic
#   (ssm_residual_inference) for the 66-well reference network — the committed
#   artefact backing the SI's OLS-inference-validity statement. For each
#   reference well it fits the upstand-corrected no-intercept SSM (full record),
#   tests residual serial correlation (Durbin–Watson, lag-1 φ, Ljung–Box) and
#   re-estimates coefficient p-values with Newey–West/HAC standard errors
#   (n-adaptive rule-of-thumb lag). Writes 22_05_ssm_residual_autocorrelation.csv
#   with the per-well diagnostics and OLS-vs-HAC p-values; the headline stat is
#   the count of coefficient significance verdicts that change under HAC. A
#   companion function (cluster_mean_residual_inference) applies the same battery
#   to the five upstand-corrected cluster centroids that carry the headline β
#   table (Report Table 3 / Paper 1 Table 1), reproducing 03_03's centroid β and
#   OLS p-values exactly and writing 22_06_ssm_cluster_mean_inference.csv. Does
#   not touch the existing Model B AR(1) analysis.
# 1.1.0 (2026-06-21) — iterate CLUSTER_LABELS not CLUSTER_COLOURS.items() — drop reserved C6 from cluster loops; no functional change, C6 was already len-guarded
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
# 1.0.1 — Doc-sweep S.16: corrected stale "lag-1 rainfall" docstring claim
#         to "contemporaneous rainfall under HEADLINE_LAG = 0" (S16-A);
#         clarified the inline comment on lag/displacement handling (S16-B);
#         added __version__ (S16-G).  Patch — no functional change.
# 1.0.x — Initial.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.paths import (
    make_all_dirs, DATA_DIR, INT_WELLS_CLEAN, INT_CLIMATE, INT_LOCATIONS,
    INT_CLUSTER_STATS, INT_22_RESIDUALS_WIDE, INT_22_FITS_TABLE,
    OUT_22_AR1_HIST, OUT_22_AR1_MAP, OUT_22_ALPHA_PHI_SCATTER,
    OUT_22_EXAMPLE_SERIES,
    INT_WELLS_REFERENCE, INT_WELL_ELEVATIONS, INT_22_SSM_RESID_INFERENCE,
    INT_22_SSM_CLUSTER_INFERENCE,
)
from utils.data_utils import normalize_well_name
from utils.map_utils import add_kml_features, add_en_axes
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS, HEADLINE_LAG
from utils.model_utils import fit_ssm_intercept, build_ssm_frame, MIN_OBS
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.diagnostic import acorr_ljungbox

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import render_figure


# ==========================================
# CONFIGURATION
# ==========================================
MIN_MONTHS = 140
AR1_WHITE_THRESHOLD = 0.3  # |phi| below this is treated as effectively white
AR1_DIAG_PVAL = 0.05

# Lag and displacement handled by fit_ssm_intercept() from model_utils:
# - rainfall is contemporaneous (HEADLINE_LAG = 0 in config.py)
# - drainage uses h_disp_prev (end-of-previous-month displacement above datum)

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

    for cid in CLUSTER_LABELS:
        col = CLUSTER_COLOURS[cid]
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
    render_figure(plt.gcf(), output_path)
    plt.close()
    saved(f"{output_path.name}")


def plot_ar1_map(fits_df, output_path):
    """Spatial map of AR(1) coefficient per well."""
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    valid = fits_df.dropna(subset=['Easting', 'Northing', 'ar1_phi'])
    if valid.empty:
        step("Skipped AR(1) map (no valid coordinates).")
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
        add_kml_features(ax, DATA_DIR)
    except Exception as e:
        note(f"KML overlay skipped: {e}")

    ax.set_title('Residual autocorrelation across the network\n'
                 f"(wells with |phi| >= {AR1_WHITE_THRESHOLD} need pre-whitening "
                 'before lag analysis)',
                 fontweight='bold')
    add_en_axes(ax)
    ax.grid(ls='--', alpha=0.4)
    plt.tight_layout()
    render_figure(plt.gcf(), output_path)
    plt.close()
    saved(f"{output_path.name}")


def plot_alpha_phi_scatter(fits_df, output_path):
    """Scatter of intercept alpha vs residual AR(1) coefficient."""
    fig, ax = plt.subplots(figsize=(9, 7), dpi=300)
    valid = fits_df.dropna(subset=['alpha', 'ar1_phi'])

    for cid in CLUSTER_LABELS:
        col = CLUSTER_COLOURS[cid]
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
    render_figure(plt.gcf(), output_path)
    plt.close()
    saved(f"{output_path.name}")


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
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    axes[-1].set_xlabel('Date')
    fig.suptitle('Example SSM Model B residuals by cluster\n'
                 '(constant part absorbed by alpha; shown series is time-varying part only)',
                 fontweight='bold', y=1.00)
    plt.tight_layout()
    render_figure(plt.gcf(), output_path)
    plt.close()
    saved(f"{output_path.name}")


# ==========================================
# MAIN
# ==========================================

# ──────────────────────────────────────────────────────────────────────────────
# HEADLINE MODEL A RESIDUAL-INFERENCE DIAGNOSTIC (reference network)
# ──────────────────────────────────────────────────────────────────────────────
# The published β₁/β₂/β₃ table is produced by ordinary least squares with
# classical (non-robust) standard errors. For a monthly time-series regression a
# reviewer will rightly ask whether those standard errors are valid under serial
# correlation. This block answers with a committed artefact: for every reference
# well it fits the headline SSM (no-intercept, displacement formulation,
# upstand-corrected — the same physical specification as Script 03), tests the
# residuals for autocorrelation (Durbin–Watson, lag-1 φ, Ljung–Box), and
# re-estimates the coefficient p-values with heteroskedasticity- and
# autocorrelation-consistent (Newey–West / HAC) standard errors. The HAC lag is
# the n-adaptive rule-of-thumb L = ⌊4·(n/100)^(2/9)⌋. The headline result is the
# number of coefficient significance verdicts (α = 0.05) that change between OLS
# and HAC across the network — near zero confirms the OLS inference is sound.

def _newey_west_lag(n: int) -> int:
    """Rule-of-thumb HAC truncation lag ⌊4·(n/100)^(2/9)⌋ (minimum 1)."""
    return max(1, int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0))))


def _upstand_lookup(elev_path):
    """Return {col_norm: upstand_m}, keyed to match reference-well column names,
    mirroring Script 03's build_upstand_lookup + col_norm convention so the
    residuals reproduce the published per-well displacement fits."""
    lookup = {}
    if not elev_path.exists():
        warn("Elevation file not found — upstand correction skipped.")
        return lookup
    elev_df = pd.read_csv(elev_path)
    elev_df.columns = [c.strip() for c in elev_df.columns]
    if "Name_norm" in elev_df.columns and "Upstand_m" in elev_df.columns:
        for _, row in elev_df.iterrows():
            if pd.notna(row.get("Upstand_m")):
                key = str(row["Name_norm"]).lower().replace(" ", "").replace("_", "")
                lookup[key] = float(row["Upstand_m"])
    return lookup


def ssm_residual_inference(climate, cluster_lookup):
    """Reference-network residual-inference diagnostic for the headline
    (no-intercept, Model A) SSM. Writes INT_22_SSM_RESID_INFERENCE and returns a
    summary dict. See the block comment above for method and rationale."""
    step("Model A residual-inference diagnostic (reference network, HAC robustness)")
    ref = pd.read_csv(INT_WELLS_REFERENCE, index_col=0, parse_dates=True)
    upstand = _upstand_lookup(INT_WELL_ELEVATIONS)

    rows = []
    for well in ref.columns:
        norm = normalize_well_name(well)
        col_norm = norm.lower().replace(" ", "").replace("_", "")
        u = upstand.get(col_norm, 0.0)
        series = pd.to_numeric(ref[well], errors="coerce").dropna() - u
        frame = build_ssm_frame(series, climate, lag=HEADLINE_LAG)
        if frame is None or len(frame) < MIN_OBS:
            continue
        y = frame["Delta_h"].values
        X = pd.DataFrame({
            "beta_1_recharge":         frame["P"].values,
            "beta_2_atmospheric_draw": -frame["PET"].values,
            "beta_3_drainage":         -frame["h_disp_prev"].values,
        }, index=frame.index)
        ols = sm.OLS(y, X).fit()
        lag = _newey_west_lag(len(y))
        hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
        resid = pd.Series(ols.resid, index=frame.index)
        n_flip = sum((ols.pvalues[c] < 0.05) != (hac.pvalues[c] < 0.05)
                     for c in X.columns)
        rows.append({
            "Well":            well,
            "Well_Normalized": norm,
            "Cluster":         cluster_lookup.get(norm, np.nan),
            "n":               int(len(y)),
            "R2":              float(ols.rsquared),
            "durbin_watson":   float(durbin_watson(resid.values)),
            "ar1_phi":         float(resid.autocorr(lag=1)),
            "ljungbox12_p":    float(acorr_ljungbox(resid, lags=[12],
                                     return_df=True)["lb_pvalue"].iloc[0]),
            "hac_maxlag":      int(lag),
            "p_beta_1_ols":    float(ols.pvalues["beta_1_recharge"]),
            "p_beta_1_hac":    float(hac.pvalues["beta_1_recharge"]),
            "p_beta_2_ols":    float(ols.pvalues["beta_2_atmospheric_draw"]),
            "p_beta_2_hac":    float(hac.pvalues["beta_2_atmospheric_draw"]),
            "p_beta_3_ols":    float(ols.pvalues["beta_3_drainage"]),
            "p_beta_3_hac":    float(hac.pvalues["beta_3_drainage"]),
            "sig_flips_hac":   int(n_flip),
        })

    df = pd.DataFrame(rows)
    df.to_csv(INT_22_SSM_RESID_INFERENCE, index=False)
    saved(f"{INT_22_SSM_RESID_INFERENCE.name}")

    dw = df["durbin_watson"]; phi = df["ar1_phi"]
    summary = {
        "n_wells":         len(df),
        "dw_median":       float(dw.median()),
        "dw_iqr":          (float(dw.quantile(.25)), float(dw.quantile(.75))),
        "phi_median":      float(phi.median()),
        "ljungbox_reject": int((df["ljungbox12_p"] < 0.05).sum()),
        "sig_flips":       int(df["sig_flips_hac"].sum()),
        "n_coeff_tests":   3 * len(df),
    }
    print("\n" + "=" * 62)
    print("  MODEL A RESIDUAL-INFERENCE SUMMARY (reference network)")
    print("=" * 62)
    print(f"  Wells fitted:                  {summary['n_wells']}")
    print(f"  Durbin-Watson median:          {summary['dw_median']:.2f} "
          f"(IQR {summary['dw_iqr'][0]:.2f}-{summary['dw_iqr'][1]:.2f})")
    print(f"  AR(1) phi median:              {summary['phi_median']:+.3f}")
    print(f"  Ljung-Box(12) reject p<0.05:   {summary['ljungbox_reject']} / {summary['n_wells']}")
    print(f"  Coeff significance flips HAC:  {summary['sig_flips']} / {summary['n_coeff_tests']}")
    print("=" * 62)
    return summary


def cluster_mean_residual_inference(wells, climate, cluster_df):
    """Cluster-mean (centroid) residual-inference diagnostic — the HAC robustness
    check for the *headline* β table (Report Table 3 / Paper 1 Table 1). Rebuilds
    each cluster's upstand-corrected centroid exactly as Script 03's
    build_cluster_centroids does, fits the headline no-intercept SSM (full record),
    and applies the same Durbin–Watson / lag-1 φ / Ljung–Box / OLS-vs-HAC battery
    as the per-well diagnostic. Writes INT_22_SSM_CLUSTER_INFERENCE and returns a
    summary dict. The centroid β and OLS p-values reproduce
    03_03_cluster_mechanistic_coefficients.csv exactly, so the HAC comparison is
    against the published headline coefficients."""
    step("Cluster-mean residual-inference diagnostic (headline β table, HAC robustness)")
    upstand = _upstand_lookup(INT_WELL_ELEVATIONS)
    well_col = {normalize_well_name(c): c for c in wells.columns}

    rows = []
    cids = sorted(pd.to_numeric(cluster_df["Cluster"], errors="coerce")
                  .dropna().astype(int).unique())
    for cid in cids:
        members = cluster_df[
            pd.to_numeric(cluster_df["Cluster"], errors="coerce") == cid
        ]["Match_ID"].astype(str).values
        cols = [well_col.get(normalize_well_name(w)) for w in members]
        cols = [c for c in cols if c is not None]
        if not cols:
            continue
        # Upstand-corrected centroid — identical to Script 03 build_cluster_centroids
        corrected = {}
        for col in cols:
            key = normalize_well_name(col).lower().replace(" ", "").replace("_", "")
            u = upstand.get(key)
            corrected[col] = wells[col] - u if u is not None else wells[col]
        centroid = pd.DataFrame(corrected).mean(axis=1)

        frame = build_ssm_frame(centroid, climate, lag=HEADLINE_LAG)
        if frame is None or len(frame) < MIN_OBS:
            continue
        y = frame["Delta_h"].values
        X = pd.DataFrame({
            "beta_1_recharge":         frame["P"].values,
            "beta_2_atmospheric_draw": -frame["PET"].values,
            "beta_3_drainage":         -frame["h_disp_prev"].values,
        }, index=frame.index)
        ols = sm.OLS(y, X).fit()
        lag = _newey_west_lag(len(y))
        hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
        resid = pd.Series(ols.resid, index=frame.index)
        n_flip = sum((ols.pvalues[c] < 0.05) != (hac.pvalues[c] < 0.05)
                     for c in X.columns)
        rows.append({
            "Cluster":        int(cid),
            "Cluster_Label":  CLUSTER_LABELS.get(cid, f"C{cid}"),
            "n_members":      len(cols),
            "n":              int(len(y)),
            "R2":             float(ols.rsquared),
            "durbin_watson":  float(durbin_watson(resid.values)),
            "ar1_phi":        float(resid.autocorr(lag=1)),
            "ljungbox12_p":   float(acorr_ljungbox(resid, lags=[12],
                                    return_df=True)["lb_pvalue"].iloc[0]),
            "hac_maxlag":     int(lag),
            "p_beta_1_ols":   float(ols.pvalues["beta_1_recharge"]),
            "p_beta_1_hac":   float(hac.pvalues["beta_1_recharge"]),
            "p_beta_2_ols":   float(ols.pvalues["beta_2_atmospheric_draw"]),
            "p_beta_2_hac":   float(hac.pvalues["beta_2_atmospheric_draw"]),
            "p_beta_3_ols":   float(ols.pvalues["beta_3_drainage"]),
            "p_beta_3_hac":   float(hac.pvalues["beta_3_drainage"]),
            "sig_flips_hac":  int(n_flip),
        })

    df = pd.DataFrame(rows)
    df.to_csv(INT_22_SSM_CLUSTER_INFERENCE, index=False)
    saved(f"{INT_22_SSM_CLUSTER_INFERENCE.name}")

    total_flips = int(df["sig_flips_hac"].sum())
    n_tests = 3 * len(df)
    print("\n" + "=" * 62)
    print("  CLUSTER-MEAN RESIDUAL-INFERENCE SUMMARY (headline β table)")
    print("=" * 62)
    for _, r in df.iterrows():
        print(f"  {r['Cluster_Label']:<22s} DW {r['durbin_watson']:.2f}  "
              f"phi {r['ar1_phi']:+.3f}  flips {int(r['sig_flips_hac'])}")
    print(f"  Coeff significance flips HAC:  {total_flips} / {n_tests}")
    print("=" * 62)
    return {"n_clusters": len(df), "sig_flips": total_flips, "n_coeff_tests": n_tests}


def main():
    banner("22", "Residual Lag Analysis", version=__version__)
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
            'beta_1_recharge':          result['beta_1_recharge'],
            'beta_2_atmospheric_draw':  result['beta_2_atmospheric_draw'],
            'beta_3_drainage':          result['beta_3_drainage'],
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
        step("No residuals to save (all wells filtered out).")
        return

    residuals_wide = pd.DataFrame(residuals_dict).sort_index()
    residuals_wide.to_csv(INT_22_RESIDUALS_WIDE)
    print(f" -> Saved: {INT_22_RESIDUALS_WIDE.name} "
          f"({residuals_wide.shape[0]} months x {residuals_wide.shape[1]} wells)")

    fits_df.to_csv(INT_22_FITS_TABLE, index=False)
    saved(f"{INT_22_FITS_TABLE.name}")

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

    # Headline Model A residual-inference diagnostic (reference network) —
    # committed HAC-robustness artefact for the SI reproducibility statement.
    ssm_residual_inference(climate, cluster_lookup)
    cluster_mean_residual_inference(wells, climate, cluster_df)

    # Plots
    plot_ar1_hist(fits_df, OUT_22_AR1_HIST)
    plot_ar1_map(fits_df, OUT_22_AR1_MAP)
    plot_alpha_phi_scatter(fits_df, OUT_22_ALPHA_PHI_SCATTER)
    plot_example_residuals(residuals_wide, fits_df, OUT_22_EXAMPLE_SERIES)

    print("\n22 complete. Next: cross-correlation stage (22b).")


if __name__ == "__main__":
    main()
