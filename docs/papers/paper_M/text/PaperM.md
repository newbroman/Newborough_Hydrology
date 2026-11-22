<!-- GENERATED MIRROR of docs/papers/paper_M/PaperM_v1_51.odt — do not edit. source-sha256=45b864ed3b9aa393 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

One model for a dune water table: what a monthly linear-reservoir model fitted to dipwell levels can forecast, and how far to trust it

M. Hollingham

Draft --- 2026

# []{#anchor}Abstract

Monthly dipwell records are often the only long record a wetland manager has, and reservoir models fitted to them are used to forecast the water table, yet are rarely tested outside their fitting months. We run the exponential-response model of Pastas month by month at 66 wells of a coastal dune aquifer at Newborough Warren, Wales, and test it three ways. Fitted on one side of January 2018 and run freely across the other, its median Nash--Sutcliffe efficiency is 0.79 forward and 0.78 in reverse; two years of record give 0.71. A new well, placed in its cluster from two years of readings, is served nearly as well by the cluster's coefficients (0.76). Run from 1930, the model reproduces the seasons of Ranwell's 1951--53 readings (0.86) but puts the water table of the drier 1989--96 decade 0.21 m too high at the median well: its main limitation. Its drainage coefficient measures how fast the water table returns to its own mean (6.5 months at the median well; 5.1 months without a model), not drainage to a physical floor. Water levels alone do not fix how the loss splits between drainage and evaporation: the model puts drainage at 45 % at the median well, a water balance with an independent storage coefficient at 31 %. A fixed drainage floor, tested and not adopted, bounds a drier climate: a 2080s high-emissions summer fall of 0.37 m could reach 0.52 m. We give a procedure for a manager with a monthly record.

**Keywords:** groundwater forecasting; hindcast; linear reservoir; Pastas; mean-reversion time; dune slack

# []{#anchor}Highlights

-   On years it never saw, a monthly Pastas model forecasts at median NSE 0.79
-   Hindcast to 1989--96, it sets the water table 0.21 m high: drier futures understated
-   Its drainage coefficient is a mean-reversion time, matched by a model-free estimate
-   Two years of dipwell record already give a forecast with median NSE 0.71

# []{#anchor}1. Introduction

Shallow groundwater governs the condition of dune slacks, fens, wet heaths and other groundwater-dependent wetlands. In most places, the record on which their management rests is a network of dipwells read by hand about once a month. What managers most want from that record is a forecast: how the water table will respond to the coming years, and to a changing climate. Recharge, drainage and evapotranspiration are rarely measured at such sites, so the forecast comes from a model fitted to the levels themselves. This paper keeps to the data a site manager can readily obtain: monthly dipwell readings, and the rainfall and temperature recorded at a single weather station.

Head-only models of this kind are in common use. Transfer-function-noise models represent the level as the convolution of each driver with an impulse response, the simplest being the exponential response of a single linear reservoir (von Asmuth et al., 2002; Knotters and Bierkens, 2000). They are implemented in open software, notably Pastas (Collenteur et al., 2019) and HydroSight (Peterson and Western, 2014), and have been applied to shallow unconfined aquifers in a range of settings (Obergfell et al., 2019; Bakker and Schaars, 2019). State-space or difference-equation forms write the same reservoir directly as a monthly balance, in which the change in level is driven by rainfall, by evaporative demand and by a drainage loss proportional to the head above a base (Knotters and van Walsum, 1997; Peters et al., 2003).

Such models are usually judged by how well they fit the record. A forecast cannot be checked until the future arrives. What can be checked, before it does, is how the model behaves on months it has not seen: recent years held back from the fit, and records from a past climate that differs from the one the model was fitted on. The second test is the nearer stand-in for a changed future, and it is rarely available.

This paper makes both tests at a coastal dune aquifer with two independent historical epochs, using the standard exponential-response model written month by month (Section 2). It asks four questions. What can the model forecast, and how far can it be trusted (Sections 4 and 5)? Can the model of one well serve its neighbours (Section 4.5)? How long a record does it need (Section 4.3)? And where does the water go: can water levels alone say how the loss splits between drainage and evaporation (Section 6)? A fixed drainage floor, the obvious physical alternative, was also tested; Section 7 says why it was not adopted and what it is still used for. Section 8 sets the answers out as a procedure that a manager with a monthly record can follow.

# []{#anchor}2. Model and test design

## []{#anchor-1}2.1 The starting point: Pastas

Pastas (Collenteur et al., 2019) is widely used open-source software for fitting a groundwater record against rainfall and evaporation. It models the water level, *h*, as a base level, *d*, plus the response to recharge. Levels are measured from the ground surface and are negative below it. Recharge, R, is the month's rainfall, P, plus a share of the potential evapotranspiration, PET. PET is the evaporative demand of the weather. The share is the evaporation factor, *f*. It is negative, so evaporation takes water away. The response to recharge builds up exponentially:

R(t) = P(t) + *f*·PET(t), θ(t) = *A*·(1 − exp(−t/*a*)),

where θ is the step response, the amount of response that has built up by month *t* under steady recharge. *A* is the long-run gain, how far the response finally goes, and *a* is the response time, how quickly it gets there. If recharge is steady within each month, one monthly step of this response is exactly

h(t) − *d* = exp(−1/*a*)·(h(t−1) − *d*) + *A*·(1 − exp(−1/*a*))·R(t).

The base level is fitted along with the response, so the model never needs to know where the water drains to. The drainage rate is set by the response time alone, and the gain *A* scales the response to rainfall and evaporation.

## []{#anchor-1}2.2 Model B: Pastas month by month

Written for one month at a time, the same model predicts the change in level. Rain adds water, evaporation removes it, and drainage removes it at a rate that grows with how high the water table stands. For month *t*,

Δh(t) = α_B + β₁·P(t) − β₂·PET(t) − β₃·(z₀ + h(t−1)).

Here P is the month's rainfall and PET its potential evapotranspiration, from Thornthwaite's method. The coefficients α_B, β₁, β₂ and β₃ are fitted to the record by least squares, and z₀ is a fixed reference level, 3.7 m beneath the ground surface. The term uses the level at the end of the previous month, h(t−1), so that the month's change is not regressed on its own end-point. This is the exponential-response model of Section 2.1, with

β₃ = 1 − exp(−1/*a*), β₁ = *A*·(1 − exp(−1/*a*)), β₂ = −*f*·*A*·(1 − exp(−1/*a*)), *d* = −z_B.

where z_B = z₀ − α_B/β₃ is the level at which the fitted drainage is zero. Because the intercept α_B absorbs any reference level, z₀ drops out of the fit: β₃ is the fraction of a departure from the water table's own equilibrium level that is recovered each month. Under steady weather a departure shrinks by a factor (1 − β₃) each month, so its e-folding time, −1/ln(1 − β₃), is a mean-reversion time, a property of the record rather than of any chosen level. Without a lower limit the fit would make β₃ negative at some wells, which would mean drainage grows as the water table falls; positive drainage is therefore imposed as a bound on β₃. This is called Model B below, to distinguish it from the fixed-floor form of Section 7. Pastas works in days; its parameters were converted to months with the mean month length, and the conversion was checked by fitting Pastas to synthetic wells generated from the cluster coefficients. Fitted to the same wells on the full record, Pastas agrees with Model B well by well (Figure 1): Spearman ρ is 1.00 for β₁, 0.96 for β₂ and 0.98 for β₃, on the 63 wells whose response time Pastas identifies. That agreement checks the code; it is not evidence for the model.

Setting β₃ = 0 removes drainage:

Δh(t) = α₀ + β₁·P(t) − β₂·PET(t).

This is the traditional linear model (TLM), the usual first model of how a water table responds to climate. Run forward, the TLM has nothing pulling the level back towards a mean, so each month's error is carried into every later month. The drainage term provides that pull.

## []{#anchor-1}2.3 How the model is tested

Every result below is a free run. The coefficients are fitted to a record of weather and water levels, and the model is then taken back to the start and run forward on the weather alone, each month from the model's own previous level; the observed level never enters again. Skill is the Nash--Sutcliffe efficiency of the simulated level (NSE; Nash and Sutcliffe, 1970): 1 is perfect, 0 is no better than quoting the well's mean level, and below 0 is worse than that mean. Three tests take the model outside the months it was fitted on. The first splits the modern record at January 2018: the model is fitted on one side and run freely across the other, both ways. The other two tests reach back before the modern network. For both, the model runs from 1930, so the level it starts from is forgotten long before the scored years. The second is the Countryside Council for Wales record of 1989--96, read before the modern network existed, at 9 wells the network still reads, in a decade drier than any the fits contain; it is scored on whether the level is in the right place. The third is Ranwell's readings of 1951--53 (Ranwell, 1959) at three sites whose positions are approximate, each paired with modern wells in the same slack basin; it is scored on the seasonal swing, with each hindcast's mean offset removed.

# []{#anchor-1}3. Site, record and fitting bases

Newborough Warren (Anglesey, Wales) is a coastal dune system of 865 ha. Its monitoring network has 88 dipwells, read at the end of each month. Monthly rainfall and Thornthwaite PET come from a single station, RAF Valley, 16 km away. Thornthwaite's method is used because it needs temperature alone, which the station records from 1930, when the hindcasts begin. The other methods compared can be computed only from 1941 (Hargreaves, Priestley--Taylor and Makkink) or from 1957 (Penman--Monteith, which needs wind and humidity), so none could drive the hindcasts, and Penman--Monteith could not score Ranwell's 1951--53 readings; Section 5.1 compares it with Thornthwaite over 1989--96. Each reading is bucketed to the month it describes, and rainfall and PET enter for the same month, with no lag.

A reference network of 66 wells is admitted on record length. To be admitted, a well needs at least 100 months of record and must still be reporting at the end of the record. Admitted records are longer than this minimum, with a median of 192 months (range 140--252).

The wells fall into five clusters by the shape of their records, before any model is fitted. Each well's monthly level series is compared with every other well's by correlation, so the timing and shape of its rises and falls count and its depth below ground does not, and the wells are grouped by Ward's linkage on one minus that correlation. Three clusters are open dune: C1 Lake Edge, C2 Dune and C3 Western Residual. Two are pine forest: C4 Main Forest and C5 Coastal Forest. The silhouette score is highest at two clusters (0.58), which separates the main forest from the rest; at five it is 0.37. Assignments are stable when wells are resampled (median co-assignment 0.95) and when months are resampled in year-long blocks (0.99), but partitions built from two disjoint samples of the record agree only moderately (adjusted Rand index 0.53, 5--95 % range 0.35--0.73). The clusters are therefore a useful grouping of one continuous aquifer, not sharply bounded units (Hollingham, 2026a).

The coefficients a study reports belong to the record they were fitted on, and in a network installed progressively the record is not one thing. Two fitting bases are used. The first is the cluster centroid on the full record: one hydrograph per cluster, the mean of its members, fitted with every month available. The second is the per-well fit, either on each well's full record or on a common comparison window, the same 100 calendar months at every well, November 2017 to February 2026, so that wells are compared under the same climate. A month in which a well was found dry stays in the window as a level at or below the deepest the dipwell can read, not as a gap. The split-sample tests fit each well on one side of January 2018 and test it on the other. A register lists, for every analysis, the wells, the record fitted and the record evaluated, and is checked automatically against the fitting call in each script before results are published; every coefficient here carries its basis in its source file.

# []{#anchor-1}4. Results

## []{#anchor-2}4.1 What the drainage term adds

At each reference well the TLM and Model B were fitted on the comparison window and each was then run freely over the same months, from the first observed level (Table 1). The test is in-sample: it asks whether a model that has seen the months can reproduce their trajectory without being corrected by them.

**Table 1.** Free-running skill of the traditional linear model (TLM) and Model B, each fitted per well on the reference well's 100-month comparison window and scored over the same months. NSE is the Nash--Sutcliffe efficiency of the simulated level; n is the number of wells.

  --------------------- ---- ------- ------- ---- ----
  C1 Lake Edge          7    0.308   0.878   5    7
  C2 Dune               18   0.391   0.848   14   18
  C3 Western Residual   25   0.439   0.823   24   25
  C4 Main Forest        9    0.541   0.697   8    9
  C5 Coastal Forest     5    0.655   0.809   5    5
  --------------------- ---- ------- ------- ---- ----

Run freely, the TLM drifts. Across the 64 wells its median NSE is 0.43, and it is negative at 8 wells, where a constant at the observed mean would do better. With the drainage term, Model B's median rises to 0.82, and its NSE is positive at all 64 wells. A model without drainage cannot forecast: the drainage term is what pulls the level back towards its mean.

## []{#anchor-2}4.2 Within the recorded climate

Fitted before January 2018 and run freely over the years after, Model B's median NSE is 0.79; fitted after and run back over the years before, 0.78. By cluster, running forward and back, it is 0.85 and 0.83 at the lake edge (C1), 0.81 and 0.81 on the dune (C2), 0.77 and 0.74 in the western residual (C3) and 0.81 and 0.72 in the coastal forest (C5). Under the main forest (C4) it fails, at 0.08 forward and 0.20 in reverse. The split at January 2018 falls a month after the December 2017 clearfell beside the main forest, so at the felled well and the wells beside it the forecast runs across a change the model does not know about. That touches a handful of wells, not whole clusters, and it cannot explain the main forest's failure, which is the same running back, from coefficients fitted after the felling.

## []{#anchor-2}4.3 How much record it needs

Less record than might be expected for a forecast, and more for the drainage coefficient. Fitted on only 24 months before 2018, Model B's median forward NSE is already 0.71, against 0.79 from all of it. Its β₃ settles more slowly. Each well's β₃ was refitted on every non-overlapping placement of each length, and its stable length taken as the shortest record on which the median departure from the full-record β₃ is within 20 %. Model B's median stable length is 60 months (63 wells), or 8.7 mean-reversion times, and β₃ is identified on only 59 % of 24-month placements at the median well. A record should span several mean-reversion times before the time read from it is trusted. Under the main forest β₃ settles at only 6 wells, and only after 144 months.

## []{#anchor-2}4.4 The two hindcasts

Two kinds of hindcast run from 1930 on the RAF Valley weather, and they do different jobs. The per-well hindcasts test the model; the warren hindcast uses it.

In the per-well hindcasts each well free-runs from 1930 on its own present-day coefficients, and its levels over 1989--96 and 1951--53 are scored against readings that no fit has seen. The run is long so that the starting level is forgotten before the scored years: the 1989--96 levels do not depend on it. The coefficients are those of today's aquifer, so the test asks whether today's aquifer, given that era's weather, reproduces the levels then recorded; it is not a reconstruction of the aquifer as it was. These hindcasts carry the out-of-sample evidence of this section and of Section 5.1.

The warren hindcast (Figure 6) describes the open dune as a whole. One rule for the open dune is run from 1930, quantile-mapped to the observed median of the reference network over the years the wells were read, and passed through two curves that relate that median level to the area of open water and of wet slack floor counted on 43 Sentinel-2 scenes (rank correlations 0.80 and 0.85). It shows how wet the warren would have been under the weather of each month since 1930. Because it is calibrated to the well record, it is not evidence of the model's skill.

On the drier decade, with each well's coefficients fitted to its last 100 months of record, which do not overlap the years being predicted, Model B puts the water table 0.21 m too high at the median well (0.23 m with coefficients fitted to the whole record). Here the question is whether the model puts the level in the right place, and it does not. Its median NSE is −0.06, below zero because the monthly errors exceed the spread of the levels about their own 1989--96 mean; on this test the bias, not the NSE, is the measure. The spread matters as well as the median (Figure 5): at most wells the free run tracks the measured record closely over seven years it never saw, and at two it sits well above the readings through the dry middle years, at one of them because the readings there record the bottom of the dipwell, not the water table.

On Ranwell's seasons Model B does well. With each hindcast's mean offset removed, its median NSE is 0.86 at the three headline pairings and 0.69 over all eleven. The seasonal timing is reproduced at all three sites. The 1951 summer draw-down is under-predicted at two of them, and the 1953 recession over-predicted.

The two results do not conflict: the seasons test scores the swing about the mean, and the drier decade scores the mean itself. Section 5.1 takes up why the model is too wet there.

## []{#anchor-2}4.5 Neighbouring wells

Clusters are formed from the hydrographs alone (Section 3), so a well can be placed in one by correlating its record with the cluster centroids, without fitting it. Lending it the cluster's coefficients then rests on two things: that a short record places the well correctly, and that cluster coefficients forecast as well as its own. Each skill test was run twice: on each well's own coefficients, and on its cluster centroid's fitted on the same span, shifted by the mean difference between the well and its centroid over the fitted months. By a rule fixed before the run, the cluster basis holds on a test if its median NSE is within 0.05 of the per-well basis or better, and, on the drier decade, its median absolute bias within 0.05 m or smaller.

The cluster coefficients forecast as well as the wells' own: across the 2018 split their median NSE is 0.80 forward and 0.77 in reverse, against 0.79 and 0.78, and on Ranwell's seasons 0.86 against 0.86. On the drier decade their median NSE is −0.27 against −0.18, outside the tolerance, though their median absolute bias is smaller (0.19 m against 0.23 m). A new well is placed in its correct cluster from two years of readings at 62 % of wells and from three years at 76 %. Placed from two years and run on its cluster's coefficients, it forecasts at 0.76 forward and 0.77 in reverse.

Where a well's own record has a gap, it is better filled from a measured neighbour than from any model. With stretches of 54 months hidden in turn, each well's mean spring level was put back from its nearest cluster-mate with a median miss of 0.041 m, against 0.139 m from a model run on the weather. This tests the repair of a record, not prediction. The direct test runs one well's coefficients, fitted before 2018 with the intercept borrowed with them, at its nearest neighbour (median distance 123 m), scored on the neighbour's record after 2018 against tolerances fixed in advance: 0.05 in r² and 0.05 m in median absolute bias. It holds across the open dune: median r² 0.82 against 0.83 on the wells' own coefficients, and median absolute bias 0.10 m against 0.07 m. In the forest the shape transfers (0.68 against 0.72) but the level does not (0.33 m against 0.19 m). C3's level sits at the bar: 0.0497 m worse, against a tolerance of 0.05 m, a margin smaller than the drift between reruns. A cluster centroid does worse than a neighbour on level (0.26 m in the open dune).

## []{#anchor-2}4.6 What the model lets you predict

There are two choices in using the model: a well's own coefficients or its cluster's, and the full record or only a few years. On the coming years any combination serves: own coefficients on the full record 0.79, on 24 months 0.71; cluster coefficients 0.80, and 0.76 for a new well placed from 24 months. This is the result a manager with a new dipwell can use. On another climate's seasons a well's own coefficients or its cluster's serve (0.86 and 0.86); a new well placed from two years drops to 0.78, outside the tolerance set before the test. For a lasting drier shift none of them serves: every combination puts the 1989--96 water table too high, by 0.20--0.39 m on short records and by a median absolute 0.19--0.37 m on cluster coefficients, because the error comes from the model, not from the wells or the record.

## []{#anchor-2}4.7 What the drainage coefficient measures

The mean-reversion time can be measured without the model. Take each month's level less the mean for its calendar month. If this is treated as a first-order autoregressive process with lag-1 autocorrelation ρ₁, anomalies decay with the e-folding time −1/ln ρ₁ (Delworth and Manabe, 1988), as level autocorrelation is used to characterize groundwater drought persistence (Bloomfield and Marchant, 2013). The model-free median is 5.1 months, against Model B's 6.5. Cluster by cluster Model B sits with it: 2.1 against 2.0 months at C1, 4.4 against 4.1 at C2, 7.4 against 6.3 at C3 and 13.3 against 12.0 at C5. At C4, where the observed time is 15.6 months, β₃ is not identified on the record. Removing a linear trend gives a model-free median of 5.0 months, and correcting ρ₁ for reading error 6.1.

A short mean-reversion time also predicts that spring levels in successive years are close to independent. The drainage term implies an expected lag-1 autocorrelation of spring level of (1 − β₃)¹², which is 0.16 at the median well; the observed value is −0.11. The drainage coefficient is therefore a measure of how quickly the water table recovers from a wet or dry spell, which the record confirms, and not a recession towards a physical floor. The literature calls both readings a memory, the time a groundwater system takes to re-equilibrate with a change in recharge (Cuthbert et al., 2019) and the persistence of level anomalies (Nygren et al., 2022); here it is the second.

# []{#anchor-2}5. Limitations of the model

These limits are stated wherever the model's results are used.

## []{#anchor-3}5.1 A drier climate

The model puts the 1989--96 water table about 0.2 m too high at the median well (Section 4.4). That is larger than the change the record was meant to measure. Any model that fits its own base level learns that level from the modern record, which includes the recent wet years, and the water-balance reading of Section 6 does the same (too wet by 0.34 m over 1989--96). In Model B the level returns quickly to that base, and the lasting response to a change in climate is smaller the faster the level returns, so a drier decade pulls the modelled level down less than the real one fell.

The two epochs ask for two time scales, a fast return to the mean and a slow one that holds the level through a drier decade. A single linear store has one. A second, slower store driven by the same climate was therefore fitted at every cluster centroid, including one drawn down by the plantation as its canopy closed. No version passed the tests fixed before the fit: either the information criterion preferred one store, or the slow store forecast worse beyond 2018.

Two other explanations were checked. The hindcast assumes the coefficients were the same then as now. Fitting 17 wells separately before and after the December 2017 clearfell, the rainfall response fell by 4.7 % across all of them, by 13 % at the wells beside the felling and by under 1 % at the two groups of unfelled control wells (−0.8 % and −0.3 %), so away from felling the assumption holds; and felling raises the water table, so where it reached a well it would make the model look less wet, not more. The evaporation formula is not the cause either: Penman--Monteith, computed from the station's full weather record, puts demand in 1989--96 lower relative to the fitting window than Thornthwaite does, which would raise the modelled level further, and by about a tenth of the bias.

## []{#anchor-3}5.2 The main forest

Under the main forest (C4) β₃ is not identified on the record, and the split-sample forecast fails (Section 4.2). C4 is therefore withheld from projection, no mean-reversion time is quoted there, and its results are reported as a range, never as a median. Whether the forest's slow response is real, or a forcing that misrepresents the forest's evapotranspiration, the record does not resolve. The coastal forest (C5) is forest too and does not behave like C4, which points to C4's own ground rather than its canopy.

## []{#anchor-3}5.3 The fitted base is not a physical floor

Model B pays for its fit. Its intercept and β₃ are almost interchangeable: their estimates correlate at 0.96 at the median well. The level its drainage refers to is therefore fitted rather than physical, and lies near each well's mean, a median 1.6 m below ground. It restates the water level rather than measuring a floor, and its drainage coefficient is not a conductivity: the model has one store per well, with no lateral flow between wells.

## []{#anchor-3}5.4 Projections, with the bound

Take the UKCP18 high-emissions scenario (RCP8.5; Met Office, 2018), applied as seasonal changes to the observed rainfall and PET, with comparison-window fits at the 57 wells where β₃ is identified both by Model B and with a fixed floor (Section 7). In the 2050s the median sustained fall of the summer level is 0.20 m. The 2050s scenario lowers the annual water balance (rainfall less PET) by 117 mm a year, about as much as the drier decade of 1989--96 fell below the modern record (110 mm a year), so this projection sits inside the range the hindcast has tested, and carries its bias. In the 2080s the median fall is 0.37 m, under a scenario that lowers the annual water balance by 210 mm a year, beyond anything in the record. Because the model is too wet in a drier climate, these falls are likely to be too small. The bound is the fixed floor of Section 7, whose slower return carries a summer deficit forward: 0.28 m in the 2050s and 0.52 m in the 2080s. It is quoted beside every projection as a bound, not as a second answer. The main forest is not projected.

# []{#anchor-3}6. Partitioning the water balance

## []{#anchor-4}6.1 What heads cannot fix

The water table loses water in two ways: by drainage, and by evapotranspiration. Heads alone cannot say how the loss splits between them, because the split depends on the level drainage is measured from, and Model B's level is fitted (Section 5.3). Without an independent measurement of at least one flux (drainage, evapotranspiration or recharge), no head-only model can fix the true split. One bound, however, needs no such measurement. Actual evapotranspiration cannot exceed the potential, and over a long record the mean change in storage is negligible, so the water balance puts drainage at or above the excess of rainfall over PET. That is a floor on drainage, not a split.

## []{#anchor-4}6.2 Three readings of the split

Three readings are reported, each free of something the others need (Table 2). Model B's own partition puts drainage at 45 % of the mean annual loss at the median well. It follows from β₁ and β₂, which Model B identifies and Pastas reproduces, but its drainage is measured from a fitted base.

The seasonal recession rates read the split without any model. Winter recession, with potential evapotranspiration near zero, is close to drainage alone, and summer recession is drainage and evapotranspiration together, so this recession ratio, of the mean monthly recession rates, is drainage's share of the summer loss, and it needs neither a base nor a storage coefficient: 60 % at C1, 35 % at C2, 66 % at C3, 51 % at C4 and 73 % at C5. It is a share of summer recession rather than of the mean annual loss; it rests on the months in which the level fell at all, 27 winter months at C1 against 50 summer months; and drainage rises with head, which inflates a winter numerator.

A water balance reads the split with the storage coefficient taken from outside the fit. Rainfall less potential evapotranspiration is a monthly surplus; the change in storage is the water-table change multiplied by the well's apparent storage coefficient Sₐ, measured by the water-table fluctuation method (the 'apparent specific yield' of Healy and Cook, 2002) and fixed before the fit; and what the surplus does not account for is taken as drainage and regressed on the previous month's head (Figure 2). Sₐ is two to three times the textbook specific yield of dune sand, because the fluctuation method takes in the moist zone above the water table as well as the sand; it ranks wells reliably but is high in absolute terms. Over 66 wells the water balance books between 0.74 and 0.97 of potential evapotranspiration as actual, cluster by cluster (Figure 3). Winter months, with evapotranspiration near zero, estimate Sₐ and the drainage law together and borrow nothing from the fluctuation method; both regression directions are fitted, because the rainfall comes from an off-site gauge and the head change carries reading error. With the fluctuation-method Sₐ the water balance puts drainage at 31 % of the annual loss at the median well; with the winter fit's two Sₐ estimates, which lie mostly below it, it puts drainage at 36--55 %. These are two water-balance estimates, not an interval around 31 % (Figure 4): the winter fit's higher Sₐ sits at the fluctuation-method value at every cluster except C1. The reading is a diagnostic and not a forecaster: run free on the half of the record it was not fitted to it reaches a median NSE of 0.70 forward and 0.62 in reverse, against Model B's 0.79 and 0.78.

**Table 2.** The drainage share of the mean loss per cluster, three ways (%). Model B: the cluster-centroid partition. Recession ratio: the winter over the summer mean monthly recession rate, with no model. Water balance: the drainage share of the mean annual loss with Sₐ from the fluctuation method. ---: β₃ not identified at C4. The water balance counts every loss of the rain, including water that evaporates before it reaches the water table, so its share is not on quite the same footing as the other two.

  --------------------- ----- ---- ----
  C1 Lake Edge          38    60   47
  C2 Dune               45    35   35
  C3 Western Residual   56    66   30
  C4 Main Forest        ---   51   16
  C5 Coastal Forest     61    73   24
  --------------------- ----- ---- ----

The three readings agree on the dune (C2). They differ most in the western residual and the coastal forest, where the water balance sends far less of the loss to drainage than the other two; there either Sₐ is too high or water flows in from higher ground, and changing the evaporation formula does not close the gap. At single wells they do not agree at all, so the split is given cluster by cluster and reported as not identified by heads. Only an independent flux measurement, from tracers, outflow gauging or eddy covariance, can close it.

## []{#anchor-4}6.3 Interception and the forest

Under the pine forest the canopy intercepts part of the rain, which evaporates without reaching the ground. The model is fitted on gross rainfall and on demand above the canopy, so its evaporation term already carries that interception loss, and the water balance books interception inside the evaporation, not on top of it. So booked, the main forest's total evaporation is 633 mm a year, 0.97 times Thornthwaite PET, within what the weather allows. A scan of the interception fraction closes the forest's atmospheric loss against PET at 0.20 in the coastal forest, consistent with the adopted fraction, and at 0.15 under the main forest, where the drainage shows no dependence on head at any fraction scanned, so what the scan returns there measures an assumed drainage law as much as a canopy.

# []{#anchor-4}7. Comparison with a fixed-floor model

The obvious alternative to a fitted base is to fix the floor in advance, so that drainage runs to a real level and β₃ cannot come out negative: the same model without an intercept (Model A), with z₀ set at 3.7 m below ground at every well, or at each well's depth to the sea at mean high water (1.88 m above Ordnance Datum, 1.7--12.5 m below ground), the one physical drainage base that can be named. Neither was adopted. It forecast no better: across the 2018 split its median NSE is 0.61 forward at 3.7 m and 0.46 at mean high water, against Model B's 0.79. Choosing the floor by fit turns it into Model B: refitted at every depth from 0.5 to 8.0 m, the best-fitting floor differs by cluster (0.7 m at the lake edge, 7.1 m under the main forest), and at every cluster it matches Model B's own zero-drainage level. Its distinctive results, the drainage share and the size of a lasting shift, are set by where the floor is put, and nothing measured fixes the floor. And it did not deliver the physics it was built for: at one main-forest well, CEH14, the 3.7 m floor still returns a negative β₃ and the free run diverges (NSE −12.87, against −0.04 for the TLM and 0.38 for Model B). Positive drainage is imposed directly instead, as the bound on Model B's β₃.

The fixed floor keeps two jobs. It is the robustness check: a result is reported as a finding only if it holds under both forms, in the same direction and, where significance is tested, significant under both. The drainage term's improvement over the TLM passes (0.77 with the fixed floor, 0.82 for Model B), as does the rise of the rainfall response inland within C3. Results that exist only because the floor is fixed do not pass and are not reported: an identified drainage coefficient and recession time under the main forest, an inland gradient of β₃ within C3, a coupling of evaporation to depth at the lake edge, and coefficient effects of forest management, which change sign with the floor. Felling and scraping are detected instead from the observed step at treated wells against untreated controls. And it is the bound in a drier climate. With its slower return, the fixed floor at 3.7 m puts the 1989--96 level within 0.03 m at the median well, though by errors that cancel from well to well, while the floor at mean high water puts it 0.16 m too low; its larger summer fall is the bound quoted with the projections (Section 5.4). What would bring the fixed floor back is a measured drainage base, such as a mapped till surface or an estuary outlet level.

# []{#anchor-5}8. Application: a procedure for managers

The procedure below is for a manager with a monthly water-level record and no measured fluxes, who wants to know what the record can forecast and how far to trust it.

1.  **Fit the model** with a free base level (Model B, or Pastas's exponential response), at the scale at which results will be used: each well, or each group of wells that rise and fall together. Keep β₃ positive by a bound.
2.  **Test what the drainage term adds**. Run the model freely from the first observed level and compare it with the same model without drainage. A model that drifts without its drainage term cannot forecast.
3.  **Test forecasts within the record**. Fit on one part of the record and run freely over the other, in both directions.
4.  **Test against a different climate** wherever an older record exists, even a few wells or a few years, and score the level, not only the swing. A sustained shift of the mean level is the nearest test of a changed future; where the model fails it, quote its bias beside every projection, with a bound.
5.  **Check the record is long enough**. Refit on shorter stretches and see when the drainage coefficient stops moving. The record should span several mean-reversion times; slow forest wells need much longer.
6.  **Referee the time scale without a model**. Compare the model's e-folding time with the lag-1 autocorrelation of the deseasonalized level, and report it as how quickly the water table recovers.
7.  **Treat the split of the loss as not identified** by heads. Report the readings that are available, the floor on drainage, and the measurement that would settle it.
8.  **Declare the fitting basis** of every result, lend a new well its cluster's coefficients once a short record has placed it, and fill gaps in a well's record from measured neighbours rather than from the model.

Table 3 sets out what the procedure gives at Newborough.

**Table 3.** The procedure applied at Newborough, per cluster. Coefficients and closure residual (Residual): Model B fitted to each cluster centroid; the residual of the mean water balance is in units of water-table change. Drainage share: Model B's partition of the mean loss at the centroid. τ_B, mean-reversion time: median over the cluster's wells of Model B's e-folding time; τ_obs, the model-free estimate from the level's lag-1 autocorrelation (Section 4.7). L_B, record for a stable β₃: median, over the wells that reach it within the lengths tested, of the shortest record on which the median departure from the full-record β₃ is within 20 % (Section 4.3). n.i.: not identified on the record.

  --------------------- ------- ------- ------- ------ ------ ------------- -----
  C1 Lake Edge          3.715   3.144   0.354   38     −0.2   2.1 / 2.0     60
  C2 Dune               3.500   2.619   0.167   45     0.0    4.4 / 4.1     48
  C3 Western Residual   3.604   2.126   0.103   56     1.6    7.4 / 6.3     80
  C4 Main Forest        2.578   2.499   0.010   n.i.   −0.5   n.i.          144
  C5 Coastal Forest     2.463   1.335   0.045   61     −3.2   13.3 / 12.0   100
  --------------------- ------- ------- ------- ------ ------ ------------- -----

# []{#anchor-6}9. Discussion and open questions

## []{#anchor-6}9.1 What heads alone can and cannot give

The two results a reader of a head-only model most needs are discussed where they are established: what the drainage coefficient measures (Section 4.7), and why water levels alone cannot split the loss (Section 6). A head-only model can always close the mean balance, because the water level records the net of what enters and leaves. What it can be trusted to forecast depends on the test it has passed. Within the recorded climate, the split-sample test, the model-free time scale and the seasons of another climate agree: Model B forecasts the water table, from a short record and on borrowed coefficients. Beyond the recorded climate only an independent epoch can say, and here it says the level of a lastingly drier climate is overestimated. A manager forecasting next year's spring level can use the model as it is; one projecting the 2080s should quote it with its bias and its bound. What heads alone cannot give is the split of the loss between evapotranspiration and drainage (Section 6).

## []{#anchor-6}9.2 Relation to transfer-function practice

Free-base transfer-function models, of which Pastas is the reference implementation, are the right form for forecasting within the recorded climate, and their agreement here with the model-free estimate and the split-sample test supports that use. What transfer-function practice does not usually do is test a forecast against a different climate. At this site that test finds the model's main limitation, and it needed records older than the network. The two practices are complementary: the fit says what the record supports, and the old records say how far it carries.

## []{#anchor-6}9.3 Limits

The forcing comes from one climate station outside the site, at monthly resolution. Thornthwaite PET is an index of demand rather than a measured flux, so β₂ is an effective coefficient. The model is linear, one-dimensional and time-invariant; changes in land cover over the record are handled elsewhere, by before--after designs. The depths below ground rest on a 2 m LiDAR terrain model, whose stated vertical accuracy is about ±0.15 m on open ground. The projections scale the observed climate by seasonal factors and assume the coefficients hold under a climate the record has not seen. The independent tests of a lasting shift rest on 9 wells in one decade, and the seasons test on three approximately placed sites in another.

## []{#anchor-6}9.4 Open questions

Three questions remain, each with the measurement or test that would settle it. How does the loss split between drainage and evaporation? A measured flux would settle it. Where is the drainage base? A mapped till surface or an estuary outlet level would fix the floor independently of the fit, and would bring a fixed floor back as a physical model. And what quantity matters ecologically? The model gives monthly level, depth below ground, seasonal range and recovery time; if what matters for the vegetation is the duration above a threshold, the timing of the spring maximum or the months within reach of the roots, the model should be scored on that.

# []{#anchor-6}10. Conclusions

A head-only model fitted to a monthly water-level record, the standard exponential-response model written month by month, forecasts that record's water table: within the recorded climate it does so from two years of record, and a new well can borrow its cluster's coefficients. Its drainage coefficient measures how fast the water table returns to its mean, which a model-free estimate confirms, not drainage to a physical floor.

Its main limitation is a lastingly drier climate. Against a drier decade that no fit had seen it puts the water table about 0.2 m too high, so its projections of a falling water table are likely to be too small. At Newborough, under a high-emissions climate, it puts the median fall of the summer level at 0.20 m in the 2050s, within the range the hindcast has tested, and 0.37 m in the 2080s, beyond it, with a fixed floor's 0.52 m as the bound. The main forest is withheld, because its drainage coefficient is not identified on the record.

Water levels do not fix the split of the loss between drainage and evaporation. The model and a water balance that fixes Sₐ from outside the fit put drainage at 45 % and 31 % at the median well; readings that do not agree are an argument for a measured flux, not for another reading. A fixed drainage floor, tested as the physical alternative, forecast no better and is kept as a robustness check and a bound. Each of these tests should be repeated at every site, with the fitting basis declared.

# []{#anchor-6}Data availability

The monitoring record, the analysis pipeline and every committed output from which the numbers in this paper are set are available in the project repository (https://github.com/newbroman/Newborough_Hydrology). Each number quoted in the text is read from a named committed output file.

# []{#anchor-6}Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work the author used Anthropic's Claude (successive Claude Opus and Claude Fable models, accessed through the Claude desktop application) for substantial drafting and editing of the manuscript text: composing prose from the author's analytical outputs and decisions, structuring and restructuring sections, and correcting the text against the study's committed analytical outputs. The conception and design of the study, the twenty-one-year manual dipwell record on which it rests, the analytical decisions, and the interpretation of the results are the author's own. Numerical values in the manuscript are set from the committed outputs of the analysis pipeline, and a decision log records the methodological and editorial calls made by the author during the work. After using this tool the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

# []{#anchor-6}Figures

![](Pictures/1.png){width="311.11pt" height="560pt"}

Figure 1. Per-well coefficients of Pastas's exponential-response model against Model B on the full record: Model B filled; hollow, the fixed-floor form of Section 7, for comparison; crosses mark wells whose response time Pastas does not identify. Dashed: 1:1.

![](Pictures/2.png){width="468.00pt" height="176.80pt"}

Figure 2. The residual drainage law. Left: each reference well's drainage rate k above its threshold against the threshold depth h₀, by cluster. Right: the fraction of each cluster's wells at which the threshold form beats the straight line by more than 2 in BIC.

![](Pictures/3.png){width="468.00pt" height="306.00pt"}

Figure 3. Evapotranspiration inferred from the winter drainage law, as a fraction of potential evapotranspiration: each well's summer fraction against its annual, by cluster. Line: 1:1.

![](Pictures/4.png){width="468.00pt" height="284.14pt"}

Figure 4. The drainage share of the mean annual loss, by cluster. The bars use the fluctuation-method Sₐ. The red span shows the shares given instead by the two Sₐ values of the winter joint fit, and the dashed line is the network median. That span is not a confidence interval, and it is not centred on its bar: a smaller Sₐ books less storage, which leaves a larger share to drainage. It therefore lies wholly above the bar at C2--C5, and straddles it only at C1, the cluster whose share depends most on choices this balance cannot settle.

![](Pictures/NRG_39_04_hindcast.png){width="468.00pt" height="600.35pt"}

Figure 5. The per-well hindcast of 1989--96. Each well free-runs from 1930 on Model B coefficients fitted to its last 100 months of record, which do not overlap the decade, and is compared with the Countryside Council for Wales readings.

![](Pictures/NRG_47_04_hindcast_still_2000-12.png){width="468.00pt" height="263.25pt"}

Figure 6. One month of the warren hindcast (December 2000). The open-dune rule, run from 1930 and quantile-mapped to the reference network's observed median over the well years, is shown through the two Sentinel-2 wet-area curves. It uses the model and is calibrated to the well record; it is not a test of skill.

# []{#anchor-6}References

Akaike, H. (1974) A new look at the statistical model identification. *IEEE Transactions on Automatic Control* 19(6), 716--723. doi:10.1109/TAC.1974.1100705

Bakker, M. and Schaars, F. (2019) Solving groundwater flow problems with time series analysis: you may not even need another model. *Groundwater* 57(6), 826--833. doi:10.1111/gwat.12927

Bloomfield, J.P. and Marchant, B.P. (2013) Analysis of groundwater drought building on the standardised precipitation index approach. *Hydrology and Earth System Sciences* 17(12), 4769--4787. doi:10.5194/hess-17-4769-2013

Collenteur, R.A., Bakker, M., Caljé, R., Klop, S.A. and Schaars, F. (2019) Pastas: open source software for the analysis of groundwater time series. *Groundwater* 57(6), 877--885. doi:10.1111/gwat.12925

Cuthbert, M.O., Gleeson, T., Moosdorf, N., Befus, K.M., Schneider, A., Hartmann, J. and Lehner, B. (2019) Global patterns and dynamics of climate--groundwater interactions. *Nature Climate Change* 9(2), 137--141. doi:10.1038/s41558-018-0386-4

Delworth, T.L. and Manabe, S. (1988) The influence of potential evaporation on the variabilities of simulated soil wetness and climate. *Journal of Climate* 1(5), 523--547. doi:10.1175/1520-0442(1988)001\<0523:TIOPEO\>2.0.CO;2

Healy, R.W. and Cook, P.G. (2002) Using groundwater levels to estimate recharge. Hydrogeology Journal 10(1), 91--109.

Hollingham, M. (2026a) A parameter-sparse state-space framework for characterizing coastal dune-aquifer architecture from manual dipwell records. Companion paper.

Knotters, M. and Bierkens, M.F.P. (2000) Physical basis of time series models for water table depths. *Water Resources Research* 36(1), 181--188. doi:10.1029/1999WR900288

Knotters, M. and van Walsum, P.E.V. (1997) Estimating fluctuation quantities from time series of water-table depths using models with a stochastic component. *Journal of Hydrology* 197(1--4), 25--46. doi:10.1016/S0022-1694(96)03278-7

Met Office (2018) UKCP18 Regional Projections on a 12 km grid over the UK for 1980--2080. Centre for Environmental Data Analysis. Met Office Hadley Centre. Available at: https://catalogue.ceda.ac.uk/uuid/b4d24b3df3754b9d9028447eb3cbd878

Nash, J.E. and Sutcliffe, J.V. (1970) River flow forecasting through conceptual models. Part I --- A discussion of principles. *Journal of Hydrology* 10(3), 282--290.

Nygren, M., Barthel, R., Allen, D.M. and Giese, M. (2022) Exploring groundwater drought responsiveness in lowland post-glacial environments. *Hydrogeology Journal* 30(7), 1937--1961. doi:10.1007/s10040-022-02521-5

Obergfell, C., Bakker, M. and Maas, K. (2019) Identification and explanation of a change in the groundwater regime using time series analysis. *Groundwater* 57(6), 886--894. doi:10.1111/gwat.12891

Peters, E., Torfs, P.J.J.F., van Lanen, H.A.J. and Bier, G. (2003) Propagation of drought through groundwater --- a new approach using linear reservoir theory. *Hydrological Processes* 17(15), 3023--3040.

Peterson, T.J. and Western, A.W. (2014) Nonlinear time-series modeling of unconfined groundwater head. *Water Resources Research* 50(10), 8330--8355. doi:10.1002/2013WR014800

Ranwell, D.S. (1959) Newborough Warren, Anglesey. I. The dune system and dune slack habitat. *Journal of Ecology* 47(3), 571--601.

von Asmuth, J.R., Bierkens, M.F.P. and Maas, K. (2002) Transfer function-noise modelling in continuous time using predefined impulse response functions. *Water Resources Research* 38(12), 1287. doi:10.1029/2001WR001136
