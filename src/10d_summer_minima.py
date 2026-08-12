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

__version__ = "1.6.0"  # Hollingham (2026) — 2026-07-14
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)

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
from utils.config import EQUIL_MIN_FIT_POINTS
from utils.render_utils import render_figure
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
banner("10d", "SUMMER MINIMA ANALYSIS (DUAL CONTROL)", version=__version__)

phase(1, "Loading data")
wells, wells_provenance, climate, master, well_locations, valid_tiers = load_clearfell_data()
print_network_summary(valid_tiers)

# ============================================================================
# COMPUTE SUMMER MINIMA
# ============================================================================
phase(2, "Computing annual summer minima")
# Year range — annual analyses use 2011+ rather than tracking PRE_FELL_START.
# Rationale: 2011 is the first year all 17 network wells have complete
# observed Jun–Sep coverage.  Monthly analyses (10a, 10b, 10e, 10h) adopt
# CEH34's donor-regression hindcast to push their window to 2010-07-01,
# but in an annual minimum-of-summer-months estimator a single hindcasted
# month could *become* the year's minimum and concentrate its uncertainty
# directly into the BACI input.  The asymmetry — monthly analyses tolerate
# hindcasts well; annual extremes tolerate them poorly — justifies the
# different cutoff here.  See CHAPTER_FLAGS_TO_REVIEW.md.
first_year = max(2011, wells.index.min().year)
last_year = min(2025, wells.index.max().year)

# Per-well summer minima — pass provenance so phantom summer minima with
# fewer than 2 measured Jun-Sep months are excluded (Defect E fix).
well_mins = {}
n_interpolated_per_well_year = {}
for w in ALL_NETWORK_WELLS:
    if w in wells.columns:
        prov_w = (wells_provenance[w]
                  if w in wells_provenance.columns else None)
        well_mins[w] = annual_summer_minimum(
            wells[w], first_year, last_year,
            provenance=prov_w, min_measured=2,
        )
        # Count how many cells the well DID have flagged as 'interpolated'
        # in each year's Jun-Sep window — for transparency in the output
        # CSV. (These cells are excluded from the minimum computation
        # above; the count is purely a diagnostic so reviewers can see
        # which years sit close to the threshold.)
        if prov_w is not None:
            for yr in range(first_year, last_year + 1):
                mask = ((wells[w].index.year == yr)
                        & (wells[w].index.month.isin(SUMMER_MONTHS)))
                n_interp = int((prov_w[mask] == 'interpolated').sum())
                n_interpolated_per_well_year[(w, yr)] = n_interp

# Control centroid summer minima — also pass provenance through.
forest_centroid_mins = forest_control_centroid_summer_min(
    wells, FOREST_CONTROL_WELLS, first_year, last_year,
    wells_provenance=wells_provenance, min_measured=2)
climate_centroid_mins = forest_control_centroid_summer_min(
    wells, CLIMATE_CONTROL_WELLS, first_year, last_year,
    wells_provenance=wells_provenance, min_measured=2)

# ============================================================================
# EXPORT: PER-WELL SUMMER MINIMA DATA
# ============================================================================
phase(3, "Exporting per-well summer minima")
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
            'n_interpolated': n_interpolated_per_well_year.get((w, yr), 0),
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
saved(f"{OUT_DATA.name} ({len(data_df)} rows)")

# ============================================================================
# COMPUTE SHIFTS (PRE/POST FELLING)
# ============================================================================
phase(4, "Computing pre/post shifts")
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
saved(f"{OUT_SHIFTS.name} ({len(shift_df)} rows)")

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
phase(5, "Running mixed-effects models")
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
                warn(f"Mixed model failed for {ctrl_label}/{tier_name}: {e}")
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
    warn("statsmodels.formula.api not available; skipping mixed models")

mixed_df = pd.DataFrame(mixed_rows)
mixed_df.to_csv(OUT_MIXED, index=False)
saved(f"{OUT_MIXED.name} ({len(mixed_df)} rows)")

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
phase(6, "Generating summer minima figures")
def _consecutive_year_series(years, values):
    """Reindex a (years, values) pair onto a complete consecutive-year axis.

    Returns (full_years, full_values) where full_years spans
    min(years)..max(years) inclusive and full_values carries np.nan for
    any calendar year absent from the input.  Plotting the result with
    matplotlib breaks the connecting line at every NaN (genuine gap)
    while still drawing markers for years that have data.

    If ``years`` is empty, returns two empty lists.
    """
    if not years:
        return [], []
    lookup = dict(zip(years, values))
    full_years = list(range(min(years), max(years) + 1))
    full_values = [lookup.get(yr, np.nan) for yr in full_years]
    return full_years, full_values


def plot_summer_minima(ctrl_label, centroid_mins, out_path):
    """4-panel figure: raw minima, impact gap, edge gap, control diagnostic."""
    fig, axes = plt.subplots(4, 1, figsize=(12, 14), dpi=300)
    fig.subplots_adjust(hspace=0.35)

    # Panel (a): Raw summer minima by tier
    ax = axes[0]
    for tier_name, tier_wells in TIERS.items():
        colour = TIER_COLOURS[tier_name]
        # Tier mean per year — FIXED MEMBERSHIP (Defect A, v1.4.0):
        # a tier-year is included only if EVERY well in the tier roster
        # has a summer minimum that year.  Years where one or more
        # roster wells are missing are omitted, so the plotted tier
        # mean is always an average of the same well set.  This mirrors
        # the v1.7.0 clearfell_common.compute_control_centroid() rule
        # and prevents the one-well-average-masquerading-as-tier-mean
        # artefact (e.g. the spurious Coastal +0.5 m peak at 2019).
        tier_mins = {}
        for w in tier_wells:
            if w not in well_mins:
                continue
            for yr, val in well_mins[w].items():
                if yr not in tier_mins:
                    tier_mins[yr] = []
                tier_mins[yr].append(val)
        # Require all roster wells present in the loaded data; a year
        # is plotted only if its sample count equals that roster size.
        roster_size = sum(1 for w in tier_wells if w in well_mins)
        complete_years = sorted(
            yr for yr, vals in tier_mins.items()
            if roster_size > 0 and len(vals) == roster_size
        )
        if complete_years:
            means = [np.mean(tier_mins[yr]) * 1000 for yr in complete_years]
            # Defect B (v1.4.0): reindex onto a consecutive-year axis so
            # the line breaks at missing years instead of bridging them.
            plot_years, plot_means = _consecutive_year_series(
                complete_years, means)
            ax.plot(plot_years, plot_means, 'o-', color=colour,
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
                # Defect B (v1.4.0): break the line at missing years.
                plot_years, plot_gaps = _consecutive_year_series(
                    years_w, gaps_w)
                ax.plot(plot_years, plot_gaps, 'o-', color=colour, ms=3,
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
            # Defect B (v1.4.0): break the line at missing years.
            # NOTE: the panel (b)-(d) tier-mean retains its NaN-skipping
            # membership (a year is included if >=1 roster well has a
            # gap).  The brief scopes the fixed-membership rule to the
            # panel (a) tier means only; changing the (b)-(d) tier-mean
            # membership is out of scope for this fix.
            plot_years, plot_means = _consecutive_year_series(years, means)
            ax.plot(plot_years, plot_means, 's-', color='black', ms=5, lw=2,
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
    render_figure(fig, out_path, facecolor='white', full_page=True)
    plt.close(fig)
    saved(f"{out_path.name}")


plot_summer_minima('Forest', forest_centroid_mins, OUT_FIG_FOREST)
plot_summer_minima('Climate', climate_centroid_mins, OUT_FIG_CLIMATE)

# ============================================================================
# EXPORT: REPORT NUMBERS
# ============================================================================
phase(7, "Exporting report numbers")
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

# Clearfell no-decay comparator (Task G): post-felling OLS slope of WMC3's
# summer-minimum forest-control gap. Matched-currency reference for the CEH36
# scrape equilibration decay (09c). Reports the SHAPE (flatness), not the step
# — the clearfell step is a monthly/mean effect and is near-zero in the summer
# minimum. Plain OLS, no AR(1).
if 'wmc3' in well_mins:
    wmc3_gap = {yr: well_mins['wmc3'][yr] - forest_centroid_mins[yr]
                for yr in well_mins['wmc3'] if yr in forest_centroid_mins}
    post_years = sorted(yr for yr in wmc3_gap if yr >= POST_YEAR)
    if len(post_years) >= EQUIL_MIN_FIT_POINTS:
        post_vals = [wmc3_gap[yr] for yr in post_years]
        r = sp_stats.linregress(post_years, post_vals)
        rpt.add("Clearfell_equilibration_slope_WMC3",
                float(r.slope),
                well="WMC3", era="Post_felling",
                note=f"OLS Gap_forest_m {post_years[0]}-{post_years[-1]}, "
                     f"p={format_p(r.pvalue)}, R2={r.rvalue**2:.2f}, "
                     f"n={len(post_years)} (plain OLS, no AR1; no-decay comparator "
                     f"to 09c scrape equilibration; flatness only, not a step)")
        print(f"  Clearfell comparator (WMC3 Gap_forest_m {post_years[0]}-"
              f"{post_years[-1]}): slope {r.slope*1000:+.1f} mm/yr, "
              f"p={format_p(r.pvalue)} \u2014 no-decay reference")
    else:
        warn("WMC3: insufficient post-felling points for no-decay comparator")
else:
    warn("WMC3 not in well_mins \u2014 skipping clearfell no-decay comparator")

n_saved = rpt.save(OUT_REPORT)
saved(f"{OUT_REPORT.name} ({n_saved} rows)")

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
