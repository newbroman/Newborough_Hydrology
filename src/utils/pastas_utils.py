"""
pastas_utils.py — the Pastas plumbing shared by Script 48 and Script 50's E8.

Script 48 (the Pastas cross-check, D-217) and Script 50 E8 (two drainage time scales per cluster, D-231)
both drive Pastas with the monthly climate spread evenly over each month's days. The spreading lived in
Script 48 alone until 2026-10-02 and moved here unchanged, with its start date as an argument, so that E8
does not copy it. Script 48's outputs are identical before and after the move.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-02 (D-231). First issue: spread_daily() from Script 48
#   1.5.0's daily_stresses() unchanged, with the start as an argument; continuous_start().

import pandas as pd


def spread_daily(cl: pd.DataFrame, start: pd.Timestamp):
    """The monthly P and PET totals spread evenly over each month's days (m/day), from `start` to the end
    of the climate record. A stress stamped YYYY-MM-01 is the total for that month (Script 01 convention)."""
    c = cl.loc[start:].dropna(subset=["P_m", "PET"])
    days = pd.date_range(c.index[0], c.index[-1] + pd.offsets.MonthEnd(0), freq="D")
    per = days.to_period("M")
    ndays = pd.Series(days, index=days).groupby(per).size()
    pm = c["P_m"].copy(); pm.index = pm.index.to_period("M")
    em = c["PET"].copy(); em.index = em.index.to_period("M")
    P = pd.Series((pm.reindex(per) / ndays.reindex(per)).to_numpy(), index=days, name="P")
    E = pd.Series((em.reindex(per) / ndays.reindex(per)).to_numpy(), index=days, name="E")
    return P.dropna(), E.dropna()


def continuous_start(cl: pd.DataFrame) -> pd.Timestamp:
    """The first month after the last gap in the monthly climate record: Pastas needs equidistant stresses,
    so the longest warm-up available is from here."""
    c = cl.dropna(subset=["P_m", "PET"])
    full = pd.date_range(cl.index[0], cl.index[-1], freq="MS")
    missing = full.difference(c.index)
    return (missing.max() + pd.offsets.MonthBegin(1)) if len(missing) else c.index[0]
