#!/usr/bin/env python3
"""
sentinel_wet_floor.py — the wet-slack-floor series from Sentinel-2, against the wells.

WHAT THIS IS

  A TOOL (not a pipeline step; writes to working/updates/). It reads every
  Sentinel-2 L2A scene over Newborough Warren from the public AWS archive
  (Earth Search STAC, anonymous, cloud-optimised GeoTIFFs — only the warren's
  window is fetched), applies ONE relative darkness rule calibrated once on the
  vetted 2021-03-24 extent (D-169), and sets the resulting wet-floor area of
  each scene against the dipwell record for that month.

WHAT IT MEASURES, AND WHAT IT DOES NOT

  Wet slack floor: surface-saturated ground or a shallow sheet over the sward, as
  a dark surface in the visible bands at 10 m. Martin (2026-09-15): most of the
  bodies vetted on 24/3/2021 WERE standing water, mostly under 15 cm, and that
  water was persistent - March does not drain in a week. Sentinel's NDWI on 30/3
  and 4/4/2021 nonetheless saw under 2 ha of open water: 15 cm over a dense sward
  leaves the leaf tops at the surface and the NIR returns from them, so shallow
  flooded sward is INVISIBLE to NDWI at 10 m. NDWI is therefore reported as the
  deep-pool fraction for reference and is not the measurement. The dark read is,
  and it cannot split standing water from saturation.

  Measured 2026-09-15 (sandbox, 186 clear scenes 2016-11 to 2026-07):
    - calibration: brightness <= SENTINEL_DARK_RATIO x the scene's warren median
      reproduces the vetted 2021 extent at IoU 0.68 (4/4) / 0.58 (30/3) on 10 m
      cells at least half wet;
    - WITHIN WINTER (Nov-Mar, 57 scenes with a well month) the dark area tracks
      the median well level at rho +0.52 (p 3e-5), by month (n=31) +0.56;
    - OUTSIDE WINTER it means nothing: August scenes with every well a metre down
      return 13-26 % dark - the summer sward on the slack floors, the same floor
      the dry-date union measured. The winter floor is ~60-80 ha in the driest
      winters; the flood signal is the excess above it.
    - a per-cell anomaly against each cell's own winter norm is WORSE (rho 0.47,
      IoU 0.35): most winters the floors are wet, so the norm contains the water.

USAGE
  python3 tools/sentinel_wet_floor.py                 # whole archive, resume-safe
  python3 tools/sentinel_wet_floor.py --since 2020-10-01 --until 2021-04-30
  python3 tools/sentinel_wet_floor.py --calibrate     # refit SENTINEL_DARK_RATIO on TRUTH_KML
  python3 tools/sentinel_wet_floor.py --validate 2020-03-30   # score the FIXED rule on a 2nd vet

  Needs `pystac-client` (pip install pystac-client) and network. Per-scene
  rasters are cached under working/updates/sentinel_cache/ (gitignored size).
"""
from __future__ import annotations

__version__ = "1.2.1"  # Hollingham (2026) - 2026-09-15. The phase 29 mask is
#   now the FLOOR mask (cells scored only where the DEM says water can lie);
#   --validate scores whole-warren and floor-only, the series carries
#   wet_floor_pct_masked on the floor.
# v1.2.0  # Hollingham (2026) - 2026-09-15. Haze gate tightened
#   (TILE_CLOUD_MAX 45 -> 25, CLEAR_MIN_PCT 85 -> 95) after 2019-03-26; the
#   phase 29 shade mask applied in --validate (scored with and without) and as
#   wet_floor_pct_masked in the series.
# v1.1.0  # Hollingham (2026) - 2026-09-15. --validate DATE: the fixed
#   rule scored on a second vetted extent (2020-03-30) inside the ground the
#   Google Earth frames cover (W94_26_<date>_covered.geojson); no refit.
# v1.0.2  # Hollingham (2026) - 2026-09-15. A cloudy scene cached as
#   an empty placeholder was returned as if usable on the next pass and
#   crashed main() (IndexError at np.median); read_scene now returns None.
# v1.0.1  # Hollingham (2026) - 2026-09-15. A progress bar with
#   elapsed and remaining time on every scene (Martin's rule, CLAUDE.md
#   "SHOW PROGRESS"); the 20-scene ticker looked hung.
# v1.0.0  # Hollingham (2026) - 2026-09-15. First cut, from the
#   2026-09-15 sandbox series; see CHANGELOG_delta_2026-09-15b.

import argparse
import os
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.console_utils import banner, info, phase, progress, saved, step, warn  # noqa: E402
from utils.paths import DATA_FLOOD_CAL_LEVELS, DATA_GEO_DIR   # noqa: E402

OUT = REPO / "working" / "updates"
CACHE = OUT / "sentinel_cache"
STAC_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-l2a"
WARREN_KML = DATA_GEO_DIR / "warren.kml"
TRUTH_KML = DATA_GEO_DIR / "flood_extent_2021-03-24_vetted.kml"
WELLS_ALL = REPO / "outputs" / "01_wells_all.csv"
# the analysis window, OSGB, 10 m cells — the warren with a margin
GRID = dict(left=239770, bottom=362090, right=244360, top=364940, res=10)
TILE_CLOUD_MAX = 25.0        # STAC tile-level cloud cover admitted to the search. Was 45
#                              until 2026-09-15: 2019-03-26 (40 % tile cloud, median 1186 against
#                              824 two days earlier) read 44 % dark — thin cloud brightens the
#                              median and the relative rule then floods the frame
CLEAR_MIN_PCT = 95.0         # share of the warren cloud-free (SCL) for a scene to count (was 85)
FLOOR_MASK = OUT / "W94_29_floor_mask.geojson"   # warren_flood_prep phase 29; optional
FLOOR_CELL_MIN = 0.5         # a 10 m cell at least this much on the floor is scored
SCL_BAD = (0, 1, 3, 8, 9, 10)  # nodata, saturated, cloud shadow, cloud (med/high), cirrus
SENTINEL_DARK_RATIO = 0.86   # brightness <= this x scene median = wet floor. Calibrated
#                              on 2021-04-04 against the vetted extent (IoU 0.684); --calibrate refits
CALIBRATION_SCENES = ("2021-04-04", "2021-03-30")
VALIDATE_WINDOW_DAYS = 14    # scenes scored either side of a vetted date
WINTER_MONTHS = (11, 12, 1, 2, 3)

os.environ.setdefault("GDAL_HTTP_TIMEOUT", "120")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")


def _grid():
    from rasterio.transform import from_origin                 # noqa: PLC0415
    g = GRID
    W = int((g["right"] - g["left"]) / g["res"])
    H = int((g["top"] - g["bottom"]) / g["res"])
    return W, H, from_origin(g["left"], g["top"], g["res"], g["res"])


def _shade_mask():
    """Cells to LEAVE OUT: less than FLOOR_CELL_MIN on the phase 29 floor, or None."""
    if not FLOOR_MASK.exists():
        return None
    import geopandas as gpd                                   # noqa: PLC0415
    from rasterio.features import rasterize                   # noqa: PLC0415
    from rasterio.transform import from_origin                # noqa: PLC0415
    W, H, _ = _grid()
    g = GRID
    fine = from_origin(g["left"], g["top"], 1.0, 1.0)
    Sf = rasterize([(x, 1) for x in gpd.read_file(FLOOR_MASK).geometry],
                   out_shape=(H * 10, W * 10), transform=fine, fill=0, dtype="uint8").astype(float)
    return Sf.reshape(H, 10, W, 10).mean(axis=(1, 3)) < FLOOR_CELL_MIN


def _warren_mask():
    from rasterio.features import rasterize                   # noqa: PLC0415
    from shapely.ops import unary_union                       # noqa: PLC0415
    from utils.kml_io import read_kml                         # noqa: PLC0415
    W, H, tr = _grid()
    w = unary_union(list(read_kml(WARREN_KML).to_crs("EPSG:27700").geometry))
    return rasterize([(w, 1)], out_shape=(H, W), transform=tr, fill=0,
                     dtype="uint8").astype(bool)


def _fetch(item, bands):
    """The warren's window of each band, reprojected onto the 10 m OSGB grid."""
    import rasterio                                           # noqa: PLC0415
    from rasterio.warp import Resampling, reproject, transform_bounds  # noqa: PLC0415
    W, H, tr = _grid()
    g = GRID
    out = {}
    for b in bands:
        with rasterio.open(item.assets[b].href) as src:
            wb = transform_bounds("EPSG:27700", src.crs, g["left"] - 200, g["bottom"] - 200,
                                  g["right"] + 200, g["top"] + 200)
            win = src.window(*wb).round_offsets().round_lengths()
            arr = src.read(1, window=win)
            dst = np.zeros((H, W), dtype=arr.dtype)
            reproject(arr, dst, src_transform=src.window_transform(win), src_crs=src.crs,
                      dst_transform=tr, dst_crs="EPSG:27700",
                      resampling=Resampling.nearest if b == "scl" else Resampling.bilinear)
            out[b] = dst.astype(float)
    return out


def _search(since, until):
    from pystac_client import Client                          # noqa: PLC0415
    from pyproj import Transformer                            # noqa: PLC0415
    from shapely.geometry import box, shape                   # noqa: PLC0415
    g = GRID
    t = Transformer.from_crs(27700, 4326, always_xy=True)
    lon0, lat0 = t.transform(g["left"], g["bottom"])
    lon1, lat1 = t.transform(g["right"], g["top"])
    bb = box(lon0, lat0, lon1, lat1)
    cat = Client.open(STAC_URL)
    items = list(cat.search(collections=[COLLECTION], bbox=[lon0, lat0, lon1, lat1],
                            datetime=f"{since}/{until}",
                            query={"eo:cloud_cover": {"lt": TILE_CLOUD_MAX}}).items())
    items = [i for i in items if shape(i.geometry).contains(bb)]
    byd = {}
    for i in items:                       # one scene per date: the least cloudy tile
        d = i.datetime.date().isoformat()
        if d not in byd or i.properties["eo:cloud_cover"] < byd[d].properties["eo:cloud_cover"]:
            byd[d] = i
    return byd


def _wells_monthly():
    """Per month: n wells, median h, share at or above ground — the pipeline frame
    plus the calibration file (D-166) for months the frame does not hold."""
    lev = pd.read_csv(WELLS_ALL, float_precision="round_trip", index_col=0)
    lev.index = pd.to_datetime(lev.index)
    rows = [(m, int(g.notna().sum()), float(g.dropna().median()), float((g.dropna() >= 0).mean()))
            for m, g in lev.iterrows()]
    if DATA_FLOOD_CAL_LEVELS.exists():
        c = pd.read_csv(DATA_FLOOD_CAL_LEVELS, float_precision="round_trip")
        d = pd.to_datetime(c["date"])
        mo = d.where(d.dt.day > 15, d - pd.offsets.MonthBegin(1))
        c["month"] = pd.to_datetime(mo.dt.strftime("%Y-%m-01"))
        for m, g in c.groupby("month"):
            if m not in lev.index:
                rows.append((m, len(g), float(g["h_m"].median()), float((g["h_m"] >= 0).mean())))
    return pd.DataFrame(rows, columns=["month", "n_wells", "h_median", "share_at_ground"]) \
        .set_index("month").sort_index()


def _scene_month(date):
    d = pd.Timestamp(date)
    m = d if d.day > 15 else d - pd.offsets.MonthBegin(1)
    return pd.Timestamp(m.year, m.month, 1)


def read_scene(date, item, Wm):
    """Cache (bright, ndwi, clear) for one scene; return them or None if too cloudy."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{date}.npz"
    if p.exists():
        z = np.load(p)
        if z["bright"].size == 0:      # cloudy placeholder cached by an earlier pass
            return None
        return z["bright"], z["ndwi"], z["clear"]
    scl = _fetch(item, ["scl"])["scl"]
    clear = Wm & ~np.isin(scl, SCL_BAD)
    if 100 * clear.sum() / Wm.sum() < CLEAR_MIN_PCT:
        np.savez_compressed(p, bright=np.zeros(0), ndwi=np.zeros(0), clear=clear)
        return None
    b = _fetch(item, ["green", "red", "nir"])
    bright = (b["green"] + b["red"]) / 2.0
    ndwi = (b["green"] - b["nir"]) / (b["green"] + b["nir"] + 1e-9)
    np.savez_compressed(p, bright=bright, ndwi=ndwi, clear=clear)
    return bright, ndwi, clear


def calibrate(Wm):
    """Refit SENTINEL_DARK_RATIO on the vetted extent; prints, does not write."""
    from rasterio.features import rasterize                   # noqa: PLC0415
    from rasterio.transform import from_origin                # noqa: PLC0415
    from utils.kml_io import read_kml                         # noqa: PLC0415
    W, H, tr = _grid()
    g = GRID
    fine = from_origin(g["left"], g["top"], 1.0, 1.0)
    vet = read_kml(TRUTH_KML).to_crs("EPSG:27700")
    Vf = rasterize([(x, 1) for x in vet.geometry], out_shape=(H * 10, W * 10),
                   transform=fine, fill=0, dtype="uint8").astype(float)
    frac = Vf.reshape(H, 10, W, 10).mean(axis=(1, 3))
    byd = _search("2021-03-25", "2021-04-10")
    for date in CALIBRATION_SCENES:
        if date not in byd:
            warn(f"  {date}: no scene")
            continue
        r = read_scene(date, byd[date], Wm)
        if r is None:
            warn(f"  {date}: too cloudy")
            continue
        bright, _, clear = r
        med = np.median(bright[clear])
        best = None
        for ratio in np.arange(0.40, 0.98, 0.01):
            p = clear & (bright <= med * ratio)
            t = clear & (frac >= 0.5)
            i = (p & t).sum()
            iou = i / (p | t).sum()
            if best is None or iou > best[0]:
                best = (iou, ratio, i / max(1, p.sum()), i / max(1, t.sum()), p.sum() * 0.01)
        step(f"{date}: best ratio {best[1]:.2f} -> IoU {best[0]:.3f} (precision {best[2]:.2f}, "
             f"recall {best[3]:.2f}), {best[4]:.1f} ha against vetted {(clear & (frac >= 0.5)).sum() * 0.01:.1f} ha")
    info(f"SENTINEL_DARK_RATIO in this file is {SENTINEL_DARK_RATIO}; change it by hand if the refit moves it")


def validate(Wm, date):
    """Score the FIXED rule against a second vetted extent — validation, not a refit.

    Reads data/geo/flood_extent_<date>_vetted.kml and, when phase 26 wrote it,
    working/updates/W94_26_<date>_covered.geojson (the part of the warren the
    Google Earth frames show — a mosaic seam or a frame edge is outside it), and
    scores every clear scene within VALIDATE_WINDOW_DAYS on the cells that are
    clear AND covered. SENTINEL_DARK_RATIO is applied as it stands; the best
    ratio on this date is printed beside it for information only. Writes
    W94_27_validation_<date>.csv.
    """
    from rasterio.features import rasterize                   # noqa: PLC0415
    from rasterio.transform import from_origin                # noqa: PLC0415
    from utils.kml_io import read_kml                         # noqa: PLC0415
    truth = DATA_GEO_DIR / f"flood_extent_{date}_vetted.kml"
    if not truth.exists():
        warn(f"no vetted extent at {truth}")
        return 1
    W, H, tr = _grid()
    g = GRID
    fine = from_origin(g["left"], g["top"], 1.0, 1.0)
    vet = read_kml(truth).to_crs("EPSG:27700")
    Vf = rasterize([(x, 1) for x in vet.geometry], out_shape=(H * 10, W * 10),
                   transform=fine, fill=0, dtype="uint8").astype(float)
    frac = Vf.reshape(H, 10, W, 10).mean(axis=(1, 3))
    covp = OUT / f"W94_26_{date}_covered.geojson"
    if covp.exists():
        import geopandas as gpd                               # noqa: PLC0415
        cov = rasterize([(x, 1) for x in gpd.read_file(covp).geometry], out_shape=(H, W),
                        transform=tr, fill=0, dtype="uint8").astype(bool) & Wm
        info(f"scoring on the {100 * cov.sum() / Wm.sum():.1f} % of the warren the frames cover")
    else:
        cov = Wm
        warn(f"no {covp.name}: scoring on the whole warren (run phase 26 for {date})")
    shade = _shade_mask()
    if shade is None:
        warn(f"no {FLOOR_MASK.name}: scoring without the floor mask (phase 29 builds it)")
    t = pd.Timestamp(date)
    byd = _search((t - pd.Timedelta(days=VALIDATE_WINDOW_DAYS)).date().isoformat(),
                  (t + pd.Timedelta(days=VALIDATE_WINDOW_DAYS)).date().isoformat())
    truth_ha = (cov & (frac >= 0.5)).sum() * 0.01
    step(f"vetted {date}: {len(vet)} bodies, {vet.area.sum() / 1e4:.2f} ha; "
         f"{truth_ha:.2f} ha of 10 m cells at least half wet inside the covered warren")
    rows = []
    for sd in sorted(byd):
        r = read_scene(sd, byd[sd], Wm)
        if r is None:
            info(f"  {sd}: too cloudy")
            continue
        bright, ndwi, clear = r
        med = float(np.median(bright[clear]))            # the SERIES' median: whole warren
        for masked in ([False, True] if shade is not None else [False]):
            ok = clear & cov & (~shade if masked else True)
            tcell = ok & (frac >= 0.5)
            p = ok & (bright <= med * SENTINEL_DARK_RATIO)
            i = (p & tcell).sum()
            iou = i / max(1, (p | tcell).sum())
            best = None
            for ratio in np.arange(0.40, 0.98, 0.01):
                q = ok & (bright <= med * ratio)
                j = (q & tcell).sum()
                v = j / max(1, (q | tcell).sum())
                if best is None or v > best[0]:
                    best = (v, ratio)
            rows.append({"vetted_date": date, "scene_date": sd, "days_off": (pd.Timestamp(sd) - t).days,
                         "floor_only": masked,
                         "clear_pct_of_covered": round(100 * ok.sum() / cov.sum(), 1),
                         "ratio": SENTINEL_DARK_RATIO, "iou": round(iou, 3),
                         "precision": round(i / max(1, p.sum()), 3), "recall": round(i / max(1, tcell.sum()), 3),
                         "wet_floor_ha": round(p.sum() * 0.01, 2), "vetted_ha": round(tcell.sum() * 0.01, 2),
                         "ndwi_open_water_ha": round((ok & (ndwi > 0)).sum() * 0.01, 2),
                         "best_ratio_here": round(best[1], 2), "best_iou_here": round(best[0], 3)})
            step(f"  {sd} ({rows[-1]['days_off']:+d} d){' floor-only' if masked else ''}: "
                 f"IoU {iou:.3f} at ratio {SENTINEL_DARK_RATIO} "
                 f"(precision {rows[-1]['precision']:.2f}, recall {rows[-1]['recall']:.2f}); "
                 f"{rows[-1]['wet_floor_ha']:.1f} ha read vs {rows[-1]['vetted_ha']:.1f} ha vetted; "
                 f"best ratio on this date {best[1]:.2f} -> IoU {best[0]:.3f}")
    if not rows:
        warn("no clear scene in the window")
        return 1
    pd.DataFrame(rows).to_csv(OUT / f"W94_27_validation_{date}.csv", index=False)
    saved(f"W94_27_validation_{date}.csv")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--since", default="2016-01-01")
    ap.add_argument("--until", default=pd.Timestamp.today().date().isoformat())
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--validate", metavar="DATE",
                    help="score the fixed rule on data/geo/flood_extent_DATE_vetted.kml")
    args = ap.parse_args()
    warnings.filterwarnings("ignore", category=UserWarning, module="rasterio")
    banner("Sentinel-2 wet slack floor series", __version__)
    Wm = _warren_mask()
    if args.calibrate:
        phase(1, "Calibrating the darkness ratio on the vetted extent")
        calibrate(Wm)
        return 0
    if args.validate:
        phase(1, f"Validating the fixed rule on the vetted {args.validate} extent")
        return validate(Wm, args.validate)
    phase(1, f"Searching {args.since} to {args.until}")
    byd = _search(args.since, args.until)
    info(f"{len(byd)} candidate date(s) at tile cloud < {TILE_CLOUD_MAX:.0f} %")
    phase(2, "Reading scenes (cached; safe to interrupt and resume)")
    shade = _shade_mask()
    if shade is None:
        warn(f"no {FLOOR_MASK.name}: wet_floor_pct_masked will be blank (phase 29 builds it)")
    rows = []
    import time                                               # noqa: PLC0415
    t0 = time.time()
    total = len(byd)
    for n, (date, item) in enumerate(sorted(byd.items()), 1):
        progress(n, total, date, started=t0)
        try:
            r = read_scene(date, item, Wm)
        except Exception as ex:                               # noqa: BLE001
            warn(f"  {date}: {type(ex).__name__}: {str(ex)[:80]}")
            continue
        if r is None:
            continue
        bright, ndwi, clear = r
        med = float(np.median(bright[clear]))
        dark = clear & (bright <= med * SENTINEL_DARK_RATIO)
        scale = Wm.sum() / clear.sum()                        # to the whole warren
        rows.append({"date": date, "scene": item.id,
                     "tile_cloud_pct": round(item.properties["eo:cloud_cover"], 1),
                     "clear_pct": round(100 * clear.sum() / Wm.sum(), 1),
                     "bright_median": round(med, 1),
                     "wet_floor_ha": round(dark.sum() * 0.01 * scale, 2),
                     "wet_floor_pct": round(100 * dark.sum() / clear.sum(), 2),
                     "ndwi_open_water_ha": round((clear & (ndwi > 0)).sum() * 0.01 * scale, 2),
                     "wet_floor_pct_masked": (round(100 * (dark & ~shade).sum() / (clear & ~shade).sum(), 2)
                                              if shade is not None else None),
                     "month": _scene_month(date)})
    print(flush=True)
    S = pd.DataFrame(rows)
    if not len(S):
        warn("no usable scene")
        return 1
    S["winter"] = S["month"].dt.month.isin(WINTER_MONTHS)
    S = S.join(_wells_monthly(), on="month")
    S["month"] = S["month"].dt.strftime("%Y-%m")
    S.to_csv(OUT / "W94_27_sentinel_wet_floor.csv", index=False)
    saved("W94_27_sentinel_wet_floor.csv")
    phase(3, "Against the wells")
    from scipy.stats import spearmanr                         # noqa: PLC0415
    ok = S.dropna(subset=["h_median"])
    w = ok[ok["winter"]]
    if len(w) >= 5:
        r, p = spearmanr(w["wet_floor_pct"], w["h_median"])
        step(f"winter scenes with a well month: {len(w)}; wet floor vs median well level "
             f"rho {r:+.3f} (p {p:.1e})")
        M = w.groupby("month").agg(wet_floor_ha=("wet_floor_ha", "median"),
                                   n_scenes=("date", "size"),
                                   h_median=("h_median", "first"),
                                   share_at_ground=("share_at_ground", "first")).reset_index()
        r2, p2 = spearmanr(M["wet_floor_ha"], M["h_median"])
        step(f"by winter month (n={len(M)}): rho {r2:+.3f} (p {p2:.1e})")
        M.to_csv(OUT / "W94_27_sentinel_winter_monthly.csv", index=False)
        saved("W94_27_sentinel_winter_monthly.csv")
    s = ok[~ok["winter"]]
    if len(s) >= 5:
        r, _ = spearmanr(s["wet_floor_pct"], s["h_median"])
        info(f"outside winter (n={len(s)}): rho {r:+.3f} — the summer sward is dark; "
             f"the read is not a flood signal there")
    return 0


if __name__ == "__main__":
    sys.exit(main())
