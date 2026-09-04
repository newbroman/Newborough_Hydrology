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
  columns     one spec per displayed column, in display order:
      col       CSV column of the row source
      lookup    (alias, key_col, value_col) — take value_col from the row of
                `alias` whose key_col equals this row's key_col (a join); or
                {"source": alias, "key": key_col, "col": value_col,
                 "where": {col: value}} to pin the joined row further
      fmt       "text" | "int" | "fixed" | "pvalue" | "stars" | "map" |
                "template" | "ci"
      dp        decimal places for fixed / pvalue / ci
      sign      True — fixed / ci render a leading "+" on positives
      map       {csv_value: template} for fmt "map"; the template is
                str.format-ed over the row's fields
      template  for fmt "template": str.format-ed over the row's fields, and a
                NUMERIC spec formats the field as a number — "{lo:+.3f}",
                "{d:,.0f} m", "{v:+.1f} ± {se:.1f}" — with the Unicode minus
      cols      [lo, hi] for fmt "ci" -> "[lo, hi]" at dp places
      re        [pattern, replacement] applied to the text after formatting
      rowspan   True — the cell is written once per run of equal values and
                the continuation rows carry covered cells (a vertical merge)
  rows.filter   {col: value | [values]} — keep rows whose col is (in) the value
  rows.order    {"col": c, "values": [...]} — rows sorted by that list, stable

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

__version__ = "1.2.0"  # Hollingham (2026) — 2026-09-04. Batch 3: the Methods
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
            {"col": "beta_1_recharge",         "fmt": "fixed", "dp": 2},   # PRECISION: 2 dp as published
            {"col": "beta_2_atmospheric_draw", "fmt": "fixed", "dp": 2},   # PRECISION: 2 dp as published
            {"col": "beta_3_drainage",         "fmt": "fixed", "dp": 3},
            {"col": "R2",                      "fmt": "fixed", "dp": 3},
            {"col": "LCSC_percent",            "fmt": "fixed", "dp": 1},   # PRECISION: 1 dp as published
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
]


def by_id(table_id: str) -> dict:
    for t in TABLES:
        if t["id"] == table_id:
            return t
    raise KeyError(table_id)
