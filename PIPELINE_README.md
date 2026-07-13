# Newborough Warren Groundwater Analysis Pipeline
## Script Input/Output Reference

This document describes the data flow between all pipeline scripts: which files each script reads, which it produces, and which outputs feed into the paper as figures or tables, or into downstream scripts.

**Generated from automated I/O audit of `src/` against GitHub `main`.**

**Run order:** 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 (suite a–e) → 10 (suite i, a, b, c, d, e, f, g, h, j, k, l) → 11 → 11b → 11c → 00 → 14 → 14b → 12 → 13 → 15 → 17 → 16 → 18 → 19 → 20 → 21 → 25 (coastal) → 22 → 23 → 24 → 26 (van Willegen MSL) → 26b (UKCP18 MSL projection) → 26c (MSL5 report figures) → 28 (C3 detrend check) → 29 (within-C3 variance) → 30 (C4 constrained fit) → 32 (differential movement) → 33 (envelope amplification) → 35 (per-well amplification) → 36 (absolute climate trend) → 37 (driver validation) → 37b (driver footing) → 24b (residual climatology) → 31 (cluster validation) → 31b (separation vs recoverability) → 34 (window sensitivity) → 38 (coastal transect) → 09f (management-effects synthesis) → 27 (grey)

**48 pipeline steps across 17 phases** (canonical count: `pipeline_manifest.json`).

Phases 1–11 produce the main analytical results documented in the report. Phase 12 (Scripts 22–24) runs supplementary diagnostics. Phase 13 runs the van Willegen et al. (2025) MSL analyses — observational 5-year MSL aggregation (Script 26, step 30), the UKCP18 RCP8.5 climate-projection companion (Script 26b, step 31), and the report-format MSL5 figures cited in §4.8.4 and §4.10.1 of the main report (Script 26c, step 32). Phase 14 runs the cluster framework diagnostics added in the post-review pass (2026-05-29): the C3 detrend check (Script 28, step 33, validating the aquifer-architecture framing of §5.1 by testing whether C3 ≠ C2 + coastal drift) and the within-C3 variance attribution (Script 29, step 34, characterising the hydrogeological structure within C3 by regressing per-well metrics against five spatial/hydrogeological predictors), and the C4 constrained-β₃ triangulation sensitivity (Script 30, step 35, recovering a physically admissible forest drainage coefficient where the unconstrained monthly fit is degenerate) — documented in §5.1.1 and §4.2.2 of the main report and §S.19 of the Methods Supplement. Phase 15 runs six observed-change/envelope/driver-validation scripts, all analytical-default as of the 2026-07-13 Task E reclassification: secular differential water-table drift (Script 32, step 36, report Fig 59), climate-swing amplification and drought-floor surface (Script 33, step 37, report Fig 60), the per-well climate-sensitivity coefficient (Script 35, step 38), the absolute climate-removed secular trend map (Script 36, step 39, Figure 63), the predicted-vs-observed driver-change validation (Script 37, step 40), and the comparative driver footing across forest/scrape/coast on common currencies (Script 37b, step 41). Phase 16 runs the MSL5 two-window sensitivity demonstration for §5.7.5 (Script 34, step 45) and the coast-to-inland MAM transect observational δ₀ diagnostic for §4.8.3 (Script 38, step 46) — both also promoted to analytical-default 2026-07-13 — alongside its remaining opt-in supplementary diagnostics: cluster-stratified residual climatology (Script 24b, step 42), independent k=5 partition validation (Script 31, step 43) and its separation-vs-recoverability companion (Script 31b, step 44), which run only with `--with-supplementary`. Phase 17 runs a synthesis figure and the greyscale figure-conversion utility. Script 09f (step 47) is a display/utility synthesis figure — the spatial-reach comparison of management interventions and coastal retreat cited in §5.8 of the main report; it reads outputs produced earlier in the same pass (Scripts 20, 25, 09d, 10a) and runs last so those already exist, falling back to documented defaults with warnings only on a partial run (see the two-pass note). The greyscale figure-conversion utility (Script 27, step 48) then converts all colour figures — including 09f's — to journal-ready greyscale as a callable post-processing step, retained in `run_analysis.py` but not treated as an analytical phase.

The main analytical script for Phase 11 (step 26) is `25_coastal_gradient.py`. Phase 13 contains three scripts: `26_van_willegen_msl.py` (step 30, observational MSL5 aggregation, the report's §4.9.8 monitoring metric), `26b_van_willegen_msl_projections.py` (step 31, perturbation overlay producing per-cluster ΔMSL5 estimates under UKCP18 RCP8.5 50th-percentile scenarios), and `26c_msl5_report_figures.py` (step 32, report-format MSL5 figures for §4.8.4 and §4.10.1 of the main report — a display-only companion that reads only canonical outputs from Scripts 26, 26b and 19). Phase 14 contains three scripts: `28_c3_detrend_check.py` (step 33, the H0 test that C3 wells de-trended against the Script 25 forest-free linear-capped gradient remain C3 rather than collapsing to C2), `29_c3_within_variance_check.py` (step 34, the within-C3 panel regression of nine per-well behavioural metrics against five spatial and hydrogeological predictors), and `30_c4_constrained_fit.py` (step 35, the triangulation-anchored C4 constrained-β₃ sensitivity that recovers a physically admissible forest drainage coefficient where the unconstrained monthly fit is degenerate). Phase 15 adds six observed-change/envelope/driver-validation scripts, all analytical-default since the 2026-07-13 Task E reclassification: `32_differential_movement.py` (step 36, report Fig 59), `33_envelope_amplification.py` (step 37, report Fig 60), `35_per_well_amplification.py` (step 38, the per-well climate-sensitivity coefficient — Paper 1 aquifer characterisation), `36_absolute_climate_trend.py` (step 39, the absolute climate-removed per-well secular trend map, Figure 63), `37_driver_validation.py` (step 40, the per-driver scale-factor regression validating Script 20's modelled fields against Script 36's climate-corrected trends), and `37b_driver_footing.py` (step 41, the Part B comparative footing of forest/scrape/coast on common currencies). Phase 16 contains five standalone diagnostics that regenerate with the pipeline: `24b_residual_climatology.py` (step 42, opt-in, cluster-stratified residual climatology), `31_cluster_validation.py` (step 43, opt-in, independent k=5 partition validation), `31b_separation_vs_recoverability.py` (step 44, opt-in, the separation-vs-recoverability companion), `34_window_sensitivity.py` (step 45, analytical-default since 2026-07-13, the §5.7.5 all-pairs MSL5 two-window sensitivity demonstration figure), and `38_coastal_transect.py` (step 46, analytical-default since 2026-07-13, the §4.8.3 coast-to-inland MAM transect observational δ₀ diagnostic). The synthesis figure for Phase 17 (step 47) is `09f_management_effects.py` (the management-vs-coastal spatial-reach figure for §5.8; two-pass, reading Scripts 20/25/09d/10a with documented fallbacks); the greyscale utility for Phase 17 (step 48) is `27_greyscale_figures.py`. Two further post-review diagnostics (added 2026-05-29 in the same cascade as Phase 14) sit inside earlier phases as successors to their data source: `11c_pflood_achievability.py` (Phase 3, step 13, the per-well categorical priority map for §5.9 / Conclusion 4 reading Script 11b's per-well λ table) and `14b_year_of_crossing.py` (Phase 4, step 16, the bootstrap year-of-crossing diagnostic for §7 Conclusion 11 reading Script 14's annual summer-min series). References to "Script 25" mean coastal-gradient; "Script 26" means van Willegen MSL and the equilibrium wetness index; "Script 26b" means UKCP18 MSL projection; "Script 26c" means MSL5 report-format figures; "Script 09f" means management-vs-coastal spatial-reach synthesis; "Script 27" means greyscale post-processing; "Script 28" means C3 detrend check; "Script 29" means within-C3 variance attribution; "Script 30" means C4 constrained-β₃ triangulation; "Script 36" means absolute climate-removed secular trend; "Script 37" means driver validation; "Script 37b" means comparative driver footing; "Script 38" means coast-to-inland MAM transect; "Script 11c" means P_flood achievability map; "Script 14b" means bootstrap year-of-crossing.

Note on Script 11 (forecasting thresholds, Phase 3 / step 11). Section 5 of that script — a per-cluster empirical spring MSL transfer function — was added 2026-05-20 as the predictive companion to Script 26's monitoring metric. The transfer function reads from `03_regional_averages.csv` and produces cluster MSL_y forecasts from antecedent winter peak and Oct–May P/PET. See the per-script entry for Script 11 below and §S.18b of the Methods Supplement.

Script 09 is a modular suite orchestrated by `run_09_scraping.py` (09a → 09b → 09c → 09d → 09e). Script 10 is a modular suite orchestrated by `run_10_clearfell.py`. The full sub-script set is 10a–10m; 10i (CEH34 donor-regression hindcast) runs first as a prerequisite for 10a/10b/10e/10h, 10j (direct Impact-vs-Edge contrast) runs after 10d's summer-minima output is available, 10k/10l (the four-zone pooled-panel BACI at monthly and summer-minimum resolution) run next — 10l reads 10d's summer-minima frame — and 10m (the WMC3-versus-forest-control dual-panel intervention figure) runs last as a display figure, reading the 10a ANCOVA clearfell headline (`10a_report_numbers.csv`) live for its on-figure reconciliation note. Within the suite, 10c (forest zone spatial analysis) is treated as supplementary and 10m is a display figure, while the other eleven sub-scripts contribute to the primary report results. All sub-modules can be run independently provided their upstream Phase 1–2 outputs exist.

> **Step numbering convention.** The canonical step numbers are those reported by `run_analysis.py` (1–44). Two of those steps — Step 9 (`run_09_scraping.py`) and Step 10 (`run_10_clearfell.py`) — are wrapper scripts that invoke a fixed ordered set of sub-scripts. Section headings and inline annotations under those two steps use a stable sub-step label (e.g. `Step 9.2` for `09b_scraping_propagation`, `Step 10.5` for `10d_summer_minima`). Sub-step labels are stable: adding a new sub-script appends at the end of the suite rather than renumbering downstream steps. Note that the wrapper-script label strings printed by `run_analysis.py` (e.g. `"Clear-fell BACI analysis suite (10a–10j)"`) are console banners only and may lag the live sub-script set; the authoritative sub-script set is the one run by the wrapper itself (`run_10_clearfell.py`) and documented per-script below.

## Two-pass execution (recommended for new datasets)

Two scripts in Phase 3 read Specific-Yield (Sy) values that are produced later in the pipeline:

| Script | Step | Reads (via `scraping_common`) | Producer | Producer step |
|---|---|---|---|---|
| `09b_scraping_propagation.py` | 9.2 | `load_cluster_params()` → Script 17 Sy | Script 17 | 20 |
| `09d_scenario_comparison.py`  | 9.4 | `load_cluster_params()` → Script 17 Sy | Script 17 | 20 |
| `21_forestry_scenarios.py`    | 25  | `load_cluster_params()` → Script 17 Sy | Script 17 | 20 |

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
- Script 21 requires `03_regional_averages_maod.csv` from Script 03, plus Scripts 10a (BACI step) and 10e (β₂ multiplier). The summer-minimum companion (`21_forestry_06`) additionally reads `03_regional_averages.csv` (cluster-centroid hydrographs, for the amplification factors) and the Script 17 WTF Sy table (`17_wtf_01_sy_estimates.csv`).
- Script 14 requires `00_well_network_summary.csv` from Script 00 and `02_cluster_stats.csv` from Script 02.
- Sub-script 10i (CEH34 hindcast) is a prerequisite for 10a / 10b / 10e / 10h and must run first within the Script 10 suite; 10d, 10f, 10j, 10k, and 10l do not consume the hindcast.
- Sub-script 10j (direct Impact-vs-Edge contrast) reads `10d_01_summer_minima.csv` from Script 10d and must run after 10d within the Script 10 suite.
- Sub-scripts 10k / 10l (four-zone pooled-panel BACI) run last within the Script 10 suite; 10l reads `10d_01_summer_minima.csv` from Script 10d and must run after 10d.

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
| broadleaf_b2_summer | Summer deciduous phenology (1.0750) | config.py |
| broadleaf_b2_winter | Winter deciduous phenology (0.8817) | config.py |
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
`BROADLEAF_B2_WINTER`, `BROADLEAF_B2_SUMMER`, `UKCP18_*` scalers.

## Data directory structure

```
data/                          ← raw input data (never modified)
  *.csv                        ← raw well, climate, metadata tables
  geo/                         ← geographic inputs (DEM + KML), resolved via paths.data_geo()
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
  10_clearfell_baci/           ← all 10a–10b, 10d–10m outputs land here
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
  25_coastal_gradient/
  26_van_willegen_msl/
  26b_van_willegen_msl_projections/
  26c_msl5_report_figures/
  27_greyscale_figures/         ← step 48 post-processing utility writes here when invoked
  28_c3_detrend/                ← step 33 (Phase 14, cluster framework diagnostics)
  29_within_c3_variance/        ← step 34 (Phase 14, cluster framework diagnostics)
  30_c4_constrained_fit/        ← step 35 (Phase 14, cluster framework diagnostics)
src/
  utils/
    config.py               ← cluster colours/labels, DRAINAGE_DATUM, HEADLINE_LAG, FOREST_INTERCEPTION, FOREST_CIDS, ecological thresholds, UKCP18 scenario factors, BROADLEAF_B2_WINTER, BROADLEAF_B2_SUMMER
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

*CSV tables sit in `data/`; the DEM and all KML layers below live in `data/geo/` and are resolved via `paths.data_geo()` (never hardcode geo filenames outside `paths.py`).*

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


#### Step 9.1 — 09a_paired_baci

**Purpose.** Hierarchical paired BACI for the scraping intervention (CEH36, CEH18, CEH21, CEH22). β₃ era testing, full parameters, Table 4.

**Writes.**

- `09_scrape_03_baci_shifts.csv`
- `09_scrape_07_beta3_confidence.png`
- `09_scrape_02_beta3_significance.csv`
- `09_scrape_01_full_parameters.csv`
- `09_scrape_04_net_benefits.csv`
- `09_scrape_report_numbers.csv`
- `09_scrape_04b_beta3_era_summary.csv`
- `09_tier1_final_cusum.csv`
- `09_scrape_05_tier1_background_drift.png`
- `09_scrape_06_tier2_scraping_signal.png`


#### Step 9.2 — 09b_scraping_propagation

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


#### Step 9.3 — 09c_summer_minima

**Purpose.** Dual-control BACI on summer minima for scraping wells; ecological threshold framing.

**Writes.**

- `09c_03_summer_minima_climate_ctrl.png`
- `09c_04_summer_minima_paired.png`
- `09c_report_numbers.csv`
- `09c_01_summer_minima.csv`
- `09c_02_summer_minima_shifts.csv`


#### Step 9.4 — 09d_scenario_comparison

**Purpose.** CEH36-anchored equilibrium scenario comparison (observed scraping vs hypothetical clearfell/thinning/broadleaf/UKCP18 climate). All scenarios evaluated at CEH36 using that well's own SSM coefficients and Sy.

**Reads.** CEH36 well-level parameters loaded directly from Scripts 01, 03, 17.
Summer climate via `scraping_common.load_summer_climate()`. Scenario constants
(UKCP18 scalers, interception, B2 multiplier defaults) from `config.py`.

**Writes.**

- `09d_01_scenario_comparison.jpg`
- `09d_01_scenario_comparison.csv`
- `09d_02_summer_scenario_comparison.png`
- `09d_02_summer_scenario_comparison.csv`


#### Step 9.5 — 09e_robustness

**Purpose.** CEH36 robustness analyses (raw BACI, synthetic control, SSM residual).

**Writes.**

- `09e_report_numbers.csv`
- `09_scrape_08_ceh36_robustness.png`


#### Step 10.1 — 10i_ceh34_hindcast (prerequisite)

**Purpose.** CEH34 donor-regression hindcast. Reconstructs a pre-2014 trajectory for the synthetic FE well at the WMC3 spatial position using CEH9 as the donor under a linear regression calibrated on the overlap period. Consumed by 10a, 10b, 10e, 10h via `clearfell_common.apply_ceh34_hindcast()`. 10d, 10f, and 10j do not consume the hindcast.

**Reads.**

- `01_wells_clean.csv` (Script 01 (step 1))

**Writes.**

- `10i_01_ceh34_hindcast.csv`


#### Step 10.2 — 10a_ancova_baci

**Purpose.** Three-counterfactual ANCOVA-BACI — primary clearfell BACI result. Forest-control, coastal-control, climate-control comparisons.


#### Step 10.3 — 10b_spatial_step_maps

**Purpose.** Spatial step-change maps (raw and BACI-corrected) for both scraping and clearfell interventions.

**Reads.**

- `data` (raw data)
- `Well_locations_height.csv` (raw data)
- `03_master_data.csv` (Script 03 (step 3))
- `01_wells_clean.csv` (Script 01 (step 1))
- `01_wells_extended.csv` (Script 01 (step 1))
- `10b_spatial_fell_corrected.png` (Script 10B (step 10.3))
- `10b_spatial_fell_raw.png` (Script 10B (step 10.3))
- `10b_spatial_scrape_corrected.png` (Script 10B (step 10.3))
- `10b_spatial_scrape_raw.png` (Script 10B (step 10.3))

**Writes.**

- `10b_spatial_step_data.csv`

**Other.**

  - `OUT_10B_SCRAPE_CORRECTED` passed to `plot_spatial_step`
  - `DATA_DIR` passed to `add_kml_features, load_dem_hillshade`
  - `OUT_10B_FELL_RAW` passed to `plot_spatial_step`
  - `OUT_10B_FELL_CORRECTED` passed to `plot_spatial_step`
  - `OUT_10B_SCRAPE_RAW` passed to `plot_spatial_step`


#### Step 10.4 — 10c_forest_zone_analysis

**Purpose.** Per-well β₁ vs β₂ scatter, β₂ vs elevation regression, C4/C5 boundary map (forest zone spatial analysis).

**Reads.**

- `data` (raw data)
- `06_pear_membership_audit_sitewide.csv` (Script 06 (step 6))
- `07_coeff_maps_data.csv` (Script 07 (step 7))
- `07_coeff_05_cluster_ranges.csv` (Script 07 (step 7)) — per-cluster beta ranges; Paper 1 Table 6

**Writes.**

- `10c_forest_zone_cluster_summary.csv`
- `10c_forest_zone_correlations.csv`
- `10c_01_b1_b2_scatter.png`
- `10c_02_b2_elevation_regression.png`
- `10c_03_c4_c5_boundary_map.png`

**Other.**

  - `DATA_DIR` passed to `add_kml_features, load_dem_hillshade`


#### Step 10.5 — 10d_summer_minima

**Purpose.** Dual-control BACI on summer minima for clearfell wells.


#### Step 10.6 — 10e_coefficient_decomposition

**Purpose.** Mechanistic-direction diagnostic: before/after SSM coefficient shifts (Δβ₁, Δβ₂, Δβ₃) at the clearfell tiers (Impact, Edge, Forest Ctrl, Coastal Ctrl, Climate Ctrl). Reports which SSM pathway moved after felling; the clearfell step *magnitude* is the 10a ANCOVA result, not 10e. Source for Script 21's β₂ multiplier. (v1.4.0, 2026-05-24: the predicted-vs-observed comparison and the `10e_02` output were removed — see `CHANGELOG_script10e_v1_4_0_option_A.md`.)


#### Step 10.7 — 10f_robustness

**Purpose.** SSM-residual and synthetic-control robustness for the clearfell signal.

**Reads.**

- `10f_report_numbers.csv` (Script 10F (step 10.7))

**Writes.**

- `10f_01_ssm_residual_results.csv`
- `10f_02_synthetic_control_results.csv`

**Other.**

  - `OUT_10F_REPORT` passed to `save`


#### Step 10.8 — 10g_diagnostics

**Purpose.** NW10 broadleaf trend, clearfell transect, rolling coefficients.

**Reads.**

- `03_regional_averages.csv` (Script 03 (step 3))
- `10g_report_numbers.csv` (Script 10G (step 10.8))

**Writes.**

- `10g_01_nw10_broadleaf_trend.csv`
- `10g_04_rolling_coefficients.csv`
- `10g_03_clearfell_transect_steps.csv`
- `10g_02_clearfell_transect.png`

**Other.**

  - `OUT_10G_REPORT` passed to `save`


#### Step 10.9 — 10h_synthetic_impact_baci

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


#### Step 10.10 — 10j_impact_edge_contrast

**Purpose.** Direct Impact-vs-Edge BACI contrast that does not invoke an external counterfactual tier. Uses the four Edge wells (CEH16, CEH20, CEH30, CEH31) as the spatial buffer for the Impact tier (WMC3): both share coastal-retreat gradient, climate forcing, and regional groundwater drift, while only the Impact tier experienced the clear-fell treatment. Fits two pooled BACI models — a monthly-mean OLS with well-FE, CWB covariate, and an Impact:Scraped1 asymmetry term (the Edge wells sit outside the 2015 scraping footprint), and an annual Jun–Sep minima OLS with well-FE, on the measured-only summer-minima frame produced by Script 10d. Reports the differential felling step (Impact − Edge) at both resolutions, written to the site-observations registry for downstream consumption. Offered as a corroborator of the headline 10a result whose identification does not pass through any easting × time coastal-erosion covariate.

**Reads.**

- `01_wells_clean.csv` (Script 01 (step 1))
- `01_climate.csv` (Script 01 (step 1))
- `10d_01_summer_minima.csv` (Script 10D (step 10.5))

**Writes.**

- `10j_01_monthly_contrast_results.csv`
- `10j_02_summer_contrast_results.csv`
- `10j_03_contrast_timeseries.jpg`
- `10j_04_summer_minima_contrast.jpg`
- `10j_report_numbers.csv`

**Other.**

  - Updates four entries in `pipeline_site_observations.csv` via `site_observations.update_site_observation()`: `impact_vs_edge_clearfell_monthly_step` (+ `_se`), `impact_vs_edge_clearfell_summer_step` (+ `_se`).


#### Step 10.11 — 10k_four_zone_baci

**Purpose.** Four-zone monthly pooled-panel BACI. Generalises the 10j two-zone method to four zones — Forest control (reference), C3/Warren (a shielded western-dune second control, `phi ≈ 0` expected), Edge, and Impact — stacked into one long-form monthly panel so that every zone-vs-zone contrast comes from a single internally-consistent OLS fit with well fixed effects and cluster-robust standard errors. Reports the three primary zone-vs-Forest felling steps plus the six derived pairwise contrasts (the C3/Warren-bearing derived contrasts are flagged as internal consistency checks; their `p_derived` is not interpretable as significance). The primary clearfell result for §4.6 of the report; 10a's three separate ANCOVAs are retained as a robustness panel. The Impact-vs-Edge derived contrast cross-validates against Script 10j's two-zone monthly contrast.

**Reads.**

- `01_wells_clean.csv` (Script 01 (step 1))
- `01_climate.csv` (Script 01 (step 1))
- `03_master_data.csv` (Script 03 (step 3))

**Writes.**

- `10k_01_four_zone_results.csv`
- `10k_02_pairwise_contrasts.csv`
- `10k_03_easting_sensitivity.csv`
- `10k_04_zone_centroids.jpg`
- `10k_05_contrast_forest.jpg`
- `10k_06_forest_plot.jpg`
- `10k_report_numbers.csv`

**Other.**

  - Adds the `C3_WARREN_WELLS` second-control zone (`ceh1, nw1, nw2, nw11`) from `clearfell_common`.
  - Updates the three primary zone-vs-Forest steps in `pipeline_site_observations.csv` via `site_observations.update_site_observation()`.


#### Step 10.12 — 10l_four_zone_summer_baci

**Purpose.** Four-zone summer-minimum pooled-panel BACI. Applies the 10k four-zone model to the annual Jun–Sep summer-minimum frame produced by Script 10d. The summer panel is annual rather than monthly and the scraping term is dropped at this resolution (as in 10j's summer model). Reports the three primary zone-vs-Forest summer-minimum felling steps and the six derived pairwise contrasts under the same primary/derived discipline as 10k. The summer-minimum result is the conservation-relevant companion to 10k's monthly result.

**Reads.**

- `01_wells_clean.csv` (Script 01 (step 1))
- `01_climate.csv` (Script 01 (step 1))
- `03_master_data.csv` (Script 03 (step 3))
- `10d_01_summer_minima.csv` (Script 10D (step 10.5))

**Writes.**

- `10l_01_four_zone_summer_results.csv`
- `10l_02_summer_pairwise_contrasts.csv`
- `10l_03_c3warren_summer_minima.csv`
- `10l_04_zone_summer_trajectories.jpg`
- `10l_05_summer_forest_plot.jpg`
- `10l_report_numbers.csv`

**Other.**

  - Updates the three primary zone-vs-Forest summer-minimum steps in `pipeline_site_observations.csv` via `site_observations.update_site_observation()`.


#### Step 11 — 11_forecasting_thresholds

**Purpose.** Closed-form P_flood derivation, winter/summer transfer functions (Tables 6, 7, 8), and a per-cluster empirical spring MSL transfer function (Section 5, "Tool A").

Section 5 was added 2026-05-20 (Script 11 v1.1.0 → v1.1.1) as the predictive companion to Script 26's observational MSL5 monitoring metric. For each cluster, an OLS-with-intercept fit on `03_regional_averages.csv` produces an equation of the form

    MSL_y = α · h_max_winter + β · P_win_to_spr + γ · PET_win_to_spr + intercept

where the hydrology year *y* runs from 1 June (*y*−1) to 31 May (*y*) (van Willegen 2025 convention), the winter peak is the maximum of Oct *y*−1 to Feb *y*, and the antecedent forcing totals run Oct *y*−1 to May *y*. Each cluster's transfer function lets managers predict the next year's MSL_y from monthly readings collected through end-February, then add to a rolling four-year history of observed MSLs to update the 5-year MSL5 monitoring statistic without waiting until end-May for the actual reading.

R² ranges 0.73–0.96 across the five clusters (C4 Main Forest and C5 Coastal Forest essentially deterministic at R² ≥ 0.95). A second variant on previous-year MSL as the antecedent input was tested at v1.1.0 and dropped at v1.1.1: R² 0.18–0.44 across the network, statistically non-significant `MSL_prev` coefficient at four of five clusters. The winter peak is the immediate antecedent state and carries the predictive signal.

**Reads.**

- `03_cluster_peak_months.csv` (Script 03 (step 3))
- `03_03_cluster_mechanistic_coefficients.csv` (Script 03 (step 3))
- `03_regional_averages.csv` (Script 03 (step 3)) — Section 5 OLS input

**Writes.**

- `11_forecast_pflood_summary.csv`
- `11_forecast_winter_transfer_functions.csv`
- `11_forecast_summer_transfer_functions.csv`
- `11_forecast_pflood_threshold_equations.csv`
- `11_forecast_spring_transfer_functions.csv` — Section 5 per-cluster equations (Tool A, Table 9)
- `11_forecast_02_spring_calibration.png` — Section 5 5-panel calibration scatter


#### Step 12 — 11b_spatial_thresholds

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
- `11_forecast_winter_transfer_functions.csv` (Script 11 (step 11))
- `11_forecast_summer_transfer_functions.csv` (Script 11 (step 11))
- `11_forecast_pflood_threshold_equations.csv` (Script 11 (step 11))
- `forecaster_template.html` (Script 11B (step 12))

**Writes.**

- `11b_04_flood_frequency.png`
- `11b_03_pflood.png`
- `11b_03_pflood_per_well.csv`
- `11b_01_summer_minima_depth.png`
- `11b_05_table10_pflood_spreadsheet.csv`
- `11b_02_winter_maxima_depth.png`

**Other.**

  - `DATA_DIR` passed to `add_kml_features, load_dem_hillshade`


#### Step 13 — 11c_pflood_achievability

**Purpose.** Per-well categorical priority map for P_flood-based scrape-target identification, operationalising §7 Conclusion 4's λ < 1.5 criterion. Reads Script 11b's per-well λ table and re-presents it as a three-band categorical map (Achievable λ < 1.5, Marginal 1.5 ≤ λ < 2.5, Unreachable λ ≥ 2.5) on the canonical DEM hillshade + KML overlay. Added 2026-05-29 as gap C in the post-review priorities list; lands as a new figure in §5.9 of the main report.

**Reads.**

- `11b_03_pflood_per_well.csv` (Script 11b (step 12))
- DEM hillshade (`data/geo/`)
- KML features (`data/geo/`)

**Writes.**

- `11c_pflood_achievability.png` — operational map for §5.9 / Conclusion 4
- `11c_pflood_achievability_per_well.csv` — per-well lookup table with category column
- `11c_pflood_achievability_results.md` — memo with summary tables and report drop-in text

**Other.**

  - All paths via `utils.paths.OUT_11C_*` (sharing `DIR_11B` with Script 11b since the input lives there).
  - Categorical bin edges (1.5 and 2.5) are operational choices, not derived from a data-driven break: the λ < 1.5 boundary is taken directly from Conclusion 4 text; the marginal-vs-unreachable boundary at 2.5 matches the abstract's wet-winter framing.
  - Standalone diagnostic following the same pattern as `14b_year_of_crossing.py` (post-review additions consuming an earlier-step output and re-presenting it for an operational reader).


### Phase 4 — Climate Projections & Figure Generation

#### Step 14 — 00_climate_summary

**Purpose.** Climate timeseries (full + monitoring period) and well-network summary statistics. Three figures (climate ts, network, summer warming) and three CSVs.

**Reads.**

- `RAF_Valley_Climate.csv` (raw data)
- `01_climate.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))
- `00_01_annual_climate_summary.csv` (Script 00 (step 14))
- `00_01_climate_timeseries.png` (Script 00 (step 14))
- `00_03_summer_warming_trend.png` (Script 00 (step 14))
- `00_03_summer_warming_stats.csv` (Script 00 (step 14))
- `00_02_well_network_summary.png` (Script 00 (step 14))
- `00_02_well_network_summary.csv` (Script 00 (step 14))

**Other.**

  - `OUT_00_SUMMER_WARMING` passed to `str`
  - `OUT_00_CLIMATE_TIMESERIES` passed to `dirname`
  - `OUT_00_WELL_NETWORK_TABLE` passed to `dirname`
  - `OUT_00_WELL_NETWORK_FIG` passed to `dirname`
  - `OUT_00_SUMMER_WARMING_TABLE` passed to `str`
  - `OUT_00_ANNUAL_CLIMATE_TABLE` passed to `dirname`


#### Step 15 — 14_climate_projections

**Purpose.** Climate trajectory projections (summer minima trend, winter exceedance) for all five clusters under UKCP18 RCP8.5.

**Reads.**

- `02_cluster_stats.csv` (Script 02 (step 2))
- `03_regional_averages.csv` (Script 03 (step 3))
- `00_02_well_network_summary.csv` (Script 00 (step 14))
- `14_climate_trajectory_stacked.png` (Script 14 (step 15))
- `14_climate_trajectory_summer.png` (Script 14 (step 15))
- `14_climate_trajectory_winter_flooding.png` (Script 14 (step 15))
- `14_seasonal_extremes_scatter.html` (Script 14 (step 15))

**Writes.**

- `14_annual_extremes.csv`
- `14_summer_trend_stats.csv`
- `14_winter_trend_stats.csv`
- `14_winter_exceedance.csv`

**Other.**

  - `OUT_14_SEASONAL_SCATTER` passed to `render_seasonal_scatter`
  - `OUT_14_CLIMATE_STACKED` passed to `render_stacked_figure`
  - `INT_REGIONAL_AVG` passed to `_compute_winter_exceedance, load_annual_extremes`
  - `OUT_14_CLIMATE_SUMMER` passed to `render_summer_figure`
  - `OUT_14_CLIMATE_WINTER` passed to `render_winter_figure`


#### Step 16 — 14b_year_of_crossing

**Purpose.** Bootstrap year-of-crossing diagnostic for per-cluster summer-minimum trends against Curreli (2013) ecological thresholds. Reads Script 14's annual summer-min table and fits OLS trends per cluster, then bootstraps (n = 1000 resamples of years with replacement) to produce 5/50/95-percentile crossing years for SD15b (0.61 m below ground, wet slack viability) and SD16 (0.98 m below ground, dry slack threshold). Added 2026-05-29 as gap B in the post-review priorities list; replaces the qualitative "around 2030–2032" date band in §7 Conclusion 11 with a stated CI on the year per cluster × threshold.

**Reads.**

- `14_annual_extremes.csv` (Script 14 (step 15))

**Writes.**

- `14b_year_of_crossing.csv` — per-cluster × threshold table (slope, intercept, year-of-crossing 5/50/95 percentiles)
- `14b_year_of_crossing.png` — five-panel figure with observed points, OLS trend + 95% CI cone, threshold lines, crossing-year CI bands
- `14b_year_of_crossing_results.md` — memo with headline table and report drop-in text

**Other.**

  - All paths via `utils.paths.DIR_14` (sharing `DIR_14` with Script 14 since the input lives there). No new path constants added — outputs use the existing `DIR_14` directory.
  - Linear extrapolation only. The bootstrap captures sampling uncertainty in slope and intercept but does NOT capture model-form uncertainty (the assumption that the linear trend extrapolates cleanly). Year-resampling bootstrap; not block-bootstrap (autocorrelation in summer-min residuals is weak).
  - Standalone diagnostic following the same pattern as `11c_pflood_achievability.py` (post-review additions consuming an earlier-step output and re-presenting it for §7).


#### Step 17 — 12_figure_site_overview

**Purpose.** Figure 1 — DEM site overview map.

**Reads.**

- `data` (raw data)

**Other.**

  - `DATA_DIR` passed to `add_kml_features`


#### Step 18 — 13_figure_experimental_design

**Purpose.** Figure 2 — five-tier BACI network plus scraping interventions.

**Reads.**

- `data` (raw data)
- `Well_locations_height.csv` (raw data)

**Other.**

  - `DATA_DIR` passed to `add_kml_features`


### Phase 5 — Depth-Dependent PET

#### Step 19 — 15_depth_dependent_pet

**Purpose.** Depth-dependent PET analysis (exp(−λd) modification, λ profile, fit comparison).

**Reads.**

- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))


### Phase 6 — WTF Cluster Sy Estimation

#### Step 20 — 17_wtf_specific_yield

**Purpose.** WTF cluster-mean Sy estimation (OLS winter and event-median methods, with optional interception correction for forested clusters).


### Phase 7 — Water Balance

#### Step 21 — 16_water_bal

**Purpose.** Water-balance decomposition by cluster; bar/volumetric plots; WTF-corrected variants.

**Reads.**

- `03_regional_averages.csv` (Script 03 (step 3))
- `03_03_cluster_mechanistic_coefficients.csv` (Script 03 (step 3))
- `16_water_bal_table.csv` (Script 16 (step 21))
- `16_water_bal_vol_table.csv` (Script 16 (step 21))

**Writes.**

- `16_water_bal_bar_lay.png`
- `16_water_bal_bar_ms.png`

**Other.**

  - `OUT_16_TABLE` passed to `save_headspace_table`
  - `OUT_16_VOL_TABLE` passed to `save_volumetric_table`


### Phase 8 — WTF Spatial Analysis

#### Step 22 — 18_wtf_spatial

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

#### Step 23 — 19_spatial_groundwater

**Purpose.** Spatial groundwater analysis (head, β fields, water balance, drainage, depth-to-water-table). Self-contained scenario viewer HTML with optional forest drawdown propagation (flow-weighted cost-distance, λ = √(D/β₃)). v2.8.0 (2026-05-27) added a new top row to the viewer's per-cluster scenario summary table reporting the van Willegen et al. (2025) 5-year mean spring water-level shift (ΔMSL5 = mean Δh over March–May, pure-climate framing matching Script 26b); per-well-aggregated β coefficients are used (consistent with the rest of the viewer's table), and the row is validated against Script 26b's per-well CSV (see Step 29 below). The scenario-summary CSV gains a corresponding `season="msl5"` block.

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
- `18_wtf_01_well_sy_estimates.csv` (Script 18 (step 22))
- `26b_msl5_ukcp18_projection_summary_perwell.csv` (Script 26b (step 31), v1.1.0; v2.8.0 cross-script validation only — loaded if present, warns on tolerance breach rather than erroring)

**Writes.**

- `19_scenario_summary.csv` — per (scenario, season, cluster) Δh / Δstorage summary; under v2.8.0 includes a new `season="msl5"` block (6 rows per scenario: 5 clusters + a well-count-weighted SITE row). Consumed by Script 26c (step 32) for the §4.10.1 Δsummer-minimum bars.
- `scenario_viewer.html` — self-contained interactive viewer; v2.8.0 carries the new top ΔMSL5 row in the per-cluster table.

**Other.**

  - `DATA_KML_CLEARFELL` passed to `kml_to_bng`
  - `KML_BROADLEAF` passed to `kml_to_bng`
  - `DATA_KML_FEATURES` passed to `kml_to_bng`
  - The viewer's ΔMSL5 row uses *per-well* aggregated β (mean of well-level OLS within each cluster), consistent with the rest of the viewer; this differs from Script 26b's *cluster-centroid* OLS by 0.5–3.7 mm per cluster per UKCP18 scenario. Both are defensible summaries of the same SSM. The viewer row matches `26b_msl5_ukcp18_projection_summary_perwell.csv` (per-well-aggregated reference) to ≤0.5 mm; the canonical numbers in §3.7.5 / §4.8.4 / §4.10.1 remain anchored to the centroid-fitted `26b_msl5_ukcp18_projection_summary.csv` (consumed by Script 26c).
  - Canopy interception is *not* applied to the ΔMSL5 row (the existing Δh/storage rows do apply it for C4/C5); the asymmetry is documented in a footnote under the viewer table. MSL5 is in any case most ecologically relevant for the non-forest clusters C1–C3.
  - Under the pure-climate framing, land-use presets (clearfell, broadleaf, thinning, baseline) produce ΔMSL5 = 0 identically; the climate-driven UKCP18 2050s / 2080s presets carry the non-zero ΔMSL5 values.


#### Step 24 — 20_spatial_figures

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

#### Step 25 — 21_forestry_scenarios

**Purpose.** Forest-management scenario hydrographs and distributions, BACI zone violins; loads BACI displacement and β₂ multiplier dynamically from 10a/10e. Requires Script 10a v1.3.0+ (which emits the directly-fitted Jun–Sep summer ANCOVA row); running against a stale `10a_report_numbers.csv` raises a clear `RuntimeError` with a remediation message (Script 21 v1.0.3+). Scenario comparison figure uses `scraping_common.compute_scenario_bars()` as the single source of truth for per-cluster scenario values. The synthetic mean-year hydrograph figure has a companion data file `21_forestry_01_hydrograph.csv` (Script 21 v1.2.0+) carrying the plotted monthly depths and a trough/separation summary. The BACI zone-violin summer minima are computed via the shared `clearfell_common` estimator (`annual_summer_minimum()`), per-well-then-aggregate with the Defect-E provenance filter, matching Script 10d by construction (Script 21 v1.1.0+). Script 21 v1.3.0 adds a summer-minimum companion to the scenario figure (`21_forestry_06_summer_scenario.csv`): per-cluster Δ summer-minimum depth for the three forest-management scenarios (clearfell, thinning, broadleaf), produced through the shared `scraping_common` flux→summer-minimum conversion and byte-identical with the forestry rows of `09b_05`.

**Reads.** Cluster parameters via `scraping_common.load_cluster_params()` and
`load_summer_climate()` for the scenario comparison figure. Also reads directly:

- `01_climate.csv` (Script 01)
- `03_regional_averages_maod.csv` (Script 03)
- `03_master_data.csv` (Script 03)
- `01_wells_clean.csv` (Script 01)
- `01_wells_extended.csv` (Script 01)
- `01_wells_provenance.csv` (Script 01)
- `01_well_elevations.csv` (Script 01)
- `10a_report_numbers.csv` (Script 10A)
- `10e_01_coefficient_shifts.csv` (Script 10E)

**Writes.**

- `21_forestry_04_baci_zone_means.csv`
- `21_forestry_04_baci_zone_violin.png`
- `21_forestry_02_distributions.png`
- `21_forestry_02_distributions_means.csv`
- `21_forestry_01_hydrograph.png`
- `21_forestry_01_hydrograph.csv`
- `21_forestry_05_scenario_comparison.jpg`
- `21_forestry_05_scenario_comparison.csv`
- `21_forestry_06_summer_scenario.csv`
- `21_forestry_03_scraping_eras.png`
- `21_forestry_03_scraping_era_means.csv`


### Phase 11 — Coastal-Retreat Gradient Analysis

#### Script 25 — 25_coastal_gradient (step 26)
**Purpose.** Network-scale, physics-based non-linear regression of per-well water-table trends against perpendicular distance to the eroding Caernarfon Bay shoreline. Fits two functional forms (linear-with-cutoff and exponential decay) at three forest-confound specifications (full network, forest-free, C3-only) and partitions each cluster's summer-min slope into climate + coastal-retreat + residual components. Also corroborates the Script 10 BACI `easting × time` absorption against the gradient-model prediction. Since v1.1.0 (2026-05-29) Script 25 also folds in the per-cluster decomposition presentation layer (formerly standalone Script 30) — `25_03_cluster_partition.csv` now carries per-component percentage shares and `25_07_cluster_decomposition.png` displays the five-cluster stacked-bar attribution figure that lands in §4.8.1 of the main report.

**Reads.**

- `data/well_distance_to_coast.csv` (versioned data input; see `data/COASTLINE_PROVENANCE.md`)
- `01_wells_clean.csv` (Script 01)
- `01_wells_extended.csv` (Script 01)
- `01_locations.csv` (Script 01)
- `01_climate.csv` (Script 01)
- `03_master_data.csv` (Script 03)
- `14_summer_trend_stats.csv` (Script 14)
- `10a_02_ancova_full_coefficients.csv` (Script 10a)

**Writes.**

- `25_01_panel_fit_parameters.csv` — all 6 fits (3 specs × 2 forms): δ₀, L, c, SEs, 95% CIs, AIC
- `25_02_per_well_summer_min_slopes.csv` — per-well annual summer-min OLS slope vs distance
- `25_03_cluster_partition.csv` — per-cluster decomposition (observed / gradient / climate / residual + per-component `gradient_pct_of_observed`, `climate_pct_of_observed`, `residual_pct_of_observed` shares; the % columns folded in from Script 30 at v1.1.0)
- `25_04_baci_corroboration.csv` — BACI absorption vs gradient prediction per zone × control
- `25_05_fit_diagnostic.jpg` — two-panel diagnostic figure
- `25_06_baci_corroboration_chart.jpg` — forest plot
- `25_07_cluster_decomposition.png` — horizontal stacked-bar figure of per-cluster climate + coastal + residual attribution (new at v1.1.0, folded in from standalone Script 30; lands in §4.8.1 of the main report)
- `25_report_numbers.csv`

**Other.**

  - All paths via `utils.paths.OUT_25_*` and `paths.DATA_DIST_COAST`.
  - Distance source covers 97 wells, range 147–5,589 m; coastline restricted to Caernarfon Bay High Water Mark (lines 1756 + 1853 of OS Open Map Local TidalBoundary).


### Phase 12 — Supplementary Diagnostics

#### Step 27 — 22_residual_lag_analysis

**Purpose.** AR(1) diagnostics on SSM residuals; α/φ scatter; example residual series by cluster.

**Reads.**

- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))
- `22_03_alpha_phi_scatter.png` (Script 22 (step 27))
- `22_01_ar1_histogram.png` (Script 22 (step 27))
- `22_02_ar1_spatial_map.png` (Script 22 (step 27))
- `22_04_example_residuals_by_cluster.png` (Script 22 (step 27))

**Writes.**

- `22_model_b_fits.csv`
- `22_residuals_wide.csv`

**Other.**

  - `OUT_22_AR1_HIST` passed to `plot_ar1_hist`
  - `OUT_22_AR1_MAP` passed to `plot_ar1_map`
  - `OUT_22_ALPHA_PHI_SCATTER` passed to `plot_alpha_phi_scatter`
  - `OUT_22_EXAMPLE_SERIES` passed to `plot_example_residuals`


#### Step 28 — 23_ridge_recharge_lag_test

**Purpose.** Ridge-proximal recharge lag hypothesis test (cross-correlation, lag vs distance, B10/B11 by cluster).

> **Note (2026-05-17):** Script 23 carries a prominent LIMITATION NOTE in its header docstring (v1.0.1+). The test design is statistically degenerate against this dataset (monthly time resolution cannot resolve sub-monthly travel times; the ~2.5% water-balance residual is at the noise floor of per-well α uncertainty). The script is retained for completeness; its result should not be cited. See §5.3 of the main report and §S.16 of the Methods Supplement for the final framing.

**Reads.**

- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))
- `23_04_b10_b11_by_cluster.png` (Script 23 (step 28))
- `23_01_ccf_headline_ridge_wells.png` (Script 23 (step 28))
- `23_03_peak_lag_spatial_map.png` (Script 23 (step 28))
- `23_02_peak_lag_vs_ridge_distance.png` (Script 23 (step 28))
- `23_05_hypothesis_test_summary.txt` (Script 23 (step 28))

**Writes.**

- `23_ridge_lag_fits.csv`
- `23_residuals_extended_wide.csv`

**Other.**

  - `OUT_23_LAG_VS_DISTANCE` passed to `plot_lag_vs_distance`
  - `OUT_23_LAG_MAP` passed to `plot_lag_map`
  - `OUT_23_CCF_HEADLINE` passed to `plot_ccf_headline`
  - `OUT_23_BETAS_BY_CLUSTER` passed to `plot_betas_by_cluster`
  - `OUT_23_TEST_SUMMARY` passed to `write_test_summary`


#### Step 29 — 24_residual_seasonality

**Purpose.** Residual-seasonality diagnostic (climatology panels, amplitude map, sun-hour correlation, phase by cluster).

**Reads.**

- `RAF_Valley_Climate.csv` (raw data)
- `01_climate.csv` (Script 01 (step 1))
- `02_cluster_stats.csv` (Script 02 (step 2))
- `01_locations.csv` (Script 01 (step 1))
- `01_wells_clean.csv` (Script 01 (step 1))
- `24_02_seasonal_amplitude_map.png` (Script 24 (step 29))
- `24_01_climatology_panels_by_cluster.png` (Script 24 (step 29))
- `24_04_phase_by_cluster.png` (Script 24 (step 29))
- `24_05_diagnostic_summary.txt` (Script 24 (step 29))
- `24_03_sun_residual_correlation.png` (Script 24 (step 29))

**Writes.**

- `24_residual_climatology.csv`

**Other.**

  - `OUT_24_SUMMARY` passed to `write_summary`
  - `OUT_24_AMPLITUDE_MAP` passed to `plot_amplitude_map`
  - `OUT_24_PHASE_BARPLOT` passed to `plot_phase_barplot`
  - `DATA_CLIMATE_RAW` passed to `load_sunshine_hours`
  - `OUT_24_CLIMATOLOGY_PANELS` passed to `plot_climatology_panels`
  - `OUT_24_SUN_CORR_SCATTER` passed to `plot_sun_corr_scatter`


### Phase 13 — Van Willegen MSL analyses

This phase contains three scripts: Script 26 produces the observational MSL5 monitoring metric, Script 26b produces the UKCP18 RCP8.5 climate-projection companion, and Script 26c produces the report-format MSL5 figures cited in §4.8.4 and §4.10.1 of the main report. Scripts 26 and 26b follow the van Willegen et al. (2025) convention (1 March – 31 May spring window; 5-year unweighted mean; hydrology year B running 1 June *y*−1 to 31 May *y*); Script 26c is a display-only companion that reads only canonical outputs from Scripts 26, 26b, and 19 and recomputes nothing.

The two scripts are paired but serve different report sections. Script 26 is the headline observational metric, cited in §4.9.8 of the report (cluster trajectories and spatial MSL5 map). Script 26b is a documented robustness/projection capability discussed briefly in the report's climate-discussion paragraph and presented in full in §S.18b of the Methods Supplement. The Script 26b figure is *not* a main-report figure — the projected ΔMSL5 shifts (1–4 cm at 2050s, 2–4 cm at 2080s under central-estimate RCP8.5) sit within observed interannual variability and below the forest-management BACI signal at this site, so the work is reported as a brief mention plus supplement detail rather than headline figure real estate.

#### Step 30 — 26_van_willegen_msl
**Purpose.** Compute the unweighted 5-year mean spring water level (MSL5), the dune slack vegetation-monitoring metric identified by van Willegen et al. (2025, *Ecological Indicators* 170, 113016) as the best-performing hydrology predictor of community-mean Ellenberg EbF response. Spring is defined as the three months March–May within a Curreli / van Willegen "hydrology year B" (1 Jun *y*−1 to 31 May *y*). The 5-year average is computed across consecutive hydrology years with strict completeness rules (3 of 3 spring months valid per annual MSL; 5 of 5 annual MSLs valid per 5-year mean).

The MSL5 aggregation is observational — it consumes Script 01's monthly water-level series and aggregates them, without using the SSM β coefficients or any other modelled quantities. Since v1.3.2 the script additionally computes an equilibrium wetness index that *is* derived from the β coefficients (see "Equilibrium wetness index" below). Outputs are presented in the depth-below-ground frame (paper convention, negative = below ground) alongside the pipeline's native depth-below-pipe-top frame. The headline output is the per-cluster trajectory of MSL5 over the 2014–2025 window-end range (restricted from the 2009 start of the per-well CSVs because the reference network expanded materially between 2007 and 2010, and the first 5-year window drawn entirely from the post-2010 network is end-year 2014). A secondary 5-year mean of the annual maximum (MAX5) is carried as a column in the CSVs for cross-reference to van Willegen's secondary metric.

The chapter's role in the report is monitoring-oriented, complementary to the predictive summer-minimum framework that drives the Script 11/11b threshold maps and the iterated P_flood derivation. The Curreli SD15b (−0.61 m) and SD16 (−0.98 m) reference lines are drawn on the trajectory plot for context; these are calibrated against summer minima, not MSL5, and the figure caption flags the ~0.54 m offset between the two metrics at the 5-year window scale (network-mean Pearson r = 0.95 with summer minima at the 5-year scale; see §S.18 of the Methods Supplement).

**Method A and Method B (v1.1.2).** Script 26 produces *two* per-cluster MSL5 trajectories that differ in their aggregation:

- **Method A** (per-well aggregation across the extended cluster network) is the **headline monitoring metric**, written to `26_msl_5yr_per_cluster.csv`. ~25 wells per cluster in C5; closest to van Willegen's per-piezometer calibration framework; used in the §4.9.8 trajectory figure and spatial map.
- **Method B** (cluster centroid from `03_regional_averages.csv`, LCSC reference network only) is the **SSM-consistent companion**, written to `26_msl_5yr_per_cluster_centroid.csv`. ~5 wells per cluster in C5; same baseline as the SSM β coefficients, P_flood, and the Script 11 Section 5 transfer function; used by Script 26b's projection figure.

The two methods can differ by tens of cm (mean |Method B − Method A| ≈ 0.30 m across the network; max 0.78 m at C4 2011) because they describe different network compositions, not different aggregation algebra. Both are valid; they answer different questions. The chapter S.18 of the Methods Supplement explains the distinction in editorial detail.

**Equilibrium wetness index and vegetation cross-validation (v1.3.2).** In addition to the observational MSL5, the script computes an equilibrium wetness index (EWI) — the steady-state level implied by each well's SSM coefficients under long-term mean climate, h_disp,eq = (β₁·P̄ − β₂·PET̄)/β₃, with EWI = h_disp,eq − DRAINAGE_DATUM in the pipe frame (below-ground frame adds Upstand_m). Reference wells take β from `03_master_data.csv`; extended wells are fitted in-script via the shared `fit_ssm()` (single pass, flagged `network='extended'`). The index is calibrated onto the MSL5 scale by OLS (MSL5 = a + b·EWI) over the open-dune wells (clusters C1–C3; C4/C5 forest wells are predicted but flagged `open_dune_scope=False`, the coefficients being least constrained there), and a per-well observed-versus-predicted comparison is written so the prediction can be weighed directly. A one-off cross-validation — not part of the recurring pipeline — tests MSL5 and EWI against the van Willegen Ellenberg-F dataset (van Willegen et al. 2024; Hill et al. 1999); the two are statistically indistinguishable (Williams' test, 1959). CEH13/CEH14 (β₃ ≈ 0) and any well below MIN_OBS are excluded. No spatial EWI surface is produced.

**Reads.**

- `01_wells_clean.csv` (Script 01 (step 1)) — reference-network monthly depths
- `01_wells_extended.csv` (Script 01 (step 1)) — extended-network monthly depths
- `01_well_elevations.csv` (Script 01 (step 1)) — Upstand_m for pipe→ground conversion
- `01_locations.csv` (Script 01 (step 1)) — easting/northing for the spatial map
- `01_wells_provenance.csv` (Script 01 (step 1)) — interpolated-cell flag (S.1 limit=1 policy)
- `02_07_cluster_membership_k5.csv` (Script 02 (step 2)) — reference cluster IDs
- `06_pear_membership_audit_sitewide.csv` (Script 06 (step 6)) — extended cluster IDs
- `03_regional_averages.csv` (Script 03 (step 3)) — cluster-centroid monthly series for Method B (v1.1.2)
- `03_master_data.csv` (Script 03 (step 3)) — reference-well SSM β coefficients for the EWI (v1.3.2)
- `01_climate.csv` (Script 01 (step 1)) — RAF Valley monthly P/PET for the EWI long-term climatology (v1.3.2)

**Writes.**

- `26_msl_annual_per_well.csv` — per (well, hydro_year) annual MSL and MAX with completeness flags
- `26_msl_5yr_per_well.csv` — per (well, end_year) 5-year MSL5 and MAX5 with cluster IDs
- `26_msl_5yr_per_cluster.csv` — **Method A** cluster-mean trajectory: mean, median, std per (cluster, end_year). Headline monitoring metric.
- `26_msl_5yr_per_cluster_centroid.csv` — **Method B** cluster-centroid trajectory from `03_regional_averages.csv`. SSM-consistent companion (v1.1.2).
- `26_msl_5yr_latest_per_well.csv` — most-recent valid MSL5 per well (input for the spatial map)
- `26_msl_5yr_trajectory.png` — cluster-mean MSL5 trajectory with SD15b/SD16 reference lines and intervention markers (report figure; Method A)
- `26_msl_5yr_map.png` — IDW-interpolated MSL5 surface with DEM hillshade, KML overlays, ridge mask; van Willegen quadrat wells flagged (report figure; Method A per-well basis)
- `26_msl_5yr_quadrat_wells.png` — per-well trajectories at the 17 van Willegen co-located quadrat wells (supplement figure)
- `26_msl_results.txt` — run transcript with cluster summary and per-quadrat-well values
- `26_equilibrium_wetness_index_per_well.csv` — per-well EWI (pipe & bg frames, β, cluster, network tier) (v1.3.2)
- `26_ewi_msl5_comparison.csv` — per-well observed vs EWI-predicted MSL5, residual, `open_dune_scope` & `in_van_willegen` flags (v1.3.2)

**Other.**

  - `INTERVENTION_MARKERS` built from `utils.scraping_common` canonical dates (SCRAPING_DATE, INTERVENTION_DATE, SCRAPING_DATE_2)
  - All methodological constants sourced from `utils.config` (MSL_SPRING_MONTHS, MSL_MIN_MONTHS_PER_SPRING, MSL_MIN_YEARS_IN_WINDOW, MSL_TRAJECTORY_START_YEAR, VW_QUADRAT_WELLS)
  - All output paths sourced from `utils.paths` (OUT_26_*)


#### Step 31 — 26b_van_willegen_msl_projections
**Purpose.** Project per-cluster MSL5 shifts under UKCP18 RCP8.5 50th-percentile Wales scenarios (2050s and 2080s) using the single-step monthly Δh perturbation pattern documented in Script 21 / `model_utils.monthly_perturbation`. The script is a robustness / climate-sensitivity capability rather than a forward-in-time forecast.

**Method.** For each cluster, the monthly Δh perturbation is

    Δh(m) = β₁ · (P_scen(m) − P_base(m)) − β₂ · (PET_scen(m) − PET_base(m))

where β₁ and β₂ are the cluster's SSM coefficients (Script 03), and P_scen / PET_scen apply the UKCP18 seasonal multipliers to the observed monthly climatology. The spring window (Mar / Apr / May) is averaged to give a single ΔMSL5 constant per cluster per scenario:

    ΔMSL5 = mean(Δh_Mar, Δh_Apr, Δh_May)

Because the perturbation is linear in P and PET and the multipliers are constant year-on-year (climatology shift, not interannual sequence), the projected trajectory is the observed Method B trajectory shifted by this constant. Three findings worth noting:

1. **The spring window has structural cancellation**: winter +P partly offsets summer +PET, so the net ΔMSL5 is modest (1–4 cm at 2050s, 2–4 cm at 2080s). Applying the same multipliers to summer minima would produce much larger shifts.
2. **C4 Main Forest has the largest shift** (highest β₂ = 2.55, most PET-sensitive); C1 Lake Edge and C5 Coastal Forest have the smallest (low β₂).
3. **The climate signal is small relative to forest management at this site.** The BACI clearfell step is +13.6 cm at the Forest Impact tier — 3–7× larger than central-estimate UKCP18 spring climate shifts.

UKCP18 multipliers used (matching Script 19 `SCENARIO_PARAMS`):

| Scenario | sP_winter | sP_summer | sPET_winter | sPET_summer |
|---|---|---|---|---|
| 2050s | 1.10 | 0.85 | 1.05 | 1.20 |
| 2080s | 1.20 | 0.70 | 1.10 | 1.35 |

Winter = Nov–Mar; Summer = May–Sep; April and October are shoulder months taking the mean of the winter and summer multipliers. The 2050s constants also exist in `utils.config` (`UKCP18_DRY_*` / `UKCP18_WET_*` pairs) but the 2080s constants are currently hardcoded in this script; a follow-up could add `UKCP18_2080s_*` to `utils.config` and have Script 19 and Script 26b share them.

**What this is and is not.** This is a perturbation overlay — "what would the observed 2014–2025 MSL5 trajectory have looked like if the UKCP18 2050s climate had been in force throughout that period?" It is *not* a forward-in-time simulation; the single-step perturbation pattern avoids the SSM drift problem documented in Script 21, consistent with the limitations of the steady-state SSM. Authors should also note the standard UKCP18 caveat: the multipliers are 50th-percentile central estimates, and the 5th–95th percentile ranges span much wider intervals at end-century (Met Office, 2018).

**Editorial weighting.** Script 26b is a documented capability; its outputs are summarised in one sentence of the report's climate discussion and in §S.18b of the Methods Supplement, but the script does *not* produce a headline report figure. The projected magnitudes (1–4 cm) are smaller than (a) observed interannual variability, (b) the BACI forest-management signal, and (c) the Method A vs Method B aggregation difference itself — so the result is reported as evidence of climate-signal scale at this site rather than as a foregrounded prediction.

**Reads.**

- `03_03_cluster_mechanistic_coefficients.csv` (Script 03 (step 3)) — cluster SSM β coefficients
- `01_climate.csv` (Script 01 (step 1)) — RAF Valley monthly P, PET (climatology baseline)
- `26_msl_5yr_per_cluster_centroid.csv` (Script 26 (step 30), v1.1.2 Method B) — observational baseline overlaid in figure

**Writes.**

- `26b_msl5_ukcp18_projection.png` — 2×3 small-multiple: 5 per-cluster trajectory panels (per-panel auto-scaled y-axes) plus 1 ΔMSL5 bar chart (cm units, coloured by cluster, hatched for 2080s). Supplement figure (§S.18b).
- `26b_msl5_ukcp18_projection_summary.csv` — **canonical centroid-fitted** per (cluster, scenario) summary: β₁, β₂, spring Δh mean, observed window mean, perturbed window mean, mean shift. β fitted by OLS on the cluster-centroid hydrograph (`03_regional_averages.csv`). The reference source for the §3.7.5 / §4.8.4 / §4.10.1 report numbers and the §S.18b chapter; consumed by Script 26c.
- `26b_msl5_ukcp18_projection_summary_perwell.csv` — **secondary per-well-aggregated** per (cluster, scenario) summary, added v1.1.0 (2026-05-27). β fitted per-well on `03_master_data.csv`, then arithmetically averaged within each cluster (5 cluster rows + a well-count-weighted SITE row per scenario). Validation target for the Script 19 v2.8.0 viewer ΔMSL5 row (per-well aggregation is the viewer's existing convention). Differs from the canonical centroid summary by 0.5–3.7 mm per cluster per scenario — both are defensible summaries of the same SSM. Not used by Script 26c.
- `26b_monthly_delta_h_per_cluster.csv` — full 12-month Δh per cluster per scenario (120 rows: 5 clusters × 2 scenarios × 12 months)
- `26b_msl5_ukcp18_results.txt` — run transcript

**Other.**

- UKCP18 multipliers hardcoded in `UKCP18_SCENARIOS` at the top of the script; documented in the docstring; cross-referenced to Script 19's `SCENARIO_PARAMS` and `utils.config.UKCP18_*`
- Δh perturbation uses the pattern from `utils.model_utils.monthly_perturbation()` but with `β₂_scen = β₂_base` (no land-use change) and the PET shift handled directly (see script docstring `_compute_monthly_delta_h`)
- All output paths via `utils.paths.OUT_26B_*`


#### Step 32 — 26c_msl5_report_figures
**Purpose.** Produce the two report-format MSL5 figures cited in §4.8.4 and §4.10.1 of the main report. The script is a display-only companion to Scripts 26 and 26b — it reads their canonical outputs (and Script 19's `19_scenario_summary.csv`) and recomputes nothing. The methodological pair is Scripts 26 (observational MSL5) and 26b (UKCP18 projection); Script 26c is the report-rendering step that turns those canonical outputs into the two figures used in the report's results chapter.

**Figure 1 — `fig_msl5_trajectory_report.png` (cited in §4.8.4).** Cluster-mean MSL5 trajectory 2014–2025, plotted against the Curreli (2013) SD15b (−0.61 m) and SD16 (−0.98 m) reference values, with the SD16 dry-slack zone shaded for visual emphasis. It is the report-format companion to Script 26's methods-context figure `26_msl_5yr_trajectory.png`: the two figures show the same data (Method A, cluster trajectories under the 2014–2025 window-end restriction); the difference is that the methods-context figure retains the intervention markers (2015 scrape, 2017 clearfell, 2023 re-scrape) for methodological clarity, while the report-format figure omits them and adds the SD16 shading and 2025 value labels for direct ecological readability.

**Figure 2 — `fig_msl5_vs_summer_min_projection.png` (cited in §4.10.1).** Two-panel horizontal-bar contrast of ΔMSL5 against Δsummer-minimum for the five clusters under UKCP18 RCP8.5, 2050s in the top panel and 2080s in the bottom. ΔMSL5 values come from Script 26b's `26b_msl5_ukcp18_projection_summary.csv`; Δsummer-minimum values come from Script 19's `19_scenario_summary.csv` (`season = summer`, `dh_mean_m` column — the seasonal mean of monthly Δh over the SUMMER_MONTHS window, treated here as the closest SSM correlate to the annual summer minimum). The figure makes one scientific point: the spring baseline metric MSL5 is substantially better buffered against the projected climate trajectory than the summer-minimum metric, by a factor of 3–6 across all five clusters and both horizons.

**Reads.**

- `26_msl_5yr_per_cluster.csv` (Script 26 (step 30), Method A) — cluster-mean trajectory series
- `26b_msl5_ukcp18_projection_summary.csv` (Script 26b (step 31)) — per-cluster ΔMSL5 under 2050s and 2080s
- `19_scenario_summary.csv` (Script 19 (step 23)) — per-cluster seasonal Δh; the `season=summer` rows supply the Δsummer-minimum bars

**Writes.**

- `fig_msl5_trajectory_report.png` — report-format trajectory figure (§4.8.4)
- `fig_msl5_vs_summer_min_projection.png` — two-panel ΔMSL5 vs Δsummer-minimum contrast (§4.10.1)
- `26c_results.txt` — run transcript with the values plotted in each figure

**Other.**

- No new analytical computation; the script is a display step.
- All output paths via `utils.paths.OUT_26C_*` / `DIR_26C`.


### Phase 14 — Cluster Framework Diagnostics (post-review)

Phase 14 was added on 2026-05-29 following the post-review pass on the main report (Hollingham 2026). Three diagnostic scripts test post-Script-25 implications for the cluster framework documented in §5.1 and §4.2.2 of the report. All consume already-produced pipeline outputs and write into their own output directories; all are documented in Methods Supplement §S.19.

#### Script 28 — 28_c3_detrend_check (step 33)

**Purpose.** Quantitative validation of the §5.1 aquifer-architecture framing. Tests the hypothesis that C3 is mechanistically C2 with a coastal-erosion drift superimposed by de-trending each well's monthly hydrograph against the Script 25 forest-free linear-capped gradient and re-classifying against the un-de-trended cluster centroids. The H1-supporting outcome would be that ≥17 of 19 testable C3 wells (the 21-well C3 cluster minus the two intervention wells CEH36 and WMC3) migrate to a C2 best-match. The headline result (2026-05-29) is **H0 confirmed**: 0 of 19 C3 wells genuinely migrate; the C3/C2 distinction is constitutive aquifer architecture, not a coastal-drift artefact.

**Reads.**

- `02_cluster_stats.csv` (Script 02)
- `01_wells_clean_maod.csv` (Script 01)
- `03_regional_averages.csv` (Script 03)
- `25_01_panel_fit_parameters.csv` (Script 25)
- `25_02_per_well_summer_min_slopes.csv` (Script 25)

**Writes.**

- `28_c3_detrend.csv` — per-well: original best-match, de-trended best-match, sensitivity outcomes
- `28_c3_detrend_results.md` — memo with headline, decision rule, robustness summary
- `28_c3_detrend_panel.png` — 4-panel figure (original vs de-trended hydrographs, classification scatter, sensitivity bars)

**Other.**

- All paths via `utils.paths.OUT_28_*`.
- Routed from `HANDOVER_c3_detrend_check.md`; documented in §S.19.1 of the Methods Supplement; supports the §5.1.1 paragraph on aquifer-architecture validation in the main report.

#### Script 29 — 29_c3_within_variance_check (step 34)

**Purpose.** Characterises the within-cluster heterogeneity for C3 once cluster identity is validated (Script 28). Regresses nine per-well behavioural metrics — slope_m_yr, β₁, β₂, β₃, drainage timescale τ, long-term mean head, summer-min depth, winter-max depth, seasonal amplitude — against five spatial and hydrogeological predictors (Script 25 exponential coastal predictor, distance to CEH36, distance to forest edge, ground elevation, depth-to-water). Reports R² per metric (univariate and full model) and drop-one unique contributions to identify which predictors carry distinct signal. Headline finding (2026-05-29): ~70–80% of within-C3 variance in the SSM coefficients is explained by spatial position, with distance to CEH36 emerging as the strongest unique predictor across β₁/β₂/β₃/τ — a hydrogeological axis within C3 anchored near the SW interior, distinct from coastal proximity.

**Reads.**

- `02_cluster_stats.csv` (Script 02)
- `01_wells_clean_maod.csv` (Script 01)
- `01_locations.csv` (Script 01)
- `07_spatial_coefficients/07_coeff_maps_data.csv` (Script 07)
- `07_spatial_coefficients/07_coeff_05_cluster_ranges.csv` (Script 07)
- `25_01_panel_fit_parameters.csv` (Script 25)
- `25_02_per_well_summer_min_slopes.csv` (Script 25)
- `data/Features.kml` (forest polygon for dist_forest predictor)

**Writes.**

- `29_within_c3_variance.csv` — per-well metrics + predictors
- `29_univariate_R2.csv` — single-predictor R² per metric
- `29_drop_one.csv` — drop-one unique contribution per predictor × metric
- `29_within_c3_variance_results.md` — memo with R² matrix, headline interpretation, caveats
- `29_within_c3_variance_panel.png` — 6-panel figure (per-well metric scatter, drop-one heatmap)

**Other.**

- All paths via `utils.paths.OUT_29_*`.
- Documented in §S.19.2 of the Methods Supplement; supports the §5.1.1 paragraph on within-C3 spatial structure in the main report.


#### Script 30 — 30_c4_constrained_fit (step 35)

**Purpose.** Triangulation-anchored constrained-β₃ sensitivity for C4 Main Forest. The unconstrained per-well SSM is degenerate at C4 — β₂ and β₃ are collinear, β₃ collapses toward zero (negative at CEH14), and the inflated β₂ compensates. The script holds β₃ at a value triangulated from the substrate (C4 is C2/C3-grade aeolian sand) and the clean coastal-forest tree effect (C5 − C3, read from the inland C5 wells to strip the coastal gradient), giving the anchor −β₃ ≈ 0.058, and refits β₁/β₂ through the canonical `fit_ssm(fixed_beta_3=...)`. The corrected centroid lands on the C3 coefficient set (β₂ 1.86, β₁ 2.99), showing C4's apparent anomaly is fit degeneracy on a thinner, lower-Sy substrate rather than a hydrogeological feature. Labelled sensitivity — not a coefficient revision; the unconstrained fit remains the method-consistent record in `03_master_data.csv`.

**Reads.** `01_wells_clean.csv`, `01_climate.csv`, `01_locations.csv`, `03_master_data.csv`, `26_msl_5yr_per_well.csv` (cluster ids), `17_wtf_well_sy.csv`.

**Writes.** `30_c4_constrained_perwell.csv`, `30_c4_constrained_report_numbers.csv`, `30_c4_constrained_fit.png`.

**Where it lands.** §4.2.2 (results flag) and §5.6.1 (substrate decomposition) of the main report, the corrected-C4 column of Table 3, and Methods Supplement §S.19.3.

### Phase 15 — Observed Differential Change, Envelope, and Driver Validation (Scripts 32, 33, 35, 36, 37, 37b)

Step 36 — `32_differential_movement.py` — the secular differential drift of the spring water table (report Fig 59). Per-well OLS trend of the anomaly (well minus site-mean spring level) against year, with AR(1)-corrected significance cross-checked by a moving-block bootstrap. Window-robust by construction; the robust signal is the coastal-margin decline. Reads `01_wells_clean.csv`, `01_locations.csv`, `03_master_data.csv`.

Step 37 — `33_envelope_amplification.py` — the climate-swing amplification field and drought-floor surface (report Fig 60). Compares genuine wet/dry extremes (antecedent-matched) rather than two marginal windows. The amplification panel (Fig 60a) uses the CO-TEMPORAL per-well coefficient from `utils.envelope_metric` (each well's swing ÷ the reference-core swing recomputed over that well's own extreme years — common-mode removed, artefact-free; forest ~1.7×, lake ~0.6×, site-mean swing ~0.75 m). The drought-floor (Fig 60b) is raw dry-extreme depth with the ecological threshold contoured. CEH13/CEH14 are INCLUDED (the coefficient is observational and independent of the SSM); only the Llyn Rhos-Ddu lake gauge is excluded. Reads the same three canonical inputs.

Step 38 — `35_per_well_amplification.py` — the per-well climate-sensitivity coefficient (Paper 1 aquifer characterisation), the discrete companion to Step 37's surface. Same co-temporal method via `utils.envelope_metric`, over wider antecedent-screened extreme pools for per-well robustness and to reach short-record wells. Produces a coefficient table (with delete-one-year jackknife 90% CIs and an A/B/C confidence tier by record completeness), an SSM-calibration figure (coefficient vs the independently-fitted β₂/β₃ — the regression uses only reliable-β wells; SSM-unreliable wells such as CEH13/CEH14 are shown but not fitted), and a discrete per-well marker map. No interpolated surface (that is Step 37's job). Reads `01_wells_clean.csv`, `01_locations.csv`, `03_master_data.csv` and the Script 06 Pearson membership audit.

Step 39 — `36_absolute_climate_trend.py` — the absolute climate-removed per-well secular trend map (report Figure 63). Unlike Step 36's differential anomaly (well minus site-mean, which inverts sign over a wet-spring-lifted window), this is an **absolute** trend: a per-well joint OLS `h(t) = a + b·CWB(t) + c·t` against the spring climatic water balance (CWB, MAM P − PET, no lag), with the secular trend `c` orthogonal to the climate term by construction. A coverage filter excludes wells whose record can't support a trend over the window (pre-2011 start, ≥80% window span). Primary window 2005–2025; robustness window 2011–2025. Only the lake gauge is excluded; CEH13/CEH14 are retained (observational, independent of the SSM). Interpolated via `add_idw_surface()` (hull_buffer_m=100) to the canonical grid. Reads `01_wells_clean.csv`, `01_locations.csv`, `03_master_data.csv`, `01_climate.csv`. Outputs to `outputs/36_absolute_climate_trend/`: `36_absolute_climate_trend_per_well.csv`, both period maps, `36_results.txt`. Promoted to analytical-default tier 2026-07-13 (Task E) — cited directly in main-report §5.7.5 (per-cluster trend values).

Step 40 — `37_driver_validation.py` — per-driver scale-factor regression validating Script 20's modelled driver-change field against Step 39's climate-corrected per-well trends. `dh_corr,i = s_coast·coast_i + s_cf·clearfell_i + c + ε_i`, OLS with HC3 robust SEs, three windows (2006–2012, 2018–2025, 2005–2025); C2 Dune is the driver-free negative control, C1 Lake Edge excluded (sluice-controlled). A validation step — sets no amplitude used elsewhere. Reads Script 36's per-well endpoint differences, Script 20's unit driver fields, δ₀/L from Script 25, the clearfell step from `10a_report_numbers.csv`. Outputs to `outputs/37_driver_validation/`: `37_scale_factors_by_window.csv`, per-well CSV, predicted-vs-observed/residual maps, `37_implied_delta0_trajectory.png`, `37_results.txt`. **Headline result is a bounded null**: every scale-factor CI spans zero (s_coast 0.53 [−0.12, 1.18] full-record) — the coastal and clearfell fields are collinear (r≈−0.48 with easting) and per-well residual scatter exceeds the driver amplitudes, so the dominant resolvable component of change is the uniform intercept (common-mode), not the driver-shaped fields. Promoted to analytical-default tier 2026-07-13 (Task E) — the driver-validation result is being written into main-report §5.7.

Step 41 — `37b_driver_footing.py` — Part B: comparative driver footing, placing forest/scrape/coast on a common footing over 2005→2025 in three currencies (peak local head change; area-integrated change in mm·ha and, via Sy=0.311, m³; Curreli 2013 threshold crossings), each driver split into gain and loss components. Uses **observed anchors** (clearfell +119.6 mm, scrape on-site +129.4 mm / off-site −54.5 mm) and the **modelled** Script 20 fields at 2025 amplitude — never Step 40's scale factors, which are null. First-order linear superposition, an upper bound in overlap zones. Outputs to `outputs/37b_driver_footing/`: `37b_driver_footing.csv`, comparative figure. Headline volumes: coastal erosion −227,108 m³; scrape net −63,759 m³ (on-site +613 mm·ha vs off-site −21,470 mm·ha); clearfell +17,132 m³ (the only unambiguous net relief). Promoted to analytical-default tier 2026-07-13 (Task E) — the comparative-footing result is being written into main-report §5.8.

Both Steps 36 and 37 stand opposite the §5.7.5 window-sensitivity caution: what the record robustly *can* show, beside what a two-window comparison cannot. Constants in `config.py` (`DIFF_*`, `ENVELOPE_*`, `ACT_*`); paths in `paths.py` (`DIR_32/OUT_32_*`, `DIR_33/OUT_33_*`, `DIR_36/OUT_36_*`, `DIR_37/OUT_37_*`, `DIR_37B/OUT_37B_*`).

### Phase 16 — Window Sensitivity, Coastal Transect, and Supplementary Cluster Diagnostics (Scripts 24b, 31, 31b, 34, 38)

Five standalone diagnostics wired into the orchestrator so they regenerate whenever upstream data change; none re-fits the SSM. Steps 45 (Script 34) and 46 (Script 38) run analytical-default as of 2026-07-13 (Task E); Steps 42–44 (Scripts 24b, 31, 31b) remain opt-in (`--with-supplementary`).

Step 42 — `24b_residual_climatology.py` — cluster-stratified residual climatology, discriminating among three candidate mechanisms for the seasonal structure in Script 24's SSM residual field (winter-phased nonlinear recharge, site-wide; ridge-derived lateral input, ridge-proximal/forest-concentrated; canopy-interception over-estimation, forest-confined), via the cluster-stratified winter-minus-summer contrast plus a within-forest ridge-distance gradient. Reads Script 22's per-well residuals, Script 03's cluster/coordinate data, and the site forest polygon. Outputs to `outputs/24b_residual_climatology/`: `24b_01_cluster_climatology.csv`, `24b_02_peak_winter_minus_summer.csv`, `24b_03_per_well_winter_minus_summer.csv`, `24b_04_cluster_climatology.png`, `24b_05_interpretation.txt`. Opt-in tier — mentioned only in the main report's Phase 16 methods-overview enumeration, no figure/number of its own reproduced elsewhere in the report.

Step 43 — `31_cluster_validation.py` — independent validation of the k=5 partition against evidence the clustering never used, organised by independence tier: Tier 1 external (geography, forest polygon, coast distance, elevation); Tier 2 metric-independent (hydrograph magnitude descriptors — the clustering used correlation/shape, not magnitude); Tier 3 convergent (same water levels, different estimation method — SSM/WTF/LCSC); Tier 4 robustness (does k=5 survive alternative linkage/distance metrics — ARI against the canonical Ward+Pearson partition). All canonical numbers read live from pipeline CSVs. Outputs to `outputs/31_cluster_validation/`: `31_validation_summary.csv`, `31_method_robustness_ari.csv`, `31_forest_confusion.csv`, `31_forest_borderline.csv`, `31_cluster_validation_panel.png`. Opt-in tier — same enumeration-only report status as Script 24b.

Step 44 — `31b_separation_vs_recoverability.py` — standalone companion to Step 43. For each independent variable X, places separation (η², variance in X explained by the partition) beside recoverability (ARI, whether Ward k=5 on standardised X alone rebuilds the canonical clusters). The point: separation is consistently high while recoverability is consistently low — the clusters differ on these variables but the variables alone don't reconstruct them, because hydrograph timing carries information no static attribute holds. Reads `01_well_elevations.csv` (dist_coast_m) and the same cluster/partition inputs as Step 43. Outputs to `outputs/31_cluster_validation/`: `31b_separation_vs_recoverability.csv`, `31b_separation_vs_recoverability.png`. Opt-in tier — same enumeration-only report status.

Step 45 — `34_window_sensitivity.py` — the MSL5 two-window sensitivity demonstration (report §5.7.5). Places the single 2017→2023 MSL5 comparison (the §4.9.8 headline, −96.8 mm) inside the envelope of every admissible window pair, deliberately including pairs touching the anomalously wet 2024 spring, to show the two-window method cannot resolve absolute site-wide change. Reads the committed per-well annual spring MSL (`26_msl_annual_per_well.csv`). Admissible pair = common panel ≥ `config.MSL5_WINDOW_MIN_PANEL` (40) wells. Outputs to `outputs/34_window_sensitivity/`: `34_window_matrix.csv`, `34_results.txt`, `34_window_sensitivity.png`. **Headline result:** site-mean change spans −0.14 to +0.22 m across 66 admissible pairs, changing sign (19 falling, 47 rising); most negative pairing 2017→2020 (−136 mm), most positive 2015→2024 (+221 mm). Promoted to analytical-default tier 2026-07-13 (Task E) — extensively cited with numbers in main-report §5.7.5.

Step 46 — `38_coastal_transect.py` — the coast-to-inland MAM transect, a model-free observational test of whether the coastal head gradient grows (erosion-consistent) or stays a constant offset (static substrate-geometry-consistent). Coastal anchor CEH22, inland anchor NW4 (~1 km inland, outside the Script 25 drawdown reach L≈894 m); CEH40/CEH41 are annotated profile-only points. Headline metric: coast-minus-inland MAM head difference, AR(1)-corrected OLS trend, 2010–2023 (n=14). Reads `01_wells_clean.csv` and δ₀/L from Script 25's `25_01_panel_fit_parameters.csv`. Outputs to `outputs/38_coastal_transect/`: `38_coast_inland_difference.jpg`, `38_transect_profile.jpg`, `38_transect.csv`, `38_results.txt`. **Headline result:** −28.2 mm/yr (95% CI −34.2 to −22.0), essentially matching Script 25's modelled δ₀ (−29.0 mm/yr) from an entirely independent construction. Promoted to analytical-default tier 2026-07-13 (Task E) — cited with full numbers in main-report §4.8.3.

### Phase 17 — Synthesis Figure and Greyscale Conversion

Step 47 — `09f_management_effects.py` — the spatial-reach synthesis figure (management interventions + coastal retreat, §5.8; two-pass, reads Scripts 20/25/09d/10a with documented first-pass fallbacks via `pipeline_params.default_value()`). Step 48 — `27_greyscale_figures.py` — converts all colour figures in `outputs/` to journal-ready greyscale versions under `outputs_bw/`. Discovery-based: rglobs the colour output tree; no per-figure paths needed. See the script docstring for usage flags (`--enhanced`, `--dpi`, `--skip-maps`, `--exclude-problem`, `--dry-run`). Renamed from `26_greyscale_figures.py` on 2026-05-20 to free script number 26 for the van Willegen MSL step; renumbered to step 31 on 2026-05-27 when Script 26c was added to Phase 13; renumbered to step 35 on 2026-05-29 when Scripts 28 and 29 were added as Phase 14; renumbered to step 36 on 2026-06-23 when Script 30 (C4 constrained-β₃) was appended to Phase 14; renumbered to step 42 on 2026-06-26 when Scripts 32 and 33 were added as Phase 15; renumbered to step 43 on 2026-06-27 when Script 35 (per-well coefficient) was added as Phase 15 step 38; renumbered to step 44 on 2026-07-02 when Script 09f (spatial-reach synthesis) was added to Phase 17 ahead of it; renumbered to step 47/48 (09f/27) on 2026-07-05–08 as Scripts 36, 37, 37b, and 38 were wired in ahead of it.


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
| Table 6 | Scraping β₃ era coefficients | 09a | `09_scrape_04b_beta3_era_summary.csv` |
| Table 7 | Clearfell ANCOVA-BACI results | 10a | `10a_report_numbers.csv` |
| Table 8 | Per-well summer min shifts | 10d | `10d_04_summer_minima_forest_ctrl.png` (source CSV) |
| Table 9 | Mixed-effects clearfell step | 10d | (embedded in 10d output) |
| Table 10 | Before/after clearfell SSM coefficients | 10e | `10e_01_coefficient_shifts.csv` |
| Table 11 | *Withdrawn* — predicted-vs-observed comparison removed in 10e v1.4.0 | 10e | (no longer produced) |
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
| 12 | Pearson integration map (all 88) | 06 | `06_pear_02_integration_map.png` |
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
- `MSL_SPRING_MONTHS = (3, 4, 5)` / `MSL_HYDRO_YEAR_START_MONTH = 6` / `MSL_DEFAULT_WINDOW_YEARS = 5` — van Willegen (2025) 5-year MSL definition
- `MSL_MIN_MONTHS_PER_SPRING = 3` / `MSL_MIN_YEARS_IN_WINDOW = 5` — strictness rules (3-of-3 spring months, 5-of-5 annual MSLs)
- `MSL_TRAJECTORY_START_YEAR = 2014` — first window-end drawn entirely from the post-2010 network
- `VW_QUADRAT_WELLS` — the 17 piezometers van Willegen (2025) co-located with permanent vegetation quadrats (calibrated EbF reference subset)
- `INTERVENTION_COLOUR_SCRAPE = '#7b3294'` / `INTERVENTION_COLOUR_CLEARFELL = '#e66101'` — print-safe colours for trajectory event markers
- `UKCP18_*_P_*` / `UKCP18_*_PET_*` — UKCP18 RCP8.5 Wales scenario multipliers

SSM keys used throughout the pipeline are the **long form**: `beta_1_recharge`, `beta_2_atmospheric_draw`, `beta_3_drainage`. These are the column names in `03_master_data.csv` and the keys returned by `model_utils.fit_ssm()`.
