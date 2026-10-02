# `data/midas_rain/` — provenance and licence

Daily rain-gauge records for Script 50 E8d (D-234): did long rain events, which a monthly total hides,
drive the 2006–08 water-table excess? Added 2026-10-02. Read only by `src/utils/midas_rain.py`, a
documented raw-input exception like Scripts 09/10/24.

## Source

| | |
|---|---|
| **Product** | Met Office **MIDAS Open: UK daily rainfall data, v202407** (dataset-version-202407) |
| **DOI** | [10.5285/8606115371e44b079e25d479cfec465c](https://doi.org/10.5285/8606115371e44b079e25d479cfec465c) |
| **Archive** | CEDA, `badc/ukmo-midas-open/data/uk-daily-rain-obs/dataset-version-202407/gwynedd/` |
| **Version used** | `qc-version-1` (the Met Office's current best version), one BADC-CSV per year |
| **Downloaded** | 2026-10-02, by Martin Hollingham (registered CEDA account) |

| folder | station | src_id | location | height | years held |
|---|---|---|---|---|---|
| `alaw_01146/` | Anglesey: Llyn Alaw | 01146 | 53.339 N, 4.441 W | 44 m | 1974–2023 (2003–2023 complete) |
| `valley_01145/` | Valley | 01145 | 53.253 N, 4.536 W | 10 m | 1961–Aug 2008 |

**Valley is the same station as `RAF_Valley_Climate.csv`** (see `CLIMATE_PROVENANCE.md`), but a
different product: that file is Met Office Historic Station Data (monthly); this is MIDAS Open (daily),
whose Valley daily record ends in 2008. Checked 2026-10-02: Valley's daily sums, with each reading assigned
to the day the rain fell, match its monthly record (r 0.994 over 154 complete months). Llyn Alaw lies
about 20 km NNE of the warren, inland and wetter (29% more rain than Valley over 1974–2008), and tracks
Valley closely (daily r 0.92, monthly 0.96, wet-day agreement 91%).

## Reading conventions (from the files)

- A daily reading (`ob_day_cnt` = 1) is the 24 h ending at 09:00 on `ob_date`; the rain is assigned to the
  day before.
- Multi-day accumulations (`ob_day_cnt` > 1) are dropped: those days are missing, never filled.
- Raw `qc-version-0` files and the empty files of CEDA's bulk zip download were not used.

## Licence

**Open Government Licence v3.0.** Attribution: "Contains public sector information licensed under the Open
Government Licence v3.0." © Crown copyright, Met Office. Cite as: Met Office (2024): MIDAS Open: UK daily
rainfall data, v202407. NERC EDS Centre for Environmental Data Analysis.
doi:10.5285/8606115371e44b079e25d479cfec465c.
