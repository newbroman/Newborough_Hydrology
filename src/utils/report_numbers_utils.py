"""
utils/report_numbers_utils.py
=============================
Neutral home for the ``ReportNumbers`` report-numbers accumulator.

Every analysis / figure script that puts a number into the report should
record that number here and emit a committed ``*_report_numbers.csv`` so the
figure-only statistics become traceable against the pipeline (the same
pattern Scripts 09/10 already use).

The accumulator was previously defined inside ``utils/clearfell_common.py``.
It is lifted here so non-clearfell scripts (07, 08, 18, 20, 29, …) can import
it without pulling in the clearfell BACI machinery. ``clearfell_common`` now
re-exports ``ReportNumbers`` from this module for backward compatibility, so
existing imports continue to work unchanged.

CSV schema (one row per cited number):

    Parameter, Well, Era, Value, Unit, Note

- Parameter : machine-readable key for the statistic (e.g. "C1_median_dNSE").
- Well      : well ID if the number is per-well, else "".
- Era       : period / scenario qualifier if any, else "".
- Value     : the number (rounded to 4 dp for floats) or a string.
- Unit      : "m", "months", "", etc.
- Note      : free-text provenance / caveat.

__version__ : 1.0.0
"""

__version__ = "1.0.1"  # Hollingham (2026) -- 2026-08-18. ReportNumbers.add() rounded EVERY report number to 4 dp
#   on the way into *_report_numbers.csv - the store the citation index and
#   every document quote from. Highest-leverage instance of the same defect.
#   Store-time rounding removed (D-035): values are
#   written at the precision they were computed and rounded where they are
#   displayed. Three decimals is a display rule for quantities of order
#   one; at storage it costs a significant figure on the small ones.
#
# v1.0.0  # Hollingham (2026) — 2026-06-21

import pandas as pd


class ReportNumbers:
    """Accumulator for report numbers CSV export."""

    def __init__(self):
        self.rows = []

    def add(self, parameter, value, unit="m", well="", era="", note=""):
        self.rows.append({
            "Parameter": parameter,
            "Well": well,
            "Era": era,
            "Value": float(value) if pd.notna(value) and isinstance(value, (int, float)) else value,
            "Unit": unit,
            "Note": note,
        })

    def to_dataframe(self):
        return pd.DataFrame(self.rows)

    def save(self, path):
        df = self.to_dataframe()
        df.to_csv(path, index=False)
        return len(self.rows)
