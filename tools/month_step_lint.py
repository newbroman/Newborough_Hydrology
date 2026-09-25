#!/usr/bin/env python3
"""
month_step_lint.py — is every monthly change one calendar month? (D-195)

WHAT IT GATES

  1. The cleaned well table has a row for every calendar month between its first
     and last (Script 01). A month no visit buckets to used to have NO row, so the
     one-month bridge could not see it: June 2005 and December 2022.
  2. The one-month bridge bridges ONLY interior gaps of one month
     (data_utils.clean_well_series): no month of a longer gap is filled, and no
     month past a record's first or last reading.
  3. utils.model_utils.build_ssm_frame, run on every reference and extended well
     against the committed CSVs, never pairs a month with anything but the level
     of the previous calendar month. It used to dropna() first and shift the
     survivors, so a gap made Delta_h span two or more months and fitted it to
     one month's weather: 151 of 13,211 reference-network pairs, 2-23 months.

  --selftest plants each defect in a synthetic series and proves the gate fails
  on it, so a green bar means the check can see what it is looking for.

USAGE
  python3 tools/month_step_lint.py
  python3 tools/month_step_lint.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-25. First cut (D-195).

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.paths import (                                     # noqa: E402
    INT_CLIMATE, INT_WELLS_CLEAN, INT_WELLS_REFERENCE, INT_WELLS_EXTENDED,
    INT_WELLS_PROVENANCE,
)
from utils.data_utils import clean_well_series                # noqa: E402
from utils.model_utils import build_ssm_frame                 # noqa: E402


def missing_months(index) -> list:
    idx = pd.DatetimeIndex(index)
    full = pd.date_range(idx.min(), idx.max(), freq="MS")
    return [d.strftime("%Y-%m") for d in full.difference(idx)]


def cross_gap_rows(frame: pd.DataFrame, series: pd.Series) -> int:
    """Rows whose h_prev is not the series' level in the previous calendar month."""
    if frame.empty:
        return 0
    prev = pd.to_numeric(series, errors="coerce").reindex(
        pd.DatetimeIndex(frame.index) - pd.DateOffset(months=1)).to_numpy(float)
    got = frame["h_prev"].to_numpy(float)
    return int((~(np.isfinite(prev) & np.isclose(prev, got))).sum())


def bridge_faults(raw: pd.Series, cleaned: pd.Series, limit: int = 1) -> int:
    """Cells filled that the one-month rule does not allow: inside a longer run of
    missing months, or before the first / after the last reading."""
    na = raw.isna()
    run_id = (na != na.shift()).cumsum()
    run_len = na.groupby(run_id).transform("sum")
    first, last = raw.first_valid_index(), raw.last_valid_index()
    edge = (raw.index < first) | (raw.index > last) if first is not None else na
    bad = na & cleaned.notna() & ((run_len > limit) | edge)
    return int(bad.sum())


def provenance_faults(prov: pd.DataFrame) -> list:
    """Wells whose provenance shows a bridged cell that is not a lone month between
    two measured months."""
    out = []
    for c in prov.columns:
        m = prov[c].astype(str).to_numpy()
        n = 0
        for i, v in enumerate(m):
            if v == "interpolated" and not (0 < i < len(m) - 1
                                            and m[i - 1] == "measured" and m[i + 1] == "measured"):
                n += 1
        if n:
            out.append((c, n))
    return out


def check() -> int:
    rc = 0
    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    gaps = missing_months(wells.index)
    if gaps:
        print(f"  FAIL  {INT_WELLS_CLEAN.name} has no row for {', '.join(gaps)} "
              f"(Script 01 must put the table on the calendar before cleaning)")
        rc = 1
    else:
        print(f"  ok    {INT_WELLS_CLEAN.name}: a row for every month "
              f"{wells.index.min():%Y-%m} to {wells.index.max():%Y-%m}")
    if INT_WELLS_PROVENANCE.exists():
        pf = provenance_faults(pd.read_csv(INT_WELLS_PROVENANCE, index_col=0))
        if pf:
            print(f"  FAIL  {sum(n for _, n in pf)} bridged cell(s) that are not a lone month "
                  f"between two readings: " + ", ".join(f"{c} ({n})" for c, n in pf[:8]))
            rc = 1
        else:
            print(f"  ok    {INT_WELLS_PROVENANCE.name}: every bridged cell is one month "
                  f"between two readings")
    cols = []
    for f in (INT_WELLS_REFERENCE, INT_WELLS_EXTENDED):
        if f.exists():
            cols += [c for c in pd.read_csv(f, index_col=0, nrows=0).columns if c in wells.columns]
    bad, rows, worst = 0, 0, []
    for c in dict.fromkeys(cols):
        fr = build_ssm_frame(wells[c], climate)
        n = cross_gap_rows(fr, wells[c])
        rows += len(fr)
        bad += n
        if n:
            worst.append((c, n))
    if bad:
        print(f"  FAIL  {bad} of {rows} build_ssm_frame rows pair a month with anything but "
              f"the previous calendar month: " + ", ".join(f"{c} ({n})" for c, n in worst[:8]))
        rc = 1
    else:
        print(f"  ok    build_ssm_frame: {rows} rows over {len(cols)} wells, every h_prev "
              f"the previous calendar month")
    return rc


def selftest() -> int:
    idx = pd.date_range("2000-01-01", periods=24, freq="MS")
    s = pd.Series(np.sin(np.arange(24) / 3.0) - 1.0, index=idx)
    clim = pd.DataFrame({"P_m": 0.05 + 0.0 * np.arange(24), "PET": 0.03 + 0.0 * np.arange(24)},
                        index=idx)
    ok = True
    # (1) a month with no row is seen
    ok &= missing_months(s.drop(idx[5]).index) == [idx[5].strftime("%Y-%m")]
    # (2) the bridge: one interior month filled; a 3-month run, a leading and a
    # trailing gap not filled — and a checker that sees pandas' limit=1 behaviour
    raw = s.copy()
    raw.iloc[[0, 4, 9, 10, 11, 23]] = np.nan
    good = clean_well_series(raw)
    ok &= bool(good.iloc[[4]].notna().all()) and bool(good.iloc[[0, 9, 10, 11, 23]].isna().all())
    ok &= bridge_faults(raw, good) == 0
    ok &= bridge_faults(raw, raw.interpolate(method="time", limit=1)) > 0
    pv = pd.DataFrame({"w": ["measured", "interpolated", "missing", "missing", "measured"]})
    ok &= provenance_faults(pv) == [("w", 1)]
    pv = pd.DataFrame({"w": ["measured", "interpolated", "measured"]})
    ok &= provenance_faults(pv) == []
    # (3) a two-month gap: the old row-order frame is caught, the calendar frame is clean
    g = s.copy()
    g.iloc[[8, 9]] = np.nan
    old = pd.DataFrame({"h": g, "P": clim["P_m"], "PET": clim["PET"]}).dropna()
    old["h_prev"] = old["h"].shift(1)
    old = old.dropna()
    ok &= cross_gap_rows(old, g) > 0
    ok &= cross_gap_rows(build_ssm_frame(g, clim), g) == 0
    print("month_step_lint --selftest: " + ("OK — every planted defect is caught"
                                             if ok else "FAIL — a planted defect was missed"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    rc = check()
    print("month_step_lint: " + ("OK" if rc == 0 else "FAIL"))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
