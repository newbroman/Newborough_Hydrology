# Coastline-distance — provenance

**Distance column:** `dist_coast_m` in `data/well_metadata.csv`
**Eroding-shoreline geometry:** `data/geo/coastline_eroding_hwm.geojson`
**Read by:** Scripts 25/28/30/31 (`dist_coast_m`, via `paths.DATA_DIST_COAST`)
**Regenerated + validated in-pipeline by:** `src/01_data_prep.py` (`_validate_dist_coast`)
**Re-generate the committed values only if:** the OS coastline product is updated, the dipwell
network gains wells in unmapped positions, or the choice of "eroding shoreline" changes.

> Supersedes the earlier note that described a separate `well_distance_to_coast.csv` "generated
> once, out-of-pipeline" (that CSV was consolidated into `well_metadata.csv`; the distances have
> since been recomputed and the range is now 119–2,338 m, not the old 147–5,589 m).

---

## What the column contains

One row per dipwell in `well_metadata.csv`, with `dist_coast_m` = the minimum perpendicular
distance (m) from the well (`E`, `N`, EPSG:27700) to the eroding Caernarfon Bay shoreline
polyline. 98 wells with a value; range ~119–2,338 m.

## Two coastlines — which is which

There are **two** committed coastline files, and they are not interchangeable:

| File | Contents | Use |
|---|---|---|
| `coastline_hwm.geojson` | Caernarfon Bay MHW **plus the Menai Strait coast** (Malltraeth excluded) | Fixed-head boundary geometry (e.g. Script 09f/20 drawdown fields) |
| `coastline_eroding_hwm.geojson` | **West-facing Caernarfon Bay frontage only** (the eroding shoreline) | `dist_coast_m` — distance to the eroding front |

The eroding-only polyline is clipped from `coastline_hwm.geojson` at the **Abermenai southern
tip** (the vertex of minimum northing), keeping the west-facing frontage and dropping the Menai
Strait limb. This matters because several eastern wells (ceh7, D29, d29b, T29, L1, L4, L7, ceh6)
sit close to the Menai coast; measured against the full coastline they would be assigned ~1.5 km
too near, corrupting the far-field of the coastal-gradient regression.

### Coastline selection (why Menai / Llanddwyn / Malltraeth are excluded)

| Segment | Decision | Reason |
|---|---|---|
| Caernarfon Bay west-facing coast | **INCLUDED** | The eroding shoreline at Newborough (Forgrave 2020; Pye & Blott 2024). |
| Menai Strait (north-east coast) | EXCLUDED | Tidal channel, not subject to the SW-prevailing-wind erosion regime. |
| Llanddwyn Island | EXCLUDED | Bedrock islet, hydrogeologically separate. |
| Malltraeth Sands estuary | EXCLUDED | Estuarine, sheltered from the eroding wave climate. |

## Distance computation

Minimum perpendicular distance from each well to the eroding-shoreline polyline, in EPSG:27700.
The in-pipeline implementation (`_validate_dist_coast` in Script 01) is a pure-numpy
point-to-segment calculation over the polyline segments — geometrically equivalent to
`shapely` `Point.distance(LineString)` but with no GIS dependency (the pipeline stays on
pandas + numpy).

## Regenerate-and-validate

The committed `dist_coast_m` values remain **canonical**. Script 01 recomputes the distance
from `coastline_eroding_hwm.geojson` and validates the committed values against it, writing the
per-well audit `outputs/01_dist_coast_validation.csv` and warning if any well drifts beyond
25 m. Current agreement: median 1.5 m, max 14.8 m across 98 wells — the residual is the
coastline's 5 m simplification. The committed values are not overwritten; if byte-exact
regeneration were required, the unsimplified source coastline would be committed in place of the
5 m polyline.

---

*End.*
