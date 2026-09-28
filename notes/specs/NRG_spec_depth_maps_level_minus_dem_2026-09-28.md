# Spec: depth maps drawn as the water level minus the ground (2026-09-28)

**Status:** NOT ADOPTED (Martin, 2026-09-28, after the preview: "areas are showing wet which shouldnt esp in the forest. I prefer how it was"). The depth maps stay as they are. Parked under D-206 until two problems are solved: the LiDAR DEM sits a median 0.23 m above the well ground, and the level drifts to the mean where there are no wells. The preview is notes/findings/depth_preview_summer_min.png.

## The rule this completes (D-206)

Every map that interpolates between the wells uses one of three treatments. Which one depends on what is being mapped.

| What is mapped | Treatment | Why |
|---|---|---|
| A per-well statistic (β, Sy, P_flood, trend slopes, envelope, step changes) | the house piecewise-linear surface, `map_utils.interpolate_surface` | In the leave-one-well-out test (`tools/interp_loo.py`), linear, IDW and kriging all score within about 0.05 of each other. The existing method is kept for continuity, and every map now draws it one way. |
| A statistic with no spatial skill (scrape step, the Script 37 residual, the water-balance residual, R²) | wells alone, with no surface | No interpolator predicts a left-out well better than the network mean. |
| A water level (the summer-minimum depth, winter-maximum depth, MSL5 and dry-spring depth maps) | the level kriged in m OD, with the ground (DEM) subtracted | A level is a head. Heads are built one way (D-205). Kriging the head beats a linear head surface in the test: 0.39 against −0.08 on MSL5, and 0.49 against 0.36 on the median-error score for the summer minimum. |

## The depth maps

| Script | Figure | Level at each well |
|---|---|---|
| 11b | 11b_01 summer minima (report9 Figure 40) | ground − mean summer minimum depth |
| 11b | 11b_02 winter maxima | ground − mean winter maximum depth |
| 26 | 26_msl_5yr_map (Figure 45) | ground + latest MSL5 |
| 33 | 33_dry_spring_depth (both panels) | ground − dry-spring depth |

**Method.** A new function in `utils/water_table.py`, `depth_surface(wells, months, grid_m)`, does four things:

1. It takes the wells' level (m OD) and the months the statistic draws on.
2. It builds the Script 01b system (`recorded_system`), with 01b's selected drift (ordinary kriging) and its mean-state variogram. The anchors are:
   - the sea, at 01b's fitted coastal head;
   - the river, at channel level;
   - Llyn Rhos-Ddu, at its gauged level over the metric's months;
   - the ridge well CEH12, at its measured depth over the metric's months.
3. It kriges the level on a grid at the grid spacing (`config.LEVEL_DEPTH_GRID_M`, proposed 10 m) inside the site outline (D-204).
4. It returns depth = DEM (averaged onto the grid) − level, plus the kriging standard error.

Callers draw that depth with their existing bands. The ridge mask goes: ridges come out deep because they are high, and fall in the deepest band.

**Which months set the anchor heads:** Jun–Sep for the summer minimum; Oct–Mar for the winter maximum; Mar–May of the window years for MSL5; the dry springs for Script 33.

**What doesn't move:** no per-well value, CSV number or count changes; only the drawn surfaces change. Captions change: report9 Figures 40 and 45, the 11b_02 and 33 captions, report8 §3.8, and Methods Supplement S.7.

**Risk:** CEH12, the ridge well, predicts badly when it is left out (a 24 m error), because nothing near it constrains the ridge. D-205 keeps it as a boundary for the same reason. The map at the ridge is drawn from CEH12 itself.
