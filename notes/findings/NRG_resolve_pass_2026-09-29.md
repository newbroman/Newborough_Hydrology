# The resolve pass — what the proof page still flags, and why (2026-09-29, changelog 29p)

Written by Claude (Fable 5.1, Cowork bridge + cloud, session_01Dyg7nMMvCZATnrDoXUriAM). Martin: "go through chapter by chapter and check the flagged values and resolve them. bring them to me if you can't resolve them." Seven readers took the 250 flagged numbers (scratch/flagged/, brief scratch/resolve/BRIEF.md in the cloud clone); their 250 verdicts are in `tools/proof_reading_verdicts.csv` (batch `2026-09-29 resolve`). Outcome: 11 digit corrections into the ODTs, about 60 numbers re-pointed at committed tables the earlier readers had not opened, proof_copy 1.26.0 for the cases that were the tool's fault, and the two lists below.

## 1. The emit list — quantities no committed CSV carries (T-96)

Each row: the chapter and section that quotes it, the number as quoted, and what the script should emit (the reader's computed value and computation are in the verdict row's `better`). These stay red on the page until the script emits them and the full run lands. Grouped by owning script; 146 rows across 43 scripts.

### Script 00 (9)

- report9 §4.1.1 Climate Record: **50** — the range of the 12-month rolling mean of monthly PET (p05-p95 50.00-56.27, min-max 47.22-58.01 mm/month; rolling(12) full windows of 01_climate.csv PET x 1000, Dec 1930-Feb 2026)
- report9 §4.1.1 Climate Record: **55** — the typical range of the 12-month rolling mean of monthly PET (see the 50 row; 5th-95th percentile 49.9-56.2 mm/month)
- report9 §4.1.2 Well Network: **0.77** — the network mean water level over all reference wells and months (-0.7681 m: 01_wells_reference.csv .stack().mean(), n=66 wells; equals sum(Mean_WL_m*N_months)/sum(N_months) of 00_02_well_network_summary.csv)
- report9 §4.1.2 Well Network: **0.68** — the median Seasonal_amplitude_m of the 66 reference wells (-0.6828 m, August minus February; median of the column in 00_02_well_network_summary.csv)
- report9 §4.1.2 Well Network: **11** — the count of reference wells with Mean_Winter_Max_m above ground (11)
- report10 §5.7.5 Parametric Prediction : **0.5** — the trend p-values of total summer PET and summer rainfall over 1931-2025 (the sentence quotes p > 0.5)
- report10 §5.8.1 P_flood Recoverability: **745** — the wettest RAF Valley Oct-Mar winter total and its ratio to the mean winter (winter 2001: 745.0 mm; mean 494.1 mm over 94 complete winters; ratio 1.508; 1.508/2.5 = 60 %; computed from data/RAF_Valley_Climate.csv Rain, Oct of the previous year to Mar)
- report11 §6.4 Thornthwaite PET and sen: **631** — the 1931-1960 mean annual Thornthwaite PET (630.7935 mm: mean of PET_annual_mm, period == early, n=30, in 00_05_pet_warming_response.csv)
- report11 §6.4 Thornthwaite PET and sen: **650** — the 1996-2025 mean annual Thornthwaite PET (649.7360 mm: mean of PET_annual_mm, period == late, n=30, in 00_05_pet_warming_response.csv)

### Script 01 (7)

- report8 §3.5.3 Dune Scraping Interven: **90** — the CEH36 minus CEH4 distance-to-coast difference (92.2 m from dist_coast_m 312.9 - 220.7)
- report8 §3.5.3 Dune Scraping Interven: **85** — the CEH21 minus CEH22 distance-to-coast difference (85.3 m from dist_coast_m 232.0 - 146.7)
- report8 §3.7.4 Network-Scale Coastal-: **15** — the length of the committed west-facing Caernarfon Bay HWM polyline used for dist_coast_m, in km (quoted as 15)
- report9 §4.2.1 Cluster Hydrographs an: **7.45** — the per-well mean water-table elevation (m AOD) of the reference wells with its network mean, min and max (mean 7.4486, min 3.0231 ceh11, max 13.3319 ceh14; column means of 01_wells_clean_maod.csv)
- report9 §4.2.1 Cluster Hydrographs an: **13.33** — per-well mean water-table elevation (m AOD) for the reference wells with the network mean, min and max (ceh14 = 13.3319, network mean 7.4486, min 3.0231 at ceh11; column means of 01_wells_clean_maod.csv)
- report9 §4.2.1 Cluster Hydrographs an: **9.37** — the C1 mean water-table elevation with and without ceh11 (8.4596 and 9.3657 m AOD; mean of per-well column means of 01_wells_clean_maod.csv over the seven C1 wells)
- report10 §5.6.3 Broadleaf Conversion: : **90** — the NW11-NW13 distance (91.8 m from E,N in 01_locations.csv)

### Script 01b (5)

- report9 §4.8.5 Slack-floor wet area: : **11,616** — sentinel_cells_tested (11616); computed as rows of 01b_04_sentinel_check.csv with class != "no surface"
- report9 §4.8.5 Slack-floor wet area: : **4.2** — sentinel_cells_above_excess and sentinel_share_above_excess (488 cells, 0.042011); computed as sum of sentinel_cells_shadow + sentinel_cells_reached_by_well + sentinel_cells_floor_edge + sentinel_cells_unexplained in 01b_report_numbers.csv, divided by 11616
- report9 §4.8.5 Slack-floor wet area: : **488** — sentinel_cells_above_excess (488 = 95+180+51+162)
- report9 §4.9.5 Mean Water Table Surfa: **7** — slacks_turning_over_20deg and n_slacks_with_turn (7 of 116); computed as rows of 01b_03_slack_directions.csv with turn_wet_dry_deg > 20 (7); rows with turn_wet_dry_deg non-blank (116)
- report9 §4.9.5 Mean Water Table Surfa: **116** — n_slacks_with_turn (116)

### Script 02 (6)

- report8 §3.4.4 Within-Forest Spatial : **14** — per-cluster well counts (C4 9, C5 5; forest zone 14) as report-numbers rows
- report9 §4.2 Network Clustering and S: **1.0** — the final (top) Ward merge distance of the reference dendrogram (0.98825: Z[-1,2] of linkage(1 - r, ward) on 01_wells_reference.csv)
- report9 §4.2.1 Cluster Hydrographs an: **0.3** — the C3 minus C1/C2 cluster mean-level offsets (C3-C2 = 0.2676 m, C3-C1 = 0.3871 m, both deeper, from cluster_mean_level_m rows)
- report9 §4.2.1 Cluster Hydrographs an: **0.6** — the C4 minus C3 cluster mean-level offset (0.5666 m deeper, cluster_mean_level_m C4 -1.33789 minus C3 -0.77125)
- report9 §4.2.1 Cluster Hydrographs an: **2.1** — the per-cluster post-2018 p90-p10 max:min ratio (C3 = 2.135 = post2018_p90_p10_max 1.373 / post2018_p90_p10_min 0.643; C1 1.434, C2 1.472, C4 1.574)
- report10 §5.7.2 Forest Management Scen: **14** — the forest-cluster well count (C4 9 + C5 5 = 14; 02_report_numbers.csv carries n = 9 and n = 5 only in notes)

### Script 03 (4)

- report8 §3.4 Using Models to derive t: **0.09** — the per-cluster R2 span across the admissible datum range (C1 0.0846 = R2(1.6 m) - R2(8.0 m) from 03_08_datum_sensitivity.csv; widest over clusters)
- report10 §5.6.3 Broadleaf Conversion: : **2.333** — the C4 per-well median beta_1_recharge (2.332887 = median of beta_1_recharge over the 9 rows with Cluster == 4 in 03_master_data.csv)
- report10 §5.6.3 Broadleaf Conversion: : **2.581** — the C4 per-well median beta_2_atmospheric_draw (2.581175 = median over the 9 rows with Cluster == 4 in 03_master_data.csv)
- report10 §5.8.1 P_flood Recoverability: **8** — per-cluster recession time 1/beta_3 range and median at the well level (C1: 7.4 to 11.4, median 10.2 months)

### Script 3 (2)

- report9 §4.9.1 Datum Sensitivity: **1.45** — the network median of max_R2_datum in the "all clusters" row of 03_18_datum_invariance.csv (well_median_max_R2_datum_m) (1.45 m); computed as median of max_R2_datum over the 66 rows of 03_09_well_optimal_datums.csv
- report9 §4.9.1 Datum Sensitivity: **0.014** — the network median r2 gain in the "all clusters" row of 03_18_datum_invariance.csv (well_median_R2_gain) (0.014239); computed as median of R2_gain_max_vs_uniform over the 66 rows of 03_09_well_optimal_datums.csv

### Script 05 (6)

- report8 §3.3.2 Classification Criteri: **16** — the number of wells changing Core/Fuzzy tier at delta-r 0.03 (16) and 0.10 (14), recomputed from 05_pear_membership_audit.csv
- report9 §4.3 Checking the Clusters: P: **60** — n_confirmed (60 of 66; Class != Spy)
- report9 §4.3 Checking the Clusters: P: **19** — n_core, n_fuzzy and n_spy from the Class column of 05_pear_membership_audit.csv (19, 41, 6)
- report9 §4.3 Checking the Clusters: P: **41** — n_core (19), n_fuzzy (41), n_spy (6) from Class
- report9 §4.3 Checking the Clusters: P: **44** — n_mca_flagged (44 of 66)
- report9 §4.3 Checking the Clusters: P: **13** — the MCA_Cluster_Label counts (C1/C2/C3 22, C2/C3/C5 13, C3/C4/C5 8, C2/C3/C4 1)

### Script 06 (1)

- report9 §4.3 Checking the Clusters: P: **3** — n_ext_core and n_ext_fuzzy from the Status column of 06_pear_membership_audit_sitewide.csv (3 and 19)

### Script 07 (1)

- report9 §4.2.2 Cluster Mechanistic Ch: **−0.01** — C4_beta2_beta3_corr_excl_ceh13_ceh14 (-0.012976; Pearson r of beta_2_atmospheric_draw vs beta_3_drainage over the 7 C4 wells of 03_master_data.csv excluding ceh13 and ceh14)

### Script 08 (2)

- report12 §7 Conclusions: **1** — the number of wells with negative iterative NSE under the SSM (1) and the TLM (11)
- report12 §7 Conclusions: **11** — the number of wells with negative iterative NSE under the TLM (11) and the SSM (1), of benchmark_n_wells = 66 (count of rows with TLM_NSE < 0 / SSM_NSE < 0 in 08_perwell_nse.csv)

### Script 10 (8)

- report §: **17** — the number of wells in the five-tier BACI network (17)
- report6 §1 Introduction: **17** — the number of wells in the five-tier BACI network (17 = Impact 1 + Edge 4 + Forest control 5 + Coastal control 2 + Climate control 5, counted from the member lists in the Note of the five Pre_felling_baseline_years_min rows of 10_consolidated_report_numbers.csv)
- report8 §3.5.4 Clearfell BACI experim: **752** — each control well distance from the felling centroid (forest controls 306.23 to 752.45 m, NW10 = 752.45; hypot(E-241210, N-363607) from 01_locations.csv)
- report8 §3.5.4 Clearfell BACI experim: **215** — each control well distance from the felling centroid (climate controls 215 to 1010 m; NW7 = 214.8 m)
- report8 §3.5.4 Clearfell BACI experim: **1010** — each control well distance from the felling centroid (climate controls 214.84 to 1009.97 m, WMC2 = 1009.97; hypot(E-241210, N-363607) from 01_locations.csv)
- report8 §3.5.4 Clearfell BACI experim: **20** — the FE1 distance to the clearfell boundary (about 20 m)
- report9 §4.6.1 Interpretive Context: **28** — the months of FE1 and FE2 record before CLEARFELL_DATE_ISO (01_wells_extended.csv has 29 monthly readings, Jul 2015 to Nov 2017; the text says approximately 28)
- report9 §4.6.1 Interpretive Context: **32** — months from SCRAPING_DATE_ISO (2015-04-01) to CLEARFELL_DATE_ISO (2017-12-01) (= 32)

### Script 10a (6)

- report10 §5.3.2 Drainage Decay and the: **0.22** — the p-value of ANCOVA_Forest_Impact_coeff_cwb2_x_fell as its own row, e.g. ANCOVA_Forest_Impact_coeff_cwb2_x_fell_p (0.2181, currently only in the Note of the coefficient row in 10_consolidated_report_numbers.csv / 10a_report_numbers.csv)
- report10 §5.3.2 Drainage Decay and the: **0.36** — the p-value of ANCOVA_Forest_Edge_coeff_cwb2_x_fell as its own row, e.g. ANCOVA_Forest_Edge_coeff_cwb2_x_fell_p (0.3648, currently only in the Note of the coefficient row)
- report10 §5.5 The Clearfell Experiment: **92** — the drift-term cost of the Impact step (step free_trend - no_trend = 91.76 mm, all5 subset)
- report10 §5.5 The Clearfell Experiment: **5.5** — the absorbed-minus-predicted coastal drift for Forest/Impact (absorbed_drift_mm_yr - coastal_differential_mm_yr = -16.148597 - (-10.675441) = -5.473156 mm/yr; 10a_09_coastal_scale_factor.csv row Forest/Impact)
- report10 §5.6.1 Atmospheric Draw, Spec: **0.22** — the p-value of the cwb2_x_fell curvature term as a Value row (Impact 0.2181, from Note "p=0.2181" of ANCOVA_Forest_Impact_coeff_cwb2_x_fell)
- report10 §5.6.1 Atmospheric Draw, Spec: **0.36** — the p-value of the cwb2_x_fell curvature term as a Value row (Edge 0.3648, from Note "p=0.3648" of ANCOVA_Forest_Edge_coeff_cwb2_x_fell)

### Script 10b (2)

- report10 §5.4 Dune Scraping: **340** — the distance from CEH36 to the December 2017 clearfell footprint (about 340 m)
- report10 §5.4.2 Interaction with the C: **340** — the distance from CEH36 to the clearfell footprint (about 340 m)

### Script 10c (5)

- report9 §4.2.2 Cluster Mechanistic Ch: **14** — the number of wells in the forest-zone comparison (C4 9 + C5 5 = 14)
- report9 §4.9.4 Per-Well Forest Zone A: **14** — forest_zone_n_wells (14 = 9 C4 + 5 C5) to a 10c report-numbers CSV
- report9 §4.9.4 Per-Well Forest Zone A: **14** — n_forest_zone_wells (14); computed as count of rows of 07_coeff_maps_data.csv with Cluster_ID in {4,5} (9 + 5)
- report9 §4.9.4 Per-Well Forest Zone A: **31** — R2_easting_only for beta_1 (0.3088); computed as pearson r of beta_1_recharge on E over the 14 C4+C5 wells of 07_coeff_maps_data.csv (r = 0.55572) squared
- report9 §4.9.4 Per-Well Forest Zone A: **2.4** — nw10_beta1_z_vs_c4 (2.4124); computed as (nw10 beta_1_recharge minus C4 mean) / C4 sample sd (ddof=1) of beta_1_recharge over the 9 C4 wells of 07_coeff_maps_data.csv

### Script 10d (3)

- report10 §5.6.3 Broadleaf Conversion: : **−1.711** — the per-well mean summer minimum (CEH2 -1.711429 m over 14 summers; mean of Summer_min_m by Well in 10d_01_summer_minima.csv)
- report10 §5.6.3 Broadleaf Conversion: : **−1.312** — the per-well mean summer minimum (CEH34 -1.312000 m over 15 summers; mean of Summer_min_m by Well in 10d_01_summer_minima.csv); the 399 mm spread is the difference -1.711429 - (-1.312000) = 0.399429
- report10 §5.6.3 Broadleaf Conversion: : **399** — the ceh2 minus ceh34 mean summer-minimum spread (0.3994 m)

### Script 10e (2)

- report9 §4.6.4 Summer Minima: **17** — CoeffShift_Network_n_wells = 17 (BACI-network wells excluding Far-field Ctrl: Tier count of 10e_01_coefficient_shifts.csv, 22 rows less 5 Far-field Ctrl; currently only in the Note of CoeffShift_Network_mean_b1_before in 10e_report_numbers.csv)
- report10 §5.6.2 Summer Minimum Depths : **+0.157** — the Forest Ctrl mean and median Δβ₂ excluding NW10 (mean 0.1570, median 0.1688; db2 of 10e_01_coefficient_shifts.csv)

### Script 10f (2)

- report9 §4.6.7 Robustness: **+27** — the Impact-minus-Forest-control SSM-residual step (0.0273 m = 0.0806 - 0.0533)
- report10 §5.5 The Clearfell Experiment: **+27** — the impact-specific residual step = SSM_Resid_Impact_mean_step - SSM_Resid_Forest_Ctrl_mean_step (0.0806 - 0.0533 = 0.0273 m)

### Script 10g (3)

- report10 §5.6.3 Broadleaf Conversion: : **+249** — NW10_mean_anomaly_full_record (0.2490294 m = mean of NW10_anomaly_m over the 17 year rows of 10g_01_nw10_broadleaf_trend.csv) and the post-felling (2018-2025, 7 years) mean 0.2675 m
- report10 §5.6.3 Broadleaf Conversion: : **+268** — the NW10 mean anomaly for the post-felling period 2018-2025 (0.2675 m)
- report10 §5.6.3 Broadleaf Conversion: : **0.10** — NW10_trend_p as a Value row (0.1014, Trend_p in 10g_01_nw10_broadleaf_trend.csv; Trend_n = 6)

### Script 11 (1)

- report8 §3.6.3 Algebraic Derivation o: **77** — alpha^n for each cluster (C2 Oct-Jan, n = 4: 0.7712 = 77.12 %)

### Script 11c (1)

- report10 §5.8.1 P_flood Recoverability: **59** — the category counts and shares of the 88 classified wells (Achievable 59 = 67.05 %, Marginal 24 = 27.27 %, Unreachable 5 = 5.68 %; category column of 11c_pflood_achievability_per_well.csv)

### Script 12 (1)

- report7 §2 Study Site: **0.6** — the clearfell area as a share of the plantation (4.4/700 = 0.63 %)

### Script 14 (7)

- report9 §4.8.1 Summer and Winter Traj: **14** — the count of years each cluster summer minimum sat below SD16 (C3 = 14 of 21, counted from 14_annual_extremes.csv Summer_Min < -0.98)
- report9 §4.8.1 Summer and Winter Traj: **18** — the count of years each cluster summer minimum sat below SD16 (C5 = 18 of 20, counted from 14_annual_extremes.csv)
- report9 §4.8.1 Summer and Winter Traj: **20** — the count of hydrological years each cluster summer minimum sat below SD15b and SD16 (C2 = 20 of 21 below SD15b); computed as rows of 14_annual_extremes.csv with Season==Summer_Min and Value_m < -config.SD15b (0.61) per Cluster: C1 20/20, C2 20/21, C3 21/21, C4 20/20, C5 20/20; below -SD16 (0.98): C1 4/20, C2 9/21, C3 14/21, C4 
- report9 §4.8.1 Summer and Winter Traj: **2.5** — the C5:C1 ratio of summer-minimum trend slopes (2.5304); computed as Slope_m_per_yr C5 / C1 in 14_summer_trend_stats.csv = -0.0291/-0.0115
- report9 §4.8.1 Summer and Winter Traj: **1.7** — the C5:C3 ratio of summer-minimum trend slopes (1.6629); computed as Slope_m_per_yr C5 / C3 in 14_summer_trend_stats.csv = -0.0291/-0.0175
- report10 §5.7.2 Forest Management Scen: **2.5** — the C5:C1 ratio of Slope_m_per_yr in 14_summer_trend_stats.csv (-0.0291 / -0.0115 = 2.5304)
- report12 §7 Conclusions: **2.5** — the C5:C1 full-record summer-minimum slope ratio (2.530 = C5 Slope_m_per_yr -0.0291 / C1 Slope_m_per_yr -0.0115, 14_summer_trend_stats.csv)

### Script 14b (2)

- report10 §5.8 The Reach of Forest Mana: **0.2** — the gap between each cluster mean summer minimum and each threshold (absolute distance from the mean Summer_Min in 14_annual_extremes.csv to Threshold_m in 14b_year_of_crossing.csv: SD15b C1 0.2399, C2 0.3252 m, both deeper than the threshold; SD16 C1 0.1301, C2 0.0448 m, both shallower than it)
- report10 §5.8 The Reach of Forest Mana: **0.4** — the gap between each cluster mean summer minimum and each threshold (SD15b: C1 0.2399, C2 0.3252 m)

### Script 15 (1)

- report9 §4.4 Model Benchmarking: Stat: **0.43** — the 1/e decay depth 1/Best_Kappa per cluster (C1 = 0.4348 m, C2 1.053, C3 2.222, C4 20.0, C5 2.222; from Best_Kappa in 15_04_best_params.csv)

### Script 17 (3)

- report9 §4.2.4 Specific Yield Estimat: **+0.09** — the clip shift (Sy_event_median_unclipped - Sy_event_median) per cluster (C1 +0.0910, C2 +0.1372, C3 +0.1256, C4 +0.1244, C5 +0.2531)
- report9 §4.2.4 Specific Yield Estimat: **1.27** — the mean ratio Sy_OLS_winter / Sy_event_median across the five clusters and the count of clusters with ratio > 1 (mean 1.2652, count 4 of 5)
- report9 §4.2.4 Specific Yield Estimat: **0.035** — the between-estimator range of Sy per cluster (C3 = 0.3486 - 0.3141 = 0.0345: max-min of Sy_event_median, Sy_rapid_median, Sy_OLS_winter)

### Script 19 (1)

- report9 §4.13.2 Forest Management Sce: **14** — n_wells in the two forest clusters (C4 9 + C5 5 = 14)

### Script 20 (12)

- report8 §3.5.4 Clearfell BACI experim: **101** — the diffusivity Kb/Sy (100.6 m2 per day = drawdown_lambda^2 * beta3_C3 / DAYS_PER_MONTH)
- report8 §3.8.1 Baseline Fields, Combi: **56** — the broadleaf-restock source magnitude (56.25 mm)
- report8 §3.8.2 Drawdown-Field visuali: **130** — the lambda sensitivity range across K = 2-20 m/day (128.7 to 407.0 m) and across b = 3-8 m (172.7 to 282.0 m)
- report8 §3.8.2 Drawdown-Field visuali: **410** — the lambda sensitivity range across K = 2-20 m/day (129 to 407 m)
- report8 §3.8.2 Drawdown-Field visuali: **840** — the SLR diffusive length 2*sqrt(D*t) (857 m from the committed inputs; the text says about 840 m)
- report9 §4.9.6 Water Balance Residual: **252** — residual_window_months, residual_p_bar_mm and residual_pet_bar_mm (the realised averaging window of the residual field) (252 months); computed as 01_climate.csv rows from the first to last month of the mean-head record maod (2005-03 to 2026-02): 252 months, mean P_m x 1000 = 74.1115, mean PET x 1000 = 54.3882
- report9 §4.11 Management influence on: **1.7** — ceh11_to_eastern_lake_edge_group_dist_min_m (1732.44 m = min over ceh27, ceh26, ceh23, ceh25, ceh5, ceh6 of Euclidean distance from ceh11 (242618.620, 362688.287) using E, N of 20_drawdown_perwell.csv)
- report9 §4.11 Management influence on: **2.0** — ceh11_to_eastern_lake_edge_group_dist_max_m (2036.63 m = max over ceh27, ceh26, ceh23, ceh25, ceh5, ceh6 of Euclidean distance from ceh11 (242618.620, 362688.287) using E, N of 20_drawdown_perwell.csv; companion of the _min_m row 1732.44)
- report9 §4.12 Combined Driver Assessm: **135** — the maximum of the combined scrape-plus-coastal baseline drawdown field (about 135 mm)
- report10 §5.7.5 Parametric Prediction : **−50** — the range of the net-state field over the forest interior (sentence quotes -50 to over -150 mm; DRAWDOWN_H0_MM = 150 [config.py] is the canopy term alone)
- report10 §5.7.5 Parametric Prediction : **59** — msl5_n_wells (59 = rows of 20_msl5_change_perwell.csv, wells carrying an MSL5 2017-to-2023 change)
- report10 §5.7.9 The 1951--53 Record: F: **60** — the modelled canopy drawdown dd_mm at each Ranwell Clwt Gwlyb site (sites 4, 11, 12, 13) so that the 60-80 mm range can be read from a file

### Script 21 (1)

- report10 §5.5.2 Forest Management Scen: **30** — the C5-to-C4 ratio of annual water-equivalent gain under clearfell and thinning (1.294)

### Script 23 (1)

- report10 §5.2.1 Water Balance Residual: **49** — the count of Bartlett-significant-peak wells as a value row (49; it is carried only in the Era cell of ridge_lag_spearman_rho_peak_lag_vs_distance in 23_report_numbers.csv)

### Script 24 (3)

- report10 §5.2.1 Water Balance Residual: **63** — wells analysed (63 = rows of 24_residual_climatology.csv), winter-peaking count (48 = phase_month>=11 or <=3) and summer-peaking count (0 = phase_month between 5 and 8 inclusive) to 24_report_numbers.csv; the three values are already computed in src/24 lines 617-620 and printed to 24_05_diagnostic_summary.txt
- report10 §5.3.1 Recharge Partitioning : **48** — wells with a winter/early-spring phase peak (48 of 63) to 24_report_numbers.csv
- report10 §5.3.1 Recharge Partitioning : **63** — wells analysed (63 = rows of 24_residual_climatology.csv) and winter-peaking count (48) to 24_report_numbers.csv

### Script 25 (7)

- report9 §4.10.2 Network-scale partiti: **1.6** — ForestFree_ref_disagreement_lincap_vs_exp (1.6338 mm/yr = |delta_ref_mm_yr(forest_free, linear_capped) - delta_ref_mm_yr(forest_free, exponential)| = |-26.37844515884186 - (-28.01224808241651)|, the 150 m counterpart of ForestFree_d0_disagreement_lincap_vs_exp)
- report9 §4.10.2 Network-scale partiti: **1.9** — delta0_loo_max_to_second_ratio (1.8728 = |delta0_loo_max_shift_mm_yr| / |delta0_loo_second_shift_mm_yr| = 3.128996626994187 / 1.6707663108716808, from 25_16_delta0_leave_one_out.csv d_delta_0_mm_yr ranks 1 and 2)
- report9 §4.10.3 What the fit cannot r: **151** — the raw-series VIF of elapsed time against the CWB covariate (about 151)
- report9 §4.12 Combined Driver Assessm: **46** — the Check2 well count (46)
- report10 §5.5 The Clearfell Experiment: **402** — the control-minus-impact distance contrast d_control_m − d_target_m for the Forest / Impact BACI corroboration (402 = 955 − 553, 25_04_baci_corroboration.csv); it is carried only in a Note
- report10 §5.7.2 Forest Management Scen: **46** — Check2_msl5raw_vs_summermin_n as a Value row (46 = wells in the merge of 20_msl5_change_perwell.csv and 25_02_per_well_summer_min_slopes.csv on well)
- report10 §5.7.7 What the Record Cannot: **18** — the R2 of the per-well trend on distance to the shore (the sentence says 18 %)

### Script 26 (14)

- report8 §3.7.5 Five-Year Mean Spring : **3.3** — the share of admitted five-year windows containing an interpolated month (29 / 866 = 3.349 %)
- report9 §4.8.3 Five-Year Mean Spring : **0.08** — the largest amount by which a cluster four-year mean annual minimum sits below SD16, per cluster (C2 = 0.08248 m at window-end 2019); computed as SD16(0.98) + min over window_end_year 2014-2025 of MINw_m_bg_mean (window_years==4, cluster_id==2) in 26_curreli_min_per_cluster.csv = 0.98 + (-1.0624833)
- report9 §4.8.3 Five-Year Mean Spring : **1.02** — the C1 minus C5 gap in cluster-mean MSL5 at window-end 2025 (1.01629 m); computed as MSL5_m_bg_mean C1 (-0.132833) minus C5 (-1.149122), window_end_year==2025 rows of 26_msl_5yr_per_cluster.csv
- report9 §4.8.3 Five-Year Mean Spring : **0.81** — the C1 minus C5 gap in the four-year mean annual minimum at window-end 2025 (0.80678 m); computed as MINw_current_m_bg C1 (-0.885) minus C5 (-1.6917754), window_years==4 rows of 26_curreli_min_cluster_threshold_summary.csv
- report9 §4.8.3 Five-Year Mean Spring : **0.19** — the C2 minus C3 gap in cluster-mean MSL5 at window-end 2025 (0.19425 m); computed as MSL5_m_bg_mean C2 (-0.189109) minus C3 (-0.383360), window_end_year==2025 rows of 26_msl_5yr_per_cluster.csv
- report9 §4.8.3 Five-Year Mean Spring : **0.65** — the C1 minus C4 gap in cluster-mean MSL5 at window-end 2025 (0.64774 m); computed as MSL5_m_bg_mean C1 (-0.132833) minus C4 (-0.780570), window_end_year==2025 rows of 26_msl_5yr_per_cluster.csv
- report9 §4.8.3 Five-Year Mean Spring : **0.60** — the C1 minus C4 gap in the four-year mean annual minimum at window-end 2025 (0.59676 m); computed as MINw_current_m_bg C1 (-0.885) minus C4 (-1.4817560), window_years==4 rows of 26_curreli_min_cluster_threshold_summary.csv
- report9 §4.8.3 Five-Year Mean Spring : **83** — n_wells_msl5_map (and the 75/8 split by window_end_year) (83); computed as rows of 26_msl_5yr_latest_per_well.csv; window_end_year==2025 for 75, earlier (2015 x3, 2017 x2, 2019, 2024 x2) for 8
- report9 §4.8.3 Five-Year Mean Spring : **85** — n_wells_msl5_any_window (85 distinct wells in 26_msl_5yr_per_well.csv)
- report9 §4.8.3 Five-Year Mean Spring : **75** — n_wells_msl5_latest_2025 (75 of 83 in 26_msl_5yr_latest_per_well.csv)
- report9 §4.8.3 Five-Year Mean Spring : **+205** — the per-cluster MSL5 step from window-end 2023 to 2024 in mm (C1 84.25, C3 157.06, C4 205.41, C5 140.00) (C4 = 205.41 mm); computed as (MSL5_m_bg_mean at window_end_year 2024 minus 2023) x 1000 from 26_msl_5yr_per_cluster.csv, per cluster_id; sentence agrees for all four
- report9 §4.8.3 Five-Year Mean Spring : **+84** — the per-cluster MSL5 step from window-end 2023 to 2024 (mm): C1 84.25, C3 157.06, C4 205.41, C5 140.00 from 26_msl_5yr_per_cluster.csv
- report9 §4.8.3 Five-Year Mean Spring : **0.6** — the C1 minus C4 and C1 minus C5 gaps in cluster-mean MSL5 at window-end 2025 (C4 0.64774 m, C5 1.01629 m); computed as MSL5_m_bg_mean C1 minus C4 and C5, window_end_year==2025 rows of 26_msl_5yr_per_cluster.csv
- report9 §4.8.4 Equilibrium Wetness In: **0.5** — the Pearson r of Ellenberg-F with each state-space coefficient and storage term over the 18 wells (best |r|) (beta_1 0.4334, beta_2 -0.3447, beta_3 0.3538, Sy_median -0.5440, storage_drainage_index_months -0.4128); computed as np.corrcoef(EbF, column) over the 18 wells of 26_ebf_comparison.csv joined on lower-cased well name; EW

### Script 30 (1)

- report9 §4.2.2 Cluster Mechanistic Ch: **1.20** — the per-cluster median per-well VIF on the 100-month window (C4 1.2028, C1 2.1950, C2 1.6420, C3 1.4322, C5 1.3012; median of VIF grouped by cluster in 30_c4_perwell_beta3.csv)

### Script 32 (1)

- report11 §6.2 Record length --- the di: **28** — the headline minimum detectable site-wide rate (about 28 mm/yr; spring 27.25 and annual 28.54 in 32_site_mean_trend.csv, mean 27.89)

### Script 33 (3)

- report9 §4.12 Combined Driver Assessm: **1.56** — the C4 mean amplification with ceh13 and ceh14 excluded (1.5591 = mean of amplification over the 8 unflagged Cluster == 4 wells of 33_envelope_per_well.csv other than ceh13 and ceh14; unflagged C4 n = 10, mean 1.662813935430809)
- report10 §5.3.2 Drainage Decay and the: **1.56** — the C4 mean amplification excluding ceh13 and ceh14 (1.5590707256644836, n=8; mean of amplification over 33_envelope_per_well.csv rows with Cluster=4.0, flagged=False, key not in {ceh13, ceh14}) to 33_cluster_summary.csv or a report-numbers CSV
- report10 §5.7.5 Parametric Prediction : **0.8** — amp_vs_beta2_r (Pearson of amplification in 33_envelope_per_well.csv against beta_2_atmospheric_draw in 03_master_data.csv joined on well: 0.795, n = 66)

### Script 37 (2)

- report10 §5.7.5 Parametric Prediction : **150** — the SD of per-well residuals by window (178.74, 113.48, 77.57 mm: sample SD of residual_<window> over rows with b3_correction_valid_<window> True and exclude_named_<window> False in 37_driver_validation_per_well.csv)
- report10 §5.7.5 Parametric Prediction : **200** — the spread (SD or MAD) of the per-well driver-validation residuals by window (sentence: of order +/-150 to 200 mm)

### Script 37b (3)

- report9 §4.12.1 Driver validation and: **949** — site_area_ha (949.2 ha, the site-mask area used to normalise the equivalent depths)
- report10 §5.8.2 Climate Trajectory as : **72** — the observed clearfell step as a share of the modelled equilibrium (ANCOVA_Forest_Impact_clearfell_step 0.108230 m / DRAWDOWN_H0_MM 150 mm = 72.15 %)
- report10 §5.8.2 Climate Trajectory as : **949** — the mapped site area on the 50 m grid (949.2 ha)

### Script 39 (1)

- report9 §4.14.1 The 1989--96 record: **0.025** — ccw_annual_range_vs_davy_2010_diff_m (0.02549 m = 0.75 (Davy et al. 2010 literature value) - ccw_annual_range_mean_m 0.7245098039215687)

### Script 40 (1)

- report8 §3.8.2 Drawdown-Field visuali: **0.06** — the 1899-line georeferencing RMSE (5.95 m, a config constant) and its rate over the 1899-2006 interval (5.95 / 106.998 yr = 0.0556 m/yr; years from 40_01_epoch_series.csv pair_extent row)

### Script 41 (1)

- report9 §4.6.8 Temporal decay of the : **1.15** — the mean forest_control ratio_to_conifer over the BACI-window aerial frames (1.1449 for the six aerial frames 2018-06-28 to 2020-04-24; window is an analyst choice)

### Script 43 (1)

- report10 §5.7.9 The 1951--53 Record: F: **120** — each Ranwell site's distance to the nearest forest well (the sentence quotes 120 to 200 m at Clwt Gwlyb)

### Script 44 (2)

- report10 §5.7.9 The 1951--53 Record: F: **0.3** — the 2-sigma exclusion bounds of ranwell_delta_m_combined_beyond_reach (fall -0.08699285572 - 2 x 0.09781012658 = -0.28261 m; rise -0.08699286 + 2 x 0.09781013 = +0.10863 m)
- report10 §5.7.9 The 1951--53 Record: F: **0.1** — the 2-sigma exclusion bounds of ranwell_delta_m_combined_beyond_reach (fall -0.28261 m; rise +0.10863 m)

### Script ? (1)

- report6 §1 Introduction: **4.4** —  Script 13 (which reads clearfell.kml) should emit the clearfell polygon area in ha (4.4255 ha: shoelace area of the clearfell.kml polygon after transforming EPSG:4326 to EPSG:27700)


## 2. For Martin — claims, not digits (the page keeps them amber or red until ruled)

Each is a sentence whose number cannot be settled by reading a file, because the fix changes what the sentence claims. The readers' full notes are in `scratch/resolve_martin_2026-09-29.md` (and `working/updates/NRG_resolve_martin_2026-09-29.md`).

1. **report8 §3.6.3, the m_P worked example** ("a C2 well with a September minimum of 0.5 m … requires m_P = 1.05, giving P_flood ≈ 448 mm — a near-average October–February total"). The committed C2 row (`11_forecast_pflood_threshold_equations.csv`, four-month Oct–Jan horizon) gives m_P = 0.99 and 397 mm at 0.5 m, or m_P = 1.05 and 419 mm at 0.6 m. 1.05/448 is the old five-month horizon. Choices: (a) keep 0.5 m → 0.99, ≈ 397 mm, "October–January", which drops the example into the sub-average class; (b) keep 1.05 → premise 0.6 m, ≈ 419 mm; (c) another depth (m_P = 1.0 at 0.51 m). Script 11 should then emit the example.
2. **report9 §4.2.1–4.2.2, elevation basis.** The text says elevations are "water level above each well's NRW 2 m lidar-derived ground surface"; the pipeline's `ground_elev_m` is DGPS at 75 of 77 surveyed wells. The 3.6 m AOD for CEH11 is the lidar ground (3.584); the DGPS ground is 3.534 (3.5), which the next sentence's "3.5 m" already uses. Reword the method sentence ("DGPS-surveyed where available, otherwise lidar") and let 3.6 → 3.5? The digit is left as it stands pending that.
3. **report9 §4.2.2, the C1 band without CEH11** ("a tight 9.1–10.9 m elevation band"). The six wells' `ground_elev_m` span 8.5–10.9 (CEH6 lowest at 8.461; 9.1 is CEH25). Corrected to 8.5 the clause repeats the previous range and "tight" (2.4 m) no longer holds — a rewording: "the six remaining wells occupy 8.5–10.9 m, CEH6 the lowest".
4. **report9 §4.12 and report8 §3.5.4, "FE1, approximately 20 m outside the felled boundary".** Against `data/geo/clearfell.kml` (the polygon Script 13 draws) FE1 is 46 m outside (CEH20 37.5 m). If another boundary is meant (the compartment edge on the ground), name it and the distance is emitted against that.
5. **report9 §4.12, "correlates above 0.98 with the two-window pattern".** The two-window map (`20_msl5_change_perwell.csv` raw change 2017→2023) correlates with the Script 32 differential slope at r = 0.21 (Spearman 0.06) over 59 wells; 0.47 against the 2005–2025 slope. Either a different quantity was meant (never committed) or the claim reverses.
6. **report9 §4.12.1 and report10 §5.7.5, "the coastal signature is collinear with easting (r ≈ −0.48)".** `37_driver_validation_per_well.csv` coast_i against easting is +0.61 to +0.73 by window (−0.66 to −0.73 as a magnitude); no 0.48 anywhere (the only 0.48 is the unrelated s_coast scale factor). Quote a stated window's value and have Script 37 emit it.
7. **report9 §4.9.2, "70–85 % of monthly variance across the central and northern open dune".** A colour-band reading of Figure 54a; no file defines the region. Per-well R² over C1–C3 runs 0.64–0.87 (median 0.75; 43 of 52 within 0.70–0.85). Keep as a figure reading (literal), replace with the CSV statement, or have Script 07 emit the quantiles.
8. **report9 §4.8.4, "best |r| ≈ 0.5" for a single coefficient or storage term against Ellenberg-F.** The three coefficients alone give 0.43 (→ 0.4); Sy gives 0.54. "≈ 0.5" holds only if Sy is in the set — state the set (Script 26 emits the correlations) or correct to 0.4.
9. **report9 §4.11 (Figure 66/67 caption), "Script 09b, p = 0.54"** for the distance-decay of the BACI-corrected Δβ₃. Not committed; regressions on `09b_01_individual_well_baci.csv` give 0.60 (18 wells), 0.53 (17 non-scraped), 0.43 (10 uphill). Name the test and well set, or drop the p.
10. **report9 §4.5.4, CEH36 MSL5 "approximately −0.50 m across window-ends 2017–2023".** The cells run −0.42 to −0.55, mean −0.485 (→ −0.49), 2020 nearest at −0.505. Keep as a plateau description, or "−0.42 to −0.55 m".
11. **report10 §5.7.5, "about 1× on the open dune".** C2 0.87, C3 1.20, pooled 1.05, network 1.08 (`33_cluster_summary.csv`). Which clusters are "open dune"?
12. **report10 §5.7.7, "survives at p = 0.002 across three methods".** The three ANCOVA specifications (10h A/B/C) give 0.0014, 0.0025, 0.0034; the four-zone and difference-in-differences tests give 0.025 and 0.13–0.27. "p between 0.001 and 0.003 across the three ANCOVA specifications", or drop "three methods".
13. **report10 §5.8.1, "deeper-end wells approach m_P = 1.9".** C3's deepest are wmc3 2.00, nw1 1.81, nw7 1.76 (median 1.27 is right). "1.8 to 2.0", or name the three.
14. **report10 §5.7.5, "correlates with the per-well β₂ (r ≈ 0.8)"** against report9's "r = +0.66" for the same Figure 75: Script 33's amplification gives 0.795 (n = 66); 0.66 is Script 35's `amp_vs_beta2_r`. The two chapters cite different amplification metrics — which is Figure 75's?
15. **report10 §5.8, "within 0.2 to 0.4 m of the SD15b and SD16 thresholds".** True of SD15b (0.24 / 0.33 m for C1 / C2); C1 and C2 are within about 0.1 m of SD16 (C2 already past it in `14b_year_of_crossing.csv`). Reword.
16. **report10 §5.7.9, "drawdown of order 60 to 80 mm" at the Clwt Gwlyb sites.** The configured law at 120–200 m gives 61–88 mm; the per-well cost-distance model 71–93 mm. Script 20 or 44 should emit per site; the upper end may read 90.
17. **report10 §5.7.5, "residual scatter of order ±150 to 200 mm".** Script 37 residual SDs are 179 (2006–12), 113 (2018–25) and 78 mm (2005–25): the range holds for the first window only.
18. **report10 §5.6.2, "mean Δβ₂ +0.169" (corrected to +0.157).** +0.157 is the mean of the four Forest-control wells excluding NW10, +0.169 their median. If the median was meant, the word changes rather than the number.
19. **Seen beside the list, not touched:** report10 §5.6.3 says NW10 is deeper than CEH2 across the record, but `10d_01_summer_minima.csv` has NW10 shallower in all 13 common years (mean −1.518 vs −1.711 m); report10 §5.7.5 calls the summer window "July–September" where Script 25 uses April–September; report10 §5.8.1 "recession time 8 to 10 months, typical of C1" against a C1 centroid 1/β₃ of 11.2; report8 §3.4 "spans at most about 0.09" where the committed widest R² span is 0.085; report9's 17-well BACI caption cites a 22-row file (a sixth Far-field tier).

## 3. Corrections applied in this pass (digits, from committed values)

report8: −9.0 ± 2.5 → ± 2.4 mm (`beta_forest_se_mm_yr` 2.4453); 9 of 1272 (0.8 %) → 0.7 %; Dune stability 0.98 → 0.99 (`cluster_stability_median · C2` 0.9875). report9: 13.32 → 13.33 m AOD (CEH14 mean, `01_wells_clean_maod.csv`); 27–72 (mean 51) → 27–73 (mean 52) `n_events`; "4 wells (5 %)" → "5 wells (6 %)" with m_P ≥ 2.5 (`11b_03_pflood_per_well.csv`; 59 + 24 + 5 = 88); −0.60 → −0.59 (18-year window r); nw9 p 0.016 → 0.017; 157 → 156 mm (5 × δ₀ 31.28); 0.77 → 0.76 (C4 lag-1 expectation at the 65-well scope). report10: 12 of 75 → 12 of 77 wells; 10.1 → 10.2 mm yr⁻¹; ARI 0.52 → 0.53, 5th percentile 0.36 → 0.35; mean Δβ₂ +0.169 → +0.157; C3 half-life about 12 → 11 months (`t_half_A_months` 11.25).
