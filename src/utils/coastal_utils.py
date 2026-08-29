"""
utils/coastal_utils.py
======================
The coastal single-event edge drawdown, defined once and read from a measurement.

WHY THIS EXISTS

  The construction

      h0 = retreat_m * (delta_0 / retreat_rate)

  converts a discrete shoreline-retreat event into an edge water-table drawdown.
  It was written out separately in Scripts 20 and 09f, and its divisor came from
  ``config.COAST_RETREAT_RATE = 8.3`` — a figure derived from a newspaper report
  of ~50 m of retreat between 2014 and 2020.

  Two things were wrong with that, and both are fixed here.

  **A period mismatch (D-090).** delta_0 is fitted over the whole record
  (2005-03 to 2026-02); the 8.3 rate was a six-year window. The ratio asserts
  "the water table fell delta_0 per year while the shore retreated R per year",
  which is a sensitivity only if both describe the same period. Measured, the
  fault is entirely in the denominator: a window-matched delta_0 moves 0.5 %,
  the rate by a factor of 3.6.

  **A fitted value in a constants file (D-075).** The rate is now MEASURED, by
  Script 40, from the digitised coastline epochs — so it is a result, and D-075
  puts results in report-numbers files, not in ``config.py``. It is read live
  here, exactly as delta_0 already is, with a documented first-pass fallback.

  ONE CONSEQUENCE MUST TRAVEL WITH THIS. h0 is no longer an independent
  calibration: delta_0 comes from the water-table record and the retreat rate
  from shoreline position, both measured by this study. That is not circular —
  they are different data — but the methods text must say so.

__version__ : 1.0.0
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-29. First issue (D-090).
#   Centralises h0 = retreat x (delta_0 / rate), previously written out in
#   Script 20 (twice) and 09f, and re-points its divisor from the committed
#   config constant to Script 40's measured rate.

import pandas as pd

from utils import paths
from utils.pipeline_params import default_value

#: The interval whose rate is used. Chosen to match delta_0's fit span; Script 40
#: emits the overlap fraction and warns below 90 %.
MATCHED_INTERVAL = ("2006", "2026")


def load_measured_retreat_rate(quiet: bool = False):
    """(rate m/yr, provenance str) from Script 40, or the documented fallback.

    Reads the live CSV first and falls back with a console warning, the pattern
    the two-pass scripts already use for delta_0 and the scrape anchor. A
    WITHHELD rate is treated as absent: Script 40 writes NA when its gate fails,
    and consuming a withheld value would defeat the gate.
    """
    try:
        df = pd.read_csv(paths.OUT_40_EPOCH_SERIES)
        row = df[(df["basis"] == "modern_common_frontage")
                 & (df["from_epoch"].astype(str) == MATCHED_INTERVAL[0])
                 & (df["to_epoch"].astype(str) == MATCHED_INTERVAL[1])]
        if len(row):
            rate = row["rate_m_yr"].iloc[0]
            if pd.notna(rate) and float(rate) > 0:
                return float(rate), (
                    f"Script 40 measured {MATCHED_INTERVAL[0]}-{MATCHED_INTERVAL[1]} "
                    f"({float(row['years'].iloc[0]):.1f} yr)")
            if not quiet:
                print("  [WARNING] Script 40 has WITHHELD its retreat rate — its "
                      "gate did not pass. Falling back to the documented default; "
                      "the figure is not citable until the gate opens.")
    except Exception as exc:
        if not quiet:
            print(f"  [WARNING] could not read Script 40's retreat rate ({exc})")
    rate = default_value("coast_retreat_rate_m_yr")
    if not quiet:
        print(f"  [WARNING] using the documented first-pass default retreat rate "
              f"{rate} m/yr")
    return float(rate), "pipeline_params default (first pass)"


def coastal_edge_h0(delta0_abs, retreat_m=None, quiet: bool = False):
    """Edge drawdown (mm) for a single retreat event of ``retreat_m`` metres.

    Returns (h0_mm, rate_m_yr, per_metre_mm, provenance).
    ``delta0_abs`` is the absolute coast-edge decline rate in mm/yr, read live
    from Script 25 by the caller.
    """
    from utils.config import COAST_RETREAT_M
    if retreat_m is None:
        retreat_m = COAST_RETREAT_M
    rate, prov = load_measured_retreat_rate(quiet=quiet)
    per_metre = delta0_abs / rate
    return retreat_m * per_metre, rate, per_metre, prov
