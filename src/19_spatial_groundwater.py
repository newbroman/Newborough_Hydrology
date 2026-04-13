"""
19_spatial_groundwater.py
=========================
Spatial Groundwater Analysis — Newborough Warren 2005–2026

Produces a data-constrained spatial analysis of the aquifer working entirely from
observed water table elevations (maOD) and empirically-fitted SSM coefficients.
This avoids the dry-cell problem that rendered the Connell (2003) MODFLOW steady-state
model uncalibratable over the rock ridge.

Three components are computed:

  Component 1 — Spatial head surfaces (maOD)
      IDW interpolation of per-well mean annual, winter, and summer head to a
      50×50 m grid. Head gradient vectors (dh/dx, dh/dy) derived from mean surface.

  Component 2 — Darcy lateral flux (independent method)
      Q = K × b × (dh/dl)
      K = 6 m/day (Connell 2003 calibrated value; sensitivity range 3–9 m/day).
      b = aquifer thickness surface (IDW from borehole constraints + cluster priors).
      Flow vectors confirm ridge-to-dune direction independently of the SSM.

  Component 3 — Spatial water balance and lateral inflow residual (SSM method)
      At each well location the mean annual water balance is:

          Lateral_inflow = (β₂ × PET̄ + β₃ × |h̄|) − β₁ × P̄_eff

      where P̄_eff = P̄ × (1 − 0.24) for Forest cluster (C4) wells (Freeman 2008).
      Per-well β coefficients are IDW-interpolated to produce continuous recharge,
      ET-draw, and drainage fields. The lateral inflow residual field is compared
      with the Darcy flux magnitude from Component 2. Spatial agreement of the two
      independent methods is the scientific core of Chapter 6.

Map rendering
-------------
All maps use a greyscale hillshade from the site DEM as a terrain background
(alpha = 0.35), rendered from the single elevation band without terrain colouring
so that the metric colour scale is unambiguous. KML site features (forest boundary,
lake, clearfell area, dipwell transects) are overlaid using the same lightweight
parser used in earlier scripts. If the DEM is absent the background is plain white;
the script never falls back to OSM tiles (which would introduce competing colours).

Scenario framework
------------------
Scenarios modify β fields or climate inputs before re-running the spatial water
balance. Currently implemented:
    baseline          — observed 2005–2026 mean conditions
    forest_removal    — C4 β₂ increased, interception correction removed
    forest_thinning   — partial forest_removal effect
    species_change    — C4 β₁ reduced (broadleaf autumn interception)
    climate_change    — climate input perturbation (delta_P_mm / delta_PET_mm)
                        or uniform head shift (delta_head_m)
    annual_prediction — run for a specific P and PET to test against observed data

Inputs (all paths from utils/paths.py):
    INT_WELLS_CLEAN_MAOD          — per-well monthly head (maOD), script 01
    INT_LOCATIONS                 — well coordinates, script 01
    INT_CLIMATE                   — monthly P (m) and PET (m), script 01
    INT_CLUSTER_STATS             — cluster assignments (reference wells), script 02
    INT_MASTER_DATA               — per-well β₁, β₂, β₃ coefficients, script 03
    INT_PEAR_AUDIT_SITEWIDE       — cluster assignments (extended wells), script 06
    OUT_18_WELL_SY_TABLE          — per-well Sy from WTF method, script 18
    DATA_DEM                      — site DEM GeoTIFF (optional; greyscale hillshade)
    DATA_KML_FEATURES             — site feature overlays
    DATA_KML_CLEARFELL            — clearfell experiment boundary
    DATA_KML_STREAMS              — site boundary polygon + drainage network

Outputs (all paths from utils/paths.py, DIR_19):
    OUT_19_THICKNESS_MAP   — aquifer thickness surface
    OUT_19_HEAD_MEAN_MAP   — mean annual head with Darcy flow vectors
    OUT_19_HEAD_SEASONAL   — winter vs summer head contrast (2-panel)
    OUT_19_BETA_FIELDS     — spatial β₁, β₂, β₃ fields (3-panel)
    OUT_19_WATER_BALANCE   — recharge, ET-draw, drainage, lateral inflow (4-panel)
    OUT_19_FLUX_MAP        — Darcy flux magnitude and direction
    OUT_19_RESIDUAL_COMP   — SSM residual vs Darcy flux (validation figure)
    OUT_19_STORAGE_MAP     — seasonal storage change (Sy × Δh)
    OUT_19_THICKNESS_CSV   — gridded thickness values
    OUT_19_HEAD_MEAN_CSV   — gridded mean head values
    OUT_19_WB_SUMMARY_CSV  — per-well water balance summary table

References:
    Connell, L. and Bristow, C.S. (2003) Hydrogeological model for Newborough Warren.
        Volume 5 of Bristow et al. (2002) report for CCW. Contract FC 73-05-18.
    Freeman, S. (2008) Hydrological impact of Corsican pine at Newborough Warren.
        BSc dissertation, University of Wales, Bangor.
    Healy, R.W. and Cook, P.G. (2002) Using groundwater levels to estimate recharge.
        Hydrogeology Journal 10, 91–109.
    Young, P.C. (2011) Recursive Estimation and Time-Series Analysis. Springer.
"""

__version__ = "1.0.0"  # Hollingham (2026) — last revised 2026-04-10

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D
from scipy.ndimage import gaussian_filter

try:
    import fiona
    fiona.drvsupport.supported_drivers["KML"] = "rw"
    import geopandas as gpd
    HAS_GEO = True
except ImportError:
    HAS_GEO = False
    warnings.warn("geopandas/fiona not available — KML overlays will be skipped.")

from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    DATA_DEM,
    DATA_KML_FEATURES,
    DATA_KML_CLEARFELL,
    DATA_KML_STREAMS,
    DIR_19,
    INT_LOCATIONS,
    INT_CLIMATE,
    INT_CLUSTER_STATS,
    INT_MASTER_DATA,
    INT_PEAR_AUDIT_SITEWIDE,
    INT_WELLS_CLEAN_MAOD,
    INT_WELL_ELEVATIONS,
    OUT_18_WELL_SY_TABLE,
    OUT_19_THICKNESS_MAP,
    OUT_19_HEAD_MEAN_MAP,
    OUT_19_HEAD_SEASONAL,
    OUT_19_BETA_FIELDS,
    OUT_19_WATER_BALANCE,
    OUT_19_FLUX_MAP,
    OUT_19_RESIDUAL_COMP,
    OUT_19_STORAGE_MAP,
    OUT_19_DEPTH_TO_WT,
    OUT_19_WINTER_FLOOD,
    OUT_19_THICKNESS_CSV,
    OUT_19_HEAD_MEAN_CSV,
    OUT_19_WB_SUMMARY_CSV,
)
from utils.config import CLUSTER_COLOURS
from utils.map_utils import load_dem_hillshade
from utils.data_utils import normalize_well_name

# ── Physical constants ────────────────────────────────────────────────────────
# Hydraulic conductivity — Connell (2003) calibrated MODFLOW value.
# Sensitivity bounds span the calibrated zone range (Betson et al. 2002).
K_CENTRAL = 6.0   # m/day
K_LOW     = 3.0   # m/day
K_HIGH    = 9.0   # m/day

GRID_RES  = 50    # m — IDW grid resolution

# Canopy interception fraction — Forest cluster only (Freeman 2008)
FOREST_INTERCEPTION = 0.24

# Monitoring period bounds — restricts climate means to the dipwell record
MONITOR_START = "2005-04"
MONITOR_END   = "2026-02"

# Seasonal month definitions
WINTER_MONTHS = [11, 12, 1, 2, 3]   # Nov–Mar
SUMMER_MONTHS = [5, 6, 7, 8, 9]     # May–Sep

# Cluster-default Sy — conservative lower bounds (Fetter 2001)
# Used only where per-well WTF Sy from script 18 is unavailable
SY_DEFAULTS = {1: 0.08, 2: 0.12, 3: 0.12, 4: 0.12, 5: 0.10, 6: 0.10}

# ── Aquifer thickness constraints ─────────────────────────────────────────────
# Hard borehole constraints from Bristow (2002) / Connell (2003).
# Values are minimum depths to basement; treated as best-estimate point values.
THICKNESS_NODES = [
    # (Easting, Northing, thickness_m, label)
    # Borehole constraints — Bristow (2002) / Connell (2003)
    (241721, 364133, 12.8, "Water borehole (Bristow 2002)"),
    (241734, 363306,  6.5, "NH1 (Bristow 2002)"),
    (242024, 363107,  6.5, "NH2 (Bristow 2002)"),
    (242837, 363288,  3.65, "Borehole 3 (Bristow 2002)"),
    # Western interior — deeper dune sand (β₁ proxy + Betson et al. 2002)
    (240200, 363500, 17.0, "C3 Western interior"),
    (240000, 363800, 18.0, "C3 Western interior"),
    # Coastal / estuarine pinch-out — aquifer thins to near-zero
    # CEH7 (243386, 363613) and CEH8 (243150, 363382) sit at the far
    # eastern estuarine margin; thickness ≈ surface elevation above OD
    # (shallow water table meets low ground) — treated as pinch-out
    (243386, 363613,  1.0, "CEH7 — estuarine margin pinch-out"),
    (243150, 363382,  1.0, "CEH8 — estuarine margin pinch-out"),
    (241800, 362800,  0.5, "Southern shore (geomorphological)"),
    (242500, 362900,  0.5, "Eastern shore (geomorphological)"),
    # Lake boundary — near-zero saturated thickness beneath open water
    (242480, 364835,  7.456, "Llyn Rhos Ddu (lake boundary)"),
]

# Cluster-prior aquifer thickness (m) — applied at well locations without
# a hard borehole constraint. Physically motivated estimates only.
CLUSTER_THICKNESS_PRIOR = {
    1: 7.0,   # C1 Eastern lake-buffer
    2: 7.0,   # C2 Eastern mature dune
    3: 16.0,  # C3 Western interior — deepest
    4: 16.0,  # C4 Forest — same as C3 Western (plantation sits on same dune
              #   sand body; earlier 3.5 m value was for forest edge only)
              #   CEH14 overridden individually in build_thickness_surface
    5: 4.0,   # C5 Coastal
    6: 7.456,   # C6 Llyn Rhos — corrected maOD (DEM-proxy, raw depth was 0.18-0.59 m below pipe)
}


# ============================================================================
# DEM HILLSHADE
# ============================================================================

# ── Stream network cache ──────────────────────────────────────────────────────
# Computed once on first call to _get_stream_polylines(), reused for all figures.
# Uses SAGA stream KML (skeletonised) not D8 flow accumulation.
_STREAM_CACHE = None

def compute_d8_streams(
    dem_path: Path,
    streams_kml: Path = None,
    dilation_radius: int = 4,
    min_component: int = 30,
    e_lim: tuple = (240100, 243900),
    n_lim: tuple = (362200, 365800),
):
    """
    Derive stream network polylines for map overlay.

    Uses the SAGA stream cell KML (streams.kml) as the primary source —
    these cells are already hydrologically meaningful. The approach is:
      1. Rasterise SAGA stream cell centroids to DEM grid
      2. Dilate by dilation_radius pixels to bridge gaps on flat dune plain
      3. Skeletonise to single-pixel-wide lines
      4. Remove components shorter than min_component pixels
      5. Trace skeleton to (xs, ys) polylines via 8-connectivity graph walk

    Falls back gracefully if streams_kml is absent or scikit-image unavailable.

    Parameters
    ----------
    dem_path : Path
    streams_kml : Path or None
        Path to SAGA streams KML. If None uses DATA_KML_STREAMS.
    dilation_radius : int
        Morphological dilation radius in DEM pixels (default 4 = 8 m at 2 m res).
    min_component : int
        Minimum skeleton component length in pixels (default 30).
    e_lim, n_lim : tuple
        Study area bounds for clipping.

    Returns
    -------
    polylines : list of (xs, ys) tuples in EPSG:27700
    """
    try:
        import rasterio
        from skimage.morphology import skeletonize, dilation, disk
        from skimage.measure import label as sk_label
        from pyproj import Transformer as _Tr
        import xml.etree.ElementTree as _ET
    except ImportError as e:
        warnings.warn(f"Stream network requires rasterio + scikit-image: {e}")
        return []

    kml_path = streams_kml or DATA_KML_STREAMS

    with rasterio.open(str(dem_path)) as src:
        dem  = src.read(1).astype(float)
        nd   = src.nodata
        tfm  = src.transform
        res  = abs(tfm.a)
        E0   = tfm.c
        N_top = tfm.f
    if nd is not None:
        dem[dem == nd] = np.nan
    rows, cols = dem.shape

    # ── 1. Rasterise SAGA stream cells ────────────────────────────────────
    stream_grid = np.zeros((rows, cols), dtype=bool)
    if kml_path.exists():
        _ns = "http://www.opengis.net/kml/2.2"
        _t  = _Tr.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
        try:
            _tree = _ET.parse(str(kml_path))
            for pm in _tree.getroot().iter(f"{{{_ns}}}Placemark"):
                cel = pm.find(f".//{{{_ns}}}coordinates")
                if cel is None or not cel.text:
                    continue
                toks = cel.text.strip().split()
                if not toks:
                    continue
                p = toks[0].split(",")
                if len(p) < 2:
                    continue
                try:
                    e, n = _t.transform(float(p[0]), float(p[1]))
                    ci = int(round((e - E0) / res))
                    ri = int(round((N_top - n) / res))
                    if 0 <= ri < rows and 0 <= ci < cols:
                        stream_grid[ri, ci] = True
                except Exception:
                    continue
            print(f"    SAGA stream cells rasterised: {stream_grid.sum()}")
        except Exception as exc:
            warnings.warn(f"SAGA KML parse failed ({exc}) — stream network unavailable.")
            return []
    else:
        warnings.warn(f"streams.kml not found at {kml_path} — stream network unavailable.")
        return []

    # ── 2. Dilate to bridge gaps ───────────────────────────────────────────
    dilated = dilation(stream_grid, footprint=disk(dilation_radius))

    # ── 3. Skeletonise ────────────────────────────────────────────────────
    skel = skeletonize(dilated)

    # ── 4. Remove small components ────────────────────────────────────────
    labeled = sk_label(skel, connectivity=2)
    clean   = np.zeros_like(skel)
    for lbl in range(1, labeled.max() + 1):
        if (labeled == lbl).sum() >= min_component:
            clean[labeled == lbl] = True

    print(f"    Skeleton: {clean.sum()} pixels in "
          f"{(sk_label(clean, connectivity=2).max())} components")

    # ── 5. Trace to polylines ─────────────────────────────────────────────
    dr = [-1,-1,-1, 0, 0, 1, 1, 1]
    dc = [-1, 0, 1,-1, 1,-1, 0, 1]
    skel_pts = set(zip(*np.where(clean)))

    def nbrs(r, c):
        return [(r + dr[k], c + dc[k]) for k in range(8)
                if (r + dr[k], c + dc[k]) in skel_pts]

    endpoints = [pt for pt in skel_pts if len(nbrs(*pt)) == 1]
    if not endpoints:
        endpoints = [next(iter(skel_pts))]

    visited = set()
    polylines = []
    for start in endpoints:
        prev, curr = None, start
        lr, lc = [curr[0]], [curr[1]]
        while True:
            nbs = [n for n in nbrs(*curr) if n != prev]
            if not nbs:
                break
            nxt = nbs[0]
            edge = (min(curr, nxt), max(curr, nxt))
            if edge in visited:
                break
            visited.add(edge)
            lr.append(nxt[0])
            lc.append(nxt[1])
            prev, curr = curr, nxt
            if len(nbrs(*curr)) != 2:
                break
        if len(lr) >= 5:
            xs = [E0 + c * res for c in lc]
            ys = [N_top - r * res for r in lr]
            polylines.append((xs, ys))

    return polylines


def _get_stream_polylines():
    """Return cached SAGA stream polylines, computing on first call."""
    global _STREAM_CACHE
    if _STREAM_CACHE is None:
        if DATA_DEM.exists():
            print("  Computing stream network from SAGA KML...")
            _STREAM_CACHE = compute_d8_streams(DATA_DEM)
            print(f"  Stream polylines: {len(_STREAM_CACHE)}")
        else:
            _STREAM_CACHE = []
    return _STREAM_CACHE




def load_kml_features():
    """
    Load KML site features into a dict of GeoDataFrames (EPSG:27700).

    Returns:
        features : dict with keys 'features' and/or 'clearfell'
        handles  : list of Line2D legend handles for drawn features
    """
    features = {}
    if not HAS_GEO:
        return features

    for fpath, key in [(DATA_KML_FEATURES, "features"),
                       (DATA_KML_CLEARFELL, "clearfell")]:
        if not fpath.exists():
            continue
        try:
            gdfs = [
                gpd.read_file(str(fpath), layer=lyr, driver="KML")
                   .set_crs(epsg=4326, allow_override=True)
                   .to_crs("EPSG:27700")
                for lyr in fiona.listlayers(str(fpath))
            ]
            if gdfs:
                features[key] = pd.concat(gdfs, ignore_index=True)
        except Exception as e:
            warnings.warn(f"Could not load {fpath.name}: {e}")

    return features


def _ring_xy(ring):
    """
    Return (xs, ys) arrays from a shapely LinearRing or exterior,
    safely stripping any Z coordinate. Uses .xy when available
    (always returns 2D), otherwise falls back to slicing coords.
    """
    if hasattr(ring, "xy"):
        return ring.xy          # shapely .xy is always (x_arr, y_arr)
    coords = list(ring.coords)
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return xs, ys


def _line_xy(geom):
    """
    Return (xs, ys) from a LineString, stripping Z if present.
    """
    if hasattr(geom, "xy"):
        return geom.xy
    coords = list(geom.coords)
    return [c[0] for c in coords], [c[1] for c in coords]


def add_kml_overlays(ax, features):
    """
    Draw KML features onto ax with consistent styling across all maps.

    Forest polygon   — purple outline, dashed
    Clearfell area   — orange outline, dash-dot
    Lake (Llyn Rhos) — light blue fill, no outline
    Transect lines   — steel blue, thin
    Other polygons   — black dashed outline

    Z coordinates in KML geometries are stripped automatically via _ring_xy
    and _line_xy so this function is safe regardless of KML dimension.

    Returns list of Line2D legend handles.
    """
    handles = []
    added   = set()

    def _handle(label, color, ls="-", lw=1.5):
        if label not in added:
            handles.append(Line2D([0], [0], color=color, linestyle=ls,
                                  linewidth=lw, label=label))
            added.add(label)

    def _exterior(geom):
        """Return the exterior ring, handling Polygon and MultiPolygon."""
        gt = geom.geom_type
        if gt == "Polygon":
            return geom.exterior
        elif "Polygon" in gt:          # MultiPolygon or GeometryCollection
            return geom.geoms[0].exterior
        return None

    gdf_f = features.get("features")
    if gdf_f is not None:
        name_col = "Name" if "Name" in gdf_f.columns else None
        for _, row in gdf_f.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            name = str(row[name_col]).lower() if name_col else ""
            gt   = geom.geom_type

            if "forest" in name or "plantation" in name or "wood" in name:
                color, ls, lw, label = "purple", "--", 2.0, "Forest boundary"

            elif "llyn" in name or "rhos" in name or "lake" in name:
                if "Polygon" in gt:
                    ext = _exterior(geom)
                    if ext is not None:
                        xs, ys = _ring_xy(ext)
                        ax.fill(xs, ys, color="dodgerblue", alpha=0.25, zorder=3)
                color, ls, lw, label = "dodgerblue", "-", 1.2, "Llyn Rhos Ddu"

            elif "LineString" in gt:
                xs, ys = _line_xy(geom)
                ax.plot(xs, ys, color="steelblue", lw=0.7,
                        alpha=0.6, zorder=4)
                _handle("Dipwell transects", "steelblue", "-", 0.7)
                continue

            else:
                color, ls, lw, label = "black", "--", 1.2, "Site features"

            if "Polygon" in gt:
                ext = _exterior(geom)
                if ext is not None:
                    xs, ys = _ring_xy(ext)
                    ax.plot(xs, ys, color=color, linestyle=ls,
                            linewidth=lw, zorder=5)
            _handle(label, color, ls, lw)

    gdf_c = features.get("clearfell")
    if gdf_c is not None:
        for geom in gdf_c.geometry:
            if geom is None or geom.is_empty:
                continue
            gt = geom.geom_type
            geoms = geom.geoms if "Multi" in gt or "Collection" in gt else [geom]
            for g in geoms:
                if "Polygon" in g.geom_type:
                    ext = _exterior(g)
                    if ext is not None:
                        xs, ys = _ring_xy(ext)
                        ax.plot(xs, ys, color="darkorange", linestyle="-.",
                                linewidth=2.0, zorder=5)
        _handle("Clearfell area", "darkorange", "-.", 2.0)

    # ── Streams — SAGA KML skeletonised to connected polylines ───────────
    stream_lines = _get_stream_polylines()
    if stream_lines:
        for xs, ys in stream_lines:
            ax.plot(xs, ys, color="#0057B7", linewidth=1.2,
                    alpha=0.75, solid_capstyle="round",
                    solid_joinstyle="round", zorder=4)
        _handle("SAGA stream network", "#0057B7", "-", 1.2)

    return handles


# ============================================================================
# INTERPOLATION HELPERS
# ============================================================================

def idw_interpolate(points_xy, values, grid_x, grid_y, power=2):
    """Inverse distance weighting interpolation onto a regular grid."""
    grid_pts = np.column_stack([grid_x.ravel(), grid_y.ravel()])
    result   = np.zeros(grid_pts.shape[0])
    for i, pt in enumerate(grid_pts):
        dist = np.sqrt(np.sum((points_xy - pt) ** 2, axis=1))
        if np.any(dist == 0):
            result[i] = values[dist == 0][0]
        else:
            w = 1.0 / dist ** power
            result[i] = np.sum(w * values) / np.sum(w)
    return result.reshape(grid_x.shape)


def interpolate_surface(pts, vals, grid_x, grid_y, mask, power=1):
    """
    IDW interpolation with NaN applied outside the site mask.
    Default power=1 (linear IDW) produces smoother surfaces than power=2
    for sparse well networks — power=2 creates bullseye artefacts around
    isolated points where the inverse-square weighting drops off sharply.
    """
    valid = ~np.isnan(vals)
    if valid.sum() < 3:
        warnings.warn(f"Too few valid points ({valid.sum()}) for interpolation.")
        return np.full(grid_x.shape, np.nan)
    surf = idw_interpolate(pts[valid], vals[valid], grid_x, grid_y, power=power)
    surf[~mask] = np.nan
    return surf


def compute_gradient(surface, res):
    """Head gradient (dh/dx, dh/dy) in m/m. NaN mask preserved."""
    fill = np.nan_to_num(surface, nan=np.nanmean(surface))
    gy, gx = np.gradient(fill, res, res)
    gx[np.isnan(surface)] = np.nan
    gy[np.isnan(surface)] = np.nan
    return gx, gy


def make_site_mask(grid_x, grid_y):
    """
    Boolean mask for the interpolation domain.

    Primary method: loads the site boundary polygon from streams.kml
    (the "DEM-derived flow network and boundary" layer in map_utils).
    The streams.kml boundary defines the perimeter of the dune system
    including the coastal margin, so masking to it gives a geographically
    correct interpolation domain.

    Fallback (if streams.kml absent or geopandas unavailable): rectangular
    mask clipped to the three sea-boundary lines.
    """
    flat = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    # ── Primary: site_boundary.kml — union of stream cells ──────────────────
    # Uses pure XML + pyproj + shapely. No fiona/osgeo KML driver needed.
    # site_boundary.kml contains the dissolved stream-cell polygons that
    # define the exact study area boundary.
    _bnd_path = DATA_DIR / "site_boundary.kml"
    if not _bnd_path.exists():
        _bnd_path = DATA_DIR / "streams.kml"   # fallback to streams.kml
    if _bnd_path.exists():
        try:
            import xml.etree.ElementTree as _ET
            from pyproj import Transformer as _Tr
            from shapely.geometry import Polygon as _Poly
            from shapely.ops import unary_union as _union
            from matplotlib.path import Path as _MplPath

            _tr = _Tr.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
            _root = _ET.parse(str(_bnd_path)).getroot()
            _polys = []

            def _parse(el):
                tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                if tag == "coordinates":
                    pts = []
                    for tok in (el.text or "").strip().split():
                        p = tok.split(",")
                        if len(p) >= 2:
                            try: pts.append((float(p[0]), float(p[1])))
                            except ValueError: pass
                    if len(pts) >= 3:
                        lons = [p[0] for p in pts]
                        lats = [p[1] for p in pts]
                        ex, ny = _tr.transform(lons, lats)
                        try: _polys.append(_Poly(zip(ex, ny)))
                        except Exception: pass
                for child in el:
                    _parse(child)

            _parse(_root)

            if _polys:
                _dissolved = _union(_polys)
                # Buffer 100m to fill gaps, then get outer boundary
                _dissolved = _dissolved.buffer(100)
                if _dissolved.geom_type == "MultiPolygon":
                    _dissolved = max(_dissolved.geoms, key=lambda g: g.area)
                _coords = list(_dissolved.exterior.coords)
                _path = _MplPath([(c[0], c[1]) for c in _coords])
                _inside = _path.contains_points(flat)
                print(f"  Site mask: {_inside.sum()} of {len(_inside)} grid cells inside boundary")
                return _inside.reshape(grid_x.shape)
        except Exception as e:
            warnings.warn(f"site_boundary.kml mask failed ({e}) — "
                          "falling back to rectangular sea-boundary mask.")

    # ── Fallback: rectangular mask clipped to sea boundaries ─────────────────
    mask = np.ones(grid_x.shape, dtype=bool)
    mask[grid_y < SEA_SOUTH_N] = False
    mask[grid_x > SEA_EAST_E]  = False
    mask[grid_x < SEA_WEST_E]  = False
    return mask


def make_convex_hull_mask(points_xy, grid_x, grid_y):
    """Retained for compatibility — use make_site_mask() for script 19."""
    from matplotlib.path import Path as MplPath
    from scipy.spatial import ConvexHull
    try:
        hull  = ConvexHull(points_xy)
        path  = MplPath(points_xy[hull.vertices])
        flat  = np.column_stack([grid_x.ravel(), grid_y.ravel()])
        return path.contains_points(flat).reshape(grid_x.shape)
    except Exception:
        return np.ones(grid_x.shape, dtype=bool)


# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    """Load all required inputs. Returns dict of DataFrames."""
    data = {}

    loc = pd.read_csv(INT_LOCATIONS)
    loc["Match_ID"] = loc["Match_ID"].apply(normalize_well_name)
    data["locations"] = loc

    cl = pd.read_csv(INT_CLUSTER_STATS)
    cl["Match_ID"] = cl["Match_ID"].apply(normalize_well_name)
    data["clusters"] = cl

    md = pd.read_csv(INT_MASTER_DATA)
    md["Name_Original"] = md["Name_Original"].apply(normalize_well_name)
    data["master"] = md

    sw = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE)
    sw["Well_Normalised"] = sw["Well_Normalised"].apply(normalize_well_name)
    data["sitewide"] = sw

    maod = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    maod.columns = [normalize_well_name(c) for c in maod.columns]
    data["maod"] = maod

    clim = pd.read_csv(INT_CLIMATE, parse_dates=["Date"], index_col="Date")
    data["climate"] = clim.loc[MONITOR_START:MONITOR_END]

    elev = pd.read_csv(INT_WELL_ELEVATIONS)
    elev["Name_norm"] = elev["Name_norm"].apply(normalize_well_name)
    data["elevations"] = elev

    if OUT_18_WELL_SY_TABLE.exists():
        sy = pd.read_csv(OUT_18_WELL_SY_TABLE)
        # Script 18 writes "Well" as the well ID column; earlier versions used
        # "Well_Normalised". Detect whichever is present and standardise to
        # "well_norm" so build_well_table() has a consistent key to map from.
        if "Well_Normalised" in sy.columns:
            sy["well_norm"] = sy["Well_Normalised"].apply(normalize_well_name)
        elif "Well" in sy.columns:
            sy["well_norm"] = sy["Well"].apply(normalize_well_name)
        else:
            warnings.warn(f"{OUT_18_WELL_SY_TABLE.name}: no recognisable well "
                          "ID column ('Well' or 'Well_Normalised') — Sy will "
                          "fall back to cluster defaults.")
            sy["well_norm"] = pd.Series(dtype=str)
        data["sy"] = sy
    else:
        warnings.warn(
            f"{OUT_18_WELL_SY_TABLE.name} not found — "
            "cluster-default Sy values will be used (run script 18 first).")
        data["sy"] = None

    return data


# ============================================================================
# WELL TABLE
# ============================================================================

def build_well_table(data):
    """
    Merge location, cluster, β coefficients, Sy, and seasonal head statistics.
    Computes the SSM mean-monthly water balance and lateral inflow residual.

        lateral_inflow = (β₂ × PET̄ + β₃ × |h̄|) − β₁ × P̄_eff

    Positive = net inflow required from ridge; negative = local surplus.
    """
    loc  = data["locations"]
    cldf = data["clusters"]
    md   = data["master"]
    maod = data["maod"]
    clim = data["climate"]

    P_bar   = clim["P_m"].mean()   # mean monthly P (m/month)
    PET_bar = clim["PET"].mean()   # mean monthly PET (m/month)

    wt = loc[["Match_ID", "E", "N"]].rename(columns={"Match_ID": "well"}).copy()

    cl = cldf[["Match_ID", "Cluster"]].rename(
        columns={"Match_ID": "well", "Cluster": "cluster"})
    wt = wt.merge(cl, on="well", how="left")

    beta = md[["Name_Original",
               "beta_1_recharge",
               "beta_2_atmospheric_draw",
               "beta_3_internal_brake"]].rename(columns={
        "Name_Original":           "well",
        "beta_1_recharge":         "beta1",
        "beta_2_atmospheric_draw": "beta2",
        "beta_3_internal_brake":   "beta3",
    })
    wt = wt.merge(beta, on="well", how="left")

    wt["mean_head"]   = wt["well"].map(maod.mean(axis=0))
    wt["winter_head"] = wt["well"].map(
        maod[maod.index.month.isin(WINTER_MONTHS)].mean(axis=0))
    wt["summer_head"] = wt["well"].map(
        maod[maod.index.month.isin(SUMMER_MONTHS)].mean(axis=0))
    wt["head_swing"]  = wt["winter_head"] - wt["summer_head"]

    # ── DEM ground elevation — for depth-below-ground computation ─────────
    elev_df = data.get("elevations")
    if elev_df is not None:
        elev_map = dict(zip(elev_df["Name_norm"], elev_df["DEM_Ground_Elev"]))
        wt["dem_elev"] = wt["well"].map(elev_map)
    else:
        wt["dem_elev"] = np.nan

    # Depth below ground: positive = below surface, negative = flooding
    # Uses same convention as 11b_spatial_thresholds.py
    wt["mean_depth_bg"]   = wt["dem_elev"] - wt["mean_head"]
    wt["winter_depth_bg"] = wt["dem_elev"] - wt["winter_head"]
    wt["summer_depth_bg"] = wt["dem_elev"] - wt["summer_head"]

    # Sy — prefer per-well WTF estimate (script 18)
    sy_df  = data.get("sy")
    sy_col = ("Sy_median"
              if sy_df is not None and "Sy_median" in sy_df.columns
              else None)
    if sy_col and sy_df is not None and "well_norm" in sy_df.columns:
        sy_map = dict(zip(sy_df["well_norm"], sy_df[sy_col]))
        wt["sy"] = wt["well"].map(sy_map)
    else:
        wt["sy"] = np.nan

    def fill_sy(row):
        if pd.notna(row.get("sy", np.nan)):
            return row["sy"]
        return SY_DEFAULTS.get(
            int(row["cluster"]) if pd.notna(row["cluster"]) else 3, 0.12)
    wt["sy"] = wt.apply(fill_sy, axis=1)

    # Effective P — C4 wells corrected for canopy interception (Freeman 2008)
    wt["P_eff"] = wt.apply(
        lambda r: P_bar * (1 - FOREST_INTERCEPTION)
        if pd.notna(r["cluster"]) and int(r["cluster"]) == 4
        else P_bar, axis=1)

    wt["recharge_m_mon"]  = wt["beta1"] * wt["P_eff"]
    wt["et_draw_m_mon"]   = wt["beta2"] * PET_bar
    wt["drainage_m_mon"]  = wt["beta3"] * wt["mean_head"].abs()
    wt["lateral_inflow_m_mon"] = (
        wt["et_draw_m_mon"] + wt["drainage_m_mon"] - wt["recharge_m_mon"])
    wt["storage_change_mm"] = wt["sy"] * wt["head_swing"] * 1000.0

    # Exclude outlier wells from spatial interpolation
    # ceh3:  perched above regional water table
    # ceh17: lowest R²=0.427, β₁=0.694 and β₃=0.049 both site minima
    SPATIAL_EXCLUDE = {"ceh3", "ceh17"}
    excluded = wt["well"].isin(SPATIAL_EXCLUDE)
    if excluded.any():
        excl_list = wt.loc[excluded, "well"].tolist()
        wt = wt.loc[~excluded].copy()
        print(f"  Excluding {len(excl_list)} outlier wells from interpolation: {excl_list}")

    wt = wt.dropna(subset=["E", "N", "mean_head"])

    print(f"  Well table: {len(wt)} wells with valid head + coordinates")
    print(f"  β coefficients available: {wt['beta1'].notna().sum()} wells")
    print(f"  C4 wells (interception-corrected): {(wt['cluster']==4).sum()}")
    print(f"  P̄ = {P_bar*1000:.1f} mm/month,  PET̄ = {PET_bar*1000:.1f} mm/month")

    return wt, P_bar, PET_bar


# ============================================================================
# GRID AND SURFACES
# ============================================================================

# ── Sea boundary definition ───────────────────────────────────────────────────
# Newborough Warren is bounded by sea/estuary on three sides, with a bedrock
# ridge forming the western and northwestern boundary.
#
# DEM analysis (newborough_dem.tif) confirms:
#
# SOUTHERN coast (Menai Strait / Caernarfon Bay) — N ≈ 362350
#   Low ground (<2 m AOD) across full width. Full-width anchors apply.
#
# EASTERN coast (Menai Strait) — E ≈ 243850
#   Elevation 1–5 m AOD throughout (N=362500–365300). The Menai Strait runs
#   the full eastern flank so zero-head anchors extend the full eastern margin.
#
# WESTERN boundary — ridge, NOT sea, above N ≈ 363500
#   At E=240200: elevation is below sea level (sea/estuary) south of N=363500,
#   rising sharply to 16–37 m above N=363800 (bedrock ridge). Zero-head anchors
#   apply only south of SEA_WEST_N_MAX where the western margin is open water.
#   Above that the ridge forms a no-flow divide — no sea boundary anchors needed.
#
# NORTHERN boundary — ridge continues off-grid to NW; Malltraeth estuary to N.
#   No zero-head anchors on the north edge — the ridge is the dominant boundary.

SEA_SOUTH_N    = 362350   # m OSGB36 — southern shoreline Northing
SEA_EAST_E     = 243850   # m OSGB36 — eastern (Menai Strait) Easting
SEA_WEST_E     = 239200   # m OSGB36 — western estuary Easting (inside DEM)
SEA_HEAD       = 0.0      # m AOD    — water table at sea level

# Northern limit for western anchors only.
# The western margin transitions from open water (estuary) to bedrock ridge
# at approximately N=363500 (DEM: -1 m AOD at N=363300, +6 m at N=363500,
# +17 m at N=363900). Anchors stop here on the west.
SEA_WEST_N_MAX = 363400   # m OSGB36

# Eastern anchors run the full eastern flank (Menai Strait throughout).
SEA_EAST_N_MAX = 365400   # m OSGB36

# Spacing of sea-boundary anchor points (m)
SEA_ANCHOR_SPACING = 200


def _sea_boundary_points():
    """
    Generate (E, N, head=0) anchor points along the sea/estuary boundaries.

    Southern coast: full width at N=SEA_SOUTH_N.
    Eastern coast:  full height (Menai Strait throughout) up to SEA_EAST_N_MAX.
    Western coast:  estuary only, capped at SEA_WEST_N_MAX where ridge begins.

    Returns (pts array [n,2], vals array [n]).
    """
    pts, vals = [], []

    # Southern coast — full width
    for e in np.arange(SEA_WEST_E, SEA_EAST_E + SEA_ANCHOR_SPACING,
                       SEA_ANCHOR_SPACING):
        pts.append([e, SEA_SOUTH_N])
        vals.append(SEA_HEAD)

    # Eastern coast (Menai Strait) — full height
    for n in np.arange(SEA_SOUTH_N, SEA_EAST_N_MAX + SEA_ANCHOR_SPACING,
                       SEA_ANCHOR_SPACING):
        pts.append([SEA_EAST_E, n])
        vals.append(SEA_HEAD)

    # Western coast (estuary) — only below ridge
    for n in np.arange(SEA_SOUTH_N, SEA_WEST_N_MAX + SEA_ANCHOR_SPACING,
                       SEA_ANCHOR_SPACING):
        pts.append([SEA_WEST_E, n])
        vals.append(SEA_HEAD)

    return np.array(pts), np.array(vals)


def build_grid(wt):
    # Extend to shoreline on south, east, and west; add buffer on north
    xi = np.arange(SEA_WEST_E,  SEA_EAST_E  + GRID_RES, GRID_RES)
    yi = np.arange(SEA_SOUTH_N, wt["N"].max() + 400,     GRID_RES)
    return np.meshgrid(xi, yi)


# Per-well thickness overrides — wells where local evidence overrides the
# cluster prior. CEH14 sits near the ridge crest at ~13.3 m AOD; the
# water table is close to surface elevation here, so saturated thickness
# is constrained by the distance from ground to bedrock (~4–5 m at this
# location, consistent with the shallow ridge geology).
WELL_THICKNESS_OVERRIDE = {
    "ceh14": 5.0,   # Ridge crest — shallow to bedrock despite being C4
}


def build_thickness_surface(wt, grid_x, grid_y, mask):
    """
    IDW thickness surface from borehole constraints + cluster priors + well
    overrides. Uses power=1 (linear IDW) rather than power=2 to produce a
    smoother surface — power=2 creates bullseye artefacts around individual
    borehole nodes where the inverse-square weighting drops off very sharply.
    Physical minimum enforced at 0.3 m.
    """
    hard_pts = np.array([[n[0], n[1]] for n in THICKNESS_NODES])
    hard_b   = np.array([n[2] for n in THICKNESS_NODES])

    # Per-well thickness: cluster prior unless overridden
    well_b = []
    for _, row in wt.iterrows():
        well_norm = str(row["well"]).lower().replace(" ", "")
        if well_norm in WELL_THICKNESS_OVERRIDE:
            well_b.append(WELL_THICKNESS_OVERRIDE[well_norm])
        else:
            cl = int(row["cluster"]) if pd.notna(row["cluster"]) else 3
            well_b.append(CLUSTER_THICKNESS_PRIOR.get(cl, 7.0))
    well_b = np.array(well_b)

    all_pts = np.vstack([hard_pts, wt[["E", "N"]].values])
    all_b   = np.concatenate([hard_b, well_b])

    # power=1 gives smoother interpolation — avoids bullseye artefacts from
    # the sharp inverse-square weighting of isolated borehole nodes
    surf = idw_interpolate(all_pts, all_b, grid_x, grid_y, power=1)
    surf = np.maximum(surf, 0.3)
    surf[~mask] = np.nan
    return surf



def solve_steady_state_head(grid_x, grid_y, mask,
                             thickness, beta1_surf, beta2_surf, beta3_surf,
                             P_eff_surf, PET_surf,
                             wt, sea_pts, sea_vals):
    """
    Solve the 2D steady-state groundwater flow equation on the grid.

    Governing equation (Helmholtz form):
        ∇·(T·∇h) − β₃·h = −W
        W = β₁·P_eff − β₂·PET      (net recharge source term, m/month)
        T = K · b                    (transmissivity, m²/day)

    The β₃·h term represents the internal drainage-to-baseflow feedback
    from the SSM — it stabilises the system and ensures a unique solution.

    Boundary conditions:
        Dirichlet h = 0 m AOD at sea boundary cells (southern coast,
        eastern coast, western estuary up to ridge).
        Neumann (no-flow) at the ridge and northern edge — implemented
        implicitly by not defining sea BCs there; the finite-difference
        stencil simply uses one-sided differences at grid edges.

    Well observations are added as soft penalty constraints:
        For each reference well, add a large diagonal term so the solution
        is pulled toward the observed head while the PDE remains satisfied
        across the interior. This blends the physics with the observations
        rather than choosing one or the other.

    Parameters
    ----------
    well_penalty : float
        Weight for well observation constraints relative to PDE residual.
        1e4 means observations are honoured to ~0.01 m accuracy.

    Returns
    -------
    h_solved : 2D ndarray, shape = grid_x.shape
        Steady-state head in m AOD. NaN outside the active domain.
    """
    from scipy.sparse import lil_matrix, diags
    from scipy.sparse.linalg import spsolve

    ny, nx = grid_x.shape
    dx = float(grid_x[0, 1] - grid_x[0, 0])   # grid spacing (m)
    dy = float(grid_y[1, 0] - grid_y[0, 0])

    # Transmissivity T = K × b at each cell
    T = K_CENTRAL * thickness   # m²/day → convert to m²/month for consistency
    T_month = T * 30.44          # approximate days/month

    def idx(i, j):
        """Flat index for cell (row i, col j)."""
        return i * nx + j

    n_cells = ny * nx
    A = lil_matrix((n_cells, n_cells), dtype=float)
    b_rhs = np.zeros(n_cells)

    # ── Identify boundary cells (sea = Dirichlet h=0) ────────────────────
    # A cell is a sea boundary if it is outside the active mask but within
    # the grid, or if it is on the edge rows/cols
    sea_bc = np.zeros((ny, nx), dtype=bool)

    # Mark sea anchor positions
    if sea_pts is not None and len(sea_pts) > 0:
        for pt in sea_pts:
            # Find nearest grid cell
            j = int(round((pt[0] - grid_x[0, 0]) / dx))
            i = int(round((pt[1] - grid_y[0, 0]) / dy))
            if 0 <= i < ny and 0 <= j < nx:
                sea_bc[i, j] = True

    # All cells outside the active mask are treated as sea BC
    sea_bc[~mask] = True

    # ── Build finite-difference system ────────────────────────────────────
    for i in range(ny):
        for j in range(nx):
            k = idx(i, j)

            if sea_bc[i, j]:
                # Dirichlet BC: h = SEA_HEAD = 0
                A[k, k] = 1.0
                b_rhs[k] = SEA_HEAD
                continue

            if not mask[i, j]:
                A[k, k] = 1.0
                b_rhs[k] = np.nan
                continue

            # ── Interior cell: 5-point stencil ────────────────────────────
            # Central difference for ∂/∂x(T·∂h/∂x):
            #   [T_{i+½,j}·(h_{i+1,j}-h_{i,j}) - T_{i-½,j}·(h_{i,j}-h_{i-1,j})] / dx²
            # Similarly for y. T at half-points from harmonic mean.

            def T_half(a, b):
                """Harmonic mean transmissivity at cell interface."""
                if a + b < 1e-12:
                    return 0.0
                return 2.0 * a * b / (a + b)

            Tc = T_month[i, j] if not np.isnan(T_month[i, j]) else 0.01

            # x-direction neighbours
            if j > 0 and mask[i, j-1]:
                Tw = T_half(Tc, T_month[i, j-1] if not np.isnan(T_month[i, j-1]) else 0.01)
                lw = Tw / dx**2
            else:
                lw = 0.0   # no-flow (Neumann) at west edge

            if j < nx-1 and mask[i, j+1]:
                Te = T_half(Tc, T_month[i, j+1] if not np.isnan(T_month[i, j+1]) else 0.01)
                le = Te / dx**2
            else:
                le = 0.0   # no-flow at east edge

            # y-direction neighbours
            if i > 0 and mask[i-1, j]:
                Ts = T_half(Tc, T_month[i-1, j] if not np.isnan(T_month[i-1, j]) else 0.01)
                ls = Ts / dy**2
            else:
                ls = 0.0   # no-flow at south edge

            if i < ny-1 and mask[i+1, j]:
                Tn = T_half(Tc, T_month[i+1, j] if not np.isnan(T_month[i+1, j]) else 0.01)
                ln = Tn / dy**2
            else:
                ln = 0.0   # no-flow at north/ridge edge

            # β₃ drainage term (Helmholtz)
            b3c = float(beta3_surf[i, j]) if not np.isnan(beta3_surf[i, j]) else 0.0
            # Convert β₃ from m/month/m to consistent units — already per month

            # Diagonal entry
            diag = -(lw + le + ls + ln) - b3c
            A[k, k] = diag

            # Off-diagonal entries (only for active neighbours)
            if lw > 0:
                A[k, idx(i, j-1)] = lw
            elif sea_bc[i, j-1] if j > 0 else True:
                b_rhs[k] -= lw * SEA_HEAD   # absorb sea BC into RHS

            if le > 0:
                A[k, idx(i, j+1)] = le
            elif (j < nx-1 and sea_bc[i, j+1]):
                b_rhs[k] -= le * SEA_HEAD

            if ls > 0:
                A[k, idx(i-1, j)] = ls
            elif (i > 0 and sea_bc[i-1, j]):
                b_rhs[k] -= ls * SEA_HEAD

            if ln > 0:
                A[k, idx(i+1, j)] = ln
            elif (i < ny-1 and sea_bc[i+1, j]):
                b_rhs[k] -= ln * SEA_HEAD

            # Source/sink term W = β₁·P_eff − β₂·PET
            b1c  = float(beta1_surf[i, j]) if not np.isnan(beta1_surf[i, j]) else 0.0
            b2c  = float(beta2_surf[i, j]) if not np.isnan(beta2_surf[i, j]) else 0.0
            Pc   = float(P_eff_surf[i, j]) if not np.isnan(P_eff_surf[i, j]) else 0.0
            PETc = float(PET_surf[i, j])   if not np.isnan(PET_surf[i, j])   else 0.0
            W    = b1c * Pc - b2c * PETc   # net recharge (m/month)
            b_rhs[k] -= W                  # negative because −W on RHS

    # Well observations are NOT used as constraints in the PDE solve.
    # The Dirichlet sea boundary conditions plus the spatially-interpolated
    # β fields (recharge, ET-draw, drainage) are sufficient to determine
    # the head field. Adding well penalties at 1e4 weight caused sharp
    # bullseye artefacts around each well — the solver was reproducing IDW
    # in a different disguise rather than solving the physics.
    # Well observations are instead used downstream to validate the solution
    # (residual comparison figure and model-vs-observed scatter).
    n_constrained = 0
    print(f"  Steady-state solver: {n_cells} cells, physics-only (no well penalties)")

    # ── Solve ─────────────────────────────────────────────────────────────
    A_csr = A.tocsr()
    h_flat = spsolve(A_csr, b_rhs)

    h_solved = h_flat.reshape(ny, nx)
    h_solved[~mask] = np.nan

    # Sanity check
    valid = h_solved[mask]
    print(f"  Solution: min={np.nanmin(valid):.2f} m AOD, "
          f"max={np.nanmax(valid):.2f} m AOD, "
          f"mean={np.nanmean(valid):.2f} m AOD")
    n_neg = np.sum(valid < -1.0)
    if n_neg > 0:
        print(f"  [{n_neg} cells below -1 m AOD — check boundary conditions]")

    return h_solved


def build_source_sink_surfaces(wt, grid_x, grid_y, mask, P_bar, PET_bar):
    """
    Build spatially interpolated P_eff and PET surfaces for the steady-state
    solver. P_eff varies by cluster (C4 corrected for canopy interception);
    PET is spatially uniform at the site-mean value.
    """
    ref = wt["beta1"].notna()
    rpts = wt.loc[ref, ["E", "N"]].values

    P_eff_surf = interpolate_surface(
        rpts, wt.loc[ref, "P_eff"].values, grid_x, grid_y, mask)
    # PET is spatially uniform — fill grid
    PET_surf = np.full(grid_x.shape, PET_bar)
    PET_surf[~mask] = np.nan

    return P_eff_surf, PET_surf


# Cluster-mean depth of water table below ground surface (m).
# Derived from well observations: depth = DGPS_ground_elev - mean_head_maOD.
# Used to construct a DEM-derived head surface for blending.
# Overall site mean used as fallback for unclassified grid cells.
CLUSTER_DEPTH_BELOW_GROUND = {
    1: 0.296,   # C1 Eastern lake-buffer — very shallow (slack floors)
    2: 0.423,   # C2 Eastern mature dune
    3: 0.700,   # C3 Western mature dune
    4: 1.084,   # C4 Forest — deeper (canopy draws water table down)
    5: 0.984,   # C5 Coastal
    6: 7.456,   # C6 Llyn Rhos — corrected maOD (see note above)
}
SITE_MEAN_DEPTH = 0.585   # m — fallback for unclassified cells


def compute_darcy_flux(head_surface, thickness_surface, wt=None,
                       grid_x=None, grid_y=None, dem_path=None):
    """
    Darcy lateral flux: Q (m²/day) = -K × b × ∇h

    The head surface used for gradient computation is a blend of:
      - IDW head surface (from well observations) — accurate at well locations
      - DEM-derived head surface (DEM elevation - depth offset) — captures
        sub-grid topographic drainage channels between wells

    Blend weight alpha = exp(-d_min / BLEND_SCALE) where d_min is the
    distance to the nearest well. Close to wells (d < ~300 m) the IDW
    dominates; far from wells the DEM-derived surface dominates.

    The blending is physically motivated: in a shallow unconfined dune
    aquifer the water table is a subdued replica of the topography
    (correlation r=0.985 across 72 wells), so the DEM captures local
    drainage patterns that the sparse well IDW cannot resolve.

    If the DEM is unavailable, falls back to IDW-only with Gaussian smoothing.

    The negative sign ensures flow is in the direction of decreasing head.
    """
    BLEND_SCALE = 400.0   # m — e-folding distance for IDW→DEM blend

    # ── Try DEM-blended approach ───────────────────────────────────────────
    dem_blend_done = False
    if (dem_path is not None and dem_path.exists()
            and wt is not None and grid_x is not None):
        try:
            import rasterio
            from scipy.ndimage import zoom as nd_zoom

            with rasterio.open(str(dem_path)) as src:
                dem_arr  = src.read(1).astype(float)
                dem_ext  = [src.bounds.left, src.bounds.right,
                            src.bounds.bottom, src.bounds.top]
                res_x    = abs(src.transform.a)
                res_y    = abs(src.transform.e)
                nodata   = src.nodata

            if nodata is not None:
                dem_arr[dem_arr == nodata] = np.nan

            # Resample DEM to match head_surface grid using true bilinear
            # interpolation. Integer-index sampling creates aliasing artefacts
            # in the gradient (spotty flux vectors); scipy.ndimage.map_coordinates
            # with order=1 performs smooth bilinear interpolation.
            from scipy.ndimage import map_coordinates
            dem_ny, dem_nx = dem_arr.shape
            grid_E = grid_x[0, :]   # 1-D easting array
            grid_N = grid_y[:, 0]   # 1-D northing array
            # Continuous fractional pixel coordinates (origin upper-left)
            col_coords = (grid_E - dem_ext[0]) / res_x          # shape (nx,)
            row_coords = (dem_ext[3] - grid_N) / res_y           # shape (ny,)
            # meshgrid of fractional row/col for map_coordinates
            col_mesh, row_mesh = np.meshgrid(col_coords, row_coords)
            # Clip to valid range
            col_mesh = np.clip(col_mesh, 0, dem_nx - 1)
            row_mesh = np.clip(row_mesh, 0, dem_ny - 1)
            # Bilinear interpolation — order=1, no NaN propagation from edges
            dem_filled = np.where(np.isnan(dem_arr),
                                  np.nanmean(dem_arr), dem_arr)
            dem_grid = map_coordinates(dem_filled,
                                       [row_mesh.ravel(), col_mesh.ravel()],
                                       order=1, mode='nearest'
                                       ).reshape(grid_x.shape)
            # Restore NaN mask for cells outside DEM coverage
            nan_mask_dem = map_coordinates(
                np.isnan(dem_arr).astype(float),
                [row_mesh.ravel(), col_mesh.ravel()],
                order=1, mode='nearest').reshape(grid_x.shape) > 0.5
            dem_grid[nan_mask_dem] = np.nan

            # DEM-derived head: use a single site-mean depth offset
            # (cluster-specific would need cluster raster; mean is adequate
            # for gradient direction which is what matters here)
            dem_head = dem_grid - SITE_MEAN_DEPTH
            dem_head[np.isnan(dem_grid)] = np.nan

            # Distance to nearest well for blend weight
            well_pts = wt[["E", "N"]].values
            flat_pts = np.column_stack([grid_x.ravel(), grid_y.ravel()])
            # Approximate nearest-well distance via chunked min
            chunk = 500
            d_min = np.full(flat_pts.shape[0], np.inf)
            for i in range(0, len(well_pts), chunk):
                d = np.sqrt(((flat_pts[:, 0:1] - well_pts[i:i+chunk, 0])**2 +
                             (flat_pts[:, 1:2] - well_pts[i:i+chunk, 1])**2).min(axis=1))
                d_min = np.minimum(d_min, d)
            d_min = d_min.reshape(grid_x.shape)

            # Blend weight: 1 = pure IDW (at well), 0 = pure DEM (far from well)
            alpha = np.exp(-d_min / BLEND_SCALE)
            alpha[np.isnan(head_surface)] = np.nan

            # Blended head
            head_blend = (alpha * head_surface +
                          (1 - alpha) * dem_head)
            head_blend[np.isnan(head_surface)] = np.nan

            # Smooth before gradient to remove pixel-level DEM noise
            filled = np.nan_to_num(head_blend, nan=np.nanmean(head_blend))
            smooth = gaussian_filter(filled, sigma=1.5)
            smooth[np.isnan(head_blend)] = np.nan

            gx, gy = compute_gradient(smooth, GRID_RES)
            dem_blend_done = True

        except Exception as e:
            warnings.warn(f"DEM-blended head failed ({e}) — using IDW only.")

    # ── Fallback: IDW-only with Gaussian smoothing ─────────────────────────
    if not dem_blend_done:
        filled = np.nan_to_num(head_surface, nan=np.nanmean(head_surface))
        smooth = gaussian_filter(filled, sigma=2)
        smooth[np.isnan(head_surface)] = np.nan
        gx, gy = compute_gradient(smooth, GRID_RES)

    # Negative sign: flow is down-gradient (decreasing head)
    return -K_CENTRAL * thickness_surface * gx, -K_CENTRAL * thickness_surface * gy


# ============================================================================
# SCENARIO FRAMEWORK
# ============================================================================

def apply_scenario(wt, P_bar, PET_bar, scenario="baseline", params=None):
    """
    Modify β fields and/or climate inputs then recompute the water balance.

    Scenarios
    ---------
    baseline
        No modification. Observed 2005–2026 mean conditions.

    forest_removal
        C4 wells: β₂ increased (deeper summer draw without canopy shielding);
        interception correction removed (P_eff → P_bar).
        params: beta2_increase_fraction (default 0.15)

    forest_thinning
        Partial forest_removal scaled by thinning_fraction.
        params: thinning_fraction (default 0.5),
                beta2_increase_fraction (default 0.15)

    species_change
        Broadleaf conversion: autumn leaf-fall shifts interception loss to the
        recharge season. Implemented as β₁ reduction + removal of interception
        correction for C4 wells.
        params: winter_recharge_reduction (default 0.10)

    climate_change
        Option A — uniform head shift:
            params: delta_head_m
        Option B — climate input perturbation:
            params: delta_P_mm, delta_PET_mm (annual totals, mm/yr)

    annual_prediction
        Substitute observed P and PET for a specific year to test the model.
        params: P_mm, PET_mm (annual totals, mm/yr)

    Returns (wt_modified, P_mod, PET_mod, label)
    """
    if params is None:
        params = {}

    wt_s    = wt.copy()
    P_mod   = P_bar
    PET_mod = PET_bar

    def _h_eq(b1, b2, b3, P_eff, PET):
        """
        Analytical SSM equilibrium head:  0 = β₁·P_eff − β₂·PET − β₃·h_eq
        Returns the equilibrium head in head-space (m, negative = below ground).
        """
        if b3 <= 0:
            return np.nan
        return (b1 * P_eff - b2 * PET) / b3

    def _apply_eq_shift(df, mask, P_eff_base, P_eff_new, PET_new,
                        b1_mult=1.0, b2_mult=1.0):
        """
        Compute the SSM equilibrium head shift for rows matching mask and
        apply it uniformly to mean_head, winter_head, and summer_head.
        The shift is Δh = h_eq(modified) - h_eq(baseline) computed per well
        from its own β coefficients.  This gives spatially variable shifts
        within the cluster reflecting per-well β heterogeneity.
        """
        for idx in df[mask].index:
            b1 = df.at[idx, "beta1"] * b1_mult
            b2 = df.at[idx, "beta2"] * b2_mult
            b3 = df.at[idx, "beta3"]
            h_base = _h_eq(df.at[idx, "beta1"],
                           df.at[idx, "beta2"], b3, P_eff_base, PET_bar)
            h_new  = _h_eq(b1, b2, b3, P_eff_new, PET_new)
            if np.isnan(h_base) or np.isnan(h_new):
                continue
            delta = h_new - h_base
            df.at[idx, "mean_head"]   += delta
            df.at[idx, "winter_head"] += delta
            df.at[idx, "summer_head"] += delta
        return df

    def _apply_climate_shift(df, delta_P, delta_PET):
        """
        Apply a climate-driven equilibrium head shift to ALL wells using
        their individual β coefficients.
        """
        for idx in df.index:
            b1 = df.at[idx, "beta1"]
            b2 = df.at[idx, "beta2"]
            b3 = df.at[idx, "beta3"]
            P_eff_b = df.at[idx, "P_eff"]
            P_eff_n = P_eff_b + delta_P * (
                1 - FOREST_INTERCEPTION
                if pd.notna(df.at[idx, "cluster"])
                   and int(df.at[idx, "cluster"]) == 4
                else 1.0)
            PET_n = PET_bar + delta_PET
            h_base = _h_eq(b1, b2, b3, P_eff_b, PET_bar)
            h_new  = _h_eq(b1, b2, b3, P_eff_n, PET_n)
            if np.isnan(h_base) or np.isnan(h_new):
                continue
            delta = h_new - h_base
            df.at[idx, "mean_head"]   += delta
            df.at[idx, "winter_head"] += delta
            df.at[idx, "summer_head"] += delta
        return df

    def _recompute(df):
        df["recharge_m_mon"]  = df["beta1"] * df["P_eff"]
        df["et_draw_m_mon"]   = df["beta2"] * PET_mod
        df["drainage_m_mon"]  = df["beta3"] * df["mean_head"].abs()
        df["lateral_inflow_m_mon"] = (
            df["et_draw_m_mon"] + df["drainage_m_mon"] - df["recharge_m_mon"])
        df["head_swing"]        = df["winter_head"] - df["summer_head"]
        df["storage_change_mm"] = df["sy"] * df["head_swing"] * 1000.0
        # Recompute depth columns from updated head values
        if "dem_elev" in df.columns:
            df["mean_depth_bg"]   = df["dem_elev"] - df["mean_head"]
            df["winter_depth_bg"] = df["dem_elev"] - df["winter_head"]
            df["summer_depth_bg"] = df["dem_elev"] - df["summer_head"]
        return df

    c4 = wt_s["cluster"] == 4

    if scenario == "baseline":
        label = "Baseline — observed mean 2005–2026"

    elif scenario == "forest_removal":
        frac  = params.get("beta2_increase_fraction", 0.15)
        label = (f"Forest removal — C4 β₂ ×{1+frac:.2f}, "
                 "interception correction removed")
        wt_s.loc[c4, "beta2"] *= (1 + frac)
        wt_s.loc[c4, "P_eff"]  = P_bar
        wt_s = _apply_eq_shift(wt_s, c4,
                               P_eff_base=P_bar * (1 - FOREST_INTERCEPTION),
                               P_eff_new=P_bar,
                               PET_new=PET_bar, b2_mult=(1 + frac))
        wt_s = _recompute(wt_s)

    elif scenario == "forest_thinning":
        thin  = params.get("thinning_fraction", 0.5)
        frac  = params.get("beta2_increase_fraction", 0.15) * thin
        label = (f"Forest thinning — {int(thin*100)}% of removal effect "
                 f"(C4 β₂ ×{1+frac:.2f})")
        wt_s.loc[c4, "beta2"] *= (1 + frac)
        P_eff_new_thin = P_bar * (1 - FOREST_INTERCEPTION * (1 - thin))
        wt_s.loc[c4, "P_eff"]  = P_eff_new_thin
        wt_s = _apply_eq_shift(wt_s, c4,
                               P_eff_base=P_bar * (1 - FOREST_INTERCEPTION),
                               P_eff_new=P_eff_new_thin,
                               PET_new=PET_bar, b2_mult=(1 + frac))
        wt_s = _recompute(wt_s)

    elif scenario == "species_change":
        reduction = params.get("winter_recharge_reduction", 0.10)
        label = (f"Broadleaf conversion — C4 β₁ ×{1-reduction:.2f} "
                 "(autumn leaf-fall removes recharge-season shielding)")
        wt_s.loc[c4, "beta1"] *= (1 - reduction)
        # Broadleaf replaces pine interception (24%) with deciduous
        # interception (~15%) — does NOT remove interception entirely.
        # The β₁ reduction captures loss of recharge-season shielding
        # when autumn leaf-fall coincides with recharge season onset.
        P_eff_broadleaf = P_bar * (1 - BROADLEAF_INTERCEPTION)
        wt_s.loc[c4, "P_eff"]  = P_eff_broadleaf
        wt_s = _apply_eq_shift(wt_s, c4,
                               P_eff_base=P_bar * (1 - FOREST_INTERCEPTION),
                               P_eff_new=P_eff_broadleaf,
                               PET_new=PET_bar, b1_mult=(1 - reduction))
        wt_s = _recompute(wt_s)

    elif scenario == "climate_change":
        if "delta_head_m" in params:
            delta = params["delta_head_m"]
            label = f"Climate change — uniform Δh = {delta:+.2f} m"
            for col in ["mean_head", "winter_head", "summer_head"]:
                wt_s[col] += delta
            wt_s = _recompute(wt_s)
        else:
            delta_P   = params.get("delta_P_mm",   0) / 1000 / 12
            delta_PET = params.get("delta_PET_mm", 0) / 1000 / 12
            P_mod   = P_bar   + delta_P
            PET_mod = PET_bar + delta_PET
            label = (f"Climate change — ΔP = {params.get('delta_P_mm',0):+.0f} mm/yr, "
                     f"ΔPET = {params.get('delta_PET_mm',0):+.0f} mm/yr")
            wt_s["P_eff"] = wt_s.apply(
                lambda r: P_mod * (1 - FOREST_INTERCEPTION)
                if pd.notna(r["cluster"]) and int(r["cluster"]) == 4
                else P_mod, axis=1)
            wt_s = _apply_climate_shift(wt_s, delta_P, delta_PET)
            wt_s = _recompute(wt_s)

    elif scenario == "annual_prediction":
        P_mm    = params.get("P_mm",   P_bar   * 12 * 1000)
        PET_mm  = params.get("PET_mm", PET_bar * 12 * 1000)
        P_mod   = P_mm   / 1000 / 12
        PET_mod = PET_mm / 1000 / 12
        label = (f"Annual prediction — P = {P_mm:.0f} mm, "
                 f"PET = {PET_mm:.0f} mm")
        wt_s["P_eff"] = wt_s.apply(
            lambda r: P_mod * (1 - FOREST_INTERCEPTION)
            if pd.notna(r["cluster"]) and int(r["cluster"]) == 4
            else P_mod, axis=1)
        wt_s = _recompute(wt_s)

    else:
        raise ValueError(
            f"Unknown scenario: '{scenario}'. Choose from: baseline, "
            "forest_removal, forest_thinning, species_change, "
            "climate_change, annual_prediction.")

    return wt_s, P_mod, PET_mod, label


# ============================================================================
# FIGURE SIZE AND DPI CONSTANTS
# ============================================================================
# JHRS column widths: single = 88 mm (3.46 in), double = 180 mm (7.09 in)
# Site aspect ratio (N/E extent) ≈ 0.67 → height ≈ width × 0.75 with legends
# All figures saved at 300 dpi (journal minimum) with tight bbox

FIG_DPI         = 300
FIG_SINGLE_W    = 7.09    # in — full double-column width
FIG_SINGLE_H    = 5.8     # in — height for single map panel
FIG_TWO_PANEL_W = 14.0    # in — two panels side by side
FIG_TWO_PANEL_H = 5.8     # in
FIG_THREE_W     = 14.0    # in — three panels (beta fields)
FIG_THREE_H     = 5.2     # in
FIG_FOUR_W      = 18.0    # in — four panels (water balance)
FIG_FOUR_H      = 5.0     # in
FIG_FONT_TITLE  = 9       # pt — title fontsize for paper figures
FIG_FONT_LABEL  = 8       # pt — axis label fontsize
FIG_FONT_TICK   = 7       # pt — tick label fontsize
FIG_FONT_ANNOT  = 6       # pt — annotation fontsize
FIG_FONT_CB     = 7       # pt — colorbar label fontsize


# ============================================================================
# MAP SETUP HELPERS
# ============================================================================

def _base_map(ax, features, title, fs=FIG_FONT_TITLE):
    """
    Standard map axis setup shared by all figures.
    Renders greyscale DEM hillshade (via map_utils.load_dem_hillshade) then
    KML overlays. Returns KML legend handles.
    """
    ax.set_facecolor("white")
    ax.set_aspect("equal")
    ax.set_xlim(240100, 243900)
    ax.set_ylim(362200, 365800)
    ax.set_title(title, fontsize=fs, fontweight="bold", pad=6)
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=FIG_FONT_LABEL)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=FIG_FONT_LABEL)
    ax.tick_params(labelsize=FIG_FONT_TICK)
    load_dem_hillshade(ax, DATA_DIR, alpha=0.35)
    return add_kml_overlays(ax, features)


def _scatter_wells(ax, wt, s=30, zorder=8):
    """Well locations coloured by cluster."""
    for _, row in wt.iterrows():
        cl = int(row["cluster"]) if pd.notna(row["cluster"]) else 3
        ax.scatter(row["E"], row["N"],
                   c=CLUSTER_COLOURS.get(cl, "grey"),
                   s=s, edgecolors="white", linewidths=0.5,
                   marker="o", zorder=zorder, alpha=0.9)


def _annotate(ax, text):
    ax.annotate(text, xy=(0.02, 0.02), xycoords="axes fraction",
                fontsize=FIG_FONT_ANNOT, color="dimgrey",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))


def _quiver(ax, Qx, Qy, grid_x, grid_y, **kw):
    """Normalised flow-direction arrows at ~150 m spacing."""
    step = max(1, int(150 / GRID_RES))
    Qs_x = Qx[::step, ::step]
    Qs_y = Qy[::step, ::step]
    mag  = np.sqrt(Qs_x**2 + Qs_y**2)
    with np.errstate(invalid="ignore"):
        Qs_x = np.where(mag > 0, Qs_x / mag, 0)
        Qs_y = np.where(mag > 0, Qs_y / mag, 0)
    ax.quiver(grid_x[::step, ::step], grid_y[::step, ::step],
              Qs_x, Qs_y, **kw)


def _kml_legend(ax, handles, loc="upper right"):
    if handles:
        ax.legend(handles=handles, title="Site features",
                  loc=loc, fontsize=7, framealpha=0.85,
                  title_fontsize=7)


# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def plot_thickness(grid_x, grid_y, thickness, wt, features, out_path=None):
    fig, ax = plt.subplots(figsize=(FIG_SINGLE_W, FIG_SINGLE_H), dpi=FIG_DPI)
    kml_handles = _base_map(ax, features,
        "Aquifer Thickness Surface — Newborough Warren\n"
        "(IDW from Bristow/Connell borehole constraints + cluster priors)")

    im = ax.pcolormesh(grid_x, grid_y, thickness, cmap="YlOrBr",
                       shading="auto", vmin=0, vmax=22, alpha=0.75, zorder=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("Estimated aquifer thickness (m)", fontsize=9)

    # Borehole constraint nodes
    hd_sc = ax.scatter(
        [n[0] for n in THICKNESS_NODES],
        [n[1] for n in THICKNESS_NODES],
        c=[n[2] for n in THICKNESS_NODES],
        cmap="YlOrBr", vmin=0, vmax=22,
        s=40, edgecolors="black", linewidths=0.8,
        marker="D", zorder=9)
    _scatter_wells(ax, wt, s=35, zorder=8)

    legend_handles = [
        Line2D([0], [0], marker="D", color="w", markerfacecolor="black",
               markersize=5, linestyle="None", label="Borehole constraint"),
    ] + kml_handles
    ax.legend(handles=legend_handles, loc="lower right",
              fontsize=7, framealpha=0.85)

    _annotate(ax,
              f"Cluster priors: C3/C4 = {CLUSTER_THICKNESS_PRIOR[3]} m  "
              f"(C4 = C3; CEH14 overridden to 5 m),  "
              f"C1/C2 = {CLUSTER_THICKNESS_PRIOR[1]} m.\n"
              "CEH7/CEH8 = 1 m (estuarine pinch-out).  "
              "Borehole constraints: Bristow (2002) / Connell (2003).  IDW power = 1.")
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_THICKNESS_MAP, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_THICKNESS_MAP.name}")


def plot_head_mean(grid_x, grid_y, head_mean, Qx, Qy, wt, features,
                   depth_mean=None, out_path=None):
    """
    Mean annual water table map.

    If depth_mean (DEM - head) is supplied, shows depth below ground surface
    with ecological zone colouring (same thresholds as 11b_spatial_thresholds).
    Falls back to absolute head (m AOD) if depth surface is unavailable.
    """
    from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
    import matplotlib.patches as mpatches

    fig, ax = plt.subplots(figsize=(FIG_SINGLE_W, FIG_SINGLE_H), dpi=FIG_DPI)

    use_depth = depth_mean is not None and not np.all(np.isnan(depth_mean))

    if use_depth:
        title = ("Mean Annual Water Table — Depth Below Ground (m)\n"
                 f"Newborough Warren 2005–2026  |  "
                 f"Darcy flux vectors K = {K_CENTRAL} m/day (Betson et al. 2002)")
    else:
        title = ("Mean Annual Water Table Elevation (m AOD) — Newborough Warren 2005–2026\n"
                 f"Indicative Darcy flux vectors  (K = {K_CENTRAL} m/day, Betson et al. 2002)")

    kml_handles = _base_map(ax, features, title)

    if use_depth:
        # Ecological zone colouring — Curreli et al. (2013) thresholds
        SD15b, SD15b_REC, SD16, SD16_REC = 0.61, 0.75, 0.98, 1.20
        bounds   = [0.0, SD15b, SD15b_REC, SD16, SD16_REC, 3.5]
        colors_z = ["#1a7abf","#a8d8a8","#ffffb2","#fd8d3c","#bd0026"]
        cmap_z   = LinearSegmentedColormap.from_list("slack", colors_z, N=256)
        norm_z   = BoundaryNorm(bounds, ncolors=256)
        im = ax.pcolormesh(grid_x, grid_y, depth_mean, cmap=cmap_z,
                           norm=norm_z, shading="auto", alpha=0.72, zorder=2)
        cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02,
                          boundaries=bounds,
                          ticks=[0, SD15b, SD15b_REC, SD16, SD16_REC, 3.0])
        cb.set_label("Mean depth below ground (m)", fontsize=9)
        cb.ax.set_yticklabels(["0 m\n(flooding)", f"{SD15b} m\nSD15b",
                               f"{SD15b_REC} m\nSD15b\nrecovery",
                               f"{SD16} m\nSD16",
                               f"{SD16_REC} m\nSD16\nrecovery", "3.0 m"],
                              fontsize=7)
        # Threshold contours on depth surface
        for level, col, lw, ls in [(SD15b, "#005fa3", 1.5, "--"),
                                    (SD16,  "#a30000", 1.5, "--"),
                                    (SD16_REC, "#4a0000", 1.2, "-.")]:
            try:
                import warnings as _w
                with _w.catch_warnings():
                    _w.simplefilter("ignore")
                    ax.contour(grid_x, grid_y, depth_mean, levels=[level],
                               colors=[col], linewidths=lw, linestyles=ls,
                               alpha=0.80, zorder=3)
            except Exception:
                pass
        # Also show 1m head contours on underlying maOD surface for reference
        try:
            cs = ax.contour(grid_x, grid_y, head_mean, levels=10,
                            colors="navy", linewidths=0.4, alpha=0.35, zorder=3)
            ax.clabel(cs, inline=True, fontsize=5, fmt="%.0f m AOD")
        except Exception:
            pass
    else:
        vmin, vmax = np.nanpercentile(head_mean, 2), np.nanpercentile(head_mean, 98)
        im = ax.pcolormesh(grid_x, grid_y, head_mean, cmap="Blues_r",
                           shading="auto", vmin=vmin, vmax=vmax, alpha=0.75, zorder=2)
        cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
        cb.set_label("Water table elevation (m AOD)", fontsize=9)
        try:
            cs = ax.contour(grid_x, grid_y, head_mean, levels=10,
                            colors="navy", linewidths=0.5, alpha=0.6, zorder=3)
            ax.clabel(cs, inline=True, fontsize=6, fmt="%.1f m")
        except Exception:
            pass

    _quiver(ax, Qx, Qy, grid_x, grid_y,
            color="white", alpha=0.85, scale=30, width=0.003, zorder=9)
    _scatter_wells(ax, wt)
    _kml_legend(ax, kml_handles)
    _annotate(ax,
              f"Arrow direction only (normalised).  "
              f"K = {K_CENTRAL} m/day (range {K_LOW}–{K_HIGH} m/day).\n"
              "Curreli et al. (2013) ecological thresholds.")
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_HEAD_MEAN_MAP, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_HEAD_MEAN_MAP.name}")


def plot_seasonal(grid_x, grid_y, head_winter, head_summer, wt, features,
                  depth_winter=None, depth_summer=None, out_path=None):
    """
    Seasonal head contrast — winter max and summer min.
    Shows depth below ground if depth surfaces are supplied,
    otherwise falls back to absolute head (m AOD).
    """
    from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm

    use_depth = (depth_winter is not None and depth_summer is not None
                 and not np.all(np.isnan(depth_winter)))

    fig, axes = plt.subplots(1, 2, figsize=(FIG_TWO_PANEL_W, FIG_TWO_PANEL_H), dpi=FIG_DPI)

    if use_depth:
        # Ecological zone colouring — same as 11b and plot_head_mean
        SD15b, SD15b_REC, SD16, SD16_REC = 0.61, 0.75, 0.98, 1.20
        bounds   = [0.0, SD15b, SD15b_REC, SD16, SD16_REC, 3.5]
        colors_z = ["#1a7abf","#a8d8a8","#ffffb2","#fd8d3c","#bd0026"]
        cmap_z   = LinearSegmentedColormap.from_list("slack", colors_z, N=256)
        norm_z   = BoundaryNorm(bounds, ncolors=256)
        pairs = [(depth_winter, "Mean Winter Depth Below Ground (Nov–Mar, m)",
                  head_winter),
                 (depth_summer, "Mean Summer Depth Below Ground (May–Sep, m)",
                  head_summer)]
        cb_label = "Depth below ground (m)"
    else:
        vmin = np.nanmin([np.nanpercentile(head_winter, 2),
                          np.nanpercentile(head_summer, 2)])
        vmax = np.nanmax([np.nanpercentile(head_winter, 98),
                          np.nanpercentile(head_summer, 98)])
        pairs = [(head_winter, "Mean Winter Water Table (Nov–Mar, m AOD)", None),
                 (head_summer, "Mean Summer Water Table (May–Sep, m AOD)", None)]
        cb_label = "Water table elevation (m AOD)"

    for ax, (surf, lbl, head_surf) in zip(axes, pairs):
        kml_h = _base_map(ax, features, lbl)
        if use_depth:
            im = ax.pcolormesh(grid_x, grid_y, surf, cmap=cmap_z,
                               norm=norm_z, shading="auto", alpha=0.72, zorder=2)
            for level, col, lw, ls in [(SD15b, "#005fa3", 1.5, "--"),
                                        (SD16,  "#a30000", 1.5, "--")]:
                try:
                    import warnings as _w
                    with _w.catch_warnings():
                        _w.simplefilter("ignore")
                        ax.contour(grid_x, grid_y, surf, levels=[level],
                                   colors=[col], linewidths=lw, linestyles=ls,
                                   alpha=0.80, zorder=3)
                except Exception:
                    pass
            if head_surf is not None:
                try:
                    cs = ax.contour(grid_x, grid_y, head_surf, levels=8,
                                    colors="navy", linewidths=0.4,
                                    alpha=0.30, zorder=3)
                    ax.clabel(cs, inline=True, fontsize=5, fmt="%.0f m AOD")
                except Exception:
                    pass
        else:
            im = ax.pcolormesh(grid_x, grid_y, surf, cmap="Blues_r",
                               shading="auto", vmin=vmin, vmax=vmax,
                               alpha=0.75, zorder=2)
            try:
                cs = ax.contour(grid_x, grid_y, surf, levels=8,
                                colors="navy", linewidths=0.5, alpha=0.5, zorder=3)
                ax.clabel(cs, inline=True, fontsize=6, fmt="%.1f m")
            except Exception:
                pass
        _scatter_wells(ax, wt, s=20)
        cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cb.set_label(cb_label, fontsize=9)
        _kml_legend(ax, kml_h)

    fig.suptitle("Seasonal Water Table Contrast — Newborough Warren 2005–2026",
                 fontsize=11, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_HEAD_SEASONAL, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_HEAD_SEASONAL.name}")


def plot_beta_fields(grid_x, grid_y, b1_surf, b2_surf, b3_surf, wt, features, out_path=None):
    panels = [
        (b1_surf, "β₁  Recharge coefficient", "YlGn",   "beta1"),
        (b2_surf, "β₂  ET-draw coefficient",  "YlOrRd", "beta2"),
        (b3_surf, "β₃  Drainage coefficient", "PuBu",   "beta3"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(FIG_THREE_W, FIG_THREE_H), dpi=FIG_DPI)
    for ax, (surf, title, cmap, col) in zip(axes, panels):
        kml_h = _base_map(ax, features, title, fs=10)
        vmin, vmax = np.nanpercentile(surf, 2), np.nanpercentile(surf, 98)
        im = ax.pcolormesh(grid_x, grid_y, surf, cmap=cmap,
                           shading="auto", vmin=vmin, vmax=vmax,
                           alpha=0.75, zorder=2)
        cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cb.set_label(f"{col} (m/month per m forcing)", fontsize=8)
        valid = wt[col].notna()
        ax.scatter(wt.loc[valid, "E"], wt.loc[valid, "N"],
                   c=wt.loc[valid, col], cmap=cmap, vmin=vmin, vmax=vmax,
                   s=55, edgecolors="black", linewidths=0.6, zorder=9)
        _kml_legend(ax, kml_h)

    fig.suptitle(
        "Spatially Interpolated SSM β-coefficient Fields — "
        "Newborough Warren 2005–2026\n"
        f"(IDW from {INT_MASTER_DATA.name}, reference wells only)",
        fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_BETA_FIELDS, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_BETA_FIELDS.name}")


def plot_water_balance(grid_x, grid_y, wt, features,
                       recharge_surf, et_surf, drainage_surf, lateral_surf, out_path=None):
    panels = [
        (recharge_surf, "Recharge  (β₁ × P̄_eff)\nm/month",             "YlGn",   False),
        (et_surf,       "ET draw  (β₂ × PET̄)\nm/month",                 "YlOrRd", False),
        (drainage_surf, "Drainage  (β₃ × |h̄|)\nm/month",                "PuBu",   False),
        (lateral_surf,  "Lateral inflow residual\nm/month\n"
                        "(positive = ridge inflow)",                      "RdBu_r", True),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(FIG_FOUR_W, FIG_FOUR_H), dpi=FIG_DPI)
    for ax, (surf, title, cmap, diverging) in zip(axes, panels):
        kml_h = _base_map(ax, features, title, fs=9)
        if diverging:
            vmax = np.nanpercentile(np.abs(surf), 97)
            norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
            im = ax.pcolormesh(grid_x, grid_y, surf, cmap=cmap,
                               norm=norm, shading="auto", alpha=0.75, zorder=2)
        else:
            vmin, vmax = np.nanpercentile(surf, 2), np.nanpercentile(surf, 98)
            im = ax.pcolormesh(grid_x, grid_y, surf, cmap=cmap,
                               shading="auto", vmin=vmin, vmax=vmax,
                               alpha=0.75, zorder=2)
        cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cb.ax.tick_params(labelsize=FIG_FONT_TICK)
        _scatter_wells(ax, wt, s=18)
        _kml_legend(ax, kml_h)

    fig.suptitle(
        "Spatial Water Balance Fields — Newborough Warren 2005–2026\n"
        f"(β coefficients from {INT_MASTER_DATA.name}, IDW-interpolated)",
        fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_WATER_BALANCE, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_WATER_BALANCE.name}")


def plot_flux_magnitude(grid_x, grid_y, Qx, Qy, wt, features, out_path=None):
    fig, ax = plt.subplots(figsize=(FIG_SINGLE_W, FIG_SINGLE_H), dpi=FIG_DPI)
    kml_handles = _base_map(ax, features,
        f"Indicative Darcy Lateral Flux — Newborough Warren 2005–2026\n"
        f"K = {K_CENTRAL} m/day  (range {K_LOW}–{K_HIGH} m/day;  Betson et al. 2002)")

    mag = np.sqrt(Qx**2 + Qy**2)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_mag = np.where(mag > 0, np.log10(mag), np.nan)
    im = ax.pcolormesh(grid_x, grid_y, log_mag, cmap="plasma",
                       shading="auto", alpha=0.75, zorder=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("Flux magnitude — log₁₀(m²/day)", fontsize=9)

    _quiver(ax, Qx, Qy, grid_x, grid_y,
            color="white", alpha=0.7, scale=35, width=0.002, zorder=9)
    _scatter_wells(ax, wt, s=30)
    _kml_legend(ax, kml_handles)
    _annotate(ax,
              "Exploratory analysis only. K uncertain at field scale.\n"
              "Values should not be used without independent calibration.")
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_FLUX_MAP, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_FLUX_MAP.name}")


def plot_residual_comparison(wt, Qx, Qy, grid_x, grid_y, features, mask, sea_pts=None, sea_vals=None, out_path=None):
    """
    The validation figure — scientific core of Chapter 6.

    Left:  SSM lateral inflow residual — derived from β coefficients only.
    Right: Darcy flux magnitude — derived from observed heads only.

    Spatial agreement of the two independent methods confirms that the
    ridge-derived lateral inflow identified by the SSM is physically real.
    """
    fig, axes = plt.subplots(1, 2, figsize=(FIG_TWO_PANEL_W, FIG_TWO_PANEL_H), dpi=FIG_DPI)

    # Left — SSM residual
    ax = axes[0]
    kml_h0 = _base_map(ax, features,
        "SSM Lateral Inflow Residual  (m/month)\n"
        "(β₂·PET̄ + β₃·|h̄| − β₁·P̄_eff) — β coefficients only")

    ref  = wt["lateral_inflow_m_mon"].notna()
    rpts = wt.loc[ref, ["E", "N"]].values
    rval = wt.loc[ref, "lateral_inflow_m_mon"].values
    resid_surf = interpolate_surface(rpts, rval, grid_x, grid_y, mask)
    vmax = np.nanpercentile(np.abs(resid_surf), 97)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    ax.pcolormesh(grid_x, grid_y, resid_surf, cmap="RdBu_r",
                  norm=norm, shading="auto", alpha=0.75, zorder=2)
    fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap="RdBu_r"),
        ax=ax, fraction=0.035, pad=0.02
    ).set_label("Lateral inflow (m/month)\npositive = ridge inflow", fontsize=8)
    ax.scatter(wt.loc[ref, "E"], wt.loc[ref, "N"],
               c=rval, cmap="RdBu_r", norm=norm,
               s=70, edgecolors="black", linewidths=0.8, zorder=9)
    _kml_legend(ax, kml_h0)
    _annotate(ax,
              f"Method: SSM β coefficients ({INT_MASTER_DATA.name}).\n"
              "No Darcy physics — independent of right panel.")

    # Right — Darcy flux
    ax = axes[1]
    kml_h1 = _base_map(ax, features,
        f"Darcy Lateral Flux Magnitude  (m²/day, log scale)\n"
        f"K × b × |∇h|,  K = {K_CENTRAL} m/day (Betson et al. 2002) — observed heads only")

    mag = np.sqrt(Qx**2 + Qy**2)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_mag = np.where(mag > 0, np.log10(mag), np.nan)
    im1 = ax.pcolormesh(grid_x, grid_y, log_mag, cmap="plasma",
                        shading="auto", alpha=0.75, zorder=2)
    fig.colorbar(im1, ax=ax, fraction=0.035, pad=0.02
                 ).set_label("log₁₀(m²/day)", fontsize=8)
    _quiver(ax, Qx, Qy, grid_x, grid_y,
            color="white", alpha=0.6, scale=35, width=0.002, zorder=9)
    _scatter_wells(ax, wt, s=30)
    _kml_legend(ax, kml_h1)
    _annotate(ax,
              f"Head data: {INT_WELLS_CLEAN_MAOD.name}.\n"
              "No β coefficients — independent of left panel.")

    fig.suptitle(
        "Independent Validation — SSM Lateral Inflow Residual vs Darcy Flux\n"
        "Newborough Warren 2005–2026  |  "
        "Spatial agreement confirms ridge-derived boundary subsidy",
        fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_RESIDUAL_COMP, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_RESIDUAL_COMP.name}")


def plot_storage_change(grid_x, grid_y, storage_surf, wt, features, out_path=None):
    fig, ax = plt.subplots(figsize=(FIG_SINGLE_W, FIG_SINGLE_H), dpi=FIG_DPI)
    kml_handles = _base_map(ax, features,
        "Seasonal Storage Change  (Sy × Head Swing)\n"
        "Newborough Warren 2005–2026  [mm water equivalent]")

    vmax = np.nanpercentile(np.abs(storage_surf), 97)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    ax.pcolormesh(grid_x, grid_y, storage_surf, cmap="RdBu",
                  norm=norm, shading="auto", alpha=0.75, zorder=2)
    fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap="RdBu"),
        ax=ax, fraction=0.03, pad=0.02
    ).set_label("Seasonal storage change (mm)", fontsize=9)
    ax.scatter(wt["E"], wt["N"],
               c=wt["storage_change_mm"], cmap="RdBu", norm=norm,
               s=65, edgecolors="black", linewidths=0.8, zorder=9)
    _kml_legend(ax, kml_handles)
    sy_source = (OUT_18_WELL_SY_TABLE.name
                 if OUT_18_WELL_SY_TABLE.exists()
                 else "cluster defaults (run script 18 for per-well values)")
    _annotate(ax,
              "Storage change = Sy × (mean winter head − mean summer head) × 1000.\n"
              f"Sy source: {sy_source}.")
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_STORAGE_MAP, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_STORAGE_MAP.name}")


# ============================================================================
def plot_depth_to_watertable(grid_x, grid_y, wt, features, out_path=None):
    """
    Spatial map of modelled depth to water table below ground surface.

    Depth is derived directly from the pipeline field measurements
    (01_wells_clean.csv, upstand-corrected by script 03) — the same data
    the SSM was fitted to. This makes the figure a direct spatial display
    of the model output, not a DEM-arithmetic approximation.

    Convention: negative = below ground (dry); positive = above ground (flooding).

    The DEM is NOT used as the reference surface here — it overestimates
    ground elevation at well locations by mean +9 cm (up to +71 cm) due
    to LiDAR returns from vegetation and pipe tops.

    Three panels stacked vertically:
      Top:    Mean annual depth — overall wetness pattern
      Middle: Summer minimum depth (May–Sep) — most critical for slack ecology
      Bottom: Flooding frequency — fraction of months depth >= 0

    Slack thresholds from Curreli et al. (2013):
      SD15b wet slack: 0.61 m below ground surface
      SD16  dry slack: 0.98 m below ground surface
    Positive depth = below ground; negative = flooding (WT above ground).
    """
    mask = make_site_mask(grid_x, grid_y)
    try:
        maod = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
        maod.columns = [normalize_well_name(c) for c in maod.columns]
    except Exception as _e:
        warnings.warn(f"Could not load maOD data ({_e}) — depth-to-WT figure skipped.")
        return

    # ── Build per-well depth statistics using DEM_Ground_Elev - maOD ─────
    # Convention: positive = below ground surface (dry); negative = flooding.
    # This matches 11b_spatial_thresholds and plot_head_mean conventions.
    # Uses DEM_Ground_Elev from well_elevations.csv as the ground reference,
    # which is consistent with the rest of the pipeline.
    _summer_months = [8, 9]   # August-September (peak dry season)
    _winter_months = [10,11,12,1,2,3]
    _E, _N = [], []
    _mean_d, _summer_d, _flood_f = [], [], []

    for _, row in wt.iterrows():
        w = row["well"]
        dem_elev = row.get("dem_elev", np.nan)
        if pd.isna(dem_elev):
            continue
        if w not in maod.columns:
            continue
        series = maod[w].dropna()
        if len(series) < 20:
            continue
        # depth_bg = DEM_Ground_Elev - maOD head
        # positive = below ground, negative = flooding
        dbg = dem_elev - series
        summer = dbg[dbg.index.month.isin(_summer_months)]
        winter = dbg[dbg.index.month.isin(_winter_months)]
        _E.append(row["E"])
        _N.append(row["N"])
        _mean_d.append(float(dbg.mean()))
        _summer_d.append(float(summer.mean()) if len(summer) > 0 else float(dbg.mean()))
        # Flooding = depth_bg < 0 (water table above ground)
        _flood_f.append(float((dbg < 0).mean()))

    if len(_E) < 4:
        warnings.warn("Too few wells for depth-to-WT interpolation — figure skipped.")
        return

    wdp = np.column_stack([_E, _N])
    surf_mean   = interpolate_surface(wdp, np.array(_mean_d),   grid_x, grid_y, mask)
    surf_summer = interpolate_surface(wdp, np.array(_summer_d), grid_x, grid_y, mask)
    surf_flood  = interpolate_surface(wdp, np.array(_flood_f),  grid_x, grid_y, mask)
    surf_flood  = np.clip(surf_flood, 0, 1)

    print(f"  Depth-to-WT: {len(_E)} wells used (DEM ground surface reference)")
    wells_flooding = sum(1 for f in _flood_f if f > 0.01)
    print(f"  Wells with >1% flooding frequency: {wells_flooding}")

    # ── Figure — three panels stacked vertically ──────────────────────────
    fig, axes = plt.subplots(1, 3,
                             figsize=(FIG_THREE_W, FIG_THREE_H + 0.5),
                             dpi=FIG_DPI)

    # Colour scale: blue = wet/flooding, red = deep/dry
    # Positive = below ground, negative = flooding
    # Range: -0.3 m (flooding) to +2.0 m (deep dry)
    DEPTH_MIN = -0.3
    DEPTH_MAX =  2.0
    depth_cmap = "RdYlBu_r"   # blue = wet (near zero/negative), red = dry (positive)

    from matplotlib.lines import Line2D as _L2D

    # Threshold handles for legend (Curreli et al. 2013)
    thresh_handles = [
        _L2D([0],[0], color="navy",    lw=1.4, ls="-",
             label="Flooding (WT at surface, 0 m)"),
        _L2D([0],[0], color="#1565C0", lw=1.0, ls="--",
             label="SD15b wet slack (0.61 m)"),
        _L2D([0],[0], color="#E65100", lw=1.0, ls="--",
             label="SD16 dry slack (0.98 m)"),
    ]

    for ax, surf, title in zip(
            axes[:2],
            [surf_mean, surf_summer],
            ["Mean annual depth below ground (m)\nDEM ground surface reference",
             "Mean summer minimum depth (Aug-Sep, m)\nDEM ground surface reference"]):

        kml_h = _base_map(ax, features, title)
        im = ax.pcolormesh(grid_x, grid_y, surf,
                           cmap=depth_cmap,
                           vmin=DEPTH_MIN, vmax=DEPTH_MAX,
                           shading="auto", alpha=0.80, zorder=2)
        cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
        cb.set_label("Depth below ground (m;\n+ve = below surface, -ve = flooding)",
                     fontsize=FIG_FONT_CB)
        cb.ax.tick_params(labelsize=FIG_FONT_TICK)

        # Flooding contour (depth = 0)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ax.contour(grid_x, grid_y, surf, levels=[0],
                           colors=["navy"], linewidths=1.4, zorder=6)
        except Exception:
            pass
        # SD15b wet slack contour at 0.61 m depth
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ax.contour(grid_x, grid_y, surf, levels=[0.61],
                           colors=["#1565C0"], linewidths=1.0,
                           linestyles=["--"], zorder=6)
        except Exception:
            pass
        # SD16 dry slack contour at 0.98 m depth
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ax.contour(grid_x, grid_y, surf, levels=[0.98],
                           colors=["#E65100"], linewidths=1.0,
                           linestyles=["--"], zorder=6)
        except Exception:
            pass

        # Scatter wells coloured by observed depth
        well_vals = np.array(_mean_d if surf is surf_mean else _summer_d)
        sc = ax.scatter(_E, _N, c=well_vals, cmap=depth_cmap,
                        vmin=DEPTH_MIN, vmax=DEPTH_MAX,
                        s=20, edgecolors="k", linewidths=0.3,
                        zorder=8)
        _kml_legend(ax, kml_h, loc="lower right")

    axes[0].legend(handles=thresh_handles, fontsize=FIG_FONT_ANNOT,
                   loc="upper right", framealpha=0.85)

    # Bottom panel — flooding frequency
    ax = axes[2]
    kml_h = _base_map(ax, features,
                      "Flooding frequency (fraction of months WT >= ground surface)")
    im3 = ax.pcolormesh(grid_x, grid_y, surf_flood,
                        cmap="Blues", vmin=0, vmax=0.5,
                        shading="auto", alpha=0.80, zorder=2)
    cb3 = fig.colorbar(im3, ax=ax, fraction=0.03, pad=0.02)
    cb3.set_label("Fraction of months flooded", fontsize=FIG_FONT_CB)
    cb3.ax.tick_params(labelsize=FIG_FONT_TICK)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ax.contour(grid_x, grid_y, surf_flood, levels=[0.1, 0.25],
                       colors=["steelblue", "navy"],
                       linewidths=[0.8, 1.0], zorder=6)
    except Exception:
        pass
    ax.scatter(_E, _N, c=_flood_f, cmap="Blues", vmin=0, vmax=0.5,
               s=20, edgecolors="k", linewidths=0.3, zorder=8)
    _kml_legend(ax, kml_h, loc="lower right")
    _annotate(ax, "Flooding frequency: fraction of months where\n"
              "water table exceeds DEM ground surface elevation.\n"
              "Contours at 10% and 25% flooding frequency.")

    fig.suptitle(
        "Water Table Depth Below Ground — Newborough Warren 2005-2026\n"
        "DEM ground surface reference (LiDAR).  "
        "Slack thresholds: Curreli et al. (2013)",
        fontsize=FIG_FONT_TITLE, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_DEPTH_TO_WT, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_DEPTH_TO_WT.name}")



def plot_winter_flooding(grid_x, grid_y, wt, features, out_path=None):
    """
    Winter water table depth and flooding extent from upstand-corrected
    field observations (Nov-Mar). Direct spatial test of the SSM.

    Left:  Winter mean depth to WT with SD15b (0.10 m) and SD16 (0.25 m)
           winter thresholds (Curreli et al. 2013)
    Right: Fraction of winter months with flooding (WT >= ground surface)
    """
    mask = make_site_mask(grid_x, grid_y)
    try:
        maod = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
        maod.columns = [normalize_well_name(c) for c in maod.columns]
    except Exception as _e:
        warnings.warn(f"Could not load maOD data ({_e}) — winter flooding skipped.")
        return

    _E, _N, _wmean, _wfreq = [], [], [], []
    for _, row in wt.iterrows():
        w = row["well"]
        dem_elev = row.get("dem_elev", np.nan)
        if pd.isna(dem_elev):
            continue
        if w not in maod.columns:
            continue
        series = maod[w].dropna()
        winter = series[series.index.month.isin(WINTER_MONTHS)]
        if len(winter) < 10:
            continue
        # depth_bg = DEM_Ground_Elev - maOD (positive = below ground)
        dbg = dem_elev - winter
        _E.append(row["E"]); _N.append(row["N"])
        _wmean.append(float(dbg.mean()))
        # Flooding = depth_bg < 0 (water table above ground surface)
        _wfreq.append(float((dbg < 0).mean()))

    if len(_E) < 4:
        warnings.warn("Too few wells for winter flooding map.")
        return

    wdp = np.column_stack([_E, _N])
    surf_wmean = interpolate_surface(wdp, np.array(_wmean), grid_x, grid_y, mask)
    # Convert fraction to mean months flooded per winter (Nov-Mar = 5 months)
    _wfreq_months = [f * 5 for f in _wfreq]
    surf_wfreq = np.clip(
        interpolate_surface(wdp, np.array(_wfreq_months), grid_x, grid_y, mask), 0, 5)

    n_flood = sum(1 for f in _wfreq if f > 0.10)
    print(f"  Winter flooding: {len(_E)} wells; {n_flood} flood >10% of winter months")

    from matplotlib.lines import Line2D as _L2D
    fig, axes = plt.subplots(1, 2, figsize=(FIG_TWO_PANEL_W, FIG_TWO_PANEL_H),
                             dpi=FIG_DPI)

    # Left — winter mean depth
    ax = axes[0]
    kml_h = _base_map(ax, features, "Winter mean depth below ground (Nov-Mar, m)\nDEM ground surface reference")
    im = ax.pcolormesh(grid_x, grid_y, surf_wmean, cmap="RdBu_r",
                       vmin=-0.3, vmax=1.5, shading="auto", alpha=0.80, zorder=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("Depth below ground (m;\n+ve = below surface, -ve = flooding)", fontsize=FIG_FONT_CB)
    cb.ax.tick_params(labelsize=FIG_FONT_TICK)
    for level, color, lw in [(0, "navy", 1.6), (0.10, "#1565C0", 1.0),
                              (0.25, "#E65100", 1.0)]:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ax.contour(grid_x, grid_y, surf_wmean, levels=[level],
                           colors=[color], linewidths=lw,
                           linestyles=["-" if level == 0 else "--"], zorder=6)
        except Exception:
            pass
    ax.scatter(_E, _N, c=_wmean, cmap="RdBu_r", vmin=-0.3, vmax=1.5,
               s=20, edgecolors="k", linewidths=0.3, zorder=8)
    ax.legend(handles=[
        _L2D([0],[0], color="navy",    lw=1.6, ls="-",  label="Flooding (WT at surface, 0 m)"),
        _L2D([0],[0], color="#1565C0", lw=1.0, ls="--", label="SD15b winter (0.10 m below)"),
        _L2D([0],[0], color="#E65100", lw=1.0, ls="--", label="SD16 winter (0.25 m below)"),
    ], fontsize=FIG_FONT_ANNOT, loc="upper right", framealpha=0.85)
    _kml_legend(ax, kml_h, loc="lower right")

    # Right — flooding frequency
    ax = axes[1]
    kml_h = _base_map(ax, features,
                      "Winter flooding frequency (fraction of Nov-Mar months)")
    im2 = ax.pcolormesh(grid_x, grid_y, surf_wfreq, cmap="Blues",
                        vmin=0, vmax=3.0, shading="auto", alpha=0.80, zorder=2)
    cb2 = fig.colorbar(im2, ax=ax, fraction=0.03, pad=0.02)
    cb2.set_label("Mean months flooded per winter (Nov-Mar)", fontsize=FIG_FONT_CB)
    cb2.ax.tick_params(labelsize=FIG_FONT_TICK)
    for level, color, lw in [(1.0, "steelblue", 0.9), (2.5, "navy", 1.2)]:
        try:
            ax.contour(grid_x, grid_y, surf_wfreq, levels=[level],
                       colors=[color], linewidths=lw, zorder=6)
        except Exception:
            pass
    ax.scatter(_E, _N, c=_wfreq_months, cmap="Blues", vmin=0, vmax=3.0,
               s=20, edgecolors="k", linewidths=0.3, zorder=8)
    _annotate(ax, "Mean months flooded per winter (Nov-Mar, 5 months).\n"
              "Contours at 1 month and 2.5 months per winter.")
    _kml_legend(ax, kml_h, loc="lower right")

    fig.suptitle(
        "Winter Water Table and Flooding Extent — Newborough Warren 2005-2026\n"
        "DEM ground surface reference (LiDAR).  "
        "Thresholds: Curreli et al. (2013)",
        fontsize=FIG_FONT_TITLE, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path or OUT_19_WINTER_FLOOD, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_19_WINTER_FLOOD.name}")


def main(scenario="baseline", scenario_params=None, output_dir=None,
         supplementary=False):
    # Resolve output directory — defaults to DIR_19 from paths.py
    # When called from the scenario runner, output_dir points to the
    # scenario-specific subfolder so all outputs land there cleanly.
    _out = Path(output_dir) if output_dir is not None else DIR_19
    _out.mkdir(parents=True, exist_ok=True)
    make_all_dirs()

    # Build local output paths (override module-level constants if output_dir given)
    _paths = {
        "thickness_map":  _out / OUT_19_THICKNESS_MAP.name,
        "head_mean_map":  _out / OUT_19_HEAD_MEAN_MAP.name,
        "head_seasonal":  _out / OUT_19_HEAD_SEASONAL.name,
        "beta_fields":    _out / OUT_19_BETA_FIELDS.name,
        "water_balance":  _out / OUT_19_WATER_BALANCE.name,
        "flux_map":       _out / OUT_19_FLUX_MAP.name,
        "residual_comp":  _out / OUT_19_RESIDUAL_COMP.name,
        "storage_map":    _out / OUT_19_STORAGE_MAP.name,
        "depth_to_wt":    _out / OUT_19_DEPTH_TO_WT.name,
        "winter_flood":   _out / OUT_19_WINTER_FLOOD.name,
        "thickness_csv":  _out / OUT_19_THICKNESS_CSV.name,
        "head_mean_csv":  _out / OUT_19_HEAD_MEAN_CSV.name,
        "wb_summary_csv": _out / OUT_19_WB_SUMMARY_CSV.name,
    }

    print("=" * 60)
    print("Script 19 — Spatial Groundwater Analysis")
    print(f"Scenario      : {scenario}")
    print(f"Supplementary : {supplementary}")
    print("=" * 60)

    print("\n[1/7] Loading data...")
    data = load_data()

    print("\n[2/7] Building well table...")
    wt_base, P_bar, PET_bar = build_well_table(data)

    print(f"\n[3/7] Applying scenario '{scenario}'...")
    wt, P_mod, PET_mod, label = apply_scenario(
        wt_base, P_bar, PET_bar,
        scenario=scenario, params=scenario_params or {})
    print(f"  {label}")

    print("\n[4/7] Building grid and interpolating surfaces...")
    grid_x, grid_y = build_grid(wt)
    print(f"  Grid: {grid_x.shape[1]} × {grid_x.shape[0]} cells at {GRID_RES} m")

    # Site mask — covers full dune system to shoreline (not convex hull)
    mask = make_site_mask(grid_x, grid_y)

    # Sea boundary anchor points — zero head at shoreline
    sea_pts, sea_vals = _sea_boundary_points()

    # ── β and water-balance fields (IDW — reference wells only) ─────────────
    ref  = wt["beta1"].notna()
    rpts = wt.loc[ref, ["E", "N"]].values
    beta1_surf    = interpolate_surface(rpts, wt.loc[ref, "beta1"].values,                grid_x, grid_y, mask)
    beta2_surf    = interpolate_surface(rpts, wt.loc[ref, "beta2"].values,                grid_x, grid_y, mask)
    beta3_surf    = interpolate_surface(rpts, wt.loc[ref, "beta3"].values,                grid_x, grid_y, mask)
    recharge_surf = interpolate_surface(rpts, wt.loc[ref, "recharge_m_mon"].values,       grid_x, grid_y, mask)
    et_surf       = interpolate_surface(rpts, wt.loc[ref, "et_draw_m_mon"].values,        grid_x, grid_y, mask)
    drainage_surf = interpolate_surface(rpts, wt.loc[ref, "drainage_m_mon"].values,       grid_x, grid_y, mask)
    lateral_surf  = interpolate_surface(rpts, wt.loc[ref, "lateral_inflow_m_mon"].values, grid_x, grid_y, mask)

    print("  Interpolating aquifer thickness...")
    thickness = build_thickness_surface(wt, grid_x, grid_y, mask)

    # ── Head surfaces — IDW with sea boundary anchors ────────────────────
    # The steady-state PDE solver (solve_steady_state_head) is available
    # for scenario difference computation in 19a_scenario_runner.py.
    # For the primary figures, IDW with sea boundary anchors gives the best
    # visual result — it honours the well observations directly and blends
    # smoothly to 0 m AOD at the coast.
    well_pts = wt[["E", "N"]].values
    pts_with_sea  = np.vstack([well_pts, sea_pts])
    head_aug      = np.concatenate([wt["mean_head"].values,  sea_vals])
    winter_aug    = np.concatenate([wt["winter_head"].values, sea_vals])
    summer_aug    = np.concatenate([wt["summer_head"].values, sea_vals])
    storage_aug   = np.concatenate([wt["storage_change_mm"].values,
                                    np.zeros(len(sea_vals))])
    head_mean    = interpolate_surface(pts_with_sea, head_aug,    grid_x, grid_y, mask)
    head_winter  = interpolate_surface(pts_with_sea, winter_aug,  grid_x, grid_y, mask)
    head_summer  = interpolate_surface(pts_with_sea, summer_aug,  grid_x, grid_y, mask)
    storage_surf = interpolate_surface(pts_with_sea, storage_aug, grid_x, grid_y, mask)

    # ── Depth-below-ground surfaces (DEM elevation − head) ───────────────
    # Interpolate well DEM elevations to grid — sea anchors not used here
    # as DEM elevation is not defined at sea.
    # Positive depth = below ground surface; negative = flooding.
    dem_valid = wt["dem_elev"].notna()
    dem_pts   = wt.loc[dem_valid, ["E", "N"]].values
    if dem_valid.sum() >= 3:
        dem_surf     = interpolate_surface(dem_pts, wt.loc[dem_valid, "dem_elev"].values,
                                           grid_x, grid_y, mask)
        depth_mean   = dem_surf - head_mean
        depth_winter = dem_surf - head_winter
        depth_summer = dem_surf - head_summer
    else:
        warnings.warn("Insufficient DEM elevations for depth surfaces — using NaN.")
        depth_mean   = np.full(grid_x.shape, np.nan)
        depth_winter = np.full(grid_x.shape, np.nan)
        depth_summer = np.full(grid_x.shape, np.nan)
        dem_surf     = np.full(grid_x.shape, np.nan)

    print("  Computing Darcy flux...")
    Qx, Qy = compute_darcy_flux(head_mean, thickness,
                                           wt=wt, grid_x=grid_x, grid_y=grid_y,
                                           dem_path=DATA_DEM)

    print("\n[5/7] Loading basemap assets...")
    dem_loaded = DATA_DIR.joinpath("newborough_dem.tif").exists()
    if dem_loaded:
        print("  DEM hillshade will be rendered via map_utils.load_dem_hillshade")
    else:
        print(f"  DEM not found at {DATA_DIR / 'newborough_dem.tif'} — plain white background")
    features = load_kml_features()
    print(f"  {len(features)} KML layer(s) loaded")

    print("\n[6/7] Saving CSVs...")
    pd.DataFrame({
        "Easting":   grid_x.ravel(),
        "Northing":  grid_y.ravel(),
        "Head_maOD": head_mean.ravel(),
    }).dropna(subset=["Head_maOD"]).to_csv(_paths["head_mean_csv"], index=False)
    print(f"  Saved: {OUT_19_HEAD_MEAN_CSV.name}")

    pd.DataFrame({
        "Easting":     grid_x.ravel(),
        "Northing":    grid_y.ravel(),
        "Thickness_m": thickness.ravel(),
    }).dropna(subset=["Thickness_m"]).to_csv(_paths["thickness_csv"], index=False)
    print(f"  Saved: {OUT_19_THICKNESS_CSV.name}")

    wb_cols = ["well", "E", "N", "cluster", "beta1", "beta2", "beta3", "sy",
               "mean_head", "winter_head", "summer_head", "head_swing",
               "mean_depth_bg", "winter_depth_bg", "summer_depth_bg",
               "P_eff", "recharge_m_mon", "et_draw_m_mon", "drainage_m_mon",
               "lateral_inflow_m_mon", "storage_change_mm", "dem_elev"]
    wt[[c for c in wb_cols if c in wt.columns]].to_csv(
        _paths["wb_summary_csv"], index=False)
    print(f"  Saved: {OUT_19_WB_SUMMARY_CSV.name}  ({len(wt)} wells)")

    print("\n[7/7] Producing figures...")

    # ── Paper figures — always generated ─────────────────────────────────
    try:
        plot_head_mean(grid_x, grid_y, head_mean, Qx, Qy, wt, features,
                      depth_mean=depth_mean,
                      out_path=_paths['head_mean_map'])
    except Exception as _e:
        print(f"  [ERROR] plot_head_mean failed: {_e}")
        import traceback; traceback.print_exc()

    try:
        plot_residual_comparison(wt, Qx, Qy, grid_x, grid_y, features, mask,
                                out_path=_paths['residual_comp'])
    except Exception as _e:
        print(f"  [ERROR] plot_residual_comparison failed: {_e}")
        import traceback; traceback.print_exc()

    # ── Supplementary figures — only generated with --supplementary flag ──
    # These support the online supplementary materials but are not cited
    # in the main paper body.
    if supplementary:
        print("  Generating supplementary figures...")
        plot_thickness(grid_x, grid_y, thickness, wt, features,
                      out_path=_paths['thickness_map'])
        plot_seasonal(grid_x, grid_y, head_winter, head_summer, wt, features,
                     depth_winter=depth_winter, depth_summer=depth_summer,
                     out_path=_paths['head_seasonal'])
        plot_beta_fields(grid_x, grid_y, beta1_surf, beta2_surf, beta3_surf, wt, features,
                        out_path=_paths['beta_fields'])
        plot_water_balance(grid_x, grid_y, wt, features,
                           recharge_surf, et_surf, drainage_surf, lateral_surf,
                           out_path=_paths['water_balance'])
        plot_flux_magnitude(grid_x, grid_y, Qx, Qy, wt, features,
                           out_path=_paths['flux_map'])
        plot_storage_change(grid_x, grid_y, storage_surf, wt, features,
                           out_path=_paths['storage_map'])
        plot_depth_to_watertable(grid_x, grid_y, wt, features,
                                out_path=_paths['depth_to_wt'])
        plot_winter_flooding(grid_x, grid_y, wt, features,
                            out_path=_paths['winter_flood'])
    else:
        print("  Supplementary figures skipped (pass --supplementary to generate)")

    print("\n--- Script 19 complete ---")
    print(f"Scenario  : {label}")
    print(f"Wells     : {len(wt)}  (β available for {wt['beta1'].notna().sum()})")
    print(f"Grid      : {grid_x.shape[1]} × {grid_x.shape[0]}  at {GRID_RES} m")
    print(f"K         : {K_CENTRAL} m/day  (range {K_LOW}–{K_HIGH} m/day)")
    print(f"P̄ used    : {P_mod*12*1000:.0f} mm/yr   "
          f"PET̄ used : {PET_mod*12*1000:.0f} mm/yr")
    print(f"DEM       : {'hillshade (greyscale, via map_utils)' if dem_loaded else 'not found — plain white background'}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Script 19 — Spatial Groundwater Analysis")
    parser.add_argument("--scenario", default="baseline",
                        choices=["baseline", "forest_removal", "forest_thinning",
                                 "species_change", "climate_change", "annual_prediction"])
    parser.add_argument("--supplementary", action="store_true",
                        help="Also generate supplementary figures (thickness, "
                             "seasonal, beta fields, water balance, flux, storage, "
                             "depth-to-WT, winter flooding). Default: paper figures only.")
    parser.add_argument("--P_mm",           type=float, default=None,
                        help="Annual rainfall (mm/yr) for annual_prediction")
    parser.add_argument("--PET_mm",         type=float, default=None,
                        help="Annual PET (mm/yr) for annual_prediction")
    parser.add_argument("--delta_head",     type=float, default=None,
                        help="Uniform head shift (m) for climate_change")
    parser.add_argument("--delta_P_mm",     type=float, default=None,
                        help="Annual rainfall change (mm/yr) for climate_change")
    parser.add_argument("--delta_PET_mm",   type=float, default=None,
                        help="Annual PET change (mm/yr) for climate_change")
    parser.add_argument("--beta2_increase", type=float, default=None,
                        help="C4 β₂ increase fraction for forest_removal (e.g. 0.15)")
    parser.add_argument("--thinning",       type=float, default=None,
                        help="Thinning fraction (0–1) for forest_thinning")
    args = parser.parse_args()

    params = {}
    if args.P_mm is not None:           params["P_mm"]                   = args.P_mm
    if args.PET_mm is not None:         params["PET_mm"]                  = args.PET_mm
    if args.delta_head is not None:     params["delta_head_m"]            = args.delta_head
    if args.delta_P_mm is not None:     params["delta_P_mm"]              = args.delta_P_mm
    if args.delta_PET_mm is not None:   params["delta_PET_mm"]            = args.delta_PET_mm
    if args.beta2_increase is not None: params["beta2_increase_fraction"] = args.beta2_increase
    if args.thinning is not None:       params["thinning_fraction"]       = args.thinning

    main(scenario=args.scenario, scenario_params=params,
         supplementary=args.supplementary)
