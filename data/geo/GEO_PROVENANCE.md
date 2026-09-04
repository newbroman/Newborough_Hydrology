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

> **⚠ Superseded 2026-08-29.** The four-epoch 2006 / 2012 / 2020 series in the
> box below was re-digitised to **2006 / 2017 / 2021 / 2026** and
> `coast2006`/`2012`/`2020.kml` withdrawn to `_superseded/` (D-087, D-089);
> `DCoast_2015.kml` was deleted. The current control is `coast2006B_blind.kml`
> (below). The 2026-08-28 box is kept as the dated record.
>
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

### The measurement series — `coast2006` / `coast2017` / `coast2021` / `coast2026`

**Re-digitised 2026-08-29 by Martin Hollingham in ONE sitting** (file mtimes
14:49–14:51), four epochs read from each file's own `<name>`: **1/1/2006,
24/3/2017, 4/4/2021, 31/3/2026**. Renamed here to the imagery-date convention
from *coast 112006*, *Coast 2432017*, *coast 442021*, *coast 3132026*.

| file | imagery date | vertices | median vertex spacing |
|---|---|---|---|
| `coast2006.kml` | 2006-01-01 | 26 | 146 m |
| `coast2017.kml` | 2017-03-24 | 36 | 105 m |
| `coast2021.kml` | 2021-04-04 | 41 | 91 m |
| `coast2026.kml` | 2026-03-31 | 86 | 42 m |

**This series carries its own control**, which is why it replaced the previous
one. Its 1/1/2006 line is **the same imagery date** as the 2026-08-28
`coast2006.kml`, traced on a different occasion, so the pair measures digitising
repeatability directly: **median 1.71 m, exactly 0.00 m across the middle ~1 km,
rising to ~9.7 m at the north end; 95th percentile of |offset| 10.78 m.** *(Superseded — this pair is contaminated: 5 of the 14 vertices are shared, so the 0.00 m middle kilometre is zero by construction; a blind re-trace gives median 3.66 m, p95 11.23 — see the `coast2006B_blind.kml` control below, W83 / D-089.)* The
operator reproduces his own line to under two metres through the middle of the
frontage. Indicator drift is therefore not available as an explanation for
anything at the tens-of-metres scale.

Sampling every epoch on **one** set of normals (medians taken on different
reference lines are not comparable) puts the old series' problem in one place —
see `_superseded/` below and D-087. The chord-sagitta generalisation bound falls
from **7.467 m to 3.829 m** on these denser lines.

**Registration accuracy is still not recorded** for any line, and the
fixed-feature control has not been digitised. The repeatability figure above
bounds registration *and* interpretation together, which is the more relevant
quantity for this measurement but is not the same test.

### `coast2006B_blind.kml` — the CONTROL

The 1/1/2006 imagery traced a **second time, blind**: the existing line not
loaded, so no vertex could be reused. 53 vertices, `<description>` "Dune edge".
Digitised by Martin Hollingham in Google Earth Pro, supplied 2026-08-29 as
*coast 112006B.kml*.

**Independence verified before use — zero shared vertices to 1e-9 degrees**
against either earlier tracing of the same imagery. That check is not
ceremonial: the first attempt at this control reused five vertices of the line
it was meant to check, and the resulting 1.71 m read as excellent agreement
while being partly agreement of a line with itself. `Script 40._control()` now
refuses to report a tolerance-grade number if any vertex is shared.

**What it measures.** Two tracings of one image cannot differ by real shoreline
change, so their separation is the digitising-plus-registration error of this
process: **|offset| median 2.34 m, p90 5.14, p95 5.53, max 11.57** across 130
normals. That set `SHORE_CONTROL_TOLERANCE_M` = 6.0 and opened Script 40's gate.

**And it separates two errors.** Against the sparse 14-vertex 2026-08-28 line
the same blind trace differs at **p95 36.98 m** — sparsity, a coarse polyline
cutting corners, not interpretation. The old series carried tens of metres of
generalisation error, far more than its 7.467 m chord-sagitta bound implied:
**that statistic understates the disagreement between two independent tracings
of differing density, and should not be read as bounding it.**

**Not a measurement input.** It is an epoch the series already has; using it as
a series line would double-count 2006.

### `coast2019-09-11.kml` / `coast2020-03-31.kml` — the STORM PAIR, not epochs

**Two shorelines bracketing one winter.** Digitised by Martin Hollingham in
**Google Earth Pro 7.3.7.1155** (both carry the application in an `atom:link`)
from historic imagery of **11 September 2019** and **31 March 2020**. Each holds
one Placemark on a single LineString — **70 vertices** and **74 vertices**
respectively — depicting the **dune edge**, the same indicator as the epoch
series. Coordinates are WGS84 lon/lat, as KML requires. Neither carries a
`<description>`, so the indicator is recorded here rather than in the file.

**Renamed on filing, 2026-08-30.** Supplied as *brendan11-9-2019.kml* and
*brendan31-3-2020.kml*; filed as `coast2019-09-11.kml` and `coast2020-03-31.kml`.
The interval is 202 days and spans **Storm Brendan (13-14 January 2020), Storm
Ciara and Storm Dennis (February 2020)**. Two frames five months apart cannot
apportion the movement between them, so naming the pair for one storm would
assert an attribution the measurement does not support. They are named for their
imagery dates, like every other line here. **The internal `<name>` elements still
read `brendan11-9-2019` and `brendan31-3-2020`** — the files were renamed on disk
and not otherwise altered, which is why the supplied names are recorded above.
Nothing globs `data/geo/coast*.kml`; checked across the repository before the
rename, so the `coast` prefix pulls them into no series.

**They are NOT epochs and are not in the epoch series.** Script 40 holds them in
a separate `STORM_PAIRS` registry that feeds neither `EPOCHS` nor `INTERVALS`.
Two reasons, both structural: a 0.55-year interval in `INTERVALS` would enter the
rate series and be read beside 2.32 m yr⁻¹ as comparable; and the epoch lines
also set the common-extent band on which every committed retreat number is
measured, so admitting these two would move published values. See **D-098**.

**What they measure, and what is deliberately not emitted.** Signed shore-normal
displacement on the pair extent, same estimator and same projection origin as the
epochs: **median +8.948 m across 139 normals, p10 +4.061, p90 +21.768, min
+0.762, max +42.840, zero progradation, over a 3454 m frontage.** Emitted to
`outputs/40_shoreline_retreat/40_07_storm_pair.csv` and
`40_report_numbers.csv`. **No rate is emitted for this pair, ever.** The interval
is carried in days. Annualising it gives 16.2 m yr⁻¹, which has the units of a
rate and the meaning of an arithmetic accident.

**Reading it.** The strongest evidence is not the median: it is that **none of
the 139 normals prograded and the least-retreating sat at +0.76 m**. Tracing
error scatters about zero, so an all-positive field is not what a digitising
artefact produces. For scale, the blind repeat-tracing control above is 2.34 m
median / **5.53 m p95**, and this frontage's measured 2006-2026 rate implies
**1.28 m** over the same 202 days. **Caveat, and it is not small: these two
frames were each traced once, by one operator, and borrow their error estimate
from the 2006 repeat-tracing control rather than carrying one of their own.**

### `_superseded/` — the 2026-08-28 series, withdrawn 2026-08-29

`coast2006_digitised_2026-08-28.kml`, `coast2012_digitised_2026-08-28.kml`,
`coast2020_digitised_2026-08-28.kml`. **Retained for corroboration and audit, not
as inputs.**

**`coast2020` is the one that failed.** Measured on a single normal set, seaward
distance back from the 2026 line: 2006 → 47.88 m, 2017 → 25.04 m, 2021 → 8.00 m,
2026 → 0. Smooth and monotonic. `coast2020` sits at **0.59 m** — effectively on
the 2026 line — when five to six years of retreat should put it ~12 m seaward.
**It is displaced landward by roughly 7–8 m relative to every other line in the
record**, and it alone produced the apparent modern acceleration (0.60 → 2.77 →
3.81) that the re-digitised series does not reproduce (1.81 → 2.37 → 2.14).

`coast2006` and `coast2012` are kept because they **agree** with the new series
(the 2006 pair to 1.71 m), which is what makes them useful as corroboration.

### DCoast_2015.kml — DELETED 2026-08-29

Martin: *"we should remove DCoast 2015 as its not verifiable. I cant tell you
what it represents."* Removed from the repository, not parked. It had been
retained as the D-060 regression anchor; **that role is gone and is not missed**,
because D-060's published 0.65 m yr⁻¹ is reproduced without it — the 1899 dune
edge against the new 2006 line gives **0.645 m yr⁻¹ over 107 years, 0.8 %** — by
a route whose every input has known provenance. Script 40 now anchors there, and
carries a second anchor that depends on no historical file at all.

For the record, since it cannot be re-derived once the file is gone: measured
against the new 24/3/2017 line it lay **+17.46 m seaward at 118 of 118
normals**, where `coast2012` is only +7.55 m seaward of that line. It was
seaward of both 2012 and 2017, so it behaved like a pre-2012 line or a more
seaward indicator, and the recollection that it came from 2017 imagery is not
supported by the geometry.

### The 2026-08-28 series — superseded; kept below for the record

**One source, one method, three epochs.** All three digitised by Martin
Hollingham in **Google Earth Pro 7.3.7.1155** from historic imagery and named
for the imagery date. All three carry the application in an `atom:link`.
**Two of the three carry the reasoning in a `<description>`, not all three:
`coast2006.kml` has no `<description>` element at all** — checked 2026-08-29,
correcting an earlier claim here that every file was self-documenting. Nothing
is lost, since this record holds the same facts, but a reader who trusted the
files to carry their own provenance would have found one of them silent.

**None of the three records the DIGITISING date**, only the imagery date and the
2026-08-28 filing. Whether the coarser 2006 and 2020 lines were traced in a
different sitting from the denser 2012 one is therefore not answerable from the
files, and it bears directly on the indicator-drift question:

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

### DCoast_2015.kml — withdrawn as evidence, RETAINED AS A REGRESSION FIXTURE

**Location: `data/geo/_fixtures/DCoast_2015.kml`** (with its `.qmd` sidecar),
moved there 2026-08-29 from `_to_delete/geo_superseded_2026-08-28/` on Martin's
ruling. `_to_delete/` is a bin, not a fixture store, and this file is wanted.

**Its presence is not reinstatement.** It is withdrawn as evidence — see below —
and kept for exactly one purpose: it is the only input that reproduces D-060's
**published 75.2 m / 0.65 m yr⁻¹** for 1899 dune edge → 2015, which is the sole
anchor any reimplementation of the retreat measurement has. **Verified from its
new location, 2026-08-29: 74.2 m over 116 yr = 0.64 m yr⁻¹ across 148 shore
normals, against the published 75.2 m / 0.65 — 1.3 % on displacement, 1.5 % on
rate.** (An earlier check gave 72.5 m / 0.63, within 4 %; that used the
nearest-distance estimator, and the signed shore-normal one lands closer to the
published QGIS figure.) Script 40 (spec:
`working/updates/NRG_script40_retreat_spec_2026-08-29.md`) asserts that
agreement as its own regression test, and cannot without this file.

**Do not use it in a retreat series.** Nothing in `_fixtures/` is a measurement
input. The modern series is `coast2006` / `coast2012` / `coast2020` — one
source, one method, three epochs.

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

## Google Earth Pro screen captures — the imagery series (46 files)

**What they are.** Screen captures of Google Earth Pro at 1920×1080, taken by
Martin Hollingham. **They are not orthophotos.** They are pictures of a rendered
perspective view, so they carry perspective distortion: absolute areas and
distances measured off them are approximate. Comparisons *between* frames at the
same viewpoint largely cancel it, which is why Script 41's canopy measure is a
comparative index rather than a fraction (D-097).

**Every imagery date, eye altitude and attribution below was READ OFF THE
RENDERED PIXELS on 2026-08-30**, frame by frame, not copied from a filename or
from the manifest's former blanket value. The rendered status bar is the
authoritative source for the date.

**Four viewpoints**, distinguished by the eye altitude and centre the frames
themselves print:

| viewpoint | eye alt | centre | files | what it shows |
|---|---|---|---|---|
| `vp1` | 1.79 km | 53°08'53.91"N 4°22'34.56"W | 12 | partial site: the forest block and its surroundings |
| `vp2` | 3.70 km | 53°08'39.92"N 4°21'58.07"W | 27 | the whole site |
| `vp2_2006` | 3.77 km | 53°08'38.76"N 4°21'57.52"W | 4 | the whole site, a *different* capture position — **not** pixel-registered with `vp2` |
| `vp3` | 6.30 km | 53°07'56.86"N 4°22'10.40"W | 2 | wide Caernarfon Bay, Llanddwyn to Abermenai Point |

`aerial31-3-2026.png` prints **2.00 km** and a centre 3 arc-seconds north of the
other eleven `vp1` frames — it is a shifted viewpoint. It is **left in `vp1`**,
where it already sat and where D-097 records the consequence (it matches only 5
placemarks and all four of its regions are withheld). The geometry is stated
rather than re-grouped, because re-grouping would change what Script 41 registers.

**`site*` frames come in PAIRS, and the `m` suffix means MARKERS.** The plain name
is markers **OFF**; `m` is the same view with the dipwell placemarks **ON**.
Verified on all 15 pairs by differencing each pair and inspecting the result, and
confirmed by eye on `site1-1-2006`, `site22-4-2017` and `site27-5-2010`. `aerial*`
frames carry markers **and** draw the green control polygon; `vp3` frames carry
markers and are unpaired.

**Role follows from that**: registration is done from the markers, so the
markers-ON frame is the **registration** frame, and the texture measurement needs
unoccluded canopy, so the markers-OFF frame is the **measurement** frame.
`aerial_manifest.csv` had this **inverted for all 15 site pairs** and was
corrected on 2026-08-30 — see the note below.

**Where they are held.** Per **D-081** and D-097's note of 2026-08-30 the captures
stay **out of the public repository**: the licensed source stays out, the
attribution travels with the derived product. They live on Martin's machine under
`data/geo/`, ignored by `.gitignore` (`aerial*.png`, `site*.png`, `seabed*.png`),
with `aerial_manifest.csv` tracked because it carries the dates, viewpoints and
attributions a reader needs. Script 41 skips with a notice when the imagery is
absent, its normal state in a clone.

### Attribution is per frame — six distinct rights-holders across the series

The manifest formerly asserted *"Bluesky, Infoterra Ltd & COWI A/S"* on every
row. Google Earth composites several providers and switches between them by date
and area, so one blanket value cannot be right across 2006–2026. Read off the
frames, the series carries:

| attribution | frames |
|---|---|
| Image © 2026 Maxar Technologies | 2010–2012 and 2017 imagery |
| Image © 2026 CNES / Airbus | 2018–2021 imagery |
| Image © 2026 Airbus | 2026 imagery |
| Image © 2026 Getmapping plc | 2009 imagery |
| Image © 2026 Bluesky, Infoterra Ltd & COWI A/S | 2006 and 2009 imagery |
| Image Landsat / Copernicus | 2006 `vp2_2006` / `vp3` frames, as a *second* line |

Some frames render **two** attribution lines (both 2006 whole-site frames, the
2006 seabed frame, and both 20-4-2009 frames); both are recorded. **Three frames
render no attribution line at all** — `aerial28-6-2018.png`, `site28-6-2018.png`
and `site28-6-2018m.png` — checked on a 190 px band, so this is a property of the
28 June 2018 layer and not a crop artefact.

### CORRECTED 2026-08-30: the manifest's `role` column was inverted

For all 15 `site*` pairs the manifest assigned `role = registration` to the plain
(markers **OFF**) frame. `41_canopy_cover.py` selects its registration frames with
`man = man[man["role"] == "registration"]`, so on the whole-site viewpoint **it was
attempting to register from frames with no markers on them.** Flipped on Martin's
instruction (*"the suffix m stands for marker! please flip the column"*).

**What the flip does to Script 41, measured rather than assumed:**

- **No citable value moves.** 44 emitted region-frame values before and after,
  identical keys, maximum difference **0.0**, and `41_report_numbers.csv` is
  byte-identical.
- **The whole-site viewpoint still withholds all 60 values**, for the reason
  D-097 already identifies: the registration bootstrap looks for the control
  polygon's outline, which the `site*` frames do not draw, so 52 of them fail with
  *"registration failed: only 0 placemark(s) matched"*. **The flip does not fix
  that and was not expected to.**
- **The evidence that the flip is nevertheless right** is in the eight frames that
  get past registration to the reference-separation test: their separation
  improves from **0.0019 / 0.0043 to 0.0124 / 0.0104**, three to five times
  better, because the index is now measured on clean frames instead of
  marker-covered ones. Still below the `CANOPY_MIN_REF_SEPARATION` floor of 0.02,
  so still withheld — the crown-resolution limit D-097 describes is unchanged.
- **The two `vp3` frames now enter the pipeline** (they previously had no manifest
  row) and contribute 8 further withheld values, all *"0 placemark(s) matched"*.

Total region-frame values 108 → **116**, withheld 64 → **72**, emitted **44 → 44**.

### CORRECTED 2026-08-30: structural faults in the manifest

* **`site20-4-2007.png` named a file that does not exist.** Its own note recorded
  that the 2007 in the filename was wrong and the frame prints 4/20/2009; the file
  had been renamed to `site20-4-2009.png` and the row never followed.
  **Repointed** to the file on disk.
* **Rows added** for every PNG that lacked one: `site20-4-2009.png`,
  `site27-5-2010.png`, and both `vp3` frames.
* The manifest now has **45 rows for 45 PNGs**; every row names a file that
  exists and every file has a row.

### FOUND 2026-08-30: `site27-5-2010.png` and `site27-5-2010m.png` are misdated

Both render **Imagery Date: 6/19/2011** and sit at the **3.77 km** viewpoint —
not 27 May 2010, and not `vp2`. Their `imagery_date` is recorded as the **rendered**
2011-06-19 and they are assigned to `vp2_2006`, which therefore holds four frames:
the two 1/1/2006 and these two. **Nothing was renamed**; the filenames are left as
they are and the disagreement is recorded here and in the manifest note.

This also resolves the two spellings of that name. **`site 27-5-2010.png` (with a
space) and `site27-5-2010.png` (without) are NOT duplicates** — different files,
different sizes (2 338 408 vs 2 354 319 bytes), different MD5s, and different
content: the spaced file genuinely renders **5/27/2010** at 3.70 km, the unspaced
one renders **6/19/2011** at 3.77 km. Both are kept and both have rows. Note that
the spaced file is therefore a `vp2` **measurement** frame whose `m` partner is
absent, and that `site19-6-2011.png` / `site19-6-2011m.png` render the same
6/19/2011 imagery at the *other* viewpoint.

Three filenames contain a **space** — `aerial 1-1-2006.png`, `site 20-4-2009m.png`,
`site 27-5-2010.png` — and are recorded exactly as they are on disk.

### The frames

| file | imagery date (rendered) | viewpoint | eye alt | markers | role | attribution (rendered) |
|---|---|---|---|---|---|---|
| `aerial 1-1-2006.png` | 2006-01-01 | vp1 | 1.79 km | ON | registration | Image © 2026 Bluesky, Infoterra Ltd & COWI A/S |
| `aerial11-9-2019.png` | 2019-09-11 | vp1 | 1.79 km | ON | registration | Image © 2026 CNES / Airbus |
| `aerial20-4-2009.png` | 2009-04-20 | vp1 | 1.79 km | ON | registration | Image © 2026 Getmapping plc |
| `aerial22-4-2017.png` | 2017-04-22 | vp1 | 1.79 km | ON | registration | Image © 2026 Maxar Technologies |
| `aerial24-3-2017.png` | 2017-03-24 | vp1 | 1.79 km | ON | registration | Image © 2026 Maxar Technologies |
| `aerial24-4-2020.png` | 2020-04-24 | vp1 | 1.79 km | ON | registration | Image © 2026 CNES / Airbus |
| `aerial26-5-2012.png` | 2012-05-26 | vp1 | 1.79 km | ON | registration | Image © 2026 Maxar Technologies |
| `aerial28-6-2018.png` | 2018-06-28 | vp1 | 1.79 km | ON | registration | NO attribution rendered in this frame (verified 2026-08-30 on a 190 px band) |
| `aerial29-7-2019.png` | 2019-07-29 | vp1 | 1.79 km | ON | registration | Image © 2026 CNES / Airbus |
| `aerial31-3-2020.png` | 2020-03-31 | vp1 | 1.79 km | ON | registration | Image © 2026 CNES / Airbus |
| `aerial31-3-2026.png` | 2026-03-31 **⚠ shifted viewpoint, 2.00 km** | vp1 | 1.79 km | ON | registration | Image © 2026 Airbus |
| `aerial8-7-2018.png` | 2018-07-08 | vp1 | 1.79 km | ON | registration | Image © 2026 CNES / Airbus |
| `seabed1-1-2006.png` | 2006-01-01 | vp3 | 6.30 km | ON | registration | Image Landsat / Copernicus; Image © 2026 Bluesky, Infoterra Ltd & COWI A/S |
| `seabed22-4-2017.png` | 2017-04-22 | vp3 | 6.30 km | ON | registration | Image © 2026 Maxar Technologies |
| `site 20-4-2009m.png` | 2009-04-20 | vp2 | 3.70 km | ON | registration | Image © 2026 Bluesky, Infoterra Ltd & COWI A/S; Image © 2026 Getmapping plc |
| `site 27-5-2010.png` | 2010-05-27 | vp2 | 3.70 km | OFF | measurement | Image © 2026 Maxar Technologies |
| `site1-1-2006.png` | 2006-01-01 | vp2_2006 | 3.77 km | OFF | measurement | Image Landsat / Copernicus; Image © 2026 Bluesky, Infoterra Ltd & COWI A/S |
| `site1-1-2006m.png` | 2006-01-01 | vp2_2006 | 3.77 km | ON | registration | Image Landsat / Copernicus; Image © 2026 Bluesky, Infoterra Ltd & COWI A/S |
| `site11-9-2019.png` | 2019-09-11 | vp2 | 3.70 km | OFF | measurement | Image © 2026 CNES / Airbus |
| `site11-9-2019m.png` | 2019-09-11 | vp2 | 3.70 km | ON | registration | Image © 2026 CNES / Airbus |
| `site19-6-2011.png` | 2011-06-19 | vp2 | 3.70 km | OFF | measurement | Image © 2026 Maxar Technologies |
| `site19-6-2011m.png` | 2011-06-19 | vp2 | 3.70 km | ON | registration | Image © 2026 Maxar Technologies |
| `site20-4-2009.png` | 2009-04-20 | vp2 | 3.70 km | OFF | measurement | Image © 2026 Getmapping plc; Image © 2026 Bluesky, Infoterra Ltd & COWI A/S |
| `site22-4-2017.png` | 2017-04-22 | vp2 | 3.70 km | OFF | measurement | Image © 2026 Maxar Technologies |
| `site22-4-2017m.png` | 2017-04-22 | vp2 | 3.70 km | ON | registration | Image © 2026 Maxar Technologies |
| `site24-3-2017.png` | 2017-03-24 | vp2 | 3.70 km | OFF | measurement | Image © 2026 Maxar Technologies |
| `site24-3-2017m.png` | 2017-03-24 | vp2 | 3.70 km | ON | registration | Image © 2026 Maxar Technologies |
| `site24-3-2021.png` | 2021-03-24 | vp2 | 3.70 km | OFF | measurement | Image © 2026 CNES / Airbus |
| `site24-3-2021m.png` | 2021-03-24 | vp2 | 3.70 km | ON | registration | Image © 2026 CNES / Airbus |
| `site26-5-2012.png` | 2012-05-26 | vp2 | 3.70 km | OFF | measurement | Image © 2026 Maxar Technologies |
| `site26-5-2012m.png` | 2012-05-26 | vp2 | 3.70 km | ON | registration | Image © 2026 Maxar Technologies |
| `site27-5-2010.png` | 2011-06-19 **⚠ filename date wrong** | vp2_2006 | 3.77 km | OFF | measurement | Image © 2026 Maxar Technologies |
| `site27-5-2010m.png` | 2011-06-19 **⚠ filename date wrong** | vp2_2006 | 3.77 km | ON | registration | Image © 2026 Maxar Technologies |
| `site28-6-2018.png` | 2018-06-28 | vp2 | 3.70 km | OFF | measurement | NO attribution rendered in this frame (verified 2026-08-30 on a 190 px band) |
| `site28-6-2018m.png` | 2018-06-28 | vp2 | 3.70 km | ON | registration | NO attribution rendered in this frame (verified 2026-08-30 on a 190 px band) |
| `site29-7-2019.png` | 2019-07-29 | vp2 | 3.70 km | OFF | measurement | Image © 2026 CNES / Airbus |
| `site29-7-2019m.png` | 2019-07-29 | vp2 | 3.70 km | ON | registration | Image © 2026 CNES / Airbus |
| `site31-3-2020.png` | 2020-03-31 | vp2 | 3.70 km | OFF | measurement | Image © 2026 CNES / Airbus |
| `site31-3-2020m.png` | 2020-03-31 | vp2 | 3.70 km | ON | registration | Image © 2026 CNES / Airbus |
| `site31-3-2026.png` | 2026-03-31 | vp2 | 3.70 km | OFF | measurement | Image © 2026 Airbus |
| `site31-3-2026m.png` | 2026-03-31 | vp2 | 3.70 km | ON | registration | Image © 2026 Airbus |
| `site4-4-2021.png` | 2021-04-04 | vp2 | 3.70 km | OFF | measurement | Image © 2026 CNES / Airbus |
| `site4-4-2021m.png` | 2021-04-04 | vp2 | 3.70 km | ON | registration | Image © 2026 CNES / Airbus |
| `site8-7-2018.png` | 2018-07-08 | vp2 | 3.70 km | OFF | measurement | Image © 2026 CNES / Airbus |
| `site8-7-2018m.png` | 2018-07-08 | vp2 | 3.70 km | ON | registration | Image © 2026 CNES / Airbus |

### `aerial_manifest.csv`

The tracked index of the series: one row per frame giving filename, imagery date,
viewpoint, role, attribution and a note. **Tracked deliberately** while the
imagery is not (D-081, D-097) — it carries what a reader needs without
redistributing a licensed basemap. Script 41 reads it through
`paths.AERIAL_MANIFEST` and filters on `role`.

Rewritten 2026-08-30: `role` flipped for the 15 site pairs, every attribution
replaced with the one rendered in its own frame, the dangling `site20-4-2007.png`
row repointed, and rows added for the four PNGs that had none. 45 rows, 45 files,
and every attribution in this section is a rendered reading rather than a gap.

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

*Corrected in place 2026-08-29.* This section was written on 2026-08-28 against a
four-epoch series that included `DCoast_2015.kml`. That line was withdrawn the
same day (register W64) once `coast2012.kml` made a single-source modern series
available and showed the 2015 line lying seaward of the 2012 one at 10 of 12
sampled longitudes. The withdrawal reached the decision log, the changelog and
the register and did not reach this file, which then stood for a day publishing a
retracted rate. The superseded rows and the corroboration claim built on them are
gone; what replaces them is below.

Re-running D-060's method (shore-normals at 25 m along the later line of each
pair, distance to the earlier) across the four epochs, single-source modern lines
throughout:

| interval | n | median | years | rate |
|---|---|---|---|---|
| 1899 → 2006 | 131 | 64.2 m | 107 | **0.60 m yr⁻¹** |
| 2006 → 2012 | 131 | 16.6 m | 6 | **2.77 m yr⁻¹** |
| 2012 → 2020 | 131 | 30.5 m | 8 | **3.81 m yr⁻¹** |
| 2006 → 2020 | 131 | 46.8 m | 14 | 3.34 m yr⁻¹ |
| **1899 → 2020** | 131 | 116.0 m | 121 | **0.96 m yr⁻¹** |

The modern series is internally additive: 16.6 + 30.5 = 47.1 m against 46.8 m
measured directly over 2006→2020, so the two sub-intervals and the span they
partition agree to 0.3 m.

**Monotonic acceleration across three consecutive intervals.** That is the
qualitative claim, and it is robust: 0.60 m yr⁻¹ across the twentieth century
against something of order 2–4 m yr⁻¹ recently. **Its magnitude is a separate
question and is open** — see the caveats below. Do not let the qualitative claim
ride on the quantitative one.

**A defect in `config.py`, and no corroboration.** Forgrave (2020) reports ≈50 m
of retreat, and `config.py` cites that same ≈50 m twice to incompatible windows:
at line 314 as 2014–2020 (giving `COAST_RETREAT_RATE` = 8.3 m yr⁻¹) and at line
411 as "since 2006" (giving `COAST_RETREAT_2005_2025_M` = 50 m). One quantity
cannot have accrued over both windows, and `config.py:413` already declines to
extrapolate 8.3 over twenty years on the grounds that it would overstate the
accumulation. **That defect stands on its own and is recorded.**

**What does not stand is reading Forgrave as corroboration of anything here.**
Read on the 2006–2020 window, ≈50 m sits against 46.8 m measured over that exact
window, about 6 % apart — and that agreement was offered, on 2026-08-29, as
support for the measured series. **Withdrawn.** If the measured field carries a
systematic offset (see the caveats below) then a newspaper figure agreeing with
it to 6 % is most likely either sharing the same indicator confusion — plausible
if it came from comparing photographs — or coincidence. Two unreliable numbers
agreeing is not evidence, which is the objection that retired the earlier
7.74-versus-8.3 claim in this same section, committed a second time with a
different pair. **No external source currently corroborates the modern series.**
Pye & Blott (2024) is the only remaining external measurement of this frontage
and it disagrees by roughly a factor of two, so dropping Forgrave as a mere
newspaper citation would not settle the question — it would remove the source
that happened to agree, and leave both `config.py` constants unsourced, one of
them a divisor in a published construction.

**Why this matters beyond the rate.** D-060 exists because the corpus carried two
coastal-retreat numbers that sat awkwardly together: a short-run 8.3 m yr⁻¹ and a
long-run 0.65 m yr⁻¹, with `config.py` warning that extrapolating the short one
overstates accumulation. The intermediate epochs show the transition, and the
tension resolves — but not as two ends of one series. It resolves because the 8.3
divides a 2006–2020 displacement by a 2014–2020 window. `config.py:413` already
declines to extrapolate 8.3 over twenty years on the grounds that it would
overstate the accumulation: the same objection, reached from the other side and
left unacted on.

**Consequences of the endpoint swap.** Substituting the 2020 line for the 2015
one as the modern endpoint leaves the long-run rate at **0.96 m yr⁻¹** — the
1899→2020 span never involved the 2015 line and is unaffected by its withdrawal.
The 0.63 m yr⁻¹ figure this section previously quoted was the 1899→2015 pairing,
retained below only as the reproduction check on the method.

**Method and status.** Reimplemented independently of QGIS in local
equirectangular metres about the site centroid; over 4 km at 53° N the projection
distortion is far below the 5.95 m georeferencing error and does not bear on the
result. The estimator is **nearest-distance**, which is biased low against true
shore-normal displacement and therefore cannot manufacture a hot rate.
**Validation: run against D-060's own pairing (1899 dune edge → 2015) it returns
72.5 m and 0.63 m yr⁻¹ against the published 75.2 m and 0.65 — agreement within
4 %,** so the method reproduces the original.

**This is INDICATIVE and NOT CITABLE.** Under D-006 a sensitivity becomes citable
only once it is a pipeline output; this is a session computation. To publish any
of it, the measurement needs to become a script with the lines as declared
inputs.

**Caveats that must travel with these numbers.**
- The 1899 line carries ±5.95 m of georeferencing error. Over a short interval
  that dominates — though it does not enter the 2006→2012, 2012→2020 or
  2006→2020 comparisons, which are modern-to-modern.
- The registration accuracy of the Google Earth lines is unrecorded, and Google
  Earth imagery georeferencing is typically a few metres. Over short intervals
  that is a large fraction of the signal. **This is the outstanding
  measurement**: digitising a fixed feature — a road junction, a building corner,
  the forest boundary — in the 2012 and 2020 imagery gives the apparent
  displacement of something that did not move, which is the registration error
  measured rather than assumed. That is the error bar the script should carry.
- **The modern series has a floor in it, and a shoreline does not.** Measured
  again on 2026-08-29 with *signed* shore-normal displacement rather than nearest
  distance, and restricted to the northing band all three modern lines span
  (1470 m, 113 normals): over 2006→2020 **every one of the 113 normals shows
  retreat**, from +24.8 m to +81.1 m. The least-eroding point on the frontage
  gives **1.77 m yr⁻¹**. Pye & Blott (2024) survey the same frontage and report
  **progradation in the north** with retreat concentrated at the southern Twyni
  Penrhos end, up to 16.3 m over 2013–2022 — **≈1.8 m yr⁻¹ at the most active
  point**. Our minimum is their maximum, and where they measure advance we
  measure 40–50 m of retreat. The natural reading is a near-constant **offset of
  order +25 m between the 2006 and 2020 lines** on top of a true signal of
  roughly ±16 m, which is what produces no negatives, a floor above zero and a
  gradient too weak to match either survey. **Until that is resolved the modern
  rates should not be quoted at all** — not 3.81, not 3.34, not 3.50. Full
  working: `working/updates/NRG_retreat_alongshore_probe_2026-08-29.md`. Note
  the estimator matters here and nothing else did: nearest distance is always
  positive, so it cannot see a floor, a sign change or progradation, which is why
  this was invisible until 2026-08-29.
- **The indicator mismatch against Pye & Blott is now measured, not asserted.**
  Sampling the 2 m NRW LiDAR DTM along the same 117 shore normals (2026-08-29),
  **the 2020 line lies 34 m landward of the DTM's 3 m contour, 20 m landward of
  its 4 m contour and 86 m landward of its 0.5 m contour**, sitting at ≈9 m AOD
  — 20–34 m landward of anything a dune toe could mean, and 5–6 m higher up the
  profile. Pye & Blott's sequence is explicitly a **dune-toe** sequence. **These
  are different features on the profile**, and retreat measured at a mid-face
  contour agrees with retreat measured at the toe only if the profile translates
  without changing shape. **This comparison is sound because the line and the
  surface are three years apart**; the ones below are not.
- **The elevations of the 2006 and 2012 lines on this DTM are withdrawn, and so
  is the argument built on them.** A first version of this bullet reported all
  three lines' elevations — 1.86 / 3.64 / 9.36 m AOD — and read their being
  **monotonic in age** as evidence that the displacements are real retreat rather
  than indicator drift. **That is void.** There is one surface here, dated after
  all three lines: sampling it at a 2006 position gives the 2023 elevation of
  that ground, not the elevation at which the line was drawn. The monotonic
  ordering is then near-tautological — three positions ordered in space, read off
  one surface that falls away seaward — and carries no information about what
  each line was digitised at. **The DTM test says nothing either way about drift
  inside the series.** Drift is untested, not weakened; the floor is unexplained;
  and the fixed-feature control is the only discriminating test available.
  (The KMLs' own altitude values are not involved — they are zero in the files,
  and the raster was sampled at the lines' horizontal positions. The fault is
  one DEM against four dates, not the KML encoding.)
- **An incidental corroboration.** `20_spatial_figures.py` builds its erosion
  front as the 0.5 m AOD waterline offset `COAST_DUNE_OFFSET_M` = 100 m inland.
  Measured here, the 2020 line sits **86 m** landward of the 0.5 m contour — so
  the assumed 100 m offset lands within ~14 m of the independently digitised
  line. The constant is supported. It also means that front sits at ≈9 m AOD,
  well up the dune, which is where the erosion field is being applied.
- **The acceleration is not an artefact of the intervals covering different
  lengths of coast.** Restricting all three to a common frontage by *extent*
  moves nothing by more than 0.15 m yr⁻¹ (2.50 / 3.91 / 3.50 against 2.77 / 3.81
  / 3.34). Restricting by *hit-success* instead does not work — `coast2012.kml`
  runs ~400 m further south than the other two, and normals in that gap strike
  its unmatched tail and return a spurious hit. A pass on 2026-08-29 that made
  that mistake reported 22.8 m of progradation at the southern end; there is no
  such progradation, and the report is withdrawn.
- **A median is not a comparison to a profile.** The long-run run showed the
  alongshore rate varying from 1.18 to 0.10 m yr⁻¹, and the median hides that.
  Any comparison against a published profile figure must be made at the
  shore-normal nearest that profile.
- Short intervals amplify everything: a few metres of registration difference
  becomes a whole m yr⁻¹.

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

**Done, 2026-08-29 (T-17, D-084).** Centralised onto a single `config.py`
constant and renamed `CLEARFELL_DATE`, "intervention date" being too vague for a
constant that fixes the before/after split of the clearfell BACI. 152 occurrences
across 22 files, with the environment-adequacy control applied: all 19 affected
scripts reproduced byte-identical outputs, 483 of 483. The four intervention
dates now live once, in `config.py`, as ISO strings. The earlier note here said
this was "deliberately not attempted from the desktop bridge, where 31 of 71
`src/` scripts cannot run at all" — that constraint was untested and wrong; it
was six missing packages.

---

## `sea_ridge.kml` — the nearshore ridge digitisation (added 2026-09-01)

**Martin's own digitisation, drawn by eye in Google Earth Pro 7.3.7.1155 and
supplied on 2026-09-01.** One placemark, `sea ridge`, holding a MultiGeometry of
**four polygons**: the dark seabed features he can see off the Newborough
frontage. Not derived from any pipeline output and not traced from a licensed
product — it is an observer's outline over a basemap, so unlike the screen
captures it carries no third-party rights and belongs in the repository (D-081
governs the imagery, not a digitisation made from it).

| ridge | area | centroid (OSGB) | extent | approx. axis | bearing |
|---|---|---|---|---|---|
| R1 | 11.07 ha | E 240296 / N 363075 | E 240056–240597, N 362836–363301 | 400 × 176 m | 51.1° |
| R2 | 9.31 ha | E 240399 / N 362820 | E 240151–240749, N 362480–363153 | 537 × 113 m | 38.7° |
| R3 | 18.75 ha | E 240610 / N 362655 | E 240214–241018, N 362333–363007 | 515 × 205 m | 47.8° |
| R4 | 22.55 ha | E 241106 / N 362078 | E 240501–241699, N 361686–362390 | 775 × 173 m | 57.9° |

**Total 61.68 ha**, union bounds E 240056–241699, N 361686–363301.

**Two things follow from the geometry and are worth recording here rather than
being rediscovered.** The four bearings span **38.7° to 57.9°**, a sub-parallel
set; the 2017 shoreline bears 118°, so all four are oblique to shore-normal and
none is shore-parallel. And **R4 lies almost entirely outside the `site` (vp2)
frame window** — only about a twentieth of it is imaged there — so it can only
be measured on the wide `seabed` (vp3) viewpoint. Any analysis that uses vp2
alone will silently under-sample it.

Measured against each frame's own open-water level (90th percentile of the
imaged sea), all four read darker than open water in **every** usable frame of
both viewpoints; R3 is the strongest, reaching 0.199 of open water in its
darkest quartile on 22 April 2017. The full table is in the W117 register entry.
