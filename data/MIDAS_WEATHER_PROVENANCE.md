# `data/midas_weather/`: provenance and licence

Hourly weather and radiation records for Valley, for the E13 test (spec `working/updates/NRG_spec_E13_evaporation_forcing_2026-10-22.md`). E13 asks whether a wind- and humidity-aware evaporation estimate (FAO-56 Penman–Monteith) removes the 2006–08 water-table excess that a temperature-only Thornthwaite PET leaves.

- Added 2026-10-23.
- Not yet read by any script. When a reader is written, it will be a documented raw-input exception, as `src/utils/midas_rain.py` is for `data/midas_rain/`.

## Source

| | |
|---|---|
| **Products** | Met Office **MIDAS Open: UK hourly weather observation data, v202407**, and **MIDAS Open: UK hourly solar radiation data, v202407** (dataset-version-202407) |
| **Archive** | CEDA, `badc/ukmo-midas-open/data/uk-hourly-weather-obs/dataset-version-202407/gwynedd/01145_valley/qc-version-1/` and the same path under `uk-radiation-obs` |
| **Version used** | `qc-version-1` (the Met Office's current best version), one BADC-CSV per year, stored gzipped (`gzip -n -9`, content unchanged) |
| **Downloaded** | 2026-10-23, by Martin Hollingham (registered CEDA account) |
| **DOIs** | Hourly weather: [10.5285/c50776e4903942cdb329589da70b83fe](https://doi.org/10.5285/c50776e4903942cdb329589da70b83fe); solar radiation: [10.5285/0afba628c2f4462da68b0a81ebf1ff4c](https://doi.org/10.5285/0afba628c2f4462da68b0a81ebf1ff4c) (CEDA catalogue records, read 2026-10-23) |

## The station

Valley, src_id 01145, 53.253 N, 4.536 W, 10 m. It is the same station as `RAF_Valley_Climate.csv` (see `CLIMATE_PROVENANCE.md`) and `data/midas_rain/valley_01145/`.

## What is held

| Folder | Years | Notes |
|---|---|---|
| `valley_01145/hourly_weather/` | 1957–2023 complete, plus the capability file | 1996, 2000 and 2004 were downloaded separately on 2026-10-23 and added. Every year has 8,700 or more hourly wind and temperature readings. Dew point and relative humidity are three-hourly only in 1968–1972, and dew point was about 93% complete in 2021. |
| `valley_01145/radiation/` | 2001 (from about October) – 2023, plus the capability file | Hourly global irradiation (`glbl_irad_amt`), 8,300 or more hours a year from 2002. 2022–2023 also carry daily (24 h) records beside the hourly ones. |

The record ends in 2023 because dataset-version-202407 does. A later dataset version would add 2024 onwards.

## Variables for E13

**Hourly weather:**
- `wind_speed`: its units are set by `wind_speed_unit_id`, which is 4 throughout 2007. **Check the code's meaning in the MIDAS documentation (knots is expected) before converting to m/s at 2 m.**
- `air_temperature`, `dewpoint`, `rltv_hum`, `msl_pressure`, `stn_pres`.
- Hourly sunshine (`wmo_hr_sun_dur`, `cs_hr_sun_dur`, `drv_hr_sun_dur`).

**Radiation:**
- `glbl_irad_amt`, global irradiation over the hour (or the 24 h of a daily record, given by `ob_hour_count`). Units are in the file headers.

## Licence

**Open Government Licence v3.0.** Attribution: "Contains public sector information licensed under the Open Government Licence v3.0." © Crown copyright, Met Office. Cite each product as Met Office (2024): MIDAS Open: UK hourly weather observation data, v202407 (and UK hourly solar radiation data, v202407). NERC EDS Centre for Environmental Data Analysis. doi:10.5285/c50776e4903942cdb329589da70b83fe (hourly weather); doi:10.5285/0afba628c2f4462da68b0a81ebf1ff4c (solar radiation).
