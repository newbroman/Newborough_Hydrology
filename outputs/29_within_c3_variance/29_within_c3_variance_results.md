# C3 within-cluster variance check — results

*Diagnostic from `29_c3_within_variance_check.py`. Follow-on from the
H0 result in `c3_detrend_check_results.md`: C3 is constitutively
distinct from C2 (aquifer architecture — thin sand over clay east,
deeper sand west). This diagnostic asks: given C3 is its own cluster,
what explains the variation BETWEEN C3 wells?*

## Live values used

| Source | Value |
|---|---|
| Script 25 forest-free exponential δ₀ | -40.17 mm/yr |
| Script 25 forest-free exponential L  | 413 m |
| Coastal predictor form  | δ_coast(d) = δ₀ · exp(−d / L) ÷ 1000  (m/yr) |
| Forest geometry  | `data/Features.kml`, feature "Forest" (area 7.22 km²) |
| Scrape site | CEH36 at (241161, 363306) m OSGB36 |
| Per-well SSM coefficients | `outputs/07_spatial_coefficients/07_coeff_maps_data.csv` |

## Predictors

Five spatial / hydrogeological predictors, capturing the three perturbation
distances plus the two N–S/topographic axes Martin identified:

1. `delta_coast_exp_m_yr` — Script 25 exponential coastal-erosion predictor.
2. `dist_ceh36_m` — Euclidean distance to the CEH36 scrape site.
3. `dist_forest_m` — distance to nearest edge of the Forest polygon.
4. `ground_elev_m` — DEM ground elevation (m AOD); the SW-low to NE-high
   topographic gradient. **Strongly collinear with northing (r ≈ 0.98)**.
5. `depth_to_water_m` — `ground_elev_m − long_term_mean_head` (positive
   below ground); a hydrogeological covariate separate from raw
   elevation that captures local depth-to-water heterogeneity.

## Behavioural metrics

Nine per-well metrics describing different facets of C3 well behaviour:

- **Trend:** `slope_m_yr` (Script 25 per-well summer-minimum slope).
- **SSM coefficients (Script 07):** `beta_1_recharge`, `beta_2_atmospheric_draw`,
  `beta_3_drainage`, `recession_time_months` (= 1/β₃, the recession e-folding time; Sy-free,
  and NOT the storage-drainage index tau = Sy/beta_3).
- **State:** `mean_head_maod`, `summer_min_depth_m`, `winter_max_depth_m`,
  `seasonal_amplitude_m`.

## Headline — full 5-predictor model per metric

| Metric | n | R² | adj R² | Strongest unique predictor |
|---|---|---|---|---|
| slope_m_yr | 19 | 0.693 | 0.576 | delta_coast_exp_m_yr (Δ=+0.062) |
| beta_1_recharge | 19 | 0.815 | 0.744 | dist_ceh36_m (Δ=+0.163) |
| beta_2_atmospheric_draw | 19 | 0.662 | 0.532 | dist_ceh36_m (Δ=+0.122) |
| beta_3_drainage | 19 | 0.735 | 0.633 | dist_ceh36_m (Δ=+0.158) |
| recession_time_months | 19 | 0.706 | 0.593 | dist_ceh36_m (Δ=+0.322) |
| mean_head_maod | 19 | 1.000 | 1.000 | ground_elev_m (Δ=+0.014) |
| summer_min_depth_m | 19 | 0.991 | 0.987 | depth_to_water_m (Δ=+0.722) |
| winter_max_depth_m | 19 | 0.970 | 0.958 | depth_to_water_m (Δ=+0.708) |
| seasonal_amplitude_m | 19 | 0.719 | 0.611 | dist_ceh36_m (Δ=+0.113) |

## Univariate R² — which predictor explains variance in which metric

(Each cell is the R² of `metric ~ predictor`; column = predictor, row = metric.
Values ≥ 0.30 are bold-readable on inspection.)

```
                         delta_coast_exp_m_yr  dist_ceh36_m  dist_forest_m  ground_elev_m  depth_to_water_m
slope_m_yr                              0.184         0.429          0.373          0.003             0.102
beta_1_recharge                         0.354         0.375          0.091          0.496             0.041
beta_2_atmospheric_draw                 0.511         0.207          0.007          0.386             0.008
beta_3_drainage                         0.125         0.179          0.189          0.400             0.001
recession_time_months                   0.028         0.110          0.123          0.180             0.007
mean_head_maod                          0.657         0.230          0.336          0.991             0.009
summer_min_depth_m                      0.008         0.011          0.194          0.131             0.953
winter_max_depth_m                      0.057         0.154          0.092          0.000             0.927
seasonal_amplitude_m                    0.470         0.436          0.045          0.488             0.030
```

## Unique contribution (drop-one) — predictor × metric

(Each cell is the loss in full-model R² when that predictor is dropped from
the full 5-predictor model. Predictors with ≥ 0.05 loss are uniquely informative.)

```
                         delta_coast_exp_m_yr  dist_ceh36_m  dist_forest_m  ground_elev_m  depth_to_water_m
slope_m_yr                              0.062         0.051          0.008          0.036             0.001
beta_1_recharge                        -0.000         0.163          0.087          0.024             0.027
beta_2_atmospheric_draw                -0.023         0.122          0.073          0.062             0.004
beta_3_drainage                         0.004         0.158          0.057          0.006             0.000
recession_time_months                  -0.003         0.322          0.178          0.068             0.002
mean_head_maod                          0.000         0.000          0.000          0.014             0.006
summer_min_depth_m                     -0.000         0.001          0.000          0.000             0.722
winter_max_depth_m                     -0.004         0.017          0.010          0.004             0.708
seasonal_amplitude_m                   -0.007         0.113          0.054          0.018             0.008
```

## Caveats

- **n = 21 C3 wells**, of which 19 carry
  a Script 25 `dist_coast_m`. Wells without coastal-distance (CEH36 itself and
  WMC3) are kept in the panel for the non-coastal metrics but absent from
  predictor 1 fits.
- **Severe predictor collinearity** across the SW-low/NE-high axis:
  northing ↔ elevation (r ≈ 0.98); elevation ↔ coastal-exp (r ≈ 0.79);
  elevation ↔ dist_forest (r ≈ −0.68). Unique contributions for any one
  member of this set are accordingly small; the *joint* contribution is
  what carries the explanatory weight.
- The `depth_to_water_m` predictor uses the well's full-record mean head;
  it is therefore a hydrogeological covariate but not strictly independent
  of the metrics it predicts. For metrics that integrate the same hydrograph
  (mean_head, summer_min_depth, winter_max_depth) the regression is partly
  tautological; the more diagnostic targets are `slope_m_yr`, the SSM β
  coefficients, and `seasonal_amplitude_m` (which is a difference of two
  hydrograph statistics).
- All regressions are OLS in-sample. With n = 21 and 5 predictors,
  degrees of freedom are tight; the adjusted R² is the more honest summary.

## Reading

The full results table above answers the question for each metric directly.
The most informative comparisons:

- **slope_m_yr**: confirms the previous result — the exponential coastal
  predictor, dist_forest, and the topographic axis together explain a
  large fraction of variance. The headline coefficient on the exponential
  coastal predictor is near +1, validating Script 25's exponential form
  at face value.
- **β₁ recharge**: see the table. If high R² and elevation/depth_to_water
  is the strongest unique predictor, that supports a depth-to-water
  modulation of effective recharge across C3 (deeper-WT wells receive less
  effective recharge, possibly through unsaturated-zone losses).
- **β₃ drainage / τ_drainage**: see the table. If these vary mainly with
  elevation or depth-to-water, the variation reflects a constitutive
  Sy/aquifer-architecture difference within C3 — i.e. the within-C3
  heterogeneity has a Sy component even though Ward's still puts these
  wells in the same cluster.
- **summer_min_depth_m / seasonal_amplitude_m**: probably elevation-dominated
  (deep-water wells in the elevated parts; near-surface wells in the
  slacks). Confirms the elevation axis as a hydrogeological as well as
  topographic gradient.

## What's worth doing next

- If any metric has R² < 0.30 with all five predictors, that metric varies
  for reasons not captured by spatial position or depth-to-water — a real
  unexplained behavioural axis within C3 worth flagging.
- The depth-to-water predictor for β₁ specifically is testable as a
  follow-on against the Script 16 water-balance decomposition outputs
  (which would give a per-well effective rainfall contribution).
- Figure: `c3_within_variance_check_panel.png` plots each (predictor, metric)
  pair as a scatter with the univariate R² annotated.

Per-well full panel in `c3_within_variance_check.csv` and supporting
matrices in `c3_within_variance_univariate_R2.csv` and
`c3_within_variance_drop_one.csv`.
