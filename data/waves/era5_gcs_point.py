"""ERA5 hourly waves at one point from Google's public ARCO-ERA5 copy (Martin 2026-11-26: "use Google"), replacing the
CDS route while the CDS queue was not starting jobs (requests queued 10+ h on 2026-11-25/26).

Source: gs://gcp-public-data-arco-era5/raw/date-variable-single_level/YYYY/MM/DD/<variable>/surface.nc - ERA5 as
ECMWF distributes it, one global 0.25-degree NetCDF3 (64-bit offset) file per day per variable, public, no account.
NetCDF3 stores values uncompressed at fixed offsets, so after parsing each file's header the 24 hourly values at one
grid point are fetched as 24 small HTTP range reads - not the 50 MB file. Values are unpacked with the file's own
scale_factor / add_offset, and _FillValue / missing_value become NaN.

Writes data/waves/era5_waves_frontage_hourly.csv.gz (time_utc, swh_m, mwd_deg, pp1d_s) - the same file, columns and
point (53.0 N, 4.5 W) as era5_to_csv.py, which converts the CDS route's downloads instead. Resumable: finished days are
kept in data/waves/gcs_cache/YYYY.csv (private, .gitignore) and skipped.

    python3 data/waves/era5_gcs_point.py [FIRST_YEAR LAST_YEAR]

Version 1.0.0 - Hollingham (2026) - 2026-11-26. First issue. Google holds two days (2023-11-09, 2023-11-10) as
NetCDF4/HDF5, not NetCDF3: those are read with h5py over the same range reads (day_point_hdf5).
"""
import gzip
import io
import struct
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import numpy as np

BASE = "https://storage.googleapis.com/gcp-public-data-arco-era5/raw/date-variable-single_level"
VARS = {"swh_m": "significant_height_of_combined_wind_waves_and_swell",
        "mwd_deg": "mean_wave_direction",
        "pp1d_s": "peak_wave_period"}
POINT = (53.0, -4.5)
HERE = Path(__file__).resolve().parent
CACHE = HERE / "gcs_cache"
OUT = HERE / "era5_waves_frontage_hourly.csv.gz"
THREADS = 48
TYPES = {1: ("b", 1), 2: ("c", 1), 3: (">h", 2), 4: (">i", 4), 5: (">f", 4), 6: (">d", 8)}


def get(url, a=None, b=None, tries=5):
    for k in range(tries):
        try:
            h = {"Range": f"bytes={a}-{b}"} if a is not None else {}
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
                return r.read()
        except Exception:
            if k == tries - 1:
                raise


class Hdr:
    """Minimal NetCDF classic / 64-bit-offset header parser: dims, variables (shape, type, begin, attrs)."""
    def __init__(self, buf):
        self.b, self.p = buf, 4
        self.v2 = buf[3] == 2
        self.numrecs = self.u4()
        self.dims = self.dim_list()
        self.gatts = self.att_list()
        self.vars = self.var_list()
        recvars = [v for v in self.vars.values() if v["rec"]]
        self.recsize = sum(v["vsize"] for v in recvars) if len(recvars) > 1 else (recvars[0]["vsize"] if recvars else 0)

    def u4(self):
        x = struct.unpack(">I", self.b[self.p:self.p + 4])[0]; self.p += 4; return x

    def name(self):
        n = self.u4(); s = self.b[self.p:self.p + n].decode(); self.p += (n + 3) // 4 * 4; return s

    def dim_list(self):
        tag, n = self.u4(), self.u4()
        out = []
        for _ in range(n):
            out.append((self.name(), self.u4()))
        return out

    def att_list(self):
        tag, n = self.u4(), self.u4()
        out = {}
        for _ in range(n):
            nm = self.name(); t = self.u4(); cnt = self.u4()
            fmt, sz = TYPES[t]
            raw = self.b[self.p:self.p + cnt * sz]; self.p += (cnt * sz + 3) // 4 * 4
            out[nm] = raw.decode(errors="replace") if t == 2 else np.frombuffer(raw, dtype=fmt)
        return out

    def var_list(self):
        tag, n = self.u4(), self.u4()
        out = {}
        for _ in range(n):
            nm = self.name(); nd = self.u4(); ids = [self.u4() for _ in range(nd)]
            atts = self.att_list(); t = self.u4(); vsize = self.u4()
            begin = struct.unpack(">Q" if self.v2 else ">I", self.b[self.p:self.p + (8 if self.v2 else 4)])[0]
            self.p += 8 if self.v2 else 4
            shape = [self.dims[i][1] for i in ids]
            out[nm] = {"ids": ids, "shape": shape, "type": t, "vsize": vsize, "begin": begin, "atts": atts,
                       "rec": bool(ids) and self.dims[ids[0]][1] == 0}
        return out


def read_coord(url, h, nm):
    v = h.vars[nm]
    fmt, sz = TYPES[v["type"]]
    raw = get(url, v["begin"], v["begin"] + v["shape"][0] * sz - 1)
    return np.frombuffer(raw, dtype=fmt).astype(float)


GRID = {}


class RangeFile(io.RawIOBase):
    """A read-only file over HTTP range requests (for h5py), cached in blocks."""
    def __init__(self, url, block=1 << 20):
        self.url, self.pos, self.block, self.cache = url, 0, block, {}
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60)
        self.size = int(r.headers["Content-Length"])

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def readinto(self, buf):
        n = min(len(buf), self.size - self.pos)
        if n <= 0:
            return 0
        out = bytearray()
        while len(out) < n:
            i, off = divmod(self.pos + len(out), self.block)
            if i not in self.cache:
                a = i * self.block
                self.cache[i] = get(self.url, a, min(self.size, a + self.block) - 1)
            out += self.cache[i][off:off + n - len(out)]
        buf[:n] = out
        self.pos += n
        return n


def day_point_hdf5(url):
    """The few days Google holds as NetCDF4/HDF5 (9-10 Nov 2023, measured 2026-11-26): read only the chunks needed.
    Needs h5py (outside the pipeline venv, like cdsapi)."""
    import h5py
    with h5py.File(RangeFile(url), "r") as f:
        lat, lon = f["latitude"][:], f["longitude"][:]
        i = int(np.argmin(abs(lat - POINT[0])))
        j = int(np.argmin(abs(((lon + 180) % 360 - 180) - POINT[1])))
        assert abs(lat[i] - POINT[0]) < 1e-6 and abs(((lon[j] + 180) % 360 - 180) - POINT[1]) < 1e-6
        v = f[[k for k in f if f[k].ndim == 3][0]]
        x = v[:, i, j].astype(float)
        a = {k: v.attrs[k] for k in v.attrs}
    bad = np.zeros(len(x), bool)
    for k in ("_FillValue", "missing_value"):
        if k in a:
            bad |= x == float(np.ravel(a[k])[0])
    x = x * float(np.ravel(a.get("scale_factor", [1.0]))[0]) + float(np.ravel(a.get("add_offset", [0.0]))[0])
    x[bad] = np.nan
    return x


def day_point(d, var):
    url = f"{BASE}/{d:%Y/%m/%d}/{var}/surface.nc"
    head = get(url, 0, 65535)
    if head[:4] == b"\x89HDF":
        return day_point_hdf5(url)
    h = Hdr(head)
    data = [k for k, v in h.vars.items() if len(v["ids"]) == 3][0]
    v = h.vars[data]
    if "grid" not in GRID:
        lat = read_coord(url, h, "latitude"); lon = read_coord(url, h, "longitude")
        i = int(np.argmin(abs(lat - POINT[0]))); j = int(np.argmin(abs(((lon + 180) % 360 - 180) - POINT[1])))
        assert abs(lat[i] - POINT[0]) < 1e-6 and abs(((lon[j] + 180) % 360 - 180) - POINT[1]) < 1e-6
        GRID["grid"] = (i, j, len(lat), len(lon))
    i, j, nlat, nlon = GRID["grid"]
    fmt, sz = TYPES[v["type"]]
    nt = h.numrecs if v["rec"] else v["shape"][0]
    vals = []
    for t in range(nt):
        off = (v["begin"] + t * h.recsize + (i * nlon + j) * sz) if v["rec"] else \
              (v["begin"] + ((t * nlat + i) * nlon + j) * sz)
        vals.append(np.frombuffer(get(url, off, off + sz - 1), dtype=fmt)[0])
    x = np.array(vals, dtype=float)
    bad = np.zeros(len(x), bool)
    for k in ("_FillValue", "missing_value"):
        if k in v["atts"]:
            bad |= x == float(v["atts"][k][0])
    x = x * float(v["atts"].get("scale_factor", [1.0])[0]) + float(v["atts"].get("add_offset", [0.0])[0])
    x[bad] = np.nan
    return x


def one_day(d):
    cols = {k: day_point(d, var) for k, var in VARS.items()}
    return [(f"{d:%Y-%m-%d} {h:02d}:00", *(cols[k][h] for k in VARS)) for h in range(24)]


def main():
    y0, y1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) == 3 else (2004, 2023)
    CACHE.mkdir(exist_ok=True)
    for y in range(y0, y1 + 1):
        f = CACHE / f"{y}.csv"
        if f.exists():
            print(f"{y}: cached", flush=True); continue
        days = [date(y, 1, 1) + timedelta(n) for n in range((date(y + 1, 1, 1) - date(y, 1, 1)).days)]
        with ThreadPoolExecutor(THREADS) as ex:
            rows = [r for day in ex.map(one_day, days) for r in day]
        tmp = f.with_suffix(".part")
        with open(tmp, "w") as fh:
            for r in rows:
                fh.write(r[0] + "," + ",".join("" if np.isnan(v) else f"{v:.3f}" for v in r[1:]) + "\n")
        tmp.rename(f)
        print(f"{y}: {len(rows)} hours", flush=True)
    if all((CACHE / f"{y}.csv").exists() for y in range(2004, 2024)):
        with open(OUT, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
            gz.write(b"time_utc,swh_m,mwd_deg,pp1d_s\n")
            for y in range(2004, 2024):
                gz.write((CACHE / f"{y}.csv").read_bytes())
        print(f"{OUT.name} written", flush=True)


if __name__ == "__main__":
    main()
