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

`run_analysis.py` provides an interactive menu with six options:

| Option | Description |
|--------|-------------|
| **1 — Run full pipeline** | Runs all 29 steps in order from the beginning |
| **2 — Resume from step** | Skips completed steps; useful after a partial run |
| **3 — Run a single step** | Runs one script in isolation for debugging or re-running |
| **4 — Prepare scenario viewer** | Runs script 19 to build the self-contained HTML viewer |
| **5 — Run supplementary diagnostics** | Runs scripts 22–24 and 09b (residual lag, ridge recharge, seasonality, scraping propagation diagnostic) |
| **6 — Show step list** | Lists all 29 steps with script names and availability status |

For non-interactive use (e.g. in a batch job):

```bash
python run_analysis.py --full          # run all 29 steps
python run_analysis.py --from 14       # resume from step 14
python run_analysis.py --viewer        # build scenario viewer only
python run_analysis.py --supplementary # run supplementary diagnostics (22–24, 09b) only
```

---

## Repository Layout

```text
Newborough_Hydro_Models/
├── data/                        Input CSV, KML, and DEM assets (not versioned)
│   ├── newborough_dem.tif       LiDAR DEM (NRW) — used by scripts 03, 04, 07, 08, 11b, 12, 13, 19, 20
│   ├── streams.kml              SAGA-derived stream network (used by scripts 19, 20)
│   ├── site_boundary.kml        Dissolved stream-cell boundary — study area mask for script 19
│   ├── Features.kml             Site features (dipwell transects, forest boundary, lake)
│   ├── broadleaf_restock.kml    Broadleaf restocking block boundary
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
│   ├── 03_cluster_peak_months.csv      │  Peak month per cluster (feeds 11, 11b)
│   └── 17_wtf_well_sy.csv             ┘  Per-well Sy intermediate (feeds 18, 19)
│   ├── 11b_spatial_thresholds/
│   │   └── forecaster.html              ← interactive groundwater forecaster (built by 11b)
│   ├── 19_spatial_groundwater/
│   │   └── scenario_viewer.html        ← self-contained interactive viewer (standalone)
│   └── [other output directories]
├── src/                         Analysis scripts (29 steps; script 19 also builds the viewer)
│   ├── utils/
│   │   ├── config.py            Cluster colours, labels, DRAINAGE_DATUM, HEADLINE_LAG, FOREST_INTERCEPTION
│   │   ├── data_utils.py        Cleaning and normalisation helpers
│   │   ├── map_utils.py         DEM, KML, and basemap helpers
│   │   ├── model_utils.py       SSM fitting, simulation, and P_flood helpers (displacement formulation)
│   │   └── paths.py             All path constants — single source of truth
│   ├── forecaster_template.html Static HTML/JS shell for the interactive forecaster (injected by 11b)
│   ├── 19_spatial_groundwater.py
│   └── [other scripts]
├── scenario_viewer.html         Lightweight linked viewer for GitHub Pages
├── seasonal_extremes_scatter.html  Interactive scatter plot (from script 14)
├── readme.md
├── requirements.txt
└── run_analysis.py              Interactive pipeline orchestrator
```

---

## Pipeline Phases

Eleven sequential phases, 29 steps total. Validation checkpoints run after Phases 1, 3, and 10.

**Reference network:** 66 wells (from a raw pool of ~80). 
Eight wells are excluded from the reference partition: FE1–4 and LIS1
(clearfell non-stationarity), Llyn Rhos (lake surface), CEH3 and CEH22
(tidal-signal singleton outliers). All except Llyn Rhos remain in the
extended network; Llyn Rhos is excluded from both networks via the
EXTENDED_NETWORK_BLACKLIST (lake stage, not a water-table response).
The reference network is partitioned into k=5 clusters using
Ward's linkage on correlation distance: C1 Lake Edge, C2 Dune, C3 Western
Residual, C4 Main Forest, C5 Coastal Forest. Cluster definitions,
colours and labels are centralised in `src/utils/config.py`.


**Critical ordering constraints:**
- Script 17 (WTF Sy) must run before script 16 (water balance)
- Script 18 (WTF spatial) must run before script 19 (spatial groundwater)
- Script 11b runs after scripts 11 and 06
- Script 21 requires `03_cluster_averages_maod.csv` from script 03
- Option 4 (scenario viewer) runs script 19 standalone — it reads pipeline outputs directly. Script 14 should have run for seasonal extremes to be available

| Phase | Scripts | Steps | Purpose |
|-------|---------|-------|---------|
| 1 | 01–04 | 1–4 | Core LCSC chain |
| 2 | 05–06 | 5–6 | Pearson membership audit and extended network integration |
| 3 | 07–11, 10b, 10c, 11b | 7–14 | Spatial coefficient mapping, model benchmarking, scraping and clearfell BACI, spatial step-change maps, forest zone spatial analysis, forecasting, spatial threshold maps |
| 4 | 00, 14, 12–13 | 15–18 | Climate summary, trajectory projections, GIS figures |
| 5 | 15 | 19 | Depth-dependent PET analysis |
| 6 | 17 | 20 | WTF cluster Sy estimation |
| 7 | 16 | 21 | Water balance decomposition |
| 8 | 18 | 22 | WTF spatial analysis and per-well Sy mapping |
| 9 | 19, 20 | 23–24 | Spatial groundwater analysis and publication figures |
| 10 | 21 | 25 | Forestry scenarios and management intervention figures |
| 11 | 22–24, 09b | 26–29 | Supplementary diagnostics: residual lag structure, ridge recharge hypothesis test, residual seasonality, scraping propagation diagnostic |

---

## Scenario Viewer

The interactive scenario viewer is built by running **option 4** from the menu (or `python run_analysis.py --viewer`). This runs script 19 which reads pipeline outputs directly and produces a single self-contained HTML file:

- `outputs/19_spatial_groundwater/scenario_viewer.html` — standalone self-contained file; opens directly in any browser with no server required

Scenario Δh values are computed dynamically in JavaScript via the SSM equilibrium equation — no precomputed difference maps are produced. The viewer supports interactive exploration of six scenarios with per-well Δh visualisation.

**Colour convention:** red = drier / deeper than baseline; blue = wetter / shallower than baseline.

**Scenario definitions (JavaScript parameters in scenario_viewer.html):**

| Scenario | sP | sPET | sI | sB2 | C4 Δh (depth convention) |
|----------|-----|------|-----|------|---------------------------|
| Full clearfell | 1.00 | 1.00 | 0 | 1.35 | +0.145 m (deeper) |
| Forest thinning | 1.00 | 1.00 | I×0.5 | 1.15 | +0.073 m |
| Broadleaf conversion | 1.00 | 1.00 | 0.25 | 1.45 | +0.003 m |
| Climate dry | 0.90 (−10% P) | 1.10 (+10% PET) | — | — | all clusters |
| Climate wet | 1.10 (+10% P) | 1.00 (unchanged) | — | — | all clusters |

Δh sign convention: **positive = water table deepens (drier)**; negative = shallower (wetter).

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
| CEH3 | Excluded from reference network (tidal-signal contamination); also excluded from spatial interpolation due to unrepresentative head values. Appears in the forecaster as nearest-cluster-only (flagged, not dropped). |
| CEH17 | Poorest SSM fit on site (R² = 0.427); β₁ = 0.694 and β₃ = 0.049 are both site minima; inflates water balance residual |
| CEH22 | Excluded from reference network (tidal-signal contamination); retained in extended network only |

**Nearest-cluster-only wells in the forecaster:** Five wells (CEH3, CEH4,
CEH7, CEH8, CEH37) sit outside the SSM operational domain but appear in
the interactive forecaster (Script 11b output) with their best-matching
cluster's coefficients. The forecaster UI marks these with an asterisk and
an explanatory notice so users know the cluster label is a nearest-type
assignment, not core membership. See `NEAREST_CLUSTER_ONLY_WELLS` in
`11b_spatial_thresholds.py`.

Note: CEH22 may or may not also need excluding from Script 19's spatial
interpolation — that depends on whether Script 19 uses the reference
network or the full well set. Worth checking when Script 19 is next
reviewed. If it uses only reference wells, CEH22 is already absent.

These wells remain in all SSM fitting and clustering analyses — they are excluded only from the spatial interpolation figures in script 19.

---

## Reproducibility Notes

- Python 3.10 or later required (3.12 tested).
- All file paths are defined in `src/utils/paths.py` — no hardcoded paths in any analysis script.
- KML support in script 19 uses pure XML + pyproj + shapely (no fiona KML driver required).
- Stream network skeletonisation (script 20) requires scikit-image.
- The `outputs/` directory should be excluded from version control.
- Scripts 18 and 19 accept a `--supplementary` flag to generate diagnostic figures not cited in the main paper body. `run_analysis.py` passes this flag automatically.
- Script 21 accepts a `--preview` flag for 150 dpi quick preview output.
- Script 00 accepts `--profile {full,short,both}`; `run_analysis.py` invokes it with `--profile full` to produce the full 95-year record outputs including the summer warming trend figure (`00_03_summer_warming_trend.png`). The `short` variant restricts everything to the well-record overlap window (Apr 2005 – Feb 2026) and can be run manually if needed.

---

## Licensing and Attribution

- **Groundwater Data:** © M. Hollingham (2026)
- **Topographic Data:** Contains NRW LiDAR information © Natural Resources Wales and Database Rights
- **Climate Data:** Contains public sector information licensed under the Open Government Licence v3.0
