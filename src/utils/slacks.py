#!/usr/bin/env python3
"""
slacks.py — slacks as closed depressions in the DEM, not as catchments.

WHY THIS EXISTS

  W94 needs a unit to score flooding against: *does THIS slack hold water on
  this date* (D-159). The only basin layer in the tree was
  `ranwell_dem_basins_prototype.geojson`, built for the Ranwell georeferencing
  and catchment scale — five polygons of 1.3 to 108 ha. Martin, 2026-09-11:
  *"the basins are too large and don't represent the slacks."*

  He is right, and the fix needs no new data. A slack IS a closed depression, so
  it can be delineated from the 2 m DEM already committed: PRIORITY-FLOOD the
  surface to fill every sink, difference the filled surface against the original,
  and label what is deeper than `SLACK_MIN_DEPTH_M`. Measured over the site
  window that gives **167 depressions of at least 0.05 ha inside the warren, at a
  median of 0.132 ha** — the scale of the thing being named, against the
  prototype's 80 and 108 ha.

  The DEM was never the limitation: it covers 100 % of the site boundary at 2 m
  with no nodata cell, and reads to a 0.030 m MAD against the 2010 DGPS survey.

WHY PRIORITY-FLOOD, AND NOT A CATCHMENT DELINEATION

  A catchment answers "where does water flowing over this point go". A slack
  asks "what is enclosed below a spill level" — which is the depression, not its
  drainage area, and is what a flooded outline in a photograph actually shows.
  Priority-flood also hands back the SPILL elevation for free: the level at
  which the depression would overtop, which bounds how full it can ever get.

  Implemented in numpy and heapq rather than pulled in from richdem or
  whitebox — the site window is 3.1 M cells and fills in under ten seconds, and
  a dependency that must be present on both the publishing machine and a
  reviewer's clone is a cost this does not need to pay (D-153's reasoning).

  See D-159 and `working/updates/NRG_spec_W94_warren_flood_surface_2026-09-11.md`.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-11. New, for D-159.

import heapq

import numpy as np

_NEIGHBOURS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def priority_flood(dem: np.ndarray) -> np.ndarray:
    """Fill every sink. Returns the filled surface; `filled - dem` is the depth.

    Classic priority-flood: seed the heap with the grid edge, pop the lowest
    cell, and raise each unvisited neighbour to at least the level it was
    reached at. Every cell therefore ends at the lowest level from which the
    edge can be reached, which is the definition of a filled surface.

    The array must carry no nodata — `newborough_dem.tif` has none. A nodata
    cell would have to be seeded as edge, and silently treating it as ground
    would invent a dam.
    """
    if not np.isfinite(dem).all():
        raise ValueError("priority_flood needs a DEM with no nodata or NaN; "
                         "a non-finite cell would act as a dam and invent a "
                         "depression that is not there")
    h, w = dem.shape
    filled = np.empty_like(dem)
    seen = np.zeros(dem.shape, dtype=bool)
    heap = []
    for i in range(h):
        for j in (0, w - 1):
            heapq.heappush(heap, (float(dem[i, j]), i, j))
            seen[i, j] = True
            filled[i, j] = dem[i, j]
    for j in range(w):
        for i in (0, h - 1):
            if not seen[i, j]:
                heapq.heappush(heap, (float(dem[i, j]), i, j))
                seen[i, j] = True
                filled[i, j] = dem[i, j]
    while heap:
        level, i, j = heapq.heappop(heap)
        for di, dj in _NEIGHBOURS:
            y, x = i + di, j + dj
            if 0 <= y < h and 0 <= x < w and not seen[y, x]:
                seen[y, x] = True
                v = dem[y, x] if dem[y, x] > level else level
                filled[y, x] = v
                heapq.heappush(heap, (float(v), y, x))
    return filled


def label_depressions(dem: np.ndarray, filled: np.ndarray, min_depth: float):
    """(labels, n) — connected depressions deeper than `min_depth`."""
    from scipy import ndimage as ndi
    return ndi.label(filled - dem > min_depth)


def depression_table(dem, filled, labels, n, cell_area_m2: float):
    """Per-depression geometry: area, floor, spill level, depth, cell count.

    Computed with bincount rather than a per-label loop: at several thousand
    depressions the loop is the slow part, and every quantity here is an
    extremum or a sum over the label.
    """
    flat_lab = labels.ravel()
    flat_dem = dem.ravel()
    flat_fill = filled.ravel()
    counts = np.bincount(flat_lab, minlength=n + 1)
    floor = np.full(n + 1, np.inf, dtype=np.float64)
    spill = np.full(n + 1, -np.inf, dtype=np.float64)
    np.minimum.at(floor, flat_lab, flat_dem)
    np.maximum.at(spill, flat_lab, flat_fill)
    rows = []
    for lab in range(1, n + 1):
        if counts[lab] == 0:
            continue
        rows.append({"slack": lab,
                     "cells": int(counts[lab]),
                     "area_m2": float(counts[lab] * cell_area_m2),
                     "floor_m": float(floor[lab]),
                     "spill_m": float(spill[lab]),
                     "depth_m": float(spill[lab] - floor[lab])})
    return rows


# ── The merge tree ───────────────────────────────────────────────────────────
#
# Martin, 2026-09-11: *"of course slacks merge as the water table rises."*
#
# A fixed-depth delineation gives static polygons and therefore cannot answer
# "which slack flooded" without also being told a level: above the SADDLE between
# two slacks they are one sheet of water. So the object is a nested hierarchy,
# and the unit of scoring is a node of it at a stated level.
#
# **A merge is a threshold observation, and that is the prize.** Two slacks shown
# as one water body in a frame put the level AT OR ABOVE their saddle; shown
# apart, BELOW it. That brackets the level from RELATIVE topography alone — it
# never touches the DEM's absolute datum, so it is immune to the +0.050 m
# systematic that an outline elevation has to be corrected for. It is a better
# measurement than the one the specification was built on, from the same
# photograph.
#
# Built by a single ascending sweep with union-find, which is the standard
# construction: process cells lowest first; a cell with no processed neighbour
# starts a component at a local minimum; a cell adjoining two or more distinct
# components IS the saddle between them, and merges them at its own elevation.

def merge_tree(dem: np.ndarray):
    """(leaf_of_cell, nodes) — the depression hierarchy of `dem`.

    `nodes` is a list of dicts, one per node:
        id, parent (-1 at the root), floor_m, merge_level_m (the saddle at which
        this node joins its parent; NaN at a root), cells (size of its subtree
        when it merged), open (its subtree reaches the grid edge, so it drains
        away rather than holding water).

    Leaves are local minima. A node's DEPTH is `merge_level_m - floor_m`: how
    deep the water can stand in it before it spills into its neighbour.
    """
    if not np.isfinite(dem).all():
        raise ValueError("merge_tree needs a DEM with no nodata or NaN")
    h, w = dem.shape
    flat = dem.ravel()
    order = np.argsort(flat, kind="stable")

    parent = []          # union-find over NODE ids
    floor, merge_at, size, openness = [], [], [], []
    node_parent = []     # tree parent, -1 while it is still a root
    comp = np.full(flat.size, -1, dtype=np.int64)   # cell -> node id (leaf side)

    def new_node(f, is_open):
        i = len(parent)
        parent.append(i)
        floor.append(f)
        merge_at.append(np.nan)
        size.append(0)
        openness.append(is_open)
        node_parent.append(-1)
        return i

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for idx in order:
        e = float(flat[idx])
        r, c = divmod(int(idx), w)
        edge = (r == 0 or c == 0 or r == h - 1 or c == w - 1)
        roots = []
        for dr, dc in _NEIGHBOURS:
            y, x = r + dr, c + dc
            if 0 <= y < h and 0 <= x < w:
                j = y * w + x
                if comp[j] >= 0:
                    rt = find(int(comp[j]))
                    if rt not in roots:
                        roots.append(rt)
        if not roots:
            n = new_node(e, edge)
            comp[idx] = n
            size[n] += 1
            continue
        if len(roots) == 1:
            rt = roots[0]
            comp[idx] = rt
            size[rt] += 1
            if edge:
                openness[rt] = True
            continue
        # A SADDLE. Every root here spills into the others at this elevation.
        merged = new_node(min(floor[r_] for r_ in roots),
                          edge or any(openness[r_] for r_ in roots))
        for r_ in roots:
            node_parent[r_] = merged
            merge_at[r_] = e
            parent[r_] = merged
            size[merged] += size[r_]
        size[merged] += 1
        comp[idx] = merged

    nodes = [{"id": i, "parent": node_parent[i], "floor_m": floor[i],
              "merge_level_m": merge_at[i], "cells": size[i],
              "open": bool(openness[i])}
             for i in range(len(parent))]
    return comp.reshape(dem.shape), nodes


def _ancestors(nodes, i):
    out = []
    while i != -1:
        out.append(i)
        i = nodes[i]["parent"]
    return out


def saddle_level(nodes, a: int, b: int) -> float:
    """The elevation at which nodes `a` and `b` become one water body.

    The lowest common ancestor's children merged at that level, so it is the
    `merge_level_m` of whichever child of the LCA leads to `a`.

    Returns **-inf** when `a` and `b` are already the same node or one contains
    the other: they are one body at any level at which both are wet, and there is
    no saddle between them. Returns **NaN** when they never join — different
    systems, or one drains to the grid edge first.

    (An earlier draft returned NaN for the same-node case, which silently read as
    "never connect" and lost every pair of wells sharing one depression — the
    common case, since wells were sited around the same slacks.)
    """
    pa = _ancestors(nodes, a)
    sb = set(_ancestors(nodes, b))
    for i, node in enumerate(pa):
        if node in sb:
            return float("-inf") if i == 0 else float(nodes[pa[i - 1]]["merge_level_m"])
    return float("nan")


def connect_level(nodes, dem, leaf_of_cell, cell_a, cell_b) -> float:
    """The water level at which two CELLS are both wet and in one water body.

    Not the same as the saddle between their depressions: a cell is dry until the
    water reaches its own ground, so an edge-sited well joins its neighbour's
    pond only once the level passes the well itself. This is the quantity to use
    for wells — `max(ground_a, ground_b, saddle)` — and it is what a frame
    showing the two as one sheet of water actually constrains.
    """
    s = saddle_level(nodes, int(leaf_of_cell[cell_a]), int(leaf_of_cell[cell_b]))
    if s != s:                      # NaN — they never join
        return float("nan")
    return max(float(dem[cell_a]), float(dem[cell_b]), s)


def leaf_ids(nodes) -> set:
    """Nodes that are local minima — the finest depressions in the hierarchy."""
    has_child = {n["parent"] for n in nodes if n["parent"] != -1}
    return {n["id"] for n in nodes} - has_child
