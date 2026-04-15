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
│   ├── streams.kml              SAGA-derived stream network (used by scripts 19, 20)
│   ├── site_boundary.kml        Dissolved stream-cell boundary — study area mask for script 19
│   ├── Features.kml             Site features (dipwell transects, forest boundary, lake)
│   └── clearfell.kml            Clearfell experiment boundary
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
│   ├── 19_spatial_groundwater/
│   │   ├── scenario_viewer.html        ← self-contained interactive viewer (standalone)
│   │   ├── baseline/                   ← baseline scenario outputs
│   │   ├── forest_removal/             ← clearfell scenario outputs
│   │   ├── forest_thinning/            ← 50% thinning scenario outputs
│   │   ├── species_change/             ← broadleaf conversion scenario outputs
│   │   ├── climate_dry/                ← climate dry scenario outputs
│   │   ├── climate_wet/                ← climate wet scenario outputs
│   │   └── difference_maps/            ← per-field Δ maps vs baseline
│   └── [other output directories]
├── src/                         Analysis scripts (23 steps + 2 viewer scripts)
│   ├── utils/
│   │   ├── config.py            Cluster colours and labels
│   │   ├── data_utils.py        Cleaning and normalisation helpers
│   │   ├── map_utils.py         DEM, KML, and basemap helpers
│   │   ├── model_utils.py       SSM fitting helpers
│   │   └── paths.py             All path constants — single source of truth
│   ├── 19_spatial_groundwater.py
│   ├── 19a_scenario_runner.py   Runs all scenarios; generates per-field difference maps
│   ├── 19b_build_viewer.py      Assembles self-contained HTML scenario viewer
│   └── [other scripts]
├── scenario_viewer.html         Lightweight linked viewer for GitHub Pages
├── seasonal_extremes_scatter.html  Interactive scatter plot (from script 14)
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
- Option 4 (scenario viewer) requires script 19 to have run; script 14 should also have run for the seasonal extremes scatter to be populated

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

The interactive scenario viewer is built by running **option 4** from the menu (or `python run_analysis.py --viewer`). This calls scripts 19a and 19b in sequence and produces two output files:

- `outputs/19_spatial_groundwater/scenario_viewer.html` — standalone self-contained file (all images base64-embedded; ~60–130 MB depending on scenarios run); opens directly in any browser with no server required
- `scenario_viewer.html` — lightweight linked viewer (~22 KB) for use with GitHub Pages; images are loaded from the `outputs/` folder by relative path

The viewer has four tabs:

- **Forest Management** — per-field difference maps (Δ vs baseline) for clearfell, 50% thinning, and broadleaf conversion scenarios
- **Climate Change** — per-field difference maps for climate dry (ΔP −10%, ΔPET +10%) and climate wet (ΔP +10%, ΔPET −5%) scenarios
- **Baseline Maps** — all spatial groundwater figures under observed 2005–2026 conditions
- **Seasonal Profiles** — cluster seasonal water table hydrographs with Curreli et al. (2013) ecological thresholds; link to seasonal extremes scatter plot

**Colour convention throughout:** red = drier / more than baseline; blue = wetter / less than baseline. Maps are auto-scaled from the p5–p95 of actual well Δ values. Maps where |Δ| is below a meaningful threshold are omitted rather than shown as noise.

**Scenario definitions:**

| Scenario | Parameters | Site-wide mean Δh |
|----------|-----------|-------------------|
| Full clearfell | β₂ ×1.15 for C4; interception removed | C4 only: −0.145 m |
| Forest thinning | 50% of clearfell effect | C4 only: −0.073 m |
| Broadleaf conversion | β₁ ×0.90 for C4 in autumn | C4 only: −0.003 m |
| Climate dry | ΔP = −89 mm/yr, ΔPET = +54 mm/yr | −0.165 m |
| Climate wet | ΔP = +89 mm/yr, ΔPET = −27 mm/yr | +0.112 m |

---

## Data Dependencies for Script 19

Script 19 requires the following files in `data/`:

| File | Purpose |
|------|---------|
| `site_boundary.kml` | Study area boundary mask — dissolved SAGA stream-cell polygons in WGS84. Used by `make_site_mask()` to clip interpolated surfaces to the dune system outline. Read via pure XML + pyproj + shapely (no fiona KML driver required). Falls back to a rectangular sea-boundary mask if absent. |
| `streams.kml` | SAGA stream network — used for stream polyline rendering in figures. Separate from `site_boundary.kml`. |
| `newborough_dem.tif` | LiDAR DEM — used for greyscale hillshade base layer. |
| `Features.kml` | Site features overlay (transects, forest boundary, lake, clearfell area). |

**Wells excluded from spatial interpolation:**

| Well | Reason |
|------|--------|
| CEH3 | Perched above the regional water table — unrepresentative head values |
| CEH17 | Poorest SSM fit on site (R² = 0.427); β₁ = 0.694 and β₃ = 0.049 are both site minima; inflates lateral inflow residual |

These wells remain in all SSM fitting and clustering analyses — they are excluded only from the spatial interpolation figures in script 19.

---

## Reproducibility Notes

- Python 3.10 or later required (3.12 tested).
- All file paths are defined in `src/utils/paths.py` — no hardcoded paths in any analysis script.
- KML support in script 19 uses pure XML + pyproj + shapely (no fiona KML driver required).
- Stream network skeletonisation (script 20) requires scikit-image.
- The `outputs/` directory should be excluded from version control.
- Scripts 18 and 19 accept a `--supplementary` flag to generate diagnostic figures not cited in the main paper body.
- Script 21 accepts a `--preview` flag for 150 dpi quick preview output.

---

## Licensing and Attribution

- **Groundwater Data:** © M. Hollingham (2026)
- **Topographic Data:** Contains NRW LiDAR information © Natural Resources Wales and Database Rights
- **Climate Data:** Contains public sector information licensed under the Open Government Licence v3.0
