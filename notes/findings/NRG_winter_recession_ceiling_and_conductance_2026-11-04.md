# The winter recession is a ceiling, and Model A's conductance is nearly uniform (2026-11-04)

Chat "Paper M editing", holding `doc:PaperM`. Martin asked why neither result is cited.
Everything below is recomputed from committed outputs today; no script was run and no
number in any document was changed.

## 1. Neither is cited, and the asymmetry is odd

`grep` over `docs/**/*.md`: the word conductance does not appear anywhere in the corpus.

The winter-recession estimate **is** cited — but only in the report (Table 6 and §4.2.3,
`Rec_drain_frac`). **Paper M does not mention it at all.** Paper M §5.6 says the split is
settled only by "an independent flux measurement, from tracers, outflow gauging or eddy
covariance", and quotes 68 % against 45 % from the two model forms alone. The project holds
a third estimate that needs neither a flux measurement nor a specific yield, and the paper
that is about the split does not report it while its companion report does.

## 2. The winter estimator is a CEILING, and the bias is measurable

`compute_recession_partition` (Script 16, src/16_water_bal.py:357) sets
`drain_frac = winter_rate / summer_rate`, winter Nov–Feb and summer Jun–Sep, on the
assumption that winter recession is drainage only. The ratio is Sy-free, which is why the
paper's §5.4 reasoning prefers it.

It is **biased high**, for a reason that needs no model: drainage rises with head, and winter
heads are higher than summer heads, so winter drainage exceeds summer drainage and the ratio
charges too much of the summer loss to drainage. Under a head-proportional law the factor is
(z₀ + h̄_winter)/(z₀ + h̄_summer). From `outputs/03_regional_averages.csv` (80–84 months each
season) with z₀ = 3.7 m:

| cluster | h̄ winter | h̄ summer | bias | Rec | Rec ÷ bias |
|---|---|---|---|---|---|
| C1 Lake Edge | −0.076 | −0.709 | 1.212 | 0.598 | 0.493 |
| C2 Dune | −0.230 | −0.807 | 1.200 | 0.348 | 0.290 |
| C3 Western Residual | −0.521 | −1.047 | 1.198 | 0.664 | 0.554 |
| C4 Main Forest | −1.203 | −1.510 | 1.141 | 0.507 | 0.444 |
| C5 Coastal Forest | −1.005 | −1.348 | 1.146 | 0.726 | 0.633 |

The bias is 1.14–1.21 across five clusters — near-uniform, which makes the correction cheap
to state. The *direction* holds under any monotone drainage law; only the size needs one.

**With §2.4's floor this brackets the split with no flux measurement**, which is more than
§5.6 currently claims is possible. Floor share = `P_minus_PET_mm_yr / P_net_mm_yr`:

| cluster | floor | ceiling (Rec) | Model A | Model B |
|---|---|---|---|---|
| C1 | 0.267 | 0.598 | **0.851 — above the ceiling** | 0.380 inside |
| C2 | 0.266 | 0.348 | **0.664 — above** | **0.451 — above** |
| C3 | 0.266 | 0.664 | 0.646 inside | 0.564 inside |
| C4 | 0.351* | 0.507 | **0.248 — below the floor** | **0.291 — below** |
| C5 | 0.356* | 0.726 | 0.611 inside | 0.611 inside |

\* the forest floors are not trustworthy: interception removes 214 mm/yr before anything
else and wet-canopy evaporation outruns Thornthwaite PET in midwinter, which is exactly the
exception §2.4 already names. Read C4 and C5 as unbounded below.

**The weak link, and why this is not yet publishable as a bound.** The floor is an annual
drainage share of total loss; the ceiling is a drainage share of *summer* losses. Table 6
already treats the four estimators as comparable and the report compares them directly, so
the identification is the corpus's, not new here — but a *bound* needs it to be exact, and
it is not. Closing that is the work, and it is arithmetic on existing outputs, not a new
emit.

## 3. The conductance uniformity is real, robust, and partly definitional

β₃ has units of month⁻¹ and hides Sy inside it (β₃ ≈ K/Sy). K = β₃ · Sy · 1000 is a flux
conductance in mm/month per metre of head. From `03_16_model_b_persistence.csv` (centroid,
full record) and `17_wtf_01_sy_estimates.csv`:

| cluster | β₃(A) | β₃(B) | Sy event | K_A | K_B |
|---|---|---|---|---|---|
| C1 Lake Edge | 0.0885 | 0.3536 | 0.210 | 18.6 | 74.3 |
| C2 Dune | 0.0617 | 0.1666 | 0.270 | 16.7 | 45.0 |
| C3 Western Residual | 0.0620 | 0.1034 | 0.312 | 19.4 | 32.3 |
| C4 Main Forest | 0.0193 | 0.0097 | 0.321 | 6.2 | 3.1 |
| C5 Coastal Forest | 0.0447 | 0.0446 | 0.364 | 16.3 | 16.2 |

Excluding the Main Forest, whose β₃ is not identified on the record (§4.4): **K_A spans
1.19-fold (16.3–19.4), K_B 4.58-fold**; over all five K_B spans 24-fold.

**Robust to the choice of Sy**, which was the open question in the 2026-11-04 handover.
Recomputed on all three estimators in Script 17, four non-forest clusters:

| Sy estimator | K_A range | spread |
|---|---|---|
| `Sy_event_median` | 16.3–19.4 | 1.19× |
| `Sy_rapid_median` | 13.9–19.5 | 1.40× |
| `Sy_OLS_winter` | 18.7–30.6 | 1.64× |

Only `Sy_OLS_winter` loosens it, and through C1 alone (its OLS Sy is 0.346 against an event
median of 0.210). A crude outer envelope from the β₃ bootstrap CI (`03_05_bootstrap_ci.csv`)
crossed with the Sy interquartile range gives C1 10.4–25.7, C2 11.7–22.8, C3 13.9–28.0,
C5 14.4–23.4: all four are consistent with one conductance near 17–19, and Model B's are not
consistent with any single value.

**But it is weaker evidence than it looks, and this is the reason not to lead with it.** At a
datum 3.7 m down, h_disp is 3.0–3.6 m at every cluster — the datum dominates the variation in
head. So K_A ∝ the drainage flux, and four clusters of one dune system under the same rainfall
having similar drainage fluxes is close to what the water balance already requires. The
uniformity is therefore a consistency check, not an independent measurement of conductivity.
Worse, K_A and K_B are not the same quantity: K_A is a conductance to a common datum and K_B a
relaxation conductance to each cluster's own equilibrium, so part of the 24-fold contrast is
definitional. §5.4's existing sentence — the recession constant describes the datum as much as
the aquifer — is the warning against overreading this.

## 4. What this would change, and who decides

Citing the ceiling means amending §5.6's claim that only a flux measurement can close the
split. That is a published claim, so it is Martin's (CLAUDE.md §7). Nothing edited.

Owed if he wants it: reconcile the summer-loss and annual-loss bases of the two bounds;
then a sentence in §2.4 or §5.6, the numbers as fields. The conductance needs a new emit with
Sy uncertainty propagated before it goes in prose at all — the `pipeline` claim holder's job.

Decisions recorded: none.

---

## 5. CORRECTION, same day: it is not a ceiling on the split the paper quotes

**Section 2's "ceiling" does not hold as a bound on the annual drainage share, and the
title of this note overstates it.** Appended rather than substituted (CLAUDE.md §3).
Martin asked for the bound to be cited; working out the basis reconciliation that
Section 2 left owed showed there is no bound to cite.

`compute_recession_partition`'s own docstring says what the ratio is: "Ratio
winter/summer gives drainage fraction of **summer losses**." The quantity Model A and
Model B report (68 % and 45 %) is a drainage share of the mean loss over the whole
record. Reconciling the two bases turns the single bias of Section 2 into two, running
opposite ways:

| | effect on Rec as an estimate of the ANNUAL share |
|---|---|
| winter heads are higher, drainage rises with head | numerator too large — pushes Rec **up** |
| summer months are the highest-loss months | denominator too large — pushes Rec **down** |

Both the numerator and the denominator are inflated relative to their annual means, so
the ratio's error has no determined sign. Section 2's inequality chain does not compose:
`Rec ≥ summer_share` and `annual_share ≥ summer_share` point the same way and bracket
nothing. The direction argument that made the head bias model-free gives no bound once
the basis changes.

A third objection, not in Section 2 at all. `winter_rate` is the mean of the winter
months **in which the level fell**, and those are a selected minority: `N_winter` is 15
to 27 of the record's ~84 winter months (18-32 %), against `N_summer` 50 to 72 (60-86 %).
Nov-Feb is the wet season, so a winter month with a net decline is one in which recharge
happened to be low. The winter rate is therefore drainage less some recharge over the
drier part of the wet season, not drainage alone.

Why the identification looked sound: `16_water_bal_vol_table.csv` multiplies all four
fractions, `Rec_drain_frac` included, by the same annual `P_net_mm_yr` to get
`Drain_mid/lo/hi_mm_yr`, and `Lo_/Hi_drain_frac` are the min and max across them. The
pipeline already treats the four as estimates of one annual quantity. That identification
is an assumption of Script 16's reporting, not an arithmetic result, and Section 2 inherited
it without checking it. **It is still the corpus's treatment and nothing here says Table 6
is wrong** — four estimators with a reported spread is the honest presentation. What cannot
be built on it is a bound.

What survives, and is what went into Paper M v1_42 §5.2: the recession ratio is a **third
estimate** of the split that comes from neither form and needs neither a datum nor a
specific yield, reported with all three limitations above. Section 2's bracket table is
withdrawn; the floor in §2.4 stands on its own, as it did before this note.

Section 3 (the conductance) is untouched by this correction and its conclusion is unchanged:
a consistency check, not a discriminator, and not yet fit for prose.
