r"""

====================================================================================
10j — DIRECT IMPACT-vs-EDGE CONTRASTS (NO EXTERNAL CONTROL)
====================================================================================

A pooled BACI-style estimator that uses the Edge tier as the spatial
counterfactual for the Impact tier rather than a separate Forest or
Climate control. The Edge wells are within or immediately adjacent to
the felled compartment but experienced much less of the felling
treatment, while sharing nearly every confounder with the Impact tier
(WMC3): coastal-retreat gradient, climate forcing, regional
groundwater drift.

The estimator therefore does not require an easting × time covariate or
a counterfactual-tier model — the spatial buffer is doing the work that
those covariates do in 10a. This is offered as the cleanest available
test of the felling response at WMC3 against the closest spatial control.

Two parallel analyses:

  1. MONTHLY-MEAN CONTRAST
     - Stacked panel of monthly depths for Impact + Edge wells
     - Fit  h ~ const + CWB + Scraped1 + Post + Impact + Impact:Scraped1
                  + Impact:Post + Impact:CWB + well-FE
     - OLS with cluster-robust SE on well to handle within-well autocorr
     - Impact:Post is the differential felling step (Impact − Edge)
     - Impact:Scraped1 is the differential scraping step (Impact − Edge),
       included because the Impact tier is inside the 2015 scraping
       footprint while the Edge tier is not

  2. SUMMER MINIMA CONTRAST
     - Reads 10d_01_summer_minima.csv (Jun–Sep annual minima already
       computed under the n_interpolated ≤ 0 cleaning rule)
     - Filters to Impact + Edge tiers
     - Fit  summer_min ~ const + Post + Impact + Impact:Post + well-FE
     - Mixed-effects model with a random intercept per well (Edge has
       n>1 wells; Impact has one well so the random intercept variance
       collapses to zero — the model degrades gracefully)
     - Impact:Post is the differential summer-minimum step

The two values are written to the site-observations registry so
downstream consumers (e.g. report-figure generation, future scenario
work) can read them as live pipeline numbers rather than caching from
this script's output.

Dependencies:
  utils/clearfell_common.py — well lists, dates, data loading, CWB,
                              PRE_FELL_START
  utils/site_observations  — registry of site-wide observations
  utils/paths              — output paths
  outputs/.../10d_01_summer_minima.csv — summer-minima frame produced
                                         by 10d under the shared
                                         interpolation / completeness
                                         rules

Outputs:
  outputs/10_clearfell_baci/10j_01_monthly_contrast_results.csv
  outputs/10_clearfell_baci/10j_02_summer_contrast_results.csv
  outputs/10_clearfell_baci/10j_03_contrast_timeseries.png
  outputs/10_clearfell_baci/10j_04_summer_minima_contrast.png
  outputs/10_clearfell_baci/10j_report_numbers.csv

  (also updates pipeline_site_observations.csv with four entries)
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from utils.paths import (
    make_all_dirs, OUT_10J_MONTHLY_RESULTS, OUT_10J_SUMMER_RESULTS,
    OUT_10J_TIMESERIES_FIG, OUT_10J_SUMMER_FIG, OUT_10J_REPORT, OUT_10D_DATA,
)
from utils.clearfell_common import (
    load_clearfell_data, print_network_summary,
    INTERVENTION_DATE, SCRAPING_DATE, PRE_FELL_START,
    IMPACT_WELLS, EDGE_WELLS,
    compute_cwb, wmc3_usable_summer_years,
    ReportNumbers, TIER_COLOURS,
)
from utils.site_observations import update_site_observation
from utils.render_utils import render_figure

__version__ = "1.3.0"  # Hollingham (2026) — 2026-07-04
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
# 1.2.2 — figure_monthly_contrast(): fix IndexError — pre/post masks now
#          computed per-series on each series' own index (Impact 172 rows,
#          Edge 180 rows); shared mask caused length mismatch in pandas.
# 1.2.1 — figure_monthly_contrast(): added pre/post period mean lines
#          (dotted, colour-matched) to both panels, with annotations
#          showing the per-zone and gap-series shifts.
# 1.2.0 — Summer-minima model moved onto the WMC3-gatekeeper year
#         panel.  fit_summer_contrast() and figure_summer_contrast()
#         now take panel_years (from clearfell_common.
#         wmc3_usable_summer_years) and select years by it instead of
#         the old per-row `n_interpolated == 0` filter.  A year enters
#         the summer analysis if the Impact well WMC3 has a usable
#         Jun-Sep record (at most one missing month); on the current
#         data this is 2011 + 2013-2018 + 2020-2025 (2012 and 2019
#         dropped).  The n_interpolated filter is removed — every row
#         in 10d_01 has already passed the Defect-E min_measured=2 rule.
#         This is the SAME year panel Script 10l uses, so the 10l
#         four-zone Impact-Edge contrast and this two-zone estimate are
#         again directly comparable (the 10l cross-check).  The summer
#         contrast and 10j's two summer site-observations regenerate;
#         the monthly model is untouched.
# 1.1.0 — Bug fix in fit_summer_contrast(): the post-felling indicator
#         was `Year >= INTERVENTION_DATE.year` (2017), which mislabelled
#         the Jun-Sep 2017 summer minimum as post-felling.  That summer
#         occurred ~6 months BEFORE the December 2017 felling and cannot
#         carry a felling signal.  Corrected to `Year >= year + 1`
#         (2018) — the first FULL post-felling summer — matching
#         Script 10d (POST_YEAR = FELLING_YEAR + 1) and Script 10l.
#         The summer contrast and the two summer site-observation
#         entries regenerate; the monthly model is unaffected (its
#         Post indicator is date-based, `date >= INTERVENTION_DATE`,
#         and was already correct).  Surfaced by the Script 10l
#         four-zone summer cross-check, which disagreed with 10j by
#         ~30 mm purely on this one-summer definition difference.
#         Also: figure_summer_contrast() now reindexes each trajectory
#         onto continuous years so a missing summer minimum (e.g. WMC3
#         has no 2019 summer minimum) breaks the line rather than being
#         bridged by a straight segment across the gap.
# 1.0.0 — Initial.  Direct Impact-vs-Edge BACI contrast at monthly and
#         annual-summer-minimum resolution.  Reads PRE_FELL_START,
#         SCRAPING_DATE, INTERVENTION_DATE and well lists from
#         clearfell_common; writes four site-observation entries.
#         No hardcoded site-specific values.


# ============================================================================
# MODEL FITTING
# ============================================================================

def _well_fe_design(df, ref_cols):
    """Build a design matrix with well fixed effects (drop-first dummies).

    Parameters
    ----------
    df : DataFrame with 'well' and the reference columns in ref_cols.
    ref_cols : list of column names to include before the well-FE block.

    Returns
    -------
    X : DataFrame with constant, ref_cols, and well-FE columns.
    """
    well_dummies = pd.get_dummies(df['well'], prefix='well',
                                  drop_first=True, dtype=float)
    X = pd.concat([df[ref_cols], well_dummies], axis=1, sort=False)
    return sm.add_constant(X)


def fit_monthly_contrast(panel):
    """Fit the monthly-mean Impact-vs-Edge contrast model.

    h ~ const + cwb + Scraped1 + Post + Impact:Scraped1 + Impact:Post
        + Impact:cwb + well-FE

    The Impact main effect is collinear with the well-FE block (Impact
    wells = {wmc3}) and is absorbed into the well dummies; it is not
    added to the design matrix.

    Parameters
    ----------
    panel : long-form DataFrame with columns:
        well, zone ('Impact'|'Edge'), h, cwb, Scraped1, Post

    Returns
    -------
    dict with fitted-model summary fields.
    """
    panel = panel.copy()
    panel['Impact_x_Scraped1'] = (panel['zone'] == 'Impact').astype(float) * panel['Scraped1']
    panel['Impact_x_Post']     = (panel['zone'] == 'Impact').astype(float) * panel['Post']
    panel['Impact_x_cwb']      = (panel['zone'] == 'Impact').astype(float) * panel['cwb']

    ref_cols = ['cwb', 'Scraped1', 'Post',
                'Impact_x_Scraped1', 'Impact_x_Post', 'Impact_x_cwb']
    X = _well_fe_design(panel, ref_cols)
    y = panel['h']

    res = sm.OLS(y, X).fit(cov_type='cluster',
                           cov_kwds={'groups': panel['well']})

    def _term(name):
        b = res.params[name]
        se = res.bse[name]
        p = res.pvalues[name]
        return b, se, p, (b - 1.96*se, b + 1.96*se)

    fell_b,  fell_se,  fell_p,  fell_ci  = _term('Impact_x_Post')
    scr_b,   scr_se,   scr_p,   scr_ci   = _term('Impact_x_Scraped1')
    edge_post_b, edge_post_se, edge_post_p, _ = _term('Post')
    edge_scr_b,  edge_scr_se,  edge_scr_p,  _ = _term('Scraped1')

    return {
        'clearfell_step':       fell_b,
        'clearfell_step_se':    fell_se,
        'clearfell_p':          fell_p,
        'clearfell_ci_lo':      fell_ci[0],
        'clearfell_ci_hi':      fell_ci[1],
        'scraping_step':        scr_b,
        'scraping_step_se':     scr_se,
        'scraping_p':           scr_p,
        'edge_post_b':          edge_post_b,
        'edge_post_p':          edge_post_p,
        'edge_scraping_b':      edge_scr_b,
        'edge_scraping_p':      edge_scr_p,
        'R2':                   res.rsquared,
        'N':                    int(res.nobs),
        'fit':                  res,
    }


def fit_summer_contrast(summer_df, panel_years):
    """Fit the summer-minima Impact-vs-Edge contrast model.

    summer_min ~ const + Post + Impact:Post + well-FE

    Scraping is not modelled at the annual-summer-minimum resolution
    because the pre-fell period contains too few Impact summers prior
    to the 2015 scraping for a stable scraping-step estimate at annual
    resolution.

    Random effects on well are not modelled here (the Impact tier has
    one well, which collapses to OLS); instead well-FE are used as
    fixed effects throughout, with cluster-robust SE on well to handle
    within-well dependence.

    Year selection is by the WMC3 gatekeeper: ``panel_years`` is the
    set of years in which the Impact well WMC3 has a usable Jun-Sep
    record (computed by clearfell_common.wmc3_usable_summer_years and
    passed in from main()).  This is the SAME year panel Script 10l's
    four-zone summer model uses, so the two estimators are directly
    comparable and 10l's Impact-Edge contrast should reproduce this
    script's estimate.  No per-row n_interpolated filter is applied —
    every row in 10d_01 has already passed the Defect-E min_measured=2
    rule and is a valid summer minimum.

    Parameters
    ----------
    summer_df : DataFrame with columns Well, Tier, Year, Summer_min_m,
        n_interpolated.
    panel_years : list of int
        Years admitted by the WMC3 gatekeeper.

    Returns
    -------
    dict with fitted-model summary fields.
    """
    df = summer_df.copy()
    df = df.loc[df['Tier'].isin(['Impact', 'Edge'])].copy()
    df = df.loc[df['Year'].isin(panel_years)].copy()  # WMC3-gatekeeper years
    df['well']    = df['Well'].str.lower()
    df['zone']    = df['Tier']
    # First post-felling summer is the first FULL Jun-Sep summer AFTER
    # the December 2017 felling — i.e. 2018.  The Jun-Sep 2017 summer
    # minimum occurred ~6 months before the felling and cannot carry a
    # felling signal, so it belongs in the pre-felling group.  This
    # matches Script 10d (POST_YEAR = FELLING_YEAR + 1) and Script 10l.
    # (Earlier 10j versions used Year >= INTERVENTION_DATE.year, which
    # mislabelled the pre-felling 2017 summer as post — see the v1.1.0
    # changelog entry.)
    df['Post']    = (df['Year'] >= INTERVENTION_DATE.year + 1).astype(float)
    df['Impact_x_Post'] = (df['zone'] == 'Impact').astype(float) * df['Post']
    df['y']       = df['Summer_min_m']

    ref_cols = ['Post', 'Impact_x_Post']
    X = _well_fe_design(df, ref_cols)
    y = df['y']

    # Cluster-robust SE on well (handles the n=1 Impact-tier case
    # gracefully: the Impact:Post coefficient is identified by the
    # within-WMC3 Post vs Pre contrast, with the residual variance
    # carried by the Edge wells).
    res = sm.OLS(y, X).fit(cov_type='cluster',
                          cov_kwds={'groups': df['well']})

    def _term(name):
        b = res.params[name]
        se = res.bse[name]
        p = res.pvalues[name]
        return b, se, p, (b - 1.96*se, b + 1.96*se)

    fell_b, fell_se, fell_p, fell_ci = _term('Impact_x_Post')
    edge_post_b, edge_post_se, edge_post_p, _ = _term('Post')

    return {
        'clearfell_step':       fell_b,
        'clearfell_step_se':    fell_se,
        'clearfell_p':          fell_p,
        'clearfell_ci_lo':      fell_ci[0],
        'clearfell_ci_hi':      fell_ci[1],
        'edge_post_b':          edge_post_b,
        'edge_post_p':          edge_post_p,
        'R2':                   res.rsquared,
        'N':                    int(res.nobs),
        'n_impact_years':       int(df.loc[df['zone'] == 'Impact'].shape[0]),
        'n_edge_years':         int(df.loc[df['zone'] == 'Edge'].shape[0]),
        'fit':                  res,
    }


# ============================================================================
# PANEL BUILDERS
# ============================================================================

def build_monthly_panel(wells, climate):
    """Build the Impact + Edge long-form monthly panel post PRE_FELL_START."""
    cwb_series = compute_cwb(climate)
    cwb_series = cwb_series - cwb_series.mean()

    records = []
    for well in IMPACT_WELLS + EDGE_WELLS:
        if well not in wells.columns:
            print(f"    [WARN] well not in data: {well}")
            continue
        s = wells[well].dropna()
        s = s.loc[s.index >= PRE_FELL_START]
        zone = 'Impact' if well in IMPACT_WELLS else 'Edge'
        for date, h in s.items():
            records.append({
                'date':     date,
                'well':     well,
                'zone':     zone,
                'h':        h,
                'cwb':      cwb_series.get(date, np.nan),
                'Scraped1': 1.0 if date >= SCRAPING_DATE else 0.0,
                'Post':     1.0 if date >= INTERVENTION_DATE else 0.0,
            })
    panel = pd.DataFrame(records).dropna(subset=['cwb'])
    return panel


# ============================================================================
# FIGURES
# ============================================================================

def figure_monthly_contrast(panel, monthly, out_path):
    """Two-panel figure: zone centroids and the raw differential series."""
    impact_mean = (panel.loc[panel['zone'] == 'Impact']
                        .groupby('date')['h'].mean())
    edge_mean   = (panel.loc[panel['zone'] == 'Edge']
                        .groupby('date')['h'].mean())
    diff        = impact_mean - edge_mean

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                             gridspec_kw={'height_ratios': [1.2, 1.0]})

    # Pre/post split for period means
    # Period means — each series masked on its own index (lengths differ)
    imp_pre_mean  = impact_mean[impact_mean.index <  INTERVENTION_DATE].mean()
    imp_post_mean = impact_mean[impact_mean.index >= INTERVENTION_DATE].mean()
    edg_pre_mean  = edge_mean[edge_mean.index   <  INTERVENTION_DATE].mean()
    edg_post_mean = edge_mean[edge_mean.index   >= INTERVENTION_DATE].mean()
    diff_pre_mean  = diff[diff.index <  INTERVENTION_DATE].mean() * 1000
    diff_post_mean = diff[diff.index >= INTERVENTION_DATE].mean() * 1000

    ax0 = axes[0]
    ax0.plot(impact_mean.index, impact_mean.values,
             color=TIER_COLOURS['Impact'], lw=1.5, label='Impact (WMC3)')
    ax0.plot(edge_mean.index, edge_mean.values,
             color=TIER_COLOURS['Edge'], lw=1.5, label='Edge centroid')
    ax0.axvline(SCRAPING_DATE,     color='grey', ls='--', alpha=0.7,
                label='Apr 2015 scraping')
    ax0.axvline(INTERVENTION_DATE, color='k',    ls='--', alpha=0.8,
                label='Dec 2017 felling')
    # Pre-felling period means
    ax0.axhline(imp_pre_mean,  color=TIER_COLOURS['Impact'], ls=':',
                lw=1.2, alpha=0.7, xmin=0,
                xmax=(INTERVENTION_DATE - impact_mean.index[0]).days /
                     (impact_mean.index[-1] - impact_mean.index[0]).days)
    ax0.axhline(edg_pre_mean,  color=TIER_COLOURS['Edge'],   ls=':',
                lw=1.2, alpha=0.7, xmin=0,
                xmax=(INTERVENTION_DATE - impact_mean.index[0]).days /
                     (impact_mean.index[-1] - impact_mean.index[0]).days)
    # Post-felling period means
    xmin_post = (INTERVENTION_DATE - impact_mean.index[0]).days / \
                (impact_mean.index[-1] - impact_mean.index[0]).days
    ax0.axhline(imp_post_mean, color=TIER_COLOURS['Impact'], ls=':',
                lw=1.2, alpha=0.7, xmin=xmin_post, xmax=1)
    ax0.axhline(edg_post_mean, color=TIER_COLOURS['Edge'],   ls=':',
                lw=1.2, alpha=0.7, xmin=xmin_post, xmax=1)
    # Annotate shifts
    ax0.annotate(f'Δ Impact = {(imp_post_mean - imp_pre_mean)*1000:+.0f} mm',
                 xy=(INTERVENTION_DATE, imp_post_mean), xytext=(10, 8),
                 textcoords='offset points', fontsize=7.5,
                 color=TIER_COLOURS['Impact'])
    ax0.annotate(f'Δ Edge = {(edg_post_mean - edg_pre_mean)*1000:+.0f} mm',
                 xy=(INTERVENTION_DATE, edg_post_mean), xytext=(10, -14),
                 textcoords='offset points', fontsize=7.5,
                 color=TIER_COLOURS['Edge'])
    ax0.set_ylabel('Water-table depth (m)')
    ax0.set_title('Impact and Edge centroids')
    ax0.legend(loc='lower right', fontsize=8)
    ax0.grid(True, alpha=0.3)

    ax1 = axes[1]
    ax1.plot(diff.index, diff.values * 1000, color='k', lw=1.2)
    ax1.axhline(0, color='grey', ls='-', alpha=0.5)
    ax1.axvline(SCRAPING_DATE,     color='grey', ls='--', alpha=0.7)
    ax1.axvline(INTERVENTION_DATE, color='k',    ls='--', alpha=0.8)
    # Pre/post mean lines on contrast panel
    ax1.axhline(diff_pre_mean,  color='steelblue', ls=':', lw=1.4, alpha=0.8,
                xmin=0, xmax=xmin_post)
    ax1.axhline(diff_post_mean, color='steelblue', ls=':', lw=1.4, alpha=0.8,
                xmin=xmin_post, xmax=1)
    ax1.annotate(f'Pre mean: {diff_pre_mean:+.0f} mm',
                 xy=(impact_mean.index[0], diff_pre_mean),
                 xytext=(4, 5), textcoords='offset points', fontsize=7.5,
                 color='steelblue')
    ax1.annotate(f'Post mean: {diff_post_mean:+.0f} mm',
                 xy=(INTERVENTION_DATE, diff_post_mean),
                 xytext=(10, 5), textcoords='offset points', fontsize=7.5,
                 color='steelblue')
    ax1.set_ylabel('Impact − Edge (mm)')
    ax1.set_xlabel('Date')
    ax1.set_title('Direct contrast: Impact minus Edge')
    ax1.grid(True, alpha=0.3)

    for ax in axes:
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    step_mm = monthly['clearfell_step'] * 1000
    ci_lo   = monthly['clearfell_ci_lo'] * 1000
    ci_hi   = monthly['clearfell_ci_hi'] * 1000
    fig.suptitle(
        f"Direct Impact-vs-Edge BACI — monthly contrast\n"
        f"Differential felling step = {step_mm:+.1f} mm "
        f"(95% CI [{ci_lo:+.1f}, {ci_hi:+.1f}], "
        f"p = {monthly['clearfell_p']:.4f}, n = {monthly['N']})",
        fontsize=11
    )
    plt.tight_layout(rect=(0, 0, 1, 0.94))
    render_figure(fig, out_path,
                  format='jpeg' if str(out_path).endswith('.jpg') else None)
    plt.close(fig)


def figure_summer_contrast(summer_df, summer, panel_years, out_path):
    """Annual summer minima trajectories for Impact + Edge.

    Restricted to the WMC3-gatekeeper year panel (``panel_years``) so
    the figure shows exactly the years the model is fitted on.  Per-well
    and tier-mean series are reindexed onto the full continuous year
    range so a year with no summer minimum becomes an explicit NaN and
    the line breaks there, rather than drawing a straight segment across
    the gap (e.g. WMC3 has no 2019 summer minimum, and 2019 is excluded
    from the panel, so the Impact line breaks at 2019).
    """
    df = summer_df.loc[summer_df['Tier'].isin(['Impact', 'Edge'])].copy()
    df = df.loc[df['Year'].isin(panel_years)].copy()

    fig, ax = plt.subplots(figsize=(10, 5))

    year_min = int(df['Year'].min())
    year_max = int(df['Year'].max())
    all_years = list(range(year_min, year_max + 1))

    for tier, group in df.groupby('Tier'):
        # Per-well thin lines and tier mean — reindexed to continuous
        # years so missing years break the line instead of bridging it.
        for well, well_group in group.groupby('Well'):
            ws = (well_group.set_index('Year')['Summer_min_m']
                            .reindex(all_years))
            ax.plot(ws.index, ws.values,
                    '-', color=TIER_COLOURS[tier], alpha=0.35, lw=0.8)
        tier_mean = (group.groupby('Year')['Summer_min_m'].mean()
                          .reindex(all_years))
        ax.plot(tier_mean.index, tier_mean.values,
                '-o', color=TIER_COLOURS[tier], lw=2.0,
                label=f'{tier} mean')

    ax.axvline(SCRAPING_DATE.year,     color='grey', ls='--', alpha=0.7,
               label='Apr 2015 scraping')
    ax.axvline(INTERVENTION_DATE.year, color='k',    ls='--', alpha=0.8,
               label='Dec 2017 felling')
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual Jun–Sep minimum water-table depth (m)')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right', fontsize=9)

    step_mm = summer['clearfell_step'] * 1000
    ci_lo   = summer['clearfell_ci_lo'] * 1000
    ci_hi   = summer['clearfell_ci_hi'] * 1000
    ax.set_title(
        f"Annual summer minima — Impact vs Edge\n"
        f"Differential felling step = {step_mm:+.1f} mm "
        f"(95% CI [{ci_lo:+.1f}, {ci_hi:+.1f}], "
        f"p = {summer['clearfell_p']:.4f}, n_Impact = {summer['n_impact_years']}, "
        f"n_Edge = {summer['n_edge_years']})",
        fontsize=11
    )
    plt.tight_layout()
    render_figure(fig, out_path,
                  format='jpeg' if str(out_path).endswith('.jpg') else None)
    plt.close(fig)


# ============================================================================
# OUTPUT WRITERS
# ============================================================================

def write_monthly_results_csv(monthly, path):
    """One-row summary of the monthly contrast fit."""
    df = pd.DataFrame([{
        'estimator':           'OLS_well_FE_cluster_robust',
        'clearfell_step_m':    round(monthly['clearfell_step'], 4),
        'clearfell_step_se_m': round(monthly['clearfell_step_se'], 4),
        'clearfell_ci_lo_m':   round(monthly['clearfell_ci_lo'], 4),
        'clearfell_ci_hi_m':   round(monthly['clearfell_ci_hi'], 4),
        'clearfell_p':         monthly['clearfell_p'],
        'scraping_step_m':     round(monthly['scraping_step'], 4),
        'scraping_step_se_m':  round(monthly['scraping_step_se'], 4),
        'scraping_p':          monthly['scraping_p'],
        'edge_post_b_m':       round(monthly['edge_post_b'], 4),
        'edge_post_p':         monthly['edge_post_p'],
        'edge_scraping_b_m':   round(monthly['edge_scraping_b'], 4),
        'edge_scraping_p':     monthly['edge_scraping_p'],
        'R2':                  round(monthly['R2'], 4),
        'N':                   monthly['N'],
    }])
    df.to_csv(path, index=False)


def write_summer_results_csv(summer, path):
    """One-row summary of the summer-minima contrast fit."""
    df = pd.DataFrame([{
        'estimator':           'OLS_well_FE_cluster_robust',
        'clearfell_step_m':    round(summer['clearfell_step'], 4),
        'clearfell_step_se_m': round(summer['clearfell_step_se'], 4),
        'clearfell_ci_lo_m':   round(summer['clearfell_ci_lo'], 4),
        'clearfell_ci_hi_m':   round(summer['clearfell_ci_hi'], 4),
        'clearfell_p':         summer['clearfell_p'],
        'edge_post_b_m':       round(summer['edge_post_b'], 4),
        'edge_post_p':         summer['edge_post_p'],
        'R2':                  round(summer['R2'], 4),
        'N':                   summer['N'],
        'n_impact_years':      summer['n_impact_years'],
        'n_edge_years':        summer['n_edge_years'],
    }])
    df.to_csv(path, index=False)


def write_report_numbers(monthly, summer, path):
    """Standard ReportNumbers CSV with all key parameters."""
    rn = ReportNumbers()

    # Monthly contrast
    rn.add('ImpactVsEdge_monthly_clearfell_step',
           monthly['clearfell_step'], well='Impact', era='Post_felling',
           note=f"p={monthly['clearfell_p']:.4f}, "
                f"CI=[{monthly['clearfell_ci_lo']:.4f},"
                f"{monthly['clearfell_ci_hi']:.4f}]")
    rn.add('ImpactVsEdge_monthly_clearfell_step_se',
           monthly['clearfell_step_se'], well='Impact', era='Post_felling')
    rn.add('ImpactVsEdge_monthly_scraping_step',
           monthly['scraping_step'], well='Impact', era='Post_scraping',
           note=f"p={monthly['scraping_p']:.4f}")
    rn.add('ImpactVsEdge_monthly_R2', monthly['R2'], unit='',
           well='Impact', note='Model R²')
    rn.add('ImpactVsEdge_monthly_N', monthly['N'], unit='months',
           well='Impact', note='Sample size')

    # Summer contrast
    rn.add('ImpactVsEdge_summer_clearfell_step',
           summer['clearfell_step'], well='Impact', era='Post_felling_Jun-Sep',
           note=f"p={summer['clearfell_p']:.4f}, "
                f"CI=[{summer['clearfell_ci_lo']:.4f},"
                f"{summer['clearfell_ci_hi']:.4f}]")
    rn.add('ImpactVsEdge_summer_clearfell_step_se',
           summer['clearfell_step_se'], well='Impact', era='Post_felling_Jun-Sep')
    rn.add('ImpactVsEdge_summer_R2', summer['R2'], unit='',
           well='Impact', note='Model R²')
    rn.add('ImpactVsEdge_summer_N', summer['N'], unit='well-years',
           well='Impact', note='Sample size')

    rn.save(path)


# ============================================================================
# MAIN
# ============================================================================

def main():
    banner("10j", "Impact–Edge Direct Contrast", version="1.2.0")
    print("=" * 72)
    print("Script 10j — Direct Impact-vs-Edge contrasts")
    print("=" * 72)

    make_all_dirs()

    print("\n  Loading data ...")
    wells, prov, climate, _master, _locs, valid_tiers = load_clearfell_data()
    print_network_summary({k: v for k, v in valid_tiers.items()
                           if k in ('Impact', 'Edge')})

    print(f"  PRE_FELL_START:   {PRE_FELL_START.date()}")
    print(f"  SCRAPING_DATE:    {SCRAPING_DATE.date()}")
    print(f"  INTERVENTION:     {INTERVENTION_DATE.date()}")
    print()

    # ── 1. Monthly contrast ────────────────────────────────────────────
    print("  1. Building monthly panel ...")
    panel = build_monthly_panel(wells, climate)
    print(f"     n_rows = {len(panel)}, "
          f"n_wells = {panel['well'].nunique()}")

    print("  2. Fitting monthly contrast ...")
    monthly = fit_monthly_contrast(panel)
    print(f"     Differential felling step "
          f"(Impact − Edge): {monthly['clearfell_step']*1000:+7.1f} mm  "
          f"95% CI [{monthly['clearfell_ci_lo']*1000:+7.1f}, "
          f"{monthly['clearfell_ci_hi']*1000:+7.1f}]  "
          f"p={monthly['clearfell_p']:.4f}")
    print(f"     Differential scraping step "
          f"(Impact − Edge): {monthly['scraping_step']*1000:+7.1f} mm  "
          f"p={monthly['scraping_p']:.4f}")
    print(f"     N = {monthly['N']}, R² = {monthly['R2']:.3f}")
    print()

    # ── 2. Summer-minima contrast ──────────────────────────────────────
    print("  3. Loading summer minima from 10d ...")
    if not OUT_10D_DATA.exists():
        raise FileNotFoundError(
            f"Required input not found: {OUT_10D_DATA}\n"
            f"  Run Script 10d (summer minima) first."
        )
    summer_df = pd.read_csv(OUT_10D_DATA)

    # WMC3-gatekeeper year panel — the same year selection Script 10l
    # uses, so the two summer estimators are directly comparable.
    summer_panel_years = wmc3_usable_summer_years(wells,
                                                  wells_provenance=prov)
    print(f"     summer panel years (WMC3 gatekeeper): "
          f"{summer_panel_years}")

    print("  4. Fitting summer-minima contrast ...")
    summer = fit_summer_contrast(summer_df, summer_panel_years)
    print(f"     Differential summer-minimum step "
          f"(Impact − Edge): {summer['clearfell_step']*1000:+7.1f} mm  "
          f"95% CI [{summer['clearfell_ci_lo']*1000:+7.1f}, "
          f"{summer['clearfell_ci_hi']*1000:+7.1f}]  "
          f"p={summer['clearfell_p']:.4f}")
    print(f"     N = {summer['N']} ({summer['n_impact_years']} Impact-years, "
          f"{summer['n_edge_years']} Edge-years), R² = {summer['R2']:.3f}")
    print()

    # ── 3. Outputs ─────────────────────────────────────────────────────
    print("  5. Writing outputs ...")
    write_monthly_results_csv(monthly, OUT_10J_MONTHLY_RESULTS)
    saved(f"{OUT_10J_MONTHLY_RESULTS.name}")
    write_summer_results_csv(summer, OUT_10J_SUMMER_RESULTS)
    saved(f"{OUT_10J_SUMMER_RESULTS.name}")
    write_report_numbers(monthly, summer, OUT_10J_REPORT)
    saved(f"{OUT_10J_REPORT.name}")

    print("  6. Building figures ...")
    figure_monthly_contrast(panel, monthly, OUT_10J_TIMESERIES_FIG)
    saved(f"{OUT_10J_TIMESERIES_FIG.name}")
    figure_summer_contrast(summer_df, summer, summer_panel_years,
                           OUT_10J_SUMMER_FIG)
    saved(f"{OUT_10J_SUMMER_FIG.name}")

    print("  7. Updating site-observations registry ...")
    update_site_observation('impact_vs_edge_clearfell_monthly_step',
                            monthly['clearfell_step'],
                            producer_script='10j')
    update_site_observation('impact_vs_edge_clearfell_monthly_step_se',
                            monthly['clearfell_step_se'],
                            producer_script='10j')
    update_site_observation('impact_vs_edge_clearfell_summer_step',
                            summer['clearfell_step'],
                            producer_script='10j')
    update_site_observation('impact_vs_edge_clearfell_summer_step_se',
                            summer['clearfell_step_se'],
                            producer_script='10j')
    saved("4 entries updated in pipeline_site_observations.csv")
    print()
    print("Script 10j complete.")


if __name__ == '__main__':
    main()
