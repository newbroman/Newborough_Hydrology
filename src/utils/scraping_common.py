"""
utils/scraping_common.py
========================
Shared constants, well lists, and helpers for the Script 09 scraping
analysis suite (09a–09d).

Analogous to clearfell_common.py for the Script 10 suite.  All scraping-
specific configuration lives here so that individual modules can stay
focused on analysis.

Constants
---------
SCRAPING_DATE       April 2015 — ground scraping at CEH36
INTERVENTION_DATE   December 2017 — pine clearfell (shared with clearfell)
SCRAPING_DATE_2     October 2023 — second (re-)scraping event
FELLING_YEAR        2017

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

__version__ = "1.1.0"  # 2026-05-08 — B2 multiplier routed through clearfell_common

import pandas as pd

# ============================================================================
# INTERVENTION DATES
# ============================================================================
SCRAPING_DATE    = pd.Timestamp("2015-04-01")
INTERVENTION_DATE = pd.Timestamp("2017-12-01")   # clearfell
SCRAPING_DATE_2  = pd.Timestamp("2023-10-01")

FELLING_YEAR = INTERVENTION_DATE.year   # 2017

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

MPL_DEFAULTS = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
}


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
    """Load well and climate data for the scraping analysis."""
    from utils.paths import INT_WELLS_CLEAN, INT_WELLS_EXTENDED, INT_CLIMATE

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

    return wells, climate


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
    import numpy as np
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
