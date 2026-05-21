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

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from utils.paths import (
    make_all_dirs, DIR_10,
    OUT_10J_MONTHLY_RESULTS, OUT_10J_SUMMER_RESULTS,
    OUT_10J_TIMESERIES_FIG, OUT_10J_SUMMER_FIG,
    OUT_10J_REPORT, OUT_10D_DATA,
)
from utils.clearfell_common import (
    load_clearfell_data, print_network_summary,
    INTERVENTION_DATE, SCRAPING_DATE, PRE_FELL_START,
    IMPACT_WELLS, EDGE_WELLS,
    compute_cwb,
    ReportNumbers, TIER_COLOURS,
)
from utils.site_observations import update_site_observation

__version__ = "1.0.0"  # Hollingham (2026) — 2026-05-21
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
    X = pd.concat([df[ref_cols], well_dummies], axis=1)
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


def fit_summer_contrast(summer_df):
    """Fit the summer-minima Impact-vs-Edge contrast model.

    summer_min ~ const + Post + Impact:Post + well-FE

    Scraping is not modelled at the annual-summer-minimum resolution
    because the pre-fell period contains only two summers (2011, 2013)
    of Impact data prior to the 2015 scraping under the n_interpolated
    ≤ 0 rule, which is too few for a stable scraping-step estimate at
    annual resolution.

    Random effects on well are not modelled here (the Impact tier has
    one well, which collapses to OLS); instead well-FE are used as
    fixed effects throughout, with cluster-robust SE on well to handle
    within-well dependence.

    Parameters
    ----------
    summer_df : DataFrame with columns Well, Tier, Year, Summer_min_m,
        n_interpolated.

    Returns
    -------
    dict with fitted-model summary fields.
    """
    df = summer_df.copy()
    df = df.loc[df['Tier'].isin(['Impact', 'Edge'])].copy()
    df = df.loc[df['n_interpolated'] == 0].copy()  # measured-only rows
    df['well']    = df['Well'].str.lower()
    df['zone']    = df['Tier']
    df['Post']    = (df['Year'] >= INTERVENTION_DATE.year).astype(float)
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

    ax0 = axes[0]
    ax0.plot(impact_mean.index, impact_mean.values,
             color=TIER_COLOURS['Impact'], lw=1.5, label='Impact (WMC3)')
    ax0.plot(edge_mean.index, edge_mean.values,
             color=TIER_COLOURS['Edge'], lw=1.5, label='Edge centroid')
    ax0.axvline(SCRAPING_DATE,     color='grey', ls='--', alpha=0.7,
                label='Apr 2015 scraping')
    ax0.axvline(INTERVENTION_DATE, color='k',    ls='--', alpha=0.8,
                label='Dec 2017 felling')
    ax0.set_ylabel('Water-table depth (m)')
    ax0.set_title('Impact and Edge centroids')
    ax0.legend(loc='lower right', fontsize=8)
    ax0.grid(True, alpha=0.3)

    ax1 = axes[1]
    ax1.plot(diff.index, diff.values * 1000, color='k', lw=1.2)
    ax1.axhline(0, color='grey', ls='-', alpha=0.5)
    ax1.axvline(SCRAPING_DATE,     color='grey', ls='--', alpha=0.7)
    ax1.axvline(INTERVENTION_DATE, color='k',    ls='--', alpha=0.8)
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
    fig.savefig(out_path, dpi=150, format='jpeg' if str(out_path).endswith('.jpg') else None,
                bbox_inches='tight')
    plt.close(fig)


def figure_summer_contrast(summer_df, summer, out_path):
    """Annual summer minima trajectories for Impact + Edge."""
    df = summer_df.loc[summer_df['Tier'].isin(['Impact', 'Edge'])].copy()
    df = df.loc[df['n_interpolated'] == 0].copy()

    fig, ax = plt.subplots(figsize=(10, 5))

    for tier, group in df.groupby('Tier'):
        # Plot per-well thin lines and tier mean as the bold line
        for well, well_group in group.groupby('Well'):
            ax.plot(well_group['Year'], well_group['Summer_min_m'],
                    '-', color=TIER_COLOURS[tier], alpha=0.35, lw=0.8)
        tier_mean = group.groupby('Year')['Summer_min_m'].mean()
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
    fig.savefig(out_path, dpi=150, format='jpeg' if str(out_path).endswith('.jpg') else None,
                bbox_inches='tight')
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
    print("=" * 72)
    print("Script 10j — Direct Impact-vs-Edge contrasts")
    print("=" * 72)

    make_all_dirs()

    print("\n  Loading data ...")
    wells, _prov, climate, _master, _locs, valid_tiers = load_clearfell_data()
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

    print("  4. Fitting summer-minima contrast ...")
    summer = fit_summer_contrast(summer_df)
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
    print(f"     → {OUT_10J_MONTHLY_RESULTS.name}")
    write_summer_results_csv(summer, OUT_10J_SUMMER_RESULTS)
    print(f"     → {OUT_10J_SUMMER_RESULTS.name}")
    write_report_numbers(monthly, summer, OUT_10J_REPORT)
    print(f"     → {OUT_10J_REPORT.name}")

    print("  6. Building figures ...")
    figure_monthly_contrast(panel, monthly, OUT_10J_TIMESERIES_FIG)
    print(f"     → {OUT_10J_TIMESERIES_FIG.name}")
    figure_summer_contrast(summer_df, summer, OUT_10J_SUMMER_FIG)
    print(f"     → {OUT_10J_SUMMER_FIG.name}")

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
    print("     → 4 entries updated in pipeline_site_observations.csv")
    print()
    print("Script 10j complete.")


if __name__ == '__main__':
    main()
