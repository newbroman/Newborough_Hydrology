# Which T41 well is van Willegen's "T41"? — and how her levels were bucketed (2026-09-28)

Source: `data/Ecohydrology_dataset.xlsx` (van Willegen et al., Mendeley doi:10.17632/p4xvb6xxp9.1),
sheet Hydrology_metric_YearB, quadrats T41A-4, T41B-2/5/7/8, T41C-3, T41D-1/6, years 2010-2019.
Compared with `outputs/01_wells_all.csv` masked to `01_wells_provenance.csv == "measured"`.

## Result 1 — the quadrat letter is the well
Each quadrat's annual statistics equal the SAME-LETTER well's record plus a constant quadrat
offset (the offsets in `26_table_s7_2_vw_datum_offsets.csv`). Residual after the offset,
statistics Min / MAX / Mean / Median / P10 / P90 / P95, 10 years each (70 values):

| Quadrat | exact matches (±1.5 mm) | best alternative |
|---|---|---|
| T41A-4 | 70 / 70 vs T41a | 4-well mean: 12-165 mm residual SD |
| T41C-3 | 70 / 70 vs T41c | |
| T41D-1 (and -6) | 70 / 70 vs T41d | |
| T41B-2 (and -5/-7/-8) | 62 / 70 vs T41b | mismatches only in hydro years 2013 and 2014 (below) |

Not an average of the transect, and not T41b alone: van Willegen's single Table 1 station "T41"
is the four-well transect, each quadrat tied to its own well. Table 1's "7" is the seven vegetated
quadrats (T41B-8 has levels but no relevés in meanEbF).

## Result 2 — her bucketing is the pipeline's (Script 01) bucketing
- Monthly values are Script 01's field-convention buckets, including its handling of months with
  two readings (a keep-first or keep-last reading of the raw file fails in 2016 and 2018).
- Interpolated months are NOT used: she leaves the gap (Jan 2017 on all four wells; Sep 2011 on
  T41b). Her 2017 means are over 11 months.
- Her year = bucketed May(Y-1)..Apr(Y) = readings dated 1 June(Y-1)..31 May(Y), labelled by the end year.
- Her seasons are reading-dated: "Mean Spring" = bucketed Feb-Apr (= readings dated Mar-May),
  Summer = bucketed May-Jul, Autumn = Aug-Oct, Winter = Nov-Jan. 10/10, 9/9, 8/8, 9/9 exact.
  So her month labels are one month later than ours (the old nearest-month convention).
  D-189 (MSL_SPRING_MONTHS = (2, 3, 4)) is confirmed.

## Hydrology-year start — RESOLVED (D-207: "match the hydrological year", config 1.71.0 sets 5)
`config.MSL_HYDRO_YEAR_START_MONTH = 6` in bucketed months is readings dated 1 July-30 June, one month
later than her (and Curreli's stated) 1 June-31 May. Spring MSL5 is unaffected (Feb-Apr falls in
the same year either way); the Curreli annual minimum (D-190) is not: across the network 174 of
1185 complete well-years change, median 50 mm, max 140 mm. D-189's reasoning would set it to 5.

## T41b, winters 2012/13 and 2013/14 — EXPLAINED (Martin: "I went back and levelled the wells and applied a correction"; her copy predates the correction, the committed log is corrected)
Her T41b is higher than the committed log in those two winters only; everything else matches.
2013/14 solves uniquely: Jan-Mar 2014 (bucketed) +80 mm (hers 0.27/0.28/0.27 m vs log 0.19/0.20/0.19).
2012/13 is not unique; her top three values are 0.27/0.30/0.31 m against the log's 0.20/0.21/0.28
(an ~+80 mm rise in most of Nov-Feb). T41b has no upstand (pipe top at ground), so these are
flood depths above ground; the log's repeated 0.19-0.21 m looks like a ceiling. The log and
`data/Newborough_well_records_pipeline.ods` agree with each other; her copy of the log differs.

## Consequence applied
config 1.71.0: VW_QUADRAT_WELLS includes t41a, t41b, t41c, t41d (20 wells, 17 stations);
VW_LOCATION_ONLY_WELLS = (). Script 26 1.19.0 follows.
