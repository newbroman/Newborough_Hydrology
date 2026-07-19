r"""
====================================================================================
10l — FOUR-ZONE SUMMER-MINIMA CLEARFELL BACI
====================================================================================

Phase 2 of the four-zone clearfell BACI redesign.  Script 10k fits the
four-zone pooled-panel model on the monthly-mean water-table series;
this script fits the same four-zone structure on the ecologically
critical annual Jun-Sep MINIMUM depth.

The four zones are identical to 10k:

    Forest control  (reference)  — ceh32, ceh34, ceh33, nw10, ceh2
    C3 / Warren                  — ceh1, nw1, nw2, nw11
    Edge                         — ceh31, ceh20, ceh30, ceh16
    Impact                       — wmc3

Zone is a four-level factor with Forest control as the reference level,
so the zone:Post coefficients are the differential summer-minimum
felling steps relative to Forest control.  Every pairwise contrast comes
from one coefficient vector with one shared covariance matrix and is

exactly subtractable, as in 10k and 10j.

Model
-----
    summer_min ~ const + Post + zone:Post + well-FE

  OLS with cluster-robust SE on well.  The Impact zone is a single well
  (WMC3); its zone:Post interaction is identified by WMC3's own
  within-well pre/post contrast, with residual variance carried by the
  multi-well zones — cluster-robust SE degrade gracefully for the n=1
  zone (the same property 10j and 10k rely on).

Why no scraping term and no climate covariate
---------------------------------------------
This estimator deliberately matches Script 10j's SUMMER contrast, not
10k's monthly model:

  * No scraping term.  At annual resolution, on the 2011-cutoff frame
    (see below), the Impact tier has only three clean pre-scraping
    summers (2011, 2013, 2014 — WMC3's 2012 Jun-Sep window holds a
    single measured reading and fails the >=2-measured rule).  Three
    points cannot support a stable annual scraping-step estimate, so
    scraping is not modelled.  10j drops scraping at annual resolution
    for the same reason.

  * No climate (CWB) covariate.  10k's engine is a zone-interacted
    monthly cumulative-water-balance term.  An annual minimum-of-summer
    frame carries no monthly climate structure, so that covariate
    cannot enter in the same form.  Following 10j's summer estimator,
    no climate covariate is used; the felling contrast is the raw
    pre/post difference net of zone and well fixed effects.

Year cutoff
-----------
The annual frame starts in 2011 — the first year all network wells
have complete observed Jun-Sep coverage — matching Script 10d's
documented annual cutoff.  Starting earlier would recover two extra
WMC3 pre-felling summers (2009, 2010) but would leave the C3/Warren
and Edge zones unbalanced against the rest of the panel, partly
reintroducing the record-length-imbalance problem the cutoff exists to
prevent.  Four-zone balance is the point of the four-zone design, so
the balanced 2011 cutoff is kept.

Summer minima — provenance and the Defect E rule
-------------------------------------------------
Annual summer minima are computed via clearfell_common.annual_summer_
minimum() with the per-cell provenance series and min_measured=2: a
year yields a summer minimum only if it has at least two MEASURED (not
interpolated) Jun-Sep months, and only measured values can become the
minimum.  This is the Defect E rule, applied identically to 10d and
10j.

The Forest, Edge and Impact zones' summer minima already exist as
canonical pipeline output in 10d_01_summer_minima.csv.  The C3/Warren
zone is new and is NOT covered by 10d (10d iterates ALL_NETWORK_WELLS,
which deliberately excludes the C3/Warren wells).  This script
therefore computes the C3/Warren summer minima itself, under the same
rule, and writes them to 10l_03_c3warren_summer_minima.csv as canonical
output.  The other three zones are read from 10d.

C3/Warren is a SECOND CONTROL zone
----------------------------------
As in 10k: C3/Warren is the shielded open western-dune zone.  The
EXPECTED RESULT is phi_{C3/Warren} ≈ 0 — it should behave like the
Forest control.  A clearly non-zero C3/Warren summer step is a flag,
not a felling finding.

Relationship to 10j and 10k
---------------------------
  * 10j — two-zone Impact-vs-Edge summer contrast.  Unchanged.  Its
    summer Impact-vs-Edge step reappears here, by construction, as one
    row of the pairwise table; agreement is asserted as a cross-check.
  * 10k — four-zone MONTHLY model.  10l is its annual-resolution
    sibling; the two are independent fits on different frames and are
    not expected to produce equal numbers.

Dependencies
------------
  utils/clearfell_common.py — well lists incl. C3_WARREN_WELLS, dates,
                              data loading, annual_summer_minimum
  utils/site_observations  — registry of site-wide observations
  utils/paths              — output paths
  outputs/10_clearfell_baci/10d_01_summer_minima.csv — Forest/Edge/
                              Impact summer minima (produced by 10d)

Outputs
-------
  outputs/10_clearfell_baci/10l_01_four_zone_summer_results.csv
  outputs/10_clearfell_baci/10l_02_summer_pairwise_contrasts.csv
  outputs/10_clearfell_baci/10l_03_c3warren_summer_minima.csv
  outputs/10_clearfell_baci/10l_04_zone_summer_trajectories.jpg
  outputs/10_clearfell_baci/10l_05_summer_forest_plot.jpg
  outputs/10_clearfell_baci/10l_report_numbers.csv

  (also updates pipeline_site_observations.csv with three entries)

References
----------
Hollingham (2026), §4.6.  Part of the Script 10 clearfell analysis suite.
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

from utils.paths import (
    make_all_dirs,
    OUT_10L_ZONE_RESULTS, OUT_10L_PAIRWISE, OUT_10L_SUMMER_MINIMA,
    OUT_10L_TRAJECTORY_FIG, OUT_10L_FOREST_PLOT, OUT_10L_REPORT,
    OUT_10D_DATA, OUT_10J_SUMMER_RESULTS,
)
from utils.clearfell_common import (
    load_clearfell_data,
    INTERVENTION_DATE,
    IMPACT_WELLS, EDGE_WELLS, FOREST_CONTROL_WELLS, C3_WARREN_WELLS,
    annual_summer_minimum, wmc3_usable_summer_years,
    ReportNumbers, TIER_COLOURS,
)
from utils.site_observations import update_site_observation
from utils.render_utils import render_figure

__version__ = "1.1.0"  # Hollingham (2026) — 2026-05-22
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
# 1.0.0 — Initial.  Four-zone summer-minima clearfell BACI — Phase 2 of
#         the four-zone redesign, the annual-resolution sibling of the
#         monthly Script 10k.  Fits summer_min ~ Post + zone:Post +
#         well-FE on the annual Jun-Sep minimum, four zones, Forest
#         control reference, OLS with cluster-robust SE.  No scraping
#         term and no climate covariate — matches Script 10j's summer
#         estimator (see module docstring for the rationale).  Computes
#         the C3/Warren zone's summer minima itself (10d does not cover
#         them) and reads the other three zones from 10d_01.
#         Year selection is by the WMC3 gatekeeper
#         (clearfell_common.wmc3_usable_summer_years): a year enters the
#         analysis if WMC3 has a usable Jun-Sep record — 2011 +
#         2013-2018 + 2020-2025 on current data.  Pairwise contrasts
#         carry a contrast_type field (primary / derived /
#         identity_check); the forest plot and CSV present primary and
#         derived contrasts separately so a derived contrast's
#         covariance-dependent SE/p is not misread as a primary result.
#         Writes three site-observation entries.  No hardcoded site
#         values.
#         [This script was developed across one session and has not
#          previously been committed; the gatekeeper and contrast_type
#          features were added before first commit and are folded into
#          this 1.0.0 description rather than versioned separately.]


# ============================================================================
# ZONE DEFINITIONS  (identical to Script 10k)
# ============================================================================
REFERENCE_ZONE = 'Forest'

ZONE_WELLS = {
    'Forest':     FOREST_CONTROL_WELLS,   # reference
    'C3/Warren':  C3_WARREN_WELLS,
    'Edge':       EDGE_WELLS,
    'Impact':     IMPACT_WELLS,
}
NON_REF_ZONES = ['C3/Warren', 'Edge', 'Impact']

ZONE_COLOURS = {
    'Forest':     TIER_COLOURS['Forest Ctrl'],
    'C3/Warren':  '#5E81AC',
    'Edge':       TIER_COLOURS['Edge'],
    'Impact':     TIER_COLOURS['Impact'],
}

ZONE_TAG = {
    'Forest':     'Forest',
    'C3/Warren':  'C3Warren',
    'Edge':       'Edge',
    'Impact':     'Impact',
}

# Annual frame — the search range.  The actual years entering the
# analysis are not this whole range: they are the subset in which the
# Impact well WMC3 has a usable Jun-Sep record, selected at runtime by
# clearfell_common.wmc3_usable_summer_years() (the WMC3 gatekeeper).
# On the current data that yields 2011 + 2013-2018 + 2020-2025 — i.e.
# 2012 and 2019 are dropped because WMC3's summer record fails there.
# FIRST_YEAR is the earliest year the search considers (2009-2010
# pre-date the full monitoring network); incomplete recent years are
# dropped automatically by the gatekeeper's four-row check.
FIRST_YEAR = 2011
LAST_YEAR_CAP = 2026

# 10d's tier labels for the three zones it does cover, so their rows can
# be pulled out of 10d_01_summer_minima.csv by Tier.
TEN_D_TIER_FOR_ZONE = {
    'Forest':  'Forest Ctrl',
    'Edge':    'Edge',
    'Impact':  'Impact',
}


# ============================================================================
# SUMMER-MINIMA ASSEMBLY
# ============================================================================

def compute_c3warren_summer_minima(wells, wells_provenance):
    """Compute the C3/Warren zone's annual Jun-Sep summer minima.

    The C3/Warren wells are not covered by Script 10d (which iterates
    ALL_NETWORK_WELLS, deliberately excluding them).  This function
    computes their summer minima under the SAME rule 10d uses — the
    Defect E provenance / min_measured=2 rule — so the C3/Warren minima
    are on an identical basis to the other three zones.

    Parameters
    ----------
    wells : pd.DataFrame
        Monthly well depths, lowercase column names.
    wells_provenance : pd.DataFrame
        Per-cell provenance flags aligned to `wells`.

    Returns
    -------
    DataFrame with columns Well, Tier, Year, Summer_min_m, n_interpolated.
        Same schema (relevant subset) as 10d_01_summer_minima.csv, so
        the rows can be concatenated with the 10d rows downstream.
    """
    from utils.clearfell_common import SUMMER_MONTHS

    rows = []
    for w in C3_WARREN_WELLS:
        if w not in wells.columns:
            print(f"    [WARN] C3/Warren well not in data: {w}")
            continue
        prov_w = (wells_provenance[w]
                  if w in wells_provenance.columns else None)
        mins = annual_summer_minimum(
            wells[w], FIRST_YEAR, LAST_YEAR_CAP,
            provenance=prov_w, min_measured=2,
        )
        for yr, val in mins.items():
            # Diagnostic interpolated-cell count for the year, mirroring
            # the n_interpolated column 10d writes.
            n_interp = 0
            if prov_w is not None:
                mask = ((wells[w].index.year == yr)
                        & (wells[w].index.month.isin(SUMMER_MONTHS)))
                n_interp = int((prov_w[mask] == 'interpolated').sum())
            rows.append({
                'Well':           w.upper(),
                'Tier':           'C3/Warren',
                'Year':           yr,
                'Summer_min_m':   round(val, 4),
                'n_interpolated': n_interp,
            })
    return pd.DataFrame(rows)


def build_summer_panel(wells, wells_provenance):
    """Build the four-zone annual summer-minima panel.

    Forest, Edge and Impact zone minima are read from 10d's canonical
    output (10d_01_summer_minima.csv).  The C3/Warren zone minima are
    computed here (10d does not cover that zone).

    Year selection is by the WMC3 gatekeeper
    (clearfell_common.wmc3_usable_summer_years): a year enters the
    analysis if the Impact well WMC3 has a usable Jun-Sep record that
    year.  No per-row n_interpolated filter is applied — every row from
    10d and from compute_c3warren_summer_minima() has already passed
    the Defect-E min_measured=2 rule and is a valid summer minimum.

    Returns
    -------
    panel : long-form DataFrame with columns
        Well, well, zone, Year, Summer_min_m, Post.
    c3_minima : DataFrame
        The C3/Warren summer minima, for writing as canonical output.
    """
    if not OUT_10D_DATA.exists():
        raise FileNotFoundError(
            f"Required input not found: {OUT_10D_DATA}\n"
            f"  Run Script 10d (summer minima) first.")

    tend = pd.read_csv(OUT_10D_DATA)

    # Forest / Edge / Impact rows from 10d, mapped to four-zone labels.
    frames = []
    for zone, tend_tier in TEN_D_TIER_FOR_ZONE.items():
        sub = tend.loc[tend['Tier'] == tend_tier,
                       ['Well', 'Year', 'Summer_min_m', 'n_interpolated']].copy()
        sub['zone'] = zone
        frames.append(sub)

    # C3/Warren rows computed here.
    c3_minima = compute_c3warren_summer_minima(wells, wells_provenance)
    if not c3_minima.empty:
        c3 = c3_minima[['Well', 'Year', 'Summer_min_m',
                        'n_interpolated']].copy()
        c3['zone'] = 'C3/Warren'
        frames.append(c3)

    panel = pd.concat(frames, ignore_index=True)

    # Year selection — the WMC3 gatekeeper.  A year enters the analysis
    # if the Impact well WMC3 has a usable Jun-Sep record that year (at
    # most one missing month); clearfell_common.wmc3_usable_summer_years
    # derives the set from the live data.  WMC3 gates the panel because
    # it is the n=1 Impact zone; the other 13 wells are allowed to be
    # patchy (the well-FE model tolerates missing well-months).  On the
    # current data this yields 2011 + 2013-2018 + 2020-2025 (2012 and
    # 2019 dropped — WMC3's summer record fails there).
    panel_years = wmc3_usable_summer_years(
        wells, wells_provenance=wells_provenance,
        start_year=FIRST_YEAR, end_year=LAST_YEAR_CAP)
    panel = panel.loc[panel['Year'].isin(panel_years)].copy()

    # No n_interpolated filter.  Every row from 10d and from
    # compute_c3warren_summer_minima() has already passed the Defect-E
    # min_measured=2 rule, so it is a valid summer minimum computed from
    # measured cells; an interpolated Jun-Sep cell elsewhere in the year
    # does not disqualify it (and cannot itself be the minimum, since
    # annual_summer_minimum only lets measured values be the minimum).
    # This keeps WMC3's 2011 and 2025 rows, which carry one interpolated
    # Jun-Sep month each — consistent with the gatekeeper rule.

    panel['well'] = panel['Well'].str.lower()
    panel['Post'] = (panel['Year'] >= INTERVENTION_DATE.year + 1).astype(float)
    # Post-felling summers start the first FULL summer after the Dec 2017
    # felling — i.e. 2018 — matching 10d's POST_YEAR convention.

    return panel, c3_minima


# ============================================================================
# MODEL FITTING
# ============================================================================

def _well_fe_design(df, ref_cols):
    """Design matrix with well fixed effects (drop-first dummies).

    Identical construction to Scripts 10j and 10k.
    """
    well_dummies = pd.get_dummies(df['well'], prefix='well',
                                  drop_first=True, dtype=float)
    X = pd.concat([df[ref_cols].reset_index(drop=True),
                   well_dummies.reset_index(drop=True)], axis=1)
    return sm.add_constant(X)


def fit_four_zone_summer(panel):
    """Fit the four-zone summer-minima BACI model.

        summer_min ~ const + Post + zone:Post + well-FE

    The zone MAIN effects are collinear with the well-FE block (every
    well belongs to exactly one zone) and are absorbed — not added to
    the design.  No scraping term and no climate covariate (see module
    docstring).

    Parameters
    ----------
    panel : long-form DataFrame with columns
        well, zone, Summer_min_m, Post.

    Returns
    -------
    dict with the fitted model, per-zone step summaries, and the
    statsmodels result object.
    """
    panel = panel.copy()

    # zone:Post interaction columns, one per non-reference zone.
    inter_cols = []
    for z in NON_REF_ZONES:
        tag = ZONE_TAG[z]
        col = f'{tag}_x_Post'
        panel[col] = (panel['zone'] == z).astype(float) * panel['Post']
        inter_cols.append(col)

    ref_cols = ['Post'] + inter_cols
    X = _well_fe_design(panel, ref_cols)
    y = panel['Summer_min_m'].reset_index(drop=True)

    res = sm.OLS(y, X).fit(cov_type='cluster',
                           cov_kwds={'groups': panel['well'].values})

    def _term(name):
        b = res.params[name]
        se = res.bse[name]
        p = res.pvalues[name]
        return b, se, p, (b - 1.96 * se, b + 1.96 * se)

    zone_results = {}
    for z in NON_REF_ZONES:
        tag = ZONE_TAG[z]
        fb, fse, fp, fci = _term(f'{tag}_x_Post')
        # Per-zone well-year counts, split pre/post.
        zp = panel.loc[panel['zone'] == z]
        zone_results[z] = {
            'clearfell_step':     fb,
            'clearfell_step_se':  fse,
            'clearfell_p':        fp,
            'clearfell_ci_lo':    fci[0],
            'clearfell_ci_hi':    fci[1],
            'n_well_years':       int(len(zp)),
            'n_pre':              int((zp['Post'] == 0).sum()),
            'n_post':             int((zp['Post'] == 1).sum()),
            'n_wells':            int(zp['well'].nunique()),
        }

    ref_post = _term('Post')

    return {
        'res':            res,
        'zone_results':   zone_results,
        'ref_post_b':     ref_post[0],
        'ref_post_p':     ref_post[2],
        'R2':             res.rsquared,
        'N':              int(res.nobs),
        'n_wells':        panel['well'].nunique(),
    }


# ============================================================================
# PAIRWISE CONTRASTS
# ============================================================================

def compute_pairwise_contrasts(fit):
    """All six ordered pairwise summer-minimum felling contrasts.

    Each non-reference zone's felling step is its {tag}_x_Post
    coefficient (the zone-vs-Forest differential); zone-vs-zone
    contrasts are linear combinations, evaluated with the shared
    covariance matrix so the arithmetic identity holds exactly.
    Identical method to Script 10k's compute_pairwise_contrasts().

    contrast_type — see Script 10k's compute_pairwise_contrasts
    docstring for the full explanation.  In brief: 'primary' rows are
    direct zone-vs-Forest coefficients (SE/p interpreted normally);
    'derived' rows are zone-vs-zone linear combinations whose SE/p
    depend on the coefficient covariance and are NOT comparable to the
    primary rows — a contrast between two correlated control-like zones
    has an artificially deflated SE and small p that is not independent
    evidence.  Report the primary contrasts.

    Returns
    -------
    list of dicts, one per ordered pair, each with
        contrast, step_m, se_m, ci_lo_m, ci_hi_m, p, contrast_type,
        identity_check
    """
    res = fit['res']
    params = list(res.params.index)

    def _lc_vector(coef_weights):
        v = np.zeros(len(params))
        for name, w in coef_weights.items():
            v[params.index(name)] = w
        return v

    def _contrast(label, coef_weights, contrast_type, identity=''):
        v = _lc_vector(coef_weights)
        t = res.t_test(v)
        b = float(np.asarray(t.effect).ravel()[0])
        se = float(np.asarray(t.sd).ravel()[0])
        p = float(np.asarray(t.pvalue).ravel()[0])
        return {
            'contrast':       label,
            'step_m':         round(b, 4),
            'se_m':           round(se, 4),
            'ci_lo_m':        round(b - 1.96 * se, 4),
            'ci_hi_m':        round(b + 1.96 * se, 4),
            'p':              p,
            'contrast_type':  contrast_type,
            'identity_check': identity,
        }

    post = {z: f'{ZONE_TAG[z]}_x_Post' for z in NON_REF_ZONES}
    rows = []

    # PRIMARY — zone-vs-Forest (direct model coefficients).
    for z in NON_REF_ZONES:
        rows.append(_contrast(f'{z} - Forest', {post[z]: +1.0}, 'primary'))

    # DERIVED — zone-vs-zone (linear combinations; SE/p not comparable).
    rows.append(_contrast('Impact - Edge',
                           {post['Impact']: +1.0, post['Edge']: -1.0},
                           'derived'))
    rows.append(_contrast('Impact - C3/Warren',
                           {post['Impact']: +1.0, post['C3/Warren']: -1.0},
                           'derived'))
    rows.append(_contrast('Edge - C3/Warren',
                           {post['Edge']: +1.0, post['C3/Warren']: -1.0},
                           'derived'))

    rows.append(_contrast(
        '(Impact-Forest) - (Edge-Forest)',
        {post['Impact']: +1.0, post['Edge']: -1.0},
        'identity_check',
        identity='equals Impact - Edge row above (shared covariance)'))

    return rows


# ============================================================================
# 10j SUMMER CROSS-CHECK
# ============================================================================

def crosscheck_against_10j_summer(contrasts, tol=0.02):
    """Compare the four-zone Impact−Edge summer contrast with Script 10j.

    Both 10l and 10j fit a well-FE, cluster-robust summer-minima model;
    10j's two-zone summer contrast and 10l's four-zone Impact−Edge
    contrast estimate the same quantity on overlapping data, so they
    should be close.  They are not guaranteed equal — 10l conditions on
    the full four-zone panel — so a moderate difference is acceptable
    and the advisory tolerance is wider than 10k's monthly cross-check.
    This function prints the comparison and returns the delta; it does
    not hard-fail.

    Parameters
    ----------
    contrasts : list of contrast dicts from compute_pairwise_contrasts().
    tol : float
        Advisory tolerance in metres (annual estimates are noisier than
        monthly, hence wider than 10k's 5 mm).

    Returns
    -------
    dict with the 10l value, the 10j value (or None), and their delta.
    """
    ie = next((c for c in contrasts
               if c['contrast'] == 'Impact - Edge'), None)
    if ie is None:
        note("Impact - Edge contrast not found — skipped")
        return {'ok': False}

    l_val = ie['step_m']

    if not OUT_10J_SUMMER_RESULTS.exists():
        print(f"   [crosscheck] 10j summer output not found at "
              f"{OUT_10J_SUMMER_RESULTS.name} — run 10j first for the "
              f"cross-check.\n"
              f"               10l Impact-Edge summer = {l_val*1000:+.1f} mm")
        return {'ok': False, 'tenl': l_val, 'tenj': None, 'delta': None}

    j_df = pd.read_csv(OUT_10J_SUMMER_RESULTS)
    j_val = float(j_df['clearfell_step_m'].iloc[0])
    delta = l_val - j_val

    note("Impact - Edge differential summer-minimum step:")
    print(f"      10l four-zone contrast : {l_val*1000:+8.1f} mm")
    print(f"      10j two-zone estimator : {j_val*1000:+8.1f} mm")
    print(f"      delta (10l - 10j)      : {delta*1000:+8.1f} mm  "
          f"(advisory tol = {tol*1000:.1f} mm)")
    if abs(delta) > tol:
        print("      [NOTE] delta exceeds advisory tolerance.  A moderate "
              "difference is\n"
              "             expected (the four-zone panel conditions the "
              "fit on Forest +\n"
              "             C3/Warren wells too, and annual estimates are "
              "noisier than\n"
              "             monthly).  Record the observed delta in the "
              "changelog.")
    else:
        info("within advisory tolerance.")
    return {'ok': True, 'tenl': l_val, 'tenj': j_val, 'delta': delta}


# ============================================================================
# OUTPUT WRITERS
# ============================================================================

def write_zone_results_csv(fit, path):
    """One row per non-reference zone — the primary results table."""
    rows = []
    for z in NON_REF_ZONES:
        zr = fit['zone_results'][z]
        rows.append({
            'zone':                 z,
            'vs_reference':         REFERENCE_ZONE,
            'clearfell_step_m':     round(zr['clearfell_step'], 4),
            'clearfell_step_se_m':  round(zr['clearfell_step_se'], 4),
            'clearfell_ci_lo_m':    round(zr['clearfell_ci_lo'], 4),
            'clearfell_ci_hi_m':    round(zr['clearfell_ci_hi'], 4),
            'clearfell_p':          zr['clearfell_p'],
            'n_wells':              zr['n_wells'],
            'n_well_years':         zr['n_well_years'],
            'n_pre':                zr['n_pre'],
            'n_post':               zr['n_post'],
            'R2':                   round(fit['R2'], 4),
            'N':                    fit['N'],
        })
    pd.DataFrame(rows).to_csv(path, index=False)


def write_pairwise_csv(contrasts, path):
    """Pairwise contrasts CSV, with primary and derived rows segregated.

    Identical structure to Script 10k's write_pairwise_csv: SE/CI/p for
    'primary' rows go in se_m / ci_lo_m / ci_hi_m / p; for 'derived'
    rows they go in se_m_derived / ci_lo_m_derived / ci_hi_m_derived /
    p_derived.  The primary p column is blank on derived rows, so a
    derived contrast's covariance-deflated p cannot be lifted from the
    'p' column into a results table.  An 'interpretation' column states
    per row how it should be used.
    """
    interp = {
        'primary':
            'Primary — direct model coefficient (zone vs Forest). '
            'SE and p interpreted normally.',
        'derived':
            'Derived — exact linear combination of two primary '
            'coefficients. Point estimate exact; SE/p depend on the '
            'coefficient covariance and are NOT comparable to primary '
            'rows. Do not cite p_derived as significance.',
        'identity_check':
            'Identity check — demonstrates (Impact-Forest)-(Edge-Forest) '
            '= Impact-Edge. Not a result.',
    }
    out = []
    for c in contrasts:
        ct = c['contrast_type']
        row = {
            'contrast':       c['contrast'],
            'contrast_type':  ct,
            'step_m':         c['step_m'],
        }
        if ct == 'primary':
            row.update({
                'se_m': c['se_m'], 'ci_lo_m': c['ci_lo_m'],
                'ci_hi_m': c['ci_hi_m'], 'p': c['p'],
                'se_m_derived': '', 'ci_lo_m_derived': '',
                'ci_hi_m_derived': '', 'p_derived': '',
            })
        else:
            row.update({
                'se_m': '', 'ci_lo_m': '', 'ci_hi_m': '', 'p': '',
                'se_m_derived': c['se_m'], 'ci_lo_m_derived': c['ci_lo_m'],
                'ci_hi_m_derived': c['ci_hi_m'], 'p_derived': c['p'],
            })
        row['interpretation'] = interp[ct]
        out.append(row)
    pd.DataFrame(out).to_csv(path, index=False)


def write_c3warren_minima_csv(c3_minima, path):
    """Write the C3/Warren summer minima as canonical pipeline output.

    10d does not cover the C3/Warren zone; this CSV is the canonical
    record of that zone's annual Jun-Sep minima, on the same Defect-E
    (provenance, min_measured=2) basis as 10d_01_summer_minima.csv.
    """
    c3_minima.to_csv(path, index=False)


def write_report_numbers(fit, contrasts, path):
    """Standard ReportNumbers CSV with FourZoneSummer_* keys."""
    rn = ReportNumbers()

    for z in NON_REF_ZONES:
        zr = fit['zone_results'][z]
        tag = ZONE_TAG[z]
        rn.add(f'FourZoneSummer_{tag}_clearfell_step',
               zr['clearfell_step'], well=z, era='Post_felling_Jun-Sep',
               note=f"vs {REFERENCE_ZONE}; p={zr['clearfell_p']:.4f}, "
                    f"CI=[{zr['clearfell_ci_lo']:.4f},"
                    f"{zr['clearfell_ci_hi']:.4f}]")
        rn.add(f'FourZoneSummer_{tag}_clearfell_step_se',
               zr['clearfell_step_se'], well=z, era='Post_felling_Jun-Sep')
        rn.add(f'FourZoneSummer_{tag}_N', zr['n_well_years'],
               unit='well-years', well=z, era='Jun-Sep',
               note=f"n_pre={zr['n_pre']}, n_post={zr['n_post']}, "
                    f"n_wells={zr['n_wells']}")

    rn.add('FourZoneSummer_R2', fit['R2'], unit='', well='all_zones',
           note='Joint model R²')
    rn.add('FourZoneSummer_N', fit['N'], unit='well-years',
           well='all_zones', note='Pooled-panel sample size')

    # Pairwise contrasts (skip the identity-demonstration row).
    # Derived contrasts are tagged in the note so their
    # covariance-deflated p is not mistaken for a primary result.
    for c in contrasts:
        if c['contrast_type'] == 'identity_check':
            continue
        key = ('FourZoneSummer_contrast_'
               + c['contrast'].replace(' - ', '_vs_')
                              .replace('/', '')
                              .replace(' ', ''))
        if c['contrast_type'] == 'primary':
            note = (f"primary; p={c['p']:.4f}, "
                    f"CI=[{c['ci_lo_m']:.4f},{c['ci_hi_m']:.4f}]")
        else:
            note = (f"DERIVED contrast — point estimate exact, but SE/p "
                    f"are covariance-dependent and not comparable to "
                    f"primary contrasts; do not cite as significance "
                    f"(p_derived={c['p']:.4f})")
        rn.add(key, c['step_m'], well=c['contrast'],
               era='Post_felling_Jun-Sep', note=note)

    rn.save(path)


# ============================================================================
# FIGURES
# ============================================================================

def _save_jpeg(fig, out_path):
    """Save a figure, enforcing the pipeline JPEG-quality-85 convention.

    matplotlib routes JPEG quality through ``pil_kwargs``; the bare
    ``quality=`` kwarg is silently ignored, so it must be passed this
    way (matching Scripts 09b, 09d, 10k, 21, 25).
    """
    is_jpeg = str(out_path).lower().endswith('.jpg')
    render_figure(
        fig, out_path,
        format='jpeg' if is_jpeg else None,
        pil_kwargs={'quality': 85} if is_jpeg else None,
    )
    plt.close(fig)


def figure_zone_summer_trajectories(panel, fit, out_path):
    """Annual summer-minima trajectories — per-well thin lines, zone means.

    Each series is reindexed onto the full continuous year range so that
    a year a well (or a whole zone) has no summer minimum becomes an
    explicit NaN.  matplotlib breaks the line at a NaN rather than
    drawing a straight segment across the gap — e.g. WMC3 has no 2019
    summer minimum (its 2019 Jun-Sep window fails the >=2-measured
    rule), so the Impact line must show a break at 2019, not a bridge
    from 2018 to 2020.
    """
    fig, ax = plt.subplots(figsize=(11, 5.5))

    year_min = int(panel['Year'].min())
    year_max = int(panel['Year'].max())
    all_years = list(range(year_min, year_max + 1))

    for z in ZONE_WELLS:
        zp = panel.loc[panel['zone'] == z]
        # Per-well thin lines — reindexed to continuous years so a
        # missing year is a NaN and the line breaks there.
        for well, wg in zp.groupby('well'):
            ws = (wg.set_index('Year')['Summer_min_m']
                    .reindex(all_years))
            ax.plot(ws.index, ws.values,
                    '-', color=ZONE_COLOURS[z], alpha=0.30, lw=0.8)
        # Zone mean (bold) — also reindexed, so a year in which the
        # whole zone has no data breaks the mean line too.
        zmean = (zp.groupby('Year')['Summer_min_m'].mean()
                   .reindex(all_years))
        lw = 2.4 if z in ('Impact', 'Forest') else 1.8
        ax.plot(zmean.index, zmean.values, '-o',
                color=ZONE_COLOURS[z], lw=lw, ms=4,
                label=f'{z}' + (' (ref)' if z == REFERENCE_ZONE else ''))

    ax.axvline(2015.0, color='grey', ls='--', alpha=0.7,
               label='Apr 2015 scraping')
    ax.axvline(INTERVENTION_DATE.year + 0.5, color='k', ls='--', alpha=0.8,
               label='Dec 2017 felling')
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual Jun–Sep minimum water-table depth (m)')
    ax.set_title('Four-zone summer minima — annual Jun–Sep minimum by zone')
    ax.legend(loc='lower right', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)

    imp = fit['zone_results']['Impact']
    fig.suptitle(
        f"Four-zone summer-minima BACI — Impact vs Forest felling step "
        f"= {imp['clearfell_step']*1000:+.1f} mm "
        f"(95% CI [{imp['clearfell_ci_lo']*1000:+.1f}, "
        f"{imp['clearfell_ci_hi']*1000:+.1f}], p = {imp['clearfell_p']:.4f})",
        fontsize=10)
    plt.tight_layout(rect=(0, 0, 1, 0.96))
    _save_jpeg(fig, out_path)


def figure_summer_forest_plot(contrasts, out_path):
    """Forest-plot of the pairwise summer contrasts, primary vs derived.

    Split into two labelled groups (PRIMARY zone-vs-Forest, dark;
    DERIVED zone-vs-zone, greyed) so the six rows are not read as
    co-equal results.  Derived rows are annotated without a p-value
    because their SE/CI are covariance-dependent and not comparable to
    the primary rows.  See Script 10k's figure_forest_plot.
    """
    primary = [c for c in contrasts if c['contrast_type'] == 'primary']
    derived = [c for c in contrasts if c['contrast_type'] == 'derived']

    GAP = 1
    n = len(primary) + len(derived) + GAP
    y_primary = list(range(n - 1, n - 1 - len(primary), -1))
    y_derived = list(range(n - 1 - len(primary) - GAP,
                           n - 1 - len(primary) - GAP - len(derived), -1))

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    ax.axvline(0, color='grey', ls='-', alpha=0.6)

    def _plot_group(group, ys, colour, ecolour, faded):
        for c, yi in zip(group, ys):
            step = c['step_m'] * 1000
            lo, hi = c['ci_lo_m'] * 1000, c['ci_hi_m'] * 1000
            ax.errorbar([step], [yi],
                        xerr=[[step - lo], [hi - step]],
                        fmt='o', color=colour, ecolor=ecolour,
                        capsize=4, ms=6, lw=1.5)
            if faded:
                txt = f"{step:+.0f} mm  (derived — see caption)"
            else:
                txt = f"{step:+.0f} mm, p={c['p']:.3f}"
            ax.annotate(txt, xy=(hi, yi), xytext=(6, 0),
                        textcoords='offset points', va='center',
                        fontsize=8, color=ecolour)

    _plot_group(primary, y_primary, '#2E3440', '#4C566A', faded=False)
    _plot_group(derived, y_derived, '#9aa4b2', '#aab2bd', faded=True)

    all_y = y_primary + y_derived
    ax.set_yticks(all_y)
    ax.set_yticklabels([c['contrast'] for c in primary]
                       + [c['contrast'] for c in derived])
    for tick, yi in zip(ax.get_yticklabels(), all_y):
        if yi in y_derived:
            tick.set_color('#9aa4b2')

    div = n - 1 - len(primary) - GAP / 2
    ax.axhline(div, color='#d0d0d0', ls='-', lw=0.8)
    ax.text(0.015, y_primary[0] + 0.55, 'PRIMARY — zone vs Forest reference '
            '(direct coefficients)', transform=ax.get_yaxis_transform(),
            fontsize=8, fontweight='bold', color='#2E3440', va='bottom')
    ax.text(0.015, y_derived[0] + 0.55, 'DERIVED — zone vs zone '
            '(linear combinations; CIs not comparable)',
            transform=ax.get_yaxis_transform(),
            fontsize=8, fontweight='bold', color='#9aa4b2', va='bottom')

    ax.set_ylim(min(all_y) - 0.8, max(all_y) + 1.4)
    ax.set_xlabel('Differential summer-minimum felling step (mm)')
    ax.set_title('Four-zone summer-minima BACI — pairwise contrasts',
                 fontsize=11)
    ax.grid(True, axis='x', alpha=0.3)

    caption = (
        "Primary contrasts (dark) are direct model coefficients — estimate, "
        "SE and p interpreted normally.  Derived contrasts (grey) are exact "
        "linear combinations of the primary coefficients: the point estimate "
        "is exact, but the SE/CI depend on the covariance between the two "
        "zones and are NOT comparable to the primary rows — a contrast "
        "between two correlated control-like zones has an artificially "
        "narrow CI.  Report the primary contrasts; Impact−Edge is "
        "corroborated independently by Script 10j.")
    fig.text(0.5, -0.04, caption, ha='center', va='top', fontsize=7,
             color='#4C566A', wrap=True)

    plt.tight_layout()
    _save_jpeg(fig, out_path)


# ============================================================================
# MAIN
# ============================================================================

def main():
    banner("10l", "Four-Zone Summer Minima", version="1.0.0")
    print("=" * 72)
    print("Script 10l — Four-zone summer-minima clearfell BACI")
    print("=" * 72)

    make_all_dirs()

    print("\n  Loading data ...")
    wells, wells_provenance, _climate, _master, _locs, _valid = \
        load_clearfell_data()

    print(f"  Zones (reference = {REFERENCE_ZONE} control):")
    for z, wl in ZONE_WELLS.items():
        ref = ' [reference]' if z == REFERENCE_ZONE else ''
        print(f"    {z:<11}: {', '.join(w.upper() for w in wl)}{ref}")
    print(f"  Annual frame: {FIRST_YEAR}+ (matches Script 10d cutoff)")
    print(f"  Post-felling summers: {INTERVENTION_DATE.year + 1}+")
    print()

    # ── 1. Build the four-zone summer panel ─────────────────────────────
    print("  1. Building four-zone summer-minima panel ...")
    print(f"     Forest/Edge/Impact zones ← {OUT_10D_DATA.name}")
    print("     C3/Warren zone           ← computed here "
          "(10d does not cover it)")
    panel, c3_minima = build_summer_panel(wells, wells_provenance)
    print(f"     n_rows = {len(panel)} well-years, "
          f"n_wells = {panel['well'].nunique()}")
    for z in ZONE_WELLS:
        zp = panel.loc[panel['zone'] == z]
        print(f"       {z:<11}: {zp['well'].nunique()} wells, "
              f"{len(zp)} well-years "
              f"({int((zp['Post']==0).sum())} pre, "
              f"{int((zp['Post']==1).sum())} post)")
    print()

    # ── 2. Fit the four-zone summer model ───────────────────────────────
    print("  2. Fitting four-zone summer-minima model ...")
    print("     summer_min ~ const + Post + zone:Post + well-FE  "
          "(no scraping, no CWB)")
    fit = fit_four_zone_summer(panel)
    for z in NON_REF_ZONES:
        zr = fit['zone_results'][z]
        print(f"     {z:<11} vs Forest: "
              f"{zr['clearfell_step']*1000:+8.1f} mm  "
              f"95% CI [{zr['clearfell_ci_lo']*1000:+7.1f}, "
              f"{zr['clearfell_ci_hi']*1000:+7.1f}]  "
              f"p={zr['clearfell_p']:.4f}")
    print(f"     N = {fit['N']} well-years, R² = {fit['R2']:.3f}")
    print()
    print("     [reminder] C3/Warren is a SECOND CONTROL zone — "
          "phi_C3Warren ~ 0 is the\n"
          "                expected result; a clearly non-zero step is a "
          "flag, not a finding.")
    print()

    # ── 3. Pairwise contrasts ───────────────────────────────────────────
    print("  3. Computing pairwise contrasts (shared covariance) ...")
    contrasts = compute_pairwise_contrasts(fit)
    print("     [primary = direct coefficient; derived = linear "
          "combination, SE/p not comparable]")
    for c in contrasts:
        ct = c['contrast_type']
        if ct == 'identity_check':
            print(f"     {c['contrast']:<34} "
                  f"{c['step_m']*1000:+8.1f} mm   [{c['identity_check']}]")
        elif ct == 'primary':
            print(f"     {c['contrast']:<34} "
                  f"{c['step_m']*1000:+8.1f} mm  p={c['p']:.4f}  [primary]")
        else:  # derived
            print(f"     {c['contrast']:<34} "
                  f"{c['step_m']*1000:+8.1f} mm  "
                  f"(derived — p not comparable)")
    print()

    # ── 4. 10j summer cross-check ───────────────────────────────────────
    print("  4. Cross-check against Script 10j summer contrast ...")
    crosscheck_against_10j_summer(contrasts)
    print()

    # ── 5. Write outputs ────────────────────────────────────────────────
    print("  5. Writing outputs ...")
    write_zone_results_csv(fit, OUT_10L_ZONE_RESULTS)
    saved(f"{OUT_10L_ZONE_RESULTS.name}")
    write_pairwise_csv(contrasts, OUT_10L_PAIRWISE)
    saved(f"{OUT_10L_PAIRWISE.name}")
    write_c3warren_minima_csv(c3_minima, OUT_10L_SUMMER_MINIMA)
    print(f"     → {OUT_10L_SUMMER_MINIMA.name} "
          f"({len(c3_minima)} rows, canonical C3/Warren summer minima)")
    write_report_numbers(fit, contrasts, OUT_10L_REPORT)
    saved(f"{OUT_10L_REPORT.name}")

    # ── 6. Figures ──────────────────────────────────────────────────────
    print("  6. Building figures ...")
    figure_zone_summer_trajectories(panel, fit, OUT_10L_TRAJECTORY_FIG)
    saved(f"{OUT_10L_TRAJECTORY_FIG.name}")
    figure_summer_forest_plot(contrasts, OUT_10L_FOREST_PLOT)
    saved(f"{OUT_10L_FOREST_PLOT.name}")

    # ── 7. Site-observations registry ───────────────────────────────────
    print("  7. Updating site-observations registry ...")
    update_site_observation(
        'four_zone_summer_step_impact',
        fit['zone_results']['Impact']['clearfell_step'],
        producer_script='10l')
    update_site_observation(
        'four_zone_summer_step_edge',
        fit['zone_results']['Edge']['clearfell_step'],
        producer_script='10l')
    update_site_observation(
        'four_zone_summer_step_c3warren',
        fit['zone_results']['C3/Warren']['clearfell_step'],
        producer_script='10l')
    saved("3 entries updated in pipeline_site_observations.csv")
    print()
    print("Script 10l complete.")


if __name__ == '__main__':
    main()
