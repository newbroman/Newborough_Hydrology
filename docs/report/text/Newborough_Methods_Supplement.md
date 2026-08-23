<!-- GENERATED MIRROR of docs/report/Newborough_Methods_Supplement_v1_9_43.odt — do not edit.
     Regenerate with: python3 tools/refresh_mirrors.py -->

# []{#anchor}[]{#anchor-1}[]{#anchor-2}Newborough Warren Methods Supplement

Hollingham (2026) --- Hydrogeological Dynamics, Behavioural Clustering and Management Intervention Analysis at Newborough Warren Coastal Sand Dune Aquifer, Wales.

This document accompanies report.pdf and Supplementary_Material.pdf. It is the per-script methodological record of the analytical pipeline.

Document version: 1.9.43 (August 2026).

## []{#anchor-2}[]{#anchor-3}[]{#anchor-4}Pipeline at a glance

*run_analysis.py*\*\* --- 50 registered steps across 17 phases\*\* (canonical count: committed *outputs/pipeline_manifest.json*, emitted on every run --- cite that, not this line, if the two ever disagree). Those 50 steps are classified two independent ways. By tier: 40 analytical, 4 display/utility (Scripts 26c, 09f, 09g, 27) and 6 diagnostic. By execution: 47 run in a default pass, and 3 --- Scripts 24b, 31 and 31b, the Phase 16 remainder --- run only with *\--with-supplementary*. The two classifications each account for the same 50 steps and are not additive with one another.

  ------- --------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------------
  Group   Scripts   Coverage                                                                                                                                                                                                    Supplement §
  1       1--4      Data preparation, clustering, SSM, cluster visualization                                                                                                                                                    §S.1--§S.4
  2       5--6      Pearson membership audit, extended network integration                                                                                                                                                      §S.4
  3       7--13     Spatial coefficients, LCSC benchmarking, scraping suite, clearfell suite, forecasting/spatial/P_flood thresholds                                                                                            §S.5--§S.7, §S.9
  4       14--18    Climate summary, climate projections, year-of-crossing, site-overview and experimental-design figures                                                                                                       §S.8
  5       19        Depth-dependent PET sensitivity                                                                                                                                                                             §S.10
  6       20        WTF cluster Specific Yield                                                                                                                                                                                  §S.12
  7       21        Water balance decomposition                                                                                                                                                                                 §S.11
  8       22        WTF spatial analysis and Sy mapping                                                                                                                                                                         §S.12
  9       23--24    Spatial groundwater analysis, spatial paper figures                                                                                                                                                         §S.13
  10      25        Forestry scenarios                                                                                                                                                                                          §S.14
  11      26        Coastal-retreat gradient                                                                                                                                                                                    §S.15
  12      27--29    Residual diagnostics (Scripts 22--24)                                                                                                                                                                       §S.16
  13      30--32    Van Willegen MSL, EWI, UKCP18 projections, report figures                                                                                                                                                   §S.18, §S.18b, §S.18c
  14      33--35    Cluster framework diagnostics (28, 29, 30) --- opt-in tier, *exec=\"default\"*                                                                                                                              §S.19
  15      36--41    Differential change, climate envelope, per-well amplification (32, 33, 35 --- analytical default); absolute climate-removed trend, driver validation, Part B comparative footing (36, 37, 37b --- opt-in)   §S.20
  16      42--46    Supplementary standalone diagnostics (24b, 31, 31b, 34, 38) --- all opt-in                                                                                                                                  §S.21
  17      47--49    Spatial-reach synthesis (09f); mechanism diagrams (09g); greyscale (27) ‡                                                                                                                                   §S.15c; §S.15d; App. A
  ------- --------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------------

‡ Display/utility steps. Also display/utility: Script 26c (step 32, Phase 13, §S.18c). Two post-review scripts inserted into earlier phases: Script 11c (step 13, Phase 3, §S.9.3) and Script 14b (step 16, Phase 4, §S.8.5). "Opt-in" steps (Scripts 24b, 31, 31b --- the Phase 16 remainder) run only with *run_analysis.py \--with-supplementary* or the interactive menu's option 1 prompt; they are tier-X diagnostics, outside the analytical tier, but they are registered pipeline steps (not ad hoc scripts) and do appear in the numbering above and in *pipeline_manifest.json*.

Sub-runners: *run_09_scraping.py* (Script 09 suite, §S.6), *run_10_clearfell.py* (Script 10 suite, §S.7).

# []{#anchor-4}[]{#anchor-5}[]{#anchor-6}F.1 Scope and audience

The main report's §3 *Methods* is calibrated to a journal-paper length: approximately 25 lines per method, with a single software-reference sentence pointing to the public repository at <https://github.com/newbroman/Newborough_Hydrology>. That length is appropriate for a paper. It is not enough for the audiences who will actually use this work.

This supplement is for those audiences. Four are anticipated. **Hydrogeological and ecohydrological researchers** rebuilding parts of the analysis on their own sites need the per-script methodological detail that the main report compresses. **Conservation managers at Newborough Warren NNR**, and at Natural Resources Wales more broadly, need to know what each result is and is not telling them --- particularly which findings are robust, which are conditional on a methodological choice that could reasonably have gone the other way, and which are honestly tentative. **Future site investigators** --- including, almost certainly, future PhD or MSc students at the warren --- need a starting point that does not require them to reconstruct the methodological reasoning from the code. And **the author**, three years on, needs to be able to defend any particular methodological choice without re-deriving why it was made.

The supplement covers all 50 registered pipeline steps (Phases 1--17) in script-by-script chapters. Four of those steps are display/utility rather than analytical: Script 26c (MSL5 report-format figures, step 32, §S.18c), Script 09f (spatial-reach synthesis, step 47, §S.15c), Script 09g (mechanism diagrams, step 48, §S.15d), and Script 27 (greyscale, step 49, Appendix A). Each chapter addresses seven concerns: motivation, inputs, methodology, site-specific choices and rationale, outputs, limitations and known caveats, and where the result appears in the report. Some chapters are short (figure-only or post-processing scripts); some are longer (Scripts 01, 02, 03, 10 suite, 17, 21, 25, 26). Total document length is approximately 260 pages.

This document is **not** a tutorial on Python or scientific computing. It is not a literature review --- references appear where they are required for methods provenance, not as a research review. It is not a redo of the main report's results; results appear only as concrete examples of what the methods produce. And it is not exhaustive code documentation --- the scripts in *src/* are the code documentation. This supplement is the methodological narrative.

The relationship between this document, the main report, and the existing supplementary material is:

-   *docs/report/report.pdf* --- the principal scientific deliverable. Canonical statement of what was found.
-   *docs/report/Supplementary_Material.pdf* --- quantitative supporting material referenced from the report (extended tables, additional figures).
-   *This document* --- methodological supplement. Canonical statement of how the work was done.

Cross-references work in both directions. The supplement points to the report wherever a result is discussed (*§4.2*, *Table 4c*, *Figure 11b*); the report's §3 *Methods* should be read in conjunction with the relevant chapters here when methodological detail is needed.

Where this supplement and the main report disagree, the main report is canonical for results and the supplement is canonical for methods. Where the supplement and the source code disagree, the source code is canonical --- the supplement describes how each script works, but the script itself is the implementation.

# []{#anchor-6}[]{#anchor-7}[]{#anchor-8}F.2 Field protocol, bucketing convention, and date semantics

The 88-well dipwell network is read monthly by the author. Readings are taken at the **end of each month** --- typically the last day of that month, or the first day or two of the following month. Each reading is the water level *for the month just ended*: a measurement taken on 1 May 2026 represents the **April 2026** water level.

Climate data from RAF Valley Meteorological Station (53°14′32″N, ≈16 km from the site) is a monthly total for the same calendar month. Rainfall (mm) and minimum and maximum temperatures (°C) are tabulated month-by-month from 1930 to present. Potential evapotranspiration is computed inside the pipeline (Script 00) using the Thornthwaite method at the RAF Valley latitude, returning a monthly PET total in millimetres.

### []{#anchor-8}[]{#anchor-9}[]{#anchor-10}Bucketing

Readings on physical dates ≤ day 15 of month *M* are bucketed into month *M*−1 because they belong to the previous month's water table. Readings on physical dates \> day 15 of month *M* are bucketed into month *M*. The cutoff is at day 15 because field readings are nearly always taken within the first week of the month or on the last day of the previous month; day 15 is comfortably in the middle of the gap and matches the field convention without ambiguity.

This bucketing is implemented in Script 01 (*01_data_prep.py*). Once bucketed, every monthly timestamp in the pipeline is the first of the month (*YYYY-MM-01*). **The ***-01*\*\* day component is a pandas formatting artefact and does not refer to the 1st of the month.\*\* A row labelled *2007-07-01* is "July 2007" --- it contains the end-of-July water level and July's climate data.

### []{#anchor-10}[]{#anchor-11}[]{#anchor-12}History: why HEADLINE_LAG was 1 and is now 0

Before April 2026, the bucketing in Script 01 used nearest-month assignment: a reading on 1 September was bucketed to September even though it represented August's water level. The pipeline compensated by applying a one-month lag to rainfall in the SSM, so that September's labelled water-table change was modelled against August's labelled rainfall --- the correct physical pairing despite the mislabelled month. This was the *HEADLINE_LAG = 1* regime.

The April 2026 bucketing fix corrected the convention to match the field protocol (day ≤ 15 → previous month). Once water-table readings are correctly labelled, the SSM should regress the August water-table change against the August rainfall, with no lag. *HEADLINE_LAG* was therefore changed to 0. All regression coefficients are numerically identical to the pre-fix lag-1 results, because the physical pairing is unchanged --- only the labelling differs. Hydrograph x-axis labels are now one month earlier than in pre-fix figures; all other numerical outputs are unaffected.

### []{#anchor-12}[]{#anchor-13}[]{#anchor-14}Note on maOD invariance to ground-surface change

The maOD (above-Ordnance-Datum) water-table elevation is a physical quantity independent of the ground surface above it. Removing material from the surface --- for example by intentional scraping for slack restoration, as at CEH18 and CEH21 in October 2023 --- does not move the water table; the maOD reading is the same before and after. Era-specific data handling is therefore only required where depth-below-ground is the quantity of interest, not where maOD water-table elevations are being averaged or compared. Script 11b (S.9) uses this principle: the DEM elevation at scraped wells is corrected by the scrape depth, but the full pre-and-post observed maOD record contributes to the water-table averaging.

### []{#anchor-14}[]{#anchor-15}[]{#anchor-16}Reporting dates in the report and supplement

Pipeline output CSVs retain the *YYYY-MM-01* index for pandas compatibility. The reader never sees these directly. In text --- both in the report and in this supplement --- monthly data is referred to by month and year only: "July 2007", "the winter 2017--18 peak", "the summer 2022 minima". On figure axes, *matplotlib.dates.DateFormatter(\'%Y\')* (for plots spanning several years) or *\'%b %Y\'* (for shorter ranges) is used in preference to *\'%Y-%m-%d\'*, so axis tick labels read as years or "Jul 2007" rather than as specific days. The *CHANGELOG_date_formatting_sweep.md* entry records the audit that brought all figure axes into compliance with this convention.

### []{#anchor-16}[]{#anchor-17}[]{#anchor-18}Hydrology year conventions

Most of the supplement reports time in calendar months and calendar years, as above. Two specific analytical contexts use *hydrology years* instead. The summer transfer functions in Script 11 Sections 2 and 4 (S.9) use an October-start hydrology year (1 October *y*−1 to 30 September *y*) --- the conventional choice for catchment-scale annual water balances. The van Willegen MSL aggregation in Script 26 (S.18), the Tool A spring MSL transfer function in Script 11 Section 5 (S.18b), and the Tool B UKCP18 MSL5 projection in Script 26b (S.18b) all use van Willegen 2025's **hydrology year B** (1 June *y*−1 to 31 May *y*). The June-start convention places the entire October-to-May antecedent forcing window --- winter peak, winter rainfall, spring rainfall, spring PET --- inside a single hydrology year alongside the spring response window it predicts. A reading dated 2010-04 therefore belongs to hydrology year 2010 under both conventions; a reading dated 2009-07 belongs to hydrology year 2010 under hydrology-year-B (because 1 June 2009 falls inside the year-2010 window) but to hydrology year 2009 under the October-start convention. The two conventions co-exist in the pipeline; chapters that use one or the other are explicit about which.

### []{#anchor-18}[]{#anchor-19}[]{#anchor-20}Concrete example

The row labelled *2007-07-01* for well CEH9 contains the following fields in the SSM design matrix (constructed by *model_utils.build_ssm_frame()*):

  ------------- ---------- ---------------------------------------------------------------------
  Term          Value      Meaning
  h(t)          −0.610 m   End-of-July reading (taken late July / early August)
  h(t−1)        −0.440 m   End-of-June reading
  Delta_h       −0.170 m   Water-table change *during* July
  P             0.1019 m   July rainfall total
  PET           0.0985 m   July PET total
  h_disp_prev   3.260 m    3.7 + (−0.440) --- displacement above drainage datum at end of June
  ------------- ---------- ---------------------------------------------------------------------

The SSM uses this row to explain July's 170 mm drop using July's rainfall, July's PET, and the water-table position at the *start* of July (= end of June).

# []{#anchor-20}[]{#anchor-21}[]{#anchor-22}F.3 The state-space model --- displacement formulation

The state-space model (SSM) is the methodological core of the analysis. Every cluster characterization, every BACI step, every forecasting threshold, every scenario response ultimately rests on it. This section gives the canonical form.

### []{#anchor-22}[]{#anchor-23}[]{#anchor-24}Equation

The fitted equation is

> Δh(t) = β₁·P(t) − β₂·PET(t) − β₃·(z₀ + h(t−1))

where:

-   **Δh(t)** is the change in water table during month *t* (m, signed; negative when the water table falls).
-   **P(t)** is the rainfall during month *t* (m). Note: under *HEADLINE_LAG = 0*, no lag is applied. In the pre-bucketing-fix regime this term was *P(t−1)*.
-   **PET(t)** is the Thornthwaite PET during month *t* (m).
-   **h(t−1)** is the water table at the *end* of month *t*−1 (m, signed; negative below ground surface).
-   **z₀** is the drainage datum, *DRAINAGE_DATUM = 3.7 m*. See *Drainage datum* below.
-   **β₁, β₂, β₃** are positive coefficients fitted by ordinary least squares (no intercept) using *utils.model_utils.fit_ssm()*.

The quantity *z₀ + h(t−1)* is the *displacement* of the water table above the drainage datum at the start of month *t*. With *z₀ = 3.7* and a typical end-of-previous-month head of −0.4 m, displacement is 3.3 m; with a deeper end-of-month head of −2.0 m, displacement is 1.7 m. The β₃ term says: the deeper the water table sits below ground at the start of a month, the smaller the drainage during that month --- Darcy-consistent.

### []{#anchor-24}[]{#anchor-25}[]{#anchor-26}Sign conventions

All three β values are reported as **positive** in the output CSV (*03_master_data.csv*, columns *beta_1_recharge*, *beta_2_atmospheric_draw*, *beta_3_drainage*). Sign conventions are baked into the OLS design matrix, not into the coefficient signs.

In the design matrix constructed by *build_ssm_frame()*:

-   The β₁ column is *+P*. A positive β₁ means rainfall raises the water table.
-   The β₂ column is *−PET*. A positive β₂ means PET lowers the water table (the negation in the column produces a negative contribution to Δh).
-   The β₃ column is *−(z₀ + h_prev)*. A positive β₃ means displacement above the datum drives drainage downward (Δh decreases as displacement increases).

Two of these signs are hard-asserted by *model_utils.assert_physical_signs()*: a fitted β₁ ≤ 0 or β₂ ≤ 0 halts the pipeline because either is physical nonsense. β₃ \> 0 is soft-asserted --- a negative β₃ is anomalous and worth investigating but does not halt the pipeline, because under unusual partitions or short data windows it could reflect a genuine statistical artefact rather than a physical impossibility.

### []{#anchor-26}[]{#anchor-27}[]{#anchor-28}Why *h(t−1)*, not *h(t)*

The drainage term uses the water-table position at the *end* of the previous month, not the contemporaneous level. Two reasons.

First, *h(t)* is the dependent variable (via Δh = h(t) − h(t−1)). Using it simultaneously as a predictor creates simultaneity bias --- the model would predict the change using the result of that change. The OLS would still fit, but the β₃ estimate would be biased and the interpretation broken.

Second --- and physically --- drainage *during* a month is driven by the head at the *start* of that month, not the head at the end. The end-of-month head is the result of drainage, not its cause. Using start-of-month head in the predictor row captures the physical dependence correctly.

**Why not the within-month mean?** The within-month mean ½\[h(t−1) + h(t)\] is, in principle, a more faithful approximation to the time-integrated drainage flux --- total monthly drainage is the integral of a head-dependent rate, so the trapezoidal form is nearer the exact integral than the forward (start-of-month) form. It is nonetheless not usable, for a fundamental reason: with a single end-of-month reading the within-month mean is unobserved and must be reconstructed as ½\[h(t−1) + h(t)\] = (z₀ + h(t−1)) + Δh/2. That reconstruction carries h(t) --- the dependent variable, via Δh = h(t) − h(t−1) --- back into the drainage predictor, reinstating exactly the simultaneity bias the h(t−1) form is chosen to avoid, and biasing β₃ (attenuation toward zero in general; spurious negative β₃ in the noise-dominated limit). The reconstruction adds no new information beyond the two endpoints; it merely relocates h(t) from response to predictor. The forward--trapezoidal discrepancy that is given up by retaining the start-of-month form is second-order: it scales with β₃·Δh (a few mm per month at the fitted coefficients) and, crucially, is an **exact reparameterisation** of β₃ rather than an estimation bias. On monthly data the two discretisations differ only by a global rescaling β₃_trap = β₃_fwd / (1 − β₃_fwd/2), which at the fitted β₃ values is a 1--5 % numerical relabelling of β₃ that leaves the model fit, residuals, and cluster contrasts entirely unchanged. The start-of-month form is therefore not a convenience approximation --- it is the only implementable choice given the observational protocol, and it costs nothing in model performance.

**Darcy interpretation guard.** β₃ is the monthly head-space recession constant --- the monthly drainage fraction per metre of displacement above the datum --- aggregating hydraulic conductivity K, saturated thickness b, specific yield Sy and flow-path geometry L (Boussinesq-linearised drainage). Its reciprocal t_R = 1/β₃ is the head-space e-folding timescale (S.12). The datum plays the role of the Darcy base head: β₃ and the datum are the slope and intercept of one flux--head line, so they are partially confounded. β₃ therefore **cannot** be decomposed into K and L independently, nor can the absolute base be located, from the SSM alone. The model accordingly must **not** be presented as a calibrated Darcian gradient model; it is a lumped linear-reservoir model with empirically determined recession constants. The surface-following convention for the datum (discussed below) is consistent with local drainage toward a base that tracks the dune topography rather than a regional sea-level gradient --- the test for this is in §S.3 (datum sensitivity) and the supporting evidence is that the per-well optimal datum depth varies modestly with ground elevation (slope +0.15 per metre of elevation, strongly surface-following) rather than tracking an absolute mAOD base.

The implementation in *model_utils.build_ssm_frame()* is

h_disp_prev = DRAINAGE_DATUM + h.shift(1)

which produces displacement above the datum *at the end of the previous month*. Every script that fits an SSM uses this function --- there is no script that reimplements the displacement calculation locally.

### []{#anchor-28}[]{#anchor-29}[]{#anchor-30}Drainage datum (3.7 m)

DRAINAGE_DATUM = 3.7 m is the depth below ground surface used as the displacement reference. The value was selected to give comfortable β₃ identification at the forest clusters (C4 and C5), where β₃ is hardest to pin down. At the live empirical minimum of 1.5 m --- the shallowest depth at which all five clusters simultaneously satisfy β₃ \> 0 with p \< 0.05 --- C4's β₃ p-value sits at the significance edge (0.044). At 3.7 m it drops to 0.0017, with C5 also gaining substantially (β₃ p-value from 1 × 10⁻¹⁰ to 2 × 10⁻¹⁶ and R² from 0.648 to 0.685). The trade-off is small R² penalties at C1 Lake Edge (−0.059) and C2 Dune (−0.032), where β₃ is over-determined and remains significant at p \< 10⁻²⁵ at either depth. 3.7 m also aligns with the Script 16 water-balance sensitivity analysis, which matters for keeping the displacement reference consistent across the pipeline. The full sensitivity sweep is in 03_state_space_model.py (outputs 03_08_datum_sensitivity.csv and .png, plus the datum-regime diagnostic 03_12_partition_vs_datum.csv and 03_12_datum_regime.png) and the trade-off is discussed at the per-cluster level in chapter S.3.

The role of the datum is to shift the reference for the drainage term. Without it (i.e. with *h(t−1)* instead of *(z₀ + h(t−1))* in the design column), the C3, C4, and C5 clusters produced negative β₃ under the head-below-ground convention. This was a sign-convention artefact, not a physical anomaly: it reflected that the OLS was correlating drainage with a quantity that crossed zero rather than staying on one side of a fixed reference. Setting the reference 3.7 m below ground places every observation comfortably on the positive side of the datum, restoring physical interpretability without changing the predictive content of the model.

***The datum convention is not inert.*** Because the headline SSM is fitted without an intercept, there is no free term to absorb a constant offset in a regressor. An offset cancels in the first-difference response Δh but not in the level term h_disp,prev, so it redistributes across β₁, β₂ and β₃ rather than being taken up by an intercept. This is measurable: when the residual per-well upstand subtraction was removed in Script 03 v1.3.0, the coefficient shifts scaled with each well\'s upstand across all 66 reference wells --- Pearson r = +0.789 for Δβ₁ (p = 3.7 × 10⁻¹⁵), −0.724 for Δβ₂ (p = 6.8 × 10⁻¹²) and −0.846 for Δβ₃ (p = 3.7 × 10⁻¹⁹) --- with β₃ shifting by 1.85 % at the median and 24.42 % at the maximum. DRAINAGE_DATUM and the ground-surface reference are therefore specification choices with quantitative consequences, not presentational conventions, which is why the frame is established once at source (S.1) and never re-derived downstream. The "Two regimes" discussion below is the complement: an intercept would absorb a constant datum shift, leaving β₃ unchanged --- which is precisely why the no-intercept specification cannot.

Δh is invariant under the choice of datum (the datum cancels in first differences), and β₁ is near-invariant across the sweep. β₂ and β₃ both shift with the datum --- the two loss terms trade against one another in carrying the loss budget --- in a way that preserves β₃'s physical interpretation as a Darcy drainage coefficient. The behaviour is a regime distinction rather than a defect: with the datum set within the water-table fluctuation range the drainage term reduces to mean-reversion of anomalies and attributes almost no steady flux to drainage, whereas at depths beyond the fluctuation range it represents Darcy outflow above a fixed base, the fitted drainage flux β₃·(z₀+h̄) plateaus, and the drainage/ET partition becomes insensitive to the exact choice. The canonical 3.7 m sits within this stable Darcy regime; the diagnostic is the two-panel datum-regime figure (03_12_datum_regime.png, Script 03 v1.5.0), presented in the report's Supplementary Material (Note S9).

Per-well optimal datums (where each well is fitted with whatever datum maximises its R²) show a coherent spatial gradient: C1 Lake Edge wells optimize at a median of \~0.8 m, C2 Dune at \~0.9 m, C3 Western Residual at \~1.7 m, C5 Coastal Forest at \~1.9 m, and C4 Main Forest at \~2.7 m. The pattern reflects deepening effective drainage base from the lake-adjacent eastern margin toward the forested western clusters. The uniform 3.7 m datum produces a network mean R² penalty of +0.028 across the network, heaviest at C1 Lake Edge (+0.069) and lightest at C4 Main Forest (+0.001) --- making the uniform datum a clean choice for cluster-level work, while a reader with a single-well question can read the per-well optimum off *03_09_well_optimal_datums.csv*. Per-well datum results are also discussed in §3.4 of the main report and at length in chapter S.3.

***Absolute versus surface-following base --- geometry test.*** The per-well sweep also indicates whether the drainage base is better represented as a fixed height above Ordnance Datum (a flat mAOD base) or as a uniform depth below the ground surface (a surface-following base that rides with the topography). The test is geometric: each well's R²-maximising datum, expressed as an elevation, is regressed on its ground elevation across the network's 10.9 m spread of ground elevations (3.53--14.42 mAOD). A flat base predicts a slope of 0 (optimal elevation independent of ground height; optimal depth tracking ground one-for-one); a surface-following base predicts a slope of +1 (optimal elevation tracking ground one-for-one; optimal depth flat). Across the 66 reference wells the datum-elevation slope is +0.868 and the mirror datum-depth slope +0.133, placing the effective base about seven-eighths of the way toward surface-following. A flat absolute base is in any case undefinable network-wide: the ground-elevation spread exceeds the active drainage-depth scale, so no single mAOD elevation keeps every well within the swept 0.5--8.0 m window. The uniform below-ground datum is therefore both the better-fitting and the physically appropriate convention: β₃ reads as a Darcy-consistent drainage coefficient --- drainage proportional to head above a base that follows the dune topography --- which is the interpretation the displacement datum is chosen to support, and the surface-following geometry is consistent with the theoretical flow paths and normalised Darcy vectors rendered from the mean-head surface (Script 20; main report §4.9.6, Figure 57). Because the datum and β₃ are identified jointly, as the intercept and slope of a single flux--head relation, the model constrains the lumped drainage coefficient together with its base rather than locating an absolute base or separating hydraulic conductivity from flow-path length; β₃ is Darcy-consistent in the lumped linear-reservoir sense. The weak residual depth-slope (+0.133) indicates the effective base is marginally flatter than purely surface-following, consistent with the westward-thickening substrate, but far from supporting an absolute datum. The two slopes are read directly from the committed per-well sweep: each well's R²-maximising datum in 03_09_well_optimal_datums.csv is taken both as a depth and, as ground elevation minus that depth, as an elevation, and each is regressed on the DGPS ground elevation in 01_well_elevations.csv (n = 66); no separate model is fitted.

### []{#anchor-30}[]{#anchor-31}[]{#anchor-32}Implementation: *model_utils.fit_ssm()*

The authoritative implementation is *src/utils/model_utils.py*. Every per-well, per-cluster, or per-network SSM fit in the pipeline goes through *fit_ssm()* (no-intercept, "Model A") or *fit_ssm_intercept()* (with-intercept, "Model B"). Scripts must not reimplement OLS locally.

The function signatures are

fit_ssm(h_series, climate, lag=None, window=None,

drainage_datum=DRAINAGE_DATUM, min_obs=MIN_OBS,

provenance=None, exclude_interpolated=False)

fit_ssm_intercept(h_series, climate, lag=None, window=None,

drainage_datum=DRAINAGE_DATUM, min_obs=MIN_OBS,

provenance=None, exclude_interpolated=False)

with defaults that produce the canonical SSM specification. The returned dict carries long-form keys (*beta_1_recharge*, *beta_2_atmospheric_draw*, *beta_3_drainage*), their p-values, R², n, and a residual series. The keys are intentionally verbose so that downstream code is self-documenting and cross-script searches (*grep beta_1_recharge*) return only genuine matches.

The *provenance=* and *exclude_interpolated=* kwargs control interpolated-row handling. Default behaviour: with *exclude_interpolated=False* (the default), interpolated rows from *01_wells_provenance.csv* remain in the SSM fit and the canonical β₁/β₂/β₃ coefficient table is preserved. Setting *exclude_interpolated=True* with a provenance series supplied restricts the fit to measured rows only, as a documented sensitivity path; the chapter that consumes this --- §S.3 --- describes when it would be invoked.

### []{#anchor-32}[]{#anchor-33}[]{#anchor-34}Two regimes: no-intercept (A) and with-intercept (B)

The headline SSM is Model A --- no intercept. The justification: the SSM is a physically motivated decomposition of Δh into rainfall, PET, and drainage contributions, and there is no remaining physical mechanism for a constant bias. A non-zero intercept under Model A would indicate that one or more β coefficients is absorbing a constant lateral inflow/outflow that the model does not explicitly represent.

Model B (with intercept α) is fitted in Scripts 22 and 24 as a diagnostic. A statistically significant α at a particular well flags that well as poorly described by the headline SSM --- typically because lateral subsidies (ridge-derived recharge, lake exchange) or local hydraulic effects matter at that location. Script 08 does not fit Model B. Its benchmark sets the headline Model A against a traditional linear model that carries its own constant term, so what it compares is the physical decomposition against a more flexible but unphysical alternative, not Model A against Model B.

### []{#anchor-34}[]{#anchor-35}[]{#anchor-36}Sanity-check assertions

*assert_physical_signs()* is called at every cluster fit in Script 03. It returns a *(hard_violations, soft_warnings)* tuple. Hard violations halt the pipeline after the relevant diagnostic outputs (LOO, bootstrap, datum sensitivity) have been written, so the investigator has the supporting tables to diagnose the failure rather than just a stack trace. Soft warnings (β₃ ≤ 0) are printed and recorded; they do not halt.

The principle is that the pipeline should fail loudly when its physical assumptions are violated. A negative β₁ is not a "degraded fit" --- it is physical nonsense that should never silently propagate into a report number.

# []{#anchor-36}[]{#anchor-37}[]{#anchor-38}F.4 Configuration, constants, and the cluster partition

All values that are constant across the pipeline live in *src/utils/config.py*. Where a scientific decision determines a value --- the canonical 24% canopy interception fraction, the 3.7 m drainage datum, the Curreli ecohydrological thresholds, the UKCP18 climate scaling factors --- that decision is recorded against the constant. Scripts must not redefine these values locally; the principle is that there is one place to change a value, and the change propagates everywhere.

### []{#anchor-38}[]{#anchor-39}[]{#anchor-40}What is in *config.py*

The principal entries:

  ------------------------------------------ ------------------------------------------------------------------------------------------------------------------------------ -----------------------------------------------------------------
  Constant                                   Value                                                                                                                          Notes
  CLUSTER_LABELS                             {1: \"C1 (Lake Edge)\", 2: \"C2 (Dune)\", 3: \"C3 (Western Residual)\", 4: \"C4 (Main Forest)\", 5: \"C5 (Coastal Forest)\"}   k=5 partition, this study
  CLUSTER_COLOURS                            {1: \"#1a6faf\", 2: \"#2ca02c\", 3: \"#d62728\", 4: \"#7f77dd\", 5: \"#8B4513\", 6: \"#0072B2\"}                               Canonical palette; ID 6 reserved
  CLUSTER_COLOURS_BW                         greyscale equivalents at ≈40-unit luminance spacing                                                                            Journal print mode (*BW_MODE*)
  CLUSTER_MARKERS                            {1: \'o\', 2: \'s\', 3: \'\^\', 4: \'D\', 5: \'P\'}                                                                            Cluster-shape symbols on spatial maps
  DRAINAGE_DATUM                             3.7 m                                                                                                                          Sensitivity analysis, Script 03 (*03_08*)
  HEADLINE_LAG                               0                                                                                                                              Post-bucketing-fix value (was 1 historically)
  FOREST_INTERCEPTION                        0.24                                                                                                                           Freeman (2008), Newborough Corsican pine
  FOREST_CIDS                                (4, 5)                                                                                                                         k=5 partition mapping
  BROADLEAF_INTERCEPTION                     0.15                                                                                                                           Komatsu et al. (2011) annual mean
  BROADLEAF_B2_SUMMER                        1.0750                                                                                                                         Script 21 monthly β₂ profile, May--Oct mean (canopy-on window)
  BROADLEAF_B2_WINTER                        0.8817                                                                                                                         Script 21 monthly β₂ profile, Nov--Apr mean (canopy-off window)
  REFERENCE_CUTOFF_DATE                      "2026-02-01"                                                                                                                   Reference-network selection in Script 01
  RAF_VALLEY_LAT_DEG                         53.25                                                                                                                          53°14′32″N, used for Thornthwaite PET
  *SD15b*, *SD15b_REC*, *SD16*, *SD16_REC*   0.61, 0.75, 0.98, 1.20 m                                                                                                       Curreli et al. (2013) summer slack thresholds
  *SD15b_WINTER*, *SD16_WINTER*              0.10, 0.25 m                                                                                                                   Curreli winter flooding limits
  *UKCP18_DRY\_\**, *UKCP18_WET\_\**         seasonal P and PET scaling factors                                                                                             UKCP18 RCP8.5 Wales, 50th percentile, 2050s
  *DEM_VMIN*, *DEM_VCENTER*, *DEM_VMAX*      0.0, 12.0, 35.0 m AOD                                                                                                          TwoSlopeNorm anchors for DEM rendering
  ------------------------------------------ ------------------------------------------------------------------------------------------------------------------------------ -----------------------------------------------------------------

The B&W rendering mode (*BW_MODE*) is toggled by the *NRG_BW_MODE* environment variable, which *run_analysis.py* sets when invoked with *\--greyscale-full*. When active, scripts switch to the *CLUSTER_COLOURS_BW* palette, apply *BW_HATCHES* to bar charts, use *BW_LINESTYLES* for multi-series line plots, and call the hillshade DEM loader for map backgrounds. The convenience functions *get_cluster_colour()*, *get_bar_hatch()*, *get_line_style()*, *get_line_colour()*, and *get_cmap()* provide colour-mode and B&W-mode behaviour in a single call, so a script does not need to branch on *BW_MODE* itself.

### []{#anchor-40}[]{#anchor-41}[]{#anchor-42}The k=5 partition

The reference network is partitioned into five behavioural clusters using Ward's linkage on correlation distance between cluster-mean hydrographs (Script 02). The cluster IDs and labels are:

  ---- --------------------- -------------- ---------------- --------------------------------
  \#   Cluster               Anchor wells   Block            Character
  1    C1 Lake Edge          ceh5, ceh11    Eastern Block    Lake-adjacent, finer sediments
  2    C2 Dune               d10            Eastern Block    Mature open dune, shallow till
  3    C3 Western Residual   nw1            Western Block    Deep aeolian sand
  4    C4 Main Forest        ceh2           Forest           Corsican pine on deep sand
  5    C5 Coastal Forest     ceh16, nw9     Coastal Forest   Corsican pine, coastal margin
  ---- --------------------- -------------- ---------------- --------------------------------

*02_clustering.py* carries a *CLUSTER_ID_ANCHORS* dict that pins Ward's raw (arbitrary) output to these canonical IDs. A guard at module load asserts that *CLUSTER_ID_ANCHORS* and *CLUSTER_LABELS* agree. Membership counts (live, May 2026 partition under *01_data_prep.py* v1.3.0 which blacklists the tidal *pdfs* well) are C1 = 7, C2 = 24, C3 = 21, C4 = 9, C5 = 5; total 66 wells in the reference network.

### []{#anchor-42}[]{#anchor-43}[]{#anchor-44}Partition history

The k=5 partition supersedes an earlier k=6 partition that included a separate "Lake" cluster for Llyn Rhos-Ddu. Under k=5, Llyn Rhos-Ddu is treated as a fixed-head boundary feature rather than a cluster --- it is the dominant local drainage sink for C1 Lake Edge wells but is not itself a behavioural cluster. The old C5 (Coastal, n=1, single tidally-influenced well) and old C6 (Lake, n=1) were dropped at the partition step as physically unreliable singletons. Their names re-appear under k=5 with different membership --- old C5 ≠ new C5.

References to "C6 Lake" or "tidal exclusion" framing of C5 elsewhere in the project file store are from the superseded k=6 partition and should be ignored.

### []{#anchor-44}[]{#anchor-45}[]{#anchor-46}The identity-vs-integer keying principle

This principle warrants its own section here, because future partition changes are not impossible (a sixth cluster could be identified, or the C5 Coastal Forest subset could be reabsorbed into C3 if the coastal-retreat signal proves to be exogenous), and the principle determines how downstream code survives.

Things keyed on **cluster identity** --- labels, colours, markers, anchor wells, well-to-cluster membership tables --- survive a partition change cleanly. When clusters are re-numbered, these values stay attached to the same physical cluster and are reassigned to the new ID automatically.

Things keyed on **cluster integer** --- Python dicts mapping *1*, *2*, ... to physical quantities like specific yield, peak month, trend value, flood frequency, residual SE --- are physical inputs to downstream arithmetic. When the partition changes, the dict key is just an integer; it does not follow a cluster around. **Each entry must be checked individually**: does the value still apply to whatever physical cluster has that integer ID under the new partition?

The convention going forward: if a dict is keyed by integer cluster ID and holds anything other than labels, colours, or markers, treat it as physical data tied to a specific cluster. When the partition changes, walk through every such dict and verify each entry; do not assume.

Several dicts in the codebase are physical-data-keyed-by-integer and need verification under any future partition change: *SUMMER_TRENDS* and *FLOOD_FREQ* in Script 16, *RESIDUAL_PCT_SE* in the water-balance work, and *CLUSTER_PEAK_MONTH* in Script 11. These dicts are now read dynamically from upstream pipeline CSVs where possible (*03_cluster_peak_months.csv* for the peak months, *16_water_bal_table.csv* for residuals), but any remaining hardcoded entries should be revisited if the partition changes.

### []{#anchor-46}[]{#anchor-47}[]{#anchor-48}Specific yield: two values per cluster

Two per-cluster specific-yield references are cited in the report: literature values for unconfined dune sand (Fetter, 2001) and empirical estimates from the water-table-fluctuation (WTF) method (Scripts 17 and 18). The water-balance partition (Script 16) uses neither --- it is Sy-free (§S.11) --- so the two references serve as substrate-storage context and as a literature-versus-empirical comparison, not as inputs to the balance. For reference here:

  --------------------- ------------ ------------------ ---------------------------
  Cluster               Sy assumed   Approach A (OLS)   Approach B (event median)
  C1 Lake Edge          0.08         0.341              0.210
  C2 Dune               0.12         0.335              0.281
  C3 Western Residual   0.12         0.351              0.328
  C4 Main Forest        0.12         0.302              0.259 (corr)
  C5 Coastal Forest     0.12         0.419              0.321 (corr)
  --------------------- ------------ ------------------ ---------------------------

The Fetter values are literature specific yields for unconfined dune sand, cited as a comparison benchmark; they do not enter Script 16\'s water-balance partition, which is Sy-free (§S.11). The WTF values are the empirical estimates from rising-limb event analysis (Script 17, Table 4c). They are not in conflict; they are independent references --- one from the literature, one empirical --- and the report cites both. The Phase 6 chapter explains why the corrected and uncorrected C4 medians both appear in Table 4c, and the Phase 8 chapter explains why the well-level cluster mean (0.202 for C4) is lower than the cluster-aggregate value (0.227).

### []{#anchor-48}[]{#anchor-49}[]{#anchor-50}Scripts in the post-Phase-2 region --- naming and step assignment

The scripts in the post-Phase-2 region of the pipeline carry filename prefixes, orchestrator step numbers, and chapter assignments aligned as follows:

-   **Script 11c** (*11c_pflood_achievability.py*) --- Per-well P_flood achievability categorical priority map. Operationalises Conclusion 4's λ \< 1.5 priority criterion. Step 13/50, Phase 3. Routed from the 2026-05-29 post-review cascade. Documented in S.9.3.
-   **Script 14b** (*14b_year_of_crossing.py*) --- Bootstrap year-of-crossing for Curreli (2013) ecological thresholds. Step 16/50, Phase 4. Routed from the 2026-05-29 post-review cascade. Documented in S.8.5.
-   **Script 25** (*25_coastal_gradient.py*) --- Coastal-retreat gradient analysis. Step 26/50, Phase 11. Documented in S.15.
-   **Script 26** (*26_van_willegen_msl.py*) --- Van Willegen 2025 observational 5-year MSL aggregation, plus (v1.3.2) the equilibrium wetness index and its Ellenberg-F cross-validation. Step 30/50, Phase 13. Documented in S.18.
-   **Script 26b** (*26b_van_willegen_msl_projections.py*) --- UKCP18 RCP8.5 MSL5 climate projections (Tool B). Step 31/50, Phase 13. Documented in S.18b.
-   **Script 26c** (*26c_msl5_report_figures.py*) --- MSL5 report-format figures for §4.8.5 and §4.10.1 of the main report. Display-only companion to Scripts 26 and 26b; reads only canonical outputs from Scripts 26, 26b, and 19; no recomputation. Step 32/50, Phase 13. Display/utility tier, not analytical. Documented in S.18c.
-   **Script 28** (*28_c3_detrend_check.py*) --- C3 detrend check; quantitative validation of the aquifer-architecture framing. Step 33/50, Phase 14. Routed from the 2026-05-29 post-review cascade. Documented in S.19.1.
-   **Script 29** (*29_c3_within_variance_check.py*) --- Within-C3 variance attribution. Step 34/50, Phase 14. Routed from the 2026-05-29 post-review cascade. Documented in S.19.2.
-   **Script 30** (*30_c4_drainage_identifiability.py*) --- C4 drainage identifiability diagnostic and reported sensitivities. Step 35/50, Phase 14. Added 2026-06-23 as a constrained-β₃ triangulation sensitivity; superseded by the identifiability diagnostic 2026-07-24. Documented in S.19.3.
-   **Script 32** (*32_differential_movement.py*) --- Secular differential water-table movement; report Figure 63. Step 36/50, Phase 15. Documented in S.20.1.
-   **Script 33** (*33_envelope_amplification.py*) --- Climate-swing amplification and dry-year spring floor; report Figures 65 and 66. Step 37/50, Phase 15. Documented in S.20.2.
-   **Script 35** (*35_per_well_amplification.py*) --- Per-well climate-sensitivity coefficient (discrete companion to the Figure 65 surface). Step 38/50, Phase 15. Documented in S.20.3.
-   **Script 36** (*36_absolute_climate_trend.py*) --- Absolute climate-removed per-well secular trend map. Step 39/50, Phase 15. **Analytical tier** (promoted 2026-07-13, Task E). Documented in S.20.4.
-   **Script 37** (*37_driver_validation.py*) --- Predicted-vs-observed driver-change validation (scatter + residual map). Step 40/50, Phase 15. **Analytical tier** (promoted 2026-07-13, Task E). Documented in S.20.5.
-   **Script 37b** (*37b_driver_footing.py*) --- Part B: comparative driver footing --- forest, scrape, and coastal-retreat effects on common currencies (peak local head change, area-integrated volume, ecological-threshold crossings). Step 41/50, Phase 15. **Analytical tier** (promoted 2026-07-13, Task E). Documented in S.20.6.
-   **Script 24b** (*24b_residual_climatology.py*) --- Cluster-stratified residual climatology; supplementary diagnostic. Step 42/50, Phase 16. **Opt-in diagnostic tier.** Documented in S.21.1.
-   **Script 31** (*31_cluster_validation.py*) --- Independent k=5 partition validation; supplementary diagnostic. Step 43/50, Phase 16. **Opt-in diagnostic tier.** Documented in S.21.2.
-   **Script 31b** (*31b_separation_vs_recoverability.py*) --- Cluster separation versus recoverability; supplementary diagnostic. Step 44/50, Phase 16. **Opt-in diagnostic tier.** Documented in S.21.3.
-   **Script 34** (*34_window_sensitivity.py*) --- MSL5 two-window sensitivity demonstration. Step 45/50, Phase 16. **Analytical tier** (promoted 2026-07-13, Task E). Documented in S.21.4.
-   **Script 38** (*38_coastal_transect.py*) --- Coast-to-inland MAM transect; observational delta_0 (coastal-retreat) diagnostic distinguishing a growing (erosion-consistent) from a static (substrate-geometry) coast-inland head gradient. Step 46/50, Phase 16. **Analytical tier** (promoted 2026-07-13, Task E; wired into *run_analysis.py* 2026-07-08, previously standalone). Documented in S.21.5.
-   **Script 09f** (*09f_management_effects.py*) --- Management-interventions-versus-coastal-retreat spatial-reach synthesis figure. Step 47/50, Phase 17. Display/utility tier, not analytical. Documented in §S.15c.
-   **Script 09g** (*09g_mechanism_diagrams.py*) --- Mechanism-diagram suite: the §5.8 combined schematic grid and the standalone coastal-vs-climate reach figure. Step 48/50, Phase 17. Display/utility tier, not analytical. Reads only committed outputs of Scripts 09f, 10m and 10a; no recomputation. Documented in §S.15d.
-   **Script 27** (*27_greyscale_figures.py*) --- Post-pipeline greyscale figure-rendering utility. Step 49/50, Phase 17. Display/utility tier, not analytical. Documented in Appendix A.

### []{#anchor-50}[]{#anchor-51}[]{#anchor-52}MSL aggregation --- constants and conventions

A new family of constants in *utils/config.py* parameterises the van Willegen 5-year mean spring water level (MSL5) aggregation introduced at Script 26 and consumed by Tools A and B in S.18b. These constants are stable across the pipeline (changing them would re-define the metric) and are documented here as the canonical source.

-   *MSL_SPRING_MONTHS = (3, 4, 5)* --- March, April, May; the spring window from van Willegen 2025 Table 2.
-   *MSL_HYDRO_YEAR_START_MONTH = 6* --- June; the start of van Willegen's hydrology year B (1 Jun *y*−1 to 31 May *y*). See F.2 for the two-hydrology-year-convention discussion.
-   *MSL_DEFAULT_WINDOW_YEARS = 5* --- the 5-year averaging window length; van Willegen et al. (2025) sensitivity-tested this choice and found cross-correlation stabilises at 5 years.
-   *MSL_MIN_MONTHS_PER_SPRING = 3* --- strict 3 of 3 completeness rule for a single annual MSL to be valid.
-   *MSL_MIN_YEARS_IN_WINDOW = 5* --- strict 5 of 5 completeness rule for a 5-year MSL window to be valid. Stricter than van Willegen 2025; consistent with the BACI summer-minima *min_measured=2* pattern in Scripts 09c and 10d.
-   *MSL_TRAJECTORY_START_YEAR = 2014* --- earliest window-end included in the cluster trajectory and per-quadrat-well figures, set to exclude windows that draw on the pre-2010 network of fewer than 35 wells. Per-well CSVs retain the full record from window-end 2009 onwards.
-   *VW_QUADRAT_WELLS* --- tuple of 17 lowercase piezometer IDs with co-located permanent vegetation quadrats from van Willegen 2025 Table 1: *ceh1, ceh4, ceh5, ceh8, ceh9, ceh22, ceh23, ceh24, ceh26, nw2, nw3, nw4, nw5, nw6, nw7, t41, wmc2*. Sixteen of these pass the strict completeness rules; T41 fails because of insufficient recent record.

A pair of intervention-line-colour constants for the trajectory figures also lives in *utils/config.py*:

-   *INTERVENTION_COLOUR_SCRAPE = \"#7b3294\"* --- purple; used for the April 2015 CEH36 scrape and the October 2023 CEH18/CEH21 re-scrape.
-   *INTERVENTION_COLOUR_CLEARFELL = \"#e66101\"* --- orange; used for the December 2017 pine clearfell.

UKCP18 multipliers used by Tool B are central-estimate Wales 50th-percentile values for RCP8.5 at the 2050s and 2080s. Both epochs live in *utils/config.py* as *UKCP18_SCENARIOS*, imported by Script 19's scenario viewer and by Script 26b. Until 2026-08-18 the two scripts each held their own copy of the same four multipliers per epoch; the follow-up previously noted here and in §S.18b.7 has been carried out.

The multipliers scale the observed P and PET series; neither is recomputed from projected temperature, so the projections inherit the observed record's seasonal structure. One assumption follows and is worth stating. The UKCP18 PET changes are derived on a physically-based footing, whereas the baseline they scale is Thornthwaite, and the two do not respond proportionally to warming: Thornthwaite carries its heat index in the denominator and so damps its own response, measured at an elasticity of 0.42 over the RAF Valley record (00_05_pet_warming_response.csv). Applying a physically-based fractional change to a Thornthwaite baseline is therefore a deliberate choice, and a conservative one --- the scenario imposes more evaporative demand than Thornthwaite would generate from the same warming.

### []{#anchor-52}[]{#anchor-53}[]{#anchor-54}*pipeline_params.py* --- the consolidated scenario parameter file

A subset of *config.py* constants is supplemented at run time by values that are computed by the pipeline itself and consumed by downstream scenario scripts. These live in a per-run CSV at *outputs/01_data_prep/pipeline_scenario_params.csv*, managed by *utils/pipeline_params.py*.

The architecture is producer-consumer with explicit provenance:

-   **Script 01** writes the initial file at the end of data preparation, populating summer climate means, head displacements, and forest flags directly; defaulting β₁, β₂, β₃, Sy, and the clearfell/thinning β₂ multipliers if upstream outputs don't exist yet.
-   **Script 03** updates β₁, β₂, β₃ once it has fitted them.
-   **Script 10e** updates the clearfell and thinning β₂ multipliers from the BACI-corrected Edge-tier ratio.
-   **Script 17** updates Sy from the WTF cluster medians.
-   **Downstream consumers** (Scripts 09b, 09d, 19, 21) call *load_params()* to read the consolidated file in one go.

Each value carries a *source\_\** column flagging whether it is from *\"pipeline\"* (a script has updated it) or *\"defaults\"* (it is still a placeholder from the initial write). Where any consumer reads a placeholder, a warning is printed recommending a second pipeline run. The two-pass workflow described in *PIPELINE_README.md* exists for this reason: the scenario figures use Sy and β₂ multipliers that are computed later in the pipeline, so the first pass uses fallbacks and the second pass uses canonical values.

# []{#anchor-54}[]{#anchor-55}[]{#anchor-56}F.5 Shared utility modules

Eight modules in *src/utils/* carry the shared functionality that the analytical scripts depend on. The module inventory:

### []{#anchor-56}[]{#anchor-57}[]{#anchor-58}config.py

Constants and palette. F.4 covers its contents in full.

### []{#anchor-58}[]{#anchor-59}[]{#anchor-60}paths.py

Single source of truth for every input and output file path. The module is organized into four blocks:

1.  **Root directories** --- *ROOT_DIR*, *DATA_DIR*, *OUT_DIR*, and per-script subdirectories *DIR_00* through *DIR_27*, plus *DIR_26B* for Script 26b's outputs. A helper function *make_all_dirs()* creates any missing directories. Scripts call this at the top of their main function rather than checking individual directories.
2.  **Data inputs** --- paths to raw CSV and GIS files in *data/*: *DATA_WELLS_RAW* (the cleaned monthly dipwell CSV), *DATA_LOCATIONS_RAW*, *DATA_CLIMATE_RAW*, the KML files (*Features.kml*, *streams.kml*, *clearfell.kml*, *broadleaf_restock.kml*), the DEM (*newborough_dem.tif*), and the precomputed coastal-distance CSV (*DATA_DIST_COAST*).
3.  **Intermediate files** --- outputs written to *OUT_DIR* root by upstream scripts and read by downstream scripts. These are named with the *INT\_* prefix: *INT_WELLS_CLEAN*, *INT_CLIMATE*, *INT_LOCATIONS*, *INT_MASTER_DATA*, *INT_REGIONAL_AVG*, *INT_CLUSTER_AVG_MAOD*, *INT_CLUSTER_PEAK_MONTHS*, and so on.
4.  **Final outputs** --- figures, tables, and report CSVs written to per-script subdirectories. These are named with the *OUT_NN\_* prefix to indicate which script writes them: *OUT_03_MECHANISTIC_TABLE*, *OUT_10E_COEFF_SHIFTS*, *OUT_25_FIT_PARAMETERS*, and so on.

The naming convention is rigid: every path constant has a single owner (the script that writes it) and many readers. A grep for *OUT_03_MECHANISTIC_TABLE* finds the writer (Script 03) and every reader (Scripts 07, 11, 16, 19, 21). No script reads or writes a hardcoded path; every path goes through *utils.paths*.

### []{#anchor-60}[]{#anchor-61}[]{#anchor-62}model_utils.py

The SSM specification. F.3 covers *build_ssm_frame()* and *fit_ssm()*; the full function inventory:

-   *build_ssm_frame(h_series, climate, lag, window, drainage_datum)* --- align well and climate data, compute the SSM predictor columns (*h*, *h_prev*, *Delta_h*, *P*, *PET*, *h_disp_prev*), drop NaN, apply optional windowing. The data-alignment helper every script was previously duplicating.
-   *fit_ssm(\...)* --- no-intercept OLS (Model A / headline SSM). Returns a dict with *beta_1_recharge*, *beta_2_atmospheric_draw*, *beta_3_drainage*, their p-values, R², n, and the residual series.
-   *fit_ssm_intercept(\...)* --- with-intercept OLS (Model B), returning the same dict plus α and its p-value. Used by Scripts 22 and 24.
-   *simulate_ssm(h0, P, PET, b1, b2, b3, drainage_datum)* --- iterative forward simulation using the displacement recurrence *h(t) = (1−β₃)·h(t−1) + β₁·P(t) − β₂·PET(t) − β₃·D*. Used by Scripts 08, 09, 15.
-   *pflood_lambda(h_target, h_0, b1, b2, b3, months, P_clim, PET_clim, drainage_datum)* --- iterated closed-form P_flood threshold with the datum drain correction. Solves for the rainfall multiplier λ that brings h from h_0 to h_target over a specified horizon. Returns λ, P_flood in mm, the collapsed linear-form slope and intercept (so P_flood = A·d + B), and the weighted sums. Used by Scripts 11 and 11b.
-   *monthly_perturbation(b1, b2_base, b2_scen_arr, P_eff_base, P_eff_scen, monthly_PET)* --- single-step forcing-change response. Computes Δh(m) = β₁·(P_scen(m) − P_base(m)) − (β₂_scen(m) − β₂_base)·PET(m). Used by Script 21 for forestry scenarios; replaced an earlier equilibrium formulation (*Δh / β₃*) that produced physically implausible magnitudes.
-   *assert_physical_signs(fit, context)* --- sign-rule enforcement. Returns hard violations (β₁ ≤ 0, β₂ ≤ 0) and soft warnings (β₃ ≤ 0).
-   *get_metrics(obs, sim)*, *get_r2(obs, sim)* --- NSE/RMSE/bias and Pearson R² helpers.

A former *compute_intercept_audit()* helper, a Model A versus Model B comparison for a single well, was removed at *model_utils* v1.4.0: it had no caller anywhere in the pipeline.

Two named thresholds: *MIN_OBS = 30* (minimum aligned rows for a per-well fit, applied inside *fit_ssm* and *fit_ssm_intercept*) and *LCSC_DATA_LIMIT = 100* (the equal-length per-well fitting window). Both are declared in *utils/config.py* --- as *SSM_MIN_OBS* and *LCSC_DATA_LIMIT* --- and re-exported under the names above by *model_utils*, so each value is declared once and every consumer imports it: Scripts 03, 08 and 30 for the window, and the *model_utils* fitters themselves for the minimum.

### []{#anchor-62}[]{#anchor-63}[]{#anchor-64}data_utils.py

Three short helpers shared across scripts:

-   *normalize_well_name(value)* --- lowercase, strip, remove spaces. Used wherever well names are joined between data sources.
-   *parse_met_date(date_str)* --- parse Met Office "Mon YY" strings (e.g. "Jan 95", "Dec 26") with the 2000-cutover handled internally.
-   *clean_well_series(series, max_depth=4.0)* --- drop unphysical depth values (\> 4.0 m below ground) to NaN, then linearly interpolate single missed-visit gaps only (*limit=1*). The 4 m maximum is the *MAX_PHYSICAL_DEPTH* constant --- set at the deepest plausible water table for the warren given site geometry and historical records.
-   *calculate_cusum(series, baseline_mean)* --- cumulative sum of departures from a baseline mean. The CUSUM diagnostic used by Scripts 09 and 10.

### []{#anchor-64}[]{#anchor-65}[]{#anchor-66}clearfell_common.py

Shared module for the Script 10 clearfell BACI suite (10a--10m). Provides:

-   **Well tier definitions.** *IMPACT_WELLS = \[\'wmc3\'\]* (the sole impact well spanning all three eras: pre-scraping, post-scraping, post-felling). *EDGE_WELLS = \[\'ceh31\', \'ceh20\', \'ceh30\', \'ceh16\'\]* (compartment edge). *FOREST_CONTROL_WELLS = \[\'ceh32\', \'ceh34\', \'ceh33\', \'nw10\', \'ceh2\'\]* (C4 interior, unaffected by felling). *COASTAL_CONTROL_WELLS = \[\'ceh19\', \'ceh17\'\]* (C5 interior, distinct β₂ regime). *CLIMATE_CONTROL_WELLS = \[\'ceh9\', \'nw7\', \'nw6\', \'nw5\', \'wmc2\'\]* (C3, climate-only counterfactual). *C3_WARREN_WELLS = \[\'ceh1\', \'nw1\', \'nw2\', \'nw11\'\]* (the balanced four-well shielded western-dune set used as the second control zone by the four-zone sub-scripts 10k and 10l). The TIERS dict groups the five clearfell tiers into the BACI network used by 10a.
-   **Intervention dates.** *INTERVENTION_DATE = 2017-12-01* (clearfell); *SCRAPING_DATE = 2015-04-01*; *SCRAPING_DATE_2 = 2023-10-01*.
-   **Spatial constants and distance functions** for scraping-propagation modelling (the λ = 300 m exponential weight).
-   **Data loaders.** *load_clearfell_data()* reads wells, climate, and master coefficients in one call.
-   **BACI helpers.** *compute_baci_displacement()*, *compute_cwb()* (climate water balance), *distance_weighted_scraping()*, *annual_summer_minimum()*.
-   *load_clearfell_b2_multiplier()* --- the BACI-corrected Edge-tier β₂ ratio, computed dynamically from *10e_01_coefficient_shifts.csv* rather than hardcoded. The thinning multiplier is derived as half-perturbation. Used by Scripts 19 and 21 to ensure their forestry scenarios use the canonical BACI-derived values rather than stale hardcoded constants.

The suite-shared module makes it possible to change the impact-well list, the BACI dates, or the distance-weight function in one place, and have all thirteen sub-scripts pick up the change consistently.

### []{#anchor-66}[]{#anchor-67}[]{#anchor-68}scraping_common.py

Analogous shared module for the Script 09 scraping suite (09a--09e). Provides:

-   **Intervention dates** (shared with clearfell where overlapping).
-   **Well groups for BACI** (*IMPACT_WELLS*, *PAIRED_CONTROLS_MAP*, *CLIMATE_CONTROLS*, *DONOR_CANDIDATES*).
-   **Tier assignments** (TIER1 controls vs TIER2 impacts).
-   **Era definitions** --- *WELL_ERAS* dict keyed by well, with *(start, end)* tuples per era. Different wells have different era boundaries: CEH36's eras are 1_Baseline / 2_Pure_Scraping / 3_Felling_Pulse around the 2015 and 2017 events; CEH21's eras are 1_Baseline / 2_Coastal_Drawdown / 3_After_Scraping around the 2017 felling and the 2023 second-scraping event. This structure allows each sub-script to apply consistent era windows without duplicating definitions.
-   **Plot style constants** --- *ERA_COLORS*, *ERA_MARKERS*, *ERA_LINESTYLES*, and *MPL_DEFAULTS*.
-   **Data loaders.** *load_scraping_data()* returns wells (reference + extended) and climate.
-   **Cluster-parameter loader.** *load_cluster_params()* consolidates β coefficients (from Script 03), Sy (from Script 17), and head displacement (from Script 01) into a single per-cluster dict.
-   **Scenario computation.** *compute_scenario_bars(cluster_params, summer_P, summer_PET, \...)* produces the per-cluster volumetric scenario bars (mm/month) for clearfell, thinning, broadleaf, climate-dry, and climate-wet scenarios using the Option 3 monthly perturbation formulation. This is the single source of truth for scenario values; Scripts 09d, 19, and 21 all call it.

### []{#anchor-68}[]{#anchor-69}[]{#anchor-70}pipeline_params.py

Consolidated scenario parameter file management. F.4 describes the architecture. The function inventory:

-   *write_initial_params(wells_clean, climate)* --- called by Script 01. Writes summer climate means, head displacements, forest flags directly; reads from existing upstream outputs (Scripts 03, 10e, 17) opportunistically, defaulting where they don't exist.
-   *update_betas(beta_by_cluster)* --- called by Script 03 after fitting.
-   *update_b2_multipliers(clearfell_mult, thinning_mult)* --- called by Script 10e.
-   *update_specific_yield(sy_by_cluster)* --- called by Script 17.
-   *update_h_disp(h_disp_by_cluster)*, *update_peak_months(peak_by_cluster)* --- auxiliary updates.
-   *load_params()* --- called by Scripts 09b, 09d, 19, 21. Returns a dict containing per-cluster β, Sy, h_disp, peak month, forest flag, and the summer climate means.

The *\_DEFAULTS* dict at the top of the module records the placeholder values used on a first pipeline run (β₁ = 3.5, β₂ = 1.5, β₃ = 0.025, Sy = 0.25, clearfell_b2_mult = 1.10, thinning_b2_mult = 1.05, peak_month = 2). These are chosen as central plausible values rather than as scientifically meaningful --- they exist to keep the pipeline runnable on a fresh install before upstream scripts have produced canonical outputs.

### []{#anchor-70}[]{#anchor-71}[]{#anchor-72}map_utils.py

GIS and map-plotting helpers shared by every spatial-output script (04, 07, 08, 11b, 12, 13, 18, 19, 20). Key functions:

-   *load_dem_layer(ax, data_dir)* --- coloured terrain colormap onto an existing axes. Used by point-symbol metric maps.
-   *load_dem_hillshade(ax, data_dir, alpha, vert_exag, zorder)* --- greyscale hillshade (LightSource, azdeg=315, altdeg=35). Used where a metric surface is overlaid semi-transparently.
-   *add_kml_features(ax, data_dir)* --- overlays *Features.kml*, *streams.kml*, *clearfell.kml*. Returns legend handles.
-   *add_osm_basemap(ax, gdf)* --- OSM fallback when the DEM is unavailable.
-   *add_idw_surface(ax, df, value_col, xi, yi, method, ridge_mask_threshold, dem_e_arr, dem_n_arr, dem_data, cmap, norm, alpha, zorder)* --- inverse-distance-weighted interpolation of a per-well metric onto a regular grid, with an optional ridge mask (cells where the DEM sits more than *ridge_mask_threshold* metres above the IDW-interpolated well-DEM surface are masked, preventing extrapolation onto the bedrock ridge where there are no wells). Returns the pcolormesh object, grid coordinates, and the masked surface.
-   *plot_metric_map(map_df, value_col, title, output_path, cmap, data_dir, vmin, vmax)* --- full publication-quality spatial map: DEM background, KML overlays, cluster-shape markers, dual colorbars, legend. The high-level wrapper that the spatial scripts call.

The module routes through *BW_MODE* for B&W mode rendering, switching to hillshade DEM, greyscale colormaps, and hatched legend markers when active.

### []{#anchor-72}[]{#anchor-73}[]{#anchor-74}How the modules compose

A typical analytical script imports from several utility modules:

from utils.config import DRAINAGE_DATUM, CLUSTER_LABELS, FOREST_CIDS

from utils.paths import (

INT_WELLS_CLEAN, INT_CLIMATE, INT_MASTER_DATA,

OUT_NN_FIGURE, OUT_NN_TABLE,

)

from utils.model_utils import fit_ssm, build_ssm_frame, assert_physical_signs

from utils.data_utils import clean_well_series, normalize_well_name

The pattern is intentional: constants from *config*, paths from *paths*, OLS from *model_utils*, and small per-row transformations from *data_utils*. Where the script implements one of the BACI or scraping analyses, it additionally imports from *clearfell_common* or *scraping_common* for the suite-shared logic. Where it is a spatial output, it imports *map_utils* for the rendering helpers. Scripts do not import from each other --- every shared piece of state passes through an intermediate CSV or through one of these utility modules.

# []{#anchor-74}[]{#anchor-75}F.6 Which record does each analysis use

The reference network admits a well at more than 100 months of record. That threshold is an admission rule and not a fitting window, and the distinction matters because the analyses below deliberately use different parts of the record. Three roles are in play. A fit whose coefficients are consumed downstream wants every month available, because identification improves with record length. A comparison across wells wants an equal record at every well, because otherwise the wells are not comparable with each other. An intervention analysis wants the months either side of the event and nothing else.

Two consequences follow, and both are deliberate. The cluster-centroid coefficients of Table 3 are fitted on each cluster\'s full record, while the per-well coefficients behind the coefficient atlas are fitted on an equal trailing window; the two are therefore on different bases, and Table 3 prints both so the difference is visible rather than implied. The benchmark of §S.5 refits both models on the same capped frame, which is the one place an equal window is load-bearing rather than conventional.

  ---------------------------------- ---------------------------------- -------------------------------------- --------------------------------------------------------------------------------------------------------
  Analysis (script)                  Wells                              Record used to fit                     Notes
  Network admission (01)             88 → 66                            ---                                    a well is admitted at more than 100 months of valid record, still reporting after February 2026
  Clustering (02)                    66                                 full record, pairwise-complete         each well pair is correlated on the months the two share; overlap ranges 113 to 250 months, median 185
  Cluster-centroid SSM (03)          5 centroids                        full record (window = None)            n = 236 to 248; the headline mechanistic table
  Per-well SSM (03)                  66                                 trailing 100 months                    n = 100 at every well; the per-well coefficient store
  Coefficient atlas (07)             66                                 inherited, no refit                    maps the per-well store; performs no fit of its own
  SSM vs TLM benchmark (08)          63                                 trailing 100 months, both models       scored over the same 100 months; CEH7, CEH8 and CEH37 excluded by rule
  Residual diagnostics (22, 24)      wells at 140+ months, 6 excluded   full record, with intercept            Model B; the diagnostic companions of §S.16
  Identifiability diagnostic (30)    C4 wells and all centroids         both bases, reported side by side      a sensitivity, not a headline
  BACI intervention suite (09, 10)   BACI tiers                         era windows either side of the event   clearfell 2017-12; scrapes 2015-04 and 2023-10
  Specific yield, WTF (17)           66                                 event-based, not a window              individual recharge events; consumes the per-well store
  MSL5 (26, 26b)                     reference and extended tiers       five-year spring windows               window means, anchored 2017 to 2023
  ---------------------------------- ---------------------------------- -------------------------------------- --------------------------------------------------------------------------------------------------------

Every window in the table is a named constant in utils/config.py, not a literal in a script: MIN_MONTHS_THRESH for admission, LCSC_DATA_LIMIT for the comparison window, RESIDUAL_DIAG_MIN_MONTHS for the residual-diagnostic floor, and the intervention dates in clearfell_common. The centroid fits pass window = None explicitly rather than by omission.

# []{#anchor-75}[]{#anchor-76}[]{#anchor-77}Phase 1 --- Core LCSC Chain

## []{#anchor-77}[]{#anchor-78}[]{#anchor-79}S.1 Script 01 --- Data preparation

Step 1 / 27. Phase 1.

### []{#anchor-79}[]{#anchor-80}[]{#anchor-81}Motivation

Script 01 is the gateway to every downstream step in the pipeline. Each of the 27 scripts that follow reads from one or more of its eight output files, and no other script touches the raw data CSVs (with two documented exceptions that re-read raw inputs for specialist purposes: Script 09a for BACI windowing and Script 24 for sunshine-hour series). The chapter therefore covers two distinct jobs that Script 01 performs together: a *technical* job --- converting three raw data sources into a self-consistent set of monthly time series with a single date convention, a single well-name convention, and well elevations in metres above Ordnance Datum --- and a *scientific* job, which is to declare the membership of the reference network and the extended network that subsequent analyses operate on. Three methodological choices here have particular weight in the rest of the document: the day-15 bucketing convention introduced in F.2, the hardcoded reference-network whitelist that excludes the Forest Enterprise clearfell wells, Llyn Rhos-Ddu, and two singleton-outlier CEH wells, and the single-month interpolation *limit=1* policy with its per-cell provenance partner file *01_wells_provenance.csv*. All three are described in summary in the front matter; this chapter is the full description.

### []{#anchor-81}[]{#anchor-82}[]{#anchor-83}Inputs

  --------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Input file                              Description
  data/Newborough_Cleaned_For_Model.csv   Field-collected monthly dipwell readings, manually pre-cleaned by the author. Wells are columns, reading dates are rows in *DD/MM/YYYY* form.
  data/Well_locations_height.csv          DGPS-surveyed easting, northing, ground elevation, and pipe-top upstand per well. The *Pipe_Top_Elev* column is the independently measured reference datum for field readings.
  data/RAF_Valley_Climate.csv             Met Office monthly returns from RAF Valley station, ≈16 km north-east of the site, 1930--present. Provides monthly maximum and minimum temperature, air-frost days, rainfall, and sunshine hours.
  --------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-83}[]{#anchor-84}[]{#anchor-85}Methodology

The script runs four blocks in sequence, preceded by a metadata sanity check.

The sanity check passes both the well-name set from *Well_locations_height.csv* and the well-name set from the dipwell CSV through *normalize_well_name* (lower-case, whitespace-stripped) and prints any mismatch. The function is also used by every downstream script that joins on well name, so the same normalization rule applies throughout the pipeline.

**Climate processing.** The Met Office CSV has *Mon YY* header dates (e.g. "Jan 95", "Dec 26"). These are parsed by *parse_met_date* with a two-digit-year cutover handled internally: years ≤ 26 are interpreted as 21st century, otherwise 20th century. The cutover is rolled forward each year as part of the annual data update. Rainfall is converted from millimetres to metres, and the Met Office *\"\-\--\"* missing-data marker is replaced by zero. Treating missing rainfall as no rainfall rather than as unknown rainfall is a conservative choice; long gaps in the RAF Valley record are rare and the 1930--present series is otherwise complete, so the alternative --- propagating NaNs through every downstream water-balance calculation --- would lose more information than it preserves. Mean monthly temperature is taken as the arithmetic mean of the recorded monthly maximum and minimum. The maximum-temperature column header occasionally migrates between *\"Max Temp ©\"* and *\"Max Temp (C)\"* between Met Office releases; both forms are handled.

Potential evapotranspiration is then computed by the local *thornthwaite_pet_m()* function (specified below). The cleaned monthly P (m) and PET (m) are written to *01_climate.csv* along with the source temperatures.

**Bucketing.** The raw well CSV is transposed so that rows become dates and columns become wells. The day-15 bucketing convention is then applied: a reading taken on day ≤ 15 of month *M* is assigned to month *M*−1 (the previous month's water table); a reading on day \> 15 of month *M* is assigned to month *M*. The cutoff is empirical --- field practice is that monthly readings are taken either in the last few days of a month or in the first week of the following month, and the day-15 boundary sits cleanly in the gap between these clusters. Once bucketed, multiple readings in the same month are averaged. The convention and its implications for downstream alignment with the climate record are covered in F.2; Script 01 is where it is implemented and where the change from the legacy nearest-month bucketing was made.

The canonical implementation in *01_data_prep.py* is

d = pd.to_datetime(wells.index, dayfirst=True, errors=\"coerce\")

prev = (d.to_period(\"M\") - 1).to_timestamp()

this = d.to_period(\"M\").to_timestamp()

wells.index = np.where(d.day \<= 15, prev, this)

*(d.to_period(\"M\") - 1).to_timestamp()* correctly subtracts one calendar month for any day-of-month. The seemingly equivalent *dt - pd.offsets.MonthBegin(1)* should **not** be used: *pd.offsets.MonthBegin* rolls to the start of the *current* month when the input is not already day-1, so for any reading taken between days 2 and 15 it returns the same month instead of the previous month --- silently corrupting every such reading. Any parallel-pipeline check that re-implements bucketing should copy the code form above verbatim.

A single-well merger handles the historical *NW8* → *NW8B* replacement: *NW8B* values take precedence where available, with *NW8* as the fallback, and the result is stored on a single *NW8* column.

**Well cleaning.** Each well column is then passed through *clean_well_series* (in *utils/data_utils.py*), which masks readings more negative than *MIN_PHYSICAL_DEPTH = −4.0* m and then fills any single-month gap (one consecutive NaN bridged between two measurements) by time-based linear interpolation. The interpolation *limit* parameter is set to *1*. Multi-month gaps are left as NaN downstream. The −4 m floor is a safety margin: the deepest plausible water table at Newborough is around 3 m below ground, so a reading more negative than −4 m is treated as unphysical and dropped before downstream analysis sees it.

The *limit=1* rule permits interpolation across single missed-visit gaps only. A looser *limit=3* setting --- bridging gaps of up to three consecutive months --- was tested against a site-wide audit of the 17-well clearfell-BACI panel from 2007 onwards and rejected. Under *limit=3*, 124 monthly cells (3.2 % of the BACI panel) were filled by interpolation; of these, 52 were two- or three-month runs and a disproportionate share spanned the Jun--Sep drawdown season --- exactly the season in which linear interpolation between May and October endpoints systematically flattens the summer minimum that the analysis is built around. Three well-years (WMC3 2019, NW6 2019, NW7 2019) acquired a phantom summer minimum despite zero measured Jun--Sep readings: a 154-day field-access gap at all three Climate-control wells would be bridged by a single straight line from each well's May reading to its October reading. Under *limit=1*, those 52 multi-month cells become NaN and are excluded from downstream analyses. The 72 cells still bridged by *limit=1* (1.85 % of the BACI panel) are all single missed-visit gaps, which match the field interpretation of one delayed monthly visit and do not span a drawdown season. The annual Forest × Impact ANCOVA-BACI step from Script 10a is robust in direction to the choice between the two settings; the summer-only contrast (Jun--Sep refit) is sensitive to it, because the multi-month summer interpolations the looser rule admits fall directly on the metric. The empirical consequences are taken up in S.6 (scraping summer minima) and S.7 (clearfell BACI).

Positive readings are not masked. The dune slacks at Newborough regularly flood above the dipwell pipe top, and on those visits the surveyor records the standing-water level above the pipe rim. These are real water-level observations, not measurement artefacts, and the SSM, the clustering, and the flood-threshold work all depend on them. The current dataset contains around 1,400 such readings, with a median of +13 cm above pipe top, a 99th percentile of +53 cm, and a maximum of +73 cm. They pass through the cleaning step unchanged.

**Provenance tracking.** Alongside the cleaned wells file, Script 01 emits *01_wells_provenance.csv* --- a sibling table of identical shape (same row index, same column set as *01_wells_clean.csv*) recording per-cell origin as one of three string values: *\"measured\"* for a value present in the raw bucketed series, *\"interpolated\"* for a value created by *clean_well_series* linear-fill, *\"missing\"* for a cell still NaN after cleaning. The provenance file is the public record of what was inferred versus what was observed. Across the full 80-well reference + extended panel from 2005 onwards (250 monthly rows × 80 columns = 20,000 cells), the current state is 14,948 measured, 274 interpolated, 4,778 missing. Restricted to the 17-well clearfell-BACI panel from 2007-01 onwards (229 months × 17 wells = 3,893 cells), the state is 3,399 measured, 72 interpolated, 422 missing.

The provenance file is consumed by analysis scripts that have an interpretive reason to discount cells with low measured-coverage. Two consumers are wired in the current pipeline: Script 10d (clearfell summer minima) and Script 09c (scraping summer minima) load the provenance file via *clearfell_common* / *scraping_common* and apply *min_measured=2* to *annual_summer_minimum*, dropping any (well, year) row whose Jun--Sep series contains fewer than two measured months. The new *n_interpolated* column in *10d_01_summer_minima.csv* and *09c_01_summer_minima.csv* flags the surviving rows for reviewer inspection. Script 03's *build_ssm_frame* / *fit_ssm* accept an optional *provenance* argument and an *exclude_interpolated=False* flag that defaults to retaining all rows in the canonical SSM fit. Retaining all rows is a separate matter from the interpolation *limit* setting, which alters *01_wells_clean.csv* itself: the canonical β₁/β₂/β₃ cluster-coefficient table is computed under *limit=1* (see §S.3). The *exclude_interpolated* flag is documented as an available sensitivity path, run on demand.

**Network partitioning.** The cleaned table is then partitioned into two networks. The full cleaned table (*01_wells_clean.csv*) retains every well with at least *MIN_MONTHS_THRESH = 100* non-NaN months. From this set:

-   The **reference network** (*01_wells_reference.csv*) is the subset that meets all three of the following criteria: at least 100 monthly observations, a final record date on or after *RECENCY_DATE = REFERENCE_CUTOFF_DATE = 2026-02-01* (from *utils.config*), *and* appears on the hardcoded *REFERENCE_NETWORK_WHITELIST* of 66 well names.
-   The **extended network** (*01_wells_extended.csv*) is every well with at least *MIN_EXTENDED_MONTHS = 24* observations, *except* those on *EXTENDED_NETWORK_BLACKLIST = frozenset({\"llynrhos\", \"pdfs\"})*. Wells that meet the automatic reference-eligibility criteria but are not on the whitelist are *demoted* --- they are excluded from the reference network and routed to the extended network.

Setting *REFERENCE_NETWORK_WHITELIST = None* restores fully automatic selection (any well meeting the auto-criteria enters the reference network). The whitelist is the live setting and exists to pin the reference network deterministically to the published partition, regardless of subsequent data additions.

The four categories of exclusion from the reference network are:

1.  **FE1--FE4 and LIS1.** These wells lie inside the Forest Enterprise clearfell footprint and record a non-stationary management regime --- the SSM's stationarity assumption is not appropriate for them. They are routed to the extended network, where they form the treatment arm of the Script 10 BACI suite. The decision is methodological, not a judgement on data quality.
2.  **Llyn Rhos-Ddu and ***pdfs***.** Llyn Rhos-Ddu records lake stage, not water-table response to recharge. It is excluded from both networks via *EXTENDED_NETWORK_BLACKLIST* because the SSM forcing terms (P and PET) do not describe a lake's hydrology in the same way they describe a dune-slack water table. The *pdfs* well was added to the blacklist on 2026-05-24: its hydrograph carries a tidal-influence signature that makes it unrepresentative of water-table behaviour, the same exclusion principle applied to CEH3 and CEH22 below. With *pdfs* blacklisted and one further extended well (*p1*) brought back in once its elevation row was completed, the classified network settles at 88 wells (66 reference + 22 extended).
3.  **CEH3 and CEH22.** Ward's hierarchical clustering identifies these wells as singleton outliers at low partition orders, consistent with tidal-signal contamination on top of the climate-forcing response that the SSM is designed to capture. CEH22 sits at 3.3 m ground elevation, near the lower end of the elevation distribution; CEH3 has the most pronounced tidal signature on inspection (working assessment by the author). Both remain in the extended network for per-well analyses where their behaviour is of interest in its own right.
4.  **Other automatic candidates.** Wells that meet the record-length and recency criteria but were not part of the originally published 2026 reference network are routed to the extended network rather than added to clustering. This is the protective half of the whitelist mechanism: adding a well to the reference network requires a code change, which guards against silent partition shifts when the underlying data is updated.

Elevation conversion. The cleaned well table is then re-expressed in metres above Ordnance Datum and written to 01_wells_clean_maod.csv. Field readings are dips from the pipe top, but the master workbook applies each well's surveyed upstand on export, so the value carried in *Newborough_Cleaned_For_Model.csv* is the *depth from surface* sheet: *level = upstand − dip*, a signed height relative to the ground surface, negative below ground and positive where a slack is ponded. The conversion is therefore *maOD = ground_elev_m + level*, which is the pipe-top conversion with the upstand already folded in: *maOD = pipe_top − dip = (ground + upstand) − dip = ground + (upstand − dip)*, the last term being the stored value. Because the upstand is applied on export, no further upstand term belongs anywhere in the pipeline. Ground and pipe-top elevations are derived once in Script 01 from *well_metadata.csv* and exported via *01_well_elevations.csv*; no downstream script re-derives them, and none reads *DEM_Ground_Elev*, *DGPS_Ground_Elev* or *Pipe_Top_Elev* directly. The conversion sign is sanity-checked on a small sample of wells against the original raw depth, with a printed pass/fail summary in the script log.

A condensed elevation lookup (01_well_elevations.csv: ground elevation, upstand, pipe-top elevation per well) is written for use by Scripts 03 (upstand audit) and 10--21.

**Thornthwaite PET (***thornthwaite_pet_m***).** PET is computed locally inside Script 01 rather than imported from a utility module, on the principle that the climate-processing step is self-contained. The implementation follows Thornthwaite (1948) with the Thornthwaite & Mather (1955) day-length and month-length correction. In outline:

The heat index *I* is a twelve-month sum of monthly heat indices *i = (T/5)¹·⁵¹⁴* for months with monthly mean temperature *T* ≥ 0 °C. The sum is taken over the trailing twelve months ending at the month being computed, not over the calendar year as in Thornthwaite (1948); the first eleven months of the station record, which have no complete trailing window, are back-filled from the first that does. The exponent *a* is the cubic polynomial in *I* of Thornthwaite (1948). Unadjusted monthly PET in millimetres is then

The departure is required because the calendar-year sum is undefined on a part-complete year. The station record ends in February 2026; summed over that calendar year, *I* fell to 3.1 against a normal near 45, and because PET scales as (10T/*I*) raised to *a*, a collapsed *I* inflates PET severalfold: February 2026 returned 66.8 mm against a range of 13.0 to 25.7 mm observed for that month at this station. A trailing window always contains exactly one of each calendar month, so it is a true annual heat sum and cannot collapse, and it is causal, where the calendar-year form makes the PET of a given month depend on the months that follow it. Over the well-record period the two forms are equivalent in central tendency: median difference in monthly PET 0.00%, 5th to 95th percentile ±5.5%, though individual months can differ by up to 16.6%. A fixed climatological *I* taken from the long-run mean of complete years was considered and rejected: at 38.0 it lies below the recent-decades mean near 45, and a lower *I* raises PET, so it would have inflated atmospheric draw across the analysis period by a median of 4.2%.

$${\text{PET}_{\text{u}} = 16}\left( \frac{10T}{I} \right)^{a}$$

with the boundary condition PET = 0 for *T* ≤ 0 °C. For *T* ≥ 26.5 °C the formula is replaced by the Camargo et al. high-temperature linearisation, which prevents the polynomial form from blowing up at temperatures that are rare but not impossible at the site. The adjusted monthly value applies the *K* correction

$$K = {\frac{N}{12} \cdot \frac{d}{30}}$$

where *N* is the mean monthly daylight hours computed from the site latitude (*RAF_VALLEY_LAT_DEG = 53.25°* from *utils.config*) and the solar declination for the mid-month day, and *d* is the number of days in the month. The output is monthly PET in **metres** per month. The pipeline-wide convention is that both P and PET are in metres; converting at the producer rather than the consumer side is more reliable than scattering unit conversions through 27 downstream scripts.

**Scenario-parameter seed.** Finally, Script 01 calls *pipeline_params.write_initial_params()* to write the initial state of *01_data_prep/pipeline_scenario_params.csv*. This file is the consolidated scenario-parameter store described in F.4: a per-cluster table of SSM coefficients, specific yields, displacement values, peak month, and summer climate seeds, written here with placeholders and then updated in later passes by Scripts 03 (cluster SSM coefficients), 10e (clearfell coefficient decomposition), and 17 (peak-month seasonal stats). The Script 01 → downstream-scenario handshake is a producer-consumer pattern; the file is the contract, the script is one of four writers, and the scenario-running scripts (09b, 09d, 19, 21) are the consumers.

### []{#anchor-85}[]{#anchor-86}[]{#anchor-87}Outputs

  ------------------------------------------- ------------------------------------------------------------------------------------------------- --------------------------------------------------------------------
  Output file                                 Contents                                                                                          Consumers
  01_locations.csv                            E, N, ground elevation, pipe-top elevation, and upstand per well                                  Scripts 02--25 (any spatial analysis)
  01_climate.csv                              Monthly P (m), PET (m), source temperatures                                                       All SSM-fitting and water-balance scripts
  01_wells_clean.csv                          Bucketed, cleaned, interpolated depth time series                                                 Scripts 02, 03, 09--21
  01_wells_provenance.csv                     Per-cell provenance partner to *01_wells_clean.csv*: values *{measured, interpolated, missing}*   Scripts 03 (optional *exclude_interpolated* sensitivity), 09c, 10d
  01_wells_clean_maod.csv                     The same series in m AOD                                                                          Scripts 03 (centroid m AOD), 20
  01_wells_reference.csv                      Reference-network subset (66 wells)                                                               Scripts 02 (clustering), 06 (extension audit)
  01_wells_extended.csv                       Extended-network subset (22 wells)                                                                Scripts 06, 09b, 10h, 18, 25
  01_well_elevations.csv                      Ground elevation, upstand, pipe-top per well                                                      Scripts 03 (upstand audit), 10--21
  01_data_prep/pipeline_scenario_params.csv   Per-cluster β, Sy, h_disp, peak month, summer climate seeds                                       Scripts 09b, 09d, 19, 21
  ------------------------------------------- ------------------------------------------------------------------------------------------------- --------------------------------------------------------------------

All paths resolve through *utils/paths.py* (*INT_LOCATIONS*, *INT_CLIMATE*, *INT_WELLS_CLEAN*, *INT_WELLS_PROVENANCE*, *INT_WELLS_CLEAN_MAOD*, *INT_WELLS_REFERENCE*, *INT_WELLS_EXTENDED*, *INT_WELL_ELEVATIONS*, *DIR_01*) and are never hardcoded in the script body.

### []{#anchor-87}[]{#anchor-88}[]{#anchor-89}Limitations and known caveats

-   **The reference-network whitelist is hardcoded.** Adding or removing a well requires a code change and a CHANGELOG entry. The trade-off is deterministic reproducibility against operational ease, and this script deliberately prioritises the former; the alternative --- an algorithmic selection that drifts silently when the data is updated --- has worse failure modes for a paper-of-record analysis.
-   **The bucketing convention assumes monthly readings.** Multiple readings in the same bucketed month are averaged, which would mask any genuine intra-month dynamics if higher-frequency data became routinely available. The current monthly cadence is set by the field protocol and the script's design follows that cadence; sub-monthly logging would require a different implementation.
-   **Thornthwaite PET is a simple empirical estimator.** It uses temperature and day length, not net radiation or vapour-pressure deficit, and is known to underestimate summer atmospheric demand for forested surfaces. The site-wide implications are taken up in S.10 (depth-dependent PET) and S.16 (residual seasonality), and §5.3 of the report discusses what this means for the cluster-mean β₂ values. For a long-term monthly model on a temperate site with the data the Met Office routinely publishes, Thornthwaite is the defensible choice; the limitation is acknowledged rather than corrected here.
-   **The 4 m depth floor catches nothing in the current dataset.** No reading in *Newborough_Cleaned_For_Model.csv* is more negative than −2.87 m. The floor is a forward-looking safeguard against stray entries from future data drops or damaged-sensor records, not a constraint on the current data. It is implemented as a signed floor (*series \>= -4.0*) against the negative-valued depth series.

### []{#anchor-89}[]{#anchor-90}[]{#anchor-91}Where the result appears in the report

-   §3.1 *Data preparation* --- bucketing convention, network partition.
-   §3.1.2 --- the FE/LIS exclusion rationale and the Llyn Rhos / CEH3 / CEH22 routing.
-   §3.2 --- Thornthwaite PET specification.
-   §3.3 and onward --- implicit, in every analysis that reads from the Script 01 outputs.

### []{#anchor-91}[]{#anchor-92}[]{#anchor-93}Cross-references

-   **F.2** --- bucketing convention, date semantics, the *HEADLINE_LAG = 0* decision and its history. Refer to F.2 rather than re-deriving.
-   **F.3** --- SSM equation form and sign conventions; relevant background to the network-partition decisions but not re-stated here.
-   **F.4** --- reference-network membership counts (66 wells; C1 = 7, C2 = 24, C3 = 21, C4 = 9, C5 = 5) and the *pipeline_scenario_params.csv* producer-consumer architecture.
-   **F.5** --- *paths.py*, *data_utils.py*, and *pipeline_params.py* module roles.
-   **S.6** (sub-script 09c) --- consumes *01_wells_provenance.csv* for the *min_measured=2* summer-minima rule.
-   **S.7** (sub-scripts 10a, 10d) --- consumes *01_wells_provenance.csv* for the same rule.
-   **S.7** (sub-script 10e) --- updates *pipeline_scenario_params.csv* with the clearfell coefficient decomposition.
-   **S.10** --- depth-dependent PET correction that addresses the Thornthwaite under-estimation noted above.

## []{#anchor-93}[]{#anchor-94}[]{#anchor-95}S.2 Script 02 --- Behavioural clustering

Step 2 / 27. Phase 1.

### []{#anchor-95}[]{#anchor-96}[]{#anchor-97}Motivation

Script 02 produces the cluster partition that almost every downstream analysis inherits. It applies Ward's hierarchical clustering on Pearson correlation distance to the 66-well reference network defined by Script 01, cuts the resulting tree at *k* = 5, and writes a per-well cluster assignment to *02_cluster_stats.csv*. Three methodological decisions made here propagate through the rest of the supplement: the choice of Ward's linkage on correlation distance (rather than Euclidean or some other behavioural metric); the choice of *k* = 5 (rather than 4, 6, or some other partition order); and the anchor-well remap that pins Ward's arbitrary integer outputs to canonical, stable cluster IDs.

Alongside the clustering itself the script computes a richer validation suite --- silhouette and Calinski-Harabasz across *k* = 2...10, bootstrap stability across *k* = 4...7, co-assignment heatmaps --- and a second analysis bundle that does not strictly belong to clustering: per-well and per-cluster seasonal-amplitude descriptors with a climate-normalized variant that excludes three identified drought summers. The amplitude descriptors feed §4.2 of the report directly.

### []{#anchor-97}[]{#anchor-98}[]{#anchor-99}Inputs

  ------------------------ ------------------------------------------------------------------------------------------------------------------------------------
  Input file               Description
  01_wells_reference.csv   Reference-network depth time series, 66 wells (Script 01)
  01_wells_clean.csv       Full cleaned table --- used inside *make_cluster_hydrograph_wb_figure()* for the water-balance panel of figure *02_03* (Script 01)
  01_climate.csv           Monthly P and PET (m), used in the same figure (Script 01)
  ------------------------ ------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-99}[]{#anchor-100}[]{#anchor-101}Methodology

The script proceeds in seven blocks executed in order in *\_\_main\_\_*:

**1. Load and prepare reference data.** *01_wells_reference.csv* is read with *parse_dates=True*, coerced to numeric, and any columns that are entirely NaN are dropped. The result is a DataFrame with monthly rows and one column per reference well.

**2. Build the correlation-distance matrix.** Distance between two wells *i* and *j* is *1 − ρ(i, j)* where ρ is the Pearson correlation of the two monthly depth series over their common non-NaN months. The full reference time series is passed through; there is no detrending or windowing step before the correlation is computed. This is intentional: the goal of the partition is to capture *behavioural* similarity (do two wells rise and fall together over the full record), and the same long-term wetting or drying signal that a linear detrend would remove is itself a behavioural property that distinguishes coastal-erosion-affected wells from the rest of the network. Removing it would reduce the dimensionality of "behaviour" that the algorithm sees.

The matrix is computed by *\_correlation_distance()*: *corr = wells.corr()* (which uses pairwise non-NA observations per cell), then *1 − corr*, then clipped to non-negative, then symmetrised against small numerical asymmetries, then converted to the condensed form scipy's *linkage* expects. The square form is retained for use as the precomputed distance input to *silhouette_score*.

**3. Ward's linkage and the k-sweep validation.** Ward's variance-minimisation linkage is applied to the condensed distance vector. The cluster validation runs over *k* = 2...10, recording silhouette score (on the precomputed correlation-distance matrix), Calinski-Harabasz score (on the raw wells-as-rows feature matrix with within-well mean-imputation of gaps for the CH computation only), and the Ward merge distance at the *k*-th-to-last linkage step. Outputs land in *02_02_validation_plots.png* (silhouette + merge distance at the chosen *k*) and *02_02b_validation_k_sweep.png* (all three metrics across the full *k* range).

**4. Bootstrap stability diagnostics (***bootstrap_cluster_stability***).** For each *k* in *K_RANGE_BOOTSTRAP = (4, 5, 6, 7)*, the reference network is resampled with replacement *N_BOOTSTRAP = 1000* times. Each bootstrap re-fits Ward's at *k* on the resampled distance matrix. Pairwise co-assignment counts are accumulated: numerator counts bootstraps in which both wells appear and land in the same cluster, denominator counts bootstraps in which both appear. The per-well stability is the median co-assignment probability between the well and its cluster-mates in the reference (full-sample) fit, which is the "does this well stick with its neighbours" interpretation. Reproducibility is fixed by *BOOTSTRAP_SEED = 20260424*. Outputs include per-well stability scores, per-cluster summary statistics, and a co-assignment heatmap for each *k*.

**5. Canonical-ID remap (***\_remap_cluster_ids_by_anchor***).** *fcluster* returns arbitrary integer IDs that depend on the order Ward's encounters merges, so the same partition can come back with cluster integers permuted between runs. The remap function locates each canonical anchor well in the raw labelling, identifies the raw cluster it belongs to, and reassigns that raw ID to its canonical ID. Two integrity checks are enforced: anchor wells listed for the same canonical ID must land in the same raw cluster (otherwise the partition assumptions have been violated and *ValueError* is raised), and no raw cluster can be claimed by two different canonical IDs (also a *ValueError*). A guard at module load asserts that *CLUSTER_ID_ANCHORS* and *utils.config.CLUSTER_LABELS* describe the same set of cluster IDs; if they disagree, *RuntimeError* is raised before any analysis runs.

The canonical anchors are:

  ---- ----------------------- --------------
  \#   Cluster                 Anchor wells
  1    C1 (Lake Edge)          ceh5, ceh11
  2    C2 (Dune)               d10
  3    C3 (Western Residual)   nw1
  4    C4 (Main Forest)        ceh2
  5    C5 (Coastal Forest)     ceh16, nw9
  ---- ----------------------- --------------

These anchors are *interior* wells --- wells that on visual inspection of the hydrograph cluster most clearly to each behavioural type --- not the wells with the highest within-cluster correlation. Anchoring to interior wells guards against centroid drift between runs silently relabelling the partition when the data is updated.

**6. Cluster assignment write-out.** The remapped labels are saved to *02_cluster_stats.csv* with columns *Match_ID* (normalized well name), *Name_Original*, *Cluster* (canonical integer ID), and *Cluster_Label* (human-readable label from *CLUSTER_LABELS*). This file is the contract for downstream consumers --- Script 03 reads it to define the per-cluster SSM fits, and most analysis scripts from 04 onwards depend on it.

**7. Dendrogram and cluster-hydrograph figures.** The dendrogram (*02_01_dendrogram.png*) is produced with *color_threshold* set to the *k* = 5 merge height; tick labels are coloured by canonical cluster ID. The cluster-hydrograph water-balance figure (*02_03_cluster_hydrographs_wb.png*) shows cluster-mean depth-below-pipe time series with an annotated water-balance panel above. The water-balance panel uses *DETREND_START = 2004-12-01* and *DETREND_END = 2025-12-01* to compute a long-term mean of the climate water balance (P − PET) for visual reference on the figure; these constants are local to the figure and play no role in the clustering distance computation.

**Amplitude descriptors (***compute_cluster_amplitude_descriptors***).** A secondary descriptor of cluster behaviour, intentionally separated from the partition itself. For each well the script computes the seasonal amplitude *p90 − p10* over the full record, over the pre-2018 sub-window (*\< AMP_SPLIT_DATE = 2018-01-01*), and over the post-2018 sub-window. The split date is anchored to the 2018 UK-wide summer drought --- one of the three identified drought summers and the most consequential meteorologically --- which falls a few weeks after the December 2017 experimental clearfell. The pre-window therefore captures the pre-2018 baseline (before both the meteorological inflection and the management intervention); the post-window captures the drought-dominated, post-felling period. A window stat requires at least *AMP_MIN_OBS_PER_WIN = 24* non-NaN months or it returns NaN.

Two parallel climate-normalized variants drop the Jun--Sep monthly observations for three identified drought summers --- *DROUGHT_SUMMERS = (2005, 2018, 2022)* --- from the relevant window before recomputing *p90 − p10*. The summers were identified empirically against the 1931--2017 RAF Valley Jun--Sep rainfall mean of 260 mm (σ = 70 mm) using a one-sigma-below-mean threshold of approximately 190 mm. The list is hardcoded so the normalization is auditable: the values should only be revised if the underlying RAF Valley series is updated. Note that the normalization drops drought summers --- not all dry summers --- and the unnormalised variant is also reported so the reader can see both.

Per-well descriptors are written to *02_08_cluster_amplitude_per_well.csv*. Per-cluster aggregation is **median-of-medians across wells** within each cluster (not aggregation on a cluster-mean hydrograph), with the per-cluster summary written to *02_09_cluster_amplitude_summary.csv* and a boxplot of post-2018 amplitude distributions to *02_10_cluster_amplitude_boxplot.png*. A defensive check at the top of the function rejects any *cluster_df* that contains non-canonical IDs (i.e. that has not been passed through the remap), so the amplitude file cannot drift away from the partition.

### []{#anchor-101}[]{#anchor-102}[]{#anchor-103}Site-specific choices and rationale

-   **Ward's linkage.** Single-linkage produces chained clusters in this data --- the algorithm strings together intermediate wells and the lake-edge / dune distinction is lost. Complete-linkage produces overly compact clusters that split otherwise coherent behavioural groups across the partition boundary. Ward's variance-minimisation is the standard choice for small-network behavioural clustering and produces clusters that align with the site's hydrogeology on inspection.
-   **Correlation distance, not Euclidean.** The clustering question is about behavioural similarity, not absolute level. Two wells with identical seasonal cycles but mean depths 1 m apart should cluster together --- and do under correlation distance. Euclidean distance on raw depths would separate them.
-   **No detrending before correlation.** Long-term trends in individual wells are part of the behavioural signal the partition is meant to capture. The coastal-edge wells in C5 share a coastal-erosion-influenced trend signature that a linear-trend removal would erase; the eastern lake-buffer wells share a different trend signature. Pearson correlation on raw monthly series captures both seasonal and inter-annual co-variation, which is the intended target. The *DETREND_START*/*DETREND_END* constants in the script are scoped to the water-balance panel of figure 02_03 and do not touch the wells.
-   **k = 5, not k = 6.** Earlier work used a k = 6 partition with a separate single-well "Lake" cluster (Llyn Rhos-Ddu, n = 1) and a separate single-well "Coastal" cluster. Under the published partition, Llyn Rhos-Ddu is excluded from the reference network on physical grounds (S.1) and treated as a fixed-head boundary feature; the current C1 (Lake Edge) captures the wells *adjacent* to the lake. The mathematical case for k = 5 rests on the Ward's merge-distance curve, which shows a clear elbow at k = 4--5: the drop from k = 4 → k = 5 (≈ 0.19 → 0.17) is the last substantial descent before the curve flattens through k = 6--10. Silhouette is monotonically declining from k = 2 (≈ 0.46) through k = 5 (≈ 0.40) and is not on its own an argument for any specific k beyond 2 --- this is typical of behavioural-clustering datasets where the data has hierarchical structure rather than well-separated point clouds. k = 5 is the partition order that sits at the merge-distance elbow, resolves the hydrogeologically meaningful C4 / C5 split (which k = 4 collapses), keeps every cluster at ≥ 5 members, and has an interpretable site reading. The full history is consolidated in F.4.
-   **Hardcoded anchor wells, not centroid- or correlation-based.** Anchors are interior wells chosen by visual inspection --- not the wells with the highest within-cluster mean correlation. Centroid-based anchoring drifts as cluster membership shifts; correlation-based anchoring can be dominated by a tightly correlated sub-group within a heterogeneous cluster. Interior-well anchoring is the most defensive choice and produces deterministic cluster IDs across runs.
-   **Drought-summer normalization in the amplitude descriptor.** The post-2018 window contains three drought summers (2005, 2018, 2022) that disproportionately inflate raw *p90 − p10* in any well that responds to those summers. The climate-normalized variant drops the Jun--Sep months of those years, identified empirically against the 1931--2017 RAF Valley mean rather than against a model-derived definition; this preserves auditability and means the list does not change if a future analysis revises the PET model. The unnormalised variant is reported alongside so the reader can see what the normalization does.
-   **N = 1000 bootstraps.** At N = 200, the per-well stability CIs are noticeably wider; at N = 5000 they tighten to within \~0.001 of the N = 1000 estimates at a runtime cost that is not justified for a diagnostic descriptor. 1000 is the standard published choice for bootstrap-stability diagnostics on networks of this size.

### []{#anchor-103}[]{#anchor-104}[]{#anchor-105}Outputs

  ------------------------------------------------------ ------------------------------------------------------------------------------
  Output                                                 Description
  *02_cluster_stats.csv* (INT\_)                         Per-well: *Match_ID*, *Name_Original*, *Cluster*, *Cluster_Label*
  02_clustering/02_01_dendrogram.png                     Ward's dendrogram, tick labels coloured by canonical cluster
  02_clustering/02_02_validation_plots.png               Merge-distance elbow and silhouette score at the chosen *k*
  02_clustering/02_02b_validation_k_sweep.png            Silhouette + Calinski-Harabasz + merge distance across *k* = 2...10
  02_clustering/02_03_cluster_hydrographs_wb.png         Cluster-mean depth hydrographs with water-balance annotation panel
  02_clustering/02_04_bootstrap_stability_summary.csv    Per-cluster median pairwise co-assignment at each *k* in *K_RANGE_BOOTSTRAP*
  02_clustering/02_05_bootstrap_stability_per_well.csv   Per-well stability scores across *k*
  02_clustering/02_06_coassignment_heatmap_k{k}.png      Co-assignment heatmap, one per *k* in *K_RANGE_BOOTSTRAP*
  02_clustering/02_07_cluster_membership_k{k}.csv        Per-well majority assignment at each *k*
  02_clustering/02_08_cluster_amplitude_per_well.csv     Per-well amplitude descriptors
  02_clustering/02_09_cluster_amplitude_summary.csv      Per-cluster median-of-medians amplitude summary
  02_clustering/02_10_cluster_amplitude_boxplot.png      Post-2018 amplitude distribution boxplot, one box per cluster
  ------------------------------------------------------ ------------------------------------------------------------------------------

### []{#anchor-105}[]{#anchor-106}[]{#anchor-107}Limitations and known caveats

-   **C3 (Western Residual) is the lowest-stability cluster, not C1.** Bootstrap diagnostics give median within-cluster co-assignment of approximately 0.50 for C3 at k = 5, against ≥ 0.93 for C1, C2, C4, and C5. C3 contains two geographically distinguishable sub-populations --- a low-ground southern coastal fringe (ceh4, ceh18, ceh21, ceh36, ceh42) and the west-side open dune wells (nw1, nw2, nw5--7, nw11, nw13) --- that Ward's does not separate at any *k* from 5 to 9 because they share a common behavioural signature at the resolution the algorithm achieves. This is treated as a landscape/behaviour distinction in §3.2 rather than as a clustering failure.
-   **CEH11 is the weakest member of C1 (Lake Edge).** Individual-well bootstrap co-assignment is approximately 0.68 for ceh11 at k = 5, against ≥ 0.95 for the other six C1 members. CEH11 is included on physical grounds (its lake-adjacent location matches the cluster's character) but is flagged as a borderline membership in both the script comment block above *CLUSTER_ID_ANCHORS* and in the report.
-   **The partition is not stable under all parameter perturbations.** Removing the drought-summer mask, or shifting *MIN_RECORD_MONTHS* from 100 to 80, produces small membership changes at the boundaries of C1 and C5 (the two smallest clusters). The published partition is the canonical one and is the basis for every downstream analysis; alternative parameter choices produce qualitatively similar five-cluster structures but are not committed.
-   **The anchor remap fails loudly under sufficient perturbation.** If a future data change causes Ward's output to place two canonical anchors in the same raw cluster, or to split one anchor pair across two raw clusters, *\_remap_cluster_ids_by_anchor* raises *ValueError* rather than silently producing an ambiguous partition. The error is the intended behaviour; resolution is to inspect the dendrogram and either revise the anchors (if the new partition is a refinement of the old) or accept that the partition has genuinely changed and recompute everything that depends on it.
-   *MIN_RECORD_MONTHS = 100*\*\* is duplicated from Script 01.\*\* Script 01's *MIN_MONTHS_THRESH = 100* defines the reference-network membership; Script 02's *MIN_RECORD_MONTHS = 100* is used only inside the cluster-hydrograph water-balance figure to filter the *full* (not reference) wells table for the short-profile panel. The two values happen to coincide and match by convention; if Script 01's threshold were ever changed, Script 02's local constant would need to be revisited.

### []{#anchor-107}[]{#anchor-108}[]{#anchor-109}Where the result appears in the report

-   §3.2 *Cluster definition* --- Ward's, correlation distance, *k* = 5, anchor remap, validation suite.
-   §4.2 *Cluster characterization and description* --- built from the cluster-hydrograph figure and the amplitude descriptors.
-   Table 3 --- cluster mechanistic coefficients (β₁, β₂, β₃) per cluster, sourced from Script 03 but indexed by the partition defined here.
-   Figures 7--9 --- dendrogram, validation, and cluster-hydrograph figures from *02_clustering/*.

### []{#anchor-109}[]{#anchor-110}[]{#anchor-111}Cross-references

-   **F.4** --- *k* = 5 partition table with anchor wells and member counts; identity-vs-integer-keying principle, which *\_remap_cluster_ids_by_anchor* operationalises.
-   **F.5** --- *paths.py*, *config.py*, and *data_utils.py* module roles.
-   **S.1** --- reference-network selection: the 66-well subset that this script consumes.
-   **S.3** --- SSM fitting on the cluster partition. Script 03 reads *02_cluster_stats.csv* and is the primary downstream consumer.
-   **S.4** --- Pearson-affinity audit and extended-network analysis (grouped chapter covering Scripts 04, 05, 06), which quantify how confidently each well's cluster assignment can be defended.
-   **F.4** --- partition history (k = 6 → k = 5 transition, dropped single-well clusters, identity-vs-integer-keying principle) is consolidated in F.4 of this supplement.

## []{#anchor-111}[]{#anchor-112}[]{#anchor-113}S.3 Script 03 --- State-space regression and LCSC

Step 3 / 27. Phase 1.

### []{#anchor-113}[]{#anchor-114}[]{#anchor-115}Motivation

Script 03 is where the state-space model gets fitted to the data. Per-well coefficients are written to *03_master_data.csv* (consumed by Scripts 07, 08, 11, 16, 19, 21, and the rest); cluster-centroid coefficients are written to *03_03_cluster_mechanistic_coefficients.csv* (the source of Table 3 in the main report). Five quantitative validation outputs sit alongside the headline fits: a lag diagnostic that tests whether the centroid responds best to the current month's rainfall or to an earlier one, a 1,000-replicate bootstrap that asks how sensitive each cluster's β estimate is to the particular set of member wells, a leave-one-out sweep that checks for single-well domination, a pre/post-2018 split-window for C1 Lake Edge, and a drainage-datum sensitivity sweep that runs both at the cluster centroid and per-well. The chapter walks each in turn. The SSM equation, sign conventions, displacement formulation, and the role of *DRAINAGE_DATUM = 3.7 m* are covered in full in F.3; this chapter does not re-derive them. The Lumped Catchment Storage Coefficient (LCSC) --- the rescaled β₁ used as the report's headline mechanistic descriptor --- is introduced here for the first time.

### []{#anchor-115}[]{#anchor-116}[]{#anchor-117}Inputs

  -------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Input file                             Description
  01_climate.csv                         Monthly P (m) and PET (m) (Script 01)
  01_wells_clean.csv                     Cleaned depth time series, ground-referenced convention (Script 01)
  01_wells_clean_maod.csv                Same series in m AOD (Script 01)
  01_well_elevations.csv                 Pipe-top elevation and upstand per well (Script 01)
  01_locations.csv                       Easting, northing, ground elevation, pipe-top elevation per well (Script 01)
  02_cluster_stats.csv                   Per-well cluster assignment (Script 02)
  02_08_cluster_amplitude_per_well.csv   Per-well amplitude descriptors (Script 02) --- optional input to the heterogeneity flag in the summary table; falls back to hard-coded values if absent
  01_wells_provenance.csv                Per-cell provenance flags from Script 01 --- optional input, loaded only when a caller invokes *fit_ssm(\..., exclude_interpolated=True)* for the measured-only sensitivity. The canonical centroid fits do not consume this file.
  -------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-117}[]{#anchor-118}[]{#anchor-119}Methodology

The script runs eleven blocks in *main()*. The order matters: per-well fits → centroid construction → centroid headline fits → diagnostic suite (lag, datum, bootstrap, leave-one-out, C1 split) → summary table → figures and regional-average exports. The hard-halt on a centroid sign violation is deferred to the very end so that the diagnostic tables and figures get written *before* the pipeline stops --- these are exactly the tables an investigator needs to diagnose the failure.

Centroid construction --- build_cluster_centroids\*\* and build_upstand_lookup.\*\* Each cluster centroid is the arithmetic mean of its member wells' depth series. No correction is applied: the series are already ground-referenced, so every member well shares a common datum. The upstand lookup (*build_upstand_lookup*) is built from *01_well_elevations.csv* and is read only by the audit below. An *upstand_audit()* diagnostic prints the wells with Upstand_m &gt; 0.30 --- under the live network, CEH2 (\~0.71 m), NW2 (\~0.59 m), and t41a (\~0.40 m) are the three flagged; CEH2 is deliberately tall to remain visible in the forest understorey, NW2 and t41a are the other two ordinary cases. The flag is informational only.

Per-well fits --- per_well_fits. Each reference-network well is fitted individually via model_utils.fit_ssm() (F.3 covers the function's interface), the series being already ground-referenced, so the *DRAINAGE_DATUM = 3.7 m* displacement reference is anchored to the ground surface for every well without further correction. The per-well fit uses window=LCSC_DATA_LIMIT = 100 --- the most recent 100 valid monthly rows --- so that all per-well coefficients describe behaviour over the same recent window. This is the LCSC window subsequently used by Script 08's benchmarking and by Script 30's identifiability sensitivity; Script 07 inherits the resulting per-well coefficients unchanged and performs no fit of its own (S.5). The rationale for choosing it here is downstream consistency. Per-well sign violations (β₁ &lt; 0 or β₂ &lt; 0) are reported but do not halt the pipeline --- only centroid violations halt, because centroid fits are the values the report cites. A second LCSC estimate, the empirical LCSC, is computed alongside the regression LCSC for cross-check: rainfall divided by Δh on each unambiguous recharge event (Δh &gt; 0.02 m), with the screen for spurious ratios (LCSC_raw outside \[0.05, 1.0\]) and a 10-event minimum. The regression LCSC is the one carried forward.

The per-well master table (*03_master_data.csv*, written by this block) is the single most consumed Script 03 output. Scripts 07, 08, 11, 16, 17, 19, and 21 all read it.

**Centroid headline fits --- ***centroid_headline_fits***.** This is the canonical Table 3 result. Each cluster centroid is fitted with *lag = HEADLINE_LAG = 0* and *window = None* --- the full record, not the 100-month window used by per-well fits. The reasoning for using the full record at cluster level is that the centroid already averages over within-cluster noise, and the longer window simply tightens the standard errors. LCSC is computed as *100 / β₁* (in mm per 10 cm of rise; F.4 explains the unit). *assert_physical_signs()* is called on each centroid fit and accumulates hard violations (β₁ ≤ 0, β₂ ≤ 0) and soft warnings (β₃ ≤ 0). Under the live data, no violations or warnings fire: all five clusters return positive β₁, β₂, β₃ with vanishingly small p-values (β₁ p ≪ 10⁻⁴⁵ everywhere; β₃ p ranges from 6×10⁻³⁵ for C1 down to 1.7×10⁻³ for C4, the weakest case).

The cluster-centroid coefficients under the live partition are:

  ----------------------- ----- ------ ------ ------- ------- ------
  Cluster                 n     β₁     β₂     β₃      R²      LCSC
  C1 (Lake Edge)          237   4.58   0.92   0.089   0.732   21.8
  C2 (Dune)               248   3.97   1.74   0.064   0.747   25.2
  C3 (Western Residual)   249   3.57   1.81   0.057   0.812   28.0
  C4 (Main Forest)        237   2.48   2.56   0.018   0.722   40.4
  C5 (Coastal Forest)     239   2.43   1.27   0.045   0.683   41.2
  ----------------------- ----- ------ ------ ------- ------- ------

These are read directly from *03_03_cluster_mechanistic_coefficients.csv*. The triplet plus LCSC is the "mechanistic signature" of each cluster.

**Interpolated-row handling.** *build_ssm_frame()* and *fit_ssm()* accept optional *provenance=* and *exclude_interpolated=* kwargs (see S.1 for the underlying provenance file). The Script 03 canonical fits are run with the default *exclude_interpolated=False*: every monthly row from *01_wells_clean.csv* enters the design matrix, regardless of whether the underlying cell is measured or interpolated. The canonical fit retains all rows rather than restricting to a measured-only characterization; the *exclude_interpolated=True* path is the documented sensitivity (next paragraph). The cluster-centroid coefficient table above is computed from *01_wells_clean.csv* under the *clean_well_series* interpolation *limit=1* policy (S.1). The interpolated-cell footprint is small: aggregated over each cluster's full member panel, the interpolated cell fraction is 1.3--1.6 % per cluster (22 cells in C1's 7-well × 250-month panel, 88 in C2's 25-well × 250-month panel, 73 in C3, 31 in C4, 16 in C5); the SSM aggregates over hundreds of monthly rows per cluster and is correspondingly robust to this footprint. The interpolation *limit* setting affects the centroid coefficients only at the second decimal, and no cluster changes rank, sign, or mechanistic signature: the LCSC ordering C1 \< C2 \< C3 \< C4 \< C5 and the forest-versus-open-dune β₂ contrast are insensitive to it.

The *exclude_interpolated=True* path is the documented sensitivity. A caller that wishes to refit the cluster centroid SSM on measured-only rows can pass the provenance series (loaded from *01_wells_provenance.csv*) alongside the cleaned centroid: *fit_ssm(h_centroid, climate, provenance=cluster_provenance, exclude_interpolated=True)* will drop any month in which the centroid cell was produced by interpolation. The chapter does not run this sensitivity. The provenance-aware path is consumed elsewhere in the pipeline --- Script 10d (clearfell summer minima) and Script 09c (scraping summer minima) apply a related *min_measured=2* rule per (well, year); see S.6 and S.7 for those consequences. Within Script 03, the sensitivity remains an on-demand check that future investigators can run against the published coefficient table.

**The LCSC.** LCSC = 100 / β₁. Interpreted as the number of millimetres of rainfall required to raise the water table by 10 cm at the cluster centroid. A cluster with LCSC = 21.8 (C1) takes 21.8 mm of rainfall to raise its water table 10 cm; a cluster with LCSC = 41.2 (C5) takes nearly twice that. The framing reverses β₁'s direction so that *larger numbers mean less responsive water tables* --- easier to communicate to a non-modeller audience than the bare β₁. The name "Lumped Catchment Storage Coefficient" was chosen because LCSC = 100 / β₁ is dimensionally equivalent to an effective lumped storativity multiplied by 100 (loosely: how many tens of millimetres of rain end up in storage per millimetre of head rise, expressed as a percentage). The construct is introduced for the first time in this script; every subsequent chapter that cites a cluster's "recharge responsiveness" is referring to LCSC.

**Lag diagnostic --- ***lag_diagnostic***.** Each cluster centroid is refitted at rainfall lags 0, 1, 2, 3 months. The result is a 5 × 4 grid of fits (*03_04_lag_diagnostic.csv*). The diagnostic is not a model-selection step --- *HEADLINE_LAG* is fixed in *config.py* --- but it is a check that the bucketing-fix-era data (F.2) actually places the rainfall--response pairing where it belongs. Under the live data, **all five clusters maximize R² at lag 0**: C1's R² drops from 0.732 at lag 0 to 0.037 at lag 1, C2 from 0.747 to 0.137, C3 from 0.812 to 0.196, C4 from 0.722 to 0.416, C5 from 0.683 to 0.217. At lag 3 the β₁ sign goes wrong for three of five clusters. This confirms the F.2 reasoning: once Script 01 buckets readings by field convention, current-month rainfall is the right predictor.

Bootstrap --- bootstrap_centroid_fits. For each cluster, draw n_members wells with replacement, build the centroid over that resample, refit fit_ssm(). Repeat N_BOOTSTRAP = 1000 times with BOOTSTRAP_SEED = 20260424. The replicates yield a distribution per cluster from which 2.5 % and 97.5 % percentile CIs are computed for β₁, β₂, β₃, R², and LCSC, plus the fraction of replicates with β₁ &gt; 0. The well-level (not month-level) resample is deliberate: the question being asked is how sensitive is the cluster β estimate to which wells happen to be in the cluster? --- not how sensitive is a single well's β to which months are observed? The latter is the per-well CI question that the OLS p-values already answer --- a validity confirmed for the reference network by the residual serial-correlation and HAC check in §S.16 (Script 22, 22_05_ssm_residual_autocorrelation.csv). Under the live data, all five clusters' β₁ CIs are comfortably positive (β₁ frac positive = 1.000 in every cluster), the CIs are narrow (C1: 4.25--4.93; C5: 2.20--2.65), and the bootstrap β median is within 1.3 % of the centroid headline β₁ everywhere (the largest gap is C4 at 1.2 %; the other four clusters are within 0.4 %). The bootstrap output is also the source of the error bars on 03_01_mechanistic_signatures.png.

**Leave-one-out --- ***leave_one_out_fits***.** For each cluster with ≥ 4 members, remove each well in turn, refit the centroid SSM on the remaining members. Useful for spotting clusters dominated by a single well. The full table is *03_06_leave_one_out.csv*. Under the live data, no cluster shows catastrophic single-well dependence: leaving out any single well moves the centroid β₁ by at most \~ 6 % of the headline. In C4 Main Forest the two wells that most improve the centroid fit on removal are CEH14 and CEH13 --- the cluster's two anomalous forest-margin wells (CEH14 returns a physically inadmissible drainage coefficient and fails the single-equation SSM; CEH13's β₃ is effectively zero). Dropping CEH14 lifts R² from 0.722 to 0.737 (+0.015) and dropping CEH13 to 0.729 (+0.007) --- the two largest R² recoveries in the C4 sweep. Both are poorly described by the single-equation SSM, so removing them tightens the centroid toward the rest of the cluster. NW10 produces the largest single β₁ shift (2.48 → 2.36 on removal) but lowers R² rather than raising it, so it is not treated as an over-influential outlier. C5 Coastal Forest shows a comparable β₁ LOO width (2.35--2.56 against C4's 2.36--2.57).

**C1 split-window --- ***c1_split_window_diagnostic***.** C1 Lake Edge underwent a regime change in 2018 --- the Llyn Rhos-Ddu drawdown event reset the lake stage that buffers most of the cluster. The split-window diagnostic refits the C1 centroid separately on the pre- and post-2018 sub-windows, and bootstraps each side by well-resampling. Under the live data the two windows do not produce overlapping β CIs: pre-2018 β₁ is 4.36 (CI 4.07--4.64), post-2018 β₁ is 4.93 (CI 4.47--5.40) --- the centroid responds more strongly to rainfall in the post-drawdown regime, consistent with a lake that no longer absorbs the rainfall pulse before it reaches the dipwell network. β₃ also shifts (0.080 pre, 0.104 post), suggesting drainage now operates against a less-buffered head. The two β₂ envelopes are also distinguishable (1.23 pre, 0.55 post) but with wider CIs. The headline cluster β values average over both regimes; the split-window result is a flag in the limitations section, not a recommendation to abandon the single-fit cluster characterization.

**Datum sensitivity (cluster-centroid) --- ***datum_sensitivity_analysis***.** The methodologically important piece. The drainage-datum sweep runs *drainage_datum* from 0.5 m to 8.0 m in 0.1 m steps, refitting all five centroids at each step. Two thresholds frame the result. The *first* is the minimum depth at which all five clusters simultaneously produce β₃ \> 0 with p \< 0.05 --- under the live data this is **1.5 m**, limited by C4 Main Forest, whose β₃ p-value crosses into significance there (p = 0.044 at 1.5 m; the criterion fails at 1.4 m, p = 0.065). The *second* is whether the datum that delivers that empirical minimum is the right one to use. It is not. At 1.5 m, C4's β₃ identification is right at the significance boundary; going deeper to 3.7 m drops C4's β₃ p-value from 0.044 to 0.0017 --- a roughly twenty-six-fold improvement in significance --- and lifts its R² by +0.007. C5 Coastal Forest gains too (β₃ p from 1×10⁻¹⁰ to 2×10⁻¹⁶, R² +0.037). The cost is borne by the well-determined eastern clusters: C1 Lake Edge loses 0.059 in R² and C2 Dune loses 0.032. But C1 and C2 are nowhere near the significance boundary at either depth --- their β₃ p-values stay around 10⁻³⁵ and 10⁻²⁵ respectively. C3 is essentially indifferent (ΔR² ≈ 0.000).

3.7 m therefore reflects a deliberate trade: a small amount of fit at the eastern clusters, where β₃ is over-determined, exchanged for substantially better β₃ identification at the two forest clusters, where it is hardest to pin down. The value also aligns with the Script 16 water-balance sensitivity analysis, which matters because consistent datum across the pipeline keeps the displacement reference comparable between the SSM coefficient fits and the water-balance arithmetic. β₁ is near-invariant in this sweep; β₂ and β₃ both shift with the datum, trading against one another in carrying the loss budget while β₃ preserves its sign and physical interpretation --- the regime reading of this trade is documented in F.3 and in the datum-regime diagnostic (03_12). The three-panel sensitivity figure (*03_08_datum_sensitivity.png*) shows β₃ vs reference depth (top), R² vs reference depth (middle), and aggregate R² + AIC vs reference depth (bottom). The "all β₃ \> 0 & sig" band is shaded green across each axis; the canonical 3.7 m sits inside the band rather than at its edge. This is the diagnostic that lets a reader satisfy themselves that the datum choice has been made with the trade-off explicit rather than tuned to a single optimum.

**Datum sensitivity (per-well) --- ***well_datum_sensitivity***.** The same sweep, applied to each well individually (66 × 76 = 5,016 fits). For each well three optima are recorded: the *primary* optimal datum (minimum depth at which β₃ \> 0 and p \< 0.05), the *secondary* optimal datum (minimum depth at which β₃ \> 0 with any p), and the *R²-maximizing* datum (highest R² across the sweep, regardless of β₃ sign). The full sweep is *03_09_well_datum_sensitivity.csv*; the per-well optima with their β coefficients are *03_09_well_optimal_datums.csv*. The motivation: under a uniform 3.7 m datum, the headline β₃ values are all positive and significant, but the optimum at any individual well may differ. The per-well sweep makes the local optimum visible.

Under the live data, the per-well primary optima are mostly pinned at the lower bound of the sweep (0.5 m) for C1, C2, and C3 wells --- meaning the data alone do not require a deep datum at these wells, but they tolerate one without breaking sign. The more informative diagnostic is the *R²-maximizing* datum, whose per-cluster medians are: C1 ≈ 0.8 m, C2 ≈ 0.9 m, C5 ≈ 1.9 m, C3 ≈ 1.6 m, C4 ≈ 2.7 m. The eastern lake-adjacent and dune wells optimize at shallow datums; the forest and coastal-forest clusters at deeper ones. The pattern is loosely consistent with a deepening effective drainage base from lake margin to dune interior, and is shown spatially by *03_10_well_datum_r2max_map.png*. The R²-gain map (*03_10_well_r2_gain_map.png*) makes visible the cost of using a uniform datum: the network mean R² gain from per-well optimisation over the uniform 3.7 m is +0.028, ranging from +0.001 at C4 (almost no penalty) to +0.069 at C1 (the cluster most penalised by the uniform datum). A reader who wants the deepest per-well fit can read it off *03_09_well_optimal_datums.csv*; the uniform-datum work is the report's headline.

Six of 66 wells never achieve β₃ \> 0 with p \< 0.05 at any datum in the sweep --- these are the wells at which the SSM's drainage term cannot be cleanly identified. They are routed into the spatial analysis (Scripts 07, 08) where their uncertainty is shown rather than hidden.

**Spatial datum maps --- ***make_well_datum_maps***.** *plot_metric_map* from *map_utils* (F.5) produces two publication-quality spatial maps: per-well R²-maximizing datum and per-well R²-gain over the uniform datum. DEM background, KML overlays (*Features.kml*, *streams.kml*, *clearfell.kml*), cluster-shape markers from *config.CLUSTER_MARKERS*, dual colorbars, legend --- all the standard rendering described in F.5. These are the only spatial maps Script 03 produces; per-well β maps are Script 07's job.

**Summary table and signatures figure --- ***build_summary_table***, ***make_signatures_figure***.** The summary table merges the centroid mechanistic coefficients with the bootstrap CIs and an amplitude-heterogeneity flag (which loads from Script 02's *02_08_cluster_amplitude_per_well.csv* if present, with a hard-coded fallback). The amplitude flag is a heuristic: a cluster is flagged "heterogeneous" if the post-2018 ratio of its highest to lowest per-well *p90 − p10* amplitude exceeds 1.5. The flag drives no analytical choice --- it is a reader-facing diagnostic. The three-panel signatures figure (*03_01_mechanistic_signatures.png*) is the bar chart of β₁, β₂, β₃ per cluster with bootstrap error bars, a pipeline diagnostic not published in the main report.

**Regional-average exports --- ***export_regional_averages***, ***export_regional_averages_maod***, ***export_cluster_peak_months***.** Three files for downstream consumption: the cluster-centroid hydrograph in depth-below-ground (*03_regional_averages.csv*), the same in m AOD (*03_regional_averages_maod.csv*), and a one-row-per-cluster table of the calendar month in which the centroid's long-term mean depth is shallowest (*03_cluster_peak_months.csv*). The peak-month table is the forecasting-horizon endpoint used by Script 11 and 11b --- the canonical "when in the year is the cluster's water table at its annual peak?".

### []{#anchor-119}[]{#anchor-120}[]{#anchor-121}Site-specific choices and rationale

-   Cluster centroid as arithmetic mean of member wells. The simplest defensible aggregation. Median, record-length-weighted mean, and PCA-derived centroids were all considered during the rebuild and rejected as adding complexity without measurable benefit on this dataset --- the within-cluster amplitude distributions are well-behaved enough that the mean is not pulled around by outliers.
-   *window = LCSC_DATA_LIMIT = 100*\*\* for per-well fits; ***window = None*** (full record) for centroid fits.\*\* The two-window design reflects the two different purposes. Per-well fits feed the spatial coefficient maps (Script 07), which inherit them unchanged, and the LCSC benchmarking (Script 08), which refits on the same most-recent 100-month window, so that what both show is contemporary behaviour rather than a long-term average. Cluster centroid fits feed the report's mechanistic table and the forecasting work, where the longest possible record tightens the standard errors and captures behaviour across the full instrumental period. The 100-month window choice itself was made to align with the LCSC analysis in the report (Section 3.3.1).
-   *MIN_OBS_PER_WELL = 30***.** Standard minimum for a no-intercept OLS fit on first differences. Below 30 aligned rows the per-well coefficient CIs widen sharply and the β estimates are dominated by noise. Both this constant and *model_utils*' *MIN_OBS* are aliases of *SSM_MIN_OBS* in *config.py*, so the per-well minimum is declared once. Script 03 passes *MIN_OBS_PER_WELL* explicitly through to *fit_ssm()* at every per-well call site (per_well_fits, well_datum_sensitivity, leave_one_out_fits), so changing the Script 03 value is the right way to retune the per-well minimum if needed.
-   Bootstrap resamples wells, not months. N_BOOTSTRAP = 1000 replicates draw the cluster's member wells with replacement, build the centroid over the resample, and refit. This matches the question being asked: how sensitive is the cluster β estimate to which wells happen to make up the cluster? --- not the per-well-monthly-noise question that the OLS standard error already answers (its serial-correlation validity is confirmed in §S.16, Script 22). BOOTSTRAP_SEED = 20260424 fixes reproducibility.
-   **The lag diagnostic refits at lags 0--3 regardless of ***HEADLINE_LAG***.** Diagnostic, not model-selection. Under the live bucketing-fix-era data, all five clusters maximize R² at lag 0 and the headline value is correct. The diagnostic is preserved because (i) the bucketing fix is recent enough that the reader may legitimately want to satisfy themselves the headline lag is right, and (ii) a future data update that drifted the bucketing could in principle reintroduce a lag signal; the diagnostic catches that.
-   **Datum sweep 0.5--8.0 m in 0.1 m steps; canonical value 3.7 m.** 76 depths × 5 clusters = 380 fits at the centroid level (fast); 76 × 66 = 5,016 fits at the per-well level (a few minutes on a current laptop). 0.5 m is the shallowest depth where the dune-slack record contains any meaningful headroom above the datum; 8.0 m is comfortably below any plausible drainage base. The canonical 3.7 m value sits above the live empirical minimum (1.7 m, at which all five clusters first simultaneously satisfy β₃ \> 0 with p \< 0.05). Going from 1.7 m to 3.7 m takes the two forest clusters from β₃ identification near the significance edge (C4 p = 0.022 at 1.7 m) to comfortably-determined fits (C4 p = 0.0017, C5 p = 10⁻¹⁶), at the cost of a small R² penalty at the two clusters where β₃ is over-determined (C1 ΔR² = −0.059, C2 ΔR² = −0.032); C1 and C2 stay astronomically significant on β₃ at either depth. 3.7 m also aligns with the Script 16 water-balance sensitivity analysis, where downstream consistency matters. β₁ is near-invariant in this sweep; β₂ and β₃ both shift with the datum, trading against one another in carrying the loss budget while β₃ preserves its sign and physical interpretation --- the regime reading of this trade is documented in F.3 and in the datum-regime diagnostic (03_12).
-   **C1 split at 2018-01-01.** Chosen because the post-2018 amplitude analysis (Script 02) showed that four of seven C1 wells had post-2018 *p90 − p10* ranges meaningfully wider than their pre-2018 values, *even after climate normalization* --- i.e. a structural change in cluster behaviour rather than a climate forcing effect. The Llyn Rhos-Ddu drawdown event provides the physical mechanism. The split-window diagnostic tests whether the change shows up in the β coefficients (it does), and the analysis is preserved as a known caveat rather than as a recommendation to fit two separate C1 models.
-   **Sign violations halt the pipeline only at the *****centroid***\*\* level, and only \*\*\*\*\*after\*\*\*\*\* the diagnostic outputs are saved.\*\* A failing centroid fit is the only kind that propagates into the report's headline values. The decision to defer the halt until after the diagnostic tables and the signatures figure are written is deliberate: the LOO, bootstrap, and datum-sensitivity outputs are exactly the diagnostics an investigator needs to understand the failure. Halting before they are saved would give the user a stack trace and no diagnostic context. Per-well sign violations are reported as console diagnostics; they may flag wells worth visiting in the spatial chapters but do not invalidate the broader analysis.

### []{#anchor-121}[]{#anchor-122}[]{#anchor-123}Outputs

  ---------------------------------------------------------------------------- -------------------------------------------------------------------------- --------------------------------------------------------------------------------
  Output file                                                                  Contents                                                                   Consumers
  *03_master_data.csv* (INT\_)                                                 Per-well β₁, β₂, β₃, p-values, R², n, LCSC, cluster ID, easting/northing   Scripts 07, 08, 11, 16, 17, 19, 21
  *03_regional_averages.csv* (INT\_)                                           Cluster-centroid monthly hydrographs (depth below ground) + P, PET in mm   Scripts 11, 16, 21
  *03_regional_averages_maod.csv* (INT\_)                                      Same in absolute m AOD                                                     Script 21 (forestry scenarios)
  *03_cluster_peak_months.csv* (INT\_)                                         Long-term mean peak month per cluster                                      Scripts 11, 11b
  03_state_space_model/03_01_mechanistic_signatures.png                        3-panel β bar chart with bootstrap CIs                                     Diagnostic / summary-document figure; not a numbered figure in the main report
  03_state_space_model/03_02_cluster_summary_table.csv                         Headline per-cluster summary with bootstrap CIs and amplitude flag         Report Table (supplementary)
  03_state_space_model/03_03_cluster_mechanistic_coefficients.csv              Centroid β coefficients with p-values, R², n, LCSC, datum                  Scripts 11, 11b, 16, 19, 21; Report Table 3
  03_state_space_model/03_04_lag_diagnostic.csv                                Centroid fits at lags 0--3 per cluster                                     Report §3.3
  03_state_space_model/03_05_bootstrap_ci.csv                                  Bootstrap median and 95 % CIs per cluster                                  Signatures figure error bars
  03_state_space_model/03_06_leave_one_out.csv                                 LOO centroid fits per cluster member                                       Report §3.3 / supplementary
  03_state_space_model/03_07_c1_split_window.csv                               C1 pre/post-2018 fits with bootstrap CIs                                   Report §4.2 (C1 caveat)
  03_state_space_model/03_08_datum_sensitivity.{csv,png}                       Cluster-level datum sweep                                                  Report §3.4
  03_state_space_model/03_12_partition_vs_datum.csv + 03_12_datum_regime.png   Datum-regime diagnostic (drainage-flux plateau + loss partition)           Supplementary Material Note S9
  03_state_space_model/03_09_well_datum_sensitivity.csv                        Per-well datum sweep (5,016 fits)                                          Report §3.4
  03_state_space_model/03_09_well_optimal_datums.{csv,png}                     Per-well primary, secondary, R²-max datum + β at each                      Report §3.4
  03_state_space_model/03_10_well_datum_r2max_map.png                          Spatial map of per-well R²-maximizing datum                                Report Figure (§3.4)
  03_state_space_model/03_10_well_r2_gain_map.png                              Spatial map of R² gain vs uniform datum                                    Report Figure (§3.4)
  ---------------------------------------------------------------------------- -------------------------------------------------------------------------- --------------------------------------------------------------------------------

All paths resolve through *utils/paths.py* (*INT_MASTER_DATA*, *INT_REGIONAL_AVG*, *INT_CLUSTER_AVG_MAOD*, *INT_CLUSTER_PEAK_MONTHS*, *OUT_03\_\**, *DIR_03*).

### []{#anchor-123}[]{#anchor-124}[]{#anchor-125}Limitations and known caveats

-   **The fitted β values are reliable for ranking clusters, not for quantifying absolute flux magnitudes.** The OLS estimator applied to a lumped monthly model carries two structural biases that inflate the absolute coefficient values: (i) collinearity between monthly P and PET inflates both β₁ and β₂ simultaneously, producing an upward bias whose magnitude cannot be recovered from the regression alone; (ii) the monthly climate regressors are area-averages over a spatially heterogeneous forcing field --- a form of errors-in-variables that further biases β away from the true site-scale coefficients. The net effect is that β₁, β₂, and β₃ as reported in Table 3 are biased somewhat high in absolute terms. The cluster contrasts --- C4 β₂ \> C5 β₂ \> C3 β₂; the open-dune β₁ gradient C1 \> C2 \> C3 --- are robust ordinal findings. Statements such as "the C4 forest cluster intercepts 2.55 m of water-table head per metre of PET" are not warranted; statements such as "C4 has a higher atmospheric draw coefficient than any open-dune cluster" are. Any downstream analysis that converts β values to volumetric fluxes (Scripts 16, 19, 21) should be read with this caveat in mind: the absolute magnitudes carry the OLS bias, so the scenario comparisons are relative rather than calibrated.
-   **The SSM is a single-equation model.** It is a lumped decomposition of Δh into rainfall, PET, and drainage contributions. It does not represent boundary-layer hydraulics, lateral subsidies (ridge recharge into C4, lake exchange at C1), tidal couplings, or non-stationary effects (coastal retreat at C5). Where any of these matter for the science, they appear as systematic residuals diagnosed downstream --- Scripts 22 (residual lag structure), 23 (ridge recharge), 24 (residual seasonality), and 25 (coastal gradient).
-   **The centroid averages over within-cluster heterogeneity.** Where a cluster contains wells with very different mean amplitudes --- notably C4, which includes CEH14 on the ridge flank --- the centroid coefficients describe the cluster mean rather than any single well. The leave-one-out output makes the well-by-well sensitivity visible; the heterogeneity flag in the summary table flags clusters where the within-cluster range exceeds a 1.5× ratio.
-   **C1 Lake Edge changed regime in 2018.** The pre/post-split-window diagnostic shows non-overlapping β CIs across both windows. The single-fit C1 cluster characterization in Table 3 is the average across both regimes. Where C1 results are quoted in the main report, the split-window outcome should be cited alongside as a caveat.
-   **Per-well fits at the network edges have small n.** Wells with \~30--50 valid rows produce β with wide CIs. Six wells in the live network never achieve β₃ \> 0 with p \< 0.05 at any datum in the sweep. Per-well coefficient maps in Script 07 annotate uncertainty so the reader can distinguish robust spatial structure from sample-size artefacts.
-   **The uniform 3.7 m datum is a deliberate trade, not an empirical optimum.** It sits above the live empirical minimum (1.5 m) and is the value at which the two forest clusters' β₃ identification is comfortably significant rather than near the threshold. The cost of going to 3.7 m rather than staying at the empirical minimum is an R² reduction of −0.059 at C1 Lake Edge and −0.032 at C2 Dune, both of which remain astronomically significant on β₃ regardless of depth. The benefit is a roughly twenty-six-fold improvement in C4 β₃ significance and substantially better fit at C5. For cluster-level work the uniform 3.7 m is the right choice; for any single-well question the per-well datum outputs (*03_09_well_optimal_datums.csv*) should be consulted --- the mean network R² penalty from using the uniform datum at every well, rather than the per-well R²-maximizing value, is +0.028 across the network, heaviest at C1 Lake Edge (+0.069) and lightest at C4 Main Forest (+0.001).
-   **C4 Main Forest has the weakest β₃ identification of the five clusters.** Even at the canonical 3.7 m datum, C4's β₃ p-value (0.0016) is several orders of magnitude larger than the other four clusters' (which sit at 10⁻¹⁶ to 10⁻³⁵). The datum choice was deliberately set deeper than the empirical minimum to move C4 away from the significance boundary, and the move worked --- but C4 remains the cluster where the SSM most underdescribes the local hydrology. CEH14 carries a head-dependent term the three-term SSM does not represent; lateral recharge from the bedrock ridge is one candidate mechanism, and the diagnostics that bear on it are in S.16.

### []{#anchor-125}[]{#anchor-126}[]{#anchor-127}Where the result appears in the report

-   §3.3 *State-space regression* --- methodology.
-   §3.4 *Drainage datum sensitivity* --- *03_08_datum_sensitivity.png* and the per-well sensitivity discussion.
-   Table 3 --- cluster mechanistic coefficients (from *03_03_cluster_mechanistic_coefficients.csv*).
-   *03_01_mechanistic_signatures.png* (cluster β bar chart) --- a diagnostic figure used in the summary documents; not a numbered figure in the main report (the report's Figure 9 is the cluster hydrographs).
-   §4.2 --- cluster characterization, drawing on the LCSC values and the cluster-mean signatures.
-   §4.9.2 / Figure 48b --- per-well β₁ map (Script 07 produces; values come from *03_master_data.csv*).
-   §4.2 *C1 caveat* --- *03_07_c1_split_window.csv*.
-   Subsequent §4 and §5 sections --- implicit, in every analysis that reads SSM outputs.

### []{#anchor-127}[]{#anchor-128}[]{#anchor-129}Cross-references

-   **F.3** --- the full SSM specification (equation, displacement formulation, sign conventions, drainage datum rationale, *model_utils.fit_ssm()* interface). Refer to F.3 throughout rather than re-deriving.
-   **F.4** --- the k=5 partition that the centroids and per-well fits use; per-cluster member counts (C1=7, C2=26, C3=19, C4=9, C5=5; n=66 total).
-   **F.5** --- *model_utils.py*, *paths.py*, and *map_utils.py* module roles.
-   **S.1** --- input data preparation; upstand source; reference-network membership; *01_wells_provenance.csv* (the optional input consumed when *exclude_interpolated=True* is invoked).
-   **S.2** --- cluster partition that defines the centroids; amplitude descriptors that feed the heterogeneity flag in *03_02_cluster_summary_table.csv*.
-   **S.7** --- spatial per-well coefficient maps that consume *03_master_data.csv*.
-   **S.8** --- LCSC vs Traditional Linear Model benchmarking.
-   **S.9** --- forecasting thresholds that consume *03_03_cluster_mechanistic_coefficients.csv* and *03_cluster_peak_months.csv*.
-   **S.16** --- supplementary diagnostics that pick up the systematic SSM residuals (the unresolved C4/CEH14 residual, residual seasonality).

# []{#anchor-129}[]{#anchor-130}[]{#anchor-131}Phase 2 --- Pearson Membership Audit

## []{#anchor-131}[]{#anchor-132}[]{#anchor-133}S.4 Scripts 04, 05, 06 --- Cluster visualization and Pearson affinity audits

Steps 4--6 / 27. Phase 2.

### []{#anchor-133}[]{#anchor-134}[]{#anchor-135}Motivation (chapter-level)

Phase 2 answers two related questions that Phase 1 leaves open. First, where in the warren does each of the five behavioural clusters actually sit on the ground --- what does the partition look like as a map rather than a dendrogram? Script 04 produces the orientation figure. Second, how confidently is each well in the cluster the partition has placed it in, and how should the \~22 extended-network wells (FE1--4, LIS1, the demoted CEH wells, and the perimeter *p\** wells) be slotted into the same five-cluster scheme when they were not part of Ward's input? Scripts 05 and 06 are the confidence-quantification layer: per-well Pearson correlations against the five cluster centroids, gap statistics between best-match and runner-up, and a status flag that separates wells comfortably inside their cluster from wells on the boundary. The three scripts are grouped here because together they form a coherent visualization-and-audit package consumed in §4.2 and §4.3 of the main report. Script 04 visualises the partition; Scripts 05 and 06 quantify how strong the partition's claim on each well actually is.

The methodology shared by Scripts 05 and 06 --- z-score each well's depth series before correlating, build cluster centroids as the mean of the z-scored member series, compute Pearson correlation against each centroid, gap = best − second-best --- is described once at the chapter level and not repeated in the two sub-sections. The cluster-identity conventions (IDs 1--5, labels, colours, markers) are inherited from F.4 and not re-derived.

### []{#anchor-135}[]{#anchor-136}[]{#anchor-137}Sub-script 04 --- Cluster orientation map (*04_cluster_visualisations.py*)

#### []{#anchor-137}[]{#anchor-138}Motivation

A single publication-quality map showing the five-cluster partition of the reference network on the Newborough Warren DEM, with each well as a cluster-coloured, cluster-shaped marker against the site's hydrological features (lake, streams, clearfell footprint). It is an orientation figure, not an analytical output: it carries no numbers, only the spatial arrangement of cluster membership that all subsequent spatial work assumes the reader has internalised.

#### []{#anchor-138}[]{#anchor-139}Inputs

  ----------------------------------------------------- ----------------------------------------------------------
  Input file                                            Description
  02_cluster_stats.csv                                  Per-well cluster assignment (Script 02)
  01_locations.csv                                      Easting, northing, ground elevation per well (Script 01)
  *data/Features.kml*, *streams.kml*, *clearfell.kml*   Site GIS overlays
  data/newborough_dem.tif                               Coloured terrain background
  ----------------------------------------------------- ----------------------------------------------------------

#### []{#anchor-139}[]{#anchor-140}Methodology

The script is 77 lines and does one thing: it joins *02_cluster_stats.csv* to *01_locations.csv* on the normalized well name (*data_utils.normalize_well_name()*), extracts the integer cluster ID from the *Cluster* column (via *cluster_id_from_value()* to tolerate either *\"C3\"* or *3* formats from upstream), and plots each well as a *matplotlib.pyplot.scatter* point. The DEM is loaded by *map_utils.load_dem_layer()*; the three KML overlays are added by *map_utils.add_kml_features()*. If the DEM file is not available, *map_utils.add_osm_basemap()* provides an OpenStreetMap fallback so the figure remains plottable in environments without the GIS data files. Each cluster's marker shape comes from *config.CLUSTER_MARKERS* (circle for C1, square for C2, triangle for C3, diamond for C4, plus for C5; see F.4) and its colour from *config.CLUSTER_COLOURS*. Well labels are placed by *adjustText* to minimize overlap, with thin black callout lines where the algorithm has had to move a label far from its point. The map extent is fixed at easting 240,100--243,900 and northing 362,200--365,800 (British National Grid, EPSG:27700) and the axes are forced to equal aspect so distances on the map are isotropic. The figure is rendered at 300 dpi and written to *04_01_core_architecture_map.png*.

The reference network only (66 wells) is plotted --- the extended-network wells appear on Script 06's integration map instead. Two legends are placed in opposite corners: cluster assignments in the lower left and KML site features (lake outline, stream, clearfell polygon) in the upper right. When the script runs in greyscale mode (*BW_MODE = True*), the DEM colour bar is suppressed because the underlying greyscale DEM raster does not carry a meaningful colour mapping; the cluster colours fall back to *CLUSTER_COLOURS_BW* via the same identity-keyed lookup, so the figure remains legible without colour.

#### []{#anchor-140}[]{#anchor-141}Outputs

  ----------------------------------------------------------- ---------------------------------------- ------------------------------------------
  Output                                                      Description                              Report reference
  04_cluster_visualisations/04_01_core_architecture_map.png   Spatial cluster map, reference network   Report Figure (§4.2 cluster orientation)
  ----------------------------------------------------------- ---------------------------------------- ------------------------------------------

### []{#anchor-141}[]{#anchor-142}[]{#anchor-143}Sub-script 05 --- Pearson affinity (reference network, *05_pearson_affinity.py*)

#### []{#anchor-143}[]{#anchor-144}Motivation

For each of the 66 reference-network wells, Ward's clustering has produced a cluster assignment; the question Script 05 answers is *how confidently does that assignment sit*. Two wells in the same cluster can have very different relationships to the cluster's centroid --- one might be a tight match, another might correlate almost as strongly with a neighbouring cluster. The Pearson affinity audit computes the gap between best-match and assigned-cluster correlation for every well and produces a four-way status classification: Core (best-match = assigned, comfortable margin), Fuzzy (best-match = assigned but small margin), Spy (best-match ≠ assigned --- Ward's and Pearson disagree), and Unclassified (insufficient data to compute a correlation). The output is read by Scripts 11b (spatial threshold maps) and indirectly underpins the per-well confidence rendering on subsequent spatial figures.

#### []{#anchor-144}[]{#anchor-145}Inputs

  ---------------------- -----------------------------------------
  Input file             Description
  01_wells_clean.csv     Cleaned depth time series (Script 01)
  02_cluster_stats.csv   Per-well cluster assignment (Script 02)
  01_locations.csv       Easting, northing per well (Script 01)
  ---------------------- -----------------------------------------

#### []{#anchor-145}[]{#anchor-146}Methodology

The script is 259 lines. After loading the wells matrix and reducing it to the 66 reference-network wells named in *02_cluster_stats.csv*, it z-scores each well's depth series row-wise (*zscore_rows*) and builds five cluster centroids as the row-mean of the z-scored member series per cluster (*build_centroids*). Z-scoring per well, before averaging, is the operative choice: it removes each well's mean depth and amplitude so the resulting correlations are sensitive to *shape* (when the well rises and falls, relative to the rest of the cluster) rather than *level* (how deep below ground its mean sits). The standard deviation uses *ddof=0* (population formula), consistent with the bootstrap convention used in Script 02 and Script 03.

For every well, the script then computes a Pearson correlation against each of the five z-scored centroids via *safe_pearson()*, which requires at least 24 paired non-missing observations and returns NaN if either series is constant over the overlap window. The 24-month minimum matches the *MIN_EXTENDED_MONTHS* threshold used by Script 01 to admit an extended-network well --- a well that did not produce enough data to be admitted to the network has no business producing a Pearson value here either. Reference-network wells comfortably exceed this minimum, so the threshold is in practice operative only for Script 06's extended-network rows.

The classification step is in *classify()*. For each well, the assigned-cluster correlation is read from the corresponding *Cluster_n* column; the best-match cluster is whichever has the highest valid correlation; the gap is best-match minus the highest *other* (non-assigned) correlation. A well where best-match ≠ assigned is labelled *Spy*; a well where best-match = assigned and the gap exceeds 0.05 is *Core*; a well where best-match = assigned but the gap is at or below 0.05 is *Fuzzy*. The 0.05 threshold is hardcoded in *classify()* and reappears as *DELTA_THRESH = 0.05* at module scope in Script 06; in the current build the two are not linked, but the value is identical.

A secondary diagnostic --- the *Mean Cluster Affinity* (MCA) flag --- is computed separately. A well is MCA-flagged if three or more of its five cluster correlations exceed 0.90 (*MCA_Count_r_gt_0_90 \>= 3*). The label *MCA_Cluster_Label* records which three (e.g. *C2/C3/C5*). The flag identifies wells whose shape signature is so generic that several cluster centroids match it strongly --- typically wells in the central dune field where C1, C2, and C3 hydrographs all rise and fall in unison and the cluster boundary is a matter of mean depth and amplitude rather than shape. Under the live data, 46 of 66 reference wells are MCA-flagged, illustrating that the partition rests on dimensions other than month-to-month co-variation alone (notably mean depth and amplitude --- see F.4 on the no-detrending choice in Script 02).

Under the live partition, the audit table classifies 17 wells as Core, 46 as Fuzzy, and 3 as Spy: CEH4 (assigned C3, best-match C5, gap −0.0118), CEH21 (assigned C3, best-match C5, gap −0.0054), and NW13 (assigned C3, best-match C2, gap −0.0015). All three spies have margins of 0.012 or smaller, i.e. they sit on the C3 boundary with barely any preference between C3 and the neighbour Pearson picks. The spy flag is descriptive, not corrective --- Ward's centroid is built from *all* members and accounts for amplitude as well as shape, where Pearson on z-scored series sees only shape, so the two methods can disagree by tiny margins on boundary wells without either being wrong.

The script writes one CSV --- *05_pear_membership_audit.csv* (the *INT_PEAR_AUDIT* intermediate) --- containing the audit columns plus the five per-cluster Pearson values, the MCA flag, and the MCA cluster label. Two figures follow. The first is a bar chart of per-cluster Pearson values for an illustrative subset of reference wells --- one or two from each cluster --- that shows the five-bar affinity profile against all five centroids and is read as the per-well analogue of the cluster-centroid signature plots in Script 03 (*05_pear_02_affinity_chart_reference.png*). The second is a spatial confidence map (*05_pear_01_spatial_confidence_map.png*) with each well drawn at its location, coloured by its best-match cluster, with marker shape encoding status (Core=circle, Fuzzy=diamond, Spy=star); Fuzzy and Spy markers carry the secondary-cluster integer as a small overlay label so the reader can see which alternative the well is wavering toward. MCA-flagged wells receive an additional open black surround marker, with the surround shape encoding the specific MCA combination (e.g. *C2/C3/C5*), so the reader can see at a glance where in space each MCA pattern occurs. The DEM and KML overlays are loaded by the same *map_utils* helpers as Script 04.

#### []{#anchor-146}[]{#anchor-147}Site-specific choices and rationale

-   **Pearson, not Spearman or Kendall.** Ward's clustering in Script 02 uses correlation distance, *1 − ρ* (Pearson). Auditing the partition with a different correlation measure would mean Pearson set the partition and a non-Pearson statistic judged it --- an inconsistency that would muddy interpretation of any disagreement. Using the same coefficient closes that loop.
-   **Z-scored centroids; mean, not median.** The Script 03 SSM also fits to the mean centroid (F.3), so the audit's centroid construction matches the fitting convention. Shape-only comparison via z-scoring is consistent with the no-detrending choice in Script 02 (S.2): both the partition and the audit operate on the behavioural-pattern axis of "wells that rise and fall together", not on the absolute-depth axis.
-   **24-month minimum on the Pearson overlap.** Matches the extended-network admission threshold. A series shorter than two years cannot resolve an annual seasonal cycle reliably and the Pearson value against an annually-cycling centroid becomes a function of which months happen to be present.
-   **Gap threshold of 0.05 for Core vs Fuzzy.** Empirical, not principled --- chosen to separate the comfortable interior of each cluster (\~26% of reference wells) from the broad boundary band (\~70%). Sensitivity to this value is low: at 0.03 the Core count rises to the high thirties, at 0.10 it falls to a handful. The threshold's role is descriptive labelling, not gatekeeping.
-   **Three-cluster MCA threshold at r \> 0.90.** Identifies wells whose hydrograph correlates strongly with several cluster centroids --- a sign that month-to-month shape alone does not separate them from the alternatives, and the cluster boundary in their case rests on amplitude or mean depth. The threshold of 0.90 and the count of 3 are both empirical; together they pick out the central-dune wells whose generic seasonal cycle correlates well across most clusters.

#### []{#anchor-147}[]{#anchor-148}Outputs

  ------------------------------------------------------------- ----------------------------------------------------------------------------------- ----------------------------------------------------------
  Output                                                        Description                                                                         Reference
  *05_pear_membership_audit.csv* (INT)                          Per-well audit table (66 rows, 16 cols)                                             Scripts 11b, 18 (read indirectly via the sitewide audit)
  05_pearson_affinity/05_pear_02_affinity_chart_reference.png   Bar chart of per-cluster Pearson values for an illustrative reference-well subset   Report §4.3
  05_pearson_affinity/05_pear_01_spatial_confidence_map.png     Spatial map of best-match cluster + status                                          Report §4.3
  ------------------------------------------------------------- ----------------------------------------------------------------------------------- ----------------------------------------------------------

#### []{#anchor-148}[]{#anchor-149}Limitations

-   **Pearson similarity captures shape, not magnitude.** A well whose mean depth has drifted systematically from the cluster mean is not caught by the audit. The drift would show up as an amplitude or mean-shift difference between the well and the centroid, neither of which contributes to a Pearson value once both have been z-scored.
-   **A small gap is descriptive, not corrective.** A Fuzzy well, or even a Spy well with a 0.01 gap, is not misclassified by Ward's. It is a well that sits in transitional behavioural territory --- the cluster boundary is genuinely indistinct for it, and the audit reports that indistinctness rather than resolving it.
-   **MCA is descriptive of the *****common***\*\* behavioural signal.\*\* A high MCA count means the well's hydrograph is generic enough to track several centroids; it is not a partition criticism, because Ward's resolves these wells using the parts of the behaviour that *do* differ between clusters (amplitude, deep-summer minima, response timing at longer lags), which the z-scored Pearson does not see.

### []{#anchor-149}[]{#anchor-150}[]{#anchor-151}Sub-script 06 --- Pearson affinity (sitewide / extended, *06_pearson_extended.py*)

#### []{#anchor-151}[]{#anchor-152}Motivation

Script 05 audits the 66 reference-network wells. Script 06 extends the same logic to the full 88-well sitewide network --- the 66 reference wells plus 22 extended wells (FE1--4, LIS1, the demoted CEH wells with shorter records or singleton-outlier behaviour, and the perimeter p1/p2/pe/pw wells; Llyn Rhos-Ddu and *pdfs* are blacklisted upstream in Script 01). Extended-network wells were excluded from Ward's input by design, because either their records are too short to anchor a stable distance to the reference wells or, in the CEH3/CEH22 case, they carry a non-stationary signal (tidal contamination, S.1) that Ward's clustering would either ignore or distort. The Pearson audit gives each of them a cluster label retroactively: the cluster whose centroid their shape best matches, with the gap statistic carried alongside as a calibration of confidence. Downstream consumers --- Script 11b for spatial thresholds, Script 18 for WTF Sy interpolation --- read the sitewide audit and decide for themselves how much weight to give a Pearson-assigned well; Script 06 does not gate-keep.

#### []{#anchor-152}[]{#anchor-153}Inputs

  ------------------------ ---------------------------------------------------
  Input file               Description
  01_wells_reference.csv   Reference-network subset, 66 wells (Script 01)
  01_wells_extended.csv    Extended-network subset, 22 wells (Script 01)
  02_cluster_stats.csv     Reference-network cluster assignments (Script 02)
  01_locations.csv         Easting, northing per well (Script 01)
  ------------------------ ---------------------------------------------------

#### []{#anchor-153}[]{#anchor-154}Methodology

The script is 363 lines and follows the same shape as Script 05, with three differences that are worth pinning down.

First, the z-scoring is applied to the *combined* reference + extended series (*z_all = zscore_rows(pd.concat(\[ref_wells, ext_wells\]))*), and the reference centroids are then extracted from this combined matrix rather than z-scoring the reference set alone. In practice the two approaches give virtually identical centroids because each well is z-scored row-wise --- adding the extended wells to the matrix does not alter any reference well's own z-score. The construction is convenient rather than substantive: the extended wells need to be z-scored anyway, and doing it in a single call keeps the indexing simple.

Second, the classification has five status labels rather than four, because the network split is binary and not every status applies to both sides. Reference-network wells with a Ward's assignment can be *Ref_Core* (best-match = assigned, gap ≥ 0.05), *Ref_Fuzzy* (best-match = assigned, gap \< 0.05), or *Ref_Spy* (best-match ≠ assigned). Extended-network wells have no Ward's assignment to be a spy of and receive either *Ext_Core* (gap ≥ 0.05 against the best-match cluster) or *Ext_Fuzzy* (gap \< 0.05). The *DELTA_THRESH = 0.05* and *MCA_THRESH = 0.90* constants are exposed at module scope here, in contrast to Script 05 where the gap threshold is buried in the *classify()* function. The values are identical between the two scripts.

Third, the spatial output is an *integration map*, not a confidence map. Reference and extended wells share the same plot, distinguished by marker fill --- reference wells are filled in their best-match cluster colour (or dark grey in BW mode), extended wells are filled in light grey, and any well classified *Ref_Spy* is drawn with a white fill and a thickened black edge so the reader can see at a glance which Ward's assignments the Pearson audit disagrees with. Cluster identity is encoded by marker *shape* (the canonical *CLUSTER_MARKERS* from F.4), so colour is freed up to carry network-membership information without ambiguity. Well labels are placed by *adjustText* with the same offset-and-repel parameters tuned for the dense reference-network labelling. The audit-bar chart for the extended wells is the only figure that Script 06 produces with the reference wells absent --- bars for FE1--4, LIS1, the demoted CEHs, the p-wells, NW8/8b/12 --- and uses the same five-cluster colour palette so the reader can read off both the assignment and the runner-up at a glance.

Under the live data, all 22 extended-network wells receive a valid Pearson best-match --- there are no rows lost to the 24-month threshold. The status breakdown is 19 *Ext_Fuzzy* and 3 *Ext_Core*. The three Ext_Core wells are NW12 (best-match C4, gap 0.123), CEH3 (best-match C5, gap 0.175), and P2 (best-match C1, gap 0.112); each is well-separated from its neighbours and has a confident assignment. The 19 Ext_Fuzzy wells include all four FE clearfell wells (each assigned to either C4 or C5 with gaps under 0.04, consistent with their forest-margin location), LIS1 (best-match C4), and the perimeter wells (P1, PE, PW), which sit at best-match C2 or C3 with small gaps, indicating they lie on the eastern open-dune / western-residual boundary. CEH3 and CEH22 --- the two wells routed to the extended network on tidal-contamination grounds (S.1) --- receive different best-match clusters under the audit: CEH3 best-matches C5, the coastal-forest cluster whose reference members (CEH16, NW9) themselves carry a partial tidal signature, while CEH22 best-matches C2 by the narrowest of margins. CEH3 takes Ext_Core status (gap 0.175) because the C5 fit is unambiguous; CEH22 takes Ext_Fuzzy with a gap of 0.0011 --- among the smallest in the entire audit --- and a low best-match correlation (0.857), its tidal signature strong enough that it does not align cleanly with any one centroid shape. CEH22's near-tie sits between C2 and C5 (correlations within 0.001 of each other, with C3 a close third), so although the audit nominally assigns it to C2 the assignment carries essentially no behavioural preference; this near-indeterminacy, rather than the specific cluster label, is the informative result. Under the previous (*limit=3*) interpolation policy CEH22 best-matched C5; the *limit=1* change moved the cluster centroids slightly and flipped this coin-flip assignment --- expected behaviour for a well this marginal, not an instability in the partition. The *pdfs* well, which carried the lowest best-match correlation sitewide in earlier audits, no longer appears: it was added to *EXTENDED_NETWORK_BLACKLIST* in Script 01 on 2026-05-24 on tidal-influence grounds (S.1) and is removed before the extended-network CSV is written.

#### []{#anchor-154}[]{#anchor-155}Site-specific choices and rationale

-   **Reference centroids drive the audit; extended wells are not included in centroid construction.** A centroid built from short, possibly non-stationary records would carry exogenous variance into the cluster mean. The reference network is the authoritative behavioural definition, and extended wells are admitted only as evaluated objects, never as evaluators.
-   **No confidence threshold for assignment.** Every extended-network well receives a cluster label and a gap value; the downstream consumer decides what to do with the gap. Script 11b downweights Pearson-assigned wells in the spatial-threshold rendering; Script 18 treats them as supplementary in WTF Sy interpolation. Centralising the decision would force a one-size-fits-all gate where the downstream contexts require different ones.
-   **Llyn Rhos-Ddu and ***pdfs*\*\* are filtered upstream in Script 01.\*\* Reflected here only as an absence --- neither appears in any row of *06_pear_membership_audit_sitewide.csv* because Script 01's *EXTENDED_NETWORK_BLACKLIST = frozenset({\"llynrhos\", \"pdfs\"})* removes them before the extended-network CSV is written. The rationale is in S.1; the audit inherits the decision rather than re-evaluating it.
-   **Cluster identity by shape, not colour, on the integration map.** Network identity (reference vs extended vs spy) needs a separate channel from cluster identity, and humans read marker fill more reliably than marker shape. Putting cluster on shape and network on fill keeps the two readable simultaneously.

#### []{#anchor-155}[]{#anchor-156}Outputs

  ------------------------------------------------------------ -------------------------------------------- --------------------------
  Output                                                       Description                                  Reference
  *06_pear_membership_audit_sitewide.csv* (INT)                Sitewide per-well audit (89 rows, 14 cols)   Scripts 11b, 18
  06_pearson_extended/06_pear_01_affinity_chart_extended.png   Bar chart of extended-network affinities     Report §4.3
  06_pearson_extended/06_pear_02_integration_map.png           Sitewide integration map                     Report §4.3 (Figure 14b)
  ------------------------------------------------------------ -------------------------------------------- --------------------------

#### []{#anchor-156}[]{#anchor-157}Limitations

-   **Short overlap windows can produce misleading correlations.** A well with only 30 monthly observations against a centroid spanning the full reference window has limited statistical power; a chance alignment between an annual cycle and a short overlap can produce a high Pearson value that does not reflect long-term cluster fidelity. The 24-month minimum protects against the worst cases but does not eliminate the effect at the lower end. Consumers of the audit table can use the per-cluster *r_C\** columns and the gap to judge robustness on a case-by-case basis.
-   **Pearson best-match is not a substitute for Ward's clustering.** A well classified as C5 by Pearson with a 0.85 correlation and a 0.02 gap should not be treated, in mechanistic inference (SSM fits, water balance, scenario analysis), as a full member of C5 in the way that an Ward's-assigned reference well is. The audit table carries the values; the scientific call is downstream.
-   **Tidal-signal wells (CEH3 and CEH22) sit on the coastal/tidal behavioural margin.** CEH16 and NW9, both reference wells in C5, are the coastal-margin pair whose hydrographs include the most coastal-process influence in the reference partition. CEH3 shares a tidal-influence signature with those wells, so the C5 centroid is its closest available match in correlation space --- a genuine rather than coincidental match, with the audit identifying the same coastal/tidal axis that motivates the C5 cluster. CEH22, by contrast, sits in a near-tie: its best-match cluster is C2 with a gap of only 0.0011 over C5, so its assignment carries no real behavioural preference. Both wells' audit results are an assessment of *shape similarity to a centroid*, not of fitness for inclusion in a reference cluster for downstream mechanistic work. CEH3 and CEH22 carry more pronounced tidal contamination than the reference C5 wells (the basis on which S.1 routes them to the extended network), so their audit assignments are informative for spatial interpretation but do not promote them to reference-cluster membership.

### []{#anchor-157}[]{#anchor-158}[]{#anchor-159}Site-specific choices and rationale (chapter-level)

-   **Three scripts, one analytical idea.** Script 04 visualises Ward's partition. Scripts 05 and 06 quantify confidence in that partition. Together they answer "where is each well, and how confidently is it where the partition says it is?" The grouping reflects the analytical unit, not a code-organisation accident.
-   **Pearson coefficient and z-scored centroids in both audit scripts.** Pearson because the partition itself uses Pearson distance (S.2). Z-scored centroids because the comparison should isolate shape --- when a well rises and falls --- from amplitude and mean depth, which are themselves cluster-distinguishing features that the partition has already handled. Both choices propagate the methodological vocabulary of S.2 into Phase 2.
-   **No CEH3/CEH22 in Script 05.** Script 01's *REFERENCE_NETWORK_WHITELIST* excludes them on tidal-contamination grounds (S.1); they appear only in Script 06's extended-network analysis, where their low best-match correlations (0.86 for both) are themselves a signature of the routing decision.
-   **The same cluster colours and shapes across all three figures.** F.4's *CLUSTER_COLOURS* and *CLUSTER_MARKERS* are the single source of truth, so the orientation map (Script 04), the spatial confidence map (Script 05), and the sitewide integration map (Script 06) all use the same visual vocabulary. A reader who has internalised the colour-shape scheme from §4.2 reads §4.3's figures without effort.

### []{#anchor-159}[]{#anchor-160}[]{#anchor-161}Limitations and known caveats (chapter-level)

-   **The Pearson audit is the project's only per-well cluster-confidence quantification.** There is no formal bootstrap confidence interval on per-well affinity, only the bootstrap CI on the cluster-level partition (S.2). Per-well CIs would be a natural extension --- e.g. resampling each well's monthly observations and recomputing all five Pearson values --- but are not in scope here. The audit table's gap statistic is the closest the pipeline gets to a per-well confidence measure.
-   **The sitewide integration map does not visualize the Pearson value itself.** Marker shape encodes best-match cluster, marker fill encodes network membership (reference / extended / spy). A reader who wants the specific correlation value or gap for an individual well must read *06_pear_membership_audit_sitewide.csv*. The trade is a map that stays legible at print resolution against carrying every diagnostic on the figure.
-   **The audit assumes the five-cluster partition is the right one.** If the partition were re-cut at k = 4 or k = 6, the audit logic would still run but the conclusions would be different. The partition is itself defended in S.2; the audit inherits that defence and does not re-litigate it.

### []{#anchor-161}[]{#anchor-162}[]{#anchor-163}Where the result appears in the report

-   §4.2 cluster orientation figure --- *04_01_core_architecture_map.png*.
-   §4.3 Pearson affinity audit --- discussion of borderline wells and the Spy/Fuzzy/Core distribution, drawing on *05_pear_membership_audit.csv* and the spatial confidence map.
-   §4.3 / Figure 14b --- *06_pear_02_integration_map.png* (sitewide integration map).

### []{#anchor-163}[]{#anchor-164}[]{#anchor-165}Cross-references

-   **F.4** --- k=5 partition, cluster IDs, labels, colours, markers.
-   **F.5** --- *map_utils.py* (DEM and KML rendering helpers used by all three scripts).
-   **S.1** --- reference-network whitelist, extended-network construction, *EXTENDED_NETWORK_BLACKLIST*, CEH3/CEH22 tidal routing.
-   **S.2** --- Ward's clustering that produces *02_cluster_stats.csv*; the no-detrending choice that motivates z-scored-shape-only auditing.
-   **S.9** --- Script 11b (the threshold-map chapter) consumes *06_pear_membership_audit_sitewide.csv* for the extended-network rendering.
-   **S.12** --- Script 18 (WTF spatial) consumes the sitewide audit for extended-network Sy interpolation.

## []{#anchor-165}[]{#anchor-166}[]{#anchor-167}S.5 Scripts 07, 08 --- Spatial coefficient maps and LCSC model benchmarking

Steps 7 and 8 / 27. Phase 2 --- Pearson Membership Audit.

Scripts 07 and 08 sit immediately after the Pearson affinity audits and together form the spatial-diagnostic layer on the per-well SSM fits. Both consume the per-well coefficients from *03_master_data.csv* produced in S.3. Script 07 renders the four β₁, β₂, β₃, and R² surfaces across the site so that spatial structure in each coefficient can be inspected directly. Script 08 quantifies how much explanatory power the SSM gains over a deliberately weak counterfactual (a "Traditional Linear Model" with intercept but no drainage term), producing the benchmarking summary that appears as Table 5 of the main report along with a CEH6 hydrograph showdown and two spatial improvement maps.

The grouping is tight. Both scripts read per-well coefficients from the same canonical store; both produce site-scale spatial outputs over the same DEM-and-KML basemap; both rely on the same *map_utils* helpers (F.5). The methodological divergence is what they ask of the coefficients: Script 07 takes the values as given and visualises them as interpolated surfaces; Script 08 refits SSM and TLM on a constrained 100-month window and compares performance per well at the well locations themselves.

### []{#anchor-167}[]{#anchor-168}[]{#anchor-169}Inputs (shared)

Path resolution for both scripts goes through *utils.paths*. The canonical input constants and their roles:

  ------------------------------------------ ----------------------------------------------------------------------------- -------------------
  Path constant                              File (contents)                                                               Used by
  INT_MASTER_DATA                            *03_master_data.csv* (per-well β, R², n, p-values, coordinates, cluster ID)   Scripts 07 and 08
  INT_WELL_ELEVATIONS                        *01_well_elevations.csv* (DEM ground elevations for ridge masking)            Script 07
  *INT_WELLS_CLEAN*, *INT_WELLS_REFERENCE*   *01_wells_clean.csv*, *01_wells_reference.csv*                                Script 08
  INT_CLIMATE                                *01_climate.csv* (monthly P and PET)                                          Script 08
  INT_CLUSTER_STATS                          *02_cluster_stats.csv* (cluster IDs for the metric map merge)                 Script 08
  *DATA_DIR* (KMLs + DEM raster)             *Features.kml*, *streams.kml*, *clearfell.kml*, *newborough_dem.tif*          Both
  ------------------------------------------ ----------------------------------------------------------------------------- -------------------

Naming and pathing conventions are project-wide. Every input goes through an *INT\_* constant defined in *paths.py*; no script reads a hardcoded filename. Cluster colour, marker shape, and label dictionaries (*CLUSTER_COLOURS*, *CLUSTER_MARKERS*, *CLUSTER_LABELS*) come from *config.py*. Scenario parameters and per-cluster mechanistic constants used downstream are consolidated through *pipeline_params.py* (F.4) --- neither Script 07 nor Script 08 modifies that store, but they share its variable naming.

### []{#anchor-169}[]{#anchor-170}[]{#anchor-171}Sub-script 07 --- Spatial coefficient mapping

**Motivation.** The SSM produces a triple (β₁, β₂, β₃) per well. Whether those coefficients vary as smooth functions of position, as cluster-level steps, or as noise around cluster means is a question that only a spatial render can answer. Script 07 produces the four maps that ground the main report's §4.4 spatial discussion: β₁ recharge sensitivity, β₂ atmospheric draw, β₃ drainage rate (log-scaled, as percentage per month), and the R² fit-quality map.

The script replaces a former *07_boundary_intercept.py* that ran a Model A vs Model B intercept audit. Under the displacement formulation (F.3), the headline SSM fits well across all clusters (Script 08 median iterative NSE = 0.75), so the intercept audit added little beyond what direct coefficient mapping reveals. The current Script 07 is a pure visualization: no refit, no statistical test, no Model B fit. Per-well coefficients are inherited unchanged from *03_master_data.csv*.

**Methodology.** Per metric (β₁, β₂, β₃ as percentage, R²), the script:

1.  Loads *INT_MASTER_DATA* and merges DEM ground elevations from *INT_WELL_ELEVATIONS* on the normalized well name.
2.  Calls *map_utils.add_idw_surface()* to interpolate the per-well metric onto the project's standard 50 m grid (*np.arange(240200, 243800, 50)* × *np.arange(362200, 365800, 50)*). The implementation routes through *scipy.interpolate.griddata* with *method=\'linear\'* --- a Delaunay-triangulation-based piecewise-linear interpolation. The grid matches the one used by Scripts 11b, 19, and 20.
3.  Renders the interpolated surface as a semi-transparent pcolormesh layer (*alpha=0.65*) on top of a greyscale DEM hillshade (*map_utils.load_dem_hillshade*, vertical exaggeration ×3).
4.  Applies a ridge mask. Grid cells where the DEM raster elevation exceeds the interpolated well-elevation surface by more than 1.0 m are set to NaN, preventing the surface from extending across inter-dune ridges where no well measurements exist. In B&W output mode the mask is disabled in favour of an annotation that warns the reader to interpret ridge-top values with caution.
5.  Overlays Features and clearfell KML features (streams are omitted for these maps), then plots the well markers themselves at each well's (E, N) --- each marker uses the cluster's colour (*config.CLUSTER_COLOURS*) and cluster shape (*config.CLUSTER_MARKERS*) at a uniform size. The markers indicate cluster membership; the metric value at each well is read off the underlying interpolated surface, not the marker.
6.  Adds metric-value contours for β₁ (every 0.5 from 2.0 to 6.5), β₂ (every 0.5 from 0.5 to 3.5), β₃ (at 0.5, 1.0, 2.0, 5.0, 10.0 %), and R² (every 0.10 from 0.50 to 0.90).

All four panels (β₁, β₂, β₃, R²) follow the same render path. The R² panel is an interpolated surface in the same sense as the β panels --- a reader looking at the β₃ map can take the corresponding R² map and read off where the underlying fits are stronger or weaker.

β₃ uses a log scale because the network range spans nearly two orders of magnitude --- C4 Main Forest median around 2 %/month (and one well, CEH14, returning negative β₃; see *Limitations*), C1 Lake Edge median around 10 %/month and reaching 13.5 %/month at its strongest wells. A linear scale would collapse the lower-β₃ cluster bulk into a narrow band at the bottom of the colour ramp. The map also rescales β₃ from its decimal form to percentage (×100) for intuitive reading.

A cluster summary table is also printed to console and written to *07_coefficient_summary.csv*. The table reports per-cluster mean, std, min, and max for each β and for R² --- a per-well-derived summary that complements (rather than replaces) the cluster-centroid Table 3 that Script 03 fits directly. A companion file, *07_coeff_05_cluster_ranges.csv*, records the per-cluster minimum and maximum of β₁, β₂ and β₃ (with n) as a compact per-cluster range summary, so the tabulated coefficient ranges have a dedicated, reviewer-findable source CSV.

Site-specific choices and rationale.

-   **Linear (Delaunay) interpolation rather than IDW.** The helper is called *add_idw_surface* for historical reasons, but the live default is *method=\'linear\'*. Linear interpolation produces a continuous surface that passes exactly through each well's coefficient value and varies smoothly between neighbours. True IDW would smooth across the network even within Delaunay triangles, which is poorly motivated here because the per-well coefficients are point measurements, not noisy realisations of a continuous field. The misnomer is on the to-fix list (end-of-chapter notes).
-   **Ridge mask threshold of 1.0 m.** The threshold removes grid cells where the DEM raster sits more than 1 m above the elevation surface the wells interpolate to --- i.e. inter-dune ridges and the bedrock ridge along the northern boundary. A 1 m threshold keeps everything within the warren's working amplitude masked-in (the highest dipwell sites sit on slack-floor terraces) while excluding the dune-ridge tops and the bedrock-ridge area where no wells exist.
-   **Cluster colour and shape on markers, with no per-well R² encoding.** Markers are filled with the cluster colour and use the cluster shape at uniform size. The metric value at each well is encoded in the interpolated surface beneath the marker, not on the marker itself. A reader of the β₁ map can identify which cluster each well belongs to without needing a separate cluster-orientation figure (S.4); per-well uncertainty is read off the dedicated R² panel.
-   **R² rendered as the fourth interpolated panel rather than as a marker overlay on the β panels.** Each of the four panels carries its own information independently. The β panels show coefficient values; the R² panel shows where the underlying fits are robust. A reader interrogating a spatial pattern in β₃ should cross-reference the R² panel at the same locations.

Outputs.

  -------------------------------------------------------- -------------------------------------------------------------
  Output                                                   Description
  07_coefficient_summary.csv                               Per-cluster summary (mean, std, min, max) for each β and R²
  07_spatial_coefficients/07_coeff_01_beta1_recharge.png   β₁ map
  07_spatial_coefficients/07_coeff_02_beta2_atm_draw.png   β₂ map
  07_spatial_coefficients/07_coeff_03_beta3_drainage.png   β₃ map (log scale, percentage)
  07_spatial_coefficients/07_coeff_04_r2_quality.png       R² map
  07_spatial_coefficients/07_coeff_maps_data.csv           Per-well data underlying the maps
  -------------------------------------------------------- -------------------------------------------------------------

Limitations and known caveats.

-   **Per-well coefficient values for wells with small n carry wide confidence intervals.** The R² map serves as a soft proxy for fit quality across the network --- wells with R² \< 0.6 should be read as carrying real spatial information only where neighbouring wells in the same cluster show concordant values.
-   **Interpolation between point measurements is a visual aid, not a mechanistic claim.** A continuous surface drawn across the site should not be read as evidence of a continuous physical gradient. Where cluster-level steps appear (for example the β₂ jump from C1 Lake Edge at 0.63 to C4 Main Forest at 2.64), the discrete cluster structure is the underlying signal; the smoothness of the interpolated surface between them is graphical, not physical.
-   **CEH14 produces a negative β₃ at the canonical 3.7 m datum** (β₃ = −0.021, R² = 0.59; see *07_coeff_maps_data.csv*). It is the only well in the network where the soft physical-sign warning fires under the canonical datum. The well sits on the bedrock ridge flank, where a head-dependent term absent from the three-term model is implicated; lateral recharge from the ridge is one candidate, raised in earlier work on the site and not excluded by the present record; the negative β₃ is the spatial map's signal that something physical is missing here rather than that the well is malfunctioning. The phenomenon is taken up in S.16.

Where the result appears in the report.

-   §4.9.2 *Spatial coefficient structure* --- the four maps as Figures 48a--d.
-   §3.4 *Drainage datum sensitivity* --- the per-well R² map provides cross-check context for the per-well datum sensitivity discussion.

### []{#anchor-171}[]{#anchor-172}[]{#anchor-173}Sub-script 08 --- LCSC model benchmarking

**Motivation.** The headline SSM is a three-parameter physically motivated model. A reasonable counter-question is: what does the third parameter (β₃, the drainage feedback) actually buy over a simpler model that lacks it? Script 08 quantifies this by fitting both the SSM and a "Traditional Linear Model" (TLM, also called Model A and Model B in the historical intercept-audit naming) on a 100-month most-recent window per well, then comparing performance on three metrics: one-step R², iterative R², and iterative NSE.

The TLM is the simplest unphysical alternative:

> Δh(t) = α + β₁·P(t) − β₂·PET(t)

Crucially the TLM has an *intercept*. Without β₃·(z₀ + h(t−1)) in the right-hand side, an intercept absorbs whatever constant lateral subsidy would otherwise be unrepresented. The TLM is therefore not the worst possible alternative --- it has one degree of freedom more than the SSM (an intercept) but lacks the displacement feedback. This makes the comparison conservative: if the SSM beats the TLM, it does so despite the TLM's extra fitted parameter.

The TLM is not put forward as the published model and is not claimed to be optimal in any sense. It is the counterfactual: a deliberately weak alternative that quantifies how much explanatory power the SSM contributes beyond a structurally simpler unphysical baseline. More elaborate alternatives (PEARL, MODFLOW with calibrated boundary conditions, Bayesian state-space formulations) would in principle fit better than either model at specific wells. The benchmarking does not engage with those --- its remit is to justify the SSM's additional complexity against the structurally simplest possible competitor.

**Methodology.** For each well in the reference network (excluding three wells in *EXCLUDED_WELLS_NORM = {\'ceh7\', \'ceh8\', \'ceh37\'}*, which carry inconsistent records that fail the benchmarking's data-quality bar --- see Site-specific choices below):

1.  The script aligns the well series with monthly climate via *build_ssm_frame()* (F.3), with *window=100* so only the most recent 100 aligned months are kept.
2.  The SSM design matrix is built directly (*\[+P, −PET, −h_disp_prev\]* with no intercept) and fit by OLS. The TLM design matrix is *sm.add_constant(\[P, −PET\])* and fit by OLS. Both fits use *HEADLINE_LAG = 0* from config --- no rainfall lag.
3.  **One-step simulation** uses the observed previous-month water level as the recurrence anchor: at each month *t*, the model predicts h(t) from h_obs(t−1) plus its own Δh prediction. This metric measures diagnostic fit (how well the model recovers month-to-month changes given the truth at the previous step).
4.  **Iterative simulation** is the autonomous forecast: starting from h_obs at the window's first month, the model predicts h forward step-by-step, with each month's prediction feeding into the next as *h_prev*. The SSM iterative simulation uses *model_utils.simulate_ssm()*. The TLM iterative is simpler --- without a feedback term, it just accumulates Δh from climate forcing alone. This metric measures forecasting stability, which is the harder test.
5.  For each well and metric, the script computes one-step R², iterative R², iterative NSE, and iterative RMSE for both models, plus per-well Δ = (SSM − TLM) for each metric.

Three figures are produced:

-   A **dual-panel showdown** for CEH6 --- top panel is one-step diagnostic fit, bottom is iterative forecasting. CEH6 was chosen as the showcase because it produces a clear visual contrast between the two models without being the most extreme case in the network. The TLM drifts to NSE = −1.12; the SSM holds at NSE = +0.66.
-   A **spatial ΔR² map** showing the SSM's per-well improvement in iterative R² over the TLM. The map is a point-scatter rendering with no interpolation: each well is plotted at its (Easting, Northing) as a cluster-shape marker filled by ΔR² value, on top of the standard DEM-and-KML basemap. The per-well improvement values are themselves the diagnostic --- interpolating between wells would smooth across the localised structure that the map exists to make visible.
-   A **spatial ΔNSE map** in the same style, with the diverging signed-NSE-improvement colour scale clipped to ±1.5 to keep the bulk of the network on the visible scale (CEH14's −6.82 outlier would otherwise compress everything else into a few colour bins; raw values are preserved in the underlying CSV).

A summary table is written for the main report (*08_lcsc_04_table3_benchmark_summary.csv*), and a per-well stats table is written for downstream reference (*08_lcsc_model_stats.csv*).

Site-specific choices and rationale.

-   **100-month window** rather than the full record. The choice keeps both fits on a recent, well-sampled segment of the record and avoids letting older data (with sparser sampling, pre-clearfell baselines, and possible measurement-protocol drift) dominate. The number is *LCSC_DATA_LIMIT = 100*, declared in *config.py* and imported by every script that uses it (Scripts 03, 08 and 30).
-   **Excluded wells: CEH7, CEH8, CEH37.** These three wells have inconsistent records --- gaps, regime changes, or sampling discontinuities that disqualify them from a 100-month-window benchmarking exercise. The exclusion is recorded as a fixed rule in *EXCLUDED_WELLS_NORM* at the top of the script. The exclusion is empirical and field-driven rather than algorithmic: documenting the per-well reason in an in-code comment at the exclusion site is on the to-fix list.
-   **CEH6 as the showcase well.** CEH6 was chosen because it produces a clear visual contrast between the TLM and SSM iterative trajectories without being the most extreme well in the network. A more extreme case would compress the visual difference into the same plot range; CEH6's NSE_TLM ≈ −1.1 / NSE_SSM ≈ +0.7 produces two trajectories that diverge visibly but both stay on a readable scale. No other methodological consideration entered the choice.
-   **Lake sentinel excluded from the max-improvement reporting.** The Table 5 "Max NSE improvement" row excludes the lake-side *LlynRhos* sentinel well. The lake sentinel has a tightly bounded surface-water signal that makes its TLM-vs-SSM comparison atypical of warren hydrology.
-   **The TLM iterative simulation has no feedback term.** That is the deliberate point. The TLM fits a constant Δh-per-month from climate alone, with no recovery mechanism if water level drifts off the observed trajectory. Without a drainage term the TLM cannot represent the physical fact that drier sites drain less slowly than wet sites; without the displacement formulation the iterative simulation accumulates whatever climate-driven Δh the OLS estimated, and drifts. This is the model the SSM is being compared against --- the simplest specification under which "memory of the water-table position" is absent.

Outputs.

  --------------------------------------------------------------- -----------------------------------------------------------------------------------------------
  Output                                                          Description
  08_lcsc_model_stats.csv                                         Per-well one-step R², iterative R², iterative NSE for both models, with per-well improvements
  08_model_benchmarking/08_lcsc_01_ceh6_showdown.png              CEH6 dual-panel showdown (one-step top, iterative bottom)
  08_model_benchmarking/08_lcsc_02_r2_improvement_map.png         Spatial ΔR² (iterative) point-scatter map
  08_model_benchmarking/08_lcsc_03_nse_improvement_map.png        Spatial ΔNSE point-scatter map
  08_model_benchmarking/08_lcsc_04_table3_benchmark_summary.csv   Six-row summary table for the main report (Table 5)
  --------------------------------------------------------------- -----------------------------------------------------------------------------------------------

The live Table 5 summary records: median one-step R² of 0.91 (TLM) vs 0.92 (SSM); median iterative R² of 0.64 vs 0.77; median iterative NSE of −0.03 vs 0.72. The one-step gap is small --- both models recover diagnostic fit. The iterative-NSE gap is large --- the SSM contributes most of its value in forecasting stability, not in one-step diagnostic fit. Thirty of 66 reference wells have iterative NSE \> 0 under the TLM; 65 of 66 do under the SSM. The single well where SSM iterative NSE is negative is CEH14 --- the same ridge-flank well that produces the negative β₃ in Script 07's map. The two diagnostics agree on which well the canonical SSM does not describe.

Limitations and known caveats.

-   **The TLM is the simplest unphysical alternative, not a comprehensive comparator.** Wells where the SSM iteratively underperforms the TLM (CEH13 by Δ_NSE = −0.027, CEH14 by Δ_NSE = −6.82) sit at the C4 Main Forest's bedrock-ridge interface. The shortfall there is not that the TLM is better; both models perform poorly. The TLM happens to drift less catastrophically because its intercept absorbs some of the systematic residual the SSM leaves at these wells. Neither model represents whatever term is missing there; lateral inflow from the bedrock ridge is the candidate raised in earlier work, and the record does not settle it. Diagnosing it requires the supplementary analyses in S.16.
-   **One-step R² gap is small by construction.** Both models share the same predictors P and PET; the one-step metric is dominated by the climate-driven variance, which both decompositions capture. The benchmarking's headline number is the iterative NSE, where the SSM's structural advantage is unmasked.
-   **The 100-month window encodes a temporal-stationarity assumption.** Where the underlying hydrology is non-stationary (C5 Coastal Forest's coastal retreat, C1 Lake Edge's 2018 regime change), restricting the fit to recent months partially mitigates the issue, but the comparison still asks "which model fits the last 100 months better" rather than "which model is correct over the full record". The non-stationary regimes are taken up in S.7 (clearfell BACI) and S.15 (coastal gradient).

Where the result appears in the report.

-   §4.4 *Model benchmarking* --- Table 5 of the main report draws directly from *08_lcsc_04_table3_benchmark_summary.csv*.
-   §4.4 / Figure --- CEH6 showdown panel.
-   §4.4 / Figure --- ΔR² and ΔNSE spatial maps.

### []{#anchor-173}[]{#anchor-174}[]{#anchor-175}Site-specific choices and rationale (chapter-level)

-   **Both scripts consume ***03_master_data.csv*\*\* as the per-well coefficient table.\*\* No script in this chapter refits the SSM on the headline (full-record) configuration; Script 07 inherits values from S.3, and Script 08's refits are on a deliberately restricted 100-month window for the model-comparison question. The headline cluster-level coefficients used elsewhere in the pipeline (S.9 thresholds, S.11 water balance, S.14 forestry scenarios, S.7 clearfell BACI) are S.3's full-record values, not the 100-month values from S.8.
-   **Both scripts produce site-scale spatial outputs over the same basemap.** The DEM-and-KML basemap, the cluster-shape and cluster-colour marker convention, the variable-name conventions inherited from *pipeline_params.py* and *config.py*: all of these are project-wide. A reader can compare Script 07's β₃ map with Script 08's ΔNSE map directly because both are rendered on the same extent with the same cluster-shape marker convention.
-   **The two scripts diverge on the question of interpolation.** Script 07's metric maps are continuous interpolated surfaces (Delaunay-linear) over the standard 50 m grid; the surface is the answer. Script 08's improvement maps are point-scatter plots: each well is a single coloured marker with no interpolation between wells. This is deliberate. Script 07's β values are correlated as members of the same cluster, so an interpolated surface between nearby wells in the same cluster is informative; Script 08's per-well improvement values encode where the canonical SSM specifically struggles, which is a per-well property, and interpolating would smooth across the localised structure that the maps exist to make visible.

### []{#anchor-175}[]{#anchor-176}[]{#anchor-177}Limitations and known caveats (chapter-level)

-   **Both spatial maps inherit the cluster partition's spatial structure.** Where the maps show step-like changes between adjacent regions, the underlying signal is that the wells on each side belong to different clusters with different mechanistic signatures (S.2, S.3). The partition is itself defended in S.2; this chapter inherits that defence rather than re-litigating it. If the cluster partition were re-cut at a different k, both Script 07's coefficient maps and Script 08's improvement maps would change.
-   **CEH14 is the consistent outlier across both scripts.** Script 07's β₃ map flags it as the single negative-β₃ well at the canonical datum; Script 08's iterative NSE flags it as the worst-fitting well in the network (Δ_NSE = −6.82). Both signals point to the same missing term in the displacement-formulation SSM. Bedrock-ridge subsidy is the candidate mechanism raised for it; the diagnostics that test it are in S.16 (ridge recharge lag hypothesis test).
-   **The benchmarking is a counterfactual, not a comprehensive model comparison.** The chapter does not claim the SSM is optimal --- only that it improves substantially over the simplest unphysical alternative. More elaborate alternatives exist; their evaluation is out of scope.

### []{#anchor-177}[]{#anchor-178}[]{#anchor-179}Cross-references

-   **F.3** --- SSM equation form, sign conventions, drainage datum, *model_utils.fit_ssm()* interface. Both scripts use this implicitly through *03_master_data.csv* (Script 07) or directly through *build_ssm_frame()* and OLS (Script 08).
-   **F.5** --- *map_utils.py* (DEM hillshade, KML overlay, grid interpolation helpers) and *model_utils.simulate_ssm()* (Script 08's SSM iterative simulation).
-   **S.3** --- produces *03_master_data.csv*, the input to both scripts. The per-well datum sensitivity discussion in S.3 also contextualises CEH14's β₃ anomaly.
-   **S.4** --- Pearson affinity audit (the immediately preceding chapter); the two chapters together carry the §4.2--§4.4 spatial discussion in the main report.
-   **S.16** --- supplementary diagnostic chapter on the unresolved CEH14 residual and the ridge-recharge hypothesis, picking up the residual signal that Script 07 and Script 08 both flag.
-   **S.9** --- Script 11b uses the same 50 m grid for spatial threshold mapping; the grid resolution is a project-wide convention.

# []{#anchor-179}[]{#anchor-180}[]{#anchor-181}Phase 3 --- Model Diagnostics and Intervention Analysis

## []{#anchor-181}[]{#anchor-182}[]{#anchor-183}S.6 Script 09 suite (a--e) --- Scraping intervention

Step 9 / 27 (sub-scripts 9a--9e). Phase 3 --- Model Diagnostics and Intervention Analysis.

In April 2015, approximately 0.2 m of surface soil was mechanically excavated over an area of approximately 0.3 ha at CEH36 in the felled forest compartment. The intervention tested whether mechanical lowering of the ground surface could restore dune-slack hydrology --- bringing the water table closer to the surface and reversing the drying that the forest canopy had imposed on the underlying slacks. This is one of two management experiments at the warren; the other is the December 2017 clearfell, covered in S.7. A second, smaller scraping event in October 2023 at CEH18 and CEH21 introduces an additional era boundary for those two wells but is not the chapter's headline. The Script 09 suite is the entire methodological evaluation of the scraping intervention.

The suite is five sub-scripts answering five distinct questions. *09a --- Hierarchical paired BACI* (the core analysis) asks whether scraping worked at the scraped well itself. *09b --- Scraping propagation* asks whether it propagated uphill into the surrounding forest as a detectable shift in SSM coefficients. *09c --- Summer minima* asks whether the intervention improved ecologically critical summer-minimum depths, not just annual means. *09d --- Scenario comparison* asks whether scraping was a good management choice compared to alternative interventions at the same site. *09e --- Robustness* gives three independent estimates of the headline step change to verify it is not an artefact of any single method's assumptions. The orchestrator *run_09_scraping.py* invokes the sub-scripts in this order; 09b must precede 09d because 09d consumes 09b's centroid CSV indirectly via the shared scenario engine. All five share infrastructure through *utils/scraping_common.py*.

The suite's principal results --- the headline +0.129 m benefit at CEH36 (paired-BACI Pure-Scraping era, vs CEH4), the propagation signal across wells 247--776 m uphill, and the alternative-intervention comparisons --- populate §4.5 *Scraping intervention* in the main report, including Table 6 (β₃ era coefficients per well, mapped from *09_scrape_04b_beta3_era_summary.csv*) and Figures 17--20, 22--24, 26, and 27.

### []{#anchor-183}[]{#anchor-184}[]{#anchor-185}Sub-script 09a --- Hierarchical paired BACI

**Motivation.** The core scraping analysis. A naïve paired BACI of CEH36 against CEH4 --- the obvious local control well, ≈100 m to the south --- would overstate the scraping benefit, because CEH4 is itself drying due to progressive coastal retreat affecting the western coastline. A two-tier hierarchical design separates the *scraping signal* at CEH36 from the *coastal drainage signal* contaminating the local controls.

**Methodology.** Tier 1 evaluates the local controls (CEH4, CEH22) against the regional mean --- a five-well climate-only composite (*CLIMATE_CONTROLS = ceh9, nw7, nw6, nw5, wmc2*). If the local controls dry faster than the regional baseline, Tier 1 has demonstrated a coastal drainage signal at the controls themselves. The result in the live data is unambiguous: CEH4 drifts to a CUSUM terminal value of −10.7 m relative to the regional mean, and CEH22 to −19.1 m. The local controls are themselves carrying a coastal signal. Tier 2 evaluates the impact wells (CEH36, CEH18, CEH21) against the paired local controls. Once Tier 1 has established the coastal signal, the Tier 2 BACI shift at CEH36 vs CEH4 is the *pure scraping effect* net of that signal.

Within each tier, per-well analysis runs in two layers. First, the well-minus-control time series is averaged within each era window (from *WELL_ERAS*, described in *Suite-level methodology* below), and the change in mean between successive eras is the BACI step. Second, the SSM (F.3) is refit per-well per-era via direct OLS on the era's monthly observations, with the same *\[+P, −PET, −(z₀ + h_prev)\]* design matrix as Script 03. Per-era β₃ estimates with 95 % confidence intervals come from an "isolated" refit: the script first fits the full SSM to extract β₁ and β₂, subtracts the climate-driven Δh component, then regresses the remaining drainage component on *−h_disp_prev* with an intercept to recover an unbiased β₃ and its CI. The isolated β₃ estimates populate the report's per-well β₃ era table (Table 6 in the main report).

The live numbers tell the story. CEH36's β₃ rises from 0.096 (Baseline, p = 0.011) to 0.142 (Pure Scraping, p = 0.001) to 0.124 (Felling Pulse, p \< 0.001) --- a structural drainage signal consistent with the surface having been lowered by 0.2 m. The paired BACI shift at CEH36 vs CEH4 is +0.129 m for the Pure Scraping era and +0.024 m for the Felling Pulse era. The net benefit against CEH21 --- the coastal benchmark, secondary impact, but the well whose own trajectory most closely represents what CEH36 would have done without scraping --- is +0.144 m.

Site-specific choices.

-   **Two-tier rather than direct impact-vs-climate.** Tier 1 confirms the coastal signal at the local controls; Tier 2 nets it out at the impact wells. Skipping Tier 1 would conflate scraping with coastal retreat.
-   **CEH21 as the coastal benchmark for the net-benefit calculation.** CEH21 is itself a secondary scraping recipient in 2023, but in the Pure Scraping era (2015--2017) it is an undisturbed coastal-retreat-affected well. Its drying baseline is the most relevant comparator for what CEH36 would have done without scraping; the net-benefit calculation accordingly uses CEH21 rather than CEH4.
-   **The paired CEH36 / CEH4 shift is the principal headline.** The +0.129 m Pure-Scraping shift is the figure quoted throughout §4.5. The slightly larger net benefit against CEH21 (+0.144 m) is reported alongside for context but is not the primary number.

Outputs.

  ----------------------------------------- ------------------------------------------------------------------
  Output                                    Description
  09_scrape_01_full_parameters.csv          Per-well, per-era SSM coefficients (β₁, β₂, β₃)
  09_scrape_02_beta3_significance.csv       Isolated β₃ estimates with 95 % CIs and p-values
  09_scrape_03_baci_shifts.csv              Paired BACI step changes between eras
  09_scrape_04_net_benefits.csv             Net benefits at impact wells vs CEH21 benchmark
  09_scrape_04b_beta3_era_summary.csv       Formatted β₃ era summary (the Table 6 source in the main report)
  09_tier1_final_cusum.csv                  Tier 1 CUSUM terminal values
  09_scrape_05_tier1_background_drift.png   Tier 1 BACI hydrographs + CUSUM panel
  09_scrape_06_tier2_scraping_signal.png    Tier 2 BACI hydrographs + CUSUM panel
  09_scrape_07_beta3_confidence.png         β₃ era estimates with 95 % CIs across wells
  09_scrape_report_numbers.csv              All citable values for §4.5
  ----------------------------------------- ------------------------------------------------------------------

### []{#anchor-185}[]{#anchor-186}[]{#anchor-187}Sub-script 09b --- Scraping propagation

**Motivation.** Did the ground-scraping at CEH36 propagate uphill into the surrounding forest as a detectable change in SSM coefficients? The physical hypothesis: increased drainage at the scraped site creates a hydraulic gradient that draws water from upgradient wells, manifesting most clearly as elevated β₃ at neighbouring wells north and northwest of CEH36 in the local groundwater-flow direction.

**Methodology.** Split-window SSM fitting on a fixed pre-scraping window (start of record to April 2015) versus a fixed post-scraping window (April 2015 to December 2017, before the felling pulse). Per-well, the SSM is fit on each window via *model_utils.fit_ssm()* (F.3) with a minimum-observations threshold of 12 months per window. The raw shift Δβ = post − pre is then BACI-corrected against the centroid raw shift of seven distant control wells (NW1, NW2, NW11, NW13, WMC4, D25, WMC2), which sit at 852--1070 m from CEH36 --- far enough that they are outside the scraping's hydraulic-gradient reach, close enough that they share the same regional climate forcing. The BACI-corrected shift at each well is the propagation signal at that well.

Ten uphill wells north and northwest of CEH36 enter the analysis (CEH31, WMC3, NW6, NW7, CEH30, CEH20, CEH33, CEH9, CEH34, CEH1), at distances 247--776 m. Wells south or coastward of CEH36 (CEH4, CEH18, CEH21, CEH22, NW5) are excluded as downhill of the scraping in the flow direction --- a change at a downhill well is not attributable to scraping in the same way, because scraping draws water *uphill* via the local hydraulic gradient, not downhill. The outer C5 coastal wells (NW9, CEH16, CEH19, CEH17) are also excluded as confounded by coastal boundary effects. FE1--4 and LIS1 are excluded because they have no pre-scraping record. CEH39 was included in an earlier 11-well pass of the analysis but has been dropped from the live set on baseline-length grounds (n_pre = 24, too short for a reliable pre-scraping SSM fit at this well).

After per-well fitting, wells are aggregated into three centroid groups: scraped (CEH36 alone), non-forest uphill (CEH31 with the C3 uphill wells), and forest uphill (the C4 wells). The centroid time series is averaged across wells and refit on the same split windows, producing a centroid-level pre β₃, post β₃, and BACI-corrected percentage shift.

The live centroid summary gives BACI-corrected β₃ shifts of +7.6 % (non-forest uphill, 6 wells), +9.4 % (forest uphill, 4 wells), and +11.0 % (all uphill, 10 wells). At the individual-well level the shifts span −24 % (CEH34) to +29 % (WMC3 at 262 m) with no monotonic distance decay: CEH9 at 571 m gives +21 % and WMC3 at 262 m gives +29 %, while NW7 at 383 m gives +5 % and NW6 at 284 m gives +0.5 %. The centroid-level signal is the robust summary; per-well shifts at this n are noisy. All three centroids are positive, individual wells are noisy, and there is no clean distance gradient.

Site-specific choices.

-   **The 852--1070 m control distance band.** Far enough that the controls are outside the scraping's hydraulic-gradient reach; close enough that they share regional climate forcing.
-   **Excluding downhill wells.** Flow-direction physics: scraping draws water uphill via the local hydraulic gradient. A change at a downhill well after the intervention is not attributable to scraping in the same way.
-   **Centroid averaging.** The 31-month post-scraping window is short relative to typical SSM fit windows. Per-well coefficients have wide CIs at this n; centroid averaging within distance bands compresses the noise and gives the propagation signal at a scale where it can be defended.
-   **The cluster-weighted scraping bars in the scenario chart.** The propagation analysis feeds a scraping scenario bar into the cross-cluster scenario comparison figure. C3 wells use the non-forest uphill centroid shifts; C4 wells use the forest uphill centroid shifts; C5 uses the C3+CEH31 centroid shifts (same western coastal zone). Bars are then weighted by the fraction of each cluster within 800 m uphill of CEH36 (C3: 29 %, C4: 78 %, C5: 100 %, C1 and C2: 0 %).

**Scenario figures are volumetric, not summer-minimum.** The cross-cluster scenario figure (*09b_05*) and the CEH36 scenario figures (*09d_01*, *09d_02*) report each scenario as an equilibrium **volumetric** change (mm water-equivalent per month), the quantity produced directly by *scraping_common.compute_scenario_bars()* (§F.5, the Option-3 engine used throughout the scenario work). Earlier versions converted this flux to a summer-**minimum** depth by dividing by the cluster specific yield and multiplying by a per-cluster amplification factor (the OLS slope of annual summer-minimum head on annual-mean head). That conversion was withdrawn on 2026-07-02: the SSM equilibrium framework carries no transient and therefore cannot resolve a true summer minimum, and the mean→minimum amplification slope is least reliable at precisely the forested clusters, where the winter-rise/summer-stagnation asymmetry means a mean-level change does not propagate cleanly to the summer trough (the +113 mm mean-level clearfell recovery yields a non-significant summer-minimum step; §S.7). All scenario figures are consequently on one volumetric scale, directly comparable across *09b* and *09d*.

Converting a volumetric bar to a water-table **head** change (mm), as used for the Curreli et al. (2013) thresholds, requires dividing by an appropriate specific yield; this is not straightforward, because the WTF specific yields are reliable for ranking clusters but high in absolute terms (§S.12, Appendix B --- the coarse Sy gradient is robust across three methodologically distinct estimators; the **only** downstream quantity that takes an absolute Sy is the Figure 50 reach λ = √(Kb/(Sy·β₃)), used as an order-of-magnitude input; the storage--drainage index Sy/β₃ is a diagnostic and is no longer relied on in the discussion; the residence time 1/β₃ is Sy-free), so any head equivalent is approximate. The figures therefore carry a caption note to that effect rather than presenting a head axis.

The scraping bar remains an *empirical* BACI shift measured directly at the scraped site (CEH36 versus CEH18 for *09b_05*; CEH36 versus CEH4 for the *09d* observed bar), rendered on the volumetric axis by multiplying the observed head shift by the relevant specific yield. It is placed on the same axis as the SSM-equilibrium scenarios for comparison but is derived independently and labelled as such.

*Implementation.* The scenario values flow from a single source of truth, *scraping_common.compute_scenario_bars()* (v1.5.0), consumed directly by *09b* (*09b_05*, all scenarios) and Script 21 (*21_forestry_06*, the forest-management scenarios only), so the per-cluster forestry volumetric values are byte-identical between the two outputs by construction. The earlier flux→summer-minimum helpers (*summer_amplification_factors()*, *flux_to_summer_min_mm()*, *scenario_summer_min_bars()*) are retained in *scraping_common.py* but are no longer called by any script; they are marked for removal in a future output-tidy pass.

Outputs.

  --------------------------------------------- ---------------------------------------------------------------------------------
  Output                                        Description
  09b_01_individual_well_baci.csv               Per-well pre/post β coefficients and BACI-corrected shifts
  09b_02_centroid_summaries.csv                 Group centroid BACI shifts with percentage β₃ change
  09b_03_ceh36_equilibration.jpg                CEH36 climate-corrected post-scraping trajectory
  09b_04_scenario_comparison.{csv,jpg}          Cross-cluster scenario bar chart with scraping bars
  09b_05_summer_scenario_comparison.{csv,png}   Volumetric cross-cluster scenario comparison (equilibrium mm water-equiv/month)
  09b_report_numbers.csv                        Citable values for §4.5
  --------------------------------------------- ---------------------------------------------------------------------------------

### []{#anchor-187}[]{#anchor-188}[]{#anchor-189}Sub-script 09c --- Summer minima

**Motivation.** Annual mean shifts can hide ecologically critical summer minima. Dune-slack flora at Newborough are constrained by summer drying; an intervention that improves the annual mean but leaves summer minima unchanged is ecologically less valuable than one that lifts the minimum. The script measures whether scraping affected the critical Jun--Sep minimum depth, not just the annual mean.

**Methodology.** Per-well annual summer-minimum depth (the minimum Jun--Sep value each year) is computed pre- and post-scraping at CEH36, CEH18, CEH21, with CEH4 and CEH22 carried as controls. Each well's "gap" each year is the well's summer minimum minus a control centroid's summer minimum. Two control centroids run in parallel --- a *climate-only* centroid (the five climate-control wells averaged) and a *paired* centroid (CEH36's paired control CEH4; CEH21's paired control CEH22) --- giving the dual-control name. The gap series is compared via Welch t-test pre- versus post-intervention, with the 2015 cut-off year as the boundary. The methodology mirrors Script 10d (S.7), applied to the scraping timeline rather than the clearfell timeline.

The dual-control design now produces two clearly significant results pointing the same direction. CEH36's summer-minimum gap against the climate-control centroid widens by +159 mm post-scraping (p = 0.007, \*\*); the gap against the paired control CEH4 widens by +195 mm (p = 0.004, \*\*). The two shift magnitudes are within 36 mm of each other. Both controls tell the same story at similar magnitude: at CEH36, scraping lifted the summer minimum.

The interpolation policy matters to this result. The five climate-control wells include NW6 and NW7, which have multi-month Jun--Sep gaps in several years; under a loose interpolation *limit* those gaps are bridged by straight lines from May to October endpoints, imputing phantom summer values into the control centroid (S.1). The *limit=1* policy excludes those multi-month bridges, so the climate-control centroid here rests on measured Jun--Sep data, and the *min_measured=2* rule (below) drops any control-well year that cannot honestly supply a summer minimum.

**Equilibration (decay) characterisation.** Beyond the pre/post step, the script characterises the shape of the post-scraping response at CEH36, because the summer-minimum gap does not simply step: it rises to a peak and then partially relaxes. For each control currency the peak is the maximum gap in the post-scraping years, the residual plateau is the mean of the final *EQUIL_RESIDUAL_WINDOW_YEARS* summer years, and the decay is an ordinary-least-squares slope of the annual gap on year --- reported both from the observed peak and from the scraping year. The slope is a plain OLS fit with no autocorrelation correction: at annual resolution (n of order ten) an AR(1) adjustment is unstable, a deliberate departure from the AR(1) treatment used for the longer monthly-derived coast-to-inland transect series (Script 38, §S.21.5). A slope is reported only where at least *EQUIL_MIN_FIT_POINTS* annual points are available. The characterisation runs on both the climate-corrected and the CEH4-paired gap: against the climate control the response peaks about two years post-scrape and relaxes toward a residual well above baseline; against the paired control the series does not turn over (its maximum is the final year, so the post-peak slope is degenerate and reported as such). This divergence is retained rather than reconciled --- CEH4 lies at the seaward end of the slack and carries the same coastal drawdown as CEH36, so pairing removes the shared coastal decline along with any scrape relaxation. The decay is therefore reported against the climate control, with the paired series making explicit that it cannot be attributed to scrape relaxation alone. The two window constants live in *config.py* (*EQUIL_RESIDUAL_WINDOW_YEARS*, *EQUIL_MIN_FIT_POINTS*); all windows otherwise derive from the scraping date, the observed peak, and the last available year.

Site-specific choices.

Outputs.

  --------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Output                                  Description
  09c_01_summer_minima.csv                Per-well, per-year summer minima and gap series; the *n_interpolated* column records how many of each (well, year)'s surviving Jun--Sep months were filled by *limit=1* interpolation (see S.1 for the underlying *01_wells_provenance.csv*). Rows with fewer than two measured Jun--Sep months are dropped by the *min_measured=2* rule.
  09c_02_summer_minima_shifts.csv         Per-well Welch t-test results, both controls
  09c_03_summer_minima_climate_ctrl.png   Three-panel: raw minima, impact gaps, control gaps (climate control)
  09c_04_summer_minima_paired.png         Paired-control comparison: CEH36 vs CEH4
  09c_report_numbers.csv                  Citable values for §4.5, plus the equilibration peak, residual plateau, and decay slopes (climate and paired controls)
  --------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-189}[]{#anchor-190}[]{#anchor-191}Sub-script 09d --- Scenario comparison

**Motivation.** Was scraping a good management choice for this site? Using CEH36's own SSM coefficients, its WTF-derived Sy, and its mean head displacement, the script computes the equilibrium volumetric response to alternative interventions --- clearfell, thinning, broadleaf conversion, UKCP18 dry and wet climate scenarios --- under both annual-mean and summer forcing, and compares each to the observed scraping benefit. The comparison is a like-for-like, single-site equivalent.

**Methodology.** Per-well parameters for CEH36 come from *03_master_data.csv* (β coefficients, cluster ID), *17_wtf_well_sy.csv* (Sy_median), and *01_wells_clean.csv* (mean depth for h_disp). Scenario perturbations use the Option 3 monthly formulation: each scenario modifies the SSM monthly flux Δh = β₁·P_eff − β₂·PET − β₃·h_disp by changing the rainfall reaching the water table (interception), the β₂ multiplier (canopy transpiration), or the PET and P scaling (climate). The flux difference is multiplied by Sy and converted to mm water equivalent per month. The same Option 3 engine is used in *scraping_common.compute_scenario_bars()* (the suite-shared scenario function) and by Script 21 (the cross-pipeline forestry scenarios chapter, S.14).

The observed scraping value is computed differently --- directly from the paired BACI step at CEH36, converted to volumetric via Sy. This is the like-for-like volumetric equivalent of the observed empirical step rather than an SSM-derived counterfactual.

The live monthly scenario bars at CEH36 give (annual-mean forcing): scraping (observed) +45.2 mm/month, clearfell (hypothetical) +15.4, thinning 50 % (hypothetical) +7.7, broadleaf (hypothetical) +4.5, climate-dry −13.8, climate-wet +7.7. Under summer (July--September) forcing: clearfell +13.5, thinning +6.7, broadleaf +2.9, climate-dry −14.4, climate-wet +7.8. The forestry scenarios are *hypothetical* in the sense that CEH36 is in C3 (not forested under current land use); the question they answer is "what would each intervention have produced at CEH36's hydrogeological setting if CEH36 were forested?" --- a like-for-like comparison framework, not a prediction.

**Two forcings, and the off-site scraping drawdown.** The scenario dict is computed twice --- once under annual-mean P and PET (*09d_01*) and once under summer (July--September) P and PET (*09d_02*) --- so the two figures are genuinely distinct rather than a single forcing re-expressed. Both are volumetric and directly comparable. Each figure also carries a modelled *off-site* scraping bar: the neighbour drawdown the scrape drain imposes on the surrounding water table, from the same steady-state drain cone that feeds the Script 20 spatial maps (edge magnitude H₀ anchored to the measured CEH36 response, decay length λ read live from *20_report_numbers.csv*, λ = 230 m). The bar is drawn at 100 m; a dark reference line across it marks the milder drawdown at 250 m (near the nearest real uphill well, 247 m). The 100 m point lies inside the near field the 88-well network cannot resolve, so this bar is explicitly modelled and captioned as such. Because the summer figure is an equilibrium response to summer forcing and *not* a summer minimum, the observed paired-BACI summer-minimum shift at CEH36 (+165 mm) is reported in the caption for context rather than plotted as a bar.

Site-specific choices.

-   **CEH36's own well-level Sy rather than the cluster median.** CEH36's WTF Sy is closer to its actual hydrogeology than the C3 cluster median. Cluster medians enter the per-cluster scenario bars in 09b's chart; the per-well scenario chart here uses the per-well Sy for sharper representation of CEH36's specific response.
-   **Forestry scenarios as hypothetical at CEH36.** CEH36 is in C3 (unforested at the time of scraping; the surrounding compartment was clearfelled in December 2017). Reporting "clearfell at CEH36" as a hypothetical lets the reader compare the monthly flux change a clearfell *would* have produced at this hydrogeological setting against what the scraping actually achieved.

Outputs.

  --------------------------------------------- ---------------------------------------------------------------------------
  Output                                        Description
  09d_01_scenario_comparison.{csv,jpg}          Equilibrium volumetric scenarios under annual-mean forcing at CEH36
  09d_02_summer_scenario_comparison.{csv,png}   Equilibrium volumetric scenarios under summer (Jul--Sep) forcing at CEH36
  --------------------------------------------- ---------------------------------------------------------------------------

### []{#anchor-191}[]{#anchor-192}[]{#anchor-193}Sub-script 09e --- Robustness

**Motivation.** Three independent estimates of the CEH36 Pure-Scraping step change confirm that the headline +0.129 m benefit is not an artefact of any single method's assumptions --- specifically not an artefact of CEH4's own progressive deepening, which is the most plausible single-source contamination of the paired BACI estimate.

**Methodology.** Three estimators on the same CEH36 series:

1.  **Raw paired BACI.** CEH36 minus CEH4, averaged over the baseline era versus the Pure Scraping era. The simplest possible estimator.
2.  **Synthetic control.** CEH36 minus a weighted composite of donor wells from *DONOR_CANDIDATES* (eleven candidate wells outside the scraping influence --- CEH1, CEH2, CEH5, CEH6, CEH9, CEH11, CEH16, CEH17, CEH19, CEH22, CEH24). Donor weights are fitted by OLS on the pre-scraping baseline, then the same weighted composite is computed across the full record. The step is the post-scraping minus pre-scraping mean of the (CEH36 − synthetic) gap series.
3.  **SSM forward residual.** The SSM is calibrated on CEH36's pre-2015 baseline via OLS on *Δh = β₁·P − β₂·PET − β₃·(z₀ + h_prev)* (with HEADLINE_LAG = 0), then iterated forward from the last baseline observation as an autonomous forecast: at each month, the predicted Δh is added to the previous predicted level. The residual (observed minus predicted) over the Pure Scraping era is the step change.

The live estimates: raw BACI +0.129 m, synthetic control +0.137 m (with 11 donors), SSM forward residual +0.081 m. The first two are tightly convergent (within 7 mm); the SSM forward residual gives a noticeably smaller estimate, partly because the model's drainage feedback term iteratively brings the predicted level back toward equilibrium as the post-2015 elevation rises, absorbing some of the observed step into the forecast trajectory. The methodological point is that all three are positive and substantial: the +0.129 m benefit is not an artefact of CEH4's deepening, which only affects the raw BACI estimate.

Outputs.

  ----------------------------------- ------------------------------------------------------------
  Output                              Description
  09e_report_numbers.csv              The three step estimates with units and notes
  09_scrape_08_ceh36_robustness.png   Three-panel: gap series, SSM forward residual, summary bar
  ----------------------------------- ------------------------------------------------------------

### []{#anchor-193}[]{#anchor-194}[]{#anchor-195}Suite-level methodology

**The era system.** Two intervention dates --- April 2015 (scraping at CEH36) and December 2017 (clearfell of the surrounding compartment) --- are the principal era boundaries for the scraping site itself. A third event --- the October 2023 second scraping at CEH18 and CEH21 --- defines an additional boundary for those two wells only. Era structures are therefore well-specific: CEH36 and CEH4 (its paired control) have three eras (Baseline, Pure Scraping, Felling Pulse); CEH18, CEH21, and CEH22 have three eras with different structure (Baseline, Felling Pulse or Coastal Drawdown, After Scraping). The per-well era windows are encoded in *scraping_common.WELL_ERAS* as start-inclusive, end-exclusive tuples and propagate identically across 09a, 09c, 09d, and 09e.

*scraping_common*\*\* as the shared infrastructure.\*\* The five sub-scripts import their well groups, era boundaries, intervention dates, climate-control list, donor candidates, data loaders, and the scenario-bar engine from a single module. Specifically: *SCRAPING_DATE*, *INTERVENTION_DATE*, *SCRAPING_DATE_2*, *WELL_ERAS*, *IMPACT_WELLS*, *PAIRED_CONTROLS_MAP*, *CLIMATE_CONTROLS*, *DONOR_CANDIDATES*, *TIER1_WELLS*, *TIER2_WELLS*, *SUMMER_MONTHS*, and the helpers *load_scraping_data()*, *load_cluster_params()*, *load_summer_climate()*, *compute_scenario_bars()*, and *compute_scenario_bars_from_params()*, plus *scenario_cluster_sy()* (used to render the empirical scraping bar on the volumetric axis) and *load_annual_climate()* (added v1.5.0, the annual-mean companion to *load_summer_climate()* used by 09d's annual-forcing figure). The former flux→summer-minimum helpers (*summer_amplification_factors()*, *flux_to_summer_min_mm()*, *scenario_summer_min_bars()*) remain in the module but are unused after the 2026-07-02 volumetric re-basis. The BACI structure, era boundaries, well-group memberships, and scenario engine are defined once and propagate consistently. *scraping_common.py* is the scraping-suite analogue of *clearfell_common.py* (S.7).

### []{#anchor-195}[]{#anchor-196}[]{#anchor-197}Site-specific choices and rationale (suite-level)

-   **CEH36 is the single scraped well.** The 2015 ground-lowering was a localised 0.3 ha excavation at one well. CEH18 and CEH21 are secondary impacts only by virtue of the 2023 second scraping; in the headline 2015 analysis they are tier-2 impact wells in the sense of being adjacent to forest management but not themselves scraped.
-   *scraping_common.WELL_ERAS*\*\* defines well-specific era windows.\*\* Different wells experience different eras because the 2023 second scraping affects CEH18 and CEH21 but not CEH36 or CEH4. The era system encodes this directly rather than imposing a uniform per-well era structure that would conflate the second-scraping signal with the felling-pulse era at the directly-scraped well.
-   **Climate-only control list (***CLIMATE_CONTROLS = ceh9, nw7, nw6, nw5, wmc2***).** Five wells across the climate-control set in *clearfell_common* (the same wells used as Climate Ctrl in S.7's clearfell BACI). The choice keeps the regional baseline consistent across the two intervention analyses.
-   **The propagation-analysis distance bands (uphill 247--776 m, control 852--1070 m).** Set empirically from the well-location data. The uphill band starts at CEH31 (247 m, the nearest uphill well) and extends to CEH1 (776 m, the most distant well that still sits within the local hydraulic-gradient catchment of CEH36). The control band is everything beyond ≈850 m --- far enough that the controls share regional climate forcing but are outside the scraping's gradient reach.
-   **Provenance-aware summer minima.** 09c consumes *01_wells_provenance.csv* (S.1) and applies a *min_measured=2* rule per (well, year): a Jun--Sep row whose summer series contains fewer than two measured months is dropped from the per-well summer-minima table, on the principle that a year with effectively no measured Jun--Sep data cannot honestly supply a summer minimum however well the wider record bridges. The *min_measured=2* choice is the same value used by 10d in the clearfell suite; the consistency is deliberate, since the two scripts share *clearfell_common* / *scraping_common* infrastructure and use the same five climate-control wells. The new *n_interpolated* column on *09c_01_summer_minima.csv* flags any surviving row whose summer minimum was selected from a series containing at least one *limit=1*-interpolated month, so reviewers can see which year's value rests on a single-missed-visit gap-fill versus an entirely-measured Jun--Sep series.

### []{#anchor-197}[]{#anchor-198}[]{#anchor-199}Limitations and known caveats (suite-level)

-   **Single scraped well in the headline.** CEH36 is the only well where ground was actually lowered in 2015. WMC3 in the clearfell suite is similarly constrained, but here the constraint is even tighter --- at the scraped well the n = 1 limit is structural to the intervention, not just to the network. Inference about scraping's effects is necessarily about *this* site rather than scraping as a general intervention.
-   **The pure-scraping window is short.** Roughly 32 months between April 2015 and December 2017. Per-well SSM fits on this window have wide CIs at the per-well level. The reported step changes are robust at the cluster-mean level (09b) and at the headline CEH36 BACI (09a, 09e); per-well shifts in the propagation analysis are noisy.
-   **The propagation analysis attributes coefficient changes to scraping rather than to concurrent change.** The split-window design assumes that the only systematic change between the pre- and post-scraping windows is the intervention itself. Climate-driven coefficient drift between the windows is netted out by the BACI correction against distant controls, but other concurrent processes --- gradual coastal retreat, undocumented forestry activity, instrumentation changes --- are partially absorbed into the correction and partially attributed to the intervention.
-   **The October 2023 second scraping affects CEH18 and CEH21.** Era 3 effects at these wells in 09a, 09c and the propagation analysis are taken up as supplementary; they do not alter the headline at CEH36.
-   **The SSM forward-residual estimator in 09e gives a smaller step than raw and synthetic estimators.** All three are positive and substantial, but the SSM forward residual at +0.081 m is materially below the raw BACI (+0.129) and synthetic control (+0.137) estimates. The most plausible source of the divergence is the drainage-feedback term iteratively absorbing the elevated post-2015 water table back toward equilibrium across the forecast horizon; the divergence is a property of the estimator rather than evidence the step is smaller than reported.

### []{#anchor-199}[]{#anchor-200}[]{#anchor-201}Outputs (consolidated)

  --------------------------------------------- ------------ --------------------------------------------------------------------------------------------------------------------
  Output file                                   Sub-script   Description
  09_scrape_01_full_parameters.csv              09a          Per-well, per-era SSM coefficients
  09_scrape_02_beta3_significance.csv           09a          Isolated β₃ estimates with CIs
  09_scrape_03_baci_shifts.csv                  09a          Paired BACI step changes
  09_scrape_04_net_benefits.csv                 09a          Net benefits vs CEH21
  09_scrape_04b_beta3_era_summary.csv           09a          Formatted β₃ era summary (Table 6 source)
  09_tier1_final_cusum.csv                      09a          Tier 1 CUSUM terminal values
  09_scrape_05_tier1_background_drift.png       09a          Tier 1 BACI + CUSUM figure
  09_scrape_06_tier2_scraping_signal.png        09a          Tier 2 BACI + CUSUM figure
  09_scrape_07_beta3_confidence.png             09a          β₃ era estimates with CIs
  09_scrape_report_numbers.csv                  09a          All citable §4.5 values
  09b_01_individual_well_baci.csv               09b          Per-well BACI-corrected shifts
  09b_02_centroid_summaries.csv                 09b          Group centroid shifts
  09b_03_ceh36_equilibration.jpg                09b          CEH36 equilibration trajectory
  09b_04_scenario_comparison.{csv,jpg}          09b          Cross-cluster scenario chart
  09b_05_summer_scenario_comparison.{csv,png}   09b          Volumetric cross-cluster scenario comparison (equilibrium mm water-equiv/month)
  09b_report_numbers.csv                        09b          Citable §4.5 values
  09c_01_summer_minima.csv                      09c          Per-well, per-year summer minima
  09c_02_summer_minima_shifts.csv               09c          Welch t-test results (both controls)
  09c_03_summer_minima_climate_ctrl.png         09c          Three-panel summer minima vs climate control
  09c_04_summer_minima_paired.png               09c          Paired-control comparison
  09c_report_numbers.csv                        09c          Citable §4.5 values, plus the equilibration peak, residual plateau, and decay slopes (climate and paired controls)
  09d_01_scenario_comparison.{csv,jpg}          09d          Equilibrium volumetric scenarios under annual-mean forcing at CEH36
  09d_02_summer_scenario_comparison.{csv,png}   09d          Equilibrium volumetric scenarios under summer (Jul--Sep) forcing at CEH36
  09e_report_numbers.csv                        09e          Three-method robustness step estimates
  09_scrape_08_ceh36_robustness.png             09e          Three-panel robustness figure
  --------------------------------------------- ------------ --------------------------------------------------------------------------------------------------------------------

### []{#anchor-201}[]{#anchor-202}[]{#anchor-203}Where the result appears in the report

-   §4.5 *Scraping intervention* --- the entire section draws on this suite.
-   Table 6 --- per-well β₃ era coefficients, sourced from *09_scrape_04b_beta3_era_summary.csv*.
-   Figures 17--20, 22--24, 26, 27 --- multiple figures from the suite.

### []{#anchor-203}[]{#anchor-204}[]{#anchor-205}Cross-references

-   **F.3** --- SSM equation, displacement formulation, sign conventions, *model_utils.fit_ssm()*. All five sub-scripts fit SSMs through this interface (09a directly via OLS using the same design matrix; 09b, 09e via *fit_ssm()*).
-   **F.4** --- *pipeline_params.py* consolidation. 09b and 09d both prefer the consolidated params file (*pipeline_params.load_params()*) and fall back to individual loaders if it is absent.
-   **F.5** --- *scraping_common.py* is documented in detail in this chapter's *Suite-level methodology* section; the front-matter listing is a brief role summary.
-   **S.1** --- input data preparation, well-cleaning policy, *01_wells_provenance.csv* (consumed by 09c via *scraping_common.load_scraping_data()* for the *min_measured=2* summer-minima rule).
-   **S.3** --- produces *03_master_data.csv* and *03_03_cluster_mechanistic_coefficients.csv*, consumed by 09a (per-well coefficients) and the *load_cluster_params()* loader (cluster-level coefficients).
-   **S.7** --- Script 10 clearfell BACI suite, the parallel intervention analysis. *clearfell_common.py* supplies the β₂ multipliers used by 09d's scenario calculations via *load_clearfell_b2_multiplier()*. The interpolation policy moves this chapter's 09c summer-minima step and S.7's summer-only Forest × Impact step in opposite directions, because the two analyses use the same NW6 / NW7 climate-control wells in different roles; the §S.7 chapter expands on the clearfell-side picture.
-   **S.12** --- Script 17 WTF Sy, consumed by 09d (CEH36-specific Sy) and by *load_cluster_params()* (cluster-median Sy).
-   **S.14** --- Script 21 forestry scenarios; uses the same *scraping_common.compute_scenario_bars()* engine for cross-cluster forestry projections.

Spring-mean companion metric (Script 09c v1.5.0). Alongside the summer minimum, Script 09c computes an annual spring mean (Mar--May) through the identical dual-control BACI code path (a \_METRICS spec list driving \_run_metric()). Both metrics reduce a well to one value per year, so the spring mean carries the same N, wells and controls as the summer minimum at no power cost; being a three-month mean rather than an extreme-order statistic it is the less noisy of the two. The spring season and its strict 3-of-3 completeness rule are the MSL_SPRING_MONTHS / MSL_MIN_MONTHS_PER_SPRING constants (F.4), sourced via clearfell_common. Outputs 09c_05--09c_08 (spring means, pre/post shifts, and the two spring figures) mirror the summer set; the spring figures carry no SD15b/SD16 threshold bands, which are summer slack-viability limits with no spring equivalent. Spring rows append to 09c_report_numbers.csv. Results are collected in Supplementary Note S8.

## []{#anchor-205}[]{#anchor-206}[]{#anchor-207}S.7 Script 10 suite (a--m) --- Clearfell BACI

Step 10 / 30 (sub-scripts 10a--10m). Phase 3 --- Model Diagnostics and Intervention Analysis.

The Script 10 suite is the second of the two management-intervention analyses at the warren. Where Script 09 (S.6) analyses the April 2015 scraping at CEH36, Script 10 analyses the December 2017 clearfell of approximately 0.6 ha of Corsican pine (*Pinus nigra* var. *maritima*) inside the western forest block. The intervention removed canopy interception and transpiration over a single compartment with the explicit aim of restoring dune-slack hydrology in the post-felled compartment and the adjacent slacks. The suite is the entire methodological evaluation of that intervention: thirteen sub-scripts orchestrated by *run_10_clearfell.py*. Eleven contribute to the main results chain; two sit outside it --- 10c, which produces supplementary spatial diagnostics of the C4--C5 forest partition, and 10m, a display figure that presents the WMC3 impact well against the forest-control mean across all three interventions.

The published BACI design uses a five-tier comparison network of 17 wells: one impact well inside the felled compartment (WMC3), four edge wells immediately adjacent (CEH31, CEH20, CEH30, CEH16), five C4 Main Forest interior controls (CEH32, CEH34, CEH33, NW10, CEH2), two C5 Coastal Forest controls (CEH19, CEH17), and five C3 Western Residual climate-only controls (CEH9, NW7, NW6, NW5, WMC2). The four FE wells inside the felled compartment (FE1--FE4) are not in the canonical network because they lack pre-intervention baseline records; FE1 and FE2 are reintroduced by 10h via donor-regression synthetic extension. NW8 and NW8B are excluded from all analyses because of data-quality issues in their pre-intervention records. CEH42 was considered for the climate tier but its 3.4-year pre-felling baseline is too short, so it is excluded as well.

The suite asks eleven questions across its eleven primary sub-scripts. How is the CEH34 Forest-control record reconciled with the pre-fell window, given that its August-2010 installation predates the January-2011 window start --- CEH34 enters the centroid on observed data, with a donor-regression hindcast of its 2006--2010 record retained only for reproducibility (10i)? Did the clearfell raise the mean monthly water table inside and adjacent to the compartment, after controlling for climate forcing and the residual influence of the earlier scraping (10a)? Where in the network is the step-change spatially concentrated, and where is it absorbed by background drift (10b)? Did the clearfell improve the ecologically critical summer-minimum water table at impact and edge wells (10d)? Which SSM pathway --- recharge sensitivity β₁, atmospheric draw β₂, or drainage feedback β₃ --- shifted at the felled and edge wells after the intervention, as a mechanistic-direction diagnostic alongside the statistical step estimate (10e)? Does the headline ANCOVA result survive being recomputed by independent estimators --- per-well SSM forward residual, and zone-level synthetic control (10f)? What do the diagnostic checks --- NW10 broadleaf succession, a radial transect from the compartment, rolling-window SSM coefficients --- say about the trajectory of the recovery (10g)? Does the result strengthen, weaken, or hold when the synthesised FE-well records are added back into the impact centroid (10h)? Does the result survive a direct Impact-vs-Edge contrast that uses only the closest spatial control and identifies the felling step without the easting × time covariate that the headline ANCOVA relies on (10j)? And does a single four-zone panel model --- fitting the Impact, Edge and a shielded second-control western-dune zone against the Forest control in one internally-consistent regression --- agree on the felling step at monthly resolution (10k) and at the summer minimum (10l)? The twelfth and thirteenth sub-scripts sit outside this question chain: 10c, a supplementary spatial diagnostic of the C4--C5 forest partition, and 10m, a display figure that plots the WMC3 impact well and the forest-control mean in displacement units across the 2015 scraping, 2017 clearfell, and 2023 re-scraping --- with per-era difference-in-differences steps on the gap series and the 10a ANCOVA clearfell headline carried as an on-figure note so the raw and climate-corrected steps cannot come adrift. The DiD steps in 10m are raw (not climate-corrected) and should not be read as validating or quantifying the spatial propagation of scraping to WMC3; they are display values that track the well's observed trajectory, not a separate causal analysis.

The headline ANCOVA-BACI result is reported in the main report as Table 7 and Figures 28, 30 and 31 (§4.6 *Clearfell intervention*); spatial maps (Figures 25, 34), summer minima (Figure 32), coefficient shifts (Figure 35), the radial transect (Figure 36), and the supplementary forest-zone analysis (Table 16) draw on the other sub-scripts. The compositional mapping is recorded in the live *PIPELINE_README.md* table. Sub-script 10m produces a display figure (*10m_02_wmc3_baci_dual.png*) used for internal interpretation and, if placed, §4.6; it introduces no new reported statistic beyond the 10a ANCOVA headline it visualises (figure number TBC with Martin).

### []{#anchor-207}[]{#anchor-208}[]{#anchor-209}Inputs (suite-shared)

  ------------------------------------------------------- ------------ ----------------------------------------------------------------------------------------------------------
  Input file                                              Source       Used by
  *01_wells_clean.csv*, *01_wells_extended.csv*           Script 01    All sub-scripts
  01_climate.csv                                          Script 01    10a, 10d, 10e, 10f, 10g, 10h, 10j, 10k
  03_master_data.csv                                      Script 03    All (per-well coefficients, locations, cluster IDs)
  Well_info.csv                                           raw data     10h (FE well locations not in master)
  07_coeff_maps_data.csv                                  Script 07    10c
  06_pear_membership_audit_sitewide.csv                   Script 06    10c
  *Features.kml*, *clearfell.kml*, *newborough_dem.tif*   raw data     10b, 10c (spatial maps)
  *10a\_\** outputs                                       Script 10a   10f, 10h (ANCOVA comparison)
  10a_report_numbers.csv                                  Script 10a   10m (ANCOVA clearfell headline for on-figure note; 10m must run after 10a)
  10d_01_summer_minima.csv                                Script 10d   10j (annual-summer-minimum contrast), 10l (four-zone summer minima)
  10e_01_coefficient_shifts.csv                           Script 10e   downstream Scripts 19, 21 via *load_clearfell_b2_multiplier()*
  10i_01_ceh34_hindcast.csv                               Script 10i   10a, 10b, 10e, 10h via *clearfell_common.apply_ceh34_hindcast()*; 10d, 10f, 10j, 10k, 10l do not consume
  ------------------------------------------------------- ------------ ----------------------------------------------------------------------------------------------------------

All loading goes through *clearfell_common.load_clearfell_data()*, which merges the reference and extended well frames, normalises column names to lowercase, and validates the five tiers against the live data. Per-well locations are sourced first from the master data, with *Well_locations_height.csv* as a fallback for wells not in the reference network.

### []{#anchor-209}[]{#anchor-210}[]{#anchor-211}Sub-script 10a --- Three-counterfactual ANCOVA-BACI

**Motivation.** This is the headline analysis. The question is whether the December 2017 clearfell produced a step-change in the water-table displacement of the impact and edge wells relative to nearby unaffected controls, after climate forcing and the residual scraping effect are controlled out.

**Methodology.** 10a runs the same ANCOVA model six times --- three control definitions (Forest, Climate, Combined) crossed with two target zones (Impact, Edge) --- yielding six ANCOVA results per intervention. The three controls are:

-   **Forest**: the five C4 Main Forest interior wells (CEH32, CEH34, CEH33, NW10, CEH2). The cleanest counterfactual mechanistically: matched canopy, matched substrate, matched climate band.
-   **Climate**: the five C3 Western Residual climate wells (CEH9, NW7, NW6, NW5, WMC2). Open-dune wells under shared climate forcing; the unconfounded climate baseline.
-   **Combined**: all 12 Forest, Coastal, and Climate control wells pooled. Larger sample, less mechanistically targeted.

(Note: a standalone "Coastal Forest" counterfactual is *not* run in 10a --- the C5 Coastal wells enter only through the Combined pool. The two Coastal wells are mechanistically distinct from the C4 interior, with lower β₂ and a confounding coastal-retreat signal that 10b's climate correction is designed to absorb. Treating C5 as a third standalone counterfactual would give it more weight in the inference than its sample size and confound structure can carry.)

For each (control, zone) pairing the script:

1.  Computes the BACI displacement timeseries: target-zone monthly mean minus control-zone monthly mean.
2.  Adds a centred climate-water-balance (CWB) covariate, computed by *compute_cwb()* as the demeaned cumulative *(P − PET)* anomaly in mm.
3.  Adds a distance-weighted scraping covariate as the *difference* of target and control centroid weights, with weight *exp(−d / λ)* and λ = 300 m by default. The differential form is essential because the BACI itself is target-minus-control.
4.  Adds the December 2017 felling dummy, the CWB × felling interaction, and where geometrically valid, an easting × time interaction that absorbs the coastal-retreat gradient.
5.  Adds a sensitivity to the October 2023 re-scraping (Model 3 includes the second scraping pulse; the difference in AIC from the baseline Model 2 records whether the second pulse measurably improves the fit).

The easting × time term is included only when the easting range across the union of target and control wells exceeds 200 m. For the Forest control runs, the C4 wells cluster too tightly in easting for the term to be informative, and it is dropped. For the Climate and Combined runs the range is large enough to fit the gradient cleanly. This is automatic --- *build_ancova_frame()* writes a boolean *has_easting* flag and *run_ancova()* reads it.

Sensitivity is checked by re-running every (control, zone) pairing at λ = 200 m and λ = 500 m. The headline values are at λ = 300 m, which sits roughly at the centroid of the within-network distances.

The headline output table records the felling step (in metres), its 95 % confidence interval, the scraping step, the easting coefficient, R², the model N, the Oct 2023 step and its AIC differential, and the climate-background subtraction in mm. The headline result is the Forest-control step at each zone:

-   **Impact (WMC3):** +113 mm, 95 % CI \[+42, +183\], p = 0.002, R² = 0.241, N = 163.
-   **Edge (four wells):** +29 mm, 95 % CI \[−21, +80\], p = 0.253, R² = 0.457, N = 159.

The Climate-control runs give a small non-significant Impact step (−14 mm, p = 0.562) and an Edge step of −106 mm, 95 % CI \[−167, −46\], p \< 0.001. The easting × time correction is significant at p \< 0.001 in both Climate runs (and in the Combined runs) but is dropped in the Forest runs by the 200 m easting-range rule (see *Site-specific choices* below). The Combined-control runs give an Impact step of +69 mm (p \< 0.001) and an Edge step of −20 mm (p = 0.128), pooling Forest, Coastal, and Climate controls; the Combined Impact estimate is tighter than either Forest or Climate alone because of the larger control sample. Each (control, zone) pair is exported as a row in *10a_01_ancova_comparison_table.csv*. Full coefficients, easting × time effects, and the per-pair model diagnostics are in *10a_02_ancova_full_coefficients.csv*. The corrected BACI displacement timeseries --- observed minus the fitted climate and easting effects --- is exported in *10a_03_baci_timeseries.csv* and underlies the §4.6 figures.

The Climate-control Edge step is small in magnitude but its sign is opposite to the Forest-control Edge step. The two controls answer different counterfactual questions: the Forest control isolates the clearfell signal against canopy-matched substrate-matched wells, while the Climate control compares the forest-edge wells against open-dune climate-baseline wells that sit further from the coast. The negative Climate-Edge step reflects residual coastal-zone drift between the C3 climate wells, which sit further west and away from the coast, and the four C4-edge wells, which sit closer to the receding coastline. The easting × time correction in the ANCOVA absorbs the linear spatial gradient across the network and is significant at p \< 0.001 in the Climate runs, but it does not remove the residual zone-level drift between two well clusters at different distances from a coastline retreating episodically through the post-felling era (Script 25 documents the gradient in detail).

**Directly-fitted summer ANCOVA step.** 10a v1.3.0 also fits the Forest-control Impact specification on a Jun--Sep subset (N = 52 months), under the same model terms as the annual headline. The fitted summer step is +50 mm, 95 % CI \[−68, +168\], p = 0.41, R² = 0.314 --- not significant at conventional thresholds. A CWB-dropped sensitivity variant (+123 mm, p = 0.058, R² = 0.098) is emitted to *10a_report_numbers.csv* as *ANCOVA_Forest_Impact_clearfell_step_summer_noCWB*; the full specification is preferred on ΔAIC grounds.

The annual Forest × Impact step is the durable headline of the clearfell analysis. Its sample size (162 months) carries the inference. The Jun--Sep subset is only 52 months and the same specification on that subset does not reach significance. The summer signal corroborates the direction of the annual step but is not retained as a separate statistical claim. The arithmetic-construct fallback (BACI_ANNUAL × 1.5034) that was retained transiently as a Script 21 fallback and removed in Script 21 v1.0.3 / 10a v1.3.0 is therefore not replaced by a summer-specific scaling.

**Curvature (CWB² × felling) sensitivity variant.** The headline ANCOVA fits a *linear* CWB × felling interaction, which tests whether felling changed the linear sensitivity of the water table to climate forcing --- the canopy-buffering hypothesis in its simplest form. That interaction is non-significant at both Forest-control zones (Impact p = 0.40, Edge p = 0.16): on a whole-range linear slope, the pre- and post-felling climate sensitivities are not distinguishable. A linear slope is, however, a blunt instrument for a hypothesis about climate *extremes* --- a buffering effect concentrated at the wet or dry tails can average to near-zero across the full CWB range. 10a v1.4.0 therefore also fits a non-linear extension on the full-data Forest-control Impact and Edge frames: the headline design matrix plus a centred CWB² main effect and a CWB² × felling interaction. The CWB² × felling term is significant at both zones (Impact −2.75 × 10⁻⁶ m mm⁻², p = 0.016; Edge −2.22 × 10⁻⁶ m mm⁻², p = 0.008), the curvature model improves on the linear model by ΔAIC −4.2 (Impact) and −10.7 (Edge), and the joint F-test of the two added curvature terms is significant at both zones. The CWB² *main* effect is non-significant at both zones --- the pre-felling relationship is linear; only the post-felling relationship bends. The negative interaction sign means the post-felling response is concave in CWB, i.e. the felling uplift is larger in dry (low-CWB) conditions. This is a reported sensitivity variant only: the headline clearfell step and the linear model are unchanged, and the curvature coefficients, the re-referenced clearfell step (which differs from the headline step because the step is evaluated at mean CWB under a curved fit --- +146 mm Impact, +50 mm Edge), the curvature-model R², the ΔAIC, and the joint-F statistic are emitted to *10a_report_numbers.csv* under the *ANCOVA_Forest\_{zone}\_coeff_cwb2_x_fell* / *\_curv\_\** keys. The result indicates the felling response is climate-state-dependent in a way the linear interaction averages away; it is consistent with --- but not on its own proof of --- a dry-period canopy-buffering mechanism, since climate-state-dependence has alternative explanations (post-felling non-stationary drift, the coastal-retreat gradient) that the variant does not exclude. The main report (§4.6) reports it neutrally as a flagged preliminary finding, not as a confirmed buffering effect.

### []{#anchor-211}[]{#anchor-212}[]{#anchor-213}Sub-script 10b --- Spatial step-change maps

**Methodology.** For each well in the warren-wide network with at least six observations in each of the three eras (pre-scraping, post-scraping, post-felling), the script computes era-mean depths and two step-changes: a scraping step (post-scrape minus pre-scrape) and a felling step (post-felling minus post-scrape). The full network of approximately 90 wells is rendered as an IDW-interpolated surface on a 40 m grid with the standard DEM hillshade and KML feature overlay (*map_utils.add_idw_surface*, *load_dem_hillshade*, *add_kml_features*). Four publication figures result: raw and climate-corrected versions of both step-changes.

The climate correction uses the median step at a deliberately chosen subset of four C3 western wells (NW5, NW6, NW7, CEH1) --- intentionally different from 10a's full C3 climate-control set. These four wells share both the western climate signal and the coastal-retreat boundary position of the intervention zone, so subtracting their median step from every well removes climate plus coastal-retreat drift in a single operation. The script's docstring records this choice and the per-well counts at each era are exported.

  ------------------------------------------------------------------- -----------------------------------------------------------------------
  Output                                                              Description
  10b_spatial_step_data.csv                                           Per-well era means, step values, climate-corrected steps, well counts
  *10b_spatial_scrape_raw.png* / *10b_spatial_scrape_corrected.png*   Scraping era maps
  *10b_spatial_fell_raw.png* / *10b_spatial_fell_corrected.png*       Clearfell era maps
  ------------------------------------------------------------------- -----------------------------------------------------------------------

The clearfell-era corrected map is the canonical Figure 34 in the main report; the scraping-era equivalent is Figure 25. The per-well step CSV is also consumed by Script 09b (scraping propagation) for the network-wide propagation modelling.

### []{#anchor-213}[]{#anchor-214}[]{#anchor-215}Sub-script 10d --- Summer minima (dual-control)

**Motivation.** The annual June--September minimum water table is the ecologically critical metric for dune-slack vegetation. A clearfell that raises the mean monthly water table but leaves the summer minimum unchanged delivers a different kind of result than one that does both. 10d evaluates the summer-minimum response separately and through two independent control structures.

**Methodology.** For each well in the 17-well network, *annual_summer_minimum()* extracts the deepest (most negative) June--September water level per year, requiring at least two observations in the window. The script then compares the well's summer-minimum series against two control centroids --- the Forest control centroid (mean of the five C4 wells' annual minima, requiring at least two wells per year) and the Climate control centroid (mean of the five C3 wells) --- yielding a "gap" series per well per control. Pre-felling years (2007--2017) are compared with post-felling years (2018--2025) by Welch t-test on the gaps.

*annual_summer_minimum()* and *forest_control_centroid_summer_min()* consume *01_wells_provenance.csv* (§S.1) and apply a *min_measured=2* rule: a (well, year) summer minimum is admitted to the panel only when at least two of the four Jun--Sep months are actual field measurements rather than interpolations. Single-month interpolations (the residuals under the *limit=1* cleaning policy) are allowed to contribute, but a *n_interpolated* column in *10d_01_summer_minima.csv* flags every (well, year) row that carries at least one such cell. The rule excludes (well, year) combinations whose summer minimum would otherwise be supported only by interpolated values --- most notably at WMC3, NW6, and NW7 where Jun--Sep 2019 was entirely unmeasured.

A pooled mixed-effects model with a random intercept per well (*statsmodels.regression.mixed_linear_model.MixedLM*) gives a tier-level clearfell-attributable step with proper uncertainty. The Impact tier (one well, WMC3) falls back to OLS.

The result is reported with care because it contains both forest-positive and forest-negative components: the mean monthly recovery in 10a is statistically significant, but the summer-minimum signal at impact wells is null and at edge wells is a negative shift that does not reach significance at α = 0.05. Specifically:

-   **Forest-control mixed model: Impact step = −1 mm, p = 0.99 (n = 1, OLS).** No improvement in summer minima at the impact well.
-   **Forest-control mixed model: Edge step = −64 mm, p = 0.12.** The edge-tier summer minima are deeper post-felling than pre-felling relative to the Forest control, but the shift is not significant at conventional thresholds.

The Climate-control mixed-model Edge step is +48 mm (p = 0.28) --- the negative shift seen under the Forest control does not reproduce against the open-dune climate baseline, which is the disconfirmation. The Coastal Control tier shows the largest negative shift across both controls (Forest control: −176 mm, p = 0.059; Climate control: −42 mm, p = 0.31), which is the coastal-retreat signal that Scripts 25 and 10c document at length.

**Clearfell no-decay comparator.** As the matched-currency reference for the scrape equilibration characterised in §S.6 (sub-script 09c), 10d reports the post-felling OLS slope of WMC3's summer-minimum forest-control gap. This is a shape comparator only --- it establishes that the clearfell response carries no post-intervention decay analogous to the scraping relaxation --- and is not a step estimate: the clearfell recovery is a mean-level and monthly effect that is weak in the summer minimum (the non-significant summer step noted above), so the durable-step claim rests on the annual/monthly ANCOVA in 10a, not on this comparator. Plain OLS, no AR(1) correction, subject to the same *EQUIL_MIN_FIT_POINTS* gate as the 09c decay characterisation.

### []{#anchor-215}[]{#anchor-216}[]{#anchor-217}Sub-script 10e --- SSM coefficient shift diagnostic

**Motivation.** The ANCOVA in 10a is the statistical estimate of the clearfell step magnitude. 10e is a complementary *mechanistic-direction* diagnostic: for each well it asks which SSM pathway moved after felling --- recharge sensitivity (β₁), atmospheric draw (β₂), or drainage feedback (β₃) --- and in which direction. It is a qualitative pattern diagnostic, not a second estimator of the step magnitude. The clearfell magnitude result is, and remains, the 10a ANCOVA BACI step.

**Methodology.** For each of the 17 network wells, the SSM frame is built via *build_ssm_frame()* (F.3) and split at the December 2017 felling date into Before and After eras. Both eras are fitted with the canonical no-intercept SSM through *model_utils.fit_ssm()* --- the same Model A form used by Script 03 and described in S.3. The Before fit additionally carries a scraping dummy (1 from April 2015 onward), supplied via the *extra_regressors* keyword of *fit_ssm()*, to absorb the residual scraping influence within the pre-felling baseline; the After fit is the standard three-column SSM. For each well the script computes the per-coefficient deltas Δβ = After − Before and reports them per well and per tier.

The script does **not** attempt to reconstruct or predict the 10a BACI step from the coefficient shifts. A Δβ-projected predicted step (*Δh_predicted = Δβ₁·mean_P − Δβ₂·mean_PET − Δβ₃·mean_h_disp*) is not commensurable with the observed 10a step: the 10a step is the coefficient on a felling dummy in an ANCOVA fitted to the *control-differenced* centroid (target centroid minus control centroid), with regional climate forcing removed by construction, whereas a Δβ projection would be built from single-well, undifferenced, per-era fits with no control subtraction and on a different climate projection basis. Reconciling the two would require absorbing a residual into an intercept shift Δα of unidentified physical content. Script 10e therefore reports the Δβ pattern as a direction-and-sign diagnostic and leaves the step magnitude to 10a; the era fits use the canonical no-intercept form, consistent with the rest of the pipeline.

Under the v1.4.0 fits, the per-tier mean coefficient shifts are: at the Impact tier (WMC3, one well) Δβ₁ = −0.10, Δβ₂ = −0.28, Δβ₃ ≈ 0.00; at the Edge tier Δβ₁ = −0.27, Δβ₂ = −0.03, Δβ₃ = −0.01. The interpretation is qualitative --- the felled and edge wells show a post-felling reduction in recharge sensitivity, with the largest single shift at the Impact well being in β₂ --- and is read as supporting mechanistic context for the 10a result, not as an independent quantification of it.

The β₂ multiplier exported via *clearfell_common.load_clearfell_b2_multiplier()* is a *differenced* tier quantity:

> clearfell_β₂_multiplier = Edge_ratio − Climate_Ctrl_ratio + 1.0

where each "ratio" is the tier mean of *b2_after / b2_before* across that tier's wells. The construction takes the Edge-tier ratio and subtracts the Climate-control-tier ratio to remove background climate drift, recentring the result near 1.0; the thinning multiplier is the half-perturbation. Both values are read dynamically from *10e_01_coefficient_shifts.csv* by Scripts 19 and 21; the previous static-constant approach is retired. *Note: the individual per-tier b2_after / b2_before ratios are differently scaled under no-intercept fits than under intercept-bearing fits --- the raw ratios should not be read as direct canopy-effect magnitudes; only the Edge-minus-Climate differenced quantity is interpreted.*

### []{#anchor-217}[]{#anchor-218}[]{#anchor-219}Sub-script 10f --- Robustness

Two independent estimators broadly support the ANCOVA result at the Impact tier.

**SSM forward residual.** For each network well, the SSM (no scraping dummy, three columns) is calibrated by OLS on the pre-scraping era (where available, requiring at least 36 calibration months) and iterated forward through the scraping and felling eras to generate a counterfactual trajectory. The residual (observed minus predicted) is normalized by subtracting the mean of the control-tier residuals. The era-mean residuals are tested via Welch t-test. The Impact mean step is +56 mm (positive, but smaller in magnitude than 10a's +113 mm Forest-control step at WMC3; the SSM forward-residual estimator is a per-well calibration against a counterfactual built from the pre-scraping era and is more sensitive than the ANCOVA to month-by-month variation); Edge mean step is essentially zero (+5 mm), reflecting that the Edge wells are well-explained by their own pre-scraping SSM fit and the felling produces a residual within climate noise --- consistent with 10a's small non-significant Forest-control Edge step.

**Synthetic control.** A donor pool of six wells outside the BACI network (CEH1, CEH5, CEH6, CEH10, CEH11, CEH24) is used to build a synthetic counterfactual at each zone. The donor weights are fitted by OLS on the pre-scraping baseline (no intercept). The gap series (observed zone mean minus synthetic) is segmented at the felling date; the step is the post-felling minus post-scraping gap. The Impact step is +99 mm, p = 0.001; the Edge step is +40 mm, p = 0.233. The three Impact-tier estimators span +56 to +113 mm (SSM forward residual, synthetic control, 10a ANCOVA Forest control). All three are positive; the synthetic-control and ANCOVA results are significant at conventional thresholds, and the SSM forward-residual estimate, though it lies at the low end of the range, is also individually significant (WMC3, p = 0.001). The methodological convergence the script exists to test holds in direction; the magnitude spread is wider than within-rounding, with the SSM residual estimator sitting roughly 57 mm below the ANCOVA headline.

Two independent estimators agreeing with 10a's headline at the Impact tier in direction and broad magnitude is the main message. The Edge tier diverges more across methods, reflecting the larger heterogeneity of edge wells and the differential climate-and-coastal-retreat correction that 10a's full ANCOVA design is built to handle.

### []{#anchor-219}[]{#anchor-220}[]{#anchor-221}Sub-script 10g --- Diagnostics

Three short diagnostics that justify network choices made elsewhere and characterize the trajectory of the recovery.

**NW10 broadleaf trend.** NW10 sits at a broadleaf-pine margin and was included in the Forest Control tier despite being borderline. The script tests its 2019--2025 summer-minimum anomaly trend relative to a pine-interior composite (CEH2, CEH32, CEH33, CEH34). The trend is −46 mm/year, p = 0.024, indicating progressive broadleaf-margin drawdown. The mean 2010--2021 anomaly (+288 mm above the pine composite) confirms NW10's distinctly shallower historical baseline. The trend is documented but NW10's inclusion in the Forest Control tier is retained --- the 2019--2025 drawdown is a real broadleaf-succession signal that the chapter discusses, not a data-quality issue.

**Radial transect.** A three-panel figure plotting WMC3 (45 m from compartment centroid), the four edge wells (152--229 m), and two reference wells (CEH34 at 306 m, CEH2 at 428 m) over time. Panel A shows depth anomaly relative to scrape-era mean as 6-month rolling means; panel B shows zone anomalies relative to the transect mean; panel C is a step-vs-distance scatter. The fitted gradient is −0.4 mm per 100 m (p = 0.186) --- no significant spatial gradient in the felling step across the transect, consistent with a recovery effect spatially concentrated at the compartment edge rather than gradiently dissipating with distance.

**Rolling SSM coefficients.** 48-month rolling-window SSM fits at the Impact centroid (WMC3), C3 (open dune) centroid, and C4 (forest interior) centroid. The diagnostic question is whether the Impact centroid β₁ shifts toward C3 post-felling --- the expected behaviour if the canopy removal restores open-dune recharge sensitivity. The pre-felling Impact β₁ rolling mean is 2.48; post-felling 2.57; the C3 post-felling rolling mean is 3.49. The Impact β₁ rises slightly toward C3 but remains well below the C3 baseline, consistent with partial canopy recovery on a one-compartment, six-year time horizon and with the limited statistical power of rolling 48-month windows applied to a single well.

### []{#anchor-221}[]{#anchor-222}[]{#anchor-223}Sub-script 10h --- Synthetic FE-well extension BACI

**Motivation.** WMC3 is the only impact-zone well that spans all three eras. FE1--FE4 sit inside or at the immediate edge of the felled compartment but have no pre-clearfell baseline (FE1 and FE2 from July 2015, FE3 and FE4 from 2017). The published 10a headline therefore rests on a single impact well. 10h extends FE1 and FE2 backwards using donor regression on Forest Control wells unaffected by the clearfell, then reruns the ANCOVA with these synthetic baselines spliced in. The extension brings the Impact-tier N from one well to three and provides an independent test of the 10a Impact result.

(FE3 and FE4 are not synthesised. Both start in 2017 --- too late for a calibration window with adequate length.)

**Methodology.** Three donor candidates (CEH34, CEH2, CEH33) are jointly regressed against FE1 and FE2 on the pre-clearfell overlap window (July 2015 to November 2017, 29 months). The donor regression is multi-donor OLS with intercept, fitted independently per FE well. The calibrated relationship is then used to hindcast each FE well backward to August 2010, gaining 49 pre-scraping months of synthetic record per well. The calibration R² is 0.998 for FE1 and 0.994 for FE2, with RMSEs of 18 and 25 mm respectively. The synthetic record is spliced with the actual FE observations from July 2015 onward.

Three impact-centroid variants are then run through the identical 10a ANCOVA framework:

-   **Variant A**: WMC3 + FE1 + FE2 (three-well centroid).
-   **Variant B**: WMC3 + FE2 (two-well centroid, excluding FE1).
-   **Variant C**: WMC3 alone (reproduces 10a Impact).

The reason for Variant B is that FE1 sits approximately 20 m outside the clearfell boundary in standing forest, while FE2 is inside the felled compartment. FE1's post-felling divergence is +9 mm (p = 0.15); FE2's is +28 mm (p \< 0.001). Averaging FE1 into the impact centroid dilutes the clearfell signal because FE1 is not actually clearfell-impacted.

  ---------------------- --------- ----------- --------------- ----------
  Variant                Zone      Step (mm)   95% CI          p
  A (WMC3 + FE1 + FE2)   Forest    +80         \[+34, +126\]   \< 0.001
  A                      Climate   −58         \[−118, +2\]    0.062
  B (WMC3 + FE2)         Forest    +97         \[+38, +156\]   0.002
  B                      Climate   −36         \[−90, +17\]    0.188
  C (WMC3)               Forest    +113        \[+42, +183\]   0.002
  ---------------------- --------- ----------- --------------- ----------

Variant C (WMC3-only) is the headline result for the impact tier; it reproduces 10a's Forest-control Impact step (+113 mm, p = 0.002) and is the form quoted as the chapter's primary impact-zone estimate. Variants A and B are robustness checks built on synthetic pre-clearfell baselines for FE1 and FE2 via donor regression on Forest Control wells. Variant B is a two-well centroid (WMC3 at the compartment edge; FE2 inside the compartment) against forested controls, returning a Forest-control step of +97 mm, p = 0.002. Variant A (which adds FE1) gives +80 mm, p \< 0.001 against the Forest control; the script reports it but does not recommend it as a robustness anchor because FE1 sits in standing forest outside the clearfell boundary.

The three Impact-tier variants span +80 to +113 mm against the Forest control, all positive and individually significant. Both synthetic-extension variants are smaller in magnitude than the WMC3-only headline, so the synthetic extension is best read as a robustness check on direction and sign rather than as an independent magnitude estimator. The methodological convergence available from 10h is: the clearfell signal is positive and significant at the Impact tier under every plausible centroid composition, and the WMC3-only step is not a one-well artefact in its sign or its direction. The magnitude attenuation under synthetic-baseline inclusion is noted but not given a physical interpretation in this chapter.

### []{#anchor-223}[]{#anchor-224}[]{#anchor-225}Sub-script 10i --- CEH34 donor-regression hindcast

**Motivation.** CEH34 is a Forest Control well used in the 10a Forest-control centroid and in the 10b spatial step maps. Its monthly record starts on 1 August 2010, later than the August 2010 first observation of several other Forest-control wells. Under the pre-fell window start in force when 10i was written (1 July 2010) this truncation affected the Forest-control centroid directly: including CEH34 with its truncated record either reduced the pre-fell N (and so the precision of the climate-corrected pre-fell mean) or introduced a composition shift around August 2010 as CEH34 joined the centroid. Following the *PRE_FELL_START* migration to 1 January 2011 (*clearfell_common* v1.7.0), CEH34's record start falls before the window and the in-window centroid is no longer truncated; the hindcast splice is retained for cross-version reproducibility and for analyses that opt into the earlier start. 10i removes the original asymmetry by hindcasting CEH34 backward to the pre-CEH34-record window using donor regression on a single donor well from the climate-control set.

**Methodology.** The donor well is CEH9. CEH2 has a stronger empirical correlation with CEH34 (r² = 0.97 against CEH9's r² = 0.89), but CEH2 is itself a Forest Control well that contributes to the BACI Forest Control centroid; hindcasting CEH34 against CEH2 and then adding both to the Forest Control set would amount to upweighting CEH2's contribution to the pre-fell baseline --- a partial double-count. CEH9 sits in the Climate Control tier and is therefore independent of the Forest Control centroid; its slightly weaker correlation reflects the strong site-wide groundwater synchrony at Newborough rather than any methodological weakness. The fit is OLS on the pre-clearfell overlap window (August 2010 to November 2017):

> CEH34(t) = α + β · CEH9(t) + ε

The pre-clearfell window is used deliberately. Fitting in the post-fell era would risk inheriting any clearfell-related divergence between CEH34 and CEH9 into the calibrated relationship; the pre-fell-only fit gives the unconditional donor regression that pre-dates the intervention. The fitted relationship is then applied to CEH9's pre-CEH34 record (May 2006 to July 2010, 51 monthly cells) to produce a synthetic CEH34 trajectory. The output is a spliced series --- synthetic for dates before 1 August 2010, observed afterwards --- with a *source* flag distinguishing the two.

**Downstream consumption.** The spliced series is exposed via *clearfell_common.load_ceh34_hindcast_series()* (added in *clearfell_common* v1.2.0). Scripts that opt in call the loader explicitly: 10a, 10b, 10e, and 10h consume the hindcast and gain a four-year extension to the Forest-control centroid's pre-fell window. Scripts 10d, 10f, and 10j do not consume the hindcast --- 10d works at annual summer-minimum resolution where the 2010 part-year would contribute no annual statistic anyway; 10f's per-well SSM forward residual fits each well independently and is not affected; 10j uses the Edge tier as control rather than the Forest tier so CEH34 is not in its design at all.

Script 10i (v1.0.0): CEH34 donor-regression hindcast against CEH9; pre-clearfell-only OLS calibration; spliced output consumed by 10a, 10b, 10e, 10h.

### []{#anchor-225}[]{#anchor-226}[]{#anchor-227}Sub-script 10j --- Direct Impact-vs-Edge contrast

**Motivation.** The three-counterfactual ANCOVA in 10a (Forest, Climate, Combined control tiers) accounts for climate forcing via the cumulative water balance (CWB) covariate and for coastal-retreat drift via an easting × time interaction whenever the well-set spans more than 200 m easting. Both covariates carry independent physical justification --- CWB tracks atmospheric forcing month by month, and the easting × time term reflects the documented coastal-retreat gradient at the western margin (Script 25; CEH4 retreat rate of order 29 mm per year over 2010--2024, with documented six-week losses during Storm Brendan, January 2020). However, the headline ANCOVA's identification of the felling step is materially dependent on the easting × time specification: a sensitivity run that omits the term (10j internal diagnostic, reported below) reduces the Forest-control Impact step from its full-specification value to a small positive figure that is not statistically distinguishable from zero. The dependence is mechanistically defensible --- coastal retreat is real, and well-documented --- but a sceptical reading of the headline benefits from a corroborating estimator whose identification does not pass through any easting × time covariate at all.

The Edge tier provides that estimator by design. The four Edge wells (CEH16, CEH20, CEH30, CEH31) sit within or immediately adjacent to the felled compartment but experienced markedly less of the felling treatment than WMC3 itself, while sharing nearly every confounder with the Impact tier: the same coastal-retreat gradient (the Edge eastings span the WMC3 easting), the same monthly climate forcing, the same regional groundwater drift, the same Cluster 4 forest-canopy interception during the pre-fell era. The 2015 scraping is the one major exception --- WMC3 sits within the scraping-influence footprint while the Edge wells, located further east of the scraped compartment, do not --- and the contrast must therefore retain a tier-asymmetric scraping term.

Conceptually the contrast is a two-zone pooled BACI in which the Edge tier is the spatial buffer. If the Impact and Edge wells would have moved together in the absence of the felling, the difference in their step changes at December 2017 is the felling response stripped of every shared confounder. This is a weaker and more defensible identifying assumption than the per-zone modelling required for 10a's three ANCOVA designs.

**Methodology.** 10j runs two parallel analyses at monthly-mean and annual-summer-minimum resolution.

The monthly-mean contrast pools the Impact and Edge wells into a long-format panel of water-table depth observations from *PRE_FELL_START* (1 January 2011) onward, and fits

> h(i,t) = α + β_cwb · CWB(t) + β_S · Scraped1(t) + β_P · Post(t) + γ_S · Z(i) · Scraped1(t) + γ_P · Z(i) · Post(t) + δ_cwb · Z(i) · CWB(t) + μ(i) + ε(i,t)

where h(i,t) is the monthly water-table depth at well *i*, time *t*; CWB(t) is the centred cumulative water balance for month *t* (the same series used by 10a's ANCOVA); Scraped1(t) is an indicator equal to 1 for *t* ≥ *SCRAPING_DATE* (1 April 2015); Post(t) is an indicator equal to 1 for *t* ≥ *INTERVENTION_DATE* (1 December 2017); Z(i) is an indicator equal to 1 for the Impact tier (zero for Edge); and μ(i) is a well-level fixed effect. Estimation is by OLS with cluster-robust standard errors clustered on *i* (well), which absorbs the within-well temporal autocorrelation.

The headline coefficient is γ_P --- the differential felling step (Impact minus Edge). The auxiliary coefficient γ_S is the differential scraping step (Impact minus Edge), retained because the scraping treatment is asymmetric across the two tiers; omitting it forces the scraping signal at WMC3 to load onto β_P and biases the felling-step estimate downward. The Z(i) · CWB(t) interaction permits the climate sensitivity to differ between the two tiers and is included for parity with 10a's *cwb_x_fell* term. The Impact main effect is collinear with the well-fixed-effects block (the Impact tier comprises a single well, WMC3) and is dropped from the design.

The annual summer-minimum contrast operates on the same panel of wells but on the (well, year) summer-minimum frame produced by 10d (*10d_01_summer_minima.csv*), which already encodes the shared cleaning rules --- Jun--Sep minimum, requiring at least two measured months per summer, with the *n_interpolated* flag identifying summers whose minimum is supported by interpolated cells. 10j restricts to the rows with *n_interpolated = 0* (measured-only summers) and fits

> m(i,y) = α + β_P · Post(y) + γ_P · Z(i) · Post(y) + μ(i) + ε(i,y)

where m(i,y) is the Jun--Sep minimum depth at well *i*, year *y*; Post(y) = 1 for *y* ≥ 2018. The scraping term is omitted at this resolution: under the measured-only rule the Impact tier contributes only two pre-2015 summers (2011 and 2013), which is too few to identify a scraping step with stable inference. The model collapses to OLS with cluster-robust standard errors on well (the Impact tier's single well makes a formal random-intercept specification redundant).

The two coefficient estimates (γ_P at monthly and annual resolution) and their standard errors are written to *pipeline_site_observations.csv* via four new registry entries --- *impact_vs_edge_clearfell_monthly_step*, *impact_vs_edge_clearfell_monthly_step_se*, *impact_vs_edge_clearfell_summer_step*, *impact_vs_edge_clearfell_summer_step_se* --- to make the values available to downstream consumers as live pipeline numbers rather than cached constants.

**Easting-term sensitivity (internal diagnostic).** 10j also runs a sensitivity check on 10a in which the easting × time covariate is omitted from each of the six ANCOVA configurations. The result is reported in the main-report editorial queue as a robustness paragraph for §4.6; 10j does not write the sensitivity to a pipeline CSV because it is a diagnostic on a different script's specification rather than an output of 10j itself. The qualitative finding --- that the Forest-control Impact step collapses to a small non-significant figure when the easting term is removed, while two other estimators (synthetic control and SSM forward residual) continue to detect a positive felling step --- supports the interpretation that the easting × time term is correctly absorbing coastal-retreat physics rather than over-fitting a felling-era residual. The direct Impact-vs-Edge contrast adds a third estimator to that set whose identification does not pass through easting × time at all.

**Relationship to the other 10-suite estimators.** The five monthly-mean estimators of the Impact felling step (10a Forest-control headline, 10f synthetic control, 10f SSM forward residual, 10a joint-fit Forest-control sensitivity, and 10j direct contrast) sample the same underlying response through different counterfactual designs and therefore answer subtly different questions. 10a's separately-fitted Forest-control ANCOVA estimates the Impact response against a mechanistically-matched but spatially-distant counterfactual; 10f's synthetic control estimates against a data-driven optimal combination of donor wells; 10f's SSM forward residual estimates against the Impact tier's own pre-scraping SSM fit; 10j estimates against the closest spatial control available. The Edge contrast is the smallest of the five in magnitude --- by construction, because both Impact and Edge experienced any unmodelled wet-period drift that the climate-corrected estimators net out, but the Edge wells did not experience the felling treatment to anything like the same degree as WMC3. The contrast is what survives once every shared confounder cancels, and it is the most conservative single statement of the felling response at WMC3.

The monthly contrast is larger in magnitude and statistically significant; the summer-minimum contrast is smaller and not statistically distinguishable from zero. This is consistent with the wider Script 10 finding (10a annual recovery significant, 10d summer minima at the Impact tier null) and reflects the seasonal phenology of the clearfell response: the felling raised the mean of the year by reducing canopy interception and direct atmospheric draw on the saturated zone, but did not detectably lift the summer minimum, which is set by the depth of the dry-period drawdown rather than by the mean. The two coefficient estimates together describe a felling response that is real in the seasonal mean but ecologically attenuated at the summer extreme --- the resolution that matters for Curreli's SD15b / SD16 wet-slack thresholds.

**Inputs.** Wells, climate, master, locations, and valid tier dictionaries are loaded via *clearfell_common.load_clearfell_data()*. The summer-minima frame is read from *OUT_10D_DATA* (*10d_01_summer_minima.csv*); 10j requires that 10d has already run in the pipeline pass. All dates and well lists are sourced from *clearfell_common* (*INTERVENTION_DATE*, *SCRAPING_DATE*, *PRE_FELL_START*, *IMPACT_WELLS*, *EDGE_WELLS*); the CWB series is built via *clearfell_common.compute_cwb()*. No site-specific values are hardcoded.

**Outputs.** Per-resolution results in *10j_01_monthly_contrast_results.csv* and *10j_02_summer_contrast_results.csv* (one row each with coefficients, standard errors, 95 % confidence intervals, p-values, R², and sample sizes); standard *ReportNumbers* CSV in *10j_report_numbers.csv*; visualization in *10j_03_contrast_timeseries.jpg* (two-panel: zone centroids and the raw Impact-minus-Edge differential) and *10j_04_summer_minima_contrast.jpg* (per-well and tier-mean annual summer-minimum trajectories). Four site-observation entries written to *pipeline_site_observations.csv* via *update_site_observation()*. No figures are saved at PNG resolution; the JPEG quality follows the suite-wide convention.

Script 10j (v1.0.0): direct Impact-vs-Edge BACI contrast at monthly and annual-summer-minimum resolution.

### []{#anchor-227}[]{#anchor-228}[]{#anchor-229}Sub-scripts 10k and 10l --- Four-zone pooled-panel BACI

**Motivation.** The three-counterfactual ANCOVA in 10a fits the same model six times, once per (control, zone) pair, and each fit has its own dependent variable --- the BACI displacement series is the target centroid minus a control centroid, and the control centroid differs between the Forest, Climate, and Combined configurations. The six step estimates therefore do not share a coefficient vector or a covariance matrix, and they are not subtractable: a reader cannot legitimately recover "Impact relative to Edge" by differencing the Forest × Impact and Forest × Edge steps, because the two fits do not share a baseline. Sub-script 10j addressed this for the two-zone Impact-vs-Edge case by stacking the Impact and Edge wells into a single long-form panel and reading the differential felling step off one interaction term. Sub-scripts 10k and 10l generalise the 10j method from two zones to four, so that every zone-vs-zone contrast comes from one internally-consistent fit. They are a methodological cross-check on the principal 10a analysis: 10a remains the principal clearfell BACI analysis of the report, and 10k/10l test whether its felling signal survives re-estimation in a single jointly-fitted panel.

10k is the monthly-mean four-zone model (Phase 1); 10l is the annual summer-minimum four-zone model (Phase 2). Both are built and live. They supplement, and do not replace, 10a (the principal three-counterfactual ANCOVA) and 10j (whose two-zone Impact-vs-Edge contrast cross-validates 10k's derived Impact-minus-Edge contrast).

**The four zones.** All wells from four zones are stacked into one panel, and *zone* becomes a four-level factor with the Forest control as the reference level:

  ---------------------------- --------------------------------- ------------------------------------------------------------------------------------------------------------------------
  Tier                         Wells                             Role
  Forest control (reference)   CEH32, CEH34, CEH33, NW10, CEH2   Mechanistically-matched counterfactual --- same Corsican pine canopy and forest hydrogeology as the felled compartment
  C3/Warren                    CEH1, NW1, NW2, NW11              Second control --- open western dune, expected to behave like the Forest control
  Edge                         CEH31, CEH20, CEH30, CEH16        Differential felling contrast --- compartment edge
  Impact                       WMC3                              Headline felling contrast --- in-situ at the felled compartment
  ---------------------------- --------------------------------- ------------------------------------------------------------------------------------------------------------------------

The Forest-control reference is the C4-interior unfelled set, so the headline Impact coefficient reads as a like-with-like Impact-minus-Forest contrast with the forest-versus-open-dune hydrological difference kept out of it. The C3/Warren zone is a newly-defined four-well set: it is the balanced subset of the C3 Western Residual cluster that reaches back to the panel baseline and lies more than 500 m from the felled compartment. NW13 and WMC4, two further C3 candidates, are dropped because their records begin in February 2012, some nineteen months after the panel baseline, which would leave the zone internally short-changed against the other three. The Coastal-control wells (CEH19, CEH17) are excluded from the four-zone panel entirely: they carry the coastal-retreat confound and are not a clean counterfactual.

C3/Warren is designated a **second control** zone, not a second impact-like zone. Forest-management perturbations at the warren propagate south-westward off the bedrock ridge; there are no C3 wells in that propagation sector, so the western-dune zone is hydraulically shielded from the felled compartment. The expectation is therefore that the C3/Warren differential felling step is near zero --- a confirmatory result that the panel design is sound, not a finding. A clearly non-zero C3/Warren step would be treated as a flag (possible unshielded propagation or another confound), not as a felling effect.

**Methodology.** 10k fits a long-form monthly panel --- one row per (well, month), every well in the four zones, every month from *PRE_FELL_START* (1 January 2011) onward. The dependent variable is the well's own monthly water-table depth, not a differenced centroid; the *zone* factor and per-well fixed effects do the differencing inside one regression. The design carries a mean-centred cumulative-water-balance covariate and its three zone interactions, a binary April-2015 scraping indicator and its three zone interactions, a December-2017 felling indicator and its three zone interactions, a single network-wide easting × time covariate, and the per-well fixed-effects block. Estimation is by OLS with cluster-robust standard errors on *well*. The zone main effects are perfectly collinear with the well fixed effects --- every well belongs to exactly one zone --- and are absorbed rather than entered as separate columns. The three felling-interaction coefficients (C3/Warren, Edge, Impact, each relative to the Forest reference) are the headline outputs. The October 2023 re-scraping is omitted from the primary model; the easting × time term is retained as a network-wide covariate and is a robustness control, not an erosion decomposition --- the coastal-retreat magnitude is estimated independently by Script 25.

10l fits the same four zones on the annual Jun--Sep summer-minimum frame. The summer panel is an order of magnitude smaller --- annual rather than monthly --- and the scraping term is dropped at this resolution, as in 10j's summer model, because the Impact tier carries too few pre-felling summers to support it. 10l is the committed Phase 2 of the four-zone design and reads its summer-minimum frame on the same provenance-aware basis as 10d.

**Primary and derived contrasts.** The four-zone model estimates three **primary** contrasts --- the C3/Warren, Edge, and Impact felling steps, each relative to the Forest reference. These are direct model coefficients; their standard errors and p-values are interpreted normally. Every zone-vs-zone contrast --- Impact-minus-Edge, Impact-minus-C3/Warren, Edge-minus-C3/Warren --- is an exact linear combination of the three primary coefficients (for example, Impact-minus-Edge equals the Impact step minus the Edge step). These **derived** contrasts have exact point estimates and the arithmetic identity holds, but their standard errors depend on the covariance between the two coefficients being differenced. When two quiet, control-like zones are differenced their coefficients are strongly positively correlated, the variances partly cancel, and the derived contrast acquires an artificially narrow confidence interval and a small p-value that is not independent evidence of a felling effect. The live pairwise-contrast CSVs (*10k_02_pairwise_contrasts.csv*, *10l_02_summer_pairwise_contrasts.csv*) deliberately segregate the primary *p* column from the derived *p_derived* column for this reason. The chapter --- and the main-report §4.6 text --- report the three primary zone-vs-Forest contrasts as the results; cite the Impact-minus-Edge derived contrast only with its 10j cross-validation as the warrant for it, not its *p_derived*; and never cite the C3/Warren-bearing derived contrasts' *p_derived* as significance.

**Monthly result (10k).** The four-zone joint fit (R² = 0.856, N = 2475 well-months) gives a primary Impact-minus-Forest monthly felling step of **+0.032 m (+32 mm), 95 % CI \[+0.010, +0.053\], p = 0.004** --- a significant post-felling rise in the felled compartment's monthly-mean water table. The primary Edge-minus-Forest step is −0.030 m, p = 0.128 (not significant) and the primary C3/Warren-minus-Forest step is +0.005 m, p = 0.647 (not significant --- the near-zero second-control result the shielding design predicts). The Impact-minus-Edge derived contrast is +0.061 m; it is not cited via its *p_derived* but is corroborated independently by 10j's two-zone monthly Impact-vs-Edge step of +0.063 m, p = 0.0002 --- the agreement between the two estimators, which sample the same response through different designs, is a validation of the four-zone fit. The easting-sensitivity refit confirms the headline is robust to the covariate: dropping the easting × time term moves the Impact step only from +32 mm to +33 mm with the significance unchanged.

The four-zone joint Impact-minus-Forest step (+32 mm) is smaller in magnitude than the +113 mm Forest × Impact step from the principal 10a ANCOVA. The two estimators are not in conflict: they differ in how climate variance is partitioned. The joint panel estimates climate sensitivity from the full cross-zone monthly record, with each zone carrying its own cumulative-water-balance interaction, so a portion of the monthly variance that the separately-fitted differenced-centroid ANCOVA attributes to the felling step is instead attributed to climate in the joint fit. The cross-check is consistent with 10a in the respects that matter for the report's conclusion: the felling response is positive and statistically significant under both estimators, and only the magnitude is sensitive to the partitioning choice.

**Summer result (10l).** The four-zone summer-minimum joint fit (R² = 0.724, N = 181 well-years) gives a primary Impact-minus-Forest summer-minimum step of **−0.007 m (−7 mm), 95 % CI \[−0.023, +0.008\], p = 0.36 --- a null.** The primary Edge-minus-Forest summer step is −0.029 m, p = 0.162 and the primary C3/Warren-minus-Forest step is +0.012 m, p = 0.257 --- neither significant. No zone contrast resolves a significant differential felling response at the summer minimum. The summer-minimum result is the more conservation-relevant of the two: the Jun--Sep minimum is the driest, most ecologically critical point of the year and the level against which the Curreli SD15b / SD16 slack thresholds are defined. The two-part four-zone finding is therefore that the felling produced a measurable rise in the felled compartment's monthly-mean water table but no detectable change at the summer minimum; both parts are reported with equal weight.

**Inputs.** Wells, climate, master, locations, and the valid tier dictionaries are loaded via *clearfell_common.load_clearfell_data()*; 10l additionally reads the summer-minimum frame from *10d_01_summer_minima.csv*. The four zones, the *C3_WARREN_WELLS* constant, and all dates are sourced from *clearfell_common*; the cumulative-water-balance series is built via *clearfell_common.compute_cwb()*. No site-specific values are hardcoded.

**Outputs.** 10k writes the three-row primary results to *10k_01_four_zone_results.csv*, the six ordered pairwise contrasts to *10k_02_pairwise_contrasts.csv* (with the primary/derived *contrast_type* column), the easting-sensitivity refit to *10k_03_easting_sensitivity.csv*, the standard *ReportNumbers* CSV to *10k_report_numbers.csv* (new *FourZone\_\** keys, no collision with 10a's *ANCOVA\_\** or 10j's *ImpactVsEdge\_\** keys), and three figures --- zone-centroid hydrographs, the differential series stacked against the Forest centroid, and a coefficient forest-plot of the six pairwise contrasts. 10l writes the parallel summer-minimum set (*10l_01_four_zone_summer_results.csv*, *10l_02_summer_pairwise_contrasts.csv*, *10l_report_numbers.csv*, and the summer trajectory and forest-plot figures). All figures follow the suite-wide JPEG convention.

Script 10k (v1.0.0): four-zone monthly pooled-panel BACI. Script 10l (v1.0.0): four-zone summer-minimum pooled-panel BACI.

### []{#anchor-229}[]{#anchor-230}[]{#anchor-231}Supplementary --- Sub-script 10c --- Forest zone analysis

Marked supplementary in *run_10_clearfell.py* and written to a separate output directory (*outputs/10c_forest_zone_analysis/*) rather than the suite's main directory. The analysis asks whether the C4/C5 partition reflects a substrate or topographic transition or is arbitrary within a continuous gradient. Per-well SSM coefficients from Script 07 are regressed against three spatial predictors (DEM elevation, distance from ridge crest at E = 241750, N = 364500, distance from coast); the C4--C5 boundary is mapped with elevation context; and the clearfell treatment wells (FE1--FE4, WMC3, LIS1) are located in β₁--β₂ space against the surrounding forest cluster. The outputs feed Table 16 in the main report and provide context for the suite's treatment of C4 and C5 as mechanistically distinct tiers in 10a. The analysis is not part of the §4.6 clearfell result and is not given further weight in this chapter.

### []{#anchor-231}[]{#anchor-232}[]{#anchor-233}Methodology (suite-level) --- *clearfell_common.py*

The suite-shared module sits at *src/utils/clearfell_common.py* and provides everything that needs to be consistent across the thirteen sub-scripts. Changing an impact-well list, an intervention date, or a distance-weight function in one place propagates to all of them.

**Well tier definitions.** Five module-level lists define the canonical network: *IMPACT_WELLS = \[\'wmc3\'\]*; *EDGE_WELLS = \[\'ceh31\', \'ceh20\', \'ceh30\', \'ceh16\'\]*; *FOREST_CONTROL_WELLS = \[\'ceh32\', \'ceh34\', \'ceh33\', \'nw10\', \'ceh2\'\]*; *COASTAL_CONTROL_WELLS = \[\'ceh19\', \'ceh17\'\]*; *CLIMATE_CONTROL_WELLS = \[\'ceh9\', \'nw7\', \'nw6\', \'nw5\', \'wmc2\'\]*. Concatenated as *ALL_NETWORK_WELLS* (17 wells). A *TIERS* dict groups them for iteration. The lowercase names match the column-name normalization that *load_clearfell_data()* applies on import. A sixth list, *C3_WARREN_WELLS = \[\'ceh1\', \'nw1\', \'nw2\', \'nw11\'\]*, defines the shielded western-dune second-control zone used by the four-zone sub-scripts 10k and 10l; it is not part of the 17-well clearfell network and is not in *ALL_NETWORK_WELLS*.

**Intervention dates.** *INTERVENTION_DATE = 2017-12-01*; *SCRAPING_DATE = 2015-04-01*; *SCRAPING_DATE_2 = 2023-10-01*. *FELLING_YEAR = 2017*. These three dates appear throughout the suite as era boundary masks (*wells.index \>= INTERVENTION_DATE*, etc.) --- the suite has no *WELL_ERAS* dict; era boundaries are inline masks against the date constants.

**Data loading.** *load_clearfell_data()* returns *(wells, climate, master, well_locations, valid_tiers)*. It merges the reference and extended well frames, lowercases the column names, applies *clean_well_series()* to each column, reads climate with *parse_dates=True*, parses *03_master_data.csv*, and builds *well_locations* from the master data (with a *Well_locations_height.csv* fallback for wells not in the master). It also validates the five tiers, emitting a warning for any well in a tier that is missing from the data.

**BACI helpers.** *compute_baci_displacement(wells, target_list, control_list)* returns the target-centroid minus control-centroid timeseries. *compute_cwb(climate, baseline_start, baseline_end)* returns the centred cumulative *(P − PET)* anomaly in mm. *compute_control_centroid()* returns the monthly mean of an arbitrary control list.

**Distance-weighted scraping covariate.** *distance_from_ceh36()* and *distance_from_fell_centroid()* are the two Euclidean distance functions, using *CEH36_EASTING = 241161*, *CEH36_NORTHING = 363306* and *FELL_CENTROID_EASTING = 241210*, *FELL_CENTROID_NORTHING = 363607*. *scraping_weight(d, λ)* returns *exp(−d / λ)* with default *SCRAPING_DECAY_LAMBDA = 300 m*. *distance_weighted_scraping()* builds the per-well covariate: zero before the scraping date, exponential weight after. *build_scraping_covariate_centroid()* builds the centroid covariate as the mean of per-well weights across a tier --- used by 10a and 10h to construct the differential scraping covariate.

**Summer-minimum extraction.** *annual_summer_minimum(series, start_year, end_year)* returns *{year: float}* of June--September minima, requiring at least two observations per year (*SUMMER_MONTHS = \[6, 7, 8, 9\]*). *forest_control_centroid_summer_min()* builds the multi-well summer-minimum centroid, requiring at least two wells per year by default.

**BACI-corrected β₂ multiplier.** *load_clearfell_b2_multiplier(verbose=True)* reads *10e_01_coefficient_shifts.csv*, computes per-tier mean *b2_after / b2_before* ratios, and returns the BACI-corrected clearfell multiplier *Edge_ratio − Climate_Ctrl_ratio + 1.0* and the thinning multiplier *1.0 + (clearfell − 1.0) / 2.0*. Fallback values of 1.10 (clearfell) and 1.05 (thinning) are returned if the 10e file is unreadable. The function returns three values --- multiplier, thinning multiplier, tier-ratios dict --- so all callers can inspect provenance.

**Reporting utility.** *ReportNumbers* is a simple accumulator class with *add(parameter, value, unit, well, era, note)* and *save(path)*. Every sub-script uses it to write a per-script *\*\_report_numbers.csv* exported into the main directory; *run_10_clearfell.py* then merges all per-sub-script files into *10_consolidated_report_numbers.csv*.

### []{#anchor-233}[]{#anchor-234}[]{#anchor-235}Site-specific choices and rationale (suite-level)

-   **The 17-well BACI network excludes FE1--FE4, NW8, and NW8B.** FE1--FE4 lack pre-clearfell baselines (FE1 and FE2 start July 2015; FE3 and FE4 in 2017). NW8 and NW8B have data-quality issues in their pre-intervention records. CEH42 is excluded by length-of-baseline rule (3.4 years pre-felling, below the threshold). The exclusions are codified in the network constants --- there is no separate exclusion list.
-   **Single impact well in the published headline (WMC3).** Like the scraping suite (S.6) where the impact-zone is CEH36 alone at the published level, the clearfell suite has structural n = 1 at the published Impact tier. 10h's synthetic extension via FE1/FE2 donor regression is the principal robustness check; both synthetic-extension variants (Variant A and Variant B) return positive, individually significant or marginally so Forest-control steps, confirming the direction and sign of the WMC3-only headline but at smaller magnitude.
-   **Three control structures (Forest, Climate, Combined), not a single counterfactual.** Each isolates a different aspect of the clearfell signal. Forest controls for canopy effects; Climate is the unconfounded climate baseline; Combined pools the three control tiers for tighter intervals at the cost of mechanistic specificity. The three are reported together rather than reduced to one because they answer different questions and the agreement (or disagreement) across them is itself the headline. There is no standalone "Coastal Forest" counterfactual --- the C5 wells enter only inside Combined, because the C5 tier carries a confounding coastal-retreat signal whose explicit handling is more clearly done by the differential easting × time correction inside the ANCOVA than by treating C5 as a third counterfactual.
-   **Easting × time correction in the ANCOVA.** Coastal retreat at Newborough is episodic and acute (approximately 50 m of retreat between 2014 and 2020, with the acute loss during Storm Brendan in January 2020). The easting × time correction in the BACI ANCOVA is a physically real spatial-gradient term, included automatically where the easting range across the wells in a single (target, control) pairing exceeds 200 m. For the Forest-control runs this fails (the C4 wells all sit close together in easting) and the term is dropped; for the Climate and Combined runs it is included and is significant at p \< 10⁻¹⁰ in every case. The fuller treatment of the coastal-erosion gradient is in chapter S.15 (Script 25); the easting × time term in 10a is the suite's local handling of the same signal.
-   **Climate-correction wells for the spatial maps (10b) are intentionally different from the ANCOVA climate controls (10a).** 10b uses the four-well western subset NW5, NW6, NW7, CEH1 because these share the western climate signal and coastal-retreat position with the impact zones, absorbing both climate and coastal drift in a single median subtraction. 10a's full five-well C3 set is used in the ANCOVA where the explicit covariate structure handles the climate signal separately. The two purposes --- spatial correction for a map, full covariate handling for a step estimate --- call for different reference sets.
-   **Fixed-membership control centroid.** As of *clearfell_common* v1.7.0, each control centroid is computed only over months in which every roster well has a value; a month with any roster well missing is excluded from the BACI series. The earlier implementation took a NaN-skipping monthly mean, so the centroid silently re-weighted whenever a control well went offline. The dominant case was the joint outage of NW10 and CEH2 from September 2011 to September 2012, during which the Forest-control centroid was the mean of only CEH32, CEH33, and CEH34. The fixed-membership rule removes that artefact. It lowers the Forest × Impact annual clearfell step from +0.135 m to +0.120 m as then computed (both p \< 0.001) and the model R² from 0.37 to 0.27; the result remains positive and highly significant. On current pipeline data the step is +0.113 m (p = 0.002). A coordinated change in the same *clearfell_common* v1.7.0 commit migrated the shared *PRE_FELL_START* cutoff from 1 July 2010 to 1 January 2011, so the legacy 10-series sub-scripts share the four-zone scripts' pre-felling start; the audit established this as a consistency change rather than the artefact fix (the 2010 install-ramp months were already outside the ANCOVA window after the cumulative-water-balance inner-join). The audit basis is *AUDIT_10series_PRE_FELL_START.md*.
-   **Provenance-aware summer minima.** 10d consumes *01_wells_provenance.csv* (§S.1) and applies a *min_measured=2* rule to *annual_summer_minimum()*: a (well, year) summer minimum is admitted to the panel only when at least two of the four Jun--Sep months are actual field measurements. Single-month interpolations under *limit=1* are allowed to contribute and are flagged in the *n_interpolated* column of *10d_01_summer_minima.csv*. The rule excludes (well, year) combinations whose minimum would rest only on interpolated values. The same provenance file and rule is consumed by §S.6 sub-script 09c.

### []{#anchor-235}[]{#anchor-236}[]{#anchor-237}Limitations and known caveats (suite-level)

-   **Single impact well in the published headline.** 10h's synthetic extension partially mitigates this but the synthetic baselines themselves carry calibration uncertainty (R² ≈ 0.99 across 29 months) and the assumption that the donor regression is stationary backward through pre-scraping years. The synthetic-extension variants confirm the direction and sign of the WMC3-only headline but return smaller magnitudes; the synthetic extension is read as a direction-and-sign robustness check rather than an independent magnitude estimator.
-   **Mean monthly recovery is significant; summer minima are not.** This is the central scientific neutrality point for the suite. 10a's Forest-control Impact step is +113 mm, p = 0.002; 10d's Forest-control mixed-model Impact step is −1 mm, p = 0.99 --- no improvement (and no penalty) in summer minima at the impact well. The Forest-control Edge summer-minimum mixed-model step is −64 mm, p = 0.12 --- a negative shift that does not reach significance at α = 0.05 against the Forest control, and that does not reproduce against the Climate-control baseline (+48 mm, p = 0.28). The mean-recovery result is real, and the summer-minima result is real; the chapter presents both with equal weight rather than emphasising the recovery and softening the null summer signal.
-   **Six-year post-felling window with a coastal-erosion event mid-way.** Just over six years from December 2017 to the analysis cut-off, with Storm Brendan in January 2020 inside the post-felling window. The easting × time correction handles the spatial-gradient component but the temporal-step component of Storm Brendan is partially absorbed into the CWB × felling interaction term rather than being separately identified.
-   **The β₂ multiplier exports a clearfell perturbation but uses no winter/summer seasonal split.** The current *load_clearfell_b2_multiplier()* returns a single annual-mean β₂ multiplier from the BACI-corrected Edge ratio. A seasonal split --- winter ≈ 0.88 (leaves off), summer ≈ 1.11 (full leaf) for broadleaf, with a corresponding asymmetric profile for evergreen pine --- would match the monthly profile that Script 21's Option 3 perturbation requires. The implications for §4.10.2 are flagged in the project's *BETA2_DECOMPOSITION_UPDATED.md*.
-   **10c is supplementary, not part of the headline chain.** Its outputs feed Table 17 but the §4.6 clearfell result rests on 10a (with 10h's extension), supported by 10b, 10d, 10e, 10f, 10g. Readers should not treat 10c's per-well coefficient regression as evidence about the clearfell --- it is evidence about the C4--C5 cluster boundary.
-   **Forest β₂ uses a single annual mean in the suite-shared multiplier.** As above; flagged for future seasonal-split work.
-   **10m DiD steps are raw, not climate-corrected.** The per-era difference-in-differences gaps in 10m are the raw WMC3-minus-Forest-control displacement differences, not the ANCOVA climate-corrected steps of 10a. They confirm direction and trajectory but are not the headline result. The on-figure 10a ANCOVA note is the scientific anchor; the DiD steps are display values only.

### []{#anchor-237}[]{#anchor-238}[]{#anchor-239}Sub-script 10m --- WMC3 BACI dual-panel display figure (v1.0.0)

**Motivation.** The headline ANCOVA result (10a, +113 mm, p = 0.002) and the broader six-tier analysis address the question of whether the clearfell raised the mean monthly water table. 10m steps back and asks: for the one well that bears the full 21-year history of both scraping events, the clearfell, and the re-scraping --- WMC3 --- what does the raw trajectory look like against the forest-control mean, and does that picture match the analytical story? The figure is a sanity-check and communication tool, not a new analysis.

**Methodology.** 10m reads *01_wells_clean.csv* for WMC3 and Forest-control monthly levels (via the *clearfell_common* loaders and tier definitions), computes the displacement gap series (WMC3 minus Forest-control mean), and overlays per-era raw difference-in-differences steps on the gap. The 10a ANCOVA clearfell step (+113 mm, p = 0.002) is loaded live from *10a_report_numbers.csv* (key *ANCOVA_Forest_Impact_clearfell_step*) and placed as an on-figure reference band so the raw and climate-corrected steps can be read simultaneously without conflation. **10m must run after 10a** --- it is wired last in *run_10_clearfell.py* to guarantee this.

**Outputs.** *10m_01_wmc3_baci_era_steps.csv* (per-era DiD steps); *10m_02_wmc3_baci_dual.png* (the dual-panel figure); *10m_report_numbers.csv* (era steps for reference). Paths: *paths.OUT_10M_ERA_STEPS*, *paths.OUT_10M_DUAL_FIG*, *paths.OUT_10M_REPORT*.

**Report location.** Internal interpretation; if placed, §4.6. Figure number TBC with Martin.

### []{#anchor-239}[]{#anchor-240}[]{#anchor-241}Outputs (consolidated)

  ------------ ---------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------
  Sub-script   Output                                                                                   Description
  10a          10a_01_ancova_comparison_table.csv                                                       6-row summary: 3 controls × 2 zones; clearfell step, CI, p, R², N
  10a          10a_02_ancova_full_coefficients.csv                                                      Full model coefficients per (control, zone)
  10a          10a_03_baci_timeseries.csv                                                               Raw and climate-corrected BACI displacement timeseries
  10a          *10a_04..08\*.png*, *10a_S1..S3\*.png*                                                   Forest-control 3-panel BACI figures, CUSUM, climate-sensitivity scatter; supplementary 3-control panels
  10b          10b_spatial_step_data.csv                                                                Per-well era means, scraping and felling step values, climate-corrected steps
  10b          *10b_spatial\_\*\_raw.png*, *10b_spatial\_\*\_corrected.png*                             Four spatial step-change maps
  10c          10c_forest_zone_correlations.csv                                                         β coefficient regression results vs elevation, distance from ridge, distance from coast
  10c          10c_forest_zone_cluster_summary.csv                                                      C4 vs C5 t-test summary statistics
  10c          10c_forest_zone_analysis/10c_01..04\*.png/.txt                                           β₁--β₂ scatter, β₂ elevation regression, boundary map, summary
  10d          10d_01_summer_minima.csv                                                                 Per-well, per-year summer minimum with control centroids; *n_interpolated* column flags rows containing single-month interpolated Jun--Sep cells
  10d          10d_02_summer_minima_shifts.csv                                                          Per-well pre/post shifts, t-test summary
  10d          10d_03_mixed_model_results.csv                                                           Mixed-effects pooled step estimates per tier
  10d          *10d_04_summer_minima_forest_ctrl.png*, *10d_05\_\*climate\*.png*                        4-panel summer-minimum figures
  10e          10e_01_coefficient_shifts.csv                                                            Per-well Before / After β coefficients and Δβ across the five BACI tiers. Source for *load_clearfell_b2_multiplier()*
  10e          10e_03_coefficient_shifts.png                                                            Before/after coefficient figure
  10f          10f_01_ssm_residual_results.csv                                                          Per-well SSM forward-residual step estimates
  10f          10f_02_synthetic_control_results.csv                                                     Zone-level synthetic-control step estimates
  10g          10g_01_nw10_broadleaf_trend.csv                                                          NW10 summer-min anomaly trend data
  10g          *10g_02_clearfell_transect.png*, *10g_03_clearfell_transect_steps.csv*                   Radial transect figure and step-vs-distance data
  10g          10g_04_rolling_coefficients.csv                                                          48-month rolling SSM coefficients (Impact, C3, C4)
  10h          10h_01_synthetic_calibration.csv                                                         Donor regression diagnostics (R², RMSE, hindcast)
  10h          10h_02_ancova_comparison_table.csv                                                       Three variants × three controls ANCOVA results
  10h          10h_03_ancova_full_coefficients.csv                                                      Full coefficients per (variant, control)
  10h          10h_04_baci_timeseries.csv                                                               BACI timeseries per variant
  10h          10h_05..10\*.png                                                                         Donor regression validation, three-panel BACI per variant, CUSUM, sensitivity
  10i          10i_01_ceh34_hindcast.csv                                                                Spliced CEH34 series with *source* flag (*\'hindcast\'* or *\'observed\'*); consumed by 10a/10b/10e/10h via *apply_ceh34_hindcast()*
  10i          10i_02_donor_regression.csv                                                              OLS fit parameters (α, β) and residual diagnostics for the CEH34 ← CEH9 regression
  10i          10i_03_hindcast_diagnostic.png                                                           Three-panel donor-regression diagnostic figure
  10j          10j_01_monthly_contrast_results.csv                                                      One-row summary of the monthly-mean Impact-vs-Edge contrast: coefficients, SE, CI, p, R², N
  10j          10j_02_summer_contrast_results.csv                                                       One-row summary of the annual-summer-minimum Impact-vs-Edge contrast (measured-only summers): coefficients, SE, CI, p, R², N
  10j          10j_03_contrast_timeseries.jpg                                                           Two-panel figure: zone centroids and raw Impact-minus-Edge differential
  10j          10j_04_summer_minima_contrast.jpg                                                        Per-well and tier-mean annual summer-minimum trajectories
  10k          10k_01_four_zone_results.csv                                                             Three primary zone-vs-Forest monthly felling contrasts: step, SE, CI, p, scraping step, CWB interaction, R², N
  10k          10k_02_pairwise_contrasts.csv                                                            Six ordered pairwise felling contrasts with a *contrast_type* column segregating primary from derived
  10k          10k_03_easting_sensitivity.csv                                                           Full model re-fit with and without the easting × time covariate --- robustness diagnostic
  10k          10k_04..06\*.jpg                                                                         Zone-centroid hydrographs, differential series vs Forest centroid, pairwise-contrast forest-plot
  10l          10l_01_four_zone_summer_results.csv                                                      Three primary zone-vs-Forest summer-minimum felling contrasts: step, SE, CI, p, well-year counts, R², N
  10l          10l_02_summer_pairwise_contrasts.csv                                                     Six ordered pairwise summer-minimum contrasts with primary/derived *contrast_type* column
  10l          10l_03_c3warren_summer_minima.csv                                                        C3/Warren-zone per-well summer-minimum series
  10l          10l_04..05\*.jpg                                                                         Zone summer-minimum trajectories, summer-minimum pairwise-contrast forest-plot
  10m          10m_01_wmc3_baci_era_steps.csv                                                           Per-era raw DiD gap steps (WMC3 minus Forest-control mean) for display
  10m          10m_02_wmc3_baci_dual.png                                                                Dual-panel display figure: WMC3 vs forest-control mean; on-figure 10a ANCOVA headline
  10m          10m_report_numbers.csv                                                                   Era DiD steps for reference / traceability
  All          *10\[a,d,e,f,g,h,i,j,k,l\]\_report_numbers.csv* → *10_consolidated_report_numbers.csv*   All citable values from each sub-script, consolidated by *run_10_clearfell.py*
  ------------ ---------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-241}[]{#anchor-242}[]{#anchor-243}Where the result appears in the report

-   §4.6 *Clearfell intervention* --- entire section.
-   **Table 7** (per the live *PIPELINE_README.md* table-mapping) --- Clearfell ANCOVA-BACI results, source: *10a_report_numbers.csv*.
-   **Table 8** --- The easting × time term fitted in each ANCOVA contrast, with the differential drift each absorbs, source: *25_04_baci_corroboration.csv*.
-   **Table 9** --- Per-well summer minimum shifts, source: *10d_02_summer_minima_shifts.csv*.
-   **Table 10** --- Mixed-effects clearfell step by tier, source: 10d / mixed-effects output.
-   **Table 11** --- Before/after clearfell SSM coefficients for all 17 BACI-network wells, source: *10e_01_coefficient_shifts.csv*.
-   **§4.6.3 / §4.6.4** --- Four-zone pooled-panel BACI: the primary monthly clearfell result (10k) and the summer-minimum response (10l), sources: *10k_report_numbers.csv*, *10l_report_numbers.csv*.
-   **Table 17** --- Forest zone spatial predictors, source: *10c_forest_zone_analysis.py* (*10c_04_forest_zone_summary.txt*; underlying correlations in *10c_forest_zone_correlations.csv*).
-   **Figure 25** --- Scraping-era spatial step map (10b).
-   **Figures 28, 30 and 31** --- CWB vs BACI displacement, Forest-control BACI Impact and Edge tiers (10a).
-   **Figure 32** --- Summer minima vs Forest control (10d).
-   **Figure 34** --- Clearfell-era spatial step map (10b).
-   **Figure 35** --- Before/after SSM coefficients across the 17-well network (10e).
-   **Figure 36** --- Clearfell radial transect, step vs distance (10g).
-   §4.6 robustness paragraph --- easting × time sensitivity and the direct Impact-vs-Edge contrast (10j); values sourced from *pipeline_site_observations.csv* (entries *impact_vs_edge_clearfell_monthly_step* and *impact_vs_edge_clearfell_summer_step*) rather than from a cached constant.
-   §4.6 / §5 conservation-management paragraph --- seasonal asymmetry between the monthly-mean and summer-minimum Impact-vs-Edge contrasts (10j), corroborating the 10d summer-minima null result against the 10a annual-mean positive result.

### []{#anchor-243}[]{#anchor-244}[]{#anchor-245}Cross-references

-   **F.3** --- SSM equation, displacement formulation, sign conventions. 10e and 10f fit SSMs through this; 10e diverges from *fit_ssm()* by adding a scraping dummy for the Before fit.
-   **F.4** --- *pipeline_params.py* consolidation, including the BACI-corrected β₂ multiplier consumed by Scripts 19 and 21.
-   **F.5** --- *clearfell_common.py* brief role summary (full detail in this chapter's *Methodology (suite-level)* section). The *site_observations.py* registry is the route by which 10j's four contrast values, and the four-zone primary zone-vs-Forest steps from 10k and 10l, reach downstream consumers without caching.
-   **S.1** --- produces *01_wells_provenance.csv* consumed by 10d (and by 09c in §S.6) under the *min_measured=2* rule; 10j inherits the rule by restricting to *n_interpolated = 0* rows of 10d's summer-minima output.
-   **S.3** --- produces *03_master_data.csv* consumed by all sub-scripts.
-   **S.6** --- Script 09 scraping suite, the parallel intervention analysis. *scraping_common.py* is the analogous shared module; the structural parallel (single impact well in the published headline, climate-water-balance covariate, era-based design) is deliberate. Script 09b also reads *10b_spatial_step_data.csv* for the network-wide propagation modelling. Sub-script 09c shares the *min_measured=2* provenance-aware summer-minima rule with this chapter's 10d. The scraping suite does not have a direct analogue of 10j because the scraping intervention does not have an Edge tier as cleanly separable from its Impact tier.
-   **S.12** --- Script 17 WTF Sy, consumed in the volumetric translation used downstream (not directly in 10d; the volumetric step appears in §4.6 narrative via cluster-level Sy values).
-   **S.14** --- Script 21 forestry scenarios, which consume 10e's BACI-corrected β₂ multiplier via *load_clearfell_b2_multiplier()*.
-   **S.15** --- Script 25 coastal-retreat gradient, which informs the easting × time correction in 10a's ANCOVA. 10j's identification design is the corroborator that bypasses that correction; the two estimators are designed to be cross-checked rather than to agree by construction.

Spring-mean companion metric (10d v1.7.0, 10l v1.2.0). The clearfell BACI summer-minimum scripts gain the annual spring mean (Mar--May) as a second seasonal metric through the same code path. In Script 10d the per-metric body (extraction, pre/post Welch shifts, mixed-effects models, figures) runs once per metric with a single shared ReportNumbers accumulator created and saved outside the loop. In the four-zone Script 10l the panel assembly, fit, contrasts and figures are parameterised on the metric; the spring panel is selected by the same WMC3 gatekeeper applied to Mar--May (wmc3_usable_spring_years). Because WMC3\'s spring record is near-complete, the spring panel gains a year: 2011 + 2013--2025 = 14 years (only 2012 dropped) against the summer panel\'s 13 (2012 and 2019 dropped) --- 2019, unusable in summer, is fully measured in spring --- even under the stricter 3-of-3 rule. The spring branch carries no Script-10j cross-check (there is no 10j spring estimator). Outputs 10d_06--10d_10 and 10l_06--10l_10; spring rows append to the shared per-metric report-numbers files and three four_zone_spring_step\_\* keys are added to the site-observations registry. Results in Supplementary Note S8.

# []{#anchor-245}[]{#anchor-246}[]{#anchor-247}Phase 4 --- Climate and Spatial Context

## []{#anchor-247}[]{#anchor-248}[]{#anchor-249}S.8 Scripts 00, 12, 13, 14 --- Climate baseline and site-overview figures

**Steps 13--16 / 27 (Phase 4 in ***run_analysis.py***). Phase 4 --- Climate and Spatial Context.**

### []{#anchor-249}[]{#anchor-250}[]{#anchor-251}Motivation

The four scripts in this chapter produce the report's foundational orientation material: the climate baseline that §2 leans on for site setting, the DEM map that opens §2 as Figure 1, the experimental-design diagram that opens §3 as the BACI network figure, and the observed-trajectory figures in §5 that frame the climate-change discussion. None of these scripts produces a CSV that feeds another analytical chain --- they are visualization and baseline-context outputs. The chapter accordingly compresses the methodological detail and concentrates on what each script chooses to render and why.

Three of the four scripts (00, 12, 13) sit at Phase 4's start as orientation tools that run alongside the main analysis. Script 14 sits later in the phase, reading from *03_regional_averages.csv* to project cluster-centroid summer minima forward to 2040 and to evaluate observed winter maxima against the Curreli et al. (2013) flooding thresholds.

### []{#anchor-251}[]{#anchor-252}[]{#anchor-253}Inputs

  ---------------------------------------------------- ------------------- ---------------------
  Input file                                           Used by             Note
  01_climate.csv                                       00                  Script 01
  01_wells_clean.csv                                   00                  Script 01
  data/RAF_Valley_Climate.csv                          00 (Figures 4, 5)   Raw climate input
  data/Well_locations_height.csv                       12, 13              Raw locations input
  data/newborough_dem.tif                              12, 13              Raw DEM input
  *data/\*.kml* (clearfell, broadleaf restock, etc.)   12, 13              Raw site features
  03_regional_averages.csv                             14                  Script 03
  ---------------------------------------------------- ------------------- ---------------------

Scripts 12 and 13 are the two pipeline scripts that legitimately read from *Well_locations_height.csv* directly rather than from a Script 01 intermediate. The exception is recorded in F.5: site-mapping figures need raw coordinates and the full locations register, including wells excluded from the analytical network, which the Script 01 intermediate does not retain.

### []{#anchor-253}[]{#anchor-254}[]{#anchor-255}Sub-script 00 --- Climate summary

Script 00 generates two complete output sets in a single run via *\_run_all()*. The **full-record** set covers the entire RAF Valley climate series (December 1930 to present, \~95 years) and produces the climate timeseries figure, well-network summary figure, summer warming-trend figure, and three matching CSV tables. The **monitoring-period** set repeats the climate and network outputs over the well-record overlap window (roughly 2004 onwards), restricting climate and wells to the date span where the reference network has observations. The two filename groups are distinguished by a *\_short* suffix on the monitoring-period outputs.

The well filter retains wells with at least *MIN_RECORD_MONTHS = 100* valid records up to *REFERENCE_CUTOFF_DATE*. Llyn Rhos-Ddu is hard-excluded by name because it is a lake-stage measurement rather than a water-table observation; this mirrors the EXTENDED_NETWORK_BLACKLIST in Script 01. Annual climate aggregation (*make_table1_annual_climate*) computes annual P, annual PET, and the P/PET ratio per year, with a *Months_complete* count and a long-term-mean summary row. The well-network table (*make_table2_well_network*) writes per-well record start/end, valid month count, mean, standard deviation, seasonal amplitude (August mean minus February mean), and the per-hydrological-year summer minimum and winter maximum.

The monitoring-period timeseries figure uses a four-panel layout (P, PET, cumulative levelled P−PET balance, network-mean well level) with an intervention line at January 2018 for the clearfell. The cumulative balance is detrended against the mean (P−PET) over a December 2004--December 2025 reference window (*DETREND_START*--*DETREND_END*); this removes the long-run climatological bias so the cumulative curve sits on zero rather than drifting linearly. The detrending mean is annotated on the figure for transparency.

The summer warming-trend figure (*00_03_summer_warming_trend.png*) is the only Script 00 figure that reads from the raw *RAF_Valley_Climate.csv* rather than from *01_climate.csv* --- the pipeline-filtered climate file contains P and PET only, not maximum temperatures. The figure plots the JJA (June--July--August) mean maximum temperature for each year of the full 95-year record as red/blue bars relative to the pre-2013 mean, with a linear OLS trend overlay and the post-2013 mean as a horizontal reference. Only years with all three summer months recorded are used. The figure is produced on the full-record profile only --- running it over the monitoring-period subset would remove the long baseline that makes the recent warming interpretable. Output CSVs accompany each figure; for the warming-trend figure the table includes the regression slope, intercept, R², p-value, pre/post-2013 means, and the post-2013 anomaly. This figure appears in the main report as Figure 4 in §4.1.1 *Climate record*.

### []{#anchor-255}[]{#anchor-256}[]{#anchor-257}Sub-script 12 --- Site overview map

Script 12 produces Figure 1 of the main report: a DEM hillshade over the full warren extent with every well in *Well_locations_height.csv* (currently 97 wells, including extended-network wells and lake-stage points) plotted as a red marker with a name label. The script reads the raw locations CSV, projects to EPSG:27700 (British National Grid), and overlays the local 1 m DEM (*newborough_dem.tif*) using *rasterio* with a custom topographic colormap. The colormap's *set_under(\'dodgerblue\')* paints any sub-zero elevation as water, and *TwoSlopeNorm* anchors the colour scale at 0 m sea level, 12 m at the slack-dune transition, and the true ridge maximum at the top. KML site features (forestry boundaries, broadleaf restock blocks, scrape sites) are added through *map_utils.add_kml_features* (F.5).

If the local DEM is absent or *rasterio* is not installed, the script falls back to a *contextily* OpenTopoMap basemap framed around the well bounding box plus a 300 m buffer. The fallback exists so the pipeline runs end-to-end on a reviewer's machine without the 1 m DEM; the published Figure 1 uses the local DEM render.

### []{#anchor-257}[]{#anchor-258}[]{#anchor-259}Sub-script 13 --- Experimental design map

Script 13 produces the BACI / scraping design figure used in §3 of the main report. The well coordinates come from the same raw CSV as Script 12, restricted by a tight bounding box (240,500--243,500 E × 362,700--364,800 N) that frames the clearfell zone and the scraping sites without the open dune to the south-east. CEH12 is dropped on coordinate grounds (out-of-area).

Each well's experimental role is assigned by *assign_category* using a strict priority order: clearfell tiers first (Impact → Edge → Forest Control → Coastal Control → Climate Control), then BACI exclusions (FE1--4, LIS1, NW8B, CEH42), then scraping roles (impact, local paired control, regional control), then background. The clearfell tier definitions are imported directly from *clearfell_common.IMPACT_WELLS*, *EDGE_WELLS*, *FOREST_CONTROL_WELLS*, *COASTAL_CONTROL_WELLS*, and *CLIMATE_CONTROL_WELLS* (S.7); under the live network this gives 1 + 4 + 5 + 2 + 5 = 17 BACI wells. Tier colours come from *clearfell_common.TIER_COLOURS* so the BACI map and the BACI analytical figures share a palette. Each tier gets a distinct marker shape (triangle, diamond, square, plus, circle) so the figure reads in greyscale as well as colour. The clearfell centroid, the felling boundary KML, and the CEH2→CEH34→WMC3 clearfell transect are overlaid; for the scraping analysis, dashed red lines connect each impact site to its local paired control.

The DEM hillshade underlay uses the same *rasterio* + custom topographic colormap as Script 12. The legend is grouped under three headings (clear-fell BACI, topographical scraping, analytical linkages) with empty *Line2D* separators acting as section breaks. Excluded BACI wells are drawn as grey crosses so the reader can see where the rejected wells sit relative to the felling boundary --- this is the figure's most useful diagnostic feature for anyone wanting to understand why the BACI network excludes the FE wells.

### []{#anchor-259}[]{#anchor-260}[]{#anchor-261}Sub-script 14 --- Climate projections

Script 14 reads *03_regional_averages.csv* (cluster-centroid hydrographs in m below ground) and computes per-cluster annual summer minima and winter maxima on a hydrological-year basis (year starts 1 October). Summer months are April--September; winter months are October--March; a minimum of three valid monthly readings is required for an annual minimum or maximum to be recorded. For each cluster, summer minima are fitted with *scipy.stats.linregress* and the trend is projected linearly from the first observation year to 2040, with a 95% confidence interval for the mean response (*fit_trend*). Winter maxima are computed and plotted as observation only --- no projection is fitted on the winter side because the report's framing is that summer minima are the climate-trajectory variable of interest, and winter exceedance is reported as an observed-frequency count against the Curreli flooding thresholds rather than as a forward projection. The observed-period winter trend (OLS slope, R², p-value, n-years) is nonetheless computed for each cluster and persisted to *14_winter_trend_stats.csv*; it is descriptive only and carries no projection, but it is written to a pipeline CSV so that any winter-trend figures cited in the report are sourced from a pipeline output rather than recomputed by hand from the raw annual extremes.

The three figure outputs are *14_climate_trajectory_summer.png* (summer panel, all five clusters, with the SD15b wet-slack and SD16 dry-slack viability lines at −0.61 m and −0.98 m), *14_climate_trajectory_winter_flooding.png* (winter panel against the SD15b_WINTER and SD16_WINTER flooding lines at −0.10 m and −0.25 m, with an in-figure exceedance-frequency box), and *14_climate_trajectory_stacked.png* (the two panels combined). A fourth output is an interactive Plotly HTML scatter of mean annual summer minimum versus mean annual winter maximum per well, coloured by cluster, with the Curreli thresholds overlaid. This is published as an Online Supplementary Tool on the project's GitHub Pages site (<https://newbroman.github.io/Newborough_Hydrology/>) rather than as a static report figure. Four CSV companions are written: *14_summer_trend_stats.csv* (per-cluster summer-minimum slope, R², p-value, n-years), *14_winter_trend_stats.csv* (the equivalent per-cluster winter-maximum statistics, descriptive only), *14_annual_extremes.csv* (annual minima and maxima per cluster), and *14_winter_exceedance.csv* (winter exceedance counts and percentages per cluster).

The framing in the report is deliberate: the OLS linear extrapolation is **not** a climate forecast --- it is an observed-trajectory baseline against which the UKCP18-based forecast in Script 21 (S.14 of this supplement) can be compared. Script 14 answers "where is the cluster heading at its observed rate of change"; Script 21 answers "where could the cluster end up under a UKCP18 scenario." The pairing is explicit in §5 of the main report.

### []{#anchor-261}[]{#anchor-262}[]{#anchor-263}Site-specific choices (suite-level)

-   **Two profiles in Script 00 (***full*\*\* and ***short***) rather than one.\*\* The well-network analysis runs over 2004--present; the climate context the report's §2 sets out runs over the full 95-year record. Producing both lets the report quote climate normals against either window without re-running the script. Both profiles are always generated; the function names retain the legacy "profile" terminology for clarity but there is no CLI flag to select one --- the orchestrator gets both.
-   **The summer warming-trend figure reads the raw climate CSV, not ***01_climate.csv***.** This is the only Script 00 output that needs temperatures (P and PET alone do not give a warming signal); Script 01's intermediate carries P and PET only. The departure from the "everything reads from intermediates" rule is intentional and limited to this one figure.
-   **DEM optional, OpenTopoMap fallback.** Scripts 12 and 13 both produce a usable figure without the local DEM raster, so the pipeline runs end-to-end on a reviewer's machine without the 1 m DEM. The published Figure 1 uses the local DEM.
-   **Script 13 uses imported tier definitions, never literals.** The script's BACI tier lists come from *clearfell_common.py*; changing a tier membership in one place automatically updates the design figure and the analytical scripts together. The excluded-well list (FE1--4, LIS1, NW8B, CEH42) is one of the few short literal lists in the script --- these are the wells the clearfell analysis dropped on baseline-stationarity and small-n grounds (S.7).
-   **Script 14 uses simple OLS rather than a more elaborate trend model.** The figure's purpose is the observed-trajectory baseline; UKCP18 scenarios (consolidated in *pipeline_params.py* and used by Script 21 in S.14) carry the forecast.
-   **No projection on the winter side.** The winter panel reports observed maxima against the Curreli flooding thresholds and an exceedance-frequency count; it does not extrapolate. The asymmetric treatment matches the report's framing.

### []{#anchor-263}[]{#anchor-264}[]{#anchor-265}Outputs

  ------------------------------------------------------------------ -------------------------------------------------------------- ----------------------------------------------------------------------
  Output                                                             Description                                                    Reference
  00_climate_summary/00_01_climate_timeseries\[\_short\].png         Monthly P, PET, balance, well level                            Report §2 (Figure)
  00_climate_summary/00_02_well_network_summary\[\_short\].png       Per-well record bar / summary                                  Report §2 (Figure)
  00_climate_summary/00_03_summer_warming_trend.png                  RAF Valley JJA max-temp anomaly, 1931--2025                    Report §4.1.1, Figure 4
  00_climate_summary/00_01_annual_climate_summary\[\_short\].csv     Annual P, PET, P/PET ratio                                     Report §2 (Table)
  00_climate_summary/00_02_well_network_summary\[\_short\].csv       Per-well record stats, summer min, winter max                  Report §2 (Table); Script 14 references *OUT_00_WELL_NETWORK\_TABLE*
  00_climate_summary/00_03_summer_warming_stats.csv                  Annual JJA means + OLS trend parameters                        Report §4.1.1
  12_figure_site_overview/12_01_dem_site_overview.png                DEM + 97-well site map                                         Report Figure 1
  13_figure_experimental_design/13_01_experimental_setup_map.png     Five-tier BACI + scraping design map                           Report §3 (BACI design figure)
  14_climate_projections/14_climate_trajectory_summer.png            Summer-minimum trajectories with 95% CI to 2040                Report §5
  14_climate_projections/14_climate_trajectory_winter_flooding.png   Winter-maximum observations vs Curreli winter thresholds       Report §5
  14_climate_projections/14_climate_trajectory_stacked.png           Combined summer + winter panel                                 Report §5
  14_climate_projections/14_summer_trend_stats.csv                   Per-cluster summer-minimum OLS parameters                      Report §5
  14_climate_projections/14_winter_trend_stats.csv                   Per-cluster winter-maximum OLS parameters (descriptive only)   Report §5
  14_climate_projections/14_annual_extremes.csv                      Annual summer min / winter max per cluster                     Report §5
  14_climate_projections/14_winter_exceedance.csv                    Winter exceedance counts per cluster                           Report §5
  14_climate_projections/14_seasonal_extremes_scatter.html           Interactive per-well scatter, summer min vs winter max         Online Supplementary Tool (GitHub Pages)
  ------------------------------------------------------------------ -------------------------------------------------------------- ----------------------------------------------------------------------

All paths resolve through *utils/paths.py* (*OUT_00\_\**, *OUT_12_DEM_OVERVIEW*, *OUT_13_EXPERIMENTAL_MAP*, *OUT_14\_\**).

### []{#anchor-265}[]{#anchor-266}[]{#anchor-267}Where the result appears in the report

-   §2 *Site setting* --- Figure 1 from Script 12 (DEM render); climate-baseline figures and tables from Script 00.
-   §3 *Methodology* --- BACI design map from Script 13.
-   §4.1.1 *Climate record* --- Figure 4 (RAF Valley summer warming trend) from Script 00.
-   §5 *Discussion / climate trajectory* --- summer- and winter-trajectory figures and exceedance summary from Script 14; the Script 00 warming-trend figure (§4.1.1 / Figure 4) provides the long-baseline temperature context that §5 draws on.
-   Online Supplementary Tool --- seasonal-extremes scatter from Script 14, hosted at the project's GitHub Pages site.

### []{#anchor-267}[]{#anchor-268}[]{#anchor-269}Cross-references

-   **F.3** --- SSM formulation that drives the cluster centroids that Script 14 reads.
-   **F.4** --- Curreli thresholds (*SD15b*, *SD16*, *SD15b_WINTER*, *SD16_WINTER*); cluster colours and labels; *REFERENCE_CUTOFF_DATE*.
-   **F.5** --- *map_utils.add_kml_features* rendering helper used by Scripts 12 and 13.
-   **S.1** --- *01_climate.csv* and *01_wells_clean.csv* consumed by Script 00.
-   **S.3** --- *03_regional_averages.csv* consumed by Script 14.
-   **S.7** --- *clearfell_common.py* tier definitions consumed by Script 13.
-   **S.14** --- Script 21 forestry scenarios, which use UKCP18 climate constants from *pipeline_params.py* for the forecast model that Script 14's linear extrapolation does not provide.

### []{#anchor-269}[]{#anchor-270}[]{#anchor-271}S.8.5 Script 14b --- Bootstrap year-of-crossing (post-review addition, Phase 4 step 16)

Script 14b was added on 2026-05-29 following the post-review pass on the main report. Conclusion 11 of the report previously read "*summer minimum trends indicate C1 summer minima approaching the SD16 dry slack viability threshold around 2030--2032 under current trajectories*", with the qualitative date band taken from a reading of Script 14's per-cluster summer-trend slopes but without a stated confidence interval. Script 14b replaces the qualitative band with a bootstrap CI on the crossing year per cluster × threshold, anchored in the same annual summer-minimum series that Script 14 produces.

**Procedure.** For each of the five clusters, the per-cluster annual summer-minimum series (*outputs/14_climate_projections/14_annual_extremes.csv* from Script 14) is fitted as a linear trend over the observed years. A non-parametric bootstrap (n = 1000 replicates) resamples years with replacement; for each resample the trend is refitted and the year at which the linear extrapolation crosses each Curreli threshold (SD15b = 0.61 m below ground, SD16 = 0.98 m below ground) is computed. The script tabulates 5th, 50th and 95th percentile crossing years per cluster × threshold and renders a five-panel figure showing observed minima, the OLS trend with 90% bootstrap CI cone, threshold lines and crossing-year CI bands.

**Headline result (2026-05-29).** The C1 SD16 crossing year, central to Conclusion 11, has a median of 2022 with a 90% confidence interval of 2017--2042 (5th--95th percentile of the bootstrap distribution). Four of the eight most recent observed C1 summer minima have already exceeded the SD16 depth (2018, 2019, 2022, 2025); 2023 sits just above the threshold at −0.92 m. The cluster is no longer approaching the threshold but oscillating across it. The wide confidence interval reflects substantial year-to-year variability in summer minima against a shallow trend slope of −9.7 mm yr⁻¹, not measurement uncertainty in the underlying slope estimate. C2 has crossed SD16 in the trend sense around 2011, with the CI extending into the pre-monitoring period (the cluster's observed minima have been below SD16 throughout the record). C3 lies above SD16 and its non-significant trend reaches the threshold beyond the 2080 horizon. C4 and C5 sat below SD16 throughout the observed record --- the forest-zone clusters do not host slack vegetation, so the threshold projection is reported for completeness rather than as an ecological signal.

**Inputs.** *outputs/14_climate_projections/14_annual_extremes.csv* (Script 14 output); Curreli thresholds from *utils.config* (*SD15b*, *SD16*).

**Outputs.** Sharing *paths.DIR_14* with Script 14: - *14b_year_of_crossing.csv* --- per-cluster × threshold table with median + 5th/95th percentile crossing years, OLS slope, intercept, and current-year (2025) predicted depth. - *14b_year_of_crossing.png* --- five-panel figure (one per cluster) showing observed minima, OLS trend, 90% bootstrap CI cone (5th--95th percentile), threshold lines and crossing-year CI bands. - *14b_year_of_crossing_results.md* --- memo with headline table, decision rule, and caveats.

No new path constants were added in *paths.py*; Script 14b shares *paths.DIR_14* with Script 14 since the input lives there.

**Limitations.** Linear extrapolation. The bootstrap captures sampling uncertainty in slope and intercept but not model-form uncertainty (the assumption that the linear trend extrapolates cleanly into a regime where summer-min approaches a drainage-controlled basement or where climate trajectory diverges from observed). The per-cluster centroid summer-minimum averages over wells with different ground elevations within each cluster, so the threshold is an effective threshold against the centroid, not against any specific well. Year-resampling bootstrap preserves the trend signal but does not preserve year-to-year autocorrelation; for trends with strong autocorrelation a block bootstrap would be marginally wider. Inspection of the summer-minimum residuals against the per-cluster linear trends does not show strong autocorrelation in the C1 series, so a block bootstrap is unlikely to materially widen the CI.

Cross-references.

-   §7 Conclusion 11 of the main report --- the "around 2030--2032" qualitative date band is replaced by the bootstrap CI from this script (median 2022, 90% CI 2017--2042 for C1 SD16).
-   §4.10.1 of the main report --- the figure *14b_year_of_crossing.png* lands here as supporting evidence for the seasonal-prediction discussion in §5.2.4.

Spring-mean centroid trend (Script 14 v1.4.x). Script 14 gains a spring-mean (Mar--May) cluster-centroid trend alongside its summer-minimum and winter-maximum trends, on the same descriptive-OLS footing from 03_regional_averages.csv, emitting 14_spring_trend_stats.csv (same columns as 14_summer_trend_stats.csv) and a trajectory figure 14_climate_trajectory_spring.png (observed means with per-cluster OLS trends; no projection and no threshold bands). Unlike the summer minimum and winter maximum --- indexed by the October-start hydrology year --- the spring mean sits wholly inside a calendar year and is indexed by calendar year (as Script 36 does, S.20). The spring trend is flat for every cluster except C5 (Coastal Forest, −0.038 m yr⁻¹, p = 0.020); see Supplementary Note S8.

## []{#anchor-271}[]{#anchor-272}[]{#anchor-273}S.9 Scripts 11, 11b --- Forecasting and spatial thresholds

Steps 11 and 12 / 27. Phase 4 --- Climate and spatial context.

The pair implements the §3.6 *Forecasting* methodology of the main report at two scales. Script 11 produces cluster-level temporal forecasts --- peak winter flood and summer drought transfer functions, plus the iterated closed-form P_flood that is the chapter's headline management tool. Script 11b applies the same threshold framework per-well, producing spatial maps of where the network sits relative to the Curreli et al. (2013) thresholds, the BACI-derived recovery limits, and the per-well P_flood surface (the §3.6.3 figure). The pair share the Curreli thresholds (F.4), the cluster β from Script 03's mechanistic table, hydrological-year indexing, and the iterated P_flood derivation in *model_utils.pflood_lambda()*; they differ only in aggregation level. Refer to F.3 for the SSM, F.4 for the constants and partition, and F.5 for the shared utilities.

### []{#anchor-273}[]{#anchor-274}[]{#anchor-275}Inputs (suite-level)

  ----------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------
  Input file                                      Source / description
  03_03_cluster_mechanistic_coefficients.csv      Script 03 --- cluster centroid β₁, β₂, β₃ and p-values
  03_master_data.csv                              Script 03 --- per-well β₁, β₂, β₃ (used in 11b for reference wells)
  03_regional_averages.csv                        Script 03 --- cluster centroid hydrographs plus monthly P_mm, PET_mm
  03_cluster_peak_months.csv                      Script 03 --- per-cluster mean peak-of-record month
  01_wells_clean_maod.csv                         Script 01 --- reference network maOD series (used by 11b)
  01_wells_clean.csv                              Script 01 --- reference network depth-below-pipe-top series (used by 11b for per-well climatology in the forecaster bundle)
  01_wells_extended.csv                           Script 01 --- extended network raw depths (used by 11b)
  01_well_elevations.csv                          Script 01 --- *DEM_Ground_Elev*, *Pipe_Top_Elev* (used by 11b)
  01_locations.csv                                Script 01 --- easting/northing (used by 11b)
  06_pear_membership_audit_sitewide.csv           Script 06 --- extended well cluster assignments
  *data/Features.kml*, *data/site_boundary.kml*   Site overlay and interpolation domain
  ----------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------

### []{#anchor-275}[]{#anchor-276}[]{#anchor-277}Sub-script 11 --- Cluster-level temporal forecasting

#### []{#anchor-277}[]{#anchor-278}Motivation

Script 11 takes Script 03's cluster-centroid SSM coefficients and answers five management-relevant forecasting questions. What rainfall is required to recover the slack from a known summer minimum (Section 2, empirical peak-flood transfer function)? What rainfall threshold triggers winter flooding to the slack floor (Section 3, the iterated P_flood, the chapter's headline)? Given a winter peak, how dry will the following summer get (Section 4, summer-drought transfer function)? Given the same winter peak, what will the *spring* mean be --- the metric the van Willegen 2025 monitoring framework uses (Section 5, added at Script 11 v1.1.1; documented in full in S.18b as Tool A)? And --- restated for the transcript --- what are the cluster-centroid coefficients that everything downstream rests on (Section 1)? The sections are independent and write to separate output CSVs.

#### []{#anchor-278}[]{#anchor-279}Methodology

**Shared infrastructure.** All four sections operate on *03_regional_averages.csv*, which carries monthly cluster-centroid hydrographs (*C1*--*C5* and block aliases *Lake_Edge*, *Eastern_Block*, *Western_Block*, *Forest*, *Coastal_Forest* --- one alias per cluster under k=5) alongside monthly *P_mm* and *PET_mm*. Hydrological year indexing --- *Hydro_Year = year + (month \>= 10)* --- keeps each recharge cycle (winter rainfall → spring peak → summer drawdown → autumn minimum) in one year. *MIN_VALID_MONTHS = 3* requires three observed months in both Apr--Sep and Oct--Mar for a hydrological year to enter a regression. A *\_Tee* context manager mirrors *print()* output to *11_forecast_01_results.txt* so regression summaries are recoverable without re-running.

**Section 1 --- Mechanistic state-space equations.** Reads *03_03_cluster_mechanistic_coefficients.csv*, extracts cluster centroid β₁, β₂, β₃, R² and p-values, and converts β₁ and β₂ from m/m to m/mm (divide by 1000) for dimensional consistency with the climatological P and PET in millimetres used by Section 3. β₃ is dimensionless and used as-is, with an *abs()* guard. The section is the bridge from S.3's analytical output to the §3.6 forecast equations; under the live partition all five clusters report.

**Section 2 --- Peak flood transfer functions.** For each block column in the regional-averages frame, the script computes a per-hydrological-year triple --- summer minimum (*h_min*, Apr--Sep minimum of the centroid hydrograph), cumulative winter rainfall (*P_winter*, Oct--Mar sum of *P_mm*), and winter maximum (*h_peak*, Oct--Mar maximum) --- and fits an OLS regression with intercept

> h_peak = β₁ · P_winter + β₂ · h_min + c

β₁ here is the regression slope on winter rainfall, not the SSM β₁ of Section 1 (the symbol-reuse is unfortunate but harmless because the regression is separately reported). Output *11_forecast_winter_transfer_functions.csv* (Table 6). Forecast use: given an observed summer minimum and a forecast winter rainfall (e.g. a UKCP18 percentile), predict the winter peak.

**Section 3 --- Critical rainfall thresholds (the iterated P_flood).** The headline forecasting tool of the chapter. The April 2026 revision replaced an earlier single-step inversion of the SSM with an iterated closed-form solution, because the single-step form neglected winter PET (≈30% of winter atmospheric demand at RAF Valley) and implicitly treated the six-month recharge season as one SSM timestep --- an approximation that produced physically implausible thresholds at the cluster extremes. The iterated form starts from the monthly recurrence with displacement-formulation drainage, written in collapsed form as

> h(t) = α · h(t−1) + β₁ · λ · P̄(t) − β₂ · PĒT(t) − β₃ · z₀, α = 1 − β₃

where P̄(t) and PĒT(t) are the long-term monthly climatologies indexed by calendar month, λ is the rainfall multiplier being solved for, and z₀ = *DRAINAGE_DATUM* = 3.7 m. Iterating from a summer-minimum head h₀ over n months gives

> hₙ = h₀ · αⁿ + β₁ · λ · S_P − β₂ · S_E − z₀ · (1 − αⁿ)

with the drainage-weighted climatology sums

> S_P = Σᵢ α\^(n−1−i) · P̄(mᵢ), S_E = Σᵢ α\^(n−1−i) · PĒT(mᵢ)

Setting hₙ = h_target = 0 (the slack-floor / ground-surface target) and solving for λ:

> λ = ( h_target − h₀ · αⁿ + β₂ · S_E + z₀ · (1 − αⁿ) ) / ( β₁ · S_P ), P_flood = λ · Σ P̄ᵢ

The *+z₀·(1−αⁿ)* term in the numerator is the accumulated effect of the displacement-formulation drainage constant; without it the threshold is systematically too low. The forecast horizon for each cluster runs from October to that cluster's historical peak-of-record month, loaded from *03_cluster_peak_months.csv*. Under the current partition the horizons are short --- three to five months --- because Newborough's slacks peak in late winter rather than late spring. The closed-form is collapsed for spreadsheet use into

> P_flood = A · d + B

where d is the well's depth below ground at summer minimum entered as a positive metre value (so h₀ = −d); A and B are written out per cluster in *11_forecast_pflood_threshold_equations.csv* with the spreadsheet formula string *=(A·A2+B)*. A reviewer-friendly summary CSV *11_forecast_pflood_summary.csv* carries A, B, λ, horizon, peak month, and P_clim_total in fewer columns. The legacy single-step value is retained in column *P_flood_old_single_step_mm* for continuity but is not used downstream.

The implementation calls *model_utils.pflood_lambda()* (F.5), which is the single source of truth for the closed form and is also the function 11b calls for the per-well map. A negative or non-finite λ flags the target as unreachable from h₀ under positive rainfall, and the script writes NaN to P_flood for that cluster.

**Section 4 --- Summer drought transfer functions.** The mirror-image regression: for each block, fit

> h_min_summer = β₁ · P_summer + β₂ · h_max_winter + c

over the same hydrological-year indexing, predicting the summer minimum from antecedent winter peak and summer rainfall. Output *11_forecast_summer_transfer_functions.csv* (Table 7). The forecast use is to bound the drought risk implied by a known winter peak under a UKCP18 summer climate, complementing Section 2's flood-direction prediction.

**Section 5 --- Spring MSL transfer functions (Tool A).** Tool A sits alongside the Phase 13 van Willegen 5-year MSL aggregation (Script 26, S.18). For each cluster, fit *MSL_y = α·h_max_winter + β·P_win_to_spr + γ·PET_win_to_spr + intercept* using van Willegen's hydrology year B (1 Jun *y*−1 to 31 May *y*; see F.2). The response is the cluster-centroid mean of {March, April, May} water levels in hydrology year *y*; the predictors are the cluster-centroid October-to-February maximum, the cumulative October-to-May rainfall, and the cumulative October-to-May PET. The fits read from *03_regional_averages.csv* --- the same Method B baseline that Tool B's UKCP18 projection uses (see S.18 §Method A and Method B aggregation). Output *11_forecast_spring_transfer_functions.csv* (Table 9) plus a per-cluster calibration scatter at *11_forecast_02_spring_calibration.png*. R² ranges 0.73 (Lake Edge) to 0.96 (Coastal Forest). A previous-MSL variant was tested at v1.1.0 and dropped at v1.1.1 on empirical grounds (previous-MSL R² 0.18--0.44; coefficient non-significant at four of five clusters). The full Tool A treatment --- coefficient table, manager workflow, rejected-variant discussion --- is in S.18b §S.18b.2.

#### []{#anchor-279}[]{#anchor-280}Site-specific choices (Script 11)

-   **Block columns under k=5 are one per cluster, not three.** *BLOCK_COLUMNS* is *\[Lake_Edge, Eastern_Block, Western_Block, Forest, Coastal_Forest\]*. The historical "Eastern / Western / Forest" three-way split survives only as labelling; the regressions are fitted at cluster-centroid level.
-   **Hydrological year starts 1 October.** Standard UK water-year convention.
-   *MIN_VALID_MONTHS = 3*\*\* per season.\*\* Empirical --- large enough to suppress dropout-driven outliers, small enough not to discard years where a month's reading was missed.
-   *EXCLUDED_CLUSTERS*\*\* is empty under k=5.\*\* Legacy from the k=6 partition where two singleton clusters were excluded; both were cleaned out at the partition step (F.4). The hook is kept rather than the logic deleted.
-   *h_target = 0*\*\* everywhere in Section 3.\*\* Section 3 solves for the rainfall that brings the water table to the ground surface (slack-floor flooding), not the Curreli SD15b/SD16 winter flooding levels. Solving for those is a one-line change to *model_utils.pflood_lambda*, but the report quotes the slack-floor figure as the management-relevant restoration threshold.

#### []{#anchor-280}[]{#anchor-281}Outputs (Script 11)

  ---------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------
  Output                                                                 Description
  11_forecasting_thresholds/11_forecast_01_results.txt                   Full transcript of the five-section run
  11_forecasting_thresholds/11_forecast_winter_transfer_functions.csv    Table 12 --- winter peak prediction equations per cluster
  11_forecasting_thresholds/11_forecast_summer_transfer_functions.csv    Table 13 --- summer drought prediction equations per cluster
  11_forecasting_thresholds/11_forecast_pflood_threshold_equations.csv   Full iterated P_flood derivation (one row per cluster, 20+ columns). Detail behind report Tables 14/15; not itself a numbered report table
  11_forecasting_thresholds/11_forecast_pflood_summary.csv               Reviewer-friendly summary: A, B, λ, horizon, P_flood per cluster
  11_forecasting_thresholds/11_forecast_spring_transfer_functions.csv    Spring MSL transfer functions per cluster (Section 5; Tool A in S.18b). In the report this appears as an inline equation in §3.6, not a numbered table
  11_forecasting_thresholds/11_forecast_02_spring_calibration.png        Per-cluster calibration scatter for Section 5; in-supplement figure for S.18b
  ---------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------

#### []{#anchor-281}[]{#anchor-282}Limitations (Script 11)

-   **Transfer-function forecasts inherit the regression residuals.** Sections 2, 4, and 5 are empirical linear regressions on \~20 hydrological years per block. The R² per block reported in the CSVs should be quoted alongside any forecast use.
-   **The iterated P_flood uses cluster-centroid β only.** Within-cluster heterogeneity in β₁, β₂, β₃ is not resolved at this scale; the 11b per-well map is the refinement where it matters. The closed form also assumes uniform rainfall scaling and climatological PET --- real winters depart from both, but the SSM's linearity means a more elaborate stochastic forecast would not change the threshold magnitudes much.

### []{#anchor-282}[]{#anchor-283}[]{#anchor-284}Sub-script 11b --- Per-well spatial threshold maps

#### []{#anchor-284}[]{#anchor-285}Motivation

Script 11b applies the threshold framework per-well. The core map products are a summer-minima depth map (binned against the Curreli SD15b/SD16 thresholds and the BACI recovery limits), a winter-maxima depth map (against the Curreli winter flooding thresholds), and the P_flood spatial map --- the per-well iterated rainfall threshold from §3.6.3, the chapter's principal spatial figure. A flood-frequency map, a Table 10 spreadsheet export, and an interactive forecaster HTML are written alongside.

#### []{#anchor-285}[]{#anchor-286}Methodology

**Shared infrastructure.** *load_well_data()* returns a single per-well DataFrame combining reference-network maOD series (with cluster assignments from *03_master_data.csv* and per-well SSM coefficients) and extended-network wells (with cluster assignments from *06_pear_membership_audit_sitewide.csv* and no per-well β). For each well, *\_summer_mins()* returns August--September minima per year and the across-years mean is the well's mean summer minimum; depth below ground is *DEM_Ground_Elev* minus that mean. *\_winter_maxima()* computes the October--March maximum per hydrological year with a three-month-minimum-data threshold. Two wells (CEH18, CEH21) scraped in October 2023 are handled by reducing the DEM elevation by the scrape depth (0.50 m and 0.70 m respectively, listed in the script's *SCRAPED* dict). The full observed record is used for the maOD water-table averaging: maOD readings are invariant to ground-surface scraping (the water table sits at the same absolute elevation before and after material is removed), so pre-2023 maOD observations remain physically valid alongside post-2023 ones. Only the DEM (subtracted to compute depth-below-ground) is era-specific.

**Summer minima depth map (***plot_summer_minima_map***).** Per-well summer-minimum depths are binned against five zones derived from the Curreli thresholds plus the BACI recovery margins: wet-slack viable (\< 0.61 m), SD15b-recoverable (0.61--0.75 m), SD16 dry slack (0.75--0.98 m), SD16-recoverable (0.98--1.20 m), and beyond single-scraping recovery (\> 1.20 m). The recovery limits encode the BACI scraping benefit of +0.144 m at CEH36 (S.6) --- a shallow scrape recovers \~0.14 m, a deeper scrape \~0.22 m --- so a well within those increments of the relevant Curreli threshold is flagged as recoverable. An interpolated background surface is rendered by *map_utils.add_idw_surface()* on the standard 50 m site grid, with the project-standard ridge mask suppressing cells where the DEM exceeds the IDW-interpolated well DEM by more than 1 m (inter-dune ridges that lie between wells and would otherwise be coloured by an unrepresentative interpolation).

**Winter maxima depth map (***plot_winter_maxima_map***).** Same approach at the winter peak. The five-zone summer scheme collapses to four winter zones because the Curreli winter framework is shorter: flooding (peak above the surface, depth \< 0 m), SD15b winter met (0--0.10 m), between SD15b and SD16 winter (0.10--0.25 m), and below SD16 winter (\> 0.25 m). The map identifies slacks where the winter peak no longer reaches the level required by the Curreli wet/dry typology.

**P_flood spatial map (***plot_pflood_map***).** The chapter's principal figure. For each well, the iterated closed-form is solved by *model_utils.pflood_lambda()* with the well's mean summer minimum as h₀ (h₀ = −depth_bg under the SSM sign convention), the cluster-specific October-to-peak-month horizon, and the RAF Valley monthly climatology averaged from *03_regional_averages.csv*. The β coefficients are selected by a two-tier hybrid: per-well β₁, β₂, β₃ from *03_master_data.csv* for reference-network wells, falling back to cluster-centroid β from *03_03_cluster_mechanistic_coefficients.csv* for extended-network wells that have no per-well fit. Wells with non-finite P_flood or λ \< 0 are flagged unreachable, excluded from the surface, and written to the per-well CSV with diagnostic columns (*alpha*, *S_P_mm*, *S_E_mm*, *lambda*, *unreachable*). The interpretive frame on the map is the climatological mean winter rainfall of 521 mm (*MEAN_WINTER_RAINFALL_MM*): wells whose P_flood is below 521 mm receive enough rainfall in a mean winter to flood the slack; wells above 521 mm need a wetter-than-average winter, with P_flood / 521 indicating how much wetter.

**Flood-frequency map and P_flood spreadsheet / forecaster.** *plot_flood_frequency_map* computes, for wells with at least five hydrological years of winter-maxima data, the fraction of years where the winter maximum reached the well's DEM (ground surface); rendered as a per-well percentage on the same 50 m grid. The map is the observational companion to P_flood: P_flood is what rainfall *would* flood under climatology, the flood-frequency map is how often it *has* under the observed record. *export_table10_spreadsheet()* re-exports Script 11's full P_flood derivation as the report's compact Table 10 (cluster, horizon, A·d + B, P_clim total, spreadsheet formula). *build_forecaster_html()* writes a single-page interactive tool that presents the report's three forecast equations as a calculator at cluster level: Forecast 1 uses Table 6 (winter peak from summer minimum), Forecast 2 uses Table 7 (summer minimum from winter peak), Forecast 3 uses Table 10 (P_flood from depth). Each forecast renders in three lines --- general equation, substituted values, result --- so the user sees exactly which published equation is being evaluated and with what inputs. The May 2026 simplification (*CHANGELOG_forecaster_simplification.md*) removed an earlier per-well SSM-iteration mode that the report does not validate; the forecaster is now cluster-level only by design.

The data bundle that backs the forecaster is built by *\_build_forecaster_data_bundle()* and carries: the cluster coefficients (β₁, β₂, β₃, peak_month, slope_A, intercept_B, P_clim_total) merged from Script 03's mechanistic table and Script 11's Table 8; the block transfer functions from Tables 6 and 7; the monthly RAF Valley P climatology; the well metadata (location, DEM, cluster assignment, *nearest_cluster_only* flag); and per-well twelve-month depth climatologies computed from *01_wells_clean.csv* (wells with fewer than 24 monthly observations or missing any calendar month are skipped and the well-details panel falls back to its cluster's climatology). The per-well climatology lets the panel show each well's own typical depths --- this month, summer minimum at the well's trough month, winter peak at the well's peak month --- above the matching cluster row, so the user can see how a specific dipwell sits relative to its cluster typical. The trough and peak months are computed per well and can differ from the cluster's (CEH9, C2, troughs in September against the C2 cluster trough in August, for instance). *\_raf_valley_winter_mean* fetches the live Met Office RAF Valley monthly record at build time and falls back to 521 mm if the fetch fails.

#### []{#anchor-286}[]{#anchor-287}Site-specific choices (Script 11b)

-   **August--September summer-minimum window** rather than the Apr--Sep window used in Script 11 Section 2. The narrower window captures the ecologically critical late-summer minimum more tightly; the broader window is appropriate for the hydrological-year regression structure but would dilute the late-summer signal on a per-well status map.
-   **DEM corrections for CEH18 (−0.50 m) and CEH21 (−0.70 m)**, both scraped October 2023. Corrected ground elevation is used for depth-below-ground. The full observed maOD record is used for the water-table averaging (maOD is invariant to surface change); only the DEM is era-specific.
-   **Recovery limits derived from the BACI scraping benefit.** *SD15b_REC = 0.75 m* and *SD16_REC = 1.20 m* encode the +0.144 m demonstrated benefit at CEH36 (S.6) as a per-well recovery target.
-   **Hybrid β architecture for the P_flood PNG map.** Per-well β for reference-network wells (full per-well dynamics), cluster-centroid β fallback for extended-network wells (cluster dynamics, well-specific h₀). The split is data-driven: extended wells have shorter records and were not refitted individually in Script 03.
-   **Forecaster is cluster-level only.** The interactive forecaster presents the report's three forecast equations --- Tables 6, 7, 10 --- as a calculator at cluster level. An earlier per-well SSM-iteration mode was retired in the May 2026 simplification (*CHANGELOG_forecaster_simplification.md*) because the report validates predictions only at cluster level. The per-well structure that does survive in the forecaster is the long-term depth climatology displayed in the well-details panel: each dipwell's own typical depths shown above its cluster's, so users can read where a specific well sits relative to its cluster typical.
-   **50 m IDW grid** for all surface interpolations --- the project-standard grid shared with Scripts 07, 19, 20, 25 (F.5).
-   *NEAREST_CLUSTER_ONLY_WELLS = {ceh3, ceh4, ceh7, ceh8, ceh37}* --- five wells flagged in the forecaster as "nearest-cluster pattern match" because their hydrograph correlates with a canonical cluster centroid but they sit outside the SSM operational domain (tidal boundary, upstream exclusions). The label is informational; P_flood is still computed.
-   **Site-boundary KML preferred for the interpolation mask** (*data/site_boundary.kml*, the dissolved SAGA stream-cell boundary), with a rectangular sea-boundary fallback.

#### []{#anchor-287}[]{#anchor-288}Outputs (Script 11b)

  -------------------------------------------------------------- ----------------------------------------------------------------------------------------------------------------------------------
  Output                                                         Description
  11b_spatial_thresholds/11b_01_summer_minima_depth.png          Per-well summer-minimum depth map, five Curreli + recovery zones
  11b_spatial_thresholds/11b_02_winter_maxima_depth.png          Per-well winter-maximum depth map, four Curreli winter zones
  11b_spatial_thresholds/11b_03_pflood.png                       Per-well iterated P_flood spatial map (the §3.6.3 figure)
  11b_spatial_thresholds/11b_03_pflood_per_well.csv              Per-well P_flood, λ, α, S_P, S_E, h₀, coeff_source, unreachable flag
  11b_spatial_thresholds/11b_04_flood_frequency.png              Per-well winter-flooding-frequency map (% of years reaching surface)
  11b_spatial_thresholds/11b_05_table10_pflood_spreadsheet.csv   Report Table 15 --- cluster-specific linear P_flood forms (cluster A, B, horizon, P_clim total); legacy *table10* filename token
  11b_spatial_thresholds/forecaster.html                         Interactive single-page forecaster tool
  -------------------------------------------------------------- ----------------------------------------------------------------------------------------------------------------------------------

#### []{#anchor-288}[]{#anchor-289}Limitations (Script 11b)

-   **Per-well DEM elevations carry sampling uncertainty.** The DEM is a LiDAR raster; per-well point elevations are sampled from it. The error is small relative to the Curreli threshold spacing but is not zero, particularly on inter-dune slopes where the raster gradient is steepest.
-   **The recovery limits assume scraping at the per-well location is operationally feasible.** Many wells flagged as "recoverable" sit inside the SSSI core, on protected vegetation, or in locations where mechanical scraping is impractical. The map is a hydrological recovery surface, not a management feasibility surface.
-   **The BACI scraping benefit is a single-site mean.** The +0.144 m at CEH36 from Script 09a is the empirical evidence base for the recovery margins. Transferability to other locations within the warren is plausible but not directly demonstrated.
-   **The 0.22 m SD16 recovery increment is an operational extrapolation, not a direct empirical observation.** The 0.14 m SD15b recovery margin is anchored on the +0.144 m mean benefit at CEH36 directly. The 0.22 m SD16 recovery margin instead represents the assumption that a *deeper* scraping than the CEH36 intervention would achieve a proportionately larger benefit --- closer to the maximum observed within-record gain rather than the mean. Both anchors should be read as planning targets rather than as point predictions: shallow excavation is taken to achieve \~0.14 m of recovery on the SD15b side, and a deeper excavation to achieve \~0.22 m on the SD16 side, with neither value carrying a quantified uncertainty band.
-   **The IDW surface is a piecewise-linear triangulation, not a true inverse-distance weighting.** *map_utils.add_idw_surface* is named "IDW" but calls *scipy.interpolate.griddata* with *method=\'linear\'* --- Delaunay triangulation with linear barycentric interpolation. For zone-status reading, the per-well markers are authoritative; the surface is a visual aid.
-   **Per-well β for the P_flood map can be noisy at network edges.** Wells with short records produce per-well β values with wide CIs in *03_master_data.csv*; the P_flood map does not propagate this uncertainty.

### []{#anchor-289}[]{#anchor-290}[]{#anchor-291}Site-specific choices and limitations (suite-level)

-   **One threshold framework, two scales.** The Curreli thresholds (F.4), the BACI recovery margins, the iterated P_flood derivation, and the *model_utils.pflood_lambda* implementation are shared between the two scripts. Script 11 produces cluster-level temporal forecasts; Script 11b produces per-well spatial status. Anything keyed by cluster ID --- peak months, mechanistic β --- flows from Script 03 to both.
-   **Iterated closed-form P_flood.** Both scripts use *model_utils.pflood_lambda*. The single-step formulation is retained only in Script 11's output CSV column *P_flood_old_single_step_mm* and is not used downstream.
-   **The P_flood threshold is a closed-form linearisation of the SSM.** Exact under the linear recurrence with uniform rainfall scaling and climatological PET; departures from linearity (the saturation behaviour as the water table approaches the ground surface, unmeasured ridge-recharge subsidies at C4/CEH14) are not captured. The threshold should be read as the rainfall that would flood the slack *under the SSM's assumed dynamics*, not as a hydrodynamic forecast.
-   *MEAN_WINTER_RAINFALL_MM = 521* is the 2005--2026 monitoring-period Oct--Mar mean. Climatologies from the full Met Office record back to 1930 differ slightly. The forecaster fetches the live record at build time and recomputes; the static script value is the report-cited figure.
-   **One peak-month per cluster.** Within-cluster heterogeneity in peak timing is not resolved by the cluster-level peak-month CSV. Wells in the spatial map inherit their cluster's peak month as the horizon end.

### []{#anchor-291}[]{#anchor-292}[]{#anchor-293}Outputs (consolidated)

  ---------------------------------------------------------------------- -------- ----------------------------------------------
  Output file                                                            Script   Description
  11_forecasting_thresholds/11_forecast_01_results.txt                   11       Transcript
  11_forecasting_thresholds/11_forecast_winter_transfer_functions.csv    11       Table 6, winter transfer functions
  11_forecasting_thresholds/11_forecast_summer_transfer_functions.csv    11       Table 7, summer transfer functions
  11_forecasting_thresholds/11_forecast_pflood_threshold_equations.csv   11       Table 8, full P_flood derivation per cluster
  11_forecasting_thresholds/11_forecast_pflood_summary.csv               11       Reviewer-friendly P_flood summary
  11b_spatial_thresholds/11b_01_summer_minima_depth.png                  11b      Summer minima zone map
  11b_spatial_thresholds/11b_02_winter_maxima_depth.png                  11b      Winter maxima zone map
  11b_spatial_thresholds/11b_03_pflood.png                               11b      Per-well P_flood spatial map
  11b_spatial_thresholds/11b_03_pflood_per_well.csv                      11b      Per-well P_flood with diagnostics
  11b_spatial_thresholds/11b_04_flood_frequency.png                      11b      Winter flooding frequency map
  11b_spatial_thresholds/11b_05_table10_pflood_spreadsheet.csv           11b      Table 10, spreadsheet-ready
  11b_spatial_thresholds/forecaster.html                                 11b      Interactive forecaster tool
  ---------------------------------------------------------------------- -------- ----------------------------------------------

### []{#anchor-293}[]{#anchor-294}[]{#anchor-295}Where the result appears in the report

-   §3.6 *Forecasting* --- Script 11 methodology and Tables 6, 7, 8, 9 (Table 9 = Section 5 spring MSL transfer function, Tool A in S.18b).
-   §3.6.3 *P_flood management tool* --- the iterated closed-form derivation; report Tables 14 and 15 (per-cluster P_flood summary and cluster collapsed linear equations); and the per-well P_flood map from 11b.
-   §4 --- Curreli-zone spatial maps from 11b (summer minima and winter maxima depth maps).
-   §4 --- winter flooding frequency map from 11b.

### []{#anchor-295}[]{#anchor-296}[]{#anchor-297}Cross-references

-   **F.3** --- SSM equation form, drainage datum, sign conventions; the basis for the iterated P_flood derivation.
-   **F.4** --- Curreli ecohydrological thresholds (*SD15b*, *SD16*, *SD15b_WINTER*, *SD16_WINTER*, *SD15b_REC*, *SD16_REC*), *MEAN_WINTER_RAINFALL_MM*, cluster colours and labels. The new MSL-aggregation constants subsection covers *MSL_SPRING_MONTHS*, *MSL_HYDRO_YEAR_START_MONTH*, and the *MSL_MIN\_\** strictness rules consumed by Section 5's hydrology-year-B partitioning.
-   **F.5** --- *model_utils.pflood_lambda()* (shared by both scripts), *map_utils.add_idw_surface()* for the 50 m grid, *paths.py* for all output paths.
-   **S.3** --- Script 03 produces *03_03_cluster_mechanistic_coefficients.csv* and *03_cluster_peak_months.csv* consumed by Script 11, and *03_master_data.csv* consumed by 11b for per-well β. The cluster-centroid *03_regional_averages.csv* is the data source for Section 5's spring MSL fits (the Method B baseline in S.18 §Method A and Method B aggregation).
-   **S.6** --- Script 09a's +0.144 m BACI scraping benefit at CEH36 is the basis for 11b's recovery-limit values (*SD15b_REC = SD15b + 0.14 m*, *SD16_REC = SD16 + 0.22 m*).
-   **S.8** --- Script 14's seasonal-extremes scatter is the per-well summer-min vs winter-max companion to 11b's static threshold maps.
-   **S.18** --- Script 26's observational MSL5 metric is the 5-year-mean target that Section 5's annual MSL forecast feeds into; managers add a Section 5 prediction to the rolling four-year history of observed MSLs to update the MSL5 statistic without waiting for end-May.
-   **S.18b** --- Full Tool A treatment: §S.18b.2 carries the per-cluster coefficient table, the manager workflow, and the rejected previous-MSL variant discussion. Tool B (Script 26b) consumes the same cluster β coefficients as the SSM-coefficient summary in Section 1 of this chapter to project ΔMSL5 under UKCP18 RCP8.5 scenarios.

### []{#anchor-297}[]{#anchor-298}[]{#anchor-299}S.9.3 Script 11c --- P_flood achievability map (post-review addition, Phase 3 step 13)

Script 11c was added on 2026-05-29 following the post-review pass on the main report. Conclusion 4 of the report names a priority criterion for scrape-target identification --- "*priority targets are the C1/C2/C3 transitional wells where the aquifer base is stable and P_flood thresholds remain achievable (rainfall multiplier λ \< 1.5)*" --- but the report does not surface a per-well lookup against this criterion. Script 11c operationalises the criterion by reading the per-well P_flood multipliers already produced by Script 11b (*11b_03_pflood_per_well.csv*) and emitting a per-well categorical map on the canonical site DEM + KML overlay. The script consumes existing Script 11b output and adds no new model fitting; it is a presentation-layer step.

**Procedure.** Each of the 88 wells in the classified network is binned on its λ value into three bands:

-   **Achievable** (λ \< 1.5) --- reachable in normal-to-mildly-wet winters.
-   **Marginal** (1.5 ≤ λ \< 2.5) --- reachable only in wet winters.
-   **Unreachable** (λ ≥ 2.5) --- effectively unreachable under current climate.

The bin edges follow Conclusion 4's explicit λ \< 1.5 boundary for the achievable band; the marginal-vs-unreachable boundary at λ = 2.5 is selected to match the abstract's reference to a 1.5--2.5× rainfall multiplier band as the conservatively wet-winter zone. Wells are rendered as colour-coded markers (green / amber / red) on the canonical DEM hillshade with KML feature overlays (forest boundary, broadleaf restocking block, clearfell footprint, site features), using the same *load_dem_hillshade()* and *add_kml_features()* helpers as Script 11b. Reference and Extended wells are marker-shape-distinguished (circle / diamond).

**Headline result (2026-05-29).** The categorisation produces a clean operational separation between the open-dune and forest zones. Of the 65 wells in C1 + C2 + C3 (the open-dune clusters), 57 are achievable, 8 are marginal, and none are unreachable. Of the 23 wells in C4 + C5 (the forest clusters), only 3 are achievable, 16 are marginal, and 4 are unreachable. The four unreachable wells are concentrated in C5 Coastal Forest (three wells) and C4 Main Forest (one well). The cluster pattern reflects the underlying mechanism: open-dune clusters carry higher β₁ recharge sensitivity (2.48--4.58) and lower summer-minimum baselines; forest clusters carry canopy interception losses and lower β₁ (1.32--2.55), and C5 additionally carries the Section 4.8 coastal-retreat gradient pushing its summer-minimum baseline progressively further below the Curreli thresholds.

Inputs.

-   *outputs/11b_spatial_thresholds/11b_03_pflood_per_well.csv* (Script 11b output).
-   DEM hillshade and KML features from *data/*, via *map_utils.load_dem_hillshade()* and *map_utils.add_kml_features()*.

**Outputs.** Sharing *paths.DIR_11B* with Script 11b --- outputs sit alongside 11b's per-well CSV with *11c\_* prefix:

-   *11c_pflood_achievability.png* --- the operational categorical map for §5.9 and Conclusion 4 of the main report.
-   *11c_pflood_achievability_per_well.csv* --- per-well lookup table with the *category* column (Achievable / Marginal / Unreachable).
-   *11c_pflood_achievability_results.md* --- memo with summary tables (counts per cluster × category), report drop-in text, and caveats.

**Path constants (new).** *paths.OUT_11C_ACHIEVABILITY_MAP*, *paths.OUT_11C_PER_WELL*, *paths.OUT_11C_RESULTS_MEMO*.

**Limitations.** The λ values come from Script 11b's per-well calculation; they inherit Script 11b's assumptions about cluster β coefficients and the climatological winter rainfall baseline. The categorical bin edges (1.5 and 2.5) are operational choices, not derived from natural breaks in the data; Conclusion 4's text explicitly identifies the λ \< 1.5 boundary, and the marginal-vs-unreachable boundary at λ = 2.5 is selected to match the abstract's wet-winter framing. The achievability category describes only whether the cluster summer minimum can be raised above the Curreli threshold by winter recharge alone --- scrape-as-drainage geometry effects (S.6) and forest-management interventions (S.14) are separate degrees of freedom in the scenario framework. Wells flagged as scraped in the existing per-well CSV (CEH36, CEH18, CEH21) retain their categorical assignment based on present-day λ; the category reflects post-intervention behaviour where applicable.

Cross-references.

-   §5.9 of the main report --- the figure *11c_pflood_achievability.png* and the per-well lookup table land here as the operational figure for Conclusion 4.
-   §7 Conclusion 4 of the main report --- the cross-reference is added to point the reader at the new figure and CSV.

## []{#anchor-299}[]{#anchor-300}[]{#anchor-301}S.10 Script 15 --- Depth-dependent PET sensitivity

**Step 17 / 27. Phase 5 in ***run_analysis.py***; second chapter under Phase 4 --- Climate and Spatial Context in the supplement.**

### []{#anchor-301}[]{#anchor-302}[]{#anchor-303}Motivation

The canonical SSM (F.3, Script 03) fits a single β₂ per cluster: PET draws the water table down at a rate proportional to monthly PET, with no dependence on how deep the water table currently sits. This is a strong assumption. Physically, evapotranspiration reaches the saturated zone through capillary rise from the root zone, and capillary connectivity weakens as the column between root zone and water table lengthens. A deep water table should be drawn down by PET less efficiently than a shallow one.

Script 15 tests this by replacing the fixed β₂ with a depth-decaying term, *β₂·exp(−λ·d)*, where *d* is the depth below ground surface and λ is a free parameter (m⁻¹) fitted per cluster. The script is a sensitivity analysis, not a replacement model: the canonical fixed-β₂ SSM remains the published headline. What Script 15 establishes is the *bound* on how much PET draw the fixed-β₂ formulation may be over- or under-estimating across the network --- a physically interpretable bracket on the headline model. The §5.3 discussion of Thornthwaite-PET limitations in the main report draws on this work; Scripts 19 and 21 consume β₂ in their spatial and forestry-scenario calculations and inherit the same caveat.

### []{#anchor-303}[]{#anchor-304}[]{#anchor-305}Inputs

  ------------------------ ---------------------------------------------------------------------
  Input file               Description
  01_wells_clean.csv       Script 01 --- cleaned, ground-referenced monthly dipwell series
  00_climate.csv           Script 00 --- monthly P and Thornthwaite PET (RAF Valley, 53.25 °N)
  02_cluster_stats.csv     Script 02 --- k=5 cluster membership
  01_locations.csv         Script 01 --- well coordinates
  01_well_elevations.csv   Script 01 --- per-well upstand heights
  ------------------------ ---------------------------------------------------------------------

### []{#anchor-305}[]{#anchor-306}[]{#anchor-307}Methodology

**Modified SSM.** The depth-coupled equation is

> Δh(t) = β₁·P(t) − β₂·exp(−λ·d(t−1))·PET(t) − β₃·(z₀ + h(t−1))

The β₁ rainfall and β₃ drainage terms are unchanged from the canonical SSM (F.3). The β₂ atmospheric-draw term is modified by an exponential decay factor in *d(t−1)*, the depth below ground at the start of the month. The functional form has two important properties: at λ = 0 the model reduces exactly to the canonical SSM (*exp(0) = 1*), and as λ grows the PET draw is progressively attenuated when the water table is deep. The decay factor is a multiplier on β₂, not a replacement: a cluster's PET sensitivity at the surface is still β₂, but the effective β₂ at depth *d* is β₂·exp(−λ·d).

**Two uses of depth, one term.** The script's docstring is emphatic that *d* (depth below ground, used in *exp(−λ·d)*) and the displacement *z₀ + h* (used in the β₃ predictor column) are not the same quantity. The displacement is referenced to the drainage datum 3.7 m below ground (F.3) and is the hydraulic head available to drive Darcy drainage; *d* is referenced to the ground surface and is the physical distance the capillary fringe must reach. The two coincide only in the trivial case where the datum equals the ground surface. Conflating them --- for example, by passing displacement into the exponential --- would change the physical meaning of λ from "decay length of capillary connectivity from the soil surface" to "decay length above the drainage datum", which has no obvious interpretation.

Cluster-centroid construction. Per-well fitting was rejected in favour of cluster centroids: the depth-decay signal is weak relative to the headline SSM at any single well, and aggregating to cluster level both stabilises the fit and matches the granularity of the downstream consumers (β₂ enters Scripts 19 and 21 at the cluster level). *build_cluster_centroids()* reads the k=5 membership from *02_cluster_stats.csv* and takes the mean across members for each monthly index; the series are already ground-referenced, so no correction is applied. The depth-coupling term uses *d = max(−h, 0)* directly, with no upstand term: adding one would measure *d* from the pipe top rather than the ground surface. The cluster-mean upstand is carried alongside the centroid because it is reported as *Mean_Upstand_m* in *15_04_best_params.csv*, not because it enters the model. Cluster-mean upstands are small (0.06--0.14 m) and dominated by per-well manufacturing variation rather than meaningful spatial signal.

**Grid search.** *grid_search_lambda()* scans λ over \[0, 6\] m⁻¹ in steps of 0.05 --- 121 grid points per cluster. At each λ, the term *−exp(−λ·d\_{t−1})·PET(t)* is a known column once d\_{t−1} is fixed, so β₁, β₂, β₃ are recovered by no-intercept OLS on a three-column design matrix (*beta_1_recharge*, *beta_2_atmospheric_draw*, *beta_3_drainage*). Physical-sign filtering follows: a grid point is accepted only if all three fitted β values are positive. Grid points with β₃ ≤ 0 are dropped --- these are statistical artefacts where the depth-coupling has shifted the OLS solution onto an unphysical drainage term. The accepted (β, λ) pair is then forward-simulated iteratively (*iterative_simulate()*, identical recurrence to Script 08 and *model_utils.simulate_ssm()* apart from the decay factor in the β₂ step), and the iterative Nash--Sutcliffe efficiency (NSE) is computed against the observed centroid. Best λ per cluster is the grid point that maximises iterative NSE.

**Why iterative NSE rather than OLS R².** One-step OLS R² is a diagnostic of how well the model fits each month's Δh conditional on the previous month's *observed* state. It is dominated by the climate-driven variance --- both the canonical and depth-coupled forms share the same P and PET inputs, so the one-step R² gap between them is small by construction (S.5 documents this for the canonical-vs-TLM comparison). Iterative NSE simulates the trajectory forward from a single initial condition, propagating the depth-coupling feedback at every step: a deeper simulated water table this month produces less PET draw next month, which feeds back into the depth term, and so on. This is the metric where the depth-coupling either earns its parameter or does not. The script inherits both the metric and the implementation idiom from Script 08 (S.5).

**Fit window.** The script uses the most-recent 100 months (*DATA_LIMIT = 100*), matching the LCSC window of Script 03 (S.3). This privileges recent data --- under steady-state climate the choice would be immaterial, but Newborough's water-table levels have trended downward over the record (S.3 documents the LCSC empirical estimate at 100 months in this context), so using the same window keeps Script 15's β₂ estimates comparable to the canonical β₂ from *03_master_data.csv*.

### []{#anchor-307}[]{#anchor-308}[]{#anchor-309}Site-specific choices and rationale

-   **λ grid range \[0, 6\] m⁻¹.** The lower bound is the canonical-SSM limit: λ = 0 returns the fixed-β₂ model exactly, so the null hypothesis (no depth coupling) is a special case in the search. The upper bound is generous: at λ = 6 m⁻¹ and a water-table depth of 1 m, *exp(−6) ≈ 0.0025*, so PET draw is effectively suppressed. No cluster's best λ approaches this bound, so the choice of upper limit does not bind any result.
-   **Grid step 0.05 m⁻¹.** This resolution is finer than the cross-cluster spread of best λ values (0.20--2.25), so quantising at 0.05 does not blur any cluster's position. A finer step would change reported λ values at the third significant figure at most.
-   **Cluster centroids rather than per-well fits.** Per-well fitting was considered but not implemented. The depth-coupling signal is small in absolute terms (Δ NSE = 0.033 to 0.184 across clusters), and per-well noise would swamp it at most wells. Aggregating to cluster level is consistent with how β₂ is consumed downstream --- Scripts 19 and 21 use one β₂ per cluster --- and matches the canonical Script 03 outputs that the chapter benchmarks against.
-   **Physical-sign filtering during the grid search.** The β₃ ≤ 0 filter is the principle of failing loudly: a coefficient that flips sign as λ varies is a statistical artefact, and feeding such a fit into the iterative simulator would produce numerically valid but physically uninterpretable trajectories. In practice the filter removes the C4 band λ ∈ \[0.25, 0.95\], where β₃ goes mildly negative --- C4's best λ at 0.20 sits at the boundary just below this band. C1, C2, C3, and C5 produce physically valid fits at every grid point.
-   **Iterative NSE as the headline metric.** Quoted from S.5: "the iterative NSE is where the SSM's structural advantage is unmasked". The same logic applies here: the depth-coupling parameter exists to change the multi-step behaviour of the model, so the multi-step metric is the appropriate test.
-   **Depth lag.** The decay term uses *d(t−1)*, the depth at the *start* of the month, not the contemporaneous *d(t)*. This is the same simultaneity argument that motivates *h_disp_prev* in the canonical β₃ term (F.3): using the result of the month's drainage as a predictor of that drainage biases the fit. The depth-coupling formulation inherits the same lag convention without further argument.

### []{#anchor-309}[]{#anchor-310}[]{#anchor-311}Outputs

  ------------------------------- ----------------------------------------------------------------------------------------------------------------
  Output                          Description
  15_00_lambda_profiles_raw.csv   Per-cluster λ-grid sweep with β₁, β₂, β₃, one-step R², iterative NSE at each grid point
  15_01_lambda_profile.png        One panel per cluster: iterative NSE vs λ, with dashed horizontal line at the canonical-SSM baseline
  15_02_fit_comparison.png        One panel per cluster: observed centroid vs canonical SSM vs best depth-coupled fit (time series)
  15_03_benchmark_table.csv       Per-cluster summary: SSM NSE, depth-coupled NSE, Δ NSE, best λ, fitted β values
  15_04_best_params.csv           Per-cluster best-fit parameters including cluster mean upstand, alongside canonical β baselines for comparison
  ------------------------------- ----------------------------------------------------------------------------------------------------------------

The principal downstream consumer is the §5.2.2 *Displacement Formulation and Depth-Dependent PET* section of the main report. Script 15 outputs are not consumed by any other pipeline script --- the depth-coupled model is sensitivity context, not a replacement that propagates forward.

### []{#anchor-311}[]{#anchor-312}[]{#anchor-313}Results to describe at the methodological level

The depth-coupled model improves iterative NSE over the canonical SSM at all five clusters. Differences are graded:

  --------------------- --------- ------------------- ------- -------------- ------------------
  Cluster               SSM NSE   Depth-coupled NSE   Δ NSE   Best λ (m⁻¹)   Mean upstand (m)
  C1 Lake Edge          0.69      0.88                +0.18   2.25           0.06
  C2 Dune               0.78      0.87                +0.09   0.95           0.07
  C3 Western Residual   0.83      0.87                +0.04   0.45           0.09
  C4 Main Forest        0.60      0.73                +0.13   0.20           0.14
  C5 Coastal Forest     0.81      0.84                +0.03   0.50           0.10
  --------------------- --------- ------------------- ------- -------------- ------------------

Three observations on the pattern. First, the cluster where depth coupling improves the fit most is C1 Lake Edge --- the cluster whose water table sits closest to the ground surface for the largest fraction of the record. A high λ at C1 (2.25 m⁻¹, the steepest decay in the network) means that the PET draw is heavily attenuated even at shallow depths: at *d* = 0.5 m, *exp(−2.25·0.5) ≈ 0.32*, so the effective β₂ is reduced by more than half. The canonical fixed-β₂ at C1 has to compromise across the seasonal swing between shallow winter levels and deeper summer levels, and the depth-coupling formulation resolves that compromise by letting β₂ vary with the season as the water table drops. Second, the forest clusters (C4, C5) and the western dune (C2, C3) take smaller λ values --- between 0.20 and 0.95. These clusters sit deeper on average, and a smaller λ reflects an effective β₂ that decays only modestly with depth across the working range. Third, C4 Main Forest's best λ at 0.20 m⁻¹ sits at a boundary in the OLS solution: λ ∈ \[0.25, 0.95\] produces a negative β₃ that the physical-sign filter rejects, so the C4 result picks up the largest contiguous band of physically valid fits at the low-λ end. The headline number is robust, but C4 is the cluster where the depth-coupled and canonical formulations are closest to being statistically indistinguishable on coefficient signs alone.

The cross-cluster λ pattern is consistent with the capillary-connectivity hypothesis: clusters where the water table is shallowest on average show steeper decay (because the working range of *d* is small, a larger λ is needed to produce a meaningful difference between summer and winter PET draw), while clusters where the water table is deepest show shallower decay (the canonical fixed-β₂ already roughly approximates the effective PET draw across the cluster's working depth range). The pattern is suggestive rather than definitive --- five points are not enough to fit a quantitative relationship between mean cluster depth and λ --- and the depth-coupling formulation is one of several physically motivated alternatives. It is the simplest one-parameter form consistent with monotonic decay of connectivity with depth.

### []{#anchor-313}Spring-mean branch and the season × gradient interaction test (v1.5.x)

Script 25 adds the spring mean (Mar--May) as a second per-well seasonal metric (compute_per_well_slopes(metric=...); spring uses a Mar--May calendar-year mean under the strict 3-of-3 rule, otherwise identical OLS and the same PANEL_OBS_MIN_YEARS = 8 guard). Crucially, the panel fit and the coastal-retreat gradient are all-season (metric-independent) and remain the headline; the spring branch reuses that same forest-free linear-capped fit and differs only in the per-well response and the Script-14 observed-centroid table it is decomposed against (14_spring_trend_stats.csv). This is the exact parallel of the committed summer decomposition, so any spring--summer difference is attributable to the metric alone rather than to a refitted gradient. The BACI corroboration (25_04) is metric-independent and is not re-emitted.

Two diagnostics accompany the spring branch. First, six MAM-only panel refits (the three specifications by two forms, restricted to Mar--May rows) are appended to 25_01_panel_fit_parameters.csv as a sensitivity: on a quarter of the panel, with the month fixed effects collapsed from 11 dummies to 2, the forest-free δ₀ standard error roughly doubles (1.97 to 3.47 mm yr⁻¹) and the reach SE loosens (48 to 78 m), while the point estimates move only a little (δ₀ −31.33 to −33.34 mm yr⁻¹; L 895 to 894 m). At the reference distance the two fits are closer still, returning −26.18 and −26.33 mm yr⁻¹ against standard errors of 1.45 and 2.56 --- a difference of 0.15 mm yr⁻¹, which is the cleanest available statement that the gradient is not a seasonal artefact. The loosening is expected sampling behaviour. The steepening of δ₀, about 6 %, is far too small against a doubled standard error to stand as a finding on its own, but it is of the same sign and roughly the same size as the interaction-test estimate below, which is not. Second, a full-panel season × δ(d)·t interaction test fits δ(d)·t·(1 + γ·S), with S = 1 in Mar--May, on the forest-free panel (10,929 observations, one model), estimating γ --- the fractional change in the gradient drift rate in spring --- with a Wald p-value (25_09_season_interaction_test.csv). This is the clean single-model test of whether the coastal-retreat gradient is itself seasonal, in place of comparing two subset fits with overlapping CIs. It rejects season-independence. The estimate is γ = +0.126 ± 0.054 (t = 2.32, p = 0.0203) for the linear-capped form and +0.115 ± 0.053 (t = 2.15, p = 0.0317) for the exponential: both significant at the 0.05 level, both positive, and the gradient drift rate accordingly about 12--13 % steeper in Mar--May than over the rest of the year. Because the two decay forms return compatible estimates, the seasonality is not an artefact of the assumed functional form. The coastal-retreat signal remains a year-round boundary effect --- γ modulates the drift rate, it does not switch it off outside spring --- but the all-season gradient is a season-averaged quantity rather than a season-independent one, and applying it unchanged to a spring metric understates the spring coastal contribution. The spring decompositions in Supplementary Note S8 are to be read on that basis. The new spring outputs are listed in the Outputs table below; full results, including the summer-vs-spring cluster comparison, are in Supplementary Note S8.

### []{#anchor-314}[]{#anchor-315}[]{#anchor-316}Limitations and known caveats

-   **Cluster-centroid fitting only.** Per-well heterogeneity within a cluster --- particularly the range of working depths within C2 Dune and C3 Western Residual --- is not addressed. A well at the dry end of C2 may behave more like C3, and the cluster-centroid λ averages over this heterogeneity. A per-well sweep would clarify the partition between within-cluster and between-cluster variation in λ but has not been implemented.
-   **Exponential decay is one of several plausible functional forms.** Power-law (*d\^{−p}*), sigmoid (*1/(1 + exp(k(d − d₀)))*), and piecewise-linear (constant above a threshold depth, decaying below) all have physical-mechanism arguments behind them. None has been tested against the exponential here. The exponential was chosen as the simplest one-parameter form consistent with monotonic decay; ranking alternative forms would require a model-comparison framework (AIC, cross-validation) that the script does not implement.
-   **The PET data is Thornthwaite-derived.** The sensitivity analysis is to the PET *signal* as Thornthwaite represents it (mean monthly temperature, day length, latitude 53.25 °N), not to a fundamentally improved PET formulation. Penman--Monteith PET would change the absolute magnitudes of both β₂ and the inferred λ. F.4 covers the Thornthwaite choice; §5.3 of the main report discusses the trade-off explicitly.
-   **The improvement in iterative NSE is graded, not transformative.** Three clusters (C2, C3, C5) gain Δ NSE between 0.03 and 0.07; two (C1, C4) gain more substantially (0.10--0.18). The canonical fixed-β₂ formulation is therefore an acceptable approximation for most of the network at most depths, and the depth-coupled model is a refinement rather than a fundamentally different description. This is the central reason Script 15 remains a sensitivity analysis: the gain does not justify retiring the simpler model.
-   **C4 sits at a coefficient-sign boundary.** The best-fit λ at 0.20 is the last physically valid grid point before β₃ flips negative for a band of intermediate λ values. This is a feature of the OLS geometry at that particular cluster centroid and may not survive perturbations (alternative climate input, longer fit window, different cluster membership). The C4 result is reported but should not be over-interpreted as a quantitative estimate of the cluster's depth-coupling parameter.

### []{#anchor-316}[]{#anchor-317}[]{#anchor-318}Where the result appears in the report

-   **§5.2.2 *****Displacement Formulation and Depth-Dependent PET*** --- the Thornthwaite limitations discussion cites Script 15's depth-coupled λ values as evidence that the fixed-β₂ formulation is defensible across the network. The graded improvements (largest at C1, smallest at C3 and C5) appear in the limitations paragraph.
-   **Not part of §4 headline results.** The canonical SSM (Script 03, fixed-β₂) remains the published model; Script 15 is sensitivity context for the §5 discussion.

### []{#anchor-318}[]{#anchor-319}[]{#anchor-320}Cross-references

-   **F.3** --- canonical SSM, displacement formulation, drainage datum, P(t) under *HEADLINE_LAG = 0*.
-   **F.4** --- cluster partition, *FOREST_CIDS = (4, 5)*, *DRAINAGE_DATUM = 3.7 m*.
-   **S.3** --- canonical cluster-level β values that Script 15 benchmarks against.
-   **S.5** --- Script 08's iterative NSE benchmarking idiom, which Script 15 inherits.
-   **S.13** --- Scripts 19 and 20 spatial groundwater calculations consume β₂ at cluster level; the depth-coupling is sensitivity context for those.
-   **S.14** --- Script 21 forestry scenarios consume β₂; the same caveat applies.

## []{#anchor-320}[]{#anchor-321}[]{#anchor-322}S.11 Script 16 --- Water balance decomposition

**Step 19 / 27. Phase 7 --- Water Balance Decomposition in ***run_analysis.py***; third chapter under Phase 4 --- Climate and Spatial Context in the supplement.**

### []{#anchor-322}[]{#anchor-323}[]{#anchor-324}Motivation

The state-space model fitted in S.3 gives each cluster three regression coefficients --- β₁, β₂, β₃ --- and a closure statistic (LCSC) that quantifies how much of the monthly Δh variance the displacement formulation explains. Those coefficients carry the physics, but a reader looking at the numbers in isolation has no straightforward way to ask the question conservation managers actually want answered: *where does the water at this cluster go?* Script 16 answers that question. It reads the cluster-mean β coefficients, computes long-term mean P and PET from the regional-average series, and rewrites the SSM equation at its steady state --- Δh̄ ≈ 0 --- to expose each component as a physical-units flux. Two outputs result: a head-space decomposition reported in m head per month, and a volumetric partition reported in mm per year. Both feed §4.2.3 *Water balance* of the main report and the two-panel Figure 11.

### []{#anchor-324}[]{#anchor-325}[]{#anchor-326}Inputs

  -------------------------------------------- -------------------------------------------------------------------------------------------------
  Input file                                   Description
  03_regional_averages.csv                     Script 03 (S.3); regional-mean cluster water-level series with merged P and PET monthly totals
  03_03_cluster_mechanistic_coefficients.csv   Script 03 (S.3); per-cluster β₁, β₂, β₃, LCSC, and the drainage datum that was used to fit them
  -------------------------------------------- -------------------------------------------------------------------------------------------------

### []{#anchor-326}[]{#anchor-327}[]{#anchor-328}Methodology

#### []{#anchor-328}[]{#anchor-329}The head-space decomposition

The SSM displacement form (see F.3) is

> Δh(t) = β₁·P(t) − β₂·PET(t) − β₃·(z₀ + h(t−1))

where *z₀ = DRAINAGE_DATUM = 3.7 m* and *h_disp(t−1) = z₀ + h(t−1)* is the displacement of the water table above the drainage base at the start of month *t*. Taken at long-term means, Δh̄ → 0: the water table is not drifting in either direction over the 21-year record. The closure condition becomes

> β₁·P̄ ≈ β₂·PET̄ + β₃·h̄\_disp

with the three terms in head-equivalent units (m head per month). Each term has a transparent physical reading. *β₁·P̄* is the **recharge** --- the head added per month by mean rainfall, filtered through whatever fraction of P actually reaches the water table at this cluster. *β₂·PET̄* is the **evapotranspirative draw** --- the head removed per month by mean PET demand. *β₃·h̄\_disp* is the **drainage flux** --- the head lost per month to lateral discharge, proportional to the cluster's mean displacement above the datum.

The function *compute_headspace()* does exactly this: it joins the per-cluster water-level series to P and PET on the date index, takes column means after *dropna()*, and computes *recharge = β₁·P̄*, *et_draw = β₂·PET̄*, *drainage = β₃·h̄\_disp* for each cluster. The residual *recharge − (et_draw + drainage)* is the closure check; in the current pipeline it sits between 0.03 % and 2.28 % of total losses, well inside the 2.5 % the script's docstring quotes as the design tolerance.

Each cluster receives the same forcing --- P̄ = 74.4 mm/month, PET̄ = 55.1 mm/month from the RAF Valley series --- but maps it into different head fluxes through its own β triplet. C1 Lake Edge converts that forcing into roughly 0.34 m/month of recharge, with drainage dominating losses (85 %, β₃ at the high end of the range and h̄\_disp deepest under the lake-buffered cluster). C4 Main Forest, at the other extreme, converts the same P̄ into only 0.19 m/month of recharge --- the β₁ ratio of 2.48 to C1's 4.58 reflects the canopy interception and the deeper unsaturated zone --- and the ET draw share rises to 76 % of losses.

#### []{#anchor-329}[]{#anchor-330}From head-space to volume

The head-space components are millimetres of head per month. To compare them with the climate baseline they have to be expressed as millimetres of water per year. The current Script 16 does this directly through the partition fractions, without an explicit specific-yield (Sy) conversion. The reasoning is simple: at the closure condition β₁·P̄ ≈ β₂·PET̄ + β₃·h̄\_disp, the head-space recharge is itself the head-equivalent of the net water flux into the cluster per month. Dividing the SSM losses into their two head-space components gives a partition fraction --- the ratio of β₂·PET̄ to total head-space loss is the ET share, and β₃·h̄\_disp / total is the drainage share --- and that partition fraction is a dimensionless ratio that transfers cleanly from the head-space to the volumetric description.

*save_volumetric_table()* implements the partition. Annual rainfall (P_annual = 892.5 mm/yr, the same for all clusters by construction) is reduced by interception at forest clusters (*I = 0.24 × P* per F.4 for C4 and C5; zero elsewhere), giving *P_net = P − I*. P_net is then split into ET and drainage according to the cluster's drainage fraction. The result is a per-cluster mm/yr breakdown that can be read alongside the 892.5 mm/yr rainfall input and the 661 mm/yr Thornthwaite PET ceiling.

#### []{#anchor-330}[]{#anchor-331}Recession as an independent check

The head-space partition is one way to split the SSM losses. It rests on the displacement formulation and inherits whatever uncertainty attaches to β₂ and β₃ separately. To bracket that uncertainty, *compute_recession_partition()* derives an independent partition from the observed seasonal behaviour of Δh itself.

The reasoning is that ET is strongly seasonal --- high in summer, low in winter --- while drainage is roughly proportional to head and varies more slowly. A winter month with low PET and a falling water table is approximately a drainage-only signal; a summer month with high PET and a falling water table carries drainage plus ET. Taking the average month-on-month decline (*Δh \< 0*) in winter (Nov--Feb) and in summer (Jun--Sep), the ratio winter / summer estimates the drainage share of summer losses. That ratio is *drain_frac* in *recession\[cid\]*, with *et_frac = 1 − drain_frac*.

Two independent constraints on the same partition then exist: the SSM head-space ratio and the recession ratio. The script does not enforce convergence --- it reports both and uses their midpoint as the central estimate, the range between them as a partition uncertainty band shown as the hatched area on the ET/drainage boundary of Figure 11b. Numerical agreement is cluster-specific: C3 Western Residual produces identical fractions under both methods (0.6/0.6, SSM/recession) and C5 Coastal Forest agrees closely (0.6/0.7), C1 Lake Edge moderately (0.8/0.6, a 20-percentage-point spread), and C2 Dune (0.7/0.4) and C4 Main Forest (0.2/0.5) the most discrepant, both at a 30-percentage-point spread. The figure shows that spread honestly rather than smoothing it; the bracket is the message.

#### []{#anchor-331}[]{#anchor-332}Interception and the energy budget

Forest interception (F.4: *FOREST_INTERCEPTION = 0.24*, *FOREST_CIDS = (4, 5)*, per Freeman (2008) for Newborough's Corsican pine canopy) appears on both bars of Figure 11b's volumetric panel. On the rainfall-input bar it sits above the net-rainfall section, reducing the rainfall that actually reaches the soil (P_net = 0.76·P at forest clusters). On the loss bar it sits above the ET and drainage losses, accounting for the canopy water that returns to the atmosphere without ever reaching the water table. The two appearances are identical and cancel in the net surplus --- by design.

The cancellation matters because interception is a partition of the rainfall energy budget at the canopy, not an additive loss on top of soil ET. The Penman-monteith demand at the canopy is taken by intercepted water first; the soil-surface ET draw measured by β₂ implicitly operates on the 0.76·P that actually reaches the soil. Showing interception as an additive loss term would double-count it, so the script subtracts it from both sides and lets the cancellation be visible. This is the project's standing convention (see F.4) and applies to C4 and C5 only.

### []{#anchor-332}[]{#anchor-333}[]{#anchor-334}Site-specific choices and rationale

-   **Long-term means rather than monthly time series.** The water balance is a steady-state description: it asks what the cluster receives and disposes of on average over the record, not how it responds month-by-month. Year-to-year variability is the SSM's domain (S.3); the residual seasonality not captured by the SSM is taken up in S.16 (Script 24). The 21-year mean window the script uses is whatever the upstream *03_regional_averages.csv* carries --- March 2005 to February 2026 for the wells with the fullest record, less for clusters whose member wells came online later. The mean is computed after *dropna()* so each cluster's window is its own complete-rows-only window.
-   **No reference cutoff filtering inside Script 16.** The script trusts whatever the upstream regional-average file contains. Script 03 applies *REFERENCE_CUTOFF_DATE = 2026-02-01* (F.4), so the means inherited here are consistent with the SSM fit window. The β coefficients in *03_03_cluster_mechanistic_coefficients.csv* and the P̄, PET̄, h̄ used in this script are from the same window --- a guarantee that the head-space balance closes against the same data the SSM was fitted on.
-   **Datum imported from the upstream coefficients file, not from ***config.py***.** Although *DRAINAGE_DATUM = 3.7 m* is the canonical value in *config.py*, *load_data()* reads the *drainage_datum_m* column from the coefficients CSV and uses that value, with a warning if it disagrees with *config.DRAINAGE_DATUM* by more than 1 cm. The point is to insulate the water-balance computation against any downstream change to the canonical datum: if a future sensitivity sweep re-fits the SSM at a different datum and writes a different value into the coefficients table, Script 16 will follow that value and produce a consistent decomposition, rather than silently mixing β values fitted at one datum with an h_disp computed at another.
-   **No Sy conversion in the canonical implementation.** The current script's volumetric translation goes directly from the dimensionless SSM partition fraction to mm/yr via the rainfall input. Earlier draft versions of this script produced Sy-weighted volumetric outputs; they were superseded by the partition-fraction approach because the head-space ratio is itself the Sy-invariant quantity. Specific yield enters elsewhere in the pipeline --- the WTF analysis in S.12 --- where its uncertainty is given its own treatment. Importing that uncertainty here would double-count it.
-   **Forest interception 0.24, hardcoded centrally rather than per-script.** *FOREST_INTERCEPTION* and *FOREST_CIDS* are imported from *config.py* (F.4). The 0.24 value is Freeman (2008) at this site for Corsican pine; it is not a global canopy interception fraction. The two forest clusters (C4 Main Forest, C5 Coastal Forest) share the same canopy type and the same value applies to both.
-   **Cluster-mean only, not per-well.** The water balance is at the cluster centroid. Per-well water balances are not produced because β₁, β₂, β₃ are noisier at the well level (S.3) and the residual closure tolerance the script enforces would not be met reliably for individual wells. The cluster-mean balance is the right scale for the methodological statement the report makes in §4.2.3.

### []{#anchor-334}[]{#anchor-335}[]{#anchor-336}Outputs

  ---------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------- --------------------------------
  Output                       Description                                                                                                                                         Report reference
  16_water_bal_table.csv       Table 4a: head-space decomposition per cluster --- β triplet, P̄, PET̄, h̄\_disp, recharge, ET draw, drainage, residual, drainage and ET percentages   Report §4.2.3, Table 4a
  16_water_bal_vol_table.csv   Table 4b: volumetric partition per cluster --- P, PET, I, P_net, both partition methods (SSM, recession), midpoint and bracketing range in mm/yr    Report §4.2.3, Table 4b
  16_water_bal_bar_ms.png      Water-balance manuscript version (300 dpi, white background, two-panel)                                                                             Report Figure 11
  16_water_bal_bar_lay.png     Figure 11 lay version (coloured background, 150 dpi)                                                                                                Report companion / web version
  ---------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------- --------------------------------

### []{#anchor-336}[]{#anchor-337}[]{#anchor-338}Limitations and known caveats

-   **The closure is steady-state.** Year-to-year variation, drought-recovery dynamics, and the response to single wet or dry years are deliberately absent from this analysis. They are the SSM's domain (S.3) and the residual-seasonality diagnostic's domain (S.16, Script 24). The water balance describes the average behaviour, not the operational range.
-   **Thornthwaite PET inherits its own caveat.** The PET̄ used in the head-space balance is the Thornthwaite estimate (F.4), known to underestimate atmospheric demand under forest canopies and at southern aspects on hot dry days. The depth-dependent PET correction in S.10 (Script 15) quantifies how much of the β₂ inter-cluster spread is attributable to substrate properties rather than canopy demand; the water balance presented here uses the canonical fixed-β₂ SSM and therefore inherits whatever direction the Thornthwaite bias pushes the cluster-mean ET share. The volumetric partition's central tendency is robust to the bias direction, but the *magnitude* of the ET draw at the forest clusters in particular is more uncertain than the numbers in Table 4b might suggest in isolation.
-   **The SSM/recession bracketing is the partition's honest uncertainty band, and at some clusters it is wide.** C1 Lake Edge differs by 20 percentage points between the two methods (SSM 80 % drainage, recession 60 %); C2 Dune by 30 (SSM 70 %, recession 40 %); C4 Main Forest by 30 (SSM 20 %, recession 50 %). The midpoint reported as the central estimate masks that spread. A reader looking at the volumetric breakdown should treat the hatched range on Figure 11b as the substantive uncertainty, not a decorative band.
-   **Specific yield uncertainty is not propagated here, but it does exist.** The choice to use the head-space partition fraction rather than a Sy-weighted volumetric conversion keeps this script's output Sy-invariant, but the upstream β coefficients themselves were fitted on water-level data --- Sy enters implicitly through the relationship between water-level change and recharge in the unsaturated zone. The decomposition presented here treats the fitted β values as fixed inputs; the full uncertainty around them is given proper accounting in the WTF chapters (S.12).

### []{#anchor-338}[]{#anchor-339}[]{#anchor-340}Where the result appears in the report

-   **§4.2.3 *****Water balance*** --- the section is built around the two tables and Figure 11 from this script.
-   **Table 4a** --- head-space decomposition (*16_water_bal_table.csv*).
-   **Table 4b** --- volumetric partition with SSM/recession bracket (*16_water_bal_vol_table.csv*).
-   **Figure 11** --- two-panel water balance figure (*16_water_bal_bar_ms.png*).

### []{#anchor-340}[]{#anchor-341}[]{#anchor-342}Cross-references

-   **F.3** --- SSM displacement formulation; the equation Script 16 rewrites at steady state.
-   **F.4** --- *DRAINAGE_DATUM*, *FOREST_INTERCEPTION*, *FOREST_CIDS*, the centralised constants this script imports.
-   **F.5** --- *model_utils.py*; not called directly here but underpins the β coefficients consumed.
-   **S.3** --- produces *03_03_cluster_mechanistic_coefficients.csv* and *03_regional_averages.csv*, the script's only inputs.
-   **S.10** --- Script 15 depth-dependent PET sensitivity; relevant context for the Thornthwaite caveat above.
-   **S.12** --- WTF specific-yield analysis; the chapter that does carry the Sy uncertainty propagation Script 16 deliberately defers.
-   **S.16** --- Scripts 22, 23, 24 residual diagnostics; Script 24 specifically addresses the residual seasonality the steady-state water balance does not capture.

## []{#anchor-342}[]{#anchor-343}[]{#anchor-344}S.12 Scripts 17, 18 --- WTF Specific Yield (cluster and spatial)

**Steps 18 and 20 / 27. Phase 6 (Script 17) and Phase 8 (Script 18) in ***run_analysis.py***; fourth chapter under Phase 4 --- Climate and Spatial Context in the supplement.**

The Water Table Fluctuation (WTF) method (Healy and Cook, 2002) translates an observed water-table rise into a recharge-equivalent volume, with specific yield (Sy) as the proportionality constant: Sy = R / Δh. The SSM in chapter S.3 characterises the *dynamic* response of the aquifer (the β coefficients), but its coefficients are in head units; converting any head-equivalent quantity into a volumetric flux requires Sy. The WTF Sy is the only network-scale, spatially distributed Sy available for Newborough Warren. Betson and Bristow (2002) report a field-measured hydraulic conductivity of K = 6 m day⁻¹ from a pumping test at the site --- the source used throughout the pipeline for K --- but do not report a Sy value from that test, and no slug or pumping test has been run at the dipwell locations themselves. A representative Sy cannot be read off the literature for a coastal dune system with this particular substrate gradient: published coastal-dune Sy values span 0.10--0.45 depending on grain size, saturation history, and depth (Baird et al., 2020; Berendsen et al., 2007), a range wide enough to carry material uncertainty into any volumetric calculation. The WTF method provides the only means of producing a well-by-well, cluster-stratified Sy calibrated to the site's own observed head fluctuations. Scripts 17 and 18 are paired because they use the same WTF event-detection logic on the same monthly time series, but answer different questions: Script 17 produces a single Sy per cluster (the value consumed by Table 4c and by Script 19's spatial calculations and Script 21's forestry scenarios), while Script 18 produces a Sy per well and combines it with the well-level β₃ from the SSM to generate the storage--drainage index map τ = Sy / β₃ that informs the main report's discussion of aquifer architecture.

### []{#anchor-344}[]{#anchor-345}[]{#anchor-346}Sub-script 17 --- *17_wtf_specific_yield.py* (cluster-level Sy)

#### []{#anchor-346}[]{#anchor-347}Motivation

The cluster-level Sy is the value most consumers downstream actually need: Script 21's forestry scenarios apply a multiplier to a cluster-mean head response and need to convert that to a volumetric flux at the cluster scale, not the individual-well scale. Per-well Sy values are noisier (Script 18 quantifies this) and not the right granularity for the cluster-mean SSM coefficients in *03_master_data.csv*. Script 17 produces a single Sy per cluster, with three independent methods (Approach A, Approach B, and Approach C), so the reader can see how sensitive the headline number is to the estimator choice. Approach C is a reported triangulation only; it does not propagate downstream.

#### []{#anchor-347}[]{#anchor-348}Methodology

Script 17 reads the regional cluster-mean hydrographs (*03_regional_averages.csv*) and the climate series (*01_climate.csv*), forms the monthly change in cluster-mean head Δh for each cluster, and applies three estimators.

**Approach A --- drainage-corrected winter OLS.** The observed Δh during a winter month reflects both recharge and continuing drainage:

> Δh = R / Sy − β₃ · \|h_prev\|

Rearranging to estimate Sy gives R = Sy · (Δh + β₃·\|h_prev\|), so the OLS regression of net recharge R against the *drainage-corrected* rise (Δh + β₃·\|h_prev\|) through the origin recovers **Sy as the slope itself** (R is the dependent variable, Δh + β₃·\|h_prev\| is the independent variable). Cluster-median β₃ values are loaded from *03_master_data.csv* to perform the correction. The regression is restricted to winter months (November--March) with PET below 25 mm/month so that net recharge (P − PET) is a defensible proxy for actual recharge. Standard errors on Sy are the OLS-through-origin slope SE directly (no delta method is required because Sy is the slope, not its reciprocal). The fit metric quoted is uncentred R² = 1 − SS_res / Σy², appropriate for through-origin regression where the centred form can be spuriously negative even when the line passes through the data well.

**Approach B --- event-median.** For every rising-limb month with Δh \> 5 mm and net recharge \> 10 mm, compute Sy_i = R_i / Δh_i directly. Reject physically implausible values (Sy \< 0.01 or Sy \> 0.50). Report the median, Q25, and Q75 across qualifying events. The event method is noisier than Approach A but distribution-free and provides empirical uncertainty bounds.

**Approach C --- rapid recharge events (Crosbie et al., 2005).** A third, methodologically independent estimator that selects episodes where the drainage correction is negligible *by construction*. For each cluster-mean head series, a candidate episode requires *WTF_C_DRY_BASELINE = 2* prior months of Δh ≤ 0 (drainage-only quasi-steady state), starts on the first month with Δh \> 0, runs while Δh \> 0 up to the *WTF_C_MAX_DURATION = 2*-month cap, and must accumulate a cumulative head rise ≥ *WTF_C_MIN_RISE_M = 50 mm*. Episodes are non-overlapping. Per episode, Sy_i = Σ net_R\[s..e\] / (h\[e\] − h\[s−1\]); forest clusters (C4, C5) receive the Freeman (2008) interception-corrected recharge, consistent with Approach B. Sy_i is filtered to \[0.01, 0.50\] (aligned to Script 18's per-well filter). The cluster estimate is the median with a *WTF_C_BOOTSTRAP_N = 1000*-resample 95 % CI (seed *WTF_RAPID_BOOT_SEED = 20260611* in *config.py*). The episode-selection criterion makes the drainage correction negligible by construction during the episode window --- which is why no β₃ term is required --- so Approaches A and C are mechanistically distinct: A corrects drainage algebraically, C avoids it by episode selection. A↔C convergence validates the β₃ correction; A/C divergence is diagnostic of where β₃ may over- or under-state drainage, not evidence that either approach is wrong. Approach C is a reported triangulation only and does not propagate downstream to Script 18, 19, 21 or any other script.

**Interception correction for forest clusters.** For Corsican pine (C4 Main Forest, C5 Coastal Forest), R is replaced with the effective recharge R_eff = (1 − 0.24)·P − PET (Freeman, 2008). The 0.24 fraction is the throughfall-gauge interception loss measured at the C5 forest at Newborough Warren. PET is not also reduced --- Thornthwaite PET is an energy-based atmospheric demand independent of land cover, and reducing it would double-count the canopy effect.

**Headline values.** Approach B is the pipeline-consumed canonical estimator: the per-well event-based values written to *17_wtf_well_sy.csv* are what Scripts 09d, 20, 29, 30, 31 and 37b read, and Approaches A and C are reported alongside as independent cross-checks that propagate to no downstream calculation. Two Approach B aggregations are in circulation and should not be conflated: the cluster-level event median in *17_wtf_01_sy_estimates.csv* (C3 = 0.3283), tabulated below and in Paper 1 Table 4; and the median of the per-well event estimates in *17_wtf_well_sy.csv* (C3 = 0.3057), which is the value the drawdown-reach figure and the other downstream consumers actually use. Approach A, Approach B, and Approach C produce the following cluster Sy estimates (Script 17 v1.4.0; verify against *17_wtf_01_sy_estimates.csv* before citing --- do not cache):

  ----------------------- ------------- ------- ------- ---- --------------- ------------------ ----------
  Cluster                 Sy (A, OLS)   SE      R²      n    Sy (B, event)   IQR                n events
  C1 (Lake Edge)          0.341         0.045   0.605   39   0.210           \[0.129, 0.259\]   59
  C2 (Dune)               0.335         0.034   0.666   50   0.281           \[0.197, 0.374\]   64
  C3 (Western Residual)   0.351         0.022   0.836   52   0.328           \[0.284, 0.410\]   57
  C4 (Main Forest)        0.302         0.018   0.864   46   0.259 (corr)    \[0.179, 0.330\]   62
  C5 (Coastal Forest)     0.419         0.024   0.871   48   0.321 (corr)    \[0.243, 0.383\]   49
  ----------------------- ------------- ------- ------- ---- --------------- ------------------ ----------

  --------------------- ---------------------- ------------------ ----
  Cluster               Sy (per-well median)   95% CI             n
  C1 Lake Edge          0.195                  \[0.098, 0.230\]   20
  C2 Dune               0.261                  \[0.197, 0.336\]   21
  C3 Western Residual   0.334                  \[0.288, 0.437\]   17
  C4 Main Forest        0.274 (corr)           \[0.229, 0.312\]   13
  C5 Coastal Forest     0.298 (corr)           \[0.269, 0.355\]   14
  --------------------- ---------------------- ------------------ ----

Three cross-approach observations: C3 converges tightly across all three methods (≈ 0.33--0.34), which solidifies the Fig-17 λ anchor at that cluster. C1 has B and C both well below A (0.210 and 0.195 vs 0.334), consistent with β₃ over-correcting in the lake-buffered cluster --- a diagnostic reading, not grounds for rejecting A. The coarse Sy gradient across the five clusters is robust to estimator choice; the fine top-end ranking (C3 vs C5) remains method-dependent: A puts C5 highest, B and C put C3 highest. The pipeline-consumed canonical for forest clusters is the corrected Approach B value (Script 18 → *17_wtf_well_sy.csv*); Table 4c of the main report uses Approach B with interception correction.

#### []{#anchor-348}[]{#anchor-349}Site-specific choices

-   **Winter restriction for Approach A.** Approach A is the more defensible of the two estimators because winter PET is small enough that any error in the PET estimate is negligible compared to P. The PET_MAX_WINTER = 25 mm/month threshold excludes warm winter months where PET is no longer negligible.
-   **Drainage correction in Approach A.** Without the β₃ correction, the regressor (raw Δh) is biased low because the rise is being shaved by continuing drainage; the slope is biased high, and Sy biased low. The correction is essential, not cosmetic --- see *Limitations* for what happens when β₃ is itself badly identified.
-   **Plausibility filter in Approach B.** Sy values below 0.01 or above 0.50 are dropped as physically implausible for the substrate. The filter interacts with the interception correction: reducing P brings previously-excluded high-Sy events (which had unrealistically large Sy_i because Δh was small relative to raw P) back into the admissible range. This is why the corrected event pool can be larger than the uncorrected pool.
-   **No bootstrap for Approach B.** The uncertainty is reported via the IQR rather than a parametric SE, because the per-event Sy distribution is heavy-tailed and a Gaussian SE understates it.
-   **Episode selection for Approach C.** The 2-month dry baseline and the 2-month cap make the drainage contribution during the rise negligible by construction --- no β₃ term is required. The \[0.01, 0.50\] plausibility filter is the same as Approach B and Script 18's per-well filter, so the three approaches share a consistent exclusion boundary. The "dry baseline then rise" criterion favours spring episodes; the non-overlapping constraint prevents a long multi-month wet stretch from being counted multiple times. Approach C values are reported as triangulation only; the pipeline-consumed Sy is Approach B per-well (Script 18).

#### []{#anchor-349}[]{#anchor-350}Outputs

  ----------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------------------------------------
  Output                        Description                                                                                                                                                                               Reference
  17_wtf_01_sy_estimates.csv    Per-cluster Approach A and B estimates with SE/IQR and n; corrected variants for forest clusters; six *Sy_rapid\_\** columns for Approach C (median, 95 % CI bounds, n, bootstrap seed)   Script 19, Script 21, Table 4c
  17_wtf_02_regression.png      OLS regression plots for Approach A, one panel per cluster                                                                                                                                Supplementary figure
  17_wtf_03_event_boxplot.png   Sy distribution boxplot for Approach B, including the corrected forest variants                                                                                                           Supplementary figure
  17_wtf_05_rapid_events.png    Approach C rapid-event Sy per cluster: median, 95 % CI, per-episode points; interception-corrected for C4/C5                                                                              Supplementary figure (not placed as a numbered report figure)
  17_wtf_04_summary.txt         Plain-text summary for report cross-reference                                                                                                                                             Author reference
  ----------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------------------------------------

### []{#anchor-350}[]{#anchor-351}[]{#anchor-352}Sub-script 18 --- *18_wtf_spatial.py* (per-well Sy and the drainage half-life map)

#### []{#anchor-352}[]{#anchor-353}Motivation

Script 18 brings the WTF estimator down to the individual well, then interpolates the result spatially. Three downstream uses motivate the per-well treatment. First, the supplementary table S1 in the main report needs a per-well Sy so readers can cross-check the cluster-level headline against the spatial pattern. Second, the spatial contour map shows where the Sy assumption is most exposed (low-Sy pockets that the cluster-level mean smooths over). Third, combining per-well Sy with per-well β₃ from *03_master_data.csv* gives the storage--drainage index τ = Sy / β₃ (months), a per-well aquifer-architecture diagnostic that is not available from the SSM alone. τ is a deliberately storage-weighted composite --- it fuses two independently estimated quantities (Sy from the WTF method, β₃ from the SSM) and therefore carries information beyond β₃ alone. It is **not** a residence time or drainage timescale in the hydraulic sense: the head-space recession e-folding time is t_R = 1/β₃ (months), which is the genuinely time-like quantity (the interval over which a recharge perturbation decays). The figure that informs the main report's discussion of aquifer architecture is the drainage half-life map (*18_wtf_05_halflife_map.png*, t½ = ln(2)/β₃). Because Sy \< 1, τ = Sy/β₃ is always shorter than 1/β₃ --- for example, C2 has 1/β₃ ≈ 14 months but τ ≈ 4 months. The two should not be conflated; t_R = 1/β₃ is reported as an interpretation layer on the β₃ atlas (see *Site-specific choices* below).

**What e-folding time means in practice.** If a recharge event raises the water table by 200 mm above its equilibrium position, and nothing further happens, the linear-reservoir model predicts that t_R months later the head has decayed to 200/e ≈ 74 mm above equilibrium --- it has lost 63 % of the perturbation. After 2·t_R it has lost 86 %, after 3·t_R it has lost 95 %. For C2 Dune (β₃ ≈ 0.07 month⁻¹, t_R ≈ 14 months) a 200 mm winter recharge event has largely dissipated by the following spring. For C4 Main Forest (β₃ ≈ 0.02 month⁻¹, t_R ≈ 49 months) the same event still carries ≈ 148 mm of residual head into the following year and ≈ 110 mm two years later --- the forest interior integrates recharge over multi-year windows, which is why the MSL5 metric (Script 26) captures its water-availability state better than a single-year summer minimum. The contrast is also why C4 appears less responsive to the clearfell signal in any single post-fell year: the long memory means the pre-fell history is still present in the water table alongside the post-fell recharge gain.

**What τ = Sy/β₃ adds beyond t_R.** The e-folding time t_R = 1/β₃ is a purely dynamic property of the drainage rate. The storage--drainage index τ = Sy/β₃ brings in the storage capacity: a cluster with a high drainage rate and a large pore volume (high Sy) will drain slowly in volume terms even if it drains quickly in head terms, because each metre of head drawdown releases Sy × 1 m of water. τ captures this --- it is, roughly, the time to drain a head column of Sy metres through a drain of rate β₃ --- and is therefore sensitive to the combined effect of both quantities. In practice the β₃ contrast dominates across the Newborough clusters (C4 β₃ ≈ 0.020 month⁻¹ vs C2 β₃ ≈ 0.070 month⁻¹), so τ and t_R carry largely the same spatial ordering; τ's additional information over t_R emerges most clearly at pairs of clusters where Sy differs markedly but β₃ is similar. The aquifer-diagnostic synthesis figure (Script 18, Figure 51) exploits the full τ-vs-ΔNSE space to give a single read of aquifer architecture that neither β₃ alone nor Sy alone provides.

#### []{#anchor-353}[]{#anchor-354}Methodology

Script 18 reads the cleaned reference-network hydrographs (*01_wells_clean.csv*), climate (*01_climate.csv*), well locations (*01_locations.csv*), and cluster assignments (*02_cluster_stats.csv*). For each reference well it applies the same event-based WTF procedure as Script 17's Approach B: Δh \> 5 mm, net recharge \> 10 mm, plausibility filter 0.01 \< Sy_i \< 0.50, median across qualifying events. Forest-cluster wells (C4 and C5, identified through *FOREST_CIDS* in *config.py*) receive the Freeman (2008) interception correction. A well needs at least five qualifying events to be included; wells with fewer than 15 are flagged as low-confidence in the output table.

**Extended-network handling.** The reference network of 66 wells is supplemented by 22 additional dipwells whose records are shorter or whose cluster identity is less certain. Cluster assignments for the extended wells come from *06_pear_membership_audit_sitewide.csv* (chapter S.4), specifically the *Best_Match_Cluster* column. Extended wells are analysed in *wtf_extended_wells()* with the same event rules and forest-correction logic, and rendered as open symbols on the extended contour map (*18_wtf_04*) so the reader can see at a glance which contour areas rely on lower-confidence wells.

**Spatial interpolation.** The per-well Sy values are interpolated onto the 50 m grid used elsewhere in the spatial pipeline via a local true inverse-distance-weighting routine (power = 2; the function is defined inline as *idw()* within the plotting functions). Note this is genuine IDW, not the piecewise-linear barycentric interpolation that *map_utils.add_idw_surface* provides elsewhere --- the local routine here does what its name implies. The site-boundary mask (*make_site_mask*) excludes the sea, lake, and forestry-bounded interior, matching the convention used in Scripts 07 and 19.

**Storage--drainage index τ = Sy / β₃.** The function *compute_storage_drainage_index()* joins the per-well Sy table with *03_master_data.csv* on a normalized well name and computes τ for each well where β₃ \> 0. Wells with negative β₃ (CEH14) or near-zero β₃ that would produce a \> 10× outlier (CEH13) are flagged as excluded; the ridge / slack-floor wells (CEH12 sand--bedrock contact, CEH15 forest slack floor) are also excluded as not representative of the dune-aquifer Sy that the WTF estimates. The remaining wells produce τ values reported in *18_wtf_05_storage_drainage_index.csv*.

**Head-space recession time t_R = 1/β₃ (interpretation layer).** The β₃ atlas produced in chapter S.5 (Script 07) is already a drainage-rate map; t_R = 1/β₃ is a deterministic monotone transform of β₃ that re-expresses each well's drainage rate as an e-folding timescale in months --- the interval over which a recharge perturbation decays to 1/e of its initial magnitude in the absence of further forcing. Because 1/β₃ is a one-to-one rescaling, the spatial pattern of t_R is identical to that of β₃ and no new figure is required; Script 18 does not compute t_R as a separate column. The interpretation anchor is: β₃ ≈ 0.10 month⁻¹ → t_R ≈ 10 months; β₃ ≈ 0.07 → t_R ≈ 14 months; β₃ ≈ 0.05 → t_R ≈ 20 months; β₃ ≈ 0.02 → t_R ≈ 50 months. Cluster-mean values from the canonical fits: C1 Lake Edge ≈ 11 months, C2 Dune ≈ 16 months, C3 Western Residual ≈ 18 months, C4 Main Forest ≈ 55 months (≈ 4.6 years), C5 Coastal Forest ≈ 23 months. CEH14 has negative β₃ and has no valid t_R; CEH13's β₃ ≈ 0.002 gives t_R ≈ 526 months and is treated as off-scale in any tabulation. t_R adds no spatial information beyond the β₃ atlas; its value is the interpretable "years of drainage memory" framing that the raw coefficient does not immediately communicate. The genuinely independent fusion of storage and drainage information remains τ = Sy/β₃ (Workstream A).

**Aquifer-diagnostic synthesis figure.** *plot_aquifer_diagnostic_synthesis()* combines three independently derived per-well metrics into a single scatter: t½ = ln(2)/β₃ (the drainage half-life in months, from β₃ here), the iterative LCSC NSE improvement ΔNSE (from chapter S.5's model-benchmarking output *08_lcsc_model_stats.csv*), and Sy itself as the marker size. Points are coloured by cluster; cluster means are anchored by larger star markers. The synthesis is the figure that turns three diagnostics into a single read of aquifer architecture. The genuinely independent fusion of storage and drainage information remains τ = Sy/β₃ (computed separately and reported in *18_wtf_05_storage_drainage_index.csv*); the figure plots t½ rather than τ because the x-axis is a pure drainage-rate quantity, independent of Sy.

#### []{#anchor-354}[]{#anchor-355}Site-specific choices

-   **The storage--drainage index τ is the per-well diagnostic, not the cluster mean.** Cluster-mean τ averages over substantial within-cluster spread (the C2 Dune τ range is 2.0--8.7 months across 24 wells, mean ≈ 4.0 months). The values are reported in *18_wtf_05_storage_drainage_index.csv*. Note that τ = Sy/β₃ is not a residence time --- see the t_R = 1/β₃ passage above for the head-space recession time and its cluster-mean anchor values. The figure that informs the report's architecture discussion plots t½ (half-life), not τ.
-   **Ridge-zone exclusions for τ.** CEH12 sits on the sand--bedrock contact where Sy is not representative of the dune aquifer; CEH15 sits on a forest slack floor where the Sy estimate is atypical of the surrounding cluster. CEH13's β₃ is near zero (0.0019, which would give τ ≈ 124 months --- physically defensible as "very slow" but dominates the index range). CEH14's β₃ is negative, making τ undefined. All four are documented in the exclusion column of *18_wtf_05_storage_drainage_index.csv*. The same exclusions apply to t_R = 1/β₃: CEH14 has no valid t_R; CEH13 is off-scale (t_R ≈ 526 months).
-   **Per-well Sy is treated as a diagnostic, not a parameter.** Downstream calculations (Script 19's spatial groundwater work, Script 21's forestry scenarios) all use the *cluster-level* Sy from Script 17, not the per-well values. The per-well map is for spatial pattern recognition, not for substitution into other calculations.

#### []{#anchor-355}[]{#anchor-356}Outputs

  -------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- ----------------------------
  Output                                       Description                                                                                                                                                            Reference
  18_wtf_01_well_sy_estimates.csv              Per-well WTF Sy with Q25/Q75, n_events, confidence flag                                                                                                                Table S1, supplementary
  18_wtf_02_spatial_sy_map.png                 Per-well Sy point map (paper figure)                                                                                                                                   Main report
  18_wtf_03_sy_contour.png                     Sy contour surface, reference wells only                                                                                                                               Supplementary figure
  18_wtf_04_sy_contour_extended.png            Sy contour surface, reference + extended                                                                                                                               Supplementary figure
  18_wtf_05_storage_drainage_index.csv         Per-well τ = Sy/β₃ values with Sy, β₃, cluster, exclusion flags; τ is the storage--drainage index (not a residence time --- see t_R = 1/β₃ in Site-specific choices)   Supplementary
  18_wtf_06_aquifer_diagnostic_synthesis.png   t½ vs ΔNSE scatter (t½ = ln(2)/β₃, months), sized by Sy, by cluster                                                                                                    Main report, §5 discussion
  17_wtf_well_sy.csv                           Intermediate copy at *outputs/* root                                                                                                                                   Internal pipeline
  -------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- ----------------------------

### []{#anchor-356}[]{#anchor-357}[]{#anchor-358}Site-specific choices and rationale (suite-level)

-   **WTF as a complement to the SSM, not a replacement.** The SSM gives the dynamic response (β₁, β₂, β₃); the WTF gives the conversion factor that turns a head response into a volumetric flux. Both are fitted to the same monthly time series but answer different questions, and reporting both lets the reader cross-check (for example) the cluster ordering by Sy against the cluster ordering by β₂ --- C4 Main Forest is among the lower-Sy clusters, which is part of the explanation for why C4's β₂ is high in head units while the volumetric water-balance partition does not place forest evapotranspiration in an extreme position (chapter S.11).
-   **Forest interception correction is shared between Scripts 17 and 18.** The 0.24 interception fraction (Freeman 2008) is hard-coded in Script 17 and imported from *config.py* (*FOREST_INTERCEPTION*) in Script 18 --- the two scripts produce consistent treatment of the forest clusters because they both apply the same correction to the recharge term. *FOREST_CIDS = (4, 5)* in *config.py* (see F.4) defines which clusters receive the correction.
-   **Live network counts.** Script 17 works at the cluster level on the five reference clusters under the k=5 partition (C1 Lake Edge, C2 Dune, C3 Western Residual, C4 Main Forest, C5 Coastal Forest), each represented by a cluster-mean hydrograph in *03_regional_averages.csv*. Script 18 works at the well level on the 66 wells of the reference network plus the 22-well extended network. The 66/22 split is established in chapter S.4.
-   **Event detection rules are identical in Scripts 17 and 18.** Minimum rise 5 mm, minimum net recharge 10 mm, Sy plausibility filter 0.01--0.50, minimum 5 events per well for inclusion. These rules are conservative --- the live event count per well averages around 50 --- and the script favours throwing out marginal events over including them.

### []{#anchor-358}[]{#anchor-359}[]{#anchor-360}Limitations and known caveats

-   **Sy estimates from the WTF method are indicative, not definitive.** Slug or pumping tests at representative wells per cluster would be the gold standard. The WTF approach assumes that monthly net recharge during rising-limb winter months equals actual aquifer recharge --- a defensible approximation for this site but not a measurement.
-   **Approach A and Approach B answer slightly different questions and are expected to differ within the data's natural spread.** Approach A's drainage correction means it is reporting Sy *given* the SSM's β₃, while Approach B is an empirical median across rising-limb months. Under the live partition the two estimators agree within \~10--15 % on C3, C4, and C5; they diverge on C1 (Lake Edge) and C2 (Dune). The chapter on Script 16's water balance (S.11) takes the view that any volumetric calculation built on a single Sy value is exposing itself to this spread, which is why Script 16 was designed to be Sy-free.
-   **C1 Lake Edge carries materially more uncertainty than the cluster-level summary suggests.** At C1 the three estimators diverge: Approach A Sy = 0.334, Approach B Sy = 0.210, Approach C Sy = 0.195. B and C converge at the lower end and independently corroborate each other, strengthening the reading that β₃ over-corrects at the lake-buffered cluster --- the Pearson correlation between R and the drainage-corrected rise at C1 is effectively zero (r ≈ 0.00 across the qualifying winter months), against r = 0.72 at C3, 0.70 at C4, and 0.76 at C5. This is a diagnostic reading, not grounds for rejecting Approach A: it means the β₃ correction is poorly identified at C1, as expected for a sluice-managed water body. At this cluster the per-event median (Approach B) is treated as the more reliable estimator, and the cluster's headline Sy in Table 4c reflects that choice.
-   **Forest-cluster Sy carries additional uncertainty from the interception value.** The 0.24 throughfall-loss fraction is a single Freeman (2008) value, measured under one canopy density in one stand. Its own uncertainty band is not propagated through the WTF estimate. Section S.13 (Scripts 19, 20) and S.14 (Script 21) both consume the corrected forest Sy values without re-propagating that uncertainty; the size of the cluster's Sy range itself remains the dominant uncertainty term.
-   **Per-well Sy in Script 18 is noisy at short-record wells.** Extended-network wells with few rise events produce wide confidence intervals; the spatial contour map smooths over this but the per-well CSV (Table S1) should be read with care. The 15-event threshold for the high-confidence flag is conservative but does not eliminate the issue.
-   **The contour interpolation extends 100 m beyond the convex hull of well locations** (*map_utils.add_idw_surface()*, *hull_buffer_m = 100*, applied from map_utils v1.5.0). The extension is bounded by nearest-neighbour fill within the buffered hull and then clipped to the site boundary and ridge mask, so the surface reaches the coastal margin rather than stopping at the outer well ring. Values in the 100 m extension zone are bounded extrapolation over unmeasured ground and should be read with corresponding caution. The dune fringes inside the hull are interpolated rather than measured; offshore and lake areas are hidden by the site-boundary mask.
-   **Downstream consumer note --- broadleaf β₂ multiplier in Script 19.** The Sy values produced here feed Script 19's spatial calculations and Script 21's forestry scenarios. Script 19 imports the broadleaf β₂ seasonal split --- *sB2_w = 0.8817* (Nov--Apr, leaves off), *sB2_s = 1.0750* (May--Oct, full leaf) --- from *utils.config* (canonical values derived from Script 21's monthly profile, see chapter S.14). §4.10.2 of the main report carries the broadleaf-scenario values.

### []{#anchor-360}[]{#anchor-361}[]{#anchor-362}Where the result appears in the report

-   **§4.2.4 (or the equivalent --- verify against the report's section numbering)** --- WTF Sy methodology and the cluster-level result.
-   **Table 4c** --- cluster-level Sy estimates from Script 17's interception-corrected output.
-   **Table 4b / Figure 11b** --- volumetric water-balance using the WTF Sy.
-   **Table S1** --- per-well Sy from Script 18, supplementary.
-   **Spatial figures** --- Script 18's contour and τ maps; the t½ vs ΔNSE synthesis figure appears in the discussion of aquifer architecture.

### []{#anchor-362}[]{#anchor-363}[]{#anchor-364}Cross-references

-   **F.3** --- SSM displacement formulation; the β coefficients consumed alongside Sy in volumetric calculations.
-   **F.4** --- *FOREST_INTERCEPTION = 0.24*, *FOREST_CIDS = (4, 5)*.
-   **F.5** --- shared utility modules and the IDW interpolation convention used by *map_utils.add_idw_surface* (which is *not* used here; the IDW in Script 18 is implemented locally).
-   **S.3** --- produces the β coefficients used for the τ = Sy / β₃ storage--drainage index calculation and for the t_R = 1/β₃ recession-time interpretation.
-   **S.4** --- the Pearson audit that provides *Best_Match_Cluster* for extended wells used by Script 18.
-   **S.5** --- model benchmarking; supplies the ΔNSE used in the t½ vs ΔNSE synthesis figure.
-   **S.11** --- Script 16's water balance deliberately defers Sy uncertainty by choosing a Sy-free partition-fraction approach. The reciprocal of the relationship: Script 16 doesn't consume Sy because Scripts 17 and 18 carry the uncertainty.
-   **S.13** --- Scripts 19 and 20 spatial groundwater calculations consume the cluster-level Sy values.
-   **S.14** --- Script 21 forestry scenarios consume the cluster-level Sy values via *clearfell_common.load_clearfell_b2_multiplier()* and elsewhere.

## []{#anchor-364}[]{#anchor-365}[]{#anchor-366}S.13 Scripts 19, 20 --- Spatial groundwater analysis

**Steps 21 and 22 / 27. Phase 9 --- Spatial Groundwater Analysis in ***run_analysis.py***; fifth chapter under Phase 4 --- Climate and Spatial Context in the supplement.**

Scripts 19 and 20 together construct §4.9 *Spatial groundwater* of the main report. They share inputs (the per-well β coefficients from *03_master_data.csv*, monthly maOD heads from *01_wells_clean_maod.csv*, the 50 m project grid, the F.3 displacement formulation, the cluster-mean Sy from S.12) and methodological choices (Freeman 2008 forest interception, Betson 2002 hydraulic conductivity, the F.2 bucketing convention). They differ in deliverable: Script 19 generates *scenario_viewer.html*, a self-contained interactive HTML calculator; Script 20 generates the publication-quality static figures for §4.9. Script 19 at \~2100 lines is among the longest in the pipeline; Script 20 at \~4400 lines produces the publication spatial figures (ten headline outputs). The interactive viewer is part of the methods rather than a results artefact: it is the calculator that lets a reader exercise the per-cluster equation engine for any scenario combination, with sliders and parameter values exposed.

### []{#anchor-366}[]{#anchor-367}[]{#anchor-368}Sub-script 19 --- Scenario viewer (interactive HTML)

**Motivation.** The mechanistic content of the report's forestry and climate scenarios sits in three places: the per-cluster β coefficients in *03_master_data.csv*, the seasonal climate baselines from *01_climate.csv*, and the seasonal cluster-mean heads. A reader who wants to interrogate any single scenario --- say, *what does a 30 % winter rainfall increase under UKCP18 2080s do to the C4 Main Forest summer minima?* --- needs all three sources combined through the equilibrium-perturbation engine. Script 19 builds that engine into a self-contained HTML file with every parameter exposed as a slider. Unlike the Flood Forecaster (S.9), which fits a temporal model to a single well, and unlike the Newborough Water-Level tool, which displays the monitoring record, the scenario viewer is purely diagnostic: it lets the reviewer see what the calibrated SSM implies for any combination of climate and forest-management perturbations.

**Methodology.** The engine is the same monthly equilibrium perturbation that Script 21 (S.14) uses for the published scenario figures. For each well with cluster ID *cl*, β coefficients (b₁, b₂, b₃) from the master CSV and seasonal head h (winter, summer or annual mean), *\_well_dh()* computes the equilibrium Δh as the difference between the perturbed and baseline net water-balance fluxes:

> Δh = \[β₁ · P_eff(scenario) − β₂(scenario) · PET(scenario) − β₃ · \|h\|\] − \[β₁ · P_eff(baseline) − β₂ · PET(baseline) − β₃ · \|h\|\]

The β₃·\|h\| terms cancel exactly, leaving a monthly perturbation in the recharge and atmospheric-draw fluxes:

> Δh = β₁ · \[P_eff(scenario) − P_eff(baseline)\] − \[β₂(scenario) · PET(scenario) − β₂ · PET(baseline)\]

For non-forest clusters P_eff equals raw P and β₂ is unscaled. For forest clusters (C4 Main Forest and C5 Coastal Forest, identified through *is_forest = (cl == 4 or cl == 5)*), three transformations apply: (1) baseline P is reduced by the Freeman (2008) canopy interception *(1 − 0.24)*; (2) under a scenario the canopy interception fraction may be replaced (clearfell → 0, broadleaf → 0.15, thinning → 0.12); (3) β₂ may be scaled by a season-specific multiplier *sB2_w* (winter) or *sB2_s* (summer). The forest scaling is identical for C4 and C5 --- the BACI analysis (S.7) does not separate them. The annual response is the unweighted mean of the winter and summer responses, with winter defined as November--April and summer as May--October --- the canopy-state phenological windows (β₂ \< 1 in winter months, β₂ ≥ \~1 in summer months) that the broadleaf β₂ derivation uses.

The Python function *\_well_dh()* and its JavaScript twin *dhOne()* implement this identically. Python-side values (well coordinates, β coefficients, seasonal climate means, cluster-mean heads, KML polygons, the DEM hillshade as a base64-encoded PNG, a coarse DEM grid for ridge masking) are interpolated into a static HTML template at generation time. The duplication is deliberate: JavaScript drives the interactive sliders, and the Python mirror writes *19_scenario_summary.csv* so the same numerical result is available as a citeable file.

**The scenarios.** Six preset scenarios are wired to buttons in the sidebar, with the slider state for each defined in the *SCENARIO_PARAMS* dictionary at the top of the script:

  ------------------------ -------------------- ---------------------- -------------- ---------------------
  Scenario                 P (winter, summer)   PET (winter, summer)   Interception   β₂ (winter, summer)
  Baseline (2005--2026)    1.00, 1.00           1.00, 1.00             0.24           1.00, 1.00
  UKCP18 2050s RCP8.5      1.10, 0.85           1.05, 1.20             0.24           1.00, 1.00
  UKCP18 2080s RCP8.5      1.20, 0.70           1.10, 1.35             0.24           1.00, 1.00
  Clearfell                1.00, 1.00           1.00, 1.00             0.00           dyn., dyn.
  Broadleaf conversion     1.00, 1.00           1.00, 1.00             0.15           0.8817, 1.0750
  Forest thinning (50 %)   1.00, 1.00           1.00, 1.00             0.12           dyn., dyn.
  ------------------------ -------------------- ---------------------- -------------- ---------------------

The clearfell and thinning forest-β₂ multipliers (shown as "dyn." above) are not literals --- they are loaded at script startup through *clearfell_common.load_clearfell_b2_multiplier()*, which reads the BACI-corrected Edge-tier ratio derived in S.7's Script 10e. Version 2.5.0 of Script 19 (April 2026) replaced an earlier hardcoded 1.20 with this dynamic load. The thinning multiplier is the same load with the BACI shift halved. This is the closest the viewer comes to the project's no-hardcoded-values discipline: the values flow from the upstream pipeline through *pipeline_params.py* to both the Python summary CSV and the embedded JavaScript at HTML-generation time.

**Sliders.** Beneath the preset buttons, six climate sliders (Winter P, Summer P, Winter PET, Summer PET, and the C4 and C5 canopy interception controls) and two β₂ scaling sliders (Winter β₂ × C4+C5, Summer β₂ × C4+C5) expose every input to the engine. Each takes a 0.5--1.5× multiplicative range except the interception sliders, which span 0.0--0.4 in absolute units (so a "0.00" position means "no canopy", as in the clearfell preset, rather than "no perturbation"). The 0.5--1.5× range brackets the UKCP18 end-century probabilistic envelope for Wales under RCP8.5 while staying inside the linear steady-state domain of the fitted SSM.

**The seasonal β₂ split for broadleaf.** Version 2.6.0 (May 2026) merged earlier per-cluster *sB2_c4*, *sB2_c5* sliders into seasonal *sB2_w*, *sB2_s* sliders shared across C4 and C5. Version 2.7.0 (May 2026) consolidated the values to a single source of truth in *utils.config*: the deciduous-conversion preset now uses *sB2_w = 0.8817* (leaves off, reduced atmospheric draw) and *sB2_s = 1.0750* (full canopy, elevated atmospheric draw), derived from Script 21's monthly β₂ profile averaged over the canopy-state phenological windows (Nov--Apr for winter, May--Oct for summer --- see chapter S.14 for the 12-month profile and the rationale for the window choice). Clearfell and thinning multipliers are non-seasonal --- canopy removal itself is non-seasonal --- so the same value is written to both seasons.

**Well exclusions and ridge mask.** Two wells are excluded: *ceh12* (on the bedrock ridge, depth signal the SSM does not represent --- see Script 23 in S.16) and *ceh15* (forest-slack-edge well whose β coefficients fit poorly and would bias the C4 cluster mean). Both exclusions match the pattern in Script 07 (S.5) for the static β maps. The viewer's spatial interpolation is then ridge-masked at runtime: each pixel is checked against a coarse 120 × 110 DEM grid (*build_dem_grid()*) and suppressed where the DEM exceeds the interpolated head surface by more than *RIDGE_MASK_THRESHOLD = 1.0* m. This is the same threshold used by *map_utils.add_idw_surface()*.

**Outputs.** A single self-contained HTML file (*scenario_viewer.html*, typical size 250--300 KB including the embedded base64 hillshade) and a tidy summary CSV (*19_scenario_summary.csv*, one row per scenario × season × spatial unit, where spatial unit is each of C1--C5 plus a site-wide mean). The CSV mirrors the JavaScript calculation through the shared *\_well_dh()* engine. To anchor with one scenario: for UKCP18 2080s annual the site-wide mean Δh is −33 mm, with the largest impacts in C4 Main Forest (−46 mm) and C3 Western Residual (−34 mm) and the smallest in C1 Lake Edge (−17 mm). Forest clusters show the most muted winter response (C4 +25 mm, C5 +26 mm) against summer drawdowns of −118 mm at C4 and −71 mm at C5, giving C4 the largest annual decline of any cluster; the steepest summer drawdown is at C2 Dune (−134 mm). Clearfell produces the inverse --- C4 +40 mm annual, C5 +39 mm annual --- with winter recovery exceeding summer recovery in both forest clusters (C4 winter +47 mm vs summer +32 mm; C5 winter +45 mm vs summer +33 mm). These values appear directly in §4.10.2 of the main report.

**ΔMSL5 row --- v2.8.0 (2026-05-27).** A new top row was added to the viewer's per-cluster scenario summary table, reporting the van Willegen et al. (2025) 5-year mean spring water-level shift defined as the mean of monthly Δh over March, April, and May. The row uses the same pure-climate perturbation formula *Δh(m) = β₁·P(m)·(sP(m)−1) − β₂·PET(m)·(sPET(m)−1)* that Script 26b uses, evaluated at *per-well* β coefficients arithmetically averaged within each cluster --- the existing viewer convention. Canopy interception is *not* applied to the ΔMSL5 row (the existing Δh/storage rows above do apply it for C4/C5); the asymmetry is documented in a footnote under the viewer table. MSL5 is in any case most ecologically relevant for the non-forest clusters C1--C3, where canopy interception does not enter the calculation. Under the pure-climate framing the four land-use presets (baseline, clearfell, broadleaf, thinning) produce ΔMSL5 = 0 identically; only the two UKCP18 climate presets carry non-zero ΔMSL5 values. The scenario summary CSV gains a corresponding *season=\"msl5\"* block (6 rows per scenario: 5 clusters plus a well-count-weighted SITE row; 12 non-zero rows for the two UKCP18 scenarios, 24 zero-valued rows for the four non-climate presets, consistent with the pure-climate framing). The CSV's *season=\"summer\"* block is the data source for Script 26c's §4.10.1 Δsummer-minimum bars.

**Why per-well aggregation, and how it relates to Script 26b.** The viewer's per-well-averaged β does not algebraically reduce to Script 26b's cluster-centroid OLS, even on the same wells: the two aggregations differ by 0.5--3.7 mm per cluster per UKCP18 scenario, with the largest gap in C1 (lake-edge, n = 7, the most heterogeneous reference-network cluster). To anchor the viewer row against a matching canonical reference, Script 26b v1.1.0 (2026-05-27) added a parallel per-well aggregation pathway that writes *26b_msl5_ukcp18_projection_summary_perwell.csv* alongside the canonical centroid summary. The viewer's CSV-side computation includes a cross-script validation block that loads the 26b per-well CSV if present, iterates the 10 (cluster, UKCP18 scenario) pairs, and prints the maximum absolute difference; current state is 0.042 mm worst case (well within the 0.5 mm acceptance tolerance, a rounding artefact of the viewer CSV's 4-dp *round()*). The canonical report numbers for §3.7.5 / §4.8.5 / §4.10.1 remain anchored to the centroid-fitted *26b_msl5_ukcp18_projection_summary.csv* consumed by Script 26c (S.18c); the per-well CSV is a secondary artefact whose role is the viewer-row validation target.

### []{#anchor-368}[]{#anchor-369}[]{#anchor-370}Sub-script 20 --- Publication spatial figures

**Motivation.** Script 20 generates ten spatial outputs that the viewer alone cannot replace: a head-surface map with the stream network and flow vectors (*20_head_surface_streams.png*); a map of the SSM water-balance residual (*20_residual_ssm.png*); an independent topographic check from a smoothed-DEM ridge-slope map (a supporting diagnostic, not carried as a numbered report figure); a flow-weighted forest-drawdown propagation map (*20_drawdown_propagation_nohead.png*, filled no-head form since v1.4.0); a three-figure coastal-process family added in May 2026 (coastal-erosion drawdown, sea-level-rise head response, and the cell-by-cell SLR-erosion net coastal change --- the coastal-figures family, cited in §3.4.5 and §4.9.4 of the main report); a dune-scrape topographic-drain drawdown field at the CEH36 site (*20_scrape_drawdown_nohead.png*, the §5.4.2 "scrape as drain" reading); a composite clearfell pre-fell baseline drawdown that overlays the scrape on the Storm Brendan coastal retreat (*20_clearfell_baseline_drawdown.png*, the §5.4.2/§5.4.3 confounder framing); and a public-summary three-driver comparison panel (*20_public_drivers_panel.png*, a lay-summary figure not numbered in the main report; forest canopy / dune scrape / coastal erosion on the shared sequential drawdown scale). Script 20 generates all ten at publication DPI.

**Methodology.** These figures share a common stack: load the DEM hillshade through *map_utils.load_dem_hillshade()* (the canonical basemap, F.5); compute or load surfaces on the 50 m grid (*np.arange(240200, 243800, 50) × np.arange(362200, 365000, 50)*); overlay KML site features through *draw_kml_features()*; and place well markers at (E, N) with cluster-coloured fills from *config.CLUSTER_COLOURS*. These figures differ in what occupies the central panel:

*Head surface with stream network and flow vectors (20_head_surface_streams.png).* The mean annual head is interpolated to the 50 m grid using the *idw_surface()* helper, which despite its name calls *scipy.interpolate.griddata* with *method=\'linear\'* --- Delaunay-triangulation piecewise-linear interpolation, as in *map_utils.add_idw_surface()* (S.5). The interpolation is augmented with zero-head anchor points every 200 m along the southern, eastern and western sea boundaries, constraining the interpolation at site edges to the saltwater datum. The SAGA-derived stream network is loaded from *data/streams.kml* as polygon cells and drawn as filled polygon outlines. Flow vectors are computed from the head-surface gradient, with magnitudes in the top 5 % suppressed to mask ridge interpolation artefacts, then **normalized to unit length** for display. Contours at 1 m intervals are labelled in m AOD.

**Per-well mean head: all-record method and cross-check.** The mean head at each well is computed as the arithmetic mean of the full observed maOD record --- every valid monthly row from *01_wells_clean_maod.csv* from the well's first measurement to *REFERENCE_CUTOFF_DATE*. The all-record method is deliberately preferred over a windowed approach for three reasons: (i) the head surface is a spatial-geometry product, not a climate-trend product --- it describes where the water table sits, not how it is changing; (ii) a short window (e.g. 2010--2025) would exclude 4--6 early-record years from several wells, including 4 reference C3 wells (CEH39--42) which fall just below a 12-of-16-year completeness threshold at a knife-edge exclusion that would be harder to defend than accepting the full record; (iii) the spatial pattern of mean head --- the SW-to-NE head gradient, the ridge-margin feature, the C5 coastal low --- is robust to the window choice.

A windowed cross-check (water years 2010--2025, ≥ 12 of 16 years with ≥ 10 months/year) was conducted against the all-record means (64 of 88 wells qualifying). The per-well differences are small: median shift −9 mm, maximum shift \~112 mm. The \~112 mm outlier is **NW9**, the central well of the C5 Coastal Forest cluster. The shift is not a measurement artefact --- it reflects a coherent C5-wide downward shift (all five C5 wells shift negative under the windowed method), because the 2006--2009 sub-period carries comparatively high water levels in the coastal-forest zone that the windowing excludes. The effect on the C5 cluster-mean head is ≈ 55 mm cluster-wide (of which NW9 contributes ≈ 14 mm), negligible against the metre-scale inter-cluster head contrasts. The interior aquifer geometry --- the flow vectors, the gradient directions, the residual-field pattern --- is unchanged between methods. The all-record method is therefore retained as the primary, with this windowed comparison as the empirical defence against the question of record-length bias.

*SSM water-balance residual (20_residual_ssm.png).* For each well, the steady-state residual α = β₂·P̄ET + β₃·h_disp − β₁·P̄\_eff is computed at the long-term seasonal mean climate and the well's mean displacement h_disp = DRAINAGE_DATUM + h_depth (F.3). A positive residual means atmospheric draw plus drainage exceeds rainfall recharge --- physically, the well requires an external (lateral) input to balance. The residual is interpolated to the 50 m grid by the same Delaunay-linear scheme, anchored at zero along the sea boundaries. The colour scale is divergent (*RdBu_r*) with *TwoSlopeNorm* anchored at zero and the 95th-percentile of \|residual\| at the limits. Flow vectors on this panel are independent of the residual: they come from the head-gradient calculation of the head-surface map (*20_head_surface_streams.png*), included so a reviewer can read the residual pattern against the flow field without flipping between figures.

*Ridge hillslope gradient --- supporting topographic check (not a numbered report figure).* Slope (degrees) from a 50 m smoothed LiDAR DEM (*scipy.ndimage.uniform_filter*), clipped to the study extent with slopes \< 1° masked to leave the flat dune plain transparent. The figure is DEM-only --- no β coefficients, no interpolation of well measurements It was introduced as a falsifiable cross-check on the residual interpretation, on the reasoning that ridge-derived lateral recharge should coincide with regions of significant ridge slope; with the corrected residual field showing no spatial structure there is no pattern left to cross-check, and it is retained as topographic context for the mean-head and Darcy flow-vector field (§4.9.6, Figure 57), which is the figure it most directly supports.

*Forest drawdown propagation (20_drawdown_propagation_nohead.png).* A flow-weighted cost-distance is computed via Dijkstra's algorithm on the LiDAR DEM (downsampled to 10 m), seeded from forest-boundary cells; cell-to-cell costs are weighted by alignment with the DEM gradient (downhill cheap, uphill expensive). The drawdown signal decays with characteristic length λ = √(K·b / (Sy·β₃)), where D = K·b / Sy is the hydraulic diffusivity. The decay length depends on aquifer properties of the *propagation medium*, not of the forest itself. Since the drawdown signal propagates outward from the forest edge into the surrounding open dune, Sy and β₃ are sourced from C3 (Western Residual): Sy ≈ 0.31 from the C3 cluster median of the per-well WTF estimates (Script 17, S.12) and β₃ from the C3 centroid SSM coefficient (Script 03, S.3) --- currently ≈ 0.057 month⁻¹ under the *limit=1* interpolation policy. With K = 6 m/day from Betson (2002) and saturated thickness b = 5 m, this gives λ ≈ 230 m. The Δh = H₀·exp(−d/λ) field with H₀ = 150 mm (forest interception deficit) is overlaid on the mean head surface, with λ annotated as a horizontal bar. Both Sy and β₃ are read from the live pipeline CSVs at generation time (Script 20 v1.0.1), so the figure tracks the current pipeline state.

#### []{#anchor-370}[]{#anchor-371}Coastal-process figures (erosion, sea-level-rise, and net coastal change)

The forest drawdown figure (*20_drawdown_propagation_nohead.png*) was joined in May 2026 by three companion fields that illustrate western-margin coastal influences on the dune water table. All three are single-mechanism illustrative constructions on the eroding Caernarfon Bay shore only, sharing the DEM hillshade base, the F.5 spatial-figure machinery, and a site-boundary clip applied through *data/site_boundary.kml* so the fields terminate at the coast and the warren edges rather than extrapolating offshore or onto the bedrock ridge. The construction of each field is documented in §3.4.5 of the main report; this sub-section carries the full parameter exposition that §3.4.5 deliberately defers to the supplement.

*Erosion drawdown.* Applies the Script 25 forest-free linear-capped coastal-retreat fit δ(d) = δ₀·(1 − d/L) to a single discrete shoreline-retreat event of magnitude COAST_RETREAT_M = 6 m (the Storm Brendan early-2020 exemplar). The retreat magnitude is converted to an edge water-table drawdown via h₀ = COAST_RETREAT_M · (δ₀ / COAST_RETREAT_RATE), where COAST_RETREAT_RATE = 8.3 m yr⁻¹ is the storm-inclusive long-term retreat rate (Forgrave 2020 / North Wales Live, 22 January 2020 --- Walker-Springett's then-ongoing Bangor coastal-erosion measurements, approximating the ≈ 50 m of retreat between 2014 and 2020). The field decays inland from a dune-edge front derived by offsetting the DEM mean-waterline contour (COAST_SHORE_LEVEL_M = 0.5 m AOD) landward by COAST_DUNE_OFFSET_M = 100 m to the dune toe. δ₀ and L are read live from *25_01_panel_fit_parameters.csv* (Script 25, S.15) at generation time --- currently δ₀ ≈ 0.13 m and L ≈ 1.5 km --- so the field tracks the live coastal-gradient fit. The retreat rate is *storm-inclusive*: a single Brendan-class event normalized by a storm-inclusive rate is the correct construction for a single-event illustration. It is **not** a chronic background retreat rate; the chronic rate at the southern frontage (≈ 1.5--1.8 m yr⁻¹ per Pye & Blott 2024) would be the wrong normaliser here.

*Sea-level-rise head response.* Models the gradual rise as a finite-window boundary perturbation diffusing inland according to Δh(d) = ΔSLR · erfc(d / (2·√(D·t))), where D = K·b/Sy is the hydraulic diffusivity. The boundary is referenced to mean sea level (SLR_SHORE_LEVEL_M = 0 m AOD), as appropriate for a water-table head response (a tidal-inundation construction would instead reference MHWS ≈ +2.9 m AOD from the Caernarfon tide tables, but is not used here). ΔSLR = SLR_RISE_M = 0.02 m over SLR_WINDOW_YEARS = 5 yr matches the UKCP18 north-Wales near-term central estimate (≈ 4 mm yr⁻¹). Aquifer parameters are SLR_K = 6 m day⁻¹ (Betson 2002) and SLR_B = 5 m saturated thickness; Sy is read live as the C3 (Western Residual) cluster median of per-well WTF estimates from *17_wtf_well_sy.csv* (currently ≈ 0.311), matching the propagation-medium convention used for the forest drawdown figure. The figure annotates √(D·t) on the inland axis.

*Net coastal change.* The cell-by-cell difference (SLR head gain minus erosion drawdown) over the matched window, on a diverging colour scale. No additional parameters: the field is purely arithmetic on the two preceding fields. It is *not* a closed water budget --- discussion caveats appropriate to that point appear in *COASTAL_NET_VS_EASTING_MEMO.md* and the §5 weave-in.

**Parameter table.** All controlling parameters for the three coastal-process figures, with their sources and the figures in which each appears. Live-pipeline values are read on each pipeline run and revise if their upstream outputs change; the snapshot values stated here apply at time of writing under the live pipeline state.

  ---------------------------------------------- --------------------- --------------------------------------------------------------------------------------- -------------------------------------------------------- ---------------------------
  Parameter                                      Symbol                Value                                                                                   Source                                                   Used in
  Forest interception deficit at edge            H₀                    150 mm                                                                                  Freeman (2008); estimate at site                         Forest drawdown
  Hydraulic conductivity                         K                     6 m day⁻¹                                                                               Betson et al. (2002); literature                         Forest drawdown, SLR, Net
  Saturated thickness                            b                     5 m                                                                                     Estimate (aquifer architecture; literature)              Forest drawdown, SLR, Net
  Specific yield (C3 propagation medium)         Sy                    ≈ 0.311 (live; C3 WTF median from *17_wtf_well_sy.csv*)                                 Live: Script 17, S.12                                    Forest drawdown, SLR, Net
  SSM drainage coefficient (C3)                  β₃                    ≈ 0.057 month⁻¹ (live; C3 centroid from *03_03_cluster_mechanistic_coefficients.csv*)   Live: Script 03, S.3                                     Forest drawdown
  Storm-magnitude shoreline retreat (exemplar)   COAST_RETREAT_M       6 m                                                                                     Storm Brendan early-2020 exemplar                        Erosion, Net
  Long-term retreat rate (storm-inclusive)       COAST_RETREAT_RATE    8.3 m yr⁻¹                                                                              Forgrave (2020); storm-inclusive normaliser              Erosion, Net
  Dune-toe offset (inland of waterline)          COAST_DUNE_OFFSET_M   100 m                                                                                   Estimate (DEM-derived dune-toe position)                 Erosion, Net
  DEM waterline contour                          COAST_SHORE_LEVEL_M   0.5 m AOD                                                                               DEM-derived                                              Erosion, Net
  Coast-edge anomaly                             δ₀                    live (Script 25 fit)                                                                    Live: Script 25, S.15                                    Erosion, Net
  Erosion-decay characteristic length            L                     live (Script 25 fit)                                                                    Live: Script 25, S.15                                    Erosion, Net
  Mean-sea-level rise (window total)             SLR_RISE_M            0.02 m                                                                                  UKCP18 north-Wales central, near-term                    SLR, Net
  Response window                                SLR_WINDOW_YEARS      5 yr                                                                                    Near-term horizon                                        SLR, Net
  SLR boundary datum                             SLR_SHORE_LEVEL_M     0 m AOD                                                                                 Physical convention (water-table head, not inundation)   SLR, Net
  ---------------------------------------------- --------------------- --------------------------------------------------------------------------------------- -------------------------------------------------------- ---------------------------

**Storm-inclusive versus chronic rate.** The 8.3 m yr⁻¹ retreat rate is the *storm-inclusive* normaliser for a single-event Brendan-class illustration --- the only physically correct choice when the construction is a single discrete retreat event of storm magnitude. Pye & Blott (2024) report chronic background retreat rates at the southern frontage of the warren of approximately 1.5--1.8 m yr⁻¹; that chronic rate is the right number for long-term contextual statements about cumulative shoreline change but is the wrong normaliser for this construction. The two rates are both correct, for different purposes, and the chapter is careful not to conflate them. The chronic rate appears in §5 of the main report (the Pye & Blott discussion weave-in); the storm-inclusive rate appears here and in §3.4.5.

**Caveats specific to the coastal-process figures.** Each field is a single-mechanism illustration on a single coastal frontage. The erosion field combines an episodic event with a chronic-rate normaliser; the SLR field combines a gradual climate process with a finite five-year window. Neither field is a deterministic forecast. The net field is a cell-by-cell difference of the two and inherits the caveats of both; it is not a closed water budget, and "net coastal change" should be read as relative spatial reach of the two opposing processes rather than as a balance. The construction depends on assumed retreat-rate, diffusivity, datum and window parameters, all of which are flagged in the table above; sensitivity to any of these can be assessed by re-running with revised constants. See *COASTAL_NET_VS_EASTING_MEMO.md* (project store) for the easting-correction comparison analysis and §5 of the main report for the wider interpretive caveats.

**Equation forms.** The model forms are stated in §3.4.5 of the main report in LibreOffice StarMath syntax (Δh = H₀·exp(−d/λ), δ(d) = δ₀·(1 − d/L), Δh(d) = ΔSLR·erfc(d/(2√(D·t)))). The supplement does not duplicate these forms; cross-reference §3.4.5 of the main report for equations.

#### []{#anchor-371}[]{#anchor-372}Dune-scrape topographic-drain drawdown (*20_scrape_drawdown_nohead.png*)

Script 20 v1.23.0--v1.24.0 (2026-06-30): drawdown model updated from single-cut envelope to multi-cut additive superposition with method-of-images coastal boundary correction. See CHANGELOG_delta_2026-06-30_scrape_drawdown_physics.md.

The scrape-drain drawdown field models all eight GPS-traced dune-scrape cuts (Feb 2013: CEH40, CEH41, CEH42; Apr 2015: CEH36, Scrape A, Scrape B; Oct 2023: CEH18, CEH21) as permanent co-active features contributing simultaneously to the long-term equilibrium water table. The field is computed as a leaky-aquifer superposition with method-of-images coastal boundary correction:

> dd(x,y) = Σᵢ H₀ᵢ · \[exp(−dᵢ/λ) − exp(−dᵢ′/λ)\]

where dᵢ is the Euclidean distance from grid point (x, y) to the footprint of cut i, dᵢ′ is the distance to the mirror image of cut i reflected across the High Water Mark coastline, λ = √(Kb/Syβ₃) is the leaky-aquifer decay length (live C3 pipeline values; K = 6 m d⁻¹, Betson & Bristow 2002; b = 5 m; λ ≈ 230 m), and H₀ᵢ is the edge drawdown magnitude for cut i.

The image term enforces the physical condition that the coast is a fixed-head boundary: the sea maintains hydraulic head and drawdown must decay to zero at the High Water Mark. The approximation is exact for a straight boundary and locally accurate for the gently curved Caernarfon Bay coast. The coastline geometry is loaded from *data/geo/coastline_hwm.geojson* (OpenStreetMap *natural=coastline*, Caernarfon Bay MHW and Menai Strait, EPSG:27700, ODbL, extracted 2026-06-30; Malltraeth estuary excluded). If *data/geo/coastline_hwm.geojson* is absent, *\_scrape_field()* falls back to unbounded superposition (no image term) with a printed warning.

The edge drawdown H₀ᵢ is set to the matched-control BACI response (Script 09a, S.7) for three monitored cuts: CEH36 +130 mm (Pure_Scraping vs CEH4), CEH21 +74 mm (After_Scraping vs CEH22), CEH18 +9 mm (After_Scraping vs CEH4). For the five unmonitored cuts (CEH40, CEH41, CEH42, Scrape A, Scrape B --- all pre-dating the dipwell network or lacking an in-cut well) H₀ is assumed equal to the CEH36 value and flagged as such in the figure annotation. The CEH36 BACI response also yields an inferred excavation depth of H₀/Sy ≈ 0.42 m via the live C3 specific yield (Script 17, S.12), consistent with the 0.40 m design depth.

The scrape interior (footprint plus a 10 m collar) is masked: each cut slack rises at the excavation, not falls, so the field displayed is the surrounding drawdown --- the dipole counterpart of the slack rise observed at the monitored cuts (the §S.7 scraping BACI step). The modelled drawdown reach is not independently resolved in the 88-well network (Script 09b distance-decay, p = 0.54).

The spatial reach of the drawdown field is modelled (leaky-aquifer superposition); the edge magnitudes at three of the eight cuts are empirically anchored to measured BACI responses. The same field is used by *plot_scrape_coastal_net()*, *plot_net_state_map()*, and *plot_public_panel()* via the shared *\_scrape_field(gx, gy)* helper. The figure is the methodological evidence underpinning §5.4.2's "scrape as topographic drain" reading of the wet-slack BACI response, and contributes the scrape-zone half of the clearfell pre-fell baseline composite below.

#### []{#anchor-372}[]{#anchor-373}Clearfell pre-fell baseline drawdown composite (*20_clearfell_baseline_drawdown.png*)

Script 20 v1.25.0 (2026-06-30): Epoch filter applied --- Oct 2023 cuts (CEH18, CEH21) excluded from this figure. See CHANGELOG_delta_2026-06-30_scrape_drawdown_physics.md.

The clearfell BACI documented in §4.6 and §S.7 controls for a number of confounders through the easting × time covariate, the CWB main effect, and the three-tier control hierarchy. The clearfell-baseline composite figure makes the confounder-set visible as a single drawdown field: scrape + Storm Brendan retreat, both head losses, both rendered on the shared sequential drawdown scale. The composite displays *what the clearfell BACI is correcting against*.

The scrape component of this figure includes only the Feb 2013 (CEH40, CEH41, CEH42) and Apr 2015 (CEH36, Scrape A, Scrape B) cuts --- five cuts in total. The Oct 2023 cuts (CEH18, CEH21) are explicitly excluded: they postdate the clearfell event (December 2017) by six years and played no part in the hydrological conditions at the time of felling. The same leaky-aquifer superposition with method-of-images coastal boundary correction is applied as for the equilibrium drawdown figure above, but restricted to the two pre-clearfell epochs via the *epochs* parameter of *\_scrape_field()*. The Storm Brendan retreat component is the coastal-erosion drawdown evaluated at *COAST_RETREAT_M = 6 m* (a single Brendan-class event), with δ₀ and L from the live Script 25 fit. The composite is *net = scrape + erosion* (both positive drawdowns; not a diverging-scale subtraction).

This figure is *not* a closed water budget. It is a paired-confounder construction: the two head losses that overlap in the western clearfell zone and that the §5.4.2/§5.4.3 framing names as the BACI's principal confounders. It replaces an earlier v1.8.0 attempt at a three-driver *net = SLR − erosion − scrape* diverging-scale composite, which conflated head gain (SLR) with two head losses on a diverging colormap and required a ±50 mm cap that obscured the scrape's own \~129 mm magnitude (v1.10.0 framing rationale). The clearfell-baseline composite drops SLR --- SLR head gain remains available on its own figure (the SLR head response, *20_slr_response.png*, and the SLR − erosion net, *20_coastal_net_effect.png*). The composite is rendered on the shared sequential drawdown scale so the scrape and the storm-retreat drawdown read colour-to-colour against each other and against the forest drawdown field (*20_drawdown_propagation_nohead.png*) --- a like-for-like magnitude comparison across the three driver mechanisms.

#### []{#anchor-373}[]{#anchor-374}Public summary three-driver comparison panel (*20_public_drivers_panel.png*)

A display-only companion figure produced at Script 20 v1.11.0, intended for the lay-summary report and presentations. The panel is a 1-over-2 portrait layout: coastal erosion spans the top of the page, with the forest canopy drawdown and the dune scrape drawdown side-by-side below. Each subpanel uses the shared discrete six-colour banded drawdown scale; the single horizontal colorbar at the bottom of the figure is sourced from the forest panel so the full 2--150 mm range is shown (coastal erosion alone reaches only \~21 mm; scrape \~129 mm; forest spans to \~150 mm). Faint context dipwells are drawn behind each subpanel for orientation; labelled band-boundary contour lines (the *DRAWDOWN_LINE_LEVELS* constants 5, 10, 25, 50, 100 mm with white-haloed labels) overlay each subpanel so the low bands read clearly regardless of fill tint. The plain-language title and caption reinforce the central scientific message: same colour = same amount, no single driver is the whole story. The figure is reproducible directly from *plot_public_panel()* and reuses the underlying field helpers (*\_forest_field*, *\_scrape_field*, *\_erosion_field*) so the public-facing figure is byte-for-byte consistent with the technical figures elsewhere in the chapter.

#### []{#anchor-374}[]{#anchor-375}Net water-table state map (*20_net_state_map.png*)

Script 20 v1.26.0 (2026-06-30): Scrape rise zones now contribute +H₀ gain to the net state field (previously treated as no change). See CHANGELOG_delta_2026-06-30_scrape_drawdown_physics.md.

The net water-table state map combines all five driver mechanisms into a single cell-by-cell balance: SLR head gain, clearfell canopy-removal gain, and scrape-rise gain on the positive side; forest drawdown loss and coastal-erosion drawdown loss on the negative side. The scrape component enters the net field as a dipole: each cut's footprint (plus a 10 m collar) contributes a gain of +H₀ᵢ mm (the measured BACI response for monitored cuts, assumed = CEH36 value for unmonitored cuts), while the surrounding area contributes a drawdown loss via the superposition-with-images field described above. The net formula is:

> net(x,y) = SLR_gain + clearfell_gain + scrape_rise − forest_loss − erosion_loss − scrape_drawdown

where *scrape_rise* is +H₀ at rise-zone pixels and zero elsewhere, and *scrape_drawdown* is the leaky-aquifer superposition field (zero at rise-zone pixels). This correctly represents the dipole nature of each cut --- the surrounding water table is drawn down, but the slack itself rises --- and ensures the rise-zone patches in the figure reflect the actual net field values rather than a purely visual overlay. All eight cuts are included at their equilibrium epoch (no epoch filter here --- the figure represents the full current-state scrape network, not the pre-clearfell baseline).

#### []{#anchor-375}[]{#anchor-376}Modelled 2005→2025 driver-change map (*20_driver_change_2005_2025.png*)

Script 20 v1.29.0 (2026-07-05): new figure added within the existing script step. No pipeline step-count change.

This figure is a modelled reading of how each driver's contribution to the site water table has shifted between the 2005 and 2025 endpoints of the monitoring record. It is not an observed water-table map --- it is derived by differencing the four modelled driver fields (clearfell canopy removal, scraping, SLR, coastal erosion) evaluated at 2005 conditions versus 2025 conditions, using the same steady-state constructions as the other Script 20 figures. A fifth component, *\_broadleaf_field()*, models the projected 2025-era broadleaf-restock block (i.e. the expected atmospheric-draw increase if the Oct 2023 restocking is a permanent management change). The broadleaf field is the least record-constrained component: the restock was recent and has not yet had time to produce a measurable hydrological signal in the dipwell network, so the field is a modelled scenario rather than an inferred observation. The coastal-erosion component uses the 20-year cumulative retreat at the coastal-gradient fitted rate (not a single-event scenario), making it the strongest of the five components at the western coastal margin. The figure is paired with Script 36's observed climate-removed trend map (§S.20.4) --- modelled versus observed over the same window --- for triangulation. The comparison is honest rather than circular: the two figures use entirely different data and methods and need not agree on spatial pattern, only on broad direction.

#### []{#anchor-376}[]{#anchor-377}Shared drawdown scale across the four drivers

Script 20 v1.4.0 introduced a single shared drawdown colour scale across the forest, scrape, coastal-erosion, and clearfell-baseline composite figures, with refinements through v1.11.1 to the discrete band ramp. The scale is *DRAWDOWN_FILL_LEVELS = \[2, 5, 10, 25, 50, 100, 150\]* mm, banded at the low end (each band is an equal-width colour segment on the colorbar, denser at low magnitudes where the small-magnitude maps reside) and capped at 150 mm with an over-range *set_over* colour. The colours are a discrete six-step warm ramp (*DRAWDOWN_BAND_COLOURS*: cream *#fff3b0* → yellow → gold → amber → orange → brown, then *#5c1d02* for \>150 mm) chosen so adjacent bands are visually distinguishable at α = 0.62, replacing a continuous YlOrBr ramp whose 2--5 / 5--10 / 10--25 mm bands rendered as near-identical pale creams (v1.11.1 fix). The honest-magnitude consequence is that the forest panel reads dark (it spans to \~150 mm) while the erosion panel reads pale (it reaches only \~21 mm) --- that is the intended scientific comparison, not a deficiency in the colour scale. The SLR map (*20_slr_response.png*) keeps its own linear GnBu colormap because head gain is a different quantity from head loss; no shared-scale comparison applies.

**Updated parameter table --- additions for the v1.1.0--v1.11.3 figures.** The coastal-process parameter table above documents the erosion, SLR, and net fields. The additional parameters introduced by the scrape and composite figures are:

  ---------------------------------- --------------------------- ----------------------------------------------------------------------------------------------------- ----------------------------------------------------------------- -----------------------------------------------------
  Parameter                          Symbol                      Value                                                                                                 Source                                                            Used in
  Scrape centre easting              SCRAPE_CENTRE_E             241 161 m OSGB36                                                                                      CEH36, the documented 2015 scrape site                            Scrape, Clearfell-baseline, Public
  Scrape centre northing             SCRAPE_CENTRE_N             363 306 m OSGB36                                                                                      CEH36, the documented 2015 scrape site                            Scrape, Clearfell-baseline, Public
  Scrape long-axis length            SCRAPE_LONG_M               60 m                                                                                                  Estimate (Newborough Warren scrape footprint)                     Scrape, Clearfell-baseline, Public
  Scrape short-axis length           SCRAPE_SHORT_M              30 m                                                                                                  Estimate (Newborough Warren scrape footprint)                     Scrape, Clearfell-baseline, Public
  Scrape long-axis bearing           SCRAPE_BEARING_DEG          45° from N (NE)                                                                                       DEM-derived; long axis points into the warren                     Scrape, Clearfell-baseline, Public
  Scrape edge drawdown magnitude     H₀ᵢ (scrape)                CEH36 +130 mm, CEH21 +74 mm, CEH18 +9 mm (live BACI shifts); unmonitored cuts assumed = CEH36 value   Live: Script 09a, S.7                                             Scrape, Clearfell-baseline, Public
  Inferred scrape excavation depth   D                           ≈ 0.42 m (back-calculated; H₀ / Sy)                                                                   Inferred output (not an input)                                    Scrape (informational only)
  Up-gradient propagation flag       SCRAPE_FAVOUR_UPGRADIENT    True                                                                                                  Coastal-drain physical reasoning                                  Scrape, Clearfell-baseline, Public
  Seaward truncation flag            SCRAPE_TRUNCATE_SEAWARD     False (CEH36 is inland)                                                                               Site-specific (active only for coastal-margin scrape scenarios)   Scrape, Clearfell-baseline, Public
  Seaward minimum elevation          SCRAPE_SEAWARD_MIN_ELEV_M   1.5 m AOD                                                                                             Foreshore-clip threshold (active only when truncation is on)      Scrape (flag-dependent)
  Shared drawdown fill levels        DRAWDOWN_FILL_LEVELS        \[2, 5, 10, 25, 50, 100, 150\] mm                                                                     Banded for low-magnitude resolution + high-end ceiling            Forest, Scrape, Erosion, Clearfell-baseline, Public
  Shared drawdown fill alpha         DRAWDOWN_ALPHA              0.62                                                                                                  Adjacent-band contrast at the low end                             Forest, Scrape, Erosion, Clearfell-baseline, Public
  ---------------------------------- --------------------------- ----------------------------------------------------------------------------------------------------- ----------------------------------------------------------------- -----------------------------------------------------

Site-specific choices.

-   **Three zero-head sea boundaries.** Anchor points are placed every 200 m along the southern Menai Strait edge and the eastern and western Caernarfon Bay edges. Without them the linear interpolation would extrapolate the on-site head pattern off the warren. The anchors are at saltwater elevation (0 m AOD) and reflect the tide-controlled boundary on three sides.
-   *FOREST_INTERCEPTION*\*\* from ***config.py***.\*\* Script 20 imports the 24 % value and applies it to P̄ only for clusters 4 and 5 in the residual computation. Other clusters use raw P̄. The choice matches the SSM design matrix construction in Script 03 (S.3) and the interception treatment documented in F.4.
-   **CEH14 annotation.** The residual map carries a fixed annotation for CEH14 (a northern-edge well that consistently shows the largest positive residual). The annotation prints the well's actual α at runtime rather than hardcoding the value. The CEH14 signal --- large positive water-balance residual co-located with the bedrock ridge --- is the qualitative anchor for the ridge-recharge interpretation taken up in Script 23 (S.16).

### []{#anchor-377}[]{#anchor-378}[]{#anchor-379}Site-specific choices and rationale (suite-level)

-   **50 m grid as the spatial resolution.** Scripts 07, 11b, 19 and 20 all use the same grid. Cell size is large enough to suppress single-well noise in the IDW and small enough that contours read smoothly at the warren's 3.5 × 2.6 km extent. It is not a project-wide convention --- *10b_spatial_step_maps.py* uses 40 m (flagged in S.5) --- but it is the spatial-figure convention.
-   *is_forest = (cl == 4 or cl == 5)***.** The forest-cluster test is the same in both scripts, matching *FOREST_CIDS = (4, 5)* in *config.py* (F.4). Script 19 uses an inline literal; Script 20 imports *FOREST_INTERCEPTION* from *config.py* but uses an inline membership check.
-   **The viewer's equation engine is shared with Script 21.** Both use the same monthly equilibrium perturbation, and ship the same clearfell and thinning multipliers (loaded via *clearfell_common*). The broadleaf β₂ values were briefly divergent between the two source files (Script 19 v2.6.0 used local literals; v2.7.0 consolidated to *utils.config*) --- see *Limitations*.
-   **Forest-drawdown propagation constants from C3.** The forest-drawdown map's diffusivity inputs are sourced from the live pipeline: Sy ≈ 0.31 from the C3 cluster median of *17_wtf_well_sy.csv* (Script 17, S.12), and β₃ from the C3 row of *03_03_cluster_mechanistic_coefficients.csv* (Script 03, S.3) --- ≈ 0.057 month⁻¹ under the *limit=1* policy --- giving λ ≈ 230 m. K = 6 m/day (Betson 2002) and saturated thickness b = 5 m remain literature/estimate literals. The Sy and β₃ loads are dynamic, so the figure tracks pipeline state.

### []{#anchor-379}[]{#anchor-380}[]{#anchor-381}Limitations and known caveats

-   **Displayed flow vectors carry direction only.** Both the head-surface map (*20_head_surface_streams.png*) and the residual map (*20_residual_ssm.png*) normalize (U, V) to unit length before plotting. The docstring's "normalized Darcy quiver" is accurate as to direction; the Darcy K = 6 m/day does not enter the displayed vectors. A reader expecting quiver length to scale with flow magnitude will not see that. K = 6 m/day is used in the forest-drawdown propagation λ length scale, not in the static-figure quivers.
-   **The ***idw_surface()*\*\* name is misleading.\*\* It calls *scipy.interpolate.griddata(method=\'linear\')* --- Delaunay piecewise-linear interpolation, not Shepard inverse-distance weighting. The misnomer is shared with *map_utils.add_idw_surface()* and the S.5 chapter; consistency with the older scripts argues against renaming.
-   **The broadleaf β₂ values are consolidated to a single source of truth.** *utils/config.py* carries *BROADLEAF_B2_WINTER = 0.8817* and *BROADLEAF_B2_SUMMER = 1.0750* --- derived from Script 21's 12-month broadleaf β₂ profile (chapter S.14) averaged over the canopy-state phenological windows (Nov--Apr for winter, May--Oct for summer). Script 19 imports these names directly from config. §4.10.2 of the main report carries these values.
-   **Remaining hardcoded literals in the forest-drawdown map.** *K = 6.0* m/day (Betson 2002), *b = 5.0* m saturated thickness, *H0 = 150* mm, *FLOW_WEIGHT = 0.4*, and *UPHILL_PENALTY = 2.0* are literals in *plot_drawdown_propagation()*. Sy and β₃ are now read from the live pipeline (Script 20 v1.0.1; see *Site-specific choices*). K has an authoritative literature source (Betson 2002); the saturated thickness *b* and initial drawdown H₀ are site-mean estimates with no published per-cluster value at this site and remain reasonable defensive literals --- but should be read explicitly in any sensitivity discussion. The flow-weighting parameters are tuning constants for the Dijkstra cost surface, not physical quantities.
-   **Broadleaf preset uses annual-mean interception, with phenology folded into β₂.** The broadleaf preset sets *sI_c4 = sI_c5 = 0.15* for both winter and summer, but deciduous canopy intercepts ≈ 0 % in winter and ≈ 25 % in summer. The annual mean 0.15 is correct; the seasonal split is absorbed into *sB2_w* / *sB2_s* rather than into interception itself. A reviewer inspecting the slider values may find this counter-intuitive; the engine still computes the correct equilibrium because the β₂ split absorbs the phenology.
-   **Broadleaf interception is a literature average, not a site measurement.** Komatsu et al. (2011) is a deciduous-forest annual mean across multiple sites and species. Unlike the Freeman (2008) 24 % value, which is a Newborough Warren measurement on Corsican pine, the broadleaf value is generic. S.14 inherits the same constraint.
-   **Linear-domain assumption.** All scenarios remain inside the steady-state equilibrium framework. Within-year dynamical trajectories --- the timing of summer minima and winter peaks --- are not resolved. The 0.5--1.5× slider range stays within the linear domain of the fitted β coefficients.
-   **The 50 m grid extends 100 m beyond the well-network convex hull** (*map_utils.add_idw_surface()*, *hull_buffer_m = 100*, applied from map_utils v1.5.0), then is clipped to the NNR site boundary and ridge mask. The extension is bounded nearest-neighbour extrapolation, not genuine interpolation, so observed maps now reach the coastal margin rather than stopping at the outer well ring. Values in the 100 m extension zone --- particularly along the northern bedrock ridge and the southern coast --- should be read as bounded extrapolation. The static figures and the viewer's ridge mask flag these zones.

### []{#anchor-381}[]{#anchor-382}[]{#anchor-383}Outputs

  ------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------
  Output                                                  Description                                                                                                                                                                                                                                                                                                                Reference
  19_spatial_groundwater/scenario_viewer.html             Self-contained interactive HTML calculator (250--300 KB)                                                                                                                                                                                                                                                                   GitHub Pages site (online supplementary tool); §4.9 reference
  19_spatial_groundwater/19_scenario_summary.csv          Per-scenario × season × cluster Δh table (6 scenarios × 3 seasons × 6 spatial units = 108 rows)                                                                                                                                                                                                                            §4.10.1 / §4.10.2 *Scenario analysis*
  20_spatial_figures/20_head_surface_streams.png          Mean annual head surface with stream network and flow vectors                                                                                                                                                                                                                                                              §4.9 *Spatial groundwater* (Figure)
  20_spatial_figures/20_residual_ssm.png                  SSM water-balance residual with independent flow vectors and CEH14 annotation                                                                                                                                                                                                                                              §4.9 *Spatial groundwater* (Figure)
  20_spatial_figures/20_slope_gradient.png                50 m smoothed DEM ridge slope, independent topographic check                                                                                                                                                                                                                                                               §4.9 supporting diagnostic; not a numbered report figure
  20_spatial_figures/20_drawdown_propagation_nohead.png   Flow-weighted forest drawdown propagation with λ length-scale annotation; filled-contour no-head form on the shared discrete drawdown scale (primary form emitted by *main()* since v1.4.0; the with-head form is callable but not in the default run)                                                                     §4.9.3 *Forest drawdown propagation* (Figure 50)
  20_spatial_figures/20_coastal_erosion.png               Coastal-erosion drawdown field for a single Brendan-class retreat event; dune-edge front; δ₀ and L from live Script 25 fit                                                                                                                                                                                                 §3.4.5 *Drawdown-Field Visualisation* / §4.9.4 *Coastal-Margin Processes* (Figure)
  20_spatial_figures/20_slr_response.png                  Sea-level-rise head response over a finite five-year window; erfc transient, mean-sea-level boundary; D = K·b/Sy with Sy live from C3 WTF                                                                                                                                                                                  §3.4.5 / §4.9.4 (Figure)
  20_spatial_figures/20_coastal_net_effect.png            Cell-by-cell net coastal change (SLR head gain minus erosion drawdown); diverging scale                                                                                                                                                                                                                                    §3.4.5 / §4.9.4 (Figure)
  20_spatial_figures/20_scrape_drawdown_nohead.png        Dune-scrape drawdown field, all eight cuts, leaky-aquifer superposition with method-of-images coastal boundary correction; H₀ empirically anchored at three monitored cuts (CEH36, CEH21, CEH18) from live Script 09a BACI shifts; shared discrete drawdown scale                                                          §3.4.5 / §5.4.2 (Figure 55)
  20_spatial_figures/20_clearfell_baseline_drawdown.png   Composite drawdown on the clearfell pre-fell baseline = Feb 2013 + Apr 2015 scrape cuts only (five cuts; Oct 2023 cuts excluded as post-clearfell) + Storm Brendan coastal retreat; both head losses on the shared sequential drawdown scale; paired-confounder construction underpinning the §5.4.2/§5.4.3 BACI framing   §3.4.5 / §5.4.2 / §5.4.3 (Figure)
  20_spatial_figures/20_public_drivers_panel.png          Public-summary three-driver comparison panel (forest canopy / dune scrape / coastal erosion); portrait 1-over-2 layout; shared drawdown scale; band-boundary contour lines                                                                                                                                                 Lay-summary report (Figure)
  ------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------

### []{#anchor-383}[]{#anchor-384}[]{#anchor-385}Where the result appears in the report

-   §3.4.5 *Drawdown-Field Visualisation* --- the methodological home of the drawdown-field figures (forest drawdown, coastal erosion, sea-level-rise head response, SLR-erosion net coastal change, dune-scrape topographic-drain drawdown, and the clearfell pre-fell baseline composite). The methods-register equation forms appear here; the supplement carries the full parameter exposition above.
-   §4.9 *Spatial groundwater* --- the head-surface, residual, and slope maps from Script 20 (*20_head_surface_streams.png*, *20_residual_ssm.png*, *20_slope_gradient.png*).
-   §4.9.4 *Coastal-Margin Processes and the Easting Gradient* --- the three coastal-process figures (*20_coastal_erosion.png*, *20_slr_response.png*, *20_coastal_net_effect.png*) and their interpretive context.
-   §4.9.3 *Drainage Decay Half-Life and Forest Drawdown Propagation* --- the forest drawdown propagation map (*20_drawdown_propagation_nohead.png*) from Script 20, published as report Figure 50.
-   §4.10.2 *Forest Management Scenarios* --- values from *19_scenario_summary.csv* for the clearfell, broadleaf and thinning rows.
-   §4.10.1 *Climate Scenario Projections* --- values from *19_scenario_summary.csv* for the 2050s and 2080s rows.
-   §5.4.2 *The scrape-as-drain reading of the wet-slack BACI* --- the dune-scrape drawdown figure (*20_scrape_drawdown_nohead.png*), all eight cuts, with H₀ anchored empirically at three monitored cuts from live Script 09a BACI shifts, supplies the propagation framing for the §5.4.2 interpretation.
-   §5.4.3 *Clearfell BACI confounder framing* --- the clearfell pre-fell baseline composite (*20_clearfell_baseline_drawdown.png*) renders the scrape + Storm Brendan retreat composite that the BACI's easting × time correction implicitly controls for.
-   Lay-summary report --- the public-summary three-driver comparison panel (*20_public_drivers_panel.png*) is the primary lay-facing figure communicating that no single driver is the whole story.

### []{#anchor-385}[]{#anchor-386}[]{#anchor-387}Cross-references

-   **F.3** --- SSM displacement formulation; the β coefficients the engine consumes.
-   **F.4** --- *DRAINAGE_DATUM*, *FOREST_INTERCEPTION*, *FOREST_CIDS*, *BROADLEAF_INTERCEPTION*, *BROADLEAF_B2_WINTER/SUMMER*, the canonical cluster constants.
-   **F.5** --- *map_utils.load_dem_hillshade*, *map_utils.add_idw_surface*; the shared spatial-figure machinery.
-   **S.3** --- per-cluster β coefficients (*03_03_cluster_mechanistic_coefficients.csv*).
-   **S.5** --- established the 50 m grid convention and the *idw_surface* naming.
-   **S.7** --- Script 10e's BACI-corrected clearfell β₂ multiplier, consumed by Script 19 via *clearfell_common.load_clearfell_b2_multiplier()*. Also Script 09a's BACI shifts (*09_baci_shifts.csv*), consumed live by Script 20 to set the empirically anchored edge drawdown magnitudes H₀ᵢ for three of the eight scrape cuts (CEH36 Pure_Scraping vs CEH4, CEH21 After_Scraping vs CEH22, CEH18 After_Scraping vs CEH4); this empirical anchoring is what underwrites the scrape-as-drain reading at §5.4.2 and the clearfell pre-fell baseline composite at §5.4.3.
-   **S.12** --- WTF cluster Sy estimates consumed for the volumetric translations in §4.9.
-   **S.14** --- Script 21 forestry scenarios; uses the same monthly perturbation engine. The broadleaf β₂ value reconciliation between Scripts 19 and 21 is owed to that chapter.
-   **S.16** --- Script 23 ridge-recharge lag hypothesis test; the qualitative anchor for the CEH14 residual annotation on the residual map (*20_residual_ssm.png*).

## []{#anchor-387}[]{#anchor-388}[]{#anchor-389}S.14 Script 21 --- Forestry scenarios

**Step 23 / 27. Phase 10 --- Forestry Scenario Analysis in ***run_analysis.py***; sixth chapter under Phase 4 --- Climate and Spatial Context in the supplement.**

### []{#anchor-389}[]{#anchor-390}[]{#anchor-391}Motivation

Section 4.10.2 of the main report quantifies how the C4 Main Forest groundwater regime would respond to three management alternatives --- full clearfell, 50 % thinning, and conversion to broadleaf --- under the calibrated SSM. Script 21 is the analysis behind that section. It produces a synthetic mean-year hydrograph that shows each scenario as a monthly perturbation from the observed C4 baseline, alongside an empirical benchmark derived from the BACI clearfell evidence accumulated in Script 10 (chapter S.7), and a series of observed summer-minimum depth distributions that document what actually happened across the site through the 2018 clearfell intervention.

The script is paired with Script 19 (chapter S.13) but answers a complementary question. Script 19's *scenario_viewer.html* is the interactive engine --- the reader-facing calculator that exposes every scenario knob through sliders. Script 21 is the publication artefact: a fixed, citeable figure that pins specific scenario shifts to specific months of the calendar year, and overlays the BACI-observed clearfell displacement as the empirical reference. The gap between the modelled and observed clearfell responses is itself an output of the analysis, not a defect: it represents the multi-year drainage adjustment that the single-step monthly perturbation deliberately does not capture, and it informs the report's framing of what the SSM-based scenarios should be read as.

Script 21 is also the canonical source for the broadleaf monthly β₂ profile that Script 19 and the wider pipeline consume in seasonal-mean form. The 12 monthly values are defined inside *build_scenarios()* and propagate downstream through *config.BROADLEAF_B2_SUMMER* and *config.BROADLEAF_B2_WINTER*, and through *pipeline_params.csv*. Where this chapter and S.13 disagree on summary values, S.14 is the canonical reference.

### []{#anchor-391}[]{#anchor-392}[]{#anchor-393}Inputs

  ----------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------
  Input file                          Description
  03_master_data.csv                  Script 03 --- per-well β coefficients (recharge, atmospheric draw, drainage) and cluster ID
  01_climate.csv                      Script 01 --- monthly P and PET (RAF Valley)
  03_regional_averages_maod.csv       Script 03 --- cluster-mean head time series in m AOD
  Well_locations_height.csv           Raw data input --- DEM ground elevation and pipe-top elevation per well
  *01_wells_clean.csv* (+ extended)   Script 01 --- quality-controlled monthly depth series; used by the distribution and BACI-violin figures
  pipeline_scenario_params.csv        Script 01's consolidated parameter file --- cluster β, Sy, h_disp, peak month, BACI-corrected β₂ multipliers, UKCP18 climate scaling
  10a_report_numbers.csv              Script 10a --- ANCOVA BACI clearfell step for Forest Impact (annual displacement)
  10e_01_coefficient_shifts.csv       Script 10e --- per-well Before / After β coefficients across the five BACI tiers (fallback source for the β₂ multiplier)
  09c_01_summer_minima.csv            Script 09c --- per-well annual summer minima (used by the scraping-era and BACI-violin functions for consistency with the scraping analysis)
  ----------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------

The script does not refit the SSM. All coefficients are loaded from upstream pipeline outputs; the master CSV is the fallback path when *pipeline_scenario_params.csv* is unavailable.

### []{#anchor-393}[]{#anchor-394}[]{#anchor-395}Methodology

**The Option 3 monthly perturbation.** The script's central operation is a single-step monthly perturbation:

> Δh(m) = β₁ · \[P_eff(scen, m) − P_eff(base, m)\] − \[β₂(scen, m) − β₂(base)\] · PET(m)

This is implemented in *model_utils.monthly_perturbation()* and applied for each of the 12 calendar months. P_eff is the effective rainfall after canopy interception; the baseline corresponds to the Corsican pine canopy with *FOREST_INTERCEPTION = 0.24* (Freeman, 2008). β₂(base) is the cluster-mean atmospheric-draw coefficient from *03_master_data.csv*; β₂(scen, m) is the scenario value, which may vary by month for broadleaf conversion and is a uniform multiple of β₂(base) for clearfell and thinning. Each scenario therefore yields a length-12 vector of monthly Δh values relative to the pine baseline.

The β₃ drainage term does not appear. This is not an oversight. The formulation prices the first-month response of the water table to a forcing change: the level at the start of the month has not yet moved in response to the new canopy condition, so the drainage flux β₃·(z₀ + h(t−1)) is identical under baseline and scenario and cancels in the difference. The cancellation is documented in the function docstring and is the same logical step that Script 19's *\_well_dh()* makes. What this means in practice is that the modelled Δh is the immediate forcing response, not the steady-state new equilibrium. Across many months the drainage term will adjust as h itself drifts; the perturbation deliberately does not follow that adjustment forward, which keeps it free of the intercept drift that troubles a literal forward SSM simulation.

**The synthetic mean-year hydrograph.** For script figure 21-01 (*OUT_21_HYDROGRAPH*), the scenario Δh vectors are added to the observed C4 mean monthly depth-below-ground cycle, which is computed from the *03_regional_averages_maod.csv* cluster-mean head series referenced to the C4-mean DEM elevation. The result is four 12-month hydrographs --- Corsican pine baseline (observed), full clearfell (observed + Δh_cf), 50 % thinning (observed + Δh_thin), and broadleaf conversion (observed + Δh_bl). They are plotted on a single axis with the wet-slack winter threshold SD15b and the dry-slack summer threshold SD16 (Curreli et al., 2013) drawn for reference, along with the C1 and C2 observed cycles as spatial context. From Script 21 v1.2.0 the figure is accompanied by a companion data file (*21_forestry_01_hydrograph.csv*, *OUT_21_HYDROGRAPH_CSV*) so the scenario separations can be cited from a pipeline output rather than read off the figure. It carries the plotted monthly depths for every line in tidy long format, and a trough/separation summary that reports each series' deepest month, its separation from the observed C4 baseline at the baseline trough month, and the largest Jun--Sep summer separation with the month it occurs. The two-anchor design is deliberate: the scenario shifts move the deepest month --- the observed baseline troughs one month later than the shifted scenarios --- so a single unqualified "trough separation" would be ambiguous.

The BACI-observed clearfell displacement is overlaid as a benchmark band: a horizontal shift applied to the C4 baseline that brackets the empirical post-2018 displacement at the Forest Impact well WMC3 (and at the wider Edge tier; chapter S.7 has the full BACI account). On the live pipeline data the ANCOVA Forest-Impact clearfell step is +0.113 m annual (95 % CI \[+0.042, +0.183\], p = 0.002, N = 163 months). The summer BACI benchmark band is the clearfell step from a Jun--Sep refit of the Script 10a ANCOVA specification, fit on N = 52 months under the same model terms as the annual headline: intercept, climate-water-balance covariate, distance-weighted scraping, clearfell dummy, CWB × clearfell interaction, and easting × time. The directly-fitted summer step is +0.050 m (95 % CI \[−0.068, +0.168\], p = 0.41, R² = 0.314) --- not significant at conventional thresholds against the Jun--Sep subsample. A CWB-dropped sensitivity variant (+0.123 m, p = 0.058) is emitted to *10a_report_numbers.csv* as *ANCOVA_Forest_Impact_clearfell_step_summer_noCWB*; the full specification is preferred on ΔAIC grounds. The annual headline is the durable BACI-observed clearfell signal; the summer step corroborates the direction but is not retained as a separate statistical claim. This whole construct replaces an earlier arithmetic construct (BACI_ANNUAL × 1.5034) preserved transiently as a fallback in Script 21 v1.0.2 and removed in v1.0.3; the legacy construct is documented as Defect 14 in the project flags log. The chapter writes the headline as displacement towards ground (water table closer to surface = positive in the script's convention).

**The broadleaf monthly β₂ profile (canonical).** Broadleaf conversion is the one scenario where β₂ varies through the year. Deciduous phenology --- bare in winter, full canopy in summer --- gives lower transpirative draw than evergreen pine when leaves are off and higher draw at peak LAI. The canonical 12-month profile is defined directly in *build_scenarios()*:

  ------- -------- -----------------------------
  Month   Factor   Canopy phenology
  Jan     0.85     Leaves off
  Feb     0.85     Leaves off
  Mar     0.88     Bud burst beginning
  Apr     0.92     Partial leaf
  May     0.98     Approaching full leaf
  Jun     1.08     Full leaf, high ET
  Jul     1.12     Peak ET
  Aug     1.15     Peak ET draw
  Sep     1.10     Late season, leaves turning
  Oct     1.02     Early leaf fall
  Nov     0.92     Mostly bare
  Dec     0.87     Dormant
  ------- -------- -----------------------------

The seasonal means consumed by downstream consumers are derived from this profile. With the canonical seasonal windows used by *config.py* --- winter = Nov--Apr, summer = May--Oct --- the means are 0.8817 (winter) and 1.0750 (summer). These are the values exported as *BROADLEAF_B2_WINTER* and *BROADLEAF_B2_SUMMER* in *config.py* and consumed by *scraping_common.compute_scenario_bars()* and by the figure-5 scenario-comparison panel within Script 21 itself. They round to 0.88 and 1.08 in any column where two decimal places are reported. The seasonal-window choice is phenologically aligned: by May the broadleaf canopy is essentially functional (β₂ ≥ \~1 for May through October), and through October the canopy is still operative; April and November are leaf-off shoulder months and are grouped with winter accordingly. The choice is broadleaf-specific --- other seasonal-window definitions in the pipeline (Script 17's PET-negligible Nov--Mar, Script 11b's summer-minimum Jun--Sep) reflect different physical questions and are unchanged.

Broadleaf interception is treated separately from pine and constant through the year: *BROADLEAF_INTERCEPTION = 0.15* (Komatsu et al., 2011, deciduous annual mean). This is a single annual-mean value rather than a seasonal split because the year-round interception loss for broadleaf --- roughly 20 % growing-season, zero in winter --- averages to about 15 % when the canopy is present for half the year.

**The BACI-corrected β₂ multiplier load.** The clearfell β₂ multiplier is not hardcoded. The script reads it through *\_load_baci_params()*, which first attempts *pipeline_params.load_params()* (the consolidated *pipeline_scenario_params.csv* written by Script 01), and on failure falls back to direct read of *10e_01_coefficient_shifts.csv*. The mathematics of the BACI correction itself live in *clearfell_common.load_clearfell_b2_multiplier()*, which computes:

> clearfell_mult = Edge_ratio − Climate_Ctrl_ratio + 1.0

where each ratio is the tier-mean of *b2_after / b2_before* across the wells of that BACI tier (Edge: CEH31, CEH20, CEH30, CEH16; Climate Ctrl: CEH9, NW7, NW6, NW5, WMC2). The Edge tier is used in preference to the Impact well WMC3 because Impact-side post-felling β₂ is suppressed by the canopy that has been removed --- the Edge wells retain pine canopy and receive lateral moisture from the cleared compartment, which gives the cleaner detection of the β₂ shift attributable to felling rather than to the canopy removal itself. The Climate Ctrl correction subtracts the post-2017 background drift. The chapter on Script 10 (S.7) develops the BACI tier structure in full.

On the live pipeline data the loaded multiplier is 1.0315 (Edge ratio 0.9830 minus Climate Ctrl ratio 0.9515, plus 1.0), with the 50 % thinning multiplier defined as half the clearfell perturbation: thinning_mult = 1.0 + (clearfell_mult − 1.0) / 2 = 1.0157. Each tier ratio is computed as the ratio of the tier-mean *b2_after* to the tier-mean *b2_before* (i.e. the pooled mean of the after-period values divided by the pooled mean of the before-period values --- ratio of means, not mean of ratios). These values flow into the b2 arrays in *build_scenarios()* and onwards into the monthly perturbation. The fallback value of 1.20 hard-coded in *\_FALLBACK_B2* reflects an older empirical estimate from a pre-BACI-correction era and is only used if *10e_01_coefficient_shifts.csv* is missing.

**The summer-minimum distribution figure.** Script figure 21-02 (*OUT_21_DISTRIBUTIONS*) is observational, not modelled. For each cluster (C1, C2, C3) and for C4 split into pre-felling (2005--2017) and post-felling (2018--2025) phases, the script computes annual summer-minimum depths from the cluster-mean monthly depth series (the well-mean within each cluster, then the annual maximum depth across June--September). The display is a strip/violin plot with the Curreli thresholds drawn as horizontal reference lines. The accompanying CSV (*21_forestry_02_distributions_means.csv*) carries phase-level mean, median, and the percentage of summers in which the cluster mean fell below SD16, which is the simplest summary the figure aims to convey.

**The scraping-era, BACI-violin, and scenario-comparison panels.** Three further figures sit alongside the headline two. The scraping-era figure (*OUT_21_SCRAPING*) shows annual summer-minimum depths for the three scraped wells (CEH36, CEH18, CEH21) and an unscraped control (CEH4) across four eras (Pre-2015, 2015--17, Post-fell 2018--23, Post-rescrape 2024+), drawing summer minima per well from *09c_01_summer_minima.csv* so the numbers reconcile with chapter S.6. The BACI-violin figure (*OUT_21_BACI_VIOLIN*) shows the same summer-minima distributions but aggregated by BACI tier (Impact, Edge, Forest Ctrl, Coastal Ctrl, Climate Ctrl) across the Pre-2015, 2015--17, and Post-fell phases; tier definitions are loaded from *clearfell_common.TIERS* and match the suite-shared 17-well network. From Script 21 v1.1.0 the per-zone summer minima are computed through the shared *clearfell_common.annual_summer_minimum()* estimator --- each well's annual Jun--Sep minimum taken individually with the provenance / *min_measured = 2* filter, then averaged across the wells of the zone (per-well-then-aggregate), on a window floored at 2011 --- so the violin matches the canonical Script 10d clearfell-BACI summer-minimum method by construction; the single-well Impact zone (WMC3) reduces to that well's own series. The scenario-comparison panel (*OUT_21_SCENARIO_COMPARE*) is the cross-pipeline summary grouped bar chart: per-cluster volumetric Δ in mm w.e./month for clearfell, thinning, broadleaf, and the two UKCP18 climate scenarios (Dry and Wet, 2050s RCP8.5, summer means). The computation runs through *scraping_common.compute_scenario_bars_from_params()*, which uses the same Option 3 formulation but with the full β₁·ΔP − Δβ₂·PET − β₃·Δh_disp form (no β₃ cancellation, because the comparison includes climate scenarios that perturb both P and PET and yield non-trivial h_disp shifts when written in equilibrium terms). The forestry rows in this panel use *BROADLEAF_B2_SUMMER = 1.0750* from *config.py* --- the same canonical value derived from the monthly profile above.

**Volumetric companion (***21_forestry_06***).** Alongside the volumetric panel, *plot_scenario_comparison()* also emits *21_forestry_06_summer_scenario.csv*: the per-cluster equilibrium volumetric metric *Delta_vol_summer_mm_per_month* for the three forest-management scenarios (clearfell, thinning, broadleaf), taken directly from the monthly scenario values and byte-identical with the forestry rows of *09b_05* by construction. The former summer-minimum amplification conversion (*scraping_common* flux → head ÷ Sy → summer minimum × amplification factor) was removed on 2026-07-02. This gives the §4.10.2 forestry narrative a forestry-module source for the volumetric ecological metric rather than having to reach into the scraping suite for it; the climate-scenario comparison remains with *09b_05*.

### []{#anchor-395}[]{#anchor-396}[]{#anchor-397}Site-specific choices and rationale

-   **Monthly perturbation, not forward SSM simulation.** The SSM contains an implicit intercept term that closes the water balance at the well's long-term mean. A literal forward simulation from an arbitrary initial condition does not include that intercept and accumulates drift that has no physical meaning. The Option 3 perturbation circumvents this by expressing the scenario response as a difference against the observed baseline --- the intercept cancels, the drainage term cancels, and what remains is the first-order forcing-change response. This is the first-year-adjustment magnitude, not a steady-state prediction.
-   **The BACI benchmark band as an empirical reference, not a target.** The figure overlays the BACI clearfell observation alongside the modelled clearfell trajectory. The two are not expected to coincide. The modelled value is a first-year forcing-change response; the BACI observation is an integrated displacement over multiple years of post-felling adjustment, during which the drainage flux responds to the new water-table position and the canopy regrowth, soil moisture, and groundwater--subsurface coupling evolve. The gap between modelled and BACI is the multi-year drainage feedback that the perturbation framework deliberately does not capture. Both are useful: the modelled value bounds the immediate response, the BACI value documents what happened.
-   **The β₂ multiplier loaded dynamically through ***pipeline_params***.** The clearfell β₂ multiplier flows from Script 10e to *pipeline_scenario_params.csv* (Script 01) to Script 21 at runtime via *\_load_baci_params()*. There is no hardcoded scenario constant in the script; the BACI evidence drives the scenario directly. The value 1.0315 in the current pipeline is the BACI-corrected Edge-tier ratio (0.9830) with the Climate Ctrl drift (0.9515) subtracted, giving a multiplier of 1.0315.
-   **Forest interception treatment.** The *FOREST_INTERCEPTION = 0.24* (Freeman 2008) value applies to the Corsican pine baseline and to 50 % thinning (taken as 0.12, i.e. half). Broadleaf uses *BROADLEAF_INTERCEPTION = 0.15*. Clearfell uses 0 (no canopy). Interception is a partition of incoming rainfall, not an additive term added to PET --- it reduces effective rainfall reaching the water table. The treatment is consistent with the SSM design matrix construction in Script 03 (chapter S.3) and is documented in F.4.
-   **C4 only for the synthetic hydrograph.** The hydrograph figure shows C4 (Main Forest) only. C5 (Coastal Forest) is forested and shares the same β₂ multipliers in the scenario-comparison panel, but it has no BACI clearfell observation --- the 2018 felling was the C4-side compartment, not C5. The hydrograph's value lies in the BACI overlay, so plotting C5 alongside C4 without an empirical reference would mislead. C5 does appear in the scenario-comparison panel (script figure 21-05) where the modelled response is presented at face value without a BACI anchor.
-   **Cluster-mean β coefficients, not per-well.** All scenario calculations use the cluster mean of *beta_1_recharge*, *beta_2_atmospheric_draw*, and *beta_3_drainage* from *03_master_data.csv*. The scenario response is a cluster-level quantity; per-well projections would over-represent the spread within each cluster, which is captured separately by Script 19's spatial viewer (chapter S.13).

### []{#anchor-397}[]{#anchor-398}[]{#anchor-399}Outputs

  ---------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------
  Output                                   Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                Reference
  21_forestry_01_hydrograph.png            Synthetic C4 mean-year hydrograph: pine baseline, full clearfell, 50 % thinning, broadleaf conversion; BACI benchmark band; SD15b / SD16 reference lines; C1, C2 observed cycles as context                                                                                                                                                                                                                                                                                                                Main report §5.7.4 (Figure 71)
  21_forestry_01_hydrograph.csv            Companion data file for the hydrograph figure (Script 21 v1.2.0+). Block 1 --- the 12-month depth-below-ground series for every plotted line (four management scenarios, observed C4 baseline, both BACI benchmarks, observed C1/C2 context) in tidy long format. Block 2 --- a trough/separation summary: each series' deepest month and depth, its separation from the observed C4 baseline anchored at the baseline trough month, and the largest Jun--Sep summer separation with the month it occurs   Main report §5.7.4
  21_forestry_02_distributions.png         Summer-minimum depth distributions per cluster, with C4 split pre/post-felling                                                                                                                                                                                                                                                                                                                                                                                                                             Pipeline diagnostic; not published
  21_forestry_02_distributions_means.csv   Phase-level mean, median, SD, min, max summer-minimum depths and percentage of summers below SD16                                                                                                                                                                                                                                                                                                                                                                                                          Reference table
  21_forestry_03_scraping_eras.png         Annual summer minima per scraped well (CEH36, CEH18, CEH21) and unscraped control (CEH4), four eras                                                                                                                                                                                                                                                                                                                                                                                                        Main report §4.5.4 (Figure 21)
  21_forestry_03_scraping_era_means.csv    Era-level summaries for the same wells                                                                                                                                                                                                                                                                                                                                                                                                                                                                     Reference table
  21_forestry_04_baci_zone_violin.png      Summer-minimum violins by BACI tier (Impact, Edge, Forest Ctrl, Coastal Ctrl, Climate Ctrl) across three phases                                                                                                                                                                                                                                                                                                                                                                                            Main report §4.6.4 (Figure 33)
  21_forestry_04_baci_zone_means.csv       Tier-level summaries                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       Reference table
  21_forestry_05_scenario_comparison.jpg   Per-cluster volumetric Δ (mm w.e./month) for clearfell, thinning, broadleaf, UKCP18 Dry, UKCP18 Wet                                                                                                                                                                                                                                                                                                                                                                                                        Pipeline diagnostic; not published
  21_forestry_05_scenario_comparison.csv   Same data in tidy form                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     Reference table
  21_forestry_06_summer_scenario.csv       Per-cluster equilibrium volumetric metric *Delta_vol_summer_mm_per_month* for clearfell, thinning, broadleaf --- byte-identical with *09b_05* forestry rows; former summer-minimum amplification conversion removed 2026-07-02                                                                                                                                                                                                                                                                             Main report §4.10.2
  ---------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------

### []{#anchor-399}[]{#anchor-400}[]{#anchor-401}Limitations and known caveats

-   **First-year adjustment, not steady state.** Every Δh produced by *monthly_perturbation()* is the immediate response to a forcing change with h held at its baseline trajectory. The water table will continue to adjust in subsequent months as the drainage flux responds to the new equilibrium head. The synthetic hydrograph is therefore a useful magnitude reference rather than a prediction of the post-management cluster mean depth in year 5 or year 10.
-   **The BACI gap is a feature.** The empirically-observed clearfell displacement at WMC3 and Edge tier (currently +0.113 m annual on the live data, with the directly-fitted summer step at +0.050 m, p = 0.41, N = 52) exceeds the single-month modelled Δh because the BACI step integrates multi-year drainage feedback that the perturbation does not. The figure presents both values; the gap is part of the result. The summer step is not significant at α = 0.05 against the Jun--Sep subsample, and is not retained as a separate statistical claim --- see the headline-values paragraph above and the Defect 14 entry in the flags log.
-   **Broadleaf β₂ --- canonical here, consolidated in config.** The 12 monthly multipliers above are the canonical source. The seasonal means consumed by downstream code are 0.8817 (Nov--Apr) and 1.0750 (May--Oct), and these are what *config.BROADLEAF_B2_WINTER* and *config.BROADLEAF_B2_SUMMER* export. Script 19 imports the same names directly from config. §4.10.2 of the main report carries these values.
-   **Thornthwaite PET caveat.** The script uses the Thornthwaite-estimated monthly PET from RAF Valley (chapter S.10) without revision. The Thornthwaite formulation is temperature-only and is known to underestimate summer PET at this site relative to Penman--Monteith; the scenario differentials are therefore conservative in the summer scaling. Chapter S.10 carries the depth-dependent sensitivity check on this; the implications carry through to the C4 summer-minimum projections in §5.7.4.
-   **C5 absent from the synthetic hydrograph.** No BACI observation exists for C5; the hydrograph plots only what can be anchored to an empirical reference. C5 appears in the scenario-comparison panel where its modelled response is presented on its own terms, and chapter S.13 carries the Script 19 viewer where C5 can be interrogated interactively.
-   **Sy enters at the scenario-comparison panel only.** The hydrograph and the distributions are in head units (m) throughout. The volumetric scenario-comparison panel converts through *cluster.Sy* from *17_wtf_01_sy_estimates.csv* (chapter S.12); the interception correction on forest-cluster Sy is the one Script 17 carries, with the uncertainty discussed there. The scenario-comparison panel inherits the same Sy uncertainty.
-   **Fallback parameters in ***\_load_baci_params()***.** There are no arithmetic BACI fallbacks: missing *10a_report_numbers.csv*, missing *ANCOVA_Forest_Impact_clearfell_step*, or missing *ANCOVA_Forest_Impact_clearfell_step_summer* each raise an explicit error with a remediation message rather than silently substituting an arithmetic construct. The β₂ multiplier fallback (1.20) is independent and remains in place --- it activates only if *10e_01_coefficient_shifts.csv* is missing, and the script prints a *WARNING:* message when it does; chapter consumers should check the log for this message before quoting a β₂ multiplier.

### []{#anchor-401}[]{#anchor-402}[]{#anchor-403}Where the result appears in the report

-   **§5.7.4 *****Forest Scenario Predictions Against the Observed Record*** --- script figure 21-01 (synthetic hydrograph) is published there as report Figure 71; the headline narrative on clearfell, thinning, and broadleaf at C4; the BACI-modelled gap. Script figure 21-02 (distributions) is a pipeline diagnostic and is not published in the main report.
-   **Script figure 21-05** (scenario comparison panel), which carries the cross-cluster volumetric summary, is a pipeline diagnostic and is not published in the main report.
-   **§4.5.4 and §4.6.4 Summer Minima** --- script figures 21-03 (scraping-era) and 21-04 (BACI tier violins) are published there; the forestry chapter draws on them for context where the forestry chapter draws on the scraping and BACI evidence for context.

### []{#anchor-403}[]{#anchor-404}[]{#anchor-405}Cross-references

-   **F.3** --- SSM displacement formulation; β₃ cancellation in the perturbation derivation.
-   **F.4** --- *FOREST_INTERCEPTION*, *BROADLEAF_INTERCEPTION*, *BROADLEAF_B2_WINTER*, *BROADLEAF_B2_SUMMER* constants.
-   **F.5** --- *monthly_perturbation()*, *clearfell_common.load_clearfell_b2_multiplier()*, *scraping_common.compute_scenario_bars_from_params()* shared utilities.
-   **S.3** --- Origin of the per-well β coefficients in *03_master_data.csv*.
-   **S.6** --- Scraping intervention; complement to forestry as a direct-surface management lever; *09c_01_summer_minima.csv* is the shared minima source for script figure 21-03.
-   **S.7** --- Clearfell BACI; origin of the β₂ multiplier and of the +0.113 m annual displacement that anchors script figure 21-01's benchmark band, along with the directly-fitted +0.050 m summer band (Script 10a v1.3.0).
-   **S.10** --- Depth-dependent PET sensitivity; carries the Thornthwaite caveat that propagates here.
-   **S.12** --- WTF Sy values that the scenario-comparison panel consumes for the volumetric conversion.
-   **S.13** --- Script 19's *scenario_viewer.html* is the interactive companion; the Option 3 engine is shared, and the broadleaf β₂ seasonal-mean divergence (defect 11) is documented here as the canonical anchor.

# []{#anchor-405}[]{#anchor-406}[]{#anchor-407}Phase 5 --- Post-pipeline supplementary analyses

The eleven Phase 4 chapters (S.8--S.14) cover the climate-and-spatial scripts that feed §4 of the report. Phase 5 collects six further chapters whose methodological purpose is supplementary: each consumes pipeline intermediates, none feeds downstream pipeline scripts, and the conclusions they produce inform the report's discussion rather than its core results chain. S.15 covers Script 25 (coastal-retreat gradient, step 26/50, Phase 11 in *run_analysis.py*). S.15c covers Script 09f (spatial-reach synthesis figure, step 47/50, Phase 17; display/utility). S.15d covers Script 09g (mechanism-diagram suite, step 48/50, Phase 17; display/utility). S.16 covers Scripts 22, 23, and 24 (residual diagnostics, steps 27--29/50, Phase 12 in *run_analysis.py*). S.18 covers Script 26 (van Willegen 5-year MSL aggregation, step 30/50, Phase 13). S.18b covers Script 11 Section 5 (Tool A --- spring MSL transfer function, embedded in Script 11 at step 11/50, Phase 3) together with Script 26b (Tool B --- UKCP18 RCP8.5 MSL5 projections, step 31/50, Phase 13). S.18c covers Script 26c (MSL5 report-format figures, step 32/50, Phase 13). S.19 covers Scripts 28, 29 and 30 (cluster framework diagnostics, steps 33--35/50, Phase 14). S.20 covers Scripts 32, 33, 35, 36, 37 and 37b (observed differential change, climate-response envelope, and driver validation; steps 36--41/50, Phase 15, all analytical-default as of 2026-07-13). S.21 covers Scripts 24b, 31, 31b, 34 and 38 (supplementary standalone diagnostics, steps 42--46/50, Phase 16 --- 34/38 analytical-default as of 2026-07-13; 24b/31/31b opt-in). S.17 is appendices. All scripts in S.15, S.15c, S.15d, S.16, S.18, S.18b, S.18c, S.19, S.20, and S.21 are part of the pipeline orchestrated by *run_analysis.py*; the "post-pipeline supplementary" framing reflects their role in the report (discussion-feeding rather than results-feeding), not their orchestration status. Scripts 26c (MSL5 report-format figures, Phase 13), 09f (spatial-reach synthesis, Phase 17), 09g (mechanism diagrams, Phase 17), and 27 (greyscale figures, Phase 17) are display/utility steps rather than analytical; Script 26c is documented in S.18c, Script 09f in S.15c, Script 09g in S.15d, and Script 27 in Appendix A.

## []{#anchor-407}[]{#anchor-408}[]{#anchor-409}S.15 Script 25 --- Coastal-retreat gradient

**Step 24 / 30. Phase 11 --- Coastal-Retreat Gradient Analysis in ***run_analysis.py***; first chapter under Phase 5 --- Post-pipeline supplementary analyses in the supplement.**

### []{#anchor-409}[]{#anchor-410}[]{#anchor-411}Motivation

The BACI ANCOVA in S.7 (Script 10a) returned a small but highly significant *easting × time* interaction. Eastings west of the clearfell block were drifting downward against time at a rate the BACI's other covariates --- cumulative water balance, scraping, the clearfell step itself --- could not absorb. That term is what allows the BACI to recover an unbiased clearfell-step coefficient; but it raised a separate question. What was easting × time actually correcting for? The candidate answer was the retreat of the Caernarfon Bay shoreline immediately west of the site, episodic but acute (Forgrave 2020; ongoing monitoring by Walker-Springett, Bangor University; \~50 m between 2014--2020 with most of the loss concentrated in Storm Brendan, January 2020). If the eroding shoreline is exporting freshwater storage westward as the dune front loses width, wells closer to the coast should show steeper summer-minimum declines than inland wells, with the steepness decaying inland on a length scale set by the aquifer's diffusive response.

Script 25 tests that hypothesis. It fits a network-scale, physics-based non-linear regression of per-well summer-minimum trends against perpendicular distance to the eroding Caernarfon Bay shoreline, recovers a forest-independent distance-decay signal --- a coast-edge rate of about −26 mm yr⁻¹ at the reference distance, decaying over an inland reach L ≈ 900 m --- and uses the fit to corroborate the BACI ANCOVA's easting × time term. The third parameter of that fit, the constant c, should not be read as a far-field climate background, and the reason is not that it is confounded with the climate covariate. Its variance inflation factor against the cumulative water balance is 1.01, and against δ₀ it is 1.44, so the constant is separately identified. What disqualifies it is instability with respect to the fitting window: holding the well set fixed and moving only the window start, c runs from −0.10 to +24.20 mm yr⁻¹ while δ₀ stays negative throughout. The constant is a straight line fitted to a non-monotonic series, and it reports the slope of whatever excursion its window spans; judged against the observed far-field trend it tracks that trend only loosely (r ≈ 0.55) and is biased high by about 7 mm yr⁻¹. The far-field decline the network does show is therefore not measured by c, and no far-field rate is quoted from this fit. The distance-dependent parameters are unaffected --- δ₀, the reference-distance rate and L are identified by the distance dependence, not by the level --- and they are what this chapter rests on.

### []{#anchor-411}[]{#anchor-412}[]{#anchor-413}Inputs

  --------------------------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Input file                                                      Description
  *data/well_metadata.csv* (*dist_coast_m*)                       Perpendicular distance to the eroding shoreline; regenerated from the committed coastline geometry (*data/geo/coastline_eroding_hwm.geojson*, OpenStreetMap MHW) and validated in Script 01
  outputs/01_wells_clean.csv                                      Script 01 --- reference-network depth time series
  outputs/01_wells_extended.csv                                   Script 01 --- extended-network depth time series
  outputs/01_locations.csv                                        Script 01 --- well coordinates
  outputs/01_climate.csv                                          Script 01 --- RAF Valley monthly P, PET
  outputs/03_master_data.csv                                      Script 03 --- cluster assignments
  outputs/14_climate_projections/14_summer_trend_stats.csv        Script 14 --- cluster-centroid summer-minimum slopes
  outputs/10_clearfell_baci/10a_02_ancova_full_coefficients.csv   Script 10a --- BACI ANCOVA coefficients for the corroboration check
  --------------------------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-413}[]{#anchor-414}[]{#anchor-415}Methodology

**Functional forms.** Two candidate decay forms are fitted, each with three parameters: a coast-edge anomaly δ₀ (mm yr⁻¹), an inland reach L (m), and a far-field asymptote c (mm yr⁻¹).

The linear-with-cutoff form follows a Dupuit--Forchheimer strip-aquifer interpretation, in which the water-table response to a steadily retreating boundary decays linearly with distance from that boundary and asymptotes to the climate background beyond the reach L:

> δ(d) = max(δ₀ · (1 − d/L), 0) + c

(For δ₀ \< 0 --- the physically expected sign for an eroding boundary --- the *max* becomes a *min* so that the gradient does not change sign at d \> L.)

The exponential decay form follows a diffusive / transient interpretation, in which the response falls off smoothly with no hard cutoff:

> δ(d) = δ₀ · exp(−d/L) + c

Both forms are tried at each specification, and AIC is used to compare them.

**Three specifications.** The fits are run at three increasingly stringent specifications to eliminate forest cover as a confound:

1.  **Full network.** All clusters, with the 17 clearfell-zone wells (Impact + Edge + Forest controls + Coastal controls, imported from *clearfell_common.py*) dropped to prevent the felling-induced rise from contaminating the gradient signal. FE1--4 (broadleaf-restock) and CEH36 (scraping) are also excluded as direct intervention effects.
2.  **Forest-free network.** C1, C2, and C3 only; C4 and C5 excluded entirely. If the distance-decay signal survives the removal of both forest clusters, forest cover cannot be the principal driver of the apparent gradient. This is the *headline* specification --- used downstream for cluster attribution and BACI corroboration.
3.  **C3 only.** The single non-forested cluster with wells at intermediate distances. The closest C3 well sits at d ≈ 400 m, so a 3-parameter fit on this restricted distance range is under-identified --- *c* is held to the forest-free value. The C3-only fit is the sensitivity check: if the gradient is real, it should reproduce on a single cluster.

**Per-well summer-minimum slopes.** Script 25 fits its own per-well annual summer-minimum slopes; it does *not* load per-well slopes from Script 14 (which produces cluster-centroid slopes only). For each well with at least 8 hydrological years (*PANEL_OBS_MIN_YEARS = 8*) of April--September observations, an OLS regression of summer-minimum depth on hydrological year returns a slope (m yr⁻¹) and standard error. These appear in the scatter visualization (panel a of the diagnostic figure) and as a per-well mean reported alongside the Script-14 centroid in the cluster partition.

**The panel fit method.** Non-linear fits run on the monthly long-form panel, not on the per-well slopes directly. Each panel observation has three components: well-and-month fixed effects absorbed by within-well demeaning (Frisch--Waugh--Lovell), a centred-cumulative-water-balance covariate (P − PET anomaly cumsum, mm), and a constrained decay term δ(d_w) · t whose coefficient is fixed at 1 --- non-linear search runs over the three parameters of δ(d_w) alone. Fitting is by *scipy.optimize.least_squares* with bounds on each parameter; the Jacobian gives a covariance matrix and Wald 95% CIs.

**Cluster attribution.** The headline (forest-free linear-capped) fit is applied to each cluster's mean distance-to-coast to compute a *gradient-only* component (δ₀ · (1 − d̄/L), clipped at zero beyond the cutoff). The decomposition is computed against a declared, balanced observed basis: *observed_balanced_annual_mean_mm_yr*, the OLS slope of the annual cross-well mean of the per-well seasonal metric, taken over the same well-set as the per-well slopes. That is one regression on one annual series rather than an average of per-well fits taken over different record windows, and the column *decomposition_basis* names it inside the file so the basis travels with the table. The Script-14 cluster-centroid slope and the mean of the per-well slopes are retained beside it as context columns and are no longer subtracted from: the earlier table subtracted the model from the centroid slope, which put three different bases into one subtraction, since the panel δ(d) is CWB-adjusted and all-season while the per-well slopes are raw annual seasonal-metric OLS and the centroid is a third quantity again. Four components are then reported against the basis: the coastal gradient; the climate contribution 1000 · β_cwb · d(CWB)/dt carried by the cumulative-water-balance covariate; the fitted far-field offset c; and the unexplained remainder. The offset and the climate contribution are written as separate columns because they measure different things, and because the offset is a window statistic rather than a rate, as the Cluster attribution note above sets out; the former column names *predicted_climate_mm_yr*, *predicted_total_mm_yr*, *residual_mm_yr* and the *\*\_pct_of_observed* shares are retired rather than reused, so a reader written against the old table fails loudly instead of reading a different quantity under a familiar name. Because each component is a rate rather than a share of a fitted total, a component can exceed the basis in either direction. The unexplained remainder does so at the clusters beyond the inland reach, which is the honest reading of a model that explains none of their deepening. The coastal gradient does so at C5, where it slightly over-explains a decline the balanced basis puts at −16.15 mm yr⁻¹.

**BACI corroboration.** The BACI ANCOVA fits *delta_easting × months_since_intervention* as a covariate to absorb monotonic spatial drift. Its coefficient (units: m per m-easting per month) implies an absorbed differential deepening rate at the impact zone relative to each control tier, which can be compared directly against the gradient model's predicted differential δ(d_impact) − δ(d_control). For each (control tier × impact zone) pair, Script 25 computes both, runs a z-test of one against the other, and labels the pair "consistent" if \|z\| \< 2. The Forest-Impact comparison is the principal check: if the BACI's easting × time term is doing nothing but coastal-retreat correction, BACI absorption and model prediction should agree.

### []{#anchor-415}[]{#anchor-416}[]{#anchor-417}Site-specific choices and rationale

-   **Caernarfon Bay west-facing coast only.** Only the \~15 km Caernarfon Bay west-facing shoreline is included. The Menai Strait north-east coast is a tidal channel, not subject to the SW-prevailing-wind erosion regime, and per project knowledge is not retreating. Llanddwyn Island is a bedrock islet, hydrogeologically separate. The Malltraeth Sands estuary is sheltered estuarine. The included polyline wraps around Abermenai Point at the SE end of the bay, which matters for the geometry of several eastern wells that would otherwise be misallocated.
-   **Perpendicular distance, in-pipeline.** The minimum perpendicular distance from each well to any segment of the eroding-shoreline polyline, in EPSG:27700 --- geometrically correct for the irregular coastline. Computed in Script 01 as a pure-*numpy* point-to-polyline calculation (no *geopandas*/*shapely* dependency) from the committed west-facing coastline geometry (*data/geo/coastline_eroding_hwm.geojson*), and validated against the committed *dist_coast_m* values (audit: *outputs/01_dist_coast_validation.csv*).
-   **Clearfell-zone exclusion.** All 17 BACI wells (WMC3 Impact + 4 Edge + 5 Forest controls + 2 Coastal controls + 5 Climate controls) are dropped from the full and forest-free fits. The December 2017 clearfell drives a positive water-table rise at Impact and Edge wells that would appear as a non-monotonic distance perturbation if left in. The list is imported from *clearfell_common.py* so any BACI design update propagates automatically.
-   **C3-only fit holds ***c*\*\* fixed.\*\* With no C3 well at d → 0, the three-parameter fit becomes under-identified: δ₀ and c trade off. Holding c to the forest-free value (−0.10 mm yr⁻¹ for linear-capped; +2.12 mm yr⁻¹ for exponential, read from *25_01_panel_fit_parameters.csv*) reduces the C3-only problem to two parameters and tests whether the same coast-edge anomaly is recoverable from C3 wells alone.
-   **Storm Brendan is not separated.** The coastal-retreat rate is treated as a long-run mean. Newborough's retreat is in fact episodic --- order-of-magnitude losses concentrated in single storms, with Storm Brendan (January 2020) the principal event of the study period. The mean rate is the methodologically defensible quantity given the data; the implications are taken up in *Limitations*.

### []{#anchor-417}[]{#anchor-418}[]{#anchor-419}Results to describe at the methodological level

All fits (each specification by two functional forms) are written to *25_01_panel_fit_parameters.csv*, together with the trend each returns at the reference distance. The headline coast-edge rate is quoted at 150 m from the shoreline rather than at the shoreline itself. The decay amplitude δ₀ is the value at zero distance, where no well sits --- the nearest is at 147 m --- so it is an extrapolation beyond the network, and it is the one distance at which the two functional forms disagree materially: they differ by 9.3 mm yr⁻¹ at the shoreline and by 1.6 mm yr⁻¹ at 150 m, converging further inland. Quoting the headline where the network has observations removes a dependence on a functional-form choice the data cannot make, rather than adjudicating it. The reference distance is the nearest round distance inside the observed range, so the headline is interpolated by construction, and Script 25 checks it against the panel's own minimum distance on every run. The cluster attribution and the BACI corroboration already evaluate the fitted decay at a cluster's mean distance, so the convention makes the headline consistent with the quantities derived from it. On the forest-free panel the headline rate is −26.18 mm yr⁻¹ (SE 1.45, 95 % CI \[−29.0, −23.3\]), its standard error propagated across the full parameter covariance by the delta method.

Model selection by AIC favours the exponential form under every specification: ΔAIC (exp − lin-cap) is −4.9 on the forest-free panel, −4.1 on the full network and −15.5 on C3-only. The linear-capped form is nevertheless retained as the headline form, on two grounds. Its Dupuit--Forchheimer strip-aquifer interpretation supplies a finite inland reach, which the exponential does not. Its far-field asymptote also carries the right sign: the exponential returns +2.12 mm yr⁻¹, a rising far field, against an observed far-field trend of −6.14 mm yr⁻¹ across the 41 wells beyond 950 m over the same window, and it crosses zero near 1400 m, predicting the inland table to shallow. The exponential buys its advantage in the near field and pays for it in the far field, where the misfit is spread thinly enough over many wells that AIC barely penalises it. Because the headline is quoted at 150 m, where the forms agree to within 1.6 mm yr⁻¹, the choice of form does not carry the headline in any case.

The three all-season linear-capped fits --- full network, forest-free and C3-only --- return δ₀ values in the range −29.1 to −31.7 mm yr⁻¹, L values in the range 895--994 m, reference-distance rates of −24.5 to −27.4 mm yr⁻¹, and c values close to zero (−0.47 to −0.10 mm yr⁻¹). As the Cluster attribution note above sets out, c is not a far-field climate background: it is a window statistic rather than a rate.

The C3-only reference-distance rate (−24.47 mm yr⁻¹, SE 2.09) and the forest-free network rate (−26.18 mm yr⁻¹, SE 1.45) differ by 1.7 mm yr⁻¹, with substantially overlapping 95 % confidence intervals (\[−28.6, −20.4\] against \[−29.0, −23.3\]). That compatibility is the chapter's primary identification claim: a coast-edge anomaly of the same sign, and of a magnitude the forest-free fit cannot be distinguished from, is recoverable from a single non-forested cluster, which is what rules out forest cover as the principal driver. The two estimates agree to within about one standard error.

The per-cluster attribution under the headline fit is in *25_03_cluster_partition.csv*, computed against the declared balanced basis. C5 (Coastal Forest, mean d̄ ≈ 419 m) carries by far the steepest observed decline (−32.7 mm yr⁻¹ on the basis; −35.9 mm yr⁻¹ at the Script-14 centroid, retained as a context column); the gradient model attributes −15.6 mm yr⁻¹, about 48 % of the basis, to coastal retreat, leaving −20.3 mm yr⁻¹ unexplained. C3 (Western Residual, d̄ ≈ 826 m) declines by −7.7 mm yr⁻¹ on the basis, of which the gradient accounts for −2.4 mm yr⁻¹, about 31 %. C1, C2 and C4 sit beyond the inland reach L, so their gradient component is zero; against balanced declines of −11.0, −10.1 and −12.6 mm yr⁻¹ the modelled total is +3.2 mm yr⁻¹ --- the climate term the cumulative-water-balance covariate carries, plus the fitted offset --- so the whole of their deepening, and a little more, is left unexplained. Why a mean of per-well slopes made that far-field deepening look smaller and better behaved is set out in *25_10_record_length_composition.csv*: within C2 the four wells with 20--21 years of record average −11.0 mm yr⁻¹ while the twenty with 15--17 years average +1.2 mm yr⁻¹, so a mean over per-well fits reports a composition of record lengths as though it were a rate.

The BACI corroboration in *25_04_baci_corroboration.csv* reports the easting × time term fitted in each ANCOVA contrast, and the differential drift each absorbs. The coefficient collapses by more than an order of magnitude and changes sign as the easting separation grows, which is what a single scalar easting difference multiplied by elapsed months produces: within any one per-contrast fit the term is collinear with a plain linear time trend, so the easting sets only the column's scale. What it absorbs is therefore a nuisance parameter fitted to whatever the model leaves, not an independent estimate of the coastal gradient. An earlier version of this section set the absorbed drift against the Script 25 gradient prediction and read the agreement at the Forest tier as corroboration. That comparison is withdrawn (D-050): it places two quantities of different kinds side by side, and the agreement at the Forest tier is as much a consequence of that tier's narrow easting span as the disagreement elsewhere is of a wide one. The file still carries the z_test_baci_vs_model and consistent columns from that reading, and they should not be quoted. Headline numbers are repeated in *25_report_numbers.csv* for downstream cross-referencing.

### []{#anchor-419}[]{#anchor-420}[]{#anchor-421}Limitations and known caveats

-   **The coastal-retreat rate itself is not fitted.** The model fits a per-well *response* to distance from a *known eroding boundary*; it does not derive the retreat rate from the water-level data. The literature value (\~50 m over 2014--2020, with acute losses in Storm Brendan, January 2020) is the assumed driver.
-   **Episodic retreat is averaged to a mean rate.** Storm-event losses are absorbed into a long-run mean. Defensible for the question asked (does retreat *signal* in the data?) but understates year-to-year variability and any qualitative non-linearity in the dune-front aquifer's response.
-   **The C3-only sample is modest.** 19 wells after the clearfell-zone exclusion (the live 21-well C3 minus the WMC3 BACI Impact well and the CEH36 scrape site). Three wells sit at d \< 400 m --- CEH4 (221 m), CEH21 (232 m) and CEH18 (302 m) --- anchoring the inward end of the fit; the remaining 16 are at d ≥ 458 m. The δ₀ recovered is a partial extrapolation from intermediate-to-inner distances. Closeness to the forest-free δ₀ is the reassurance; under-identification (hence c held fixed) is the caveat.
-   The cluster partition's per-well subsample is small in the forested clusters. After the clearfell-zone exclusion, the per-well slope panel contains four C4 wells and three C5 wells. The decomposition is computed against the balanced observed basis rather than the Script-14 centroid slope, and the centroid and the per-well mean are retained beside it as context columns. C5's *coastal_gradient_pct_of_basis* (113 %) should be read with that small subsample in mind: the fitted gradient slightly over-explains the cluster's observed decline, which a three-well basis cannot resolve finely.

### []{#anchor-421}[]{#anchor-422}[]{#anchor-423}Outputs

  -------------------------------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------
  Output                                                               Description                                                                                                                                                                        Reference
  25_coastal_gradient/25_01_panel_fit_parameters.csv                   All six fits (3 specs × 2 forms): δ₀, L, c with SE and 95% CI, AIC, n                                                                                                              Report §5.4.3, §5.7.2
  25_coastal_gradient/25_02_per_well_summer_min_slopes.csv             Per-well annual summer-minimum OLS slopes (m yr⁻¹), SE, p, R², n_years, easting, northing, cluster, distance to coast                                                              Diagnostic figure panel (a)
  25_coastal_gradient/25_03_cluster_partition.csv                      Cluster attribution: observed centroid slope, observed per-well mean, predicted gradient + climate + residual, gradient pct                                                        Report §5.8, §5.9
  25_coastal_gradient/25_04_baci_corroboration.csv                     BACI easting × time absorption vs model prediction for each (control × impact zone) pair, with z-test and consistency verdict                                                      Report §5.4.3, §5.7.2
  25_coastal_gradient/25_05_fit_diagnostic.jpg                         Two-panel figure: (a) per-well slopes vs distance with three fits, (b) cluster stacked-bar decomposition                                                                           Report figure
  25_coastal_gradient/25_06_baci_corroboration_chart.jpg               Forest plot of BACI absorption vs model prediction per pair                                                                                                                        Report figure
  25_coastal_gradient/25_07_cluster_decomposition.png                  Horizontal stacked-bar figure: each cluster's observed centroid slope decomposed into climate + coastal + residual. New at v1.1.0 (2026-05-29, folded in from retired Script 30)   Report §4.8.2 figure
  25_coastal_gradient/25_report_numbers.csv                            Headline numbers in project-standard *Parameter, Well, Era, Value, Unit, Note* format                                                                                              Report cross-referencing
  25_coastal_gradient/25_02_per_well_spring_mean_slopes.csv            Per-well annual spring-mean OLS slopes (spring sibling of 25_02)                                                                                                                   Supp. Note S8
  25_coastal_gradient/25_03_cluster_partition_spring.csv               Spring cluster attribution: all-season gradient applied to 14_spring_trend_stats.csv                                                                                               Supp. Note S8
  25_coastal_gradient/25_05_fit_diagnostic_spring.jpg                  Spring diagnostic: per-well spring slopes with the all-season fits, and the spring cluster decomposition                                                                           Supp. Note S8
  25_coastal_gradient/25_07_cluster_decomposition_spring.png           Spring per-cluster decomposition (spring sibling of 25_07)                                                                                                                         Supp. Note S8
  25_coastal_gradient/25_08_spring_vs_summer_comparison.csv (+ .png)   Observed centroid slope by cluster, summer minimum versus spring mean                                                                                                              Supp. Note S8
  25_coastal_gradient/25_09_season_interaction_test.csv                Season × δ(d)·t interaction test: γ, SE, t, p on the forest-free panel                                                                                                             Supp. Note S8
  -------------------------------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------

All paths resolve through *utils/paths.py* (*OUT_25_FIT_PARAMETERS*, *OUT_25_PER_WELL_SLOPES*, *OUT_25_CLUSTER_PARTITION*, *OUT_25_BACI_CORROBORATION*, *OUT_25_FIT_DIAGNOSTIC*, *OUT_25_BACI_CHART*, *OUT_25_CLUSTER_DECOMP_FIG*, *OUT_25_REPORT_NUMBERS*, *DIR_25*).

**Update --- 2026-05-29 (Script 25 v1.0.1 → v1.1.0).** Two changes were folded into Script 25 in the post-review cascade. First, *25_03_cluster_partition.csv* gains two percentage-share columns parallel to the existing *gradient_pct_of_observed*: *climate_pct_of_observed* and *residual_pct_of_observed*. All existing columns and numerical values remain byte-identical. Second, a new figure *25_07_cluster_decomposition.png* renders the per-cluster decomposition as a horizontal stacked-bar visualization, with each bar showing the cluster's observed centroid summer-minimum slope (diamond marker) decomposed into climate-uniform background (blue), coastal-retreat gradient (red), and unattributed residual (grey), and the cluster's mean perpendicular distance to coast and (n-in-fit / n-total) annotated to the right. This figure lands in §4.8.2 of the main report as the visual companion to the per-cluster decomposition table inserted in that section. The fold-in retired a short-lived standalone script (*30_cluster_slope_decomposition.py*, 2026-05-27 to 2026-05-29) that produced the same figure from already-existing Script 25 outputs; the decomposition logic is now resident in *cluster_partition()* and the rendering in *plot_cluster_decomposition()*. See also §S.19 for the post-review cluster framework diagnostics that motivated the surfacing of this decomposition as a report-level table and figure.

### []{#anchor-423}[]{#anchor-424}[]{#anchor-425}Where the result appears in the report

-   §5.4.3 --- coastal-retreat gradient context for the BACI clearfell step.
-   §5.7.2 --- corroboration of the BACI's *easting × time* covariate as a coastal-retreat correction at the Impact zone.
-   §5.8 --- cluster-level summer-trend partition (C5 Coastal Forest attribution, C3 Western Residual attribution).
-   §5.9 --- implications for the whole-site interpretation of summer-minimum decline.
-   Conclusions --- coastal retreat as a network-wide confound on long-term trend interpretation.

(The acknowledgement edits to §5.4.3, §5.7.2, §5.8, §5.9 and Conclusions regarding coastal retreat's network-wide implications are in progress at the time of writing.)

### []{#anchor-425}[]{#anchor-426}[]{#anchor-427}Cross-references

-   **F.3** --- SSM displacement formulation; the per-well slopes in Script 25 are independent of the SSM but the cluster attribution lands against an SSM-fitted picture.
-   **S.3** --- Script 03's cluster assignments are the basis for the per-cluster partition.
-   **S.7** --- Script 10 suite (BACI); Script 25's BACI corroboration directly references Script 10a's *easting × time* coefficient.
-   **S.13** --- Script 19's residual and per-well slope figures show the same coast-to-inland gradient from an independent visualization. Script 20's coastal-process figures (*20_coastal_erosion.png*, *20_slr_response.png*, *20_coastal_net_effect.png*) consume δ₀ and L from this chapter's *25_01_panel_fit_parameters.csv* live at generation time; see *COASTAL_NET_VS_EASTING_MEMO.md* (project store) for the SLR-extended comparison against the BACI easting × time coefficient.
-   **S.15c** --- Script 09f (spatial-reach synthesis figure) reads δ₀ and L live from *25_01_panel_fit_parameters.csv* produced by this chapter.
-   **S.15d** --- Script 09g (mechanism diagrams) draws its coastal reach from the columns of *09f_01_reach_profile.csv*, whose coastal decay derives from this chapter's δ₀ and L.
-   **Supplementary Note S8** --- the spring-mean seasonal robustness analysis (Scripts 09c, 10d, 10l, 14, 25), which reuses this chapter's all-season coastal-retreat gradient and adds the season × gradient interaction test.
-   **S.16** --- Scripts 22/23/24 residual diagnostics, which benefit from the coastal-gradient framing established here.

## []{#anchor-427}[]{#anchor-428}[]{#anchor-429}S.15c Script 09f --- Management-interventions-versus-coastal-retreat spatial reach

Step 47/50, Phase 17. Display/utility tier, not analytical. Documented here as a companion to §S.15 (Script 25, coastal gradient), whose outputs it reads.

### []{#anchor-429}[]{#anchor-430}[]{#anchor-431}Motivation

The scenario figures (Scripts 09b/09d) and the spatial drawdown fields (Script 20) quantify individual interventions, but the report's §5.8 argument --- that forest management and scraping are spatially confined while coastal retreat is a basin-wide drawdown --- is best carried by a single figure placing all of them on one axis. Script 09f produces that synthesis figure.

### []{#anchor-431}[]{#anchor-432}[]{#anchor-433}Inputs

All read live from committed pipeline outputs:

  -------------------------------- ------------ -----------------------------------------------------------------------------------------
  Input file                       Source       Contents
  20_report_numbers.csv            Script 20    Drawdown length scale λ; forest interception deficit H₀
  25_01_panel_fit_parameters.csv   Script 25    Coast-edge retreat gradient δ₀ and inland reach L (forest-free linear-capped fit)
  09d_01_scenario_comparison.csv   Script 09d   Observed scraping off-site bar
  10a_report_numbers.csv           Script 10a   Measured clearfell recovery (ANCOVA_Forest_Impact_clearfell_step row)
  config.py                        ---          *SCRAPE_RISE_BUFFER_M*, *COAST_RETREAT_M*, *COAST_RETREAT_RATE* (shared with Script 20)
  -------------------------------- ------------ -----------------------------------------------------------------------------------------

The measured scrape BACI edge response comes from the site-observations registry via the same *09_baci_shifts.csv* path used by Script 20.

### []{#anchor-433}[]{#anchor-434}[]{#anchor-435}Method

Each intervention and driver is expressed as an equilibrium head change decaying with distance from its source. The scrape drain is a dipole (local benefit at the slack inverting to neighbour drawdown) and the forest curves are canopy drawdowns, all decaying exponentially over λ ≈ 230 m. The two coastal-retreat curves decay linearly to zero at L ≈ 894 m, reusing Script 20's coastal-erosion construction exactly: a single Storm-Brendan-class 6 m event (edge drawdown = *COAST_RETREAT_M × δ₀ / COAST_RETREAT_RATE*) and a five-year accumulation of the fitted trend (edge = 5 × δ₀; the chronic rate cancels, so the curve is independent of the assumed chronic retreat rate). Two measured points are plotted as anchors (scrape BACI response; clearfell recovery); the standing-pine curve begins at the modelled canopy deficit (H₀ ≈ 150 mm), which exceeds the measured clearfell recovery (≈120 mm) because felling recovers most but not all of the modelled deficit.

### []{#anchor-435}[]{#anchor-436}[]{#anchor-437}Site-specific choices

-   **Five years, not a decade, for the chronic accumulation curve.** The five-year horizon keeps the amplitude (≈−145 mm) on the same continuous axis as the other curves without requiring a broken axis, and is a less speculative projection than a decade.
-   **Linear-capped coastal decay form.** The coastal curves use Script 20's linear-capped decay (its §4.8.2 fitted construction), not the drain-cone exponential, so the figure is internally consistent with the report's coastal gradient rather than reusing the drain law.

### []{#anchor-437}[]{#anchor-438}[]{#anchor-439}Two-pass execution and defaults

Script 09f runs in Phase 17 (step 47), after all its upstream scripts, so on a normal full-pipeline run every input already exists. On a partial or interrupted run each loader falls back to a documented Newborough-2026 default (centralised in *pipeline_params.\_DEFAULTS*, read via *default_value()*) with a console warning, mirroring the Script 09b/09d Sy-default precedent. Because the figure re-presents existing modelled fields and performs no new analysis, first-pass defaults do not affect any analytical result.

### []{#anchor-439}[]{#anchor-440}[]{#anchor-441}Outputs

  ----------------------------------- ----------------------------------------------------------------------------------- ------------------
  Output                              Description                                                                         Reference
  09f_management_effects.png          Spatial-reach synthesis figure (all interventions vs coastal retreat on one axis)   §5.8
  09f_management_effects_public.png   Public/academic-summary version (*\--public* flag)                                  Academic summary
  09f_01_reach_profile.csv            All curve profiles tabulated for traceability                                       Provenance
  ----------------------------------- ----------------------------------------------------------------------------------- ------------------

The figure caption is supplied in the report and summary document text, not baked into the figure.

### []{#anchor-441}[]{#anchor-442}[]{#anchor-443}Limitations

Every curve is a single-mechanism steady-state construction anchored at only one or two measured points; the five-year coastal curve is a forward projection of the fitted coast-edge retreat trend, not an observation; and the propagation timescales are multi-year to multi-decadal, so none of these fields is resolvable within the 31-month monitoring record.

### []{#anchor-443}[]{#anchor-444}[]{#anchor-445}Cross-references

-   **§S.15** --- Script 25 produces *25_01_panel_fit_parameters.csv* (δ₀, L) consumed live here.
-   **§S.13** --- Script 20 produces *20_report_numbers.csv* (λ, H₀) and the *\_scrape_field()* construction reused here.
-   **§S.6/§S.7** --- Scripts 09d and 10a supply the two measured anchor points.
-   **§5.8 of the main report** --- the primary destination for *09f_management_effects.png*.

## []{#anchor-445}[]{#anchor-446}[]{#anchor-447}S.15d Script 09g --- Mechanism diagrams (§5.8 schematic figure)

**Step 48/50, Phase 17. Display/utility (***tier=\"D\"***); not analytical. Added 2026-07-18 (***run_analysis.py*\*\* v2.2.0). Reads only committed outputs of Scripts 09f, 10m and 10a; no recomputation.\*\*

### []{#anchor-448}[]{#anchor-449}[]{#anchor-450}Motivation

Script 09f (§S.15c) places the management interventions and the coastal retreat on one quantitative spatial axis; §5.8 of the report also needs the *mechanisms* behind those numbers in a form a non-specialist reader can follow --- how a standing pine canopy suppresses the water table beneath and beside it, why a scrape pools where it is cut while drawing down the slack off the cut, why coastal retreat steepens the seaward water table while climate decline lowers it everywhere at once. Script 09g renders that argument as a single combined schematic grid: two starting states (wet dune with slacks; the same reach under standing forest), the two interventions (scrape; clearfell), and a full-width coastal-vs-climate panel along a continuous 900 m reach. A standalone version of the reach panel is emitted alongside the grid.

### []{#anchor-450}[]{#anchor-451}[]{#anchor-452}Inputs

All physical amplitudes are read live from committed pipeline outputs --- the script contains no hardcoded magnitudes:

  -------------------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Input file                                   Description
  *09f_01_reach_profile.csv* (Script 09f)      One edge amplitude per driver (row 0: forest standing, thinned, scrape cut rise, coastal 5-yr and single-storm, climate 20-yr) and the full 0--900 m reach columns (coastal 5-yr, single-storm and climate profiles)
  *10m_report_numbers.csv* (Script 10 suite)   *WMC3_BACI_DiD_step_2015_scraping* --- the one measured off-cut scrape drawdown
  *10a_report_numbers.csv* (Script 10 suite)   Clearfell BACI annual and summer steps with their significance strings, carried as the grid's clearfell magnitude note
  -------------------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Figure-design geometry (the shared cross-section profile, the 0.10 px/mm amplitude scale shared with 09f, retreat-state shorelines, erosion-ghosting fractions, the reach's inland dune body) comes from *config.py* (*MECH_FIG\_\**). Remaining per-mechanism drawing coordinates are named module constants in *utils/mechanism_fig_utils.py* --- internal drawing coordinates of the figure, not scientific parameters.

### []{#anchor-452}[]{#anchor-453}[]{#anchor-454}Methodology

A chained short-Dupuit-segment solver (developed and locked on the coastal figure) draws every water table on a shared schematic cross-section: within each flooded slack the table is pinned at the pond surface; between pinned levels it follows short Dupuit segments; slacks whose floor sits above the table are drawn dry. Per-mechanism builders add mechanism-specific geometry on top: canopy suppression bands and tree symbols (forest/clearfell), the excavated slack with its pool at the seaward-slack level and the measured off-cut drawdown (scrape), progressive shoreline-retreat states with eroded-dune ghosting (coastal), and a uniform lowering with pond-only refill (climate). All panels share one amplitude scale, so equal vertical distances mean equal head changes across the whole grid.

The coastal-vs-climate reach panel joins the schematic near-shore cross-section (0--330 m of the reach scale) to a data-drawn inland continuation (330--900 m) on one continuous distance axis. The three near-shore retreat parabolas are anchored at the 330 m boundary to the same committed drawdowns the inland side plots, so every curve is exactly continuous at the join (verified to 0.00 px by the script's console checks); the single-storm and 5-yr curves continue inland along their committed CSV profiles, and the 20-yr coastal curve is the 5-yr profile scaled by the horizon ratio (*MECHANISM_HORIZON_YEARS / COAST_CHRONIC_YEARS*). The flat climate line is the committed 20-yr climate amplitude, and the crossing distance --- where the coastal and climate profiles are equal, beyond which climate is the deeper driver (≈ 697 m on current committed data) --- is derived from the CSV columns at run time, never typed.

### []{#anchor-454}[]{#anchor-455}[]{#anchor-456}Site-specific choices and rationale

-   **Scrape physics follows ***SCRAPING_EFFECTS_KNOWLEDGE.md***:** the pool sits at the seaward-slack level (a high-permeability connection, not an impermeable basin); the off-cut drawdown is drawn as the single measured WMC3 point; no smooth network-wide drawdown cone is depicted, consistent with the Script 09b distance-decay null (§S.6).
-   **The clearfell magnitude line quotes the live Script 10a BACI steps** with their significance strings, so the schematic cannot come adrift from the headline result when the pipeline reruns.
-   **The coastal grid cell keeps schematic retreat-curve anchors** while the reach panel is data-anchored: the cell has no distance scale to be continuous with, and legible separation of the three retreat states is the cell's purpose (decision 2026-07-18; the data-derived anchors differ by 1.4--2.8 px and compress the storm curve without adding information the reach panel does not already carry).
-   **Captions are supplied in the document text**, not baked into the figures, and must describe the figures as schematic, vertically exaggerated, and not to scale.

### []{#anchor-456}[]{#anchor-457}[]{#anchor-458}Two-pass execution and defaults

Script 09g runs at the end of Phase 17 (step 48), after 09f, so on a normal full run every input exists. On a partial or interrupted run each loader falls back to a documented default in *pipeline_params.\_DEFAULTS* (read via *default_value()*) with a console warning --- the Script 09b/09d/09f precedent. The reach fallback is reconstructed from the documented Script 25 fit defaults (δ₀, L, c), not duplicated literals. Because the figures re-present existing modelled and measured fields, first-pass defaults affect no analytical result. As a final step Script 09g also renders two lay public-summary figures through *gen_grid_lay.render_all()* --- plain-language before/after diagrams built on the same committed geometry --- so the technical and lay figures cannot drift apart; *gen_grid_lay.py* is a public-summary asset and is not itself a registered pipeline step.

### []{#anchor-458}[]{#anchor-459}[]{#anchor-460}Outputs

  --------------------------------------------- -------------------------------------------------------------------------------------------------- --------------------------------
  Output                                        Description                                                                                        Reference
  *09g_mechanism_grid.svg* / *.png*             Combined mechanism grid: starting states, scrape, clearfell, full-width coastal-vs-climate reach   §5.8
  *09g_coastal_vs_climate_reach.svg* / *.png*   Standalone coastal-vs-climate reach figure                                                         §5.8 (optional standalone use)
  *09g_mechanism_lay_management.svg* / *.png*   Lay before/after figure: undisturbed → scrape, forest → clearfell (public summary)                 Public summary
  *09g_mechanism_lay_drivers.svg* / *.png*      Lay before/after figure: undisturbed → coastal, undisturbed → climate (public summary)             Public summary
  --------------------------------------------- -------------------------------------------------------------------------------------------------- --------------------------------

### []{#anchor-460}[]{#anchor-461}[]{#anchor-462}Limitations and known caveats

-   **Schematic, not to scale.** Vertical amplitudes share one exaggerated scale; the cross-section topography is illustrative. No distance, depth or volume should be read off the grid panels; only the reach panel carries a real distance axis, and even there the terrain is schematic.
-   **No new analysis.** Every magnitude is a re-presentation of a committed upstream value; the script fits nothing and its outputs must never be cited as evidence independent of their Script 09f/10a/10m sources.
-   **The drawn off-cut drawdown is the measured WMC3 point applied schematically** to the inland slack; its spatial extent is not resolved by the network (the §S.6 distance-decay null) and the drawing does not claim otherwise.
-   **The lay figures are register-shifted, not re-analysed.** *09g_mechanism_lay\_\** carry the same mechanisms and directions as the technical grid but with rounded plain-language annotations and no well names, p-values, or script references, and the modelled coastal driver is flagged in plain words as "expected, not yet directly measured". A build-time glyph guard rejects any drawn character outside the base sans font, guarding the Welsh and Polish rebuilds against missing-glyph boxes.

### []{#anchor-462}[]{#anchor-463}[]{#anchor-464}Where the result appears

The combined grid is the §5.8 conceptual figure of the main report (figure number assigned at placement). The standalone reach figure is available for the public summaries and presentations. Companion chapters: §S.15c (Script 09f, the quantitative reach), §S.6 and §S.7 (the scraping and clearfell analyses whose results the schematic re-presents), §S.15 (Script 25, source of the coastal-gradient parameters).

## []{#anchor-464}[]{#anchor-465}[]{#anchor-466}S.16 Scripts 22, 23, 24 --- Residual diagnostics

**Steps 27--29/50 in the orchestrator (Phase 12 --- Residual Diagnostics in ***run_analysis.py***); analytical tier; second chapter under Phase 5 --- Post-pipeline supplementary analyses in the supplement.**

### []{#anchor-466}[]{#anchor-467}[]{#anchor-468}Motivation

Earlier revisions of the main report framed the spatial pattern of the SSM water-balance residual as ridge-derived recharge: wells along the northern bedrock ridge flank, with CEH14 as the canonical example, were reported as carrying persistent positive residuals that the three-term SSM did not represent. *That pattern is not present in the corrected residual field.* The correction (Script 20, 2026-08-06; §4.9.7, Figure 58, see S.13) removed the observation the framing rested on: sixty-four of the sixty-six reference wells now fall within ±0.01 m/month, residual magnitude is uncorrelated with position on either axis, no well exceeds +0.02 m/month, and the largest positive residuals sit in the open dune rather than at the ridge margin. At the network scale the balance closes without requiring an additional flux, and there is no forest-margin band for a lateral subsidy to explain.

One qualification attaches to CEH14 itself. The well --- the most ridge-proximal in the network --- carries the second most negative residual at −0.011 m/month, the most negative being the open-dune well D7. That value cannot be read as evidence against a lateral input at this well, because β₃ enters the residual expression directly: the well's anomalous negative drainage coefficient drives its own residual negative by construction. Substituting the C4 median β₃ and leaving every other term at CEH14's own fitted values returns a residual of approximately +0.09 m/month, an order of magnitude above any value in the network. The residual field is therefore a network-level result. It does not adjudicate the two wells (CEH14 and CEH13) whose β₃ is itself anomalous, and ridge-derived recharge --- raised in earlier work on this site --- remains an open candidate at CEH14 specifically, neither supported nor excluded by this diagnostic.

Scripts 22, 23 and 24 were built as the analytical apparatus that subjected the ridge-recharge interpretation to mechanistic testing. Their results stand and nothing here is recomputed; what changes is what they are for. They are retained as a bound on what a 21-year monthly record could have detected, in a network whose water balance closes without an additional flux. They share a single source --- the SSM residual series e(t) at each well --- and ask three complementary questions about that series. Script 22 characterises the residual: how time-structured is it well-by-well, and do the wells with the largest mean residuals (the intercept α from Model B) also have the most autocorrelated residuals? Script 23 puts the residual to a physical test: if it carries genuine ridge-to-well travel time, the cross-correlation peak lag against rainfall should increase with distance from the ridge. Script 24 asks the alternative-hypothesis question: does the residual carry a seasonal signature consistent with the Thornthwaite PET estimate misrepresenting summer demand, or is the seasonal structure flat (consistent with steady ridge baseflow), or something else again? Together the three diagnostics constrain what the residual can and cannot be, and in doing so establish the limits of what this monitoring design could have resolved had a lateral flux been present.

### []{#anchor-468}[]{#anchor-469}[]{#anchor-470}Inputs

  ------------------------ --------------------------------------------------- ------------
  Input file               Source                                              Used by
  01_wells_clean.csv       Script 01 --- cleaned wide well-level matrix        22, 23, 24
  01_climate.csv           Script 01 --- monthly P_m and PET                   22, 23, 24
  01_locations.csv         Script 01 --- well coordinates (E, N, OSGB36)       22, 23, 24
  02_clusters.csv          Script 02 --- cluster ID per well (k=5 partition)   22, 23, 24
  RAF_Valley_Climate.csv   raw data input --- monthly sunshine hours           24 only
  ------------------------ --------------------------------------------------- ------------

Sunshine hours are loaded from the raw RAF Valley climate CSV directly (*DATA_CLIMATE_RAW*) rather than from a pipeline intermediate. The pipeline's *01_climate.csv* carries P and PET only --- sunshine hours are not used anywhere else in the pipeline and so were not propagated into the cleaned climate file. Script 24 parses the original *MMM YY* date format (e.g. "Jan 25" = January 2025) directly from the raw file.

### []{#anchor-470}[]{#anchor-471}[]{#anchor-472}Methodology --- Script 22 (residual lag analysis)

Script 22 refits Model B --- the SSM with a constant intercept --- on the full record under the shared residual-diagnostic floor (RESIDUAL_DIAG_MIN_MONTHS, config.py), on the full record rather than the 100-month recent window used by Script 07. The model is the canonical displacement-formulation SSM with an additive constant:

> Δh(t) = α + β₁·P(t) − β₂·PET(t) − β₃·(z₀ + h(t−1))

The fit is performed via the shared *fit_ssm_intercept()* in *model_utils.py* (see F.5), with *HEADLINE_LAG = 0* from *config.py*. The intercept α absorbs whatever constant part the unmodelled hydrological inputs carry; the residual series e(t) = Δh_observed − Δh_predicted then represents only the *time-varying* component of the unmodelled contribution. This decomposition is methodologically important. If the residual at a ridge-adjacent well averages, say, +0.030 m/month, that constant offset is by construction absorbed into α --- it cannot also show up in e(t). Any signal that e(t) carries must therefore vary in time, which is the only kind of signal that can carry a lag structure against rainfall.

Choosing the full record over the per-well 100-month window (fitted in Script 03, mapped by Script 07) is deliberate: lag analysis at the monthly timestep needs as many degrees of freedom as the record will allow, and rolling-window stability of the lag signal (a stage 3 analysis not implemented in Script 22 itself) requires that windows of different lengths be available. The trade-off is that Model B's β fits in this script are full-record averages, whereas the main report's Figure 48b uses the recent 100-month window (Table 3's cluster coefficients are full-record centroid fits). The two should be similar but will not be identical --- Script 22 is an analytical companion, not a replacement for the headline fits.

For each well's residual series, Script 22 then computes an AR(1) diagnostic: it regresses e(t) on e(t−1) via OLS and reports the AR(1) coefficient φ, its p-value, and the residual standard deviation. The decision criterion *AR1_WHITE_THRESHOLD = 0.3* flags wells whose residuals are sufficiently autocorrelated that pre-whitening would be required before any cross-correlation analysis. A second diagnostic --- the α-vs-φ scatter --- tests whether the wells with the largest persistent subsidies (high α) are also the wells with the most time-structured residuals (high \|φ\|). If both conditions held, the unmodelled input would be both high in magnitude and variable in time, the physical signature expected from a sustained lateral flux that itself responds to seasonal or interannual climate.

The Script 22 outputs are eight files: a wide residuals CSV (rows = months, columns = wells, values = e(t)), a per-well fits table with α, β₁, β₂, β₃, R², AR(1) statistics, mean and standard deviation of the residual, the per-well headline-SSM residual-inference table *22_05_ssm_residual_autocorrelation.csv* and the cluster-mean counterpart *22_06_ssm_cluster_mean_inference.csv* (both see below), and four figures --- an AR(1) histogram by cluster, a spatial map of AR(1) coefficient, the α-vs-φ scatter, and example residual time series for one well per cluster (chosen as the longest-record well with a valid AR(1) fit).

### []{#anchor-472}[]{#anchor-473}[]{#anchor-474}Methodology --- Script 22 (headline-SSM residual inference)

Alongside the Model B AR(1) apparatus above, Script 22 (v1.2.0) carries a second, independent diagnostic addressing a distinct question: are the classical-OLS standard errors that produce the headline coefficient p-values valid under residual serial correlation? This is a fair question for any monthly time-series regression, and a sharper one here because the drainage term −β₃·(z₀ + h(t−1)) makes the SSM a dynamic (lagged-level) model. The diagnostic refits the headline no-intercept (Model A) SSM --- ground-referenced, full record, the specification behind the published coefficient table --- at each of the 66 reference-network wells and interrogates the residuals.

Two findings. First, the residuals are close to white with a slight *negative* first-order autocorrelation: median Durbin--Watson 2.20 (IQR 2.11--2.37), median lag-1 φ = −0.12. The negative sign is the error-correction drainage term at work --- it absorbs the first-order persistence of the level series --- so the OLS standard errors are mildly conservative, not anti-conservative. A Ljung--Box test at lag 12 rejects white noise at 19 of 62 wells, but that is the seasonal residual structure Script 24 (§S.16, below) analyses, not low-order persistence, and it is orthogonal to the coefficient standard errors. Second, re-estimating the coefficient p-values with heteroskedasticity- and autocorrelation-consistent (Newey--West / HAC) standard errors --- n-adaptive rule-of-thumb truncation lag L = ⌊4·(n/100)\^(2/9)⌋ --- leaves the significance verdicts (α = 0.05) unchanged in 185 of the 186 coefficient tests (62 wells × three coefficients). The single change is β₂ at CEH25, moving from p = 0.083 to p = 0.030, i.e. *toward* significance, so no coefficient that OLS reports as significant is overturned. The classical-OLS inference underlying the coefficient tables is therefore sound.

The check runs at two levels. At the per-well level (the noisier fit), the diagnostics are written to *22_residual_lag_analysis/22_05_ssm_residual_autocorrelation.csv*. A companion routine applies the same battery to the five cluster centroids that carry the headline β table (Report Table 3; *outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv*) --- rebuilt exactly as Script 03 builds them, so the centroid β and OLS p-values reproduce the published table to full precision --- and writes *22_residual_lag_analysis/22_06_ssm_cluster_mean_inference.csv*. At the cluster-mean level none of the fifteen coefficient tests (five clusters × three) changes significance under HAC; the centroid residuals are near-white (Durbin--Watson 2.0--2.4) at every cluster except C4 Main Forest, where a mild positive autocorrelation (DW 1.83) still leaves all three coefficients HAC-significant. Together, the two levels are the committed backing for the bootstrap section's statement that the per-well CI question is already answered by the OLS p-values.

### []{#anchor-474}[]{#anchor-475}[]{#anchor-476}Methodology --- Script 23 (ridge recharge lag test)

Script 23 is the principal mechanistic test of the hypothesis. The physical reasoning is straightforward: if the water-balance residual were to reflect genuine lateral recharge from the northern rock ridge, then water arriving at any given well had to travel from the ridge to that well. That travel has a time, and that time must increase with distance from the ridge. The cross-correlation peak lag between the residual series and rainfall --- at what lag does the residual best correlate with past rainfall? --- should therefore increase systematically with distance from a fixed ridge reference point.

The methodological subtlety is what Script 22's diagnostic implies for the test design. A single-period SSM leaves any rainfall response that takes more than one month to propagate through the vadose zone in the residual. At the monthly timestep this generic vadose-zone lag is non-negligible: at every well across the network, e(t) will correlate to some extent with P(t−1). This generic signal would dominate any ridge-specific structure if the test were run on the Model B residuals directly. Script 23 deals with this by fitting an *extended* model that includes both contemporaneous and lag-1 rainfall:

> Δh(t) = α + β₁₀·P(t) + β₁₁·P(t−1) − β₂·PET(t) − β₃·(z₀ + h(t−1))

The β₁₁·P(t−1) term absorbs the generic monthly-timescale vadose-zone response. The residual from this extended model is, by construction, free of the generic lag-1 confound, and any remaining lag structure against rainfall is the candidate ridge signal. (A current design note in the docstring records that, with *HEADLINE_LAG* now configurable, the two-month spanning window of P(t)+P(t−1) is retained pending a scientific review of whether the same absorb-the-generic-lag purpose could be achieved with an alternative shift.) The β₂ and β₃ from this fit are not propagated back to any pipeline output --- Script 23 is a diagnostic refit, and the canonical β values in *03_master_data.csv* remain authoritative.

The ridge reference point is fixed at E = 241750, N = 364500 (OSGB36) --- the northern rock-ridge centroid as estimated from the site DEM and the ridge KML overlay. Distance from the ridge to each well is computed as Euclidean distance in OSGB36 metres. A coordinate-validity filter (*MAX_RIDGE_DISTANCE_M = 3000* m) discards any well whose ridge distance exceeds 3 km, which removes records carrying garbage coordinates (the location CSV contains some non-well rows with placeholder coordinates 300+ km from the site) without affecting any real Newborough well --- the most distant real well sits at roughly 2 km from the reference point.

For each well, Script 23 then computes the cross-correlation between the extended-model residual and rainfall at lags 0 to 12 months. Both series are pre-whitened before the CCF is computed: rainfall is pre-whitened once globally using its own AR(1) coefficient, and any residual series whose AR(1) coefficient exceeds \|0.2\| is additionally pre-whitened to remove its own autocorrelation. The peak-correlation lag N\* is the lag at which \|r\| is largest. Bartlett's 95 % confidence threshold is computed per-well as 1.96/√n_eff where n_eff is the smallest sample size across the computed lags; wells whose peak \|r\| falls below this threshold are classified as not showing a significant peak.

The hypothesis test itself is a Spearman rank correlation of peak lag against ridge distance, restricted to wells with a significant peak. The choice of Spearman rather than Pearson reflects the nature of the prediction: the physical theory predicts monotone increase, not linear proportionality, and the lag axis is discrete (integer months) rather than continuous. The verdict at the bottom of the summary is recorded in three branches: H1 supported (positive ρ, p \< 0.05), an unexpected-direction outcome (negative ρ, p \< 0.05), and H0 not rejected. The third branch carries the methodological caveat that a null result does not by itself rule out steady ridge baseflow --- a constant subsidy that is effectively smoothed in time by the time it reaches the dune field would be observationally indistinguishable from the constant α that Model B already absorbs.

**A structural caveat on the test design.** Investigation of Script 23 in May 2026 established that the test as constructed cannot resolve the mechanism it is designed to detect, for three structural reasons: (a) monthly time resolution against a \~2 km transect collapses the expected lag range onto a 2--3 month discrete grid, leaving only a handful of distinguishable lag values across the network's distance range; (b) peak-lag is a poor cross-correlation summary, discarding amplitude and shape information that would carry the lateral-flux signature if it were present; (c) the residual signal the mechanism would explain is approximately 2.5 % of annual flux, at or below the per-well intercept α uncertainty in the headline SSM; and (d) a methodological floor at short lags --- OLS residuals are orthogonal to the fitted rainfall regressors at lags 0 and 1 by construction, so the peak-lag statistic is partly determined by the fitting procedure rather than by hydrology. The consequence of (d) is that the observed concentration of peak lags at 2 months (42 of the 50 significant-peak wells) should not be read as a travel-time observation at all; 47 of the 63 wells peak at lag 1 or 2 irrespective of ridge distance, a pattern that persists under a Box-Jenkins pre-whitened reformulation. A reframed α-geography test was also explored --- correlating per-well α against ridge distance and against elevation --- and was inconclusive due to physical collinearity between elevation and ridge distance: the ridge *is* the high ground, so any elevation-related residual structure is partly indistinguishable from a ridge-distance-related one. The script is retained in the pipeline as documentation of the analysis attempted; its null result should not be interpreted as evidence against ridge recharge, only as evidence that the present monitoring design cannot resolve the question. Sub-monthly water-level monitoring at the ridge-adjacent wells, paired with rainfall at the same resolution, would be the design needed to test the mechanism cleanly; that data does not exist at this site for the analysis period.

### []{#anchor-476}[]{#anchor-477}[]{#anchor-478}Methodology --- Script 24 (residual seasonality)

Script 24 is the third diagnostic. It refits Model B via *fit_ssm_intercept()* for every well (so the residuals are directly comparable with Script 22's), and asks whether those residuals carry a systematic seasonal signature. Two physically distinct hypotheses produce contrasting predictions. If Thornthwaite PET --- computed from temperature only --- underestimates true summer atmospheric demand by some proportion, the residual should be systematically negative in summer (JJA) and approximately zero in winter (DJF), with a sinusoidal climatology peaking near the temperature low. If the unmodelled input is instead a flat year-round ridge baseflow, the climatology should be approximately flat across all months at a constant positive offset --- and that offset is, again, already absorbed into α, leaving the climatology of e(t) close to zero everywhere.

The diagnostic computes a monthly climatology per well --- the mean of e(t) across all instances of each calendar month --- and fits a single-harmonic sinusoid to the twelve monthly means:

> ē(m) = a₀ + a₁·cos(2π·m/12) + a₂·sin(2π·m/12)

The fitted offset (a₀), amplitude (√(a₁² + a₂²)), and phase (the calendar month at which the sinusoid peaks) summarize each well's seasonal residual structure. The winter-minus-summer contrast (mean of DJF months minus mean of JJA months) is reported alongside as a model-free check. The convention matches Paper 1 and the main report's residual-field discussion, and matches the cluster-stratified diagnostic introduced below.

The chapter-defining methodological detail is the sunshine-hours correlation. A naïve correlation of e(t) against PET would be zero by construction --- OLS makes residuals orthogonal to every regressor, so any test that uses PET as the seasonality proxy is testing nothing. To test whether real ET departs from the Thornthwaite estimate in a way that the fitted β₂ has not absorbed, Script 24 correlates e(t) against monthly *sunshine hours* --- an independent radiation-based ET proxy that is not in the regression. A systematic negative correlation across the network would indicate that high-insolation months carry extra ET losses that the temperature-only Thornthwaite estimate has not captured and that β₂ has therefore not been able to fit. A network-wide null result (correlations scattered within Bartlett bands) is direct evidence that Thornthwaite's seasonal bias, whatever it is, has been absorbed by β₂ and is not what the residual is reflecting.

A C3 split diagnostic --- partitioning the Western Residual cluster by ridge distance at 1000 m --- is retained as a within-cluster check that the seasonal amplitude is not systematically different in the forest-adjacent subset versus the warren interior. The 1000 m threshold is a legacy parameter from the k=4 partition era, where the C3 cluster contained both forest-adjacent and interior wells; under the k=5 partition the forest-adjacent subset of the old C3 has been split out as C5 (Coastal Forest), and the diagnostic is now an *intra*-C3 robustness check rather than an across-cluster comparison.

The phase analysis uses a circular mean rather than an arithmetic mean to handle the December/January wrap correctly, and is plotted on a hydrological-year axis (September → August) to make the winter--early-spring versus summer signal easier to read off.

### []{#anchor-478}[]{#anchor-479}[]{#anchor-480}Diagnostic --- cluster-stratified residual climatology (Script 24b, non-pipeline)

Script 24b (*24b_residual_climatology.py*) is step 42/50 in the orchestrated pipeline, wired into Phase 16 alongside Scripts 31, 31b, 34, and 38 (§S.21). It runs after the canonical residual-diagnostics suite (Scripts 22--24) and reads their committed outputs. Its purpose is to ask whether the seasonal residual signature uncovered by Script 24 carries any cluster-level structure that would discriminate between candidate mechanisms --- in particular, whether the winter-spring residual is concentrated in the forested clusters (as a canopy-interception over-estimation would predict) or in the open-dune cluster (as a recharge-nonlinearity would predict). Full documentation is in §S.21.1.

The method reads Script 22's per-well residuals *e(t)* directly --- there is no SSM re-fit, so the diagnostic inherits whatever the canonical Model B has fitted at each well. For every well meeting Script 22's 140-month minimum, it computes a per-well *winter-minus-summer contrast* defined as the mean of e(t) across all calendar DJF months (December, January, February) minus the mean across all calendar JJA months (June, July, August). The five clusters are then aggregated by a well-level bootstrap with 1000 resamples within each cluster, producing a cluster-mean contrast, a 95 % confidence interval on the cluster mean, and a two-sided one-sample *t*-test of the cluster mean against zero. Per-well distance-to-ridge and a signed distance-to-forest-edge are attached as covariates --- the forest-edge geometry comes from the "Forest" polygon in *Features.kml*, reprojected to OSGB36 / EPSG:27700, with positive values denoting wells inside the forest and negative values denoting wells outside. The ridge reference point is defined locally in the diagnostic, mirroring Script 24's coordinates, so the script can run standalone against a clean *main* with no shared-file edits.

The cluster-stratified result (k = 5 partition, current *22_residuals_wide.csv*):

  --------------------- --------------- ---------- ---------------------------------------------------------
  Cluster               Contrast (mm)   p          Interpretation
  C3 Western Residual   +7.5            \< 0.001   Substantive positive contrast
  C4 Main Forest        +6.4            0.086      Marginal positive contrast
  C1 Lake Edge          +7.3            0.198      Magnitude similar to C3 but small *n* and high variance
  C2 Dune               +3.4            0.152      Small positive contrast, not significant
  C5 Coastal Forest     −2.8            0.138      Small negative contrast, not significant
  --------------------- --------------- ---------- ---------------------------------------------------------

Within the 14 forest wells (C4 ∪ C5), the contrast strengthens toward the ridge: regressing per-well contrast against ridge distance gives Pearson r = −0.63, n = 14 --- wells closer to the ridge carry larger winter-minus-summer residuals.

The result is conservative against a canopy-interception over-estimation. If the F = 0.24 Freeman interception fraction were too large, the over-correction would concentrate the winter residual in the forested clusters (C4 and C5), because that is where the correction is applied. Instead, the largest contrast sits in C3 --- an unforested cluster --- and the C3 \> C4 \> C5 ordering places the smallest contrast in C5, which is the most ridge-distant of the two forest clusters. Canopy-interception miscalibration cannot account for that ordering; the diagnostic provides no data-driven case to revise F = 0.24. The within-forest gradient toward the ridge is consistent with a ridge-derived component but, on its own, cannot be separated from a site-wide recharge nonlinearity --- the C3 result demonstrates that the same winter-spring excess exists where there is no canopy and no immediate ridge proximity.

Taken with Script 24's network-wide null on the sunshine-hours correlation, this places the seasonal residual signature as consistent with a winter-phased recharge mechanism rather than with either a Thornthwaite PET misspecification or a canopy-interception parameterization error. The mechanistic attribution beyond that --- separating ridge-derived from site-wide winter recharge --- is left to future work, since the present monitoring resolution at monthly time-steps and \~2 km transect cannot discriminate cleanly between candidates that respond at similar bandwidths. Paper 1 §5.4 and SI S9.3 carry the same finding under the same terminology; this diagnostic is the methodological back-reference for those claims.

The diagnostic emits three CSVs (per-well contrasts with covariates; cluster bootstrap summary; forest-only gradient regression), a single 3×2 PNG panel figure (per-cluster contrast distributions, the spatial map of per-well contrasts, the forest-only contrast-vs-ridge-distance scatter with regression line, the per-cluster bootstrap CI bars, the per-cluster boxplots, and a forest-edge-signed-distance panel), and a plain-text interpretation file. Outputs are listed below in the chapter's *Outputs* table under the "Script 24b --- cluster-stratified residual climatology" group; full documentation is in §S.21.1.

### []{#anchor-480}[]{#anchor-481}[]{#anchor-482}Site-specific choices

-   **Full record vs the per-well 100-month window.** Scripts 22 and 24 use the full per-well record to maximize statistical power for the lag and seasonality analyses, which need as many monthly observations as possible. The trade-off is that the Model B fits here are not identical to the main report's per-well coefficient figures. The per-well coefficients in 03_master_data.csv remain the 100-month-window fits, and the report's headline cluster coefficients (Table 3) are full-record centroid fits; Scripts 22, 23, 24 are diagnostic companions, not revisions.
-   \**140-month minimum record (*RESIDUAL_DIAG_MIN_MONTHS = 140*, config.py).*\* Roughly 11.7 years of continuous data; in practice the binding minimum among eligible wells is 151 months, so the floor drops only ceh40, ceh41 and ceh42. Wells with fewer observations are dropped from Scripts 23 and 24. This excludes shorter-record monitoring points without compromising the Bartlett confidence threshold calculation, which becomes unreliable below 100 monthly observations.
-   **Common exclusion set (***RESIDUAL_DIAG_EXCLUDED_WELLS = {ceh3, ceh4, ceh7, ceh8, ceh37, llynrhos}***, config.py).** CEH7, CEH8 and CEH37 carry over the upstream exclusions from Script 07. CEH3 sits at the tidal boundary and is outside the SSM's operational domain (report §S4.4.2). CEH4 carries both a coastal-erosion drift and a post-2017 clearfell drawdown pulse (S.7); both confound any lag or seasonality signal. Llyn Rhos-Ddu is a surface-water level gauge rather than one of the 88 classified dipwells, so it carries no water-balance residual in the SSM sense; it was excluded from Scripts 23 and 24 in August 2026. The set is shared across Scripts 22, 23 and 24 so that the three diagnostics describe a coherent well population. Script 22's residual-inference table runs the reference network under these rules and carries 62 wells; Scripts 23 and 24 read the cleaned table and carry 63, the difference being ceh22, a classified dipwell that sits outside the 66-well reference partition.
-   **Ridge reference point (E = 241750, N = 364500).** Estimated from the site DEM and the ridge KML feature. The point sits on the bedrock ridge crest at the northern site boundary, approximately equidistant from the eastern and western extents of the ridge feature. The diagnostic is not sensitive to small displacements of this point along the ridge axis --- what matters is the *gradient* of distance across the well network, which is dominated by the perpendicular distance from the ridge axis.
-   **MAX_RIDGE_DISTANCE_M = 3000 m.** A coordinate-validity filter, not a methodological exclusion. Real Newborough wells all sit within \~2 km of the ridge reference; anything beyond 3 km is a placeholder coordinate that the location CSV carries for non-well records.
-   **AR(1) pre-whitening with threshold \|φ\| ≥ 0.2 in Script 23.** A higher-order or non-parametric pre-whitening (e.g. ARMA-based or wavelet) could be defended; the AR(1) choice is what the standard CCF literature uses and is conservative against over-fitting at small effective sample size. The residual AR(1) coefficients across the network sit in a narrow band around −0.12 (see Script 22), so the additional pre-whitening rarely activates in practice.

### []{#anchor-482}[]{#anchor-483}[]{#anchor-484}Results to describe at the methodological level

Script 22's per-well AR(1) diagnostics show that the network's Model B residuals are close to white. Across the 62 wells with valid fits, the AR(1) coefficient sits at a small negative value at most wells (network mean φ ≈ −0.13, median ≈ −0.12), and only two wells exceed \|φ\| = 0.3. The α-vs-φ scatter shows essentially no relationship (Pearson r ≈ −0.08): wells with large persistent subsidies (high α) are not preferentially the wells with the most time-structured residuals. The constant part of the unmodelled input --- whatever it is --- sits in α, and the small remaining time-varying part is not strongly clustered in any particular well or cluster.

Script 23's hypothesis test returns a null result. With 50 of 63 wells showing a significant peak in the cross-correlation against rainfall, the Spearman rank correlation of peak lag against ridge distance is ρ = −0.005, p = 0.97. The mean peak lag (2.68 months across all significant wells) does not vary systematically with distance from the ridge. The cluster ordering of mean peak lag (C1, C2 = 2.00 months; C3 = 3.00; C4 = 3.67; C5 = 11.00, n = 1) does not parallel the ridge-distance ordering: C4 and C5 sit at the southern forest margin, not adjacent to the northern ridge. The b₁₀ / b₁₁ pattern by cluster shows a forest--dune contrast, but the parameterisation is not identified well enough to carry a physical reading on its own. The cluster-median lagged fraction b₁₁/(b₁₀+b₁₁) does rise from C1 −0.08 and C2 −0.03 through C3 +0.11 to C4 +0.28 and C5 +0.16, and the cluster-mean b₁₁ is 0.75 in C4 and 0.47 in C5. But b₁₁ is significant at only 26 of the 63 wells and negative at 32 of them, and a negative lagged-rainfall coefficient has no vadose interpretation; P(t−1) and the drainage regressor are collinear (mean correlation +0.234 across the network, range −0.102 to +0.532), so b₁₁ and β₃ compete for the same variance and b₁₁ is what survives after the drainage term takes its share. The vadose reading is nonetheless independently supported, and is better anchored on direct measurement than on this coefficient: Freeman (2008) measured forest soil moisture at roughly half the open Warren\'s (≈6.5 % against ≈17.7 %, ANOVA p \< 0.001) and the forest water table about 1.07 m deeper, a drier and thicker unsaturated zone that holds more of each rainfall pulse in transit and damps the water-table response. Either way the contrast is unrelated to ridge transport.

There is no longer a ridge-recharge interpretation for the Spearman test to corroborate or refute. Its value now is as a bound on the test design itself: as the structural caveat above records, the test as constructed could not have resolved the mechanism either way. The null is consistent with the residual being largely model error, with a near-steady baseflow observationally indistinguishable from the constant α that Model B already absorbs, and --- the reading that now leads --- with the design simply lacking the temporal resolution to detect a lag pattern had one been present. The main report (§5.2.1) treats the residual field as a model-adequacy diagnostic and advances no ridge contribution. Script 23\'s null documents the analytical attempt and the limit of what the present data can support; it is not positive evidence against a mechanism, and it is not evidence for one.

Script 24's seasonal diagnostic supports neither the Thornthwaite-PET-misspecification hypothesis nor the dominant-unmodelled-summer-ET interpretation. Across all 63 wells, no well's correlation between e(t) and sunshine hours exceeds the Bartlett threshold (\|r\| \< 0.15 at every well); the network mean is −0.03. The winter-minus-summer contrast at the cluster mean is small in magnitude across all clusters (between −0.003 and +0.007 m). The seasonal amplitude per well is small (cluster mean amplitudes between 0.009 and 0.015 m). What the diagnostic *does* find is a strong phase preference: 47 of 63 wells have their residual climatology peaking in the November--March window (winter to early spring), and zero wells peak in the May--August window. This is not the signature of unmodelled summer ET --- it is consistent with threshold or nonlinear recharge behaviour not captured by the linear β₁·P term: in mid-winter with saturated soils, rainfall reaches the water table with higher efficiency than the cluster-mean β₁ represents. The Thornthwaite-misspecification hypothesis can be set aside; what remains is a small but coherent winter-spring residual that is not ridge-related.

Taken together, the three diagnostics bound what the record could have shown. The spatial concentration of large residuals along the northern ridge flank, of which CEH14 was the canonical example, does not survive the Script 20 correction: the corrected field has no spatial structure on either axis, and CEH14 is its most negative well. Script 24 establishes that the residual does not carry a Thornthwaite-bias signature, ruling out the unmodelled-summer-ET interpretation. Script 23 establishes that no month-scale distance-dependent lag pattern is detectable --- but, as the structural caveat above records, the test design at monthly resolution cannot resolve a sub-monthly lag if one were present, and the residual amplitude itself sits at the noise floor of per-well α uncertainty. What survives across all three diagnostics is a residual that is (a) constant in time at the level the model can resolve, (b) absorbed into α at any well where it dominates, and (c) carries a small winter-spring recharge nonlinearity at the wider network. With the corrected field showing no spatial structure, model inadequacy distributed across the network is the parsimonious reading, and no additional flux is required to close the balance. Sub-monthly water-level monitoring at ridge-adjacent wells, paired with rainfall at the same resolution, would remain the design needed to establish whether a lateral flux exists at all.

### []{#anchor-484}[]{#anchor-485}[]{#anchor-486}Limitations

-   **Single-station climate.** The diagnostic relies on RAF Valley as the sole source for rainfall, PET, and sunshine hours. Any seasonal-bias diagnostic at the residual level is conditional on RAF Valley being representative; the chapter's null result on the Thornthwaite-misspecification hypothesis is therefore an absence of evidence given the available data, not a positive demonstration that Thornthwaite is well-specified at the dune-field scale.
-   **140-month threshold and cluster representation.** With the 140-month minimum and the six-well exclusion set, Scripts 23 and 24 carry 63 wells. C5 Coastal Forest is represented by five wells in Script 24 and only one in the Script 23 significant-peak population --- too few to make a within-C5 statement. The cluster-mean lag and amplitude figures should be read with this n in mind.
-   **Spatial sparsity for the distance-lag test.** The 51 significant-peak wells in Script 23 span a ridge-distance range of roughly 270 to 2000 m, distributed unevenly across the gradient. The test has reasonable power to detect a strong monotone trend; it would be less reliable against a weak trend, and a non-rejection here is not the same as a precise estimate that the slope is zero.
-   **AR(1) pre-whitening.** Higher-order or non-parametric whitening could in principle reveal lag structure that AR(1) does not remove. The residual AR(1) magnitudes are small enough (most wells \|φ\| \< 0.2) that this is not a likely confound, but the choice is principled rather than verified.
-   **Lag-extended SSM in Script 23 vs canonical Model B.** Script 23's extended model differs from the canonical SSM in including P(t−1) as a second rainfall regressor. The β₂ and β₃ from this fit are not propagated downstream, and the canonical β values in *03_master_data.csv* remain the report's source of truth.

### []{#anchor-486}[]{#anchor-487}[]{#anchor-488}Outputs

  ----------------------------------------------------------------- ----------------------------------------------------------------------------------------- ------------------------------------------------------
  Output                                                            Description                                                                               Reference
  22_residuals_wide.csv                                             Wide Model B residuals, rows = months, columns = wells                                    Stage 2/3 lag analyses (planned); cross-script reuse
  22_model_b_fits.csv                                               Per-well Model B fits: α, β₁, β₂, β₃, R², AR(1) φ, p, σ                                   Script 22 plots; cross-script reuse
  22_residual_lag_analysis/22_01_ar1_histogram.png                  AR(1) coefficient histogram by cluster                                                    §S6 supplementary note
  22_residual_lag_analysis/22_02_ar1_spatial_map.png                Spatial map of AR(1) coefficient per well                                                 §S6 supplementary note
  22_residual_lag_analysis/22_03_alpha_phi_scatter.png              α vs AR(1) φ scatter, coloured by cluster                                                 §S6 supplementary note
  22_residual_lag_analysis/22_04_example_residuals_by_cluster.png   Example e(t) time series, one well per cluster                                            §S6 supplementary note
  23_residuals_extended_wide.csv                                    Wide extended-model residuals (after P(t)+P(t−1) fit)                                     Reserved for stage 3
  23_ridge_lag_fits.csv                                             Per-well extended-model fits, ridge distance, peak lag, peak r, significance              Script 23 plots; §5.3
  23_ridge_recharge_lag_test/23_01_ccf_headline_ridge_wells.png     CCF curves overlaid for four headline ridge-adjacent wells                                §5.3 mechanistic test
  23_ridge_recharge_lag_test/23_02_peak_lag_vs_ridge_distance.png   The key figure: peak lag vs ridge distance, with Spearman ρ annotated                     §5.3 mechanistic test
  23_ridge_recharge_lag_test/23_03_peak_lag_spatial_map.png         Spatial map of peak lag, ridge reference marked                                           §5.3 mechanistic test
  23_ridge_recharge_lag_test/23_04_b10_b11_by_cluster.png           β₁₀ vs β₁₁ by cluster --- diagnostic check on the extended model                          §5.3 mechanistic test
  23_ridge_recharge_lag_test/23_05_hypothesis_test_summary.txt      Plain-text summary of the hypothesis test result                                          §5.3 mechanistic test
  24_residual_climatology.csv                                       Per-well climatology summary: offset, amplitude, phase, summer--winter, sun correlation   Script 24 plots; §5.4
  24_residual_seasonality/24_01_climatology_panels_by_cluster.png   Per-cluster mean climatology with per-well overlays                                       §5.4 PET-bias caveat
  24_residual_seasonality/24_02_seasonal_amplitude_map.png          Spatial map of seasonal amplitude per well                                                §5.4 PET-bias caveat
  24_residual_seasonality/24_03_sun_residual_correlation.png        Sunshine-hours vs residual correlation per well, by cluster                               §5.4 PET-bias caveat
  24_residual_seasonality/24_04_phase_by_cluster.png                Per-well phase month, grouped by cluster, on hydrological-year axis                       §5.4 PET-bias caveat
  24_residual_seasonality/24_05_diagnostic_summary.txt              Plain-text interpretive summary                                                           §5.4 PET-bias caveat
  ----------------------------------------------------------------- ----------------------------------------------------------------------------------------- ------------------------------------------------------

### []{#anchor-488}[]{#anchor-489}[]{#anchor-490}Where the result appears in the report

-   §4.9.7 *Water Balance Residual Field* --- the corrected field, which closes without requiring an additional flux. Scripts 23 and 24 supply the bound on what the record could have detected.
-   §5.2.1 *Water Balance Residuals as a Model-Adequacy Diagnostic* --- Script 23 is the principal test; its null result on the distance-lag relationship is the substantive finding that bounds what the monthly record could have resolved.
-   §5.4 *PET-bias caveat* --- Script 24 supplies the diagnostic that the Thornthwaite-misspecification interpretation can be set aside, and that a winter-spring recharge nonlinearity is the residual signal that survives.
-   §5 conclusions --- the integrated finding from the three diagnostics: the residual is observationally consistent with a steady or near-steady subsidy at ridge-adjacent wells (captured by α) plus a small winter-spring recharge nonlinearity at the wider network, but not with month-scale ridge-to-well lateral transport or with Thornthwaite PET misspecification.

### []{#anchor-490}[]{#anchor-491}[]{#anchor-492}Cross-references

-   **F.3** --- SSM formulation; the displacement-formulation equation that Scripts 22 and 24 fit via *fit_ssm_intercept()* and that Script 23 extends with a lag-1 rainfall term.
-   **F.4** --- *HEADLINE_LAG = 0*, *DRAINAGE_DATUM = 3.7 m*, cluster labels and colours.
-   **F.5** --- shared utility modules. *model_utils.fit_ssm_intercept()* is the authoritative Model B fit used by Scripts 22 and 24; *model_utils.build_ssm_frame()* is the underlying data-alignment routine.
-   **S.3** --- origin of the per-well α values that Script 22's α-vs-φ scatter cross-correlates against; the canonical β coefficients that Scripts 22, 23, 24 do not revise.
-   **S.5** --- the per-well 100-month windowed fits that Script 07 maps, contrasted with Script 22's full-record fit.
-   **S.13** --- Figure 58 (SSM water-balance residual map) is the visual the diagnostic suite is interrogating; CEH14 is annotated on that figure as the most negative well around which the §5.3 interpretation is anchored.
-   **S.15** --- coastal-retreat gradient as an alternative explanation for some southern-network residual structure; Scripts 23 and 24 are the northern-ridge analogues to that southern-boundary diagnostic.

End of chapter S.16.

## []{#anchor-492}[]{#anchor-493}[]{#anchor-494}S.18 Script 26 --- Van Willegen MSL aggregation and Equilibrium Wetness Index

**Step 30 / 35. Phase 13 --- Van Willegen MSL Analyses in ***run_analysis.py***; paired with S.18b which covers the forecasting tools that operate on this chapter's outputs and with S.18c which covers the report-format figures that render this chapter's trajectory output for §4.8.5.**

### []{#anchor-494}[]{#anchor-495}[]{#anchor-496}Motivation

Curreli et al. (2013) is the foundational reference for ecohydrological thresholds in lowland dune slacks. That paper calibrated absolute groundwater-depth thresholds (SD15b at −0.61 m and SD16 at −0.98 m below ground) against vegetation community composition at fifteen Welsh dune sites, including Newborough, using a 4-year mean of winter water levels as the hydrological metric. The thresholds remain the operational standard for conservation management across the SAC network --- they are the numbers cited by Natural Resources Wales when reporting site condition against vegetation criteria.

Van Willegen et al. (2025) revisited the framework with a larger dataset and a wider range of candidate metrics. The paper tested eighty hydrology metrics against community-mean Ellenberg EbF moisture response across 17 dune-slack vegetation quadrats at Newborough, drawing on vegetation surveys from 2010 to 2019 (453 relevées) and contemporaneous groundwater monitoring from 2007 to 2019. The best-performing predictor was the unweighted 5-year mean spring water level --- MSL5, the metric this chapter documents. The refinement over Curreli is modest in shape but practically significant: the window is 5 years rather than 4 (sensitivity-tested by van Willegen et al. (2025), who found cross-correlation stabilises at 5), and the seasonal sub-window shifts from winter to spring (March through May) to capture conditions during the active vegetative growth period. The paper does not derive new absolute thresholds; the Curreli SD15b and SD16 values remain the calibration anchor against which sites are reported.

The Newborough connection runs deeper than co-location alone. The author of the present study is a co-author on van Willegen et al. (2025), and the paper's piezometer dataset is the same long-term Newborough monitoring network this pipeline operates on. The methodological framework is therefore directly applicable, and the present chapter implements the metric on the full project network --- the 66 reference and \~18 extended-network wells, of which 17 carry co-located vegetation quadrats (the van Willegen quadrat subset). At those 17 wells the calibrated link between MSL5 and vegetation response applies directly; at the other \~67 wells, MSL5 is a hydrological monitoring metric rather than a calibrated vegetation predictor, useful for tracking spatial pattern but not directly tied to a quantified ecological response.

The chapter sits as a complement to, not a replacement for, the report's existing summer-minimum predictive framework. The Scripts 11 / 11b transfer functions, the iterated P_flood derivation in §3.6.3 of the main report, the BACI clearfell summer-minimum step in Scripts 10a / 10d, the CEH36 scraping benefit in Script 09c, the climate projections in Script 14 --- all of these run in summer-minimum space, against the Curreli SD15b / SD16 thresholds. MSL5 serves a monitoring role rather than a predictive one: managers who collect spring readings can monitor MSL5 directly each year, and the 5-year integrated window damps single-year extremes. The two frameworks measure the same multi-year hydrological state through different seasonal windows, and the Empirical relationship to summer minima section below quantifies their cross-correlation at the network scale (Pearson r = 0.95 between MSL5 and the parallel 5-year summer-minimum mean) and the constant offset between them (≈ 0.54 m, the seasonal amplitude of the typical Newborough water table).

### []{#anchor-496}[]{#anchor-497}[]{#anchor-498}Inputs

  ----------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------
  Input file                                      Description
  outputs/01_wells_clean.csv                      Script 01 --- reference-network monthly depths
  outputs/01_wells_extended.csv                   Script 01 --- extended-network monthly depths
  outputs/01_well_elevations.csv                  Script 01 --- Upstand_m, reported per well; no conversion is applied
  outputs/01_locations.csv                        Script 01 --- easting / northing for the MSL5 spatial map
  outputs/01_wells_provenance.csv                 Script 01 --- interpolated-cell flags (S.1 limit=1 policy)
  outputs/02_07_cluster_membership_k5.csv         Script 02 --- reference cluster identifiers
  outputs/06_pear_membership_audit_sitewide.csv   Script 06 --- extended cluster identifiers
  outputs/03_regional_averages.csv                Script 03 --- cluster-centroid monthly series (used by the Method B output; see the Method A and Method B aggregation section below)
  outputs/03_master_data.csv                      Script 03 --- reference-well SSM β coefficients (β₁, β₂, β₃) for the equilibrium wetness index (v1.3.2)
  outputs/01_climate.csv                          Script 01 --- RAF Valley monthly P and PET for the EWI long-term climatology (v1.3.2)
  data/Ecohydrology_dataset.xlsx                  Documented external input --- van Willegen et al. (2024) Mendeley dataset; gitignored, not redistributed; EbF Pass runs if present (v1.3.3)
  ----------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-498}[]{#anchor-499}[]{#anchor-500}Methodology

**Spring window and hydrology year.** The spring window is calendar months 3, 4, and 5 --- March, April, May --- following van Willegen 2025 Table 2. The hydrology year *y* (van Willegen's "hydrology year B") runs from 1 June (*y*−1) to 31 May (*y*), so spring of hydrology year *y* is the three months immediately preceding the year's close. A reading dated 2010-04 therefore belongs to hydrology year 2010 (spring of 2010); a reading dated 2009-07 belongs to hydrology year 2010 (summer of the preceding calendar year). The annual MSL_y for a single piezometer is the unweighted mean of the three spring months of hydrology year *y*. The 5-year mean MSL5(end-year *y*) is the unweighted mean of the five consecutive annual MSLs {MSL\_{y−4}, MSL\_{y−3}, MSL\_{y−2}, MSL\_{y−1}, MSL_y}. The convention follows Curreli 2013 (who used a 4-year winter-mean version) and is sensitivity-tested at 5 years in van Willegen et al. (2025).

**Strictness rules.** Two completeness rules are applied. The minimum-months-per-spring rule requires all three of {March, April, May} to be present in the cleaned monthly series for an annual MSL to be valid (3 of 3, strict). The minimum-years-in-window rule requires all five constituent annual MSLs to be valid for a 5-year mean to be valid (5 of 5, strict). Single-month interpolation under the S.1 limit=1 cleaning policy is allowed to count toward the 3/3 requirement; the per-well CSVs flag interpolation in an *n_interpolated_spring* column so analysts can audit reliance on filled cells. These rules are stricter than van Willegen 2025 itself, which permitted lower completeness in their published analysis. The project's preference for cleanliness over coverage is consistent with the BACI summer-minima panel in Scripts 09c and 10d, which use a similar two-of-four months policy. Annual MSL rows that fail the 3/3 rule are excluded; 5-year windows that contain any excluded annual MSL are excluded; the per-well trajectory line is broken with a true gap rather than bridged with a straight diagonal (see the Site-specific choices section below).

Sign conventions. The pipeline's native depth frame is below the ground surface, which is also the paper convention: *01_wells_clean.csv* carries the master's *depth from surface* values (*level = upstand − dip*), negative below ground and positive where a slack is ponded. No conversion is applied. Script 26 v1.6.0 removed the earlier duplicate *\_m_pipe* columns, which had added the upstand a second time; every output CSV now carries a single ground-referenced frame named *\_m_bg* (*MSL_m_bg*, *MAX_m_bg*, and the same for MSL5 and MAX5), used by all trajectory and spatial figures.

**Annual maxima as a secondary metric.** Van Willegen 2025 reports MAX (annual maximum water level over the hydrology year) as the second-best-performing metric in their Table 2. Each Script 26 output CSV carries MAX5 (5-year mean annual maximum) alongside MSL5 for cross-reference. The chapter does not develop MAX5 separately --- the paper notes that topographic truncation of peaks at individual slacks (water can pond at the surface in wet years, capping the measurable maximum) makes MAX inferior to MSL for cross-site comparison --- but the column is retained for any analyst who wants to reproduce the secondary panel of the van Willegen et al. (2025) analysis.

**Cluster aggregation.** Per-cluster MSL5 trajectories are computed as the simple unweighted mean of constituent wells' per-well MSL5 by (cluster, end-year), pooling the reference and extended-network wells. Cluster identifiers follow the k=5 partition from Script 02 (reference wells) and the Script 06 Pearson membership audit (extended wells assigned to the same k=5 clusters). C1 is the Lake Edge cluster; C2 Dune; C3 Western Residual; C4 Main Forest; C5 Coastal Forest. The Method A and Method B aggregation section below documents a second aggregation method introduced at v1.1.2 --- the cluster-centroid trajectory from *03_regional_averages.csv*, which is the SSM-consistent companion used by the forecasting tools documented in S.18b. The per-well method described here is the headline monitoring metric.

**Network coverage.** The script processes 1,433 (well, hydrology year) annual rows, of which 1,304 (91 %) pass the strict 3/3 rule. From these are derived 884 (well, end-year) 5-year window rows, covering 84 wells (66 reference + 18 extended). 16 of the 17 van Willegen quadrat wells are covered (T41 fails the rule because of an insufficient recent record). The cluster trajectory restricts to window-ends 2014 onwards (see the Site-specific choices section below) and contains 79 (cluster, end-year) rows across the five clusters and sixteen valid window-end years.

### []{#anchor-500}[]{#anchor-501}[]{#anchor-502}Site-specific choices

Three editorial decisions warrant explicit defence in this chapter, since they depart from the most literal van Willegen 2025 protocol.

**Trajectory restriction to window-ends ≥ 2014.** The reference and extended monitoring network expanded materially between 2007 and 2010 as CEH instrumentation came online. Valid annual MSL counts by hydrology year are 7 (2005), 10 (2006), 24 (2007), 31 (2008), 34 (2009), and then 60 from 2010 onwards. Pre-2010 5-year windows draw from a network of fewer than 35 wells, materially differently composed from the post-2010 network of \~60 wells, and any cluster-mean trajectory line that mixes the two creates the visual appearance of a hydrological shift around 2010 that is in fact a network-composition shift. The first 5-year window drawn entirely from the post-2010 network closes at end-year 2014 (covering hydrology years 2010 through 2014). The per-well CSVs retain the full record from window-end 2009 onwards for any analyst who needs early data; only the cluster trajectory plot and the per-quadrat-well plot are clipped to end-year 2014 onwards. This restriction is consistent with van Willegen 2025 themselves, whose published analysis period is 2010--2019 for the same network-coverage reason.

**Pooling reference and extended networks at cluster level.** The cluster aggregations include extended-network wells that the SSM-fitting analyses (Script 03 onward) do not use. The rationale is that spatial coverage matters more than network purity for a monitoring lens: the extended-network wells provide more piezometers in the coastal-edge sub-cluster of C5 and in the lake margin of C1, two areas where the reference network alone is thin. Per-well CSV rows are flagged with a *network* column ∈ {Reference, Extended} so analysts can split the network if needed for a more conservative analysis. The Method B output introduced at v1.1.2 (see the Method A and Method B aggregation section below) uses only the reference network and serves as the SSM-consistent companion.

**Curreli SD15b / SD16 reference lines on the MSL5 trajectory.** The two horizontal reference lines drawn on every Script 26 trajectory plot (SD15b at −0.61 m, SD16 at −0.98 m, both below ground) are the Curreli ecohydrological thresholds, calibrated against summer minima, not against MSL5. Strictly, they are not threshold lines for the MSL5 metric. They are retained on the MSL5 plot because they are the most-recognized ecological reference points in the literature and a manager reading the figure expects to see them. The figure caption notes the offset explicitly --- a cluster-mean MSL5 line touching SD15b corresponds to a 5-year summer-minimum mean roughly at SD16, given the ≈ 0.54 m offset documented in the Empirical relationship to summer minima section below.

**Analysis-specific exclusion of CEH13 and CEH14 from MSL5 (v1.2.0, 2026-06-25).** Two wells --- CEH13 and CEH14 --- are excluded from every derived MSL5 product: the Method A cluster-mean trajectory, the latest-per-well table, the IDW change map, and the quadrat figure. Both wells have a degenerate SSM drainage coefficient (CEH13 near-zero β₃, an SSM identification failure producing a physically implausible τ outlier; CEH14 negative β₃, SSM failure, NSE = −3.21) that makes their MSL5 five-year spring windows unreliable. The exclusion criterion is the MSL5-side application of the same β₃ identification criterion that already excluded CEH13 and CEH14 from the τ = Sy/β₃ storage--drainage index computation (§S.12): both are excluded on β₃ ≤ 0 or near-zero grounds; the same rationale applies here to the five-year windowed spring metric. The excluded wells are held in *config.MSL5_EXCLUDED_WELLS* (keys lowercase to match the normalized well column in the per-well CSV). The rows are **retained** in *26_msl_5yr_per_well.csv* with two new columns, *msl5_excluded* (boolean) and *msl5_excluded_reason*, for transparency; a filtered subset with excluded rows removed feeds all downstream products. This is an analysis-specific exclusion that does not affect either well's membership of the clustering, SSM, BACI, or any other pipeline analysis.

### []{#anchor-502}[]{#anchor-503}[]{#anchor-504}Empirical relationship to summer minima

A direct cross-check between MSL5 and the parallel 5-year mean of summer minima (5-yr SM5) was run as part of script verification. At the individual-year scale (annual MSL vs annual summer minimum, per well), the Pearson correlation across all valid (well, year) rows is 0.77. At the 5-year window scale (MSL5 vs the corresponding 5-year mean summer minimum, per well across window-ends 2014 onwards), the correlation rises to 0.945 (n = 829 (well, end-year) rows where both metrics are valid). The constant offset between the two metrics, computed as the mean of (5-yr SM5 − MSL5) across the same rows, is 0.54 m with a standard deviation of 0.15 m. The 5-yr SM5 is roughly 0.54 m deeper than MSL5 --- the seasonal amplitude of a typical Newborough water table between spring and the late-summer minimum.

The offset is approximately constant across clusters, varying only over the range 0.51 to 0.67 m at window-end 2025:

  --------------------- ---- ---------- -------------- ----------------
  Cluster               n    MSL5 (m)   5-yr SM5 (m)   SM5 − MSL5 (m)
  C1 Lake Edge          8    −0.24      −0.82          −0.58
  C2 Dune               30   −0.27      −0.89          −0.62
  C3 Western Residual   12   −0.78      −1.50          −0.72
  C4 Main Forest        8    −0.83      −1.35          −0.52
  C5 Coastal Forest     26   −0.62      −1.18          −0.56
  --------------------- ---- ---------- -------------- ----------------

The two metrics measure essentially the same multi-year hydrological state through different seasonal windows. MSL5 is shallower because spring water tables, refreshed by winter recharge, sit roughly half a metre above the late-summer minimum at each cluster. The implication for the report's analytical structure is that MSL5 does not add new *predictive* capacity beyond the existing summer-minimum forecasting framework --- the two are essentially co-linear at the 5-year window scale. What MSL5 does add is the *calibrated link to the van Willegen vegetation framework* at the 17 quadrat wells, plus a metric that can be computed from spring readings alone for managers who prefer that monitoring cadence.

This complementarity is not a contradiction. The two frameworks describe the same hydrological state through different seasonal windows, and a reader who encounters substantial summer-minimum threshold-crossing predictions in §4.10.1 of the report alongside more modest MSL5 climate projections in §S.18b should not interpret the contrast as one framework overturning the other. Section S.18b.3.7 expands on this point in the context of the UKCP18 climate scenarios: the spring window's structural cancellation between increased winter rainfall and increased summer PET produces a smaller projected climate shift than the summer-minimum window, which has no compensating winter-rainfall effect. Both readings are correct; they sample the climate signal at different points of its seasonal structure.

### []{#anchor-504}[]{#anchor-505}[]{#anchor-506}Climate context for the post-2024 trajectory lift

The cluster MSL5 trajectory shows a marked upward lift at window-ends 2024 and 2025. The lift is real, but it is largely climate-driven rather than evidence of management recovery. Hydrology year 2024 is the wettest in the 2007--2026 record at Newborough --- 1,143 mm annual rainfall against a long-term mean of 855 mm (+34 %), and 234 mm spring rainfall against a long-term mean of 161 mm (+45 %). The 2024 spring is the wettest spring in the record. By contrast, hydrology year 2025 returned to dry conditions: 746 mm annual (−13 %) and 121 mm spring rainfall (−25 %).

Because MSL5 at window-end 2024 averages hydrology years 2020 through 2024 --- and window-end 2025 averages 2021 through 2025 --- the entry of the record-wet 2024 year into both windows lifts the cluster means substantially. The expected lift from a single wet year carrying \~7 % of the window's weight, multiplied by the 73 mm spring anomaly and the local β₁ recharge coefficient, is consistent in scale with the observed end-2024 lift across the network. The post-2024 trajectory is not evidence of management recovery alone; the climate component is doing most of the work at the right edge of the figure. As hydrology year 2024 ages out of the rolling window in subsequent years, MSL5 should fall back closer to its pre-2024 level unless one of the intervening years matches 2024's anomaly.

This is exactly the kind of single-year extreme influence that the 5-year window is designed to dampen, and the framework does dampen it --- the lift is real but smaller than the 2024 single-year anomaly would produce on an annual basis. The window smooths; it does not eliminate. The chapter's limitations section makes this caveat explicit, and the §5 discussion in the main report should mirror the same caution: trajectory readings from the most-recent window-ends should be interpreted with the underlying climate sequence in mind.

### []{#anchor-506}[]{#anchor-507}[]{#anchor-508}Intervention markers and the management-response horizon

The cluster trajectory and per-quadrat-well plots draw three intervention events as paired vertical lines, encoding the temporal logic of the 5-year window:

  ---------------------- --------------- ------------------------- --------------------------- -----------------------------
  Event                  Date            Intervention hydro-year   First affected window-end   First fully-post window-end
  Scrape (CEH36)         April 2015      2015                      2015                        2019
  Clearfell              December 2017   2018                      2018                        2022
  Re-scrape (CEH18/21)   October 2023    2024                      2024                        (out of range)
  ---------------------- --------------- ------------------------- --------------------------- -----------------------------

The solid vertical line marks the first window-end that contains any post-intervention spring data --- the earliest window in which an intervention can register at all under a 5-year aggregation. The dashed vertical line marks the first window-end where all five constituent years are fully post-intervention --- the earliest window in which the intervention is the only post-intervention signal in the average.

For the December 2017 clearfell, the first fully-post-clearfell window closes at end-year 2022, covering hydrology years 2018 through 2022. This is the management-relevant horizon for expecting a vegetation response under van Willegen's 5-year framework. Vegetation monitoring rounds before the end-2022 window are observing partial-recovery hydrology (the 5-year mean still includes pre-clearfell years); rounds at or after the end-2022 window are observing the integrated post-clearfell hydrological state. A practical implication for site managers is that monitoring at year-end 2022 onwards is the first time the framework would expect the clearfell signal to be visible in MSL5 at any cluster; expecting earlier response is asking the metric to do something the 5-year smoothing was specifically designed to avoid.

Intervention dates are imported from *utils.scraping_common* as the canonical pipeline constants (*SCRAPING_DATE = 2015-04-01*, *INTERVENTION_DATE = 2017-12-01*, *SCRAPING_DATE_2 = 2023-10-01*); intervention line colours come from *utils.config* (*INTERVENTION_COLOUR_SCRAPE = \"#7b3294\"* purple for scraping, *INTERVENTION_COLOUR_CLEARFELL = \"#e66101\"* orange for clearfell). Both are sourced from configuration rather than hardcoded locally.

### []{#anchor-508}[]{#anchor-509}[]{#anchor-510}Method A and Method B aggregation

Script 26 produces two per-cluster MSL5 aggregation methods alongside the per-well aggregation described above. The reason two methods exist is an internal consistency requirement: the SSM β coefficients in Script 03 are fitted against the cluster-centroid monthly series in *03_regional_averages.csv*, which uses the LCSC reference network only (the 66 reference wells, not the \~84 reference + extended pool). The MSL5 forecasting tools introduced in S.18b --- Section 5 of Script 11 (Tool A) and Script 26b (Tool B) --- would otherwise sit in a different baseline than the per-well-aggregated trajectory documented above. To make the forecasting tools internally consistent with the SSM coefficients they read from, Script 26 produces a second per-cluster CSV alongside the per-well-aggregated one.

The terminology used in the codebase and across the supplement is:

-   **Method A**: per-well annual MSL → arithmetic cluster mean across all wells assigned to the cluster (reference + extended). Written to *26_msl_5yr_per_cluster.csv*. This is the headline monitoring metric documented in the preceding sections of this chapter, used in the §4.8.5 trajectory figure and spatial map.
-   **Method B**: cluster-centroid monthly series from *03_regional_averages.csv* → annual MSL → 5-year MSL5 on the centroid. Reference network only. Written to *26_msl_5yr_per_cluster_centroid.csv*. This is the SSM-consistent companion used by the forecasting tools in S.18b.

The two methods can differ by tens of centimetres at any single (cluster, year) pair because they describe different network compositions, not different aggregation algebra. The empirical comparison across all 77 common (cluster, window-end) rows shows mean \|Method B − Method A\| of 0.30 m and maximum 0.78 m (at C4 Main Forest in window-end 2011); the Pearson correlation between the two trajectories is 0.69. The sign of the difference varies by cluster: Method B is deeper than Method A at C1, C2, C4, and C5 (because the extended network adds shallower coastal-edge and lake-margin wells that pull the per-well mean upward), but shallower at C3 (because the C3 reference network omits some particularly deep wells that the extended network includes).

Both methods are mathematically correct. They answer different questions and describe different cluster populations. Method A is "what is the typical well in this cluster experiencing?" --- the natural aggregation for monitoring, closest to van Willegen's per-piezometer calibration framework. Method B is "what is the cluster's reference-network signal?" --- the natural aggregation for any analysis that sits on top of the SSM coefficients. The chapter retains both and the report's editorial convention is that §4.8.5 figures cite Method A and any numerical claim from Tool A or Tool B carries the implicit Method B provenance. Each cluster MSL5 number quoted in the report should be qualified with the method that produced it; the supplement's chapter S.18b restates this point in its own context.

### []{#anchor-510}[]{#anchor-511}[]{#anchor-512}Limitations

A small set of limitations should be noted alongside the chapter's results, all of which are operational rather than methodological challenges to the metric itself.

MSL5 is an aggregation, not a model. The script does not attribute the cluster-mean trajectory to particular drivers (clearfell, climate, coastal retreat). Attribution work sits in Scripts 10a and 10d (BACI clearfell), Script 25 (coastal-retreat gradient), and Script 14 (climate projections), all of which operate in summer-minimum space against the Curreli thresholds. The MSL5 trajectory should be read as a monitoring record, not as a causal decomposition.

Direct ecological calibration applies only at the 17 van Willegen quadrat wells where co-located permanent vegetation quadrats exist. At the other \~67 wells in the network MSL5 is a hydrological monitoring metric only, useful for tracking spatial pattern but not directly tied to a quantified vegetation response. Sixteen of the seventeen quadrat wells pass the strict 3/3 + 5/5 rules; T41 is excluded because of an insufficient recent record.

The 5-year window lags the underlying hydrological state by approximately half the window length. A change in conditions in year *y* will not be fully reflected in MSL5 until the window closes at end-year *y* + 4. This is by design --- the smoothing is the point --- but it means that the metric is not a real-time indicator. Tool A in S.18b addresses this by providing an empirical transfer function that lets managers predict the next year's annual MSL from monthly readings collected through end-February; that prediction can be added to a rolling four-year history of observed annual MSLs to update the MSL5 statistic without waiting until end-May for the actual reading.

The post-2024 trajectory lift documented in the Climate context section is climate-influenced rather than purely management-driven. Conclusions about clearfell or scraping recovery drawn from the most-recent window-end alone should be made cautiously; the broader trajectory shape is the more defensible reading. As hydrology year 2024 ages out of the rolling window in subsequent years, the lift should attenuate unless one of the intervening years matches its anomaly.

The Curreli SD15b and SD16 reference lines on the trajectory plot are calibrated against summer minima, not MSL5. They are retained on the MSL5 plot for visual familiarity, with the ≈ 0.54 m offset between the two metrics flagged in the figure caption and quantified in the Empirical relationship to summer minima section above. A site whose MSL5 trajectory crosses SD15b is operationally in the SD16-equivalent state when read in summer-minimum space, and the management implications follow correspondingly.

No UKCP18 forward projection of MSL5 is produced by this chapter. The predictive forecasting framework runs in summer-minimum space (Scripts 11, 11b, 14). A separate perturbation overlay applying UKCP18 RCP8.5 multipliers to the MSL5 trajectory is documented in chapter S.18b as Tool B; that capability sits in the Method B baseline (cluster centroid from *03_regional_averages.csv*) and produces small projected shifts of 1 to 4 cm at the 2050s and 2080s. The smallness of the projected MSL5 shifts is structural --- a feature of the spring window straddling the seasonal partition of the UKCP18 multipliers --- and is not in tension with the larger projected summer-minimum shifts that drive the report's climate-vulnerability framing.

### []{#anchor-512}[]{#anchor-513}[]{#anchor-514}Outputs

  ----------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Output                                                                  Description
  outputs/26_van_willegen_msl/26_msl_annual_per_well.csv                  Per (well, hydro_year) annual MSL and MAX in the ground-referenced frame, with completeness flags
  outputs/26_van_willegen_msl/26_msl_5yr_per_well.csv                     Per (well, end_year) 5-year MSL5 and MAX5 with cluster identifiers, network flag, and *msl5_excluded* / *msl5_excluded_reason* columns (CEH13 and CEH14 flagged; all rows retained --- downstream products filter on *msl5_excluded = False*)
  outputs/26_van_willegen_msl/26_msl_5yr_per_cluster.csv                  **Method A** cluster-mean trajectory: mean, median, std per (cluster, end_year). Headline monitoring metric.
  outputs/26_van_willegen_msl/26_msl_5yr_per_cluster_centroid.csv         **Method B** cluster-centroid trajectory from *03_regional_averages.csv*. SSM-consistent companion to Tools A and B.
  outputs/26_van_willegen_msl/26_msl_5yr_latest_per_well.csv              Most-recent valid MSL5 per well --- input to the spatial map
  outputs/26_van_willegen_msl/26_equilibrium_wetness_index_per_well.csv   Per-well EWI (pipe and bg frames, β coefficients, cluster, *network* tier) (v1.3.2)
  outputs/26_van_willegen_msl/26_ewi_msl5_comparison.csv                  Per-well observed vs EWI-predicted MSL5, residual, 95 % bootstrap prediction interval, *open_dune_scope* and *in_van_willegen* flags --- the weighable prediction table (v1.3.2)
  outputs/26_van_willegen_msl/26_ewi_calibration_fit.csv                  OLS calibration fit: slope, intercept, 95 % CIs, n, R², RMSE by scope group (v1.4.0)
  outputs/26_van_willegen_msl/26_ebf_comparison.csv                       Per-piezometer Ellenberg-F with MSL5 and EWI predictions and residuals --- vegetation cross-validation; produced when *data/Ecohydrology_dataset.xlsx* is present (v1.3.3)
  outputs/26_van_willegen_msl/26_ebf_prediction_scatter.png               Three-panel between-well Ellenberg-F scatter (MSL5 / annual EWI / spring EWI); produced when dataset present (v1.3.3)
  outputs/26_van_willegen_msl/26_msl_5yr_trajectory.png                   Cluster-mean MSL5 trajectory with SD15b/SD16 reference lines and intervention markers (Method A; main-report figure)
  outputs/26_van_willegen_msl/26_msl_5yr_map.png                          IDW-interpolated MSL5 surface with DEM hillshade, KML overlays, ridge mask; van Willegen quadrat wells flagged (main-report figure)
  outputs/26_van_willegen_msl/26_msl_5yr_quadrat_wells.png                Per-well MSL5 trajectories at the 17 van Willegen quadrat wells (supplement figure)
  outputs/26_van_willegen_msl/26_msl_results.txt                          Run transcript with cluster-level summary and per-quadrat-well numerical values
  ----------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-514}[]{#anchor-515}[]{#anchor-516}Where the result appears in the report

  -------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Report section                                                       Content
  §4.8.5 *Five-Year Mean Spring Water Level (MSL5)*                    **Table 16** (cluster-mean MSL5 at window-end 2025 with SD15b/SD16 threshold-crossing counts, source *26_msl_5yr_per_cluster.csv*), the cluster trajectory plot (**Figure 43**) and the spatial MSL5 map (**Figure 44**); the results narrative
  §3.7.6 *Equilibrium wetness index*                                   EWI definition, calibration, and its derivation from the SSM coefficients (Methods)
  §4.8.6 *Equilibrium wetness index and vegetation cross-validation*   EWI-vs-MSL5 comparison table; Ellenberg-F cross-validation; Williams' test (Results)
  §5.7.6 *Equilibrium wetness index as a monitoring complement*        EWI as a short-record alternative to MSL5; forest-cluster caveat (Discussion)
  -------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-516}[]{#anchor-517}[]{#anchor-518}Cross-references

-   **F.4** --- Curreli SD15b / SD16 constants; the MSL\_\* constants; *VW_QUADRAT_WELLS*; *INTERVENTION_COLOUR\_\**
-   **F.5** --- *paths.OUT_26\_\**, *paths.DIR_26*
-   **S.1** --- limit=1 cleaning policy underlying the strict 3/3 spring rule
-   **S.6** (Script 09c) --- summer minima at CEH36 scraping; the metric MSL5 is offset from
-   **S.7** (Scripts 10a, 10d) --- BACI clearfell summer-minimum step; the predictive complement
-   **S.9** (Scripts 11, 11b) --- spatial threshold maps in summer-minimum space; cross-correlation with MSL5 at the 5-year scale (r = 0.945, see Empirical relationship section above)
-   **S.15** (Script 25) --- coastal-retreat gradient contributing to the western-margin pattern visible in the MSL5 map
-   **S.18b** (Scripts 11 Section 5, 26b) --- forecasting tools that operate on this chapter's Method B output: empirical spring MSL transfer function (Tool A) and UKCP18 RCP8.5 climate projection (Tool B)

### []{#anchor-518}[]{#anchor-519}[]{#anchor-520}Equilibrium wetness index and vegetation cross-validation (v1.3.2)

Added 2026-07-03. Extends Script 26 with a coefficient-based steady-state wetness metric and a one-off cross-validation against the Ellenberg-F vegetation dataset.

From v1.3.2 the script computes an equilibrium wetness index (EWI): the steady-state water-table level implied by a well's fitted SSM coefficients under long-term mean climate. Setting the mean monthly change to zero in the SSM and solving the head-dependent drainage term for the steady-state displacement gives h_disp,eq = (β₁P̄ − β₂PET̄)/β₃, whence EWI_bg = h_disp,eq − DRAINAGE_DATUM in the ground frame; no upstand term is added. Here P̄, PET̄ are the full-record monthly-mean rainfall and Thornthwaite PET --- the same long-term climatology basis as the Script 21 scenario normals --- making the index climate-window-independent. Reference wells take β from 03_master_data.csv; extended wells are fitted in-script via the shared fit_ssm() (single pass, no reference QA, flagged network = extended), with cluster labels from the Script 06 Pearson sitewide integration. CEH13 and CEH14 (degenerate β₃) and any well below MIN_OBS (NW12, L1) are excluded. This yields 84 wells (64 reference + 20 extended).

**Consistency with the withdrawn equilibrium form.** §F.5 records that an equilibrium Δh/β₃ formulation was withdrawn from the Script 21 scenario engine for producing physically implausible magnitudes. The EWI is an equilibrium form, and its raw magnitudes are indeed systematically too deep --- a mean bias of about −0.37 m against observed MSL5. This is acknowledged rather than contradicted: the raw equilibrium level is never reported. The index is used only after calibration onto the MSL5 scale by ordinary least squares, MSL5 = a + b · EWI, which absorbs the magnitude bias; the equilibrium form is retained only as the *shape* that orders wells by intrinsic wetness. The calibration is scoped to the open-dune network (clusters C1--C3), consistent with MSL5's own open-dune character and with the forest coefficients being least constrained (§S.19); C4/C5 forest wells are predicted but flagged *open_dune_scope = False*. Verified fit: MSL5 = 0.195 + 0.924 · EWI (n = 62, r = 0.94, RMSE = 107 mm). The relationship is assessed at three levels: 100 mm RMSE on the 46 open-dune wells outside the van Willegen quadrat set; 160 mm RMSE on the calibration wells; 227 mm RMSE on the out-of-scope forest set (n = 20, *open_dune_scope = False*).

**EWI prediction uncertainty.** The *26_ewi_msl5_comparison.csv* output carries a per-well 95 % prediction interval, estimated by a bootstrap residual re-sampling procedure (n = 500 resamples from the calibration-well residuals, applied per well, seeded for reproducibility). The typical open-dune interval width is ≈ ±220 mm; interval width is not constant --- it narrows where the calibration regression is densely supported and widens in sparse regions of EWI space. The forest-well intervals are wider still (≈ ±370 mm) because the *open_dune_scope = False* flag propagates the full extrapolation uncertainty. These intervals are carried in the output CSV for downstream consumers (report table, web forecaster) and should be reported wherever a single EWI value is cited. The calibration fit itself is reported with its own 95 % CI on the slope and intercept from the OLS fit (see *26_ewi_calibration_fit.csv*, written at the same pass).

**Vegetation cross-validation.** To test both metrics against the ecological target directly, co-located Ellenberg-F moisture indicator values (wetness scale 1--12; Hill et al., 1999) from the van Willegen open dataset (van Willegen et al., 2024) are aggregated to a mean per piezometer. Observed MSL5 and the EWI are each regressed on mean Ellenberg-F between wells; the difference between the two dependent correlations is tested by Williams' test (Williams, 1959). The two are statistically indistinguishable --- MSL5 r = +0.83 \[0.59, 0.93\], RMSE 0.337 Ellenberg-F units; EWI r = +0.81 \[0.55, 0.93\], RMSE 0.352; Williams p = 0.81 (n = 18) --- with the equivalence holding band by band. From v1.3.3 this cross-validation is generated by the pipeline (Script 26 Pass 7) from the documented external dataset (*paths.DATA_ELLENBERG_EXT*, *data/Ecohydrology_dataset.xlsx*, gitignored and not redistributed); it runs when the dataset is present and is skipped otherwise, writing *26_ebf_comparison.csv* and the three-panel scatter *26_ebf_prediction_scatter.png*. No spatial EWI surface is produced: a standalone map overstated the (modest) local coverage advantage, so the weighable per-well comparison table replaces it.

Outputs.

  ------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------- ----------------------------------
  Output file                                 Contents                                                                                                                               paths constant
  26_equilibrium_wetness_index_per_well.csv   Per-well EWI (pipe and bg frames, β coefficients, cluster, network tier)                                                               paths.OUT_26_EWI_PER_WELL
  26_ewi_msl5_comparison.csv                  Per-well observed vs EWI-predicted MSL5, residual, 95 % bootstrap prediction interval, *open_dune_scope* and *in_van_willegen* flags   paths.OUT_26_EWI_MSL5_COMPARISON
  26_ewi_calibration_fit.csv                  OLS calibration fit: slope, intercept, 95 % CIs, n, R², RMSE by scope group                                                            paths.OUT_26_EWI_CALIB_FIT
  ------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------- ----------------------------------

References added (Script 26 v1.3.2).

-   Hill, M.O., Mountford, J.O., Roy, D.B. & Bunce, R.G.H. (1999). Ellenberg's indicator values for British plants. ECOFACT Volume 2, Technical Annex. ITE, Huntingdon.
-   van Willegen, L. et al. (2024). Dune slack Ecohydrology Dataset. Mendeley Data, V1. https://doi.org/10.17632/p4xvb6xxp9.1
-   Williams, E.J. (1959). The comparison of regression variables. *J. R. Statist. Soc. B*, 21(2), 396--399.

End of chapter S.18.

## []{#anchor-520}[]{#anchor-521}[]{#anchor-522}S.18b --- Spring MSL forecasting tools (Script 11 Section 5, Script 26b)

**Step 31/50 for Script 26b (Phase 13 --- Van Willegen MSL Analyses in ***run_analysis.py***); Script 11 Section 5 lives in Phase 3 at step 11/50 inside ***11_forecasting_thresholds.py***. Companion to S.18; followed in the supplement by S.18c which documents Script 26c's display-only report-format figures.**

### []{#anchor-522}[]{#anchor-523}[]{#anchor-524}S.18b.1 Purpose and editorial weighting

This chapter documents two complementary forecasting capabilities that pair with the observational 5-year mean spring water level (MSL5) metric introduced in S.18. The first is a per-cluster empirical transfer function predicting next-year MSL from monthly readings collected through end-February (Tool A, implemented as Section 5 of Script *11_forecasting_thresholds.py*). The second is a perturbation-overlay capability producing per-cluster ΔMSL5 estimates under UKCP18 RCP8.5 50th-percentile climate scenarios for the 2050s and 2080s (Tool B, implemented as Script *26b_van_willegen_msl_projections.py*).

The two tools sit at different levels of editorial weight in the report. Tool A produces fits with R² between 0.73 and 0.96 across the network and a clean operational use case for site managers; the equations are reported as Table 9 in §3.6 and the calibration scatter as a §3.6 figure. Tool B is a documented robustness / climate-sensitivity capability whose projected magnitudes (1--4 cm at 2050s and 2--4 cm at 2080s) sit within observed interannual variability and well below the forest-management BACI signal at this site. Tool B is therefore presented in this supplement chapter with full method detail but is summarized in the main report in a single discussion sentence rather than as a headline figure. This editorial weighting reflects the empirical scale of the result rather than a methodological reservation about the technique.

### []{#anchor-524}[]{#anchor-525}[]{#anchor-526}S.18b.2 Tool A: empirical spring MSL transfer function

#### []{#anchor-526}[]{#anchor-527}S.18b.2.1 Specification

For each of the five clusters (C1 Lake Edge, C2 Dune, C3 Western Residual, C4 Main Forest, C5 Coastal Forest) the transfer function takes the form

MSL_y = α · h_max_winter + β · P_win_to_spr + γ · PET_win_to_spr + intercept

where MSL_y is the mean of March, April, and May water levels in hydrology year y (the van Willegen 2025 spring window), h_max_winter is the maximum cluster-centroid head over October y−1 to February y, and P_win_to_spr and PET_win_to_spr are cumulative totals over October y−1 to May y. The hydrology year follows van Willegen's "hydrology year B" (1 June y−1 to 31 May y), so the response and all three predictors fall within the same hydrology year by construction. Coefficients are fitted independently per cluster by ordinary least squares with an intercept term.

#### []{#anchor-527}[]{#anchor-528}S.18b.2.2 Data source

The fit uses Script 03's cluster-centroid monthly series in *03_regional_averages.csv* --- five columns (Lake_Edge, Eastern_Block, Western_Block, Forest, Coastal_Forest) corresponding to the five clusters under Script 03's BLOCK_MAP. This is the same baseline that the report's state-space coefficients β₁, β₂, β₃ are fitted against (S.3 of this supplement) and the same baseline as Tool B's perturbation overlay. The choice ensures internal consistency between the empirical transfer function, the SSM mechanism, and the projection companion. Section S.18b.4 below addresses the relationship between this cluster-centroid baseline (referred to in the codebase as "Method B") and the per-well-aggregated baseline used in S.18's headline trajectory figure ("Method A").

The annual-aggregation strictness rules match those of S.18: three of three spring months must be present for an annual MSL to be valid, and the rolling 5-year MSL5 statistic (not used by Tool A directly, but inherited from the framework's data source) requires all five constituent annual MSLs to be valid.

#### []{#anchor-528}[]{#anchor-529}S.18b.2.3 Results

The five-cluster table of fitted coefficients is reproduced below (full numerical values are written to *outputs/11_forecasting_thresholds/11_forecast_spring_transfer_functions.csv*).

  --------------------- ------------------ -------------- ---------------- --------------- ------- ----
  Cluster               β(h_max, winter)   β(P_win→spr)   β(PET_win→spr)   Intercept (m)   R²      n
  C1 Lake Edge          +0.139             +0.00110       −0.00130         −0.646          0.719   19
  C2 Dune               +0.371             +0.00131       −0.00175         −0.668          0.842   20
  C3 Western Residual   +0.637             +0.00096       −0.00097         −0.703          0.888   20
  C4 Main Forest        +0.841             +0.00086       +0.00045         −0.953          0.959   19
  C5 Coastal Forest     +0.753             +0.00040       −0.00027         −0.601          0.960   19
  --------------------- ------------------ -------------- ---------------- --------------- ------- ----

Coefficients on h_max_winter, P_win_to_spr are positive everywhere and statistically significant (p \< 0.01) at all clusters except Lake Edge and Dune, where the winter-peak coefficient is small (+0.14) and non-significant (p = 0.47). PET_win_to_spr coefficients are negative at all clusters except Main Forest, where the value (+0.00045) is essentially zero and statistically non-significant (p = 0.73). Physical interpretation: rainfall over the October-to-May window raises the next spring's MSL; potential evapotranspiration lowers it; and the previous winter peak --- when statistically distinguishable from zero --- carries information about the antecedent groundwater state.

Five-cluster R² values range from 0.719 (Lake Edge) to 0.960 (Coastal Forest), with the two forest clusters (C4 and C5) fitted essentially deterministically. The Lake Edge cluster has the lowest R² of the five but the fit is still strongly predictive; its lower R² is consistent with the lake's hydrological buffering, where the lake stage moderates year-to-year sensitivity of the dune water table to the winter peak.

#### []{#anchor-529}[]{#anchor-530}S.18b.2.4 A rejected variant

An earlier two-variant implementation (Script 11 v1.1.0) also fitted a "previous-MSL input" form of the transfer function using the previous year's MSL as the antecedent state in place of the winter peak. That variant was empirically weaker: R² values ranged from 0.18 (Forest) to 0.44 (Coastal Forest), and the previous-MSL coefficient was statistically non-significant (p \> 0.5) at four of five clusters. Only Coastal Forest, with its high persistence and long memory, gave the previous-MSL form real predictive weight. The previous-MSL variant was dropped at v1.1.1 in favour of the single winter-peak form retained here. The decision was made on empirical grounds: a manager-accessible form with weak predictive power is not a useful tool, and the winter-peak form requires no additional measurement effort beyond the routine monthly dipwell programme that managers already operate.

#### []{#anchor-530}[]{#anchor-531}S.18b.2.5 Manager workflow

The intended use case is illustrated by the following workflow. A site manager monitoring spring readings each year accumulates a rolling history of observed MSL values {MSL_y−4, MSL_y−3, MSL_y−2, MSL_y−1}. To project the next 5-year MSL5 forward in early spring of year y --- before taking the actual May reading --- the manager takes the cluster's winter peak from October-to-February monthly readings, the cumulative October-to-May rainfall, and the corresponding PET, and plugs the values into the appropriate cluster's transfer function from the table above. The predicted MSL_y is then added to the rolling history to produce an updated 5-year MSL5 estimate. The estimate becomes verifiable when end-May readings arrive, at which point it can be replaced by the observation.

The workflow is most operationally useful for early-warning purposes: a predicted MSL_y that crosses into a depth-of-concern band before May allows managers to consider intervention or attention scheduling in advance. Coupling the transfer function to van Willegen's Ellenberg EbF response curves (for clusters where per-piezometer calibrations are available) extends the early warning into a vegetation-risk indicator.

### []{#anchor-531}[]{#anchor-532}[]{#anchor-533}S.18b.3 Tool B: UKCP18 RCP8.5 MSL5 climate projection

#### []{#anchor-533}[]{#anchor-534}S.18b.3.1 Specification

Script *26b_van_willegen_msl_projections.py* produces per-cluster projected MSL5 trajectories under UKCP18 RCP8.5 50th-percentile Wales scenarios for the 2050s and 2080s. The script does not run the state-space model forward in time. Instead, it computes a monthly Δh perturbation from each cluster's fitted SSM coefficients and the UKCP18 multipliers, and applies the perturbation as a constant vertical shift to the observational Method B trajectory produced by Script 26.

#### []{#anchor-534}[]{#anchor-535}S.18b.3.2 Method

For each cluster and each scenario the monthly Δh perturbation is

Δh(m) = β₁ · (P_scen(m) − P_base(m)) − β₂ · (PET_scen(m) − PET_base(m))

where β₁ and β₂ are the cluster's SSM coefficients from Script 03 (S.3 of this supplement), P_base and PET_base are the long-term monthly climatology over the monitoring period (2005-04 to 2026-02), and P_scen and PET_scen apply seasonal UKCP18 multipliers to P_base and PET_base. The pattern matches the single-step monthly perturbation function documented in Script 21 (*utils.model_utils.monthly_perturbation*), with the simplification that for a pure climate scenario the scenario β₂ equals the baseline β₂ --- no land-use change --- so the PET term reduces to the form shown.

The UKCP18 multipliers used by Tool B are the central-estimate Wales 50th-percentile values for RCP8.5 at the 2050s and 2080s time horizons, identical to those exposed by Script 19's *SCENARIO_PARAMS* dictionary in the scenario viewer. Specifically:

  -------------------- ------------ ------------ -------------- --------------
  Period               Winter P ×   Summer P ×   Winter PET ×   Summer PET ×
  2050s (2040--2069)   1.10         0.85         1.05           1.20
  2080s (2070--2099)   1.20         0.70         1.10           1.35
  -------------------- ------------ ------------ -------------- --------------

Winter is taken as November through March; summer as May through September. April and October are shoulder months, and Tool B assigns each shoulder month the mean of the winter and summer multipliers --- a documented choice for transitional months that straddle the canonical seasonal windows. April matters because it is one of the three spring-window months; assigning it the mean rather than either pure winter or pure summer is the least biased choice when the spring window straddles the seasonal partition.

Because the perturbation is linear in P and PET and the multipliers are constant year-on-year (climatology shift, not interannual sequence), the resulting MSL5 shift is a single constant per cluster per scenario equal to the mean of the spring Δh values:

ΔMSL5 = mean(Δh_Mar, Δh_Apr, Δh_May)

The projected MSL5 trajectory is therefore the observational Method B trajectory shifted vertically by this constant. The observed line and the projected lines differ in absolute position but share the year-to-year shape --- same wet years, same dry years, same intervention markers in the same places. The horizontal offset between observed and projected trajectories is the scenario sensitivity at each cluster.

#### []{#anchor-535}[]{#anchor-536}S.18b.3.3 What the projection is and is not

Tool B is a perturbation overlay. It answers the question "what would the observed MSL5 trajectory over the monitoring period have looked like if the UKCP18 2050s (or 2080s) climate had been in force throughout?" The horizontal offset is the scenario sensitivity; the year-to-year shape is the observed climatology.

Tool B is *not* a forward-in-time forecast of what MSL5 will be observed in 2050. UKCP18 projects shifts in climatology, not shifts in interannual variability; the actual 2050 record could include individual years wetter or drier than any in the 2014--2025 observed window. The projection is a climatological response under stationary observed variability, not a single-realisation forecast.

Tool B's single-step perturbation approach also avoids the SSM forward-integration drift problem documented in Script 21. Running the SSM forward from an arbitrary initial condition accumulates drift because the water-balance intercept α that closes the SSM at fitting time is not part of the single-step propagation rule. The single-step perturbation pattern works as a forcing-shift overlay on the observed record rather than as an integrated time projection, and is drift-free by construction.

A standard UKCP18 caveat applies: the multipliers used are 50th-percentile central estimates. The 5th-to-95th percentile ranges span considerably wider intervals at end-century, and the projection magnitudes shown below would be correspondingly wider if computed under those ranges. Tool B is run on the central estimates as a single best-guess perturbation; the report does not extend it to the full UKCP18 uncertainty range.

#### []{#anchor-536}[]{#anchor-537}S.18b.3.4 Results

Per-cluster projected ΔMSL5 values are reproduced below (full numerical values are written to *outputs/26b_van_willegen_msl_projections/26b_msl5_ukcp18_projection_summary.csv*).

  --------------------- ------ ------ ----------------- -----------------
  Cluster               β₁     β₂     ΔMSL5 2050s (m)   ΔMSL5 2080s (m)
  C1 Lake Edge          4.58   0.92   −0.011            −0.021
  C2 Dune               3.97   1.74   −0.017            −0.031
  C3 Western Residual   3.57   1.81   −0.017            −0.031
  C4 Main Forest        2.48   2.56   −0.021            −0.039
  C5 Coastal Forest     2.43   1.27   −0.012            −0.022
  --------------------- ------ ------ ----------------- -----------------

The projected MSL5 shifts are modest at all five clusters: between 1.1 and 2.1 cm under the 2050s scenario and between 2.1 and 3.9 cm under the 2080s scenario. Main Forest (C4) has the largest shift because its high β₂ makes it most responsive to PET increases; Lake Edge and Coastal Forest (lower β₂) have the smallest shifts. The signs are negative everywhere --- net drying --- because the PET-driven term dominates the rainfall-driven term across the spring window even when winter rainfall is projected to increase.

#### []{#anchor-537}[]{#anchor-538}S.18b.3.5 The spring-window structural cancellation

A non-trivial feature of the projection is the partial cancellation between winter and summer climate signals within the spring window. The spring months span both the winter (March) and the summer (May) UKCP18 partition windows, with April as the shoulder month. Across these three months the rainfall multiplier shifts from +5% in March through +10% in April (shoulder mean) to +10% in May (summer); the PET multiplier shifts from +5% in March through +13% in April (shoulder mean) to +20% in May. The two trends largely offset for spring totals, and the net Δh emerges as the residual.

This structural cancellation is specific to the spring window. The same UKCP18 multipliers applied to summer minima would produce much larger shifts, because the summer-minimum window (June through September) sits entirely within the summer partition and the +20--35% PET increase has no compensating winter-rainfall offset. The existing Script 11 Section 4 summer transfer function captures the summer signal explicitly. The implication for managers using MSL5 as a monitoring metric is that the metric is relatively climate-resilient compared to the summer minimum, which is a feature for monitoring stability but is *not* a finding that the site is insensitive to climate change overall.

#### []{#anchor-538}[]{#anchor-539}S.18b.3.6 Climate signal in context

The projected ΔMSL5 magnitudes (1--4 cm) are smaller than three other quantities that bear on the report's interpretation:

The forest-management BACI clearfell signal at the Forest Impact tier is +0.113 m (raising spring water tables; Chapter S.7 of this supplement, BACI ANCOVA results). The clearfell signal is three to seven times larger than the central-estimate UKCP18 spring climate signal. Within the spring monitoring window and at the decadal timescale considered, forest management decisions matter more than central-estimate climate change for cluster-mean MSL5 at this site. Over longer (multi-decadal) horizons the climate signal accumulates and could become comparable, but within the framing of van Willegen's 5-year monitoring statistic the management signal dominates.

The observed interannual variability of MSL5 across the 2014--2025 monitoring window is on the order of tens of centimetres at each cluster --- substantially larger than the projected climate shifts. A single dry or wet year shifts MSL5 by more than the 2080s projection moves the climatology mean. Interpreting the projection therefore requires care: the climatology shifts but a manager observing a particular year will continue to see the dominant interannual signal on top of it.

The aggregation-method difference between Method A and Method B (S.18b.4 below) is itself on the order of tens of centimetres at some clusters --- mean \|Method B − Method A\| of about 30 cm across the network, maximum of 78 cm at Main Forest in 2011. The methodological choice between aggregations therefore moves cluster MSL5 estimates by more than the projected climate signal, which is one of several reasons the chapter retains both methods rather than declaring one canonical.

These three quantities --- management signal, interannual variability, aggregation choice --- all exceed the central-estimate climate signal by an order of magnitude or more. This sets the appropriate weight for Tool B in the report: a documented capability whose results are reported as evidence of climate-signal scale at this site rather than as a foregrounded prediction.

#### []{#anchor-539}[]{#anchor-540}S.18b.3.7 Relationship to the Curreli summer-minimum predictions

The report's principal climate-vulnerability framing (§4.10.1 and the discussion in §5) uses summer minima and the Curreli SD15b and SD16 ecological thresholds. Under UKCP18 RCP8.5 50th-percentile central estimates, summer minima at most clusters are projected to cross those thresholds during the 2040s and beyond. Tool B, in contrast, finds that spring MSL5 shifts only by 1--4 cm under the same UKCP18 scenarios. The two findings can appear contradictory: how can summer minima be projected to fall through ecological thresholds while spring MSL5 barely moves?

The two findings are not contradictory. They are the same UKCP18 climate signal projected onto two different observation windows, and the difference arises from the seasonal asymmetry of the climate signal itself. UKCP18 RCP8.5 projects winter (Nov--Mar) wetter (P × 1.10 to 1.20) and slightly elevated PET (× 1.05 to 1.10), while it projects summer (May--Sep) drier (P × 0.85 to 0.70) and substantially elevated PET (× 1.20 to 1.35). The spring window (Mar--May) straddles the boundary: March and parts of April sample winter conditions, while May samples summer conditions. Within the spring window the wet-winter and dry-summer signals partially offset (S.18b.3.5). The summer-minimum window (Jun--Sep), by contrast, sits entirely inside the dry-summer signal with no offsetting winter-rainfall contribution.

For direct comparison: Script 19's spatial-groundwater scenarios --- which apply the same UKCP18 multipliers to seasonal cluster water balances --- project summer-season Δh values of approximately 6 to 7 cm at the 2050s and 11 to 13 cm at the 2080s across the five clusters, compared with Tool B's spring-window ΔMSL5 of 1 to 2 cm at the 2050s and 2 to 4 cm at the 2080s. The summer-season projections are three to five times larger than the spring projections, with the precise ratio depending on the cluster's β₂ and the relative weight of the winter offset in its spring window. This three-to-five-fold ratio between summer and spring climate sensitivity is the structural feature of the UKCP18 signal at this site, not a discrepancy between two competing methodologies.

The implication for monitoring practice is that the two metrics measure different aspects of ecological stress. Summer minima measure the annual depth-of-drying peak --- the seasonal stress maximum that pushes vegetation toward the dry end of its tolerance band --- and are the appropriate metric for the Curreli SD15b and SD16 thresholds, which were calibrated against summer-stress responses. The 5-year mean spring water level (MSL5) measures the integrated water availability during the spring growing window --- the conditions for active vegetative growth --- and is the appropriate metric for the van Willegen 2025 Ellenberg-EbF framework, which was calibrated against per-piezometer spring conditions across multiple sites. Both metrics are ecologically valid; they characterize distinct stresses; and they respond differently to a seasonally-structured climate signal. The MSL5 metric is structurally climate-resilient because the spring window straddles the seasonal partition; the summer-minimum metric is structurally climate-sensitive because it samples only the side of the year that is drying. Neither finding overturns the other.

For the report's main-text discussion this means three things. First, the Curreli summer-minimum threshold-crossing projections stand: they are the correct climate-vulnerability framing for the SD15b and SD16 thresholds, and the projected 2040s+ crossings are real. Second, the modest MSL5 shifts in Tool B are also correct: they are the spring-window response to the same climate signal, and they characterize the climate resilience of the spring monitoring metric specifically. Third, the right reading is that **MSL5 is a stable monitoring backbone while the summer-minimum framework captures the climate-vulnerability dimension**, and both belong in the report's monitoring recommendations. Managers using MSL5 for routine annual tracking should also continue to track summer minima as the climate-stress indicator; the two together give a more complete picture of dune-slack water-table dynamics under change than either gives alone.

#### []{#anchor-540}[]{#anchor-541}S.18b.3.8 A parallel per-well aggregation pathway

Tool B as documented above fits the SSM β coefficients on the cluster-centroid hydrograph: one OLS per cluster, with β₁ and β₂ taken from the cluster-centroid *03_regional_averages.csv* series. This is the canonical pathway. Its outputs anchor §3.7.5 of the main report (the MSL5 methods framework), §4.8.5 (Script 26c's cluster trajectory figure), and §4.10.1 (Script 26c's ΔMSL5 vs Δsummer-minimum contrast); the Method B aggregation rationale (S.18b.4) gives the reasoning.

A parallel per-well aggregation pathway was added at Script 26b v1.1.0 (2026-05-27) producing the secondary CSV *26b_msl5_ukcp18_projection_summary_perwell.csv*. The per-well pathway fits the SSM β coefficients per well on *03_master_data.csv* and then arithmetically averages β₁ and β₂ within each cluster, applying the same pure-climate perturbation formula *Δh(m) = β₁ · P(m) · (sP(m) − 1) − β₂ · PET(m) · (sPET(m) − 1)* and the same Mar--May spring window. The output is a separate CSV with 12 rows per scenario (5 cluster rows plus a well-count-weighted SITE row), structurally parallel to the centroid summary.

The per-well aggregation does not reduce algebraically to the centroid OLS, even on the same wells: the two aggregations differ by 0.5 to 3.7 mm per cluster per UKCP18 scenario, with the largest gap in C1 (lake-edge, n = 7, the most heterogeneous reference-network cluster). Both are defensible summaries of the same SSM. The motivation for the parallel pathway is the Script 19 v2.8.0 scenario viewer (S.13), whose new ΔMSL5 row uses per-well-averaged β throughout --- consistent with the rest of the viewer's per-cluster table --- and which therefore cannot validate against the centroid CSV on principle. The per-well CSV serves as the matching canonical reference for the viewer row, validating to ≤0.5 mm per (cluster, scenario) pair (current state: 0.042 mm worst case, a rounding artefact of the viewer CSV's 4-dp formatting). The canonical centroid CSV remains unchanged byte-for-byte at the v1.1.0 commit; Script 26c continues to read it, and the §3.7.5 / §4.8.5 / §4.10.1 report numbers are not affected by the addition of the per-well pathway.

The two CSVs therefore sit side-by-side as parallel summaries: the centroid CSV is the report-anchored canonical, and the per-well CSV is a secondary artefact whose primary role is the viewer-row validation target. A future report-aggregation decision can compare them directly.

### []{#anchor-541}[]{#anchor-542}[]{#anchor-543}S.18b.4 Tool C: Equilibrium Wetness Index (EWI) MSL5 prediction

The EWI is documented in full in chapter S.18 (§*Equilibrium wetness index and vegetation cross-validation*). This sub-section records only its position in the tool hierarchy and its relationship to Tools A and B.

The EWI answers a different question from Tools A and B. Tool A is a forward-predictor --- given this winter's climate, what will next spring's MSL5 be? Tool B is a climate-scenario overlay --- how does the MSL5 trajectory shift under UKCP18? Tool C (EWI) is a structural diagnostic --- given a well's SSM coefficients and the long-term mean climate, what is its intrinsic wetness equilibrium? It requires no MSL5 observations, only an SSM fit (order 30 months minimum). This makes it available at wells that lack five complete consecutive springs and therefore cannot carry an observed MSL5 value.

Tool C is complementary, not a replacement: where both MSL5 and EWI are available, the two should be read together --- EWI narrows the structural band; MSL5 tracks the recent observed departure from it. The 95 % prediction intervals in *26_ewi_msl5_comparison.csv* (§S.18) carry this relationship explicitly: the interval is the calibration-transfer uncertainty, not a process uncertainty, and it is wider for forest-zone wells where the calibration does not apply directly.

Cross-reference: §S.18 (full EWI methodology, calibration statistics, vegetation cross-validation); §4.8.6 of the main report (EWI results and comparison table); §5.7.6 (monitoring complement framing).

### []{#anchor-543}[]{#anchor-544}[]{#anchor-545}S.18b.5 Method A and Method B aggregation

A consequence of paired Tools A and B both operating on Script 03's cluster-centroid monthly series is that the report carries two MSL5 aggregations side by side. Script 26 produces both as parallel CSV outputs:

*26_msl_5yr_per_cluster.csv* is the **Method A** trajectory, computed by taking the per-well annual MSL5 for every well assigned to the cluster (under the k=5 partition extended through Script 06's Pearson membership audit) and then taking the mean across wells per cluster per window-end-year. Method A aggregates the extended cluster network --- on the order of 25 wells in C5, for example. It is the natural aggregation for monitoring because it uses the maximum spatial coverage available and is closest to the per-piezometer framework that van Willegen uses for vegetation calibration. The trajectory figure in §4.8.5 of the report and the spatial MSL5 map in §4.8.5 are both Method A.

*26_msl_5yr_per_cluster_centroid.csv* is the **Method B** trajectory, computed by taking the cluster-centroid monthly series from *03_regional_averages.csv* (which is the LCSC reference network only, on the order of 5 wells in C5) and applying the same 3/3 + 5/5 strictness rules used by Method A. Method B is the aggregation that the SSM β coefficients are fitted against and is therefore the internally consistent baseline for Tool A's empirical OLS fits and Tool B's perturbation overlay. The Method B trajectory is referenced by Tools A and B; it is not a headline observational figure in the report.

The two methods are both valid; they answer different questions and describe different network compositions, not different aggregation algebra. The Method A cluster mean is "the typical well in this cluster", aggregating across all monitored points; the Method B cluster centroid is "the cluster's reference-network signal", aggregating across the subset that the SSM coefficients describe. When network composition is stable the two coincide; at Newborough the extended cluster network includes shallower coastal-edge wells (in C5 particularly) that the reference network does not, so the mean depths differ. Mean \|Method B − Method A\| across all (cluster, window-end) pairs is approximately 0.30 m; maximum 0.78 m at Main Forest in 2011. C3 Western Residual is the one cluster where Method B is shallower than Method A (the C3 reference network omits some particularly deep wells that the extended network includes); the other four clusters have Method B deeper than Method A.

The chapter S.18 of this supplement covers the Method A side as the headline monitoring metric. This chapter (S.18b) uses Method B because it is the SSM-consistent baseline for the predictive tools, and Tools A and B both read from *03_regional_averages.csv* (Method B's underlying monthly series) for that reason. Each cluster MSL5 number quoted in the report should be qualified with the method that produced it; the main-report convention is that §4.8.5 figures cite Method A and any number from Tool A or Tool B carries the implicit "Method B" provenance.

### []{#anchor-545}[]{#anchor-546}[]{#anchor-547}S.18b.6 Pipeline integration

Tool A and Tool B are integrated into the analytical pipeline managed by *run_analysis.py* as follows:

Tool A is Section 5 of Script *11_forecasting_thresholds.py* (step 22 of the pipeline, Phase 1). It runs whenever Script 11 runs and adds two outputs (one CSV, one calibration figure) to the existing five-output Script 11 result set. Section 5 is invoked from Script 11's *run_models()* orchestrator function after the four pre-existing sections (state-space coefficient summary, winter transfer functions, summer transfer functions, P_flood iteration); existing outputs are unchanged.

Tool B is Script *26b_van_willegen_msl_projections.py* (step 29 of the pipeline, Phase 13). It runs alongside Script 26 (step 28) and produces four CSV outputs and one figure to its own output directory *outputs/26b_van_willegen_msl_projections/*. The script reads its observational baseline from Script 26's Method B CSV (*26_msl_5yr_per_cluster_centroid.csv*), so Script 26 must run first; this dependency is enforced by run order within Phase 13. The four CSVs are the centroid-fitted projection summary (the canonical one consumed by Script 26c and used in §3.7.5 / §4.8.5 / §4.10.1), the parallel per-well-aggregated summary (added at Script 26b v1.1.0 as a validation target for Script 19's scenario-viewer ΔMSL5 row --- see §S.18b.3.8 below), the full 12-month Δh-per-cluster matrix, and the run transcript.

Script *26c_msl5_report_figures.py* (step 30 of the pipeline, Phase 13) follows Script 26b and renders the two report-format MSL5 figures cited in §4.8.5 and §4.10.1 of the main report; it is documented in S.18c and reads only canonical outputs from Scripts 26, 26b, and 19, so all three must have run.

The greyscale figure-conversion utility (*27_greyscale_figures.py*) is step 44 of the pipeline and sits in Phase 17 as part of the post-analytical phase alongside Script 09f.

### []{#anchor-547}[]{#anchor-548}[]{#anchor-549}S.18b.7 Data sources and reproducibility

UKCP18 RCP8.5 multipliers used by Tool B are central-estimate (50th-percentile) Wales values for the 2050s and 2080s time horizons. The 2050s constants also exist in *utils.config* as *UKCP18_DRY\_\** / *UKCP18_WET\_\** pairs (carried for cross-reference with Script 19's scenario viewer); the 2080s constants are hardcoded in Script 26b's *UKCP18_SCENARIOS* dictionary at the top of the file. Centralising the 2080s constants in *utils.config* alongside the 2050s pairs, so Scripts 19 and 26b share a single source, is noted as a follow-up.

Source: van Willegen et al. (2025), *Ecological Indicators* 170, 113016 --- methodological anchor for the MSL5 statistic and its hydrology-year convention. Met Office (2018), UKCP18 Land Projections, Regional 12 km ensemble --- source of the climate multipliers. Curreli et al. (2013) --- source of the SD15b and SD16 reference thresholds shown on the trajectory figures (note that these are calibrated against summer minima, not MSL5; the \~0.54 m offset at the 5-year window scale is documented in S.18 of this supplement).

End of chapter S.18b.

## []{#anchor-549}[]{#anchor-550}[]{#anchor-551}S.18c Script 26c --- Report-format MSL5 figures

**Step 32 / 35. Phase 13 --- Van Willegen MSL Analyses in ***run_analysis.py***; display-only companion to S.18 and S.18b.**

Script 26c is a display-only companion to Scripts 26 and 26b. It produces two figures cited in §4.8.5 and §4.10.1 of the main report and reads only the canonical outputs of Scripts 26, 26b, and 19; no analysis is recomputed. The methodological framework underlying both figures is the MSL5 framework documented at §3.7.5 of the main report and at §S.18 and §S.18b of this supplement. This chapter records only the display step.

The first output is *fig_msl5_trajectory_report.png*, the report-format cluster-mean MSL5 trajectory over 2014--2025. The figure plots Script 26's Method A trajectory against the Curreli (2013) SD15b (−0.61 m) and SD16 (−0.98 m) reference values, with the SD16 dry-slack zone shaded for visual emphasis of cluster-time combinations sitting inside that ecohydrological regime. The figure is a report-format companion to the methods-context trajectory *26_msl_5yr_trajectory.png* produced by Script 26: both show the same data; the difference is editorial. The methods-context figure retains the intervention markers (2015 scrape, 2017 clearfell, 2023 re-scrape) for methodological clarity; the report-format figure omits them and adds the SD16 shading and 2025 value labels for direct ecological readability. Both figures are valid in their respective contexts.

The second output is *fig_msl5_vs_summer_min_projection.png*, a two-panel horizontal-bar contrast of ΔMSL5 against Δsummer-minimum for the five clusters under UKCP18 RCP8.5, with the 2050s in the top panel and the 2080s in the bottom. ΔMSL5 values are read from Script 26b's *26b_msl5_ukcp18_projection_summary.csv*; Δsummer-minimum values are read from Script 19's *19_scenario_summary.csv* (rows where *season = summer*, column *dh_mean_m* --- Script 19's "summer" Δh is the seasonal mean of monthly Δh over the SUMMER_MONTHS window, treated here as the closest SSM correlate to the annual summer minimum). The figure makes one scientific point: the spring baseline metric MSL5 is substantially better buffered against the projected climate trajectory than the summer-minimum metric, by a factor of three to six across all five clusters and both horizons. The cross-reference to §4.10.1 of the main report carries the discussion of this result.

End of chapter S.18c.

## []{#anchor-551}[]{#anchor-552}[]{#anchor-553}S.19 Scripts 28, 29, 30 --- Cluster framework diagnostics (Phase 14)

Steps 33, 34 and 35 / 36. Phase 14 --- Cluster framework diagnostics.

The two scripts in this chapter were added on 2026-05-29 following the post-review pass on the main report (Hollingham 2026). They test post-Script-25 implications for the cluster framework documented in §5.1 of the report and supply the quantitative validation paragraphs in §5.1.1 (gap D in the post-review priorities list). Both scripts consume already-produced pipeline outputs and write into their own output directories; both run after Phase 13 and before the Phase 15 differential-change scripts.

The methodological motivation for both diagnostics is the same. §5.1 of the main report frames C2 and C3 as eastern and western positions on a substrate-thickness gradient --- shallow sand over till in the east, deeper sand in the west as the basal till sheet dips and merges with the Menai Strait estuarine clays. The Ward's clustering on (1 − Pearson r) distance imposes a discrete cluster boundary on what is, on this substrate-architecture picture, a continuous behavioural gradient. The framing rests on Stratford et al. (2007) and Grootjans et al. (2004) but is not, in the published version of the report, validated against the project's own data. Two questions follow naturally. First: is the C2/C3 behavioural distinction reproducible by adding a coastal-erosion drift onto C2 hydrographs --- i.e., can the distinction be folded back into C2 by a single reductive operation acting on the level signal? Second: given that C3 is internally heterogeneous in spatial coefficients (visible in Script 07's per-well β maps), what is the structure of that heterogeneity, and does it resolve a smooth gradient or warrant a finer cluster partition? Script 28 addresses the first question; Script 29 addresses the second. Together they form a diagnostic dyad: Script 28 rules out one reductive alternative, Script 29 provides a spatial-gradient signature that the substrate-architecture picture predicts.

### []{#anchor-553}[]{#anchor-554}[]{#anchor-555}S.19.1 Script 28 --- C3 detrend check

**Motivation.** Test whether the C3 cluster is mechanistically C2 with a western-margin coastal-erosion drift superimposed (H1) or whether it is a behaviourally coherent cluster on a westward-thickening substrate gradient (H0). Under H1, removing the predicted coastal drift from each C3 well's hydrograph should cause the de-trended series to migrate to a C2 best-match against the un-de-trended cluster centroids; under H0, C3 wells should remain best-matched to C3 regardless of de-trending. The test rules out the simplest reductive explanation (a linear-in-time drift on level, added to otherwise C2-like behaviour); it does not by itself distinguish a discrete-architecture C3 from a continuous-substrate-gradient C3, which Script 29 addresses.

Inputs.

  -------------------------------------- ----------- ---------------------------------------------------------------
  Input file                             Source      Contents
  02_cluster_stats.csv                   Script 02   Cluster assignments and reference network membership
  01_wells_clean_maod.csv                Script 01   Monthly hydrographs in mAOD
  03_regional_averages.csv               Script 03   Cluster centroid time series for re-classification
  25_01_panel_fit_parameters.csv         Script 25   Live δ₀, L, c from the forest-free linear-capped headline fit
  25_02_per_well_summer_min_slopes.csv   Script 25   Per-well *dist_coast_m* for evaluating δ(d)
  -------------------------------------- ----------- ---------------------------------------------------------------

**Methodology.** For each well, the predicted coastal-erosion drift rate is δ(d) = δ₀ · max(0, 1 − d/L) using the live Script 25 forest-free linear-capped fit (δ₀ = −29.03 mm/yr, L = 894 m, c = −6.40 mm/yr at the headline state of 2026-05-29). The well's monthly hydrograph is de-trended by subtracting the linear trend of slope δ(d) over the observation window: since δ is negative (a decline rate), the correction is positive in time, undoing the drift the model attributes to coastal-erosion proximity. The de-trended series is then re-classified against the un-de-trended cluster centroids using correlation distance on monthly anomalies (1 − Pearson r, the same metric Script 02 uses to construct the clusters). The well is assigned to the cluster whose centroid it correlates with most strongly post-de-trending.

The diagnostic rule of decision is calibrated against the C3 cluster size of n = 21 wells (with two intervention wells excluded --- CEH36, the 2015 dune-scrape site, and WMC3, the 2017 clearfell Impact well --- leaving 19 testable C3 wells). If ≥ 17 of 19 (≈ 90 %) C3 wells migrate to a C2 best-match after de-trending, H1 is strongly supported. If 11--16 wells migrate, the result is partial. If ≤ 10 wells migrate, H1 is rejected --- the reductive "C2 + coastal drift" explanation does not account for the C2/C3 distinction.

Five sensitivity variants are run to guard against under-specification of the drift model: the headline forest-free monthly-uniform variant; a summer-only Jun--Sep variant that applies the drift correction only to summer-window months; a full-network δ₀ variant that uses the full-fit gradient (which includes forest wells) instead of the forest-free fit; an L = 500 m variant (shorter inland reach); and an L = 1500 m variant (longer inland reach). A C2 sanity check accompanies each variant: C2 wells should not migrate to other clusters under the same procedure, since the gradient model attributes negligible drift to them (C2 wells are mostly beyond L). Low C2 retention would indicate that the de-trending procedure is contaminating hydrographs rather than testing a hypothesis.

Outputs.

  ------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Output                                           Description
  outputs/28_c3_detrend/28_c3_detrend.csv          Per-well: original best-match, de-trended best-match (headline + 4 sensitivities), correlation deltas, *dist_coast_m*, applied δ(d)
  outputs/28_c3_detrend/28_c3_detrend_results.md   Memo with headline result, decision rule, full sensitivity table, C2 sanity-check retention, excluded-wells list
  outputs/28_c3_detrend/28_c3_detrend_panel.png    Four-panel figure: (a) representative C3 hydrograph before and after de-trending; (b) classification scatter showing correlation deltas; (c) sensitivity bar chart across the five variants; (d) C2 sanity-check retention bars
  ------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Path constants (new).** *paths.DIR_28*, *paths.OUT_28_DETREND_TABLE*, *paths.OUT_28_DETREND_MEMO*, *paths.OUT_28_DETREND_PANEL*.

**Headline result (2026-05-29).** **H1 rejected.** Of 19 testable C3 wells, **0 genuinely migrate** from a C3 best-match to a C2 best-match as a result of de-trending. One nominal migrant (NW13 under the headline variant) was already C2-best-matched before any de-trending and is therefore not a genuine migrant. The result is robust across all five sensitivity variants --- the highest migration count in any variant is 2 of 19, well below the H1 threshold of 17. C2 sanity-check retention is 24 of 24 wells (100 %), confirming the de-trending procedure does not contaminate the underlying hydrographs. The reductive "C2 + linear coastal drift" explanation is rejected; the result is compatible with both a discrete-architecture C3 and a continuous-substrate-gradient C3, and Script 29 (below) provides additional evidence favouring the gradient interpretation.

**Implication for the report.** The C2/C3 behavioural distinction cannot be reproduced by removing a linear coastal-erosion drift from C2 hydrographs --- it is not the residue of an east-to-west drift superimposed on identical underlying behaviour. This is consistent with the §5.1 aquifer-architecture framing --- shallow sand over till in the east, deeper sand in the west --- without by itself resolving whether the substrate change is a discrete architectural boundary or a continuous westward-thickening gradient as the basal till sheet dips and merges with the Menai Strait estuarine clays. Script 29's spatial-structure findings within C3 (below) favour the gradient interpretation. The result feeds the first §5.1.1 paragraph in the main report.

**Limitations.** The de-trending is linear in time, applying the steady-state δ(d) over the full observation window. Any transient coastal-erosion signal (episodic retreat events such as Storm Brendan 2020) is not separately resolved. The drift correction operates only on the western-margin coastal-erosion mechanism on the level signal; if other site-wide mechanisms contribute to the C2/C3 distinction --- most notably an east-to-west substrate-thickness gradient as the basal till dips and merges with the Menai Strait estuarine clays, producing a continuous shift in the SSM coefficient field rather than a drift in level --- they are not represented in the test. The procedure tests a specific H1 (C3 = C2 + coastal drift on the level signal); it does not falsify a continuous-substrate-gradient explanation, which Script 29 is better positioned to address through the within-C3 spatial-structure analysis.

### []{#anchor-555}[]{#anchor-556}[]{#anchor-557}S.19.2 Script 29 --- Within-C3 variance attribution

**Motivation.** Given that Script 28 rejects the reductive "C3 = C2 + coastal drift" hypothesis, what is the structure of variation *between* C3 wells, and does it favour a discrete-architecture or continuous-substrate-gradient interpretation? The per-well β maps from Script 07 visibly show within-cluster heterogeneity in β₁, β₂, β₃, and τ across the C3 wells. The question is whether this within-cluster variance follows a spatial or hydrogeological axis that the cluster framework treats as noise but that warrants explicit treatment in the report's discussion of the §5.1 cluster boundaries, and --- if it does --- whether the axis location is geometrically consistent with the dipping-till / Menai-estuarine-clays substrate-gradient picture.

Inputs.

  ------------------------------------------------ ---------------------- ------------------------------------------------------------------------------
  Input file                                       Source                 Contents
  02_cluster_stats.csv                             Script 02              C3 cluster membership
  01_wells_clean_maod.csv                          Script 01              Monthly hydrographs for slope and amplitude metrics
  01_locations.csv                                 Script 01              Easting, northing, ground elevation per well
  07_spatial_coefficients/07_coeff_maps_data.csv   Script 07              Per-well β₁, β₂, β₃, τ (storage--drainage index Sy/β₃; not a residence time)
  25_01_panel_fit_parameters.csv                   Script 25              δ₀, L for the exponential and linear-capped coastal predictors
  25_02_per_well_summer_min_slopes.csv             Script 25              Per-well *dist_coast_m* and *slope_m_yr*
  data/Features.kml                                versioned data input   Forest polygon for the *dist_forest* predictor
  ------------------------------------------------ ---------------------- ------------------------------------------------------------------------------

**Methodology.** Two panels are constructed for each well in C3:

-   **Behavioural metrics (n = 9):** annual summer-minimum slope *slope_m_yr*, per-well coefficients β₁, β₂, β₃, storage--drainage index τ = Sy / β₃ (not a residence time --- see §S.12 for the t_R = 1/β₃ recession-time distinction), long-term mean head *mean_head_maod*, summer-minimum depth *summer_min_depth_m*, winter-maximum depth *winter_max_depth_m*, and seasonal amplitude as the p90 − p10 spread of the monthly mean hydrograph (matching Script 02's amplitude descriptor).
-   **Predictors (n = 5):** the Script 25 exponential coastal predictor δ₀ · exp(−d/L) (using the forest-free exponential parameters δ₀ = −40.24 mm/yr, L = 407 m, c = −5.24 mm/yr); distance to CEH36 (the 2015 dune-scrape site at 241,161 E / 363,306 N --- chosen as a topographic and hydrogeological anchor in the south-western interior of the warren); distance to the forest polygon edge from the *Features.kml* feature set (the C4/C5 boundary that bounds forest-management influence); ground elevation from *01_locations.csv* (a topographic axis correlated with northing and elevation); and depth-to-water as *ground_elev − long_term_mean_head* (a hydrogeological covariate separating depth-to-water response from raw ground elevation).

The predictor space has substantial known collinearity: northing and ground elevation correlate at r ≈ 0.98 in the C3 well set, and elevation correlates with the coastal-exponential predictor at r ≈ 0.79. The analysis therefore reports both univariate R² per (metric, predictor) pair and drop-one unique contributions in the full five-predictor model --- the drop-one Δ identifies the predictor that carries unique signal not absorbed by any other predictor.

Outputs.

  ---------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------
  Output                                                           Description
  outputs/29_within_c3_variance/29_within_c3_variance.csv          Per-well: nine behavioural metrics + five predictors + ancillary variables
  outputs/29_within_c3_variance/29_univariate_R2.csv               Single-predictor R² matrix (metric × predictor)
  outputs/29_within_c3_variance/29_drop_one.csv                    Drop-one unique contribution matrix (metric × predictor)
  outputs/29_within_c3_variance/29_within_c3_variance_results.md   Memo: full R² and drop-one matrices with headline interpretation and caveats
  outputs/29_within_c3_variance/29_within_c3_variance_panel.png    Six-panel figure: per-metric scatter against the strongest unique predictor; drop-one heatmap; collinearity matrix
  ---------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------

**Path constants (new).** *paths.DIR_29*, *paths.OUT_29_PANEL_CSV*, *paths.OUT_29_UNIVARIATE_R2*, *paths.OUT_29_DROP_ONE*, *paths.OUT_29_MEMO*, *paths.OUT_29_PANEL_FIG*.

**Headline result (2026-05-29).** Within-C3 variance is well-explained by spatial position, with the strongest fits at the SSM coefficients:

  --------------------------- --------------------- ------------------ ------------------------------
  Behavioural metric          R² (all predictors)   R² (best single)   Strongest predictor (ΔR²)
  β₁ recharge                 0.813                 0.741              dist_CEH36 (Δ = +0.166)
  β₃ drainage                 0.736                 0.634              dist_CEH36 (Δ = +0.156)
  τ storage--drainage index   0.700                 0.585              dist_CEH36 (Δ = +0.317)
  β₂ atmospheric draw         0.672                 0.546              dist_CEH36 (Δ = +0.114)
  slope_m_yr                  0.696                 0.579              delta_coast_exp (Δ = +0.060)
  seasonal_amplitude          0.724                 0.617              dist_CEH36 (Δ = +0.112)
  --------------------------- --------------------- ------------------ ------------------------------

The summer/winter depth and mean-head metrics return near-perfect R² (≥ 0.97) because of their definitional dependence on depth_to_water --- these are sanity-check results rather than findings.

**Distance to CEH36 emerges as the strongest unique predictor across all four SSM coefficients** and across the storage--drainage index and seasonal amplitude. The dist_CEH36 axis represents a hydrogeological gradient within C3 anchored near the south-western interior of the warren, distinct from the network's coastal-erosion axis (which is the strongest unique predictor for the summer-minimum slope itself but does not dominate the SSM coefficients).

A methodological aside emerges from the regression: the Script 25 exponential coastal predictor lands at a regression coefficient of +1.046 against per-well slopes, an independent face-value validation of the exponential functional form (S.15 reports both linear-capped and exponential fits; on AIC the linear-capped form is marginally the better of the two).

**Implication for the report.** Within-C3 heterogeneity is structured --- not noise --- and the structure aligns along an axis anchored near the south-western interior of the warren rather than along the coastal margin. This anchor location is **predicted by**, not merely compatible with, the westward-thickening substrate-gradient hypothesis: a basal till sheet dipping westward and merging with the Menai Strait estuarine clays would produce the thickest overlying sand (and therefore the most distinctive SSM coefficient values) in exactly the south-western interior the regression identifies. The k = 6 sensitivity check performed in the same session (not in Script 29's outputs, but documented in the session log) confirms that this structure is internally coherent: at k = 6, Ward's clustering does not split C3 (all 21 wells remain together) but instead splits C2 (24 wells → 17 + 7 by seasonal amplitude). C3 is "structured but not strongly enough to split" on the (1 − Pearson r) distance metric --- exactly the behaviour expected from a smooth substrate gradient that varies the SSM coefficient field continuously without producing a stepped discontinuity. Read together with Script 28's rejection of the reductive "C2 + coastal drift" hypothesis, the two diagnostics together support the picture of a continuous substrate-gradient architecture with the C2/C3 cluster boundary as a behavioural cut on the continuum rather than a discrete geological boundary. The result feeds the second §5.1.1 paragraph in the main report and is cross-referenced from §5.7.2 (the discussion of within-cluster spatial structure).

**Limitations.** The regression uses n = 19 wells (the C3 cluster minus CEH36 and WMC3, which carry direct intervention signals), so degrees of freedom are limited and the unique contributions of correlated predictors are not always cleanly separable. The dist_CEH36 axis is operationally defined by the 2015 scrape-site location, which is a hydrogeological anchor of opportunity rather than a parameter fitted to the data --- its physical interpretation (proximity to a topographic and hydrogeological transition within C3) is a candidate explanation rather than a tested one. The analysis is C3-specific by motivation; analogous within-cluster diagnostics for C1, C2, C4 and C5 are not produced, on the grounds that the original motivating question (the C3 cluster's distinctness and internal structure) is the §5.1-relevant one.

### []{#anchor-557}[]{#anchor-558}[]{#anchor-559}Cross-references

-   **F.4** --- Cluster partition constants, k=5 anchor wells, partition history.
-   **S.2** --- Ward's hierarchical clustering on (1 − Pearson r) distance; the metric used for the re-classification step in Script 28.
-   **S.3** --- Cluster centroid time series (*03_regional_averages.csv*) used by Script 28 for re-classification.
-   **S.7** --- Per-well β maps (Script 10 spatial coefficients) showing within-C3 heterogeneity; the visual motivation for Script 29.
-   **S.15** --- Script 25 coastal-retreat gradient parameters (δ₀, L, c) feeding both scripts' coastal predictors.
-   §5.1.1 of the main report --- primary destination for both scripts' headline findings (gap D in the 2026-05-29 post-review cascade).

### []{#anchor-559}[]{#anchor-560}[]{#anchor-561}S.19.3 Script 30 --- C4 drainage identifiability diagnostic and reported sensitivities

Step 35/50, Phase 14; opt-in diagnostic tier (cite the committed *pipeline_manifest.json* rather than these counts). Added 2026-06-23 as a constrained-β₃ triangulation sensitivity (v1.0.0--v1.1.0); replaced 2026-07-24 (v2.1.0) by the direct identifiability diagnostic documented here, after the degeneracy premise the earlier script rested on was tested and not supported; per-well two-basis panel and centroid exclusion sensitivity added 2026-08-16 (v2.2.0); results removed from the script's own docstring, comments and console strings in favour of run-time derivation 2026-08-16 (v2.2.1). The retired script's archived outputs remain committed under *outputs/30_c4_constrained_fit/* but are produced by no live script.

**Motivation.** C4 Main Forest returns the network's lowest drainage coefficient and its highest atmospheric draw. Because β₂·PET and β₃·h_disp are the two loss terms in the SSM, the obvious objection is that they are collinear at a cluster with a deep water table, so that the low β₃ is an artefact of the fit rather than a property of the cluster. The earlier version of this script accepted that premise and constrained β₃ to an open-dune anchor. This version tests the premise instead, at the cluster-centroid scale the report cites, and reports two sensitivities that bound the coefficient without revising it.

Inputs.

  ------------------------- ----------- ------------------------------------------------------------------------------------------------------------------------
  Input file                Source      Contents
  02_cluster_stats.csv      Script 02   Cluster membership used to build the centroids
  01_wells_clean.csv        Script 01   Ground-referenced monthly well series
  01_climate.csv            Script 01   Monthly rainfall and Thornthwaite PET
  03_state_space_model.py   Script 03   build_cluster_centroids() is imported, not reimplemented, so the centroids are identical to the canonical construction
  ------------------------- ----------- ------------------------------------------------------------------------------------------------------------------------

**Methodology.** Centroid fits use the shared *model_utils.fit_ssm* on the full record, matching §S.3. Four tests run per cluster. **A, collinearity:** the variance inflation factor of *h_disp_prev* on {P, PET}, the correlation between PET and displacement, and the design condition number --- a high value at C4 relative to the rest of the network would support the degeneracy reading. **B, signal:** the standard deviation and range of displacement, which set the leverage available to resolve β₃, together with β₃'s own standard error. **C, recession:** a recession-only (Δh \< 0) regression of Δh on displacement controlling for PET, an SSM-restricted cross-check on whether the head-dependent response is resolvable independently of the full model. **D, closure:** the steady-state water-balance closure residual evaluated across a grid of fixed β₃ (β₁ and β₂ refitted at each), locating the residual-minimising value relative to the fitted one. Every ranking the script reports is derived from its own diagnostic table at run time; none is typed into the script.

**Per-well panel, two bases.** Each reference well is fitted twice --- on the comparison window used for the per-well coefficient table (§S.3) and on its full record --- so that two candidate explanations for per-well instability can be separated: collinearity, which would show in the per-well VIF, and limited power on a short record, which shows as instability that resolves when the window is lifted. On the committed data the C4 per-well fits move from three of nine returning a significant positive β₃ on the window to seven of nine on full records, with only CEH13 and CEH14 failing; the per-well VIF is unchanged between bases. The counts trace to *30_c4_perwell_beta3.csv* and to the *c4_perwell_sig_window100* and *c4_perwell_sig_fullrecord* keys.

**Centroid exclusion sensitivity --- reported, not adopted.** The canonical C4 centroid is fitted on all nine members and is unchanged by this script. The same centroid is additionally fitted without CEH14, and without both wells listed in *config.MSL5_EXCLUDED_WELLS* (CEH13 and CEH14), whose drainage the displacement model does not resolve over their full records. What is reused is that constant's well set, not its MSL5-only scope; the shared justification is the underlying SSM failure. On the committed data the exclusion raises β₃ from 0.018 to 0.029 month⁻¹ and shortens the recession half-life from about 38 to about 24 months. These are reported in §5.2.3 as a sensitivity; the cluster value in the mechanistic table is unchanged.

Outputs.

  --------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------- -----------------------------------
  Output                                                                Description                                                                                                                     Reference
  30_c4_drainage_identifiability/30_c4_identifiability_by_cluster.csv   Per-cluster VIF, corr(PET, displacement), condition number, displacement SD and range, recession-only response --- tests A--C   §5.2.3
  30_c4_drainage_identifiability/30_c4_perwell_beta3.csv                Per-well β₃, standard error, p-value, VIF and leverage on both the comparison window and the full record                        §5.2.3; §5.4 coefficient surfaces
  30_c4_drainage_identifiability/30_c4_centroid_sensitivity.csv         C4 centroid fitted with all members, without CEH14, and without MSL5_EXCLUDED_WELLS --- sensitivity only                        §5.2.3
  30_c4_drainage_identifiability/30_c4_report_numbers.csv               Named keys --- the single source for the §5.2.3 citations                                                                       §5.2.3
  30_c4_drainage_identifiability/30_c4_drainage_identifiability.png     Per-well β₃ on both bases with the cluster-centroid fit overlaid                                                                Not cited in the report
  --------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------- -----------------------------------

**Trace map (§5.2.3 citation → report-numbers key).** C4 centroid β₃ → *c4_centroid_beta3*; its p-value → *c4_centroid_beta3_p*; variance inflation factor → *c4_vif*; PET--displacement correlation → *c4_corr_pet_hdisp*; displacement SD → *c4_hd_sd*; closure-minimising β₃ → *c4_closure_min_beta3*; per-well non-significant count → *c4_perwell_n_nonsig*; per-well significant counts on the two bases → *c4_perwell_sig_window100* and *c4_perwell_sig_fullrecord*; exclusion-sensitivity β₃ and half-life → *c4_centroid_beta3_excl* and *c4_centroid_halflife_excl*. Values are read from the committed CSV, never from this chapter.

**Limitations.** The diagnostic tests whether C4's drainage coefficient is identifiable; it does not revise it, and nothing downstream reads its outputs. Ranks reported against the rest of the network are comparisons among five clusters and should be read as such rather than as evidence of an absolute threshold. The open-dune anchor of the retired triangulation (0.058 month⁻¹) is retained in §5.2.3 only as a conservative bound on the forest drainage rate, not as a competing estimate: it opens the water-balance closure residual well beyond the fitted value. Per-well fits on the comparison window are individually noisy, which is why the full-record basis is reported alongside rather than instead. The exclusion sensitivity is reported and not adopted, so the cluster coefficient cited throughout the report remains the nine-member fit.

Cross-references.

-   §S.3 --- canonical SSM fits; *03_master_data.csv* and *03_03_cluster_mechanistic_coefficients.csv*, and the centroid composition sensitivity *03_13_centroid_composition_sensitivity.csv*.
-   §S.11 --- Script 16 water-balance decomposition; partition convention and Table 4a.
-   §S.12 --- t_R = 1/β₃ head-space recession time; τ = Sy/β₃ storage--drainage index.
-   §5.2.3 of the main report --- the only location in the report that cites Script 30's numbers.

End of chapter S.19.

## []{#anchor-562}[]{#anchor-563}[]{#anchor-564}S.20 Scripts 32, 33, 35, 36, 37, 37b --- Observed differential change and the climate-response envelope

Phase 15 (steps 36--41/50; 32/33/35 analytical-default, 36/37/37b opt-in --- *\--with-supplementary*). Six analyses that characterize observed network change and driver attribution directly, independently of (and, for 37/37b, in comparison against) the single-mechanism driver model of §S.13--§S.14: where the spring water table is moving relative to the site (Script 32, Figure 63), how far it swings between climate extremes (Script 33, Figure 65), how deep it sits in dry years against the ecological thresholds (Script 33, Figure 66), a per-well frame-independent coefficient extending the amplification metric to short-record wells (Script 35), an absolute climate-removed secular trend map placing the coastal and forest drying on one figure without mean-referencing or residual-construction artefacts (Script 36), a predicted-versus-observed validation of the modelled driver-change map (Script 37), and a comparative footing of forest/scrape/coastal effects on common currencies (Script 37b, Part B). All six read committed pipeline outputs and re-fit nothing in the SSM; their value layers are observational.

### []{#anchor-564}[]{#anchor-565}[]{#anchor-566}S.20.1 Script 32 --- Secular differential water-table movement (Figure 63)

**Motivation.** The two-window MSL5 comparison (Figure 62) cannot separate secular change from window choice (Script 34, §S.21.4). The differential-movement map isolates the secular component by fitting, for each well, the trend of its spring level relative to the site mean. Subtracting the site mean removes the common climate signal, leaving the relative drift --- the slow inland mound holding its position while the fast-draining lake and coastal margins decline. The map is explicitly a differential-recession field, not an absolute-drying map and not a management-signature map.

**Inputs.** *outputs/01_wells_clean.csv* (per-well monthly levels, depth below ground); *outputs/01_locations.csv* (well Easting/Northing); *outputs/03_master_data.csv* (per-well cluster id). The SSM is not re-fitted.

**Methodology.** A spring value is formed per well-year as the mean of the available March--May readings (*config.MSL_SPRING_MONTHS*). The well's anomaly is its spring level minus the site-mean spring level in the same year. The site-mean reference panel is held to the wells present in at least a fixed majority fraction of the period's springs (*PANEL_MIN_FRACTION*), so the reference does not drift with coverage. The metric is the ordinary-least-squares slope of the anomaly against year, in mm yr⁻¹, requiring a minimum number of spring-years per well. Significance is a lag-1 autoregression-corrected t-test on the effective sample size, cross-checked against a moving-block bootstrap confidence interval; significant wells are drawn solid, non-significant wells hollow. Two periods are mapped: 2011--2025 (primary; 66-well site-mean panel) and 2005--2025 (robustness; 21-well panel). Only the Llyn Rhos-Ddu lake gauge is excluded --- CEH13 and CEH14, withheld from the SSM for state-space reasons, are retained because the differential anomaly trend is observational. The per-well slopes are interpolated to a 50 m grid by inverse-distance weighting (power 2), masked beyond 450 m of the nearest well.

**Headline result.** Over 2011--2025, 8 of 74 mapped wells move significantly, almost all sinkers on the south-western coastal and western margin (CEH22 −26.5, CEH21 −15.1, CEH11 −13.3 mm yr⁻¹). Over 2005--2025 the pattern firms to 13 of 77, the coastal and western sinkers (CEH22, NW8, CEH3, NW9, CEH17) strengthening. The forest interior holds its position, with the forest control wells (CEH32 +20.5, CEH34 +17.2, CEH2 +14.9 mm yr⁻¹) among the few drifting upward.

**Outputs.** *outputs/32_differential_movement/*: *32_differential_movement_per_well.csv* (slope, significance, both periods); *32_differential_movement_2011_2025.png* (Figure 63 primary); *32_differential_movement_2005_2025.png* (robustness); *32_results.txt*.

**Limitations.** The differential framing answers "where relative to the site", not "how much in absolute terms" --- the absolute site-mean trend is separately and non-significantly −7.0 mm yr⁻¹ (Script 32 site-mean panel, AR-corrected, p = 0.52). The per-well metric is an OLS slope; the AR correction enters the significance test only. Sparse-coverage wells are flagged via the panel rule rather than dropped.

**Report location.** Figure 63; main-report §4.9.8 (description) and §5.7.5 (interpretation).

### []{#anchor-566}[]{#anchor-567}[]{#anchor-568}S.20.2 Script 33 --- Climate-swing amplification and dry-year spring floor (Figures 65 and 66)

**Motivation.** A window-independent companion to the window-sensitivity caution (Script 34) and to Script 32's secular drift: rather than differencing two marginal windows, it compares genuine dry and wet end-members. From the envelope it derives two products --- a relative amplification field (how much each area magnifies or damps the shared climate swing) and an absolute drought-floor surface (how deep the dry-year spring table sits against the ecological thresholds).

**Inputs.** *outputs/01_wells_clean.csv*; *outputs/01_locations.csv*; *outputs/03_master_data.csv*. The coefficient is observational and does not use the SSM.

**Methodology.** Spring values are formed as for Script 32. Dry and wet extreme states are the per-well mean spring level over fixed extreme-year sets selected by site-mean spring extremity and antecedent-rainfall consistency --- dry {2011, 2012, 2019} and wet {2014, 2021, 2024}. The year 2006 is excluded as a wet extreme because its 2004--2005 antecedent was the driest in the record, so the slow-recession forest wells had not refilled by that spring (it is not an antecedent-matched wet state). Each well's swing is its wet state minus its dry state; its amplification coefficient (Figure 65) is that swing divided by the network-mean swing, with the common-mode swing removed, so values above one magnify and below one damp the shared forcing. The drought-floor surface (Figure 66) is the dry-state depth to water, kept in absolute depth below ground and contoured against the Curreli et al. (2013) SD15b (0.61 m) and SD16 (0.98 m) thresholds, which are absolute distances to surface. Only the lake gauge is excluded; CEH13 and CEH14 are included (*config ENVELOPE_METRIC_EXCLUDE = lake only*) because the coefficient is observational. The amplification field is interpolated to a 50 m grid by linear interpolation (*scipy griddata*), masked beyond 450 m; the drought-floor surface is likewise linearly interpolated with a ridge mask, and the single raised inter-slack well CEH10 is shown as a distinct slack-edge marker but excluded from the interpolated slack-floor surface, which would otherwise smear its raised-ground depth across the neighbouring slacks.

**Headline result.** The site-mean dry-to-wet spring swing is ≈ 752 mm (0.75 m). The slow-draining C4 forest interior amplifies it to ≈ 1.72× (≈ 1.7×), the lake edge damps it to ≈ 0.61× (≈ 0.6×), and the open dune is close to unity. The amplification field correlates with the per-well β₂ coefficient, a marker of the deep, slow-recession store. In the dry years the forest interior and western residual block already sit below the SD16 dry-slack threshold.

**Outputs.** *outputs/33_envelope_amplification/*: *33_envelope_per_well.csv* (dry/wet state, swing, amplification, cluster); *33_amplification_field.png* (Figure 65); *33_dry_spring_depth.png* (Figure 66); *33_results.txt*.

**Limitations.** The amplification is a relative measure and the extreme-year selection is fixed and antecedent-screened rather than data-adaptive. The drought-floor contour is a strict, conservative lower bound on the area below ecological viability: because spring is the seasonal high, a spring level already below a summer-minimum threshold guarantees the summer minimum is deeper still, so the true late-summer sub-threshold footprint is larger. Head swing is not specific-yield-normalized --- the figures report observed head movement directly, for ecological and observational directness.

**Report location.** Figures 65 and 66; main-report §4.9.8 and §5.7.5.

### []{#anchor-568}[]{#anchor-569}[]{#anchor-570}S.20.3 Script 35 --- Per-well climate-sensitivity coefficient

**Motivation.** A discrete, frame-independent per-well companion to Script 33's interpolated amplification field, extended to wells with short or inconsistent records that the matched surface and the SSM cannot reach. It produces no surface --- a coefficient table, an SSM-calibration figure, and a discrete marker map --- so it does not duplicate Script 33.

**Inputs.** *outputs/01_wells_clean.csv*; *outputs/01_locations.csv*; *outputs/03_master_data.csv* (β₁/β₂/β₃ + cluster, for calibration); *outputs/06_pear_membership_audit_sitewide.csv* (cluster fallback for unclustered wells).

**Methodology.** Each well's dry-to-wet spring swing is normalized co-temporally: the reference core is the wells with full dry-extreme coverage and adequate wet coverage, and the coefficient is the well's swing divided by the core's mean swing recomputed over that well's own extreme years. This cancels the common climate signal window by window, so wells measured on different subsets of extreme springs remain comparable; it reproduces the matched-window amplification (validated r ≈ 0.98) while removing coverage artefacts. Each coefficient carries a confidence tier (A: ≥ 2 dry and ≥ 2 wet years; B: ≥ 1 of each; C: a single year on one side) and a delete-one-extreme-year jackknife 90% interval. The coefficient is calibrated against the independently fitted SSM response --- amplification versus β₂ (≈ +0.74) and versus β₃ (≈ −0.45) --- with the SSM-unreliable wells shown as hollow markers ("shown, not fitted") and dropped from the calibration regression.

**Honesty note.** The coefficient is validated only where β₂ exists (long-record wells); short-record wells are both the use case and the place it cannot be directly verified. The tiers, jackknife CIs, and β₂/β₃ calibration are how that extrapolation is kept honest. Language throughout is "consistent with the fitted drainage/draw response", never "confirms".

**Outputs.** *outputs/35_amplification_metric/*: *35_per_well_amplification.csv* (coefficient, CI, confidence tier); the SSM-calibration figure; the discrete per-well marker map.

**Report location.** Main-report §5.7.5 (and Paper 1).

### []{#anchor-570}[]{#anchor-571}[]{#anchor-572}S.20.4 Script 36 --- Absolute climate-removed secular trend (Phase 15)

**Step 39/50, Phase 15. Added 2026-07-05 (v1.0.4); promoted to analytical tier (***exec=\"default\"***) 2026-07-13 per the Task E signed-off audit. Analytical tier. See the Pipeline-at-a-glance table and ***outputs/pipeline_manifest.json***.**

**Motivation.** Script 32's differential map (Figure 63) answers "where relative to the site", re-referencing every well to the network mean, which over a wet-spring-lifted window inverts the reading (the forest interior reads as rising because it amplifies the lifted mean, not because it is genuinely wetting). The MSL5 change map (Figure 62) is absolute but retains the common climate signal, so the whole site deepens together and spatial structure is masked. Script 36 fills the gap: an **absolute** per-well secular trend with the climate signal removed by an **external** index (spring CWB), not re-referenced to the network mean, so the real site-wide recharge decline and coastal drying survive while the inter-annual climate wobble is removed.

**Inputs.** *outputs/01_wells_clean.csv* (levels); *outputs/01_locations.csv* (Easting/Northing); *outputs/03_master_data.csv* (cluster ids); *outputs/01_climate.csv* (P_m, PET → spring CWB). The SSM is not re-fitted.

**Methodology.** A spring value is formed per well-year as the mean of the available March--May readings (*config.MSL_SPRING_MONTHS*, identical to Script 32). The external climate index is the spring climatic water balance, CWB(t) = Σ(P_m − PET) over March--May, contemporaneous with the spring level (no lag; *HEADLINE_LAG = 0*). For each well a single **joint** ordinary-least-squares model is fitted:

> h(t) = a + b · CWB(t) + c · t

and the secular trend is the fitted time coefficient c (mm yr⁻¹). Because CWB and time are fitted jointly, neither absorbs the other's variance: c is orthogonal to the climate term by construction. A two-step estimator --- regressing level on CWB and then fitting a trend on the residual --- was rejected: over a climatically non-stationary window the CWB series itself trends, and this absorbs the real secular drying before the slope is measured. Significance on c is a lag-1 autoregression-corrected t-test with residual degrees of freedom reduced for the three fitted parameters, cross-checked against a moving-block bootstrap that re-fits the full model each iteration; significant wells are drawn solid, non-significant wells hollow.

A **coverage filter** removes wells that cannot support a trend over the window: a well is included only if it has at least one spring observation before 2011 (the start of the shorter window) and its observed span covers at least 80 % of the window. Without this filter, short-record wells whose record begins after 2011 fit only a post-2011 drought-recovery trajectory and contribute spurious strong positive slopes. Two periods are fitted: **2005--2025 (primary)** and 2011--2025 (robustness); the longer window is primary because the shorter one is coverage-corrupted for many wells. Only the Llyn Rhos-Ddu lake gauge is excluded; CEH13 and CEH14 are retained (observational metric, independent of the SSM). The per-well trends are interpolated to the canonical 50 m grid via IDW (*map_utils.add_idw_surface()*, *hull_buffer_m = 100* so the surface extends 100 m beyond the well convex hull to reach the coastal margin) and clipped to the NNR site boundary.

**Headline result.** Over 2005--2025 the coastal-forest cluster (C5) has a mean climate-removed trend of −11.6 mm yr⁻¹ --- clearly negative and the most negative of the clusters, consistent with the coastal-retreat gradient (δ₀ ≈ −29 mm yr⁻¹ at the shoreline; C5 wells sit back from the edge so the cluster mean is smaller in magnitude). The forest interior no longer reads as strongly wetting once the coverage artefact and the mean-referencing of Figure 63 are removed. *Regenerate exact figures from 36_absolute_climate_trend_per_well.csv before quoting --- do not cache these numbers.*

Outputs.

  ----------------------------------------- -------------------------------------------------------------
  Output                                    Description
  36_absolute_climate_trend_per_well.csv    Per-well slope, CI, significance, CWB loading, both periods
  36_absolute_climate_trend_2005_2025.png   Primary map (report figure --- number TBC with Martin)
  36_absolute_climate_trend_2011_2025.png   Robustness map
  36_results.txt                            Summary statistics
  ----------------------------------------- -------------------------------------------------------------

All at *outputs/36_absolute_climate_trend/*.

**Limitations.** The metric is absolute but still an interpolation of point trends; the 100 m hull extension is bounded extrapolation over unmeasured coastal ground. The joint fit assumes the climate response and the secular trend are separable and linear over the window. The coverage filter trades coverage for reliability --- short-record wells are excluded rather than down-weighted.

**Report location.** Figure number TBC with Martin. Main-report §4.9.8 / §5.7.5, as the absolute companion to Figure 63 (Script 32 differential map). Pairs with the Script 20 modelled 2005→2025 driver-change map (*20_driver_change_2005_2025.png*) --- modelled versus observed over the same window. The per-well climate-sensitivity coefficient b̂ fitted here is the term that Script 37 (§S.20.5) removes when constructing its climate-corrected endpoint differences; Script 38 (§S.21.5) provides the one observational handle on δ₀ that triangulates with this figure's absolute-trend result.

### []{#anchor-572}[]{#anchor-573}[]{#anchor-574}S.20.5 Script 37 --- Driver validation (per-driver scale-factor regression)

**Step 40/50, Phase 15. Analytical tier (***exec=\"default\"***), promoted 2026-07-13 per the Task E signed-off audit.**

**Motivation.** Sections S.19--S.20 characterise each driver's *modelled* spatial field (forest canopy, scrape dipole, coastal retreat). Script 37 asks the complementary question: do those fields, at their modelled amplitudes, actually account for the observed climate-corrected change across the well network, and can their amplitudes be recovered independently from the data? It is a validation step, not a fitting step --- it does not set any driver amplitude used elsewhere.

Inputs.

  ------------------------------------------------- ----------------------------------- ---------------------------------------------------------------------------------------------------------------------
  Field                                             Source                              Detail
  Climate-corrected per-well endpoint differences   Script 36                           b̂ fitted on *ACT_BHAT_WINDOW = 2005--2017*; *h_corr = h − b̂·CWB*; endpoint means with *ACT_ENDPOINT_FRACTION = 1/3*
  Unit driver fields                                Script 20 v1.32.0                   *\_erosion_field*, felling-polygon clearfell shape, *\_broadleaf_field*; imported live
  δ₀, L                                             Script 25 *OUT_25_FIT_PARAMETERS*   Forest-free linear-capped fit; δ₀ = −29.03 mm yr⁻¹
  Clearfell step                                    10a_report_numbers.csv              ANCOVA Path B, +119.6 mm observed
  ------------------------------------------------- ----------------------------------- ---------------------------------------------------------------------------------------------------------------------

No raw inputs; no hard-coded amplitudes.

**Methodology.** For each analysis window the observed climate-corrected change dh_corr,i is regressed on the driver fields as separate regressors at their modelled amplitudes, with a **free spatially-uniform intercept**:

> dh_corr,i = s_coast·coast_i + s_cf·clearfell_i + c + ε_i

Each field is β₃-corrected per well so a scale factor is dimensionless --- s = 1 means the aquifer feels exactly the modelled amplitude. The intercept c absorbs the site-wide β₁-recharge decline so that a uniform background drying cannot be laundered into s_coast. Three windows: 2006--2012 (pre-intervention: coast + intercept), 2018--2025 (coast + clearfell + intercept), 2005--2025 (full record). Inference is OLS with HC3 robust standard errors. The coastal amplitude per window is δ₀ · Δt_mid · shape, with Δt_mid the span between endpoint-group centroids. An expanding-window run yields an implied-δ₀(t) trajectory as an independent temporal check.

**Site-specific choices and rationale.** **C2 Dune** is the negative control: its wells carry no coastal or clearfell field, and their near-zero mean residual (−1.8 mm full-record) is the internal check that the climate correction is unbiased on driver-free wells. **C1 Lake Edge is excluded from the fit** --- Llyn Rhos-Ddu's level is sluice-controlled (*ACT_FIT_EXCLUDE_CLUSTERS = (\"C1\",)*), so those wells report management, not natural forcing. Excluding them shifts every coefficient by less than 0.15 of its standard error. The 2015--2017 scrape window is not regressed (3 points, unidentifiable); scraping is owned by the BACI evidence. Broadleaf enters only as an optional 2018--2025 covariate, never a headline factor.

**Outputs.** *outputs/37_driver_validation/*: *37_scale_factors_by_window.csv* (per-window s_coast, s_cf, c with HC3 CIs, R², n); *37_driver_validation_per_well.csv*; predicted-vs-observed and residual maps; *37_implied_delta0_trajectory.png*; *37_results.txt*.

**Limitations and known caveats.** The result is a **bounded null on attribution**, and should be stated as such. Every scale-factor CI spans zero (s_coast 0.53 \[−0.12, 1.18\] full-record), because only \~15 wells sit within the coastal field's reach and \~12--20 within the clearfell field, the two fields are collinear (r ≈ −0.48 with easting), and per-well residual scatter (±150--200 mm) exceeds the driver amplitudes. The only tightly-determined term is the uniform intercept (−559 mm through the 2006--2012 drought; +90 mm post-2017), so the dominant, resolvable component of change is common-mode, not driver-shaped. The coastal *shape* (δ₀, L) is fitted from the same network (Script 25), so the spatial test is partly self-confirming; the implied-δ₀(t) trajectory is the only independent check and it is too drought-contaminated to be conclusive. Script 37 does not resolve scraping, does not close the coastal budget, and cannot separate coastal erosion from the collinear clay-dip substrate gradient --- only characterise the change as dominated by a common-mode background against which the modelled coastal field cannot be independently confirmed.

**Where it appears in the report.** ⟨§5.7 --- coastal driver subsection⟩: the modelled coastal field is carried as modelled-and-unconfirmed on the strength of this result; the common-mode dominance supports the site-wide recharge-decline reading.

### []{#anchor-574}[]{#anchor-575}[]{#anchor-576}S.20.6 Script 37b --- Comparative driver footing (Part B)

**Step 41/50, Phase 15. v1.0.1 (2026-07-07); promoted to analytical tier (***exec=\"default\"***) 2026-07-13 per the Task E signed-off audit. Analytical tier.**

**Motivation.** The report weighs interventions and natural processes against one another, but the drivers are mechanistically incommensurate (equilibrium suppression vs local redistribution vs progressive accumulation). Script 37b places forest, scraping and coast on a common footing by expressing each in three shared currencies over a common 2005→2025 horizon, so the comparison is explicit rather than rhetorical.

**Inputs.** The Script 20 unit fields at 2025 amplitude; observed anchors (clearfell +119.6 mm from *10a_report_numbers.csv*; scrape on-site +129.4 mm and off-site −54.5 mm from the scraping BACI/DiD outputs; δ₀ and L from Script 25); Sy = 0.311 (C3, read live from Script 17's cluster table); Curreli (2013) summer thresholds (wet-slack SD15b −0.61 m, dry-slack SD16 −0.98 m); the observed summer-minimum baseline per well. **Script 37b uses observed anchors and modelled fields --- never Script 37's scale factors**, which are null.

**Methodology.** Each driver enters as a *gain* and a *loss* component (forest = clearfell + broadleaf restock; scrape = on-site rise + off-site drain cone; coast = sea-level rise + erosion drawdown), because all three are two-sided. Three currencies: (1) **peak local head change** --- one number per component; (2) **area-integrated change** --- each field integrated over the site mask, in mm·ha and in m³ via Sy; (3) **ecological threshold crossings** --- each field added to the observed per-well summer-minimum baseline, counting wells crossing the Curreli thresholds. A mechanism-type column (step / redistributive / progressive) keeps the currencies from implying the drivers are the same kind of quantity.

**Site-specific choices and rationale.** Per-driver representative Sy (C3 0.311 for scrape/coast) rather than per-cell, for traceability, with the ±40 % Sy spread noted. Threshold crossings are computed per-well (not per-area) to avoid double interpolation. The scrape is reported as rise, drain and **net** separately, because the net integral is the quantitative basis for the "scraping worsens the site-wide table while benefiting the slack" claim.

**Outputs.** *outputs/37b_driver_footing/*: *37b_driver_footing.csv* (component × currency, with mechanism-type and observed/modelled flags); comparative figure. Headline values: coastal erosion peak −580.6 mm, area −74,291 mm·ha, volume **−227,108 m³**, six dry-slack wells worsened; scrape on-site +129.4 mm (613 mm·ha) but off-site −54.5 mm (−21,470 mm·ha), net **−63,759 m³**, five dry-slack wells worsened vs one relieved; clearfell +119.6 mm, **+17,132 m³**, the only unambiguous net relief (three dry-slack wells un-crossed); broadleaf −10,339 m³; SLR +8,619 m³. *Regenerate from the committed CSV before quoting --- do not cache these numbers.*

**Limitations and known caveats.** First-order linear superposition --- an upper bound in overlap zones, the same caveat as the Script 20 map. The coastal figures (both components) are **modelled** and, per Script 37, spatially unconfirmed; the scrape near-field cone is modelled and unresolvable (nearest uphill well 247 m); clearfell and scrape on-site/off-site points are observed. The currency-conversion assumptions use a representative Sy, not a per-cell value; the ±40 % spread on C3 Sy propagates to the volume figures. The "scraping worsens site-wide" result is reported *with its magnitude set against the coastal integral* --- a real net loss, but a fraction of coast's --- so it should not be read as a headline driver.

**Where it appears in the report.** ⟨§5.8 --- the comparative-footing summary⟩, as the anchor for the even-handed treatment of interventions and natural processes, alongside the spatial-reach comparison figure.

End of chapter S.20.

## []{#anchor-576}[]{#anchor-577}[]{#anchor-578}S.21 Scripts 24b, 31, 31b, 34, 38 --- Supplementary standalone diagnostics

Phase 16 (steps 42--46/50; the first three opt-in --- *\--with-supplementary* --- the last two running by default). Five standalone diagnostics wired into the orchestrator so they regenerate whenever upstream data change, each addressing a specific robustness question raised elsewhere in the analysis: the mechanism behind the seasonal SSM residual (Script 24b), whether the k=5 partition is corroborated by evidence the clustering never used (Scripts 31 and 31b), whether the two-window MSL5 method can resolve absolute site-wide change (Script 34), and whether the coast-to-inland MAM head gradient is growing (erosion-consistent) or static (substrate-geometry) as a model-free corroboration of the coastal-retreat rate δ₀ (Script 38). None re-fits the SSM; all read committed pipeline outputs.

### []{#anchor-578}[]{#anchor-579}[]{#anchor-580}S.21.1 Script 24b --- Cluster-stratified residual climatology

**Motivation.** Script 24 reports a seasonal structure in the SSM residual field. Three mechanisms could produce it, each with a distinct spatial signature: (1) winter-phased nonlinear recharge that the linear β₁·P term under-represents in heavy-rainfall months --- site-wide, including the open dune; (2) ridge-derived lateral input from the metamorphic bedrock ridge to the north --- ridge-proximal, concentrated at C4 and forest-margin wells; (3) over-estimation of the F = 0.24 canopy-interception correction in winter --- forest-confined, at both C4 and C5. Script 24b discriminates among them; it does not pre-judge.

**Inputs.** The per-well per-month SSM residuals (Script 22), the cluster assignment and Easting/Northing (Script 03 master data), and the "Forest" KML polygon (for distance-to-forest-edge). The SSM is not re-fitted.

**Methodology.** The residual climatology is stratified across the k=5 partition; the discriminant is the per-cluster winter-minus-summer residual contrast together with a within-forest ridge-distance gradient. A site-wide contrast points to mechanism (1); a contrast concentrated at C4 with a ridge-distance gradient points to (2); a contrast shared by C4 and C5 without a ridge gradient points to (3). Reported neutrally.

**Outputs.** *outputs/24b_residual_climatology/*: *24b_01_cluster_climatology.csv* (per-cluster mean residual by month) and the accompanying diagnostic figures.

**Report location.** Supports the discussion of the SSM residual field and the ridge-recharge hypothesis in the main report; supplementary diagnostic, not a headline result.

### []{#anchor-580}[]{#anchor-581}[]{#anchor-582}S.21.2 Script 31 --- Independent k=5 partition validation

**Motivation.** The canonical clusters are formed in Script 02 by Ward's linkage on (1 − Pearson correlation) distance between well hydrographs. Script 31 asks whether that partition is corroborated by evidence the clustering never used, organized by how independent each line of evidence actually is.

**Methodology.** Four tiers. Tier 1 (external): data orthogonal to the hydrographs --- geography, the forest-canopy polygon, distance-to-coast, elevation. Tier 2 (metric-independent): magnitude descriptors of the hydrographs --- mean depth, amplitude, summer minima, dry depth --- which are largely orthogonal to the correlation (shape/timing) structure the clustering used. Tier 3 (convergent): the same water-level series via a different estimation method --- SSM betas, WTF Sy, LCSC --- supporting but not independent. Tier 4 (robustness): whether k=5 survives a different linkage or distance metric (average, complete; Spearman, DTW), measured by the Adjusted Rand Index against the canonical Ward+Pearson partition. All canonical numbers are read from live pipeline CSVs.

**Outputs.** *outputs/31_cluster_validation/*: *31_validation_summary.csv* (one row per test --- tier, statistic, p, independence); *31_method_robustness_ari.csv* (ARI of each alternative clustering vs canonical); *31_forest_confusion.csv* (cluster × forest-polygon crosstab + Cohen's kappa); *31_forest_borderline.csv* (wells within the edge band, signed distance); *31_cluster_validation_panel.png* (4-panel figure).

**Report location.** Supports the k=5 cluster-framework justification in the main report (§4.2 / §5.1); supplementary diagnostic.

### []{#anchor-582}[]{#anchor-583}[]{#anchor-584}S.21.3 Script 31b --- Cluster separation versus recoverability

**Motivation.** A standalone companion to Script 31 making one point with one figure: the clusters differ on the independent variables (so they are real), but those variables do not by themselves reconstruct the clusters (because the hydrograph timing carries information no static attribute holds). High separation does not imply high recoverability.

**Methodology.** For each independent variable X the figure places side by side a separation statistic --- η², the variance in X explained by the pre-formed partition ("do the clusters differ on X?") --- and a recoverability statistic --- the Adjusted Rand Index of a fresh Ward k=5 clustering on standardized X against the canonical partition ("does X alone rebuild the clusters?"). Distance-to-coast is taken to the Caernarfon Bay mean-high-water shoreline (the Menai Strait excluded), from the consolidated well metadata.

**Outputs.** *outputs/31_cluster_validation/*: *31b_separation_vs_recoverability.csv*; *31b_separation_vs_recoverability.png*.

**Report location.** Companion to Script 31; supplementary diagnostic.

### []{#anchor-584}[]{#anchor-585}[]{#anchor-586}S.21.4 Script 34 --- MSL5 two-window sensitivity demonstration

**Step 45/50, Phase 16. Analytical tier (***exec=\"default\"***), promoted 2026-07-13 per the Task E signed-off audit.**

**Motivation.** A deliberate cautionary demonstration: how strongly an apparent "site-mean water-table change" depends on which two five-year spring windows are differenced. The §4.9.8 headline differences window-end 2017 against window-end 2023 and reports −96.8 mm; Script 34 places that single comparison inside the envelope of every admissible window pair, so §5.7.5 can show from a committed, reproducible figure that the two-window MSL5 method cannot resolve absolute site-wide change.

**Inputs.** The committed per-well annual spring MSL (*outputs/26_van_willegen_msl/26_msl_annual_per_well.csv*, column *MSL_m_bg*), valid rows only; the committed annual climate summary (for the window-axis rainfall-deviation annotations). Exclusions: *config.MSL5_EXCLUDED_WELLS* (CEH13, CEH14), matching Script 26.

**Methodology.** Per-well MSL5 for a window ending in year Y is the mean of the well's annual spring MSL over years Y−4 to Y; a well qualifies only if all five spring-years are present. For each ordered pair (Wi \< Wj) the site-mean change is the mean over the common panel (wells qualifying in both windows) of the per-well (Wj − Wi) change --- the panel is held fixed across the pair, so composition change cannot inflate it. A pair is admissible when its common panel reaches *config.MSL5_WINDOW_MIN_PANEL = 40* wells, which excludes only the thin seven-well 2005--2009 baseline, so the spread arises from window choice alone. All admissible pairs are retained, including those whose current window contains the anomalously wet 2024 spring --- admitting them is the point of the demonstration.

**Headline result.** The site-mean change spans −0.14 to +0.22 m (−136 to +221 mm) across the 66 admissible pairs and changes sign --- 19 falling, 47 rising. The 2017→2023 pair reproduces the −96.8 mm headline (it returns −96.5 mm, n = 60; a one-well coverage-rule nuance). The most negative pairing is 2017→2020 (−136 mm) and the most positive 2015→2024 (+221 mm).

**Outputs.** *outputs/34_window_sensitivity/*: *34_window_matrix.csv* (every admissible pair: baseline-end, current-end, change, n_common, admissible); *34_results.txt* (anchor check, envelope range, sign split); *34_window_sensitivity.png* (Panel A all-pairs matrix; Panel B site-mean spring trajectory with interannual SD).

**Limitations.** Panel B's own-panel OLS trend is descriptive; the canonical secular trend is Script 32's AR-corrected −7.0 mm yr⁻¹ (p = 0.52), and both are non-significant. The demonstration deliberately admits the wet-2024 windows, so the envelope is wider than a "defensible-windows" subset would give --- that is the intended message, not a defect.

**Report location.** Main-report §5.7.5 (window-sensitivity figure).

### []{#anchor-586}[]{#anchor-587}[]{#anchor-588}S.21.5 Script 38 --- Coast-to-inland MAM transect (observational δ₀)

**Step 46/50, Phase 16. v1.3.0 (2026-07-08, wired into ***run_analysis.py*\*\* --- previously standalone); promoted to analytical tier (***exec=\"default\"***) 2026-07-13 per the Task E signed-off audit. Analytical tier.\*\*

**Motivation.** Script 37 could not confirm the modelled coastal field spatially. Script 38 takes a different, model-free route: a single coast-to-inland transect, viewed through time, tests whether the coast-to-inland head *gradient grows* --- which only a moving coastal boundary (erosion) can produce; a static substrate geometry gives a constant offset. It is the one observational handle on δ₀ the network affords.

**Inputs.** MAM spring-mean water levels (m AOD) for the transect wells, from *01_wells_clean.csv*; δ₀ and L from Script 25 (*25_01_panel_fit_parameters.csv*) for comparison. No modelled fields.

**Methodology.** A line running coast→inland (bearing ≈ 45° SW→NE): coastal anchor **CEH22** (SD13, most coastal), interior **NW5**, inland anchor **NW4** (\~1 km inland, outside the L ≈ 894 m drawdown band); CEH40 and CEH41 are annotated profile-only points (Feb-2013 eastern-scrape offset, never in the metric). The headline metric is the coast-minus-inland MAM head difference *h_CEH22 − h_NW4* per year, fitted with an AR(1)-corrected OLS trend --- a model-free observational estimate of δ₀. The climate-corrected profile panel anchor-references every well to the erosion-free inland anchor NW4, stripping common-mode climate without a model.

**Site-specific choices and rationale.** The window is computed from data coverage as the later of the CEH22 / CEH41 first-valid MAM (≈2010) to the last MAM before the Oct-2023 western scrape --- a clean ≈2010--2023, n = 14. CEH22 is retained over the longer-record coastal wells CEH17/CEH19 deliberately: those sit near the forest margin and would import forest signal onto a line meant to isolate the coastal gradient. The clearfell is not excluded because the felled compartment is in the western forest and propagates south-westward, not onto this open-dune transect (a site-geography argument specific to this transect).

**Outputs.** *outputs/38_coastal_transect/*: *38_coast_inland_difference.jpg* (the δ₀ headline figure); *38_transect_profile.jpg* (two-panel: raw and climate-corrected); *38_transect.csv*; *38_results.txt*.

**Limitations and known caveats.** Trend −28.16 mm yr⁻¹, 95 % CI \[−34.23, −21.98\], n = 14 --- sitting essentially on the modelled δ₀ (−29.03 mm yr⁻¹ from Script 25). The coast falls −21.9 mm yr⁻¹ in absolute terms; the inland anchor is near-flat, so the divergence is the coast dropping, not the inland rising. Anchor-referenced coastal-end ordering Spearman −0.873 (raw −0.321), and spring CWB does not trend over the window (VIF ≈ 1.0), so the metric is not a disguised climate trend. Caveats: n = 14, so a jackknife shows the *magnitude* robust (all leave-one-out slopes −19 to −37 mm yr⁻¹) but formal significance is borderline on shorter sub-windows; one line and four/five wells, so a *growing* gradient is erosion-specific but a *flat* one would mean erosion is undetectable *here*, not absent; a growing gradient separates erosion-like from substrate-geometry-like, but not erosion from a *time-varying* substrate effect. The result is stated as *consistent with* the modelled δ₀, independently and observationally --- not as confirmation. The cored SW--NE transect remains the mechanism-resolving test.

**Where it appears in the report.** ⟨§5.7 --- coastal driver subsection⟩, as the one observational support for the modelled coastal field and the lead-in to the cored-transect structural prediction.

End of chapter S.21.

## []{#anchor-588}[]{#anchor-589}S.22 Script 39 --- SSM hindcast against the 1989--96 CCW record

**Step 47/50, Phase 16 in ***run_analysis.py***. Analytical tier (***exec=\"default\"***). The step skips cleanly when the historic inputs are absent, so a default full run cannot fail over an optional raw input.**

### []{#anchor-590}[]{#anchor-591}Motivation

Every other test of the state-space model in this corpus lies inside the window the model was fitted on. Script 39 is the one that does not. It predicts monthly water-table levels over May 1989 to April 1996 from RAF Valley climate alone, using per-well coefficients fitted over 2005--2026 by Script 03, and compares the prediction with the dipwell record of the Countryside Council for Wales (CCW) monitoring block. The comparison is against levels rather than against a rate, so unlike a trend comparison it does not depend on the network resolving a rate --- which, as §5.7.7 of the main report sets out, it does not.

A second question is older than the model. The water table of the early 1990s was recorded as depressed, and that depression has been read since as a forest signal, a drought signal, or a compound of the two that the data of the day could not separate. The hindcast supplies the climate-only expectation directly, and the residual between it and the observation is the part climate does not explain. The script computes and emits that residual per month. It does not attribute it: attribution needs the canopy state of 1989, which is not observed.

### []{#anchor-592}[]{#anchor-593}Data provenance and permission

The 1989--96 dipwell records are held by Natural Resources Wales and were supplied for this study. Access is covered by the Environmental Information Regulations 2004; re-use and republication are separate matters, governed by whatever licence attaches. Written confirmation of those terms has been sought and was outstanding when this chapter was written, and the chapter is reported on that basis. The derived results below are this study's own; the underlying records are not.

### []{#anchor-594}[]{#anchor-595}Inputs

Read via *utils.paths*: *data/ccw_1989_1996_depths.csv* (the CCW Wells block as tidy rows --- month, reading date, code, depth, censoring flag); *data/ccw_1989_1996_code_map.csv* (code, well, status, datum offset and the evidence for each assignment); *01_climate.csv* (monthly P and PET in m/month); *03_master_data.csv* (per-well β₁, β₂, β₃); *01_locations.csv* (ground elevation); and *01_wells_clean.csv* (modern levels, for the epoch contrast). The committed canopy history is an optional input: absent, the canopy columns come back blank and nothing else changes.

**The raw-input exception.** The two historic files are raw inputs that no pipeline step produces. Scripts other than Script 01 do not read raw CSVs without a documented exception, and this one is recorded as D-051 in the Decision Log. The record basis is RB-14 in *tools/record_basis.csv*, which records the evaluation basis only: this step fits nothing. The coefficients are read from Script 03's committed output and applied forward, so the basis of the coefficients is Script 03's and the basis recorded here is the window over which they are evaluated.

### []{#anchor-596}[]{#anchor-597}Datum

Historic depths are carried onto the modern ground datum by a per-well offset held in the code map. Where it is derivable, the offset is the 1989 ground elevation implied by the workbook's own derived level columns, less the committed DGPS value; it is derivable at four of the admitted wells and is at most 0.061 m. This is equivalent to reducing the original dip against today's measured upstand provided the pipe has not moved --- a construction the size of the offsets supports and nothing available here can prove. The raw dips are not in the workbook, so the implied-ground route is the only one open. Wells with no derivable offset are carried unadjusted and the fact travels with the result.

### []{#anchor-598}[]{#anchor-599}Censoring

Readings at the pipe base (*config.CCW_PIPE_BASE_M* = −2.000 m) are left-censored rather than missing: the water table was at or below the bottom of the pipe, and the reading records the pipe rather than the aquifer. Including them would bias the comparison toward the model, so they are dropped from every metric and counted in the output. A code is admitted only when fewer than *config.CCW_MAX_CENSORED_FRACTION* (0.25) of its months are censored. One admitted well, wmc3, has fifteen of its eighty-two months at the pipe base and is compared on the remaining sixty-seven.

### []{#anchor-600}[]{#anchor-601}The admission gate

Codes are mapped to wells through the committed code map, which carries a status per code, so a mapping question is settled in a committed file rather than in code. Of the thirteen historic codes, twelve are mapped to present wells and one (2A) was never identified. Nine are admitted, and the four exclusions are written into *39_results.txt* with a reason each: 1A (nw12) and 2D (nw8) have no committed coefficient triple, 1B (nw10) is censored in sixty-three of its eighty-two months, and 2A has no mapping. Wells nw8 and nw12 have historic records but no modern fit --- nw8's modern record ends in 2015 and nw8b succeeds it, and nw12 has no modern record at all.

### []{#anchor-602}[]{#anchor-603}Methodology

**Forcing and spin-up.** The recurrence is driven from the start of the committed RAF Valley record, December 1930, so the initial condition is forgotten long before the comparison window opens. The spin-up runs 701 months. This is reported rather than assumed: restarting from the equilibrium head displaced across the probed range (*config.CCW_H0_PROBE_OFFSETS_M*) changes the comparison window by at most 3 × 10⁻¹¹ m, and by exactly zero at four of the nine wells.

**Recurrence.** *utils.model_utils.simulate_ssm* --- the shared implementation, not a local copy. Coefficients are read per well from the committed master data. Nothing is refitted, and no parameter is free to absorb the difference between the epochs.

**Bucketing.** Historic readings are assigned to months by the project rule --- a reading on day 15 or earlier belongs to the previous month. Every one of these readings falls on day 14 or earlier, so each moves back one month and no month receives two readings.

**Canopy.** Each well's 1989 canopy state and felling year are joined from the committed canopy history and travel with its result. The modern land-cover flag answers whether a well is under canopy now, which is the wrong question for a 1989--96 comparison: several of these wells were felled around 1995 and one in 2017, so their fitted coefficients describe a canopy that did not exist over the window being hindcast. Open-ground and under-canopy wells are reported apart in every output and are never pooled.

**Reading r against NSE.** The correlation r asks whether the hindcast reproduces the shape of the record --- the timing and size of the seasonal and interannual swing. Nash--Sutcliffe efficiency additionally penalises the level. A well with high r and poor NSE has the dynamics right and the datum wrong, which is a statement about the record rather than about the model, so the script emits the bias-removed NSE alongside the NSE and the two are read together.

### []{#anchor-604}[]{#anchor-605}Sensitivity to β₁

The coefficients are fitted over 2005--2026 and the corpus establishes a site-wide β₁ decline, so the 1989 value was plausibly higher than the fitted one. Run at the fitted value alone, the hindcast would under-predict recharge and place the table too deep. The direction is knowable, so the script reports metrics across *config.CCW_BETA1_SCALINGS* rather than a single number, and keeps the two canopy groups apart. Over the six open-ground wells the mean NSE runs +0.235 at the fitted value, +0.306 at a 3 % scaling, +0.012 at 6 % and −0.949 at 10 %, with the mean bias passing through zero between the first two (−0.069 m and +0.057 m). Over the three canopy wells the mean NSE is negative at every scaling and falls monotonically, from −1.473 to −9.247. The open-ground optimum is shallow and sits below the scaling implied by the independently established β₁ decline, so the result is consistent in direction and order of magnitude with that decline and is not a measurement of it. It is worth recording because the two routes are wholly independent.

### []{#anchor-606}[]{#anchor-607}Outputs

*outputs/39_ccw_hindcast/*: *39_01_hindcast_per_well.csv* (per well --- months compared, censored count, canopy state, coefficients, datum offset, spin-up length, initial-condition sensitivity, observed and predicted means, NSE, RMSE, bias, r, bias-removed NSE, modern mean and epoch shift); *39_02_hindcast_series.csv* (observed, predicted and residual, monthly, per well); *39_03_beta1_sensitivity.csv* (metrics across the scaling range, grouped by canopy state); *39_04_hindcast.png* (observed against predicted, one panel per well); and *39_results.txt* (the console summary, including the exclusions and their reasons).

### []{#anchor-608}[]{#anchor-609}Headline results

The model reproduces the shape of the historic record. Across the nine admitted wells the observed-to-predicted correlation has a median of 0.859 and runs from 0.660 at nw11 to 0.945 at nw5. It reproduces the level less reliably, though the error is small: NSE is negative at five of the nine, while the bias-removed NSE at those same wells reaches 0.35 to 0.87 --- the signature of a model that has the dynamics and the datum only approximately. The mean residual (observed less predicted) is −0.057 m across the nine wells and +0.069 m across the six cleanest, so the prediction falls either side of the record rather than consistently to one side of it.

The epoch shift is the level contrast between the two records: each well's 1989--96 mean less its modern mean. All nine are negative, from −0.132 m at wmc2 to −0.835 m at nw11, with a network median of −0.582 m. The direction is the same at every well --- the water table of the early 1990s stood lower than it stands today.

Six of the nine wells were open ground in 1989 and are open ground now, and they carry the cleanest signal: a median correlation of 0.910, a median bias-removed NSE of 0.818 and a median epoch shift of −0.338 m. The remaining three either changed canopy state or sat under canopy throughout, and both their fits and their shifts are worse. The well that has been forest across both epochs, nw11, is simultaneously the poorest fit in the set and the largest shift, which is what a model carrying a modern canopy state would produce.

That contrast is very largely climate, and the forcing says so before the model is consulted. The comparison window is the driest sustained stretch in the ninety-five-year RAF Valley record: rainfall averages 0.770 m yr⁻¹ over 1989--96 against 0.886 m yr⁻¹ over the modern record, and the surplus of rainfall over potential evapotranspiration is +0.127 m yr⁻¹ against +0.237 m yr⁻¹. A lower table in those years is what climate alone predicts, and the hindcast, which knows nothing else, produces it. What is left over at the six open-ground wells is +0.069 m against a contrast of −0.338 m. The shift is therefore a contrast between a dry epoch and a wetter one; its direction is a recovery rather than a decline, and it neither contradicts nor corroborates the declines reported inside the modern record.

### []{#anchor-610}[]{#anchor-611}Limitations

Coefficient stationarity is assumed and the corpus contradicts it; the β₁ scan above is the response, and it bounds the effect rather than removing it. The 1989 canopy state is not observed, so the under-canopy group rests on an assumption the open-ground group does not require, and the two are never pooled. The epoch shift is a level contrast and should be read as one: dividing it by the twenty-three years separating the midpoints of the two records assumes a straight line across years that hold no observations, and two windows cannot say what happened between them. The quotient is not a rate and must not be reported as one, in either direction. The residual is emitted per month and is not attributed. Two historic records, nw8 and nw12, cannot be used at all for want of a modern fit.

### []{#anchor-612}[]{#anchor-613}Report location

Main-report §5.7.8 (out-of-sample test against the 1989--96 record), which reports the result and the provenance note; §5.7.7 sets out the record-length argument the test sits inside.

End of chapter S.22.

## []{#anchor-614}[]{#anchor-615}[]{#anchor-616}S.17 Appendices

Reference and post-pipeline material. Final chapter of the supplement.

This chapter closes the Methods Supplement. It covers two pieces of material that belong with the document but sit outside the main script-by-script chapter sequence (S.1--S.18b). Appendix A documents the one remaining pipeline script not yet given a chapter --- the post-pipeline greyscale figure utility. Appendix B is the canonical-sources index: a reference table mapping each recurring concept across the supplement to the place where it is authoritatively defined.

### []{#anchor-616}[]{#anchor-617}[]{#anchor-618}A. Greyscale figure post-processing --- Script 27

*27_greyscale_figures.py* is a post-pipeline rendering utility, not an analytical step. It exists to produce a journal-ready black-and-white bundle of the pipeline's colour figures without re-running any analytical script. Reviewers, journal proofs, and print compatibility occasionally require this; the conversion runs once and produces a parallel *outputs_bw/* tree alongside the canonical *outputs/* tree, preserving the directory structure so that any figure has the same relative path in both.

The script offers two conversion modes. The default uses ITU-R BT.709 perceptual luminance weights (0.2126 R + 0.7152 G + 0.0722 B), preserving the alpha channel where present and compositing onto white first to avoid grey halos around transparent edges. This is the right choice for line plots, bar charts, scatter plots, and most hydrograph figures --- the kind of figure whose informational content is in shape and position rather than colour. The *\--enhanced* mode applies contrast-limited adaptive histogram equalisation (CLAHE-style auto-contrast with a 0.5 % cutoff, plus light sharpening) on top of the luminance conversion. It is intended for figures where the colour palette compresses into a narrow luminance range, typically diverging colormaps on spatial maps.

Two classes of figure do not survive naive greyscale conversion and are flagged in the output with *\[REVIEW\]*. Script 11b's categorized ecological-zone maps (*11b_01_summer_minima_depth*, *11b_02_winter_maxima_depth*, *11b_03_pflood*) use four or five colour bands that collapse to similar mid-greys under any luminance transform --- distinguishing them in print needs native B&W rendering with hatched zones rather than post-processing. The Script 19 difference maps (*difference_maps/diff\_\**) use diverging RdBu colormaps with colourbar labels reading "blue = wetter / red = drier" baked into the raster; the labels become meaningless in greyscale and cannot be post-edited. Both classes are still converted by default (the output is usable, just suboptimal), and *\--exclude-problem* skips them entirely.

The CLI is

python src/27_greyscale_figures.py \[\--enhanced\] \[\--dpi DPI\] \[\--skip-maps\]

\[\--exclude-problem\] \[\--dry-run\]

with *\--dpi* overriding the source DPI, *\--skip-maps* excluding the spatial-map outputs that benefit from manual review, and *\--dry-run* listing the files that would be converted without writing anything. Script 27 is orchestrated by *run_analysis.py* as PHASE_17 (step 49/50) but is a post-analysis utility rather than an analytical step --- it is display/utility rather than analytical and lives here in Appendix A. The script is idempotent: deleting *outputs_bw/* and re-running rebuilds it cleanly.

Script 27's filename prefix (*27\_*) and orchestrator step number (49/50) deliberately do not match --- the same convention applied to Script 26 (*26_van_willegen_msl.py* at step 30/50), Script 26b (*26b_van_willegen_msl_projections.py* at step 31/50), Script 26c (*26c_msl5_report_figures.py* at step 32/50), Script 09f (*09f_management_effects.py* at step 47/50), and Script 09g (*09g_mechanism_diagrams.py* at step 48/50). The filename groups Script 27 alphabetically with the other *2x\_* scripts; the orchestrator number reflects its position in the run order at the end of Phase 17. Script 27 carries no analytical-step number of its own --- it is the post-analysis utility documented in this appendix. Script 26c, the MSL5 report-format figure-rendering companion, is similarly display/utility and is documented in §S.18c. Script 09f, the spatial-reach synthesis figure, is also excluded and is documented in §S.15c. Script 09g, the mechanism-diagram companion to 09f, is likewise excluded and is documented in §S.15d.

### []{#anchor-618}[]{#anchor-619}[]{#anchor-620}B. Canonical sources of truth --- reference table

The supplement is long enough that a reader who has read it once and needs to find where a particular concept, parameter, or function is defined will not always remember which chapter to open. This table is the navigational index. For each recurring concept, it points to the single canonical source --- a chapter, a front-matter section, or a specific file in the repository --- where the concept is defined and explained. Where a constant is read from *config.py*, the table names the constant; where a function is the canonical implementation, it names the module.

The convention throughout the supplement is that there is one place to change a value and one place to look it up. The table reflects that. Entries are organized into thematic groups --- model formulation, partition and cluster constants, intervention machinery, scenario engine, ecological thresholds, spatial machinery, MSL aggregation, and provenance and orchestration.

#### []{#anchor-620}[]{#anchor-621}Model formulation

  ------------------------------------- ----------------------------------- --------------------------------------------------------------------------------------
  Concept                               Reference                           Definition / value
  SSM equation                          F.3                                 Δh(t) = β₁·P(t) − β₂·PET(t) − β₃·(z₀ + h(t−1))
  SSM displacement formulation          F.3                                 h_disp = DRAINAGE_DATUM + h_depth
  DRAINAGE_DATUM = 3.7 m                F.4 / *config.py*                   Sensitivity analysis in Script 03 (*03_08_datum_sensitivity.csv*)
  HEADLINE_LAG = 0                      F.4 / *config.py*                   Contemporaneous rainfall; lag-1 regime is historical
  Bucketing convention                  F.2                                 Day ≤ 15 → previous month; day \> 15 → same month
  Sign conventions                      F.3                                 All three β reported positive; sign baked into design matrix
  MIN_OBS = 30                          F.5 / *config.py* (*SSM_MIN_OBS*)   Minimum aligned rows for any per-well SSM fit; re-exported by model_utils as MIN_OBS
  LCSC_DATA_LIMIT = 100                 F.5 / *config.py*                   Per-well fitting window (Scripts 03, 08, 30); centroid fits use the full record
  assert_physical_signs()               F.3 / F.5 / *model_utils.py*        Hard violations (β₁≤0, β₂≤0); soft warnings (β₃≤0)
  build_ssm_frame()                     F.3 / F.5 / *model_utils.py*        Canonical data alignment; no script reimplements
  *fit_ssm()* / *fit_ssm_intercept()*   F.3 / F.5 / *model_utils.py*        No-intercept (Model A, headline) / with-intercept (Model B, diagnostic)
  simulate_ssm()                        F.5 / *model_utils.py*              Forward simulation with displacement recurrence
  Two regimes (A / B)                   F.3 / S.5                           Model A is the headline; Model B used by Scripts 07, 08, 22, 24
  ------------------------------------- ----------------------------------- --------------------------------------------------------------------------------------

#### []{#anchor-621}[]{#anchor-622}Partition and cluster constants

  ------------------------------------------------------------ ---------------------------------------------------- -------------------------------------------------------------
  Constant / concept                                           Reference                                            Value / meaning
  *CLUSTER_LABELS* (C1--C5)                                    F.4 / *config.py*                                    k=5 Ward's partition
  *CLUSTER_COLOURS*, *CLUSTER_COLOURS_BW*, *CLUSTER_MARKERS*   F.4 / *config.py*                                    Canonical palette and B&W equivalents
  CLUSTER_ID_ANCHORS                                           F.4 / *02_clustering.py*                             Pins Ward's raw output to canonical IDs
  Anchor wells per cluster                                     F.4 / *config.py*                                    C1: ceh5, ceh11; C2: d10; C3: nw1; C4: ceh2; C5: ceh16, nw9
  Reference network (66 wells)                                 S.2 / *01_data_prep.py*                              REFERENCE_CUTOFF_DATE = \"2026-02-01\"
  Identity-vs-integer keying principle                         F.4                                                  Survives partition changes if applied correctly
  Partition history (k=6 → k=5)                                F.4                                                  Old C5 ≠ new C5; Lake cluster dropped as singleton
  Cluster β coefficients                                       S.3 / *03_master_data.csv*                           Per-well β₁, β₂, β₃; canonical source for downstream
  Per-cluster mean β coefficients                              S.3 / *03_03_cluster_mechanistic_coefficients.csv*   Used by Scripts 07, 11, 16, 19, 21
  *BW_MODE* rendering                                          F.4 / *config.py*                                    Toggled by *NRG_BW_MODE* environment variable
  ------------------------------------------------------------ ---------------------------------------------------- -------------------------------------------------------------

#### []{#anchor-622}[]{#anchor-623}Specific yield

  --------------------------------------- ----------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Constant / concept                      Reference                                       Value / meaning
  Fetter mass-balance Sy                  F.4 / S.11 / *config.py*                        Operational Sy for Script 16 water balance
  WTF cluster median Sy (Approach B)      S.12 / *17_wtf_01_sy_estimates.csv*             Canonical WTF cluster Sy; Approach A also valid in the current pipeline --- chapter S.12 quotes both
  WTF per-well Sy                         S.12 / *18_wtf_per_well_sy.csv*                 Used by Script 19 volumetric conversion
  Storage--drainage index τ = Sy/β₃       S.12 / *18_wtf_05_storage_drainage_index.csv*   Deliberately storage-weighted composite; **not** a residence time. Head-space recession time is t_R = 1/β₃ (see S.12 *Site-specific choices*; cluster means C1 ≈ 11, C2 ≈ 16, C3 ≈ 18, C4 ≈ 55, C5 ≈ 23 months)
  Interception correction for forest Sy   S.12                                            Cluster vs well-level reconciliation
  --------------------------------------- ----------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#### []{#anchor-623}[]{#anchor-624}Forest and forest scenarios

  ---------------------------------------------- ----------------------------- ---------------------------------------------------------------------------------------
  Constant / concept                             Reference                     Value / meaning
  FOREST_CIDS = (4, 5)                           F.4 / *config.py*             Both forested clusters under k=5
  FOREST_INTERCEPTION = 0.24                     F.4 / *config.py*             Freeman (2008), Newborough Corsican pine
  BROADLEAF_INTERCEPTION = 0.15                  F.4 / *config.py*             Komatsu et al. (2011) annual mean
  *BROADLEAF_B2_SUMMER*, *BROADLEAF_B2_WINTER*   F.4 / *config.py* / S.14      Live values: 1.0750 / 0.8817 (May--Oct / Nov--Apr)
  Interception treatment under SSM               F.4                           Partition of PET energy budget, not additive
  load_clearfell_b2_multiplier()                 F.5 / *clearfell_common.py*   BACI-corrected Edge-tier ratio; read dynamically from *10e_01_coefficient_shifts.csv*
  Thinning β₂ multiplier                         F.5 / *clearfell_common.py*   Derived as half-perturbation from clearfell multiplier
  ---------------------------------------------- ----------------------------- ---------------------------------------------------------------------------------------

#### []{#anchor-624}[]{#anchor-625}Intervention machinery

  --------------------------------------------------------------- ---------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------
  Constant / concept                                              Reference                          Value / meaning
  BACI 5-tier network                                             S.7 / *clearfell_common.py*        Impact / Edge / Forest Ctrl / Coastal Ctrl / Climate Ctrl
  Clearfell well tier definitions                                 F.5 / *clearfell_common.py*        *IMPACT_WELLS*, *EDGE_WELLS*, *FOREST_CONTROL_WELLS*, *COASTAL_CONTROL_WELLS*, *CLIMATE_CONTROL_WELLS*
  INTERVENTION_DATE = 2017-12-01                                  F.5 / *clearfell_common.py*        Clearfell intervention boundary
  *SCRAPING_DATE*, *SCRAPING_DATE_2*                              F.5 / *clearfell_common.py*        2015-04-01 and 2023-10-01
  Scraping suite well groups                                      F.5 / *scraping_common.py*         *IMPACT_WELLS*, *PAIRED_CONTROLS_MAP*, *CLIMATE_CONTROLS*, *DONOR_CANDIDATES*
  Scraping era definitions                                        F.5 / *scraping_common.py* / S.6   Per-well *WELL_ERAS* dict
  Scraping λ = 300 m                                              F.5 / *clearfell_common.py*        Exponential distance weight for scraping propagation
  *INTERVENTION_COLOUR_SCRAPE*, *INTERVENTION_COLOUR_CLEARFELL*   F.4 / *config.py* / S.18           Purple *#7b3294* for scraping (2015 CEH36, 2023 CEH18/21), orange *#e66101* for the 2017 clearfell; used by Script 26 trajectory plots
  --------------------------------------------------------------- ---------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------

#### []{#anchor-625}[]{#anchor-626}Scenario engine

  -------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------
  Constant / concept                                                                                                   Reference                                                                                        Value / meaning
  monthly_perturbation()                                                                                               F.5 / *model_utils.py* / S.14                                                                    Option 3 single-step forcing-change response; replaces equilibrium *Δh / β₃*
  compute_scenario_bars()                                                                                              F.5 / *scraping_common.py*                                                                       Per-cluster scenario engine consumed by Scripts 09d, 19, 21
  *summer_amplification_factors()*, *scenario_cluster_sy()*, *flux_to_summer_min_mm()*, *scenario_summer_min_bars()*   F.5 / *scraping_common.py*                                                                       Flux → summer-minimum helpers (retained but unused after 2026-07-02 volumetric re-basis; marked for removal)
  pflood_lambda()                                                                                                      F.5 / *model_utils.py* / S.9                                                                     Iterated closed-form P_flood threshold
  UKCP18 2050s scaling factors                                                                                         F.4 / *config.py*                                                                                RCP8.5 Wales, 50th percentile, 2050s; *UKCP18_DRY\_\** / *UKCP18_WET\_\** constants in *config.py*
  UKCP18 2080s scaling factors                                                                                         F.4 / S.18b / *26b_van_willegen_msl_projections.py*                                              Currently hardcoded in Script 26b's *UKCP18_SCENARIOS* dict; follow-up to centralise as *UKCP18_2080s\_\** in *config.py*
  pipeline_scenario_params.csv                                                                                         F.4 / *pipeline_params.py* / S.1                                                                 Producer-consumer architecture for cross-script parameters
  load_params()                                                                                                        F.5 / *pipeline_params.py*                                                                       Read by Scripts 09b, 09d, 19, 21
  Tool A --- spring MSL transfer function                                                                              S.9 (§Sub-script 11 Methodology) / S.18b (§S.18b.2) / *11_forecasting_thresholds.py* Section 5   *MSL_y = α·h_max_winter + β·P_win_to_spr + γ·PET_win_to_spr + intercept*; R² 0.73--0.96; previous-MSL variant dropped at v1.1.1
  Tool B --- UKCP18 MSL5 perturbation overlay                                                                          S.18b (§S.18b.3) / *26b_van_willegen_msl_projections.py*                                         Single-step *Δh(m) = β₁·ΔP − β₂·ΔPET*; drift-free by construction; ΔMSL5 1--4 cm
  Spring-window structural cancellation                                                                                S.18b §S.18b.3.5                                                                                 Why ΔMSL5 modest at 1--4 cm despite +20--35 % summer PET; the spring window straddles the UKCP18 seasonal partition
  -------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------

#### []{#anchor-626}[]{#anchor-627}Ecological thresholds

  -------------------------------- -------------------------------------------- ------------------------------------
  Constant / concept               Reference                                    Value / meaning
  Curreli summer thresholds        F.4 / *config.SD15b*, *SD16*                 Wet slack 0.61 m, dry slack 0.98 m
  Curreli winter flooding limits   F.4 / *config.SD15b_WINTER*, *SD16_WINTER*   Wet slack 0.10 m, dry slack 0.25 m
  Recovery / excavation limits     F.4 / *config.SD15b_REC*, *SD16_REC*         Wet slack 0.75 m, dry slack 1.20 m
  Ecological zone categorisation   S.9 / *11b_spatial_thresholds.py*            Native rendering of zone maps
  -------------------------------- -------------------------------------------- ------------------------------------

#### []{#anchor-627}[]{#anchor-628}Coastal and spatial

  -------------------------------------------- --------------------------------- --------------------------------------------------------
  Constant / concept                           Reference                         Value / meaning
  Coastal-retreat gradient parameters          S.15 / *25_coastal_gradient.py*   δ₀ = −28.6 mm/yr, L = 894 m, c = −6.3 mm/yr
  Coastline provenance                         S.15                              OpenStreetMap MHW (*natural=coastline*), EPSG:27700
  *well_metadata.csv* (*dist_coast_m*)         S.15 / *paths.DATA_DIST_COAST*    Regenerated + validated in Script 01
  Site geography (drainage paths, ridge)       F.2 / *site_geography.md*         Bedrock ridge as northern boundary; bipartite drainage
  add_idw_surface()                            F.5 / *map_utils.py* / S.5        50 m grid IDW with optional ridge mask
  *load_dem_layer()*, *load_dem_hillshade()*   F.5 / *map_utils.py*              DEM rendering helpers
  add_kml_features()                           F.5 / *map_utils.py*              Features, streams, clearfell overlays
  plot_metric_map()                            F.5 / *map_utils.py*              High-level publication map wrapper
  -------------------------------------------- --------------------------------- --------------------------------------------------------

#### []{#anchor-628}[]{#anchor-629}MSL aggregation

  ------------------------------------------------------------- ------------------------------------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------
  Constant / concept                                            Reference                                                                      Value / meaning
  Spring window (Mar--May)                                      S.18 / *config.MSL_SPRING_MONTHS = (3, 4, 5)*                                  Van Willegen 2025 Table 2
  Hydrology year B (1 Jun y−1 to 31 May y)                      F.2 / S.18 / *config.MSL_HYDRO_YEAR_START_MONTH = 6*                           Van Willegen 2025 convention; co-exists with the October-start convention used in Script 11 Sections 2 and 4
  5-year MSL window                                             S.18 / *config.MSL_DEFAULT_WINDOW_YEARS = 5*                                   Van Willegen et al. (2025) sensitivity-tested this choice
  Strictness: 3/3 spring, 5/5 window                            S.18 / *config.MSL_MIN_MONTHS_PER_SPRING = 3*, *MSL_MIN_YEARS_IN_WINDOW = 5*   Stricter than van Willegen 2025; consistent with 09c, 10d summer-minima *min_measured=2* pattern
  Trajectory restriction to window-ends ≥ 2014                  S.18 / *config.MSL_TRAJECTORY_START_YEAR = 2014*                               Network-composition shift around 2010; per-well CSVs retain full record from 2009
  Van Willegen quadrat wells (17 piezometers)                   S.18 / *config.VW_QUADRAT_WELLS*                                               16/17 covered under strict rules; T41 excluded for insufficient recent record
  Method A (per-well cluster mean)                              S.18 / *paths.OUT_26_5YR_PER_CLUSTER*                                          Headline monitoring metric; extended network
  Method B (cluster-centroid from *03_regional_averages.csv*)   S.18 / S.18b / *paths.OUT_26_5YR_PER_CLUSTER_CENTROID*                         SSM-consistent companion; reference network only; baseline for Tools A and B
  MSL5 ↔ summer-minima 5-yr offset (\~0.54 m)                   S.18 §Empirical relationship to summer minima                                  Pearson r = 0.945 at the 5-year window scale (n = 829 well-year rows)
  Curreli SD15b/SD16 on MSL5 plots                              S.18 §Site-specific choices                                                    Reference lines retained for visual familiarity; calibrated against summer minima, not MSL5 --- figure captions flag the offset
  ------------------------------------------------------------- ------------------------------------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------

#### []{#anchor-629}[]{#anchor-630}Residuals and diagnostics

  ---------------------------------- ------------------ -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Constant / concept                 Reference          Value / meaning
  SSM residual structure             S.16 / Script 22   Network mean residual AR(1) ≈ −0.12
  Ridge-recharge lag null result     S.16 / Script 23   Spearman ρ = +0.010 on lag-vs-distance; test design statistically degenerate against monthly resolution (see §S.16 structural caveat) --- null result documents the analytical attempt, not positive evidence against the mechanism
  Residual seasonality diagnostics   S.16 / Script 24   Phase 12 residual diagnostics; 47/63 wells peak Nov--Mar
  LCSC vs TLM benchmarking           S.5 / Script 08    SSM (Model A) against a traditional linear model with its own constant term
  ---------------------------------- ------------------ -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#### []{#anchor-630}[]{#anchor-631}Climate and field data

  ---------------------------- ------------------------------------ --------------------------------------------------------------------
  Constant / concept           Reference                            Value / meaning
  RAF Valley climate station   F.2 / *RAF_VALLEY_LAT_DEG = 53.25*   53°14′32″N, ≈16 km from site
  Thornthwaite PET             F.2 / S.8 / Script 00                Computed at RAF Valley latitude
  Dipwell field protocol       F.2                                  End-of-month readings, day-15 bucketing
  clean_well_series()          F.5 / *data_utils.py*                Drops \> 4.0 m depths; linear interp single-month gaps (*limit=1*)
  MAX_PHYSICAL_DEPTH = 4.0 m   F.5 / *data_utils.py*                Deepest plausible water table
  normalize_well_name()        F.5 / *data_utils.py*                Used wherever well names join across sources
  ---------------------------- ------------------------------------ --------------------------------------------------------------------

#### []{#anchor-631}[]{#anchor-632}Orchestration and rendering

  ------------------------------------------------------------------------- ------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------
  Constant / concept                                                        Reference                                               Value / meaning
  *paths.py* *OUT\_\** / *INT\_\** / *DIR\_\**                              F.5 / *utils/paths.py*                                  All file paths; no script hardcodes a path
  make_all_dirs()                                                           F.5 / *paths.py*                                        Directory creation helper
  run_analysis.py                                                           S.1 (introduction)                                      Pipeline orchestrator; CLI flags for phases
  Two-pass workflow                                                         F.4 / *PIPELINE_README.md*                              First pass uses fallbacks; second uses canonical Sy / β₂ multipliers
  Greyscale post-processor                                                  Appendix A (this chapter) / *27_greyscale_figures.py*   Phase 17 in *run_analysis.py* (step 49/50); display/utility rather than analytical
  Spatial-reach synthesis figure                                            §S.15c / *09f_management_effects.py*                    Phase 17 in *run_analysis.py* (step 47/50); display/utility; display/utility rather than analytical
  Mechanism-diagram suite                                                   §S.15d / *09g_mechanism_diagrams.py*                    Phase 17 in *run_analysis.py* (step 48/50); display/utility; display/utility rather than analytical
  Script 11c / 14b / 25 / 26 / 26b / 26c / 27 / 28 / 29 naming convention   F.4                                                     Filename prefix, orchestrator step number, and chapter assignment aligned
  *paths.DIR_26*, *paths.OUT_26\_\**                                        F.5 / *utils/paths.py* / S.18                           All Script 26 outputs (Method A + Method B parallel CSVs; quadrat-wells figure; MSL5 map)
  *paths.DIR_26B*, *paths.OUT_26B\_\**                                      F.5 / *utils/paths.py* / S.18b                          All Script 26b outputs (UKCP18 projection figure, summary table, monthly Δh table, results transcript)
  *paths.DIR_26C*, *paths.OUT_26C\_\**                                      F.5 / *utils/paths.py* / S.18c                          All Script 26c outputs (trajectory report figure, ΔMSL5 vs Δsummer-min projection figure, results transcript)
  *paths.OUT_11_TABLE_SPRING*, *paths.OUT_11_SPRING_CALIBRATION*            F.5 / *utils/paths.py* / S.9 / S.18b                    Tool A outputs (Script 11 §5): Table 9 coefficients CSV and per-cluster calibration scatter figure
  paths.OUT_11C\_\*                                                         F.5 / *utils/paths.py* / S.9.3                          Script 11c P_flood achievability outputs (sharing *DIR_11B* with Script 11b): map PNG, per-well category CSV, results memo
  *paths.DIR_14* (shared with Script 14b)                                   F.5 / *utils/paths.py* / S.8.5                          Script 14b bootstrap year-of-crossing outputs share Script 14's directory; no new path constants added
  *paths.DIR_28*, *paths.OUT_28\_\**                                        F.5 / *utils/paths.py* / S.19.1                         All Script 28 C3 detrend check outputs (per-well CSV, results memo, four-panel figure)
  *paths.DIR_29*, *paths.OUT_29\_\**                                        F.5 / *utils/paths.py* / S.19.2                         All Script 29 within-C3 variance outputs (per-well panel CSV, univariate R² matrix, drop-one matrix, results memo, six-panel figure)
  paths.OUT_25_CLUSTER_DECOMP_FIG                                           F.5 / *utils/paths.py* / S.15                           Script 25 v1.1.0 fold-in: per-cluster decomposition stacked-bar figure (§4.8.2 of the main report)
  ------------------------------------------------------------------------- ------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------

### []{#anchor-632}[]{#anchor-633}[]{#anchor-634}Closing remarks

The Methods Supplement closes here. The chapters S.1--S.22 together document the Newborough Warren analytical pipeline as registered in the committed *pipeline_manifest.json*, the design choices behind each step, the rationale for site-specific parameters, and the verification chain by which pipeline outputs feed the main report. Script 26c (*26c_msl5_report_figures.py*, Phase 13 in *run_analysis.py*) is a display-only figure-rendering companion to Scripts 26 and 26b, display/utility rather than analytical, covered in §S.18c; Script 09f (*09f_management_effects.py*, Phase 17 in *run_analysis.py*) is the spatial-reach synthesis figure, display/utility rather than analytical, covered in §S.15c; Script 09g (*09g_mechanism_diagrams.py*, Phase 17 in *run_analysis.py*) is the mechanism-diagram companion to 09f, display/utility rather than analytical, covered in §S.15d; and Script 27 (*27_greyscale_figures.py*, Phase 17 in *run_analysis.py*) is a post-analysis figure-conversion utility, also display/utility rather than analytical, covered in Appendix A. Readers needing a specific topic should consult the canonical-sources table in Appendix B; readers needing the canonical implementation of any function or constant should consult the live *main* branch of <https://github.com/newbroman/Newborough_Hydrology>, which remains the source of truth. The supplement is a guide to what the repository contains and why each choice was made; the repository itself is the deliverable.

End of the Methods Supplement.
