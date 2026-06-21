# Paper 1 — figure source files

*Per-paper figure provenance for Hollingham (2026), aquifer-characterisation framework. Keyed on the source pipeline filename. Class ∈ {measured, modelled, illustrative}.*

**Traceability status (2026-05-31): all 18 figures trace to existing pipeline outputs.** Fig 5 now uses the Script 05 affinity map (decision 2026-05-31).

*Verified against the live `outputs/` tree on `main`. Manuscript captions do not carry the source filename (Paper 1 does not follow the report's "(`file.png`)" convention); the mapping below is the authoritative provenance record.*

| Paper 1 Fig | media/ file | Source pipeline file | Script | Topic | Class |
|---|---|---|---|---|---|
| 1 | fig01_site.jpg | `12_01_dem_site_overview.png` | 12 | Site topography, geology & monitoring network | measured |
| 2 | fig02_climate.jpg | `00_01_climate_timeseries.png` | 00 | Climate forcing — P, PET, cumulative surplus | measured |
| 3 | fig03_warming.jpg | `00_03_summer_warming_trend.png` | 00 | Post-2013 summer warming | measured |
| 4 | fig04_dendro.jpg + fig04b_validation.jpg | `02_01_dendrogram.png` + `02_02_validation_plots.png` | 02 | Ward's dendrogram + dual-metric k-selection | modelled |
| 5 | fig05_clustermap.jpg (re-stage from `05_pear_01`) | `05_pear_01_spatial_confidence_map.png` | 05 | Membership-affinity map: best-match cluster + confidence | modelled |
| 6 | fig06_hydrographs.jpg | `02_03_cluster_hydrographs_wb.png` | 02 | Cluster-centroid hydrographs & amplitudes | measured |
| 7 | fig07_waterbal.jpg | `16_water_bal_bar_ms.png` | 16 | Water-balance decomposition by cluster | modelled |
| 8 | fig08_sy.jpg | `18_wtf_02_spatial_sy_map.png` | 18 | Interception-corrected WTF specific-yield surface | modelled |
| 9 | fig09_nse.jpg | `08_lcsc_02_r2_improvement_map.png` | 08 | SSM-over-TLM iterative NSE gain | modelled |
| 10 | fig10a_datum.jpg + fig10b_datumgain.jpg | `03_09_well_optimal_datums.png` + `03_10_well_r2_gain_map.png` | 03 | Per-well optimal drainage datum + R² gain over 3.7 m | modelled |
| 11 | fig11a_b1.jpg + fig11b_b2.jpg + fig11c_b3.jpg + fig11d_r2.jpg | `07_coeff_01_beta1_recharge.png`, `07_coeff_02_beta2_atm_draw.png`, `07_coeff_03_beta3_drainage.png`, `07_coeff_04_r2_quality.png` | 07 | SSM coefficient atlas (β₁ / β₂ / β₃ / R²) | modelled |
| 12 | fig12_tau.jpg | `18_wtf_05_drainage_timescale_map.png` | 18 | Drainage timescale τ = Sy/β₃ | modelled |
| 13 | fig13_synth.jpg | `18_wtf_06_aquifer_diagnostic_synthesis.png` | 18 | Aquifer diagnostic synthesis (τ vs ΔNSE, sized by Sy) | modelled |
| 14 | fig14_head.jpg | `20_head_surface_streams.png` | 20 | Mean head surface + normalized Darcy vectors | modelled |
| 15 | fig15_residual.jpg | `20_residual_ssm.png` | 20 | SSM water-balance residual field | modelled |
| 16 | fig16_gradient.jpg | `25_05_fit_diagnostic.jpg` | 25 | Coastal-retreat gradient (a) + per-cluster decomposition (b) | modelled |
| 17 | fig17a_forest.jpg | `20_drawdown_propagation_nohead.png` | 20 | Forest-interception drawdown reach | illustrative |
| 18 | fig17b_coastal.jpg | `20_coastal_erosion.png` | 20 | Episodic coastal-retreat reach | illustrative |

## Fig 5 — resolved

Fig 5 now uses `05_pear_01_spatial_confidence_map.png` (Script 05), the per-well best-match-cluster map, which also carries the Core/Fuzzy/Spy confidence tiers and multi-cluster-affinity flags discussed in §4 and §5.1. Two follow-through steps in the manuscript (not yet applied): re-stage the figure from this PNG in place of the current core-assignments render, and widen the caption from "spatial distribution of the five clusters" to describe the affinity/confidence content.

## Corrections to the prior pass

- **Fig 10** is Script **03**, not 07 — `03_09_well_optimal_datums.png` (datum) and `03_10_well_r2_gain_map.png` (R² gain), both present in `outputs/03_state_space_model/`. Underlying data: `03_08_datum_sensitivity.*`, `03_09_well_datum_sensitivity.csv`.
- **Fig 16** is the single Script 25 file `25_05_fit_diagnostic.jpg` (both panels) — earlier "missing panel a" flag withdrawn.
- **Captions carry no source filename** (all 18). If you want the report's "(`file.png`)" convention here, the Source-pipeline-file column is exactly what each caption's closing parenthesis would hold.
- **Orphan note:** a full sweep needs the report's and Paper 2's figure lists alongside this. `20_slope_gradient.png` (Script 20) is unused in Paper 1 — check report/Paper 2 before calling it an orphan.
