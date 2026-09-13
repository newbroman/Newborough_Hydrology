#!/usr/bin/env python3
"""What part of the warren does the 2026-09-12 tiled series actually see, and at
what resolution, on each imagery date?

WHY THIS COMES FIRST. The tiles are being adopted as the flood read's evidence in
place of the vp2 series, because they are 1.4× to 2.9× finer and 2.8× to 6.8×
better registered. None of that matters on ground no frame covers. A flood area
computed from tiles that miss a third of the warren is not a smaller flood, it is
an unknown one — and the failure is silent, because a mosaic of whatever happened
to be captured still produces a polygon and an area.

So this tool answers, per date, three things and refuses to average them:

  COVERED     the fraction of the warren inside at least one frame's footprint.
  RESOLUTION  the ground sampling distance actually available at each cell, which
              is the FINEST of the frames covering it — tiles overlap, and where
              they do the better frame is the one that will be used.
  HOLES       where the gaps are, as polygons, because a gap at the lake edge and
              a gap in the open dune do not cost the same thing.

A FOOTPRINT IS NOT THE WHOLE FRAME. Each capture's usable window is Script 41's
`_frame_window`, which is what every other measurement in this project reads, and
the interface sits outside it. Using the full 1920 x 1040 would overstate
coverage by the width of two panels and a status bar.

Transforms come from the cache `tools/crossres_date_check.py --register` writes,
so this tool fits nothing itself and cannot disagree with the registration. A
frame that inherited its transform from a twin has the same footprint as that
twin by construction, so the inherited rows add dates and redundancy but never
new ground — they are counted separately for exactly that reason.

Usage:
    python3 tools/tile_coverage.py                  # CSV + per-date maps
    python3 tools/tile_coverage.py --res 5.0        # coarser grid, quicker
    python3 tools/tile_coverage.py --no-maps        # numbers only
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) - 2026-09-13. The covered-area
#   threshold is RETIRED (Martin). A gap can only hide flood where there is
#   a hollow to hold it, so what is reported is the hollow area inside the
#   gap - a bound on how far a total can be understated - carried with every
#   area instead of a pass/fail on covered fraction.
# 1.0.0  Hollingham (2026) - 2026-09-12. New: the coverage map for the tiled
#   series, the first step in moving the flood read off the vp2 frames
#   (D-159).

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from utils.console_utils import banner, info, phase, saved, step, warn  # noqa: E402

OUT = REPO / "working" / "updates"
CACHE = OUT / "crossres_transforms.json"
INVENTORY = OUT / "W159_registration_inventory.csv"
COVERAGE_CSV = OUT / "W159_coverage_by_date.csv"
MAP_DIR = OUT / "coverage_maps"
DEFAULT_RES_M = 5.0
# A hole smaller than the smallest thing this project calls a slack cannot hide
# one, so it is not reported as a gap. Derived, not chosen.
MIN_HOLE_AREA_M2 = None          # set from SLACK_MIN_AREA_M2 at run time
# THERE IS NO COVERED-AREA THRESHOLD ANY MORE, and its removal is the point.
# `TILE_MIN_COVERAGE` was 0.98, chosen when the (wrong, pre-SIFT) numbers said
# 100 %, and on corrected geometry it condemned fifteen dates of sixteen at
# 92-97 %. Any replacement figure would have been just as arbitrary, because
# COVERED AREA IS THE WRONG QUANTITY: a gap can only hide flood where there is a
# hollow to hold it, and a gap over bare ridge costs nothing.
#
# What is reported instead is the HOLLOW AREA INSIDE THE GAP — the most a flood
# total can be understated by — carried with every tile-derived area as an
# explicit bound rather than rounded away into a whole-warren claim.
#
# One hard exclusion remains, for the case where the bound swallows the
# measurement. Measured 2026-09-13, the 1 m dates hide 1.6-6.6 % of the warren's
# hollow and the two December composites hide 73.7 %, so any line between 10 %
# and 60 % separates them identically — which is how you can tell the variable is
# the right one. 0.10 is the conservative end of that indifference range.
HOLLOW_UNSEEN_MAX_FRAC = 0.10


def _m41():
    import importlib.util as iu                               # noqa: PLC0415
    spec = iu.spec_from_file_location("m41", str(REPO / "src" / "41_canopy_cover.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _grid(site, res):
    minx, miny, maxx, maxy = site.bounds
    ge = np.arange(np.floor(minx / res) * res, maxx + res, res)
    gn = np.arange(np.ceil(maxy / res) * res, miny - res, -res)
    return np.meshgrid(ge, gn)


def _rasterise(geom, EE, NN):
    from PIL import Image, ImageDraw                          # noqa: PLC0415
    h, w = EE.shape
    minx, maxy = EE[0, 0], NN[0, 0]
    res = float(EE[0, 1] - EE[0, 0])
    img = Image.new("1", (w, h), 0)
    dr = ImageDraw.Draw(img)
    polys = (list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom])
    for poly in polys:
        dr.polygon([((c[0] - minx) / res, (maxy - c[1]) / res)
                    for c in list(poly.exterior.coords)[:-1]], fill=1)
        for ring in poly.interiors:
            dr.polygon([((c[0] - minx) / res, (maxy - c[1]) / res)
                        for c in list(ring.coords)[:-1]], fill=0)
    return np.array(img, dtype=bool)


def _footprint(m41, pairs, shape, EE, NN):
    """Which grid cells fall inside this frame's usable window."""
    H = m41._homography(np.asarray(pairs, float))
    r0, r1, c0, c1 = m41._frame_window(shape[0], shape[1])
    u, v = H(EE.ravel(), NN.ravel())
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    ok = (u >= c0) & (u < c1) & (v >= r0) & (v < r1)
    return ok.reshape(EE.shape)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--res", type=float, default=DEFAULT_RES_M)
    ap.add_argument("--no-maps", action="store_true")
    a = ap.parse_args()
    banner("Tile coverage of the warren", __version__)

    if not CACHE.exists():
        warn(f"no transform cache at {CACHE.name}; run "
             f"'python3 tools/crossres_date_check.py --register' first")
        return 1
    from PIL import Image
    from shapely.geometry import shape as shapely_shape

    from utils.config import SLACK_MIN_AREA_M2
    from utils.warren_mask import warren_on

    m41 = _m41()
    frames = json.loads(CACHE.read_text())["frames"]
    tiles = {k: v for k, v in frames.items() if v["series"] == "tile"}
    inv = pd.read_csv(INVENTORY, float_precision="round_trip")
    inherited = inv[inv["status"] == "inherited"]
    by_source = {}
    for _, r in inherited.iterrows():
        by_source.setdefault(str(r["locate_source"]), []).append(str(r["file"]))
    info(f"{len(tiles)} registered tile(s) in the cache, "
         f"{len(inherited)} inherited frame(s) in the inventory")
    if not tiles:
        warn("the cache holds no tiles; nothing to map")
        return 1

    phase(1, "the warren, on a common grid")
    site = warren_on(str(inv["date"].max()))
    EE, NN = _grid(site, float(a.res))
    inside = _rasterise(site, EE, NN)
    cell_m2 = float(a.res) ** 2
    total = float(inside.sum()) * cell_m2
    step(f"grid {EE.shape[1]} x {EE.shape[0]} at {a.res:.1f} m; warren "
         f"{total / 1e4:.1f} ha in {int(inside.sum())} cell(s)")
    import geopandas as gpd                                   # noqa: PLC0415
    hollows = gpd.read_file(OUT / "W94_06_hollows.geojson").set_crs(
        "EPSG:27700", allow_override=True)
    hol_all = (hollows.union_all() if hasattr(hollows, "union_all")
               else hollows.unary_union)
    hol_mask = _rasterise(hol_all, EE, NN) & inside
    hol_total = float(hol_mask.sum()) * cell_m2
    info(f"{len(hollows)} hollow(s), {hol_total / 1e4:.1f} ha inside the warren — "
         f"this is what a gap can hide, and the only part of it that can")
    min_hole = float(SLACK_MIN_AREA_M2)
    info(f"a gap smaller than SLACK_MIN_AREA_M2 = {min_hole:.0f} m2 cannot hide a "
         f"slack and is not reported — derived, not chosen")

    phase(2, "per date: what is covered, and how finely")
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    dates = sorted({v["date"] for v in tiles.values() if v["date"]})
    for d in dates:
        mine = {k: v for k, v in tiles.items() if v["date"] == d}
        best = np.full(EE.shape, np.nan)          # finest GSD available per cell
        n_frames = 0
        for name, v in mine.items():
            p = REPO / "data" / "geo" / "slacks" / name
            if not p.exists():
                continue
            with Image.open(p) as im:
                w_, h_ = im.size
            fp = _footprint(m41, v["pairs"], (h_, w_), EE, NN) & inside
            g = float(v["gsd_m"])
            best = np.where(fp & (np.isnan(best) | (g < best)), g, best)
            n_frames += 1
        cov = np.isfinite(best) & inside
        f_cov = float(cov.sum()) / float(inside.sum())
        holes_m2 = float((inside & ~cov).sum()) * cell_m2
        # THE BOUND: hollow the tiles cannot see. Flood can only be missed where
        # there is a hollow to hold it, so this is the most the total can be
        # understated by — and it is a number to report, not a test to pass.
        unseen = float((hol_mask & ~cov).sum()) * cell_m2
        row = {
            "imagery_date": d,
            "frames_registered": n_frames,
            "frames_inherited": sum(len(by_source.get(k, [])) for k in mine),
            "covered_frac": round(f_cov, 4),
            "covered_ha": round(float(cov.sum()) * cell_m2 / 1e4, 1),
            "uncovered_ha": round(holes_m2 / 1e4, 1),
            "unseen_hollow_ha": round(unseen / 1e4, 2),
            "unseen_hollow_frac": (round(unseen / hol_total, 4)
                                   if hol_total else None),
            "gsd_best_m": (round(float(np.nanmin(best)), 3) if cov.any() else None),
            "gsd_median_m": (round(float(np.nanmedian(best[cov])), 3)
                             if cov.any() else None),
            "gsd_worst_m": (round(float(np.nanmax(best[cov])), 3)
                            if cov.any() else None),
            "frac_at_or_below_1_6m": (round(float((best[cov] <= 1.6).mean()), 4)
                                      if cov.any() else None),
        }
        rows.append(row)
        info(f"  {d}  {n_frames:2d} frame(s)  covered {f_cov * 100:5.1f} %  "
             f"GSD median {row['gsd_median_m']}  "
             f"UNSEEN HOLLOW {row['unseen_hollow_ha']:6.2f} ha "
             f"({(row['unseen_hollow_frac'] or 0) * 100:4.1f} % of all hollow)")
        if not a.no_maps:
            _draw(d, EE, NN, inside, best, MAP_DIR)

    D = pd.DataFrame(rows)
    D.to_csv(COVERAGE_CSV, index=False)
    saved(COVERAGE_CSV.name)

    phase(3, "what this says about using the tiles")
    usable = D[D["unseen_hollow_frac"] <= HOLLOW_UNSEEN_MAX_FRAC]
    excl = D[D["unseen_hollow_frac"] > HOLLOW_UNSEEN_MAX_FRAC]
    step(f"{len(usable)} date(s) usable, {len(excl)} excluded "
         f"(more than {HOLLOW_UNSEEN_MAX_FRAC * 100:.0f} % of the warren's "
         f"hollow unseen)")
    info("  a usable date's area is reported WITH its bound, never as a "
         "whole-warren total:")
    for r in usable.sort_values("unseen_hollow_ha").itertuples():
        info(f"    {r.imagery_date}: seen area + at most {r.unseen_hollow_ha:.2f} "
             f"ha unseen ({r.unseen_hollow_frac * 100:.1f} % of hollow)")
    for r in excl.itertuples():
        warn(f"    {r.imagery_date}: EXCLUDED — {r.unseen_hollow_ha:.1f} ha of "
             f"hollow unseen, {r.unseen_hollow_frac * 100:.0f} % of the warren's. "
             f"A total from this date would be a guess with a number on it. It "
             f"can still carry a per-slack read over the ground it does see.")
    info("NO FLOOD READ IS RUN OR CHANGED BY THIS TOOL. It reports what ground "
         "the series holds, so the decision about which dates can carry a "
         "warren-wide number is made on the coverage rather than discovered in "
         "the answer.")
    return 0


def _draw(date, EE, NN, inside, best, out_dir) -> None:
    """One map per date: resolution where covered, gaps picked out."""
    import matplotlib                                         # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                           # noqa: PLC0415

    from utils.render_utils import MPL_DEFAULTS                # noqa: PLC0415
    plt.rcParams.update(MPL_DEFAULTS)
    ext = (EE[0, 0], EE[0, -1], NN[-1, 0], NN[0, 0])
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    gap = inside & ~np.isfinite(best)
    ax.imshow(np.where(gap, 1.0, np.nan), extent=ext, origin="upper",
              cmap="Greys", vmin=0, vmax=1.4, interpolation="nearest")
    im = ax.imshow(np.where(inside, best, np.nan), extent=ext, origin="upper",
                   cmap="viridis_r", interpolation="nearest")
    cb = fig.colorbar(im, ax=ax, shrink=0.82)
    cb.set_label("finest available GSD (m/px)")
    ax.set_title(f"Tile coverage — {date}")
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    ax.set_aspect("equal")
    p = out_dir / f"W159_coverage_{date}.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
