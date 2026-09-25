#!/usr/bin/env python3
"""
sentinel_thumbs.py — small true-colour Sentinel-2 crops of the Warren for the film

WHAT THIS IS

  A TOOL, not a pipeline step. It picks FILM_THUMB_N winter scenes from the
  committed scene series (data/sentinel/two_class_series.csv) and, for each, fetches
  the true-colour (TCI) window of the listed stac_id from the public Earth Search
  archive. That is the same source the scene manifest names. Each window is
  reprojected onto the wet-area model's 10 m OSGB grid (WET_AREA_GRID), so a
  thumbnail and a model map of the same month register cell for cell. The PNGs and
  thumbs_manifest.csv are written to data/sentinel/thumbs/ and committed. Script 47
  reads them with no network access.

THE CHOICE IS A RULE, NOT A PICK

  Scenes that fed the D-178 fit (used_in_fit, not excluded) with at least
  FILM_THUMB_CLEAR_MIN_PCT of the warren clear are ranked by dark_total_ha. The
  FILM_THUMB_N scenes nearest the evenly spaced quantiles 0 .. 1 of that ranking are
  taken, which is always the driest and the wettest scene plus the ones spread
  between them. Only one scene per month is kept, so no two thumbnails point at the
  same place on the monthly check figure.

LICENCE

  The imagery carries the Copernicus credit "Contains modified Copernicus Sentinel
  data <year>". The manifest carries the year of each scene, and Script 47 writes
  the credit on the "Please read this" and "Credits" slides.

USAGE
  python3 tools/sentinel_thumbs.py            # select, fetch, write PNGs + manifest
  python3 tools/sentinel_thumbs.py --list     # show the selection only; no network

  Needs rasterio and network access. The stored PNGs are the TCI bytes as served,
  with no stretch: display stretching is a rendering decision and is made in
  Script 47.
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) - 2026-09-25. Each scene also gets its near-
#   infrared (B08) window, <date>_nir.png: 16-bit surface reflectance x 10000 with the
#   item's own scale and offset applied, so scenes before and after the 2022 processing
#   baseline (BOA offset) share one scale. Martin: the calibration slides show the band
#   the method reads, not true colour.
# 1.0.0  Hollingham (2026) - 2026-09-25. First cut, for Script 47 1.2.0
#   (spec NRG_spec_script47_v1_2_2026-09-25, items 3 and 4).

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.console_utils import banner, info, saved, step    # noqa: E402
from utils.config import (                                   # noqa: E402
    WET_AREA_GRID as GRID, FILM_THUMB_N, FILM_THUMB_CLEAR_MIN_PCT,
)
from utils.paths import (                                    # noqa: E402
    SENTINEL_TWO_CLASS_SERIES, SENTINEL_SCENE_MANIFEST, SENTINEL_THUMBS_DIR,
    SENTINEL_THUMBS_MANIFEST,
)

STAC_URL = "https://earth-search.aws.element84.com/v1"
NIR_SCALE = 1e-4          # reflectance per stored DN: the PNG holds reflectance x 10000
COLLECTION = "sentinel-2-l2a"

os.environ.setdefault("GDAL_HTTP_TIMEOUT", "120")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")


def select() -> pd.DataFrame:
    """The FILM_THUMB_N scenes, driest to wettest, by the rule in the docstring."""
    S = pd.read_csv(SENTINEL_TWO_CLASS_SERIES)
    M = pd.read_csv(SENTINEL_SCENE_MANIFEST, comment="#")
    M = M[M["used_in_fit"].astype(bool) & ~M["excluded"].astype(bool)
          & (M["clear_pct"] >= FILM_THUMB_CLEAR_MIN_PCT)]
    R = S.merge(M[["date", "stac_id", "clear_pct"]], on="date")
    R["month"] = R["date"].str[:7]
    R = R.sort_values(["dark_total_ha", "clear_pct"], ascending=[True, False])
    R = R.drop_duplicates("month", keep="first").reset_index(drop=True)
    picks, taken = [], set()
    for q in np.linspace(0, 1, FILM_THUMB_N):
        target = R["dark_total_ha"].quantile(q)
        order = (R["dark_total_ha"] - target).abs().sort_values().index
        i = next(j for j in order if j not in taken)
        taken.add(i)
        picks.append(i)
    return R.loc[sorted(picks, key=lambda j: R.loc[j, "dark_total_ha"])].reset_index(drop=True)


def _item(stac_id: str) -> dict:
    url = f"{STAC_URL}/collections/{COLLECTION}/items/{stac_id}"
    with urllib.request.urlopen(url, timeout=60) as r:          # noqa: S310
        return json.load(r)


def fetch(stac_id: str, asset: str = "visual") -> np.ndarray:
    """One asset's window over the grid, reprojected onto the 10 m OSGB grid: the TCI
    ("visual") as uint8 RGB, or a single band as float surface reflectance (the item's
    raster:bands scale and offset applied)."""
    import rasterio                                           # noqa: PLC0415
    from rasterio.transform import from_origin                # noqa: PLC0415
    from rasterio.warp import Resampling, reproject, transform_bounds  # noqa: PLC0415
    g = GRID
    W = int((g["right"] - g["left"]) / g["res"])
    H = int((g["top"] - g["bottom"]) / g["res"])
    tr = from_origin(g["left"], g["top"], g["res"], g["res"])
    a = _item(stac_id)["assets"][asset]
    with rasterio.open(a["href"]) as src:
        wb = transform_bounds("EPSG:27700", src.crs, g["left"] - 200, g["bottom"] - 200,
                              g["right"] + 200, g["top"] + 200)
        win = src.window(*wb).round_offsets().round_lengths()
        bands = [1, 2, 3] if asset == "visual" else [1]
        arr = src.read(bands, window=win).astype(np.float64)
        dst = np.zeros((len(bands), H, W), dtype=np.float64)
        for b in range(len(bands)):
            reproject(arr[b], dst[b], src_transform=src.window_transform(win), src_crs=src.crs,
                      dst_transform=tr, dst_crs="EPSG:27700", resampling=Resampling.bilinear)
    if asset == "visual":
        return np.moveaxis(np.clip(np.rint(dst), 0, 255).astype(np.uint8), 0, -1)
    rb = (a.get("raster:bands") or [{}])[0]
    return dst[0] * float(rb.get("scale", NIR_SCALE)) + float(rb.get("offset", 0.0))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true", help="show the selection; no network")
    a = ap.parse_args()
    banner("sentinel_thumbs", __version__)
    R = select()
    for _, r in R.iterrows():
        step(f"{r['date']}  {r['stac_id']}  dark {r['dark_total_ha']:.1f} ha  "
             f"level {r['h_scene']:+.3f} m  clear {r['clear_pct']:.1f} %")
    if a.list:
        return 0
    from PIL import Image                                     # noqa: PLC0415
    SENTINEL_THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for _, r in R.iterrows():
        p = SENTINEL_THUMBS_DIR / f"{r['date']}_tci.png"
        Image.fromarray(fetch(r["stac_id"])).save(p, optimize=True)
        q = SENTINEL_THUMBS_DIR / f"{r['date']}_nir.png"
        nir = np.clip(np.rint(fetch(r["stac_id"], "nir") / NIR_SCALE), 0, 65535).astype(np.uint16)
        Image.fromarray(nir).save(q, optimize=True)
        rows.append(dict(date=r["date"], stac_id=r["stac_id"], file=p.name, nir_file=q.name,
                         dark_total_ha=r["dark_total_ha"], h_scene=r["h_scene"],
                         sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                         nir_sha256=hashlib.sha256(q.read_bytes()).hexdigest()))
        saved(p.name, f"{p.stat().st_size / 1024:.0f} kB")
        saved(q.name, f"{q.stat().st_size / 1024:.0f} kB")
    with open(SENTINEL_THUMBS_MANIFEST, "w", encoding="utf-8") as f:
        f.write(f"# Sentinel-2 true-colour and near-infrared thumbnails for Script 47, written by "
                f"tools/sentinel_thumbs.py {__version__}.\n"
                "# TCI as served and B08 as reflectance x 10000 (16-bit), reprojected onto "
                "WET_AREA_GRID; no stretch. "
                "Credit: Contains modified Copernicus Sentinel data <year>.\n")
        pd.DataFrame(rows).to_csv(f, index=False)
    saved(SENTINEL_THUMBS_MANIFEST.name)
    info("commit data/sentinel/thumbs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
