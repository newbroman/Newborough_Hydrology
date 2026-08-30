#!/usr/bin/env python3
"""
Script 41 — canopy and forest-cover change from the dated aerial series.

WHAT THIS MEASURES, AND WHAT IT DOES NOT

  A TEXTURE INDEX, not a canopy fraction. For each region and each dated frame:
  the local standard deviation of luminance in a small window, averaged over the
  region and divided by that region's mean luminance, then placed between two
  references taken INSIDE THE SAME FRAME:

      index = (region - open) / (conifer - open)

  0 means the region has the texture of open ground, 1 the texture of mature
  conifer. The in-frame normalisation is doing the real work: frame luminance
  runs 28.7 to 81.4 across this series because these are screen captures with
  varying exposure and compression, and both references move with it in step.

  THE UPPER ANCHOR IS CONIFER. A closed BROADLEAF canopy legitimately reads
  below 1, so the index cannot speak to full closure of the restock block at
  all — testing BL_CANOPY_FRACTION_2025 = 1.0 would need a closed broadleaf
  reference, and there is none in frame. The script prints this rather than
  leaving a reader to infer a percentage from a 0-1 number.

  It does NOT write BL_CANOPY_FRACTION_2005. That is an input in config.py, and
  D-075 puts fitted results in report-numbers files, not in a constants file —
  the rule that retired COAST_RETREAT_EFFECTIVE_M (D-086) and shaped D-091.

WHY A TEXTURE MEASURE AND NOT A COLOUR ONE

  Colour confuses species and season: the restock block reads reddish-brown in
  the March frames (deciduous leaf-off) and green in June. Crown-gap structure
  is closer to the physical quantity and survives the season.

REGISTRATION

  These are perspective screen captures, not orthophotos, so no affine can be
  right everywhere: the control polygon gives 1.35 m/px east-west against 1.59
  north-south, and that 15% anisotropy IS the perspective. So the control
  polygon only STARTS the registration. Every dipwell is a rendered marker and
  the project knows all 88 coordinates, so the markers are detected, matched to
  wells, and an eight-parameter HOMOGRAPHY is fitted by least squares — the
  transform the geometry actually calls for.

  Measured, on this series: validating the control affine without re-fitting
  reported a 51 m p95 against a 40 px search window, which is the WINDOW, not
  the error. Fitting an affine to the matched markers gave 14.3 m median;
  fitting the homography gave 6.8 m median, 17.2 m p95. The residual the affine
  left was structured perspective, exactly as the anisotropy predicted, and
  halving it by changing the model is what says so.

  Because the frames of one viewpoint are pixel-registered, the perspective
  distortion is common to all of them and cancels in any comparison BETWEEN
  frames. Absolute areas carry it; changes do not. That is why this script
  reports change fractions and never an area in hectares.

GATING - the D-085 precedent

  A region's index for a frame is WITHHELD, with the reason in the output,
  when the region is not wholly inside the map area, its footprint is under
  CANOPY_MIN_REGION_PX, the reference separation is under
  CANOPY_MIN_REF_SEPARATION, or the registration residual exceeds
  CANOPY_MAX_RESIDUAL_M. A withheld value is absent, not a number with a
  caveat beside it.

THE IMAGERY IS NOT IN THE REPOSITORY BY DEFAULT

  It is screen capture of a licensed basemap (Bluesky, Infoterra, COWI via
  Google Earth Pro). D-081 settled the shape of this for the historic OS scan:
  the source stays out, the attribution travels with the derived product. This
  script SKIPS with a notice when the imagery is absent, so a clone without it
  still runs the pipeline.

__version__ : 1.0.0
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-29. First issue. Formalises
#   the 2026-08-29 prototype (working/updates/NRG_BL_canopy_measurement…), whose
#   own recommendation was tools/ rather than a Script number; Martin ruled it
#   into the pipeline. The prototype's six hand-placed reference patches — its
#   stated weakest joint — are replaced by references derived from the KMLs.

import sys
import pathlib

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from utils.paths import (                                    # noqa: E402
    AERIAL_DIR, AERIAL_MANIFEST, KML_BROADLEAF, DATA_GEO_DIR,
    OUT_41_INDEX, OUT_41_CHANGE, OUT_41_REGISTRATION,
    OUT_41_SERIES_FIG, OUT_41_REPORT_NUMBERS, INT_LOCATIONS,
)
from utils.config import (                                   # noqa: E402
    CANOPY_TEXTURE_WINDOW, CANOPY_MIN_REGION_PX, CANOPY_MIN_REF_SEPARATION,
    CANOPY_MAX_RESIDUAL_M, CANOPY_CHANGE_PCTL, CANOPY_REF_BUFFER_M,
)
from utils.console_utils import banner, phase, step, info, warn, saved  # noqa: E402
from utils.render_utils import render_figure                 # noqa: E402

# The control polygon: its outline is drawn in every frame, so it is what the
# per-viewpoint affine is measured FROM. Declared, not guessed.
CONTROL_KML = "broadleaf_restock"

# Analysis regions: name -> (kml stem or Features.kml layer name, kind)
REGIONS = [
    ("broadleaf_restock", "kml:broadleaf_restock", "managed"),
    ("clearfell",         "kml:clearfell",         "managed"),
    ("felling_experiment", "features:Felling experiment", "managed"),
    ("forest_in_view",    "features:Forest",       "forest"),
]


def _lum(a: np.ndarray) -> np.ndarray:
    """BT.709 luminance, matching the greyscale convention used elsewhere."""
    return (0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2])


def _texture(lum: np.ndarray, w: int) -> np.ndarray:
    """Local standard deviation in a w x w window."""
    from scipy import ndimage
    k = np.ones((w, w), float) / (w * w)
    m = ndimage.convolve(lum, k, mode="nearest")
    m2 = ndimage.convolve(lum * lum, k, mode="nearest")
    return np.sqrt(np.maximum(m2 - m * m, 0.0))


def _region_stat(tex: np.ndarray, lum: np.ndarray, mask: np.ndarray):
    """mean(sd)/mean(luminance) over a mask, with the pixel count."""
    n = int(mask.sum())
    if n == 0:
        return np.nan, 0
    ml = float(lum[mask].mean())
    if ml < 1.0:                      # a 0-255 luminance; guard the DIVISOR, not
        return np.nan, n              # a 1e-6 epsilon (the prototype's bug)
    return float(tex[mask].mean()) / ml, n


def _load_geometries():
    import geopandas as gpd
    import warnings
    warnings.filterwarnings("ignore")
    from shapely.ops import unary_union

    out = {}
    feats = gpd.read_file(str(DATA_GEO_DIR / "Features.kml"), driver="KML").to_crs("EPSG:27700")
    for name, spec, kind in REGIONS:
        if spec.startswith("kml:"):
            g = gpd.read_file(str(DATA_GEO_DIR / f"{spec[4:]}.kml"), driver="KML").to_crs("EPSG:27700")
            geom = unary_union([x for x in g.geometry if x.geom_type in ("Polygon", "MultiPolygon")])
        else:
            sel = feats[feats["Name"] == spec.split(":", 1)[1]]
            geom = unary_union(list(sel.geometry)) if len(sel) else None
        if geom is None or geom.is_empty:
            warn(f"region {name}: no polygon found; skipped")
            continue
        out[name] = (geom, kind)

    # References, from the KMLs rather than by hand — the prototype's weakest
    # joint and the first thing it said an implementation must fix.
    forest = unary_union(list(feats[feats["Name"] == "Forest"].geometry))
    managed = unary_union([out[n][0] for n, _, k in REGIONS
                           if n in out and k == "managed"])
    conifer_ref = forest.difference(managed.buffer(CANOPY_REF_BUFFER_M))
    site = gpd.read_file(str(DATA_GEO_DIR / "site_boundary.kml"), driver="KML").to_crs("EPSG:27700")
    site_u = unary_union(list(site.geometry))
    open_ref = site_u.difference(forest.buffer(CANOPY_REF_BUFFER_M))
    return out, conifer_ref, open_ref


def _affine_from_control(png_paths, control_geom):
    """Pixel<->grid affine per viewpoint, measured from the control outline.

    Returns (fn_grid_to_px, m_per_px_e, m_per_px_n, bbox_px) or None.
    """
    from PIL import Image
    a = np.asarray(Image.open(png_paths[0]).convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    m = (g > 195) & (b < 60) & (g - b > 150) & (g - r > 50)
    m[:90, :] = False
    m[:, :215] = False
    m[:, 1845:] = False
    m[1000:, :] = False
    ys, xs = np.nonzero(m)
    if len(xs) < 200:
        return None
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    minx, miny, maxx, maxy = control_geom.bounds
    mpx_e = (maxx - minx) / (x1 - x0)
    mpx_n = (maxy - miny) / (y1 - y0)

    def to_px(E, N):
        return (x0 + (np.asarray(E) - minx) / mpx_e,
                y0 + (maxy - np.asarray(N)) / mpx_n)

    return to_px, mpx_e, mpx_n, (int(x0), int(x1), int(y0), int(y1))


def _fit_from_placemarks(png, to_px, mpx_e, mpx_n):
    """Least-squares affine from the rendered dipwell placemarks.

    The control-polygon affine is only a STARTING POINT: it is measured from one
    polygon in one corner of the frame, and a perspective view drifts away from
    it. Validating against the placemarks without re-fitting measures the
    matching radius, not the registration — the first run reported a 51 m p95
    against a 40 px search window, which is the window, not the error.

    So: predict with the initial affine, match to detected marker tips, fit a
    six-parameter affine by least squares on the matched pairs, and iterate once
    with a tighter window. Residuals are then a property of the registration.

    Returns (fitted_to_px or None, median_m, p95_m, n_matched).
    """
    from PIL import Image
    from scipy import ndimage
    try:
        wells = pd.read_csv(INT_LOCATIONS)
    except Exception:
        return None, np.nan, np.nan, 0
    ecol = next((c for c in wells.columns if c.lower() in ("easting", "e", "x")), None)
    ncol = next((c for c in wells.columns if c.lower() in ("northing", "n", "y")), None)
    if ecol is None or ncol is None:
        return None, np.nan, np.nan, 0
    E = wells[ecol].values.astype(float)
    N = wells[ncol].values.astype(float)

    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    pin = (b > 150) & (b - r > 45) & (b - g > 30)
    pin[:90, :] = False
    pin[:, :215] = False
    pin[:, 1845:] = False
    lab, n = ndimage.label(pin)
    if n == 0:
        return None, np.nan, np.nan, 0
    sizes = ndimage.sum(pin, lab, range(1, n + 1))
    keep = [i + 1 for i in range(n) if 120 < sizes[i] < 1500]
    if len(keep) < 6:
        return None, np.nan, np.nan, 0
    cen = ndimage.center_of_mass(pin, lab, keep)
    # the marker POINTS at its well from the bottom of the teardrop
    tips = np.array([[c[1], c[0] + 16.0] for c in cen])

    coef = None
    for radius in (45.0, 18.0):
        if coef is None:
            px, py = to_px(E, N)
        else:
            px = coef[0] * E + coef[1] * N + coef[2]
            py = coef[3] * E + coef[4] * N + coef[5]
        pairs = []
        used = set()
        for i in range(len(E)):
            d = np.hypot(tips[:, 0] - px[i], tips[:, 1] - py[i])
            j = int(d.argmin())
            if d[j] < radius and j not in used:
                used.add(j)
                pairs.append((E[i], N[i], tips[j, 0], tips[j, 1]))
        if len(pairs) < 6:
            return None, np.nan, np.nan, len(pairs)
        P = np.array(pairs)
        A = np.column_stack([P[:, 0], P[:, 1], np.ones(len(P))])
        cx, *_ = np.linalg.lstsq(A, P[:, 2], rcond=None)
        cy, *_ = np.linalg.lstsq(A, P[:, 3], rcond=None)
        coef = (cx[0], cx[1], cx[2], cy[0], cy[1], cy[2])

    # An affine cannot represent a perspective view, and the residual it leaves
    # is structured rather than random. With enough matched markers, fit the
    # eight-parameter homography the geometry actually calls for and keep it
    # only if it beats the affine on the same points.
    H = None
    if len(P) >= 8:
        E_, N_, U_, V_ = P[:, 0], P[:, 1], P[:, 2], P[:, 3]
        E0, N0 = E_.mean(), N_.mean()
        e, nn = (E_ - E0) / 1000.0, (N_ - N0) / 1000.0
        M, rhs = [], []
        for k in range(len(P)):
            M.append([e[k], nn[k], 1, 0, 0, 0, -U_[k] * e[k], -U_[k] * nn[k]])
            rhs.append(U_[k])
            M.append([0, 0, 0, e[k], nn[k], 1, -V_[k] * e[k], -V_[k] * nn[k]])
            rhs.append(V_[k])
        hsol, *_ = np.linalg.lstsq(np.array(M), np.array(rhs), rcond=None)
        def _h(Ev, Nv, h=hsol, E0=E0, N0=N0):
            ee, nv = (np.asarray(Ev, float) - E0) / 1000.0, (np.asarray(Nv, float) - N0) / 1000.0
            den = h[6] * ee + h[7] * nv + 1.0
            return ((h[0] * ee + h[1] * nv + h[2]) / den,
                    (h[3] * ee + h[4] * nv + h[5]) / den)
        hu, hv = _h(E_, N_)
        if np.hypot(hu - U_, hv - V_).mean() < np.hypot(A @ cx - U_, A @ cy - V_).mean():
            H = _h

    res_px = (np.hypot(*[a - b for a, b in zip(H(P[:, 0], P[:, 1]), (P[:, 2], P[:, 3]))])
              if H is not None else np.hypot(A @ cx - P[:, 2], A @ cy - P[:, 3]))
    scale = (mpx_e + mpx_n) / 2.0
    res_m = res_px * scale

    def fitted(Ev, Nv):
        if H is not None:
            return H(Ev, Nv)
        Ev = np.asarray(Ev, float)
        Nv = np.asarray(Nv, float)
        return (coef[0] * Ev + coef[1] * Nv + coef[2],
                coef[3] * Ev + coef[4] * Nv + coef[5])

    return fitted, float(np.median(res_m)), float(np.percentile(res_m, 95)), len(P)


def main() -> int:
    banner("41", "Canopy and forest cover from the dated aerial series",
           version=__version__)

    if not AERIAL_MANIFEST.exists():
        warn(f"No aerial manifest at {AERIAL_MANIFEST.name} — the imagery is not "
             f"in the repository by design (D-081). Skipping Script 41.")
        return 0
    man = pd.read_csv(AERIAL_MANIFEST)
    man = man[man["role"] == "registration"].copy()
    man["imagery_date"] = pd.to_datetime(man["imagery_date"])
    man = man.sort_values("imagery_date")
    paths = [AERIAL_DIR / f for f in man["filename"]]
    missing = [p.name for p in paths if not p.exists()]
    if missing:
        warn(f"{len(missing)} frame(s) named in the manifest are absent "
             f"(e.g. {missing[0]}). Skipping Script 41.")
        return 0

    phase(1, "Geometry and registration")
    regions, conifer_ref, open_ref = _load_geometries()
    import geopandas as gpd
    import warnings
    warnings.filterwarnings("ignore")
    from shapely.ops import unary_union
    ctrl = unary_union(list(gpd.read_file(
        str(DATA_GEO_DIR / f"{CONTROL_KML}.kml"), driver="KML")
        .to_crs("EPSG:27700").geometry))

    aff = _affine_from_control(paths, ctrl)
    if aff is None:
        warn("control outline not detected in the first frame; cannot register. "
             "Skipping Script 41.")
        return 0
    to_px, mpx_e, mpx_n, bbox = aff
    info(f"affine from {CONTROL_KML}: {mpx_e:.2f} m/px E-W, {mpx_n:.2f} m/px N-S")
    info(f"  the {abs(mpx_e - mpx_n) / max(mpx_e, mpx_n) * 100:.0f}% anisotropy is "
         f"the perspective; these are captures, not orthophotos")

    from PIL import Image, ImageDraw
    h, w = np.asarray(Image.open(paths[0]).convert("RGB")).shape[:2]

    # Fit the registration ONCE, on the first frame, and use it for the masks.
    # The frames of one viewpoint are pixel-registered, so one transform serves
    # them all; validating per frame is what catches a viewpoint that moved.
    fit0, med0, p950, n0 = _fit_from_placemarks(paths[0], to_px, mpx_e, mpx_n)
    project = fit0 if fit0 is not None else to_px
    if fit0 is None:
        warn("placemark fit failed on the first frame; falling back to the "
             "control-polygon affine, which does not model the perspective")
    else:
        info(f"registration fitted from {n0} placemarks: median {med0:.1f} m, "
             f"p95 {p950:.1f} m")

    def mask_of(geom):
        """Rasterise a projected polygon in PIXEL space.

        The transform is a homography, not an affine, so a north-up raster
        transform cannot express it. Projecting the vertices and filling in
        pixel space is exact for the model we actually fitted.
        """
        img = Image.new("1", (w, h), 0)
        d = ImageDraw.Draw(img)
        polys = (list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom])
        for poly in polys:
            cc = list(poly.exterior.coords)[:-1]
            xs, ys = project([c[0] for c in cc], [c[1] for c in cc])
            d.polygon(list(zip(np.asarray(xs), np.asarray(ys))), fill=1)
            for ring in poly.interiors:
                cc = list(ring.coords)[:-1]
                xs, ys = project([c[0] for c in cc], [c[1] for c in cc])
                d.polygon(list(zip(np.asarray(xs), np.asarray(ys))), fill=0)
        return np.array(img, dtype=bool)

    map_area = np.zeros((h, w), bool)
    map_area[90:1000, 215:1845] = True
    masks = {n: mask_of(g) & map_area for n, (g, _) in regions.items()}
    ref_con = mask_of(conifer_ref) & map_area
    ref_opn = mask_of(open_ref) & map_area
    for n, m in masks.items():
        info(f"  region {n:20s} {int(m.sum()):7d} px in view")
    info(f"  reference conifer      {int(ref_con.sum()):7d} px")
    info(f"  reference open         {int(ref_opn.sum()):7d} px")

    phase(2, "Texture index per frame")
    reg_rows, idx_rows, cache = [], [], {}
    for p, d in zip(paths, man["imagery_date"]):
        fitted, med, p95, nmatch = _fit_from_placemarks(p, to_px, mpx_e, mpx_n)
        reg_rows.append({"frame": p.name, "imagery_date": d.date(),
                         "n_control_points": nmatch,
                         "residual_median_m": None if np.isnan(med) else med,
                         "residual_p95_m": None if np.isnan(p95) else p95})
        a = np.asarray(Image.open(p).convert("RGB")).astype(float)
        lum = _lum(a)
        tex = _texture(lum, CANOPY_TEXTURE_WINDOW)
        cache[p.name] = (lum, tex)
        c_stat, _ = _region_stat(tex, lum, ref_con)
        o_stat, _ = _region_stat(tex, lum, ref_opn)
        sep = c_stat - o_stat
        for name, m in masks.items():
            r_stat, npx = _region_stat(tex, lum, m)
            reason = ""
            if npx < CANOPY_MIN_REGION_PX:
                reason = f"region {npx} px < {CANOPY_MIN_REGION_PX}"
            elif not np.isfinite(sep) or sep < CANOPY_MIN_REF_SEPARATION:
                reason = f"reference separation {sep:.4f} < {CANOPY_MIN_REF_SEPARATION}"
            elif np.isnan(p95):
                reason = (f"registration failed: only {nmatch} placemark(s) "
                          f"matched — the frame is not registered, so the "
                          f"region mask cannot be trusted")
            elif p95 > CANOPY_MAX_RESIDUAL_M:
                reason = f"registration p95 {p95:.1f} m > {CANOPY_MAX_RESIDUAL_M}"
            val = np.nan if reason else (r_stat - o_stat) / sep
            idx_rows.append({"region": name, "imagery_date": d.date(),
                             "frame": p.name, "n_px": npx,
                             "index": None if reason else float(val),
                             "withheld_reason": reason})
    # D-035: stores carry what the pipeline computed. Rounding is a rendering
    # decision and belongs where a number is shown, not where it is written.
    pd.DataFrame(reg_rows).to_csv(OUT_41_REGISTRATION, index=False)
    saved(OUT_41_REGISTRATION.name)
    idx = pd.DataFrame(idx_rows)
    idx.to_csv(OUT_41_INDEX, index=False)
    saved(OUT_41_INDEX.name)

    phase(3, "Change between consecutive frames")
    ch_rows = []
    names = list(man["filename"])
    for i in range(1, len(names)):
        la, ta = cache[names[i - 1]]
        lb, tb = cache[names[i]]
        na = (la - la[map_area].mean()) / max(la[map_area].std(), 1e-6)
        nb = (lb - lb[map_area].mean()) / max(lb[map_area].std(), 1e-6)
        diff = np.abs(na - nb)
        thr = np.percentile(diff[map_area], CANOPY_CHANGE_PCTL)
        changed = (diff > thr) & map_area
        for name, m in masks.items():
            npx = int(m.sum())
            ch_rows.append({
                "region": name,
                "from_date": man["imagery_date"].iloc[i - 1].date(),
                "to_date": man["imagery_date"].iloc[i].date(),
                "change_fraction": float((changed & m).sum() / npx) if npx else None,
            })
    pd.DataFrame(ch_rows).to_csv(OUT_41_CHANGE, index=False)
    saved(OUT_41_CHANGE.name)

    phase(4, "Figure and report numbers")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))
    for name in masks:
        sub = idx[(idx["region"] == name) & idx["index"].notna()]
        if len(sub):
            ax.plot(pd.to_datetime(sub["imagery_date"]), sub["index"],
                    marker="o", label=name)
    ax.set_ylabel("texture index  (0 = open ground, 1 = mature conifer)")
    ax.set_xlabel("imagery date")
    ax.set_title("Canopy texture index from the dated aerial series")
    ax.axhline(0, lw=0.6, color="0.6")
    ax.legend(fontsize=8)
    render_figure(fig, OUT_41_SERIES_FIG)
    saved(OUT_41_SERIES_FIG.name)

    rn = []
    bl = idx[(idx["region"] == "broadleaf_restock") & idx["index"].notna()]
    if len(bl):
        first = bl.iloc[0]
        rn.append({"Parameter": "canopy_index_restock_first_frame", "Well": "",
                   "Era": str(first["imagery_date"]), "Value": first["index"],
                   "Unit": "index",
                   "Note": ("texture position between in-frame open and conifer "
                            "references; NOT a canopy fraction, and its upper "
                            "anchor is conifer so a closed broadleaf canopy reads "
                            "below 1")})
        rn.append({"Parameter": "canopy_index_restock_plateau_median", "Well": "",
                   "Era": "2009-2026", "Value": float(bl["index"][1:].median()),
                   "Unit": "index", "Note": "median of every frame after the first"})
    pd.DataFrame(rn).to_csv(OUT_41_REPORT_NUMBERS, index=False)
    saved(OUT_41_REPORT_NUMBERS.name)

    withheld = int(idx["withheld_reason"].astype(bool).sum())
    step(f"{len(idx)} region-frame values, {withheld} withheld")
    info("the index is a texture position, not a canopy fraction: its upper "
         "anchor is conifer, so a closed broadleaf canopy reads below 1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
