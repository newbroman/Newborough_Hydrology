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

  HOW WELL IT WORKS IS MEASURABLE, and it is a result rather than a hope. The
  `forest_in_view` control — mature conifer, same normalisation — reads 1.010
  with a range of 1.004 to 1.019 across 2006-2017. One per cent over eleven
  years of varying exposure is what says the anchoring holds.

  THE INDEX IS NOT BOUNDED ABOVE BY 1, and v1.0.0 said it was. That docstring
  asserted "a closed BROADLEAF canopy legitimately reads below 1". The measured
  restock reaches 1.28 against the conifer control IN THE SAME FRAME, so it is
  not a normalisation artefact: the block genuinely has more normalised local
  variance than mature conifer. Martin's mechanism, and it is the right one —

      THE INDEX SEES CANOPY AND UNDERSTOREY TOGETHER.

  A young open broadleaf block has structure at two levels; a closed conifer
  stand has a bare, shaded floor. So the expected signature of a maturing block
  is a RISE THEN A FALL, as its own closing canopy suppresses the understorey
  that was contributing the roughness — not a plateau, and not a monotone climb.

  It does NOT write BL_CANOPY_FRACTION_2005. That is an input in config.py, and
  D-075 puts fitted results in report-numbers files, not in a constants file —
  the rule that retired COAST_RETREAT_EFFECTIVE_M (D-086) and shaped D-091.

LEAF STATE IS NOT OPTIONAL

  For a deciduous region the index is only comparable between frames in the same
  phenological state, and the difference is large. On the in-frame ratio to the
  conifer control:

      full leaf (May-Jul)   n=4   1.215   sd 0.044  (3.6%)   spans 2012-2019
      emerging  (Mar-Apr)   n=5   1.030   sd 0.148
      leaf off  (Nov-Feb)   n=1   0.567

  Stratifying is what turns this series from unusable into usable, and the
  classes come from config (LEAF_*_MONTHS), named for leaf state rather than
  season under D-100.

  AND IT WITHDRAWS A CLAIM. v1.0.0 emitted a "plateau median" over every frame
  after the first, and the 2006 -> 2012 rise reads as a canopy growth curve. It
  is not one. The three points are 2006-01 LEAF OFF 0.567, 2009-04 EMERGING
  0.897, 2012-05 FULL LEAF 1.206 — three different leaf states in exactly
  ascending order of leaf state — and there is no full-leaf frame before 2012,
  so growth and phenology cannot be separated at all on this record. On the
  full-leaf subset the series is FLAT: 1.206, 1.176, 1.278, 1.200. This version
  reports on a full-leaf basis and emits no growth number.

WHY A TEXTURE MEASURE AND NOT A COLOUR ONE

  Colour confuses species and season: the restock block reads reddish-brown in
  the March frames (deciduous leaf-off) and green in June. Crown-gap structure
  is closer to the physical quantity and survives the season better — though as
  the numbers above show, "better" is not "entirely".

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
  fitting the homography gave 6.8 m median, 17.2 m p95.

  THE MARKERS ARE TWO SIZES, and v1.0.0 only found one of them. The `site*m`
  captures render the same blue markers MUCH SMALLER than the `aerial` captures
  do. A 120 px blob floor rejected every small one, so all 60 of those region-
  frame values were withheld as "0 placemark(s) matched" and 2021 — which has no
  `aerial` frame at all — was lost entirely. Three literals caused it and all
  three are now config constants or derived: the size floor, a 16 px tip offset
  calibrated to the large teardrop, and absolute pixel crop margins that assume
  one frame width. The tip is now taken from each blob's own bounding box, which
  is scale-free, and the margins are fractions of the frame — the 2026 capture is
  a different size because the window shifts when the historic imagery is toggled
  off.

CHANGE IS MEASURED ON THE GROUND, NOT ON THE SCREEN

  v1.0.0's phase 3 walked consecutive rows of the frame MANIFEST and differenced
  raw luminance pixel-by-pixel. Three things followed, all of them in the
  committed CSV: 56 of 112 rows compared a date with itself, because the
  `aerial`, `site` and `seabed` captures of one date are separate manifest rows;
  rows crossing viewpoints compared unaligned images, where the difference is
  dominated by perspective; and the region masks were applied to UNREGISTERED
  frames — the same frames phase 2 correctly refuses, used silently because the
  change output had no withheld_reason column and no gate.

  Frames also differ in size, so a pixel difference is not merely mislabelled,
  it is ill-defined. This version resamples each registered frame onto a common
  OSGB grid at CANOPY_CHANGE_GRID_M and differences there, pairs consecutive
  IMAGERY DATES rather than manifest rows, uses only pairs where both frames
  registered, and carries a withheld_reason so a refused pair is absent rather
  than a plausible number.

THE CONTROL MASK EXCLUDES THE MANAGED BLOCKS

  `forest_in_view` is the control, and in v1.0.0 it was the raw Forest polygon —
  which overlaps the felled area. It read 1.010 over 2006-2017 and 0.954 from
  2018, a 5.6% step coincident with the clearfell. Conifers are evergreen and
  the step is not a month effect (pre-2018 frames span months 1,3,4,5 and
  post-2018 span 3,4,6,7,9, so both cover spring and summer and sun angle is
  excluded), which leaves the polygon. The control now has the managed blocks
  and their CANOPY_REF_BUFFER_M collar subtracted — the same construction the
  conifer REFERENCE already used — and the removed area is reported so the
  correction is visible rather than assumed.

GATING - the D-085 precedent

  A region's index for a frame is WITHHELD, with the reason in the output,
  when the frame did not register, its residual exceeds CANOPY_MAX_RESIDUAL_M,
  the region is not wholly inside the map area, its footprint is under
  CANOPY_MIN_REGION_PX, or the reference separation is under
  CANOPY_MIN_REF_SEPARATION. A withheld value is absent, not a number with a
  caveat beside it. The registration test is now FIRST, because a frame that did
  not register cannot have a meaningful reference separation either and reporting
  the downstream symptom hid the cause.

THE IMAGERY IS NOT IN THE REPOSITORY BY DEFAULT

  It is screen capture of a licensed basemap (Bluesky, Infoterra, COWI via
  Google Earth Pro). D-081 settled the shape of this for the historic OS scan:
  the source stays out, the attribution travels with the derived product. This
  script SKIPS with a notice when the imagery is absent, so a clone without it
  still runs the pipeline.

  A CONSEQUENCE FOR WHOEVER EDITS THIS FILE: it cannot be exercised from a
  clone. Compiling proves nothing. Run it where the imagery is, then READ THE
  ARTEFACTS BACK — 41_03's n_control_points and residuals for the 2021 and 2026
  frames are the test of the marker change, and a recovered frame with a poor
  residual is a false-positive match, not a recovery.

__version__ : 2.0.0
"""
from __future__ import annotations

__version__ = "2.2.0"  # Hollingham (2026) — 2026-08-31. THE RESOLUTION GATE,
#   and it closes the 2021 question with a negative rather than leaving it open.
#   v2.1.0 recovered the site* and seabed frames and they promptly produced
#   plausible-looking values that measure nothing: pooled over the managed
#   regions their index correlates with the AERIAL index of the same region on
#   the same day at r = +0.089 (n = 33), and for the restock at -0.513, the
#   wrong sign. The clearfell settles it — aerial 1.235 (2017-04) to 0.141
#   (2018-06) across the December 2017 fell, site 0.016 to -0.048 and already
#   near zero in 2009. Not registration: those frames now sit at 2.7-4.4 m. It
#   is resolution, and the gate is on measured GROUND SAMPLING DISTANCE, derived
#   per group from its own fitted transform. So 2021, which exists only in the
#   site viewpoint, is NOT recoverable as a canopy measurement - and the reason
#   is now in the output rather than in someone's memory.
#
# v2.1.0  # Hollingham (2026) — 2026-08-31. THE SEED, which is what
#   v2.0.0 got wrong. Fixing the marker SIZE was necessary and not sufficient:
#   site24-3-2021m yielded 97 marker blobs and still matched four, because every
#   frame was seeded from the FIRST frame's affine and the site* captures are a
#   different viewpoint 91 px away. Martin: "they are all in the same location in
#   all images, and the same size" - measured true WITHIN a constellation group,
#   to 0.0 px, and the groups differ by a small rigid offset because the view was
#   nudged between sessions. So: group the frames by constellation, seed each
#   group from its OWN control outline where it has one, chain from a solved
#   group where the constellations genuinely coincide, and iterate the match/refit
#   to convergence instead of exactly twice. Also corrects v2.0.0's crop
#   fractions (computed for 1200 x 1920; the frames are 1920 x 1080) and turns
#   dilation off (it merged adjacent large markers).
#
# v2.0.0  # Hollingham (2026) — 2026-08-31. Martin signed off the
#   four changes below on 2026-08-31; spec in
#   working/updates/NRG_spec_script41_2026-08-31.md (W109-W112).
#
#   (1) MARKER DETECTION. The small blue markers of the `site*m` captures were
#   rejected by a 120 px blob floor, taking 60 region-frame values and the whole
#   of 2021 with them. Size bounds are config; the teardrop tip comes from each
#   blob's own bounding box instead of a fixed 16 px; crop margins are fractions
#   of the frame rather than pixels; and a dilation before labelling keeps an
#   anti-aliased small symbol as one component. NOTE what is NOT done: the
#   residual tolerance is untouched. If lowering the floor produces matches with
#   poor residuals, CANOPY_MAX_RESIDUAL_M must refuse them — the withholding
#   gate is the part that has been working correctly throughout.
#
#   (2) LEAF STATE. 41_01 gains leaf_state and ratio_to_conifer; report numbers
#   are computed on a FULL-LEAF basis only. The mislabelled
#   canopy_index_restock_plateau_median is withdrawn — its own note said "median
#   of every frame after the first", which spans two leaf states and the growth
#   limb — and no growth number is emitted, because growth and phenology are not
#   separable before 2012.
#
#   (3) CHANGE ON A COMMON GROUND GRID, pairing imagery dates rather than
#   manifest rows, registered frames only, with a withheld_reason column.
#
#   (4) THE CONTROL MASK subtracts the managed blocks and their buffer, which is
#   what the 2018 step in forest_in_view was.
#
# v1.0.0  # Hollingham (2026) — 2026-08-29. First issue. Formalises
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
    CANOPY_MARKER_MIN_PX, CANOPY_MARKER_MAX_PX, CANOPY_MARKER_DILATE,
    CANOPY_CROP_FRAC_TOP, CANOPY_CROP_FRAC_LEFT, CANOPY_CROP_FRAC_RIGHT,
    CANOPY_CROP_FRAC_BOTTOM, CANOPY_CHANGE_GRID_M,
    CANOPY_CONSTELLATION_TOL_PX, CANOPY_GROUP_MIN_FRACTION, CANOPY_CHAIN_MIN_TIPS,
    CANOPY_MIN_CONTROL_POINTS, CANOPY_MATCH_RADII_NARROW, CANOPY_MATCH_RADII_WIDE,
    CANOPY_MATCH_MAX_ITER, CANOPY_MAX_GSD_M,
    LEAF_OFF_MONTHS, LEAF_EMERGING_MONTHS, LEAF_FULL_MONTHS,
    LEAF_SENESCING_MONTHS,
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
    ("forest_in_view",    "features:Forest",       "control"),
]

# The control region. Named once here rather than spelled in three places, so
# the ratio, the mask correction and the report numbers cannot drift apart.
CONTROL_REGION = "forest_in_view"


def _viewpoint(frame_name: str) -> str:
    """Which camera position a frame was captured from.

    THIS MATTERS NOW AND DID NOT BEFORE. Until v2.1.0 only the `aerial` frames
    registered, so every usable value came from one viewpoint and the question
    never arose. With the site* and seabed frames recovered, the same region on
    the same DAY reads very differently between them — measured 2026-08-31 on
    2017-04-22: broadleaf_restock 1.045 from the aerial frame, -0.113 from the
    site frame, 0.113 from the seabed frame.

    That is not an error. Local texture depends on ground sampling distance and
    on obliquity, and these are three different views of the same ground. It
    means the index is comparable WITHIN a viewpoint and not between viewpoints,
    the way it is comparable within a leaf state and not between them.
    """
    n = frame_name.strip().lower()
    for v in ("aerial", "seabed", "site"):
        if n.startswith(v):
            return v
    return "unknown"


def _leaf_state(month: int) -> str:
    """Which phenological class a frame's month belongs to.

    Named for LEAF STATE, not season (D-100). The classes are Martin's, set from
    the series itself on 2026-08-31, and they live in config so `season_lint`
    can see them and no script can define a private variant.
    """
    m = int(month)
    if m in LEAF_OFF_MONTHS:
        return "leaf_off"
    if m in LEAF_EMERGING_MONTHS:
        return "emerging"
    if m in LEAF_FULL_MONTHS:
        return "full_leaf"
    if m in LEAF_SENESCING_MONTHS:
        return "senescing"
    return "unclassified"


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


def _frame_window(h: int, w: int) -> tuple:
    """The usable rectangle of a frame, as FRACTIONS of its own size.

    v1.0.0 wrote these as pixels — [:90], [:215], [1845:], [1000:] — which
    assumes one frame width. The 2026 capture is a different size because the
    window shifts when the historic imagery is toggled off, so absolute margins
    mask the wrong part of it. Returns (row0, row1, col0, col1).
    """
    return (int(round(CANOPY_CROP_FRAC_TOP * h)),
            int(round(CANOPY_CROP_FRAC_BOTTOM * h)),
            int(round(CANOPY_CROP_FRAC_LEFT * w)),
            int(round(CANOPY_CROP_FRAC_RIGHT * w)))


def _apply_window(mask: np.ndarray) -> np.ndarray:
    """Zero everything outside the usable rectangle, in place-safe fashion."""
    h, w = mask.shape
    r0, r1, c0, c1 = _frame_window(h, w)
    out = np.zeros_like(mask)
    out[r0:r1, c0:c1] = mask[r0:r1, c0:c1]
    return out


def _load_geometries():
    """Region polygons, plus the in-frame conifer and open references.

    The CONTROL region has the managed blocks and their buffer subtracted. It is
    a control for the managed change, so any overlap with a felled block makes it
    partly a control for the thing it is controlling — which is what the 5.6%
    step in forest_in_view after 2018 was. The same buffer the conifer REFERENCE
    already used is applied, so the two are constructed alike.

    Returns (regions, conifer_ref, open_ref, control_overlap_m2).
    """
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

    # The control has the managed blocks subtracted, but NOT the buffer collar
    # the conifer REFERENCE uses. Subtracting both makes the control identical
    # to the reference, and the index of a region that IS the reference is 1.000
    # by construction with zero variance — measured, 2026-08-31, on the first
    # v2.1.0 run. A control that cannot move is not a control.
    overlap = 0.0
    if CONTROL_REGION in out:
        raw, kind = out[CONTROL_REGION]
        cleaned = raw.difference(managed)
        overlap = float(raw.area - cleaned.area)
        out[CONTROL_REGION] = (cleaned, kind)
    return out, conifer_ref, open_ref, overlap


def _affine_from_control(png_paths, control_geom):
    """Pixel<->grid affine per viewpoint, measured from the control outline.

    Returns (fn_grid_to_px, m_per_px_e, m_per_px_n, bbox_px) or None.
    """
    from PIL import Image
    a = np.asarray(Image.open(png_paths[0]).convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    m = (g > 195) & (b < 60) & (g - b > 150) & (g - r > 50)
    m = _apply_window(m)
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


def _detect_markers(a: np.ndarray):
    """Blue placemark tips, in pixel coordinates.

    TWO SIZES. The `aerial` captures render large teardrops; the `site*m`
    captures render the same markers much smaller. v1.0.0 kept blobs of
    120-1500 px and took the tip 16 px below the centroid, both calibrated to
    the large symbol — so every small marker was rejected before matching, and
    even a detected one would have been placed 16 px away from where it points.

    Two changes make it scale-free. The blob floor comes from config and is set
    for the SMALL symbol. The tip is the bottom-centre of each blob's own
    bounding box, which is where a teardrop points regardless of its size.

    A dilation before labelling is the third: a small symbol is mostly
    anti-aliased edge, so a per-pixel colour test fragments it into several
    components, each below any sane floor. Size is measured on the UNDILATED
    mask so the bounds still mean what they say.
    """
    from scipy import ndimage
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    pin = (b > 150) & (b - r > 45) & (b - g > 30)
    pin = _apply_window(pin)
    lab_src = ndimage.binary_dilation(pin) if CANOPY_MARKER_DILATE else pin
    lab, n = ndimage.label(lab_src)
    if n == 0:
        return np.zeros((0, 2), float)
    sizes = ndimage.sum(pin, lab, range(1, n + 1))
    keep = [i + 1 for i in range(n)
            if CANOPY_MARKER_MIN_PX < sizes[i] < CANOPY_MARKER_MAX_PX]
    if not keep:
        return np.zeros((0, 2), float)
    # Bottom-centre of each blob: where the teardrop points, at any scale.
    slices = ndimage.find_objects(lab)
    tips = []
    for k in keep:
        sy, sx = slices[k - 1]
        tips.append([(sx.start + sx.stop - 1) / 2.0, float(sy.stop - 1)])
    return np.asarray(tips, float)


def _homography(P):
    """Eight-parameter projective fit to matched (E, N) -> (px, py) pairs."""
    E_, N_, U_, V_ = P[:, 0], P[:, 1], P[:, 2], P[:, 3]
    E0, N0 = E_.mean(), N_.mean()
    e, nn = (E_ - E0) / 1000.0, (N_ - N0) / 1000.0
    M, rhs = [], []
    for k in range(len(P)):
        M.append([e[k], nn[k], 1, 0, 0, 0, -U_[k] * e[k], -U_[k] * nn[k]])
        rhs.append(U_[k])
        M.append([0, 0, 0, e[k], nn[k], 1, -V_[k] * e[k], -V_[k] * nn[k]])
        rhs.append(V_[k])
    h, *_ = np.linalg.lstsq(np.array(M), np.array(rhs), rcond=None)

    def H(Ev, Nv, h=h, E0=E0, N0=N0):
        ee = (np.asarray(Ev, float) - E0) / 1000.0
        nv = (np.asarray(Nv, float) - N0) / 1000.0
        den = h[6] * ee + h[7] * nv + 1.0
        return ((h[0] * ee + h[1] * nv + h[2]) / den,
                (h[3] * ee + h[4] * nv + h[5]) / den)
    return H


def _match_and_fit(tips, E, N, seed, radii):
    """Match wells to marker tips and refit, ITERATING TO CONVERGENCE.

    v1.0.0 matched at 45 px, refit, matched at 18 px, and stopped. Two passes
    cannot bootstrap: a seed that starts with six matches ends with six. Here
    each radius is re-matched and re-fitted until the match count stops growing
    before the radius tightens, so a roughly-right seed pulls itself in.

    The homography is fitted alongside the affine at every step and kept only
    where it beats the affine on the same points — an affine cannot represent a
    perspective view, and the residual it leaves is structured, not random.
    """
    pred = seed
    P = None
    last = -1
    for radius in radii:
        for _ in range(CANOPY_MATCH_MAX_ITER):
            px, py = pred(E, N)
            pairs, used = [], set()
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

            def aff(Ev, Nv, cx=cx, cy=cy):
                Ev, Nv = np.asarray(Ev, float), np.asarray(Nv, float)
                return (cx[0] * Ev + cx[1] * Nv + cx[2],
                        cy[0] * Ev + cy[1] * Nv + cy[2])
            pred = aff
            if len(P) >= 8:
                H = _homography(P)
                hu, hv = H(P[:, 0], P[:, 1])
                au, av = aff(P[:, 0], P[:, 1])
                if (np.hypot(hu - P[:, 2], hv - P[:, 3]).mean()
                        < np.hypot(au - P[:, 2], av - P[:, 3]).mean()):
                    pred = H
            if len(pairs) == last:
                break
            last = len(pairs)
    u, v = pred(P[:, 0], P[:, 1])
    res = np.hypot(u - P[:, 2], v - P[:, 3])
    return pred, res, P, len(P)


def _constellation_offset(A, B, span, step=2):
    """Best integer (dx, dy) putting constellation A onto B, and how many
    tips then coincide. Cheap because the offsets are small: the view was
    nudged between sessions, not re-composed."""
    best = (-1, (0, 0))
    for dx in range(-span, span + 1, step):
        for dy in range(-span, span + 1, step):
            d = np.hypot(A[:, None, 0] + dx - B[None, :, 0],
                         A[:, None, 1] + dy - B[None, :, 1]).min(1)
            n = int((d < CANOPY_CONSTELLATION_TOL_PX).sum())
            if n > best[0]:
                best = (n, (dx, dy))
    return best


def _group_by_constellation(tips_by_frame):
    """Frames whose marker constellations coincide are the same viewpoint.

    Martin, 2026-08-31: "they are all in the same location in all images, and
    the same size." Measured true WITHIN a group, to 0.0 px. Between groups the
    view was nudged, so the constellation shifts rigidly — 12 px between the two
    site groups, 49 px for the 2026 aerial frame against its siblings. That 49 px
    against a 45 px first radius is the entire reason 2026 never registered.
    """
    groups = []
    for f, T in tips_by_frame.items():
        if len(T) < 6:
            groups.append([f])
            continue
        for g in groups:
            B = tips_by_frame[g[0]]
            if len(B) < 6:
                continue
            n, _ = _constellation_offset(T, B, span=4, step=1)
            if n >= CANOPY_GROUP_MIN_FRACTION * min(len(T), len(B)):
                g.append(f)
                break
        else:
            groups.append([f])
    return groups


def _seed_from_wells(tips, E, N):
    """A seed for a group with NO control outline: scan scale, vote translation.

    The site* and seabed captures carry no green control outline at all —
    measured, 0 pixels pass the test — so they can never be seeded from the
    control polygon, and v2.0.0's fallback of borrowing the aerial affine put
    them 91 px out. But the wells themselves are the ground truth: for every
    (well, tip) pair the implied translation is (tip - scaled well), and the
    true transform shows up as a PEAK in the histogram of those translations.
    Scan a coarse range of pixels-per-metre, take the best peak.

    Measured on this series: 44 of 88 wells land within 10 px for
    site1-1-2006m and 39 for site24-3-2021m, against 6 for the borrowed aerial
    affine. That is a seed the refinement can work from.
    """
    Ec, Nc = E.mean(), N.mean()
    best = (-1.0, None)
    for sx in np.arange(0.25, 1.25, 0.025):
        wx = (E - Ec) * sx
        for sy in np.arange(0.25, 1.25, 0.025):
            wy = -(N - Nc) * sy
            dx = (tips[:, 0][:, None] - wx[None, :]).ravel()
            dy = (tips[:, 1][:, None] - wy[None, :]).ravel()
            bx = np.arange(dx.min(), dx.max() + 6.0, 6.0)
            by = np.arange(dy.min(), dy.max() + 6.0, 6.0)
            if len(bx) < 2 or len(by) < 2:
                continue
            H, xe, ye = np.histogram2d(dx, dy, bins=[bx, by])
            i, j = np.unravel_index(H.argmax(), H.shape)
            if H[i, j] > best[0]:
                cx = (xe[i] + xe[i + 1]) / 2.0 - Ec * sx
                cy = (ye[j] + ye[j + 1]) / 2.0 + Nc * sy
                best = (float(H[i, j]), (sx, sy, cx, cy))
    if best[1] is None:
        return None
    sx, sy, cx, cy = best[1]

    def seed(Ev, Nv, sx=sx, sy=sy, cx=cx, cy=cy):
        return (np.asarray(Ev, float) * sx + cx, -np.asarray(Nv, float) * sy + cy)
    return seed


def _register_all(paths, ctrl_geom, E, N):
    """Register every frame, seeding each CONSTELLATION GROUP in its own right.

    Three seeds are tried per group, in this order, and the best accepted
    solution is kept:

      1. the group's OWN control outline, where the group has one. This alone
         recovers aerial31-3-2026, whose outline sits 80 px from its siblings'.
      2. a SOLVED group's transform, where the two constellations genuinely
         coincide (>= CANOPY_CHAIN_MIN_TIPS). Measured: the two site groups
         share 20 tips and chain; site-to-aerial shares 3 and does not — which
         is the guard that stops a seed crossing viewpoints, the exact fault in
         v2.0.0.
      3. the base control affine, as a last resort, with a wide radius schedule.

    "Best" is the LOWEST MEDIAN RESIDUAL among solutions with at least
    CANOPY_MIN_CONTROL_POINTS matches. Selecting a registration on its residual
    against known ground truth is not selecting a result on its outcome: the
    residual measures the fit to the 88 surveyed well positions, which is the
    thing being fitted, and it is reported per frame so the choice is auditable.
    """
    from PIL import Image
    tips_by = {}
    for p in paths:
        a = np.asarray(Image.open(p).convert("RGB")).astype(int)
        tips_by[p.name] = _detect_markers(a)

    groups = _group_by_constellation(tips_by)
    by_name = {p.name: p for p in paths}
    info(f"{len(groups)} constellation group(s) across {len(paths)} frame(s):")
    for gi, g in enumerate(groups):
        info(f"    group {gi}: {len(tips_by[g[0]]):3d} tips, {len(g)} frame(s) "
             f"— {g[0]}" + (f" +{len(g) - 1} more" if len(g) > 1 else ""))

    base = None
    for p in paths:
        aff = _affine_from_control([p], ctrl_geom)
        if aff is not None:
            base = aff
            break
    if base is None:
        warn("no frame carries the control outline; cannot register anything")
        return {}, groups
    scale = (base[1] + base[2]) / 2.0

    solved, out = {}, {}
    for _pass in range(2):                     # a second pass lets a group chain
        for gi, g in enumerate(groups):        # off one solved in the first
            if gi in solved or len(tips_by[g[0]]) < 6:
                continue
            T = tips_by[g[0]]
            cands = []
            own = None
            for f in g:
                own = _affine_from_control([by_name[f]], ctrl_geom)
                if own is not None:
                    break
            if own is not None:
                cands.append(("own control outline", own[0], CANOPY_MATCH_RADII_NARROW))
            for sj, (spred, sT) in solved.items():
                n, (dx, dy) = _constellation_offset(T, sT, span=160, step=2)
                if n >= CANOPY_CHAIN_MIN_TIPS:
                    def chained(Ev, Nv, spred=spred, dx=dx, dy=dy):
                        u, v = spred(Ev, Nv)
                        return (np.asarray(u) - dx, np.asarray(v) - dy)
                    cands.append((f"chained from group {sj} ({dx:+d},{dy:+d}) px, "
                                  f"{n} tips coincide", chained,
                                  CANOPY_MATCH_RADII_NARROW))
            if own is None:
                vs = _seed_from_wells(T, E, N)
                if vs is not None:
                    cands.append(("well-constellation vote", vs,
                                  CANOPY_MATCH_RADII_NARROW))
                    cands.append(("well-constellation vote, wide", vs,
                                  CANOPY_MATCH_RADII_WIDE))
            cands.append(("base control affine", base[0], CANOPY_MATCH_RADII_WIDE))
            cands.append(("base control affine", base[0], CANOPY_MATCH_RADII_NARROW))

            best = None
            for how, seed, radii in cands:
                pred, res, P, n = _match_and_fit(T, E, N, seed, radii)
                if pred is None or n < CANOPY_MIN_CONTROL_POINTS:
                    continue
                med = float(np.median(res)) * scale
                if best is None or med < best[0]:
                    best = (med, float(np.percentile(res, 95)) * scale, n, pred, how)
            if best is None:
                continue
            med, p95, n, pred, how = best
            solved[gi] = (pred, T)
            # Ground sampling distance from the fitted transform itself: move a
            # well 100 m east and 100 m north and see how far the image moves.
            _E0, _N0 = float(np.mean(E)), float(np.mean(N))
            _u0, _v0 = pred(_E0, _N0)
            _ue, _ve = pred(_E0 + 100.0, _N0)
            _un, _vn = pred(_E0, _N0 + 100.0)
            _ge = 100.0 / max(float(np.hypot(_ue - _u0, _ve - _v0)), 1e-9)
            _gn = 100.0 / max(float(np.hypot(_un - _u0, _vn - _v0)), 1e-9)
            gsd = (_ge + _gn) / 2.0
            for f in g:
                out[f] = dict(fitted=pred, median_m=med, p95_m=p95,
                              n=n, group=gi, seed=how, gsd_m=gsd)
            info(f"    group {gi}: {n} points, median {med:.2f} m, p95 {p95:.2f} m, "
                 f"GSD {gsd:.2f} m/px — {how}")

    for gi, g in enumerate(groups):
        if gi not in solved:
            for f in g:
                out[f] = dict(fitted=None, median_m=np.nan, p95_m=np.nan,
                              n=len(tips_by[f]), group=gi, gsd_m=np.nan,
                              seed="no seed produced an accepted fit")
            warn(f"    group {gi} UNREGISTERED ({len(tips_by[g[0]])} tips): "
                 f"{', '.join(g)}")
    return out, groups


# ── Change detection on a common ground grid ─────────────────────────────────

def _build_grid(geoms):
    """A regular OSGB grid covering the union of the analysis polygons.

    Change is differenced HERE, not in pixel space. The frames differ in size and
    viewpoint, so a pixel difference measures the perspective; a difference on
    the ground measures the ground.
    """
    from shapely.ops import unary_union
    u = unary_union(list(geoms))
    minx, miny, maxx, maxy = u.bounds
    res = float(CANOPY_CHANGE_GRID_M)
    minx, miny = np.floor(minx / res) * res, np.floor(miny / res) * res
    maxx, maxy = np.ceil(maxx / res) * res, np.ceil(maxy / res) * res
    ge = np.arange(minx, maxx + res, res)
    gn = np.arange(maxy, miny - res, -res)          # north-up rows
    EE, NN = np.meshgrid(ge, gn)
    return EE, NN, (minx, miny, maxx, maxy, res)


def _grid_mask_of(geom, extent):
    """Rasterise a polygon onto the ground grid.

    In grid space the transform is a plain affine — the grid IS north-up OSGB —
    so this is exact, unlike the pixel-space rasterisation, which has to project
    through a homography.
    """
    from PIL import Image, ImageDraw
    minx, miny, maxx, maxy, res = extent
    w = int(round((maxx - minx) / res)) + 1
    h = int(round((maxy - miny) / res)) + 1
    img = Image.new("1", (w, h), 0)
    d = ImageDraw.Draw(img)
    polys = (list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom])
    for poly in polys:
        cc = list(poly.exterior.coords)[:-1]
        d.polygon([((c[0] - minx) / res, (maxy - c[1]) / res) for c in cc], fill=1)
        for ring in poly.interiors:
            cc = list(ring.coords)[:-1]
            d.polygon([((c[0] - minx) / res, (maxy - c[1]) / res) for c in cc], fill=0)
    return np.array(img, dtype=bool)


def _sample_to_grid(lum, fitted, EE, NN):
    """Nearest-neighbour sample of one frame onto the ground grid.

    Returns (values, valid). `valid` is False wherever the grid node falls
    outside the frame's usable window, so a pair is compared only where BOTH
    frames actually saw the ground.
    """
    h, w = lum.shape
    r0, r1, c0, c1 = _frame_window(h, w)
    px, py = fitted(EE.ravel(), NN.ravel())
    xi = np.rint(np.asarray(px, float)).astype(int)
    yi = np.rint(np.asarray(py, float)).astype(int)
    ok = (xi >= c0) & (xi < c1) & (yi >= r0) & (yi < r1)
    vals = np.full(xi.shape, np.nan, float)
    vals[ok] = lum[yi[ok], xi[ok]]
    return vals.reshape(EE.shape), ok.reshape(EE.shape)


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
    regions, conifer_ref, open_ref, ctrl_overlap = _load_geometries()
    import geopandas as gpd
    import warnings
    warnings.filterwarnings("ignore")
    from shapely.ops import unary_union
    ctrl = unary_union(list(gpd.read_file(
        str(DATA_GEO_DIR / f"{CONTROL_KML}.kml"), driver="KML")
        .to_crs("EPSG:27700").geometry))

    if ctrl_overlap > 0:
        info(f"control region {CONTROL_REGION}: {ctrl_overlap / 10000.0:.2f} ha "
             f"of managed block subtracted (NOT the reference's buffer collar — "
             f"with the collar the control becomes the reference and reads "
             f"1.000 exactly, which is not a control)")
        info("  (the un-subtracted control stepped 1.010 -> 0.954 across the "
             "2017 clearfell; a control must not contain what it controls for)")

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
    # The crop fractions were chosen to reproduce v1.0.0's pixel literals
    # exactly on the frame size they were written for. Log the derived window so
    # that assumption is visible in the run rather than trusted, and log any
    # frame whose size differs — which is how the 2026 capture announces itself.
    _r0, _r1, _c0, _c1 = _frame_window(h, w)
    info(f"frame {w} x {h}; usable window rows {_r0}-{_r1}, cols {_c0}-{_c1} "
         f"(fractions of the frame, not pixels)")
    _sizes = {}
    for _p in paths:
        with Image.open(_p) as _im:
            _sizes.setdefault(_im.size, []).append(_p.name)
    if len(_sizes) > 1:
        warn(f"{len(_sizes)} different frame sizes in the series — the window is "
             f"scaled per frame, but check the odd ones registered:")
        for _sz, _names in sorted(_sizes.items(), key=lambda kv: -len(kv[1])):
            warn(f"    {_sz[0]} x {_sz[1]}  ({len(_names)} frame(s), "
                 f"e.g. {_names[0]})")

    # Register every frame, one CONSTELLATION GROUP at a time. v1.0.0 fitted
    # once on the first frame and used that transform for everything, which is
    # why a different viewpoint could never register however well its markers
    # were found.
    import pandas as _pd
    _w = _pd.read_csv(INT_LOCATIONS)
    _ec = next(c for c in _w.columns if c.lower() in ("easting", "e", "x"))
    _nc = next(c for c in _w.columns if c.lower() in ("northing", "n", "y"))
    E_all = _w[_ec].values.astype(float)
    N_all = _w[_nc].values.astype(float)
    reg, groups = _register_all(paths, ctrl, E_all, N_all)

    # The masks are rasterised through the transform of the group the FIRST
    # frame belongs to, because the region pixel counts have to be one thing.
    first = reg.get(paths[0].name, {})
    project = first.get("fitted") or to_px
    if first.get("fitted") is None:
        warn("the first frame's group did not register; masks fall back to the "
             "control-polygon affine, which does not model the perspective")

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

    map_area = _apply_window(np.ones((h, w), bool))
    masks = {n: mask_of(g) & map_area for n, (g, _) in regions.items()}
    ref_con = mask_of(conifer_ref) & map_area
    ref_opn = mask_of(open_ref) & map_area
    for n, m in masks.items():
        info(f"  region {n:20s} {int(m.sum()):7d} px in view")
    info(f"  reference conifer      {int(ref_con.sum()):7d} px")
    info(f"  reference open         {int(ref_opn.sum()):7d} px")

    phase(2, "Texture index per frame")
    reg_rows, idx_rows, cache, transforms = [], [], {}, {}
    for p, d in zip(paths, man["imagery_date"]):
        r = reg.get(p.name, {})
        fitted, med, p95 = r.get("fitted"), r.get("median_m", np.nan), r.get("p95_m", np.nan)
        nmatch = int(r.get("n", 0))
        reg_rows.append({"frame": p.name, "imagery_date": d.date(),
                         "constellation_group": r.get("group"),
                         "gsd_m": r.get("gsd_m"),
                         "seed": r.get("seed", ""),
                         "n_control_points": nmatch,
                         "residual_median_m": None if not np.isfinite(med) else med,
                         "residual_p95_m": None if not np.isfinite(p95) else p95})
        a = np.asarray(Image.open(p).convert("RGB")).astype(float)
        lum = _lum(a)
        tex = _texture(lum, CANOPY_TEXTURE_WINDOW)
        cache[p.name] = (lum, tex)
        registered = (fitted is not None and np.isfinite(p95)
                      and p95 <= CANOPY_MAX_RESIDUAL_M)
        if registered:
            transforms[p.name] = fitted
        c_stat, _ = _region_stat(tex, lum, ref_con)
        o_stat, _ = _region_stat(tex, lum, ref_opn)
        sep = c_stat - o_stat
        # The registration test comes FIRST. A frame that did not register
        # cannot have a meaningful reference separation either, and v1.0.0
        # reported that downstream symptom instead of the cause.
        vals_this_frame = {}
        for name, m in masks.items():
            r_stat, npx = _region_stat(tex, lum, m)
            reason = ""
            _gsd = r.get("gsd_m", np.nan)
            if np.isfinite(_gsd) and _gsd > CANOPY_MAX_GSD_M:
                reason = (f"ground sampling distance {_gsd:.2f} m/px > "
                          f"{CANOPY_MAX_GSD_M} — the {CANOPY_TEXTURE_WINDOW} px "
                          f"texture window spans "
                          f"{_gsd * CANOPY_TEXTURE_WINDOW:.0f} m of ground and "
                          f"cannot resolve a crown. Measured: this viewpoint's "
                          f"index correlates with the aerial index of the same "
                          f"region on the same day at r = +0.089")
            elif not np.isfinite(p95):
                reason = (f"registration failed: only {nmatch} placemark(s) "
                          f"matched — the frame is not registered, so the "
                          f"region mask cannot be trusted")
            elif p95 > CANOPY_MAX_RESIDUAL_M:
                reason = f"registration p95 {p95:.1f} m > {CANOPY_MAX_RESIDUAL_M}"
            elif npx < CANOPY_MIN_REGION_PX:
                reason = f"region {npx} px < {CANOPY_MIN_REGION_PX}"
            elif not np.isfinite(sep) or sep < CANOPY_MIN_REF_SEPARATION:
                reason = f"reference separation {sep:.4f} < {CANOPY_MIN_REF_SEPARATION}"
            val = np.nan if reason else (r_stat - o_stat) / sep
            vals_this_frame[name] = None if reason else float(val)
            idx_rows.append({"region": name, "imagery_date": d.date(),
                             "frame": p.name,
                             "leaf_state": _leaf_state(d.month),
                             "viewpoint": _viewpoint(p.name),
                             "n_px": npx,
                             "index": None if reason else float(val),
                             "ratio_to_conifer": None,
                             "withheld_reason": reason})
        # The in-frame ratio to the control. Not a convenience: it is what makes
        # frames comparable, by cancelling exposure and any residual frame-level
        # effect, and leaving a reader to compute it invites them not to.
        ctrl_val = vals_this_frame.get(CONTROL_REGION)
        if ctrl_val:
            for row in idx_rows[-len(masks):]:
                if row["index"] is not None:
                    row["ratio_to_conifer"] = row["index"] / ctrl_val

    # D-035: stores carry what the pipeline computed. Rounding is a rendering
    # decision and belongs where a number is shown, not where it is written.
    pd.DataFrame(reg_rows).to_csv(OUT_41_REGISTRATION, index=False)
    saved(OUT_41_REGISTRATION.name)
    idx = pd.DataFrame(idx_rows)
    idx.to_csv(OUT_41_INDEX, index=False)
    saved(OUT_41_INDEX.name)

    phase(3, "Change between consecutive imagery dates, on the ground")
    EE, NN, extent = _build_grid([g for _, (g, _) in regions.items()])
    gmasks = {n: _grid_mask_of(g, extent) for n, (g, _) in regions.items()}
    info(f"change grid {EE.shape[1]} x {EE.shape[0]} at "
         f"{CANOPY_CHANGE_GRID_M:.0f} m; frames are differenced here, never "
         f"pixel-to-pixel")

    # One frame per imagery date: the registered one with the best residual.
    reg_df = pd.DataFrame(reg_rows)
    reg_df["ok"] = reg_df["frame"].isin(transforms)
    per_date = {}
    for d, grp in reg_df.groupby("imagery_date"):
        good = grp[grp["ok"]]
        per_date[d] = (good.sort_values("residual_p95_m").iloc[0]["frame"]
                       if len(good) else None)
    dates = sorted(per_date)

    ch_rows = []
    for i in range(1, len(dates)):
        d0, d1 = dates[i - 1], dates[i]
        f0, f1 = per_date[d0], per_date[d1]
        reason = ""
        if f0 is None and f1 is None:
            reason = "neither frame registered"
        elif f0 is None:
            reason = f"the {d0} frame did not register"
        elif f1 is None:
            reason = f"the {d1} frame did not register"
        if reason:
            for name in gmasks:
                ch_rows.append({"region": name, "from_date": d0, "to_date": d1,
                                "from_frame": f0, "to_frame": f1,
                                "change_fraction": None,
                                "withheld_reason": reason})
            continue
        g0, v0 = _sample_to_grid(cache[f0][0], transforms[f0], EE, NN)
        g1, v1 = _sample_to_grid(cache[f1][0], transforms[f1], EE, NN)
        both = v0 & v1 & np.isfinite(g0) & np.isfinite(g1)
        if both.sum() < CANOPY_MIN_REGION_PX:
            for name in gmasks:
                ch_rows.append({"region": name, "from_date": d0, "to_date": d1,
                                "from_frame": f0, "to_frame": f1,
                                "change_fraction": None,
                                "withheld_reason": (f"only {int(both.sum())} grid "
                                                    f"node(s) seen by both frames")})
            continue
        z0 = (g0 - g0[both].mean()) / max(g0[both].std(), 1e-6)
        z1 = (g1 - g1[both].mean()) / max(g1[both].std(), 1e-6)
        diff = np.abs(z0 - z1)
        thr = np.percentile(diff[both], CANOPY_CHANGE_PCTL)
        changed = (diff > thr) & both
        for name, m in gmasks.items():
            mm = m & both
            n = int(mm.sum())
            ch_rows.append({
                "region": name, "from_date": d0, "to_date": d1,
                "from_frame": f0, "to_frame": f1,
                "change_fraction": (float((changed & mm).sum() / n) if n else None),
                "withheld_reason": ("" if n else
                                    "region not seen by both frames on the grid"),
            })
    pd.DataFrame(ch_rows).to_csv(OUT_41_CHANGE, index=False)
    saved(OUT_41_CHANGE.name)

    phase(4, "Figure and report numbers")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))
    marks = {"full_leaf": "o", "emerging": "s", "leaf_off": "^",
             "senescing": "v", "unclassified": "x"}
    for name in masks:
        sub = idx[(idx["region"] == name) & idx["index"].notna()
                  & (idx["viewpoint"] == "aerial")]
        if not len(sub):
            continue
        line, = ax.plot(pd.to_datetime(sub["imagery_date"]), sub["index"],
                        lw=1.0, label=name)
        for st, mk in marks.items():
            s2 = sub[sub["leaf_state"] == st]
            if len(s2):
                ax.plot(pd.to_datetime(s2["imagery_date"]), s2["index"], mk,
                        color=line.get_color(), ms=6, ls="none")
    ax.set_ylabel("texture index  (0 = open ground, 1 = mature conifer)")
    ax.set_xlabel("imagery date")
    ax.set_title("Canopy texture index — aerial viewpoint "
                 "(the index is not comparable between viewpoints)")
    ax.axhline(0, lw=0.6, color="0.6")
    ax.axhline(1, lw=0.6, color="0.6", ls=":")
    ax.legend(fontsize=8, title="marker = leaf state (o full, s emerging, ^ off)",
              title_fontsize=7)
    render_figure(fig, OUT_41_SERIES_FIG)
    saved(OUT_41_SERIES_FIG.name)

    # Report numbers on a FULL-LEAF basis only. A deciduous region's index is
    # not comparable across leaf states — the emerging class scatters five times
    # as much — so a summary that mixes them is not a summary of anything.
    rn = []
    # AERIAL viewpoint only. The index is not comparable between viewpoints
    # (see _viewpoint), and every earlier finding rests on the aerial series
    # because it was the only one that registered.
    full = idx[(idx["leaf_state"] == "full_leaf") & idx["index"].notna()
               & (idx["viewpoint"] == "aerial")]
    bl = full[full["region"] == "broadleaf_restock"]
    if len(bl):
        rr = bl["ratio_to_conifer"].dropna()
        rn.append({"Parameter": "canopy_ratio_restock_conifer_full_leaf_median",
                   "Well": "", "Era": f"{bl['imagery_date'].min()}–{bl['imagery_date'].max()}",
                   "Value": float(rr.median()) if len(rr) else float("nan"),
                   "Unit": "ratio",
                   "Note": ("restock texture index divided by the conifer control "
                            "in the SAME frame, full-leaf frames only. Above 1 "
                            "because the index sees canopy and understorey "
                            "together and a young open block has structure at two "
                            "levels; it is not a canopy fraction. AERIAL "
                            "viewpoint only — the index is not comparable "
                            "between viewpoints")})
        rn.append({"Parameter": "canopy_ratio_restock_conifer_full_leaf_sd",
                   "Well": "", "Era": f"{bl['imagery_date'].min()}–{bl['imagery_date'].max()}",
                   "Value": float(rr.std()) if len(rr) > 1 else float("nan"),
                   "Unit": "ratio",
                   "Note": ("spread of the full-leaf class; the emerging class "
                            "scatters several times as much, which is why the "
                            "basis is full leaf only")})
        rn.append({"Parameter": "canopy_full_leaf_frames_n", "Well": "",
                   "Era": f"{bl['imagery_date'].min()}–{bl['imagery_date'].max()}",
                   "Value": float(len(bl)), "Unit": "frames",
                   "Note": "frames on the comparison basis; the rest are withheld "
                           "from the summary, not from the table"})
    cf = full[full["region"] == "clearfell"]
    if len(cf):
        rn.append({"Parameter": "canopy_index_clearfell_full_leaf_median",
                   "Well": "", "Era": f"{cf['imagery_date'].min()}–{cf['imagery_date'].max()}",
                   "Value": float(cf["index"].median()), "Unit": "index",
                   "Note": ("the clearfell area is deliberately kept clear of "
                            "trees (Martin, 2026-08-31), so a low value is a "
                            "management outcome and not failed regeneration")})
    pd.DataFrame(rn).to_csv(OUT_41_REPORT_NUMBERS, index=False)
    saved(OUT_41_REPORT_NUMBERS.name)

    withheld = int(idx["withheld_reason"].astype(bool).sum())
    step(f"{len(idx)} region-frame values, {withheld} withheld")
    by = (idx[idx["index"].notna()].groupby(["viewpoint", "leaf_state"])["region"]
          .count().to_dict())
    info(f"usable values by (viewpoint, leaf state): {by}")
    info("the index is comparable WITHIN a viewpoint and within a leaf state, "
         "and between neither: the same region on the same day reads 1.045 from "
         "the aerial frame and -0.113 from the site frame")
    info("the index is a texture position, not a canopy fraction, and it is NOT "
         "bounded above by 1: it sees canopy and understorey together, so a "
         "young open broadleaf block can exceed a closed conifer stand")
    info("no growth number is emitted — before 2012 there is no full-leaf frame, "
         "so growth and phenology are not separable on this record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
