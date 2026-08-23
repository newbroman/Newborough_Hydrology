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

## One defect, recorded rather than fixed

`src/01_data_prep.py` reads the rainfall column as

```python
pd.to_numeric(climate["Rain (mm)"].replace("---", "0"), errors="coerce").fillna(0) / 1000
```

so **June 1941's missing rainfall enters the pipeline as 0 mm rather than as
unknown.** A month the Met Office declares unmeasured is recorded as the driest
possible month in the record.

**What it does not touch.** June 1941 lies 64 years before the well record, so no
BACI result, no SSM coefficient, no summer-minimum trend and none of the
coastal-gradient fits see it. The PET series is computed from temperature and is
unaffected, so the long-record PET trends (`trend_annual_pet_1931_2025` and its
siblings) are unaffected.

**What it does touch.** The 95-year annual rainfall table understates 1941, and
any long-record rainfall statistic that spans the 1940s inherits it — including
the "driest decade in the long RAF Valley rainfall record" framing used when
discussing Betson et al. (2002).

**Not fixed here** because the fix is a decision, not an edit: leaving the month
as NaN changes what downstream aggregations do with an incomplete year, and the
annual summary already carries `Months_complete` and a `Notes` flag that could
carry it properly instead. Raised for Martin.
