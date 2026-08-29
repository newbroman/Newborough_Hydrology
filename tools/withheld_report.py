#!/usr/bin/env python3
"""
withheld_report — say out loud when a script has withheld its own headline.

WHY

  Script 40 writes `rate_m_yr` as NA when its gate fails, rather than emitting a
  number with a "not citable" note beside it (D-085). That is deliberate: a note
  relies on the next reader honouring it, and D-006 makes a pipeline output
  citable by definition, so the refusal has to be in the output.

  But a refusal that nothing reports back is indistinguishable from success. A
  green check_all with a silently empty column is exactly how a withheld value
  becomes a forgotten one. So this reports the state on every run.

  REPORTED, NOT GATED. Withholding is the script working correctly; failing the
  build on it would teach us to route around the gate. The real failures are the
  file going missing and the D-060 regression breaking, and both are surfaced.

__version__ : 1.0.0
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-29. First issue, with
#   Script 40.

import sys
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
SERIES = ROOT / "outputs" / "40_shoreline_retreat" / "40_01_epoch_series.csv"

GREEN, YELLOW, RED, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[0m"


def main() -> int:
    if not SERIES.exists():
        print(f"  {YELLOW}absent{RESET}   {SERIES.relative_to(ROOT)} — Script 40 has not run")
        return 0
    df = pd.read_csv(SERIES)

    reg = df[df["basis"] == "d060_regression_unrestricted"]
    if reg.empty:
        print(f"  {RED}FAIL{RESET}     Script 40: no D-060 regression row — the method is unchecked")
    else:
        r = reg.iloc[0]
        dev = float(r.get("deviation_pct", float("nan")))
        colour = GREEN if dev <= 10.0 else RED
        print(f"  {colour}D-060{RESET}    reproduction {r['median_m']:.3f} m / "
              f"{r['rate_m_yr']:.3f} m/yr against published "
              f"{r.get('d060_published_m')} m / {r.get('d060_published_rate_m_yr')} m/yr "
              f"({dev:.1f}%)")

    gated = df[df["basis"] != "d060_regression_unrestricted"]
    withheld = gated[gated["withheld"] == True]          # noqa: E712
    if withheld.empty:
        print(f"  {GREEN}OK{RESET}       Script 40: headline EMITTED — the gate passes")
        return 0

    reason = str(withheld.iloc[0]["withheld_reason"])
    print(f"  {YELLOW}withheld{RESET} Script 40: {len(withheld)} of {len(gated)} intervals "
          f"carry no rate. This is the gate working, not a build failure.")
    for part in [p.strip() for p in reason.split(";") if p.strip()]:
        print(f"             · {part}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
