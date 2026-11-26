# `data/waves/`: provenance and licence

Hourly ERA5 wave fields off the Newborough frontage, for Script 40's storm table (`40_09_storm_winters.csv`,
`40_10_storm_events.csv`; Martin 2026-11-25: "a storm table", with waves beside the Valley wind and the tides).

- Added 2026-11-25. Kept in the PRIVATE repository (force-added; `.gitignore` keeps it out of the public one).
- Read only by `src/40_shoreline_retreat.py` 1.11.0 (`_read_era5_waves`, `paths.DATA_WAVES_ERA5`).

## Source

| | |
|---|---|
| **Product** | **ERA5 hourly data on single levels from 1940 to present** (`reanalysis-era5-single-levels`), Copernicus Climate Change Service (C3S) Climate Data Store |
| **DOI** | [10.24381/cds.adbb2d47](https://doi.org/10.24381/cds.adbb2d47) |
| **Reference** | Hersbach, H. et al. (2023): ERA5 hourly data on single levels from 1940 to present. C3S CDS |
| **Licence** | Licence to use Copernicus Products (accepted by Martin Hollingham on his CDS account). Acknowledge as: "Generated using Copernicus Climate Change Service information [2026]" and cite the DOI. Neither the European Commission nor ECMWF is responsible for any use of the information. |
| **Downloaded** | 2026-11-25/26, by a claude.ai/code session on Martin's CDS account (API key held as a network secret, never in the repository) |
| **Request** | product_type reanalysis; variables `significant_height_of_combined_wind_waves_and_swell`, `mean_wave_direction`, `peak_wave_period`; every hour 2004-01-01 to 2023-12-31; area N 53.5, W -5.0, S 52.8, E -4.0; NetCDF, unarchived; one request per half-year (`download_era5_waves.py`) |

## What is held

| File | What |
|---|---|
| `era5_waves_YYYY_H1.nc`, `_H2.nc` | CDS NetCDF4 as downloaded, unaltered: 40 files, Jan-Jun and Jul-Dec of 2004-2023. Grid 2 x 3 points at 0.5 deg (53.5, 53.0 N x 5.0, 4.5, 4.0 W); `swh` (m), `mwd` (degree true, direction FROM), `pp1d` (s) |
| `era5_waves_frontage_hourly.csv.gz` | **The pipeline input.** `era5_to_csv.py`: the point 53.0 N, 4.5 W only, columns `time_utc, swh_m, mwd_deg, pp1d_s`, gzip with no timestamp (byte-reproducible) |
| `download_era5_waves.py`, `era5_to_csv.py` | the download and the conversion; neither runs in the pipeline |

**Why one point.** 53.0 N, 4.5 W is open Caernarfon Bay, about 16 km south-west of Llanddwyn and the grid point
nearest the eroding frontage; the frontage faces it. 53.5 N lies north of Anglesey (Irish Sea, the wrong exposure);
the 4.0 W column is close to the Llŷn and Arfon coasts. ERA5's wave model runs on a coarser grid than the 0.25 deg
atmosphere, so a point 16 km offshore is the resolution the data has: it gives the offshore wave climate, not the
breaking wave at the dune toe.

**Why a CSV.** The pipeline's venv carries no NetCDF4 (HDF5) reader, and one input does not justify a new pinned
dependency; the conversion runs once, outside the pipeline, with h5py.

## Checks on the first file (2004-01)

No missing values at any of the six points; January 2004 means Hs 0.8-1.7 m, direction 233-254 deg (WSW), peak
period 5.9-6.6 s.

## sha256

Written below when the download completes.
