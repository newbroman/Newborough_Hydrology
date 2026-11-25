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
| 5 | `07_spatial_coefficients/07_coeff_05_cluster_ranges.csv` | 07 | Per-well SSM coefficient ranges by cluster |
| 6 | `10c_forest_zone_correlations.csv` | 10c | Within-forest spatial predictors of per-well coefficients (n = 14) — Pearson r (p) |
| 7 | `14_climate_projections/14_summer_trend_stats.csv` | 14 | Trend in the annual summer minimum by cluster (mm/yr), full record and from 2011 (§4.11; D-343, 2026-11-25; table_gen paper1/Table7) |

The SSM-versus-TLM benchmark table (formerly Table 5) moved to the companion methods paper
on 2026-10-08 (D-244), where it is Paper M Table 1 (`08_model_benchmarking/08_cluster_nse_medians.csv`);
Paper 1 now cites that paper, and its later tables were renumbered 6–9 → 5–8.

The drainage-decay half-life table (Table 6 until 2026-11-18) was removed under D-334 (J-19, T-110): a recession
time at a fixed floor is not a finding, Script 18's CSV had moved to Model B's β₃, and the per-cluster
mean-reversion times are tabulated in Paper M Table 3. The per-well map stays as Paper 1 Figure 14. Tables 7–8
renumbered 6–7.

## Reading the sources

**Table 4 — Approach B only.** Script 17 emits three specific-yield estimators into
this CSV: Approach A (`Sy_OLS_*`), Approach B (`Sy_event_*`) and Approach C, the
rapid-recharge-event method after Crosbie et al. (2005) (`Sy_rapid_*`). Table 4 reports
the **event-median (Approach B)** values only; Approaches A and C appear solely in SI
Section S11. The corrected forest rows are the interception-corrected Approach B
variant.

Note also that two Approach B aggregations exist and are not interchangeable: the
cluster-level event median in `17_wtf_01_sy_estimates.csv`, which is what Table 4
reports, and the median of per-well event estimates in `18_wtf_01_well_sy_estimates.csv`, which is
what the pipeline consumes downstream.

**The half-life table is gone (2026-11-18, J-19, T-110, D-334).** Its source column was
`half_life_months` in `18_wtf_spatial/18_wtf_05_storage_drainage_index.csv`, never
`storage_drainage_index_months` (the storage-weighted composite τ = Sy/β₃). The per-well map that
remains, Paper 1 Figure 14, reads the same column; §4.7 says what the timescale is and is not.

**Table 6** — `10c_forest_zone_correlations.csv` is written to the `outputs/` root
rather than a per-script subdirectory. The `INT_`-prefixed path *variable* is cosmetic;
the file is a genuine, findable output.

**Table 7** — the well counts are the gradient-analysis subset (clearfell-zone wells
dropped; a valid summer-minimum slope required), not the cluster sizes of Table 1.

## Cross-check on numbers

Pull all tabulated figures live from the CSVs — β₁/β₂/β₃, LCSC, Sy, t½,
water-balance partitions and decomposition shares all recompute on pipeline reruns.
`audit_number_drift.py` diffs the committed CSVs between two commits and flags values a
document still prints, which catches drift but not renamed files or columns; those need
checking by hand against the paths above.

The coastal decomposition table (Table 7 until 2026-11-24) went to Paper C with the coastal material (J-29). Table 7
is now §4.11's summer-minimum trends (D-343, 2026-11-25).
