# Fine sweep of the proof copies (reading pass 2) — findings for Martin's ruling, 2026-09-29

Fifteen Sonnet readers (brief `scratch/sweep/BRIEF.md`, in the cloud clone at d601d58 + today's mirrors) read every number of the report the first reading pass had not confirmed: 4,148 rows. Verdicts: confirm 2,139; deny 1,120 (238 of them `needs emit`: a real pipeline quantity no committed file carries); literal 784 (config constants, arbitrary choices, coordinates, references, equation constants); **stale 96**; unsure 9. Merged into `tools/proof_reading_verdicts.csv` (batch `2026-09-29 sweep`) and painted on the proof page (artifact v19; proof_copy 1.24.0). On the page: report9 traced 2,022 → 2,402, near-ties 247 → 5, elsewhere 57 → 0; denied 15 → 101 (the emit list is red by design until the scripts emit); stale 6 → 65. Every reader's summary is in `scratch/sweep/` beside its CSV.

## 1. Stale — the document quotes a value the committed source does not carry

Each row: chapter § · number as printed · the reader's reason · the committed value. **Nothing has been edited**: some are one-unit roundings Martin's 0.01 rule may wave through, some are real drifts, a few are scientific inconsistencies. Ruling wanted per row or per class.

| doc | § | printed | reason | committed |
|---|---|---|---|---|
| report |  | −6.2 | the sentence quotes the C4 UKCP18 2050s annual water equivalent, whose committed median is -6.143 (mean -6.257), not -6.2; the sibling -10.9 for the 2080s is the median, so the median is the like-for-like row. The attrib | ukcp18_2050s / annual / C4 · we_median_mm = -6.14338 [19_scenario_summary.csv] |
| report8 | 3.2.3 Cluster Determination  | 0.49 | sentence gives the western residual (C3) median per-well stability as 0.49; committed well-bootstrap median is 0.3827 (month-bootstrap median 0.476); 0.494 is a single well, not the median | C3 (Western Residual) · cluster_stability_median = 0.38273 [02_report_numbers.csv] |
| report8 | 3.2.3 Cluster Determination  | 0.40 | sentence says silhouette at k = 5 is 0.40; committed value is 0.3727 (0.37) | silhouette_k5 = 0.37267 [02_report_numbers.csv] |
| report8 | 3.3.2 Classification Criteri | 46 | sentence says the MCA flag is raised for 46 of 66 reference wells; 05_pear_membership_audit.csv has MCA_Flag True for 44 (three or more centroids at r > 0.90, recounted from the r columns); no report-numbers row carries  | needs emit: Script 05 should emit the MCA-flag count (committed audit gives 44, not 46) |
| report8 | 3.4 Using Models to derive t | 0.28 | sentence says the Pastas base level is 0.28 m lower than Model B on the identified full record; committed median difference is -0.2015 m (the 0.276 attributed is the C1 cluster row of a different group) | pastas_vs_ssmB_base_level_m_median_diff_identified_full = -0.201519 [48_report_numbers.csv] |
| report8 | 3.4.1 Modelling the Cluster  | 4.8 | sentence gives the upper end of C3 per-well beta1 as 4.8; the committed C3 maximum is 5.514 (T41a) on the comparison window and 5.296 (D38) on the full record; 4.8 was the maximum before D-196 moved D38, T41a and others  | needs emit: Script 03 should emit the C3 per-well beta1 range; committed max is 5.514 (T41a) in 03_master_data.csv |
| report8 | 3.4.1 Modelling the Cluster  | 17 | sentence gives forest-interior (C4) half-lives as "about 17 to 82 months"; committed per-well full-record half-lives (D-192) have min 16.30 months | C4 (Main Forest) · t_half_min = 16.29982 [18_wtf_08_cluster_half_life_summary.csv] |
| report8 | 3.4.1 Modelling the Cluster  | 82 | sentence gives the maximum forest-interior half-life as 82 months; committed C4 maximum is 41.58 months (CEH34, full record) | C4 (Main Forest) · t_half_max = 41.58021 [18_wtf_08_cluster_half_life_summary.csv] |
| report8 | 3.4.1 Modelling the Cluster  | 32 | sentence gives the C4 cluster median half-life as 32 months; committed C4 median is 23.00 months | C4 (Main Forest) · t_half_median = 22.99633 [18_wtf_08_cluster_half_life_summary.csv] |
| report8 | 3.7.5 Five-Year Mean Spring  | 0.8 | 9 of 1272 is 0.7075 %, which rounds to 0.7 %, not 0.8 %; the tool row (SD15b_REC) is unrelated | 0.7 (9 / 1272 = 0.7075 %) from msl5_n_annual_valid_with_interp / msl5_n_annual_valid [26_report_numbers.csv]; the percen |
| report8 | 3.8.1 Baseline Fields, Combi | 129 | the scrape edge drawdown is 128.09 mm, which rounds to 128, not 129 (the tool row is 0.1285 m, a C1 MSL5 mean, whose rounding produced the 129) | scrape_H0_mm = 128.09 [20_scrape_report_numbers.csv] |
| report8 | 3.8.1 Baseline Fields, Combi | 0.99 | the committed co-temporal vs matched-window amplification correlation is r = 0.966 (n = 68), not 0.99; the tool row is a Pastas ratio | validation_cotemporal_vs_matched_r = 0.9659 [35_report_numbers.csv] |
| report8 | 3.8.1 Baseline Fields, Combi | +230 | the upper end of the envelope is 228.96 mm, which rounds to 229, not 230; the tool row (SD15b_REC - SD16) is unrelated | window_change_envelope_max_mm = 228.96 [34_report_numbers.csv] |
| report8 | 3.8.3 Drainage Half-life Fie | 97 | the ceh13 full-record half-life is 107.9 months (b3 = 0.006426), not 97; the tool found no committed value | ceh13 · t_half_months = 107.87 [03_19_per_well_recession_full_record.csv] |
| report9 | 4.2 Network Clustering and S | 0.40 | the committed silhouette at the chosen k = 5 is 0.3727, which rounds to 0.37; 0.40 matches no k-sweep row at k = 5 (k = 6 is 0.405, k = 7 is 0.406) | silhouette_k5 = 0.372670 [02_report_numbers.csv] |
| report9 | 4.2 Network Clustering and S | 0.93 | the four stable clusters carry median co-assignments of 0.9803 (C1), 0.9875 (C2), 0.9904 (C5) and 1.0 (C4); the lowest is 0.980, so the quoted 0.93 bound is looser than, and matches, no committed value | cluster_stability_median (C1 (Lake Edge), lowest of the four stable clusters) = 0.980257 [02_report_numbers.csv] |
| report9 | 4.2.2 Cluster Mechanistic Ch | 17 | the C4 change under the common 2015 reference refit is -12.66 % in beta_3 (ref_date row of 03_13; beta_1 -1.5 %, beta_2 +1.5 %), not about 17 %; the tool matched a spring rainfall rank | C4 (Main Forest) / ref_date · beta_3_pct_delta_vs_published = -12.6564 [03_13_centroid_composition_sensitivity.csv] |
| report9 | 4.2.2 Cluster Mechanistic Ch | 3.6 | the ceh11 ground elevation is committed as 3.534 m (DGPS; 3.5 m, which report8 states); the quoted 3.6 m matches only the DEM_Ground_Elev column (3.584) | ceh11 · ground_elev_m = 3.534 [01_locations.csv] |
| report9 | 4.2.2 Cluster Mechanistic Ch | 1.6 | the distance from ceh11 to its nearest C1 well (ceh26) is committed as 1732.4 m, i.e. 1.7 km (report8 says 1.7 km), not 1.6 km; the tool matched a datum-sensitivity minimum | cluster_isolated_nearest_dist_m (ceh11, nearest C1 member ceh26) = 1732.44 m [02_report_numbers.csv] |
| report9 | 4.2.2 Cluster Mechanistic Ch | 8.6 | the lowest ground elevation among the six other C1 wells (ceh6) is committed as 8.461 m (8.5 m, which report8 states); 8.6 matches only ceh6's DEM_Ground_Elev (8.611) | C1 (Lake Edge) · cluster_others_ground_elev_min_m = 8.461 [02_report_numbers.csv] |
| report9 | 4.2.2 Cluster Mechanistic Ch | 3.6 | the ceh11 ground elevation is committed as 3.534 m (3.5 m in report8); 3.6 matches only the DEM_Ground_Elev column (3.584) | ceh11 · ground_elev_m = 3.534 [01_locations.csv] |
| report9 | 4.2.3 Recharge and Losses: A | 16 | sentence says 16 to 27 winter months; smallest committed N_winter is 15 (C4), largest 27 (C1) | C4 (Main Forest) · N_winter = 15 [16_water_bal_rec_table.csv] |
| report9 | 4.2.3 Recharge and Losses: A | 892 | sentence quotes 892 mm/yr; committed annual rainfall is 893.1 at every cluster (and 678 net vs 678.7 committed) | C1 (Lake Edge) · P_mm_yr = 893.1 [16_water_bal_vol_table.csv] |
| report9 | 4.2.4 Specific Yield Estimat | 72 | sentence says up to 72 events per well; the committed maximum is 73 (nw1) | nw1 · n_events = 73 [18_wtf_01_well_sy_estimates.csv] |
| report9 | 4.3 Checking the Clusters: P | +1.0 | sentence quotes +1.0 for the coefficient of slope_m_yr on the exponential coastal predictor; the committed univariate coefficient is 0.869 (full five-predictor model -0.205) | C3_slope_coast_coef_univariate = 0.8692 [29_report_numbers.csv] |
| report9 | 4.3 Checking the Clusters: P | 0.63 | sentence quotes eta2 = 0.63 for distance to coast; the committed eta2 is 0.577 | 1 external / ANOVA / distance to coast · statistic = 0.577 [31_validation_summary.csv] |
| report9 | 4.3 Checking the Clusters: P | 0.21 | sentence quotes ground-elevation eta2 = 0.21; the committed value is 0.217 (which rounds to 0.22, as the same paragraph later says); the tool matched the ARI of distance to coast | 1 external / ANOVA / ground elevation · statistic = 0.217 [31_validation_summary.csv] |
| report9 | 4.4 Model Benchmarking: Stat | 0.91 | sentence quotes a median one-step R2 of 0.91 for one model; committed values are 0.9208 (TLM) and 0.9242 (SSM), neither rounds to 0.91 (Table 9 prints 0.921 and 0.924) | Median one-step R2 · Traditional_Model_A = 0.9208 [08_lcsc_04_table3_benchmark_summary.csv] |
| report9 | 4.5.2 Paired BACI and Robust | −0.073 | sentence quotes CEH18 corrected net benefit after scraping as -0.073 m; the committed Net_benefit for CEH18 After_Scraping is -0.0753 (-0.075); the tool matched a climate-control centroid | Net_benefit · CEH18 · After_Scraping = -0.07525 [09_scrape_report_numbers.csv] |
| report9 | 4.5.3 Drainage Coefficient R | 0.041 | table p-value for CEH36 baseline is quoted as 0.041 but the committed P_Value is 0.04045 (0.040 at three decimals; 0.041 is a double rounding of 0.0405); the tool matched an unrelated spring-means gap | CEH36 / 1_Baseline · P_Value = 0.04045 [09_scrape_02_beta3_significance.csv] |
| report9 | 4.5.4 Summer Minima | −0.72 | sentence quotes MSL5 at CEH36 as -0.72 m at window-end 2015; committed MSL5_m_bg for ceh36 at 2015 is -0.6372 (the tool matched an unrelated CEH4 dry depth) | ceh36 / 2015 · MSL5_m_bg = -0.6372 [26_msl_5yr_per_well.csv] |
| report9 | 4.5.5 Scraping Propagation i | +0.69 | sentence quotes r = +0.69 for beta_3 increasing inland across C3 (Section 4.9.2); the committed Pearson r is 0.5752 (+0.58), which Section 4.3 and Section 4.9.2 quote | C3_beta3_vs_inland_r = 0.5752 [29_report_numbers.csv] |
| report9 | 4.5.5 Scraping Propagation i | 0.003 | sentence quotes p = 0.003 for the C3 beta_3 inland gradient; the committed p is 0.006368 (0.006, as Section 4.9.2 quotes) | C3_beta3_vs_inland_p = 0.006368 [29_report_numbers.csv] |
| report9 | 4.6.6 Coefficient Decomposit | −0.03 | Edge-tier mean db2 is quoted as -0.03 but the committed tier mean is -0.0746 (four Edge wells -0.1986, -0.0930, -0.0341, +0.0272); the attribution is an unrelated summer-min shift | quoted -0.03; committed CoeffShift_Edge_mean_db2 = -0.074625 [10e_report_numbers.csv] |
| report9 | 4.6.7 Robustness | −0.4 | transect gradient quoted -0.4 mm per 100 m; committed Transect_gradient_mm_per_100m is -0.4528 (-0.5 at one decimal, and the Figure caption already reads -0.5) | Transect_gradient_mm_per_100m = -0.4528 [10g_report_numbers.csv] |
| report9 | 4.6.7 Robustness | 0.19 | transect gradient p quoted 0.19; committed Transect_gradient_p is 0.1409 (0.14, as the Figure caption states) | Transect_gradient_p = 0.1409 [10g_report_numbers.csv] |
| report9 | 4.6.8 Temporal decay of the  | −19 | contrast between the in-block pair (CEH32, CEH33) and the outside pair, early era: committed -20.74 mm (fixed_s25 and none; -20.54 free_per_era), quoted -19; the attribution is a lambda-200 Climate sensitivity that merel | (CEH32+CEH33)-(CEH34+CEH2) / fixed_s25 / 2017-12..2020-12 · step_mm = -20.74 [10a_13_era_split.csv] |
| report9 | 4.6.8 Temporal decay of the  | −8 | same contrast, late era: committed -9.358 mm (fixed_s25 and none; -8.51 free_per_era), quoted -8; the attribution is a Forest Ctrl mixed-model coefficient (-0.0079) | (CEH32+CEH33)-(CEH34+CEH2) / fixed_s25 / 2021-01..2026-02 · step_mm = -9.358 [10a_13_era_split.csv] |
| report9 | 4.7.2 Seasonal Prediction Eq | 0.005 | coastal forest intercept p quoted 0.005; committed p_value_intercept is 0.004336 (0.004); the attribution is a Dune spring P_win_to_spr p that coincides | Coastal_Forest · p_value_intercept = 0.004336 [11_forecast_winter_transfer_functions.csv] |
| report9 | 4.7.3 Summer Drought Predict | 0.05 | caption says all coefficients are significant at p < 0.05, but the same table gives Coastal Forest p(P_summer) = 0.0515, which is not (the body text repeats the claim) | Coastal_Forest · p_value_P_summer = 0.05155 [11_forecast_summer_transfer_functions.csv] |
| report9 | 4.7.4 Spatial Distribution o | 87 | quoted 87 of 88 wells with m_P > 1.0; committed 11b_03_pflood_per_well.csv has all 88 above 1 (smallest lambda 1.058, ceh6) | ceh6 · lambda = 1.058331 [11b_03_pflood_per_well.csv] |
| report9 | 4.7.4 Spatial Distribution o | 0.98 | quoted single exception m_P = 0.98; no well in the committed per-well table has lambda <= 1 (the minimum is 1.058, ceh6), and the config constant SD16 = 0.98 the tool matched is unrelated | ceh6 · lambda = 1.058331 [11b_03_pflood_per_well.csv] |
| report9 | 4.7.4 Spatial Distribution o | 4 | quoted "remaining 4 wells"; the committed 11c per-well table has 5 wells with m_P >= 2.5 (CEH17, FE3, CEH31, CEH33, CEH30) | Unreachable count = 5 [11c_pflood_achievability_per_well.csv, category == Unreachable] |
| report9 | 4.7.4 Spatial Distribution o | 5 | quoted 5 % for the 4 remaining wells; 5 wells of 88 is 5.7 % (6 %); RANWELL_FLOOR_PCT is unrelated | Unreachable share = 5/88 = 5.7 % [11c_pflood_achievability_per_well.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | 117 | quoted 117 mm; committed C2 msl5_window_se_mm_median is 112.7 mm (both scopes), beyond the quoted digit | reference / C2 (Dune) · msl5_window_se_mm_median = 112.6837 [26_index_precision_by_cluster.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | 316 | quoted 316 mm; committed C1 ewi_se_mm_beta3_median is 302.6 mm (reference) or 312.2 mm (all) | reference / C1 (Lake Edge) · ewi_se_mm_beta3_median = 302.5616 [26_index_precision_by_cluster.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | 455 | quoted 455 mm; committed C2 value is 431.7 mm (reference) or 421.2 mm (all) | reference / C2 (Dune) · ewi_se_mm_beta3_median = 431.7395 [26_index_precision_by_cluster.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | 513 | quoted 513 mm; committed C3 value is 418.8 mm (reference) or 416.7 mm (all) | reference / C3 (Western Residual) · ewi_se_mm_beta3_median = 418.7717 [26_index_precision_by_cluster.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | 430 | quoted 430 mm; committed C5 value is 415.3 mm (reference) or 366.0 mm (all) | reference / C5 (Coastal Forest) · ewi_se_mm_beta3_median = 415.2863 [26_index_precision_by_cluster.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | 1115 | quoted 1115 mm; committed C4 value is 1014 mm (reference) or 1030 mm (all) | reference / C4 (Main Forest) · ewi_se_mm_beta3_median = 1014.0189 [26_index_precision_by_cluster.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | 3.3 | quoted lower end 3.3; committed ewi_over_msl5_ratio_beta3 minimum across clusters is 2.888 (reference, C3) or 2.859 (all) | min of ewi_over_msl5_ratio_beta3 (reference, C3) = 2.888 [26_index_precision_by_cluster.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | 6.2 | quoted upper end 6.2; committed ewi_over_msl5_ratio_beta3 maximum is 5.615 (reference, C4) or 5.704 (all) | max of ewi_over_msl5_ratio_beta3 (reference, C4) = 5.615 [26_index_precision_by_cluster.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | −0.17 | quoted Spearman r = -0.17 across the extended network; committed value is -0.0900 | extended_relSE_beta3_vs_nobs_spearman_r = -0.09002 [26_report_numbers.csv] |
| report9 | 4.8.4 Equilibrium Wetness In | 0.48 | quoted p = 0.48 for the same test; committed value is 0.7059 | extended_relSE_beta3_vs_nobs_spearman_p = 0.7059 [26_report_numbers.csv] |
| report9 | 4.9.2 Spatial Coefficient St | 0.68 | sentence says C4 and C5 mean R2 is 0.68; committed cluster means are 0.697 (C4) and 0.695 (C5), pooled 0.696, so it should read 0.70 | Model_R² · C4_mean = 0.697, C5_mean = 0.695 [10c_forest_zone_cluster_summary.csv] |
| report9 | 4.9.2 Spatial Coefficient St | 2.0 | lower end of the C4 beta_2 range in the figure text (2.0--3.8 mm/mm); committed C4 minimum is 2.062, which rounds to 2.1, so the 2.0 is stale; CEH14 beta_3 is unrelated | C4 (Main Forest) · beta_2_atmospheric_draw_min = 2.0621 [07_coeff_05_cluster_ranges.csv] |
| report9 | 4.9.4 Per-Well Forest Zone A | −0.021 | ceh14 beta_3 is -0.0203 (committed), not -0.021; the tool took an unrelated hydrograph separation | CEH14_beta3 = -0.0202915 [07_report_numbers.csv] |
| report9 | 4.10.3 What the fit cannot r | −0.10 | the committed c_far is -0.3 (-0.2989), not -0.10; the same section and 4.10.2 quote -0.3; SE 0.55 matches | forest_free / linear_capped · c_mm_yr = -0.3 [25_01_panel_fit_parameters.csv] |
| report9 | 4.11 Management influence on | 230 | the figure caption gives lambda as 230 m; the committed scrape lambda is 222.9 m, which the text of the same section quotes as 220 m (nearest 10 m) | scrape_lambda_m = 222.9294 [20_scrape_report_numbers.csv] |
| report9 | 4.12 Combined Driver Assessm | 117 | C2 window SE is 112.68 mm (= 251.97/sqrt(5)); the report says 117 | reference / C2 (Dune) · msl5_window_se_mm_median = 112.6837 [26_index_precision_by_cluster.csv] |
| report9 | 4.12 Combined Driver Assessm | −0.14 | lower end of the cluster-mean lag-1 range: committed minimum is C3 -0.161 (65-well scope; -0.159 reference), not -0.14 | all · C3 (Western Residual) · rho_lag1_mean = -0.1614 [26_index_precision_by_cluster.csv] |
| report9 | 4.12 Combined Driver Assessm | +0.01 | upper end of the cluster-mean lag-1 range: committed maximum is C5 +0.089 in the 65-well scope (+0.005 only in the 61-well reference scope), not +0.01 | all · C5 (Coastal Forest) · rho_lag1_mean = 0.0890 [26_index_precision_by_cluster.csv] |
| report9 | 4.12 Combined Driver Assessm | 0.17 | p of that Spearman test is 0.262, not 0.17 (r = 0.141 on 65 wells) | rho_lag1_vs_tR_spearman_p = 0.2621 [26_report_numbers.csv] |
| report9 | 4.12 Combined Driver Assessm | 72 | the committed network row maps 74 wells over 2011-2025 (the sentence says 72, and "eight" significant against 13 committed) | network (mapped wells) · 2011_2025 · n_wells = 74 [32_cluster_summary.csv] |
| report9 | 4.12 Combined Driver Assessm | 13 | over 2005-2025 the committed network row has 12 significant wells, not 13 | network (mapped wells) · 2005_2025 · n_sig_ar = 12 [32_cluster_summary.csv] |
| report9 | 4.12 Combined Driver Assessm | 75 | over 2005-2025 the committed network row maps 77 wells, not 75 | network (mapped wells) · 2005_2025 · n_wells = 77 [32_cluster_summary.csv] |
| report9 | 4.12 Combined Driver Assessm | 0.75 | the committed site-mean dry-to-wet spring swing is 774 mm (33_results.txt "Tier-A site-mean swing 774 mm"; network row of the cluster summary); 0.75 m is a docstring figure in Script 33 (not the SD15b_REC threshold, whic | canonical / network (unflagged wells) · swing_mm_mean = 774.4254 [33_cluster_summary.csv] |
| report9 | 4.12 Combined Driver Assessm | +0.8 | the committed Pearson r of amplification with beta2 is +0.66 (n = 64), which section 4.12 itself quotes two paragraphs later; no committed file gives +0.8 or a forest-excluded variant | amp_vs_beta2_r = 0.6574 [35_report_numbers.csv] |
| report9 | 4.12 Combined Driver Assessm | 0.73 | the same site-mean swing as above: the committed value is 774 mm, not 0.73 m (Script 33 comment carries 0.73) | canonical / network (unflagged wells) · swing_mm_mean = 774.4254 [33_cluster_summary.csv] |
| report9 | 4.12 Combined Driver Assessm | +0.3 | the committed C2 (Dune) cluster mean differential slope over 2011-2025 is -0.62, not +0.3 | 2011_2025 / C2 (Dune) · slope_mean_mm_yr = -0.616493 [32_cluster_summary.csv] |
| report9 | 4.13.1 Climate Scenario Proj | +0.055 | site-wide 2080s winter mean is 0.05555 (SITE dh_mean_m), which rounds to +0.056 not +0.055; the attribution (C3 median 0.0546) is the wrong row, and the value sits on a rounding boundary | ukcp18_2080s / winter / SITE · dh_mean_m = 0.0555 [19_scenario_summary.csv] (unrounded 0.055547) |
| report9 | 4.13.1 Climate Scenario Proj | −21 | upper end of the 2050s range is C4 (-0.021518 m = -21.5 mm, rounds to -22); the attribution names C1 at 2080s, the wrong row, and the quoted -21 is a rounding-boundary flip | msl5_shift_mean_m_c4_main_forest_2050s = -0.021518 [26b_report_numbers.csv] |
| report9 | 4.13.1 Climate Scenario Proj | −69 | upper end of the 2050s summer range is C2 at -0.0681 m (-68 mm), not -69; the attribution is a count with no source | ukcp18_2050s / summer / C2 · dh_mean_m = -0.0681 [19_scenario_summary.csv] |
| report9 | 4.13.1 Climate Scenario Proj | −69 | lower end of the 2080s summer range is C5 at -0.0697 m (-70 mm), not -69 | ukcp18_2080s / summer / C5 · dh_mean_m = -0.0697 [19_scenario_summary.csv] |
| report9 | 4.13.1 Climate Scenario Proj | −131 | upper end of the 2080s summer range is C2 at -0.1291 m (-129 mm), which agrees with the -0.129 quoted earlier in the section; -131 is the NW5 well value, not a cluster mean | ukcp18_2080s / summer / C2 · dh_mean_m = -0.1291 [19_scenario_summary.csv] |
| report9 | 4.13.2 Forest Management Sce | +0.020 | C5 broadleaf winter cluster mean is 0.02053 (rounds to +0.021, and Script 21 gives 0.0215); the attribution is the C5 median (0.0196), a different statistic than the C4 mean beside it; rounding-boundary case | broadleaf / winter / C5 · dh_mean_m = 0.0205 [19_scenario_summary.csv] (unrounded 0.020529) |
| report9 | 4.14.2 The 1951--53 record | 0.80 | highest bias-removed efficiency over all pairings is 0.7902 (site 8, nw5), which rounds to 0.79 not 0.80; the attribution is the mean r, a different statistic | 8 (nw5) · nse_after_offset = 0.7902 [44_04_hindcast_metrics.csv] |
| report10 | 5.1.1 Cluster Classification | +1.0 | the C3 within-cluster panel regression (Script 29) returns a coastal-predictor coefficient of +0.87 alone and -0.21 in the five-predictor model, and 29's own reading says it does not validate the exponential form; +1.0 i | C3_slope_coast_coef_univariate = 0.8692191054107624 (five-predictor C3_slope_coast_coef_full = -0.205005912431151) [29_r |
| report10 | 5.2.3 The C4 Main Forest Dra | 0.57 | the bootstrap 95 % CI lower bound for C1 beta_2 is 0.5545 (renders 0.55), not 0.57; sibling of the upper bound. | C1 (Lake Edge) · beta_2_lo = 0.554453 [03_05_bootstrap_ci.csv] |
| report10 | 5.2.3 The C4 Main Forest Dra | 1.19 | the bootstrap 95 % CI upper bound for C1 beta_2 is 1.1826 (renders 1.18), not 1.19. | C1 (Lake Edge) · beta_2_hi = 1.182591 [03_05_bootstrap_ci.csv] |
| report10 | 5.2.5 Seasonal Prediction an | −71 | the smallest 2080s summer-minimum deepening is C5 -0.0697 m (-70 mm), not -71. | ukcp18_2080s summer C5 · dh_mean_m = -0.0697 [19_scenario_summary.csv] (also Delta smin_80s in 26c_results.txt) |
| report10 | 5.2.5 Seasonal Prediction an | −134 | the largest 2080s summer-minimum deepening is C2 -0.1291 m (-129 mm), not -134. | ukcp18_2080s summer C2 · dh_mean_m = -0.1291 [19_scenario_summary.csv] (scenario_dh_mean_ukcp18_2080s_summer_C2 = -0.129 |
| report10 | 5.3.2 Drainage Decay and the | 892 | the committed annual rainfall applied to every cluster is 893.1 mm/yr (Table 7 source), not 892 (the throughfall to 678 has the same one-millimetre offset: P_net 678.7). | P_mm_yr = 893.1 (P_net_mm_yr C4/C5 = 678.7) [16_water_bal_vol_table.csv] |
| report10 | 5.6.3 Broadleaf Conversion:  | 100 | the committed coordinates place CEH2 346 m from NW10 (01_locations.csv E,N), not 100 m; LCSC_DATA_LIMIT = 100 is an unrelated window constant. The distance is not emitted. | 01_locations.csv: nw10 (241435, 364325) to ceh2 = 346.3 m; needs emit if the 100 m is meant as an inter-well distance |
| report10 | 5.6.3 Broadleaf Conversion:  | 100 | CEH2 lies 346 m from NW10 by the committed coordinates, not 100 m downslope; the count-class '100' has no source and 01_locations.csv contradicts it. | 01_locations.csv: nw10 to ceh2 = 346.3 m (ground_elev_m nw10 11.66, ceh2 11.32) |
| report10 | 5.7 Spatial Groundwater Mode | −0.017 | the 2050s site-wide mean annual delta-h is -0.0178 m/month (renders -0.018; report9 quotes -0.018); -0.017 is a truncation, one unit at the quoted precision. | ukcp18_2050s / annual / SITE · dh_mean_m = -0.0178 [19_scenario_summary.csv] |
| report10 | 5.7 Spatial Groundwater Mode | −0.030 | the 2080s site-wide mean annual delta-h is -0.0319 m/month (renders -0.032; report9 quotes -0.032), not -0.030. | ukcp18_2080s / annual / SITE · dh_mean_m = -0.0319 [19_scenario_summary.csv] |
| report10 | 5.7.2 Forest Management Scen | −36 | C5 summer-minimum decline (mm/yr): no committed value is -36; the C5 rows in the summer/spring comparison read -29.1 (summer centroid) and -31.98 (balanced annual mean) | C5 (Coastal Forest) · observed_centroid_mm_yr_summer = -29.1 [25_08_spring_vs_summer_comparison.csv] |
| report10 | 5.7.2 Forest Management Scen | −38 | C5 spring-mean decline (mm/yr): no committed value is -38; the C5 spring rows read -23.5 (centroid) and -23.91 (balanced annual mean) | C5 (Coastal Forest) · observed_centroid_mm_yr_spring = -23.5 [25_08_spring_vs_summer_comparison.csv] |
| report10 | 5.7.5 Parametric Prediction  | 72 | number of wells mapped in the 2011--2025 differential-movement fit: the committed value is 74, not 72 (the tool's 72 is the common wells of a Script 34 window pair) | network (mapped wells) · n_wells = 74 [32_cluster_summary.csv, period 2011_2025] |
| report10 | 5.7.5 Parametric Prediction  | 0.75 | network-mean dry-to-wet spring swing: the committed value is 0.774 m (774 mm, canonical panel), not 0.75 m; the config constant SD15b_REC = 0.75 the tool cited is a digit coincidence | network (unflagged wells) · swing_mm_mean = 774.4 [33_cluster_summary.csv, panel canonical] |
| report10 | 5.7.5 Parametric Prediction  | 15 | C2 (open dune) recession time 1/beta_3 at the centroid is 15.9 months (would be quoted 16), not 15; the tool's C4 n_years_median = 15 is a digit coincidence | C2 (Dune) · centroid_recession_time_months = 15.90 [30_c4_report_numbers.csv] |
| report10 | 5.8.1 P_flood Recoverability | 1.97 | the deepest C3 well's m_P is 2.003 (WMC3), not 1.97; the tool's config row (delta_0_se = 1.97) is a coincidence | wmc3 · lambda = 2.003 [11b_03_pflood_per_well.csv] |
| report10 | 5.8.2 Climate Trajectory as  | −21 | edge drawdown of a single 6 m storm retreat: the committed value is -80.9 mm (6 m x 13.48 mm/m, after the D-090 measured-rate correction), not about -21 mm | coastal_6m_storm_head_mm (distance 0) = -80.87 [09f_01_reach_profile.csv]; also coastal_h0 = 80.87 [20_report_numbers.cs |
| report10 | 5.8.2 Climate Trajectory as  | 157 | 5 x delta_0 at the toe: the committed 5-yr coastal head at distance 0 is -156.4 mm (delta_0 = 31.28), not 157 mm | coastal_5yr_head_mm (distance 0) = -156.40 [09f_01_reach_profile.csv] |
| report10 | 5.8.2 Climate Trajectory as  | 12 | C3 half-life is 11.25 months at the centroid (t_half_A_months), quoted 'about 12'; the tool's BACI_DETECT_MIN_ERA_MONTHS = 12 is a coincidence | C3 (Western Residual) · t_half_A_months = 11.25 [03_16_model_b_persistence.csv, level centroid] |

## 2. Needs emit — quantities the text quotes that no committed file carries

Grouped by the script the reader named. A `needs emit` stays red on the page until the script emits it (then the reader's `better` resolves and it paints green on its own). Script 00 1.14.0 and Script 01 1.25.0 already cover the RAF Valley distance and the 66/22/88 counts (run pending).


**Script 00** (17 rows)

- report11 §6.4 Thornthwaite PET: `631` — Script 00 should emit the 1931-1960 mean annual PET (630.79 mm)
- report11 §6.4 Thornthwaite PET: `650` — Script 00 should emit the 1996-2025 mean annual PET (649.74 mm)
- report11 §6.4 Thornthwaite PET: `16` — Script 00 (or 12) should emit the distance from RAF Valley station to the monitoring network (16.4 km to the well centroid)
- report8 §3.1.2 Climate Data: `16` — Script 00 should emit raf_valley_distance_km (16.27 km, coded in 00_climate_summary.py 1.14.0, awaiting regenerated 00_report_numbers.csv)
- report9 §4.1.1 Climate Record: `50` — Script 00 should emit the typical range of the 12-month rolling mean of monthly PET (5th-95th percentile of the series I computed from 01_climate.csv is 49.9-56.2 mm/month; full min-max 32.8-58.0)
- report9 §4.1.1 Climate Record: `55` — Script 00 should emit the typical range of the 12-month rolling mean of monthly PET (see the 50 row; 5th-95th percentile 49.9-56.2 mm/month)
- report9 §4.1.2 Well Network: `0.77` — Script 00 should emit the network mean water level across all reference wells and months (-0.7681 m, pooled well-months of 01_wells_reference.csv)
- report9 §4.1.2 Well Network: `0.68` — Script 00 should emit the median Seasonal_amplitude_m of the 66 reference wells (-0.6828 m, August minus February)
- report9 §4.1.2 Well Network: `11` — Script 00 should emit the count of reference wells with Mean_Winter_Max_m above ground (11)
- report9 §4.7.4 Spatial Distri: `745` — Script 00 should emit the wettest Oct-Mar winter total (745.0 mm in 2001) from 01_climate.csv
- report9 §4.7.4 Spatial Distri: `1.51` — Script 00 should emit the wettest-winter multiple of the mean Oct-Mar winter (1.508)
- report9 §4.7.4 Spatial Distri: `60` — Script 00 or 11b should emit the wettest winter as a share of the m_P = 2.5 demand (60.3 %)
- report9 §4.11 Management infl: `88` — Script 00 or 01 should emit the dipwell count of the network (88 = 66 reference + 22 extended)
- report10 §5 Discussion: `88` — Script 00 (or 01) should emit the dipwell total (88 = 66 reference + 22 extended) and n_extended_wells = 22 to a report_numbers file
- report10 §5.7.5 Parametric Pre: `0.5` — Script 00 should emit the trend p-values of total summer PET and summer rainfall over 1931-2025 (the sentence quotes p > 0.5)
- report10 §5.8.1 P_flood Recove: `745` — Script 00 or 11b should emit the wettest winter rainfall total of the RAF Valley record (745 mm, winter 2001) and its ratio to the climatological mean (1.51)

**Script 01** (18 rows)

- report §: `88` — Script 01 should emit the number of dipwells in the active network (88 = 66 reference + 22 extended, excluding the Llyn Rhos-Ddu gauge)
- report7 §2 Study Site: `22` — Script 01 should emit the number of extended-network dipwells (22)
- report8 §3.1.1 Groundwater Re: `22` — Script 01 should emit wells_extended_n (22; coded in 01_data_prep.py 1.25.0, not yet in the committed 01_report_numbers.csv)
- report8 §3.1.1 Groundwater Re: `88` — Script 01 should emit wells_classified_n (88 = 66 reference + 22 extended; coded in 01_data_prep.py 1.25.0, awaiting a regenerated 01_report_numbers.csv)
- report8 §3.1.1 Groundwater Re: `22` — Script 01 should emit wells_extended_n (22; coded in 01_data_prep.py 1.25.0, awaiting a regenerated 01_report_numbers.csv)
- report8 §3.5.3 Dune Scraping : `90` — Script 01 should emit the CEH36 minus CEH4 distance-to-coast difference (92.2 m from dist_coast_m 312.9 - 220.7)
- report8 §3.5.3 Dune Scraping : `85` — Script 01 should emit the CEH21 minus CEH22 distance-to-coast difference (85.3 m from dist_coast_m 232.0 - 146.7)
- report8 §3.7.4 Network-Scale : `15` — Script 01 (or 25) should emit the length of the committed west-facing Caernarfon Bay HWM polyline used for dist_coast_m, in km (quoted as 15)
- report9 §4.2.1 Cluster Hydrog: `13.32` — Script 01 or 02 should emit per-well mean water-table elevation (m AOD) for the reference wells (ceh14 = 13.3319, network maximum)
- report9 §4.7.4 Spatial Distri: `22` — Script 01 (or 00) should emit the extended-network well count (22)
- report9 §4.9 Spatial Groundwa: `88` — Script 01 (or 05/06) should emit classified_network_n_wells (88 = 66 reference + 22 extended)
- report9 §4.9 Spatial Groundwa: `22` — Script 01 (or 06) should emit extended_n_wells (22)
- report9 §4.13.2 Forest Manage: `66` — Script 01 should emit n_reference_wells (66)
- report10 §5.6.3 Broadleaf Conv: `90` — Script 01 (or 12) should emit the NW11-NW13 distance (91.8 m from E,N in 01_locations.csv)

**Script 02** (11 rows)

- report8 §3.3.1 Cluster Member: `5` — Script 02 should emit the chosen k / number of clusters (5) and per-cluster well counts (C1 7, C2 19, C3 26, C4 9, C5 5) as report-numbers rows
- report8 §3.4.4 Within-Forest : `14` — Script 02 should emit per-cluster well counts (C4 9, C5 5; forest zone 14) as report-numbers rows
- report9 §4.2 Network Clusteri: `1.0` — Script 02 should emit the final Ward merge distance of the reference dendrogram (0.9883)
- report9 §4.2.1 Cluster Hydrog: `0.3` — Script 02 should emit the C3 minus C1/C2 mean-level offset (C3-C2 = 0.2669 m, C3-C1 = 0.3871 m)
- report9 §4.2.1 Cluster Hydrog: `0.6` — Script 02 should emit the C4 minus C3 mean-level offset (0.5666 m)
- report9 §4.2.1 Cluster Hydrog: `7.45` — Script 02 (or 01b) should emit the network mean water-table elevation over the 66 reference wells (7.4486 m AOD)
- report9 §4.2.1 Cluster Hydrog: `2.1` — Script 02 should emit the per-cluster post-2018 p90-p10 max:min ratio (C3 = 2.135)
- report10 §5.7.2 Forest Managem: `14` — Script 02 should emit the forest-cluster well count (C4 9 + C5 5 = 14; 02_report_numbers.csv carries n = 9 and n = 5 only in notes)

**Script 03** (10 rows)

- report8 §3.4 Using Models to : `0.09` — Script 03 should emit the per-cluster R2 span across the admissible datum range (C1 0.0846 from 03_08_datum_sensitivity.csv)
- report8 §3.4.1 Modelling the : `2.3` — Script 03 should emit the C3 per-well beta1 range (min 2.332 CEH21, max 5.514 T41a on the comparison window)
- report9 §4.2.1 Cluster Hydrog: `9.37` — Script 03 (or 02) should emit the C1 mean water-table elevation excluding ceh11 (9.3657 m AOD)
- report9 §4.9.1 Datum Sensitiv: `1.45` — Script 03 should emit the network median of max_R2_datum (1.45 m, from 03_09_well_optimal_datums.csv; the 03_18 all-clusters row leaves well_median_max_R2_datum_m blank)
- report9 §4.9.1 Datum Sensitiv: `0.014` — Script 03 should emit the network median r2 gain of per-well optimal over uniform datum (0.014239, median of R2_gain_max_vs_uniform in 03_09_well_optimal_datums.csv)
- report10 §5.6.3 Broadleaf Conv: `2.333` — Script 03 (or 07) should emit the C4 per-well median beta_1 (2.33289 = ceh34)
- report10 §5.6.3 Broadleaf Conv: `2.581` — Script 03 (or 07) should emit the C4 per-well median beta_2 (2.58117 = ceh34)
- report10 §5.8.1 P_flood Recove: `8` — Script 03 should emit per-cluster recession time 1/beta_3 range and median at the well level (C1: 7.4 to 11.4, median 10.2 months)

**Script 05** (10 rows)

- report8 §3.3.2 Classification: `16` — Script 05 should emit the number of wells changing Core/Fuzzy tier at delta-r 0.03 (16) and 0.10 (14), recomputed from 05_pear_membership_audit.csv
- report9 §4.3 Checking the Clu: `60` — Script 05 should emit n_confirmed (60 of 66; Class != Spy)
- report9 §4.3 Checking the Clu: `19` — Script 05 should emit n_core (19), n_fuzzy (41), n_spy (6) from Class
- report9 §4.3 Checking the Clu: `44` — Script 05 should emit n_mca_flagged (44 of 66)
- report9 §4.3 Checking the Clu: `22` — Script 05 should emit the MCA_Cluster_Label counts (C1/C2/C3 22, C2/C3/C5 13, C3/C4/C5 8, C2/C3/C4 1)

**Script 06** (2 rows)

- report9 §4.3 Checking the Clu: `3` — Script 06 should emit n_ext_core (3) and n_ext_fuzzy (19) from Status

**Script 07** (1 rows)

- report9 §4.2.2 Cluster Mechan: `−0.01` — Script 07 should emit C4_beta2_beta3_corr_excl_ceh13_ceh14 (-0.012976)

**Script 08** (2 rows)

- report12 §7 Conclusions: `1` — Script 08 should emit the number of wells with negative iterative NSE under the SSM (1) and the TLM (11)
- report12 §7 Conclusions: `11` — Script 08 should emit the number of wells with negative iterative NSE under the TLM (11) and the SSM (1)

**Script 10** (14 rows)

- report §: `17` — Script 10 should emit the number of wells in the five-tier BACI network (17)
- report8 §3.5.4 Clearfell BACI: `17` — Script 10 should emit the clearfell-BACI well count (17 = 1 + 4 + 5 + 2 + 5)
- report8 §3.5.4 Clearfell BACI: `752` — Script 10 should emit each control well distance from the felling centroid (forest controls 306 to 752 m; NW10 = 752.5 m)
- report8 §3.5.4 Clearfell BACI: `215` — Script 10 should emit each control well distance from the felling centroid (climate controls 215 to 1010 m; NW7 = 214.8 m)
- report8 §3.5.4 Clearfell BACI: `12` — Script 10 should emit the pooled control-well count (12 = 5 forest + 2 coastal + 5 climate)
- report8 §3.5.4 Clearfell BACI: `20` — Script 10 should emit the FE1 distance to the clearfell boundary (about 20 m)
- report9 §4.6.1 Interpretive C: `28` — Script 10 should emit the months of FE1 and FE2 record before CLEARFELL_DATE_ISO (01_wells_extended.csv has 29 monthly readings, Jul 2015 to Nov 2017; the text says approximately 28)
- report9 §4.6.1 Interpretive C: `32` — Script 10 should emit months from SCRAPING_DATE_ISO (2015-04-01) to CLEARFELL_DATE_ISO (2017-12-01) (= 32)
- report15 §10.1 Data Availabili: `17` — Script 10 should emit the number of wells in the clearfell BACI design (sentence quotes 17; not computed here)

**Script 11** (1 rows)

- report8 §3.6.3 Algebraic Deri: `77` — Script 11 should emit alpha^n for each cluster (C2 Oct-Jan, n = 4: 0.7712) and the surviving share as a percentage (77.12 %)

**Script 12** (3 rows)

- report6 §1 Introduction: `4.4` — Script 12 (or 13) should emit the clearfell polygon area in ha (about 4.4 ha, from data/geo/clearfell.kml)
- report7 §2 Study Site: `0.6` — Script 12 (or 13) should emit the clearfell area as a share of the plantation (4.4/700 = 0.63 %)

**Script 14** (8 rows)

- report12 §7 Conclusions: `2.5` — Script 14 should emit the C5:C1 summer-trend ratio (2.53)
- report9 §4.8.1 Summer and Win: `14` — Script 14 should emit the count of years each cluster summer minimum sat below SD16 (C3 = 14 of 21, counted from 14_annual_extremes.csv Summer_Min < -0.98)
- report9 §4.8.1 Summer and Win: `18` — Script 14 should emit the count of years each cluster summer minimum sat below SD16 (C5 = 18 of 20, counted from 14_annual_extremes.csv)
- report9 §4.8.1 Summer and Win: `20` — Script 14 should emit the count of years each cluster summer minimum sat below SD15b (C2 = 20 of 21, counted from 14_annual_extremes.csv Summer_Min < -0.61)
- report9 §4.8.1 Summer and Win: `2.5` — Script 14 should emit the C5:C1 ratio of summer trend slopes (2.53 from 14_summer_trend_stats.csv)
- report9 §4.8.1 Summer and Win: `1.7` — Script 14 should emit the C5:C3 ratio of summer trend slopes (1.66 from 14_summer_trend_stats.csv)
- report10 §5.7.2 Forest Managem: `2.5` — Script 14 should emit the C5:C1 ratio of full-record summer-minimum slopes (2.53 from 14_summer_trend_stats.csv Slope_m_per_yr, C5 -0.0291 over C1 -0.0115)

**Script 15** (1 rows)

- report9 §4.4 Model Benchmarki: `0.43` — Script 15 should emit the 1/e decay depth 1/Best_Kappa per cluster (C1 = 0.435 m, from Best_Kappa 2.3 m-1 in 15_report_numbers.csv)

**Script 17** (4 rows)

- report9 §4.2.4 Specific Yield: `+0.09` — Script 17 should emit the clip shift (Sy_event_median_unclipped - Sy_event_median) per cluster (C1 +0.0910, C5 +0.2531)
- report9 §4.2.4 Specific Yield: `1.27` — Script 17 should emit the mean ratio Sy_OLS_winter / Sy_event_median across clusters (1.2652) and the count of clusters with ratio > 1 (4)
- report9 §4.2.4 Specific Yield: `0.035` — Script 17 should emit the between-estimator range of Sy per cluster (C3: max-min of event median, rapid median, winter OLS = 0.0345)

**Script 18** (1 rows)

- report9 §4.2.4 Specific Yield: `51` — Script 18 should emit min, max and mean of n_events over the reference wells (27, 73, 51.5)

**Script 19** (1 rows)

- report9 §4.13.2 Forest Manage: `14` — Script 19 should emit n_wells in the two forest clusters (C4 9 + C5 5 = 14)

**Script 20** (22 rows)

- report8 §3.5.4 Clearfell BACI: `101` — Script 20 should emit the diffusivity Kb/Sy (100.6 m2 per day = drawdown_lambda^2 * beta3_C3 / DAYS_PER_MONTH)
- report8 §3.8.1 Baseline Field: `56` — Script 20 should emit the broadleaf-restock source magnitude (56.25 mm)
- report8 §3.8.2 Drawdown-Field: `130` — Script 20 should emit the lambda sensitivity range across K = 2-20 m/day (129 to 407 m) and across b = 3-8 m (173 to 282 m)
- report8 §3.8.2 Drawdown-Field: `410` — Script 20 should emit the lambda sensitivity range across K = 2-20 m/day (129 to 407 m)
- report8 §3.8.2 Drawdown-Field: `840` — Script 20 should emit the SLR diffusive length 2*sqrt(D*t) (857 m from the committed inputs; the text says about 840 m)
- report9 §4.9.6 Water Balance : `252` — Script 20 should emit residual_window_n_months (252)
- report9 §4.9.6 Water Balance : `54.39` — Script 20 should emit residual_pet_bar_mm (54.388) and residual_p_bar_mm (74.112)
- report9 §4.11 Management infl: `1.7` — Script 20 should emit the distance from ceh11 to each of the six eastern lake-edge wells (1.73 to 2.04 km)
- report9 §4.12 Combined Driver: `135` — Script 20 should emit the maximum of the combined scrape-plus-coastal baseline drawdown field (about 135 mm)
- report9 §4.12 Combined Driver: `56` — Script 20 should emit the broadleaf canopy-increment drawdown at source (56.25 mm)
- report9 §4.12 Combined Driver: `59` — Script 20 should emit the number of wells on the MSL5 change map (59)
- report9 §4.12 Combined Driver: `20` — Script 20 or 10b should emit the distance of fe1 from the December 2017 felled boundary (about 20 m)
- report9 §4.12.1 Driver valida: `157` — Script 20 (or 37b) should emit the coastal toe depth lowering over the stated horizon (5 x coastal_delta0 = 5 x 31.28 = 156.4 mm; the quoted 157 came from delta_0 = 31.4)
- report10 §5.7.5 Parametric Pre: `−50` — Script 20 should emit the range of the net-state field over the forest interior (the sentence quotes -50 to over -150 mm)
- report10 §5.7.5 Parametric Pre: `59` — Script 20 should emit the msl5 comparison well count (59; only in the notes of msl5_mean_2017 [20_msl5_report_numbers.csv])
- report10 §5.7.9 The 1951--53 R: `60` — Script 20 or 44 should emit the modelled forest drawdown at each Ranwell site (the sentence quotes 60 to 80 mm)

**Script 21** (1 rows)

- report10 §5.5.2 Forest Managem: `30` — Script 21 should emit the C5-to-C4 ratio of annual water-equivalent gain under clearfell and thinning (1.294)

**Script 23** (1 rows)

- report10 §5.2.1 Water Balance : `49` — Script 23 should emit the count of Bartlett-significant-peak wells (49) as a Value row

**Script 24** (3 rows)

- report10 §5.2.1 Water Balance : `63` — Script 24 should emit wells analysed (63) and the summer-phase-peak count (0 of 63) to 24_report_numbers.csv
- report10 §5.3.1 Recharge Parti: `48` — Script 24 should emit wells with a winter/early-spring phase peak (48 of 63) to 24_report_numbers.csv
- report10 §5.3.1 Recharge Parti: `63` — Script 24 should emit wells analysed (63) to 24_report_numbers.csv

**Script 25** (9 rows)

- report9 §4.10.2 Network-scale: `1.6` — Script 25 should emit ForestFree_ref_disagreement_lincap_vs_exp (1.634 mm/yr)
- report9 §4.10.2 Network-scale: `1.9` — Script 25 should emit delta0_loo_max_over_second_ratio (1.873 for delta_0; 1.547 for the 150 m rate)
- report9 §4.10.3 What the fit : `151` — Script 25 should emit the raw-series VIF of elapsed time against the CWB covariate (about 151)
- report9 §4.12 Combined Driver: `46` — Script 25 should emit the Check2 well count (46)
- report10 §5.5 The Clearfell Ex: `5.5` — Script 25 should emit the absorbed-minus-predicted difference for the Forest/Impact pair (-16.1486 - (-10.6754) = -5.473 mm/yr)
- report10 §5.7.2 Forest Managem: `46` — Script 25 should emit the Check 2 sample size as a value (46 wells; only in the note of Check2_msl5raw_vs_summermin_pearson_p [25_report_numbers.csv])
- report10 §5.7.7 What the Recor: `18` — Script 25 should emit the R2 of the per-well trend on distance to the shore (the sentence says 18 %)
- report10 §5.7.7 What the Recor: `14.9` — Script 25 should emit the SD of per-well residuals about the fitted profile (the sentence says 14.9 mm/yr)

**Script 26** (23 rows)

- report8 §3.7.5 Five-Year Mean: `3.3` — Script 26 should emit the share of admitted five-year windows containing an interpolated month (29 / 866 = 3.349 %)
- report9 §4.5.4 Summer Minima: `−0.50` — Script 26 should emit the CEH36 MSL5 mean over window-ends 2017-2023 (-0.485 m, from 26_msl_5yr_per_well.csv)
- report9 §4.5.4 Summer Minima: `+0.05` — Script 26 should emit the CEH36 minus CEH4 MSL5 difference per window-end 2017-2023 and its range (+0.031 to +0.092 m from 26_msl_5yr_per_well.csv; text says roughly +0.05 to +0.10)
- report9 §4.5.4 Summer Minima: `−0.60` — Script 26 should emit the CEH4 MSL5 mean over window-ends 2019-2023 (-0.592 m, from 26_msl_5yr_per_well.csv)
- report9 §4.8.3 Five-Year Mean: `0.08` — Script 26 should emit the largest amount by which a cluster four-year mean annual minimum sits below SD16 (C2 = 0.0825 m from 26_curreli_min_per_cluster.csv)
- report9 §4.8.3 Five-Year Mean: `1.02` — Script 26 should emit the C5 minus C1 gap in MSL5 at window-end 2025 (1.016 m from 26_msl_5yr_per_cluster.csv)
- report9 §4.8.3 Five-Year Mean: `0.81` — Script 26 should emit the C5 minus C1 gap in the four-year mean annual minimum at window-end 2025 (0.807 m from 26_curreli_min_cluster_threshold_summary.csv)
- report9 §4.8.3 Five-Year Mean: `0.19` — Script 26 should emit the C3 minus C2 gap in MSL5 at window-end 2025 (0.194 m from 26_msl_5yr_per_cluster.csv)
- report9 §4.8.3 Five-Year Mean: `0.65` — Script 26 should emit the C4 minus C1 gap in MSL5 at window-end 2025 (0.648 m from 26_msl_5yr_per_cluster.csv)
- report9 §4.8.3 Five-Year Mean: `0.60` — Script 26 should emit the C4 minus C1 gap in the four-year mean annual minimum at window-end 2025 (0.597 m from 26_curreli_min_cluster_threshold_summary.csv)
- report9 §4.8.3 Five-Year Mean: `83` — Script 26 should emit n_wells_msl5_map (83 = rows of 26_msl_5yr_latest_per_well.csv)
- report9 §4.8.3 Five-Year Mean: `85` — Script 26 should emit n_wells_msl5_any_window (85 distinct wells in 26_msl_5yr_per_well.csv)
- report9 §4.8.3 Five-Year Mean: `75` — Script 26 should emit n_wells_msl5_latest_2025 (75 of 83 in 26_msl_5yr_latest_per_well.csv)
- report9 §4.8.3 Five-Year Mean: `+205` — Script 26 should emit the per-cluster MSL5 step from window-end 2023 to 2024 (mm): C1 84.25, C3 157.06, C4 205.41, C5 140.00 from 26_msl_5yr_per_cluster.csv
- report9 §4.8.3 Five-Year Mean: `0.6` — Script 26 should emit the C4 and C5 minus C1 gaps in MSL5 at window-end 2025 (0.648 m and 1.016 m from 26_msl_5yr_per_cluster.csv)
- report9 §4.8.4 Equilibrium We: `0.5` — Script 26 should emit the correlation of each state-space coefficient and storage term with Ellenberg-F (best |r| by my recompute from betas is 0.433, not about 0.5; check the sentence)

**Script 30** (2 rows)

- report9 §4.2.2 Cluster Mechan: `1.20` — Script 30 should emit the per-cluster median per-well VIF on the 100-month window (C4 1.2028; C1 2.195, C2 1.642, C3 1.432, C5 1.301)
- report10 §5.2.3 The C4 Main Fo: `0.001` — Script 30 should emit |c4_closure_min_beta3 - c4_centroid_beta3| (0.019 - 0.018466 = 0.00053 per month)

**Script 32** (3 rows)

- report11 §6.2 Record length --: `28` — Script 32 should emit the headline minimum detectable site-wide rate (about 28 mm/yr; spring 27.25 and annual 28.54 in 32_site_mean_trend.csv, mean 27.89)
- report9 §4.12 Combined Driver: `0.98` — Script 32 should emit the correlation between the differential-trend map and the two-window change map (quoted above 0.98; my check gives 0.21)
- report10 §5.7.7 What the Recor: `7` — Script 32 should emit the record length at which the minimum detectable rate falls to 7 mm/yr (the sentence says roughly five decades)

**Script 33** (4 rows)

- report9 §4.12 Combined Driver: `1.56` — Script 33 should emit the C4 mean amplification with ceh13 and ceh14 excluded (about 1.56)
- report10 §5.3.2 Drainage Decay: `1.31` — Script 33 should emit the C4 per-well amplification range (min 1.306292 at ceh30, max 2.318729 at ceh14) to 33_cluster_summary.csv
- report10 §5.3.2 Drainage Decay: `1.56` — Script 33 should emit the C4 mean amplification excluding ceh13 and ceh14 (1.559 on unflagged wells)
- report10 §5.7.5 Parametric Pre: `0.8` — Script 33 should emit the Pearson r of the canonical per-well amplification against SSM beta_2 (computed 0.83, n = 63 unflagged wells)

**Script 37** (4 rows)

- report9 §4.12.1 Driver valida: `−0.48` — Script 37 should emit the correlation of the modelled coastal signature (coast_i) with easting at the wells entering the fit (recomputed here as +0.67 for 2018_2025, +0.66 for 2006_2012, +0.61 for 200
- report10 §5.7.5 Parametric Pre: `−0.48` — Script 37 should emit the correlation of the modelled coastal amplitude (coast_i) with well easting (the sentence quotes r about -0.48)
- report10 §5.7.5 Parametric Pre: `150` — Script 37 should emit the spread (SD or MAD) of the per-well driver-validation residuals by window (sentence: of order +/-150 to 200 mm)

**Script 39** (1 rows)

- report9 §4.14.1 The 1989--96 : `0.025` — Script 39 should emit the difference between ccw_annual_range_mean_m (0.72451) and the Davy et al. (2010) 0.75 m (0.0255)

**Script 40** (2 rows)

- report8 §3.8.2 Drawdown-Field: `0.06` — Script 40 should emit the 1899-line positional error expressed as a rate over the 1899-2006 interval (5.95 / 107 = 0.0556 m/yr)

**Script 41** (1 rows)

- report9 §4.6.8 Temporal decay: `1.15` — Script 41 should emit the mean forest_control ratio_to_conifer across the aerial frames of the BACI window (1.145 for 2018-06-28 to 2020-04-24)

**Script 43** (4 rows)

- report10 §5.7.9 The 1951--53 R: `120` — Script 43 should emit each Ranwell site's distance to the nearest forest well (the sentence quotes 120 to 200 m at Clwt Gwlyb)

**Script 44** (2 rows)

- report10 §5.7.9 The 1951--53 R: `0.3` — Script 44 should emit the excluded fall and rise bounds at the inland sites (delta -0.087 m -/+ 2 sigma 0.098 m gives -0.28 m and +0.11 m)

**Script 01B** (7 rows)

- report9 §4.8.5 Slack-floor we: `11,616` — Script 01b should emit sentinel_cells_tested (11616 = sum of the seven sentinel_cells_* rows)
- report9 §4.8.5 Slack-floor we: `4.2` — Script 01b should emit sentinel_cells_above_excess (=488) and sentinel_share_above_excess (=0.04201) to 01b_report_numbers.csv
- report9 §4.8.5 Slack-floor we: `488` — Script 01b should emit sentinel_cells_above_excess (488 = 95+180+51+162)
- report9 §4.9.5 Mean Water Tab: `0.68` — Script 01b should emit loo_p90_abs_mean_m (0.6764; 01b_01_drift_selection.csv holds loo_p90 columns per drift but 01b_report_numbers.csv does not)
- report9 §4.9.5 Mean Water Tab: `7` — Script 01b should emit slacks_turning_over_20deg (7)
- report9 §4.9.5 Mean Water Tab: `116` — Script 01b should emit n_slacks_with_turn (116)

**Script 09B** (2 rows)

- report8 §3.5.3 Dune Scraping : `10` — Script 09b should emit the uphill well count (10; 09b_01_individual_well_baci.csv role = uphill)
- report9 §4.11 Management infl: `0.54` — Script 09b should emit the distance-decay test of the BACI-corrected delta-beta3 (p quoted 0.54)

**Script 10A** (1 rows)

- report10 §5.5 The Clearfell Ex: `92` — Script 10a should emit the drift-term cost of the Impact step (step free_trend - no_trend = 91.76 mm, all5 subset)

**Script 10B** (3 rows)

- report10 §5.4 Dune Scraping: `340` — Script 10b (or 09) should emit the distance from CEH36 to the December 2017 clearfell footprint (about 340 m)
- report10 §5.4.2 Interaction wi: `340` — Script 10b (or 09) should emit the distance from CEH36 to the clearfell footprint (about 340 m)

**Script 10C** (6 rows)

- report9 §4.2.2 Cluster Mechan: `14` — Script 10c should emit the number of wells in the forest-zone comparison (C4 9 + C5 5 = 14)
- report9 §4.9.4 Per-Well Fores: `14` — Script 10c should emit forest_zone_n_wells (14 = 9 C4 + 5 C5) to a 10c report-numbers CSV
- report9 §4.9.4 Per-Well Fores: `14` — Script 10c should emit forest_zone_n_wells (14) to a 10c report-numbers CSV
- report9 §4.9.4 Per-Well Fores: `31` — Script 10c should emit R2_easting_only for beta_1 (0.3091 = 0.556^2)
- report9 §4.9.4 Per-Well Fores: `2.4` — Script 10c should emit nw10 beta_1 z-score against the C4 mean (2.41)

**Script 10D** (3 rows)

- report10 §5.6.3 Broadleaf Conv: `−1.711` — Script 10d should emit per-well mean summer minima (ceh2 -1.7114, ceh34 -1.3120 in 10d_01_summer_minima.csv)
- report10 §5.6.3 Broadleaf Conv: `399` — Script 10d should emit the ceh2 minus ceh34 mean summer-minimum spread (0.3994 m)

**Script 10E** (5 rows)

- report9 §4.6.4 Summer Minima: `17` — Script 10e should emit CoeffShift_Network_n_wells = 17 (BACI-network wells excluding Far-field Ctrl; currently only in the Note "n=17 BACI-network wells" of CoeffShift_Network_mean_b1_before in 10e_re
- report9 §4.6.6 Coefficient De: `17` — Script 10e should emit the BACI well count of the tiers shown in Table 10e (17; 10e_01_coefficient_shifts.csv has 22 rows including 5 Far-field Ctrl)
- report10 §5.6.2 Summer Minimum: `+0.169` — Script 10e should emit the Forest Ctrl delta-beta_2 excluding NW10 (mean 0.157, median 0.169 from CEH32/34/33/2: 0.1437, 0.2528, 0.0376, 0.1939); check whether the report means mean or median

**Script 10F** (2 rows)

- report9 §4.6.7 Robustness: `+27` — Script 10f should emit the Impact-minus-Forest-control SSM-residual step (0.0806 - 0.0533 = 0.0273 m)
- report10 §5.5 The Clearfell Ex: `+27` — Script 10f should emit the impact-specific residual step, SSM_Resid_Impact_mean_step - SSM_Resid_Forest_Ctrl_mean_step (0.0273 m)

**Script 10G** (3 rows)

- report10 §5.6.3 Broadleaf Conv: `+249` — Script 10g should emit the NW10 mean anomaly over the full record (0.2490 m) and post-felling (2018-2025, 0.2675 m); NW10_mean_anomaly_2010_2021 = 0.2951 is a different window
- report10 §5.6.3 Broadleaf Conv: `+268` — Script 10g should emit the NW10 mean anomaly for the post-felling period 2018-2025 (0.2675 m)
- report10 §5.6.3 Broadleaf Conv: `+249` — Script 10g should emit the NW10 mean anomaly over the full record (0.2490 m)

**Script 11B** (3 rows)

- report9 §4.7.4 Spatial Distri: `88` — Script 11b should emit the classified-network well count (88 = 66 reference + 22 extended; 11b_03_pflood_per_well.csv has 88 rows)

**Script 11C** (11 rows)

- report9 §4.7.4 Spatial Distri: `59` — Script 11c should emit the count of wells per m_P band (Achievable 59, Marginal 24, Unreachable 5 of 88)
- report9 §4.7.4 Spatial Distri: `67` — Script 11c should emit the percentage of wells per m_P band (59/88 = 67.0 %)
- report9 §4.7.4 Spatial Distri: `24` — Script 11c should emit the count of Marginal wells (24 of 88)
- report9 §4.7.4 Spatial Distri: `27` — Script 11c should emit the percentage of wells per m_P band (24/88 = 27.3 %)
- report10 §5.8.1 P_flood Recove: `88` — Script 11c should emit the number of classified wells (88 = 66 reference + 22 extended) and the counts by category
- report10 §5.8.1 P_flood Recove: `59` — Script 11c should emit the Achievable well count (59; category counts 59 / 24 / 5 of 88)
- report10 §5.8.1 P_flood Recove: `67` — Script 11c should emit the Achievable share of classified wells (59 of 88 = 67.0 %)
- report10 §5.8.1 P_flood Recove: `24` — Script 11c should emit the Marginal well count (24; category counts 59 / 24 / 5 of 88)
- report10 §5.8.1 P_flood Recove: `27` — Script 11c should emit the Marginal share of classified wells (24 of 88 = 27.3 %)
- report10 §5.8.1 P_flood Recove: `5` — Script 11c should emit the Unreachable well count (5; category counts 59 / 24 / 5 of 88)
- report10 §5.8.1 P_flood Recove: `6` — Script 11c should emit the Unreachable share of classified wells (5 of 88 = 5.7 %)

**Script 14B** (2 rows)

- report10 §5.8 The Reach of For: `0.2` — Script 14b should emit the gap between each cluster's current summer-minimum depth and the SD15b and SD16 thresholds (sentence: 0.2 to 0.4 m for C1 and C2)

**Script 37B** (4 rows)

- report9 §4.12.1 Driver valida: `949` — Script 37b should emit site_area_ha (949.2 ha, the site-mask area used to normalise the equivalent depths)
- report10 §5.8.2 Climate Trajec: `72` — Script 37b or 20 should emit the observed clearfell response as a share of the modelled equilibrium (108.2/150 = 72 %)
- report10 §5.8.2 Climate Trajec: `949` — Script 37b should emit the mapped site area on the 50 m grid (949.2 ha)

## 3. Unsure

- report8 §3.4.1 Modelling the : `700` — 700 ha is a descriptive site area; committed study_area_ha in 12_report_numbers.csv is 864.76 ha (a different boundary definition, D-203) and the Bristow-cited borehole sentence also says 700 ha, so I cannot tell whether it is a literature 
- report8 §3.6.3 Algebraic Deri: `1.05` — the worked example does not reproduce from the committed C2 row: with alpha 0.93712, b1 0.0038957, b2 0.0016664, S_P 360.98, S_E 99.33 and D = 3.7 m, h0 = -0.5 m gives m_p = 0.994 (P_flood 397 mm) and h0 = -0.6 m gives m_p = 1.049; the tool
- report8 §3.6.3 Algebraic Deri: `448` — the illustrative 448 mm is not reproduced: C2 at h0 = -0.5 m gives about 397 mm and at h0 = -0.6 m about 419 mm (lambda x P_clim 399.6 mm); the actual C2 P_flood is 473.3 mm at h0 = -0.8477 m [11_forecast_pflood_summary.csv]; Martin to say 
- report9 §4.9.2 Spatial Coeffi: `70` — "70--85%" is a colour-band reading of the R2 map over a region (central/northern open dune) that no file defines; Model_R2 in 07_coeff_maps_data spans 0.563 to 0.870 (C1-C3 cluster means 0.742 to 0.761), 07_05 R2_adj_covariates 0.70 is a di
- report9 §4.9.2 Spatial Coeffi: `85` — upper end of the same map-band reading; FourZone_R2 (BACI four-zone model) is unrelated; per-well Model_R2 maximum is 0.8699 (07_coeff_maps_data)
- report9 §4.10.2 Network-scale: `−0.7` — value is the C5 unexplained under the superseded pre-D-196 partition (nw8b in C3); no committed file carries that counterfactual, and the attribution (nw8b leave-one-out shift) is a different quantity; current C5 unexplained is -17.5602 in 
- report10 §5.7.5 Parametric Pre: `1` — 'about 1x on the open dune' is qualitative: C2 amplification_mean is 0.868 and C3 1.199 (33_cluster_summary.csv canonical), network 1.077; no single row is 1
- report10 §5.7.7 What the Recor: `0.002` — 'survives at p = 0.002 across three methods': the three ANCOVA specifications give Forest-control clearfell p of 0.00137 (A), 0.00245 (B) and 0.00342 (C) in 10h, so no single p = 0.002 is committed; the tool's Climate/Edge row is a differen
- report10 §5.8.1 P_flood Recove: `1.9` — 'deeper-end wells approach m_p = 1.9' has no single committed value: the C3 wells in 11c_pflood_achievability_per_well.csv have lambda 2.003 (wmc3), 1.808 (nw1), 1.758 (nw7)
