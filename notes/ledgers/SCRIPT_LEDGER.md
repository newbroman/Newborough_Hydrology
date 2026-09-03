# SCRIPT_LEDGER — Newborough Warren pipeline

**Living ledger. Edit in place; do not date the filename.** One row per pipeline
script: what it consumes, what it emits, which documents describe it, and its
current code-vs-documentation status. This is the anti-drift spine — read it to
know the current state without replaying the changelog history.

- **Source of truth:** GitHub `main`, HEAD `616bf2f` (2026-08-26).
- **First populated:** 2026-08-14, from a full code scan + a code-vs-doc audit
  (see `NRG_methods_code_audit_2026-08-14.md` for the finding detail).
- **Version housekeeping:** 2026-08-28 — rows 10a, 25 and 30 bumped with the
  changes of that day (D-076, D-077, D-078, the `baci_corroboration` cap fix
  and Script 30's derived `note=` ranks). Their **Status flags are NOT reset**:
  a version bump is not a reconciliation, and each row's standing finding is
  still open under T-15.
- **Last reconciled:** 2026-08-26 (T-02). Every `DRIFT?` row — the seventeen
  `ledger_lint --fix-versions` had bumped without re-reading — was adjudicated
  against the script, its diff since the ledger was built, and the documents its
  `Cited` cell names. Evidence per row:
  `working/updates/T02_LEDGER_2026-08-26.md`.
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
Supplement (currently v1_9_50) · SM = Supplementary Material (currently v1_22) ·
P1 = Paper 1 · P1SI = Paper 1 SI methods · P2 = Paper 2.

*There is no code for report9 or report10.* Six of the seventeen rows read on
2026-08-26 hit this: the results chapters carry the text that describes a
script's output, and the `Cited` cell has no way to say so, which makes those
rows look less documented than they are and leaves the results chapters outside
every check that walks this column. Adding R9/R10 means re-auditing `Cited` on
all 68 rows, so it is recorded here rather than done by halves.

**Scanner caveats:** Consumes/Emits are AST-derived and attributed by the
`paths.py` `OUT_/INT_` convention plus write-scan. A script's own second-pass
self-reads appear under Emits, not Consumes (e.g. 03 reading `03_master_data`).
Display/utility helpers (`gen_grid_lay.py`, `run_09_scraping.py`,
`run_10_clearfell.py`) are not numbered rows.

`tools/script_io_scan.py` re-derives the two I/O columns on demand and prints the
difference against each row. It follows path constants through module aliases,
dict dispatch tables and one level of helper — enough to see the figures saved by
`render_utils.render_figure`, which is most of them — and it prints what it could
*not* resolve rather than dropping it. It writes nothing and sets no status: the
same reasoning `ledger_lint` gives for refusing these columns still holds, and
the tool answers only the mechanical half. Where it cannot parse a shared module
it says so, and that line means one of two quite different things — establish
which before acting on it. On 2026-08-26 it flagged `mechanism_fig_utils`, that
was read as a live import failure, and it was not one: the message came from a
Cowork sandbox running Python 3.10 while this project runs on 3.12.3. What it had
really found was the tree's only undeclared ≥3.12 syntax, since removed. Worth
knowing either way: `src/venv/bin/python3.12` is a symlink to `/usr/bin/python3`,
so it is whatever the host's system Python happens to be, not a pinned
interpreter.

## Summary

68 numbered scripts. **34 clean · 34 with drift/gap findings.** The count of
findings rose sharply on 2026-08-26 and the reason is worth stating plainly: the
seventeen `DRIFT?` rows were not noise. Fourteen of them turned out to carry a
real finding, and sixteen had read `OK` a fortnight earlier. What the ledger was
recording, once someone read the scripts, was that **a fast run of code changes
between 2026-08-18 and 2026-08-23 outpaced the documents** — the D-035
rounding removal, the far-field control tier, the D-038 Sy rename, the spring-mean
strand, the `in_forest` land-cover flag — and that several of those batches say
so in their own changelogs ("No document text was changed").

The drift clusters into: (1) prose describing a pipeline shape the code has
outgrown — the "Script-35 class" — 07, 09f, 10i, 16, 20, 30, and now 09g (the
retired far-field term still drawn in MS, P1 and report10) and 10k (MS still
calls it the primary §4.6 result, against D-061); (2) stale numbers/counts — 03,
08, 14, 20, 26, and now 09a (CEH36 β₃ triple, where MS and P2 disagree with the
CSV *and* with each other) and 10k; (3) wrong attribution/provenance — 00, 18,
26b, 09f→Paper1, the Approach-B Sy conflation in MS S.12, and now 09d, 17 and 21,
all three of which are the same D-038 rename reaching the documents late;
(4) an undocumented emitted element — 37b's common-mode component, 33's
recent-window products, and now 02's month-wise stability block, 10a's far-field
tier and `10a_09`, 25's canopy-controlled fourth fit and its `_spring` twins, 32's
four-row site-mean basis, 19's water-equivalent columns and basis toggle; (5)
minor stragglers — 09b, 09c, 10h, 10m, 26c step-numbers, 29's retired-τ label,
33's missing 2016 wet year, 10c's leave-one-out R², 10f's `ALL_NETWORK_WELLS`
sentence, 21's `TIERS` sentence. Confirmed clean on the things most likely to
have rotted: the τ=Sy/β₃ retirement (no document calls it a residence time), the
MSL upstand removal (Script 26), Script 35 itself (the trigger case — now
documented correctly), and, on this pass, 31, 34 and 11b, where the version bump
turned out to have moved the code *toward* the documents rather than away.

Three cautions about this table. **A finding here is a documentation job, not a
broken result** — in most of these rows the code is right and the prose is
behind. **`-TR` is not reassurance**: 10a's rows say the committed CSVs changed
precision under D-035, so pre- and post-2026-08-18 quotations of the same fit do
not agree. And **the clean rows were checked against the markdown mirrors and the
committed CSVs that exist**; where `outputs/` held nothing to retrace against,
the row's adjudication says so.

## Ledger

| # | Script | Ver | Consumes | Emits (data) | Emits (figs) | Cited | Status |
|---|--------|-----|----------|--------------|--------------|-------|--------|
| 00 | 00_climate_summary.py | 1.4.1 | 01_climate.csv, 01_wells_clean.csv | 00_01_annual_climate_summary.csv, 00_02_well_network_summary.csv, 00_03_summer_warming_stats.csv, 00_04_climatology.csv, 00_report_numbers.csv | 00_01_climate_timeseries.png, 00_02_well_network_summary.png, 00_03_summer_warming_trend.png | MS | **DRIFT** |
| 01 | 01_data_prep.py | 1.14.0 | Newborough_Cleaned_For_Model.csv, well_metadata.csv, RAF_Valley_Climate.csv, Newborough_well_records_pipeline.ods, geo/coastline_eroding_hwm.geojson, geo/forest_boundary.geojson (new at 1.12.0); 2nd-pass: 03_master_data.csv, 06_pear_membership_audit_sitewide.csv, and via pipeline_params (all .exists()-guarded) 03_03_cluster_mechanistic_coefficients.csv, 03_cluster_peak_months.csv, 10e_01_coefficient_shifts.csv, 18_wtf_01_well_sy_estimates.csv | 01_climate.csv, 01_locations.csv (incl. in_forest), 01_wells_clean.csv, 01_wells_clean_maod.csv, 01_wells_reference.csv, 01_wells_extended.csv, 01_wells_provenance.csv, 01_well_elevations.csv, 01_dry_depths.csv, 01_observation_states.csv (also self-read as .ods fallback), 01_observation_state_conflicts.csv, 01_dist_coast_validation.csv, pipeline_scenario_params.csv (helper-written) | 01_coverage_states_extended.png, 01_coverage_states_reference.png (helper-saved) | R8,MS | **DRIFT** |
| 02 | 02_clustering.py | 1.6.0 | 01_climate.csv, 01_wells_clean.csv, 01_wells_reference.csv | 02_cluster_stats.csv, 02_04_bootstrap_stability_summary.csv, 02_05_bootstrap_stability_per_well.csv, 02_06_k_sweep_validation.csv, 02_07_cluster_membership_k{k}.csv (+stability_months at k=5), 02_08_cluster_amplitude_per_well.csv, 02_09_cluster_amplitude_summary.csv, 02_11_month_stability.csv, 02_report_numbers.csv | 02_01_dendrogram.png, 02_02_validation_plots.png, 02_02b_validation_k_sweep.png, 02_03_cluster_hydrographs_wb.png, 02_03b_cluster_spaghetti.png, 02_06_coassignment_heatmap_k{k}.png, 02_10_cluster_amplitude_boxplot.png, 02_12_month_stability_diagnostic.png | MS | **OK** |
| 03 | 03_state_space_model.py | 1.9.4 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 01_wells_clean_maod.csv, 01_well_elevations.csv, 02_cluster_stats.csv, 02_08_cluster_amplitude_per_well.csv | 03_master_data.csv, 03_regional_averages.csv, 03_regional_averages_maod.csv, 03_cluster_peak_months.csv, 03_02_cluster_summary_table.csv, 03_03_cluster_mechanistic_coefficients.csv, 03_04_lag_diagnostic.csv, 03_05_bootstrap_ci.csv, 03_06_leave_one_out.csv, 03_07_c1_split_window.csv, 03_08_datum_sensitivity.csv, 03_09_well_datum_sensitivity.csv, 03_09_well_optimal_datums.csv, 03_11_datum_confound_diagnostics.csv, 03_12_partition_vs_datum.csv, 03_13_centroid_composition_sensitivity.csv, 03_14_centroid_window_sensitivity.csv, 03_15_per_well_window_sensitivity.csv | 03_01_mechanistic_signatures.png, 03_08_datum_sensitivity.png, 03_09_well_optimal_datums.png, 03_10_well_datum_r2max_map.png, 03_10_well_r2_gain_map.png, 03_12_datum_regime.png | MS,SM | **OK** |
| 04 | 04_cluster_visualisations.py | 1.0.0 | 01_locations.csv, 02_cluster_stats.csv | — | 04_01_core_architecture_map.png | MS | **OK** |
| 05 | 05_pearson_affinity.py | 1.3.1 | 01_locations.csv, 02_cluster_stats.csv | 05_pear_membership_audit.csv | 05_pear_01_spatial_confidence_map.png, 05_pear_02_affinity_chart_reference.png | MS | **OK** |
| 06 | 06_pearson_extended.py | 1.0.0 | 01_wells_extended.csv, 01_wells_reference.csv, 02_cluster_stats.csv | 06_pear_membership_audit_sitewide.csv | 06_pear_01_affinity_chart_extended.png, 06_pear_02_integration_map.png | MS | **OK** |
| 07 | 07_spatial_coefficients.py | 1.2.1 | 01_well_elevations.csv, 03_master_data.csv | 07_cluster_coeff_means.csv, 07_report_numbers.csv | (IDW surfaces, helper-saved) | MS | **DRIFT** |
| 08 | 08_model_benchmarking.py | 1.5.0 | 01_climate.csv, 01_wells_clean.csv, 02_cluster_stats.csv, 03_master_data.csv | 08_lcsc_04_table3_benchmark_summary.csv, 08_perwell_nse.csv, 08_report_numbers.csv | 08_lcsc_01_ceh6_showdown.png, 08_lcsc_02_r2_improvement_map.png, 08_lcsc_03_nse_improvement_map.png | MS | **DRIFT** |
| 09a | 09a_paired_baci.py | 2.9.0 | 01_climate.csv, 01_wells_clean.csv, 01_wells_extended.csv, 01_wells_provenance.csv (all via scraping_common.load_scraping_data; provenance received and unused) | 09_scrape_01…04b_*.csv, 09_scrape_report_numbers.csv, 09_tier1_final_cusum.csv, 09_scrape_09_monthly_step_trend.csv, 09_scrape_10_detectability.csv | 09_scrape_05_tier1_background_drift.png, 09_scrape_06_tier2_scraping_signal.png, 09_scrape_07_beta3_confidence.png | R8,MS,P2 | **DRIFT** — v2.9.0 (D-103) adds the monthly step/trend fits and the detectability floor beside the era contrasts; 09_scrape_03_baci_shifts.csv is unchanged and the step-only coefficient is asserted at run time to reproduce it |
| 09b | 09b_scraping_propagation.py | 1.7.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 01_wells_extended.csv, 03_master_data.csv, 17_wtf_01_sy_estimates.csv | 09b_01_individual_well_baci.csv, 09b_02_centroid_summaries.csv, 09b_04_scenario_comparison.csv, 09b_05_summer_scenario_comparison.csv | 09b_03_ceh36_equilibration.jpg, 09b_04_scenario_comparison.jpg, 09b_05_summer_scenario_comparison.png | MS | **DRIFT** |
| 09c | 09c_summer_minima.py | 1.6.0 | 01_climate.csv, 03_master_data.csv | 09c_01_summer_minima.csv, 09c_02_summer_minima_shifts.csv, 09c_05_spring_means.csv, 09c_06_spring_means_shifts.csv, 09c_report_numbers.csv | 09c_03…04 + 09c_07_spring_means_climate_ctrl.png, 09c_08_spring_means_paired.png | MS,SM | **DRIFT-min** |
| 09d | 09d_scenario_comparison.py | 3.10.2 | 01_climate.csv, 01_wells_clean.csv, 03_master_data.csv, **18_wtf_01_well_sy_estimates.csv** (per-well Sy; D-038), 20_report_numbers.csv (λ), pipeline_scenario_params.csv and pipeline_site_observations.csv (via helpers), 10e_01_coefficient_shifts.csv (β₂-mult fallback) | 09d_01_scenario_comparison.csv, 09d_02_summer_scenario_comparison.csv | 09d_01_scenario_comparison.jpg, 09d_02_summer_scenario_comparison.png | R8,MS | **DRIFT-attr** |
| 09e | 09e_robustness.py | 2.2.0 | 03_master_data.csv | 09e_report_numbers.csv | 09_scrape_08_ceh36_robustness.png | MS | **OK** |
| 09f | 09f_management_effects.py | 1.9.0 | 03_03_cluster_mechanistic_coefficients.csv, 09b_01_individual_well_baci.csv, 09d_01_scenario_comparison.csv, 10a_report_numbers.csv, 10m_report_numbers.csv, 20_report_numbers.csv, 25_01_panel_fit_parameters.csv | 09f_01_reach_profile.csv (one column per drawn curve; climate and far-field columns both retired — D-039, D-043) | 09f_management_effects.png, 09f_management_effects_public.png | R8,MS,P1 | **DRIFT** |
| 09g | 09g_mechanism_diagrams.py | 1.7.0 | 09f_01_reach_profile.csv, 10a_report_numbers.csv, 10m_report_numbers.csv (all via utils/mechanism_fig_utils; 25_01 retired at v1.6.0, D-049) | — | 09g_mechanism_grid.svg/.png, 09g_coastal_vs_climate_reach.svg/.png, 09g_mechanism_lay_management.svg/.png, 09g_mechanism_lay_drivers.svg/.png (SVG is the master, PNG a cairosvg placement copy; the lay pair via gen_grid_lay.render_all()) | R8,MS,P1 | **DRIFT** |
| 10a | 10a_ancova_baci.py | 1.11.1 | 01_climate.csv, 01_wells_clean.csv, 01_wells_extended.csv, 01_wells_provenance.csv, 03_master_data.csv, well_metadata.csv, 10i_01_ceh34_hindcast.csv, 25_01_panel_fit_parameters.csv (2nd-pass; falls back to a pipeline_params default) — all via clearfell_common | 10a_report_numbers.csv, 10a_01_ancova_comparison_table.csv, 10a_02_ancova_full_coefficients.csv, 10a_02b_drift_design_equivalence.csv, 10a_03_baci_timeseries.csv, 10a_09_control_well_spread.csv (new at 1.6.0; read by Script 25), 10a_09_coastal_scale_factor.csv (M14/D-076), 10a_10_coastal_fixed1_sensitivity.csv | 10a_04…08 + S1–S3 | R8,MS | **OK** |
| 10b | 10b_spatial_step_maps.py | 1.7.0 | 01_well_elevations.csv, 01_wells_clean.csv, 01_wells_extended.csv, 03_master_data.csv | 10b_spatial_step_data.csv | 10b_spatial_fell_corrected.png, 10b_spatial_fell_raw.png, 10b_spatial_scrape_corrected.png, 10b_spatial_scrape_raw.png | R8,MS | **OK** |
| 10c | 10c_forest_zone_analysis.py | 1.2.0 | 06_pear_membership_audit_sitewide.csv, 07_coeff_maps_data.csv, well_metadata.csv (helper-loaded, map only) | 10c_forest_zone_correlations.csv (+R2_elevation_only_LOO at 1.1.0), 10c_forest_zone_cluster_summary.csv, 10c_04_forest_zone_summary.txt — all three in outputs/10c_forest_zone_analysis/ since 1.2.0; the first two were INT_ at the outputs root and nothing downstream reads them | 10c_01_b1_b2_scatter.png, 10c_02_b2_elevation_regression.png, 10c_03_c4_c5_boundary_map.png | R8,MS | **GAP-min** |
| 10d | 10d_summer_minima.py | 1.8.0 | 01_wells_clean.csv, 01_climate.csv (via clearfell_common.load_clearfell_data) | 10d_01_summer_minima.csv, 10d_02_summer_minima_shifts.csv, 10d_03_mixed_model_results.csv, 10d_06_spring_means.csv, 10d_07_spring_means_shifts.csv, 10d_08_spring_mixed_model_results.csv, 10d_report_numbers.csv | 10d_04, 10d_05 summer + 10d_09, 10d_10 spring | MS,SM | **OK-TR** |
| 10e | 10e_coefficient_decomposition.py | 1.7.0 | 03_master_data.csv | 10e_01_coefficient_shifts.csv (β₂ multipliers), 10e_report_numbers.csv | 10e_03_* (report Fig 35) | MS | **OK** |
| 10f | 10f_robustness.py | 1.3.0 | 01_climate.csv, 01_wells_clean.csv, 01_wells_extended.csv, 01_wells_provenance.csv, 03_master_data.csv, well_metadata.csv (all via clearfell_common.load_clearfell_data; donor pool pinned to CORE_NETWORK_WELLS at 1.2.0) | 10f_01_ssm_residual_results.csv, 10f_02_synthetic_control_results.csv, 10f_report_numbers.csv | — | MS | **DRIFT-min** |
| 10g | 10g_diagnostics.py | 1.2.0 | 03_regional_averages.csv | 10g_01_nw10_broadleaf_trend.csv, 10g_03_clearfell_transect_steps.csv, 10g_04_rolling_coefficients.csv, 10g_report_numbers.csv | 10g_02_clearfell_transect.png | MS | **OK** |
| 10h | 10h_synthetic_impact_baci.py | 1.5.0 | 01_wells_clean.csv, 01_climate.csv (via clearfell_common); donor pool CEH34/CEH2/CEH33 | 10h_01_synthetic_calibration.csv, 10h_02_ancova_comparison_table.csv, 10h_03_ancova_full_coefficients.csv, 10h_04_baci_timeseries.csv, 10h_report_numbers.csv | 10h_05_donor_regression_validation.png, 10h_06…08 BACI time-series (variants A, B, C) | MS | **DRIFT-min** |
| 10i | 10i_ceh34_hindcast.py | 1.2.0 | (donor regression) | 10i_01_ceh34_hindcast.csv, 10i_02_donor_regression.csv, 10i_report_numbers.csv | 10i_03_hindcast_diagnostic.png | MS | **DRIFT** |
| 10j | 10j_impact_edge_contrast.py | 1.4.0 | 10d_01_summer_minima.csv | 10j_01_monthly_contrast_results.csv, 10j_02_summer_contrast_results.csv, 10j_report_numbers.csv | 10j_03_contrast_timeseries.jpg, 10j_04_summer_minima_contrast.jpg | R8,MS | **OK** |
| 10k | 10k_four_zone_baci.py | 1.4.0 | 01_climate.csv, 01_wells_clean.csv, 01_wells_extended.csv, 01_wells_provenance.csv, 03_master_data.csv (via clearfell_common.load_clearfell_data); 10j_01_monthly_contrast_results.csv (optional — cross-check only) | 10k_01_four_zone_results.csv, 10k_02_pairwise_contrasts.csv, 10k_03_easting_sensitivity.csv, 10k_report_numbers.csv | 10k_04_zone_centroids.jpg, 10k_05_contrast_forest.jpg, 10k_06_forest_plot.jpg | R8,MS | **OK** |
| 10l | 10l_four_zone_summer_minima.py | 1.3.0 | 10j_02_summer_contrast_results.csv, 10d_01_summer_minima.csv (summer), 10d_06_spring_means.csv (spring) | 10l_01…03 summer + 10l_06…08 spring, 10l_report_numbers.csv | 10l_04,05,09,10 | MS,SM | **OK** |
| 10m | 10m_wmc3_baci_dual.py | 1.2.0 | (WMC3 BACI); 10a_report_numbers.csv (live ANCOVA step, CI and p) | 10m_01_wmc3_baci_era_steps.csv, 10m_report_numbers.csv | 10m_02_wmc3_baci_dual.png | MS | **DRIFT-min** |
| 10n | 10n_synthetic_did.py | 1.1.0 | 01_climate.csv, 01_wells_clean.csv (via clearfell_common.load_clearfell_data); donor pool read from 10f_robustness.py | 10n_01_zone_gaps.csv, 10n_02_did_contrasts.csv, 10n_03_placebo.csv, 10n_04_pretrend.csv, 10n_report_numbers.csv | — | MS | **OK** |
| 11 | 11_forecasting_thresholds.py | 1.3.3 | 03_03_cluster_mechanistic_coefficients.csv, 03_cluster_peak_months.csv | 11_forecast_pflood_threshold_equations.csv, 11_forecast_*_transfer_functions.csv, 11_forecast_pflood_summary.csv | 11_forecast_02_spring_calibration.png | MS | **OK** |
| 11b | 11b_spatial_thresholds.py | 1.7.1 | 01_locations.csv, 01_well_elevations.csv, 01_wells_clean.csv, 01_wells_clean_maod.csv, 01_wells_extended.csv, 03_master_data.csv, 03_03_cluster_mechanistic_coefficients.csv, 03_cluster_peak_months.csv, 03_regional_averages.csv, 06_pear_membership_audit_sitewide.csv, 11_forecast_winter_transfer_functions.csv, 11_forecast_summer_transfer_functions.csv, 11_forecast_pflood_threshold_equations.csv, src/forecaster_template.html, DEM + Features/clearfell/site_boundary KML (helper-loaded) | 11b_03_pflood_per_well.csv, 11b_05_table10_pflood_spreadsheet.csv, forecaster.html (published to Pages by nrg_git.sh), living/forecaster_engine.json (hash-gated engine feed for the Well Logger app; written only when the engine subset moves) | 11b_01…04 | R8,MS | **OK*** |
| 11c | 11c_pflood_achievability.py | 1.2.0 | (pflood) | 11c_pflood_achievability_per_well.csv | 11c_pflood_achievability.png | R8,MS | **OK** |
| 12 | 12_figure_site_overview.py | 1.4.0 | (KML/DEM), 01_locations.csv | 12_02_break_in_slope.csv, 12_report_numbers.csv | 12_01_dem_site_overview.png, 12_02_break_in_slope.png | MS | **OK** — numeric emitter since 1.4.0 (D-099): the northern break in slope, gated on column coverage and break-elevation sd. 12_01 is report Figure 1 and is NOT altered by the break work; the break has its own map |
| 13 | 13_figure_experimental_design.py | 1.2.0 | (KML) | — | 13_01_experimental_setup_map.png | MS | **OK** |
| 14 | 14_climate_projections.py | 1.5.0 | 03_regional_averages.csv, 00_02_well_network_summary.csv, 02_cluster_stats.csv | 14_annual_extremes.csv, 14_spring/summer/winter_trend_stats.csv, 14_winter_exceedance.csv | 14_climate_trajectory_spring/summer/stacked/winter_flooding.png + 14_seasonal_extremes_scatter.html | MS,SM | **OK** |
| 14b | 14b_year_of_crossing.py | 1.2.0 | (bootstrap) | 14b_year_of_crossing.csv | 14b_year_of_crossing.png | R8,MS | **OK** |
| 15 | 15_depth_dependent_pet.py | 1.4.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 15_03_benchmark_table.csv, 15_04_best_params.csv, 15_00_lambda_profiles_raw.csv | 15_01_lambda_profile.png, 15_02_fit_comparison.png | MS,SM | **OK?** |
| 16 | 16_water_bal.py | 1.2.0 | 03_03_cluster_mechanistic_coefficients.csv, 03_regional_averages.csv | 16_water_bal_table.csv, 16_water_bal_vol_table.csv | 16_water_bal_bar_ms.png, 16_water_bal_bar_lay.png | MS | **DRIFT** |
| 17 | 17_wtf_specific_yield.py | 1.4.3 | 01_climate.csv, 03_master_data.csv (β₃, guarded), 03_regional_averages.csv | 17_wtf_01_sy_estimates.csv, 17_wtf_04_summary.txt | 17_wtf_02_regression.png, 17_wtf_03_event_boxplot.png, 17_wtf_05_rapid_events.png | MS | **DRIFT-attr** |
| 18 | 18_wtf_spatial.py | 1.9.2 | 03_master_data.csv, 06_pear_…, 08_lcsc_model_stats.csv (+01/02) | 18_wtf_01_well_sy_estimates.csv (the per-well table; the `17_wtf_well_sy.csv` legacy prefix was RETIRED 2026-08-19, D-038, and is no longer written), 18_wtf_05_storage_drainage_index.csv, 18_wtf_07_sy_spatial_trends.csv, 18_report_numbers.csv | 18_wtf_02_spatial_sy_map.png, 18_wtf_03/04_sy_contour*.png, 18_wtf_05_halflife_map.png, 18_wtf_06_aquifer_diagnostic_synthesis.png | MS | **OK** |
| 19 | 19_spatial_groundwater.py | 2.17.0 | 01_climate.csv, 01_locations.csv, 01_well_elevations.csv, 01_wells_clean_maod.csv, 02_cluster_stats.csv, 03_master_data.csv (window-basis β), 03_15_per_well_window_sensitivity.csv (full-record β — viewer basis toggle, D-034), 18_wtf_01_well_sy_estimates.csv (per-well Sy), 26b_msl5_ukcp18_projection_summary_perwell.csv (ΔMSL5 cross-check), 10e_01_coefficient_shifts.csv (helper-read), (KML/DEM) | 19_scenario_summary.csv (+we_mean_mm, we_median_mm, sy_mean at 2.15.0), scenario_viewer.html | — | MS,SM | **OK** |
| 19b | 19b_scraping_simulator.py | 1.2.0 | 03_master_data.csv, 18_wtf_01_well_sy_estimates.csv (+01/02) | scraping_simulator.html | — | — | **OK-orphan** |
| 20 | 20_spatial_figures.py | 1.41.0 | 01_wells_clean.csv, 01_wells_clean_maod.csv, 01_wells_extended.csv, 01_locations.csv, 01_well_elevations.csv, 01_climate.csv, 25_01_panel_fit_parameters.csv, newborough_dem.tif, streams.kml, Features.kml, broadleaf_restock.kml, 03_master_data.csv, 03_03_cluster_mechanistic_coefficients.csv, 06_pear_…, 09_scrape_03, 10a_report_numbers.csv, 10b_spatial_step_data.csv, 18_wtf_01_well_sy_estimates.csv (median-of-per-well; was `17_wtf_well_sy.csv`, retired D-038), 26_msl_5yr_per_well.csv | 20_report_numbers.csv, 20_msl5_report_numbers.csv, 20_residual_report_numbers.csv, 20_drawdown_perwell.csv, 20_msl5_change_perwell.csv, 20_residual_perwell.csv, 20_scrape_drawdown_perwell.csv | 16 figures (2 further with-head variants 20_drawdown_propagation.png / 20_scrape_drawdown.png are show_head-gated, off by default) incl. 20_net_state_map.png (Fig 60), 20_driver_change_2005_2025.png (Fig 61), 20_drawdown_propagation_nohead.png (Fig 50), 20_scrape_drawdown_nohead.png, 20_clearfell_gain.png, 20_msl5_change_2017_2023.png, 20_observed_change_2012_2026.png | R8,MS,SM,P1SI | **OK** |
| 21 | 21_forestry_scenarios.py | 1.8.0 | 01_climate.csv, 01_well_elevations.csv, 01_wells_clean.csv, 01_wells_extended.csv (opt), 01_wells_provenance.csv (opt), 03_master_data.csv, 03_03_cluster_mechanistic_coefficients.csv (helper-read), 03_regional_averages_maod.csv, 09c_01_summer_minima.csv, 10a_report_numbers.csv, 10e_01_coefficient_shifts.csv (β₂-mult fallback), pipeline_scenario_params.csv (β₂ mult + Sy; Sy seeded by Script 01 from **18_wtf_01_well_sy_estimates.csv**, median-of-per-well; D-038) | 21_forestry_01…06_*.csv | 21_forestry_01…05_*.png/.jpg | MS,SM | **DRIFT-min** |
| 22 | 22_residual_lag_analysis.py | 1.4.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 22_05_ssm_residual_autocorrelation.csv, 22_06_ssm_cluster_mean_inference.csv, 22_model_b_fits.csv, 22_residuals_wide.csv | 22_01…04 | R8,MS,SM,P1SI | **OK** |
| 23 | 23_ridge_recharge_lag_test.py | 1.2.1 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 23_ridge_lag_fits.csv, 23_05_hypothesis_test_summary.txt, 23_residuals_extended_wide.csv | 23_01…04 | MS,SM | **OK** |
| 24 | 24_residual_seasonality.py | 1.3.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 24_residual_climatology.csv, 24_05_diagnostic_summary.txt | 24_01…04 | MS | **OK** |
| 24b | 24b_residual_climatology.py | 1.5.0 | 03_master_data.csv, 22_residuals_wide.csv | 24b_01_cluster_climatology.csv, 24b_02/03, 24b_05_interpretation.txt | 24b_04_cluster_climatology.png | R8,MS | **OK?** |
| 25 | 25_coastal_gradient.py | 1.23.0 | well_metadata.csv (dist_coast_m), 01_climate.csv, 01_locations.csv (incl. in_forest), 01_wells_clean.csv, 01_wells_extended.csv, 03_master_data.csv, 06_pear_membership_audit_sitewide.csv, 10a_02_ancova_full_coefficients.csv, 10a_09_control_well_spread.csv (warn-and-skip if absent), 14_summer_trend_stats.csv, 14_spring_trend_stats.csv, 20_msl5_change_perwell.csv (Check 2; skipped if absent) | 25_01_panel_fit_parameters.csv (all-season + full_canopy + MAM-only rows), 25_02/03 (+spring), 25_04_baci_corroboration.csv, 25_04b_baci_corroboration_spread.csv, 25_08_spring_vs_summer_comparison.csv, 25_09_season_interaction_test.csv, 25_10_record_length_composition.csv (+spring), 25_11_matched_window_sensitivity.csv (reported only), 25_12_window_sweep.csv, 25_13_rolling_window.csv, 25_14_correction_diagnostic.csv (+spring; two donor fits since 1.18.0), 25_15_covariate_specification_range.csv (reported only), 25_report_numbers.csv | 25_05…08 (incl. 25_05/25_07 _spring twins), 25_12_window_sweep.png, 25_13_rolling_window.png | R8,MS,SM,P1,P1SI | **OK** |
| 26 | 26_van_willegen_msl.py | 1.8.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 01_wells_extended.csv, 01_wells_provenance.csv, 01_well_elevations.csv, 02_cluster_stats.csv, 03_master_data.csv, 03_regional_averages.csv (Method B, cluster-centroid MSL5), 06_pear_membership_audit_sitewide.csv (extended network) | 26_msl_5yr_per_well.csv, 26_msl_5yr_latest_per_well.csv, 26_msl_5yr_per_cluster*.csv, 26_msl_annual_per_well.csv, 26_equilibrium_wetness_index_per_well.csv, 26_ewi_msl5_comparison.csv, 26_ebf_comparison.csv, 26_report_numbers.csv (+msl5_n_* counts), 26_metric_diagnostics_per_well.csv, 26_index_precision_by_cluster.csv, 26_table_s7_1_ewi_per_well.csv/.md, 26_msl_results.txt | 26_msl_5yr_map.png, 26_msl_5yr_trajectory.png, 26_msl_5yr_quadrat_wells.png, 26_ebf_prediction_scatter.png, 26_metric_diagnostics.png | R8,MS | **OK** |
| 26b | 26b_van_willegen_msl_projections.py | 1.3.0 | 01_climate.csv, **03_03_cluster_mechanistic_coefficients.csv** (pre-fitted β), 26_msl_5yr_per_cluster_centroid.csv | 26b_msl5_ukcp18_projection_summary*.csv, 26b_monthly_delta_h_per_cluster.csv | 26b_msl5_ukcp18_projection.png | R8,MS | **OK** |
| 26c | 26c_msl5_report_figures.py | 1.1.0 | 19_scenario_summary.csv, 26_msl_5yr_per_cluster.csv, 26b_msl5_ukcp18_projection_summary.csv | 26c_results.txt | fig_msl5_trajectory_report.png, fig_msl5_vs_summer_min_projection.png | R8,MS | **OK*** |
| 27 | 27_greyscale_figures.py | 1.0.0 | (figures) | — | (greyscale renders) | R8,MS | **OK** |
| 28 | 28_c3_detrend_check.py | 1.2.0 | 03_master_data.csv | 28_c3_detrend.csv | 28_c3_detrend_panel.png | R8,MS | **OK** |
| 29 | 29_c3_within_variance_check.py | 1.6.0 | 02_cluster_stats.csv, 01_wells_clean_maod.csv, 01_locations.csv, 07_coeff_maps_data.csv, 25_01_panel_fit_parameters.csv, 25_02_per_well_summer_min_slopes.csv, 18_wtf_01_well_sy_estimates.csv (Script 17 event-median Sy), Features.kml | 29_within_c3_variance.csv, 29_univariate_R2.csv, 29_drop_one.csv, 29_report_numbers.csv, 29_within_c3_variance_results.md | 29_within_c3_variance_panel.png | R8,MS | **OK** |
| 30 | 30_c4_drainage_identifiability.py | 2.3.0 | 01_climate.csv, 01_wells_clean.csv, 02_cluster_stats.csv | 30_c4_identifiability_by_cluster.csv, 30_c4_perwell_beta3.csv, 30_c4_report_numbers.csv | 30_c4_drainage_identifiability.png | R8,MS | **DRIFT** |
| 31 | 31_cluster_validation.py | 1.4.1 | 01_dry_depths.csv, 01_well_elevations.csv, 01_wells_clean.csv, 03_master_data.csv, **18_wtf_01_well_sy_estimates.csv** (per-well Sy_median; D-038) | 31_validation_summary.csv, 31_forest_confusion.csv, 31_method_robustness_ari.csv, 31_forest_borderline.csv | 31_cluster_validation_panel.png | R8,MS | **OK** |
| 31b | 31b_separation_vs_recoverability.py | 1.3.0 | 01_dry_depths.csv, 01_well_elevations.csv, 01_wells_clean.csv, 03_master_data.csv | 31b_separation_vs_recoverability.csv | 31b_separation_vs_recoverability.png | R8,MS | **OK** |
| 32 | 32_differential_movement.py | 1.4.0 | 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv | 32_differential_movement_per_well.csv, 32_site_mean_trend.csv (4 rows at 1.3.0: basis × period, + detectability columns), 32_results.txt | 32_differential_movement_2005_2025.png, 32_differential_movement_2011_2025.png | R8,MS,SM | **GAP** |
| 33 | 33_envelope_amplification.py | 1.4.0 | 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv, 06_pear_membership_audit_sitewide.csv | 33_envelope_per_well.csv, 33_envelope_per_well_recent.csv, 33_results.txt | 33_amplification_field.png (Fig 66), 33_dry_spring_depth.png (Fig 67), +_recent variants | R8,MS,SM | **OK** |
| 34 | 34_window_sensitivity.py | 0.6.0 | 00_01_annual_climate_summary.csv, 26_msl_annual_per_well.csv, 32_site_mean_trend.csv (filtered on config.DIFF_SITE_MEAN_CITED_BASIS at 0.6.0) | 34_window_matrix.csv, 34_results.txt | 34_window_sensitivity.png | R8,MS,SM | **OK*** |
| 35 | 35_per_well_amplification.py | 1.2.0 | 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv, 06_pear_membership_audit_sitewide.csv | 35_per_well_amplification.csv, 35_results.txt | 35_coefficient_markers.png, 35_ssm_calibration.png | R8,MS,SM | **OK** |
| 36 | 36_absolute_climate_trend.py | 1.4.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv | 36_absolute_climate_trend_per_well.csv, 36_results.txt | 36_absolute_climate_trend_2005_2025.png, 36_absolute_climate_trend_2011_2025.png | R8,MS,SM | **OK** |
| 37 | 37_driver_validation.py | 3.4.0 | 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv, 10a_report_numbers.csv, 25_01_panel_fit_parameters.csv, 36_absolute_climate_trend_per_well.csv | 37_driver_validation_per_well.csv, 37_scale_factors_by_window.csv, 37_results.txt | 37_predicted_vs_observed.png, 37_residual_map.png, 37_implied_delta0_trajectory.png | R8,MS | **OK** |
| 37b | 37b_driver_footing.py | 1.3.0 | 01_wells_clean.csv, 03_master_data.csv, 09_scrape_03_baci_shifts.csv, 10a_report_numbers.csv, 10m_report_numbers.csv, 20_report_numbers.csv, 25_01_panel_fit_parameters.csv | 37b_driver_footing.csv, 37b_results.txt | 37b_driver_footing.png | R8,MS | **OK** |
| 38 | 38_coastal_transect.py | 1.6.0 | 01_locations.csv, 01_wells_clean_maod.csv, 25_01_panel_fit_parameters.csv | 38_transect.csv, 38_results.txt, 38_report_numbers.csv | 38_transect_profile.jpg, 38_coast_inland_difference.jpg | R8,MS | **OK** |
| 39 | 39_ccw_hindcast.py | 1.3.0 | 01_climate.csv, 01_locations.csv, 01_wells_clean.csv, 03_master_data.csv | 39_01_hindcast_per_well.csv, 39_02_hindcast_series.csv, 39_03_beta1_sensitivity.csv, 39_05_full_hindcast_site.csv, 39_06_full_hindcast_decadal.csv, 39_results.txt | 39_04_hindcast.png, 39_07_full_hindcast.png | MS | **OK** |
| 40 | 40_shoreline_retreat.py | 1.6.3 | 25_01_panel_fit_parameters.csv, 25_12_window_sweep.csv, coast1899.kml, coast2006.kml, coast2017.kml, coast2021.kml, coast2026.kml, coast2006B_blind.kml, coast2019-09-11.kml, coast2020-03-31.kml, site_boundary.kml, newborough_dem.tif | 40_01_epoch_series.csv, 40_02_normals.csv, 40_03_control.csv, 40_04_generalisation.csv, 40_05_dtm_profile.csv, 40_06_coastal_sensitivity.csv, 40_07_storm_pair.csv, 40_report_numbers.csv | 40_01_alongshore_profile.png | — | **OK** — headline EMITTED 2026-08-29 (D-089): all three gate tests pass on the blind repeat-tracing control. rate_m_yr is citable under D-006. The STORM PAIR (coast2019-09-11 / coast2020-03-31, D-098) is a separate registry and emits NO rate at all: displacement plus the interval in days. Instance tag `winter2019_20`, read from the registry row and guarded by _check_storm_tags(); it names both calendar years so it reads correctly under either year convention (D-098, second note 2026-08-30) |
| 41 | 41_canopy_cover.py | 2.2.1 | data/geo/aerial_manifest.csv + the dated aerial frames it names (NOT in the repository by default — D-081), broadleaf_restock.kml, clearfell.kml, Features.kml (Forest, Felling experiment), site_boundary.kml, 01_locations.csv (registration control points) | 41_01_canopy_index.csv, 41_02_change_events.csv, 41_03_registration.csv, 41_report_numbers.csv | 41_04_canopy_series.png | — | **OK** |

*(Not rows: `gen_grid_lay.py`, `run_09_scraping.py`, `run_10_clearfell.py` — utility/orchestration.)*
