"""Download ERA5 hourly wave fields for the Newborough frontage (see data/WAVES_PROVENANCE.md).

One request per HALF-YEAR to the Copernicus Climate Data Store (reanalysis-era5-single-levels). The CDS
costs a request in fields x grid points (here 6 points): a year of three variables costs 158,112 against a limit of
121,000 and is refused ("cost limits exceeded"); a half-year costs 78,624 (estimate_costs, 2026-11-25). Monthly
requests also pass but queue ~15 min each, so 240 of them would take days:
significant height of combined wind waves and swell, mean wave direction, peak wave period;
2004-2023; area N 53.5, W -5.0, S 52.8, E -4.0; NetCDF. A half-year already on disk is
skipped, so an interrupted run resumes where it stopped. Files: era5_waves_YYYY_H1.nc (Jan-Jun), _H2.nc (Jul-Dec).

Run with the CDS key available to cdsapi (in a cloud session the network proxy injects it into
the PRIVATE-TOKEN header, so CDSAPI_KEY may be a placeholder):
    CDSAPI_URL=https://cds.climate.copernicus.eu/api CDSAPI_KEY=proxy-injected \
        python3 data/waves/download_era5_waves.py [FIRST_YEAR LAST_YEAR]

Version 1.0.0 - Hollingham (2026) - 2026-11-25. First issue: half-year jobs, at most MAX_LIVE queued at once (the CDS
rejects more), collected as they finish; job ids kept in era5_jobs.json so a restart resumes.
"""
import json
import os
import sys
import time
from pathlib import Path

from ecmwf.datastores import Client   # installed with cdsapi >= 0.7

OUT = Path(__file__).resolve().parent
JOBS = OUT / "era5_jobs.json"          # request ids, so a restart collects jobs already queued
VARIABLES = ["significant_height_of_combined_wind_waves_and_swell",
             "mean_wave_direction", "peak_wave_period"]
AREA = [53.5, -5.0, 52.8, -4.0]   # N, W, S, E
POLL_S = 60
MAX_LIVE = 3        # queued + running jobs the CDS accepts per user (2026-11-25: a 4th is rejected)
BACKOFF_S = 600     # after a rejection, wait this long before resubmitting that half-year


def live_jobs(c):
    """Jobs on the account still queued or running (any origin: a stale job holds a slot too)."""
    js = c.get_jobs(limit=100, status=["accepted", "running"])
    return len(js.json.get("jobs", []))


def request(y, months):
    return {
        "product_type": ["reanalysis"],
        "variable": VARIABLES,
        "year": [str(y)],
        "month": [f"{m:02d}" for m in months],
        "day": [f"{d:02d}" for d in range(1, 32)],
        "time": [f"{h:02d}:00" for h in range(24)],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def main():
    y0, y1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) == 3 else (2004, 2023)
    c = Client(url=os.environ.get("CDSAPI_URL", "https://cds.climate.copernicus.eu/api"),
               key=os.environ.get("CDSAPI_KEY", "proxy-injected"))
    jobs = json.loads(JOBS.read_text()) if JOBS.exists() else {}
    want = {}
    for y in range(y0, y1 + 1):
        for half, months in (("H1", range(1, 7)), ("H2", range(7, 13))):
            tag = f"{y}_{half}"
            if (OUT / f"era5_waves_{tag}.nc").exists():
                print(f"{tag}: present, skipped", flush=True)
                continue
            want[tag] = months
    # The CDS keeps only a few queued jobs per user (MAX_LIVE) and REJECTS the rest at once (measured 2026-11-25:
    # 146 rejections in a few minutes when all 40 were submitted together). So submit only into a free slot,
    # counting every live job on the account, and back off after a rejection.
    pending = set(want)
    rejected_at = {}
    while pending:
        live = live_jobs(c)
        for tag in sorted(pending):
            jid = jobs.get(tag)
            st = c.get_remote(jid).status if jid else None
            if st == "successful":
                tmp = OUT / f"era5_waves_{tag}.part"
                c.get_remote(jid).download(str(tmp))
                target = OUT / f"era5_waves_{tag}.nc"
                tmp.rename(target)
                print(f"{tag}: {target.name} {target.stat().st_size} bytes", flush=True)
                pending.discard(tag)
            elif st in (None, "failed", "rejected", "dismissed", "deleted"):
                if st == "rejected" and tag not in rejected_at:
                    rejected_at[tag] = time.time()
                    print(f"{tag}: job {jid} rejected; waiting for a free slot", flush=True)
                if live >= MAX_LIVE or time.time() - rejected_at.get(tag, 0) < BACKOFF_S:
                    continue
                y = int(tag[:4])
                jobs[tag] = c.submit("reanalysis-era5-single-levels", request(y, want[tag])).request_id
                rejected_at.pop(tag, None)
                JOBS.write_text(json.dumps(jobs, indent=1))
                live += 1
                print(f"{tag}: submitted {jobs[tag]} ({live} live)", flush=True)
        if pending:
            time.sleep(POLL_S)
    print("all present", flush=True)


if __name__ == "__main__":
    main()
