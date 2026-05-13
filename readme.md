# Newborough Warren Groundwater Analysis Pipeline

Reproducible Python workflow supporting the manuscript:

> *Hydrogeological Dynamics, Behavioural Clustering and Management Intervention
> Analysis at Newborough Warren Coastal Sand Dune Aquifer, Wales* (Hollingham, 2026)

---

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_analysis.py           # opens interactive menu
```

---

## Documents

All documents are in [`docs/`](docs/) and linked from the
[GitHub Pages site](https://newbroman.github.io/Newborough_Hydrology/).

| Document | Path | Description |
|----------|------|-------------|
| **Full report** | `docs/report/report.pdf` | Main manuscript (35 figures, 11 tables) |
| **Supplementary material** | `docs/report/Supplementary_Material.pdf` | Additional tables and figures |
| **Academic summary** | `docs/academic_summaries/academic_summary.pdf` | Concise research summary for researchers |
| **Public summary (EN)** | `docs/public_summaries/Newborough_Warren_Public_Summary.pdf` | Plain-language overview |
| **Public summary (CY)** | `docs/public_summaries/Niwbwrch_Crynodeb_Cyhoeddus.pdf` | Crynodeb cyhoeddus Cymraeg |
| **Public summary (PL)** | `docs/public_summaries/Newborough_Warren_Podsumowanie.pdf` | Podsumowanie po polsku |
| **Glossary (EN)** | `docs/Glossaries/Dune_Hydrology_Glossary.pdf` | Dune hydrology terminology |
| **Glossary (CY)** | `docs/Glossaries/Geirfa_Hydroleg_Twyni.pdf` | Geirfa Cymraeg |
| **Glossary (PL)** | `docs/Glossaries/Slownik_Hydrologii_Wydm.pdf` | Słownik polski |
| **Web Tools User Manual** | `docs/web_tools/NRG_Web_Tools_User_Manual.pdf` | How to operate the Forecaster, Scenario Viewer and Scatter |
| **Web Tools Technical Note** | `docs/web_tools/NRG_Web_Tools_Technical_Note.pdf` | Model equations, data bundles and rendering |

---

## Running the Pipeline

`run_analysis.py` provides an interactive menu with six options:

| Option | Description |
|--------|-------------|
| **1 — Run full pipeline** | Runs all 28 steps in order from the beginning |
| **2 — Resume from step** | Skips completed steps; useful after a partial run |
| **3 — Run a single step** | Runs one script in isolation for debugging or re-running |
| **4 — Prepare scenario viewer** | Runs script 19 to build the self-contained HTML viewer |
| **5 — Run supplementary diagnostics** | Runs scripts 22–24 (residual lag, ridge recharge, seasonality) |
| **6 — Show step list** | Lists all 28 steps with script names and availability status |

For non-interactive use (e.g. in a batch job):

```bash
python run_analysis.py --full          # run all 28 steps
python run_analysis.py --from 14       # resume from step 14
python run_analysis.py --viewer        # build scenario viewer only
python run_analysis.py --supplementary # run supplementary diagnostics (22–25) only
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
├── src/                         Analysis scripts (28 steps; script 19 also builds the viewer)
│   ├── utils/
│   │   ├── config.py            Cluster colours, labels, DRAINAGE_DATUM, HEADLINE_LAG, FOREST_INTERCEPTION
│   │   ├── data_utils.py        Cleaning and normalisation helpers
│   │   ├── map_utils.py         DEM, KML, and basemap helpers
│   │   ├── model_utils.py       SSM fitting, simulation, and P_flood helpers (displacement formulation)
│   │   └── paths.py             All path constants — single source of truth
│   ├── forecaster_template.html Static HTML/JS shell for the interactive forecaster (injected by 11b)
│   ├── 19_spatial_groundwater.py
│   └── [other scripts]
├── docs/                        Reports, summaries and reference documents
│   ├── report/
│   │   ├── report.pdf                  Full manuscript
│   │   └── Supplementary_Material.pdf  Tables, figures not in main text
│   ├── academic_summaries/
│   │   └── academic_summary.pdf        Concise research summary
│   ├── public_summaries/
│   │   ├── Newborough_Warren_Public_Summary.pdf    English
│   │   ├── Niwbwrch_Crynodeb_Cyhoeddus.pdf        Cymraeg
│   │   └── Newborough_Warren_Podsumowanie.pdf      Polski
│   ├── Glossaries/
│   │   ├── Dune_Hydrology_Glossary.pdf             English
│   │   ├── Geirfa_Hydroleg_Twyni.pdf               Cymraeg
│   │   └── Slownik_Hydrologii_Wydm.pdf             Polski
│   └── web_tools/
│       ├── NRG_Web_Tools_User_Manual.pdf           How to use the web tools
│       ├── NRG_Web_Tools_Technical_Note.pdf         Model equations & data architecture
│       ├── NRG_Web_Tools_User_Manual.docx           (editable)
│       └── NRG_Web_Tools_Technical_Note.docx        (editable)
├── scenario_viewer.html         Lightweight linked viewer for GitHub Pages
├── seasonal_extremes_scatter.html  Interactive scatter plot (from script 14)
├── index.html                   GitHub Pages landing page
├── readme.md
├── requirements.txt
└── run_analysis.py              Interactive pipeline orchestrator
```

---

## Pipeline Phases

Thirteen sequential phases, 28 steps total. Validation checkpoints run after Phases 1, 3, 9, and 10.

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
- Script 25 (coastal-retreat) requires `14_summer_trend_stats.csv` from script 14 and `10a_02_ancova_full_coefficients.csv` from script 10a
- Option 4 (scenario viewer) runs script 19 standalone — it reads pipeline outputs directly. Script 14 should have run for seasonal extremes to be available

| Phase | Scripts | Steps | Purpose |
|-------|---------|-------|---------|
| 1 | 01–04 | 1–4 | Core LCSC chain |
| 2 | 05–06 | 5–6 | Pearson membership audit and extended network integration |
| 3 | 07, 08, 09 suite, 10 suite, 11, 11b | 7–12 | Spatial coefficient mapping, model benchmarking, scraping (09a–e) and clearfell BACI (10a–h), forecasting and spatial threshold maps |
| 4 | 00, 14, 12, 13 | 13–16 | Climate summary, trajectory projections, GIS figures |
| 5 | 15 | 17 | Depth-dependent PET analysis |
| 6 | 17 | 18 | WTF cluster Sy estimation |
| 7 | 16 | 19 | Water balance decomposition |
| 8 | 18 | 20 | WTF spatial analysis and per-well Sy mapping |
| 9 | 19, 20 | 21–22 | Spatial groundwater analysis and publication figures |
| 10 | 21 | 23 | Forestry scenarios and management intervention figures |
| 11 | 25 (coastal-gradient) | 24 | Coastal-retreat gradient analysis |
| 12 | 22–24 | 25–27 | Supplementary diagnostics: residual lag structure, ridge recharge hypothesis test, residual seasonality |
| 13 | 26 (greyscale) | 28 | Greyscale figure conversion utility (journal-ready B&W) |

Phases 1–11 produce the main analytical results documented in the report. Phase 12 runs supplementary diagnostics. Phase 13 runs the greyscale utility (Script 26), retained in `run_analysis.py` as a callable step but not treated as an analytical phase. The main analytical Script 25 (`25_coastal_gradient.py`, Phase 11) and the greyscale utility Script 26 (`26_greyscale_figures.py`, Phase 13) are distinct files. Within the Script 10 clearfell BACI suite, `10c_forest_zone_analysis.py` runs in order but its outputs are treated as supplementary; the other seven sub-scripts (10a, 10b, 10d–10h) contribute to the primary report results.

---

## Scenario Viewer

The interactive scenario viewer is built by running **option 4** from the menu (or `python run_analysis.py --viewer`). This runs script 19 which reads pipeline outputs directly and produces a single self-contained HTML file:

- `outputs/19_spatial_groundwater/scenario_viewer.html` — standalone self-contained file; opens directly in any browser with no server required

Scenario Δh values are computed dynamically in JavaScript via the SSM equilibrium equation — no precomputed difference maps are produced. The viewer supports interactive exploration of seven scenarios (baseline, UKCP18 2050s, UKCP18 2080s, clearfell, broadleaf, thinning, scraping) with per-well Δh visualisation.

**Colour convention:** red = drier / deeper than baseline; blue = wetter / shallower than baseline.

**Scenario definitions (JavaScript parameters in scenario_viewer.html):**

Scenario parameters are injected at viewer generation time. The clearfell and thinning β₂ multipliers are loaded dynamically from Script 10e output via `clearfell_common.load_clearfell_b2_multiplier()` — no hardcoded values remain.

| Scenario | sP_w | sP_s | sPET_w | sPET_s | sI | sB2 |
|----------|------|------|--------|--------|----|-----|
| Baseline | 1.00 | 1.00 | 1.00 | 1.00 | 0.24 | 1.00 |
| UKCP18 2050s | 1.10 | 0.85 | 1.05 | 1.20 | 0.24 | 1.00 |
| UKCP18 2080s | 1.20 | 0.70 | 1.10 | 1.35 | 0.24 | 1.00 |
| Full clearfell | 1.00 | 1.00 | 1.00 | 1.00 | 0 | ~1.108 (BACI-corrected) |
| Broadleaf conversion | 1.00 | 1.00 | 1.00 | 1.00 | 0.15 | 1.00 |
| Forest thinning | 1.00 | 1.00 | 1.00 | 1.00 | 0.12 | ~1.054 (half-perturbation) |

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
