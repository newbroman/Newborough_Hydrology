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
  python3 tools/sentinel_wet_floor.py --two-class      # regenerate data/sentinel/ inputs (D-178)
  python3 tools/sentinel_wet_floor.py --write-manifest # data/sentinel/sentinel_scene_manifest.csv

  Needs `pystac-client` (pip install pystac-client) and network. Per-scene
  rasters are cached under working/updates/sentinel_cache/ (gitignored size).
"""
from __future__ import annotations

__version__ = "1.12.0"  # Hollingham (2026) - 2026-09-17. T-40: the wet-area line
#   is now the pipeline. This tool keeps only the two scene-dependent steps —
#   --two-class writes the scene series and the per-cell switching levels into
#   data/sentinel/, --write-manifest writes the scene list there — and no longer
#   fits, drives the SSM, animates, or writes the feed: those are Steps 45
#   (src/45_wet_area_model.py) and 46 (src/46_wet_area_feed.py). The grid, class
#   ratios and cell-min move to utils.config; --emit-feed and --animate are gone.
# v1.11.0  Hollingham (2026) - 2026-09-17. --write-manifest:
#   sentinel_scene_manifest.csv, the LIST of Copernicus scenes the D-178
#   fit consumes (T-40, promoting this line into the pipeline). One row per fitted
#   scene: date, STAC id, tile, collection, cloud/clear, used_in_fit, and the
#   sha256 of its cached B8 array. The scenes are NOT bundled (Martin 2026-09-17):
#   a re-runner pulls their own from Copernicus by STAC id and verifies the
#   derivation against the committed series. Pure pandas + hashlib; no network,
#   no rasterio, so it runs anywhere.
# v1.10.0  Hollingham (2026) - 2026-09-17. `cells.floor`: the
#   phase 29 floor mask inside the warren, packbits-ed and base64-ed (~22 kB). The
#   feed could say which cells have a switching level but not which cells are FLOOR
#   - 11,703 of 30,697 - so a reader confined to the feed (Script 45, T-39) could
#   not draw the study area, nor the "floor never seen wet" fill the film uses for
#   a month beyond the record. Without it that reader has to open the private npz,
#   which is the one thing the feed exists to avoid.
# v1.9.0  Hollingham (2026) - 2026-09-17. The history block
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
from utils.paths import (                                    # noqa: E402
    DATA_FLOOD_CAL_LEVELS, DATA_GEO_DIR, DATA_SENTINEL_DIR,
    SENTINEL_TWO_CLASS_SERIES, SENTINEL_CELL_THRESHOLDS, SENTINEL_SCENE_MANIFEST,
)
# The model's grid, class ratios and cell-min are shared with Steps 45/46 (T-40),
# so they live in utils.config, not here.
from utils.config import (                                   # noqa: E402
    WET_AREA_GRID as GRID, NIR_BLACK_RATIO, NIR_DARK_RATIO, CELL_MIN_SCENES,
)

OUT = REPO / "working" / "updates"
CACHE = OUT / "sentinel_cache"
STAC_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-l2a"
WARREN_KML = DATA_GEO_DIR / "warren.kml"
TRUTH_KML = DATA_GEO_DIR / "flood_extent_2021-03-24_vetted.kml"
WELLS_ALL = REPO / "outputs" / "01_wells_all.csv"
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
# NIR_BLACK_RATIO, NIR_DARK_RATIO and CELL_MIN_SCENES are imported from utils.config
# (shared with Steps 45/46 since T-40).
TWO_CLASS_EXCLUDE = ("2016-12-26",)   # a 12-degree-sun December scene, 3.5x off the curve


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


def two_class(Wm):
    """Regenerate the two committed wet-area inputs from the Sentinel-2 scenes
    (T-40, D-178): the scene series and the per-cell switching levels.

    Phase 1 reads B8 for every winter scene and writes the series (h_scene and
    the class areas). Phase 2 turns the scene stack into the per-cell switching
    levels. Both land in data/sentinel/, the committed inputs of record. The FIT
    and the SSM drive are Step 45 (src/45_wet_area_model.py); the public feed is
    Step 46 (src/46_wet_area_feed.py) — this tool no longer produces them. Needs
    the scenes, so it runs only where the cache and rasterio are; run the series
    first.
    """
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
    SENTINEL_TWO_CLASS_SERIES.parent.mkdir(parents=True, exist_ok=True)
    R.to_csv(SENTINEL_TWO_CLASS_SERIES, index=False)
    saved(f"data/sentinel/{SENTINEL_TWO_CLASS_SERIES.name}  (Step 45 fits the curves from this)")
    phase(2, "Per-cell switching levels")
    order = np.argsort([s_[0] for s_ in stack])
    h = np.array([stack[i][0] for i in order])
    seen = np.stack([stack[i][1] for i in order]); black = np.stack([stack[i][2] for i in order])
    dark = np.stack([stack[i][3] for i in order])
    hb, eb = _cell_switch_levels(black, seen, h)
    hd, ed = _cell_switch_levels(dark, seen, h)
    hd = np.minimum(hd, hb)
    SENTINEL_CELL_THRESHOLDS.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(SENTINEL_CELL_THRESHOLDS, h_open_water=hb, h_wet_floor=hd,
                        err_open_water=eb, err_wet_floor=ed, n_seen=seen.sum(0), floor=floor,
                        grid=np.array([GRID["left"], GRID["bottom"], GRID["right"], GRID["top"], GRID["res"]]))
    step(f"{int((np.isfinite(hb) & floor).sum())} cells ever open water, "
         f"{int((np.isfinite(hd) & floor).sum())} ever wet floor, of {int(floor.sum())} on the floor")
    saved(f"data/sentinel/{SENTINEL_CELL_THRESHOLDS.name}  (Step 46 reads the cell layer from this)")
    step("The fit and the SSM drive are Step 45 (src/45_wet_area_model.py); the public feed is "
         "Step 46 (src/46_wet_area_feed.py). Run `python3 run_analysis.py` to rebuild them, or "
         "--write-manifest here to refresh the scene list.")
    return 0


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


# The manifest and the fitted-scene series are committed under data/sentinel/
# (T-40); SERIES_CSV (all scenes, cloud/clear) stays the working-store intermediate.
SERIES_CSV = OUT / "W94_27_sentinel_wet_floor.csv"       # scene ids + cloud/clear, all scenes


def write_scene_manifest() -> int:
    """data/sentinel/sentinel_scene_manifest.csv — the Copernicus scenes the D-178
    fit consumes, LISTED not bundled (T-40, D-179).

    Martin, 2026-09-17: "list the sentinel inputs; others rerunning the analysis
    will have to pull their own copies from Copernicus." So this is the input of
    record for the wet-area line: the scene identifiers a re-runner fetches from
    the Copernicus / Earth Search archive, with enough to know which fed the fit
    and a checksum of the derived B8 array so a re-fetch can be verified. The
    226 MB scene cache stays gitignored working-store; this list is what the
    pipeline commits.

    Pure pandas + hashlib — no scene read, no network, no rasterio — so it runs on
    any host, including the bridge. Dispatched before _warren_mask() for that
    reason.
    """
    import hashlib                                            # noqa: PLC0415
    for pth in (SERIES_CSV, SENTINEL_TWO_CLASS_SERIES):
        if not pth.exists():
            warn(f"no {pth.name} — run the series and --two-class first; manifest not written")
            return 1
    S = pd.read_csv(SERIES_CSV)
    fitted = set(pd.read_csv(SENTINEL_TWO_CLASS_SERIES)["date"].astype(str))
    # The fit takes the winter scenes with a well level, minus the excluded ones;
    # the two_class_series IS that set, so it is the authority for used_in_fit.
    rows = []
    for _, r in S.iterrows():
        date = str(r["date"])
        stac = str(r["scene"])
        parts = stac.split("_")
        tile = parts[1] if len(parts) > 1 else ""
        b8 = CACHE / f"b8_{date}.npz"
        sha = ""
        if b8.exists():
            h = hashlib.sha256()
            with open(b8, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            sha = h.hexdigest()
        rows.append({
            "date": date, "stac_id": stac, "tile": tile, "collection": COLLECTION,
            "tile_cloud_pct": round(float(r["tile_cloud_pct"]), 1),
            "clear_pct": round(float(r["clear_pct"]), 1),
            "winter": bool(r["winter"]),
            "used_in_fit": date in fitted,
            "excluded": date in TWO_CLASS_EXCLUDE,
            "b8_sha256": sha,
        })
    M = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    SENTINEL_SCENE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Sentinel-2 scene manifest for the Newborough wet-area model (D-178, T-40).\n"
        f"# The INPUT of record for the wet-area line: these Copernicus scenes are LISTED,\n"
        f"# not committed. Re-fetch each stac_id from {STAC_URL} (collection {COLLECTION}),\n"
        f"# reproject onto the {GRID['res']} m OSGB grid "
        f"[{GRID['left']},{GRID['bottom']},{GRID['right']},{GRID['top']}], and the derivation\n"
        f"# should reproduce data/sentinel/two_class_series.csv. b8_sha256 is the sha256 of\n"
        f"# this session's cached B8 array for the scene (working-store; blank where not cached).\n"
        f"# Classes: open water B8<={NIR_BLACK_RATIO} x floor median; wet floor {NIR_BLACK_RATIO}-{NIR_DARK_RATIO}.\n"
        f"# Generated by sentinel_wet_floor.py {__version__} --write-manifest.\n"
    )
    with open(SENTINEL_SCENE_MANIFEST, "w", encoding="utf-8", newline="") as fh:
        fh.write(header)
        M.to_csv(fh, index=False)
    n_fit = int(M["used_in_fit"].sum())
    step(f"{len(M)} scene(s) listed, {n_fit} used in the fit, "
         f"{int((M['b8_sha256'] != '').sum())} with a B8 checksum")
    saved(f"data/sentinel/{SENTINEL_SCENE_MANIFEST.name}  (the scene input list — T-40, D-179)")
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
                    help="regenerate the committed wet-area inputs (T-40, D-178): the scene "
                         "series and the per-cell switching levels, into data/sentinel/; needs "
                         "the series. The fit and feed are Steps 45/46, not this tool")
    ap.add_argument("--write-manifest", action="store_true",
                    help="write data/sentinel/sentinel_scene_manifest.csv (the scene input "
                         "list, T-40); no network, no rasterio")
    ap.add_argument("--cells", nargs="+", metavar="DATE",
                    help="supervised per-cell classifier trained on the first vetted date, "
                         "tested on the rest; writes vettable KMLs and true-colour overlays")
    args = ap.parse_args()
    warnings.filterwarnings("ignore", category=UserWarning, module="rasterio")
    banner("Sentinel-2 wet slack floor series", __version__)
    if args.write_manifest:
        # Before _warren_mask(): pure pandas + hashlib, runs on any host.
        phase(1, "The scene input list")
        return write_scene_manifest()
    Wm = _warren_mask()
    if args.calibrate:
        phase(1, "Calibrating the darkness ratio on the vetted extent")
        calibrate(Wm)
        return 0
    if args.two_class:
        return two_class(Wm)
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
