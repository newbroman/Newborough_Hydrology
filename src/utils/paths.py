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

from pathlib import Path

# ==========================================
# ROOT DIRECTORIES
# ==========================================
_UTILS_DIR = Path(__file__).parent
SRC_DIR = _UTILS_DIR.parent
ROOT_DIR = SRC_DIR.parent

DATA_DIR = ROOT_DIR / "data"
OUT_DIR = ROOT_DIR / "outputs"

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
DIR_07 = OUT_DIR / "07_boundary_intercept"
DIR_08 = OUT_DIR / "08_model_benchmarking"
DIR_09 = OUT_DIR / "09_scraping_intervention"
DIR_10 = OUT_DIR / "10_clearfell_baci"
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

ALL_DIRS = [
    OUT_DIR,
    DIR_00, DIR_01,
    DIR_02, DIR_03, DIR_04, DIR_05, DIR_06, DIR_07,
    DIR_08, DIR_09, DIR_10, DIR_11, DIR_11B, DIR_12, DIR_13, DIR_14,
    DIR_15, DIR_16, DIR_17, DIR_18, DIR_19, DIR_20, DIR_21, DIR_22, DIR_23, DIR_24,
]


def make_all_dirs():
    """Create all output directories if they do not already exist."""
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# ==========================================
# DATA INPUTS
# ==========================================
DATA_WELLS_RAW      = DATA_DIR / "Newborough_Cleaned_For_Model.csv"
DATA_LOCATIONS_RAW  = DATA_DIR / "Well_locations_height.csv"
DATA_CLIMATE_RAW    = DATA_DIR / "RAF_Valley_Climate.csv"
DATA_DEM            = DATA_DIR / "newborough_dem.tif"
DATA_KML_FEATURES   = DATA_DIR / "Features.kml"
DATA_KML_STREAMS    = DATA_DIR / "streams.kml"
DATA_KML_CLEARFELL  = DATA_DIR / "clearfell.kml"
# Broadleaf restock block boundary — geometry also embedded in Features.kml
# for automatic rendering via add_kml_features(); this entry retained for
# any script that loads the boundary explicitly.
KML_BROADLEAF        = DATA_DIR / "broadleaf_restock.kml"
DATA_WELL_ELEVATIONS = DATA_DIR / "Well_locations_height.csv"  # alias for script 10 transect

# ==========================================
# INTERMEDIATE FILES — outputs/ root
# (read by downstream scripts)
# ==========================================

# Script 01
INT_LOCATIONS       = OUT_DIR / "01_locations.csv"
INT_CLIMATE         = OUT_DIR / "01_climate.csv"
INT_WELLS_CLEAN     = OUT_DIR / "01_wells_clean.csv"
INT_WELLS_CLEAN_MAOD = OUT_DIR / "01_wells_clean_maod.csv"
INT_WELLS_REFERENCE = OUT_DIR / "01_wells_reference.csv"
INT_WELLS_EXTENDED  = OUT_DIR / "01_wells_extended.csv"
INT_WELL_ELEVATIONS = OUT_DIR / "01_well_elevations.csv"

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
INT_INTERCEPT_METRICS = OUT_DIR / "07_intercept_metrics.csv"

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

# Script 02 — Clustering
OUT_02_DENDROGRAM       = DIR_02 / "02_01_dendrogram.png"
OUT_02_VALIDATION       = DIR_02 / "02_02_validation_plots.png"
# Stability diagnostics (Phase 1 rebuild validation — bootstrap co-assignment,
# k-sweep, per-well stability). See 02_clustering.py run_stability_diagnostics().
OUT_02_VALIDATION_EXTENDED = DIR_02 / "02_02b_validation_k_sweep.png"
OUT_02_STABILITY_SUMMARY   = DIR_02 / "02_04_bootstrap_stability_summary.csv"
OUT_02_STABILITY_PER_WELL  = DIR_02 / "02_05_bootstrap_stability_per_well.csv"
# The following two are templates — .format(k=...) is applied at the call site
# because one file is written per bootstrap k value.
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

# Script 03 — State-space model
OUT_03_SIGNATURES          = DIR_03 / "03_01_mechanistic_signatures.png"
OUT_03_SIGNATURES_WELLMEAN = DIR_03 / "03_01b_mechanistic_signatures_wellmean.png"
OUT_03_CLUSTER_SUMMARY     = DIR_03 / "03_02_cluster_summary_table.csv"
OUT_03_MECHANISTIC_TABLE   = DIR_03 / "03_03_cluster_mechanistic_coefficients.csv"

# Script 04 — Cluster visualisations
OUT_04_ARCHITECTURE_MAP = DIR_04 / "04_01_core_architecture_map.png"

# Script 05 — Pearson affinity
OUT_05_CONFIDENCE_MAP   = DIR_05 / "05_pear_01_spatial_confidence_map.png"

# Script 06 — Pearson extended
OUT_06_AFFINITY_CHART   = DIR_06 / "06_pear_01_affinity_chart_extended.png"
OUT_06_INTEGRATION_MAP  = DIR_06 / "06_pear_02_integration_map.png"

# Script 07 — Boundary intercept
OUT_07_CEH14_SHOWDOWN       = DIR_07 / "07_intercept_01_ceh14_showdown.png"
OUT_07_CEH14_SHOWDOWN_DATA  = DIR_07 / "07_intercept_ceh14_showdown_data.csv"
OUT_07_PLUMBING_MAP         = DIR_07 / "07_intercept_02_plumbing_map.png"
OUT_07_NSE_PENALTY_MAP      = DIR_07 / "07_intercept_03_nse_penalty_map.png"
OUT_07_MAPS_MERGED_DATA     = DIR_07 / "07_intercept_maps_merged_data.csv"

# Script 08 — Model benchmarking
OUT_08_CEH19_WITH_MODEL_B   = DIR_08 / "08_lcsc_01_ceh19_with_model_b.png"
OUT_08_R2_MAP               = DIR_08 / "08_lcsc_02_r2_improvement_map.png"
OUT_08_NSE_MAP              = DIR_08 / "08_lcsc_03_nse_improvement_map.png"
OUT_08_TABLE3_SUMMARY       = DIR_08 / "08_lcsc_04_table3_benchmark_summary.csv"

# Script 09 — Scraping intervention
OUT_09_FULL_PARAMS          = DIR_09 / "09_scrape_01_full_parameters.csv"
OUT_09_BETA3_SIG            = DIR_09 / "09_scrape_02_beta3_significance.csv"
OUT_09_BACI_SHIFTS          = DIR_09 / "09_scrape_03_baci_shifts.csv"
OUT_09_NET_BENEFITS         = DIR_09 / "09_scrape_04_net_benefits.csv"
OUT_09_TABLE4_SUMMARY       = DIR_09 / "09_scrape_04b_table4_beta3_era_summary.csv"
OUT_09_TIER1_DRIFT          = DIR_09 / "09_scrape_05_tier1_background_drift.png"
OUT_09_TIER2_SIGNAL         = DIR_09 / "09_scrape_06_tier2_scraping_signal.png"
OUT_09_BETA3_CI             = DIR_09 / "09_scrape_07_beta3_confidence.png"
OUT_09_ROBUSTNESS           = DIR_09 / "09_scrape_08_ceh36_robustness.png"

# Script 10 — Clearfell BACI
OUT_10_DUAL_BACI            = DIR_10 / "10_cfell_01_dual_control_baci.png"
OUT_10_DRAINAGE_PART1       = DIR_10 / "10_cfell_02_drainage_diagnostic_part1.png"
OUT_10_DRAINAGE_PART2       = DIR_10 / "10_cfell_02_drainage_diagnostic_part2.png"
OUT_10_BETA3_SLOPES         = DIR_10 / "10_cfell_03_beta3_ols_slopes.png"
OUT_10_DRAINAGE_DATA        = DIR_10 / "10_cfell_04_diagnostic_drainage_data.csv"
OUT_10_STAT_VERIFICATION    = DIR_10 / "10_cfell_05_baci_statistical_verification.csv"
OUT_10_FULL_PARAMS          = DIR_10 / "10_cfell_06_full_parameters.csv"
OUT_10_COEFF_SLOPES         = DIR_10 / "10_cfell_07_coefficient_slopes.csv"
OUT_10_BACI_TIMESERIES      = DIR_10 / "10_cfell_08_baci_timeseries_plotdata.csv"
OUT_10_TABLE5_SUMMARY       = DIR_10 / "10_cfell_09_table5_beta3_before_after.csv"
OUT_10_TRANSECT             = DIR_10 / "10_cfell_10_clearfell_transect.png"
OUT_10_TRANSECT_CSV         = DIR_10 / "10_cfell_10_clearfell_transect_steps.csv"
OUT_10_NW10_TREND           = DIR_10 / "10_cfell_11_nw10_broadleaf_trend.csv"

# Script 11 — Forecasting thresholds
OUT_11_RESULTS              = DIR_11 / "11_forecast_01_results.txt"
OUT_11_TABLE6_WINTER        = DIR_11 / "11_forecast_winter_transfer_functions.csv"
OUT_11_TABLE7_SUMMER        = DIR_11 / "11_forecast_summer_transfer_functions.csv"
OUT_11_TABLE8_THRESHOLDS    = DIR_11 / "11_forecast_pflood_threshold_equations.csv"

# Script 11b — Spatial threshold maps
OUT_11B_SUMMER_MAP      = DIR_11B / "11b_01_summer_minima_depth.png"
OUT_11B_WINTER_MAP      = DIR_11B / "11b_02_winter_maxima_depth.png"
OUT_11B_PFLOOD_MAP      = DIR_11B / "11b_03_pflood.png"
OUT_11B_PFLOOD_PER_WELL = DIR_11B / "11b_03_pflood_per_well.csv"
OUT_11B_FLOOD_FREQ      = DIR_11B / "11b_04_flood_frequency.png"
OUT_11B_TABLE10         = DIR_11B / "11b_05_table10_pflood_spreadsheet.csv"
OUT_11B_FORECASTER_HTML = DIR_11B / "forecaster.html"
SRC_FORECASTER_TEMPLATE = SRC_DIR / "forecaster_template.html"

# Script 14 — Climate projections
OUT_14_CLIMATE_SUMMER     = DIR_14 / "14_climate_trajectory_summer.png"
OUT_14_CLIMATE_WINTER     = DIR_14 / "14_climate_trajectory_winter_flooding.png"
OUT_14_CLIMATE_STACKED    = DIR_14 / "14_climate_trajectory_stacked.png"
OUT_14_SUMMER_TREND_CSV   = DIR_14 / "14_summer_trend_stats.csv"
OUT_14_ANNUAL_EXTREMES    = DIR_14 / "14_annual_extremes.csv"
OUT_14_WINTER_EXCEED      = DIR_14 / "14_winter_exceedance.csv"
OUT_14_SEASONAL_SCATTER   = DIR_14 / "14_seasonal_extremes_scatter.html"

# Script 15 — Depth-dependent PET
OUT_15_LAMBDA_PROFILE   = DIR_15 / "15_01_lambda_profile.png"
OUT_15_FIT_COMPARISON   = DIR_15 / "15_02_fit_comparison.png"
OUT_15_BENCHMARK_TABLE  = DIR_15 / "15_03_benchmark_table.csv"
OUT_15_BEST_PARAMS      = DIR_15 / "15_04_best_params.csv"

# Script 12 — Figure: site overview
OUT_12_DEM_OVERVIEW         = DIR_12 / "12_01_dem_site_overview.png"

# Script 13 — Figure: experimental design
OUT_13_EXPERIMENTAL_MAP     = DIR_13 / "13_01_experimental_setup_map.png"

# Script 02 — additional outputs
OUT_02_CLUSTER_HYDRO_WB     = DIR_02 / "02_03_cluster_hydrographs_wb.png"

# Script 16 — Water balance
DIR_01_CLIMATE              = DIR_00          # climate summary shares DIR_00
OUT_16_TABLE                = DIR_16 / "16_water_bal_table.csv"
OUT_16_VOL_TABLE            = DIR_16 / "16_water_bal_vol_table.csv"
OUT_16_BAR_LAY              = DIR_16 / "16_water_bal_bar_lay.png"
OUT_16_BAR_MS               = DIR_16 / "16_water_bal_bar_ms.png"
OUT_16_VOL_MS               = DIR_16 / "16_water_bal_volumetric_ms.png"
OUT_16_VOL_LAY              = DIR_16 / "16_water_bal_volumetric_lay.png"
OUT_16_VOL_WTF_TABLE        = DIR_16 / "16_water_bal_vol_wtf_table3d.csv"
OUT_16_VOL_WTF_MS           = DIR_16 / "16_water_bal_volumetric_wtf_ms.png"
OUT_16_VOL_WTF_LAY          = DIR_16 / "16_water_bal_volumetric_wtf_lay.png"

# Script 17 — WTF specific yield
OUT_17_SY_TABLE             = DIR_17 / "17_wtf_01_sy_estimates.csv"
OUT_17_REGRESSION           = DIR_17 / "17_wtf_02_regression.png"
OUT_17_BOXPLOT              = DIR_17 / "17_wtf_03_event_boxplot.png"
OUT_17_SUMMARY              = DIR_17 / "17_wtf_04_summary.txt"
INT_WTF_WELL_SY             = OUT_DIR / "17_wtf_well_sy.csv"

# Script 18 — WTF spatial
OUT_18_WELL_SY_TABLE        = DIR_18 / "18_wtf_01_well_sy_estimates.csv"
OUT_18_SY_MAP               = DIR_18 / "18_wtf_02_spatial_sy_map.png"
OUT_18_SY_CONTOUR           = DIR_18 / "18_wtf_03_sy_contour.png"
OUT_18_SY_CONTOUR_EXT       = DIR_18 / "18_wtf_04_sy_contour_extended.png"

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

# Script 21 — Forestry scenarios
OUT_21_HYDROGRAPH        = DIR_21 / "21_forestry_01_hydrograph.png"
OUT_21_DISTRIBUTIONS     = DIR_21 / "21_forestry_02_distributions.png"
OUT_21_DISTRIBUTIONS_CSV = DIR_21 / "21_forestry_02_distributions_means.csv"
OUT_21_SCRAPING          = DIR_21 / "21_forestry_03_scraping_eras.png"
OUT_21_SCRAPING_CSV      = DIR_21 / "21_forestry_03_scraping_era_means.csv"
OUT_21_BACI_VIOLIN       = DIR_21 / "21_forestry_04_baci_zone_violin.png"
OUT_21_BACI_CSV          = DIR_21 / "21_forestry_04_baci_zone_means.csv"

# Script 22 — SSM residuals and lag analysis (ridge-subsidy mechanistic test)
INT_22_RESIDUALS_WIDE    = OUT_DIR / "22_residuals_wide.csv"
INT_22_FITS_TABLE        = OUT_DIR / "22_model_b_fits.csv"
OUT_22_AR1_HIST          = DIR_22 / "22_01_ar1_histogram.png"
OUT_22_AR1_MAP           = DIR_22 / "22_02_ar1_spatial_map.png"
OUT_22_ALPHA_PHI_SCATTER = DIR_22 / "22_03_alpha_phi_scatter.png"
OUT_22_EXAMPLE_SERIES    = DIR_22 / "22_04_example_residuals_by_cluster.png"

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
