# `data/tides/`: provenance and licence

Tide-gauge records for Script 40's storm table (`40_09_storm_winters.csv`, `40_10_storm_events.csv`): the day's
highest observed level and largest surge residual on each storm day, at the gauges either side of the frontage.

- Added 2026-11-25 (BODC download by Martin Hollingham, uploaded to the claude.ai/code session the same evening).
- Kept in the PRIVATE repository (force-added; `.gitignore` keeps `/data/tides/` out of the public one). The
  licence would allow publishing them; they are private because the 2026-11-25 handover asked for it.
- Read only by `src/40_shoreline_retreat.py` 1.11.0 (`_read_bodc`; `paths.DATA_TIDES_HOLYHEAD`,
  `paths.DATA_TIDES_BARMOUTH`).

## Source

| | |
|---|---|
| **Product** | BODC (British Oceanographic Data Centre) UK National Tide Gauge Network, **processed** 15-minute data |
| **Gauges** | **Holyhead**, port P054, 53.30777 N 4.63116 W (north of the frontage); **Barmouth**, port P923, 52.71906 N 4.04517 W (south of it). Bubbler gauges, parameter ASLVBG02 |
| **Contributor** | National Oceanography Centre, Liverpool (each file's header) |
| **Datum** | Admiralty Chart Datum (ACD), stated in every file header. The two gauges' ACDs differ, so levels compare within a gauge, never across |
| **Licence** | **Open Government Licence** (`bodc_lists/open_government_licence.pdf`, in the download). Acknowledge BODC and the NOC as the source |
| **Format** | `bodc_lists/format.pdf`. Flags: M improbable (BODC QC), N null, T interpolated; the reader drops all three |

## What is held

- `holyhead/20YYHOL.txt.gz`: 2004-2024, one per year. `barmouth/20YYBAR.txt.gz`: 2003 and 2005-2024 (**no 2004 file
  for Barmouth in the download**). Stored with `gzip -n -9`, content unaltered (sha256 below is of the uncompressed
  text, i.e. the file as downloaded).
- `*/recent/`: BODC's monthly files Sep 2023 and 2025-Feb 2026, as downloaded and gzipped. **Not read** (the reader
  takes the folder's top level only); Sep 2023 overlaps the 2023 yearly file.
- `bodc_lists/`: the station pages (`HOL.html`, `BAR.html`), BODC's multi-station `extremes.txt`, `means.txt`,
  `surges.txt`, the format note and the licence, as downloaded.
- **Not kept: Bangor.** BODC's "Bangor" is BANGOR (NORTHERN IRELAND), Belfast Lough, not Bangor on the Menai
  Strait; it appears only as rows of the multi-station lists, which are kept whole.

## Quality: BODC flags whole months improbable

The M flag marks real faults (Holyhead 2010 reaches a "level" of 32.19 m; 2015 residuals reach 10.8 m) in runs of
whole months, so the flag is taken as BODC set it. Barmouth's record is **effectively absent from 2016**: every
value from 2016 to 2024 is flagged or null. Holyhead's clean share falls to 53-56% in 2010 and 2012. 40_09 reports
the clean-tide days per winter (`tide_days_holyhead`, `tide_days_barmouth`), so a thin winter reads as thin, not calm.

| file | 15-min values | clean (unflagged) level | sha256 (uncompressed) |
|---|---:|---:|---|
| `holyhead/2004HOL.txt.gz` | 35136 | 99.7% | `b91ce04cdc160252…` |
| `holyhead/2005HOL.txt.gz` | 35040 | 81.2% | `f3266c93fe2bbd39…` |
| `holyhead/2006HOL.txt.gz` | 35040 | 97.7% | `8adf37c90a4dbcc9…` |
| `holyhead/2007HOL.txt.gz` | 35040 | 91.3% | `cd76f9c0ec1b9e97…` |
| `holyhead/2008HOL.txt.gz` | 35136 | 94.2% | `4d1bd81575c3d86b…` |
| `holyhead/2009HOL.txt.gz` | 35040 | 83.6% | `a95609e9a02b932b…` |
| `holyhead/2010HOL.txt.gz` | 35040 | 56.0% | `b52b3146fae7f061…` |
| `holyhead/2011HOL.txt.gz` | 35040 | 73.8% | `e34f9dc3ecc06b42…` |
| `holyhead/2012HOL.txt.gz` | 35136 | 52.6% | `48a15e6af7df7c1d…` |
| `holyhead/2013HOL.txt.gz` | 35040 | 100.0% | `8214cedf6a6846bd…` |
| `holyhead/2014HOL.txt.gz` | 35040 | 95.8% | `5ea55235be1b75f9…` |
| `holyhead/2015HOL.txt.gz` | 35040 | 65.2% | `787dd1e969398e23…` |
| `holyhead/2016HOL.txt.gz` | 35136 | 93.7% | `2cb7c51617f28ceb…` |
| `holyhead/2017HOL.txt.gz` | 35040 | 68.1% | `70f8a2b366994043…` |
| `holyhead/2018HOL.txt.gz` | 35040 | 93.8% | `84e4478bd16572a7…` |
| `holyhead/2019HOL.txt.gz` | 35040 | 98.8% | `e8d3a9875ae839e3…` |
| `holyhead/2020HOL.txt.gz` | 35136 | 77.8% | `7cc9ac473dbec820…` |
| `holyhead/2021HOL.txt.gz` | 35040 | 85.3% | `6a81dfe1b479baf5…` |
| `holyhead/2022HOL.txt.gz` | 35040 | 73.0% | `5d3a1fb2da14fc99…` |
| `holyhead/2023HOL.txt.gz` | 35040 | 74.0% | `7099c4b8ba694300…` |
| `holyhead/2024HOL.txt.gz` | 35136 | 67.6% | `f6e3ce38e706c19c…` |
| `barmouth/2003BAR.txt.gz` | 35040 | 37.1% | `47d085e57f416403…` |
| `barmouth/2005BAR.txt.gz` | 35040 | 77.9% | `0b6639dc6c1b9fe2…` |
| `barmouth/2006BAR.txt.gz` | 35040 | 97.2% | `3165ad4f9d9a197c…` |
| `barmouth/2007BAR.txt.gz` | 35040 | 65.2% | `67fa6f2615bed227…` |
| `barmouth/2008BAR.txt.gz` | 35136 | 80.9% | `8f754e8da22c08d9…` |
| `barmouth/2009BAR.txt.gz` | 35040 | 64.2% | `3ab4c1f3b30ce0ec…` |
| `barmouth/2010BAR.txt.gz` | 35040 | 80.4% | `39a0385cecd84d02…` |
| `barmouth/2011BAR.txt.gz` | 35040 | 41.9% | `dc78ffa973015c10…` |
| `barmouth/2012BAR.txt.gz` | 35136 | 36.3% | `bfbfced93b432a79…` |
| `barmouth/2013BAR.txt.gz` | 35040 | 86.9% | `bce6e26572a4b71c…` |
| `barmouth/2014BAR.txt.gz` | 35040 | 91.5% | `0bdd942549cf6162…` |
| `barmouth/2015BAR.txt.gz` | 35040 | 72.5% | `fd321f577de27008…` |
| `barmouth/2016BAR.txt.gz` | 35136 | 3.0% | `d7c5ab7219e83625…` |
| `barmouth/2017BAR.txt.gz` | 35040 | 0.0% | `c22b40049183c9d9…` |
| `barmouth/2018BAR.txt.gz` | 35040 | 0.0% | `1840b36ec41cbb3f…` |
| `barmouth/2019BAR.txt.gz` | 35040 | 0.0% | `4305467cac8492b7…` |
| `barmouth/2020BAR.txt.gz` | 35136 | 0.4% | `413e31275c680d7a…` |
| `barmouth/2021BAR.txt.gz` | 35040 | 0.0% | `d199856c85a0454e…` |
| `barmouth/2022BAR.txt.gz` | 35040 | 0.0% | `39c34decb3af43a3…` |
| `barmouth/2023BAR.txt.gz` | 35040 | 0.0% | `373ed4a9ba6ac015…` |
| `barmouth/2024BAR.txt.gz` | 35136 | 0.0% | `a1f137798614f1e9…` |
