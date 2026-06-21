r"""
====================================================================================
10g — DIAGNOSTICS: NW10 TREND, CLEARFELL TRANSECT, ROLLING COEFFICIENTS
====================================================================================
Three diagnostic analyses for the clearfell BACI assessment:

  1. NW10 Broadleaf Trend (Section 4.6.8)
     - Summer minimum anomaly of NW10 relative to pine interior composite
       (CEH2, CEH32, CEH33, CEH34)
     - OLS trend over 2019–2025 to test broadleaf succession signal

  2. Clearfell Transect (3-panel figure)
     - Panel A: depth anomaly relative to scrape-era mean (6-mo rolling)
     - Panel B: relative position — zone mean anomalies vs transect mean
     - Panel C: step change vs distance scatter with regression

  3. Rolling SSM Coefficients (cluster transition)
     - 48-month rolling-window SSM fits for impact zone, C3, and C4 centroids
     - Tests whether the felled zone β₁/β₃ converge toward C3 (open dune)
       post-felling

Excluded wells:
  NW8 and NW8B are compromised and excluded from all analyses.

Dependencies:
  utils/clearfell_common.py — well lists, dates, data loading
  utils/model_utils.py      — build_ssm_frame()

Outputs:
  outputs/10_clearfell_baci/10g_01_nw10_broadleaf_trend.csv
  outputs/10_clearfell_baci/10g_02_clearfell_transect.png
  outputs/10_clearfell_baci/10g_03_clearfell_transect_steps.csv
  outputs/10_clearfell_baci/10g_04_rolling_coefficients.csv
  outputs/10_clearfell_baci/10g_report_numbers.csv
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import statsmodels.api as sm
from scipy import stats as sp_stats

from utils.paths import (
    make_all_dirs, DIR_10, INT_REGIONAL_AVG,
    OUT_10G_NW10_TREND, OUT_10G_TRANSECT_FIG, OUT_10G_TRANSECT_CSV,
    OUT_10G_ROLLING_CSV, OUT_10G_REPORT,
)
from utils.model_utils import build_ssm_frame
from utils.config import DRAINAGE_DATUM, HEADLINE_LAG
from utils.clearfell_common import (
    load_clearfell_data, print_network_summary,
    INTERVENTION_DATE, SCRAPING_DATE, SCRAPING_DATE_2,
    IMPACT_WELLS, EDGE_WELLS,
    FOREST_CONTROL_WELLS, COASTAL_CONTROL_WELLS, CLIMATE_CONTROL_WELLS,
    FELL_CENTROID_EASTING, FELL_CENTROID_NORTHING,
    SUMMER_MONTHS,
    ReportNumbers,
)

__version__ = "1.0.0"

# ── Exclusions ──────────────────────────────────────────────────────────────
EXCLUDED_WELLS = {'nw8', 'nw8b'}

# ── Transect configuration ──────────────────────────────────────────────────
# Radial transect from the clearfell centroid outward.
# NW8B excluded (compromised) — replaced by CEH31 and CEH30.
TRANSECT_WELLS = {
    'wmc3':  {'label': 'WMC3\nCore impact',     'dist_m':  45, 'role': 'impact'},
    'ceh31': {'label': 'CEH31\nEdge S',         'dist_m': 152, 'role': 'edge'},
    'ceh30': {'label': 'CEH30\nEdge NW',        'dist_m': 206, 'role': 'edge'},
    'ceh16': {'label': 'CEH16\nEdge W',         'dist_m': 222, 'role': 'edge'},
    'ceh20': {'label': 'CEH20\nEdge N',         'dist_m': 229, 'role': 'edge'},
    'ceh34': {'label': 'CEH34\nForest control', 'dist_m': 306, 'role': 'control'},
    'ceh2':  {'label': 'CEH2\nPine/BL margin',  'dist_m': 428, 'role': 'reference'},
}

TRANSECT_LINESTYLES = {
    'wmc3':  ('-',  '#D55E00'),
    'ceh31': ('-',  '#E69F00'),
    'ceh30': ('-',  '#56B4E9'),
    'ceh16': ('-',  '#9467BD'),
    'ceh20': ('-',  '#1F77B4'),
    'ceh34': ('--', '#2CA02C'),
    'ceh2':  ('--', '#888888'),
}

# Pine interior composite for NW10 analysis
PINE_INTERIOR = ['ceh2', 'ceh32', 'ceh33', 'ceh34']

# Rolling window for SSM coefficients
ROLL_WINDOW = 48  # months

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


# ============================================================================
# 1. NW10 BROADLEAF TREND
# ============================================================================

def nw10_broadleaf_trend(wells, rpt):
    """Fit OLS trend to NW10 normalised summer minimum anomaly (2019–2025)."""
    print("\n2. NW10 Broadleaf Trend Analysis...")

    pine_avail = [w for w in PINE_INTERIOR
                  if w in wells.columns and w not in EXCLUDED_WELLS]
    if 'nw10' not in wells.columns or len(pine_avail) < 2:
        print("   NW10 or pine interior wells not available — skipping")
        return

    # Annual summer minimum (Jun–Sep) — most negative = deepest
    nw10_mins = {}
    pine_mins = {}
    for yr in range(2007, 2027):
        mask = ((wells.index.year == yr) &
                (wells.index.month.isin(SUMMER_MONTHS)))
        nw10_s = wells['nw10'][mask].dropna()
        if len(nw10_s) >= 2:
            nw10_mins[yr] = float(nw10_s.min())  # min = deepest summer level

        pine_s = wells[pine_avail][mask].mean(axis=1).dropna()
        if len(pine_s) >= 2:
            pine_mins[yr] = float(pine_s.min())

    common_yrs = sorted(set(nw10_mins) & set(pine_mins))
    if len(common_yrs) < 5:
        print("   Insufficient common years — skipping")
        return

    anom = pd.Series(
        {yr: nw10_mins[yr] - pine_mins[yr] for yr in common_yrs})

    # Full-record mean anomaly (bramble-dominated phase 2010–2021)
    bramble = anom[(anom.index >= 2010) & (anom.index <= 2021)]
    mean_anom_bramble = float(bramble.mean()) if len(bramble) > 0 else np.nan

    # OLS trend over 2019–2025
    trend_data = anom[(anom.index >= 2019) & (anom.index <= 2025)]
    slope_m_yr = np.nan
    p_val = np.nan

    if len(trend_data) >= 4:
        X = np.column_stack([np.ones(len(trend_data)),
                             trend_data.index.astype(float)])
        y = trend_data.values
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        n, k = len(y), 2
        r = y - X @ b
        s2 = (r @ r) / (n - k)
        se_b1 = np.sqrt(s2 * np.linalg.inv(X.T @ X)[1, 1])
        t_stat = b[1] / se_b1
        p_val = float(2 * sp_stats.t.sf(abs(t_stat), df=n - k))
        slope_m_yr = float(b[1])
        slope_mm_yr = slope_m_yr * 1000

        print(f"   Pine composite: {', '.join(w.upper() for w in pine_avail)}")
        print(f"   Mean NW10 anomaly vs pine (2010–2021): {mean_anom_bramble:+.3f} m")
        print(f"   OLS trend 2019–2025: {slope_mm_yr:+.1f} mm/yr "
              f"(p={p_val:.3f}, n={n})")

        rpt.add("NW10_trend_slope_mm_yr", round(slope_mm_yr, 1), "mm/yr",
                note=f"p={p_val:.3f}, n={n}")
        rpt.add("NW10_mean_anomaly_2010_2021", round(mean_anom_bramble, 4), "m")
    else:
        print("   Insufficient data for 2019–2025 trend (n < 4)")

    # Export
    export_rows = []
    for yr in common_yrs:
        export_rows.append({
            'Year': yr,
            'NW10_summer_min_m': round(nw10_mins[yr], 4),
            'Pine_composite_min_m': round(pine_mins[yr], 4),
            'NW10_anomaly_m': round(float(anom[yr]), 4),
        })
    df_export = pd.DataFrame(export_rows)

    if pd.notna(slope_m_yr):
        trend_row = pd.DataFrame([{
            'Year': np.nan,
            'NW10_summer_min_m': np.nan,
            'Pine_composite_min_m': np.nan,
            'NW10_anomaly_m': np.nan,
            'Trend_slope_m_yr': round(slope_m_yr, 5),
            'Trend_p': round(p_val, 4),
            'Trend_n': len(trend_data),
        }])
        df_export = pd.concat([df_export, trend_row], ignore_index=True)

    df_export.to_csv(OUT_10G_NW10_TREND, index=False, float_format="%.4f")
    print(f"   -> Saved: {OUT_10G_NW10_TREND.name}")


# ============================================================================
# 2. CLEARFELL TRANSECT (3-panel figure)
# ============================================================================

def clearfell_transect(wells, rpt):
    """Three-panel transect figure: anomaly, relative position, distance scatter."""
    print("\n3. Clearfell Transect Figure...")

    transect_available = {w: cfg for w, cfg in TRANSECT_WELLS.items()
                          if w in wells.columns and w not in EXCLUDED_WELLS}
    if len(transect_available) < 3:
        print("   Too few transect wells available — skipping")
        return

    print(f"   Using {len(transect_available)} wells: "
          f"{', '.join(w.upper() for w in transect_available)}")

    # Era masks
    mask_scrape = ((wells.index >= SCRAPING_DATE) &
                   (wells.index < INTERVENTION_DATE))
    mask_post = wells.index >= INTERVENTION_DATE

    # Step changes
    step_changes = {}
    for w in transect_available:
        s = wells[w]
        pre = s[mask_scrape].mean()
        post = s[mask_post].mean()
        if pd.notna(pre) and pd.notna(post):
            step_changes[w] = post - pre

    # Transect mean for anomaly reference
    transect_mean = wells[list(transect_available.keys())].mean(axis=1)
    roll_mean = transect_mean.rolling(6, min_periods=3).mean()

    # ── Build figure ─────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(14, 10), facecolor='white')
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.30,
                  top=0.90, bottom=0.07, left=0.08, right=0.96)
    ax_a = fig.add_subplot(gs[0, :])  # full width top
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])

    # ── Panel A: depth anomaly relative to scrape-era mean ───────────────────
    for w, cfg in transect_available.items():
        ls, col = TRANSECT_LINESTYLES[w]
        lw = 1.8 if cfg['role'] == 'impact' else 1.4
        scrape_mean_w = wells[w][mask_scrape].mean()
        if pd.isna(scrape_mean_w):
            continue
        anomaly = wells[w] - scrape_mean_w
        anomaly_smooth = anomaly.rolling(6, min_periods=3).mean()
        ax_a.plot(wells.index, anomaly_smooth, ls=ls, color=col, lw=lw,
                  label=f"{cfg['label'].split(chr(10))[0]} ({cfg['dist_m']}m)",
                  alpha=0.85)

    ax_a.axhline(0, color='black', lw=0.8, ls='-', alpha=0.4)
    for vdate, vcol, vlbl in [
            (SCRAPING_DATE,     '#2166AC', 'Scrape'),
            (INTERVENTION_DATE, '#CC0000', 'Clearfell'),
            (SCRAPING_DATE_2,   '#888888', 'Scrape 2')]:
        ax_a.axvline(pd.Timestamp(vdate), color=vcol, lw=1.1, ls='--', alpha=0.7)
    ax_a.axvspan(SCRAPING_DATE, INTERVENTION_DATE, alpha=0.06, color='#2166AC')
    ax_a.axvspan(INTERVENTION_DATE, wells.index.max(), alpha=0.06, color='#CC0000')
    ax_a.set_ylabel('Anomaly vs scrape-era mean (m)', fontsize=8)
    ax_a.legend(fontsize=6.5, loc='upper left', framealpha=0.9, ncol=2)
    ax_a.grid(axis='y', alpha=0.2, lw=0.5)
    ax_a.set_title('(a) Depth anomaly — rising = shallowing', fontsize=9, fontweight='bold')
    ax_a.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # ── Panel B: anomaly vs transect mean ────────────────────────────────────
    role_groups = {}
    for w, cfg in transect_available.items():
        role_groups.setdefault(cfg['role'], []).append(w)

    # Individual wells (thin)
    for w, cfg in transect_available.items():
        ls, col = TRANSECT_LINESTYLES[w]
        anom = wells[w].rolling(6, min_periods=3).mean() - roll_mean
        ax_b.plot(wells.index, anom, ls=ls, color=col, lw=0.8, alpha=0.4)

    # Zone means (thick)
    for role, role_wells, col, lbl in [
            ('impact',  role_groups.get('impact', []),  '#D55E00', 'Impact mean'),
            ('edge',    role_groups.get('edge', []),     '#1F77B4', 'Edge mean'),
            ('control', (role_groups.get('control', []) +
                         role_groups.get('reference', [])), '#2CA02C', 'Control/ref mean')]:
        if role_wells:
            zone_mean = (wells[role_wells].mean(axis=1)
                         .rolling(6, min_periods=3).mean() - roll_mean)
            ax_b.plot(wells.index, zone_mean, ls='-', color=col, lw=2.0,
                      alpha=0.9, label=lbl)

    ax_b.axhline(0, color='black', lw=0.8, ls='-', alpha=0.5)
    for vdate, vcol in [(SCRAPING_DATE, '#2166AC'),
                         (INTERVENTION_DATE, '#CC0000'),
                         (SCRAPING_DATE_2, '#888888')]:
        ax_b.axvline(pd.Timestamp(vdate), color=vcol, lw=1.1, ls='--', alpha=0.7)
    ax_b.axvspan(SCRAPING_DATE, INTERVENTION_DATE, alpha=0.06, color='#2166AC')
    ax_b.axvspan(INTERVENTION_DATE, wells.index.max(), alpha=0.06, color='#CC0000')
    ax_b.set_ylabel('Anomaly vs transect mean (m)', fontsize=8)
    ax_b.set_title('(b) Relative position — zone means', fontsize=9, fontweight='bold')
    ax_b.grid(axis='y', alpha=0.2, lw=0.5)
    ax_b.legend(fontsize=7, framealpha=0.9)
    ax_b.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # ── Panel C: step change vs distance scatter ─────────────────────────────
    if step_changes:
        dists = [TRANSECT_WELLS[w]['dist_m'] for w in step_changes]
        steps = [step_changes[w] for w in step_changes]
        roles = [TRANSECT_WELLS[w]['role'] for w in step_changes]
        labels = [TRANSECT_WELLS[w]['label'].split('\n')[0] for w in step_changes]

        for i, w in enumerate(step_changes):
            _, col = TRANSECT_LINESTYLES[w]
            ax_c.scatter(dists[i], steps[i], c=col, s=80, zorder=5,
                         edgecolors='white', linewidths=0.8)
            ax_c.annotate(labels[i], (dists[i], steps[i]),
                          fontsize=6.5, ha='left', va='bottom',
                          xytext=(4, 3), textcoords='offset points')

        # Regression through impact + edge
        interv_idx = [i for i, r in enumerate(roles) if r in ('impact', 'edge')]
        if len(interv_idx) >= 3:
            d_fit = np.array([dists[i] for i in interv_idx])
            s_fit = np.array([steps[i] for i in interv_idx])
            slope, intercept, r_val, p_reg, _ = sp_stats.linregress(d_fit, s_fit)
            x_line = np.linspace(min(dists) - 20, max(dists) + 20, 100)
            ax_c.plot(x_line, intercept + slope * x_line,
                      color='#CC0000', lw=1.5, ls='--', alpha=0.7,
                      label=f'Gradient: {slope*1000:.1f} mm/100m  p={p_reg:.3f}')
            rpt.add("Transect_gradient_mm_per_100m", round(slope * 1000, 1),
                    "mm/100m", note=f"p={p_reg:.3f}")

        ctrl_steps = [steps[i] for i, r in enumerate(roles)
                      if r in ('control', 'reference')]
        if ctrl_steps:
            ctrl_mean = np.mean(ctrl_steps)
            ax_c.axhline(ctrl_mean, color='#2CA02C', lw=1.2, ls=':',
                         alpha=0.6, label=f'Control baseline: {ctrl_mean:+.3f} m')

        ax_c.set_xlabel('Distance from clearfell centroid (m)', fontsize=8)
        ax_c.set_ylabel('Post-fell step vs scrape era (m)', fontsize=8)
        ax_c.set_title('(c) Step change vs distance', fontsize=9, fontweight='bold')
        ax_c.grid(alpha=0.2, lw=0.5)
        ax_c.legend(fontsize=6.5, framealpha=0.9)

    fig.suptitle(
        'Clearfell Transect Analysis\n'
        'Post-felling step change decays with distance from clearfell core',
        fontsize=10, fontweight='bold', y=0.97)

    plt.savefig(OUT_10G_TRANSECT_FIG, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"   -> Saved: {OUT_10G_TRANSECT_FIG.name}")

    # Export step-change CSV
    rows = []
    for w in transect_available:
        cfg = transect_available[w]
        rows.append({
            'Well': w.upper(),
            'Label': cfg['label'].replace('\n', ' '),
            'Distance_m': cfg['dist_m'],
            'Role': cfg['role'],
            'Scrape_era_mean_m': round(float(wells[w][mask_scrape].mean()), 4),
            'Post_fell_mean_m': round(float(wells[w][mask_post].mean()), 4),
            'Step_change_m': round(float(step_changes.get(w, np.nan)), 4),
        })
    pd.DataFrame(rows).to_csv(OUT_10G_TRANSECT_CSV, index=False, float_format="%.4f")
    print(f"   -> Saved: {OUT_10G_TRANSECT_CSV.name}")


# ============================================================================
# 3. ROLLING SSM COEFFICIENTS (cluster transition)
# ============================================================================

def _rolling_ssm_coeffs(h_series, climate_df, window=ROLL_WINDOW):
    """Compute rolling-window SSM β₁ and β₃ over time."""
    results = []
    df = build_ssm_frame(h_series, climate_df, lag=HEADLINE_LAG,
                         drainage_datum=DRAINAGE_DATUM)
    if len(df) < window:
        return pd.DataFrame()

    for end_idx in range(window, len(df) + 1):
        chunk = df.iloc[end_idx - window:end_idx]
        X = pd.DataFrame({
            'b1':  chunk['P'].values,
            'b2': -chunk['PET'].values,
            'b3': -chunk['h_disp_prev'].values,
        })
        try:
            _fit = sm.OLS(chunk['Delta_h'].values, X).fit()
            results.append({
                'date': chunk.index[-1],
                'beta_1': float(_fit.params['b1']),
                'beta_2': float(_fit.params['b2']),
                'beta_3': float(_fit.params['b3']),
                'R2': float(_fit.rsquared),
            })
        except Exception:
            continue
    return pd.DataFrame(results).set_index('date') if results else pd.DataFrame()


def rolling_coefficients(wells, climate, rpt):
    """Rolling SSM coefficients for impact zone vs C3/C4 centroids."""
    print("\n4. Rolling SSM Coefficient Analysis (cluster transition)...")

    # Impact zone mean
    valid_impact = [w for w in IMPACT_WELLS
                    if w in wells.columns and w not in EXCLUDED_WELLS]
    if not valid_impact:
        print("   No impact wells available — skipping")
        return

    impact_mean = wells[valid_impact].mean(axis=1).dropna()
    roll_impact = _rolling_ssm_coeffs(impact_mean, climate)

    # Reference cluster centroids from Script 03
    c3_centroid = c4_centroid = None
    try:
        reg_avg = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
        if 'C3' in reg_avg.columns:
            c3_centroid = reg_avg['C3']
        if 'C4' in reg_avg.columns:
            c4_centroid = reg_avg['C4']
    except Exception:
        print("   Could not load cluster centroids from Script 03 — skipping")
        return

    roll_c3 = _rolling_ssm_coeffs(c3_centroid, climate) if c3_centroid is not None else pd.DataFrame()
    roll_c4 = _rolling_ssm_coeffs(c4_centroid, climate) if c4_centroid is not None else pd.DataFrame()

    # Transition assessment
    if not roll_impact.empty and not roll_c3.empty:
        post_roll = roll_impact[roll_impact.index >= INTERVENTION_DATE]
        pre_roll = roll_impact[(roll_impact.index >= SCRAPING_DATE) &
                               (roll_impact.index < INTERVENTION_DATE)]
        c3_post = roll_c3[roll_c3.index >= INTERVENTION_DATE]

        if len(post_roll) >= 6 and len(c3_post) >= 6:
            b1_impact_post = post_roll['beta_1'].mean()
            b3_impact_post = post_roll['beta_3'].mean()
            b1_c3_post = c3_post['beta_1'].mean()
            b3_c3_post = c3_post['beta_3'].mean()
            b1_c4_post = (roll_c4[roll_c4.index >= INTERVENTION_DATE]['beta_1'].mean()
                          if not roll_c4.empty else np.nan)

            if len(pre_roll) >= 3:
                b1_impact_pre = pre_roll['beta_1'].mean()
                b1_shift = b1_impact_post - b1_impact_pre
                b1_direction = ("toward C3"
                                if abs(b1_impact_post - b1_c3_post) < abs(b1_impact_pre - b1_c3_post)
                                else "away from C3")

                print(f"   Impact β₁ pre-felling:  {b1_impact_pre:.3f}")
                print(f"   Impact β₁ post-felling: {b1_impact_post:.3f}  (shift: {b1_shift:+.3f})")
                print(f"   C3 β₁ post-felling:     {b1_c3_post:.3f}")
                print(f"   C4 β₁ post-felling:     {b1_c4_post:.3f}")
                print(f"   β₁ direction: {b1_direction}")
                print(f"   Impact β₃ pre:  {pre_roll['beta_3'].mean():.4f}  "
                      f"post: {b3_impact_post:.4f}")
                print(f"   C3 β₃ post:     {b3_c3_post:.4f}")

                rpt.add("Rolling_b1_impact_pre", round(b1_impact_pre, 3), "")
                rpt.add("Rolling_b1_impact_post", round(b1_impact_post, 3), "")
                rpt.add("Rolling_b1_shift", round(b1_shift, 3), "",
                        note=b1_direction)
                rpt.add("Rolling_b1_c3_post", round(b1_c3_post, 3), "")
            else:
                print("   Insufficient pre-felling rolling windows for transition assessment")
        else:
            print("   Insufficient post-felling rolling windows for transition assessment")
    else:
        print("   Cluster centroids not available for transition analysis")

    # Export rolling coefficients CSV
    roll_export = pd.DataFrame()
    if not roll_impact.empty:
        roll_export['Impact_beta1'] = roll_impact['beta_1']
        roll_export['Impact_beta2'] = roll_impact['beta_2']
        roll_export['Impact_beta3'] = roll_impact['beta_3']
        roll_export['Impact_R2']    = roll_impact['R2']
    if not roll_c3.empty:
        roll_export['C3_beta1'] = roll_c3['beta_1']
        roll_export['C3_beta2'] = roll_c3['beta_2']
        roll_export['C3_beta3'] = roll_c3['beta_3']
    if not roll_c4.empty:
        roll_export['C4_beta1'] = roll_c4['beta_1']
        roll_export['C4_beta2'] = roll_c4['beta_2']
        roll_export['C4_beta3'] = roll_c4['beta_3']
    if not roll_export.empty:
        roll_export.to_csv(OUT_10G_ROLLING_CSV, float_format="%.4f")
        print(f"   -> Saved: {OUT_10G_ROLLING_CSV.name}")
    else:
        print("   No rolling data to export")


# ============================================================================
# MAIN
# ============================================================================

def main():
    make_all_dirs()

    print("=" * 72)
    print("SCRIPT 10g — DIAGNOSTICS")
    print("=" * 72)

    # ── Load data ────────────────────────────────────────────────────────────
    print("\n1. Loading data...")
    wells, climate, master, well_locations, valid_tiers = load_clearfell_data()
    print_network_summary(valid_tiers)

    rpt = ReportNumbers()

    # ── Run analyses ─────────────────────────────────────────────────────────
    nw10_broadleaf_trend(wells, rpt)
    clearfell_transect(wells, rpt)
    rolling_coefficients(wells, climate, rpt)

    # ── Export report numbers ────────────────────────────────────────────────
    rpt.save(OUT_10G_REPORT)

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("SCRIPT 10g COMPLETE")
    print("=" * 72)
    print(f"  NW10 trend:          {OUT_10G_NW10_TREND.name}")
    print(f"  Transect figure:     {OUT_10G_TRANSECT_FIG.name}")
    print(f"  Transect data:       {OUT_10G_TRANSECT_CSV.name}")
    print(f"  Rolling coefficients: {OUT_10G_ROLLING_CSV.name}")
    print(f"  Report numbers:      {OUT_10G_REPORT.name} ({len(rpt.rows)} entries)")
    print("=" * 72)


if __name__ == '__main__':
    main()
