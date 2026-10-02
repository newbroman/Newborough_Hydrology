"""
midas_rain.py — Met Office MIDAS Open daily rainfall (BADC-CSV), read into one daily series per gauge.

Script 50 E8d (D-234) asks whether rain arriving in long events, which a monthly total hides, explains the
2006-08 excess. The daily gauges are a documented raw-input exception, like Scripts 09/10/24: they are read
only here. See data/MIDAS_RAIN_PROVENANCE.md.

Conventions, all from the files themselves:
  * a daily reading (ob_day_cnt == 1) is the 24 h ending at 09:00 on ob_date, so the rain is assigned to the
    day BEFORE ob_date (checked 2026-10-02: Valley's daily sums then match its monthly record, r 0.994);
  * multi-day accumulations (ob_day_cnt > 1) cannot be placed on a day and are dropped, leaving those days
    missing — never filled;
  * when a day appears more than once, the latest version_num wins.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-02 (D-234). First issue.

import io
from pathlib import Path

import pandas as pd


def _read_one(path: Path) -> pd.DataFrame:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "\ndata\n" not in text:
        return pd.DataFrame()
    body = text.split("\ndata\n", 1)[1].rsplit("\nend data", 1)[0]
    return pd.read_csv(io.StringIO(body))


def read_daily(station_dir: Path) -> pd.Series:
    """Daily rainfall (mm) for one gauge, indexed by the day the rain fell; days without a single-day
    reading are absent (missing), never zero."""
    frames = [_read_one(p) for p in sorted(Path(station_dir).glob("*_qcv-1_*.csv"))]
    d = pd.concat([f for f in frames if len(f)], ignore_index=True)
    d = d[d["ob_day_cnt"] == 1].copy()
    d["ob_date"] = pd.to_datetime(d["ob_date"])
    d = d.sort_values(["ob_date", "version_num"]).drop_duplicates("ob_date", keep="last")
    s = d.set_index("ob_date")["prcp_amt"].astype(float)
    s.index = (s.index - pd.Timedelta(days=1)).normalize()
    s.name = Path(station_dir).name
    return s.sort_index()


def station_meta(station_dir: Path) -> dict:
    """observation_station, location and height from the newest file's header."""
    files = sorted(Path(station_dir).glob("*_qcv-1_*.csv"))
    meta = {}
    for line in files[-1].read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split(",")
        if len(parts) >= 3 and parts[1] == "G" and parts[0] in ("observation_station", "location", "height", "midas_station_id"):
            meta[parts[0]] = ",".join(parts[2:])
        if line == "data":
            break
    return meta
