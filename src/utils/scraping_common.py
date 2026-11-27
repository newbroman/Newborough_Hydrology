"""
utils/scraping_common.py
========================
Shared constants, well lists, and helpers for the Script 09 scraping
analysis suite (09a–09e).

Analogous to clearfell_common.py for the Script 10 suite.  All scraping-
specific configuration lives here so that individual modules can stay
focused on analysis.

Constants
---------
SCRAPING_DATE         April 2015 — ground scraping at CEH36
CLEARFELL_DATE     December 2017 — pine clearfell (shared with clearfell)
SCRAPING_DATE_2       October 2023 — second (re-)scraping event
FELLING_YEAR          2017
REGIONAL_MEAN_START   Feb 2009 — fixed-composition window for regional mean

Well groups
-----------
IMPACT_WELLS        Wells on or adjacent to the scraped area
CONTROL_WELLS       C3 climate-control wells (undisturbed)
PAIRED_CONTROLS     {impact: control} for paired BACI
DONOR_CANDIDATES    Long-record wells for synthetic control
TIER1_WELLS         Controls evaluated vs regional mean
TIER2_WELLS         Impacts evaluated vs paired control

Era system
----------
WELL_ERAS           {well: {era_name: (start, end)}} for all analysis wells.
                    Start is inclusive, end is exclusive.
"""

__version__ = "1.16.0"  # 2026-11-27 (D-349 B2, B3, A8): compute_scenario_bars() returns the SUSTAINED change in stored water (the summer forcing change, recurring each summer, carried to its periodic steady state on the group's beta_3 and averaged over the summer months, x Sy; mm w.e.), not a one-month flux, and NaN at a group whose beta_3 is not identified (beta3_identified_groups, D-333); compute_scenario_bar_range() carries Clearfell / Thinning over the clearfell anchor range; flux_to_summer_min_mm() takes that storage (NaN-safe); load_cluster_params' mean depth over RECORD_FIT_START onward. Was "1.15.0"  # 2026-11-27 (D-348): cluster keys from CLUSTER_LABELS (five groups); forest by FOREST_CIDS; scenario_cluster_sy matches a key to its group label so C3 no longer matches C3f; load_cluster_params' Sy median and mean depth from cluster-level wells. Was "1.14.0"  # Hollingham (2026) - 2026-11-20 (T-209, D-333; changelog 2026-11-20b).
#   compute_scenario_bars(): Clearfell and Thinning 50% return a share of the interception
#   (clearfell_common.clearfell_return_fraction, calibrated on the observed BACI step) instead of a beta_2
#   multiplier; arguments clearfell_frac / thinning_frac replace clearfell_b2_mult / thinning_b2_mult.
# 1.13.0  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b). load_cluster_params() measures
#   h_disp from each cluster's Model B implied datum (03_03 implied_datum_m = DRAINAGE_DATUM - alpha/beta_3) instead of
#   DRAINAGE_DATUM, so b3*h_disp is Model B's drainage term with 03_03's (now Model B) betas, and returns alpha and
#   implied_datum_m. compute_scenario_bars() differences two fluxes at one h_disp, so its bars do not depend on the datum.
# 1.12.0  # Hollingham (2026) - 2026-10-04 (T-97, D-239). The forestry bars are anchored to the
#   December 2017 felling: the canopy's draw scaled by the felled well's measured beta_2 change (Impact tier net of
#   the Climate controls, clearfell_common.load_clearfell_impact_b2_multiplier) and no interception recharge term;
#   compute_scenario_bars_from_params() passes those multipliers. The climate bars are unchanged.
# 1.11.0  # Hollingham (2026) - 2026-10-03 (D-238). compute_scenario_bars(): the climate scenarios no
#   longer multiply the rainfall change by (1 - I) at forest clusters - beta_1 was fitted on gross rainfall,
#   so the canopy is already inside it. The forestry bars (sP = 1) are unchanged.
# 1.10.0  # Hollingham (2026) - 2026-08-31. SUMMER_MONTHS and SCENARIO_SUMMER_MONTHS both now from config.SUMMER_MINIMUM_MONTHS - this module held two copies of the same window.
#   Batch two of the seasonal-windows migration (D-100): the window's
#   MONTHS ARE UNCHANGED and the constant is asserted equal to the literal it
#   replaced, in value and in type, read mechanically out of git HEAD. No
#   committed value moves.
#
# v1.9.0  # Hollingham (2026) — 2026-08-29. the legacy alias is removed; CLEARFELL_DATE is the only name (T-17).
#   No value changes; verified by re-run against the 2026-08-29 pipeline outputs.
# v1.8.0  # Hollingham (2026) — 2026-08-29. Intervention dates now
#   built from utils.config instead of duplicating clearfell_common (D-084);
#   SCRAPING_DATE_0 (Feb 2013) added, having been absent here; CLEARFELL_DATE
#   added as the unambiguous alias. No value changes.
# v1.7.0  # Hollingham (2026) — 2026-08-20. Adds the
#     scrape-affected-well registry (SCRAPE_WELLS_POST_INSTALL,
#     SCRAPE_WELLS_CENSORED) and apply_scrape_treatment().  Script 25 held a
#     per-script SCRAPED_WELLS = ["ceh36"] that contradicted
#     config.SCRAPE_KML_FILES, so five wells inside scrape footprints sat in
#     the coastal-gradient panel untreated.  The dates come from
#     SCRAPING_DATE_2 rather than being restated.
# 1.6.1  # Hollingham (2026) — 2026-08-19. Reads the per-well
#   WTF Sy table from OUT_18_WELL_SY_TABLE; INT_WTF_WELL_SY is retired
#   (D-038). Pure path/symbol change, values identical.
#
# v1.6.0  # 2026-07-19 — MPL_DEFAULTS relocated to render_utils.py;
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import pandas as pd
import numpy as np
from scipy import stats as _stats

# ============================================================================
# INTERVENTION DATES
# ============================================================================
# Built from utils.config (D-084). These were literals here until 2026-08-29,
# duplicating clearfell_common. Values unchanged. SCRAPING_DATE_0 is NEW here —
# the February 2013 cuts existed only in clearfell_common, so no scraping
# analysis working from this module could see them.
from utils.config import (
    SUMMER_MINIMUM_MONTHS,
    CLUSTER_LABELS as _CLUSTER_LABELS,
    FOREST_CIDS as _FOREST_CIDS,
    CLEARFELL_DATE_ISO as _CLEARFELL_DATE_ISO,
    SCRAPING_DATE_0_ISO as _SCRAPING_DATE_0_ISO,
    SCRAPING_DATE_ISO as _SCRAPING_DATE_ISO,
    SCRAPING_DATE_2_ISO as _SCRAPING_DATE_2_ISO,
)

SCRAPING_DATE_0  = pd.Timestamp(_SCRAPING_DATE_0_ISO)  # Feb 2013 unmonitored cuts
SCRAPING_DATE    = pd.Timestamp(_SCRAPING_DATE_ISO)    # April 2015 CEH36 scrape
CLEARFELL_DATE   = pd.Timestamp(_CLEARFELL_DATE_ISO)   # December 2017 clearfell
SCRAPING_DATE_2  = pd.Timestamp(_SCRAPING_DATE_2_ISO)  # October 2023 re-scraping

FELLING_YEAR = CLEARFELL_DATE.year   # 2017

# ============================================================================
# RECORD-LENGTH-BALANCE CUTOFFS
# ============================================================================
# The scraping suite's paired BACI design (impact_well − paired_control_well)
# self-equalises pre-event record lengths via dropna() — a paired series can
# only exist where both wells are reading.  However, the *regional-mean*
# control (mean over CLIMATE_CONTROLS) does NOT self-equalise: it changes
# composition through time as wells come online.  CLIMATE_CONTROLS:
#   NW5, NW6, NW7  reading from 2005-03 (3 wells)
#   + CEH9         from 2006-05 (4 wells)
#   + WMC2         from 2009-02 (5 wells — fixed composition thereafter)
#
# REGIONAL_MEAN_START restricts the regional-mean control to the
# fixed-composition window (5 wells, 2009-02 onwards).  CEH4 evaluated vs
# regional mean drops 33 pre-2009-02 rows from its Baseline era; the
# The Baseline-era mean shifts in consequence.  CEH22 paired against
# regional mean is unchanged (CEH22 starts 2010-03, already inside the
# fixed-composition window).
REGIONAL_MEAN_START = pd.Timestamp("2009-02-01")

# ============================================================================
# SCRAPE-AFFECTED WELLS — WHICH RECORD IS USABLE, AND FROM WHEN
# ============================================================================
# Six dipwells sit inside a GPS-traced scrape footprint (the canonical list is
# config.SCRAPE_KML_FILES; Scrape_A and Scrape_B contain no wells).  Measured
# perpendicular distances to the footprint outline, from the committed KML
# geometry: ceh41 2 m, ceh40 3 m, ceh21 9 m, ceh42 11 m, ceh36 16 m, ceh18
# 19 m.  They divide into two classes, and any trend analysis has to treat
# them differently:
#
#   SCRAPE_WELLS_POST_INSTALL — installed AFTER their scrape.  No clean record
#     exists at any point, so the well carries no usable pre-intervention
#     baseline and is dropped entirely from trend work.
#
#   SCRAPE_WELLS_CENSORED — installed BEFORE their scrape, so the record up to
#     the scrape date is clean and is kept; only the post-scrape tail is
#     dropped.  CEH18 and CEH21 were scraped in October 2023 alone, which
#     leaves 87% and 85% of their records respectively — dropping these wells
#     outright would discard two of the three near-shore anchors of the
#     coastal-gradient fit for the sake of their last two years.
#
# CEH36 is deliberately absent from both lists.  It is the scraping study's own
# impact well and is excluded by the analyses that examine it, on separate
# grounds; listing it here as well would double-book the exclusion.
#
# CEH4 is retained in full.  At 24 m it is the nearest well outside any
# footprint, but the April-2015 before/after test finds no drawdown signature
# at it: it changed -105 mm across the step against a network mean of -144 mm,
# i.e. it moved LESS than average, which is the wrong sign for a drawdown cone.
# It is also the principal near-shore anchor of the coastal-gradient fit.
SCRAPE_WELLS_POST_INSTALL = ["ceh40", "ceh41", "ceh42"]

SCRAPE_WELLS_CENSORED = {
    "ceh18": SCRAPING_DATE_2,
    "ceh21": SCRAPING_DATE_2,
}


def apply_scrape_treatment(long, well_col="well", date_col="date"):
    """Remove scrape contamination from a long-form (well, date, value) frame.

    Drops every row of a well installed after its own scrape, and truncates a
    well installed before its scrape at that scrape's date.  Well names are
    matched on the normalised (stripped, lower-cased) form used throughout the
    pipeline.  Returns a filtered copy; the input is not modified.
    """
    wells = long[well_col].astype(str).str.strip().str.lower()
    keep = ~wells.isin(SCRAPE_WELLS_POST_INSTALL)
    for well, scrape_date in SCRAPE_WELLS_CENSORED.items():
        keep &= ~((wells == well) & (long[date_col] >= scrape_date))
    return long[keep].copy()

# ============================================================================
# WELL GROUPS
# ============================================================================

# --- Core BACI wells ---
IMPACT_WELLS = ["ceh36", "ceh18", "ceh21"]
PAIRED_CONTROLS_MAP = {
    "ceh36": "ceh4",
    "ceh18": "ceh4",
    "ceh21": "ceh22",
}

# --- Tier assignments (for BACI figures) ---
TIER1_WELLS = ["ceh4", "ceh22"]      # controls — evaluated vs regional mean
TIER2_WELLS = ["ceh36", "ceh18", "ceh21"]  # impacts — evaluated vs paired ctrl

# --- Regional climate controls ---
CLIMATE_CONTROLS = ["ceh9", "nw7", "nw6", "nw5", "wmc2"]

# --- Donor pool for synthetic control ---
DONOR_CANDIDATES = [
    "ceh1", "ceh2", "ceh5", "ceh6", "ceh9", "ceh11", "ceh16",
    "ceh17", "ceh19", "ceh22", "ceh24",
]

# --- Summer months (Jun–Sep) for ecological threshold analysis ---
SUMMER_MONTHS = list(SUMMER_MINIMUM_MONTHS)

# ============================================================================
# ERA DEFINITIONS
# ============================================================================
WELL_ERAS = {
    "ceh36": {
        "1_Baseline":       (None, SCRAPING_DATE),
        "2_Pure_Scraping":  (SCRAPING_DATE, CLEARFELL_DATE),
        "3_Felling_Pulse":  (CLEARFELL_DATE, None),
    },
    "ceh4": {
        "1_Baseline":       (None, SCRAPING_DATE),
        "2_Pure_Scraping":  (SCRAPING_DATE, CLEARFELL_DATE),
        "3_Felling_Pulse":  (CLEARFELL_DATE, None),
    },
    "ceh18": {
        "1_Baseline":       (None, CLEARFELL_DATE),
        "2_Felling_Pulse":  (CLEARFELL_DATE, SCRAPING_DATE_2),
        "3_After_Scraping": (SCRAPING_DATE_2, None),
    },
    "ceh21": {
        "1_Baseline":        (None, CLEARFELL_DATE),
        "2_Coastal_Drawdown": (CLEARFELL_DATE, SCRAPING_DATE_2),
        "3_After_Scraping":  (SCRAPING_DATE_2, None),
    },
    "ceh22": {
        "1_Baseline":        (None, CLEARFELL_DATE),
        "2_Coastal_Drawdown": (CLEARFELL_DATE, SCRAPING_DATE_2),
        "3_After_Scraping":  (SCRAPING_DATE_2, None),
    },
}

# ============================================================================
# STYLE CONSTANTS
# ============================================================================
ERA_COLORS = {
    "1_Baseline":        "#009E73",
    "2_Pure_Scraping":   "#56B4E9",
    "3_Felling_Pulse":   "#CC79A7",
    "2_Felling_Pulse":   "#CC79A7",
    "2_Coastal_Drawdown": "#E69F00",
    "3_After_Scraping":  "#D55E00",
}

ERA_MARKERS = {
    "1_Baseline":        "o",
    "2_Pure_Scraping":   "s",
    "3_Felling_Pulse":   "^",
    "2_Felling_Pulse":   "^",
    "2_Coastal_Drawdown": "v",
    "3_After_Scraping":  "D",
}

ERA_LINESTYLES = {
    "1_Baseline":        ":",
    "2_Pure_Scraping":   "--",
    "3_Felling_Pulse":   "-",
    "2_Felling_Pulse":   "-",
    "2_Coastal_Drawdown": "--",
    "3_After_Scraping":  "-.",
}

# MPL_DEFAULTS relocated to utils/render_utils.py (2026-07-19, render_utils
# v1.0.0) so figure styling has a single home. Re-exported here for backwards
# compatibility with 09a/09c/09d/09e/09f. Import from render_utils in new code.
from utils.render_utils import MPL_DEFAULTS  # noqa: F401  (re-export)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def era_filter(series, start, end):
    """Filter a pandas Series to a date range [start, end)."""
    mask = pd.Series(True, index=series.index)
    if start is not None:
        mask &= series.index >= start
    if end is not None:
        mask &= series.index < end
    return series[mask]


def load_scraping_data():
    """Load well, provenance, and climate data for the scraping analysis.

    Since v1.3.0 (Defect E fix), this returns a 3-tuple including a
    per-cell provenance DataFrame from `01_wells_provenance.csv`. The
    provenance has values in {"measured", "interpolated", "missing"}
    aligned to ``wells`` and is forwarded by 09c into
    ``annual_summer_minimum`` so that years with fewer than 2 measured
    Jun-Sep months for a given well are correctly excluded (this drops
    the phantom 2019 summer minima for NW6 and NW7 — both in
    CLIMATE_CONTROLS). Other scraping scripts (09a, 09d, 09e) accept the
    new return for forwards compatibility but do not yet consume the
    provenance directly; their pre/post-fix shifts come from the
    updated `01_wells_clean.csv` content under `limit=1`.

    Returns
    -------
    wells : pd.DataFrame
        Monthly well depth timeseries (negative = below ground). Columns
        are lowercase, no-space well names. Union of clean + extended.
    wells_provenance : pd.DataFrame
        Per-cell origin flags aligned to ``wells`` (values in
        {"measured", "interpolated", "missing"}). Wells present in
        ``wells`` but absent from the provenance file (extended-only
        wells) appear with all rows flagged "measured" — extended-only
        wells are not used by the scraping panel's BACI or summer-minima
        analyses and a coarser flag is acceptable for them. If the
        provenance file does not exist (pre-Defect-E pipeline state), a
        warning is issued and an all-"measured" placeholder is returned.
    climate : pd.DataFrame
        Monthly climate with DatetimeIndex (P_m, PET columns).
    """
    from utils.paths import (
        INT_WELLS_CLEAN, INT_WELLS_EXTENDED, INT_CLIMATE,
        INT_WELLS_PROVENANCE,
    )

    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    climate = climate.sort_index()

    wells_main = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells_main.columns = wells_main.columns.str.lower().str.replace(" ", "")

    if INT_WELLS_EXTENDED.exists():
        wells_ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
        wells_ext.columns = wells_ext.columns.str.lower().str.replace(" ", "")
        new_cols = [c for c in wells_ext.columns if c not in wells_main.columns]
        wells = pd.concat([wells_main, wells_ext[new_cols]], axis=1)
    else:
        wells = wells_main

    # ── Provenance ────────────────────────────────────────────────────
    # Loaded with the same lower-case column treatment as wells. Extended-
    # only wells get an all-"measured" placeholder because the provenance
    # file only covers the clean-network well set; extended wells are not
    # used by the BACI or summer-minima analyses, so a coarser flag is
    # acceptable.
    if INT_WELLS_PROVENANCE.exists():
        prov = pd.read_csv(INT_WELLS_PROVENANCE, index_col=0,
                           parse_dates=True)
        prov.columns = prov.columns.str.lower().str.replace(" ", "")
        wells_provenance = pd.DataFrame(
            "measured", index=wells.index, columns=wells.columns,
            dtype=object,
        )
        common_cols = [c for c in wells.columns if c in prov.columns]
        wells_provenance.loc[:, common_cols] = prov.reindex(
            index=wells.index, columns=common_cols,
        )
        wells_provenance = wells_provenance.fillna("missing")
    else:
        import warnings
        warnings.warn(
            f"INT_WELLS_PROVENANCE not found at {INT_WELLS_PROVENANCE}; "
            f"assuming all cells measured. Re-run Script 01 to generate.",
            stacklevel=2,
        )
        wells_provenance = pd.DataFrame(
            "measured", index=wells.index, columns=wells.columns,
            dtype=object,
        )

    return wells, wells_provenance, climate


def format_p_value(p):
    """Format a p-value for display."""
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "<0.001"
    return f"{p:.4f}"


def load_cluster_params():
    """Load consolidated cluster parameters from pipeline outputs.

    Combines:
      - beta from Script 03 cluster mechanistic table
      - Sy from the WTF per-well estimates, cluster median (Script 17's
        method, written by Script 18 — D-038)
      - h_disp = the cluster's Model B implied datum (03_03 implied_datum_m,
        DRAINAGE_DATUM − α/β₃; D-332) + its wells' mean depth (Script 01)
      - forest flag (groups in FOREST_CIDS: C4 and C3f, D-348)

    D-348: the cluster Sy median and mean depth use the group's cluster-level wells only (In_Cluster_Level).

    Model B is exactly Model A at the implied datum, so β₃·h_disp here is
    Model B's drainage term (β₃·(D + h) − α).

    Returns
    -------
    dict : {cname: {b1, b2, b3, alpha, implied_datum_m, Sy, h_disp, forest}}
    """
    from utils.paths import (
        OUT_03_MECHANISTIC_TABLE, INT_MASTER_DATA,
        OUT_18_WELL_SY_TABLE, INT_WELLS_CLEAN,
    )
    from utils.config import DRAINAGE_DATUM

    coeff = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
    from utils.cluster_series import in_cluster_level
    from utils.config import RECORD_FIT_START
    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells.columns = wells.columns.str.lower().str.replace(" ", "")
    # 1.16.0 (D-349): the mean depth over D-347's window, the one the implied datum is fitted on
    wells = wells[wells.index >= pd.Timestamp(RECORD_FIT_START)]
    master = pd.read_csv(INT_MASTER_DATA)
    master["match"] = master["Name_Original"].str.lower().str.replace(" ", "")
    master = master[in_cluster_level(master)]   # D-348: cluster-level wells only

    sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
    _grp = dict(zip(master["match"], master["Cluster"].astype(int)))
    sy_df["_group"] = sy_df["Well"].astype(str).str.lower().str.replace(" ", "").map(_grp)
    sy_by_cluster = sy_df.dropna(subset=["_group"]).groupby("_group")["Sy_median"].median()
    sy_by_cluster.index = sy_by_cluster.index.astype(int)

    params = {}
    for _, row in coeff.iterrows():
        cl = int(row["Cluster"])
        cname = f"C{cl}"

        cl_wells = master[master["Cluster"] == cl]["match"].tolist()
        available = [w for w in cl_wells if w in wells.columns]
        mean_depth = wells[available].mean().mean() if available else -0.5
        # 1.13.0 (D-332): displacement above Model B's implied datum, not DRAINAGE_DATUM
        z_b = (float(row["implied_datum_m"]) if "implied_datum_m" in row and pd.notna(row["implied_datum_m"])
               else float(DRAINAGE_DATUM))
        h_disp = z_b + mean_depth

        params[cname] = {
            "b1": float(row["beta_1_recharge"]),
            "b2": float(row["beta_2_atmospheric_draw"]),
            "b3": float(row["beta_3_drainage"]),
            "alpha": float(row["alpha"]) if "alpha" in row and pd.notna(row["alpha"]) else 0.0,
            "implied_datum_m": z_b,
            "Sy": float(sy_by_cluster.get(cl, 0.25)),
            "h_disp": h_disp,
            "forest": cl in _FOREST_CIDS,
        }

    return params


def load_summer_climate():
    """Load summer mean P and PET from pipeline climate data."""
    from utils.paths import INT_CLIMATE
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    summer = climate[climate.index.month.isin(SUMMER_MONTHS)]
    return float(summer["P_m"].mean()), float(summer["PET"].mean())


def load_annual_climate():
    """Load annual-mean (all-month) P and PET from pipeline climate data.

    Companion to load_summer_climate(); used by Script 09d to evaluate the
    scenario bars under annual-mean forcing (Figure 26) alongside the
    summer-forcing figure (Figure 27).
    """
    from utils.paths import INT_CLIMATE
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    return float(climate["P_m"].mean()), float(climate["PET"].mean())


def significance_stars(p):
    """Return significance stars for a p-value."""
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
# SCENARIO COMPARISON — shared computation
# ============================================================================

def beta3_identified_groups():
    """1.16.0 (D-349 B2, D-333): {group id: True/False}, whether the group's Model B centroid beta_3 passes Script
    48's identifiability rule (model_utils.response_identified on 03_03's beta_3_drainage, pvalue_beta_3 and n;
    four parameters). A group that fails it carries no level through 1/beta_3 (C4 on the committed run). An absent
    table (first pass) counts every group identified, with a warning."""
    from utils.paths import OUT_03_MECHANISTIC_TABLE
    from utils.model_utils import response_identified
    try:
        t = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
    except FileNotFoundError:
        print(f"  WARNING: {OUT_03_MECHANISTIC_TABLE.name} not found - every group's beta_3 counted identified")
        return {int(c): True for c in _CLUSTER_LABELS}
    return {int(r["Cluster"]): bool(response_identified(r["beta_3_drainage"], r["pvalue_beta_3"], r["n"], 4)[0])
            for _, r in t.iterrows()}


def compute_scenario_bars(cluster_params, summer_P, summer_PET,
                          clearfell_frac=None, thinning_frac=None):
    """Compute per-cluster scenario bars: the SUSTAINED change in stored water (mm w.e.).

    Uses the Option 3 seasonal perturbation formulation for the one-month forcing change:
        Δf = β₁·ΔP − Δβ₂·PET
    with forestry interception and UKCP18 climate scaling, on the summer-mean climate. 1.16.0 (D-349 B2): that
    change, applied in the summer months (SUMMER_MINIMUM_MONTHS) of every year, is carried to its sustained level
    on the group's beta_3 (model_utils.sustained_monthly_response, the periodic steady state), as D-239 says; the
    bar is that level's mean over the summer months, × Sy × 1000 as stored water. Before 1.16.0 the bar was the one-month flux
    change × Sy ("mm w.e./month"), a rate set beside levels. A group whose beta_3 is not identified
    (beta3_identified_groups(), D-333: C4) gets NaN for every scenario: no level is carried through 1/β₃ there.

    Parameters
    ----------
    cluster_params : dict
        {cname: {b1, b2, b3, Sy, h_disp, forest}} from pipeline outputs.
    summer_P : float
        Mean summer rainfall (m/month) from climate data.
    summer_PET : float
        Mean summer PET (m/month) from climate data.
    clearfell_frac : float or None
        1.14.0 (T-209, D-333): the share f of the canopy's interception the clearfell returns as recharge
        (clearfell_common.clearfell_return_fraction(), calibrated on the observed BACI step at the felled
        well). If None, loaded. The clearfell bar is that flux sensitivity, not a beta_2 multiplier.
    thinning_frac : float or None
        Half the clearfell's f if None: an upper bound (the remaining trees take up part of it).

    Returns
    -------
    dict : {scenario_name: {cluster: sustained storage change, mm w.e. (NaN: beta_3 not identified)}}
    """
    from utils.model_utils import sustained_monthly_response
    from utils.config import (
        FOREST_INTERCEPTION, BROADLEAF_INTERCEPTION,
        BROADLEAF_B2_SUMMER,
        UKCP18_DRY_P_SUMMER, UKCP18_DRY_PET_SUMMER,
        UKCP18_WET_P_SUMMER, UKCP18_WET_PET_SUMMER,
    )

    # 1.14.0 (T-209, D-333): the clearfell returns a share f of the interception, calibrated on the observed
    # BACI step; no beta_2 multiplier from era refits (withdrawn, D-333).
    if clearfell_frac is None:
        from utils.clearfell_common import clearfell_return_fraction
        clearfell_frac = clearfell_return_fraction(verbose=False)["f"]
    if thinning_frac is None:
        thinning_frac = clearfell_frac / 2.0

    clusters = [f"C{c}" for c in _CLUSTER_LABELS]   # D-348: the five groups (C5 = C3f)
    scenarios = {}
    identified = beta3_identified_groups()   # 1.16.0 (D-349 B2, D-333)
    _SUMMER_SET = set(SUMMER_MINIMUM_MONTHS)

    def _flux(b1, b2, P_eff, PET, b3, h_disp):
        return b1 * P_eff - b2 * PET - b3 * h_disp

    for scenario_name, config in [
        # 1.14.0 (T-209, D-333): the clearfell returns f of the interception (sI = I(1 - f)), the draw unchanged;
        # thinning returns at most half that.
        ("Clearfell",    {"sI": FOREST_INTERCEPTION * (1 - clearfell_frac), "sB2": 1.0,
                          "sP": 1.0, "sPET": 1.0,         "forest_only": True}),
        ("Thinning 50%", {"sI": FOREST_INTERCEPTION * (1 - thinning_frac),  "sB2": 1.0,
                          "sP": 1.0, "sPET": 1.0,         "forest_only": True}),
        ("Broadleaf",    {"sI": None,                      "sB2": BROADLEAF_B2_SUMMER,
                          "sP": 1.0, "sPET": 1.0,         "forest_only": True}),
        ("Climate dry",  {"sI": None,                      "sB2": 1.0,
                          "sP": UKCP18_DRY_P_SUMMER,       "sPET": UKCP18_DRY_PET_SUMMER,
                          "forest_only": False}),
        ("Climate wet",  {"sI": None,                      "sB2": 1.0,
                          "sP": UKCP18_WET_P_SUMMER,       "sPET": UKCP18_WET_PET_SUMMER,
                          "forest_only": False}),
    ]:
        vals = {}
        for c in clusters:
            if c not in cluster_params:
                vals[c] = 0.0
                continue
            cp = cluster_params[c]
            is_forest = cp["forest"]

            if config["forest_only"] and not is_forest:
                vals[c] = 0.0
                continue

            # Baseline flux
            P_base = summer_P * (1 - FOREST_INTERCEPTION) if is_forest else summer_P
            flux_base = _flux(cp["b1"], cp["b2"], P_base, summer_PET,
                              cp["b3"], cp["h_disp"])

            # Scenario flux
            # 1.11.0 (D-238): the rainfall change passes through beta_1 unreduced; only a change
            # OF canopy adds raw_P·(I - sI). At sP = 1 this is summer_P·(1 - sI), as before.
            raw_P = summer_P * config["sP"]
            if is_forest:
                s_i = FOREST_INTERCEPTION if config["sI"] is None else config["sI"]
                P_scen = (summer_P * config["sP"] * (1 - s_i) if config["sP"] == 1.0   # forestry: as before, to the bit
                          else P_base + (raw_P - summer_P) + raw_P * (FOREST_INTERCEPTION - s_i))
            else:
                P_scen = raw_P

            b2_scen = cp["b2"] * config["sB2"]
            PET_scen = summer_PET * config["sPET"]
            flux_scen = _flux(cp["b1"], b2_scen, P_scen, PET_scen,
                              cp["b3"], cp["h_disp"])

            # 1.16.0 (D-349 B2): the sustained level of the forcing change, as stored water
            if not identified.get(int(c[1:]), True):
                vals[c] = float("nan")
                continue
            # The change is a SUMMER one (summer-mean P and PET, UKCP18 summer factors), so it is applied in the
            # summer months of every year and nothing else; the bar is the mean of the periodic steady state over
            # those months (the sustained summer level).
            _f12 = np.array([(flux_scen - flux_base) if m in _SUMMER_SET else 0.0 for m in range(1, 13)])
            _ss = sustained_monthly_response(cp["b3"], _f12)
            level = float(np.mean(_ss[[m - 1 for m in sorted(_SUMMER_SET)]]))
            vals[c] = round(level * cp["Sy"] * 1000, 1)

        scenarios[scenario_name] = vals

    return scenarios


def compute_scenario_bar_range(cluster_params, summer_P, summer_PET):
    """1.16.0 (D-349 B3): the Clearfell and Thinning 50% bars over the clearfell anchor range,
    {member: {"Clearfell": {cluster: mm}, "Thinning 50%": {cluster: mm}}} for member in
    clearfell_common.CLEARFELL_ANCHORS (drift free / drift fixed / drift-free DiD), each with that member's f."""
    from utils.clearfell_common import clearfell_return_fraction_range
    out = {}
    for m, f in clearfell_return_fraction_range(verbose=False).items():
        if not np.isfinite(f):
            out[m] = {k: {c: float("nan") for c in _GROUP_KEYS} for k in ("Clearfell", "Thinning 50%")}
            continue
        b = compute_scenario_bars(cluster_params, summer_P, summer_PET, clearfell_frac=f, thinning_frac=f / 2.0)
        out[m] = {k: b[k] for k in ("Clearfell", "Thinning 50%")}
    return out


def compute_scenario_bars_from_params():
    """Convenience wrapper: load all params from pipeline file, compute bars.

    Uses pipeline_params.load_params() as the single source, falling
    back to the individual loaders if the params file doesn't exist.

    Returns
    -------
    (scenario_values, cluster_params, summer_P, summer_PET) tuple
    """
    try:
        from utils.pipeline_params import load_params
        p = load_params()
        return (
            compute_scenario_bars(p["clusters"], p["summer_P"], p["summer_PET"]),   # 1.14.0 (T-209)
            p["clusters"],
            p["summer_P"],
            p["summer_PET"],
        )
    except FileNotFoundError:
        # Fallback to individual loaders (first-ever run, no params file)
        cluster_params = load_cluster_params()
        summer_P, summer_PET = load_summer_climate()
        return (
            compute_scenario_bars(cluster_params, summer_P, summer_PET),   # 1.14.0 (T-209)
            cluster_params,
            summer_P,
            summer_PET,
        )


# ============================================================================
# SUMMER-MINIMUM SCENARIO CONVERSION
# ----------------------------------------------------------------------------
# Single source of truth for the ecological scenario metric
# (`Delta_summer_min_mm`). The monthly water-equivalent flux produced by
# compute_scenario_bars() is converted to a change in summer-minimum depth in
# three steps: flux -> head (divide by specific yield) -> summer minimum
# (multiply by a per-cluster summer amplification factor). Both Script 09b
# (09b_05) and Script 21 (21_forestry_06) call these helpers so the two
# scripts report byte-identical per-cluster forestry summer-minimum values.
# Extracted from 09b_scraping_propagation._summer_scenario() (scraping_common
# v1.3.0, 2026-05-30) without behavioural change.
# ============================================================================

SCENARIO_SUMMER_MONTHS = SUMMER_MINIMUM_MONTHS
SY_SCENARIO_FALLBACK = 0.20
_GROUP_KEYS = tuple(f"C{c}" for c in _CLUSTER_LABELS)   # D-348: "C1".."C5", C5 = C3f (Western Dune, forest)
AMP_FACTOR_FALLBACK = 0.85


def summer_amplification_factors(regional_avg,
                                 clusters=_GROUP_KEYS,
                                 summer_months=SCENARIO_SUMMER_MONTHS,
                                 years=range(2006, 2026),
                                 fallback=AMP_FACTOR_FALLBACK):
    """Per-cluster summer amplification factor.

    The factor is the OLS slope of annual summer-minimum head on annual-mean
    head, regressed across years on the cluster-centroid hydrograph
    (``03_regional_averages.csv``). It expresses how a unit change in the
    annual-mean water table propagates into the summer minimum. A year
    contributes an annual mean only if it has >= 8 monthly values, and a summer
    minimum only if it has >= 2 measured Jun-Sep months. Clusters absent from
    the regional table are omitted; clusters present but with fewer than eight
    paired years are assigned ``fallback`` (0.85). Callers should resolve any
    omitted cluster with ``.get(c, fallback)``.

    Returns
    -------
    dict : {cluster: amplification_factor}
    """
    amp = {}
    for c in clusters:
        if c not in regional_avg.columns:
            continue
        annual, summin = {}, {}
        for yr in years:
            yr_data = regional_avg.loc[regional_avg.index.year == yr, c].dropna()
            if len(yr_data) >= 8:
                annual[yr] = float(yr_data.mean())
            sm_mask = ((regional_avg.index.year == yr) &
                       (regional_avg.index.month.isin(summer_months)))
            sm_data = regional_avg.loc[sm_mask, c].dropna()
            if len(sm_data) >= 2:
                summin[yr] = float(sm_data.min())
        common = sorted(set(annual) & set(summin))
        if len(common) >= 8:
            x = np.array([annual[yr] for yr in common])
            y = np.array([summin[yr] for yr in common])
            slope, _, _, _, _ = _stats.linregress(x, y)
            amp[c] = float(slope)
        else:
            amp[c] = fallback
    return amp


def scenario_cluster_sy(sy_table,
                        clusters=_GROUP_KEYS,
                        fallback=SY_SCENARIO_FALLBACK):
    """Per-cluster specific yield for scenario conversion.

    Reads ``Sy_event_median`` from the WTF table (``17_wtf_01_sy_estimates.csv``).
    For the forest groups (FOREST_CIDS: C4 and C3f) the interception-corrected variant is
    preferred where present; a key "C{n}" matches the row labelled CLUSTER_LABELS[n] (D-348: the C5 key is the
    row "C3f (Western Dune, forest)"), or a row labelled "C{n} (..." written before D-348; the base variant is used otherwise. Clusters with
    no usable row are omitted; callers should resolve them with
    ``.get(c, fallback)``.

    Parameters
    ----------
    sy_table : pandas.DataFrame or None
        Loaded WTF Sy table, or None if the file is absent (all clusters then
        omitted, i.e. every caller falls back).

    Returns
    -------
    dict : {cluster: Sy}
    """
    sy = {}
    if sy_table is None:
        return sy
    label_col = sy_table["Cluster"].astype(str)
    _forest_keys = {f"C{k}" for k in _FOREST_CIDS}
    for c in clusters:
        _lab = _CLUSTER_LABELS.get(int(c[1:]), c) if c[1:].isdigit() else c
        _is_c = label_col.str.startswith(_lab) | label_col.str.startswith(c + " ")   # D-348: C3 must not match C3f
        corr_mask = (_is_c &
                     label_col.str.contains("corrected", case=False, na=False))
        base_mask = (_is_c &
                     ~label_col.str.contains("corrected", case=False, na=False))
        row = (sy_table[corr_mask]
               if c in _forest_keys and corr_mask.any()
               else sy_table[base_mask])
        if not row.empty and pd.notna(row["Sy_event_median"].iloc[0]):
            sy[c] = float(row["Sy_event_median"].iloc[0])
    return sy


def flux_to_summer_min_mm(storage_mm, sy, amp_factor):
    """Convert a sustained change in stored water (mm w.e., compute_scenario_bars 1.16.0) to a change in
    summer-minimum depth, rounded to the nearest mm.

    summer-minimum change (mm) = round( storage / Sy * amplification factor )

    1.16.0 (D-349 B2): the input is a sustained level as stored water; before 1.16.0 it was a one-month flux, so
    the "head" it gave was one month's rate. NaN in, NaN out (a group whose beta_3 is not identified). The name
    is kept so its callers stay one search away.
    """
    if not np.isfinite(storage_mm):
        return float("nan")
    return round(storage_mm / sy * amp_factor)


def scenario_summer_min_bars(flux_bars, sy_by_cluster, amp_factors,
                             scenarios, clusters=_GROUP_KEYS,
                             sy_fallback=SY_SCENARIO_FALLBACK,
                             amp_fallback=AMP_FACTOR_FALLBACK):
    """Per-scenario, per-cluster ``Delta_summer_min_mm`` from a monthly flux table.

    Parameters
    ----------
    flux_bars : dict or pandas.DataFrame
        Either ``{scenario: {cluster: mm_per_month}}`` (as returned by
        compute_scenario_bars) or a long DataFrame with columns
        ``Scenario`` / ``Cluster`` / ``Delta_storage_sustained_mm`` (or the pre-1.16.0 ``Delta_vol_mm_per_month``).
    sy_by_cluster, amp_factors : dict
        From scenario_cluster_sy() and summer_amplification_factors().
    scenarios : iterable of str
        Scenario keys to convert (e.g. ("Clearfell", "Thinning 50%", "Broadleaf")).

    Returns
    -------
    dict : {scenario: {cluster: rounded_mm}}
    """
    if hasattr(flux_bars, "columns"):
        fb = {}
        _col = ("Delta_storage_sustained_mm" if "Delta_storage_sustained_mm" in flux_bars.columns
                else "Delta_vol_mm_per_month")   # 1.16.0: the column 09b/21 write since D-349 B2
        for _, r in flux_bars.iterrows():
            fb.setdefault(r["Scenario"], {})[r["Cluster"]] = float(r[_col])
        flux_bars = fb
    out = {}
    for s in scenarios:
        out[s] = {}
        for c in clusters:
            vol = flux_bars.get(s, {}).get(c, 0.0)
            out[s][c] = flux_to_summer_min_mm(
                vol,
                sy_by_cluster.get(c, sy_fallback),
                amp_factors.get(c, amp_fallback),
            )
    return out
