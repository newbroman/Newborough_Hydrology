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

__version__ = "1.0.0"  # Hollingham (2026) — 2026-05-04

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
# C3 wells with long records, no intervention confound.
# NW8/NW8B excluded (NW8 damaged Jun 2015; NW8B only 2.5 yr baseline).
CLIMATE_CONTROLS = ["ceh9", "nw7", "nw6", "nw5", "wmc2"]

# --- Donor pool for synthetic control ---
# Long-record wells outside the scraping footprint, excluding CEH36
# (target), CEH4 (raw BACI control), and felling-zone wells.
# CEH23 replaced by CEH11 (C1, complete record — CEH23 has 17-mo gap).
# CEH28 replaced by CEH24 (C2, complete record — CEH28 has 20-mo gap).
DONOR_CANDIDATES = [
    "ceh1", "ceh2", "ceh5", "ceh6", "ceh9", "ceh11", "ceh16",
    "ceh17", "ceh19", "ceh22", "ceh24",
]

# --- Summer months (Jun–Sep) for ecological threshold analysis ---
SUMMER_MONTHS = [6, 7, 8, 9]

# ============================================================================
# ERA DEFINITIONS
# ============================================================================
# Each well has a dict of {era_name: (start_timestamp, end_timestamp)}.
# start is inclusive, end is exclusive.  None means unbounded.

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

# Matplotlib publication defaults
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
    """Filter a pandas Series to a date range [start, end).

    Parameters
    ----------
    series : pd.Series with DatetimeIndex
    start : pd.Timestamp or None (unbounded left)
    end : pd.Timestamp or None (unbounded right)

    Returns
    -------
    pd.Series — filtered view
    """
    mask = pd.Series(True, index=series.index)
    if start is not None:
        mask &= series.index >= start
    if end is not None:
        mask &= series.index < end
    return series[mask]


def load_scraping_data():
    """Load well and climate data for the scraping analysis.

    Returns
    -------
    wells : pd.DataFrame — merged clean + extended well time series
    climate : pd.DataFrame — monthly climate (P_m, PET, etc.)

    Reads from Script 01 pipeline intermediates.
    """
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
