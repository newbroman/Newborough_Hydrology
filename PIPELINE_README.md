# Newborough Warren Groundwater Analysis Pipeline
## Script Input/Output Reference

This document describes the data flow between all pipeline scripts, identifying
which files each script reads, which it produces, and which outputs feed into
the paper as figures, tables or into downstream scripts.

Run order: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 11b → 12 → 13 → 14 → 15 → 17 → 16 → 18 → 19 → 20 → 21

Scripts 19a and 19b are not part of the numbered pipeline. They build the
self-contained HTML scenario viewer and are run separately via option 4 in
the interactive menu, or with `python run_analysis.py --viewer`.

Critical ordering constraints:
- Script 17 (WTF Sy) must run before script 16 (water balance)
- Script 18 (WTF spatial) must run before script 19 (spatial groundwater)
- Script 11b requires outputs from scripts 11 and 06
- Script 21 requires `03_cluster_averages_maod.csv` from script 03
- Script 19a/19b (viewer) requires script 19 to have run; script 14 should
  also have run for the seasonal extremes tab to be populated

---

## Data Directory Structure

```
data/                          ← raw input data (never modified)
outputs/                       ← all generated outputs
  00_climate_summary/
  02_clustering/
  03_state_space_model/
  04_cluster_visualisations/
  05_pearson_affinity/
  06_pearson_extended/
  07_boundary_intercept/
  08_model_benchmarking/
  09_scraping_intervention/
  10_clearfell_baci/
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
utils/                         ← shared utility modules
  config.py                    ← cluster colours, labels
  data_utils.py                ← cleaning, normalisation functions
  map_utils.py                 ← DEM, KML, basemap helpers
  model_utils.py               ← SSM fitting helpers
  paths.py                     ← all path constants
```

---

## Raw Data Inputs (data/ directory)

| File | Description | Used by |
|---|---|---|
| `Newborough_Cleaned_For_Model.csv` | Raw dipwell records | 01, 09, 10 |
| `Well_locations_height.csv` | Well coordinates and pipe-top elevations | 01 |
| `RAF_Valley_Climate.csv` | Monthly rainfall and temperature | 01, 09, 10 |
| DEM `.tif` files | LiDAR Digital Terrain Model (NRW, 2023) | 04, 05, 06, 07, 08, 12, 13 |
| KML boundary files | Site features (clearfell, hydro boundaries) | 04, 12, 13 |
| `broadleaf_restock.kml` | 1993/1996 broadleaf restocking block boundary; geometry also embedded in `Features.kml` | 12, 13 |
| `streams.kml` | SAGA-derived stream network (2×2 m cells, 9,847 cells) | 19, 20 |
| `site_boundary.kml` | Dissolved stream-cell polygons — study area mask for script 19 spatial interpolation | 19 |

---

## Script 00 — Climate and Well Network Summary
**Purpose:** Generates baseline climate figures and network summary statistics.

**Reads:**
- `outputs/01_climate.csv` ← from script 01
- `outputs/01_wells_clean.csv` ← from script 01

**Produces:**

| File | Type | Paper destination |
|---|---|---|
| `00_01_climate_timeseries.png` | Figure | Figure 3 (full record) |
| `00_02_well_network_summary.png` | Figure | Figure 4 |
| `00_01_climate_timeseries_short.png` | Figure | Figure 3 (well-record period) |
| `00_02_well_network_summary_short.png` | Figure | Figure 4 alternative |
| `00_01_annual_climate_summary.csv` | Table | Table 1 source data |
| `00_02_well_network_summary.csv` | Data | Section 4.1 statistics |

---

## Script 01 — Data Preparation
**Purpose:** Cleans raw dipwell and climate data, applies quality control,
splits into reference and extended networks, exports upstand lookup.

**Reads (raw data):**
- `data/Newborough_Cleaned_For_Model.csv`
- `data/Well__locations_height.csv`
- `data/RAF_Valley_Climate.csv`

**Produces (intermediate — outputs/ root):**

| File | Description | Used by |
|---|---|---|
| `01_climate.csv` | Monthly P and PET (Thornthwaite) | 00, 02, 03, 07, 08, 11 |
| `01_wells_clean.csv` | QC'd depth-to-water, all wells (negative convention) | 00, 02, 03, 05, 07, 08 |
| `01_wells_reference.csv` | Reference network (≥100 months, to Feb 2026) | 02, 08 |
| `01_wells_extended.csv` | Extended network (shorter/earlier records) | 06 |
| `01_locations.csv` | Well coordinates and elevations | 03, 04, 05, 06, 07, 08, 12, 13 |
| `01_well_elevations.csv` | Upstand heights and pipe-top elevations | 03 |

**Note:** Depth convention in `01_wells_clean.csv` is **negative = below pipe top**
(inverted from field recording convention). mAOD conversion formula:
`h = pipe_top_elevation + depth` (because depth is negative).

---

## Script 02 — Hierarchical Clustering
**Purpose:** Performs Ward's variance minimisation on z-scored depth-to-water
time series to identify k=6 hydrogeological clusters.

**Reads:**
- `outputs/01_climate.csv`
- `outputs/01_wells_clean.csv`
- `outputs/01_wells_reference.csv`

**Produces (intermediate):**

| File | Description | Used by |
|---|---|---|
| `02_cluster_stats.csv` | Cluster assignments for all reference wells | 03, 04, 05, 06, 07, 08, 09, 10 |

**Produces (figures — outputs/02_clustering/):**

| File | Type | Paper destination |
|---|---|---|
| `02_01_dendrogram.png` | Figure | Figure 5 (dendrogram) |
| `02_02_validation_plots.png` | Figure | Supplementary (elbow/silhouette) |
| `02_03_cluster_hydrographs_wb.png` | Figure | Figure 6 (cluster hydrographs) |

**Note:** Cluster hydrograph figure reads directly from `01_wells_clean.csv`
(depth-to-water, NOT mAOD). Do not change this dependency.

---

## Script 03 — State-Space Model
**Purpose:** Fits the SSM (Δh = β₁P − β₂PET − β₃h_prev) to each well and
to cluster average hydrographs. Exports LCSC values and mechanistic coefficients.

**Reads:**
- `outputs/01_locations.csv`
- `outputs/01_climate.csv`
- `outputs/01_wells_clean.csv`
- `outputs/01_well_elevations.csv` ← upstand correction for cluster averaging
- `outputs/02_cluster_stats.csv`

**Produces (intermediate):**

| File | Description | Used by |
|---|---|---|
| `03_master_data.csv` | Per-well LCSC, β coefficients, cluster | 07, 08 |
| `03_regional_averages.csv` | Monthly cluster average hydrographs (depth from ground) | 11 |
| `03_cluster_averages_maod.csv` | Monthly cluster mean heads in maOD | 21 |
| `03_cluster_summary_table.csv` | Table 1: cluster membership summary | Paper Table 1 |
| `03_cluster_mechanistic_coefficients.csv` | Table 2: β₁, β₂, −β₃, LCSC per cluster | Paper Table 2 |

**Produces (figures — outputs/03_state_space_model/):**

| File | Type | Paper destination |
|---|---|---|
| `03_01_mechanistic_signatures.png` | Figure | Figure 7 (mechanistic maps) |

**Important:** Cluster centroid construction applies upstand correction
(`corrected[col] = wells_clean[col] - upstand`) before averaging, so all
wells share a common ground-surface datum. Individual well SSM fits do NOT
apply this correction (pipe-top offset cancels in Δh).

---

## Script 04 — Cluster Visualisations
**Purpose:** Produces spatial map of cluster assignments overlaid on DEM.

**Reads:**
- `outputs/02_cluster_stats.csv`
- `outputs/01_locations.csv`
- DEM and KML files from data/

**Produces (figures — outputs/04_cluster_visualisations/):**

| File | Type | Paper destination |
|---|---|---|
| `04_01_core_architecture_map.png` | Figure | Figure 8 (cluster map) |

---

## Script 05 — Pearson Affinity (Reference Network)
**Purpose:** Validates cluster assignments for all 69 reference network wells
using Pearson correlation against cluster average hydrographs. Classifies
wells as Core (Δr > 0.05) or Fuzzy (Δr < 0.05). Flags Multi-Cluster
Affinity (MCA) wells.

**Reads:**
- `outputs/01_wells_clean.csv`
- `outputs/02_cluster_stats.csv`
- `outputs/01_locations.csv`

**Produces (intermediate):**

| File | Description | Used by |
|---|---|---|
| `05_pear_membership_audit.csv` | Per-well affinity audit (reference network) | 06 |

**Produces (figures — outputs/05_pearson_affinity/):**

| File | Type | Paper destination |
|---|---|---|
| `05_01_confidence_map.png` | Figure | Figure 9a (affinity confidence map) |

---

## Script 06 — Pearson Affinity (Extended Network)
**Purpose:** Classifies all 20 extended network wells against reference
cluster centroids. Produces integrated site-wide affinity map.

**Reads:**
- `outputs/01_wells_reference.csv`
- `outputs/01_wells_extended.csv`
- `outputs/02_cluster_stats.csv`
- `outputs/01_locations.csv`
- `outputs/05_pear_membership_audit.csv`

**Produces (intermediate):**

| File | Description | Used by |
|---|---|---|
| `06_pear_membership_audit_sitewide.csv` | Per-well affinity audit (all 89 wells) | Paper Section 4.2.3 |

**Produces (figures — outputs/06_pearson_extended/):**

| File | Type | Paper destination |
|---|---|---|
| `06_01_affinity_chart.png` | Figure | Figure 9b (affinity bar chart) |
| `06_02_integration_map.png` | Figure | Figure 9 (integrated spatial map) |

---

## Script 07 — Boundary Intercept Audit
**Purpose:** Compares Model A (intercept = 0) vs Model B (free intercept) for
all 69 reference wells. Maps spatial pattern of boundary subsidies and NSE
improvement. Identifies tidal, lacustrine and ridge-front boundary wells.

**Reads:**
- `outputs/01_wells_clean.csv`
- `outputs/01_climate.csv`
- `outputs/03_master_data.csv`
- `outputs/02_cluster_stats.csv`

**Produces (intermediate):**

| File | Description | Used by |
|---|---|---|
| `07_intercept_metrics.csv` | Per-well Model A vs B comparison | Paper Section 4.4.2 |
| `07_intercept_maps_merged_data.csv` | Spatial data for maps | Paper figures |
| `07_intercept_ceh14_showdown_data.csv` | CEH14 model comparison time series | Paper Figure |

**Produces (figures — outputs/07_boundary_intercept/):**

| File | Type | Paper destination |
|---|---|---|
| `07_intercept_01_ceh14_showdown.png` | Figure | Figure 10 (CEH14 comparison) |
| `07_intercept_02_plumbing_map.png` | Figure | Figure 11a (intercept map) |
| `07_intercept_03_nse_penalty_map.png` | Figure | Figure 11b (NSE effect map) |

---

## Script 08 — Model Benchmarking
**Purpose:** Compares SSM vs Traditional Linear Model (TLM) performance across
all 69 reference wells under one-step diagnostic and iterative 100-month
forecasting modes. Maps spatial pattern of improvement.

**Reads:**
- `outputs/01_wells_clean.csv`
- `outputs/01_wells_reference.csv`
- `outputs/01_climate.csv`
- `outputs/03_master_data.csv`
- `outputs/02_cluster_stats.csv`

**Produces (intermediate):**

| File | Description | Used by |
|---|---|---|
| `08_lcsc_model_stats.csv` | Per-well NSE, R², RMSE for TLM and SSM | Paper Table 3 |
| `08_lcsc_04_table3_benchmark_summary.csv` | Summary statistics table | Paper Table 3 |

**Produces (figures — outputs/08_model_benchmarking/):**

| File | Type | Paper destination |
|---|---|---|
| `08_lcsc_01_ceh19_showdown.png` | Figure | Figure 12 (CEH19 comparison) |
| `08_lcsc_02_r2_improvement_map.png` | Figure | Figure 13a (ΔR² map) |
| `08_lcsc_03_nse_improvement_map.png` | Figure | Figure 13b (ΔNSE map) |

---

## Script 09 — Dune Scraping Intervention Analysis
**Purpose:** Hierarchical Nested Control BACI analysis of dune scraping events
at CEH36 (Apr 2015), CEH18 and CEH21 (Oct 2023). Tier 1 validates controls
against regional mean; Tier 2 isolates pure scraping signal.

**Reads (raw — bypasses intermediate files):**
- `data/RAF_Valley_Climate.csv`
- `data/Newborough_Cleaned_For_Model.csv`

**Produces (outputs/09_scraping_intervention/):**

| File | Type | Paper destination |
|---|---|---|
| `09_scrape_01_full_parameters.csv` | Data | Diagnostic only (not used in paper) |
| `09_scrape_02_beta3_significance.csv` | Data | Paper Table 4 source |
| `09_scrape_03_baci_shifts.csv` | Data | Paper Section 4.5 |
| `09_scrape_04_net_benefits.csv` | Data | Paper Section 4.5 |
| `09_scrape_04b_table4_beta3_era_summary.csv` | Table | **Paper Table 4** |
| `09_tier1_final_cusum.csv` | Data | Paper Section 4.5 |
| `09_scrape_05_tier1_background_drift.png` | Figure | Figure 14 (Tier 1 CUSUM) |
| `09_scrape_06_tier2_scraping_signal.png` | Figure | Figure 15 (Tier 2 CUSUM) |
| `09_scrape_07_beta3_confidence.png` | Figure | Figure 16 (−β₃ CI plot) |

**Note:** Two different β₃ calculations exist in this script:
- `09_scrape_01_full_parameters.csv` — full SSM fit per era (unstable for short eras)
- `09_scrape_04b_table4_beta3_era_summary.csv` — **two-step isolation method** (use this for the paper):
  β₁ and β₂ fitted to full record; β₃ fitted to drainage residual per era separately.

---

## Script 10 — Clearfell BACI Experiment
**Purpose:** Three-zone hierarchical BACI experiment (core impact, edge zone,
regional control) assessing the December 2017 plantation clearfell. Includes
ANCOVA-BACI climate correction, CUSUM analysis, and SSM coefficient shifts.

**Reads (raw — bypasses intermediate files):**
- `data/RAF_Valley_Climate.csv`
- `data/Newborough_Cleaned_For_Model.csv`
- `outputs/03_master_data.csv`

**Produces (outputs/10_clearfell_baci/):**

| File | Type | Paper destination |
|---|---|---|
| `10_cfell_04_diagnostic_drainage_data.csv` | Data | Diagnostic/reproducibility |
| `10_cfell_05_baci_statistical_verification.csv` | Data | Paper Sections 4.6.1, 4.6.3 |
| `10_cfell_06_full_parameters.csv` | Data | Paper Section 4.6.4, Figure caption |
| `10_cfell_08_baci_timeseries_plotdata.csv` | Data | Paper Section 4.6.1 |
| `10_cfell_09_table5_beta3_before_after.csv` | Table | **Paper Table 5** |
| `10_cfell_09b_climate_corrected_cusum.csv` | Data | Paper Section 4.6.2 verification |
| `10_cfell_01_dual_control_baci.png` | Figure | Figure 17 (ANCOVA-BACI) |
| `10_cfell_01b_raw_baci.png` | Figure | Figure 18 (raw BACI) |
| `10_cfell_02_drainage_diagnostic_part1.png` | Figure | Supplementary / public repo |
| `10_cfell_02_drainage_diagnostic_part2.png` | Figure | Supplementary / public repo |
| `10_cfell_03_beta3_ols_slopes.png` | Figure | Figure 19 (−β₃ shifts) |

**Key verified numbers from this script:**
- Raw BACI scraping step: −0.207 m; felling step: −0.043 m; combined: −0.251 m
- ANCOVA Model 2: R²=0.600, scraping −0.119 m, clearfell −0.094 m, combined −0.214 m
- Climate sensitivity reduction post-felling: 79.3%
- Climate-corrected CUSUM at clearfell: +6.40 m; zero crossing June 2025; final −0.46 m

---

## Script 11 — Forecasting Thresholds
**Purpose:** Derives cluster-level Pflood equations by algebraic inversion of
SSM. Fits seasonal transfer functions for winter peak and summer minimum
prediction. All results in m/mm units (× 1000 relative to Table 2).

**Reads:**
- `outputs/03_regional_averages.csv`
- `outputs/01_climate.csv`

**Produces (outputs/11_forecasting_thresholds/):**

| File | Type | Paper destination |
|---|---|---|
| `11_forecast_01_results.txt` | Text | Reference/verification |
| `11_forecast_02_table6_winter_transfer.csv` | Table | **Paper Table 6** |
| `11_forecast_03_table7_summer_transfer.csv` | Table | **Paper Table 7** |
| `11_forecast_04_table8_critical_thresholds.csv` | Table | **Paper Table 8** |

**Key Pflood equations (correct values):**
- C1: (h_gap + 0.3660 × h_prev) / 0.0016
- C2: (h_gap + 0.2000 × h_prev) / 0.0017
- C3: (h_gap + 0.1179 × h_prev) / 0.0012
- C4: (h_gap + 0.0776 × h_prev) / 0.0010

**Note:** At typical Forest summer minima (−1.8 m), C4 Pflood ≈ 1,940 mm —
physically impossible under any realistic rainfall scenario.

---

## Script 12 — Site Overview Figure
**Purpose:** Produces publication-quality GIS site map with DEM, well network,
and site features.

**Reads:**
- `outputs/01_locations.csv`
- DEM and KML files from data/

**Produces (outputs/12_figure_site_overview/):**

| File | Type | Paper destination |
|---|---|---|
| `12_01_dem_site_overview.png` | Figure | **Figure 1** |

---

## Script 13 — Experimental Design Figure
**Purpose:** Produces GIS map showing hierarchical BACI experimental design,
well zones, and scraping/clearfell intervention footprints.

**Reads:**
- `outputs/01_locations.csv`
- `outputs/02_cluster_stats.csv`
- DEM and KML files from data/

**Produces (outputs/13_figure_experimental_design/):**

| File | Type | Paper destination |
|---|---|---|
| `13_01_experimental_setup_map.png` | Figure | **Figure 2** |

---

## Script 14 — Climate Projections
**Purpose:** Fits OLS trends to annual summer minima for C1, C2, C3 and
extrapolates to 2040. Plots observed winter maxima against flooding thresholds.
Identifies 2030–2039 critical intervention window.

**Reads:**
- `outputs/03_regional_averages.csv`

**Produces (outputs/14_climate_projections/):**

| File | Type | Paper destination |
|---|---|---|
| `14_climate_trajectory_summer.png` | Figure | Figure 20a |
| `14_climate_trajectory_winter_flooding.png` | Figure | Figure 20b |
| `14_climate_trajectory_stacked.png` | Figure | **Figure 20 (combined)** |
| `14_summer_trend_stats.csv` | Data | Paper Section 4.8.1 verification |
| `14_annual_extremes.csv` | Data | Paper Section 4.8 source data |
| `14_winter_exceedance.csv` | Data | Paper Section 4.8.2 source data |
| `14_seasonal_extremes_scatter.html` | Interactive figure | Seasonal Extremes tab in scenario viewer |

**Key verified numbers:**
- C1: −0.0100 m yr⁻¹ (R²=0.247, p=0.026, n=20)
- C2: −0.0115 m yr⁻¹ (R²=0.172, p=0.061, n=21)
- C3: −0.0149 m yr⁻¹ (R²=0.166, p=0.067, n=21)
- Winter flooding (wet slack): C1 14/21 yrs (67%), C2 11/21 (52%), C3 1/21 (5%)

---

## Scripts 19a and 19b — Hydrological Scenario Viewer

These two scripts are not part of the numbered 23-step pipeline. They are run
separately to build the self-contained HTML scenario viewer. Use option 4 in
the interactive menu, or `python run_analysis.py --viewer`.

**Script 19a — Scenario Runner**
Applies management and climate perturbations to the baseline IDW head surfaces
produced by script 19 and writes scenario-specific PNG outputs to
`outputs/19_spatial_groundwater/{scenario}/`.

**Reads:**
- `outputs/19_spatial_groundwater/baseline/` — baseline head surfaces from script 19
- `outputs/02_cluster_stats.csv` — cluster assignments

**Produces (outputs/19_spatial_groundwater/):**
- One subfolder per scenario: `forest_removal/`, `forest_thinning/`, `species_change/`, `climate_dry/`, `climate_wet/`
- `difference_maps/` — scenario vs baseline anomaly PNGs
- `difference_maps/scenario_summary.png` — all-scenario summary panel

**Script 19b — Viewer Builder**
Assembles all scenario images and the script 14 seasonal scatter into a single
self-contained HTML file. All images are embedded as base64; the file opens in
any browser with no server required.

**Reads:**
- `outputs/19_spatial_groundwater/{scenario}/` — all scenario PNGs from 19a
- `outputs/14_climate_projections/14_seasonal_extremes_scatter.html` — from script 14 (optional; tab shows placeholder if missing)

**Produces:**
- `outputs/19_spatial_groundwater/scenario_viewer.html`

**Viewer tabs:**
- **Scenario Figures** — maps under six scenarios with click-to-zoom
- **Difference Maps** — anomaly maps (blue = wetter, red = drier)
- **Seasonal Extremes** — interactive scatter plot of summer minimum vs winter maximum per well, with cluster colouring, threshold lines, and well search

---

## Script 21 — Forestry Scenarios and Management Intervention Figures
**Purpose:** Produces four publication figures for the forest management and
intervention analysis sections of the report.

**Reads:**
- `outputs/03_master_data.csv` ← SSM coefficients and cluster assignments
- `outputs/03_cluster_averages_maod.csv` ← cluster mean heads in maOD (from script 03)
- `outputs/INT_INTERCEPT_METRICS` ← boundary intercept metrics (from script 07)
- `outputs/01_climate.csv` ← climate record (from script 01)
- `data/Newborough_Cleaned_For_Model.csv` ← raw dipwell records (direct)
- `data/Well_locations_height.csv` ← well coordinates and pipe-top elevations (direct)

**Produces (outputs/21_forestry_scenarios/):**

| File | Type | Report destination |
|---|---|---|
| `21_forestry_01_hydrograph.png` | Figure | Figure 31 (synthetic hydrograph) |
| `21_forestry_02_distributions.png` | Figure | Supplementary (cluster summer minima violin) |
| `21_forestry_03_scraping_eras.png` | Figure | Figure 19 (scraping treatment wells) |
| `21_forestry_04_baci_zone_violin.png` | Figure | Figure 23 (BACI zone summer minima) |

**Run with `--preview` for 150 dpi quick check; default is publication DPI.**

**Scraping dates:**
- CEH36: scraped April 2015 and October 2023
- CEH18, CEH21: scraped October 2023 only
- CEH4: unmanaged control

**BACI zone definitions:**
- Core impact: FE2, FE4, WMC3
- Edge zone: FE1, FE3, CEH20, CEH30, CEH16, NW8B
- Forest interior: CEH2, CEH13, CEH32, CEH33, CEH34
- Regional control: CEH19, NW10, CEH31, LIS1

---

## Data Flow Diagram (simplified)

```
RAW DATA
├── Newborough_Cleaned_For_Model.csv ──→ 01 ──→ 09, 10 (direct)
├── Well__locations_height.csv ─────────→ 01
└── RAF_Valley_Climate.csv ─────────────→ 01 ──→ 09, 10 (direct)

SCRIPT 01 outputs
├── 01_climate.csv ─────────────────────→ 00, 02, 03, 07, 08, 11
├── 01_wells_clean.csv ─────────────────→ 00, 02, 03, 05, 07, 08
├── 01_wells_reference.csv ─────────────→ 02, 08
├── 01_wells_extended.csv ──────────────→ 06
├── 01_locations.csv ───────────────────→ 03, 04, 05, 06, 07, 08, 12, 13
└── 01_well_elevations.csv ─────────────→ 03

SCRIPT 02 outputs
└── 02_cluster_stats.csv ───────────────→ 03, 04, 05, 06, 07, 08, 13

SCRIPT 03 outputs
├── 03_master_data.csv ─────────────────→ 07, 08, 10, 21
├── 03_regional_averages.csv ───────────→ 11, 14
├── 03_cluster_averages_maod.csv ───────→ 21
├── 03_cluster_summary_table.csv ───────→ Paper Table 1
└── 03_cluster_mechanistic_coefficients → Paper Table 2

SCRIPT 05 output
└── 05_pear_membership_audit.csv ───────→ 06

SCRIPT 08 outputs
└── 08_lcsc_04_table3_benchmark_summary → Paper Table 3

SCRIPT 09 outputs
└── 09_scrape_04b_table4_beta3_era ─────→ Paper Table 4

SCRIPT 10 outputs
└── 10_cfell_09_table5_beta3_before ────→ Paper Table 5

SCRIPT 11 outputs
├── 11_forecast_02_table6_winter ───────→ Paper Table 6
├── 11_forecast_03_table7_summer ───────→ Paper Table 7
└── 11_forecast_04_table8_thresholds ───→ Paper Table 8

SCRIPT 11b outputs
└── 11b_01_summer_minima_depth.png ─────→ Paper Figure (Section 4.7)

SCRIPT 14 outputs
└── 14_climate_trajectory_stacked.png ──→ Paper Figure 20

SCRIPT 15 outputs (depth-dependent PET)
└── [diagnostic figures — not cited in main paper]

SCRIPT 17 → SCRIPT 16 → SCRIPT 18 → SCRIPT 19 → SCRIPT 20
├── 17_wtf_01_sy_table.csv ─────────────→ feeds 16, 18, 19
├── 16_wb_03_table.csv ─────────────────→ Paper Table (water balance)
├── 18_wtf_02_spatial_sy_map.png ───────→ Paper Figure (Sy distribution)
├── 19_head_mean_map.png ───────────────→ Paper Figure (Section 4.9)
├── 19_residual_comparison.png ─────────→ Paper Figure (validation)
├── 20_head_surface_streams.png ────────→ Paper Figure 1 (Section 4.9)
└── 20_residual_d8_comparison.png ──────→ Paper Figure 2 (Section 4.9)
```

---

## Streams KML

`data/streams.kml` is a filtered version of the SAGA-derived stream network:
- Source: SAGA stream extraction run on the site LiDAR DEM
- Filter applied: DEM elevation 1.0–18.0 m AOD, within E 240100–243900,
  N 362200–365800, DN=1 cells only
- Cells kept: 9,847 (from original ~11,634)
- Removed: ridge tops >18 m AOD, coastal/tidal cells <1 m AOD, out-of-bounds
- Format: SAGA MultiPolygon KML (2×2 m cells)
- geopandas/fiona CAN read this file (MultiPolygon geometries intact)
- Scripts 19 and 20 skeletonise this grid to produce connected stream polylines

## Site Boundary KML

`data/site_boundary.kml` defines the spatial interpolation domain for script 19:
- Source: dissolved SAGA stream-cell polygons (same source as streams.kml)
- Format: WGS84 MultiPolygon KML — 23,094 small polygons covering the dune system
- Used by: `make_site_mask()` in script 19 only
- Method: read via pure XML + pyproj + shapely (no fiona KML driver required);
  all polygon coordinates projected to OSGB36, dissolved via shapely unary_union,
  buffered 100 m to fill inter-cell gaps, exterior used as matplotlib Path mask
- Fallback: if file absent or shapely fails, rectangular sea-boundary mask applied
- Do NOT use as a substitute for streams.kml in scripts 19 or 20 — these are
  separate files with separate purposes

---

## DEM Corrections for Scraped Wells

Two wells were scraped after the LiDAR survey was flown. Scripts 11b, 19, and
20 apply DEM corrections and use only post-scraping data for these wells:

| Well  | Scraping date | DEM correction | Post-scrape start |
|-------|--------------|----------------|-------------------|
| CEH18 | October 2023 | −0.50 m        | 2023              |
| CEH21 | October 2023 | −0.70 m        | 2023              |

---

## Known Issues and Code Changes Made

### Script 01
- Added `01_well_elevations.csv` export (upstand heights and DEM ground elevations)
- Removed mAOD conversion block (was causing sign problems)
- Input file: `Well_locations_height.csv` (one underscore, not two)

### Script 02
- Cluster hydrograph figure now reads `01_wells_clean.csv` directly
- Removed dependency on `03_regional_averages.csv` (was showing mAOD values)

### Script 03
- Upstand correction applied before cluster averaging
- Exports corrected mechanistic coefficients table

### Script 10
- Added `10_cfell_09b_climate_corrected_cusum.csv` export
- Prints verification stats to console

### Script 11b
- CEH18 and CEH21 DEM corrections applied (see table above)
- Uses full well network (68 reference + 19 extended, 87 total)
- Ecological zones use Curreli et al. (2013) thresholds with BACI scraping
  recovery limits from Hollingham (2026): SD15b recovery = 0.75 m,
  SD16 recovery = 1.20 m

### Script 14
- Added p-value output to console
- Fixed C1 winter n (was hardcoded as 20, corrected to 21)
- Added three CSV exports for verification

### Scripts 18 and 19
- `--supplementary` flag added; only paper figures generated by default
- Script 19: lake boundary corrected to 7.456 m AOD (was 0.300/0.500 m)
- Script 19: all depth figures now use DEM_Ground_Elev − maOD convention
  (positive = below ground, consistent with 11b and Curreli thresholds)
- Script 19: Connell (2003) K reference corrected to Betson et al. (2002)
- Script 19: D8 stream network uses SAGA KML skeletonisation rather than
  pure D8 flow accumulation (cleaner lines on flat dune plain)

### Script 19 — spatial analysis updates (April 2026)
- **Well exclusions:** CEH3 (perched water table) and CEH17 (R² = 0.427,
  β₁ = 0.694 and β₃ = 0.049 both site minima) excluded from spatial
  interpolation via `SPATIAL_EXCLUDE` set in `build_well_table()`. Both wells
  remain in all SSM fitting and clustering analyses.
- **Depth columns in water balance CSV:** `mean_depth_bg`, `winter_depth_bg`,
  `summer_depth_bg`, and `dem_elev` now written to
  `19_water_balance_summary.csv` for use by scenario difference maps.
- **Depth recomputation in scenarios:** `_recompute()` now updates all three
  depth columns after any scenario head shift, so scenario CSVs carry correct
  depth values rather than baseline values.
- **Site boundary mask:** `make_site_mask()` now uses `data/site_boundary.kml`
  (dissolved stream-cell polygons) via pure XML + pyproj + shapely to produce
  a geographically accurate interpolation mask. Falls back to the rectangular
  sea-boundary mask if the file is absent or any dependency fails.

### Scripts 19a and 19b — scenario viewer (April 2026)
- Complete rewrite of both scripts.
- 19a generates per-field difference maps (Δ scenario vs baseline) for all
  six scenarios across ten water balance and head fields. Maps are auto-scaled
  from well-level p5–p95 Δ values; maps below a per-field threshold are omitted.
- 19b builds a four-tab HTML viewer: Forest Management, Climate Change,
  Baseline Maps, Seasonal Profiles. Produces both a standalone base64-embedded
  viewer and a lightweight linked viewer for GitHub Pages.
- Colour convention: red = drier/more than baseline; blue = wetter/less.
  RdBu colourmap for head and recharge (positive = wetter = blue);
  RdBu_r for depth, ET, and drainage (positive = drier = red);
  YlOrRd for seasonal storage change (magnitude only).

### Script 19 — map extent
- All figures now explicitly set xlim(240100, 243900), ylim(362200, 365800)
  via _base_map() — previously the DEM extent was used

### utils/map_utils.py
- `load_dem_hillshade()` added — greyscale LightSource hillshade for
  continuous-surface maps (scripts 11b, 19, 20)
- `add_idw_surface()` added — IDW interpolation with ridge masking,
  returns (mesh, gx, gy, surf_masked)
- `add_kml_features()` — guard added for empty GeoDataFrame; SAGA polygon
  KML fallback parser using ElementTree + scatter dots
- `add_kml_features()` — `include_streams` keyword argument added (default True);
  broadleaf restock block rendering added (description-based fallback for KML Name field)

### Paths and pipeline housekeeping (2026-04-10)
- All scripts now import exclusively from `utils/paths.py` — standalone try/except
  path discovery blocks removed from scripts 14, 15, 16, 17, 18
- `run_analysis.py` — `--from-step N` argument added for partial pipeline reruns
- Script 19 — dead code removed (`load_kml_features`, `add_kml_overlays`,
  `_ring_xy`, `_line_xy`); `features` parameter removed from all plot function signatures;
  script now uses `add_kml_features()` from map_utils via `_base_map()`
- Scripts 06, 07, 08, 12, 13 — inline KML rendering blocks replaced with
  `add_kml_features()` calls
- `Features.kml` — broadleaf restocking block polygon added as named Placemark
- `broadleaf_restock.kml` — source file added to data directory
- All 22 numbered scripts carry `__version__ = "1.0.0"` for traceability

---

## Paper Tables Quick Reference

| Table | Script | File |
|---|---|---|
| Table 1: Cluster summary | 03 | `03_cluster_summary_table.csv` |
| Table 2: Mechanistic coefficients | 03 | `03_cluster_mechanistic_coefficients.csv` |
| Table 3: Model benchmarking | 08 | `08_lcsc_04_table3_benchmark_summary.csv` |
| Table 4: Scraping −β₃ era summary | 09 | `09_scrape_04b_table4_beta3_era_summary.csv` |
| Table 5: Clearfell −β₃ before/after | 10 | `10_cfell_09_table5_beta3_before_after.csv` |
| Table 6: Winter transfer functions | 11 | `11_forecast_02_table6_winter_transfer.csv` |
| Table 7: Summer transfer functions | 11 | `11_forecast_03_table7_summer_transfer.csv` |
| Table 8: Pflood equations | 11 | `11_forecast_04_table8_critical_thresholds.csv` |

## Paper Figures Quick Reference

| Figure | Script | File |
|---|---|---|
| Figure 1: Site overview | 12 | `12_01_dem_site_overview.png` |
| Figure 2: Experimental design | 13 | `13_01_experimental_setup_map.png` |
| Figure 3: Climate timeseries | 00 | `00_01_climate_timeseries.png` |
| Figure 4: Well network | 00 | `00_02_well_network_summary.png` |
| Figure 5: Cluster validation | 02 | `02_02_validation_plots.png` |
| Figure 6: Dendrogram | 02 | `02_01_dendrogram.png` |
| Figure 7: Cluster hydrographs | 02 | `02_03_cluster_hydrographs_wb.png` |
| Figure 8: Water balance | 16 | `16_wb_02_bar_ms.png` |
| Figure 9: WTF Sy surface | 18 | `18_wtf_02_spatial_sy_map.png` |
| Figure 10: Pearson affinity | 05 | `05_pear_01_spatial_confidence_map.png` |
| Figure 11: Cluster map | 06 | `06_pear_02_integration_map.png` |
| Figure 12: CEH19 model fit | 08 | `08_lcsc_01_ceh19_with_model_b.png` |
| Figure 13: SSM gain over TLM | 08 | `08_lcsc_02_r2_improvement_map.png` |
| Figure 14: CEH14 model fit | 07 | `07_intercept_01_ceh14_showdown.png` |
| Figure 15: Boundary intercepts | 07 | `07_intercept_02_plumbing_map.png` |
| Figure 16: Tier 1 CUSUM | 09 | `09_scrape_05_tier1_background_drift.png` |
| Figure 17: Tier 2 scraping signal | 09 | `09_scrape_06_tier2_scraping_signal.png` |
| Figure 18: β₃ era coefficients | 09 | `09_scrape_07_beta3_confidence.png` |
| Figure 19: Scraping eras | 21 | `21_forestry_03_scraping_eras.png` |
| Figure 20: Dual-control BACI | 10 | `10_cfell_01_dual_control_baci.png` |
| Figure 21: ANCOVA-BACI | 10 | `10_cfell_02_drainage_diagnostic_part2.png` |
| Figure 22: OLS coefficients | 10 | `10_cfell_03_beta3_ols_slopes.png` |
| Figure 23: BACI zone violin | 21 | `21_forestry_04_baci_zone_violin.png` |
| Figure 24: Summer min depth map | 11b | `11b_01_summer_minima_depth.png` |
| Figure 25: Winter max depth map | 11b | `11b_02_winter_maximum_depth.png` |
| Figure 26: P_flood map | 11b | `11b_03_pflood_map.png` |
| Figure 27: Flood frequency | 11b | `11b_04_flood_frequency.png` |
| Figure 28: Climate trajectory | 14 | `14_climate_trajectory_stacked.png` |
| Figure 29: Head surface + streams | 20 | `20_head_surface_streams.png` |
| Figure 30: SSM residual | 20 | `20_residual_ssm.png` |
| Figure 31: Synthetic hydrograph | 21 | `21_forestry_01_hydrograph.png` |
