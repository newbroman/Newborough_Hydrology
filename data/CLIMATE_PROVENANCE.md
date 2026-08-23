# `RAF_Valley_Climate.csv` — provenance and licence

Companion to `COASTLINE_PROVENANCE.md`. Written 2026-08-23 because the file had
none, and a climate record with no stated source cannot be defended under review.

## Source

| | |
|---|---|
| **URL** | `https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/valleydata.txt` |
| **Product** | Met Office **Historic Station Data** — monthly station series |
| **Station** | Valley (Anglesey) |
| **Grid / coordinates** | 230800E 375800N; lat **53.252**, lon **−4.535**; **10 m amsl** |
| **Record in the source** | December 1930 to July 2026 (the most recent months marked *Provisional*) |
| **Record in this project** | December 1930 to the corpus cut-off; 1143 monthly rows |
| **Confirmed by** | source header and first data row read 2026-08-23 and matched against `data/RAF_Valley_Climate.csv` — Dec 1930 reads 8.6 / 5.5 / 0 / 130.3 / 31.5 in both |

**This is not MIDAS Open.** The two are different products with different QC and
different provenance, and the columns here (`Max Temp / Min Temp / af Days /
Rain (mm) / Sun (hrs)`, rows keyed `Dec 30`) are the Historic Station Data
format. A reviewer recomputing PET from MIDAS may not reproduce these values
exactly. Cite the route actually used.

## Licence

**Open Government Licence v3.0**, which permits redistribution by a third party.
Two conditions:

- **Attribution.** "Contains public sector information licensed under the Open
  Government Licence v3.0." © Crown copyright.
- The **derived** series — Thornthwaite PET, the cumulative water balance — are
  this project's own work and are ours to license. The raw monthly observations
  are Crown copyright under OGL.

So the climate inputs are depositable without seeking permission. That is worth
stating in the data-availability statement, since it is settled while the NRW
position on the 1989–96 dipwell block is not.

*Licence reading, not legal advice.*

## What the source's own quality flags mean, and what became of them

The source header declares three conventions:

- `*` after a value — **estimated**
- `---` — **missing** (more than 2 days missing in the month)
- `#` on sunshine — automatic Kipp & Zonen sensor rather than Campbell Stokes

Counted in the source on 2026-08-23, the whole 95-year file contains **exactly
one** of each of the first two:

| flag | column | month | reaches the pipeline? |
|---|---|---|---|
| `*` estimated | sunshine | Oct 2022 | **no** — sunshine is not read by Script 01 |
| `---` missing | rainfall | **Jun 1941** | **yes**, and see below |

Temperature and rainfall carry no estimated values anywhere in the record. That
is a cleaner input than this project has any right to expect and is worth knowing
before anyone goes looking for a data-quality explanation of a result.

## One defect, found here and fixed on 2026-08-23

`src/01_data_prep.py` used to read the rainfall column as

```python
pd.to_numeric(climate["Rain (mm)"].replace("---", "0"), errors="coerce").fillna(0) / 1000
```

so **June 1941's missing rainfall entered the pipeline as 0 mm rather than as
unknown** — a month the Met Office declares unmeasured recorded as the driest
possible month in the record. It now reads

```python
_rain_missing = _rain_raw.str.contains("---", na=False)
climate["P_m"] = pd.to_numeric(_rain_raw.where(~_rain_missing), errors="coerce") / 1000
```

and the run prints which months were affected.

**How much it mattered, measured before it was changed.** June at Valley has a
median of 48.1 mm, so 1941's true total is near 734 mm against the 686.3 mm the
pipeline recorded.

| | |
|---|---|
| 95-year mean annual rainfall, 1941 in at June = 0 | 856.0 mm |
| 95-year mean annual rainfall, 1941 excluded | **857.8 mm** |
| difference | 1.8 mm |

And the claim that rests on the 1940s does not move: the 1990s are the driest
decade at 793.4 mm either way, against 819.1 mm for the 1940s excluding 1941 or
805.8 mm including the zero. **That measurement is why the record was not
truncated.** Starting the analysis after the gap would have discarded 126 good
months to avoid one bad one, and would have moved every long-record baseline
including the PET trends that anchor §4.10.3 — trends computed from
temperature, which has no missing values at all.

**What changed downstream.** One committed number: `summer_P` in
`pipeline_scenario_params.csv`, from 0.0646926 to 0.0648633 m/month
(+0.17 mm/month), because `load_summer_climate()` in
`src/utils/scraping_common.py` averages June across all 95 years. Everything
else either slices to the well record or drops NaN before use — checked across
all nine readers of `01_climate.csv`.

**A related thing noticed and not changed.** `load_summer_climate()` and
`load_annual_climate()` average the FULL 95-year record. That is the same shape
as the defect Script 20 fixed at v1.35.0, where a 95-year climate normal was
being used to evaluate wells whose mean heads span the monitoring record only.
Whether the scenario forcing should be a 95-year normal or a well-period normal
is a modelling decision, not a bug fix, and is raised rather than taken.

**Where the numbers live now.** `mean_annual_rain_long_record`,
`rain_months_missing_in_source` and the decade series are committed keys in
`outputs/00_climate_summary/00_report_numbers.csv` (D-070). Before this, the
long-run rainfall mean and the driest-decade figure existed only as prose in
report10.
