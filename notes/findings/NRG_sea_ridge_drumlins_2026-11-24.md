# The foreshore ridges in `data/geo/sea_ridge.kml` — drumlin form and grain (2026-11-24)

**Status:** measured finding. Cited in Paper 1 v1_110 §5.1 (without figures; the numbers below are geometry of a
hand-mapped KML, not a pipeline output). Supplements `NRG_drumlin_c2_c3_divide_2026-09-19.md`.

**Source.** `data/geo/sea_ridge.kml` (four polygons) was mapped by Martin from aerial imagery (Google Maps) of the
structures off the western shore, during the drumlin work of September 2026. The imagery is the Google Earth Pro seabed captures of Llanddwyn Bay registered in `data/geo/aerial_manifest.csv` (`seabed1-1-2006.png`, 2006-01-01; `seabed22-4-2017*.png`, 2017-04-22, five views), which are kept out of git (D-081) and since 2026-11-24 backed up to Drive with the other local-only files. The KML was committed in 512352b9 (2026-11-17)
and is read by no script. Martin, 2026-11-24: "There are coastal kml structures in the /data folder"; "We looked
extensively at Google Maps photos to outline where the drumlins might be, looking at the structures off the coast."

## Measured (EPSG:27700; long axis = principal axis of the polygon's vertices)

| ridge | centre (E, N) | long axis | length | width | area | from HWM | nearest wells |
|---|---|---|---|---|---|---|---|
| 1 | 240289, 363057 | 51° | 664 m | 240 m | 11.1 ha | 11 m seaward | CEH17, CEH19 (C5) ~730 m |
| 2 | 240421, 362840 | 39° | 874 m | 165 m | 9.3 ha | 50 m seaward | CEH4 (C3) 802 m |
| 3 | 240585, 362712 | 48° | 904 m | 295 m | 18.8 ha | 141 m seaward | CEH4 (C3) 740 m |
| 4 | 240944, 362012 | 58° | 1312 m | 304 m | 22.6 ha | 105 m seaward | CEH21 (C3) 1065 m |

High-water mark: `data/geo/coastline_hwm.geojson`. No ridge crosses it: all four are intertidal, on the Caernarfon Bay
foreshore beside the western dunes, seaward of C5 Coastal Forest and C3 Western Residual.

## Reading

- **Form:** elongated (length 2.8–5.3 × width), 0.7–1.3 km long: the drumlin form.
- **Grain:** long axes 39–58°, north-east to south-west — the Irish Sea ice-flow direction across Anglesey and the
  drumlin grain Hart (1995) documents in southern Anglesey; the same trend as the site's bedrock ridge.
- **Where:** on the WESTERN (C3/C5, deep-sand) side. The 2026-09-19 memo's point 3 applies: till ridges exposed on
  this foreshore mean the base rises locally under the western sand too, so "thin sand east, thick sand west" is at
  best the base's average shape. Paper 1 §5.1 now says exactly that, and no more.
- **Projected inland** along their axes, the ridges run under C5 and the seaward C3 wells — the same wells that group
  with C5 in Script 02's post-2018 partition (`02_14_period_split.csv`). That coincidence is noted, not claimed.

## Not settled here

`data/geo/clay.kml` (one line, 2.4 km, bearing ~170°, E 243245–244131 on the eastern side) is undocumented; it may be
the estuarine-clay outcrop edge Paper 1 §5.1 describes. Neither file has a provenance note in `data/`.
