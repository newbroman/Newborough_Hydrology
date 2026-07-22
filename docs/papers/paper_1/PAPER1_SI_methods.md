# Supporting Information

## Hollingham (2026), Paper 1 — *A parameter-sparse state-space framework for aquifer characterization from long-term manual dipwell records: a 21-year case study at Newborough Warren*

*To be submitted with the main manuscript to Journal of Hydrology.*

This Supporting Information document gives the methodological detail underlying the analyses reported in the main text. It is self-contained: every parameter, equation, and design choice that supports a result in the manuscript is laid out here. Section numbers in the manuscript refer back to the headed sections here (S1–S16).

The pipeline and outputs are archived in full (Section S15). The headline numerical values used in the manuscript are reproduced live from the pipeline output CSVs cited at the foot of each section, and are unchanged at the time of submission.

---

## Contents

| Section | Page |
|---|---:|
| S1. Field protocol, data preparation, and date semantics | 2 |
| S2. Constants and configuration | 4 |
| S3. Behavioural clustering and the *k* = 5 partition | 5 |
| S4. Pearson affinity audit and spatial confidence | 7 |
| S5. The state-space model — displacement formulation | 7 |
| S6. SSM regression: per-well and cluster-mean fits, with LCSC | 10 |
| S7. SSM vs traditional linear model (benchmarking) | 12 |
| S8. Spatial interpolation of SSM coefficients | 13 |
| S9. Residual-field diagnostics | 14 |
| S10. Water-balance decomposition | 15 |
| S11. Water-table-fluctuation specific yield | 16 |
| S12. Mean water-table surface and the Darcy flow field | 18 |
| S13. Coastal-retreat gradient regression | 19 |
| S14. Forest-interception drawdown reach (Figure 17) | 21 |
| S15. Software, parameters and reproducibility | 22 |
| S16. Supplementary references | 23 |

---

## S1. Field protocol, data preparation, and date semantics

The 88-well manual dipwell network is read monthly by the author. Readings are taken at the **end of each month** — typically the last day of that month, or the first day or two of the following month. Each reading is the water level *for the month just ended*: a measurement taken on 1 May 2026 represents the **April 2026** water level. Climate data from RAF Valley Meteorological Station (53°14′32″N, ≈16 km from the site) is a monthly total for the same calendar month: rainfall *P* (mm), and minimum and maximum temperatures from which monthly Thornthwaite PET is computed at the RAF Valley latitude (53.25°).

**Bucketing.** Readings on physical dates ≤ day 15 of month *M* are bucketed into month *M*−1 because they belong to the previous month's water table. Readings on physical dates > day 15 of month *M* are bucketed into month *M*. The cutoff is at day 15 because field readings are nearly always taken either within the first week of a month or on the last day of the preceding month; day 15 is comfortably in the middle of the gap.

**Date semantics.** Every monthly timestamp in the pipeline is recorded in `YYYY-MM-01` date format. The `-01` day component is a formatting convention used to make monthly records machine-readable as dates; it does not refer to the 1st of the month. A row labelled `2007-07-01` is "July 2007": it contains the end-of-July water level and July's climate totals.

A concrete example for well CEH9, row `2007-07-01`:

| Field | Value | Meaning |
|---|---:|---|
| *h*(*t*) | −0.610 m | End-of-July reading |
| *h*(*t*−1) | −0.440 m | End-of-June reading |
| Δ*h* | −0.170 m | Water-table change *during* July |
| *P* | 101.9 mm | July rainfall total |
| PET | 98.5 mm | July Thornthwaite PET |
| *h*<sub>disp,prev</sub> | 3.260 m | 3.7 + (−0.440), displacement above drainage datum at end of June |

The state-space model (Section S5) uses this row to explain July's 170 mm drop using July's rainfall, July's PET, and the water-table position at the start of July (= end of June).

**Above-Ordnance-Datum invariance.** The above-Ordnance-Datum (mAOD) water-table elevation is a physical quantity independent of the ground surface above it. Removing material from the surface does not move the water table; the mAOD reading is the same before and after. Era-specific data handling is therefore only required where depth-below-ground is the quantity of interest, not where mAOD water-table elevations are being averaged or compared.

---

The data-preparation step (`01_data_prep.py`) reads the three raw inputs — `Newborough_Cleaned_For_Model.csv` (water-table records), `Well_locations_height.csv` (well coordinates and DEM-derived ground elevations), `RAF_Valley_Climate.csv` (monthly rainfall and temperatures) — and produces the cleaned, bucketed, masked frames consumed by every downstream script.

### S1.3 Cleaning and gap rules

Water-table records are screened for sentinel values and obvious measurement errors. Short interpolation gaps (a single missing month with valid neighbours) are filled by linear interpolation, with the gap limit set to `limit = 1`; the pre-2026 value of `limit = 3` was found to introduce phase artefacts in winter-peak detection and was tightened in the April 2026 audit (`CHANGELOG.md` entry under Script 01 v1.3.0). After the change, 72 cells out of approximately 110,000 well-month observations across the 88-well network are filled by interpolation; the remainder are observed.

### S1.4 Reference-network selection

The reference network (66 wells, Section S3) is the subset of the 88-well network that meets all of:
- record start ≥ 2005 and record continuing through `REFERENCE_CUTOFF_DATE` (2026-02-01);
- not on the blacklist of wells with known tidal influence (notably the `pdfs` well at the south-eastern shore);
- not within the clearfell-impacted zone (used for the BACI analysis in Paper 2 but excluded from Paper 1's network-mean coefficients).

The extended network adds the remaining 22 wells (clearfell-zone, shorter records, scraped wells) for spatial visualization only; coefficients fitted to extended-network wells are reported only where stated, and the per-cluster coefficients in Table 1 are reference-network only.

### S1.5 Output

Cleaned monthly per-well frames, the climate frame, and the canonical pipeline parameters CSV are written to `outputs/01_data_prep/`. The well-provenance audit (`01_wells_provenance.csv`) records membership in each network and lists the reason for any exclusion, supporting reviewer reproducibility.

---

## S2. Constants and configuration

All pipeline constants and the canonical runtime-parameters file are described here. The cluster partition that determines which wells belong to which group is the output of the behavioural clustering step (Section S3); the full table is given there.

### S2.1 Constants

All values that are constant across the pipeline are defined in a single centralized configuration file, so that any change propagates everywhere and no script can redefine a value locally. The constants used in Paper 1 are:

| Constant | Value | Origin |
|---|---|---|
| `DRAINAGE_DATUM` | 3.7 m | Sensitivity analysis (Section S5.4) |
| `HEADLINE_LAG` | 0 | Field-convention bucketing (Section S1) |
| `FOREST_INTERCEPTION` | 0.24 | Freeman (2008), Newborough Corsican pine |
| `FOREST_CIDS` | (4, 5) | *k* = 5 partition; forested clusters |
| `REFERENCE_CUTOFF_DATE` | 2026-02-01 | Network selection (Section S1) |
| `RAF_VALLEY_LAT_DEG` | 53.25 | 53°14′32″N |
| Hydraulic conductivity *K* | 6 m day⁻¹ | Betson et al. (2002) tracer test |

The 24% Corsican pine canopy-interception fraction is from Freeman (2008), the most spatially proximate canopy-interception measurement available for the Newborough plantation. *K* = 6 m day⁻¹ is from the single tracer test reported in the contemporaneous CCW groundwater-modelling study; it is required only in the Figure 17 forest-drawdown reach calculation (Section S14) and does not enter any other framework output.

### S2.2 Canonical pipeline parameters file

A single canonical table of pipeline parameters, `pipeline_scenario_params.csv`, is written by the data-preparation step (Section S1) and updated in place by the downstream steps that fit new parameter values (the SSM regression, the BACI auxiliaries, and the WTF specific-yield estimation). Every downstream step reads its pipeline parameters from this file rather than from a hardcoded value, which rules out a category of inconsistencies that can otherwise propagate silently through long pipelines.

---

## S3. Behavioural clustering and the *k* = 5 partition

### S3.1 Distance metric and linkage

Cluster identification (`02_clustering.py`) operates on a pairwise distance matrix between per-well hydrographs. The metric is one minus the Pearson correlation coefficient between any two wells' monthly time series over their common record window. A small minimum-overlap requirement (≥ 36 months) prevents short pairs from dominating; pairs that do not meet it are flagged as undefined and the affected well is excluded from clustering rather than imputed.

Ward's hierarchical linkage (Ward, 1963) is then applied. Ward's criterion minimizes the increase in within-cluster sum of squares at each merge, which produces compact, well-separated clusters when the underlying data have structure. The choice of Ward over alternatives (single, complete, average linkage) reflects its well-attested performance on behavioural time-series data (Rao and Srinivas, 2006; Liao, 2005) and its tendency to produce spherical, balanced clusters of comparable size (Milligan and Cooper, 1985) — desirable for downstream interpretation against physical substrate units.

### S3.2 Cluster-count selection

The clustering literature offers several internal-validity indices for choosing the cluster count *k*. The two used here are the Rousseeuw silhouette coefficient (Rousseeuw, 1987) and the Calinski–Harabasz pseudo-*F* statistic (Calinski and Harabasz, 1974). Both are evaluated for *k* in {2, ..., 8}. Each curve has its own maximum and the maxima do not generally agree; this is a known property of internal validity indices applied to real data.

For Newborough the silhouette curve maximizes at *k* = 2 (~0.41) and falls monotonically to *k* = 8 (~0.18). The Calinski–Harabasz curve also favours small *k*. By the internal-validity criterion alone, the best choice would be *k* = 2: a single eastern–western split.

This was not adopted. The internal-validity indices reward separability; they are agnostic to the physical interpretability of the resulting clusters. A *k* = 2 partition collapses C4 Main Forest into either the eastern (C1, C2) or the western (C3) block depending on which well dominates the merge order, losing the canopy-interception signature that drives the management interpretation. *k* = 4 collapses C5 Coastal Forest into C3, losing the coastal-retreat signature. The Coastal Forest cluster is small (*n* = 5) and lies at the edge of the network, where bootstrap stability is fragile (Section S3.5), but its physical distinctness — Corsican pine on the coastal sand body, with the most rapid recent water-table decline in the network — is the basis on which it is retained as a separate cluster.

This study therefore selects *k* = 5 on a physical–mechanistic basis rather than on an internal-validity-index basis, and reports the indices transparently. The decision is taken openly in Section 3.2 of the main manuscript and is also reflected in the Pearson affinity audit (Section S4), which shows that C5 wells sit at the edge of cluster space rather than in its interior, but that the edge position is consistent and reproducible across the 21-year record.

### S3.3 The k = 5 partition table

The reference network is partitioned into five behavioural clusters by Ward's linkage on correlation distance between cluster-mean hydrographs (Section S3). The cluster IDs and labels are:

| ID | Label | n | Substrate / vegetation |
|---:|---|---:|---|
| 1 | C1 Lake Edge | 7 | Lake-adjacent (Llyn Rhos-Ddu), finer sediments |
| 2 | C2 Dune | 24 | Mature open dune, eastern block |
| 3 | C3 Western Residual | 21 | Deep aeolian sand, western block |
| 4 | C4 Main Forest | 9 | Corsican pine on deep sand, northern ridge flank |
| 5 | C5 Coastal Forest | 5 | Corsican pine, coastal margin |

Membership counts (canonical *k* = 5 partition under the live data-preparation pipeline) total 66 wells in the reference network. The extended network of 22 additional dipwells is used for spatial visualization and BACI work but is not part of the partition. Llyn Rhos-Ddu is treated as a fixed-head boundary feature rather than a behavioural cluster.

### S3.4 Canonical ID anchoring

Ward's linkage produces clusters in an arbitrary integer-numbering order that depends on the merge sequence. To make cluster IDs stable across pipeline runs and across partition changes, the clustering step carries a lookup table mapping each canonical cluster ID to one or two anchor wells whose membership identifies the cluster. After Ward returns its raw partition, the clusters are re-numbered so that the anchor wells fall in the expected ID, and an automated check confirms that the renumbering succeeded. This convention has the practical effect that "C1" refers to the same physical cluster across all pipeline outputs, irrespective of run order.

### S3.5 Stability

Bootstrap resampling of the per-well hydrograph set (100 bootstrap draws, with sampling at the well level) returns the same five clusters with stable core memberships at C1, C2, C3 and C4; C5 has lower bootstrap stability because its small membership (*n* = 5) is sensitive to the inclusion or exclusion of any single well. The most marginal members of C5 (those with the lowest Pearson affinity to the C5 centroid, Section S4) are not the wells that anchor the cluster; the anchors ceh16 and nw9 remain in C5 across all bootstrap draws.

---

## S4. Pearson affinity audit and spatial confidence

The clustering algorithm assigns each well to the cluster with whose centroid it has the highest Pearson correlation. The *strength* of that assignment — how clearly a well belongs to its cluster, rather than sitting near the boundary between two — is recoverable from the affinity matrix: each well's Pearson correlation against every cluster centroid.

A well with a high primary affinity and substantially lower secondary affinities is a *core member* of its cluster. A well with a primary affinity only slightly above its secondary is *gradational* — it sits at the boundary between two behavioural patterns. The Pearson affinity audit (`05_pearson_affinity.py`, Figure 5 of the main manuscript) makes this structure visible at the well level.

The audit shows three patterns. First, the cluster cores (C1, C2, C4 anchors; central C3; ceh16 and nw9 in C5) are spatially compact and behaviourally distinct. Second, the boundary between C2 (eastern Dune) and C3 (Western Residual) is gradational rather than sharp — several wells in the centre-east of the network have primary affinity to one cluster but a secondary affinity within 0.05 of the primary, indicating that they sit on a continuous substrate gradient between the two clusters rather than within a structural discontinuity. Third, C5 Coastal Forest is a tight core (anchors ceh16, nw9) with the lowest affinity to any other cluster, indicating that even though C5 has only five members, those five behave consistently with each other and distinctly from the rest of the network.

The C2/C3 gradation is discussed at length in Section 5.1 of the main manuscript and is the basis for the "behaviourally coherent cluster on a continuous substrate gradient" interpretation of C3. It is also why the discussion uses "C3 transitional zone" rather than "C2/C3 boundary".

The output `05_pear_01_spatial_confidence_map.png` is Figure 5 of the main manuscript. The underlying affinity matrix is in `outputs/05_pearson_affinity/05_affinity_per_well.csv`.

---


## S5. The state-space model — displacement formulation

The state-space model (SSM) is the methodological core of the analysis. The cluster characterization, the specific-yield estimation, the water-balance decomposition, the residual field and the coastal-retreat gradient regression all rest on it.

### S5.1 Equation

The fitted equation is

> Δ*h*(*t*) = β₁ · *P*(*t*) − β₂ · PET(*t*) − β₃ · (*D* + *h*(*t*−1))

where Δ*h*(*t*) is the change in water table during month *t* (m, signed; negative when the water table falls); *P*(*t*) and PET(*t*) are the rainfall and Thornthwaite PET during month *t* (m); *h*(*t*−1) is the water table at the end of month *t*−1 (m, signed; negative below ground surface); *D* is the drainage datum, *D* = 3.7 m (Section S2); and β₁, β₂, β₃ are positive coefficients fitted by ordinary least squares (no intercept).

The quantity *D* + *h*(*t*−1) is the displacement of the water table above the drainage datum at the start of month *t*. With *D* = 3.7 m and a typical end-of-previous-month head of −0.4 m, displacement is 3.3 m; with a deeper end-of-month head of −2.0 m, displacement is 1.7 m. The β₃ term says: the deeper the water table sits below ground at the start of a month, the smaller the drainage during that month — consistent with Darcy's law for a shallow unconfined aquifer drained to a fixed lateral discharge horizon.

### S5.2 Sign conventions

All three β values are reported positive. Signs are baked into the design matrix, not into the coefficient values. In the design matrix the β₁ column is +*P* (a positive β₁ means rainfall raises the water table), the β₂ column is −PET (a positive β₂ means PET lowers the water table), and the β₃ column is −(*D* + *h*<sub>prev</sub>) (a positive β₃ means displacement above the datum drives drainage downward). A fitted β₁ ≤ 0 or β₂ ≤ 0 halts the pipeline because either is physical nonsense; β₃ > 0 is soft-asserted (a negative β₃ is anomalous and worth investigating but does not halt the pipeline).

### S5.3 Why *h*(*t*−1) rather than *h*(*t*)

The drainage term uses the water-table position at the end of the previous month, not the contemporaneous level, for two reasons. First, *h*(*t*) is the dependent variable through Δ*h* = *h*(*t*) − *h*(*t*−1); using it simultaneously as a predictor would create simultaneity bias and break the interpretation of β₃. Second — and physically — drainage during a month is driven by the head at the *start* of that month, not the head at the end; the end-of-month head is the result of drainage, not its cause. The displacement at the start of month *t* equals the displacement at the end of month *t*−1, hence the *h*(*t*−1) form.

### S5.4 Drainage datum

The 3.7 m drainage datum was selected to give comfortable β₃ identification at the forest clusters (C4 Main Forest, C5 Coastal Forest), where β₃ is hardest to pin down because the water table sits deepest below ground there. A sensitivity sweep over *D* (Figure S1, output `03_08_datum_sensitivity.csv`) compares the live empirical minimum *D* = 1.7 m — the shallowest depth at which all five clusters simultaneously satisfy β₃ > 0 with *p* < 0.05 — against the operating value *D* = 3.7 m. At the empirical minimum C4's β₃ *p*-value sits at the significance edge (0.040); at 3.7 m it drops to 0.0027, with C5 also gaining substantially (β₃ *p*-value from 4 × 10⁻¹¹ to 4 × 10⁻¹⁶, *R*² from 0.648 to 0.680). The trade-off is small *R*² penalties at C1 Lake Edge (−0.052) and C2 Dune (−0.029), where β₃ is over-determined and remains significant at *p* < 10⁻²⁵ at either depth.

The role of the datum is to shift the reference for the drainage term. Without it (i.e. with *h*(*t*−1) instead of (*D* + *h*(*t*−1)) in the design column), the C3, C4 and C5 clusters produced negative β₃ estimates. This was a sign-convention artefact: it reflected that the OLS was correlating drainage with a quantity that crossed zero rather than staying on one side of a fixed reference. Setting the reference 3.7 m below ground places every observation comfortably on the positive side of the datum.

Δ*h* is invariant under the choice of datum (the datum cancels in first differences). β₁ and β₂ are also invariant. Only β₃ shifts numerically, in a way that preserves its physical interpretation as a Darcy drainage coefficient.

### S5.5 Implementation: two levels of fit

The SSM is fitted at two distinct levels of aggregation and Paper 1 uses both. The distinction is material because the two fits address different questions and feed different downstream products. Section S6 maps the fits to the products explicitly; the rest of this subsection covers the construction of the design matrix, which is common to both.

**Cluster-mean fit — the primary characterization tool.** A single OLS regression is run for each cluster, with the per-month design rows of every well in the cluster stacked into one regression. The result is one set of coefficients (β₁, β₂, β₃) per cluster, with the regression *R*² and per-coefficient *p*-values that anchor Table 1 of the main manuscript. The cluster-mean fit is what underwrites the substrate-gradient interpretation of Sections 5.1–5.2, the lumped climate-storage contribution (Section S6.4), and the drainage-timescale τ = *S*<sub>y</sub>/β₃ used throughout the discussion. Stacking across all wells in a cluster has the practical benefit that per-well noise averages out and the cluster-level signal — what separates C1 from C2, C2 from C3, and the forest from the open-dune blocks — is recovered with much tighter uncertainty than any single well permits.

**Per-well fit — the spatial-products tool.** The SSM is also fitted independently at each well in the reference network, producing a separate (β₁, β₂, β₃) at every well. The per-well fits feed the spatial products: the coefficient atlas (Figure 11, four interpolated surfaces built from the per-well values), the per-well residual field (Figure 15, the per-well residuals from the per-well fit interpolated to a continuous surface), and the per-well water-balance decomposition (Section S10). Per-well fits are noisier than the cluster-mean fit because each is conditioned on a single well's record; per-well coefficient values are therefore best read in the spatial pattern they form across the network rather than at any single point.

**Common design-matrix construction.** The design matrix is built one (well, month) row at a time. For each row the well's water-table series is joined with the RAF Valley climate record on the bucketed monthly index, and Δ*h* and *h*<sub>disp,prev</sub> are computed, producing a row with columns *h*, *h*<sub>prev</sub>, Δ*h*, *P*, PET and *h*<sub>disp,prev</sub>. Row construction is identical for either level of fit; what differs is which rows are pooled into the OLS regression. The per-well fit at well *w* runs OLS over the rows belonging to *w* alone, yielding a per-well (β₁, β₂, β₃). The cluster-mean fit at cluster *c* runs a single OLS over the union of rows from every well in *c*, yielding one cluster-level set of coefficients. A three-coefficient OLS regression (no intercept) is fitted in either case and reports the coefficients with their standard errors, *p*-values from a two-sided *t*-test against zero, regression *R*², and residual series. The row construction and the regression are implemented once in a shared library; there is no reimplementation elsewhere in the pipeline.

### S5.6 Residual serial correlation and inference validity

Because the SSM is a monthly time-series regression, the classical OLS standard errors that produce the coefficient *p*-values are valid only if the residuals are free of substantial serial correlation. This is tested directly (`22_residual_lag_analysis.py`, output `22_05_ssm_residual_autocorrelation.csv`). The headline (no-intercept) SSM is refitted at each of the 66 reference wells and the residuals are examined: the median Durbin–Watson statistic is 2.20 (interquartile range 2.11–2.37) and the median lag-1 autocorrelation is −0.12. The residuals therefore carry a slight *negative* first-order autocorrelation rather than the positive persistence that would inflate significance — a direct consequence of the drainage term −β₃·(*D* + *h*<sub>prev</sub>), which acts as an error-correction term and absorbs the first-order persistence of the level series. Negative residual autocorrelation makes the OLS standard errors mildly conservative, not anti-conservative. A Ljung–Box test at lag 12 rejects white-noise residuals at 19 of the 66 wells; this reflects the *seasonal* residual structure characterized independently in Section S9.3 (winter–spring phased), not low-order persistence, and it is orthogonal to the coefficient standard errors.

As a robustness check the coefficient *p*-values are re-estimated with heteroskedasticity- and autocorrelation-consistent (Newey–West / HAC) standard errors, using the *n*-adaptive rule-of-thumb truncation lag *L* = ⌊4·(*n*/100)<sup>2/9</sup>⌋. Across the 198 coefficient tests (66 wells × three coefficients), the HAC and OLS significance verdicts at α = 0.05 agree in all but one instance — β₂ at CEH25, which moves from *p* = 0.079 to *p* = 0.028, i.e. *toward* significance. No coefficient that OLS reports as significant is overturned under HAC. The classical-OLS inference underlying the coefficient tables is therefore sound. These diagnostics are run at the per-well level, which is the noisier of the two fits; the cluster-mean fits that anchor Table 1 pool the rows of every well in a cluster and are correspondingly better-conditioned.

---


## S6. State-space regression and the lumped climate-storage characterization

### S6.1 Per-well and cluster-mean fits, and where each is used

Section S5.5 introduced the two levels of fit; both are implemented in `03_state_space_model.py`. The mapping of each fit to the downstream products of Paper 1 is:

| Output | Fit used | Section |
|---|---|---|
| Table 1 cluster mechanistic coefficients | Cluster-mean | S6.2 |
| Lumped climate-storage contribution (LCSC) | Cluster-mean | S6.4 |
| Drainage timescale τ = *S*<sub>y</sub>/β₃ by cluster | Cluster-mean | S10, main text §5.5 |
| Traditional-linear-model benchmarking | Cluster-mean | S6.5 |
| Substrate-gradient interpretation (Sections 5.1–5.2) | Cluster-mean | main text |
| Coefficient atlas, Figure 11 (β₁, β₂, β₃, LCSC surfaces) | Per-well, interpolated | S8 |
| Per-well residuals and residual field (Figure 15) | Per-well, interpolated | S9 |
| Per-well water-balance decomposition | Per-well | S9 |
| Coastal-retreat panel regression (Section S13) | Per-well (cumulative water-balance covariate) | S12 |
| Residual-field diagnostics (cross-correlation, climatology) | Per-well (residual series) | S13 |
| Pearson affinity audit (Figure 5) | Independent of SSM — operates on raw hydrographs | S7 |
| Water-table-fluctuation specific yield | Independent of SSM — operates on recharge / Δ*h* | S10 |
| Mean water-table head surface (Figure 14) | Independent of SSM — operates on observed mean heads | S11 |

The cluster-mean fit is the primary characterization tool: Table 1 of the manuscript and the substrate-gradient discussion that runs through Sections 5.1, 5.2 and 5.5 are all carried by the cluster-mean coefficients. The per-well fit is the spatial-products tool: it lets the cluster characterization be projected as continuous surfaces across the site for visual and diagnostic interpretation.

Three of the Paper 1 outputs are independent of the SSM regression entirely. The Pearson affinity audit operates on raw cluster-centroid hydrographs and provides a behavioural cross-check on cluster membership. The water-table-fluctuation specific-yield estimation operates on the recharge–rise relationship at observed monthly events and provides a storage-side mechanistic cross-check. The mean water-table head surface is a direct spatial interpolation of observed long-term mean heads. These independent products converge on the same cluster structure that the SSM identifies; that convergence — same physical groupings emerging from three independent statistical operations — is what justifies the cluster framework, rather than the SSM regression alone.

### S6.2 Cluster-mean coefficients

The headline cluster-mean coefficients used throughout the manuscript, read live from `outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv`, are:

| Cluster | β₁ (recharge) | β₂ (atmospheric draw) | β₃ (drainage) | *R*² | *n* | LCSC % |
|---|---:|---:|---:|---:|---:|---:|
| C1 Lake Edge | 4.58 | 0.96 | 0.090 | 0.732 | 236 | 21.8 |
| C2 Dune | 3.98 | 1.77 | 0.066 | 0.747 | 247 | 25.1 |
| C3 Western Residual | 3.57 | 1.85 | 0.058 | 0.813 | 248 | 28.0 |
| C4 Main Forest | 2.52 | 2.55 | 0.020 | 0.685 | 236 | 39.7 |
| C5 Coastal Forest | 2.41 | 1.32 | 0.045 | 0.680 | 238 | 41.5 |

All three coefficients are highly significant at every cluster (β₁: every *p* < 10⁻⁴⁶; β₂: every *p* < 10⁻⁴; β₃: every *p* < 10⁻²). The within-cluster *R*² varies between 0.68 and 0.81 — high for a three-coefficient model fitted to monthly water-table change in a system with non-trivial drainage geometry.

The cluster-level coefficients have direct physical interpretations: β₁ is the marginal water-table response (in metres) per metre of rainfall over the month; β₂ is the corresponding response per metre of PET; β₃ is the drainage decay rate. The forest clusters (C4, C5) carry the lowest β₁ — consistent with canopy interception of incident rainfall — and C4 also carries the highest β₂ together with the lowest β₃. C5's β₂ is conspicuously lower than C4's despite a common Corsican pine canopy; this contrast is discussed in Section 5.2 of the manuscript and is the basis for the "substrate and topographic position dominate the cluster-level β₂ contrast" argument.

### S6.3 Caveats on OLS coefficient values

The OLS fits are biased high in absolute magnitude under all three coefficients, in a way that affects absolute scale but not ranking. Two structural sources contribute. First, the design matrix carries non-zero collinearity between *P* and the other regressors at the monthly time-step, particularly during recharge events when *P*, the recovery in *h*, and the consequent rise in displacement co-vary; the OLS distributes this co-variation across the coefficients in a way that inflates each individual estimate slightly. Second, errors-in-variables bias on the regressors (RAF Valley *P* and Thornthwaite PET are themselves estimates, not point measurements) attenuates the regressor scale and inflates the fitted coefficients to compensate. Both biases are common to lumped state-space hydrological models fitted by OLS and are documented in the transfer-noise-model and WTF literatures (Knotters and van Walsum, 1997; Healy and Cook, 2002).

The practical implication is that the coefficients should be read as *ranking*-reliable but not absolute-flux-calibrated. Cluster-to-cluster contrasts (e.g. C4 has substantially higher β₂ than C5) are robust under bootstrap resampling and under reasonable variations in the regression specification; absolute values are not. This caveat is foregrounded in Section 5.2 of the main manuscript, where the β₂ scope is explicitly limited to the cluster-level contrast rather than to point-flux interpretation.

### S6.4 Lumped climate-storage contribution

The lumped climate-storage contribution (LCSC) is the fraction of monthly Δ*h* variance explained by climate forcing alone, conditional on the start-of-month displacement. It is computed from a nested fit that fixes β₃ at its cluster-mean value and reports the fraction of total variance attributable to the (β₁·*P* − β₂·PET) component versus the residual. The LCSC column in the table above ranges from 22% at C1 Lake Edge (where rapid drainage to the lake dominates the variance) to 41% at C5 Coastal Forest (where the climate-forcing contribution is relatively larger because drainage is slow). The LCSC ordering by cluster is consistent with the cluster-mean β₃ ordering, as it must be, and provides a sanity check on the regression.

## S7. SSM vs traditional linear model (benchmarking)

The SSM-vs-TLM benchmark (`08_model_benchmarking.py`) fits a traditional linear model (TLM) in which the drainage term is referenced to the ground surface rather than to a fixed sub-surface datum (i.e. *D* = 0 in the Section S5 equation) was fitted as a benchmark. The TLM returns negative β₃ at C3, C4 and C5 — a sign-convention artefact when the regressor crosses zero rather than staying on one side of a fixed reference (Section S5.4). The displacement-form SSM resolves this and produces physically interpretable β₃ values at every cluster. The Δ*R*² between the two specifications is small at C1 and C2 (where the TLM also returns positive β₃ values, near-equivalent to the displacement form), but large at C3, C4 and C5 where the TLM β₃ is non-physical.

The TLM benchmark is reported as a methodological diagnostic — to demonstrate that the displacement formulation is not just a notational choice but a substantive improvement at the forest and western-residual clusters, where the drainage signature would otherwise be lost or mis-signed.

---

## S8. Spatial interpolation of SSM coefficients

The per-well β₁, β₂, β₃ values (Section S6.1) are interpolated to continuous surfaces across the site (`07_spatial_coefficients.py`) using inverse-distance weighting (IDW). The interpolation is purely geometric; the surfaces are *aggregators of point responses*, not the output of a calibrated distributed-flow model. This distinction is foregrounded in the manuscript and in the figure captions.

### S8.1 IDW configuration

The IDW exponent is *p* = 2, a conventional choice that emphasizes local control. The grid is built on a LiDAR-derived 5 m digital elevation model resampled to a 40 m regular working grid; grid resolution sensitivity was checked against a 50 m grid (no qualitative change to the surfaces, mean coefficient values within 1% across the network).

### S8.2 Masking

Grid cells over the northern rock-ridge bedrock outcrop (those above the 20 m AOD contour) are masked from the coefficient interpolations: there are no monitoring wells over the bedrock outcrop, and the aquifer parameterization does not apply on bare metamorphic basement. Cells outside the dune-field site polygon (sea, drift agriculture to the north, river) are also masked. The mean water-table surface (Section S12) uses a wider mask that includes the ridge zone, because water levels are observable on the ridge in principle; the residual field (Section S10) is presented unmasked but with caption notes flagging the ridge zone as extrapolation (Section S9.5 and Fig. 15 caption).

### S8.3 Bandwidth and edge effects

The IDW search bandwidth is set to include all wells within 1 km of each grid cell, or the nearest six wells, whichever is more permissive. The bandwidth-six-wells minimum prevents over-smoothing in the well-sparse north-western corner; the 1 km cap prevents under-smoothing in the dense central network. Edge effects (the south-western and south-eastern margins are bounded by the coast and the Menai Strait) are partly mitigated by the polygon mask but the surfaces remain less reliable within ~200 m of the coastal edge than in the interior. This is flagged in the relevant figure captions.

### S8.4 Coefficient atlas

The four interpolated coefficient surfaces (β₁, β₂, β₃, LCSC) are presented as Figure 11 of the main manuscript and constitute the "coefficient atlas". The surfaces are intended as diagnostic readings of the cluster characterization extended continuously across the site; they are not flux maps and not predictions in any forward-modelling sense.

---


## S9. Residual-field diagnostics

The state-space regression (Section S6) produces a per-month residual at every well: the portion of the observed Δ*h* not explained by the lumped balance β₁·*P* − β₂·PET − β₃·(*D* + *h*<sub>prev</sub>). Summed over the 18-water-year reference window, these monthly residuals form a per-well total (positive at a well where the observed water table rose more, or fell less, than the lumped balance predicts; negative at a well where the model over-predicted the water-table position). Interpolating those per-well totals across the network by the same IDW procedure as the coefficient surfaces (Section S8) produces the *residual field* (Figure 15 of the main manuscript), which is the object analysed here. The formal partition of the modelled signal into its three SSM components, together with the interception correction applied at forest wells, is given in Section S10; the residual is the same in either treatment.

The spatially-structured residual field is the empirical anchor of the Section 5.4 discussion of unmodelled lateral fluxes. Three diagnostic tests were run to discriminate between candidate mechanisms.

### S9.1 Cross-correlation lag test (`22_residual_lag_analysis.py`)

If the largest positive residuals along the northern forest margin and ridge flank represent ridge-derived lateral input — a Darcy-conveyed subsidy from the metamorphic bedrock ridge through the down-gradient open dune — then a distance-dependent transport lag should be detectable: the time between a recharge event at the ridge and the corresponding response at down-gradient wells should increase systematically with distance. The cross-correlation lag test computes lagged correlations between (i) a ridge-zone composite recharge signal and (ii) the de-trended water-table series at each down-gradient well, identifying the lag at maximum correlation per well.

The test returns a null result: there is no monotonic distance-dependent lag structure across the down-gradient wells. The lag-at-maximum-correlation is dispersed (range 0 to 4 months) and uncorrelated with distance from the ridge.

This null result must be qualified by sampling frequency: monthly observations are an order of magnitude coarser than the days-to-weeks transit times expected for fracture-flow input from a metamorphic bedrock ridge, so a real ridge-derived lag could be invisible at this resolution. The null result therefore bears on what the present record can resolve rather than on whether the mechanism is operative.

### S9.2 Ridge-recharge lag hypothesis test (`23_ridge_recharge_lag_test.py`)

A complementary test specifies an explicit recharge model with a ridge-input component (a fraction *r* of measured rainfall is conveyed from the ridge to each down-gradient well at a fitted lag) and tests whether including *r* improves the SSM fit at the ridge-adjacent wells. The test is structurally degenerate at the available record length: the parameters *r* and the SSM β₁ are not jointly identifiable in the presence of the noisy monthly water-table response, and the fitted *r* values are unbounded by the data. The test is reported in §5.3 of the manuscript as a structural-identifiability finding rather than as a mechanism rejection.

### S9.3 Seasonal climatology test (`24_residual_seasonality.py`)

If the positive residuals along the forest margin represented systematic underestimation of summer evaporative demand — for example, an under-resolved canopy-driven evaporative loss not captured by Thornthwaite PET — then the residual field should peak in summer when those fluxes are active. The seasonal climatology test computes the monthly mean residual at each well across the 21-year record and tests whether the peak month is summer (June–August) or some other season.

The result: residuals peak in winter and early spring at the great majority of wells and at none in summer. This is inconsistent with any vertical-flux parameterization error — systematically underestimated summer PET, an incomplete canopy-interception correction, or any under-resolved summer evaporative demand, all of which would peak in summer when those fluxes are active. The winter–spring phase therefore rules out the vertical-flux family of errors and points to either a winter-phased nonlinear recharge mechanism or a ridge-derived lateral input arriving during the months of greatest rainfall.

### S9.4 CEH14 point-source attribution

The single largest positive residual in the network, at well CEH14, is decoupled from the ridge-margin interpretation. CEH14 lies adjacent to a cottage whose septic-tank drainage field discharges into the well's footprint, providing a continuous, locally confined influx that accounts for both the well's anomalous negative β₃ (drainage decay is masked by the continuous input) and its outlier positive residual. The ridge-margin pattern is therefore read on the remaining wells.

### S9.5 Ridge-zone extrapolation

The interpolated residual surface (Figure 15) extends over the rock-ridge bedrock outcrop on the northern boundary, which carries no monitoring wells; values shown there are extrapolations from the surrounding network and are not interpretable as residuals on bedrock. This is flagged in the Fig. 15 caption.

### S9.6 Status of the residual interpretation

The combined picture from the three diagnostic tests is that the spatially-structured residual field is real and reproducible across the 21-year record, but its attribution between a genuine ridge-derived lateral subsidy and an unidentified modelling artefact cannot be settled by the present analysis. The residual field is therefore presented as a *structural diagnostic of where the lumped balance is insufficient*, not as a quantified flux map.

---


## S10. Water-balance decomposition

A water-balance decomposition is computed at every reference-network well from the SSM fit. The decomposition partitions the monthly water-table change into its three SSM-driven components — recharge, atmospheric draw, and drainage — plus a residual:

> Δ*h*(*t*) = (β₁ · *P*(*t*)) − (β₂ · PET(*t*)) − (β₃ · (*D* + *h*(*t*−1))) + ε(*t*)

The residual ε(*t*) is the part of the observed Δ*h*(*t*) that the lumped SSM does not explain. Summed over a multi-year window, ε integrates to a per-well *residual*: the net excess or deficit between observed water-table change and modelled water-table change over the integration window.

### S10.1 Per-well residual

Per-well residuals are computed (`16_water_bal.py`) over the full reference window (water-year 2007 to water-year 2025, 18 complete water-years). Positive residuals indicate that the well's observed water-table level rose more (or fell less) than the lumped SSM predicts — a candidate signature of an unmodelled lateral subsidy. Negative residuals indicate the converse — a candidate signature of unmodelled loss or unmodelled additional ET.

### S10.2 Interception correction

For wells in the forested clusters (C4 Main Forest, C5 Coastal Forest), incident rainfall is replaced by *effective rainfall*:

> *P*<sub>eff</sub>(*t*) = (1 − *i*) · *P*(*t*)

where *i* = 0.24 is the canopy interception fraction (Freeman, 2008). PET is not adjusted, because Thornthwaite PET is an energy-based atmospheric demand independent of land cover; reducing only *P* is the physically correct partition. The interception correction is applied uniformly through the forest growth phase (the entire 21-year monitoring window for C4; the corresponding window for C5).

### S10.3 Spatial residual field

The per-well residuals are interpolated to a continuous surface by the same IDW procedure as the coefficient surfaces (Section S8). The residual field (Figure 15 of the main manuscript) shows a clearly spatially-structured pattern, with positive residuals concentrated along the northern forest margin and ridge flank, decaying south-eastward along the Darcy flow field. This structure is the empirical signature interpreted in Section 5.4 of the manuscript as a candidate ridge-derived lateral subsidy, with the caveats developed in Section S9.

The residual at CEH14 — the largest single positive residual in the network — is decoupled from the ridge-margin interpretation: CEH14 is adjacent to a cottage whose septic-tank drainage field discharges into the well's footprint, providing a continuous, locally confined influx that accounts for both its anomalous negative β₃ and its outlier residual. The ridge-margin signal is therefore read on the remaining wells.

---


## S11. Water-table-fluctuation specific yield

Specific yield *S*<sub>y</sub> — the drainable porosity of the saturated medium near the water table — is estimated in `17_wtf_specific_yield.py` and is required to convert per-well water-table behaviour into a volumetric storage interpretation. It is also a substrate-character diagnostic in its own right, since a spatial gradient in *S*<sub>y</sub> across an open dune-aquifer can indicate a corresponding gradient in sediment character (grain size, sorting, fines, weathering).

### S11.1 The water-table-fluctuation method

The water-table-fluctuation (WTF) method (Healy and Cook, 2002) estimates *S*<sub>y</sub> from the relationship between net recharge and the corresponding water-table rise:

> *S*<sub>y</sub> = *R* / Δ*h*

where *R* is the net recharge (rainfall minus PET, restricted to winter months when PET is small, *R* > 0) and Δ*h* is the corresponding water-table rise. Two parallel implementations of the method are used here, with closely-agreeing results.

**Approach A — winter OLS.** A no-intercept ordinary-least-squares regression of Δ*h* against *R* is fitted at each cluster, restricted to winter months (November–March) when Thornthwaite PET is below 25 mm month⁻¹ and net recharge approximates actual recharge well. The fitted slope is *S*<sub>y</sub><sup>−1</sup>; *S*<sub>y</sub> is its reciprocal. This approach is statistically the most defensible (a single regression with a clear assumption) but provides limited uncertainty information beyond the regression standard error.

**Approach B — event median.** An event-detection step identifies rising-limb months (winter months with positive recharge and positive Δ*h*), computes *S*<sub>y</sub> = *R* / Δ*h* per event, and reports the cluster-level median together with its 25th and 75th percentiles. This is noisier per event but provides empirical uncertainty bounds and shows the within-cluster variability of the estimate.

### S11.2 Cluster-level estimates

Cluster-level *S*<sub>y</sub> estimates from both approaches, read live from `outputs/17_wtf_specific_yield/17_wtf_01_sy_estimates.csv`:

| Cluster | OLS *S*<sub>y</sub> (winter) | Event median *S*<sub>y</sub> | Event IQR |
|---|---:|---:|---|
| C1 Lake Edge | 0.334 (SE 0.043, *R*² 0.62) | 0.21 | [0.13, 0.26] |
| C2 Dune | 0.328 (SE 0.034, *R*² 0.67) | 0.27 | [0.20, 0.37] |
| C3 Western Residual | 0.343 (SE 0.021, *R*² 0.84) | 0.33 | [0.29, 0.41] |
| C4 Main Forest | 0.297 (SE 0.017, *R*² 0.87) | 0.31 | [0.26, 0.39] |
| C5 Coastal Forest | 0.410 (SE 0.022, *R*² 0.88) | 0.36 | [0.32, 0.43] |
| C4 (interception-corrected) | — | 0.25 | [0.18, 0.32] |
| C5 (interception-corrected) | — | 0.32 | [0.24, 0.40] |

For the forested clusters (C4, C5) an interception-corrected variant is also reported. The correction applies *R*<sub>eff</sub> = (1 − *i*) · *P* − PET, with *i* = 0.24 (Freeman, 2008), and reduces the apparent *S*<sub>y</sub> by approximately 0.06 at C4 and 0.04 at C5. The corrected values are the ones used in the Table 1 interpretation. The corrected fits are reported by Approach B (event median) only; the corrected Approach A OLS fits were numerically unstable and are not reported.

### S11.3 Caveats

Monthly resolution prevents isolation of individual storm events; the WTF estimates therefore conflate true gravity drainage with capillary-fringe release, and should be read as upper bounds on the storage coefficient rather than as point estimates of the gravity *S*<sub>y</sub> alone (Healy and Cook, 2002; Scanlon et al., 2002). Slug tests or pumping tests at representative wells per cluster remain the gold-standard alternative; this would be the priority future field measurement.

### S11.4 Spatial *S*<sub>y</sub> surface

A per-well *S*<sub>y</sub> field (`18_wtf_spatial.py`) is produced by applying the Approach A regression at each well individually (open-dune clusters C1–C3 only; forest wells excluded because the interception correction is applied uniformly at the cluster level and per-well forest fits are noisier). The per-well *S*<sub>y</sub> values are interpolated to a continuous surface (Figure 8 of the main manuscript) by the IDW procedure of Section S8. The surface shows no discontinuity at the cluster margins — *S*<sub>y</sub> varies smoothly across the network — and a planar trend (*R*² ≈ 0.62) with a south-westward gradient (azimuth ≈ 235°). The substrate-gradient interpretation of this pattern is developed in Section 5.2 of the main manuscript.

---


## S12. Mean water-table surface and the Darcy flow field

### S12.1 Mean head per well

A long-term mean water-table elevation is computed at every well in the reference network (`19_spatial_groundwater.py`). The mean is taken over the full reference window (water-year 2007 to water-year 2025); for wells with shorter records (extended-network or scraped wells, included for spatial visualization only) the mean is taken over the available record. Heads are reported in metres above Ordnance Datum (mAOD).

### S12.2 Spatial head surface

The per-well mean heads are interpolated to a continuous surface by IDW (Section S8) on a 40 m regular grid masked to the dune-field site polygon plus the rock-ridge zone (heads are observable at the ridge in principle, unlike SSM coefficients). The interpolated head surface (Figure 14 of the main manuscript) is broadly smooth, with the water table sitting close to the ground surface in dune-slack areas (≤ 1 m below ground for SD15b-defining wells) and dipping westward and south-westward across the open dune.

### S12.3 Darcy flow field

A Darcy flow-field is computed from the head surface by

> **q** = −*K* · ∇*h*

where ∇*h* is the spatial gradient of the head surface and *K* is the bulk hydraulic conductivity (Section S2.1, 6 m day⁻¹ from Betson et al., 2002). The resulting vector field is reported as a directional flow pattern rather than as a quantitative discharge map: the head surface is observed but *K* is uncertain (single tracer test, no spatial variation), so the flux magnitudes are not calibrated.

The directional pattern is robust regardless of the choice of *K*: the field shows south-westward flow in the western half of the site (toward Caernarfon Bay) and south-eastward flow in the eastern half (toward the Menai Strait), with the watershed boundary tracking the topographic ridge mid-site. The Darcy field is broadly consistent with the DEM-derived flow-accumulation network on the site overview (Figure 1), which supports the use of topographic flow-accumulation as an operational proxy for subsurface flow divides at this site — although the two are co-determined by the underlying till and bedrock architecture rather than one causing the other.

---


## S13. Coastal-retreat gradient regression

The Newborough coastline at the south-western dune front (Caernarfon Bay) is undergoing measurable retreat (Pye and Blott, 2024; Forgrave, 2020). The hypothesis tested in Section 4.11 of the main manuscript is that this coastal retreat is producing a spatially-structured water-table decline that decays inland — a chronic, location-dependent forcing distinct from the spatially-uniform climate background.

### S13.1 Panel regression specification

The test (`25_coastal_gradient.py`) is a panel regression of well-level long-term water-table trends against perpendicular distance to the eroding shoreline:

> *t*<sub>*ij*</sub> = δ(*d*<sub>*i*</sub>) + α<sub>*i*</sub> + α<sub>*j*</sub> + γ · *W*<sub>*ij*</sub> + ε<sub>*ij*</sub>

where *t*<sub>*ij*</sub> is the monthly water-table change at well *i* in month *j*, *d*<sub>*i*</sub> is well *i*'s perpendicular distance from the eroding shoreline, δ(·) is the modelled distance decay, α<sub>*i*</sub> and α<sub>*j*</sub> are well and month fixed effects (absorbed by within-well demeaning), *W*<sub>*ij*</sub> is the cumulative water-balance covariate (the integrated SSM water balance to month *j*, included to absorb the spatially-uniform climate background and so isolate the spatially-structured residual), γ is its coefficient, and ε<sub>*ij*</sub> is the residual.

Two functional forms are tested for the distance decay δ(·):

- **Linear-capped**: δ(*d*) = δ₀ + (*c* − δ₀) · min(*d*/*L*, 1). A linear decline from a coast-edge intercept δ₀ to a far-field background *c* over an inland reach *L*; flat at *c* beyond *L*.
- **Exponential**: δ(*d*) = *c* + (δ₀ − *c*) · exp(−*d*/*L*). An exponential decay from δ₀ at *d* = 0 to *c* asymptotically, with characteristic length *L*.

Both forms are fitted by nonlinear least squares. Model selection between the two is by the Akaike information criterion (Akaike, 1974).

### S13.2 Nested specifications

Three nested specifications are fitted to test robustness:

- **Full network**: all open-dune and forested wells in the reference network, excluding the clearfell-zone wells (which carry a non-coastal management forcing).
- **Forest-free**: the open-dune wells (C1, C2, C3) only, excluding all forested wells. This is the primary specification reported in the manuscript: it removes any contamination from forest interception or canopy-driven evaporative demand from the distance fit.
- **C3-only**: wells in C3 Western Residual only, with the far-field background *c* fixed at the forest-free value rather than re-estimated. This tests whether the distance gradient is identifiable within the single cluster geographically closest to the eroding shoreline.

### S13.3 Parameter values

Fitted parameters, read live from `outputs/25_coastal_gradient/25_01_panel_fit_parameters.csv`:

| Specification | Model | *n* | AIC | δ₀ (mm yr⁻¹) | *L* (m) | *c* (mm yr⁻¹) |
|---|---|---:|---:|---:|---:|---:|
| Full | linear-capped | 12,457 | −35,168.4 | −29.2 ± 1.9 | 971 ± 58 | −6.8 ± 0.6 |
| Full | exponential | 12,457 | −35,166.8 | −39.1 ± 3.0 | 514 ± 84 | −4.5 ± 1.2 |
| Forest-free | linear-capped | 11,778 | −34,260.9 | −28.8 ± 1.9 | 894 ± 52 | −6.4 ± 0.6 |
| Forest-free | exponential | 11,778 | −34,261.4 | −40.2 ± 3.8 | 407 ± 64 | −5.2 ± 0.9 |
| C3-only | linear-capped (*c* fixed) | 3,794 | −10,647.4 | −26.1 ± 2.6 | 972 ± 83 | −6.40 |
| C3-only | exponential (*c* fixed) | 3,794 | −10,654.4 | −29.5 ± 3.8 | 652 ± 108 | −5.24 |

Confidence intervals are 95% (1.96 SE). The forest-free linear-capped fit is the headline specification: δ₀ = −28.8 mm yr⁻¹, *L* = 894 m, *c* = −6.4 mm yr⁻¹.

### S13.4 Model selection

The ΔAIC between linear-capped and exponential in the forest-free specification is approximately 0.5 in favour of the exponential — a small difference that does not strongly discriminate the two forms. Both fits agree on the sense of the gradient (a coast-edge deepening that decays inland), on the magnitude of the coast-edge component (~−29 to −40 mm yr⁻¹), and on the far-field background (~−4.5 to −6.4 mm yr⁻¹). The choice of functional form changes the inland reach *L* and the partition of the coast-edge intercept δ₀ between the two functions, but does not change the central finding: a near-coast water-table deepening of order 25–40 mm yr⁻¹ above the climate background, declining over an inland reach of order 400–1000 m to a far-field climate background of about −6.4 mm yr⁻¹.

The headline values reported in the manuscript adopt the linear-capped fit for its slightly more conservative coast-edge magnitude (−28.8 vs −40.2 mm yr⁻¹) and its more interpretable reach length (a capped-linear *L* of 894 m is closer to the physical scale of the dune body than the exponential *L* of 407 m, which is the *e*-folding length). The exponential fit is reported as a sensitivity case.

### S13.5 C5 out-of-sample sentinel

The C5 Coastal Forest well nw9, at 419 m from the eroding shoreline, shows a decline of −32.8 mm yr⁻¹ (*p* = 0.002, *R*² = 0.41, *n* = 20 years from `outputs/25_coastal_gradient/25_02_per_well_summer_min_slopes.csv`). nw9 is forested and is excluded from the forest-free regression; it therefore functions as an out-of-sample sentinel, testing the fitted gradient at a near-coast position without contributing to it. The fitted gradient at 419 m predicts a coastal-retreat contribution of approximately −15 mm yr⁻¹ under either functional form; the residual between the observed −32.8 mm yr⁻¹ and the predicted −15 mm yr⁻¹ is consistent with the climate background (−6.4 mm yr⁻¹) and an additional substrate-position amplification developed in Section 5.2 of the manuscript.

---


## S14. Forest-interception drawdown reach (Figure 17)

Section 4.11 of the main manuscript renders the inland reach of forest-interception drawdown (`20_spatial_figures.py` for the figure) — the distance over which interception-driven recharge suppression at the plantation boundary persists in the down-gradient open dune — as a physical decay length. The calculation is a Dupuit-style drainage length:

> λ = √( *Kb* / (*S*<sub>y</sub> · β₃) )

where λ is the inland decay length, *K* the hydraulic conductivity, *b* the saturated thickness, *S*<sub>y</sub> the specific yield and β₃ the drainage coefficient (in daily units). The expression is the characteristic length over which a head perturbation at the source decays in a homogeneous, fixed-base unconfined aquifer.

The parameters used in Figure 17 are taken from C3 Western Residual, the open-dune cluster immediately down-gradient of the plantation boundary, with: *S*<sub>y</sub> = 0.33 (C3 event-median, Section S11.2); β₃ = 0.058 month⁻¹ ≈ 1.93 × 10⁻³ day⁻¹ (C3 cluster-mean, Section S6.2); *K* = 6 m day⁻¹ (Betson et al., 2002, Section S2.1); *b* = 5 m (nominal saturated thickness, the latter uncertain by a factor of two or more given the absence of cored aquifer-thickness data; the geophysics of Bristow, 2002, indicates 12–27 m in the forest interior, but the open-dune thickness immediately south of the plantation boundary may be lower).

With these inputs, λ ≈ 223 m (matching the value rendered on Figure 17). The contours on Figure 17 should be read as an order-of-magnitude diagnostic of the inland reach, not as a calibrated prediction. λ scales as √(*Kb*), so a factor of two uncertainty in *b* corresponds to a factor of √2 ≈ 1.4 in λ; the true reach could plausibly be anywhere between roughly 150 m and 320 m on reasonable variations of the input assumptions. The order-of-magnitude conclusion — that forest-interception drawdown is felt within roughly 100–300 m of the plantation boundary, not across the whole site — is robust to those uncertainties.

This is the only output of the framework that depends on *K*. Every other coefficient surface, residual field, water-balance partition, *S*<sub>y</sub> estimate, coastal-retreat gradient and diagnostic synthesis presented in the manuscript is derived without a *K* estimate (Section 5.6 of the main manuscript). A measured *K* — from slug tests at representative wells per cluster, the priority future field measurement — would tighten only the Figure 17 reach calculation.

The empirically fitted coastal-retreat reach (Figure 18 of the manuscript) is *not* an analogue of the Figure 17 reach in this sense: the coastal-reach length *L* is fitted directly from the panel regression (Section S13) and *K* and *b* do not enter its derivation. The forest and coastal reaches are therefore methodologically distinct: Figure 17 is a forward calculation from independent SSM and literature parameters, while Figure 18 is a back-calculation from observed water-table trends. Section 5.6 of the main manuscript discusses the implications.

---


## S15. Software, parameters and reproducibility

The full analysis pipeline is open source and version-controlled on GitHub at `github.com/newbroman/Newborough_Hydrology`. A versioned snapshot of the code, the author-collected input data, and every output CSV referenced in this document is archived on Zenodo at the time of submission (DOI to be inserted on acceptance). The pipeline version is recorded in the `pipeline_version` field of `outputs/pipeline_manifest.json`. The Zenodo deposit is the citable, immutable reference; the GitHub repository carries any subsequent updates.

**Software environment.** Python 3.12.3. The complete, version-pinned environment is specified in `requirements.txt`; key packages are NumPy 2.4.6, SciPy 1.17.1, pandas 3.0.3 and statsmodels 0.14.6 (numerical and statistical processing); GeoPandas 1.1.3, Rasterio 1.5.0, Shapely 2.1.2 and pyproj 3.7.2 (spatial); and Matplotlib 3.10.9 (plotting). Random seeds for every stochastic step (bootstrap resampling, cluster stability) are defined centrally in `utils/config.py`, giving byte-equivalent reproduction.

**Pipeline orchestration.** The pipeline is run as a single command (`python run_analysis.py`) which executes the analytical steps in canonical order. Each step writes its outputs to a step-specific subdirectory under `outputs/` and updates the canonical pipeline parameters file (Section S2.2) where appropriate. A full run on a standard workstation completes in approximately 30 minutes.

**Pipeline parameters table.** Headline values used in this document, all read live from the canonical CSVs at the time of submission:

| Symbol | Value | Source CSV |
|---|---|---|
| Network size (reference) | 66 wells | `01_wells_provenance.csv` |
| Drainage datum *D* | 3.7 m | `pipeline_scenario_params.csv` |
| HEADLINE_LAG | 0 | `pipeline_scenario_params.csv` |
| Forest interception | 0.24 | Freeman (2008), `config.py` |
| C1–C5 β₁, β₂, β₃, *R*² | (see Section S6.2) | `03_03_cluster_mechanistic_coefficients.csv` |
| Cluster *S*<sub>y</sub> | (see Section S11.2) | `17_wtf_01_sy_estimates.csv` |
| Coastal δ₀, *L*, *c* (forest-free) | −28.83, 894, −6.40 | `25_01_panel_fit_parameters.csv` |
| nw9 decline | −32.8 mm yr⁻¹ | `25_02_per_well_summer_min_slopes.csv` |
| Hydraulic conductivity *K* | 6 m day⁻¹ | Betson et al. (2002) |

**Data availability.** The dipwell water-level records and the well location/elevation data analysed here were collected by the author and are deposited, in cleaned form, in the Zenodo archive alongside the code (`Newborough_Cleaned_For_Model.csv`, `Well_locations_height.csv`). The RAF Valley climate series (monthly rainfall, and the mean-temperature series used to derive Thornthwaite PET) are Met Office historic station observations, © Crown Copyright, Met Office, available from the Met Office at `https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/valleydata.txt` under the Open Government Licence v3.0, and are not re-archived here. This dataset contains public sector information licensed under the Open Government Licence v3.0.

**Code availability.** All scripts, all output CSVs and figures, and a complete `README.md` are at `github.com/newbroman/Newborough_Hydrology`. The repository licence is MIT for code and CC-BY-4.0 for the author-collected data and figures. The author can be contacted at the address on the title page for any aspect of the analysis not covered here.

---


## S16. Supplementary references

References cited only in this SI document, not in the main manuscript:

Calinski, T. and Harabasz, J. (1974) A dendrite method for cluster analysis. *Communications in Statistics* 3(1), 1–27.

Liao, T.W. (2005) Clustering of time series data — a survey. *Pattern Recognition* 38(11), 1857–1874.

Milligan, G.W. and Cooper, M.C. (1985) An examination of procedures for determining the number of clusters in a data set. *Psychometrika* 50(2), 159–179.

All other references — Akaike (1974), Bear (1972), Betson, Connell and Bristow (2002), Bristow (2002), Bristow and Bailey (2001), Curreli et al. (2013), Davy et al. (2006), Fetter (2001), Forgrave (2020), Freeman (2008), Freeze and Cherry (1979), Healy and Cook (2002), Hollingham (2026b, in preparation), Knotters and van Walsum (1997), Pye and Blott (2024), Ranwell (1958), Rao and Srinivas (2006), Rhind et al. (2001), Robins and Davies (2015), Rousseeuw (1987), Scanlon et al. (2002), Stratford et al. (2007), Ward (1963), Young (2011) — appear in the main manuscript's reference list and are not duplicated here.

---

*End of Supporting Information.*
