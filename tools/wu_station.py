#!/usr/bin/env python3
"""
wu_station.py — Martin's Weather Underground station IANGLESE3 (Newborough): its daily record and
how its rain compares with RAF Valley (D-278).

  build   raw daily JSON (data/wu_ianglese3/, on the L14 only, gitignored) -> data/wu_ianglese3_daily.csv
  ratio   the descriptive comparison D-278 records: station / RAF Valley and Llyn Alaw / RAF Valley over the
          complete months, and the station / RAF Valley ratio by year

The station's rain was looked at as a possible test of a local rain excess in 2006-08 (Martin, 2026-10-25).
Its archive holds no rain before 2010 and only January in 2008-2011; continuous daily rain runs from 2012
to January 2021. It cannot test 2006-08, and its year-to-year ratio to Valley is too variable to judge two
winters by, so no rule-based test is run on it (D-278). This tool reproduces the numbers that decision quotes.

Usage:
    python3 tools/wu_station.py build      # on the L14, where the raw JSON is
    python3 tools/wu_station.py ratio
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-25. First issue (D-278; Martin 20:41 "lets go with your
#   suggestion with the IANGLESE data").

import argparse
import glob
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

RAW = REPO / "data" / "wu_ianglese3"
CSV = REPO / "data" / "wu_ianglese3_daily.csv"
SUSPECT_MM = 100.0          # a daily total at or above this is flagged as a gauge fault, not rain
MIN_MONTH_COVER = 0.9       # a month counts only if this share of its days carries a rain total
SPAN = ("2012-01-01", "2022-12-31")


def build() -> int:
    import pandas as pd
    files = sorted(glob.glob(str(RAW / "*.json")))
    if not files:
        print(f"no raw files in {RAW.relative_to(REPO)} - the raw JSON stays on the L14")
        return 1
    rows = []
    for f in files:
        d = Path(f).stem
        obs = json.loads(Path(f).read_text()).get("observations", [])
        if not obs:
            continue
        o = obs[0]
        m = o["metric"]
        p = m["precipTotal"]
        flag = "ok" if p is not None else "no_rain_total"
        if p is not None and p >= SUSPECT_MM:
            flag = "suspect_gauge_fault"
        rows.append(dict(date=f"{d[:4]}-{d[4:6]}-{d[6:]}", precip_mm=p, temp_avg_c=m["tempAvg"],
                         qc_status=o["qcStatus"], flag=flag))
    df = pd.DataFrame(rows)
    df.to_csv(CSV, index=False)
    print(f"wrote {CSV.relative_to(REPO)}: {len(df)} reporting days "
          f"({df['flag'].value_counts().to_dict()}), from {len(files)} downloaded days")
    return 0


def _monthly(s):
    import pandas as pd
    g = s.resample("MS")
    tot, n = g.sum(min_count=1), g.count()
    days = pd.Series(tot.index.days_in_month, index=tot.index)
    return tot.where(n >= MIN_MONTH_COVER * days)


def ratio() -> int:
    import pandas as pd
    from utils.midas_rain import read_daily
    from utils.paths import MIDAS_RAIN_DIR, INT_CLIMATE
    w = pd.read_csv(CSV, parse_dates=["date"], index_col="date")
    p = w["precip_mm"].where(w["flag"] == "ok")
    raf = pd.read_csv(INT_CLIMATE, parse_dates=[0], index_col=0)["P_m"] * 1000
    alaw = read_daily(MIDAS_RAIN_DIR / "alaw_01146")
    d = pd.DataFrame({"station": _monthly(p.loc[SPAN[0]:SPAN[1]]), "raf": raf,
                      "alaw": _monthly(alaw.loc[SPAN[0]:SPAN[1]])}).dropna(subset=["station", "raf"])
    both = d.dropna(subset=["alaw"])
    win = d[d.index.month.isin([10, 11, 12, 1, 2, 3])]
    summ = d.drop(win.index)
    print(f"complete months ({SPAN[0][:4]}-{SPAN[1][:4]}): {len(d)}; with Llyn Alaw: {len(both)}")
    print(f"station / RAF Valley      {d.station.sum() / d.raf.sum():.2f}   (monthly r {d.station.corr(d.raf):.2f})")
    print(f"  winter Oct-Mar          {win.station.sum() / win.raf.sum():.2f}")
    print(f"  summer Apr-Sep          {summ.station.sum() / summ.raf.sum():.2f}")
    print(f"Llyn Alaw / RAF Valley    {both.alaw.sum() / both.raf.sum():.2f}   (same months)")
    print(f"station / Llyn Alaw       {both.station.sum() / both.alaw.sum():.2f}")
    y = d.groupby(d.index.year).agg(months=("station", "size"), station=("station", "sum"), raf=("raf", "sum"))
    y["ratio"] = y["station"] / y["raf"]
    print(y[y["months"] >= 6].round({"station": 0, "raf": 0, "ratio": 2}).to_string())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("build", "ratio"))
    a = ap.parse_args()
    return build() if a.action == "build" else ratio()


if __name__ == "__main__":
    raise SystemExit(main())
