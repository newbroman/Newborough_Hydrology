"""
utils/clearfell_common.py
=========================
Shared module for the Script 10 clearfell analysis suite (10a–10g).

Provides:
  - Well tier definitions (impact, edge, forest control, climate control)
  - Intervention dates
  - Spatial constants and distance functions
  - Data loading (wells, climate, master coefficients)
  - BACI displacement and covariate computation
  - Summer minimum extraction

All sub-scripts import from here to ensure consistent well lists,
dates, and data handling.  No analysis is performed — this module
only prepares data.

Usage
-----
    from utils.clearfell_common import (
        load_clearfell_data, INTERVENTION_DATE, SCRAPING_DATE,
        IMPACT_WELLS, EDGE_WELLS, FOREST_CONTROL_WELLS,
        CLIMATE_CONTROL_WELLS, ALL_NETWORK_WELLS,
        compute_baci_displacement, compute_cwb,
        distance_weighted_scraping, annual_summer_minimum,
    )
"""

import warnings
import numpy as np
import pandas as pd
from pathlib import Path

from utils.paths import (
    INT_WELLS_CLEAN, INT_WELLS_EXTENDED, INT_CLIMATE,
    INT_MASTER_DATA, DATA_WELL_ELEVATIONS,
    OUT_10E_COEFF_SHIFTS,
    make_all_dirs,
)
from utils.data_utils import clean_well_series
from utils.config import DRAINAGE_DATUM

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

ALL_NETWORK_WELLS = (
    IMPACT_WELLS + EDGE_WELLS +
    FOREST_CONTROL_WELLS + COASTAL_CONTROL_WELLS +
    CLIMATE_CONTROL_WELLS
)

# Convenience grouping for iteration
TIERS = {
    'Impact':        IMPACT_WELLS,
    'Edge':          EDGE_WELLS,
    'Forest Ctrl':   FOREST_CONTROL_WELLS,
    'Coastal Ctrl':  COASTAL_CONTROL_WELLS,
    'Climate Ctrl':  CLIMATE_CONTROL_WELLS,
}

# ============================================================================
# INTERVENTION DATES
# ============================================================================

INTERVENTION_DATE = pd.Timestamp('2017-12-01')   # December 2017 clearfell
SCRAPING_DATE     = pd.Timestamp('2015-04-01')   # April 2015 scraping
SCRAPING_DATE_2   = pd.Timestamp('2023-10-01')   # October 2023 re-scraping

FELLING_YEAR = INTERVENTION_DATE.year  # 2017

# ============================================================================
# SPATIAL CONSTANTS
# ============================================================================

# CEH36 scraping site
CEH36_EASTING  = 241161.0
CEH36_NORTHING = 363306.0

# Felling compartment centroid (mean of FE1-4 + WMC3)
FELL_CENTROID_EASTING  = 241210.0
FELL_CENTROID_NORTHING = 363607.0

# Distance-weighted scraping decay length (metres)
SCRAPING_DECAY_LAMBDA = 300.0

# Summer months (1-indexed)
SUMMER_MONTHS = [6, 7, 8, 9]

# ============================================================================
# DATA LOADING
# ============================================================================

def load_clearfell_data():
    """Load and validate wells, climate, and master data for clearfell analysis.

    Returns
    -------
    wells : pd.DataFrame
        Monthly well depth timeseries (negative = below ground).
        Columns are lowercase well names. Merged from clean + extended.
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

    for col in wells.columns:
        wells[col] = clean_well_series(wells[col])

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

    return wells, climate, master, well_locations, valid_tiers


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

def compute_control_centroid(wells, control_list):
    """Monthly mean of control wells.

    Parameters
    ----------
    wells : pd.DataFrame
    control_list : list of str

    Returns
    -------
    pd.Series with DatetimeIndex
    """
    available = [w for w in control_list if w in wells.columns]
    if not available:
        raise ValueError("No control wells found in data")
    return wells[available].mean(axis=1)


def compute_baci_displacement(wells, target_list, control_list):
    """Compute BACI displacement timeseries.

    Returns target_centroid − control_centroid, dropping NaN rows.
    """
    target_mean = wells[[w for w in target_list if w in wells.columns]].mean(axis=1)
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
# SUMMER MINIMA
# ============================================================================

def annual_summer_minimum(series, start_year=2006, end_year=2026):
    """Compute annual summer minimum (Jun–Sep) depth for a well.

    Parameters
    ----------
    series : pd.Series with DatetimeIndex (depth below ground, negative)
    start_year, end_year : int

    Returns
    -------
    dict : {year: float} — minimum (most negative) depth in Jun–Sep
    """
    mins = {}
    for yr in range(start_year, end_year + 1):
        mask = (series.index.year == yr) & (series.index.month.isin(SUMMER_MONTHS))
        vals = series[mask].dropna()
        if len(vals) >= 2:
            mins[yr] = float(vals.min())
    return mins


def forest_control_centroid_summer_min(wells, forest_wells,
                                        start_year=2006, end_year=2026,
                                        min_wells=2):
    """Compute forest control centroid annual summer minimum.

    For each year, averages the summer minimum across all forest control
    wells with data, requiring at least min_wells.

    Returns
    -------
    dict : {year: float}
    """
    per_well = {}
    for w in forest_wells:
        if w in wells.columns:
            per_well[w] = annual_summer_minimum(wells[w], start_year, end_year)

    all_years = set()
    for wm in per_well.values():
        all_years |= set(wm.keys())

    centroid = {}
    for yr in sorted(all_years):
        vals = [per_well[w][yr] for w in per_well if yr in per_well[w]]
        if len(vals) >= min_wells:
            centroid[yr] = np.mean(vals)

    return centroid


# ============================================================================
# REPORTING UTILITIES
# ============================================================================

class ReportNumbers:
    """Accumulator for report numbers CSV export."""

    def __init__(self):
        self.rows = []

    def add(self, parameter, value, unit="m", well="", era="", note=""):
        self.rows.append({
            "Parameter": parameter,
            "Well": well,
            "Era": era,
            "Value": round(value, 4) if pd.notna(value) and isinstance(value, (int, float)) else value,
            "Unit": unit,
            "Note": note,
        })

    def to_dataframe(self):
        return pd.DataFrame(self.rows)

    def save(self, path):
        df = self.to_dataframe()
        df.to_csv(path, index=False)
        return len(self.rows)


# ============================================================================
# TIER COLOURS (for consistent plotting across sub-scripts)
# ============================================================================

TIER_COLOURS = {
    'Impact':        '#D73027',
    'Edge':          '#F46D43',
    'Forest Ctrl':   '#4DAC26',
    'Coastal Ctrl':  '#8B6914',  # brown — C5 Coastal Forest
    'Climate Ctrl':  '#4575B4',
}

WELL_MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X', 'h', '<', '>']


# ============================================================================
# PRINT UTILITIES
# ============================================================================

def print_network_summary(valid_tiers):
    """Print the 5-tier network summary to console."""
    total = sum(len(v) for v in valid_tiers.values())
    print(f"\n  Network: {total} wells (5-tier design)")
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
    For each BACI tier, compute the mean ratio (b2_after / b2_before) across
    all wells in that tier.  The clearfell multiplier is the BACI-corrected
    Edge-tier ratio:

        multiplier = Edge_ratio − Climate_Ctrl_ratio + 1.0

    This subtracts the background climate drift (measured at Climate Ctrl
    wells that share the same post-2017 period but were unaffected by
    felling) from the Edge-tier signal, which showed the strongest
    clearfell-attributable β₂ response.  Using the Edge tier rather than
    the Impact tier is a conservative upper bound: the Impact well (WMC3)
    shows only ×1.04, partly because felling removes the canopy that
    amplified β₂ in the first place, while Edge wells retain canopy but
    receive lateral moisture from the cleared compartment.

    The thinning multiplier is defined as half the clearfell perturbation:

        thinning = 1.0 + (clearfell − 1.0) / 2.0

    Returns
    -------
    clearfell_mult : float
        Multiplier for full clearfell (expected ~1.10 with current data).
    thinning_mult : float
        Multiplier for 50% thinning (expected ~1.05 with current data).
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
            print(f"           Using fallback β₂ multipliers")
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
            print(f"  WARNING: Missing Edge or Climate Ctrl tier ratios "
                  f"— using fallback β₂ multipliers")
        return _FALLBACK_CLEARFELL_B2, _FALLBACK_THINNING_B2, tier_ratios

    # BACI-corrected Edge ratio: subtract climate drift, re-centre on 1.0
    edge_ratio   = tier_ratios['Edge']
    climate_drift = tier_ratios['Climate Ctrl']
    clearfell_mult = edge_ratio - climate_drift + 1.0
    thinning_mult  = 1.0 + (clearfell_mult - 1.0) / 2.0

    if verbose:
        print(f"  β₂ multiplier (BACI-corrected Edge ratio):")
        for tn, tr in tier_ratios.items():
            print(f"    {tn:15s}: {tr:.4f}")
        print(f"    Edge − Climate Ctrl + 1 = "
              f"{edge_ratio:.4f} − {climate_drift:.4f} + 1.0 = "
              f"{clearfell_mult:.4f}")
        print(f"    Clearfell: {clearfell_mult:.4f}  "
              f"Thinning: {thinning_mult:.4f}")

    return clearfell_mult, thinning_mult, tier_ratios
