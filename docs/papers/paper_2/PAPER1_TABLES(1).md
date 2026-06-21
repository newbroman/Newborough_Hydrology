# Paper 1 — table source files

*Per-paper table provenance for Hollingham (2026), aquifer-characterisation framework. Keyed on the source pipeline filename.*

**Traceability status (2026-05-31): all 9 tables trace to dedicated pipeline output CSVs.** Table 6 gained its own CSV (`07_coeff_05_cluster_ranges.csv`, Script 07, added 2026-05-31); all others were already emitted directly.

*Verified against the live `outputs/` tree on `main`.*

| Paper 1 Table | Source pipeline file | Script | Content |
|---|---|---|---|
| 1 | `03_03_cluster_mechanistic_coefficients.csv` | 03 | Cluster mechanistic characterization — β₁, β₂, −β₃, LCSC, R² |
| 2 | `16_water_bal_table.csv` | 16 | Mean monthly head-space water balance (m/month) |
| 3 | `16_water_bal_vol_table.csv` | 16 | Indicative annual volumetric water balance (mm/yr) |
| 4 | `17_wtf_01_sy_table.csv` | 17 | Specific yield by cluster, WTF method (per-well data in `17_wtf_well_sy.csv`) |
| 5 | `08_lcsc_04_table3_benchmark_summary.csv` | 08 | SSM (B) vs traditional linear model (A) benchmarking |
| 6 | `07_coeff_05_cluster_ranges.csv` | 07 | Per-well SSM coefficient ranges by cluster |
| 7 | `18_wtf_05_drainage_timescale.csv` | 18 | Characteristic drainage timescale τ = Sy/β₃ (months) by cluster |
| 8 | `10c_forest_zone_correlations.csv`; figure `10c_02_b2_elevation_regression.png` | 10c | Within-forest spatial predictors of per-well coefficients (n = 14) — Pearson r (p) |
| 9 | `25_03_cluster_partition.csv` | 25 | Decomposition of summer-minimum decline into coastal-retreat + climate (mm/yr) |

## Notes

- **Table 6** now has a dedicated CSV: `07_coeff_05_cluster_ranges.csv` (Script 07, added 2026-05-31) — per-cluster min/max of β₁/β₂/β₃ with n, written after `07_coeff_maps_data.csv`. Reproduces the paper's ranges (e.g. C4 β₂ 2.17–3.72, C5 0.88–1.47). Regenerates on the next Script 07 run.
- **Table 8** source is `10c_forest_zone_correlations.csv` (Script 10c), written to the `outputs/` root and already documented in the methods supplement (Table 17 note) and PIPELINE_README. The `INT_`-prefixed path *variable* is cosmetic — the file is a genuine, findable output. Optionally relocate it into `outputs/10c_forest_zone_analysis/` for shelf-consistency, but that would also touch the methods-supplement and README references.
- **Cross-check on numbers.** Pull all tabulated figures live from the CSVs at run time (β₁/β₂/β₃, LCSC, Sy, τ, water-balance partitions, decomposition shares) — several recompute on pipeline reruns.
