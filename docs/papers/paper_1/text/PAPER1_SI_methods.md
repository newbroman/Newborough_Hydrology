<!-- GENERATED MIRROR of docs/papers/paper_1/PAPER1_SI_methods_v1_4.odt — do not edit.
     Regenerate with: python3 tools/refresh_mirrors.py -->

# Supporting Information

## Hollingham (2026), Paper 1 --- *A parameter-sparse state-space framework for aquifer characterization from long-term manual dipwell records: a 21-year case study at Newborough Warren*

This Supporting Information document gives the methodological detail underlying the analyses reported in the main text. It is self-contained: every parameter, equation, and design choice that supports a result in the manuscript is laid out here. Section numbers in the manuscript refer back to the headed sections here (S1--S16).

[]{#anchor}The pipeline and outputs are archived in full (Section S15). The headline numerical values used in the manuscript are reproduced live from the pipeline output CSVs cited at the foot of each section, and are unchanged at the time of submission.

### S13.6 Seasonal robustness (spring mean)

The gradient regression above uses the annual summer minimum (Jun--Sep) as the per-well response. It was repeated with the annual spring mean (Mar--May) as a second per-well metric through the identical code path (compute_per_well_slopes(metric=...), strict 3-of-3 monthly completeness). The panel fit and the coastal-retreat gradient are all-season and metric-independent --- the same forest-free linear-capped fit is applied to both metrics --- so any spring--summer difference in the decomposition is attributable to the response metric, not to a refitted gradient. That is a property of the procedure, not evidence that the gradient is season-invariant; the test below shows that it is not.

The gradient is itself seasonal. A full-panel season × δ(d)·t interaction (11,834 observations, one model) fits δ(d)·t·(1 + γ·S), with S = 1 in Mar--May, and returns γ = +0.135 ± 0.056 (t = 2.43, p = 0.015) for the linear-capped form and +0.143 ± 0.056 (t = 2.54, p = 0.011) for the exponential. Both forms reject season-independence at the 0.05 level, and both put γ above zero: the coastal-retreat drift rate is about 13--14 % steeper in Mar--May than over the rest of the year. That the estimate is significant, of the same sign and of near-identical magnitude under both decay forms indicates a seasonal modulation of the gradient itself rather than an artefact of the assumed functional form. The MAM-only refit of the panel (a sensitivity block in 25_01_panel_fit_parameters.csv) points the same way: it loses power as expected (δ₀ SE roughly doubles, 1.91 to 3.43 mm yr⁻¹) but returns a steeper spring coast-edge anomaly than the all-season fit (δ₀ −31.2 against −29.22 mm yr⁻¹), a change of about 7 % in the same direction as γ. What remains year-round is the boundary effect itself: C5 Coastal Forest --- the out-of-sample sentinel of S13.5 --- declines in both seasons (summer −35.9, spring −37.9 mm yr⁻¹), so γ modulates the drift rate rather than switching it off outside spring. The all-season gradient is therefore a season-averaged quantity, not a season-independent one, and applying it unchanged to a spring metric understates the spring coastal contribution: the ≈ 41 % of C5\'s spring decline that it attributes to coastal retreat is a lower bound. Full seasonal results are in the report\'s Supplementary Material, Note S8.

## Contents

  --------------------------------------------------------------- -----------------
  S1. Field protocol, data preparation, and date semantics        2
  S2. Constants and configuration                                 4
  S3. Behavioural clustering and the *k* = 5 partition            5
  S4. Pearson affinity audit and spatial confidence               7
  S5. The state-space model --- displacement formulation          7
  S6. SSM regression: per-well and cluster-mean fits, with LCSC   10
  S7. SSM vs traditional linear model (benchmarking)              12
  S8. Spatial interpolation of SSM coefficients                   13
  S9. Residual-field diagnostics                                  14
  S10. Water-balance decomposition                                15
  S11. Water-table-fluctuation specific yield                     16
  S12. Mean water-table surface and the Darcy flow field          18
  S13. Coastal-retreat gradient regression                        19
  S14. Forest-interception drawdown reach (Figure 19)             21
  S15. Software, parameters and reproducibility                   22
  S16. Supplementary references                                   23[]{#contents}
  --------------------------------------------------------------- -----------------

## S1. Field protocol, data preparation, and date semantics

The 88-well manual dipwell network is read monthly by the author. Readings are taken at the **end of each month** --- typically the last day of that month, or the first day or two of the following month. Each reading is the water level *for the month just ended*: a measurement taken on 1 May 2026 represents the **April 2026** water level. Climate data from RAF Valley Meteorological Station (53°14′32″N, ≈16 km from the site) is a monthly total for the same calendar month: rainfall *P* (mm), and minimum and maximum temperatures from which monthly Thornthwaite PET is computed at the RAF Valley latitude (53.25°).

Thornthwaite (1948) defines the heat index *I* as the sum of the monthly contributions *i* = (*T*/5)\^1.514 over the calendar year. Here the sum is taken over the trailing twelve months ending at the month being computed. That window contains exactly one of each calendar month and is therefore a full annual heat sum, but unlike the calendar-year form it is defined at every month of a record that does not end in December, and the PET of a given month does not depend on the months that follow it. The monitoring record is live and is analysed part-way through a calendar year, where the calendar-year sum is undefined: applied to the two months of 2026 available, it returned *I* = 3.1 against a normal near 45 and a February PET of 66.8 mm against a range of 13.0 to 25.7 mm observed for that month at this station. Over the analysis period the two forms are equivalent in central tendency, differing in monthly PET by a median of 0.00% (5th to 95th percentile ±5.5%); individual months can differ by up to 16.6%. This is a departure from the published method rather than a correction to it, and is recorded as such.

**Bucketing.** Readings on physical dates ≤ day 15 of month *M* are bucketed into month *M*−1 because they belong to the previous month's water table. Readings on physical dates \> day 15 of month *M* are bucketed into month *M*. The cutoff is at day 15 because field readings are nearly always taken either within the first week of a month or on the last day of the preceding month; day 15 is comfortably in the middle of the gap.

**Date semantics.** Every monthly timestamp in the pipeline is recorded in YYYY-MM-01 date format. The -01 day component is a formatting convention used to make monthly records machine-readable as dates; it does not refer to the 1st of the month. A row labelled 2007-07-01 is "July 2007": it contains the end-of-July water level and July's climate totals.

A concrete example for well CEH9, row 2007-07-01:

  -------------- ---------- ------------------------------------------------------------------
  *h*(*t*)       −0.610 m   End-of-July reading
  *h*(*t*−1)     −0.440 m   End-of-June reading
  Δ*h*           −0.170 m   Water-table change *during* July
  *P*            101.9 mm   July rainfall total
  PET            98.5 mm    July Thornthwaite PET
  *h*disp,prev   3.260 m    3.7 + (−0.440), displacement above drainage datum at end of June
  -------------- ---------- ------------------------------------------------------------------

The state-space model (Section S5) uses this row to explain July's 170 mm drop using July's rainfall, July's PET, and the water-table position at the start of July (= end of June).

**Above-Ordnance-Datum invariance.** The above-Ordnance-Datum (mAOD) water-table elevation is a physical quantity independent of the ground surface above it. Removing material from the surface does not move the water table; the mAOD reading is the same before and after. Era-specific data handling is therefore only required where depth-below-ground is the quantity of interest, not where mAOD water-table elevations are being averaged or compared.

The data-preparation step (01_data_prep.py) reads the three raw inputs --- Newborough_Cleaned_For_Model.csv (water-table records), Well_locations_height.csv (well coordinates and DEM-derived ground elevations), RAF_Valley_Climate.csv (monthly rainfall and temperatures) --- and produces the cleaned, bucketed, masked frames consumed by every downstream script.

### []{#anchor-1}S1.3 Cleaning and gap rules

Water-table records are screened for sentinel values and obvious measurement errors. Short interpolation gaps (a single missing month with valid neighbours) are filled by linear interpolation, with the gap limit set to limit = 1; 72 cells out of approximately 110,000 well-month observations across the 88-well network are filled by interpolation; the remainder are observed.

### S1.4 Reference-network selection

The reference network (66 wells, Section S3) is the subset of the 88-well network that meets all of: - record start ≥ 2005 and record continuing through REFERENCE_CUTOFF_DATE (2026-02-01); - not on the blacklist of wells with known tidal influence (notably the pdfs well at the south-eastern shore); - not within the clearfell-impacted zone (used for the BACI analysis in Paper 2 but excluded from Paper 1's network-mean coefficients).

[]{#s1.4-reference-network-selection}The extended network adds the remaining 22 wells (clearfell-zone, shorter records, scraped wells) for spatial visualization only; coefficients fitted to extended-network wells are reported only where stated, and the per-cluster coefficients in Table 1 are reference-network only.

### []{#anchor-1}S1.5 Output

Cleaned monthly per-well frames, the climate frame, and the canonical pipeline parameters CSV are written to outputs/01_data_prep/. The well-provenance audit (01_wells_provenance.csv) records membership in each network and lists the reason for any exclusion, supporting reviewer reproducibility.

## []{#anchor-1}S2. Constants and configuration

All pipeline constants and the canonical runtime-parameters file are described here. The cluster partition that determines which wells belong to which group is the output of the behavioural clustering step (Section S3); the full table is given there.

### []{#anchor-1}S2.1 Constants

All values that are constant across the pipeline are defined in a single centralized configuration file, so that any change propagates everywhere and no script can redefine a value locally. The constants used in Paper 1 are:

  ---------------------------- ------------ ------------------------------------------
  DRAINAGE_DATUM               3.7 m        Sensitivity analysis (Section S5.4)
  HEADLINE_LAG                 0            Field-convention bucketing (Section S1)
  FOREST_INTERCEPTION          0.24         Freeman (2008), Newborough Corsican pine
  FOREST_CIDS                  (4, 5)       *k* = 5 partition; forested clusters
  REFERENCE_CUTOFF_DATE        2026-02-01   Network selection (Section S1)
  RAF_VALLEY_LAT_DEG           53.25        53°14′32″N
  Hydraulic conductivity *K*   6 m day⁻¹    Betson et al. (2002) tracer test
  ---------------------------- ------------ ------------------------------------------

The 24% Corsican pine canopy-interception fraction is from Freeman (2008), the most spatially proximate canopy-interception measurement available for the Newborough plantation. *K* = 6 m day⁻¹ is from the single tracer test reported in the contemporaneous CCW groundwater-modelling study; it is required only in the Figure 19 forest-drawdown reach calculation (Section S14) and does not enter any other framework output.

### []{#anchor-1}S2.2 Canonical pipeline parameters file

A single canonical table of pipeline parameters, pipeline_scenario_params.csv, is written by the data-preparation step (Section S1) and updated in place by the downstream steps that fit new parameter values (the SSM regression, the BACI auxiliaries, and the WTF specific-yield estimation). Every downstream step reads its pipeline parameters from this file rather than from a hardcoded value, which rules out a category of inconsistencies that can otherwise propagate silently through long pipelines.

## []{#anchor-1}S3. Behavioural clustering and the *k* = 5 partition

### S3.1 Distance metric and linkage

Cluster identification (02_clustering.py) operates on a pairwise distance matrix between per-well hydrographs. The metric is one minus the Pearson correlation coefficient between any two wells' monthly time series over their common record window. A small minimum-overlap requirement (≥ 36 months) prevents short pairs from dominating; pairs that do not meet it are flagged as undefined and the affected well is excluded from clustering rather than imputed.

[]{#s3.1-distance-metric-and-linkage}Ward's hierarchical linkage (Ward, 1963) is then applied. Ward's criterion minimizes the increase in within-cluster sum of squares at each merge, which produces compact, well-separated clusters when the underlying data have structure. The choice of Ward over alternatives (single, complete, average linkage) reflects its well-attested performance on behavioural time-series data (Rao and Srinivas, 2006; Liao, 2005) and its tendency to produce spherical, balanced clusters of comparable size (Milligan and Cooper, 1985) --- desirable for downstream interpretation against physical substrate units.

### []{#anchor-2}S3.2 Cluster-count selection

The clustering literature offers several internal-validity indices for choosing the cluster count *k*. The two used here are the Rousseeuw silhouette coefficient (Rousseeuw, 1987) and the Calinski--Harabasz pseudo-*F* statistic (Calinski and Harabasz, 1974). Both are evaluated for *k* in {2, ..., 8}. Each curve has its own maximum and the maxima do not generally agree; this is a known property of internal validity indices applied to real data.

For Newborough the silhouette curve maximizes at *k* = 2 (\~0.41) and falls monotonically to *k* = 8 (\~0.18). The Calinski--Harabasz curve also favours small *k*. By the internal-validity criterion alone, the best choice would be *k* = 2: a single eastern--western split.

This was not adopted. The internal-validity indices reward separability; they are agnostic to the physical interpretability of the resulting clusters. A *k* = 2 partition collapses C4 Main Forest into either the eastern (C1, C2) or the western (C3) block depending on which well dominates the merge order, losing the canopy-interception signature that drives the management interpretation. *k* = 4 collapses C5 Coastal Forest into C3, losing the coastal-retreat signature. The Coastal Forest cluster is small (*n* = 5) and lies at the edge of the network, where bootstrap stability is fragile (Section S3.5), but its physical distinctness --- Corsican pine on the coastal sand body, with the most rapid recent water-table decline in the network --- is the basis on which it is retained as a separate cluster.

This study therefore selects *k* = 5 on a physical--mechanistic basis rather than on an internal-validity-index basis, and reports the indices transparently. The decision is taken openly in Section 3.2 of the main manuscript and is also reflected in the Pearson affinity audit (Section S4), which shows that C5 wells sit at the edge of cluster space rather than in its interior, but that the edge position is consistent and reproducible across the 21-year record.

### []{#anchor-2}S3.3 The k = 5 partition table

The reference network is partitioned into five behavioural clusters by Ward's linkage on correlation distance between cluster-mean hydrographs (Section S3). The cluster IDs and labels are:

  --- --------------------- ---- --------------------------------------------------
  1   C1 Lake Edge          7    Lake-adjacent (Llyn Rhos-Ddu), finer sediments
  2   C2 Dune               24   Mature open dune, eastern block
  3   C3 Western Residual   21   Deep aeolian sand, western block
  4   C4 Main Forest        9    Corsican pine on deep sand, northern ridge flank
  5   C5 Coastal Forest     5    Corsican pine, coastal margin
  --- --------------------- ---- --------------------------------------------------

Membership counts (canonical *k* = 5 partition under the live data-preparation pipeline) total 66 wells in the reference network. The extended network of 22 additional dipwells is used for spatial visualization and BACI work but is not part of the partition. Llyn Rhos-Ddu is treated as a fixed-head boundary feature rather than a behavioural cluster.

### S3.4 Canonical ID anchoring

[]{#s3.4-canonical-id-anchoring}Ward's linkage produces clusters in an arbitrary integer-numbering order that depends on the merge sequence. To make cluster IDs stable across pipeline runs and across partition changes, the clustering step carries a lookup table mapping each canonical cluster ID to one or two anchor wells whose membership identifies the cluster. After Ward returns its raw partition, the clusters are re-numbered so that the anchor wells fall in the expected ID, and an automated check confirms that the renumbering succeeded. This convention has the practical effect that "C1" refers to the same physical cluster across all pipeline outputs, irrespective of run order.

### []{#anchor-2}S3.5 Stability

Bootstrap resampling of the per-well hydrograph set returns the same five clusters with stable cluster cores. The procedure draws 1000 random samples (with replacement) from the 66 reference-network wells, repeats the Ward\'s-linkage clustering on each draw, and counts the proportion of bootstrap draws in which each well is co-assigned to its canonical-partition cluster (02_04_bootstrap_stability_summary.csv). Four of the five clusters are highly stable, with median co-assignment above 0.97 --- 1.00 at C4 Main Forest, 0.99 at C5 Coastal Forest, and 0.98 at both C1 Lake Edge and C2 Dune. C3 Western Residual is the exception, at a median of 0.49: it is the most behaviourally heterogeneous cluster, and its members reassign more readily across bootstrap draws --- the resampling signature of the continuous substrate gradient identified in Section S4, along which wells near the cluster margins move between behavioural neighbours without the cluster cores dissolving. C5 Coastal Forest, despite having the smallest membership (n = 5), is among the most stable clusters rather than the least: its five wells behave consistently with each other and distinctly from the rest of the network (Section S4), and the anchor wells ceh16 and nw9 remain in C5 across all bootstrap draws.

## S4. Pearson affinity audit and spatial confidence

The clustering algorithm assigns each well to the cluster with whose centroid it has the highest Pearson correlation. The *strength* of that assignment --- how clearly a well belongs to its cluster, rather than sitting near the boundary between two --- is recoverable from the affinity matrix: each well's Pearson correlation against every cluster centroid.

A well with a high primary affinity and substantially lower secondary affinities is a *core member* of its cluster. A well with a primary affinity only slightly above its secondary is *gradational* --- it sits at the boundary between two behavioural patterns. The Pearson affinity audit (05_pearson_affinity.py, Figure 5 of the main manuscript) makes this structure visible at the well level.

The audit shows three patterns. First, the cluster cores are spatially compact and behaviourally distinct, with high primary affinities and substantially lower secondary affinities. Second, the boundary between C2 (eastern Dune) and C3 (Western Residual) is gradational rather than sharp --- several wells in the centre-east of the network have primary affinity to one cluster but a secondary affinity within 0.05 of the primary, indicating that they sit on a continuous substrate gradient between the two clusters rather than within a structural discontinuity. Third, C5 Coastal Forest is a tight core with the lowest affinity to any other cluster, indicating that even though C5 has only five members, those five behave consistently with each other and distinctly from the rest of the network.

The C2/C3 gradation is discussed at length in Section 5.1 of the main manuscript and is the basis for the "behaviourally coherent cluster on a continuous substrate gradient" interpretation of C3. It is also why the discussion uses "C3 transitional zone" rather than "C2/C3 boundary".

The output 05_pear_01_spatial_confidence_map.png is Figure 5 of the main manuscript. The underlying affinity matrix is in outputs/05_pearson_affinity/05_affinity_per_well.csv.

[]{#anchor-2}Across the 66 reference-network wells, the audit classifies 17 as Core (sitting cleanly in their assigned cluster, with Pearson margin above 0.05), 46 as Fuzzy (assigned cluster is the best match but the margin to the second-best is small), and three as Spy (k-means assignment and Pearson best match disagree): ceh4 and ceh21, both assigned to C3 Western Residual but matching C5 Coastal Forest by margins of 1.7 % and 0.9 % respectively, and nw13, assigned to C3 but matching C2 Dune by 0.3 %. Closer inspection shows ceh21 and nw13 to be persistent borderline cases with margins of around 1 % throughout the record. The ceh4 case is more interesting: its pre-2018 hydrograph preferred C5 by 1.8 %, but its post-clearfell (December 2017 onwards) hydrograph prefers its k-means assignment C3 by 3.1 % --- the full-record audit is dominated by the longer pre-clearfell period. The three borderline cases are documented but retained in their k-means assignments; Pearson margins within sampling noise are not a defensible basis for re-partitioning. The 96 % Core + Fuzzy share within the assigned cluster supports the partition as a reasonable behavioural grouping of the network.

## []{#anchor-3}S5. The state-space model --- displacement formulation

The state-space model (SSM) is the methodological core of the analysis. The cluster characterization, the specific-yield estimation, the water-balance decomposition, the residual field and the coastal-retreat gradient regression all rest on it.

### []{#anchor-4}S5.1 Equation

The fitted equation is

> Δ*h*(*t*) = β₁ · *P*(*t*) − β₂ · PET(*t*) − β₃ · (*D* + *h*(*t*−1))

where Δ*h*(*t*) is the change in water table during month *t* (m, signed; negative when the water table falls); *P*(*t*) and PET(*t*) are the rainfall and Thornthwaite PET during month *t* (m); *h*(*t*−1) is the water table at the end of month *t*−1 (m, signed; negative below ground surface); *D* is the drainage datum, *D* = 3.7 m (Section S2); and β₁, β₂, β₃ are positive coefficients fitted by ordinary least squares (no intercept).

The quantity *D* + *h*(*t*−1) is the displacement of the water table above the drainage datum at the start of month *t*. With *D* = 3.7 m and a typical end-of-previous-month head of −0.4 m, displacement is 3.3 m; with a deeper end-of-month head of −2.0 m, displacement is 1.7 m. The β₃ term says: the deeper the water table sits below ground at the start of a month, the smaller the drainage during that month --- consistent with Darcy's law for a shallow unconfined aquifer drained to a fixed lateral discharge horizon.

The equation is a multiple linear regression: three predictor variables (rainfall, PET, start-of-month displacement) and one response variable (Δ*h*). The three coefficients are estimated jointly by ordinary least squares (OLS), which finds the values that minimize the sum of squared residuals across all (well, month) observations in the regression sample. The fit returns each coefficient with its standard error and *p*-value, the overall regression *R*² (the fraction of monthly Δ*h* variance jointly explained by the three predictors), and the residual series at every observation.

### []{#anchor-4}S5.2 Sign conventions

All three β values are reported positive. Signs are baked into the design matrix, not into the coefficient values. In the design matrix the β₁ column is +*P* (a positive β₁ means rainfall raises the water table), the β₂ column is −PET (a positive β₂ means PET lowers the water table), and the β₃ column is −(*D* + *h*prev) (a positive β₃ means displacement above the datum drives drainage downward). A fitted β₁ ≤ 0 or β₂ ≤ 0 halts the pipeline because either is physical nonsense; β₃ \> 0 is soft-asserted (a negative β₃ is anomalous and worth investigating but does not halt the pipeline).

### S5.3 Why *h*(*t*−1) rather than *h*(*t*)

[]{#s5.3-why-ht1-rather-than-ht}The drainage term uses the water-table position at the end of the previous month, not the contemporaneous level, for two reasons. First, h(t) is the dependent variable through Δh = h(t) − h(t−1); using it simultaneously as a predictor would create simultaneity bias and break the interpretation of β₃. Second --- and physically --- drainage during a month is driven by the head at the start of that month, not the head at the end; the end-of-month head is the result of drainage, not its cause. The displacement at the start of month t equals the displacement at the end of month t−1, hence the h(t−1) form. The within-month mean head would in principle be a more faithful driver still, since total monthly drainage is the time-integral of a head-dependent flux and the start-of-month form is in effect its forward discretization; but the mean is not observed. With a single end-of-month reading it can only be reconstructed as ½·\[h(t−1) + h(t)\], which carries h(t) --- and hence Δh --- back into the predictor, reinstating the simultaneity the h(t−1) form is chosen to avoid while adding no information beyond the two endpoints. The two discretizations are in fact an exact reparameterization of one another on monthly data --- the mean-head form rescales β₃ by 1/(1 − β₃/2) and leaves the fit, residuals and cluster contrasts unchanged --- so the start-of-month choice costs nothing in fit, and only the simultaneity argument bears on it.

### []{#anchor-4}S5.4 Drainage datum

The 3.7 m drainage datum was selected to give comfortable β₃ identification at the forest clusters (C4 Main Forest, C5 Coastal Forest), where β₃ is hardest to pin down because the water table sits deepest below ground there. A sensitivity sweep over *D* compares the live empirical minimum *D* = 1.7 m --- the shallowest depth at which all five clusters simultaneously satisfy β₃ \> 0 with *p* \< 0.05 --- against the operating value *D* = 3.7 m. At the empirical minimum C4's β₃ *p*-value sits at the significance edge (0.040); at 3.7 m it drops to 0.0027, with C5 also gaining substantially (β₃ *p*-value from 4 × 10⁻¹¹ to 4 × 10⁻¹⁶, *R*² from 0.648 to 0.680). The trade-off is small *R*² penalties at C1 Lake Edge (−0.052) and C2 Dune (−0.029), where β₃ is over-determined and remains significant at *p* \< 10⁻²⁵ at either depth.

The role of the datum is to shift the reference for the drainage term. Without it (i.e. with *h*(*t*−1) instead of (*D* + *h*(*t*−1)) in the design column), the C3, C4 and C5 clusters produced negative β₃ estimates. This was a sign-convention artefact: it reflected that the OLS was correlating drainage with a quantity that crossed zero rather than staying on one side of a fixed reference. Setting the reference 3.7 m below ground places every observation comfortably on the positive side of the datum.

Δ*h* is invariant under the choice of datum (the datum cancels in first differences). β₁ and β₂ are also invariant. Only β₃ shifts numerically, in a way that preserves its physical interpretation as a Darcy drainage coefficient.

### []{#anchor-4}S5.5 Implementation: two levels of fit

The SSM is fitted at two distinct levels of aggregation and Paper 1 uses both. The distinction is material because the two fits address different questions and feed different downstream products. Section S6 maps the fits to the products explicitly; the rest of this subsection covers the construction of the design matrix, which is common to both.

**Cluster-mean fit --- the primary characterization tool.** A single OLS regression is run for each cluster on the cluster-mean hydrograph. The cluster centroid is constructed by averaging the water-table depths of cluster members month by month, producing one mean-depth time series per cluster; the SSM design matrix is then built from that centroid series and the shared climate forcing, and fitted by OLS. The result is one set of coefficients (β₁, β₂, β₃) per cluster, with the regression *R*² and per-coefficient *p*-values that anchor Table 1 of the main manuscript. Working on the centroid rather than on per-well-stacked rows is the standard behavioural-cluster characterisation approach: the cluster centroid is the canonical "average member" of the cluster, and fitting the SSM to it gives the coefficients that describe the cluster's collective behaviour without per-well noise. The cluster-mean fit is what underwrites the substrate-gradient interpretation of Sections 5.1--5.2, the lumped climate-storage contribution (Section S6.4), and the drainage decay half-life t½ = ln(2)/β₃ reported in Section 4.7.

**Per-well fit --- the spatial-products tool.** The SSM is also fitted independently at each well in the reference network, producing a separate (β₁, β₂, β₃) at every well. The per-well fits feed the spatial products: the coefficient atlas (Figures 11--13, three interpolated surfaces built from the per-well values), the per-well residual field (Figure 17, the per-well residuals from the per-well fit interpolated to a continuous surface), and the per-well water-balance decomposition (Section S10). Per-well fits are noisier than the cluster-mean fit because each is conditioned on a single well's record; per-well coefficient values are therefore best read in the spatial pattern they form across the network rather than at any single point.

**Common design-matrix construction.** The design matrix is built one (well, month) row at a time. For each row the well's water-table series is joined with the RAF Valley climate record on the bucketed monthly index, and Δ*h* and *h*disp,prev are computed, producing a row with columns *h*, *h*prev, Δ*h*, *P*, PET and *h*disp,prev. The per-well fit at well *w* runs OLS over the rows belonging to *w* alone, yielding a per-well (β₁, β₂, β₃). The cluster-mean fit at cluster *c* builds the same row structure from the cluster centroid --- the month-by-month mean of cluster members' depth series --- joined against the shared climate record, and runs OLS over those centroid rows. A three-coefficient OLS regression (no intercept) is fitted in either case and reports the coefficients with their standard errors, *p*-values from a two-sided *t*-test against zero, regression *R*², and residual series. The row construction and the regression are implemented in 03_state_space_model.py, which calls the shared helpers build_ssm_frame() and fit_ssm() from src/utils/model_utils.py; there is no reimplementation of the displacement calculation or the OLS fit elsewhere in the pipeline.

### S5.6 Residual serial correlation and inference validity

Because the SSM is a monthly time-series regression, the classical OLS standard errors that produce the coefficient *p*-values are valid only if the residuals are free of substantial serial correlation. This is tested directly (22_residual_lag_analysis.py, output 22_05_ssm_residual_autocorrelation.csv). The headline (no-intercept) SSM is refitted at each of the 66 reference wells and the residuals are examined: the median Durbin--Watson statistic is 2.20 (interquartile range 2.11--2.37) and the median lag-1 autocorrelation is −0.12. The residuals therefore carry a slight *negative* first-order autocorrelation rather than the positive persistence that would inflate significance --- a direct consequence of the drainage term −β₃·(*D* + *h*(*t*−1)), which acts as an error-correction term and absorbs the first-order persistence of the level series. Negative residual autocorrelation makes the OLS standard errors mildly conservative, not anti-conservative. A Ljung--Box test at lag 12 rejects white-noise residuals at 19 of the 66 wells; this reflects the *seasonal* residual structure characterized independently in Section S9.2 (winter--spring phased), not low-order persistence, and it is orthogonal to the coefficient standard errors.

As a robustness check the coefficient *p*-values are re-estimated with heteroskedasticity- and autocorrelation-consistent (Newey--West / HAC) standard errors, using the *n*-adaptive rule-of-thumb truncation lag L = floor(4·(n/100)\^(2/9)). Across the 198 coefficient tests (66 wells × three coefficients), the HAC and OLS significance verdicts at α = 0.05 agree in all but one instance --- β₂ at CEH25, which moves from *p* = 0.079 to *p* = 0.028, i.e. *toward* significance. No coefficient that OLS reports as significant is overturned under HAC. The classical-OLS inference underlying the coefficient tables is therefore sound. These diagnostics are run at the per-well level, the noisier of the two fits. The same battery applied to the five cluster centroids that carry the headline β table (Table 1; 22_06_ssm_cluster_mean_inference.csv, whose centroid β and OLS *p*-values reproduce 03_03_cluster_mechanistic_coefficients.csv exactly) leaves every coefficient significant under both OLS and HAC: none of the fifteen cluster-level tests (five clusters × three coefficients) changes verdict. The centroid residuals are close to white (Durbin--Watson 2.0--2.4) at every cluster except C4 Main Forest, where a mild *positive* autocorrelation (Durbin--Watson 1.66, φ = +0.06) still leaves all three coefficients HAC-significant. The cluster-mean fits, pooling every well in a cluster, are the better-conditioned of the two levels.

## **S5.7 Rainfall enters contemporaneously **

The recharge term uses the current month\'s rainfall, *P*(*t*), with no lag. This follows from the measurement protocol (Section S1): an end-of-month reading integrates the whole of that month\'s recharge, so the water-table change during month *t* is driven by month-*t* rainfall, and under the day-15 bucketing convention the correct pairing is same-month. The choice is confirmed by the lag diagnostic (03_04_lag_diagnostic.csv), which refits each cluster centroid at rainfall lags of 0--3 months: every cluster maximises R² at lag 0 by a wide margin (R² 0.68--0.81 at lag 0, falling to 0.04--0.38 at lag 1 and lower thereafter), and β₁ turns non-significant and sign-incoherent at the longer lags. Contemporaneous rainfall is unambiguously the correct predictor at the monthly timestep.

## []{#anchor-4}S6. State-space regression and the lumped climate-storage characterization

### []{#anchor-5}S6.1 Per-well and cluster-mean fits, and where each is used

Section S5.5 introduced the two levels of fit; both are implemented in 03_state_space_model.py. The mapping of each fit to the downstream products of Paper 1 is:

  ------------------------------------------------------------- -------------------------------------------------------- ----------------------
  Table 1 cluster mechanistic coefficients                      Cluster-mean                                             S6.2
  Lumped climate-storage contribution (LCSC)                    Cluster-mean                                             S6.4
  Drainage decay half-life t½ = ln(2)/β₃ by cluster             Cluster-mean                                             S6.2, main text §4.7
  Traditional-linear-model benchmarking                         Cluster-mean                                             S6.5
  Substrate-gradient interpretation (Sections 5.1--5.2)         Cluster-mean                                             main text
  Coefficient atlas, Figures 11--13 (β₁, β₂, β₃ surfaces)       Per-well, interpolated                                   S8
  Per-well residuals and residual field (Figure 17)             Per-well, interpolated                                   S9
  Per-well water-balance decomposition                          Per-well                                                 S9
  Coastal-retreat panel regression (Section S13)                Per-well (cumulative water-balance covariate)            S12
  Residual-field diagnostics (cross-correlation, climatology)   Per-well (residual series)                               S13
  Pearson affinity audit (Figure 5)                             Independent of SSM --- operates on raw hydrographs       S7
  Water-table-fluctuation specific yield                        Independent of SSM --- operates on recharge / Δ*h*       S10
  Mean water-table head surface (Figure 16)                     Independent of SSM --- operates on observed mean heads   S11
  ------------------------------------------------------------- -------------------------------------------------------- ----------------------

The cluster-mean fit is the primary characterization tool: Table 1 of the manuscript and the substrate-gradient discussion that runs through Sections 5.1, 5.2 and 5.5 are all carried by the cluster-mean coefficients. The per-well fit is the spatial-products tool: it lets the cluster characterization be projected as continuous surfaces across the site for visual and diagnostic interpretation.

Three of the Paper 1 outputs are independent of the SSM regression entirely. The Pearson affinity audit is the principal independent cross-check on the cluster structure: it tests, well by well, whether each dipwell sits closer to its assigned cluster centroid than to any other, using a Pearson correlation that does not depend on the SSM regression. Of the 66 reference-network wells, 63 sit in their assigned cluster as Core or Fuzzy members (96 %); three (ceh4, ceh21, nw13) are flagged as borderline cases where the Pearson best match disagrees with the k-means assignment by margins below 1.7 % --- documented but retained, since within-noise Pearson differences are not a defensible basis for re-partitioning. The water-table-fluctuation specific-yield estimation takes cluster identity as an input rather than testing it, but the distinguishably different cluster-level *S*y values that emerge (Section S11.2) provide a storage-side validation that the clusters mean something physically rather than being a statistical artefact. The mean water-table head surface is a third independent product --- independent of the cluster structure by construction, since clusters describe behaviour (how hydrographs move together) while the head surface describes where the water table sits (geometry and discharge boundary positions) --- and feeds the Darcy flow field in Section S12 rather than the cluster argument. The justification for the cluster framework rests on the Pearson affinity audit, with WTF *S*y as a supporting line of evidence.

### []{#anchor-6}S6.2 Cluster-mean coefficients

The full per-cluster (β₁, β₂, β₃) values, their standard errors and *p*-values, regression *R*², sample sizes *n* and lumped climate-storage contributions (LCSC %, defined in S6.4) are reported as Table 1 of the main manuscript and are read live from 03_03_cluster_mechanistic_coefficients.csv. The substantive interpretation --- the physical meaning of each coefficient, the direction of the cluster-to-cluster contrasts, and the comparison of C4 with C5 --- is developed in Section 5.2 of the main manuscript.

### []{#anchor-6}S6.3 Caveats on OLS coefficient values

[]{#anchor-6}The cluster-mean coefficients are well-determined within the OLS framework: regression *R*² values lie between 0.68 and 0.81, the per-coefficient *p*-values are all very small (Section S6.2, Table 1 of the manuscript), and bootstrap resampling of the within-cluster wells gives tight confidence intervals on each (β₁, β₂, β₃). The interpretive caveat is not about coefficient accuracy in that statistical sense but about the *scope* of what the coefficients represent.

First, the coefficients are lumped cluster-mean responses, not point-flux measurements. β₁ is the system-aggregate sensitivity of monthly Δ*h* to rainfall, integrated over the cluster\'s heterogeneity, not a point recharge efficiency at any particular location; β₂ and β₃ are analogous lumped responses. Two wells from the same cluster need not share a common (β₁, β₂, β₃) --- the per-well fits show modest within-cluster variation around the cluster mean --- and a literal reading of the cluster coefficient as the value at any individual well over-extends the claim.

Second, the SSM is linearised --- it assumes additive superposition of recharge, atmospheric draw and drainage. Real shallow-aquifer systems have nonlinearities (soil-moisture deficit thresholding recharge, depth-dependent ET access, hysteresis in the unsaturated zone) that the lumped monthly fit averages over. The high *R*² values say the linearisation works at monthly timestep --- much of the variance is recovered by a three-coefficient linear model --- but they do not say there is no nonlinearity to find. The residual climatology (Section S9.2) shows systematic seasonal structure at the cluster level rather than month-to-month random variation, consistent with residual nonlinearity in the recharge term, the atmospheric-draw term, or both.

Third, at monthly timestep *P*, PET and *h* co-vary during recharge events. Collinearity between regressors widens the practical confidence interval on each individual coefficient relative to the OLS standard error, without inflating the point estimate in a known direction. The cluster-mean fits mitigate this by averaging over wells with slightly different individual covariances, but the issue is in principle present in any lumped state-space model fitted by OLS (Knotters and van Walsum, 1997; Healy and Cook, 2002).

The practical implication is that the *ranking* of clusters by each coefficient --- C4 has the highest β₂; the forest clusters have the lowest β₁; C1 has the highest β₃ --- is robust to all three caveats. Cross-cluster contrasts at this level reflect the substrate, vegetation and topographic differences between clusters, which the SSM is designed to detect. Absolute coefficient values should be interpreted as lumped cluster-mean responses, not as instrument-equivalent calibrated fluxes. The main manuscript Section 5.2 notes the same scope in the context of the β₂ ranking --- that cross-cluster β₂ comparisons rest on the ordering and the relative magnitudes, not on absolute flux interpretation.

### []{#anchor-7}S6.4 Lumped climate-storage contribution

The lumped climate-storage contribution (LCSC) is the fraction of monthly Δ*h* variance explained by climate forcing alone, conditional on the start-of-month displacement. It is computed from a nested fit that fixes β₃ at its cluster-mean value and reports the fraction of total variance attributable to the (β₁·*P* − β₂·PET) component versus the residual. Per-cluster LCSC values are reported alongside the cluster-mean coefficients in Table 1 of the main manuscript; the relative ordering across clusters is interpreted in Section 5.2.

## S7. SSM vs traditional linear model (benchmarking)

The SSM's third coefficient β₃ --- the drainage feedback term --- is what distinguishes it from a generic climate-only linear model. Whether it earns its place is the question the TLM benchmark (08_model_benchmarking.py) addresses, by fitting a structurally simpler counterfactual at every reference well and comparing performance.

The TLM is the simplest unphysical alternative:

> Δ*h*(*t*) = α + β₁ · *P*(*t*) − β₂ · PET(*t*)

--- rainfall, PET, and an intercept α; no drainage feedback. The intercept absorbs any constant lateral subsidy or systematic offset that the SSM's β₃ term would otherwise represent. The TLM therefore has one degree of freedom more than the SSM (the intercept) but lacks the drainage feedback. This makes the comparison conservative: if the SSM outperforms the TLM, it does so despite the TLM's extra fitted parameter.

The TLM is not proposed as a published model and is not claimed to be optimal in any sense. It is a deliberately weak counterfactual that quantifies how much explanatory power the SSM contributes beyond a structurally simpler unphysical baseline.

At each well in the reference network (excluding three with inconsistent records that fail the benchmarking data-quality bar), both models are fitted by OLS on the most recent 100 aligned months. Two performance metrics are reported per well. The *one-step* *R*² takes the model's Δ*h* prediction added to the *observed* previous-month head, so each month is predicted with the truth at the previous step --- it measures diagnostic fit. The *iterative* *R*² and NSE perform an autonomous forecast from the window's first month forward, with each month's prediction feeding into the next as *h*prev --- this measures forecasting stability, which is the harder test because errors compound.

The SSM outperforms the TLM at every well in the reference network on the iterative metrics, and at almost every well on the one-step metric. The improvement is largest at the forest and western-residual clusters, where the displacement feedback is doing most of its work. The CEH6 showcase, reported in the main manuscript, illustrates the contrast: the TLM drifts to iterative NSE = −1.12 over the 100-month window, while the SSM holds at iterative NSE = +0.66. The headline ΔR² and ΔNSE per-well values are tabulated in 08_lcsc_model_stats.csv and rendered as cluster-coded spatial scatters in the same output directory.

[]{#anchor-7}The TLM benchmark is reported as a methodological diagnostic, not a competition: it demonstrates that the SSM's three-coefficient structure provides substantive explanatory power over a structurally simpler alternative, and quantifies that improvement spatially.

## S8. Spatial interpolation of SSM coefficients

The per-well β₁, β₂, β₃ values (Section S6.1) are interpolated to continuous surfaces across the site (07_spatial_coefficients.py) using inverse-distance weighting (IDW). The interpolation is purely geometric; the surfaces are *aggregators of point responses*, not the output of a calibrated distributed-flow model. This distinction is foregrounded in the manuscript and in the figure captions.

### []{#anchor-8}S8.1 IDW configuration

The IDW exponent is *p* = 2, a conventional choice that emphasizes local control. The grid is built on a LiDAR-derived 5 m digital elevation model resampled to a 40 m regular working grid; grid resolution sensitivity was checked against a 50 m grid (no qualitative change to the surfaces, mean coefficient values within 1% across the network).

### []{#anchor-8}S8.2 Masking

Only one monitoring well (CEH12) lies on the northern rock-ridge bedrock outcrop (the area above the 20 m AOD contour) and it has a short record, so any interpolated coefficient values shown there are extrapolations from the surrounding network rather than supported by data. The aquifer parameterization does not apply on bare metamorphic basement in any case, so the interpretation in the manuscript does not rest on the ridge-zone cells. Individual figures handle the ridge zone differently --- some render the extrapolated values for visual continuity, others mask them out --- and the relevant figure captions flag this where it matters for interpretation (notably Figure 17, the residual field). Cells outside the dune-field site polygon (sea, drift agriculture to the north, river) are masked from every figure.

### S8.3 Bandwidth and edge effects

[]{#s8.3-bandwidth-and-edge-effects}The IDW search bandwidth is set to include all wells within 1 km of each grid cell, or the nearest six wells, whichever is more permissive. The bandwidth-six-wells minimum prevents over-smoothing in the well-sparse north-western corner; the 1 km cap prevents under-smoothing in the dense central network. Edge effects (the south-western and south-eastern margins are bounded by the coast and the Menai Strait) are partly mitigated by the polygon mask but the surfaces remain less reliable within \~200 m of the coastal edge than in the interior. This is flagged in the relevant figure captions.

### S8.4 Coefficient atlas

[]{#anchor-8}[]{#s8.4-coefficient-atlas}The three interpolated coefficient surfaces (β₁, β₂, β₃) are presented as Figures 11--13 of the main manuscript and constitute the "coefficient atlas". The surfaces are intended as diagnostic readings of the cluster characterization extended continuously across the site; they are not flux maps and not predictions in any forward-modelling sense.

## []{#anchor-9}S9. Residual-field diagnostics

The state-space regression (Section S6) produces a per-month residual at every well: the portion of the observed Δ*h* not explained by the lumped balance β₁·*P* − β₂·PET − β₃·(*D* + *h*\<sub\>prev\</sub\>). Evaluated at each well\'s long-term mean climate and mean head, this steady-state balance --- modelled mean losses (β₂·PET̄ + β₃·h_disp̄) minus modelled mean recharge (β₁·P̄) --- gives a per-well residual in m/month (positive where modelled losses exceed modelled recharge, implying an unmodelled input; negative where the model over-predicts). Interpolating those per-well totals across the network by the same IDW procedure as the coefficient surfaces (Section S8) produces the residual field (Figure 17 of the main manuscript), which is the object analysed here. The per-well residual computation and the IDW interpolation are implemented in 20_spatial_figures.py. The formal partition of the modelled signal into its three SSM components is given in Section S10. Rainfall enters gross at every well, including the forested ones. Because the coefficients are fitted on gross rainfall and above-canopy PET, the canopy interception loss is already carried inside the fitted β₂·PET̄ term; subtracting it from rainfall as well would double-count it and insert a spurious positive residual at C4 and C5. The residual is not invariant to this choice, so the convention is stated explicitly here.

The residual field carries no spatial structure, with a small systematic negative offset: 64 of the 66 reference wells fall within ±0.01 m/month and 58 are negative, and residual magnitude is uncorrelated with position on either axis (Spearman ρ = +0.099 against Easting, p = 0.43; ρ = +0.111 against Northing, p = 0.37). The signed residual carries a weak west-to-east gradient short of conventional significance (ρ = −0.226, p = 0.07); the ridge-to-dune axis, on which a ridge-derived input would express itself, remains null (ρ = −0.171, p = 0.17). No well exceeds +0.02 m/month, the eight positive residuals all fall below +0.005 m/month and lie in the open dune and coastal forest, and the most negative residual falls at the open-dune well D7 (−0.0115 m/month), with the ridge-flank well CEH14 (−0.0106 m/month) close behind. The balance closes without requiring an additional flux. The two diagnostic tests below were run when the field was believed to be spatially structured; they are retained for what they establish about the limits of the monitoring design rather than as a discrimination among candidate mechanisms. Script 22, which characterises the residual series itself (per-well AR(1), Durbin--Watson and HAC standard errors, Section S5.6), establishes that the network\'s residuals are close to white: the AR(1) coefficient is small and negative at most wells (network mean φ = −0.126, median −0.115) and only two of the 62 wells exceed \|φ\| = 0.3.

### S9.1 Cross-correlation lag test (23_ridge_recharge_lag_test.py)

If a ridge-derived lateral input were present --- a Darcy-conveyed subsidy from the metamorphic bedrock ridge through the down-gradient open dune --- then a distance-dependent transport lag should be detectable: the time between a recharge event at the ridge and the corresponding response at down-gradient wells should increase systematically with distance. The cross-correlation lag test computes lagged correlations between (i) a ridge-zone composite recharge signal and (ii) the de-trended water-table series at each down-gradient well, identifying the lag at maximum correlation per well.

The test returns a null result: there is no monotonic distance-dependent lag structure across the down-gradient wells. Across the 50 of 63 wells with a significant cross-correlation peak, the Spearman rank correlation of peak lag against ridge distance is ρ = −0.005, p = 0.97. The peak lags are not, however, an observation of travel time. OLS residuals are orthogonal to the fitted rainfall regressors at lags 0 and 1 by construction, which imposes a methodological floor: 42 of the 50 significant peaks fall at lag 2, and 47 of the 63 wells peak at lag 1 or 2 irrespective of ridge distance, a pattern that persists under a Box-Jenkins pre-whitened reformulation. The statistic is therefore partly determined by the fitting procedure rather than by hydrology. What structure the lags do carry is organised by cluster rather than by ridge distance: all five wells peaking at lag 3 are C4 Main Forest (ridge distances 741--1068 m, peak r = +0.16 to +0.20), consistent with the slow storage turnover of the forest interior (t½ ≈ 36 months) rather than with a distance-dependent transport path. The three wells peaking beyond lag 3 carry the weakest correlations in the set (\|r\| ≤ 0.19, two of them negative) and reflect the flatness of the cross-correlation function rather than a resolvable delay.

[]{#anchor-9}This null result must be qualified by sampling frequency: monthly observations are an order of magnitude coarser than the days-to-weeks transit times expected for fracture-flow input from a metamorphic bedrock ridge, so a real ridge-derived lag could be invisible at this resolution. The null result therefore bears on what the present record can resolve rather than on whether the mechanism is operative.

### []{#anchor-10}S9.2 Seasonal climatology test (24_residual_seasonality.py)

If the residual field reflected systematic underestimation of summer evaporative demand at the forest margin --- for example, an under-resolved canopy-driven evaporative loss not captured by Thornthwaite PET --- then the residual field should peak in summer when those fluxes are active. The seasonal climatology test computes the monthly mean residual at each well across the 21-year record.

The test discriminates among candidate mechanisms. A summer-dominated peak confined to the forest clusters would indicate canopy-interception over-estimation or an analogous vertical-flux error. A pattern not confined to the forest clusters would indicate a different family of mechanism --- for example, recharge nonlinearity in the lumped monthly model, or an unmodelled non-vertical-flux input.

A cluster-stratified analysis aggregates the per-well climatology by the *k* = 5 partition and computes the winter-minus-summer contrast at each cluster, with bootstrap confidence intervals; the pipeline reports the complement, so signs are reversed in 24_05_diagnostic_summary.txt. The strongest contrast across the network is at open-dune C3 Western Residual (+7.5 mm, p = 0.0002), not at either forest cluster --- C4 Main Forest shows +6.4 mm (p = 0.098, marginal) and C5 Coastal Forest shows −2.8 mm (n.s.). This pattern is inconsistent with canopy-interception over-estimation as the sole driver: that mechanism would predict both forest clusters peaked and open dune flat, and the data show the reverse. A weak within-forest gradient (winter--summer contrast strengthens toward the ridge across 14 forest wells, *r* = −0.63) is consistent with a ridge-derived component but cannot be separated from a site-wide recharge term on the present evidence.

The full seasonal climatology has additional structure --- including non-trivial shoulder months --- that the winter-minus-summer contrast does not fully characterise; a detailed seasonal decomposition disaggregating the recharge and atmospheric-draw terms is the subject of a follow-up methodological treatment and is outside the Paper 1 scope.

### []{#anchor-11}S9.3 Ridge-zone extrapolation

The interpolated residual surface (Figure 17) extends over the rock-ridge bedrock outcrop on the northern boundary, which carries no reference monitoring wells; values shown there are extrapolations from the surrounding network and are not interpretable as residuals on bedrock. This is flagged in the Fig. 15 caption.

### []{#anchor-12}S9.4 Status of the residual field

The spatially-structured residual field on which this section was originally built did not survive correction of the Script 20 computation: the structure was an artefact of the two arithmetic defects described above, and the corrected field shows no spatial organisation on either axis. What the diagnostics establish is a bound on the monitoring design rather than a discrimination among mechanisms --- the seasonal test finds no summer signature that would indicate Thornthwaite misspecification, and the lag test could not have resolved a travel-time gradient had one been present. The residual field is therefore presented as a *structural diagnostic of where the lumped balance is insufficient*, not as a quantified flux map.

## []{#anchor-13}S10. Water-balance decomposition

The SSM equation (Section S5.1) is, equivalently, a monthly water-balance identity that partitions the change in water-table head into four terms: recharge driven by rainfall, atmospheric draw driven by PET, drainage proportional to displacement above the lateral discharge horizon, and a residual ε that the lumped balance does not explain. Paper 1 uses this identity at two levels: a headline cluster water balance at cluster-mean scale (Section S10.1, the primary analysis), and a per-well residual field analysed as a spatial diagnostic (Section S9).

### S10.1 Cluster water balance (primary analysis)

The cluster water-balance decomposition (16_water_bal.py) is the headline analysis. The β coefficients fitted by the SSM are monthly-scale: β₁ is the response (in metres of Δ*h*) per metre of rainfall *during a given month*, and analogously for β₂ and β₃. The natural product β₁·*P̄* is therefore a *monthly* recharge contribution when *P̄* is a monthly mean.

For each cluster the partition is computed at monthly timestep as

$${\text{recharge} = \beta_{1}}\cdot\overline{P}$$

$${\text{atmospheric draw} = \beta_{2}}\cdot\overline{\mathit{PET}}$$

$${\text{drainage} = \beta_{3}}\cdot\overline{h_{\text{disp}}}$$

where *P̄* and PET̄ are the long-term means of the RAF Valley monthly climate forcing (computed as sum across the record divided by number of months observed; identical across clusters), *h̄*\<sub\>disp\</sub\> is the long-term monthly mean of the cluster centroid displacement, and the β values come from the cluster-mean SSM fit (Section S6.2, 03_03_cluster_mechanistic_coefficients.csv). Each contribution is then scaled to annual units by multiplication by 12 (months per year) for reporting in Table 3 of the main manuscript and Figure 7 --- equivalent to multiplying the β coefficient by the long-term *annual* mean of the corresponding driver (record sum ÷ years on record). The two normalisations give the same annual contribution.

The water-balance closure follows from the SSM equation evaluated at long-term means. Δ*h̄* over the full record is approximately zero (no net trend on the cluster centroid hydrograph), so the four right-hand-side terms must sum to approximately zero:

> $$\Delta{\overline{h} = \beta_{1}}\cdot\overline{P}-\beta_{2}\cdot\overline{\mathit{PET}}-\beta_{3}\cdot{\overline{h_{\text{disp}}} + \overline{\epsilon}}\approx 0$$

The mean residual ε̄ is what the lumped SSM does not explain, and is what the closure result quantifies. Across all five clusters this closure error is within 2.5 % of total losses, i.e. the three β-weighted long-term means account for around 97.5 % of the long-term storage balance; the small remainder is the contribution of whatever the lumped three-term balance does not represent --- residual nonlinearity, spatial heterogeneity within the cluster, and error in the climate forcing among them. Its spatial structure is examined in Section S9, where the corrected per-well field is found to carry none.

### []{#anchor-13}S10.2 Canopy interception at the forest clusters

For C4 Main Forest and C5 Coastal Forest, Freeman (2008) measured canopy interception at 24 % of incident rainfall. The intercepted depth is

> *I*(*t*) = *i* · *P*(*t*)

where *i* = 0.24 is the canopy interception fraction (Freeman, 2008). This depth is not subtracted from rainfall anywhere in the fitted model. The cluster SSM (Section S6) is fitted on gross rainfall and on Thornthwaite PET computed above the canopy, so the interception loss is already carried inside the fitted β₂·PET̄ term. Interception is a partition of the available atmospheric energy budget rather than an additional demand on top of it: re-evaporation from intercepted rainfall on leaf surfaces, transpiration, and direct evaporation from the water table all draw on the same PET. Subtracting the intercepted depth from rainfall as well would count the same loss twice --- a defect that was present in the per-well residual computation of Script 20 until its correction on 2026-08-06 (Section S9), and that is not present in the cluster analysis reported here. The lower β₁ values at the forest clusters are therefore a fitted result rather than a consequence of any pre-adjustment: they reflect a damped water-table response to gross rainfall, consistent with Freeman\'s measurement of forest soil moisture at roughly half the open Warren\'s and a forest water table about 1.07 m deeper. The 24 % fraction enters the analysis only as a display partition. In the volumetric panel (Figure 7 panel b) the interception band is drawn identically on the input and the loss side, cancelling in the net surplus but making visible how much of the forest clusters\' rainfall is re-evaporated before it can reach the water table; it does not change total losses, the residual, or the balance at any cluster.

# **S11. Water-table-fluctuation specific yield**

Specific yield Sy --- the drainable porosity of the saturated medium near the water table --- is estimated in 17_wtf_specific_yield.py and is required to convert per-well water-table behaviour into a volumetric storage interpretation. It is also a substrate-character diagnostic in its own right, since a spatial gradient in Sy across an open dune-aquifer can indicate a corresponding gradient in sediment character (grain size, sorting, fines, weathering).

## **S11.1 The water-table-fluctuation method**

The water-table-fluctuation (WTF) method (Healy and Cook, 2002) estimates Sy from the relationship between net recharge and the corresponding water-table rise:

Sy = R / Δh

where R is the net recharge (rainfall minus PET, restricted to winter months when PET is small, R \> 0) and Δh is the corresponding water-table rise. Three parallel implementations of the method are used here; they agree closely at C3 Western Residual and on the coarse cross-cluster ordering, but diverge at C1 Lake Edge (Section S11.3).

**Approach A --- winter OLS.** The ratio above attributes the whole of the observed monthly change to recharge, whereas part of it is drainage occurring within the same month. Approach A removes that term first, using the state-space drainage coefficient: from Δh = (R / Sy) − β₃·\|h_prev\| it follows that R = Sy · (Δh + β₃·\|h_prev\|), so a no-intercept ordinary-least-squares regression of net recharge R against the drainage-corrected rise (Δh + β₃·\|h_prev\|) recovers Sy as the fitted slope directly. The fit is restricted to winter months (November--March) when Thornthwaite PET is below 25 mm month⁻¹ and net recharge approximates actual recharge well. This approach is statistically the most defensible (a single regression with a clear assumption) but provides limited uncertainty information beyond the regression standard error.

**Approach B --- event median**. An event-detection step identifies rising-limb months (winter months with positive recharge and positive Δh), computes Sy = R / Δh per event, and reports the cluster-level median together with its 25th and 75th percentiles. This is noisier per event but provides empirical uncertainty bounds and shows the within-cluster variability of the estimate.

**Approach C --- rapid recharge events**. A third estimator, after Crosbie et al. (2005), targets the same quantity by a route that shares the assumptions of neither of the first two. Approach A removes the drainage contribution to the observed rise mechanistically, using the fitted β₃; Approach B does not remove it at all and is correspondingly biased low. Approach C instead selects episodes in which the drainage contribution over the rise is negligible by construction, so that the uncorrected ratio is approximately unbiased. A candidate episode requires at least two consecutive prior months of falling or static water table (Δh ≤ 0), marking a drainage-dominated quasi-steady state; it begins at the first subsequent month with Δh \> 0, continues for at most two further months while the rise persists, and must accumulate a cumulative rise of at least 50 mm. For each qualifying episode Sy is the summed net recharge over the episode divided by the cumulative rise, retained only within the physically plausible interval 0.01 \< Sy \< 0.50 (the same interval applied per event in Approach B and in the per-well fits of Section S11.4). The cluster estimate is the median of qualifying episodes, with a 95 per cent confidence interval from 1000 bootstrap resamples of the episode set; episodes are non-overlapping. For the forested clusters the interception-corrected recharge of Section S11.2 is used, so the reported forest values are directly comparable with the corrected Approach B variant. Approach C is reported as an independent cross-check only and does not propagate to any downstream calculation.

## **S11.2 Cluster-level estimates**

Cluster-level event-median Sy estimates are reported as Table 4 of the main manuscript; all three approaches are read live from 17_wtf_01_sy_estimates.csv and compared in Section S11.3.

For the forested clusters (C4, C5) an interception-corrected variant is also reported. The correction applies Reff = (1 − i) · P − PET, with i = 0.24 (Freeman, 2008). The corrected values are the ones used in the Table 1 interpretation. The interception-corrected forest fits are reported by Approaches B (event median) and C (rapid-event). Approach A is not used for the corrected variant because the winter-only filter combined with the interception correction reduces the C4 and C5 sample sizes to the point where the no-intercept OLS becomes unstable; this is a sample-size limitation specific to the corrected forest case, not a general property of Approach A, which is reliable across all five uncorrected fits.

## **S11.3 Caveats**

Monthly resolution prevents isolation of individual storm events; the WTF estimates therefore conflate true gravity drainage with capillary-fringe release, and should be read as upper bounds on the storage coefficient rather than as point estimates of the gravity Sy alone (Healy and Cook, 2002; Scanlon et al., 2002). Slug tests or pumping tests at representative wells per cluster remain the gold-standard alternative; this would be the priority future field measurement. As with the SSM coefficients (Section S6.3), the robust and used quantity is the cross-cluster ordering, not the absolute magnitude. The three estimators converge closely at C3 Western Residual (0.35, 0.33, 0.33 for Approaches A, B, C) --- the value that anchors the Figure 19 forest-drawdown reach --- and Approaches B and C agree that C1 Lake Edge is the low-storage end (0.21 and 0.19), the higher winter-OLS estimate there (0.34) being consistent with the β₃ drainage correction over-correcting in the lake-buffered setting. Where an absolute Sᵧ nonetheless enters a downstream quantity --- the Figure 19 reach λ = √(Kb⁄(Sᵧ·β₃)) --- it is used as an order-of-magnitude input and reported accordingly (Section S14). The one genuinely method-dependent feature is the top of the ranking: the uncorrected winter-OLS fit places C5 highest, whereas the interception-corrected event and rapid-event estimates place C3 highest.

## **S11.4 Spatial Sy surface**

A per-well Sy field (18_wtf_spatial.py) is produced by computing per-event Sy = R / Δh at every well in the reference network and reporting the per-well median across rising-limb events (Approach B applied at the well level, with per-well 25th and 75th percentiles for uncertainty), retained within the same 0.01 \< Sy \< 0.50 interval. Forest clusters (C4, C5) carry the interception correction directly in the recharge term --- Reff = (1 − 0.24) · P − PET --- and forest values therefore carry additional uncertainty associated with the canopy correction (Freeman, 2008). The contrast with the SSM treatment in Section S10.2 is a consequence of the two methods\' structure rather than an inconsistency: the WTF method estimates recharge directly, so the canopy loss must be removed from rainfall explicitly, whereas the SSM is fitted on gross rainfall and above-canopy PET and therefore already carries that loss inside the fitted β₂·PET̄ term. Two wells are excluded from the contour interpolation on physical grounds: CEH12 sits on the bedrock ridge in a forested area, where the WTF Sy reflects bedrock rather than the sand aquifer, and CEH15 sits in a low-lying slack within the plantation where the local hydrology is not representative of upland forest sand. The per-well Sy values are interpolated to a continuous surface (Figure 8 of the main manuscript) by the IDW procedure of Section S8. The substrate-gradient interpretation of this pattern is developed in Section 5.2 of the main manuscript.

## []{#anchor-14}S12. Mean water-table surface and the Darcy flow field

### []{#anchor-15}S12.1 Mean head per well

A long-term mean water-table elevation is computed at each well in the reference and extended networks (20_spatial_figures.py) using all available observations at that well, and interpolated to the mean water-table surface shown in Figure 16 of the main manuscript (mAOD). For most reference-network wells this is essentially the full 21-year monitoring window; for extended-network wells, recently-installed wells, and wells with intervention-driven baselines (the scraped well CEH36), the available record is shorter and the mean correspondingly reflects a narrower time window.

The "all-record" approach has two known potential biases. (i) Wells with records ending or starting mid-year may produce means weighted toward different seasonal fractions; (ii) wells joining or leaving the network at different times alter the spatial composition of the contributing set. To check that the spatial pattern is robust to method, the per-well mean head was recomputed over a common reference period (water years 2010--2025) restricted to wells with substantially complete records over that period (≥ 12 of 16 water years with ≥ 10 months observed per year, qualifying 64 of 88 wells). The windowed and all-record per-well means are essentially identical: the median shift is −9 mm and the maximum is approximately 112 mm at a single well, with the per-well comparison points lying on the 1:1 line. The substantive spatial pattern --- the high levels centre-north and the low levels south-east --- is preserved. The maximum per-well shift was at nw9, the central well of the small (five-well) C5 Coastal Forest cluster; this is not an isolated outlier but the extreme of a coherent cluster-wide pattern, with all five C5 wells showing the windowed mean lying below the all-record mean, reflecting a comparatively high 2006--2009 sub-period in the coastal-forest zone that the windowing excludes. The effect on the C5 cluster-mean head is small (≈ 55 mm cluster-wide, of which nw9 contributes ≈ 14 mm) and negligible against the metre-scale inter-cluster head contrasts, so the substrate-gradient interpretation and the Figure 16 aquifer geometry are unchanged. The all-record approach is therefore retained as the primary method because it preserves full network coverage at the periphery; the windowed comparison is reported as a methodological check.

### S12.2 Spatial head surface

[]{#s12.2-spatial-head-surface}The per-well mean heads are interpolated to a continuous surface (Figure 16) by IDW (Section S8) on a 40 m regular grid masked to the dune-field site polygon plus the rock-ridge zone (heads are observable at the ridge in principle, unlike SSM coefficients). The interpolated head surface is broadly smooth, with the water table sitting close to the ground surface in dune-slack areas (≤ 1 m below ground for SD15b-defining wells) and dipping westward and south-westward across the open dune.

### []{#anchor-15}S12.3 Darcy flow field

The Darcy flow field (Figure 16, overlaid on the head surface as normalised flow-direction vectors) is computed from the head surface by

> **q** = −*K* · ∇*h*

where ∇*h* is the spatial gradient of the head surface and *K* is the bulk hydraulic conductivity (Section S2.1, 6 m day⁻¹ from Betson et al., 2002). The resulting vector field is reported as a directional flow pattern rather than as a quantitative discharge map: the head surface is observed but *K* is uncertain (single tracer test, no spatial variation), so the flux magnitudes are not calibrated.

The directional pattern is robust regardless of the choice of *K*: the field shows south-westward flow in the western half of the site (toward Caernarfon Bay) and south-eastward flow in the eastern half (toward the Menai Strait), with the watershed boundary tracking the topographic ridge mid-site. The Darcy field is broadly consistent with the DEM-derived topographic drainage paths overlaid on the spatial figures (most clearly visible on Figure 1, the site overview). This overlay is a cartographic-context layer loaded by the pipeline from data/streams.kml and produced in QGIS using GRASS r.watershed with multiple-flow-direction routing and a 4000-cell channelisation threshold (≈ 1.6 ha minimum contributing area) against the LiDAR digital elevation model; it is rendered as cartographic context rather than as a pipeline output. The agreement between the Darcy field and the topographic drainage paths supports the use of topographic flow-accumulation as an operational proxy for subsurface flow divides at this site, although the two are co-determined by the underlying till and bedrock architecture rather than one causing the other.

## []{#anchor-15}S13. Coastal-retreat gradient regression

The Newborough coastline at the south-western dune front (Caernarfon Bay) is undergoing measurable retreat (Pye and Blott, 2024; Forgrave, 2020). The hypothesis tested in Section 4.11 of the main manuscript is that this coastal retreat is producing a spatially-structured water-table decline that decays inland --- a chronic, location-dependent forcing distinct from the spatially-uniform climate background.

### S13.1 Panel regression specification

The test (25_coastal_gradient.py) is a panel regression of well-level long-term water-table trends against perpendicular distance to the eroding shoreline:

$${t_{\mathit{ij}} = \delta}{\left( d_{i} \right) + \alpha_{i} + \alpha_{j} + \gamma}\cdot{W_{\mathit{ij}} + \epsilon_{\mathit{ij}}}$$

where *t*~*ij*~ is the monthly water-table change at well *i* in month *j*, *d*~*i*\ ~is well *i*'s perpendicular distance from the eroding shoreline, δ(·) is the modelled distance decay, α~*i*\ ~and α~*j*~ are well and month fixed effects (absorbed by within-well demeaning), *W*~*ij*~ is the cumulative water-balance covariate (the integrated SSM water balance to month *j*, included to absorb the spatially-uniform climate background and so isolate the spatially-structured residual), γ is its coefficient, and ε~*ij*~ is the residual.

Two functional forms are tested for the distance decay δ(·):

-   **Linear-capped**: δ(*d*) = δ₀ + (*c* − δ₀) · min(*d*/*L*, 1). A linear decline from a coast-edge intercept δ₀ to a far-field background *c* over an inland reach *L*; flat at *c* beyond *L*.
-   **Exponential**: δ(*d*) = *c* + (δ₀ − *c*) · exp(−*d*/*L*). An exponential decay from δ₀ at *d* = 0 to *c* asymptotically, with characteristic length *L*.

[]{#s13.1-panel-regression-specification}Both forms are fitted by nonlinear least squares. Model selection between the two is by the Akaike information criterion (Akaike, 1974).

### []{#anchor-15}S13.2 Nested specifications

Three nested specifications are fitted to test robustness:

-   **Full network**: all open-dune and forested wells in the reference network, excluding the clearfell-zone wells (which carry a non-coastal management forcing).
-   **Forest-free**: the open-dune wells (C1, C2, C3) only, excluding all forested wells. This is the primary specification reported in the manuscript: it removes any contamination from forest interception or canopy-driven evaporative demand from the distance fit.
-   **C3-only**: wells in C3 Western Residual only, with the far-field background *c* fixed at the forest-free value rather than re-estimated. This tests whether the distance gradient is identifiable within the single cluster geographically closest to the eroding shoreline.

### []{#anchor-15}S13.3 Parameter values

Fitted parameters, read live from outputs/25_coastal_gradient/25_01_panel_fit_parameters.csv:

  ------------- --------------------------- -------- ----------- --------------- ----------- --------------
  Full          linear-capped               12,516   −35,203.6   −29.71 ± 1.86   972 ± 55    −0.15 ± 0.55
  Full          exponential                 12,516   −35,201.7   −39.30 ± 2.89   532 ± 86    +2.40 ± 1.24
  Forest-free   linear-capped               11,834   −34,320.0   −29.22 ± 1.91   901 ± 52    +0.18 ± 0.54
  Forest-free   exponential                 11,834   −34,319.9   −40.20 ± 3.65   422 ± 66    +1.50 ± 0.90
  C3-only       linear-capped (*c* fixed)   3,813    −10,618.2   −24.89 ± 2.62   971 ± 94    +0.18
  C3-only       exponential (*c* fixed)     3,813    −10,621.4   −29.59 ± 4.03   605 ± 102   +1.50
  ------------- --------------------------- -------- ----------- --------------- ----------- --------------

Confidence intervals are 95% (1.96 SE). The forest-free linear-capped fit is the headline specification: δ₀ = −29.22 mm yr⁻¹, *L* = 901 m, *c* = +0.18 mm yr⁻¹. *c* is the fitted far-field offset, not a climate background: it is not separately identified from the trend contribution the cumulative water-balance covariate carries over the fitted span, and only the sum of the two is recovered.

### []{#anchor-15}S13.4 Model selection

The AIC difference between linear-capped and exponential in the forest-free specification is 0.1 (−34,320.0 against −34,319.9), marginally in favour of the linear-capped form; on the full network the same comparison gives 1.9, again favouring linear-capped. A gap of 0.1 AIC is not a discrimination between functional forms and should not be read as one. Both fits agree on the sense of the gradient (a coast-edge deepening that decays inland) and on the magnitude of the coast-edge component (\~−29 to −40 mm yr⁻¹), and both return a far-field offset *c* close to zero (−0.15 to +2.40 mm yr⁻¹ across the six fits). The choice of functional form changes the inland reach *L* and the partition of the coast-edge intercept δ₀ between the two functions, but does not change the central finding: a near-coast water-table deepening of order 25--40 mm yr⁻¹ relative to the far field, declining over an inland reach of order 400--1000 m to a far-field level indistinguishable from zero. That far-field level is not a climate background. The cumulative water-balance covariate of S13.1 already absorbs the spatially-uniform climate forcing, and over the panel\'s own span that covariate itself carries a trend contribution; a constant offset and that contribution trade off exactly, so only their sum is recovered and *c* alone is not separately identified.

The headline values reported in the manuscript adopt the linear-capped fit for its slightly more conservative coast-edge magnitude (−29.22 vs −40.20 mm yr⁻¹) and its more interpretable reach length (a capped-linear *L* of 901 m is closer to the physical scale of the dune body than the exponential *L* of 422 m, which is the *e*-folding length). AIC now favours the linear-capped form as well, so the choice no longer runs against the model-selection criterion, though the margin is far too slight to carry it. The exponential fit is reported as a sensitivity case.

### []{#anchor-15}S13.5 C5 out-of-sample sentinel

The C5 Coastal Forest well nw9, at 419 m from the eroding shoreline, shows a decline of −32.7 mm yr⁻¹ (*p* = 0.002, *R*² = 0.41, *n* = 20 years, from 25_02_per_well_summer_min_slopes.csv). nw9 is forested and is excluded from the forest-free regression; it therefore functions as an out-of-sample sentinel, testing the fitted gradient at a near-coast position without contributing to it. Under the headline linear-capped fit the gradient at 419 m predicts a coastal-retreat contribution of −15.6 mm yr⁻¹, leaving −17.1 mm yr⁻¹ of the observed decline unaccounted for by distance to the shoreline. No climate background closes that gap. The two cluster-independent terms are the trend contribution the cumulative water-balance covariate carries, +2.98 mm yr⁻¹, and the fitted far-field offset *c*, +0.18 mm yr⁻¹; they are not separately identified, and their sum is positive, so the unexplained remainder is larger still at −20.3 mm yr⁻¹ (25_08_spring_vs_summer_comparison.csv, C5 summer columns). That remainder is what the substrate-position amplification developed in Section 5.2 of the manuscript addresses.

## []{#anchor-15}S14. Forest-interception drawdown reach (Figure 19)

Section 4.11 of the main manuscript renders the inland reach of forest-interception drawdown (20_spatial_figures.py for the figure) --- the distance over which interception-driven recharge suppression at the plantation boundary persists in the down-gradient open dune --- as a physical decay length. The calculation is a Dupuit-style drainage length:

> λ = √( *Kb* / (*S*y · β₃) )

where λ is the inland decay length, *K* the hydraulic conductivity, *b* the saturated thickness, *S*y the specific yield and β₃ the drainage coefficient (in daily units). The expression is the characteristic length over which a head perturbation at the source decays in a homogeneous, fixed-base unconfined aquifer.

The parameters used in Figure 19 are taken from C3 Western Residual, the open-dune cluster immediately down-gradient of the plantation boundary, with: *S*y = 0.3057 (C3 per-well median of the Approach B event estimates --- the pipeline-consumed canonical, Section S11.2); β₃ = 0.058 month⁻¹ ≈ 1.93 × 10⁻³ day⁻¹ (C3 cluster-mean, Section S6.2); *K* = 6 m day⁻¹ (Betson et al., 2002, Section S2.1); *b* = 5 m (nominal saturated thickness, the latter uncertain by a factor of two or more given the absence of cored aquifer-thickness data; the geophysics of Bristow, 2002, indicates 12--27 m in the forest interior, but the open-dune thickness immediately south of the plantation boundary may be lower).

With these inputs, λ ≈ 225 m (matching the value rendered on Figure 19). The contours on Figure 19 should be read as an order-of-magnitude diagnostic of the inland reach, not as a calibrated prediction. λ scales as √(*Kb*), so a factor of two uncertainty in *b* corresponds to a factor of √2 ≈ 1.4 in λ; the true reach could plausibly be anywhere between roughly 150 m and 320 m on reasonable variations of the input assumptions. The order-of-magnitude conclusion --- that forest-interception drawdown is felt within roughly 100--300 m of the plantation boundary, not across the whole site --- is robust to those uncertainties.

This is the only output of the framework that depends on *K*. Every other coefficient surface, residual field, water-balance partition, *S*y estimate, coastal-retreat gradient and diagnostic synthesis presented in the manuscript is derived without a *K* estimate (Section 5.6 of the main manuscript). A measured *K* --- from slug tests at representative wells per cluster, the priority future field measurement --- would tighten only the Figure 19 reach calculation.

The empirically fitted coastal-retreat reach (Figure 20 of the manuscript) is *not* an analogue of the Figure 19 reach in this sense: the coastal-reach length *L* is fitted directly from the panel regression (Section S13) and *K* and *b* do not enter its derivation. The forest and coastal reaches are therefore methodologically distinct: Figure 19 is a forward calculation from independent SSM and literature parameters, while Figure 20 is a back-calculation from observed water-table trends. Section 5.6 of the main manuscript discusses the implications.\

## []{#anchor-16}S15. Software, parameters and reproducibility

The full analysis pipeline is open source and version-controlled on GitHub at github.com/newbroman/Newborough_Hydrology (commit XXXXXXX at submission). A versioned snapshot of the code, the author-collected input data, and every output CSV referenced in this document is archived on Zenodo at DOI [10.5281/zenodo.XXXXXXX](https://doi.org/10.5281/zenodo.XXXXXXX). The pipeline version is recorded in the pipeline_version field of outputs/pipeline_manifest.json. The Zenodo deposit is the citable, immutable reference; the GitHub repository carries any subsequent updates.

**Software environment.** Python 3.12.3. The complete, version-pinned environment is specified in requirements.txt; key packages are NumPy 2.4.6, SciPy 1.17.1, pandas 3.0.3 and statsmodels 0.14.6 (numerical and statistical processing); GeoPandas 1.1.3, Rasterio 1.5.0, Shapely 2.1.2 and pyproj 3.7.2 (spatial); and Matplotlib 3.10.9 (plotting). Random seeds for every stochastic step (bootstrap resampling, cluster stability) are defined centrally in utils/config.py, giving byte-equivalent reproduction.

**Cartographic-context overlays.** Site-overview cartography combines pipeline outputs with cartographic-context overlays loaded by the pipeline from KML files in data/. The data/streams.kml overlay --- the topographic drainage network shown on Figure 1, Figure 8, Figure 16 and other spatial maps --- was produced in QGIS 3.34.4-Prizren using the GRASS provider, tool r.watershed, with multiple-flow-direction routing and a 4000-cell channelisation threshold (≈ 16,000 m² minimum contributing area). The input was the merged 2 m LiDAR DEM (mergeddem.tif, EPSG:27700) used throughout the pipeline. The line network was extracted via r.to.vect and exported to KML, then post-processed to remove drainage paths below 0 m AOD (intertidal/foreshore) by sampling the DEM at each line vertex; the masking utility is included in the repository as a one-shot data-preparation step. Other context overlays (Features.kml, site_boundary.kml, clearfell.kml) are similarly produced or maintained in GIS and loaded by the pipeline via src/utils/map_utils.py add_kml_features(). The Python pipeline reproduces the analytical work; these GIS files are cartographic context.

**Pipeline orchestration.** The pipeline is run as a single command (python run_analysis.py) which executes the analytical steps in canonical order. Each step writes its outputs to a step-specific subdirectory under outputs/ and updates the canonical pipeline parameters file (Section S2.2) where appropriate. A full run on a standard workstation completes in approximately 30 minutes.

**Pipeline parameters table.** Headline values used in this document, all read live from the canonical CSVs at the time of submission:

  ------------------------------------ --------------------- --------------------------------------------
  Network size (reference)             66 wells              01_wells_provenance.csv
  Drainage datum *D*                   3.7 m                 pipeline_scenario_params.csv
  HEADLINE_LAG                         0                     pipeline_scenario_params.csv
  Forest interception                  0.24                  Freeman (2008), config.py
  C1--C5 β₁, β₂, β₃, *R*²              (see Section S6.2)    03_03_cluster_mechanistic_coefficients.csv
  Cluster *S*y                         (see Section S11.2)   17_wtf_01_sy_estimates.csv
  Coastal δ₀, *L*, *c* (forest-free)   (see Section S13)     25_01_panel_fit_parameters.csv
  nw9 decline                          (see Section S13.5)   25_02_per_well_summer_min_slopes.csv
  Hydraulic conductivity *K*           6 m day⁻¹             Betson et al. (2002)
  ------------------------------------ --------------------- --------------------------------------------

**Data availability.** The dipwell water-level records and the well location/elevation data analysed here were collected by the author and are deposited, in cleaned form, in the Zenodo archive alongside the code (Newborough_Cleaned_For_Model.csv, Well_locations_height.csv). The RAF Valley climate series (monthly rainfall, and the mean-temperature series used to derive Thornthwaite PET) are Met Office historic station observations, © Crown Copyright, Met Office, available from the Met Office at https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/valleydata.txt under the Open Government Licence v3.0, and are not re-archived here. This dataset contains public sector information licensed under the Open Government Licence v3.0.

**Code availability.** All scripts, all output CSVs and figures, and a complete README.md are at github.com/newbroman/Newborough_Hydrology. The repository licence is MIT for code and CC-BY-4.0 for the author-collected data and figures. The author can be contacted at the address on the title page for any aspect of the analysis not covered here.

## S16. Supplementary references

References cited only in this SI document, not in the main manuscript:

> Calinski, T. and Harabasz, J. (1974) A dendrite method for cluster analysis. *Communications in Statistics* 3(1), 1--27.

> Crosbie, R.S., Binning, P. and Kalma, J.D. (2005) A time series approach to inferring groundwater recharge using the water table fluctuation method. **Water Resources Research** 41(1), W01008. doi:10.1029/2004WR003077.

> Liao, T.W. (2005) Clustering of time series data --- a survey. *Pattern Recognition* 38(11), 1857--1874.

> Milligan, G.W. and Cooper, M.C. (1985) An examination of procedures for determining the number of clusters in a data set. *Psychometrika* 50(2), 159--179.

All other references --- Akaike (1974), Bear (1972), Betson, Connell and Bristow (2002), Bristow (2002), Bristow and Bailey (2001), Curreli et al. (2013), Davy et al. (2006), Fetter (2001), Forgrave (2020), Freeman (2008), Freeze and Cherry (1979), Healy and Cook (2002), Hollingham (2026b, in preparation), Knotters and van Walsum (1997), Pye and Blott (2024), Ranwell (1958), Rao and Srinivas (2006), Rhind et al. (2001), Robins and Davies (2015), Rousseeuw (1987), Scanlon et al. (2002), Stratford et al. (2007), Ward (1963), Young (2011) --- appear in the main manuscript's reference list and are not duplicated here.

[]{#supporting-information}[]{#s16.-supplementary-references}End of Supporting Information.
