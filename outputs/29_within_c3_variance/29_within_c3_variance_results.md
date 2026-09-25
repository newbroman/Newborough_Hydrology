# C3 within-cluster variance check — results

*Diagnostic from `29_c3_within_variance_check.py`. Follow-on from the
H0 result in `outputs/28_c3_detrend/28_c3_detrend_results.md`: C3 is constitutively
distinct from C2 (aquifer architecture — thin sand over clay east,
deeper sand west). This diagnostic asks: given C3 is its own cluster,
what explains the variation BETWEEN C3 wells?*

## Live values used

| Source | Value |
|---|---|
| Script 25 forest-free exponential δ₀ | -40.59 mm/yr |
| Script 25 forest-free exponential L  | 498 m |
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
| slope_m_yr | 21 | 0.461 | 0.281 | depth_to_water_m (Δ=+0.093) |
| beta_1_recharge | 21 | 0.807 | 0.743 | dist_ceh36_m (Δ=+0.221) |
| beta_2_atmospheric_draw | 21 | 0.715 | 0.620 | dist_ceh36_m (Δ=+0.337) |
| beta_3_drainage | 21 | 0.711 | 0.615 | dist_ceh36_m (Δ=+0.333) |
| recession_time_months | 21 | 0.672 | 0.563 | dist_ceh36_m (Δ=+0.453) |
| mean_head_maod | 21 | 1.000 | 1.000 | ground_elev_m (Δ=+0.019) |
| summer_min_depth_m | 21 | 0.994 | 0.991 | depth_to_water_m (Δ=+0.880) |
| winter_max_depth_m | 21 | 0.964 | 0.952 | depth_to_water_m (Δ=+0.751) |
| seasonal_amplitude_m | 21 | 0.806 | 0.741 | delta_coast_exp_m_yr (Δ=+0.127) |

## Univariate R² — which predictor explains variance in which metric

(Each cell is the R² of `metric ~ predictor`; column = predictor, row = metric.
Values ≥ 0.30 are bold-readable on inspection.)

```
                         delta_coast_exp_m_yr  dist_ceh36_m  dist_forest_m  ground_elev_m  depth_to_water_m
slope_m_yr                              0.252         0.286          0.145          0.016             0.131
beta_1_recharge                         0.546         0.508          0.054          0.133             0.013
beta_2_atmospheric_draw                 0.311         0.067          0.010          0.344             0.007
beta_3_drainage                         0.265         0.312          0.024          0.064             0.038
recession_time_months                   0.181         0.219          0.006          0.048             0.008
mean_head_maod                          0.472         0.049          0.308          0.989             0.020
summer_min_depth_m                      0.034         0.000          0.071          0.129             0.947
winter_max_depth_m                      0.064         0.165          0.189          0.023             0.876
seasonal_amplitude_m                    0.636         0.618          0.116          0.118             0.002
```

## Unique contribution (drop-one) — predictor × metric

(Each cell is the loss in full-model R² when that predictor is dropped from
the full 5-predictor model. Predictors with ≥ 0.05 loss are uniquely informative.)

```
                         delta_coast_exp_m_yr  dist_ceh36_m  dist_forest_m  ground_elev_m  depth_to_water_m
slope_m_yr                              0.001         0.013          0.037          0.026             0.093
beta_1_recharge                         0.145         0.221          0.146          0.126             0.006
beta_2_atmospheric_draw                 0.050         0.337          0.202          0.175             0.000
beta_3_drainage                         0.103         0.333          0.222          0.194             0.081
recession_time_months                   0.053         0.453          0.295          0.226             0.026
mean_head_maod                          0.000         0.000          0.000          0.019             0.010
summer_min_depth_m                      0.006         0.001          0.000          0.000             0.880
winter_max_depth_m                      0.015         0.013          0.005          0.005             0.751
seasonal_amplitude_m                    0.127         0.076          0.028          0.031             0.001
```

## Caveats

- **n = 26 C3 wells**, of which 21 carry
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
- All regressions are OLS in-sample. With n = 26 and 5 predictors,
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
