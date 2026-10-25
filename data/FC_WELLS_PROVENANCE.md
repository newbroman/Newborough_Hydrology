# Forestry Commission wells, 1989–95 — provenance

Two files, added 2026-10-25, kept for reference only. **The FC wells lie outside the study area** (Martin, 2026-10-25 22:19: "The FC wells aren't in my study area. I did measure some of those points early on, but not since 2010."). No pipeline step reads them, and they are not network data.

## `fc_wells_1989_95_levels.csv`
- **What:** monthly readings from March 1989 to May 1995 (75 months). Tidy form: `month`, `series`, `value`.
- **Series:**
  - Forestry Commission wells `1`–`19`;
  - four ponds: `L.P.M.`, `Canada`, `Newt P.`, `D.S.Pool`;
  - FC's monthly `RAINFALL`, actual evaporation `FCAET` and their difference `Wb`.
- **Source:** the "FC Well records" sheet of `data/fc and ccw waterlevels.ods` (Martin Hollingham's workbook), header row and dated rows only. The sheet's derived blocks below ("Forest excluding pools", "Wells 11,12,19", "Wells 7+9") are not carried.
- **Second copy:** Laurence Jones sent the same records on 2026-10-25 as `fc_data_89-95.xlsx`. It is identical in every dated row checked.
- **Units are not stated in the sheet:**
  - the wells read negative, −310 to −1,570, apparently mm below ground;
  - `L.P.M.` reads positive, apparently a pond-gauge level;
  - `D.S.Pool` repeats well 19 in the rows checked.
  - These units are to be confirmed before any use.

## `fc_wells_1989_95_locations.csv`
- **What:** positions of FC wells 1–12, 14, 15 and 17, and of Canada and Newt pools. Also listed: the University of Lancaster wells (NF2, NF2b, well 3) and CCW well 5/NF5, which share the KML's forest group.
- **Source:** Martin Hollingham's Google Earth placemarks, `data/geo/DIPwells.kml` (the network's 109 placemarks), received 2026-10-25. WGS84 is converted to OSGB (EPSG:27700) by pyproj. Each placemark's note is kept: most FC wells are "lost"; FC well 6 was found on 2010-01-08; FC well 12 is NF1, read 2006–08.
- **Open points:**
  - two placemarks are both named "FC well 17". The one in line with wells 14 and 15 may be 16; Martin to confirm;
  - no position is given for FC wells 13, 16, 18 or 19, nor for the L.P.M. and D.S. Pool ponds.
- **Where they lie:** mainly the north-west forest, 360 m (wells 7–9, from CEH12) to 1.5 km from the nearest modern network well. None is co-located with a modern well.

## `quadrat_dipwell_pairs_jones.csv` (same batch)
- **What:** Laurence Jones's pairing of quadrats Q47–Q49 with dipwells CEH35, CEH38/CEH4 and CEH36. Q35 is near no dipwell.
- **Source:** his email of 2026-10-25.
- **Use:** for the Sentinel and MSL work (Martin, 2026-10-25 22:01).
