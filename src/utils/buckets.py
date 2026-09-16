"""
utils/buckets.py
================
Script 01's field-convention month bucketing — THE implementation.

It lives in a module of its own, importing nothing but numpy and pandas, so that
every caller can have it: `01_data_prep` at the head of the pipeline, the flood
tools, and `tools/month_bucket_lint.py`, which must be able to run in an
environment without statsmodels. `utils.model_utils` re-exports it, so
`from utils.model_utils import month_bucket` also works and the SSM module keeps
its role as the canonical surface.

One rule, one implementation, one gate (T-32).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-16. New, for T-32: the
#   bucketing rule had FIVE correct implementations and THREE broken ones across
#   the tree. Lifted here from model_utils 1.6.0 so that importing it costs
#   nothing but numpy and pandas.


def month_bucket(dates):
    """Script 01's field-convention bucketing. The single implementation.

    A dipwell reading is taken at the END of the month it represents, sometimes
    a day or two into the next one. So a reading on day > 15 belongs to THAT
    month, and a reading on day <= 15 belongs to the PREVIOUS one: 2021-04-04 is
    March 2021. Returns YYYY-MM-01 — a Timestamp for a scalar, a DatetimeIndex
    for anything vector-like. NaT passes through as NaT.

    NEVER WRITE THIS AS ``d - pd.offsets.MonthBegin(1)``. From any day but the
    first, MonthBegin rolls back only to the CURRENT month's first day, so the
    day <= 15 branch silently does nothing for days 2 to 15 — the rule reads as
    applied and is not. Measured on pandas 3.0.2: 2021-04-04 buckets to April.
    That defect was found and fixed in `warren_flood_prep._well_levels` on
    2026-09-13, and had been reintroduced in two more places by 2026-09-15,
    because the rule lived in a comment at each call site instead of here. It
    cost 49 of 110 Sentinel scenes their correct month. THIS FUNCTION EXISTS SO
    THAT CANNOT HAPPEN A FOURTH TIME (T-32).

    The form below is the one Script 01 already used at its vectorised call
    site: periods, not offsets. It is exhaustively equivalent to every correct
    variant the tree carried — proved over every day from 1990 to 2040 by
    `tools/month_bucket_lint.py`, which is a gate in check_all.
    """
    scalar = isinstance(dates, (str, bytes)) or not hasattr(dates, "__len__")
    d = pd.DatetimeIndex(pd.to_datetime([dates] if scalar else dates))
    per = d.to_period("M")
    out = pd.DatetimeIndex(
        np.where(d.day <= 15, (per - 1).to_timestamp(), per.to_timestamp()))
    return out[0] if scalar else out
