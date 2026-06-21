r"""

====================================================================================
10k — FOUR-ZONE POOLED-PANEL CLEARFELL BACI
====================================================================================

A single pooled-panel BACI model that replaces the three-separate-ANCOVA
structure of Script 10a (Forest / Climate / Pooled controls) with one
regression in which zone is a four-level factor.  The four zones are:

    Forest control  (reference)  — ceh32, ceh34, ceh33, nw10, ceh2
    C3 / Warren                  — ceh1, nw1, nw2, nw11
    Edge                         — ceh31, ceh20, ceh30, ceh16
    Impact                       — wmc3

Because every pairwise contrast comes from one coefficient vector with
one shared covariance matrix, the contrasts are internally consistent
and exactly subtractable:

    (Impact − Forest) − (Edge − Forest)  =  Impact − Edge   (exactly)

This is the same estimator as Script 10j's two-zone Impact-vs-Edge
contrast, generalised from two zones to four.  10j is NOT replaced — it
remains a valid standalone two-zone estimator, and its monthly
Impact-vs-Edge step reappears here, by construction, as one row of the
pairwise-contrast table.  Agreement between the two is asserted as a
built-in validation check.

Model (monthly-mean panel, one row per well-month from PRE_FELL_START_FOURZONE)
---------------------------------------------------------------------
    h ~ const + CWB
          + zone:CWB                      (zone × climate sensitivity)
          + Scraped1 + zone:Scraped1       (zone-asymmetric 2015 scraping)
          + Post     + zone:Post           (zone-asymmetric felling step)
          + easting × time                 (single network-wide covariate)
          + well-FE

  - Forest control is the reference level; the zone:Post coefficients are
    therefore the differential felling steps relative to Forest control.
  - The zone MAIN effects are collinear with the well-FE block (every
    well belongs to exactly one zone) and are absorbed into the well
    dummies — they are NOT added to the design matrix.
  - OLS with cluster-robust SE on well (handles within-well autocorr;
    degrades gracefully for the n=1 Impact zone).
  - Binary Scraped1 (Apr 2015), zone-interacted — following 10j, not the
    distance-weighted decay covariate that 10a uses.  The Oct 2023
    re-scrape is NOT modelled (post-2023 window too short).
  - easting × time is a single network-wide covariate.  It absorbs any
    easting-correlated trend, not coastal retreat alone.  The
    with/without-easting comparison (10k_03) is a robustness diagnostic,
    NOT an erosion decomposition — coastal-retreat magnitude is estimated
    independently by Script 25.

Scientific note — the C3/Warren zone is a SECOND CONTROL
--------------------------------------------------------
C3/Warren is the open western-dune zone.  Forest-management
perturbations propagate south-westward off the bedrock ridge; the
C3/Warren wells are all > 500 m from the felled compartment and none
lie in that propagation sector.  The zone is therefore expected to be
shielded from the felling signal: the EXPECTED RESULT IS
phi_{C3/Warren} ≈ 0, behaving like the Forest control.  A clearly
non-zero C3/Warren step is to be treated as a flag (possible unshielded
propagation or another confound), NOT as a felling finding.  See the
four-zone BACI design spec §4.4 and its decision record (Item B).

Relationship to Script 10a
--------------------------
This script is the PRIMARY §4.6 clearfell result.  10a's three separate
ANCOVAs are retained as a robustness panel ("the same contrasts as
independent fits give consistent signs and overlapping intervals") and
are not deleted.  10a continues to emit 10a_report_numbers.csv unchanged,
so Script 21's dependency on it is undisturbed.  10k emits its own
report-numbers CSV with FourZone_* keys — no key collision with 10a's
ANCOVA_* keys or 10j's ImpactVsEdge_* keys.

The four-zone joint fit does NOT reproduce 10a's separate-fit
Forest-control headline (≈ +135 mm).  The joint model estimates climate
sensitivity from the full cross-zone record, so the felling step absorbs
less climate variance; the joint Impact-vs-Forest step is consequently
smaller (design-session ad-hoc ≈ +33 mm).  This is a substantive,
defensible change to the headline — see the design spec §6 for how §4.6
presents it.

Dependencies
------------
  utils/clearfell_common.py — well lists incl. C3_WARREN_WELLS, dates,
                              data loading, CWB, PRE_FELL_START_FOURZONE
  utils/site_observations  — registry of site-wide observations
  utils/paths              — output paths

Outputs
-------
  outputs/10_clearfell_baci/10k_01_four_zone_results.csv
  outputs/10_clearfell_baci/10k_02_pairwise_contrasts.csv
  outputs/10_clearfell_baci/10k_03_easting_sensitivity.csv
  outputs/10_clearfell_baci/10k_04_zone_centroids.jpg
  outputs/10_clearfell_baci/10k_05_contrast_forest.jpg
  outputs/10_clearfell_baci/10k_06_forest_plot.jpg
  outputs/10_clearfell_baci/10k_report_numbers.csv

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
import matplotlib.dates as mdates

from utils.paths import (
    make_all_dirs,
    OUT_10K_ZONE_RESULTS, OUT_10K_PAIRWISE, OUT_10K_EASTING_SENS,
    OUT_10K_CENTROIDS_FIG, OUT_10K_CONTRAST_FIG, OUT_10K_FOREST_PLOT,
    OUT_10K_REPORT, OUT_10J_MONTHLY_RESULTS,
)
from utils.clearfell_common import (
    load_clearfell_data, INTERVENTION_DATE, SCRAPING_DATE,
    PRE_FELL_START_FOURZONE, IMPACT_WELLS, EDGE_WELLS, FOREST_CONTROL_WELLS,
    C3_WARREN_WELLS, compute_cwb, ReportNumbers, TIER_COLOURS,
)
from utils.site_observations import update_site_observation

__version__ = "1.2.0"  # Hollingham (2026) — 2026-05-22
# 1.2.0 — Pairwise contrasts now carry a contrast_type field
#         (primary / derived / identity_check).  The six contrasts are
#         not co-equal: 'primary' are direct zone-vs-Forest
#         coefficients; 'derived' are zone-vs-zone linear combinations
#         whose SE/p are covariance-dependent and NOT comparable to the
#         primary rows.  Structural changes so the outputs stop
#         inviting that misreading: the forest plot (10k_06) splits
#         into labelled PRIMARY (dark) and DERIVED (greyed) groups with
#         a caption; the pairwise CSV (10k_02) puts derived SE/CI/p in
#         separate *_derived columns (primary p column blank on derived
#         rows) plus an interpretation column; report-numbers notes tag
#         derived keys.  No model or numerical change — estimates are
#         identical; only presentation.
# 1.1.0 — Panel now starts at PRE_FELL_START_FOURZONE (2011-01-01)
#         instead of the legacy PRE_FELL_START (2010-07-01).  The
#         Jan-Sep 2010 months are a monitoring-network installation
#         ramp (several Forest-control wells not yet in), which
#         contaminates the pre-felling baseline; 2011-01 is the first
#         full calendar year clear of the ramp and matches the
#         four-zone summer panel's 2011 start.  Headline numbers
#         regenerate.
# 1.0.0 — Initial.  Four-zone pooled-panel clearfell BACI generalising
#         the Script 10j two-zone Impact-vs-Edge estimator to four
#         zones (Forest ref / C3-Warren / Edge / Impact).  Monthly-mean
#         panel only — the summer-minima four-zone model is a committed
#         Phase 2 in a separate session.  Reads well lists, dates and
#         PRE_FELL_START_FOURZONE from clearfell_common; writes three
#         site-observation entries.  No hardcoded site-specific values.


# ============================================================================
# ZONE DEFINITIONS
# ============================================================================
# Forest control is the REFERENCE level; the other three zones are the
# non-reference levels whose zone:Post coefficients are the differential
# felling steps.  Order here fixes the factor-level order.
REFERENCE_ZONE = 'Forest'

ZONE_WELLS = {
    'Forest':     FOREST_CONTROL_WELLS,   # reference — ceh32,ceh34,ceh33,nw10,ceh2
    'C3/Warren':  C3_WARREN_WELLS,        # ceh1,nw1,nw2,nw11
    'Edge':       EDGE_WELLS,             # ceh31,ceh20,ceh30,ceh16
    'Impact':     IMPACT_WELLS,           # wmc3
}
NON_REF_ZONES = ['C3/Warren', 'Edge', 'Impact']

# Zone plot colours.  Forest/Edge/Impact reuse the canonical TIER_COLOURS;
# C3/Warren takes a distinct blue-grey (open western dune).
ZONE_COLOURS = {
    'Forest':     TIER_COLOURS['Forest Ctrl'],
    'C3/Warren':  '#5E81AC',
    'Edge':       TIER_COLOURS['Edge'],
    'Impact':     TIER_COLOURS['Impact'],
}

# Safe column-name fragment per zone (no slashes / spaces) for the
# interaction-term column names and the report-number keys.
ZONE_TAG = {
    'Forest':     'Forest',
    'C3/Warren':  'C3Warren',
    'Edge':       'Edge',
    'Impact':     'Impact',
}


# ============================================================================
# PANEL BUILDER
# ============================================================================

def build_monthly_panel(wells, climate):
    """Build the four-zone long-form monthly panel from PRE_FELL_START_FOURZONE.

    One row per (well, month) for every well in the four zones, for every
    month from PRE_FELL_START_FOURZONE onward.  The dependent variable is the
    well's own monthly water-table depth `h` (m, negative below ground) —
    not a BACI displacement series.

    Parameters
    ----------
    wells : pd.DataFrame
        Monthly well depths, lowercase column names.
    climate : pd.DataFrame
        Monthly climate (P_m, PET).

    Returns
    -------
    panel : long-form DataFrame with columns
        date, well, zone, h, cwb, easting, Scraped1, Post
    """
    cwb_series = compute_cwb(climate)
    cwb_series = cwb_series - cwb_series.mean()

    # Time index for the easting × time covariate: months since the
    # earliest panel month.  Built once the panel dates are known below.
    records = []
    for zone, well_list in ZONE_WELLS.items():
        for well in well_list:
            if well not in wells.columns:
                print(f"    [WARN] well not in data: {well} (zone {zone})")
                continue
            s = wells[well].dropna()
            s = s.loc[s.index >= PRE_FELL_START_FOURZONE]
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


def attach_easting(panel, well_locations, master=None):
    """Attach the easting × time covariate to the panel.

    The easting × time covariate is well_easting × months-since-record-
    start.  It is a SINGLE network-wide covariate (not zone-interacted):
    it absorbs any easting-correlated trend.  See module docstring — this
    is a control term, not an erosion measurement.

    Parameters
    ----------
    panel : DataFrame from build_monthly_panel().
    well_locations : dict {well: {'easting': float, 'northing': float}}.
        As returned by load_clearfell_data().  This dict is populated
        only for wells in ALL_NETWORK_WELLS — it therefore does NOT
        contain the C3/Warren zone wells, which are deliberately not part
        of that five-tier constant.
    master : pd.DataFrame or None
        Script 03 master data (the 4th return of load_clearfell_data),
        with 'well', 'Easting', 'Northing' columns.  Used as a fallback
        easting source for any panel well missing from well_locations —
        in practice the four C3/Warren wells.  If None, those wells'
        rows are dropped (and a warning is printed).

    Returns
    -------
    panel : the same DataFrame with an added 'easting_x_time' column.
        Rows for wells with no easting from either source are dropped.
    """
    panel = panel.copy()

    # Primary source: the well_locations dict from load_clearfell_data().
    easting_lookup = {w: loc['easting']
                      for w, loc in well_locations.items()}

    # Fallback source: the Script 03 master data, for panel wells (the
    # C3/Warren zone) that are not in ALL_NETWORK_WELLS and therefore
    # absent from well_locations.
    if master is not None:
        m = master.copy()
        if 'well' not in m.columns:
            m['well'] = m['Name_Original'].str.lower().str.replace(' ', '')
        for _, row in m.iterrows():
            w = row['well']
            if w not in easting_lookup:
                easting_lookup[w] = float(row['Easting'])

    eastings = panel['well'].map(easting_lookup)
    missing = sorted(panel.loc[eastings.isna(), 'well'].unique())
    if missing:
        print(f"    [WARN] no easting (well_locations or master) for: "
              f"{missing} — rows dropped")
    panel['easting'] = eastings
    panel = panel.dropna(subset=['easting'])

    # Months since the earliest panel month (a clean integer-ish time
    # index; absolute scale is immaterial since easting × time enters
    # only as a single linear covariate).
    t0 = panel['date'].min()
    months_since = ((panel['date'] - t0).dt.days / 30.4375)
    panel['easting_x_time'] = panel['easting'].values * months_since.values
    return panel


# ============================================================================
# MODEL FITTING
# ============================================================================

def _well_fe_design(df, ref_cols):
    """Design matrix with well fixed effects (drop-first dummies).

    Parameters
    ----------
    df : DataFrame with a 'well' column and the columns named in ref_cols.
    ref_cols : list of column names to place before the well-FE block.

    Returns
    -------
    X : DataFrame with constant, ref_cols, and well-FE columns.
    """
    well_dummies = pd.get_dummies(df['well'], prefix='well',
                                  drop_first=True, dtype=float)
    X = pd.concat([df[ref_cols].reset_index(drop=True),
                   well_dummies.reset_index(drop=True)], axis=1)
    return sm.add_constant(X)


def _build_zone_interactions(panel):
    """Add zone × {CWB, Scraped1, Post} interaction columns in place.

    For each non-reference zone z, adds three columns:
        {tag}_x_cwb, {tag}_x_Scraped1, {tag}_x_Post
    where tag = ZONE_TAG[z].  The reference zone (Forest) has no
    interaction columns — its effect is the model's baseline.

    Returns
    -------
    panel : copy with the interaction columns added.
    inter_cols : list of the interaction column names, in zone order.
    """
    panel = panel.copy()
    inter_cols = []
    for z in NON_REF_ZONES:
        tag = ZONE_TAG[z]
        is_z = (panel['zone'] == z).astype(float)
        c_cwb  = f'{tag}_x_cwb'
        c_scr  = f'{tag}_x_Scraped1'
        c_post = f'{tag}_x_Post'
        panel[c_cwb]  = is_z * panel['cwb']
        panel[c_scr]  = is_z * panel['Scraped1']
        panel[c_post] = is_z * panel['Post']
        inter_cols += [c_cwb, c_scr, c_post]
    return panel, inter_cols


def fit_four_zone(panel, include_easting=True):
    """Fit the four-zone pooled-panel BACI model.

    h ~ const + cwb + zone:cwb + Scraped1 + zone:Scraped1
          + Post + zone:Post + [easting_x_time] + well-FE

    The zone MAIN effects are collinear with the well-FE block and are
    absorbed — they are not added to the design.  The Impact zone is a
    single well; its zone:Post interaction is still identified by WMC3's
    own within-well pre/post contrast (cluster-robust SE degrade
    gracefully for the n=1 zone).

    Parameters
    ----------
    panel : long-form DataFrame with columns
        well, zone, h, cwb, Scraped1, Post, easting_x_time.
    include_easting : bool
        If False, the easting × time covariate is dropped (used for the
        robustness/sensitivity run — NOT an erosion decomposition).

    Returns
    -------
    dict with the fitted model, per-zone step summaries, and the
    statsmodels result object (for downstream contrast tests).
    """
    panel, inter_cols = _build_zone_interactions(panel)

    ref_cols = ['cwb', 'Scraped1', 'Post'] + inter_cols
    if include_easting:
        ref_cols = ref_cols + ['easting_x_time']

    X = _well_fe_design(panel, ref_cols)
    y = panel['h'].reset_index(drop=True)

    res = sm.OLS(y, X).fit(cov_type='cluster',
                           cov_kwds={'groups': panel['well'].values})

    def _term(name):
        b = res.params[name]
        se = res.bse[name]
        p = res.pvalues[name]
        return b, se, p, (b - 1.96 * se, b + 1.96 * se)

    # Per-zone differential felling / scraping steps (vs Forest reference)
    zone_results = {}
    for z in NON_REF_ZONES:
        tag = ZONE_TAG[z]
        fb, fse, fp, fci = _term(f'{tag}_x_Post')
        sb, sse, sp, _   = _term(f'{tag}_x_Scraped1')
        cb, cse, cp, _   = _term(f'{tag}_x_cwb')
        zone_results[z] = {
            'clearfell_step':     fb,
            'clearfell_step_se':  fse,
            'clearfell_p':        fp,
            'clearfell_ci_lo':    fci[0],
            'clearfell_ci_hi':    fci[1],
            'scraping_step':      sb,
            'scraping_step_se':   sse,
            'scraping_p':         sp,
            'cwb_interaction':    cb,
            'cwb_interaction_se': cse,
            'cwb_interaction_p':  cp,
        }

    # Reference-zone (Forest) Post and Scraped1 main effects, for context.
    ref_post = _term('Post')
    ref_scr  = _term('Scraped1')

    return {
        'res':              res,
        'zone_results':     zone_results,
        'ref_post_b':       ref_post[0],
        'ref_post_p':       ref_post[2],
        'ref_scraping_b':   ref_scr[0],
        'ref_scraping_p':   ref_scr[2],
        'R2':               res.rsquared,
        'N':                int(res.nobs),
        'n_wells':          panel['well'].nunique(),
        'include_easting':  include_easting,
    }


# ============================================================================
# PAIRWISE CONTRASTS
# ============================================================================

def compute_pairwise_contrasts(fit):
    """All six ordered pairwise felling contrasts from the shared cov matrix.

    Each non-reference zone's felling step is its {tag}_x_Post coefficient
    (the zone-vs-Forest differential).  A contrast between two zones A and
    B is a linear combination of those coefficients:

        A − Forest      = +1 · A_x_Post
        A − B  (A,B≠ref)= +1 · A_x_Post  − 1 · B_x_Post

    statsmodels' t_test gives the linear-combination estimate, SE and p
    with the exact shared covariance matrix, so the arithmetic identity
    (Impact−Forest) − (Edge−Forest) = (Impact−Edge) holds to machine
    precision.

    contrast_type — IMPORTANT for interpretation
    ---------------------------------------------
    The six contrasts are NOT six co-equal results.  Each row carries a
    contrast_type field:

      'primary'          — a zone-vs-Forest contrast; a DIRECT model
                           coefficient.  Estimate, SE and p are direct
                           model output and are interpreted normally.
      'derived'          — a zone-vs-zone contrast; an exact linear
                           combination of two primary coefficients.  The
                           point estimate is exact, but the SE and p
                           depend on the COVARIANCE between the two
                           coefficients and are NOT comparable to the
                           primary ones.  Differencing two strongly
                           correlated zones (e.g. two control-like zones)
                           deflates the SE and produces a small p that
                           is NOT independent evidence of an effect.
      'identity_check'   — the explicit (Impact-Forest)-(Edge-Forest)
                           row, present only to demonstrate the identity.

    Reporting rule: report the 'primary' contrasts.  Impact-Edge,
    although 'derived', is additionally trustworthy because Script 10j
    reproduces it with an independent estimator — but cite that
    reproduction, not its p-value, as the reason.  The C3/Warren-bearing
    derived contrasts are internal consistency checks, not findings.

    Returns
    -------
    list of dicts, one per ordered pair, each with
        contrast, step_m, se_m, ci_lo_m, ci_hi_m, p, contrast_type,
        identity_check
    """
    res = fit['res']
    params = list(res.params.index)

    def _lc_vector(coef_weights):
        """Build a length-len(params) restriction vector from {name: weight}."""
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

    # Three zone-vs-Forest contrasts — PRIMARY (direct model coefficients).
    for z in NON_REF_ZONES:
        rows.append(_contrast(f'{z} - Forest', {post[z]: +1.0}, 'primary'))

    # Three zone-vs-zone contrasts — DERIVED (linear combinations; SE/p
    # depend on the coefficient covariance and are not comparable to the
    # primary contrasts — see the docstring).
    rows.append(_contrast('Impact - Edge',
                           {post['Impact']: +1.0, post['Edge']: -1.0},
                           'derived'))
    rows.append(_contrast('Impact - C3/Warren',
                           {post['Impact']: +1.0, post['C3/Warren']: -1.0},
                           'derived'))
    rows.append(_contrast('Edge - C3/Warren',
                           {post['Edge']: +1.0, post['C3/Warren']: -1.0},
                           'derived'))

    # Explicit arithmetic-identity demonstration row:
    #   (Impact-Forest) - (Edge-Forest) must equal (Impact-Edge).
    identity = _contrast(
        '(Impact-Forest) - (Edge-Forest)',
        {post['Impact']: +1.0, post['Edge']: -1.0},
        'identity_check',
        identity='equals Impact - Edge row above (shared covariance)')
    rows.append(identity)

    return rows


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
            'scraping_step_m':      round(zr['scraping_step'], 4),
            'scraping_p':           zr['scraping_p'],
            'cwb_interaction':      round(zr['cwb_interaction'], 4),
            'cwb_interaction_p':    zr['cwb_interaction_p'],
            'R2':                   round(fit['R2'], 4),
            'N':                    fit['N'],
        })
    pd.DataFrame(rows).to_csv(path, index=False)


def write_pairwise_csv(contrasts, path):
    """Pairwise contrasts CSV, with primary and derived rows segregated.

    The six contrasts are NOT co-equal.  To stop a derived contrast's
    covariance-deflated p-value being lifted into a results table as if
    it were a primary result, the CSV places SE/CI/p for 'primary' rows
    in the columns se_m / ci_lo_m / ci_hi_m / p, and for 'derived' rows
    in SEPARATELY NAMED columns se_m_derived / ci_lo_m_derived /
    ci_hi_m_derived / p_derived.  The primary p column is therefore
    blank on derived rows and vice versa — a derived p cannot be read
    from the 'p' column.  An 'interpretation' column states, per row,
    how it should be used.
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
            'step_m':         c['step_m'],   # point estimate — always exact
        }
        if ct == 'primary':
            row.update({
                'se_m': c['se_m'], 'ci_lo_m': c['ci_lo_m'],
                'ci_hi_m': c['ci_hi_m'], 'p': c['p'],
                'se_m_derived': '', 'ci_lo_m_derived': '',
                'ci_hi_m_derived': '', 'p_derived': '',
            })
        else:  # derived or identity_check
            row.update({
                'se_m': '', 'ci_lo_m': '', 'ci_hi_m': '', 'p': '',
                'se_m_derived': c['se_m'], 'ci_lo_m_derived': c['ci_lo_m'],
                'ci_hi_m_derived': c['ci_hi_m'], 'p_derived': c['p'],
            })
        row['interpretation'] = interp[ct]
        out.append(row)
    pd.DataFrame(out).to_csv(path, index=False)


def write_easting_sensitivity_csv(fit_with, fit_without, path):
    """Two rows per zone: with-easting and without-easting felling steps.

    This is a robustness diagnostic — does the felling conclusion survive
    removal of the easting × time covariate?  It is NOT an erosion
    decomposition: the with-minus-without difference is not "the coastal
    effect", because the easting term absorbs any easting-correlated
    trend, not coastal retreat alone.  Coastal-retreat magnitude is
    estimated independently by Script 25.
    """
    rows = []
    for z in NON_REF_ZONES:
        for label, fit in [('with_easting', fit_with),
                            ('without_easting', fit_without)]:
            zr = fit['zone_results'][z]
            rows.append({
                'zone':                z,
                'specification':       label,
                'clearfell_step_m':    round(zr['clearfell_step'], 4),
                'clearfell_step_se_m': round(zr['clearfell_step_se'], 4),
                'clearfell_p':         zr['clearfell_p'],
                'R2':                  round(fit['R2'], 4),
                'N':                   fit['N'],
            })
    df = pd.DataFrame(rows)
    df.attrs['note'] = ('Robustness diagnostic, not an erosion '
                        'decomposition — see Script 25 for coastal retreat.')
    df.to_csv(path, index=False)


def write_report_numbers(fit, contrasts, path):
    """Standard ReportNumbers CSV with FourZone_* keys."""
    rn = ReportNumbers()

    for z in NON_REF_ZONES:
        zr = fit['zone_results'][z]
        tag = ZONE_TAG[z]
        rn.add(f'FourZone_{tag}_clearfell_step',
               zr['clearfell_step'], well=z, era='Post_felling',
               note=f"vs {REFERENCE_ZONE}; p={zr['clearfell_p']:.4f}, "
                    f"CI=[{zr['clearfell_ci_lo']:.4f},"
                    f"{zr['clearfell_ci_hi']:.4f}]")
        rn.add(f'FourZone_{tag}_clearfell_step_se',
               zr['clearfell_step_se'], well=z, era='Post_felling')
        rn.add(f'FourZone_{tag}_scraping_step',
               zr['scraping_step'], well=z, era='Post_scraping',
               note=f"vs {REFERENCE_ZONE}; p={zr['scraping_p']:.4f}")

    rn.add('FourZone_R2', fit['R2'], unit='', well='all_zones',
           note='Joint model R²')
    rn.add('FourZone_N', fit['N'], unit='well-months', well='all_zones',
           note='Pooled-panel sample size')

    # Pairwise contrasts (skip the identity-demonstration row).
    # Primary contrasts carry SE/p normally; derived contrasts are
    # tagged in the note so their covariance-deflated p is not mistaken
    # for a primary result (see write_pairwise_csv).
    for c in contrasts:
        if c['contrast_type'] == 'identity_check':
            continue
        key = ('FourZone_contrast_'
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
        rn.add(key, c['step_m'], well=c['contrast'], era='Post_felling',
               note=note)

    rn.save(path)


# ============================================================================
# 10j CROSS-CHECK
# ============================================================================

def crosscheck_against_10j(contrasts, tol=0.005):
    """Assert the four-zone Impact−Edge contrast reproduces Script 10j.

    Both 10j and 10k use the same estimator (OLS, well-FE, cluster-robust
    SE, zone-interacted CWB and binary Scraped1) on overlapping data, so
    the four-zone Impact−Edge contrast should reproduce 10j's monthly
    Impact-vs-Edge step.  A mismatch beyond `tol` is a bug.

    The two are not guaranteed byte-identical: 10k's Impact−Edge contrast
    is conditioned on the full four-zone panel (Forest and C3/Warren wells
    also inform the shared CWB and easting coefficients), whereas 10j
    fits Impact+Edge alone.  A small difference is expected; a large one
    is not.  This function prints the comparison and returns the delta;
    it does not hard-fail (the difference is reported, for the changelog).

    Parameters
    ----------
    contrasts : list of contrast dicts from compute_pairwise_contrasts().
    tol : float
        Advisory tolerance in metres.  Differences above this print a
        prominent warning.

    Returns
    -------
    dict with the 10k value, the 10j value (or None), and their delta.
    """
    ie = next((c for c in contrasts
               if c['contrast'] == 'Impact - Edge'), None)
    if ie is None:
        note("Impact - Edge contrast not found — skipped")
        return {'ok': False}

    k_val = ie['step_m']

    if not OUT_10J_MONTHLY_RESULTS.exists():
        print(f"   [crosscheck] 10j output not found at "
              f"{OUT_10J_MONTHLY_RESULTS.name} — run 10j first for the "
              f"cross-check.  10k Impact-Edge = {k_val*1000:+.1f} mm")
        return {'ok': False, 'tenk': k_val, 'tenj': None, 'delta': None}

    j_df = pd.read_csv(OUT_10J_MONTHLY_RESULTS)
    j_val = float(j_df['clearfell_step_m'].iloc[0])
    delta = k_val - j_val

    note("Impact - Edge differential felling step:")
    print(f"      10k four-zone contrast : {k_val*1000:+8.1f} mm")
    print(f"      10j two-zone estimator : {j_val*1000:+8.1f} mm")
    print(f"      delta (10k - 10j)      : {delta*1000:+8.1f} mm  "
          f"(advisory tol = {tol*1000:.1f} mm)")
    if abs(delta) > tol:
        print("      [NOTE] delta exceeds advisory tolerance — expected to "
              "be small (the\n"
              "             four-zone panel conditions the shared CWB / "
              "easting terms on\n"
              "             Forest + C3/Warren wells too).  Record the "
              "observed delta in\n"
              "             the changelog; investigate if it is large.")
    else:
        info("within advisory tolerance.")
    return {'ok': True, 'tenk': k_val, 'tenj': j_val, 'delta': delta}


# ============================================================================
# FIGURES
# ============================================================================

def _save_jpeg(fig, out_path):
    """Save a figure, enforcing the pipeline JPEG-quality-85 convention.

    All pipeline figures are saved as JPEG at quality 85 (matching
    Scripts 09b, 09d, 21, 25).  matplotlib routes JPEG quality through
    ``pil_kwargs``; the bare ``quality=`` kwarg is silently ignored, so
    it must be passed this way.
    """
    is_jpeg = str(out_path).lower().endswith('.jpg')
    fig.savefig(
        out_path, dpi=150,
        format='jpeg' if is_jpeg else None,
        pil_kwargs={'quality': 85} if is_jpeg else None,
        bbox_inches='tight',
    )
    plt.close(fig)


def figure_zone_centroids(panel, fit, out_path):
    """Four zone-centroid hydrographs on one panel."""
    fig, ax = plt.subplots(figsize=(12, 5.5))

    for z in ZONE_WELLS:
        centroid = (panel.loc[panel['zone'] == z]
                         .groupby('date')['h'].mean())
        lw = 2.2 if z in ('Impact', 'Forest') else 1.6
        ax.plot(centroid.index, centroid.values,
                color=ZONE_COLOURS[z], lw=lw,
                label=f'{z}' + (' (ref)' if z == REFERENCE_ZONE else ''))

    ax.axvline(SCRAPING_DATE,     color='grey', ls='--', alpha=0.7,
               label='Apr 2015 scraping')
    ax.axvline(INTERVENTION_DATE, color='k',    ls='--', alpha=0.8,
               label='Dec 2017 felling')
    ax.set_ylabel('Water-table depth (m)')
    ax.set_xlabel('Date')
    ax.set_title('Four-zone centroids — monthly mean water-table depth')
    ax.legend(loc='lower right', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    imp = fit['zone_results']['Impact']
    fig.suptitle(
        f"Four-zone pooled-panel BACI — Impact vs Forest felling step "
        f"= {imp['clearfell_step']*1000:+.1f} mm "
        f"(95% CI [{imp['clearfell_ci_lo']*1000:+.1f}, "
        f"{imp['clearfell_ci_hi']*1000:+.1f}], p = {imp['clearfell_p']:.4f})",
        fontsize=10)
    plt.tight_layout(rect=(0, 0, 1, 0.96))
    _save_jpeg(fig, out_path)


def figure_contrast_forest(panel, out_path):
    """Three differential series: each non-reference zone minus Forest."""
    forest = (panel.loc[panel['zone'] == 'Forest']
                   .groupby('date')['h'].mean())

    fig, ax = plt.subplots(figsize=(12, 5))
    for z in NON_REF_ZONES:
        zc = (panel.loc[panel['zone'] == z]
                   .groupby('date')['h'].mean())
        diff = (zc - forest).dropna()
        ax.plot(diff.index, diff.values * 1000,
                color=ZONE_COLOURS[z], lw=1.4, label=f'{z} − Forest')

    ax.axhline(0, color='grey', ls='-', alpha=0.5)
    ax.axvline(SCRAPING_DATE,     color='grey', ls='--', alpha=0.7)
    ax.axvline(INTERVENTION_DATE, color='k',    ls='--', alpha=0.8)
    ax.set_ylabel('Zone − Forest centroid (mm)')
    ax.set_xlabel('Date')
    ax.set_title('Differential series — each zone relative to the '
                 'Forest control reference')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    plt.tight_layout()
    _save_jpeg(fig, out_path)


def figure_forest_plot(contrasts, out_path):
    """Forest-plot of the pairwise felling contrasts, primary vs derived.

    The plot is split into two labelled groups so the six rows are not
    read as co-equal results:

      PRIMARY — the three zone-vs-Forest contrasts, drawn dark.  Direct
        model coefficients; SE/CI interpreted normally.
      DERIVED — the three zone-vs-zone contrasts, drawn greyed.  Exact
        linear combinations; their CIs are covariance-dependent and not
        comparable to the primary rows, so they are visually demoted
        and annotated without a p-value.

    A caption states the interpretation rule explicitly.
    """
    primary = [c for c in contrasts if c['contrast_type'] == 'primary']
    derived = [c for c in contrasts if c['contrast_type'] == 'derived']

    # Primary group on top, derived group below, with a gap row between.
    GAP = 1
    n = len(primary) + len(derived) + GAP
    # y positions, top-to-bottom: primary first, gap, then derived.
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
                # Derived: annotate WITHOUT a p-value — its p is
                # covariance-deflated and not comparable.
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
    # Grey the derived tick labels.
    for tick, yi in zip(ax.get_yticklabels(), all_y):
        if yi in y_derived:
            tick.set_color('#9aa4b2')

    # Group divider and labels.
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
    ax.set_xlabel('Differential felling step (mm)')
    ax.set_title('Four-zone BACI — pairwise felling contrasts',
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
    banner("10k", "Four-Zone Pooled-Panel BACI", version="1.2.0")
    print("=" * 72)
    print("Script 10k — Four-zone pooled-panel clearfell BACI")
    print("=" * 72)

    make_all_dirs()

    print("\n  Loading data ...")
    wells, _prov, climate, master, well_locations, _valid = \
        load_clearfell_data()

    print(f"  Zones (reference = {REFERENCE_ZONE} control):")
    for z, wl in ZONE_WELLS.items():
        present = [w for w in wl if w in wells.columns]
        ref = ' [reference]' if z == REFERENCE_ZONE else ''
        print(f"    {z:<11}: {', '.join(w.upper() for w in present)}{ref}")
    print(f"  PRE_FELL_START_FOURZONE:  {PRE_FELL_START_FOURZONE.date()}")
    print(f"  SCRAPING_DATE:   {SCRAPING_DATE.date()}")
    print(f"  INTERVENTION:    {INTERVENTION_DATE.date()}")
    print()

    # ── 1. Build panel ──────────────────────────────────────────────────
    print("  1. Building four-zone monthly panel ...")
    panel = build_monthly_panel(wells, climate)
    panel = attach_easting(panel, well_locations, master=master)
    print(f"     n_rows = {len(panel)}, n_wells = {panel['well'].nunique()}, "
          f"n_months = {panel['date'].nunique()}")
    by_zone = panel.groupby('zone')['well'].nunique()
    print("     wells per zone: "
          + ", ".join(f"{z} {by_zone.get(z, 0)}" for z in ZONE_WELLS))
    print()

    # ── 2. Fit the joint model (with easting) ───────────────────────────
    print("  2. Fitting four-zone joint model (with easting × time) ...")
    fit = fit_four_zone(panel, include_easting=True)
    for z in NON_REF_ZONES:
        zr = fit['zone_results'][z]
        print(f"     {z:<11} vs Forest: "
              f"{zr['clearfell_step']*1000:+8.1f} mm  "
              f"95% CI [{zr['clearfell_ci_lo']*1000:+7.1f}, "
              f"{zr['clearfell_ci_hi']*1000:+7.1f}]  "
              f"p={zr['clearfell_p']:.4f}")
    print(f"     N = {fit['N']} well-months, R² = {fit['R2']:.3f}")
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
                  f"{c['step_m']*1000:+8.1f} mm   "
                  f"[{c['identity_check']}]")
        elif ct == 'primary':
            print(f"     {c['contrast']:<34} "
                  f"{c['step_m']*1000:+8.1f} mm  p={c['p']:.4f}  [primary]")
        else:  # derived
            print(f"     {c['contrast']:<34} "
                  f"{c['step_m']*1000:+8.1f} mm  "
                  f"(derived — p not comparable)")
    print()

    # ── 4. 10j cross-check ──────────────────────────────────────────────
    print("  4. Cross-check against Script 10j ...")
    crosscheck_against_10j(contrasts)
    print()

    # ── 5. Easting sensitivity (robustness — NOT erosion decomposition) ─
    print("  5. Easting sensitivity (re-fit with easting × time dropped) ...")
    fit_noeast = fit_four_zone(panel, include_easting=False)
    for z in NON_REF_ZONES:
        zw = fit['zone_results'][z]['clearfell_step'] * 1000
        zn = fit_noeast['zone_results'][z]['clearfell_step'] * 1000
        print(f"     {z:<11} with easting {zw:+8.1f} mm  |  "
              f"without {zn:+8.1f} mm")
    print("     [note] robustness diagnostic only — the with/without "
          "difference is NOT\n"
          "            the coastal effect (see Script 25 for coastal "
          "retreat).")
    print()

    # ── 6. Write outputs ────────────────────────────────────────────────
    print("  6. Writing outputs ...")
    write_zone_results_csv(fit, OUT_10K_ZONE_RESULTS)
    saved(f"{OUT_10K_ZONE_RESULTS.name}")
    write_pairwise_csv(contrasts, OUT_10K_PAIRWISE)
    saved(f"{OUT_10K_PAIRWISE.name}")
    write_easting_sensitivity_csv(fit, fit_noeast, OUT_10K_EASTING_SENS)
    saved(f"{OUT_10K_EASTING_SENS.name}")
    write_report_numbers(fit, contrasts, OUT_10K_REPORT)
    saved(f"{OUT_10K_REPORT.name}")

    # ── 7. Figures ──────────────────────────────────────────────────────
    print("  7. Building figures ...")
    figure_zone_centroids(panel, fit, OUT_10K_CENTROIDS_FIG)
    saved(f"{OUT_10K_CENTROIDS_FIG.name}")
    figure_contrast_forest(panel, OUT_10K_CONTRAST_FIG)
    saved(f"{OUT_10K_CONTRAST_FIG.name}")
    figure_forest_plot(contrasts, OUT_10K_FOREST_PLOT)
    saved(f"{OUT_10K_FOREST_PLOT.name}")

    # ── 8. Site-observations registry ───────────────────────────────────
    print("  8. Updating site-observations registry ...")
    update_site_observation(
        'four_zone_clearfell_step_impact',
        fit['zone_results']['Impact']['clearfell_step'],
        producer_script='10k')
    update_site_observation(
        'four_zone_clearfell_step_edge',
        fit['zone_results']['Edge']['clearfell_step'],
        producer_script='10k')
    update_site_observation(
        'four_zone_clearfell_step_c3warren',
        fit['zone_results']['C3/Warren']['clearfell_step'],
        producer_script='10k')
    saved("3 entries updated in pipeline_site_observations.csv")
    print()
    print("Script 10k complete.")


if __name__ == '__main__':
    main()
