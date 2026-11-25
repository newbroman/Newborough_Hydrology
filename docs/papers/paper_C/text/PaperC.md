<!-- GENERATED MIRROR of docs/papers/paper_C/PaperC_v1_2.odt — do not edit. source-sha256=73115e60e8b17f54 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

Coastal retreat draws down a dune aquifer: separating shoreline erosion from climate in a 21-year dipwell record

M. Hollingham

2026

**Abstract**

**Study region:** Newborough Warren, Anglesey, north-west Wales: a coastal sand body with dune-slack habitat of European conservation importance, whose west-facing Caernarfon Bay shoreline is retreating. Its water table has been read monthly by hand at 88 dipwells over 21 years (2005--2026).

**Study focus:** Where a shoreline erodes, the seaward drainage boundary of the aquifer moves inland and draws the water table down behind it. Climate lowers the water table too, so a monthly dipwell record mixes the two. We separate them by the one property only the coast has: its effect depends on distance from the shore. A panel regression of per-well water-table trend against distance to the eroding shoreline is tested against shoreline retreat measured independently from coastlines digitized for 2006--2026, and against a model-free coast-to-inland transect.

**New hydrological insights for the region:** The water table deepens fastest at the coast, by 26.38 mm/yr at 150 m from the shoreline (95% CI 33.23 to 19.53), relative to wells further inland. The effect reaches 455 to 904 m inland, depending on the years fitted. Over the same years the shoreline retreated 2.32 m/yr. The two sides of the transect separated at 27.8 mm/yr, without any model. Coastal retreat accounts for most of the decline in the open dune nearest the shore and about half of it in the coastal forest. It accounts for none of the decline far inland. The method needs only routine dipwell records and a shoreline position. It transfers to any dune aquifer with a retreating coast.

**Highlights**

-   An eroding shoreline lowers the water table behind it; climate does not depend on distance.
-   Fitting trend against distance separates the two in a routine dipwell record.
-   Deepening is fastest at the coast and reaches 455--904 m inland.
-   Shorelines digitized for 2006--2026 give an independent retreat of 2.3 m/yr.
-   Inland wells decline too: the coast does not explain the whole site's fall.

**Keywords:** dune slack; groundwater; coastal erosion; shoreline retreat; Dupuit--Forchheimer; dipwell record

# []{#anchor}1. Introduction

Coastal dune aquifers are bounded on the seaward side by a drainage boundary at the shoreline. Where that shoreline is stable, the boundary is fixed and the water table behind it settles to a steady profile. Where the shoreline erodes, the boundary moves landward. The ground surface is lowered relative to the water table at the coast, the seaward hydraulic gradient steepens, and the water table near the coast falls over time along a Dupuit drawdown curve (Fetter, 2001). An eroding dune margin therefore draws down its own hinterland. The effect has been documented at the retreating Whiteford Burrows dune system in South Wales, where dune-front erosion lowered the water table in adjacent slacks (Robins, Pye and Wallace, 2013).

Dune-slack vegetation responds to the summer water table, and a falling summer water table is the commonest reason given for slack degradation. Where a slack lies near an eroding coast, two causes of a falling water table act at once. Climate acts across the whole aquifer: drier summers and higher evaporative demand lower every well. Coastal retreat acts only near the shore. Both appear in a dipwell record as a downward trend. A climate attribution that ignores the coast will fold the coastal decline into an apparently network-wide one, and overstate the climate effect at the wells nearest the shore.

Newborough Warren, on Anglesey in north-west Wales, has both. Its west-facing Caernarfon Bay frontage is retreating, chronically at the southern Twyni Penrhos frontage and in discrete storm events (Pye and Blott, 2024). Its dipwell network has been read monthly for 21 years. A companion paper characterizes the aquifer's behavioural clusters and their climate response with a state-space model (Hollingham, 2026a). A second assesses the forest clearfell and dune scraping carried out on the site (Hollingham, 2026b). Hollingham (2026a) reports a decline in summer minima across the network. This paper separates its coastal part.

The test rests on one property. Climate forcing is, to first order, the same at every well; coastal retreat depends on distance from the eroding shoreline. A regression of each well's long-term trend on its distance to that shoreline therefore separates the two, provided the spatially uniform forcing is absorbed first. We fit that regression across the network (Section 3.3), test it against the shoreline retreat measured over the same years from digitized coastlines (Section 3.2), and check it without a model along a coast-to-inland transect (Section 3.6). We then ask how much of each cluster's decline the coast accounts for (Section 3.5).

# []{#anchor}2. Study site

Newborough Warren is a coastal sand body on the south-west coast of Anglesey, bounded by the Menai Strait to the south-east and Caernarfon Bay to the west. The back dunes carry a mature Corsican pine plantation (Newborough Forest); the open dune to the east holds the dune slacks and the lake Llyn Rhos-Ddu. The groundwater body is unconfined dune sand over glacial till and bedrock. The site is a National Nature Reserve and part of a Special Area of Conservation.

The Caernarfon Bay shoreline is the only boundary considered here to be eroding. The Menai Strait shore and Llanddwyn Island are treated as non-eroding boundaries and are excluded from the distance coordinate. Retreat along the bay frontage is not uniform: Pye and Blott (2024) record a north-positive to south-negative gradient, with progradation in the north and chronic retreat concentrated at the southern Twyni Penrhos frontage, up to 16.3 m at one profile over 2013--2022. Retreat is also episodic. The Storm Brendan event of early 2020 removed several metres of the dune front in one event (Forgrave, 2020).

The dipwell network and its five behavioural clusters are described in Hollingham (2026a). In brief: C1 Lake Edge rings Llyn Rhos-Ddu; C2 Dune is the open eastern dune; C3 Western Residual is the open dune nearest the western shore; C4 Main Forest and C5 Coastal Forest are under the plantation, C5 on the lowest, most coast-proximal ground.

# []{#anchor}3. Data and methods

## []{#anchor}3.1 Records and the distance coordinate

Monthly water-table levels at the reference wells span April 2005 to February 2026. The data preparation, quality control and well selection are those of Hollingham (2026a). Wells in the 2017 clearfell zone are excluded, because they carry a management forcing that is not coastal (Hollingham, 2026b).

Every quantity in this paper is indexed by one coordinate, *d*: the perpendicular distance from a well to the eroding Caernarfon Bay high-water mark. It is computed within the pipeline (25_coastal_gradient.py) as the minimum distance to a committed coastline polyline (OpenStreetMap mean high water, EPSG:27700), restricted to the west-facing Newborough frontage. A well's distance is therefore to the shoreline that is retreating, not to the nearest water.

## []{#anchor}3.2 Shoreline retreat measured from digitized coastlines

The retreat rate is measured here, not taken from the literature. Shoreline positions were digitized for 2006, 2017, 2021 and 2026 along the bay frontage (40_shoreline_retreat.py). Displacement between two epochs is measured as a signed shore-normal distance at transects spaced along the frontage. A signed measure can see progradation as well as retreat, which a nearest-distance measure cannot: nearest distance is always positive.

Three checks decide whether a rate is reported at all, and the script withholds the rate if any fails. The first is a floor test: the least-eroding transect must not retreat faster than the most active point surveyed independently on the same frontage (Pye and Blott, 2024). A field that did would be measuring a shifted line, not a shoreline. The second is a control: the 2006 shoreline was digitized twice, the second time blind to the first. The two agree to a median of 2.3 m, with 95% of transects within 5.5 m. Displacements smaller than that are not distinguished from digitizing error. The third is a generalization test: the error introduced by representing the digitized line as straight segments must stay within a set tolerance.

The headline is the mean retreat over the common modern frontage from 2006 to 2026, E_c = 2.32 m/yr across 128 transects. That window matches the span of the dipwell record over which the gradient is fitted. It is the rate used to scale the gradient into an event-scale drawdown (Section 4.6).

## []{#anchor}3.3 The gradient regression

**Three quantities, defined once (Figure 1).** The coastal effect is described by three parameters.

-   **δ₀, the coast-edge amplitude** (mm/yr): how much faster the water table deepens at the shoreline than far inland.
-   **L_cg, the inland reach** (m): the distance from the shoreline at which the coastal deepening falls to zero.
-   **c_far, the far-field level** (mm/yr): the trend the fit assigns to wells beyond the reach. It is a nuisance term, not a result (Section 4.3).

The regression is fitted to monthly water-table changes, not to a single trend per well. Each well's monthly series enters with its own fixed effect, each calendar month has its own fixed effect, and a cumulative water-balance covariate absorbs the climate forcing that is common to every well. What remains is a trend that differs from well to well. The coastal term models how that trend depends on distance *d*.

Two shapes are fitted for the coastal term. The first is a linear decline from δ₀ at the shoreline to c_far at the reach L_cg, flat beyond it:

δ(*d*) = δ₀ + (c_far − δ₀) · min(*d*/L_cg, 1).

This is the steady-state Dupuit--Forchheimer expectation for a strip aquifer whose drainage boundary has moved: a drawdown that declines across a finite reach and vanishes beyond it. The second is an exponential decline from δ₀ towards c_far, with L_cg as its e-folding length. It represents a diffusive transient. The two are the steady-state and transient limits of the same drawdown physics. Both are fitted by profile non-linear least squares, and the Akaike information criterion compares them (Akaike, 1974). The full specification is in the Supporting Information, Section S1.

**Why the rate is quoted at 150 m.** No well sits at the shoreline. δ₀ is therefore an extrapolation beyond the network, and the shoreline is also the one place where the two shapes disagree materially. The headline is quoted instead as the fitted deepening rate at 150 m from the shoreline, which is close to the nearest wells and inside the range of well positions.

**Uncertainty is quoted on the well basis.** Consecutive monthly readings within a well are not independent observations. The standard errors from the monthly rows understate the uncertainty and are retained only as the nominal precision of the model. The uncertainty quoted is estimated by refitting the model once per well with that well withheld (a delete-one jackknife over the 61 wells of the headline panel).

## []{#anchor}3.4 Specifications

The headline fit uses only the wells on open ground, whatever their cluster (the forest-free panel), so that canopy-driven drawdown under the plantation cannot contaminate the distance fit. Three further fits test whether the result depends on that choice. The full network includes the forested wells. A canopy-controlled fit adds a canopy × time term to the full network, so that forest cover is controlled explicitly rather than by exclusion. A single-cluster fit uses only C3 Western Residual, the open-dune cluster nearest the shore, with c_far held at the forest-free value because the cluster has no well beyond the reach to fix it. The headline is also refitted under alternative climate covariates and with the season of the year interacting with the coastal term.

## []{#anchor}3.5 How much of each cluster's decline is coastal

The headline fit is applied to each cluster's observed decline in the annual summer minimum. The observed decline is a balanced basis: the slope of the annual cross-well mean of the per-well summer minima, one regression on one annual series. An average of per-well slopes is not used, because the wells' records cover different years and such an average mixes record lengths into the rate. A cluster's coastal term is the mean over its wells of the fitted coastal decline at each well's own distance. A cluster that straddles the reach therefore carries the share of its wells that lie inside it.

## []{#anchor}3.6 A model-free check along a transect

A shore-normal transect runs from a coastal anchor well (CEH22, close to the reference distance) to an inland anchor beyond the fitted reach (NW4) (38_coastal_transect.py). The inland anchor sees the climate but not the coast. Subtracting it from the coastal record removes the common climate signal without a model. The spring (March--May) mean of that difference is regressed on year, with an AR(1) correction and a bootstrap confidence interval. If the boundary is migrating, the difference should grow through time. A static geometric offset or a climate fluctuation would not make it grow.

# []{#anchor}4. Results

## 4.1 The decline to be separated

Hollingham (2026a) reports the decline in the annual summer minimum, all causes together, for each cluster. Fitted to each cluster's centroid, with each well held at its own level, the trends are −11.5 mm/yr at C1 Lake Edge, −14.3 at C2 Dune, −17.5 at C3 Western Residual and −29.1 at C5 Coastal Forest. The trend at C4 Main Forest, −11.5 mm/yr, is not significant (p = 0.362). The decline lies before 2011: refitted from 2011, no cluster has a significant trend.

This paper decomposes the same decline on a different basis (Section 3.5). It uses the slope of the annual mean of the summer minima over the gradient subset, which is the set of wells the gradient is fitted to, with the clearfell-zone wells dropped. The two bases differ in which wells they include and in how they average them. They agree at C1, C2 and C5 (−11.0, −14.6 and −32.0 mm/yr; Table 1). They differ at C3, where Table 1 gives −7.5 mm/yr, and at C4, −6.5 mm/yr. The coastal shares below are shares of the Table 1 basis, because the coastal term is averaged over the same wells. They are not shares of the centroid trends.

## []{#anchor}4.2 The coastal gradient

The water table deepens fastest at the coast (Figure 3). In the forest-free headline fit the water-table trend at 150 m from the shoreline is −26.38 mm/yr relative to the far field (95% CI −33.23 to −19.53, well basis). The effect falls to zero at an inland reach of L_cg = 902 m (95% CI 620 to 1185 m). Extrapolated to the shoreline, δ₀ = −31.28 ± 4.79 mm/yr, more than six standard errors from zero. That reach depends on the years fitted (Section 4.3).

The AIC favours the exponential shape (ΔAIC = −6.0, exponential minus linear). The linear shape is kept as the headline on physical grounds: it is the Dupuit--Forchheimer expectation of a finite reach, beyond which the moved boundary has no influence. The choice matters little where the rate is quoted. At 150 m the two shapes agree to within 1.6 mm/yr; at the shoreline they differ by 9.3 mm/yr.

## []{#anchor}4.3 How robust the gradient is

**Forest cover.** The amplitude does not depend on how the forest is treated. The full network gives δ₀ = −31.58 mm/yr, the canopy-controlled fit −32.26 and C3 Western Residual alone −28.28, against the headline −31.28. The canopy-controlled fit absorbs a separate deepening under pine of −9.0 mm/yr, and leaves the coastal amplitude essentially unchanged. The coastal decline is not the plantation's own drawdown.

**Climate covariate.** Substituting any of the alternative climate covariates leaves δ₀ between −31.4 and −28.6 mm/yr and L_cg between 902 and 1067 m.

**Single wells.** One well carries more leverage than the rest. Withholding CEH3, 176 m from the shore, moves δ₀ by 3.1 mm/yr and the 150 m rate by 2.4 mm/yr, 1.9 times the next-largest single-well shift. That shift lies inside the well-basis error. It reflects a network with few wells close to the shore, not an unstable fit.

**What the far-field level is, and why no climate rate is read from it.** It would be natural to read c_far as the background decline due to climate. It is not one. The regression already removes the climate forcing common to all wells through the water-balance covariate, and a constant drift at every well can be traded against that covariate's own trend over the record: the fit can recover their sum but not each one separately. In plain terms, c_far is whatever is left over once the covariate has taken its share, and how much it takes depends on which years are in the window. Moving the start of the fitting window, with the same wells, moves c_far from −0.3 mm/yr over the full record to +24.0 mm/yr for the window starting in 2014. c_far is therefore reported in the Supporting Information as a nuisance parameter and used nowhere in the attribution.

**Fitting window.** The same sweep tests δ₀ and L_cg. δ₀ stays negative in every window, between −36.9 and −24.0 mm/yr. L_cg does not hold. It falls from about 900 m to about 520 m once the window starts after August 2007, and across the whole sweep it runs from 455 to 904 m. The reach is therefore quoted as that range, not as one value. The coastal amplitude is robust to the window; how far inland it reaches is not (Supporting Information, Section S1.8).

## []{#anchor}4.4 Seasonality

The coastal deepening is steeper in spring but present all year. A season × distance interaction on the forest-free panel (10,909 observations) fits the coastal term as δ(*d*)·*t*·(1 + γ·*S*), with *S* = 1 in March--May. It returns γ = +0.309 ± 0.060 for the linear shape and +0.304 ± 0.059 for the exponential (p \< 0.001 for both). The coastal deepening is thus about 31% faster in spring than in the rest of the year. Outside spring it still runs at about three-quarters of its spring rate. The all-season fit is a season-averaged quantity, not a season-independent one.

## []{#anchor}4.5 How much of each cluster's decline is coastal

Table 1 sets the coastal term against each cluster's observed summer-minimum decline. The coastal share follows how many of a cluster's wells lie within the reach.

-   **C3 Western Residual**, the open dune nearest the shore, has 11 of its 22 wells within the reach. The coast accounts for −7.0 mm/yr of its decline, most of it (93%; 87--102% across the delete-one-well refits). This is the most secure cluster result: C3 is an open-dune cluster, and its wells are in the headline fit.
-   **C5 Coastal Forest** has all four of its wells within the reach. The coast accounts for −17.1 mm/yr, about half of its decline of −32.0 mm/yr. The share rests on four wells and is sensitive to which wells the cluster contains. It is reported as "about half", not as a calibrated share (Section 5.3).
-   **C4 Main Forest** has 3 of its 4 wells in the gradient subset within the reach. The coast accounts for −4.8 mm/yr, about three-quarters of a cluster decline that the record does not resolve from zero.
-   **C1 Lake Edge and C2 Dune**, far inland, carry almost no coastal term: −0.6 mm/yr at C1, from its 1 well inside the reach, and none at C2. Their declines, −11.0 and −14.6 mm/yr, are not explained by the coast. The one C1 well inside the reach, CEH11, is not typical of its cluster. It stands 1.7 km from the nearest other C1 well, and it leaves C1 when the record before 2018 is clustered alone (Hollingham, 2026a).

The decline away from the coast is the main thing this decomposition does not explain. It is not attributed to climate here, because the fit does not isolate a climate rate (Section 4.3). It is discussed in Section 5.5. The full decomposition, with the non-coastal term and the unexplained remainder for every cluster, is in the Supporting Information, Table S2.

**Table 1.** How much of each cluster's summer-minimum decline is coastal (mm/yr; negative = falling water table). Observed: the slope of the annual cross-well mean of the per-well summer minima over the gradient subset (balanced basis). Coastal: the mean over the cluster's wells of the fitted coastal decline at each well's own distance from the shore, at the full-record fit (L_cg = 902 m). Well counts are the gradient subset (clearfell-zone wells dropped; a valid summer-minimum slope required), not the cluster sizes of Hollingham (2026a).

  --------------------- ---- ------ ------- ------- ------------------------
  C1 Lake Edge          7    1819   −11.0   −0.6    negligible
  C2 Dune               22   1565   −14.6   0.0     none
  C3 Western Residual   22   906    −7.5    −7.0    most (93%)
  C4 Main Forest        4    889    −6.5    −4.8    about three-quarters ‡
  C5 Coastal Forest     4    410    −32.0   −17.1   about half †
  --------------------- ---- ------ ------- ------- ------------------------

† Four wells, all within the reach; the share depends on which wells the cluster contains (Section 5.3). ‡ Of a decline the record does not resolve from zero.

## []{#anchor}4.6 Shoreline retreat over the same years

The shoreline retreated throughout the record (Figure 2). Over 2006--2026 the mean retreat across the common modern frontage was 2.32 m/yr, and every transect retreated: the least-eroding retreated at 0.39 m/yr. The rate was similar in each sub-period: 1.81 m/yr over 2006--2017, 2.37 over 2017--2021 and 2.14 over 2021--2026. The retreat is a measured, continuing displacement of the boundary over the whole period in which the gradient is fitted.

The retreat is episodic within those periods. Across the winter of 2019--20, which included Storm Brendan, the median shore-normal displacement was 8.9 m over 202 days, against about 1.3 m that the mean rate would give over that interval. Figure 5 maps the inland drawdown implied by a single event of this kind.

## []{#anchor}4.7 The transect check

Along the CEH22--NW4 transect, the spring coast-to-inland head difference deepened at −27.8 mm/yr over 2010--2023 (bootstrap 95% CI −36.1 to −19.3; AR(1)-corrected; Figure 4). This agrees with the regression's rate of −26.38 mm/yr at 150 m, close to the coastal anchor's own distance. Referencing the coastal well to the inland well removes the common climate signal: the coastal record's ordering through time improves from Spearman ρ = −0.21 for the raw record to −0.79 after referencing. A coast-to-inland difference that grows through time is the signature of a migrating boundary, not of a fixed offset or a climate fluctuation.

# []{#anchor}5. Discussion

## []{#anchor}5.1 Two views of one forcing: an episodic coast and a chronic gradient

The gradient is a chronic, year-on-year deepening; the shoreline retreats in storms. These are not in conflict. A departure of the water table from its mean takes months to decay at this site: the e-folding time is about two months at the fastest-responding cluster and over a year under the forest (Hollingham, 2026c). Every cluster's response is far longer than a storm. The aquifer therefore acts as a low-pass filter on the shoreline. It smooths discrete retreat events into a steady gradient, which is why a steady-state Dupuit--Forchheimer shape describes it. The same hydraulic diffusivity sets the time a boundary change takes to propagate across the reach, of order years to decades (Gerla, 2019).

Figure 5 shows the event view: the inland drawdown implied by a single Brendan-scale retreat, scaled from the fitted gradient through the measured retreat rate. The gradient regression averages many such events into a rate. The two are views of the same forcing, and they agree in scale.

## []{#anchor}5.2 What the independent evidence adds

Three lines of evidence point the same way. The regression finds a deepening that depends on distance from the eroding shore and on nothing else tested: forest cover, the climate covariate, the functional form or any single well. The digitized coastlines show that the boundary moved inland throughout the fitting period, at every transect. The transect shows a coast-to-inland difference that grows through time, without any model. Pye and Blott (2024) independently record chronic retreat at the southern frontage.

None of these, on its own, separates erosion from a slowly varying substrate. A thinner saturated zone near the coast would amplify any forcing there. The test that would resolve this is a cored shore-normal transect, which would give the saturated thickness directly.

## []{#anchor}5.3 C5 Coastal Forest: about half

C5 shows the steepest summer-minimum decline in the network. It lies closest to the shore, on the lowest ground, and all four of its wells in the gradient subset are within the reach. The fitted gradient accounts for about half of its decline. That figure rests on four wells, three reference wells and one extended well with a shorter record, and it moves with which wells the cluster contains. It is reported as "about half", with that caveat, and not as a calibrated share.

Only one of the four, NW9, is under the plantation. It is excluded from the forest-free fit, so it tests the gradient rather than contributing to it (Supporting Information, Section S1.5). The other three, CEH3, NW8 and NW8B, stand on open ground and are in the headline fit. Their decline is in the direction and of the order the gradient predicts at their distance. The remainder is consistent with the thin saturated thickness inferred for C5 (Hollingham, 2026a) and with the maturing canopy, which this record cannot separate.

## []{#anchor}5.4 Sea-level rise works the other way

A rising sea raises the water table at the coast, and the rise decays inland over a comparable reach. The fitted gradient is therefore the net of two opposing coastal processes: erosion lowering the water table and sea-level rise raising it. Sea-level rise of about 4 mm/yr is the UKCP18 near-term central estimate for north Wales. The fitted deepening is therefore a conservative estimate of the erosion component alone.

## []{#anchor}5.5 The decline away from the coast

The coast accounts for little or none of the decline at C1 and C2. Their summer minima fell at −11.0 and −14.6 mm/yr (Table 1). Once the coastal term and the two terms common to every well are removed, −13.0 and −17.2 mm/yr remain unexplained (Supporting Information, Table S2). The common terms add a small rise, so the remainder is a little larger than the decline itself.

This remainder is not attributed to climate here. The regression removes the climate forcing common to all wells through its water-balance covariate, and the far-field level left over depends on the years fitted (Section 4.3).

Three facts limit what the remainder can be. It is network-wide: it appears at the lake edge and in the open dune alike. It lies before 2011: refitted from 2011, no cluster has a significant summer-minimum trend (Hollingham, 2026a). And the water balance shows no matching change. Over the well record the summer balance trends at −4.19 mm/yr and the winter balance at +3.74 mm/yr; neither separates from zero, and their annual sum is flat (+1.10 mm/yr). Potential evapotranspiration does rise, by 1.96 mm/yr over the same years, and the rise is long-standing: 0.32 mm/yr over 1931--2025 (Hollingham, 2026d).

Two routes stay open. Rising summer evaporative demand acts through the model's draw term. A change in how rain falls within a month, which a monthly model cannot see, would show only as a fall in recharge sensitivity. A driver that has risen steadily, as evaporative demand has, does not by itself explain a decline confined to the years before 2011. This paper does not choose between the routes.

The coastal term behaves differently. It is a difference between wells, not a level, and the transect shows it still growing over 2010--2023 (Section 4.7). What this paper establishes is the prior step: near the western shore, the coastal part has to be removed first. A climate attribution that skipped it would overstate the climate effect at exactly the wells where the decline is steepest.

## []{#anchor}5.6 Limitations

The network has few wells within 300 m of the shore, so the coast-edge amplitude leans on a small number of wells; this is why uncertainty is quoted on the well basis and CEH3's leverage is reported. A single amplitude is fitted along a frontage whose retreat is not uniform (Pye and Blott, 2024), so δ₀ is a frontage average. The distance coordinate is to the mean high-water line, which is not necessarily the hydraulic boundary; the two need not move together. And, as Section 5.2 sets out, the analysis cannot on its own separate erosion from a substrate that thins towards the coast.

## []{#anchor}5.7 The method beyond Newborough

The method needs a dipwell network with a spread of distances from an eroding shore, a record long enough for per-well trends, and the shoreline's position at two or more dates. It uses no hydraulic conductivity and no aquifer thickness: the reach is fitted from the trends, not computed from aquifer properties. It separates a migrating-boundary drawdown from climate wherever the two act together, and it gives a site an estimate of how far inland its coast is drawing the water table down.

# []{#anchor}6. Conclusions

1.  At Newborough Warren the water table deepens fastest at the eroding coast, by about 26 mm/yr at 150 m from the shoreline relative to wells further inland. The effect reaches 455 to 904 m inland, depending on the years fitted.
2.  The result is not an artefact of forest cover, the climate covariate, the functional form or any single well.
3.  The shoreline retreated at 2.3 m/yr over the same years, measured from digitized coastlines, and a model-free transect shows the coast-to-inland difference growing at the rate the regression predicts.
4.  Coastal retreat accounts for most of the decline in the open dune nearest the shore and about half in the coastal forest. It accounts for none of the decline far inland. That decline lies before 2011, and neither the coast nor the climate covariate explains it.
5.  The fitted far-field level is not a climate rate. Separating the coast first is a precondition for any climate attribution near this shore, not a substitute for one.

# []{#anchor}Figures

![](Pictures/0.png){width="6.29921in" height="2.6274347285431574in"}

**Figure 1.** The three coastal-retreat quantities, defined on a long-section from the eroding Caernarfon Bay shoreline inland to the fitted reach. The coastal water table (solid) is the fitted coast-edge trend accumulated over twenty years, declining linearly to zero at L_cg; the undisturbed table (dotted) is the same surface without it. δ₀ is the deepening rate at the shoreline, an extrapolation beyond the nearest well; the headline rate is read at 150 m. c_far is not drawn: it is a nuisance parameter, not a rate. The ghosted wedges at the shore mark the shoreline positions implied by the measured 2019--20 storm winter (8.9 m; Section 4.6) and by five and twenty years of the mean retreat rate. Schematic, built from the fitted parameters; vertical scale exaggerated. (Source: 09g_coastal_vs_climate_reach.png; parameters from 25_01_panel_fit_parameters.csv.)

![](Pictures/1.png){width="6.29921in" height="3.453426842531189in"}

**Figure 2.** Shoreline retreat along the Caernarfon Bay frontage, measured as signed shore-normal displacement between the digitized coastlines of 2006, 2017, 2021 and 2026. (Source: 40_01_alongshore_profile.png.)

![](Pictures/2.jpg){width="5.11811in" height="3.5843263952764763in"}

**Figure 3.** The coastal gradient: per-well summer-minimum trend against distance to the eroding shoreline, with the forest-free, full-network and C3-only linear fits and the forest-free exponential fit. (Source: 25_05a_gradient_fits.jpg.)

![](Pictures/3.jpg){width="5.90551in" height="3.662431144590128in"}

**Figure 4.** The model-free check: the spring coast-to-inland head difference (CEH22 minus NW4) against year, with its AR(1)-corrected trend. (Source: 38_coast_inland_difference.jpg.)

![](Pictures/4.png){width="6.29921in" height="4.285888635896953in"}

**Figure 5.** The episodic view: water-table drawdown contoured inland from the dune front for a single storm retreat event, over the fitted reach. The per-event edge drawdown is scaled from the chronic gradient through the measured retreat rate E_c. The event is the measured 2019--20 winter median displacement, 8.9 m (Section 4.6). (Source: 20_coastal_erosion.png; parameters from 25_report_numbers.csv and 40_report_numbers.csv.)

# []{#anchor}Supporting Information

The Supporting Information gives the full specification of the gradient regression, its parameter table, the model selection, the C5 out-of-sample test, the seasonal tests, the single-well leverage and the sensitivity to the fitting window, with Figures S1 and S2 (S1); the full cluster decomposition, with the non-coastal term and the unexplained remainder (S2); and the shoreline digitizing with its three checks (S3).

# []{#anchor}Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work the author used Anthropic's Claude (successive Claude Opus and Claude Fable models, accessed through the Claude desktop application) for substantial drafting and editing of the manuscript text: composing prose from the author's analytical outputs and decisions, structuring and restructuring sections, and correcting the text against the study's committed analytical outputs. The conception and design of the study, the twenty-one-year manual dipwell record on which it rests, the analytical decisions, and the interpretation of the results are the author's own. Numerical values in the manuscript were verified against the committed outputs of the analysis pipeline, and a decision log records the methodological and editorial calls made by the author during the work. After using this tool the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

# []{#anchor}References

Akaike, H. (1974) A new look at the statistical model identification. *IEEE Transactions on Automatic Control* 19(6), 716--723. doi:10.1109/TAC.1974.1100705

Fetter, C.W. (2001) *Applied Hydrogeology* (4th ed.). Upper Saddle River, NJ: Prentice Hall.

Forgrave, A. (2020) Dramatic pictures show the beautiful little corner of North Wales that's fast being lost to the sea. *North Wales Live / Daily Post*, 22 January 2020.

Gerla, P.J. (2019) Monitoring and modeling the effect of agricultural drainage and recent channel incision on adjacent groundwater-dependent ecosystems. *Water* 11(4), 863. doi:10.3390/w11040863

Hollingham, M. (2026a) Dune-aquifer architecture from manual dipwell records: clusters, coefficients and storage at Newborough Warren. *In preparation.*

Hollingham, M. (2026b) Hydrological response of a coastal dune aquifer to plantation clearfell and dune scraping: a BACI analysis of a 21-year manual record. *In preparation.*

Hollingham, M. (2026c) One model for a dune water table: what a monthly linear-reservoir model fitted to dipwell levels can forecast, and how far to trust it. *In preparation.*

Hollingham, M. (2026d) Hydrogeological Dynamics, Behavioural Clustering and Management Intervention Analysis at Newborough Warren Coastal Sand Dune Aquifer, Wales. Technical report. doi:10.5281/zenodo.19567643

Pye, K. and Blott, S.J. (2024) *Dune rejuvenation AfterLIFE options for Twyni Penrhos, Newborough.* NRW Evidence Report No. 787, 73 pp. Bangor: Natural Resources Wales.

Robins, N.S., Pye, K. and Wallace, H. (2013) Dynamic coastal dune spit: the impact of morphological change on dune slacks at Whiteford Burrows, South Wales, UK. *Journal of Coastal Conservation* 17(3), 473--482. doi:10.1007/s11852-013-0245-4
