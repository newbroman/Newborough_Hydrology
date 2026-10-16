<!-- GENERATED MIRROR of docs/papers/paper_M/PaperM_v1_20.odt — do not edit. source-sha256=0d6b2b28e928e603 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you

M. Hollingham

Draft --- 2026

# []{#anchor}Abstract

Monthly water-level records from shallow dipwells are common; measurements of the fluxes that drive them are not. Simple reservoir models fitted to such records are widely used to infer the water balance, but three choices that decide what their coefficients mean are seldom stated: whether the model has an intercept, how deep the drainage base is placed, and which part of the record is fitted. We test all three on 66 wells in a coastal dune aquifer at Newborough Warren, Wales. Without an intercept, the drainage coefficient depends on the assumed base. Once the base lies below an identification floor, the drainage flux and the split of the water budget between drainage and evapotranspiration stop changing with it, but the recession constant does not. With an intercept, the same model measures how quickly the water table returns to its own mean. The two readings differ more than twofold: e-folding times of 15.8 and 6.5 months at the median well. A model-free estimate (5.1 months) and a split-sample test favour the second for the dynamics; an independent, drier decade before the network favours the first for the level. At Newborough, with the drainage base on the plateau, drainage carries 24--89 % of the mean loss across the five units (under a fitted base, 29--60 %), and away from the main forest the water table returns to its mean within 2.1--13.3 months. The no-intercept coefficient is stable on 24 months of record at the median well; the free-intercept one needs 60, and under pine forest both need far more. We give a procedure that assigns each reported quantity to the form that identifies it.

**Keywords:** groundwater time series; linear reservoir; drainage datum; mean-reversion time; dune slack; model identification

# []{#anchor}Plain-language summary

Many wetlands depend on groundwater, such as the damp hollows (dune slacks) among sand dunes. They are usually monitored by measuring the water level in shallow pipes about once a month. What is almost never measured is where the water comes from and where it goes: how much rain soaks in, how much is drawn back up by plants and the sun, and how much drains away underground. Scientists therefore try to work these out from the water levels alone, by fitting a simple mathematical model to the record.

This paper shows that three choices made when fitting such a model, usually without comment, change what its answers mean: whether the model includes a constant term, how deep the notional floor is that the water is assumed to drain towards, and which part of the record is used. All three are tested on 66 monitoring wells at Newborough Warren, a coastal dune system on Anglesey in Wales.

The key finding is that the model's drainage number can be read in two different ways. Without the constant, it describes drainage towards the chosen floor, and its value depends strongly on where that floor is placed; once the floor is deep enough, however, the split of the water budget between drainage and evaporation stops changing. With the constant, the floor is in effect worked out from the data, and the number describes how quickly the water table returns to its normal level after a wet or dry spell.

The two readings differ by more than a factor of two. At a typical well, the first says that a disturbance takes about 16 months to shrink to about a third of its size, and the second about 6.5 months. Two checks favour the second for how the water table behaves over time: a method that uses no model at all gives 5.1 months, and the second reading also does better on data held back from the fit. An independent record from an earlier, drier decade, made before the present wells were installed, points the other way and favours the first reading for the level itself.

The two readings also need different amounts of data. At a typical well the first is stable on 24 months of readings and the second needs 60, while under pine forest both need much longer. The paper ends with a step-by-step procedure that tells users which version of the model to trust for each quantity they want to report.

# []{#anchor}1. Introduction

Shallow groundwater governs the condition of dune slacks, fens, wet heaths and other groundwater-dependent wetlands. In most places, the record on which their management rests is a network of dipwells read by hand about once a month. Recharge, drainage and evapotranspiration are rarely measured at such sites. What is known about the water balance is therefore inferred from the levels themselves. This is done by fitting a model that turns rainfall and evaporative demand into a water-level response.

Two families of head-only model are in common use. Transfer-function-noise models represent the level as the convolution of each driver with an impulse response. The simplest such response is the exponential response of a single linear reservoir (von Asmuth et al., 2002; Knotters and Bierkens, 2000). These models are implemented in open software, notably Pastas (Collenteur et al., 2019) and HydroSight (Peterson and Western, 2014). They have been applied to shallow unconfined aquifers in a range of settings (Obergfell et al., 2019; Bakker and Schaars, 2019). State-space or difference-equation forms write the same reservoir directly as a monthly balance. In that balance, the change in level is driven by rainfall, by evaporative demand, and by a drainage loss proportional to the head above a base (Knotters and van Walsum, 1997; Peters et al., 2003). The two families are closely related. Both return a small number of coefficients that are read physically: a recharge sensitivity, an evaporative coefficient and a drainage rate or response time.

The drainage coefficient is read in two incompatible ways. In the first, it is a linearized Darcy coefficient: the fraction of the stored head above the drainage base that leaves each month. A drainage flux follows from it, and so does a partition of the mean loss between drainage and evapotranspiration. In the second, it is a response time or "memory": how long a departure of the water table from its usual level persists. Both readings appear in applied studies, often of the same coefficient. The quantities derived from the coefficient, such as half-lives, persistence of anomalies and sustained responses to a change in climate, inherit whichever reading was intended. Which reading a given fit actually supports depends on choices that are seldom reported: whether an intercept is fitted, where the drainage base is placed, and which months enter the fit.

This paper makes those choices explicit and shows what each decides. It uses a long monthly record from a coastal dune aquifer. There the drainage base is physically uncertain, the water table lies within a few metres of the surface, and the network spans open dune and pine plantation with very different response speeds. The paper makes five contributions.

First, the no-intercept and free-intercept forms are one model family, separated only by the datum. The free-intercept form is the no-intercept form at a fitted datum, and it is term for term the exponential-response model of Pastas. Without the drainage term it reduces to a linear transfer of climate, whose free run drifts (Sections 2 and 5.4).

Second, without an intercept the datum is not inert. A datum sweep exposes a regime boundary. Below it, the drainage reading holds and the water balance becomes insensitive to the datum, while the recession constant does not (Section 4).

Third, a physically anchored datum reproduces that water balance but degrades the model's dynamics (Section 4.7).

Fourth, the free-intercept form measures the mean-reversion time. A model-free autocorrelation estimate and an out-of-sample test both support it. Each form should therefore be used for the quantity it identifies (Section 5).

Fifth, the record decides how far either reading can be trusted. The two forms need different lengths of record. An independent epoch drier than the fitted record separates them where fit within the record cannot (Section 6).

Section 7 sets these out as a procedure that any site with a monthly head record can follow.

# []{#anchor}2. The model family

## []{#anchor}2.1 The displacement form

The model predicts how much the water level changes in a month. Three things drive the change: rain adds water, evaporation removes it, and drainage removes it at a rate that grows with how high the water table stands. For month *t*,

Δh(t) = β₁·P(t) − β₂·PET(t) − β₃·h_disp(t−1), with h_disp(t−1) = z₀ + h(t−1).

Here *h* is the water level, measured from the ground surface and negative below it. P is the month's rainfall and PET its potential evapotranspiration. The coefficients β₁, β₂ and β₃ are fitted to the record.

The drainage term needs a reference level, the drainage datum, at depth z₀ below ground. h_disp is the height of the water table above that datum. Written this way, β₃ is positive wherever the water table lies above the datum, and drainage is proportional to head above a base. This is the linearized Darcy flux of a shallow unconfined aquifer draining to a boundary (Knotters and van Walsum, 1997). The term uses the level at the start of the month, h(t−1), so that the month's change is not regressed on its own end-point.

The datum matters. Measured from the ground surface instead (z₀ = 0), 2 of the five clusters at this site return a negative β₃, which would mean drainage grows as the water table falls. Depth below ground on its own therefore does not represent the gradient that drives drainage.

## []{#anchor}2.2 Model A and Model B

Model A is the equation above, fitted by ordinary least squares with no constant term (no intercept). Model B adds a constant, α_B:

Δh(t) = α_B + β₁·P(t) − β₂·PET(t) − β₃·(z₀ + h(t−1)).

The constant can be folded into the drainage term. Because −β₃·z₀ is also a constant, Model B is Model A with the datum moved to

z_B = z₀ − α_B/β₃,

the level at which the fitted drainage is zero. The two forms are therefore one family, and they differ only in where the datum comes from: Model A fixes it in advance, Model B fits it. Two consequences follow, and the rest of the paper is organized around them.

First, in Model A the choice of datum changes the coefficients. There is no constant to absorb a change in z₀, so moving the datum shifts β₁, β₂ and β₃ together. The mean drainage loss, β₃ times the mean height above the datum, must still balance the mean water budget. So as the datum is set deeper, β₃ falls, roughly as 1/(z₀ + mean h) once the flux has settled (Section 4.4), and the recession half-life t½ = ln 2/β₃ rises. t½ describes the chosen datum as much as the aquifer.

Second, in Model B the datum drops out. β₃ is then the fraction of a departure from the water table's own equilibrium level that is recovered each month. Under steady weather a departure shrinks by a factor (1 − β₃) each month, so its e-folding time, the time it takes to fall to 1/e of its size, is −1/ln(1 − β₃). This is the mean-reversion time. This is a property of the record, not of any reference level.

## []{#anchor}2.3 Relation to Pastas

Pastas (Collenteur et al., 2019) is widely used software for the same task. It models the level as a base level plus the response to a recharge series. In its linear setting, recharge is rainfall plus a (negative) fraction of PET, and the response to recharge builds up exponentially:

R(t) = P(t) + *f*·PET(t), θ(t) = *A*·(1 − exp(−t/*a*)),

where *A* is the long-run gain, *a* the response time, *f* the evaporation factor and *d* the base level. If recharge is steady within each month, one monthly step of this response is exactly

h(t) − *d* = exp(−1/*a*)·(h(t−1) − *d*) + *A*·(1 − exp(−1/*a*))·R(t).

This is Model B, with the parameters related by

β₃ = 1 − exp(−1/*a*), β₁ = *A*·β₃, β₂ = −*f*·*A*·β₃, *d* = −(z₀ − α_B/β₃),

so Pastas's base level is Model B's zero-drainage level. Pastas works in days; its parameters were converted to months with the mean month length, and the conversion was checked by fitting Pastas to synthetic wells generated from the cluster coefficients.

Model A has no Pastas equivalent, because Pastas has neither a fixed datum nor a separate drainage term. Agreement between Pastas and Model B therefore checks the code. It is not independent evidence for either form (Section 5.6).

## []{#anchor}2.4 What neither form can decide

The water table loses water in two ways: by drainage, and by atmospheric draw (evapotranspiration). Heads alone cannot say how the loss splits between them, because the split depends on the level drainage is measured from. Model A sets that level by assumption and Model B by fit. Without an independent measurement of at least one flux (drainage, evapotranspiration or recharge), neither form can fix the true split. The split is therefore reported here as conditional on the datum, with the range of datums over which it holds (Section 4).

## []{#anchor}2.5 The family without drainage

Setting β₃ = 0 in Model B removes drainage:

Δh(t) = α₀ + β₁·P(t) − β₂·PET(t).

This is the traditional linear model (TLM), the usual first model of how a water table responds to climate. Rain and evaporative demand change the level, and nothing depends on the level itself. Run forward from a starting level, the TLM has nothing pulling the level back towards a mean, so each month's error is carried into every later month. The drainage term provides that pull.

The TLM sits inside Model B and differs from it by the drainage term alone. It differs from Model A in two ways: Model A adds the drainage term, and it replaces the TLM's free constant with −β₃·z₀, which is set by the datum and tied to the drainage rate (Section 2.2).

# []{#anchor}3. Site, record and the fitting bases

Newborough Warren (Anglesey, Wales) is a coastal dune system of 865 ha. Its monitoring network has 88 dipwells, read at the end of each month. Monthly rainfall and Thornthwaite PET come from a single station, RAF Valley, 16 km away.

A reference network of 66 wells is admitted on record length. To be admitted, a well needs at least 100 months of record and must still be reporting at the end of the record. Admitted records are longer than this minimum, with a median of 192 months (range 140--252).

The wells fall into five hydrogeological clusters by the shape of their records: Ward's linkage on one minus the correlation between their monthly level series, before any model is fitted. Three are open dune: C1 Lake Edge, C2 Dune and C3 Western Residual. Two are pine forest: C4 Main Forest and C5 Coastal Forest.

The clusters are formed before any model is fitted. Each reference well's monthly level series is compared with every other well's by correlation, so the timing and shape of its rises and falls count and its depth below ground does not. The wells are grouped by Ward's linkage on one minus that correlation, and five clusters are kept.

The silhouette score is highest at two clusters (0.58), which separates the main forest from the rest; at five it is 0.37. A well's assignment is stable when wells are resampled (median co-assignment 0.95) and when months are resampled in year-long blocks (0.99). Partitions built from two disjoint samples of the record agree only moderately, however: the adjusted Rand index is 0.53, with a 5--95 % range of 0.35--0.73. In every month-resampled replicate at least two clusters merge.

The clusters are therefore a useful grouping of one continuous aquifer, not sharply bounded units (Hollingham, 2026a). The coefficients are fitted afterwards, both to each well and to each cluster centroid, the mean hydrograph of the cluster's members.

Each reading is bucketed to the month it describes. Rainfall and PET enter for the same month, with no lag.

Two fitting bases are used. Every analysis declares which one it uses, in a register that is checked automatically against each script's fitting call. The first basis is the cluster centroid on the full record: one hydrograph per cluster, the mean of its members, fitted with every month available. The second is the per-well fit on a common comparison window, the most recent 100 months at every well, so that wells are compared under the same climate.

Section 4 uses the first basis. Sections 4.7 and 5, and the common-elevation test of Section 4.6, fit each well on its own full record. The first test of Section 4.6 uses the per-well comparison-window fits. The split-sample tests fit each well on one side of January 2018 and test it on the other. Section 6 shows why the distinction matters for the drainage coefficient, and what the length of the record decides.

# []{#anchor}4. What the datum decides (Model A)

## []{#anchor}4.1 The sweep

The cluster-centroid Model A was refitted at every datum from 0.5 to 8.0 m below ground, in 0.1 m steps. At each datum we recorded β₃, its significance, R², AIC (Akaike, 1974) and the mean drainage flux β₃·mean(h_disp) (Figure 1).

## []{#anchor}4.2 An identification floor

The sweep shows a floor at 1.6 m. Shallower than this, at least one cluster's β₃ is non-positive or not significant. From this depth down, every cluster's β₃ is positive and significant (p \< 0.05) at every deeper datum. Shallower than the floor, the datum lies within the range the water table occupies, and the drainage term is not identified.

## []{#anchor}4.3 What fit prefers, and why it is not the datum

The datum that minimizes AIC differs by cluster: 0.7, 1.2, 2.2, 6.0 and 3.7 m for C1--C5.

Model B's zero-drainage level, z₀ − α_B/β₃, at the same centroids is 0.69, 1.18, 2.16, 6.00 and 3.66 m. At every cluster the two agree within one sweep step.

This is the algebra of Section 2.2 made visible: the best-fitting Model A is Model B. A datum chosen on fit alone therefore measures mean reversion, not drainage.

## []{#anchor}4.4 A flux plateau

Deeper than the floor, β₃ keeps falling but the mean drainage flux does not.

At 3.7 m the flux is 0.97, 0.96, 0.93, 0.82 and 0.89 of its value at the deepest datum swept (C1--C5). It stays within 80 % of that value at every datum deeper than a depth that ranges from 1.7 m (C1) to 3.6 m (C4).

On the plateau the drainage share of the mean loss settles too. Taken at the floor, at 3.7 m and at 8 m, it runs 73, 86 and 89 % at C1; 57, 69 and 72 % at C2; 47, 65 and 69 % at C3; 26, 63 and 68 % at C5; and 4, 24 and 28 % at C4.

Two regimes therefore exist. Near the water table, the partition swings with the datum and β₃ behaves as a reversion rate. On the plateau, the partition and the flux are insensitive to the datum, and β₃ reads as a Darcy discharge coefficient. t½, however, continues to scale with the datum there, and must be reported as conditional on it.

## []{#anchor}4.5 The cost of one datum

A single network datum, z₀ = 3.7 m, is chosen. It lies on the plateau for the deepest cluster and below the fluctuation range everywhere.

Against each cluster's own optimum, this datum costs 92.8, 28.5, 8.0, 0.4 and 0.0 AIC units for C1--C5. R² is lower by at most 0.086 (C1). The cost is largest where the water table is shallowest, and it vanishes under the forest.

The ranking of clusters by β₃ is the same at every swept datum from 0.5 m. The ranking by mean flux is the same from 1.2 m.

## []{#anchor}4.6 Elevation or depth

Is the drainage base a fixed height, or a depth below ground? Two tests address the question.

The first test expresses each well's fit-optimal datum as an elevation and regresses it on the well's ground elevation. A fixed base predicts a slope of 0; a base that follows the surface predicts a slope of 1. Across the 66 reference wells, which span 10.9 m of ground elevation, the slope is 0.84 (R² 0.79). This test is partly circular. A fit-optimal datum tracks the well's mean depth to water (r = 0.59; Section 4.3), and the water table itself follows the ground. The slope therefore describes how the base follows the ground, rather than locating it.

The second test fitted a common datum in elevation at every well on its full record (79 wells, reference and extended). The datum was set at every level from −2 to 8 m above Ordnance Datum, in 0.25 m steps. Its best median R² is 0.736, at 2.5 m. On the same wells, a depth datum of 3.7 m below ground gives 0.739. The elevation datum fits worse than the depth datum at every level tried, but only marginally.

Higher levels also leave the drainage term unidentified at many wells. At 6 m above Ordnance Datum, β₃ is non-positive at 18 wells, against 1 at the depth datum.

On fit, therefore, the two frames are indistinguishable. Depth below ground is preferred because it keeps the drainage term identified. It is also consistent with a base that follows the topography, with each slack draining locally.

## []{#anchor}4.7 A physically anchored datum

At a coastal site, the most defensible physical datum is the level to which the aquifer ultimately drains. Mean high water is a single elevation. This datum is therefore one point of the elevation sweep of Section 4.6, expressed as a depth at each well.

Each well was fitted on its full record with its own datum, set at its depth to mean high water (1.88 m above Ordnance Datum). This places the datums between 1.7 and 12.5 m below ground (median 6.7 m).

The anchored datum reproduces the water-balance partition of the single 3.7 m datum. The median drainage share is 68 % against 68 %. The 10th--90th percentile spread across wells is almost unchanged (43--78 % against 39--79 %). This is because nearly every well's depth to mean high water lies on the plateau.

It is nonetheless the worse model. The deeper datum passes into β₃, and the implied e-folding time roughly doubles: 29 months, against 16 at 3.7 m and 5.1 observed. Out-of-sample efficiency falls (Section 5.5), to 0.46 forward and 0.53 in reverse, against 0.61 and 0.67. The anchored datum forecasts better at only 17 % of wells.

A datum chosen on physical grounds thus answers the objection that a single depth is arbitrary, because the partition is the same. It is not the one adopted, because the dynamics are worse.

# []{#anchor}5. What the intercept decides, and what the drainage term adds

## []{#anchor-1}5.1 Two quantities with one name

Model A's β₃ gives the recession of storage above the datum. Model B's gives the mean-reversion time. The two differ more than twofold. Fitted per well on the full record, the e-folding time at the median well is 15.8 months under Model A and 6.5 under Model B.

## []{#anchor-1}5.2 A model-free referee

The mean-reversion time can be measured without either model. Take each month's level less the mean for its calendar month. If this is treated as a first-order autoregressive process with lag-1 autocorrelation ρ₁, anomalies decay with the e-folding time −1/ln ρ₁ (Delworth and Manabe, 1988). Level autocorrelation is used in the same way to characterize groundwater drought persistence (Bloomfield and Marchant, 2013). The median is 5.1 months.

Cluster by cluster, Model B sits with it: 2.1 against 2.0 months at C1, 4.4 against 4.1 at C2, 7.4 against 6.3 at C3 and 13.3 against 12.0 at C5. Model A's median is about three times the observed value. At C4, Model B's β₃ is not identified on the record (Section 6.3).

The estimate is exposed to two biases in opposite directions. A trend in a well's record lengthens it, and reading error shortens it. Removing a linear trend gives a median of 5.0 months. Correcting ρ₁ for reading error with ρ₂/ρ₁ gives 6.1. With either correction, or both, Model B remains the nearer form at every cluster where it is identified. The largest change is at C5, where removing the trend gives 10.4 months against the 12.0 above. Anomalies above and below the calendar-month mean return at the same rate: at no well does the difference reach significance.

## []{#anchor-1}5.3 Year-to-year persistence

A short mean-reversion time predicts that spring levels in successive years are close to independent. The drainage term implies an expected lag-1 autocorrelation of spring level, which is the lag-12 autocorrelation of the monthly recurrence, (1 − β₃)¹². With each form fitted on the well's full record, this is 0.16 at the median well under Model B and 0.47 under Model A. The observed lag-1 autocorrelation of spring levels is −0.11. Taken at face value, Model A's expectation would make a five-year mean of spring levels a poorly averaged quantity. The record does not support that.

## []{#anchor-1}5.4 What the drainage term adds

At each reference well, three models were fitted on the comparison window, the most recent 100 months: the TLM, Model A at the network datum of 3.7 m, and Model B. Each was then run freely over the same months. The run starts from the first observed level, and each month is computed from the model's own previous level. Skill is the Nash--Sutcliffe efficiency of the simulated level (Table 1).

The test is in-sample. It asks whether a model that has seen the months can reproduce their trajectory without being corrected by them. A forecast (Section 5.5) has not seen the months it is scored on. Two comparisons follow from Section 2.5. The TLM against Model B isolates the drainage term, since the TLM is Model B with β₃ = 0. The TLM against Model A adds the drainage term and, with it, replaces the free constant by the datum-fixed −β₃·z₀.

If the models are instead corrected each month by the observed level, the TLM and Model A are indistinguishable, with a median R² of 0.92 for both. The observed level supplies the return the TLM lacks.

**Table 1.** Free-running skill of the traditional linear model (TLM), the no-intercept state-space model at z₀ = 3.7 m (Model A) and the free-intercept form (Model B), each fitted per well on the reference well's 100-month comparison window and scored over the same months. NSE is the Nash--Sutcliffe efficiency of the simulated level; n is the number of wells.

  --------------------- ---- ------- ------- ------- ---- ---- ----
  C1 Lake Edge          7    0.308   0.745   0.878   5    7    7
  C2 Dune               19   0.389   0.763   0.840   14   19   19
  C3 Western Residual   26   0.438   0.800   0.824   22   26   26
  C4 Main Forest        9    0.541   0.662   0.691   9    8    9
  C5 Coastal Forest     5    0.622   0.823   0.809   5    5    5
  --------------------- ---- ------- ------- ------- ---- ---- ----

Run freely, the TLM drifts. Across the 66 wells its median efficiency is 0.42. It is negative at 11 wells, where a constant at the observed mean would do better. With the drainage term alone, as in Model B, the median rises to 0.82, a median per-well gain of 0.40, and the efficiency is positive at all 66 wells. With the drainage term at the network datum, as in Model A, the median is 0.77, a median gain of 0.37, and the efficiency is positive at 65 wells.

The gain rises with the drainage coefficient: Pearson r = 0.42 between Model A's per-well gain and its β₃ (p \< 0.001). The gain is largest at the fastest-draining cluster, C1, where it is 0.57 under Model B and 0.45 under Model A. C1 is also where the two forms differ most, as the single datum costs most there (Section 4.5). At C5 Model A is marginally the higher.

The pine forest is the exception. At C4 the drainage is slow, and the TLM's accumulation of error does least harm. The TLM is positive at all 9 wells. The median gain is 0.15 under Model B and 0.12 under Model A, and Model A is positive at 8. At two C4 wells, CEH13 and CEH14, Model A scores below the TLM. At CEH14 its drainage coefficient on the window is negative, and the free run diverges: its efficiency is −7.54 against 0.25 for the TLM. Model B, whose datum is fitted, scores 0.43 there and 0.44 at CEH13.

What the drainage term adds is the return a free-running model needs. Without it, a linear transfer of climate accumulates its errors, and how much that costs depends on how fast the aquifer drains. Where a fixed datum leaves the drainage term unidentified at a well, as at CEH14, the term can cost more than it adds.

## []{#anchor-1}5.5 Out-of-sample skill

Each form was fitted on the record before January 2018 and run freely over the years after, each month from the model's own previous level. The test was then run in reverse. Forward, Model B's median Nash--Sutcliffe efficiency (Nash and Sutcliffe, 1970) is 0.79 against 0.61 for Model A, and Model B is better at 88 % of wells. In reverse its median is 0.78 against 0.67, and it is better at 77 %. The advantage is clearest in the open dune. Under the coastal forest the two forms are close. At C4 both forecast poorly, with forward medians of 0.08 for Model B and 0.21 for Model A.

The poor forecast at C4 could reflect the forcing rather than the drainage. One PET index and one fitted β₂ stand for every unit. That includes a pine canopy whose interception changes when it is thinned or felled. A test fixed before the run (Script 50, D-260) refitted every C4 and C5 well with the canopy's interception taken out of the rainfall. Interception was removed either as a constant fraction or following a satellite canopy index. A constant fraction is absorbed by β₁ and changes nothing. Letting interception follow the canopy raised the median forward efficiency at the inner C4 wells from 0.22 to 0.53. However, it worsened the full-record fit by the Bayesian information criterion (BIC), and it left both Model B's identification and the summer-minus-winter residual unchanged. At the four wells beside the clearfell of December 2017, it made the forecast far worse. In a check added after the run, a single step in the inner wells' rainfall at the felling recovered most of the gain (0.49). The gain therefore reflects a one-off shift after 2018, not the canopy being tracked. By the rule, the forcing reading is not resolved at either forest cluster.

## []{#anchor-1}5.6 Identification, and why Model B does not set the datum

Model B pays for its fit. Its intercept and β₃ are almost interchangeable: their estimates correlate at 0.96 at the median well. The level its drainage refers to is therefore fitted rather than physical. That level lies near each well's mean, a median 1.6 m below ground, at the identification floor of Section 4.2. With it, more of the mean loss is booked to atmospheric draw: a drainage share of 45 % against Model A's 68 %. Adopting it as the datum would make Model A identical to Model B. In Model A the β₂ and β₃ estimates are negatively correlated (−0.64). Atmospheric draw and drainage compete for the mean loss, which is the partition question again.

Pastas, fitted to the same wells on the full record, agrees with Model B well by well (Figure 2). Spearman ρ is 1.00 for β₁, 0.96 for β₂ and 0.98 for β₃, on the 63 wells whose response time Pastas identifies. By Section 2.3 that agreement is expected. It checks the implementation rather than the form.

## []{#anchor-1}5.7 Which form for which quantity

Model A, at a datum on the plateau, serves the coefficients, the water balance and thresholds inverted from the coefficients. Model B serves the quantities set by the mean-reversion time: the year-to-year persistence of the level, and forecasting within the climate the record spans.

A forward run into a different climate, whether a hindcast of a drier past or a projection, asks for a sustained shift of the mean level. There the one independent test favours Model A (Section 6.4). Every forward run here therefore uses Model A at the network datum, with Model B beside it as the fast-reversion bound. The two are reported as a pair on the same wells and never averaged.

Model A's β₃ carries its datum. The datum the drier decade supports (Section 6.5) is therefore carried as the sensitivity of a projection, not its basis. Take a 2080s high-emissions scenario (UKCP18 RCP8.5; Met Office, 2018), with comparison-window fits at the 57 wells both forms identify. The median sustained fall of the summer level is 0.51 m under Model A at the network datum, 0.44 m under Model A at 2.9 m and 0.36 m under Model B. Neither form serves a quantity where its β₃ is not identified.

# []{#anchor-1}6. What the record decides

## []{#anchor-1}6.1 Two bases, two questions

The coefficients a study reports belong to the record they were fitted on. In a network installed progressively, the record is not one thing. The cluster centroid is fitted on its full record, to characterize the cluster's mechanism with every month available. The per-well fit uses the common comparison window, the most recent 100 months at every well. Wells are then compared under the same climate, rather than over histories of different length and wetness.

To measure what the length of the record decides, both forms were refitted at every reference well. The records fitted ran from 24 months to twelve years long, and the full record was fitted too. Each fit was scored three ways: the stability of β₃, forecast skill inside the modern record, and a hindcast of an epoch no fit has seen.

## []{#anchor-1}6.2 What the window does to β₃

At the cluster centroids, fitting the comparison window instead of the full record shifts β₃ by +16 % at C1, +8 % at C2, +1 % at C3 and −3 % at C5, but by −34 % at C4. Well by well the picture is the same. The ratio of Model A's comparison-window β₃ to its full-record β₃ has a median of 1.03 (10th--90th percentile 0.78--1.12), and 0.73 at C4. The forest is where it matters, because its response is slow.

## []{#anchor-1}6.3 How much record each form needs

Each well's β₃ was refitted on every non-overlapping placement of each length. Its stable length was taken as the shortest record on which the median departure from the full-record β₃ is within 20 %.

Model A's β₃ is the more robust. Its median stable length is 24 months. That is the shortest length tested, and so an upper bound. Model A reaches stability within the lengths tested at 64 wells. Model B's median stable length is 60 months (62 wells), and its β₃ is identified on only 60 % of 24-month placements at the median well.

Measured in each well's Model B mean-reversion times, the stable length is 4.7 for Model A and 9.0 for Model B. The Model A figure is a maximum, because its stable length is on the floor of the test. The rule that a record must span several mean-reversion times holds, and it binds the free-intercept form harder.

The forest is the exception for both forms. At C4 Model A needs 120 months and Model B 144. Model B reaches stability within the lengths tested at only 5 of its wells.

Pastas, which estimates the response time directly, tells the same story. It identifies the response time at 53 of 66 wells on the comparison window and at 63 on the full record. The wells it loses on the window are mainly forest wells (9 at C4), whose response time is comparable with the window. The same rule withholds C4 from every quantity set by the mean-reversion time (Section 5.7).

## []{#anchor-1}6.4 Forecasting and hindcasting

Inside the modern record, Model B forecasts better at every length. Each form was fitted on the months before January 2018 and run freely after it. Model B's median Nash--Sutcliffe efficiency is 0.72 from 24 months of record and 0.79 from all of it. Model A's rises from −0.14 to 0.59 at 100 months and 0.61 when fitted on all the months before 2018. A site with a few years of record can forecast its own water table with the free-intercept form.

The one test no fit has seen is the Countryside Council for Wales record of 1989--96. It was read before the modern network was installed, at 9 wells that the network still reads, in a decade drier than any the fits contain. Hindcast from fits to the full modern record of each well, Model A is close to unbiased, with a median bias of 0.03 m. Model B is too wet by 0.30 m. Their median efficiencies are −0.14 and −1.46 respectively. The ordering holds at every record length, whether the fit is taken from the start or the end of the modern record. Model B's median bias lies between 0.27 and 0.51 m. Model A's is within 0.09 m of zero once the fit spans four years.

The two tests split by what they score. A forecast inside the modern record is dominated by the seasonal swing, which a fast reversion follows well. The drier decade is a sustained shift of the mean level, which Model A carries and Model B does not.

## []{#anchor-1}6.5 What the drier past says about the datum

If the drier decade favours Model A, it can also be asked which datum Model A should use. Model A was refitted at each well on the comparison window at every datum of the sweep, and each fit was used to hindcast the same decade. By a rule fixed before the run, the datum that maximizes the median efficiency is 2.9 m, with a band of 2.8--2.9 m within 0.05 of the best (median efficiency 0.44 at that datum, against −0.06 at the network datum). The median absolute bias is smallest at 2.6 m. Deeper than the network datum, every measure is worse. The drier past therefore does not ask for a deeper datum, as might be expected under drying. The network datum lies below the supported band, but it is close to unbiased on the same fits (median bias −0.01 m).

A second epoch, Ranwell's readings of 1951--53 (Ranwell, 1959), tests the same question nearly forty years earlier. The readings come from three sites whose positions are approximate, so this epoch is scored on the seasonal swing with the mean offset removed. By the same rule it supports 0.7 m (band 0.5--1.1 m). There Model A behaves as Model B does. The median efficiencies are 0.86 at that datum and 0.86 for Model B, against 0.46 at the network datum.

The two epochs disagree, and in the way the two tests of Section 6.4 do. The swing favours a shallow datum or a free intercept. The sustained shift favours a datum on the plateau.

What would the model need to match Ranwell's readings, and what could supply it? This was explored after the comparison above, so it describes rather than tests (Script 50, D-261). Scaling each coefficient of the paired wells, in turn and together, the readings ask for a weaker response to rain (β₁ ×0.7), a stronger evaporative draw (β₂ ×1.6) and faster drainage (β₃ ×4.0). The median efficiency across the 11 site--well pairs then rises from 0.57 to 0.84. Faster drainage is the shallow datum above in another form. On its own, though, the drainage scale is not identified: much slower and much faster drainage each improve the fit, and the pairs divide 7 to 4 between them.

Each candidate cause was then sized against that need. The weather was ordinary: every seasonal statistic of 1951--53 lies between percentiles 43 and 68 of all three-year windows of the climate record, and the five years before them at percentile 48. Little of a departure survives two years in the model (a fraction of 0.03--0.29 at the three main pairs), so earlier years cannot carry over within it. Rain from Ranwell's own gauge on the site makes the hindcast worse at every pair (median efficiency −0.35). Ranwell's pipes could not read below about a metre, but capping the model there leaves the efficiency unchanged (0.57). A barer, rabbit-grazed dune would have recharged more and transpired less: lysimeters on dune sand drained 77 % of rain under bare sand and 44 % under natural dune vegetation (Minderman and Leeflang, 1968). That is the opposite of what is needed, and at its upper bound it lowers the efficiency to −0.03. The forest planted since now stands within its drawdown reach of one of the three sites. Open-ground wells within that reach differ from those beyond it by at most 11 % in any coefficient, two of the three in the wrong direction, and removing that difference at the 6 pairs concerned lifts the median efficiency only to 0.60. A sea level a few centimetres lower moves the drainage base the wrong way, and too little to matter. Two candidates point the right way: drains dug for the young plantation, and a lower outlet of Llyn Rhos-Ddu beside one of Ranwell's three sites. Neither is recorded, and the record cannot size either. What can be measured is the result: relative to the model, the seasonal swing at the three main pairs was 3--20 % smaller then than it is now.

## []{#anchor-1}6.6 A second, slower store?

The two epochs ask for two time scales. One is a fast return of the level to its mean, which the seasonal swing of 1951--53 and the free-intercept form both show. The other is a slow one, which holds the level through the drier decade where the no-intercept form at the network datum places it. A single linear store has one time scale, so it can match one epoch or the other but not both. The natural explanation is a second, slower store in parallel with the first, responding to the same rainfall and evaporation.

That store was fitted at each cluster centroid beside the first. It was warmed up over the climate record since 1941, so that its starting level is not a free parameter. The two-store fit was compared with the one-store fit by the Bayesian information criterion. At every cluster the fit put essentially all of the response through one of the two stores, so it reduced to a single store, and the criterion preferred one store. A slow response to the same climate therefore does not explain why the water table stood above the single-store model in the early years of the record.

At a site with a pine plantation, a second store invites a specific reading. The reading is that the plantation has drawn down a body of water that was once there, and that the early record caught the last of it. Two features of the record bear on it.

First, a step, a relaxing step and a ramp were each fitted at every cluster centroid, with the date profiled. They find the early excess to be a transient that drained within a few years, not the tail of a higher baseline. By rules fixed before the fit, a term earns its place only at the coastal-forest cluster (C5). At C2, C3 and C4 it improves the fit but fails the out-of-sample test. C1 does not need it. No dated felling falls within the fitted interval.

Second, with any such term the drier decade before the network becomes markedly too wet at the clusters that have wells from that decade. The level was therefore not held higher then. The main-forest cluster (C4) has no wells from that decade.

Neither is a fair test of the forest reading at the forest clusters themselves. Until the canopy closed, the ground now under C4 and C5 behaved as open dune. A model warmed up from 1941 on today's forest coefficients therefore cannot hold a store filled before planting.

The fair test runs those years on the coefficients of the open-dune clusters the ground then resembled: C3 for C4, and C2 for C5. It then moves to the forest coefficients as the canopy closes. The move follows an S-shaped curve over the 15--20 years a Corsican pine canopy usually takes to close (Forest Research, n.d.). It was run for planting in 1947, 1956 and 1965, the start, middle and end of the planting.

A rule was fixed before the fit. A store drawn down by the plantation is supported only if, in every one of these cases, the two-store fit does three things: it beats the fit on forest coefficients throughout by a clear margin in the information criterion, it holds the forward out-of-sample test, and it reduces the early excess. No case passes at either cluster. At C4, planting in 1956 or 1965 yields a slow store with a time scale of one to two decades. That store fits better and reduces the 2006--08 excess by about a third, but its forecast beyond 2018 is far worse than that of the forest-throughout fit. At C5 a slow store appears only for the latest planting, and it falls short of the margin. On this record, a store drawn down across the open dune is not supported, and nor is a store drawn down by the plantation at C4 or C5.

C5 is also the cluster nearest the retreating shore, and the coastal reading needs the same test. A retreating coast lowers the water table near it progressively, at a rate set by the retreat (Hollingham, 2026a). The change that earns its place at C5 is not of that form. It is a fall concentrated in a few years that then settled, which the relaxing step fits markedly better than a ramp. A discrete erosion event could produce such a fall, and so could a change in the canopy. Heads alone cannot separate the two at a single cluster, so a forest-linked or coast-linked change at C5 remains possible.

A cause outside the monthly forcing was also tested. Prolonged rain events lose less to interception and evaporation than their monthly totals imply, and a monthly model cannot represent this. Daily rainfall from a gauge on Anglesey (Met Office, 2024) shows three things. Only one of the three winters of the early excess was unusual in the share of its rain that fell in long events. Later wet winters had as large a share. Finally, a term for long events, though it fits the early years better, forecasts worse at every cluster with an excess. How the rain fell does not explain the early excess.

## []{#anchor-1}6.7 Per well or per cluster?

Section 4's identification results come from the cluster centroids. The skill tests of Sections 5.5, 6.4 and 6.5 come from fits to each well. Whether that skill belongs to the coefficients the procedure reports depends on whether it survives a change of basis.

Each test was therefore run twice: once on each well's own coefficients, and once on its cluster centroid's, fitted on the same span. A centroid run at a well is shifted by the mean difference between the well and its centroid over the fitted months. It is then scored on how the level rises and falls, not on the cluster's mean depth.

A rule was fixed before the run. On a test, the cluster basis holds if its median efficiency is within 0.05 of the per-well basis or better. On the drier decade, its median absolute bias must also be within 0.05 m of the per-well basis or smaller.

Under the no-intercept form the cluster basis holds on all three tests. On the drier decade its median efficiency is −0.18 against −0.14, and its median absolute bias 0.23 m against 0.26 m. Against Ranwell's readings it scores 0.49 against 0.46 on the three headline pairings, and 0.70 against 0.57 over all 11. Its seasonal range is 1.00 of Ranwell's on average, against 1.09 for the per-well fits. In the split-sample test it scores 0.70 against 0.61 forward and 0.66 against 0.67 backward.

Under the free-intercept form the cluster basis also holds on all three tests, and on the drier decade it does markedly better. Its median efficiency is −0.41 against −1.46, and its median absolute bias 0.21 m against 0.30 m. One reading is that a single well's intercept carries that well's own mean level over the modern record, while the centroid's averages many wells and carries less of it into the past. The test does not separate this reading from others.

The skill reported in this paper therefore does not depend on fitting each well separately. The per-cluster coefficients forecast and hindcast as well as each well's own, within the tolerance, and under the free-intercept form they transfer to the drier decade better.

## []{#anchor-1}6.8 Declaring the basis

Coefficients from the two bases differ where it matters most. Each analysis should therefore state which record it fitted and over which it was evaluated. Here a register lists, for every analysis, the wells, the record fitted and the record evaluated. The register is checked automatically against the fitting call in each script before results are published. Every coefficient in this paper carries its basis in its source file. Section 6.7 compares the two bases on the skill tests.

# []{#anchor-1}7. A procedure for other sites

The procedure below is for a head-dependent drainage model fitted to monthly levels. It applies at a site where no water-balance flux (drainage, evapotranspiration or recharge) is measured independently.

1.  **Sweep the datum** over the plausible range of the drainage base. At each datum, refit at the scale at which the coefficients will be published, and record β₃, its significance, R², AIC and the mean drainage flux β₃·mean(h_disp).
2.  **Find the identification floor**. This is the shallowest datum from which every unit's β₃ is positive and significant at every deeper datum.
3.  **Fit the free-intercept form** and compute its zero-drainage level, z₀ − α_B/β₃. If this level coincides with each unit's fit-optimal datum, the data prefer mean reversion. A datum chosen on fit alone would then measure persistence, not drainage.
4.  **Locate the flux plateau**. It starts at the datum from which β₃·mean(h_disp) stays within a stated fraction of its deepest-datum value. On the plateau the flux and the partition are insensitive to the datum. t½ is not, and is reported as conditional on the datum.
5.  **Choose one datum** on or beyond the plateau for the unit with the deepest water table. It should lie below the fluctuation range everywhere and within the saturated thickness that boreholes allow.
6.  **Decide the frame**: fixed elevation, or depth below ground. First, regress each well's fit-optimal datum, as an elevation, on ground elevation. Second, fit a common datum in elevation across the network and compare its fit with that of a depth below ground. Then test a physically anchored datum, such as the depth to mean high water, for the partition it gives and the skill it costs.
7.  **Publish the cost**. Report each unit's ΔAIC and ΔR² at the chosen datum, and the range over which the rankings by β₃ and by flux are unchanged.
8.  **Referee the dynamics without a model**. Compare each form's e-folding time with the lag-1 autocorrelation of the deseasonalized level. Run a split-sample free-run test, and a free run against the same model without its drainage term.
9.  **Assign each quantity to the form that identifies it**. Use the no-intercept form for coefficients, water balance and thresholds. Use the free-intercept form for persistence and for forecasting within the climate of the record. For forward runs into a different climate, use the form an independent epoch supports, with the other beside it. Use neither where β₃ is not identified.
10. **Declare the fitting basis** of every analysis. Measure how long a record each form needs before reading its β₃. Wherever an independent epoch exists, test a sustained response against it.

## []{#anchor-1}7.1 The procedure at Newborough

Table 2 sets out what the procedure gives at Newborough, with each quantity under the form that identifies it. The coefficients and the partition of the mean loss come from the no-intercept form at the network datum, which lies on every cluster's flux plateau (Section 4.4). The mean-reversion time comes from the free-intercept form, shown beside its model-free estimate (Section 5.2). The table also gives the record each form needs before its β₃ is stable (Section 6.3).

The partition is a share of the modelled loss, in units of water-table change. Converting it to a depth of water needs a specific yield, which heads alone do not give. The share is also the quantity most open to doubt (Table 3). Moving the datum along the plateau, or to each well's depth to mean high water, changes it by a few points. The wells of a cluster also scatter around the centroid's value. The larger change comes from the form. Under a fitted base (Model B) the share falls to between 29 and 60 %. It falls furthest at the lake edge (37 % at C1), because the fitted base lies near each well's mean level (Section 5.6). The no-intercept form at a datum on the plateau remains the basis for the partition (Section 5.7), and the partition is reported with that condition.

**Table 2.** The procedure applied at Newborough, per cluster, each quantity under the form that identifies it. Coefficients, drainage share and closure residual (Residual): the no-intercept form (Model A) fitted to each cluster centroid at z₀ = 3.7 m; the residual of the mean water balance is in units of water-table change. τ_B, mean-reversion time: median over the cluster's wells of the free-intercept form's e-folding time; τ_obs, the model-free estimate from the level's lag-1 autocorrelation (Section 5.2); n.i., not identified on the record. L_A and L_B, record for a stable β₃ in each form: median, over the wells that reach it within the lengths tested, of the shortest record on which the median departure from the full-record β₃ is within 20 % (Section 6.3); a value equal to the shortest length tested is an upper bound. Table 3 gives the drainage share under each source of uncertainty.

  --------------------- ------- ------- ------- ---- ------ ------------- -----------
  C1 Lake Edge          4.578   0.911   0.089   86   −4.1   2.1 / 2.0     24 / 60
  C2 Dune               3.896   1.666   0.063   69   −3.3   4.4 / 4.1     24 / 36
  C3 Western Residual   3.758   1.778   0.062   65   0.3    7.4 / 6.3     24 / 80
  C4 Main Forest        2.476   2.570   0.018   24   0.1    n.i.          120 / 144
  C5 Coastal Forest     2.412   1.248   0.045   63   −3.2   13.3 / 12.0   36 / 100
  --------------------- ------- ------- ------- ---- ------ ------------- -----------

**Table 3.** The drainage share of the mean loss (%) under each source of uncertainty, per cluster. Floor, Datum and Deep: the no-intercept form (Model A) fitted to each cluster centroid with the datum at the identification floor (1.6 m), at the network datum (3.7 m) and at the deepest datum swept (8 m) (Section 4.4). Model A, MHW datum and Model B, wells: median over the cluster's n reference wells fitted on their full records, with the 10th--90th percentile in brackets, under the no-intercept form at the network datum, the same form at each well's depth to mean high water (Section 4.7) and the free-intercept form (Section 5.6). Statistical uncertainty in the fitted coefficients is not included. A negative value marks wells at which the drainage term is not identified.

  --------------------- ---- ---- ---- ---- ------------- ------------- -------------
  C1 Lake Edge          7    73   86   89   87 (79--95)   89 (76--99)   37 (29--45)
  C2 Dune               19   57   69   72   71 (65--74)   72 (67--75)   42 (38--49)
  C3 Western Residual   26   47   65   69   65 (50--75)   67 (52--77)   55 (38--61)
  C4 Main Forest        9    4    24   28   31 (4--41)    34 (0--45)    29 (−5--42)
  C5 Coastal Forest     5    26   63   68   63 (60--72)   64 (61--70)   60 (50--67)
  --------------------- ---- ---- ---- ---- ------------- ------------- -------------

# []{#anchor-1}8. Discussion

## []{#anchor-1}8.1 What heads alone can and cannot give

The water level records the net of what enters and leaves. A head-only model can therefore always close the mean balance. On its own, however, it cannot say how the mean loss divides between evapotranspiration and drainage. Model A answers by an assumption about where drainage is measured from, and Model B by a fitted equilibrium level. The two answers differ (68 against 45 % drainage at the median well). Only an independent flux measurement, from tracers, outflow gauging or eddy covariance, can close that question.

What heads alone do give is substantial. They give the ranking of units by recharge sensitivity, evaporative draw and drainage, and here that ranking does not change across the plateau. They give the dynamics, on which two independent checks agree. And they give the range of the partition over the datums the record admits. Reporting the partition as a range conditional on the datum is more honest than a single figure. As Section 4.7 shows, it is also more robust than it might appear, because a physically motivated datum lands on the same plateau.

## []{#anchor-1}8.2 The regime boundary as a site property

The identification floor sits near the shallow end of the water table's range, and Model B's zero-drainage level sits on it. Both are properties of this aquifer's water-table depths, not general constants. At a site with a deeper or shallower water table the boundary moves. The sweep must therefore be repeated there, rather than the number reused. The same holds for the plateau. Its onset at each cluster follows that cluster's mean depth to water. This is why a single network datum has to be chosen for the deepest unit, and why its cost is paid mainly where the water table is shallowest.

## []{#anchor-1}8.3 Naming the quantity

The literature calls both readings of β₃ a memory. One is the time a groundwater system takes to re-equilibrate with a change in recharge, its "hydraulic memory" (Cuthbert et al., 2019). The other is the persistence of level anomalies, measured by their autocorrelation (Nygren et al., 2022). Neither is a memory, and here the two differ more than twofold.

The no-intercept recession constant describes how storage above an assumed base drains, and it scales with that base. The free-intercept mean-reversion time describes how quickly the level forgets a disturbance, and it does not depend on any base. Persistence of anomalies and the averaging behaviour of multi-year metrics depend on the second. In a one-store model the sustained response to a climate shift would depend on it too, but here it does not. The drier decade of Section 6.4 is reproduced by the slower no-intercept form, not by the mean-reversion time. A second store driven by the same climate does not reconcile the two (Section 6.6).

Interpreting persistence and multi-year averages through the first, as the no-intercept form invites, overstates persistence by a factor that grows with the datum, and with it the case that spring levels carry the previous year's anomaly. Naming the quantity removes an ambiguity that otherwise propagates silently into persistence, projection and ecological interpretation.

## []{#anchor-1}8.4 Relation to transfer-function practice

Free-base transfer-function models, of which Pastas is the reference implementation, estimate the mean-reversion form. That is the right form for forecasting and for persistence. Its agreement here with the model-free autocorrelation estimate and the split-sample test supports its use. Its agreement with Pastas is an identity check, not independent evidence.

A drainage reading of the same coefficient, and the water-balance partition that comes with it, requires the datum and the plateau test, which transfer-function practice does not perform. The reason is that the free base absorbs exactly the information the test needs. The two practices are therefore complementary rather than competing. The free-base model serves the dynamics, and the fixed-datum model on the plateau serves the balance. Each is checked against the other through the identity of Section 2.2.

## []{#anchor-1}8.5 Limits

The forcing comes from one climate station outside the site, at monthly resolution. Thornthwaite PET is an index of demand rather than a measured flux, so β₂ is an effective coefficient. The model is linear and time-invariant. Changes in land cover over the record are handled elsewhere, by before--after designs, rather than within the model.

The one exception is the pre-canopy test of Section 6.6, which moves the coefficients through canopy closure. Its timing rests on three planting years spanning the planting period and a literature closure age, not on compartment records. A slower closure on the dunes is untested.

The forest cluster's free-intercept drainage coefficient is not identified on the record. This withholds it from the quantities that depend on the mean-reversion time. A slow response is one reading of that. A forcing that misrepresents the forest's evapotranspiration is another, and the direct test of Section 5.5 did not resolve between them.

The independent tests of the sustained response rest on 9 wells in one decade, and on three sites, approximately placed, in another; why the earlier epoch's swing differs is not resolved (Section 6.5). Finally, both frame tests of Section 4.6 rest on fit, which by Section 4.3 tracks mean levels. They show that the drainage base follows the ground, not where it physically lies.

# []{#anchor-1}9. Conclusions

A head-dependent drainage model fitted to monthly water levels returns a drainage coefficient whose meaning depends on the intercept, the datum and the record.

Without an intercept, and with the datum below an identification floor, the coefficient reads as a Darcy discharge coefficient. The drainage flux and the partition of the mean loss are then insensitive to the datum, and the recession constant is conditional on it. With a free intercept, the same model measures the mean-reversion time, which an autocorrelation estimate and an out-of-sample test both support. A physically anchored datum reproduces the partition but not the dynamics.

The record decides how far either reading can be trusted. The no-intercept coefficient stabilizes on a short record, while the free-intercept one needs several mean-reversion times. Only an independent epoch, here a drier decade, tests a sustained response.

At Newborough, with the drainage base on the plateau, drainage takes between a quarter of the mean loss under the main forest (24--28 %) and most of it at the lake edge (86--89 %). The open dune is at 65--72 % and the coastal forest at 63--68 %, and evapotranspiration takes the rest. Under a fitted base the share is lower, 29--60 %, most so at the lake edge. Away from the main forest the water table returns to its mean within 2.1--13.3 months. A second, slower store, whether across the open dune or drawn down by the plantation, is not supported.

Each quantity should be taken from the form that identifies it, with the fitting basis declared and the datum sweep repeated at every site.

# []{#anchor-1}Data availability

The monitoring record, the analysis pipeline and every committed output from which the numbers in this paper are set are available in the project repository (https://github.com/newbroman/Newborough_Hydrology). Each number quoted in the text is read from a named committed output file.

# []{#anchor-1}Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work the author used Anthropic's Claude (successive Claude Opus and Claude Fable models, accessed through the Claude desktop application) for substantial drafting and editing of the manuscript text: composing prose from the author's analytical outputs and decisions, structuring and restructuring sections, and correcting the text against the study's committed analytical outputs. The conception and design of the study, the twenty-one-year manual dipwell record on which it rests, the analytical decisions, and the interpretation of the results are the author's own. Numerical values in the manuscript are set from the committed outputs of the analysis pipeline, and a decision log records the methodological and editorial calls made by the author during the work. After using this tool the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

# []{#anchor-1}Figures

![](Pictures/0.png){width="468pt" height="386.64pt"}

Figure 1. Datum sweep of the cluster-centroid no-intercept model. Top: the fitted mean drainage flux β₃·(z₀ + mean h) against the datum depth z₀; bottom: the drainage share of the modelled mean loss. Shaded: the range shallower than the identification floor, where at least one cluster's β₃ is non-positive or not significant. Dotted: the network datum.

![](Pictures/1.png){width="311.11pt" height="560pt"}

Figure 2. Per-well coefficients of Pastas's exponential-response model against the state-space model on the full record: Model B filled, Model A hollow; crosses mark wells whose response time Pastas does not identify. Dashed: 1:1.

# []{#anchor-1}References

Akaike, H. (1974) A new look at the statistical model identification. *IEEE Transactions on Automatic Control* 19(6), 716--723. doi:10.1109/TAC.1974.1100705

Bakker, M. and Schaars, F. (2019) Solving groundwater flow problems with time series analysis: you may not even need another model. *Groundwater* 57(6), 826--833. doi:10.1111/gwat.12927

Bloomfield, J.P. and Marchant, B.P. (2013) Analysis of groundwater drought building on the standardised precipitation index approach. *Hydrology and Earth System Sciences* 17(12), 4769--4787. doi:10.5194/hess-17-4769-2013

Collenteur, R.A., Bakker, M., Caljé, R., Klop, S.A. and Schaars, F. (2019) Pastas: open source software for the analysis of groundwater time series. *Groundwater* 57(6), 877--885. doi:10.1111/gwat.12925

Cuthbert, M.O., Gleeson, T., Moosdorf, N., Befus, K.M., Schneider, A., Hartmann, J. and Lehner, B. (2019) Global patterns and dynamics of climate--groundwater interactions. *Nature Climate Change* 9(2), 137--141. doi:10.1038/s41558-018-0386-4

Delworth, T.L. and Manabe, S. (1988) The influence of potential evaporation on the variabilities of simulated soil wetness and climate. *Journal of Climate* 1(5), 523--547. doi:10.1175/1520-0442(1988)001\<0523:TIOPEO\>2.0.CO;2

Forest Research (n.d.) Corsican pine (CP). Tree species database. Forest Research, Farnham. https://www.forestresearch.gov.uk/tools-and-resources/tree-species-database/131590-corsican-pine-cp-2 (accessed 11 October 2026).

Hollingham, M. (2026a) A parameter-sparse state-space framework for characterizing coastal dune-aquifer architecture from manual dipwell records. Companion paper.

Knotters, M. and Bierkens, M.F.P. (2000) Physical basis of time series models for water table depths. *Water Resources Research* 36(1), 181--188. doi:10.1029/1999WR900288

Knotters, M. and van Walsum, P.E.V. (1997) Estimating fluctuation quantities from time series of water-table depths using models with a stochastic component. *Journal of Hydrology* 197(1--4), 25--46. doi:10.1016/S0022-1694(96)03278-7

Met Office (2018) UKCP18 Regional Projections on a 12 km grid over the UK for 1980--2080. Centre for Environmental Data Analysis. Met Office Hadley Centre. Available at: https://catalogue.ceda.ac.uk/uuid/b4d24b3df3754b9d9028447eb3cbd878

Met Office (2024) MIDAS Open: UK daily rainfall data, v202407. NERC EDS Centre for Environmental Data Analysis. doi:10.5285/8606115371e44b079e25d479cfec465c

Minderman, G. and Leeflang, K.W.F. (1968) The amounts of drainage water and solutes from lysimeters planted with either oak, pine or natural dune vegetation, or without any vegetation cover. *Plant and Soil* 28(1), 61--80.

Nash, J.E. and Sutcliffe, J.V. (1970) River flow forecasting through conceptual models. Part I --- A discussion of principles. *Journal of Hydrology* 10(3), 282--290.

Nygren, M., Barthel, R., Allen, D.M. and Giese, M. (2022) Exploring groundwater drought responsiveness in lowland post-glacial environments. *Hydrogeology Journal* 30(7), 1937--1961. doi:10.1007/s10040-022-02521-5

Obergfell, C., Bakker, M. and Maas, K. (2019) Identification and explanation of a change in the groundwater regime using time series analysis. *Groundwater* 57(6), 886--894. doi:10.1111/gwat.12891

Peters, E., Torfs, P.J.J.F., van Lanen, H.A.J. and Bier, G. (2003) Propagation of drought through groundwater --- a new approach using linear reservoir theory. *Hydrological Processes* 17(15), 3023--3040.

Peterson, T.J. and Western, A.W. (2014) Nonlinear time-series modeling of unconfined groundwater head. *Water Resources Research* 50(10), 8330--8355. doi:10.1002/2013WR014800

Ranwell, D.S. (1959) Newborough Warren, Anglesey. I. The dune system and dune slack habitat. *Journal of Ecology* 47(3), 571--601.

von Asmuth, J.R., Bierkens, M.F.P. and Maas, K. (2002) Transfer function-noise modelling in continuous time using predefined impulse response functions. *Water Resources Research* 38(12), 1287. doi:10.1029/2001WR001136
