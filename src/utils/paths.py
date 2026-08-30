"""
utils/paths.py
Central definition of all input and output paths for the pipeline.

All scripts import from here rather than hardcoding paths. If a file moves
or is renamed, change it in one place and it propagates everywhere.

Structure
---------
Intermediate files (read by downstream scripts) live in OUT_DIR root.
Final outputs (figures, tables, reports) live in per-script subfolders.
"""

__version__ = "1.8.0"  # Hollingham (2026) — 2026-08-30. Script 12 becomes a
#   numeric emitter: OUT_12_BREAK_IN_SLOPE, OUT_12_BREAK_FIG and
#   OUT_12_REPORT_NUMBERS for the northern break in slope. See D-099.
#
# v1.7.0  # Hollingham (2026) — 2026-08-30. Storm-pair inputs and
#   outputs for Script 40: DATA_KML_COAST_2019_09_11 / DATA_KML_COAST_2020_03_31
#   (renamed from brendan*.kml), OUT_40_STORM_PAIR and OUT_40_REPORT_NUMBERS.
#   See D-098.
#
# v1.6.9  # Hollingham (2026) — 2026-08-27. OUT_10C_CORRELATION_TABLE
#     and OUT_10C_CLUSTER_SUMMARY replace the INT_ pair and move into DIR_10C.
#     Path change only; both files keep their names.
# v1.6.8  # Hollingham (2026) — 2026-08-21. Adds CANOPY_HISTORY,
#     the per-well 1989 canopy state and felling year read by Script 39.
#     Additive only.
# v1.6.7 (2026-08-21): Adds CCW_DEPTHS and
#     CCW_CODE_MAP (raw inputs for the standalone 1989-96 hindcast) and the
#     DIR_39 output block. Additive only; no existing path changes.
# v1.6.6 (2026-08-21): Adds
#     OUT_25_CORRECTION_DIAGNOSTIC and its spring companion (25_14), carrying
#     the three quantities that decide whether the fitted coastal gradient can
#     be applied to individual wells as a correction. Additive only; no
#     existing path changes.
# v1.6.5 (2026-08-21): Adds
#     OUT_10A_CONTROL_WELL_SPREAD (10a_09) and OUT_25_BACI_TIER_SPREAD (25_04b),
#     the per-control-well spread emitted beside every BACI control-tier
#     estimate and its carry-through to the coastal-gradient corroboration.
#     Additive only; no existing path changes.
# v1.6.4 (2026-08-20): Adds
#     OUT_25_ROLLING_WINDOW / _FIG for Script 25's fixed-length rolling-window
#     sweep (25_13), which slides a window of constant length along the record
#     beside the moving-start sweep already in 25_12.
# v1.6.3 (2026-08-20): Adds
#     OUT_20_SCRAPE_DRAWDOWN_PERWELL.
# v1.6.2 (2026-08-20): Adds
#     OUT_25_WINDOW_SWEEP / _FIG for Script 25's fit-window sensitivity sweep.
# v1.6.1 (2026-08-20): Adds
#     DATA_FOREST_BOUNDARY (data/geo/forest_boundary.geojson), the plantation
#     outline in EPSG:27700, from which Script 01 derives the in_forest
#     land-cover flag.
# v1.6.0 (2026-08-19): Adds the Script 25
#   cluster-attribution rebuild outputs: OUT_25_RECORD_LENGTH_COMPOSITION
#   (+ _SPRING) for the per-cluster record-length composition diagnostic, and
#   OUT_25_MATCHED_WINDOW_SENS for the reported-only matched-window
#   sensitivity. Additive only; no existing path changes.
#
# v1.5.1  # Hollingham (2026) — 2026-08-19. Reads the per-well
#   WTF Sy table from OUT_18_WELL_SY_TABLE; INT_WTF_WELL_SY is retired
#   (D-038). Pure path/symbol change, values identical.
#
# v1.5.0  # Hollingham (2026) -- 2026-08-18. OUT_00_PET_WARMING
#   added: Script 00 emits the PET response to warming (00_05).
#
# v1.4.0  # Hollingham (2026) — 2026-08-18. Adds
#   OUT_03_CENTROID_WINDOW_SENS and OUT_03_PER_WELL_WINDOW_SENS. Script 03 wrote
#   both by inline path, which was fine while it was the only party; Script 19
#   now reads them for the viewer's basis toggle, and a path spelled in two
#   places is the drift this module exists to prevent (D-034).
#
# v1.3.0  # Hollingham (2026) — 2026-08-16. Adds
#   OUT_02_MONTH_STABILITY and OUT_02_MONTH_STABILITY_FIG for the month-wise
#   partition-stability diagnostic (D-030).
#
# v1.2.0  # Hollingham (2026) — 2026-08-16
# Module versioning introduced 2026-08-13 (pre-1.1.0 history is tracked via
# the CHANGELOG_delta files and consuming-script versions). Bump this on ANY
# edit to this module, as for pipeline scripts.
# v1.2.0 (2026-08-16): OUT_30_C4_CENTROID_SENS added for the Script 30 v2.2.0
#   C4 centroid exclusion sensitivity. Reported-only: the canonical C4
#   coefficients remain OUT_03_MECHANISTIC_TABLE's nine-member fit. Script 03's
#   companion output (03_13_centroid_composition_sensitivity.csv) is written to
#   an inline DIR_03 path, matching that script's convention for its secondary
#   diagnostics — deliberately not given a constant here.
# v1.1.0 (2026-08-13): __version__ introduced; Script 03 datum-regime
#   constants added (OUT_03_PARTITION_VS_DATUM, OUT_03_DATUM_REGIME_FIG);
#   stale Script 30 section comment corrected (the constants belong to the
#   identifiability diagnostic; the constrained-fit script it named was
#   retired in Script 30 v2.1.0 — its archived outputs remain in
#   outputs/30_c4_constrained_fit/ as the reported-only triangulation source).

from pathlib import Path

# ==========================================
# ROOT DIRECTORIES
# ==========================================
_UTILS_DIR = Path(__file__).parent
SRC_DIR = _UTILS_DIR.parent
ROOT_DIR = SRC_DIR.parent

DATA_DIR = ROOT_DIR / "data"
OUT_DIR = ROOT_DIR / "outputs"

# Geographic inputs (DEM, KML/KMZ overlays, scrape footprints) live in a
# dedicated subfolder so the data/ root holds only the model-input and
# metadata tables. Route every geo path through data_geo() — no hardcoded
# geo filenames anywhere outside this module.
DATA_GEO_DIR = DATA_DIR / "geo"


def data_geo(name: str) -> Path:
    """Resolve a geographic input filename to its path under data/geo/."""
    return DATA_GEO_DIR / name

# ==========================================
# PIPELINE MANIFEST — outputs/ root
# ==========================================
# Machine-readable step/phase count and per-step tier/exec tags, emitted by
# run_analysis.py on every full/resumed run (or standalone via its
# --manifest-only flag). Documents and tooling cite this committed artefact
# rather than a typed step/phase total, which drifts every time a script is
# added or reclassified.
OUT_PIPELINE_MANIFEST = OUT_DIR / "pipeline_manifest.json"


def pipeline_manifest() -> Path:
    """Path to the committed step-count manifest emitted by run_analysis.py."""
    return OUT_PIPELINE_MANIFEST

# ==========================================
# PER-SCRIPT OUTPUT SUBDIRECTORIES
# ==========================================
DIR_00 = OUT_DIR / "00_climate_summary"
DIR_01 = OUT_DIR / "01_data_prep"
DIR_02 = OUT_DIR / "02_clustering"
DIR_03 = OUT_DIR / "03_state_space_model"
DIR_04 = OUT_DIR / "04_cluster_visualisations"
DIR_05 = OUT_DIR / "05_pearson_affinity"
DIR_06 = OUT_DIR / "06_pearson_extended"
DIR_07 = OUT_DIR / "07_spatial_coefficients"
DIR_08 = OUT_DIR / "08_model_benchmarking"
DIR_09 = OUT_DIR / "09_scraping_intervention"
DIR_10 = OUT_DIR / "10_clearfell_baci"
DIR_10C = OUT_DIR / "10c_forest_zone_analysis"
DIR_11 = OUT_DIR / "11_forecasting_thresholds"
DIR_11B = OUT_DIR / "11b_spatial_thresholds"
DIR_12 = OUT_DIR / "12_figure_site_overview"
DIR_13 = OUT_DIR / "13_figure_experimental_design"
DIR_14 = OUT_DIR / "14_climate_projections"
DIR_15 = OUT_DIR / "15_depth_dependent_pet"
DIR_16 = OUT_DIR / "16_water_balance"
DIR_17 = OUT_DIR / "17_wtf_specific_yield"
DIR_18 = OUT_DIR / "18_wtf_spatial"
DIR_19 = OUT_DIR / "19_spatial_groundwater"
DIR_20 = OUT_DIR / "20_spatial_figures"
DIR_21 = OUT_DIR / "21_forestry_scenarios"
DIR_22 = OUT_DIR / "22_residual_lag_analysis"
DIR_23 = OUT_DIR / "23_ridge_recharge_lag_test"
DIR_24 = OUT_DIR / "24_residual_seasonality"
DIR_25 = OUT_DIR / "25_coastal_gradient"
DIR_26 = OUT_DIR / "26_van_willegen_msl"
DIR_26B = OUT_DIR / "26b_van_willegen_msl_projections"
DIR_26C = OUT_DIR / "26c_msl5_report_figures"
DIR_30 = OUT_DIR / "30_c4_drainage_identifiability"
DIR_27 = OUT_DIR / "27_greyscale_figures"
DIR_28 = OUT_DIR / "28_c3_detrend"
DIR_29 = OUT_DIR / "29_within_c3_variance"

ALL_DIRS = [
    OUT_DIR,
    DIR_00, DIR_01,
    DIR_02, DIR_03, DIR_04, DIR_05, DIR_06, DIR_07,
    DIR_08, DIR_09, DIR_10, DIR_10C, DIR_11, DIR_11B, DIR_12, DIR_13, DIR_14,
    DIR_15, DIR_16, DIR_17, DIR_18, DIR_19, DIR_20, DIR_21, DIR_22, DIR_23, DIR_24,
    DIR_25, DIR_26, DIR_26B, DIR_26C, DIR_27, DIR_28, DIR_29,
]


def make_all_dirs():
    """Create all output directories if they do not already exist."""
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# ==========================================
# DATA INPUTS
# ==========================================
DATA_WELLS_RAW      = DATA_DIR / "Newborough_Cleaned_For_Model.csv"
# Consolidated well metadata (locations, both ground-elev sources, upstand,
# pipe-top, distance-to-coast, aliases) — one table, coords stored once.
DATA_WELL_METADATA  = DATA_DIR / "well_metadata.csv"
DATA_LOCATIONS_RAW  = DATA_WELL_METADATA
DATA_CLIMATE_RAW    = DATA_DIR / "RAF_Valley_Climate.csv"
# Documented external input (Script 26 v1.3.3), gitignored — NOT redistributed.
# Ellenberg-F dune-slack ecohydrology dataset, van Willegen et al. (2024),
# Mendeley Data V1, doi:10.17632/p4xvb6xxp9.1. Obtain and place at this path;
# Script 26's EbF cross-validation Pass runs if present and skips cleanly if not.
DATA_ELLENBERG_EXT  = DATA_DIR / "Ecohydrology_dataset.xlsx"

# Geographic inputs — all resolved via data_geo() (files live in data/geo/).
DATA_DEM               = data_geo("newborough_dem.tif")
DATA_KML_FEATURES      = data_geo("Features.kml")
DATA_KML_STREAMS       = data_geo("streams.kml")
DATA_KML_CLEARFELL     = data_geo("clearfell.kml")
DATA_KML_SITE_BOUNDARY = data_geo("site_boundary.kml")
# OSM-derived Caernarfon Bay + Menai Strait High Water Mark coastline,
# EPSG:27700, used as the fixed-head boundary for scrape drawdown
# method-of-images correction in Script 20.  Generated 2026-06-30 from
# OpenStreetMap via Overpass API (ODbL licence); Malltraeth estuary excluded.
DATA_COASTLINE_HWM     = data_geo("coastline_hwm.geojson")
# West-facing Caernarfon Bay MHW only (the eroding shoreline), clipped from
# coastline_hwm.geojson at the Abermenai southern tip so the non-eroding Menai
# Strait coast is excluded. This is the coastline used for the well-to-coast
# perpendicular distance (dist_coast_m); Script 01 recomputes and validates
# dist_coast_m against this geometry. EPSG:27700.
DATA_COASTLINE_ERODING = data_geo("coastline_eroding_hwm.geojson")
# Corsican pine plantation boundary, reprojected from the Features.kml
# "Forest" placemark to EPSG:27700 once and committed, so the land-cover
# flag costs the pipeline no CRS dependency — the same pattern as the
# eroding-shoreline polyline above. Script 01 derives in_forest from it.
DATA_FOREST_BOUNDARY   = data_geo("forest_boundary.geojson")
# Broadleaf restock block boundary — geometry also embedded in Features.kml
# for automatic rendering via add_kml_features(); this entry retained for
# any script that loads the boundary explicitly.
KML_BROADLEAF        = data_geo("broadleaf_restock.kml")
DATA_WELL_ELEVATIONS = DATA_WELL_METADATA  # consolidated; was Well_locations_height.csv

# Perpendicular distance from each dipwell to the eroding Caernarfon Bay
# shoreline (dist_coast_m), carried in well_metadata.csv. Script 01 recomputes
# this from the committed DATA_COASTLINE_ERODING geometry and validates the
# committed values against it (regenerate-and-validate; the committed
# dist_coast_m remains canonical). See data/COASTLINE_PROVENANCE.md. Read by
# Scripts 25/28/30/31.
DATA_DIST_COAST     = DATA_WELL_METADATA  # consolidated; was well_distance_to_coast.csv

# ==========================================
# INTERMEDIATE FILES — outputs/ root
# (read by downstream scripts)
# ==========================================

# Script 01
INT_LOCATIONS       = OUT_DIR / "01_locations.csv"
INT_CLIMATE         = OUT_DIR / "01_climate.csv"
INT_WELLS_CLEAN     = OUT_DIR / "01_wells_clean.csv"
# Audit of the in-pipeline dist_coast_m regeneration (Script 01): per-well
# committed vs recomputed perpendicular distance to the eroding shoreline.
INT_DIST_COAST_VALIDATION = OUT_DIR / "01_dist_coast_validation.csv"
# Per-cell provenance for INT_WELLS_CLEAN. Same shape and index as the cleaned
# wells file; each cell holds one of {"measured", "interpolated", "missing"}.
# Emitted by Script 01 alongside 01_wells_clean.csv since the Defect E fix
# (2026-05-19) so downstream consumers can filter or weight interpolated rows
# (e.g. annual_summer_minimum requires >=2 measured Jun-Sep months).
INT_WELLS_PROVENANCE = OUT_DIR / "01_wells_provenance.csv"
INT_WELLS_CLEAN_MAOD = OUT_DIR / "01_wells_clean_maod.csv"

# Raw records spreadsheet carrying the field comments (dry/flooded/not-found/
# inaccessible reasons) parsed by utils.comment_states. Added 2026-06-15.
DATA_WELL_RECORDS_ODS = DATA_DIR / "Newborough_well_records_pipeline.ods"  # slimmed 2-sheet pipeline ODS
# Per-cell observation-state grid (month x well) and the censored dry-at-depth
# observations, both emitted by Script 01 alongside the provenance file.
INT_OBSERVATION_STATES = OUT_DIR / "01_observation_states.csv"
INT_DRY_DEPTHS         = OUT_DIR / "01_dry_depths.csv"
INT_COVERAGE_FIGURE_REF = DIR_01 / "01_coverage_states_reference.png"
INT_COVERAGE_FIGURE_EXT = DIR_01 / "01_coverage_states_extended.png"
INT_COVERAGE_FIGURE    = INT_COVERAGE_FIGURE_REF  # back-compat alias (primary plate)
INT_OBS_STATE_CONFLICTS = OUT_DIR / "01_observation_state_conflicts.csv"
INT_WELLS_REFERENCE = OUT_DIR / "01_wells_reference.csv"
INT_WELLS_EXTENDED  = OUT_DIR / "01_wells_extended.csv"
INT_WELL_ELEVATIONS = OUT_DIR / "01_well_elevations.csv"
INT_PIPELINE_PARAMS = DIR_01 / "pipeline_scenario_params.csv"
INT_SITE_OBSERVATIONS = DIR_01 / "pipeline_site_observations.csv"

# Script 02
INT_CLUSTER_STATS   = OUT_DIR / "02_cluster_stats.csv"

# Script 03
INT_MASTER_DATA      = OUT_DIR / "03_master_data.csv"
INT_REGIONAL_AVG     = OUT_DIR / "03_regional_averages.csv"
INT_CLUSTER_AVG_MAOD = OUT_DIR / "03_regional_averages_maod.csv"  # cluster-mean maOD heads; produced by script 03, read by script 21
# Long-term mean peak month per cluster (calendar month 1-12 of highest mean
# water table). Derived from the cluster-centroid hydrograph in 03; consumed
# by script 11's forecasting horizon. Stale-data hazard noted: rerun script 03
# whenever the partition or the input window changes.
INT_CLUSTER_PEAK_MONTHS = OUT_DIR / "03_cluster_peak_months.csv"

# Script 05
INT_PEAR_AUDIT      = OUT_DIR / "05_pear_membership_audit.csv"

# Script 06
INT_PEAR_AUDIT_SITEWIDE = OUT_DIR / "06_pear_membership_audit_sitewide.csv"

# Script 07
INT_COEFF_SUMMARY     = OUT_DIR / "07_coefficient_summary.csv"

# Script 08
INT_LCSC_MODEL_STATS  = OUT_DIR / "08_lcsc_model_stats.csv"

# ==========================================
# FINAL OUTPUTS — per-script subfolders
# ==========================================

# Script 00 — Climate summary
OUT_00_CLIMATE_TIMESERIES   = DIR_00 / "00_01_climate_timeseries.png"
OUT_00_WELL_NETWORK_FIG     = DIR_00 / "00_02_well_network_summary.png"
OUT_00_SUMMER_WARMING       = DIR_00 / "00_03_summer_warming_trend.png"
OUT_00_ANNUAL_CLIMATE_TABLE = DIR_00 / "00_01_annual_climate_summary.csv"
OUT_00_WELL_NETWORK_TABLE   = DIR_00 / "00_02_well_network_summary.csv"
OUT_00_SUMMER_WARMING_TABLE = DIR_00 / "00_03_summer_warming_stats.csv"
OUT_00_PET_WARMING          = DIR_00 / "00_05_pet_warming_response.csv"  # how much
                                                                        # of the station's
                                                                        # warming reaches PET
OUT_00_CLIMATOLOGY          = DIR_00 / "00_04_climatology.csv"          # §4.1.1 12-month P/PET climatology (full-years well period)
OUT_00_REPORT_NUMBERS       = DIR_00 / "00_report_numbers.csv"          # §4.1.1 cited climate stats

# Script 02 — Clustering
OUT_02_DENDROGRAM       = DIR_02 / "02_01_dendrogram.png"
OUT_02_VALIDATION       = DIR_02 / "02_02_validation_plots.png"
# Stability diagnostics (Phase 1 rebuild validation — bootstrap co-assignment,
# k-sweep, per-well stability). See 02_clustering.py run_stability_diagnostics().
OUT_02_VALIDATION_EXTENDED = DIR_02 / "02_02b_validation_k_sweep.png"
OUT_02_STABILITY_SUMMARY   = DIR_02 / "02_04_bootstrap_stability_summary.csv"
OUT_02_K_SWEEP             = DIR_02 / "02_06_k_sweep_validation.csv"   # §4.2 Fig 6 per-k silhouette/CH/merge
OUT_02_REPORT_NUMBERS      = DIR_02 / "02_report_numbers.csv"          # §4.2 cited cluster-validation stats
OUT_02_STABILITY_PER_WELL  = DIR_02 / "02_05_bootstrap_stability_per_well.csv"
# The following two are templates — .format(k=...) is applied at the call site
# because one file is written per bootstrap k value.
# THE 02_06 PREFIX IS USED TWICE, AND IS LEFT THAT WAY DELIBERATELY.
# OUT_02_K_SWEEP above is 02_06_k_sweep_validation.csv and this is
# 02_06_coassignment_heatmap_k{k}.png. Raised by T-02, 2026-08-26, and
# checked on 2026-08-28: the two never collide, because the extensions
# differ and nothing in src/ or tools/ globs the prefix. The number is a
# naming convention, not an index anything resolves against.
# Renaming either would move a committed output and would have to be
# followed through the Methods Supplement's file-list table and the
# SCRIPT_LEDGER's Emits cell — three records changed to tidy a clash that
# has never cost anything. Noted so the next reader does not re-raise it.
OUT_02_COASSIGN_HEATMAP    = DIR_02 / "02_06_coassignment_heatmap_k{k}.png"
OUT_02_MEMBERSHIP_SWEEP    = DIR_02 / "02_07_cluster_membership_k{k}.csv"
# Cluster amplitude descriptors (pattern/amplitude orthogonality — Section 4.2).
# Raw and climate-normalised seasonal amplitude (p90 - p10), per well and per
# cluster median, plus distribution boxplot. Climate normalisation excludes
# Jun-Sep of DROUGHT_SUMMERS = (2005, 2018, 2022), empirically identified in
# the Lake-cluster follow-up from RAF Valley rainfall.
OUT_02_AMP_PER_WELL     = DIR_02 / "02_08_cluster_amplitude_per_well.csv"
OUT_02_AMP_SUMMARY      = DIR_02 / "02_09_cluster_amplitude_summary.csv"
OUT_02_AMP_BOXPLOT      = DIR_02 / "02_10_cluster_amplitude_boxplot.png"

# Month-wise partition stability (D-030). The existing bootstrap resamples
# WELLS; these two resample MONTHS, in blocks, and answer the different and
# weaker question of whether the partition reproduces on another period of
# record. Diagnostic tier — the figure is not a report figure.
OUT_02_MONTH_STABILITY     = DIR_02 / "02_11_month_stability.csv"
OUT_02_MONTH_STABILITY_FIG = DIR_02 / "02_12_month_stability_diagnostic.png"

# Script 03 — State-space model
OUT_03_SIGNATURES          = DIR_03 / "03_01_mechanistic_signatures.png"
OUT_03_CLUSTER_SUMMARY     = DIR_03 / "03_02_cluster_summary_table.csv"
OUT_03_MECHANISTIC_TABLE   = DIR_03 / "03_03_cluster_mechanistic_coefficients.csv"
OUT_03_DATUM_CONFOUND      = DIR_03 / "03_11_datum_confound_diagnostics.csv"  # optimal-datum vs mean water-table depth
# Datum-regime diagnostic (Script 03 v1.5.0): drainage flux β₃·(D+h̄) and
# drainage share of losses across the swept datums, + 2-panel regime figure.
OUT_03_PARTITION_VS_DATUM  = DIR_03 / "03_12_partition_vs_datum.csv"
OUT_03_CENTROID_WINDOW_SENS = DIR_03 / "03_14_centroid_window_sensitivity.csv"
OUT_03_PER_WELL_WINDOW_SENS = DIR_03 / "03_15_per_well_window_sensitivity.csv"
OUT_03_DATUM_REGIME_FIG    = DIR_03 / "03_12_datum_regime.png"

# Script 04 — Cluster visualisations
OUT_04_ARCHITECTURE_MAP = DIR_04 / "04_01_core_architecture_map.png"

# Script 05 — Pearson affinity
OUT_05_CONFIDENCE_MAP   = DIR_05 / "05_pear_01_spatial_confidence_map.png"
OUT_05_AFFINITY_CHART   = DIR_05 / "05_pear_02_affinity_chart_reference.png"

# Script 06 — Pearson extended
OUT_06_AFFINITY_CHART   = DIR_06 / "06_pear_01_affinity_chart_extended.png"
OUT_06_INTEGRATION_MAP  = DIR_06 / "06_pear_02_integration_map.png"

# Script 07 — Spatial coefficient maps
OUT_07_BETA1_MAP            = DIR_07 / "07_coeff_01_beta1_recharge.png"
OUT_07_BETA2_MAP            = DIR_07 / "07_coeff_02_beta2_atm_draw.png"
OUT_07_BETA3_MAP            = DIR_07 / "07_coeff_03_beta3_drainage.png"
OUT_07_R2_MAP               = DIR_07 / "07_coeff_04_r2_quality.png"
OUT_07_MAPS_DATA            = DIR_07 / "07_coeff_maps_data.csv"
OUT_07_CLUSTER_COEFF_MEANS  = DIR_07 / "07_cluster_coeff_means.csv"   # §4.9 per-cluster mean β₁/β₂/β₃ (3.7 m datum)
OUT_07_REPORT_NUMBERS       = DIR_07 / "07_report_numbers.csv"        # §4.9 cited coefficient stats

# Script 08 — Model benchmarking
OUT_08_SHOWDOWN             = DIR_08 / "08_lcsc_01_ceh6_showdown.png"
OUT_08_R2_MAP               = DIR_08 / "08_lcsc_02_r2_improvement_map.png"
OUT_08_NSE_MAP              = DIR_08 / "08_lcsc_03_nse_improvement_map.png"
OUT_08_TABLE3_SUMMARY       = DIR_08 / "08_lcsc_04_table3_benchmark_summary.csv"
OUT_08_PERWELL_NSE          = DIR_08 / "08_perwell_nse.csv"           # per-well TLM/SSM NSE + ΔNSE + β₂/β₃ join
OUT_08_CLUSTER_NSE_MEDIANS  = DIR_08 / "08_cluster_nse_medians.csv"   # per-cluster median ΔNSE and median TLM NSE
OUT_08_REPORT_NUMBERS       = DIR_08 / "08_report_numbers.csv"        # §4.9.1 cited ΔNSE stats + correlations

# Script 09 — Scraping intervention
OUT_09_FULL_PARAMS          = DIR_09 / "09_scrape_01_full_parameters.csv"
OUT_09_BETA3_SIG            = DIR_09 / "09_scrape_02_beta3_significance.csv"
OUT_09_BACI_SHIFTS          = DIR_09 / "09_scrape_03_baci_shifts.csv"
OUT_09_NET_BENEFITS         = DIR_09 / "09_scrape_04_net_benefits.csv"
OUT_09_BETA3_ERA_SUMMARY    = DIR_09 / "09_scrape_04b_beta3_era_summary.csv"
OUT_09_TIER1_DRIFT          = DIR_09 / "09_scrape_05_tier1_background_drift.png"
OUT_09_TIER2_SIGNAL         = DIR_09 / "09_scrape_06_tier2_scraping_signal.png"
OUT_09_BETA3_CI             = DIR_09 / "09_scrape_07_beta3_confidence.png"
OUT_09_ROBUSTNESS           = DIR_09 / "09_scrape_08_ceh36_robustness.png"
OUT_09_REPORT_NUMBERS       = DIR_09 / "09_scrape_report_numbers.csv"
OUT_09_TIER1_CUSUM          = DIR_09 / "09_tier1_final_cusum.csv"

# Script 09b — Scraping propagation into forest
OUT_09B_INDIVIDUAL          = DIR_09 / "09b_01_individual_well_baci.csv"
OUT_09B_CENTROIDS           = DIR_09 / "09b_02_centroid_summaries.csv"
OUT_09B_TRAJECTORY          = DIR_09 / "09b_03_ceh36_equilibration.jpg"
OUT_09B_SCENARIO            = DIR_09 / "09b_04_scenario_comparison.jpg"
OUT_09B_SCENARIO_CSV        = DIR_09 / "09b_04_scenario_comparison.csv"
OUT_09B_SUMMER_SCENARIO     = DIR_09 / "09b_05_summer_scenario_comparison.png"
OUT_09B_SUMMER_SCENARIO_CSV = DIR_09 / "09b_05_summer_scenario_comparison.csv"
OUT_09B_REPORT_NUMBERS      = DIR_09 / "09b_report_numbers.csv"

# Script 09c — Summer minima (scraping)
OUT_09C_SUMMER_MINIMA       = DIR_09 / "09c_01_summer_minima.csv"
OUT_09C_SUMMER_SHIFTS       = DIR_09 / "09c_02_summer_minima_shifts.csv"
OUT_09C_REPORT_NUMBERS      = DIR_09 / "09c_report_numbers.csv"
OUT_09C_FIG_CLIMATE         = DIR_09 / "09c_03_summer_minima_climate_ctrl.png"
OUT_09C_FIG_PAIRED          = DIR_09 / "09c_04_summer_minima_paired.png"
# Spring-mean (Mar-May) siblings — same analysis, second seasonal metric.
# The report-numbers registry is shared (09c_report_numbers.csv); spring rows
# are distinguished by their Parameter keys.
OUT_09C_SPRING_MEANS        = DIR_09 / "09c_05_spring_means.csv"
OUT_09C_SPRING_SHIFTS       = DIR_09 / "09c_06_spring_means_shifts.csv"
OUT_09C_FIG_SPRING_CLIMATE  = DIR_09 / "09c_07_spring_means_climate_ctrl.png"
OUT_09C_FIG_SPRING_PAIRED   = DIR_09 / "09c_08_spring_means_paired.png"

# Script 09d — CEH36 scenario comparison
OUT_09D_SCENARIO            = DIR_09 / "09d_01_scenario_comparison.jpg"
OUT_09D_SCENARIO_CSV        = DIR_09 / "09d_01_scenario_comparison.csv"
# Script 09f — management effects: spatial reach figure (discussion §5.8 + academic summary)
OUT_09F_EFFECTS             = DIR_09 / "09f_management_effects.png"
OUT_09F_EFFECTS_PUBLIC      = DIR_09 / "09f_management_effects_public.png"
OUT_09F_REACH_CSV           = DIR_09 / "09f_01_reach_profile.csv"
# Script 09g — mechanism diagrams: driver schematic grid + coastal reach
# reach (§5.8 conceptual figure; display/utility, tier D). SVG is the editable
# master; PNG is the report/summary placement copy.
OUT_09G_GRID_SVG            = DIR_09 / "09g_mechanism_grid.svg"
OUT_09G_GRID_PNG            = DIR_09 / "09g_mechanism_grid.png"
OUT_09G_REACH_SVG           = DIR_09 / "09g_coastal_vs_climate_reach.svg"
OUT_09G_REACH_PNG           = DIR_09 / "09g_coastal_vs_climate_reach.png"
OUT_09G_LAY_MGMT_SVG        = DIR_09 / "09g_mechanism_lay_management.svg"
OUT_09G_LAY_MGMT_PNG        = DIR_09 / "09g_mechanism_lay_management.png"
OUT_09G_LAY_DRIVERS_SVG     = DIR_09 / "09g_mechanism_lay_drivers.svg"
OUT_09G_LAY_DRIVERS_PNG     = DIR_09 / "09g_mechanism_lay_drivers.png"
OUT_09D_SUMMER_SCENARIO     = DIR_09 / "09d_02_summer_scenario_comparison.png"
OUT_09D_SUMMER_SCENARIO_CSV = DIR_09 / "09d_02_summer_scenario_comparison.csv"

# Script 09e — CEH36 robustness analysis
OUT_09E_REPORT_NUMBERS      = DIR_09 / "09e_report_numbers.csv"

# Script 10 — Clearfell BACI Analysis Suite (10a–10g)
OUT_10_REPORT_NUMBERS       = DIR_10 / "10_cfell_report_numbers.csv"
OUT_10_CONSOLIDATED_REPORT  = DIR_10 / "10_consolidated_report_numbers.csv"

# Script 10a — Three-counterfactual ANCOVA-BACI (primary result)
OUT_10A_COMPARISON          = DIR_10 / "10a_01_ancova_comparison_table.csv"
OUT_10A_FULL_COEFFS         = DIR_10 / "10a_02_ancova_full_coefficients.csv"
OUT_10A_TIMESERIES          = DIR_10 / "10a_03_baci_timeseries.csv"
OUT_10A_FIG_IMPACT          = DIR_10 / "10a_04_baci_timeseries_impact.png"
OUT_10A_FIG_EDGE            = DIR_10 / "10a_05_baci_timeseries_edge.png"
OUT_10A_FIG_SCATTER         = DIR_10 / "10a_06_climate_sensitivity.png"
OUT_10A_REPORT              = DIR_10 / "10a_report_numbers.csv"
# Single-control-well refits of each control tier's ANCOVA — the per-well
# spread that must be reported beside every tier estimate.  Read by Script 25,
# which carries it through to the BACI corroboration spread table.
OUT_10A_CONTROL_WELL_SPREAD = DIR_10 / "10a_09_control_well_spread.csv"

# Script 10b — Spatial step-change maps (scraping + clearfell)
OUT_10B_SCRAPE_RAW          = DIR_10 / "10b_spatial_scrape_raw.png"
OUT_10B_FELL_RAW            = DIR_10 / "10b_spatial_fell_raw.png"
OUT_10B_SCRAPE_CORRECTED    = DIR_10 / "10b_spatial_scrape_corrected.png"
OUT_10B_FELL_CORRECTED      = DIR_10 / "10b_spatial_fell_corrected.png"
OUT_10B_STEP_DATA           = DIR_10 / "10b_spatial_step_data.csv"

# Script 10c — Forest zone spatial analysis
# Both were INT_ at OUT_DIR root until 2026-08-27. The INT_/OUT_ convention this
# module states is "intermediate (read by a downstream script) at the root, final
# output in the per-script folder" — and nothing outside Script 10c has ever read
# either file. They were finals wearing an intermediate's prefix, and the wrong
# prefix put them in the wrong directory. Names unchanged, so every document that
# cites them by filename still resolves.
OUT_10C_CORRELATION_TABLE   = DIR_10C / "10c_forest_zone_correlations.csv"
OUT_10C_CLUSTER_SUMMARY     = DIR_10C / "10c_forest_zone_cluster_summary.csv"
OUT_10C_B1_B2_SCATTER       = DIR_10C / "10c_01_b1_b2_scatter.png"
OUT_10C_B2_ELEV_REGRESSION  = DIR_10C / "10c_02_b2_elevation_regression.png"
OUT_10C_BOUNDARY_MAP        = DIR_10C / "10c_03_c4_c5_boundary_map.png"
OUT_10C_SUMMARY             = DIR_10C / "10c_04_forest_zone_summary.txt"

# Script 10d — Summer minima (dual control)
OUT_10D_DATA                = DIR_10 / "10d_01_summer_minima.csv"
OUT_10D_SHIFTS              = DIR_10 / "10d_02_summer_minima_shifts.csv"
OUT_10D_MIXED               = DIR_10 / "10d_03_mixed_model_results.csv"
OUT_10D_FIG_FOREST          = DIR_10 / "10d_04_summer_minima_forest_ctrl.png"
OUT_10D_FIG_CLIMATE         = DIR_10 / "10d_05_summer_minima_climate_ctrl.png"
OUT_10D_REPORT              = DIR_10 / "10d_report_numbers.csv"
# Spring-mean (MAM) siblings, v1.7.0 (2026-08-13). Consumed by Script 10l's
# spring panel; 10d itself defines matching local constants.
OUT_10D_SPRING_DATA         = DIR_10 / "10d_06_spring_means.csv"
OUT_10D_SPRING_SHIFTS       = DIR_10 / "10d_07_spring_means_shifts.csv"
OUT_10D_SPRING_MIXED        = DIR_10 / "10d_08_spring_mixed_model_results.csv"
OUT_10D_FIG_SPRING_FOREST   = DIR_10 / "10d_09_spring_means_forest_ctrl.png"
OUT_10D_FIG_SPRING_CLIMATE  = DIR_10 / "10d_10_spring_means_climate_ctrl.png"

# Script 10e — SSM coefficient decomposition
OUT_10E_COEFF_SHIFTS        = DIR_10 / "10e_01_coefficient_shifts.csv"
# NOTE: 10e_02_predicted_vs_observed.csv was removed in Script 10e v1.4.0
# (2026-05-24). 10e no longer produces a predicted-vs-observed comparison.
OUT_10E_FIG_COEFFS          = DIR_10 / "10e_03_coefficient_shifts.png"
OUT_10E_REPORT              = DIR_10 / "10e_report_numbers.csv"

# Script 10f — Robustness analyses (SSM residual, synthetic control)
OUT_10F_SSM_RESIDUAL        = DIR_10 / "10f_01_ssm_residual_results.csv"
OUT_10F_SYNTH_CTRL          = DIR_10 / "10f_02_synthetic_control_results.csv"
OUT_10F_REPORT              = DIR_10 / "10f_report_numbers.csv"

# Script 10g — Diagnostics (NW10 trend, transect, rolling coefficients)
OUT_10G_NW10_TREND          = DIR_10 / "10g_01_nw10_broadleaf_trend.csv"
OUT_10G_TRANSECT_FIG        = DIR_10 / "10g_02_clearfell_transect.png"
OUT_10G_TRANSECT_CSV        = DIR_10 / "10g_03_clearfell_transect_steps.csv"
OUT_10G_ROLLING_CSV         = DIR_10 / "10g_04_rolling_coefficients.csv"
OUT_10G_REPORT              = DIR_10 / "10g_report_numbers.csv"

# Script 10h — Synthetic-extension BACI (FE well donor regression)
OUT_10H_CALIBRATION         = DIR_10 / "10h_01_synthetic_calibration.csv"
OUT_10H_COMPARISON          = DIR_10 / "10h_02_ancova_comparison_table.csv"
OUT_10H_FULL_COEFFS         = DIR_10 / "10h_03_ancova_full_coefficients.csv"
OUT_10H_TIMESERIES          = DIR_10 / "10h_04_baci_timeseries.csv"
OUT_10H_FIG_DONORS          = DIR_10 / "10h_05_donor_regression_validation.png"
OUT_10H_FIG_VAR_A           = DIR_10 / "10h_06_baci_timeseries_varA.png"
OUT_10H_FIG_VAR_B           = DIR_10 / "10h_07_baci_timeseries_varB.png"
OUT_10H_FIG_VAR_C           = DIR_10 / "10h_08_baci_timeseries_varC.png"
OUT_10H_FIG_CUSUM           = DIR_10 / "10h_09_cusum_varB.png"
OUT_10H_FIG_SENSITIVITY     = DIR_10 / "10h_10_climate_sensitivity_varB.png"
OUT_10H_REPORT              = DIR_10 / "10h_report_numbers.csv"

# Script 10i — CEH34 donor-regression hindcast (CEH9 donor)
OUT_10I_HINDCAST            = DIR_10 / "10i_01_ceh34_hindcast.csv"

# 10j — direct Impact-vs-Edge contrast (no external control)
OUT_10J_MONTHLY_RESULTS     = DIR_10 / "10j_01_monthly_contrast_results.csv"
OUT_10J_SUMMER_RESULTS      = DIR_10 / "10j_02_summer_contrast_results.csv"
OUT_10J_TIMESERIES_FIG      = DIR_10 / "10j_03_contrast_timeseries.jpg"
OUT_10J_SUMMER_FIG          = DIR_10 / "10j_04_summer_minima_contrast.jpg"
OUT_10J_REPORT              = DIR_10 / "10j_report_numbers.csv"
OUT_10I_REGRESSION          = DIR_10 / "10i_02_donor_regression.csv"
OUT_10I_DIAGNOSTIC          = DIR_10 / "10i_03_hindcast_diagnostic.png"
OUT_10I_REPORT              = DIR_10 / "10i_report_numbers.csv"

# 10k — four-zone pooled-panel BACI (Forest ref / C3-Warren / Edge / Impact)
OUT_10K_ZONE_RESULTS        = DIR_10 / "10k_01_four_zone_results.csv"
OUT_10K_PAIRWISE            = DIR_10 / "10k_02_pairwise_contrasts.csv"
OUT_10K_EASTING_SENS        = DIR_10 / "10k_03_easting_sensitivity.csv"
OUT_10K_CENTROIDS_FIG       = DIR_10 / "10k_04_zone_centroids.jpg"
OUT_10K_CONTRAST_FIG        = DIR_10 / "10k_05_contrast_forest.jpg"
OUT_10K_FOREST_PLOT         = DIR_10 / "10k_06_forest_plot.jpg"
OUT_10K_REPORT              = DIR_10 / "10k_report_numbers.csv"

# 10l — four-zone summer-minima BACI (Phase 2 of the four-zone redesign)
OUT_10L_ZONE_RESULTS        = DIR_10 / "10l_01_four_zone_summer_results.csv"
OUT_10L_PAIRWISE            = DIR_10 / "10l_02_summer_pairwise_contrasts.csv"
OUT_10L_SUMMER_MINIMA       = DIR_10 / "10l_03_c3warren_summer_minima.csv"
OUT_10L_TRAJECTORY_FIG      = DIR_10 / "10l_04_zone_summer_trajectories.jpg"
OUT_10L_FOREST_PLOT         = DIR_10 / "10l_05_summer_forest_plot.jpg"
OUT_10L_REPORT              = DIR_10 / "10l_report_numbers.csv"
# Spring-mean (MAM) four-zone siblings, v1.2.0 (2026-08-13). Same four-zone
# structure on the annual Mar-May mean; report numbers share OUT_10L_REPORT.
OUT_10L_SPRING_ZONE_RESULTS = DIR_10 / "10l_06_four_zone_spring_results.csv"
OUT_10L_SPRING_PAIRWISE     = DIR_10 / "10l_07_spring_pairwise_contrasts.csv"
OUT_10L_SPRING_MEANS        = DIR_10 / "10l_08_c3warren_spring_means.csv"
OUT_10L_SPRING_TRAJECTORY_FIG = DIR_10 / "10l_09_zone_spring_trajectories.jpg"
OUT_10L_SPRING_FOREST_PLOT  = DIR_10 / "10l_10_spring_forest_plot.jpg"

# 10m — WMC3-vs-forest-control dual-panel intervention figure
OUT_10M_ERA_STEPS           = DIR_10 / "10m_01_wmc3_baci_era_steps.csv"
OUT_10M_DUAL_FIG            = DIR_10 / "10m_02_wmc3_baci_dual.png"
OUT_10M_REPORT              = DIR_10 / "10m_report_numbers.csv"

# Script 11 — Forecasting thresholds
OUT_11_RESULTS              = DIR_11 / "11_forecast_01_results.txt"
OUT_11_TABLE6_WINTER        = DIR_11 / "11_forecast_winter_transfer_functions.csv"
OUT_11_TABLE7_SUMMER        = DIR_11 / "11_forecast_summer_transfer_functions.csv"
OUT_11_TABLE8_THRESHOLDS    = DIR_11 / "11_forecast_pflood_threshold_equations.csv"
OUT_11_PFLOOD_SUMMARY       = DIR_11 / "11_forecast_pflood_summary.csv"
# Spring MSL transfer functions — single-year prediction from antecedent
# winter peak and Oct-May P/PET (Section 5 of Script 11, paired with
# Script 26b's UKCP18 projection). Variant on previous-year MSL was tested
# and dropped 2026-05-20: R² 0.18-0.44 across the network vs 0.73-0.96 for
# the winter-peak variant retained here.
OUT_11_TABLE_SPRING         = DIR_11 / "11_forecast_spring_transfer_functions.csv"
OUT_11_SPRING_CALIBRATION   = DIR_11 / "11_forecast_02_spring_calibration.png"

# Script 11b — Spatial threshold maps
OUT_11B_SUMMER_MAP      = DIR_11B / "11b_01_summer_minima_depth.png"
OUT_11B_WINTER_MAP      = DIR_11B / "11b_02_winter_maxima_depth.png"
OUT_11B_PFLOOD_MAP      = DIR_11B / "11b_03_pflood.png"
OUT_11B_PFLOOD_PER_WELL = DIR_11B / "11b_03_pflood_per_well.csv"
OUT_11B_FLOOD_FREQ      = DIR_11B / "11b_04_flood_frequency.png"
OUT_11B_TABLE10         = DIR_11B / "11b_05_table10_pflood_spreadsheet.csv"
OUT_11B_FORECASTER_HTML = DIR_11B / "forecaster.html"

# The forecast-engine feed for the Well Logger app. Written by
# utils/forecaster_engine.py from 11b's DATA bundle, hash-gated so a no-op run
# writes nothing. It lands in living/ rather than outputs/ deliberately: it is
# consumed live from raw.githubusercontent by a separate app, alongside the
# other living feeds, and is not a pipeline output any downstream script reads.
LIVING_FORECASTER_ENGINE = ROOT_DIR / "living" / "forecaster_engine.json"

# Script 11c — P_flood achievability categorical map (Phase 3, step 12b)
OUT_11C_ACHIEVABILITY_MAP    = DIR_11B / "11c_pflood_achievability.png"
OUT_11C_PER_WELL             = DIR_11B / "11c_pflood_achievability_per_well.csv"
OUT_11C_RESULTS_MEMO         = DIR_11B / "11c_pflood_achievability_results.md"
SRC_FORECASTER_TEMPLATE = SRC_DIR / "forecaster_template.html"

# Script 14 — Climate projections
OUT_14_CLIMATE_SUMMER     = DIR_14 / "14_climate_trajectory_summer.png"
OUT_14_CLIMATE_WINTER     = DIR_14 / "14_climate_trajectory_winter_flooding.png"
OUT_14_CLIMATE_STACKED    = DIR_14 / "14_climate_trajectory_stacked.png"
OUT_14_CLIMATE_SPRING     = DIR_14 / "14_climate_trajectory_spring.png"  # v1.4.1
OUT_14_SUMMER_TREND_CSV   = DIR_14 / "14_summer_trend_stats.csv"
OUT_14_WINTER_TREND_CSV   = DIR_14 / "14_winter_trend_stats.csv"
OUT_14_SPRING_TREND_CSV   = DIR_14 / "14_spring_trend_stats.csv"  # v1.4.0 (MAM centroid trend)
OUT_14_ANNUAL_EXTREMES    = DIR_14 / "14_annual_extremes.csv"
OUT_14_WINTER_EXCEED      = DIR_14 / "14_winter_exceedance.csv"
OUT_14_SEASONAL_SCATTER   = DIR_14 / "14_seasonal_extremes_scatter.html"

# Script 14b — Bootstrap year-of-crossing diagnostic (shares DIR_14)
OUT_14B_CROSSING_CSV      = DIR_14 / "14b_year_of_crossing.csv"
OUT_14B_CROSSING_FIG      = DIR_14 / "14b_year_of_crossing.png"
OUT_14B_RESULTS_MEMO      = DIR_14 / "14b_year_of_crossing_results.md"

# Script 15 — Depth-dependent PET
OUT_15_LAMBDA_PROFILE   = DIR_15 / "15_01_lambda_profile.png"
OUT_15_FIT_COMPARISON   = DIR_15 / "15_02_fit_comparison.png"
OUT_15_BENCHMARK_TABLE  = DIR_15 / "15_03_benchmark_table.csv"
OUT_15_BEST_PARAMS      = DIR_15 / "15_04_best_params.csv"

# Script 12 — Figure: site overview
OUT_12_DEM_OVERVIEW         = DIR_12 / "12_01_dem_site_overview.png"
# The northern break in slope (D-099). A SEPARATE figure, not an overlay on
# 12_01: that PNG is report Figure 1 and altering a published figure is Martin's
# call, not a side effect of adding a measurement.
OUT_12_BREAK_IN_SLOPE       = DIR_12 / "12_02_break_in_slope.csv"
OUT_12_BREAK_FIG            = DIR_12 / "12_02_break_in_slope.png"
OUT_12_REPORT_NUMBERS       = DIR_12 / "12_report_numbers.csv"

# Script 13 — Figure: experimental design
OUT_13_EXPERIMENTAL_MAP     = DIR_13 / "13_01_experimental_setup_map.png"

# Script 02 — additional outputs
OUT_02_CLUSTER_HYDRO_WB     = DIR_02 / "02_03_cluster_hydrographs_wb.png"
OUT_02_SPAGHETTI            = DIR_02 / "02_03b_cluster_spaghetti.png"

# Script 16 — Water balance
DIR_01_CLIMATE              = DIR_00          # climate summary shares DIR_00
OUT_16_TABLE                = DIR_16 / "16_water_bal_table.csv"
OUT_16_VOL_TABLE            = DIR_16 / "16_water_bal_vol_table.csv"
OUT_16_BAR_LAY              = DIR_16 / "16_water_bal_bar_lay.png"
OUT_16_BAR_MS               = DIR_16 / "16_water_bal_bar_ms.png"
# (removed 2026-05-17: OUT_16_VOL_MS, OUT_16_VOL_LAY, OUT_16_VOL_WTF_TABLE,
#  OUT_16_VOL_WTF_MS, OUT_16_VOL_WTF_LAY — orphan constants from an earlier
#  Script 16 revision; never imported or consumed.  Doc-sweep S.11 Item D.)

# Script 17 — WTF specific yield
OUT_17_SY_TABLE             = DIR_17 / "17_wtf_01_sy_estimates.csv"
OUT_17_REGRESSION           = DIR_17 / "17_wtf_02_regression.png"
OUT_17_BOXPLOT              = DIR_17 / "17_wtf_03_event_boxplot.png"
OUT_17_SUMMARY              = DIR_17 / "17_wtf_04_summary.txt"
OUT_17_RAPID_EVENTS         = DIR_17 / "17_wtf_05_rapid_events.png"
# INT_WTF_WELL_SY (outputs/17_wtf_well_sy.csv) RETIRED 2026-08-19, D-038.
# Script 18 wrote the same well_results frame to two paths; the "17_" prefix
# named a script that never produced it. All consumers now read
# OUT_18_WELL_SY_TABLE. Removed rather than aliased so a stale importer fails
# loudly.

# Script 30 — C4 drainage identifiability diagnostic (Phase 14, opt-in).
# Supersedes the retired 30_c4_constrained_fit.py (see Script 30 v2.1.0);
# that script's archived outputs remain committed in
# outputs/30_c4_constrained_fit/ as the reported-only triangulation source
# (report §4.2.2) but are produced by no live script.
OUT_30_C4_IDENTIFIABILITY   = DIR_30 / "30_c4_identifiability_by_cluster.csv"
OUT_30_C4_PERWELL           = DIR_30 / "30_c4_perwell_beta3.csv"
OUT_30_C4_REPORT_NUMBERS    = DIR_30 / "30_c4_report_numbers.csv"
# C4 centroid with and without the ridge-flank wells the displacement model does
# not resolve (Script 30 v2.2.0). REPORTED SENSITIVITY ONLY — the canonical C4
# coefficients remain those in OUT_03_MECHANISTIC_TABLE, fitted on all nine
# members. Nothing downstream reads this file.
OUT_30_C4_CENTROID_SENS     = DIR_30 / "30_c4_centroid_sensitivity.csv"
OUT_30_C4_FIG               = DIR_30 / "30_c4_drainage_identifiability.png"

# Script 32 — differential water-table movement (standalone figure; report Fig 59)
DIR_32 = OUT_DIR / "32_differential_movement"
OUT_32_PER_WELL             = DIR_32 / "32_differential_movement_per_well.csv"
OUT_32_SITE_MEAN_TREND      = DIR_32 / "32_site_mean_trend.csv"
OUT_32_FIG_PRIMARY          = DIR_32 / "32_differential_movement_2011_2025.png"
OUT_32_FIG_ROBUST           = DIR_32 / "32_differential_movement_2005_2025.png"
OUT_32_RESULTS              = DIR_32 / "32_results.txt"

# Script 33 — climate-swing amplification + dry-year spring depth (standalone figures; Fig 60)
DIR_33 = OUT_DIR / "33_envelope_amplification"
OUT_33_PER_WELL             = DIR_33 / "33_envelope_per_well.csv"
OUT_33_FIG_AMP              = DIR_33 / "33_amplification_field.png"
OUT_33_FIG_DRY_SPRING       = DIR_33 / "33_dry_spring_depth.png"
OUT_33_RESULTS              = DIR_33 / "33_results.txt"
# Recent (extended-network) window panels — separate files, canonical handles unchanged.
OUT_33_PER_WELL_RECENT      = DIR_33 / "33_envelope_per_well_recent.csv"
OUT_33_FIG_AMP_RECENT       = DIR_33 / "33_amplification_field_recent.png"
OUT_33_FIG_DRY_SPRING_RECENT = DIR_33 / "33_dry_spring_depth_recent.png"

# --- Script 35: per-well climate-sensitivity coefficient -------------------------
DIR_35 = OUT_DIR / "35_amplification_metric"
OUT_35_PER_WELL = DIR_35 / "35_per_well_amplification.csv"
OUT_35_FIG_CALIB = DIR_35 / "35_ssm_calibration.png"
OUT_35_FIG_MARKERS = DIR_35 / "35_coefficient_markers.png"
OUT_35_RESULTS = DIR_35 / "35_results.txt"

# Script 36 — absolute climate-removed per-well secular trend map (Phase 15)
DIR_36 = OUT_DIR / "36_absolute_climate_trend"
DIR_36.mkdir(parents=True, exist_ok=True)
OUT_36_PER_WELL             = DIR_36 / "36_absolute_climate_trend_per_well.csv"
OUT_36_FIG_PRIMARY          = DIR_36 / "36_absolute_climate_trend_2005_2025.png"
OUT_36_FIG_ROBUST           = DIR_36 / "36_absolute_climate_trend_2011_2025.png"
OUT_36_RESULTS              = DIR_36 / "36_results.txt"

# Script 37 — driver-change map validation: predicted vs observed (Phase 15)
DIR_37 = OUT_DIR / "37_driver_validation"
DIR_37.mkdir(parents=True, exist_ok=True)
OUT_37_PER_WELL          = DIR_37 / "37_driver_validation_per_well.csv"
OUT_37_SCATTER           = DIR_37 / "37_predicted_vs_observed.png"
OUT_37_RESIDUAL_MAP      = DIR_37 / "37_residual_map.png"
OUT_37_RESULTS           = DIR_37 / "37_results.txt"
# v3.0.0 (2026-07-06) — per-driver scale-factor regression
OUT_37_SCALE_FACTORS     = DIR_37 / "37_scale_factors_by_window.csv"
OUT_37_DELTA0_TRAJECTORY = DIR_37 / "37_implied_delta0_trajectory.png"

# Script 37b — Part B comparative driver footing (forest · scrape · coast)
DIR_37B = OUT_DIR / "37b_driver_footing"
DIR_37B.mkdir(parents=True, exist_ok=True)
OUT_37B_COMPARISON = DIR_37B / "37b_driver_footing.csv"
OUT_37B_FIGURE     = DIR_37B / "37b_driver_footing.png"
OUT_37B_RESULTS    = DIR_37B / "37b_results.txt"

# Script 34 — MSL5 two-window sensitivity (standalone demonstration figure; §5.7.5)
DIR_34 = OUT_DIR / "34_window_sensitivity"
OUT_34_MATRIX               = DIR_34 / "34_window_matrix.csv"
OUT_34_RESULTS              = DIR_34 / "34_results.txt"
OUT_34_FIG                  = DIR_34 / "34_window_sensitivity.png"

# Script 38 — coast-to-inland MAM transect (observational delta_0 diagnostic).
# Opt-in diagnostic tier (Phase 16, wired into run_analysis.py 2026-07-08;
# runs with --with-supplementary or the menu option 1 prompt — see
# pipeline_manifest.json for its current step index). Reads committed
# pipeline intermediates only (01_wells_clean_maod.csv, 01_locations.csv,
# 25_01_panel_fit_parameters.csv); writes nothing consumed downstream.
DIR_38 = OUT_DIR / "38_coastal_transect"
DIR_38.mkdir(parents=True, exist_ok=True)
OUT_38_CSV         = DIR_38 / "38_transect.csv"
OUT_38_FIG_PROFILE = DIR_38 / "38_transect_profile.jpg"
OUT_38_FIG_DIFF    = DIR_38 / "38_coast_inland_difference.jpg"
OUT_38_RESULTS     = DIR_38 / "38_results.txt"

# Script 24b — cluster-stratified residual climatology (supplementary diagnostic)
DIR_24B = OUT_DIR / "24b_residual_climatology"
OUT_24B_CLUSTER_CLIMATOLOGY = DIR_24B / "24b_01_cluster_climatology.csv"
OUT_24B_WINTER_MINUS_SUMMER = DIR_24B / "24b_02_peak_winter_minus_summer.csv"
OUT_24B_PER_WELL_CONTRAST   = DIR_24B / "24b_03_per_well_winter_minus_summer.csv"
OUT_24B_CLIMATOLOGY_FIG     = DIR_24B / "24b_04_cluster_climatology.png"
OUT_24B_SUMMARY             = DIR_24B / "24b_05_interpretation.txt"

# Script 31 / 31b — independent k=5 cluster validation (supplementary diagnostic).
# 31 and 31b share this directory; 31b writes the 31b_* products into it.
DIR_31 = OUT_DIR / "31_cluster_validation"
OUT_31_VALIDATION_SUMMARY   = DIR_31 / "31_validation_summary.csv"
OUT_31_METHOD_ROBUSTNESS    = DIR_31 / "31_method_robustness_ari.csv"
OUT_31_FOREST_CONFUSION     = DIR_31 / "31_forest_confusion.csv"
OUT_31_FOREST_BORDERLINE    = DIR_31 / "31_forest_borderline.csv"
OUT_31_PANEL_FIG            = DIR_31 / "31_cluster_validation_panel.png"
OUT_31B_SEPARATION_CSV      = DIR_31 / "31b_separation_vs_recoverability.csv"
OUT_31B_SEPARATION_FIG      = DIR_31 / "31b_separation_vs_recoverability.png"

# Script 18 — WTF spatial
OUT_18_WELL_SY_TABLE        = DIR_18 / "18_wtf_01_well_sy_estimates.csv"
OUT_18_SY_MAP               = DIR_18 / "18_wtf_02_spatial_sy_map.png"
OUT_18_SY_CONTOUR           = DIR_18 / "18_wtf_03_sy_contour.png"
OUT_18_SY_CONTOUR_EXT       = DIR_18 / "18_wtf_04_sy_contour_extended.png"
OUT_18_HALFLIFE_MAP         = DIR_18 / "18_wtf_05_halflife_map.png"
OUT_18_STORAGE_DRAINAGE_INDEX_CSV = DIR_18 / "18_wtf_05_storage_drainage_index.csv"
OUT_18_AQUIFER_SYNTHESIS    = DIR_18 / "18_wtf_06_aquifer_diagnostic_synthesis.png"
OUT_18_SY_SPATIAL_TRENDS    = DIR_18 / "18_wtf_07_sy_spatial_trends.csv"  # open-dune Sy plane + within-forest Sy correlations
OUT_18_REPORT_NUMBERS       = DIR_18 / "18_report_numbers.csv"        # §4.9.3 half-life / 1/β₃ stats

# Script 19 — Spatial groundwater analysis
OUT_19_THICKNESS_MAP  = DIR_19 / "19_aquifer_thickness.jpg"
OUT_19_HEAD_MEAN_MAP  = DIR_19 / "19_head_mean_map.jpg"
OUT_19_HEAD_WINTER    = DIR_19 / "19_head_surface_winter.jpg"
OUT_19_HEAD_SUMMER    = DIR_19 / "19_head_surface_summer.jpg"
OUT_19_BETA1          = DIR_19 / "19_beta1_field.jpg"
OUT_19_BETA2          = DIR_19 / "19_beta2_field.jpg"
OUT_19_BETA3          = DIR_19 / "19_beta3_field.jpg"
OUT_19_WB_RECHARGE    = DIR_19 / "19_wb_recharge.jpg"
OUT_19_WB_ET          = DIR_19 / "19_wb_et.jpg"
OUT_19_WB_DRAINAGE    = DIR_19 / "19_wb_drainage.jpg"
OUT_19_WB_LATERAL     = DIR_19 / "19_wb_lateral.jpg"
OUT_19_FLUX_MAP       = DIR_19 / "19_lateral_flux.jpg"
OUT_19_RESIDUAL_COMP  = DIR_19 / "19_residual_comparison.jpg"
OUT_19_STORAGE_MAP    = DIR_19 / "19_storage_change.jpg"
OUT_19_DEPTH_SUMMER   = DIR_19 / "19_depth_to_watertable.jpg"
OUT_19_FLOOD_FREQ     = DIR_19 / "19_flood_frequency.jpg"
OUT_19_WINTER_FLOOD   = DIR_19 / "19_winter_flooding.jpg"
OUT_19_THICKNESS_CSV  = DIR_19 / "19_thickness_surface.csv"
OUT_19_HEAD_MEAN_CSV  = DIR_19 / "19_head_surface_mean.csv"
OUT_19_WB_SUMMARY_CSV = DIR_19 / "19_water_balance_summary.csv"
# Scenario-viewer per-cluster Δh / ΔMSL5 summary table, written by
# compute_scenario_summary() (the same DIR_19 / "19_scenario_summary.csv"
# the script builds locally). Defined here 2026-05-27 so Script 26c can
# reference it canonically as paths.OUT_19_SCENARIO_SUMMARY.
OUT_19_SCENARIO_SUMMARY = DIR_19 / "19_scenario_summary.csv"
# Legacy aliases for file-store script compatibility
OUT_19_HEAD_SEASONAL  = OUT_19_HEAD_WINTER
OUT_19_BETA_FIELDS    = OUT_19_BETA1
OUT_19_WATER_BALANCE  = OUT_19_WB_RECHARGE
OUT_19_DEPTH_TO_WT    = OUT_19_DEPTH_SUMMER

# Script 20 — Spatial figures (paper)
OUT_20_HEAD_STREAMS         = DIR_20 / "20_head_surface_streams.png"
OUT_20_RESIDUAL_D8          = DIR_20 / "20_residual_d8_comparison.png"
OUT_20_RESIDUAL_SSM         = DIR_20 / "20_residual_ssm.png"
OUT_20_SLOPE                = DIR_20 / "20_slope_gradient.png"
OUT_20_DRAWDOWN             = DIR_20 / "20_drawdown_propagation.png"
OUT_20_DRAWDOWN_NOHEAD      = DIR_20 / "20_drawdown_propagation_nohead.png"
OUT_20_DRAWDOWN_PERWELL     = DIR_20 / "20_drawdown_perwell.csv"      # per-well modelled drawdown dd_mm + dist_forest
OUT_20_REPORT_NUMBERS       = DIR_20 / "20_report_numbers.csv"        # §4.9 cited drawdown stats (λ + key wells)
OUT_20_RESIDUAL_PERWELL     = DIR_20 / "20_residual_perwell.csv"      # Fig 56 per-well SSM water-balance residual α
OUT_20_RESIDUAL_REPORT_NUMBERS = DIR_20 / "20_residual_report_numbers.csv"  # Fig 56 cited residual stats
OUT_20_MSL5_CHANGE_PERWELL  = DIR_20 / "20_msl5_change_perwell.csv"   # Fig 54 per-well MSL5 change (below-ground, raw)
OUT_20_MSL5_REPORT_NUMBERS  = DIR_20 / "20_msl5_report_numbers.csv"   # Fig 54 cited MSL5-change stats
OUT_20_COASTAL_EROSION      = DIR_20 / "20_coastal_erosion.png"
OUT_20_SLR_RESPONSE         = DIR_20 / "20_slr_response.png"
OUT_20_COASTAL_NET          = DIR_20 / "20_coastal_net_effect.png"
OUT_20_SCRAPE_DRAWDOWN      = DIR_20 / "20_scrape_drawdown.png"
OUT_20_SCRAPE_DRAWDOWN_NOHEAD = DIR_20 / "20_scrape_drawdown_nohead.png"
# Per-well scrape drawdown, the superposed-source field of plot_scrape_drawdown().
# Written so §4.9.6's contour claims can be checked against a committed output;
# the field had no CSV of any kind before 2026-08-20.
OUT_20_SCRAPE_DRAWDOWN_PERWELL = DIR_20 / "20_scrape_drawdown_perwell.csv"
OUT_20_CLEARFELL_BASELINE_DRAWDOWN = DIR_20 / "20_clearfell_baseline_drawdown.png"
OUT_20_PUBLIC_PANEL         = DIR_20 / "20_public_drivers_panel.png"
OUT_20_NET_STATE_MAP        = DIR_20 / "20_net_state_map.png"
OUT_20_DRIVER_CHANGE        = DIR_20 / "20_driver_change_2005_2025.png"
OUT_20_DRIVER_CHANGE_20YR   = DIR_20 / "20_driver_change_20yr.png"       # Script 20 v1.32.0 — 20-yr SymLogNorm variant
OUT_20_CLEARFELL_GAIN       = DIR_20 / "20_clearfell_gain.png"
OUT_20_OBSERVED_CHANGE      = DIR_20 / "20_observed_change_2012_2026.png"
OUT_20_MSL5_CHANGE          = DIR_20 / "20_msl5_change_2017_2023.png"

# Script 21 — Forestry scenarios
OUT_21_HYDROGRAPH        = DIR_21 / "21_forestry_01_hydrograph.png"
OUT_21_HYDROGRAPH_CSV    = DIR_21 / "21_forestry_01_hydrograph.csv"
OUT_21_DISTRIBUTIONS     = DIR_21 / "21_forestry_02_distributions.png"
OUT_21_DISTRIBUTIONS_CSV = DIR_21 / "21_forestry_02_distributions_means.csv"
OUT_21_SCRAPING          = DIR_21 / "21_forestry_03_scraping_eras.png"
OUT_21_SCRAPING_CSV      = DIR_21 / "21_forestry_03_scraping_era_means.csv"
OUT_21_BACI_VIOLIN       = DIR_21 / "21_forestry_04_baci_zone_violin.png"
OUT_21_BACI_CSV          = DIR_21 / "21_forestry_04_baci_zone_means.csv"
OUT_21_SCENARIO_COMPARE  = DIR_21 / "21_forestry_05_scenario_comparison.jpg"
OUT_21_SCENARIO_CSV      = DIR_21 / "21_forestry_05_scenario_comparison.csv"
OUT_21_SUMMER_SCENARIO_CSV = DIR_21 / "21_forestry_06_summer_scenario.csv"

# Script 22 — SSM residuals and lag analysis (ridge-subsidy mechanistic test)
INT_22_RESIDUALS_WIDE    = OUT_DIR / "22_residuals_wide.csv"
INT_22_FITS_TABLE        = OUT_DIR / "22_model_b_fits.csv"
OUT_22_AR1_HIST          = DIR_22 / "22_01_ar1_histogram.png"
OUT_22_AR1_MAP           = DIR_22 / "22_02_ar1_spatial_map.png"
OUT_22_ALPHA_PHI_SCATTER = DIR_22 / "22_03_alpha_phi_scatter.png"
OUT_22_EXAMPLE_SERIES    = DIR_22 / "22_04_example_residuals_by_cluster.png"
INT_22_SSM_RESID_INFERENCE = DIR_22 / "22_05_ssm_residual_autocorrelation.csv"
INT_22_SSM_CLUSTER_INFERENCE = DIR_22 / "22_06_ssm_cluster_mean_inference.csv"

# Script 23 — Ridge-recharge lag hypothesis test
INT_23_RESIDUALS_WIDE    = OUT_DIR / "23_residuals_extended_wide.csv"
INT_23_FITS_TABLE        = OUT_DIR / "23_ridge_lag_fits.csv"
OUT_23_CCF_HEADLINE      = DIR_23 / "23_01_ccf_headline_ridge_wells.png"
OUT_23_LAG_VS_DISTANCE   = DIR_23 / "23_02_peak_lag_vs_ridge_distance.png"
OUT_23_LAG_MAP           = DIR_23 / "23_03_peak_lag_spatial_map.png"
OUT_23_BETAS_BY_CLUSTER  = DIR_23 / "23_04_b10_b11_by_cluster.png"
OUT_23_TEST_SUMMARY      = DIR_23 / "23_05_hypothesis_test_summary.txt"

# Script 24 — Seasonal residual diagnostic
INT_24_CLIMATOLOGY_TABLE  = OUT_DIR / "24_residual_climatology.csv"
OUT_24_CLIMATOLOGY_PANELS = DIR_24 / "24_01_climatology_panels_by_cluster.png"
OUT_24_AMPLITUDE_MAP      = DIR_24 / "24_02_seasonal_amplitude_map.png"
OUT_24_SUN_CORR_SCATTER   = DIR_24 / "24_03_sun_residual_correlation.png"
OUT_24_PHASE_BARPLOT      = DIR_24 / "24_04_phase_by_cluster.png"
OUT_24_SUMMARY            = DIR_24 / "24_05_diagnostic_summary.txt"

# Script 25 — Coastal-retreat gradient analysis (Phase 12)
OUT_25_FIT_PARAMETERS     = DIR_25 / "25_01_panel_fit_parameters.csv"
OUT_25_PER_WELL_SLOPES    = DIR_25 / "25_02_per_well_summer_min_slopes.csv"
OUT_25_CLUSTER_PARTITION  = DIR_25 / "25_03_cluster_partition.csv"
OUT_25_BACI_CORROBORATION = DIR_25 / "25_04_baci_corroboration.csv"
# Per-control-well breakdown of the rows in 25_04: every control tier's
# members carried through the same comparison individually, so a reader can
# judge how much of a tier verdict rests on the tier mean.
OUT_25_BACI_TIER_SPREAD   = DIR_25 / "25_04b_baci_corroboration_spread.csv"
OUT_25_FIT_DIAGNOSTIC     = DIR_25 / "25_05_fit_diagnostic.jpg"
OUT_25_BACI_CHART         = DIR_25 / "25_06_baci_corroboration_chart.jpg"
OUT_25_CLUSTER_DECOMP_FIG = DIR_25 / "25_07_cluster_decomposition.png"
OUT_25_REPORT_NUMBERS     = DIR_25 / "25_report_numbers.csv"
# Spring-mean (MAM) siblings + summer-vs-spring comparison, v1.5.0 (2026-08-13).
# The panel fit / gradient is all-season (metric-independent, the headline); the
# spring branch reuses it and differs only in per-well metric and the Script 14
# observed-centroid CSV. 25_04 is metric-independent and is NOT re-emitted.
OUT_25_PER_WELL_SLOPES_SPRING   = DIR_25 / "25_02_per_well_spring_mean_slopes.csv"
OUT_25_CLUSTER_PARTITION_SPRING = DIR_25 / "25_03_cluster_partition_spring.csv"
OUT_25_FIT_DIAGNOSTIC_SPRING    = DIR_25 / "25_05_fit_diagnostic_spring.jpg"
OUT_25_CLUSTER_DECOMP_FIG_SPRING = DIR_25 / "25_07_cluster_decomposition_spring.png"
OUT_25_SPRING_VS_SUMMER_CSV     = DIR_25 / "25_08_spring_vs_summer_comparison.csv"
OUT_25_SPRING_VS_SUMMER_FIG     = DIR_25 / "25_08_spring_vs_summer_comparison.png"
OUT_25_SEASON_INTERACTION       = DIR_25 / "25_09_season_interaction_test.csv"
# Cluster-attribution rebuild (Script 25 v1.6.0): the composition diagnostic
# that explains the far-field background as a record-length artefact, and the
# matched-window refit, which is REPORTED ONLY and is not adopted anywhere.
OUT_25_RECORD_LENGTH_COMPOSITION        = DIR_25 / "25_10_record_length_composition.csv"
OUT_25_RECORD_LENGTH_COMPOSITION_SPRING = DIR_25 / "25_10_record_length_composition_spring.csv"
OUT_25_MATCHED_WINDOW_SENS              = DIR_25 / "25_11_matched_window_sensitivity.csv"
OUT_25_WINDOW_SWEEP                     = DIR_25 / "25_12_window_sweep.csv"
OUT_25_WINDOW_SWEEP_FIG                 = DIR_25 / "25_12_window_sweep.png"
# Fixed-length rolling-window sweep (Script 25 v1.13.0). 25_12 moves the window
# start with the end pinned, so position and length are confounded; 25_13 holds
# the length fixed and slides the whole window, at each length in
# config.ROLLING_WINDOW_YEARS.
OUT_25_ROLLING_WINDOW                   = DIR_25 / "25_13_rolling_window.csv"
OUT_25_ROLLING_WINDOW_FIG               = DIR_25 / "25_13_rolling_window.png"

# 25_14 — whether the fitted coastal gradient can be applied to individual wells
# as a correction: BACI-tier membership of the fit panel, the dispersion of
# per-well trend about the fitted profile, and the differential the profile
# predicts between the impact zone and each control tier. Emitted per metric,
# because the per-well slopes it reads are a seasonal quantity.
OUT_25_CORRECTION_DIAGNOSTIC            = DIR_25 / "25_14_correction_diagnostic.csv"
OUT_25_CORRECTION_DIAGNOSTIC_SPRING     = DIR_25 / "25_14_correction_diagnostic_spring.csv"


# --- Script 39: SSM hindcast against the 1989-96 CCW record (standalone) -------
# The CCW block is a RAW input: no pipeline step produces it. Script 39 is the
# documented exception, in the same class as Scripts 09/10 for the BACI and
# Script 24 for sunshine hours.
CCW_DEPTHS   = DATA_DIR / "ccw_1989_1996_depths.csv"
CCW_CODE_MAP = DATA_DIR / "ccw_1989_1996_code_map.csv"
# Canopy state in 1989 and felling year per well, from site history. Optional:
# Script 39 emits blank columns without it. The modern in_forest flag cannot
# stand in for this — several of these wells were felled between the two epochs.
CANOPY_HISTORY = DATA_DIR / "canopy_history.csv"

DIR_39 = OUT_DIR / "39_ccw_hindcast"
DIR_39.mkdir(parents=True, exist_ok=True)
OUT_39_PER_WELL           = DIR_39 / "39_01_hindcast_per_well.csv"
OUT_39_SERIES             = DIR_39 / "39_02_hindcast_series.csv"
OUT_39_BETA1_SENSITIVITY  = DIR_39 / "39_03_beta1_sensitivity.csv"
OUT_39_FIG                = DIR_39 / "39_04_hindcast.png"
OUT_39_FULL_SITE          = DIR_39 / "39_05_full_hindcast_site.csv"
OUT_39_FULL_DECADAL       = DIR_39 / "39_06_full_hindcast_decadal.csv"
OUT_39_FULL_FIG           = DIR_39 / "39_07_full_hindcast.png"

# --- Script 40 — shoreline-retreat measurement ---------------------------------
DIR_40 = OUT_DIR / "40_shoreline_retreat"
DIR_40.mkdir(parents=True, exist_ok=True)
OUT_40_EPOCH_SERIES    = DIR_40 / "40_01_epoch_series.csv"
OUT_40_NORMALS         = DIR_40 / "40_02_normals.csv"
OUT_40_CONTROL         = DIR_40 / "40_03_control.csv"
OUT_40_GENERALISATION  = DIR_40 / "40_04_generalisation.csv"
OUT_40_DTM_PROFILE     = DIR_40 / "40_05_dtm_profile.csv"
OUT_40_SENSITIVITY     = DIR_40 / "40_06_coastal_sensitivity.csv"
# The storm-pair measurement. NOT an epoch interval and deliberately not in the
# epoch series file: an 0.55-year displacement sitting in a table of rates is an
# invitation to divide it by its interval, which is the one thing this
# measurement must never carry (D-098). Numbered 07 because 05 and 06 are taken;
# the spec called it 40_05 before those existed.
OUT_40_STORM_PAIR      = DIR_40 / "40_07_storm_pair.csv"
OUT_40_REPORT_NUMBERS  = DIR_40 / "40_report_numbers.csv"

# ── Script 41 — canopy and forest cover from the dated aerial series ──────────
# The IMAGERY IS NOT IN THE REPOSITORY BY DEFAULT. It is screen capture of a
# licensed basemap, and D-081 already settled the shape of that question for the
# historic OS scan: the source stays out, the attribution travels with the
# derived product. AERIAL_DIR is therefore a location, not a promise — Script 41
# skips with a notice when it is empty, exactly as the pipeline skips when any
# optional input is absent, so a clone without the imagery still runs.
AERIAL_DIR      = DATA_GEO_DIR
AERIAL_MANIFEST = AERIAL_DIR / "aerial_manifest.csv"

DIR_41 = OUT_DIR / "41_canopy_cover"
DIR_41.mkdir(parents=True, exist_ok=True)
OUT_41_INDEX          = DIR_41 / "41_01_canopy_index.csv"
OUT_41_CHANGE         = DIR_41 / "41_02_change_events.csv"
OUT_41_REGISTRATION   = DIR_41 / "41_03_registration.csv"
OUT_41_SERIES_FIG     = DIR_41 / "41_04_canopy_series.png"
OUT_41_REPORT_NUMBERS = DIR_41 / "41_report_numbers.csv"
OUT_40_FIG             = DIR_40 / "40_01_alongshore_profile.png"

# Coastline epochs. coast1899.kml carries TWO placemarks and labels neither;
# Script 40 identifies them by which reproduces the D-060 baseline rather than
# trusting index order, so a re-export that reorders them cannot silently swap
# the high-water line for the dune edge.
# The measurement series, re-digitised 2026-08-29 in ONE sitting by one operator
# at four epochs. It replaced the 2026-08-28 series after the new 1/1/2006 line -
# the same imagery date traced twice - showed digitising repeatability of 1.71 m
# median, and sampling every epoch on one set of normals localised the old
# series' inflated recent rate to a single displaced line (D-087).
DATA_KML_COAST_1899    = data_geo("coast1899.kml")
DATA_KML_COAST_2006    = data_geo("coast2006.kml")
DATA_KML_COAST_2017    = data_geo("coast2017.kml")
DATA_KML_COAST_2021    = data_geo("coast2021.kml")
DATA_KML_COAST_2026    = data_geo("coast2026.kml")
# STORM-PAIR frames, NOT epochs. Two shorelines bracketing the 2019/20 winter
# storm season, digitised from imagery of 11/9/2019 and 31/3/2020. They are
# deliberately absent from Script 40's EPOCHS and INTERVALS: a 0.55-year interval
# in the epoch series would enter the rate series and shift the common-extent
# band that every committed number is measured on. Named for their imagery dates
# rather than for a storm - the interval spans Brendan, Ciara AND Dennis and
# cannot separate them, so naming it for one would be a false attribution
# (D-098). Nothing globs data/geo/coast*.kml, so the coast prefix is safe;
# checked before the rename.
DATA_KML_COAST_2019_09_11 = data_geo("coast2019-09-11.kml")
DATA_KML_COAST_2020_03_31 = data_geo("coast2020-03-31.kml")
# The CONTROL: the 1/1/2006 imagery traced a second time, BLIND - the existing
# line not loaded, so no vertex could be reused (verified: zero shared vertices
# to 1e-9 deg against either earlier tracing). Two independent tracings of one
# image differ only by digitising and registration error, so the pair measures
# exactly what the gate needs. It replaces the fixed-feature control the spec
# originally called for, which Martin ruled against holding out for. See D-089.
DATA_KML_COAST_2006_REPEAT = data_geo("coast2006B_blind.kml")
# Withdrawn 2026-08-29, retained for corroboration and audit only - NOT inputs.
# coast2020 is the one that failed: it sits 0.59 m from the 2026 line when six
# years of retreat should put it ~12 m seaward. coast2006/coast2012 sit near the
# new series and are kept because they agree, not because they are used.
DATA_KML_COAST_SUPERSEDED_DIR = DATA_GEO_DIR / "_superseded"
# The fixed-feature registration control, owed by Martin (three hard-edged
# features, opposite ends plus mid-frontage). Absent is a valid state: Script 40
# reports "control: absent" and its gate treats absent as failing.
DATA_KML_SHORE_CONTROL = data_geo("shore_control.kml")
# DCoast_2015.kml WAS HERE and is DELETED, 2026-08-29 (Martin: "we should remove
# DCoast 2015 as its not verifiable. I cant tell you what it represents"). It had
# been retained as the D-060 regression anchor; that role is gone and is not
# missed, because D-060's published 0.65 m/yr is reproduced WITHOUT it - the 1899
# dune edge against the new 2006 line gives 0.645 m/yr over 107 years, a route
# whose every input has known provenance. Script 40's regression test now uses
# that pairing. See D-087.
OUT_39_RESULTS            = DIR_39 / "39_results.txt"

# Script 26 — Van Willegen et al. (2025) 5-year MSL aggregation (Phase 13)
OUT_26_ANNUAL_PER_WELL    = DIR_26 / "26_msl_annual_per_well.csv"
OUT_26_5YR_PER_WELL       = DIR_26 / "26_msl_5yr_per_well.csv"
OUT_26_5YR_PER_CLUSTER    = DIR_26 / "26_msl_5yr_per_cluster.csv"
OUT_26_5YR_PER_CLUSTER_CENTROID = DIR_26 / "26_msl_5yr_per_cluster_centroid.csv"
OUT_26_5YR_LATEST_PER_WELL = DIR_26 / "26_msl_5yr_latest_per_well.csv"
OUT_26_TRAJECTORY         = DIR_26 / "26_msl_5yr_trajectory.png"
OUT_26_QUADRAT_WELLS      = DIR_26 / "26_msl_5yr_quadrat_wells.png"
OUT_26_MAP                = DIR_26 / "26_msl_5yr_map.png"
OUT_26_RESULTS_TXT        = DIR_26 / "26_msl_results.txt"
# Equilibrium Wetness Index (Script 26 v1.3.x) — structural steady-state spring
# level from the SSM coefficients under long-term mean climate, and the per-well
# observed-vs-predicted MSL5 comparison table.
OUT_26_EWI_PER_WELL       = DIR_26 / "26_equilibrium_wetness_index_per_well.csv"
OUT_26_EWI_MSL5_COMPARISON = DIR_26 / "26_ewi_msl5_comparison.csv"
# EbF vegetation cross-validation (v1.3.3) — generated from the documented
# external Ellenberg dataset (DATA_ELLENBERG_EXT); skipped if that file is absent.
OUT_26_EBF_COMPARISON     = DIR_26 / "26_ebf_comparison.csv"
OUT_26_EBF_SCATTER        = DIR_26 / "26_ebf_prediction_scatter.png"
# Metric diagnostics (v1.4.0) — window sensitivity of MSL5 and the precision of
# the two indices, per well and rolled up per cluster. Supplies the cited
# statistics for report §4.8.6 / §6.9 (spring autocorrelation, interannual
# amplitude, index standard errors) so none of them is computed in prose.
OUT_26_METRIC_DIAGNOSTICS = DIR_26 / "26_metric_diagnostics_per_well.csv"
OUT_26_INDEX_PRECISION    = DIR_26 / "26_index_precision_by_cluster.csv"
OUT_26_REPORT_NUMBERS     = DIR_26 / "26_report_numbers.csv"
OUT_26_METRIC_DIAG_FIG    = DIR_26 / "26_metric_diagnostics.png"
# Supplementary Table S7.1 emitter (v1.5.0). Display-formatted renderings of the
# per-well EWI reconstruction for paste into Supplementary_Material — the CSV via
# Paste Special > Unformatted text, the Markdown for review before pasting.
OUT_26_TABLE_S7_1_CSV     = DIR_26 / "26_table_s7_1_ewi_per_well.csv"
OUT_26_TABLE_S7_1_MD      = DIR_26 / "26_table_s7_1_ewi_per_well.md"

# Script 26b — Van Willegen MSL UKCP18 climate projections (Phase 13, Tool B)
# Pairs with Script 11 Section 5 (Tool A) and Script 26 (observational MSL5).
OUT_26B_PROJECTION_FIG    = DIR_26B / "26b_msl5_ukcp18_projection.png"
OUT_26B_PROJECTION_TABLE  = DIR_26B / "26b_msl5_ukcp18_projection_summary.csv"
OUT_26B_DELTA_H_PER_CLUSTER = DIR_26B / "26b_monthly_delta_h_per_cluster.csv"
OUT_26B_RESULTS_TXT       = DIR_26B / "26b_msl5_ukcp18_results.txt"
# v1.1.0 (2026-05-27) added parallel per-well-aggregation pathway. The
# centroid-fitted summary above remains canonical for Script 26c and for
# the §3.7.5 / §4.8.4 / §4.10.1 report numbers; the per-well summary is a
# secondary artefact that serves as the validation target for the
# Script 19 v2.8.0 viewer ΔMSL5 row. See 26b docstring for the rationale.
OUT_26B_PROJECTION_TABLE_PERWELL = DIR_26B / "26b_msl5_ukcp18_projection_summary_perwell.csv"

# Script 26c — MSL5 report-format figures (Phase 13, report companions)
# Re-renders the trajectory and contrast figures cited in §4.8.4 / §4.10.1
# from the canonical Script 26 / 26b / 19 outputs. Added 2026-05-27: these
# constants were referenced by 26c_msl5_report_figures.py but were missing
# from paths.py, so Script 26c could not run; defining them here fixes that.
OUT_26C_TRAJECTORY        = DIR_26C / "fig_msl5_trajectory_report.png"
OUT_26C_CONTRAST          = DIR_26C / "fig_msl5_vs_summer_min_projection.png"
OUT_26C_RESULTS_TXT       = DIR_26C / "26c_results.txt"

# Script 27 — Greyscale figure conversion (Phase 15, post-processing)
# Uses discovery-based rglob over outputs/ — no per-figure path entries needed.
# Output tree mirrors outputs/ structure under outputs_bw/.

# Script 28 — C3 detrend check (Phase 14, cluster framework diagnostics)
OUT_28_DETREND_TABLE = DIR_28 / "28_c3_detrend.csv"
OUT_28_DETREND_MEMO  = DIR_28 / "28_c3_detrend_results.md"
OUT_28_DETREND_PANEL = DIR_28 / "28_c3_detrend_panel.png"

# Script 29 — Within-C3 variance attribution (Phase 14, cluster framework diagnostics)
OUT_29_PANEL_CSV      = DIR_29 / "29_within_c3_variance.csv"
OUT_29_UNIVARIATE_R2  = DIR_29 / "29_univariate_R2.csv"
OUT_29_DROP_ONE       = DIR_29 / "29_drop_one.csv"
OUT_29_MEMO           = DIR_29 / "29_within_c3_variance_results.md"
OUT_29_PANEL_FIG      = DIR_29 / "29_within_c3_variance_panel.png"
OUT_29_REPORT_NUMBERS = DIR_29 / "29_report_numbers.csv"   # §4.9.2 C3 gradient stats (β₁/β₃/Sy vs inland)
