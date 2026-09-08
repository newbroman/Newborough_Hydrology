# Spec — Script 43 v2.0.0: Ranwell (1959) sites placed by hand over a georeferenced sketch, height-checked against the DEM, basin-tested (W95; D-140 revisited)

**Provenance.** Cowork session `01PhSvhMMGSWW9UnSFdTK5GU` · configured `claude-fable-5-1` ·
2026-09-08, amended the same day after the slack-floor sweep. Supersedes the Route A/B design of
`NRG_spec_script43_2026-09-06.md` (D-140) in the way §1 records. Design → sign-off → build.
**Amendment 2026-09-08b:** Route T is a basin test, not an outline test (§2, §3); the per-group
slack floors are a diagnostic layer at documented Δ (§2); §0 states what the script adds to the
report, which Martin asked and which the spec did not answer.

## 0. What this adds to the report — and what it does not

The 2026-08-22 session (handover `HANDOVER_cowork_NRG_2026-08-22_ranwell_and_coast.md`) already
settled that **none of the four Ranwell results the report uses needs the site positions**: the
unchanged 70–100 cm seasonal range, the CCW cross-validation, the 1950s hindcast anomaly, and
D-059. It abandoned per-site comparison because positional error exceeded the signal. Script 43
therefore adds to the report exactly one of the following, and Martin chooses which:

- **(i) Nothing beyond provenance.** The sites CSV, the overlay figure and §S.23b make the
  placement reproducible and record that Ranwell's heights agree with the modern DEM to
  levelling error while his outlines do not. That is a Supplement matter; the report gets at most
  a sentence in the historical-context passage of report6 (which still cites Ranwell for "a
  well-documented trend of water table decline" — a loose end flagged on 08-22 that this work
  bears on directly, since the only epoch contrast the record supports is a recovery).
- **(ii) A slack-level absolute comparison, 1951–53 against the modern record.** The objection of
  08-22 was positional: metre-scale relief within slacks. The height check now shows that each
  site's *ground level* is known to about ±0.13 m (offset +0.06 m), and the basin test shows which
  modern wells share each site's basin. Within one slack basin the water table is close to flat,
  so the mean 1951–53 water level at Ranwell's sites, referred to OD through his levelled heights,
  can be set against the modern wells in the same basin without pinning pipes to pipes. Four
  basins (AS, BS, CG, PL), one number each, with the 1950s hindcast anomaly (−0.021 m) as the
  expected climate-only difference. This is the only version of Script 43 that produces a report
  result; it needs Ranwell's fortnightly water-level table transcribed (nine pages, `store/`),
  which is not done.

Recommendation: build v2 as (i) now — it is what the sweep has already produced — and open (ii)
as its own register item with the transcription as its first step, to be done only if the report
wants a 1951 absolute-level statement. Nothing in (i) is wasted by (ii); (ii) adds a Script 43b
or a second phase.

## 1. What changed since D-140, and why the method moves

D-140 registered Ranwell's Fig. 3 by a similarity transform (Route A: one hard point, the scale
bar, rotation assumed grid-north-up) and used the tabulated OD heights as a check (Route B).
On 2026-09-07 Martin overlaid the sketch on a georeferenced base and found it **non-metric**: a
field sketch, topologically right (which slack, what is beside what) but not rigidly or affinely
registrable. Route A's placements were 60–460 m from the sites' true slacks; the assumed rotation
was the largest part of it. D-140's Revisit-if named exactly this event.

What replaced it, in order: (i) Martin georeferenced the sketch as a warped GeoTIFF
(`ranwell_map_modified.tif`, EPSG:27700, 2.23 m/px; in-copyright, gitignored); (ii) the 17 numeral
positions were read off it (`ranwell_1959_sites_georef_px.csv`), which recovered sites 2, 3 and 7
(the sketch's "37" beside 18) and put every site inside the slack the sketch shows it in;
(iii) Martin then hand-placed all 17 in Google Earth against his slack and ridge outlines —
`MARTIN-RANWELL-WELLS.kml` + `R9.kml`, committed as **`ranwell_1959_sites_martin.csv`** (numbered
by nearest-neighbour to (ii); R9 supplied separately); (iv) the DEM was compared with Ranwell's
tabulated heights at those points: with one global datum offset fitted on gentle ground
(**+0.06 m**), 13 of 17 sites already sat within ±0.3 m and every residual is within ±0.13 m
after moves of 2–11 m — except sites 1 and 12, which the heights move about 40 m onto a flank.
The heights **corroborate** the hand placement; they cannot refine position within a flat slack
floor, and the output says so per site.

(v) **The slack-floor sweep (2026-09-08).** DEM watershed segmentation (10 m Gaussian smoothing,
1.0 m h-minima markers) reproduces the sketch's grouping of sites into basins for 15 of 17 (R10
sits in its own small coastal basin; R11 on the CG/PL divide). Flooding each group from a
per-site local floor (5th percentile within 100 m) by Δ = 0.75, 0.5, 0.4, 0.3, 0.15, 0.05 m
showed that only AS — a closed trough — resolves into a discrete slack with a DEM-defined margin.
BS, CG and PL are sections of continuous low ground along the slack corridors: at every Δ the
flood is bounded by the search reach, not the ground, and below 0.3 m it strips the flanks the
sites stand on (0.15 m: seven sites 3–14 m off; 0.05 m: PL loses both). R12 and R13, drawn in a
discrete slack on the sketch, sit in one corridor on the ground. **Ranwell's slack outlines are
therefore not recoverable from the DEM outside AS**, and the sketch's slack shapes carry no more
metric information than its site positions do. Martin's reading, 2026-09-08.

## 2. Routes in v2

| Route | Role in v2 | Inputs |
|---|---|---|
| **M (headline)** | Martin's hand placement over the georeferenced sketch | `data/geo/ranwell_1959_sites_martin.csv` (17 rows: site_no, sketch_slack, E, N, height_m_od, source) |
| **H (height check + refinement)** | global offset δ on gentle ground; per-site cost minimisation of (Δz/σ_h)² + (d/σ_d)² within R; resolvability flag | `newborough_dem.tif`; `RANWELL_H_SIGMA_M` = 0.15, `RANWELL_D_SIGMA_M` = 40, `RANWELL_H_SEARCH_M` = 80, `RANWELL_GENTLE_SLOPE` = 0.05, `RANWELL_FLAT_CELLS` = 400 |
| **T (topology — basin test)** | DEM watershed basins; each site's basin id; sites that share a basin against the sketch grouping (`sketch_slack`); ridge crests = basin divides. Pass = every site in a `sketch_slack` group shares a basin with at least one other member of the group, or is in a basin adjacent to one (R10, R11 are the documented exceptions). | `newborough_dem.tif`; `RANWELL_DEM_SMOOTH_M` = 10.0, `RANWELL_BASIN_HMIN_M` = 1.0 |
| **F (slack floors — diagnostic)** | per-site local floor (5th percentile within `RANWELL_FLOOR_WINDOW_M` = 100) + `RANWELL_SLACK_DELTA_M` = {AS: 0.75, BS: 0.3, CG: 0.3, PL: 0.3}, clipped to the group's basins and to `RANWELL_SLACK_REACH_M` = 300 of the sites; per group a flag `bounded_by` = `dem` \| `reach` | as T |
| **A (retired, kept as diagnostic)** | the similarity registration of v1, run and written so the record shows how far it was wrong | as v1 |

The Δ values are the ones at which every site of the group stands on its floor (0.3 m: R1 alone
8 m off); they are documented constants, not fitted ones, and §S.23b says why they differ between
AS and the rest. Martin's traced outlines (`ranwell_features.kml`, `ranwell_ridge.kml`) are drawn
on the overlay for comparison only — no test reads them.

Route B of v1 is absorbed into H; the numeral positions read off the GeoTIFF (ii) are kept as an
input column (`georef_easting/northing`) so the CSV shows the hand move from them.

## 3. Outputs (`outputs/43_ranwell/`)

- `43_01_ranwell_sites.csv` — one row per site (17): `site_no, sketch_slack, easting, northing`
  (M), `georef_easting, georef_northing, hand_move_m`, `height_m_od, dem_m, resid_m,
  resid_after_offset_m, refined_easting, refined_northing, refined_move_m, refined_resid_m, slope,
  matching_cells_within_R, resolvability` (`flank` | `flat_floor` | `unconstrained`) (H),
  `basin_id, basin_shared_with_group, dist_to_slack_floor_m` (T, F), `routeA_easting,
  routeA_northing, routeA_error_m` (A), `nearest_well, nearest_well_dist_m, nearest_well_same_basin`.
- `43_02_nearest_well.csv` — from Route M positions, three nearest, with `same_basin` per pair.
- `43_03_registration_diagnostic.csv` — one row: `datum_offset_m`, its MAD, n gentle sites, σ_h,
  σ_d, R, `routeA_rms_error_m`, `n_sites_basin_consistent` (of 17), the exceptions by site_no.
- `43_04_overlay.png` — DEM hillshade, basin divides (black), Route F floors by group, Martin's
  traced outlines (thin), Route M points labelled, refined points, Route A greyed with error
  vectors, modern wells.
- `43_05_ranwell_sites.geojson` — Route M positions with all columns.
- `43_06_slack_floors.geojson` — Route F polygons, one feature per group with `delta_m`,
  `floor_m`, `area_ha`, `bounded_by`; and the basin divides as a second layer.
- `43_report_numbers.csv` — `ranwell_sites_total` 17, `ranwell_datum_offset_m`,
  `ranwell_sites_within_0p3m`, `ranwell_routeA_rms_error_m`, `ranwell_sites_basin_consistent`,
  `ranwell_sites_flank`, `ranwell_modern_wells_with_analogue` (same basin and within
  `RANWELL_ANALOGUE_RADIUS_M`).

## 4. Records

- `SCRIPT_LEDGER` row 43 (2.0.0; new inputs; Emits 43_01–43_06; Cited MS).
- `GEO_PROVENANCE.md`: entries for `ranwell_1959_sites_martin.csv`, `ranwell_1959_sites_georef_px.csv`,
  `ranwell_features.kml`, `ranwell_ridge.kml`; the GeoTIFF/PNG described as local-only (D-081).
- **§S.23b rewritten** (MS frozen; `REASON=` the changelog): §1 in the seven-concern form, ending
  with (v): heights corroborate, outlines do not resolve, AS the exception; "positions are
  provisional" replaced by "positions are Martin's hand placement, corroborated by Ranwell's
  heights and by the DEM basin structure". Numbers by key.
- **D-140 amended** (dated bullet): sketch found non-metric 2026-09-07; Route A retired to a
  diagnostic; Route M + H + T(basin) + F adopted 2026-09-08; slack outlines found unrecoverable
  outside AS. Revisit-if: a metric survey of Ranwell's pipe positions turns up.
- W95 register row: closed once §S.23b lands. **New row for §0 (ii)** if Martin wants it, first
  step the transcription of the 1951–53 table.
- report6: the "well-documented trend of decline (Ranwell, 1959)" sentence — a live-document
  edit, Martin's wording — is the one place the report changes under (i).

## 5. Build and verification

1. `config.py` constants (§2); `paths.py` for the new inputs, the renamed ridge KML, and 43_06.
2. `43_ranwell_sites.py` 1.0.1 → 2.0.0: Route M loader (17 rows, hard fail on a missing site,
   height or `sketch_slack`); Route H as the 2026-09-08 bridge prototype (numpy on the DEM
   window); Routes T and F as the 2026-09-08 cloud prototype (`/tmp/slacks2.py`: scipy.ndimage +
   scikit-image watershed; both already used elsewhere in the pipeline — check `environment.json`
   before adding scikit-image as a dependency, otherwise implement the watershed with
   `scipy.ndimage` only); Route A kept as a function, output columns prefixed.
3. Bridge cannot run it. Verification on the L14: Route H reproduces the prototype table (offset
   +0.06, sites 1 and 12 moves ≈ 44 / 42 m, residuals ≤ 0.13 m); Route T gives 15/17 basin-
   consistent with R10 and R11 the exceptions; Route F reproduces the sweep at Δ = 0.3/0.75
   (BS 16.8 ha, AS 6.5, CG 27.9, PL 22.6; R1 8 m off); Route A errors reproduce the 60–460 m
   shifts. `ms_chapters`, `ledger_lint`, `record_basis` untouched (tier D, no fit).
4. Changelog; §S.23b; D-140 amendment; register; GEO_PROVENANCE.

## 6. For Martin

- (i) or (ii) in §0.
- Rename `ranwell ridge.kml` → `ranwell_ridge.kml` (or I do it in the build).
- Whether scikit-image may join the environment or the watershed goes to scipy only.
