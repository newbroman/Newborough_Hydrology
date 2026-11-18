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
| 2 | `00_01_climate_timeseries_short.png` | `01_climate.csv` | 00 | Climate forcing — P, PET, cumulative surplus | measured |
| 3 | `00_03_summer_warming_trend.png` | `00_climate_summary/00_03_summer_warming_stats.csv` | 00 | Post-2013 summer warming | measured |
| 4 | `02_01_dendrogram.png` + `02_02_validation_plots.png` | `02_clustering/02_07_cluster_membership_k5.csv` | 02 | Ward's dendrogram + dual-metric k-selection | modelled |
| 5 | `05_pear_01_spatial_confidence_map.png` | `05_pear_membership_audit.csv`; `01_locations.csv` | 05 | Spatial cluster distribution, Pearson-affinity validation | modelled |
| 6 | `02_03_cluster_hydrographs_wb.png` | `02_clustering/02_09_cluster_amplitude_summary.csv` | 02 | Cluster-centroid hydrographs & seasonal amplitudes | measured |
| 7 | `51_07_cluster_gap_fill.png` | `51_cluster_gap_fill/51_06_gap_fill_summary.csv` | 51 | Filling gaps from cluster-mates: miss by method, and the two hidden stretches | modelled |
| 8 | `16_water_bal_bar_ms.png` | `16_water_balance/16_water_bal_table.csv` | 16 | Water-balance decomposition by cluster | modelled |
| 9 | `18_wtf_02_spatial_sy_map.png` | `18_wtf_spatial/18_wtf_01_well_sy_estimates.csv` | 18 | Interception-corrected WTF specific-yield surface | modelled |
| 10 | `08_lcsc_02_r2_improvement_map.png` | `08_model_benchmarking/08_perwell_nse.csv` | 08 | SSM-over-TLM iterative NSE gain | modelled |
| 11 | `07_coeff_01_beta1_recharge.png` | `07_spatial_coefficients/07_coeff_maps_data.csv` | 07 | β₁ recharge-sensitivity surface | modelled |
| 12 | `07_coeff_02_beta2_atm_draw.png` | `07_spatial_coefficients/07_coeff_maps_data.csv` | 07 | β₂ atmospheric-draw surface | modelled |
| 13 | `07_coeff_03_beta3_drainage.png` | `07_spatial_coefficients/07_coeff_maps_data.csv` | 07 | β₃ drainage-rate surface | modelled |
| 14 | `18_wtf_spatial/18_wtf_05_halflife_map.png` | `18_wtf_spatial/18_wtf_05_storage_drainage_index.csv` (`half_life_months`) | 18 | Drainage decay half-life t½ = ln(2)/β₃ — the half-life of a departure from a well's own level under Model B | modelled |
| 15 | `01b_01_water_table_flow.png` | `01b_report_numbers.csv`, `01b_water_table_{wet,mean,dry}.tif` (kriged from the dipwells) | 01b | Kriged water table + flow arrows sized by gradient (the Delaunay `20_head_surface_streams.png` retired 2026-09-27, D-205, T-89; swapped into the Paper 1 ODT in v1_61, T-90) | modelled |
| 16 | `20_residual_ssm.png` | `20_spatial_figures/20_residual_perwell.csv` | 20 | SSM water-balance residual at the wells | modelled |
| 17 | `25_05_fit_diagnostic.jpg` (a) + `38_coast_inland_difference.jpg` (b) | `25_coastal_gradient/25_report_numbers.csv`; `25_coastal_gradient/25_03_cluster_partition.csv`; `38_coastal_transect/38_results.txt` | 25 (+38) | Coastal-retreat gradient; per-cluster decomposition; transect corroboration | modelled |
| 18 | `20_drawdown_propagation_nohead.png` | schematic; `config.py` (`FOREST_INTERCEPTION`, `DRAWDOWN_H0_MM`, `DRAWDOWN_K_MDAY`, `DRAWDOWN_B_M`) | 20 | Forest-interception drawdown reach | illustrative |
| 19 | `20_coastal_erosion.png` | schematic; `25_coastal_gradient/25_report_numbers.csv`; `config.py` (`COAST_RETREAT_M`, `COAST_RETREAT_RATE`) | 20 | Episodic coastal-retreat reach | illustrative |
| 20 | `09g_coastal_vs_climate_reach.png` | schematic; δ₀ / L / c from `25_coastal_gradient/25_01_panel_fit_parameters.csv` | 09g | Conceptual coastal-vs-climate reach | illustrative |

## Reading the sources

**Figure 14 — read `half_life_months`.** It plots the drainage decay half-life
t½ = ln(2)/β₃, which is specific-yield-independent. The source CSV also carries
`storage_drainage_index_months`, the storage–drainage index τ = Sy/β₃, which is a
diagnostic composite and *not* what the figure shows.

Since 2026-11-18 (J-19) the column is Model B's β₃, so the timescale is a mean-reversion time, not a
recession to a fixed floor: it is a property of the record and no datum conditions it. The image's own
title still reads "half-life" (T-218).

**Figure 18 — λ render.** The decay length is baked into the image, so the figure must
be regenerated whenever β₃ or Sy move. It is shared with report Figure 50, and the SI
refers to the value it renders; one Script 20 rerun settles all three.

**Figure 17 panels.** The a/b/c assignment follows the manuscript caption. Script 38
emits no PNG in the committed tree — panel c is rendered by Script 25 from the Script 38
result.

## Renders not used by Paper 1

- `18_wtf_spatial/18_wtf_06_aquifer_diagnostic_synthesis.png` — the former Figure 15, removed from Paper 1 on
  2026-10-07 (D-199: the clusters no longer separate on ΔNSE).
- `03_10_well_datum_r2max_map.png`, `03_10_well_r2_gain_map.png` — the per-well datum sweep, Paper 1's
  Figure 11 until 2026-11-18 (J-19, T-110): the fixed floor is the tested alternative, not a result
  (D-334), and the sweep is Paper M's Section 7. report9 Figures 53a/b still carry the maps.
- `07_coeff_04_r2_quality.png` — one-step fit-quality surface, present in the tree but
  not a numbered Paper 1 figure.
- `20_slope_gradient.png` — Script 20, unused in Paper 1.
- `18_wtf_03_sy_contour.png`, `18_wtf_04_sy_contour_extended.png`,
  `18_wtf_05a_recip_beta3_map.png` — Script 18, unused in Paper 1.

Check the report and Paper 2 figure lists before treating any of these as orphans.

*Rows for Figures 2, 10 and 19 (then 18) corrected 2026-10-07 to the outputs the paper actually embeds (identified by picture content with tools/reembed_paper_figures.py); the earlier rows named the full-record climate figure, the datum histograms and a three-panel layout the paper does not carry.*

*Figure 15 (aquifer diagnostic synthesis) removed 2026-10-07 under D-199 (Martin: "Remove, renumber"); Figures 16–21 renumbered 15–20 in the manuscript, its Source data block, the SI and this table.*

*Figure 7 (Script 51, filling gaps from cluster-mates) was missing from this table on 2026-11-18 (J-19, T-110):
the manuscript has carried it since Script 51 landed, and every row from 7 on was therefore one number behind the
manuscript. `reembed_paper_figures.py` pairs embedded pictures against these rows IN ORDER, so the gap made it
replace the wrong picture: in the committed Paper1_v1_92 it had written `16_water_bal_bar_ms.png` over Figure 7
(measured here — v1_91 holds the right 2240x768 render). Row inserted and rows 7–20 renumbered 8–21.*

*Figure 11 (the per-well datum sweep) was dropped from the manuscript on 2026-11-18 (J-19, T-110) and
Figures 12–21 renumbered 11–20 here, in the paper, in its SI and in the Source data block. The half-life map
is Figure 14 and reads Model B's β₃; its own title still says 'half-life' (T-218).*
