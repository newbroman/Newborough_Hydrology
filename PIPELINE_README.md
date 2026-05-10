# Newborough Warren Groundwater Analysis Pipeline
## Script Input/Output Reference

This document describes the data flow between all pipeline scripts: which files each script reads, which it produces, and which outputs feed into the paper as figures or tables, or into downstream scripts.

**Generated from automated I/O audit of `src/` against GitHub `main`.**

**Run order:** 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 (suite a–e) → 10 (suite a–g) → 11 → 11b → 00 → 14 → 12 → 13 → 15 → 17 → 16 → 18 → 19 → 20 → 21 → 22 → 23 → 24

**27 pipeline steps across 11 phases.**

Script 09 is a modular suite orchestrated by `run_09_scraping.py` (09a → 09b → 09c → 09d → 09e). Script 10 is a modular suite orchestrated by `run_10_clearfell.py` (10a → 10b → 10c → 10d → 10e → 10f → 10g → 10h). All sub-modules can be run independently provided their upstream Phase 1–2 outputs exist.

## Two-pass execution (recommended for new datasets)

Two scripts in Phase 3 read Specific-Yield (Sy) values that are produced later in the pipeline:

| Script | Step | Reads (via `scraping_common`) | Producer | Producer step |
|---|---|---|---|---|
| `09b_scraping_propagation.py` | 10 | `load_cluster_params()` → Script 17 Sy | Script 17 | 18 |
| `09d_scenario_comparison.py`  | 12 | `load_cluster_params()` → Script 17 Sy | Script 17 | 18 |
| `21_forestry_scenarios.py`    | 23 | `load_cluster_params()` → Script 17 Sy | Script 17 | 18 |

All three scripts load cluster parameters (β, Sy, h_disp) via
`scraping_common.load_cluster_params()`, which consolidates from Scripts 01,
03, and 17. On a fresh first-pass run, Script 17 hasn't produced its Sy
estimates yet, so `load_cluster_params()` will fail. Scripts 09b's summer
scenario has a local `SY_FALLBACK = 0.20` for this case.

**For accurate scenario figures on a new dataset, run the pipeline twice:**

```
# pass 1 — fits the SSM, computes Sy, but 09b/09d use Sy fallbacks
python run_analysis.py --full

# pass 2 — re-runs Phase 3 with canonical Sy from Script 17
python run_analysis.py --from 9
```

## Other ordering constraints

- Script 17 (WTF Sy) must run before Script 16 (water balance — uses cluster Sy).
- Script 18 (WTF spatial) must run before Script 19 (spatial groundwater — uses well-level Sy).
- Script 11b requires outputs from Scripts 11 (P_flood equations) and 06 (extended Pearson audit).
- Script 21 requires `03_regional_averages_maod.csv` from Script 03, plus Scripts 10a (BACI step) and 10e (β₂ multiplier).
- Script 14 requires `00_well_network_summary.csv` from Script 00 and `02_cluster_stats.csv` from Script 02.

## Consolidated pipeline parameters (`pipeline_params.py`)

All derived values needed by downstream scenario scripts are consolidated
into a single CSV: `outputs/01_data_prep/pipeline_scenario_params.csv`.

Script 01 writes this file at the end of data preparation, opportunistically
reading from existing upstream outputs. Later scripts update it in place:

```
pipeline_params.write_initial_params()     [Script 01]
  Writes: pipeline_scenario_params.csv
  Reads (if available): Scripts 03, 10e, 17 outputs
  Falls back to defaults with source_*="defaults" flag

pipeline_params.update_beta_coefficients() [Script 03]
  Updates: beta_1, beta_2, beta_3 per cluster

pipeline_params.update_peak_months()       [Script 03]
  Updates: peak_month per cluster

pipeline_params.update_b2_multipliers()    [Script 10e]
  Updates: clearfell_b2_mult, thinning_b2_mult

pipeline_params.update_specific_yield()    [Script 17]
  Updates: Sy per cluster

pipeline_params.load_params()              [09b, 09d, 19, 21]
  Returns: {clusters, peak_months, clearfell_b2_mult,
            thinning_b2_mult, broadleaf_b2_summer,
            broadleaf_b2_winter, summer_P, summer_PET,
            all_pipeline}
```

The CSV schema:

| Column | Source | Updated by |
|--------|--------|------------|
| Cluster | C1–C5 | Script 01 |
| beta_1, beta_2, beta_3 | SSM coefficients | Script 03 |
| Sy | Specific yield (cluster median) | Script 17 |
| h_disp | DRAINAGE_DATUM + mean_depth | Script 01 |
| forest | True for C4, C5 | config.py |
| peak_month | Calendar month of peak water table | Script 03 |
| clearfell_b2_mult | BACI-corrected Edge ratio | Script 10e |
| thinning_b2_mult | 50% of clearfell effect | Script 10e |
| broadleaf_b2_summer | Summer deciduous phenology (1.09) | config.py |
| broadleaf_b2_winter | Winter deciduous phenology (0.87) | config.py |
| summer_P | Mean Jun–Sep P (m/month) | Script 01 |
| summer_PET | Mean Jun–Sep PET (m/month) | Script 01 |
| source_* | "defaults" or "pipeline" per field | — |

On a fully-run pipeline, all `source_*` columns read "pipeline" and
`load_params()` returns `all_pipeline=True`.

## Legacy parameter functions (`scraping_common.py`)

Three functions in `scraping_common.py` remain functional as fallbacks.
New code should prefer `pipeline_params.load_params()`.

```
load_cluster_params()
  Reads: 03_03_cluster_mechanistic_coefficients.csv (β₁, β₂, β₃)
         17_wtf_well_sy.csv (Sy, cluster median)
         01_wells_clean.csv + DRAINAGE_DATUM (h_disp)
  Returns: {C1: {b1, b2, b3, Sy, h_disp, forest}, ...}

load_summer_climate()
  Reads: 01_climate.csv (Jun–Sep mean P and PET)
  Returns: (summer_P, summer_PET)

compute_scenario_bars(cluster_params, summer_P, summer_PET)
  Reads: config.py (UKCP18 scalers, interception), clearfell_common (B2 mult)
  Returns: {scenario: {cluster: mm_we_per_month}}

compute_scenario_bars_from_params()
  Wrapper: loads everything from pipeline_params, falls back to above
  Returns: (scenario_values, cluster_params, summer_P, summer_PET)
```

**True constants** (do not change with data) live in `config.py`:
`DRAINAGE_DATUM`, `FOREST_INTERCEPTION`, `BROADLEAF_INTERCEPTION`,
`BROADLEAF_B2_SUMMER`, `UKCP18_*` scalers.

## Data directory structure

```
data/                          ← raw input data (never modified)
outputs/                       ← all generated outputs
  00_climate_summary/
  01_data_prep/                ← (intermediates live in outputs/ root)
  02_clustering/
  03_state_space_model/
  04_cluster_visualisations/
  05_pearson_affinity/
  06_pearson_extended/
  07_spatial_coefficients/
  08_model_benchmarking/
  09_scraping_intervention/    ← all 09a–09e outputs land here
  10_clearfell_baci/           ← all 10a–10b, 10d–10g outputs land here
  10c_forest_zone_analysis/    ← 10c-specific subfolder
  11_forecasting_thresholds/
  11b_spatial_thresholds/
  12_figure_site_overview/
  13_figure_experimental_design/
  14_climate_projections/
  15_depth_dependent_pet/
  16_water_balance/
  17_wtf_specific_yield/
  18_wtf_spatial/
  19_spatial_groundwater/
  20_spatial_figures/
  21_forestry_scenarios/
  22_residual_lag_analysis/
  23_ridge_recharge_lag_test/
  24_residual_seasonality/
src/
  utils/
    config.py               ← cluster colours/labels, DRAINAGE_DATUM, HEADLINE_LAG, FOREST_INTERCEPTION, FOREST_CIDS, ecological thresholds, UKCP18 scenario factors, BROADLEAF_B2_SUMMER
    data_utils.py           ← cleaning, normalisation, CUSUM helpers
    map_utils.py            ← DEM hillshade, KML, IDW surface
    model_utils.py          ← SSM fitting (build_ssm_frame, fit_ssm, fit_ssm_intercept, simulate_ssm, pflood_lambda, monthly_perturbation)
    paths.py                ← all path constants — single source of truth
    pipeline_params.py      ← consolidated scenario parameter file (write/update/read)
                               + write_initial_params()        — called by Script 01
                               + update_beta_coefficients()    — called by Script 03
                               + update_peak_months()          — called by Script 03
                               + update_b2_multipliers()       — called by Script 10e
                               + update_specific_yield()       — called by Script 17
                               + load_params()                 — called by 09b, 09d, 19, 21
    clearfell_common.py     ← shared 5-tier well lists & BACI helpers for Script 10 suite
    scraping_common.py      ← shared constants, well lists, era definitions for Script 09 suite
                               + load_cluster_params()         — legacy: consolidated β, Sy, h_disp
                               + load_summer_climate()         — legacy: summer mean P/PET
                               + compute_scenario_bars()       — per-cluster scenario values
                               + compute_scenario_bars_from_params() — wrapper using pipeline_params
```

## Raw data inputs (`data/`)

| File | Description | Used by |
|---|---|---|
| `Newborough_Cleaned_For_Model.csv` | Raw dipwell records | 01 |
| `Well_locations_height.csv` | Well coordinates and pipe-top elevations | 01 |
| `RAF_Valley_Climate.csv` | Monthly P, max/min T, sun hours | 01 |
| `newborough_dem.tif` | LiDAR DEM | 04, 05, 06, 07, 08, 12, 13, 19, 20 (via `map_utils.load_dem_hillshade`) |
| `Features.kml` | Site features (slack boundaries, broadleaf restock, etc.) | 04, 06, 07, 08, 12, 13 (via `map_utils.add_kml_features`) |
| `streams.kml` | SAGA-derived stream network | 19, 20 |
| `clearfell.kml` | Clear-fell block boundary | 12, 13 |
| `broadleaf_restock.kml` | Broadleaf restocking block | 12, 13 |

---

## Per-script reference

### Phase 1 — Core LCSC Chain

#### Step 1 — 01_data_prep

**Purpose.** Cleans raw dipwell and climate data, applies QC, splits into reference (66 wells) and extended networks, exports upstand/elevation lookup, computes Thornthwaite PET.

**Reads.**

- `RAF_Valley_Climate.csv` (raw data)
- `Well_locations_height.csv` (raw data)
- `Newborough_Cleaned_For_Model.csv` (raw data)

**Writes.**

- `01_climate.csv`
- `01_locations.csv`
- `01_wells_clean.csv`
- `01_wells_clean_maod.csv`
- `01_wells_extended.csv`
- `01_wells_reference.csv`
- `01_well_elevations.csv`
- `01_data_prep/pipeline_scenario_params.csv` — consolidated scenario parameters (updated by Scripts 03, 10e, 17)


#### Step 2 — 02_clustering

**Purpose.** Behavioural Ward's-distance clustering on the 66-well reference network. Produces k=5 partition (canonical), dendrogram, validation plots, bootstrap stability diagnostics, cluster amplitude descriptors.

**Reads.**

- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_wells_clean.csv` (Script 01 (step 1))
- `01_wells_reference.csv` (Script 01 (step 1))
- `02_06_coassignment_heatmap_k{k}.png` (Script 02 (step 2))
- `02_07_cluster_membership_k{k}.csv` (Script 02 (step 2))

**Writes.**

- `02_cluster_stats.csv`
- `02_10_cluster_amplitude_boxplot.png`
- `02_08_cluster_amplitude_per_well.csv`
- `02_09_cluster_amplitude_summary.csv`
- `02_03_cluster_hydrographs_wb.png`
- `02_01_dendrogram.png`
- `02_05_bootstrap_stability_per_well.csv`
- `02_04_bootstrap_stability_summary.csv`
- `02_02_validation_plots.png`
- `02_02b_validation_k_sweep.png`

**Other.**

  - `OUT_02_COASSIGN_HEATMAP` passed to `str`
  - `OUT_02_MEMBERSHIP_SWEEP` passed to `str`


#### Step 3 — 03_state_space_model

**Purpose.** Per-well SSM fitting (β₁, β₂, β₃) and cluster-mean LCSC mechanism. Produces master coefficient table, cluster mechanistic table, regional and mAOD averages, peak-month export. Single canonical source for SSM coefficients.

**Reads.**

- `data` (raw data)
- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))
- `01_wells_clean_maod.csv` (Script 01 (step 1))
- `01_well_elevations.csv` (Script 01 (step 1))
- `02_08_cluster_amplitude_per_well.csv` (Script 02 (step 2))
- `03_01_mechanistic_signatures.png` (Script 03 (step 3))

**Writes.**

- `03_regional_averages_maod.csv`
- `03_master_data.csv`
- `03_regional_averages.csv`
- `03_02_cluster_summary_table.csv`
- `03_03_cluster_mechanistic_coefficients.csv`

**Other.**

  - `INT_WELL_ELEVATIONS` passed to `build_upstand_lookup`
  - `OUT_03_SIGNATURES` passed to `make_signatures_figure`


#### Step 4 — 04_cluster_visualisations

**Purpose.** Core cluster architecture map and extended visualisations.

**Reads.**

- `data` (raw data)
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))

**Writes.**

- `04_01_core_architecture_map.png`

**Other.**

  - `DATA_DIR` passed to `add_kml_features, load_dem_layer`


### Phase 2 — Pearson Membership Audit

#### Step 5 — 05_pearson_affinity

**Purpose.** Pearson cluster-membership audit for the reference network — confidence map.

**Reads.**

- `data` (raw data)
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))

**Writes.**

- `05_pear_membership_audit.csv`
- `05_pear_01_spatial_confidence_map.png`

**Other.**

  - `DATA_DIR` passed to `add_kml_features, load_dem_layer`
  - `INT_WELLS_CLEAN` passed to `load_matrix`


#### Step 6 — 06_pearson_extended

**Purpose.** Pearson audit for the extended network (FE wells, LIS, etc.) — affinity chart and integration map.

**Reads.**

- `data` (raw data)

**Writes.**

- `06_pear_membership_audit_sitewide.csv`

**Other.**

  - `DATA_DIR` passed to `add_kml_features`


### Phase 3 — Model Diagnostics & Intervention Analysis

#### Step 7 — 07_spatial_coefficients

**Purpose.** Maps β₁, β₂, β₃, R² across the site (reads pre-fitted coefficients from 03_master_data).

**Reads.**

- `data` (raw data)
- `03_master_data.csv` (Script 03 (step 3))
- `01_well_elevations.csv` (Script 01 (step 1))

**Other.**

  - `DATA_DIR` passed to `add_kml_features, load_dem_hillshade`


#### Step 8 — 08_model_benchmarking

**Purpose.** LCSC vs Traditional Linear Model benchmarking (NSE/R² improvement maps, CEH6 showdown figure, Table 3).

**Reads.**

- `data` (raw data)
- `08_lcsc_04_table3_benchmark_summary.csv` (Script 08 (step 8))

**Other.**

  - `OUT_08_TABLE3_SUMMARY` passed to `export_table3_summary`
  - `DATA_DIR` passed to `add_kml_features`


#### Step 9 — 09a_paired_baci

**Purpose.** Hierarchical paired BACI for the scraping intervention (CEH36, CEH18, CEH21, CEH22). β₃ era testing, full parameters, Table 4.

**Writes.**

- `09_scrape_03_baci_shifts.csv`
- `09_scrape_07_beta3_confidence.png`
- `09_scrape_02_beta3_significance.csv`
- `09_scrape_01_full_parameters.csv`
- `09_scrape_04_net_benefits.csv`
- `09_scrape_report_numbers.csv`
- `09_scrape_04b_table4_beta3_era_summary.csv`
- `09_tier1_final_cusum.csv`
- `09_scrape_05_tier1_background_drift.png`
- `09_scrape_06_tier2_scraping_signal.png`


#### Step 10 — 09b_scraping_propagation

**Purpose.** Split-window SSM fitting with BACI correction against distant controls; tests whether scraping propagated uphill into the forest interior. Centroid summaries for C3+CEH31 and C4. Scenario comparison bar charts.

**Reads.** Cluster parameters via `scraping_common.load_cluster_params()` and
`load_summer_climate()` (which consolidate from Scripts 01, 03, 17). Also reads
directly:

- `01_climate.csv` (Script 01)
- `01_locations.csv` (Script 01)
- `03_master_data.csv` (Script 03)
- `03_regional_averages.csv` (Script 03)
- `01_wells_clean.csv` (Script 01)
- `01_wells_extended.csv` (Script 01)

**Note:** The hardcoded fallback parameter dict and `h_aod` formulation have
been removed. All cluster parameters (β, Sy, h_disp) now come from
`scraping_common.load_cluster_params()`, which reads from Scripts 03 and 17
at runtime. If you rerun Script 03 or 17 with new data, the scenario figures
update automatically on the next 09b run.

**Writes.**

- `09b_02_centroid_summaries.csv`
- `09b_01_individual_well_baci.csv`
- `09b_04_scenario_comparison.jpg`
- `09b_04_scenario_comparison.csv`
- `09b_05_summer_scenario_comparison.png`
- `09b_05_summer_scenario_comparison.csv`
- `09b_03_ceh36_equilibration.jpg`


#### Step 11 — 09c_summer_minima

**Purpose.** Dual-control BACI on summer minima for scraping wells; ecological threshold framing.

**Writes.**

- `09c_03_summer_minima_climate_ctrl.png`
- `09c_04_summer_minima_paired.png`
- `09c_report_numbers.csv`
- `09c_01_summer_minima.csv`
- `09c_02_summer_minima_shifts.csv`


#### Step 12 — 09d_scenario_comparison

**Purpose.** CEH36-anchored equilibrium scenario comparison (observed scraping vs hypothetical clearfell/thinning/broadleaf/UKCP18 climate). All scenarios evaluated at CEH36 using that well's own SSM coefficients and Sy.

**Reads.** CEH36 well-level parameters loaded directly from Scripts 01, 03, 17.
Summer climate via `scraping_common.load_summer_climate()`. Scenario constants
(UKCP18 scalers, interception, B2 multiplier defaults) from `config.py`.

**Writes.**

- `09d_01_scenario_comparison.jpg`
- `09d_01_scenario_comparison.csv`
- `09d_02_summer_scenario_comparison.png`
- `09d_02_summer_scenario_comparison.csv`


#### Step 13 — 09e_robustness

**Purpose.** CEH36 robustness analyses (raw BACI, synthetic control, SSM residual).

**Writes.**

- `09e_report_numbers.csv`
- `09_scrape_08_ceh36_robustness.png`


#### Step 14 — 10a_ancova_baci

**Purpose.** Three-counterfactual ANCOVA-BACI — primary clearfell BACI result. Forest-control, coastal-control, climate-control comparisons.


#### Step 15 — 10b_spatial_step_maps

**Purpose.** Spatial step-change maps (raw and BACI-corrected) for both scraping and clearfell interventions.

**Reads.**

- `data` (raw data)
- `Well_locations_height.csv` (raw data)
- `03_master_data.csv` (Script 03 (step 3))
- `01_wells_clean.csv` (Script 01 (step 1))
- `01_wells_extended.csv` (Script 01 (step 1))
- `10b_spatial_fell_corrected.png` (Script 10B (step 15))
- `10b_spatial_fell_raw.png` (Script 10B (step 15))
- `10b_spatial_scrape_corrected.png` (Script 10B (step 15))
- `10b_spatial_scrape_raw.png` (Script 10B (step 15))

**Writes.**

- `10b_spatial_step_data.csv`

**Other.**

  - `OUT_10B_SCRAPE_CORRECTED` passed to `plot_spatial_step`
  - `DATA_DIR` passed to `add_kml_features, load_dem_hillshade`
  - `OUT_10B_FELL_RAW` passed to `plot_spatial_step`
  - `OUT_10B_FELL_CORRECTED` passed to `plot_spatial_step`
  - `OUT_10B_SCRAPE_RAW` passed to `plot_spatial_step`


#### Step 16 — 10c_forest_zone_analysis

**Purpose.** Per-well β₁ vs β₂ scatter, β₂ vs elevation regression, C4/C5 boundary map (forest zone spatial analysis).

**Reads.**

- `data` (raw data)
- `06_pear_membership_audit_sitewide.csv` (Script 06 (step 6))
- `07_coeff_maps_data.csv` (Script 07 (step 7))

**Writes.**

- `10c_forest_zone_cluster_summary.csv`
- `10c_forest_zone_correlations.csv`
- `10c_01_b1_b2_scatter.png`
- `10c_02_b2_elevation_regression.png`
- `10c_03_c4_c5_boundary_map.png`

**Other.**

  - `DATA_DIR` passed to `add_kml_features, load_dem_hillshade`


#### Step 17 — 10d_summer_minima

**Purpose.** Dual-control BACI on summer minima for clearfell wells.


#### Step 18 — 10e_coefficient_decomposition

**Purpose.** Before/after SSM coefficient shifts at clearfell tiers (Impact, Edge, Forest Ctrl, Coastal Ctrl, Climate Ctrl). Source for Script 21's β₂ multiplier.


#### Step 19 — 10f_robustness

**Purpose.** SSM-residual and synthetic-control robustness for the clearfell signal.

**Reads.**

- `10f_report_numbers.csv` (Script 10F (step 19))

**Writes.**

- `10f_01_ssm_residual_results.csv`
- `10f_02_synthetic_control_results.csv`

**Other.**

  - `OUT_10F_REPORT` passed to `save`


#### Step 20 — 10g_diagnostics

**Purpose.** NW10 broadleaf trend, clearfell transect, rolling coefficients.

**Reads.**

- `03_regional_averages.csv` (Script 03 (step 3))
- `10g_report_numbers.csv` (Script 10G (step 20))

**Writes.**

- `10g_01_nw10_broadleaf_trend.csv`
- `10g_04_rolling_coefficients.csv`
- `10g_03_clearfell_transect_steps.csv`
- `10g_02_clearfell_transect.png`

**Other.**

  - `OUT_10G_REPORT` passed to `save`


#### Step 21 — 10h_synthetic_impact_baci

**Purpose.** Robustness check extending FE1/FE2 records backwards using donor regression on Forest Control wells (CEH34, CEH2, CEH33). Tests three impact centroid variants (WMC3+FE1+FE2, WMC3+FE2, WMC3 alone) against all three control definitions. Includes CUSUM and climate sensitivity diagnostics for Variant B.

**Reads.**

- `01_wells_clean.csv` (Script 01 (step 1))
- `01_wells_extended.csv` (Script 01 (step 1))
- `01_climate.csv` (Script 01 (step 1))
- `03_master_data.csv` (Script 03 (step 3))

**Writes.**

- `10h_01_synthetic_calibration.csv`
- `10h_02_ancova_comparison_table.csv`
- `10h_03_ancova_full_coefficients.csv`
- `10h_04_baci_timeseries.csv`
- `10h_05_donor_regression_validation.png`
- `10h_06_baci_timeseries_varA.png`
- `10h_07_baci_timeseries_varB.png`
- `10h_08_baci_timeseries_varC.png`
- `10h_09_cusum_varB.png`
- `10h_10_climate_sensitivity_varB.png`
- `10h_report_numbers.csv`


#### Step 22 — 11_forecasting_thresholds

**Purpose.** Closed-form P_flood derivation and winter/summer transfer functions; Tables 6, 7, 8.

**Reads.**

- `03_cluster_peak_months.csv` (Script 03 (step 3))
- `03_03_cluster_mechanistic_coefficients.csv` (Script 03 (step 3))

**Writes.**

- `11_forecast_pflood_summary.csv`
- `11_forecast_winter_transfer_functions.csv`
- `11_forecast_summer_transfer_functions.csv`
- `11_forecast_pflood_threshold_equations.csv`


#### Step 23 — 11b_spatial_thresholds

**Purpose.** Spatial threshold maps (summer minima depth, winter maxima depth, P_flood, flood frequency); builds the public forecaster HTML.

**Reads.**

- `data` (raw data)
- `03_cluster_peak_months.csv` (Script 03 (step 3))
- `01_locations.csv` (Script 01 (step 1))
- `03_master_data.csv` (Script 03 (step 3))
- `06_pear_membership_audit_sitewide.csv` (Script 06 (step 6))
- `01_wells_clean_maod.csv` (Script 01 (step 1))
- `01_wells_extended.csv` (Script 01 (step 1))
- `01_well_elevations.csv` (Script 01 (step 1))
- `11_forecast_winter_transfer_functions.csv` (Script 11 (step 21))
- `11_forecast_summer_transfer_functions.csv` (Script 11 (step 21))
- `11_forecast_pflood_threshold_equations.csv` (Script 11 (step 21))
- `forecaster_template.html` (Script 11B (step 22))

**Writes.**

- `11b_04_flood_frequency.png`
- `11b_03_pflood.png`
- `11b_03_pflood_per_well.csv`
- `11b_01_summer_minima_depth.png`
- `11b_05_table10_pflood_spreadsheet.csv`
- `11b_02_winter_maxima_depth.png`

**Other.**

  - `DATA_DIR` passed to `add_kml_features, load_dem_hillshade`


### Phase 4 — Climate Projections & Figure Generation

#### Step 24 — 00_climate_summary

**Purpose.** Climate timeseries (full + monitoring period) and well-network summary statistics. Three figures (climate ts, network, summer warming) and three CSVs.

**Reads.**

- `RAF_Valley_Climate.csv` (raw data)
- `01_climate.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))
- `00_01_annual_climate_summary.csv` (Script 00 (step 23))
- `00_01_climate_timeseries.png` (Script 00 (step 23))
- `00_03_summer_warming_trend.png` (Script 00 (step 23))
- `00_03_summer_warming_stats.csv` (Script 00 (step 23))
- `00_02_well_network_summary.png` (Script 00 (step 23))
- `00_02_well_network_summary.csv` (Script 00 (step 23))

**Other.**

  - `OUT_00_SUMMER_WARMING` passed to `str`
  - `OUT_00_CLIMATE_TIMESERIES` passed to `dirname`
  - `OUT_00_WELL_NETWORK_TABLE` passed to `dirname`
  - `OUT_00_WELL_NETWORK_FIG` passed to `dirname`
  - `OUT_00_SUMMER_WARMING_TABLE` passed to `str`
  - `OUT_00_ANNUAL_CLIMATE_TABLE` passed to `dirname`


#### Step 25 — 14_climate_projections

**Purpose.** Climate trajectory projections (summer minima trend, winter exceedance) for all five clusters under UKCP18 RCP8.5.

**Reads.**

- `02_cluster_stats.csv` (Script 02 (step 2))
- `03_regional_averages.csv` (Script 03 (step 3))
- `00_02_well_network_summary.csv` (Script 00 (step 23))
- `14_climate_trajectory_stacked.png` (Script 14 (step 24))
- `14_climate_trajectory_summer.png` (Script 14 (step 24))
- `14_climate_trajectory_winter_flooding.png` (Script 14 (step 24))
- `14_seasonal_extremes_scatter.html` (Script 14 (step 24))

**Writes.**

- `14_annual_extremes.csv`
- `14_summer_trend_stats.csv`
- `14_winter_exceedance.csv`

**Other.**

  - `OUT_14_SEASONAL_SCATTER` passed to `render_seasonal_scatter`
  - `OUT_14_CLIMATE_STACKED` passed to `render_stacked_figure`
  - `INT_REGIONAL_AVG` passed to `_compute_winter_exceedance, load_annual_extremes`
  - `OUT_14_CLIMATE_SUMMER` passed to `render_summer_figure`
  - `OUT_14_CLIMATE_WINTER` passed to `render_winter_figure`


#### Step 26 — 12_figure_site_overview

**Purpose.** Figure 1 — DEM site overview map.

**Reads.**

- `data` (raw data)

**Other.**

  - `DATA_DIR` passed to `add_kml_features`


#### Step 27 — 13_figure_experimental_design

**Purpose.** Figure 2 — five-tier BACI network plus scraping interventions.

**Reads.**

- `data` (raw data)
- `Well_locations_height.csv` (raw data)

**Other.**

  - `DATA_DIR` passed to `add_kml_features`


### Phase 5 — Depth-Dependent PET

#### Step 28 — 15_depth_dependent_pet

**Purpose.** Depth-dependent PET analysis (exp(−λd) modification, λ profile, fit comparison).

**Reads.**

- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))


### Phase 6 — WTF Cluster Sy Estimation

#### Step 29 — 17_wtf_specific_yield

**Purpose.** WTF cluster-mean Sy estimation (OLS winter and event-median methods, with optional interception correction for forested clusters).


### Phase 7 — Water Balance

#### Step 30 — 16_water_bal

**Purpose.** Water-balance decomposition by cluster; bar/volumetric plots; WTF-corrected variants.

**Reads.**

- `03_regional_averages.csv` (Script 03 (step 3))
- `03_03_cluster_mechanistic_coefficients.csv` (Script 03 (step 3))
- `16_water_bal_table.csv` (Script 16 (step 29))
- `16_water_bal_vol_table.csv` (Script 16 (step 29))

**Writes.**

- `16_water_bal_bar_lay.png`
- `16_water_bal_bar_ms.png`

**Other.**

  - `OUT_16_TABLE` passed to `save_headspace_table`
  - `OUT_16_VOL_TABLE` passed to `save_volumetric_table`


### Phase 8 — WTF Spatial Analysis

#### Step 31 — 18_wtf_spatial

**Purpose.** Per-well Sy via WTF, IDW spatial interpolation of Sy, contour maps, drainage timescale map (τ = Sy / β₃), and aquifer diagnostic synthesis scatter (τ vs ΔNSE vs Sy).

**Reads.**

- `data` (raw data)
- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `06_pear_membership_audit_sitewide.csv` (Script 06 (step 6))
- `01_wells_clean.csv` (Script 01 (step 1))
- `01_wells_extended.csv` (Script 01 (step 1))
- `03_master_data.csv` (Script 03 (step 3)) — β₃ for τ computation
- `08_lcsc_model_stats.csv` (Script 08 (step 8)) — ΔNSE for synthesis scatter

**Writes.**

- `17_wtf_well_sy.csv`
- `18_wtf_01_well_sy_estimates.csv`
- `18_wtf_02_spatial_sy_map.png`
- `18_wtf_03_sy_contour.png` (supplementary)
- `18_wtf_04_sy_contour_extended.png` (supplementary)
- `18_wtf_05_drainage_timescale_map.png` (supplementary)
- `18_wtf_05_drainage_timescale.csv` (supplementary)
- `18_wtf_06_aquifer_diagnostic_synthesis.png` (supplementary)

**Other.**

  - `DATA_DIR` passed to `add_kml_features, load_dem_hillshade`
  - Exclusions for τ map: CEH12 (bedrock), CEH15 (slack floor), CEH14 (negative β₃), CEH13 (near-zero β₃, τ outlier)


### Phase 9 — Spatial Groundwater

#### Step 32 — 19_spatial_groundwater

**Purpose.** Spatial groundwater analysis (head, β fields, water balance, drainage, depth-to-water-table). Self-contained scenario viewer HTML with optional forest drawdown propagation (flow-weighted cost-distance, λ = √(D/β₃)).

**Reads.**

- `newborough_dem.tif` (raw data)
- `clearfell.kml` (raw data)
- `Features.kml` (raw data)
- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `03_master_data.csv` (Script 03 (step 3))
- `01_wells_clean_maod.csv` (Script 01 (step 1))
- `01_well_elevations.csv` (Script 01 (step 1))
- `broadleaf_restock.kml` (raw data)
- `18_wtf_01_well_sy_estimates.csv` (Script 18 (step 30))

**Other.**

  - `DATA_KML_CLEARFELL` passed to `kml_to_bng`
  - `KML_BROADLEAF` passed to `kml_to_bng`
  - `DATA_KML_FEATURES` passed to `kml_to_bng`


#### Step 33 — 20_spatial_figures

**Purpose.** Paper figures: head + streams overlay, SSM water-balance residual map, slope/gradient, forest drawdown propagation.

**Reads.**

- `newborough_dem.tif` (raw data)
- `data` (raw data)
- `Features.kml` (raw data)
- `streams.kml` (raw data)
- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `03_master_data.csv` (Script 03 (step 3))
- `06_pear_membership_audit_sitewide.csv` (Script 06 (step 6))
- `01_wells_clean_maod.csv` (Script 01 (step 1))
- `01_wells_extended.csv` (Script 01 (step 1))
- `01_well_elevations.csv` (Script 01 (step 1))

**Writes.**

- `20_head_surface_streams.png`
- `20_residual_ssm.png`
- `20_slope_gradient.png`
- `20_drawdown_propagation.png`

**Other.**

  - `DATA_DIR` passed to `load_dem_hillshade`


### Phase 10 — Forestry Scenarios

#### Step 34 — 21_forestry_scenarios

**Purpose.** Forest-management scenario hydrographs and distributions, BACI zone violins; loads BACI displacement and β₂ multiplier dynamically from 10a/10e. Scenario comparison figure now uses `scraping_common.compute_scenario_bars()` as the single source of truth for per-cluster scenario values.

**Reads.** Cluster parameters via `scraping_common.load_cluster_params()` and
`load_summer_climate()` for the scenario comparison figure. Also reads directly:

- `01_climate.csv` (Script 01)
- `03_regional_averages_maod.csv` (Script 03)
- `03_master_data.csv` (Script 03)
- `01_wells_clean.csv` (Script 01)
- `01_wells_extended.csv` (Script 01)
- `01_well_elevations.csv` (Script 01)
- `10a_report_numbers.csv` (Script 10A)
- `10e_01_coefficient_shifts.csv` (Script 10E)

**Writes.**

- `21_forestry_04_baci_zone_means.csv`
- `21_forestry_04_baci_zone_violin.png`
- `21_forestry_02_distributions.png`
- `21_forestry_02_distributions_means.csv`
- `21_forestry_01_hydrograph.png`
- `21_forestry_05_scenario_comparison.jpg`
- `21_forestry_05_scenario_comparison.csv`
- `21_forestry_03_scraping_eras.png`
- `21_forestry_03_scraping_era_means.csv`


### Phase 11 — Supplementary Diagnostics

#### Step 35 — 22_residual_lag_analysis

**Purpose.** AR(1) diagnostics on SSM residuals; α/φ scatter; example residual series by cluster.

**Reads.**

- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))
- `22_03_alpha_phi_scatter.png` (Script 22 (step 34))
- `22_01_ar1_histogram.png` (Script 22 (step 34))
- `22_02_ar1_spatial_map.png` (Script 22 (step 34))
- `22_04_example_residuals_by_cluster.png` (Script 22 (step 34))

**Writes.**

- `22_model_b_fits.csv`
- `22_residuals_wide.csv`

**Other.**

  - `OUT_22_AR1_HIST` passed to `plot_ar1_hist`
  - `OUT_22_AR1_MAP` passed to `plot_ar1_map`
  - `OUT_22_ALPHA_PHI_SCATTER` passed to `plot_alpha_phi_scatter`
  - `OUT_22_EXAMPLE_SERIES` passed to `plot_example_residuals`


#### Step 36 — 23_ridge_recharge_lag_test

**Purpose.** Ridge-proximal recharge lag hypothesis test (cross-correlation, lag vs distance, B10/B11 by cluster).

**Reads.**

- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))
- `23_04_b10_b11_by_cluster.png` (Script 23 (step 35))
- `23_01_ccf_headline_ridge_wells.png` (Script 23 (step 35))
- `23_03_peak_lag_spatial_map.png` (Script 23 (step 35))
- `23_02_peak_lag_vs_ridge_distance.png` (Script 23 (step 35))
- `23_05_hypothesis_test_summary.txt` (Script 23 (step 35))

**Writes.**

- `23_ridge_lag_fits.csv`
- `23_residuals_extended_wide.csv`

**Other.**

  - `OUT_23_LAG_VS_DISTANCE` passed to `plot_lag_vs_distance`
  - `OUT_23_LAG_MAP` passed to `plot_lag_map`
  - `OUT_23_CCF_HEADLINE` passed to `plot_ccf_headline`
  - `OUT_23_BETAS_BY_CLUSTER` passed to `plot_betas_by_cluster`
  - `OUT_23_TEST_SUMMARY` passed to `write_test_summary`


#### Step 37 — 24_residual_seasonality

**Purpose.** Residual-seasonality diagnostic (climatology panels, amplitude map, sun-hour correlation, phase by cluster).

**Reads.**

- `RAF_Valley_Climate.csv` (raw data)
- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))
- `24_02_seasonal_amplitude_map.png` (Script 24 (step 37))
- `24_01_climatology_panels_by_cluster.png` (Script 24 (step 37))
- `24_04_phase_by_cluster.png` (Script 24 (step 37))
- `24_05_diagnostic_summary.txt` (Script 24 (step 37))
- `24_03_sun_residual_correlation.png` (Script 24 (step 37))

**Writes.**

- `24_residual_climatology.csv`

**Other.**

  - `OUT_24_SUMMARY` passed to `write_summary`
  - `OUT_24_AMPLITUDE_MAP` passed to `plot_amplitude_map`
  - `OUT_24_PHASE_BARPLOT` passed to `plot_phase_barplot`
  - `DATA_CLIMATE_RAW` passed to `load_sunshine_hours`
  - `OUT_24_CLIMATOLOGY_PANELS` passed to `plot_climatology_panels`
  - `OUT_24_SUN_CORR_SCATTER` passed to `plot_sun_corr_scatter`


---

## Paper tables — quick reference

| Table | Description | Script | File |
|---|---|---|---|
| Table 1 | Annual climate summary | 00 | `00_01_annual_climate_summary.csv` |
| Table 2 | Cluster amplitude damping | 02 | `02_09_cluster_amplitude_summary.csv` |
| Table 3 | Cluster mechanistic coefficients | 03 | `03_03_cluster_mechanistic_coefficients.csv` |
| Table 4a | Head-space water balance | 16 | `16_water_bal_table.csv` |
| Table 4b | Volumetric water balance | 16 | `16_water_bal_vol_table.csv` |
| Table 4c | WTF specific yield | 17 | `17_wtf_01_sy_table.csv` |
| Table 5 | Model benchmarking (SSM vs TLM) | 08 | `08_lcsc_04_table3_benchmark_summary.csv` |
| Table 6 | Scraping β₃ era coefficients | 09a | `09_scrape_04b_table4_beta3_era_summary.csv` |
| Table 7 | Clearfell ANCOVA-BACI results | 10a | `10a_report_numbers.csv` |
| Table 8 | Per-well summer min shifts | 10d | `10d_04_summer_minima_forest_ctrl.png` (source CSV) |
| Table 9 | Mixed-effects clearfell step | 10d | (embedded in 10d output) |
| Table 10 | Before/after clearfell SSM coefficients | 10e | `10e_01_coefficient_shifts.csv` |
| Table 11 | Predicted vs observed clearfell step | 10e | (derived from 10e) |
| Table 12 | Winter peak prediction equations | 11 | `11_forecast_winter_transfer_functions.csv` |
| Table 13 | Summer drought prediction equations | 11 | `11_forecast_summer_transfer_functions.csv` |
| Table 14 | Per-cluster P_flood summary | 11 | `11_forecast_pflood_threshold_equations.csv` |
| Table 15 | P_flood linear forms | 11 | `11_forecast_pflood_threshold_equations.csv` |
| Table 16 | Forest zone spatial predictors | 10c | `10c_forest_zone_correlations.csv` |

## Paper figures — quick reference

| Figure | Description | Script | File |
|---|---|---|---|
| 1 | Site topography and DEM | 12 | `12_01_dem_site_overview.png` |
| 2 | Experimental design (5-tier BACI) | 13 | `13_01_experimental_setup_map.png` |
| 3 | Climate timeseries (2005–2026) | 00 | `00_01_climate_timeseries.png` |
| 4 | Summer warming trend (1931–2025) | 00 | `00_03_summer_warming_trend.png` |
| 5 | Well network characterisation | 00 | `00_02_well_network_summary.png` |
| 6 | Cluster validation plots | 02 | `02_02_validation_plots.png` |
| 7 | Ward's dendrogram | 02 | `02_01_dendrogram.png` |
| 8 | Cluster hydrographs + water balance | 02 | `02_03_cluster_hydrographs_wb.png` |
| 9 | Water balance decomposition | 16 | `16_water_bal_bar_ms.png` |
| 10 | WTF Sy spatial surface | 18 | `18_wtf_02_spatial_sy_map.png` |
| 11 | Pearson affinity (reference) | 05 | `05_pear_01_spatial_confidence_map.png` |
| 12 | Pearson integration map (all 89) | 06 | `06_pear_02_integration_map.png` |
| 13 | CEH6 SSM vs TLM showdown | 08 | `08_lcsc_01_ceh6_showdown.png` |
| 14 | SSM gain over TLM (R²/NSE maps) | 08 | `08_lcsc_02_r2_improvement_map.png` |
| 15 | Tier 1 CUSUM (background drift) | 09a | `09_scrape_05_tier1_background_drift.png` |
| 16 | Tier 2 paired CUSUM (scraping) | 09a | `09_scrape_06_tier2_scraping_signal.png` |
| 17 | Three-method robustness (CEH36) | 09e | `09_scrape_08_ceh36_robustness.png` |
| 18 | β₃ era coefficients with CIs | 09a | `09_scrape_07_beta3_confidence.png` |
| 19 | Scraping treatment summer minima | 21 | `21_forestry_03_scraping_eras.png` |
| 20 | Scraping summer minima vs climate ctrl | 09c | `09c_03_summer_minima_climate_ctrl.png` |
| 21 | Paired BACI summer min (CEH36 vs CEH4) | 09c | `09c_04_summer_minima_paired.png` |
| 22 | Climate-corrected anomaly (CEH36 vs CEH4) | 09b | `09b_03_ceh36_equilibration.jpg` |
| 23 | Spatial step-change map (scraping era) | 10b | `10b_spatial_scrape_corrected.png` |
| 24 | Scenario comparison at CEH36 | 09d | `09d_01_scenario_comparison.jpg` |
| 25 | Summer min scenario comparison (CEH36) | 09d | `09d_02_summer_scenario_comparison.png` |
| 26 | CWB vs BACI displacement (clearfell) | 10a | `10a_03_baci_timeseries_*.png` |
| 27 | Forest control BACI — Impact tier | 10a | `10a_03_baci_timeseries_*.png` |
| 28 | Forest control BACI — Edge tier | 10a | `10a_03_baci_timeseries_*.png` |
| 29 | Summer minima vs Forest control | 10d | `10d_04_summer_minima_forest_ctrl.png` |
| 30 | Summer min distributions by BACI tier | 21 | `21_forestry_04_baci_zone_violin.png` |
| 31 | Spatial step-change map (clearfell era) | 10b | `10b_spatial_fell_corrected.png` |
| 32 | Before/after SSM coefficients (17 wells) | 10e | `10e_*.png` |
| 33 | Clearfell transect (step vs distance) | 10g | `10g_02_clearfell_transect.png` |
| 34 | Summer min depth (spatial threshold) | 11b | `11b_01_summer_minima_depth.png` |
| 35 | P_flood spatial distribution | 11b | `11b_03_pflood.png` |
| 36 | Winter max depth (spatial threshold) | 11b | `11b_02_winter_maxima_depth.png` |
| 37 | Winter flooding frequency | 11b | `11b_04_flood_frequency.png` |
| 38 | Climate trajectory + threshold exceedance | 14 | `14_climate_trajectory_stacked.png` |
| 39 | Per-well optimal drainage datum | 07 | `07_coeff_*_*.png` |
| 40 | Spatial SSM coefficient atlas | 07 | `07_coeff_*_*.png` |
| 41 | Drainage timescale (τ = Sy/β₃) | 18 | `18_wtf_05_drainage_timescale_map.png` |
| 42 | Forest drawdown propagation | 20 | `20_drawdown_propagation.png` |
| 43 | Aquifer diagnostic synthesis | 18 | `18_wtf_06_aquifer_diagnostic_synthesis.png` |
| 44 | Mean head surface + streams | 20 | `20_head_surface_streams.png` |
| 45 | SSM water balance residual | 20 | `20_residual_ssm.png` |
| 46 | Forestry scenario hydrograph | 21 | `21_forestry_01_hydrograph.png` |

---

## Conventions and constants — quick reference

All scripts import physical and statistical constants from `utils/config.py`. The single sources of truth are:

- `DRAINAGE_DATUM = 3.7 m` — displacement reference for β₃
- `HEADLINE_LAG = 0` — no rainfall lag (corrected bucketing convention)
- `FOREST_INTERCEPTION = 0.24` — Corsican pine canopy fraction (Freeman 2008)
- `BROADLEAF_INTERCEPTION = 0.15` — annual mean (Komatsu et al. 2011)
- `FOREST_CIDS = (4, 5)` — clusters carrying pine canopy under k=5
- `RAF_VALLEY_LAT_DEG = 53.25` — Thornthwaite day-length latitude
- `REFERENCE_CUTOFF_DATE = '2026-02-01'` — reference-network selection cutoff
- `CLUSTER_LABELS / CLUSTER_COLOURS / CLUSTER_MARKERS` — k=5 partition (C1 Lake Edge, C2 Dune, C3 Western Residual, C4 Main Forest, C5 Coastal Forest)
- `SD15b / SD15b_REC / SD16 / SD16_REC` — Curreli (2013) ecological thresholds
- `UKCP18_*_P_*` / `UKCP18_*_PET_*` — UKCP18 RCP8.5 Wales scenario multipliers

SSM keys used throughout the pipeline are the **long form**: `beta_1_recharge`, `beta_2_atmospheric_draw`, `beta_3_drainage`. These are the column names in `03_master_data.csv` and the keys returned by `model_utils.fit_ssm()`.
