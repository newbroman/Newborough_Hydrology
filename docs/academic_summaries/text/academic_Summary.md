<!-- GENERATED MIRROR of docs/academic_summaries/academic_Summary_v1_28.odt — do not edit. source-sha256=e781ff446dc6408f pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

Newborough Warren Groundwater Study

Evidence Summary --- Hydrogeological Dynamics, Behavioural Clustering and Management Intervention Analysis

Hollingham, M. (2026) \| Draft \| Summarised for researchers, evidence reviewers and dune system managers

Full report, methods supplement and data: github.com/newbroman/Newborough_Hydrology \| Contact: martin.hollingham+nrg@gmail.com \| ORCID: 0000-0003-0253-9301

Study design and methods

A 21-year dipwell monitoring dataset (2005--2026) covering 88 wells (66 reference, 22 extended) across Newborough Warren SAC was analysed using a 59-step reproducible Python pipeline. Monthly water levels were combined with RAF Valley climate data (rainfall, Thornthwaite PET). The core analytical tool is a state-space model (SSM) fitted independently to each well, estimating three physical coefficients: recharge sensitivity (β₁), atmospheric draw (β₂) and drainage (β₃). SSM performance was benchmarked against a transfer function lacking the drainage term; the SSM achieved positive Nash--Sutcliffe efficiency in iterative forecast mode at 65 of 66 reference wells (vs 44 of 66 for the transfer function).

Cluster analysis (hierarchical Ward, k=5) partitioned the reference network into five hydrogeological zones. Management interventions were assessed via ANCOVA-BACI with five-tier experimental design and three independent control groups. Climate projections used UKCP18 RCP8.5 50th-percentile forcing. Ecological thresholds follow Curreli et al. (2013): wet-slack summer minimum −0.61 m, dry-slack −0.98 m. Spring baseline change was assessed using the van Willegen et al. (2025) MSL5 metric.

![](Pictures/10000000000007600000065963A870F2.png){width="14cm" height="10.714cm"}

Figure 1. The five hydrogeological zones identified by cluster analysis (hierarchical Ward, k=5): C1 Lake Edge (blue, n=7), C2 Dune (green, n=19), C3 Western Residual (red, n=26), C4 Main Forest (purple, n=9), C5 Coastal Forest (brown, n=5). Forest boundary magenta; 2017 clearfell zone orange.

Aquifer characterisation

The k=5 partition yields five zones with distinct SSM coefficient profiles (Table 1). The Main Forest (C4) exhibits the lowest recharge sensitivity and highest atmospheric draw, driven by pine interception and thin substrate over irregular bedrock. The Lake Edge (C1) has the highest recharge sensitivity and fastest drainage, buffered by the adjacent lake. Coastal Forest (C5) shows the steepest summer minimum decline of all zones. Ground elevation explains approximately 95% of the variance in β₂ within the forested area, confirming that substrate thickness rather than canopy cover is the primary control on summer drawdown intensity.

  ------------------- ---- ------------- -------------- ------------- -------
  Zone                n    β₁ recharge   β₂ atm. draw   β₃ drainage   LCSC
  C1 Lake Edge        7    4.578         0.911          0.089         0.218
  C2 Dune             19   3.896         1.666          0.063         0.257
  C3 W. Residual      26   3.758         1.778          0.062         0.266
  C4 Main Forest      9    2.476         2.570          0.018         0.404
  C5 Coastal Forest   5    2.412         1.248          0.045         0.415
  ------------------- ---- ------------- -------------- ------------- -------

Table 1. SSM mechanistic coefficients by cluster (cluster-centroid fits). β₁, β₂ dimensionless; β₃ month⁻¹. LCSC = lumped climate-storage contribution (100/β₁), the reciprocal of recharge sensitivity.

Climate forcing and threshold analysis

Summer maximum temperatures at RAF Valley have trended upward at +0.014°C yr⁻¹ (p \< 0.001) over the full record (1931--2025), with a step increase of +0.94°C above baseline since 2013. Trend analysis of summer minimum water-table depth yields statistically significant declining trends in C1 (p \< 0.05) and C5 (p \< 0.05); C2 is marginal; C3 and C4 are non-significant on their own. Extrapolation of cluster-mean trends indicates C1 Lake Edge crosses the wet-slack viability threshold (SD15b, −0.61 m) around 2030--2032 under current trajectory.

The van Willegen et al. (2025) finding that a five-year mean spring level (MSL5) best explains dune slack vegetation response reflects an ecological carry-over: plant communities integrate hydrological conditions over roughly five years. Whether the five spring readings within an MSL5 window are independent depends on how quickly the water table returns to its own mean. That is not the drainage half-life t½ = ln(2)/β₃ of the published no-intercept model, which is the recession constant of the drainage term at the 3.7 m datum and changes with the datum. It is measured by refitting the same model with a free intercept, whose drainage coefficient does not depend on the datum, and it is short: the e-folding time is about half a year (median 6.5 months, against 5.1 months from the observed autocorrelation of the deseasonalized level), from about 2 months at C1 Lake Edge to about 13 months at C5 Coastal Forest. The year-to-year spring persistence this implies is small, from 0.01 at C1 to 0.28 at C5 (median 0.15 across wells), and the observed lag-1 autocorrelation of annual spring level is approximately zero at every cluster (median −0.11). The readings within an MSL5 window are therefore close to independent across the network, and MSL5 behaves as a genuine five-year average. Window sensitivity is real and graded, but as a matter of amplitude rather than persistence: it is greatest at C4 Main Forest, whose spring levels swing furthest, and the interannual spread of spring level follows the atmospheric-draw coefficient β₂ rather than β₃. C4\'s free-intercept drainage coefficient is not identified on the record.

UKCP18 RCP8.5 50th-percentile projections were evaluated as the sustained change in water level, per well on the coefficients of the intercept form of the model (whose drainage coefficient does not depend on the drainage datum); C4 Main Forest is not projected, its drainage coefficient not being identified on the record. The site-wide mean annual level falls by 0.158 m by the 2050s and 0.284 m by the 2080s. Summer carries most of the change: summer levels fall by 0.212 and 0.385 m site-wide, reaching 0.438 m at C3 by the 2080s, and winter levels fall too (0.103 and 0.180 m) everywhere except C1. The spring baseline moves far less in the open dune: by the 2080s MSL5 changes by +52 mm at C1 and −22 mm at C2, against summer falls of 315 and 359 mm. At C3 and C5 it falls by about half as much as the summer level (−150 against −438 mm, and −141 against −302 mm), the longer mean-reversion time there carrying a summer deficit into the following spring. Critical rainfall multipliers (m_P) classify 57 of 65 open-dune wells as achievable (m_P \< 1.5) and 5 of 23 forest-zone wells as structurally unreachable (m_P ≥ 2.5).

![](Pictures/100000000000076200000446097E6DF6.png){width="14cm" height="8.1cm"}

Figure 2. Projected summer minimum trajectory for all five zones vs Curreli et al. (2013) ecological thresholds. Critical intervention window 2030--2039 shaded.

![](Pictures/10000000000006B2000004D245961E36.png){width="14cm" height="10.090cm"}

Figure 3. Projected sustained shift in the five-year mean spring water level (MSL5, blue) and in the summer water level (orange), by zone, under UKCP18 RCP8.5 forcing for the 2050s and 2080s, on the intercept-form coefficients. C4 is not projected (its drainage coefficient is not identified). Negative is deeper. The spring metric moves far less than the summer level in the open dune (C1, C2), and about half as much at C3 and C5.

Management intervention analysis

Dune scraping --- CEH36 (April 2015) and CEH18/CEH21 (October 2023)

CEH36: Three independent estimators yield consistent scraping effects --- raw paired BACI +129 mm, synthetic control +137 mm, SSM forward-residual +73 mm. The headline figure is the paired summer minimum BACI shift: +195 mm (p = 0.004) relative to the unscraped control CEH4. This represents a permanent geometric benefit: the ground surface is closer to the water table, so the relative water-table depth is shallower regardless of absolute level. CEH36 predates the MSL5 comparison windows (2013--2017 vs 2019--2023); its initial rise does not appear in Figure 4.

CEH18/CEH21 (October 2023): Insufficient post-intervention record (\<2 years) for statistical inference. Both sites occupy more seaward positions where the coastal-retreat gradient is a confounding factor. No significant post-scraping signal is detectable at either well against the backdrop of year-to-year variability.

Clearfell BACI --- December 2017 (4.2 ha)

Five-tier ANCOVA-BACI design: 17 wells, three independent control definitions (Forest, Climate, Combined). Headline result (Forest control, WMC3 impact well): clearfell step +0.113 m (p = 0.002, CI \[0.042, 0.184\]). Forest Edge: +0.030 m (p = 0.249). Synthetic extension (10h, WMC3+FE1+FE2 centroid): +0.085 m (p \< 0.001). Summer-only ANCOVA (Jun--Sep subset): +0.046 m (p = 0.436) --- not significant. The summer non-result is robust across all control definitions.

The null summer result is consistent with a dual canopy role: interception removal increases winter recharge but exposure increases direct summer evapotranspiration from the now-unshaded soil. These effects approximately cancel in the June--September window. A site-wide decline in recharge efficiency (β₁ declining over time across all clusters) is identified as the primary driver of summer minimum deterioration, operating independently of canopy management.

Observed spring baseline change and spatial structure

MSL5 comparison (window-end 2017 vs window-end 2023): site-mean deepening −105 mm (network mean −467 to −572 mm). Of 59 wells with valid data in both windows, 58 deepened \>25 mm; 0 became shallower \>25 mm. Largest declines at the south-western coastal margin (CEH22: −233 mm); smallest at the eastern Lake Edge. Clearfell zone shows no distinguishable signal.

![](Pictures/10000001000009EE00000967C79BE1C0.png){width="13cm" height="9.377cm"}

Figure 4. MSL5 change 2017→2023. n=59 wells; 56 deepened \>25 mm, 0 shallower \>25 mm. Source: 20_msl5_change_2017_2023.png; Report Figure 72.

Differential spring movement analysis (Script 32, 2011--2025) reveals divergent within-network trends. C4 Main Forest is uniformly positive (+8.4 to +20.5 mm yr⁻¹ relative to site mean, cluster mean +14.9 mm yr⁻¹); none individually significant after AR(1) correction. This reflects two reinforcing mechanisms: (1) the forest occupies the hydraulic high of the aquifer, furthest from any constant-head boundary (lake to the east, Menai Strait to the south-east, coast to the south-west), giving the water table maximum freedom to rise in wet years and fall in dry ones; (2) the low-specific-yield substrate (thin sand over bedrock) concentrates recharge into larger head changes. Recent wet springs (2021, 2024) have amplified C4 relative to the network. C1 Lake Edge and C5 Coastal Forest are uniformly negative (−8.0 and −6.8 mm yr⁻¹ respectively), driven by the coastal-retreat boundary signal. C2 Dune is near-neutral on average.

![](Pictures/100000010000075D0000047A9BEF99AE.png){width="14.986cm" height="10.811cm"}

Figure 5. Differential spring movement 2011--2025. C4 uniformly positive (amplified wet-year response + hydraulic-high position); C1 and C5 uniformly negative (coastal boundary effect). C2/C3 broadly neutral. Filled = significant (AR-corrected p \< 0.05).

Coastal retreat signal

A network-scale regression of per-well trends against distance to the eroding shoreline resolves a real coastal-retreat gradient affecting the western margin. Independently, a two-well transect of coastal control wells deteriorates in a pattern consistent with progressive boundary-condition lowering. The coastal-retreat signal accounts, within uncertainty, for the whole of C5's exceptional decline. Groundwater propagation lags mean current data partly reflect historical erosion; if erosion is accelerating, the worst effects have not yet reached interior wells. CEH22 (outside the reference network, SW coastal margin) is declining at −26.5 mm yr⁻¹ (p \< 0.001), the fastest in the network.

The scale of observed change in context

The management interventions studied to date have produced measurable effects at the local scale: the scraping benefit at CEH36 is statistically robust and ecologically significant, and the clearfell produced a detectable improvement in mean monthly water levels against forest controls. However, the site-wide spring baseline deepened by 105 mm between the 2017 and 2023 comparison windows --- a change affecting 58 of 59 monitored wells simultaneously and driven by forces operating at the scale of the whole aquifer. Summer temperatures have trended upward at +0.014°C yr⁻¹ since 1931, with a step increase of +0.94°C above baseline since 2013. The coastal-retreat signal accounts, within uncertainty, for the whole of the Coastal Forest zone's exceptional decline, and extends several hundred metres inland. Against these signals, the scraping benefit at a single well (+195 mm) and the clearfell monthly-mean improvement (+113 mm relative to unfelled forest) represent localised responses that do not alter the direction of the network-wide trend. The UKCP18 projections indicate a further fall in summer water level of about 0.39 m site-wide by the 2080s (0.30 to 0.44 m across the projected zones; C4 not projected), on top of the 105 mm of spring-baseline deepening already measured between the 2017 and 2023 comparison windows, and substantially exceeding any management effect observed in this record.

Key quantitative findings

  -------------------------------------------------------------- ---------------------------- ----------------
  Finding                                                        Value                        Source
  Scraping step CEH36 (paired BACI)                              \+ 195 mm p = 0.004          Script 09c
  Clearfell step vs Forest control (monthly mean)                \+ 113 mm p = 0.002          Script 10a
  Clearfell step vs Forest control (summer only)                 \+ 46 mm p = 0.44 (n.s.)     Script 10a
  MSL5 change 2017→2023 (site mean)                              − 105 mm                     Script 26 / 20
  Wells deepened \>25 mm (of 59 valid)                           58 (98%)                     Script 20
  C4 differential trend 2011--2025                               \+ 14.9 mm/yr (mean)         Script 32
  C5 differential trend 2011--2025                               − 6.8 mm/yr (mean)           Script 32
  C4 amplification coefficient (canonical)                       1.65× site mean              Script 33/35
  C1 amplification coefficient                                   0.66× site mean              Script 33/35
  CEH22 (coastal margin) trend                                   − 26.5 mm/yr p \< 0.001      Script 32
  C1 threshold crossing (summer min)                             \~2030--2032                 Script 14
  UKCP18 2080s summer level fall, site-wide (C4 not projected)   385 mm (302--438 by zone)    Script 19
  UKCP18 2080s MSL5 change, C1 / C2 / C3 / C5                    +52 / −22 / −150 / −141 mm   Script 19
  -------------------------------------------------------------- ---------------------------- ----------------

Table 2. Headline quantitative results. All figures from committed pipeline CSVs on GitHub main branch.

Conclusions

> • The summer minimum water table is the ecologically binding variable. MSL5 is a better-measured proxy that tracks slower system drift but understates the amplitude of the ecological risk, most of all in the open dune (C1, C2), where projected spring levels barely move while summer levels fall by more than 0.3 m by the 2080s.

> • Dune scraping at well-chosen inland sites is the most effective available direct intervention but does not address the underlying drivers. Benefits erode against the background climate trend.

> • Clearfell raises mean water-table levels in the forest zone relative to unfelled controls but produces no detectable summer minimum improvement, consistent with canopy-removal dual effects cancelling in summer.

> • A site-wide decline in recharge efficiency, operating independently of surface management, is the dominant driver of summer minimum deterioration.

> • The coastal-retreat boundary signal is a distinct, lagged, and currently unmanageable threat to the western margin. Interior wells have not yet experienced the full effect of recent accelerated erosion.

> • The hydraulic position of the forest (topographic and aquifer high, no nearby constant-head boundary) makes it a strong amplifier of year-to-year climate variability, not a recovery signal.

> • Climate and coastal forces are operating at a magnitude that swamps the localised management interventions observed to date.
