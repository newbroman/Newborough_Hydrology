<!-- GENERATED MIRROR of docs/papers/paper_1/PAPER1_SI_methods_v1_29.odt — do not edit. source-sha256=9225936db75c2983 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

# Supporting Information

## Hollingham (2026a), Paper 1 --- *A parameter-sparse state-space framework for characterizing coastal dune-aquifer architecture from manual dipwell records*

This Supporting Information document gives the methodological detail underlying the analyses reported in the main text. It is self-contained: every parameter, equation, and design choice that supports a result in the manuscript is laid out here. Section numbers in the manuscript refer back to the headed sections here (S1--S15).

[]{#anchor}The pipeline and outputs are archived in full (Section S14). The headline numerical values used in the manuscript are reproduced live from the pipeline output CSVs cited at the foot of each section, and are unchanged at the time of submission.

### S12.6 Seasonal robustness (spring mean)

The gradient regression above uses the annual summer minimum (Jun--Sep) as the per-well response. It was repeated with the annual spring mean (Mar--May) as a second per-well metric through the identical code path (compute_per_well_slopes(metric=...), strict 3-of-3 monthly completeness). The panel fit and the coastal-retreat gradient are all-season and metric-independent --- the same forest-free linear-capped fit is applied to both metrics --- so any spring--summer difference in the decomposition is attributable to the response metric, not to a refitted gradient. That is a property of the procedure, not evidence that the gradient is season-invariant; the test below shows that it is not.

The gradient is itself seasonal. A full-panel season × δ(d)·t interaction (10,909 observations, one model) fits δ(d)·t·(1 + γ·S), with S = 1 in Mar--May, and returns γ = +0.309 ± 0.060 (t = 5.16, p \< 0.001) for the linear-capped form and +0.304 ± 0.059 (t = 5.15, p \< 0.001) for the exponential. Both forms reject season-independence, and both put γ above zero: the coastal-retreat drift rate is about 31 % steeper in Mar--May than over the rest of the year. That the estimate is significant, of the same sign and of compatible magnitude under both decay forms indicates a seasonal modulation of the gradient itself rather than an artefact of the assumed functional form. The MAM-only refit of the panel (a sensitivity block in 25_01_panel_fit_parameters.csv) points the same way: it loses power as expected (the fitted δ₀ SE roughly doubles, 1.97 to 3.71 mm yr⁻¹) but returns a steeper spring coast-edge anomaly than the all-season fit (δ₀ −34.06 against −31.28 mm yr⁻¹), a change of about 9 % in the same direction as γ. At the reference distance the two fits are closer still, at −25.87 against −26.38 mm yr⁻¹. What remains year-round is the boundary effect itself: C5 Coastal Forest --- the out-of-sample sentinel of S12.5 --- declines in both seasons (summer −32.0, spring −23.9 mm yr⁻¹, balanced annual means), so γ modulates the drift rate rather than switching it off outside spring. The all-season gradient is therefore a season-averaged quantity, not a season-independent one, and applying it unchanged to a spring metric understates the spring coastal contribution: the ≈ 71 % of C5\'s spring decline that it attributes to coastal retreat is a lower bound. Full seasonal results are in the report\'s Supplementary Material, Note S8.

### S12.7 Single-well leverage of δ₀

Because the forest-free panel has few wells inside 300 m of the shore, the shoreline amplitude δ₀ can lean on individual near-shore wells. Script 25 refits the headline specification (forest-free, linear-capped, all-season, 61 wells) once per well with that well withheld, holding the starting values, bounds and climate covariate fixed, and writes one row per well to 25_16_delta0_leave_one_out.csv; a withhold-nothing control must reproduce the headline fit exactly. The largest shift is ceh3 (176 m): withholding it moves δ₀ from −31.28 to −28.15 mm yr⁻¹ (+3.1) and the 150 m rate by +2.4 mm yr⁻¹; the next-largest shifts are wmc2 (458 m, −1.7), ceh22 (147 m, −1.4), d25 (894 m, +1.4) and ceh39 (771 m, +1.0), and no other well moves δ₀ by more than 1 mm yr⁻¹. The standard error of δ₀ estimated from the 61 refits (the delete-one estimate, √((n−1)/n·Σ(δ₀,ᵢ − δ̄₀)²)) is 4.8 mm yr⁻¹, against the fitted 1.97, which is computed from the residuals of about 11,000 monthly rows treated as independent. The two answer different questions --- the fitted value is the precision of the model given its rows, the refit value the precision given that the wells are the units of independence --- and the manuscript quotes the well basis: δ₀ = −31.28 ± 4.79 mm yr⁻¹ (95% CI −40.66 to −21.89), the 150 m rate −26.38 ± 3.49 mm yr⁻¹ (95% CI −33.23 to −19.53) and L_cg 902 ± 144 m (620 to 1185), each the delete-one estimate over the 61 refits (25_report_numbers.csv, \*\_well_basis\_\*). The fitted standard errors remain in 25_01_panel_fit_parameters.csv as the nominal precision of the model and are not quoted as uncertainties. The leverage of ceh3 lies inside the well-basis error.

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

The 88-well manual dipwell network is read monthly by the author. Readings are taken at the **end of each month** --- typically the last day of that month, or the first day or two of the following month. Each reading is the water level *for the month just ended*: a measurement taken on 1 May 2026 represents the **April 2026** water level. Climate data from RAF Valley Meteorological Station (53°15′00″N, ≈16 km from the site) is a monthly total for the same calendar month: rainfall *P* (mm), and minimum and maximum temperatures from which monthly Thornthwaite PET is computed at the RAF Valley latitude (53.25°).

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

Water-table records are screened for sentinel values and obvious measurement errors. Short interpolation gaps (a single missing month with valid neighbours) are filled by linear interpolation, with the gap limit set to limit = 1; 259 of the 15,025 well-months present in the well-provenance audit (01_wells_provenance.csv, Section S1.5) are filled by interpolation; the remainder are observed.

### S1.4 Reference-network selection

The reference network (66 wells, Section S3) is the subset of the 88-well network that meets all of: - record start ≥ 2005 and record continuing through REFERENCE_CUTOFF_DATE (2026-02-01); - not on the blacklist of wells with known tidal influence (notably the pdfs well at the south-eastern shore); - not one of the five wells of the clearfell monitoring footprint (FE1--FE4 and LIS1), whose records span a change of regime that a single set of SSM coefficients cannot describe; they form the treatment arm of the clearfell analysis in Paper 2 (Hollingham, 2026b).

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
  RAF_VALLEY_LAT_DEG           53.25        53°15′00″N
  Hydraulic conductivity *K*   6 m day⁻¹    Betson et al. (2002) tracer test
  ---------------------------- ------------ ------------------------------------------

The 24% Corsican pine canopy-interception fraction is from Freeman (2008), the most spatially proximate canopy-interception measurement available for the Newborough plantation. *K* = 6 m day⁻¹ is from the single tracer test reported in the contemporaneous CCW groundwater-modelling study; it is required only in the Figure 18 forest-drawdown reach calculation (Section S13) and does not enter any other framework output.

### []{#anchor-1}S2.2 Canonical pipeline parameters file

A single canonical table of pipeline parameters, pipeline_scenario_params.csv, is written by the data-preparation step (Section S1) and updated in place by the downstream steps that fit new parameter values (the SSM regression, the BACI auxiliaries, and the WTF specific-yield estimation). Every downstream step reads its pipeline parameters from this file rather than from a hardcoded value, which rules out a category of inconsistencies that can otherwise propagate silently through long pipelines.

## []{#anchor-1}S3. Behavioural clustering and the *k* = 5 partition

### S3.1 Distance metric and linkage

Cluster identification (02_clustering.py) operates on a pairwise distance matrix between per-well hydrographs. The metric is one minus the Pearson correlation coefficient between any two wells' monthly time series over their common record window. A small minimum-overlap requirement (≥ 36 months) prevents short pairs from dominating; pairs that do not meet it are flagged as undefined and the affected well is excluded from clustering rather than imputed.

[]{#s3.1-distance-metric-and-linkage}Ward's hierarchical linkage (Ward, 1963) is then applied. Ward's criterion minimizes the increase in within-cluster sum of squares at each merge, which produces compact, well-separated clusters when the underlying data have structure. The choice of Ward over alternatives (single, complete, average linkage) reflects its well-attested performance on behavioural time-series data (Rao and Srinivas, 2006; Liao, 2005) and its tendency to produce spherical, balanced clusters of comparable size (Milligan and Cooper, 1985) --- desirable for downstream interpretation against physical substrate units.

### []{#anchor-2}S3.2 Cluster-count selection

The clustering literature offers several internal-validity indices for choosing the cluster count *k*. The two used here are the Rousseeuw silhouette coefficient (Rousseeuw, 1987) and the Calinski--Harabasz pseudo-*F* statistic (Calinski and Harabasz, 1974). Both are evaluated for k in {2, \..., 10}. Each curve has its own maximum and the maxima do not generally agree; this is a known property of internal validity indices applied to real data.

For Newborough the silhouette curve maximizes at k = 2 (0.58) and lies between 0.37 and 0.43 for k = 3 to 10 (0.37 at k = 5). The Calinski--Harabasz index also peaks at k = 2. By the internal-validity criterion alone, the best choice would be k = 2: the top division of the dendrogram (Ward merge distance ≈ 0.99), which separates C4 Main Forest from the other 57 wells.

This was not adopted. The internal-validity indices reward separability; they are agnostic to the physical interpretability of the resulting clusters. A k = 2 partition isolates C4 Main Forest and leaves the other 57 wells undivided, losing the east--west division between the eastern clusters (C1, C2) and the western (C3 with C5), which follows at a Ward merge distance of ≈ 0.61. *k* = 4 collapses C5 Coastal Forest into C3, losing the coastal-retreat signature. The Coastal Forest cluster is small (*n* = 5) and lies at the edge of the network, yet it is among the most stable clusters under bootstrap resampling (median co-assignment 0.99, Section S3.5), and its physical distinctness --- Corsican pine on the coastal sand body, with the steepest water-table decline in the network over the record --- is the basis on which it is retained as a separate cluster.

This study therefore selects *k* = 5 on a physical--mechanistic basis rather than on an internal-validity-index basis, and reports the indices transparently. The decision is taken openly in Section 3.2 of the main manuscript and is also reflected in the Pearson affinity audit (Section S4), which shows that C5 wells sit at the edge of cluster space rather than in its interior, but that the edge position is consistent and reproducible across the 21-year record.

### []{#anchor-2}S3.3 The k = 5 partition table

The reference network is partitioned into five behavioural clusters by Ward's linkage on correlation distance between per-well hydrographs (Section S3.1). The cluster IDs and labels are:

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

Bootstrap resampling of the per-well hydrograph set returns the same five clusters with stable cluster cores. The procedure draws 1000 random samples (with replacement) from the 66 reference-network wells, repeats the Ward\'s-linkage clustering on each draw, and counts the proportion of bootstrap draws in which each well is co-assigned to its canonical-partition cluster (02_04_bootstrap_stability_summary.csv). Four of the five clusters are highly stable, with median co-assignment above 0.97 --- 1.00 at C4 Main Forest, 0.99 at C5 Coastal Forest, and 0.98 at both C1 Lake Edge and C2 Dune. C3 Western Residual is the exception, at a median of 0.38: it is the most behaviourally heterogeneous cluster, and its members reassign more readily across bootstrap draws --- the resampling signature of the continuous substrate gradient identified in Section S4, along which wells near the cluster margins move between behavioural neighbours without the cluster cores dissolving. C5 Coastal Forest, despite having the smallest membership (n = 5), is among the most stable clusters rather than the least: its five wells behave consistently with each other and distinctly from the rest of the network (Section S4), and its anchor wells remain in C5 in almost every draw (nw9 in all of them, ceh16 in 99 %).

## S4. Pearson affinity audit and spatial confidence

The clustering algorithm assigns each well to the cluster with whose centroid it has the highest Pearson correlation. The *strength* of that assignment --- how clearly a well belongs to its cluster, rather than sitting near the boundary between two --- is recoverable from the affinity matrix: each well's Pearson correlation against every cluster centroid.

A well with a high primary affinity and substantially lower secondary affinities is a *core member* of its cluster. A well with a primary affinity only slightly above its secondary is *gradational* --- it sits at the boundary between two behavioural patterns. The Pearson affinity audit (05_pearson_affinity.py, Figure 5 of the main manuscript) makes this structure visible at the well level.

The audit shows three patterns. First, the cluster cores are spatially compact and behaviourally distinct, with high primary affinities and substantially lower secondary affinities. Second, the boundary between C2 (eastern Dune) and C3 (Western Residual) is gradational rather than sharp --- several wells in the centre-east of the network have primary affinity to one cluster but a secondary affinity within 0.05 of the primary, indicating that they sit on a continuous substrate gradient between the two clusters rather than within a structural discontinuity. Third, C5 Coastal Forest is a tight core with the lowest affinity to any other cluster, indicating that even though C5 has only five members, those five behave consistently with each other and distinctly from the rest of the network.

The C2/C3 gradation is discussed at length in Section 5.1 of the main manuscript and is the basis for the "behaviourally coherent cluster on a continuous substrate gradient" interpretation of C3. It is also why the discussion uses "C3 transitional zone" rather than "C2/C3 boundary".

The output 05_pear_01_spatial_confidence_map.png is Figure 5 of the main manuscript. The underlying affinity matrix is in outputs/05_pearson_affinity/05_affinity_per_well.csv.

[]{#anchor-2}Across the 66 reference-network wells, the audit classifies 19 as Core (sitting cleanly in their assigned cluster, with Pearson margin above 0.05), 41 as Fuzzy (assigned cluster is the best match but the margin to the second-best is small), and six as Spy (Ward\'s assignment and Pearson best match disagree): ceh21, ceh4 and wmc3, assigned to C3 Western Residual but matching C5 Coastal Forest, and d38, t41a and ceh40, assigned to C3 but matching C2 Dune; d38 and t41a are two of the five boundary wells that moved from C2 to C3 in the final revision of the partition. All six margins are small (\|Δr\| \< 0.015): borderline assignments at gradational boundaries. The six are documented but retained in their Ward\'s assignments; Pearson margins within sampling noise are not a defensible basis for re-partitioning. The 91 % Core + Fuzzy share within the assigned cluster supports the partition as a reasonable behavioural grouping of the network.

## []{#anchor-3}S5. The state-space model --- displacement formulation

The state-space model (SSM) is the methodological core of the analysis. The cluster characterization, the specific-yield estimation, the water-balance decomposition, the residual field and the coastal-retreat gradient regression all rest on it.

### []{#anchor-4}S5.1 Equation

The fitted equation is

> Δ*h*(*t*) = β₁ · *P*(*t*) − β₂ · PET(*t*) − β₃ · (*z₀* + *h*(*t*−1))

where Δ*h*(*t*) is the change in water table during month *t* (m, signed; negative when the water table falls); *P*(*t*) and PET(*t*) are the rainfall and Thornthwaite PET during month *t* (m); *h*(*t*−1) is the water table at the end of month *t*−1 (m, signed; negative below ground surface); *z₀* is the drainage datum, *z₀* = 3.7 m (Section S2); and β₁, β₂, β₃ are positive coefficients fitted by ordinary least squares (no intercept).

The quantity *z₀* + *h*(*t*−1) is the displacement of the water table above the drainage datum at the start of month *t*. With *z₀* = 3.7 m and a typical end-of-previous-month head of −0.4 m, displacement is 3.3 m; with a deeper end-of-month head of −2.0 m, displacement is 1.7 m. The β₃ term says: the deeper the water table sits below ground at the start of a month, the smaller the drainage during that month --- consistent with Darcy's law for a shallow unconfined aquifer drained to a fixed lateral discharge horizon.

The equation is a multiple linear regression: three predictor variables (rainfall, PET, start-of-month displacement) and one response variable (Δ*h*). The three coefficients are estimated jointly by ordinary least squares (OLS), which finds the values that minimize the sum of squared residuals across all (well, month) observations in the regression sample. The fit returns each coefficient with its standard error and *p*-value, the overall regression *R*² (the fraction of monthly Δ*h* variance jointly explained by the three predictors), and the residual series at every observation.

### []{#anchor-4}S5.2 Sign conventions

All three β values are reported positive. Signs are baked into the design matrix, not into the coefficient values. In the design matrix the β₁ column is +*P* (a positive β₁ means rainfall raises the water table), the β₂ column is −PET (a positive β₂ means PET lowers the water table), and the β₃ column is −(*z₀* + *h*prev) (a positive β₃ means displacement above the datum drives drainage downward). A fitted β₁ ≤ 0 or β₂ ≤ 0 halts the pipeline because either is physical nonsense; β₃ \> 0 is soft-asserted (a negative β₃ is anomalous and worth investigating but does not halt the pipeline).

### S5.3 Why *h*(*t*−1) rather than *h*(*t*)

[]{#s5.3-why-ht1-rather-than-ht}The drainage term uses the water-table position at the end of the previous month, not the contemporaneous level, for two reasons. First, h(t) is the dependent variable through Δh = h(t) − h(t−1); using it simultaneously as a predictor would create simultaneity bias and break the interpretation of β₃. Second --- and physically --- drainage during a month is driven by the head at the start of that month, not the head at the end; the end-of-month head is the result of drainage, not its cause. The displacement at the start of month t equals the displacement at the end of month t−1, hence the h(t−1) form. The within-month mean head would in principle be a more faithful driver still, since total monthly drainage is the time-integral of a head-dependent flux and the start-of-month form is in effect its forward discretization; but the mean is not observed. With a single end-of-month reading it can only be reconstructed as ½·\[h(t−1) + h(t)\], which carries h(t) --- and hence Δh --- back into the predictor, reinstating the simultaneity the h(t−1) form is chosen to avoid while adding no information beyond the two endpoints. The two discretizations are in fact an exact reparameterization of one another on monthly data --- the mean-head form rescales β₃ by 1/(1 − β₃/2) and leaves the fit, residuals and cluster contrasts unchanged --- so the start-of-month choice costs nothing in fit, and only the simultaneity argument bears on it.

### []{#anchor-4}S5.4 Drainage datum

The 3.7 m drainage datum was selected to give comfortable β₃ identification at the forest clusters (C4 Main Forest, C5 Coastal Forest), where β₃ is hardest to pin down because the water table sits deepest below ground there. A sensitivity sweep over *z₀* compares the live empirical minimum z₀ = 1.6 m --- the shallowest depth at which all five clusters simultaneously satisfy β₃ \> 0 with p \< 0.05 --- against the operating value z₀ = 3.7 m. At the empirical minimum C4\'s β₃ p-value sits at the significance edge (0.035); at 3.7 m it drops to 0.001, with C5 also gaining substantially (β₃ p-value from 3 × 10⁻¹¹ to 1 × 10⁻¹⁶, R² from 0.642 to 0.677). The trade-off is small R² penalties at C1 Lake Edge (−0.053) and C2 Dune (−0.025), where β₃ is over-determined and remains significant at *p* \< 10⁻²⁵ at either depth.

The role of the datum is to shift the reference for the drainage term. Without it (i.e. with *h*(*t*−1) instead of (*z₀* + *h*(*t*−1)) in the design column), the C4 and C5 clusters produced negative β₃ estimates. This was a sign-convention artefact: it reflected that the OLS was correlating drainage with a quantity that crossed zero rather than staying on one side of a fixed reference. Setting the reference 3.7 m below ground places every observation comfortably on the positive side of the datum.

Δh is invariant under the choice of datum (the datum cancels in first differences), but the coefficients are not: because the model has no intercept, a shift in the datum constant redistributes across β₁, β₂ and β₃ together. The datum therefore fixes the absolute scale of the drainage coefficient and of the half-life, which are reported as conditional on z₀ = 3.7 m, while the cluster ordering, the open-dune drainage contrasts and the mean water-balance closure are robust across the swept range.

### []{#anchor-4}S5.5 Implementation: two levels of fit

The SSM is fitted at two distinct levels of aggregation and Paper 1 uses both. The distinction is material because the two fits address different questions and feed different downstream products. Section S6 maps the fits to the products explicitly; the rest of this subsection covers the construction of the design matrix, which is common to both.

**Cluster-mean fit --- the primary characterization tool.** A single OLS regression is run for each cluster on the cluster-mean hydrograph. The cluster centroid is constructed by averaging the water-table depths of cluster members month by month, producing one mean-depth time series per cluster; the SSM design matrix is then built from that centroid series and the shared climate forcing, and fitted by OLS. The result is one set of coefficients (β₁, β₂, β₃) per cluster, with the regression *R*² and per-coefficient *p*-values that anchor Table 1 of the main manuscript. Working on the centroid rather than on per-well-stacked rows is the standard behavioural-cluster characterisation approach: the cluster centroid is the canonical "average member" of the cluster, and fitting the SSM to it gives the coefficients that describe the cluster's collective behaviour without per-well noise. The cluster-mean fit is what underwrites the substrate-gradient interpretation of Sections 5.1--5.2, the Lumped Catchment Storage Coefficient (Section S6.4), and the drainage decay half-life t½ = ln(2)/β₃ reported in Section 4.7.

**Per-well fit --- the spatial-products tool.** The SSM is also fitted independently at each well in the reference network, producing a separate (β₁, β₂, β₃) at every well. The per-well fits feed the spatial products: the coefficient atlas (Figures 11--13, three interpolated surfaces built from the per-well values), the per-well residuals (Figure 16, the per-well residuals from the per-well fit, shown at the wells alone), and the per-well water-balance decomposition (Section S9). Per-well fits are noisier than the cluster-mean fit because each is conditioned on a single well's record; per-well coefficient values are therefore best read in the spatial pattern they form across the network rather than at any single point.

**Common design-matrix construction.** The design matrix is built one (well, month) row at a time. For each row the well's water-table series is joined with the RAF Valley climate record on the bucketed monthly index, and Δ*h* and *h*disp,prev are computed, producing a row with columns *h*, *h*prev, Δ*h*, *P*, PET and *h*disp,prev. The per-well fit at well *w* runs OLS over the rows belonging to *w* alone, yielding a per-well (β₁, β₂, β₃). The cluster-mean fit at cluster *c* builds the same row structure from the cluster centroid --- the month-by-month mean of cluster members' depth series --- joined against the shared climate record, and runs OLS over those centroid rows. A three-coefficient OLS regression (no intercept) is fitted in either case and reports the coefficients with their standard errors, *p*-values from a two-sided *t*-test against zero, regression *R*², and residual series. The row construction and the regression are implemented in 03_state_space_model.py, which calls the shared helpers build_ssm_frame() and fit_ssm() from src/utils/model_utils.py; there is no reimplementation of the displacement calculation or the OLS fit elsewhere in the pipeline.

### S5.6 Residual serial correlation and inference validity

Because the SSM is a monthly time-series regression, the classical OLS standard errors that produce the coefficient *p*-values are valid only if the residuals are free of substantial serial correlation. This is tested directly (22_residual_lag_analysis.py, output 22_05_ssm_residual_autocorrelation.csv). The headline (no-intercept) SSM is refitted at each of the 62 reference wells with a valid fit and the residuals are examined: the median Durbin--Watson statistic is 2.28 (interquartile range 2.17--2.40) and the median lag-1 autocorrelation is −0.14. The residuals therefore carry a slight *negative* first-order autocorrelation rather than the positive persistence that would inflate significance --- a direct consequence of the drainage term −β₃·(*z₀* + *h*(*t*−1)), which acts as an error-correction term and absorbs the first-order persistence of the level series. Negative residual autocorrelation makes the OLS standard errors mildly conservative, not anti-conservative. A Ljung--Box test at lag 12 rejects white-noise residuals at 21 of the 62 wells; this reflects the *seasonal* residual structure characterized independently in Section S8.2 (winter--spring phased), not low-order persistence, and it is orthogonal to the coefficient standard errors.

As a robustness check the coefficient *p*-values are re-estimated with heteroskedasticity- and autocorrelation-consistent (Newey--West / HAC) standard errors, using the *n*-adaptive rule-of-thumb truncation lag L = floor(4·(n/100)\^(2/9)). Across the 186 coefficient tests (62 wells × three coefficients), the HAC and OLS significance verdicts at α = 0.05 agree in all but two instances --- β₂ at CEH23 (p = 0.079 to 0.026) and at CEH25 (p = 0.092 to 0.029), both toward significance. No coefficient that OLS reports as significant is overturned under HAC. The classical-OLS inference underlying the coefficient tables is therefore sound. These diagnostics are run at the per-well level, the noisier of the two fits. The same battery applied to the five cluster centroids that carry the headline β table (Table 1; 22_06_ssm_cluster_mean_inference.csv, whose centroid β and OLS *p*-values reproduce 03_03_cluster_mechanistic_coefficients.csv exactly) leaves every coefficient significant under both OLS and HAC: none of the fifteen cluster-level tests (five clusters × three coefficients) changes verdict. The centroid residuals are close to white (Durbin--Watson 2.05--2.26) at every cluster except C4 Main Forest, where a mild positive autocorrelation (Durbin--Watson 1.82, φ = +0.06) still leaves all three coefficients HAC-significant. The cluster-mean fits, pooling every well in a cluster, are the better-conditioned of the two levels.

## **S5.7 Rainfall enters contemporaneously **

The recharge term uses the current month\'s rainfall, *P*(*t*), with no lag. This follows from the measurement protocol (Section S1): an end-of-month reading integrates the whole of that month\'s recharge, so the water-table change during month *t* is driven by month-*t* rainfall, and under the day-15 bucketing convention the correct pairing is same-month. The choice is supported by the lag diagnostic (03_04_lag_diagnostic.csv), which refits each cluster centroid at rainfall lags of 0--3 months: every cluster maximises R² at lag 0 by a wide margin (R² 0.68--0.81 at lag 0, falling to 0.04--0.42 at lag 1 and lower thereafter), and β₁ turns non-significant and sign-incoherent at the longer lags. Contemporaneous rainfall is therefore the best-supported predictor at the monthly timestep.

## []{#anchor-4}S6. State-space regression and the Lumped Catchment Storage Coefficient

### []{#anchor-5}S6.1 Per-well and cluster-mean fits, and where each is used

Section S5.5 introduced the two levels of fit; both are implemented in 03_state_space_model.py. The mapping of each fit to the downstream products of Paper 1 is:

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

The cluster-mean fit is the primary characterization tool: Table 1 of the manuscript and the substrate-gradient discussion that runs through Sections 5.1, 5.2 and 5.5 are all carried by the cluster-mean coefficients. The per-well fit is the spatial-products tool: it lets the cluster characterization be projected as continuous surfaces across the site for visual and diagnostic interpretation.

Three of the Paper 1 outputs are independent of the SSM regression entirely. The Pearson affinity audit is the principal independent cross-check on the cluster structure: it tests, well by well, whether each dipwell sits closer to its assigned cluster centroid than to any other, using a Pearson correlation that does not depend on the SSM regression. Of the 66 reference-network wells, 60 sit in their assigned cluster as Core or Fuzzy members (91 %); six (ceh21, ceh4, wmc3, d38, t41a, ceh40) are flagged as borderline cases where the Pearson best match disagrees with Ward\'s assignment by small margins (\|Δr\| \< 0.015) --- documented but retained, since within-noise Pearson differences are not a defensible basis for re-partitioning. The water-table-fluctuation specific-yield estimation takes cluster identity as an input rather than testing it, and it does not separate the clusters: once canopy interception is corrected, the cluster-level Sy values (Section S10.2) and the per-well estimates (Section S10.4) converge across the clusters, with C5 Coastal Forest at the edge of the range, which indicates that the behavioural contrasts the clusters capture are surface- and land-cover-mediated rather than differences in subsurface storage. The mean water-table head surface is a third independent product --- independent of the cluster structure by construction, since clusters describe behaviour (how hydrographs move together) while the head surface describes where the water table sits (geometry and discharge boundary positions) --- and feeds the Darcy flow field in Section S11 rather than the cluster argument. The justification for the cluster framework rests on the Pearson affinity audit.

### []{#anchor-6}S6.2 Cluster-mean coefficients

The full per-cluster (β₁, β₂, β₃) values, their standard errors and *p*-values, regression *R*², sample sizes *n* and Lumped Catchment Storage Coefficients (LCSC %, defined in S6.4) are reported as Table 1 of the main manuscript and are read live from 03_03_cluster_mechanistic_coefficients.csv. The substantive interpretation --- the physical meaning of each coefficient, the direction of the cluster-to-cluster contrasts, and the comparison of C4 with C5 --- is developed in Section 5.2 of the main manuscript.

### []{#anchor-6}S6.3 Caveats on OLS coefficient values

[]{#anchor-6}The cluster-mean coefficients are well-determined within the OLS framework: regression *R*² values lie between 0.68 and 0.81, the per-coefficient *p*-values are all very small (Section S6.2, Table 1 of the manuscript), and bootstrap resampling of the within-cluster wells gives tight confidence intervals on each (β₁, β₂, β₃). The interpretive caveat is not about coefficient accuracy in that statistical sense but about the *scope* of what the coefficients represent.

First, the coefficients are lumped cluster-mean responses, not point-flux measurements. β₁ is the system-aggregate sensitivity of monthly Δ*h* to rainfall, integrated over the cluster\'s heterogeneity, not a point recharge efficiency at any particular location; β₂ and β₃ are analogous lumped responses. Two wells from the same cluster need not share a common (β₁, β₂, β₃) --- the per-well fits show modest within-cluster variation around the cluster mean --- and a literal reading of the cluster coefficient as the value at any individual well over-extends the claim.

Second, the SSM is linearised --- it assumes additive superposition of recharge, atmospheric draw and drainage. Real shallow-aquifer systems have nonlinearities (soil-moisture deficit thresholding recharge, depth-dependent ET access, hysteresis in the unsaturated zone) that the lumped monthly fit averages over. The high *R*² values say the linearisation works at monthly timestep --- much of the variance is recovered by a three-coefficient linear model --- but they do not say there is no nonlinearity to find. The residual climatology (Section S8.2) shows systematic seasonal structure at the cluster level rather than month-to-month random variation, consistent with residual nonlinearity in the recharge term, the atmospheric-draw term, or both.

Third, at monthly timestep *P*, PET and *h* co-vary during recharge events. Collinearity between regressors widens the practical confidence interval on each individual coefficient relative to the OLS standard error, without inflating the point estimate in a known direction. The cluster-mean fits mitigate this by averaging over wells with slightly different individual covariances, but the issue is in principle present in any lumped state-space model fitted by OLS (Knotters and van Walsum, 1997; Healy and Cook, 2002).

The practical implication is that the *ranking* of clusters by each coefficient --- C4 has the highest β₂; the forest clusters have the lowest β₁; C1 has the highest β₃ --- is robust to all three caveats. Cross-cluster contrasts at this level reflect the substrate, vegetation and topographic differences between clusters, which the SSM is designed to detect. Absolute coefficient values should be interpreted as lumped cluster-mean responses, not as instrument-equivalent calibrated fluxes. The main manuscript Section 5.2 notes the same scope in the context of the β₂ ranking --- that cross-cluster β₂ comparisons rest on the ordering and the relative magnitudes, not on absolute flux interpretation.

### []{#anchor-7}S6.4 Lumped Catchment Storage Coefficient

The Lumped Catchment Storage Coefficient (LCSC) is the reciprocal of the recharge sensitivity, expressed as a percentage:

> LCSC = 100 / β₁

Because β₁ is the water-table rise per unit depth of rainfall and is therefore dimensionless, its reciprocal is the depth of rainfall required to raise the water table by one unit depth --- equivalently, the millimetres of rainfall required for a rise of 100 mm, which is the rendering used in Table 1 of the main manuscript. Dimensionally that is a storage coefficient: the proportion of a unit rise occupied by water rather than by matrix. No separate estimation step is involved; the coefficient is read directly off the cluster-mean fit described above, and the same definition is given in the methods of the main manuscript.

The coefficient is *lumped* in the sense that it does not isolate drainable porosity. Because β₁ carries both the aquifer's storage response and the efficiency with which a month's rainfall reaches the water table, LCSC rises when either the porosity is greater or the recharge is poorer, and this quantity does not separate the two.

The contrast across the canopy boundary illustrates the distinction. The two forested clusters carry the highest values in the network (C4 40.4%, C5 41.5%) against 21.8% to 26.6% in the open dune, which is consistent with canopy interception reducing the proportion of rainfall reaching the water table rather than with the plantation overlying a more porous body. Specific yield estimated by the water-table-fluctuation method (Section S10.1 below; Section 3.8 of the main manuscript) is independent of β₁ and bears on this directly: once corrected for interception, the C4 forest median of 0.261 falls within the open-dune range of 0.210 to 0.325, and the C5 median of 0.330 sits just above its upper edge, although the C5 estimate is constrained by the physical-plausibility limit and is only weakly corroborative. The Lumped Catchment Storage Coefficient and the water-table-fluctuation specific yield are therefore related but not interchangeable, and are reported separately; the reconciliation is developed in Section 5.2 of the main manuscript.

Per-cluster LCSC values are reported alongside the cluster-mean coefficients in Table 1 of the main manuscript, read live from 03_03_cluster_mechanistic_coefficients.csv; the relative ordering across clusters is interpreted in Section 5.2.

## S7. Spatial interpolation of SSM coefficients

The per-well β₁, β₂, β₃ values (Section S6.1) are interpolated to continuous surfaces across the site (07_spatial_coefficients.py) by piecewise-linear interpolation over the Delaunay triangulation of the wells. The interpolation is purely geometric; the surfaces are *aggregators of point responses*, not the output of a calibrated distributed-flow model. This distinction is foregrounded in the manuscript and in the figure captions.

### []{#anchor-8}S7.1 Interpolation configuration

Each surface is piecewise-linear over the Delaunay triangulation of the 66 reference wells, evaluated on a regular 50 m grid on the British National Grid (EPSG:27700) and drawn over a hillshade of the merged 2 m LiDAR digital elevation model. The same interpolator is used for every map of a per-well statistic in Paper 1 except the water table (Section S11). It was chosen by leave-one-well-out prediction: where a statistic has spatial skill, piecewise-linear, inverse-distance and kriged surfaces predict a withheld well about equally well, so a single method is kept across the maps rather than a different winner chosen for each statistic.

### []{#anchor-9}S7.2 Masking

Only one monitoring well (CEH12) lies on the northern rock-ridge bedrock outcrop (the area above the 20 m AOD contour) and it has a short record, so any interpolated coefficient values shown there are extrapolations from the surrounding network rather than supported by data. The aquifer parameterization does not apply on bare metamorphic basement in any case, so the interpretation in the manuscript does not rest on the ridge-zone cells. On the coefficient surfaces (Figures 11--13) a grid cell is masked as dune ridge where the LiDAR ground stands more than 1 m above the ground elevation interpolated between the wells, so the surfaces describe the ground the wells sit on rather than the ridges between them. The specific-yield surface (Figure 8, Section S10.4) is in addition clipped to the site outline. A per-well statistic on which no interpolation between wells predicts a withheld well better than the network mean is not given a surface at all: the SSM water-balance residual (Figure 16, Section S8) is shown at the wells alone.

### S7.3 Bandwidth and edge effects

[]{#anchor-10}A piecewise-linear surface has no search bandwidth: each grid cell takes its value from the three wells at the corners of the Delaunay triangle that contains it. Beyond the convex hull of the wells the surface is extended by at most 100 m, taking the value of the nearest well, and is not drawn further out, so there is no extrapolation towards the coast or the Menai Strait beyond that margin. Near the network edge the triangles are long and thin, and the surfaces are less reliable there than in the interior.

### S7.4 Coefficient atlas

[]{#anchor-11}[]{#anchor-12}The three interpolated coefficient surfaces (β₁, β₂, β₃) are presented as Figures 11--13 of the main manuscript and constitute the "coefficient atlas". The surfaces are intended as diagnostic readings of the cluster characterization extended continuously across the site; they are not flux maps and not predictions in any forward-modelling sense.

## []{#anchor-13}S8. Residual-field diagnostics

The state-space regression (Section S6) produces a per-month residual at every well: the portion of the observed Δ*h* not explained by the lumped balance β₁·*P* − β₂·PET − β₃·(*z₀* + *h*\<sub\>prev\</sub\>). Evaluated at each well\'s long-term mean climate and mean head, this steady-state balance --- modelled mean losses (β₂·PET̄ + β₃·h_disp̄) minus modelled mean recharge (β₁·P̄) --- gives a per-well residual in m/month (positive where modelled losses exceed modelled recharge, implying an unmodelled input; negative where the model over-predicts). These per-well totals are shown at the wells alone (Figure 16 of the main manuscript), and it is that set of values, not a surface, that is analysed here: no interpolation between wells predicts a withheld well's residual better than the network mean, so no surface is drawn. The per-well residual computation is implemented in 20_spatial_figures.py, and the per-well values are written to 20_residual_perwell.csv. The formal partition of the modelled signal into its three SSM components is given in Section S9. Rainfall enters gross at every well, including the forested ones. Because the coefficients are fitted on gross rainfall and above-canopy PET, the canopy interception loss is already carried inside the fitted β₂·PET̄ term; subtracting it from rainfall as well would double-count it and insert a spurious positive residual at C4 and C5. The residual is not invariant to this choice, so the convention is stated explicitly here.

The residual field carries no spatial structure, with a small systematic negative offset: 65 of the 66 reference wells fall within ±0.01 m/month and 51 are negative, and residual magnitude is uncorrelated with position on either axis (Spearman ρ = −0.14 against Easting, p = 0.27; ρ = +0.16 against Northing, p = 0.20). The signed residual shows no gradient on either axis (ρ = +0.02 against Easting, p = 0.86; ρ = −0.10 against Northing, p = 0.40). No well exceeds +0.02 m/month; the fifteen positive residuals all fall below +0.008 m/month (largest NW3, +0.0080 m/month) and lie in the open dune, at the lake edge and in the coastal forest, none in C4 Main Forest; the most negative residual falls at the ridge-flank well CEH14 (−0.0105 m/month), with CEH32 (−0.0079 m/month) next. The balance closes without requiring an additional flux. The two diagnostic tests below were run when the field was believed to be spatially structured; they are retained for what they establish about the limits of the monitoring design rather than as a discrimination among candidate mechanisms. Script 22, which characterises the residual series itself (per-well AR(1), Durbin--Watson and HAC standard errors, Section S5.6), establishes that the network\'s residuals are close to white: the AR(1) coefficient is small and negative at most wells (network mean φ = −0.142, median −0.144) and only four of the 62 wells exceed \|φ\| = 0.3.

### S8.1 Cross-correlation lag test (23_ridge_recharge_lag_test.py)

If a ridge-derived lateral input were present --- a Darcy-conveyed subsidy from the metamorphic bedrock ridge through the down-gradient open dune --- then a distance-dependent transport lag should be detectable: the time between a recharge event at the ridge and the corresponding response at down-gradient wells should increase systematically with distance. The cross-correlation lag test computes lagged correlations between (i) a ridge-zone composite recharge signal and (ii) the de-trended water-table series at each down-gradient well, identifying the lag at maximum correlation per well.

The test returns a null result: there is no monotonic distance-dependent lag structure across the down-gradient wells. Across the 49 of 66 wells with a significant cross-correlation peak, the Spearman rank correlation of peak lag against ridge distance is ρ = −0.03, p = 0.85. The peak lags are not, however, an observation of travel time. OLS residuals are orthogonal to the fitted rainfall regressors at lags 0 and 1 by construction, which imposes a methodological floor: 42 of the 49 significant peaks fall at lag 2, and 50 of the 66 wells peak at lag 2 irrespective of ridge distance, a pattern that persists under a Box-Jenkins pre-whitened reformulation. The statistic is therefore partly determined by the fitting procedure rather than by hydrology. What structure the lags do carry is organised by cluster rather than by ridge distance: all five wells peaking at lag 3 are C4 Main Forest (ridge distances 741--1068 m, peak r = +0.16 to +0.20), consistent with the weak head-dependent drainage of the forest interior (the network\'s lowest cluster β₃, 0.018 month⁻¹) rather than with a distance-dependent transport path. The two significant wells peaking beyond lag 3 (ceh17 at 11 months, Ceh32 at 12) carry among the weakest correlations in the set (\|r\| ≤ 0.18, one of them negative) and reflect the flatness of the cross-correlation function rather than a resolvable delay.

[]{#anchor-14}This null result must be qualified by sampling frequency: monthly observations are an order of magnitude coarser than the days-to-weeks transit times expected for fracture-flow input from a metamorphic bedrock ridge, so a real ridge-derived lag could be invisible at this resolution. The null result therefore bears on what the present record can resolve rather than on whether the mechanism is operative.

### []{#anchor-15}S8.2 Seasonal climatology test (24_residual_seasonality.py)

If the residual field reflected systematic underestimation of summer evaporative demand at the forest margin --- for example, an under-resolved canopy-driven evaporative loss not captured by Thornthwaite PET --- then the residual field should peak in summer when those fluxes are active. The seasonal climatology test computes the monthly mean residual at each well across the 21-year record.

The test discriminates among candidate mechanisms. A summer-dominated peak confined to the forest clusters would indicate canopy-interception over-estimation or an analogous vertical-flux error. A pattern not confined to the forest clusters would indicate a different family of mechanism --- for example, recharge nonlinearity in the lumped monthly model, or an unmodelled non-vertical-flux input.

A cluster-stratified analysis aggregates the per-well climatology by the *k* = 5 partition and computes the winter-minus-summer contrast at each cluster, with bootstrap confidence intervals; the pipeline reports the complement, so signs are reversed in 24_05_diagnostic_summary.txt. The strongest contrast across the network is at open-dune C3 Western Residual (+8.6 mm, p \< 0.001), not at either forest cluster --- C4 Main Forest shows +5.4 mm (p = 0.068, marginal) and C5 Coastal Forest shows −0.3 mm (n.s.). This pattern is inconsistent with canopy-interception over-estimation as the sole driver: that mechanism would predict both forest clusters peaked and open dune flat, and the data show the reverse. A weak within-forest gradient (winter--summer contrast strengthens toward the ridge across 14 forest wells, r = −0.58) is consistent with a ridge-derived component but cannot be separated from a site-wide recharge term on the present evidence.

The full seasonal climatology has additional structure --- including non-trivial shoulder months --- that the winter-minus-summer contrast does not fully characterise; a detailed seasonal decomposition disaggregating the recharge and atmospheric-draw terms is the subject of a follow-up methodological treatment and is outside the Paper 1 scope.

### []{#anchor-16}S8.3 Ridge zone

The residuals in Figure 16 are drawn at the wells alone, so no residual value is shown on the rock-ridge bedrock outcrop on the northern boundary, which carries no reference monitoring well, or anywhere else between wells. The head-gradient arrows drawn beneath them come from the kriged water table of Section S11, not from the residuals.

### []{#anchor-17}S8.4 Status of the residual field

The spatially-structured residual field on which this section was originally built did not survive correction of the Script 20 computation: the structure was an artefact of two arithmetic defects in that computation --- canopy interception subtracted from rainfall at the forest wells as well as carried inside the fitted β₂·PET̄ term (above, and Section S9.2), and long-term climate means taken over the whole RAF Valley record from 1930 rather than over the monitoring period of the mean heads --- and the corrected field shows no spatial organisation on either axis. What the diagnostics establish is a bound on the monitoring design rather than a discrimination among mechanisms --- the seasonal test finds no summer signature that would indicate Thornthwaite misspecification, and the lag test could not have resolved a travel-time gradient had one been present. The per-well residuals are therefore presented as a diagnostic of how completely the lumped balance closes at each well, not as a quantified flux map.

## []{#anchor-18}S9. Water-balance decomposition

The SSM equation (Section S5.1) is, equivalently, a monthly water-balance identity that partitions the change in water-table head into four terms: recharge driven by rainfall, atmospheric draw driven by PET, drainage proportional to displacement above the lateral discharge horizon, and a residual ε that the lumped balance does not explain. Paper 1 uses this identity at two levels: a headline cluster water balance at cluster-mean scale (Section S9.1, the primary analysis), and a per-well residual field analysed as a spatial diagnostic (Section S8).

### S9.1 Cluster water balance (primary analysis)

The cluster water-balance decomposition (16_water_bal.py) is the headline analysis. The β coefficients fitted by the SSM are monthly-scale: β₁ is the response (in metres of Δ*h*) per metre of rainfall *during a given month*, and analogously for β₂ and β₃. The natural product β₁·*P̄* is therefore a *monthly* recharge contribution when *P̄* is a monthly mean.

For each cluster the partition is computed at monthly timestep as

$${\text{recharge} = \beta_{1}}\cdot\overline{P}$$

$${\text{atmospheric draw} = \beta_{2}}\cdot\overline{\mathit{PET}}$$

$${\text{drainage} = \beta_{3}}\cdot\overline{h_{\text{disp}}}$$

where *P̄* and PET̄ are the long-term means of the RAF Valley monthly climate forcing (computed as sum across the record divided by number of months observed; identical across clusters), *h̄*\<sub\>disp\</sub\> is the long-term monthly mean of the cluster centroid displacement, and the β values come from the cluster-mean SSM fit (Section S6.2, 03_03_cluster_mechanistic_coefficients.csv). Each contribution is then scaled to annual units by multiplication by 12 (months per year) for reporting in Table 3 of the main manuscript and Figure 7 --- equivalent to multiplying the β coefficient by the long-term *annual* mean of the corresponding driver (record sum ÷ years on record). The two normalisations give the same annual contribution.

The water-balance closure follows from the SSM equation evaluated at long-term means. Δ*h̄* over the full record is approximately zero (no net trend on the cluster centroid hydrograph), so the four right-hand-side terms must sum to approximately zero:

> $$\Delta{\overline{h} = \beta_{1}}\cdot\overline{P}-\beta_{2}\cdot\overline{\mathit{PET}}-\beta_{3}\cdot{\overline{h_{\text{disp}}} + \overline{\epsilon}}\approx 0$$

The mean residual ε̄ is what the lumped SSM does not explain, and is what the closure result quantifies. Across all five clusters this closure error is within 1.8 % of total losses, i.e. the three β-weighted long-term means account for at least 98 % of the long-term storage balance; the small remainder is the contribution of whatever the lumped three-term balance does not represent --- residual nonlinearity, spatial heterogeneity within the cluster, and error in the climate forcing among them. Its spatial structure is examined in Section S8, where the corrected per-well field is found to carry none.

### []{#anchor-19}S9.2 Canopy interception at the forest clusters

For C4 Main Forest and C5 Coastal Forest, Freeman (2008) measured canopy interception at 24 % of incident rainfall. The intercepted depth is

> *I*(*t*) = *i* · *P*(*t*)

where *i* = 0.24 is the canopy interception fraction (Freeman, 2008). This depth is not subtracted from rainfall anywhere in the fitted model. The cluster SSM (Section S6) is fitted on gross rainfall and on Thornthwaite PET computed above the canopy, so the interception loss is already carried inside the fitted β₂·PET̄ term. Interception is a partition of the available atmospheric energy budget rather than an additional demand on top of it: re-evaporation from intercepted rainfall on leaf surfaces, transpiration, and direct evaporation from the water table all draw on the same PET. Subtracting the intercepted depth from rainfall as well would count the same loss twice --- a defect that was present in the per-well residual computation of Script 20 until its correction on 2026-08-06 (Section S8), and that is not present in the cluster analysis reported here. The lower β₁ values at the forest clusters are therefore a fitted result rather than a consequence of any pre-adjustment: they reflect a damped water-table response to gross rainfall, consistent with Freeman\'s measurement of forest soil moisture at roughly half the open Warren\'s and a forest water table about 1.07 m deeper. The 24 % fraction enters the analysis only as a display partition. In the volumetric panel (Figure 7 panel b) the interception band is drawn identically on the input and the loss side, cancelling in the net surplus but making visible how much of the forest clusters\' rainfall is re-evaporated before it can reach the water table; it does not change total losses, the residual, or the balance at any cluster.

# **S10. Water-table-fluctuation specific yield**

Specific yield Sy --- the drainable porosity of the saturated medium near the water table --- is estimated in 17_wtf_specific_yield.py and is required to convert per-well water-table behaviour into a volumetric storage interpretation. It is also a substrate-character diagnostic in its own right, since a spatial gradient in Sy across an open dune-aquifer can indicate a corresponding gradient in sediment character (grain size, sorting, fines, weathering).

## **S10.1 The water-table-fluctuation method**

The water-table-fluctuation (WTF) method (Healy and Cook, 2002) estimates Sy from the relationship between net recharge and the corresponding water-table rise:

Sy = R / Δh

where R is the net recharge (rainfall minus PET, restricted to winter months when PET is small, R \> 0) and Δh is the corresponding water-table rise. Three parallel implementations of the method are used here; they agree closely at C3 Western Residual and on the coarse cross-cluster ordering, but diverge at C1 Lake Edge (Section S10.3).

**Approach A --- winter OLS.** The ratio above attributes the whole of the observed monthly change to recharge, whereas part of it is drainage occurring within the same month. Approach A removes that term first, using the state-space drainage coefficient: from Δh = (R / Sy) − β₃·\|h_prev\| it follows that R = Sy · (Δh + β₃·\|h_prev\|), so a no-intercept ordinary-least-squares regression of net recharge R against the drainage-corrected rise (Δh + β₃·\|h_prev\|) recovers Sy as the fitted slope directly. The fit is restricted to winter months (November--March) when Thornthwaite PET is below 25 mm month⁻¹ and net recharge approximates actual recharge well. This approach is statistically the most defensible (a single regression with a clear assumption) but provides limited uncertainty information beyond the regression standard error.

**Approach B --- event median**. An event-detection step identifies rising-limb months (winter months with positive recharge and positive Δh), computes Sy = R / Δh per event, and reports the cluster-level median together with its 25th and 75th percentiles. This is noisier per event but provides empirical uncertainty bounds and shows the within-cluster variability of the estimate.

**Approach C --- rapid recharge events**. A third estimator, after Crosbie et al. (2005), targets the same quantity by a route that shares the assumptions of neither of the first two. Approach A removes the drainage contribution to the observed rise mechanistically, using the fitted β₃; Approach B does not remove it at all and is correspondingly biased low. Approach C instead selects episodes in which the drainage contribution over the rise is negligible by construction, so that the uncorrected ratio is approximately unbiased. A candidate episode requires at least two consecutive prior months of falling or static water table (Δh ≤ 0), marking a drainage-dominated quasi-steady state; it begins at the first subsequent month with Δh \> 0, continues for at most two further months while the rise persists, and must accumulate a cumulative rise of at least 50 mm. For each qualifying episode Sy is the summed net recharge over the episode divided by the cumulative rise, retained only within the physically plausible interval 0.01 \< Sy \< 0.50 (the same interval applied per event in Approach B and in the per-well fits of Section S10.4). The cluster estimate is the median of qualifying episodes, with a 95 per cent confidence interval from 1000 bootstrap resamples of the episode set; episodes are non-overlapping. For the forested clusters the interception-corrected recharge of Section S10.2 is used, so the reported forest values are directly comparable with the corrected Approach B variant. Approach C is reported as an independent cross-check only and does not propagate to any downstream calculation.

## **S10.2 Cluster-level estimates**

Cluster-level event-median Sy estimates are reported as Table 4 of the main manuscript; all three approaches are read live from 17_wtf_01_sy_estimates.csv and compared in Section S10.3.

For the forested clusters (C4, C5) an interception-corrected variant is also reported. The correction applies Reff = (1 − i) · P − PET, with i = 0.24 (Freeman, 2008). The corrected values are the ones used in the Table 1 interpretation. The interception-corrected forest fits are reported by Approaches B (event median) and C (rapid-event). Approach A is not used for the corrected variant because the winter-only filter combined with the interception correction reduces the C4 and C5 sample sizes to the point where the no-intercept OLS becomes unstable; this is a sample-size limitation specific to the corrected forest case, not a general property of Approach A, which is reliable across all five uncorrected fits.

## **S10.3 Caveats**

Monthly resolution prevents isolation of individual storm events; the WTF estimates therefore conflate true gravity drainage with capillary-fringe release, and should be read as upper bounds on the storage coefficient rather than as point estimates of the gravity Sy alone (Healy and Cook, 2002; Scanlon et al., 2002). Slug tests or pumping tests at representative wells per cluster remain the gold-standard alternative; this would be the priority future field measurement. As with the SSM coefficients (Section S6.3), the robust and used quantity is the cross-cluster ordering, not the absolute magnitude. The three estimators converge closely at C3 Western Residual (0.35, 0.32, 0.31 for Approaches A, B, C) --- the value that anchors the Figure 18 forest-drawdown reach --- and Approaches B and C agree that C1 Lake Edge is the low-storage end (0.21 and 0.19), the higher winter-OLS estimate there (0.34) being consistent with the β₃ drainage correction over-correcting in the lake-buffered setting. Where an absolute Sᵧ nonetheless enters a downstream quantity --- the Figure 18 reach λ = √(Kb⁄(Sᵧ·β₃)) --- it is used as an order-of-magnitude input and reported accordingly (Section S13). The one genuinely method-dependent feature is the top of the ranking: the uncorrected winter-OLS fit places C5 highest, whereas the interception-corrected rapid-event estimate places C3 highest and the interception-corrected event estimate places C5 marginally above C3 (0.330 against 0.325).

## **S10.4 Spatial Sy surface**

A per-well Sy field (18_wtf_spatial.py) is produced by computing per-event Sy = R / Δh at every well in the reference network and reporting the per-well median across rising-limb events (Approach B applied at the well level, with per-well 25th and 75th percentiles for uncertainty), retained within the same 0.01 \< Sy \< 0.50 interval. Forest clusters (C4, C5) carry the interception correction directly in the recharge term --- Reff = (1 − 0.24) · P − PET --- and forest values therefore carry additional uncertainty associated with the canopy correction (Freeman, 2008). The contrast with the SSM treatment in Section S9.2 is a consequence of the two methods\' structure rather than an inconsistency: the WTF method estimates recharge directly, so the canopy loss must be removed from rainfall explicitly, whereas the SSM is fitted on gross rainfall and above-canopy PET and therefore already carries that loss inside the fitted β₂·PET̄ term. Two wells are excluded from the contour interpolation on physical grounds: CEH12 sits on the bedrock ridge in a forested area, where the WTF Sy reflects bedrock rather than the sand aquifer, and CEH15 sits in a low-lying slack within the plantation where the local hydrology is not representative of upland forest sand. The per-well Sy values are interpolated to a continuous surface (Figure 8 of the main manuscript) by the piecewise-linear procedure of Section S7, clipped to the site outline. The substrate-gradient interpretation of this pattern is developed in Section 5.2 of the main manuscript.

## []{#anchor-20}S11. Mean water-table surface and the Darcy flow field

### []{#anchor-21}S11.1 Mean head per well

A long-term mean water-table elevation (m OD) is computed at each well in the reference and extended networks that has a surveyed ground elevation, as that elevation plus the mean of every reading in the well's record (01b_water_table.py), and the mean water-table surface shown in Figure 15 of the main manuscript is kriged from those means. The same construction is repeated for a wet and a dry state of the network --- the months in the top and bottom decile of the network-median level --- with each well's mean taken over that state's months. A well enters only if it has enough readings in all three states, so the three surfaces rest on one set of 83 wells, the 66 of the reference network and 17 extended wells (n_wells_kriged, 01b_report_numbers.csv). For most reference-network wells the mean state is essentially the full 21-year monitoring window; for extended-network wells, recently-installed wells, and wells with intervention-driven baselines (the scraped well CEH36), the available record is shorter and the mean correspondingly reflects a narrower time window.

Taking each well's whole record, rather than a mean over a common reference period, keeps full network coverage at the periphery. It has two known costs: a record that starts or ends part-way through a year weights the seasons unevenly, and wells that join or leave the network at different times change the composition of the contributing set. Neither is corrected for.

### S11.2 Spatial head surface

[]{#anchor-22}The per-well mean heads are kriged, with a spherical variogram fitted to the wells, onto a 20 m grid over the study area (Figure 15). The water table is the one per-well quantity mapped by kriging rather than by the piecewise-linear surface of Section S7, because kriging admits the ground surface as an external drift and that drift can be tested. Four forms were compared: ordinary kriging with no drift, and drifts on the raw LiDAR DEM, on the DEM smoothed to the scale of the dune ridges and on a slack-floor lower envelope. Each was judged by leave-one-well-out error, with the withheld well left out of both the fit and the variogram, and by a physical test, whether the surface stands above the ground where Sentinel-2 never recorded water. Ordinary kriging was selected: it has the smallest leave-one-out error in all three states, with a median absolute error of 0.14 m and a bias of −0.005 m in the mean state (01b_01_drift_selection.csv). The edges of the surface are anchored rather than extrapolated. The sea is anchored along the high-water mark at a coastal head fitted to the coastal wells between mean tide level and mean high water, which returns 1.87 m OD, close to mean high water (coastal_head_m, 01b_report_numbers.csv). Three landward boundaries were each kept only because they did not worsen the leave-one-out error at the wells near them beyond a small tie margin: the Afon Braint at its channel elevation, Llyn Rhos-Ddu at its gauged level and the ridge well CEH12 at its measured depth below ground. A boundary along the whole ridge divide was tested and dropped, because it over-predicted the forest-edge wells. No elevation-model mask is applied: the water table need not lie below the ground everywhere, and in the slacks it periodically does not. The mean surface is a single mound, highest beside the bedrock ridge, falling to the coastal head along Caernarfon Bay and to the river and lake levels inland.

### []{#anchor-23}S11.3 Darcy flow field

The flow-direction field (Figure 15) is the negative gradient of the kriged head surface, which by Darcy's law gives the direction of groundwater flow through an isotropic aquifer:

> **direction of flow = −∇h**

where ∇h is evaluated by finite differences on the kriged grid. The arrows are drawn on a regular lattice coarser than the grid, each sized and coloured by the magnitude of the head gradient rather than normalised, so that steep and slack gradients are distinguished; arrows far from any dipwell are drawn faint, because there a boundary rather than a measurement sets them. Neither a hydraulic conductivity nor an aquifer thickness enters the field: it is the flow geometry of the mapped surface, not a discharge map.

Flow runs outward from the water-table high beside the bedrock ridge: south and south-west to Caernarfon Bay across the west and centre of the site, north towards Llyn Rhos-Ddu from the slacks beside the lake, and east and south-east to the Afon Braint. The pattern barely changes with the state of the aquifer: the median head gradient is 0.0071 in the wet state and 0.0062 in the dry, and the median flow direction at the slacks turns by 4.7° between the two (01b_report_numbers.csv). It is also insensitive to the boundary choices: fixing the coastal head anywhere from 0 m OD to mean high water changes the median slack flow direction by less than 1°, and removing the landward boundaries by about 2°; the runner-up drift, the smoothed DEM, changes it by about 19° (01b_05_sensitivity.csv). The DEM-derived topographic drainage paths are drawn on Figures 15 and 16 for comparison with this field. That overlay is a cartographic-context layer loaded by the pipeline from data/streams.kml and produced in QGIS using GRASS r.watershed with multiple-flow-direction routing and a 4000-cell channelisation threshold (≈ 1.6 ha minimum contributing area) against the LiDAR digital elevation model; it is rendered as cartographic context rather than as a pipeline output. The overlay is surface routing, which spills each closed slack over its saddle, and is drawn for comparison with the groundwater flow field, not as evidence for it.

## []{#anchor-24}S12. Coastal-retreat gradient regression

The Newborough coastline at the south-western dune front (Caernarfon Bay) is undergoing measurable retreat (Pye and Blott, 2024; Forgrave, 2020). The hypothesis tested in Section 4.11 of the main manuscript is that this coastal retreat is producing a spatially-structured water-table decline that decays inland --- a chronic, location-dependent forcing distinct from the spatially-uniform climate background.

### S12.1 Panel regression specification

The test (25_coastal_gradient.py) is a panel regression of well-level long-term water-table trends against perpendicular distance to the eroding shoreline:

$${t_{\mathit{ij}} = \delta}{\left( d_{i} \right) + \alpha_{i} + \alpha_{j} + \gamma}\cdot{W_{\mathit{ij}} + \epsilon_{\mathit{ij}}}$$

where *t*~*ij*~ is the monthly water-table change at well *i* in month *j*, *d*~*i*\ ~is well *i*'s perpendicular distance from the eroding shoreline, δ(·) is the modelled distance decay, α~*i*\ ~and α~*j*~ are well and month fixed effects (absorbed by within-well demeaning), *W*~*ij*~ is the cumulative water-balance covariate (the integrated SSM water balance to month *j*, included to absorb the spatially-uniform climate background and so isolate the spatially-structured residual), γ is its coefficient, and ε~*ij*~ is the residual.

Two functional forms are tested for the distance decay δ(·):

-   **Linear-capped**: δ(*d*) = δ₀ + (*c_far* − δ₀) · min(*d*/*L_cg*, 1). A linear decline from a coast-edge intercept δ₀ to a far-field background *c_far* over an inland reach *L_cg*; flat at *c_far* beyond *L_cg*.
-   **Exponential**: δ(*d*) = *c_far* + (δ₀ − *c_far*) · exp(−*d*/*L_cg*). An exponential decay from δ₀ at *d* = 0 to *c_far* asymptotically, with characteristic length *L_cg*.

[]{#anchor-25}Both forms are fitted by nonlinear least squares. Model selection between the two is by the Akaike information criterion (Akaike, 1974).

### []{#anchor-26}S12.2 Nested specifications

Four specifications are fitted to test robustness:

-   **Full network**: all open-dune and forested wells in the reference network, excluding the clearfell-zone wells (which carry a non-coastal management forcing).
-   **Forest-free**: the open-dune wells (C1, C2, C3) only, excluding all forested wells. This is the primary specification reported in the manuscript: it removes any contamination from forest interception or canopy-driven evaporative demand from the distance fit.
-   **C3-only**: wells in C3 Western Residual only, with the far-field background *c_far* fixed at the forest-free value rather than re-estimated. This tests whether the distance gradient is identifiable within the single cluster geographically closest to the eroding shoreline.
-   **Canopy-controlled full network** (Script 25 v1.9.0): the full network refitted with a canopy × time term on the *in_forest* land-cover flag, controlling forest cover explicitly rather than excluding it. The absorbed canopy coefficient is −9.0 ± 2.5 mm yr⁻¹ (linear-capped) --- the extra water-table fall under pine, net of distance to the coast --- and the coast-edge amplitude is essentially unchanged (δ₀ −32.26 against the forest-free −31.28), so the gradient does not depend on how forest cover is handled. It is a cross-check, not the headline; *full* and *full_canopy* are not comparable on AIC, as the canopy term is absorbed in the within-group step.

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

Confidence intervals are 95% (1.96 SE). The ± in the table are the fitted, row-basis standard errors; the uncertainties quoted in the manuscript are on the well basis (§S12.7). The forest-free linear-capped fit is the headline specification: δ₀ = −31.28 mm yr⁻¹, L_cg = 902 m, c_far = −0.30 mm yr⁻¹. The rate quoted in the manuscript is the fitted trend at 150 m from the shoreline, −26.38 mm yr⁻¹ (well-basis SE 3.49, §S12.7; fitted SE 1.45), rather than δ₀ itself: no well sits at the shoreline, and the two decay forms disagree there by 9.3 mm yr⁻¹ against 1.6 mm yr⁻¹ at 150 m. The constant *c_far* is the fitted far-field asymptote, not a climate background. It is separately identified --- its variance inflation factor against the cumulative water-balance covariate is 1.01 --- but it is unstable with respect to the fitting window, running from −0.30 to +23.96 mm yr⁻¹ as the window start is moved with the well set held fixed, so it is a window statistic rather than a rate.

### []{#anchor-28}S12.4 Model selection

Model selection by AIC favours the exponential form in the forest-free specification: the difference is −6.0 (−31,813.4 against −31,819.4, exp − lin-capped). On the full network the same comparison gives −5.1, and on C3-only −9.9, in each case favouring the exponential. Both fits agree on the sense of the gradient --- a coast-edge deepening that decays inland --- and on the magnitude of the coast-edge component (about −28 to −41 mm yr⁻¹), and both return a far-field asymptote c_far between −0.65 and +3.21 mm yr⁻¹ across the six fits. The choice of functional form changes the inland reach *L_cg* and the partition of the coast-edge intercept δ₀ between the two functions, but does not change the central finding: a near-coast water-table deepening of order 25--41 mm yr⁻¹ relative to the far field, declining over an inland reach of order 400--1000 m. Quoting the headline at 150 m from the shoreline, where the two forms agree to within 1.6 mm yr⁻¹, keeps the reported rate largely independent of that choice. The far-field level is not a climate background: *c_far* is separately identified but unstable with respect to the fitting window, as S12.3 sets out.

The headline values reported in the manuscript adopt the linear-capped fit for its Dupuit--Forchheimer interpretation of a finite inland reach, and because its far-field asymptote takes the same sign as the observed far-field trend where the exponential's does not: the exponential returns +2.01 mm yr⁻¹ against an observed far-field trend of −6.35 mm yr⁻¹ over the same window. Its reach is also the more interpretable of the two --- a capped-linear L_cg of 902 m is closer to the physical scale of the dune body than the exponential L_cg of 498 m, which is an e-folding length rather than a reach. AIC runs against that choice rather than with it, which is stated here rather than left implicit. The exponential fit is reported as a sensitivity case. The panel\'s climate covariate is an undecayed cumulative water balance, and it is not the best-fitting one available: exponential accumulators of the same series, with half-lives from two to twenty-four months, and a forward integration of the site\'s own state-space model all predict the water table better out of sample. Substituting any of them leaves δ₀ within −28.6 and −31.4 mm yr⁻¹ and L_cg within 902 and 1067 m. The undecayed form is retained because the covariate is a nuisance term, absorbed by the within-well demeaning rather than reported as a parameter, and selecting it on predictive fit would introduce a free parameter into a published estimate; the ranges given here are the specification uncertainty on δ₀ and *L_cg*.

### []{#anchor-29}S12.5 C5 out-of-sample sentinel

The C5 Coastal Forest well nw9, at 419 m from the eroding shoreline, shows a decline of −32.7 mm yr⁻¹ (p = 0.002, R² = 0.41, n = 20 years, from *25_02_per_well_summer_min_slopes.csv*). nw9 is under canopy and is excluded from the forest-free regression; it therefore functions as an out-of-sample sentinel, testing the fitted gradient at a near-coast position without contributing to it. Under the headline linear-capped fit the gradient at 419 m predicts a coastal-retreat contribution of −16.87 mm yr⁻¹, leaving −15.85 mm yr⁻¹ of the observed decline unaccounted for by distance to the shoreline. No climate background closes that gap. The two cluster-independent terms are the trend contribution the cumulative water-balance covariate carries, +2.95 mm yr⁻¹, and the fitted far-field asymptote c_far, −0.30 mm yr⁻¹; their sum is positive, so the remainder unexplained at this well is larger still, at −18.50 mm yr⁻¹. That remainder is what the substrate-position amplification developed in Section 5.2 of the manuscript addresses.

## []{#anchor-30}S13. Forest-interception drawdown reach (Figure 18)

Section 4.11 of the main manuscript renders the inland reach of forest-interception drawdown (20_spatial_figures.py for the figure) --- the distance over which interception-driven recharge suppression at the plantation boundary persists in the down-gradient open dune --- as a physical decay length. The calculation is a Dupuit-style drainage length:

> λ = √( *Kb* / (*S*y · β₃) )

where λ is the inland decay length, *K* the hydraulic conductivity, *b* the saturated thickness, *S*y the specific yield and β₃ the drainage coefficient (in daily units). The expression is the characteristic length over which a head perturbation at the source decays in a homogeneous, fixed-base unconfined aquifer.

The parameters used in Figure 18 are taken from C3 Western Residual, the open-dune cluster immediately down-gradient of the plantation boundary, with: *Sy = 0.298 (C3 per-well median of the Approach B event estimates, 18_wtf_01_well_sy_estimates.csv, Section S10.4); β₃ = 0.0616 month⁻¹ ≈ 2.02 × 10⁻³ day⁻¹* (C3 cluster-mean, Section S6.2); *K* = 6 m day⁻¹ (Betson et al., 2002, Section S2.1); *b* = 5 m (nominal saturated thickness, the latter uncertain by a factor of two or more given the absence of cored aquifer-thickness data; the geophysics of Bristow, 2002, indicates 12--27 m in the forest interior, but the open-dune thickness immediately south of the plantation boundary may be lower).

With these inputs, λ ≈ 220 m (drawdown_lambda in 20_report_numbers.csv, quoted to the nearest 10 m). The contours on Figure 18 should be read as an order-of-magnitude diagnostic of the inland reach, not as a calibrated prediction. λ scales as √(Kb): across the conductivity range reported for dune sand (2--20 m day⁻¹) it spans roughly 130--410 m, and across a saturated thickness of 3--8 m it spans 170--280 m. The order-of-magnitude conclusion --- that forest-interception drawdown reaches of order 200 m beyond the plantation boundary, not across the whole site --- holds across that range. Because the calculation carries canopy interception alone, it is an upper bound on the reach of the forest effect beyond the canopy and a lower bound on its magnitude.

This is the only output of the framework that depends on *K*. Every other coefficient surface, residual field, water-balance partition, *S*y estimate, coastal-retreat gradient and diagnostic synthesis presented in the manuscript is derived without a *K* estimate (Section 5.6 of the main manuscript). A measured *K* --- from slug tests at representative wells per cluster, the priority future field measurement --- would tighten only the Figure 18 reach calculation.

The empirically fitted coastal-retreat reach (Figure 19 of the manuscript) is *not* an analogue of the Figure 18 reach in this sense: the coastal-reach length *L_cg* is fitted directly from the panel regression (Section S12) and *K* and *b* do not enter its derivation. The forest and coastal reaches are therefore methodologically distinct: Figure 18 is a forward calculation from independent SSM and literature parameters, while Figure 19 is a back-calculation from observed water-table trends. Section 5.6 of the main manuscript discusses the implications.\

## []{#anchor-31}S14. Software, parameters and reproducibility

The full analysis pipeline is open source and version-controlled on GitHub at github.com/newbroman/Newborough_Hydrology (commit XXXXXXX at submission). A versioned snapshot of the code, the author-collected input data, and every output CSV referenced in this document is archived on Zenodo at DOI [10.5281/zenodo.19567643](https://doi.org/10.5281/zenodo.19567643). The pipeline release is recorded in the pipeline_release field of outputs/pipeline_manifest.json. The Zenodo deposit is the citable, immutable reference; the GitHub repository carries any subsequent updates.

**Software environment.** Python 3.12.3. The complete, version-pinned environment is specified in requirements.txt; key packages are NumPy 2.4.6, SciPy 1.17.1, pandas 3.0.3 and statsmodels 0.14.6 (numerical and statistical processing); GeoPandas 1.1.3, Rasterio 1.5.0, Shapely 2.1.2 and pyproj 3.7.2 (spatial); and Matplotlib 3.10.9 (plotting). Random seeds for every stochastic step (bootstrap resampling, cluster stability) are defined centrally in utils/config.py, giving byte-equivalent reproduction.

**Cartographic-context overlays.** Site-overview cartography combines pipeline outputs with cartographic-context overlays loaded by the pipeline from KML files in data/. The data/streams.kml overlay --- the topographic drainage network, drawn only where it is set against the groundwater flow field (Figures 15 and 16) --- was produced in QGIS 3.34.4-Prizren using the GRASS provider, tool r.watershed, with multiple-flow-direction routing and a 4000-cell channelisation threshold (≈ 16,000 m² minimum contributing area). The input was the merged 2 m LiDAR DEM (mergeddem.tif, EPSG:27700) used throughout the pipeline. The line network was extracted via r.to.vect and exported to KML, then post-processed to remove drainage paths below 0 m AOD (intertidal/foreshore) by sampling the DEM at each line vertex; the masking utility is included in the repository as a one-shot data-preparation step. Other context overlays (Features.kml, site_boundary.kml, clearfell.kml) are similarly produced or maintained in GIS and loaded by the pipeline via src/utils/map_utils.py add_kml_features(). The Python pipeline reproduces the analytical work; these GIS files are cartographic context.

**Pipeline orchestration.** The pipeline is run as a single command (python run_analysis.py) which executes the analytical steps in canonical order. Each step writes its outputs to a step-specific subdirectory under outputs/ and updates the canonical pipeline parameters file (Section S2.2) where appropriate. A full run on a standard workstation completes in approximately 30 minutes.

**Pipeline parameters table.** Headline values used in this document, all read live from the canonical CSVs at the time of submission:

  ------------------------------------------- --------------------- --------------------------------------------
  Network size (reference)                    66 wells              01_wells_provenance.csv
  Drainage datum *z₀*                         3.7 m                 pipeline_scenario_params.csv
  HEADLINE_LAG                                0                     pipeline_scenario_params.csv
  Forest interception                         0.24                  Freeman (2008), config.py
  C1--C5 β₁, β₂, β₃, *R*²                     (see Section S6.2)    03_03_cluster_mechanistic_coefficients.csv
  Cluster *S*y                                (see Section S10.2)   17_wtf_01_sy_estimates.csv
  Coastal δ₀, *L_cg*, *c_far* (forest-free)   (see Section S12)     25_01_panel_fit_parameters.csv
  nw9 decline                                 (see Section S12.5)   25_02_per_well_summer_min_slopes.csv
  Hydraulic conductivity *K*                  6 m day⁻¹             Betson et al. (2002)
  ------------------------------------------- --------------------- --------------------------------------------

**Data availability.** The dipwell water-level records and the well location/elevation data analysed here were collected by the author and are deposited, in cleaned form, in the Zenodo archive alongside the code (Newborough_Cleaned_For_Model.csv, Well_locations_height.csv). The RAF Valley climate series (monthly rainfall, and the mean-temperature series used to derive Thornthwaite PET) are Met Office historic station observations, © Crown Copyright, Met Office, available from the Met Office at https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/valleydata.txt under the Open Government Licence v3.0, and are not re-archived here. This dataset contains public sector information licensed under the Open Government Licence v3.0.

**Code availability.** All scripts, all output CSVs and figures, and a complete README.md are at github.com/newbroman/Newborough_Hydrology. The repository licence is MIT for code and CC-BY-4.0 for the author-collected data and figures. The author can be contacted at the address on the title page for any aspect of the analysis not covered here.

## S15. Supplementary references

References cited only in this SI document, not in the main manuscript:

> Calinski, T. and Harabasz, J. (1974) A dendrite method for cluster analysis. *Communications in Statistics* 3(1), 1--27.

> Crosbie, R.S., Binning, P. and Kalma, J.D. (2005) A time series approach to inferring groundwater recharge using the water table fluctuation method. **Water Resources Research** 41(1), W01008. doi:10.1029/2004WR003077.

> Liao, T.W. (2005) Clustering of time series data --- a survey. *Pattern Recognition* 38(11), 1857--1874.

> Milligan, G.W. and Cooper, M.C. (1985) An examination of procedures for determining the number of clusters in a data set. *Psychometrika* 50(2), 159--179.

All other references --- Akaike (1974), Bear (1972), Betson, Connell and Bristow (2002), Bristow (2002), Bristow and Bailey (2001), Curreli et al. (2013), Davy et al. (2006), Fetter (2001), Forgrave (2020), Freeman (2008), Freeze and Cherry (1979), Healy and Cook (2002), Hollingham (2026b, in preparation), Knotters and van Walsum (1997), Pye and Blott (2024), Ranwell (1958), Rao and Srinivas (2006), Rhind et al. (2001), Robins and Davies (2015), Rousseeuw (1987), Scanlon et al. (2002), Stratford et al. (2007), Ward (1963), Young (2011) --- appear in the main manuscript's reference list and are not duplicated here.

[]{#supporting-information}[]{#anchor-32}End of Supporting Information.
