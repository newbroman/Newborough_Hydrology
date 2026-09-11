#!/usr/bin/env python3
"""
warren_mask.py — the open-dune warren on a given frame date, with the canopy out.

WHY THIS EXISTS

  W94 reads flooded slacks off the dated aerial series (D-159). At the site
  frames' ~2.9 m/px the hard problem is **dark canopy against dark water**: two
  low-reflectance classes with overlapping distributions and no texture budget
  left to separate them. Martin, 2026-09-11: *"There are no flooded slacks in
  the forest, so it should be easy to separate them from the forest."* Exclude
  the canopy a priori and that class leaves the scene — the problem stops being
  a classifier and becomes a threshold on masked open dune.

  Under a closed canopy the ground is not visible from the air anyway, so the
  exclusion cannot lose a flood that could ever have been seen. It is free in
  observational terms and buys the whole separation.

WHY IT IS BY DATE, AND NOT THE in_forest FLAG

  `in_forest` is a static land-cover flag; canopy over a 21-year series is not.
  The frames straddle changes in both directions:

    * the 1998 replant is OPEN ground in the 2006 and 2009 frames and closed
      later — nw9's six flooded months are 2006-05 to 2009-01, exactly when its
      ground was open and visible;
    * the 2017 clearfell INVERTS — canopy before, open after — so water standing
      there in 2021 is real, and a static forest mask would discard it.

  So the canopy is assembled per frame date, and the closure dates are a
  MEASUREMENT rather than an assertion: a block counts as canopy once its
  Script 41 texture index reaches `CANOPY_CLOSURE_RATIO` of the untouched-forest
  control in the SAME frame.

  Applied MONOTONICALLY — the first date after which the ratio never falls below
  the threshold.

  **The reason is not that a canopy cannot re-open. It can: thinning re-opens
  it.** felling_1998_3 reads 0.856 in 2017-04 and 0.603 in 2018-06, and Martin
  identifies that as a THINNING (2026-09-11) — a real management event, in the
  same window as the December 2017 clearfell, when machinery was on site. The
  monotone rule is kept because the index alone cannot separate a thinning from
  frame noise without a forestry record, and monotone is the PERMISSIVE reading:
  it defers closure, keeps more ground in the warren, and so makes the
  negative-control test harder to pass. That is the right way round for a method
  that has to earn trust.

  **With a thinning date from the forestry record this should become monotone
  BETWEEN RECORDED MANAGEMENT EVENTS**, which is strictly better. Owed.

WHAT IS NOT HERE

  The sea, the lake and cast shadow are also dark and also need masking, but
  they are properties of a frame and a tide rather than of the canopy, so they
  belong with the digitising step. This module answers one question: which
  ground was open dune on this date.

  See D-159 and `working/updates/NRG_spec_W94_warren_flood_surface_2026-09-11.md`.
"""
from __future__ import annotations

__version__ = "1.3.0"  # Hollingham (2026) - 2026-09-11. The warren is
#   data/geo/warren.kml, digitised by Martin (447.2 ha), NOT site_boundary less
#   the forest (657 ha). The site boundary reaches over the estuary, which the
#   first flood read duly classified as flooding; no mask could remove it
#   because the boundary itself included it.
# v1.2.0  # Hollingham (2026) - 2026-09-11. Geometry cached by
#   CANOPY STATE rather than by date: sixteen dates collapse to five states, and
#   site.difference(canopy) on an 11,715-part boundary is expensive enough that
#   recomputing it per call was what stopped the step-1 tool finishing.
# v1.1.0  # Hollingham (2026) - 2026-09-11. The monotone rule's
#   JUSTIFICATION is corrected (D-159 amended): the 2017-18 drop in
#   felling_1998_3 is a thinning, not frame noise, so "a canopy does not re-open"
#   was wrong. Behaviour unchanged - see the docstring for why monotone is still
#   the right rule and what would improve it.
# v1.0.0  # Hollingham (2026) - 2026-09-11. New, for D-159.
#   closure_dates() derives per-block canopy closure from the committed Script 41
#   index; canopy_on() and warren_on() return the masked geometries for a date.

from functools import lru_cache
from pathlib import Path

import pandas as pd
from shapely.ops import unary_union

from utils.config import CANOPY_CLOSURE_RATIO, CLEARFELL_DATE_ISO
from utils.console_utils import info, warn
from utils.kml_io import read_kml
from utils.paths import DATA_GEO_DIR, OUT_41_INDEX

OSGB = "EPSG:27700"

#: Blocks whose canopy state CHANGES over the series, and the Script 41 region
#: whose index reports on each. A block absent from the index cannot be dated and
#: is handled by `closure_dates` with a warning rather than a guess.
_VARIABLE_BLOCKS = {
    "broadleaf_restock": "broadleaf_restock",
    "felling_1998_1":    "felling_1998_1",
    "felling_1998_2":    "felling_1998_2",
    "felling_1998_3":    "felling_1998_3",
}

#: The Script 41 region used as the untouched-forest reference. `ratio_to_conifer`
#: in the committed index is already each region's index divided by this one on
#: the SAME frame, which is the comparison we want — it cancels exposure.
_CONTROL_REGION = "forest_in_view"

#: Viewpoint the closure ratios are read on. The index is not comparable between
#: viewpoints (Script 41 `_viewpoint`), so closure must be decided on one.
_CLOSURE_VIEWPOINT = "vp1"


@lru_cache(maxsize=None)
def _geom(name: str):
    """Union of one KML's polygons, in OSGB36. Cached — every caller wants the
    same few files, and a KML read through the three-driver fallback is not free.
    """
    g = read_kml(DATA_GEO_DIR / f"{name}.kml").to_crs(OSGB)
    polys = g[g.geom_type.isin(("Polygon", "MultiPolygon"))]
    if not len(polys):
        raise ValueError(f"{name}.kml holds no polygon")
    return unary_union(list(polys.geometry))


@lru_cache(maxsize=None)
def _features(label: str):
    """Union of the `Features.kml` entries whose Name equals `label`. Cached."""
    g = read_kml(DATA_GEO_DIR / "Features.kml").to_crs(OSGB)
    sel = g[g["Name"].astype(str) == label]
    if not len(sel):
        raise ValueError(f"Features.kml holds no feature named {label!r}")
    return unary_union(list(sel.geometry))


def closure_dates(index_csv: str | Path | None = None) -> dict:
    """{block: pd.Timestamp or None} — when each variable block became canopy.

    Derived from the committed Script 41 index, never typed. `None` means the
    block has not closed within the observed series, which is a legitimate
    answer and must not be read as "closed at the start".
    """
    path = Path(index_csv) if index_csv is not None else OUT_41_INDEX
    if not path.is_file():
        warn(f"{path.name} not found — canopy closure cannot be derived, so "
             f"every variable block is treated as OPEN. That is the direction "
             f"that admits canopy as a flood candidate; do not trust a flood "
             f"result produced this way.")
        return {b: None for b in _VARIABLE_BLOCKS}

    idx = pd.read_csv(path, float_precision="round_trip")
    idx = idx[(idx["viewpoint"] == _CLOSURE_VIEWPOINT)
              & idx["ratio_to_conifer"].notna()]
    out = {}
    for block, region in _VARIABLE_BLOCKS.items():
        s = (idx[idx["region"] == region]
             .assign(d=lambda f: pd.to_datetime(f["imagery_date"]))
             .sort_values("d")
             .set_index("d")["ratio_to_conifer"])
        if s.empty:
            warn(f"no {_CLOSURE_VIEWPOINT} index rows for {region} — treated as "
                 f"OPEN for the whole series")
            out[block] = None
            continue
        # The first date after which the ratio NEVER falls below the threshold.
        closed = None
        for i, d in enumerate(s.index):
            if (s.iloc[i:] >= CANOPY_CLOSURE_RATIO).all():
                closed = d
                break
        out[block] = closed
        if closed is None:
            info(f"  {block:20s} never reaches {CANOPY_CLOSURE_RATIO} of the "
                 f"control in the observed series — OPEN throughout "
                 f"(max {s.max():.3f})")
        else:
            flips = int((s < CANOPY_CLOSURE_RATIO).sum())
            info(f"  {block:20s} canopy from {closed.date()} "
                 f"(ratio {s.loc[closed]:.3f}; {flips} earlier frame(s) below "
                 f"the threshold)")
    return out


#: Geometry cache keyed by CANOPY STATE, not by date. Sixteen frame dates
#: collapse to a handful of states, and `site.difference(canopy)` on an
#: 11,715-part boundary is expensive enough that recomputing it per date was the
#: step that stopped the tool finishing.
_STATE_CACHE: dict = {}


def _state(date, closures) -> tuple:
    d = pd.Timestamp(date)
    return (d >= pd.Timestamp(CLEARFELL_DATE_ISO),
            tuple(sorted(b for b, c in closures.items()
                         if c is not None and d >= c)))


def canopy_on(date, closures: dict | None = None):
    """The canopy geometry on `date` — what must be masked OUT of the warren."""
    d = pd.Timestamp(date)
    closures = closures if closures is not None else closure_dates()
    key = ("canopy",) + _state(d, closures)
    if key in _STATE_CACHE:
        return _STATE_CACHE[key]

    parts = [_features("Forest")]

    # The clearfell INVERTS: canopy before the felling, open ground after. It is
    # inside the Forest polygon, so after felling it must be SUBTRACTED.
    fell = pd.Timestamp(CLEARFELL_DATE_ISO)
    clearfell = _geom("clearfell")

    for block, closed in closures.items():
        if closed is not None and d >= closed:
            parts.append(_geom(block))

    canopy = unary_union(parts)
    if d >= fell:
        canopy = canopy.difference(clearfell)
    # Before the felling the clearfell block is canopy, and it already lies
    # inside Forest, so nothing is added.

    # A variable block that has NOT closed by this date must be open, even where
    # it falls inside the Forest outline — which the 1998 replant blocks do.
    for block, closed in closures.items():
        if closed is None or d < closed:
            canopy = canopy.difference(_geom(block))
    _STATE_CACHE[key] = canopy
    return canopy


#: The warren's own boundary, digitised by Martin 2026-09-11 (447.2 ha).
#:
#: `site_boundary.kml` is 861.6 ha and is NOT the warren: it reaches over the
#: Cefni estuary and the northern farmland, so a flood read clipped to it
#: classified estuary water as slack flooding and no mask could remove it —
#: subtracting the forest does not touch that edge, and neither
#: `cluster_regions.kml` (same footprint) nor `warren_control.kml` (the 19 ha
#: comparator) draws the line where the dune system actually ends.
WARREN_KML = "warren"


def warren_on(date, closures: dict | None = None):
    """The open-dune warren on `date`: Martin's warren boundary less the canopy."""
    closures = closures if closures is not None else closure_dates()
    key = ("warren",) + _state(date, closures)
    if key in _STATE_CACHE:
        return _STATE_CACHE[key]
    site = _geom(WARREN_KML)
    out = site.difference(canopy_on(date, closures))
    _STATE_CACHE[key] = out
    return out
