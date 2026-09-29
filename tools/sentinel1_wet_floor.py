#!/usr/bin/env python3
"""
sentinel1_wet_floor.py — the Sentinel-1 radar read of the warren floors and the
forest, against the wells (T-94).

WHAT THIS IS

  A TOOL (not a pipeline step; writes to data/sentinel/ and working/updates/).
  It reads every Sentinel-1 radiometrically terrain-corrected scene over the
  warren from Microsoft's Planetary Computer archive (STAC, anonymous signed
  URLs, cloud-optimised GeoTIFFs; only the site's window is read), on the same
  10 m OSGB grid as the Sentinel-2 wet-area line (WET_AREA_GRID), and asks three
  questions with three different priors, kept apart:

    1. the open warren — calibrated HANDS-FREE against the Sentinel-2 classes of
       the committed series on coincident scenes (Martin, 2026-09-29: "s2
       classes alone"); the vetted extents are the meaning check, never the fit.
       Radar sees still water as dark (specular) and SATURATED ground as brighter
       than dry (dielectric), so the two S2 classes that B8 cannot split may
       separate here. Then the series over every scene (winter first, then all
       year) and the per-cell switching levels beside the S2 ones.
    2. the forest — the D-210 polygons plus closed pine this time (Martin:
       "include and test, exclude later if needs be"); a polygon reads water if
       its backscatter FOLLOWS the water table: a rise (double bounce under a
       stand) or a fall of the dark share (open water on a visible floor).
    3. nothing touches Script 45, 46, the feed or the report: the outputs are
       diagnostics until Martin rules on them.

  Grid, masks, level interpolation, switching-level fitter and forest polygons
  are imported from tools/sentinel_wet_floor.py; nothing is reimplemented.

USAGE
  python3 tools/sentinel1_wet_floor.py --list                  # coverage by orbit (network, seconds)
  python3 tools/sentinel1_wet_floor.py --cache [--orbit 52]    # every scene on the orbit, resume-safe
  python3 tools/sentinel1_wet_floor.py --calibrate             # the S2 classes' radar signature -> thresholds
  python3 tools/sentinel1_wet_floor.py --series                # the scene series (winter and all-year)
  python3 tools/sentinel1_wet_floor.py --cells                 # per-cell switching levels vs the S2 ones
  python3 tools/sentinel1_wet_floor.py --forest                # the forest polygons and closed pine
  python3 tools/sentinel1_wet_floor.py --all                   # calibrate, series, cells, forest (cache first)
  python3 tools/sentinel1_wet_floor.py --check                 # the committed series regenerates from the cache

  Needs `pystac-client`, `planetary-computer`, `rasterio`, `scipy`, `geopandas`
  and network for --list/--cache; the rest runs from the cache. Per-scene arrays
  are cached under working/updates/sentinel_cache/s1_<date>_<orbit>.npz.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-29. T-94: the Sentinel-1 read. --list, --cache,
#   --calibrate (thresholds from the S2 classes on coincident scenes, absolute dB and ridge-normalised,
#   the vets as the meaning check), --series (winter and all-year, with the Script 45 curve fitted on
#   both sources for comparison), --cells (switching levels beside the S2 ones), --forest (the D-210
#   polygons plus closed pine, sign-tested), --check. Spec working/updates/NRG_spec_T94_sentinel1_read_2026-09-29.md.

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))

from utils.console_utils import banner, info, phase, progress, saved, step, warn  # noqa: E402
from utils.buckets import month_bucket                                         # noqa: E402
from utils.config import (                                                     # noqa: E402
    WET_AREA_GRID as GRID, S1_STAC_URL, S1_COLLECTION, S1_SINCE, S1_ORBIT, S1_SPECKLE_WINDOW,
    S1_MATCH_DAYS, S1_DB_FLOOR, S1_CELL_MIN_SCENES, NIR_BLACK_RATIO, NIR_DARK_RATIO,
    WET_AREA_FOREST_PLACEMARK,
)
from utils.paths import (                                                      # noqa: E402
    SENTINEL_TWO_CLASS_SERIES, SENTINEL_CELL_THRESHOLDS, SENTINEL_S1_MANIFEST, SENTINEL_S1_CALIBRATION,
    SENTINEL_S1_SERIES, SENTINEL_S1_CELL_THRESHOLDS, SENTINEL_S1_FOREST_SERIES, DATA_GEO_DIR,
    INT_LOCATIONS, OUT_44_SLACK_FLOOR_DATUM,
)
import sentinel_wet_floor as s2                                                # noqa: E402
from sentinel_wet_floor import (                                               # noqa: E402
    _grid, _shade_mask, _warren_mask, _wells_monthly, _level_at, _cell_switch_levels,
    _forest_polygons, _polygon_cells, CACHE, OUT, WINTER_MONTHS,
)

VETS = {"2021-03-24": DATA_GEO_DIR / "flood_extent_2021-03-24_vetted.kml",
        "2020-03-30": DATA_GEO_DIR / "flood_extent_2020-03-30_vetted.kml"}
FIG_DIR = OUT
MEASURES = ("vv_db", "vh_db", "vv_norm", "vh_norm", "ratio_db")

os.environ.setdefault("GDAL_HTTP_TIMEOUT", "120")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")


# ─────────────────────────────────────────────────────────────────────────────
# STAC and the cache
# ─────────────────────────────────────────────────────────────────────────────
def _site_bbox():
    from pyproj import Transformer                            # noqa: PLC0415
    g = GRID
    t = Transformer.from_crs(27700, 4326, always_xy=True)
    lon0, lat0 = t.transform(g["left"], g["bottom"])
    lon1, lat1 = t.transform(g["right"], g["top"])
    return [lon0, lat0, lon1, lat1]


def _search(since, until, orbit=None):
    """Every S1 RTC item intersecting the site window, {date: item}; one item per
    date on the orbit (the later duplicate of a split frame is dropped)."""
    from pystac_client import Client                          # noqa: PLC0415
    from shapely.geometry import box, shape                   # noqa: PLC0415
    bb = _site_bbox()
    cat = Client.open(S1_STAC_URL)
    q = {"sat:relative_orbit": {"eq": int(orbit)}} if orbit is not None else None
    items = list(cat.search(collections=[S1_COLLECTION], bbox=bb, datetime=f"{since}/{until}",
                            query=q).items())
    site = box(*bb)
    items = [i for i in items if shape(i.geometry).contains(site)]
    byd = {}
    for i in items:
        d = i.datetime.date().isoformat()
        if d not in byd:
            byd[d] = i
    return byd


def list_orbits():
    """Phase 0: coverage by relative orbit and pass direction."""
    from pystac_client import Client                          # noqa: PLC0415
    from shapely.geometry import box, shape                   # noqa: PLC0415
    bb = _site_bbox()
    cat = Client.open(S1_STAC_URL)
    items = list(cat.search(collections=[S1_COLLECTION], bbox=bb,
                            datetime=f"{S1_SINCE}/{pd.Timestamp.today().date()}").items())
    site = box(*bb)
    rows = {}
    for i in items:
        if not shape(i.geometry).contains(site):
            continue
        k = (int(i.properties["sat:relative_orbit"]), i.properties["sat:orbit_state"])
        d = i.datetime.date().isoformat()
        r = rows.setdefault(k, {"n": 0, "first": d, "last": d})
        r["n"] += 1; r["first"] = min(r["first"], d); r["last"] = max(r["last"], d)
    for (o, p), r in sorted(rows.items(), key=lambda kv: -kv[1]["n"]):
        step(f"orbit {o:3d} {p:10s} {r['n']:4d} scenes  {r['first']} .. {r['last']}"
             + ("   <- S1_ORBIT" if o == S1_ORBIT else ""))
    return 0


def _to_db(a):
    out = np.full(a.shape, S1_DB_FLOOR, np.float32)
    ok = np.isfinite(a) & (a > 0)
    out[ok] = 10.0 * np.log10(a[ok])
    return out


def _fetch(item, bands=("vv", "vh")):
    """The site window of each band, reprojected onto the 10 m OSGB grid (bilinear
    in linear power, then dB)."""
    import planetary_computer as pc                           # noqa: PLC0415
    import rasterio                                           # noqa: PLC0415
    from rasterio.warp import Resampling, reproject, transform_bounds  # noqa: PLC0415
    W, H, tr = _grid()
    g = GRID
    out = {}
    for b in bands:
        href = pc.sign(item.assets[b].href)
        # the S2 tool sets CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif at import; the RTC assets are .tiff
        with rasterio.Env(CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff"), rasterio.open(href) as src:
            wb = transform_bounds("EPSG:27700", src.crs, g["left"] - 200, g["bottom"] - 200,
                                  g["right"] + 200, g["top"] + 200)
            win = src.window(*wb).round_offsets().round_lengths()
            arr = src.read(1, window=win).astype("float32")
            if src.nodata is not None:
                arr[arr == src.nodata] = np.nan
            dst = np.full((H, W), np.nan, dtype="float32")
            reproject(arr, dst, src_transform=src.window_transform(win), src_crs=src.crs,
                      dst_transform=tr, dst_crs="EPSG:27700", src_nodata=np.nan, dst_nodata=np.nan,
                      resampling=Resampling.bilinear)
            out[b] = dst
    return out


def _cache_path(date, orbit):
    return CACHE / f"s1_{date}_{int(orbit)}.npz"


def cache(orbit, since, until):
    """Phase 1: every scene on the orbit, VV and VH in dB (unfiltered), resume-safe."""
    CACHE.mkdir(parents=True, exist_ok=True)
    byd = _search(since, until, orbit)
    todo = [d for d in sorted(byd) if not _cache_path(d, orbit).exists()]
    info(f"orbit {orbit}: {len(byd)} scenes {min(byd)} .. {max(byd)}; {len(todo)} to fetch")
    rows = []
    t0 = time.time()
    for n, d in enumerate(todo, 1):
        progress(n, len(todo), d, started=t0)
        it = byd[d]
        try:
            r = _fetch(it)
        except Exception as e:                                # noqa: BLE001
            warn(f"{d}: {e.__class__.__name__}: {str(e)[:80]}; skipped")
            continue
        vv, vh = _to_db(r["vv"]), _to_db(r["vh"])
        swath = np.isfinite(r["vv"]) & (r["vv"] > 0)
        np.savez_compressed(_cache_path(d, orbit), vv=vv, vh=vh, swath=swath,
                            stac_id=np.array(it.id), pass_=np.array(it.properties["sat:orbit_state"]))
    print(flush=True)
    for d, it in sorted(byd.items()):
        p = _cache_path(d, orbit)
        if p.exists():
            rows.append({"date": d, "stac_id": it.id, "orbit": int(orbit),
                         "pass": it.properties["sat:orbit_state"],
                         "platform": it.properties.get("platform", ""),
                         "sha256_vv": hashlib.sha256(np.load(p)["vv"].tobytes()).hexdigest()[:16]})
    M = pd.DataFrame(rows)
    SENTINEL_S1_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    M.to_csv(SENTINEL_S1_MANIFEST, index=False)
    saved(f"data/sentinel/{SENTINEL_S1_MANIFEST.name}  ({len(M)} scenes cached)")
    return 0


def _cached_scenes(orbit):
    out = {}
    for p in sorted(CACHE.glob(f"s1_*_{int(orbit)}.npz")):
        out[p.name.split("_")[1]] = p
    return out


def _load(p):
    """A cached scene: speckle-filtered VV/VH dB and the swath mask."""
    from scipy import ndimage as ndi                          # noqa: PLC0415
    z = np.load(p)
    k = int(S1_SPECKLE_WINDOW)
    vv = ndi.median_filter(z["vv"], size=k, mode="nearest") if k > 1 else z["vv"]
    vh = ndi.median_filter(z["vh"], size=k, mode="nearest") if k > 1 else z["vh"]
    return vv, vh, z["swath"].astype(bool)


def _measures(vv, vh, ridge):
    """The five candidate measures: absolute dB, ridge-normalised dB (the scene's
    median over the dry ridge cells subtracted, as the B8 rule's warren median
    does), and the VV-VH ratio."""
    mv, mh = float(np.median(vv[ridge])), float(np.median(vh[ridge]))
    return {"vv_db": vv, "vh_db": vh, "vv_norm": vv - mv, "vh_norm": vh - mh, "ratio_db": vv - vh}


def _masks():
    Wm = _warren_mask()
    shade = _shade_mask()
    floor = Wm & (~shade if shade is not None else True)
    ridge = Wm & ~floor
    return Wm, floor, ridge


def _level_series():
    M = _wells_monthly()["h_median"].dropna()
    return pd.Series(M.values, index=M.index + pd.offsets.MonthEnd(0))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — calibration against the S2 classes (hands-free)
# ─────────────────────────────────────────────────────────────────────────────
def _s2_scene_classes(date, floor):
    """The S2 classes of a committed-series scene from the cached B8: 2 open water,
    1 wet floor, 0 dry, -1 unseen."""
    p = CACHE / f"b8_{date}.npz"
    if not p.exists():
        return None
    z = np.load(p)
    nir, clear = z["nir"], z["clear"].astype(bool)
    ok = floor & clear
    med = float(np.median(nir[ok]))
    cls = np.full(nir.shape, -1, np.int8)
    cls[ok] = 0
    cls[ok & (nir <= NIR_DARK_RATIO * med)] = 1
    cls[ok & (nir <= NIR_BLACK_RATIO * med)] = 2
    return cls


def _youden(x, pos, lo_is_pos=True):
    """Threshold maximising TPR - FPR for the class `pos` (bool) on measure x;
    lo_is_pos: the class lies BELOW the threshold."""
    xs = np.sort(np.unique(np.round(x, 1)))
    if len(xs) < 3:
        return np.nan, np.nan
    best, bt = -1.0, np.nan
    npos, nneg = pos.sum(), (~pos).sum()
    for t in xs[::max(1, len(xs) // 400)]:
        sel = x <= t if lo_is_pos else x >= t
        j = (sel & pos).sum() / max(npos, 1) - (sel & ~pos).sum() / max(nneg, 1)
        if j > best:
            best, bt = j, t
    return float(bt), float(best)


def _iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else np.nan


def calibrate(orbit):
    """The radar signature of the S2 classes on coincident scenes, the thresholds
    that reproduce them, and the vets as the meaning check."""
    Wm, floor, ridge = _masks()
    S2 = pd.read_csv(SENTINEL_TWO_CLASS_SERIES)
    s1 = _cached_scenes(orbit)
    s1_dates = pd.to_datetime(list(s1))
    pairs = []
    for d in S2["date"]:
        dt = pd.Timestamp(d)
        gap = np.abs((s1_dates - dt).days)
        if len(gap) and gap.min() <= S1_MATCH_DAYS:
            pairs.append((d, list(s1)[int(np.argmin(gap))], int(gap.min())))
    info(f"{len(pairs)} S2 scenes of {len(S2)} have an S1 scene on orbit {orbit} within {S1_MATCH_DAYS} d")
    # pooled per-cell samples, one row per (pair, floor cell seen by both)
    samp = {m: [] for m in MEASURES}
    cls_all = []
    per_pair = []
    scenes = {}
    for d2, d1, gap in pairs:
        cls = _s2_scene_classes(d2, floor)
        if cls is None:
            warn(f"{d2}: no cached B8; pair skipped")
            continue
        vv, vh, sw = _load(s1[d1])
        ok = (cls >= 0) & sw
        meas = _measures(vv, vh, ridge & sw)
        for m in MEASURES:
            samp[m].append(meas[m][ok])
        cls_all.append(cls[ok])
        scenes[d2] = (d1, gap, cls, meas, ok)
    if not cls_all:
        warn("no pairs; calibration not written")
        return 1
    C = np.concatenate(cls_all)
    rows = []
    best = {}
    for m in MEASURES:
        X = np.concatenate(samp[m])
        med = {k: float(np.median(X[C == k])) for k in (0, 1, 2) if (C == k).any()}
        iqr = {k: tuple(np.percentile(X[C == k], [25, 75])) for k in (0, 1, 2) if (C == k).any()}
        # open water: the dark tail
        t_w, j_w = _youden(X, C == 2, lo_is_pos=True)
        # wet floor against dry: on whichever side its median lies
        side = "bright" if med.get(1, 0) > med.get(0, 0) else "dark"
        sub = C <= 1
        t_f, j_f = _youden(X[sub], C[sub] == 1, lo_is_pos=(side == "dark"))
        rows.append(dict(measure=m, n_cells=int(len(X)), n_pairs=len(cls_all),
                         dry_median=med.get(0), dry_q25=iqr.get(0, (np.nan,))[0], dry_q75=iqr.get(0, (np.nan, np.nan))[1],
                         wet_floor_median=med.get(1), wet_floor_q25=iqr.get(1, (np.nan,))[0], wet_floor_q75=iqr.get(1, (np.nan, np.nan))[1],
                         open_water_median=med.get(2), open_water_q25=iqr.get(2, (np.nan,))[0], open_water_q75=iqr.get(2, (np.nan, np.nan))[1],
                         water_threshold=t_w, water_youden=j_w, wet_floor_side=side,
                         wet_floor_threshold=t_f, wet_floor_youden=j_f))
        best[m] = (t_w, j_w, side, t_f, j_f)
        step(f"{m:9s} dry {med.get(0, np.nan):6.1f}  wet floor {med.get(1, np.nan):6.1f} ({side})  open water "
             f"{med.get(2, np.nan):6.1f} dB | water <= {t_w:6.1f} (J {j_w:.2f}); wet floor {side} of {t_f:6.1f} (J {j_f:.2f})")
    cal = pd.DataFrame(rows)
    # per-pair IoU of the S1 rule against the S2 class, for the best measure by Youden
    m_w = cal.sort_values("water_youden", ascending=False).iloc[0]["measure"]
    m_f = cal.sort_values("wet_floor_youden", ascending=False).iloc[0]["measure"]
    info(f"best measure: open water {m_w}, wet floor {m_f}")
    for d2, (d1, gap, cls, meas, ok) in scenes.items():
        t_w = best[m_w][0]; side, t_f = best[m_f][2], best[m_f][3]
        water1 = ok & (meas[m_w] <= t_w)
        floor1 = ok & ~water1 & ((meas[m_f] <= t_f) if side == "dark" else (meas[m_f] >= t_f))
        per_pair.append(dict(s2_date=d2, s1_date=d1, gap_days=gap, n_cells=int(ok.sum()),
                             s2_open_water=int((cls == 2).sum()), s1_open_water=int(water1.sum()),
                             iou_open_water=_iou(cls == 2, water1),
                             s2_wet_floor=int((cls == 1).sum()), s1_wet_floor=int(floor1.sum()),
                             iou_wet_floor=_iou(cls == 1, floor1),
                             iou_dark_total=_iou(cls >= 1, water1 | floor1)))
    P = pd.DataFrame(per_pair)
    # the vets: the meaning check (never the fit)
    vet_rows = []
    import geopandas as gpd                                    # noqa: PLC0415
    from rasterio.features import rasterize                    # noqa: PLC0415
    from rasterio.transform import from_origin                 # noqa: PLC0415
    from utils.kml_io import read_kml                          # noqa: PLC0415
    W, H, tr = _grid()
    for vd, kml in VETS.items():
        if not kml.exists():
            continue
        dt = pd.Timestamp(vd)
        gap = np.abs((s1_dates - dt).days)
        if not len(gap) or gap.min() > 7:
            continue
        d1 = list(s1)[int(np.argmin(gap))]
        vet = read_kml(kml).to_crs("EPSG:27700")
        fine = from_origin(GRID["left"], GRID["top"], 1.0, 1.0)
        Vf = rasterize([(x, 1) for x in vet.geometry], out_shape=(H * 10, W * 10), transform=fine,
                       fill=0, dtype="uint8").astype(float).reshape(H, 10, W, 10).mean(axis=(1, 3))
        truth = (Vf >= 0.5) & floor
        vv, vh, sw = _load(s1[d1])
        meas = _measures(vv, vh, ridge & sw)
        ok = floor & sw
        t_w = best[m_w][0]; side, t_f = best[m_f][2], best[m_f][3]
        water1 = ok & (meas[m_w] <= t_w)
        floor1 = ok & ~water1 & ((meas[m_f] <= t_f) if side == "dark" else (meas[m_f] >= t_f))
        vet_rows.append(dict(vet_date=vd, s1_date=d1, gap_days=int(gap.min()), vet_cells=int(truth.sum()),
                             iou_open_water=_iou(truth, water1), iou_dark_total=_iou(truth, water1 | floor1),
                             s1_open_water=int(water1.sum()), s1_wet_floor=int(floor1.sum())))
        step(f"vet {vd} vs S1 {d1} ({int(gap.min())} d): IoU open water {vet_rows[-1]['iou_open_water']:.2f}, "
             f"dark total {vet_rows[-1]['iou_dark_total']:.2f} (S2 rule: 0.68 / 0.58 on the two vets)")
    cal["role"] = "measure"
    out = pd.concat([cal, P.assign(role="pair"), pd.DataFrame(vet_rows).assign(role="vet")], ignore_index=True)
    out.insert(0, "orbit", int(orbit))
    out.to_csv(SENTINEL_S1_CALIBRATION, index=False)
    saved(f"data/sentinel/{SENTINEL_S1_CALIBRATION.name}")
    if len(P):
        step(f"per-pair IoU against the S2 class: open water median {P['iou_open_water'].median():.2f}, "
             f"wet floor {P['iou_wet_floor'].median():.2f}, dark total {P['iou_dark_total'].median():.2f}")
    _plot_calibration(cal, samp, C, m_w, m_f, orbit)
    return 0


def _rule():
    """The calibrated rule from the committed calibration file."""
    cal = pd.read_csv(SENTINEL_S1_CALIBRATION)
    cal = cal[cal["role"] == "measure"]
    w = cal.sort_values("water_youden", ascending=False).iloc[0]
    f = cal.sort_values("wet_floor_youden", ascending=False).iloc[0]
    return dict(m_w=w["measure"], t_w=float(w["water_threshold"]),
                m_f=f["measure"], side=f["wet_floor_side"], t_f=float(f["wet_floor_threshold"]))


def _classify(meas, ok, rule):
    water = ok & (meas[rule["m_w"]] <= rule["t_w"])
    wet = ok & ~water & ((meas[rule["m_f"]] <= rule["t_f"]) if rule["side"] == "dark"
                         else (meas[rule["m_f"]] >= rule["t_f"]))
    return water, wet


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — the series
# ─────────────────────────────────────────────────────────────────────────────
def _fit_curve(h, a_ha):
    """Script 45's form, a*exp(b*h), in log space; returns a, b, rho, n."""
    from scipy.stats import spearmanr                          # noqa: PLC0415
    m = np.isfinite(h) & np.isfinite(a_ha) & (a_ha > 0)
    if m.sum() < 5:
        return np.nan, np.nan, np.nan, int(m.sum())
    b, la = np.polyfit(h[m], np.log(a_ha[m]), 1)
    rho = spearmanr(h[m], a_ha[m])[0]
    return float(np.exp(la)), float(b), float(rho), int(m.sum())


def series(orbit):
    Wm, floor, ridge = _masks()
    rule = _rule()
    info(f"rule: open water {rule['m_w']} <= {rule['t_w']:.1f}; wet floor {rule['m_f']} {rule['side']} of {rule['t_f']:.1f}")
    end = _level_series()
    s1 = _cached_scenes(orbit)
    rows = []
    t0 = time.time()
    sc = float(GRID["res"]) ** 2 / 1e4
    for n, (d, p) in enumerate(s1.items(), 1):
        progress(n, len(s1), d, started=t0)
        h, dh = _level_at(d, end)
        vv, vh, sw = _load(p)
        ok = floor & sw
        if ok.sum() < 0.5 * floor.sum():
            continue
        meas = _measures(vv, vh, ridge & sw)
        water, wet = _classify(meas, ok, rule)
        scale = floor.sum() / ok.sum()
        rows.append({"date": d, "orbit": int(orbit), "month": month_bucket(pd.Timestamp(d)).strftime("%Y-%m"),
                     "winter": pd.Timestamp(d).month in WINTER_MONTHS,
                     "h_scene": round(h, 3) if np.isfinite(h) else np.nan,
                     "dh_month": round(dh, 3) if np.isfinite(dh) else np.nan,
                     "n_floor_seen": int(ok.sum()),
                     "ridge_median_vv_db": round(float(np.median(vv[ridge & sw])), 2),
                     "floor_median_vv_db": round(float(np.median(vv[ok])), 2),
                     "open_water_ha": round(water.sum() * sc * scale, 2),
                     "wet_floor_ha": round(wet.sum() * sc * scale, 2),
                     "dark_total_ha": round((water.sum() + wet.sum()) * sc * scale, 2)})
    print(flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(SENTINEL_S1_SERIES, index=False)
    saved(f"data/sentinel/{SENTINEL_S1_SERIES.name}  ({len(R)} scenes, {int(R['h_scene'].notna().sum())} with a level)")
    # the comparison: S2 series vs S1 series on the same curve, winter and all-year
    S2 = pd.read_csv(SENTINEL_TWO_CLASS_SERIES)
    for lab, cols in (("open_water_ha", "open_water_ha"), ("wet_floor_ha", "wet_floor_ha"), ("dark_total_ha", "dark_total_ha")):
        a2, b2, r2, n2 = _fit_curve(S2["h_scene"].values, S2[cols].values)
        Rw = R[R["winter"] & R["h_scene"].notna()]
        Ra = R[R["h_scene"].notna()]
        aw, bw, rw, nw = _fit_curve(Rw["h_scene"].values, Rw[cols].values)
        aa, ba, ra, na = _fit_curve(Ra["h_scene"].values, Ra[cols].values)
        step(f"{lab:14s} S2 winter n={n2:3d} rho {r2:+.2f} b {b2:5.2f} | S1 winter n={nw:3d} rho {rw:+.2f} b {bw:5.2f}"
             f" | S1 all-year n={na:3d} rho {ra:+.2f} b {ba:5.2f}")
    _plot_series(R, S2, orbit)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 — per-cell switching levels
# ─────────────────────────────────────────────────────────────────────────────
def cells(orbit, all_year=False):
    Wm, floor, ridge = _masks()
    rule = _rule()
    end = _level_series()
    s1 = _cached_scenes(orbit)
    stack = []
    t0 = time.time()
    for n, (d, p) in enumerate(s1.items(), 1):
        progress(n, len(s1), d, started=t0)
        if not all_year and pd.Timestamp(d).month not in WINTER_MONTHS:
            continue
        h, _ = _level_at(d, end)
        if not np.isfinite(h):
            continue
        vv, vh, sw = _load(p)
        ok = floor & sw
        meas = _measures(vv, vh, ridge & sw)
        water, wet = _classify(meas, ok, rule)
        stack.append((h, ok, water, water | wet))
    print(flush=True)
    order = np.argsort([s_[0] for s_ in stack])
    h = np.array([stack[i][0] for i in order])
    seen = np.stack([stack[i][1] for i in order]); black = np.stack([stack[i][2] for i in order])
    dark = np.stack([stack[i][3] for i in order])
    hb, eb = _cell_switch_levels(black, seen, h)
    hd, ed = _cell_switch_levels(dark, seen, h)
    hd = np.minimum(hd, hb)
    hb[seen.sum(0) < S1_CELL_MIN_SCENES] = np.inf; hd[seen.sum(0) < S1_CELL_MIN_SCENES] = np.inf
    np.savez_compressed(SENTINEL_S1_CELL_THRESHOLDS, h_open_water=hb, h_wet_floor=hd, err_open_water=eb,
                        err_wet_floor=ed, n_seen=seen.sum(0), floor=floor, all_year=np.array(all_year),
                        n_scenes=np.array(len(h)),
                        grid=np.array([GRID["left"], GRID["bottom"], GRID["right"], GRID["top"], GRID["res"]]))
    step(f"{len(h)} scenes: {int((np.isfinite(hb) & floor).sum())} cells ever open water, "
         f"{int((np.isfinite(hd) & floor).sum())} ever wet floor, of {int(floor.sum())} on the floor")
    saved(f"data/sentinel/{SENTINEL_S1_CELL_THRESHOLDS.name}")
    # against the S2 switching levels
    if SENTINEL_CELL_THRESHOLDS.exists():
        z = np.load(SENTINEL_CELL_THRESHOLDS)
        for lab, s1v, s2v in (("open water", hb, z["h_open_water"]), ("wet floor", hd, z["h_wet_floor"])):
            both = np.isfinite(s1v) & np.isfinite(s2v) & floor
            only1 = np.isfinite(s1v) & ~np.isfinite(s2v) & floor
            only2 = ~np.isfinite(s1v) & np.isfinite(s2v) & floor
            if both.sum() > 10:
                r = np.corrcoef(s1v[both], s2v[both])[0, 1]
                mad = float(np.median(np.abs(s1v[both] - s2v[both])))
                step(f"{lab}: {int(both.sum())} cells resolved by both (r {r:+.2f}, median |diff| {mad:.2f} m); "
                     f"S1 only {int(only1.sum())}, S2 only {int(only2.sum())}")
        _plot_cells(hb, hd, z, floor, orbit, all_year)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — the forest, closed pine included
# ─────────────────────────────────────────────────────────────────────────────
def forest(orbit):
    from scipy.stats import spearmanr                          # noqa: PLC0415
    Wm, floor, ridge = _masks()
    rule = _rule()
    end = _level_series()
    polys, forest_geom = _forest_polygons()
    W, H, tr = _grid()
    pid = np.zeros((H, W), np.int8)
    names = list(polys)
    for k, n in enumerate(names, 1):
        c = _polygon_cells(polys[n]["geom"]) & ~pid.astype(bool)
        pid[c] = k
    pine = _polygon_cells(forest_geom) & ~pid.astype(bool)
    names.append("closed_pine"); pid[pine] = len(names)
    roles = {n: polys[n]["role"] for n in polys}
    roles["closed_pine"] = "the rest of the Forest placemark: closed Corsican pine (Martin: include and test)"
    for k, n in enumerate(names, 1):
        step(f"{n}: {int((pid == k).sum())} cells - {roles[n]}")
    s1 = _cached_scenes(orbit)
    rows = []
    t0 = time.time()
    for n_, (d, p) in enumerate(s1.items(), 1):
        progress(n_, len(s1), d, started=t0)
        h, dh = _level_at(d, end)
        vv, vh, sw = _load(p)
        meas = _measures(vv, vh, ridge & sw)
        for k, n in enumerate(names, 1):
            since = polys[n]["since"] if n in polys else None
            if since and d < since:
                continue
            ok = (pid == k) & sw
            if not ok.any():
                continue
            water, wet = _classify(meas, ok, rule)
            rows.append({"date": d, "polygon": n, "h_scene": round(h, 3) if np.isfinite(h) else np.nan,
                         "winter": pd.Timestamp(d).month in WINTER_MONTHS, "n_cells": int(ok.sum()),
                         "vv_db": round(float(np.median(vv[ok])), 2), "vh_db": round(float(np.median(vh[ok])), 2),
                         "vv_norm": round(float(np.median(meas["vv_norm"][ok])), 2),
                         "dark_share": round(float(water.sum() / ok.sum()), 3),
                         "wet_share": round(float((water.sum() + wet.sum()) / ok.sum()), 3)})
    print(flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(SENTINEL_S1_FOREST_SERIES, index=False)
    saved(f"data/sentinel/{SENTINEL_S1_FOREST_SERIES.name}")
    summ = []
    for n in names:
        s = R[(R["polygon"] == n) & R["h_scene"].notna()]
        sw_ = s[s["winter"]]
        rec = {"polygon": n, "n_scenes": len(s), "n_winter": len(sw_), "role": roles[n]}
        for lab, sub in (("", s), ("_winter", sw_)):
            for col in ("vv_norm", "vh_db", "dark_share"):
                rho, pv = spearmanr(sub[col], sub["h_scene"]) if len(sub) >= 8 else (np.nan, np.nan)
                rec[f"rho_{col}{lab}"], rec[f"p_{col}{lab}"] = float(rho), float(pv)
        rec["vv_norm_median"] = float(s["vv_norm"].median()) if len(s) else np.nan
        rec["dark_share_median"] = float(s["dark_share"].median()) if len(s) else np.nan
        up = rec["rho_vv_norm_winter"] > 0.3 and rec["p_vv_norm_winter"] < 0.01
        dn = rec["rho_dark_share_winter"] > 0.3 and rec["p_dark_share_winter"] < 0.01
        rec["reading"] = ("backscatter rises with the level: double bounce, water under the stand" if up else
                          "dark share rises with the level: open water on a visible floor" if dn else
                          "does not follow the water table")
        summ.append(rec)
        step(f"{n:22s} n={len(s):3d} vv_norm rho {rec['rho_vv_norm_winter']:+.2f} (p {rec['p_vv_norm_winter']:.1e}) "
             f"dark share rho {rec['rho_dark_share_winter']:+.2f} - {rec['reading']}")
    pd.DataFrame(summ).to_csv(OUT / "s1_forest_summary.csv", index=False)
    saved("working/updates/s1_forest_summary.csv")
    # the forest wells beside their cells
    if OUT_44_SLACK_FLOOR_DATUM.exists() and INT_LOCATIONS.exists():
        from utils.data_utils import normalize_well_name        # noqa: PLC0415
        s44 = pd.read_csv(OUT_44_SLACK_FLOOR_DATUM); s44 = s44[s44["row"] == "well"]
        loc = pd.read_csv(INT_LOCATIONS); loc["k"] = loc["Match_ID"].map(normalize_well_name); loc = loc.set_index("k")
        yy, xx = np.indices(pid.shape)
        left, top, res = GRID["left"], GRID["top"], GRID["res"]
        cx, cy = left + (xx + 0.5) * res, top - (yy + 0.5) * res
        wr = []
        for w in [w for w in s44["well"] if w in loc.index and bool(loc.loc[w, "in_forest"])]:
            e, n_ = float(loc.loc[w, "E"]), float(loc.loc[w, "N"])
            near = (np.hypot(cx - e, cy - n_) <= 50) & (pid > 0)
            pk = sorted({names[k - 1] for k in np.unique(pid[near])}) if near.any() else []
            wr.append(dict(well=w, polygons="; ".join(pk), n_cells=int(near.sum()),
                           reading="; ".join(f"{r['polygon']}: {r['reading']}" for r in summ if r["polygon"] in pk)))
        pd.DataFrame(wr).to_csv(OUT / "s1_forest_wells.csv", index=False)
        saved("working/updates/s1_forest_wells.csv")
    _plot_forest(R, names, orbit)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# figures (caption-free)
# ─────────────────────────────────────────────────────────────────────────────
def _plt():
    import matplotlib                                          # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                            # noqa: PLC0415
    return plt


def _plot_calibration(cal, samp, C, m_w, m_f, orbit):
    plt = _plt()
    fig, axes = plt.subplots(1, len(MEASURES), figsize=(3.2 * len(MEASURES), 3.6), sharey=False)
    for ax, m in zip(axes, MEASURES):
        X = np.concatenate(samp[m])
        for k, lab, col in ((0, "dry (S2)", "#c8b070"), (1, "wet floor (S2)", "#4c9ed9"), (2, "open water (S2)", "#1b3a6b")):
            if (C == k).any():
                ax.hist(X[C == k], bins=60, density=True, histtype="step", color=col, label=lab)
        r = cal[cal["measure"] == m].iloc[0]
        ax.axvline(r["water_threshold"], color="#1b3a6b", ls="--", lw=0.9)
        ax.axvline(r["wet_floor_threshold"], color="#4c9ed9", ls="--", lw=0.9)
        ax.set_title(m + ("  [water]" if m == m_w else "") + ("  [floor]" if m == m_f else ""), fontsize=9)
        ax.set_xlabel("dB")
    axes[0].legend(fontsize=7)
    fig.suptitle(f"Sentinel-1 orbit {orbit}: the radar signature of the Sentinel-2 classes on coincident scenes", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "s1_calibration.png", dpi=150); plt.close(fig)
    saved("working/updates/s1_calibration.png")


def _plot_series(R, S2, orbit):
    plt = _plt()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    Rl = R[R["h_scene"].notna()]
    for ax, col in zip(axes, ("open_water_ha", "wet_floor_ha", "dark_total_ha")):
        ax.scatter(Rl[~Rl["winter"]]["h_scene"], Rl[~Rl["winter"]][col], s=8, color="#c8b070", label="S1 Apr-Oct")
        ax.scatter(Rl[Rl["winter"]]["h_scene"], Rl[Rl["winter"]][col], s=10, color="#4c9ed9", label="S1 Nov-Mar")
        ax.scatter(S2["h_scene"], S2[col], s=22, marker="s", facecolor="none", edgecolor="k", label="S2 (committed)")
        for lab, sub, c in (("S1 winter", Rl[Rl["winter"]], "#4c9ed9"), ("S2", S2, "k")):
            a, b, rho, n = _fit_curve(sub["h_scene"].values, sub[col].values)
            if np.isfinite(a):
                hh = np.linspace(Rl["h_scene"].min(), Rl["h_scene"].max(), 50)
                ax.plot(hh, a * np.exp(b * hh), color=c, lw=1, label=f"{lab}: rho {rho:+.2f}, n {n}")
        ax.set_xlabel("network-median level at the scene date (m, 0 = ground)"); ax.set_ylabel("ha")
        ax.set_title(col.replace("_", " "), fontsize=10, loc="left"); ax.grid(alpha=0.3); ax.legend(fontsize=6.5)
    fig.suptitle(f"Sentinel-1 orbit {orbit} against the water table, beside the Sentinel-2 series", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "s1_series.png", dpi=150); plt.close(fig)
    saved("working/updates/s1_series.png")


def _plot_cells(hb, hd, z, floor, orbit, all_year):
    plt = _plt()
    from utils.map_utils import add_en_axes                    # noqa: PLC0415
    extent = (GRID["left"], GRID["right"], GRID["bottom"], GRID["top"])
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5))
    panels = ((hd, "S1 wet floor"), (z["h_wet_floor"], "S2 wet floor"), (hb, "S1 open water"), (z["h_open_water"], "S2 open water"))
    for ax, (v, lab) in zip(axes.ravel(), panels):
        m = np.where(floor & np.isfinite(v), v, np.nan)
        im = ax.imshow(m, extent=extent, origin="upper", cmap="viridis_r", vmin=-0.9, vmax=0.1, interpolation="nearest")
        ax.imshow(np.ma.masked_where(~(floor & ~np.isfinite(v)), np.ones_like(m)), extent=extent, origin="upper",
                  cmap="Greys", vmin=0, vmax=3, interpolation="nearest")
        add_en_axes(ax, apply_extent=False)
        ax.set_title(f"{lab}: {int((floor & np.isfinite(v)).sum())} cells resolved", fontsize=9, loc="left")
    fig.colorbar(im, ax=axes, shrink=0.6, label="switching level (m, network median, 0 = ground)")
    fig.suptitle(f"Per-cell switching levels: Sentinel-1 orbit {orbit} ({'all year' if all_year else 'winter'}) beside Sentinel-2", fontsize=10)
    fig.savefig(FIG_DIR / "s1_cells.png", dpi=140); plt.close(fig)
    saved("working/updates/s1_cells.png")


def _plot_forest(R, names, orbit):
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    Rl = R[R["h_scene"].notna() & R["winter"]]
    for n in names:
        s = Rl[Rl["polygon"] == n].sort_values("h_scene")
        if len(s):
            axes[0].plot(s["h_scene"], s["vv_norm"], marker="o", ms=2.5, lw=0.6, label=n.replace("_", " "))
            axes[1].plot(s["h_scene"], s["dark_share"], marker="o", ms=2.5, lw=0.6, label=n.replace("_", " "))
    axes[0].set_ylabel("median VV, ridge-normalised (dB)"); axes[1].set_ylabel("share of cells below the water threshold")
    for ax in axes:
        ax.set_xlabel("network-median level at the scene date (m, 0 = ground)"); ax.grid(alpha=0.3)
    axes[0].legend(fontsize=7)
    axes[0].set_title("(a) backscatter against the water table (a rise = double bounce)", fontsize=9, loc="left")
    axes[1].set_title("(b) dark share against the water table (a rise = open water on the floor)", fontsize=9, loc="left")
    fig.suptitle(f"Sentinel-1 orbit {orbit}: the forest polygons and closed pine, winter scenes", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "s1_forest.png", dpi=150); plt.close(fig)
    saved("working/updates/s1_forest.png")


# ─────────────────────────────────────────────────────────────────────────────
def check(orbit):
    """The committed series regenerates from the cache (the manifest names the scenes)."""
    if not SENTINEL_S1_SERIES.exists():
        warn("no committed S1 series"); return 1
    old = pd.read_csv(SENTINEL_S1_SERIES)
    tmp = SENTINEL_S1_SERIES.with_suffix(".check.csv")
    keep = SENTINEL_S1_SERIES
    try:
        globals()["SENTINEL_S1_SERIES"] = tmp
        series(orbit)
    finally:
        globals()["SENTINEL_S1_SERIES"] = keep
    new = pd.read_csv(tmp); tmp.unlink()
    same = old.shape == new.shape and np.allclose(old["dark_total_ha"], new["dark_total_ha"], atol=0.05)
    step(f"series {'regenerates' if same else 'DIFFERS'} ({len(old)} vs {len(new)} rows)")
    return 0 if same else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true"); ap.add_argument("--cache", action="store_true")
    ap.add_argument("--calibrate", action="store_true"); ap.add_argument("--series", action="store_true")
    ap.add_argument("--cells", action="store_true"); ap.add_argument("--forest", action="store_true")
    ap.add_argument("--all", action="store_true"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--orbit", type=int, default=S1_ORBIT)
    ap.add_argument("--all-year", action="store_true", help="--cells on every scene, not winter only")
    ap.add_argument("--since", default=S1_SINCE); ap.add_argument("--until", default=str(pd.Timestamp.today().date()))
    a = ap.parse_args()
    banner("Sentinel-1 radar read (T-94)", f"orbit {a.orbit}", __version__)
    rc = 0
    if a.list:
        rc |= list_orbits()
    if a.cache:
        rc |= cache(a.orbit, a.since, a.until)
    if a.calibrate or a.all:
        phase(2, "Calibration against the Sentinel-2 classes"); rc |= calibrate(a.orbit)
    if a.series or a.all:
        phase(3, "The series"); rc |= series(a.orbit)
    if a.cells or a.all:
        phase(4, "Per-cell switching levels"); rc |= cells(a.orbit, a.all_year)
    if a.forest or a.all:
        phase(5, "The forest"); rc |= forest(a.orbit)
    if a.check:
        rc |= check(a.orbit)
    return rc


if __name__ == "__main__":
    sys.exit(main())
