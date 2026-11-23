<!-- GENERATED MIRROR of docs/papers/paper_C/PaperC_SI_v1_0.odt — do not edit. source-sha256=0a44c7a2e9bfe335 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

Supporting Information

Hollingham (2026f), Paper C --- *Coastal retreat draws down a dune aquifer: separating shoreline erosion from climate in a 21-year dipwell record*

This Supporting Information gives the methodological detail behind the coastal-retreat analysis of the main text. It is self-contained. Every number in it is read from the committed outputs of the analysis pipeline: Script 25 (25_coastal_gradient.py), Script 38 (38_coastal_transect.py) and Script 40 (40_shoreline_retreat.py). Section S1 carries over, whole, the regression specification first set out in the Supporting Information of the companion characterization paper (Hollingham, 2026a), which now cites this document for it.

# []{#anchor}S1. The coastal-retreat gradient regression

## []{#anchor}S1.1 Specification

The test (25_coastal_gradient.py) is a panel regression of monthly water-table change against perpendicular distance to the eroding Caernarfon Bay shoreline:

*t*~*ij*~ = δ(*d*~*i*~) + α~*i*~ + α~*j*~ + γ · *W*~*ij*~ + ε~*ij*~

where *t*~*ij*~ is the monthly water-table change at well *i* in month *j*; *d*~*i*~ is the well's perpendicular distance from the eroding shoreline; δ(·) is the modelled distance decay; α~*i*~ and α~*j*~ are well and month fixed effects, absorbed by within-well demeaning; *W*~*ij*~ is the cumulative water-balance covariate, the integrated water balance to month *j*, included to absorb the spatially uniform climate forcing; γ is its coefficient; and ε~*ij*~ is the residual.

Two forms are fitted for δ(·):

-   **Linear-capped**: δ(*d*) = δ₀ + (c_far − δ₀) · min(*d*/L_cg, 1). A linear decline from the coast-edge amplitude δ₀ to the far-field level c_far over the inland reach L_cg, flat beyond it.
-   **Exponential**: δ(*d*) = c_far + (δ₀ − c_far) · exp(−*d*/L_cg). A decay from δ₀ at *d* = 0 towards c_far, with L_cg its e-folding length.

Both are fitted by non-linear least squares; the Akaike information criterion compares them (Akaike, 1974). The coastal rate quoted in the main text is the fitted δ at the reference distance of 150 m.

## []{#anchor}S1.2 Nested specifications

-   **Full network**: all open-dune and forested wells of the reference network, less the clearfell-zone wells, which carry a management forcing that is not coastal.
-   **Forest-free** (the headline): the open-dune clusters C1, C2 and C3 only, so that canopy-driven drawdown cannot contaminate the distance fit.
-   **C3-only**: the C3 Western Residual wells only, with c_far held at the forest-free value, because the cluster has no well beyond the reach to fix it.
-   **Canopy-controlled full network**: the full network with a canopy × time term on the land-cover flag, controlling forest cover rather than excluding it. The absorbed canopy coefficient is −9.0 ± 2.4 mm yr⁻¹ (linear-capped): the extra fall of the water table under pine, net of distance to the coast. The canopy-controlled fit is a cross-check, not the headline, and is not compared with the full network on AIC, because the canopy term is absorbed in the within-group step.

## []{#anchor}S1.3 Parameter values

Table S1 gives the fitted parameters (25_01_panel_fit_parameters.csv). The ± values are the fitted standard errors from the monthly rows. They are the nominal precision of the model and are not the uncertainties quoted in the main text, which are on the well basis (S1.7).

**Table S1.** Fitted parameters of the coastal-retreat panel regression. δ₀ and c_far in mm yr⁻¹; L_cg in m; ± one fitted standard error.

  ------------------------- --------------- -------- --------------- ----------- --------------
  Full                      linear-capped   11,982   −31.58 ± 1.94   1005 ± 58   −0.65 ± 0.56
  Full                      exponential     11,982   −41.28 ± 2.54   617 ± 101   +3.21 ± 1.55
  Forest-free               linear-capped   10,909   −31.28 ± 1.97   902 ± 49    −0.30 ± 0.55
  Forest-free               exponential     10,909   −40.59 ± 3.08   498 ± 78    +2.01 ± 1.11
  C3-only (c_far fixed)     linear-capped   4,772    −28.28 ± 2.47   1019 ± 91   −0.30
  C3-only (c_far fixed)     exponential     4,772    −34.92 ± 3.33   640 ± 77    +2.01
  Full, canopy-controlled   linear-capped   11,982   −32.26 ± 1.95   936 ± 49    −0.01 ± 0.56
  ------------------------- --------------- -------- --------------- ----------- --------------

The forest-free linear-capped fit is the headline. Its fitted rate at the reference distance is −26.38 mm yr⁻¹ (fitted standard error 1.45).

## []{#anchor}S1.4 Model selection and the climate covariate

AIC favours the exponential form in every specification: ΔAIC (exponential minus linear-capped) is −6.0 on the forest-free panel, −5.1 on the full network and −9.9 on C3-only. Both forms agree on the sense of the gradient, a coast-edge deepening that decays inland, and on its magnitude where wells exist. At the reference distance the two forest-free forms differ by 1.6 mm yr⁻¹; at the shoreline, by 9.3 mm yr⁻¹.

The linear-capped form is the headline for two reasons. It is the Dupuit--Forchheimer expectation of a finite inland reach. And its far-field level takes the same sign as the observed far-field trend, where the exponential's does not: the exponential returns +2.01 mm yr⁻¹ against an observed far-field trend of −6.35 mm yr⁻¹ over the same window. AIC runs against that choice rather than with it, and this is stated rather than left implicit.

The panel's climate covariate is an undecayed cumulative water balance, and it is not the best-fitting one available. Exponential accumulators of the same series with half-lives from two to twenty-four months, and a forward integration of the site's state-space model, all predict the water table better out of sample. Substituting any of them leaves δ₀ between −31.4 and −28.6 mm yr⁻¹ and L_cg between 902 and 1067 m (25_15_covariate_specification_range.csv). The undecayed form is kept because the covariate is a nuisance term, absorbed by the within-well demeaning: selecting it on predictive fit would put a free parameter into a published estimate. These ranges are the specification uncertainty on δ₀ and L_cg.

## []{#anchor}S1.5 C5 Coastal Forest as an out-of-sample test

The C5 Coastal Forest wells are under canopy and are excluded from the forest-free fit, so they test the gradient without contributing to it. One of them, NW9, 419 m from the shore, declines at −32.7 mm yr⁻¹ (standard error 9.2; p = 0.002, R² = 0.41, 20 years; 25_02_per_well_summer_min_slopes.csv). That decline is steeper than the fitted coast-edge amplitude itself, δ₀ = −31.28 mm yr⁻¹, which is the largest deepening the gradient attributes at any distance. NW9 lies inside the reach, where the gradient's contribution is smaller than δ₀, so distance to the shore cannot account for the whole of its decline. Neither cluster-independent term closes that gap: the trend carried by the cumulative water-balance covariate is +2.95 mm yr⁻¹ and the fitted far-field level −0.30 mm yr⁻¹, and their sum is positive. The remainder is consistent with the thin saturated thickness inferred for C5 (Hollingham, 2026a).

## []{#anchor}S1.6 Seasonal robustness

The regression in the main text uses the annual summer minimum (June--September) as the per-well response. Script 25 repeats it with the annual spring mean (March--May) through the same code path, with strict 3-of-3 monthly completeness. The same forest-free linear-capped fit is applied to both metrics, so any spring--summer difference in the decomposition comes from the response metric, not from a refitted gradient. That is a property of the procedure, not evidence that the gradient is season-invariant; the test below shows that it is not.

A full-panel season × δ(*d*)·*t* interaction (10,909 observations, one model) fits δ(*d*)·*t*·(1 + γ·*S*), with *S* = 1 in March--May. For the linear-capped form γ = +0.309 ± 0.060 (t = 5.16, p \< 0.001); for the exponential, +0.304 ± 0.059 (t = 5.15, p \< 0.001). Both forms reject season-independence and both put γ above zero (25_09_season_interaction_test.csv).

A spring-only refit of the panel points the same way. It loses power, as expected, with 2,765 observations: the fitted standard error of δ₀ goes from 1.97 to 3.72 mm yr⁻¹. But it returns a steeper spring coast-edge amplitude than the all-season fit, δ₀ = −34.06 against −31.28 mm yr⁻¹, with L_cg 894 against 902 m. At the reference distance the two are closer still: −25.87 against −26.38 mm yr⁻¹.

The boundary effect itself is year-round. C5 declines in both seasons: −32.0 mm yr⁻¹ in the summer minimum and −23.9 in the spring mean (balanced basis; 25_08_spring_vs_summer_comparison.csv). So γ modulates the drift rather than switching it off outside spring. Applying the all-season gradient unchanged to a spring metric understates the spring coastal contribution: the 71% of C5's spring decline that it attributes to coastal retreat is a lower bound.

## []{#anchor}S1.7 Single-well leverage and the well-basis uncertainty

The forest-free panel has few wells close to the shore, so δ₀ can lean on single near-shore wells. Script 25 refits the headline specification once per well with that well withheld, over the 61 wells of the panel, holding the starting values, bounds and climate covariate fixed (25_16_delta0_leave_one_out.csv). A withhold-nothing control reproduces the headline fit exactly.

The largest shift is from CEH3, 176 m from the shore: withholding it moves δ₀ by +3.1 mm yr⁻¹ and the rate at the reference distance by +2.4 mm yr⁻¹. The next-largest shifts in δ₀ are from WMC2 (−1.7), CEH22 (−1.4), D25 (+1.4) and CEH39 (+1.0); no other well moves δ₀ by more than 1 mm yr⁻¹.

The standard error estimated from the refits is the delete-one jackknife, √((*n*−1)/*n*·Σ(δ₀,ᵢ − δ̄₀)²). It answers a different question from the fitted standard error, which treats the monthly rows as independent: the jackknife takes the wells as the units of independence. The main text quotes the well basis (25_report_numbers.csv):

-   δ₀ = −31.28 ± 4.79 mm yr⁻¹ (95% CI −40.66 to −21.89);
-   the rate at the reference distance −26.38 ± 3.49 mm yr⁻¹ (95% CI −33.23 to −19.53);
-   L_cg = 902 ± 144 m (95% CI 620 to 1185);
-   c_far = −0.30 ± 1.46 mm yr⁻¹ (95% CI −3.15 to +2.56).

The leverage of CEH3 lies inside the well-basis error.

# []{#anchor}S2. The full cluster decomposition

Table S2 gives the decomposition from which the main text's Table 1 is drawn. The non-coastal term is the same at every cluster: the trend the cumulative water-balance covariate carries over the fitted span, plus the fitted far-field level. Unexplained is the observed decline minus the coastal and non-coastal terms. The delete-one range is the coastal share across the refits of S1.7, which move δ₀ and L_cg together.

**Table S2.** Decomposition of each cluster's summer-minimum decline, mm yr⁻¹ (negative = falling water table). Observed: balanced basis, the slope of the annual cross-well mean of the per-well summer minima. Source: 25_03_cluster_partition.csv and 25_08_spring_vs_summer_comparison.csv.

  --------------------- ------- ------- ------- ------- ------- ---- ---------
  C1 Lake Edge          −11.0   −0.6    +2.95   −0.30   −13.0   5    3--8
  C2 Dune               −14.6   0.0     +2.95   −0.30   −17.2   0    --
  C3 Western Residual   −7.5    −7.0    +2.95   −0.30   −3.2    93   87--102
  C4 Main Forest        −6.5    −4.8    +2.95   −0.30   −4.3    74   58--91
  C5 Coastal Forest     −32.0   −17.1   +2.95   −0.30   −17.6   53   50--57
  --------------------- ------- ------- ------- ------- ------- ---- ---------

The unexplained remainder is of the same order as the coastal term at C5, which rests on four wells. That is why the main text reports C5's coastal share as "about half" and not as a calibrated attribution.

**Why the far-field level is not a climate rate.** The far-field level c_far is statistically separable from the covariate: its variance inflation factor against the covariate, on the within-well demeaned design, is 1.01. It is not interpretively separable. A constant drift at every well trades off against the covariate's own trend over the panel's span, so only their sum is recovered. Its value therefore depends on the window. Moving the start of the window with the well set held fixed (25_12_window_sweep.csv) takes c_far from −0.30 mm yr⁻¹ over the full record to +23.96 for the window from February 2014. Fitted in rolling windows of fixed length (25_13_rolling_window.csv), its standard deviation across windows is 13.1 mm yr⁻¹ for ten-year windows and 4.6 for eighteen-year windows, and it correlates with the covariate's trend in the same window at −0.82 and −0.59. It is a window statistic, not a rate, and the main text uses it in no attribution.

# []{#anchor}S3. Shoreline retreat from digitized coastlines

## []{#anchor}S3.1 Method

Shoreline positions were digitized for 2006, 2017, 2021 and 2026 along the Caernarfon Bay frontage, with an 1899 shoreline georeferenced from the historical map (40_shoreline_retreat.py). Displacement between two epochs is measured as a signed shore-normal distance at transects every 25 m along the frontage. A signed measure can see progradation as well as retreat; a nearest-distance measure, always positive, cannot, and is kept in the outputs only as a labelled comparator.

## []{#anchor}S3.2 The three checks

The script withholds the rate unless all three checks pass.

1.  **Floor.** The least-eroding transect over 2006--2026 must not retreat faster than the most active point surveyed independently on the same frontage (Pye and Blott, 2024). A field that did would be measuring a shifted line, not a shoreline. The least-eroding transect retreated at 0.39 m yr⁻¹.
2.  **Control.** The 2006 shoreline was digitized twice, the second time blind to the first. Across 130 transects the two agree to a median of 2.34 m, with 90% within 5.14 m and 95% within 5.53 m, against a tolerance of 6.0 m (40_03_control.csv).
3.  **Generalization.** The error introduced by representing the digitized line as straight segments must stay within 5.0 m (40_04_generalisation.csv).

## []{#anchor}S3.3 Retreat by epoch

**Table S3.** Mean shore-normal retreat by epoch (m yr⁻¹; positive = retreat), with the least-eroding transect and the number of transects (40_01_epoch_series.csv). The 2006--2026 rate over the common modern frontage is the headline E_c of the main text.

  ------------ --------------- ------ ------- -----
  2006--2017   common modern   1.81   −1.87   131
  2017--2021   common modern   2.37   −0.95   131
  2021--2026   common modern   2.14   −2.16   128
  2006--2026   common modern   2.32   0.39    128
  1899--2006   pair extent     0.64   0.37    120
  ------------ --------------- ------ ------- -----

The sub-periods carry progradation at some transects (a negative least-eroding rate), so the field is not locked to one sign; over the full 2006--2026 span every transect retreated. The 1899 shoreline's georeferencing error, spread over the 1899--2006 interval, is equivalent to 0.06 m yr⁻¹, small beside the century rate.

## []{#anchor}S3.4 The 2019--20 winter

Across the winter of 2019--20, which included Storm Brendan, two coastlines 202 days apart were compared at 139 transects over 3,450 m of frontage. The median shore-normal displacement was 8.9 m (10th to 90th percentile 4.1 to 21.8 m), against 1.3 m that the mean rate would give over the interval. No transect prograded. The median exceeds the control's 95th percentile of 5.5 m, so it is displacement, not digitizing error.

# []{#anchor}S4. References

Akaike, H. (1974) A new look at the statistical model identification. *IEEE Transactions on Automatic Control* 19(6), 716--723. doi:10.1109/TAC.1974.1100705

Hollingham, M. (2026a) A parameter-sparse state-space framework for characterizing coastal dune-aquifer architecture from manual dipwell records. *In preparation.*

Pye, K. and Blott, S.J. (2024) *Dune rejuvenation AfterLIFE options for Twyni Penrhos, Newborough.* NRW Evidence Report No. 787, 73 pp. Bangor: Natural Resources Wales.
