"""
utils/clearfell_common.py
=========================
Shared module for the Script 10 clearfell analysis suite (10a–10h).

Provides:
  - Well tier definitions (impact, edge, forest control, coastal control,
    climate control, far-field control)
  - Intervention dates
  - Record-length-balance BACI cutoffs (PRE_FELL_START family)
  - Spatial constants and distance functions
  - Data loading (wells, climate, master coefficients)
  - BACI displacement and covariate computation
  - Summer minimum extraction

All sub-scripts import from here to ensure consistent well lists,
dates, and data handling.  No analysis is performed — this module
only prepares data.

Record-length-balance principle
-------------------------------
Pooled cross-well BACI inference must not mix wells with substantially
different record-start dates: when a comparison aggregates target and
control centroids over a period when only a subset of wells are reading,
the resulting BACI displacement is a different statistical quantity from
the same comparison aggregated over a period when all wells are reading.
The unbalanced contrast introduces spurious step-change signal at the
boundary where late-starting wells come online.

Two record-length-balanced cutoffs are codified here:

* ``PRE_FELL_START = 2010-07-01`` — all 17 clearfell-suite wells aligned.
  This is the date from which every network well has continuous record
  once CEH34's missing 2010-07 month is supplied by Script 10i's
  CEH9-donor hindcast.  Pre-fell window is 90 months (2010-07 to
  2017-11); post-fell window is 99 months.
* ``PRE_FELL_START_LONG = 2009-06-01`` + ``LONG_RECORD_NETWORK_WELLS``
  (12-well subset) — for analyses that genuinely require a longer
  pre-fell baseline.  Excludes the five 2010-starting CEH3x wells
  (CEH30, CEH31, CEH32, CEH33, CEH34).  Pre-fell window ≈ 103 months.

The two cutoffs encode the same principle in two forms: "all wells,
shorter baseline" vs "long-record subset, longer baseline".  Pooled
BACI scripts must pick one or the other — never a third hybrid.

Per-well analyses (forward-residual diagnostics, individual hydrographs,
visualisation panels) are not subject to these cutoffs — they pose no
mixing concern because the unit of inference is the individual well, not
a pooled centroid.

Usage
-----
    from utils.clearfell_common import (
        load_clearfell_data, CLEARFELL_DATE, SCRAPING_DATE,
        PRE_FELL_START, PRE_FELL_START_LONG, LONG_RECORD_NETWORK_WELLS,
        IMPACT_WELLS, EDGE_WELLS, FOREST_CONTROL_WELLS,
        CLIMATE_CONTROL_WELLS, ALL_NETWORK_WELLS,
        compute_baci_displacement, compute_cwb,
        distance_weighted_scraping, annual_summer_minimum,
    )

Note
----
Since v1.3.0 (Defect E fix), ``load_clearfell_data`` returns a 6-tuple:
``wells, wells_provenance, climate, master, well_locations, valid_tiers``.
The new ``wells_provenance`` element is aligned to ``wells`` and holds
per-cell flags from {"measured", "interpolated", "missing"}. Most
clearfell-suite scripts only need ``wells`` and can ignore the
provenance with ``_ = wells_prov``. Script 10d uses it to require
>=2 measured Jun-Sep months in ``annual_summer_minimum``.
"""

__version__ = "1.13.1"  # Hollingham (2026) - 2026-09-02. drift_term() and
#   coastal_differential_mm_yr(), for D-111's BACI_DRIFT_DESIGN. The accessor
#   exists so that no downstream site names a drift design: five guards in 10a
#   tested the literal 'easting_x_time' and each one guarded a CORRECTION, so a
#   second design under a second name would have skipped them silently. It
#   RAISES on absence where the caller says a term is required, because a
#   missing drift column is a build fault and not a case to skip.
#
#   The differential is read from the committed 25_14 rather than recomputed;
#   Combined has no tier row of its own and is the well-count-weighted mean of
#   Forest, Coastal and Climate. All four reproduce M14_RESULT §3 exactly:
#   Forest -10.70, Climate -0.94, Combined -3.74, FarField -13.13.
#
#   1.13.1 (same day): the differential is per ZONE x control, not per control.
#   1.13.0 keyed it on the control alone and returned the Impact differential
#   for every zone, so the Edge contrasts were scaled by the wrong quantity and
#   s_coast came out low by exactly Impact-Forest / Edge-Forest = 1.127. Stored
#   defaults are now the six TIER TRENDS rather than eight differentials: every
#   zone x control combination derives from them, six numbers instead of eight,
#   and a new zone adds none.
#
# v1.12.0  # Hollingham (2026) - 2026-08-31. SUMMER_MONTHS now imported from config.SUMMER_MINIMUM_MONTHS, joining SPRING_MONTHS which was already re-exported from config.
#   Batch two of the seasonal-windows migration (D-100): the window's
#   MONTHS ARE UNCHANGED and the constant is asserted equal to the literal it
#   replaced, in value and in type, read mechanically out of git HEAD. No
#   committed value moves.
#
# v1.11.0  # Hollingham (2026) — 2026-08-29. the legacy alias is removed; CLEARFELL_DATE is the only name (T-17).
#   No value changes; verified by re-run against the 2026-08-29 pipeline outputs.
# v1.10.0  # Hollingham (2026) — 2026-08-29. The four intervention
#   dates are built from utils.config rather than declared here (D-084); adds
#   CLEARFELL_DATE as the unambiguous alias for CLEARFELL_DATE. No value changes.
# v1.9.0  # Hollingham (2026) — 2026-08-21 (far-field control tier)
#
# 1.9.0 — FAR_FIELD_CONTROL_WELLS added beside the three existing control tiers:
#         a control set chosen for DISTANCE CONTRAST against the impact zone, so
#         the BACI easting × time covariate can be tested against the coastal-
#         gradient model on a contrast large enough to carry the test. NW4 is
#         deliberately excluded — see the comment at the definition.
#         (a) CORE_NETWORK_WELLS and CORE_TIERS name the published five-tier
#             design explicitly. ALL_NETWORK_WELLS and TIERS are the same five
#             with the far-field tier APPENDED, so existing membership, order
#             and every table or figure built by iterating them are unchanged.
#             Consumers that must stay at five tiers now say so by name rather
#             than by omission — Script 10f's synthetic-control donor pool
#             (which defines donors as wells outside the design, and would
#             otherwise have silently lost two donors to the new tier) and
#             Script 21's BACI-zone violin.
#         (b) TIER_COLOURS gains the far-field entry; the label constants
#             FAR_FIELD_TIER_LABEL / FAR_FIELD_CONTROL_LABEL are shared with
#             Scripts 10a and 25 so the two naming schemes cannot drift.
#         (c) New derivation helpers — well_distances_to_coast(),
#             tier_distance_stats(), far_field_admission_threshold_m() and
#             far_field_tier_audit() — so the tier's geometry and its
#             admission criterion are computed from the committed metadata and
#             the fitted reach at run time instead of being asserted anywhere.
#             The threshold is config.FAR_FIELD_REACH_MULTIPLE × the fitted
#             reach L, read live from 25_01 with the documented first-pass
#             fallback.
#         (d) print_network_summary() takes its tier count from the mapping it
#             is handed instead of a typed "5-tier".
#         No change to any existing tier's membership, to the centroid or BACI
#         machinery, or to any committed value.
#
# 1.8.0 — Seasonal metric extraction generalised so the spring mean (MAM) can be
#         computed on exactly the same footing as the summer minimum, for the
#         spring BACI analyses in Scripts 09c/10d/10l.
#         (a) annual_seasonal_metric() is the new general extractor; the
#             provenance-aware measured-only logic and the min_measured guard are
#             unchanged. annual_summer_minimum() becomes a thin wrapper over it
#             (behaviour byte-identical); annual_spring_mean() is the new sibling.
#         (b) control_centroid_seasonal() generalises the centroid pooling;
#             forest_control_centroid_summer_min() becomes a thin wrapper and
#             forest_control_centroid_spring_mean() is the new sibling.
#         (c) well_year_usable_season() / usable_panel_years() generalise the
#             four-zone panel gatekeeper; the summer entry points are thin
#             wrappers and wmc3_usable_spring_years() is the new sibling.
#         (d) Spring months and the spring completeness rule come from
#             config.MSL_SPRING_MONTHS / config.MSL_MIN_MONTHS_PER_SPRING — no
#             new local constants, one definition of "spring" across the pipeline.
#         No change to any summer code path or committed summer output.
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import warnings
import numpy as np
import pandas as pd

from utils.paths import (
    INT_WELLS_CLEAN, INT_WELLS_PROVENANCE, INT_WELLS_EXTENDED, INT_CLIMATE,
    INT_MASTER_DATA, DATA_WELL_ELEVATIONS, DATA_DIST_COAST,
    OUT_10E_COEFF_SHIFTS, OUT_10I_HINDCAST, OUT_25_FIT_PARAMETERS,
    OUT_25_CORRECTION_DIAGNOSTIC,
)
from utils.data_utils import PROV_MEASURED, PROV_MISSING
from utils.config import (
    SUMMER_MINIMUM_MONTHS,
    CEH36_E as _CEH36_E, CEH36_N as _CEH36_N,
    MSL_SPRING_MONTHS as _MSL_SPRING_MONTHS,
    MSL_MIN_MONTHS_PER_SPRING as _MSL_MIN_MONTHS_PER_SPRING,
    FAR_FIELD_REACH_MULTIPLE,
    CLEARFELL_DATE_ISO as _CLEARFELL_DATE_ISO,
    SCRAPING_DATE_0_ISO as _SCRAPING_DATE_0_ISO,
    SCRAPING_DATE_ISO as _SCRAPING_DATE_ISO,
    SCRAPING_DATE_2_ISO as _SCRAPING_DATE_2_ISO,
)

# ============================================================================
# WELL TIER DEFINITIONS
# ============================================================================

IMPACT_WELLS = ['wmc3']

EDGE_WELLS = ['ceh31', 'ceh20', 'ceh30', 'ceh16']

FOREST_CONTROL_WELLS = [
    'ceh32', 'ceh34', 'ceh33', 'nw10', 'ceh2',  # C4 interior (Main Forest)
]

COASTAL_CONTROL_WELLS = [
    'ceh19', 'ceh17',  # C5 (Coastal Forest — lower β₂, distinct from C4)
]

CLIMATE_CONTROL_WELLS = [
    'ceh9', 'nw7', 'nw6', 'nw5', 'wmc2',  # C3 wells, all ≥8 yr pre-felling
]
# Excluded: CEH42 (3.4 yr pre-felling baseline)

# ----------------------------------------------------------------------------
# FAR-FIELD CONTROL TIER  (Scripts 10a and 25)
# ----------------------------------------------------------------------------
# A control tier selected for DISTANCE CONTRAST against the impact zone, so
# that the BACI easting × time covariate can be tested against the coastal-
# gradient model on a contrast large enough to carry the test.
#
# Why it exists.  The Forest and Climate tiers are each sited to match their
# impact zone's setting, which necessarily matches its distance from the
# shore.  A control that sits at the impact zone's own distance gives the
# gradient model almost no differential to predict, so whatever the easting ×
# time term absorbs there is not being compared against the gradient — the
# comparison cannot discriminate.  A tier selected on distance is the only one
# of the three that puts the gradient model at risk.
#
# Admission criteria, applied in this order.  Every member satisfies all five,
# and the screen is re-derivable from the committed metadata and the fitted
# reach — no distance is restated as a literal here or in config.py:
#
#   1. Distance to the coast beyond config.FAR_FIELD_REACH_MULTIPLE times the
#      FITTED reach L (Script 25, forest-free linear-capped panel).  See
#      far_field_admission_threshold_m() below, and the config docstring for
#      why the criterion is a multiple rather than a distance.
#   2. Open ground — Script 01's `in_forest` land-cover flag false.  A
#      forested control would confound canopy with distance, which is the
#      confound the forest-free panel exists to avoid.
#   3. The same pre-felling baseline requirement already applied to
#      CLIMATE_CONTROL_WELLS, on which CEH42 was excluded.
#   4. A post-felling record.  This is NOT redundant with (3): CEH7's record
#      ends at the intervention and CEH8's post-felling record is a small
#      fraction of the others', so both would have entered a tier built on
#      distance and baseline alone, and CEH7 would have contributed nothing to
#      a before-and-after comparison while still appearing in the well count.
#   5. Not already assigned to another tier, and not scrape-affected.
#
# NW4 IS DELIBERATELY EXCLUDED even though it satisfies every criterion above.
# It is the inland anchor of the Script 38 shore-normal transect, which the
# report cites as INDEPENDENT corroboration of the same coastal gradient.  A
# well used in both places would make the two corroborations share a member
# and stop them being independent, which is the whole value of quoting them
# side by side.  Excluding it costs one well and slightly RAISES the tier's
# mean distance.  This is a deliberate omission — do not "fix" it by adding
# NW4 back.
#
# The tier spans a wide band of distances by construction, and its members may
# not respond alike.  Consumers must therefore report the PER-WELL SPREAD
# beside the tier estimate rather than the tier mean alone: Script 10a emits
# the single-control-well BACI refits and Script 25 carries them through to
# the corroboration spread table.
FAR_FIELD_CONTROL_WELLS = [
    'nw4b', 'wmc1', 'ceh5', 'l7', 'ceh6',
]

# Two labels, because the suite already carries two naming schemes and the new
# tier has to answer to both: TIERS / TIER_COLOURS use the "<name> Ctrl" form
# ('Forest Ctrl'), while the Script 10a CONTROLS dict and the `Control` column
# it writes use the bare form ('Forest').  Script 25 matches its corroboration
# rows on the value 10a wrote, so both scripts take the label from here rather
# than typing it twice and drifting.
FAR_FIELD_TIER_LABEL    = 'Far-field Ctrl'   # TIERS / TIER_COLOURS key
FAR_FIELD_CONTROL_LABEL = 'FarField'         # 10a CONTROLS key / 25 control_tier

# ── BACI drift term: the accessor and the coastal donor (D-111, M14) ─────────
#
# WHY AN ACCESSOR AND NOT A NAME. The drift covariate was called
# `easting_x_time` and that literal string was tested in five places in 10a of
# the form `if 'easting_x_time' in fit['col_names']`, each guarding a CORRECTION.
# Introducing a second design under a second column name would have left every
# one of those guards False, and a guard that is False here does not raise — it
# skips the correction and returns a "corrected" series that was never
# corrected. Silent, plausible, and wrong. So downstream code asks for THE DRIFT
# TERM and never names a design.
DRIFT_COLUMNS = ('easting_x_time', 'coastal_x_time')


def drift_term(col_names, required=True):
    """The drift column present in `col_names`, or None.

    `col_names` may be a fit's col_names list or a DataFrame's columns.

    Raises when `required` and none is present: under a design that declares a
    drift term, its absence is a build fault, not a case to skip. That is the
    whole reason this function exists — see the note above.
    """
    names = list(getattr(col_names, 'columns', col_names))
    found = [c for c in DRIFT_COLUMNS if c in names]
    if len(found) > 1:
        raise ValueError(f"two drift columns present at once: {found}. "
                         "The design chooses one; carrying both makes the "
                         "coefficient table ambiguous about which drift the "
                         "step is net of.")
    if not found:
        if required:
            raise KeyError(
                "no drift column in " + repr(names) + ". Expected one of "
                + repr(list(DRIFT_COLUMNS)) + ".")
        return None
    return found[0]


# Which 25_14 tiers make up each of 10a's CONTROLS keys. 'Combined' has no tier
# row of its own in 25_14 — it is Forest + Coastal + Climate — so its
# differential is the well-count-weighted mean of the three. Verified against
# M14_RESULT_2026-08-28 §3: Forest -10.70, Climate -0.94, Combined -3.74,
# FarField -13.13, all four reproduced from the committed CSV.
CONTROL_TIER_COMPOSITION = {
    'Forest':                ('Forest',),
    'Climate':               ('Climate',),
    'Combined':              ('Forest', 'Coastal', 'Climate'),
    FAR_FIELD_CONTROL_LABEL: ('FarField',),
}


def coastal_differential_mm_yr(control_label, zone_label='Impact',
                               donor_fit=None, quiet=False):
    """ZONE-minus-control coastal trend differential, mm/yr, from 25_14.

    THE ZONE IS NOT OPTIONAL. The first version of this took the control label
    alone and returned the Impact differential for every zone, so the Edge
    contrasts were scaled by the wrong quantity and s_coast came out low by
    exactly Impact-Forest / Edge-Forest = 1.127. It was visible only because the
    older coastal_drift_differential() still printed the right Delta-delta
    beside the wrong s_coast; had both come from here they would have agreed
    with each other and been wrong together.

    Read live from the committed `25_14_correction_diagnostic.csv` rather than
    recomputed: the decay function and its fitted parameters belong to Script
    25, and evaluating them a second time here is how two "coastal gradients"
    start to disagree.

    SECOND-PASS READ. Script 25 runs AFTER Script 10, so on a first pass this
    file may not exist. Falls back to the documented default with a console
    warning, which is the 09b/09d/09f pattern.
    """
    from utils.config import BACI_COASTAL_DONOR_FIT
    from utils.pipeline_params import default_value

    donor_fit = donor_fit or BACI_COASTAL_DONOR_FIT
    tiers = CONTROL_TIER_COMPOSITION.get(control_label)
    if tiers is None:
        raise KeyError(
            f"no 25_14 tier composition for control set {control_label!r}. "
            f"Known: {sorted(CONTROL_TIER_COMPOSITION)}. Add a row rather than "
            f"defaulting — a missing composition silently means zero drift.")

    # The six TIER TRENDS are the stored quantity, not the eight differentials:
    # every zone x control combination derives from them, so there are six
    # numbers to keep true rather than eight, and adding a zone adds none.
    if OUT_25_CORRECTION_DIAGNOSTIC.exists():
        d = pd.read_csv(OUT_25_CORRECTION_DIAGNOSTIC)
        d = d[d['fit_label'] == donor_fit].set_index('tier')
        if d.empty:
            raise ValueError(
                f"donor fit {donor_fit!r} is not in "
                f"{OUT_25_CORRECTION_DIAGNOSTIC.name}; present: "
                f"{sorted(pd.read_csv(OUT_25_CORRECTION_DIAGNOSTIC).fit_label.unique())}")
        trend = {t: float(d.loc[t, 'predicted_trend_mm_yr']) for t in d.index}
    else:
        trend = {t: float(default_value(f"baci_coastal_trend_{t.lower()}_mm_yr"))
                 for t in ('Impact', 'Edge', 'Forest', 'Coastal', 'Climate',
                           'FarField')}
        if not quiet:
            warnings.warn(
                f"{OUT_25_CORRECTION_DIAGNOSTIC.name} not found — using the "
                f"documented first-pass tier trends for "
                f"{zone_label} x {control_label}", RuntimeWarning)

    if zone_label not in trend:
        raise KeyError(f"no 25_14 tier for zone {zone_label!r}; "
                       f"present: {sorted(trend)}")

    # Weighted by the DESIGN's own well counts, from the tier lists above, so
    # the weighting does not depend on a column of the donor CSV.
    counts = {'Forest': len(FOREST_CONTROL_WELLS),
              'Coastal': len(COASTAL_CONTROL_WELLS),
              'Climate': len(CLIMATE_CONTROL_WELLS),
              'Edge': len(EDGE_WELLS),
              'Impact': len(IMPACT_WELLS),
              'FarField': len(FAR_FIELD_CONTROL_WELLS)}
    n = sum(counts[t] for t in tiers)
    mean_ctrl = sum(trend[t] * counts[t] for t in tiers) / n
    return trend[zone_label] - mean_ctrl


# The five-tier clearfell design — the network whose BACI results are
# published.  Named separately from ALL_NETWORK_WELLS so that consumers which
# must NOT see the far-field diagnostic tier can say so explicitly rather than
# by omission: the Script 10f synthetic-control donor pool (which defines
# donors as wells OUTSIDE the design, and would otherwise silently lose two
# donors to the new tier) and the Script 21 BACI-zone violin are both keyed on
# this constant.
CORE_NETWORK_WELLS = (
    IMPACT_WELLS + EDGE_WELLS +
    FOREST_CONTROL_WELLS + COASTAL_CONTROL_WELLS +
    CLIMATE_CONTROL_WELLS
)

# Every well the clearfell suite loads locations for.  The far-field tier is
# APPENDED, so the membership and the order of the five published tiers are
# unchanged and per-well loops over this list gain rows without moving any.
ALL_NETWORK_WELLS = CORE_NETWORK_WELLS + FAR_FIELD_CONTROL_WELLS

# ----------------------------------------------------------------------------
# C3 / WARREN ZONE — for the Script 10k four-zone pooled-panel BACI
# ----------------------------------------------------------------------------
# The western-dune ("Western Residual") control zone for the four-zone
# joint model.  This is a DELIBERATELY CARVED zone, not the raw k=5
# cluster-3 partition: cluster 3 (21 wells in 03_master_data.csv)
# contains the Impact well (WMC3), all five Climate-control wells, and
# the scraping site CEH36 itself, so the raw cluster cannot serve as a
# zone.  The carving applied three filters (see the four-zone BACI
# design spec §4.3 and its decision record):
#
#   1. Remove wells already assigned to another clearfell tier
#      (WMC3; the Climate-control wells) and the project-excluded
#      CEH39 (<24 mo pre-scraping baseline).
#   2. Remove the scraping footprint — CEH36 itself plus CEH4 and
#      CEH18, which sit inside its decay neighbourhood (and within
#      500 m of the felled compartment).
#   3. Record-length balance — keep only wells whose record reaches
#      back to PRE_FELL_START (2010-07-01), so the zone is balanced
#      against the Impact/Edge/Forest zones.  This drops NW13 and
#      WMC4 (both start 2012-02, ~19 months after the baseline).
#
# A 500 m shielding rule (wells > 500 m from WMC3, the in-situ Impact
# well) was also specified; it removes no further wells — the three
# scraping-footprint wells were already inside 500 m and the four
# retained wells are all beyond it (CEH1 at 541 m is the marginal
# member).  The 500 m rule is the basis for treating C3/Warren as a
# SECOND CONTROL zone: with no C3 wells in the south-westward
# forest-perturbation propagation sector, the western dune is expected
# to be shielded from the felling signal, so the four-zone model's
# C3/Warren differential felling step is expected to be ~0.  A clearly
# non-zero value is a flag, not a felling finding.
#
# Not added to ALL_NETWORK_WELLS: that constant defines the five-tier
# clearfell network used by the 10a/10d/10e/etc. suite; the C3/Warren
# zone is specific to Script 10k.
C3_WARREN_WELLS = ['ceh1', 'nw1', 'nw2', 'nw11']

# Convenience grouping for iteration.
#
# CORE_TIERS is the published five-tier design.  TIERS adds the far-field
# control tier and is what the per-well loops and tier-label lookups iterate;
# the far-field entry is appended LAST, so iteration order over the five
# published tiers — and therefore every figure and table built by iterating
# them — is unchanged.  A consumer that must stay at five tiers reads
# CORE_TIERS (Script 21's BACI-zone violin does).
CORE_TIERS = {
    'Impact':        IMPACT_WELLS,
    'Edge':          EDGE_WELLS,
    'Forest Ctrl':   FOREST_CONTROL_WELLS,
    'Coastal Ctrl':  COASTAL_CONTROL_WELLS,
    'Climate Ctrl':  CLIMATE_CONTROL_WELLS,
}

TIERS = {
    **CORE_TIERS,
    FAR_FIELD_TIER_LABEL: FAR_FIELD_CONTROL_WELLS,
}

# ============================================================================
# INTERVENTION DATES
# ============================================================================

# Built from utils.config, which holds the ISO strings as the single source of
# truth (D-084). These four were literals here until 2026-08-29, duplicated in
# scraping_common and again in 09b. Values unchanged.
CLEARFELL_DATE    = pd.Timestamp(_CLEARFELL_DATE_ISO)    # December 2017 clearfell
SCRAPING_DATE_0   = pd.Timestamp(_SCRAPING_DATE_0_ISO)   # February 2013 (CEH40/41/42 unmonitored cuts)
SCRAPING_DATE     = pd.Timestamp(_SCRAPING_DATE_ISO)     # April 2015 scraping
SCRAPING_DATE_2   = pd.Timestamp(_SCRAPING_DATE_2_ISO)   # October 2023 re-scraping

FELLING_YEAR = CLEARFELL_DATE.year  # 2017

# ============================================================================
# RECORD-LENGTH-BALANCE BACI CUTOFFS
# ============================================================================
# See module docstring for rationale.  These constants must be used by any
# script performing pooled cross-well BACI inference (e.g. ANCOVA pooling
# Impact and Control centroids).  Per-well analyses are not subject to them.

# Full network, balanced pre-fell window.  This is the date from which
# every clearfell-suite well has continuous record once CEH34's missing
# 2010-07 month is supplied by Script 10i's CEH9-donor hindcast.
# CEH30/CEH31 (2010-06-01 starts) and CEH32/CEH33 (2010-07-01 starts) are
# observed; CEH34's 2010-07-01 value is the single hindcast point.
# Pre-fell window: 83 months (Jan 2011 to Nov 2017).  Default for the
# clearfell-suite BACI ANCOVA (Scripts 10a/10b/10e/10h).
#
# Migrated 2010-07-01 -> 2011-01-01 in clearfell_common v1.7.0, so the
# legacy 10-series shares the four-zone scripts' pre-felling start
# (PRE_FELL_START_FOURZONE).  2011-01 is the first full calendar year
# clear of the 2010 install ramp.  Note that for the centroid-based
# scripts (10a/10h) the start-date migration is a CONSISTENCY change,
# not the artefact fix: the install-ramp months were already outside
# the ANCOVA window after the CWB inner-join.  The artefact fix is the
# fixed-membership centroid in compute_control_centroid() — see the
# v1.7.0 changelog entry above and AUDIT_10series_PRE_FELL_START.md.
#
# PRE_FELL_START and PRE_FELL_START_FOURZONE are now numerically equal.
# They are kept as two named constants for now; collapsing them is a
# deliberate follow-up (it requires re-pointing the four-zone scripts).
#
# Consumers of CEH34 that include data prior to 2010-08-01 should call
# load_ceh34_hindcast_series() rather than using wells['ceh34'] directly,
# so the synthetic 2010-07-01 value is correctly substituted in.  (With
# the 2011-01 start the CEH34 hindcast no longer affects the in-window
# rows, but the call is harmless and the rosters/loaders still apply it.)
PRE_FELL_START = pd.Timestamp('2011-01-01')

# ----------------------------------------------------------------------------
# FOUR-ZONE BACI pre-felling start  (Scripts 10k; 10l reads it indirectly)
# ----------------------------------------------------------------------------
# The four-zone monthly BACI (Script 10k) starts its panel in January
# 2011, NOT at the legacy PRE_FELL_START (2010-07-01).
#
# Why distinct from PRE_FELL_START.  The monthly network reaches a
# stable 14/14-well count only from October 2010; the Jan-Sep 2010
# months are a genuine installation ramp in which several Forest-control
# wells (CEH32/33/34) do not yet exist.  A centroid or panel spanning
# those months is contaminated — this is the 2010-2012 artefact that the
# four-zone summer work documented.  2011-01 is the first full calendar
# year clear of the install ramp; it also matches the four-zone summer
# panel's 2011 start, so the monthly and summer four-zone frames are
# consistent.  (The late-2011 / 2012 gaps that remain — the NW10 outage,
# the dry 2012 — are scattered missing well-months, which the well-FE
# panel model tolerates; they are not an install ramp and do not
# warrant a later start.)
#
# This was historically a SEPARATE constant from PRE_FELL_START, added
# while the legacy shared cutoff still sat at 2010-07-01.  As of
# clearfell_common v1.7.0 the legacy PRE_FELL_START has been migrated to
# 2011-01-01, so the two constants are now numerically equal.  They are
# retained as two named constants for clarity of intent (four-zone vs
# legacy 10-series); collapsing them into one is left as a deliberate
# follow-up, since it requires re-pointing the four-zone scripts.
PRE_FELL_START_FOURZONE = pd.Timestamp('2011-01-01')

# Long-record subset, balanced pre-fell window.  For analyses that
# genuinely require a longer pre-fell baseline than 88 months.  Drops
# the five 2010-starting CEH3x wells; pre-fell window ≈ 103 months.
# Use together with LONG_RECORD_NETWORK_WELLS — never mix this cutoff
# with the full 17-well network.
PRE_FELL_START_LONG = pd.Timestamp('2009-06-01')

# The 12-well subset to use with PRE_FELL_START_LONG.  Derived as
# {w for w in ALL_NETWORK_WELLS if w.first_obs <= PRE_FELL_START_LONG}.
# Hardcoded here so the list is stable across pipeline runs and visible
# in code review — not regenerated from data.  Tier composition:
#   Impact:        1  (wmc3)
#   Edge:          2  (ceh20, ceh16)        — loses ceh30, ceh31
#   Forest Ctrl:   2  (nw10, ceh2)          — loses ceh32, ceh33, ceh34
#   Coastal Ctrl:  2  (ceh19, ceh17)        — full
#   Climate Ctrl:  5  (ceh9, nw7, nw6, nw5, wmc2) — full
LONG_RECORD_NETWORK_WELLS = [
    'wmc3',
    'ceh20', 'ceh16',
    'nw10', 'ceh2',
    'ceh19', 'ceh17',
    'ceh9', 'nw7', 'nw6', 'nw5', 'wmc2',
]

# ============================================================================
# SPATIAL CONSTANTS
# ============================================================================

# CEH36 scraping site
CEH36_EASTING  = _CEH36_E   # config.py — documented 2015 dune-scrape site
CEH36_NORTHING = _CEH36_N

# Felling compartment centroid (mean of FE1-4 + WMC3)
FELL_CENTROID_EASTING  = 241210.0
FELL_CENTROID_NORTHING = 363607.0

# Distance-weighted scraping decay length (metres)
SCRAPING_DECAY_LAMBDA = 300.0

# Summer months (1-indexed)
SUMMER_MONTHS = list(SUMMER_MINIMUM_MONTHS)

# Spring months (1-indexed) — re-exported from config so the clearfell/scraping
# suite shares ONE definition of "spring" with the van Willegen MSL machinery
# (Scripts 26/26b/34) and the coastal-gradient work.  Deliberately NOT a local
# literal, unlike SUMMER_MONTHS above (which predates the config convention and
# is duplicated in scraping_common).
SPRING_MONTHS = list(_MSL_SPRING_MONTHS)

# Minimum MEASURED spring months required for a valid annual spring mean.
# Sourced from config.MSL_MIN_MONTHS_PER_SPRING (3 of 3) — the same strictness
# van Willegen's MSL5 classification uses.  The strict rule is affordable here:
# across the network it retains 289 well-years against 291 at 2-of-3 and 294 at
# 1-of-3, versus 293 for the committed Jun-Sep >=2-of-4 summer rule (measured
# above, 2026-08-13).  Requiring all three months means the spring mean is
# genuinely a three-month mean and needs no caveat about which months
# contributed.  NOTE this is stricter than Script 36's spring_year_table(),
# which takes the mean of whatever MAM months are present; that divergence is
# recorded in claude/NRG_spring_BACI_spec_2026-08-13.md and is immaterial
# (~2% of well-years).
SPRING_MIN_MEASURED = _MSL_MIN_MONTHS_PER_SPRING

# ============================================================================
# DATA LOADING
# ============================================================================

def load_clearfell_data():
    """Load and validate wells, climate, and master data for clearfell analysis.

    Since v1.3.0 (Defect E fix) this function returns a 6-tuple including a
    per-cell provenance DataFrame, and no longer re-applies
    ``clean_well_series`` on the reloaded wells (the second cleaning pass
    was a no-op in normal pipeline order but a logical error obscuring
    data lineage).

    Returns
    -------
    wells : pd.DataFrame
        Monthly well depth timeseries (negative = below ground).
        Columns are lowercase well names. Merged from clean + extended.
    wells_provenance : pd.DataFrame
        Per-cell origin flags aligned to ``wells``, with values in
        ``{"measured", "interpolated", "missing"}``. Wells present in
        ``wells`` but absent from the provenance file (extended-only wells
        that were not in INT_WELLS_PROVENANCE) appear here with all rows
        flagged "measured" for compatibility — extended wells are not used
        by BACI consumers and a coarser flag is acceptable in their case.
    climate : pd.DataFrame
        Monthly climate with DatetimeIndex.  Columns include P_m, PET.
    master : pd.DataFrame
        Per-well SSM coefficients and cluster assignments from Script 03.
        Has 'well' column (lowercase, no spaces).
    well_locations : dict
        {well_name: {'easting': float, 'northing': float}} for all
        network wells found in the master data.
    valid_tiers : dict
        {'Impact': [...], 'Edge': [...], ...} with only wells present
        in the wells DataFrame.
    """
    # ── Climate ──────────────────────────────────────────────────────
    if not INT_CLIMATE.exists():
        raise FileNotFoundError(
            f"Climate file not found: {INT_CLIMATE}. Run Script 01 first.")
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    climate = climate.sort_index()

    # ── Wells ────────────────────────────────────────────────────────
    if not INT_WELLS_CLEAN.exists():
        raise FileNotFoundError(
            f"Wells file not found: {INT_WELLS_CLEAN}. Run Script 01 first.")

    wells_main = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells_main.index = pd.to_datetime(wells_main.index)
    wells_main.columns = wells_main.columns.str.lower().str.replace(' ', '')

    if INT_WELLS_EXTENDED.exists():
        wells_ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
        wells_ext.index = pd.to_datetime(wells_ext.index)
        wells_ext.columns = wells_ext.columns.str.lower().str.replace(' ', '')
        new_cols = [c for c in wells_ext.columns if c not in wells_main.columns]
        wells = pd.concat([wells_main, wells_ext[new_cols]], axis=1)
    else:
        wells = wells_main.copy()

    # NOTE: Per Defect E fix (v1.3.0), the wells loaded here are NOT re-cleaned.
    # `INT_WELLS_CLEAN` is the canonical cleaned output of Script 01 and any
    # re-application here would either be a no-op (current order) or, in
    # ordering edge cases, double-mask values that Script 01 already handled.
    # The cleaning function is now invoked exactly once per pipeline run, in
    # Script 01, and the resulting provenance file is the authoritative
    # record of what was measured vs interpolated.

    # ── Provenance ───────────────────────────────────────────────────
    # Loaded with the SAME column treatment as the wells frame so indexing
    # remains aligned. Extended-only wells get an all-"measured" placeholder
    # because the provenance file only covers the clean-network well set.
    if INT_WELLS_PROVENANCE.exists():
        prov = pd.read_csv(INT_WELLS_PROVENANCE, index_col=0, parse_dates=True)
        prov.index = pd.to_datetime(prov.index)
        prov.columns = prov.columns.str.lower().str.replace(' ', '')
        # Align to wells index and column set
        wells_provenance = pd.DataFrame(
            PROV_MEASURED, index=wells.index, columns=wells.columns,
            dtype=object,
        )
        common_cols = [c for c in wells.columns if c in prov.columns]
        wells_provenance.loc[:, common_cols] = prov.reindex(
            index=wells.index, columns=common_cols
        )
        # Fill any NaN provenance (e.g. months outside the per-well record)
        # with "missing" so the field is always one of the three flag values.
        wells_provenance = wells_provenance.fillna("missing")
    else:
        # Pre-Defect-E provenance file absent: assume all measured. Issues
        # a warning so the user is aware. Re-run Script 01 to populate.
        warnings.warn(
            f"INT_WELLS_PROVENANCE not found at {INT_WELLS_PROVENANCE}; "
            f"assuming all cells measured. Re-run Script 01 to generate.",
            stacklevel=2,
        )
        wells_provenance = pd.DataFrame(
            PROV_MEASURED, index=wells.index, columns=wells.columns,
            dtype=object,
        )

    # ── Master data ──────────────────────────────────────────────────
    if not INT_MASTER_DATA.exists():
        raise FileNotFoundError(
            f"Master data not found: {INT_MASTER_DATA}. Run Script 03 first.")
    master = pd.read_csv(INT_MASTER_DATA)
    master['well'] = master['Name_Original'].str.lower().str.replace(' ', '')

    # ── Well locations ───────────────────────────────────────────────
    well_locations = {}
    for _, row in master.iterrows():
        w = row['well']
        if w in ALL_NETWORK_WELLS:
            well_locations[w] = {
                'easting': float(row['Easting']),
                'northing': float(row['Northing']),
            }

    # Also try the locations file for wells not in master (e.g. extended)
    if DATA_WELL_ELEVATIONS.exists():
        loc_df = pd.read_csv(DATA_WELL_ELEVATIONS)
        loc_df['well'] = loc_df['Name'].str.lower().str.replace(' ', '')
        for _, row in loc_df.iterrows():
            w = row['well']
            if w in ALL_NETWORK_WELLS and w not in well_locations:
                well_locations[w] = {
                    'easting': float(row['E']),
                    'northing': float(row['N']),
                }

    # ── Validate tiers ───────────────────────────────────────────────
    valid_tiers = {}
    for tier_name, tier_wells in TIERS.items():
        valid = [w for w in tier_wells if w in wells.columns]
        valid_tiers[tier_name] = valid
        missing = [w for w in tier_wells if w not in wells.columns]
        if missing:
            warnings.warn(f"{tier_name}: missing wells {missing}")

    return wells, wells_provenance, climate, master, well_locations, valid_tiers


def load_ceh34_hindcast_series():
    """Load the CEH34 spliced (hindcast + observed) series from Script 10i.

    The hindcast is a donor regression of CEH34 against CEH9 (Climate
    Control) fitted on the pre-clearfell overlap.  Use this loader from
    scripts that need to include CEH34 in a pre-fell window starting
    before CEH34's 2010-08-01 first observation (e.g. for
    PRE_FELL_START = 2010-07-01).

    Returns
    -------
    series : pd.Series with DatetimeIndex
        Monthly CEH34 depth (m, negative below ground).  Index covers
        the union of hindcast and observed dates.  Values for dates
        prior to 2010-08-01 are synthetic; values from 2010-08-01
        onwards are observed.
    source : pd.Series with DatetimeIndex (str)
        ``'hindcast'`` or ``'observed'`` per row, aligned with `series`.

    Raises
    ------
    FileNotFoundError
        If Script 10i has not been run.  Run ``python src/10i_ceh34_hindcast.py``
        first.

    Notes
    -----
    The donor regression has r² ≈ 0.89 and an RMSE of ~150 mm; each
    hindcast value carries a ±290 mm 95% prediction interval.  This is
    substantial uncertainty; consumers should treat the spliced series
    as a single-well sensitivity tool, not as observational data.
    """
    if not OUT_10I_HINDCAST.exists():
        raise FileNotFoundError(
            f"CEH34 hindcast not found at {OUT_10I_HINDCAST}.  "
            f"Run Script 10i first: python src/10i_ceh34_hindcast.py")
    df = pd.read_csv(OUT_10I_HINDCAST, parse_dates=['Date'])
    df = df.set_index('Date').sort_index()
    return df['CEH34'], df['source']


def apply_ceh34_hindcast(wells, verbose=True):
    """Return a copy of `wells` with CEH34 replaced by its spliced
    (hindcast + observed) series from Script 10i.

    This is the opt-in mechanism for the pooled BACI scripts that adopt
    PRE_FELL_START = 2010-07-01.  Without this substitution, the
    2010-07-01 row of CEH34 will be NaN and the BACI centroid for that
    month will drop CEH34 — partly undoing the alignment the hindcast
    is intended to provide.

    Parameters
    ----------
    wells : pd.DataFrame
        Wells DataFrame as returned by load_clearfell_data().
    verbose : bool
        Print one-line confirmation of how many hindcast points were
        substituted.

    Returns
    -------
    wells_subbed : pd.DataFrame
        Copy of `wells` with the 'ceh34' column overlaid by the spliced
        series for dates < 2010-08-01.  Observed dates are unchanged.
    """
    series, source = load_ceh34_hindcast_series()
    wells_out = wells.copy()
    if 'ceh34' not in wells_out.columns:
        # No CEH34 column to substitute into — return unchanged
        return wells_out

    hindcast_dates = series.index[source == 'hindcast']
    # Align to the wells index — add rows for dates not currently present
    union_idx = wells_out.index.union(hindcast_dates)
    wells_out = wells_out.reindex(union_idx)
    # Substitute values
    wells_out.loc[hindcast_dates, 'ceh34'] = series.loc[hindcast_dates].values
    wells_out = wells_out.sort_index()

    if verbose:
        print(f"   [hindcast] CEH34: substituted {len(hindcast_dates)} hindcast "
              f"value(s) prior to 2010-08-01 (from Script 10i, CEH9 donor)")
    return wells_out


def get_tier(well_name):
    """Return the tier name for a given well, or 'Unknown'."""
    w = well_name.lower().replace(' ', '')
    for tier_name, tier_wells in TIERS.items():
        if w in tier_wells:
            return tier_name
    return 'Unknown'


# ============================================================================
# BACI DISPLACEMENT
# ============================================================================

def compute_control_centroid(wells, control_list, min_wells=None):
    """Fixed-membership monthly mean of control wells.

    A month contributes a centroid value only if at least ``min_wells``
    of the roster wells have a value that month; otherwise the centroid
    is NaN for that month (and the BACI row built from it drops out).

    By default ``min_wells = len(control_list)``, i.e. the centroid is a
    strict fixed-membership average — every roster well must be present.
    This prevents the silently-shifting-membership artefact: a plain
    NaN-skipping ``.mean(axis=1)`` would re-weight the centroid whenever
    a well goes offline (the NW10+CEH2 joint outage, Sep 2011-Sep 2012,
    being the dominant case), so the "centroid" would be an average of a
    different well set from month to month.  See
    AUDIT_10series_PRE_FELL_START.md and the v1.7.0 changelog.

    Parameters
    ----------
    wells : pd.DataFrame
    control_list : list of str
    min_wells : int or None
        Minimum number of roster wells that must have a value in a month
        for that month's centroid to be defined.  None (default) means
        ``len(available roster wells)`` — strict fixed membership.  Pass
        an explicit lower value only if a caller deliberately wants the
        legacy NaN-skipping behaviour; this is not recommended for BACI
        centroids and should be justified at the call site.

    Returns
    -------
    pd.Series with DatetimeIndex.  Months failing the threshold are NaN.
    """
    available = [w for w in control_list if w in wells.columns]
    if not available:
        raise ValueError("No control wells found in data")

    sub = wells[available]
    threshold = len(available) if min_wells is None else min_wells

    # Per-month count of roster wells with a value.
    present_count = sub.notna().sum(axis=1)
    centroid = sub.mean(axis=1)
    # Blank out months that fail the membership threshold.
    centroid = centroid.where(present_count >= threshold)
    return centroid


def compute_baci_displacement(wells, target_list, control_list):
    """Compute BACI displacement timeseries.

    Returns target_centroid − control_centroid, dropping NaN rows.

    Both the target and control centroids are fixed-membership averages
    (see compute_control_centroid): a month contributes only if every
    roster well on that side has a value.  This keeps the BACI a
    difference of two like-for-like centroids and avoids the
    shifting-membership artefact on either side.  As of v1.7.0 the
    target side is also fixed-membership; for a single-well target
    (the Impact zone, WMC3) this is a no-op, but it matters for the
    multi-well Edge zone.
    """
    target_mean = compute_control_centroid(wells, target_list)
    control_mean = compute_control_centroid(wells, control_list)
    baci = (target_mean - control_mean).dropna()
    return baci


# ============================================================================
# CUMULATIVE WATER BALANCE
# ============================================================================

def compute_cwb(climate, baseline_start=None, baseline_end=None):
    """Compute centred cumulative water balance (P − PET anomaly).

    Parameters
    ----------
    climate : pd.DataFrame with P_m and PET columns
    baseline_start, baseline_end : optional Timestamps for baseline period.
        If None, uses the full climate record.

    Returns
    -------
    pd.Series : centred cumulative water balance in mm
    """
    P_mm = pd.to_numeric(climate['P_m'], errors='coerce') * 1000
    PET_mm = pd.to_numeric(climate['PET'], errors='coerce') * 1000
    wb = (P_mm - PET_mm).dropna()

    if baseline_start is not None and baseline_end is not None:
        mask = (wb.index >= baseline_start) & (wb.index <= baseline_end)
        baseline_mean = wb[mask].mean()
    else:
        baseline_mean = wb.mean()

    cwb = (wb - baseline_mean).cumsum()
    return cwb


# ============================================================================
# DISTANCE TO COAST — TIER GEOMETRY (Scripts 10a and 25)
# ============================================================================
# Everything a document or a console banner might want to say about how far a
# tier sits from the shore is DERIVED here from the committed well metadata.
# No script, comment or docstring in the suite types a tier distance.

def well_distances_to_coast():
    """Distance to the coast, in metres, keyed by lowercase well name.

    Read from the committed well metadata (`DATA_DIST_COAST`), the same file
    Script 25 fits its cross-shore panel against, so the tier geometry and the
    gradient model cannot disagree about where a well is.
    """
    meta = pd.read_csv(DATA_DIST_COAST)
    meta['well'] = meta['Name'].astype(str).str.strip().str.lower()
    return dict(zip(meta['well'], meta['dist_coast_m'].astype(float)))


def tier_distance_stats(tier_wells, distances=None):
    """Distance-to-coast summary for one tier.

    Parameters
    ----------
    tier_wells : sequence of str
        Lowercase well names.
    distances : dict, optional
        Pre-loaded {well: distance_m}; loaded via well_distances_to_coast()
        when omitted.

    Returns
    -------
    dict with keys ``n``, ``mean_m``, ``sd_m``, ``min_m``, ``max_m``,
    ``span_m`` and ``wells`` (the members that carried a distance, ordered
    nearest to furthest).  Wells absent from the metadata are skipped and are
    absent from ``wells``, so ``n`` always describes the wells the statistics
    were actually computed over.
    """
    if distances is None:
        distances = well_distances_to_coast()
    pairs = [(w, distances[w]) for w in tier_wells
             if w in distances and np.isfinite(distances[w])]
    pairs.sort(key=lambda p: p[1])
    d = np.array([p[1] for p in pairs], dtype=float)
    if len(d) == 0:
        return dict(n=0, mean_m=np.nan, sd_m=np.nan, min_m=np.nan,
                    max_m=np.nan, span_m=np.nan, wells=[])
    return dict(
        n=len(d),
        mean_m=float(d.mean()),
        sd_m=float(d.std(ddof=1)) if len(d) > 1 else np.nan,
        min_m=float(d.min()),
        max_m=float(d.max()),
        span_m=float(d.max() - d.min()),
        wells=[p[0] for p in pairs],
    )


def far_field_admission_threshold_m(verbose=True):
    """The far-field tier's distance criterion, in metres, for THIS run.

    ``config.FAR_FIELD_REACH_MULTIPLE`` × the fitted cross-shore reach L.  The
    reach is read live from Script 25's committed panel-fit table (forest-free,
    linear-capped — the headline fit), and falls back to the documented
    first-pass default with a console warning when that table has not been
    written yet, following the same pattern as the other second-run consumers.

    Returns
    -------
    (threshold_m, reach_L_m, source) : tuple[float, float, str]
    """
    reach = None
    source = None
    try:
        if OUT_25_FIT_PARAMETERS.exists():
            fits = pd.read_csv(OUT_25_FIT_PARAMETERS)
            row = fits[(fits['source'] == 'forest_free')
                       & (fits['model'] == 'linear_capped')]
            if not row.empty and np.isfinite(float(row['L_m'].iloc[0])):
                reach = float(row['L_m'].iloc[0])
                source = OUT_25_FIT_PARAMETERS.name
    except Exception as exc:                              # pragma: no cover
        warnings.warn(f"Could not read the fitted reach from "
                      f"{OUT_25_FIT_PARAMETERS.name}: {exc}", stacklevel=2)
    if reach is None:
        from utils.pipeline_params import default_value
        reach = float(default_value("coast_reach_L_m"))
        source = "pipeline_params default_value('coast_reach_L_m')"
        if verbose:
            print(f"   ! Fitted reach unavailable — falling back to the "
                  f"documented default ({source})")
    return FAR_FIELD_REACH_MULTIPLE * reach, reach, source


def coastal_decay_params(source="full_canopy", model="linear_capped",
                         verbose=True):
    """(delta_0_mm_yr, L_m, provenance) for one of Script 25's panel fits.

    Read live from the committed panel-fit table, with the same documented
    first-pass fallback every other second-run consumer in this module uses.

    The default donor is the CANOPY-CONTROLLED full-network fit, per D-076.
    Twelve of the seventeen BACI wells are under canopy, so the forest-free
    headline — which drops those wells — estimates the gradient on the part of
    the network this panel mostly excludes. `full_canopy` keeps them and
    measures the canopy drift as its own term, so its delta_0 and L are net of
    canopy rather than free of forest.
    """
    d0 = L = None
    prov = None
    try:
        if OUT_25_FIT_PARAMETERS.exists():
            fits = pd.read_csv(OUT_25_FIT_PARAMETERS)
            row = fits[(fits['source'] == source) & (fits['model'] == model)]
            if not row.empty:
                d0v, Lv = float(row['delta_0_mm_yr'].iloc[0]), float(row['L_m'].iloc[0])
                if np.isfinite(d0v) and np.isfinite(Lv):
                    d0, L = d0v, Lv
                    prov = f"{OUT_25_FIT_PARAMETERS.name} [{source}/{model}]"
    except Exception as exc:                              # pragma: no cover
        warnings.warn(f"Could not read the coastal decay from "
                      f"{OUT_25_FIT_PARAMETERS.name}: {exc}", stacklevel=2)
    if d0 is None:
        from utils.pipeline_params import default_value
        d0 = float(default_value("coast_delta0_mm_yr"))
        L = float(default_value("coast_reach_L_m"))
        prov = "pipeline_params default_value(coast_delta0_mm_yr, coast_reach_L_m)"
        if verbose:
            print(f"   ! Coastal decay unavailable — falling back to the "
                  f"documented default ({prov})")
    return d0, L, prov


def coastal_drift_differential(target_wells, control_wells,
                               source="full_canopy", model="linear_capped",
                               verbose=True):
    """The coastal field's contribution to a BACI displacement, mm/yr.

    ``mean_w∈target δ(d_w) − mean_w∈control δ(d_w)``, with
    ``δ(d) = δ₀·max(0, 1 − d/L)``.

    THE MEAN OF THE DECAY, NOT THE DECAY OF THE MEAN. δ is capped, so the two
    differ wherever a tier straddles the reach — and the Forest control tier
    does, at a mean 955 m against L ≈ 895–930 m, where evaluating at the mean
    returns zero and credits the controls with no coastal drift at all. That
    exact mistake was live in Script 25's `baci_corroboration()` until
    2026-08-28 and put 1.9 mm/yr into a published z-test. Same defect class as
    D-046.

    The fit's constant `c` is deliberately omitted: it is common to both sides
    and cancels in a differential, so carrying it would only invite the reader
    to wonder whether it had been handled.

    Returns (differential_mm_yr, delta_0, L, provenance).
    """
    d0, L, prov = coastal_decay_params(source, model, verbose=verbose)
    dists = well_distances_to_coast()

    def mean_delta(wells):
        vals = [d0 * max(0.0, 1.0 - dists[w.lower()] / L)
                for w in wells if w.lower() in dists]
        return float(np.mean(vals)) if vals else float('nan')

    return mean_delta(target_wells) - mean_delta(control_wells), d0, L, prov


def far_field_tier_audit(verbose=True):
    """Re-derive the far-field tier's geometry and check it against the
    criterion, so the tier states its own properties instead of a comment
    asserting them.

    Returns a DataFrame with one row per member — distance to the coast, the
    admission threshold in force this run, and whether the member clears it —
    carrying the tier mean, span and the contrast against the impact zone as
    columns so the summary travels with the rows.
    """
    dists = well_distances_to_coast()
    threshold, reach, source = far_field_admission_threshold_m(verbose=verbose)
    ff = tier_distance_stats(FAR_FIELD_CONTROL_WELLS, dists)
    imp = tier_distance_stats(IMPACT_WELLS, dists)
    rows = []
    for w in ff['wells']:
        rows.append({
            'well': w.upper(),
            'dist_coast_m': dists[w],
            'reach_L_m': reach,
            'reach_source': source,
            'admission_threshold_m': threshold,
            'clears_threshold': bool(dists[w] > threshold),
            'tier_mean_dist_m': ff['mean_m'],
            'tier_span_m': ff['span_m'],
            'impact_dist_m': imp['mean_m'],
            'contrast_vs_impact_m': ff['mean_m'] - imp['mean_m'],
        })
    return pd.DataFrame(rows)


# ============================================================================
# DISTANCE-WEIGHTED SCRAPING COVARIATE
# ============================================================================

def distance_from_ceh36(easting, northing):
    """Euclidean distance from CEH36 scraping site."""
    return np.sqrt((easting - CEH36_EASTING)**2 +
                   (northing - CEH36_NORTHING)**2)


def distance_from_fell_centroid(easting, northing):
    """Euclidean distance from felling compartment centroid."""
    return np.sqrt((easting - FELL_CENTROID_EASTING)**2 +
                   (northing - FELL_CENTROID_NORTHING)**2)


def scraping_weight(distance_m, lambda_m=None):
    """Exponential decay weight for distance-weighted scraping.

    weight = exp(-d / λ)

    Parameters
    ----------
    distance_m : float
        Distance from scraping site in metres.
    lambda_m : float, optional
        Decay length scale. Default: SCRAPING_DECAY_LAMBDA (300 m).
    """
    if lambda_m is None:
        lambda_m = SCRAPING_DECAY_LAMBDA
    return np.exp(-distance_m / lambda_m)


def distance_weighted_scraping(date_index, scraping_date, well_easting,
                                well_northing, lambda_m=None):
    """Build distance-weighted scraping covariate for a single well.

    Returns a Series: 0 before scraping_date, exp(-d/λ) after.

    Parameters
    ----------
    date_index : DatetimeIndex
    scraping_date : Timestamp
    well_easting, well_northing : float
    lambda_m : float, optional

    Returns
    -------
    pd.Series
    """
    d = distance_from_ceh36(well_easting, well_northing)
    w = scraping_weight(d, lambda_m)
    covar = pd.Series(0.0, index=date_index)
    covar[date_index >= scraping_date] = w
    return covar


def build_scraping_covariate_centroid(date_index, scraping_date,
                                       well_locations, well_list,
                                       lambda_m=None):
    """Build distance-weighted scraping covariate for a tier centroid.

    The centroid covariate is the mean of per-well scraping weights
    for the wells in well_list.

    Parameters
    ----------
    date_index : DatetimeIndex
    scraping_date : Timestamp
    well_locations : dict of {well: {'easting': float, 'northing': float}}
    well_list : list of well names
    lambda_m : float, optional

    Returns
    -------
    pd.Series
    """
    weights = []
    for w in well_list:
        if w in well_locations:
            loc = well_locations[w]
            d = distance_from_ceh36(loc['easting'], loc['northing'])
            weights.append(scraping_weight(d, lambda_m))
    if not weights:
        return pd.Series(0.0, index=date_index)

    mean_weight = np.mean(weights)
    covar = pd.Series(0.0, index=date_index)
    covar[date_index >= scraping_date] = mean_weight
    return covar


# ============================================================================
# SEASONAL METRICS — summer minima and spring means
# ============================================================================
#
# Both metrics reduce a well to ONE value per year, so they are
# interchangeable as the response variable in a BACI design: same wells,
# same years, same N.  The summer minimum is an extreme-order statistic
# (the single lowest Jun-Sep month); the spring mean averages the three
# MAM months and is correspondingly less noisy.  The summer minimum is
# the drought-stress metric; the spring mean is the one the Curreli
# ecological thresholds are defined on.  Neither replaces the other.

def annual_seasonal_metric(series, months, agg, start_year=2006,
                           end_year=2026, provenance=None, min_measured=2):
    """Reduce a well's monthly series to one value per year over a season.

    General extractor behind ``annual_summer_minimum`` (agg='min' over
    Jun-Sep) and ``annual_spring_mean`` (agg='mean' over Mar-May).

    Parameters
    ----------
    series : pd.Series with DatetimeIndex (depth below ground, negative)
    months : sequence of int
        1-indexed calendar months forming the season.
    agg : {'min', 'mean'} or callable
        Reduction applied to the season's values.
    start_year, end_year : int
    provenance : pd.Series or None
        Optional per-cell provenance flags aligned to ``series`` from the
        Defect E fix. Values in {"measured", "interpolated", "missing"}.
        When supplied, only MEASURED in-season months count toward the
        ``min_measured`` threshold and only measured values enter the
        reduction. With provenance left as None, all non-null in-season
        months count (pre-Defect-E behaviour).
    min_measured : int
        Minimum number of measured in-season months required for a year
        to yield a value. Years below the threshold are omitted.

    Returns
    -------
    dict : {year: float}
    """
    if callable(agg):
        _reduce = agg
    elif agg == "min":
        _reduce = np.min
    elif agg == "mean":
        _reduce = np.mean
    else:
        raise ValueError(
            f"annual_seasonal_metric: agg must be 'min', 'mean' or a "
            f"callable, got {agg!r}")

    out = {}
    for yr in range(start_year, end_year + 1):
        mask = (series.index.year == yr) & (series.index.month.isin(months))
        if provenance is None:
            vals = series[mask].dropna()
        else:
            # Restrict to MEASURED cells only.
            prov_yr = provenance[mask]
            meas_mask = prov_yr == PROV_MEASURED
            vals = series[mask][meas_mask].dropna()
        if len(vals) >= min_measured:
            out[yr] = float(_reduce(vals))
    return out


def annual_spring_mean(series, start_year=2006, end_year=2026,
                       provenance=None, min_measured=None):
    """Compute annual spring mean (Mar–May) depth for a well.

    Thin wrapper over ``annual_seasonal_metric``. Season and strictness
    come from config (MSL_SPRING_MONTHS, MSL_MIN_MONTHS_PER_SPRING), so
    "spring mean" has one definition across the pipeline. Pass
    ``min_measured`` explicitly only to override the 3-of-3 default.

    Returns
    -------
    dict : {year: float} — mean Mar–May depth among measured cells.
           Years not meeting the threshold are omitted.
    """
    if min_measured is None:
        min_measured = SPRING_MIN_MEASURED
    return annual_seasonal_metric(
        series, SPRING_MONTHS, "mean",
        start_year=start_year, end_year=end_year,
        provenance=provenance, min_measured=min_measured,
    )


def annual_summer_minimum(series, start_year=2006, end_year=2026,
                          provenance=None, min_measured=2):
    """Compute annual summer minimum (Jun–Sep) depth for a well.

    Parameters
    ----------
    series : pd.Series with DatetimeIndex (depth below ground, negative)
    start_year, end_year : int
    provenance : pd.Series or None
        Optional per-cell provenance flags aligned to ``series`` from the
        Defect E fix. Values in {"measured", "interpolated", "missing"}.
        When supplied, only MEASURED Jun-Sep months count toward the
        ``min_measured`` threshold and only measured values can become the
        annual minimum. With provenance left as None, all non-null Jun-Sep
        months count (pre-Defect-E behaviour).
    min_measured : int
        Minimum number of measured Jun-Sep months required for a year to
        yield a summer minimum. Default 2 (matches the Defect E fix
        specification). When ``provenance`` is None this acts on non-null
        cells instead.

    Returns
    -------
    dict : {year: float} — minimum (most negative) depth in Jun–Sep among
           measured cells. Years not meeting the threshold are omitted.
    """
    return annual_seasonal_metric(
        series, SUMMER_MONTHS, "min",
        start_year=start_year, end_year=end_year,
        provenance=provenance, min_measured=min_measured,
    )


# ----------------------------------------------------------------------------
# SUMMER-PANEL YEAR SELECTION — for the four-zone BACI work
# ----------------------------------------------------------------------------
# Scripts 10j (summer), 10k and 10l select which years enter the summer
# analysis by a single rule: the Impact well WMC3 must have a usable
# Jun-Sep record that year.
#
# WHY WMC3 ONLY, not a balanced all-wells panel.  The four-zone model is
# a well-FE panel regression — every well carries its own intercept and
# the felling coefficient is fitted from whatever well-months exist.  A
# control well with a thin year simply contributes fewer rows; it does
# not distort the fit (there is no centroid whose membership could
# shift).  WMC3 is the exception: it is the entire n=1 Impact zone, so a
# year in which WMC3 has no usable summer has no Impact observation at
# all and the felling contrast for that year is unconstructible.  WMC3
# is therefore necessary; the other 13 wells are allowed to be patchy.
#
# "Usable" = at most ONE of the four Jun-Sep months is MISSING.  An
# interpolated / one-month-hindcast value counts as present; two or more
# missing months does not.
#
# Outcome on the current data: 2012 (WMC3 one measured month, a dry
# year) and 2019 (WMC3 Jun-Sep is one interpolated June + three missing)
# are dropped; the retained summer panel is 2011 + 2013-2018 + 2020
# onward.  SUMMER_PANEL_YEARS_EXCLUDED records this reviewed outcome;
# wmc3_usable_summer_years() below derives it from the live data and
# warns if the two disagree.
SUMMER_PANEL_GATEKEEPER_WELL = 'wmc3'
SUMMER_PANEL_MAX_MISSING = 1          # at most one missing Jun-Sep month
SUMMER_PANEL_YEARS_EXCLUDED = [2012, 2019]

# SPRING panel equivalent (Mar-May).  The same WMC3-gatekeeper reasoning
# applies unchanged — WMC3 is still the entire n=1 Impact zone.
#
# The spring rule is STRICTER than the summer one (max_missing = 0, i.e. all
# three MAM months present) and still admits MORE years, because WMC3's spring
# record is near-complete: 3-of-3 measured in 14 of the 15 years 2011-2025.
# Only 2012 is thin (1 measured, 1 interpolated, 1 missing).  2019 — dropped
# from the SUMMER panel because WMC3's Jun-Sep was one interpolated June plus
# three missing months — is fully measured in spring and is retained here.
# Retained spring panel: 2011 + 2013-2025 = 14 years, against the summer
# panel's 13.  Measured 2026-08-13; see claude/NRG_spring_BACI_spec_2026-08-13.md.
SPRING_PANEL_MAX_MISSING = 0          # all three Mar-May months required
SPRING_PANEL_YEARS_EXCLUDED = [2012]


def well_year_usable_summer(series, year, provenance=None,
                            max_missing=SUMMER_PANEL_MAX_MISSING):
    """Is a single well's Jun-Sep record for one year usable?

    Usable means at most ``max_missing`` of the four Jun-Sep months are
    MISSING.  An interpolated value counts as present (not missing);
    only genuinely absent months count against the well.  A year with
    no Jun-Sep rows at all (e.g. an as-yet-incomplete current year) is
    not usable.

    Parameters
    ----------
    series : pd.Series
        A single well's monthly depth series (DatetimeIndex).
    year : int
    provenance : pd.Series or None
        Per-cell provenance aligned to ``series``.  When None, non-null
        cells are treated as present (pre-Defect-E fallback).
    max_missing : int

    Returns
    -------
    bool
    """
    return well_year_usable_season(series, year, SUMMER_MONTHS,
                                   provenance=provenance,
                                   max_missing=max_missing)


def well_year_usable_season(series, year, months, provenance=None,
                            max_missing=SUMMER_PANEL_MAX_MISSING):
    """Is a single well's in-season record for one year usable?

    General form behind ``well_year_usable_summer`` (Jun-Sep) and the
    spring gatekeeper (Mar-May).  Usable means at most ``max_missing`` of
    the season's months are MISSING.  An interpolated value counts as
    present (not missing); only genuinely absent months count against the
    well.  A year with fewer index rows than the season has months (e.g.
    an as-yet-incomplete current year) is not usable.

    Parameters
    ----------
    series : pd.Series
        A single well's monthly depth series (DatetimeIndex).
    year : int
    months : sequence of int
        1-indexed calendar months forming the season.
    provenance : pd.Series or None
        Per-cell provenance aligned to ``series``.  When None, non-null
        cells are treated as present (pre-Defect-E fallback).
    max_missing : int

    Returns
    -------
    bool
    """
    mask = (series.index.year == year) & (series.index.month.isin(months))
    n_rows = int(mask.sum())
    if n_rows < len(months):
        # Fewer in-season index rows than the season has months —
        # an incomplete year.
        return False
    if provenance is None:
        n_missing = int(series[mask].isna().sum())
    else:
        n_missing = int((provenance[mask] == PROV_MISSING).sum())
    return n_missing <= max_missing


def wmc3_usable_summer_years(wells, wells_provenance=None,
                             start_year=2011, end_year=2026):
    """Years that enter the four-zone summer panel — the WMC3 gatekeeper.

    A year is included if the Impact well WMC3 has a usable Jun-Sep
    record that year (``well_year_usable_summer``).  See the block
    comment above for why WMC3 alone gates the panel and the other 13
    wells do not.

    The set is derived from the live data; it is cross-checked against
    the reviewed SUMMER_PANEL_YEARS_EXCLUDED constant and a note is
    printed if they disagree (e.g. the underlying record has changed),
    but the data-derived set is what is returned.

    Parameters
    ----------
    wells : pd.DataFrame
        Monthly well depths, lowercase column names.
    wells_provenance : pd.DataFrame or None
        Per-well provenance, same columns as ``wells``.
    start_year, end_year : int
        Range searched.  start_year defaults to 2011 — the earliest year
        the four-zone summer panel can begin (2009-2010 pre-date the
        full monitoring network).  Incomplete years near end_year are
        dropped automatically by the four-row check.

    Returns
    -------
    list of int
        Sorted years in which WMC3 has a usable summer record.
    """
    return _gatekeeper_usable_years(
        wells, SUMMER_MONTHS, SUMMER_PANEL_MAX_MISSING,
        SUMMER_PANEL_YEARS_EXCLUDED, "wmc3_usable_summer_years",
        "SUMMER_PANEL_YEARS_EXCLUDED",
        wells_provenance=wells_provenance,
        start_year=start_year, end_year=end_year,
    )


def wmc3_usable_spring_years(wells, wells_provenance=None,
                             start_year=2011, end_year=2026):
    """Years that enter the four-zone SPRING panel — the WMC3 gatekeeper.

    Spring sibling of ``wmc3_usable_summer_years``.  Same reasoning (WMC3
    is the entire n=1 Impact zone, so a year without a usable WMC3 record
    has no Impact observation), applied to Mar-May with
    ``SPRING_PANEL_MAX_MISSING`` and cross-checked against the reviewed
    ``SPRING_PANEL_YEARS_EXCLUDED``.

    Returns
    -------
    list of int
        Sorted years in which WMC3 has a usable spring record.
    """
    return _gatekeeper_usable_years(
        wells, SPRING_MONTHS, SPRING_PANEL_MAX_MISSING,
        SPRING_PANEL_YEARS_EXCLUDED, "wmc3_usable_spring_years",
        "SPRING_PANEL_YEARS_EXCLUDED",
        wells_provenance=wells_provenance,
        start_year=start_year, end_year=end_year,
    )


def _gatekeeper_usable_years(wells, months, max_missing, reviewed_excluded,
                             fn_label, const_label, wells_provenance=None,
                             start_year=2011, end_year=2026):
    """Shared implementation of the WMC3 panel-year gatekeeper.

    Derives the usable-year set from the live data, cross-checks it
    against the reviewed excluded-years constant, prints a note if they
    disagree, and returns the data-derived set.
    """
    w = SUMMER_PANEL_GATEKEEPER_WELL
    if w not in wells.columns:
        raise KeyError(f"{fn_label}: '{w}' not in data")
    prov_w = (wells_provenance[w]
              if wells_provenance is not None
              and w in wells_provenance.columns else None)

    years = [yr for yr in range(start_year, end_year + 1)
             if well_year_usable_season(wells[w], yr, months, prov_w,
                                        max_missing=max_missing)]

    derived_excluded = sorted(set(range(start_year, max(years) + 1))
                              - set(years)) if years else []
    expected_excluded = sorted(y for y in reviewed_excluded
                               if start_year <= y <= end_year)
    if derived_excluded != expected_excluded:
        print(f"  [{fn_label}] NOTE: data-derived excluded "
              f"years {derived_excluded} differ from the reviewed "
              f"constant {expected_excluded}.\n"
              f"    The data-derived set is being used.  If unexpected, "
              f"WMC3's record may have changed — review "
              f"{const_label}.")
    return years


def forest_control_centroid_summer_min(wells, forest_wells,
                                        start_year=2006, end_year=2026,
                                        min_wells=2, wells_provenance=None,
                                        min_measured=2):
    """Compute forest control centroid annual summer minimum.

    For each year, averages the summer minimum across all forest control
    wells with data, requiring at least min_wells.

    Parameters
    ----------
    wells : pd.DataFrame
    forest_wells : list of str
        Well names whose summer minima are pooled into the centroid.
    start_year, end_year : int
    min_wells : int
        Minimum number of wells contributing in a given year for a
        centroid value to be returned.
    wells_provenance : pd.DataFrame or None
        Per-well provenance flags (same shape and column names as
        ``wells``). When supplied, the per-well summer minima are computed
        with ``provenance=`` passed through and only measured cells count.
    min_measured : int
        Forwarded to ``annual_summer_minimum``. Default 2.

    Returns
    -------
    dict : {year: float}
    """
    return control_centroid_seasonal(
        wells, forest_wells, annual_summer_minimum,
        start_year=start_year, end_year=end_year, min_wells=min_wells,
        wells_provenance=wells_provenance, min_measured=min_measured,
    )


def control_centroid_seasonal(wells, control_wells, metric_fn,
                              start_year=2006, end_year=2026,
                              min_wells=2, wells_provenance=None,
                              min_measured=None):
    """Pool a per-well annual seasonal metric into a control centroid.

    General form behind ``forest_control_centroid_summer_min`` and
    ``forest_control_centroid_spring_mean``. For each year, averages the
    metric across all listed control wells that yielded a value,
    requiring at least ``min_wells`` contributors.

    Parameters
    ----------
    wells : pd.DataFrame
    control_wells : list of str
        Well names whose annual values are pooled into the centroid.
    metric_fn : callable
        ``annual_summer_minimum`` or ``annual_spring_mean`` (or any
        function with the same signature).
    start_year, end_year : int
    min_wells : int
        Minimum number of wells contributing in a given year for a
        centroid value to be returned.
    wells_provenance : pd.DataFrame or None
        Per-well provenance flags (same shape and column names as
        ``wells``). When supplied, only measured cells count.
    min_measured : int or None
        Forwarded to ``metric_fn``; None uses that metric's own default
        (2 of 4 for the summer minimum, 3 of 3 for the spring mean).

    Returns
    -------
    dict : {year: float}
    """
    per_well = {}
    for w in control_wells:
        if w in wells.columns:
            prov = (wells_provenance[w]
                    if wells_provenance is not None and w in wells_provenance.columns
                    else None)
            kwargs = {} if min_measured is None else {"min_measured": min_measured}
            per_well[w] = metric_fn(
                wells[w], start_year, end_year, provenance=prov, **kwargs,
            )

    all_years = set()
    for wm in per_well.values():
        all_years |= set(wm.keys())

    centroid = {}
    for yr in sorted(all_years):
        vals = [per_well[w][yr] for w in per_well if yr in per_well[w]]
        if len(vals) >= min_wells:
            centroid[yr] = np.mean(vals)

    return centroid


def forest_control_centroid_spring_mean(wells, control_wells,
                                        start_year=2006, end_year=2026,
                                        min_wells=2, wells_provenance=None,
                                        min_measured=None):
    """Control-centroid annual SPRING MEAN — spring sibling of
    ``forest_control_centroid_summer_min``. See that function and
    ``control_centroid_seasonal`` for parameters.
    """
    return control_centroid_seasonal(
        wells, control_wells, annual_spring_mean,
        start_year=start_year, end_year=end_year, min_wells=min_wells,
        wells_provenance=wells_provenance, min_measured=min_measured,
    )


# ============================================================================
# REPORTING UTILITIES
# ============================================================================

# ReportNumbers was lifted to utils/report_numbers_utils.py (2026-06-21) so
# non-clearfell scripts can import it without the clearfell BACI machinery.
# Re-exported here for backward compatibility — existing
# `from utils.clearfell_common import ReportNumbers` imports keep working.
from utils.report_numbers_utils import ReportNumbers  # noqa: F401


# ============================================================================
# TIER COLOURS (for consistent plotting across sub-scripts)
# ============================================================================

TIER_COLOURS = {
    'Impact':        '#D73027',
    'Edge':          '#F46D43',
    'Forest Ctrl':   '#4DAC26',
    'Coastal Ctrl':  '#8B6914',  # brown — C5 Coastal Forest
    'Climate Ctrl':  '#4575B4',
    # Colour-blind-safe purple (Dark2), well separated from the two blues and
    # the green above; the far-field tier plots beside all five.
    FAR_FIELD_TIER_LABEL: '#7570B3',
}

WELL_MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X', 'h', '<', '>']


# ============================================================================
# PRINT UTILITIES
# ============================================================================

def print_network_summary(valid_tiers):
    """Print the network summary to console.

    The tier count is taken from the mapping passed in rather than typed, so
    a caller that hands over a subset (Script 10j passes Impact + Edge only)
    is described correctly and adding a tier does not leave a stale count
    behind in the banner.
    """
    total = sum(len(v) for v in valid_tiers.values())
    print(f"\n  Network: {total} wells ({len(valid_tiers)}-tier design)")
    for tier, wells_list in valid_tiers.items():
        print(f"    {tier:<14}: {', '.join(w.upper() for w in wells_list)}")
    print()


# ============================================================================
# BACI-CORRECTED β₂ MULTIPLIER
# ============================================================================

# Fallback values used only when 10e_01_coefficient_shifts.csv cannot be read.
# These match the expected dynamic values (~1.10 / ~1.05) to within rounding
# so that outputs degrade gracefully rather than using the old 1.20.
_FALLBACK_CLEARFELL_B2 = 1.10
_FALLBACK_THINNING_B2  = 1.05


def load_clearfell_b2_multiplier(verbose=True):
    """Compute BACI-corrected clearfell β₂ multiplier from Script 10e output.

    Methodology
    -----------
    For each BACI tier, compute the tier ratio as the ratio of the
    tier-mean b2_after to the tier-mean b2_before:

        tier_ratio = mean(b2_after) / mean(b2_before)

    (i.e. a ratio of means, not a mean of per-well ratios).  The clearfell
    multiplier is the BACI-corrected Edge-tier ratio:

        multiplier = Edge_ratio − Climate_Ctrl_ratio + 1.0

    This subtracts the background climate drift (measured at Climate Ctrl
    wells that share the same post-2017 period but were unaffected by
    felling) from the Edge-tier signal, which showed the strongest
    clearfell-attributable β₂ response.  Using the Edge tier rather than
    the Impact tier is the more defensible choice: the Impact tier is a
    single well (WMC3), whose ratio (≈0.86) is dominated by the canopy
    removal that felling itself caused, while Edge wells retain canopy but
    receive lateral moisture from the cleared compartment.

    The thinning multiplier is defined as half the clearfell perturbation:

        thinning = 1.0 + (clearfell − 1.0) / 2.0

    Interpreting the per-tier ratios — read this before using them
    --------------------------------------------------------------
    The Before/After era fits in Script 10e use the canonical
    no-intercept SSM (`fit_ssm()` with `intercept=False`, Model A,
    consistent with Script 03 and Methods Supplement S.3).  A
    consequence is that the individual per-tier ratios are *not*
    interpretable on their own as absolute "fraction of β₂ retained"
    figures.  With no intercept, the fit has no free constant to absorb
    era-level offsets, so the whole β₂ scale is pulled towards the
    slope; the per-tier ratios come out compressed, and most of them
    sit below 1.0 (on the current data four of the five tiers — Impact,
    Edge, Coastal Ctrl, Climate Ctrl — are below 1.0; only Forest Ctrl
    exceeds it).  That sub-1.0 tendency is largely an artefact of the
    no-intercept rescaling, NOT a uniform physical decline in β₂ across
    every tier — so a single tier ratio should never be quoted as if it
    were a stand-alone effect size.

    What *is* interpretable is the difference between two ratios.  The
    clearfell multiplier is a difference-in-differences:

        clearfell = Edge_ratio − Climate_Ctrl_ratio + 1.0

    Because both ratios are produced by the same no-intercept fitting
    procedure on the same post-2017 period, the no-intercept rescaling
    enters each ratio in the same way and cancels in the subtraction.
    The differenced quantity is therefore invariant to that rescaling:
    it is the same difference-in-differences whether the eras are fitted
    with or without an intercept.  The differenced multiplier — not the
    individual ratios — is the quantity to interpret and to carry into
    the forestry scenarios.

    Worked example (live data, 2026-06, limit=1 pipeline)
    ------------------------------------------------------
    From `10e_01_coefficient_shifts.csv` the per-tier ratios
    (ratio of tier-mean b2_after to tier-mean b2_before — ratio of
    means, not mean of ratios) are::

        Impact       ratio = 0.8629   (WMC3, single well — canopy removed)
        Edge         ratio = 0.9830   (canopy retained, lateral moisture)
        Forest Ctrl  ratio = 1.0603
        Coastal Ctrl ratio = 0.9198
        Climate Ctrl ratio = 0.9515   (background drift)

    As above, do not read these as absolute β₂-retention fractions —
    the no-intercept fit has compressed the scale and pushed most tiers
    below 1.0.  Only their difference is rescaling-invariant.  The
    BACI-corrected clearfell multiplier is then::

        clearfell = Edge − Climate + 1.0
                  = 0.9830 − 0.9515 + 1.0
                  = 1.0315    (≈ +3.2% β₂)

    And the thinning multiplier::

        thinning = 1.0 + (1.0315 − 1.0) / 2.0
                 = 1.0157    (≈ +1.6% β₂)

    These are the values used by Scripts 19 and 21 in their forestry
    scenarios.  Recomputing on each call (rather than caching a constant)
    means the multipliers are always consistent with the latest 10e run.

    Returns
    -------
    clearfell_mult : float
        Multiplier for full clearfell (expected ~1.08 with current data).
    thinning_mult : float
        Multiplier for 50% thinning (expected ~1.04 with current data).
    tier_ratios : dict
        Per-tier mean b2_after/b2_before ratios, for provenance logging.
    """
    if not OUT_10E_COEFF_SHIFTS.exists():
        if verbose:
            print(f"  WARNING: {OUT_10E_COEFF_SHIFTS.name} not found "
                  f"— using fallback β₂ multipliers "
                  f"(clearfell={_FALLBACK_CLEARFELL_B2}, "
                  f"thinning={_FALLBACK_THINNING_B2})")
        return _FALLBACK_CLEARFELL_B2, _FALLBACK_THINNING_B2, {}

    try:
        cs = pd.read_csv(OUT_10E_COEFF_SHIFTS)
    except Exception as e:
        if verbose:
            print(f"  WARNING: Could not read {OUT_10E_COEFF_SHIFTS.name}: {e}")
            print("           Using fallback β₂ multipliers")
        return _FALLBACK_CLEARFELL_B2, _FALLBACK_THINNING_B2, {}

    # Compute per-tier mean ratios
    tier_ratios = {}
    for tier_name in ['Impact', 'Edge', 'Forest Ctrl', 'Coastal Ctrl',
                      'Climate Ctrl']:
        sub = cs[cs['Tier'] == tier_name]
        if sub.empty or sub['b2_before'].mean() <= 0:
            if verbose:
                print(f"  WARNING: No valid {tier_name} data in 10e — "
                      f"skipping tier")
            continue
        tier_ratios[tier_name] = sub['b2_after'].mean() / sub['b2_before'].mean()

    # Need both Edge and Climate Ctrl to compute BACI-corrected ratio
    if 'Edge' not in tier_ratios or 'Climate Ctrl' not in tier_ratios:
        if verbose:
            print("  WARNING: Missing Edge or Climate Ctrl tier ratios "
                  "— using fallback β₂ multipliers")
        return _FALLBACK_CLEARFELL_B2, _FALLBACK_THINNING_B2, tier_ratios

    # BACI-corrected Edge ratio: subtract climate drift, re-centre on 1.0
    edge_ratio   = tier_ratios['Edge']
    climate_drift = tier_ratios['Climate Ctrl']
    clearfell_mult = edge_ratio - climate_drift + 1.0
    thinning_mult  = 1.0 + (clearfell_mult - 1.0) / 2.0

    if verbose:
        print("  β₂ multiplier (BACI-corrected Edge ratio):")
        for tn, tr in tier_ratios.items():
            print(f"    {tn:15s}: {tr:.4f}")
        print(f"    Edge − Climate Ctrl + 1 = "
              f"{edge_ratio:.4f} − {climate_drift:.4f} + 1.0 = "
              f"{clearfell_mult:.4f}")
        print(f"    Clearfell: {clearfell_mult:.4f}  "
              f"Thinning: {thinning_mult:.4f}")

    return clearfell_mult, thinning_mult, tier_ratios
