# Coastline-distance CSV — provenance

**File:** `data/well_distance_to_coast.csv`
**Read by:** `src/25_coastal_gradient.py` (via `paths.DATA_DIST_COAST`)
**Generated:** May 2026, once, out-of-pipeline
**Re-generation needed only if:** the OS coastline product is updated, the dipwell network is extended with new wells in unmapped positions, or the choice of "eroding shoreline" changes.

---

## What the CSV contains

One row per dipwell, with columns:

| Column | Description |
|---|---|
| `well` | Lower-case well name matching the convention used throughout the pipeline (`01_locations.csv`, `03_master_data.csv`) |
| `easting` | OSGB36 easting (m), EPSG:27700 |
| `northing` | OSGB36 northing (m), EPSG:27700 |
| `dist_coast_m` | Perpendicular distance from the well to the chosen coastline polyline (m) |

97 wells, distance range 147–5,589 m.

---

## How the distances were computed

### Coastline source

**OS Open Map Local** — *TidalBoundary* layer (file: `SH_TidalBoundary.shp`), classification `"High Water Mark"` (MHW).

Downloaded from the Ordnance Survey OpenData portal (Crown copyright OS 2025). Licence: Open Government Licence v3.0.

### Coastline selection

The OS High Water Mark for the Newborough area contains several physically distinct shorelines:

| Segment | Decision | Reason |
|---|---|---|
| **Caernarfon Bay west-facing coast** (line 1756 + 1853, ~15.0 km total) | **INCLUDED** | This is the eroding shoreline at Newborough. The dune-system retreat documented by Forgrave (2020) and the CEH22/CEH4 CUSUM trajectories operate on this coast. |
| Menai Strait (north-east coast) | EXCLUDED | Tidal channel, not subject to the SW-prevailing-wind erosion regime; per project knowledge this coast is not retreating. |
| Llanddwyn Island | EXCLUDED | Bedrock islet, hydrogeologically separate from the dune aquifer. |
| Malltraeth Sands estuary (south interior) | EXCLUDED | Estuarine, sheltered from the eroding wave climate. |

The 15 km included polyline wraps around the SE end of the bay through Abermenai Point — this is geometrically important because several eastern wells (D29, T29, CEH7, etc.) sit close to that wrap-around section and would be misallocated if the coastline were clipped to the western beach only.

### Distance computation

For each dipwell:

```python
from shapely.geometry import Point, LineString
# coastline: a single LineString or MultiLineString in EPSG:27700
well_pt = Point(easting, northing)
dist_m = well_pt.distance(coastline)
```

`Point.distance(LineString)` returns the **minimum perpendicular distance** to any segment of the polyline — the geometrically correct measure for "how far is this well from the coast".

### Visual sanity check

Each well's nearest-point connector to the coastline was plotted in the sanity-check figure `coastline_geometry_check.png` (kept alongside the working scripts but not in the pipeline). Connectors should run cleanly perpendicular to the coast at each well's nearest point.

---

## Why this CSV is a versioned data input rather than computed in-pipeline

Three reasons:

1. **External GIS dependency.** Computing distances from scratch requires the OS shapefile, `geopandas`, and `shapely`. The rest of the pipeline runs on `pandas` + `numpy` + `statsmodels` + `scipy`. Adding GIS dependencies for one analytic question increases the maintenance and re-run burden on downstream users disproportionately.

2. **Stable across pipeline iterations.** The dipwell coordinates and the coastline don't change between pipeline re-runs. Re-computing distances every time the pipeline runs is wasted work.

3. **Reviewer-auditable.** Putting the precomputed values in version control with this provenance sidecar means anyone reading the report or rerunning Script 25 can see exactly what coastline was used and how distances were measured, without needing to re-acquire and re-process the OS data themselves.

If the coastline source or methodology changes, regenerate this CSV and commit both the new CSV and an updated version of this provenance note.

---

*End.*
