# Interpolator test for the per-well maps: leave-one-well-out (2026-09-28)

This note answers Martin's proofread question: should the per-well maps be kriged, as the water table is under D-205? The tool is `tools/interp_loo.py` (1.0.0) and the results are in `NRG_interp_loo_2026-09-28.csv`.

**Method.** Each well is dropped in turn and predicted from the others. Four methods are compared:

- **mean**: the no-skill baseline.
- **linear**: what `map_utils.add_idw_surface()` draws. It is Delaunay piecewise-linear with nearest fill outside the hull, despite the function's name.
- **idw2**: inverse-distance weighting, as in Script 32.
- **ok**: ordinary kriging, with a spherical variogram refitted in every fold and the Script 01b bins and lag.

The depth-type maps get two more rows, `linear_head` and `ok_head`. These interpolate the level in maOD and then subtract each well's ground elevation.

**Scores.** Skill is 1 − MSE/MSE(mean). A second score uses the median absolute error, so that one badly predicted well cannot dominate it.

## Result

**1. Where a surface has skill, no method wins.** The metrics are β₁, β₂, β₃, Sy, P_flood, the differential slopes, the envelope swing and amplification, and the summer-minimum depth. On these the three interpolators score between 0.5 and 0.8, and within about 0.05 of each other:

- kriging leads on β₁, β₃, Sy and the envelope swing;
- linear leads on β₂, P_flood, the differential slopes and the amplification;
- IDW leads on MSL5 and the summer-minimum depth.

Kriging does not earn a switch on these metrics.

**2. Four surfaces have no skill.** For each, no method predicts a well better than the network mean, or only barely:

| Map | Script | Linear | IDW | OK | Nugget share |
|---|---|---|---|---|---|
| Scrape step, climate-corrected | 10b | −0.33 | −0.15 | −0.11 | 0.83 |
| Driver residual 2005–2025 | 37 | −0.56 | −0.20 | −0.05 | 1.00 |
| Water-balance residual | 20 | −0.11 | 0.11 | 0.13 | 0.38 |
| R² | 07(a) | 0.00 | 0.19 | 0.12 | 0.25 |

Any spatial pattern drawn between the wells on these maps is not supported by the wells. The clearfell step (10b fell_step_cc) does have modest skill, 0.33–0.37.

**3. The level route for the depth maps is mixed.**

- **MSL5:** `ok_head` scores 0.39 on the mean-square measure and 0.55 on the median measure, against 0.53 and 0.48 for kriging the depth directly.
- **Summer-minimum depth:** the level route is ruined by the ridge well CEH12, whose ground stands 20 m above its neighbours; one prediction is off by 24 m. On the median measure it scores 0.49, level with the direct surfaces.
- **Limits of the test:** it scores only at the wells. The level route's real advantage would lie between the wells, where a surface drawn against the 2 m DEM follows the slacks without needing a ridge mask. A leave-one-well-out test cannot see that.

**Caveat.** Every score is taken at the wells. The test says nothing about how plausible a surface looks between them.
