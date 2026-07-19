"""
utils/map_utils.py
Shared GIS and map plotting helpers used across all spatial output scripts.

Key functions
-------------
load_dem_layer(ax, data_dir)
    Loads the site DEM onto an existing axes object using a coloured terrain
    colormap. Returns the image layer (for colorbar attachment) and a boolean
    indicating success. Used by all point-symbol metric maps (scripts 04, 07,
    08, 12, 13, 18).

load_dem_hillshade(ax, data_dir, alpha, vert_exag, zorder)
    Loads the site DEM as a greyscale hillshade (LightSource, azdeg=315,
    altdeg=35) onto an existing axes object. Returns the pcolormesh layer and
    a boolean indicating success. Used by continuous-surface maps where the
    metric surface is overlaid semi-transparently on top (scripts 11b, 19, 20).

add_kml_features(ax, data_dir)
    Overlays Features.kml, streams.kml, and clearfell.kml onto an axes object.
    Returns a list of legend handles for the features drawn.

add_osm_basemap(ax, gdf)
    Fallback basemap from OpenStreetMap when the DEM is unavailable.

add_idw_surface(ax, df, value_col, xi, yi, method, ridge_mask_threshold,
                dem_e_arr, dem_n_arr, dem_data, cmap, norm, alpha, zorder,
                apply_site_mask)
    IDW-interpolates a per-well metric to a regular grid, applies an optional
    ridge mask (cells where the DEM sits more than ridge_mask_threshold metres
    above the IDW-interpolated well-DEM surface are masked), and renders as a
    pcolormesh. Optional apply_site_mask=True clips the surface to the NNR
    site boundary via make_site_mask(). Returns (pcolormesh_object, grid_x,
    grid_y, surf_masked) so the caller can attach a colorbar and draw contours.
    Used by scripts 11b, 18, 19, 20.

make_site_mask(grid_x, grid_y)
    Boolean mask for the IDW interpolation domain clipped to the NNR site
    boundary. Primary path: XML parse of site_boundary.kml → OSGB36 polygon.
    Fallback: rectangular clip to three sea-boundary lines. Moved from Script 18
    (v1.4.0) so all IDW-surface scripts share one implementation.

plot_metric_map(map_df, value_col, title, output_path, cmap, data_dir, vmin, vmax)
    Full publication-quality spatial metric map with DEM background, KML overlays,
    cluster-shape markers, dual colorbars, and legend.
"""

__version__ = "1.6.0"  # Hollingham (2026) — 2026-07-19
# 1.6.0 (2026-07-19): legibility hand pass — add_en_axes default tick
#   labelsize 8 -> 9 and axis label_fontsize 9 -> 10 (axis labels +1 pt on
#   all maps using the defaults); plot_metric_map BW value labels 6 -> 6.5
#   (well labels +0.5 pt). No call-site changes.
# 1.5.0 — add_idw_surface() gains hull_buffer_m parameter (default 100.0 m).
#         Linear griddata is NaN outside the convex hull of the wells, so an
#         observed-data surface stops at the outer well ring, short of the coast
#         (no dipwells sit seaward). The buffer fills NaN cells within the well
#         hull dilated by hull_buffer_m using nearest-neighbour values, extending
#         the surface a fixed distance past the outermost wells. Fill runs before
#         ridge/site masking, so the extension is still clipped to the shoreline
#         and dune ridges. Default 100 m applies to ALL callers (Scripts 07, 10b,
#         11b, 18, 19, 26, 33, 36); set hull_buffer_m=None for the strict
#         hull-bounded surface. Pure extrapolation over unmeasured ground —
#         intentionally bounded and small.
# 1.4.0 — make_site_mask() moved here from Script 18 so all IDW-surface scripts
#         share one implementation. add_idw_surface() gains apply_site_mask
#         parameter (default False): when True calls make_site_mask(gx, gy)
#         internally and masks the surface before rendering, replacing the
#         per-function site-mask calls in Script 18. add_idw_surface() default
#         xi/yi grid corrected from stale literals (240200–243800, 362200–365800)
#         to SITE_MAP_* canonical values (240100–243900, 362200–365500).
#         DATA_KML_SITE_BOUNDARY added to paths import (required by
#         make_site_mask()). Three sea-boundary fallback constants added
#         (_SEA_SOUTH_N, _SEA_EAST_E, _SEA_WEST_E).
# 1.3.0 — Canonical map frame + Easting/Northing axes consolidated here.
#         New public helper add_en_axes(ax, apply_extent=True) sets the
#         canonical site extent from config.SITE_MAP_* (E 240100–243900,
#         N 362200–365500), forces equal aspect (true OS-grid scale, identical
#         extent across panels), draws plain 6-digit E/N axes (no offset), and
#         labels them "Easting/Northing (m, OSGB36)". Every map function in the
#         pipeline (except scripts 12 and 13) now calls this instead of carrying
#         its own xlim/ylim/aspect/tick logic; the previous hardcoded extent in
#         plot_metric_map (240100/243900/362200/365800) is removed and replaced
#         by add_en_axes(). apply_extent=False draws the E/N axes but leaves the
#         caller's xlim/ylim intact (for the rare figure that legitimately needs
#         a wider window for an in-data legend).
# 1.2.0 — Scrape footprints are now a shared site feature. add_kml_features()
#         gains include_scrapes=True and draws the GPS-traced scrape outlines
#         (navy solid; black dotted in BW) with a "Scrape footprints" legend
#         entry, so every map that calls it shows them. New public loader
#         load_scrape_kml() (promoted from Script 20's private _load_one_scrape_kml,
#         now the single implementation). Footprint list from config.SCRAPE_KML_FILES.
# 1.1.0 — data/geo/ reorg: geo inputs now resolved from utils.paths constants
#         (DATA_DEM, DATA_KML_FEATURES, DATA_KML_STREAMS, DATA_KML_CLEARFELL)
#         instead of reconstructing data_dir / "X". The data_dir parameter is
#         retained in every signature (vestigial but harmless) so the 22
#         call sites need no change. No functional change to rendering.
# 1.0.x — Initial.

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LightSource
import geopandas as gpd
import contextily as ctx
import fiona
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.interpolate import griddata, RegularGridInterpolator
from pathlib import Path

from utils.config import (
    BW_MODE, CLUSTER_LABELS, CLUSTER_MARKERS, DEM_VMIN, DEM_VCENTER, DEM_VMAX,
    FEATURE_COLOUR_SCRAPE, SCRAPE_KML_FILES,
    SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX, SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX,
)
from utils.paths import (
    DATA_DEM, DATA_KML_FEATURES, DATA_KML_STREAMS, DATA_KML_CLEARFELL,
    DATA_KML_SITE_BOUNDARY, data_geo,
)

fiona.drvsupport.supported_drivers["KML"] = "rw"


# ── Canonical site extent, re-exported for callers that need the raw tuple ────
SITE_XLIM = (SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
SITE_YLIM = (SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)

# ── Sea-boundary fallback constants for make_site_mask() ──────────────────────
# Used only when site_boundary.kml KML parse fails.
_SEA_SOUTH_N = 362350   # m OSGB36 — southern shoreline Northing
_SEA_EAST_E  = 243850   # m OSGB36 — eastern (Menai Strait) Easting
_SEA_WEST_E  = 239200   # m OSGB36 — western estuary Easting


def add_en_axes(ax, apply_extent: bool = True, labelsize: int = 9,
                label_fontsize: int = 10, osgb_label: bool = True):
    """
    Apply the canonical Easting/Northing axes treatment to a map axes.

    This is the single place the pipeline's OS-grid maps get their frame and
    scale, so every map (except scripts 12 and 13) renders the site at one
    identical, undistorted extent.

    Does, in order:
      1. (if apply_extent) set xlim/ylim to the canonical site extent from
         config.SITE_MAP_* — E 240100–243900, N 362200–365500.
      2. set_aspect("equal") — true OS-grid scale; identical extent across
         panels regardless of differing colorbars/legends.
      3. plain 6-digit tick labels with no "+2.4e5" offset.
      4. labelled "Easting (m, OSGB36)" / "Northing (m, OSGB36)" axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    apply_extent : bool, default True
        If True, set the canonical xlim/ylim. Pass False to keep the caller's
        own xlim/ylim (used only where a figure legitimately needs a wider
        window for an in-data legend) while still drawing E/N axes and equal
        aspect.
    labelsize : int, default 9
        Tick label font size.
    label_fontsize : int, default 10
        Axis label font size.
    osgb_label : bool, default True
        If True, axis labels read "Easting (m, OSGB36)"; if False, the shorter
        "Easting (m)" used by the §4.9 differential-movement maps (scripts
        32/33).

    Returns
    -------
    ax : matplotlib.axes.Axes
        The same axes (for chaining).
    """
    if apply_extent:
        ax.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
        ax.set_ylim(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX)
    ax.set_aspect("equal")
    ax.tick_params(labelsize=labelsize)
    ax.ticklabel_format(style="plain", useOffset=False)
    suffix = ", OSGB36" if osgb_label else ""
    ax.set_xlabel(f"Easting (m{suffix})", fontsize=label_fontsize)
    ax.set_ylabel(f"Northing (m{suffix})", fontsize=label_fontsize)
    return ax


def _safe_read_kml(path_obj):
    """Read a KML file, returning None and printing a warning on failure."""
    try:
        return gpd.read_file(str(path_obj), driver="KML")
    except Exception as exc:
        print(f"  [WARNING] Skipping {Path(path_obj).name}: KML unavailable ({exc})")
        return None


def load_dem_layer(ax, data_dir: Path):
    """
    Load the site DEM and render it onto ax.

    In BW_MODE, redirects to load_dem_hillshade() with faint alpha to
    produce a clean, almost-white background for print. The return
    signature is (layer, loaded) — callers that need dem arrays should
    use load_dem_hillshade() or load_dem_auto() directly.

    Uses a custom terrain colormap with TwoSlopeNorm anchored at sea level (0 m),
    the dune crest inflection (12 m), and the DEM maximum. Sub-zero pixels are
    painted dodgerblue to represent water.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    data_dir : Path

    Returns
    -------
    dem_layer : AxesImage or None
        The imshow layer, suitable for attaching a colorbar.
    dem_loaded : bool
    """
    # BW mode: use faint hillshade instead of coloured terrain
    if BW_MODE:
        result = load_dem_hillshade(ax, data_dir)
        return result[0], result[1]

    dem_path = DATA_DEM
    if not dem_path.exists():
        return None, False

    try:
        import rasterio

        with rasterio.open(str(dem_path)) as src:
            dem_data = src.read(1)
            extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
            if src.nodata is not None:
                dem_data = np.ma.masked_where(dem_data == src.nodata, dem_data)

            terrain_colors = plt.cm.terrain(np.linspace(0.25, 1.0, 256))
            custom_topo = mcolors.LinearSegmentedColormap.from_list(
                "custom_topo", terrain_colors
            )
            custom_topo.set_under("dodgerblue")

            div_norm = mcolors.TwoSlopeNorm(
                vmin=DEM_VMIN, vcenter=DEM_VCENTER, vmax=DEM_VMAX
            )
            dem_layer = ax.imshow(
                dem_data,
                cmap=custom_topo,
                alpha=0.45,
                norm=div_norm,
                extent=extent,
                origin="upper",
                zorder=1,
            )
            ax.set_xlim(extent[0], extent[1])
            ax.set_ylim(362000, 365000)
            return dem_layer, True

    except Exception as e:
        print(f"  [WARNING] DEM load failed: {e}. Falling back to OSM.")
        return None, False


def load_dem_hillshade(
    ax,
    data_dir: Path,
    alpha: float = 1.0,
    vert_exag: float = 3.0,
    azdeg: float = 315.0,
    altdeg: float = 35.0,
    zorder: int = 1,
):
    """
    Load the site DEM as a greyscale hillshade and render onto ax.

    In BW_MODE, alpha is capped at 0.35 to produce a faint, almost-white
    background that prints cleanly — matching Script 18's proven rendering.
    Callers that explicitly pass a low alpha (e.g. alpha=0.35) are unaffected.

    Uses matplotlib.colors.LightSource to compute an illuminated surface.
    Intended as the base layer for continuous-surface maps (scripts 11b, 19,
    20) where a semi-transparent metric surface is overlaid on top. Contrast
    with load_dem_layer() which uses a coloured terrain colormap and is suited
    to point-symbol maps.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    data_dir : Path
        Directory containing newborough_dem.tif.
    alpha : float
        Opacity of the hillshade layer (default 1.0 — fully opaque base).
    vert_exag : float
        Vertical exaggeration for the hillshade (default 3.0).
    azdeg : float
        Azimuth of the light source in degrees (default 315 — NW).
    altdeg : float
        Altitude of the light source in degrees (default 35).
    zorder : int
        Drawing order (default 1 — bottom layer).

    Returns
    -------
    hs_mesh : QuadMesh or None
        The pcolormesh layer. None if DEM unavailable.
    dem_loaded : bool
    dem_e_arr : np.ndarray or None
        1-D array of easting coordinates matching DEM columns.
    dem_n_arr : np.ndarray or None
        1-D array of northing coordinates matching DEM rows (top to bottom).
    dem_data : np.ndarray or None
        2-D DEM elevation array (NaN where nodata). Returned so callers can
        use it for ridge masking without re-reading the file.
    """
    dem_path = DATA_DEM
    if not dem_path.exists():
        print(f"  [WARNING] DEM not found at {dem_path}")
        return None, False, None, None, None

    try:
        import rasterio

        with rasterio.open(str(dem_path)) as src:
            raw = src.read(1).astype(float)
            transform = src.transform
            res_x = abs(transform.a)
            res_y = abs(transform.e)
            dem_e_arr = transform.c + np.arange(raw.shape[1]) * transform.a
            dem_n_arr = transform.f + np.arange(raw.shape[0]) * transform.e
            if src.nodata is not None:
                raw[raw == src.nodata] = np.nan

        dem_data = raw.copy()
        # Fill NaN for hillshade computation (NaN produces artefacts)
        filled = np.nan_to_num(raw, nan=0.0)

        ls = LightSource(azdeg=azdeg, altdeg=altdeg)
        hs = ls.hillshade(filled, vert_exag=vert_exag, dx=res_x, dy=res_y)

        DEM_E, DEM_N = np.meshgrid(dem_e_arr, dem_n_arr)
        # BW mode: cap alpha at 0.35 for faint, almost-white background
        _alpha = min(alpha, 0.35) if BW_MODE else alpha
        hs_mesh = ax.pcolormesh(
            DEM_E, DEM_N, hs,
            cmap="gray", shading="auto",
            vmin=0.2, vmax=1.0,
            alpha=_alpha, zorder=zorder,
        )
        return hs_mesh, True, dem_e_arr, dem_n_arr, dem_data

    except Exception as exc:
        print(f"  [WARNING] Hillshade load failed: {exc}")
        return None, False, None, None, None


def load_dem_auto(ax, data_dir: Path, force_hillshade: bool = False):
    """Route to hillshade or coloured DEM based on BW_MODE.

    In BW_MODE (or when force_hillshade=True), uses the light-grey
    hillshade basemap which prints cleanly. In colour mode, uses the
    full terrain colormap.

    Returns
    -------
    For hillshade mode: (hs_mesh, dem_loaded, dem_e_arr, dem_n_arr, dem_data)
        — same as load_dem_hillshade().
    For colour mode: (dem_layer, dem_loaded)
        — same as load_dem_layer(), with three extra Nones for API compat.

    Usage
    -----
    result = load_dem_auto(ax, data_dir)
    dem_loaded = result[1]
    # If you need dem arrays for ridge masking etc:
    # dem_e, dem_n, dem_data = result[2], result[3], result[4]
    """
    if BW_MODE or force_hillshade:
        return load_dem_hillshade(ax, data_dir)
    else:
        layer, loaded = load_dem_layer(ax, data_dir)
        return layer, loaded, None, None, None


def make_site_mask(grid_x: np.ndarray, grid_y: np.ndarray) -> np.ndarray:
    """
    Boolean mask for an IDW interpolation grid, clipped to the NNR site boundary.

    Primary path: pure XML + pyproj + shapely parse of site_boundary.kml
    (falls back to streams.kml if absent). No fiona/KML driver required.
    Fallback: rectangular clip to three sea-boundary lines (_SEA_*).

    Moved from Script 18 (v1.4.0) so all IDW-surface scripts share one
    implementation.

    Parameters
    ----------
    grid_x, grid_y : np.ndarray
        2-D meshgrid arrays of Easting and Northing (EPSG:27700).

    Returns
    -------
    mask : np.ndarray of bool, same shape as grid_x
        True where the grid cell lies inside the site boundary.
    """
    import warnings
    flat = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    _bnd_path = DATA_KML_SITE_BOUNDARY
    if not _bnd_path.exists():
        _bnd_path = DATA_KML_STREAMS

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
                            try:
                                pts.append((float(p[0]), float(p[1])))
                            except ValueError:
                                pass
                    if len(pts) >= 3:
                        lons = [pt[0] for pt in pts]
                        lats = [pt[1] for pt in pts]
                        ex, ny = _tr.transform(lons, lats)
                        try:
                            _polys.append(_Poly(zip(ex, ny)))
                        except Exception:
                            pass
                for child in el:
                    _parse(child)

            _parse(_root)

            if _polys:
                _dissolved = _union(_polys)
                _dissolved = _dissolved.buffer(100)
                if _dissolved.geom_type == "MultiPolygon":
                    _dissolved = max(_dissolved.geoms, key=lambda g: g.area)
                _coords = list(_dissolved.exterior.coords)
                _path = _MplPath([(c[0], c[1]) for c in _coords])
                _inside = _path.contains_points(flat)
                print(f"  Site mask: {_inside.sum()} of {len(_inside)} "
                      f"grid cells inside boundary")
                return _inside.reshape(grid_x.shape)

        except Exception as e:
            warnings.warn(
                f"site_boundary.kml mask failed ({e}) — "
                "falling back to rectangular sea-boundary mask."
            )

    # Fallback: rectangular clip to three sea-boundary lines
    mask = np.ones(grid_x.shape, dtype=bool)
    mask[grid_y < _SEA_SOUTH_N] = False
    mask[grid_x > _SEA_EAST_E]  = False
    mask[grid_x < _SEA_WEST_E]  = False
    return mask


def add_idw_surface(
    ax,
    df: pd.DataFrame,
    value_col: str,
    easting_col: str = "E",
    northing_col: str = "N",
    dem_col: str = "dem",
    xi: np.ndarray = None,
    yi: np.ndarray = None,
    method: str = "linear",
    ridge_mask_threshold: float = 1.0,
    dem_e_arr: np.ndarray = None,
    dem_n_arr: np.ndarray = None,
    dem_data: np.ndarray = None,
    cmap=None,
    norm=None,
    alpha: float = 0.65,
    zorder: int = 2,
    vmin: float = None,
    vmax: float = None,
    apply_site_mask: bool = False,
    hull_buffer_m: float = 100.0,
):
    """
    Interpolate a per-well metric to a regular grid and render as pcolormesh.

    Applies an optional ridge mask: grid cells where the DEM raster elevation
    exceeds the IDW-interpolated well-DEM surface by more than
    ``ridge_mask_threshold`` metres are masked (set to NaN). This correctly
    removes inter-dune ridge areas that lie between wells and are not
    ecologically representative of the interpolated value.

    Optionally applies make_site_mask() to clip the surface to the NNR site
    boundary (apply_site_mask=True). This is the KML-boundary mask, distinct
    from the ridge mask above — both can be active simultaneously.

    The caller is responsible for attaching a colorbar and drawing contours
    using the returned objects.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    df : DataFrame
        Must contain easting_col, northing_col, value_col. If ridge masking is
        requested, must also contain dem_col (the well ground elevation).
    value_col : str
        Column to interpolate.
    easting_col, northing_col : str
        Coordinate columns (default 'E', 'N').
    dem_col : str
        Well DEM elevation column used to build the IDW well-surface for ridge
        masking (default 'dem'). Ignored if dem_data is None.
    xi, yi : np.ndarray
        1-D arrays defining the interpolation grid. Defaults to the canonical
        site extent from config.SITE_MAP_* at 50 m resolution:
        np.arange(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX, 50) and
        np.arange(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX, 50).
    method : str
        scipy.interpolate.griddata method ('linear', 'nearest', 'cubic').
    ridge_mask_threshold : float
        Metres above IDW well surface at which a grid cell is considered a
        dune ridge and masked. Set to None to disable masking.
    dem_e_arr, dem_n_arr : np.ndarray or None
        DEM coordinate arrays from load_dem_hillshade(). Required for ridge
        masking; if None masking is skipped.
    dem_data : np.ndarray or None
        2-D DEM elevation array from load_dem_hillshade(). Required for ridge
        masking; if None masking is skipped.
    cmap : colormap or str
        Passed to pcolormesh.
    norm : matplotlib.colors.Normalize or None
        Passed to pcolormesh. If None, vmin/vmax are used.
    alpha : float
        Opacity of the surface (default 0.65).
    zorder : int
        Drawing order (default 2 — above hillshade, below wells/legend).
    vmin, vmax : float or None
        Colour scale limits used when norm is None.
    apply_site_mask : bool
        If True, calls make_site_mask(gx, gy) after ridge masking and sets
        cells outside the NNR boundary to NaN. Default False.
    hull_buffer_m : float or None
        Distance (m) to extend the interpolated surface beyond the convex hull
        of the well points. Linear griddata returns NaN outside the data hull,
        so an observed-data surface otherwise stops at the outer well ring —
        short of the coast where no dipwells sit seaward. When set, cells that
        are NaN from the linear pass but fall within the well hull dilated by
        hull_buffer_m are filled with a nearest-neighbour value, extending the
        surface a fixed distance past the outermost wells. The ridge mask and
        site mask are applied AFTER this fill, so the extension is still clipped
        to the true shoreline (apply_site_mask=True) and to dune ridges. This is
        pure extrapolation over unmeasured ground and is intentionally bounded;
        default 100.0 m. Set to None to keep the strict hull-bounded surface.

    Returns
    -------
    mesh : QuadMesh
        The pcolormesh object for colorbar attachment.
    gx : np.ndarray
        2-D grid easting coordinates.
    gy : np.ndarray
        2-D grid northing coordinates.
    surf_masked : np.ndarray
        The interpolated surface after ridge and/or site masking (NaN where
        masked).
    """
    if xi is None:
        xi = np.arange(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX, 50)
    if yi is None:
        yi = np.arange(SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX, 50)

    gx, gy = np.meshgrid(xi, yi)
    pts = df[[easting_col, northing_col]].values

    surf = griddata(pts, df[value_col].values, (gx, gy), method=method)

    # ── Hull-buffer extension ──────────────────────────────────────────────────
    # Linear griddata is NaN outside the convex hull of the wells, so the surface
    # stops at the outer well ring. Extend it up to hull_buffer_m beyond the hull
    # by filling those NaN cells (within the buffered hull) with nearest-neighbour
    # values. Runs before ridge/site masking so both still clip the extension.
    if hull_buffer_m is not None and hull_buffer_m > 0 and len(pts) >= 3:
        try:
            from shapely.geometry import MultiPoint, Point as _Pt
            from shapely import contains_xy as _cxy
            hull = MultiPoint([tuple(p) for p in pts]).convex_hull
            buffered = hull.buffer(hull_buffer_m)
            in_buffer = _cxy(buffered, gx.ravel(), gy.ravel()).reshape(gx.shape)
            need_fill = np.isnan(surf) & in_buffer
            if need_fill.any():
                surf_near = griddata(pts, df[value_col].values, (gx, gy),
                                     method="nearest")
                surf = np.where(need_fill, surf_near, surf)
        except Exception:
            pass   # on any geometry failure, keep the strict hull-bounded surface

    # ── Ridge masking ──────────────────────────────────────────────────────
    surf_masked = surf.copy()
    if (ridge_mask_threshold is not None
            and dem_e_arr is not None
            and dem_n_arr is not None
            and dem_data is not None
            and dem_col in df.columns):

        # IDW-interpolate well DEM elevations to the same grid
        surf_dem = griddata(pts, df[dem_col].values, (gx, gy), method=method)

        # Resample DEM raster to grid resolution
        dem_interp = RegularGridInterpolator(
            (dem_n_arr[::-1], dem_e_arr),
            dem_data[::-1, :],
            method="linear",
            bounds_error=False,
            fill_value=np.nan,
        )
        dem_at_grid = dem_interp(
            np.column_stack([gy.ravel(), gx.ravel()])
        ).reshape(gx.shape)

        ridge_mask = (dem_at_grid - surf_dem) > ridge_mask_threshold
        surf_masked = np.where(ridge_mask, np.nan, surf)

    # ── Site boundary masking ─────────────────────────────────────────────────
    if apply_site_mask:
        _site_mask = make_site_mask(gx, gy)
        surf_masked = np.where(_site_mask, surf_masked, np.nan)

    # ── Render ────────────────────────────────────────────────────────────
    kwargs = dict(shading="auto", alpha=alpha, zorder=zorder)
    if norm is not None:
        kwargs["norm"] = norm
        if cmap is not None:
            kwargs["cmap"] = cmap
    else:
        if cmap is not None:
            kwargs["cmap"] = cmap
        if vmin is not None:
            kwargs["vmin"] = vmin
        if vmax is not None:
            kwargs["vmax"] = vmax

    mesh = ax.pcolormesh(gx, gy, surf_masked, **kwargs)
    return mesh, gx, gy, surf_masked


def add_osm_basemap(ax, gdf):
    """Add an OpenStreetMap basemap as a fallback when the DEM is unavailable."""
    ctx.add_basemap(
        ax,
        crs=gdf.crs.to_string(),
        source=ctx.providers.OpenStreetMap.Mapnik,
        zorder=1,
        alpha=0.7,
    )


def load_scrape_kml(name):
    """Load and union the polygons of a single scrape-footprint KML (resolved
    under data/geo/ via paths.data_geo), reprojected to OSGB36. Returns a
    (Multi)Polygon, or None if the file is absent or unparseable.

    Single implementation shared by add_kml_features() (outline overlay) and
    Script 20's scrape-drawdown registry. Names come from
    config.SCRAPE_KML_FILES.
    """
    import re as _re
    from pyproj import Transformer
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    kml = data_geo(name)
    if not kml.exists():
        return None
    tf = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    polys = []
    try:
        xml = kml.read_text(errors="replace")
        for s in _re.findall(r"<coordinates>(.*?)</coordinates>", xml, _re.S):
            pts = [p.split(",") for p in s.split() if p.strip()]
            if len(pts) < 3:
                continue
            lon = [float(p[0]) for p in pts]
            lat = [float(p[1]) for p in pts]
            E, N = tf.transform(lon, lat)
            poly = Polygon(zip(E, N))
            if not poly.is_valid:
                poly = poly.buffer(0)
            polys.append(poly)
    except Exception:
        return None
    return unary_union(polys) if polys else None


def add_kml_features(ax, data_dir: Path, include_streams: bool = True,
                     include_scrapes: bool = True):
    """
    Overlay site feature KML layers onto ax.

    Draws Features.kml (lakes, forest boundary, broadleaf restock block, other features),
    streams.kml (if include_streams=True), clearfell.kml, and the GPS-traced scrape
    footprints (if include_scrapes=True; navy solid outline). Returns a deduplicated list
    of Line2D legend handles for the layers actually drawn.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    data_dir : Path
        Vestigial — retained for call-site compatibility. Geo inputs are read
        from the utils.paths constants, not reconstructed from data_dir.
    include_streams : bool, optional (default True)
        If False, streams.kml is not overlaid. Useful for maps where the
        drainage network would clutter the display.
    include_scrapes : bool, optional (default True)
        If False, the scrape footprint outlines are not overlaid. Useful for
        the dedicated scrape-drawdown figures that render scrapes themselves.

    Returns
    -------
    site_feature_handles : list of Line2D
    """
    site_feature_handles = []

    features_path = DATA_KML_FEATURES
    if features_path.exists():
        gdf_features = _safe_read_kml(features_path)
        if gdf_features is not None:
            gdf_features.set_crs(epsg=4326, inplace=True, allow_override=True)
            gdf_features = gdf_features.to_crs("EPSG:27700")
            feature_text = (
                gdf_features.get("Name", pd.Series("", index=gdf_features.index))
                .fillna("")
                .astype(str)
            )
            lake_mask = feature_text.str.contains("lake|llyn|rhos", case=False, na=False)
            forest_mask = feature_text.str.contains(
                "forest|plantation|wood|boundary", case=False, na=False
            )
            broadleaf_mask = (
                feature_text.str.contains("broadleaf|restock", case=False, na=False) |
                gdf_features.get("description", pd.Series("", index=gdf_features.index))
                    .fillna("").astype(str)
                    .str.contains("broadleaf|restock", case=False, na=False)
            )
            gdf_features[~(lake_mask | forest_mask | broadleaf_mask)].plot(
                ax=ax, facecolor="none", edgecolor="black",
                linewidth=1.3, linestyle="--", zorder=2,
            )
            _fb_colour = "black" if BW_MODE else "purple"
            _fb_lw = 3.0 if BW_MODE else 2.2
            gdf_features[forest_mask].plot(
                ax=ax, facecolor="none", edgecolor=_fb_colour, linewidth=_fb_lw, zorder=2
            )
            gdf_features[lake_mask].plot(
                ax=ax, facecolor="dodgerblue", edgecolor="dodgerblue",
                linewidth=1.8, alpha=0.25, zorder=2,
            )
            if broadleaf_mask.any():
                _bl_colour = "black" if BW_MODE else "#228B22"
                _bl_style = "-" if BW_MODE else "--"
                _bl_lw = 2.5 if BW_MODE else 2.0
                gdf_features[broadleaf_mask].plot(
                    ax=ax, facecolor="none", edgecolor=_bl_colour,
                    linewidth=_bl_lw, linestyle=_bl_style, zorder=2,
                )
                site_feature_handles.append(
                    Line2D([0], [0], color=_bl_colour, linestyle=_bl_style,
                           linewidth=_bl_lw, label="Broadleaf restocking block")
                )
            site_feature_handles.append(
                Line2D([0], [0], color="black", linestyle="--",
                       linewidth=1.6, label="Other Site Features")
            )
            _fb_colour = "black" if BW_MODE else "purple"
            _fb_lw = 3.0 if BW_MODE else 2.2
            site_feature_handles.append(
                Line2D([0], [0], color=_fb_colour, linestyle="-",
                       linewidth=_fb_lw, label="Forest Boundary")
            )

    streams_path = DATA_KML_STREAMS
    if include_streams and streams_path.exists():
        gdf_streams = _safe_read_kml(streams_path)
        if gdf_streams is not None and not gdf_streams.empty:
            if gdf_streams.crs is None:
                gdf_streams.set_crs(epsg=4326, inplace=True)
            gdf_streams.to_crs("EPSG:27700").plot(
                ax=ax, facecolor="none", edgecolor="dodgerblue", linewidth=0.45, zorder=2
            )
            site_feature_handles.append(
                Line2D([0], [0], color="dodgerblue", linestyle="-",
                       linewidth=0.45, label="DEM-derived topographic drainage paths")
            )

    clearfell_path = DATA_KML_CLEARFELL
    if clearfell_path.exists():
        gdf_clearfell = _safe_read_kml(clearfell_path)
        if gdf_clearfell is not None:
            if gdf_clearfell.crs is None:
                gdf_clearfell.set_crs(epsg=4326, inplace=True)
            _fe_colour = "black" if BW_MODE else "darkorange"
            _fe_style = "-" if BW_MODE else "-."
            _fe_lw = 2.5 if BW_MODE else 2.2
            gdf_clearfell.to_crs("EPSG:27700").plot(
                ax=ax, facecolor="none", edgecolor=_fe_colour,
                linewidth=_fe_lw, linestyle=_fe_style, zorder=2,
            )
            site_feature_handles.append(
                Line2D([0], [0], color=_fe_colour, linestyle=_fe_style,
                       linewidth=_fe_lw, label="Felling Area")
            )

    # Scrape footprints (navy solid outline) — shared site feature drawn on
    # every map that calls add_kml_features unless include_scrapes=False.
    if include_scrapes:
        scrape_geoms = [g for g in (load_scrape_kml(n) for n in SCRAPE_KML_FILES)
                        if g is not None]
        if scrape_geoms:
            _sc_colour = "black" if BW_MODE else FEATURE_COLOUR_SCRAPE
            _sc_style = ":" if BW_MODE else "-"
            _sc_lw = 2.0 if BW_MODE else 1.8
            gpd.GeoSeries(scrape_geoms, crs="EPSG:27700").plot(
                ax=ax, facecolor="none", edgecolor=_sc_colour,
                linewidth=_sc_lw, linestyle=_sc_style, zorder=2,
            )
            site_feature_handles.append(
                Line2D([0], [0], color=_sc_colour, linestyle=_sc_style,
                       linewidth=_sc_lw, label="Scrape footprints")
            )

    # Deduplicate by label
    dedup = {}
    for handle in site_feature_handles:
        dedup[handle.get_label()] = handle
    return list(dedup.values())


def plot_metric_map(
    map_df,
    value_col: str,
    title: str,
    output_path: Path,
    cmap: str,
    data_dir: Path,
    vmin=None,
    vmax=None,
):
    """
    Publication-quality spatial metric map.

    Renders well locations as cluster-shaped markers coloured by a numeric
    metric, over a DEM background with KML overlays. Produces dual colorbars
    (metric + elevation) and a cluster shape legend.

    Parameters
    ----------
    map_df : DataFrame
        Must contain columns: Easting, Northing, value_col.
        Optional: Cluster_ID (int 1-6).
    value_col : str
        Column in map_df to colour the markers by.
    title : str
    output_path : Path
    cmap : str
        Matplotlib colormap name. Diverging cmaps recommended for difference metrics.
    data_dir : Path
    vmin, vmax : float, optional
        Explicit colour scale limits. If None, inferred from data.
    """
    map_df = map_df.copy()
    required_cols = ["Easting", "Northing", value_col]
    missing_required = [c for c in required_cols if c not in map_df.columns]
    if missing_required:
        print(
            f"  [WARNING] Missing columns for map: {missing_required}. "
            f"Skipping {output_path.name}"
        )
        return

    if "Cluster_ID" not in map_df.columns:
        map_df["Cluster_ID"] = 1

    valid = map_df.dropna(subset=["Easting", "Northing", value_col]).copy()
    valid["Cluster_ID"] = (
        pd.to_numeric(valid["Cluster_ID"], errors="coerce").fillna(1).astype(int)
    )
    if valid.empty:
        print(
            f"  [WARNING] No mappable data for {value_col}. Skipping {output_path.name}"
        )
        return

    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)

    dem_result = load_dem_auto(ax, data_dir)
    dem_layer, dem_loaded = dem_result[0], dem_result[1]
    if not dem_loaded:
        gdf_tmp = gpd.GeoDataFrame(
            valid,
            geometry=gpd.points_from_xy(valid.Easting, valid.Northing),
            crs="EPSG:27700",
        )
        add_osm_basemap(ax, gdf_tmp)
    # Canonical map extent + E/N axes (single source: config.SITE_MAP_*)
    add_en_axes(ax)

    site_feature_handles = add_kml_features(ax, data_dir)

    # Colour scaling
    is_intercept = "intercept" in value_col.lower()
    is_nse = value_col.lower().startswith("nse") or "penalty" in value_col.lower()

    # BW mode: override colourmap to discrete grey bands for readability.
    if BW_MODE:
        import numpy as _np
        vals_arr = pd.to_numeric(valid[value_col], errors="coerce").dropna().to_numpy(dtype=float)
        _lo = float(vmin) if vmin is not None else float(_np.nanmin(vals_arr)) if vals_arr.size else 0.0
        _hi = float(vmax) if vmax is not None else float(_np.nanmax(vals_arr)) if vals_arr.size else 1.0
        if _hi <= _lo:
            _hi = _lo + 1e-6

        if is_intercept or (is_nse and _lo < 0 < _hi):
            # Diverging data: 3 clear bands in BW
            edges = _np.array([_lo, _lo/3, _hi/3, _hi])
            colors = ["#333333", "#b0b0b0", "#707070"]
        else:
            # Sequential data: 3 clear bands from light to dark
            edges = _np.linspace(_lo, _hi, 4)
            colors = ["#d0d0d0", "#808080", "#2a2a2a"]

        cmap_obj = mcolors.ListedColormap(colors)
        scatter_norm = mcolors.BoundaryNorm(edges, cmap_obj.N, clip=True)
        scatter_vmin = scatter_vmax = None
        cmap = cmap_obj

    elif is_intercept:
        if vmin is not None and vmax is not None:
            norm = mcolors.TwoSlopeNorm(vmin=float(vmin), vcenter=0.0, vmax=float(vmax))
        else:
            max_abs = np.nanpercentile(
                np.abs(valid[value_col].to_numpy(dtype=float)), 99
            )
            max_abs = max(float(max_abs) * 1.15, 0.08)
            norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)
        scatter_norm = norm
        scatter_vmin = scatter_vmax = None
    elif is_nse:
        _vmin = valid[value_col].min() if vmin is None else vmin
        _vmax = valid[value_col].max() if vmax is None else vmax
        center = 0 if _vmin < 0 < _vmax else (_vmin + _vmax) / 2
        norm = mcolors.TwoSlopeNorm(vmin=_vmin, vcenter=center, vmax=_vmax)
        scatter_norm = norm
        scatter_vmin = scatter_vmax = None
        if not BW_MODE:
            cmap = "RdYlBu"
    else:
        scatter_norm = None
        scatter_vmin = vmin
        scatter_vmax = vmax

    handles = []
    sc = None
    for cluster_id in sorted(valid["Cluster_ID"].dropna().unique()):
        marker = CLUSTER_MARKERS.get(int(cluster_id), "o")
        cluster_points = valid[valid["Cluster_ID"] == cluster_id]
        sc = ax.scatter(
            cluster_points["Easting"],
            cluster_points["Northing"],
            c=cluster_points[value_col],
            cmap=cmap,
            s=120,
            marker=marker,
            edgecolor="black",
            linewidth=0.6,
            alpha=0.9,
            norm=scatter_norm,
            vmin=scatter_vmin,
            vmax=scatter_vmax,
            zorder=5,
        )
        handles.append(
            plt.Line2D(
                [0], [0],
                marker=marker, color="w",
                label=CLUSTER_LABELS.get(int(cluster_id), f"C{int(cluster_id)}"),
                markerfacecolor="gray", markeredgecolor="black",
                markersize=12, linestyle="None",
            )
        )

    if sc is None:
        plt.close(fig)
        return

    # BW mode: label each marker with its value
    if BW_MODE:
        from adjustText import adjust_text
        texts = []
        for _, row in valid.iterrows():
            val = row[value_col]
            if pd.notna(val):
                fmt_val = f"{val:.2f}" if abs(val) < 10 else f"{val:.1f}"
                t = ax.text(
                    row["Easting"], row["Northing"], fmt_val,
                    fontsize=6.5, fontweight="bold", color="#222222",
                    ha="left", va="bottom", zorder=11,
                )
                texts.append(t)
        try:
            adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color="#999", lw=0.4))
        except Exception:
            pass  # adjust_text not critical

    divider = make_axes_locatable(ax)
    cax_metric = divider.append_axes("right", size="2.75%", pad=0.598)
    cbar = fig.colorbar(sc, cax=cax_metric)
    cbar.set_label(value_col.replace("_", " "), rotation=270, labelpad=32, fontsize=14)

    if dem_layer is not None:
        cax_dem = divider.append_axes("right", size="2.75%", pad=1.306)
        cbar_dem = fig.colorbar(dem_layer, cax=cax_dem, extend="both")
        cbar_dem.set_label("Elevation (m AOD)", rotation=270, labelpad=32, fontsize=14)

    ax.set_title(title, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.4)

    cluster_legend = ax.legend(
        handles=handles, title="Core Cluster Assignments",
        loc="lower left", frameon=True,
    )
    ax.add_artist(cluster_legend)

    if site_feature_handles:
        # Placed OUTSIDE the axes (below the map) as a horizontal legend.
        # With the canonical extent's trimmed northern edge (365500) an
        # in-data upper-right legend overlaps the topmost wells, so the site
        # feature key is moved out of the frame entirely. bbox_inches="tight"
        # captures it.
        ax.legend(
            handles=site_feature_handles, title="Site Features",
            loc="upper center", bbox_to_anchor=(0.5, -0.08),
            ncol=3, frameon=True,
        )

    plt.subplots_adjust(left=0.08, right=0.99, top=0.93, bottom=0.12)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
