# Newborough Warren Groundwater Analysis Pipeline
## Script Input/Output Reference

This document describes the data flow between all pipeline scripts, identifying
which files each script reads, which it produces, and which outputs feed into
the paper as figures, tables or into downstream scripts.

Run order: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 10b → 10c → 11 → 11b → 00 → 14 → 12 → 13 → 15 → 17 → 16 → 18 → 19 → 20 → 21 → 22 → 23 → 24

Script 19 is step 23 of the 29-step pipeline. As a byproduct of running its
main spatial analysis it also builds the self-contained HTML scenario viewer.
Menu option 4 (`python run_analysis.py --viewer`) rebuilds the viewer alone
by re-running script 19 without stepping through the earlier scripts.

Critical ordering constraints:
- Script 17 (WTF Sy) must run before script 16 (water balance)
- Script 18 (WTF spatial) must run before script 19 (spatial groundwater)
- Script 11b requires outputs from scripts 11 and 06
- Script 21 requires `03_cluster_averages_maod.csv` from script 03
- Rebuilding the scenario viewer via option 4 requires that all earlier
  pipeline outputs already exist; in particular script 14 should have run
  for the seasonal extremes tab to be populated

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
  07_spatial_coefficients/
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
  config.py                    ← cluster colours, labels, DRAINAGE_DATUM, HEADLINE_LAG, FOREST_INTERCEPTION
  data_utils.py                ← cleaning, normalisation functions
  map_utils.py                 ← DEM, KML, basemap helpers
  model_utils.py               ← SSM fitting helpers (displacement formulation)
  paths.py                     ← all path constants
```

---

## Raw Data Inputs (data/ directory)

| File | Description | Used by |
|---|---|---|
| `Newborough_Cleaned_For_Model.csv` | Raw dipwell records | 01, 09, 10 |
| `Well_locations_height.csv` | Well coordinates and pipe-top elevations | 01 |
| `RAF_Valley_Climate.csv` | Monthly rainfall and temperature | 01, 09, 10 |
| DEM `.tif` files | LiDAR Digital Terrain Model (NRW, 2023) | 03, 04, 05, 06, 07, 08, 11b, 12, 13, 19, 20 |
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
- `data/RAF_Valley_Climate.csv` ← raw climate record (used by Figure 3 only)

**Profiles:**
Script 00 accepts `--profile {full,short,both}`. `run_analysis.py` invokes
it with `--profile full`, producing the full 95-year record outputs. Running
with `--profile short` restricts everything to the well-record overlap
window (Apr 2005 – Feb 2026) and produces `_short`-suffixed variants of
Figures 1 and 2. Figure 3 (warming trend) requires the full 95-year record
and is produced under `--profile full` only.

**Produces (full profile):**

| File | Type | Paper destination |
|---|---|---|
| `00_01_climate_timeseries.png` | Figure | Figure 3 (full record) |
| `00_02_well_network_summary.png` | Figure | Figure 5 |
| `00_03_summer_warming_trend.png` | Figure | RAF Valley JJA max-temp anomaly, 1931–2025 |
| `00_01_annual_climate_summary.csv` | Table | Table 1 source data |
| `00_02_well_network_summary.csv` | Data | Section 4.1 statistics |
| `00_03_summer_warming_stats.csv` | Data | Per-year summer means + linear regression stats (slope, R², p, pre/post-2013 split) |

**Produces (short profile, additional):**

| File | Type | Paper destination |
|---|---|---|
| `00_01_climate_timeseries_short.png` | Figure | Figure 3 (well-record period) |
| `00_02_well_network_summary_short.png` | Figure | Figure 5 alternative |
| `00_01_annual_climate_summary_short.csv` | Data | Monitoring-period climate summary |
| `00_02_well_network_summary_short.csv` | Data | Monitoring-period network stats |

---

## Script 01 — Data Preparation
**Purpose:** Cleans raw dipwell and climate data, applies quality control,
splits into reference and extended networks, exports upstand lookup.

**Reads (raw data):**
- `data/Newborough_Cleaned_For_Model.csv`
- `data/Well_locations_height.csv`
- `data/RAF_Valley_Climate.csv`

**Produces (intermediate — outputs/ root):**

| File | Description | Used by |
|---|---|---|
| `01_climate.csv` | Monthly P and PET (Thornthwaite) | 00, 02, 03, 08, 11 |
| `01_wells_clean.csv` | QC'd depth-to-water, all wells (negative convention) | 00, 02, 03, 05, 08 |
| `01_wells_reference.csv` | Reference network (66 wells; ≥100 months, to Feb 2026) | 02, 08 |
| `01_wells_extended.csv` | Extended network (shorter/earlier records) | 06 |
| `01_locations.csv` | Well coordinates and elevations | 03, 04, 05, 06, 07, 08, 12, 13 |
| `01_well_elevations.csv` | Upstand heights and pipe-top elevations | 03, 07 |
| `01_wells_clean_maod.csv` | QC'd heads in mAOD, all wells with elevation data | 03, 21 |

**Reference-network exclusions:** The 66-well reference network is defined
by a hard-coded whitelist (`REFERENCE_NETWORK_WHITELIST`). The following
wells are excluded with documented physical rationale:
- **FE1–4, LIS1** (5 wells) — post-December 2017 clearfell non-stationarity
- **Llyn Rhos** (1 well) — reads a lake surface, not a water table
- **CEH3, CEH22** (2 wells) — tidal-signal contamination; Ward's clustering
  consistently identifies both as singleton outliers at every k from 4 to 9

FE1–4, LIS1, CEH3 and CEH22 remain in the extended network for per-well
analyses. Llyn Rhos is excluded from both networks via the
EXTENDED_NETWORK_BLACKLIST — its lake-stage signal is not interpretable
as groundwater behaviour.

**Note:** Depth convention in `01_wells_clean.csv` is **negative = below pipe top**
(inverted from field recording convention). mAOD conversion formula:
`h = pipe_top_elevation + depth` (because depth is negative).
---

## Script 02 — Hierarchical Clustering
**Purpose:** Performs Ward's variance minimisation on correlation-based
distance (d = 1 − r) to identify k=5 hydrogeological clusters from the
66-well reference network. Includes bootstrap stability diagnostics and
seasonal amplitude descriptors.

**Reads:**
- `outputs/01_climate.csv`
- `outputs/01_wells_clean.csv`
- `outputs/01_wells_reference.csv`
- `data/RAF_Valley_Climate.csv` ← drought-summer identification for amplitude normalisation

**Produces (intermediate — outputs/ root):**

| File | Description | Used by |
|---|---|---|
| `02_cluster_stats.csv` | Cluster assignments for all 66 reference wells | 03, 04, 05, 06, 07, 08, 09, 10 |

**Produces (diagnostics and figures — outputs/02_clustering/):**

| File | Type | Description |
|---|---|---|
| `02_01_dendrogram.png` | Figure | Ward's dendrogram (Paper Figure 7) |
| `02_02_validation_plots.png` | Figure | Elbow + silhouette validation |
| `02_02b_validation_k_sweep.png` | Figure | Extended k-sweep: silhouette, Calinski–Harabasz, merge distance |
| `02_03_cluster_hydrographs_wb.png` | Figure | Cluster hydrographs + water balance (Paper Figure 8) |
| `02_04_bootstrap_stability_summary.csv` | Data | Per-cluster stability medians across k=4..7 |
| `02_05_bootstrap_stability_per_well.csv` | Data | Per-well stability scores (long form, all candidate k) |
| `02_06_coassignment_heatmap_k{k}.png` | Figure | Bootstrap co-assignment heatmap per candidate k |
| `02_07_cluster_membership_k{k}.csv` | Data | Cluster memberships at each candidate k |
| `02_08_cluster_amplitude_per_well.csv` | Data | Per-well amplitude descriptors (p90−p10, std, summer min; raw + climate-normalised) |
| `02_09_cluster_amplitude_summary.csv` | Data | Per-cluster amplitude summary (medians, damping %, within-cluster spread) |
| `02_10_cluster_amplitude_boxplot.png` | Figure | Post-2018 seasonal amplitude by cluster (box + strip) |

**Cluster partition (k=5):**

| ID | Name | n | Anchors | Colour |
|---|---|---|---|---|
| C1 | Lake Edge | 7 | ceh5, ceh11 | `#1a6faf` blue |
| C2 | Dune | 26 | d10 | `#2ca02c` green |
| C3 | Western Residual | 19 | nw1 | `#d62728` red |
| C4 | Main Forest | 9 | ceh2 | `#7f77dd` purple |
| C5 | Coastal Forest | 5 | ceh16, nw9 | `#8B4513` brown |

Cluster IDs are deterministically assigned via anchor-well identity so
that integer IDs are stable across re-runs regardless of fcluster's
arbitrary ordering. The anchor mapping is defined in `CLUSTER_ID_ANCHORS`
in `02_clustering.py`; the script raises `ValueError` if any anchor well
lands in a different Ward's cluster than expected.

**Bootstrap stability:** 1000 resamples at each candidate k in {4, 5, 6, 7}.
At k=5, four clusters have median per-well stability ≥ 0.93 (Main Forest
1.00, Coastal Forest 0.99, Lake 0.98, Dune 0.93). Western Residual has
moderate stability (~0.50) reflecting landscape heterogeneity.

**Amplitude descriptors:** Per-well and per-cluster seasonal amplitude
(p90 − p10) over three windows (full record, pre-2018, post-2018), with
a climate-normalised variant that removes drought summers (2005, 2018,
2022) identified from RAF Valley Jun–Sep rainfall. See §3.2.4 in the
report methods.

**Note:** Cluster hydrograph figure reads directly from `01_wells_clean.csv`
(depth-to-water, NOT mAOD). Do not change this dependency.

---

## Script 03 — State-Space Model
**Purpose:** Fits the SSM (displacement formulation) to each well and
to cluster-centroid hydrographs. Exports LCSC values, mechanistic coefficients,
and a full suite of validation diagnostics (lag sweep, bootstrap CIs,
leave-one-out, C1 split-window, datum sensitivity).

**Model (displacement formulation):**

    Δh(t) = β₁·P(t−k) + β₂·(−PET(t)) + β₃·(−h_disp_prev(t))

where `h_disp = DRAINAGE_DATUM + h_depth` (displacement above a reference
drainage base; `DRAINAGE_DATUM = 3.7 m` below ground surface, from
`config.py`); `k = HEADLINE_LAG` (from `config.py`; currently 0 after the
Script 01 bucketing fix — originally 1 to compensate for a month-assignment
convention; after fixing the bucketing, lag-0 gives identical coefficients).
The displacement formulation was adopted after a sensitivity
analysis found that the depth-below-surface formulation produces negative β₃
for three of five clusters. No-intercept OLS throughout.

**Physical sign conventions:**
- `β₁ > 0` — rainfall raises the water table (hard assertion; pipeline halts)
- `β₂ > 0` — PET draws the water table down (hard assertion; pipeline halts)
- `β₃ > 0` — drainage increases with head above datum (soft assertion; warned but not halted)

**Key configuration constants:**
- `HEADLINE_LAG` — rainfall lag from `config.py` (currently 0 after bucketing fix)
- `LCSC_DATA_LIMIT = 100` — most-recent 100 months for per-well fits
- `MIN_OBS_PER_WELL = 30` — minimum observations for a per-well SSM fit
- `N_BOOTSTRAP = 1000`, `BOOTSTRAP_SEED = 20260424`
- `UPSTAND_AUDIT_THRESHOLD = 0.30 m`
- `C1_SPLIT_DATE = 2018-01-01`
- `DRAINAGE_DATUM = 3.7 m` (from `config.DRAINAGE_DATUM`)

**Reads:**
- `outputs/01_locations.csv`
- `outputs/01_climate.csv`
- `outputs/01_wells_clean.csv`
- `outputs/01_wells_clean_maod.csv` ← for maOD cluster-centroid export
- `outputs/01_well_elevations.csv` ← upstand correction for cluster averaging
- `outputs/02_cluster_stats.csv`
- `outputs/02_clustering/02_08_cluster_amplitude_per_well.csv` ← optional; amplitude heterogeneity flags (falls back to hard-coded values if absent)
- `data/newborough_dem.tif`, `data/Features.kml`, etc. ← spatial datum maps (optional; degrades gracefully if absent)

**Produces (intermediate — outputs/ root):**

| File | Description | Used by |
|---|---|---|
| `03_master_data.csv` | Per-well LCSC, β coefficients, cluster | 07, 08, 10, 16, 17, 18, 19 |
| `03_regional_averages.csv` | Monthly cluster average hydrographs (depth from ground) + climate | 11, 14, 16 |
| `03_cluster_averages_maod.csv` | Monthly cluster mean heads in maOD + climate | 21 |
| `03_cluster_peak_months.csv` | Long-term mean peak month per cluster (calendar month 1–12 of highest mean water table) | 11, 11b |

**β column-name convention (two separate files):**

| File | β columns | Units |
|---|---|---|
| `03_master_data.csv` (per-well) | `beta_1_recharge`, `beta_2_atmospheric_draw`, `beta_3_drainage` | m/m (rainfall & PET in m/month) |
| `03_cluster_mechanistic_coefficients.csv` (per-cluster) | `beta_1`, `beta_2`, `beta_3` | m/m (same) |

Downstream consumers must use the correct column names for each file.
Scripts 11b and 16 apply a `/1000` conversion (m/m → m/mm) when they work
with millimetre-denominated climatology.

**Produces (figures and diagnostics — outputs/03_state_space_model/):**

| File | Type | Paper destination |
|---|---|---|
| `03_01_mechanistic_signatures.png` | Figure | Diagnostic (β values presented in paper Table 2) |
| `03_02_cluster_summary_table.csv` | Table | **Paper Table 1** — cluster membership summary with bootstrap CIs and amplitude heterogeneity flag |
| `03_03_cluster_mechanistic_coefficients.csv` | Table | **Paper Table 2** — centroid β₁, β₂, β₃, LCSC, R², p-values, drainage datum |
| `03_04_lag_diagnostic.csv` | Data | Centroid SSM fits at lags 0, 1, 2, 3 months per cluster |
| `03_05_bootstrap_ci.csv` | Data | B=1000 bootstrap CIs per cluster (well-level resampling) |
| `03_06_leave_one_out.csv` | Data | Per-cluster leave-one-well-out centroid fits |
| `03_07_c1_split_window.csv` | Data | C1 Lake Edge pre/post-2018 split-window diagnostic with bootstrap CIs |
| `03_08_datum_sensitivity.csv` | Data | β₃ and R² at reference depths 0.5–8.0 m (0.1 m steps), all five clusters |
| `03_08_datum_sensitivity.png` | Figure | 3-panel: β₃ vs datum, R² vs datum, aggregate fit quality + AIC |
| `03_09_well_datum_sensitivity.csv` | Data | Full per-well datum sweep (66 wells × 76 depths) |
| `03_09_well_optimal_datums.csv` | Data | Per-well optimal datums: primary (β₃>0 & sig), secondary (β₃>0), R²-max; plus fit at uniform datum and R² gain |
| `03_09_well_optimal_datums.png` | Figure | 4-panel: histograms and boxplots of primary and R²-max datums by cluster |
| `03_10_well_datum_r2max_map.png` | Figure | **Section 3.4** — spatial map of R²-maximising drainage datum per well (DEM + KML overlay) |
| `03_10_well_r2_gain_map.png` | Figure | **Section 3.4** — spatial map of R² gain from per-well optimal vs uniform 3.7 m datum |

**Validation diagnostics:**
- **Lag diagnostic (03_04):** Confirms every cluster prefers lag-1 over lag-0
  (R² ~0.6–0.7 vs ~0.3–0.5; β₁ large/significant/positive at lag-1). Physical
  basis: monthly dipwell readings taken in the first week of month t reflect
  recharge from the previous month's rainfall.
- **Bootstrap CIs (03_05):** Well-level resampling within each cluster
  (B=1000, fixed seed). Reports median and 2.5%/97.5% percentile CIs for
  β₁, β₂, β₃, R², LCSC. Also reports fraction of bootstrap replicates
  with β₁ > 0.
- **Leave-one-out (03_06):** Per-cluster centroid refit with each member
  excluded in turn (clusters with ≥4 members). Detects single-well domination.
- **C1 split-window (03_07):** Fits C1 Lake Edge centroid SSM separately on
  pre-2018 and post-2018 windows, with well-resampling bootstrap on each
  side. Tests whether the Lake cluster has undergone a regime shift.
- **Datum sensitivity (03_08):** Sweeps reference drainage datum from 0.5 to
  8.0 m in 0.1 m steps. Selection criterion: minimum depth at which β₃ is
  positive AND significant (p < 0.05) for all five clusters simultaneously.
  If the empirical minimum differs from `DRAINAGE_DATUM` by >0.15 m, a
  warning is printed.
- **Per-well datum sensitivity (03_09):** Same sweep applied to each of the
  66 reference wells individually (upstand-corrected). Records three datum
  measures per well: primary (minimum depth where β₃ > 0 & p < 0.05),
  secondary (minimum depth where β₃ > 0), and R²-maximising (depth that
  produces the best-fitting model regardless of β₃ sign). Also records
  the fit at the uniform datum and R² gain from per-well optimisation.
  Shows a spatial gradient in effective drainage base depth (0.5 m near
  the lake → 3+ m under the forest).
- **Spatial datum maps (03_10):** Two publication-quality maps using
  `plot_metric_map` from `map_utils` with DEM background and KML overlays.
  The R²-max datum map shows the east-to-west gradient in effective drainage
  base. The R² gain map shows the cost of the uniform datum is negligible
  except for C1 Lake Edge (+0.048). Skipped gracefully if DEM/KML files
  or mapping dependencies are unavailable. Report destination: Section 3.4.

**Upstand correction:** Cluster centroid construction applies upstand
correction (`corrected[col] = wells_clean[col] - upstand`) before averaging,
so all wells share a common ground-surface datum. Individual per-well SSM
fits also apply upstand correction (pipe-top depth → ground-surface depth)
so that the `DRAINAGE_DATUM` displacement is relative to the ground surface
for every well. An upstand audit prints any reference-network wells
exceeding `UPSTAND_AUDIT_THRESHOLD` (0.30 m); CEH2 (~71 cm) is deliberately
tall-for-visibility in the forest understorey.

**Amplitude heterogeneity:** Per-cluster amplitude range is loaded from
Script 02's `02_08_cluster_amplitude_per_well.csv` (joined on normalised
well name via the authoritative Option-A cluster assignments, not the
amplitude file's own cluster column). Falls back to hard-coded values
from `SCRIPT_03_BRIEF.md` if the file is absent. A cluster is flagged as
heterogeneous if the ratio of max to min post-2018 amplitude exceeds 1.5.

**Block map:** Under the current Option-A partition, each cluster maps to
its own block (C1 → Lake Edge, C2 → Eastern Block, C3 → Western Block,
C4 → Forest, C5 → Coastal Forest). These are reported separately per
Martin's call, not merged.

**Peak-month derivation:** `export_cluster_peak_months()` computes the
calendar month with the highest long-term mean cluster-centroid head for
each cluster (depth-below-pipe convention; argmax = least-negative =
highest water table). The output CSV (`03_cluster_peak_months.csv`) is the
single source of truth for Script 11's forecasting horizon and Script 11b's
P_flood iterated-SSM closed form.

**LCSC print ordering:** the final manuscript LCSC block prints clusters
sorted by integer cluster ID (`C1, C2, ..., C5`) with a `C{n}` prefix,
not alphabetical by block label.

**Hard halt behaviour:** If any centroid fit violates β₁ > 0 or β₂ > 0,
the pipeline prints warnings immediately but defers the hard halt until
after all diagnostic tables (03_04–03_10) and the signatures figure are
saved, so the investigator has the diagnostic outputs to work with.

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
| `04_01_core_architecture_map.png` | Figure | Diagnostic (not in paper) |

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
| `05_01_confidence_map.png` | Figure | Figure 12a (affinity confidence map) |

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
| `06_01_affinity_chart.png` | Figure | Figure 11 (affinity bar chart) |
| `06_02_integration_map.png` | Figure | Figure 12b (integrated spatial map) |

---

## Script 07 — Spatial Coefficient Mapping
**Purpose:** Maps the per-well SSM coefficients (β₁ recharge sensitivity,
β₂ atmospheric draw, β₃ drainage rate) from `03_master_data.csv` across the
site as IDW-interpolated surfaces over a DEM hillshade. Shows how the three
mechanistic processes vary spatially.

This script replaces the former `07_boundary_intercept.py`. The old intercept
audit (Model A vs Model B with/without a fitted constant) was superseded by
the displacement formulation: with the SSM fitting well across all clusters
(Script 08 median iterative NSE = 0.77), direct coefficient mapping reveals
the spatial structure more clearly than the intercept residual did.

**Units:**
- β₁: mm / mm rainfall (dimensionless — water-table rise per unit rainfall)
- β₂: mm / mm PET (dimensionless — water-table decline per unit PET)
- β₃: month⁻¹ (fractional drainage per timestep)

**Reads:**
- `outputs/03_master_data.csv` ← per-well SSM coefficients, cluster, coordinates
- `outputs/01_well_elevations.csv` ← DEM ground elevations (for ridge masking)

**Produces (intermediate):**

| File | Description | Used by |
|---|---|---|
| `07_coefficient_summary.csv` | Cluster-level β statistics (mean, std, range) | Paper Section 4.4 |
| `07_coeff_maps_data.csv` | Per-well spatial data for maps | Paper figures |

**Produces (figures — outputs/07_spatial_coefficients/):**

| File | Type | Paper destination |
|---|---|---|
| `07_coeff_01_beta1_recharge.png` | Figure | β₁ recharge sensitivity surface |
| `07_coeff_02_beta2_atm_draw.png` | Figure | β₂ atmospheric draw surface |
| `07_coeff_03_beta3_drainage.png` | Figure | β₃ drainage rate surface (log scale) |
| `07_coeff_04_r2_quality.png` | Figure | Per-well R² model quality surface |

---

## Script 08 — Model Benchmarking
**Purpose:** Compares SSM vs Traditional Linear Model (TLM) performance across
all 66 reference wells (minus CEH7, CEH8, CEH37) under one-step diagnostic and
iterative 100-month forecasting modes. Per-well OLS is fitted independently for
each well using the displacement formulation (`h_disp = DRAINAGE_DATUM + h_depth`)
and lag-1 rainfall, matching Script 03. Maps spatial pattern of improvement.

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
| `08_lcsc_01_ceh6_showdown.png` | Figure | Figure 13 (CEH6 TLM vs SSM showdown) |
| `08_lcsc_02_r2_improvement_map.png` | Figure | Figure 14a (ΔR² map) |
| `08_lcsc_03_nse_improvement_map.png` | Figure | Figure 14b (ΔNSE map) |

---

## Script 09 — Dune Scraping Intervention Analysis
**Purpose:** Hierarchical Nested Control BACI analysis of dune scraping events
at CEH36 (Apr 2015), CEH18 and CEH21 (Oct 2023). Tier 1 validates controls
against regional mean; Tier 2 isolates pure scraping signal. Includes a
three-method robustness analysis for CEH36 (raw BACI, synthetic control,
SSM forward residual).

**Reads:**
- `outputs/01_climate.csv` ← pipeline PET and rainfall (primary climate source)
- `data/Newborough_Cleaned_For_Model.csv` ← raw well records (bypasses pipeline intermediate)

**Era definitions:**

| Well | Role | Era 1 | Era 2 | Era 3 |
|---|---|---|---|---|
| CEH36 | Central Impact | Baseline (< Apr 2015) | Pure Scraping (Apr 2015 – Dec 2018) | Felling Pulse (≥ Dec 2018) |
| CEH4 | Central Control | Baseline (< Apr 2015) | Pure Scraping (Apr 2015 – Dec 2018) | Felling Pulse (≥ Dec 2018) |
| CEH18 | Boundary Impact | Baseline (< Dec 2018) | Felling Pulse (Dec 2018 – Oct 2023) | After Scraping (≥ Oct 2023) |
| CEH21 | Coastal Impact | Baseline (< Dec 2018) | Coastal Drawdown (Dec 2018 – Oct 2023) | After Scraping (≥ Oct 2023) |
| CEH22 | Coastal Control | Baseline (< Dec 2018) | Coastal Drawdown (Dec 2018 – Oct 2023) | After Scraping (≥ Oct 2023) |

**Hierarchical pairings:** CEH36 → CEH4, CEH18 → CEH4, CEH21 → CEH22,
CEH4 → Regional Mean, CEH22 → Regional Mean. Regional Mean is the average
of 6 control wells (CEH9, NW8, NW8B, NW5, NW6, NW7).

**SSM specification:** Uses lag-1 rainfall (`P_m_lag1`), consistent with
`HEADLINE_LAG = 1` in Script 03. No-intercept OLS with the same three-term
design matrix (β₁·P, β₂·(−PET), β₃·(−h_prev)).

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/09_scraping_intervention/):**

| File | Type | Paper destination |
|---|---|---|
| `09_scrape_01_full_parameters.csv` | Data | Diagnostic only (per-era full SSM fits) |
| `09_scrape_02_beta3_significance.csv` | Data | Paper Table 4 source (two-step isolation β₃) |
| `09_scrape_03_baci_shifts.csv` | Data | Paper Section 4.5 (era-to-era BACI mean shifts) |
| `09_scrape_04_net_benefits.csv` | Data | Paper Section 4.5 (net benefit vs CEH21 benchmark) |
| `09_scrape_04b_table4_beta3_era_summary.csv` | Table | **Paper Table 4** (manuscript-ready β₃ era summary) |
| `09_tier1_final_cusum.csv` | Data | Final CUSUM values for Tier 1 control wells |
| `09_scrape_05_tier1_background_drift.png` | Figure | Figure 15 (Tier 1 CUSUM: CEH4 & CEH22 vs regional mean) |
| `09_scrape_06_tier2_scraping_signal.png` | Figure | Figure 16 (Tier 2 CUSUM: CEH36, CEH18, CEH21 vs paired controls) |
| `09_scrape_07_beta3_confidence.png` | Figure | Figure 18 (−β₃ CI plot: impact wells by era) |
| `09_scrape_08_ceh36_robustness.png` | Figure | CEH36 robustness — 3-panel: raw BACI vs synthetic control gap series, SSM forward residual, step-change bar chart |

**CEH36 robustness analysis (3 independent methods):**
1. **Raw BACI:** CEH36 minus CEH4 (existing paired approach)
2. **Synthetic control:** CEH36 minus a weighted OLS composite of 11 donor
   wells (CEH1, CEH2, CEH5, CEH6, CEH9, CEH16, CEH17, CEH19, CEH22, CEH23,
   CEH28), fitted on the pre-2015 baseline period without intercept
3. **SSM forward residual:** SSM calibrated on pre-2015 baseline at CEH36,
   run forward through scraping/felling/post-2023 eras; observed − predicted
   residual measures deviation from the climate-driven trajectory

Method convergence supports the inference that the Pure Scraping era benefit
is not an artefact of CEH4's own progressive deepening. Method divergence
is interpretable: raw BACI and synthetic control measure relative topographic
benefit; the SSM residual measures whether the benefit is structural
(permanent ground surface lowering) or hydrodynamic (sustained departure
from climate forecast).

**Note:** Two different β₃ calculations exist in this script:
- `09_scrape_01_full_parameters.csv` — full SSM fit per era (unstable for short eras)
- `09_scrape_04b_table4_beta3_era_summary.csv` — **two-step isolation method** (use this for the paper):
  β₁ and β₂ fitted to full record; β₃ fitted to drainage residual per era separately.

**Note:** `RAF_VALLEY_LAT_DEG` is set to 53.25° in this script for the
Thornthwaite PET day-length correction. The confirmed latitude for RAF
Valley climate station is 53.15°N (per Martin); the in-script value is
superseded — the primary PET computation uses `outputs/01_climate.csv`
from Script 01, which uses the correct latitude.

---

## Script 10 — Clearfell BACI Experiment
**Purpose:** Three-zone hierarchical BACI experiment (core impact, edge zone,
regional control) assessing the December 2017 plantation clearfell. Includes
ANCOVA-BACI climate correction with cumulative water balance covariate,
raw and climate-corrected CUSUM analysis, SSM coefficient shifts (β₁, β₂, β₃),
spatial transect analysis, and NW10 broadleaf trend analysis.

**Reads:**
- `data/RAF_Valley_Climate.csv` ← raw climate (Thornthwaite PET computed in-script)
- `outputs/01_wells_clean.csv` ← main network (including CEH9, NW7, NW6)
- `outputs/01_wells_extended.csv` ← FE series and edge wells (FE1–4, LIS1, NW8B; merged at load time)
- `outputs/03_master_data.csv` ← per-well SSM coefficients (canonical LCSC03 output)

**Well loading:** Script 10 merges `01_wells_clean.csv` (main network) with
`01_wells_extended.csv` (extended wells). Main takes priority for any
overlapping column names. Falls back to raw `Newborough_Cleaned_For_Model.csv`
if pipeline outputs are absent.

**Experiment configuration:**
- **Intervention date:** December 2017 (`2017-12-01`)
- **Scraping 1:** April 2015 (`2015-04-01`)
- **Scraping 2:** October 2023 (`2023-10-01`) — tested and found non-significant
  (p = 0.258, ΔAIC = +0.66); not retained in final ANCOVA model
- **Impact wells (3):** FE2, FE4, WMC3
- **Edge wells (8):** FE1, FE3, CEH31, LIS1, CEH20, CEH30, CEH16, NW8B
- **Control wells (8):** CEH32, CEH34, CEH33, NW10, CEH19, CEH9, NW7, NW6

**Three-era BACI:** Pre-scraping (< Apr 2015), post-scraping pre-felling
(Apr 2015 – Dec 2017), post-felling (≥ Dec 2017). The post-felling era is
further split at Oct 2023 into pure clearfell (Dec 2017 – Sep 2023) and
post-Oct-2023-scraping sub-eras.

**ANCOVA-BACI (Model 2):** Climate correction via cumulative water balance
covariate. The water balance baseline (`WB_BASELINE_MM`) is computed
dynamically from the well-record period (first well date to end of climate
record) as the mean monthly (P − PET) in mm/month, ensuring the baseline
is tied to the study period rather than hardcoded. The model includes:
`impact = intercept + b_cwb·cum_wb + b_scraping·Scraped + b_post·Post + b_interaction·(cwb×Post)`.
Climate-corrected BACI removes the cwb and interaction effects; the
corrected CUSUM is computed relative to the post-scraping baseline.

**SSM specification:** Uses lag-1 rainfall (`P_m_lag1`), consistent with
`HEADLINE_LAG = 1` in Script 03. No-intercept OLS.

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/10_clearfell_baci/):**

| File | Type | Paper destination |
|---|---|---|
| `10_cfell_04_diagnostic_drainage_data.csv` | Data | Diagnostic/reproducibility — per-well drainage component |
| `10_cfell_05_baci_statistical_verification.csv` | Data | Paper Sections 4.6.2, 4.6.3 — per-well β₃ CIs + BACI summary rows |
| `10_cfell_06_full_parameters.csv` | Data | Paper Section 4.6.5 — β₁, β₂, β₃ + CIs per well, Before/After/After_Scrape2 |
| `10_cfell_07_coefficient_slopes.csv` | Data | Coefficient slope summary |
| `10_cfell_08_baci_timeseries_plotdata.csv` | Data | Paper Section 4.6.2 — raw BACI time series for plotting |
| `10_cfell_09_table5_beta3_before_after.csv` | Table | **Paper Table 5** — before/after β₃ with delta and significance by zone |
| `10_cfell_09b_climate_corrected_cusum.csv` | Data | Paper Section 4.6.3 — climate-corrected CUSUM verification |
| `10_cfell_11_nw10_broadleaf_trend.csv` | Data | **Paper Section 4.6.8** — NW10 broadleaf anomaly and OLS trend |
| `10_cfell_01_dual_control_baci.png` | Figure | **Figure 21** (4-panel ANCOVA-BACI: cum WB, corrected BACI, CUSUM, scatter) |
| `10_cfell_01b_raw_baci.png` | Figure | **Figure 20** (3-panel raw BACI: hydrographs, displacement, CUSUM) |
| `10_cfell_02_drainage_diagnostic_part{n}.png` | Figure | Supplementary — drainage component scatter (Before vs After) per well, 8 wells per page |
| `10_cfell_03_beta3_ols_slopes.png` | Figure | **Figure 24** (SSM coefficient shifts: 3-row × 2-col, zone-grouped whisker + Δ inset) |
| `10_cfell_10_clearfell_transect.png` | Figure | **Figure 22** (3-panel spatial transect: hydrographs, anomaly, step bar chart) |
| `10_cfell_10_clearfell_transect_steps.csv` | Data | Paper Section 4.6.4 — per-well step changes and distances |

**Table 5 construction:** `export_table5_summary()` combines `After` and
`After_Scrape2` periods into a single post-felling estimate by pooling
observations. Zone assignments (Core Impact, Edge Zone, Regional Ctrl) are
hard-coded in the function. Well order follows the spatial progression from
core through edge to regional control.

**Transect analysis:** Six wells from plantation interior to dune edge
(CEH2 414m, CEH34 285m, CEH16 191m, CEH20 186m, NW8B 184m, WMC3 92m —
distances from clearfell centroid E=241177, N=363645). Post-felling step
change vs scrape-era baseline is spatially uniform across all wells with no
distance gradient, consistent with a climate baseline effect rather than a
clearfell-specific gradient.

**NW10 broadleaf trend analysis (Section 4.6.8):** Compares NW10 normalised
summer minimum anomaly (Jun–Sep max depth) against a pine interior composite
(CEH2, CEH32, CEH33, CEH34). OLS trend fitted over 2019–2025. The bramble-
dominated phase (2010–2021) is used for the full-record mean anomaly.

**SSM coefficient shifts figure:** Three-row figure (β₁, β₂, β₃) with
zone-grouped whisker plots (Impact/Edge/Control). Each panel shows
per-well Before (open circle) vs After (filled square) with 95% CIs, plus
a summary inset with bootstrapped zone-mean delta ± 95% CI.

**Key verified numbers from this script (8-well control pool):**
- Raw BACI pre-scraping: −0.107 m; post-scraping: −0.325 m; post-felling: −0.370 m
- Raw step change (felling): −0.045 m; combined hydrological cost: −0.263 m
- ANCOVA Model 2: R²=0.729, scraping −0.137 m ***, clearfell −0.093 m [−0.131, −0.055] ***, combined −0.230 m
- Climate sensitivity reduction post-felling: 79.3% (pre: −0.0618 m/100mm; post: −0.0127 m/100mm)
- Climate-corrected CUSUM at clearfell date: +7.29 m; final value Feb 2026: +0.64 m
- −β₃ zone mean gains: core impact +0.021, edge +0.022, regional control +0.013
- Transect step changes (post-fell vs scrape era): WMC3 +0.142 m, NW8B +0.127 m, CEH20 +0.108 m, CEH16 +0.026 m, CEH34 +0.094 m, CEH2 +0.130 m — no distance gradient
- NW10 broadleaf anomaly vs pine composite (CEH2, CEH32, CEH33, CEH34), mean 2010–2021: +0.267 m
- NW10 trend 2019–2025: −11.2 mm/yr, p = 0.094, n = 7 (non-significant)
- Oct 2023 scraping term: coef = −0.031 m, p = 0.258, ΔAIC = +0.66 — not retained in final model

**Note:** `RAF_VALLEY_LAT_DEG` is set to 53.25° in this script for the
Thornthwaite PET day-length correction. The confirmed latitude for RAF
Valley climate station is 53.15°N (per Martin); this value is used only
as a fallback when the script reads raw climate data directly rather than
pipeline `01_climate.csv`.

---

## Script 10b — Spatial Step-Change Maps
**Purpose:** Four publication-quality spatial maps showing the step change in
mean water-table depth across the scraping (Apr 2015) and clearfell (Dec 2017)
interventions. Uses the full monitoring network (~75 wells with sufficient
data), IDW-interpolated surface with DEM hillshade and ridge masking, and KML
overlays. Produces both raw and climate-corrected versions.

Climate correction subtracts the C1 (Lake Edge) + C2 (Dune) median step
change from every well. These clusters are outside any intervention zone
of influence; their median represents the climate-driven shift between eras.
The residual isolates the intervention-specific spatial signal.

**Reads:**
- `outputs/01_wells_clean.csv` ← main network
- `outputs/01_wells_extended.csv` ← extended wells (FE series, edge wells)
- `outputs/03_master_data.csv` ← cluster assignments
- `data/Well_locations_height.csv` ← well coordinates and DEM elevations
- `data/newborough_dem.tif` ← DEM raster (hillshade + ridge masking)
- `data/Features.kml`, `data/clearfell.kml` ← site feature overlays

**Era definitions:**
- **Pre-scraping:** before April 2015
- **Scrape era:** April 2015 – December 2017
- **Post-felling:** December 2017 onward
- Minimum 6 months of data per era required for inclusion.

**Climate reference:** C1 + C2 median step change (n=33 wells).
Scraping baseline: −0.053 m; clearfell baseline: +0.107 m.

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/10_clearfell_baci/):**

| File | Type | Paper destination |
|---|---|---|
| `10b_spatial_scrape_raw.png` | Figure | Raw step change: scraping |
| `10b_spatial_fell_raw.png` | Figure | Raw step change: clearfell |
| `10b_spatial_scrape_corrected.png` | Figure | Climate-corrected: scraping |
| `10b_spatial_fell_corrected.png` | Figure | Climate-corrected: clearfell |
| `10b_spatial_step_data.csv` | Data | Per-well step changes (raw + corrected), coordinates, cluster |

**Key findings (console summary):**
- Clearfell zone (15 wells, <350 m from centroid): raw +0.080 m, corrected −0.027 m
- C1+C2 reference (33 wells): raw +0.108 m (site-wide drying trend)
- Clearfell vs C1+C2: −0.028 m (clearfell zone 28 mm wetter than reference)
- NE quadrant (27 wells, open dune): raw +0.109 m — clearfell 29 mm wetter
- Interpretation: the felled area resisted the site-wide drying trend,
  consistent with reduced canopy transpiration after tree removal

---
---

## Script 10c — Forest Zone Spatial Analysis
**Purpose:** Investigates the spatial structure of SSM coefficients (β₁, β₂, β₃)
within the forest zone (C4 Main Forest + C5 Coastal Forest). Tests whether the
C4/C5 partition reflects a genuine substrate/topographic transition or is
arbitrary within a continuous gradient.

Four questions addressed:
1. Which spatial variable (elevation, distance from ridge, Easting) best
   predicts within-forest coefficient variation?
2. Do C4 and C5 form two distinct groups or a continuum in β₁–β₂ space?
3. Are NW10 (broadleaf, high β₁) and CEH14 (ridge flank, high β₂)
   positional outliers or canopy-type outliers?
4. Does the C4/C5 boundary correspond to a physical substrate transition?

**Reads:**
- `outputs/07_spatial_coefficients/07_coeff_maps_data.csv` ← per-well SSM coefficients
- `outputs/06_pear_membership_audit_sitewide.csv` ← Pearson affinity correlations
- `data/newborough_dem.tif` ← DEM raster (hillshade for boundary map)
- `data/Features.kml`, `data/streams.kml` ← site feature overlays

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/10c_forest_zone_analysis/):**

| File | Type | Description |
|---|---|---|
| `10c_forest_zone_correlations.csv` | Data | Pearson correlations and regression R² |
| `10c_forest_zone_cluster_summary.csv` | Data | C4 vs C5 summary statistics and t-tests |
| `10c_01_b1_b2_scatter.png` | Figure | β₁ vs β₂ scatter coloured by cluster |
| `10c_02_b2_elevation_regression.png` | Figure | β₂ vs elevation linear regression |
| `10c_03_c4_c5_boundary_map.png` | Figure | Spatial map of C4/C5 wells with elevation context |
| `10c_04_forest_zone_summary.txt` | Text | Interpretive summary of all four questions |

**Key findings:**
- Elevation explains 95.1% of β₂ variance across 14 forest wells (r = 0.975)
- C4 and C5 are two distinct groups in β₂ (p < 0.001), not a continuum
- CEH14's extreme β₂ is consistent with its elevation — not a genuine outlier
- C4/C5 boundary corresponds to an elevation gap of 2.2 m (zero overlap),
  reflecting the dune ridge → coastal plain topographic transition


## Script 11 — Forecasting Thresholds
**Purpose:** Fits cluster-level mechanistic SSM equations (Section 1), derives
P_flood threshold equations via the iterated closed-form SSM (§3.6.3,
Section 3), and fits seasonal block transfer functions for winter peak
(Section 2) and summer minimum (Section 4) prediction.

Under the k=5 partition all five clusters are included. The old k=6
EXCLUDED_CLUSTERS set (C5 tidal, C6 lake-buffered) has been emptied; those
groups were cleaned out at the partition level.

**Reads:**
- `outputs/03_regional_averages.csv`
- `outputs/03_cluster_peak_months.csv` ← cluster-specific peak month (from script 03)

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/11_forecasting_thresholds/):**

| File | Type | Paper destination |
|---|---|---|
| `11_forecast_01_results.txt` | Text | Reference/verification |
| `11_forecast_winter_transfer_functions.csv` | Table | **Paper Table 6** |
| `11_forecast_summer_transfer_functions.csv` | Table | **Paper Table 7** |
| `11_forecast_pflood_threshold_equations.csv` | Table | **Paper Table 8** |

**Section 1** fits Δh = β₁P − β₂PET − β₃h_prev (OLS without intercept) on
the cluster-mean hydrograph in mm units. β₁ for each cluster is used by
Section 3 to derive the closed-form P_flood.

**Section 2** fits peak-flood transfer functions per block
(h_peak = β₁·P_winter + β₂·h_min + c). Under k=5, five separate blocks:
Lake_Edge, Eastern_Block, Western_Block, Forest, Coastal_Forest.

**Section 3** derives the iterated closed-form P_flood per cluster:
`P_flood = slope_A × d + intercept_B` where d is depth below ground (m).
`slope_A = αⁿ × P_clim_total / (β₁ × S_P)` and
`intercept_B = β₂ × S_E × P_clim_total / (β₁ × S_P)`.
The horizon months (Oct → peak_month) are loaded dynamically from
`03_cluster_peak_months.csv`.

**Section 4** fits summer-drought transfer functions per block
(h_min = β₁·P_summer + β₂·h_max_winter + c).

**!! Known issue — iterated-SSM / block-TF discrepancy:**
The Section 1 SSM is fit on year-round monthly data but applied to a
winter-only horizon in Section 3. This produces P_flood values that
contradict the empirical block transfer functions (Section 2). For C1
(Lake), block-TF inversion gives ~1.05× climatological rainfall to reach
surface from 0.81 m depth; the iterated SSM gives 2.75×. For C4 (Main
Forest), β₁ is negative (p=0.54) making the closed form meaningless.
See `HANDOVER_PFLOOD_DIAGNOSIS.md` for full analysis and proposed fixes.

---

## Script 11b — Spatial Threshold Maps and Forecaster
**Purpose:** Produces spatial threshold maps (summer minima, winter maxima,
P_flood, flood frequency) and builds the interactive web forecaster by
injecting pipeline data into the forecaster HTML template.

**Reads:**
- `outputs/03_master_data.csv` ← per-well SSM coefficients
- `outputs/03_cluster_mechanistic_coefficients.csv` ← per-cluster β values
- `outputs/03_regional_averages.csv` ← monthly climatology
- `outputs/06_pear_membership_audit_sitewide.csv` ← extended-network cluster assignments
- `outputs/11_forecast_pflood_threshold_equations.csv` ← Table 8 (slope_A, intercept_B)
- `outputs/11_forecast_winter_transfer_functions.csv` ← Table 6
- `outputs/11_forecast_summer_transfer_functions.csv` ← Table 7
- `outputs/03_cluster_peak_months.csv` ← peak months per cluster
- `src/forecaster_template.html` ← static HTML/JS shell for the forecaster

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/11b_spatial_thresholds/):**

| File | Type | Paper destination |
|---|---|---|
| `11b_01_summer_minima_depth.png` | Figure | **Figure 26** — mean summer minimum depth |
| `11b_02_winter_maxima_depth.png` | Figure | **Figure 28** — mean winter maximum depth |
| `11b_03_pflood.png` | Figure | **Figure 27** — P_flood spatial distribution |
| `11b_04_flood_frequency.png` | Figure | **Figure 29** — winter flooding frequency |
| `11b_05_pflood_per_well.csv` | Data | Per-well P_flood and λ values (Table 10) |
| `forecaster.html` | Interactive | Groundwater flooding forecaster web app |

**Key features:**
- Five separate blocks (one per cluster) under k=5 partition.
- `NEAREST_CLUSTER_ONLY_WELLS = {ceh3, ceh4, ceh7, ceh8, ceh37}` — wells
  whose cluster assignment is a pattern-match nearest-type, not a core
  membership. These wells appear in the forecaster with a `nearest_cluster_only`
  flag; the template renders them with an asterisk and an explanatory notice.
- `_coerce_cluster_int()` helper handles the int-vs-string schema mismatch
  between Script 03 (integer Cluster column) and Script 11 (string 'C1'
  Cluster column) defensively.
- β column names from `03_cluster_mechanistic_coefficients.csv` are `beta_1`,
  `beta_2`, `beta_3` (short names). The `/1000` conversion (m/m → m/mm) is
  correct and required because downstream P_flood arithmetic uses P_clim in mm.

**Forecaster template (`src/forecaster_template.html`):**
- Data-driven well selector (derived from `Object.keys(DATA.cluster_coeffs)`)
- Horizon labels derived at runtime from `coeff.peak_month`
- Default selection: first well in bundle (no hardcoded cluster ID)
- Nearest-cluster-only wells badged with asterisk + explanatory notice

---

## Script 12 — Site Overview Figure
**Purpose:** Produces publication-quality GIS site map with DEM, well network,
and site features.

**Reads:**
- `outputs/01_locations.csv`
- DEM and KML files from data/

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/12_figure_site_overview/):**

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

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/13_figure_experimental_design/):**

| File | Type | Paper destination |
|---|---|---|
| `13_01_experimental_setup_map.png` | Figure | **Figure 2** |

---

## Script 14 — Climate Projections
**Purpose:** Fits OLS trends to annual summer minima for the slack-ecology
trajectory clusters (C1 Lake, C2 Dune, C3 Western Residual) and extrapolates
to 2040. Plots observed winter maxima against flooding thresholds. Identifies
2030–2039 critical intervention window.

Forest clusters (C4 Main Forest, C5 Coastal Forest) are shown as faded
background scatter on the trajectory panels — no trend lines are fitted
because their summer minima lie below the slack ecohydrological viability
thresholds (Curreli et al. 2013). A methods footnote explains this on each
figure. The `TRAJECTORY_CLUSTERS` constant in the script controls scope;
the `FOREST_CONTEXT_CLUSTERS` constant controls which clusters appear as
faded context scatter.

The interactive seasonal-extremes scatter (`14_seasonal_extremes_scatter.html`)
uses all five clusters from `02_cluster_stats.csv` via config-derived label
and colour dicts.

**Reads:**
- `outputs/03_regional_averages.csv`
- `outputs/02_cluster_stats.csv` ← cluster assignments for scatter plot
- `outputs/00_well_network_table.csv` ← well-level seasonal extremes

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/14_climate_projections/):**

| File | Type | Paper destination |
|---|---|---|
| `14_climate_trajectory_summer.png` | Figure | Figure 30a |
| `14_climate_trajectory_winter_flooding.png` | Figure | Figure 30b |
| `14_climate_trajectory_stacked.png` | Figure | **Figure 30 (combined)** |
| `14_summer_trend_stats.csv` | Data | Paper Section 4.8.1 verification |
| `14_annual_extremes.csv` | Data | Paper Section 4.8 source data |
| `14_winter_exceedance.csv` | Data | Paper Section 4.8.2 source data |
| `14_seasonal_extremes_scatter.html` | Interactive figure | Seasonal Extremes tab in scenario viewer |

**Key numbers (!! VERIFY — regenerate by running script 14):**
- C1: −0.0100 m yr⁻¹ (R²=0.247, p=0.026, n=20 — missing summer 2005)
- C2: −0.0115 m yr⁻¹ (R²=0.172, p=0.061, n=21)
- C3: −0.0149 m yr⁻¹ (R²=0.166, p=0.067, n=21)
- Winter flooding (wet slack): C1 14/21 yrs (67%), C2 11/21 (52%), C3 1/21 (5%)
- Winter panel shows cluster mean (dashed) and median (dotted)
  horizontal lines per cluster with μ/ø annotations.

---

## Script 19 — Hydrological Scenario Viewer

Script 19 is a **standalone self-contained HTML scenario viewer**. It is not
part of the numbered 29-step pipeline. It reads pipeline outputs directly and
generates an interactive browser-based tool for exploring management and climate
scenarios. Run separately via option 4 in the interactive menu, or
`python run_analysis.py --viewer`.

**Note:** Scripts 19a and 19b no longer exist. Script 19 now handles everything
previously split across those two scripts — it loads data, computes per-well
scenario Δh dynamically in JavaScript, and outputs a single HTML file.

**Reads:**
- `outputs/03_master_data.csv` — SSM coefficients and cluster assignments
- `outputs/01_climate.csv` — climate record
- `outputs/01_well_elevations.csv` — pipe top elevations
- `outputs/01_wells_clean_maod.csv` — reference well maOD time series
- `data/Features.kml`, `data/site_boundary.kml` — KML overlays

**Produces:**
- `outputs/19_spatial_groundwater/scenario_viewer.html` — self-contained viewer

**Scenario parameters (JavaScript, computed per-well dynamically):**
- baseline: sP=1.00, sPET=1.00, sI=FOREST_INTERCEPTION(0.24), sB2=1.00
- climate_dry: sP=0.90 (−10% P), sPET=1.10 (+10% PET)
- climate_wet: sP=1.10 (+10% P), sPET=1.00 (PET unchanged — conservative)
- clearfell: sI=0 (interception removed), sB2=1.35 (β₂ ×1.35)
- thinning: sI=FOREST_INTERCEPTION×0.5, sB2=1.15
- broadleaf: sI=BROADLEAF_INTERCEPTION(0.25), sB2=1.45

**Δh sign convention:** positive = water table deepens (drier); negative = shallower (wetter)

**No precomputed difference maps are produced.** Scenario Δh is computed
dynamically in the browser via the SSM equilibrium equation. Interactive
visualisation is the primary output; for paper-cited cluster-level shifts see
Section 4.9 and script 19a_scenario_runner.py (now retired).

---

## Script 21 — Forestry Scenarios and Management Intervention Figures
**Purpose:** Produces four publication figures for the forest management and
intervention analysis sections of the report.

**Reads:**
- `outputs/03_master_data.csv` ← SSM coefficients and cluster assignments
- `outputs/03_cluster_averages_maod.csv` ← cluster mean heads in maOD (from script 03)
- `outputs/07_coefficient_summary.csv` ← cluster-level β summary (from script 07)
- `outputs/01_climate.csv` ← climate record (from script 01)
- `data/Newborough_Cleaned_For_Model.csv` ← raw dipwell records (direct)
- `data/Well_locations_height.csv` ← well coordinates and pipe-top elevations (direct)

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/21_forestry_scenarios/):**

| File | Type | Report destination |
|---|---|---|
| `21_forestry_01_hydrograph.png` | Figure | Figure 35 (synthetic hydrograph) |
| `21_forestry_02_distributions.png` | Figure | Supplementary (cluster summer minima violin) |
| `21_forestry_03_scraping_eras.png` | Figure | Figure 19 (scraping treatment wells) |
| `21_forestry_04_baci_zone_violin.png` | Figure | Figure 25 (BACI zone summer minima) |

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

## Script 09b — Scraping Propagation Diagnostic (Supplementary)
**Purpose:** Evaluates whether the CEH36 scraping event (0.2 m ground
lowering, April 2015) propagated uphill into the forest as a detectable
shift in SSM coefficients. Uses split-window SSM fitting with BACI
correction against distant control wells.

Companion to Script 09: Script 09 asks "did scraping work at the scraped
site?" Script 09b asks "what did scraping do to the neighbours?"

**Status:** Supplementary diagnostic (Phase 11, step 29). The split-window
coefficient shifts were not robust to methodological variation — the
two-step isolation method collapses the signal entirely. Scraping is
modelled in the report as a direct level perturbation, not a coefficient
change. This script is retained for diagnostic context only; its outputs
are not consumed by any downstream script.

**Reads:**
- `outputs/01_wells_clean.csv`
- `outputs/01_wells_extended.csv`
- `outputs/01_climate.csv`
- `outputs/01_locations.csv`
- `outputs/03_master_data.csv`

**Produces (to outputs/09_scraping_intervention/):**

| File | Type | Description |
|---|---|---|
| `09b_01_individual_well_baci.csv` | CSV | Per-well BACI-corrected Δβ₁, Δβ₂, Δβ₃ |
| `09b_02_centroid_summaries.csv` | CSV | Group centroid BACI shifts |
| `09b_03_ceh36_equilibration.jpg` | Figure | CEH36 trajectory vs CEH4 |

**Method:** SSM fitted separately to pre-scraping (start of record to
Apr 2015) and post-scraping/pre-felling (Apr 2015 to Dec 2017) windows
using `model_utils.fit_ssm()`. BACI correction subtracts the control
centroid shift (7 distant C3 wells at 850–1100 m from CEH36).

**Well selection:** 11 wells north/northwest (uphill) of CEH36. Outer C5
coastal wells excluded (western coastal boundary confound). FE wells
excluded (no pre-scraping data). See `SCRAPING_PROPAGATION_SUMMARY.md`.

---

## Data Flow Diagram (simplified)

```
RAW DATA
├── Newborough_Cleaned_For_Model.csv ──→ 01 ──→ 09, 10 (direct)
├── Well__locations_height.csv ─────────→ 01
└── RAF_Valley_Climate.csv ─────────────→ 01 ──→ 09, 10 (direct)

SCRIPT 01 outputs
├── 01_climate.csv ─────────────────────→ 00, 02, 03, 08, 11
├── 01_wells_clean.csv ─────────────────→ 00, 02, 03, 05, 08
├── 01_wells_reference.csv ─────────────→ 02, 08
├── 01_wells_extended.csv ──────────────→ 06
├── 01_locations.csv ───────────────────→ 03, 04, 05, 06, 08, 12, 13
└── 01_well_elevations.csv ─────────────→ 03, 07

SCRIPT 02 outputs
└── 02_cluster_stats.csv ───────────────→ 03, 04, 05, 06, 08, 13

SCRIPT 03 outputs
├── 03_master_data.csv ─────────────────→ 07, 08, 10, 16, 17, 18, 19, 21, 21
├── 03_regional_averages.csv ───────────→ 11, 14, 16
├── 03_cluster_averages_maod.csv ───────→ 21
├── 03_cluster_peak_months.csv ─────────→ 11, 11b
├── 03_cluster_summary_table.csv ───────→ Paper Table 1
└── 03_cluster_mechanistic_coefficients → Paper Table 2, 11b

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
├── 11b_01_summer_minima_depth.png ─────→ Figure 26 (Section 4.7.4)
├── 11b_02_winter_maxima_depth.png ─────→ Figure 28 (Section 4.7.4)
├── 11b_03_pflood.png ─────────────────→ Figure 27 (Section 4.7.4)
├── 11b_04_flood_frequency.png ─────────→ Figure 29 (Section 4.7.4)
├── 11b_05_pflood_per_well.csv ─────────→ Table 10 (per-well P_flood)
└── forecaster.html ────────────────────→ Interactive forecaster web app

SCRIPT 14 outputs
└── 14_climate_trajectory_stacked.png ──→ Paper Figure 30

SCRIPT 15 outputs (depth-dependent PET)
└── [diagnostic figures — not cited in main paper]

SCRIPT 17 → SCRIPT 16 → SCRIPT 18 → SCRIPT 19 → SCRIPT 20
├── 17_wtf_01_sy_table.csv ─────────────→ feeds 16, 18, 19
├── 16_wb_03_table.csv ─────────────────→ Paper Table (water balance)
├── 18_wtf_02_spatial_sy_map.png ───────→ Paper Figure (Sy distribution)
├── 19_head_mean_map.png ───────────────→ Paper Figure (Section 4.9)
├── 19_residual_comparison.png ─────────→ Paper Figure (validation)
├── 20_head_surface_streams.png ────────→ Paper Figure 33 (Section 4.9)
└── 20_residual_d8_comparison.png ──────→ Paper Figure 34 (Section 4.9)
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
- Reference-network whitelist reduced from 69 to 66 wells. Three additional
  exclusions: Llyn Rhos (lake surface), CEH3 and CEH22 (tidal-signal
  singleton outliers). All three remain in the extended network.
- Exclusion rationale documented in `REFERENCE_NETWORK_WHITELIST` docstring.
- `01_wells_clean_maod.csv` output added to paths.py.

### Script 02
- Cluster hydrograph figure now reads `01_wells_clean.csv` directly
- Removed dependency on `03_regional_averages.csv` (was showing mAOD values)
- **Distance metric bug fixed:** `pdist(1 - corr_matrix)` was computing
  Euclidean distances on (1−r) row vectors rather than correlation distance.
  Replaced with a dedicated `_correlation_distance()` helper that builds the
  correct condensed distance matrix via `1 - corr`, clip, symmetrise,
  `squareform`. All four consumers of Ward's tree (main partition, validation
  plots, stability diagnostics, dendrogram) now agree on the same distance.
- **k reduced from 6 to 5.** Bootstrap stability analysis (1000 resamples at
  k=4..7) showed that k=6 produced a singleton or fragile 2-well cluster at
  every configuration tested. k=5 gives four robust clusters (stability
  ≥ 0.93) plus one moderate cluster (Western Residual, 0.50).
- **Anchor-based canonical cluster IDs.** `CLUSTER_ID_ANCHORS` dict maps
  fcluster's arbitrary integer labels to stable canonical IDs via named
  anchor wells. Script raises `ValueError` if anchors land in different
  Ward's clusters (fail-loudly partition-drift detection).
- **Cluster renumbering** to match the old report ordering: C1=Lake,
  C2=Dune, C3=Western Residual, C4=Main Forest, C5=Coastal Forest.
  Colours matched to old report palette where possible; C5 Coastal Forest
  uses brown (`#8B4513`).
- **Bootstrap stability diagnostics added:** k-sweep (silhouette +
  Calinski–Harabasz + merge distance, k=2..10), bootstrap co-assignment
  heatmaps per candidate k, per-well stability CSV, per-cluster stability
  summary.
- **Amplitude descriptors added:** per-well and per-cluster seasonal
  amplitude (p90 − p10) across full / pre-2018 / post-2018 windows, with
  climate-normalised variant (drought summers 2005, 2018, 2022 removed).
  Outputs: per-well CSV, cluster summary CSV, boxplot figure.
- Old hardcoded labels ("Eastern Block Lake", "Forest", etc.) removed.
  All labels now sourced from `utils/config.CLUSTER_LABELS`.


### Script 03
- Upstand correction applied before cluster averaging
- Exports corrected mechanistic coefficients table
- **April 2026:** `export_cluster_peak_months()` added — writes
  `03_cluster_peak_months.csv` (long-term mean peak month per cluster,
  derived from cluster-centroid hydrograph). Consumed by scripts 11 and 11b.
- **April 2026:** LCSC print block sorted by integer cluster ID (was
  alphabetical by block label, which put Coastal Forest before Eastern Block).

### Script 10
- Added `10_cfell_09b_climate_corrected_cusum.csv` export
- Prints verification stats to console

### Script 11b
- CEH18 and CEH21 DEM corrections applied (see table above)
- Uses full well network (68 reference + 19 extended, 87 total)
- Ecological zones use Curreli et al. (2013) thresholds with BACI scraping
  recovery limits from Hollingham (2026): SD15b recovery = 0.75 m,
  SD16 recovery = 1.20 m
- **April 2026:** Three new figures added — winter maxima depth map,
  P_flood map, and flood frequency map (Paper Figures 27, 28, 29).
- **April 2026 (cluster rebuild):**
  - `EXCLUDED_CLUSTERS` emptied (old C5/C6 boundary groups retired under k=5).
  - Five separate blocks (one per cluster) replacing the old 3-block
    macro-aggregation (Eastern/Western/Forest).
  - `NEAREST_CLUSTER_ONLY_WELLS = {ceh3, ceh4, ceh7, ceh8, ceh37}` — tidal
    and upstream-excluded wells are flagged (not dropped) so the forecaster
    UI can communicate "nearest-type assignment, not core member".
  - `_coerce_cluster_int()` helper added to handle the int-vs-string
    schema mismatch between Script 03 and Script 11 Cluster columns.
  - β column names corrected: `beta_1`, `beta_2`, `beta_3` (matching
    `03_cluster_mechanistic_coefficients.csv`). The `/1000` conversion
    (m/m → m/mm) is correct — downstream P_flood works in mm.
  - Forecaster HTML template (`forecaster_template.html`) patched:
    data-driven well-selector order, peak-month-derived horizon labels,
    nearest-cluster-only badging with explanatory notice, default selection
    is first well in bundle (no hardcoded cluster ID).

**Produces (https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/11b_spatial_thresholds/):**

| File | Type | Paper destination |
|---|---|---|
| `11b_01_summer_minima_depth.png` | Figure | **Figure 26** — mean summer minimum depth |
| `11b_02_winter_maxima_depth.png` | Figure | **Figure 28** — mean winter maximum depth |
| `11b_03_pflood.png` | Figure | **Figure 27** — P_flood spatial distribution |
| `11b_04_flood_frequency.png` | Figure | **Figure 29** — winter flooding frequency |

**Key constants:**
- `MEAN_WINTER_RAINFALL_MM = 521` — mean annual Oct–Mar rainfall, monitoring period 2005–2026
- P_flood equation: `(h_gap + β₃ × h_prev) / β₁` using per-well SSM coefficients from `03_master_data.csv`
- Flood frequency: % of hydrological years (Oct–Sep) where winter maximum maOD ≥ DEM ground elevation

### Script 14
- Added p-value output to console
- Fixed C1 winter n (was hardcoded as 20, corrected to 21)
- Added three CSV exports for verification
- **April 2026 (cluster rebuild):**
  - Labels, colours, markers now sourced from `utils/config.py`.
  - `TRAJECTORY_CLUSTERS = ("C1", "C2", "C3")` — explicit constant
    separating trajectory scope from styling scope.
  - Forest clusters (C4, C5) rendered as faded background scatter on all
    three trajectory panels, with italic methods footnote: "Forest clusters
    shown for context only — no trend fitted, as wells lie below the slack
    ecohydrological viability thresholds (Curreli et al. 2013)."
  - Summer y-axis widened from −1.60 to −2.10 m to accommodate forest wells.
  - Seasonal scatter HTML: `_SCATTER_COLOURS`/`_SCATTER_LABELS` replaced
    with config adapters; legacy "C5/C6 Boundary" grey aliases retired.
    Cluster-map int-vs-string bug fixed. Silent `.fillna("C2")` default
    replaced with explicit UNKNOWN constant.

### Cluster-label standardisation pass (April 2026)
All downstream scripts updated to source labels, colours, and markers from
`utils/config.py` rather than hardcoded local dicts. Scripts touched:
02, 03, 07, 08, 11, 11b, 14, 15, 16, 17, 18, 22, 23, 24, plus
`paths.py` and `forecaster_template.html`. Key changes per script:

- **07, 08, 22, 23, 24:** pure label/colour swap (local dicts → config import).
- **15:** `CLUSTER_ORDER` from config; 2×2 grids → 2×3 with unused panel hidden.
- **16:** programmatic label dicts (auto-sync with config + Sy values);
  `FOREST_CIDS = (4, 5)` for interception correction; `col_map` derived
  dynamically; `RESIDUAL_PCT_SE`/`FLOOD_FREQ`/`SY_WTF`/`SUMMER_TRENDS`
  left as 4-entry dicts with `!! REGENERATE` flags pending C5 computation.
  β column names corrected to match `03_master_data.csv` schema.
- **17:** string-keyed adapter; `FOREST_CIDS = ("C4", "C5")`; all four-cluster
  iterations extended to five; regression subplot 2×2 → 2×3.
- **18:** label/colour swap; `EXCLUDE_CLUSTERS` emptied; `FOREST_CIDS = (4, 5)`.

See `PARTITION_HISTORY.md` for the full renumber mapping, identity-vs-integer
rule, Sy values, and list of stale dicts requiring regeneration.

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

### Script 19 — scenario viewer (April 2026, revised)
- Complete rewrite of both scripts.
- Scripts 19a and 19b retired; script 19 now a standalone scenario viewer
  six scenarios across ten water balance and head fields. Maps are auto-scaled
  from well-level p5–p95 Δ values; maps below a per-field threshold are omitted.
- Climate scenario parameters: climate_dry sP=0.90/sPET=1.10; climate_wet sP=1.10/sPET=1.00
  Baseline Maps, Seasonal Profiles. Produces both a standalone base64-embedded
  viewer and a lightweight linked viewer for GitHub Pages.
- Colour convention: red = drier/more than baseline; blue = wetter/less.
  RdBu colourmap for head and recharge (positive = wetter = blue);
  RdBu_r for depth, ET, and drainage (positive = drier = red);
  YlOrRd for seasonal storage change (magnitude only).

### Script 19 — map extent
- All figures now explicitly set xlim(240100, 243900), ylim(362200, 365800)
  via _base_map() — previously the DEM extent was used

### config.py:**
- `CLUSTER_LABELS` updated to k=5 canonical names.
- `CLUSTER_COLOURS` matched to old report palette; C5 = brown.
- Module docstring added noting that `CLUSTER_LABELS.keys()` is
  authoritative for "which clusters are in use".

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

### Terminology rename: "boundary subsidy" → "water balance residual" (2026-04-20)
- Scripts 07, 08, 16, 19, 20, 21 — all figure titles, CSV column headers, legend
  labels, docstring text, and internal variable names renamed. The underlying
  quantity is unchanged; only the terminology differs, for alignment with the
  academic summary document.
- Script 16 — `SUBSIDY_PCT_SE` → `RESIDUAL_PCT_SE`; `C_SUB` → `C_RES`;
  `subsidy`/`subsidy_se` → `residual`/`residual_se`
- Script 16 CSV column headers now read "Water balance residual (m/month)",
  "Residual (mm/yr)", "Residual (% rainfall)", "Residual SE (mm/yr)" (previously
  "Boundary Subsidy (m/month)", "Subsidy (mm/yr)" etc.)
- Script 20 — `lateral_residual` DataFrame column → `residual_wb`; figure title
  "SSM Lateral Inflow Residual" → "SSM Water Balance Residual"

### Script 00 (2026-04-20)
- New Figure 4 (`00_03_summer_warming_trend.png`) — RAF Valley summer
  (JJA) maximum-temperature anomaly plot with linear trend line over the
  full 95-year record. Produced from raw `data/RAF_Valley_Climate.csv`;
  accompanied by `00_03_summer_warming_stats.csv` containing per-year
  values and regression statistics.
- Figures 1 and 2 now generate on both profiles (previously skipped on
  the full profile).
- `run_analysis.py` now calls script 00 with `--profile full` (previously
  passed `--profile short`), producing the full-record outputs by default.

### run_analysis.py (2026-04-20)
- Scripts 18 and 19 now invoked with `--supplementary` to produce their
  complete output sets (WTF IDW contour maps for 18; thickness, seasonal,
  β fields, water balance, flux, storage, depth-to-WT and winter flooding
  maps for 19).
- `VIEWER_SCRIPTS` list collapsed to `VIEWER_SCRIPT` constant — only
  script 19 is now required for the viewer menu option (19b retired).

---

## Paper Tables Quick Reference

| Table | Script | File |
|---|---|---|
| Table 1: Cluster summary | 03 | `03_cluster_summary_table.csv` |
| Table 2: Mechanistic coefficients | 03 | `03_cluster_mechanistic_coefficients.csv` |
| Table 3: Model benchmarking | 08 | `08_lcsc_04_table3_benchmark_summary.csv` |
| Table 4: Scraping −β₃ era summary | 09 | `09_scrape_04b_table4_beta3_era_summary.csv` |
| Table 5: Clearfell −β₃ before/after | 10 | `10_cfell_09_table5_beta3_before_after.csv` |
| Table 6: Winter transfer functions | 11 | `11_forecast_winter_transfer_functions.csv` |
| Table 7: Summer transfer functions | 11 | `11_forecast_summer_transfer_functions.csv` |
| Table 8: Pflood equations | 11 | `11_forecast_pflood_threshold_equations.csv` |

---

## Paper Figures Quick Reference

Output files link directly to the repository. Not all pipeline outputs appear in the paper — each script directory contains additional diagnostic and supplementary figures.

| Figure | Description | Script | File |
|---|---|---|---|
| Figure 1 | Site overview | 12 | [`12_01_dem_site_overview.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/12_figure_site_overview/12_01_dem_site_overview.png) |
| Figure 2 | Experimental design | 13 | [`13_01_experimental_setup_map.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/13_figure_experimental_design/13_01_experimental_setup_map.png) |
| Figure 3 | Climate timeseries | 00 | [`00_01_climate_timeseries.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/00_climate_summary/00_01_climate_timeseries.png) |
| Figure 4 | Summer temperature trend | 00 | [`00_03_summer_warming_trend.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/00_climate_summary/00_03_summer_warming_trend.png) |
| Figure 5 | Well network | 00 | [`00_02_well_network_summary.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/00_climate_summary/00_02_well_network_summary.png) |
| Figure 6 | Cluster validation | 02 | [`02_02_validation_plots.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/02_clustering/02_02_validation_plots.png) |
| Figure 7 | Dendrogram | 02 | [`02_01_dendrogram.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/02_clustering/02_01_dendrogram.png) |
| Figure 8 | Cluster hydrographs | 02 | [`02_03_cluster_hydrographs_wb.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/02_clustering/02_03_cluster_hydrographs_wb.png) |
| Figure 9 | Water balance decomposition | 16 | [`16_wb_02_bar_ms.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/16_water_bal/16_wb_02_bar_ms.png) |
| Figure 10 | WTF Sy surface | 18 | [`18_wtf_04_sy_contour_extended.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/18_wtf_spatial/18_wtf_04_sy_contour_extended.png) |
| Figure 11 | Pearson affinity chart | 06 | [`06_pear_01_affinity_chart_extended.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/06_pearson_extended/06_pear_01_affinity_chart_extended.png) |
| Figure 12a | Pearson confidence map | 05 | [`05_pear_01_spatial_confidence_map.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/05_pearson_affinity/05_pear_01_spatial_confidence_map.png) |
| Figure 12b | Cluster integration map | 06 | [`06_pear_02_integration_map.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/06_pearson_extended/06_pear_02_integration_map.png) |
| Figure 13 | SSM vs TLM at CEH6 | 08 | [`08_lcsc_01_ceh6_showdown.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/08_model_benchmarking/08_lcsc_01_ceh6_showdown.png) |
| Figure 14a | SSM R² gain map | 08 | [`08_lcsc_02_r2_improvement_map.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/08_model_benchmarking/08_lcsc_02_r2_improvement_map.png) |
| Figure 14b | SSM NSE gain map | 08 | [`08_lcsc_03_nse_improvement_map.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/08_model_benchmarking/08_lcsc_03_nse_improvement_map.png) |
| Figure 15 | Tier 1 CUSUM | 09 | [`09_scrape_05_tier1_background_drift.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/09_scraping_intervention/09_scrape_05_tier1_background_drift.png) |
| Figure 16 | Tier 2 CUSUM treatment | 09 | [`09_scrape_06_tier2_scraping_signal.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/09_scraping_intervention/09_scrape_06_tier2_scraping_signal.png) |
| Figure 17 | Three-method robustness | 09 | [`09_scrape_08_ceh36_robustness.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/09_scraping_intervention/09_scrape_08_ceh36_robustness.png) |
| Figure 18 | Era-specific β₃ scraping | 09 | [`09_scrape_07_beta3_confidence.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/09_scraping_intervention/09_scrape_07_beta3_confidence.png) |
| Figure 19 | Scraping treatment wells | 21 | [`21_forestry_03_scraping_eras.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/21_forestry_scenarios/21_forestry_03_scraping_eras.png) |
| Figure 20 | Raw BACI clearfell | 10 | [`10_cfell_01b_raw_baci.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/10_clearfell_baci/10_cfell_01b_raw_baci.png) |
| Figure 21 | ANCOVA-BACI | 10 | [`10_cfell_01_dual_control_baci.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/10_clearfell_baci/10_cfell_01_dual_control_baci.png) |
| Figure 22 | Clearfell transect | 10 | [`10_cfell_10_clearfell_transect.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/10_clearfell_baci/10_cfell_10_clearfell_transect.png) |
| Figure 23 | Spatial step-change maps | 10b | [`10b_spatial_scrape_corrected.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/10_clearfell_baci/10b_spatial_scrape_corrected.png), [`10b_spatial_fell_corrected.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/10_clearfell_baci/10b_spatial_fell_corrected.png) |
| Figure 24 | SSM coefficient shifts | 10 | [`10_cfell_03_beta3_ols_slopes.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/10_clearfell_baci/10_cfell_03_beta3_ols_slopes.png) |
| Figure 25 | BACI zone violin | 21 | [`21_forestry_04_baci_zone_violin.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/21_forestry_scenarios/21_forestry_04_baci_zone_violin.png) |
| Figure 26 | Summer min depth map | 11b | [`11b_01_summer_minima_depth.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/11b_spatial_thresholds/11b_01_summer_minima_depth.png) |
| Figure 27 | P_flood map | 11b | [`11b_03_pflood.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/11b_spatial_thresholds/11b_03_pflood.png) |
| Figure 28 | Winter max depth map | 11b | [`11b_02_winter_maxima_depth.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/11b_spatial_thresholds/11b_02_winter_maxima_depth.png) |
| Figure 29 | Winter flooding frequency | 11b | [`11b_04_flood_frequency.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/11b_spatial_thresholds/11b_04_flood_frequency.png) |
| Figure 30 | Climate trajectory | 14 | [`14_climate_trajectory_stacked.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/14_climate_projections/14_climate_trajectory_stacked.png) |
| Figure 31 | Datum sensitivity | 03 | [`03_08_datum_sensitivity.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/03_state_space_model/03_08_datum_sensitivity.png) |
| Figure 32 | Spatial coefficient atlas | 07 | [`07_coeff_01_beta1_recharge.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/07_spatial_coefficients/07_coeff_01_beta1_recharge.png) – `07_coeff_04_r2.png` |
| Figure 33 | Head surface + Darcy vectors | 20 | [`20_head_surface_streams.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/20_spatial_figures/20_head_surface_streams.png) |
| Figure 34 | Water balance residual field | 20 | [`20_residual_ssm.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/20_spatial_figures/20_residual_ssm.png) |
| Figure 35 | Synthetic hydrograph (scenarios) | 21 | [`21_forestry_01_hydrograph.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/21_forestry_scenarios/21_forestry_01_hydrograph.png) |
| Supplementary | β₁–β₂ scatter | 10c | [`25_01_b1_b2_scatter.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/25_forest_zone_analysis/25_01_b1_b2_scatter.png) |
| Supplementary | β₂–elevation regression | 10c | [`25_02_b2_elevation_regression.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/25_forest_zone_analysis/25_02_b2_elevation_regression.png) |
| Supplementary | C4/C5 boundary map | 10c | [`25_03_c4_c5_boundary_map.png`](https://github.com/newbroman/Newborough_Hydrology/blob/main/outputs/25_forest_zone_analysis/25_03_c4_c5_boundary_map.png) |

