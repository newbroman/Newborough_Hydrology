# Newborough Warren Groundwater Analysis Pipeline

Reproducible Python workflow supporting the manuscript:

> *Hydrogeological Dynamics, Behavioural Clustering and Management Intervention
> Analysis at Newborough Warren Coastal Sand Dune Aquifer, Wales* (Hollingham, 2026)
> *Journal of Hydrology: Regional Studies*

---

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_analysis.py           # opens interactive menu
```

---

## Running the Pipeline

`run_analysis.py` provides an interactive menu with four options:

| Option | Description |
|--------|-------------|
| **1 — Run full pipeline** | Runs all 23 steps in order from the beginning |
| **2 — Resume from step** | Skips completed steps; useful after a partial run |
| **3 — Run a single step** | Runs one script in isolation for debugging or re-running |
| **4 — Prepare scenario viewer** | Runs scripts 19a and 19b to build the self-contained HTML viewer |
| **5 — Show step list** | Lists all 23 steps with script names and availability status |

For non-interactive use (e.g. in a batch job):

```bash
python run_analysis.py --full          # run all 23 steps
python run_analysis.py --from 14       # resume from step 14
python run_analysis.py --viewer        # build scenario viewer only
```

---

## Repository Layout

```text
Newborough_Hydro_Models/
├── data/                        Input CSV, KML, and DEM assets (not versioned)
├── outputs/                     Generated tables and figures (not versioned)
│   ├── 01_locations.csv                ┐
│   ├── 01_climate.csv                  │
│   ├── 01_wells_clean.csv              │
│   ├── 01_wells_clean_maod.csv         │  Intermediate files read by downstream
│   ├── 01_wells_reference.csv          │  scripts; live in outputs/ root
│   ├── 01_wells_extended.csv           │
│   ├── 01_well_elevations.csv          │
│   ├── 02_cluster_stats.csv            │
│   ├── 03_master_data.csv              │
│   ├── 03_regional_averages.csv        │
│   ├── 03_cluster_averages_maod.csv    │  Cluster mean heads in maOD (feeds 21)
│   └── 17_wtf_well_sy.csv             ┘  Per-well Sy intermediate (feeds 18, 19)
│   ├── 00_climate_summary/
│   ├── 02_clustering/
│   ├── 03_state_space_model/
│   ├── 04_cluster_visualisations/
│   ├── 05_pearson_affinity/
│   ├── 06_pearson_extended/
│   ├── 07_boundary_intercept/
│   ├── 08_model_benchmarking/
│   ├── 09_scraping_intervention/
│   ├── 10_clearfell_baci/
│   ├── 11_forecasting_thresholds/
│   ├── 11b_spatial_thresholds/
│   ├── 12_figure_site_overview/
│   ├── 13_figure_experimental_design/
│   ├── 14_climate_projections/
│   ├── 15_depth_dependent_pet/
│   ├── 16_water_balance/
│   ├── 17_wtf_specific_yield/
│   ├── 18_wtf_spatial/
│   ├── 19_spatial_groundwater/
│   │   └── scenario_viewer.html       ← self-contained interactive viewer
│   ├── 20_spatial_figures/
│   └── 21_forestry_scenarios/
├── src/                         Analysis scripts (23 steps + 2 viewer scripts)
│   ├── utils/
│   │   ├── config.py            Cluster colours and labels
│   │   ├── data_utils.py        Cleaning and normalisation helpers
│   │   ├── map_utils.py         DEM, KML, and basemap helpers
│   │   ├── model_utils.py       SSM fitting helpers
│   │   └── paths.py             All path constants — single source of truth
│   ├── 00_climate_summary.py
│   ├── 01_data_prep.py
│   ├── 02_clustering.py
│   ├── 03_state_space_model.py
│   ├── 04_cluster_visualisations.py
│   ├── 05_pearson_affinity.py
│   ├── 06_pearson_extended.py
│   ├── 07_boundary_intercept.py
│   ├── 08_model_benchmarking.py
│   ├── 09_scraping_intervention.py
│   ├── 10_clearfell_baci.py
│   ├── 11_forecasting_thresholds.py
│   ├── 11b_spatial_thresholds.py
│   ├── 12_figure_site_overview.py
│   ├── 13_figure_experimental_design.py
│   ├── 14_climate_projections.py
│   ├── 15_depth_dependent_pet.py
│   ├── 16_water_bal.py
│   ├── 17_wtf_specific_yield.py
│   ├── 18_wtf_spatial.py
│   ├── 19_spatial_groundwater.py
│   ├── 19a_scenario_runner.py   Generates scenario head surfaces for viewer
│   ├── 19b_build_viewer.py      Assembles self-contained HTML viewer
│   ├── 20_spatial_figures.py
│   └── 21_forestry_scenarios.py
├── readme.md
├── requirements.txt
└── run_analysis.py              Interactive pipeline orchestrator
```

---

## Pipeline Phases

Ten sequential phases, 23 steps total. Validation checkpoints run after Phases 1, 3, and 10.

**Critical ordering constraints:**
- Script 17 (WTF Sy) must run before script 16 (water balance)
- Script 18 (WTF spatial) must run before script 19 (spatial groundwater)
- Script 11b runs after scripts 11 and 06
- Script 21 requires `03_cluster_averages_maod.csv` from script 03

| Phase | Scripts | Steps | Purpose |
|-------|---------|-------|---------|
| 1 | 01–04 | 1–4 | Core LCSC chain |
| 2 | 05–06 | 5–6 | Pearson membership audit and extended network integration |
| 3 | 07–11, 11b | 7–12 | Model diagnostics, intercept audit, scraping and clearfell BACI, forecasting, spatial threshold maps |
| 4 | 00, 14, 12–13 | 13–16 | Climate summary, trajectory projections, GIS figures |
| 5 | 15 | 17 | Depth-dependent PET analysis |
| 6 | 17 | 18 | WTF cluster Sy estimation |
| 7 | 16 | 19 | Water balance decomposition |
| 8 | 18 | 20 | WTF spatial analysis and per-well Sy mapping |
| 9 | 19, 20 | 21–22 | Spatial groundwater analysis and publication figures |
| 10 | 21 | 23 | Forestry scenarios and management intervention figures |

---

## Scenario Viewer

The interactive scenario viewer is a self-contained HTML file that opens in any browser with no server required. It is built by running option 4 from the menu (or `python run_analysis.py --viewer`), which calls scripts 19a and 19b in sequence.

The viewer contains three tabs:

- **Scenario Figures** — IDW head surfaces, Darcy flux, water balance, winter flooding, and storage change maps under six management/climate scenarios (baseline, full clearfell, 50% thinning, broadleaf conversion, climate dry, climate wet)
- **Difference Maps** — scenario vs baseline anomaly maps (blue = wetter, red = drier)
- **Seasonal Extremes** — interactive scatter plot of mean annual summer minimum vs winter maximum water table depth per well, coloured by hydrogeological cluster, with Curreli et al. (2013) ecological threshold lines and a well-search function

Script 14 must have been run before the viewer is built for the seasonal extremes tab to be populated.

---

## Reproducibility Notes

- Python 3.10 or later required (3.12 tested).
- All file paths are defined in `src/utils/paths.py` — no hardcoded paths in any analysis script.
- KML support requires Fiona with the LIBKML driver enabled.
- Stream network skeletonisation (script 20) requires scikit-image.
- The `outputs/` directory should be excluded from version control.
- Scripts 18 and 19 accept a `--supplementary` flag to generate diagnostic figures not cited in the main paper body.
- Script 21 accepts a `--preview` flag for 150 dpi quick preview output.

---

## Licensing and Attribution

- **Groundwater Data:** © M. Hollingham (2026)
- **Topographic Data:** Contains NRW LiDAR information © Natural Resources Wales and Database Rights
- **Climate Data:** Contains public sector information licensed under the Open Government Licence v3.0
