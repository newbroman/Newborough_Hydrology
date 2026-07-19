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
INTERVENTION_DATE     December 2017 — pine clearfell (shared with clearfell)
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

__version__ = "1.6.0"  # 2026-07-19 — MPL_DEFAULTS relocated to render_utils.py;
                        # re-exported here for backwards compatibility
                        # (09a/09c/09d/09e/09f unchanged). No other changes.
# 1.5.0  2026-07-02 — added load_annual_climate() companion to
                        # load_summer_climate(); used by Script 09d v3.4.0 to
                        # evaluate scenario bars under annual-mean forcing
                        # (Figure 26) alongside summer forcing (Figure 27).
                        # No change to existing helpers.
# 1.4.0  2026-05-30 — Summer-minimum scenario conversion
                        # (monthly flux -> head /Sy -> summer-min x amplification)
                        # extracted from 09b into shared helpers:
                        # summer_amplification_factors(), scenario_cluster_sy(),
                        # flux_to_summer_min_mm(), scenario_summer_min_bars().
                        # Single source of truth for the Delta_summer_min_mm metric;
                        # 09b_05 and 21_forestry_06 both call these (byte-identical
                        # forestry rows). No change to any prior behaviour.
# 1.3.0 — 2026-05-19 — Defect E fix integration: load_scraping_data
                        # now returns (wells, wells_provenance, climate) and reads
                        # the per-cell provenance file emitted by Script 01 v1.2.0
                        # alongside 01_wells_clean.csv. Call sites in 09a, 09c,
                        # 09d, 09e updated to accept the new third return; 09c
                        # forwards provenance to annual_summer_minimum so the
                        # phantom 2019 summer minima for NW6/NW7 (Climate
                        # controls) drop out cleanly. The double-clean issue
                        # (E.2) does not exist in this loader — there is no
                        # clean_well_series call here, only a CSV read.
# 1.2.0 — 2026-05-16 — REGIONAL_MEAN_START codifies the fixed-composition
#         window for the regional-mean control (consistency with the
#         clearfell-suite record-length-balance principle, but smaller in
#         scope because the paired-BACI design here already self-equalises
#         within each pair).
# 1.1.0 — 2026-05-08 — B2 multiplier routed through clearfell_common.
# 1.0.x — Initial scraping-suite shared module.

import pandas as pd
import numpy as np
from scipy import stats as _stats

# ============================================================================
# INTERVENTION DATES
# ============================================================================
SCRAPING_DATE    = pd.Timestamp("2015-04-01")
INTERVENTION_DATE = pd.Timestamp("2017-12-01")   # clearfell
SCRAPING_DATE_2  = pd.Timestamp("2023-10-01")

FELLING_YEAR = INTERVENTION_DATE.year   # 2017

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
# Baseline-era mean shifts by ~36 mm in consequence.  CEH22 paired against
# regional mean is unchanged (CEH22 starts 2010-03, already inside the
# fixed-composition window).
REGIONAL_MEAN_START = pd.Timestamp("2009-02-01")

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
SUMMER_MONTHS = [6, 7, 8, 9]

# ============================================================================
# ERA DEFINITIONS
# ============================================================================
WELL_ERAS = {
    "ceh36": {
        "1_Baseline":       (None, SCRAPING_DATE),
        "2_Pure_Scraping":  (SCRAPING_DATE, INTERVENTION_DATE),
        "3_Felling_Pulse":  (INTERVENTION_DATE, None),
    },
    "ceh4": {
        "1_Baseline":       (None, SCRAPING_DATE),
        "2_Pure_Scraping":  (SCRAPING_DATE, INTERVENTION_DATE),
        "3_Felling_Pulse":  (INTERVENTION_DATE, None),
    },
    "ceh18": {
        "1_Baseline":       (None, INTERVENTION_DATE),
        "2_Felling_Pulse":  (INTERVENTION_DATE, SCRAPING_DATE_2),
        "3_After_Scraping": (SCRAPING_DATE_2, None),
    },
    "ceh21": {
        "1_Baseline":        (None, INTERVENTION_DATE),
        "2_Coastal_Drawdown": (INTERVENTION_DATE, SCRAPING_DATE_2),
        "3_After_Scraping":  (SCRAPING_DATE_2, None),
    },
    "ceh22": {
        "1_Baseline":        (None, INTERVENTION_DATE),
        "2_Coastal_Drawdown": (INTERVENTION_DATE, SCRAPING_DATE_2),
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
      - Sy from Script 17 WTF per-well estimates (cluster median)
      - h_disp from Script 01 wells + DRAINAGE_DATUM
      - forest flag (clusters 4 and 5)

    Returns
    -------
    dict : {cname: {b1, b2, b3, Sy, h_disp, forest}}
    """
    from utils.paths import (
        OUT_03_MECHANISTIC_TABLE, INT_MASTER_DATA,
        INT_WTF_WELL_SY, INT_WELLS_CLEAN,
    )
    from utils.config import DRAINAGE_DATUM

    coeff = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
    sy_df = pd.read_csv(INT_WTF_WELL_SY)
    sy_by_cluster = sy_df.groupby("Cluster")["Sy_median"].median()

    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells.columns = wells.columns.str.lower().str.replace(" ", "")
    master = pd.read_csv(INT_MASTER_DATA)
    master["match"] = master["Name_Original"].str.lower().str.replace(" ", "")

    params = {}
    for _, row in coeff.iterrows():
        cl = int(row["Cluster"])
        cname = f"C{cl}"

        cl_wells = master[master["Cluster"] == cl]["match"].tolist()
        available = [w for w in cl_wells if w in wells.columns]
        mean_depth = wells[available].mean().mean() if available else -0.5
        h_disp = DRAINAGE_DATUM + mean_depth

        params[cname] = {
            "b1": float(row["beta_1_recharge"]),
            "b2": float(row["beta_2_atmospheric_draw"]),
            "b3": float(row["beta_3_drainage"]),
            "Sy": float(sy_by_cluster.get(cl, 0.25)),
            "h_disp": h_disp,
            "forest": cl in (4, 5),
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

def compute_scenario_bars(cluster_params, summer_P, summer_PET,
                          clearfell_b2_mult=None, thinning_b2_mult=None):
    """Compute per-cluster volumetric scenario bars (mm w.e./month).

    Uses the Option 3 seasonal perturbation formulation:
        Δh(m) = β₁·ΔP − Δβ₂·PET
    with forestry interception and UKCP18 climate scaling.

    Parameters
    ----------
    cluster_params : dict
        {cname: {b1, b2, b3, Sy, h_disp, forest}} from pipeline outputs.
    summer_P : float
        Mean summer rainfall (m/month) from climate data.
    summer_PET : float
        Mean summer PET (m/month) from climate data.
    clearfell_b2_mult : float or None
        If None, loaded dynamically from clearfell_common.
    thinning_b2_mult : float or None
        If None, loaded dynamically from clearfell_common.

    Returns
    -------
    dict : {scenario_name: {cluster: value_mm_per_month}}
    """
    from utils.config import (
        FOREST_INTERCEPTION, BROADLEAF_INTERCEPTION,
        BROADLEAF_B2_SUMMER,
        UKCP18_DRY_P_SUMMER, UKCP18_DRY_PET_SUMMER,
        UKCP18_WET_P_SUMMER, UKCP18_WET_PET_SUMMER,
    )

    # β₂ multipliers: use passed values, or load from clearfell_common
    if clearfell_b2_mult is None or thinning_b2_mult is None:
        from utils.clearfell_common import load_clearfell_b2_multiplier
        _cf, _thin, _ = load_clearfell_b2_multiplier()
        if clearfell_b2_mult is None:
            clearfell_b2_mult = _cf
        if thinning_b2_mult is None:
            thinning_b2_mult = _thin

    clusters = ["C1", "C2", "C3", "C4", "C5"]
    scenarios = {}

    def _flux(b1, b2, P_eff, PET, b3, h_disp):
        return b1 * P_eff - b2 * PET - b3 * h_disp

    for scenario_name, config in [
        ("Clearfell",    {"sI": 0.0,                       "sB2": clearfell_b2_mult,
                          "sP": 1.0, "sPET": 1.0,         "forest_only": True}),
        ("Thinning 50%", {"sI": FOREST_INTERCEPTION * 0.5, "sB2": thinning_b2_mult,
                          "sP": 1.0, "sPET": 1.0,         "forest_only": True}),
        ("Broadleaf",    {"sI": BROADLEAF_INTERCEPTION,    "sB2": BROADLEAF_B2_SUMMER,
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
            if config["sI"] is not None:
                P_scen = summer_P * config["sP"] * (1 - config["sI"])
            else:
                raw_P = summer_P * config["sP"]
                P_scen = raw_P * (1 - FOREST_INTERCEPTION) if is_forest else raw_P

            b2_scen = cp["b2"] * config["sB2"]
            PET_scen = summer_PET * config["sPET"]
            flux_scen = _flux(cp["b1"], b2_scen, P_scen, PET_scen,
                              cp["b3"], cp["h_disp"])

            vals[c] = round((flux_scen - flux_base) * cp["Sy"] * 1000, 1)

        scenarios[scenario_name] = vals

    return scenarios


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
            compute_scenario_bars(
                p["clusters"], p["summer_P"], p["summer_PET"],
                clearfell_b2_mult=p["clearfell_b2_mult"],
                thinning_b2_mult=p["thinning_b2_mult"],
            ),
            p["clusters"],
            p["summer_P"],
            p["summer_PET"],
        )
    except FileNotFoundError:
        # Fallback to individual loaders (first-ever run, no params file)
        cluster_params = load_cluster_params()
        summer_P, summer_PET = load_summer_climate()
        return (
            compute_scenario_bars(cluster_params, summer_P, summer_PET),
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

SCENARIO_SUMMER_MONTHS = (6, 7, 8, 9)
SY_SCENARIO_FALLBACK = 0.20
AMP_FACTOR_FALLBACK = 0.85


def summer_amplification_factors(regional_avg,
                                 clusters=("C1", "C2", "C3", "C4", "C5"),
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
                        clusters=("C1", "C2", "C3", "C4", "C5"),
                        fallback=SY_SCENARIO_FALLBACK):
    """Per-cluster specific yield for scenario conversion.

    Reads ``Sy_event_median`` from the WTF table (``17_wtf_01_sy_estimates.csv``).
    For the forested clusters C4 and C5 the interception-corrected variant is
    preferred where present; the base variant is used otherwise. Clusters with
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
    for c in clusters:
        corr_mask = (label_col.str.startswith(c) &
                     label_col.str.contains("corrected", case=False, na=False))
        base_mask = (label_col.str.startswith(c) &
                     ~label_col.str.contains("corrected", case=False, na=False))
        row = (sy_table[corr_mask]
               if c in ("C4", "C5") and corr_mask.any()
               else sy_table[base_mask])
        if not row.empty and pd.notna(row["Sy_event_median"].iloc[0]):
            sy[c] = float(row["Sy_event_median"].iloc[0])
    return sy


def flux_to_summer_min_mm(flux_mm_per_month, sy, amp_factor):
    """Convert a monthly water-equivalent flux to a change in summer-minimum
    depth, rounded to the nearest mm.

    summer-minimum change (mm) = round( flux / Sy * amplification factor )

    This is the single conversion used for the ``Delta_summer_min_mm`` scenario
    metric in 09b_05 and 21_forestry_06.
    """
    return round(flux_mm_per_month / sy * amp_factor)


def scenario_summer_min_bars(flux_bars, sy_by_cluster, amp_factors,
                             scenarios, clusters=("C1", "C2", "C3", "C4", "C5"),
                             sy_fallback=SY_SCENARIO_FALLBACK,
                             amp_fallback=AMP_FACTOR_FALLBACK):
    """Per-scenario, per-cluster ``Delta_summer_min_mm`` from a monthly flux table.

    Parameters
    ----------
    flux_bars : dict or pandas.DataFrame
        Either ``{scenario: {cluster: mm_per_month}}`` (as returned by
        compute_scenario_bars) or a long DataFrame with columns
        ``Scenario`` / ``Cluster`` / ``Delta_vol_mm_per_month``.
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
        for _, r in flux_bars.iterrows():
            fb.setdefault(r["Scenario"], {})[r["Cluster"]] = float(
                r["Delta_vol_mm_per_month"])
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
