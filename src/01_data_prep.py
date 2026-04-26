"""
01_data_prep.py
Purpose: Prepares raw groundwater, location, and climate data, producing cleaned
outputs and reference/extended network splits for downstream scripts.

Outputs (intermediate — outputs/ root):
    01_locations.csv
    01_climate.csv
    01_wells_clean.csv
    01_wells_reference.csv
    01_wells_extended.csv

Requirements:
    pandas, numpy
"""

__version__ = "1.0.0"  # Hollingham (2026) — last revised 2026-04-10

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
del _sys, _os

import pandas as pd
import numpy as np

from utils.paths import (
    make_all_dirs,
    DATA_WELLS_RAW, DATA_LOCATIONS_RAW, DATA_CLIMATE_RAW,
    DATA_DIR,
    INT_LOCATIONS, INT_CLIMATE, INT_WELLS_CLEAN, INT_WELLS_CLEAN_MAOD,
    INT_WELLS_REFERENCE, INT_WELLS_EXTENDED,
    INT_WELL_ELEVATIONS,
)
from utils.data_utils import normalize_well_name, parse_met_date, clean_well_series
from utils.config import REFERENCE_CUTOFF_DATE

# Consolidated well elevation / upstand reference file (data directory).
_WELL_ELEV_FILE = DATA_DIR / "Well_locations_height.csv"

MIN_MONTHS_THRESH   = 100
RECENCY_DATE        = pd.Timestamp(REFERENCE_CUTOFF_DATE)
MIN_EXTENDED_MONTHS = 24

# ──────────────────────────────────────────────────────────────────────────────
# REFERENCE NETWORK WHITELIST
#
# The cluster analysis (Script 02) and the mechanistic SSM fits (Script 03)
# assume each cluster represents a coherent hydrogeological population whose
# water-level response to climate forcing is stationary over the monitoring
# period. Wells that have experienced a non-stationary regime change — for
# instance, clearfelling which removes the canopy interception loss and
# initiates an ongoing upward drift in the water table — violate this
# assumption. Their single-β SSM fit does not describe any real physical
# state; it averages over a pre-transition regime, a transition period,
# and an incomplete post-transition equilibrium.
#
# This whitelist pins the reference network to the 69 wells that were
# clustered and modelled in the published analysis (Hollingham 2026,
# Table 2). It excludes:
#
#   - The five "FE" and "LIS" wells (FE1, FE2, FE3, FE4, LIS1) from the
#     clearfell management footprint. These remain available in the
#     extended-network analysis (Script 06) and form the treatment arm
#     of the clearfell BACI analysis (Script 10 / Section 4.6).
#
#   - The Llyn Rhos well, which reads a lake surface rather than a water
#     table. An SSM fit treating Llyn Rhos as a water-table response is
#     physical nonsense; it is excluded from the reference network on
#     the same "not in a stationary single-β regime" grounds as FE/LIS.
#     Llyn Rhos remains available through the extended-network file for
#     lake-level analysis where needed.
#
#   - CEH3 and CEH22, which Ward's hierarchical clustering consistently
#     identifies as singleton outliers. Their correlation structure does
#     not align with any of the behavioural groups in the rest of the
#     network — a signature consistent with tidal-signal contamination
#     on top of the climate-forcing response the SSM is designed to
#     capture. Both wells are low-elevation and coastal (ground elevation
#     3.3 m at CEH22; CEH3 shows the clearest tidal signature on
#     inspection). Including them distorts the Ward's tree at lower k
#     values: CEH3 suppresses the Lake/Dune split at k=4 on a 68-well
#     network, and CEH22 is a persistent singleton at k=5..9 on a 67-
#     well network. Like FE/LIS and Llyn Rhos, CEH3 and CEH22 remain in
#     the extended network for per-well analyses.
#
#   - Any other wells that meet the automatic record-length criterion
#     (>=100 monthly observations, record extending to 2026-02) but were
#     not part of the original 2026 reference network. Those wells may
#     have joined the network more recently and are available in the
#     extended-network analyses.
#
# To restore the fully automatic reference-network selection (i.e., let
# any well meeting MIN_MONTHS_THRESH and RECENCY_DATE into the reference
# network), set REFERENCE_NETWORK_WHITELIST = None.
# ──────────────────────────────────────────────────────────────────────────────
REFERENCE_NETWORK_WHITELIST = frozenset({
    "ceh1",  "ceh10", "ceh11", "ceh13", "ceh14", "ceh16", "ceh17", "ceh18",
    "ceh19", "ceh2",  "ceh20", "ceh21", "ceh23", "ceh24", "ceh25",
    "ceh26", "ceh27", "ceh28", "ceh30", "ceh31", "ceh32", "ceh33",
    "ceh34", "ceh36", "ceh39", "ceh4",  "ceh40", "ceh41", "ceh42", "ceh5",
    "ceh6",  "ceh9",  "d10",   "d15",   "d17",   "d25",   "d38",   "d41",
    "d43",   "d44",   "d5",    "d6",    "d7",    "d8",    "d9",    "l7",
    "nw1",   "nw10",  "nw11",  "nw13",  "nw2",   "nw3",   "nw4",
    "nw4b",  "nw5",   "nw6",   "nw7",   "nw9",   "t41a",  "t41b",  "t41c",
    "t41d",  "wmc1",  "wmc2",  "wmc3",  "wmc4",
})

# RAF Valley, Anglesey — site latitude for Thornthwaite day-length correction
RAF_VALLEY_LAT_DEG  = 53.25


def thornthwaite_pet_m(t_mean: pd.Series, lat_deg: float = RAF_VALLEY_LAT_DEG) -> pd.Series:
    """
    Compute monthly PET in metres using the Thornthwaite (1948) method with the
    Thornthwaite & Mather (1955) day-length and month-length correction factor.

    The formula is:
        PET_unadj (mm) = 16 * (10 * T / I) ^ alpha     [for 0 < T < 26.5 °C]
        alpha = 6.75e-7 * I^3 - 7.71e-5 * I^2 + 1.792e-2 * I + 0.49239
        I = sum of monthly heat-index contributions i = (T/5)^1.514 over 12 months
        K = (N/12) * (NDM/30)   [day-length correction; N = mean photoperiod hours]
        PET_adj (m) = PET_unadj * K / 1000

    For T <= 0, PET = 0. For T >= 26.5, the Camargo et al. high-temperature
    linearisation is applied: PET = -415.85 + 32.24*T - 0.43*T^2.

    Parameters
    ----------
    t_mean  : pd.Series of mean monthly temperature (°C) with DatetimeIndex
              at month-start timestamps. NaN months are handled gracefully.
    lat_deg : site latitude in decimal degrees north (default 53.25, RAF Valley).

    Returns
    -------
    pd.Series of PET in metres per month, same index as t_mean.
    NaN is preserved where t_mean is NaN.

    References
    ----------
    Thornthwaite, C.W. (1948). An approach toward a rational classification of
        climate. Geographical Review, 38(1), 55-94.
    Thornthwaite, C.W. & Mather, J.R. (1955). The water balance. Publications in
        Climatology, 8(1), 1-104.
    """
    temps_pos = t_mean.clip(lower=0).fillna(0)

    # Annual heat index I: sum of 12 monthly contributions within each calendar year.
    # Months with missing temperature contribute zero to I (conservative).
    i_monthly = (temps_pos / 5) ** 1.514
    i_annual  = i_monthly.groupby(t_mean.index.year).sum()
    I = pd.Series(t_mean.index.year, index=t_mean.index).map(i_annual)
    I = I.replace(0, np.nan)  # guard against all-zero temperature years

    alpha = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.792e-2 * I) + 0.49239

    # Unadjusted PET (mm, standard 30-day 12-hour basis)
    pet_unadj = np.where(
        temps_pos <= 0, 0.0,
        np.where(
            temps_pos < 26.5,
            16.0 * (10.0 * temps_pos / I) ** alpha,
            -415.85 + 32.24 * temps_pos - 0.43 * temps_pos ** 2,
        ),
    )

    # Day-length correction factor K = (N/12) * (NDM/30)
    lat_rad = np.radians(lat_deg)
    mid_doy = np.array([15, 46, 75, 106, 136, 167, 197, 228, 259, 289, 320, 350])
    decl    = np.radians(23.45 * np.sin(np.radians(360 * (mid_doy - 80) / 365)))
    cos_ha  = -np.tan(lat_rad) * np.tan(decl[t_mean.index.month - 1])
    N       = (24 / np.pi) * np.arccos(np.clip(cos_ha, -1, 1))
    K       = (N / 12) * (t_mean.index.days_in_month / 30)

    pet_m = pd.Series(pet_unadj * K / 1000, index=t_mean.index, name="PET")

    # Restore NaN where original temperature was missing
    pet_m[t_mean.isna()] = np.nan

    return pet_m

if __name__ == "__main__":
    make_all_dirs()
    print("Starting Data Preparation Pipeline...")

    locs_raw  = pd.read_csv(DATA_LOCATIONS_RAW)
    wells_raw = pd.read_csv(DATA_WELLS_RAW, header=1)

    # Sanity check
    print("\n" + "=" * 40)
    print("  DATA SANITY CHECK: Metadata vs. Time-Series")
    print("=" * 40)
    locs_raw.columns   = locs_raw.columns.str.strip()
    loc_names          = set(locs_raw["Name"].apply(normalize_well_name))
    well_names_in_data = set(wells_raw.iloc[:, 0].dropna().apply(normalize_well_name))
    missing_in_data    = loc_names - well_names_in_data
    missing_in_locs    = well_names_in_data - loc_names
    if not missing_in_data and not missing_in_locs:
        print("  ✅ SUCCESS: All wells match perfectly between files.")
    else:
        if missing_in_data:
            print(f"  [WARNING] {len(missing_in_data)} wells have locations but no time-series data.")
        if missing_in_locs:
            print(f"  [WARNING] {len(missing_in_locs)} wells have time-series but no location metadata.")
    print("=" * 40 + "\n")

    # Locations
    locs_raw["Match_ID"] = locs_raw["Name"].apply(normalize_well_name)
    locs_raw.dropna(subset=["E", "N"]).to_csv(INT_LOCATIONS, index=False)

    # Climate
    climate = pd.read_csv(DATA_CLIMATE_RAW)
    climate["Date"] = climate["Unnamed: 0"].apply(parse_met_date)
    climate = climate.set_index("Date")
    climate["P_m"] = (
        pd.to_numeric(climate["Rain (mm)"].replace("---", "0"), errors="coerce")
        .fillna(0) / 1000
    )
    t_max_col = "Max Temp ©" if "Max Temp ©" in climate.columns else "Max Temp (C)"
    t_mean = (
        pd.to_numeric(climate[t_max_col], errors="coerce")
        + pd.to_numeric(climate["Min Temp (C)"], errors="coerce")
    ) / 2
    climate["PET"] = thornthwaite_pet_m(t_mean)
    climate[["P_m", "PET"]].to_csv(INT_CLIMATE)

    # Wells
    wells = wells_raw.set_index(wells_raw.columns[0]).transpose()

    # ── Month bucketing: assign each reading to its NEAREST month-start ──────
    # The earlier pipeline version used `to_period("M").to_timestamp()` which
    # truncates every reading to the start of its own calendar month. That
    # creates phantom "missing" months when fieldwork straddled month-ends:
    # e.g. readings on 2011-01-30 and 2011-03-01 would bucket as Jan and Mar,
    # leaving February apparently empty even though the field interval was
    # 30 days. Nearest-month assignment rounds readings on day 16 or later
    # forward to the following month-start, eliminating the artefact while
    # preserving all genuine extended gaps (Jul 2005, Jan 2023).
    d = pd.to_datetime(wells.index, dayfirst=True, errors="coerce")
    month_start = d.to_period("M").to_timestamp()
    next_start = month_start + pd.DateOffset(months=1)
    dist_prev = np.abs((d - month_start).total_seconds())
    dist_next = np.abs((d - next_start).total_seconds())
    wells.index = np.where(dist_next < dist_prev, next_start, month_start)
    wells = wells.apply(pd.to_numeric, errors="coerce").groupby(level=0).mean()
    if "NW8" in wells.columns and "NW8b" in wells.columns:
        wells["NW8"] = wells["NW8b"].combine_first(wells["NW8"])
        wells.drop(columns=["NW8b"], inplace=True)
    for col in wells.columns:
        wells[col] = clean_well_series(wells[col])

    wells_clean = wells.dropna(axis=1, thresh=MIN_MONTHS_THRESH)
    wells_clean.to_csv(INT_WELLS_CLEAN)

    reference_wells, extended_wells = [], []
    demoted_wells = []   # wells that meet auto-criteria but are not whitelisted
    for col in wells.columns:
        series = wells[col].dropna()
        if series.empty:
            continue
        meets_reference_criteria = (
            len(series) >= MIN_MONTHS_THRESH
            and series.index.max() >= RECENCY_DATE
        )
        if meets_reference_criteria:
            col_norm = normalize_well_name(col)
            if REFERENCE_NETWORK_WHITELIST is None or col_norm in REFERENCE_NETWORK_WHITELIST:
                reference_wells.append(col)
            else:
                demoted_wells.append(col)
                if len(series) >= MIN_EXTENDED_MONTHS:
                    extended_wells.append(col)
        elif len(series) >= MIN_EXTENDED_MONTHS:
            extended_wells.append(col)

    wells[reference_wells].to_csv(INT_WELLS_REFERENCE)
    wells[extended_wells].to_csv(INT_WELLS_EXTENDED)

    print(f"Complete. Retained {len(wells_clean.columns)} wells.")
    print(f" -> Reference: {len(reference_wells)} wells")
    print(f" -> Extended:  {len(extended_wells)} wells")
    if demoted_wells:
        print(f" -> Demoted to extended (not on reference-network whitelist): "
              f"{len(demoted_wells)} wells  "
              f"[{', '.join(sorted(str(w) for w in demoted_wells))}]")


    # ------------------------------------------------------------------ #
    #  maOD CONVERSION                                                    #
    #  Convert depth-below-pipe-top (negative convention) to water table  #
    #  elevation in metres above Ordnance Datum (maOD).                  #
    #                                                                     #
    #  Formula:  maOD = Pipe_Top_Elev + raw_depth                        #
    #                                                                     #
    #  Raw depth is stored as a negative value (e.g. −1.5 m means the    #
    #  water table is 1.5 m below pipe top). Adding it to the pipe-top   #
    #  elevation therefore subtracts the depth, giving the correct        #
    #  upward-positive maOD value.                                        #
    #                                                                     #
    #  Pipe_Top_Elev is used directly (not reconstructed from            #
    #  DGPS_Ground_Elev + Upstand_m) because the two do not agree for    #
    #  70 of 97 wells — Pipe_Top_Elev is the independently measured       #
    #  value and is the correct reference datum for field readings.       #
    #                                                                     #
    #  Sign check: summer maOD < winter maOD (water table deeper in       #
    #  summer). Verified against nw1, ceh2, nw5, ceh14, d15.             #
    # ------------------------------------------------------------------ #
    print("\n -> Converting depth series to maOD...")
    if _WELL_ELEV_FILE.exists():
        elev_raw = pd.read_csv(_WELL_ELEV_FILE)
        elev_raw.columns = [c.strip() for c in elev_raw.columns]
        elev_raw["name_norm"] = (
            elev_raw["Name"].astype(str).str.strip()
            .str.lower().str.replace(" ", "").str.replace("_", "")
        )
        pipe_top_map = (
            elev_raw.dropna(subset=["Pipe_Top_Elev"])
            .set_index("name_norm")["Pipe_Top_Elev"]
            .to_dict()
        )
        maod_cols = {}
        n_converted = 0
        n_no_elev   = 0
        for col in wells_clean.columns:
            col_norm = normalize_well_name(col)
            pipe_top = pipe_top_map.get(col_norm)
            if pipe_top is not None:
                # raw depth is negative convention: maOD = Pipe_Top + depth
                maod_cols[col] = wells_clean[col] + pipe_top
                n_converted += 1
            else:
                n_no_elev += 1
        if maod_cols:
            wells_maod = pd.DataFrame(maod_cols, index=wells_clean.index)
            wells_maod.to_csv(INT_WELLS_CLEAN_MAOD)
            print(f"    Converted {n_converted} wells to maOD")
            if n_no_elev:
                print(f"    [WARNING] {n_no_elev} wells have no elevation data "
                      f"and are excluded from maOD file")
            print(f"    Saved: {INT_WELLS_CLEAN_MAOD.name}")
        else:
            print("    [WARNING] No wells could be converted to maOD — "
                  "check elevation file contents")
    else:
        print(f"    [WARNING] Elevation file not found: {_WELL_ELEV_FILE}")
        print(f"    maOD file not produced — script 19 will fail without it")

    # ------------------------------------------------------------------ #
    #  ELEVATION LOOKUP EXPORT                                            #
    #  Exports upstand heights for use by script 03 centroid correction.  #
    #  Script 03 applies depth - upstand before averaging into centroids  #
    #  so all wells share a common ground-surface datum.                  #
    # ------------------------------------------------------------------ #
    print("\n -> Exporting well elevation lookup...")

    if _WELL_ELEV_FILE.exists():
        elev_df = pd.read_csv(_WELL_ELEV_FILE)
        elev_df.columns = [c.strip() for c in elev_df.columns]
        elev_df["Name_norm"] = (
            elev_df["Name"].astype(str).str.strip()
            .str.lower().str.replace(" ", "").str.replace("_", "")
        )
        elev_df.to_csv(INT_WELL_ELEVATIONS, index=False)
        print(f"    Saved elevation lookup: {INT_WELL_ELEVATIONS.name}")
    else:
        print(f"    [WARNING] Elevation file not found: {_WELL_ELEV_FILE}")
        print(f"    Upstand correction in script 03 will be skipped.")
