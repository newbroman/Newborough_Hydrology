r"""
====================================================================================
10d — SUMMER MINIMA ANALYSIS (DUAL CONTROL)
====================================================================================
Purpose
-------
Evaluates the clearfell effect on the ecologically critical annual summer
minimum depth (Jun–Sep).  Runs against both forest and climate control
centroids.  Each well's gap (well summer min − control centroid summer min)
is compared pre- vs post-felling via Welch t-test.

A mixed-effects model (random intercept per well) provides a pooled
clearfell step estimate with proper uncertainty for each tier.

Outputs
-------
CSV:
  10d_01_summer_minima.csv            — per-well, per-year summer minima
  10d_02_summer_minima_shifts.csv     — per-well pre/post shift summary
  10d_03_mixed_model_results.csv      — mixed-effects model output
  10d_report_numbers.csv              — all citable values

Figures:
  10d_04_summer_minima_forest_ctrl.png  — 4-panel: raw, impact gap, edge gap, ctrl gap
  10d_05_summer_minima_climate_ctrl.png — same for climate control

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
    TIER_COLOURS, ReportNumbers, print_network_summary,
    annual_summer_minimum, forest_control_centroid_summer_min,
    SUMMER_MONTHS,
)
from utils.paths import make_all_dirs, DIR_10
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
OUT_DATA          = DIR_10 / "10d_01_summer_minima.csv"
OUT_SHIFTS        = DIR_10 / "10d_02_summer_minima_shifts.csv"
OUT_MIXED         = DIR_10 / "10d_03_mixed_model_results.csv"
OUT_REPORT        = DIR_10 / "10d_report_numbers.csv"
OUT_FIG_FOREST    = DIR_10 / "10d_04_summer_minima_forest_ctrl.png"
OUT_FIG_CLIMATE   = DIR_10 / "10d_05_summer_minima_climate_ctrl.png"

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


def format_p(p):
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
print("SCRIPT 10d — SUMMER MINIMA ANALYSIS (DUAL CONTROL)")
print("=" * 72)

print("\n1. Loading data...")
wells, climate, master, well_locations, valid_tiers = load_clearfell_data()
print_network_summary(valid_tiers)

# ============================================================================
# COMPUTE SUMMER MINIMA
# ============================================================================
print("2. Computing annual summer minima...")

# Year range
first_year = max(2006, wells.index.min().year)
last_year = min(2025, wells.index.max().year)

# Per-well summer minima
well_mins = {}
for w in ALL_NETWORK_WELLS:
    if w in wells.columns:
        well_mins[w] = annual_summer_minimum(wells[w], first_year, last_year)

# Control centroid summer minima
forest_centroid_mins = forest_control_centroid_summer_min(
    wells, FOREST_CONTROL_WELLS, first_year, last_year)
climate_centroid_mins = forest_control_centroid_summer_min(
    wells, CLIMATE_CONTROL_WELLS, first_year, last_year)

# ============================================================================
# EXPORT: PER-WELL SUMMER MINIMA DATA
# ============================================================================
print("3. Exporting per-well summer minima...")

data_rows = []
for w in ALL_NETWORK_WELLS:
    if w not in well_mins:
        continue
    tier = None
    for t, wlist in TIERS.items():
        if w in wlist:
            tier = t
            break
    for yr, val in well_mins[w].items():
        row = {
            'Well': w.upper(),
            'Tier': tier,
            'Year': yr,
            'Summer_min_m': round(val, 4),
        }
        if yr in forest_centroid_mins:
            row['Forest_ctrl_centroid_m'] = round(forest_centroid_mins[yr], 4)
            row['Gap_forest_m'] = round(val - forest_centroid_mins[yr], 4)
        if yr in climate_centroid_mins:
            row['Climate_ctrl_centroid_m'] = round(climate_centroid_mins[yr], 4)
            row['Gap_climate_m'] = round(val - climate_centroid_mins[yr], 4)
        data_rows.append(row)

data_df = pd.DataFrame(data_rows)
data_df.to_csv(OUT_DATA, index=False)
print(f" -> Saved: {OUT_DATA.name} ({len(data_df)} rows)")

# ============================================================================
# COMPUTE SHIFTS (PRE/POST FELLING)
# ============================================================================
print("4. Computing pre/post shifts...")

# Post-felling years start from the first full summer after Dec 2017 → 2018
POST_YEAR = FELLING_YEAR + 1  # 2018

shift_rows = []
for w in ALL_NETWORK_WELLS:
    if w not in well_mins:
        continue
    tier = None
    for t, wlist in TIERS.items():
        if w in wlist:
            tier = t
            break

    for ctrl_label, centroid_mins in [('Forest', forest_centroid_mins),
                                       ('Climate', climate_centroid_mins)]:
        # Compute gaps
        gaps_pre = []
        gaps_post = []
        for yr, val in well_mins[w].items():
            if yr not in centroid_mins:
                continue
            gap = val - centroid_mins[yr]
            if yr < POST_YEAR:
                gaps_pre.append(gap)
            else:
                gaps_post.append(gap)

        if len(gaps_pre) < 2 or len(gaps_post) < 2:
            continue

        pre_mean = np.mean(gaps_pre)
        post_mean = np.mean(gaps_post)
        shift = post_mean - pre_mean

        # Welch t-test
        t_stat, p_val = sp_stats.ttest_ind(gaps_post, gaps_pre, equal_var=False)

        shift_rows.append({
            'Well': w.upper(),
            'Tier': tier,
            'Control': ctrl_label,
            'N_pre': len(gaps_pre),
            'N_post': len(gaps_post),
            'Pre_mean_gap_m': round(pre_mean, 4),
            'Post_mean_gap_m': round(post_mean, 4),
            'Shift_m': round(shift, 4),
            'Shift_mm': round(shift * 1000, 1),
            't_stat': round(t_stat, 3),
            'p_value': p_val,
            'Sig': p_to_sig(p_val),
        })

shift_df = pd.DataFrame(shift_rows)
shift_df.to_csv(OUT_SHIFTS, index=False)
print(f" -> Saved: {OUT_SHIFTS.name} ({len(shift_df)} rows)")

# Tier-mean summaries
print("\n   Tier-mean shifts (mm):")
for ctrl_label in ['Forest', 'Climate']:
    print(f"\n   {ctrl_label} control:")
    ctrl_shifts = shift_df[shift_df['Control'] == ctrl_label]
    for tier in ['Impact', 'Edge', 'Forest Ctrl', 'Climate Ctrl']:
        tier_shifts = ctrl_shifts[ctrl_shifts['Tier'] == tier]
        if tier_shifts.empty:
            continue
        mean_shift = tier_shifts['Shift_mm'].mean()
        n_sig = (tier_shifts['p_value'] < 0.05).sum()
        print(f"     {tier:<14}  mean = {mean_shift:+6.0f} mm  "
              f"({n_sig}/{len(tier_shifts)} significant)")

# ============================================================================
# MIXED-EFFECTS MODEL (ROBUSTNESS)
# ============================================================================
print("\n5. Running mixed-effects models...")

mixed_rows = []
try:
    import statsmodels.formula.api as smf

    for ctrl_label, centroid_mins in [('Forest', forest_centroid_mins),
                                       ('Climate', climate_centroid_mins)]:
        for tier_name, tier_wells in TIERS.items():
            # Build long-form data for this tier
            records = []
            for w in tier_wells:
                if w not in well_mins:
                    continue
                for yr, val in well_mins[w].items():
                    if yr not in centroid_mins:
                        continue
                    gap = val - centroid_mins[yr]
                    records.append({
                        'well': w,
                        'year': yr,
                        'gap': gap,
                        'post_felling': int(yr >= POST_YEAR),
                        'scraping_era': int(yr >= 2015 and yr < POST_YEAR),
                    })
            if len(records) < 10:
                continue

            lf = pd.DataFrame(records)

            # Check we have multiple wells (needed for random effects)
            if lf['well'].nunique() < 2:
                # Single well (Impact) — fall back to fixed-effects
                model = smf.ols("gap ~ post_felling + scraping_era", data=lf).fit()
                mixed_rows.append({
                    'Control': ctrl_label,
                    'Tier': tier_name,
                    'Model': 'OLS (single well)',
                    'Clearfell_coef_m': round(model.params.get('post_felling', np.nan), 4),
                    'Clearfell_SE_m': round(model.bse.get('post_felling', np.nan), 4),
                    'Clearfell_p': model.pvalues.get('post_felling', np.nan),
                    'Scraping_coef_m': round(model.params.get('scraping_era', np.nan), 4),
                    'Scraping_p': model.pvalues.get('scraping_era', np.nan),
                    'N': len(lf),
                    'N_wells': lf['well'].nunique(),
                })
                continue

            try:
                model = smf.mixedlm("gap ~ post_felling + scraping_era",
                                     data=lf, groups=lf["well"]).fit(reml=True)
                mixed_rows.append({
                    'Control': ctrl_label,
                    'Tier': tier_name,
                    'Model': 'Mixed-effects (random intercept)',
                    'Clearfell_coef_m': round(model.fe_params.get('post_felling', np.nan), 4),
                    'Clearfell_SE_m': round(model.bse_fe.get('post_felling', np.nan), 4) if hasattr(model, 'bse_fe') else np.nan,
                    'Clearfell_p': model.pvalues.get('post_felling', np.nan),
                    'Scraping_coef_m': round(model.fe_params.get('scraping_era', np.nan), 4),
                    'Scraping_p': model.pvalues.get('scraping_era', np.nan),
                    'N': len(lf),
                    'N_wells': lf['well'].nunique(),
                })
            except Exception as e:
                print(f"     [WARNING] Mixed model failed for {ctrl_label}/{tier_name}: {e}")
                # Fall back to OLS with clustered errors
                model = smf.ols("gap ~ post_felling + scraping_era", data=lf).fit(
                    cov_type='cluster', cov_kwds={'groups': lf['well']})
                mixed_rows.append({
                    'Control': ctrl_label,
                    'Tier': tier_name,
                    'Model': 'OLS (clustered SE)',
                    'Clearfell_coef_m': round(model.params.get('post_felling', np.nan), 4),
                    'Clearfell_SE_m': round(model.bse.get('post_felling', np.nan), 4),
                    'Clearfell_p': model.pvalues.get('post_felling', np.nan),
                    'Scraping_coef_m': round(model.params.get('scraping_era', np.nan), 4),
                    'Scraping_p': model.pvalues.get('scraping_era', np.nan),
                    'N': len(lf),
                    'N_wells': lf['well'].nunique(),
                })

except ImportError:
    print("   [WARNING] statsmodels.formula.api not available; skipping mixed models")

mixed_df = pd.DataFrame(mixed_rows)
mixed_df.to_csv(OUT_MIXED, index=False)
print(f" -> Saved: {OUT_MIXED.name} ({len(mixed_df)} rows)")

if not mixed_df.empty:
    print("\n   Mixed-effects results:")
    for _, row in mixed_df.iterrows():
        print(f"     {row['Control']:<10} {row['Tier']:<14}  "
              f"clearfell = {row['Clearfell_coef_m']*1000:+6.0f} mm  "
              f"p = {format_p(row['Clearfell_p'])}  "
              f"({row['Model']})")

# ============================================================================
# FIGURES
# ============================================================================
print("\n6. Generating summer minima figures...")


def plot_summer_minima(ctrl_label, centroid_mins, out_path):
    """4-panel figure: raw minima, impact gap, edge gap, control diagnostic."""
    fig, axes = plt.subplots(4, 1, figsize=(12, 14), dpi=300)
    fig.subplots_adjust(hspace=0.35)

    # Panel (a): Raw summer minima by tier
    ax = axes[0]
    for tier_name, tier_wells in TIERS.items():
        colour = TIER_COLOURS[tier_name]
        # Tier mean per year
        tier_mins = {}
        for w in tier_wells:
            if w not in well_mins:
                continue
            for yr, val in well_mins[w].items():
                if yr not in tier_mins:
                    tier_mins[yr] = []
                tier_mins[yr].append(val)
        if tier_mins:
            years = sorted(tier_mins.keys())
            means = [np.mean(tier_mins[yr]) for yr in years]
            ax.plot(years, np.array(means) * 1000, 'o-', color=colour,
                    ms=4, lw=1.5, label=tier_name)

    ax.axvline(FELLING_YEAR + 0.5, color='#333', ls='-', lw=1.2)
    ax.axvline(2015.3, color='#999', ls='--', lw=0.8)
    ax.set_ylabel('Summer min depth (mm)')
    ax.set_title(f'(a) Annual summer minima by tier — {ctrl_label} control')
    ax.legend(loc='best', frameon=False, fontsize=9)

    # Panels (b)–(d): gap timeseries for impact, edge, control diagnostic
    panels = [
        ('Impact', IMPACT_WELLS, '(b) Impact gap vs control'),
        ('Edge', EDGE_WELLS, '(c) Edge gap vs control'),
    ]

    # Diagnostic: forest ctrl gap vs climate ctrl (or vice versa)
    if ctrl_label == 'Forest':
        panels.append(('Climate Ctrl', CLIMATE_CONTROL_WELLS,
                        '(d) Climate ctrl gap vs forest ctrl'))
    else:
        panels.append(('Forest Ctrl', FOREST_CONTROL_WELLS,
                        '(d) Forest ctrl gap vs climate ctrl'))

    for panel_idx, (tier_name, tier_wells, title) in enumerate(panels):
        ax = axes[panel_idx + 1]
        colour = TIER_COLOURS.get(tier_name, '#888888')

        for w in tier_wells:
            if w not in well_mins:
                continue
            years_w = []
            gaps_w = []
            for yr, val in sorted(well_mins[w].items()):
                if yr in centroid_mins:
                    years_w.append(yr)
                    gaps_w.append((val - centroid_mins[yr]) * 1000)
            if years_w:
                ax.plot(years_w, gaps_w, 'o-', color=colour, ms=3,
                        lw=0.8, alpha=0.5, label=w.upper())

        # Tier mean gap
        tier_gap_means = {}
        for w in tier_wells:
            if w not in well_mins:
                continue
            for yr, val in well_mins[w].items():
                if yr in centroid_mins:
                    if yr not in tier_gap_means:
                        tier_gap_means[yr] = []
                    tier_gap_means[yr].append(val - centroid_mins[yr])
        if tier_gap_means:
            years = sorted(tier_gap_means.keys())
            means = [np.mean(tier_gap_means[yr]) * 1000 for yr in years]
            ax.plot(years, means, 's-', color='black', ms=5, lw=2,
                    label='Tier mean', zorder=5)

        ax.axvline(FELLING_YEAR + 0.5, color='#333', ls='-', lw=1.2)
        ax.axvline(2015.3, color='#999', ls='--', lw=0.8)
        ax.axhline(0, color='grey', ls=':', lw=0.5)
        ax.set_ylabel('Gap (mm)')
        ax.set_title(title)
        ax.legend(loc='best', frameon=False, fontsize=8, ncol=2)

    axes[-1].set_xlabel('Year')
    fig.suptitle(
        f'Summer minima analysis — {ctrl_label} control centroid',
        fontsize=13, y=0.98)
    fig.savefig(out_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f" -> Saved: {out_path.name}")


plot_summer_minima('Forest', forest_centroid_mins, OUT_FIG_FOREST)
plot_summer_minima('Climate', climate_centroid_mins, OUT_FIG_CLIMATE)

# ============================================================================
# EXPORT: REPORT NUMBERS
# ============================================================================
print("\n7. Exporting report numbers...")
rpt = ReportNumbers()

for _, row in shift_df.iterrows():
    rpt.add(f"SummerMin_{row['Control']}_{row['Well']}_shift",
            row['Shift_m'],
            well=row['Well'], era="Post_felling",
            note=f"p={format_p(row['p_value'])}, "
                 f"n_pre={row['N_pre']}, n_post={row['N_post']}")

# Tier means
for ctrl_label in ['Forest', 'Climate']:
    ctrl_shifts = shift_df[shift_df['Control'] == ctrl_label]
    for tier in ['Impact', 'Edge', 'Forest Ctrl', 'Climate Ctrl']:
        tier_shifts = ctrl_shifts[ctrl_shifts['Tier'] == tier]
        if tier_shifts.empty:
            continue
        rpt.add(f"SummerMin_{ctrl_label}_{tier}_mean_shift",
                tier_shifts['Shift_m'].mean(),
                well=tier,
                note=f"n_wells={len(tier_shifts)}, "
                     f"n_sig={int((tier_shifts['p_value']<0.05).sum())}")

# Mixed-effects results
for _, row in mixed_df.iterrows():
    rpt.add(f"MixedModel_{row['Control']}_{row['Tier']}_clearfell",
            row['Clearfell_coef_m'],
            well=row['Tier'],
            note=f"p={format_p(row['Clearfell_p'])}, "
                 f"model={row['Model']}, N={row['N']}")

n_saved = rpt.save(OUT_REPORT)
print(f" -> Saved: {OUT_REPORT.name} ({n_saved} rows)")

# ============================================================================
# CONSOLE SUMMARY
# ============================================================================
print("\n" + "=" * 72)
print("SUMMER MINIMA SUMMARY")
print("=" * 72)
for ctrl_label in ['Forest', 'Climate']:
    ctrl_s = shift_df[shift_df['Control'] == ctrl_label]
    print(f"\n  {ctrl_label} control:")
    print(f"  {'Tier':<14} {'Mean shift (mm)':>16} {'n sig':>8}")
    print(f"  {'-'*40}")
    for tier in ['Impact', 'Edge', 'Forest Ctrl', 'Climate Ctrl']:
        ts = ctrl_s[ctrl_s['Tier'] == tier]
        if ts.empty:
            continue
        mean_mm = ts['Shift_mm'].mean()
        n_sig = (ts['p_value'] < 0.05).sum()
        print(f"  {tier:<14} {mean_mm:>+16.0f} {n_sig:>4}/{len(ts)}")

print("=" * 72)
print("Script 10d complete.\n")
