"""
utils/data_utils.py
Shared data preparation helpers used across multiple pipeline scripts.
"""

import pandas as pd
import numpy as np

MAX_PHYSICAL_DEPTH = 4.0


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


def clean_well_series(series: pd.Series, max_depth: float = MAX_PHYSICAL_DEPTH) -> pd.Series:
    """
    Clean a well time series by removing unphysical values and interpolating short gaps.

    Values exceeding max_depth are replaced with NaN, then gaps of up to 3 months
    are filled by time-based linear interpolation.
    """
    cleaned = series.where(series <= max_depth, np.nan)
    return cleaned.interpolate(method="time", limit=3)


def calculate_cusum(series: pd.Series, baseline_mean: float) -> pd.Series:
    """
    Calculate the Cumulative Sum (CUSUM) relative to a baseline mean.

    C_t = sum_{i=1}^{t} (x_i - baseline_mean)
    """
    return (series - baseline_mean).cumsum()
