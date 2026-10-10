<!-- GENERATED MIRROR of docs/papers/paper_M/PaperM_v1_8.odt — do not edit. source-sha256=255558008a186b4b pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

Which quantity does each model form identify? A procedure for reservoir models fitted to monthly groundwater-level records

M. Hollingham

Draft --- 2026

# []{#anchor}Abstract

Monthly water-level records from shallow dipwell networks are common; measurements of the fluxes that drive them are not. Linear-reservoir and transfer-function models fitted to such records are widely used to infer the water balance, but three choices that decide what their coefficients mean are usually left implicit: whether the model has an intercept, the depth of the base that drainage is measured from, and which part of the record is fitted. We examine all three on 66 wells in a coastal dune aquifer at Newborough Warren, Wales. Without an intercept, the drainage coefficient carries the datum: below an identification floor the fitted drainage flux and the evapotranspiration--drainage partition become insensitive to the datum while the recession constant keeps scaling with it. With a free intercept the model is the same model at a fitted datum, and its drainage coefficient measures the rate at which the water table returns to its own mean. The two readings differ more than twofold (e-folding times of 15.8 and 6.5 months at the median well); a model-free autocorrelation estimate (5.1 months) and a split-sample test side with the free-intercept form for the dynamics, but an independent, drier decade recorded before the network sides with the no-intercept form for the level. The no-intercept drainage coefficient is stable on records of 24 months, the shortest tested, at the median well; the free-intercept one needs 60, and under pine forest both need far more. We set out a procedure that assigns each reported quantity to the form that identifies it.

**Keywords:** groundwater time series; linear reservoir; drainage datum; mean-reversion time; dune slack; model identification

# []{#anchor}Plain-language summary

Many wetlands depend on groundwater, such as the damp hollows (dune slacks) among sand dunes. They are usually monitored by measuring the water level in shallow pipes about once a month. What is almost never measured is where the water comes from and where it goes: how much rain soaks in, how much is drawn back up by plants and the sun, and how much drains away underground. Scientists therefore try to work these out from the water levels alone, by fitting a simple mathematical model to the record.

This paper shows that three choices made when fitting such a model, usually without comment, change what its answers mean: whether the model includes a constant term, how deep the notional floor is that the water is assumed to drain towards, and which part of the record is used. All three are tested on 66 monitoring wells at Newborough Warren, a coastal dune system on Anglesey in Wales.

The key finding is that the model's drainage number can be read in two different ways. Without the constant, it describes drainage towards the chosen floor, and its value depends strongly on where that floor is placed; once the floor is deep enough, however, the split of the water budget between drainage and evaporation stops changing. With the constant, the floor is in effect worked out from the data, and the number describes how quickly the water table returns to its normal level after a wet or dry spell.

The two readings differ by more than a factor of two. At a typical well, the first says that a disturbance takes about 16 months to shrink to about a third of its size, and the second about 6.5 months. Two checks favour the second for how the water table behaves over time: a method that uses no model at all gives 5.1 months, and the second reading also does better on data held back from the fit. An independent record from an earlier, drier decade, made before the present wells were installed, points the other way and favours the first reading for the level itself.

The two readings also need different amounts of data. At a typical well the first is stable on 24 months of readings and the second needs 60, while under pine forest both need much longer. The paper ends with a step-by-step procedure that tells users which version of the model to trust for each quantity they want to report.

# []{#anchor}1. Introduction

Shallow groundwater governs the condition of dune slacks, fens, wet heaths and other groundwater-dependent wetlands, and the record on which their management rests is, in most places, a network of dipwells read by hand about once a month. Recharge, drainage and evapotranspiration are rarely measured at such sites. What is known about the water balance is therefore inferred from the levels themselves, by fitting a model that turns rainfall and evaporative demand into a water-level response.

Two families of head-only model are in common use. Transfer-function-noise models represent the level as the convolution of each driver with an impulse response, the simplest of which is the exponential response of a single linear reservoir (von Asmuth et al., 2002; Knotters and Bierkens, 2000). They are implemented in open software, notably Pastas (Collenteur et al., 2019) and HydroSight (Peterson and Western, 2014), and have been applied to shallow unconfined aquifers in a range of settings (Obergfell et al., 2019; Bakker and Schaars, 2019). State-space or difference-equation forms write the same reservoir directly as a monthly balance in which the change in level is driven by rainfall, by evaporative demand, and by a drainage loss proportional to the head above a base (Knotters and van Walsum, 1997; Peters et al., 2003). The two are closely related, and both return a small number of coefficients that are read physically: a recharge sensitivity, an evaporative coefficient and a drainage rate or response time.

The drainage coefficient is read in two incompatible ways. In one, it is a linearized Darcy coefficient: the fraction of the stored head above the drainage base that leaves each month, from which a drainage flux and a partition of the mean loss between drainage and evapotranspiration follow. In the other, it is a response time or "memory": how long a departure of the water table from its usual level persists. Both readings appear in applied studies, often of the same coefficient, and the quantities derived from them, such as half-lives, persistence of anomalies and sustained responses to a change in climate, inherit whichever reading was intended. Which reading a given fit actually supports depends on choices that are seldom reported: whether an intercept is fitted, where the drainage base is placed, and which months enter the fit.

This paper makes those choices explicit and shows what each decides. It uses a long monthly record from a coastal dune aquifer, where the drainage base is physically uncertain, the water table lies within a few metres of the surface, and the network spans open dune and pine plantation with very different response speeds. Its contributions are five. First, the no-intercept and free-intercept forms are one model family, separated only by the datum: the free-intercept form is the no-intercept form at a fitted datum, and is term for term the exponential-response model of Pastas, and without the drainage term it reduces to a linear transfer of climate, whose free run drifts (Sections 2 and 5.4). Second, without an intercept the datum is not inert, and a datum sweep exposes a regime boundary below which the drainage reading holds and the water balance becomes insensitive to the datum, while the recession constant does not (Section 4). Third, a physically anchored datum reproduces that water balance but degrades the model's dynamics (Section 4.7). Fourth, the free-intercept form measures the mean-reversion time, which a model-free autocorrelation estimate and an out-of-sample test both support; each form should therefore be used for the quantity it identifies (Section 5). Fifth, the record decides how far either reading can be trusted: the two forms need different lengths of record, and an independent epoch drier than the fitted record separates them where fit within the record cannot (Section 6). Section 7 sets these out as a procedure any site with a monthly head record can follow.

# []{#anchor}2. The model family

## []{#anchor}2.1 The displacement form

The water-level change during month *t* is written

Δh(t) = β₁·P(t) − β₂·PET(t) − β₃·h_disp(t−1), with h_disp(t−1) = z₀ + h(t−1),

where *h* is the level (negative below ground), P and PET are the rainfall and potential-evapotranspiration totals for month *t*, and z₀ is the depth of the drainage datum below ground. The drainage term is driven by the level at the start of the month, h(t−1), which avoids regressing a change on its own end-point. Written as a displacement above the datum, β₃ is positive wherever the water table lies above the datum, and drainage is proportional to head above a base: the linearized Darcy flux of a shallow unconfined aquifer draining to a boundary (Knotters and van Walsum, 1997). Fitted on raw depth instead (z₀ = 0), 2 of the five clusters at this site return a negative β₃, so depth below ground alone does not represent the gradient that drives drainage.

## []{#anchor}2.2 Model A and Model B

Model A is the form above, fitted by ordinary least squares with no intercept. Model B adds a constant α_B:

Δh(t) = α_B + β₁·P(t) − β₂·PET(t) − β₃·(z₀ + h(t−1)).

Because −β₃·z₀ is itself a constant, Model B is Model A with the datum moved to

z_B = z₀ − α_B/β₃,

the level at which the fitted drainage is zero. The two forms are therefore one family indexed by the datum: Model A fixes it in advance, Model B estimates it. Two consequences follow, and they organize the rest of the paper.

In Model A the datum is not inert. A shift in z₀ cannot be absorbed by an intercept, so it is redistributed across β₁, β₂ and β₃ together. Because the mean drainage loss β₃·mean(h_disp) must still close the mean water balance, β₃ falls as z₀ deepens, roughly as 1/(z₀ + mean h) once the flux has settled (Section 4.4), and the recession constant t½ = ln 2/β₃ rises with it. t½ is a property of the datum as much as of the aquifer.

In Model B the datum cancels. β₃ is then the fraction of a departure from the water table's own equilibrium that is recovered each month. Under constant forcing a departure decays as (1 − β₃)ᵗ, so the e-folding time −1/ln(1 − β₃) is the mean-reversion time, a property of the record and not of any reference level.

## []{#anchor}2.3 Relation to Pastas

Pastas (Collenteur et al., 2019) simulates the head as a base level plus the response to a recharge series. With linear recharge and the exponential response function,

R(t) = P(t) + *f*·PET(t), θ(t) = *A*·(1 − exp(−t/*a*)),

where *A* is the steady gain, *a* the response time, *f* the (negative) evaporation factor and *d* the base level. For a recharge rate that is constant through each month, the exponential response over one monthly step is exactly the recurrence

h(t) − *d* = exp(−1/*a*)·(h(t−1) − *d*) + *A*·(1 − exp(−1/*a*))·R(t),

which is Model B written in Pastas's parameters:

β₃ = 1 − exp(−1/*a*), β₁ = *A*·β₃, β₂ = −*f*·*A*·β₃, *d* = −(z₀ − α_B/β₃),

the last being Model B's zero-drainage level. Pastas works in days; its parameters were converted to months using the mean month length, and the conversion was checked by refitting, with Pastas, synthetic wells generated from the cluster coefficients. Model A has no Pastas counterpart, because Pastas has no datum and no separate drainage term. Agreement between Pastas and Model B therefore checks an implementation; it is not independent evidence for either form (Section 5.6).

## []{#anchor}2.4 What neither form can decide

The mean loss is drainage plus atmospheric draw, and from heads alone the split between them depends on the level drainage is measured from. Model A sets that level by assumption, Model B by fit. Neither identifies the absolute partition between evapotranspiration and drainage without an independent measurement of at least one of the fluxes (drainage, evapotranspiration or recharge); the partition is reported here as conditional on the datum, together with the range of datums over which it holds (Section 4).

## []{#anchor}2.5 The family without drainage

Setting β₃ = 0 in Model B leaves

Δh(t) = α₀ + β₁·P(t) − β₂·PET(t),

a linear transfer of rainfall and evaporative demand to the change in level, with no term that depends on the level itself. This traditional linear model (TLM) is the usual first model of a water-table response to climate. Run forward from an initial level, it has nothing that returns the level towards a mean, so each month's error is carried into every later month; the drainage term is what supplies that return. The TLM is nested in Model B, and the two differ by the drainage term alone. It differs from Model A in two ways: Model A adds the drainage term and also replaces the TLM's free constant by −β₃·z₀, which is fixed by the datum and tied to the drainage rate (Section 2.2).

# []{#anchor}3. Site, record and the fitting bases

Newborough Warren (Anglesey, Wales) is a coastal dune system of 865 ha with a monitoring network of 88 dipwells read at the end of each month; monthly rainfall and Thornthwaite PET come from a single station, RAF Valley, 16 km away. A reference network of 66 wells is admitted on record length (at least 100 months, still reporting at the end of the record); admitted records are longer, a median of 192 months (range 140--252). The wells fall into five hydrogeological clusters by their per-well coefficients: open dune C1 Lake Edge, C2 Dune and C3 Western Residual, pine forest C4 Main Forest, and C5 Coastal Forest. The clustering is the subject of a companion paper (Hollingham, 2026a) and is used here only as a grouping.

Readings are bucketed to the month they describe, and rainfall and PET enter for the same month, with no lag. Two fitting bases are used, and every analysis declares which, in a register that is checked automatically against each script's fitting call. The first is the cluster centroid on the full record: one hydrograph per cluster, the mean of its members, fitted with every month available. The second is the per-well fit on a common comparison window, the most recent 100 months at every well, so that wells are compared under the same climate. Section 4 uses the first basis. Sections 4.7 and 5, and the common-elevation test of Section 4.6, fit each well on its own full record (the first test of Section 4.6 uses the per-well comparison-window fits), and the split-sample tests on the record either side of January 2018. Section 6 shows why the distinction matters for the drainage coefficient, and what the length of the record decides.

# []{#anchor}4. What the datum decides (Model A)

## []{#anchor}4.1 The sweep

The cluster-centroid Model A was refitted at every datum from 0.5 to 8.0 m below ground in 0.1 m steps, recording β₃, its significance, R², AIC (Akaike, 1974) and the mean drainage flux β₃·mean(h_disp) (Figure 1).

## []{#anchor}4.2 An identification floor

Shallower than 1.6 m, at least one cluster's β₃ is non-positive or not significant; from that depth down every cluster's β₃ is positive and significant (p \< 0.05) at every deeper datum. Shallower than the floor, the datum lies within the range the water table occupies and the drainage term is not identified.

## []{#anchor}4.3 What fit prefers, and why it is not the datum

The datum that minimizes AIC differs by cluster: 0.7, 1.2, 2.2, 6.0 and 3.7 m for C1--C5. Model B's zero-drainage level z₀ − α_B/β₃ at the same centroids is 0.69, 1.18, 2.16, 6.00 and 3.66 m: the same, within one sweep step, at every cluster. This is the algebra of Section 2.2 made visible: the best-fitting Model A is Model B. A datum chosen on fit alone measures mean reversion, not drainage.

## []{#anchor}4.4 A flux plateau

Deeper than the floor, β₃ keeps falling but the mean drainage flux does not. At 3.7 m the flux is 0.97, 0.96, 0.93, 0.82 and 0.89 of its value at the deepest datum swept (C1--C5), and it stays within 80 % of that value from 1.7 m (C1) to 3.6 m (C4). On the plateau the drainage share of the mean loss settles too. From the floor to 3.7 m to 8 m it runs 73, 86 and 89 % at C1; 57, 69 and 72 % at C2; 47, 65 and 69 % at C3; 26, 63 and 68 % at C5; and 4, 24 and 28 % at C4.

Two regimes therefore exist. Near the water table the partition swings with the datum and β₃ behaves as a reversion rate. On the plateau the partition and the flux are insensitive to the datum and β₃ reads as a Darcy discharge coefficient, while t½ continues to scale with the datum and must be reported as conditional on it.

## []{#anchor}4.5 The cost of one datum

A single network datum, z₀ = 3.7 m, is chosen on the plateau for the deepest cluster and below the fluctuation range everywhere. Against each cluster's own optimum it costs 92.8, 28.5, 8.0, 0.4 and 0.0 AIC units for C1--C5, and an R² lower by at most 0.086 (C1). The cost is largest where the water table is shallowest and vanishes under the forest. The ranking of clusters by β₃ is the same at every swept datum from 0.5 m, and the ranking by mean flux from 1.2 m.

## []{#anchor}4.6 Elevation or depth

Is the drainage base a fixed height or a depth below ground? Two tests address it. The first expresses each well's fit-optimal datum as an elevation and regresses it on the well's ground elevation: a fixed base predicts a slope of 0, a base that follows the surface a slope of 1. Across the 66 reference wells, which span 10.9 m of ground elevation, the slope is 0.84 (R² 0.79). The test is partly circular: a fit-optimal datum tracks the well's mean depth to water (r = 0.59; Section 4.3), and the water table itself follows the ground, so the slope describes how the base follows the ground rather than locating it. In the second, a common datum in elevation was fitted at every well on its full record (79 wells, reference and extended), at every level from −2 to 8 m above Ordnance Datum in 0.25 m steps. Its best median R² is 0.736, at 2.5 m, against 0.739 for a depth of 3.7 m below ground on the same wells; the elevation datum fits worse than the depth datum at every level tried. Higher levels also leave the drainage term unidentified at many wells: at 6 m above Ordnance Datum β₃ is non-positive at 18 wells, against 1 at the depth datum. On fit the two frames are indistinguishable; depth below ground is preferred because it keeps the drainage term identified, and it is consistent with a base that follows the topography, each slack draining locally.

## []{#anchor}4.7 A physically anchored datum

The most defensible physical datum at a coastal site is the level to which the aquifer ultimately drains. Mean high water is a single elevation, so this datum is one point of the elevation sweep of Section 4.6, expressed as a depth at each well. Fitting each well on its full record with its own datum at its depth to mean high water (1.88 m above Ordnance Datum) places the datums between 1.7 and 12.5 m below ground (median 6.7 m). It reproduces the water-balance partition of the single 3.7 m datum: a median drainage share of 68 % against 68 %, with the 10th--90th percentile spread across wells almost unchanged (43--78 % against 39--79 %), because nearly every well's depth to mean high water lies on the plateau. It is nonetheless the worse model. The deeper datum passes into β₃, and the implied e-folding time roughly doubles (29 months against 16 at 3.7 m, and 5.1 observed); out-of-sample efficiency falls (Section 5.5) to 0.46 forward and 0.53 in reverse, against 0.61 and 0.67, and the anchored datum forecasts better at only 17 % of wells. A datum chosen on physical grounds thus answers the objection that a single depth is arbitrary (the partition is the same) without being the one adopted (the dynamics are worse).

# []{#anchor}5. What the intercept decides, and what the drainage term adds

## []{#anchor-1}5.1 Two quantities with one name

Model A's β₃ gives the recession of storage above the datum; Model B's gives the mean-reversion time. They differ more than twofold: fitted per well on the full record, at the median well the e-folding time is 15.8 months under Model A and 6.5 under Model B.

## []{#anchor-1}5.2 A model-free referee

The mean-reversion time can be measured without either model. If each month's level, less the mean for its calendar month, is treated as a first-order autoregressive process with lag-1 autocorrelation ρ₁, anomalies decay with the e-folding time −1/ln ρ₁ (Delworth and Manabe, 1988); level autocorrelation is used in the same way to characterize groundwater drought persistence (Bloomfield and Marchant, 2013). The median is 5.1 months. Cluster by cluster, Model B sits with it: 2.1 against 2.0 months at C1, 4.4 against 4.1 at C2, 7.4 against 6.3 at C3 and 13.3 against 12.0 at C5. Model A's median is about three times the observed value. At C4, Model B's β₃ is not identified on the record (Section 6.3).

## []{#anchor-1}5.3 Year-to-year persistence

A short mean-reversion time predicts that spring levels in successive years are close to independent. The expected lag-1 autocorrelation of spring level implied by the drainage term, the lag-12 autocorrelation of the monthly recurrence (1 − β₃)¹², is 0.16 at the median well under Model B and 0.47 under Model A, each fitted on the well's full record; the observed lag-1 autocorrelation of spring levels is −0.11. Taken at face value, Model A's expectation would make a five-year mean of spring levels a poorly averaged quantity; the record does not support that.

## []{#anchor-1}5.4 What the drainage term adds

At each reference well the TLM, Model A at the network datum of 3.7 m and Model B were fitted on the comparison window, the most recent 100 months, and each was run freely over the same months from the first observed level, each month from the model's own previous level. Skill is the Nash--Sutcliffe efficiency of the simulated level (Table 1). The test is in-sample: it asks whether a model that has seen the months can reproduce their trajectory without being corrected by them, which a forecast (Section 5.5) does not. Two comparisons follow from Section 2.5. The TLM against Model B isolates the drainage term, since the TLM is Model B with β₃ = 0. The TLM against Model A adds the drainage term and, with it, replaces the free constant by the datum-fixed −β₃·z₀. Corrected each month by the observed level instead, the TLM and Model A are indistinguishable (a median R² of 0.92 for both), because the observed level supplies the return the TLM lacks.

**Table 1.** Free-running skill of the traditional linear model (TLM), the no-intercept state-space model at z₀ = 3.7 m (Model A) and the free-intercept form (Model B), each fitted per well on the reference well's 100-month comparison window and scored over the same months. NSE is the Nash--Sutcliffe efficiency of the simulated level; n is the number of wells.

  --------------------- ---- ------- ------- ------- ---- ---- ----
  C1 Lake Edge          7    0.308   0.745   0.878   5    7    7
  C2 Dune               19   0.389   0.763   0.840   14   19   19
  C3 Western Residual   26   0.438   0.800   0.824   22   26   26
  C4 Main Forest        9    0.541   0.662   0.691   9    8    9
  C5 Coastal Forest     5    0.622   0.823   0.809   5    5    5
  --------------------- ---- ------- ------- ------- ---- ---- ----

Run freely, the TLM drifts. Across the 66 wells its median efficiency is 0.42, and it is negative at 11 wells, where a constant at the observed mean would do better. With the drainage term alone the median rises to 0.82 under Model B, a median per-well gain of 0.40, and the efficiency is positive at all 66 wells. With the drainage term at the network datum the median is 0.77 under Model A, a median gain of 0.37, positive at 65 wells. The gain rises with the drainage coefficient (Pearson r = 0.42 between Model A's per-well gain and its β₃; p \< 0.001) and is largest at the fastest-draining cluster, C1, where it is 0.57 under Model B and 0.45 under Model A. C1 is also where the two forms differ most, as the single datum costs most there (Section 4.5); at C5 Model A is marginally the higher.

The pine forest is the exception. At C4 the drainage is slow and the TLM's accumulation of error does least harm: the TLM is positive at all 9 wells, the median gain is 0.15 under Model B and 0.12 under Model A, and Model A is positive at 8. At two C4 wells, CEH13 and CEH14, Model A scores below the TLM. At CEH14 its drainage coefficient on the window is negative and the free run diverges (efficiency −7.54 against 0.25 for the TLM), while Model B, whose datum is fitted, scores 0.43 there and 0.44 at CEH13. What the drainage term adds is the return a free-running model needs: without it a linear transfer of climate accumulates its errors, and how much that costs depends on how fast the aquifer drains. Where a fixed datum leaves the drainage term unidentified at a well, as at CEH14, the term can cost more than it adds.

## []{#anchor-1}5.5 Out-of-sample skill

Each form was fitted on the record before January 2018 and run freely over the years after, each month from the model's own previous level, and then the reverse. Model B's median Nash--Sutcliffe efficiency (Nash and Sutcliffe, 1970) forward is 0.79 against 0.61 for Model A, better at 88 % of wells; in reverse it is 0.78 against 0.67 (better at 77 %). The advantage is clearest in the open dune; under the coastal forest the two forms are close; at C4 both forecast poorly (forward medians of 0.08 for Model B and 0.21 for Model A).

## []{#anchor-1}5.6 Identification, and why Model B does not set the datum

Model B pays for its fit. Its intercept and β₃ are almost interchangeable, their estimates correlating at 0.96 at the median well, so the level its drainage refers to is fitted rather than physical. That level lies near each well's mean, a median 1.6 m below ground, at the identification floor of Section 4.2, and with it more of the mean loss is booked to atmospheric draw: a drainage share of 45 % against Model A's 68 %. Adopting it as the datum would make Model A identical to Model B. In Model A the β₂ and β₃ estimates are negatively correlated (−0.64): atmospheric draw and drainage compete for the mean loss, which is the partition question again.

Pastas, fitted to the same wells on the full record, agrees with Model B well by well (Figure 2): Spearman ρ is 1.00 for β₁, 0.96 for β₂ and 0.98 for β₃, on the 63 wells whose response time it identifies. By Section 2.3 that is expected, and it checks the implementation rather than the form.

## []{#anchor-1}5.7 Which form for which quantity

Model A, at a datum on the plateau, serves the coefficients, the water balance and thresholds inverted from the coefficients. Model B serves the quantities set by the mean-reversion time: the year-to-year persistence of the level, and forecasting within the climate the record spans. A forward run into a different climate, whether a hindcast of a drier past or a projection, asks for a sustained shift of the mean level, and there the one independent test favours Model A (Section 6.4). Every forward run here therefore uses Model A at the network datum, with Model B beside it as the fast-reversion bound; the two are reported as a pair on the same wells and never averaged. Because Model A\'s β₃ carries its datum, the datum the drier decade supports (Section 6.5) is carried as the sensitivity of a projection, not its basis: for a 2080s high-emissions scenario (UKCP18 RCP8.5; Met Office, 2018) the median sustained fall of the summer level, on comparison-window fits at the 57 wells both forms identify, is 0.51 m under Model A at the network datum, 0.44 m under Model A at 2.9 m and 0.36 m under Model B. Neither serves a quantity where its β₃ is not identified.

# []{#anchor-1}6. What the record decides

## []{#anchor-1}6.1 Two bases, two questions

The coefficients a study reports belong to the record they were fitted on, and in a network installed progressively the record is not one thing. The cluster centroid is fitted on its full record, to characterize the cluster's mechanism with every month available. The per-well fit uses the common comparison window, the most recent 100 months at every well, so that wells are compared under the same climate rather than over histories of different length and wetness. To measure what the length of the record decides, both forms were refitted at every reference well on records from 24 months to twelve years long and on the full record, and each fit was scored three ways: the stability of β₃, forecast skill inside the modern record, and a hindcast of an epoch no fit has seen.

## []{#anchor-1}6.2 What the window does to β₃

At the cluster centroids, fitting the comparison window instead of the full record shifts β₃ by +16 % at C1, +8 % at C2, +1 % at C3 and −3 % at C5, but by −34 % at C4. Well by well the picture is the same: the ratio of Model A's comparison-window β₃ to its full-record β₃ has a median of 1.03 (10th--90th percentile 0.78--1.12), and 0.73 at C4. The forest is where it matters, because its response is slow.

## []{#anchor-1}6.3 How much record each form needs

Each well's β₃ was refitted on every non-overlapping placement of each length, and its stable length taken as the shortest record on which the median departure from the full-record β₃ is within 20 %. Model A's β₃ is the more robust: its median stable length is 24 months, the shortest length tested and so an upper bound, reached within the lengths tested at 64 wells, against 60 months for Model B (62 wells), whose β₃ is identified on only 60 % of 24-month placements at the median well. Measured in each well's Model B mean-reversion times, the stable length is 4.7 for Model A (at most, its stable length being on the floor of the test) and 9.0 for Model B: the rule that a record must span several mean-reversion times holds, and binds the free-intercept form harder. The forest is the exception for both forms. At C4 Model A needs 120 months and Model B 144, and Model B reaches stability within the lengths tested at only 5 of its wells.

Pastas, which estimates the response time directly, tells the same story: it identifies the response time at 53 of 66 wells on the comparison window and at 63 on the full record, and the wells it loses on the window are mainly forest wells (9 at C4), whose response time is comparable with the window. The same rule withholds C4 from every quantity set by the mean-reversion time (Section 5.7).

## []{#anchor-1}6.4 Forecasting and hindcasting

Inside the modern record, Model B forecasts better at every length. Fitted on the months before January 2018 and run freely after it, its median Nash--Sutcliffe efficiency is 0.72 from 24 months of record and 0.79 from all of it, while Model A's rises from −0.14 to 0.59 at 100 months and 0.61 on the full side. A site with a few years of record can forecast its own water table with the free-intercept form.

The one test no fit has seen is the Countryside Council for Wales record of 1989--96, read before the modern network was installed at 9 wells that it still reads, in a decade drier than any the fits contain. Hindcast from fits to the full modern record, Model A is close to unbiased, a median bias of 0.03 m, and Model B is too wet by 0.30 m (median efficiencies −0.14 and −1.46). The ordering holds at every record length, whether the fit is taken from the start or the end of the modern record: Model B's median bias lies between 0.27 and 0.51 m, and Model A's is within 0.09 m of zero once the fit spans four years.

The two tests split by what they score. A forecast inside the modern record is dominated by the seasonal swing, which a fast reversion follows well. The drier decade is a sustained shift of the mean level, which Model A carries and Model B does not.

## []{#anchor-1}6.5 What the drier past says about the datum

If the drier decade favours Model A, it can also be asked which datum Model A should use. Refitting Model A at every datum of the sweep on the comparison window and hindcasting the same decade, the datum that maximizes the median efficiency, by a rule fixed before the run, is 2.9 m, with a band of 2.8--2.9 m within 0.05 of the best (median efficiency 0.44, against −0.06 at the network datum); the median absolute bias is smallest at 2.6 m. Deeper than the network datum every measure is worse. The drier past therefore does not ask for a deeper datum, as might be expected under drying. The network datum lies below the supported band but is close to unbiased on the same fits (median bias −0.01 m).

A second epoch, Ranwell's readings of 1951--53 (Ranwell, 1959), tests the same question nearly forty years earlier, at three sites whose positions are approximate, so it is scored on the seasonal swing with the mean offset removed. By the same rule it supports 0.7 m (band 0.5--1.1 m), where Model A behaves as Model B does: median efficiencies of 0.86 there and 0.86 for Model B, against 0.46 at the network datum. The two epochs disagree, and in the way the two tests of Section 6.4 do: the swing favours a shallow datum or a free intercept, the sustained shift a datum on the plateau.

## []{#anchor-1}6.6 A second, slower store?

The two epochs ask for two time scales: a fast return of the level to its mean, which the seasonal swing of 1951--53 and the free-intercept form both show, and a slow one, which holds the level through the drier decade where the no-intercept form at the network datum places it. A single linear store has one time scale, so it can match one epoch or the other but not both. The natural explanation is a second, slower store in parallel with the first, responding to the same rainfall and evaporation. That store was fitted at each cluster centroid beside the first, warmed up over the climate record since 1941 so that its starting level is not a free parameter, and the two-store fit was compared with the one-store fit by the Bayesian information criterion. At every cluster the fit sent the slow store's share to zero and the criterion preferred one store. A slow response to the same climate therefore does not explain why the water table stood above the single-store model in the early years of the record.

At a site with a pine plantation, a second store invites a specific reading: that the plantation has drawn down a body of water that was once there, and that the early record caught the last of it. Two features of the record bear on it. First, a step, a relaxing step and a ramp were each fitted at every cluster centroid, with the date profiled: they find the early excess to be a transient that drained within a few years, not the tail of a higher baseline, and by rules fixed before the fit a term earns its place only at the coastal-forest cluster (C5); at C2, C3 and C4 it improves the fit but fails the out-of-sample test, C1 does not need it, and no dated felling falls within the fitted interval. Second, with any such term the drier decade before the network becomes markedly too wet at the clusters that have wells from that decade, so the level was not held higher then; the main-forest cluster (C4) has none. Neither is yet a fair test of the forest reading at the forest clusters themselves. Until the canopy closed, the ground now under C4 and C5 behaved as open dune, so a model warmed up from 1941 on today's forest coefficients cannot hold a store filled before planting. The fair test runs those years on the coefficients of the open-dune clusters the ground then resembled, C3 for C4 and C2 for C5, and switches at canopy closure; it has not been run. On this record, a store drawn down across the open dune is not supported, and a store drawn down by the plantation at C4 and C5 is neither shown nor excluded.

C5 is also the cluster nearest the retreating shore, and the coastal reading needs the same test. A retreating coast lowers the water table near it progressively, at a rate set by the retreat (Hollingham, 2026a). The change that earns its place at C5 is not of that form: it is a fall concentrated in a few years that then settled, which the relaxing step fits markedly better than a ramp. A discrete erosion event could produce such a fall, and so could a change in the canopy; heads alone cannot separate the two at a single cluster, so a forest-linked or coast-linked change at C5 remains possible. A cause outside the monthly forcing also remains open: prolonged rain events lose less to interception and evaporation than their monthly totals imply, which a monthly model cannot represent, and testing that needs daily rainfall.

## []{#anchor-1}6.7 Declaring the basis

Because coefficients from the two bases differ where it matters most, each analysis should state which record it fitted and over which it was evaluated. Here a register lists, for every analysis, the wells, the record fitted and the record evaluated, and it is checked automatically against the fitting call in each script before results are published; every coefficient in this paper carries its basis in its source file.

# []{#anchor-1}7. A procedure for other sites

For a head-dependent drainage model fitted to monthly levels at a site where no water-balance flux (drainage, evapotranspiration or recharge) is measured independently:

1.  **Sweep the datum** over the plausible range of the drainage base, refitting at the scale at which the coefficients will be published, and record β₃, its significance, R², AIC and the mean drainage flux β₃·mean(h_disp).
2.  **Find the identification floor**: the shallowest datum from which every unit's β₃ is positive and significant at every deeper datum.
3.  **Fit the free-intercept form** and compute its zero-drainage level z₀ − α_B/β₃. If it coincides with each unit's fit-optimal datum, the data prefer mean reversion, and a datum chosen on fit alone would measure persistence, not drainage.
4.  **Locate the flux plateau**: the datum from which β₃·mean(h_disp) stays within a stated fraction of its deepest-datum value. On the plateau the flux and the partition are insensitive to the datum; t½ is not, and is reported as conditional on the datum.
5.  **Choose one datum** on or beyond the plateau for the unit with the deepest water table, below the fluctuation range everywhere and within the saturated thickness that boreholes allow.
6.  **Decide the frame** (fixed elevation against depth below ground) by regressing each well's fit-optimal datum, as an elevation, on ground elevation, and by fitting a common datum in elevation across the network and comparing its fit with a depth below ground; test a physically anchored datum, such as the depth to mean high water, for the partition it gives and the skill it costs.
7.  **Publish the cost**: each unit's ΔAIC and ΔR² at the chosen datum, and the range over which the rankings by β₃ and by flux are unchanged.
8.  **Referee the dynamics without a model**: compare each form's e-folding time with the lag-1 autocorrelation of the deseasonalized level, and run a split-sample free-run test and a free run against the same model without its drainage term.
9.  **Assign each quantity to the form that identifies it**: no intercept for coefficients, water balance and thresholds; free intercept for persistence and forecasting within the climate of the record; for forward runs into a different climate, the form an independent epoch supports, with the other beside it; neither where β₃ is not identified.
10. **Declare the fitting basis** of every analysis, measure how long a record each form needs before reading its β₃, and test a sustained response against an independent epoch wherever one exists.

## []{#anchor-1}7.1 The procedure at Newborough

Table 2 sets out what the procedure gives at Newborough, each quantity under the form that identifies it: the coefficients and the partition of the mean loss from the no-intercept form at the network datum, which lies on every cluster's flux plateau (Section 4.4); the mean-reversion time from the free-intercept form beside its model-free estimate (Section 5.2); and the record each form needs before its β₃ is stable (Section 6.3). The partition is a share of the modelled loss, in units of water-table change; converting it to a depth of water needs a specific yield, which heads alone do not give.

**Table 2.** The procedure applied at Newborough, per cluster, each quantity under the form that identifies it. Coefficients, drainage share and closure residual (Residual): the no-intercept form (Model A) fitted to each cluster centroid at z₀ = 3.7 m; the residual of the mean water balance is in units of water-table change. τ_B, mean-reversion time: median over the cluster's wells of the free-intercept form's e-folding time; τ_obs, the model-free estimate from the level's lag-1 autocorrelation (Section 5.2); n.i., not identified on the record. L_A and L_B, record for a stable β₃ in each form: median, over the wells that reach it within the lengths tested, of the shortest record on which the median departure from the full-record β₃ is within 20 % (Section 6.3); a value equal to the shortest length tested is an upper bound.

  --------------------- ------- ------- ------- ---- ------ ------------- -----------
  C1 Lake Edge          4.578   0.911   0.089   86   −4.1   2.1 / 2.0     24 / 60
  C2 Dune               3.896   1.666   0.063   69   −3.3   4.4 / 4.1     24 / 36
  C3 Western Residual   3.758   1.778   0.062   65   0.3    7.4 / 6.3     24 / 80
  C4 Main Forest        2.476   2.570   0.018   24   0.1    n.i.          120 / 144
  C5 Coastal Forest     2.412   1.248   0.045   63   −3.2   13.3 / 12.0   36 / 100
  --------------------- ------- ------- ------- ---- ------ ------------- -----------

# []{#anchor-1}8. Discussion

## []{#anchor-1}8.1 What heads alone can and cannot give

The water level records the net of what enters and leaves, so a head-only model can always close the mean balance, but it cannot say on its own how the mean loss divides between evapotranspiration and drainage. Model A answers by assumption about where drainage is measured from, Model B by a fitted equilibrium level, and the two differ (68 against 45 % drainage at the median well). Only an independent flux measurement, from tracers, outflow gauging or eddy covariance, can close that question. What heads alone do give is substantial: the ranking of units by recharge sensitivity, evaporative draw and drainage, which here does not change across the plateau; the dynamics, which two independent checks agree on; and the range of the partition over the datums the record admits. Reporting the partition as a range conditional on the datum is more honest than a single figure and, as Section 4.7 shows, more robust than it might appear, because a physically motivated datum lands on the same plateau.

## []{#anchor-1}8.2 The regime boundary as a site property

The identification floor sits near the shallow end of the water table's range, and Model B's zero-drainage level sits on it. Both are properties of this aquifer's water-table depths, not general constants. At a site with a deeper or shallower water table the boundary moves, so the sweep must be repeated there rather than the number reused. The same holds for the plateau: its onset at each cluster follows that cluster's mean depth to water, which is why a single network datum has to be chosen for the deepest unit, and why its cost is paid mainly where the water table is shallowest.

## []{#anchor-1}8.3 Naming the quantity

Both readings of β₃ are called a memory in the literature: the time a groundwater system takes to re-equilibrate with a change in recharge, its "hydraulic memory" (Cuthbert et al., 2019), and the persistence of level anomalies measured by their autocorrelation (Nygren et al., 2022). Neither is one, and here they differ more than twofold. The no-intercept recession constant describes how storage above an assumed base drains and scales with that base; the free-intercept mean-reversion time describes how quickly the level forgets a disturbance and does not depend on any base. Persistence of anomalies and the averaging behaviour of multi-year metrics depend on the second. In a one-store model the sustained response to a climate shift would depend on it too, but here it does not: the drier decade of Section 6.4 is reproduced by the slower no-intercept form, not by the mean-reversion time, and a second store driven by the same climate does not reconcile the two (Section 6.6). Interpreting them through the first, as the no-intercept form invites, overstates persistence by a factor that grows with the datum, and with it the case that spring levels carry the previous year's anomaly. Naming the quantity removes an ambiguity that otherwise propagates silently into persistence, projection and ecological interpretation.

## []{#anchor-1}8.4 Relation to transfer-function practice

Free-base transfer-function models, of which Pastas is the reference implementation, estimate the mean-reversion form. That is the right form for forecasting and for persistence, and its agreement here with the model-free autocorrelation estimate and the split-sample test supports its use; its agreement with Pastas is an identity check, not independent evidence. A drainage reading of the same coefficient, and the water-balance partition that comes with it, requires the datum and the plateau test, which transfer-function practice does not perform, because the free base absorbs exactly the information the test needs. The two practices are therefore complementary rather than competing: the free-base model for dynamics, the fixed-datum model on the plateau for the balance, each checked against the other through the identity of Section 2.2.

## []{#anchor-1}8.5 Limits

The forcing comes from one climate station outside the site, at monthly resolution; Thornthwaite PET is an index of demand rather than a measured flux, so β₂ is an effective coefficient. The model is linear and time-invariant; changes in land cover over the record are handled elsewhere by before--after designs rather than within the model. The forest cluster's response is slow enough that its free-intercept drainage coefficient is not identified on the record, which withholds it from the quantities that depend on the mean-reversion time. The independent tests of the sustained response rest on 9 wells in one decade and three sites, approximately placed, in another. Finally, both frame tests of Section 4.6 rest on fit, which by Section 4.3 tracks mean levels; they show that the drainage base follows the ground, not where it physically lies.

# []{#anchor-1}9. Conclusions

A head-dependent drainage model fitted to monthly water levels returns a drainage coefficient whose meaning depends on the intercept, the datum and the record. Without an intercept and with the datum below an identification floor, the coefficient reads as a Darcy discharge coefficient, the drainage flux and the partition of the mean loss are insensitive to the datum, and the recession constant is conditional on it. With a free intercept, the same model measures the mean-reversion time, which an autocorrelation estimate and an out-of-sample test both support. A physically anchored datum reproduces the partition but not the dynamics. The record decides how far either reading can be trusted: the no-intercept coefficient stabilizes on a short record and the free-intercept one needs several mean-reversion times, and only an independent epoch, here a drier decade, tests a sustained response. Each quantity should be taken from the form that identifies it, the fitting basis declared, and the datum sweep repeated at every site.

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
