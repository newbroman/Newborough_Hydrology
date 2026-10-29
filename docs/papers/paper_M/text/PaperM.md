<!-- GENERATED MIRROR of docs/papers/paper_M/PaperM_v1_40.odt — do not edit. source-sha256=ad7a33242b4e39f0 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you

M. Hollingham

Draft --- 2026

# []{#anchor}Abstract

Monthly water-level records from shallow dipwells are often the only long record a wetland manager has. Simple reservoir models fitted to them are used to forecast the water table and to judge the aquifer, but whether such a model can be trusted to forecast is rarely tested. We test one linear-reservoir model in its two common forms, without an intercept and with a free one, on 66 wells of a coastal dune aquifer at Newborough Warren, Wales. Within the climate of the record the free-intercept form forecasts better: fitted before 2018 and run freely after it, its median Nash--Sutcliffe efficiency is 0.79 against 0.61, and a few years of record suffice. Against a drier decade that no fit has seen, 1989--96, the order reverses: the no-intercept form is close to unbiased (0.03 m) and the free-intercept form too wet by 0.30 m. The forms differ because their drainage coefficients measure different things: a recession above an assumed datum, and the time the water table takes to return to its own mean (15.8 against 6.5 months at the median well; 5.1 months without a model). Under a 2080s high-emissions climate the two forms bracket a median fall of the summer level of 0.37--0.52 m. We give a procedure that tells a manager which form to use for each question, and when a record is long enough to answer it.

**Keywords:** groundwater forecasting; hindcast; linear reservoir; drainage datum; mean-reversion time; dune slack

# []{#anchor}Plain-language summary

Many wetlands depend on groundwater, such as the damp hollows (dune slacks) among sand dunes. They are usually monitored by measuring the water level in shallow pipes about once a month. Managers want to know what those levels will do next, especially as the climate changes, and a simple mathematical model fitted to the record is the usual way to find out.

This paper asks when such a model can be trusted to forecast. It tests two common versions of the same model on 66 monitoring wells at Newborough Warren, a coastal dune system on Anglesey in Wales. Because the future cannot yet be checked, the models were tested in two other ways: on recent years held back from the fit, and on old records from drier times, made before the present wells were installed.

The two tests disagree. One version forecasts the recent years better; the other reproduces the drier past better. The reason is that the model's drainage number means something different in each version: in one, how fast stored water drains towards an assumed floor; in the other, how quickly the water table returns to its normal level after a wet or dry spell. Under a high-emissions climate in the 2080s the two versions together put the typical fall of the summer water table at between about a third and a half of a metre.

The paper ends with a step-by-step procedure that tells managers which version to use for each question, and how long a record each needs.

# []{#anchor}1. Introduction

Shallow groundwater governs the condition of dune slacks, fens, wet heaths and other groundwater-dependent wetlands. In most places, the record on which their management rests is a network of dipwells read by hand about once a month. What managers most want from that record is a forecast: how the water table will respond to the coming years, and to a changing climate. Recharge, drainage and evapotranspiration are rarely measured at such sites, so the forecast comes from a model fitted to the levels themselves.

Two families of head-only model are in common use. Transfer-function-noise models represent the level as the convolution of each driver with an impulse response, the simplest being the exponential response of a single linear reservoir (von Asmuth et al., 2002; Knotters and Bierkens, 2000). They are implemented in open software, notably Pastas (Collenteur et al., 2019) and HydroSight (Peterson and Western, 2014), and have been applied to shallow unconfined aquifers in a range of settings (Obergfell et al., 2019; Bakker and Schaars, 2019). State-space or difference-equation forms write the same reservoir directly as a monthly balance, in which the change in level is driven by rainfall, by evaporative demand and by a drainage loss proportional to the head above a base (Knotters and van Walsum, 1997; Peters et al., 2003).

Such a model can be fitted with or without an intercept, and the choice is seldom reported. It changes what the drainage coefficient means, and with it how the model behaves when run forward. A forecast cannot be checked until the future arrives. What can be checked, before it does, is how each form behaves on months it has not seen: recent years held back from the fit, and records from a past climate that differs from the one the model was fitted on. The second test is the nearer stand-in for a changed future, and it is rarely available.

This paper makes that test at a coastal dune aquifer with two independent historical epochs, and asks what a head-only model can be trusted to forecast. It makes four contributions. First, the no-intercept and free-intercept forms are one model family, separated only by the datum. The free-intercept form is the no-intercept form at a fitted datum. It is also the Pastas exponential-response model (Collenteur et al., 2019) written month by month, with each term matching one in Pastas (Section 2). Second, the two forms forecast differently, and the tests that favour each differ: the free-intercept form wins within the recorded climate, and the no-intercept form against a drier past (Section 4). Third, the drainage coefficient carries two readings, a recession above an assumed datum and a mean-reversion time, and a model-free estimate shows which the dynamics follow (Section 5). Fourth, the record decides how far either can be trusted. Section 6 sets these out as a procedure that a manager with a monthly record can follow.

# []{#anchor}2. The model

## []{#anchor}2.1 The displacement form

The model predicts how much the water level changes in a month. Three things drive the change: rain adds water, evaporation removes it, and drainage removes it at a rate that grows with how high the water table stands. For month *t*,

Δh(t) = β₁·P(t) − β₂·PET(t) − β₃·h_disp(t−1), with h_disp(t−1) = z₀ + h(t−1).

Here *h* is the water level, measured from the ground surface and negative below it. P is the month's rainfall and PET its potential evapotranspiration. The coefficients β₁, β₂ and β₃ are fitted to the record.

The drainage term needs a reference level, the drainage datum, at depth z₀ below ground. h_disp is the height of the water table above that datum. Written this way, β₃ is positive wherever the water table lies above the datum, and drainage is proportional to head above a base. This is the linearized Darcy flux of a shallow unconfined aquifer draining to a boundary (Knotters and van Walsum, 1997). The term uses the level at the start of the month, h(t−1), so that the month's change is not regressed on its own end-point. Measured from the ground surface instead (z₀ = 0), 2 of the five clusters at this site return a negative β₃, which would mean drainage grows as the water table falls.

## []{#anchor}2.2 Model A and Model B

Model A is the equation above, fitted by ordinary least squares with no constant term (no intercept). Model B adds a constant, α_B:

Δh(t) = α_B + β₁·P(t) − β₂·PET(t) − β₃·(z₀ + h(t−1)).

The constant can be folded into the drainage term. Because −β₃·z₀ is also a constant, Model B is Model A with the datum moved to

z_B = z₀ − α_B/β₃,

the level at which the fitted drainage is zero. The two forms are therefore one family, and they differ only in where the datum comes from: Model A fixes it in advance, Model B fits it.

In Model A the choice of datum changes the coefficients. There is no constant to absorb a change in z₀, so moving the datum shifts β₁, β₂ and β₃ together. The mean drainage loss, β₃ times the mean height above the datum, must still balance the mean water budget, so as the datum is set deeper β₃ falls and the recession half-life t½ = ln 2/β₃ rises. In Model B the datum drops out. β₃ is then the fraction of a departure from the water table's own equilibrium level that is recovered each month. Under steady weather a departure shrinks by a factor (1 − β₃) each month, so its e-folding time is −1/ln(1 − β₃). This is the mean-reversion time, a property of the record rather than of any reference level.

Setting β₃ = 0 in Model B removes drainage:

Δh(t) = α₀ + β₁·P(t) − β₂·PET(t).

This is the traditional linear model (TLM), the usual first model of how a water table responds to climate. Run forward, the TLM has nothing pulling the level back towards a mean, so each month's error is carried into every later month. The drainage term provides that pull.

## []{#anchor}2.3 Relation to Pastas

Pastas (Collenteur et al., 2019) is widely used software for the same task. It models the level as a base level, *d*, plus the response to a recharge series. In its linear setting, recharge is rainfall plus a (negative) fraction of PET, and the response to recharge builds up exponentially:

R(t) = P(t) + *f*·PET(t), θ(t) = *A*·(1 − exp(−t/*a*)),

where *A* is the long-run gain, *a* the response time and *f* the evaporation factor. If recharge is steady within each month, one monthly step of this response is exactly

h(t) − *d* = exp(−1/*a*)·(h(t−1) − *d*) + *A*·(1 − exp(−1/*a*))·R(t).

This is Model B, with

β₃ = 1 − exp(−1/*a*), β₁ = *A*·(1 − exp(−1/*a*)), β₂ = −*f*·*A*·(1 − exp(−1/*a*)), *d* = −z_B.

The drainage rate is set by the response time alone, the gain *A* scales the response to rainfall and evaporation, and Pastas's base level is Model B's zero-drainage level (Section 2.2), with its sign reversed because Pastas measures levels upwards. Pastas works in days; its parameters were converted to months with the mean month length, and the conversion was checked by fitting Pastas to synthetic wells generated from the cluster coefficients. Model A has no Pastas equivalent, because Pastas has neither a fixed datum nor a separate drainage term. Agreement between Pastas and Model B therefore checks the code. It is not independent evidence for either form (Section 5.6).

## []{#anchor}2.4 What neither form can decide

The water table loses water in two ways: by drainage, and by atmospheric draw (evapotranspiration). Heads alone cannot say how the loss splits between them, because the split depends on the level drainage is measured from. Model A sets that level by assumption and Model B by fit. Without an independent measurement of at least one flux (drainage, evapotranspiration or recharge), neither form can fix the true split.

A second limit applies to Model A's split. Evaporation from a shallow water table falls as the water table deepens, so it varies with head as drainage does, and the fit books it to β₃. Letting evaporative draw decline with depth to water moves part of the loss from drainage to evapotranspiration, most where the water table is shallowest. The drainage share of Model A therefore leans high, and is reported here only as conditional on the datum; the split is quoted from Model B (Section 5.6). A forecast does not depend on the split: it needs the coefficients together, not the fluxes apart.

# []{#anchor}3. Site, record and fitting bases

Newborough Warren (Anglesey, Wales) is a coastal dune system of 865 ha. Its monitoring network has 88 dipwells, read at the end of each month. Monthly rainfall and Thornthwaite PET come from a single station, RAF Valley, 16 km away. Each reading is bucketed to the month it describes, and rainfall and PET enter for the same month, with no lag.

A reference network of 66 wells is admitted on record length. To be admitted, a well needs at least 100 months of record and must still be reporting at the end of the record. Admitted records are longer than this minimum, with a median of 192 months (range 140--252).

The wells fall into five clusters by the shape of their records, before any model is fitted. Each well's monthly level series is compared with every other well's by correlation, so the timing and shape of its rises and falls count and its depth below ground does not, and the wells are grouped by Ward's linkage on one minus that correlation. Three clusters are open dune: C1 Lake Edge, C2 Dune and C3 Western Residual. Two are pine forest: C4 Main Forest and C5 Coastal Forest. The silhouette score is highest at two clusters (0.58), which separates the main forest from the rest; at five it is 0.37. Assignments are stable when wells are resampled (median co-assignment 0.95) and when months are resampled in year-long blocks (0.99), but partitions built from two disjoint samples of the record agree only moderately (adjusted Rand index 0.53, 5--95 % range 0.35--0.73). The clusters are therefore a useful grouping of one continuous aquifer, not sharply bounded units (Hollingham, 2026a).

The coefficients a study reports belong to the record they were fitted on, and in a network installed progressively the record is not one thing. Two fitting bases are used. The first is the cluster centroid on the full record: one hydrograph per cluster, the mean of its members, fitted with every month available. The second is the per-well fit, either on each well's full record or on a common comparison window, the most recent 100 months at every well, so that wells are compared under the same climate. The split-sample tests fit each well on one side of January 2018 and test it on the other. A register lists, for every analysis, the wells, the record fitted and the record evaluated, and is checked automatically against the fitting call in each script before results are published; every coefficient here carries its basis in its source file.

# []{#anchor}4. Can the record forecast?

## []{#anchor}4.1 What the drainage term adds

At each reference well, three models were fitted on the comparison window: the TLM, Model A at the network datum of 3.7 m, and Model B. Each was then run freely over the same months, from the first observed level, each month computed from the model's own previous level (Table 1). The test is in-sample: it asks whether a model that has seen the months can reproduce their trajectory without being corrected by them.

**Table 1.** Free-running skill of the traditional linear model (TLM), the no-intercept state-space model at z₀ = 3.7 m (Model A) and the free-intercept form (Model B), each fitted per well on the reference well's 100-month comparison window and scored over the same months. NSE is the Nash--Sutcliffe efficiency of the simulated level; n is the number of wells.

  --------------------- ---- ------- ------- ------- ---- ---- ----
  C1 Lake Edge          7    0.308   0.745   0.878   5    7    7
  C2 Dune               18   0.391   0.766   0.848   14   18   18
  C3 Western Residual   25   0.439   0.804   0.823   24   25   25
  C4 Main Forest        9    0.541   0.662   0.697   8    8    9
  C5 Coastal Forest     5    0.655   0.830   0.809   5    5    5
  --------------------- ---- ------- ------- ------- ---- ---- ----

Run freely, the TLM drifts. Across the 64 wells its median Nash--Sutcliffe efficiency (NSE; Nash and Sutcliffe, 1970) is 0.43, and it is negative at 8 wells, where a constant at the observed mean would do better. With the drainage term alone, as in Model B, the median rises to 0.82, and the NSE is positive at all 64 wells. With the drainage term at the network datum, as in Model A, the median is 0.77, positive at 63 wells. If the models are instead corrected each month by the observed level, the TLM and Model A are indistinguishable (median R² 0.92): the observed level supplies the return the TLM lacks.

The gain rises with the drainage coefficient (Pearson r = 0.46 between Model A's per-well gain and its β₃, p \< 0.001), and is largest at the fastest-draining cluster, C1. The pine forest is the exception: at C4 drainage is slow and the TLM's accumulation of error does least harm. At one C4 well, CEH14, Model A's drainage coefficient on the window is negative and its free run diverges (NSE −12.87 against −0.04 for the TLM), while Model B, whose datum is fitted, scores 0.38. A model without drainage cannot forecast; where a fixed datum leaves the drainage term unidentified, the term can cost more than it adds.

## []{#anchor}4.2 Forecasting within the recorded climate

Each form was fitted on the record before January 2018 and run freely over the years after, each month from the model's own previous level; the test was then run in reverse. Forward, Model B's median NSE is 0.79 against 0.61 for Model A, and Model B is better at 88 % of wells. In reverse, Model B's median is 0.78 against 0.67, better at 77 % of wells. The advantage is clearest in the open dune; under the coastal forest the two forms are close.

At C4 both forecast poorly, with forward medians of 0.08 for Model B and 0.21 for Model A. The split at January 2018 falls a month after the December 2017 clearfell beside the main forest, so the forest forecasts are scored over years in which the canopy changed. The 100-month comparison window likewise begins, for most wells, in November 2017, a month before the felling.

## []{#anchor}4.3 Forecasting into a different climate

A forecast inside the modern record is dominated by the seasonal swing. A changed climate asks something else of the model: a sustained shift of the mean level. The one test of that which no fit has seen is the Countryside Council for Wales record of 1989--96, read before the modern network was installed, at 9 wells that the network still reads, in a decade drier than any the fits contain. Hindcast from fits to the full modern record of each well, Model A is close to unbiased, with a median bias of 0.03 m. Model B is too wet by 0.30 m. Their median NSE values are −0.14 and −1.46. Both are below zero: the hindcast's monthly errors are larger than the spread of the levels about their own 1989--96 mean, so a constant at that mean would score better. That mean is not something a forecast could know in advance; it is the shift the test asks the model to find. On this test bias, not NSE, is the measure that separates the forms. The ordering holds at every record length, whether the fit is taken from the start or the end of the modern record: Model B's median bias lies between 0.27 and 0.51 m, and Model A's is within 0.09 m of zero once the fit spans four years. The two tests split by what they score: a fast reversion follows the seasonal swing well, and the sustained shift is what Model A carries and Model B does not.

The same decade can be asked which datum Model A should use. Model A was refitted at each well on the comparison window at every datum of the sweep, and each fit used to hindcast 1989--96. By a rule fixed before the run, the datum that maximizes the median NSE is 2.9 m, with a band of 2.8--2.9 m within 0.05 of the best (median NSE 0.44, against −0.06 at the network datum). Deeper than the network datum every measure is worse, so the drier past does not ask for a deeper datum. The network datum lies below the supported band, but it is close to unbiased on the same fits (median bias −0.01 m). A base fixed in elevation rather than a depth below ground was tested on the same decade and is reported in Section 5.5.

A second epoch, Ranwell's readings of 1951--53 (Ranwell, 1959), tests the same question nearly forty years earlier. The readings come from three sites whose positions are approximate, so this epoch is scored on the seasonal swing with the mean offset removed. By the same rule it supports 0.7 m (band 0.5--1.1 m), and there Model A behaves as Model B does: the median NSE values are 0.86 at that datum and 0.86 for Model B, against 0.46 at the network datum of 3.7 m. The two epochs disagree because they score different things: with its mean removed, Ranwell's record tests only the seasonal swing, which a fast return to the mean follows and which Model A reproduces only with a shallow datum; the drier decade tests a sustained shift of the mean, which the plateau datum carries.

Why Ranwell's swing differs was explored after the comparison, so it describes rather than tests. The readings ask for a weaker response to rain, a stronger evaporative draw and faster drainage than today's coefficients give, and relative to the model the seasonal swing at the three main pairs was 3--20 % smaller then than it is now. Ordinary weather, carry-over from earlier years, Ranwell's own rain gauge, the depth limit of his pipes, a barer rabbit-grazed dune, the forest planted since and a slightly lower sea each fail to supply it. Drains dug for the young plantation and a lower outlet of Llyn Rhos-Ddu point the right way, but neither is recorded.

The two epochs ask for two time scales, a fast return to the mean and a slow one that holds the level through a drier decade. A single linear store has one. A second, slower store driven by the same climate was therefore fitted at every cluster centroid, including one drawn down by the plantation as its canopy closed. No version passed the tests fixed before the fit: either the information criterion preferred one store, or the slow store forecast worse beyond 2018. A head-only model at this site has one time scale, and the form chosen decides which.

## []{#anchor}4.4 How much record a forecast needs

Within the modern record, Model B forecasts better at every length of fit. Fitted on 24 months before 2018 its median forward NSE is already 0.72, and 0.79 from all of it. Model A's rises from −0.14 to 0.59 at 100 months and 0.61 on all the months before 2018. A site with a few years of record can forecast its own water table with the free-intercept form.

The coefficients need more. Each well's β₃ was refitted on every non-overlapping placement of each length, and its stable length taken as the shortest record on which the median departure from the full-record β₃ is within 20 %. Model A's β₃ is the more robust: its median stable length is 24 months, the shortest length tested and so an upper bound, reached at 64 wells. Model B's is 60 months (62 wells), and its β₃ is identified on only 60 % of 24-month placements at the median well. Measured in each well's mean-reversion times, the stable length is 4.7 for Model A and 9.0 for Model B: a record must span several mean-reversion times, and the rule binds the free-intercept form harder.

The forest is the exception for both forms. At C4 Model A needs 120 months and Model B 144, and Model B reaches stability within the lengths tested at only 5 of its wells. Fitting the comparison window instead of the full record shifts the C4 centroid's β₃ by −35 %, against +17 % or less elsewhere. Pastas tells the same story: the wells whose response time it loses on the window are mainly forest wells (9 at C4).

## []{#anchor}4.5 Per well or per cluster?

Clusters are formed from the hydrographs alone (Section 3), so a well can be placed in one by correlating its record with the cluster centroids, without fitting it. Lending it the cluster's coefficients then rests on two things: that a short record places the well correctly, and that cluster coefficients forecast as well as its own. The second is tested here: each skill test was run twice: on each well's own coefficients, and on its cluster centroid's fitted on the same span, shifted by the mean difference between the well and its centroid over the fitted months. By a rule fixed before the run, the cluster basis holds on a test if its median NSE is within 0.05 of the per-well basis or better, and, on the drier decade, its median absolute bias within 0.05 m or smaller.

With Model A, the cluster coefficients pass all three tests. On the drier decade their median NSE is −0.17 against −0.14 for the wells' own coefficients, and their median absolute bias 0.23 m against 0.26 m. Both NSE values are below zero, as in Section 4.3, so on this test the comparison rests mainly on bias. Forecasting forward from the January 2018 split, their median NSE is 0.72 against 0.61. With Model B they also pass all three, and on the drier decade they do much better than the wells' own (median NSE −0.27 against −1.46). Within the tolerances set before the run, cluster coefficients forecast and hindcast as well as each well's own.

Where a well's own record has a gap, it is better filled from a measured neighbour than from the model. With stretches of 54 months hidden in turn, each well's mean spring level was put back from its nearest cluster-mate with a median miss of 0.041 m, against 0.139 m from Model A run on the climate.

## []{#anchor}4.6 Which form to forecast with

Within the climate the record spans, Model B is the form to forecast with: it forecasts better, needs only a few years of record, and its mean-reversion time is the one the record supports (Section 5). A forward run into a different climate, whether a hindcast of a drier past or a projection, asks for a sustained shift of the mean level, and there the one independent test favours Model A. Forward runs into a changed climate therefore use Model A at the network datum, with Model B beside it as the fast-reversion bound. The two are reported as a pair on the same wells and never averaged, and the datum the drier decade supports is carried as a sensitivity. Neither form serves a quantity where its β₃ is not identified, which withholds the main forest from projection.

## []{#anchor}4.7 What the record projects

Take the UKCP18 high-emissions scenario (RCP8.5; Met Office, 2018), applied as seasonal changes to the observed rainfall and PET, with comparison-window fits at the 57 wells both forms identify. In the 2050s the median sustained fall of the summer level is 0.28 m under Model A at the network datum, 0.24 m under Model A at 2.9 m and 0.20 m under Model B. The 2050s scenario lowers the annual water balance (rainfall less PET) by 117 mm a year, about as much as the drier decade of 1989--96 fell below the modern record (110 mm a year), so this projection sits inside the range the hindcast of Section 4.3 has tested.

In the 2080s the median fall of the summer level is 0.52 m under Model A at the network datum, 0.44 m at 2.9 m and 0.37 m under Model B. The 2080s scenario lowers the annual water balance by 210 mm a year, beyond anything in the record, so this projection is an extrapolation. It is reported as the range between the two forms, not as a single figure, and the range itself is the honest statement of what a head-only model can say about a climate it has not seen.

In both periods the fall is larger in summer than over the year, and larger under Model A, whose slower recession carries the summer deficit forward. The main forest is not projected, because its drainage coefficient is not identified on the record.

# []{#anchor}5. What the coefficients mean

## []{#anchor}5.1 Two time scales from one coefficient

In both forms the drainage coefficient sets an e-folding time, 1/β₃, but the two forms measure it from different reference levels and so answer different questions. In Model A the drainage term acts on the height of the water table above the fixed datum, and its e-folding time is a recession time: how long the storage above the datum would take to fall by a factor of e if rain and evaporation stopped. In Model B the free intercept absorbs that fixed level, and the drainage term acts on the departure from the level the climate normally sustains. Its e-folding time is a mean-reversion time: how quickly a wet or dry anomaly dies away while the climate continues. The recession time depends on where the datum is set (Section 5.4); the mean-reversion time does not. Fitted per well on the full record, the median well's recession time (Model A) is 15.8 months and its mean-reversion time (Model B) 6.5.

## []{#anchor}5.2 A model-free referee

The mean-reversion time can be measured without either model. Take each month's level less the mean for its calendar month. If this is treated as a first-order autoregressive process with lag-1 autocorrelation ρ₁, anomalies decay with the e-folding time −1/ln ρ₁ (Delworth and Manabe, 1988), as level autocorrelation is used to characterize groundwater drought persistence (Bloomfield and Marchant, 2013). The model-free median is 5.1 months.

Cluster by cluster, Model B sits with it: 2.1 against 2.0 months at C1, 4.4 against 4.1 at C2, 7.4 against 6.3 at C3 and 13.3 against 12.0 at C5. Model A's median is about three times the observed value. At C4, where the observed time is 15.6 months, Model B's β₃ is not identified on the record (Section 4.4). Removing a linear trend gives a median of 5.0 months, and correcting ρ₁ for reading error 6.1; with either correction Model B remains the nearer form at every cluster where it is identified.

## []{#anchor}5.3 Year-to-year persistence

A short mean-reversion time predicts that spring levels in successive years are close to independent. The drainage term implies an expected lag-1 autocorrelation of spring level of (1 − β₃)¹², which is 0.16 at the median well under Model B and 0.47 under Model A. The observed value is −0.11. Taken at face value, Model A would make a five-year mean of spring levels a poorly averaged quantity; the record does not support that.

## []{#anchor}5.4 What the datum decides in Model A

The cluster-centroid Model A was refitted at every datum from 0.5 to 8.0 m below ground (Figure 1). Shallower than 1.6 m, at least one cluster's β₃ is non-positive or not significant: the datum lies within the range the water table occupies and the drainage term is not identified. The datum that fits best differs by cluster (0.7--7.1 m by AIC; Akaike, 1974) and agrees at every cluster, within one sweep step, with Model B's zero-drainage level. The best-fitting Model A is Model B, so a datum chosen on fit alone measures mean reversion, not drainage.

Deeper than the floor, β₃ keeps falling but the mean drainage flux does not. At 3.7 m the flux is 0.81--0.97 of its value at the deepest datum swept, and Model A's drainage share of the mean loss is within five points of its deep value at every cluster. On this plateau the coefficients' ranking and the water balance are insensitive to the datum, but t½ continues to scale with it and must be reported as conditional on it. A single network datum, 3.7 m, lies on the plateau for the deepest cluster and below the fluctuation range everywhere. Against each cluster's own optimum it costs 94.0 AIC units at C1, where the water table is shallowest, and almost nothing under the forest.

## []{#anchor}5.5 A physically anchored datum

Is the drainage base a fixed height or a depth below ground? A common datum in elevation, fitted at every well, fits slightly worse than the depth datum at every level tried (best median R² 0.738 against 0.740), and higher levels leave the drainage term unidentified at many wells. At a coastal site the most defensible physical datum is the level to which the aquifer ultimately drains. Each well was therefore fitted on its full record with its own datum at its depth to mean high water (1.88 m above Ordnance Datum), which places the datums between 1.7 and 12.5 m below ground.

The anchored datum reproduces Model A's water-balance partition at the network datum (median drainage share 68 % at the anchored datum against 68 % at the network datum, both Model A), because nearly every well's depth to mean high water lies on the plateau. It is nonetheless the worse forecaster. The deeper datum passes into β₃ and the implied e-folding time roughly doubles, to 29 months against 16 at 3.7 m and 5.1 observed. Out-of-sample NSE falls to 0.46 forward and 0.53 in reverse, against 0.61 and 0.67. A physical datum answers the objection that a single depth is arbitrary, because the partition is the same; it is not adopted, because the dynamics are worse.

A single base in elevation was also tested as a forecaster. Model A was refitted at each well with its datum at the well's height above one common base, between −2 and 8 m above Ordnance Datum, and run forward as in Section 4.3. By the rule fixed before the run, the best base is 2.75 m, just above mean high water. Against the network datum on the same wells, it hindcasts the drier decade better (both Model A: median NSE 0.25 against −0.06) and Ranwell's swing better (0.58 against 0.46, 3 pairings), but forecasts the modern record worse (median split-sample NSE 0.56 against 0.64), and one more well loses its drainage term. It is not adopted. The medians hide a split by cluster. 5 of the 6 drier-decade wells in the Western Residual hindcast better on the common base (median NSE 0.42 against −0.24), while the 2 open-dune wells fail (median NSE −3.37 against 0.28 at the network datum). Under one base, β₃ falls with each well's height above it (Spearman ρ −0.74), so the e-folding time is short near the coast and long inland. A drainage path to a coastal base would predict that pattern, but the no-intercept form produces it mechanically too, so the fit cannot tell the two apart. A base per cluster does no better. Chosen for each cluster from the modern record alone and then tested on the two earlier epochs, it beats the network datum only at the Lake Edge, and fails in the open dune, the Western Residual and the coastal forest. The level the aquifer drains to varies within clusters as well as between them, which is why a datum that follows the ground serves every cluster.

## []{#anchor}5.6 Why Model B does not set the datum

Model B pays for its fit. Its intercept and β₃ are almost interchangeable: their estimates correlate at 0.96 at the median well. The level its drainage refers to is therefore fitted rather than physical, and lies near each well's mean, a median 1.6 m below ground, at the identification floor. With it, more of the mean loss is booked to atmospheric draw: a drainage share of 45 % against Model A's 68 %. That is the split this paper quotes: it follows from β₁ and β₂, which Model B identifies and Pastas reproduces, and an intercept that absorbs the datum leaves it the same at every datum. Adopting Model B's base as the datum would make Model A identical to Model B.

Pastas, fitted to the same wells on the full record, agrees with Model B well by well (Figure 2): Spearman ρ is 1.00 for β₁, 0.96 for β₂ and 0.98 for β₃, on the 63 wells whose response time Pastas identifies. By Section 2.3 that agreement is expected; it checks the implementation rather than the form.

# []{#anchor}6. A procedure for managers

The procedure below is for a manager with a monthly water-level record and no measured fluxes, who wants to know what the record can forecast and what its coefficients mean.

1.  **Fit both forms**, with and without an intercept, at the scale at which results will be used: each well, or each group of wells that rise and fall together. For the no-intercept form, sweep the datum and choose one on the plateau where the mean drainage flux stops changing, below the range the water table occupies.
2.  **Test what the drainage term adds**. Run each form freely from the first observed level and compare it with the same model without drainage. A model that drifts without its drainage term cannot forecast.
3.  **Test forecasts within the record**. Fit on one part of the record and run freely over the other, in both directions. Use the form that wins here, at Newborough the free-intercept form, to forecast within the climate the record spans.
4.  **Test against a different climate** wherever an older record exists, even a few wells or a few years. A sustained shift of the mean level is the nearest test of a changed future. Use the form it supports for projections, with the other beside it, and report the pair, not an average.
5.  **Check the record is long enough**. Refit on shorter stretches and see when the drainage coefficient stops moving. The record should span several mean-reversion times; slow forest wells need much longer.
6.  **Referee the time scale without a model**. Compare each form's e-folding time with the lag-1 autocorrelation of the deseasonalized level, and report the mean-reversion time as how quickly the water table recovers, not the recession half-life, which depends on the datum.
7.  **Treat the coefficients as coefficients, not fluxes**. The split of the loss between drainage and evaporation depends on the datum and leans towards drainage where the water table is shallow; report it as conditional, or not at all.
8.  **Declare the fitting basis** of every result, and fill gaps in a well's record from measured neighbours rather than from the model.

Table 2 sets out what the procedure gives at Newborough, with each quantity under the form that identifies it.

**Table 2.** The procedure applied at Newborough, per cluster, each quantity under the form that identifies it. Coefficients and closure residual (Residual): the no-intercept form (Model A) fitted to each cluster centroid at z₀ = 3.7 m; the residual of the mean water balance is in units of water-table change. Drainage share: the free-intercept form (Model B) at each cluster centroid, the split this paper quotes (Section 5.6); Model A's share at the network datum is in Section 5.4. τ_B, mean-reversion time: median over the cluster's wells of the free-intercept form's e-folding time; τ_obs, the model-free estimate from the level's lag-1 autocorrelation (Section 5.2); n.i., not identified on the record. L_A and L_B, record for a stable β₃ in each form: median, over the wells that reach it within the lengths tested, of the shortest record on which the median departure from the full-record β₃ is within 20 % (Section 4.4); a value equal to the shortest length tested is an upper bound.

  --------------------- ------- ------- ------- ---- ------ ------------- -----------
  C1 Lake Edge          4.577   0.942   0.088   38   −4.2   2.1 / 2.0     24 / 60
  C2 Dune               3.989   1.842   0.062   45   −2.7   4.4 / 4.1     24 / 36
  C3 Western Residual   3.808   1.833   0.062   56   0.3    7.4 / 6.3     24 / 80
  C4 Main Forest        2.502   2.564   0.019   29   0.2    n.i.          120 / 144
  C5 Coastal Forest     2.462   1.336   0.045   61   −3.2   13.3 / 12.0   36 / 100
  --------------------- ------- ------- ------- ---- ------ ------------- -----------

# []{#anchor}7. Discussion

## []{#anchor}7.1 What heads alone can and cannot give

A head-only model can always close the mean balance, because the water level records the net of what enters and leaves. What it can be trusted to forecast depends on the test it has passed. Within the recorded climate, the split-sample test and a model-free time scale agree on the free-intercept form. Beyond it, only an independent epoch can say, and here it says something different: the drier decade is reproduced by the slower no-intercept form, and a second store driven by the same climate does not reconcile the two. A manager forecasting next year's spring level and one projecting the 2080s should not use the same form, and should know why.

What heads alone cannot give is the split of the loss between evapotranspiration and drainage. Model A answers by an assumption about where drainage is measured from, and Model B by a fitted equilibrium level, and the two answers differ (68 against 45 % drainage at the median well). Only an independent flux measurement, from tracers, outflow gauging or eddy covariance, can close that question. The literature also calls both readings of β₃ a memory: the time a groundwater system takes to re-equilibrate with a change in recharge (Cuthbert et al., 2019), and the persistence of level anomalies (Nygren et al., 2022). Neither is a memory, and here the two differ more than twofold. Reading persistence through the recession constant overstates it by a factor that grows with the datum.

## []{#anchor}7.2 The regime boundary as a site property

The identification floor sits near the shallow end of the water table's range, and Model B's zero-drainage level sits on it. Both are properties of this aquifer's water-table depths, not general constants, and so is the plateau, whose onset at each cluster follows that cluster's mean depth to water. At another site the sweep must be repeated, not the numbers reused, and the same holds for the record length each form needs.

## []{#anchor}7.3 Relation to transfer-function practice

Free-base transfer-function models, of which Pastas is the reference implementation, estimate the mean-reversion form. That is the right form for forecasting within the recorded climate, and its agreement here with the model-free estimate and the split-sample test supports its use. Its agreement with Pastas is an identity check, not independent evidence. What transfer-function practice does not do is test a forecast against a different climate, and at this site that test reverses the ranking. The two practices are complementary: the free-base model serves the dynamics within the record, and the fixed-datum model on the plateau, tested against an independent epoch, serves the sustained response.

## []{#anchor}7.4 Limits

The forcing comes from one climate station outside the site, at monthly resolution. Thornthwaite PET is an index of demand rather than a measured flux, so β₂ is an effective coefficient, and β₃ under Model A includes evaporation from the water table as well as drainage. The model is linear and time-invariant; changes in land cover over the record are handled elsewhere, by before--after designs. The projections scale the observed climate by seasonal factors and assume the coefficients hold under a climate the record has not seen, which the hindcasts test only to the 2050s.

The forest cluster's free-intercept drainage coefficient is not identified on the record, which withholds it from forecasting and projection. A slow response is one reading of that, and a forcing that misrepresents the forest's evapotranspiration is another, and the record does not resolve between them. The independent tests of the sustained response rest on 9 wells in one decade, and on three approximately placed sites in another, and why the earlier epoch's swing differs is not resolved.

# []{#anchor}8. Conclusions

A head-only model fitted to a monthly water-level record can forecast that record's water table, but which form can be trusted depends on what is being forecast. Within the climate the record spans, the free-intercept form forecasts better, needs only a few years of record, and measures the time the water table takes to return to its mean, which a model-free estimate confirms. Against a drier decade that no fit had seen, the no-intercept form at a datum on the flux plateau reproduces the sustained shift of the level, and the free-intercept form does not.

Projections into a changed climate should therefore use the form an independent epoch supports, with the other beside it, and report the pair. At Newborough, under a high-emissions climate, the two forms put the median fall of the summer level at 0.20--0.28 m in the 2050s, within the range the hindcast has tested, and 0.37--0.52 m in the 2080s, beyond it. The main forest is withheld, because its drainage coefficient is not identified on the record.

The coefficients themselves are not fluxes. The split of the loss between drainage and evapotranspiration is conditional on the datum and leans towards drainage where the water table is shallow, and the recession half-life describes the datum as much as the aquifer. Each quantity should be taken from the form that identifies it, with the fitting basis declared and the tests repeated at every site.

# []{#anchor}Data availability

The monitoring record, the analysis pipeline and every committed output from which the numbers in this paper are set are available in the project repository (https://github.com/newbroman/Newborough_Hydrology). Each number quoted in the text is read from a named committed output file.

# []{#anchor}Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work the author used Anthropic's Claude (successive Claude Opus and Claude Fable models, accessed through the Claude desktop application) for substantial drafting and editing of the manuscript text: composing prose from the author's analytical outputs and decisions, structuring and restructuring sections, and correcting the text against the study's committed analytical outputs. The conception and design of the study, the twenty-one-year manual dipwell record on which it rests, the analytical decisions, and the interpretation of the results are the author's own. Numerical values in the manuscript are set from the committed outputs of the analysis pipeline, and a decision log records the methodological and editorial calls made by the author during the work. After using this tool the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

# []{#anchor}Figures

![](Pictures/0.png){width="468pt" height="386.64pt"}

Figure 1. Datum sweep of the cluster-centroid no-intercept model. Top: the fitted mean drainage flux β₃·(z₀ + mean h) against the datum depth z₀; bottom: the drainage share of the modelled mean loss. Shaded: the range shallower than the identification floor, where at least one cluster's β₃ is non-positive or not significant. Dotted: the network datum.

![](Pictures/1.png){width="311.11pt" height="560pt"}

Figure 2. Per-well coefficients of Pastas's exponential-response model against the state-space model on the full record: Model B filled, Model A hollow; crosses mark wells whose response time Pastas does not identify. Dashed: 1:1.

# []{#anchor}References

Akaike, H. (1974) A new look at the statistical model identification. *IEEE Transactions on Automatic Control* 19(6), 716--723. doi:10.1109/TAC.1974.1100705

Bakker, M. and Schaars, F. (2019) Solving groundwater flow problems with time series analysis: you may not even need another model. *Groundwater* 57(6), 826--833. doi:10.1111/gwat.12927

Bloomfield, J.P. and Marchant, B.P. (2013) Analysis of groundwater drought building on the standardised precipitation index approach. *Hydrology and Earth System Sciences* 17(12), 4769--4787. doi:10.5194/hess-17-4769-2013

Collenteur, R.A., Bakker, M., Caljé, R., Klop, S.A. and Schaars, F. (2019) Pastas: open source software for the analysis of groundwater time series. *Groundwater* 57(6), 877--885. doi:10.1111/gwat.12925

Cuthbert, M.O., Gleeson, T., Moosdorf, N., Befus, K.M., Schneider, A., Hartmann, J. and Lehner, B. (2019) Global patterns and dynamics of climate--groundwater interactions. *Nature Climate Change* 9(2), 137--141. doi:10.1038/s41558-018-0386-4

Delworth, T.L. and Manabe, S. (1988) The influence of potential evaporation on the variabilities of simulated soil wetness and climate. *Journal of Climate* 1(5), 523--547. doi:10.1175/1520-0442(1988)001\<0523:TIOPEO\>2.0.CO;2

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
