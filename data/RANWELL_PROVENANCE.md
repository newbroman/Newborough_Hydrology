# Ranwell (1959) water-table data — provenance of the digitised files

Source: Ranwell, D. (1959) Newborough Warren, Anglesey: I. The dune system and dune slack
habitat. *J. Ecol.* 47(3), 571–601. Read from the JSTOR scan in `literature/` (in copyright,
never committed; D-081). The files below are factual data recovered from its printed figures;
no figure image is committed. Digitised 2026-09-08 (Cowork session `01PhSvhMMGSWW9UnSFdTK5GU`,
configured `claude-fable-5-1`); method and accuracy per file.

Ranwell printed **no table of readings**. Seventeen pipes (1 m galvanised gas pipe, driven to
about 95 cm; readings by dipstick, so depths greater than about 95 cm are not observable),
levelled to OD in 1951 and re-surveyed 1953 (agreement within a few cm). Readings at least
fortnightly February 1951 – August 1953, none June–September 1952. Site OD heights are in
`geo/ranwell_1959_sites_martin.csv` (his Fig. 3 table). **No BS-slack site (2, 5, 6, 14, 15)
has any printed series** — Figs 4 and 7 cover PL (1, 16), CG (4, 11, 12, 13) and AS (8, 18) only.

## `ranwell_1951_53_water_levels.csv` — Fig. 4, the time series (146 readings)

Sites 1 and 4 for 1951, 1952 and 1953 (to August); Site 8 for 1951 only. Page rendered at
300 dpi (`pdftoppm`); each year's panel cropped; hollow markers (triangle = Site 1, circle =
Site 4) found as enclosed white connected components and classified by hole shape; crosses
(Site 8) by normalised template match (threshold 0.68); fifteen occluded or overlapping markers
added by hand from 2× gridded zooms; text glyphs and legend markers removed by position. Axes
calibrated on the printed tick marks: 1951 panel 0 cm at row 43, 100 cm at row 432 (3.89 px/cm),
Jan 1 at column 88, 117.4 px per month; 1952 panel 47/436, 82/117.7; 1953 panel 43/439.4
(110 cm at 479), 73.5/118. Day of year is linear within the panel (month lengths are not
resolved by the figure). Columns: `site_no, date, depth_below_surface_cm, level_m_od`
(= Fig. 3 height − depth), `source, px_x, px_y` (pixel position in the panel crop, so any
point can be re-read). **Accuracy about ±1 cm and ±2 days**; a few points where two markers
overlap (late March 1953, both sites) are ±2 cm. Check figure:
`ranwell_fig4_digitised_check.png` (project store / outputs), each panel re-plotted beside the
original.

## `ranwell_1951_53_monthly_ranges.csv` — Fig. 7, monthly ranges (7 sites × 12 months)

Sites 1, 4, 11, 12, 13, 16, 18. Each month is one open bar (two thin verticals) giving the
range of all readings in that calendar month over 1951–53 pooled; the years are not separated
in the figure and are not guessed here. Bars found as vertical dark runs after a 9-px vertical
closing, paired by proximity (the two verticals of every bar agree within 6 px, recorded in
`line_pair_disagreement_px`); y-axis from the printed 20-cm ticks (≈2.67 px/cm), the 0 cm row
being the dashed soil-surface line; month from the x-axis tick bins. Negative depths are levels
**above** the surface (Site 12 floods to about 20 cm in winter). Columns: `site_no, month,
depth_min_cm, depth_max_cm, level_max_m_od, level_min_m_od, line_pair_disagreement_px, source`.
**Accuracy about ±1.5 cm.**

**Cross-check, independent digitisations of the same readings.** For Sites 1 and 4 the monthly
extremes of the Fig. 4 series agree with the Fig. 7 ranges to within ±4 cm in 20 of 24 months;
where Fig. 7 is wider (Site 1 Jul/Aug/Dec; Site 4 Apr/Jul) Fig. 4 plots fewer readings than
Fig. 7 pools (the 1952 gap, and single points). Two disagreements are in the figures
themselves, not the digitisation: Site 1 January (Fig. 4 shows 30–34 cm in January 1953, Fig. 7
caps the month at 25 cm) and Site 1 October (Fig. 4 minimum 67 cm, Fig. 7 50 cm). Neither
changes a mean by more than 2 cm.

## `ranwell_1950_53_parc_mawr_rain.csv` — Fig. 2, monthly rainfall at Parc Mawr (48 months)

Bar chart, four annual panels; bars at uniform 39-px pitch from the axis; top of each bar =
lowest dark row scanning up from the baseline; y from the printed 40-mm tick (≈0.97 px/mm; the
1950 panel's ticks are slightly wider, 1.01 px/mm). **Digitised annual totals against the
printed ones: 1951 999 vs 987 mm, 1952 718 vs 707, 1953 698 vs 690 (within 2%); 1950 1109 vs
1037 (7% high — the bars as drawn sum to more than the printed total; no bar is misread, so
the discrepancy is Ranwell's; 1950 is spin-up only and the flag stays).** Gauge: 5-in funnel,
9 in above ground, Parc Mawr Forestry Nursery, on fixed dune. Use: a check on the RAF Valley
forcing over the hindcast years (Script 44 `44_06_climate_check.csv`), not a forcing.

## Not digitised

Fig. 5 (diurnal, August 1951, Sites 3, 7, 8, 9 — hours, not dates); Fig. 6 (dune-foot water
table profile, arbitrary datum); Fig. 8 (soil moisture). Text values used directly: annual range
70–100 cm at all sites; winter flooding 1950–51 (pools to 5000 m² at Clwt Gwlyb, 1.5 m deep in
younger slacks); a 2.5 cm rain event 10–13 April raising slack water tables about 20 cm; no
tidal signal at Site 10.
