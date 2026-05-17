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

__version__ = "1.1.1"  # Hollingham (2026) — last revised 2026-05-14
# Changelog:
#   1.1.1 (2026-05-14) — Docstring fix: REFERENCE_NETWORK_WHITELIST comment
#     said "69 wells"; corrected to 66 (= published partition, no real wells
#     lost; stale text from a pre-publication count).
#   1.1.0 (2026-05-14) — Clarified the well-cleaning call to call out the
#     depth-floor sign-convention fix in utils/data_utils.py. The cleaning
#     function now masks readings deeper than -4.0 m (corrected comparison
#     direction); positive readings, which represent slack flooding above
#     pipe top, are retained.
#   1.0.0 (2026-04-10) — Initial pipeline release.

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
from utils.config import REFERENCE_CUTOFF_DATE, RAF_VALLEY_LAT_DEG

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
# This whitelist pins the reference network to the 66 wells that were
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
#     Llyn Rhos is also excluded from the extended network via the
#     EXTENDED_NETWORK_BLACKLIST (see below) because its lake-stage
#     signal is not interpretable as groundwater behaviour.
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

# ──────────────────────────────────────────────────────────────────────────────
# EXTENDED NETWORK BLACKLIST
#
# Wells excluded from BOTH networks — not just the reference network.
# The reference whitelist already keeps these out of the clustering and SSM,
# but by default they still appear in the extended network (Script 06) because
# they meet the minimum-record-length criterion.
#
# Llyn Rhos-ddu is a lake-stage measurement, not a water-table observation.
# Including it in the extended Pearson affinity audit adds a physically
# meaningless data point (best-match r = 0.66, lowest in the sitewide
# audit) that cannot be interpreted as groundwater behaviour. It is
# excluded here so that Scripts 05/06 remain purely algorithmic and the
# exclusion rationale is documented in one place.
#
# To include a blacklisted well in the extended network (e.g. for a
# lake-level comparison study), remove it from this set.
# ──────────────────────────────────────────────────────────────────────────────
EXTENDED_NETWORK_BLACKLIST = frozenset({
    "llynrhos",   # lake surface, not a water-table response
})

# RAF Valley, Anglesey — site latitude for Thornthwaite day-length correction.
# Imported from utils.config (RAF_VALLEY_LAT_DEG = 53.25).


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

    # ── Month bucketing: assign each reading to the month it represents ────
    # Fieldwork convention: a visit on day 1–15 of month M is the END-of-
    # previous-month reading (represents month M−1). A visit on day 16–31
    # is a within-month reading (represents month M).
    #
    # Example: 01/09/2011 → represents August 2011 → bucket to 2011-08.
    #          31/08/2011 → represents August 2011 → bucket to 2011-08.
    #
    # This ensures the monthly well index aligns with calendar months in
    # the climate record without requiring a compensating lag-1 shift in
    # downstream regressions. HEADLINE_LAG in config.py is set to 0.
    d = pd.to_datetime(wells.index, dayfirst=True, errors="coerce")
    prev_month = (d.to_period("M") - 1).to_timestamp()
    this_month = d.to_period("M").to_timestamp()
    wells.index = np.where(d.day <= 15, prev_month, this_month)
    wells = wells.apply(pd.to_numeric, errors="coerce").groupby(level=0).mean()
    if "NW8" in wells.columns and "NW8b" in wells.columns:
        wells["NW8"] = wells["NW8b"].combine_first(wells["NW8"])
        wells.drop(columns=["NW8b"], inplace=True)
    # clean_well_series masks readings deeper than MIN_PHYSICAL_DEPTH = -4.0 m
    # (a safety floor; the deepest plausible water table at Newborough is ~3 m
    # below ground). Positive readings are RETAINED — the slacks regularly
    # flood above pipe top and those readings are real flood-month
    # observations that the SSM and flood-threshold work depend on. See
    # utils/data_utils.py for the history of this threshold (an earlier
    # implementation had the comparison direction wrong and did not mask
    # any deep readings).
    for col in wells.columns:
        wells[col] = clean_well_series(wells[col])

    wells_clean = wells.dropna(axis=1, thresh=MIN_MONTHS_THRESH)
    wells_clean.to_csv(INT_WELLS_CLEAN)

    reference_wells, extended_wells = [], []
    demoted_wells = []   # wells that meet auto-criteria but are not whitelisted
    blacklisted_wells = []  # wells excluded from both networks
    for col in wells.columns:
        series = wells[col].dropna()
        if series.empty:
            continue
        col_norm = normalize_well_name(col)
        if col_norm in EXTENDED_NETWORK_BLACKLIST:
            blacklisted_wells.append(col)
            continue
        meets_reference_criteria = (
            len(series) >= MIN_MONTHS_THRESH
            and series.index.max() >= RECENCY_DATE
        )
        if meets_reference_criteria:
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
    if blacklisted_wells:
        print(f" -> Excluded from both networks (blacklist): "
              f"{len(blacklisted_wells)} wells  "
              f"[{', '.join(sorted(str(w) for w in blacklisted_wells))}]")


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

    # ------------------------------------------------------------------ #
    #  PIPELINE SCENARIO PARAMETERS                                       #
    #  Writes the consolidated parameter file used by all downstream      #
    #  scenario scripts (09b, 09d, 19, 21). On re-runs, picks up real    #
    #  values from existing upstream outputs (03, 10e, 17); on first      #
    #  run, uses defaults with a flag.                                    #
    # ------------------------------------------------------------------ #
    print("\n -> Writing pipeline scenario parameters...")
    from utils.pipeline_params import write_initial_params
    write_initial_params(wells_clean, climate)

    # ------------------------------------------------------------------ #
    #  Seed site-wide observations CSV (long-format registry of single-  #
    #  value pipeline-produced observations that don't fit the per-      #
    #  cluster schema of pipeline_scenario_params.csv).  Defaults are    #
    #  written here; producer scripts (09a, 16, ...) overwrite their     #
    #  rows downstream.                                                  #
    # ------------------------------------------------------------------ #
    print("\n -> Writing pipeline site observations...")
    from utils.site_observations import write_initial_site_observations
    write_initial_site_observations()

    print("\n=== Script 01 complete ===")
