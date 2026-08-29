# data/geo — provenance

**Companion to `data/CLIMATE_PROVENANCE.md`.** One entry per geographic input:
what it is, where it came from, what coordinate system it is in, whether its
source is committed, and what reads it.

**Why it exists.** The vector layers underpin published figures and at least one
published *number* — the long-run coastal retreat rate of D-060 — and until now
nothing recorded who digitised them, from what, or how well. Two of them
(`coastline_hwm.geojson` and its clipped child) carry provenance inside the file
as GeoJSON properties, which is the right pattern; the KMLs carry none, because
a QGIS KML export has nowhere obvious to put it. The `.qmd` sidecars QGIS writes
*do* have the fields — `<title>`, `<abstract>`, `<contact>`, `<dates>`,
`<links>` — and they are all empty. This file is the interim answer; filling the
`.qmd` fields at source would be the better one.

`tools/geo_provenance.py --check` fails if a file in `data/geo/` has no entry
here, or an entry names a file that is not there.

**Fields marked TO CONFIRM are gaps, not omissions to be quietly dropped.** A
layer whose georeferencing method and error are unrecorded cannot support a
quoted retreat rate in a submitted paper.

---

## Coastline — the D-060 retreat measurement

> **Settled position, 2026-08-28.** Everything below is closed except two
> questions only Martin can answer (Google Earth imagery dates; the method
> behind DCoast_2015.kml). In brief:
>
> - **Four epochs**: 1899 (OS sheet, QGIS) and 2006 / 2012 / 2020 (Google Earth
>   Pro, imagery 2006-01-01, 2012-05-26, 2020-04-24). Files named for the epoch
>   each represents — the 1899 survey revision, and each modern imagery date.
>   DCoast_2015.kml was **removed on evidence**: it lies seaward of the 2012
>   line at 10 of 12 longitudes despite being three years later.
> - **`coast1899.kml` holds two lines** — `id=1` high-water mark (seaward),
>   `id=2` dune edge. Both now flagged in the file's own `SimpleData`.
> - **`id=2` is the comparable line** for the modern series: dune edge against
>   dune edge. That comparison reproduces D-060's 0.65 m yr⁻¹.
> - **Georeferencing: 27 GCPs, RMSE 5.95 m**, EPSG:27700, February 2022 — about
>   7 % of the measured displacement, and **the rate must be quoted with it**.
> - **Licences**: the 1899 sheet is NLS, CC-BY-NC-SA 4.0 (scan not
>   redistributed, D-081); the modern shoreline is OpenStreetMap, ODbL. **Both
>   attributions are now in `report15` Source Data Credits**, and the NLS one is
>   also embedded in `coast1899.kml`.
> - **Outstanding**: the retreat measurement is not yet written into any
>   document. When it is, it needs the ±6 m error term and both attributions.

These four are **not read by any script.** They were measured in QGIS by hand,
and the number that came out of them is quoted in the report. That makes their
provenance *more* important than the pipeline layers', not less: nothing
regenerates them, so nothing would catch an error.

### `coast1899.kml`
- **What:** **two lines, not one** — the historic high-tide mark and the dune
  edge. The baseline of D-060's long-run retreat measurement.
- **Which line is which.** The KML declares `High_tide` and `Dune_edge` in its
  schema, **and leaves both fields empty on both placemarks**; the two are
  distinguishable in the file only by `id`. Established geometrically instead,
  by comparing latitude at matched longitude across the whole overlap:
  **`id=1` (24 vertices) lies seaward of `id=2` (21 vertices) at every point**,
  mean separation **124 m** (range 28–215 m). The seaward line is the high-water
  mark, so **`id=1` = High_tide, `id=2` = Dune_edge** — the same order the schema
  declares. **Written into the file 2026-08-28** — both placemarks now carry
  `High_tide` and `Dune_edge` flags in their `SimpleData`, so the identification
  no longer has to be re-derived. XML well-formedness re-checked after the edit.
- **`id=2` is the line comparable to the modern series.** The 2006 and 2021 KMLs
  are the warren's *seaward edge* — a dune edge, not a tide mark — so the
  like-for-like comparison is dune edge against dune edge. A rough check
  supports it: `id=2` to the 2021 line is ≈ 0.0015° of latitude at mid-transect,
  which over 122 years and after projecting onto the shore-normal is ≈ 0.65 m
  yr⁻¹, matching D-060's published rate. Comparing `id=1` instead would mix a
  tide mark with a dune edge.
- **Source map:** **OS Anglesey XXV.NW, revised 1899, published 1901.** Recorded
  in `working/updates/NRG_1900_coastline_retreat_2026-08-22.md` and in D-060.
- **On the name.** Martin: 1900 is the publication year of an 1899 survey, so the
  file name is not an error and **no rename is needed.** One residual nit for
  whoever writes the methods paragraph: the working note gives publication as
  **1901**, not 1900, against a revision date of 1899. All three years are
  defensible labels for different things; the documents should pick one form —
  *"OS Anglesey XXV.NW, revised 1899"* is the least ambiguous — and use it
  consistently.
- **Digitised by:** Martin Hollingham, in **QGIS**, week of 2026-08-17; committed
  `f1d17e6`, 2026-08-22. The raster it was traced from was georeferenced in
  February 2022 — the two steps are four years apart and should not be conflated
  in a methods statement.
- **Attribution now travels with the file.** `coast1899.kml` carries a
  `<Document><description>` block holding the source sheet, the NLS permission
  and licence, the georeferencing parameters, and the id=1/id=2 identification.
  A provenance record in a separate file can be parted from the data; this
  cannot. Worked under the name coast.kml (no file of that name exists now, or ever
  reached git) before commit.
- **CRS:** sidecar declares **EPSG:27700** (OSGB36 / British National Grid) as the
  source-layer CRS. The KML body is WGS84, as the format requires.
- **Georeferencing — established 2026-08-28** from the QGIS control-point file
  archived beside the raster (`1900 copy_modified.tif.points`). Georeferenced to
  **EPSG:27700** from **27 ground control points**, **RMSE 5.95 m** — **3.27 m**
  excluding two outliers of 23.2 m and 12.2 m, both of which remain enabled in
  the QGIS transform. Done in **February 2022**, four years before the lines were
  digitised from it.
  **What this means for the retreat rate.** The measured displacement is of order
  80 m over 122 years; a ±6 m positional error on the historic line is roughly
  7 % of that, and it applies to one end of the comparison only. It is a real
  error term, not a fatal one, and the methods text should quote it rather than
  present the rate as exact.
- **MHW definition mismatch — known and unquantified.** The 1899 sheet marks
  *"High Water Mark of Ordinary Tides"*; the modern line is OS MHW. The working
  note flags the drift between the two definitions as unquantified, and it bears
  directly on the retreat rate.
- **Licence:** the scan came from the **National Library of Scotland**
  (`maps.nls.uk`), confirmed by Martin 2026-08-28. NLS licences its georeferenced
  historic OS scans **CC-BY-NC-SA 4.0**. That means the scan *could* lawfully be
  redistributed with attribution — the decision to keep it out is deliberate and
  is about the share-alike and non-commercial terms reaching a repository
  attached to a journal submission, not about a prohibition (**D-081**). The
  digitised vector is Martin's own work and is committed.
- **Required attribution** wherever the scan or anything traced from it is used:
  *Ordnance Survey Anglesey XXV.NW, revised 1899, published 1901. Reproduced with
  the permission of the National Library of Scotland
  (https://maps.nls.uk), CC-BY-NC-SA 4.0.* This is owed by `coast1899.kml`, which
  was traced from it, and therefore by every figure and rate derived from it.
- **Read by:** no code. Manual QGIS measurement only.

### `1900 copy_modified.tif` — restored, and now in `data/geo/histmaps/`
- **What:** the georeferenced scan of the OS sheet, from which `coast1899.kml`
  was digitised.
- **Status, 2026-08-28: restored and filed.** Now at
  **`data/geo/histmaps/1900 copy_modified.tif`** — the location `.gitignore`
  already designated for historic sheets, ignored by directory so no per-file
  rule is needed and a further sheet cannot be committed by accident.
- **Off-repository archive — it already existed.** The full working set is in
  Google Drive under `projects/newborough/NEWBRO_DEM/`, dated February 2022:
  the original scan (*1900 copy.png* (archive)), two georeferenced rasters, a world file,
  and — the useful one — the **QGIS `.points` control-point files** that record
  the georeferencing and its residuals. That archive is what makes the
  georeferencing reproducible, and it is the backup this record previously
  asked for.
- **Committed:** **no — deliberately.** The 2026-08-22 handover note records it
  plainly: *"The 1900 TIF is deliberately ignored (licence)."* That decision is
  sound and unchanged; it does mean the file has no backup in this repository.
- **"modified" — resolved 2026-08-28** from the archive. The name is QGIS
  georeferencer output, not an edit to the image: the source scan
  *1900 copy.png* (archive) is 1920 × 907 px, and `1900 copy_modified.tif` is
  1949 × 969 px at a 5.74 m pixel scale with a tie point — a slightly larger
  canvas because the warp rotates the sheet onto the grid. *1900 copy_mod_trans.tif* (archive)
  is the same sheet resampled to a **2 m** grid (2000 × 2363), matching the DEM.
  *1900 copy_modified_modified.tif* (archive) is a **false start** — its pixel scale is
  0.174 and its world file places it at (−41150, −62021), which is not a British
  National Grid position; it should not be used.
- **Read by:** no code.

### The modern seaward-edge series — `coast2006.kml`, `coast2012.kml`, `coast2020.kml`

**One source, one method, three epochs.** All three digitised by Martin
Hollingham in **Google Earth Pro 7.3.7.1155** from historic imagery, each named
for the imagery date, each recording the application in its own `atom:link` and
the date and reasoning in its `<description>`:

| file | imagery date | vertices | supplied as |
|---|---|---|---|
| `coast2006.kml` | 2006-01-01 | 14 | *coast 2006.kml* |
| `coast2012.kml` | 2012-05-26 | 29 | *Coast 26-5-2012.kml* |
| `coast2020.kml` | 2020-04-24 | 14 | *coast 2021.kml* |

With the `id=2` dune-edge line of `coast1899.kml` these give a four-epoch series
on a consistent definition — dune edge throughout — with only the 1899 line
coming from a different source and method.

Coordinates are WGS84 lon/lat, as KML requires. **Registration accuracy is not
recorded for any of the three**, and Google Earth imagery georeferencing is
typically a few metres; over the short recent intervals that is a material
fraction of the signal. It is the main remaining uncertainty in the series.

### DCoast_2015.kml — superseded and removed 2026-08-28

Parked in `_to_delete/geo_superseded_2026-08-28/`, not destroyed.

**It was removed on evidence, not only for want of provenance.** With
`coast2012.kml` available the line could be tested against a consistent series,
and it fails: **DCoast_2015.kml lies seaward of the 2012 line at 10 of 12
sampled longitudes**, despite being dated three years later. Under monotonic
retreat that is impossible. The same bias shows up in the rates — 2006→2015
returns 1.53 m yr⁻¹ over nine years against 2.77 m yr⁻¹ for 2006→2012 over six,
so the later line is *closer* to 2006 than the earlier one is.

The likely cause is a different source or a different definition of "dune edge",
which is precisely what its unrecorded provenance left unresolvable. It was the
modern end of D-060's published 0.65 m yr⁻¹.

### `coastline_hwm.geojson`
- **What:** mean high water for the whole site.
- **Source:** **OpenStreetMap (ODbL)**, `natural=coastline`, via the Overpass API
  — recorded in the file's own properties.
- **CRS:** **EPSG:27700**, declared in the file.
- **Licence:** ODbL. Attribution required; share-alike applies to derived
  databases. **It was not attributed anywhere in the corpus** — found and fixed
  2026-08-28: `report15` Source Data Credits now carries a *Shoreline Data*
  entry naming OpenStreetMap, the Overpass retrieval and the ODbL. This mattered
  more than the historic-map attribution, because the clipped child of this file
  is the distance datum for **every `dist_coast_m` in the study**, not for one
  measurement.
- **Committed:** yes. **Read by:** `src/20_spatial_figures.py`.

### `coastline_eroding_hwm.geojson`
- **What:** the west-facing Caernarfon Bay MHW — the eroding shoreline, the
  distance datum for the whole coastal-gradient analysis.
- **Source:** derived from `coastline_hwm.geojson`; clipped at the Abermenai
  southern tip, Menai Strait and Malltraeth estuary excluded, `vertices 0..48`.
  **All of this is recorded inside the file** as `source`, `description`,
  `derived_from` and `clip` properties. **This is the model the others should
  follow.**
- **CRS:** EPSG:27700, declared. **Licence:** inherits ODbL.
- **Committed:** yes. **Read by:** `src/01_data_prep.py` — so every
  `dist_coast_m` in the study traces to this file.

---

## Site, terrain and management layers

**Provenance confirmed by Martin 2026-08-28: he digitised these himself in
Google Earth.** Corroborated file by file — a Google Earth Pro export leaves an
`atom:link` naming the application, and a QGIS export leaves a `<Schema>` block,
so each file states its own origin:

| file | producing tool, per the file | committed | read by |
|---|---|---|---|
| `newborough_dem.tif` | NRW LiDAR DTM (not digitised) | yes | `19`, `20`, `map_utils`, `mask_streams_to_land`, `living/` |
| `site_boundary.kml` | **QGIS export** — see the note below | yes | `19`, `20`, `11b`, `map_utils`, `kml_io` |
| `streams.kml` | plain KML, no tool signature | yes | `20`, `map_utils`, `mask_streams_to_land`, `living/` |
| `Features.kml` | plain KML, no tool signature | yes | `19`, `20`, `24b`, `29`, `31`, `11b`, `living/` |
| `forest_boundary.geojson` | GeoJSON | yes | `paths.py` (`DATA_FOREST_BOUNDARY`) |
| `clearfell.kml` | **QGIS export** | yes | `13`, `19`, `11b`, `map_utils`, `living/` |
| `broadleaf_restock.kml` | Google Earth | yes | `19`, `20`, `config.py`, `living/` |
| `streams.kml` — **derived from `site_boundary.kml`**, not an independent input | | | |
| `clay.kml` | Google Earth | yes | **nothing** |
| `moad.kml` | Google Earth | yes | **nothing — see below** |

Three do not match "digitised in Google Earth", and the difference is in the
files rather than in anyone's memory: `site_boundary.kml` and `clearfell.kml`
are QGIS exports, and `streams.kml` and `Features.kml` carry no tool signature
at all. Worth a second look at those two, since `Features.kml` is the most
widely read vector layer in the project.

### `moad.kml` — used by nothing at all

A full-repository search for the string `moad` — every `.py`, `.sh`, `.md`,
`.csv`, `.json` and `.ipynb` outside this record — returns **nothing**. No
script, no config constant, no path helper, no document, no note. It is
committed, and it is inert. Martin asked directly on 2026-08-28 whether anything
uses it; the answer is no. Nothing here needs it, and it can go whenever he
says.

### `site_boundary.kml` — the GRASS stream network, used as a mask (settled, D-082)

**Confirmed by Martin 2026-08-29: it is the derived stream network of the study
area, produced in GRASS GIS, made by him, and it is the source from which
`streams.kml` was made.** The pipeline uses it as a **mask**.

Its internal layer name is **stream_bound__streama** and it holds **11,715
polygons** across 123,264 vertices in 12 MB — which is what a polygonised raster
looks like, and exactly what a GRASS stream-network extraction produces. That
settles the shape question; `src/utils/mask_streams_to_land.py` beside it does
the corresponding job.

**The filename is a description of its role, not an error.** This being a
hydrological study, the **catchment is the unit of study**, so a
catchment-and-stream-derived mask *is* the study-area boundary in the sense that
matters. Not renamed: five modules read it (`19`, `20`, `11b`, `map_utils`,
`kml_io`) and a rename buys tidiness at the cost of touching working code.

**Note the dependency this creates:** `streams.kml` is derived from this file,
so the two are not independent inputs. `streams.kml` carries no tool signature
because it is a downstream product, which also explains why it looked anomalous.

### `broadleaf_restock.kml` — restock year settled at 1995 (D-082)

The polygon is a Google Earth digitisation whose internal name is
**Broadleaf_conversion_1995.kml** (a layer name, not a file). The felling year is consistent everywhere
at **1993**. **The restocking year is not:**

| source | says |
|---|---|
| the KML's own internal name | **1995** |
| `report10.md:256` | *"established following clearfell in 1993 and restocked around **1996**"* |
| `Supplementary_Material.md:75` | *"the 1993 clearfell and **1996** broadleaf restocking block"* |
| `report9.md:898` | *"felled in 1993 and restocked in **1998**"* |

**Settled 2026-08-29: 1995**, which is what the data file itself had carried all
along — the 1996 and 1998 variants existed only in prose. Applied to `report9`,
`report10`, `report11`, Supplementary Material **v1_26** and the commentary in
`config.py` (**v1.13.0**). Felling year 1993 was already consistent throughout.

**One consequence is flagged and deliberately not acted on.**
`BL_CANOPY_FRACTION_2005 = 0.4` was judged against a **1998** restock — seven
growing seasons by the 2005 baseline. On **1995** it is **ten**. That constant
feeds Script 20's 2005→2025 driver-change map, so 0.4 is now likely low and its
stated basis has moved. It is Martin's judgement to revise, not a mechanical
follow-on, so the value stands with the shift recorded (D-082).

It is the same class of defect T-15 pass 1 was built to catch — a document
contradicting itself — and it was missed because that pass looked for computed
numbers, not dates.

## Scrape polygons

`CEH18_scrape.kml`, `CEH21_scrape.kml`, `CEH40_scrape.kml`, `CEH41_scrape.kml`,
`CEH42_Scape.kml` *(note the spelling — `Scape`, not `Scrape`)*, `ceh36_scrape.kml`,
`Scrape_A.kml`, `Scrape_B.kml`. All committed `a4b9ae8`, 2026-06-21. No direct
code reference by filename.

**All eight are Google Earth digitisations by Martin**, confirmed 2026-08-28 and
corroborated by the `atom:link` in every one of them. Each keeps its original
Google Earth layer name internally (*"CEH18 scrape.kml"*, *"Scrape A.kml"*, and
so on).

**Dates: the author's recollection, and labelled as such.** Martin states
(2026-08-29) that the intervention dates are from memory. One is different:
`config.py:508` calls **CEH36 the "documented April 2015 dune-scrape site"**, so
that one has a source; the rest do not, and neither does the felling date.

That is a legitimate provenance category — Martin has monitored this site for
twenty-one years and is the best-placed witness — but it is weaker than a record,
and it should be **stated in the methods rather than left implicit**, because
the dates define the before/after split of the study's central quasi-experiment.
A documentary cross-check against NRW or Forestry operations records would cost
little and would close the last soft joint in the BACI design. *Recorded as a
known limitation rather than a gap to be filled silently.*

---

## Notes

- **All KML bodies are WGS84** by specification, whatever the `.qmd` sidecar says
  the source layer was. Anything reading a KML and treating its coordinates as
  British National Grid would be wrong by hundreds of kilometres — worth stating
  because `kml_io.py` and `map_utils.py` both reproject.
- **The `.qmd` sidecars exist but are empty** on every field that matters
  (`title`, `abstract`, `contact`, `dates`, `links`, `fees`). Their `<extent>`
  blocks hold uncomputed float sentinels rather than real bounds.
- Only two files of twenty-four carry machine-readable provenance, and both are
  GeoJSON. KML cannot easily hold it; a `.qmd` beside each KML can.

---

## Resolution discrepancy — the DEM is 2 m, and ten places say 1 m

Read directly from the GeoTIFF header: **2000 × 2500 px, `ModelPixelScale`
(2.0, 2.0)** — a 2 m grid over 4 km × 5 km. `report8 §3` agrees, and states the
source precisely (NRW LiDAR DTM, 2 m, March 2023, DataMapWales).

Ten places say otherwise, all of them captions or data-source text:

**Corrected 2026-08-28.** All ten now read 2 m: `report9.odt` ×6 and
`report15.odt` ×1 edited in place, `Paper1` bumped **v1_24 → v1_25** ×3.
Verified in `content.xml`, since caption text inside image frames does not
appear in a LibreOffice text export. The portal attribution is **not** changed —
see below.

| where | said |
|---|---|
| `report9.md` :193, :699, :703, :723, :725, :735 | *"1 m LiDAR DEM hillshade"* ×6 |
| `Paper1.md` :273, :275, :277 | *"1 m LiDAR DEM hillshade"* ×3 |
| `report15.md` :18 | *"1-metre resolution LiDAR composite datasets … via the Welsh Government's Lle Geo-Portal"* |

**Paper 1 is the one that gets defended (D-064), and three of its figure captions
carry the wrong figure.** Nothing computed depends on it — the DEM is used for
hillshade backgrounds and for ground elevations, and the elevations were
validated against DGPS regardless — so this is a description error, not a
numerical one. It is still a reviewer-visible error in a methods statement.

**Portal naming unified 2026-08-28.** `report15` attributed the data to the
**Lle Geo-Portal** where report8 says **DataMapWales**. These are the same portal
at different times: Lle was decommissioned and its holdings moved to
DataMapWales, and `lle.gov.wales` now serves a decommissioning notice pointing
there. `report15` now reads *"accessed via DataMapWales (the Welsh Government
geospatial portal, successor to the decommissioned Lle Geo-Portal); 2 m DTM,
captured March 2023. © Natural Resources Wales and Ordnance Survey."* — carrying
the current name, the historic one, the capture date and the attribution in one
place. It is the only occurrence of either name outside report8.

*Found 2026-08-28 while filling in this record, not by any document check.*

---

## `1900 copy_modified.tif` stays out of the repo (settled — D-081)

**Settled 2026-08-28.** Source confirmed as the National Library of Scotland;
the file stays out of the public repository. The reasoning below stands, with
the supplier question now answered: NLS terms would in fact *permit*
redistribution, so this is a choice rather than a constraint.

**Not a legal opinion — I am not a lawyer, and the decision is Martin's.** The
factual position, so he can make it:

**The map is almost certainly out of copyright.** OS maps are Crown copyright,
and Crown copyright in a published work runs **50 years from first
publication**. A sheet published in 1901 passed out of copyright in 1951. The
cartography itself is public domain; nothing about reproducing it infringes the
Ordnance Survey.

**The scan is a separate question, and probably also unprotected.** UK Intellectual
Property Office guidance is that a faithful digital reproduction of an
out-of-copyright two-dimensional work is unlikely to attract fresh copyright,
because a straight copy is not "the author's own intellectual creation". A flat
scan of an old map is the textbook case.

**What actually binds is the supplier's licence terms, which are contract, not
copyright** — and those apply whatever the copyright status. This is where the
answer really lies, and it turns on the one thing not recorded:

- **National Library of Scotland** (`maps.nls.uk`) — **this is the source.**
  NLS licences its scans **CC-BY-NC-SA 4.0**. Redistribution is *permitted* with
  attribution, so nothing forbids committing it; but the share-alike term would
  reach the repository, and the non-commercial term sits awkwardly with work
  headed to a subscription journal. Those are the grounds for leaving it out.
- **Old-Maps.co.uk / Landmark** and similar commercial suppliers impose terms
  that generally **do not** permit redistribution.

**Recommendation: keep it out, and record why.** Three reasons that hold
regardless of which supplier it was: the licence is unresolved and the cost of
being wrong is a takedown against a public repo attached to a submission; the
repository does not need it, because the analysis consumes `coast1899.kml`,
which is Martin's own work and unambiguously his to publish; and 7.3 MB of
raster buys no reproducibility that a precise provenance record does not already
buy. The existing decision is therefore sound and unchanged.

**The backup exists.** Keeping it out of git is a licensing decision; having no
copy anywhere would have been an accident. The Google Drive archive at
`projects/newborough/NEWBRO_DEM/` holds the original scan, both georeferenced
rasters and the control-point files, and is the authoritative copy. The working
copy in `data/geo/histmaps/` is local and gitignored.

**Settled.** The source is NLS, so the attribution string above is what the
methods section owes — and it is owed whether or not the scan itself is
redistributed, because `coast1899.kml` was traced from it. The remaining action
is a backup outside the repository: keeping it out of git is a licensing
decision, having no copy anywhere is an accident.

---

## Retreat is accelerating — a four-epoch series, and the two ends of the corpus reconciled

Re-running D-060's method (shore-normals at 25 m along the later line of each
pair, distance to the earlier) across all four epochs, 2026-08-28:

| interval | n | median | years | rate |
|---|---|---|---|---|
| 1899 → 2006 | 131 | 64.2 m | 107 | **0.60 m yr⁻¹** |
| 2006 → 2015 | 153 | 15.7 m | 9 | **1.74 m yr⁻¹** |
| 2015 → 2020 | 131 | 38.7 m | 5 | **7.74 m yr⁻¹** |
| 2006 → 2020 | 131 | 46.8 m | 14 | 3.34 m yr⁻¹ |
| **1899 → 2020** | 131 | 116.0 m | 121 | **0.96 m yr⁻¹** |

**Monotonic acceleration across three consecutive intervals**, and the most
recent one lands on a number the corpus already holds independently:
`COAST_RETREAT_RATE` = **8.3 m yr⁻¹ for 2014–20**, against **7.74** measured
here for 2015–20 — agreement to within 7 %, from lines digitised years apart by
different means.

**Why this matters beyond the rate.** D-060 exists because the corpus carried
two coastal-retreat numbers that sat awkwardly together: a short-run 8.3 m yr⁻¹
and a long-run 0.65 m yr⁻¹, with `config.py` warning that extrapolating the
short one overstates accumulation. They were never in conflict — they are the
two ends of a single accelerating series, and the intermediate epochs show the
transition. That reading is available now and was not before, because 2006 and
2020 did not exist as digitised lines when D-060 was written.

**Consequences for the swap Martin asked for.** Substituting the 2020 line for
the 2015 one as the modern endpoint moves the long-run rate from **0.63 to 0.96
m yr⁻¹, a 52 % increase** — not a cosmetic change, and it happens because the
last five years contribute a third of the total displacement.

**Method and status.** Reimplemented independently of QGIS in local
equirectangular metres about the site centroid; over 4 km at 53° N the
projection distortion is far below the 5.95 m georeferencing error and does not
bear on the result. **Validation: run against D-060's own pairing (1899 dune
edge → 2015) it returns 72.5 m and 0.63 m yr⁻¹ against the published 75.2 m and
0.65 — agreement within 4 %,** so the method reproduces the original.

**This is INDICATIVE and NOT CITABLE.** Under D-006 a sensitivity becomes
citable only once it is a pipeline output; this is a session computation. To
publish any of it, the measurement needs to become a script with the lines as
declared inputs.

**Caveats that must travel with these numbers.**
- The 1899 line carries ±5.95 m of georeferencing error. Over a 5-year interval
  that alone is ±1.2 m yr⁻¹ — though it does not enter the 2015→2020 or
  2006→2020 comparisons, which are modern-to-modern.
- The registration accuracy of the Google Earth lines is unrecorded, and Google
  Earth imagery georeferencing is typically a few metres. Over short intervals
  that is a large fraction of the signal.
- Both intervals involving 2015 inherit that line's unknown source imagery.
- Short intervals amplify everything: 5 years converts a few metres of
  registration difference into a whole m yr⁻¹.

---

## The felling date is declared three times, and its provenance is memory

Following Martin's statement of 2026-08-29 that the intervention dates are his
recollection, the code was checked for how that date is held. It is held **three
times independently**:

| where | as |
|---|---|
| `src/utils/clearfell_common.py:309` | `INTERVENTION_DATE = pd.Timestamp('2017-12-01')` |
| `src/utils/scraping_common.py:60` | `INTERVENTION_DATE = pd.Timestamp("2017-12-01")` |
| `src/09b_scraping_propagation.py:73` | `FELL_DATE = pd.Timestamp("2017-12-01")` |

All three currently agree, so nothing is wrong today. **Twelve modules consume
it** — 09a, 09e, 10a, 10b, 10e, 10h, 10i, 10j, 10k, 10m, 10n and
`scraping_common` — and this single date defines the before/after split of the
clearfell BACI, which is the study's central quasi-experiment.

**This is the exact defect D-016 already fixed once.** That entry centralised
`LCSC_DATA_LIMIT` into `config.py` *"from three independent module-local
declarations"* — the same count, the same shape, on a less load-bearing
constant.

**Why it matters more now than yesterday.** A constant whose provenance is
documentary is unlikely to move. A constant whose provenance is recollection
might: if a felling record turns up giving November 2017 or January 2018, the
date changes — and two of the three copies would silently not follow, while
twelve modules carried on importing whichever one they happened to import.

**Recommended, not done here:** centralise onto a single `config.py` constant,
as D-016 did, and apply the environment-adequacy control — reproduce each
affected script's committed output first, and require byte-identical results,
since the value is unchanged and nothing should move. Deliberately not attempted
from the desktop bridge, where 31 of 71 `src/` scripts cannot run at all.
