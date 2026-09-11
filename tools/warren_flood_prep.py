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

__version__ = "1.1.0"  # Hollingham (2026) - 2026-09-11. SLACKS, delineated from
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


def main() -> int:
    banner("W94 step 1 — the warren mask by frame date", __version__)

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

    sg = sg0.merge(
        sdf[["slack", "area_ha", "floor_m", "spill_m", "depth_m",
             "in_warren", "readable", "area_ha_clipped", "wells_inside",
             "wells_wet_at_m", "nearest_well", "nearest_well_m"]],
        on="slack", how="left")
    p = OUT / "W94_06_slacks.geojson"
    p.write_text(sg.to_json(), encoding="utf-8")
    saved(p.name)
    tmp = Path(tempfile.mkdtemp()) / "slacks.kml"
    sg.to_crs("EPSG:4326").to_file(tmp, driver="KML")
    p = OUT / "W94_06_slacks.kml"
    p.write_bytes(tmp.read_bytes())
    shutil.rmtree(tmp.parent, ignore_errors=True)
    saved(p.name)

    phase(7, "Map — the slacks, for recognition on the ground")
    fig2, ax2 = plt.subplots(figsize=(11.5, 9.8))
    load_dem_hillshade(ax2, DATA_GEO_DIR, alpha=0.6)
    gpd.GeoSeries([w_ref], crs=OSGB).plot(ax=ax2, facecolor="none",
                                          edgecolor="#08519c", lw=1.0, zorder=3)
    sg.plot(ax=ax2, facecolor="#2171b5", edgecolor="#08306b", lw=0.35,
            alpha=0.85, zorder=4)
    wpts.plot(ax=ax2, color="#d94801", markersize=8, zorder=5)
    joined = gpd.sjoin(wpts, sg[["slack", "geometry"]], how="inner",
                       predicate="within")
    for _, r in joined.iterrows():
        ax2.annotate(r["well"], (r.geometry.x, r.geometry.y), fontsize=6,
                     xytext=(3, 3), textcoords="offset points", zorder=6,
                     color="#7f2704")
    sg_area = sg.assign(ha=sg.area / 1e4)
    for _, r in sg_area.nlargest(14, "ha").iterrows():
        c = r.geometry.representative_point()
        ax2.annotate(f"{r['ha']:.1f} ha", (c.x, c.y), fontsize=6, ha="center",
                     va="center", zorder=7, color="white")
    ax2.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
    ax2.set_ylim(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)
    add_en_axes(ax2, apply_extent=False)
    ax2.set_title(
        f"W94 — slacks holding at least {SLACK_MIN_DEPTH_M * 100:.0f} cm, in the "
        f"warren\n{len(sg)} depressions, {sg.area.sum() / 1e4:.0f} ha; lake and "
        f"shore excluded; wells orange, largest slacks labelled")
    p = OUT / "W94_07_slacks.png"
    render_figure(fig2, p)
    saved(p.name)

    info("the repeat-floor drift test is NOT run here — it needs digitised "
         "outlines on two dates, which do not exist yet. See the module "
         "docstring.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
