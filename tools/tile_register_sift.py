#!/usr/bin/env python3
"""Register the 2026-09-12 tiles against the vp2 frames, by image features.

WHY NOT THE CONTROL NET. `georef_grid.kml` is 180 pins on an exact 200 m lattice,
and a lattice looks the same shifted by one step: measured 2026-09-12, all 25
candidate offsets for one tile returned **39 matched points at 0.57 px, identical
to two decimals**. The residual is blind to which offset is right, every tile
chose independently, and two tiles of one date ended up correlating at 0.02-0.09
where two captures of one surface must agree. Every tile-derived result of
2026-09-12 was void.

WHY NOT THE STATUS BAR. The plan after that was to break the tie with the frame
centre Google Earth prints. It prints the position under the POINTER: two of
Martin's captures of the same ground at the same altitude quote coordinates 1.7 km
apart (2026-09-13). Recorded so it is not tried again.

WHAT THIS DOES INSTEAD. The one registration this project has verified is the vp2
homography — its markers-ON/OFF twins, sampled to the ground grid through it,
agree at r = 0.994. So the tiles are tied to that and to no control net at all:
SIFT features on the tile and on a vp2 frame, ratio-test matching, a RANSAC
homography from tile pixels to vp2 pixels, composed with the vp2 ground
transform. Measured on 2021-03-24: 1044-1779 inliers per tile at scales of
0.33-0.51, which is the 1.0-1.5 m against 2.884 m ratio those frames should have.

AND EVERY FIT IS GATED ON AGREEMENT, NOT ON ITS OWN RESIDUAL. A fit is accepted
only where it agrees, on the ground, with another capture of the same place —
`TILE_AGREE_MIN_R`. That is the check whose absence let the lattice fits through:
a residual is a statement about the assignment you happened to make, and only a
second, independent capture can test it. One tile in four of the first trial
produced no overlap at all and is refused by this rule.

Usage:
    python3 tools/tile_register_sift.py                 # all dates, resumable
    python3 tools/tile_register_sift.py --date 2021-03-24
    python3 tools/tile_register_sift.py --report        # what the cache holds
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-13. New: feature-based
#   tile registration against the vp2 frames, replacing the ambiguous
#   lattice control net (D-159).

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
REPORT = OUT / "W159_sift_registration.csv"
TILE_DIR = REPO / "data" / "geo" / "slacks"
INVENTORY = OUT / "W159_registration_inventory.csv"
MANIFEST = REPO / "data" / "geo" / "aerial_manifest.csv"

SIFT_FEATURES = 20000
RATIO = 0.75                  # Lowe's ratio test, the standard value
RANSAC_PX = 5.0
MIN_INLIERS = 200
# The band exists to reject a match that is not of this scene at all, NOT to
# assert that every tile is finer than vp2. 0.20-0.95 did assert that, and it
# refused all eight captures of 2020-04-24 at scales of 1.01-1.13 on 374-402
# inliers apiece — a clean match to a frame that simply was not taken closer in
# than vp2. The scale a capture should show is its own eye altitude over vp2's
# 3.70 km, so an altitude at or a little above vp2's is legitimate and a scale
# near 1 means exactly that. Widened to cover roughly 0.74-5.2 km, which still
# rejects a gross mismatch; the AGREEMENT GATE is what actually tests a fit.
MIN_SCALE, MAX_SCALE = 0.20, 1.40
# Two captures of one surface, sampled to the ground, must agree. Calibrated on
# what a working pair gives: the vp2 twins reach 0.994 and a correct tile pair
# 0.87-0.89, against 0.02-0.09 for the lattice fits this replaces.
TILE_AGREE_MIN_R = 0.50
AGREE_MIN_CELLS = 5000


def _m41():
    import importlib.util as iu                              # noqa: PLC0415
    spec = iu.spec_from_file_location("m41", str(REPO / "src" / "41_canopy_cover.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _wfp():
    import importlib.util as iu                              # noqa: PLC0415
    spec = iu.spec_from_file_location(
        "wfp", str(REPO / "tools" / "warren_flood_prep.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _gray(path):
    import cv2                                               # noqa: PLC0415
    from PIL import Image                                    # noqa: PLC0415
    a = np.asarray(Image.open(path).convert("L"))
    # CLAHE, because a dune scene is low-contrast and its detail is local. Without
    # it SIFT finds most of its features on the interface and the coastline.
    return cv2.createCLAHE(3.0, (8, 8)).apply(a)


def _lum(path):
    from PIL import Image                                    # noqa: PLC0415
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    return 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]


def _vp2_reference(date, man):
    """The vp2 measurement frame for this date, else the nearest date's.

    A TILE DATE WITH NO vp2 FRAME IS NOT A FAILURE, but it is a weaker tie and is
    reported as one: 2020-04-24 and the two December composites exist only in the
    tiled series. SIFT across dates is far more tolerant than correlation — the
    vp2 series correlates at 0.34 between dates and matches fine — but the
    agreement gate, not this function, is what decides whether it worked.
    """
    m = man[(man["viewpoint"].astype(str).str.startswith("vp2"))
            & (man["role"] == "measurement")].copy()
    m["d"] = pd.to_datetime(m["imagery_date"], errors="coerce")
    m = m[m["d"].notna()]
    exact = m[m["imagery_date"].astype(str) == date]
    if len(exact):
        return str(exact["filename"].iloc[0]), True
    if not len(m):
        return None, False
    t = pd.Timestamp(date)
    m = m.assign(gap=(m["d"] - t).abs()).sort_values("gap")
    return str(m["filename"].iloc[0]), False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", action="append", default=None)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--budget", type=float, default=1e9,
                    help="stop after this many seconds; the cache is written "
                         "as it goes, so a re-run resumes")
    a = ap.parse_args()
    banner("Tile registration by image features", __version__)

    import time
    import cv2
    m41, wfp = _m41(), _wfp()
    man = pd.read_csv(MANIFEST, float_precision="round_trip")
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {"frames": {}}

    if a.report:
        t = {k: v for k, v in cache["frames"].items() if v.get("series") == "tile"}
        by = {}
        for k, v in t.items():
            by.setdefault(str(v.get("date")), []).append(v.get("registration", "?"))
        for d in sorted(by):
            from collections import Counter
            info(f"  {d}: " + ", ".join(f"{n} {w}" for w, n in
                                        Counter(by[d]).most_common()))
        return 0

    inv = pd.read_csv(INVENTORY, float_precision="round_trip")
    dates = sorted({str(x)[:10] for x in inv["date"].dropna()})
    if a.date:
        dates = [d for d in dates if d in set(a.date)]
    info(f"{len(dates)} date(s) to register")

    Hvp2, _ = wfp._vp2_transform()
    if Hvp2 is None:
        warn("the vp2 transform is unavailable; nothing to tie the tiles to")
        return 1
    sift = cv2.SIFT_create(nfeatures=SIFT_FEATURES)
    bf = cv2.BFMatcher()

    # the ground grid the agreement gate is measured on
    import geopandas as gpd
    from rasterio.features import geometry_mask
    from rasterio.transform import from_origin

    from utils.config import CANOPY_CHANGE_GRID_M
    from utils.warren_mask import warren_on
    hol = gpd.read_file(OUT / "W94_06_hollows.geojson").set_crs(
        "EPSG:27700", allow_override=True)
    res = float(CANOPY_CHANGE_GRID_M)
    minx, miny, maxx, maxy = hol.total_bounds
    minx, miny = np.floor(minx / res) * res - 200, np.floor(miny / res) * res - 200
    maxx, maxy = np.ceil(maxx / res) * res + 200, np.ceil(maxy / res) * res + 200
    EE, NN = np.meshgrid(np.arange(minx, maxx + res, res),
                         np.arange(maxy, miny - res, -res))
    gtr = from_origin(minx - res / 2, maxy + res / 2, res, res)

    t0 = time.time()
    rows = []
    for date in dates:
        phase(1, f"{date}")
        ref_name, exact = _vp2_reference(date, man)
        if ref_name is None:
            warn("  no vp2 frame at all; cannot tie this date")
            continue
        ref_p = REPO / "data" / "geo" / ref_name
        if not ref_p.exists():
            warn(f"  {ref_name} is not on disk")
            continue
        info(f"  reference: {ref_name}"
             + ("" if exact else "  — A DIFFERENT DATE; this date has no vp2 "
                                "frame, so the tie is across time and the "
                                "agreement gate is what tests it"))
        k1, d1 = sift.detectAndCompute(_gray(ref_p), None)
        wm = geometry_mask([warren_on(date)], out_shape=EE.shape, transform=gtr,
                           invert=True)

        names = [str(f) for f in inv[inv["date"].astype(str) == date]["file"]]
        fitted = {}
        for name in names:
            if time.time() - t0 > a.budget:
                warn("  budget reached; re-run to continue")
                break
            p = TILE_DIR / name
            if not p.exists():
                continue
            k2, d2 = sift.detectAndCompute(_gray(p), None)
            if d2 is None or len(k2) < 50:
                rows.append({"date": date, "tile": name, "verdict": "no features"})
                continue
            good = [x for x, y in bf.knnMatch(d2, d1, k=2)
                    if x.distance < RATIO * y.distance]
            if len(good) < 20:
                rows.append({"date": date, "tile": name, "n_good": len(good),
                             "verdict": "too few matches"})
                continue
            src = np.float32([k2[x.queryIdx].pt for x in good]).reshape(-1, 1, 2)
            dst = np.float32([k1[x.trainIdx].pt for x in good]).reshape(-1, 1, 2)
            H, mask = cv2.findHomography(src, dst, cv2.RANSAC, RANSAC_PX)
            if H is None or mask is None:
                rows.append({"date": date, "tile": name, "n_good": len(good),
                             "verdict": "no homography"})
                continue
            inl = int(mask.sum())
            scale = float(np.sqrt(abs(np.linalg.det(H[:2, :2]))))
            if inl < MIN_INLIERS or not (MIN_SCALE <= scale <= MAX_SCALE):
                rows.append({"date": date, "tile": name, "n_good": len(good),
                             "inliers": inl, "scale": round(scale, 3),
                             "verdict": "refused: inliers or scale"})
                continue
            Hi = np.linalg.inv(H)

            def f(E, N, Hi=Hi):
                u, v = Hvp2(np.asarray(E, float), np.asarray(N, float))
                q = Hi @ np.stack([np.asarray(u), np.asarray(v),
                                   np.ones_like(np.asarray(u))])
                return q[0] / q[2], q[1] / q[2]

            fitted[name] = {"f": f, "inliers": inl, "scale": scale,
                            "n_good": len(good)}

        if not fitted:
            warn("  no tile of this date produced a usable fit")
            continue

        # ── the gate: agreement with another capture of the same ground ──────
        step(f"  {len(fitted)} fit(s); testing each against the others")
        samp = {}
        for name, r in fitted.items():
            g, ok = m41._sample_to_grid(_lum(TILE_DIR / name), r["f"], EE, NN)
            samp[name] = (g, ok & np.isfinite(g) & wm)
        best_r = {n: -1.0 for n in fitted}
        partner = {n: None for n in fitted}
        for a_ in fitted:
            for b_ in fitted:
                if a_ >= b_:
                    continue
                ga, oa = samp[a_]
                gb, ob = samp[b_]
                m = oa & ob
                if int(m.sum()) < AGREE_MIN_CELLS:
                    continue
                rr = float(np.corrcoef(ga[m], gb[m])[0, 1])
                if not np.isfinite(rr):
                    continue
                for x, y in ((a_, b_), (b_, a_)):
                    if rr > best_r[x]:
                        best_r[x], partner[x] = rr, y

        grid = pd.read_csv(REPO / "data" / "geo" / "georef_grid.csv",
                           float_precision="round_trip")
        gE, gN = grid["easting"].values, grid["northing"].values
        n_ok = 0
        for name, r in fitted.items():
            rr = best_r[name]
            row = {"date": date, "tile": name, "reference": ref_name,
                   "same_date_reference": exact, "n_good": r["n_good"],
                   "inliers": r["inliers"], "scale": round(r["scale"], 3),
                   "agree_r": (round(rr, 3) if rr > -1 else None),
                   "agree_with": partner[name]}
            if rr < TILE_AGREE_MIN_R:
                row["verdict"] = ("refused: agrees with no other capture "
                                  f"(best r {rr:.3f})" if rr > -1
                                  else "refused: no overlap with any other tile")
                warn(f"    {name[-12:]}: {row['verdict']}")
                rows.append(row)
                cache["frames"].pop(name, None)
                continue
            u, v = r["f"](gE, gN)
            du = np.hypot(np.diff(u), np.diff(v))
            dm = np.hypot(np.diff(gE), np.diff(gN))
            m_ = (du > 1) & (dm > 1)
            gsd = float(np.median(dm[m_] / du[m_])) if m_.any() else float("nan")
            cache["frames"][name] = {
                "series": "tile", "date": date, "gsd_m": gsd,
                "residual_m": None, "registration": "sift-vp2",
                "reference": ref_name, "inliers": r["inliers"],
                "agree_r": round(rr, 3),
                "pairs": [[float(e), float(n), float(x), float(y)]
                          for e, n, x, y in zip(gE, gN, u, v)],
            }
            row["gsd_m"] = round(gsd, 3)
            row["verdict"] = "accepted"
            rows.append(row)
            n_ok += 1
        CACHE.write_text(json.dumps(cache))
        acc = [r_ for r_ in rows if r_["date"] == date
               and r_.get("verdict") == "accepted"]
        info(f"  accepted {n_ok} of {len(fitted)}; agreement r "
             + (f"{min(x['agree_r'] for x in acc):.2f} to "
                f"{max(x['agree_r'] for x in acc):.2f}" if acc else "n/a")
             + (f", GSD {np.median([x['gsd_m'] for x in acc]):.2f} m median"
                if acc else ""))

    if rows:
        D = pd.DataFrame(rows)
        if REPORT.exists():
            prev = pd.read_csv(REPORT, float_precision="round_trip")
            prev = prev[~prev["date"].astype(str).isin(D["date"].astype(str))]
            D = pd.concat([prev, D], ignore_index=True)
        D.sort_values(["date", "tile"]).to_csv(REPORT, index=False)
        saved(REPORT.name)
    saved(CACHE.name)
    info("EVERY TILE RESULT FROM 2026-09-12 MUST BE RE-RUN on this cache — "
         "coverage, the mosaics, phase 10 and phase 11 on tiles were all "
         "computed through the lattice fits and are void.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
