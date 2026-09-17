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
  python3 tools/sentinel_wet_floor.py --two-class [--animate]  # the wet-area model (D-178)
  python3 tools/sentinel_wet_floor.py --emit-feed      # living/wet_area_model.json from
                                                       # the committed CSV + npz alone

  Needs `pystac-client` (pip install pystac-client) and network. Per-scene
  rasters are cached under working/updates/sentinel_cache/ (gitignored size).
"""
from __future__ import annotations

__version__ = "1.9.0"  # Hollingham (2026) - 2026-09-17. The history block
#   carries each mode's fit against the wells - RMSE and Spearman rho, COMPUTED from
#   W94_27_well_fit.csv rather than scraped out of the summary CSV's prose value
#   cells. The forecaster quotes them where it explains Mode R and Mode C, so they
#   have to move with a refit instead of being typed into a page.
# v1.8.0  # Hollingham (2026) - 2026-09-17. The feed carries
#   a `history` block: the SSM's monthly median level 2005-10 to 2026-03, both modes,
#   with the observed level beside it, read from W94_27_ssm_through_nir_curves.csv.
#   It is what lets the forecaster's cell layer show a PAST month - the layer was
#   forward-only, so the 2021-02 film still could not be checked against the page by
#   eye (Martin, 2026-09-17). Optional: no CSV, no history, and the page hides the
#   history control rather than failing.
# v1.7.0  # Hollingham (2026) - 2026-09-16. T-36 item 1:
#   write_wet_area_feed() emits living/wet_area_model.json - the two curves, the
#   fitted range and the per-cell switching levels (int16 centimetres, base64) as
#   the PUBLIC feed the forecaster reads. Route (a) of the 2026-09-16 spec: this
#   tool computes the model, so this tool publishes it (D-096). --two-class writes
#   it at the end of the run; --emit-feed regenerates it from the committed CSV and
#   npz alone, with no scene read, no network and no rasterio. Hash-gated: a run
#   that moves nothing but `generated` rewrites nothing. The never/not-floor
#   sentinel is 32767, not the spec's -1, which collides with -0.01 m.
# v1.6.1  # Hollingham (2026) - 2026-09-16. --animate falls back to a GIF
#   when imageio-ffmpeg is absent (the L14: imageio routed the MP4 to tifffile
#   and rejected fps). The model, the thresholds and the drive were unaffected.
# v1.6.0  # Hollingham (2026) - 2026-09-16. --two-class: THE WET-AREA
#   MODEL (D-178) — open water (B8 <= 0.5 x median) and wet floor (0.5-0.8)
#   on the floor, each fitted a*exp(b*h) against the well level at the scene
#   date, no vet in the fit; per-cell switching levels from the scene stack;
#   phase 27's SSM level through the curves; --animate the monthly MP4.
#   Consolidates the 2026-09-16 sandbox runs into the tool.
# v1.5.0  # Hollingham (2026) - 2026-09-16. --cells: a supervised
#   per-cell classifier (all five bands relative to the scene median + NDWI,
#   NDMI, MNDWI; logistic, Newton) trained on the vetted 2021 extent and
#   applied unchanged to 2020 — Martin: the single ratio under-rates Sentinel.
#   Writes vettable cell KMLs and true-colour GroundOverlays per scene.
# v1.4.0  # Hollingham (2026) - 2026-09-16. T-32: _scene_month and
#   _wells_monthly both bucketed with `d - pd.offsets.MonthBegin(1)`, a no-op for
#   days 2-15, so 49 of the 110 scenes carried the wrong month and were joined to
#   the wrong dipwell reading. Both now call the single
#   utils.model_utils.month_bucket. Measured effect on the headline: the
#   floor-only rank correlation with the median well level moves +0.711 -> +0.707
#   with n 36 -> 44, so D-170's finding stands (dated Note appended there).
#   REGENERATE the series after this change; the 215 MB scene cache makes it a
#   re-read, not a re-download.
# v1.3.0  # Hollingham (2026) - 2026-09-15. --swir-test: MNDWI, NDMI
#   and the SWIR ratio (B11) against the vetted extents, first date's threshold
#   carried to the second — does SWIR split flooded from damp floor? A test;
#   the series is unchanged.
# v1.2.1  # Hollingham (2026) - 2026-09-15. The phase 29 mask is
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
import time
import os
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.console_utils import banner, info, phase, progress, saved, step, warn  # noqa: E402
from utils.buckets import month_bucket                      # noqa: E402
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
        c["month"] = month_bucket(d)          # T-32: was a MonthBegin no-op
        for m, g in c.groupby("month"):
            if m not in lev.index:
                rows.append((m, len(g), float(g["h_m"].median()), float((g["h_m"] >= 0).mean())))
    return pd.DataFrame(rows, columns=["month", "n_wells", "h_median", "share_at_ground"]) \
        .set_index("month").sort_index()


def _scene_month(date):
    """The dipwell month a scene belongs to, by Script 01's rule.

    T-32: this read `d - pd.offsets.MonthBegin(1)`, which is a no-op for days
    2-15, so 49 of the 110 scenes carried the wrong month and were joined to the
    wrong well reading. The rule now has one implementation.
    """
    return month_bucket(date)


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


SWIR_TEST_INDICES = ("mndwi", "ndmi", "swir_ratio", "bright_ratio")


def _truth_cells(date):
    """(frac wet per 10 m cell, covered mask) for a vetted date."""
    from rasterio.features import rasterize                   # noqa: PLC0415
    from rasterio.transform import from_origin                # noqa: PLC0415
    from utils.kml_io import read_kml                         # noqa: PLC0415
    W, H, tr = _grid()
    g = GRID
    fine = from_origin(g["left"], g["top"], 1.0, 1.0)
    vet = read_kml(DATA_GEO_DIR / f"flood_extent_{date}_vetted.kml").to_crs("EPSG:27700")
    Vf = rasterize([(x, 1) for x in vet.geometry], out_shape=(H * 10, W * 10),
                   transform=fine, fill=0, dtype="uint8").astype(float)
    frac = Vf.reshape(H, 10, W, 10).mean(axis=(1, 3))
    covp = OUT / f"W94_26_{date}_covered.geojson"
    cov = None
    if covp.exists():
        import geopandas as gpd                               # noqa: PLC0415
        cov = rasterize([(x, 1) for x in gpd.read_file(covp).geometry], out_shape=(H, W),
                        transform=tr, fill=0, dtype="uint8").astype(bool)
    return frac, cov


def swir_test(Wm, dates):
    """Does SWIR split flooded floor from damp floor where the visible bands cannot?

    For every clear scene within VALIDATE_WINDOW_DAYS of each vetted date,
    fetches green, NIR, SWIR (B11, 20 m native, resampled to the 10 m grid) and
    scores four indices on the floor: MNDWI (green-SWIR), NDMI (NIR-SWIR), the
    SWIR ratio to the scene median, and the visible brightness ratio as the
    control. Each index is swept for its best threshold ON EACH SCENE (a fit),
    and the threshold best on the FIRST date is then applied to the others
    (the transfer — the number that matters). Writes W94_27_swir_test.csv.
    Nothing here changes the series.
    """
    shade = _shade_mask()
    scenes = []
    for date in dates:
        frac, cov = _truth_cells(date)
        ok0 = Wm & (cov if cov is not None else True) & (~shade if shade is not None else True)
        t = pd.Timestamp(date)
        byd = _search((t - pd.Timedelta(days=VALIDATE_WINDOW_DAYS)).date().isoformat(),
                      (t + pd.Timedelta(days=VALIDATE_WINDOW_DAYS)).date().isoformat())
        for sd in sorted(byd):
            r = read_scene(sd, byd[sd], Wm)
            if r is None:
                continue
            _, _, clear = r
            b = _fetch(byd[sd], ["green", "nir", "swir16"])
            ok = ok0 & clear
            med = lambda a: float(np.median(a[clear]))    # noqa: E731
            idx = {"mndwi": (b["green"] - b["swir16"]) / (b["green"] + b["swir16"] + 1e-9),
                   "ndmi": (b["nir"] - b["swir16"]) / (b["nir"] + b["swir16"] + 1e-9),
                   "swir_ratio": -b["swir16"] / med(b["swir16"]),        # negated: wet = high
                   "bright_ratio": -b["green"] / med(b["green"])}      # the visible control
            scenes.append(dict(vet=date, scene=sd, ok=ok, truth=ok & (frac >= 0.5), idx=idx))
            info(f"  {sd} for {date}: fetched")

    def score(mask_pred, truth):
        i = (mask_pred & truth).sum()
        return i / max(1, (mask_pred | truth).sum()), i / max(1, mask_pred.sum()), i / max(1, truth.sum())

    rows = []
    first = dates[0]
    for name in SWIR_TEST_INDICES:
        # best threshold per scene, and the first date's threshold carried to the rest
        fit = {}
        for sc in scenes:
            v = sc["idx"][name]
            qs = np.quantile(v[sc["ok"]], np.linspace(0.02, 0.98, 97))
            best = max(((score(sc["ok"] & (v >= q), sc["truth"])[0], q) for q in qs))
            fit[sc["scene"]] = best
        ref = np.median([fit[sc["scene"]][1] for sc in scenes if sc["vet"] == first])
        for sc in scenes:
            v = sc["idx"][name]
            iou_t, prec, rec = score(sc["ok"] & (v >= ref), sc["truth"])
            rows.append({"index": name, "vetted_date": sc["vet"], "scene_date": sc["scene"],
                         "best_iou_here": round(fit[sc["scene"]][0], 3),
                         "best_thr_here": round(float(fit[sc["scene"]][1]), 4),
                         f"thr_from_{first}": round(float(ref), 4),
                         "iou_transfer": round(iou_t, 3), "precision": round(prec, 3),
                         "recall": round(rec, 3),
                         "read_ha": round((sc["ok"] & (v >= ref)).sum() * 0.01, 1),
                         "vetted_ha": round(sc["truth"].sum() * 0.01, 1)})
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "W94_27_swir_test.csv", index=False)
    saved("W94_27_swir_test.csv")
    for name in SWIR_TEST_INDICES:
        sub = R[R["index"] == name]
        step(name)
        for _, r in sub.iterrows():
            info(f"    {r['vetted_date']} <- {r['scene_date']}: fit IoU {r['best_iou_here']:.3f}; "
                 f"with the {first} threshold IoU {r['iou_transfer']:.3f} "
                 f"(P {r['precision']:.2f} R {r['recall']:.2f}) {r['read_ha']:.1f} vs {r['vetted_ha']:.1f} ha")
    return 0


CELL_BANDS = ("blue", "green", "red", "nir", "swir16")
CELL_TRAIN_DAYS = 14          # scenes this close to a vetted date train or test on it


def _cell_features(item, clear):
    """Per-cell feature matrix from one scene: each band relative to its own
    clear-warren median (so illumination and haze divide out), plus NDWI, NDMI
    and MNDWI. Returns (X, bands dict) with X shaped (H*W, n_features)."""
    b = _fetch(item, list(CELL_BANDS))
    feats = []
    for k in CELL_BANDS:
        med = float(np.median(b[k][clear]))
        feats.append(np.log(np.clip(b[k], 1, None) / max(med, 1.0)))
    g, n, sw = b["green"], b["nir"], b["swir16"]
    feats.append((g - n) / (g + n + 1e-9))
    feats.append((n - sw) / (n + sw + 1e-9))
    feats.append((g - sw) / (g + sw + 1e-9))
    X = np.stack([f.ravel() for f in feats], axis=1)
    return X, b


def _logit_fit(X, y, l2=1e-2, iters=60):
    """Logistic regression by Newton's method (no sklearn on the L14). Returns
    (w, b) on standardised features; the standardisation is returned too."""
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = np.column_stack([np.ones(len(X)), (X - mu) / sd])
    w = np.zeros(Z.shape[1])
    # balance the classes: wet cells are the minority
    pw = 0.5 / max(1, y.sum()) * len(y)
    wt = np.where(y, pw, 1.0)
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Z @ w))
        grad = Z.T @ (wt * (p - y)) + l2 * np.r_[0, w[1:]]
        Hm = (Z * (wt * p * (1 - p))[:, None]).T @ Z + l2 * np.diag(np.r_[0, np.ones(len(w) - 1)])
        step = np.linalg.solve(Hm, grad)
        w -= step
        if np.abs(step).max() < 1e-6:
            break
    return w, mu, sd


def _logit_predict(w, mu, sd, X):
    Z = np.column_stack([np.ones(len(X)), (X - mu) / sd])
    return 1 / (1 + np.exp(-Z @ w))


def _cells_to_kml(mask, prob, path, name):
    """One placemark per 10 m cell, NO FILL, in folders by probability, so the
    classification can be vetted in Google Earth over the imagery."""
    from pyproj import Transformer                            # noqa: PLC0415
    W, H, tr = _grid()
    t = Transformer.from_crs(27700, 4326, always_xy=True)
    g = GRID
    k = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>', f"<name>{name}</name>",
         '<Style id="c"><LineStyle><color>ff00ffff</color><width>1.5</width></LineStyle>'
         '<PolyStyle><fill>0</fill><outline>1</outline></PolyStyle></Style>']
    edges = (0.9, 0.7, 0.5)
    rows, cols = np.where(mask)
    for i, lo in enumerate(edges):
        hi = 1.01 if i == 0 else edges[i - 1]
        sel = (prob[rows, cols] >= lo) & (prob[rows, cols] < hi)
        if not sel.any():
            continue
        k.append(f"<Folder><name>p {lo:.1f}-{min(hi, 1):.1f} ({int(sel.sum())})</name><open>0</open>")
        for rr, cc in zip(rows[sel], cols[sel]):
            x0 = g["left"] + cc * g["res"]; y1 = g["top"] - rr * g["res"]
            pts = [(x0, y1), (x0 + g["res"], y1), (x0 + g["res"], y1 - g["res"]), (x0, y1 - g["res"]), (x0, y1)]
            ll = " ".join("%.7f,%.7f,0" % t.transform(x, y) for x, y in pts)
            k.append(f"<Placemark><name>c{rr}_{cc}</name><description>p {prob[rr, cc]:.2f}</description>"
                     f"<styleUrl>#c</styleUrl><Polygon><outerBoundaryIs><LinearRing><coordinates>{ll}"
                     "</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>")
        k.append("</Folder>")
    k.append("</Document></kml>")
    path.write_text("\n".join(k), encoding="utf-8")


def _overlay_png(b, clear, path, kml_path, name):
    """True-colour PNG of the scene with a KML GroundOverlay so it can be viewed
    in Google Earth, image-only (no numbers) — for Martin to look at."""
    from PIL import Image                                     # noqa: PLC0415
    from pyproj import Transformer                            # noqa: PLC0415
    rgb = np.stack([b["red"], b["green"], b["blue"]], axis=-1)
    lo, hi = np.percentile(rgb[clear], [1, 99])
    img = np.clip((rgb - lo) / (hi - lo), 0, 1)
    Image.fromarray((img * 255).astype("uint8")).save(path)
    g = GRID
    t = Transformer.from_crs(27700, 4326, always_xy=True)
    w_, s_ = t.transform(g["left"], g["bottom"]); e_, n_ = t.transform(g["right"], g["top"])
    kml_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2">'
        f"<GroundOverlay><name>{name}</name><Icon><href>{path.name}</href></Icon>"
        f"<LatLonBox><north>{n_:.6f}</north><south>{s_:.6f}</south><east>{e_:.6f}</east>"
        f"<west>{w_:.6f}</west></LatLonBox></GroundOverlay></kml>", encoding="utf-8")


def cells(Wm, dates):
    """A SUPERVISED per-cell classifier trained on the first vetted date.

    Martin (2026-09-16): the single darkness ratio under-rates Sentinel; train
    on the vetted extent instead. Features are every band Sentinel has, each
    relative to the scene's own median, plus three water indices; a logistic
    model is fitted on the floor cells of the scenes within CELL_TRAIN_DAYS of
    dates[0] (cell wet = at least half inside the vetted extent) and applied
    UNCHANGED to the scenes around every later date — the transfer score is
    the one that matters. Writes W94_27_cells_scores.csv; per scene, the
    classified cells as a vettable KML (folders by probability), the true-colour
    scene as a Google Earth ground overlay, and the probability raster.
    """
    shade = _shade_mask()
    scenes = []
    for date in dates:
        frac, cov = _truth_cells(date)
        ok0 = Wm & (cov if cov is not None else True) & (~shade if shade is not None else True)
        t = pd.Timestamp(date)
        byd = _search((t - pd.Timedelta(days=CELL_TRAIN_DAYS)).date().isoformat(),
                      (t + pd.Timedelta(days=CELL_TRAIN_DAYS)).date().isoformat())
        for sd in sorted(byd):
            r = read_scene(sd, byd[sd], Wm)
            if r is None:
                continue
            clear = r[2]
            X, b = _cell_features(byd[sd], clear)
            ok = ok0 & clear
            scenes.append(dict(vet=date, scene=sd, X=X, ok=ok, truth=ok & (frac >= 0.5), bands=b, clear=clear))
            info(f"  {sd} for {date}: {int(ok.sum())} floor cells, {int((ok & (frac >= 0.5)).sum())} vetted wet")
    train = [sc for sc in scenes if sc["vet"] == dates[0]]
    if not train:
        warn("no training scene")
        return 1
    Xt = np.concatenate([sc["X"][sc["ok"].ravel()] for sc in train])
    yt = np.concatenate([sc["truth"].ravel()[sc["ok"].ravel()] for sc in train]).astype(float)
    w, mu, sd = _logit_fit(Xt, yt)
    names = [f"log_{k}" for k in CELL_BANDS] + ["ndwi", "ndmi", "mndwi"]
    step("fitted on " + ", ".join(sc["scene"] for sc in train) +
         f": {len(yt)} cells, {int(yt.sum())} wet; standardised weights " +
         ", ".join(f"{n} {v:+.2f}" for n, v in zip(names, w[1:])))
    W_, H_, _ = _grid()
    rows = []
    for sc in scenes:
        p = _logit_predict(w, mu, sd, sc["X"]).reshape(H_, W_)
        p[~sc["ok"]] = 0
        pred = sc["ok"] & (p >= 0.5)
        tr = sc["truth"]
        i = (pred & tr).sum()
        best = max(((((sc["ok"] & (p >= q)) & tr).sum() / max(1, ((sc["ok"] & (p >= q)) | tr).sum()), q)
                    for q in np.arange(0.1, 0.95, 0.05)))
        rows.append({"vetted_date": sc["vet"], "scene_date": sc["scene"],
                     "role": "train" if sc["vet"] == dates[0] else "TEST",
                     "iou": round(i / max(1, (pred | tr).sum()), 3),
                     "precision": round(i / max(1, pred.sum()), 3), "recall": round(i / max(1, tr.sum()), 3),
                     "pred_ha": round(pred.sum() * 0.01, 2), "vetted_ha": round(tr.sum() * 0.01, 2),
                     "best_iou_here": round(best[0], 3), "best_p_here": round(float(best[1]), 2)})
        step(f"  {sc['scene']} [{rows[-1]['role']}] IoU {rows[-1]['iou']:.3f} (P {rows[-1]['precision']:.2f} "
             f"R {rows[-1]['recall']:.2f}) {rows[-1]['pred_ha']:.1f} vs {rows[-1]['vetted_ha']:.1f} ha; "
             f"best p {best[1]:.2f} -> {best[0]:.3f}")
        _cells_to_kml(sc["ok"] & (p >= 0.5), p, OUT / f"W94_27_cells_{sc['scene']}.kml",
                      f"Sentinel wet cells {sc['scene']} — trained on {dates[0]}")
        _overlay_png(sc["bands"], sc["clear"], OUT / f"W94_27_scene_{sc['scene']}.png",
                     OUT / f"W94_27_scene_{sc['scene']}.kml", f"Sentinel-2 true colour {sc['scene']}")
        np.save(OUT / f"W94_27_cells_{sc['scene']}_p.npy", p)
    pd.DataFrame(rows).to_csv(OUT / "W94_27_cells_scores.csv", index=False)
    saved("W94_27_cells_scores.csv; W94_27_cells_<scene>.kml, W94_27_scene_<scene>.kml/.png")
    return 0


# ── the two-class wet-area model (D-178) ──────────────────────────────────────
NIR_BLACK_RATIO = 0.50        # B8 <= this x the scene's clear-floor median = open water
NIR_DARK_RATIO = 0.80         # B8 <= this (and above BLACK) = wet floor
TWO_CLASS_EXCLUDE = ("2016-12-26",)   # a 12-degree-sun December scene, 3.5x off the curve
CELL_MIN_SCENES = 10          # a cell seen in fewer scenes gets no switching level
HINDCAST_MONTHLY = OUT / "W94_27_hindcast_monthly.csv"   # phase 27's levels (warren_flood_prep)


def _b8_scene(date, item, Wm):
    """B8 for one usable scene, cached beside the visible read."""
    p = CACHE / f"b8_{date}.npz"
    if p.exists():
        z = np.load(p)
        return z["nir"], z["clear"]
    r = read_scene(date, item, Wm)
    if r is None:
        return None
    nir = _fetch(item, ["nir"])["nir"].astype("float32")
    np.savez_compressed(p, nir=nir, clear=r[2])
    return nir, r[2]


def _level_at(date, end):
    """Median well level interpolated to a date from the bracketing month-end
    readings, and the rate of change (m/month); NaN when the gap exceeds 45 d."""
    d = pd.Timestamp(date)
    after, before = end[end.index >= d], end[end.index < d]
    if not len(after) or not len(before):
        return np.nan, np.nan
    t1, h1, t0, h0 = after.index[0], after.iloc[0], before.index[-1], before.iloc[-1]
    if (t1 - t0).days > 45:
        return np.nan, np.nan
    f = (d - t0).days / (t1 - t0).days
    return h0 + f * (h1 - h0), (h1 - h0) / ((t1 - t0).days / 30.4)


def _fit_exp(y, h):
    """log-linear fit y = a·exp(b·h); returns a, b, sigma (log), Spearman rho."""
    ly = np.log(np.clip(y, 0.3, None))
    b, la = np.polyfit(h, ly, 1)
    sd = float((ly - (la + b * h)).std())
    rho = float(pd.Series(y).rank().corr(pd.Series(h).rank()))
    return float(np.exp(la)), float(b), sd, rho


def _cell_switch_levels(cls, seen, h):
    """Per cell, the lowest level at which the cell is in the class — the step on
    the scene-date level that best explains the cell's own history (scenes sorted
    by h). inf = never in the class, or seen in fewer than CELL_MIN_SCENES."""
    n, H, W = cls.shape
    inc = (cls & seen).astype(np.int16)
    notc = (~cls & seen).astype(np.int16)
    cum_in, cum_not, tot_not = np.cumsum(inc, 0), np.cumsum(notc, 0), notc.sum(0)
    best_err = np.full((H, W), 10 ** 6, np.int32)
    best_k = np.full((H, W), n, np.int16)
    for k in range(n + 1):
        err = (cum_in[k - 1] if k else 0) + tot_not - (cum_not[k - 1] if k else 0)
        better = err < best_err
        best_err[better], best_k[better] = err[better], k
    lvl = np.where(best_k >= n, np.inf, h[np.minimum(best_k, n - 1)])
    lvl[seen.sum(0) < CELL_MIN_SCENES] = np.inf
    return lvl, best_err


def two_class(Wm, animate=False):
    """The hands-free wet-area model: open water and wet floor from B8 alone,
    each a function of the median well level; the per-cell switching levels;
    the SSM drive; the figures. D-178. Reads the series CSV (run the series
    first). Writes W94_27_two_class_series.csv, W94_27_wet_area_model.csv (the
    four parameters and their sigmas — the model), W94_27_cell_thresholds.npz,
    W94_27_ssm_through_nir_curves.csv/.png when phase 27's levels exist, and
    the fit figure; --animate adds the month-by-month MP4 (Mode R).
    """
    import matplotlib                                         # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                           # noqa: PLC0415
    shade = _shade_mask()
    floor = Wm & (~shade if shade is not None else True)
    S = pd.read_csv(OUT / "W94_27_sentinel_wet_floor.csv")
    S = S[S["winter"] & S["h_median"].notna() & ~S["date"].isin(TWO_CLASS_EXCLUDE)]
    M = _wells_monthly()["h_median"].dropna()
    end = pd.Series(M.values, index=M.index + pd.offsets.MonthEnd(0))
    byd = {}
    for y in sorted({d[:4] for d in S["date"]}):
        byd.update(_search(f"{y}-01-01", f"{y}-12-31"))
    phase(1, f"Reading B8 for {len(S)} winter scenes (cached)")
    rows, stack = [], []
    t0 = time.time()
    for n, (_, r) in enumerate(S.iterrows(), 1):
        progress(n, len(S), r["date"], started=t0)
        h, dh = _level_at(r["date"], end)
        if np.isnan(h) or r["date"] not in byd:
            continue
        b = _b8_scene(r["date"], byd[r["date"]], Wm)
        if b is None:
            continue
        nir, clear = b
        ok = floor & clear
        med = float(np.median(nir[ok]))
        black, dark = ok & (nir <= NIR_BLACK_RATIO * med), ok & (nir <= NIR_DARK_RATIO * med)
        sc = floor.sum() / ok.sum() * 0.01
        rows.append({"date": r["date"], "h_scene": round(h, 3), "dh_month": round(dh, 3),
                     "phase": "wetting" if dh > 0.02 else ("drying" if dh < -0.02 else "flat"),
                     "open_water_ha": round(black.sum() * sc, 2),
                     "wet_floor_ha": round((dark.sum() - black.sum()) * sc, 2),
                     "dark_total_ha": round(dark.sum() * sc, 2)})
        stack.append((h, ok, black, dark))
    print(flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "W94_27_two_class_series.csv", index=False)
    saved("W94_27_two_class_series.csv")
    phase(2, "Fitting the two curves on the scenes alone")
    fits = {}
    for cls in ("open_water", "wet_floor", "dark_total"):
        a, b, sd, rho = _fit_exp(R[f"{cls}_ha"].values, R["h_scene"].values)
        fits[cls] = dict(cls=cls, a=a, b=b, sigma_log=sd, sigma_factor=float(np.exp(sd)), rho=rho,
                         n=len(R), h_min=float(R["h_scene"].min()), h_max=float(R["h_scene"].max()))
        step(f"{cls}: {a:.1f} * exp({b:.2f} h) ha; sigma x/÷ {np.exp(sd):.2f}; rho {rho:+.2f}; n {len(R)}")
    pd.DataFrame(fits.values()).to_csv(OUT / "W94_27_wet_area_model.csv", index=False)
    saved("W94_27_wet_area_model.csv  (the model)")
    hh = np.linspace(R["h_scene"].min() - 0.05, R["h_scene"].max() + 0.1, 60)
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for cls, c, lab in (("open_water", "#0b6e8f", "open water (B8 <= 0.5 x median)"),
                        ("wet_floor", "#d4a017", "wet floor (0.5-0.8)")):
        f = fits[cls]
        ax.scatter(R["h_scene"], R[f"{cls}_ha"], s=24, color=c, alpha=0.85)
        ax.fill_between(hh, f["a"] * np.exp(f["b"] * hh - f["sigma_log"]),
                        f["a"] * np.exp(f["b"] * hh + f["sigma_log"]), color=c, alpha=0.12)
        ax.plot(hh, f["a"] * np.exp(f["b"] * hh), color=c, lw=2,
                label=f"{lab}: {f['a']:.0f}·exp({f['b']:.2f}·h) ha, rho {f['rho']:+.2f}")
    ax.set_xlabel("median well level at the scene date, m (0 = ground)")
    ax.set_ylabel("area, ha (whole warren)")
    ax.set_title(f"The wet-area model — {len(R)} winter Sentinel-2 scenes, B8 alone, no vet (D-178)", fontsize=9.5)
    ax.grid(alpha=0.3); ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(OUT / "W94_27_wet_area_model.png", dpi=160); plt.close(fig)
    saved("W94_27_wet_area_model.png")
    phase(3, "Per-cell switching levels")
    order = np.argsort([s_[0] for s_ in stack])
    h = np.array([stack[i][0] for i in order])
    seen = np.stack([stack[i][1] for i in order]); black = np.stack([stack[i][2] for i in order])
    dark = np.stack([stack[i][3] for i in order])
    hb, eb = _cell_switch_levels(black, seen, h)
    hd, ed = _cell_switch_levels(dark, seen, h)
    hd = np.minimum(hd, hb)
    np.savez_compressed(OUT / "W94_27_cell_thresholds.npz", h_open_water=hb, h_wet_floor=hd,
                        err_open_water=eb, err_wet_floor=ed, n_seen=seen.sum(0), floor=floor,
                        grid=np.array([GRID["left"], GRID["bottom"], GRID["right"], GRID["top"], GRID["res"]]))
    step(f"{int((np.isfinite(hb) & floor).sum())} cells ever open water, "
         f"{int((np.isfinite(hd) & floor).sum())} ever wet floor, of {int(floor.sum())} on the floor")
    saved("W94_27_cell_thresholds.npz")
    if not HINDCAST_MONTHLY.exists():
        warn(f"no {HINDCAST_MONTHLY.name}: the SSM drive needs phase 27's levels")
        phase(4, "The public feed the forecaster reads")
        return write_wet_area_feed()
    phase(4, "The SSM's monthly level through the two curves")
    Hc = pd.read_csv(HINDCAST_MONTHLY)
    for cls in ("open_water", "wet_floor"):
        f = fits[cls]
        Hc[f"{cls}_ha_modelled"] = f["a"] * np.exp(f["b"] * Hc["median_level_modelled_m"])
        Hc[f"{cls}_ha_observed"] = np.where(Hc["median_level_observed_m"].notna(),
                                            f["a"] * np.exp(f["b"] * Hc["median_level_observed_m"]), np.nan)
    keep = ["month", "mode", "median_level_modelled_m", "median_level_observed_m", "n_wells_observed",
            "open_water_ha_modelled", "wet_floor_ha_modelled", "open_water_ha_observed",
            "wet_floor_ha_observed", "sentinel_index"]
    Hc[keep].round(3).to_csv(OUT / "W94_27_ssm_through_nir_curves.csv", index=False)
    saved("W94_27_ssm_through_nir_curves.csv")
    for m, g in Hc.groupby("mode"):
        ok = g["median_level_observed_m"].notna() & (g["n_wells_observed"] >= 20)
        for cls in ("open_water", "wet_floor"):
            e = np.log(g.loc[ok, f"{cls}_ha_modelled"]) - np.log(g.loc[ok, f"{cls}_ha_observed"])
            step(f"Mode {m} {cls}: median x{np.exp(np.median(e)):.2f}, 68 % range "
                 f"x{np.exp(np.percentile(e, 16)):.2f}-{np.exp(np.percentile(e, 84)):.2f} over {int(ok.sum())} months")
    t = pd.to_datetime(Hc["month"])
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for ax, m in zip(axes, ("R", "C")):
        g = Hc[Hc["mode"] == m]; tt = t[g.index]
        ax.fill_between(tt, 0, g["open_water_ha_modelled"], color="#0b6e8f", alpha=0.85, label="open water, SSM level")
        ax.fill_between(tt, g["open_water_ha_modelled"], g["open_water_ha_modelled"] + g["wet_floor_ha_modelled"],
                        color="#d4a017", alpha=0.55, label="wet floor, SSM level")
        o = g[g["median_level_observed_m"].notna() & (g["n_wells_observed"] >= 20)]
        ax.plot(t[o.index], o["open_water_ha_observed"] + o["wet_floor_ha_observed"], color="black", lw=0.8,
                label="same curves on the observed level")
        ax.set_ylabel("ha (whole warren)"); ax.grid(alpha=0.3); ax.legend(fontsize=7.5, loc="upper left")
        ax.set_title(f"Mode {m} — SSM monthly level through the two curves", fontsize=9.5)
    fig.tight_layout(); fig.savefig(OUT / "W94_27_ssm_through_nir_curves.png", dpi=150); plt.close(fig)
    saved("W94_27_ssm_through_nir_curves.png")
    if animate:
        _animate(Hc, hb, hd, floor)
    phase(5, "The public feed the forecaster reads")
    write_wet_area_feed()
    return 0


def _animate(Hc, hb, hd, floor):
    """Month-by-month MP4 of the two classes under the SSM Mode R level, each
    cell switched at its own observed level. An illustration of the area model
    on the Sentinel grid, not a flood map (D-177 stands)."""
    import imageio                                            # noqa: PLC0415
    import matplotlib.pyplot as plt                           # noqa: PLC0415
    from PIL import Image                                     # noqa: PLC0415
    R = Hc[Hc["mode"] == "R"].reset_index(drop=True)
    bg = OUT / "W94_27_scene_2021-04-04.png"
    base = (np.array(Image.open(bg).convert("L")).astype(float) / 255 if bg.exists()
            else np.full(floor.shape, 0.6))
    rgb = np.stack([base * 0.55 + 0.25] * 3, -1)
    fig = plt.figure(figsize=(9.2, 6.4), dpi=100); gs = fig.add_gridspec(5, 1)
    ax, ax2 = fig.add_subplot(gs[:4]), fig.add_subplot(gs[4])
    t, lvl = pd.to_datetime(R["month"]), R["median_level_modelled_m"].values
    ax2.plot(t, lvl, color="black", lw=0.8); ax2.axhline(0, color="grey", lw=0.6, ls=":")
    ax2.set_ylabel("SSM level, m", fontsize=8); ax2.tick_params(labelsize=7); ax2.set_ylim(-1.3, 0.2)
    marker = ax2.axvline(t[0], color="#c0504d", lw=1.4)
    im = ax.imshow(rgb); ax.set_axis_off(); title = ax.set_title("", fontsize=10)
    frames = []
    for i in range(len(R)):
        h = lvl[i]; img = rgb.copy(); y, b = floor & (hd <= h), floor & (hb <= h)
        img[y] = [0.85, 0.68, 0.10]; img[b] = [0.04, 0.43, 0.56]
        im.set_data(img); marker.set_xdata([t[i], t[i]])
        title.set_text(f"{t[i].strftime('%B %Y')} — SSM Mode R level {h:+.2f} m   open water "
                       f"{b.sum() * 0.01:.0f} ha   wet floor {y.sum() * 0.01 - b.sum() * 0.01:.0f} ha")
        fig.canvas.draw(); a = np.asarray(fig.canvas.buffer_rgba())[..., :3]
        frames.append(a[:a.shape[0] // 2 * 2, :a.shape[1] // 2 * 2].copy())
    plt.close(fig)
    try:
        import imageio_ffmpeg                                 # noqa: PLC0415,F401
        imageio.mimwrite(OUT / "W94_27_wet_area_animation_modeR.mp4", frames, fps=8, codec="libx264",
                         quality=8, macro_block_size=None)
        saved("W94_27_wet_area_animation_modeR.mp4")
    except ImportError:
        # no ffmpeg plugin on this machine (imageio falls through to tifffile and
        # rejects fps): write an animated GIF instead, same frames, same rate
        warn("imageio-ffmpeg not installed (pip install imageio-ffmpeg for the MP4); writing a GIF")
        Image.fromarray(frames[0]).save(OUT / "W94_27_wet_area_animation_modeR.gif", save_all=True,
                                        append_images=[Image.fromarray(f) for f in frames[1:]],
                                        duration=125, loop=0)
        saved("W94_27_wet_area_animation_modeR.gif")


# ── the public feed the forecaster reads (T-36 item 1, D-178) ────────────────
# WHY THIS TOOL WRITES IT. W94_27_wet_area_model.csv and W94_27_cell_thresholds.npz
# live in the private store; the forecaster is public and reads from living/. The
# feed is therefore written by the thing that COMPUTES the model — route (a) of the
# 2026-09-16 spec — on D-096's reasoning: a feed the page trusts has to be emitted
# by the code that produced its numbers, not by a second reader of its outputs.
# Nothing in nrg_git.sh objects: the public repo stages living/ with `git add -A`,
# living/wet_area_model.json is not gitignored, and this tool is ALREADY a public
# file (the spec's route (b) was argued from "keeps the tool private-only", which
# is not the case — tools/sentinel_wet_floor.py is tracked in the public repo).
#
# It reads the two artefacts back from disk rather than serialising the in-memory
# fit, so the feed is provably the committed model and carries its hash.
LIVING_FEED = REPO / "living" / "wet_area_model.json"
FEED_SCHEMA = "nw-wet-area-1"
CELL_NEVER = 32767            # int16 sentinel: never in the class, or not on the floor.
#   NOT -1, which the spec proposed: -1 cm is a LEGAL switching level (-0.01 m) and
#   the fitted range runs -0.80 to +0.03 m, so -1 collides with real data.
LEVEL_DEFINITION = ("median of the monthly dipwell readings across the recorded network "
                    "(01_wells_all + D-166 months), m, 0 at ground")


def _sha16(path) -> str:
    import hashlib                                            # noqa: PLC0415
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


SSM_CURVES = OUT / "W94_27_ssm_through_nir_curves.csv"   # phase 4's drive; optional
WELL_FIT = OUT / "W94_27_well_fit.csv"                  # phase 27's per-well-month fit


def _mode_fit():
    """Each hindcast mode's fit against the wells: RMSE and Spearman rho over every
    well-month with both an observed and a modelled level.

    COMPUTED, not scraped. `W94_27_hindcast_summary.csv` states the same figures, but
    in a prose `value` cell ("R 0.229 / C 0.366") and a prose `notes` cell — a regex
    over those would go on returning a number long after the format moved. The raw
    per-well-month table is right there; rank correlation is done the way `_fit_exp`
    does it, so this still runs on a host with no scipy.
    """
    if not WELL_FIT.exists():
        return None
    F = pd.read_csv(WELL_FIT)
    need = {"mode", "observed_h_m", "modelled_h_recurrence_m"}
    if not need.issubset(F.columns):
        warn(f"{WELL_FIT.name} has no {sorted(need - set(F.columns))}; mode fit omitted")
        return None
    out = {"source": WELL_FIT.name, "source_hash": _sha16(WELL_FIT),
           "definition": ("modelled_h_recurrence_m against observed_h_m over every "
                          "well-month carrying both; rho is Spearman"),
           "modes": {}}
    for mode, g in F.groupby("mode"):
        d = g[["observed_h_m", "modelled_h_recurrence_m"]].dropna()
        if len(d) < 2:
            continue
        err = d["modelled_h_recurrence_m"].to_numpy(float) - d["observed_h_m"].to_numpy(float)
        rho = float(d["modelled_h_recurrence_m"].rank().corr(d["observed_h_m"].rank()))
        out["modes"][str(mode)] = {"rmse_m": round(float(np.sqrt((err ** 2).mean())), 3),
                                   "rho": round(rho, 3), "n": int(len(d))}
    return out if out["modes"] else None


def _wet_area_history():
    """The SSM's monthly median level through the record, for the forecaster's
    history control — or None when phase 4 has not run.

    WHY IT IS IN THIS FEED. It is an SSM product, not a Sentinel one, which is a
    fair objection. It is here because the cell layer is a function of the median
    level and nothing else, so a level series is the only thing that lets the page
    show a month that has already happened — and because the film
    (`_animate`) draws exactly these levels, so a page fed from anywhere else
    could not be compared with it. Mode R is the film's mode. The observed level
    travels with it, unrounded from the CSV's own 3 dp, so the page can say which
    of the two it is drawing.
    """
    if not SSM_CURVES.exists():
        return None
    H = pd.read_csv(SSM_CURVES)
    need = {"month", "mode", "median_level_modelled_m"}
    if not need.issubset(H.columns):
        warn(f"{SSM_CURVES.name} has no {sorted(need - set(H.columns))}; history omitted")
        return None
    months = sorted(H["month"].astype(str).unique())
    idx = {m: i for i, m in enumerate(months)}
    level = {}
    for mode, g in H.groupby("mode"):
        col = [None] * len(months)
        for _, r in g.iterrows():
            v = r["median_level_modelled_m"]
            col[idx[str(r["month"])]] = None if pd.isna(v) else round(float(v), 3)
        level[str(mode)] = col
    obs = [None] * len(months)
    nobs = [None] * len(months)
    if "median_level_observed_m" in H.columns:
        for _, r in H.iterrows():
            i = idx[str(r["month"])]
            v = r["median_level_observed_m"]
            if obs[i] is None and not pd.isna(v):
                obs[i] = round(float(v), 3)
            if "n_wells_observed" in H.columns and nobs[i] is None and not pd.isna(r["n_wells_observed"]):
                nobs[i] = int(r["n_wells_observed"])
    fit = _mode_fit()
    return {"source": SSM_CURVES.name, "source_hash": _sha16(SSM_CURVES),
            "fit": fit,
            "definition": ("the SSM's monthly median well level (phase 27 recurrence) driving the "
                           "curves, D-178 item 3; mode R is the one the film animates"),
            "default_mode": "R" if "R" in level else sorted(level)[0],
            "months": months, "level_m": level,
            "level_observed_m": obs, "n_wells_observed": nobs}


def write_wet_area_feed() -> int:
    """living/wet_area_model.json — the two curves and the per-cell switching
    levels, as a public feed for the forecaster (T-36 item 1).

    Hash-gated like the engine feed (D-096): a run that does not move anything
    but `generated` rewrites nothing, so the file's timestamp stays a provenance
    claim rather than a byproduct of having run the tool again.
    """
    import base64                                             # noqa: PLC0415
    import json                                               # noqa: PLC0415
    from datetime import datetime, timezone                   # noqa: PLC0415
    model_csv = OUT / "W94_27_wet_area_model.csv"
    npz_path = OUT / "W94_27_cell_thresholds.npz"
    for p in (model_csv, npz_path):
        if not p.exists():
            warn(f"no {p.name} — run --two-class first; feed not written")
            return 1
    M = pd.read_csv(model_csv).set_index("cls")
    z = np.load(npz_path)
    floor = z["floor"].astype(bool)
    W = int((GRID["right"] - GRID["left"]) / GRID["res"])
    H = int((GRID["top"] - GRID["bottom"]) / GRID["res"])
    if floor.shape != (H, W):
        warn(f"{npz_path.name} is {floor.shape}, GRID says {(H, W)} — feed not written")
        return 1

    def _encode(a):
        """metres -> int16 centimetres, row-major, row 0 = NORTH (from_origin(left, top));
        CELL_NEVER where the cell is off the floor or was never seen in the class."""
        cm = np.rint(np.asarray(a, dtype="float64") * 100.0)
        out = np.full(cm.shape, CELL_NEVER, dtype="<i2")
        ok = floor & np.isfinite(cm) & (np.abs(cm) < CELL_NEVER)
        out[ok] = cm[ok].astype("<i2")
        return base64.b64encode(out.tobytes(order="C")).decode("ascii"), int(ok.sum())

    ow_b64, n_ow = _encode(z["h_open_water"])
    wf_b64, n_wf = _encode(z["h_wet_floor"])
    curves = {}
    for cls in ("open_water", "wet_floor", "dark_total"):
        if cls not in M.index:
            continue
        r = M.loc[cls]
        curves[cls] = {"a": float(r["a"]), "b": float(r["b"]),
                       "sigma_log": float(r["sigma_log"]),
                       "sigma_factor": float(r["sigma_factor"]),
                       "rho": float(r["rho"]), "n": int(r["n"])}
    hmin = float(M["h_min"].min())
    hmax = float(M["h_max"].max())
    history = _wet_area_history()
    body = {
        "schema": FEED_SCHEMA,
        "decision": "D-178",
        "source": f"sentinel_wet_floor.py {__version__} --two-class",
        "source_hash": _sha16(model_csv),
        "source_cells_hash": _sha16(npz_path),
        "level_definition": LEVEL_DEFINITION,
        "area_definition": ("hectares on the slack floors, scaled to the whole warren by the "
                            "scene's clear fraction; NOT a flood map (D-177)"),
        "curves": curves,
        "curve_form": "area_ha = a * exp(b * h); sigma is a log-space factor (x/div sigma_factor)",
        "fitted_range_m": {"min": hmin, "max": hmax},
        "classes": {
            "open_water": f"B8 <= {NIR_BLACK_RATIO:.2f} x the scene's clear-floor median",
            "wet_floor": f"{NIR_BLACK_RATIO:.2f} < B8 <= {NIR_DARK_RATIO:.2f} x median",
        },
        "grid": {"left": GRID["left"], "bottom": GRID["bottom"], "right": GRID["right"],
                 "top": GRID["top"], "res": GRID["res"], "crs": "EPSG:27700",
                 "cols": W, "rows": H},
        "cells": {
            "dtype": "int16", "byte_order": "little",
            "order": "row-major, row 0 = NORTH edge (top), column 0 = WEST edge (left)",
            "units": "centimetres of median well level (0 = ground)",
            "never": CELL_NEVER,
            "encoding": (
                "base64 of an int16 array, one value per 10 m cell: the median well level at "
                f"which the cell switches into the class; {CELL_NEVER} = never seen in the class, "
                f"seen in fewer than {CELL_MIN_SCENES} scenes, or not on the phase 29 floor. "
                "NOTE the asymmetry with `curves`: `cells.wet_floor` is the DARK-TOTAL switching "
                "level (B8 <= 0.80 x median, i.e. open water OR wet floor), exactly as "
                "sentinel_wet_floor._animate uses it — draw it as the yellow layer and overdraw "
                "open water in blue; the wet-floor-only cells are (wet_floor <= h) AND NOT "
                "(open_water <= h). `curves.wet_floor` is the RING alone (0.50-0.80)."),
            "n_open_water": n_ow, "n_wet_floor": n_wf,
            "n_floor": int(floor.sum()),
            "open_water": ow_b64, "wet_floor": wf_b64,
        },
        "history": history,
        "colours": {"open_water": "#0b6e8f", "wet_floor": "#d4a017"},
        "caveat": ("cells switch at the level Sentinel-2 saw them switch in 2016-2026; an "
                   "illustration of the area model on the Sentinel grid, not a prediction of "
                   "where water will stand (D-177)"),
    }
    if LIVING_FEED.exists():
        try:
            old = json.loads(LIVING_FEED.read_text(encoding="utf-8"))
            old.pop("generated", None)
            if old == json.loads(json.dumps(body)):
                info(f"{LIVING_FEED.name} unchanged (hash gate) — not rewritten")
                return 0
        except Exception:                                     # noqa: BLE001
            pass
    feed = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    feed.update(body)
    LIVING_FEED.parent.mkdir(parents=True, exist_ok=True)
    LIVING_FEED.write_text(json.dumps(feed, indent=1) + "\n", encoding="utf-8")
    if history:
        step(f"history: {len(history['months'])} months {history['months'][0]} to "
             f"{history['months'][-1]}, modes {'/'.join(sorted(history['level_m']))}")
        if history.get("fit"):
            for m, f in sorted(history["fit"]["modes"].items()):
                step(f"  mode {m}: RMSE {f['rmse_m']:.3f} m, rho {f['rho']:+.3f}, n {f['n']}")
        else:
            warn(f"no {WELL_FIT.name}: the page will explain the modes without their fit")
    else:
        warn(f"no {SSM_CURVES.name}: the feed carries no history and the page's history "
             f"control will be hidden")
    step(f"{n_ow} cells with an open-water switching level, {n_wf} with a dark-total one, "
         f"of {int(floor.sum())} on the floor; {LIVING_FEED.stat().st_size / 1024:.0f} kB")
    saved(f"living/{LIVING_FEED.name}  (the public feed — D-178, T-36)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--since", default="2016-01-01")
    ap.add_argument("--until", default=pd.Timestamp.today().date().isoformat())
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--validate", metavar="DATE",
                    help="score the fixed rule on data/geo/flood_extent_DATE_vetted.kml")
    ap.add_argument("--swir-test", nargs="+", metavar="DATE",
                    help="SWIR indices against these vetted dates; first date sets the threshold")
    ap.add_argument("--two-class", action="store_true",
                    help="the wet-area model (D-178): open water and wet floor from B8 vs the "
                         "wells, per-cell switching levels, the SSM drive; needs the series")
    ap.add_argument("--animate", action="store_true", help="with --two-class: the monthly MP4")
    ap.add_argument("--emit-feed", action="store_true",
                    help="rewrite living/wet_area_model.json from the committed "
                         "W94_27_wet_area_model.csv and W94_27_cell_thresholds.npz; no scene "
                         "read, no network, no rasterio")
    ap.add_argument("--cells", nargs="+", metavar="DATE",
                    help="supervised per-cell classifier trained on the first vetted date, "
                         "tested on the rest; writes vettable KMLs and true-colour overlays")
    args = ap.parse_args()
    warnings.filterwarnings("ignore", category=UserWarning, module="rasterio")
    banner("Sentinel-2 wet slack floor series", __version__)
    if args.emit_feed:
        # Before _warren_mask(): the feed is a re-read of two committed artefacts and
        # must run on a host without rasterio.
        phase(1, "The public feed the forecaster reads")
        return write_wet_area_feed()
    Wm = _warren_mask()
    if args.calibrate:
        phase(1, "Calibrating the darkness ratio on the vetted extent")
        calibrate(Wm)
        return 0
    if args.two_class:
        return two_class(Wm, animate=args.animate)
    if args.cells:
        phase(1, "Per-cell classifier trained on the vetted extent, every band")
        return cells(Wm, args.cells)
    if args.swir_test:
        phase(1, "SWIR against the vetted extents — can it split flooded from damp floor?")
        return swir_test(Wm, args.swir_test)
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
