# `data/wu_ianglese3_daily.csv` — provenance

Martin Hollingham's own weather station at Newborough, run on Weather Underground as **IANGLESE3**. Added 2026-10-25 to check whether the warren gets more rain than RAF Valley, the station that forces the model (D-278). Read only by `tools/wu_station.py`; no pipeline step reads it.

## Source

| | |
|---|---|
| **Station** | IANGLESE3, a personal weather station owned and run by Martin Hollingham |
| **Location** | 53.1641 N, 4.3595 W (as reported by the station): Newborough village, at the north-east edge of the warren |
| **Product** | Weather Underground PWS history API, daily summary (`/v2/pws/history/daily`, metric units) |
| **Downloaded** | 2026-10-25 by Martin, with the station owner's API key (the key is not stored in the repository) |
| **Raw form** | one JSON file per day in `data/wu_ianglese3/` (5,875 days, 2007-12-15 to 2024-01-14, 24 MB), kept on the L14 and gitignored |
| **Committed form** | `wu_ianglese3_daily.csv`, built from the raw files by `python3 tools/wu_station.py build` |

## What the archive holds

- **Reporting days:** 4,036, from 2008-01-01 to 2023-04-17.
- **2008–2011:** January only in each year, with no rain total in 2008–09.
- **Daily rain totals:** from 2010-01-01. Continuous from 2012 to January 2021. Patchy in 2021–22 (about half the days lack a total). The station stopped in April 2023.
- **Rain coverage:** 3,559 days carry a usable rain total; 476 reporting days carry none.

## Columns and conventions

- `date`, `precip_mm`, `temp_avg_c`, `qc_status`, `flag`.
- **The day is the local calendar day** (Europe/London, midnight to midnight, as Weather Underground summarises it). MIDAS readings are the 24 h to 09:00 (`MIDAS_RAIN_PROVENANCE.md`), so the two differ day to day but not month to month.
- **`qc_status`** is Weather Underground's own flag (−1, 0, 1), carried as given.
- **`flag`:**
  - `ok`: a usable rain total.
  - `no_rain_total`: the station reported that day but gave no rain total.
  - `suspect_gauge_fault`: a daily total of 100 mm or more. Only one day is affected: 152.4 mm on 2014-05-19, exactly 6.00 in and also reported as the hourly rate, so a gauge fault, not rain.

## Licence

The station and its readings are Martin Hollingham's own.
