r"""

====================================================================================
10d — SEASONAL BACI ANALYSIS (DUAL CONTROL): SUMMER MINIMA + SPRING MEANS
====================================================================================
Purpose
-------
Evaluates the clearfell effect on two annual seasonal metrics, run through
the IDENTICAL code path against both forest and climate control centroids.
Each well's gap (well value − control centroid value) is compared pre- vs
post-felling via Welch t-test.

  * Summer minimum (Jun–Sep) — the ecologically critical drought low.
  * Spring mean (Mar–May)    — the season the Curreli ecological
                               thresholds are defined on.

Both metrics reduce a well to ONE value per year, so they are interchangeable
as the BACI response variable: same wells, same years, same N, no power cost.
The summer minimum is an extreme-order statistic; the spring mean averages
three MAM months and is correspondingly less noisy.  The spring mean is NOT a
replacement for the summer minimum — both are reported.

A mixed-effects model (random intercept per well) provides a pooled
step estimate with proper uncertainty for each tier, for each metric.

Outputs
-------
CSV:
  10d_01_summer_minima.csv            — per-well, per-year summer minima
  10d_02_summer_minima_shifts.csv     — per-well pre/post shift summary
  10d_03_mixed_model_results.csv      — mixed-effects model output (summer)
  10d_06_spring_means.csv             — per-well, per-year spring means
  10d_07_spring_means_shifts.csv      — per-well pre/post shift summary (spring)
  10d_08_spring_mixed_model_results.csv — mixed-effects model output (spring)
  10d_report_numbers.csv              — all citable values, BOTH metrics
                                        (distinguished by Parameter key)

Figures:
  10d_04_summer_minima_forest_ctrl.png  — 4-panel: raw, impact gap, edge gap, ctrl gap
  10d_05_summer_minima_climate_ctrl.png — same for climate control
  10d_09_spring_means_forest_ctrl.png   — spring sibling of 10d_04
  10d_10_spring_means_climate_ctrl.png  — spring sibling of 10d_05

References
----------
Hollingham (2026), §4.6.  Part of the Script 10 clearfell analysis suite.
====================================================================================
"""

__version__ = "1.8.0"  # Hollingham (2026) — 2026-08-29. CLEARFELL_DATE rename (T-17).
#   No value changes; verified by re-run against the 2026-08-29 pipeline outputs.
# v1.7.0  # Hollingham (2026) — 2026-08-13 (spring-mean MAM analysis alongside the summer minimum)
#
# 1.7.0 — Added the annual SPRING MEAN (Mar-May) as a second seasonal metric,
#         run through the identical clearfell BACI code path as the summer
#         minimum.  The per-metric computation (extraction → per-well CSV →
#         pre/post Welch shifts → mixed-effects models → figures → report
#         rows) moved into run_metric(), driven by the _METRICS spec list; the
#         module loads once and loops.  The summer path is unchanged and its
#         outputs (10d_01–10d_05, and the summer prefix of 10d_report_numbers)
#         are byte-identical.  The ReportNumbers accumulator is created once
#         and saved once, outside the metric loop (spring rows append after
#         the summer rows, preserving the summer prefix).  Spring metric and
#         its 3-of-3 completeness rule come from clearfell_common (sourced from
#         config.MSL_SPRING_MONTHS / MSL_MIN_MONTHS_PER_SPRING) — no new local
#         constants.  Mirrors the 09c v1.5.0 seasonal refactor.
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
    CLEARFELL_DATE, SCRAPING_DATE, SCRAPING_DATE_2, FELLING_YEAR,
    TIER_COLOURS, ReportNumbers, print_network_summary,
    annual_summer_minimum, forest_control_centroid_summer_min,
    annual_spring_mean, forest_control_centroid_spring_mean,
    SUMMER_MONTHS, SPRING_MONTHS, SPRING_MIN_MEASURED,
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
OUT_FIG_FOREST    = DIR_10 / "10d_04_summer_minima_forest_ctrl.png"
OUT_FIG_CLIMATE   = DIR_10 / "10d_05_summer_minima_climate_ctrl.png"
# Spring-mean siblings (new in v1.7.0).
OUT_SPRING_DATA        = DIR_10 / "10d_06_spring_means.csv"
OUT_SPRING_SHIFTS      = DIR_10 / "10d_07_spring_means_shifts.csv"
OUT_SPRING_MIXED       = DIR_10 / "10d_08_spring_mixed_model_results.csv"
OUT_FIG_SPRING_FOREST  = DIR_10 / "10d_09_spring_means_forest_ctrl.png"
OUT_FIG_SPRING_CLIMATE = DIR_10 / "10d_10_spring_means_climate_ctrl.png"
# Shared registry (both metrics).
OUT_REPORT        = DIR_10 / "10d_report_numbers.csv"

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
# SEASONAL METRIC SPECS
# ============================================================================
# Both metrics reduce a well to one value per year, so they are
# interchangeable as the BACI response variable: same wells, same years,
# same N, no power cost.  The summer minimum is an extreme-order statistic
# (the lowest single Jun-Sep month) and carries the drought-stress
# interpretation; the spring mean averages three MAM months, is less noisy,
# and is the season the Curreli ecological thresholds are defined on.
# Neither replaces the other — both are reported.  Only the extraction
# function, completeness rule, column/parameter labels, output paths and
# figure text vary; the code path (run_metric) is identical.
_METRICS = [
    {
        "key": "summer_min",
        "name": "summer minima",
        "months": SUMMER_MONTHS,
        "metric_fn": annual_summer_minimum,
        "centroid_fn": forest_control_centroid_summer_min,
        "min_measured": 2,
        "value_col": "Summer_min_m",
        # Report-number key stems — the committed summer keys, unchanged.
        "rpt_prefix": "SummerMin",
        "mixed_prefix": "MixedModel",
        "comparator_key": "Clearfell_equilibration_slope_WMC3",
        # Figure text pieces (summer strings are the committed ones).
        "fig_ylabel": "Summer min depth (mm)",
        "fig_panel_a": "Annual summer minima",
        "fig_suptitle": "Summer minima analysis",
        "out_data": OUT_DATA,
        "out_shifts": OUT_SHIFTS,
        "out_mixed": OUT_MIXED,
        "fig_forest": OUT_FIG_FOREST,
        "fig_climate": OUT_FIG_CLIMATE,
    },
    {
        "key": "spring_mean",
        "name": "spring means",
        "months": SPRING_MONTHS,
        "metric_fn": annual_spring_mean,
        "centroid_fn": forest_control_centroid_spring_mean,
        "min_measured": SPRING_MIN_MEASURED,
        "value_col": "Spring_mean_m",
        "rpt_prefix": "SpringMean",
        "mixed_prefix": "MixedModelSpring",
        "comparator_key": "Clearfell_equilibration_slope_WMC3_spring",
        "fig_ylabel": "Spring mean depth (mm)",
        "fig_panel_a": "Annual spring means",
        "fig_suptitle": "Spring means analysis",
        "out_data": OUT_SPRING_DATA,
        "out_shifts": OUT_SPRING_SHIFTS,
        "out_mixed": OUT_SPRING_MIXED,
        "fig_forest": OUT_FIG_SPRING_FOREST,
        "fig_climate": OUT_FIG_SPRING_CLIMATE,
    },
]


# ============================================================================
# FIGURES
# ============================================================================
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


def plot_seasonal_minima(spec, well_mins, ctrl_label, centroid_mins, out_path):
    """4-panel figure: raw metric, impact gap, edge gap, control diagnostic.

    Parameterised on the seasonal metric via ``spec`` (see ``_METRICS``);
    only the value column and the figure text pieces vary.  The summer
    figures reproduce byte-identically.
    """
    fig, axes = plt.subplots(4, 1, figsize=(12, 14), dpi=300)
    fig.subplots_adjust(hspace=0.35)

    # Panel (a): Raw seasonal metric by tier
    ax = axes[0]
    for tier_name, tier_wells in TIERS.items():
        colour = TIER_COLOURS[tier_name]
        # Tier mean per year — FIXED MEMBERSHIP (Defect A, v1.4.0):
        # a tier-year is included only if EVERY well in the tier roster
        # has a value that year.  Years where one or more roster wells
        # are missing are omitted, so the plotted tier mean is always an
        # average of the same well set.  This mirrors the v1.7.0
        # clearfell_common.compute_control_centroid() rule and prevents
        # the one-well-average-masquerading-as-tier-mean artefact (e.g.
        # the spurious Coastal +0.5 m peak at 2019).
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
    ax.set_ylabel(spec["fig_ylabel"])
    ax.set_title(f'(a) {spec["fig_panel_a"]} by tier — {ctrl_label} control')
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
        f'{spec["fig_suptitle"]} — {ctrl_label} control centroid',
        fontsize=13, y=0.98)
    render_figure(fig, out_path, facecolor='white', full_page=True)
    plt.close(fig)
    saved(f"{out_path.name}")


# ============================================================================
# PER-METRIC ANALYSIS
# ============================================================================
def run_metric(spec, wells, wells_provenance, first_year, last_year, rpt):
    """Run the full dual-control clearfell BACI analysis for ONE metric.

    Identical code path for the summer minimum and the spring mean — only
    the extraction function, completeness rule, column/parameter labels,
    output paths and figure text vary, all supplied by ``spec`` (see
    ``_METRICS``).  Report-number rows for this metric are appended to the
    shared ``rpt`` accumulator (created and saved once by the caller).
    """
    hr()
    info(f"Metric: {spec['name']}")

    # ── 2. Compute the annual seasonal metric ─────────────────────────────
    phase(2, f"Computing annual {spec['name']}")
    # Per-well seasonal values — pass provenance so phantom values with
    # fewer than the required number of measured in-season months are
    # excluded (Defect E fix).
    well_mins = {}
    n_interpolated_per_well_year = {}
    for w in ALL_NETWORK_WELLS:
        if w in wells.columns:
            prov_w = (wells_provenance[w]
                      if w in wells_provenance.columns else None)
            well_mins[w] = spec["metric_fn"](
                wells[w], first_year, last_year,
                provenance=prov_w, min_measured=spec["min_measured"],
            )
            # Count how many cells the well DID have flagged as
            # 'interpolated' in each year's in-season window — for
            # transparency in the output CSV. (These cells are excluded
            # from the metric computation above; the count is purely a
            # diagnostic so reviewers can see which years sit close to
            # the threshold.)
            if prov_w is not None:
                for yr in range(first_year, last_year + 1):
                    mask = ((wells[w].index.year == yr)
                            & (wells[w].index.month.isin(spec["months"])))
                    n_interp = int((prov_w[mask] == 'interpolated').sum())
                    n_interpolated_per_well_year[(w, yr)] = n_interp

    # Control centroid seasonal values — also pass provenance through.
    forest_centroid_mins = spec["centroid_fn"](
        wells, FOREST_CONTROL_WELLS, first_year, last_year,
        wells_provenance=wells_provenance, min_measured=spec["min_measured"])
    climate_centroid_mins = spec["centroid_fn"](
        wells, CLIMATE_CONTROL_WELLS, first_year, last_year,
        wells_provenance=wells_provenance, min_measured=spec["min_measured"])

    # ── 3. Export per-well seasonal data ──────────────────────────────────
    phase(3, f"Exporting per-well {spec['name']}")
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
                spec["value_col"]: round(val, 4),
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
    data_df.to_csv(spec["out_data"], index=False)
    saved(f"{spec['out_data'].name} ({len(data_df)} rows)")

    # ── 4. Compute shifts (pre/post felling) ──────────────────────────────
    phase(4, "Computing pre/post shifts")
    # Post-felling years start from the first full season after Dec 2017 → 2018
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
    shift_df.to_csv(spec["out_shifts"], index=False)
    saved(f"{spec['out_shifts'].name} ({len(shift_df)} rows)")

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

    # ── 5. Mixed-effects models (robustness) ──────────────────────────────
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
    mixed_df.to_csv(spec["out_mixed"], index=False)
    saved(f"{spec['out_mixed'].name} ({len(mixed_df)} rows)")

    if not mixed_df.empty:
        print("\n   Mixed-effects results:")
        for _, row in mixed_df.iterrows():
            print(f"     {row['Control']:<10} {row['Tier']:<14}  "
                  f"clearfell = {row['Clearfell_coef_m']*1000:+6.0f} mm  "
                  f"p = {format_p(row['Clearfell_p'])}  "
                  f"({row['Model']})")

    # ── 6. Figures ────────────────────────────────────────────────────────
    phase(6, f"Generating {spec['name']} figures")
    plot_seasonal_minima(spec, well_mins, 'Forest', forest_centroid_mins,
                         spec["fig_forest"])
    plot_seasonal_minima(spec, well_mins, 'Climate', climate_centroid_mins,
                         spec["fig_climate"])

    # ── 7. Report numbers (appended to the shared accumulator) ────────────
    for _, row in shift_df.iterrows():
        rpt.add(f"{spec['rpt_prefix']}_{row['Control']}_{row['Well']}_shift",
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
            rpt.add(f"{spec['rpt_prefix']}_{ctrl_label}_{tier}_mean_shift",
                    tier_shifts['Shift_m'].mean(),
                    well=tier,
                    note=f"n_wells={len(tier_shifts)}, "
                         f"n_sig={int((tier_shifts['p_value']<0.05).sum())}")

    # Mixed-effects results
    for _, row in mixed_df.iterrows():
        rpt.add(f"{spec['mixed_prefix']}_{row['Control']}_{row['Tier']}_clearfell",
                row['Clearfell_coef_m'],
                well=row['Tier'],
                note=f"p={format_p(row['Clearfell_p'])}, "
                     f"model={row['Model']}, N={row['N']}")

    # Clearfell no-decay comparator (Task G): post-felling OLS slope of WMC3's
    # seasonal-metric forest-control gap. Matched-currency reference for the
    # CEH36 scrape equilibration decay (09c). Reports the SHAPE (flatness),
    # not the step — the clearfell step is a monthly/mean effect and is
    # near-zero in the summer minimum. Plain OLS, no AR(1).
    if 'wmc3' in well_mins:
        wmc3_gap = {yr: well_mins['wmc3'][yr] - forest_centroid_mins[yr]
                    for yr in well_mins['wmc3'] if yr in forest_centroid_mins}
        post_years = sorted(yr for yr in wmc3_gap if yr >= POST_YEAR)
        if len(post_years) >= EQUIL_MIN_FIT_POINTS:
            post_vals = [wmc3_gap[yr] for yr in post_years]
            r = sp_stats.linregress(post_years, post_vals)
            rpt.add(spec["comparator_key"],
                    float(r.slope),
                    well="WMC3", era="Post_felling",
                    note=f"OLS Gap_forest_m {post_years[0]}-{post_years[-1]}, "
                         f"p={format_p(r.pvalue)}, R2={r.rvalue**2:.2f}, "
                         f"n={len(post_years)} (plain OLS, no AR1; no-decay comparator "
                         f"to 09c scrape equilibration; flatness only, not a step)")
            print(f"  Clearfell comparator (WMC3 Gap_forest_m {post_years[0]}-"
                  f"{post_years[-1]}): slope {r.slope*1000:+.1f} mm/yr, "
                  f"p={format_p(r.pvalue)} — no-decay reference")
        else:
            warn("WMC3: insufficient post-felling points for no-decay comparator")
    else:
        warn("WMC3 not in well_mins — skipping clearfell no-decay comparator")

    # ── Console summary for this metric ───────────────────────────────────
    print("\n" + "=" * 72)
    print(f"{spec['name'].upper()} SUMMARY")
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


# ============================================================================
# LOAD DATA
# ============================================================================
banner("10d", "SEASONAL BACI ANALYSIS (DUAL CONTROL) — "
              "SUMMER MINIMA + SPRING MEANS", version=__version__)

phase(1, "Loading data")
wells, wells_provenance, climate, master, well_locations, valid_tiers = load_clearfell_data()
print_network_summary(valid_tiers)

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

# ============================================================================
# RUN BOTH METRICS THROUGH THE IDENTICAL CODE PATH
# ============================================================================
# The ReportNumbers accumulator is created ONCE and saved ONCE, outside the
# metric loop: the summer rows are added first (byte-identical to the
# committed prefix) and the spring rows append after them.
rpt = ReportNumbers()

for spec in _METRICS:
    run_metric(spec, wells, wells_provenance, first_year, last_year, rpt)

# ============================================================================
# EXPORT: REPORT NUMBERS (shared registry, both metrics)
# ============================================================================
phase(7, "Exporting report numbers")
n_saved = rpt.save(OUT_REPORT)
saved(f"{OUT_REPORT.name} ({n_saved} rows)")

print("\nScript 10d complete.\n")
