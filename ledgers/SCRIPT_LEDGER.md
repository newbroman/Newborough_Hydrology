# SCRIPT_LEDGER — Newborough Warren pipeline

**Living ledger. Edit in place; do not date the filename.** One row per pipeline
script: what it consumes, what it emits, which documents describe it, and its
current code-vs-documentation status. This is the anti-drift spine — read it to
know the current state without replaying the changelog history.

- **Source of truth:** GitHub `main`, HEAD `30aed9b` (2026-08-14 09:09).
- **First populated:** 2026-08-14, from a full code scan + a code-vs-doc audit
  (see `NRG_methods_code_audit_2026-08-14.md` for the finding detail).
- **Maintenance rule:** every script change updates its row here AND drops a
  dated `CHANGELOG_delta`. The delta records *what changed*; this row records
  *what is now true*. When you touch a script, re-check its Consumes/Emits and
  reset Status to OK once the docs are reconciled.

**Status legend:** OK = docs match code · DRIFT = a document describes
behaviour/outputs/method the code no longer does (or describes it wrongly) ·
GAP = code does something material no document mentions · `-min` = minor/low
materiality · `-TR` = matches but quoted numbers are volatile (retrace to
committed CSV before publishing) · `-attr` = provenance/attribution error ·
`*` = clean but carries a low-severity note · `?` = needs a pipeline rerun to
confirm · `-orphan` = uncited but legitimately so.

**Document codes:** R8 = report Methods chapter (report8) · MS = Methods
Supplement v1_9_8 · SM = Supplementary Material v1_6 · P1 = Paper 1 · P1SI =
Paper 1 SI methods · P2 = Paper 2.

**Scanner caveats:** Consumes/Emits are AST-derived and attributed by the
`paths.py` `OUT_/INT_` convention plus write-scan. A script's own second-pass
self-reads appear under Emits, not Consumes (e.g. 03 reading `03_master_data`).
A few helper-saved figures whose path constant carries no script number may be
missing from the figs column (e.g. Script 01's coverage plates) — correct by
hand when noticed. Display/utility helpers (`gen_grid_lay.py`,
`run_09_scraping.py`, `run_10_clearfell.py`) are not numbered rows.

## Summary

66 numbered scripts. **45 OK · 21 with drift/gap findings.** The drift clusters
into: (1) prose describing a pipeline shape the code has outgrown — the
"Script-35 class" — 07, 09f, 10i, 16, 20, 30; (2) stale numbers/counts — 03, 08,
14, 20, 26; (3) wrong attribution/provenance — 00, 18, 26b, 09f→Paper1, the
Approach-B Sy conflation in MS S.12; (4) an undocumented emitted element — 37b's
common-mode component, 33's recent-window products; (5) minor stragglers — 09b,
09c, 10h, 10m, 26c step-numbers, 29's retired-τ label, 33's missing 2016 wet
year. Confirmed clean on the things most likely to have rotted: the τ=Sy/β₃
retirement (no document calls it a residence time), the MSL upstand removal
(Script 26), and Script 35 itself (the trigger case — now documented correctly).

## Ledger

| # | Script | Ver | Consumes | Emits (data) | Emits (figs) | Cited | Status |
|---|--------|-----|----------|--------------|--------------|-------|--------|
| 00 | 00_climate_summary.py | 1.4.1 | 01_climate.csv, 01_wells_clean.csv | 00_01_annual_climate_summary.csv, 00_02_well_network_summary.csv, 00_03_summer_warming_stats.csv, 00_04_climatology.csv, 00_report_numbers.csv | 00_01_climate_timeseries.png, 00_02_well_network_summary.png, 00_03_summer_warming_trend.png | MS | **DRIFT** |
| 01 | 01_data_prep.py | 1.12.0 | 06_pear_membership_audit_sitewide.csv (2nd-pass) | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 01_wells_clean_maod.csv, 01_wells_reference.csv, 01_wells_extended.csv, 01_wells_provenance.csv, 01_well_elevations.csv, 01_dry_depths.csv, 01_observation_states.csv (+more) | 01_coverage_states_*.png (helper-saved) | MS | **DRIFT?** |
| 02 | 02_clustering.py | 1.6.0 | 01_climate.csv, 01_wells_clean.csv, 01_wells_reference.csv | 02_cluster_stats.csv, 02_04_bootstrap_stability_summary.csv, 02_07_cluster_membership_k{k}.csv, 02_08_cluster_amplitude_per_well.csv, 02_09_cluster_amplitude_summary.csv, 02_report_numbers.csv | 02_01_dendrogram.png, 02_02_validation_plots.png, 02_02b_validation_k_sweep.png, 02_03_cluster_hydrographs_wb.png, 02_10_cluster_amplitude_boxplot.png | MS | **DRIFT?** |
| 03 | 03_state_space_model.py | 1.9.4 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 01_wells_clean_maod.csv, 02_08_cluster_amplitude_per_well.csv, 02_cluster_stats.csv | 03_master_data.csv, 03_regional_averages.csv, 03_regional_averages_maod.csv, 03_02_cluster_summary_table.csv, 03_03_cluster_mechanistic_coefficients.csv, 03_11_datum_confound_diagnostics.csv, 03_12_partition_vs_datum.csv | 03_01_mechanistic_signatures.png, 03_12_datum_regime.png | MS,SM | **DRIFT** |
| 04 | 04_cluster_visualisations.py | 1.0.0 | 01_locations.csv, 02_cluster_stats.csv | — | 04_01_core_architecture_map.png | MS | **OK** |
| 05 | 05_pearson_affinity.py | 1.3.1 | 01_locations.csv, 02_cluster_stats.csv | 05_pear_membership_audit.csv | 05_pear_01_spatial_confidence_map.png, 05_pear_02_affinity_chart_reference.png | MS | **OK** |
| 06 | 06_pearson_extended.py | 1.0.0 | 01_wells_extended.csv, 01_wells_reference.csv, 02_cluster_stats.csv | 06_pear_membership_audit_sitewide.csv | 06_pear_01_affinity_chart_extended.png, 06_pear_02_integration_map.png | MS | **OK** |
| 07 | 07_spatial_coefficients.py | 1.2.1 | 01_well_elevations.csv, 03_master_data.csv | 07_cluster_coeff_means.csv, 07_report_numbers.csv | (IDW surfaces, helper-saved) | MS | **DRIFT** |
| 08 | 08_model_benchmarking.py | 1.5.0 | 01_climate.csv, 01_wells_clean.csv, 02_cluster_stats.csv, 03_master_data.csv | 08_lcsc_04_table3_benchmark_summary.csv, 08_perwell_nse.csv, 08_report_numbers.csv | 08_lcsc_01_ceh6_showdown.png, 08_lcsc_02_r2_improvement_map.png, 08_lcsc_03_nse_improvement_map.png | MS | **DRIFT** |
| 09a | 09a_paired_baci.py | 2.7.3 | 01_wells_clean.csv, 03_master_data.csv | 09_scrape_01…04b_*.csv, 09_scrape_report_numbers.csv, 09_tier1_final_cusum.csv | 09_scrape_05_tier1_background_drift.png, 09_scrape_06_tier2_scraping_signal.png, 09_scrape_07_beta3_confidence.png | R8,MS,P2 | **DRIFT?** |
| 09b | 09b_scraping_propagation.py | 1.6.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 01_wells_extended.csv, 03_master_data.csv, 17_wtf_01_sy_estimates.csv | 09b_01_individual_well_baci.csv, 09b_02_centroid_summaries.csv, 09b_04_scenario_comparison.csv, 09b_05_summer_scenario_comparison.csv | 09b_03_ceh36_equilibration.jpg, 09b_04_scenario_comparison.jpg, 09b_05_summer_scenario_comparison.png | MS | **DRIFT** |
| 09c | 09c_summer_minima.py | 1.5.0 | 01_climate.csv, 03_master_data.csv | 09c_01_summer_minima.csv, 09c_02_summer_minima_shifts.csv, 09c_05_spring_means.csv, 09c_06_spring_means_shifts.csv, 09c_report_numbers.csv | 09c_03…04 + 09c_07_spring_means_climate_ctrl.png, 09c_08_spring_means_paired.png | MS,SM | **DRIFT-min** |
| 09d | 09d_scenario_comparison.py | 3.10.2 | 01_wells_clean.csv, 03_master_data.csv, 17_wtf_well_sy.csv, 20_report_numbers.csv | 09d_01_scenario_comparison.csv, 09d_02_summer_scenario_comparison.csv | 09d_01_scenario_comparison.jpg, 09d_02_summer_scenario_comparison.png | MS | **DRIFT?** |
| 09e | 09e_robustness.py | 2.1.0 | 03_master_data.csv | 09e_report_numbers.csv | (panels) | MS | **OK** |
| 09f | 09f_management_effects.py | 1.9.0 | 03_03_cluster_mechanistic_coefficients.csv, 09b_01_individual_well_baci.csv, 09d_01_scenario_comparison.csv, 10a_report_numbers.csv, 10m_report_numbers.csv, 20_report_numbers.csv, 25_01_panel_fit_parameters.csv | 09f_01_reach_profile.csv (one column per drawn curve; climate and far-field columns both retired — D-039, D-043) | 09f_management_effects.png, 09f_management_effects_public.png | R8,MS,P1 | **DRIFT** |
| 09g | 09g_mechanism_diagrams.py | 1.7.0 | 09f_01_reach_profile.csv, 25_01_panel_fit_parameters.csv, 10a/10m report_numbers | — | 09g_mechanism_grid.png/.svg, 09g_coastal_vs_climate_reach.png/.svg | R8,MS,P1 | **DRIFT?** |
| 10a | 10a_ancova_baci.py | 1.6.0 | (clearfell_common; raw BACI) | 10a_report_numbers.csv, 10a_01_ancova_comparison_table.csv | 10a_04…08 + S1–S3 | R8,MS | **DRIFT?** |
| 10b | 10b_spatial_step_maps.py | 1.6.0 | 01_well_elevations.csv, 01_wells_clean.csv, 01_wells_extended.csv, 03_master_data.csv | 10b_spatial_step_data.csv | 10b_spatial_fell_corrected.png, 10b_spatial_fell_raw.png, 10b_spatial_scrape_corrected.png, 10b_spatial_scrape_raw.png | R8,MS | **OK** |
| 10c | 10c_forest_zone_analysis.py | 1.1.0 | 06_pear_membership_audit_sitewide.csv, 07_coeff_maps_data.csv | 10c_forest_zone_correlations.csv, 10c_forest_zone_cluster_summary.csv, 10c_04_forest_zone_summary.txt | 10c_01_b1_b2_scatter.png, 10c_02_b2_elevation_regression.png, 10c_03_c4_c5_boundary_map.png | MS | **DRIFT?** |
| 10d | 10d_summer_minima.py | 1.7.0 | (BACI panels) | 10d_03_mixed_model_results.csv, 10d_report_numbers.csv, 10d_06…10 spring | — | MS,SM | **OK-TR** |
| 10e | 10e_coefficient_decomposition.py | 1.6.0 | 03_master_data.csv | 10e_01_coefficient_shifts.csv (β₂ multipliers) | 10e_03_* (report Fig 35) | MS | **OK** |
| 10f | 10f_robustness.py | 1.2.0 | (BACI) | 10f_01_ssm_residual_results.csv, 10f_02_synthetic_control_results.csv, 10f_report_numbers.csv | — | MS | **DRIFT?** |
| 10g | 10g_diagnostics.py | 1.1.0 | 03_regional_averages.csv | 10g_01_nw10_broadleaf_trend.csv, 10g_03_clearfell_transect_steps.csv, 10g_04_rolling_coefficients.csv, 10g_report_numbers.csv | 10g_02_clearfell_transect.png | MS | **OK** |
| 10h | 10h_synthetic_impact_baci.py | 1.4.1 | (donors CEH34/2/33) | (synthetic control) | — | MS | **DRIFT-min** |
| 10i | 10i_ceh34_hindcast.py | 1.1.0 | (donor regression) | 10i_01_ceh34_hindcast.csv, 10i_02_donor_regression.csv, 10i_report_numbers.csv | 10i_03_hindcast_diagnostic.png | MS | **DRIFT** |
| 10j | 10j_impact_edge_contrast.py | 1.3.0 | 10d_01_summer_minima.csv | 10j_01_monthly_contrast_results.csv, 10j_02_summer_contrast_results.csv, 10j_report_numbers.csv | 10j_03_contrast_timeseries.jpg, 10j_04_summer_minima_contrast.jpg | R8,MS | **OK** |
| 10k | 10k_four_zone_baci.py | 1.3.1 | 10j_01_monthly_contrast_results.csv | 10k_01_four_zone_results.csv, 10k_02_pairwise_contrasts.csv, 10k_03_easting_sensitivity.csv, 10k_report_numbers.csv | 10k_04…06 | MS | **DRIFT?** |
| 10l | 10l_four_zone_summer_minima.py | 1.2.0 | 10j_02_summer_contrast_results.csv | 10l_01…03 summer + 10l_06…08 spring, 10l_report_numbers.csv | 10l_04,05,09,10 | MS,SM | **OK** |
| 10m | 10m_wmc3_baci_dual.py | 1.1.0 | (WMC3 BACI) | 10m_01_wmc3_baci_era_steps.csv, 10m_report_numbers.csv | 10m_02_wmc3_baci_dual.png | MS | **DRIFT-min** |
| 10n | 10n_synthetic_did.py | 1.0.0 | 01_climate.csv, 01_wells_clean.csv (via clearfell_common.load_clearfell_data); donor pool read from 10f_robustness.py | 10n_01_zone_gaps.csv, 10n_02_did_contrasts.csv, 10n_03_placebo.csv, 10n_04_pretrend.csv, 10n_report_numbers.csv | — | MS | **OK** |
| 11 | 11_forecasting_thresholds.py | 1.2.0 | 03_03_cluster_mechanistic_coefficients.csv, 03_cluster_peak_months.csv | 11_forecast_pflood_threshold_equations.csv, 11_forecast_*_transfer_functions.csv, 11_forecast_pflood_summary.csv | 11_forecast_02_spring_calibration.png | MS | **OK** |
| 11b | 11b_spatial_thresholds.py | 1.6.3 | 03_master_data.csv, 11_forecast_* , 06_pear_… | 11b_03_pflood_per_well.csv, 11b_05_table10_pflood_spreadsheet.csv | 11b_01…04 | MS | **DRIFT?** |
| 11c | 11c_pflood_achievability.py | 1.2.0 | (pflood) | 11c_pflood_achievability_per_well.csv | 11c_pflood_achievability.png | R8,MS | **OK** |
| 12 | 12_figure_site_overview.py | 1.3.0 | (KML/DEM) | — | 12_01_dem_site_overview.png | MS | **OK** |
| 13 | 13_figure_experimental_design.py | 1.2.0 | (KML) | — | 13_01_experimental_setup_map.png | MS | **OK** |
| 14 | 14_climate_projections.py | 1.4.1 | 00_02_well_network_summary.csv, 02_cluster_stats.csv | 14_annual_extremes.csv, 14_spring/summer/winter_trend_stats.csv, 14_winter_exceedance.csv | 14_climate_trajectory_spring/summer/stacked/winter_flooding.png + 14_seasonal_extremes_scatter.html | MS,SM | **DRIFT** |
| 14b | 14b_year_of_crossing.py | 1.2.0 | (bootstrap) | 14b_year_of_crossing.csv | 14b_year_of_crossing.png | R8,MS | **OK** |
| 15 | 15_depth_dependent_pet.py | 1.2.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 15_03_benchmark_table.csv, 15_04_best_params.csv | 15_01_lambda_profile.png, 15_02_fit_comparison.png | MS,SM | **OK** |
| 16 | 16_water_bal.py | 1.1.1 | 03_03_cluster_mechanistic_coefficients.csv, 03_regional_averages.csv | 16_water_bal_table.csv, 16_water_bal_vol_table.csv | 16_water_bal_bar_ms.png, 16_water_bal_bar_lay.png | MS | **DRIFT** |
| 17 | 17_wtf_specific_yield.py | 1.4.2 | 03_master_data.csv | 17_wtf_01_sy_estimates.csv, 17_wtf_04_summary.txt | 17_wtf_02_regression.png, 17_wtf_03_event_boxplot.png, 17_wtf_05_rapid_events.png | MS | **DRIFT?** |
| 18 | 18_wtf_spatial.py | 1.9.2 | 03_master_data.csv, 06_pear_…, 08_lcsc_model_stats.csv (+01/02) | **17_wtf_well_sy.csv** (per-well, legacy prefix), 18_wtf_01_well_sy_estimates.csv, 18_wtf_05_storage_drainage_index.csv, 18_wtf_07_sy_spatial_trends.csv, 18_report_numbers.csv | 18_wtf_02_spatial_sy_map.png, 18_wtf_03/04_sy_contour*.png, 18_wtf_05_halflife_map.png, 18_wtf_06_aquifer_diagnostic_synthesis.png | MS | **DRIFT-attr** |
| 19 | 19_spatial_groundwater.py | 2.14.0 | 03_master_data.csv, 18_wtf_01_well_sy_estimates.csv (per-well Sy) (+01/02) | 19_scenario_summary.csv, scenario_viewer.html | — | MS,SM | **DRIFT?** |
| 19b | 19b_scraping_simulator.py | 1.2.0 | 03_master_data.csv, 18_wtf_01_well_sy_estimates.csv (+01/02) | scraping_simulator.html | — | — | **OK-orphan** |
| 20 | 20_spatial_figures.py | 1.40.0 | 03_master_data.csv, 03_03_cluster_mechanistic_coefficients.csv, 06_pear_…, 09_scrape_03, 10a_report_numbers.csv, 10b_spatial_step_data.csv, **17_wtf_well_sy.csv** (median-of-per-well), 25_01, 26_msl_5yr_per_well.csv | 20_report_numbers.csv, 20_msl5_report_numbers.csv, 20_residual_report_numbers.csv, 20_drawdown_perwell.csv, 20_msl5_change_perwell.csv, 20_residual_perwell.csv | 18 figures incl. 20_net_state_map.png (Fig 60), 20_driver_change_2005_2025.png (Fig 61), 20_drawdown_propagation_nohead.png (Fig 50), 20_scrape_drawdown*, 20_clearfell_gain.png, 20_msl5_change_2017_2023.png, 20_observed_change_2012_2026.png | R8,MS,SM,P1SI | **DRIFT** |
| 21 | 21_forestry_scenarios.py | 1.6.2 | 03_master_data.csv, 03_regional_averages_maod.csv, 09c_01, 10a_report_numbers.csv, 10e_01 (Sy via scraping_common → **17_wtf_well_sy.csv** median-of-per-well) | 21_forestry_01…06_*.csv | 21_forestry_01…05_*.png/.jpg | MS,SM | **DRIFT?** |
| 22 | 22_residual_lag_analysis.py | 1.4.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 22_05_ssm_residual_autocorrelation.csv, 22_06_ssm_cluster_mean_inference.csv, 22_model_b_fits.csv, 22_residuals_wide.csv | 22_01…04 | R8,MS,SM,P1SI | **OK** |
| 23 | 23_ridge_recharge_lag_test.py | 1.2.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 23_ridge_lag_fits.csv, 23_05_hypothesis_test_summary.txt, 23_residuals_extended_wide.csv | 23_01…04 | MS,SM | **OK** |
| 24 | 24_residual_seasonality.py | 1.3.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 24_residual_climatology.csv, 24_05_diagnostic_summary.txt | 24_01…04 | MS | **OK** |
| 24b | 24b_residual_climatology.py | 1.3.1 | 03_master_data.csv, 22_residuals_wide.csv | 24b_01_cluster_climatology.csv, 24b_02/03, 24b_05_interpretation.txt | 24b_04_cluster_climatology.png | R8,MS | **OK** |
| 25 | 25_coastal_gradient.py | 1.17.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 01_wells_extended.csv, 03_master_data.csv | 25_01_panel_fit_parameters.csv, 25_02/03 (+spring), 25_04_baci_corroboration.csv, 25_08_spring_vs_summer_comparison.csv, 25_09_season_interaction_test.csv, 25_report_numbers.csv | 25_05…08 | R8,MS,SM | **DRIFT?** |
| 26 | 26_van_willegen_msl.py | 1.7.0 | 01_climate.csv, 01_wells_clean.csv, 01_wells_extended.csv, 01_wells_provenance.csv, 01_well_elevations.csv, 02_cluster_stats.csv, 03_master_data.csv, 06_pear_… | 26_msl_5yr_per_well.csv, 26_msl_5yr_per_cluster*.csv, 26_msl_annual_per_well.csv, 26_equilibrium_wetness_index_per_well.csv, 26_ewi_msl5_comparison.csv, 26_ebf_comparison.csv, 26_report_numbers.csv (+msl5_n_* counts) | 26_msl_5yr_map.png, 26_msl_5yr_trajectory.png, 26_msl_5yr_quadrat_wells.png, 26_ebf_prediction_scatter.png, 26_metric_diagnostics.png | R8,MS | **DRIFT** |
| 26b | 26b_van_willegen_msl_projections.py | 1.2.1 | 01_climate.csv, **03_03_cluster_mechanistic_coefficients.csv** (pre-fitted β), 26_msl_5yr_per_cluster_centroid.csv | 26b_msl5_ukcp18_projection_summary*.csv, 26b_monthly_delta_h_per_cluster.csv | 26b_msl5_ukcp18_projection.png | R8,MS | **DRIFT** |
| 26c | 26c_msl5_report_figures.py | 1.1.0 | 19_scenario_summary.csv, 26_msl_5yr_per_cluster.csv, 26b_msl5_ukcp18_projection_summary.csv | 26c_results.txt | fig_msl5_trajectory_report.png, fig_msl5_vs_summer_min_projection.png | R8,MS | **OK*** |
| 27 | 27_greyscale_figures.py | 1.0.0 | (figures) | — | (greyscale renders) | R8,MS | **OK** |
| 28 | 28_c3_detrend_check.py | 1.2.0 | 03_master_data.csv | 28_c3_detrend.csv | 28_c3_detrend_panel.png | R8,MS | **OK** |
| 29 | 29_c3_within_variance_check.py | 1.4.1 | 03_master_data.csv | 29_within_c3_variance.csv, 29_univariate_R2.csv, 29_drop_one.csv, 29_report_numbers.csv | 29_within_c3_variance_panel.png | R8,MS | **DRIFT** |
| 30 | 30_c4_drainage_identifiability.py | 2.2.1 | 01_climate.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 30_c4_identifiability_by_cluster.csv, 30_c4_perwell_beta3.csv, 30_c4_report_numbers.csv | 30_c4_drainage_identifiability.png | R8,MS | **DRIFT** |
| 31 | 31_cluster_validation.py | 1.4.1 | 01_dry_depths.csv, 01_well_elevations.csv, 01_wells_clean.csv, 03_master_data.csv, 17_wtf_well_sy.csv | 31_validation_summary.csv, 31_forest_confusion.csv, 31_method_robustness_ari.csv, 31_forest_borderline.csv | 31_cluster_validation_panel.png | R8,MS | **DRIFT?** |
| 31b | 31b_separation_vs_recoverability.py | 1.3.0 | 01_dry_depths.csv, 01_well_elevations.csv, 01_wells_clean.csv, 03_master_data.csv | 31b_separation_vs_recoverability.csv | 31b_separation_vs_recoverability.png | R8,MS | **OK** |
| 32 | 32_differential_movement.py | 1.4.0 | 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv | 32_differential_movement_per_well.csv, 32_site_mean_trend.csv, 32_results.txt | 32_differential_movement_2005_2025.png, 32_differential_movement_2011_2025.png | R8,MS,SM | **DRIFT?** |
| 33 | 33_envelope_amplification.py | 1.4.0 | 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv, 06_pear_membership_audit_sitewide.csv | 33_envelope_per_well.csv, 33_envelope_per_well_recent.csv, 33_results.txt | 33_amplification_field.png (Fig 65), 33_dry_spring_depth.png (Fig 66), +_recent variants | R8,MS,SM | **DRIFT** |
| 34 | 34_window_sensitivity.py | 0.6.0 | 00_01_annual_climate_summary.csv, 26_msl_annual_per_well.csv, 32_site_mean_trend.csv | 34_window_matrix.csv, 34_results.txt | 34_window_sensitivity.png | R8,MS,SM | **DRIFT?** |
| 35 | 35_per_well_amplification.py | 1.2.0 | 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv, 06_pear_membership_audit_sitewide.csv | 35_per_well_amplification.csv, 35_results.txt | 35_coefficient_markers.png, 35_ssm_calibration.png | R8,MS,SM | **OK** |
| 36 | 36_absolute_climate_trend.py | 1.3.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv | 36_absolute_climate_trend_per_well.csv, 36_results.txt | 36_absolute_climate_trend_2005_2025.png, 36_absolute_climate_trend_2011_2025.png | R8,MS,SM | **OK** |
| 37 | 37_driver_validation.py | 3.2.0 | 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv, 10a_report_numbers.csv, 25_01_panel_fit_parameters.csv, 36_absolute_climate_trend_per_well.csv | 37_driver_validation_per_well.csv, 37_scale_factors_by_window.csv, 37_results.txt | 37_predicted_vs_observed.png, 37_residual_map.png, 37_implied_delta0_trajectory.png | R8,MS | **OK** |
| 37b | 37b_driver_footing.py | 1.3.0 | 01_wells_clean.csv, 03_master_data.csv, 09_scrape_03_baci_shifts.csv, 10a_report_numbers.csv, 10m_report_numbers.csv, 20_report_numbers.csv, 25_01_panel_fit_parameters.csv | 37b_driver_footing.csv, 37b_results.txt | 37b_driver_footing.png | R8,MS | **DRIFT** |
| 38 | 38_coastal_transect.py | 1.5.0 | 01_locations.csv, 01_wells_clean_maod.csv, 25_01_panel_fit_parameters.csv | 38_transect.csv, 38_results.txt | 38_transect_profile.jpg, 38_coast_inland_difference.jpg | R8,MS | **OK** |
| 39 | 39_ccw_hindcast.py | 1.3.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv | 39_01_hindcast_per_well.csv, 39_02_hindcast_series.csv, 39_03_beta1_sensitivity.csv, 39_05_full_hindcast_site.csv, 39_06_full_hindcast_decadal.csv, 39_results.txt | 39_04_hindcast.png, 39_07_full_hindcast.png | MS | **OK** |

*(Not rows: `gen_grid_lay.py`, `run_09_scraping.py`, `run_10_clearfell.py` — utility/orchestration.)*
