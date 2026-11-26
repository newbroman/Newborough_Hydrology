"""Convert the half-yearly ERA5 wave NetCDF files to the one hourly CSV Script 40 reads (see data/WAVES_PROVENANCE.md).

The pipeline's venv has no NetCDF4 reader (the files are HDF5-based NetCDF4), and adding one for a single input is
not worth a new pinned dependency, so the conversion is done here, once, with h5py, and its output is the input:
    data/waves/era5_waves_frontage_hourly.csv.gz
columns time_utc, swh_m, mwd_deg, pp1d_s at the ERA5 grid point nearest the Newborough frontage, FRONTAGE_POINT
(53.0 N, 4.5 W: open Caernarfon Bay, ~16 km south-west of Llanddwyn). Every half-year file must be present; a gap is a refusal.

    python3 -m pip install --target <dir> h5py   # outside the pipeline venv
    PYTHONPATH=<dir> python3 data/waves/era5_to_csv.py

Version 1.0.0 - Hollingham (2026) - 2026-11-25. First issue.
"""
import gzip
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "era5_waves_frontage_hourly.csv.gz"
FRONTAGE_POINT = (53.0, -4.5)
YEARS = range(2004, 2024)


def main():
    missing = [f"{y}_{h}" for y in YEARS for h in ("H1", "H2")
               if not (HERE / f"era5_waves_{y}_{h}.nc").exists()]
    if missing:
        sys.exit(f"{len(missing)} half-year file(s) missing, e.g. {missing[:5]}: run download_era5_waves.py first")
    n = 0
    # mtime=0: the gzip header carries no timestamp, so the same input gives the same bytes.
    with open(OUT, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
        gz.write(b"time_utc,swh_m,mwd_deg,pp1d_s\n")
        for y in YEARS:
            for h in ("H1", "H2"):
                f = h5py.File(HERE / f"era5_waves_{y}_{h}.nc", "r")
                lat, lon = f["latitude"][:], f["longitude"][:]
                i = int(np.argmin(np.abs(lat - FRONTAGE_POINT[0])))
                j = int(np.argmin(np.abs(lon - FRONTAGE_POINT[1])))
                assert abs(lat[i] - FRONTAGE_POINT[0]) < 1e-6 and abs(lon[j] - FRONTAGE_POINT[1]) < 1e-6
                t = f["valid_time"][:]
                cols = [f[v][:, i, j] for v in ("swh", "mwd", "pp1d")]
                for k in range(len(t)):
                    ts = datetime.fromtimestamp(int(t[k]), tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
                    vals = ",".join("" if np.isnan(c[k]) else f"{c[k]:.3f}" for c in cols)
                    gz.write(f"{ts},{vals}\n".encode())
                    n += 1
                f.close()
    print(f"{OUT.name}: {n} hours, point {FRONTAGE_POINT}")


if __name__ == "__main__":
    main()
