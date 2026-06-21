"""
utils/data_utils.py
Shared data preparation helpers used across multiple pipeline scripts.
"""

import pandas as pd
import numpy as np

# Physical depth floor for water-table readings (m, signed, below pipe top).
# Raw dipwell readings are stored as negative values by convention: a reading
# of -1.5 m means the water table sits 1.5 m below pipe top. The deepest
# plausible water table at Newborough is around 3 m below ground; -4.0 m is
# the safety margin. Any reading more negative than this (e.g. a stray -7 m
# from a missed entry or a damaged sensor record) is treated as unphysical
# and masked.
#
# Positive readings are NOT masked. The slacks at Newborough regularly flood
# above pipe top, and field readings on those visits record the standing-
# water level above the pipe rim. These are real flood-month observations
# and must be retained for the SSM, the cluster analysis, and the flooding
# thresholds. There are >1,400 such readings in the current dataset.
MIN_PHYSICAL_DEPTH = -4.0   # signed floor; readings below this are masked

# Legacy alias retained for any external code that imported the old name.
# The old constant (MAX_PHYSICAL_DEPTH = 4.0) referred to the magnitude of
# the depth floor, but was used in a comparison whose direction did not
# actually mask deep readings. It is preserved here as a positive magnitude
# (=  -MIN_PHYSICAL_DEPTH) so that imports do not break; the corrected
# implementation reads it through MIN_PHYSICAL_DEPTH.
MAX_PHYSICAL_DEPTH = -MIN_PHYSICAL_DEPTH   # = 4.0; magnitude of the floor


# Provenance flag values written into the per-cell provenance series.
PROV_MEASURED     = "measured"
PROV_INTERPOLATED = "interpolated"
PROV_MISSING      = "missing"


def normalize_well_name(value: str) -> str:
    """Normalise well IDs for robust joining (lowercase, no spaces)."""
    return str(value).strip().lower().replace(" ", "")


def parse_met_date(date_str: str) -> pd.Timestamp:
    """Parse Met Office month-year strings such as 'Jan 95' or 'Dec 26'."""
    try:
        m, y = str(date_str).split()
        year = int(y) + (2000 if int(y) <= 26 else 1900)
        return pd.to_datetime(f"01-{m}-{year}")
    except Exception:
        return pd.NaT


def clean_well_series(
    series: pd.Series,
    min_depth: float = MIN_PHYSICAL_DEPTH,
    limit: int = 1,
    return_provenance: bool = False,
):
    """
    Clean a well time series by removing unphysical deep readings and
    interpolating short single-month gaps.

    Raw dipwell readings use a negative-depth convention (e.g. -1.5 m means
    the water table sits 1.5 m below pipe top). Readings more negative than
    ``min_depth`` (default -4.0 m, deeper than physically plausible at
    Newborough) are replaced with NaN. Positive readings are retained: the
    Newborough slacks flood above pipe top regularly, and the field readings
    on those visits are real water-level observations that the SSM and
    the flood-threshold work depend on.

    Single missed-visit gaps (one consecutive NaN month between two
    measurements) are then filled by time-based linear interpolation. Multi-
    month gaps are left as NaN.

    Parameters
    ----------
    series : pd.Series
        Time-indexed depth series for one well.
    min_depth : float
        Signed lower floor (e.g. -4.0 m). Readings strictly below this are
        masked to NaN before interpolation.
    limit : int
        Maximum length of consecutive NaN run that is filled by linear
        interpolation. Default 1: only single missed monthly visits are
        bridged. See history note below.
    return_provenance : bool
        If True, return ``(cleaned, provenance)`` where ``provenance`` is a
        Series aligned to ``series.index`` with values in
        ``{"measured", "interpolated", "missing"}``. If False (default),
        return only the cleaned series.

    Returns
    -------
    pd.Series
        Cleaned series (and provenance series if requested).

    History
    -------
    Prior to the Defect E fix (2026-05-19), ``limit`` defaulted to 3.
    A site-wide audit of the clearfell-BACI panel found that the
    multi-month interpolation runs disproportionately span the Jun-Sep
    drawdown season, where linear interpolation systematically flattens
    summer minima and produces phantom minimum values for well-years with
    zero measured Jun-Sep coverage (e.g. WMC3 2019, NW6 2019, NW7 2019:
    all silently filled across the entire summer from May/Oct endpoints).
    The headline Forest x Impact ANCOVA step was robust in direction but
    the summer-only contrast lost statistical significance once
    interpolated cells were excluded. The current setting ``limit=1``
    matches the physical interpretation that one missed monthly visit can
    plausibly be bridged while leaving the analytically dangerous 2-3
    month summer gaps honestly NaN downstream.

    An earlier version of this function also tested ``series <= 4.0``
    against the same negative-valued series. The comparison direction did
    not mask any deep readings - every legitimate negative depth passed the
    test. The signed floor used here makes the intent explicit and actually
    masks deep-magnitude outliers if they appear.
    """
    raw = pd.to_numeric(series, errors="coerce")
    masked = raw.where(raw >= min_depth, np.nan)
    cleaned = masked.interpolate(method="time", limit=limit)

    if not return_provenance:
        return cleaned

    prov = pd.Series(PROV_MISSING, index=series.index, dtype=object)
    prov[masked.notna()] = PROV_MEASURED
    prov[masked.isna() & cleaned.notna()] = PROV_INTERPOLATED
    return cleaned, prov


def calculate_cusum(series: pd.Series, baseline_mean: float) -> pd.Series:
    """
    Calculate the Cumulative Sum (CUSUM) relative to a baseline mean.

    C_t = sum_{i=1}^{t} (x_i - baseline_mean)
    """
    return (series - baseline_mean).cumsum()
