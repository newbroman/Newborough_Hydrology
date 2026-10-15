<!-- GENERATED MIRROR of docs/papers/paper_1/PAPER1_SI_methods_v1_31.odt — do not edit. source-sha256=cb1bf276c93753f1 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

# Supporting Information

## Hollingham (2026a), Paper 1 --- *A parameter-sparse state-space framework for characterizing coastal dune-aquifer architecture from manual dipwell records*

[]{#anchor}This Supporting Information document gives the methodological detail behind the analyses reported in the main text. It is self-contained. Every parameter, equation and design choice that supports a result in the manuscript is set out here. Section numbers in the manuscript refer back to the headed sections here (S1--S15).

The pipeline and outputs are archived in full (Section S14). The headline numerical values used in the manuscript are reproduced live from the pipeline output CSVs cited at the foot of each section. They are unchanged at the time of submission.

### S12.6 Seasonal robustness (spring mean)

The gradient regression above uses the annual summer minimum (Jun--Sep) as the per-well response. It was repeated with a second per-well metric, the annual spring mean (Mar--May), through the identical code path (compute_per_well_slopes(metric=...), strict 3-of-3 monthly completeness). The panel fit and the coastal-retreat gradient are all-season and metric-independent: the same forest-free linear-capped fit is applied to both metrics. Any spring--summer difference in the decomposition is therefore attributable to the response metric, not to a refitted gradient. That is a property of the procedure. It is not evidence that the gradient is season-invariant, and the test below shows that it is not.

The gradient is itself seasonal. A full-panel season × δ(d)·t interaction (10,909 observations, one model) fits δ(d)·t·(1 + γ·S), with S = 1 in Mar--May. For the linear-capped form it returns γ = +0.309 ± 0.060 (t = 5.16, p \< 0.001); for the exponential form it returns +0.304 ± 0.059 (t = 5.15, p \< 0.001). Both forms reject season-independence, and both put γ above zero. The coastal-retreat drift rate is about 31 % steeper in Mar--May than over the rest of the year. The estimate is significant, has the same sign and is of compatible magnitude under both decay forms. This indicates a seasonal modulation of the gradient itself rather than an artefact of the assumed functional form.

The MAM-only refit of the panel (a sensitivity block in 25_01_panel_fit_parameters.csv) points the same way. It loses power, as expected: the fitted δ₀ SE roughly doubles, 1.97 to 3.71 mm yr⁻¹. But it returns a steeper spring coast-edge anomaly than the all-season fit (δ₀ −34.06 against −31.28 mm yr⁻¹), a change of about 9 % in the same direction as γ. At the reference distance the two fits are closer still, at −25.87 against −26.38 mm yr⁻¹.

What remains year-round is the boundary effect itself. C5 Coastal Forest, the out-of-sample sentinel of S12.5, declines in both seasons (summer −32.0, spring −23.9 mm yr⁻¹, balanced annual means). So γ modulates the drift rate rather than switching it off outside spring. The all-season gradient is therefore a season-averaged quantity, not a season-independent one. Applying it unchanged to a spring metric understates the spring coastal contribution: the ≈ 71 % of C5's spring decline that it attributes to coastal retreat is a lower bound. Full seasonal results are in the report's Supplementary Material, Note S8.

### S12.7 Single-well leverage of δ₀

The forest-free panel has few wells inside 300 m of the shore, so the shoreline amplitude δ₀ can lean on individual near-shore wells. To test this, Script 25 refits the headline specification (forest-free, linear-capped, all-season, 61 wells) once per well, with that well withheld. The starting values, bounds and climate covariate are held fixed. One row per well is written to 25_16_delta0_leave_one_out.csv. A withhold-nothing control must reproduce the headline fit exactly.

The largest shift is CEH3 (176 m). Withholding it moves δ₀ from −31.28 to −28.15 mm yr⁻¹ (+3.1) and moves the 150 m rate by +2.4 mm yr⁻¹. The next-largest shifts are WMC2 (458 m, −1.7), CEH22 (147 m, −1.4), D25 (894 m, +1.4) and CEH39 (771 m, +1.0). No other well moves δ₀ by more than 1 mm yr⁻¹.

The standard error of δ₀ estimated from the 61 refits is 4.8 mm yr⁻¹. This is the delete-one estimate, √((n−1)/n·Σ(δ₀,ᵢ − δ̄₀)²). The fitted standard error is 1.97, computed from the residuals of about 11,000 monthly rows treated as independent. The two answer different questions. The fitted value is the precision of the model given its rows. The refit value is the precision given that the wells are the units of independence.

The manuscript quotes the well basis. Each of the following is the delete-one estimate over the 61 refits (25_report_numbers.csv, *\_well_basis\_*): δ₀ = −31.28 ± 4.79 mm yr⁻¹ (95% CI −40.66 to −21.89), the 150 m rate −26.38 ± 3.49 mm yr⁻¹ (95% CI −33.23 to −19.53) and L_cg 902 ± 144 m (620 to 1185). The fitted standard errors remain in 25_01_panel_fit_parameters.csv as the nominal precision of the model. They are not quoted as uncertainties. The leverage of CEH3 lies inside the well-basis error.

## Contents

  --------------------------------------------------------------- -----------------
  S1. Field protocol, data preparation, and date semantics        2
  S2. Constants and configuration                                 4
  S3. Behavioural clustering and the *k* = 5 partition            5
  S4. Pearson affinity audit and spatial confidence               7
  S5. The state-space model --- displacement formulation          7
  S6. SSM regression: per-well and cluster-mean fits, with LCSC   10
  S7. Spatial interpolation of SSM coefficients                   12
  S8. Residual-field diagnostics                                  13
  S9. Water-balance decomposition                                 14
  S10. Water-table-fluctuation specific yield                     15
  S11. Mean water-table surface and the Darcy flow field          17
  S12. Coastal-retreat gradient regression                        18
  S13. Forest-interception drawdown reach (Figure 18)             20
  S14. Software, parameters and reproducibility                   21
  S15. Supplementary references                                   22[]{#contents}
  --------------------------------------------------------------- -----------------

## S1. Field protocol, data preparation, and date semantics

The author reads the 88-well manual dipwell network monthly. Readings are taken at the **end of each month**: typically the last day of that month, or the first day or two of the following month. Each reading is the water level *for the month just ended*. A measurement taken on 1 May 2026 represents the **April 2026** water level.

Climate data come from RAF Valley Meteorological Station (53°15′00″N, ≈16 km from the site) as monthly totals for the same calendar month. They comprise rainfall *P* (mm) and minimum and maximum temperatures. Monthly Thornthwaite PET is computed from the temperatures at the RAF Valley latitude (53.25°).

Thornthwaite (1948) defines the heat index *I* as the sum of the monthly contributions *i* = (*T*/5)\^1.514 over the calendar year. Here the sum is taken instead over the trailing twelve months ending at the month being computed. That window contains exactly one of each calendar month, so it is still a full annual heat sum. Unlike the calendar-year form, however, it is defined at every month of a record that does not end in December. The PET of a given month also does not depend on the months that follow it.

The change matters because the monitoring record is live and is analysed part-way through a calendar year, where the calendar-year sum is undefined. Applied to the two months of 2026 available, the calendar-year form returned *I* = 3.1 against a normal near 45. It gave a February PET of 66.8 mm, against a range of 13.0 to 25.7 mm observed for that month at this station. Over the analysis period the two forms are equivalent in central tendency: monthly PET differs by a median of 0.00% (5th to 95th percentile ±5.5%). Individual months can differ by up to 16.6%. This is a departure from the published method rather than a correction to it, and is recorded as such.

**Bucketing.** Readings on physical dates ≤ day 15 of month *M* are bucketed into month *M*−1, because they belong to the previous month's water table. Readings on physical dates \> day 15 of month *M* are bucketed into month *M*. Field readings are nearly always taken either within the first week of a month or on the last day of the preceding month. That is why the cutoff is at day 15: day 15 is comfortably in the middle of the gap.

**Date semantics.** Every monthly timestamp in the pipeline is recorded in YYYY-MM-01 date format. The -01 day component is a formatting convention that makes monthly records machine-readable as dates. It does not refer to the 1st of the month. A row labelled 2007-07-01 is "July 2007": it contains the end-of-July water level and July's climate totals.

A concrete example for well CEH9, row 2007-07-01:

  -------------- ---------- ------------------------------------------------------------------
  *h*(*t*)       −0.610 m   End-of-July reading
  *h*(*t*−1)     −0.440 m   End-of-June reading
  Δ*h*           −0.170 m   Water-table change *during* July
  *P*            101.9 mm   July rainfall total
  PET            98.5 mm    July Thornthwaite PET
  *h*disp,prev   3.260 m    3.7 + (−0.440), displacement above drainage datum at end of June
  -------------- ---------- ------------------------------------------------------------------

The state-space model (Section S5) uses this row to explain July's 170 mm drop. The predictors are July's rainfall, July's PET, and the water-table position at the start of July (= end of June).

**Above-Ordnance-Datum invariance.** The above-Ordnance-Datum (mAOD) water-table elevation is a physical quantity, independent of the ground surface above it. Removing material from the surface does not move the water table, so the mAOD reading is the same before and after. Era-specific data handling is therefore needed only where depth-below-ground is the quantity of interest. It is not needed where mAOD water-table elevations are averaged or compared.

The data-preparation step (01_data_prep.py) reads three raw inputs: Newborough_Cleaned_For_Model.csv (water-table records), Well_locations_height.csv (well coordinates and DEM-derived ground elevations) and RAF_Valley_Climate.csv (monthly rainfall and temperatures). It produces the cleaned, bucketed and masked frames that every downstream script consumes.

### []{#anchor-1}S1.3 Cleaning and gap rules

Water-table records are screened for sentinel values and obvious measurement errors. Short gaps (a single missing month with valid neighbours) are filled by linear interpolation, with the gap limit set to limit = 1. Of the 15,025 well-months present in the well-provenance audit (01_wells_provenance.csv, Section S1.5), 259 are filled by interpolation. The remainder are observed.

### S1.4 Reference-network selection

[]{#s1.4-reference-network-selection}The reference network (66 wells, Section S3) is the subset of the 88-well network that meets all of the following criteria: - record start ≥ 2005, with the record continuing through REFERENCE_CUTOFF_DATE (2026-02-01); - not on the blacklist of wells with known tidal influence (notably the pdfs well at the south-eastern shore); - not one of the five wells of the clearfell monitoring footprint (FE1--FE4 and LIS1). The records of those five span a change of regime that a single set of SSM coefficients cannot describe. They form the treatment arm of the clearfell analysis in Paper 2 (Hollingham, 2026b).

The extended network adds the remaining 22 wells (clearfell-zone wells, wells with shorter records, and scraped wells) for spatial visualization only. Coefficients fitted to extended-network wells are reported only where stated. The per-cluster coefficients in Table 1 are reference-network only.

### []{#anchor-1}S1.5 Output

Cleaned monthly per-well frames, the climate frame and the canonical pipeline-parameters CSV are written to outputs/01_data_prep/. The well-provenance audit (01_wells_provenance.csv) records each well's membership in each network and the reason for any exclusion. It supports reviewer reproducibility.

## []{#anchor-1}S2. Constants and configuration

This section describes all pipeline constants and the canonical runtime-parameters file. The cluster partition, which determines the group each well belongs to, is the output of the behavioural clustering step (Section S3). The full partition table is given there.

### []{#anchor-1}S2.1 Constants

All values that are constant across the pipeline are defined in a single centralized configuration file. Any change therefore propagates everywhere, and no script can redefine a value locally. The constants used in Paper 1 are:

  ---------------------------- ------------ ------------------------------------------
  DRAINAGE_DATUM               3.7 m        Sensitivity analysis (Section S5.4)
  HEADLINE_LAG                 0            Field-convention bucketing (Section S1)
  FOREST_INTERCEPTION          0.24         Freeman (2008), Newborough Corsican pine
  FOREST_CIDS                  (4, 5)       *k* = 5 partition; forested clusters
  REFERENCE_CUTOFF_DATE        2026-02-01   Network selection (Section S1)
  RAF_VALLEY_LAT_DEG           53.25        53°15′00″N
  Hydraulic conductivity *K*   6 m day⁻¹    Betson et al. (2002) tracer test
  ---------------------------- ------------ ------------------------------------------

The 24% Corsican pine canopy-interception fraction is from Freeman (2008). It is the most spatially proximate canopy-interception measurement available for the Newborough plantation. *K* = 6 m day⁻¹ is from the single tracer test reported in the contemporaneous CCW groundwater-modelling study. It is required only in the Figure 18 forest-drawdown reach calculation (Section S13) and does not enter any other framework output.

### []{#anchor-1}S2.2 Canonical pipeline parameters file

The pipeline parameters are held in a single canonical table, pipeline_scenario_params.csv. The data-preparation step (Section S1) writes it. The downstream steps that fit new parameter values (the SSM regression, the BACI auxiliaries and the WTF specific-yield estimation) update it in place. Every downstream step reads its pipeline parameters from this file rather than from a hardcoded value. This rules out a category of inconsistencies that can otherwise propagate silently through long pipelines.

## []{#anchor-1}S3. Behavioural clustering and the *k* = 5 partition

### S3.1 Distance metric and linkage

[]{#s3.1-distance-metric-and-linkage}Cluster identification (02_clustering.py) works on a matrix of pairwise distances between per-well hydrographs. The distance between two wells is one minus the Pearson correlation coefficient between their monthly time series over their common record window. A small minimum-overlap requirement (≥ 36 months) stops short pairs from dominating. Pairs that do not meet it are flagged as undefined, and the affected well is excluded from clustering rather than imputed.

Ward's hierarchical linkage (Ward, 1963) is then applied. At each merge, Ward's criterion minimizes the increase in within-cluster sum of squares. This produces compact, well-separated clusters when the underlying data have structure. Ward was chosen over the alternatives (single, complete and average linkage) for two reasons. It performs well on behavioural time-series data (Rao and Srinivas, 2006; Liao, 2005). It also tends to produce spherical, balanced clusters of comparable size (Milligan and Cooper, 1985), which is desirable for interpreting them against physical substrate units.

### []{#anchor-2}S3.2 Cluster-count selection

The clustering literature offers several internal-validity indices for choosing the cluster count *k*. Two are used here: the Rousseeuw silhouette coefficient (Rousseeuw, 1987) and the Calinski--Harabasz pseudo-*F* statistic (Calinski and Harabasz, 1974). Both are evaluated for k in {2, \..., 10}. Each curve has its own maximum, and the maxima do not generally agree. This is a known property of internal validity indices applied to real data.

For Newborough the silhouette curve is highest at k = 2 (0.58). For k = 3 to 10 it lies between 0.37 and 0.43 (0.37 at k = 5). The Calinski--Harabasz index also peaks at k = 2. By the internal-validity criterion alone, the best choice would be k = 2. That is the top division of the dendrogram (Ward merge distance ≈ 0.99), which separates C4 Main Forest from the other 57 wells.

This was not adopted. The internal-validity indices reward separability, but they say nothing about whether the resulting clusters are physically interpretable. A k = 2 partition isolates C4 Main Forest and leaves the other 57 wells undivided. It loses the east--west division between the eastern clusters (C1, C2) and the western (C3 with C5), which follows at a Ward merge distance of ≈ 0.61. *k* = 4 collapses C5 Coastal Forest into C3, losing the coastal-retreat signature.

The Coastal Forest cluster is small (*n* = 5) and lies at the edge of the network. Yet it is among the most stable clusters under bootstrap resampling (median co-assignment 0.99, Section S3.5). It is also physically distinct: Corsican pine on the coastal sand body, with the steepest water-table decline in the network over the record. That physical distinctness is the basis on which it is retained as a separate cluster.

This study therefore selects *k* = 5 on a physical--mechanistic basis rather than on an internal-validity-index basis, and reports the indices transparently. The decision is taken openly in Section 3.2 of the main manuscript. It is also reflected in the Pearson affinity audit (Section S4). That audit shows that C5 wells sit at the edge of cluster space rather than in its interior, but that the edge position is consistent and reproducible across the 21-year record.

### []{#anchor-2}S3.3 The k = 5 partition table

Ward's linkage on correlation distance between per-well hydrographs (Section S3.1) partitions the reference network into five behavioural clusters. The cluster IDs and labels are:

  --- --------------------- ---- --------------------------------------------------
  1   C1 Lake Edge          7    Lake-adjacent (Llyn Rhos-Ddu), finer sediments
  2   C2 Dune               24   Mature open dune, eastern block
  3   C3 Western Residual   21   Deep aeolian sand, western block
  4   C4 Main Forest        9    Corsican pine on deep sand, northern ridge flank
  5   C5 Coastal Forest     5    Corsican pine, coastal margin
  --- --------------------- ---- --------------------------------------------------

Membership counts (canonical *k* = 5 partition under the live data-preparation pipeline) total 66 wells in the reference network. The extended network of 22 additional dipwells is used for spatial visualization and BACI work, but it is not part of the partition. Llyn Rhos-Ddu is treated as a fixed-head boundary feature rather than a behavioural cluster.

### S3.4 Canonical ID anchoring

[]{#s3.4-canonical-id-anchoring}Ward's linkage numbers its clusters in an arbitrary order that depends on the merge sequence. To keep cluster IDs stable across pipeline runs and partition changes, the clustering step carries a lookup table. The table maps each canonical cluster ID to one or two anchor wells whose membership identifies the cluster. After Ward returns its raw partition, the clusters are renumbered so that the anchor wells fall in the expected ID. An automated check confirms that the renumbering succeeded. In practice, this means "C1" refers to the same physical cluster across all pipeline outputs, irrespective of run order.

### []{#anchor-2}S3.5 Stability

Bootstrap resampling of the per-well hydrograph set returns the same five clusters, with stable cluster cores. The procedure draws 1000 random samples (with replacement) from the 66 reference-network wells and repeats the Ward's-linkage clustering on each draw. For each well, it counts the proportion of draws in which the well is co-assigned to its canonical-partition cluster (02_04_bootstrap_stability_summary.csv).

Four of the five clusters are highly stable, with median co-assignment above 0.97: 1.00 at C4 Main Forest, 0.99 at C5 Coastal Forest, and 0.98 at both C1 Lake Edge and C2 Dune. C3 Western Residual is the exception, at a median of 0.38. It is the most behaviourally heterogeneous cluster, and its members reassign more readily across bootstrap draws. This is the resampling signature of the continuous substrate gradient identified in Section S4. Along that gradient, wells near the cluster margins move between behavioural neighbours without the cluster cores dissolving.

C5 Coastal Forest has the smallest membership (n = 5), yet it is among the most stable clusters rather than the least. Its five wells behave consistently with each other and distinctly from the rest of the network (Section S4). Its anchor wells remain in C5 in almost every draw (NW9 in all of them, CEH16 in 99 %).

## S4. Pearson affinity audit and spatial confidence

[]{#anchor-2}The clustering algorithm assigns each well to the cluster with whose centroid it has the highest Pearson correlation. The *strength* of that assignment is how clearly a well belongs to its cluster, rather than sitting near the boundary between two. It can be recovered from the affinity matrix, which holds each well's Pearson correlation against every cluster centroid.

A well with a high primary affinity and substantially lower secondary affinities is a *core member* of its cluster. A well whose primary affinity is only slightly above its secondary is *gradational*: it sits at the boundary between two behavioural patterns. The Pearson affinity audit (05_pearson_affinity.py, Figure 5 of the main manuscript) makes this structure visible at the well level.

The audit shows three patterns. First, the cluster cores are spatially compact and behaviourally distinct, with high primary affinities and substantially lower secondary affinities. Second, the boundary between C2 (eastern Dune) and C3 (Western Residual) is gradational rather than sharp. Several wells in the centre-east of the network have primary affinity to one cluster but a secondary affinity within 0.05 of the primary. This indicates that they sit on a continuous substrate gradient between the two clusters rather than within a structural discontinuity. Third, C5 Coastal Forest is a tight core with the lowest affinity to any other cluster. This indicates that, although C5 has only five members, those five behave consistently with each other and distinctly from the rest of the network.

Section 5.1 of the main manuscript discusses the C2/C3 gradation at length. It is the basis for interpreting C3 as a "behaviourally coherent cluster on a continuous substrate gradient". It is also why the discussion uses "C3 transitional zone" rather than "C2/C3 boundary".

The output 05_pear_01_spatial_confidence_map.png is Figure 5 of the main manuscript. The underlying affinity matrix is in outputs/05_pearson_affinity/05_affinity_per_well.csv.

The audit classifies the 66 reference-network wells into three groups. 19 are Core: they sit cleanly in their assigned cluster, with a Pearson margin above 0.05. 41 are Fuzzy: the assigned cluster is the best match, but the margin to the second-best is small. Six are Spy: Ward's assignment and the Pearson best match disagree. Of these six, CEH21, CEH4 and WMC3 are assigned to C3 Western Residual but match C5 Coastal Forest. The other three, D38, T41a and CEH40, are assigned to C3 but match C2 Dune; D38 and T41a are two of the five boundary wells that moved from C2 to C3 in the final revision of the partition.

All six margins are small (\|Δr\| \< 0.015), marking borderline assignments at gradational boundaries. The six are documented but retained in their Ward's assignments, because Pearson margins within sampling noise are not a defensible basis for re-partitioning. The 91 % Core + Fuzzy share within the assigned cluster supports the partition as a reasonable behavioural grouping of the network.

## []{#anchor-3}S5. The state-space model --- displacement formulation

The state-space model (SSM) is the methodological core of the analysis. All of the following rest on it: the cluster characterization, the specific-yield estimation, the water-balance decomposition, the residual field and the coastal-retreat gradient regression.

### []{#anchor-4}S5.1 Equation

The fitted equation is

> Δ*h*(*t*) = β₁ · *P*(*t*) − β₂ · PET(*t*) − β₃ · (*z₀* + *h*(*t*−1))

Here Δ*h*(*t*) is the change in water table during month *t* (m, signed; negative when the water table falls). *P*(*t*) and PET(*t*) are the rainfall and Thornthwaite PET during month *t* (m). *h*(*t*−1) is the water table at the end of month *t*−1 (m, signed; negative below ground surface). *z₀* is the drainage datum, *z₀* = 3.7 m (Section S2). β₁, β₂ and β₃ are positive coefficients fitted by ordinary least squares (no intercept).

The quantity *z₀* + *h*(*t*−1) is the displacement of the water table above the drainage datum at the start of month *t*. With *z₀* = 3.7 m and a typical end-of-previous-month head of −0.4 m, the displacement is 3.3 m. With a deeper end-of-month head of −2.0 m, it is 1.7 m. The β₃ term says that the deeper the water table sits below ground at the start of a month, the smaller the drainage during that month. This is consistent with Darcy's law for a shallow unconfined aquifer drained to a fixed lateral discharge horizon.

The equation is a multiple linear regression. It has three predictor variables (rainfall, PET and start-of-month displacement) and one response variable (Δ*h*). Ordinary least squares (OLS) estimates the three coefficients jointly. It finds the values that minimize the sum of squared residuals across all (well, month) observations in the regression sample. The fit returns each coefficient with its standard error and *p*-value. It also returns the overall regression *R*² (the fraction of monthly Δ*h* variance jointly explained by the three predictors) and the residual series at every observation.

### []{#anchor-4}S5.2 Sign conventions

All three β values are reported positive. The signs are built into the design matrix, not into the coefficient values. In the design matrix the β₁ column is +*P*, so a positive β₁ means rainfall raises the water table. The β₂ column is −PET, so a positive β₂ means PET lowers the water table. The β₃ column is −(*z₀* + *h*prev), so a positive β₃ means displacement above the datum drives drainage downward. A fitted β₁ ≤ 0 or β₂ ≤ 0 halts the pipeline, because either is physical nonsense. β₃ \> 0 is soft-asserted: a negative β₃ is anomalous and worth investigating, but it does not halt the pipeline.

### S5.3 Why *h*(*t*−1) rather than *h*(*t*)

[]{#s5.3-why-ht1-rather-than-ht}The drainage term uses the water-table position at the end of the previous month, not the level in the same month. There are two reasons. First, h(t) is the dependent variable, through Δh = h(t) − h(t−1). Using it at the same time as a predictor would create simultaneity bias and break the interpretation of β₃. Second, and physically, drainage during a month is driven by the head at the start of that month, not the head at the end. The end-of-month head is the result of drainage, not its cause. The displacement at the start of month t equals the displacement at the end of month t−1, hence the h(t−1) form.

In principle, the within-month mean head would be a still more faithful driver. Total monthly drainage is the time-integral of a head-dependent flux, and the start-of-month form is in effect its forward discretization. But the mean is not observed. With a single end-of-month reading it can only be reconstructed as ½·\[h(t−1) + h(t)\]. That carries h(t), and hence Δh, back into the predictor. It reinstates the simultaneity the h(t−1) form is chosen to avoid, while adding no information beyond the two endpoints. In fact, the two discretizations are an exact reparameterization of one another on monthly data. The mean-head form rescales β₃ by 1/(1 − β₃/2) and leaves the fit, residuals and cluster contrasts unchanged. The start-of-month choice therefore costs nothing in fit, and only the simultaneity argument bears on it.

### []{#anchor-4}S5.4 Drainage datum

The 3.7 m drainage datum was selected to give comfortable β₃ identification at the forest clusters (C4 Main Forest, C5 Coastal Forest). β₃ is hardest to pin down there, because the water table sits deepest below ground. A sensitivity sweep over *z₀* compares two values. One is the live empirical minimum, z₀ = 1.6 m: the shallowest depth at which all five clusters simultaneously satisfy β₃ \> 0 with p \< 0.05. The other is the operating value, z₀ = 3.7 m. At the empirical minimum, C4's β₃ p-value sits at the significance edge (0.035). At 3.7 m it drops to 0.001. C5 also gains substantially: its β₃ p-value goes from 3 × 10⁻¹¹ to 1 × 10⁻¹⁶, and its R² from 0.642 to 0.677. The trade-off is small R² penalties at C1 Lake Edge (−0.053) and C2 Dune (−0.025). At these clusters β₃ is over-determined and remains significant at *p* \< 10⁻²⁵ at either depth.

The role of the datum is to shift the reference for the drainage term. Without it, the design column would hold *h*(*t*−1) instead of (*z₀* + *h*(*t*−1)), and the C4 and C5 clusters produced negative β₃ estimates. This was a sign-convention artefact. The OLS was correlating drainage with a quantity that crossed zero, rather than one that stayed on one side of a fixed reference. Setting the reference 3.7 m below ground places every observation comfortably on the positive side of the datum.

Δh does not change with the choice of datum, because the datum cancels in first differences. The coefficients do change. The model has no intercept, so a shift in the datum constant redistributes across β₁, β₂ and β₃ together. The datum therefore fixes the absolute scale of the drainage coefficient and of the half-life, which are reported as conditional on z₀ = 3.7 m. The cluster ordering, the open-dune drainage contrasts and the mean water-balance closure are robust across the swept range.

### []{#anchor-4}S5.5 Implementation: two levels of fit

The SSM is fitted at two distinct levels of aggregation, and Paper 1 uses both. The distinction matters because the two fits address different questions and feed different downstream products. Section S6 maps the fits to the products explicitly. The rest of this subsection covers the construction of the design matrix, which is common to both.

**Cluster-mean fit --- the primary characterization tool.** A single OLS regression is run for each cluster on the cluster-mean hydrograph. The cluster centroid is constructed by averaging the water-table depths of cluster members month by month, which gives one mean-depth time series per cluster. The SSM design matrix is then built from that centroid series and the shared climate forcing, and fitted by OLS. The result is one set of coefficients (β₁, β₂, β₃) per cluster. Each set comes with the regression *R*² and per-coefficient *p*-values that anchor Table 1 of the main manuscript. Working on the centroid, rather than on per-well-stacked rows, is the standard behavioural-cluster characterization approach. The cluster centroid is the canonical "average member" of the cluster. Fitting the SSM to it gives the coefficients that describe the cluster's collective behaviour without per-well noise. The cluster-mean fit underwrites the substrate-gradient interpretation of Sections 5.1--5.2, the Lumped Catchment Storage Coefficient (Section S6.4), and the drainage decay half-life t½ = ln(2)/β₃ reported in Section 4.7.

**Per-well fit --- the spatial-products tool.** The SSM is also fitted independently at each well in the reference network. This gives a separate (β₁, β₂, β₃) at every well. The per-well fits feed the spatial products. These are the coefficient atlas (Figures 11--13, three interpolated surfaces built from the per-well values), the per-well residuals (Figure 16, the residuals from the per-well fit, shown at the wells alone), and the per-well water-balance decomposition (Section S9). Per-well fits are noisier than the cluster-mean fit, because each is conditioned on a single well's record. Per-well coefficient values are therefore best read in the spatial pattern they form across the network, not at any single point.

**Common design-matrix construction.** The design matrix is built one (well, month) row at a time. For each row, the well's water-table series is joined with the RAF Valley climate record on the bucketed monthly index. Δ*h* and *h*disp,prev are then computed, giving a row with columns *h*, *h*prev, Δ*h*, *P*, PET and *h*disp,prev. The per-well fit at well *w* runs OLS over the rows belonging to *w* alone, and yields a per-well (β₁, β₂, β₃). The cluster-mean fit at cluster *c* builds the same row structure from the cluster centroid, which is the month-by-month mean of cluster members' depth series. It joins this against the shared climate record and runs OLS over those centroid rows. In either case a three-coefficient OLS regression (no intercept) is fitted. It reports the coefficients with their standard errors, *p*-values from a two-sided *t*-test against zero, regression *R*², and residual series. The row construction and the regression are implemented in 03_state_space_model.py. This script calls the shared helpers build_ssm_frame() and fit_ssm() from src/utils/model_utils.py. Nowhere else in the pipeline is the displacement calculation or the OLS fit reimplemented.

### S5.6 Residual serial correlation and inference validity

The SSM is a monthly time-series regression. The classical OLS standard errors behind the coefficient *p*-values are therefore valid only if the residuals are free of substantial serial correlation. This is tested directly (22_residual_lag_analysis.py, output 22_05_ssm_residual_autocorrelation.csv). The headline (no-intercept) SSM is refitted at each of the 62 reference wells with a valid fit, and the residuals are examined. The median Durbin--Watson statistic is 2.28 (interquartile range 2.17--2.40), and the median lag-1 autocorrelation is −0.14. The residuals therefore carry a slight *negative* first-order autocorrelation, not the positive persistence that would inflate significance. This is a direct consequence of the drainage term −β₃·(*z₀* + *h*(*t*−1)), which acts as an error-correction term and absorbs the first-order persistence of the level series. Negative residual autocorrelation makes the OLS standard errors mildly conservative, not anti-conservative. A Ljung--Box test at lag 12 rejects white-noise residuals at 21 of the 62 wells. This reflects the *seasonal* residual structure characterized independently in Section S8.2 (winter--spring phased), not low-order persistence. It is orthogonal to the coefficient standard errors.

As a robustness check, the coefficient *p*-values are re-estimated with heteroskedasticity- and autocorrelation-consistent (Newey--West / HAC) standard errors. The truncation lag follows the *n*-adaptive rule of thumb L = floor(4·(n/100)\^(2/9)). There are 186 coefficient tests (62 wells × three coefficients). Across them, the HAC and OLS significance verdicts at α = 0.05 agree in all but two instances: β₂ at CEH23 (p = 0.079 to 0.026) and at CEH25 (p = 0.092 to 0.029), both toward significance. HAC overturns no coefficient that OLS reports as significant. The classical-OLS inference underlying the coefficient tables is therefore sound.

These diagnostics are run at the per-well level, the noisier of the two fits. The same battery was also applied to the five cluster centroids that carry the headline β table (Table 1; 22_06_ssm_cluster_mean_inference.csv). The centroid β and OLS *p*-values in that file reproduce 03_03_cluster_mechanistic_coefficients.csv exactly. Every coefficient remains significant under both OLS and HAC: none of the fifteen cluster-level tests (five clusters × three coefficients) changes verdict. The centroid residuals are close to white (Durbin--Watson 2.05--2.26) at every cluster except C4 Main Forest. There, a mild positive autocorrelation (Durbin--Watson 1.82, φ = +0.06) still leaves all three coefficients HAC-significant. The cluster-mean fits, which pool every well in a cluster, are the better-conditioned of the two levels.

## **S5.7 Rainfall enters contemporaneously **

The recharge term uses the current month's rainfall, *P*(*t*), with no lag. This follows from the measurement protocol (Section S1). An end-of-month reading integrates the whole of that month's recharge, so the water-table change during month *t* is driven by month-*t* rainfall. Under the day-15 bucketing convention the correct pairing is same-month. The lag diagnostic (03_04_lag_diagnostic.csv) supports the choice. It refits each cluster centroid at rainfall lags of 0--3 months. Every cluster maximizes R² at lag 0 by a wide margin: R² is 0.68--0.81 at lag 0, falls to 0.04--0.42 at lag 1, and is lower thereafter. At the longer lags β₁ turns non-significant and sign-incoherent. Contemporaneous rainfall is therefore the best-supported predictor at the monthly timestep.

## []{#anchor-4}S6. State-space regression and the Lumped Catchment Storage Coefficient

### []{#anchor-5}S6.1 Per-well and cluster-mean fits, and where each is used

Section S5.5 introduced the two levels of fit. Both are implemented in 03_state_space_model.py. The mapping of each fit to the downstream products of Paper 1 is:

  ------------------------------------------------------------- -------------------------------------------------------- ----------------------------------------------
  Table 1 cluster mechanistic coefficients                      Cluster-mean                                             S6.2
  Lumped Catchment Storage Coefficient (LCSC)                   Cluster-mean                                             S6.4
  Drainage decay half-life t½ = ln(2)/β₃ by cluster             Cluster-mean                                             S6.2, main text §4.7
  Traditional-linear-model benchmarking                         Per-well, 100-month comparison window                    main text §3.5, Figure 9; Hollingham (2026c)
  Substrate-gradient interpretation (Sections 5.1--5.2)         Cluster-mean                                             main text
  Coefficient atlas, Figures 11--13 (β₁, β₂, β₃ surfaces)       Per-well, interpolated                                   S7
  Per-well residuals, shown at the wells (Figure 16)            Per-well, interpolated                                   S8
  Per-well water-balance decomposition                          Per-well                                                 S9
  Coastal-retreat panel regression (Section S12)                Per-well (cumulative water-balance covariate)            S12
  Residual-field diagnostics (cross-correlation, climatology)   Per-well (residual series)                               S8
  Pearson affinity audit (Figure 5)                             Independent of SSM --- operates on raw hydrographs       S4
  Water-table-fluctuation specific yield                        Independent of SSM --- operates on recharge / Δ*h*       S10
  Mean water-table head surface (Figure 15)                     Independent of SSM --- operates on observed mean heads   S11
  ------------------------------------------------------------- -------------------------------------------------------- ----------------------------------------------

The cluster-mean fit is the primary characterization tool. Table 1 of the manuscript, and the substrate-gradient discussion that runs through Sections 5.1, 5.2 and 5.5, are all carried by the cluster-mean coefficients. The per-well fit is the spatial-products tool. It lets the cluster characterization be projected as continuous surfaces across the site, for visual and diagnostic interpretation.

Three of the Paper 1 outputs are entirely independent of the SSM regression.

The first, the Pearson affinity audit, is the principal independent cross-check on the cluster structure. It tests, well by well, whether each dipwell sits closer to its assigned cluster centroid than to any other. It uses a Pearson correlation that does not depend on the SSM regression. Of the 66 reference-network wells, 60 sit in their assigned cluster as Core or Fuzzy members (91 %). Six (CEH21, CEH4, WMC3, D38, T41a, CEH40) are flagged as borderline cases, where the Pearson best match disagrees with Ward's assignment by small margins (\|Δr\| \< 0.015). They are documented but retained, since within-noise Pearson differences are not a defensible basis for re-partitioning.

The second, the water-table-fluctuation specific-yield estimation, takes cluster identity as an input rather than testing it. It does not separate the clusters. Once canopy interception is corrected, the cluster-level Sy values (Section S10.2) and the per-well estimates (Section S10.4) converge across the clusters, with C5 Coastal Forest at the edge of the range. This indicates that the behavioural contrasts the clusters capture are surface- and land-cover-mediated, rather than differences in subsurface storage.

The third, the mean water-table head surface, is independent of the cluster structure by construction. Clusters describe behaviour (how hydrographs move together), while the head surface describes where the water table sits (geometry and discharge boundary positions). The head surface feeds the Darcy flow field in Section S11, not the cluster argument. The justification for the cluster framework rests on the Pearson affinity audit.

### []{#anchor-6}S6.2 Cluster-mean coefficients

Table 1 of the main manuscript reports the full per-cluster (β₁, β₂, β₃) values, their standard errors and *p*-values, regression *R*², sample sizes *n* and Lumped Catchment Storage Coefficients (LCSC %, defined in S6.4). These are read live from 03_03_cluster_mechanistic_coefficients.csv. Section 5.2 of the main manuscript develops the substantive interpretation: the physical meaning of each coefficient, the direction of the cluster-to-cluster contrasts, and the comparison of C4 with C5.

### []{#anchor-6}S6.3 Caveats on OLS coefficient values

[]{#anchor-6}The cluster-mean coefficients are well determined within the OLS framework. Regression *R*² values lie between 0.68 and 0.81. The per-coefficient *p*-values are all very small (Section S6.2, Table 1 of the manuscript). Bootstrap resampling of the within-cluster wells gives tight confidence intervals on each (β₁, β₂, β₃). The interpretive caveat is not about coefficient accuracy in that statistical sense. It is about the *scope* of what the coefficients represent.

First, the coefficients are lumped cluster-mean responses, not point-flux measurements. β₁ is the system-aggregate sensitivity of monthly Δ*h* to rainfall, integrated over the cluster's heterogeneity. It is not a point recharge efficiency at any particular location. β₂ and β₃ are analogous lumped responses. Two wells from the same cluster need not share a common (β₁, β₂, β₃): the per-well fits show modest within-cluster variation around the cluster mean. A literal reading of the cluster coefficient as the value at any individual well over-extends the claim.

Second, the SSM is linearized: it assumes additive superposition of recharge, atmospheric draw and drainage. Real shallow-aquifer systems have nonlinearities, such as soil-moisture deficit thresholding recharge, depth-dependent ET access and hysteresis in the unsaturated zone. The lumped monthly fit averages over these. The high *R*² values say that the linearization works at monthly timestep: a three-coefficient linear model recovers much of the variance. They do not say that there is no nonlinearity to find. The residual climatology (Section S8.2) shows systematic seasonal structure at the cluster level, rather than month-to-month random variation. This is consistent with residual nonlinearity in the recharge term, the atmospheric-draw term, or both.

Third, at monthly timestep *P*, PET and *h* co-vary during recharge events. Collinearity between regressors widens the practical confidence interval on each individual coefficient relative to the OLS standard error, without inflating the point estimate in a known direction. The cluster-mean fits mitigate this by averaging over wells with slightly different individual covariances. The issue is nonetheless present in principle in any lumped state-space model fitted by OLS (Knotters and van Walsum, 1997; Healy and Cook, 2002).

The practical implication is that the *ranking* of clusters by each coefficient is robust to all three caveats: C4 has the highest β₂, the forest clusters have the lowest β₁, and C1 has the highest β₃. Cross-cluster contrasts at this level reflect the substrate, vegetation and topographic differences between clusters, which the SSM is designed to detect. Absolute coefficient values should be interpreted as lumped cluster-mean responses, not as instrument-equivalent calibrated fluxes. Section 5.2 of the main manuscript notes the same scope for the β₂ ranking: cross-cluster β₂ comparisons rest on the ordering and the relative magnitudes, not on absolute flux interpretation.

### []{#anchor-7}S6.4 Lumped Catchment Storage Coefficient

The Lumped Catchment Storage Coefficient (LCSC) is the reciprocal of the recharge sensitivity, expressed as a percentage:

> LCSC = 100 / β₁

β₁ is the water-table rise per unit depth of rainfall, so it is dimensionless. Its reciprocal is therefore the depth of rainfall required to raise the water table by one unit depth. Equivalently, it is the millimetres of rainfall required for a rise of 100 mm, which is how Table 1 of the main manuscript renders it. Dimensionally, that is a storage coefficient: the proportion of a unit rise occupied by water rather than by matrix. No separate estimation step is involved. The coefficient is read directly off the cluster-mean fit described above, and the methods of the main manuscript give the same definition.

The coefficient is *lumped* in the sense that it does not isolate drainable porosity. β₁ carries both the aquifer's storage response and the efficiency with which a month's rainfall reaches the water table. LCSC therefore rises when either the porosity is greater or the recharge is poorer, and this quantity does not separate the two.

The contrast across the canopy boundary illustrates the distinction. The two forested clusters carry the highest values in the network (C4 40.4%, C5 41.5%), against 21.8% to 26.6% in the open dune. This is consistent with canopy interception reducing the proportion of rainfall that reaches the water table, rather than with the plantation overlying a more porous body. Specific yield estimated by the water-table-fluctuation method (Section S10.1 below; Section 3.8 of the main manuscript) is independent of β₁ and bears on this directly. Once corrected for interception, the C4 forest median of 0.261 falls within the open-dune range of 0.210 to 0.325. The C5 median of 0.330 sits just above its upper edge, although the C5 estimate is constrained by the physical-plausibility limit and is only weakly corroborative. The Lumped Catchment Storage Coefficient and the water-table-fluctuation specific yield are therefore related but not interchangeable, and they are reported separately. Section 5.2 of the main manuscript develops the reconciliation.

Per-cluster LCSC values are reported alongside the cluster-mean coefficients in Table 1 of the main manuscript, read live from 03_03_cluster_mechanistic_coefficients.csv. Section 5.2 interprets the relative ordering across clusters.

## S7. Spatial interpolation of SSM coefficients

The per-well β₁, β₂, β₃ values (Section S6.1) are interpolated to continuous surfaces across the site (07_spatial_coefficients.py). The method is piecewise-linear interpolation over the Delaunay triangulation of the wells. The interpolation is purely geometric. The surfaces are *aggregators of point responses*, not the output of a calibrated distributed-flow model. The manuscript and the figure captions foreground this distinction.

### []{#anchor-8}S7.1 Interpolation configuration

Each surface is piecewise-linear over the Delaunay triangulation of the 66 reference wells. It is evaluated on a regular 50 m grid on the British National Grid (EPSG:27700) and drawn over a hillshade of the merged 2 m LiDAR digital elevation model. Every map of a per-well statistic in Paper 1 uses the same interpolator, except the water table (Section S11). The interpolator was chosen by leave-one-well-out prediction. Where a statistic has spatial skill, piecewise-linear, inverse-distance and kriged surfaces predict a withheld well about equally well. A single method is therefore kept across the maps, rather than a different winner being chosen for each statistic.

### []{#anchor-9}S7.2 Masking

Only one monitoring well (CEH12) lies on the northern rock-ridge bedrock outcrop (the area above the 20 m AOD contour), and it has a short record. Any interpolated coefficient values shown there are therefore extrapolations from the surrounding network, not values supported by data. In any case, the aquifer parameterization does not apply on bare metamorphic basement, so the interpretation in the manuscript does not rest on the ridge-zone cells. On the coefficient surfaces (Figures 11--13), a grid cell is masked as dune ridge where the LiDAR ground stands more than 1 m above the ground elevation interpolated between the wells. The surfaces thus describe the ground the wells sit on, not the ridges between them. The specific-yield surface (Figure 8, Section S10.4) is in addition clipped to the site outline. A per-well statistic is not given a surface at all if no interpolation between wells predicts a withheld well better than the network mean. The SSM water-balance residual (Figure 16, Section S8) is such a case, and is shown at the wells alone.

### S7.3 Bandwidth and edge effects

[]{#anchor-10}A piecewise-linear surface has no search bandwidth. Each grid cell takes its value from the three wells at the corners of the Delaunay triangle that contains it. Beyond the convex hull of the wells, the surface is extended by at most 100 m, taking the value of the nearest well. It is not drawn further out, so there is no extrapolation towards the coast or the Menai Strait beyond that margin. Near the network edge the triangles are long and thin, and the surfaces are less reliable there than in the interior.

### S7.4 Coefficient atlas

[]{#anchor-11}[]{#anchor-12}The three interpolated coefficient surfaces (β₁, β₂, β₃) are presented as Figures 11--13 of the main manuscript. Together they form the "coefficient atlas". The surfaces are intended as diagnostic readings of the cluster characterization, extended continuously across the site. They are not flux maps, and not predictions in any forward-modelling sense.

## []{#anchor-13}S8. Residual-field diagnostics

The state-space regression (Section S6) produces a per-month residual at every well. This is the portion of the observed Δ*h* not explained by the lumped balance β₁·*P* − β₂·PET − β₃·(*z₀* + *h*\<sub\>prev\</sub\>). Evaluated at each well's long-term mean climate and mean head, this becomes a steady-state balance: modelled mean losses (β₂·PET̄ + β₃·h_disp̄) minus modelled mean recharge (β₁·P̄). The result is a per-well residual in m/month. It is positive where modelled losses exceed modelled recharge, implying an unmodelled input, and negative where the model over-predicts. These per-well totals are shown at the wells alone (Figure 16 of the main manuscript), and it is that set of values, not a surface, that is analysed here. No interpolation between wells predicts a withheld well's residual better than the network mean, so no surface is drawn. The per-well residual computation is implemented in 20_spatial_figures.py, and the per-well values are written to 20_residual_perwell.csv. Section S9 gives the formal partition of the modelled signal into its three SSM components.

Rainfall enters gross at every well, including the forested ones. The coefficients are fitted on gross rainfall and above-canopy PET, so the canopy interception loss is already carried inside the fitted β₂·PET̄ term. Subtracting it from rainfall as well would double-count it and insert a spurious positive residual at C4 and C5. The residual is not invariant to this choice, so the convention is stated explicitly here.

The residual field carries no spatial structure, with a small systematic negative offset. Of the 66 reference wells, 65 fall within ±0.01 m/month and 51 are negative. Residual magnitude is uncorrelated with position on either axis (Spearman ρ = −0.14 against Easting, p = 0.27; ρ = +0.16 against Northing, p = 0.20). The signed residual shows no gradient on either axis (ρ = +0.02 against Easting, p = 0.86; ρ = −0.10 against Northing, p = 0.40). No well exceeds +0.02 m/month. The fifteen positive residuals all fall below +0.008 m/month (largest NW3, +0.0080 m/month). They lie in the open dune, at the lake edge and in the coastal forest, and none lies in C4 Main Forest. The most negative residual falls at the ridge-flank well CEH14 (−0.0105 m/month), with CEH32 (−0.0079 m/month) next. The balance closes without requiring an additional flux.

The two diagnostic tests below were run when the field was believed to be spatially structured. They are retained for what they establish about the limits of the monitoring design, not as a discrimination among candidate mechanisms. Script 22 characterizes the residual series itself (per-well AR(1), Durbin--Watson and HAC standard errors, Section S5.6). It establishes that the network's residuals are close to white: the AR(1) coefficient is small and negative at most wells (network mean φ = −0.142, median −0.144) and only four of the 62 wells exceed \|φ\| = 0.3.

### S8.1 Cross-correlation lag test (23_ridge_recharge_lag_test.py)

[]{#anchor-14}Suppose a ridge-derived lateral input were present: a Darcy-conveyed subsidy from the metamorphic bedrock ridge through the down-gradient open dune. A distance-dependent transport lag should then be detectable. The time between a recharge event at the ridge and the corresponding response at down-gradient wells should increase systematically with distance. The cross-correlation lag test computes lagged correlations between (i) a ridge-zone composite recharge signal and (ii) the de-trended water-table series at each down-gradient well. It identifies the lag at maximum correlation for each well.

The test returns a null result: there is no monotonic distance-dependent lag structure across the down-gradient wells. Across the 49 of 66 wells with a significant cross-correlation peak, the Spearman rank correlation of peak lag against ridge distance is ρ = −0.03, p = 0.85. The peak lags are not, however, an observation of travel time. By construction, OLS residuals are orthogonal to the fitted rainfall regressors at lags 0 and 1. This imposes a methodological floor. Of the 49 significant peaks, 42 fall at lag 2, and 50 of the 66 wells peak at lag 2 irrespective of ridge distance. The pattern persists under a Box-Jenkins pre-whitened reformulation. The statistic is therefore partly determined by the fitting procedure rather than by hydrology.

What structure the lags do carry is organized by cluster, not by ridge distance. All five wells peaking at lag 3 are C4 Main Forest (ridge distances 741--1068 m, peak r = +0.16 to +0.20). This is consistent with the weak head-dependent drainage of the forest interior (the network's lowest cluster β₃, 0.018 month⁻¹), rather than with a distance-dependent transport path. Two significant wells peak beyond lag 3: CEH17 at 11 months and CEH32 at 12. They carry among the weakest correlations in the set (\|r\| ≤ 0.18, one of them negative). Their peaks reflect the flatness of the cross-correlation function rather than a resolvable delay.

This null result must be qualified by sampling frequency. Monthly observations are an order of magnitude coarser than the days-to-weeks transit times expected for fracture-flow input from a metamorphic bedrock ridge, so a real ridge-derived lag could be invisible at this resolution. The null result therefore bears on what the present record can resolve, not on whether the mechanism is operative.

### []{#anchor-15}S8.2 Seasonal climatology test (24_residual_seasonality.py)

The residual field might reflect systematic underestimation of summer evaporative demand at the forest margin, for example an under-resolved canopy-driven evaporative loss not captured by Thornthwaite PET. If so, the residual field should peak in summer, when those fluxes are active. The seasonal climatology test computes the monthly mean residual at each well across the 21-year record.

The test discriminates among candidate mechanisms. A summer-dominated peak confined to the forest clusters would indicate canopy-interception over-estimation or an analogous vertical-flux error. A pattern not confined to the forest clusters would indicate a different family of mechanism. Examples are recharge nonlinearity in the lumped monthly model, or an unmodelled non-vertical-flux input.

A cluster-stratified analysis aggregates the per-well climatology by the *k* = 5 partition. It computes the winter-minus-summer contrast at each cluster, with bootstrap confidence intervals. The pipeline reports the complement, so signs are reversed in 24_05_diagnostic_summary.txt. The strongest contrast across the network is at open-dune C3 Western Residual (+8.6 mm, p \< 0.001), not at either forest cluster. C4 Main Forest shows +5.4 mm (p = 0.068, marginal), and C5 Coastal Forest shows −0.3 mm (n.s.). This pattern is inconsistent with canopy-interception over-estimation as the sole driver. That mechanism would predict both forest clusters peaked and the open dune flat, and the data show the reverse. There is a weak within-forest gradient: the winter--summer contrast strengthens toward the ridge across 14 forest wells (r = −0.58). This is consistent with a ridge-derived component, but it cannot be separated from a site-wide recharge term on the present evidence.

The full seasonal climatology has additional structure, including non-trivial shoulder months, that the winter-minus-summer contrast does not fully characterize. A detailed seasonal decomposition, disaggregating the recharge and atmospheric-draw terms, is the subject of a follow-up methodological treatment and is outside the Paper 1 scope.

### []{#anchor-16}S8.3 Ridge zone

The residuals in Figure 16 are drawn at the wells alone. No residual value is therefore shown on the rock-ridge bedrock outcrop on the northern boundary, which carries no reference monitoring well, or anywhere else between wells. The head-gradient arrows drawn beneath the residuals come from the kriged water table of Section S11, not from the residuals.

### []{#anchor-17}S8.4 Status of the residual field

This section was originally built on a spatially structured residual field. That structure did not survive correction of the Script 20 computation. It was an artefact of two arithmetic defects in that computation. First, canopy interception was subtracted from rainfall at the forest wells as well as being carried inside the fitted β₂·PET̄ term (above, and Section S9.2). Second, long-term climate means were taken over the whole RAF Valley record from 1930, rather than over the monitoring period of the mean heads. The corrected field shows no spatial organization on either axis. What the diagnostics establish is a bound on the monitoring design, not a discrimination among mechanisms. The seasonal test finds no summer signature that would indicate Thornthwaite misspecification, and the lag test could not have resolved a travel-time gradient had one been present. The per-well residuals are therefore presented as a diagnostic of how completely the lumped balance closes at each well, not as a quantified flux map.

## []{#anchor-18}S9. Water-balance decomposition

The SSM equation (Section S5.1) is, equivalently, a monthly water-balance identity. It partitions the change in water-table head into four terms: recharge driven by rainfall, atmospheric draw driven by PET, drainage proportional to displacement above the lateral discharge horizon, and a residual ε that the lumped balance does not explain. Paper 1 uses this identity at two levels. The headline is a cluster water balance at cluster-mean scale (Section S9.1, the primary analysis). The second is a per-well residual field, analysed as a spatial diagnostic (Section S8).

### S9.1 Cluster water balance (primary analysis)

The cluster water-balance decomposition (16_water_bal.py) is the headline analysis. The β coefficients fitted by the SSM are monthly-scale. β₁ is the response (in metres of Δ*h*) per metre of rainfall *during a given month*, and β₂ and β₃ are defined analogously. The natural product β₁·*P̄* is therefore a *monthly* recharge contribution when *P̄* is a monthly mean.

For each cluster the partition is computed at monthly timestep as

$${\text{recharge} = \beta_{1}}\cdot\overline{P}$$

$${\text{atmospheric draw} = \beta_{2}}\cdot\overline{\mathit{PET}}$$

$${\text{drainage} = \beta_{3}}\cdot\overline{h_{\text{disp}}}$$

where *P̄* and PET̄ are the long-term means of the RAF Valley monthly climate forcing. They are computed as the sum across the record divided by the number of months observed, and are identical across clusters. *h̄*\<sub\>disp\</sub\> is the long-term monthly mean of the cluster centroid displacement. The β values come from the cluster-mean SSM fit (Section S6.2, 03_03_cluster_mechanistic_coefficients.csv). Each contribution is then scaled to annual units by multiplying by 12 (months per year), for reporting in Table 3 of the main manuscript and Figure 7. This is equivalent to multiplying the β coefficient by the long-term *annual* mean of the corresponding driver (record sum ÷ years on record). The two normalizations give the same annual contribution.

The water-balance closure follows from the SSM equation evaluated at long-term means. Over the full record Δ*h̄* is approximately zero, because the cluster centroid hydrograph has no net trend. The four right-hand-side terms must therefore sum to approximately zero:

> $$\Delta{\overline{h} = \beta_{1}}\cdot\overline{P}-\beta_{2}\cdot\overline{\mathit{PET}}-\beta_{3}\cdot{\overline{h_{\text{disp}}} + \overline{\epsilon}}\approx 0$$

The mean residual ε̄ is what the lumped SSM does not explain, and the closure result quantifies it. Across all five clusters this closure error is within 1.8 % of total losses. In other words, the three β-weighted long-term means account for at least 98 % of the long-term storage balance. The small remainder comes from whatever the lumped three-term balance does not represent, including residual nonlinearity, spatial heterogeneity within the cluster and error in the climate forcing. Section S8 examines its spatial structure and finds that the corrected per-well field carries none.

### []{#anchor-19}S9.2 Canopy interception at the forest clusters

For C4 Main Forest and C5 Coastal Forest, Freeman (2008) measured canopy interception at 24 % of incident rainfall. The intercepted depth is

> *I*(*t*) = *i* · *P*(*t*)

> where *i* = 0.24 is the canopy interception fraction (Freeman, 2008). This depth is not subtracted from rainfall anywhere in the fitted model. The cluster SSM (Section S6) is fitted on gross rainfall and on Thornthwaite PET computed above the canopy. The interception loss is therefore already carried inside the fitted β₂·PET̄ term. Interception is a partition of the available atmospheric energy budget, not an additional demand on top of it. Re-evaporation from intercepted rainfall on leaf surfaces, transpiration and direct evaporation from the water table all draw on the same PET. Subtracting the intercepted depth from rainfall as well would count the same loss twice. That defect was present in the per-well residual computation of Script 20 until its correction on 2026-08-06 (Section S8); it is not present in the cluster analysis reported here.

> The lower β₁ values at the forest clusters are therefore a fitted result, not a consequence of any pre-adjustment. They reflect a damped water-table response to gross rainfall. This is consistent with Freeman's measurement of forest soil moisture at roughly half the open Warren's and a forest water table about 1.07 m deeper. The 24 % fraction enters the analysis only as a display partition. In the volumetric panel (Figure 7 panel b), the interception band is drawn identically on the input side and the loss side. It cancels in the net surplus, but it makes visible how much of the forest clusters' rainfall is re-evaporated before it can reach the water table. It does not change total losses, the residual, or the balance at any cluster.

# **S10. Water-table-fluctuation specific yield**

Specific yield Sy is the drainable porosity of the saturated medium near the water table. It is estimated in 17_wtf_specific_yield.py, and it is required to convert per-well water-table behaviour into a volumetric storage interpretation. It is also a substrate-character diagnostic in its own right: a spatial gradient in Sy across an open dune-aquifer can indicate a corresponding gradient in sediment character (grain size, sorting, fines, weathering).

## **S10.1 The water-table-fluctuation method**

The water-table-fluctuation (WTF) method (Healy and Cook, 2002) estimates Sy from the relationship between net recharge and the corresponding water-table rise:

Sy = R / Δh

where R is the net recharge and Δh is the corresponding water-table rise. R is rainfall minus PET, restricted to winter months when PET is small (R \> 0). Three parallel implementations of the method are used here. They agree closely at C3 Western Residual and on the coarse cross-cluster ordering, but diverge at C1 Lake Edge (Section S10.3).

**Approach A --- winter OLS.** The ratio above attributes the whole of the observed monthly change to recharge. Part of that change, however, is drainage occurring within the same month. Approach A removes that term first, using the state-space drainage coefficient. From Δh = (R / Sy) − β₃·\|h_prev\| it follows that R = Sy · (Δh + β₃·\|h_prev\|). A no-intercept ordinary-least-squares regression of net recharge R against the drainage-corrected rise (Δh + β₃·\|h_prev\|) therefore recovers Sy directly as the fitted slope. The fit is restricted to winter months (November--March), when Thornthwaite PET is below 25 mm month⁻¹ and net recharge approximates actual recharge well. This approach is statistically the most defensible, being a single regression with a clear assumption. It provides limited uncertainty information, however, beyond the regression standard error.

**Approach B --- event median**. An event-detection step identifies rising-limb months, which are winter months with positive recharge and positive Δh. It computes Sy = R / Δh for each event and reports the cluster-level median, together with its 25th and 75th percentiles. This is noisier per event, but it provides empirical uncertainty bounds and shows the within-cluster variability of the estimate.

**Approach C --- rapid recharge events**. A third estimator, after Crosbie et al. (2005), targets the same quantity by a route that shares the assumptions of neither of the first two. Approach A removes the drainage contribution to the observed rise mechanistically, using the fitted β₃. Approach B does not remove it at all, and is correspondingly biased low. Approach C instead selects episodes in which the drainage contribution over the rise is negligible by construction, so that the uncorrected ratio is approximately unbiased. A candidate episode requires at least two consecutive prior months of falling or static water table (Δh ≤ 0), which mark a drainage-dominated quasi-steady state. The episode begins at the first subsequent month with Δh \> 0 and continues for at most two further months while the rise persists. It must accumulate a cumulative rise of at least 50 mm. For each qualifying episode, Sy is the summed net recharge over the episode divided by the cumulative rise. It is retained only within the physically plausible interval 0.01 \< Sy \< 0.50, the same interval applied per event in Approach B and in the per-well fits of Section S10.4. Episodes are non-overlapping. The cluster estimate is the median of qualifying episodes, with a 95 per cent confidence interval from 1000 bootstrap resamples of the episode set. For the forested clusters the interception-corrected recharge of Section S10.2 is used, so the reported forest values are directly comparable with the corrected Approach B variant. Approach C is reported as an independent cross-check only, and it does not propagate to any downstream calculation.

## **S10.2 Cluster-level estimates**

Cluster-level event-median Sy estimates are reported as Table 4 of the main manuscript. All three approaches are read live from 17_wtf_01_sy_estimates.csv and compared in Section S10.3.

For the forested clusters (C4, C5) an interception-corrected variant is also reported. The correction applies Reff = (1 − i) · P − PET, with i = 0.24 (Freeman, 2008). The corrected values are the ones used in the Table 1 interpretation. Approaches B (event median) and C (rapid-event) report the interception-corrected forest fits. Approach A is not used for the corrected variant. The winter-only filter combined with the interception correction reduces the C4 and C5 sample sizes so far that the no-intercept OLS becomes unstable. This sample-size limitation is specific to the corrected forest case. It is not a general property of Approach A, which is reliable across all five uncorrected fits.

## **S10.3 Caveats**

Monthly resolution prevents isolation of individual storm events. The WTF estimates therefore conflate true gravity drainage with capillary-fringe release. They should be read as upper bounds on the storage coefficient, not as point estimates of the gravity Sy alone (Healy and Cook, 2002; Scanlon et al., 2002). Slug tests or pumping tests at representative wells per cluster remain the gold-standard alternative, and would be the priority future field measurement. As with the SSM coefficients (Section S6.3), the robust and used quantity is the cross-cluster ordering, not the absolute magnitude.

The three estimators converge closely at C3 Western Residual (0.35, 0.32, 0.31 for Approaches A, B, C). This is the value that anchors the Figure 18 forest-drawdown reach. Approaches B and C agree that C1 Lake Edge is the low-storage end (0.21 and 0.19). The higher winter-OLS estimate there (0.34) is consistent with the β₃ drainage correction over-correcting in the lake-buffered setting. Where an absolute Sᵧ nonetheless enters a downstream quantity, namely the Figure 18 reach λ = √(Kb⁄(Sᵧ·β₃)), it is used as an order-of-magnitude input and reported accordingly (Section S13). The one genuinely method-dependent feature is the top of the ranking. The uncorrected winter-OLS fit places C5 highest. The interception-corrected rapid-event estimate places C3 highest. The interception-corrected event estimate places C5 marginally above C3 (0.330 against 0.325).

## **S10.4 Spatial Sy surface**

A per-well Sy field (18_wtf_spatial.py) is produced by computing per-event Sy = R / Δh at every well in the reference network. The field reports the per-well median across rising-limb events, retained within the same 0.01 \< Sy \< 0.50 interval. This is Approach B applied at the well level, with per-well 25th and 75th percentiles for uncertainty. Forest clusters (C4, C5) carry the interception correction directly in the recharge term, Reff = (1 − 0.24) · P − PET. Forest values therefore carry additional uncertainty associated with the canopy correction (Freeman, 2008).

This differs from the SSM treatment in Section S9.2, but the difference is a consequence of the two methods' structure rather than an inconsistency. The WTF method estimates recharge directly, so the canopy loss must be removed from rainfall explicitly. The SSM is fitted on gross rainfall and above-canopy PET, and therefore already carries that loss inside the fitted β₂·PET̄ term.

Two wells are excluded from the contour interpolation on physical grounds. CEH12 sits on the bedrock ridge in a forested area, where the WTF Sy reflects bedrock rather than the sand aquifer. CEH15 sits in a low-lying slack within the plantation, where the local hydrology is not representative of upland forest sand. The per-well Sy values are interpolated to a continuous surface (Figure 8 of the main manuscript) by the piecewise-linear procedure of Section S7, clipped to the site outline. Section 5.2 of the main manuscript develops the substrate-gradient interpretation of this pattern.

## []{#anchor-20}S11. Mean water-table surface and the Darcy flow field

### []{#anchor-21}S11.1 Mean head per well

A long-term mean water-table elevation (m OD) is computed at each well in the reference and extended networks that has a surveyed ground elevation. It is that elevation plus the mean of every reading in the well's record (01b_water_table.py). The mean water-table surface shown in Figure 15 of the main manuscript is kriged from those means. The same construction is repeated for a wet and a dry state of the network: the months in the top and bottom decile of the network-median level. Each well's mean is then taken over that state's months. A well enters only if it has enough readings in all three states. The three surfaces therefore rest on one set of 83 wells: the 66 of the reference network and 17 extended wells (n_wells_kriged, 01b_report_numbers.csv). For most reference-network wells the mean state is essentially the full 21-year monitoring window. Extended-network wells, recently-installed wells, and wells with intervention-driven baselines (the scraped well CEH36) have a shorter available record. For these the mean correspondingly reflects a narrower time window.

Taking each well's whole record, rather than a mean over a common reference period, keeps full network coverage at the periphery. It has two known costs. A record that starts or ends part-way through a year weights the seasons unevenly. Wells that join or leave the network at different times change the composition of the contributing set. Neither is corrected for.

### S11.2 Spatial head surface

[]{#anchor-22}The per-well mean heads are kriged onto a 20 m grid over the study area (Figure 15), with a spherical variogram fitted to the wells. The water table is the one per-well quantity mapped by kriging rather than by the piecewise-linear surface of Section S7. This is because kriging admits the ground surface as an external drift, and that drift can be tested. Four forms were compared: ordinary kriging with no drift, and drifts on the raw LiDAR DEM, on the DEM smoothed to the scale of the dune ridges, and on a slack-floor lower envelope. Each was judged in two ways. The first was leave-one-well-out error, with the withheld well left out of both the fit and the variogram. The second was a physical test: whether the surface stands above the ground where Sentinel-2 never recorded water. Ordinary kriging was selected. It has the smallest leave-one-out error in all three states, with a median absolute error of 0.14 m and a bias of −0.005 m in the mean state (01b_01_drift_selection.csv).

The edges of the surface are anchored rather than extrapolated. The sea is anchored along the high-water mark at a coastal head fitted to the coastal wells between mean tide level and mean high water. This returns 1.87 m OD, close to mean high water (coastal_head_m, 01b_report_numbers.csv). Three landward boundaries were kept, each only because it did not worsen the leave-one-out error at the wells near it beyond a small tie margin: the Afon Braint at its channel elevation, Llyn Rhos-Ddu at its gauged level, and the ridge well CEH12 at its measured depth below ground. A boundary along the whole ridge divide was tested and dropped, because it over-predicted the forest-edge wells. No elevation-model mask is applied. The water table need not lie below the ground everywhere, and in the slacks it periodically does not. The mean surface is a single mound, highest beside the bedrock ridge. It falls to the coastal head along Caernarfon Bay and to the river and lake levels inland.

### []{#anchor-23}S11.3 Darcy flow field

The flow-direction field (Figure 15) is the negative gradient of the kriged head surface. By Darcy's law, this gives the direction of groundwater flow through an isotropic aquifer:

> **direction of flow = −∇h**

> where ∇h is evaluated by finite differences on the kriged grid. The arrows are drawn on a regular lattice coarser than the grid. Each arrow is sized and coloured by the magnitude of the head gradient rather than normalized, so that steep and slack gradients are distinguished. Arrows far from any dipwell are drawn faint, because there a boundary rather than a measurement sets them. Neither a hydraulic conductivity nor an aquifer thickness enters the field. It is the flow geometry of the mapped surface, not a discharge map.

> Flow runs outward from the water-table high beside the bedrock ridge. It runs south and south-west to Caernarfon Bay across the west and centre of the site, north towards Llyn Rhos-Ddu from the slacks beside the lake, and east and south-east to the Afon Braint. The pattern barely changes with the state of the aquifer. The median head gradient is 0.0071 in the wet state and 0.0062 in the dry, and the median flow direction at the slacks turns by 4.7° between the two (01b_report_numbers.csv). The pattern is also insensitive to the boundary choices. Fixing the coastal head anywhere from 0 m OD to mean high water changes the median slack flow direction by less than 1°. Removing the landward boundaries changes it by about 2°. The runner-up drift, the smoothed DEM, changes it by about 19° (01b_05_sensitivity.csv).

> The DEM-derived topographic drainage paths are drawn on Figures 15 and 16 for comparison with this field. That overlay is a cartographic-context layer, loaded by the pipeline from data/streams.kml. It was produced in QGIS using GRASS r.watershed against the LiDAR digital elevation model, with multiple-flow-direction routing and a 4000-cell channelization threshold (≈ 1.6 ha minimum contributing area). It is rendered as cartographic context rather than as a pipeline output. The overlay is surface routing, which spills each closed slack over its saddle. It is drawn for comparison with the groundwater flow field, not as evidence for it.

## []{#anchor-24}S12. Coastal-retreat gradient regression

The Newborough coastline at the south-western dune front (Caernarfon Bay) is undergoing measurable retreat (Pye and Blott, 2024; Forgrave, 2020). Section 4.11 of the main manuscript tests the hypothesis that this coastal retreat is producing a spatially-structured water-table decline that decays inland. The hypothesized decline is a chronic, location-dependent forcing, distinct from the spatially-uniform climate background.

### S12.1 Panel regression specification

The test (25_coastal_gradient.py) is a panel regression of well-level long-term water-table trends against perpendicular distance to the eroding shoreline:

$${t_{\mathit{ij}} = \delta}{\left( d_{i} \right) + \alpha_{i} + \alpha_{j} + \gamma}\cdot{W_{\mathit{ij}} + \epsilon_{\mathit{ij}}}$$

where *t*~*ij*~ is the monthly water-table change at well *i* in month *j*, *d*~*i*\ ~is well *i*'s perpendicular distance from the eroding shoreline, δ(·) is the modelled distance decay, α~*i*\ ~and α~*j*~ are well and month fixed effects (absorbed by within-well demeaning), *W*~*ij*~ is the cumulative water-balance covariate (the integrated SSM water balance to month *j*, included to absorb the spatially-uniform climate background and so isolate the spatially-structured residual), γ is its coefficient, and ε~*ij*~ is the residual.

Two functional forms are tested for the distance decay δ(·):

-   **Linear-capped**: δ(*d*) = δ₀ + (*c_far* − δ₀) · min(*d*/*L_cg*, 1). This is a linear decline from a coast-edge intercept δ₀ to a far-field background *c_far* over an inland reach *L_cg*. Beyond *L_cg* it is flat at *c_far*.
-   **Exponential**: δ(*d*) = *c_far* + (δ₀ − *c_far*) · exp(−*d*/*L_cg*). This is an exponential decay from δ₀ at *d* = 0, approaching *c_far* asymptotically, with characteristic length *L_cg*.

[]{#anchor-25}Both forms are fitted by nonlinear least squares. Model selection between the two is by the Akaike information criterion (Akaike, 1974).

### []{#anchor-26}S12.2 Nested specifications

Four specifications are fitted to test robustness:

-   **Full network**: all open-dune and forested wells in the reference network. The clearfell-zone wells are excluded, because they carry a non-coastal management forcing.
-   **Forest-free**: the open-dune wells (C1, C2, C3) only, with all forested wells excluded. This is the primary specification reported in the manuscript. It removes from the distance fit any contamination from forest interception or canopy-driven evaporative demand.
-   **C3-only**: wells in C3 Western Residual only. The far-field background *c_far* is fixed at the forest-free value rather than re-estimated. This tests whether the distance gradient is identifiable within the single cluster geographically closest to the eroding shoreline.
-   **Canopy-controlled full network** (Script 25 v1.9.0): the full network refitted with a canopy × time term on the *in_forest* land-cover flag. This controls forest cover explicitly rather than excluding it. The absorbed canopy coefficient is −9.0 ± 2.5 mm yr⁻¹ (linear-capped): the extra water-table fall under pine, net of distance to the coast. The coast-edge amplitude is essentially unchanged (δ₀ −32.26 against the forest-free −31.28), so the gradient does not depend on how forest cover is handled. This fit is a cross-check, not the headline. *full* and *full_canopy* are not comparable on AIC, because the canopy term is absorbed in the within-group step.

### []{#anchor-27}S12.3 Parameter values

Fitted parameters, read live from outputs/25_coastal_gradient/25_01_panel_fit_parameters.csv:

  ------------- ------------------------------- -------- ----------- --------------- ----------- --------------
  Full          linear-capped                   12,006   −33,668.5   −31.73 ± 1.95   994 ± 57    −0.47 ± 0.56
  Full          exponential                     12,006   −33,672.6   −41.30 ± 2.58   609 ± 99    +3.28 ± 1.52
  Forest-free   linear-capped                   10,929   −31,848.8   −31.35 ± 1.97   894 ± 48    −0.10 ± 0.55
  Forest-free   exponential                     10,929   −31,853.7   −40.63 ± 3.15   489 ± 76    +2.12 ± 1.09
  C3-only       linear-capped (*c_far* fixed)   3,676    −10,254.1   −29.06 ± 2.75   928 ± 71    −0.10
  C3-only       exponential (*c_far* fixed)     3,676    −10,269.6   −32.15 ± 3.71   713 ± 109   +2.12
  ------------- ------------------------------- -------- ----------- --------------- ----------- --------------

Confidence intervals are 95% (1.96 SE). The ± values in the table are the fitted, row-basis standard errors. The uncertainties quoted in the manuscript are on the well basis (§S12.7). The forest-free linear-capped fit is the headline specification: δ₀ = −31.28 mm yr⁻¹, L_cg = 902 m, c_far = −0.30 mm yr⁻¹. The manuscript quotes the fitted trend at 150 m from the shoreline, −26.38 mm yr⁻¹ (well-basis SE 3.49, §S12.7; fitted SE 1.45), rather than δ₀ itself. No well sits at the shoreline, and the two decay forms disagree there by 9.3 mm yr⁻¹, against 1.6 mm yr⁻¹ at 150 m.

The constant *c_far* is the fitted far-field asymptote, not a climate background. It is separately identified: its variance inflation factor against the cumulative water-balance covariate is 1.01. But it is unstable with respect to the fitting window. It runs from −0.30 to +23.96 mm yr⁻¹ as the window start is moved with the well set held fixed. It is therefore a window statistic rather than a rate.

### []{#anchor-28}S12.4 Model selection

Model selection by AIC favours the exponential form in the forest-free specification. The difference is −6.0 (−31,813.4 against −31,819.4, exp − lin-capped). The same comparison gives −5.1 on the full network and −9.9 on C3-only, in each case favouring the exponential. Both fits agree on the sense of the gradient: a coast-edge deepening that decays inland. They also agree on the magnitude of the coast-edge component (about −28 to −41 mm yr⁻¹). Both return a far-field asymptote c_far between −0.65 and +3.21 mm yr⁻¹ across the six fits. The choice of functional form changes the inland reach *L_cg* and how the coast-edge intercept δ₀ is partitioned between the two functions. It does not change the central finding: a near-coast water-table deepening of order 25--41 mm yr⁻¹ relative to the far field, declining over an inland reach of order 400--1000 m. Quoting the headline at 150 m from the shoreline, where the two forms agree to within 1.6 mm yr⁻¹, keeps the reported rate largely independent of that choice. The far-field level is not a climate background. *c_far* is separately identified but unstable with respect to the fitting window, as S12.3 sets out.

The headline values reported in the manuscript adopt the linear-capped fit for its Dupuit--Forchheimer interpretation of a finite inland reach. A further reason is that its far-field asymptote takes the same sign as the observed far-field trend, where the exponential's does not. The exponential returns +2.01 mm yr⁻¹ against an observed far-field trend of −6.35 mm yr⁻¹ over the same window. The linear-capped reach is also the more interpretable of the two. A capped-linear L_cg of 902 m is closer to the physical scale of the dune body than the exponential L_cg of 498 m, which is an e-folding length rather than a reach. AIC runs against that choice rather than with it, and this is stated here rather than left implicit. The exponential fit is reported as a sensitivity case.

The panel's climate covariate is an undecayed cumulative water balance, and it is not the best-fitting one available. Exponential accumulators of the same series, with half-lives from two to twenty-four months, all predict the water table better out of sample. So does a forward integration of the site's own state-space model. Substituting any of them leaves δ₀ within −28.6 and −31.4 mm yr⁻¹ and L_cg within 902 and 1067 m. The undecayed form is retained because the covariate is a nuisance term, absorbed by the within-well demeaning rather than reported as a parameter. Selecting it on predictive fit would introduce a free parameter into a published estimate. The ranges given here are the specification uncertainty on δ₀ and *L_cg*.

### []{#anchor-29}S12.5 C5 out-of-sample sentinel

The C5 Coastal Forest well NW9 lies 419 m from the eroding shoreline. It shows a decline of −32.7 mm yr⁻¹ (p = 0.002, R² = 0.41, n = 20 years, from *25_02_per_well_summer_min_slopes.csv*). NW9 is under canopy and is excluded from the forest-free regression. It therefore functions as an out-of-sample sentinel: it tests the fitted gradient at a near-coast position without contributing to it. Under the headline linear-capped fit, the gradient at 419 m predicts a coastal-retreat contribution of −16.87 mm yr⁻¹. That leaves −15.85 mm yr⁻¹ of the observed decline unaccounted for by distance to the shoreline. No climate background closes that gap. The two cluster-independent terms are the trend contribution carried by the cumulative water-balance covariate, +2.95 mm yr⁻¹, and the fitted far-field asymptote c_far, −0.30 mm yr⁻¹. Their sum is positive, so the remainder unexplained at this well is larger still, at −18.50 mm yr⁻¹. The substrate-position amplification developed in Section 5.2 of the manuscript addresses that remainder.

## []{#anchor-30}S13. Forest-interception drawdown reach (Figure 18)

Section 4.11 of the main manuscript renders the inland reach of forest-interception drawdown as a physical decay length (20_spatial_figures.py for the figure). This reach is the distance over which interception-driven recharge suppression at the plantation boundary persists in the down-gradient open dune. The calculation is a Dupuit-style drainage length:

> λ = √( *Kb* / (*S*y · β₃) )

where λ is the inland decay length, *K* the hydraulic conductivity, *b* the saturated thickness, *S*y the specific yield and β₃ the drainage coefficient (in daily units). The expression is the characteristic length over which a head perturbation at the source decays in a homogeneous, fixed-base unconfined aquifer.

The parameters used in Figure 18 are taken from C3 Western Residual, the open-dune cluster immediately down-gradient of the plantation boundary. They are: *Sy = 0.298 (C3 per-well median of the Approach B event estimates, 18_wtf_01_well_sy_estimates.csv, Section S10.4); β₃ = 0.0616 month⁻¹ ≈ 2.02 × 10⁻³ day⁻¹* (C3 cluster-mean, Section S6.2); *K* = 6 m day⁻¹ (Betson et al., 2002, Section S2.1); and *b* = 5 m (nominal saturated thickness). The saturated thickness is uncertain by a factor of two or more, given the absence of cored aquifer-thickness data. The geophysics of Bristow, 2002, indicates 12--27 m in the forest interior, but the open-dune thickness immediately south of the plantation boundary may be lower.

With these inputs, λ ≈ 220 m (drawdown_lambda in 20_report_numbers.csv, quoted to the nearest 10 m). The contours on Figure 18 should be read as an order-of-magnitude diagnostic of the inland reach, not as a calibrated prediction. λ scales as √(Kb). Across the conductivity range reported for dune sand (2--20 m day⁻¹) it spans roughly 130--410 m. Across a saturated thickness of 3--8 m it spans 170--280 m. The order-of-magnitude conclusion holds across that range: forest-interception drawdown reaches of order 200 m beyond the plantation boundary, not across the whole site. The calculation carries canopy interception alone. It is therefore an upper bound on the reach of the forest effect beyond the canopy, and a lower bound on its magnitude.

This is the only output of the framework that depends on *K*. Every other coefficient surface, residual field, water-balance partition, *S*y estimate, coastal-retreat gradient and diagnostic synthesis presented in the manuscript is derived without a *K* estimate (Section 5.6 of the main manuscript). A measured *K* would tighten only the Figure 18 reach calculation. It would come from slug tests at representative wells per cluster, the priority future field measurement.

The empirically fitted coastal-retreat reach (Figure 19 of the manuscript) is *not* an analogue of the Figure 18 reach in this sense. The coastal-reach length *L_cg* is fitted directly from the panel regression (Section S12), and *K* and *b* do not enter its derivation. The forest and coastal reaches are therefore methodologically distinct. Figure 18 is a forward calculation from independent SSM and literature parameters. Figure 19 is a back-calculation from observed water-table trends. Section 5.6 of the main manuscript discusses the implications.

## []{#anchor-31}S14. Software, parameters and reproducibility

The full analysis pipeline is open source and version-controlled on GitHub at github.com/newbroman/Newborough_Hydrology (commit XXXXXXX at submission). A versioned snapshot is archived on Zenodo at DOI 10.5281/zenodo.19567643. It holds the code, the author-collected input data, and every output CSV referenced in this document. The pipeline release is recorded in the pipeline_release field of outputs/pipeline_manifest.json. The Zenodo deposit is the citable, immutable reference. The GitHub repository carries any subsequent updates.

**Software environment.** Python 3.12.3. The complete, version-pinned environment is specified in requirements.txt. Key packages are NumPy 2.4.6, SciPy 1.17.1, pandas 3.0.3 and statsmodels 0.14.6 (numerical and statistical processing); GeoPandas 1.1.3, Rasterio 1.5.0, Shapely 2.1.2 and pyproj 3.7.2 (spatial); and Matplotlib 3.10.9 (plotting). Random seeds for every stochastic step (bootstrap resampling, cluster stability) are defined centrally in utils/config.py. This gives byte-equivalent reproduction.

**Cartographic-context overlays.** Site-overview cartography combines pipeline outputs with cartographic-context overlays, loaded by the pipeline from KML files in data/. The data/streams.kml overlay is the topographic drainage network. It is drawn only where it is set against the groundwater flow field (Figures 15 and 16). It was produced in QGIS 3.34.4-Prizren using the GRASS provider, tool r.watershed, with multiple-flow-direction routing and a 4000-cell channelization threshold (≈ 16,000 m² minimum contributing area). The input was the merged 2 m LiDAR DEM (mergeddem.tif, EPSG:27700) used throughout the pipeline. The line network was extracted via r.to.vect and exported to KML. It was then post-processed to remove drainage paths below 0 m AOD (intertidal/foreshore), by sampling the DEM at each line vertex. The masking utility is included in the repository as a one-shot data-preparation step. Other context overlays (Features.kml, site_boundary.kml, clearfell.kml) are similarly produced or maintained in GIS, and are loaded by the pipeline via src/utils/map_utils.py add_kml_features(). The Python pipeline reproduces the analytical work; these GIS files are cartographic context.

**Pipeline orchestration.** The pipeline is run as a single command (python run_analysis.py), which executes the analytical steps in canonical order. Each step writes its outputs to a step-specific subdirectory under outputs/. Where appropriate, it also updates the canonical pipeline parameters file (Section S2.2). A full run on a standard workstation completes in approximately 30 minutes.

**Pipeline parameters table.** Headline values used in this document, all read live from the canonical CSVs at the time of submission:

  ------------------------------------------- --------------------- --------------------------------------------
  Network size (reference)                    66 wells              01_wells_provenance.csv
  Drainage datum *z₀*                         3.7 m                 pipeline_scenario_params.csv
  HEADLINE_LAG                                0                     pipeline_scenario_params.csv
  Forest interception                         0.24                  Freeman (2008), config.py
  C1--C5 β₁, β₂, β₃, *R*²                     (see Section S6.2)    03_03_cluster_mechanistic_coefficients.csv
  Cluster *S*y                                (see Section S10.2)   17_wtf_01_sy_estimates.csv
  Coastal δ₀, *L_cg*, *c_far* (forest-free)   (see Section S12)     25_01_panel_fit_parameters.csv
  NW9 decline                                 (see Section S12.5)   25_02_per_well_summer_min_slopes.csv
  Hydraulic conductivity *K*                  6 m day⁻¹             Betson et al. (2002)
  ------------------------------------------- --------------------- --------------------------------------------

**Data availability.** The dipwell water-level records and the well location/elevation data analysed here were collected by the author. They are deposited, in cleaned form, in the Zenodo archive alongside the code (Newborough_Cleaned_For_Model.csv, Well_locations_height.csv). The RAF Valley climate series are Met Office historic station observations: monthly rainfall, and the mean-temperature series used to derive Thornthwaite PET. They are © Crown Copyright, Met Office, and are available from the Met Office at https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/valleydata.txt under the Open Government Licence v3.0. They are not re-archived here. This dataset contains public sector information licensed under the Open Government Licence v3.0.

**Code availability.** All scripts, all output CSVs and figures, and a complete README.md are at github.com/newbroman/Newborough_Hydrology. The repository licence is MIT for code and CC-BY-4.0 for the author-collected data and figures. The author can be contacted at the address on the title page for any aspect of the analysis not covered here.

## S15. Supplementary references

[]{#supporting-information}[]{#anchor-32}References cited only in this SI document, not in the main manuscript:

> Calinski, T. and Harabasz, J. (1974) A dendrite method for cluster analysis. *Communications in Statistics* 3(1), 1--27.

> Crosbie, R.S., Binning, P. and Kalma, J.D. (2005) A time series approach to inferring groundwater recharge using the water table fluctuation method. *Water Resources Research* 41(1), W01008. doi:10.1029/2004WR003077.

> Liao, T.W. (2005) Clustering of time series data --- a survey. *Pattern Recognition* 38(11), 1857--1874.

> Milligan, G.W. and Cooper, M.C. (1985) An examination of procedures for determining the number of clusters in a data set. *Psychometrika* 50(2), 159--179.

All other references --- Akaike (1974), Bear (1972), Betson, Connell and Bristow (2002), Bristow (2002), Bristow and Bailey (2001), Curreli et al. (2013), Davy et al. (2006), Fetter (2001), Forgrave (2020), Freeman (2008), Freeze and Cherry (1979), Healy and Cook (2002), Hollingham (2026b, in preparation), Knotters and van Walsum (1997), Pye and Blott (2024), Ranwell (1958), Rao and Srinivas (2006), Rhind et al. (2001), Robins and Davies (2015), Rousseeuw (1987), Scanlon et al. (2002), Stratford et al. (2007), Ward (1963), Young (2011) --- appear in the main manuscript's reference list and are not duplicated here.

End of Supporting Information.
