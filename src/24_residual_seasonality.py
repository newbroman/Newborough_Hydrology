"""
====================================================================================
24_residual_seasonality.py — Seasonal Climatology Diagnostic for SSM Residuals
====================================================================================
Purpose:
    Independent diagnostic test of whether the SSM residuals carry a
    systematic seasonal signature that would indicate the Thornthwaite PET
    estimate is misrepresenting summer atmospheric demand, or alternatively
    that the ridge-subsidy component is delivered as a flat year-round baseflow.

    Companion to Script 23 (ridge-transport lag test). Both scripts are
    standalone analytical companions to the main pipeline, not part of the
    01-21 canonical sequence. Their outputs feed into Supplementary Note S6.

    Test logic:
        If the residual is pure steady ridge baseflow, the monthly climatology
        of ε(t) should be approximately flat — similar magnitude in every
        month.

        If the residual is pure unmodelled summer ET, ε(t) should be
        systematically negative in summer (JJA) and approximately zero in
        winter (DJF).

        If mixed, we would expect a year-round offset plus an additional
        summer-heavy negative excursion.

    Phase of the seasonal fit distinguishes two failure modes for Thornthwaite:
        phase ~ July/August => proportional underestimation (right shape, wrong
                               amplitude)
        phase ~ May/June    => biased seasonality (temperature-driven estimate
                               lags the true radiation-driven peak)

Outputs:
    INT_24_CLIMATOLOGY_TABLE   — per-well seasonal summary CSV
    OUT_24_CLIMATOLOGY_PANELS  — per-cluster mean climatology with per-well overlays
    OUT_24_AMPLITUDE_MAP       — spatial map of seasonal amplitude per well
    OUT_24_SUN_CORR_SCATTER    — sunshine-hours-vs-residual scatter
    OUT_24_PHASE_BARPLOT       — phase month by cluster
    OUT_24_SUMMARY             — plain-text interpretive summary

Note on the sunshine-hours diagnostic:
    A naive correlation of residual against PET would be zero by construction,
    because OLS fits make residuals orthogonal to every regressor. To test
    whether real ET departs from the Thornthwaite estimate in a way that the
    fitted b2 has not absorbed, we correlate the residual against monthly
    SUNSHINE HOURS instead — an independent radiation-based proxy that is not
    in the regression. A systematic negative correlation would indicate that
    high-insolation months carry extra ET losses that Thornthwaite (temperature-
    only) has not captured and b2 has therefore not fitted.

Ridge reference point (inherited from Script 23): E = 241750, N = 364500 (OSGB36)
C3 split threshold: 1000 m from ridge (forest-adjacent vs warren-interior)
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as scipy_stats

from utils.paths import (
    make_all_dirs,
    INT_WELLS_CLEAN, INT_CLIMATE, INT_LOCATIONS, INT_CLUSTER_STATS,
    DATA_CLIMATE_RAW,
    # New Script 24 paths — added to paths.py by accompanying patch:
    INT_24_CLIMATOLOGY_TABLE,
    OUT_24_CLIMATOLOGY_PANELS, OUT_24_AMPLITUDE_MAP,
    OUT_24_SUN_CORR_SCATTER, OUT_24_PHASE_BARPLOT,
    OUT_24_SUMMARY,
)
from utils.data_utils import normalize_well_name
from utils.map_utils import add_kml_features
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS
from utils.model_utils import fit_ssm_intercept


# ==========================================
# CONFIGURATION
# ==========================================
MIN_MONTHS = 140
EXCLUDED_WELLS_NORM = {'ceh7', 'ceh8', 'ceh37', 'ceh3', 'ceh4'}
RIDGE_E = 241750.0
RIDGE_N = 364500.0
MAX_RIDGE_DISTANCE_M = 3000.0
C3_SPLIT_DISTANCE_M = 1000.0  # legacy: under the new partition the forest-adjacent
                              # subset of the old C3 has been split out as C5
                              # (Coastal Forest); this constant retains a within-
                              # cluster diagnostic on the new C3 (Western Residual).

# CLUSTER_LABELS and CLUSTER_COLOURS imported from utils.config (k=5 partition).

# Lag and displacement handled by fit_ssm_intercept() from model_utils.
MONTH_LABELS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

plt.rcParams.update({
    'font.family': 'sans-serif',
    'axes.labelsize': 12, 'axes.titlesize': 14,
    'xtick.labelsize': 10, 'ytick.labelsize': 10,
    'legend.fontsize': 10,
})


# ==========================================
# CORE COMPUTATION
# ==========================================

def fit_ssm_residual(well_series, climate):
    """Fit SSM via shared model_utils, return residual Series or None."""
    result = fit_ssm_intercept(well_series, climate, min_obs=MIN_MONTHS)
    if result is None:
        return None
    return result['resid']


def sinusoidal_fit(monthly_means):
    """
    Fit y = a0 + a1*cos(2*pi*m/12) + a2*sin(2*pi*m/12) to 12 monthly means.
    Returns: offset a0, amplitude sqrt(a1^2+a2^2), phase (month of peak),
    residual std.
    """
    m = np.arange(1, 13)
    y = monthly_means.values
    mask = np.isfinite(y)
    if mask.sum() < 8:
        return np.nan, np.nan, np.nan, np.nan
    X = np.column_stack([np.ones(12), np.cos(2*np.pi*m/12), np.sin(2*np.pi*m/12)])
    coefs, _, _, _ = np.linalg.lstsq(X[mask], y[mask], rcond=None)
    a0, a1, a2 = coefs
    amp = float(np.sqrt(a1**2 + a2**2))
    phase_rad = np.arctan2(a2, a1)
    phase_month = (phase_rad / (2*np.pi) * 12) % 12
    if phase_month == 0:
        phase_month = 12.0
    rmse = float(np.std(y[mask] - X[mask] @ coefs))
    return float(a0), amp, float(phase_month), rmse


def ridge_distance(e, n):
    return float(np.sqrt((e - RIDGE_E) ** 2 + (n - RIDGE_N) ** 2))


def circular_mean_month(phases):
    """
    Circular mean of phase-month values (1–12).

    Treats months as angles on a circle (each month = 30°) so that
    averaging Dec (12) and Feb (2) gives Jan (1), not Jul (7).
    """
    phases = np.asarray(phases, dtype=float)
    phases = phases[np.isfinite(phases)]
    if len(phases) == 0:
        return np.nan
    angles = (phases - 1) * 2 * np.pi / 12   # month 1 → 0 rad, month 12 → 11π/6
    mean_angle = np.arctan2(np.sin(angles).mean(), np.cos(angles).mean())
    mean_month = (mean_angle / (2 * np.pi) * 12) % 12 + 1
    # Wrap 13 → 1 (floating-point edge case when mean lands exactly on Jan)
    if mean_month > 12.5:
        mean_month -= 12
    return float(mean_month)


def load_sunshine_hours(raf_path):
    """
    Load RAF Valley monthly sunshine hours. The raw file uses 'MMM YY' format
    (e.g. 'Dec 30' = Dec 1930; 'Jan 25' = Jan 2025). Returns a Series indexed
    by first-of-month Timestamp.
    """
    import calendar
    raw = pd.read_csv(raf_path)
    first_col = raw.columns[0]

    def parse(s):
        try:
            mon_str, yr_str = str(s).strip().split()
            month = list(calendar.month_abbr).index(mon_str)
            yr = int(yr_str)
            # Two-digit year heuristic: 30-99 -> 19xx; 00-29 -> 20xx
            year = 1900 + yr if yr >= 30 else 2000 + yr
            return pd.Timestamp(year=year, month=month, day=1)
        except Exception:
            return pd.NaT

    idx = raw[first_col].apply(parse)
    sun = pd.to_numeric(raw['Sun (hrs)'], errors='coerce')
    out = pd.Series(sun.values, index=idx, name='sun_hrs').dropna()
    out = out.sort_index()
    return out


# ==========================================
# PLOTTING
# ==========================================

def plot_climatology_panels(resids_dict, meta_df, output_path):
    """Per-cluster mean climatology with per-well overlays."""
    clusters_present = sorted(meta_df['Cluster'].dropna().unique())
    n_panels = len(clusters_present)
    if n_panels == 0:
        print("  [skip] No clusters to plot.")
        return

    ncols = min(n_panels, 3)
    nrows = int(np.ceil(n_panels / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows),
                             dpi=300, sharey=True)
    axes = np.atleast_1d(axes).flatten()

    for ax, cid in zip(axes, clusters_present):
        wells_in_c = meta_df[meta_df['Cluster'] == cid].index.tolist()
        if not wells_in_c:
            ax.set_visible(False)
            continue

        well_climatologies = {}
        for well in wells_in_c:
            if well not in resids_dict:
                continue
            s = resids_dict[well]
            well_climatologies[well] = s.groupby(s.index.month).mean().reindex(range(1, 13))

        clim_df = pd.DataFrame(well_climatologies)
        cluster_mean = clim_df.mean(axis=1)

        months = np.arange(1, 13)
        # Per-well overlays (faint)
        for well, ser in well_climatologies.items():
            ax.plot(months, ser.values, color=CLUSTER_COLOURS.get(int(cid), 'grey'),
                    alpha=0.2, lw=0.8, zorder=1)
        # Cluster mean (bold)
        ax.plot(months, cluster_mean.values,
                color=CLUSTER_COLOURS.get(int(cid), 'black'),
                lw=2.6, marker='o', markersize=6, markeredgecolor='black',
                markeredgewidth=0.6, zorder=3,
                label=f"Cluster mean (n={len(well_climatologies)})")
        ax.axhline(0, color='black', lw=0.8, ls='--', alpha=0.6, zorder=2)
        # Shade JJA and DJF
        ax.axvspan(5.5, 8.5, color='red',  alpha=0.06, zorder=0)
        ax.axvspan(11.5, 12.5, color='blue', alpha=0.06, zorder=0)
        ax.axvspan(0.5, 2.5,   color='blue', alpha=0.06, zorder=0)

        ax.set_xticks(months)
        ax.set_xticklabels(MONTH_LABELS)
        ax.set_xlim(0.5, 12.5)
        ax.set_xlabel('Month')
        ax.set_ylabel('Residual (m)')
        ax.set_title(f"{CLUSTER_LABELS.get(int(cid), f'C{int(cid)}')}", fontweight='bold')
        ax.grid(ls='--', alpha=0.4)
        ax.legend(loc='upper right', fontsize=8, frameon=True, edgecolor='black')

    # Hide unused subplots
    for i in range(len(clusters_present), len(axes)):
        axes[i].set_visible(False)

    fig.suptitle("Seasonal climatology of SSM residuals by cluster\n"
                 "(red band = JJA, blue bands = DJF)",
                 fontsize=14, fontweight='bold', y=1.00)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


def plot_amplitude_map(clim_df, output_path):
    """Spatial map of seasonal amplitude per well."""
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    valid = clim_df.dropna(subset=['Easting', 'Northing', 'amplitude'])
    if valid.empty:
        print("  [skip] No valid coordinates for amplitude map.")
        return

    sc = ax.scatter(valid['Easting'], valid['Northing'],
                    c=valid['amplitude'], cmap='viridis',
                    vmin=0, vmax=max(0.05, valid['amplitude'].quantile(0.95)),
                    s=90, edgecolor='black', linewidth=0.7, zorder=4)
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label('Seasonal amplitude (m)', fontsize=11)

    ax.scatter(RIDGE_E, RIDGE_N, marker='*', s=500, color='red',
               edgecolor='black', linewidth=1.2, zorder=5,
               label='Ridge reference')

    # Label the notable wells
    for well in ['ceh14', 'ceh34', 'ceh2', 'nw10']:
        row = valid[valid['Well_Normalized'] == well]
        if not row.empty:
            ax.annotate(well.upper(),
                        xy=(row['Easting'].iloc[0], row['Northing'].iloc[0]),
                        xytext=(6, 6), textcoords='offset points',
                        fontsize=8, fontweight='bold', zorder=6)

    try:
        add_kml_features(ax)
    except Exception as e:
        print(f"  [note] KML overlay skipped: {e}")

    ax.set_xlabel('Easting (m, OSGB36)')
    ax.set_ylabel('Northing (m, OSGB36)')
    ax.set_title('Seasonal amplitude of SSM residuals\n'
                 '(large amplitude indicates a strong annual cycle in the residual)',
                 fontweight='bold')
    ax.set_aspect('equal')
    ax.grid(ls='--', alpha=0.4)
    ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


def plot_sun_corr_scatter(clim_df, output_path):
    """Distribution of (sunshine hours, residual) correlation per well, by cluster.

    Sunshine hours is an independent radiation-based ET proxy, NOT in the OLS
    regression. A systematic negative correlation would indicate that high-
    insolation months carry extra ET losses that Thornthwaite (temperature-
    only) has not captured."""
    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)

    clusters = sorted(clim_df['Cluster'].dropna().unique())
    for i, cid in enumerate(clusters):
        sub = clim_df[clim_df['Cluster'] == cid]
        col = CLUSTER_COLOURS.get(int(cid), '#777777')
        x = np.full(len(sub), i) + np.random.default_rng(int(cid)).uniform(-0.15, 0.15, len(sub))
        ax.scatter(x, sub['corr_sun_resid'],
                   color=col, s=60, edgecolor='black', linewidth=0.5,
                   alpha=0.8, label=f"{CLUSTER_LABELS.get(int(cid), f'C{int(cid)}')} (n={len(sub)})")
        # Cluster mean as large diamond
        ax.scatter([i], [sub['corr_sun_resid'].mean()],
                   color=col, s=250, marker='D', edgecolor='black', linewidth=1.4,
                   zorder=5)

    ax.axhline(0, color='black', lw=0.8, ls='--', alpha=0.7)
    thresh = 1.96 / np.sqrt(170)
    ax.axhspan(-thresh, thresh, color='grey', alpha=0.12,
               label=f'Bartlett 95% CI (|r|<{thresh:.2f})')

    ax.set_xticks(range(len(clusters)))
    ax.set_xticklabels([CLUSTER_LABELS.get(int(c), f'C{int(c)}') for c in clusters])
    ax.set_ylabel('Pearson r (SSM residual vs sunshine hours)')
    ax.set_title("Correlation between residual and sunshine hours, per well\n"
                 "Negative values would indicate Thornthwaite underestimates summer ET",
                 fontweight='bold')
    ax.grid(axis='y', ls='--', alpha=0.4)
    ax.legend(loc='best', frameon=True, edgecolor='black', fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


def plot_phase_barplot(clim_df, output_path):
    """Per-well phase month, grouped by cluster, on a hydrological-year axis
    (Sep–Aug). Uses circular mean for cluster averages so that wrapping around
    Dec/Jan is handled correctly."""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    # Hydrological year: Sep=1, Oct=2, ... Aug=12
    # Mapping from calendar month (1-12) to hydro position:
    #   cal  9 10 11 12  1  2  3  4  5  6  7  8
    #   hyd  1  2  3  4  5  6  7  8  9 10 11 12
    HYDRO_LABELS = ['S', 'O', 'N', 'D', 'J', 'F', 'M', 'A', 'M', 'J', 'J', 'A']

    def cal_to_hydro(cal_month):
        """Convert calendar month (1-12) to hydro position (1-12)."""
        return ((cal_month - 9) % 12) + 1

    clusters = sorted(clim_df['Cluster'].dropna().unique())
    x_pos = 0
    tick_positions = []
    tick_labels = []
    rng = np.random.default_rng(0)

    for cid in clusters:
        sub = clim_df[clim_df['Cluster'] == cid].dropna(subset=['phase_month'])
        col = CLUSTER_COLOURS.get(int(cid), '#777777')
        if len(sub) > 0:
            hydro_phases = sub['phase_month'].apply(cal_to_hydro).values
            xs = np.full(len(sub), x_pos) + rng.uniform(-0.25, 0.25, len(sub))
            ax.scatter(xs, hydro_phases,
                       s=70, color=col, edgecolor='black', linewidth=0.5,
                       alpha=0.85, zorder=3)
            # Circular mean (in calendar months), then convert to hydro
            cmean_cal = circular_mean_month(sub['phase_month'].values)
            cmean_hydro = cal_to_hydro(cmean_cal)
            ax.scatter([x_pos], [cmean_hydro],
                       s=260, color=col, marker='*',
                       edgecolor='black', linewidth=1.5, zorder=5)
            tick_positions.append(x_pos)
            tick_labels.append(f"{CLUSTER_LABELS.get(int(cid), f'C{int(cid)}')}\n(n={len(sub)})")
            x_pos += 1

    # Summer and winter bands (in hydro coordinates)
    # Summer JJA = hydro 10, 11, 12
    ax.axhspan(9.5, 12.5, color='red',  alpha=0.08, zorder=0, label='Summer (JJA)')
    # Winter DJF = hydro 4, 5, 6
    ax.axhspan(3.5, 6.5, color='blue', alpha=0.08, zorder=0, label='Winter (DJF)')

    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)
    ax.set_yticks(range(1, 13))
    ax.set_yticklabels(HYDRO_LABELS)
    ax.set_ylabel('Month of residual peak (phase) — hydrological year')
    ax.set_ylim(0.5, 12.5)
    ax.set_title("Phase of seasonal residual cycle, per well\n"
                 "Summer phase = ET signature; Winter phase = recharge nonlinearity\n"
                 "★ = circular mean  |  Axis starts at September (hydrological year)",
                 fontweight='bold')
    ax.grid(axis='y', ls='--', alpha=0.4)
    ax.legend(loc='upper right', frameon=True, edgecolor='black', fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {output_path.name}")


# ==========================================
# INTERPRETIVE SUMMARY
# ==========================================

def write_summary(clim_df, output_path):
    lines = []
    lines.append("=" * 78)
    lines.append("  SEASONAL RESIDUAL DIAGNOSTIC — SUMMARY")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"  Wells analysed: {len(clim_df)}")
    lines.append(f"  Ridge reference: E={RIDGE_E:.0f}, N={RIDGE_N:.0f}")
    lines.append(f"  C3 split distance: {C3_SPLIT_DISTANCE_M:.0f} m")
    lines.append("")

    # Summer-winter, amplitude, phase by cluster
    lines.append("-" * 78)
    lines.append("  PER-CLUSTER SEASONAL STATISTICS")
    lines.append("-" * 78)
    grp = clim_df.groupby('Cluster').agg(
        n=('Well_Normalized', 'count'),
        s_minus_w=('summer_minus_winter', 'mean'),
        amplitude=('amplitude', 'mean'),
        phase=('phase_month', lambda x: circular_mean_month(x.values)),
        corr_sun=('corr_sun_resid', 'mean'),
    ).round(4)
    lines.append(grp.to_string())
    lines.append("")

    # C3 split
    c3 = clim_df[clim_df['Cluster'] == 3]
    if len(c3) > 0:
        adj = c3[c3['ridge_distance_m'] < C3_SPLIT_DISTANCE_M]
        far = c3[c3['ridge_distance_m'] >= C3_SPLIT_DISTANCE_M]
        lines.append("-" * 78)
        lines.append(f"  C3 SPLIT BY DISTANCE (< vs >= {C3_SPLIT_DISTANCE_M:.0f} m from ridge)")
        lines.append("-" * 78)
        lines.append(f"  Forest-adjacent (n={len(adj)}): "
                     f"amplitude = {adj['amplitude'].mean():.4f}  "
                     f"s-w = {adj['summer_minus_winter'].mean():+.4f}")
        lines.append(f"  Warren-interior (n={len(far)}): "
                     f"amplitude = {far['amplitude'].mean():.4f}  "
                     f"s-w = {far['summer_minus_winter'].mean():+.4f}")
        if len(adj) > 2 and len(far) > 2:
            u, p = scipy_stats.mannwhitneyu(
                adj['amplitude'], far['amplitude'], alternative='less')
            lines.append(f"  Mann-Whitney (adj < far amp): U={u:.1f}, p={p:.4f}")
        lines.append("")

    # Sunshine-hours correlation (independent ET proxy, not in regression)
    lines.append("-" * 78)
    lines.append("  SUNSHINE-HOURS CORRELATION (INDEPENDENT ET DIAGNOSTIC)")
    lines.append("-" * 78)
    lines.append("  Sunshine hours is not in the OLS regression, so cor(resid, sun) is")
    lines.append("  a real test rather than zero by construction. A systematic negative")
    lines.append("  correlation would indicate extra ET losses in high-insolation months")
    lines.append("  that Thornthwaite has not captured and b2 has therefore not fitted.")
    lines.append("")
    thresh = 1.96 / np.sqrt(170)
    vals = clim_df['corr_sun_resid'].dropna()
    neg = (vals < -thresh).sum()
    pos = (vals > thresh).sum()
    null = len(vals) - neg - pos
    lines.append(f"  Wells with r < {-thresh:+.3f} (extra ET not in Thornthwaite): "
                 f"{neg} / {len(vals)}")
    lines.append(f"  Wells with r >  {+thresh:+.3f}:                                "
                 f"{pos} / {len(vals)}")
    lines.append(f"  Wells within Bartlett null band:                          "
                 f"{null} / {len(vals)}")
    lines.append(f"  Network mean: {vals.mean():+.4f}")
    lines.append("")

    # Interpretation
    lines.append("-" * 78)
    lines.append("  INTERPRETATION")
    lines.append("-" * 78)
    mean_sw = clim_df['summer_minus_winter'].mean()
    mean_phase = circular_mean_month(clim_df['phase_month'].values)
    mean_sun_corr = clim_df['corr_sun_resid'].mean()

    if abs(mean_sun_corr) < thresh and abs(mean_sw) < 0.04:
        lines.append("  NULL on ET hypothesis: sunshine-residual correlation is within the")
        lines.append("  Bartlett null band across clusters and summer-minus-winter residual")
        lines.append("  is small in magnitude. The residual is not dominantly unmodelled")
        lines.append("  summer ET — whatever systematic bias Thornthwaite has, b2 has")
        lines.append("  already absorbed it.")
    elif mean_sun_corr < -thresh:
        lines.append("  ET HYPOTHESIS PARTIALLY SUPPORTED: systematic negative correlation")
        lines.append("  between sunshine hours and residual, consistent with Thornthwaite")
        lines.append("  underestimating summer atmospheric demand beyond what b2 absorbs.")
    else:
        lines.append("  MIXED / UNCLEAR ET signal.")
    lines.append("")

    # Winter-peak (recharge nonlinearity) signal
    winter_peaking = ((clim_df['phase_month'] >= 11) |
                      (clim_df['phase_month'] <= 3)).sum()
    summer_peaking = ((clim_df['phase_month'] >= 5) &
                      (clim_df['phase_month'] <= 8)).sum()
    lines.append(f"  Wells with winter/early-spring phase peak (Nov-Mar): "
                 f"{winter_peaking} / {len(clim_df)}")
    lines.append(f"  Wells with summer phase peak (May-Aug):              "
                 f"{summer_peaking} / {len(clim_df)}")
    lines.append("")

    if winter_peaking > 2 * summer_peaking:
        lines.append("  Dominant phase is winter/early spring. This is not the signature")
        lines.append("  of unmodelled summer ET. It is consistent with threshold/nonlinear")
        lines.append("  recharge behaviour not captured by the linear b1*P term: in")
        lines.append("  mid-winter with saturated soils, rainfall reaches the water table")
        lines.append("  with higher efficiency than the cluster-mean b1 represents.")
    lines.append("")
    lines.append("=" * 78)

    output_path.write_text("\n".join(lines))
    print(f" -> Saved: {output_path.name}")
    print("\n" + "\n".join(lines))


# ==========================================
# MAIN
# ==========================================

def main():
    make_all_dirs()
    print("Starting 24: Seasonal Residual Diagnostic...")

    wells      = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    climate    = pd.read_csv(INT_CLIMATE,    index_col=0, parse_dates=True)
    locations  = pd.read_csv(INT_LOCATIONS)
    cluster_df = pd.read_csv(INT_CLUSTER_STATS)

    cluster_df['_norm'] = cluster_df['Match_ID'].apply(normalize_well_name)
    cluster_lookup = dict(zip(cluster_df['_norm'], cluster_df['Cluster']))

    locations['_norm'] = locations['Name'].apply(normalize_well_name)
    coords_lookup = {r['_norm']: (r['E'], r['N']) for _, r in locations.iterrows()}

    # Load sunshine hours as the independent ET proxy (not in regression, so
    # cor(residual, sun) is a real test rather than zero by construction).
    try:
        sun = load_sunshine_hours(DATA_CLIMATE_RAW)
        print(f" -> Loaded sunshine hours: {len(sun)} months "
              f"({sun.index.min():%Y-%m} to {sun.index.max():%Y-%m})")
    except Exception as e:
        print(f"  [warn] Could not load sunshine hours ({e}); sun correlations will be NaN.")
        sun = pd.Series(dtype=float)

    candidate_wells = [c for c in wells.columns
                       if normalize_well_name(c) not in EXCLUDED_WELLS_NORM]
    print(f" -> Candidate wells: {len(candidate_wells)}")

    rows = []
    resids_dict = {}

    for well_col in candidate_wells:
        norm = normalize_well_name(well_col)
        coords = coords_lookup.get(norm, (np.nan, np.nan))
        if pd.isna(coords[0]):
            continue
        d_ridge = ridge_distance(coords[0], coords[1])
        if d_ridge > MAX_RIDGE_DISTANCE_M:
            continue

        resid = fit_ssm_residual(wells[well_col], climate)
        if resid is None:
            continue

        resids_dict[norm] = resid

        # Monthly climatology
        month_mean = resid.groupby(resid.index.month).mean()
        full = month_mean.reindex(range(1, 13))
        summer = month_mean.reindex([6, 7, 8]).mean()
        winter = month_mean.reindex([12, 1, 2]).mean()
        a0, amp, phase, rmse = sinusoidal_fit(full)

        # Sunshine-hours correlation (independent ET proxy; not in regression)
        if len(sun) > 0:
            common = resid.index.intersection(sun.index)
            if len(common) > 30:
                corr_sun = float(np.corrcoef(sun.loc[common].values,
                                             resid.loc[common].values)[0, 1])
            else:
                corr_sun = np.nan
        else:
            corr_sun = np.nan

        rows.append({
            'Well':             well_col,
            'Well_Normalized':  norm,
            'Cluster':          cluster_lookup.get(norm, np.nan),
            'Easting':          coords[0],
            'Northing':         coords[1],
            'ridge_distance_m': d_ridge,
            'n_obs':            len(resid),
            'summer_mean':      float(summer) if pd.notna(summer) else np.nan,
            'winter_mean':      float(winter) if pd.notna(winter) else np.nan,
            'summer_minus_winter': (float(summer - winter)
                                    if pd.notna(summer) and pd.notna(winter) else np.nan),
            'offset_a0':        a0,
            'amplitude':        amp,
            'phase_month':      phase,
            'sinusoid_rmse':    rmse,
            'corr_sun_resid':   corr_sun,
        })

    clim_df = pd.DataFrame(rows)
    print(f" -> Computed climatologies for {len(clim_df)} wells.")

    # Save table
    clim_df.to_csv(INT_24_CLIMATOLOGY_TABLE, index=False)
    print(f" -> Saved: {INT_24_CLIMATOLOGY_TABLE.name}")

    # Meta indexed by well for the per-cluster plot
    meta_df = clim_df.set_index('Well_Normalized')

    # Figures
    plot_climatology_panels(resids_dict, meta_df, OUT_24_CLIMATOLOGY_PANELS)
    plot_amplitude_map(clim_df, OUT_24_AMPLITUDE_MAP)
    plot_sun_corr_scatter(clim_df, OUT_24_SUN_CORR_SCATTER)
    plot_phase_barplot(clim_df, OUT_24_PHASE_BARPLOT)

    # Summary
    write_summary(clim_df, OUT_24_SUMMARY)

    print("\n24 complete.")


if __name__ == "__main__":
    main()
