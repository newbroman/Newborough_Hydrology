# Paper 1 — figure source files

*Per-paper figure provenance for Hollingham (2026), aquifer-characterisation framework.
Keyed on the source pipeline filename. Class ∈ {measured, modelled, illustrative}.*

**Regenerated 2026-07-24 from the "Source data" block of `Paper1.pdf` at commit
`938fa34`.** The paper's Source data block cites the underlying **data** files (the CSVs
holding the numbers); this document additionally records the **rendered** artefact
(the PNG/JPG that became each figure), which the paper's block does not carry. Both
columns are given below, so this file is a superset and is the durable record once the
review-only Source data block is stripped at production.

**Coverage: 21 figures.** The previous revision of this file listed 18 and predated
three changes — the β-coefficient atlas split into separate Figures 11/12/13, the
retitling of Figure 14 from the storage–drainage index to the drainage decay half-life,
and the addition of Figures 19–21.

*Rendered-file existence verified against the committed `outputs/` tree on `main`.
Manuscript captions do not carry the source filename (Paper 1 does not follow the
report's "(`file.png`)" convention); the mapping below is the authoritative record.*

| Fig | Rendered file | Source data file(s) | Script | Topic | Class |
|---|---|---|---|---|---|
| 1 | `12_01_dem_site_overview.png` | `01_locations.csv` (+ DEM/KML in `data/geo/`) | 12 | Site topography, geology & monitoring network | measured |
| 2 | `00_01_climate_timeseries.png` | `01_climate.csv` | 00 | Climate forcing — P, PET, cumulative surplus | measured |
| 3 | `00_03_summer_warming_trend.png` | `00_climate_summary/00_03_summer_warming_stats.csv` | 00 | Post-2013 summer warming | measured |
| 4 | `02_01_dendrogram.png` + `02_02_validation_plots.png` | `02_clustering/02_07_cluster_membership_k5.csv` | 02 | Ward's dendrogram + dual-metric k-selection | modelled |
| 5 | `05_pear_01_spatial_confidence_map.png` | `05_pear_membership_audit.csv` (+ `01_locations.csv`) | 05 | Spatial cluster distribution, Pearson-affinity validation | modelled |
| 6 | `02_03_cluster_hydrographs_wb.png` | `02_clustering/02_09_cluster_amplitude_summary.csv` | 02 | Cluster-centroid hydrographs & seasonal amplitudes | measured |
| 7 | `16_water_bal_bar_ms.png` | `16_water_balance/16_water_bal_table.csv` | 16 | Water-balance decomposition by cluster | modelled |
| 8 | `18_wtf_02_spatial_sy_map.png` | `17_wtf_specific_yield/17_wtf_01_sy_estimates.csv` | 18 | Interception-corrected WTF specific-yield surface | modelled |
| 9 | `08_lcsc_02_r2_improvement_map.png` | `08_model_benchmarking/08_perwell_nse.csv` | 08 | SSM-over-TLM iterative NSE gain | modelled |
| 10 | `03_09_well_optimal_datums.png` + `03_10_well_r2_gain_map.png` | `03_09_well_optimal_datums.csv`; `03_08_datum_sensitivity.csv` | 03 | Per-well optimal drainage datum + R² gain over 3.7 m | modelled |
| 11 | `07_coeff_01_beta1_recharge.png` | `07_spatial_coefficients/07_coeff_maps_data.csv` | 07 | β₁ recharge-sensitivity surface | modelled |
| 12 | `07_coeff_02_beta2_atm_draw.png` | `07_spatial_coefficients/07_coeff_maps_data.csv` | 07 | β₂ atmospheric-draw surface | modelled |
| 13 | `07_coeff_03_beta3_drainage.png` | `07_spatial_coefficients/07_coeff_maps_data.csv` | 07 | β₃ drainage-rate surface | modelled |
| 14 | `18_wtf_05_drainage_timescale_map.png` | `18_wtf_spatial/18_wtf_05_drainage_timescale.csv` (`half_life_months`) | 18 | Drainage decay half-life t½ = ln(2)/β₃ | modelled |
| 15 | `18_wtf_06_aquifer_diagnostic_synthesis.png` | `18_wtf_05_drainage_timescale.csv`; `08_perwell_nse.csv`; `17_wtf_01_sy_estimates.csv` | 18 | Aquifer diagnostic synthesis (t½ vs ΔNSE, sized by Sy) | modelled |
| 16 | `20_head_surface_streams.png` | `03_master_data.csv` (per-well mean annual head, IDW-interpolated) | 20 | Mean head surface + normalised Darcy vectors | modelled |
| 17 | `20_residual_ssm.png` | `20_spatial_figures/20_residual_perwell.csv` | 20 | SSM water-balance residual field | modelled |
| 18 | `25_05_fit_diagnostic.jpg` (a) + `25_07_cluster_decomposition.png` (b) + `25_06_baci_corroboration_chart.jpg` (c) — **confirm** | `25_report_numbers.csv`; `25_03_cluster_partition.csv`; `38_coastal_transect/38_results.txt` | 25 (+38) | Coastal-retreat gradient; per-cluster decomposition; transect corroboration | modelled |
| 19 | `20_drawdown_propagation_nohead.png` — **confirm** | schematic; `config.py` (`FOREST_INTERCEPTION`, `DRAWDOWN_H0/K/B`) via Script 09f | 20 / 09f | Forest-interception drawdown reach | illustrative |
| 20 | `20_coastal_erosion.png` — **confirm** | schematic; `25_report_numbers.csv` + `config.py` (`COAST_RETREAT_*`) | 20 / 09f | Episodic coastal-retreat reach | illustrative |
| 21 | `09g_coastal_vs_climate_reach.png` | schematic; δ₀/L/c from `25_coastal_gradient/25_01_panel_fit_parameters.csv` | 09f / 09g | Conceptual coastal-vs-climate reach | illustrative |

## Items to confirm

Three rows are marked **confirm** — the rendered file is inferred rather than stated in
the paper's Source data block, which for these figures records parameters rather than a
rendered artefact. All named files exist in the committed `outputs/` tree; what needs
confirming is which one became which figure (or panel).

- **Figure 18 panels.** The paper's block cites three data sources but no rendered file.
  Three plausible Script 25 renders exist: `25_05_fit_diagnostic.jpg` (per-well slope vs
  distance, with the fits overlaid), `25_07_cluster_decomposition.png` (per-cluster
  decomposition) and `25_06_baci_corroboration_chart.jpg` (the AR(1)-corrected transect
  corroboration, matching panel c's −28.2 mm/yr). The a/b/c assignment above follows the
  caption, but should be confirmed against the staged figure. Script 38 emits no PNG in
  the committed tree — panel c appears to be rendered by Script 25 from the Script 38
  result.
- **Figures 19 and 20.** The block says "via Script 09f" and cites `config.py`
  constants, but the rendered files present in the tree are Script 20's
  `20_drawdown_propagation_nohead.png` and `20_coastal_erosion.png`. Most likely these
  are rendered by Script 20 and parameterised through 09f/`config.py`; confirm which
  script owns the render before relying on this row.

## Notes

- **Figure 14 retitled.** This figure now shows the drainage decay half-life
  t½ = ln(2)/β₃, which is specific-yield-independent — *not* the storage–drainage index
  τ = Sy/β₃ that earlier revisions of this file recorded. The source CSV retains the
  historical `drainage_timescale` filename stem and carries **both** quantities as of
  Script 18 v1.7.0: read `half_life_months` for t½, not `tau_months` (the
  storage–drainage index). The same distinction applies to Figure 15.
  Do not rename the file stem.
- **Figure 15 axis.** Likewise plots t½ (not τ) against ΔNSE, with point size ∝ Sy.
- **One-step fit-quality surface.** `07_coeff_04_r2_quality.png` exists in the tree but
  is not a numbered Paper 1 figure. §4.7 previously pointed to it in the Supplement;
  that pointer is being removed, so the render is currently unused by Paper 1 — check
  the report and Paper 2 before treating it as an orphan.
- **Orphan sweep.** A full sweep needs the report's and Paper 2's figure lists alongside
  this one. `20_slope_gradient.png` (Script 20) remains unused in Paper 1.
