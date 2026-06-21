# PAPER 2 — FIGURE SOURCES

Per-paper figure manifest. Stable key = the **source pipeline file** (never renamed).
Staged copies live in `media/` (JPEG, long edge ≤1700 px, q88). Captions in the paper
end with the source filename in parentheses, matching the "Source:" column here.
Class: **measured** (data figure) | **modelled** (scenario/SSM output) | **illustrative**
(assumed-geometry schematic).

| Paper 2 Fig | media/ file | Source pipeline file | Script | Topic | Class |
|---|---|---|---|---|---|
| 1 | fig_scraping_robustness.jpg | 09_scrape_08_ceh36_robustness.png | 09 | CEH36 three-method scraping robustness | measured |
| 2 | fig_scraping_summer_minima.jpg | 09c_04_summer_minima_paired.png | 09c | CEH36 vs CEH4 paired summer minima | measured |
| 3 | fig_clearfell_baci_cusum.jpg | 10a_07_cusum_impact.png | 10a | Forest-control BACI + CUSUM (Impact) | measured |
| 4 | fig_summer_minima_violin.jpg | 21_forestry_04_baci_zone_violin.png | 21 | Summer-minimum distributions by tier | measured |
| 5 | fig_coeff_decomposition.jpg | 10e_03_coefficient_shifts.png | 10e | Before/after SSM coefficient dumbbells by tier; β₁/β₂ %-shift summary | measured — **pipeline-sourced (Script 10e v1.5.0)** |
| 6 | fig_scenario_comparison.jpg | 21_forestry_05_scenario_comparison.jpg | 21 | Forest-management & climate scenarios | modelled |
| 7 | fig_forest_drawdown_reach.jpg | 20_drawdown_propagation.png | 20 | Plantation drawdown reach (SW propagation) | illustrative (assumed edge deficit) |
| 8 | fig_scrape_drawdown.jpg | 20_scrape_drawdown_nohead.png | 20 | Scrape-induced drawdown / cascade | modelled field — **edge magnitude MEASURED (CEH36 Pure-Scraping ≈0.13 m, 09a); depth inferred D=H₀/Sy≈0.42 m; reach modelled (λ≈220 m)** |
