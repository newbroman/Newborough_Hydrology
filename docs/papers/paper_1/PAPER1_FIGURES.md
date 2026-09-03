# Paper 1 — figure source files

*Figure provenance for Hollingham (2026), aquifer-characterisation framework.
Class ∈ {measured, modelled, illustrative}.*

This document is the durable traceability record. The paper's own "Source data" block
cites the underlying **data** files; this document additionally records the **rendered**
artefact that became each figure, which the paper's block does not carry. Manuscript
captions do not name their source file — Paper 1 does not follow the report's
`` (`file.png`) `` convention — so the mapping below is the authoritative record.

*Rendered paths are relative to `outputs/`. All files below verified present in the
committed tree.*

| Fig | Rendered file | Source data file(s) | Script | Topic | Class |
|---|---|---|---|---|---|
| 1 | `12_01_dem_site_overview.png` | `01_locations.csv` (+ DEM/KML in `data/geo/`) | 12 | Site topography, geology & monitoring network | measured |
| 2 | `00_01_climate_timeseries.png` | `01_climate.csv` | 00 | Climate forcing — P, PET, cumulative surplus | measured |
| 3 | `00_03_summer_warming_trend.png` | `00_climate_summary/00_03_summer_warming_stats.csv` | 00 | Post-2013 summer warming | measured |
| 4 | `02_01_dendrogram.png` + `02_02_validation_plots.png` | `02_clustering/02_07_cluster_membership_k5.csv` | 02 | Ward's dendrogram + dual-metric k-selection | modelled |
| 5 | `05_pear_01_spatial_confidence_map.png` | `05_pear_membership_audit.csv`; `01_locations.csv` | 05 | Spatial cluster distribution, Pearson-affinity validation | modelled |
| 6 | `02_03_cluster_hydrographs_wb.png` | `02_clustering/02_09_cluster_amplitude_summary.csv` | 02 | Cluster-centroid hydrographs & seasonal amplitudes | measured |
| 7 | `16_water_bal_bar_ms.png` | `16_water_balance/16_water_bal_table.csv` | 16 | Water-balance decomposition by cluster | modelled |
| 8 | `18_wtf_02_spatial_sy_map.png` | `18_wtf_spatial/18_wtf_01_well_sy_estimates.csv` | 18 | Interception-corrected WTF specific-yield surface | modelled |
| 9 | `08_lcsc_02_r2_improvement_map.png` | `08_model_benchmarking/08_perwell_nse.csv` | 08 | SSM-over-TLM iterative NSE gain | modelled |
| 10 | `03_09_well_optimal_datums.png` + `03_10_well_r2_gain_map.png` | `03_state_space_model/03_09_well_optimal_datums.csv`; `03_state_space_model/03_08_datum_sensitivity.csv` | 03 | Per-well optimal drainage datum + R² gain over 3.7 m | modelled |
| 11 | `07_coeff_01_beta1_recharge.png` | `07_spatial_coefficients/07_coeff_maps_data.csv` | 07 | β₁ recharge-sensitivity surface | modelled |
| 12 | `07_coeff_02_beta2_atm_draw.png` | `07_spatial_coefficients/07_coeff_maps_data.csv` | 07 | β₂ atmospheric-draw surface | modelled |
| 13 | `07_coeff_03_beta3_drainage.png` | `07_spatial_coefficients/07_coeff_maps_data.csv` | 07 | β₃ drainage-rate surface | modelled |
| 14 | `18_wtf_spatial/18_wtf_05_halflife_map.png` | `18_wtf_spatial/18_wtf_05_storage_drainage_index.csv` (`half_life_months`) | 18 | Drainage decay half-life t½ = ln(2)/β₃ | modelled |
| 15 | `18_wtf_spatial/18_wtf_06_aquifer_diagnostic_synthesis.png` | `18_wtf_spatial/18_wtf_05_storage_drainage_index.csv`; `08_model_benchmarking/08_perwell_nse.csv`; `18_wtf_spatial/18_wtf_01_well_sy_estimates.csv` | 18 | Aquifer diagnostic synthesis (t½ vs ΔNSE, sized by Sy) | modelled |
| 16 | `20_head_surface_streams.png` | `03_master_data.csv` (per-well mean annual head, IDW-interpolated) | 20 | Mean head surface + normalised Darcy vectors | modelled |
| 17 | `20_residual_ssm.png` | `20_spatial_figures/20_residual_perwell.csv` | 20 | SSM water-balance residual field | modelled |
| 18 | `25_05_fit_diagnostic.jpg` (a) + `25_07_cluster_decomposition.png` (b) + `25_06_baci_corroboration_chart.jpg` (c) | `25_coastal_gradient/25_report_numbers.csv`; `25_coastal_gradient/25_03_cluster_partition.csv`; `38_coastal_transect/38_results.txt` | 25 (+38) | Coastal-retreat gradient; per-cluster decomposition; transect corroboration | modelled |
| 19 | `20_drawdown_propagation_nohead.png` | schematic; `config.py` (`FOREST_INTERCEPTION`, `DRAWDOWN_H0_MM`, `DRAWDOWN_K_MDAY`, `DRAWDOWN_B_M`) | 20 | Forest-interception drawdown reach | illustrative |
| 20 | `20_coastal_erosion.png` | schematic; `25_coastal_gradient/25_report_numbers.csv`; `config.py` (`COAST_RETREAT_M`, `COAST_RETREAT_RATE`) | 20 | Episodic coastal-retreat reach | illustrative |
| 21 | `09g_coastal_vs_climate_reach.png` | schematic; δ₀ / L / c from `25_coastal_gradient/25_01_panel_fit_parameters.csv` | 09g | Conceptual coastal-vs-climate reach | illustrative |

## Reading the sources

**Figures 14 and 15 — read `half_life_months`.** Both plot the drainage decay half-life
t½ = ln(2)/β₃, which is specific-yield-independent. The source CSV also carries
`storage_drainage_index_months`, the storage–drainage index τ = Sy/β₃, which is a
diagnostic composite and *not* what these figures show. Figure 15 plots t½ against ΔNSE
with point size ∝ Sy.

The half-life is conditional on the 3.7 m displacement datum, since β₃ scales with that
reference; ratios between clusters are datum-invariant.

**Figure 19 — λ render.** The decay length is baked into the image, so the figure must
be regenerated whenever β₃ or Sy move. It is shared with report Figure 50, and the SI
refers to the value it renders; one Script 20 rerun settles all three.

**Figure 18 panels.** The a/b/c assignment follows the manuscript caption. Script 38
emits no PNG in the committed tree — panel c is rendered by Script 25 from the Script 38
result.

## Renders not used by Paper 1

- `07_coeff_04_r2_quality.png` — one-step fit-quality surface, present in the tree but
  not a numbered Paper 1 figure.
- `20_slope_gradient.png` — Script 20, unused in Paper 1.
- `18_wtf_03_sy_contour.png`, `18_wtf_04_sy_contour_extended.png`,
  `18_wtf_05a_recip_beta3_map.png` — Script 18, unused in Paper 1.

Check the report and Paper 2 figure lists before treating any of these as orphans.
