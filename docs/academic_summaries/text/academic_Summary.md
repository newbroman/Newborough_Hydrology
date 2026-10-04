<!-- GENERATED MIRROR of docs/academic_summaries/academic_Summary_v1_32.odt — do not edit. source-sha256=60dd2517c3620f5e pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

Newborough Warren Groundwater Study

Evidence Summary --- Hydrogeological Dynamics, Behavioural Clustering and Management Intervention Analysis

Hollingham, M. (2026) \| Draft \| Summarised for researchers, evidence reviewers and dune system managers

Full report, methods supplement and data: github.com/newbroman/Newborough_Hydrology \| Contact: martin.hollingham+nrg@gmail.com \| ORCID: 0000-0003-0253-9301

Study design and methods

A 21-year dipwell monitoring dataset (2005--2026) covering 88 wells (66 reference, 22 extended) across Newborough Warren SAC was analysed using a 60-step reproducible Python pipeline. Monthly water levels were combined with RAF Valley climate data (rainfall, Thornthwaite PET). The core analytical tool is a state-space model (SSM) fitted independently to each well, estimating three physical coefficients: recharge sensitivity (β₁), atmospheric draw (β₂) and drainage (β₃). SSM performance was benchmarked against a traditional linear model (TLM) lacking the drainage term; the SSM achieved positive Nash--Sutcliffe efficiency in iterative forecast mode at 65 of 66 reference wells (vs 55 of 66 for the traditional linear model).

Cluster analysis (hierarchical Ward, k=5) partitioned the reference network into five hydrogeological zones. Management interventions were assessed via ANCOVA-BACI with five-tier experimental design and three independent control groups. Climate projections used UKCP18 RCP8.5 50th-percentile forcing. Ecological thresholds follow Curreli et al. (2013): wet-slack summer minimum −0.61 m, dry-slack −0.98 m. Spring baseline change was assessed using the van Willegen et al. (2025) MSL5 metric.

![](Pictures/10000000000007600000065963A870F2.png){width="14cm" height="10.714cm"}

Figure 1. The five hydrogeological zones identified by cluster analysis (hierarchical Ward, k=5): C1 Lake Edge (blue, n=7), C2 Dune (green, n=19), C3 Western Residual (red, n=26), C4 Main Forest (purple, n=9), C5 Coastal Forest (brown, n=5). Forest boundary magenta; 2017 clearfell zone orange.

Aquifer characterisation

The k=5 partition yields five zones with distinct SSM coefficient profiles (Table 1). The Main Forest (C4) exhibits the lowest recharge sensitivity and highest atmospheric draw, driven by pine interception and thin substrate over irregular bedrock. The Lake Edge (C1) has the highest recharge sensitivity and fastest drainage, buffered by the adjacent lake. Coastal Forest (C5) shows the steepest summer minimum decline of all zones. Ground elevation explains 98% of the variance in β₂ within the forested area, confirming that substrate thickness rather than canopy cover is the primary control on summer drawdown intensity.

  ------------------- ---- ------------- -------------- ------------- -------
  Zone                n    β₁ recharge   β₂ atm. draw   β₃ drainage   LCSC
  C1 Lake Edge        7    4.578         0.911          0.089         0.218
  C2 Dune             19   3.896         1.666          0.063         0.257
  C3 W. Residual      26   3.758         1.778          0.062         0.266
  C4 Main Forest      9    2.476         2.570          0.018         0.404
  C5 Coastal Forest   5    2.412         1.248          0.045         0.415
  ------------------- ---- ------------- -------------- ------------- -------

Table 1. SSM mechanistic coefficients by cluster (cluster-centroid fits). β₁, β₂ dimensionless; β₃ month⁻¹. LCSC = Lumped Catchment Storage Coefficient (100/β₁), the reciprocal of recharge sensitivity.

Climate forcing and threshold analysis

Summer maximum temperatures at RAF Valley have trended upward at +0.014°C yr⁻¹ (p \< 0.001) over the full record (1931--2025), with a step increase of +0.94°C above baseline since 2013. Trend analysis of summer minimum water-table depth yields statistically significant declining trends over the full record in C1, C2, C3 and C5 (p = 0.024, 0.033, 0.028 and 0.004); C4 is not significant (p = 0.36). The decline is concentrated before 2011: refitted from 2011, no cluster shows a significant trend. C1 Lake Edge\'s summer minimum has been deeper than the wet-slack threshold (SD15b, −0.61 m) in every year of the record; a bootstrap of its summer-minimum trend places the median crossing of the dry-slack threshold (SD16, −0.98 m) at 2027 (90% CI 2021--2046), and three of the eight most recent summer minima already exceed it.

The van Willegen et al. (2025) finding that a five-year mean spring level (MSL5) best explains dune slack vegetation response reflects an ecological carry-over: plant communities integrate hydrological conditions over roughly five years. Whether the five spring readings within an MSL5 window are independent depends on how quickly the water table returns to its own mean. That is not the drainage half-life t½ = ln(2)/β₃ of the published no-intercept model, which is the recession constant of the drainage term at the 3.7 m datum and changes with the datum. It is measured by refitting the same model with a free intercept, whose drainage coefficient does not depend on the datum, and it is short: the e-folding time is about half a year (median 6.5 months, against 5.1 months from the observed autocorrelation of the deseasonalized level), from about 2 months at C1 Lake Edge to about 13 months at C5 Coastal Forest. The year-to-year spring persistence this implies is small, from 0.01 at C1 to 0.28 at C5 (median 0.15 across wells), and the observed lag-1 autocorrelation of annual spring level is approximately zero at every cluster (median −0.11). The readings within an MSL5 window are therefore close to independent across the network, and MSL5 behaves as a genuine five-year average. Window sensitivity is real and graded, but as a matter of amplitude rather than persistence: it is greatest at C4 Main Forest, whose spring levels swing furthest, and the interannual spread of spring level follows the atmospheric-draw coefficient β₂ rather than β₃. C4\'s free-intercept drainage coefficient is not identified on the record.

UKCP18 RCP8.5 50th-percentile projections were evaluated as the sustained change in water level, per well on the coefficients of the intercept form of the model (whose drainage coefficient does not depend on the drainage datum); C4 Main Forest is not projected, its drainage coefficient not being identified on the record. The site-wide mean annual level falls by 0.159 m by the 2050s and 0.286 m by the 2080s. Summer carries most of the change: summer levels fall by 0.213 and 0.387 m site-wide, reaching 0.440 m at C3 by the 2080s, and winter levels fall too (0.103 and 0.180 m) everywhere except C1. The spring baseline moves far less in the open dune: by the 2080s MSL5 changes by +52 mm at C1 and −22 mm at C2, against summer falls of 315 and 359 mm. At C3 and C5 it falls by about half as much as the summer level (−150 against −440 mm, and −141 against −319 mm), the longer mean-reversion time there carrying a summer deficit into the following spring. Critical rainfall multipliers (m_P) classify 58 of 64 open-dune wells as achievable (m_P \< 1.5) and 5 of 24 forest-zone wells as structurally unreachable (m_P ≥ 2.5).

![](Pictures/100000000000076200000446097E6DF6.png){width="14cm" height="8.1cm"}

Figure 2. Projected summer minimum trajectory for all five zones vs Curreli et al. (2013) ecological thresholds. Source: 14_climate_trajectory_summer.png.

![](Pictures/10000000000006B2000004D245961E36.png){width="14cm" height="13.5728cm"}

Figure 3. Projected sustained shift in the five-year mean spring water level (MSL5, blue) and in the summer water level (orange), by zone, under UKCP18 RCP8.5 forcing for the 2050s and 2080s, under the intercept form (Model B, filled) and the published no-intercept form (Model A, hatched). C4 is not projected (its drainage coefficient is not identified). Negative is deeper. The spring metric moves far less than the summer level in the open dune (C1, C2), and a third to a half as much at C3 and C5 under Model B. Source: fig_msl5_vs_summer_min_projection.png.

Management intervention analysis

Dune scraping --- CEH36 (April 2015) and CEH18/CEH21 (October 2023)

CEH36: Three independent estimators yield consistent scraping effects --- raw paired BACI +128 mm, synthetic control +141 mm, SSM forward-residual +100 mm. The headline figure is the paired summer minimum BACI shift: +195 mm (p = 0.004) relative to the unscraped control CEH4. This represents a permanent geometric benefit: the ground surface is closer to the water table, so the relative water-table depth is shallower regardless of absolute level. CEH36 predates the MSL5 comparison windows (2013--2017 vs 2019--2023); its initial rise does not appear in Figure 4.

CEH18/CEH21 (October 2023): Both showed limited responses that did not survive correction for background drift. Both sites occupy more seaward positions where the coastal-retreat gradient is a confounding factor. No significant post-scraping signal is detectable at either well against the backdrop of year-to-year variability.

Clearfell BACI --- December 2017 (4.2 ha)

Five-tier ANCOVA-BACI design: 17 wells, three independent control definitions (Forest, Climate, Combined). Headline result (Forest control, WMC3 impact well): after felling the well rose +0.128 m over October--March (p = 0.048, CI \[0.001, 0.254\]) and not at all over June--September; the annual-mean clearfell step, +0.108 m, is not significant on its own once autocorrelation is allowed for (p = 0.10, CI \[−0.021, 0.237\]; autocorrelation-robust (Newey--West) errors throughout). Forest Edge: +0.031 m (p = 0.50), not significant. Synthetic extension (10h, WMC3 + FE2 centroid): +0.094 m (p = 0.12). Summer-only ANCOVA (Jun--Sep subset): −0.001 m (p = 0.99) --- not significant. The step is not stationary: +152 mm to December 2020 and +39 mm thereafter, with the compartment held clear by grazing (Script 10a). The summer non-result is robust across all control definitions.

The felled well itself shows no rise in recharge sensitivity after felling (β₁ 0.98 of its pre-felling value, net of the climate controls) and a fall in atmospheric draw 4.8% beyond the climate controls, with no loss of the canopy\'s summer shielding (draw in the canopy-on months −1.7% net). The step sits in the mean monthly level, not the summer level. A network-mean decline in recharge sensitivity (β₁ −4.6% across the 17 BACI wells) is a candidate mechanism for summer minimum deterioration, but the unfelled Climate Control tier shows almost none of it (−0.3%), so its independence of management is not established.

Forestry scenarios (D-239) are anchored to what the December 2017 felling measured at WMC3: a fall in atmospheric draw and no rise in recharge. As sustained changes in level, clearfell raises the water table by +0.038 m (Model B) to +0.066 m (Model A) at C5 and by +0.217 m at C4 (Model A); at the felled well it gives +0.060 and +0.135 m, either side of the +0.108 m measured there. Thinning gives at most half of each. Broadleaf conversion ranges from a slight fall (−0.037 m at C5 and −0.121 m at C4, Model A) without an interception gain to a rise (+0.308 and +0.506 m) with one. These are the lower end of the clearfell range: the 4.2 ha compartment is narrower than the drawdown reach (about 220 m), so a recharge gain there would spread into the surrounding forest; the interception form marks the upper end for a wider felling, bounded by an open-dune end state of 0.5--0.9 m. The scenarios are evaluated well by well and cannot show whether a change in the forest reaches the open dune. By the 2080s the annual level at C5 falls by 0.27 m (Model B) to 0.49 m (Model A) under UKCP18, more than the lower end of any forestry scenario raises it.

Observed spring baseline change and spatial structure

MSL5 comparison (window-end 2017 vs window-end 2023): site-mean deepening −105 mm (network-mean MSL5 from 467 to 572 mm below ground). Of 59 wells with valid data in both windows, 58 deepened \>25 mm; 0 became shallower \>25 mm. Largest declines at the south-western coastal margin (CEH22: −233 mm); smallest at the eastern Lake Edge. Clearfell zone shows no distinguishable signal.

![](Pictures/10000001000009EE00000967C79BE1C0.png){width="13cm" height="9.377cm"}

Figure 4. MSL5 change 2017→2023. n=59 wells; 58 deepened \>25 mm, 0 shallower \>25 mm. Source: 20_msl5_change_2017_2023.png; Report Figure 72.

Differential spring movement analysis (Script 32, 2011--2025) reveals divergent within-network trends. C4 Main Forest is uniformly positive (+6.9 to +18.9 mm yr⁻¹ relative to site mean, cluster mean +13.7 mm yr⁻¹); none individually significant after AR(1) correction. This reflects two reinforcing mechanisms: (1) the forest occupies the hydraulic high of the aquifer, furthest from any constant-head boundary (lake to the east, Menai Strait to the south-east, coast to the south-west), giving the water table maximum freedom to rise in wet years and fall in dry ones; (2) the low-specific-yield substrate (thin sand over bedrock) concentrates recharge into larger head changes. Recent wet springs (2021, 2024) have amplified C4 relative to the network. C1 Lake Edge declines at −5.6 mm yr⁻¹ (CEH11 significant) and C5 Coastal Forest at −8.5 mm yr⁻¹ (NW9, CEH17 and CEH19 significant), the latter consistent with the coastal-retreat boundary signal. C2 Dune is near-neutral on average.

![](Pictures/100000010000075D0000047A9BEF99AE.png){width="14.986cm" height="10.811cm"}

Figure 5. Differential spring movement 2011--2025. C4 uniformly positive (amplified wet-year response + hydraulic-high position); C5 uniformly negative (coastal boundary effect) and C1 mostly negative. C2/C3 broadly neutral. Filled = significant (AR-corrected p \< 0.05).

Coastal retreat signal

A network-scale regression of per-well trends against distance to the eroding shoreline resolves a real coastal-retreat gradient affecting the western margin. Independently, a two-well transect of coastal control wells deteriorates in a pattern consistent with progressive boundary-condition lowering. The coastal-retreat gradient accounts for about half of C5's exceptional decline (53% on the balanced basis), leaving −17.6 mm yr⁻¹ unexplained; the share is sensitive to which wells the cluster contains. Groundwater propagation lags mean current data partly reflect historical erosion; if erosion is accelerating, the worst effects have not yet reached interior wells. CEH22 (outside the reference network, SW coastal margin) is declining at −27.8 mm yr⁻¹ (p \< 0.001), the fastest in the network.

The scale of observed change in context

The management interventions studied to date have produced measurable effects at the local scale: the scraping benefit at CEH36 is statistically robust and ecologically significant, and the clearfell was followed by a winter rise at the felled well (+128 mm over October--March) but none in summer, although the annual-mean step against forest controls (+108 mm) is not significant on its own. However, the site-wide spring baseline deepened by 105 mm between the 2017 and 2023 comparison windows --- a change affecting 58 of 59 monitored wells simultaneously and driven by forces operating at the scale of the whole aquifer. Summer temperatures have trended upward at +0.014°C yr⁻¹ since 1931, with a step increase of +0.94°C above baseline since 2013. The coastal-retreat signal accounts for about half of the Coastal Forest zone's exceptional decline, and extends several hundred metres inland. Against these signals, the scraping benefit at a single well (+195 mm) and the clearfell monthly-mean improvement (+108 mm relative to unfelled forest) represent localised responses that do not alter the direction of the network-wide trend. The UKCP18 projections indicate a further fall in summer water level of about 0.39 m site-wide by the 2080s (0.32 to 0.44 m across the projected zones; C4 not projected), on top of the 105 mm of spring-baseline deepening already measured between the 2017 and 2023 comparison windows, and substantially exceeding any management effect observed in this record.

Key quantitative findings

  -------------------------------------------------------------- ---------------------------- ----------------
  Finding                                                        Value                        Source
  Scraping step CEH36 (paired BACI)                              \+ 195 mm p = 0.004          Script 09c
  Clearfell step vs Forest control (monthly mean)                \+ 108 mm p = 0.10           Script 10a
  Clearfell step vs Forest control (summer only)                 − 1 mm p = 0.99 (n.s.)       Script 10a
  MSL5 change 2017→2023 (site mean)                              − 105 mm                     Script 26 / 20
  Wells deepened \>25 mm (of 59 valid)                           58 (98%)                     Script 20
  C4 differential trend 2011--2025                               \+ 13.7 mm/yr (mean)         Script 32
  C5 differential trend 2011--2025                               − 8.5 mm/yr (mean)           Script 32
  C4 amplification coefficient (canonical)                       1.66× site mean              Script 33/35
  C1 amplification coefficient                                   0.64× site mean              Script 33/35
  CEH22 (coastal margin) trend                                   − 27.8 mm/yr p \< 0.001      Script 32
  C1 SD16 crossing (summer min, bootstrap median)                2027 (90% CI 2021--2046)     Script 14
  UKCP18 2080s summer level fall, site-wide (C4 not projected)   387 mm (319--440 by zone)    Script 19
  UKCP18 2080s MSL5 change, C1 / C2 / C3 / C5                    +52 / −22 / −150 / −141 mm   Script 19
  -------------------------------------------------------------- ---------------------------- ----------------

Table 2. Headline quantitative results. All figures from committed pipeline CSVs on GitHub main branch.

Conclusions

> • The summer minimum water table is the ecologically binding variable. MSL5 is a better-measured proxy that tracks slower system drift but understates the amplitude of the ecological risk, most of all in the open dune (C1, C2), where projected spring levels barely move while summer levels fall by more than 0.3 m by the 2080s.

> • Dune scraping at well-chosen inland sites is the most effective available direct intervention but does not address the underlying drivers. Benefits erode against the background climate trend.

> • After clearfell the felled well rose in winter (+128 mm over October--March, p = 0.048) but not in summer, the annual-mean step (+108 mm) is not significant on its own once autocorrelation is allowed for, and there is no detectable summer minimum improvement, the step is front-loaded (+152 mm to December 2020, +39 mm thereafter) and the felled well shows a fall in draw with no rise in recharge (D-239).

> • A network-wide decline in recharge sensitivity is a candidate mechanism for summer minimum deterioration; its independence of management is not established.

> • The coastal-retreat boundary signal is a distinct, lagged, and currently unmanageable threat to the western margin. Interior wells have not yet experienced the full effect of recent accelerated erosion.

> • The hydraulic position of the forest (topographic and aquifer high, no nearby constant-head boundary) makes it a strong amplifier of year-to-year climate variability, not a recovery signal.

> • Climate and coastal forces are operating at a magnitude that swamps the localised management interventions observed to date.
