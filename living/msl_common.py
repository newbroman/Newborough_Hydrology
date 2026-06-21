#!/usr/bin/env python3
"""
msl_common.py
=============

Van Willegen et al. (2025) five-year mean spring water level (MSL5), ported
verbatim from Script 26 (26_van_willegen_msl.py) so the *living* forecaster
metric uses exactly the published method and cannot drift from it.

Method (van Willegen et al. 2025, Ecological Indicators 170, 113016):
  * Spring window : 1 Mar – 31 May  (months 3, 4, 5)
  * Annual MSL_y  : unweighted mean of {Mar, Apr, May} in hydrology year y,
                    valid only if all 3 spring months are present.
  * Hydrology yr  : "year B" — starts 1 Jun; a date in Jun(y-1)..May(y) is
                    hydro-year y. Spring months (<6) therefore map to their
                    own calendar year.
  * MSL5(end=y)   : unweighted mean of {MSL_{y-4}..MSL_y}, valid only if all
                    5 annual MSLs are present.
  * latest        : most-recent valid window per well (max window_end_year).

Frame: levels are in the depth-below-ground frame (negative = below ground),
matching the paper. The living hub stores this directly as
`depth_below_ground` (= level_pipe + Upstand_m), so no conversion is needed.

Constants mirror utils/config.py (paper-defined, stable).
"""

import pandas as pd

SPRING_MONTHS = (3, 4, 5)
HYDRO_YEAR_START_MONTH = 6
WINDOW_YEARS = 5
MIN_MONTHS_PER_SPRING = 3
MIN_YEARS_IN_WINDOW = 5


def hydrology_year(year: int, month: int) -> int:
    """Van Willegen 'hydrology year B' (starts 1 June)."""
    return int(year + (1 if month >= HYDRO_YEAR_START_MONTH else 0))


def annual_msl(long: pd.DataFrame) -> pd.DataFrame:
    """
    Per (well, hydro_year): mean of the spring (Mar/Apr/May) levels, valid only
    if all three spring months are present (strict 3-of-3).

    `long` columns required: well, year, month, level_bg.
    """
    spring = long[long["month"].isin(SPRING_MONTHS)].copy()
    # Spring months are < HYDRO_YEAR_START_MONTH, so hydro_year == calendar year,
    # but compute it explicitly to stay faithful to Script 26.
    spring["hydro_year"] = [hydrology_year(y, m)
                            for y, m in zip(spring["year"], spring["month"])]
    g = (spring.groupby(["well", "hydro_year"])["level_bg"]
         .agg(["mean", "count"]).reset_index()
         .rename(columns={"mean": "MSL_m_bg", "count": "n_spring_months"}))
    g["valid"] = g["n_spring_months"] >= MIN_MONTHS_PER_SPRING
    return g


def rolling_5yr(annual: pd.DataFrame,
                window: int = WINDOW_YEARS,
                min_years: int = MIN_YEARS_IN_WINDOW) -> pd.DataFrame:
    """
    Per well, per end_year: mean of {MSL_{y-4}..MSL_y}, reported only if all
    `min_years` annual MSLs in the window are valid.
    """
    rows = []
    for well, sub in annual.groupby("well"):
        sub = sub.set_index("hydro_year").sort_index()
        valid_sub = sub[sub["valid"]]
        if valid_sub.empty:
            continue
        for end_y in range(int(valid_sub.index.min()), int(valid_sub.index.max()) + 1):
            window_years = list(range(end_y - window + 1, end_y + 1))
            present = valid_sub.reindex(window_years)
            n_valid = int(present["MSL_m_bg"].notna().sum())
            if n_valid < min_years:
                continue
            rows.append({
                "well": well,
                "window_end_year": end_y,
                "n_years_in_window": n_valid,
                "MSL5_m_bg": present["MSL_m_bg"].mean(),
            })
    return pd.DataFrame(rows).sort_values(["well", "window_end_year"]).reset_index(drop=True)


def latest_per_well(per_well_5yr: pd.DataFrame) -> pd.DataFrame:
    """Most-recent valid window per well (Script 26's selection)."""
    if per_well_5yr.empty:
        return per_well_5yr
    return (per_well_5yr.sort_values("window_end_year")
            .groupby("well", as_index=False).tail(1)
            .reset_index(drop=True))


def msl5_latest_from_long(long: pd.DataFrame) -> pd.DataFrame:
    """Convenience: long [well, year, month, level_bg] -> latest MSL5 per well."""
    return latest_per_well(rolling_5yr(annual_msl(long)))
