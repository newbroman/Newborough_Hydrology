# Paper 1 — table source files

*Per-paper table provenance for Hollingham (2026), aquifer-characterisation framework.
Keyed on the source pipeline filename.*

**Regenerated 2026-07-24 directly from the "Source data" block of `Paper1.pdf` at
commit `938fa34`,** so the two agree by construction. This file is the durable
traceability record: the paper's own Source data block is marked "for review only —
to be removed at production", after which this document is the only mapping.

*Paths are relative to `outputs/`, or to `config.py` / `data/` where noted.*

| Paper 1 Table | Source pipeline file | Script | Content |
|---|---|---|---|
| 1 | `03_state_space_model/03_03_cluster_mechanistic_coefficients.csv` | 03 | Cluster mechanistic characterisation — β₁, β₂, −β₃, LCSC, R² |
| 2 | `16_water_balance/16_water_bal_table.csv` | 16 | Mean monthly head-space water balance (m/month) |
| 3 | `16_water_balance/16_water_bal_vol_table.csv` | 16 | Indicative annual volumetric water balance (mm/yr) |
| 4 | `17_wtf_specific_yield/17_wtf_01_sy_estimates.csv` | 17 | Specific yield by cluster, WTF method — **event-median (Approach B)**; per-well data in `17_wtf_well_sy.csv` |
| 5 | `08_model_benchmarking/08_lcsc_04_table3_benchmark_summary.csv` | 08 | SSM (B) vs traditional linear model (A) benchmarking |
| 6 | `07_spatial_coefficients/07_coeff_05_cluster_ranges.csv` | 07 | Per-well SSM coefficient ranges by cluster |
| 7 | `18_wtf_spatial/18_wtf_05_drainage_timescale.csv` | 18 | Drainage decay half-life t½ = ln(2)/β₃ (months) by cluster — **see traceability note below** |
| 8 | `10c_forest_zone_correlations.csv` | 10c | Within-forest spatial predictors of per-well coefficients (n = 14) — Pearson r (p) |
| 9 | `25_coastal_gradient/25_03_cluster_partition.csv` | 25 | Decomposition of cluster summer-minimum decline into coastal-retreat + climate (mm/yr) |

## Notes

- **Table 4 — Approach B only.** Script 17 v1.4.0 emits three specific-yield
  estimators into this CSV: Approach A (`Sy_OLS_*`), Approach B (`Sy_event_*`) and
  Approach C, the rapid-recharge-event method after Crosbie et al. (2005)
  (`Sy_rapid_*`). Paper 1 Table 4 reports the **event-median (Approach B)** values
  only; Approaches A and C appear solely in SI Section S11. The corrected forest
  rows are the interception-corrected Approach B variant.
  Earlier revisions of this file cited `17_wtf_01_sy_table.csv` — that filename does
  not exist; the committed output is `17_wtf_01_sy_estimates.csv`.

- **Table 7 — read the `half_life_months` column.** The paper reports the drainage
  decay half-life **t½ = ln(2)/β₃**, which is specific-yield-independent. Script 18
  v1.7.0 (2026-07-24) emits this directly as `half_life_months`; it reproduces
  Table 7 exactly (min/median/max and n, all five clusters). Take care not to read
  `tau_months` by mistake — that is the **storage–drainage index** τ = Sy/β₃, a
  storage-weighted composite that Paper 1 deliberately does *not* report in Table 7
  (see §4.7, which explains why the half-life is used instead). Both columns are
  retained; only `half_life_months` corresponds to the published table.
  The `drainage_timescale` filename stem is historical and is retained deliberately —
  do not rename it.

- **Table 8** source `10c_forest_zone_correlations.csv` (Script 10c) is written to the
  `outputs/` root rather than a per-script subdirectory. The `INT_`-prefixed path
  *variable* is cosmetic — the file is a genuine, findable output.

- **Cross-check on numbers.** Pull all tabulated figures live from the CSVs at run
  time (β₁/β₂/β₃, LCSC, Sy, t½, water-balance partitions, decomposition shares) —
  several recompute on pipeline reruns.
