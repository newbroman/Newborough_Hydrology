#!/usr/bin/env python3
"""
table_configs.py — which report table is built from which pipeline CSV, and how.

WHY THIS IS DATA AND NOT CODE

  Martin ruled on 2026-09-04 that report tables are GENERATED from the pipeline
  (spec: working/updates/NRG_spec_pipeline_number_ledger_2026-09-04.md, option
  B). A table renders a ROUNDED SUBSET of its source CSV, with its own column
  order, labels and precision, so "generate" needs a mapping per table. That
  mapping is the only thing that differs between tables; the engine
  (`tools/table_gen.py`) is the same for all of them. Scaling to the other
  tables in `tools/figure_table_sources.csv` therefore means adding an entry
  HERE, not touching the engine.

  `figure_table_sources.csv` declares one source per table. This file is where
  that declaration becomes precise enough to regenerate the table: report9
  Table 1.3, for instance, is declared against 03_03 but its ten data rows
  carry BOTH record bases, which only 03_14 holds (03_03 is the full-record
  subset of 03_14, value for value), and its well counts come from 03_02.

SCHEMA (one dict per table)

  id          "report9/Table21" — chapter and ODF table:name; printed only
  doc         chapter number, resolved through doc_paths.chapter_odt()
  table_name  the table:name attribute in content.xml (stable across edits; the
              typed "Table 1.3" number is a caption FIELD and is not used)
  caption     what the table is, for a reader of this file
  sources     {alias: repo-relative CSV path}; the first alias drives the rows
  rows        {"source": alias, "filter": {col: value}} — one table row per CSV
              row that survives the filter, in CSV order (the pipeline emits
              its tables in display order; sorting here would be a second
              opinion about that)
  header      the exact header-row cell texts. The engine REFUSES to touch a
              table whose header differs — it is the assertion that the table
              found by name is the table this entry describes.
  columns     one spec per displayed column, in display order:
      col       CSV column of the row source
      lookup    (alias, key_col, value_col) — take value_col from the row of
                `alias` whose key_col equals this row's key_col (a join)
      fmt       "text" | "int" | "fixed" | "pvalue" | "map"
      dp        decimal places for fixed / pvalue
      map       {csv_value: template} for fmt "map"; the template is
                str.format-ed over the row's raw fields
      re        [pattern, replacement] applied to the text after formatting
      rowspan   True — the cell is written once per run of equal values and
                the continuation rows carry covered cells (a vertical merge)

  Numbers: "fixed" renders a float at `dp` places with the Unicode minus
  (U+2212) for negatives, which is what every table in the corpus uses;
  "pvalue" renders "<0.001" below that threshold and `dp` places otherwise.
  Rounding is a RENDERING decision (project rule): the CSV carries full
  precision and the precision here is what the table displays.

  NOTE ON PRECISION. The project rule says displayed outputs carry three
  decimal places. Table 1.3 has always shown LCSC and R² at two, and this
  entry reproduces the table AS PUBLISHED — the prototype's job is to prove
  that generation reproduces the hand-typed table exactly. Moving those two
  columns to 3 dp is an editorial call for Martin; it is a one-character
  change to `dp` here when he makes it.
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) — 2026-09-04. First table: report9
#   Table 1.3 (cluster mechanistic coefficients, two record bases), the
#   phase-4 prototype of the pipeline-first number ledger.

TABLES = [
    {
        "id": "report9/Table21",
        "doc": 9,
        "table_name": "Table21",
        "caption": "Table 1.3 — cluster-centroid SSM coefficients on the full "
                   "record and the 100-month comparison window",
        "sources": {
            "fit":   "outputs/03_state_space_model/03_14_centroid_window_sensitivity.csv",
            "wells": "outputs/03_state_space_model/03_02_cluster_summary_table.csv",
        },
        "rows": {"source": "fit"},
        "header": ["Cluster", "Basis", "n", "β₁", "β₂", "−β₃", "p(β₃)",
                   "LCSC (%)", "R²"],
        "columns": [
            {"col": "Cluster_Label", "fmt": "text", "rowspan": True,
             "re": [r"^(C\d) \((.+)\)$", r"\1 \2"]},        # "C1 (Lake Edge)" -> "C1 Lake Edge"
            {"col": "basis", "fmt": "map",
             "map": {"full_record":       "full record ({n} mo)",
                     "comparison_window": "{window_months}-month window ({n} mo)"}},
            {"lookup": ("wells", "Cluster", "n_wells"), "fmt": "int"},
            {"col": "beta_1_recharge",         "fmt": "fixed",  "dp": 3},
            {"col": "beta_2_atmospheric_draw", "fmt": "fixed",  "dp": 3},
            {"col": "beta_3_drainage",         "fmt": "fixed",  "dp": 3},
            {"col": "pvalue_beta_3",           "fmt": "pvalue", "dp": 3},
            {"col": "LCSC_percent",            "fmt": "fixed",  "dp": 3},
            {"col": "R2",                      "fmt": "fixed",  "dp": 3},
        ],
    },
]


def by_id(table_id: str) -> dict:
    for t in TABLES:
        if t["id"] == table_id:
            return t
    raise KeyError(table_id)
