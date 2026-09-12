#!/usr/bin/env python3
"""
warren_flood_prep.py — step 1 of W94 (D-159): the warren mask, by frame date.

WHAT THIS IS, AND WHAT IT IS NOT

  A TOOL, not a pipeline step. It writes to `working/updates/`, not `outputs/`,
  and it is not in the manifest. That is deliberate: D-159's method has a
  falsification test it has not yet faced — both May frames must come back empty
  of flood patches — and registering a step whose method may not survive would
  move the documented pipeline counts for something provisional. When the method
  is proven it becomes a numbered script with its outputs in `outputs/`.

WHAT IT DOES

  1. Derives canopy closure per variable block from the committed Script 41
     index (`utils.warren_mask.closure_dates`), and writes the table.
  2. Writes the warren and canopy areas for every frame date in the manifest.
  3. Writes the warren polygon once per CANOPY EPOCH — the distinct states the
     mask takes across the series — as GeoJSON and KML, so it can be opened in
     Google Earth against the frames themselves.
  4. Reports which DEM basins fall inside the warren, since those are the basins
     a flood reading can be attributed to.

  Everything here is polygon and DEM work. No imagery is read.

NOT DONE HERE, AND WHY

  **The repeat-floor drift test cannot run yet.** The specification lists it as
  step 1, which was wrong: comparing a slack's floor elevation between two dates
  needs DIGITISED OUTLINES on both, and there are none. The 2023 LiDAR against
  2006-2026 frames remains an open assumption; the substitute check available
  today is the DEM-minus-DGPS residual (median +0.050 m, MAD 0.030 m at 81
  wells), and what would make it decisive is the DGPS survey DATE, which no
  record in this tree states.

  See D-159 and `working/updates/NRG_spec_W94_warren_flood_surface_2026-09-11.md`.
"""
from __future__ import annotations

__version__ = "1.4.0"  # Hollingham (2026) - 2026-09-11. PHASE 8, the flood read
#   (D-159, spec NRG_spec_W94_phase8_flood_read_2026-09-11.md). The photographs
#   classify and the DEM only names the result. Each frame is normalised against
#   its OWN OPEN DUNE - the warren less the hollows, never flooded by
#   construction - so the cut is exposure-free across five rights-holders; a
#   BIMODALITY GATE lets a dry frame return DRY, which plain Otsu cannot, and
#   that is what makes the two May negatives a test the method can fail. The vp2
#   transform is cached as CONTROL POINTS (registration costs two minutes), and
#   one transform serves every vp2 frame - measured, which is what lets
#   2010-05-27 be read at all. `--phase` and `--date` added; the tool is no
#   longer all-or-nothing. THE CUT IS EACH FRAME'S OWN OTSU THRESHOLD, gated on
#   where that threshold falls (config 1.40.0): measured on five frames, the
#   between-class variance separates wet from dry by 0.713 against 0.604 and the
#   threshold POSITION by 1.15 z, so the gate moved to the statistic that
#   carries the signal and no value is frozen from one frame onto fifteen.
#   --calibrate MERGES by date rather than overwriting:
#   the cut comes from a wet frame and the gate from frames the record says are
#   dry, so the file is built up across runs.
# v1.3.0 superseded within the day; see the note above.
# v1.2.0  # Hollingham (2026) - 2026-09-11. THE HOLLOW AND THE
#   SLACK ARE SEPARATED. A depression was SELECTED on holding SLACK_MIN_DEPTH_M
#   and then DRAWN floor-to-spill, so every internal rise inside it was mapped as
#   slack - the ridge Martin can see near CEH32. Measured on that node: 5.60 ha
#   drawn, 0.01 ha wet at floor + 0.10 m, 89 % of it more than 0.5 m above its
#   own floor; area-weighted over 400 slacks the wet fraction is 0.05. Phase 6
#   now emits BOTH - `W94_06_hollows.*`, the node extent, which is the
#   attribution unit, and `W94_06_slacks.*`, the surface at floor +
#   SLACK_MIN_DEPTH_M, which is the wet area and the thing a photograph can be
#   compared with. "Hollow" rather than the spec's "basin" because phases 4 and 5
#   already use `basin` for the Ranwell catchments. D-159.
# v1.1.0  # Hollingham (2026) - 2026-09-11. SLACKS, delineated from
#   the DEM as closed depressions, replace the Ranwell prototype basins as the
#   scoring unit (Martin: "the basins are too large and don't represent the
#   slacks"). Phase 4 now reports both, so the scale difference is visible
#   rather than asserted.
# v1.0.0  # Hollingham (2026) - 2026-09-11. New, for D-159 step 1.

import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import geopandas as gpd                                      # noqa: E402
import numpy as np                                           # noqa: E402
import pandas as pd                                          # noqa: E402
import rasterio                                              # noqa: E402
from rasterio.mask import mask as rio_mask                    # noqa: E402

from utils.config import CANOPY_CLOSURE_RATIO                 # noqa: E402
from utils.console_utils import banner, info, phase, saved, step, warn  # noqa: E402
from utils.paths import DATA_DEM, DATA_GEO_DIR                # noqa: E402
from utils.warren_mask import (OSGB, _features, canopy_on, closure_dates,
                               warren_on)  # noqa: E402

OUT = REPO / "working" / "updates"
MANIFEST = DATA_GEO_DIR / "aerial_manifest.csv"
BASINS = DATA_GEO_DIR / "ranwell_dem_basins_prototype.geojson"
# The vp2 frame the shared transform is fitted on. Any vp2 frame would do -
# phase-correlating every one of them against this frame returns (0, 0) px -
# and this one is named because it is the frame the twin test was run on.
VP2_REFERENCE_FRAME = "site24-3-2021m.png"


def main() -> int:
    import argparse                                          # noqa: PLC0415
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", type=int, default=None,
                    help="run one phase only (8 is the flood read)")
    ap.add_argument("--date", action="append", default=None,
                    help="restrict phase 8 to this frame date; repeatable")
    ap.add_argument("--calibrate", action="store_true",
                    help="phase 8: report the open-dune z at wet and dry wells "
                         "and write W94_08_calibration.csv, writing no result")
    args = ap.parse_args()

    banner("W94 step 1 — the warren mask by frame date", __version__)
    if args.phase == 8:
        return phase8(dates=args.date, calibrate=args.calibrate)
    if args.phase is not None:
        warn(f"--phase {args.phase} is not separable; phases 1-7 run together")
        return 1

    phase(1, "Canopy closure, derived from the committed Script 41 index")
    info(f"a block is canopy once its index reaches {CANOPY_CLOSURE_RATIO} of the "
         f"same-frame forest control, applied monotonically")
    closures = closure_dates()
    cdf = pd.DataFrame(
        [{"block": b,
          "canopy_from": "" if d is None else str(pd.Timestamp(d).date()),
          "open_throughout": d is None}
         for b, d in sorted(closures.items())])
    p = OUT / "W94_01_canopy_closure.csv"
    cdf.to_csv(p, index=False)
    saved(p.name)

    phase(2, "Warren and canopy area, per frame date")
    man = pd.read_csv(MANIFEST, float_precision="round_trip")
    dates = sorted(set(man["imagery_date"].astype(str)))
    rows = []
    for d in dates:
        w, c = warren_on(d, closures), canopy_on(d, closures)
        rows.append({"imagery_date": d,
                     "warren_ha": round(w.area / 1e4, 3),
                     "canopy_ha": round(c.area / 1e4, 3),
                     "frames": int((man["imagery_date"].astype(str) == d).sum())})
    adf = pd.DataFrame(rows)
    p = OUT / "W94_02_warren_area_by_date.csv"
    adf.to_csv(p, index=False)
    saved(p.name)
    step(f"warren spans {adf['warren_ha'].min():.1f} to "
         f"{adf['warren_ha'].max():.1f} ha across {len(adf)} frame date(s) — "
         f"a {adf['warren_ha'].max() - adf['warren_ha'].min():.1f} ha swing, "
         f"which is the canopy changing, not the boundary")

    phase(3, "The warren polygon, once per canopy epoch")
    # One geometry per DISTINCT mask, not per date: sixteen dates collapse to a
    # handful of states, and writing sixteen identical polygons would invite a
    # reader to think they differ.
    epochs, seen = [], {}
    for d in dates:
        key = round(warren_on(d, closures).area, 3)
        if key not in seen:
            seen[key] = d
            epochs.append(d)
    info(f"{len(epochs)} distinct canopy state(s) across {len(dates)} date(s): "
         f"{', '.join(epochs)}")
    g = gpd.GeoDataFrame(
        {"epoch_from": epochs,
         "warren_ha": [round(warren_on(d, closures).area / 1e4, 3) for d in epochs]},
        geometry=[warren_on(d, closures) for d in epochs], crs=OSGB)
    # OVERWRITE BY TRUNCATION, NEVER BY UNLINK. A GDAL driver replaces an
    # existing file by deleting it first, and the desktop-bridge mount refuses
    # unlink — so a re-run fails with PermissionError on a file the first run
    # wrote. Writing the bytes ourselves truncates in place and works on both.
    p = OUT / "W94_03_warren_epochs.geojson"
    p.write_text(g.to_crs(OSGB).to_json(), encoding="utf-8")
    saved(p.name)
    p = OUT / "W94_03_warren_epochs.kml"
    tmp = Path(tempfile.mkdtemp()) / "epochs.kml"
    g.to_crs("EPSG:4326").to_file(tmp, driver="KML")
    p.write_bytes(tmp.read_bytes())
    shutil.rmtree(tmp.parent, ignore_errors=True)
    saved(p.name)

    phase(4, "Which DEM basins lie in the warren")
    if not BASINS.is_file():
        warn(f"{BASINS.name} not found — basin attribution skipped")
        return 0
    b = gpd.read_file(BASINS).to_crs(OSGB)
    latest = warren_on(dates[-1], closures)
    earliest = warren_on(dates[0], closures)
    rows = []
    with rasterio.open(DATA_DEM) as dem:
        px = dem.res[0] * dem.res[1]
        for i, row in b.iterrows():
            geom = row.geometry
            try:
                a, _ = rio_mask(dem, [geom], crop=True, filled=False)
                v = a[0].compressed()
            except Exception as exc:                       # noqa: BLE001
                warn(f"basin {i}: DEM read failed ({exc})")
                continue
            if v.size < 50:
                continue
            floor = float(np.percentile(v, 1))
            rows.append({
                "basin": row.get("basin", i),
                "area_ha": round(geom.area / 1e4, 3),
                "floor_m": round(floor, 3),
                "in_warren_earliest_pct": round(
                    100.0 * geom.intersection(earliest).area / geom.area, 1),
                "in_warren_latest_pct": round(
                    100.0 * geom.intersection(latest).area / geom.area, 1),
                "ha_below_floor_plus_0_1": round((v <= floor + 0.1).sum() * px / 1e4, 3),
                "ha_below_floor_plus_0_2": round((v <= floor + 0.2).sum() * px / 1e4, 3),
                "ha_below_floor_plus_0_5": round((v <= floor + 0.5).sum() * px / 1e4, 3),
            })
    bdf = pd.DataFrame(rows)
    p = OUT / "W94_04_basin_warren_sensitivity.csv"
    bdf.to_csv(p, index=False)
    saved(p.name)
    if len(bdf):
        r2 = (bdf["ha_below_floor_plus_0_2"] / bdf["ha_below_floor_plus_0_1"]).replace(
            [np.inf, -np.inf], np.nan).dropna()
        r5 = (bdf["ha_below_floor_plus_0_5"] / bdf["ha_below_floor_plus_0_1"]).replace(
            [np.inf, -np.inf], np.nan).dropna()
        step(f"extent sensitivity, median over {len(r2)} basin(s): "
             f"+0.2 m gives {r2.median():.2f}x the area of +0.1 m, "
             f"+0.5 m gives {r5.median():.2f}x")
        info("this is why D-159 scores flooding PER SLACK and treats area as "
             "secondary: a 0.1 m level error moves the area by about half, and "
             "the DEM's own sd is 0.145 m")
    phase(5, "Map — the basins on the warren, by epoch")
    import matplotlib.pyplot as plt                          # noqa: PLC0415
    from matplotlib.patches import Patch                     # noqa: PLC0415

    from utils.config import (SITE_MAP_EAST_MAX, SITE_MAP_EAST_MIN,
                              SITE_MAP_NORTH_MAX, SITE_MAP_NORTH_MIN)
    from utils.map_utils import add_en_axes, load_dem_hillshade
    from utils.render_utils import apply_house_style, render_figure

    apply_house_style()
    fig, ax = plt.subplots(figsize=(8.6, 7.4))
    load_dem_hillshade(ax, DATA_GEO_DIR, alpha=0.55)

    # The warren at its LARGEST and SMALLEST, so the canopy swing is the thing
    # the eye picks up rather than a single outline that looks definitive.
    first, last = epochs[0], epochs[-1]
    w_first, w_last = warren_on(first, closures), warren_on(last, closures)
    c_first, c_last = canopy_on(first, closures), canopy_on(last, closures)
    site = w_last.union(c_last)
    w_ref = warren_on('2021-03-24', closures)   # the strongest flood date

    # Draw what is EXCLUDED, not what is included. The question this map answers
    # is "which basins can be read from the air", and the eye answers it faster
    # from the canopy than from a warren fill that the basins would sit on top of.
    gpd.GeoSeries([c_last.intersection(site)], crs=OSGB).plot(
        ax=ax, facecolor="#4d7c4d", edgecolor="#2f4f2f", alpha=0.45, linewidth=0.6,
        zorder=2)
    # Ground that was OPEN in the first frame and canopy by the last — the 1998
    # replant closing. This is the part a static forest mask would get wrong.
    closing = c_last.difference(c_first).intersection(site)
    if not closing.is_empty:
        gpd.GeoSeries([closing], crs=OSGB).plot(
            ax=ax, facecolor="#c7e9c0", edgecolor="#2f4f2f", alpha=0.85,
            linewidth=0.6, hatch="///", zorder=3)
    # Ground that was canopy in the first frame and open by the last — the 2017
    # clearfell, which inverts.
    opening = c_first.difference(c_last).intersection(site)
    if not opening.is_empty:
        gpd.GeoSeries([opening], crs=OSGB).plot(
            ax=ax, facecolor="#fdae6b", edgecolor="#a63603", alpha=0.9,
            linewidth=0.6, hatch="\\\\", zorder=3)

    gpd.GeoSeries([w_last], crs=OSGB).plot(
        ax=ax, facecolor="none", edgecolor="#08519c", linewidth=1.3, zorder=5)
    b.plot(ax=ax, facecolor="none", edgecolor="#d94801", linewidth=1.6, zorder=6)
    for _, row in b.iterrows():
        c = row.geometry.representative_point()
        share = (100.0 * row.geometry.intersection(w_last).area / row.geometry.area)
        ax.annotate(f"{row.get('basin', '?')}\n{share:.0f}%",
                    (c.x, c.y), ha="center", va="center", fontsize=8, zorder=7,
                    bbox=dict(boxstyle="round,pad=0.18", fc="white",
                              ec="#d94801", lw=0.6, alpha=0.9))

    ax.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
    ax.set_ylim(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)
    add_en_axes(ax, apply_extent=False)
    handles = [
        Patch(facecolor="#4d7c4d", edgecolor="#2f4f2f", alpha=0.45,
              label=f"canopy at {last} — excluded"),
        Patch(facecolor="#c7e9c0", edgecolor="#2f4f2f", hatch="///",
              label=f"open in {first}, canopy by {last} (1998 replant closing)"),
        Patch(facecolor="#fdae6b", edgecolor="#a63603", hatch="\\\\",
              label=f"canopy in {first}, open by {last} (2017 clearfell)"),
        Patch(facecolor="none", edgecolor="#08519c", linewidth=1.3,
              label=f"warren at {last} ({w_last.area / 1e4:.0f} ha; "
                    f"{w_first.area / 1e4:.0f} ha at {first})"),
        Patch(facecolor="none", edgecolor="#d94801", linewidth=1.6,
              label="DEM basin (label: % in the warren)"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7.5, framealpha=0.92)
    ax.set_title("W94 — which DEM basins can be read from the air\n"
                 "canopy excluded by frame date; the hatched blocks are the ground "
                 "a static forest mask would get wrong")
    p = OUT / "W94_05_basins_on_warren.png"
    render_figure(fig, p)
    saved(p.name)

    phase(6, "Slacks — closed depressions in the DEM")
    from scipy import ndimage as ndi                         # noqa: PLC0415
    from rasterio.features import geometry_mask, shapes      # noqa: PLC0415
    from shapely.geometry import shape as shapely_shape      # noqa: PLC0415

    from utils.config import SLACK_MIN_AREA_M2, SLACK_MIN_DEPTH_M
    from utils.slacks import leaf_ids, merge_tree

    with rasterio.open(DATA_DEM) as dem_src:
        db = dem_src.bounds
        want = site.bounds
        # CLAMP TO THE RASTER. `site` is the warren UNION the canopy, and the
        # forest block runs well outside both the site boundary and the DEM
        # footprint — asking for its bounds gives a window partly off the raster,
        # which rasterio serves without complaint and which silently misplaces
        # every cell. Measured while this was wrong: the warren came back as
        # 104.5 ha of the window instead of 656.9, and the slack count in the
        # warren fell from 167 to 31.
        read_b = (max(want[0], db.left), max(want[1], db.bottom),
                  min(want[2], db.right), min(want[3], db.top))
        if read_b != want:
            info("the requested window runs outside the DEM (the forest block "
                 "does); clamped to the raster footprint")
        win = rasterio.windows.from_bounds(*read_b, dem_src.transform)
        arr = dem_src.read(1, window=win).astype("float32")
        tr = dem_src.window_transform(win)
        cell = abs(tr.a * tr.e)
    info(f"site window {arr.shape[1]} x {arr.shape[0]} cells at {abs(tr.a):.0f} m")
    # The warren must be essentially inside the window, or every count below is
    # measured against the wrong ground.
    _wm_check = geometry_mask([w_ref], out_shape=arr.shape, transform=tr,
                              invert=True)
    _cover = 100.0 * _wm_check.sum() * cell / w_ref.area
    if _cover < 99.0:
        warn(f"only {_cover:.1f} % of the warren falls inside the DEM window — "
             f"the slack counts below are measured against the wrong ground. "
             f"Fix the window before reading anything from them.")
    else:
        info(f"{_cover:.1f} % of the warren is inside the window")
    # THE MERGE TREE, not a fixed-depth labelling: slacks merge as the level
    # rises (Martin, 2026-09-11), so the unit is a node of a hierarchy and a
    # level, never a static polygon.
    leaf, nodes = merge_tree(arr)
    leaves = leaf_ids(nodes)
    by_id = {n["id"]: n for n in nodes}
    Nn = len(nodes)
    par = np.fromiter((nd["parent"] for nd in nodes), dtype=np.int64, count=Nn)
    depth_a = np.fromiter(((nd["merge_level_m"] - nd["floor_m"])
                           if nd["parent"] != -1 else -1.0 for nd in nodes),
                          dtype=float, count=Nn)
    area_a = np.fromiter((nd["cells"] * cell for nd in nodes),
                         dtype=float, count=Nn)
    open_a = np.fromiter((nd["open"] for nd in nodes), dtype=bool, count=Nn)

    # A LEAF IS NOT A SLACK. There are a quarter of a million local minima in
    # this DEM and they are pinholes: taking leaves as the unit gave 87 in the
    # warren and none above 500 m2. The slack is the LARGEST node on each branch
    # that still holds water — qualifying, with no qualifying ancestor.
    qual = (~open_a) & (depth_a > SLACK_MIN_DEPTH_M) & (area_a >= SLACK_MIN_AREA_M2)
    idx = np.arange(Nn, dtype=np.int64)
    jump = np.where(par < 0, idx, par)
    cur, anc = jump.copy(), qual[jump].copy()
    for _ in range(64):
        nxt = jump[cur]
        if (nxt == cur).all():
            break
        cur = nxt
        anc |= qual[cur]
    maximal = qual & ~anc
    sdf = pd.DataFrame([
        {"slack": int(i), "cells": by_id[int(i)]["cells"],
         "area_m2": float(area_a[i]), "floor_m": float(by_id[int(i)]["floor_m"]),
         "spill_m": float(by_id[int(i)]["merge_level_m"]),
         "depth_m": float(depth_a[i])}
        for i in np.flatnonzero(maximal)])
    info(f"merge tree: {Nn} node(s), {len(leaves)} local minima; "
         f"{int(qual.sum())} qualify at depth > {SLACK_MIN_DEPTH_M} m and "
         f">= {SLACK_MIN_AREA_M2:.0f} m2, of which {len(sdf)} are maximal on "
         f"their branch — those are the slacks")
    # Rasterise the kept slacks: a cell belongs to the kept ANCESTOR of its leaf.
    keep_set = set(sdf["slack"])
    # Map every node to its kept ancestor by POINTER JUMPING, then index the
    # leaf raster through it. Two earlier drafts were too slow to finish: a loop
    # over 264k leaf labels against 3.8M cells (10^12 comparisons), and a Python
    # chain-walk over all 516k nodes. This is a handful of vectorised passes.
    N = len(nodes)
    par = np.fromiter((nd["parent"] for nd in nodes), dtype=np.int64, count=N)
    idx = np.arange(N, dtype=np.int64)
    par = np.where(par < 0, idx, par)                 # roots point at themselves
    res = np.full(N, -1, dtype=np.int64)
    for k in keep_set:
        res[k] = k
    jump = par.copy()
    for _ in range(64):
        todo = (res < 0) & (jump != idx)
        if not todo.any():
            break
        res[todo] = res[jump[todo]]
        jump = jump[jump]
    lut = np.zeros(N + 1, dtype="int32")
    lut[:N] = np.where(res < 0, 0, res)
    lab = lut[leaf]

    # In the warren, and gauged or not — the two facts that decide whether a
    # slack can be READ from the air and whether the network already reports it.
    wmask = geometry_mask([w_ref], out_shape=arr.shape, transform=tr, invert=True)
    in_warren = {int(v) for v in np.unique(lab[wmask & (lab > 0)])}
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    inv = ~tr
    # HYDRAULIC ATTACHMENT, not a distance. A well belongs to the slack whose
    # depression contains it in the hierarchy, and it becomes wet when the level
    # reaches its OWN ground — which is what an edge-sited well is (Martin,
    # 2026-09-10: sited at slack edges for ease of measurement). No metres to
    # choose, and `nearest_well_m` stays for wells no depression reaches.
    gauged, wet = {}, {}
    for _, r in wells.iterrows():
        col, row = inv * (r["E"], r["N"])
        col, row = int(col), int(row)
        if 0 <= row < lab.shape[0] and 0 <= col < lab.shape[1]:
            lv = int(lab[row, col])
            if lv:
                gauged.setdefault(lv, []).append(str(r["Name"]))
                wet.setdefault(lv, []).append(round(float(arr[row, col]), 2))
    sdf["in_warren"] = sdf["slack"].isin(in_warren)
    sdf["wells_inside"] = sdf["slack"].map(lambda k: ";".join(gauged.get(k, [])))
    sdf["wells_wet_at_m"] = sdf["slack"].map(
        lambda k: ";".join(str(v) for v in wet.get(k, [])))
    # POINT-IN-POLYGON IS THE WRONG JOIN HERE, and the record says why: wells
    # were sited at slack EDGES for ease of measurement (Martin, 2026-09-10;
    # CEH1, CEH9 and NW6 named). Measured: only 37 of 99 wells fall inside a
    # warren slack, the median well sits 13.6 m from the nearest one, and 52 are
    # within 20 m. So "contains a well" undercounts the gauged slacks badly.
    # The distance is written out and the THRESHOLD IS NOT CHOSEN HERE — it is a
    # design call, and baking one in would fix a headline count by fiat.
    sdf["area_ha"] = (sdf["area_m2"] / 1e4).round(4)
    for c in ("floor_m", "spill_m", "depth_m"):
        sdf[c] = sdf[c].round(3)
    # Nearest well to each slack, recorded rather than thresholded.
    #
    # POLYGONISE ONLY WHAT IS USED. The tree keeps thousands of slacks, most of
    # them a handful of cells, and vectorising every one then dissolving was the
    # step that would not finish. Polygons are built for slacks in the warren at
    # or above POLY_MIN_AREA_M2; the CSV keeps them all, so nothing is lost that
    # a later step cannot recover.
    from shapely.geometry import Point                       # noqa: PLC0415
    keep_ids = set(sdf.loc[sdf["in_warren"], "slack"])
    info(f"polygonising {len(keep_ids)} slack(s) that touch the warren; "
         f"the CSV keeps all {len(sdf)}")
    keep_arr = np.zeros(len(nodes) + 1, dtype=bool)
    for k in keep_ids:
        keep_arr[k] = True
    poly_lab = np.where(keep_arr[lab], lab, 0).astype("int32")
    polys0, ids0 = [], []
    for geom, val in shapes(poly_lab, mask=(poly_lab > 0), transform=tr):
        polys0.append(shapely_shape(geom))
        ids0.append(int(val))
    sg0 = gpd.GeoDataFrame({"slack": ids0}, geometry=polys0, crs=OSGB)
    sg0 = sg0.dissolve(by="slack", as_index=False)

    # CLIP TO READABLE GROUND, and drop what no longer qualifies (Martin,
    # 2026-09-11: "exclude the lake and the shore"). Two independent failure
    # modes, each catching what the other misses:
    #   * LLYN RHOS-DDU is permanent open water, not a flooded slack. It came
    #     through as a 5.41 ha depression, floor 7.28 m. Counting it as a true
    #     positive is the error that keeping the lake gauge out of the 88
    #     dipwells exists to prevent.
    #   * THE SHORE. Eighteen "slacks" sat below 1 m AOD, 7.4 ha, including a
    #     4.96 ha striped feature at -1.52 m — wet intertidal sand in the LiDAR.
    #     They survived because a depression only had to TOUCH the warren.
    # Clipping strictly to the warren and subtracting the lake removes both
    # without an elevation threshold to argue about.
    from utils.config import SLACK_LAKE_OVERLAP_FRAC, SLACK_MIN_FLOOR_M
    lake = _features("Llyn Rhos Ddu")
    before_n, before_ha = len(sg0), sg0.area.sum() / 1e4
    sg0["geometry"] = sg0.geometry.intersection(w_ref)
    sg0 = sg0[~sg0.geometry.is_empty].copy()
    n_clip = len(sg0)
    # The lake, by overlap fraction rather than subtraction.
    frac = sg0.geometry.intersection(lake).area / lake.area
    is_lake = frac.fillna(0) >= SLACK_LAKE_OVERLAP_FRAC
    sg0 = sg0[~is_lake]
    n_lake = int(is_lake.sum())
    # The shore, by floor elevation.
    floors = dict(zip(sdf["slack"], sdf["floor_m"]))
    on_shore = sg0["slack"].map(floors) < SLACK_MIN_FLOOR_M
    sg0 = sg0[~on_shore]
    n_shore = int(on_shore.sum())
    sg0 = sg0[sg0.area >= SLACK_MIN_AREA_M2].copy()
    info(f"clipped to the warren: {before_n} -> {n_clip}; "
         f"lake removed {n_lake}; shore (floor < {SLACK_MIN_FLOOR_M} m) removed "
         f"{n_shore}; {len(sg0)} slack(s) remain, "
         f"{before_ha:.1f} -> {sg0.area.sum() / 1e4:.1f} ha")
    # THE HOLLOW IS NOT THE SLACK, and conflating them is what put a ridge
    # inside a mapped "slack" near CEH32 (Martin, 2026-09-11). `sg0` is the
    # node's extent - everything that drains to the floor, up to the spill - so
    # it answers "which depression does this belong to". It does NOT answer
    # "what is under water", because the node is drawn to its spill while the
    # criterion is a depth. The wet surface is the cells at or below
    # floor + SLACK_MIN_DEPTH_M, and it is a different polygon: at the CEH32
    # node, 0.01 ha of 5.60. Both are emitted, named differently, and the maps
    # and the scoring each take the one they mean.
    floor_lut = np.zeros(len(nodes) + 1, dtype="float64")
    floor_lut[:] = np.inf
    for _k, _f in zip(sdf["slack"], sdf["floor_m"]):
        floor_lut[int(_k)] = float(_f)
    wet_cells = (lab > 0) & (arr <= floor_lut[lab] + SLACK_MIN_DEPTH_M)
    wet_lab = np.where(wet_cells & keep_arr[lab], lab, 0).astype("int32")
    wpolys, wids = [], []
    for geom, val in shapes(wet_lab, mask=(wet_lab > 0), transform=tr):
        wpolys.append(shapely_shape(geom))
        wids.append(int(val))
    sw0 = gpd.GeoDataFrame({"slack": wids}, geometry=wpolys, crs=OSGB)
    sw0 = sw0.dissolve(by="slack", as_index=False)
    sw0["geometry"] = sw0.geometry.intersection(w_ref)
    sw0 = sw0[~sw0.geometry.is_empty].copy()
    sw0 = sw0[sw0["slack"].isin(set(sg0["slack"]))].copy()
    _wet = dict(zip(sw0["slack"], sw0.area))
    sdf["wet_area_m2"] = sdf["slack"].map(_wet)
    sdf["wet_area_ha"] = (sdf["wet_area_m2"] / 1e4).round(4)
    _hol = dict(zip(sg0["slack"], sg0.area))
    sdf["wet_frac"] = (sdf["slack"].map(_wet)
                       / sdf["slack"].map(_hol)).round(3)
    _hw, _ww = sg0.area.sum() / 1e4, sw0.area.sum() / 1e4
    step(f"hollows {len(sg0)}, {_hw:.1f} ha drawn to their spill; "
         f"WET at floor + {SLACK_MIN_DEPTH_M * 100:.0f} cm, {_ww:.1f} ha "
         f"({100 * _ww / _hw:.1f} % of the drawn area) across {len(sw0)} "
         f"slack(s). THE SECOND NUMBER IS THE ONE THAT FLOODS.")

    # The clipped area is the one that counts, so it replaces the tree's.
    clipped = dict(zip(sg0["slack"], (sg0.area / 1e4).round(4)))
    sdf["area_ha_clipped"] = sdf["slack"].map(clipped)
    sdf["readable"] = sdf["slack"].isin(set(sg0["slack"]))
    wpts = gpd.GeoDataFrame(
        {"well": wells["Name"].astype(str)},
        geometry=[Point(x, y) for x, y in zip(wells["E"], wells["N"])], crs=OSGB)
    near = gpd.sjoin_nearest(sg0, wpts, how="left", distance_col="nearest_well_m")
    near = (near.sort_values("nearest_well_m")
                .drop_duplicates("slack")[["slack", "well", "nearest_well_m"]]
                .rename(columns={"well": "nearest_well"}))
    near["nearest_well_m"] = near["nearest_well_m"].round(1)
    sdf = sdf.merge(near, on="slack", how="left")

    p = OUT / "W94_06_slacks.csv"
    sdf.sort_values("area_m2", ascending=False).to_csv(p, index=False)
    saved(p.name)

    inw = sdf[sdf["in_warren"]]
    step(f"{len(inw)} slack(s) in the warren at or above {SLACK_MIN_AREA_M2:.0f} m2")
    for cut in (500.0, 1000.0, 5000.0):
        c = inw[inw["area_m2"] >= cut]
        if len(c):
            info(f"  >= {cut:6.0f} m2 : {len(c):4d} slack(s), median "
                 f"{c['area_ha'].median():.3f} ha, "
                 f"{int(c['wells_inside'].astype(bool).sum()):3d} contain a well")
    _nw = sdf.loc[sdf["readable"], "nearest_well_m"].dropna()
    info(f"HOW MANY ARE UNGAUGED DEPENDS ON THE ATTACHMENT RULE, which is not "
         f"decided here: of {len(wells)} wells, "
         f"{int(sdf['wells_inside'].astype(bool).sum())} readable slack(s) "
         f"contain one; slack-to-nearest-well is "
         f"{(_nw <= 0).sum()} at 0 m, {(_nw <= 20).sum()} within 20 m and "
         f"{(_nw <= 50).sum()} within 50 m of {len(_nw)}. Wells were sited at "
         f"slack EDGES, so `nearest_well_m` is written per slack and the cut is "
         f"made later, in the open.")
    info(f"for comparison the Ranwell prototype basins run "
         f"{bdf['area_ha'].min():.1f} to {bdf['area_ha'].max():.1f} ha — "
         f"catchment scale, which is why they are not the scoring unit")
    info("AREA IS NOT FILTERED BY WHAT A FRAME CAN SEE. The slack map is a "
         "property of the ground; CANOPY_FLOOD_MIN_PATCH_PX is applied per "
         "frame at scoring time, so the ground truth does not depend on which "
         "photographs happen to exist.")

    _attrs = ["slack", "area_ha", "floor_m", "spill_m", "depth_m",
              "in_warren", "readable", "area_ha_clipped", "wet_area_ha",
              "wet_frac", "wells_inside", "wells_wet_at_m", "nearest_well",
              "nearest_well_m"]
    # THE HOLLOW — the node extent, floor to spill. The ATTRIBUTION unit: which
    # depression a flood body belongs to. Never an area that floods.
    sh = sg0.merge(sdf[_attrs], on="slack", how="left")
    # THE SLACK — the surface at floor + SLACK_MIN_DEPTH_M. The WET area: what a
    # photograph is compared with, and what is recognised on the ground.
    sg = sw0.merge(sdf[_attrs], on="slack", how="left")
    for _name, _gdf, _stem in (("hollows", sh, "W94_06_hollows"),
                               ("slacks", sg, "W94_06_slacks")):
        q = OUT / f"{_stem}.geojson"
        q.write_text(_gdf.to_json(), encoding="utf-8")
        saved(q.name)
        tmp = Path(tempfile.mkdtemp()) / f"{_name}.kml"
        _gdf.to_crs("EPSG:4326").to_file(tmp, driver="KML")
        q = OUT / f"{_stem}.kml"
        q.write_bytes(tmp.read_bytes())
        shutil.rmtree(tmp.parent, ignore_errors=True)
        saved(q.name)

    phase(7, "Map — the slacks, for recognition on the ground")
    fig2, ax2 = plt.subplots(figsize=(11.5, 9.8))
    load_dem_hillshade(ax2, DATA_GEO_DIR, alpha=0.6)
    gpd.GeoSeries([w_ref], crs=OSGB).plot(ax=ax2, facecolor="none",
                                          edgecolor="#08519c", lw=1.0, zorder=3)
    # The hollow is drawn as an OUTLINE and the wet surface as the fill, so the
    # difference between them is visible on the map rather than collapsed into
    # one blue polygon — the collapse that made a ridge read as slack.
    sh.plot(ax=ax2, facecolor="none", edgecolor="#6baed6", lw=0.4, zorder=3.5)
    sg.plot(ax=ax2, facecolor="#2171b5", edgecolor="#08306b", lw=0.35,
            alpha=0.85, zorder=4)
    wpts.plot(ax=ax2, color="#d94801", markersize=8, zorder=5)
    joined = gpd.sjoin(wpts, sh[["slack", "geometry"]], how="inner",
                       predicate="within")
    for _, r in joined.iterrows():
        ax2.annotate(r["well"], (r.geometry.x, r.geometry.y), fontsize=6,
                     xytext=(3, 3), textcoords="offset points", zorder=6,
                     color="#7f2704")
    sg_area = sh.assign(ha=sh.area / 1e4)
    for _, r in sg_area.nlargest(14, "ha").iterrows():
        c = r.geometry.representative_point()
        ax2.annotate(f"{r['ha']:.1f} ha", (c.x, c.y), fontsize=6, ha="center",
                     va="center", zorder=7, color="white")
    ax2.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
    ax2.set_ylim(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)
    add_en_axes(ax2, apply_extent=False)
    ax2.set_title(
        f"W94 — slacks in the warren: WET area under "
        f"{SLACK_MIN_DEPTH_M * 100:.0f} cm of water (solid), inside the hollow "
        f"that holds it (outline)\n{len(sh)} hollows, "
        f"{sh.area.sum() / 1e4:.0f} ha drawn to their spill; wet "
        f"{sg.area.sum() / 1e4:.1f} ha; lake and shore excluded; wells orange, "
        f"hollows labelled by their own area")
    p = OUT / "W94_07_slacks.png"
    render_figure(fig2, p)
    saved(p.name)

    info("the repeat-floor drift test is NOT run here — it needs digitised "
         "outlines on two dates, which do not exist yet. See the module "
         "docstring.")
    return 0


def _vp2_transform():
    """The vp2 homography, cached as CONTROL POINTS rather than as a function.

    Registration costs about two minutes — `_register_all` detects markers on
    every registration frame in the manifest — and phase 8 needs it on every
    run. The cache is `W94_08_vp2_control.csv`: the well positions and their
    fitted pixel coordinates, from which `_homography` refits the same eight
    parameters exactly (measured: 2.4e-10 px maximum disagreement). A table of
    correspondences is auditable in a way a pickled closure is not, and it is
    the evidence for the fit rather than the fit itself.

    ONE TRANSFORM SERVES EVERY vp2 FRAME. Measured 2026-09-11: phase-correlating
    every vp2 frame against `site24-3-2021.png` returns (0, 0) px with the peak
    200-430x the noise sd, and the markers-ON twin returns r = 0.9954. That is
    what lets 2010-05-27 — the only measurement frame with no twin, and a May
    negative — be read at all.
    """
    import importlib.util                                    # noqa: PLC0415
    from shapely.ops import unary_union                      # noqa: PLC0415
    from utils.kml_io import read_kml                        # noqa: PLC0415
    from utils.paths import INT_LOCATIONS                    # noqa: PLC0415

    spec = importlib.util.spec_from_file_location(
        "m41", str(REPO / "src" / "41_canopy_cover.py"))
    m41 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m41)

    cache = OUT / "W94_08_vp2_control.csv"
    if cache.exists():
        c = pd.read_csv(cache, float_precision="round_trip")
        info(f"vp2 transform from {cache.name} ({len(c)} control point(s))")
    else:
        info("no cached vp2 transform; registering — about two minutes")
        ctrl = unary_union(list(
            read_kml(DATA_GEO_DIR / f"{m41.CONTROL_KML}.kml").geometry))
        w = pd.read_csv(INT_LOCATIONS, float_precision="round_trip")
        ec = next(x for x in w.columns if x.lower() in ("easting", "e", "x"))
        nc = next(x for x in w.columns if x.lower() in ("northing", "n", "y"))
        E = w[ec].values.astype(float)
        N = w[nc].values.astype(float)
        man = pd.read_csv(MANIFEST, float_precision="round_trip")
        man = man[man["role"] == "registration"]
        paths = [m41.AERIAL_DIR / f for f in man["filename"]
                 if (m41.AERIAL_DIR / f).exists()]
        reg, _ = m41._register_all(paths, ctrl, E, N)
        r = reg.get(VP2_REFERENCE_FRAME)
        if r is None or r.get("fitted") is None:
            warn(f"{VP2_REFERENCE_FRAME} did not register; phase 8 cannot run")
            return None, m41
        px, py = r["fitted"](E, N)
        c = pd.DataFrame({"E": E, "N": N, "px": px, "py": py})
        c.to_csv(cache, index=False)
        saved(cache.name)
    P = np.column_stack([c["E"].values, c["N"].values,
                         c["px"].values, c["py"].values])
    H = m41._homography(P)
    u, v = H(P[:, 0], P[:, 1])
    err = float(np.max(np.hypot(u - P[:, 2], v - P[:, 3])))
    info(f"refit reproduces the cached control points to {err:.2e} px")
    return H, m41


def _otsu(x):
    """(threshold, between-class variance as a fraction of the total).

    The FRACTION is the point. Otsu's threshold always exists; the fraction says
    whether the histogram it split was two populations or one.
    """
    x = x[np.isfinite(x)]
    if x.size < 100:
        return float("nan"), 0.0
    lo, hi = np.percentile(x, [0.5, 99.5])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return float("nan"), 0.0
    hist, edges = np.histogram(np.clip(x, lo, hi), bins=256, range=(lo, hi))
    p = hist.astype(float) / max(hist.sum(), 1)
    mids = 0.5 * (edges[1:] + edges[:-1])
    w0 = np.cumsum(p)
    m0 = np.cumsum(p * mids)
    mt = m0[-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        between = (mt * w0 - m0) ** 2 / (w0 * (1.0 - w0))
    between = np.where(np.isfinite(between), between, 0.0)
    k = int(np.argmax(between))
    total = float(np.sum(p * (mids - mt) ** 2))
    return float(mids[k]), (float(between[k] / total) if total > 0 else 0.0)


def phase8(dates=None, calibrate=False) -> int:
    """The flood read: the photographs classify, the DEM names the result."""
    from rasterio.features import geometry_mask, shapes      # noqa: PLC0415
    from rasterio.transform import from_origin                # noqa: PLC0415
    from scipy import ndimage as ndi                         # noqa: PLC0415
    from shapely.geometry import shape as shapely_shape      # noqa: PLC0415
    from PIL import Image                                    # noqa: PLC0415

    from utils.config import (CANOPY_CHANGE_GRID_M,          # noqa: PLC0415
                              CANOPY_FLOOD_MIN_PATCH_PX,
                              FLOOD_NEAR_GROUND_M, FLOOD_OTSU_MAX_Z)

    phase(8, "The flood read — the photographs classify, the DEM names")
    hol_p = OUT / "W94_06_hollows.geojson"
    if not hol_p.exists():
        warn("phase 6 has not run: W94_06_hollows.geojson is missing")
        return 1
    hollows = gpd.read_file(hol_p).set_crs(OSGB, allow_override=True)
    info(f"{len(hollows)} hollow(s) from phase 6, "
         f"{hollows.area.sum() / 1e4:.1f} ha")

    man = pd.read_csv(MANIFEST, float_precision="round_trip")
    meas = man[(man["viewpoint"].astype(str).str.startswith("vp2"))
               & (man["role"] == "measurement")].copy()
    if dates:
        meas = meas[meas["imagery_date"].isin(dates)]
    meas = meas.sort_values("imagery_date")
    if not len(meas):
        warn("no vp2 measurement frame matches; nothing to read")
        return 1
    info(f"{len(meas)} frame(s) to read: "
         f"{', '.join(meas['imagery_date'].astype(str))}")

    H, m41 = _vp2_transform()
    if H is None:
        return 1

    # THE FRAME'S OWN GEOMETRY, from the COMMITTED registration rather than
    # typed here: `gsd_m` converts the patch-size threshold from image pixels to
    # ground, and `residual_median_m` is how well the frame can localise a well
    # at all. Both are properties of the fit Script 41 published, so neither is
    # a number this tool is free to choose.
    rg = pd.read_csv(REPO / "outputs" / "41_canopy_cover" / "41_03_registration.csv",
                     float_precision="round_trip")
    rg = rg[rg["frame"] == VP2_REFERENCE_FRAME]
    if not len(rg):
        warn(f"{VP2_REFERENCE_FRAME} is not in the committed registration")
        return 1
    gsd = float(rg["gsd_m"].iloc[0])
    resid = float(rg["residual_median_m"].iloc[0])
    info(f"vp2 registration: {gsd:.3f} m/px, median residual {resid:.2f} m "
         f"(from 41_03_registration.csv)")

    # THE GROUND GRID. Luminance is compared on the ground, never in pixel
    # space: the frames differ in viewpoint, so a pixel difference measures the
    # perspective rather than the ground.
    res = float(CANOPY_CHANGE_GRID_M)
    minx, miny, maxx, maxy = hollows.total_bounds
    minx, miny = np.floor(minx / res) * res - 200.0, np.floor(miny / res) * res - 200.0
    maxx, maxy = np.ceil(maxx / res) * res + 200.0, np.ceil(maxy / res) * res + 200.0
    ge = np.arange(minx, maxx + res, res)
    gn = np.arange(maxy, miny - res, -res)
    EE, NN = np.meshgrid(ge, gn)
    gtr = from_origin(minx - res / 2, maxy + res / 2, res, res)
    info(f"ground grid {EE.shape[1]} x {EE.shape[0]} at {res:.0f} m")

    # THE DEM ON THE SAME GRID. Used for two things only, both of which are
    # relative and so immune to the +0.22 m offset the raster carries: the 1 m
    # elevation band that splits welded water bodies, and nothing else.
    with rasterio.open(DATA_DEM) as ds:
        dem = np.array(list(ds.sample(
            np.column_stack([EE.ravel(), NN.ravel()])))).astype(float)[:, 0]
        nod = ds.nodata
    if nod is not None:
        dem[dem == nod] = np.nan
    dem = dem.reshape(EE.shape)

    hol_mask = geometry_mask(list(hollows.geometry), out_shape=EE.shape,
                             transform=gtr, invert=True)
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    lev = pd.read_csv(REPO / "outputs" / "01_wells_clean.csv",
                      float_precision="round_trip")
    lev = lev.rename(columns={lev.columns[0]: "month"})
    lev["month"] = pd.to_datetime(lev["month"])

    rows, calib = [], []
    for _, fr in meas.iterrows():
        date = str(fr["imagery_date"])
        frame = str(fr["filename"])
        step(f"{date} — {frame}")
        fp = m41.AERIAL_DIR / frame
        if not fp.exists():
            rows.append({"date": date, "frame": frame, "verdict": "SKIPPED",
                         "reason": "frame not on disk"})
            warn("  frame not on disk")
            continue
        a = np.asarray(Image.open(fp).convert("RGB")).astype(float)
        lum = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]
        grid, ok = m41._sample_to_grid(lum, H, EE, NN)

        # THE MASK IS DATE-DEPENDENT. `warren_on` subtracts the canopy as at
        # this date, so a block that had closed by now is not read as ground.
        wmask = geometry_mask([warren_on(date)], out_shape=EE.shape,
                              transform=gtr, invert=True)
        usable = wmask & ok & np.isfinite(grid) & np.isfinite(dem)
        if usable.sum() < 1000:
            rows.append({"date": date, "frame": frame, "verdict": "SKIPPED",
                         "reason": "the warren is barely in this frame's window"})
            warn("  the warren is barely inside this frame's usable window")
            continue

        # NORMALISE AGAINST THIS FRAME'S OWN OPEN DUNE — the warren less the
        # mapped hollows, which by construction never floods. Robust, because a
        # few genuinely dark cells in it must not move the reference.
        dune = usable & ~hol_mask
        ref = grid[dune]
        med = float(np.median(ref))
        mad = float(np.median(np.abs(ref - med)))
        sigma = 1.4826 * mad if mad > 0 else float("nan")
        if not np.isfinite(sigma) or sigma <= 0:
            rows.append({"date": date, "frame": frame, "verdict": "SKIPPED",
                         "reason": "the open-dune reference has no spread"})
            warn("  the open-dune reference has no spread")
            continue
        z = (grid - med) / sigma
        info(f"  open dune: median {med:.1f}, MAD {mad:.1f} over "
             f"{int(dune.sum())} cell(s); {int(usable.sum())} usable")

        # THE CUT IS THIS FRAME'S OWN OTSU THRESHOLD, and the GATE is where that
        # threshold falls. A dry frame fails here on its own evidence rather
        # than being argued away afterwards: Otsu always returns a threshold,
        # but on a dry frame it splits bright from brighter, at or above the
        # dune median, because there is no dark population to find.
        thr, frac = _otsu(z[usable])
        info(f"  Otsu on z: threshold {thr:.2f} (gate {FLOOD_OTSU_MAX_Z}), "
             f"between-class variance {frac:.3f} of total (diagnostic only)")

        if calibrate:
            wl = _well_levels(lev, wells, date)
            for _, wr in wl.iterrows():
                c, r0 = ~gtr * (wr["E"], wr["N"])
                c, r0 = int(c), int(r0)
                if 0 <= r0 < z.shape[0] and 0 <= c < z.shape[1] and usable[r0, c]:
                    calib.append({"date": date, "well": wr["well"],
                                  "h_m": wr["h_m"], "wet_truth": wr["h_m"] >= 0,
                                  "lum": float(grid[r0, c]),
                                  "z": float(z[r0, c]),
                                  "otsu_z": thr, "bimodal_frac": frac})
            continue

        if not np.isfinite(thr) or thr > FLOOD_OTSU_MAX_Z:
            rows.append({"date": date, "frame": frame, "n_bodies": 0,
                         "flood_ha": 0.0, "otsu_z": round(float(thr), 4),
                         "bimodal_frac": round(frac, 4), "verdict": "DRY",
                         "reason": f"the frame's own split falls at "
                                   f"{thr:.2f}, above {FLOOD_OTSU_MAX_Z} — no "
                                   f"dark population"})
            step("  DRY — the frame's own split is not on the dark side of its "
                 "own dune; no cut applied")
            continue

        wet = usable & (z <= thr)
        # A WATER BODY IS LEVEL, and that is a filter. Labelling flood cells in
        # plan alone welded 45.7 ha across 13.4 m of relief — slacks joined by
        # dark threads over the ridges between them. Labelling within 1 m
        # elevation bands splits them without cutting genuine water in half,
        # which tighter bands do (D-159).
        band = np.floor(np.where(np.isfinite(dem), dem, 0.0)).astype(int)
        lab = np.zeros(wet.shape, dtype=np.int32)
        nxt = 0
        for b in np.unique(band[wet]):
            m_ = wet & (band == b)
            ll, nn_ = ndi.label(m_)
            ll[ll > 0] += nxt
            lab = np.where(m_, ll, lab)
            nxt += nn_
        if nxt:
            # CANOPY_FLOOD_MIN_PATCH_PX IS IN IMAGE PIXELS at the frame's own
            # GSD — that is how config.py derives it — and the labelling here is
            # on the 2 m GROUND grid. Comparing the two directly applied a
            # threshold two-fifths of the documented size.
            min_cells = int(round(CANOPY_FLOOD_MIN_PATCH_PX * gsd * gsd
                                  / (res * res)))
            counts = np.bincount(lab.ravel())
            small = np.flatnonzero(counts < min_cells)
            drop = np.zeros(counts.size, bool)
            drop[small] = True
            drop[0] = True
            lab = np.where(drop[lab], 0, lab)
        n_bodies = int(len(np.unique(lab)) - 1)
        polys, ids = [], []
        for geom, val in shapes(lab, mask=(lab > 0), transform=gtr):
            polys.append(shapely_shape(geom))
            ids.append(int(val))
        if not polys:
            rows.append({"date": date, "frame": frame, "n_bodies": 0,
                         "flood_ha": 0.0, "otsu_z": round(float(thr), 4),
                         "bimodal_frac": round(frac, 4),
                         "verdict": "READ", "reason": "no body survived the "
                                                      "minimum patch size"})
            step("  no body survived the minimum patch size")
            continue
        fg = gpd.GeoDataFrame({"body_id": ids}, geometry=polys, crs=OSGB)
        fg = fg.dissolve(by="body_id", as_index=False)
        fg["area_m2"] = fg.area.round(1)
        fg["elev_band_m"] = [int(np.floor(np.nanmedian(dem[lab == i])))
                             for i in fg["body_id"]]
        fg["median_z"] = [round(float(np.nanmedian(z[lab == i])), 3)
                          for i in fg["body_id"]]
        # ATTRIBUTION, not delineation: the hollow NAMES the body. The DEM does
        # not decide where water is allowed to be (D-159's inversion).
        j = gpd.sjoin(fg[["body_id", "geometry"]], hollows[["slack", "geometry"]],
                      how="left", predicate="intersects")
        j = j.drop_duplicates("body_id")[["body_id", "slack"]]
        fg = fg.merge(j, on="body_id", how="left")
        fg["slack"] = fg["slack"].astype("Int64")

        sc = _score(fg, lev, wells, date, gtr, usable, FLOOD_NEAR_GROUND_M,
                    resid)
        _flood_map(date, frame, fg, hollows, sc, thr)
        if len(sc["per_well"]):
            p = OUT / f"W94_08_wells_{date}.csv"
            sc["per_well"].to_csv(p, index=False)
            saved(p.name)
        else:
            # NO FILE RATHER THAN AN EMPTY ONE. A zero-row frame wrote a
            # headerless CSV that every later reader choked on; 2026-03-31 has
            # no dipwell month at all, the record ending at
            # REFERENCE_CUTOFF_DATE, and that is a fact to state, not a file.
            warn(f"  no dipwell month for {date}: the read cannot be scored")
        for stem, gdf in ((f"W94_08_flood_{date}", fg),):
            q = OUT / f"{stem}.geojson"
            q.write_text(gdf.to_json(), encoding="utf-8")
            saved(q.name)
            tmp = Path(tempfile.mkdtemp()) / "flood.kml"
            gdf.to_crs("EPSG:4326").to_file(tmp, driver="KML")
            q = OUT / f"{stem}.kml"
            q.write_bytes(tmp.read_bytes())
            shutil.rmtree(tmp.parent, ignore_errors=True)
            saved(q.name)
        row = {"date": date, "frame": frame, "transform_source": "vp2 (shared)",
               "n_bodies": n_bodies, "flood_ha": round(fg.area.sum() / 1e4, 3),
               "otsu_z": round(float(thr), 4),
               "bimodal_frac": round(frac, 4), "verdict": "READ", "reason": ""}
        row.update(sc["summary"])
        rows.append(row)
        step(f"  {n_bodies} body(ies), {fg.area.sum() / 1e4:.2f} ha; "
             f"recall {sc['summary']['recall']}, "
             f"precision {sc['summary']['precision']}, "
             f"agreement {sc['summary']['agreement']} at "
             f"{sc['summary']['n_wells']} wells")

    if calibrate:
        if not calib:
            warn("no calibration rows — no well fell in a usable cell")
            return 1
        cdf = pd.DataFrame(calib)
        # MERGE BY DATE, never overwrite. Calibration is built up one frame at a
        # time — the wet frame sets the cut, the record's dry frames set the
        # gate — and a run that replaced the file lost the frame before it.
        p = OUT / "W94_08_calibration.csv"
        if p.exists():
            prev = pd.read_csv(p, float_precision="round_trip")
            prev = prev[~prev["date"].isin(cdf["date"].unique())]
            cdf = pd.concat([prev, cdf], ignore_index=True)
        cdf = cdf.sort_values(["date", "well"])
        cdf.to_csv(p, index=False)
        saved(p.name)
        for d, g in cdf.groupby("date"):
            wet_, dry_ = g[g.wet_truth], g[~g.wet_truth]
            info(f"  {d}: {len(wet_)} wet / {len(dry_)} dry wells; "
                 f"z median wet "
                 f"{(wet_['z'].median() if len(wet_) else float('nan')):.2f}, "
                 f"dry {(dry_['z'].median() if len(dry_) else float('nan')):.2f}; "
                 f"bimodal {g['bimodal_frac'].iloc[0]:.3f}")
        info("FREEZE FLOOD_LUM_Z between the two medians and FLOOD_BIMODAL_MIN "
             "below the calibration frame's fraction, in config.py, then run "
             "without --calibrate.")
        return 0

    sdf = pd.DataFrame(rows)
    p = OUT / "W94_09_scores.csv"
    sdf.to_csv(p, index=False)
    saved(p.name)
    return 0


def _flood_map(date, frame, fg, hollows, sc, thr):
    """The read, on the ground: water solid, hollows outlined, wells scored.

    The map is where a false positive stops being a number and becomes a place —
    which is how the CEH32 ridge was found, and how the estuary patch was.
    """
    import matplotlib.pyplot as plt                          # noqa: PLC0415
    from utils.config import (SITE_MAP_EAST_MAX,             # noqa: PLC0415
                              SITE_MAP_EAST_MIN, SITE_MAP_NORTH_MAX,
                              SITE_MAP_NORTH_MIN)
    from utils.map_utils import add_en_axes, load_dem_hillshade  # noqa: PLC0415
    from utils.render_utils import render_figure             # noqa: PLC0415
    from shapely.geometry import Point                       # noqa: PLC0415

    fig, ax = plt.subplots(figsize=(11.5, 9.8))
    load_dem_hillshade(ax, DATA_GEO_DIR, alpha=0.6)
    gpd.GeoSeries([warren_on(date)], crs=OSGB).plot(
        ax=ax, facecolor="none", edgecolor="#08519c", lw=1.0, zorder=3)
    hollows.plot(ax=ax, facecolor="none", edgecolor="#bdd7e7", lw=0.3,
                 zorder=3.5)
    fg.plot(ax=ax, facecolor="#2171b5", edgecolor="#08306b", lw=0.3,
            alpha=0.85, zorder=4)
    per = sc["per_well"]
    if len(per):
        el = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                         float_precision="round_trip")
        en = {str(n).lower(): (x, y) for n, x, y in
              zip(el["Name"], el["E"], el["N"])}
        # FOUR OUTCOMES, four colours. An agreement figure hides WHERE it
        # disagrees, and the where is the evidence.
        style = {(True, True): ("#238b45", "o", "wet, found"),
                 (True, False): ("#cb181d", "v", "wet, missed"),
                 (False, True): ("#fd8d3c", "^", "dry, called wet"),
                 (False, False): ("#737373", ".", "dry, agreed")}
        for key, (col, mk, lab) in style.items():
            sel = per[(per["wet_truth"] == key[0]) & (per["wet_pred"] == key[1])]
            pts = [en.get(str(w).lower()) for w in sel["well"]]
            pts = [q for q in pts if q is not None]
            if not pts:
                continue
            gpd.GeoSeries([Point(*q) for q in pts], crs=OSGB).plot(
                ax=ax, color=col, marker=mk, markersize=26, zorder=5,
                label=f"{lab} ({len(pts)})")
        for _, r in per[per["wet_truth"] != per["wet_pred"]].iterrows():
            q = en.get(str(r["well"]).lower())
            if q:
                ax.annotate(str(r["well"]), q, fontsize=7, xytext=(4, 4),
                            textcoords="offset points", zorder=6)
        ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    ax.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
    ax.set_ylim(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)
    add_en_axes(ax, apply_extent=False)
    sm = sc["summary"]
    ax.set_title(
        f"W94 — flood read from {frame}, {date}\n"
        f"{len(fg)} water bod(ies), {fg.area.sum() / 1e4:.1f} ha; cut at this "
        f"frame's own Otsu z = {thr:.2f} against its open dune; "
        f"recall {sm['recall']}, precision {sm['precision']} "
        f"(a LOWER bound — edge-sited wells) at {sm['n_wells']} wells")
    q = OUT / f"W94_08_flood_{date}.png"
    render_figure(fig, q)
    saved(q.name)


def _well_levels(lev, wells, date):
    """Wells reporting in the frame's month, with their level.

    BUCKETING IS SCRIPT 01's, not a new convention: a reading on day > 15
    belongs to the same month, day <= 15 to the previous. So 2021-03-24 is
    March 2021, and the frame is compared with the level for the month it
    falls in.
    """
    d = pd.Timestamp(date)
    month = (d - pd.offsets.MonthBegin(1)) if d.day <= 15 else d
    key = pd.Timestamp(month.year, month.month, 1)
    row = lev[lev["month"] == key]
    out = []
    if not len(row):
        return pd.DataFrame(columns=["well", "h_m", "E", "N"])
    row = row.iloc[0]
    byname = {str(n).lower(): (e, nn) for n, e, nn
              in zip(wells["Name"], wells["E"], wells["N"])}
    for c in lev.columns:
        if c == "month":
            continue
        v = pd.to_numeric(pd.Series([row[c]]), errors="coerce").iloc[0]
        if pd.isna(v):
            continue
        en = byname.get(str(c).lower())
        if en is None:
            continue
        out.append({"well": c, "h_m": float(v), "E": en[0], "N": en[1]})
    return pd.DataFrame(out)


def _score(fg, lev, wells, date, gtr, usable, near_m, tol_m):
    """Score the flood bodies against the dipwell record for that month.

    PRECISION IS A LOWER BOUND AND RECALL IS NOT. Wells were sited at slack
    EDGES for ease of measurement (Martin, 2026-09-10; CEH1, CEH9 and NW6
    named), so a well can read below ground while its slack is flooded, and
    every such well scores as a FALSE POSITIVE when the method is right. Delta,
    which would correct it, is not known. The near-ground band is reported
    separately so the size of the effect is visible rather than asserted.
    """
    from shapely.geometry import Point                       # noqa: PLC0415
    wl = _well_levels(lev, wells, date)
    if not len(wl):
        return {"per_well": pd.DataFrame(),
                "summary": {"n_wells": 0, "recall": None, "precision": None,
                            "agreement": None, "tp": 0, "fp": 0, "fn": 0,
                            "tn": 0}}
    pts = gpd.GeoDataFrame(
        wl, geometry=[Point(x, y) for x, y in zip(wl["E"], wl["N"])], crs=OSGB)
    keep = []
    for _, r in pts.iterrows():
        c, r0 = ~gtr * (r["E"], r["N"])
        c, r0 = int(c), int(r0)
        keep.append(0 <= r0 < usable.shape[0] and 0 <= c < usable.shape[1]
                    and bool(usable[r0, c]))
    pts = pts[pd.Series(keep, index=pts.index)].copy()
    if not len(pts):
        return {"per_well": pd.DataFrame(),
                "summary": {"n_wells": 0, "recall": None, "precision": None,
                            "agreement": None, "tp": 0, "fp": 0, "fn": 0,
                            "tn": 0}}
    # A WELL IS NOT LOCALISED TO A POINT IN THIS FRAME. `tol_m` is the
    # registration's OWN median residual against the 88 surveyed positions, read
    # from the committed 41_03 — the frame cannot place a well better than that,
    # so a boundary drawn finer than it is spurious precision. It is not a
    # tuning knob: measured 2026-09-11, eleven of eleven false negatives at
    # strict containment had water within 10.1 m and six within 3.8 m, which is
    # the waterline running through the pipe, not a classification error. The
    # value is whatever Script 41 published; this tool does not choose it.
    j = gpd.sjoin_nearest(pts, fg[["body_id", "slack", "geometry"]], how="left",
                          max_distance=tol_m, distance_col="body_dist_m")
    j = j.sort_values("body_dist_m").drop_duplicates(subset=["well"])
    j["wet_pred"] = j["body_id"].notna()
    j["wet_truth"] = j["h_m"] >= 0.0
    j["near_ground"] = j["h_m"].abs() <= near_m
    tp = int((j.wet_truth & j.wet_pred).sum())
    fp = int((~j.wet_truth & j.wet_pred).sum())
    fn = int((j.wet_truth & ~j.wet_pred).sum())
    tn = int((~j.wet_truth & ~j.wet_pred).sum())
    n = tp + fp + fn + tn
    per = j[["well", "h_m", "wet_truth", "wet_pred", "body_id", "slack",
             "body_dist_m", "near_ground"]].copy()
    per["body_dist_m"] = per["body_dist_m"].round(2)
    per["h_m"] = per["h_m"].round(3)
    return {"per_well": per.sort_values("well"),
            "summary": {
                "n_wells": n,
                "recall": round(tp / (tp + fn), 3) if (tp + fn) else None,
                "precision": round(tp / (tp + fp), 3) if (tp + fp) else None,
                "agreement": round((tp + tn) / n, 3) if n else None,
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                "fp_near_ground": int((~j.wet_truth & j.wet_pred
                                       & j.near_ground).sum())}}


if __name__ == "__main__":
    sys.exit(main())

