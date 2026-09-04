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
  doc         a chapter number (report_edits/odt/reportN.odt, edited in place)
              OR a repo-relative glob for a VERSIONED document
              ("docs/report/Newborough_Methods_Supplement_v*.odt"): the newest
              file is read and a --write goes to the next version's filename
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
  transpose   True — the CSV is one row per displayed COLUMN (a table of
              metrics across and statistics down). Each column spec becomes a
              table ROW with its `label` in the stub column, and each CSV row
              that survives the filter a table column, in CSV order; `header`
              is then the stub heading followed by one cell per CSV row.
  columns     one spec per displayed column, in display order:
      col       CSV column of the row source
      lookup    (alias, key_col, value_col) — take value_col from the row of
                `alias` whose key_col equals this row's key_col (a join); or
                {"source": alias, "key": key_col, "col": value_col,
                 "where": {col: value}} to pin the joined row further, with
                an optional "key_re": both keys are reduced to the pattern's
                first group before comparison, so a row can join its own
                variant in the same CSV ("C4 (Main Forest)" to
                "C4 (Main Forest) (corrected)" on ^(C\d)) — matching, not
                maths
      fmt       "text" | "int" | "fixed" | "pvalue" | "stars" | "map" |
                "template" | "ci" | "val_p"
      dp        decimal places for fixed / pvalue / ci
      sign      True — fixed / ci render a leading "+" on positives
      map       {csv_value: template} for fmt "map"; the template is
                str.format-ed over the row's fields
      template  for fmt "template": str.format-ed over the row's fields, and a
                NUMERIC spec formats the field as a number — "{lo:+.3f}",
                "{d:,.0f} m", "{v:+.1f} ± {se:.1f}" — with the Unicode minus;
                a field that is not a number takes a string spec
                ("{Variant:.1}" is its first character)
      cols      [lo, hi] for fmt "ci" -> "[lo, hi]" at dp places (`scale`
                and `sign` apply as for fixed); [value, p] for fmt "val_p"
      label     transpose only — the stub-column text of the row this spec makes
      re        [pattern, replacement] applied to the text after formatting,
                or a list of such pairs applied in order
      rowspan   True — the cell is written once per run of equal values and
                the continuation rows carry covered cells (a vertical merge)
      when      {col: value | [values]} — render the cell only on rows whose
                col is (in) the value; otherwise the cell shows `else`
      unless    the complement of `when`
      else      what a row excluded by when / unless shows (default "—")
      scale     fixed / ci — multiply the value before rendering, for a
                column the table shows with the opposite sign to its CSV, or
                in millimetres where the CSV holds metres
  rows.filter   {col: value | [values]} — keep rows whose col is (in) the value
  rows.require  [cols] — keep rows where the named columns are non-empty (one
                block of a multi-block CSV)
  rows.exclude  [{col: value | [values]}, ...] — drop a row that matches EVERY
                condition of any one clause (a table that shows all but one
                (variant, control) pair of a long CSV)
  rows.order    {"col": c, "values": [...]} — rows sorted by that list, stable

  A cell LibreOffice has typed as a number carries an office:value attribute
  beside its text; the engine reads it with the cell and keeps it equal to the
  text it writes, so a config need not know which cells are typed.

  fixed, pvalue and int pass a NON-NUMERIC cell through unchanged: a source
  may carry "30 / 66", "—" or an already-rendered "<0.001", and the table
  shows exactly that. stars maps a p-value to *** / ** / * / ns at
  0.001 / 0.01 / 0.05.

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

__version__ = "1.7.0"  # Hollingham (2026) — 2026-09-04. Methods Supplement
#   batch 2: ms/Table5 and ms/Table45 (Script 17 Sy by cluster, Approaches A
#   and B, the forest rows joined to their interception-corrected variants
#   via lookup key_re), ms/Table46 (Approach C rapid-event Sy) and ms/Table31
#   (Script 10h synthetic-extension ANCOVA variants, via rows.exclude and a
#   scaled ci). Needs table_gen 1.7.0.
# v1.6.0  # Hollingham (2026) — 2026-09-04. report9 Table 1.19
#   (ODF Table20) from 10c_forest_zone_correlations.csv via fmt "val_p" +
#   rows.require. Table 1.20
#   (ODF Table18) from 25_03_cluster_partition.csv; the climate + far-field
#   column reads Script 25's committed climate_plus_far_field_mm_yr (D-126).
# v1.4.0  # Hollingham (2026) — 2026-09-04. Batch 6: report9
#   Tables 1.16, 1.17 and 1.18, now that Script 26 1.9.0 emits their sources
#   (CHANGELOG 2026-09-04o). Table 1.17 is the first `transpose` entry (its
#   CSV is one row per metric; the table shows metrics across) and its
#   "value [lo, hi]" cells are `template`s; Table 1.18 is the first table
#   whose cells LibreOffice typed as numbers. Tables 1.14 and 1.20 remain
#   unconfigured (no pipeline source for their cells).
#
# v1.3.0  # Hollingham (2026) — 2026-09-04. Batch 5: five more
#   report9 tables (1.1, 1.2, 1.4c, 1.10, 1.15) — the span-wrapped and
#   fragmented cells batch 2 set aside, now that table_gen 1.3.0 reads them.
#   Uses the new `when` / `unless` / `else` and `scale` column options. Tables
#   1.14, 1.16, 1.17, 1.18 and 1.20 remain unconfigured: their cells are
#   AGGREGATES (window-end counts, r / CI / RMSE, band counts, a column sum)
#   that no pipeline CSV carries, and a config never computes.
#
# v1.2.1  # 2026-09-04. ms/Table12 to 3 dp throughout (Martin's
#   ruling, matching report9 Table 1.3); ms/Table71 regenerated under D-127.
#
# v1.2.0  # Hollingham (2026) — 2026-09-04. Batch 3: the Methods
#   Supplement, reached through the versioned-document resolver (`doc` is a
#   glob; table_gen reads the newest file and writes the next). Four tables.
#
# v1.1.0  # Hollingham (2026) — 2026-09-04. Batch 2: ten more
#   report9 tables (1.4a, 1.4b, 1.5, 1.6, 1.7, 1.8, 1.9, 1.11, 1.12, 1.13),
#   each configured to reproduce the table AS PUBLISHED. A column marked
#   "PRECISION" sits below three decimal places on a fixed float and is a
#   question for Martin, not a change made here.
#
# v1.0.1  # 2026-09-04. Table 1.3 LCSC and R² to 3 dp (Martin's ruling).
# v1.0.0  # Hollingham (2026) — 2026-09-04. First table: report9
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
    # ── 2026-09-04 batch 2: report9 Tables 1.4a/b, 1.5–1.9, 1.11–1.13 ──────────
    {
        "id": "report9/Table4",
        "doc": 9,
        "table_name": "Table4",
        "caption": "Table 1.4 (a) — SSM water-balance partition per cluster, m/month",
        "sources": {"wb": "outputs/16_water_balance/16_water_bal_table.csv"},
        "rows": {"source": "wb"},
        "header": ["Cluster", "Label", "LCSC (%)", "Recharge (m/month)",
                   "Atm. Draw (m/month)", "Drainage (m/month)",
                   "Total Loss (m/month)", "Residual (m/month)"],
        "columns": [
            {"fmt": "template", "template": "C{Cluster}"},
            {"col": "Label", "fmt": "text", "re": [r"^C\d \((.+)\)$", r"\1"]},
            {"col": "LCSC_pct",         "fmt": "fixed", "dp": 1},   # PRECISION: 1 dp as published
            {"col": "Recharge_m_month", "fmt": "fixed", "dp": 3},
            {"col": "ET_draw_m_month",  "fmt": "fixed", "dp": 3},
            {"col": "Drainage_m_month", "fmt": "fixed", "dp": 3},
            {"col": "Total_loss_m_month", "fmt": "fixed", "dp": 3},
            {"col": "Residual_m_month", "fmt": "fixed", "dp": 3, "sign": True},
        ],
    },
    {
        "id": "report9/Table5",
        "doc": 9,
        "table_name": "Table5",
        "caption": "Table 1.4 (b) — annual water-balance volumes per cluster, mm/yr",
        "sources": {"vol": "outputs/16_water_balance/16_water_bal_vol_table.csv"},
        "rows": {"source": "vol"},
        "header": ["Cluster", "Label", "P (mm/yr)", "I (mm/yr)", "P_net (mm/yr)",
                   "ET mid (mm/yr)", "Drainage mid (mm/yr)"],
        "columns": [
            {"fmt": "template", "template": "C{Cluster}"},
            {"col": "Label", "fmt": "text", "re": [r"^C\d \((.+)\)$", r"\1"]},
            {"col": "P_mm_yr",       "fmt": "fixed", "dp": 0},   # PRECISION: 0 dp as published
            {"col": "I_mm_yr",       "fmt": "fixed", "dp": 0},
            {"col": "P_net_mm_yr",   "fmt": "fixed", "dp": 0},
            {"col": "ET_mid_mm_yr",  "fmt": "fixed", "dp": 0},
            {"col": "Drain_mid_mm_yr", "fmt": "fixed", "dp": 0},
        ],
    },
    {
        "id": "report9/Table7",
        "doc": 9,
        "table_name": "Table7",
        "caption": "Table 1.5 — TLM vs SSM benchmark summary (Script 08)",
        # 08_lcsc_04_table3_benchmark_summary.csv IS this table row for row;
        # the declared 08_lcsc_model_stats.csv is the per-well file it summarises.
        "sources": {"bm": "outputs/08_model_benchmarking/08_lcsc_04_table3_benchmark_summary.csv"},
        "rows": {"source": "bm"},
        "header": ["Metric", "TLM", "SSM", "Improvement Δ"],
        "columns": [
            {"col": "Metric",              "fmt": "text", "re": [r"R2$", "R²"]},
            {"col": "Traditional_Model_A", "fmt": "fixed", "dp": 3},
            {"col": "StateSpace_Model_B",  "fmt": "fixed", "dp": 3},
            {"col": "Delta_B_minus_A",     "fmt": "fixed", "dp": 4},
        ],
    },
    {
        "id": "report9/Table8",
        "doc": 9,
        "table_name": "Table8",
        "caption": "Table 1.6 — per-era β₃ at the scraping treatment and control wells",
        "sources": {"era": "outputs/09_scraping_intervention/09_scrape_04b_beta3_era_summary.csv"},
        "rows": {"source": "era",
                 "order": {"col": "Well",
                           "values": ["CEH36", "CEH18", "CEH21", "CEH4", "CEH22"]}},
        "header": ["Well", "Role", "Era", "β₃", "95% CI", "p-value", "Sig"],
        "columns": [
            {"col": "Well", "fmt": "text"},
            {"col": "Role", "fmt": "map",
             "map": {"Impact (scraped)": "Treatment", "Impact (boundary)": "Treatment",
                     "Impact (coastal)": "Treatment", "Control (paired)": "Control",
                     "Control (coastal)": "Control"}},
            {"col": "Era",     "fmt": "text"},
            {"col": "beta_3",  "fmt": "fixed", "dp": 3},
            {"col": "CI_95",   "fmt": "text", "re": ["-", "−"]},   # CSV carries the bracket string
            {"col": "p_value", "fmt": "pvalue", "dp": 3},
            {"col": "Sig",     "fmt": "text"},
        ],
    },
    {
        "id": "report9/Table9",
        "doc": 9,
        "table_name": "Table9",
        "caption": "Table 1.7 — ANCOVA-BACI clearfell and scraping steps by control and zone",
        "sources": {"anc": "outputs/10_clearfell_baci/10a_01_ancova_comparison_table.csv"},
        "rows": {"source": "anc",
                 "filter": {"Control": ["Forest", "Climate", "Combined"]}},  # FarField rows not shown
        "header": ["Control", "Zone", "Clearfell step (m)", "95% CI (m)", "p", "Sig",
                   "Scraping step (m)", "Scraping p", "R²", "n"],
        "columns": [
            {"col": "Control", "fmt": "text"},
            {"col": "Zone",    "fmt": "text"},
            {"col": "Clearfell_step_m", "fmt": "fixed", "dp": 3, "sign": True},
            {"fmt": "ci", "cols": ["Clearfell_CI_lo_m", "Clearfell_CI_hi_m"], "dp": 3, "sign": True},
            {"col": "Clearfell_p",   "fmt": "pvalue", "dp": 3},
            {"col": "Clearfell_sig", "fmt": "text"},
            {"col": "Scraping_step_m", "fmt": "fixed", "dp": 3, "sign": True},
            {"col": "Scraping_p",    "fmt": "pvalue", "dp": 3},
            {"col": "R2",            "fmt": "fixed", "dp": 3},
            {"col": "N",             "fmt": "int"},
        ],
    },
    {
        "id": "report9/Table10",
        "doc": 9,
        "table_name": "Table10",
        "caption": "Table 1.8 — BACI corroboration of the coastal differential (Script 25)",
        "sources": {"cor": "outputs/25_coastal_gradient/25_04_baci_corroboration.csv"},
        "rows": {"source": "cor"},
        "header": ["Control tier", "Impact zone", "Coastal differential (mm yr⁻¹)",
                   "ξ", "SE", "p", "Absorbed drift (mm yr⁻¹)"],
        "columns": [
            {"col": "control_tier", "fmt": "map",
             "map": {"Forest": "Forest", "Climate": "Climate", "FarField": "Far-field"}},
            {"col": "impact_zone",  "fmt": "text"},
            {"col": "drift_scale",  "fmt": "fixed", "dp": 2, "sign": True},   # PRECISION: 2 dp as published
            {"col": "baci_coef",    "fmt": "fixed", "dp": 3, "sign": True},
            {"col": "baci_coef_se", "fmt": "fixed", "dp": 3},
            {"col": "baci_coef_p",  "fmt": "pvalue", "dp": 3},
            {"fmt": "template",
             "template": "{baci_absorbs_mm_yr:+.1f} ± {baci_absorbs_se_mm_yr:.1f}"},
        ],
    },
    {
        "id": "report9/Table11",
        "doc": 9,
        "table_name": "Table11",
        "caption": "Table 1.9 — summer-minimum shifts at the Impact and Edge wells vs the Forest control",
        "sources": {"sm": "outputs/10_clearfell_baci/10d_02_summer_minima_shifts.csv"},
        "rows": {"source": "sm",
                 "filter": {"Control": "Forest", "Tier": ["Impact", "Edge"]}},
        "header": ["Well", "Tier", "Control", "n pre", "n post", "Pre gap (m)",
                   "Post gap (m)", "Shift (mm)", "p", "Sig"],
        "columns": [
            {"col": "Well",    "fmt": "text"},
            {"col": "Tier",    "fmt": "text"},
            {"col": "Control", "fmt": "text"},
            {"col": "N_pre",   "fmt": "int"},
            {"col": "N_post",  "fmt": "int"},
            {"col": "Pre_mean_gap_m",  "fmt": "fixed", "dp": 3, "sign": True},
            {"col": "Post_mean_gap_m", "fmt": "fixed", "dp": 3, "sign": True},
            {"col": "Shift_mm", "fmt": "fixed", "dp": 0, "sign": True},
            {"col": "p_value",  "fmt": "pvalue", "dp": 3},
            {"col": "Sig",      "fmt": "text"},
        ],
    },
    {
        "id": "report9/Table13",
        "doc": 9,
        "table_name": "Table13",
        "caption": "Table 1.11 — before/after-clearfell SSM coefficients for the BACI network",
        "sources": {"cs": "outputs/10_clearfell_baci/10e_01_coefficient_shifts.csv"},
        "rows": {"source": "cs",
                 "filter": {"Tier": ["Impact", "Edge", "Forest Ctrl",
                                     "Coastal Ctrl", "Climate Ctrl"]}},   # Far-field Ctrl not shown
        "header": ["Well", "Tier", "β₁ before", "β₁ after", "Δβ₁", "β₂ before",
                   "β₂ after", "Δβ₂", "β₃ before", "β₃ after", "Δβ₃"],
        "columns": [
            {"col": "Well", "fmt": "text"},
            {"col": "Tier", "fmt": "text"},
            {"col": "b1_before", "fmt": "fixed", "dp": 3},
            {"col": "b1_after",  "fmt": "fixed", "dp": 3},
            {"col": "db1",       "fmt": "fixed", "dp": 3, "sign": True},
            {"col": "b2_before", "fmt": "fixed", "dp": 3},
            {"col": "b2_after",  "fmt": "fixed", "dp": 3},
            {"col": "db2",       "fmt": "fixed", "dp": 3, "sign": True},
            {"col": "b3_before", "fmt": "fixed", "dp": 4},
            {"col": "b3_after",  "fmt": "fixed", "dp": 4},
            {"col": "db3",       "fmt": "fixed", "dp": 4, "sign": True},
        ],
    },
    {
        "id": "report9/Table14",
        "doc": 9,
        "table_name": "Table14",
        "caption": "Table 1.12 — winter transfer functions per block (Script 11)",
        "sources": {"tf": "outputs/11_forecasting_thresholds/11_forecast_winter_transfer_functions.csv"},
        "rows": {"source": "tf"},
        "header": ["Block", "Equation", "R²", "n", "p(P_winter)", "p(h_min)"],
        "columns": [
            {"col": "Block", "fmt": "map",
             "map": {"Lake_Edge": "Lake Edge (C1)", "Eastern_Block": "Dune (C2)",
                     "Western_Block": "Western Residual (C3)", "Forest": "Main Forest (C4)",
                     "Coastal_Forest": "Coastal Forest (C5)"}},
            {"fmt": "template",
             "template": "h_peak = {a_P_winter:.5f}·P_winter {a_h_min:+.3f}·h_min {intercept:+.3f}",
             "re": [r" ([+−])(\d)", r" \1 \2"]},          # "x −0.134·h" -> "x − 0.134·h"
            {"col": "R2", "fmt": "fixed", "dp": 2},        # PRECISION: 2 dp as published
            {"col": "n_hydrological_years", "fmt": "int"},
            {"col": "p_value_P_winter", "fmt": "pvalue", "dp": 3},
            {"col": "p_value_h_min",    "fmt": "pvalue", "dp": 3},
        ],
    },
    {
        "id": "report9/Table15",
        "doc": 9,
        "table_name": "Table15",
        "caption": "Table 1.13 — summer transfer functions per block (Script 11)",
        "sources": {"tf": "outputs/11_forecasting_thresholds/11_forecast_summer_transfer_functions.csv"},
        "rows": {"source": "tf"},
        "header": ["Block", "Equation", "R²", "p(P_summer)", "p(h_max)"],
        "columns": [
            {"col": "Block", "fmt": "map",
             "map": {"Lake_Edge": "Lake Edge (C1)", "Eastern_Block": "Dune (C2)",
                     "Western_Block": "Western Residual (C3)", "Forest": "Forest (C4)",
                     "Coastal_Forest": "Coastal Forest (C5)"}},
            {"fmt": "template",
             "template": "h_min = {a_P_summer:.5f}·P_summer {a_h_max_winter:+.3f}·h_max_winter {intercept:+.3f}",
             "re": [r" ([+−])(\d)", r" \1 \2"]},
            {"col": "R2", "fmt": "fixed", "dp": 3},
            {"col": "p_value_P_summer",     "fmt": "pvalue", "dp": 3},
            {"col": "p_value_h_max_winter", "fmt": "pvalue", "dp": 3},
        ],
    },
    # ── 2026-09-04 batch 3: Methods Supplement (versioned; resolved by glob) ──
    {
        "id": "ms/Table12",
        "doc": "docs/report/Newborough_Methods_Supplement_v*.odt",
        "table_name": "Table12",
        "caption": "Methods Supplement — cluster-centroid SSM coefficients (Script 03)",
        "sources": {"co": "outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv"},
        "rows": {"source": "co"},
        "header": ["Cluster", "n", "β₁", "β₂", "β₃", "R²", "LCSC"],
        "columns": [
            {"col": "Cluster_Label", "fmt": "text"},
            {"col": "n", "fmt": "int"},
            {"col": "beta_1_recharge",         "fmt": "fixed", "dp": 3},   # 3 dp — Martin, 2026-09-04 (as report9 Table 1.3)
            {"col": "beta_2_atmospheric_draw", "fmt": "fixed", "dp": 3},
            {"col": "beta_3_drainage",         "fmt": "fixed", "dp": 3},
            {"col": "R2",                      "fmt": "fixed", "dp": 3},
            {"col": "LCSC_percent",            "fmt": "fixed", "dp": 3},
        ],
    },
    {
        "id": "ms/Table42",
        "doc": "docs/report/Newborough_Methods_Supplement_v*.odt",
        "table_name": "Table42",
        "caption": "Methods Supplement — depth-coupled PET benchmark per cluster (Script 15)",
        "sources": {"bm": "outputs/15_depth_dependent_pet/15_03_benchmark_table.csv",
                    "bp": "outputs/15_depth_dependent_pet/15_04_best_params.csv"},
        "rows": {"source": "bm"},
        "header": ["Cluster", "SSM NSE", "Depth-coupled NSE", "Δ NSE", "Best κ (m⁻¹)",
                   "Mean upstand (m)"],
        "columns": [
            {"col": "Label", "fmt": "text", "re": [r"^(C\d) \((.+)\)$", r"\1 \2"]},
            {"col": "SSM_Iterative_NSE", "fmt": "fixed", "dp": 2},   # PRECISION: 2 dp as published
            {"col": "DDP_Iterative_NSE", "fmt": "fixed", "dp": 2},   # PRECISION
            {"col": "Delta_NSE",         "fmt": "fixed", "dp": 2, "sign": True},   # PRECISION
            {"col": "Best_Kappa_m-1",    "fmt": "fixed", "dp": 2},   # PRECISION
            {"lookup": ("bp", "Cluster", "Mean_Upstand_m"), "fmt": "fixed", "dp": 2},   # PRECISION
        ],
    },
    {
        "id": "ms/Table71",
        "doc": "docs/report/Newborough_Methods_Supplement_v*.odt",
        "table_name": "Table71",
        "caption": "Methods Supplement — spring transfer functions per cluster (Script 11)",
        "sources": {"tf": "outputs/11_forecasting_thresholds/11_forecast_spring_transfer_functions.csv"},
        "rows": {"source": "tf"},
        "header": ["Cluster", "β(h_max, winter)", "β(P_win→spr)", "β(PET_win→spr)",
                   "Intercept (m)", "R²", "n"],
        "columns": [
            {"col": "Block", "fmt": "map",
             "map": {"Lake_Edge": "C1 Lake Edge", "Eastern_Block": "C2 Dune",
                     "Western_Block": "C3 Western Residual", "Forest": "C4 Main Forest",
                     "Coastal_Forest": "C5 Coastal Forest"}},
            {"col": "alpha_W_h_max_winter", "fmt": "fixed", "dp": 3, "sign": True},
            {"col": "a_P_win_to_spr",       "fmt": "fixed", "dp": 5, "sign": True},
            {"col": "a_PET_win_to_spr",     "fmt": "fixed", "dp": 5, "sign": True},
            {"col": "intercept",            "fmt": "fixed", "dp": 3, "sign": True},
            {"col": "R2",                   "fmt": "fixed", "dp": 3},
            {"col": "n_hydrological_years", "fmt": "int"},
        ],
    },
    {
        "id": "ms/Table73",
        "doc": "docs/report/Newborough_Methods_Supplement_v*.odt",
        "table_name": "Table73",
        "caption": "Methods Supplement — UKCP18 MSL5 projections per cluster (Script 26b)",
        "sources": {"pj": "outputs/26b_van_willegen_msl_projections/26b_msl5_ukcp18_projection_summary.csv"},
        "rows": {"source": "pj", "filter": {"scenario": "2050s"}},   # one row per cluster; 2080s by lookup
        "header": ["Cluster", "β₁", "β₂", "ΔMSL5 2050s (m)", "ΔMSL5 2080s (m)"],
        "columns": [
            {"col": "cluster_label", "fmt": "text", "re": [r"^(C\d) \((.+)\)$", r"\1 \2"]},
            {"col": "beta_1_recharge",         "fmt": "fixed", "dp": 2},   # PRECISION: 2 dp as published
            {"col": "beta_2_atmospheric_draw", "fmt": "fixed", "dp": 2},   # PRECISION
            {"col": "msl5_shift_mean_m", "fmt": "fixed", "dp": 3, "sign": True},
            {"lookup": {"source": "pj", "key": "cluster_id", "col": "msl5_shift_mean_m",
                        "where": {"scenario": "2080s"}},
             "fmt": "fixed", "dp": 3, "sign": True},
        ],
    },
    # ── 2026-09-04 batch 5: report9 Tables 1.1, 1.2, 1.4c, 1.10, 1.15 ─────────
    {
        "id": "report9/Table1",
        "doc": 9,
        "table_name": "Table1",
        "caption": "Table 1.1 — annual climate summary, RAF Valley (Script 00)",
        "sources": {"cl": "outputs/00_climate_summary/00_01_annual_climate_summary_short.csv"},
        "rows": {"source": "cl"},
        "header": ["Year", "Annual P mm", "Annual PET mm", "Months complete", "P PET ratio"],
        "columns": [
            {"col": "Year", "fmt": "text"},
            {"col": "Annual_P_mm",   "fmt": "fixed", "dp": 1},   # PRECISION: 1 dp as published (mm totals)
            {"col": "Annual_PET_mm", "fmt": "fixed", "dp": 1},   # PRECISION
            # the mean row's "12" means "complete years only"; the table leaves it blank
            {"col": "Months_complete", "fmt": "int",
             "unless": {"Year": "Long-term mean"}, "else": ""},
            # no ratio is shown for a partial year (the caption says so)
            {"col": "P_PET_ratio", "fmt": "fixed", "dp": 2,     # PRECISION: 2 dp as published
             "when": {"Months_complete": "12.0"}, "else": "—"},
        ],
    },
    {
        "id": "report9/Table2",
        "doc": 9,
        "table_name": "Table2",
        "caption": "Table 1.2 — per-well seasonal amplitude by cluster, pre- vs post-2018 (Script 02)",
        "sources": {"am": "outputs/02_clustering/02_09_cluster_amplitude_summary.csv"},
        "rows": {"source": "am"},
        "header": ["Cluster", "n", "Pre-2018 (m)", "Post-2018 (m)", "Δ pre→post (%)",
                   "Climate-normalized Δ (%)"],
        "columns": [
            {"col": "cluster_name", "fmt": "text", "re": [r"^(C\d) \((.+)\)$", r"\1 \2"]},
            {"col": "n_wells", "fmt": "int"},
            {"col": "median_p90_p10_pre2018",  "fmt": "fixed", "dp": 2},   # PRECISION: 2 dp as published
            {"col": "median_p90_p10_post2018", "fmt": "fixed", "dp": 2},   # PRECISION
            # the CSV stores DAMPING (positive = amplitude reduced); the table
            # shows the change pre→post, so the sign flips (caption: negative =
            # damping, positive = amplification)
            {"col": "amplitude_damping_pct", "fmt": "fixed", "dp": 0, "sign": True,
             "scale": -1, "re": [r"$", "%"]},
            {"col": "amplitude_damping_pct_climnorm", "fmt": "fixed", "dp": 0, "sign": True,
             "scale": -1, "re": [r"$", "%"]},
        ],
    },
    {
        "id": "report9/Table6",
        "doc": 9,
        "table_name": "Table6",
        "caption": "Table 1.4 (c) — WTF specific-yield estimates by cluster (Script 17)",
        "sources": {"sy": "outputs/17_wtf_specific_yield/17_wtf_01_sy_estimates.csv"},
        "rows": {"source": "sy"},
        "header": ["Cluster", "n events", "Sy assumed", "WTF event-median", "OLS-winter",
                   "Q25", "Q75", "Interception corrected?"],
        "columns": [
            {"col": "Cluster", "fmt": "text", "re": [r"^(C\d) \(([^)]+)\)", r"\1 \2"]},   # "C4 (Main Forest) (corrected)" -> "C4 Main Forest (corrected)"
            {"col": "Sy_event_n",  "fmt": "int"},
            {"col": "Sy_assumed",  "fmt": "fixed", "dp": 2},   # PRECISION: the assumed constants, as published
            {"col": "Sy_event_median", "fmt": "fixed", "dp": 3},
            {"col": "Sy_OLS_winter",   "fmt": "fixed", "dp": 3,
             "when": {"Corrected": "False"}, "else": "—"},    # no OLS fit on the corrected rows
            {"col": "Sy_event_Q25",    "fmt": "fixed", "dp": 3},
            {"col": "Sy_event_Q75",    "fmt": "fixed", "dp": 3},
            {"col": "Corrected", "fmt": "map",
             "map": {"False": "No", "True": "Yes — Freeman (2008)"}},
        ],
    },
    {
        "id": "report9/Table12",
        "doc": 9,
        "table_name": "Table12",
        "caption": "Table 1.10 — pooled mixed-effects clearfell step by tier vs the Forest control (Script 10d)",
        "sources": {"mm": "outputs/10_clearfell_baci/10d_03_mixed_model_results.csv"},
        "rows": {"source": "mm",
                 "filter": {"Control": "Forest",
                            "Tier": ["Impact", "Edge", "Forest Ctrl",
                                     "Coastal Ctrl", "Climate Ctrl"]}},   # Far-field Ctrl and the Climate-control block not shown
        "header": ["Control", "Tier", "Model", "Clearfell coef (m)", "SE", "p", "n obs"],
        "columns": [
            {"col": "Control", "fmt": "text"},
            {"col": "Tier",    "fmt": "text"},
            {"col": "Model", "fmt": "map",
             "map": {"OLS (single well)": "OLS (single well)",
                     "Mixed-effects (random intercept)": "Mixed-effects"}},
            {"col": "Clearfell_coef_m", "fmt": "fixed", "dp": 3, "sign": True},
            {"col": "Clearfell_SE_m",   "fmt": "fixed", "dp": 3},
            {"col": "Clearfell_p",      "fmt": "pvalue", "dp": 3},
            {"col": "N",                "fmt": "int"},
        ],
    },
    {
        "id": "report9/Table17",
        "doc": 9,
        "table_name": "Table17",
        "caption": "Table 1.15 — cluster-specific P_flood linear forms and recharge-horizon Σ P_clim (Script 11)",
        "sources": {"pf": "outputs/11_forecasting_thresholds/11_forecast_pflood_summary.csv"},
        "rows": {"source": "pf"},
        "header": ["Cluster", "Label", "Horizon", "P_flood equation (mm)", "Σ P_clim (mm)"],
        "columns": [
            {"col": "Cluster", "fmt": "text"},
            {"col": "Label", "fmt": "text", "re": [r"^C\d \((.+)\)$", r"\1"]},
            # the horizon label is built from peak_month and horizon_n_months,
            # not the CSV's `horizon` string, which renders January as "M1"
            {"col": "peak_month", "fmt": "map",
             "map": {"1": "Oct–Jan ({horizon_n_months} mo)",
                     "2": "Oct–Feb ({horizon_n_months} mo)"}},
            {"fmt": "template", "template": "{slope_A:.2f}·d + {intercept_B:.2f}"},   # PRECISION: 2 dp as published
            {"col": "P_clim_mm", "fmt": "fixed", "dp": 0},   # PRECISION: 0 dp as published (mm)
        ],
    },
    # ── 2026-09-04 batch 6: report9 Tables 1.16, 1.17, 1.18 (Script 26 1.9.0) ──
    {
        "id": "report9/Table19",
        "doc": 9,
        "table_name": "Table19",
        "caption": "Table 1.16 — cluster-mean MSL5 at the latest window-end, with counts of "
                   "window-ends below the SD15b / SD16 thresholds (Script 26)",
        "sources": {"th": "outputs/26_van_willegen_msl/26_msl_5yr_cluster_threshold_summary.csv"},
        "rows": {"source": "th"},
        # the header hard-types the window-end year the CSV carries as
        # window_end_current: a later window-end fails this assertion rather
        # than refreshing the cells under a stale "(2025)"
        "header": ["Cluster", "n wells (2025)", "Current MSL5 (m)", "below SD15b", "below SD16"],
        "columns": [
            {"col": "cluster_label", "fmt": "text", "re": [r"^(C\d) \((.+)\)$", r"\1 \2"]},   # "C4 (Main Forest)" -> "C4 Main Forest"
            {"col": "n_wells_current",       "fmt": "int"},
            {"col": "MSL5_current_m_bg",     "fmt": "fixed", "dp": 3},
            {"col": "n_windows_below_SD15b", "fmt": "int"},
            {"col": "n_windows_below_SD16",  "fmt": "int"},
        ],
    },
    {
        "id": "report9/T140087",
        "doc": 9,
        "table_name": "T140087",
        "caption": "Table 1.17 — between-well prediction of mean Ellenberg-F by observed MSL5 "
                   "and by the equilibrium wetness index (Script 26)",
        "sources": {"ebf": "outputs/26_van_willegen_msl/26_ebf_prediction_summary.csv"},
        # the CSV is one row per METRIC and the table shows metrics ACROSS with
        # the statistics down, so it is transposed: each column spec below is a
        # table row (its `label` the stub cell) and each surviving CSV row a
        # table column. EWI_spring is not shown — the table carries the annual
        # basis adopted in Section 3.7.6.
        "rows": {"source": "ebf", "filter": {"metric": ["MSL5", "EWI_annual"]}},
        "transpose": True,
        "header": ["", "MSL5", "Equilibrium wetness index "],   # the trailing space is as typed
        "columns": [
            {"label": "r [95% CI]", "fmt": "template",
             "template": "{pearson_r:+.2f} [{r_ci_lo:.2f}, {r_ci_hi:.2f}]"},           # PRECISION: 2 dp as published
            {"label": "RMSE (Ellenberg-F units)", "fmt": "template",
             "template": "{rmse_ebf:.3f} [{rmse_ci_lo:.2f}, {rmse_ci_hi:.2f}]"},       # PRECISION: CI bounds at 2 dp as published
        ],
    },
    {
        "id": "report9/T140087_1",
        "doc": 9,
        "table_name": "T140087_1",
        "caption": "Table 1.18 — Ellenberg-F prediction accuracy by match band, MSL5 versus "
                   "the equilibrium wetness index (Script 26)",
        "sources": {"bd": "outputs/26_van_willegen_msl/26_ebf_band_summary.csv"},
        "rows": {"source": "bd"},
        "header": ["Match band", "Absolute error (Ellenberg-F units)", "MSL5 (wells)", "EWI (wells)"],
        "columns": [
            {"col": "band_label", "fmt": "text", "re": [r"^(\w) \((.+)\)$", r"\1 — \2"]},   # "A (excellent)" -> "A — excellent"
            {"col": "abs_error_ebf_range", "fmt": "text",
             "re": [[r"^<= ", "≤ "], [r"^(\d\.\d+)-(\d\.\d+)$", r"\1–\2"]]},     # "<= 0.15" -> "≤ 0.15"; "0.15-0.30" -> en dash
            # the count cells are typed as numbers in the ODT (office:value);
            # table_gen keeps the attribute equal to the text
            {"col": "n_wells_MSL5", "fmt": "int"},
            {"col": "n_wells_EWI",  "fmt": "int"},
        ],
    },
    {
        "id": "report9/Table18",
        "doc": 9,
        "table_name": "Table18",
        "caption": "Table 1.20 - per-cluster decomposition of the summer-minimum decline "
                   "under the forest-free linear-capped panel regression (Script 25)",
        "sources": {"dec": "outputs/25_coastal_gradient/25_03_cluster_partition.csv"},
        "rows": {"source": "dec"},
        "header": ["Cluster", "n in fit", "Mean dist. to coast",
                   "Observed, balanced (mm/yr)", "Climate + far-field (mm/yr)",
                   "Coastal (mm/yr)", "Unexplained (mm/yr)"],
        "columns": [
            {"col": "cluster_label", "fmt": "text"},
            {"col": "n_wells", "fmt": "int"},
            {"fmt": "template", "template": "{mean_dist_coast_m:.0f} m"},
            {"col": "observed_balanced_annual_mean_mm_yr", "fmt": "fixed", "dp": 2},
            # identified climate + far-field component, emitted by Script 25
            # (D-126: the script emits derived quantities; the config never computes)
            {"col": "climate_plus_far_field_mm_yr", "fmt": "fixed", "dp": 2, "sign": True},
            {"col": "coastal_gradient_mm_yr", "fmt": "fixed", "dp": 2},
            {"col": "unexplained_mm_yr", "fmt": "fixed", "dp": 2},
        ],
    },
    {
        "id": "report9/Table20",
        "doc": 9,
        "table_name": "Table20",
        "caption": "Table 1.19 - per-well spatial predictors of SSM coefficient "
                   "variation in the forest zone (Script 10c)",
        "sources": {"fz": "outputs/10c_forest_zone_analysis/10c_forest_zone_correlations.csv"},
        # the CSV packs the correlation block and an R2 block (blank separator);
        # require r_vs_Elevation non-empty to take the three correlation rows only.
        "rows": {"source": "fz", "require": ["r_vs_Elevation"]},
        "header": ["Coefficient", "vs Elevation r (p)", "vs Dist. ridge r (p)",
                   "vs Easting r (p)"],
        "columns": [
            {"col": "Coefficient", "fmt": "map", "map": {
                "β₁_recharge": "β₁ (recharge)",
                "β₂_atm_draw": "β₂ (atm. draw)",
                "β₃_drainage": "β₃ (drainage)"}},
            {"fmt": "val_p", "cols": ["r_vs_Elevation", "p_vs_Elevation"], "dp": 3},
            {"fmt": "val_p", "cols": ["r_vs_Dist_from_ridge", "p_vs_Dist_from_ridge"], "dp": 3},
            {"fmt": "val_p", "cols": ["r_vs_Easting", "p_vs_Easting"], "dp": 3},
        ],
    },
    # ── 2026-09-04 Methods Supplement batch 2: Tables 5, 45, 46, 31 ──────────
    {
        "id": "ms/Table5",
        "doc": "docs/report/Newborough_Methods_Supplement_v*.odt",
        "table_name": "Table5",
        "caption": "Methods Supplement — specific yield, two values per cluster: the "
                   "assumed Sy and the WTF Approaches A and B (Script 17)",
        "sources": {"sy": "outputs/17_wtf_specific_yield/17_wtf_01_sy_estimates.csv"},
        # one row per cluster: the forest clusters are shown on their
        # interception-corrected (Approach B) rows, whose Approach A cells are
        # empty in the CSV and are taken from the uncorrected row by a lookup
        # keyed on the cluster id (key_re) — no value is computed here
        "rows": {"source": "sy",
                 "filter": {"Cluster": ["C1 (Lake Edge)", "C2 (Dune)", "C3 (Western Residual)",
                                        "C4 (Main Forest) (corrected)",
                                        "C5 (Coastal Forest) (corrected)"]}},
        "header": ["Cluster", "Sy assumed", "Approach A (OLS)", "Approach B (event median)"],
        "columns": [
            {"col": "Cluster", "fmt": "text",
             "re": [[r" \(corrected\)$", ""], [r"^(C\d) \((.+)\)$", r"\1 \2"]]},   # "C4 (Main Forest) (corrected)" -> "C4 Main Forest"
            {"col": "Sy_assumed", "fmt": "fixed", "dp": 2},   # the assumed constants, as published
            {"lookup": {"source": "sy", "key": "Cluster", "key_re": r"^(C\d)",
                        "col": "Sy_OLS_winter", "where": {"Corrected": "False"}},
             "fmt": "fixed", "dp": 3},
            {"col": "Corrected", "fmt": "map",
             "map": {"False": "{Sy_event_median:.3f}",
                     "True":  "{Sy_event_median:.3f} (corr)"}},
        ],
    },
    {
        "id": "ms/Table45",
        "doc": "docs/report/Newborough_Methods_Supplement_v*.odt",
        "table_name": "Table45",
        "caption": "Methods Supplement — WTF specific yield by cluster, Approach A (OLS-winter) "
                   "and Approach B (event median) (Script 17)",
        "sources": {"sy": "outputs/17_wtf_specific_yield/17_wtf_01_sy_estimates.csv"},
        # as ms/Table5: forest clusters on their corrected rows; the four
        # Approach A cells come from the uncorrected row via key_re
        "rows": {"source": "sy",
                 "filter": {"Cluster": ["C1 (Lake Edge)", "C2 (Dune)", "C3 (Western Residual)",
                                        "C4 (Main Forest) (corrected)",
                                        "C5 (Coastal Forest) (corrected)"]}},
        "header": ["Cluster", "Sy (A, OLS)", "SE", "R²", "n", "Sy (B, event)", "IQR", "n events"],
        "columns": [
            {"col": "Cluster", "fmt": "text", "re": [r" \(corrected\)$", ""]},   # "C4 (Main Forest) (corrected)" -> "C4 (Main Forest)"
            {"lookup": {"source": "sy", "key": "Cluster", "key_re": r"^(C\d)",
                        "col": "Sy_OLS_winter", "where": {"Corrected": "False"}},
             "fmt": "fixed", "dp": 3},
            {"lookup": {"source": "sy", "key": "Cluster", "key_re": r"^(C\d)",
                        "col": "Sy_OLS_SE", "where": {"Corrected": "False"}},
             "fmt": "fixed", "dp": 3},
            {"lookup": {"source": "sy", "key": "Cluster", "key_re": r"^(C\d)",
                        "col": "Sy_OLS_R2", "where": {"Corrected": "False"}},
             "fmt": "fixed", "dp": 3},
            {"lookup": {"source": "sy", "key": "Cluster", "key_re": r"^(C\d)",
                        "col": "Sy_OLS_n", "where": {"Corrected": "False"}},
             "fmt": "int"},
            {"col": "Corrected", "fmt": "map",
             "map": {"False": "{Sy_event_median:.3f}",
                     "True":  "{Sy_event_median:.3f} (corr)"}},
            {"fmt": "ci", "cols": ["Sy_event_Q25", "Sy_event_Q75"], "dp": 3},
            {"col": "Sy_event_n", "fmt": "int"},
        ],
    },
    {
        "id": "ms/Table46",
        "doc": "docs/report/Newborough_Methods_Supplement_v*.odt",
        "table_name": "Table46",
        "caption": "Methods Supplement — WTF specific yield by cluster, Approach C "
                   "(rapid recharge events, Crosbie et al. 2005) (Script 17)",
        "sources": {"sy": "outputs/17_wtf_specific_yield/17_wtf_01_sy_estimates.csv"},
        # Approach C attaches to the uncorrected (base) cluster row only; the
        # "(corr)" suffix marks the forest clusters, whose Approach C recharge
        # is interception-corrected in Script 17 (FOREST_CIDS). The CSV carries
        # no flag for that — its Corrected column is the A/B row identity — so
        # the map names the two clusters; a Sy_rapid_corrected column from
        # Script 17 would let this read from the file instead.
        "rows": {"source": "sy", "filter": {"Corrected": "False"}},
        "header": ["Cluster", "Sy (per-well median)", "95% CI", "n"],
        "columns": [
            {"col": "Cluster", "fmt": "text", "re": [r"^(C\d) \((.+)\)$", r"\1 \2"]},   # "C1 (Lake Edge)" -> "C1 Lake Edge"
            {"col": "Cluster", "fmt": "map",
             "map": {"C1 (Lake Edge)":        "{Sy_rapid_median:.3f}",
                     "C2 (Dune)":             "{Sy_rapid_median:.3f}",
                     "C3 (Western Residual)": "{Sy_rapid_median:.3f}",
                     "C4 (Main Forest)":      "{Sy_rapid_median:.3f} (corr)",
                     "C5 (Coastal Forest)":   "{Sy_rapid_median:.3f} (corr)"}},
            {"fmt": "ci", "cols": ["Sy_rapid_CI_lo", "Sy_rapid_CI_hi"], "dp": 3},
            {"col": "Sy_rapid_n", "fmt": "int"},
        ],
    },
    {
        "id": "ms/Table31",
        "doc": "docs/report/Newborough_Methods_Supplement_v*.odt",
        "table_name": "Table31",
        "caption": "Methods Supplement — synthetic-extension ANCOVA-BACI variants A, B, C "
                   "against the Forest and Climate controls (Script 10h)",
        "sources": {"an": "outputs/10_clearfell_baci/10h_02_ancova_comparison_table.csv"},
        # Forest and Climate controls only (Combined is not shown), and the
        # table omits Variant C's Climate row — C is WMC3 alone and its Climate
        # contrast is 10a's, quoted in the prose; the five rows are as published
        "rows": {"source": "an",
                 "filter": {"Control": ["Forest", "Climate"]},
                 "exclude": [{"Variant": "C (WMC3 only)", "Control": "Climate"}]},
        "header": ["Variant", "Zone", "Step (mm)", "95% CI", "p"],
        "columns": [
            # the variant label is written in full on its Forest row and
            # reduced to the letter on the Climate row beneath it, as
            # published: "A (WMC3+FE1+FE2)" -> "A (WMC3 + FE1 + FE2)" / "A"
            {"col": "Control", "fmt": "map",
             "map": {"Forest": "{Variant}", "Climate": "{Variant:.1}"},
             "re": [[r"\+", " + "], [r" only\)", ")"]]},
            {"col": "Control", "fmt": "text"},
            {"col": "Clearfell_step_m", "fmt": "fixed", "dp": 0, "sign": True, "scale": 1000},
            {"fmt": "ci", "cols": ["Clearfell_CI_lo_m", "Clearfell_CI_hi_m"],
             "dp": 0, "sign": True, "scale": 1000},
            {"col": "Clearfell_p", "fmt": "pvalue", "dp": 3, "re": [r"^<", "< "]},   # "< 0.001" with the space, as published
        ],
    },
]


def by_id(table_id: str) -> dict:
    for t in TABLES:
        if t["id"] == table_id:
            return t
    raise KeyError(table_id)
