# `data/waves/`: provenance and licence

Hourly ERA5 wave fields off the Newborough frontage, for Script 40's storm table (`40_09_storm_winters.csv`,
`40_10_storm_events.csv`; Martin 2026-11-25: "a storm table", with waves beside the Valley wind and the tides).

- Added 2026-11-25. Public since 2026-11-26 (Martin), as for MIDAS and Sentinel: the converted series and both
  scripts. The raw CDS NetCDF files and the CDS job list stay in the private repository (`.gitignore`).
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

## The route actually used: Google's public copy (2026-11-26)

The CDS queue did not start a single half-year job in over 10 hours (2026-11-25/26), so on Martin's word ("use Google")
the series was read from **Google's public ARCO-ERA5 copy**: `gs://gcp-public-data-arco-era5/raw/date-variable-single_level/`
(served at `https://storage.googleapis.com/gcp-public-data-arco-era5/...`), which holds ERA5 single-level fields as ECMWF
distributes them, one global 0.25-degree NetCDF3 file per day per variable; public, no account. The product, licence and
citation above are unchanged: it is the same ERA5 reanalysis (ARCO-ERA5: Carver & Merose (2023), Google Research).
`era5_gcs_point.py` parses each file's header and fetches only the 24 hourly values at the point (HTTP range reads of
2 bytes each, unpacked with the file's own scale_factor / add_offset) - not the 50 MB file.

**Checked against the CDS:** January 2004 at 53.0 N 4.5 W, from the one CDS file that arrived: Hs 1.28 m, mean direction
248.4 deg, peak period 6.23 s. From Google: 1.28 m, 248.4 deg, 6.23 s. Identical at the quoted precision.

## What is held

| File | What |
|---|---|
| `era5_waves_frontage_hourly.csv.gz` | **The pipeline input.** The point 53.0 N, 4.5 W, hourly 2004-01-01 00:00 to 2023-12-31 23:00 UTC, columns `time_utc, swh_m, mwd_deg, pp1d_s`, gzip with no timestamp (byte-reproducible). Written by `era5_gcs_point.py` |
| `era5_gcs_point.py` | the route used: Google's copy, point values by range read |
| `download_era5_waves.py`, `era5_to_csv.py` | the CDS route (half-year NetCDF jobs, then conversion): kept, not used for the committed series |
| `gcs_cache/YYYY.csv` | per-year working files of the Google route (gitignored; rebuildable) |

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

`era5_waves_frontage_hourly.csv.gz` (2.0 MB; 175,320 hours, 2004-01-01 00:00 to 2023-12-31 23:00 UTC, no gaps, no missing
values; written 2026-11-26): `6ce117572af7d6a3a9084ee8347b3282ebd5f589b77550451a7418d79ea7c49d`.
Two days, 2023-11-09 and 2023-11-10, are held by Google as NetCDF4/HDF5 rather than NetCDF3; `era5_gcs_point.py` reads them
with h5py and they join their neighbours continuously (8 Nov 23:00 Hs 1.42 m, 9 Nov 00:00 1.36 m).
