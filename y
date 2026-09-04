# Newborough Warren pipeline run log
# Started: 2026-09-04T01:15:16
# Command: run_analysis.py

  ℹ Recording console output to: y
  ℹ pipeline release 2.3.0 (2026-08-13); orchestrator module v2.9.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 1  — Core LCSC Chain
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 1/52  Data preparation
      script: 01_data_prep.py
  ──────────────────────────────────────────────────────────────────
  ⚠ [deps] This step reads INT_PEAR_AUDIT_SITEWIDE from 06_pearson_extended.py (step 6); if that hasn't run yet it falls back.
  ⚠ WARNING: 1 wells have locations but no time-series data.
  ⚠ WARNING: 32 comment(s) collided with a genuine measurement (kept the reading) -> 01_observation_state_conflicts.csv

════════════════════════════════════════════════════════════════════════
SCRIPT 01 — Data Preparation  [v1.14.0]
════════════════════════════════════════════════════════════════════════
Starting Data Preparation Pipeline...

========================================
  DATA SANITY CHECK: Metadata vs. Time-Series
========================================
========================================

  · in_forest: 23 of 99 wells inside the plantation boundary.
  · rainfall: 1 month(s) marked missing in the source and carried as NaN — Jun 1941
Complete. Retained 78 wells.
  ▸ Reference: 66 wells
  ▸ Extended:  22 wells
 -> Demoted to extended (not on reference-network whitelist): 6 wells  [FE1, FE2, FE3, ceh22, ceh3, nw8b]
 -> Excluded from both networks (blacklist): 2 wells  [llyn rhos, pdfs]
  ✓ Saved: observation states -> 01_observation_states.csv (250x89); 01_dry_depths.csv (173 dry-at-depth cells)
  ✓ Saved: 01_coverage_states_reference.png  (236 dpi)
  ✓ Saved: coverage figure -> 01_coverage_states_reference.png
  ✓ Saved: 01_coverage_states_extended.png  (236 dpi)
  ✓ Saved: coverage figure -> 01_coverage_states_extended.png

 -> Deriving canonical well geometry...
    ground_elev_m resolved for 99 of 99 wells (21 lidar, 78 dgps)
  ✓ Saved: 01_well_elevations.csv

 -> Converting level series to maOD...
    Converted 78 wells to maOD
  ✓ Saved: 01_wells_clean_maod.csv

 -> Validating well-to-coast distances...
  · dist_coast validation: n=98  median|Δ|=1.52 m  max|Δ|=14.8 m  (tolerance 25 m)
  · dist_coast_m reproduced from committed eroding-shoreline geometry within tolerance.
  ✓ Saved: 01_dist_coast_validation.csv

 -> Writing pipeline scenario parameters...
  Pipeline params: β coefficients loaded from 03_03_cluster_mechanistic_coefficients.csv
  Pipeline params: peak months loaded from 03_cluster_peak_months.csv
  Pipeline params: h_disp loaded from 03_master_data.csv
  Pipeline params: β₂ multipliers loaded (clearfell=1.0189, thinning=1.0094)
  Pipeline params: Sy loaded from 18_wtf_01_well_sy_estimates.csv (5 clusters)
  Pipeline params written: pipeline_scenario_params.csv (5 clusters, 6/6 fields from pipeline)
  All fields populated from pipeline outputs.

 -> Writing pipeline site observations...

=== Script 01 complete ===
  ✓ done  (10.1s)

  ▶ STEP 2/52  Behavioural clustering
      script: 02_clustering.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 02_02_validation_plots.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×5.0 in).
  ⚠ WARNING: Legibility: 02_12_month_stability_diagnostic.png smallest label ~4.8 pt as authored when placed at 160 mm (figsize 13.0×5.5 in).
  ⚠ WARNING:   month-wise co-assignment 0.986 exceeds split-half ARI 0.546 by 0.440, over the 0.25 alert gap: co-assignment is inflated by whole-cluster merging (merge rate 0.993) and is not a reproducibility statistic - quote both (D-030)
  ⚠ WARNING: Legibility: 02_02b_validation_k_sweep.png smallest label ~3.9 pt as authored when placed at 160 mm (figsize 16.0×4.5 in).
  ⚠ WARNING: Legibility: 02_06_coassignment_heatmap_k4.png smallest label ~3.5 pt as authored when placed at 160 mm (figsize 9.0×8.0 in).
  ⚠ WARNING: Legibility: 02_06_coassignment_heatmap_k5.png smallest label ~3.5 pt as authored when placed at 160 mm (figsize 9.0×8.0 in).
  ⚠ WARNING: Legibility: 02_06_coassignment_heatmap_k6.png smallest label ~3.5 pt as authored when placed at 160 mm (figsize 9.0×8.0 in).
  ⚠ WARNING: Legibility: 02_06_coassignment_heatmap_k7.png smallest label ~3.5 pt as authored when placed at 160 mm (figsize 9.0×8.0 in).
  ⚠ WARNING: Legibility: 02_01_dendrogram.png smallest label ~5.0 pt after ×1.49 font scale (cap) when placed at 160 mm (figsize 15.0×8.0 in).
  ⚠ WARNING: Legibility: 02_03_cluster_hydrographs_wb.png smallest label ~3.9 pt as authored when placed at 160 mm (figsize 13.0×8.0 in).
  ⚠ WARNING: Legibility: 02_03b_cluster_spaghetti.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×12.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 02 — k-Means Clustering & Partition  [v1.6.0]
════════════════════════════════════════════════════════════════════════
--- Starting 02: Reference Clustering ---
  ▸ Clustering 66 reference wells...
  ▸ Generating Cluster Validation Plots...
  ✓ Saved: 02_02_validation_plots.png  (135 dpi)
  ✓ Saved: 02_02_validation_plots.png

--- Cluster Stability Diagnostics ---
  ▸ k-sweep validation (k=2..10)...
    silhouette  calinski_harabasz  merge_distance  min_cluster_size  max_cluster_size  n_singletons
k                                                                                                  
2        0.459             25.553           0.546                31                35             0
3        0.442             22.387           0.299                 9                31             0
4        0.408             15.574           0.197                 7                26             0
5        0.396             15.285           0.158                 5                24             0
6        0.358             14.500           0.158                 5                21             0
7        0.388             12.588           0.122                 5                17             0
8        0.363             10.749           0.099                 5                17             0
9        0.364              9.932           0.088                 2                17             0
10       0.363              8.724           0.085                 2                17             0
    Silhouette favours k = 2
    Calinski-Harabasz favours k = 2
  ▸ Saved k-sweep validation: 02_06_k_sweep_validation.csv
  ▸ Month-wise stability at k=5 (1000 block resamples, 12-month blocks)...
  ▸ Saved month-wise stability: 02_11_month_stability.csv
  ✓ Saved: 02_12_month_stability_diagnostic.png  (145 dpi)
  ✓ Saved: 02_12_month_stability_diagnostic.png
  ·   stability to which WELLS : median 0.938
  ·   stability to which MONTHS: median 0.986
  ·   split-half ARI: mean 0.546 (5-95th pct 0.390-0.742, 200 replicates)
  ·   reference clusters surviving intact and unmerged: 1.714 of 5 (>=2 clusters collapsed together in 0.993 of replicates)
  ▸ Saved report numbers: 02_report_numbers.csv (20 rows)
  ✓ Saved: 02_02b_validation_k_sweep.png  (118 dpi)
  ✓ Saved: 02_02b_validation_k_sweep.png
  ▸ Bootstrap stability at k=4 (1000 resamples)...
    Saved membership: /home/john/projects/NRG/outputs/02_clustering/02_07_cluster_membership_k4.csv
  ✓ Saved: 02_06_coassignment_heatmap_k4.png  (210 dpi)
    Saved heatmap:    /home/john/projects/NRG/outputs/02_clustering/02_06_coassignment_heatmap_k4.png
    Memberships at k=4:
      C1 (n=7, median stab=0.98): ceh11, ceh23, ceh25, ceh26, ceh27, ceh5, ceh6
      C2 (n=24, median stab=0.99): D10, D15, D17, D38, D41, D43, D44, D5, D6, D7, D8, D9, L7, T41a, T41b, T41c, T41d, WMC1, ceh10, ceh24, ceh28, nw3, nw4, nw4b
      C3 (n=9, median stab=1.00): Ceh32, ceh13, ceh14, ceh2, ceh20, ceh30, ceh33, ceh34, nw10
      C4 (n=26, median stab=0.71): D25, WMC2, ceh1, ceh16, ceh17, ceh18, ceh19, ceh21, ceh31, ceh36, ceh39, ceh4, ceh40, ceh41, ceh42, ceh9, nw1, nw11, nw13, nw2, nw5, nw6, nw7, nw9, wmc3, wmc4
  ▸ Bootstrap stability at k=5 (1000 resamples)...
    Saved membership: /home/john/projects/NRG/outputs/02_clustering/02_07_cluster_membership_k5.csv
  ✓ Saved: 02_06_coassignment_heatmap_k5.png  (210 dpi)
    Saved heatmap:    /home/john/projects/NRG/outputs/02_clustering/02_06_coassignment_heatmap_k5.png
    Memberships at k=5:
      C1 (n=7, median stab=0.98): ceh11, ceh23, ceh25, ceh26, ceh27, ceh5, ceh6
      C2 (n=24, median stab=0.98): D10, D15, D17, D38, D41, D43, D44, D5, D6, D7, D8, D9, L7, T41a, T41b, T41c, T41d, WMC1, ceh10, ceh24, ceh28, nw3, nw4, nw4b
      C3 (n=9, median stab=1.00): Ceh32, ceh13, ceh14, ceh2, ceh20, ceh30, ceh33, ceh34, nw10
      C4 (n=5, median stab=0.99): ceh16, ceh17, ceh19, ceh31, nw9
      C5 (n=21, median stab=0.49): D25, WMC2, ceh1, ceh18, ceh21, ceh36, ceh39, ceh4, ceh40, ceh41, ceh42, ceh9, nw1, nw11, nw13, nw2, nw5, nw6, nw7, wmc3, wmc4
  ▸ Bootstrap stability at k=6 (1000 resamples)...
    Saved membership: /home/john/projects/NRG/outputs/02_clustering/02_07_cluster_membership_k6.csv
  ✓ Saved: 02_06_coassignment_heatmap_k6.png  (210 dpi)
    Saved heatmap:    /home/john/projects/NRG/outputs/02_clustering/02_06_coassignment_heatmap_k6.png
    Memberships at k=6:
      C1 (n=7, median stab=0.96): ceh11, ceh23, ceh25, ceh26, ceh27, ceh5, ceh6
      C2 (n=17, median stab=0.97): D10, D15, D17, D41, D44, D5, D6, D8, T41b, T41c, T41d, WMC1, ceh24, ceh28, nw3, nw4, nw4b
      C3 (n=7, median stab=0.80): D38, D43, D7, D9, L7, T41a, ceh10
      C4 (n=9, median stab=1.00): Ceh32, ceh13, ceh14, ceh2, ceh20, ceh30, ceh33, ceh34, nw10
      C5 (n=5, median stab=0.99): ceh16, ceh17, ceh19, ceh31, nw9
      C6 (n=21, median stab=0.36): D25, WMC2, ceh1, ceh18, ceh21, ceh36, ceh39, ceh4, ceh40, ceh41, ceh42, ceh9, nw1, nw11, nw13, nw2, nw5, nw6, nw7, wmc3, wmc4
  ▸ Bootstrap stability at k=7 (1000 resamples)...
    Saved membership: /home/john/projects/NRG/outputs/02_clustering/02_07_cluster_membership_k7.csv
  ✓ Saved: 02_06_coassignment_heatmap_k7.png  (210 dpi)
    Saved heatmap:    /home/john/projects/NRG/outputs/02_clustering/02_06_coassignment_heatmap_k7.png
    Memberships at k=7:
      C1 (n=7, median stab=0.92): ceh11, ceh23, ceh25, ceh26, ceh27, ceh5, ceh6
      C2 (n=17, median stab=0.93): D10, D15, D17, D41, D44, D5, D6, D8, T41b, T41c, T41d, WMC1, ceh24, ceh28, nw3, nw4, nw4b
      C3 (n=7, median stab=0.77): D38, D43, D7, D9, L7, T41a, ceh10
      C4 (n=9, median stab=1.00): Ceh32, ceh13, ceh14, ceh2, ceh20, ceh30, ceh33, ceh34, nw10
      C5 (n=5, median stab=0.98): ceh16, ceh17, ceh19, ceh31, nw9
      C6 (n=9, median stab=0.55): D25, WMC2, ceh18, ceh21, ceh36, ceh4, ceh42, nw5, nw6
      C7 (n=12, median stab=0.67): ceh1, ceh39, ceh40, ceh41, ceh9, nw1, nw11, nw13, nw2, nw7, wmc3, wmc4
  ▸ Saved stability summary: 02_04_bootstrap_stability_summary.csv
  ▸ Saved per-well stability: 02_05_bootstrap_stability_per_well.csv

--- Stability diagnostics: quick look ---
  k=4: median stab=0.94  robust (>=0.9): 52%  borderline (0.7-0.9): 32%  fragile (<0.7): 17%
  k=5: median stab=0.94  robust (>=0.9): 53%  borderline (0.7-0.9): 6%  fragile (<0.7): 41%
  k=6: median stab=0.89  robust (>=0.9): 50%  borderline (0.7-0.9): 14%  fragile (<0.7): 36%
  k=7: median stab=0.84  robust (>=0.9): 44%  borderline (0.7-0.9): 20%  fragile (<0.7): 36%
-----------------------------------------

  ↳ Partition target k=5 (analyst-fixed run parameter; silhouette peaks at the trivial k=2 and is NOT used to select k)
  ▸ Saved cluster stats: 02_cluster_stats.csv
     Cluster sizes (canonical IDs):
       C1 (Lake Edge)                 n=7
       C2 (Dune)                      n=24
       C3 (Western Residual)          n=21
       C4 (Main Forest)               n=9
       C5 (Coastal Forest)            n=5
  ▸ Generating Dendrogram...
  ✓ Saved: 02_01_dendrogram.png  (126 dpi, fonts ×1.49)
  ▸ Generating Cluster Hydrograph + Water-Balance Figure...
Long-term mean P-PET (2004-12-01 to 2025-12-01): 19.51 mm/month
Study period: 2005-03-01 to 2026-02-01 (252 months)
Cumulative anomaly range: -376.9 to 157.3 mm
  ✓ Saved: 02_03_cluster_hydrographs_wb.png  (145 dpi)
  ✓ Saved: 02_03_cluster_hydrographs_wb.png
  ▸ Generating Per-Well Spaghetti Figure...
  ✓ Saved: 02_03b_cluster_spaghetti.png  (158 dpi)
  ✓ Saved: 02_03b_cluster_spaghetti.png

--- Cluster Amplitude Descriptors ---
  ▸ Computing per-well amplitude stats (66 wells)...
  ✓ Saved: 02_08_cluster_amplitude_per_well.csv
 -> Aggregating to 5 clusters...
 -> Drought summers (climate normalisation): 2005, 2018, 2022
  ✓ Saved: 02_09_cluster_amplitude_summary.csv
  ✓ Saved: 02_10_cluster_amplitude_boxplot.png  (210 dpi)
  ✓ Saved: 02_10_cluster_amplitude_boxplot.png

--- Amplitude quick look (post-2018) ---
  C1 (Lake Edge)       (n=7):  median 1.00m  range 0.85–1.22  Δpre/post(raw) −19.4%  (climnorm −15.1%)
  C2 (Dune)            (n=24):  median 1.02m  range 0.78–1.37  Δpre/post(raw) −0.1%  (climnorm +8.7%)
  C3 (Western Residual) (n=21):  median 1.01m  range 0.64–1.28  Δpre/post(raw) +1.4%  (climnorm +8.1%)
  C4 (Main Forest)     (n=9):  median 1.09m  range 0.91–1.46  Δpre/post(raw) +5.8%  (climnorm +5.8%)
  C5 (Coastal Forest)  (n=5):  median 0.73m  range 0.58–0.80  Δpre/post(raw) +17.7%  (climnorm +20.7%)
----------------------------------------

  ▸ Clustering Complete.
  ✓ done  (24.9s)

  ▶ STEP 3/52  State-space regression + LCSC
      script: 03_state_space_model.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING:   beta_3 <= 0 at 1 well(s): ceh14 (-0.0207, p=0.143)
  ⚠ WARNING:   a non-positive drainage coefficient makes the iterative simulation in Script 08 divergent; expect a large negative NSE at these wells and do not read it as a physical result
  ⚠ WARNING: Legibility: 03_08_datum_sensitivity.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×14.0 in).
  ⚠ WARNING: Legibility: 03_12_datum_regime.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×10.0 in).
  ⚠ WARNING: Legibility: 03_09_well_optimal_datums.png smallest label ~3.9 pt as authored when placed at 160 mm (figsize 16.0×12.0 in).
  ⚠ WARNING: Legibility: 03_01_mechanistic_signatures.png smallest label ~4.2 pt as authored when placed at 160 mm (figsize 15.0×6.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 03 — State-Space Regression & LCSC  [v1.9.4]
════════════════════════════════════════════════════════════════════════
Starting 03: State-Space Regression & LCSC...
 -> Cluster partition verified: [np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5)] matches config.CLUSTER_LABELS.
  ▸ Upstand lookup loaded: 99 wells.

 -> Upstand audit (threshold > 0.30 m):
    C2: t41a        upstand = 0.400 m
    C3: nw2         upstand = 0.590 m
    C4: ceh2        upstand = 0.710 m

 -> Fitting per-well SSM and computing LCSC...
 -> Saved: 03_master_data.csv (66 wells)
  ▸ Per-well window sensitivity (full record vs comparison window)...
  ·   comparison_window : 60 of 66 wells with a significant positive beta_3
  ·   full_record       : 64 of 66 wells with a significant positive beta_3
  ·   window basis reproduces 03_master_data.csv exactly
  ✓ Saved: 03_15_per_well_window_sensitivity.csv
    [INFO] Per-well sign violations: beta_1<0 in 0 wells, beta_2<0 in 1 wells. Not halting — per-well violations are informational. Centroid-fit violations halt the pipeline.

   PER-WELL AVERAGE STATISTICS BY CLUSTER (window = 100 months)
         beta_1_recharge  ...  Model_R2
Cluster                   ...          
1                  5.012  ...     0.740
2                  4.275  ...     0.726
3                  3.510  ...     0.731
4                  2.474  ...     0.678
5                  2.339  ...     0.684

[5 rows x 5 columns]

 -> Building cluster centroids...

 -> Fitting cluster-centroid SSMs (headline, lag 0)...
  ✓ Saved: 03_03_cluster_mechanistic_coefficients.csv
  ▸ Centroid window sensitivity (full record vs comparison window)...
  ·   C1 (Lake Edge)         full 0.0886 (p=9e-36, n=237)  |  window 0.1026 (p=1.37e-19)  +16%
  ·   C2 (Dune)              full 0.0643 (p=5.5e-26, n=248)  |  window 0.0700 (p=2.9e-13)  +9%
  ·   C3 (Western Residual)  full 0.0569 (p=5.92e-29, n=249)  |  window 0.0558 (p=6.84e-12)  -2%
  ·   C4 (Main Forest)       full 0.0185 (p=0.00163, n=237)  |  window 0.0110 (p=0.251)  -41%   <- not significant on the window
  ·   C5 (Coastal Forest)    full 0.0449 (p=1.09e-16, n=239)  |  window 0.0438 (p=3.77e-07)  -2%
  ✓ Saved: 03_14_centroid_window_sensitivity.csv
  ▸ Centroid composition sensitivity (growing vs stable membership)...
  ·   C1 (Lake Edge)         published 0.0886 -> ref_date 0.0916 (+3.4%), stable 0.0894 (+0.9%)
  ·   C2 (Dune)              published 0.0643 -> ref_date 0.0693 (+7.8%), stable 0.0673 (+4.6%)
  ·   C3 (Western Residual)  published 0.0569 -> ref_date 0.0575 (+0.9%), stable 0.0545 (-4.3%)
  ·   C4 (Main Forest)       published 0.0185 -> ref_date 0.0152 (-17.4%), stable 0.0163 (-11.5%)
  ·   C5 (Coastal Forest)    published 0.0449 -> ref_date 0.0487 (+8.5%), stable 0.0498 (+11.0%)
  ✓ Saved: 03_13_centroid_composition_sensitivity.csv
  Pipeline params updated: β coefficients from Script 03

 -> Lag diagnostic (lags 0, 1, 2, 3 months)...
  ✓ Saved: 03_04_lag_diagnostic.csv

 -> Datum sensitivity analysis (0.5–8.0 m, 0.1 m steps, selected = 3.7 m)...
  ✓ Saved: 03_08_datum_sensitivity.csv
    Minimum datum for all β₃ > 0 & p < 0.05: 1.5 m
    [NOTE] Empirical minimum (1.5 m) differs from DRAINAGE_DATUM (3.7 m) — consider updating config.DRAINAGE_DATUM.
  ✓ Saved: 03_08_datum_sensitivity.png  (158 dpi)
  ✓ Saved: 03_08_datum_sensitivity.png

 -> Datum-regime diagnostic (flux and partition vs datum)...
  ✓ Saved: 03_12_partition_vs_datum.csv
  ✓ Saved: 03_12_datum_regime.png  (158 dpi)
  ✓ Saved: 03_12_datum_regime.png

 -> Per-well datum sensitivity (0.5–8.0 m, 0.1 m steps)...
  ✓ Saved: 03_09_well_datum_sensitivity.csv
  ✓ Saved: 03_09_well_optimal_datums.csv
    60/66 wells have β₃ > 0 & p < 0.05 at some datum
    Median optimal datum: 0.5 m  (IQR: 0.5–0.5 m)
      C1 (Lake Edge)           : median 0.5 m  (range 0.5–0.5, n=7)
      C2 (Dune)                : median 0.5 m  (range 0.5–0.5, n=24)
      C3 (Western Residual)    : median 0.5 m  (range 0.5–0.8, n=21)
      C4 (Main Forest)         : median 1.3 m  (range 0.7–1.6, n=3)
      C5 (Coastal Forest)      : median 0.6 m  (range 0.5–1.7, n=5)
    6 wells never achieved p < 0.05 on β₃ (6 of these achieve β₃ > 0 without significance)

    R²-maximising datum analysis:
      Median R²-max datum: 1.4 m
      Mean R² gain vs uniform 3.7 m: +0.0245
      β₃ negative at R²-max datum: 1/66 wells
        C1 (Lake Edge)           : median datum 0.7 m, R² gain +0.0638, β₃<0 at max: 0/7
        C2 (Dune)                : median datum 0.9 m, R² gain +0.0344, β₃<0 at max: 0/24
        C3 (Western Residual)    : median datum 1.6 m, R² gain +0.0129, β₃<0 at max: 0/21
        C4 (Main Forest)         : median datum 2.8 m, R² gain +0.0015, β₃<0 at max: 1/9
        C5 (Coastal Forest)      : median datum 1.9 m, R² gain +0.0118, β₃<0 at max: 0/5
  ✓ Saved: 03_09_well_optimal_datums.png  (118 dpi)
  ✓ Saved: 03_09_well_optimal_datums.png

 -> Datum confound diagnostics (vs mean water-table depth)...
  • Datum vs mean water-table depth: r=+0.588; easting slope -0.898 m/km (p=0.0000) -> -0.403 m/km (p=0.081) with depth controlled
  • Optimum below mean water table: 65/66 wells
  ✓ Saved: 03_11_datum_confound_diagnostics.csv

 -> Generating spatial datum maps...
  ✓ Saved: 03_10_well_datum_r2max_map.png
  ✓ Saved: 03_10_well_r2_gain_map.png

 -> Bootstrapping centroid fits (B = 1000, seed = 20260424)...
  ✓ Saved: 03_05_bootstrap_ci.csv

 -> Leave-one-well-out centroid fits...
  ✓ Saved: 03_06_leave_one_out.csv

 -> C1 Lake pre/post-2018 split-window diagnostic...
  ✓ Saved: 03_07_c1_split_window.csv
    Loaded amplitude heterogeneity from 02_08_cluster_amplitude_per_well.csv (66 wells matched).
  ✓ Saved: 03_02_cluster_summary_table.csv
  ✓ Saved: 03_01_mechanistic_signatures.png  (126 dpi)
  ✓ Saved: 03_01_mechanistic_signatures.png

==================================================
   FINAL MANUSCRIPT LCSC PERCENTAGES
==================================================
 Coastal Forest   : 43.3%
 Eastern Block    : 23.7%
 Forest           : 41.3%
 Lake Edge        : 20.3%
 Western Block    : 29.8%
==================================================
  ✓ Saved: 03_regional_averages.csv
  ✓ Saved: 03_regional_averages_maod.csv
  C1 (C1 (Lake Edge)): peak month = 1
  C2 (C2 (Dune)): peak month = 1
  C3 (C3 (Western Residual)): peak month = 2
  C4 (C4 (Main Forest)): peak month = 2
  C5 (C5 (Coastal Forest)): peak month = 2
  ✓ Saved: 03_cluster_peak_months.csv
  Pipeline params updated: peak months from Script 03 (5 clusters)

03 complete.
  ✓ done  (84.0s)

  ▶ STEP 4/52  Core cluster visualisation
      script: 04_cluster_visualisations.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 04_01_core_architecture_map.png smallest label ~4.0 pt as authored when placed at 160 mm (figsize 14.0×11.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 04 — Cluster Visualisations  [v1.0.0]
════════════════════════════════════════════════════════════════════════
--- Starting 04: Core Visualization ---
  ✓ Saved: 04_01_core_architecture_map.png  (135 dpi)
  ✓ Saved: 04_01_core_architecture_map.png
  ✓ done  (8.5s)

  ✓ Phase 1 validation passed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 2  — Pearson Membership Audit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 5/52  Pearson membership audit
      script: 05_pearson_affinity.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 05_pear_02_affinity_chart_reference.png smallest label ~3.5 pt as authored when placed at 160 mm (figsize 16.0×7.0 in).
  ⚠ WARNING: Legibility: 05_pear_01_spatial_confidence_map.png smallest label ~4.7 pt as authored when placed at 160 mm (figsize 12.0×10.0 in).
Starting 05: Pearson Membership Affinity Audit...
  ✓ Saved: 05_pear_02_affinity_chart_reference.png  (118 dpi)
  ✓ Saved: 05_pear_01_spatial_confidence_map.png  (158 dpi)

Membership Summary: Core=17 Fuzzy=46 Spy=3 MCA=46
MCA wells: CEH1, CEH16, CEH18, CEH20, CEH21, CEH24, CEH28, CEH30, CEH31, CEH33, CEH34, CEH36, CEH39, CEH40, CEH41, CEH42, CEH9, D10, D15, D17, D25, D38, D41, D43, D44, D5, D6, D7, D8, D9, L7, NW11, NW13, NW3, NW4, NW4B, NW5, NW7, T41A, T41B, T41C, T41D, WMC1, WMC2, WMC3, WMC4
  ✓ Saved: 05_pear_membership_audit.csv, 05_pear_02_affinity_chart_reference.png, 05_pear_01_spatial_confidence_map.png
  ✓ done  (13.2s)

  ▶ STEP 6/52  Pearson extended network integration
      script: 06_pearson_extended.py
  ──────────────────────────────────────────────────────────────────
  ⚠ [deps] This step's outputs are consumed earlier by: 01_data_prep.py (step 1). On a fresh tree those steps used fallbacks — re-run them after this step for final figures.
  ⚠ WARNING: Legibility: 06_pear_01_affinity_chart_extended.png smallest label ~4.3 pt as authored when placed at 160 mm (figsize 16.0×7.0 in).
  ⚠ WARNING: Legibility: 06_pear_02_integration_map.png smallest label ~4.0 pt as authored when placed at 160 mm (figsize 14.0×11.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 06 — Pearson Affinity — Extended Network  [v1.0.0]
════════════════════════════════════════════════════════════════════════
--- Starting Phase 2: Pearson Affinity Audit ---
  ▸ Running correlation matrix against Reference Templates...
  ▸ Audit saved. Found 22 Extended wells.
  ✓ Saved: 06_pear_01_affinity_chart_extended.png  (118 dpi)
  ▸ Generating Pearson Integration Map...
  ✓ Saved: 06_pear_02_integration_map.png  (135 dpi)
Success: Integration Map saved to 06_pear_02_integration_map.png
  ✓ done  (13.7s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 3  — Model Diagnostics and Intervention Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 7/52  Spatial coefficient mapping
      script: 07_spatial_coefficients.py
  ──────────────────────────────────────────────────────────────────
Starting SSM07 Spatial Coefficient Mapping...
  Loaded 66 wells from 03_master_data.csv

  Cluster-level SSM coefficient summary
  ------------------------------------------------------------------------------
  Cluster                  n   β₁ mean  β₂ mean  β₃ mean R² mean
  ------------------------------------------------------------------------------
  C1 (Lake Edge)           7     5.012    0.542   0.1030   0.740
  C2 (Dune)               24     4.275    1.588   0.0723   0.726
  C3 (Western Residual)   21     3.510    1.683   0.0569   0.731
  C4 (Main Forest)         9     2.474    2.584   0.0158   0.678
  C5 (Coastal Forest)      5     2.339    1.134   0.0458   0.684
  ------------------------------------------------------------------------------
  ▸ Exported cluster summary to 07_coefficient_summary.csv
  ▸ Saved 07_coeff_01_beta1_recharge.png (5357 KB)
  ▸ Saved 07_coeff_02_beta2_atm_draw.png (5347 KB)
  ▸ Saved 07_coeff_03_beta3_drainage.png (5345 KB)
  ▸ Saved 07_coeff_04_r2_quality.png (5338 KB)
  ▸ Exported map data to 07_coeff_maps_data.csv
  ▸ Exported per-cluster coefficient ranges to 07_coeff_05_cluster_ranges.csv
  ▸ Exported per-cluster coefficient means to 07_cluster_coeff_means.csv
  ▸ Exported 22 report numbers to 07_report_numbers.csv

SSM07 Spatial Coefficient Mapping complete.
  ✓ done  (45.1s)

  ▶ STEP 8/52  Model benchmarking (LCSC vs Traditional)
      script: 08_model_benchmarking.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 08_lcsc_01_ceh6_showdown.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×10.0 in).
  ⚠ WARNING: Legibility: 08_lcsc_02_r2_improvement_map.png smallest label ~4.0 pt as authored when placed at 160 mm (figsize 14.0×11.0 in).
  ⚠ WARNING: Legibility: 08_lcsc_03_nse_improvement_map.png smallest label ~4.0 pt as authored when placed at 160 mm (figsize 14.0×11.0 in).
Starting SSM08 Model Showdown Pipeline...
  Displacement formulation: DRAINAGE_DATUM = 3.7 m
  Rainfall lag: 0 month(s)
 -> Restricting to 66 reference network wells (excluded 12 non-reference + 3 by rule: CEH7/CEH8/CEH37)

 -> Exported SSM08 SSMvTLM stats table (includes NSE): 08_lcsc_model_stats.csv
  ▸ Saved manuscript Table 3 summary: 08_lcsc_04_table3_benchmark_summary.csv
  ✓ Saved: 08_perwell_nse.csv (66 wells)
  ✓ Saved: 08_cluster_nse_medians.csv (5 clusters)
  ✓ Saved: 08_report_numbers.csv (21 report numbers)
  ✓ Saved: 08_lcsc_01_ceh6_showdown.png  (135 dpi)
  ▸ Saved CEH6 showdown: 08_lcsc_01_ceh6_showdown.png
  ✓ Saved: 08_lcsc_02_r2_improvement_map.png  (135 dpi)
  ✓ Saved: 08_lcsc_03_nse_improvement_map.png  (135 dpi)
  ▸ Saved diagnostic map 1: 08_lcsc_02_r2_improvement_map.png
  ▸ Saved diagnostic map 2: 08_lcsc_03_nse_improvement_map.png

SSM08 Model Showdown Complete!
  ✓ done  (15.5s)

  ▶ STEP 9/52  Scraping analysis suite (09a–09e)
      script: run_09_scraping.py
  ──────────────────────────────────────────────────────────────────
  ⚠ [deps] This step reads OUT_20_REPORT_NUMBERS from 20_spatial_figures.py (step 24); if that hasn't run yet it falls back.
  ⚠ [deps] This step reads OUT_18_WELL_SY_TABLE from 18_wtf_spatial.py (step 22); if that hasn't run yet it falls back.
  ⚠ [deps] This step reads OUT_17_SY_TABLE from 17_wtf_specific_yield.py (step 20); if that hasn't run yet it falls back.
  ⚠ WARNING:     floor now 115.9 mm against an observed +23.9 mm — BELOW the floor
  ⚠ WARNING:     floor now 80.5 mm against an observed +22.3 mm — BELOW the floor
  ⚠ WARNING: Legibility: 09_scrape_05_tier1_background_drift.png smallest label ~4.7 pt as authored when placed at 160 mm (figsize 16.0×12.0 in).
  ⚠ WARNING: Legibility: 09_scrape_06_tier2_scraping_signal.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×18.0 in).
  ⚠ WARNING: Legibility: 09b_05_summer_scenario_comparison.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×7.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 09 — Scraping Pipeline Orchestrator  [v1.0.0]
════════════════════════════════════════════════════════════════════════
========================================================================
SCRAPING ANALYSIS SUITE
Modules: 09a, 09b, 09c, 09d, 09e
========================================================================

────────────────────────────────────────────────────────────────────────
Running 09a: 09a_paired_baci
────────────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 09a — HIERARCHICAL PAIRED BACI ANALYSIS  [v2.9.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading Climate and Well Data ────────────────────────────

──  Phase 2 · Running Master Statistical Analysis ──────────────────────

──  Phase 3 · Exporting CSV files ──────────────────────────────────────
  · CEH21 vs CEH22, 2023 re-scrape: step-only reproduces the era contrast (+73.5465 mm, |diff| 5.55e-17 m)
  ▸ CEH21 vs CEH22, 2023 re-scrape: step +73.5 mm (p=0.01467) -> +23.9 mm with a trend (p=0.563); pre-window trend +16.5 mm/yr (p=0.009666)
  · CEH18 vs CEH4, 2023 re-scrape: step-only reproduces the era contrast (+8.4709 mm, |diff| 3.12e-17 m)
  ▸ CEH18 vs CEH4, 2023 re-scrape: step +8.5 mm (p=0.6054) -> +22.3 mm with a trend (p=0.4371); pre-window trend -4.0 mm/yr (p=0.5924)
  ↳ CEH36 vs CEH4, 2015 scrape (positive control): era contrast not comparable — window spans more than 1_Baseline and 2_Pure_Scraping (the post side continues past this era), so the step-only coefficient is a different contrast and is NOT asserted equal
  ▸ CEH36 vs CEH4, 2015 scrape (positive control): step +147.2 mm (p=2.979e-17) -> +99.5 mm with a trend (p=0.0002119); pre-window trend +15.3 mm/yr (p=0.1055)
  ·     floor now 75.3 mm against an observed +99.5 mm — above the floor
  ✓ Saved: 09_scrape_09_monthly_step_trend.csv (3 pairs)
  ✓ Saved: 09_scrape_10_detectability.csv (15 rows)

──  Phase 4 · Generating the Visual Suite ──────────────────────────────
  ✓ Saved: 09_scrape_05_tier1_background_drift.png  (118 dpi)
  ✓ Saved: 09_scrape_05_tier1_background_drift.png
  ✓ Saved: 09_scrape_06_tier2_scraping_signal.png  (135 dpi)
  ✓ Saved: 09_scrape_06_tier2_scraping_signal.png
  ✓ Saved: 09_scrape_07_beta3_confidence.png  (172 dpi)
  ✓ Saved: 09_scrape_07_beta3_confidence.png

--- Absolute Paired-BACI Shifts ---
 Well            Shift   Delta_m       Control
CEH36    Pure_Scraping  0.129426          CEH4
CEH36    Felling_Pulse  0.023607          CEH4
 CEH4    Pure_Scraping -0.014945 Regional Mean
 CEH4    Felling_Pulse -0.087856 Regional Mean
CEH18    Felling_Pulse  0.029706          CEH4
CEH18   After_Scraping  0.008471          CEH4
CEH21 Coastal_Drawdown  0.043085         CEH22
CEH21   After_Scraping  0.073547         CEH22
CEH22 Coastal_Drawdown -0.165167 Regional Mean
CEH22   After_Scraping -0.129491 Regional Mean

Exporting report numbers CSV...
  ✓ Saved: 09_scrape_report_numbers.csv (49 rows)

Done.

────────────────────────────────────────────────────────────────────────
Running 09b: 09b_scraping_propagation
────────────────────────────────────────────────────────────────────────
======================================================================
09b — Scraping Propagation Analysis
======================================================================

──  Phase 1 · Loading data ─────────────────────────────────────────────
   Wells (clean): 78 columns
   Wells (extended): 22 columns
   Climate: 1143 months

──  Phase 2 · Fitting split-window SSMs ────────────────────────────────
   Pre-scrape window:  start of record – Apr 2015
   Post-scrape window: Apr 2015 – Dec 2017
   Fitted 18 wells ({'uphill': 10, 'control': 7, 'scraped': 1})

──  Phase 3 · Computing BACI correction ────────────────────────────────
   Control centroid raw shifts (n=7 wells):
     Δβ₁ = +0.105
     Δβ₂ = +0.466
     Δβ₃ = +0.0004 (+0.4 × 10⁻³)

   Uphill wells (BACI-corrected):
     ceh31     C5    247m  Δβ₃= +4.3×10⁻³  n_pre=56
     wmc3      C3    262m  Δβ₃= +8.6×10⁻³  n_pre=64
     nw6       C3    284m  Δβ₃= +0.3×10⁻³  n_pre=109
     nw7       C3    383m  Δβ₃= +2.3×10⁻³  n_pre=105
     ceh30     C4    463m  Δβ₃= +6.3×10⁻³  n_pre=57
     ceh20     C4    523m  Δβ₃= +4.8×10⁻³  n_pre=76
     ceh33     C4    550m  Δβ₃= +4.5×10⁻³  n_pre=56
     ceh9      C3    571m  Δβ₃= +7.3×10⁻³  n_pre=98
     ceh34     C4    606m  Δβ₃= -6.1×10⁻³  n_pre=54
     ceh 1     C3    776m  Δβ₃= +1.2×10⁻³  n_pre=107

──  Phase 4 · Computing centroid summaries ─────────────────────────────
   CEH36 (scraped) (1 wells):
     BACI Δβ₁=+0.132  Δβ₂=-0.406  Δβ₃=+2.7×10⁻³ (+5%)
   C3+CEH31 (non-forest uphill) (6 wells):
     BACI Δβ₁=+0.191  Δβ₂=+0.126  Δβ₃=+3.3×10⁻³ (+7%)
   C4 (forest uphill) (4 wells):
     BACI Δβ₁=+0.310  Δβ₂=-0.017  Δβ₃=+2.8×10⁻³ (+9%)
   All uphill (10 wells):
     BACI Δβ₁=+0.122  Δβ₂=-0.019  Δβ₃=+4.1×10⁻³ (+10%)

──  Phase 5 · Exporting CSVs ───────────────────────────────────────────
   → 09b_01_individual_well_baci.csv
   → 09b_02_centroid_summaries.csv

──  Phase 6 · Generating CEH36 equilibration figure ────────────────────
  ✓ Saved: 09b_03_ceh36_equilibration.jpg  (135 dpi)
   → 09b_03_ceh36_equilibration.jpg

──  Phase 7 · Generating scenario comparison figure ────────────────────
  ✓ Saved: 09b_04_scenario_comparison.jpg  (135 dpi)
   → 09b_04_scenario_comparison.jpg
   → 09b_04_scenario_comparison.csv

──  Phase 8 · Generating volumetric summer-forcing scenario comparison ─
   Sy from Script 17: C1=0.210, C2=0.267, C3=0.327, C4=0.260, C5=0.321
   Scraping (CEH36 vs CEH18): +143 mm head (+46 mm w.e./month volumetric)  p = 0.017
   Clearfell volumetric: C4=+8.6  C5=+10.9 mm w.e./month
   Thinning 50% volumetric: C4=+4.3  C5=+5.4 mm w.e./month
   Broadleaf volumetric: C4=-0.7  C5=+1.7 mm w.e./month
  ✓ Saved: 09b_05_summer_scenario_comparison.png  (135 dpi)
   → 09b_05_summer_scenario_comparison.png
   → 09b_05_summer_scenario_comparison.csv  ⚠ WARNING: Legibility: 09c_03_summer_minima_climate_ctrl.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×14.0 in).
  ⚠ WARNING: Legibility: 09c_04_summer_minima_paired.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×10.0 in).
  ⚠ WARNING: Legibility: 09c_07_spring_means_climate_ctrl.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×14.0 in).
  ⚠ WARNING: Legibility: 09c_08_spring_means_paired.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×10.0 in).
  ⚠ WARNING: Legibility: 09d_01_scenario_comparison.jpg smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×6.8 in).
  ⚠ WARNING: Legibility: 09d_02_summer_scenario_comparison.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×6.8 in).


Done.

────────────────────────────────────────────────────────────────────────
Running 09c: 09c_summer_minima
────────────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 09c — SEASONAL BACI ANALYSIS (DUAL CONTROL) — SUMMER MINIMA + SPRING MEANS  [v1.6.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  · Metric: summer minimum (Jun–Sep)

──  Phase 2 · Computing annual summer minimums ─────────────────────────
   5 wells, 15 centroid years

──  Phase 3 · Exporting per-well summer minimums ───────────────────────
  ✓ Saved: 09c_01_summer_minima.csv (75 rows)

──  Phase 4 · Computing pre/post shifts ────────────────────────────────
  ✓ Saved: 09c_02_summer_minima_shifts.csv (8 rows)

   Summer minimum shifts (mm):

   Climate control:
     CEH18     shift =    +22 mm  p = 0.5676
     CEH21     shift =    -60 mm  p = 0.3801
     CEH22     shift =    -52 mm  p = 0.4486
     CEH36     shift =   +161 mm  p = 0.0062 *
     CEH4      shift =    -34 mm  p = 0.3321

   Paired control:
     CEH18     shift =    +56 mm  p = 0.2037
     CEH21     shift =     -8 mm  p = 0.8865
     CEH36     shift =   +194 mm  p = 0.0045 *
  · Characterising scrape equilibration (decay) at CEH36 [summer minimum]
     [Climate] peak +423 mm @ 2017  residual +187 mm  slope(peak→) -16.9 mm/yr  slope(scrape→) -13.9 mm/yr
     [Paired] peak +300 mm @ 2025  residual +182 mm  slope(peak→) n/a (peak at final yr)  slope(scrape→) +7.0 mm/yr

──  Phase 5 · Generating figures ───────────────────────────────────────
  ✓ Saved: 09c_03_summer_minima_climate_ctrl.png  (135 dpi)
  ✓ Saved: 09c_03_summer_minima_climate_ctrl.png
  ✓ Saved: 09c_04_summer_minima_paired.png  (135 dpi)
  ✓ Saved: 09c_04_summer_minima_paired.png
────────────────────────────────────────────────────────────────────────
  · Metric: spring mean (Mar–May)

──  Phase 2 · Computing annual spring means ────────────────────────────
   5 wells, 15 centroid years

──  Phase 3 · Exporting per-well spring means ──────────────────────────
  ✓ Saved: 09c_05_spring_means.csv (74 rows)

──  Phase 4 · Computing pre/post shifts ────────────────────────────────
  ✓ Saved: 09c_06_spring_means_shifts.csv (8 rows)

   Spring mean shifts (mm):

   Climate control:
     CEH18     shift =    -54 mm  p = 0.2312
     CEH21     shift =   -107 mm  p = 0.1913
     CEH22     shift =   -165 mm  p = 0.1927
     CEH36     shift =    +46 mm  p = 0.5367
     CEH4      shift =    -72 mm  p = 0.3893

   Paired control:
     CEH18     shift =    +18 mm  p = 0.7057
     CEH21     shift =    +57 mm  p = 0.2311
     CEH36     shift =   +117 mm  p = 0.0028 *
  · Characterising scrape equilibration (decay) at CEH36 [spring mean]
     [Climate] peak +237 mm @ 2017  residual +22 mm  slope(peak→) -18.8 mm/yr  slope(scrape→) -8.2 mm/yr
     [Paired] peak +173 mm @ 2025  residual +120 mm  slope(peak→) n/a (peak at final yr)  slope(scrape→) +3.9 mm/yr

──  Phase 5 · Generating figures ───────────────────────────────────────
  ✓ Saved: 09c_07_spring_means_climate_ctrl.png  (135 dpi)
  ✓ Saved: 09c_07_spring_means_climate_ctrl.png
  ✓ Saved: 09c_08_spring_means_paired.png  (135 dpi)
  ✓ Saved: 09c_08_spring_means_paired.png

──  Phase 6 · Exporting report numbers ─────────────────────────────────
  ✓ Saved: 09c_report_numbers.csv (32 rows)

Done.

────────────────────────────────────────────────────────────────────────
Running 09d: 09d_scenario_comparison
────────────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 09d — CEH36 SCENARIO COMPARISON  [v3.10.2]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading CEH36 parameters and climate forcings ────────────
   CEH36: b1=2.767  b2=0.908  b3=0.0501  Sy=0.358  h_disp=3.017m  cluster=C3
   Annual-mean climate: P=0.071465  PET=0.053021 m/month
   Summer-mean climate: P=0.064863  PET=0.090155 m/month

──  Phase 2 · Computing scenario responses at CEH36 (annual + summer forcing) 
   Annual-mean forcing:
     β₂ multipliers: clearfell=1.0189  thinning=1.0094
     scenario responses (mm w.e./month):
       Scraping (observed)             +46.4
       Scraping (off-site 100 m)       -31.2
       Clearfell (hypothetical)        +16.7
       Thinning 50% (hypothetical)     +8.3
       Broadleaf (hypothetical)        +5.1
       Climate dry                     -14.1
       Climate wet                     +7.9
   Summer forcing:
     β₂ multipliers: clearfell=1.0189  thinning=1.0094
     scenario responses (mm w.e./month):
       Scraping (observed)             +46.4
       Scraping (off-site 100 m)       -31.2
       Clearfell (hypothetical)        +14.9
       Thinning 50% (hypothetical)     +7.4
       Broadleaf (hypothetical)        +3.6
       Climate dry                     -14.4
       Climate wet                     +7.9

──  Phase 3 · Plotting annual-mean forcing scenario comparison ─────────
  ✓ Saved: 09d_01_scenario_comparison.jpg  (158 dpi)
  ▸ 09d_01_scenario_comparison.jpg
  ▸ 09d_01_scenario_comparison.csv

──  Phase 4 · Plotting summer forcing scenario comparison ──────────────
  ✓ Saved: 09d_02_summer_scenario_comparison.png  (158 dpi)
  ▸ 09d_02_summer_scenario_comparison.png
  ▸ 09d_02_summer_scenario_comparison.csv

Done.

────────────────────────────────────────────────────────────────────────
Running 09e: 09e_robustness
────────────────────────────────────────────────────────────────────────  ⚠ WARNING: Legibility: 09_scrape_08_ceh36_robustness.png smallest label ~4.8 pt as authored when placed at 160 mm (figsize 13.0×11.0 in).


════════════════════════════════════════════════════════════════════════
SCRIPT 09e — CEH36 SCRAPING ROBUSTNESS ANALYSIS  [v2.2.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────

──  Phase 2 · Computing raw BACI ───────────────────────────────────────
   Raw BACI step: +0.129 m

──  Phase 3 · Computing synthetic control ──────────────────────────────
   Synthetic step: +0.137 m (11 donors)

──  Phase 4 · Computing SSM forward residual ───────────────────────────
   SSM residual step: +0.073 m

──  Phase 5 · Generating robustness figure ─────────────────────────────
  ✓ Saved: 09_scrape_08_ceh36_robustness.png  (145 dpi)
  ✓ Saved: 09_scrape_08_ceh36_robustness.png
   Raw BACI step:    +0.129 m
   Synthetic step:   +0.137 m
   SSM residual:     +0.073 m

──  Phase 6 · Exporting report numbers ─────────────────────────────────
  ✓ Saved: 09e_report_numbers.csv

Done.

========================================================================
SCRAPING ANALYSIS SUITE COMPLETE
========================================================================
  ✓ done  (11.3s)

  ▶ STEP 10/52  Clear-fell BACI analysis suite (10a–10m)
      script: run_10_clearfell.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 10i_03_hindcast_diagnostic.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×11.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 10i — CEH34 DONOR-REGRESSION HINDCAST  [v1.2.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────
   CEH34    record: 2010-08-01 → 2026-02-01  (185 months)
   CEH9     record: 2006-05-01 → 2026-02-01  (229 months)

2. Fitting donor regression on pre-clearfell overlap (2010-08-01 to 2017-11-30)...
   Fit: CEH34 = -0.1485 + +1.0515 · CEH9
   α = -0.1485  (SE 0.0346, p = 0.0000)
   β = +1.0515   (SE 0.0371, p < 1e-30)
   r² = 0.9115     RMSE = 124.6 mm     n_cal = 80

──  Phase 3 · Hindcasting CEH34 over pre-record window ─────────────────
   Hindcast covers 51 months: 2006-05-01 → 2010-07-01

──  Phase 4 · Splicing hindcast with observed record ───────────────────
   -> Saved: 10i_01_ceh34_hindcast.csv  (51 hindcast + 185 observed = 236 months)

──  Phase 5 · Exporting regression diagnostics ─────────────────────────
  ✓ Saved: 10i_02_donor_regression.csv

──  Phase 6 · Generating diagnostic figure ─────────────────────────────
  ✓ Saved: 10i_03_hindcast_diagnostic.png  (158 dpi)
  ✓ Saved: 10i_03_hindcast_diagnostic.png

──  Phase 7 · Exporting report numbers ─────────────────────────────────
  ✓ Saved: 10i_report_numbers.csv

========================================================================
HINDCAST SUMMARY
========================================================================
  Target well : CEH34
  Donor well  : CEH9  (Climate Control — independent of Forest Control set)
  Calibration : 80 months, pre-clearfell overlap
  Fit quality : r² = 0.911, RMSE = 124.6 mm
  Hindcast    : 51 months  (2006-05-01 → 2010-07-01)
  Pred. band  : ±244 mm at 95% confidence per month
========================================================================
Script 10i complete.

  ⚠ WARNING: Legibility: 10a_04_baci_timeseries_impact.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×5.0 in).
  ⚠ WARNING: Legibility: 10a_05_baci_timeseries_edge.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×5.0 in).
  ⚠ WARNING: Legibility: 10a_06_climate_sensitivity.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×5.0 in).
  ⚠ WARNING: Legibility: 10a_07_cusum_impact.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×8.0 in).
  ⚠ WARNING: Legibility: 10a_08_cusum_edge.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×8.0 in).
  ⚠ WARNING: Legibility: 10a_S1_baci_timeseries_impact_3panel.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×12.0 in).
  ⚠ WARNING: Legibility: 10a_S2_baci_timeseries_edge_3panel.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×12.0 in).
  ⚠ WARNING: Legibility: 10a_S3_climate_sensitivity_3panel.png smallest label ~3.9 pt as authored when placed at 160 mm (figsize 16.0×10.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 10a — THREE-COUNTERFACTUAL ANCOVA-BACI  [v1.11.1]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────
   [hindcast] CEH34: substituted 51 hindcast value(s) prior to 2010-08-01 (from Script 10i, CEH9 donor)

  Network: 22 wells (6-tier design)
    Impact        : WMC3
    Edge          : CEH31, CEH20, CEH30, CEH16
    Forest Ctrl   : CEH32, CEH34, CEH33, NW10, CEH2
    Coastal Ctrl  : CEH19, CEH17
    Climate Ctrl  : CEH9, NW7, NW6, NW5, WMC2
    Far-field Ctrl: NW4B, WMC1, CEH5, L7, CEH6

  · Far-field control tier: 5 wells, mean 1946 m from the coast, span 866 m, contrast 1393 m against the impact zone at 553 m
  ·   admission threshold 1430 m = 1.60 x the fitted reach 894 m (25_01_panel_fit_parameters.csv); members clearing it: 5/5
     NW4B      d =  1471.7 m   clears threshold
     WMC1      d =  1630.5 m   clears threshold
     CEH5      d =  2075.5 m   clears threshold
     L7        d =  2211.9 m   clears threshold
     CEH6      d =  2338.0 m   clears threshold

──  Phase 2 · Building BACI displacement time-series ───────────────────

──  Phase 3 · Running three-counterfactual ANCOVA ──────────────────────
   Forest control × Impact... step = +113 mm  CI = [+42, +184]  p = 0.0021  R² = 0.241
   Forest control × Edge... step = +30 mm  CI = [-21, +80]  p = 0.2486  R² = 0.457
   Climate control × Impact... step = -15 mm  CI = [-63, +34]  p = 0.5551  R² = 0.206
   Climate control × Edge... step = -107 mm  CI = [-167, -46]  p = <0.001  R² = 0.241
   Combined control × Impact... step = +70 mm  CI = [+34, +105]  p = <0.001  R² = 0.256
   Combined control × Edge... step = -20 mm  CI = [-46, +6]  p = 0.1289  R² = 0.484
   FarField control × Impact... step = -81 mm  CI = [-203, +40]  p = 0.1895  R² = 0.050
   FarField control × Edge... step = -158 mm  CI = [-291, -25]  p = 0.0210  R² = 0.075

3a. Direct summer (Jun-Sep) ANCOVA — Forest × Impact...
   Summer panel: N = 52  (pre-fell 23, post-fell 29)
   Full spec  : step = +50 mm  CI = [-67, +168]  p = 0.4080  R² = 0.315  AIC = -232.42
   No-CWB     : step = +123 mm  CI = [-1, +247]  p = 0.0584  R² = 0.098  AIC = -222.12
   ΔAIC (full − no-CWB) = -10.30  (CWB retained preferred)

3b. Curvature (CWB² × felling) variant — Forest × Impact, Edge...
   Impact: cwb2_x_fell = -1.551e-06  p = 0.1705  ΔAIC = +0.63  joint F = 1.62 (p = 0.2010)  step +113→+127 mm
   Edge: cwb2_x_fell = -9.116e-07  p = 0.2806  ΔAIC = -2.27  joint F = 3.04 (p = 0.0509)  step +30→+34 mm

3c. Per-control-well spread — refitting each tier one control well at a time...
   Forest     × Impact  tier step = +113 mm   per-well steps +12 to +143 mm (n=5, SD=54 mm)
   Forest     × Edge    tier step = +30 mm   per-well steps -37 to +51 mm (n=5, SD=34 mm)
   Climate    × Impact  tier step = -15 mm   per-well steps -49 to +41 mm (n=5, SD=34 mm)
   Climate    × Edge    tier step = -107 mm   per-well steps -129 to -53 mm (n=5, SD=29 mm)
   Combined   × Impact  tier step = +70 mm   per-well steps -49 to +143 mm (n=12, SD=63 mm)
   Combined   × Edge    tier step = -20 mm   per-well steps -129 to +51 mm (n=12, SD=61 mm)
   FarField   × Impact  tier step = -81 mm   per-well steps -146 to -3 mm (n=5, SD=55 mm)
   FarField   × Edge    tier step = -158 mm   per-well steps -214 to -79 mm (n=5, SD=50 mm)

──  Phase 4 · Scraping decay sensitivity (λ = 200 m, 500 m) ────────────
   Clearfell steps by λ:
     λ=200  Forest     Impact    step = +113 mm  p = 0.0021
     λ=200  Forest     Edge      step = +30 mm  p = 0.2486
     λ=200  Climate    Impact    step = -15 mm  p = 0.5551
     λ=200  Climate    Edge      step = -107 mm  p = <0.001
     λ=200  Combined   Impact    step = +70 mm  p = <0.001
     λ=200  Combined   Edge      step = -20 mm  p = 0.1289
     λ=200  FarField   Impact    step = -81 mm  p = 0.1895
     λ=200  FarField   Edge      step = -158 mm  p = 0.0210
     λ=500  Forest     Impact    step = +113 mm  p = 0.0021
     λ=500  Forest     Edge      step = +30 mm  p = 0.2486
     λ=500  Climate    Impact    step = -15 mm  p = 0.5551
     λ=500  Climate    Edge      step = -107 mm  p = <0.001
     λ=500  Combined   Impact    step = +70 mm  p = <0.001
     λ=500  Combined   Edge      step = -20 mm  p = 0.1289
     λ=500  FarField   Impact    step = -81 mm  p = 0.1895
     λ=500  FarField   Edge      step = -158 mm  p = 0.0210

──  Phase 5 · Exporting comparison table ───────────────────────────────
  ✓ Saved: 10a_01_ancova_comparison_table.csv (8 rows)
  ✓ Saved: 10a_02_ancova_full_coefficients.csv (48 rows)
  ✓ Saved: 10a_02b_drift_design_equivalence.csv (16 rows)
  ✓ Saved: 10a_09_control_well_spread.csv (54 rows)

──  Phase 6 · Exporting BACI time-series data ──────────────────────────
  ✓ Saved: 10a_03_baci_timeseries.csv (1244 rows)

──  Phase 7 · Generating figures ───────────────────────────────────────
  ✓ Saved: 10a_04_baci_timeseries_impact.png  (135 dpi)
  ✓ Saved: 10a_04_baci_timeseries_impact.png
  ✓ Saved: 10a_05_baci_timeseries_edge.png  (135 dpi)
  ✓ Saved: 10a_05_baci_timeseries_edge.png
   Climate sensitivity (Forest control)...
  ✓ Saved: 10a_06_climate_sensitivity.png  (135 dpi)
  ✓ Saved: 10a_06_climate_sensitivity.png
   CUSUM (Forest control)...
  ✓ Saved: 10a_07_cusum_impact.png  (135 dpi)
  ✓ Saved: 10a_07_cusum_impact.png
  ✓ Saved: 10a_08_cusum_edge.png  (135 dpi)
  ✓ Saved: 10a_08_cusum_edge.png
   Supplementary three-panel figures...
  ✓ Saved: 10a_S1_baci_timeseries_impact_3panel.png  (135 dpi)
  ✓ Saved: 10a_S1_baci_timeseries_impact_3panel.png
  ✓ Saved: 10a_S2_baci_timeseries_edge_3panel.png  (135 dpi)
  ✓ Saved: 10a_S2_baci_timeseries_edge_3panel.png
  ✓ Saved: 10a_S3_climate_sensitivity_3panel.png  (118 dpi)
  ✓ Saved: 10a_S3_climate_sensitivity_3panel.png

──  Phase 9 · Exporting report numbers ─────────────────────────────────

3d. Coastal scale factor s_coast (M14 / D-076) ...
   Forest    Impact  Δδ=-10.70 mm/yr  absorbed=-17.04  s_coast=+1.592 ± 0.442  (p vs 0 <0.001, p vs 1 0.1823)
   Forest    Edge    Δδ= -9.50 mm/yr  absorbed=-11.66  s_coast=+1.228 ± 0.360  (p vs 0 <0.001, p vs 1 0.5269)
   Climate   Impact  Δδ= -0.94 mm/yr  s_coast=-7.71 ± 3.31  — NOT IDENTIFIED (SE > 2.0: cannot separate s = 1 from s = 0; these tiers sit at nearly the same distance from the shore)
   Climate   Edge    Δδ= +0.26 mm/yr  s_coast=+45.67 ± 15.21  — NOT IDENTIFIED (SE > 2.0: cannot separate s = 1 from s = 0; these tiers sit at nearly the same distance from the shore)
   Combined  Impact  Δδ= -3.74 mm/yr  absorbed= -5.00  s_coast=+1.338 ± 0.608  (p vs 0 0.0295, p vs 1 0.5793)
   Combined  Edge    Δδ= -2.53 mm/yr  absorbed= +0.03  s_coast=-0.010 ± 0.670  (p vs 0 0.9878, p vs 1 0.1341)
   FarField  Impact  Δδ=-13.10 mm/yr  absorbed=+19.76  s_coast=-1.508 ± 0.613  (p vs 0 0.0149, p vs 1 <0.001)
   FarField  Edge    Δδ=-11.89 mm/yr  absorbed=+23.59  s_coast=-1.984 ± 0.756  (p vs 0 0.0095, p vs 1 <0.001)
  ✓ Saved: 10a_09_coastal_scale_factor.csv (8 rows)
   Forest    Impact  step +113.1 mm (s free) -> +77.2 mm (s fixed at 1, p=0.0018)
   Forest    Edge    step +29.7 mm (s free) -> +17.8 mm (s fixed at 1, p=0.3085)
   Combined  Impact  step +69.7 mm (s free) -> +62.3 mm (s fixed at 1, p=<0.001)
   Combined  Edge    step -20.2 mm (s free) -> -5.5 mm (s fixed at 1, p=0.5410)
   FarField  Impact  step -81.4 mm (s free) -> +104.2 mm (s fixed at 1, p=0.0188)
   FarField  Edge    step -158.2 mm (s free) -> +34.6 mm (s fixed at 1, p=0.4825)
  ✓ Saved: 10a_10_coastal_fixed1_sensitivity.csv (6 rows)
   Scraping distance weights:
     WMC3      d =    262 m   weight = 0.417
     CEH31     d =    247 m   weight = 0.438
     CEH20     d =    523 m   weight = 0.175
     CEH30     d =    463 m   weight = 0.214
     CEH16     d =    354 m   weight = 0.307
     CEH32     d =    697 m   weight = 0.098
     CEH34     d =    606 m   weight = 0.133
     CEH33     d =    550 m   weight = 0.160
     NW10      d =   1055 m   weight = 0.030
     CEH2      d =    721 m   weight = 0.090
     CEH19     d =    388 m   weight = 0.274
     CEH17     d =    447 m   weight = 0.225
     CEH9      d =    571 m   weight = 0.149
     NW7       d =    383 m   weight = 0.279
     NW6       d =    284 m   weight = 0.389
     NW5       d =    619 m   weight = 0.127
     WMC2      d =    853 m   weight = 0.058
     NW4B      d =   1331 m   weight = 0.012
     WMC1      d =   1640 m   weight = 0.004
     CEH5      d =   1787 m   weight = 0.003
     L7        d =   1978 m   weight = 0.001
     CEH6      d =   2036 m   weight = 0.001
  ✓ Saved: 10a_report_numbers.csv (175 rows)

========================================================================
ANCOVA-BACI SUMMARY
========================================================================

  Impact zone:
  Control       Step (mm)                   CI          p     R²
  ------------------------------------------------------------
  Forest             +113 [    +42,    +184]     0.0021  0.241
  Climate             -15 [    -63,     +34]     0.5551  0.206
  Combined            +70 [    +34,    +105]     <0.001  0.256
  FarField            -81 [   -203,     +40]     0.1895  0.050

  Edge zone:
  Control       Step (mm)                   CI          p     R²
  ------------------------------------------------------------
  Forest              +30 [    -21,     +80]     0.2486  0.457
  Climate            -107 [   -167,     -46]     <0.001  0.241
  Combined            -20 [    -46,      +6]     0.1289  0.484
  FarField           -158 [   -291,     -25]     0.0210  0.075

  Scraping decay λ = 300 m
========================================================================
Script 10a complete.

  ⚠ WARNING: Legibility: 10b_spatial_scrape_raw.png smallest label ~4.0 pt as authored when placed at 160 mm (figsize 14.0×11.0 in).
  ⚠ WARNING: Legibility: 10b_spatial_fell_raw.png smallest label ~4.0 pt as authored when placed at 160 mm (figsize 14.0×11.0 in).
  ⚠ WARNING: Legibility: 10b_spatial_scrape_corrected.png smallest label ~4.0 pt as authored when placed at 160 mm (figsize 14.0×11.0 in).
  ⚠ WARNING: Legibility: 10b_spatial_fell_corrected.png smallest label ~4.0 pt as authored when placed at 160 mm (figsize 14.0×11.0 in).

──  Phase 1 · Loading well time series ─────────────────────────────────
   [hindcast] CEH34: substituted 51 hindcast value(s) prior to 2010-08-01 (from Script 10i, CEH9 donor)
   89 well columns loaded

──  Phase 2 · Computing step changes ───────────────────────────────────
   Climate reference (C3W controls, n=4: NW5, NW6, NW7, CEH1):
     Scraping baseline: +0.0025 m
     Clearfell baseline: +0.0743 m
   Scrape step: 74 wells
   Clearfell step: 71 wells

──  Phase 3 · Building four spatial figures ────────────────────────────
  ✓ Saved: 10b_spatial_scrape_raw.png  (135 dpi)
  ✓ Saved: 10b_spatial_scrape_raw.png
  ✓ Saved: 10b_spatial_fell_raw.png  (135 dpi)
  ✓ Saved: 10b_spatial_fell_raw.png
  ✓ Saved: 10b_spatial_scrape_corrected.png  (135 dpi)
  ✓ Saved: 10b_spatial_scrape_corrected.png
  ✓ Saved: 10b_spatial_fell_corrected.png  (135 dpi)
  ✓ Saved: 10b_spatial_fell_corrected.png
  ▸ Saved step data: 10b_spatial_step_data.csv

========================================================================
SPATIAL STEP-CHANGE SUMMARY
========================================================================

Clearfell zone (<350 m from centroid): n=15
  Raw fell step:  mean=+0.0811 m, median=+0.0841 m
  Corrected:      mean=+0.0068 m, median=+0.0098 m

C3W reference: n=4
  Raw fell step:  mean=+0.0782 m, median=+0.0743 m

Clearfell vs C3W: +0.0030 m (negative = clearfell wetter)

Quadrant comparison (raw fell step):
  NW: n= 2  mean=+0.0961 m  Clearfell − NW = -0.0150 m
  NE: n=28  mean=+0.1071 m  Clearfell − NE = -0.0259 m
  SE: n=27  mean=+0.0800 m  Clearfell − SE = +0.0011 m
  SW: n= 4  mean=+0.0477 m  Clearfell − SW = +0.0335 m

========================================================================
Outputs:
  /home/john/projects/NRG/outputs/10_clearfell_baci/10b_spatial_scrape_raw.png
  /home/john/projects/NRG/outputs/10_clearfell_baci/10b_spatial_fell_raw.png
  /home/john/projects/NRG/outputs/10_clearfell_baci/10b_spatial_scrape_corrected.png
  /home/john/projects/NRG/outputs/10_clearfell_baci/10b_spatial_fell_corrected.png
  /home/john/projects/NRG/outputs/10_clearfell_baci/10b_spatial_step_data.csv
========================================================================

════════════════════════════════════════════════════════════════════════
SCRIPT 10c — Forest Zone Analysis  [v1.2.0]
════════════════════════════════════════════════════════════════════════

============================================================
Script 10c — Forest Zone Spatial Analysis
============================================================

  Forest wells: 14 (C4 = 9, C5 = 5)
  Clearfell wells in dataset: 1
  C3 boundary wells: 7
  [saved] 10c_forest_zone_correlations.csv
  [saved] 10c_forest_zone_cluster_summary.csv
  ✓ Saved: 10c_01_b1_b2_scatter.png  (236 dpi)
  [saved] 10c_01_b1_b2_scatter.png
  ✓ Saved: 10c_02_b2_elevation_regression.png  (270 dpi)
  [saved] 10c_02_b2_elevation_regression.png
  ✓ Saved: 10c_03_c4_c5_boundary_map.png  (236 dpi)
  [saved] 10c_03_c4_c5_boundary_map.png
  [saved] 10c_04_forest_zone_summary.txt
========================================================================
SCRIPT 10c — Forest Zone Spatial Analysis Summary
========================================================================

1. SPATIAL PREDICTORS
----------------------------------------
   β₂ vs elevation: r = 0.983, R² = 0.967
   Elevation is the dominant predictor of β₂ (96.7% of β₂ variance explained in sample;
   leave-one-out predicted R² = 0.955).
   Distance from ridge adds negligible information for β₂.
   β₃: elevation R² = 0.691, + dist_ridge R² = 0.788
   β₁: no strong spatial predictor (best: Easting r = 0.579)

2. CONTINUUM OR TWO GROUPS?
----------------------------------------
   C4 β₂ = 2.584 ± 0.540
   C5 β₂ = 1.134 ± 0.225
   t-test p = 0.0001 — two distinct groups.
   β₁ t-test p = 0.5393 — ranges overlap (not distinguishing).
   WMC3 (clearfell): β₁ = 2.440, β₂ = 1.747 — sits between C4 and C5.

3. OUTLIER ASSESSMENT
----------------------------------------
   NW10 (broadleaf): β₁ = 3.481 (C4 mean = 2.474), dist_ridge = 360 m
   Both position (closest to ridge) and canopy type may contribute.
   CEH14: β₂ = 3.828 at elev = 14.4 m — consistent with elevation trend,
   not a genuine outlier (upper end of tight linear relationship).

4. C4/C5 BOUNDARY
----------------------------------------
   C4 elevation: 8.6–14.4 m (n = 9)
   C5 elevation: 4.7–6.3 m (n = 5)
   Elevation gap: 2.3 m (zero overlap).
   C4 Northing: 363760–364488
   C5 Northing: 363533–363615
   Conclusion: boundary reflects a real topographic/substrate
   transition (dune ridge → coastal plain), not an arbitrary cut.
   Pearson affinity: 14/14 wells have best-match = assigned cluster.

  · Script 10c complete.

  ⚠ WARNING: Legibility: 10d_04_summer_minima_forest_ctrl.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×14.0 in).
  ⚠ WARNING: Legibility: 10d_05_summer_minima_climate_ctrl.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×14.0 in).
  ⚠ WARNING: Legibility: 10d_09_spring_means_forest_ctrl.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×14.0 in).
  ⚠ WARNING: Legibility: 10d_10_spring_means_climate_ctrl.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×14.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 10d — SEASONAL BACI ANALYSIS (DUAL CONTROL) — SUMMER MINIMA + SPRING MEANS  [v1.8.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────

  Network: 22 wells (6-tier design)
    Impact        : WMC3
    Edge          : CEH31, CEH20, CEH30, CEH16
    Forest Ctrl   : CEH32, CEH34, CEH33, NW10, CEH2
    Coastal Ctrl  : CEH19, CEH17
    Climate Ctrl  : CEH9, NW7, NW6, NW5, WMC2
    Far-field Ctrl: NW4B, WMC1, CEH5, L7, CEH6

────────────────────────────────────────────────────────────────────────
  · Metric: summer minima

──  Phase 2 · Computing annual summer minima ───────────────────────────

──  Phase 3 · Exporting per-well summer minima ─────────────────────────
  ✓ Saved: 10d_01_summer_minima.csv (317 rows)

──  Phase 4 · Computing pre/post shifts ────────────────────────────────
  ✓ Saved: 10d_02_summer_minima_shifts.csv (44 rows)

   Tier-mean shifts (mm):

   Forest control:
     Impact          mean =     -7 mm  (0/1 significant)
     Edge            mean =    -43 mm  (0/4 significant)
     Forest Ctrl     mean =     -1 mm  (0/5 significant)
     Climate Ctrl    mean =    -26 mm  (0/5 significant)

   Climate control:
     Impact          mean =    -19 mm  (0/1 significant)
     Edge            mean =     +7 mm  (0/4 significant)
     Forest Ctrl     mean =    +21 mm  (0/5 significant)
     Climate Ctrl    mean =    +20 mm  (0/5 significant)

──  Phase 5 · Running mixed-effects models ─────────────────────────────
  ✓ Saved: 10d_03_mixed_model_results.csv (12 rows)

   Mixed-effects results:
     Forest     Impact          clearfell =     -1 mm  p = 0.9905  (OLS (single well))
     Forest     Edge            clearfell =    -64 mm  p = 0.1229  (Mixed-effects (random intercept))
     Forest     Forest Ctrl     clearfell =     -8 mm  p = 0.6182  (Mixed-effects (random intercept))
     Forest     Coastal Ctrl    clearfell =   -176 mm  p = 0.0586  (Mixed-effects (random intercept))
     Forest     Climate Ctrl    clearfell =    -46 mm  p = 0.4251  (Mixed-effects (random intercept))
     Forest     Far-field Ctrl  clearfell =   -134 mm  p = 0.1009  (Mixed-effects (random intercept))
     Climate    Impact          clearfell =    -28 mm  p = 0.6410  (OLS (single well))
     Climate    Edge            clearfell =    +51 mm  p = 0.2501  (Mixed-effects (random intercept))
     Climate    Forest Ctrl     clearfell =    +56 mm  p = 0.3031  (Mixed-effects (random intercept))
     Climate    Coastal Ctrl    clearfell =    -39 mm  p = 0.3603  (Mixed-effects (random intercept))
     Climate    Climate Ctrl    clearfell =    +53 mm  p = 0.0233  (Mixed-effects (random intercept))
     Climate    Far-field Ctrl  clearfell =    -13 mm  p = 0.6865  (Mixed-effects (random intercept))

──  Phase 6 · Generating summer minima figures ─────────────────────────
  ✓ Saved: 10d_04_summer_minima_forest_ctrl.png  (158 dpi)
  ✓ Saved: 10d_04_summer_minima_forest_ctrl.png
  ✓ Saved: 10d_05_summer_minima_climate_ctrl.png  (158 dpi)
  ✓ Saved: 10d_05_summer_minima_climate_ctrl.png
  Clearfell comparator (WMC3 Gap_forest_m 2018-2025): slope +1.1 mm/yr, p=0.9604 — no-decay reference

========================================================================
SUMMER MINIMA SUMMARY
========================================================================

  Forest control:
  Tier            Mean shift (mm)    n sig
  ----------------------------------------
  Impact                       -7    0/1
  Edge                        -43    0/4
  Forest Ctrl                  -1    0/5
  Climate Ctrl                -26    0/5

  Climate control:
  Tier            Mean shift (mm)    n sig
  ----------------------------------------
  Impact                      -19    0/1
  Edge                         +7    0/4
  Forest Ctrl                 +21    0/5
  Climate Ctrl                +20    0/5
========================================================================
────────────────────────────────────────────────────────────────────────
  · Metric: spring means

──  Phase 2 · Computing annual spring means ────────────────────────────

──  Phase 3 · Exporting per-well spring means ──────────────────────────
  ✓ Saved: 10d_06_spring_means.csv (323 rows)

──  Phase 4 · Computing pre/post shifts ────────────────────────────────
  ✓ Saved: 10d_07_spring_means_shifts.csv (44 rows)

   Tier-mean shifts (mm):

   Forest control:
     Impact          mean =    -15 mm  (0/1 significant)
     Edge            mean =   -101 mm  (0/4 significant)
     Forest Ctrl     mean =     -9 mm  (0/5 significant)
     Climate Ctrl    mean =    -78 mm  (0/5 significant)

   Climate control:
     Impact          mean =    +19 mm  (0/1 significant)
     Edge            mean =    +14 mm  (0/4 significant)
     Forest Ctrl     mean =    +74 mm  (0/5 significant)
     Climate Ctrl    mean =     +9 mm  (0/5 significant)

──  Phase 5 · Running mixed-effects models ─────────────────────────────
  ✓ Saved: 10d_08_spring_mixed_model_results.csv (12 rows)

   Mixed-effects results:
     Forest     Impact          clearfell =    -17 mm  p = 0.8510  (OLS (single well))
     Forest     Edge            clearfell =   -146 mm  p = 0.0027  (Mixed-effects (random intercept))
     Forest     Forest Ctrl     clearfell =    -18 mm  p = 0.2171  (Mixed-effects (random intercept))
     Forest     Coastal Ctrl    clearfell =   -280 mm  p = 0.0110  (Mixed-effects (random intercept))
     Forest     Climate Ctrl    clearfell =   -119 mm  p = 0.0064  (Mixed-effects (random intercept))
     Forest     Far-field Ctrl  clearfell =   -168 mm  p = 0.0490  (Mixed-effects (random intercept))
     Climate    Impact          clearfell =    +14 mm  p = 0.6574  (OLS (single well))
     Climate    Edge            clearfell =    +29 mm  p = 0.3592  (Mixed-effects (random intercept))
     Climate    Forest Ctrl     clearfell =   +107 mm  p = 0.0139  (Mixed-effects (random intercept))
     Climate    Coastal Ctrl    clearfell =   -106 mm  p = 0.0652  (Mixed-effects (random intercept))
     Climate    Climate Ctrl    clearfell =    +17 mm  p = 0.2424  (Mixed-effects (random intercept))
     Climate    Far-field Ctrl  clearfell =    +17 mm  p = 0.7299  (Mixed-effects (random intercept))

──  Phase 6 · Generating spring means figures ──────────────────────────
  ✓ Saved: 10d_09_spring_means_forest_ctrl.png  (158 dpi)
  ✓ Saved: 10d_09_spring_means_forest_ctrl.png
  ✓ Saved: 10d_10_spring_means_climate_ctrl.png  (158 dpi)
  ✓ Saved: 10d_10_spring_means_climate_ctrl.png
  Clearfell comparator (WMC3 Gap_forest_m 2018-2025): slope -28.6 mm/yr, p=0.2222 — no-decay reference

========================================================================
SPRING MEANS SUMMARY
========================================================================

  Forest control:
  Tier            Mean shift (mm)    n sig
  ----------------------------------------
  Impact                      -15    0/1
  Edge                       -101    0/4
  Forest Ctrl                  -9    0/5
  Climate Ctrl                -78    0/5

  Climate control:
  Tier            Mean shift (mm)    n sig
  ----------------------------------------
  Impact                      +19    0/1
  Edge                        +14    0/4
  Forest Ctrl                 +74    0/5
  Climate Ctrl                 +9    0/5
========================================================================

──  Phase 7 · Exporting report numbers ─────────────────────────────────
  ✓ Saved: 10d_report_numbers.csv (130 rows)

Script 10d complete.


════════════════════════════════════════════════════════════════════════
SCRIPT 10e — SSM COEFFICIENT DECOMPOSITION  [v1.7.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────
   [hindcast] CEH34: substituted 51 hindcast value(s) prior to 2010-08-01 (from Script 10i, CEH9 donor)

  Network: 22 wells (6-tier design)
    Impact        : WMC3
    Edge          : CEH31, CEH20, CEH30, CEH16
    Forest Ctrl   : CEH32, CEH34, CEH33, NW10, CEH2
    Coastal Ctrl  : CEH19, CEH17
    Climate Ctrl  : CEH9, NW7, NW6, NW5, WMC2
    Far-field Ctrl: NW4B, WMC1, CEH5, L7, CEH6


──  Phase 2 · Fitting per-era SSM coefficients ─────────────────────────
   WMC3      Δβ₁=-0.096  Δβ₂=-0.306  Δβ₃=+0.000
   CEH31     Δβ₁=-0.581  Δβ₂=-0.256  Δβ₃=-0.017
   CEH20     Δβ₁=-0.055  Δβ₂=-0.183  Δβ₃=-0.000
   CEH30     Δβ₁=-0.262  Δβ₂=-0.012  Δβ₃=-0.014
   CEH16     Δβ₁=-0.179  Δβ₂=+0.052  Δβ₃=-0.008
   CEH32     Δβ₁=-0.149  Δβ₂=+0.129  Δβ₃=-0.012
   CEH34     Δβ₁=-0.256  Δβ₂=+0.266  Δβ₃=-0.015
   CEH33     Δβ₁=-0.245  Δβ₂=+0.062  Δβ₃=-0.014
   NW10      Δβ₁=+0.264  Δβ₂=-0.125  Δβ₃=+0.007
   CEH2      Δβ₁=+0.091  Δβ₂=+0.219  Δβ₃=-0.005
   CEH19     Δβ₁=-0.173  Δβ₂=-0.190  Δβ₃=-0.002
   CEH17     Δβ₁=-0.400  Δβ₂=-0.121  Δβ₃=-0.019
   CEH9      Δβ₁=-0.186  Δβ₂=+0.068  Δβ₃=-0.002
   NW7       Δβ₁=-0.302  Δβ₂=-0.079  Δβ₃=-0.011
   NW6       Δβ₁=-0.063  Δβ₂=-0.236  Δβ₃=+0.000
   NW5       Δβ₁=+0.014  Δβ₂=-0.120  Δβ₃=-0.001
   WMC2      Δβ₁=-0.082  Δβ₂=-0.357  Δβ₃=+0.001
   NW4B      Δβ₁=-0.010  Δβ₂=-0.273  Δβ₃=+0.002
   WMC1      Δβ₁=+0.141  Δβ₂=-0.223  Δβ₃=+0.005
   CEH5      Δβ₁=+0.940  Δβ₂=-0.371  Δβ₃=+0.023
   L7        Δβ₁=-0.090  Δβ₂=+0.039  Δβ₃=-0.012
   CEH6      Δβ₁=+1.267  Δβ₂=-0.955  Δβ₃=+0.041

 -> Saved: 10e_01_coefficient_shifts.csv (22 rows)
  Pipeline params updated: β₂ multipliers from Script 10e (clearfell=1.0189, thinning=1.0094)

──  Phase 3 · Generating coefficient shift figure ──────────────────────
  ✓ Saved: 10e_03_coefficient_shifts.png  (201 dpi)
  ✓ Saved: 10e_03_coefficient_shifts.png

──  Phase 4 · Exporting report numbers ─────────────────────────────────
  ✓ Saved: 10e_report_numbers.csv (210 rows)

========================================================================
COEFFICIENT SHIFT SUMMARY (mechanistic direction diagnostic)
========================================================================

  Tier                Δβ₁      Δβ₂      Δβ₃
  ----------------------------------------
  Impact           -0.096   -0.306   +0.000
  Edge             -0.269   -0.099   -0.010
  Forest Ctrl      -0.059   +0.111   -0.008
  Climate Ctrl     -0.124   -0.145   -0.003
========================================================================
Script 10e complete.


════════════════════════════════════════════════════════════════════════
SCRIPT 10f — ROBUSTNESS ANALYSES  [v1.3.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────

  Network: 22 wells (6-tier design)
    Impact        : WMC3
    Edge          : CEH31, CEH20, CEH30, CEH16
    Forest Ctrl   : CEH32, CEH34, CEH33, NW10, CEH2
    Coastal Ctrl  : CEH19, CEH17
    Climate Ctrl  : CEH9, NW7, NW6, NW5, WMC2
    Far-field Ctrl: NW4B, WMC1, CEH5, L7, CEH6


──  Phase 2 · SSM Residual Analysis — per-well forward prediction ──────
   (calibrate on pre-scraping, iterate forward, normalise by control mean)
   WMC3     [Impact        ] scrape=+0.127  fell=+0.183  step=+0.056  p=0.001 **
   CEH31    [Edge          ] scrape=+0.042  fell=+0.033  step=-0.009  p=0.526 ns
   CEH20    [Edge          ] scrape=+0.098  fell=+0.187  step=+0.089  p=<0.001 ***
   CEH30    [Edge          ] scrape=+0.083  fell=+0.118  step=+0.035  p=0.001 **
   CEH16    [Edge          ] scrape=+0.033  fell=-0.062  step=-0.096  p=<0.001 ***
   CEH32    [Forest Ctrl   ] scrape=+0.061  fell=+0.127  step=+0.066  p=0.004 **
   CEH34    [Forest Ctrl   ] scrape=+0.069  fell=+0.181  step=+0.111  p=<0.001 ***
   CEH33    [Forest Ctrl   ] scrape=+0.077  fell=+0.104  step=+0.027  p=0.052 ns
   NW10     [Forest Ctrl   ] scrape=-0.017  fell=+0.139  step=+0.156  p=<0.001 ***
   CEH2     [Forest Ctrl   ] scrape=-0.007  fell=+0.022  step=+0.029  p=0.025 *
   CEH19    [Coastal Ctrl  ] scrape=+0.042  fell=-0.069  step=-0.111  p=<0.001 ***
   CEH17    [Coastal Ctrl  ] scrape=+0.037  fell=-0.107  step=-0.144  p=<0.001 ***
   CEH9     [Climate Ctrl  ] scrape=-0.123  fell=-0.192  step=-0.070  p=<0.001 ***
   NW7      [Climate Ctrl  ] scrape=-0.071  fell=-0.146  step=-0.075  p=<0.001 ***
   NW6      [Climate Ctrl  ] scrape=-0.076  fell=-0.061  step=+0.015  p=0.567 ns
   NW5      [Climate Ctrl  ] scrape=-0.044  fell=-0.064  step=-0.020  p=0.074 ns
   WMC2     [Climate Ctrl  ] scrape=+0.052  fell=+0.066  step=+0.015  p=0.328 ns
   NW4B     [Far-field Ctrl] scrape=-0.093  fell=+0.009  step=+0.101  p=0.020 *
   WMC1     [Far-field Ctrl] scrape=-0.069  fell=-0.009  step=+0.061  p=0.033 *
   CEH5     [Far-field Ctrl] scrape=-0.048  fell=+0.005  step=+0.053  p=0.308 ns
   L7       [Far-field Ctrl] scrape=+0.030  fell=+0.101  step=+0.071  p=0.038 *
   CEH6     [Far-field Ctrl] scrape=-0.009  fell=-0.004  step=+0.005  p=0.913 ns

   MEAN     [Impact        ] step=+0.056 m  (n=1)
   MEAN     [Edge          ] step=+0.005 m  (n=4)
   MEAN     [Forest Ctrl   ] step=+0.078 m  (n=5)
   MEAN     [Coastal Ctrl  ] step=-0.128 m  (n=2)
   MEAN     [Climate Ctrl  ] step=-0.027 m  (n=5)

   -> Saved: 10f_01_ssm_residual_results.csv

──  Phase 3 · Synthetic Control Analysis — zone-level ──────────────────
   Donor pool: CEH1, CEH5, CEH6, CEH10, CEH11, CEH24 (n=6)
   Impact: scrape gap=-0.061  fell gap=+0.038  step=+0.099  p=0.001 **
   Edge: scrape gap=-0.083  fell gap=-0.042  step=+0.040  p=0.233 ns

   -> Saved: 10f_02_synthetic_control_results.csv

========================================================================
SCRIPT 10f COMPLETE
========================================================================
  SSM Residual:     10f_01_ssm_residual_results.csv (22 wells)
  Synthetic Control: 10f_02_synthetic_control_results.csv (2 zones)
  Report numbers:   10f_report_numbers.csv (7 entries)
========================================================================
  ⚠ WARNING: Legibility: 10g_02_clearfell_transect.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×10.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 10g — DIAGNOSTICS  [v1.2.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────

  Network: 22 wells (6-tier design)
    Impact        : WMC3
    Edge          : CEH31, CEH20, CEH30, CEH16
    Forest Ctrl   : CEH32, CEH34, CEH33, NW10, CEH2
    Coastal Ctrl  : CEH19, CEH17
    Climate Ctrl  : CEH9, NW7, NW6, NW5, WMC2
    Far-field Ctrl: NW4B, WMC1, CEH5, L7, CEH6


──  Phase 2 · NW10 Broadleaf Trend Analysis ────────────────────────────
   Pine composite: CEH2, CEH32, CEH33, CEH34
   Mean NW10 anomaly vs pine (2010–2021): +0.288 m
   OLS trend 2019–2025: -46.1 mm/yr (p=0.024, n=7)
  ✓ Saved: 10g_01_nw10_broadleaf_trend.csv

──  Phase 3 · Clearfell Transect Figure ────────────────────────────────
   Using 7 wells: WMC3, CEH31, CEH30, CEH16, CEH20, CEH34, CEH2
  ✓ Saved: 10g_02_clearfell_transect.png  (135 dpi)
  ✓ Saved: 10g_02_clearfell_transect.png
  ✓ Saved: 10g_03_clearfell_transect_steps.csv

──  Phase 4 · Rolling SSM Coefficient Analysis (cluster transition) ────
   Impact β₁ pre-felling:  2.474
   Impact β₁ post-felling: 2.561  (shift: +0.087)
   C3 β₁ post-felling:     3.479
   C4 β₁ post-felling:     2.335
   β₁ direction: toward C3
   Impact β₃ pre:  0.0359  post: 0.0360
   C3 β₃ post:     0.0540
  ✓ Saved: 10g_04_rolling_coefficients.csv

========================================================================
SCRIPT 10g COMPLETE
========================================================================
  NW10 trend:          10g_01_nw10_broadleaf_trend.csv
  Transect figure:     10g_02_clearfell_transect.png
  Transect data:       10g_03_clearfell_transect_steps.csv
  Rolling coefficients: 10g_04_rolling_coefficients.csv
  Report numbers:      10g_report_numbers.csv (7 entries)
========================================================================
  ⚠ WARNING: Legibility: 10h_05_donor_regression_validation.png smallest label ~3.9 pt as authored when placed at 160 mm (figsize 16.0×8.0 in).
  ⚠ WARNING: Legibility: 10h_06_baci_timeseries_varA.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×12.0 in).
  ⚠ WARNING: Legibility: 10h_07_baci_timeseries_varB.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×12.0 in).
  ⚠ WARNING: Legibility: 10h_08_baci_timeseries_varC.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×12.0 in).
  ⚠ WARNING: Legibility: 10h_09_cusum_varB.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×8.0 in).
  ⚠ WARNING: Legibility: 10h_10_climate_sensitivity_varB.png smallest label ~3.9 pt as authored when placed at 160 mm (figsize 16.0×5.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 10h — SYNTHETIC-EXTENSION BACI (FE WELLS)  [v1.5.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────
   [hindcast] CEH34: substituted 51 hindcast value(s) prior to 2010-08-01 (from Script 10i, CEH9 donor)

  Network: 22 wells (6-tier design)
    Impact        : WMC3
    Edge          : CEH31, CEH20, CEH30, CEH16
    Forest Ctrl   : CEH32, CEH34, CEH33, NW10, CEH2
    Coastal Ctrl  : CEH19, CEH17
    Climate Ctrl  : CEH9, NW7, NW6, NW5, WMC2
    Far-field Ctrl: NW4B, WMC1, CEH5, L7, CEH6


──  Phase 2 · Building synthetic FE well extensions ────────────────────

  FE1:
    Donors: CEH34, CEH2, CEH33
    Calibration: 2015-07 to 2017-11 (n=29)
    R² = 0.9978, RMSE = 18.2 mm
    Hindcast: 2010-07 to 2015-06 (48 months)
    Pre-scraping months gained: 45
    Post-clearfell divergence: +9.3 mm (p=0.1450, n=98)
    Synthetic record: 2010-07 to 2026-02 (175 months)

  FE2:
    Donors: CEH34, CEH2, CEH33
    Calibration: 2015-07 to 2017-11 (n=29)
    R² = 0.9944, RMSE = 24.6 mm
    Hindcast: 2010-07 to 2015-06 (48 months)
    Pre-scraping months gained: 45
    Post-clearfell divergence: +28.3 mm (p=0.0008, n=98)
    Synthetic record: 2010-07 to 2026-02 (175 months)

 -> Saved: 10h_01_synthetic_calibration.csv

──  Phase 3 · Building impact centroid variants ────────────────────────
  A (WMC3+FE1+FE2): 3 wells, earliest=2009-06
  B (WMC3+FE2): 2 wells, earliest=2009-06
  C (WMC3 only): 1 wells, earliest=2009-06

──  Phase 4 · Running ANCOVA for all variants × controls ───────────────
   Forest     × A (WMC3+FE1+FE2): step = +80 mm  CI = [+34, +127]  p = <0.001  R² = 0.286  n = 163
   Climate    × A (WMC3+FE1+FE2): step = -58 mm  CI = [-119, +2]  p = 0.0605  R² = 0.115  n = 147
   Combined   × A (WMC3+FE1+FE2): step = +31 mm  CI = [+6, +56]  p = 0.0175  R² = 0.204  n = 145
   Forest     × B (WMC3+FE2): step = +97 mm  CI = [+38, +157]  p = 0.0016  R² = 0.311  n = 163
   Climate    × B (WMC3+FE2): step = -37 mm  CI = [-90, +17]  p = 0.1837  R² = 0.197  n = 147
   Combined   × B (WMC3+FE2): step = +49 mm  CI = [+21, +77]  p = <0.001  R² = 0.349  n = 145
   Forest     × C (WMC3 only): step = +113 mm  CI = [+42, +184]  p = 0.0021  R² = 0.241  n = 163
   Climate    × C (WMC3 only): step = -15 mm  CI = [-63, +34]  p = 0.5551  R² = 0.206  n = 147
   Combined   × C (WMC3 only): step = +70 mm  CI = [+34, +105]  p = <0.001  R² = 0.256  n = 145

──  Phase 5 · Saving CSV outputs ───────────────────────────────────────
  ✓ Saved: 10h_02_ancova_comparison_table.csv (9 rows)
  ✓ Saved: 10h_03_ancova_full_coefficients.csv (54 rows)
  ✓ Saved: 10h_04_baci_timeseries.csv (1365 rows)

──  Phase 6 · Generating donor regression validation figure ────────────
  ✓ Saved: 10h_05_donor_regression_validation.png  (118 dpi)
  ✓ Saved: 10h_05_donor_regression_validation.png

──  Phase 7 · Generating BACI time-series figures ──────────────────────
  ✓ Saved: 10h_06_baci_timeseries_varA.png  (135 dpi)
  ✓ Saved: 10h_06_baci_timeseries_varA.png
  ✓ Saved: 10h_07_baci_timeseries_varB.png  (135 dpi)
  ✓ Saved: 10h_07_baci_timeseries_varB.png
  ✓ Saved: 10h_08_baci_timeseries_varC.png  (135 dpi)
  ✓ Saved: 10h_08_baci_timeseries_varC.png

──  Phase 8 · Generating CUSUM figure (Variant B, Forest control) ──────
  ✓ Saved: 10h_09_cusum_varB.png  (135 dpi)
  ✓ Saved: 10h_09_cusum_varB.png

──  Phase 9 · Generating climate sensitivity scatter (Forest control) ──
  ✓ Saved: 10h_10_climate_sensitivity_varB.png  (118 dpi)
  ✓ Saved: 10h_10_climate_sensitivity_varB.png

──  Phase 10 · Exporting report numbers ────────────────────────────────
  ✓ Saved: 10h_report_numbers.csv

──  Phase 11 · Generating robustness forest plot ───────────────────────
  ✓ Saved: 10h_11_robustness_forest.png  (249 dpi)
  ✓ Saved: 10h_11_robustness_forest.png

========================================================================
SYNTHETIC-EXTENSION BACI SUMMARY
========================================================================

  Donor wells: CEH34, CEH2, CEH33 (Forest Control)
  FE1: R²=0.9978, RMSE=18 mm, hindcast=48 months, divergence=+9 mm (p=0.1450)
  FE2: R²=0.9944, RMSE=25 mm, hindcast=48 months, divergence=+28 mm (p=0.0008)

  Variant                   Control     Step (mm)                   CI          p     R²   Net (mm)
  -----------------------------------------------------------------------------------------------
  A (WMC3+FE1+FE2)          Forest            +80          [+34, +127]     <0.001  0.286       +139
  A (WMC3+FE1+FE2)          Climate           -58           [-119, +2]     0.0605  0.115         +0
  A (WMC3+FE1+FE2)          Combined          +31            [+6, +56]     0.0175  0.204        +89
  B (WMC3+FE2)              Forest            +97          [+38, +157]     0.0016  0.311       +134
  B (WMC3+FE2)              Climate           -37           [-90, +17]     0.1837  0.197         +0
  B (WMC3+FE2)              Combined          +49           [+21, +77]     <0.001  0.349        +86
  C (WMC3 only)             Forest           +113          [+42, +184]     0.0021  0.241       +128
  C (WMC3 only)             Climate           -15           [-63, +34]     0.5551  0.206         +0
  C (WMC3 only)             Combined          +70          [+34, +105]     <0.001  0.256        +84

  Net clearfell = Forest (or Combined) step minus Climate background step

  Scraping decay λ = 300 m
========================================================================
Script 10h complete.


════════════════════════════════════════════════════════════════════════
SCRIPT 10j — Impact–Edge Direct Contrast  [v1.4.0]
════════════════════════════════════════════════════════════════════════
========================================================================
Script 10j — Direct Impact-vs-Edge contrasts
========================================================================

  Loading data ...

  Network: 5 wells (2-tier design)
    Impact        : WMC3
    Edge          : CEH31, CEH20, CEH30, CEH16

  PRE_FELL_START:   2011-01-01
  SCRAPING_DATE:    2015-04-01
  INTERVENTION:     2017-12-01

  1. Building monthly panel ...
     n_rows = 891, n_wells = 5
  2. Fitting monthly contrast ...
     Differential felling step (Impact − Edge):   +65.3 mm  95% CI [  +30.1,  +100.6]  p=0.0003
     Differential scraping step (Impact − Edge):   -25.9 mm  p=0.1010
     N = 891, R² = 0.818

  3. Loading summer minima from 10d ...
     summer panel years (WMC3 gatekeeper): [2011, 2013, 2014, 2015, 2016, 2017, 2018, 2020, 2021, 2022, 2023, 2024, 2025]
  4. Fitting summer-minima contrast ...
     Differential summer-minimum step (Impact − Edge):   +21.3 mm  95% CI [  -18.5,   +61.1]  p=0.2947
     N = 64 (13 Impact-years, 51 Edge-years), R² = 0.731

  5. Writing outputs ...
  ✓ Saved: 10j_01_monthly_contrast_results.csv
  ✓ Saved: 10j_02_summer_contrast_results.csv
  ✓ Saved: 10j_report_numbers.csv
  6. Building figures ...
  ✓ Saved: 10j_03_contrast_timeseries.jpg  (172 dpi)
  ✓ Saved: 10j_03_contrast_timeseries.jpg
  ✓ Saved: 10j_04_summer_minima_contrast.jpg  (189 dpi)
  ✓ Saved: 10j_04_summer_minima_contrast.jpg
  7. Updating site-observations registry ...
  ✓ Saved: 4 entries updated in pipeline_site_observations.csv

Script 10j complete.
  ⚠ WARNING: Legibility: 10k_04_zone_centroids.jpg smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×5.5 in).
  ⚠ WARNING: Legibility: 10k_05_contrast_forest.jpg smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×5.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 10k — Four-Zone Pooled-Panel BACI  [v1.4.0]
════════════════════════════════════════════════════════════════════════
========================================================================
Script 10k — Four-zone pooled-panel clearfell BACI
========================================================================

  Loading data ...
  Zones (reference = Forest control):
    Forest     : CEH32, CEH34, CEH33, NW10, CEH2 [reference]
    C3/Warren  : CEH1, NW1, NW2, NW11
    Edge       : CEH31, CEH20, CEH30, CEH16
    Impact     : WMC3
  PRE_FELL_START_FOURZONE:  2011-01-01
  SCRAPING_DATE:   2015-04-01
  INTERVENTION:    2017-12-01

  1. Building four-zone monthly panel ...
     n_rows = 2489, n_wells = 14, n_months = 181
     wells per zone: Forest 5, C3/Warren 4, Edge 4, Impact 1

  2. Fitting four-zone joint model (with easting × time) ...
     C3/Warren   vs Forest:     +8.5 mm  95% CI [  -15.4,   +32.5]  p=0.4854
     Edge        vs Forest:    -38.5 mm  95% CI [  -79.2,    +2.2]  p=0.0638
     Impact      vs Forest:    +24.1 mm  95% CI [   +0.8,   +47.4]  p=0.0427
     N = 2489 well-months, R² = 0.848

     [reminder] C3/Warren is a SECOND CONTROL zone — phi_C3Warren ~ 0 is the
                expected result; a clearly non-zero step is a flag, not a finding.

  3. Computing pairwise contrasts (shared covariance) ...
     [primary = direct coefficient; derived = linear combination, SE/p not comparable]
     C3/Warren - Forest                     +8.5 mm  p=0.4854  [primary]
     Edge - Forest                         -38.5 mm  p=0.0638  [primary]
     Impact - Forest                       +24.1 mm  p=0.0427  [primary]
     Impact - Edge                         +62.6 mm  (derived — p not comparable)
     Impact - C3/Warren                    +15.6 mm  (derived — p not comparable)
     Edge - C3/Warren                      -47.0 mm  (derived — p not comparable)
     (Impact-Forest) - (Edge-Forest)       +62.6 mm   [equals Impact - Edge row above (shared covariance)]

  4. Cross-check against Script 10j ...
  ↳ Impact - Edge differential felling step:
      10k four-zone contrast :    +62.6 mm
      10j two-zone estimator :    +65.3 mm
      delta (10k - 10j)      :     -2.7 mm  (advisory tol = 5.0 mm)
  · within advisory tolerance.

  5. Easting sensitivity (re-fit with easting × time dropped) ...
     C3/Warren   with easting     +8.5 mm  |  without     +8.4 mm
     Edge        with easting    -38.5 mm  |  without    -39.9 mm
     Impact      with easting    +24.1 mm  |  without    +25.5 mm
     [note] robustness diagnostic only — the with/without difference is NOT
            the coastal effect (see Script 25 for coastal retreat).

  6. Writing outputs ...
  ✓ Saved: 10k_01_four_zone_results.csv
  ✓ Saved: 10k_02_pairwise_contrasts.csv
  ✓ Saved: 10k_03_easting_sensitivity.csv
  ✓ Saved: 10k_report_numbers.csv
  7. Building figures ...
  ✓ Saved: 10k_04_zone_centroids.jpg  (158 dpi)
  ✓ Saved: 10k_04_zone_centroids.jpg
  ✓ Saved: 10k_05_contrast_forest.jpg  (158 dpi)
  ✓ Saved: 10k_05_contrast_forest.jpg
  ✓ Saved: 10k_06_forest_plot.jpg  (199 dpi)
  ✓ Saved: 10k_06_forest_plot.jpg
  8. Updating site-observations registry ...
  ✓ Saved: 3 entries updated in pipeline_site_observations.csv

Script 10k complete.

════════════════════════════════════════════════════════════════════════
SCRIPT 10l — Four-Zone Seasonal BACI — Summer Minima + Spring Means  [v1.3.0]
════════════════════════════════════════════════════════════════════════
========================================================================
Script 10l — Four-zone seasonal clearfell BACI (summer minima + spring means)
========================================================================

  Loading data ...
  Zones (reference = Forest control):
    Forest     : CEH32, CEH34, CEH33, NW10, CEH2 [reference]
    C3/Warren  : CEH1, NW1, NW2, NW11
    Edge       : CEH31, CEH20, CEH30, CEH16
    Impact     : WMC3
  Annual frame: 2011+ (matches Script 10d cutoff)
  Post-felling seasons: 2018+

────────────────────────────────────────────────────────────────────────
  Metric: summer minima  (value column Summer_min_m)
  1. Building four-zone summer minima panel ...
     Forest/Edge/Impact zones ← 10d_01_summer_minima.csv
     C3/Warren zone           ← computed here (10d does not cover it)
     n_rows = 181 well-years, n_wells = 14, panel years = 13 (2011–2025)
       Forest     : 5 wells, 65 well-years (30 pre, 35 post)
       C3/Warren  : 4 wells, 52 well-years (24 pre, 28 post)
       Edge       : 4 wells, 51 well-years (24 pre, 27 post)
       Impact     : 1 wells, 13 well-years (6 pre, 7 post)

  2. Fitting four-zone summer minima model ...
     Summer_min_m ~ const + Post + zone:Post + well-FE  (no scraping, no CWB)
     C3/Warren   vs Forest:    +12.0 mm  95% CI [   -8.8,   +32.8]  p=0.2572
     Edge        vs Forest:    -28.6 mm  95% CI [  -68.7,   +11.5]  p=0.1622
     Impact      vs Forest:     -7.3 mm  95% CI [  -22.8,    +8.2]  p=0.3576
     N = 181 well-years, R² = 0.724

     [reminder] C3/Warren is a SECOND CONTROL zone — phi_C3Warren ~ 0 is the
                expected result; a clearly non-zero step is a flag, not a finding.

  3. Computing pairwise contrasts (shared covariance) ...
     [primary = direct coefficient; derived = linear combination, SE/p not comparable]
     C3/Warren - Forest                    +12.0 mm  p=0.2572  [primary]
     Edge - Forest                         -28.6 mm  p=0.1622  [primary]
     Impact - Forest                        -7.3 mm  p=0.3576  [primary]
     Impact - Edge                         +21.3 mm  (derived — p not comparable)
     Impact - C3/Warren                    -19.3 mm  (derived — p not comparable)
     Edge - C3/Warren                      -40.6 mm  (derived — p not comparable)
     (Impact-Forest) - (Edge-Forest)       +21.3 mm   [equals Impact - Edge row above (shared covariance)]

  4. Cross-check against Script 10j summer contrast ...
  ↳ Impact - Edge differential summer-minimum step:
      10l four-zone contrast :    +21.3 mm
      10j two-zone estimator :    +21.3 mm
      delta (10l - 10j)      :     +0.0 mm  (advisory tol = 20.0 mm)
  · within advisory tolerance.

  5. Writing outputs ...
  ✓ Saved: 10l_01_four_zone_summer_results.csv
  ✓ Saved: 10l_02_summer_pairwise_contrasts.csv
     → 10l_03_c3warren_summer_minima.csv (60 rows, canonical C3/Warren summer minima)
  6. Building figures ...
  ✓ Saved: 10l_04_zone_summer_trajectories.jpg  (172 dpi)
  ✓ Saved: 10l_04_zone_summer_trajectories.jpg
  ✓ Saved: 10l_05_summer_forest_plot.jpg  (199 dpi)
  ✓ Saved: 10l_05_summer_forest_plot.jpg
  7. Updating site-observations registry ...
  ✓ Saved: 3 entries updated in pipeline_site_observations.csv

────────────────────────────────────────────────────────────────────────
  Metric: spring means  (value column Spring_mean_m)
  1. Building four-zone spring means panel ...
     Forest/Edge/Impact zones ← 10d_06_spring_means.csv
     C3/Warren zone           ← computed here (10d does not cover it)
     n_rows = 196 well-years, n_wells = 14, panel years = 14 (2011–2025)
       Forest     : 5 wells, 70 well-years (30 pre, 40 post)
       C3/Warren  : 4 wells, 56 well-years (24 pre, 32 post)
       Edge       : 4 wells, 56 well-years (24 pre, 32 post)
       Impact     : 1 wells, 14 well-years (6 pre, 8 post)

  2. Fitting four-zone spring means model ...
     Spring_mean_m ~ const + Post + zone:Post + well-FE  (no scraping, no CWB)
     C3/Warren   vs Forest:     -9.7 mm  95% CI [  -32.7,   +13.3]  p=0.4069
     Edge        vs Forest:    -46.4 mm  95% CI [  -82.1,   -10.6]  p=0.0110
     Impact      vs Forest:    -14.7 mm  95% CI [  -37.0,    +7.6]  p=0.1964
     N = 196 well-years, R² = 0.572

     [reminder] C3/Warren is a SECOND CONTROL zone — phi_C3Warren ~ 0 is the
                expected result; a clearly non-zero step is a flag, not a finding.

  3. Computing pairwise contrasts (shared covariance) ...
     [primary = direct coefficient; derived = linear combination, SE/p not comparable]
     C3/Warren - Forest                     -9.7 mm  p=0.4069  [primary]
     Edge - Forest                         -46.4 mm  p=0.0110  [primary]
     Impact - Forest                       -14.7 mm  p=0.1964  [primary]
     Impact - Edge                         +31.7 mm  (derived — p not comparable)
     Impact - C3/Warren                     -5.0 mm  (derived — p not comparable)
     Edge - C3/Warren                      -36.7 mm  (derived — p not comparable)
     (Impact-Forest) - (Edge-Forest)       +31.7 mm   [equals Impact - Edge row above (shared covariance)]

  4. No 10j cross-check for spring (there is no 10j spring estimator).

  5. Writing outputs ...
  ✓ Saved: 10l_06_four_zone_spring_results.csv
  ✓ Saved: 10l_07_spring_pairwise_contrasts.csv
     → 10l_08_c3warren_spring_means.csv (60 rows, canonical C3/Warren spring means)
  6. Building figures ...
  ✓ Saved: 10l_09_zone_spring_trajectories.jpg  (172 dpi)
  ✓ Saved: 10l_09_zone_spring_trajectories.jpg
  ✓ Saved: 10l_10_spring_forest_plot.jpg  (199 dpi)
  ✓ Saved: 10l_10_spring_forest_plot.jpg
  7. Updating site-observations registry ...
  ✓ Saved: 3 entries updated in pipeline_site_observations.csv

  ✓ Saved: 10l_report_numbers.csv

Script 10l complete.

════════════════════════════════════════════════════════════════════════
SCRIPT 10 — Clearfell Pipeline Orchestrator  [v1.0.0]
════════════════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════════════════
  SCRIPT 10 — CLEARFELL BACI ANALYSIS SUITE
════════════════════════════════════════════════════════════════════════

  Running 14 sub-script(s):
    10i  CEH34 donor-regression hindcast (CEH9 donor) — prerequisite  [ready]
    10a  Three-counterfactual ANCOVA-BACI (primary)  [ready]
    10b  Spatial step-change maps  [ready]
    10c  Forest zone spatial analysis (supplementary)  [ready]
    10d  Summer minima (dual control)  [ready]
    10e  SSM coefficient decomposition  [ready]
    10f  Robustness analyses  [ready]
    10g  Diagnostics  [ready]
    10h  Synthetic FE well extension BACI  [ready]
    10j  Direct Impact-vs-Edge contrast (monthly + summer)  [ready]
    10k  Four-zone pooled-panel BACI (primary §4.6 result)  [ready]
    10l  Four-zone summer-minima BACI (Phase 2)  [ready]
    10m  WMC3-vs-forest-control dual-panel intervention figure (display)  [ready]
    10n  Forest-normalised synthetic control (difference-in-differences)  [ready]

────────────────────────────────────────────────────────────────────────
  10i  CEH34 donor-regression hindcast (CEH9 donor) — prerequisite
  Script: 10i_ceh34_hindcast.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10a  Three-counterfactual ANCOVA-BACI (primary)
  Script: 10a_ancova_baci.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10b  Spatial step-change maps
  Script: 10b_spatial_step_maps.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10c  Forest zone spatial analysis (supplementary)
  Script: 10c_forest_zone_analysis.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10d  Summer minima (dual control)
  Script: 10d_summer_minima.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10e  SSM coefficient decomposition
  Script: 10e_coefficient_decomposition.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10f  Robustness analyses
  Script: 10f_robustness.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10g  Diagnostics
  Script: 10g_diagnostics.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10h  Synthetic FE well extension BACI
  Script: 10h_synthetic_impact_baci.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10j  Direct Impact-vs-Edge contrast (monthly + summer)
  Script: 10j_impact_edge_contrast.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10k  Four-zone pooled-panel BACI (primary §4.6 result)
  Script: 10k_four_zone_baci.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10l  Four-zone summer-minima BACI (Phase 2)
  Script: 10l_four_zone_summer_minima.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10m  WMC3-vs-forest-control dual-panel intervention figure (display)  ⚠ WARNING: Legibility: 10m_02_wmc3_baci_dual.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×9.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 10m — WMC3 vs forest-control dual-panel intervention figure  [v1.2.1]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load data ────────────────────────────────────────────────
  · Impact well: WMC3   Forest control: CEH32, CEH34, CEH33, NW10, CEH2
  · Record: Mar 2005 – Feb 2026  (192 paired months)

──  Phase 2 · Era means and difference-in-differences steps ────────────
  • Pre-2015 scrape (baseline): +165 mm  (n=65)
  • Post-2015 scrape / pre-fell: +110 mm  (n=32)
  • Post-clearfell / pre-2023: +150 mm  (n=66)
  • Post-2023 scrape: +97 mm  (n=29)
────────────────────────────────────────────────────────────────────────
  • 2015 scraping: -55 mm  (falls)
  • 2017 clearfell: +41 mm  (rises)
  • 2023 scraping: -54 mm  (falls)

──  Phase 3 · ANCOVA clearfell headline (live from 10a) ────────────────
  · ANCOVA clearfell step: +113 mm  [p=0.0021, CI=[0.0423,0.1839]]

──  Phase 4 · Build figure ─────────────────────────────────────────────
  ✓ Saved: 10m_02_wmc3_baci_dual.png  (135 dpi)
  ✓ Saved: 10m_02_wmc3_baci_dual.png

──  Phase 5 · Write outputs ────────────────────────────────────────────
  ✓ Saved: 10m_01_wmc3_baci_era_steps.csv
  ✓ Saved: 10m_report_numbers.csv  (4 rows)

────────────────────────────────────────────────────────────────────────
Done  (Script 10m)


════════════════════════════════════════════════════════════════════════
SCRIPT 10n — FOREST-NORMALISED SYNTHETIC CONTROL (DiD)  [v1.1.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading data ─────────────────────────────────────────────

  Network: 22 wells (6-tier design)
    Impact        : WMC3
    Edge          : CEH31, CEH20, CEH30, CEH16
    Forest Ctrl   : CEH32, CEH34, CEH33, NW10, CEH2
    Coastal Ctrl  : CEH19, CEH17
    Climate Ctrl  : CEH9, NW7, NW6, NW5, WMC2
    Far-field Ctrl: NW4B, WMC1, CEH5, L7, CEH6


   Donor pool: CEH1, CEH5, CEH6, CEH10, CEH11, CEH24 (n=6)

──  Phase 2 · Zone synthetics from the shared donor pool ───────────────
   Impact           n=1 baseline R²=0.990 gross step=  +99.3 mm  p_HAC=0.011
   Edge             n=4 baseline R²=0.988 gross step=  +40.2 mm  p_HAC=0.383
   Forest Ctrl      n=5 baseline R²=0.990 gross step=  +50.0 mm  p_HAC=0.406
   Climate Ctrl     n=5 baseline R²=0.995 gross step=  +27.5 mm  p_HAC=0.251
   Coastal Ctrl     n=2 baseline R²=0.990 gross step=  +36.7 mm  p_HAC=0.462
   Far-field Ctrl   REFUSED — tier shares wells with the donor pool: ceh5, ceh6

   -> 10n_01_zone_gaps.csv

──  Phase 3 · Forest-normalised contrasts ──────────────────────────────
   Impact       − Forest Ctrl   step=  +47.3 mm  95% CI [-14.7, +109.2]  p_HAC=0.135 ns  (p_Welch=0.013)
                  (all pre-fell)  step=  +20.9 mm  p_HAC=0.294
   Edge         − Forest Ctrl   step=   -9.8 mm  95% CI [-48.3, +28.6]  p_HAC=0.617 ns  (p_Welch=0.422)
                  (all pre-fell)  step=  -49.3 mm  p_HAC=0.002

   -> 10n_02_did_contrasts.csv

──  Phase 4 · Parallel pre-trends, and the step net of any trend ───────
   Impact - Forest Ctrl       pre-trend (all pre-fell)         -13.2 mm/yr  p_HAC=0.007  -> PARALLEL TRENDS FAIL
   Impact - Forest Ctrl       pre-trend (post-scrape only)     -50.7 mm/yr  p_HAC=0.048  -> PARALLEL TRENDS FAIL
   Impact - Forest Ctrl       step net of trend   +39.4 mm  95% CI [-37.9, +116.6]  p_HAC=0.318 ns
   Edge - Forest Ctrl         pre-trend (all pre-fell)         -20.5 mm/yr  p_HAC=<0.001  -> PARALLEL TRENDS FAIL
   Edge - Forest Ctrl         pre-trend (post-scrape only)     -40.1 mm/yr  p_HAC=0.026  -> PARALLEL TRENDS FAIL
   Edge - Forest Ctrl         step net of trend    +6.4 mm  95% CI [-54.6, +67.4]  p_HAC=0.836 ns

   -> 10n_04_pretrend.csv

──  Phase 5 · Falsification ────────────────────────────────────────────
   in-space  Climate Ctrl   − Forest Ctrl  step=  -22.5 mm  p_HAC=0.710 ns
   in-space  Coastal Ctrl   − Forest Ctrl  step=  -13.4 mm  p_HAC=0.564 ns
   in-time   pseudo-fell 2014-04-01      step=  -33.9 mm  p_HAC=0.210 ns
   in-time   pseudo-fell 2015-09-01      step=  -34.7 mm  p_HAC=0.326 ns

   -> 10n_03_placebo.csv
   -> 10n_report_numbers.csv (8 keys)

  Script: 10m_wmc3_baci_dual.py
────────────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
  10n  Forest-normalised synthetic control (difference-in-differences)
  Script: 10n_synthetic_did.py
────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
  Consolidating report numbers...
────────────────────────────────────────────────────────────────────────
  + 10a_report_numbers.csv (175 rows)
  + 10d_report_numbers.csv (130 rows)
  + 10e_report_numbers.csv (210 rows)
  + 10f_report_numbers.csv (7 rows)
  + 10g_report_numbers.csv (7 rows)
  + 10h_report_numbers.csv (57 rows)
  + 10i_report_numbers.csv (8 rows)
  + 10k_report_numbers.csv (17 rows)
  + 10l_report_numbers.csv (34 rows)
  + 10m_report_numbers.csv (4 rows)
  + 10n_report_numbers.csv (8 rows)

  -> Consolidated: 10_consolidated_report_numbers.csv (657 rows)

════════════════════════════════════════════════════════════════════════
  SCRIPT 10 COMPLETE — all 14 sub-scripts succeeded
════════════════════════════════════════════════════════════════════════

  ✓ done  (75.2s)

  ▶ STEP 11/52  Forecasting and critical thresholds
      script: 11_forecasting_thresholds.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 11 — Forecasting Thresholds  [v1.3.3]
════════════════════════════════════════════════════════════════════════

Loading input data...
  [OK] 250 monthly rows loaded | Columns: C1, C2, C3, C4, C5, Lake_Edge, Eastern_Block, Western_Block, Forest, Coastal_Forest, P_mm, PET_mm

======================================================================
SECTION 1: MECHANISTIC STATE-SPACE EQUATIONS  (dh = b1*P - b2*PET - b3*h_prev)
======================================================================
  Cluster-centroid SSM coefficients from Script 03
  Source: 03_03_cluster_mechanistic_coefficients.csv

  C1 (Lake Edge):  dh = (0.004578*P) - (0.000923*PET) - (0.0886*h_prev)   |  R2 = 0.732   n = 237
        p-values:  P = 3.7274e-67   PET = 3.6435e-05   h_prev = 8.9962e-36
  C2 (Dune):  dh = (0.003972*P) - (0.001742*PET) - (0.0643*h_prev)   |  R2 = 0.747   n = 248
        p-values:  P = 2.5660e-69   PET = 1.5679e-16   h_prev = 5.4976e-26
  C3 (Western Residual):  dh = (0.003573*P) - (0.001807*PET) - (0.0569*h_prev)   |  R2 = 0.812   n = 249
        p-values:  P = 1.2566e-83   PET = 4.0461e-26   h_prev = 5.9176e-29
  C4 (Main Forest):  dh = (0.002477*P) - (0.002563*PET) - (0.0185*h_prev)   |  R2 = 0.722   n = 237
        p-values:  P = 2.0673e-51   PET = 9.1757e-36   h_prev = 1.6312e-03
  C5 (Coastal Forest):  dh = (0.002428*P) - (0.001274*PET) - (0.0449*h_prev)   |  R2 = 0.683   n = 239
        p-values:  P = 1.8852e-54   PET = 2.3503e-15   h_prev = 1.0909e-16

======================================================================
SECTION 2: PEAK FLOOD TRANSFER FUNCTIONS  (h_peak = a_P·P_winter + a_h·h_min + c)
======================================================================
  OLS with intercept | Hydrological year: Oct 1 - Sep 30
  Blocks (one per cluster, k=5 partition): Lake_Edge (C1), Eastern_Block (C2), Western_Block (C3), Forest (C4), Coastal_Forest (C5).

  Lake_Edge:
    h_peak = (0.00108·P_winter) + (-0.058·h_min) - 0.550
    R² = 0.481   |   n = 19 hydrological years
    p-values:  P_winter = 0.0019   h_min = 0.7801   intercept = 0.0540

  Eastern_Block:
    h_peak = (0.00171·P_winter) + (0.165·h_min) - 0.829
    R² = 0.553   |   n = 20 hydrological years
    p-values:  P_winter = 0.0023   h_min = 0.5751   intercept = 0.0932

  Western_Block:
    h_peak = (0.00124·P_winter) + (0.847·h_min) - 0.040
    R² = 0.670   |   n = 20 hydrological years
    p-values:  P_winter = 0.0520   h_min = 0.0079   intercept = 0.9445

  Forest:
    h_peak = (0.00005·P_winter) + (1.253·h_min) + 1.134
    R² = 0.885   |   n = 19 hydrological years
    p-values:  P_winter = 0.9236   h_min = 0.0000   intercept = 0.0301

  Coastal_Forest:
    h_peak = (0.00045·P_winter) + (1.609·h_min) + 1.293
    R² = 0.873   |   n = 19 hydrological years
    p-values:  P_winter = 0.3382   h_min = 0.0000   intercept = 0.0052


======================================================================
SECTION 4: SUMMER DROUGHT TRANSFER FUNCTIONS  (h_min = a_P·P_summer + a_h·h_max_winter + c)
======================================================================
  OLS with intercept | Hydrological year: Oct 1 - Sep 30
  Predicting summer minimum from antecedent winter peak and summer rain.

  Lake_Edge:
    h_min_summer = (0.00146·P_summer) + (0.459·h_max_winter) - 1.423
    R² = 0.437   |   n = 19 hydrological years
    p-values:  P_summer = 0.0037   h_max_winter = 0.0314   intercept = 0.0000

  Eastern_Block:
    h_min_summer = (0.00178·P_summer) + (0.526·h_max_winter) - 1.598
    R² = 0.642   |   n = 20 hydrological years
    p-values:  P_summer = 0.0003   h_max_winter = 0.0001   intercept = 0.0000

  Western_Block:
    h_min_summer = (0.00125·P_summer) + (0.563·h_max_winter) - 1.410
    R² = 0.733   |   n = 20 hydrological years
    p-values:  P_summer = 0.0070   h_max_winter = 0.0000   intercept = 0.0000

  Forest:
    h_min_summer = (0.00129·P_summer) + (0.758·h_max_winter) - 1.447
    R² = 0.935   |   n = 19 hydrological years
    p-values:  P_summer = 0.0030   h_max_winter = 0.0000   intercept = 0.0000

  Coastal_Forest:
    h_min_summer = (0.00069·P_summer) + (0.522·h_max_winter) - 1.288
    R² = 0.897   |   n = 19 hydrological years
    p-values:  P_summer = 0.0412   h_max_winter = 0.0000   intercept = 0.0000


======================================================================
SECTION 3: CRITICAL RAINFALL THRESHOLD EQUATIONS  (P_flood - iterated)
======================================================================
  Iterated closed form from cluster-level SSM coefficients.
  Monthly rainfall scales by λ; PET from RAF Valley climatology.

  C1 (Lake Edge)
    h_0 = -0.752 m  (long-term mean of month-of-minimum)
    horizon: [10, 11, 12, 1]  (n = 4 months, peak = month 1)
    α = 0.9114   αⁿ = 0.6899
    S_P =   346.8 mm    S_E =    94.6 mm
    climatological totals: P = 400 mm   PET = 113 mm
    λ = 1.104
    P_flood (iterated)    =   442 mm    [1.10x climatology]
    P_flood (old 1-step)  =   221 mm    [reference only]
    Collapsed form:  P_flood = 173.96 * d + 311.24   (d in m below ground)

  C2 (Dune)
    h_0 = -0.899 m  (long-term mean of month-of-minimum)
    horizon: [10, 11, 12, 1]  (n = 4 months, peak = month 1)
    α = 0.9357   αⁿ = 0.7665
    S_P =   360.8 mm    S_E =    99.3 mm
    climatological totals: P = 400 mm   PET = 113 mm
    λ = 1.204
    P_flood (iterated)    =   482 mm    [1.20x climatology]
    P_flood (old 1-step)  =   272 mm    [reference only]
    Collapsed form:  P_flood = 214.10 * d + 289.66   (d in m below ground)

  C3 (Western Residual)
    h_0 = -1.107 m  (long-term mean of month-of-minimum)
    horizon: [10, 11, 12, 1, 2]  (n = 5 months, peak = month 2)
    α = 0.9431   αⁿ = 0.7459
    S_P =   405.4 mm    S_E =   115.0 mm
    climatological totals: P = 461 mm   PET = 133 mm
    λ = 1.362
    P_flood (iterated)    =   629 mm    [1.36x climatology]
    P_flood (old 1-step)  =   351 mm    [reference only]
    Collapsed form:  P_flood = 237.59 * d + 365.60   (d in m below ground)

  C4 (Main Forest)
    h_0 = -1.639 m  (long-term mean of month-of-minimum)
    horizon: [10, 11, 12, 1, 2]  (n = 5 months, peak = month 2)
    α = 0.9815   αⁿ = 0.9111
    S_P =   442.5 mm    S_E =   126.7 mm
    climatological totals: P = 461 mm   PET = 133 mm
    λ = 1.959
    P_flood (iterated)    =   904 mm    [1.96x climatology]
    P_flood (old 1-step)  =   677 mm    [reference only]
    Collapsed form:  P_flood = 383.48 * d + 275.20   (d in m below ground)

  C5 (Coastal Forest)
    h_0 = -1.388 m  (long-term mean of month-of-minimum)
    horizon: [10, 11, 12, 1, 2]  (n = 5 months, peak = month 2)
    α = 0.9551   αⁿ = 0.7950
    S_P =   416.7 mm    S_E =   118.6 mm
    climatological totals: P = 461 mm   PET = 133 mm
    λ = 1.989
    P_flood (iterated)    =   918 mm    [1.99x climatology]
    P_flood (old 1-step)  =   614 mm    [reference only]
    Collapsed form:  P_flood = 362.49 * d + 414.78   (d in m below ground)

Note: P_flood_new supersedes the single-step formulation in prior drafts.
      See Section 3.6.3 of Hollingham (2026) for derivation.

  Reviewer summary → 11_forecast_pflood_summary.csv

======================================================================
SECTION 5: SPRING MSL TRANSFER FUNCTIONS  (MSL_y from winter peak and Oct-May forcing)
======================================================================
  OLS with intercept | Hydrology year: 1 Jun y-1 to 31 May y (van Willegen 2025 convention)
  Predicting next-year MSL from antecedent winter peak.

  Lake_Edge:
    MSL_y = (+0.142·h_max_winter) + (+0.00111·P_win_to_spr) + (-0.00179·PET_win_to_spr) + -0.513
    R² = 0.726   |   n = 19 hydro years
    p-values:  h_max_winter = 0.4546   P = 0.0008   PET = 0.1544   intercept = 0.1810

  Eastern_Block:  ⚠ WARNING: Legibility: 11_forecast_02_spring_calibration.png smallest label ~4.8 pt as authored when placed at 160 mm (figsize 13.0×8.0 in).

    MSL_y = (+0.387·h_max_winter) + (+0.00131·P_win_to_spr) + (-0.00214·PET_win_to_spr) + -0.554
    R² = 0.843   |   n = 20 hydro years
    p-values:  h_max_winter = 0.0089   P = 0.0006   PET = 0.1271   intercept = 0.2181

  Western_Block:
    MSL_y = (+0.641·h_max_winter) + (+0.00096·P_win_to_spr) + (-0.00138·PET_win_to_spr) + -0.585
    R² = 0.888   |   n = 20 hydro years
    p-values:  h_max_winter = 0.0000   P = 0.0078   PET = 0.3372   intercept = 0.2223

  Forest:
    MSL_y = (+0.839·h_max_winter) + (+0.00087·P_win_to_spr) + (+0.00001·PET_win_to_spr) + -0.833
    R² = 0.958   |   n = 19 hydro years
    p-values:  h_max_winter = 0.0000   P = 0.0084   PET = 0.9952   intercept = 0.0745

  Coastal_Forest:
    MSL_y = (+0.754·h_max_winter) + (+0.00039·P_win_to_spr) + (-0.00055·PET_win_to_spr) + -0.519
    R² = 0.960   |   n = 19 hydro years
    p-values:  h_max_winter = 0.0000   P = 0.0605   PET = 0.6114   intercept = 0.1431

  Spring transfer table → 11_forecast_spring_transfer_functions.csv
  ✓ Saved: 11_forecast_02_spring_calibration.png  (145 dpi)
  Calibration figure → 11_forecast_02_spring_calibration.png


======================================================================
  Analysis complete.
======================================================================


[OUTPUT] Results transcript saved → /home/john/projects/NRG/outputs/11_forecasting_thresholds/11_forecast_01_results.txt
  ✓ done  (3.4s)

  ▶ STEP 12/52  Spatial eco-hydrological threshold maps
      script: 11b_spatial_thresholds.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 11b_01_summer_minima_depth.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 12.0×10.0 in).
  ⚠ WARNING: Legibility: 11b_02_winter_maxima_depth.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 12.0×10.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 11b — Spatial Threshold Maps  [v1.7.1]
════════════════════════════════════════════════════════════════════════

=== 11b_spatial_thresholds.py ===
Loading well data...
  Wells loaded: 88 total  (Reference: 66, Extended: 22)
Generating summer minima depth map...
  ✓ Saved: 11b_01_summer_minima_depth.png  (158 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/11b_spatial_thresholds/11b_01_summer_minima_depth.png
Generating winter maxima depth map...
  ✓ Saved: 11b_02_winter_maxima_depth.png  (158 dpi)
  ✓ Saved: 11b_02_winter_maxima_depth.png
Generating P_flood map (iterated, Section 3.6.3)...
  [WARNING] ceh14: β₃ = -0.0207 is negative (expected positive under displacement formulation)
  P_flood computed for 88 wells (66 per-well, 22 cluster-level; 88 reachable, 0 unreachable; 0 skipped — no peak month; 0 skipped — invalid beta)
  ✓ Saved: 11b_03_pflood.png  (158 dpi)
  ✓ Saved: 11b_03_pflood.png
  ✓ Saved: 11b_03_pflood_per_well.csv
Generating flood frequency map...
  ✓ Saved: 11b_04_flood_frequency.png  (158 dpi)
  ✓ Saved: 11b_04_flood_frequency.png
Exporting Table 10 (spreadsheet-ready P_flood equations)...
  ✓ Saved: 11b_05_table10_pflood_spreadsheet.csv

  Table 10 contents (spreadsheet-ready, report paste-in):
    C1      Oct–Jan (4 mo)      P_flood = 173.96·d + 311.24             ΣP̄ᵢ = 400 mm
    C2      Oct–Jan (4 mo)      P_flood = 214.10·d + 289.66             ΣP̄ᵢ = 400 mm
    C3      Oct–Feb (5 mo)      P_flood = 237.59·d + 365.60             ΣP̄ᵢ = 461 mm
    C4      Oct–Feb (5 mo)      P_flood = 383.48·d + 275.20             ΣP̄ᵢ = 461 mm
    C5      Oct–Feb (5 mo)      P_flood = 362.49·d + 414.78             ΣP̄ᵢ = 461 mm
Building interactive forecaster HTML...
  Met Office RAF Valley Oct-Mar mean: 516 mm (n=20 complete winters, 2006-2025)
  Forecaster base layer: hillshade embedded OK
  Forecaster base layer: 26 KML polylines from 5 layers
[emit_forecaster_engine] engine constants unchanged since 2026-09-02T12:56:10Z (hash 9e68b9e5550b2051); no rewrite.
  ✓ Saved: forecaster.html
    wells: 88  clusters: 5  blocks: 5  template size: 73,528 chars → rendered size: 2,750,863 chars

────────────────────────────────────────────────────────────────────────
Done

  ✓ done  (34.6s)

  ▶ STEP 13/52  P_flood achievability categorical map (§5.9 / Conclusion 4)
      script: 11c_pflood_achievability.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 11c_pflood_achievability.png smallest label ~4.2 pt as authored when placed at 160 mm (figsize 12.0×10.0 in).
────────────────────────────────────────────────────────────────────────
11c — P_flood achievability map (gap C)
────────────────────────────────────────────────────────────────────────
Loaded 88 wells from outputs/11b_spatial_thresholds/11b_03_pflood_per_well.csv

─── Category counts by cluster ──────────────────────────────────
category  Achievable  Marginal  Unreachable
cluster                                    
1                  8         0            0
2                 28         4            0
3                 21         4            0
4                  1        10            2
5                  0         7            3

─── Totals ──────────────────────────────────────────────────────
category
Achievable     58
Marginal       25
Unreachable     5

Wrote outputs/11b_spatial_thresholds/11c_pflood_achievability_per_well.csv
  ✓ Saved: 11c_pflood_achievability.png  (158 dpi)
Wrote outputs/11b_spatial_thresholds/11c_pflood_achievability.png
Wrote outputs/11b_spatial_thresholds/11c_pflood_achievability_results.md

────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
Done

────────────────────────────────────────────────────────────────────────
  ✓ done  (6.1s)

  ✓ Phase 3 validation passed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 4  — Climate Projections and Figure Generation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 14/52  Climate summary outputs
      script: 00_climate_summary.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 00_01_climate_timeseries.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×12.0 in).
  ⚠ WARNING: Legibility: 00_02_well_network_summary.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×10.0 in).
  ⚠ WARNING: Legibility: 00_01_climate_timeseries_short.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×15.0 in).
  ⚠ WARNING: Legibility: 00_02_well_network_summary_short.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×10.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 00 — Climate Summary  [v1.4.1]
════════════════════════════════════════════════════════════════════════

--- Full-record outputs ---
  ✓ Saved: 00_01_climate_timeseries.png  (135 dpi)
  ✓ Saved: 00_02_well_network_summary.png  (135 dpi)
Generating Figure 3 — RAF Valley summer warming trend (95-year record)...
  ✓ Saved: 00_03_summer_warming_trend.png  (172 dpi)

--- Monitoring-period outputs ---
  ✓ Saved: 00_01_climate_timeseries_short.png  (135 dpi)
  ✓ Saved: 00_02_well_network_summary_short.png  (135 dpi)
  Saved climatology → 00_04_climatology.csv (20 complete years 2006-2025)
Computing PET response to warming (full record)...
  PET warming response: T 10.12 -> 10.85 degC (+7.2%), annual PET 630.8 -> 649.7 mm (+3.0%), elasticity 0.42
  Saved → 00_report_numbers.csv (59 report numbers)

Files created:
 - /home/john/projects/NRG/outputs/00_climate_summary/00_01_climate_timeseries.png
 - /home/john/projects/NRG/outputs/00_climate_summary/00_02_well_network_summary.png
 - /home/john/projects/NRG/outputs/00_climate_summary/00_03_summer_warming_trend.png
 - /home/john/projects/NRG/outputs/00_climate_summary/00_01_annual_climate_summary.csv
 - /home/john/projects/NRG/outputs/00_climate_summary/00_02_well_network_summary.csv
 - /home/john/projects/NRG/outputs/00_climate_summary/00_03_summer_warming_stats.csv
 - /home/john/projects/NRG/outputs/00_climate_summary/00_01_climate_timeseries_short.png
 - /home/john/projects/NRG/outputs/00_climate_summary/00_02_well_network_summary_short.png
 - /home/john/projects/NRG/outputs/00_climate_summary/00_03_summer_warming_trend.png
 - /home/john/projects/NRG/outputs/00_climate_summary/00_01_annual_climate_summary_short.csv
 - /home/john/projects/NRG/outputs/00_climate_summary/00_02_well_network_summary_short.csv
 - /home/john/projects/NRG/outputs/00_climate_summary/00_03_summer_warming_stats.csv

Headline statistics:
 - Full climate record: 95.2 years (1143 months)
 - Analysis window: 2005-03-01 to 2026-02-01 (252 months)
 - Reference wells: 77

00 climate summary complete.
  ✓ done  (7.6s)

  ▶ STEP 15/52  Figure: Climate trajectory projections
      script: 14_climate_projections.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 14_climate_trajectory_summer.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×7.0 in).
  ⚠ WARNING: Legibility: 14_climate_trajectory_winter_flooding.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×7.0 in).
  ⚠ WARNING: Legibility: 14_climate_trajectory_stacked.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×11.0 in).
  ⚠ WARNING: Legibility: 14_climate_trajectory_spring.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×7.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 14 — Climate Projections  [v1.5.0]
════════════════════════════════════════════════════════════════════════

[14] Loading observed data and fitting summer trends per cluster...
  C1 winter exceedance: wet=17/20 (85%), dry=19/20
  C2 winter exceedance: wet=12/21 (57%), dry=17/21
  C3 winter exceedance: wet=4/21 (19%), dry=9/21
  C4 winter exceedance: wet=0/20 (0%), dry=0/20
  C5 winter exceedance: wet=1/20 (5%), dry=1/20
  C1 summer trend: -0.0109 m yr⁻¹  (R²=0.234, p=0.0307, n=20)
  C1 winter observed trend (descriptive only): +0.0075 m yr⁻¹  (R²=0.096, p=0.1844, n=20)
  C2 summer trend: -0.0112 m yr⁻¹  (R²=0.162, p=0.0706, n=21)
  C2 winter observed trend (descriptive only): +0.0069 m yr⁻¹  (R²=0.034, p=0.4230, n=21)
  C3 summer trend: -0.0094 m yr⁻¹  (R²=0.089, p=0.1882, n=21)
  C3 winter observed trend (descriptive only): +0.0005 m yr⁻¹  (R²=0.000, p=0.9678, n=21)
  C4 summer trend: -0.0178 m yr⁻¹  (R²=0.078, p=0.2320, n=20)
  C4 winter observed trend (descriptive only): -0.0073 m yr⁻¹  (R²=0.008, p=0.7004, n=20)
  C5 summer trend: -0.0359 m yr⁻¹  (R²=0.394, p=0.0030, n=20)
  C5 winter observed trend (descriptive only): -0.0349 m yr⁻¹  (R²=0.215, p=0.0396, n=20)
  ✓ Saved: 14_climate_trajectory_summer.png  (158 dpi)
  [14] Saved: 14_climate_trajectory_summer.png
  ✓ Saved: 14_climate_trajectory_winter_flooding.png  (158 dpi)
  [14] Saved: 14_climate_trajectory_winter_flooding.png
  ✓ Saved: 14_climate_trajectory_stacked.png  (158 dpi)
  [14] Saved: 14_climate_trajectory_stacked.png
  ✓ Saved: 14_summer_trend_stats.csv
  ✓ Saved: 14_winter_trend_stats.csv

[14] Fitting spring-mean (MAM, calendar-year) trends per cluster...
  C1 spring trend: +0.0065 m yr⁻¹  (R²=0.050, p=0.3561, n=19)
  C2 spring trend: +0.0003 m yr⁻¹  (R²=0.000, p=0.9734, n=21)
  C3 spring trend: -0.0010 m yr⁻¹  (R²=0.000, p=0.9277, n=21)
  C4 spring trend: -0.0012 m yr⁻¹  (R²=0.000, p=0.9540, n=19)
  C5 spring trend: -0.0379 m yr⁻¹  (R²=0.267, p=0.0197, n=20)
  ✓ Saved: 14_spring_trend_stats.csv
  ✓ Saved: 14_climate_trajectory_spring.png  (158 dpi)
  [14] Saved: 14_climate_trajectory_spring.png
  ✓ Saved: 14_annual_extremes.csv
  ✓ Saved: 14_winter_exceedance.csv
  [14] Saved: 14_seasonal_extremes_scatter.html

[14] Climate projection figures complete.

  ✓ done  (3.6s)

  ▶ STEP 16/52  Bootstrap year-of-crossing for Curreli thresholds (§7 Conclusion 11)
      script: 14b_year_of_crossing.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 14b_year_of_crossing.png smallest label ~4.2 pt as authored when placed at 160 mm (figsize 15.0×9.0 in).
────────────────────────────────────────────────────────────────────────
14b — Bootstrap year-of-crossing for per-cluster summer-min trends
────────────────────────────────────────────────────────────────────────
Loaded 102 summer-min rows across 5 clusters

Wrote outputs/14_climate_projections/14b_year_of_crossing.csv

─── Year of crossing (median, 95% CI) ───
Cluster Threshold    slope (mm/yr)          crossing yr (5–50–95)
------------------------------------------------------------------------
C1     SD15b               -10.88           2080 –  2080 –  2080
C1     SD16                -10.88           2022 –  2028 –  2049
C2     SD15b               -11.23           2080 –  2080 –  2080
C2     SD16                -11.23           2010 –  2015 –  2080
C3     SD15b                -9.40           2080 –  2080 –  2080
C3     SD16                 -9.40           2007 –  2080 –  2080
C4     SD15b               -17.77           2080 –  2080 –  2080
C4     SD16                -17.77           2080 –  2080 –  2080
C5     SD15b               -35.94           2080 –  2080 –  2080
C5     SD16                -35.94           2006 –  2080 –  2080
  ✓ Saved: 14b_year_of_crossing.png  (126 dpi)

Wrote outputs/14_climate_projections/14b_year_of_crossing.png
Wrote outputs/14_climate_projections/14b_year_of_crossing_results.md

────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
Done

────────────────────────────────────────────────────────────────────────
  ✓ done  (2.3s)

  ▶ STEP 17/52  Figure: DEM site overview
      script: 12_figure_site_overview.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 12_01_dem_site_overview.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×12.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 12 — Figure — Site Overview  [v1.4.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Site overview map (report Figure 1) ──────────────────────

============================================================
 GENERATING FIGURE 1: FULL DEM AND SITE OVERVIEW
============================================================
  · Loading DEM via map_utils.load_dem_layer()...
  · Adding KML site features...
  · Plotting Monitoring Wells...
  · Adding well name labels...
  · Repelling 99 well name labels...
  ✓ Saved: 12_01_dem_site_overview.png  (158 dpi)
  [SUCCESS] Map saved locally as /home/john/projects/NRG/outputs/12_figure_site_overview/12_01_dem_site_overview.png

──  Phase 2 · Northern break in slope ──────────────────────────────────
  · Llyn Rhos-Ddu from 01_locations.csv: E 242560.208, N 364820.878, 7.34 m AOD
  · break window 241000-243800 E, 364100-365600 N — 1400 columns x 750 rows of the DEM
  ▸ skipped 411 column(s): no_plain
  ▸ skipped 154 column(s): no_relief
  • break: 835 columns; elevation median 11.387 m AOD (p10 8.919, p90 13.714, sd 1.683 m)
  ·     northing 364623 to 365505, easting 241823 to 243491
  ✓ Saved: 12_02_break_in_slope.csv  (835 columns)
  ✓ Saved: 12_report_numbers.csv  (11 value(s))
  ·     break_lake_offset_north_m: 220.12
  ·     break_lake_offset_vertical_m: 4.04
  ↳ a CANDIDATE landward limit for the sand aquifer — modelled and unconfirmed, and the NORTHERN boundary only
  ✓ Saved: 12_02_break_in_slope.png  (172 dpi)
  ✓ Saved: 12_02_break_in_slope.png

────────────────────────────────────────────────────────────────────────
Done  (Script 12)

  ✓ done  (12.8s)

  ▶ STEP 18/52  Figure: Experimental design GIS map
      script: 13_figure_experimental_design.py
  ──────────────────────────────────────────────────────────────────
/home/john/projects/NRG/venv/lib/python3.12/site-packages/geopandas/plotting.py:305: UserWarning: You passed a edgecolor/edgecolors ('black') for an unfilled marker ('x').  Matplotlib is ignoring the edgecolor in favor of the facecolor.  This behavior may change in the future.
  collection = ax.scatter(x, y, vmin=vmin, vmax=vmax, cmap=cmap, **kwargs)
  ⚠ WARNING: Legibility: 13_01_experimental_setup_map.png smallest label ~3.9 pt as authored when placed at 160 mm (figsize 16.0×12.0 in).

──  Phase 1 · Loading spatial datasets ─────────────────────────────────

──  Phase 2 · Categorising wells by experimental role ──────────────────

──  Phase 3 · Generating figure ────────────────────────────────────────
  ▸ Drawing hierarchical pairings...

──  Phase 4 · Repelling text labels ────────────────────────────────────
  ✓ Saved: 13_01_experimental_setup_map.png  (118 dpi)

Success! Reviewer-ready GIS map saved as '/home/john/projects/NRG/outputs/13_figure_experimental_design/13_01_experimental_setup_map.png'.
  ✓ done  (7.7s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 5  — Depth-Dependent PET Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 19/52  Depth-dependent PET analysis
      script: 15_depth_dependent_pet.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 15 — Depth-Dependent PET Model  [v1.4.0]
════════════════════════════════════════════════════════════════════════
=================================================================
  15: Depth-Dependent PET Model — Grid Search
=================================================================
Loading data...
  Loaded upstand data for 99 wells
Building cluster centroids...
  C1: 7 wells, mean upstand = 0.057 m
  C2: 24 wells, mean upstand = 0.075 m
  C3: 21 wells, mean upstand = 0.091 m
  C4: 9 wells, mean upstand = 0.140 m
  C5: 5 wells, mean upstand = 0.102 m

Fitting standard SSM baselines (κ=0)...
  C1  one-step R²=0.783  iterative NSE=0.694  n=100
  C2  one-step R²=0.801  iterative NSE=0.779  n=100
  C3  one-step R²=0.830  iterative NSE=0.828  n=100
  C4  one-step R²=0.747  iterative NSE=0.599  n=100
  C5  one-step R²=0.715  iterative NSE=0.805  n=100

Grid searching κ ∈ [0.0, 6.0] step 0.05 (121 values)...
  C1 ... best κ=2.25  NSE=0.878
  C2 ... best κ=0.95  NSE=0.873
  C3 ... best κ=0.45  NSE=0.871
  C4 ... best κ=0.20  NSE=0.733
  C5 ...   ⚠ WARNING: Legibility: 15_01_lambda_profile.png smallest label ~4.2 pt as authored when placed at 160 mm (figsize 15.0×8.0 in).
  ⚠ WARNING: Legibility: 15_02_fit_comparison.png smallest label ~3.7 pt as authored when placed at 160 mm (figsize 17.0×10.0 in).
best κ=0.50  NSE=0.838

Extracting best parameters...

=================================================================
  BENCHMARK SUMMARY — Depth-Dependent vs Standard SSM
=================================================================
Cluster    SSM NSE   DDP NSE    Δ NSE    Best κ  Note
-----------------------------------------------------------------
  C1          0.694      0.878    +0.184      2.25  ↑ improvement
  C2          0.779      0.873    +0.094      0.95  ↑ improvement
  C3          0.828      0.871    +0.043      0.45  ↑ improvement
  C4          0.599      0.733    +0.134      0.20  ↑ improvement
  C5          0.805      0.838    +0.033      0.50  ↑ improvement
=================================================================

Saving outputs...
  ✓ Saved: 15_03_benchmark_table.csv
  ✓ Saved: 15_04_best_params.csv

Generating figures...
  ✓ Saved: 15_01_lambda_profile.png  (126 dpi)
  ✓ Saved: 15_01_lambda_profile.png
  ✓ Saved: 15_02_fit_comparison.png  (111 dpi)
  ✓ Saved: 15_02_fit_comparison.png

15 Complete.
  ✓ done  (4.1s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 6  — WTF Cluster Sy Estimation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 20/52  WTF cluster Sy estimation
      script: 17_wtf_specific_yield.py
  ──────────────────────────────────────────────────────────────────
  ⚠ [deps] This step's outputs are consumed earlier by: 09b_scraping_propagation.py (step 9). On a fresh tree those steps used fallbacks — re-run them after this step for final figures.
  ⚠ WARNING: Legibility: 17_wtf_02_regression.png smallest label ~4.4 pt as authored when placed at 160 mm (figsize 13.0×8.0 in).
  ⚠ WARNING: Legibility: 17_wtf_03_event_boxplot.png smallest label ~4.6 pt as authored when placed at 160 mm (figsize 11.0×5.5 in).
  ⚠ WARNING: Legibility: 17_wtf_05_rapid_events.png smallest label ~4.6 pt as authored when placed at 160 mm (figsize 11.0×5.5 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 17 — WTF Specific Yield  [v1.4.3]
════════════════════════════════════════════════════════════════════════
Loading data...
  250 monthly records, 2005-03-01 to 2026-02-01
  Partition: k=5 (C1 (Lake Edge), C2 (Dune), C3 (Western Residual), C4 (Main Forest), C5 (Coastal Forest))
  Forest clusters (interception-corrected): C4 (Main Forest), C5 (Coastal Forest)

Approach A — OLS regression (winter months, drainage-corrected):
  C1 (Lake Edge)                    Sy = 0.342  R² = 0.594  n = 40  SE = 0.0453  β₃ = 0.098
  C2 (Dune)                         Sy = 0.338  R² = 0.666  n = 51  SE = 0.0338  β₃ = 0.069
  C3 (Western Residual)             Sy = 0.352  R² = 0.837  n = 53  SE = 0.0215  β₃ = 0.051
  C4 (Main Forest)                  Sy = 0.297  R² = 0.845  n = 48  SE = 0.0186  β₃ = 0.018
  C5 (Coastal Forest)               Sy = 0.412  R² = 0.863  n = 50  SE = 0.0235  β₃ = 0.044

Approach B — Event-based median:
  C1 (Lake Edge)                    Sy median = 0.210  IQR [0.127, 0.255]  n = 58
  C2 (Dune)                         Sy median = 0.267  IQR [0.194, 0.369]  n = 62
  C3 (Western Residual)             Sy median = 0.327  IQR [0.281, 0.393]  n = 56
  C4 (Main Forest)                  Sy median = 0.312  IQR [0.254, 0.401]  n = 51
  C5 (Coastal Forest)               Sy median = 0.355  IQR [0.321, 0.432]  n = 36
  C4 (Main Forest) (corrected)      Sy median = 0.260  IQR [0.181, 0.324]  n = 63
  C5 (Coastal Forest) (corrected)   Sy median = 0.321  IQR [0.244, 0.388]  n = 51

Approach C — Rapid recharge events (Crosbie et al., 2005):
  C1 (Lake Edge)                    Sy = 0.180  95% CI [0.097, 0.220]  n = 19
  C2 (Dune)                         Sy = 0.260  95% CI [0.180, 0.333]  n = 20
  C3 (Western Residual)             Sy = 0.319  95% CI [0.274, 0.409]  n = 16
  C4 (Main Forest)                  Sy = 0.273  95% CI [0.235, 0.348]  n = 13  (interception-corrected)
  C5 (Coastal Forest)               Sy = 0.311  95% CI [0.270, 0.376]  n = 13  (interception-corrected)

Generating figures...
  ✓ Saved: 17_wtf_02_regression.png  (145 dpi)
Regression figure saved → 17_wtf_02_regression.png
  ✓ Saved: 17_wtf_03_event_boxplot.png  (172 dpi)
Boxplot figure saved → 17_wtf_03_event_boxplot.png
  ✓ Saved: 17_wtf_05_rapid_events.png  (172 dpi)
Rapid-events figure saved → 17_wtf_05_rapid_events.png

Exporting outputs...
CSV saved → 17_wtf_01_sy_estimates.csv
Summary saved → 17_wtf_04_summary.txt

All outputs written to /home/john/projects/NRG/outputs/17_wtf_specific_yield
  ✓ done  (2.4s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 7  — Water Balance Decomposition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 21/52  Water balance decomposition
      script: 16_water_bal.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 16 — Water Balance  [v1.2.0]
════════════════════════════════════════════════════════════════════════
Starting 16: Water Balance Decomposition...

  HEAD-SPACE WATER BALANCE (m/month)
  Cluster                    Rech       ET    Drain   Losses     Resid    D%   ET%
  C1 (Lake Edge)           0.3404   0.0505   0.2940   0.3445   -0.0041   85%   15%
  C2 (Dune)                0.2953   0.0946   0.2037   0.2983   -0.0030   68%   32%
  C3 (Western Residual)    0.2653   0.0983   0.1668   0.2651   +0.0002   63%   37%
  C4 (Main Forest)         0.1842   0.1402   0.0440   0.1842   -0.0000   24%   76%
  C5 (Coastal Forest)      0.1804   0.0694   0.1143   0.1837   -0.0033   62%   38%
  ✓ Saved: 16_water_bal_table.csv

  RECESSION PARTITION (winter/summer ratio)
  Cluster                   Win Δh    Sum Δh  D_frac   n_w   n_s
  C1 (Lake Edge)           -0.0980   -0.1627    0.60    27    50
  C2 (Dune)                -0.0755   -0.1683    0.45    19    55
  C3 (Western Residual)    -0.0848   -0.1361    0.62    18    62
  C4 (Main Forest)         -0.0624   -0.1264    0.49    16    72
  C5 (Coastal Forest)      -0.0683   -0.0927    0.74    22    67
  ✓ Saved: 16_water_bal_vol_table.csv
  ✓ Saved: 16_water_bal_bar_ms.png
  ✓ Saved: 16_water_bal_bar_lay.png

  Done.
  ✓ done  (1.8s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 8  — WTF Spatial Analysis and Sy Mapping
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 22/52  WTF spatial analysis and Sy mapping
      script: 18_wtf_spatial.py
  ──────────────────────────────────────────────────────────────────
  ⚠ [deps] This step's outputs are consumed earlier by: 09d_scenario_comparison.py (step 9). On a fresh tree those steps used fallbacks — re-run them after this step for final figures.
  ⚠ WARNING: Legibility: 18_wtf_03_sy_contour.png smallest label ~4.2 pt as authored when placed at 160 mm (figsize 12.0×10.0 in).
  ⚠ WARNING: Legibility: 18_wtf_04_sy_contour_extended.png smallest label ~4.2 pt as authored when placed at 160 mm (figsize 12.0×10.0 in).
  ⚠ WARNING: Legibility: 18_wtf_05_halflife_map.png smallest label ~4.2 pt as authored when placed at 160 mm (figsize 12.0×10.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 18 — WTF Spatial Analysis  [v1.9.2]
════════════════════════════════════════════════════════════════════════
────────────────────────────────────────────────────────────────────────
  18: WTF Spatial Analysis — Individual Well Sy and Mapping
  Supplementary figures: yes
────────────────────────────────────────────────────────────────────────

Loading well data...

Running reference well WTF analysis...
  66 wells processed  (66 high confidence)

Exporting reference well Sy table...
  Saved → 18_wtf_01_well_sy_estimates.csv

Re-running WTF without canopy correction (diagnostic only)...
  66 wells processed  (66 high confidence)

Computing open-dune Sy plane and within-forest Sy correlations...
  • Open-dune Sy plane: n=52, R2=0.613, 0.0712 Sy/km at 234°
  • Within-forest Sy (n=14): r vs elevation -0.952, r vs ridge distance +0.837
  ✓ Saved: 18_wtf_07_sy_spatial_trends.csv (42 rows)

Generating spatial point map (reference wells)...
  Point map saved → 18_wtf_02_spatial_sy_map.png

Generating Sy contour map (reference wells only)...
  Site mask: 3780 of 5016 grid cells inside boundary
  KML features added (6 layers)
  ✓ Saved: 18_wtf_03_sy_contour.png  (158 dpi)
  Contour map saved → 18_wtf_03_sy_contour.png

Running extended well WTF analysis...
  22 extended wells processed  (17 high confidence)

Generating Sy contour map (reference + extended wells)...
  Site mask: 3780 of 5016 grid cells inside boundary
  KML features added (6 layers)
  ✓ Saved: 18_wtf_04_sy_contour_extended.png  (158 dpi)
  Extended contour map saved → 18_wtf_04_sy_contour_extended.png

Computing drainage decay half-life (t½ = ln(2)/β₃)...
  1/β₃ computed for 64 wells; 2 excluded (CEH13, CEH14)
    C1 (Lake Edge): t½ = 6.9 months (range 5.2–8.0), 1/β₃ = 9.9 months
    C2 (Dune): t½ = 9.9 months (range 6.4–12.5), 1/β₃ = 14.3 months
    C3 (Western Residual): t½ = 13.6 months (range 6.8–21.1), 1/β₃ = 19.7 months
    C4 (Main Forest): t½ = 37.9 months (range 17.1–82.0), 1/β₃ = 54.6 months
    C5 (Coastal Forest): t½ = 15.5 months (range 12.1–18.1), 1/β₃ = 22.3 months

Generating half-life map...
  Site mask: 3780 of 5016 grid cells inside boundary
  KML features added (6 layers)
  ✓ Saved: 18_wtf_05_halflife_map.png  (158 dpi)
  Half-life map saved → 18_wtf_05_halflife_map.png

Computing storage–drainage index (τ = Sy/β₃) — diagnostic CSV only...
  t½ and storage–drainage index computed for 64 wells; 2 excluded (CEH13, CEH14)
    C1 (Lake Edge): t½ = 7.1 months (range 5.2–8.0, n=7)
      storage–drainage index = 2.1 (range 1.3–2.6) — diagnostic, not a duration
    C2 (Dune): t½ = 10.0 months (range 6.4–12.5, n=24)
      storage–drainage index = 3.7 (range 2.1–4.9) — diagnostic, not a duration
    C3 (Western Residual): t½ = 13.6 months (range 6.8–21.1, n=21)
      storage–drainage index = 6.3 (range 2.6–10.5) — diagnostic, not a duration
    C4 (Main Forest): t½ = 32.0 months (range 17.1–82.0, n=7)
      storage–drainage index = 13.7 (range 6.2–30.2) — diagnostic, not a duration
    C5 (Coastal Forest): t½ = 15.8 months (range 12.1–18.1, n=5)
      storage–drainage index = 6.8 (range 5.4–7.7) — diagnostic, not a duration
  Saved → 18_wtf_05_storage_drainage_index.csv

Generating aquifer diagnostic synthesis scatter (Fig 48)...
  64 wells with t½ + ΔNSE + Sy for synthesis scatter
  ✓ Saved: 18_wtf_06_aquifer_diagnostic_synthesis.png  (189 dpi)
  Aquifer diagnostic synthesis saved → 18_wtf_06_aquifer_diagnostic_synthesis.png
  Saved → 18_report_numbers.csv (22 report numbers)

All outputs written to /home/john/projects/NRG/outputs/18_wtf_spatial
  ✓ done  (64.6s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 9  — Spatial Groundwater Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 23/52  Spatial groundwater analysis
      script: 19_spatial_groundwater.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 19 — Spatial Groundwater Scenarios  [v2.17.0]
════════════════════════════════════════════════════════════════════════
============================================================
Script 19 -- Scenario Viewer Generator
Output: /home/john/projects/NRG/outputs/19_spatial_groundwater/scenario_viewer.html
============================================================

[1/4] Loading data...

[2/4] Building well table...
  Well table: 77 wells
  beta available: 66 wells
  Forest wells (C4+C5): 14
  P_bar  = 74.24 mm/mo   PET_bar = 54.47 mm/mo

[3/4] Loading KML polygons from DATA_DIR...
  DATA_DIR = /home/john/projects/NRG/data
  clearfell.kml: 5 pts
  Features.kml: found ['lake', 'forest_raw'] + 18 line feature(s)
  broadleaf_restock.kml: 16 pts
  site_boundary.kml: 15 pts (simplified)
  Forest (clipped): 9 pts

[4/4] Generating HTML...
  Building DEM hillshade basemap...
  Hillshade: 1100x750 px, 1118.1 KB base64
  Building DEM grid for ridge masking...
  DEM grid: 160x110 cells, ~114.0 KB JSON
  Scenario summary CSV: 19_scenario_summary.csv (144 rows = 6 scenarios x 4 seasons (incl. msl5) x 6 spatial units)
  ΔMSL5 cross-check vs 26b per-well CSV: max abs diff = 0.034 mm (≤ 0.5 mm tolerance) — OK

  Saved   : /home/john/projects/NRG/outputs/19_spatial_groundwater/scenario_viewer.html
  Version : v2.17.0
  Size    : 1297.0 KB
  Wells   : 77 total  (beta available: 66)
  Extent  : E 240200-243700, N 362400-364800
  KML     : ['clearfell', 'lake', 'tracks', 'broadleaf', 'site', 'forest']

--- Script 19 complete ---
Open scenario_viewer.html in any browser.
  ✓ done  (5.0s)

  ▶ STEP 24/52  Spatial paper figures
      script: 20_spatial_figures.py
  ──────────────────────────────────────────────────────────────────
  ⚠ [deps] This step's outputs are consumed earlier by: 09d_scenario_comparison.py (step 9). On a fresh tree those steps used fallbacks — re-run them after this step for final figures.
  ⚠ [deps] This step reads OUT_26_5YR_PER_WELL from 26_van_willegen_msl.py (step 30); if that hasn't run yet it falls back.
  ⚠ [deps] This step reads OUT_25_FIT_PARAMETERS from 25_coastal_gradient.py (step 26); if that hasn't run yet it falls back.
  ⚠ WARNING: Legibility: 20_head_surface_streams.png smallest label ~5.0 pt as authored when placed at 160 mm (figsize 10.0×9.0 in).
  ⚠ WARNING: Legibility: 20_residual_ssm.png smallest label ~5.0 pt as authored when placed at 160 mm (figsize 10.0×9.0 in).
  ⚠ WARNING: Legibility: 20_slope_gradient.png smallest label ~5.0 pt as authored when placed at 160 mm (figsize 10.0×9.0 in).

=== 20_spatial_figures.py ===
  DPI: 300  (publication)

[1/4] Loading data...
[2/4] Building well table...
  Reference wells: 67, Extended wells: 22
  Wells: 89  (residual available for 66)
  P̄ = 74.1 mm/month  PET̄ = 54.4 mm/month  (averaged over the head record, 2005-03 to 2026-02)
[3/4] Loading stream polygons...
  Stream polygons loaded: 2391
[4/4] Loading KML features...
  KML features: 22

Generating Figure 1 — Head surface + stream network...
  ✓ Saved: 20_head_surface_streams.png  (189 dpi)
  Saved: 20_head_surface_streams.png
Generating Figure 2a — SSM water balance residual...
  Saved → 20_residual_perwell.csv (66 wells)
  Saved → 20_residual_report_numbers.csv (6 report numbers)
  Site mask: 3680 of 4389 grid cells inside boundary
  Stream polygons loaded: 2391
  ✓ Saved: 20_residual_ssm.png  (189 dpi)
  Saved: 20_residual_ssm.png
Generating Figure 2b — Ridge hillslope gradient...
  Computing hillslope gradient...
  ✓ Saved: 20_slope_gradient.png  (189 dpi)
  Saved: 20_slope_gradient.png
Generating Figure 3 — Forest drawdown propagation...
  λ = 230 m  (K=6.0, Sy=0.3083 [C3 WTF], b=5.0, β₃=0.0569/month [C3 SSM])
  Saved → 20_drawdown_perwell.csv (89 wells)
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  Saved → 20_report_numbers.csv (13 report numbers)
  site_boundary.kml loaded for clipping (type=Polygon)
  ✓ Saved: 20_drawdown_propagation_nohead.png  (189 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_drawdown_propagation_nohead.png
Generating Figure 4 — Coastal-erosion drawdown...
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  h₀ = 81.1 mm  (6 m retreat × 31.35/2.3207 mm per m, rate Script 40 measured 2006-2026 (20.2 yr)), L = 894 m
  ✓ Saved: 20_coastal_erosion.png  (189 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_coastal_erosion.png
Generating Figure 5 — Sea-level-rise head response...
  SLR response: +0.020 m over 5 yr; D=97.3 m²/day (Sy=0.308 [C3 WTF]), √(Dt)=421 m
  ✓ Saved: 20_slr_response.png  (189 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_slr_response.png
Generating Figure 6 — Net coastal head change (SLR − erosion)...
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  net head change range: -64.9 to 20.0 mm  (h₀_eros=81, SLR=20 mm)
  ✓ Saved: 20_coastal_net_effect.png  (189 dpi)
Generating Figure 7 — Scrape-drain drawdown...
  λ = 230 m  (K=6.0, Sy=0.3083 [C3 WTF], b=5.0, β₃=0.0569/month [C3 SSM]);  H0 = 129 mm (measured CEH36 response) → inferred cut 0.42 m
  coastline_hwm.geojson loaded (type=LineString, length=15212 m)
  Saved → 20_scrape_drawdown_perwell.csv (89 wells)
  ✓ Saved: 20_scrape_drawdown_nohead.png  (189 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_scrape_drawdown_nohead.png
Generating clearfell-baseline drawdown map (scrape + Storm Brendan)...
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  clearfell-baseline drawdown: max 254 mm (scrape H0=129 mm [measured], Storm Brendan h0=81 mm, retreat=6 m)
  ✓ Saved: 20_clearfell_baseline_drawdown.png  (189 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_clearfell_baseline_drawdown.png
Generating public-summary three-driver panel...
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  ✓ Saved: 20_public_drivers_panel.png  (180 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_public_drivers_panel.png  (forest H0=150, scrape H0=129, erosion h0=81 mm)
Generating MSL5 change map (window end 2017 vs 2023)...
  MSL5 change: excluded 2 flagged well(s) (msl5_excluded)
  MSL5 change: n=59 wells, range -229 to -13 mm
  Saved → 20_msl5_change_perwell.csv (59 wells)
  Saved → 20_msl5_report_numbers.csv (10 report numbers)
  ✓ Saved: 20_msl5_change_2017_2023.png  (210 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_msl5_change_2017_2023.png
Generating observed water-table change map (2012–2015 vs 2024–2026)...
  Observed spring change: 64 wells, climate offset = -51.7 mm, normalised range -145 to +93 mm
  ✓ Saved: 20_observed_change_2012_2026.png  (210 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_observed_change_2012_2026.png
Generating net water-table state map (all five drivers)...
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  ✓ Saved: 20_net_state_map.png  (210 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_net_state_map.png  (net range -289 to 130 mm)
Generating 2005→2025 modelled driver-change map (5-yr chronic coastal)...
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  ✓ Saved: 20_driver_change_2005_2025.png  (210 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_driver_change_2005_2025.png  (range -323 to 133 mm; coastal 5-yr; clearfell +113 mm)
Generating 2005→2025 driver-change map (20-yr coastal, log scale)...
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  ✓ Saved: 20_driver_change_20yr.png  (210 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_driver_change_20yr.png  (range -745 to 133 mm; coastal 20-yr; clearfell +113 mm)
Generating clearfell gain map...
  Clearfell gain: 71 wells, range -162 to +100 mm (median +27 mm)
  ✓ Saved: 20_clearfell_gain.png  (210 dpi)
  Saved → /home/john/projects/NRG/outputs/20_spatial_figures/20_clearfell_gain.png  (n=71, range -162 to +100 mm)

=== Script 20 complete ===
  ✓ done  (89.4s)

  ✓ Phase 9 validation passed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 10 — Forestry Scenario Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 25/52  Forestry scenarios and management figures
      script: 21_forestry_scenarios.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 21_forestry_01_hydrograph.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×10.0 in).
  ⚠ WARNING: Legibility: 21_forestry_02_distributions.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 12.0×10.5 in).
  ⚠ WARNING: Legibility: 21_forestry_04_baci_zone_violin.png smallest label ~4.3 pt as authored when placed at 160 mm (figsize 14.5×8.5 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 21 — Forestry Scenarios  [v1.8.0]
════════════════════════════════════════════════════════════════════════

=== 21_forestry_scenarios.py ===
  DPI: 300  (publication)

[0/6] Loading BACI parameters from Script 10 outputs...
  BACI annual step from 10a: 0.1131 m (directly fitted, full record, full ANCOVA spec)
  BACI summer step from 10a: 0.0501 m (directly fitted, Jun-Sep, full ANCOVA spec)
  β₂ multiplier from pipeline params: 1.0189
  BACI_ANNUAL=0.113  BACI_SUMMER=0.050
  CLEARFELL_B2_MULT=1.0189  THINNING_B2_MULT=1.0094

[1/6] Loading data...
  Master: 66 wells  |  Climate: 1930-12-01 to 2026-02-01

[2/6] Building scenarios...
  Scenario β from pipeline params: β₁=2.4771  β₂=2.5626  β₃=0.0185
  C4 mean DEM: 10.60 m AOD
  β₁=2.4771  β₂=2.5626  β₃=0.0185
  Scenarios: ['Baseline (Corsican pine)', 'Full clearfell', '50% thinning', 'Broadleaf conversion']

[3/6] Plotting hydrograph figure...
  ✓ Saved: 21_forestry_01_hydrograph.png  (172 dpi)
  ✓ Saved: 21_forestry_01_hydrograph.png
  ✓ Saved: 21_forestry_01_hydrograph.csv

  === Monthly depth below ground — scenario summary (m) ===
  Month  Baseline (Cors  Full clearfell  50% thinning    Broadleaf conv  Observed
  Jan             0.907           0.859           0.883           0.882     0.907
  Feb             0.834           0.798           0.816           0.812     0.834
  Mar             0.831           0.796           0.813           0.808     0.831
  Apr             0.886           0.860           0.873           0.866     0.886
  May             0.950           0.923           0.936           0.934     0.950
  Jun             1.113           1.086           1.100           1.121     1.113
  Jul             1.248           1.215           1.232           1.266     1.248
  Aug             1.354           1.317           1.335           1.375     1.354
  Sep             1.463           1.416           1.440           1.462     1.463
  Oct             1.472           1.408           1.440           1.449     1.472
  Nov             1.248           1.189           1.218           1.219     1.248
  Dec             1.000           0.938           0.969           0.970     1.000

  === Summer minimum (Aug, m below ground) ===
  Baseline (Corsican pine)      : 1.354  (shift vs baseline: +0.000 m)
  Full clearfell                : 1.317  (shift vs baseline: +0.036 m)
  50% thinning                  : 1.335  (shift vs baseline: +0.018 m)
  Broadleaf conversion          : 1.375  (shift vs baseline: -0.021 m)
  BACI summer benchmark         : 1.404

[4/6] Loading raw well data...

[4/6] Plotting distributions figure...
  ✓ Saved: 21_forestry_02_distributions.png  (158 dpi)
  ✓ Saved: 21_forestry_02_distributions.png

  === Summer minimum distributions — summary statistics ===
  Group                        Phase                   n    Mean      SD   %>SD16
  ----------------------------------------------------------------------------
  C1 Eastern lake-buffer       Pre-scrape 2005–14      9   0.787   0.117      11%
  C1 Eastern lake-buffer       Scraping era 2015–17    3   0.824   0.135       0%
  C1 Eastern lake-buffer       Post-felling 2018+      8   0.928   0.107      38%
  C2 Eastern mature dune       Pre-scrape 2005–14     10   0.918   0.159      40%
  C2 Eastern mature dune       Scraping era 2015–17    3   1.008   0.166      67%
  C2 Eastern mature dune       Post-felling 2018+      8   1.039   0.152      50%
  C3 Warren interior           Pre-scrape 2005–14     10   1.111   0.195      70%
  C3 Warren interior           Scraping era 2015–17    3   1.186   0.179      67%
  C3 Warren interior           Post-felling 2018+      8   1.202   0.171      75%
  C5 Coastal forest            Pre-scrape 2005–14      9   1.251   0.398      78%
  C5 Coastal forest            Scraping era 2015–17    3   1.547   0.130     100%
  C5 Coastal forest            Post-felling 2018+      8   1.602   0.129     100%
  C4 Main forest               Pre-scrape 2005–14      9   1.572   0.434     100%
  C4 Main forest               Scraping era 2015–17    3   1.740   0.256     100%
  C4 Main forest               Post-felling 2018+      8   1.742   0.285     100%
  ✓ Saved: 21_forestry_02_distributions_means.csv

[5/6] Plotting scraping eras figure...
  ✓ Saved: 21_forestry_03_scraping_eras.png  (189 dpi)
  ✓ Saved: 21_forestry_03_scraping_eras.png
  ✓ Saved: 21_forestry_03_scraping_era_means.csv

[5/6] Plotting BACI zone violin figure...
  ✓ Saved: 21_forestry_04_baci_zone_violin.png  (130 dpi)
  ✓ Saved: 21_forestry_04_baci_zone_violin.png

  Zone                   Phase               n    Mean      SD
  ------------------------------------------------------------
  Impact (WMC3)          Pre-2015            3   1.573   0.154
  Impact (WMC3)          2015–17             3   1.620   0.170
  Impact (WMC3)          Post-fell 2018+     7   1.600   0.168
  Edge (CEH31, CEH20, CE Pre-2015            4   1.781   0.248
  Edge (CEH31, CEH20, CE 2015–17             3   1.696   0.164
  Edge (CEH31, CEH20, CE Post-fell 2018+     8   1.742   0.186
  Forest Ctrl (CEH32, CE Pre-2015            4   1.885   0.402
  Forest Ctrl (CEH32, CE 2015–17             3   1.753   0.241
  Forest Ctrl (CEH32, CE Post-fell 2018+     8   1.776   0.276
  Coastal Ctrl (CEH19, C Pre-2015            4   1.799   0.130
  Coastal Ctrl (CEH19, C 2015–17             3   1.800   0.124
  Coastal Ctrl (CEH19, C Post-fell 2018+     7   1.828   0.106
  Climate Ctrl (CEH9, NW Pre-2015            4   1.171   0.087
  Climate Ctrl (CEH9, NW 2015–17             3   1.190   0.182
  Climate Ctrl (CEH9, NW Post-fell 2018+     8   1.183   0.166
  ✓ Saved: 21_forestry_04_baci_zone_means.csv

[6/6] Plotting scenario comparison figure...
  ✓ Saved: 21_forestry_05_scenario_comparison.jpg  (135 dpi)
  ✓ Saved: 21_forestry_05_scenario_comparison.jpg
  ✓ Saved: 21_forestry_05_scenario_comparison.csv
  ✓ Saved: 21_forestry_06_summer_scenario.csv

=== Script 21 complete ===
  ✓ done  (5.7s)

  ✓ Phase 10 validation passed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 11 — Coastal-Retreat Gradient Analysis (Script 25)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 26/52  Coastal-retreat gradient analysis
      script: 25_coastal_gradient.py
  ──────────────────────────────────────────────────────────────────
  ⚠ [deps] This step's outputs are consumed earlier by: 20_spatial_figures.py (step 24). On a fresh tree those steps used fallbacks — re-run them after this step for final figures.
  ⚠ WARNING: 25_11 is a sensitivity: nothing downstream reads it and the published δ₀ / L are unchanged
  ⚠ WARNING: c spans -0.10 to +24.20 mm/yr on the forest-free panel with the well set unchanged — it is a property of the fit window, not a rate, and is not quoted as one
  ⚠ WARNING: 25_13 is a sensitivity: nothing downstream reads it and the published δ₀ / L / c are unchanged

════════════════════════════════════════════════════════════════════════
SCRIPT 25 — Coastal Gradient Analysis  [v1.24.0]
════════════════════════════════════════════════════════════════════════

========================================================================
 Script 25 — Coastal-retreat gradient analysis
========================================================================

  Distance source: well_metadata.csv  (99 wells, d range 119–2338 m)

  Fitting [1/4] Full network ...
  Fitting [2/4] Forest-free network ...
  Fitting [3/4] C3 only (c fixed to forest-free network) ...
  Fitting [4/4] Full network, canopy controlled ...

  Fitted parameters (linear-capped form):
    Source             δ₀ (mm/yr)      L (m)      c (mm/yr)
    Full            -31.72 ± 1.95    995 ± 57     -0.47
    Forest-free     -31.35 ± 1.97    894 ± 48     -0.10
    C3 only         -29.03 ± 2.74    929 ± 71     -0.10
    Full +canopy    -32.40 ± 1.95    928 ± 48     +0.16
    canopy x time drift = -9.01 ± 2.52 mm/yr (extra fall under pine, net of distance to the coast; well-clustered SE)

  ΔAIC (forest-free, exp − lin-cap) = -4.8  (exp preferred)

  Matched-window sensitivity (reported only, not adopted) ...
    full_panel    n_wells= 61  δ₀= -31.35 ± 1.97  L=   894 ± 48  c= -0.10 ± 0.55  β_cwb·dCWB/dt=+2.93  sum= +2.83
    long_record   n_wells= 19  δ₀= -25.47 ± 2.66  L=   880 ± 72  c= -8.36 ± 0.87  β_cwb·dCWB/dt=+3.07  sum= -5.30
    short_record  n_wells= 42  δ₀= -44.62 ± 4.75  L=   524 ± 44  c= +6.98 ± 0.66  β_cwb·dCWB/dt=+2.81  sum= +9.79
  ▸ Fit-window sensitivity sweep
  · window sweep: 216 fits, 215 usable, 1 rejected (1 at a parameter bound, 0 with a reach beyond the panel's distance range)
  ·   c3_only: c -4.51 to +27.87  |  delta_0 -49.49 to -21.98 mm/yr
  ·   forest_free: c -0.10 to +24.20  |  delta_0 -36.23 to -23.37 mm/yr
  ✓ Saved: 25_12_window_sweep.csv
  ✓ Saved: 25_12_window_sweep.png  (197 dpi)
  ✓ Saved: 25_12_window_sweep.png
  ▸ Fixed-length rolling-window sweep
  · rolling window sweep: 120 fits, 83 usable, 37 rejected (13 at a parameter bound, 28 with a fitted reach beyond the panel's own distance range) (step 3 months)
  ·   forest_free 10y  n= 22  c  -7.76 (sd 13.16)  climate  +6.29 (sd 16.70)  sum  -1.47 (sd  9.64)  corr(c, climate) -0.817
  ·   forest_free 12y  n= 24  c  +1.20 (sd 12.61)  climate  +5.57 (sd 12.51)  sum  +6.78 (sd  7.85)  corr(c, climate) -0.805
  ·   forest_free 15y  n= 24  c  -3.07 (sd 10.92)  climate  +7.22 (sd  3.94)  sum  +4.14 (sd  8.24)  corr(c, climate) -0.777
  ·   forest_free 18y  n= 13  c  -0.20 (sd  4.64)  climate  +3.09 (sd  1.43)  sum  +2.88 (sd  3.95)  corr(c, climate) -0.597
  ✓ Saved: 25_13_rolling_window.csv
  ✓ Saved: 25_13_rolling_window.png  (197 dpi)
  ✓ Saved: 25_13_rolling_window.png

  Fitting MAM-only sensitivity (Mar–May rows) ...
    forest-free lin-cap MAM: δ₀=-33.34 ± 3.47 mm/yr, L=894 ± 78 m (all-season headline: δ₀=-31.35 ± 1.97, L=894)

  Headline coast-edge trend at 150 m (nearest forest-free well 147 m):
    lin-cap  -26.19 ± 1.45   exp  -27.78 ± 1.76
    form spread 1.59 mm/yr here against 9.29 at d=0 — the headline is quoted where the forms agree and the data constrains them

  Season × gradient interaction test (forest-free panel) ...
    [lin-cap] γ = +0.126 ± 0.054  (t = +2.32, p = 0.0202)  →  gradient IS seasonal at 0.05
    [exp] γ = +0.115 ± 0.053  (t = +2.15, p = 0.0314)  →  gradient IS seasonal at 0.05

  Climate-covariate specification range (forest-free lin-cap) ...
  ✓ Saved: 25_15_covariate_specification_range.csv
    δ₀ spans -31.47 to -28.54 mm/yr and L spans 894 to 1047 m across 7 climate covariates (published: δ₀ -31.35, L 894)

  Running BACI corroboration check ...
control_tier impact_zone  d_target_m  d_control_m  baci_absorbs_mm_yr  model_predicts_mm_yr  z_test_baci_vs_model consistent
      Forest      Impact       553.0        955.0               -17.0                 -10.1                 -1.46        yes
      Forest        Edge       587.0        955.0               -11.7                  -8.9                 -0.80        yes
     Climate      Impact       553.0        580.0                 7.3                  -0.9                  2.64         no
     Climate        Edge       587.0        580.0                11.9                   0.3                  2.94         no
    FarField      Impact       553.0       1946.0                19.8                 -12.0                  3.95         no
    FarField        Edge       587.0       1946.0                23.6                 -10.7                  3.82         no
    (read d_target_m against d_control_m before reading the verdict: a tier with little distance contrast cannot carry the test, whichever way its row falls)
  ✓ Saved: 25_06_baci_corroboration_chart.jpg  (189 dpi)

  Per-control-well spread behind each tier row:
    Forest    Impact  tier z = -1.46   per-well z -3.76 to -0.70   absorbs -19.2 to -15.3 mm/yr   2/3 estimated members consistent  [2 member(s) carry no easting x time term]
    Forest    Edge    tier z = -0.80   per-well z -3.91 to +0.45   absorbs -12.0 to -8.9 mm/yr   3/4 estimated members consistent  [1 member(s) carry no easting x time term]
    Climate   Impact  tier z = +2.64   per-well z +0.45 to +4.06   absorbs -3.8 to +15.5 mm/yr   2/5 estimated members consistent
    Climate   Edge    tier z = +2.94   per-well z +1.75 to +4.82   absorbs +1.2 to +20.4 mm/yr   2/5 estimated members consistent
    FarField  Impact  tier z = +3.95   per-well z +2.31 to +4.61   absorbs +13.6 to +28.9 mm/yr   0/5 estimated members consistent
    FarField  Edge    tier z = +3.82   per-well z +2.46 to +4.55   absorbs +19.0 to +31.2 mm/yr   0/5 estimated members consistent

  CWB trend over the headline panel span (2005-03–2026-02): +1.856 mm/yr; β_cwb = 1.5806e-03 m per mm  →  climate term +2.93 mm/yr (c = -0.10; only the sum is identified)

  [summer-min] Computing per-well slopes ...
  · 59 wells with ≥8 years (25_02_per_well_summer_min_slopes.csv)
  ✓ Saved: 25_14_correction_diagnostic.csv
  · distance accounts for 0.184 of the variation in per-well trend; wells sit 14.87 mm/yr from the profile (median per-well slope SE 8.52)
  ·   [ff_lincap] Edge           0/4 in the fit panel; profile predicts -1.21 mm/yr vs Impact (0.08 x the dispersion)
  ·   [ff_lincap] Forest         0/5 in the fit panel; profile predicts -10.14 mm/yr vs Impact (0.68 x the dispersion)
  ·   [ff_lincap] Coastal        0/2 in the fit panel; profile predicts +6.71 mm/yr vs Impact (0.45 x the dispersion)
  ·   [ff_lincap] Climate        5/5 in the fit panel; profile predicts -0.95 mm/yr vs Impact (0.06 x the dispersion)
  ·   [ff_lincap] FarField       5/5 in the fit panel; profile predicts -11.96 mm/yr vs Impact (0.80 x the dispersion)
  ·   [full_lincap_canopy] Edge           0/4 in the fit panel; profile predicts -1.21 mm/yr vs Impact (0.08 x the dispersion)
  ·   [full_lincap_canopy] Forest         0/5 in the fit panel; profile predicts -10.70 mm/yr vs Impact (0.72 x the dispersion)
  ·   [full_lincap_canopy] Coastal        0/2 in the fit panel; profile predicts +6.68 mm/yr vs Impact (0.45 x the dispersion)
  ·   [full_lincap_canopy] Climate        5/5 in the fit panel; profile predicts -0.94 mm/yr vs Impact (0.06 x the dispersion)
  ·   [full_lincap_canopy] FarField       5/5 in the fit panel; profile predicts -13.10 mm/yr vs Impact (0.88 x the dispersion)
  [summer-min] Computing per-cluster attribution (all-season gradient × balanced annual mean; 14_summer_trend_stats.csv retained as context) ...
        cluster_label  mean_dist_coast_m  observed_centroid_mm_yr  observed_per_well_mean_mm_yr  observed_balanced_annual_mean_mm_yr  coastal_gradient_mm_yr  climate_cwb_mm_yr  far_field_offset_mm_yr  unexplained_mm_yr  coastal_gradient_pct_of_basis
       C1 (Lake Edge)            1818.66                    -10.9                         -9.12                               -10.97                    0.00               2.93                    -0.1             -13.80                          -0.00
            C2 (Dune)            1473.35                    -11.2                         -1.04                               -11.10                    0.00               2.93                    -0.1             -13.93                          -0.00
C3 (Western Residual)             802.75                     -9.4                         -7.50                               -14.15                   -3.19               2.93                    -0.1             -13.79                          22.57
     C4 (Main Forest)             888.90                    -17.8                         -0.63                                -6.53                   -0.17               2.93                    -0.1              -9.18                           2.65
  C5 (Coastal Forest)             372.10                    -35.9                        -41.31                               -16.15                  -18.30               2.93                    -0.1              -0.68                         113.31  ⚠ WARNING: Legibility: 25_05_fit_diagnostic.jpg smallest label ~4.2 pt as authored when placed at 160 mm (figsize 15.0×6.0 in).
  ⚠ WARNING: Legibility: 25_05_fit_diagnostic_spring.jpg smallest label ~4.2 pt as authored when placed at 160 mm (figsize 15.0×6.0 in).

  · record-length composition → 25_10_record_length_composition.csv
        cluster_label  n_wells  record_length_break_years  n_wells_long  mean_slope_long_mm_yr  n_wells_short  mean_slope_short_mm_yr  observed_per_well_mean_mm_yr  observed_balanced_annual_mean_mm_yr  composition_gap_mm_yr
       C1 (Lake Edge)        7                       20.0             3                 -11.35              4                   -7.45                         -9.12                               -10.97                   1.85
            C2 (Dune)       28                       20.0             4                 -11.02             24                    0.62                         -1.04                               -11.10                  10.05
C3 (Western Residual)       17                       13.0            16                  -8.50              1                    8.45                         -7.50                               -14.15                   6.65
     C4 (Main Forest)        4                       19.0             2                 -12.58              2                   11.31                         -0.63                                -6.53                   5.89
  C5 (Coastal Forest)        3                       20.0             2                 -32.38              1                  -59.16                        -41.31                               -16.15                 -25.16
  ✓ Saved: 25_05_fit_diagnostic.jpg  (126 dpi)
  ✓ Saved: 25_07_cluster_decomposition.png  (180 dpi)

  [spring-mean] Computing per-well slopes ...
  · 59 wells with ≥8 years (25_02_per_well_spring_mean_slopes.csv)
  ✓ Saved: 25_14_correction_diagnostic_spring.csv
  · distance accounts for 0.293 of the variation in per-well trend; wells sit 14.35 mm/yr from the profile (median per-well slope SE 13.46)
  ·   [ff_lincap] Edge           0/4 in the fit panel; profile predicts -1.21 mm/yr vs Impact (0.08 x the dispersion)
  ·   [ff_lincap] Forest         0/5 in the fit panel; profile predicts -10.14 mm/yr vs Impact (0.71 x the dispersion)
  ·   [ff_lincap] Coastal        0/2 in the fit panel; profile predicts +6.71 mm/yr vs Impact (0.47 x the dispersion)
  ·   [ff_lincap] Climate        5/5 in the fit panel; profile predicts -0.95 mm/yr vs Impact (0.07 x the dispersion)
  ·   [ff_lincap] FarField       5/5 in the fit panel; profile predicts -11.96 mm/yr vs Impact (0.83 x the dispersion)
  ·   [full_lincap_canopy] Edge           0/4 in the fit panel; profile predicts -1.21 mm/yr vs Impact (0.09 x the dispersion)
  ·   [full_lincap_canopy] Forest         0/5 in the fit panel; profile predicts -10.70 mm/yr vs Impact (0.76 x the dispersion)
  ·   [full_lincap_canopy] Coastal        0/2 in the fit panel; profile predicts +6.68 mm/yr vs Impact (0.48 x the dispersion)
  ·   [full_lincap_canopy] Climate        5/5 in the fit panel; profile predicts -0.94 mm/yr vs Impact (0.07 x the dispersion)
  ·   [full_lincap_canopy] FarField       5/5 in the fit panel; profile predicts -13.10 mm/yr vs Impact (0.93 x the dispersion)
  [spring-mean] Computing per-cluster attribution (all-season gradient × balanced annual mean; 14_spring_trend_stats.csv retained as context) ...
        cluster_label  mean_dist_coast_m  observed_centroid_mm_yr  observed_per_well_mean_mm_yr  observed_balanced_annual_mean_mm_yr  coastal_gradient_mm_yr  climate_cwb_mm_yr  far_field_offset_mm_yr  unexplained_mm_yr  coastal_gradient_pct_of_basis
       C1 (Lake Edge)            1818.66                      6.5                          8.51                                 6.56                    0.00               2.93                    -0.1               3.73                           0.00
            C2 (Dune)            1473.35                      0.3                         12.09                                -2.82                    0.00               2.93                    -0.1              -5.65                          -0.00
C3 (Western Residual)             802.75                     -1.0                          3.73                                -4.91                   -3.19               2.93                    -0.1              -4.55                          65.03
     C4 (Main Forest)             888.90                     -1.2                         11.28                                14.70                   -0.17               2.93                    -0.1              12.04                          -1.18
  C5 (Coastal Forest)             372.10                    -37.9                        -39.80                               -14.98                  -18.30               2.93                    -0.1               0.48                         122.11
  · record-length composition → 25_10_record_length_composition_spring.csv
        cluster_label  n_wells  record_length_break_years  n_wells_long  mean_slope_long_mm_yr  n_wells_short  mean_slope_short_mm_yr  observed_per_well_mean_mm_yr  observed_balanced_annual_mean_mm_yr  composition_gap_mm_yr
       C1 (Lake Edge)        7                       19.0             3                   5.05              4                   11.10                          8.51                                 6.56                   1.95
            C2 (Dune)       28                       12.0            27                  12.39              1                    4.21                         12.09                                -2.82                  14.92
C3 (Western Residual)       17                       13.0            16                   3.25              1                   11.33                          3.73                                -4.91                   8.64
     C4 (Main Forest)        4                       18.0             2                   3.85              2                   18.70                         11.28                                14.70                  -3.42
  C5 (Coastal Forest)        3                       19.0             2                 -24.18              1                  -71.03                        -39.80                               -14.98                 -24.82
  ✓ Saved: 25_05_fit_diagnostic_spring.jpg  (126 dpi)
  ✓ Saved: 25_07_cluster_decomposition_spring.png  (180 dpi)

  Building spring-vs-summer comparison ...
  ✓ Saved: 25_08_spring_vs_summer_comparison.png  (172 dpi)
  ↳ Check 2 (raw): Pearson r=+0.498 (p=0.0004), Spearman r=+0.433 (p=0.0027), n=46

  Outputs written to: /home/john/projects/NRG/outputs/25_coastal_gradient/
    25_01_panel_fit_parameters.csv  (all-season + MAM sensitivity)
    25_15_covariate_specification_range.csv  (climate-covariate range)
    25_02_per_well_summer_min_slopes.csv / _spring_mean_slopes.csv
    25_03_cluster_partition.csv / _spring.csv
    25_04_baci_corroboration.csv
    25_14_correction_diagnostic.csv (+ _spring)
    25_04b_baci_corroboration_spread.csv
    25_05_fit_diagnostic.jpg / _spring.jpg
    25_06_baci_corroboration_chart.jpg
    25_07_cluster_decomposition.png / _spring.png
    25_08_spring_vs_summer_comparison.csv + .png
    25_09_season_interaction_test.csv
    25_10_record_length_composition.csv / _spring.csv
    25_11_matched_window_sensitivity.csv  (reported only)
    25_report_numbers.csv
  · Script 25 complete.

  ✓ done  (54.0s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 12 — Supplementary Diagnostics (Scripts 22–24)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 27/52  Residual lag structure analysis
      script: 22_residual_lag_analysis.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 22_04_example_residuals_by_cluster.png smallest label ~4.8 pt as authored when placed at 160 mm (figsize 13.0×12.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 22 — Residual Lag Analysis  [v1.4.0]
════════════════════════════════════════════════════════════════════════
Starting 22: SSM Residual and AR(1) Diagnostics...
 -> Candidate wells: 72 (excluded: ['ceh3', 'ceh37', 'ceh4', 'ceh7', 'ceh8', 'llynrhos'])
 -> Fitted Model B for 63 wells (>= 140 months of data).
 -> Saved: 22_residuals_wide.csv (249 months x 63 wells)
  ✓ Saved: 22_model_b_fits.csv

==============================================================
  AR(1) DIAGNOSTICS SUMMARY
==============================================================
  Wells with AR(1) fit:          63
  Mean phi:                      -0.139
  Median phi:                    -0.143
  Wells with |phi| <  0.3:       59 / 63
  Wells with |phi| >= 0.3:       4 / 63
  Wells with significant AR(1) (p < 0.05): 31 / 63

  Per-cluster mean phi:
Cluster
1.0   -0.160
2.0   -0.133
3.0   -0.167
4.0   -0.055
5.0   -0.230
==============================================================
  ▸ Model A residual-inference diagnostic (reference network, HAC robustness)
  ✓ Saved: 22_05_ssm_residual_autocorrelation.csv

==============================================================
  MODEL A RESIDUAL-INFERENCE SUMMARY (reference network)
==============================================================
  Wells fitted:                  62
  Durbin-Watson median:          2.25 (IQR 2.15-2.41)
  AR(1) phi median:              -0.128
  Ljung-Box(12) reject p<0.05:   24 / 62
  Coeff significance flips HAC:  1 / 186
==============================================================
  ▸ Cluster-mean residual-inference diagnostic (headline β table, HAC robustness)
  ✓ Saved: 22_06_ssm_cluster_mean_inference.csv

==============================================================
  CLUSTER-MEAN RESIDUAL-INFERENCE SUMMARY (headline β table)
==============================================================
  C1 (Lake Edge)         DW 2.22  phi -0.113  flips 0
  C2 (Dune)              DW 2.39  phi -0.200  flips 0
  C3 (Western Residual)  DW 2.40  phi -0.213  flips 0
  C4 (Main Forest)       DW 1.85  phi +0.045  flips 0
  C5 (Coastal Forest)    DW 2.06  phi -0.039  flips 0
  Coeff significance flips HAC:  0 / 15
==============================================================
  ✓ Saved: 22_01_ar1_histogram.png  (210 dpi)
  ✓ Saved: 22_01_ar1_histogram.png
  ✓ Saved: 22_02_ar1_spatial_map.png  (189 dpi)
  ✓ Saved: 22_02_ar1_spatial_map.png
  ✓ Saved: 22_03_alpha_phi_scatter.png  (210 dpi)
  ✓ Saved: 22_03_alpha_phi_scatter.png
  ✓ Saved: 22_04_example_residuals_by_cluster.png  (145 dpi)
  ✓ Saved: 22_04_example_residuals_by_cluster.png

22 complete. Next: cross-correlation stage (22b).
  ✓ done  (7.3s)

  ▶ STEP 28/52  Ridge recharge lag hypothesis test
      script: 23_ridge_recharge_lag_test.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 23_04_b10_b11_by_cluster.png smallest label ~4.5 pt as authored when placed at 160 mm (figsize 14.0×5.5 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 23 — Ridge Recharge Lag Test  [v1.2.1]
════════════════════════════════════════════════════════════════════════
Starting 23: Ridge-recharge lag hypothesis test...
  ▸ Rainfall AR(1) phi = +0.207; pre-whitened series built.
 -> Candidate wells: 72 (excluded: ['ceh3', 'ceh37', 'ceh4', 'ceh7', 'ceh8', 'llynrhos'])
  ▸ Extended-model fit + CCF for 63 wells.
  ✓ Saved: 23_residuals_extended_wide.csv
  ✓ Saved: 23_ridge_lag_fits.csv
  ✓ Saved: 23_01_ccf_headline_ridge_wells.png  (189 dpi)
  ✓ Saved: 23_01_ccf_headline_ridge_wells.png
  ✓ Saved: 23_02_peak_lag_vs_ridge_distance.png  (189 dpi)
  ✓ Saved: 23_02_peak_lag_vs_ridge_distance.png
  ✓ Saved: 23_03_peak_lag_spatial_map.png  (189 dpi)
  ✓ Saved: 23_03_peak_lag_spatial_map.png
  ✓ Saved: 23_04_b10_b11_by_cluster.png  (135 dpi)
  ✓ Saved: 23_04_b10_b11_by_cluster.png
  ✓ Saved: 23_05_hypothesis_test_summary.txt

==============================================================================
  RIDGE-RECHARGE LAG HYPOTHESIS TEST — SUMMARY
==============================================================================

  Ridge reference point: E = 241750, N = 364500 (OSGB36)
  Analysis model: Delta_h = alpha + b10*P(t) + b11*P(t-1) - b2*PET(t) - b3*h_disp_prev(t)
  Displacement formulation: h_disp = 3.7 + h_depth
  Wells analysed: 63 with n >= 140 months
  Excluded: ['ceh3', 'ceh37', 'ceh4', 'ceh7', 'ceh8', 'llynrhos']

------------------------------------------------------------------------------
  HYPOTHESIS
------------------------------------------------------------------------------
  H1: If the water-balance residual reflects genuine lateral recharge from
      the northern rock ridge, then the peak-correlation lag N* between
      extended-model residuals and rainfall should increase with distance
      from the ridge (longer travel time = longer lag).

  H0: If the residual is model error rather than ridge recharge, no such
      distance-lag relationship will exist.

------------------------------------------------------------------------------
  RESULT
------------------------------------------------------------------------------
  Spearman rank correlation of peak lag vs ridge distance:
     rho = -0.0418
     p   = 0.7730
     n   = 50 wells with significant peak

  Mean peak lag (all sig wells):      2.50 months
  Median peak lag (all sig wells):    2.0 months
  Peak lag standard deviation:        1.98 months

  By cluster (significant wells only):
     C1 (Lake Edge)  n= 7  mean lag = 2.00  mean |r| = 0.269
     C2 (Dune)       n=22  mean lag = 2.00  mean |r| = 0.222
     C3 (Western Residual) n=11  mean lag = 2.91  mean |r| = 0.182
     C4 (Main Forest) n= 9  mean lag = 3.67  mean |r| = 0.190

------------------------------------------------------------------------------
  INTERPRETATION
------------------------------------------------------------------------------
  H0 NOT REJECTED: no significant distance-lag relationship detected.
  The water-balance residual cannot be attributed to ridge-derived recharge
  on lag-structure evidence. Either (a) the residual is largely model error
  and should be reported as such, or (b) ridge recharge is delivered via a
  mechanism that does not produce a month-scale distance-dependent lag
  (e.g. a near-steady baseflow that is effectively smoothed in time by the
  time it reaches the dune field).

  Path (b) is not ruled out by a null result here; but it also cannot be
  claimed from these data alone, because a steady baseflow is
  observationally indistinguishable from a constant alpha, which is already
  what Model B absorbs.

==============================================================================

23 complete.
  ✓ done  (7.5s)

  ▶ STEP 29/52  Residual seasonality diagnostics
      script: 24_residual_seasonality.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 24_01_climatology_panels_by_cluster.png smallest label ~4.2 pt as authored when placed at 160 mm (figsize 15.0×8.0 in).
  ⚠ WARNING: Legibility: 24_02_seasonal_amplitude_map.png smallest label ~4.7 pt as authored when placed at 160 mm (figsize 12.0×10.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 24 — Residual Seasonality Diagnostics  [v1.3.0]
════════════════════════════════════════════════════════════════════════
Starting 24: Seasonal Residual Diagnostic...
 -> Loaded sunshine hours: 1142 months (1930-12 to 2026-02)
  ▸ Candidate wells: 72
  ▸ Computed climatologies for 63 wells.
  ✓ Saved: 24_residual_climatology.csv
  ✓ Saved: 24_01_climatology_panels_by_cluster.png  (126 dpi)
  ✓ Saved: 24_01_climatology_panels_by_cluster.png
  ✓ Saved: 24_02_seasonal_amplitude_map.png  (158 dpi)
  ✓ Saved: 24_02_seasonal_amplitude_map.png
  ✓ Saved: 24_03_sun_residual_correlation.png  (210 dpi)
  ✓ Saved: 24_03_sun_residual_correlation.png
  ✓ Saved: 24_04_phase_by_cluster.png  (189 dpi)
  ✓ Saved: 24_04_phase_by_cluster.png
  ✓ Saved: 24_05_diagnostic_summary.txt

==============================================================================
  SEASONAL RESIDUAL DIAGNOSTIC — SUMMARY
==============================================================================

  Wells analysed: 63
  Ridge reference: E=241750, N=364500
  C3 split distance: 1000 m

------------------------------------------------------------------------------
  PER-CLUSTER SEASONAL STATISTICS
------------------------------------------------------------------------------
          n  s_minus_w  amplitude    phase  corr_sun
Cluster                                             
1.0       7    -0.0048     0.0078  12.4552   -0.0540
2.0      24    -0.0041     0.0113  12.0948   -0.0338
3.0      17    -0.0101     0.0109  12.2080   -0.0333
4.0       9    -0.0076     0.0158   2.3549   -0.0078
5.0       5    -0.0008     0.0109  11.1036   -0.0237

------------------------------------------------------------------------------
  SUMMER-MINUS-WINTER CONTRAST — PER-CLUSTER TESTS AGAINST ZERO
------------------------------------------------------------------------------
  Positive = residuals higher in summer than winter. A systematic
  negative contrast would be the signature of unmodelled summer ET.

  Cluster                  n   mean_mm  p_signrank   p_ttest       boot 95% CI (mm)
  C1 (Lake Edge)           7     -4.83      0.5781    0.3426        [-14.18, +2.57]
  C2 (Dune)               24     -4.06      0.1011    0.1000         [-8.81, +0.41]
  C3 (Western Residual)   17    -10.15      0.0000    0.0000        [-12.56, -7.70]
  C4 (Main Forest)         9     -7.56      0.0195    0.0238        [-13.00, -2.78]
  C5 (Coastal Forest)      5     -0.82      1.0000    0.5889         [-3.36, +1.43]

  Sign-rank is the headline test; 10000 bootstrap
  resamples, seed 20260809. Values in mm.

------------------------------------------------------------------------------
  C3 SPLIT BY DISTANCE (< vs >= 1000 m from ridge)
------------------------------------------------------------------------------
  Forest-adjacent (n=7): amplitude = 0.0109  s-w = -0.0136
  Warren-interior (n=10): amplitude = 0.0110  s-w = -0.0078
  Mann-Whitney (adj < far amp): U=38.0, p=0.6302

------------------------------------------------------------------------------
  SUNSHINE-HOURS CORRELATION (INDEPENDENT ET DIAGNOSTIC)
------------------------------------------------------------------------------
  Sunshine hours is not in the OLS regression, so cor(resid, sun) is
  a real test rather than zero by construction. A systematic negative
  correlation would indicate extra ET losses in high-insolation months
  that Thornthwaite has not captured and b2 has therefore not fitted.

  Wells with r < -0.150 (extra ET not in Thornthwaite): 0 / 63
  Wells with r >  +0.150:                                0 / 63
  Wells within Bartlett null band:                          63 / 63
  Network mean: -0.0317

------------------------------------------------------------------------------
  INTERPRETATION
------------------------------------------------------------------------------
  NULL on ET hypothesis: sunshine-residual correlation is within the
  Bartlett null band across clusters and summer-minus-winter residual
  is small in magnitude. The residual is not dominantly unmodelled
  summer ET — whatever systematic bias Thornthwaite has, b2 has
  already absorbed it.

  Wells with winter/early-spring phase peak (Nov-Mar): 50 / 63
  Wells with summer phase peak (May-Aug):              0 / 63

  Dominant phase is winter/early spring. This is not the signature
  of unmodelled summer ET. It is consistent with threshold/nonlinear
  recharge behaviour not captured by the linear b1*P term: in
  mid-winter with saturated soils, rainfall reaches the water table
  with higher efficiency than the cluster-mean b1 represents.

==============================================================================

24 complete.
  ✓ done  (8.6s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 13 — Van Willegen MSL Analyses (Scripts 26, 26b, 26c)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 30/52  Van Willegen (2025) 5-year MSL aggregation
      script: 26_van_willegen_msl.py
  ──────────────────────────────────────────────────────────────────
  ⚠ [deps] This step's outputs are consumed earlier by: 20_spatial_figures.py (step 24). On a fresh tree those steps used fallbacks — re-run them after this step for final figures.
  ⚠ WARNING: NW12 β₃=-0.0133 ≤ 0.001 — EWI undefined, skipped
  ⚠ WARNING: Legibility: 26_ebf_prediction_scatter.png smallest label ~4.2 pt as authored when placed at 160 mm (figsize 15.0×5.2 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 26 — van Willegen MSL Projection  [v1.8.0]
════════════════════════════════════════════════════════════════════════
========================================================================
Script 26 — van Willegen et al. (2025) 5-year MSL aggregation
========================================================================
  01_wells_clean.csv           : 250 rows × 78 wells
  01_wells_extended.csv        : 250 rows × 22 wells
  01_well_elevations.csv       : 99 wells
  01_locations.csv             : 99 wells
  02_cluster_stats.csv         : 66 wells
  06_pear_membership_audit_sitewide.csv : 88 wells
  01_wells_provenance.csv      : 78 wells, 19500 (well,month) cells

Pass 1 — annual MSL/MAX: 1430 (well, hydro_year) rows; 1302 valid (3/3 spring rule)
  ✓ Saved: 26_msl_annual_per_well.csv

Pass 2 — 5-year rolling MSL/MAX: 895 (well, end_year) rows across 85 wells
  ✓ Saved: 26_msl_5yr_per_well.csv
  MSL5 exclusion (flagged in per-well CSV; removed from cluster trajectory / latest / map): CEH13, CEH14

Pass 3 — cluster trajectories (Method A, per-well aggregation): 80 (cluster, year) rows
  ✓ Saved: 26_msl_5yr_per_cluster.csv

Pass 3b — cluster-centroid trajectories (Method B, reference network): 80 (cluster, year) rows
  ✓ Saved: 26_msl_5yr_per_cluster_centroid.csv

Pass 4 — latest MSL5 per well: 83 wells
  ✓ Saved: 26_msl_5yr_latest_per_well.csv

Pass 5 — equilibrium wetness index (EWI) from SSM coefficients
  · long-term monthly climate normals: P̄=0.0715 m  PET̄=0.0530 m
  · extended-network SSM fits contributing to EWI: 20
  ✓ Saved: 26_equilibrium_wetness_index_per_well.csv
  ·   reference  n= 64  EWI mean=-0.792 m below ground
  ·   extended   n= 20  EWI mean=-1.023 m below ground

Pass 6 — EWI-predicted MSL5 vs observed (per-well comparison)
  ✓ Saved: 26_ewi_msl5_comparison.csv
  ·   open-dune calibration  MSL5 = +0.254 + 0.959·EWI   (n=62, r=0.978, RMSE=61 mm)
  ·     |residual| ≤50 mm    : 42 open-dune wells
  ·     |residual| 50–100 mm : 11 open-dune wells
  ·     |residual| 100–200 mm:  9 open-dune wells
  ·     |residual| >200 mm   :  0 open-dune wells
  ·   generalization: RMSE 60 mm on 46 non-van-Willegen open-dune wells vs 63 mm on 16 calibration wells
  ·   out-of-scope forest (C4/C5): n=20, RMSE 153 mm (predicted but flagged unreliable)

Pass 7 — Ellenberg-F cross-validation (MSL5 vs EWI; external dataset)
  ✓ Saved: 26_ebf_comparison.csv
  ·   EbF ~ MSL5:  r=+0.829 [+0.59,+0.93]  RMSE=0.337 EbF-units
  ·   EbF ~ EWI :  r=+0.788 [+0.51,+0.92]  RMSE=0.371 EbF-units
  ·   Williams' test (MSL5 vs EWI): t=+0.784, p=0.445 (indistinguishable)
  ·   match bands (MSL5 / EWI): A 4/5, B 7/7, C 5/2, D 2/4
  ✓ Saved: 26_ebf_prediction_scatter.png  (126 dpi)
  ✓ Saved: 26_ebf_prediction_scatter.png

Pass 8 — metric diagnostics (window sensitivity and index precision)
  ✓ Saved: 26_metric_diagnostics_per_well.csv
  ✓ Saved: 26_index_precision_by_cluster.csv
  ·   autocorrelation (n=65 wells with ≥12 springs): observed lag-1 mean -0.078 against an AR(1) expectation of 0.488
  ·     site-mean spring series: ρ=-0.000 over 21 years
  ·     ρ vs recession time: Spearman r=+0.060, p=0.634 — no association
  ·   interannual spring SD (what drives window sensitivity):
  ·     vs β₂ controlling for t_R: partial r=+0.622, p=3.11e-08
  ·     vs t_R controlling for β₂: partial r=+0.181, p=0.149
  ·     (β₂ and t_R themselves correlate at Spearman +0.381)
  ·   index precision: the equilibrium index is more precise than a 5-year MSL5 mean at 0/65 wells
  ·     C1 (Lake Edge)         MSL5 SE     78 mm | EWI SE     316 mm | ratio 4.05
  ·     C2 (Dune)              MSL5 SE    112 mm | EWI SE     455 mm | ratio 4.05
  ·     C3 (Western Residual)  MSL5 SE    141 mm | EWI SE     513 mm | ratio 3.64
  ·     C4 (Main Forest)       MSL5 SE    181 mm | EWI SE    1115 mm | ratio 6.18
  ·     C5 (Coastal Forest)    MSL5 SE    124 mm | EWI SE     430 mm | ratio 3.47
  ✓ Saved: 26_metric_diagnostics.png  (172 dpi)
  ✓ Saved: 26_metric_diagnostics.png
  ✓ Saved: 26_report_numbers.csv

Pass 9 — Supplementary Table S7.1 (per-well EWI reconstruction)
  ✓ Saved: 26_table_s7_1_ewi_per_well.csv
  ✓ Saved: 26_table_s7_1_ewi_per_well.md
  ·   84 wells listed
  ·     Calibration       62
  ·     Reconstructed      2
  ·     Out of scope      20

Rendering figures...
  ✓ Saved: 26_msl_5yr_trajectory.png  (189 dpi)
  ✓ Saved: 26_msl_5yr_trajectory.png
  ✓ Saved: 26_msl_5yr_quadrat_wells.png  (172 dpi)
  ✓ Saved: 26_msl_5yr_quadrat_wells.png
  ✓ Saved: 26_msl_5yr_map.png  (189 dpi)
  ✓ Saved: 26_msl_5yr_map.png

   → 26_msl_results.txt

Done.
  ✓ done  (11.3s)

  ▶ STEP 31/52  UKCP18 MSL5 climate projections (Tool B)
      script: 26b_van_willegen_msl_projections.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 26b_msl5_ukcp18_projection.png smallest label ~3.6 pt as authored when placed at 160 mm (figsize 14.0×8.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 26b — van Willegen MSL Scenarios  [v1.3.0]
════════════════════════════════════════════════════════════════════════
========================================================================
Script 26b — UKCP18 MSL5 climate projections (Tool B)
========================================================================

  Method: monthly Δh perturbation overlay on observed climatology
  Convention: van Willegen 2025 5-year MSL (window-ends from Script 26)
  Scenarios: UKCP18 RCP8.5 Wales 50th %ile — 2050s and 2080s

  03_03_cluster_mechanistic_coefficients.csv       : 5 clusters
  01_climate.csv                                   : 1143 monthly rows
  26_msl_5yr_per_cluster_centroid.csv              : 80 (cluster, end_year) rows

  Monthly P climatology mean (2005-2026): 74.2 mm/month
  Monthly PET climatology mean: 54.4 mm/month

  Cluster 1 (C1 (Lake Edge)):
    β₁ = 4.5785   β₂ = 0.9228   β₃ = 0.0886
    2050s: spring Δh mean = -0.0112 m/month;  projected ΔMSL5 = -0.011 m
    2080s: spring Δh mean = -0.0210 m/month;  projected ΔMSL5 = -0.021 m

  Cluster 2 (C2 (Dune)):
    β₁ = 3.9721   β₂ = 1.7419   β₃ = 0.0643
    2050s: spring Δh mean = -0.0168 m/month;  projected ΔMSL5 = -0.017 m
    2080s: spring Δh mean = -0.0307 m/month;  projected ΔMSL5 = -0.031 m

  Cluster 3 (C3 (Western Residual)):
    β₁ = 3.5728   β₂ = 1.8073   β₃ = 0.0569
    2050s: spring Δh mean = -0.0169 m/month;  projected ΔMSL5 = -0.017 m
    2080s: spring Δh mean = -0.0308 m/month;  projected ΔMSL5 = -0.031 m

  Cluster 4 (C4 (Main Forest)):
    β₁ = 2.4771   β₂ = 2.5626   β₃ = 0.0185
    2050s: spring Δh mean = -0.0215 m/month;  projected ΔMSL5 = -0.021 m
    2080s: spring Δh mean = -0.0387 m/month;  projected ΔMSL5 = -0.039 m

  Cluster 5 (C5 (Coastal Forest)):
    β₁ = 2.4279   β₂ = 1.2743   β₃ = 0.0449
    2050s: spring Δh mean = -0.0118 m/month;  projected ΔMSL5 = -0.012 m
    2080s: spring Δh mean = -0.0215 m/month;  projected ΔMSL5 = -0.022 m

  ✓ Saved: 26b_msl5_ukcp18_projection_summary.csv
  ✓ Saved: 26b_monthly_delta_h_per_cluster.csv

  Per-well aggregation pathway (v1.1.0):
  Per-well ΔMSL5 aggregation: 66 wells across 5 clusters
    2050s  C1: n= 7  β₁̄=5.0118  β₂̄=0.5419  ΔMSL5 = -0.0088 m
    2050s  C2: n=24  β₁̄=4.2751  β₂̄=1.5879  ΔMSL5 = -0.0159 m
    2050s  C3: n=21  β₁̄=3.5097  β₂̄=1.6825  ΔMSL5 = -0.0159 m
    2050s  C4: n= 9  β₁̄=2.4737  β₂̄=2.5836  ΔMSL5 = -0.0216 m
    2050s  C5: n= 5  β₁̄=2.3385  β₂̄=1.1339  ΔMSL5 = -0.0107 m
    2080s  C1: n= 7  β₁̄=5.0118  β₂̄=0.5419  ΔMSL5 = -0.0167 m
    2080s  C2: n=24  β₁̄=4.2751  β₂̄=1.5879  ΔMSL5 = -0.0292 m
    2080s  C3: n=21  β₁̄=3.5097  β₂̄=1.6825  ΔMSL5 = -0.0290 m
    2080s  C4: n= 9  β₁̄=2.4737  β₂̄=2.5836  ΔMSL5 = -0.0390 m
    2080s  C5: n= 5  β₁̄=2.3385  β₂̄=1.1339  ΔMSL5 = -0.0195 m
  ✓ Saved: 26b_msl5_ukcp18_projection_summary_perwell.csv
  ✓ Saved: 26b_msl5_ukcp18_projection.png  (135 dpi)
  ✓ Saved: 26b_msl5_ukcp18_projection.png
  ✓ Saved: 26b_msl5_ukcp18_results.txt


────────────────────────────────────────────────────────────────────────
Done

  ✓ done  (2.1s)

  ▶ STEP 32/52  MSL5 report-format figures (Figures for §4.8.4 / §4.10.1)
      script: 26c_msl5_report_figures.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 26c — MSL-5 Report Figures  [v1.1.0]
════════════════════════════════════════════════════════════════════════
Script 26c — MSL5 report-format figures
============================================================
  per-cluster trajectory rows : 80
  projection summary rows     : 10
  scenario summary rows       : 144
  ✓ Saved: fig_msl5_trajectory_report.png  (210 dpi)
  wrote fig_msl5_trajectory_report.png
  ✓ Saved: fig_msl5_vs_summer_min_projection.png  (210 dpi)
  wrote fig_msl5_vs_summer_min_projection.png
  wrote 26c_results.txt
=== Script 26c complete ===
  ✓ done  (1.9s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 14 — Cluster Framework Diagnostics (Scripts 28–30)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 33/52  Cluster framework diagnostic: C3 detrend check (H0)
      script: 28_c3_detrend_check.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 28_c3_detrend_panel.png smallest label ~2.9 pt as authored when placed at 160 mm (figsize 15.0×8.8 in).
────────────────────────────────────────────────────────────────────────
c3_detrend_check — diagnostic for HANDOVER_c3_detrend_check.md
────────────────────────────────────────────────────────────────────────
Live fit (forest-free linear-capped): δ₀ = -31.35 mm/yr, L = 894 m
Live fit (full linear-capped):        δ₀ = -31.72 mm/yr, L = 995 m
Cluster assignments loaded: n = 66 wells
Hydrographs loaded: 78 wells × 250 months
Centroids loaded: ['C1', 'C2', 'C3', 'C4', 'C5'] × 250 months

Wrote outputs/28_c3_detrend/28_c3_detrend.csv: 59 rows

─── HEADLINE C3 result ──────────────────────────────────────────
C3 wells with hydrograph + dist data: 16 of 21
After forest-free de-trending:
  ✓ Saved: C2  :   1 (6%)
  ✓ Saved: C3  :  15 (94%)

─── Sanity checks (proportion staying in original cluster) ──────
  C2: stays in C2 = 24/24 (100%)  [excluded: 0]
  C4: stays in C4 = 2/2 (100%)  [excluded: 7]
  C5: stays in C5 = 0/1 (0%)  [excluded: 4]

─── Excluded wells (no dist_coast_m) ──
  nw10        C4 (Main Forest)
  ceh2        C4 (Main Forest)
  ceh16       C5 (Coastal Forest)
  ceh17       C5 (Coastal Forest)
  ceh19       C5 (Coastal Forest)
  ceh20       C4 (Main Forest)
  ceh30       C4 (Main Forest)
  ceh31       C5 (Coastal Forest)
  ceh32       C4 (Main Forest)
  ceh33       C4 (Main Forest)
  ceh34       C4 (Main Forest)
  ceh36       C3 (Western Residual)
  ceh40       C3 (Western Residual)
  ceh41       C3 (Western Residual)
  ceh42       C3 (Western Residual)
  wmc3        C3 (Western Residual)

─── C3 sensitivity ─────────────────────────────────────────────
  forest-free, monthly-uniform (HEADLINE)       → C2:  1  C3: 15  other: 0
  forest-free, summer-only Jun–Sep              → C2:  1  C3: 13  other: 2
  full δ₀ (includes forest)                     → C2:  1  C3: 15  other: 0
  L = 500 m                                     → C2:  1  C3: 14  other: 1
  L = 1500 m                                    → C2:  1  C3: 15  other: 0

Wrote outputs/28_c3_detrend/28_c3_detrend_results.md
  ✓ Saved: 28_c3_detrend_panel.png  (126 dpi)
Wrote outputs/28_c3_detrend/28_c3_detrend_panel.png

────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
Done

────────────────────────────────────────────────────────────────────────
  ✓ done  (5.5s)

  ▶ STEP 34/52  Cluster framework diagnostic: within-C3 spatial structure
      script: 29_c3_within_variance_check.py
  ──────────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────
c3_within_variance_check — what explains within-C3 variation
────────────────────────────────────────────────────────────────────────
C3 wells: 21
Coastal exponential (forest-free): δ₀ = -40.63 mm/yr, L = 489 m
Forest geometry: area = 7.22 km²

Built panel: 21 C3 wells × 24 columns
Saved outputs/29_within_c3_variance/29_within_c3_variance.csv
Saved outputs/29_within_c3_variance/29_report_numbers.csv (9 report numbers)

────────────────────────────────────────────────────────────────────────
Per-metric regression against all 5 predictors
────────────────────────────────────────────────────────────────────────
Metric                         n      R²   adj R²  Strongest unique predictor
------------------------------------------------------------------------
slope_m_yr                    16   0.780    0.669  dist_ceh36_m (Δ=+0.030)
beta_1_recharge               16   0.864    0.796  dist_ceh36_m (Δ=+0.117)
beta_2_atmospheric_draw       16   0.657    0.485  dist_ceh36_m (Δ=+0.151)
beta_3_drainage               16   0.748    0.622  dist_ceh36_m (Δ=+0.190)
recession_time_months         16   0.700    0.551  dist_ceh36_m (Δ=+0.344)
mean_head_maod                16   1.000    1.000  ground_elev_m (Δ=+0.013)
summer_min_depth_m            16   0.993    0.990  depth_to_water_m (Δ=+0.570)
winter_max_depth_m            16   0.978    0.966  depth_to_water_m (Δ=+0.702)
seasonal_amplitude_m          16   0.810    0.715  delta_coast_exp_m_yr (Δ=+0.061)

Univariate R² matrix saved.
Drop-one (unique contribution) matrix saved.

Wrote outputs/29_within_c3_variance/29_within_c3_variance_results.md
  ✓ Saved: 29_within_c3_variance_panel.png  (222 dpi)
Wrote outputs/29_within_c3_variance/29_within_c3_variance_panel.png

────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
Done

────────────────────────────────────────────────────────────────────────
  ✓ done  (2.5s)

  ▶ STEP 35/52  Cluster framework diagnostic: C4 drainage identifiability (tests β2/β3 separability; reports two sensitivities)
      script: 30_c4_drainage_identifiability.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 30 — C4 Drainage Identifiability Diagnostic  [v2.3.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Setup — canonical centroids ──────────────────────────────
  · Built 5 cluster centroids.

──  Phase 2 · Tests A/B/C — centroid identifiability by cluster ────────
  ✓ Saved: 30_c4_identifiability_by_cluster.csv
  ·   C1 (Lake Edge)         β₃=0.0886 (p=0.000)  VIF=1.82  hd_sd=0.339
  ·   C2 (Dune)              β₃=0.0643 (p=0.000)  VIF=1.40  hd_sd=0.368
  ·   C3 (Western Residual)  β₃=0.0569 (p=0.000)  VIF=1.27  hd_sd=0.364
  ·   C4 (Main Forest)       β₃=0.0185 (p=0.002)  VIF=1.10  hd_sd=0.477
  ·   C5 (Coastal Forest)    β₃=0.0449 (p=0.000)  VIF=1.08  hd_sd=0.428
  ▸ C4 (Main Forest) centroid: β₃=0.0185, p=0.0016, VIF=1.10 (2nd lowest), hd_sd=0.477 (largest)

──  Phase 3 · Test D — water-balance closure over β₃ ───────────────────
  · C4 closure-minimising β₃ = 0.0190  (|residual| = 0.00006 m/mo)
  ·   vs fitted β₃ = 0.0185 — the closure minimum lies above the fitted value.

──  Phase 4 · Per-well panel — window vs full record ───────────────────
  ✓ Saved: 30_c4_perwell_beta3.csv
  ·   C4 per-well, 100-month window: 9 wells, 1 negative, 6 non-significant (p>.05), median VIF 1.20
  ·   C4 per-well, full record: 9 wells, 1 negative, 2 non-significant (p>.05)
  ▸ C4 significant positive β₃: 3 of 9 on the 100-month window, 7 of 9 on full records — the per-well weakness is a windowing effect.

──  Phase 5 · C4 centroid exclusion sensitivity (reported, not adopted) 
  ·   all_members          β₃=0.0185 (p=1.6e-03)  t½=37.6 mo  n_members=9
  ·   drop_ceh14           β₃=0.0244 (p=1.9e-05)  t½=28.4 mo  n_members=8
  ·   drop_msl5_excluded   β₃=0.0290 (p=6.0e-07)  t½=23.9 mo  n_members=7
  ✓ Saved: 30_c4_centroid_sensitivity.csv
  ✓ Saved: 30_c4_report_numbers.csv (11 numbers)

──  Phase 6 · Figure — per-well β₃ panel, window vs full record ────────
  ✓ Saved: 30_c4_drainage_identifiability.png  (242 dpi)
  ✓ Saved: 30_c4_drainage_identifiability.png
  ▸ Verdict for C4 (Main Forest): β₃ = 0.0185 (p = 0.0016); collinearity VIF 1.10, 2nd lowest of 5 clusters (test A); displacement SD 0.477 m, largest (test B); recession-only response p = 3.01e-07 (test C); closure minimum above the fitted value (test D). Per-well: 7 of 9 resolve on full records against 3 on the 100-month window.
  ✓ done  (3.7s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 15 — Observed Differential Change, Envelope, and Driver Validation (Scripts 32, 33, 35, 36, 37, 37b)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 36/52  Figure: secular differential water-table drift (report Fig 59)
      script: 32_differential_movement.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 32_differential_movement_2011_2025.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).
  ⚠ WARNING: Legibility: 32_differential_movement_2005_2025.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 32 — Differential water-table movement (anomaly-trend map)  [v1.4.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load inputs ──────────────────────────────────────────────
  · spring-year table: 77 wells x 21 years (2005-2025)
  ↳ excluded from trends: lake gauge only (CEH13/CEH14 blanket-included — observational metric)

──  Phase 2 · Per-well anomaly trends 2011-2025 ────────────────────────
  ▸ site-mean panel: 66 wells
  • 2011_2025 wells mapped: 74
  • 2011_2025 significant (AR p<0.05): 8/74
  • 2011_2025 bootstrap agreement: 60/74
  • 2011_2025 median drift: +0.53 mm/yr
  • 2011_2025 site-mean trend [spring_mam]: +19.66 mm/yr  AR p=0.275  (OLS p=0.275) (n.s.)
  • 2011_2025 resolvable [spring_mam]: residual sd 288.8 mm; smallest detectable slope +/-48.4 mm/yr at 80% power
  • 2011_2025 site-mean trend [annual_all_month]: +13.38 mm/yr  AR p=0.250  (OLS p=0.250) (n.s.)
  • 2011_2025 resolvable [annual_all_month]: residual sd 186.1 mm; smallest detectable slope +/-31.2 mm/yr at 80% power
  ↳ basis read downstream (Script 34, spatial chapter): spring_mam

──  Phase 3 · Render map 2011_2025 ─────────────────────────────────────
  ✓ Saved: 32_differential_movement_2011_2025.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/32_differential_movement/32_differential_movement_2011_2025.png

──  Phase 2 · Per-well anomaly trends 2005-2025 ────────────────────────
  ▸ site-mean panel: 21 wells
  • 2005_2025 wells mapped: 77
  • 2005_2025 significant (AR p<0.05): 13/77
  • 2005_2025 bootstrap agreement: 68/77
  • 2005_2025 median drift: +1.17 mm/yr
  • 2005_2025 site-mean trend [spring_mam]: -7.03 mm/yr  AR p=0.516  (OLS p=0.503) (n.s.)
  • 2005_2025 resolvable [spring_mam]: residual sd 285.7 mm; smallest detectable slope +/-29.7 mm/yr at 80% power
  • 2005_2025 site-mean trend [annual_all_month]: -13.12 mm/yr  AR p=0.232  (OLS p=0.104) (n.s.)
  • 2005_2025 resolvable [annual_all_month]: residual sd 213.3 mm; smallest detectable slope +/-28.8 mm/yr at 80% power
  ↳ basis read downstream (Script 34, spatial chapter): spring_mam

──  Phase 3 · Render map 2005_2025 ─────────────────────────────────────
  ✓ Saved: 32_differential_movement_2005_2025.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/32_differential_movement/32_differential_movement_2005_2025.png

──  Phase 4 · Write per-well CSV ───────────────────────────────────────
  ✓ Saved: /home/john/projects/NRG/outputs/32_differential_movement/32_differential_movement_per_well.csv

──  Phase 5 · Write site-mean trend CSV ────────────────────────────────
  ✓ Saved: /home/john/projects/NRG/outputs/32_differential_movement/32_site_mean_trend.csv
  ✓ Saved: /home/john/projects/NRG/outputs/32_differential_movement/32_results.txt
────────────────────────────────────────────────────────────────────────

=== 2011_2025  (2011-2025) ===
site-mean panel: 66 wells; mapped: 74; significant: 8; bootstrap agreement: 60/74
holds up (mm/yr): Ceh32 +20.48, ceh13 +18.52, ceh34 +17.21, ceh1 +16.62, ceh14 +15.14
sinks    (mm/yr): ceh22 -26.50*, ceh3 -18.88, ceh21 -15.13*, ceh11 -13.25*, ceh19 -12.20
site-mean level trend [spring_mam]: +19.66 mm/yr (AR-corrected p=0.275; OLS p=0.275; bootstrap CI [-3.13, +42.82]; panel n=66, 15 years)  — not significant
    interannual residual sd 288.8 mm; smallest slope distinguishable from zero +/-48.4 mm/yr (alpha 0.05, power 80%) — trend falls inside it, so the record does not resolve a rate of this size either way
site-mean level trend [annual_all_month]: +13.38 mm/yr (AR-corrected p=0.250; OLS p=0.250; bootstrap CI [-3.74, +30.42]; panel n=66, 15 years)  — not significant
    interannual residual sd 186.1 mm; smallest slope distinguishable from zero +/-31.2 mm/yr (alpha 0.05, power 80%) — trend falls inside it, so the record does not resolve a rate of this size either way

=== 2005_2025  (2005-2025) ===
site-mean panel: 21 wells; mapped: 77; significant: 13; bootstrap agreement: 68/77
holds up (mm/yr): Ceh32 +20.60, ceh8 +20.45*, ceh7 +17.97*, ceh34 +17.33, ceh33 +13.48
sinks    (mm/yr): ceh22 -27.53*, nw8 -27.37*, ceh3 -23.74*, nw9 -19.28*, ceh17 -16.12*
site-mean level trend [spring_mam]: -7.03 mm/yr (AR-corrected p=0.516; OLS p=0.503; bootstrap CI [-27.24, +11.86]; panel n=21, 21 years)  — not significant
    interannual residual sd 285.7 mm; smallest slope distinguishable from zero +/-29.7 mm/yr (alpha 0.05, power 80%) — trend falls inside it, so the record does not resolve a rate of this size either way
site-mean level trend [annual_all_month]: -13.12 mm/yr (AR-corrected p=0.232; OLS p=0.104; bootstrap CI [-30.04, +3.36]; panel n=25, 21 years)  — not significant
    interannual residual sd 213.3 mm; smallest slope distinguishable from zero +/-28.8 mm/yr (alpha 0.05, power 80%) — trend falls inside it, so the record does not resolve a rate of this size either way

────────────────────────────────────────────────────────────────────────
Done  (Script 32)

  ✓ done  (45.9s)

  ▶ STEP 37/52  Figure: climate-swing amplification + drought-floor (report Fig 60)
      script: 33_envelope_amplification.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 33_amplification_field.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).
  ⚠ WARNING: Legibility: 33_dry_spring_depth.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).
  ⚠ WARNING: Legibility: 33_amplification_field_recent.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).
  ⚠ WARNING: Legibility: 33_dry_spring_depth_recent.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 33 — Climate-swing amplification + dry-year spring depth  [v1.4.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load inputs ──────────────────────────────────────────────
  · canonical: dry [2011, 2012, 2019]; wet [2014, 2016, 2021, 2024]
  ↳ 2006 excluded from wet extreme (driest-in-record 2004-2005 antecedent); 2016 included (wettest-antecedent recharge season on record)

──  Phase 2 · Canonical amplification (co-temporal) + drought-floor states 
  • amplification wells: 77 (9 Tier B/C off-surface)
  ▸ C1 (Lake Edge)       amplification 0.61x  (n=7)
  ▸ C2 (Dune)            amplification 0.94x  (n=27)
  ▸ C3 (Western Residual) amplification 1.20x  (n=18)
  ▸ C4 (Main Forest)     amplification 1.72x  (n=10)
  ▸ C5 (Coastal Forest)  amplification 0.84x  (n=6)

──  Phase 3 · Robustness to extreme-year choice ────────────────────────
robustness — cluster amplification across year-set choices (naive normalisation):
  set              C1  C2  C3  C4  C5
  primary          0.57  0.89  1.11  1.51  0.79
  wet_2016_swap    0.58  0.90  1.12  1.53  0.76
  dry_no_2019      0.65  0.96  1.16  1.50  0.77
  wet_incl_2006    0.58  0.89  1.11  1.54  0.83

──  Phase 4 · Render canonical figures ─────────────────────────────────
  ✓ Saved: 33_amplification_field.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/33_envelope_amplification/33_amplification_field.png
  ✓ Saved: 33_dry_spring_depth.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/33_envelope_amplification/33_dry_spring_depth.png

──  Phase 5 · Recent-window panels (extended network) ──────────────────
  · recent: dry [2019, 2020, 2025]; wet [2021, 2024]
  • recent amplification wells: 73
  ▸ C1 (Lake Edge)       amplification 0.62x  (n=7)
  ▸ C2 (Dune)            amplification 0.83x  (n=26)
  ▸ C3 (Western Residual) amplification 1.10x  (n=22)
  ▸ C4 (Main Forest)     amplification 1.60x  (n=10)
  ▸ C5 (Coastal Forest)  amplification 0.88x  (n=8)
  ✓ Saved: 33_amplification_field_recent.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/33_envelope_amplification/33_amplification_field_recent.png
  ✓ Saved: 33_dry_spring_depth_recent.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/33_envelope_amplification/33_dry_spring_depth_recent.png

──  Phase 6 · Write outputs ────────────────────────────────────────────
  ✓ Saved: /home/john/projects/NRG/outputs/33_envelope_amplification/33_envelope_per_well.csv
  ✓ Saved: /home/john/projects/NRG/outputs/33_envelope_amplification/33_envelope_per_well_recent.csv
  ✓ Saved: /home/john/projects/NRG/outputs/33_envelope_amplification/33_results.txt
────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
Done  (Script 33)

  ✓ done  (54.1s)

  ▶ STEP 38/52  Figure+table: per-well climate-sensitivity coefficient (Paper 1; co-temporal, SSM-calibrated)
      script: 35_per_well_amplification.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 35_ssm_calibration.png smallest label ~4.8 pt as authored when placed at 160 mm (figsize 13.0×5.5 in).
  ⚠ WARNING: Legibility: 35_coefficient_markers.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 35 — Per-well climate-sensitivity coefficient (amplification metric)  [v1.2.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load inputs ──────────────────────────────────────────────
  · spring months (3, 4, 5); dry pool [2011, 2012, 2019, 2020, 2025]; wet pool [2014, 2016, 2021, 2024]

──  Phase 2 · Reference core + per-well coefficients ───────────────────
  · reference core = 54 full-dry-coverage wells; single-year σ = 119 mm; blanket include (CEH13/14 in; lake gauge out)
  • wells with a coefficient: 77
  • by tier: A=75  B=2  C=0
  • short-record (no fitted β₂): 11: ['ceh15', 'ceh22', 'ceh3', 'ceh37', 'ceh7', 'ceh8', 'fe1', 'fe2', 'fe3', 'nw8', 'nw8b']

──  Phase 3 · Validation vs matched-window amplification ───────────────
  ▸ co-temporal vs matched: n=68  r=0.978  bias=+0.073  max|dev|=0.343

──  Phase 4 · SSM calibration ──────────────────────────────────────────
  ▸ amp vs β₂: r=+0.74 (p=0.000, n=64; SSM-unreliable dropped)
  ▸ amp vs β₃: r=-0.49 (p=0.000, n=64; SSM-unreliable dropped)
  ▸ calibration drops SSM-unreliable wells (β untrustworthy): ['ceh13', 'ceh14']

──  Phase 5 · Render figures ───────────────────────────────────────────
  ✓ Saved: 35_ssm_calibration.png  (145 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/35_amplification_metric/35_ssm_calibration.png
  ✓ Saved: 35_coefficient_markers.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/35_amplification_metric/35_coefficient_markers.png

──  Phase 6 · Write outputs ────────────────────────────────────────────
  ✓ Saved: /home/john/projects/NRG/outputs/35_amplification_metric/35_per_well_amplification.csv
  ✓ Saved: /home/john/projects/NRG/outputs/35_amplification_metric/35_results.txt
────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
Done  (Script 35)

  ✓ done  (16.0s)

  ▶ STEP 39/52  Figure: absolute climate-removed per-well secular trend map (spring CWB detrended)
      script: 36_absolute_climate_trend.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 36_absolute_climate_trend_2005_2025.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).
  ⚠ WARNING: Legibility: 36_absolute_climate_trend_2011_2025.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 36 — Absolute climate-removed per-well secular trend map  [v1.4.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load inputs ──────────────────────────────────────────────
  · spring-year table: 77 wells × 21 years (2005–2025)
  · spring CWB series: 95 years (1931–2025)
  ↳ excluded: lake gauge only (CEH13/CEH14 blanket-included — observational metric)

──  Phase 2 · Per-well climate-removed trends 2005–2025 ────────────────
  ↳ coverage filter dropped 47 wells from 2005–2025 (no data before 2011 or observed span < 80% of window)
  • 2005_2025 wells mapped: 30
  • 2005_2025 significant (AR p<0.05): 0/30
  • 2005_2025 bootstrap agreement: 28/30
  • 2005_2025 median absolute trend: -0.11 mm/yr
  • C5 mean slope (gate a — must be < 0): -11.43 mm/yr
  • C2 mean slope (gate b reference): +4.79 mm/yr
  ▸ C5 gate PASSED: C5 -11.43 < 0 and ≤ C2 +4.79 mm/yr

──  Phase 3 · Render map 2005_2025 ─────────────────────────────────────
  Site mask: 3780 of 5016 grid cells inside boundary
  ✓ Saved: 36_absolute_climate_trend_2005_2025.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/36_absolute_climate_trend/36_absolute_climate_trend_2005_2025.png

──  Phase 2 · Per-well climate-removed trends 2011–2025 ────────────────
  ↳ coverage filter dropped 19 wells from 2011–2025 (no data before 2011 or observed span < 80% of window)
  • 2011_2025 wells mapped: 55
  • 2011_2025 significant (AR p<0.05): 1/55
  • 2011_2025 bootstrap agreement: 20/55
  • 2011_2025 median absolute trend: +21.18 mm/yr

──  Phase 3 · Render map 2011_2025 ─────────────────────────────────────
  Site mask: 3780 of 5016 grid cells inside boundary
  ✓ Saved: 36_absolute_climate_trend_2011_2025.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/36_absolute_climate_trend/36_absolute_climate_trend_2011_2025.png

──  Phase 2 · Per-well climate-removed trends 2006–2012 ────────────────
  • 2006_2012 wells mapped: 59
  • 2006_2012 significant (AR p<0.05): 36/59
  • 2006_2012 bootstrap agreement: 36/59
  • 2006_2012 median absolute trend: -241.41 mm/yr
  ↳ No figure path for 2006_2012 (calibration window — slopes written to CSV only)

──  Phase 2 · Per-well climate-removed trends 2015–2017 ────────────────
  ↳ coverage filter dropped 13 wells from 2015–2017 (no data before 2011 or observed span < 80% of window)
  • 2015_2017 wells mapped: 57
  • 2015_2017 significant (AR p<0.05): 56/57
  • 2015_2017 bootstrap agreement: 56/57
  • 2015_2017 median absolute trend: +1205.71 mm/yr
  ↳ No figure path for 2015_2017 (calibration window — slopes written to CSV only)

──  Phase 2 · Per-well climate-removed trends 2017–2025 ────────────────
  ↳ coverage filter dropped 18 wells from 2017–2025 (no data before 2011 or observed span < 80% of window)
  • 2017_2025 wells mapped: 56
  • 2017_2025 significant (AR p<0.05): 1/56
  • 2017_2025 bootstrap agreement: 52/56
  • 2017_2025 median absolute trend: +24.67 mm/yr
  ↳ No figure path for 2017_2025 (calibration window — slopes written to CSV only)

──  Phase 2 · Per-well climate-removed trends 2018–2025 ────────────────
  ↳ coverage filter dropped 18 wells from 2018–2025 (no data before 2011 or observed span < 80% of window)
  • 2018_2025 wells mapped: 55
  • 2018_2025 significant (AR p<0.05): 0/55
  • 2018_2025 bootstrap agreement: 52/55
  • 2018_2025 median absolute trend: +20.63 mm/yr
  ↳ No figure path for 2018_2025 (calibration window — slopes written to CSV only)

──  Phase 2 · Per-well climate-removed trends 2005–2010 ────────────────
  • 2005_2010 wells mapped: 30
  • 2005_2010 significant (AR p<0.05): 11/30
  • 2005_2010 bootstrap agreement: 17/30
  • 2005_2010 median absolute trend: -83.24 mm/yr
  ↳ No figure path for 2005_2010 (calibration window — slopes written to CSV only)

──  Phase 2 · Per-well climate-removed trends 2005–2013 ────────────────
  ↳ coverage filter dropped 8 wells from 2005–2013 (no data before 2011 or observed span < 80% of window)
  • 2005_2013 wells mapped: 59
  • 2005_2013 significant (AR p<0.05): 5/59
  • 2005_2013 bootstrap agreement: 11/59
  • 2005_2013 median absolute trend: -146.99 mm/yr
  ↳ No figure path for 2005_2013 (calibration window — slopes written to CSV only)

──  Phase 2 · Per-well climate-removed trends 2005–2016 ────────────────
  ↳ coverage filter dropped 11 wells from 2005–2016 (no data before 2011 or observed span < 80% of window)
  • 2005_2016 wells mapped: 59
  • 2005_2016 significant (AR p<0.05): 1/59
  • 2005_2016 bootstrap agreement: 56/59
  • 2005_2016 median absolute trend: -2.21 mm/yr
  ↳ No figure path for 2005_2016 (calibration window — slopes written to CSV only)

──  Phase 2 · Per-well climate-removed trends 2005–2019 ────────────────
  ↳ coverage filter dropped 18 wells from 2005–2019 (no data before 2011 or observed span < 80% of window)
  • 2005_2019 wells mapped: 59
  • 2005_2019 significant (AR p<0.05): 4/59
  • 2005_2019 bootstrap agreement: 50/59
  • 2005_2019 median absolute trend: -12.56 mm/yr
  ↳ No figure path for 2005_2019 (calibration window — slopes written to CSV only)

──  Phase 2 · Per-well climate-removed trends 2005–2022 ────────────────
  ↳ coverage filter dropped 18 wells from 2005–2022 (no data before 2011 or observed span < 80% of window)
  • 2005_2022 wells mapped: 59
  • 2005_2022 significant (AR p<0.05): 1/59
  • 2005_2022 bootstrap agreement: 49/59
  • 2005_2022 median absolute trend: +4.18 mm/yr
  ↳ No figure path for 2005_2022 (calibration window — slopes written to CSV only)

──  Phase 4 · Write per-well CSV ───────────────────────────────────────
  · identity block taken from the union of 11 period(s): 29 well(s) recovered coordinates the primary-window-only basis dropped (D-104)
  ✓ Saved: /home/john/projects/NRG/outputs/36_absolute_climate_trend/36_absolute_climate_trend_per_well.csv
  ✓ Saved: /home/john/projects/NRG/outputs/36_absolute_climate_trend/36_results.txt

────────────────────────────────────────────────────────────────────────
Done  (Script 36)

  ✓ done  (63.9s)

  ▶ STEP 40/52  Validation: predicted-vs-observed driver-change map (scatter + residual map)
      script: 37_driver_validation.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 37_predicted_vs_observed.png smallest label ~3.4 pt as authored when placed at 160 mm (figsize 18.6×6.0 in).
  ⚠ WARNING: Legibility: 37_residual_map.png smallest label ~5.2 pt as authored when placed at 160 mm (figsize 11.0×9.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 37 — Per-Driver Scale-Factor Regression  [v3.4.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load Script 36 per-well data ─────────────────────────────
  · Script 36 wells loaded: 59 total
  ·   2006_2012 (dh_corr_mm_2006_2012): 59 wells with coverage
  ·   2018_2025 (dh_corr_mm_2018_2025): 55 wells with coverage
  ·   2005_2025 (dh_corr_mm_2005_2025): 30 wells with coverage
  ↳ 7 wells have β₃ ≤ 0 or NaN (excluded from all fits)

──  Phase 2 · Load live parameters from upstream CSVs ──────────────────
  · coastal fit (live): δ₀=31.35 mm/yr, L=894 m
  · clearfell step (Path B, live): 113.1 mm

──  Phase 3 · Build spatial factors via Script 20 ──────────────────────
  ▸ importing Script 20 via importlib …
  · Script 20 loaded
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  ·   coast_unit: 0.000–0.927  clearfell: 0–113 mm  fLam=226 m
  ▸ importing Script 36 via importlib (for endpoint-group years only) …
  · Script 36 loaded

──  Phase 4 · Per-window scale-factor regressions ──────────────────────
  · 2006_2012: 59 wells with dh_corr coverage
  ↳ 2006_2012: excluded from fit — 7 β₃≤0, 12 named (40 remain)
  • 2006_2012 s_coast: 1.247
  • 2006_2012 c (intercept, mm): -592.9
  • 2006_2012 R² (n=40): 0.038
  · 2018_2025: 55 wells with dh_corr coverage
  ↳ 2018_2025: excluded from fit — 3 β₃≤0, 12 named (40 remain)
  • 2018_2025 s_coast: 0.209
  • 2018_2025 s_cf: 1.651
  • 2018_2025 c (intercept, mm): 108.4
  • 2018_2025 R² (n=40): 0.113
  · 2005_2025: 30 wells with dh_corr coverage
  ↳ 2005_2025: excluded from fit — 2 β₃≤0, 8 named (20 remain)
  • 2005_2025 s_coast: 0.507
  • 2005_2025 s_cf: -0.420
  • 2005_2025 c (intercept, mm): 92.8
  • 2005_2025 R² (n=20): 0.303

──  Phase 5 · Broadleaf covariate — robustness variant (2018_2025 only) 
  ↳ 2018_2025 WITH broadleaf covariate (robustness, NOT headline): s_coast=-0.449  s_cf=1.153  s_bl=-4.164  R²=0.365

──  Phase 6 · Independent test — implied δ₀(t) expanding-window trajectory 

──  Phase 7 · Write outputs ────────────────────────────────────────────
  ✓ Saved: /home/john/projects/NRG/outputs/37_driver_validation/37_scale_factors_by_window.csv
  ✓ Saved: /home/john/projects/NRG/outputs/37_driver_validation/37_driver_validation_per_well.csv
  ✓ Saved: 37_predicted_vs_observed.png  (102 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/37_driver_validation/37_predicted_vs_observed.png
  Site mask: 3780 of 5016 grid cells inside boundary
  ✓ Saved: 37_residual_map.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/37_driver_validation/37_residual_map.png
  ✓ Saved: 37_implied_delta0_trajectory.png  (236 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/37_driver_validation/37_implied_delta0_trajectory.png
  ✓ Saved: /home/john/projects/NRG/outputs/37_driver_validation/37_results.txt

────────────────────────────────────────────────────────────────────────
Done  (Script 37)

  ✓ done  (21.0s)

  ▶ STEP 41/52  Part B: comparative driver footing — forest · scrape · coast on common currencies (peak / area-integrated / ecological-threshold)
      script: 37b_driver_footing.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 37b — Part B — Comparative Driver Footing  [v1.3.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load live parameters ─────────────────────────────────────
  · δ₀ = 31.35 mm/yr, L = 894 m (live, Script 25 forest-free linear-capped)
  · uniform residual = -11.01 mm/yr (live, mean over 3 open-dune clusters; spread 0.14 mm/yr) — central estimate, not a resolved rate
  · clearfell step (live, 10a ANCOVA): 113.1 mm
  · scrape on-site (live, CEH36 Pure_Scraping BACI): 129.4 mm
  · scrape off-site (live, WMC3 DiD mean of 2 steps): -54.5 mm
  · drain-cone λ (live, 20_report_numbers): 226.4 m
  · per-cluster Sy (live, pipeline_scenario_params.csv): {C1=0.211, C2=0.258, C3=0.308, C4=0.252, C5=0.306}

──  Phase 2 · Load well roster and per-well summer-minima baseline ─────
  • reference-network wells: 66
  · representative Sy: coast/scrape (C3) = 0.308; forest (C4 n=9 + C5 n=5, weighted) = 0.271; climate (C3, per sign-off) = 0.308
  • wells with summer-minima baseline: 66/66

──  Phase 3 · Build spatial fields (Script 20 v1.32.0 builders, via importlib) 
  ▸ importing Script 20 …
  Site mask: 3797 of 5159 grid cells inside boundary
  · grid: 77×67 at 50 m, 3797 cells inside site mask (949.2 ha)
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m
  coastline_hwm.geojson loaded (type=LineString, length=15212 m)
  · scrape registry: 8 cuts loaded

──  Phase 4 · Currency 1 — peak local head change ──────────────────────
  •   coast_erosion peak: -627.0 mm
  •   slr peak: +20.0 mm
  •   clearfell peak: +113.1 mm
  •   broadleaf peak: -56.2 mm
  •   climate peak: -220.2 mm
  •   scrape_onsite peak: +129.4 mm
  •   scrape_offsite peak: -54.5 mm

──  Phase 5 · Currency 2 — area-integrated change (mm·ha, m³) ──────────
  •   coast_erosion volume: -247329.4 m³
  •   slr volume: +8650.6 m³
  •   clearfell volume: +16221.4 m³
  •   broadleaf volume: -10339.8 m³
  •   scrape_offsite volume: -66853.4 m³
  •   climate volume: -644390.9 m³
  •   scrape_onsite volume: +1890.0 m³

──  Phase 6 · Currency 3 — ecological threshold crossings (Curreli) ────
  Coastal fit (live, Script 25 forest-free linear-capped): δ₀=31.35 mm/yr, L=894 m

──  Phase 7 · Assemble comparison table and write outputs ──────────────
  ✓ Saved: /home/john/projects/NRG/outputs/37b_driver_footing/37b_driver_footing.csv
  ✓ Saved: 37b_driver_footing.png  (262 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/37b_driver_footing/37b_driver_footing.png
  ✓ Saved: /home/john/projects/NRG/outputs/37b_driver_footing/37b_results.txt

────────────────────────────────────────────────────────────────────────
Done  (Script 37b)

  ✓ done  (9.8s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 16 — Window Sensitivity, Coastal Transect, and Supplementary Cluster Diagnostics (Scripts 34, 38 default; 24b, 31, 31b opt-in)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 42/52  Cluster-stratified residual climatology (supplementary diagnostic)
      script: 24b_residual_climatology.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 24b_04_cluster_climatology.png smallest label ~4.3 pt as authored when placed at 160 mm (figsize 10.2×7.2 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 24b — Cluster-Stratified Residual Climatology  [v1.5.0]
════════════════════════════════════════════════════════════════════════
====================================================================================
Script 24b (DIAGNOSTIC) — Cluster-stratified residual climatology
  [not a pipeline step; not invoked by run_analysis.py]
====================================================================================
 -> Loaded residual matrix: 249 months × 63 wells (from Script 22).
 -> Per-well contrasts: 62 wells → 24b_03_per_well_winter_minus_summer.csv
 -> Cluster climatology: 60 rows → 24b_01_cluster_climatology.csv
  ▸ Cluster contrasts → 24b_02_peak_winter_minus_summer.csv
  ✓ Saved: 24b_04_cluster_climatology.png  (185 dpi)
  ▸ Figure (3×2 PNG) → 24b_04_cluster_climatology.png
  ▸ Interpretation → 24b_05_interpretation.txt
====================================================================================
Script 24b diagnostic complete.
  ✓ done  (2.5s)

  ▶ STEP 43/52  Independent k=5 partition validation (supplementary diagnostic)
      script: 31_cluster_validation.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 31_cluster_validation_panel.png smallest label ~4.0 pt as authored when placed at 160 mm (figsize 14.0×11.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 31 — Independent validation of the k=5 partition  [v1.4.1]
════════════════════════════════════════════════════════════════════════
  · realised partition k=5 matches the requested target (k=5); forest clusters [4, 5]

──  Phase 1 · Tier 1 external — spatial coherence, forest recovery ─────

──  Phase 2 · Tier 2 metric-independent — magnitude descriptors ────────

──  Phase 3 · Tier 3 convergent — SSM betas, WTF Sy, LCSC ──────────────

──  Phase 4 · Tier 4 robustness — ARI of alternative linkage/distance vs canonical 

──  Phase 5 · Write outputs + panel figure ─────────────────────────────
  ✓ Saved: /home/john/projects/NRG/outputs/31_cluster_validation/31_validation_summary.csv
  ✓ Saved: /home/john/projects/NRG/outputs/31_cluster_validation/31_method_robustness_ari.csv
  ✓ Saved: /home/john/projects/NRG/outputs/31_cluster_validation/31_forest_confusion.csv
  ✓ Saved: /home/john/projects/NRG/outputs/31_cluster_validation/31_forest_borderline.csv
  ✓ Saved: 31_cluster_validation_panel.png  (135 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/31_cluster_validation/31_cluster_validation_panel.png

──  Phase 6 · Summary ──────────────────────────────────────────────────
  · Tier 1-3 validation summary:
          tier                            test                        descriptor statistic_name  statistic  p_value       independence
    1 external      within-cluster compactness               geographic distance  mean_within_m    620.900   0.0001           external
    1 external                 join-count (BB)            same-cluster adjacency              z     18.810   0.0001           external
    1 external        Moran's I (C1 indicator)               C1 spatial autocorr       morans_I      0.452   0.0001           external
    1 external        Moran's I (C2 indicator)               C2 spatial autocorr       morans_I      0.742   0.0001           external
    1 external        Moran's I (C3 indicator)               C3 spatial autocorr       morans_I      0.637   0.0001           external
    1 external        Moran's I (C4 indicator)               C4 spatial autocorr       morans_I      0.602   0.0001           external
    1 external        Moran's I (C5 indicator)               C5 spatial autocorr       morans_I      0.497   0.0001           external
    1 external                 ANOVA / Kruskal                 distance to coast           eta2      0.629   0.0000           external
    1 external                 ANOVA / Kruskal                  ground elevation           eta2      0.209   0.0059           external
    1 external       forest-footprint recovery canopy polygon vs forest clusters    cohen_kappa      0.914      NaN           external
    1 external forest recovery (edge excluded) canopy polygon vs forest clusters    cohen_kappa      0.955      NaN           external
2 metric-indep                           ANOVA               mean depth to water           eta2      0.521   0.0000 metric-independent
2 metric-indep                           ANOVA                seasonal amplitude           eta2      0.350   0.0000 metric-independent
2 metric-indep                           ANOVA                    summer minimum           eta2      0.482   0.0000 metric-independent
2 metric-indep                           ANOVA                         dry depth           eta2      0.356   0.0433 metric-independent
  3 convergent                           ANOVA                         SSM beta1           eta2      0.657   0.0000         convergent
  3 convergent                           ANOVA                         SSM beta2           eta2      0.638   0.0000         convergent
  3 convergent                           ANOVA                         SSM beta3           eta2      0.670   0.0000         convergent
  3 convergent                           ANOVA                            WTF Sy           eta2      0.583   0.0000         convergent
  3 convergent                           ANOVA                              LCSC           eta2      0.718   0.0000         convergent
  · Tier 4 method robustness (ARI vs canonical):
distance  linkage         note  k  n_wells  ARI_vs_canonical
 Pearson     ward reproduction  5       66             1.000
 Pearson  average  alt linkage  5       66             0.689
 Pearson complete  alt linkage  5       66             0.385
Spearman     ward alt distance  5       66             0.548
     DTW     ward alt distance  5       66             0.520
  • forest recovery: kappa(all)=0.914  kappa(edge excluded)=0.955
  · confusion (rows=in_forest_poly, cols=in_forest_cluster):
in_forest_cluster  False  True 
in_forest_poly                 
False                 50      0
True                   2     14
  · borderline wells (|dist to forest edge| < 50 m):
 well  Cluster  signed_dist_m  in_forest_cluster
 ceh1        3          -49.1              False
  nw2        3          -46.9              False
ceh36        3          -45.6              False
 nw11        3           34.3              False
  ↳ inside forest polygon but NOT in a forest cluster (kappa misses):
well  Cluster  signed_dist_m
nw11        3           34.3
wmc3        3           50.4
────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
Done  (Script 31)

  ✓ done  (11.1s)

  ▶ STEP 44/52  Cluster separation vs recoverability (supplementary diagnostic)
      script: 31b_separation_vs_recoverability.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 31b_separation_vs_recoverability.png smallest label ~5.4 pt as authored when placed at 160 mm (figsize 11.0×7.0 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 31b — Separation (eta^2) vs recoverability (ARI) per variable  [v1.3.0]
════════════════════════════════════════════════════════════════════════
  · realised partition k=5 matches the requested target (k=5)

──  Phase 1 · Load descriptors ─────────────────────────────────────────

──  Phase 2 · Compute separation (eta^2) and recoverability (ARI) ──────
  ✓ Saved: /home/john/projects/NRG/outputs/31_cluster_validation/31b_separation_vs_recoverability.csv

──  Phase 3 · Render figure ────────────────────────────────────────────
  ✓ Saved: 31b_separation_vs_recoverability.png  (172 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/31_cluster_validation/31b_separation_vs_recoverability.png
                        descriptor        column  binary  eta2_separation  ari_recoverability
                  Ground elevation ground_elev_m   False            0.209               0.018
                Seasonal amplitude     amplitude   False            0.350               0.072
                         Dry depth     dry_depth   False            0.356               0.133
                    Summer minimum    summer_min   False            0.482               0.159
               Mean depth to water    mean_depth   False            0.521               0.230
Distance to coast (Caernarfon Bay)  dist_coast_m   False            0.629               0.258
                           Easting       Easting   False            0.833               0.336
              Forest (canopy flag)        forest    True            0.851               0.246
────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
Done  (Script 31b)

  ✓ done  (2.9s)

  ▶ STEP 45/52  MSL5 two-window sensitivity demonstration figure (§5.7.5)
      script: 34_window_sensitivity.py
  ──────────────────────────────────────────────────────────────────
  ⚠ WARNING: Legibility: 34_window_sensitivity.png smallest label ~3.3 pt as authored when placed at 160 mm (figsize 15.5×6.6 in).

════════════════════════════════════════════════════════════════════════
SCRIPT 34 — MSL5 two-window comparison sensitivity (§5.7.5)  [v0.6.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load committed annual MSL ────────────────────────────────
  · excluded ['ceh13', 'ceh14']; 87 wells; 17 five-year windows (2009-2025)

──  Phase 2 · Window rainfall context ──────────────────────────────────
  · committed long-term mean annual rainfall 858 mm; window % shown relative to this

──  Phase 3 · Validate against committed anchor ────────────────────────
  • anchor 2017->2023: -96.5 mm, n=60 (committed -96.8, n=59)

──  Phase 4 · All admissible window pairs (fixed common panel; wet-2024 retained) 
  • admissible pairs: 66 (common panel >= 40)
  • site-mean change envelope: -136.2 to +221.2 mm  (-0.14 to +0.22 m)
  • sign split: 19 negative / 47 positive
  ↳ the -96 mm 2017->2023 headline is one point in this wide, sign-changing envelope; the +ve extreme 2015->2024 (+221 mm) is a wet-2024 'wrong pair'

──  Phase 5 · Write outputs + figure ───────────────────────────────────
  • Script 32 secular trend (canonical): -7.03 mm/yr  AR p=0.52  [2005_2025, from 32_site_mean_trend.csv]
  ✓ Saved: /home/john/projects/NRG/outputs/34_window_sensitivity/34_window_matrix.csv
  ✓ Saved: /home/john/projects/NRG/outputs/34_window_sensitivity/34_results.txt
  ✓ Saved: 34_window_sensitivity.png  (122 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/34_window_sensitivity/34_window_sensitivity.png
────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────
Done  (Script 34)

  ✓ done  (2.1s)

  ▶ STEP 46/52  Coast-to-inland MAM transect — observational delta_0 diagnostic (§5.7)
      script: 38_coastal_transect.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 38 — Coast-to-inland MAM transect (observational delta_0 test)  [v1.6.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load inputs ──────────────────────────────────────────────
  · spring-year table: 78 wells x 21 years (2005–2025)
  ·   CEH22   dist=   0.0 m
  ·   NW5     dist= 336.4 m
  ·   CEH40   dist= 842.4 m
  ·   CEH41   dist= 971.7 m
  ·   NW4     dist=1347.9 m

──  Phase 2 · Compute window ───────────────────────────────────────────
  • window start (CEH22 first-valid MAM; CEH41 no longer gates this): 2010
  • window end (last MAM before Oct-2023, capped by data): 2023
  • actual n of MAM points in window: 14

──  Phase 3 · Fit AR-corrected trend on Delta_coast_inland(t) ──────────
  • Delta_coast_inland trend: -28.16 mm/yr (AR p=0.000, OLS p=0.000)
  • bootstrap 95% CI: [-34.23, -21.98] mm/yr
  • Script 25 delta_0 (forest_free, linear_capped): -31.35 mm/yr

──  Phase 4 · Render figures ───────────────────────────────────────────
  ✓ Saved: 38_transect_profile.jpg  (230 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/38_coastal_transect/38_transect_profile.jpg
  ✓ Saved: 38_coast_inland_difference.jpg  (236 dpi)
  ✓ Saved: /home/john/projects/NRG/outputs/38_coastal_transect/38_coast_inland_difference.jpg

──  Phase 5 · Write outputs ────────────────────────────────────────────
  ✓ Saved: /home/john/projects/NRG/outputs/38_coastal_transect/38_transect.csv  (14 years)
  ✓ Saved: /home/john/projects/NRG/outputs/38_coastal_transect/38_results.txt
  ✓ Saved: /home/john/projects/NRG/outputs/38_coastal_transect/38_report_numbers.csv  (10 value(s))

────────────────────────────────────────────────────────────────────────
Done  (Script 38)

  ✓ done  (1.8s)

  ▶ STEP 47/52  SSM hindcast against the 1989–96 CCW record — out-of-sample validation (§5.7.8)
      script: 39_ccw_hindcast.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 39 — SSM hindcast against the 1989–96 CCW record  [v1.3.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Load inputs ──────────────────────────────────────────────
  · CCW record: 1066 readings, 13 codes, 1989-05 to 1996-04
  · climate forcing available from 1930-12

──  Phase 2 · Admit codes ──────────────────────────────────────────────
  ↳ 1A excluded: no committed coefficients
  ↳ 1B excluded: censored in 63 of 82 months
  ▸ 1C -> nw11
  ▸ 1D -> nw13
  ▸ 1E -> nw3
  ▸ 1F -> nw4
  ↳ 2A excluded: mapping unidentified
  ▸ 2B -> nw9
  ▸ 2C -> wmc3
  ↳ 2D excluded: no committed coefficients
  ▸ 2E -> nw6
  ▸ 2F -> nw5
  ▸ 2G -> wmc2
  • codes admitted: 9 of 13

──  Phase 3 · Hindcast ─────────────────────────────────────────────────
  • nw11 (1C): NSE -3.032  r +0.660  NSE(level removed) -0.109  bias +0.461 m  epoch shift -0.835 m  n 82
  • nw13 (1D): NSE -0.449  r +0.750  NSE(level removed) +0.409  bias +0.302 m  epoch shift -0.693 m  n 82
  • nw3 (1E): NSE +0.732  r +0.907  NSE(level removed) +0.803  bias -0.085 m  epoch shift -0.416 m  n 82
  • nw4 (1F): NSE +0.326  r +0.912  NSE(level removed) +0.832  bias -0.211 m  epoch shift -0.259 m  n 82
  • nw9 (2B): NSE -0.674  r +0.826  NSE(level removed) +0.581  bias +0.229 m  epoch shift -0.683 m  n 82
  • wmc3 (2C): NSE -0.713  r +0.689  NSE(level removed) +0.346  bias +0.238 m  epoch shift -0.582 m  n 67
  • nw6 (2E): NSE +0.607  r +0.859  NSE(level removed) +0.718  bias +0.090 m  epoch shift -0.583 m  n 82
  • nw5 (2F): NSE +0.206  r +0.945  NSE(level removed) +0.874  bias -0.244 m  epoch shift -0.248 m  n 82
  • wmc2 (2G): NSE -0.013  r +0.934  NSE(level removed) +0.854  bias -0.263 m  epoch shift -0.132 m  n 82

──  Phase 4 · Write outputs ────────────────────────────────────────────
  ✓ Saved: 39_01_hindcast_per_well.csv
  ✓ Saved: 39_02_hindcast_series.csv
  ✓ Saved: 39_03_beta1_sensitivity.csv
  ✓ Saved: 39_04_hindcast.png  (210 dpi)
  ✓ Saved: 39_04_hindcast.png

──  Phase 5 · Full-record hindcast ─────────────────────────────────────
  ↳ ceh13 not in panel: under canopy
  ↳ ceh14 not in panel: under canopy
  ↳ ceh16 not in panel: under canopy
  ↳ ceh17 not in panel: under canopy
  ↳ ceh19 not in panel: under canopy
  ↳ ceh2 not in panel: under canopy
  ↳ ceh20 not in panel: under canopy
  ↳ ceh30 not in panel: under canopy
  ↳ ceh31 not in panel: under canopy
  ↳ ceh32 not in panel: under canopy
  ↳ ceh33 not in panel: under canopy
  ↳ ceh34 not in panel: under canopy
  ↳ nw10 not in panel: under canopy
  ↳ nw11 not in panel: under canopy
  ↳ nw9 not in panel: under canopy
  ↳ wmc3 not in panel: under canopy
  • panel wells: 50 of 66 candidates
  ✓ Saved: 39_05_full_hindcast_site.csv
  ✓ Saved: 39_06_full_hindcast_decadal.csv
  ✓ Saved: 39_07_full_hindcast.png  (210 dpi)
  ✓ Saved: 39_07_full_hindcast.png
  ✓ Saved: 39_results.txt

────────────────────────────────────────────────────────────────────────
Done

  ✓ done  (4.4s)

  ▶ STEP 48/52  Shoreline retreat from the digitised coastline epochs — signed shore-normal displacement; WITHHOLDS its own headline until the gate passes (D-085)
      script: 40_shoreline_retreat.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 40 — Shoreline retreat from the digitised coastline epochs  [v1.6.3]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading coastline epochs ─────────────────────────────────
  · local projection origin 53.1385 N, -4.3753 E
  · inland reference (site-boundary centroid) at 723, 988 m local
  · coast1899 placemarks resolved by measurement, not index order: dune edge = placemark 1 (median 113.0 m to 2020), high water = placemark 0 (201.0 m)

──  Phase 2 · Common frontage and normal orientation ───────────────────
  · common northing band -830 to 757 m local (span 1587 m) — restricted by EXTENT, not hit-success
  · seaward normals 180–227 deg across 152 normals; 4 degenerate (2.6%) excluded

──  Phase 3 · Signed shore-normal displacement ─────────────────────────
  ▸ 1899→2006: median 68.390 m over 107.0 yr = 0.639 m/yr  (n=120, progradation 0, nearest 68.236 m)
  ▸ 2006→2017: median 20.306 m over 11.2 yr = 1.809 m/yr  (n=131, progradation 23, nearest 20.204 m)
  ▸ 2017→2021: median 9.376 m over 4.0 yr = 2.326 m/yr  (n=135, progradation 14, nearest 9.367 m)
  ▸ 2021→2026: median 10.141 m over 5.0 yr = 2.033 m/yr  (n=131, progradation 29, nearest 10.126 m)
  ▸ 2006→2026: median 46.980 m over 20.2 yr = 2.321 m/yr  (n=128, progradation 0, nearest 46.369 m)
  ▸ 1899→2026: median 126.923 m over 127.2 yr = 0.997 m/yr  (n=118, progradation 0, nearest 126.227 m)
  ·     on the shared modern frontage: 2006→2017 20.306 m = 1.809 m/yr (n=131)
  ·     on the shared modern frontage: 2017→2021 9.556 m = 2.371 m/yr (n=131)
  ·     on the shared modern frontage: 2021→2026 10.691 m = 2.143 m/yr (n=128)
  ·     on the shared modern frontage: 2006→2026 46.980 m = 2.321 m/yr (n=128)

──  Phase 4 · Diagnostics ──────────────────────────────────────────────
  · chord-sagitta bound 3.829 m (measured, not densified away)
  · repeat-tracing control: |offset| median 2.341 m, p95 5.532 m across 130 normals, 0 shared vertices
  · period match: delta_0 2006-01–2026-02 against retreat 2006–2026, overlap 99%
  · matched sensitivity 13.566 mm per m of retreat -> h0 = 81.39 mm for a 6 m event (committed construction gives 22.66 mm)

──  Phase 5 · Storm pair — displacement, not rate ──────────────────────
  ▸ 2019/20 winter storm sequence: median 8.948 m over 202 days (n=139, progradation 0, min 0.762 m)
  ·     against a repeat-tracing control p95 of 5.532 m and a between-storm expectation of 1.283 m over the same 202 days at the 2006-2026 rate (2.3207 m/yr over 20.24 yr)

──  Phase 6 · Anchors ──────────────────────────────────────────────────
  · D-060 anchor: 0.645 m/yr (from 69.021 m over 107 yr) against published 0.65 m/yr (0.8% — within 10%)
  · synthetic anchor: a 37.5 m translation measures as 36.969 m (error 0.531 m — within 1.0 m)

──  Phase 7 · Gate ─────────────────────────────────────────────────────
  • headline: EMITTED — all three gate tests pass

──  Phase 8 · Writing outputs ──────────────────────────────────────────
  ✓ Saved: 40_01_epoch_series.csv  (12 intervals)
  ✓ Saved: 40_02_normals.csv  (156 normals)
  ✓ Saved: 40_03_control.csv  (1 pairs)
  ✓ Saved: 40_04_generalisation.csv  (bound 3.829 m)
  ✓ Saved: 40_05_dtm_profile.csv  (5 rows)
  ✓ Saved: 40_06_coastal_sensitivity.csv  (3 bases)
  ✓ Saved: 40_07_storm_pair.csv  (1 pair(s), no rate emitted)
  ✓ Saved: 40_report_numbers.csv  (12 value(s))
  ✓ Saved: 40_01_alongshore_profile.png  (210 dpi)
  ✓ Saved: 40_01_alongshore_profile.png

────────────────────────────────────────────────────────────────────────
Done  (Script 40)

  ✓ done  (1.7s)

  ▶ STEP 49/52  Canopy and forest-cover texture index from the dated aerial series — registration fitted from the dipwell placemarks; WITHHOLDS a value whose frame is unregistered. Skips when the imagery is absent, which is its normal state in a clone (D-081)
      script: 41_canopy_cover.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 41 — Canopy and forest cover from the dated aerial series  [v2.2.1]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Geometry and registration ────────────────────────────────
  · control region forest_in_view: 11.48 ha of managed block subtracted (NOT the reference's buffer collar — with the collar the control becomes the reference and reads 1.000 exactly, which is not a control)
  ·   (the un-subtracted control stepped 1.010 -> 0.954 across the 2017 clearfell; a control must not contain what it controls for)
  · affine from broadleaf_restock: 1.35 m/px E-W, 1.59 m/px N-S
  ·   the 15% anisotropy is the perspective; these are captures, not orthophotos
  · frame 1920 x 1080; usable window rows 90-1000, cols 215-1845 (fractions of the frame, not pixels)
  · 5 constellation group(s) across 29 frame(s):
  ·     group 0:  51 tips, 11 frame(s) — aerial 1-1-2006.png +10 more
  ·     group 1:  96 tips, 2 frame(s) — site1-1-2006m.png +1 more
  ·     group 2:  75 tips, 2 frame(s) — seabed1-1-2006.png +1 more
  ·     group 3: 106 tips, 13 frame(s) — site 20-4-2009m.png +12 more
  ·     group 4:  40 tips, 1 frame(s) — aerial31-3-2026.png
  ·     group 0: 30 points, median 5.73 m, p95 16.02 m, GSD 1.26 m/px — base control affine
  ·     group 1: 86 points, median 4.42 m, p95 19.73 m, GSD 2.95 m/px — well-constellation vote
  ·     group 2: 69 points, median 2.70 m, p95 12.99 m, GSD 4.77 m/px — well-constellation vote
  ·     group 3: 87 points, median 3.93 m, p95 19.03 m, GSD 2.88 m/px — chained from group 1 (+2,-12) px, 20 tips coincide
  ·     group 4: 32 points, median 5.36 m, p95 19.17 m, GSD 1.38 m/px — own control outline
  ·   region broadleaf_restock      31706 px in view
  ·   region clearfell              28575 px in view
  ·   region felling_experiment     25581 px in view
  ·   region forest_in_view        879182 px in view
  ·   reference conifer       839363 px
  ·   reference open          489261 px

──  Phase 2 · Texture index per frame ──────────────────────────────────
  ✓ Saved: 41_03_registration.csv
  ✓ Saved: 41_01_canopy_index.csv

──  Phase 3 · Change between consecutive imagery dates, on the ground ──
  · change grid 1766 x 2380 at 2 m; frames are differenced here, never pixel-to-pixel
  ✓ Saved: 41_02_change_events.csv

──  Phase 4 · Figure and report numbers ────────────────────────────────
  ✓ Saved: 41_04_canopy_series.png  (210 dpi)
  ✓ Saved: 41_04_canopy_series.png
  ✓ Saved: 41_report_numbers.csv
  ▸ 116 region-frame values, 68 withheld
  · usable values by (viewpoint, leaf state): {('aerial', 'emerging'): 24, ('aerial', 'full_leaf'): 16, ('aerial', 'leaf_off'): 4, ('aerial', 'senescing'): 4}
  · the index is comparable WITHIN a viewpoint and within a leaf state, and between neither: the same region on the same day reads 1.045 from the aerial frame and -0.113 from the site frame
  · the index is a texture position, not a canopy fraction, and it is NOT bounded above by 1: it sees canopy and understorey together, so a young open broadleaf block can exceed a closed conifer stand
  · no growth number is emitted — before 2012 there is no full-leaf frame, so growth and phenology are not separable on this record
  ✓ done  (41.0s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PHASE 17 — Synthesis Figures and Greyscale Conversion (Scripts 09f, 09g, 27)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶ STEP 50/52  Figure: management-interventions + coastal-retreat spatial reach (§5.8; two-pass, reads Scripts 20/25/09d/10a)
      script: 09f_management_effects.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 09f — MANAGEMENT EFFECTS — SPATIAL REACH  [v1.9.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading live values ──────────────────────────────────────
  · λ = 226.4 m   forest H0 = 150 mm
  · scrape edge head (measured, live) = 129.4 mm
  · clearfell recovery = 113.1 mm
  · coast-edge δ₀ = -31.4 mm/yr (CI -35.2, -27.5), L = 894 m
  · coastal 6 m storm edge = 81.1 mm; 5-year (5×δ₀) edge = 156.8 mm
  · WMC3 measured off-cut drawdown = -55.2 mm at 262 m
  · forest t½ (C4–C5) = 38–15 mo; C3 t½ = 12 mo

──  Phase 2 · Plotting reach + timescale figure (stacked) ──────────────
  ✓ Saved: 09f_management_effects.png  (201 dpi)
  ✓ Saved: 09f_management_effects.png
  ✓ Saved: 09f_01_reach_profile.csv

Done.
  ✓ done  (2.3s)

  ▶ STEP 51/52  Figure: mechanism grid + coastal reach (§5.8 conceptual; display only, reads 09f/10m/10a)
      script: 09g_mechanism_diagrams.py
  ──────────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════════════════
SCRIPT 09g — MECHANISM DIAGRAMS — SCHEMATIC GRID + COASTAL REACH  [v1.7.0]
════════════════════════════════════════════════════════════════════════

──  Phase 1 · Loading committed amplitudes ─────────────────────────────
  · edge amplitudes sourced from committed 09f (09f_01_reach_profile.csv row 0)
  · scrape_offslack = -55.2 mm (measured WMC3 BACI, 10m)
  · clearfell steps: +0.113 m annual (p=0.00); +0.050 m summer (n.s.)
  · forest suppression 15.0 px (-150 mm on the shared scale)
  ·   inland slack @ 459: no-tree 190.6 (wet)  forest 205.6 (DRY)  felled 190.6 (wet again)
  · scrape pool level 211.8 (+3.5 px vs seaward slack — measured +129 mm rise, drawn capped in-slack); span 201–343
  ·   off-cut drawdown (measured WMC3 -55 mm = 5.5 px, localised near-field); inland slack after 196.0 (still wet, -1.0 vs floor 197)
  · reach (committed 09f (09f_01_reach_profile.csv)): coastal shore -627 mm, tapering to zero at the fitted reach L = 894 m (δ₀ -31.35 mm/yr); no far-field term drawn, no crossing computed
  · drivers drawn: three (scrape, clearfell, coastal) — the grid title counts this register
  ·   clearance [storm]:  +0.00 px below the drawn surface,  +0.00 px below the undisturbed table
  ·   clearance [  5yr]:  +0.00 px below the drawn surface,  +0.00 px below the undisturbed table
  ·   clearance [ 20yr]:  +0.00 px below the drawn surface,  +0.00 px below the undisturbed table
  · sub-surface check: OK, minimum clearance +0.00 px
  ·   d=    0 m  coastal_dd= 627.0 mm
  ·   d=  447 m  coastal_dd= 313.6 mm
  ·   d=  894 m  coastal_dd=   0.2 mm
  · reach seam @330 m [storm]: near 177.11 px  inland 177.11 px  Δ=+0.00 px  OK (dd=51.1 mm; storm/5-yr continue to 900 m)
  · reach seam @330 m [  5yr]: near 181.89 px  inland 181.89 px  Δ=+0.00 px  OK (dd=98.9 mm; storm/5-yr continue to 900 m)
  · reach seam @330 m [ 20yr]: near 211.56 px  inland 211.56 px  Δ=+0.00 px  OK (dd=395.6 mm; storm/5-yr continue to 900 m)

──  Phase 2 · Compositing figures ──────────────────────────────────────
  ✓ Saved: 09g_mechanism_grid.svg + 09g_mechanism_grid.png
  ✓ Saved: 09g_coastal_vs_climate_reach.svg + 09g_coastal_vs_climate_reach.png

──  Phase 3 · Rendering lay public-summary figures ─────────────────────
  ✓ Saved: 09g_mechanism_lay_management.png
  ✓ Saved: 09g_mechanism_lay_drivers.png

Done.
  ✓ done  (1.2s)

══════════════════════════════════════════════════════════════════════
  PIPELINE COMPLETE  ·  steps 1–51 written to outputs/
══════════════════════════════════════════════════════════════════════
  ℹ greyscale (step 52) runs separately (menu option 6 / --greyscale)
  ℹ pipeline_manifest.json written to /home/john/projects/NRG/outputs/pipeline_manifest.json
  ℹ total run time: 15.7 min

  ℹ Console output saved to: y
