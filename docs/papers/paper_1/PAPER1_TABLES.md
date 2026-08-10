# Paper 1 — table source files

*Table provenance for Hollingham (2026), aquifer-characterisation framework.*

This document is the durable traceability record. The paper's own "Source data" block
is marked *for review only — to be removed at production*, after which this is the only
mapping from published table to pipeline output.

*Paths are relative to `outputs/`, or to `config.py` / `data/` where noted. All paths
below verified present in the committed tree.*

| Table | Source pipeline file | Script | Content |
|---|---|---|---|
| 1 | `03_state_space_model/03_03_cluster_mechanistic_coefficients.csv` | 03 | Cluster mechanistic characterisation — β₁, β₂, −β₃, LCSC, R² |
| 2 | `16_water_balance/16_water_bal_table.csv` | 16 | Mean monthly head-space water balance (m/month) |
| 3 | `16_water_balance/16_water_bal_vol_table.csv` | 16 | Indicative annual volumetric water balance (mm/yr) |
| 4 | `17_wtf_specific_yield/17_wtf_01_sy_estimates.csv` | 17 | Specific yield by cluster, WTF method — event-median (Approach B) |
| 5 | `08_model_benchmarking/08_lcsc_04_table3_benchmark_summary.csv` | 08 | SSM (B) vs traditional linear model (A) benchmarking |
| 6 | `07_spatial_coefficients/07_coeff_05_cluster_ranges.csv` | 07 | Per-well SSM coefficient ranges by cluster |
| 7 | `18_wtf_spatial/18_wtf_05_storage_drainage_index.csv` | 18 | Drainage decay half-life t½ = ln(2)/β₃ (months) by cluster |
| 8 | `10c_forest_zone_correlations.csv` | 10c | Within-forest spatial predictors of per-well coefficients (n = 14) — Pearson r (p) |
| 9 | `25_coastal_gradient/25_03_cluster_partition.csv` | 25 | Decomposition of cluster summer-minimum decline into coastal-retreat + climate (mm/yr) |

## Reading the sources

**Table 4 — Approach B only.** Script 17 emits three specific-yield estimators into
this CSV: Approach A (`Sy_OLS_*`), Approach B (`Sy_event_*`) and Approach C, the
rapid-recharge-event method after Crosbie et al. (2005) (`Sy_rapid_*`). Table 4 reports
the **event-median (Approach B)** values only; Approaches A and C appear solely in SI
Section S11. The corrected forest rows are the interception-corrected Approach B
variant.

Note also that two Approach B aggregations exist and are not interchangeable: the
cluster-level event median in `17_wtf_01_sy_estimates.csv`, which is what Table 4
reports, and the median of per-well event estimates in `17_wtf_well_sy.csv`, which is
what the pipeline consumes downstream.

**Table 7 — read the `half_life_months` column.** The paper reports the drainage decay
half-life **t½ = ln(2)/β₃**, which is specific-yield-independent. Do not read
`storage_drainage_index_months` — that is the storage–drainage index τ = Sy/β₃, a
storage-weighted diagnostic composite that Paper 1 deliberately does *not* report in
Table 7 (see §4.7, which explains why the half-life is used instead). Both columns are
present in the file; only `half_life_months` corresponds to the published table.

The half-life is conditional on the 3.7 m displacement datum, since β₃ scales with that
reference. Ratios between clusters are datum-invariant, so the cluster contrasts the
table supports are not affected.

**Table 8** — `10c_forest_zone_correlations.csv` is written to the `outputs/` root
rather than a per-script subdirectory. The `INT_`-prefixed path *variable* is cosmetic;
the file is a genuine, findable output.

**Table 9** — the well counts are the gradient-analysis subset (clearfell-zone wells
dropped; a valid summer-minimum slope required), not the cluster sizes of Table 1.

## Cross-check on numbers

Pull all tabulated figures live from the CSVs — β₁/β₂/β₃, LCSC, Sy, t½,
water-balance partitions and decomposition shares all recompute on pipeline reruns.
`audit_number_drift.py` diffs the committed CSVs between two commits and flags values a
document still prints, which catches drift but not renamed files or columns; those need
checking by hand against the paths above.
