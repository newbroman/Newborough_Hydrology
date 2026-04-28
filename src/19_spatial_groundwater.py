"""
19_spatial_groundwater.py
=========================
Spatial Groundwater Analysis — Newborough Warren 2005-2026
Hollingham (2026)

Reads pipeline intermediates and writes a single self-contained interactive
HTML file: scenario_viewer.html

Physical constants:
    K = 6 m/day (Betson et al. 2002)
    Forest interception = 24% (Freeman 2008, Corsican pine)
    Broadleaf interception = 15% (Komatsu et al. 2011, deciduous annual mean)
    Sy floor: C1 = 6%, C2-C5 = 12%
    Wells excluded from IDW: ceh12 (bedrock), ceh15 (forest slack edge)
    Ridge mask threshold: 1.0 m (matches map_utils.add_idw_surface)

Usage:
    python 19_spatial_groundwater.py
    python 19_spatial_groundwater.py --out /path/to/custom.html
"""

__version__ = "2.2.1"   # Hollingham (2026) -- 2026-04-19
                         # v2.2.1: Help dropdown z-index + overflow fix
                         #         (nav-links was clipping dropdown via
                         #         overflow-x:auto; dropdown z-index raised
                         #         to 600 and nav stacking context to 500).
                         # v2.2.0: Expanded viewer extent to full study area
                         #         (E 240200-243700, N 362400-364800); fixed
                         #         map size at 640x440 px; Help dropdown in
                         #         nav bar; hillshade/DEM grid re-aspected.
                         # v2.1.0: UKCP18 seasonal scenarios; DEM hillshade
                         #         basemap; DEM-based ridge masking; power-1
                         #         k=8 IDW interpolation.

import sys
import json
import warnings
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    DATA_DEM,
    DATA_KML_FEATURES,
    DATA_KML_CLEARFELL,
    KML_BROADLEAF,
    DIR_19,
    INT_LOCATIONS,
    INT_CLIMATE,
    INT_CLUSTER_STATS,
    INT_MASTER_DATA,
    INT_WELL_ELEVATIONS,
    INT_WELLS_CLEAN_MAOD,
    OUT_18_WELL_SY_TABLE,
)
from utils.data_utils import normalize_well_name
from utils.config import FOREST_INTERCEPTION

# Physical constants
BROADLEAF_INTERCEPTION = 0.15   # Deciduous annual mean -- Komatsu et al. (2011)
                                # Approximates summer (~25%, leafed) and winter
                                # (~0%, leafless) averaged over the year. The
                                # steady-state equilibrium framework applies this
                                # as an annual mean; the seasonal phenology
                                # mechanism that drives lower broadleaf summer
                                # minima is dynamical and not resolved here
                                # (see Section 5.4.4 for mechanism).
MONITOR_START = "2005-04-01"
MONITOR_END   = "2026-02-28"
WINTER_MONTHS = [11, 12, 1, 2, 3]
SUMMER_MONTHS = [5, 6, 7, 8, 9]
SY_DEFAULTS   = {1: 0.08, 2: 0.12, 3: 0.12, 4: 0.12, 5: 0.10, 6: 0.10}
SY_FLOOR      = {1: 0.06, 2: 0.12, 3: 0.12, 4: 0.12, 5: 0.12, 6: 0.12}
EXCLUDE_WELLS = {"ceh12", "ceh15"}

# Viewer map extent (OSGB36 / EPSG:27700). Single source of truth -- used by:
#   * build_hillshade (raster window into the LiDAR DEM)
#   * build_dem_grid (120x120 grid for the ridge mask in depth mode)
#   * forest polygon clip rectangle
#   * JS EMIN/EMAX/NMIN/NMAX constants in the HTML template
# If these ever drift apart the hillshade and DEM mis-register relative to the
# wells. E-span covers all wells (240339--243600) with ~100m margin; N-span
# covers wells (362615--364725) plus margin south to the Menai Strait shore.
VIEWER_EMIN, VIEWER_EMAX = 240200, 243700
VIEWER_NMIN, VIEWER_NMAX = 362400, 364800

# Scenario parameter sets -- mirror the JS SCEN dict in the viewer HTML.
# Keeping a single source of truth here ensures the interactive viewer and
# the Python-side scenario summary CSV never drift apart.
#
# Each scenario defines per-season multipliers on P and PET:
#   sP_w  = multiplier applied to winter (Nov-Mar) P baseline
#   sP_s  = multiplier applied to summer (May-Sep) P baseline
#   sPET_w, sPET_s = same for PET
# For the 'annual' season, Delta-h is the month-weighted average of the
# winter and summer Delta-h responses.
#
# UKCP18 presets are central-estimate (50th percentile) values under RCP8.5
# for Wales, informed by UKCP18 Regional 12 km ensemble (Met Office, 2018)
# and CHESS-SCAPE bias-corrected projections (Robinson et al., 2023). Spring
# and autumn contributions are aggregated into the winter and summer bins in
# proportion to their month memberships in the paper's seasonal definitions.
SCENARIO_PARAMS = {
    "baseline":       {"sP_w": 1.00, "sP_s": 1.00, "sPET_w": 1.00, "sPET_s": 1.00,
                       "sI": FOREST_INTERCEPTION, "sB2": 1.00},
    "ukcp18_2050s":   {"sP_w": 1.10, "sP_s": 0.85, "sPET_w": 1.05, "sPET_s": 1.20,
                       "sI": FOREST_INTERCEPTION, "sB2": 1.00},
    "ukcp18_2080s":   {"sP_w": 1.20, "sP_s": 0.70, "sPET_w": 1.10, "sPET_s": 1.35,
                       "sI": FOREST_INTERCEPTION, "sB2": 1.00},
    "clearfell":   {"sP_w": 1.00, "sP_s": 1.00, "sPET_w": 1.00, "sPET_s": 1.00,
                    "sI": 0.00,
                    "sB2": 1.20},
    "broadleaf":   {"sP_w": 1.00, "sP_s": 1.00, "sPET_w": 1.00, "sPET_s": 1.00,
                    "sI": BROADLEAF_INTERCEPTION, "sB2": 1.00},
    "thinning":    {"sP_w": 1.00, "sP_s": 1.00, "sPET_w": 1.00, "sPET_s": 1.00,
                    "sI": FOREST_INTERCEPTION * 0.5, "sB2": 1.10},
}
SEASONS = ["annual", "winter", "summer"]


# Hillshade base layer -- rendering resolution for the embedded PNG.
# At the viewer's 3500x2400 m extent this gives ~3.2 m/px, adequate for the
# visual basemap without bloating the HTML (typical output 200-300 KB base64).
# Aspect ratio (1100/750 = 1.467) matches E-span/N-span (3500/2400 = 1.458);
# the PNG is drawn stretched onto the 640x440 canvas, so PNG aspect must track
# geographic extent or features will appear distorted.
HILLSHADE_COLS = 1100
HILLSHADE_ROWS = 750

# DEM elevation grid for dune-ridge masking -- serialised as a JSON array of
# numbers, read by the viewer's JS to replicate the ridge mask applied in the
# static figures (map_utils.add_idw_surface, ridge_mask_threshold = 1.0 m).
# At the 3500x2400 m extent this gives ~22 m/cell, which safely exceeds the
# viewer's pixel-block rendering step (~15 px) while keeping the embedded
# grid under ~80 KB of JSON. Aspect tracks E-span/N-span.
DEM_GRID_COLS = 160
DEM_GRID_ROWS = 110
RIDGE_MASK_THRESHOLD = 1.0   # metres -- matches map_utils.add_idw_surface default


# ============================================================================
# HILLSHADE BASE LAYER
# ============================================================================

def build_hillshade_base64(site_polygon_xy=None):
    """
    Build a site-masked greyscale hillshade PNG of the viewer extent, returned
    as a base64-encoded data URI string ready to embed in HTML.

    The hillshade is computed from newborough_dem.tif using the same LightSource
    parameters as utils.map_utils.load_dem_hillshade (azimuth 315 deg NW,
    altitude 35 deg, vertical exaggeration 3) so the viewer basemap matches
    the static figures in the rest of the pipeline.

    Returns an empty string if the DEM, rasterio, matplotlib, or PIL are not
    available -- the JS drawBg() function falls back to the flat green fill
    in that case, so the viewer remains functional.
    """
    # Viewer extent (single source of truth -- module-level VIEWER_* constants).
    EMIN, EMAX = VIEWER_EMIN, VIEWER_EMAX
    NMIN, NMAX = VIEWER_NMIN, VIEWER_NMAX

    try:
        import rasterio
        from rasterio.windows import from_bounds
        from matplotlib.colors import LightSource
        from PIL import Image
        import base64
        import io
    except ImportError as exc:
        print(f"  [INFO] Hillshade skipped (missing dependency: {exc}).")
        return ""

    if not DATA_DEM.exists():
        print(f"  [INFO] Hillshade skipped (DEM not found at {DATA_DEM}).")
        return ""

    try:
        with rasterio.open(str(DATA_DEM)) as src:
            # Crop to viewer extent to avoid reading the whole DEM.
            window = from_bounds(EMIN, NMIN, EMAX, NMAX, transform=src.transform)
            dem = src.read(1, window=window, boundless=True,
                           fill_value=np.nan).astype(float)
            win_transform = src.window_transform(window)
            res_x = abs(win_transform.a)
            res_y = abs(win_transform.e)
            if src.nodata is not None:
                dem[dem == src.nodata] = np.nan

        # Resample to target render resolution. scipy.ndimage.zoom with
        # order=1 (bilinear) hits the target shape exactly regardless of
        # whether the source DEM is coarser or finer than HILLSHADE_COLS/
        # ROWS -- the previous integer-factor block-mean implementation
        # silently skipped downsampling whenever src_dim < 2 x target_dim.
        # Pre-resample NaNs are set to 0 so they don't propagate through
        # the bilinear interpolation; the alpha mask below hides those
        # cells from the final PNG.
        from scipy.ndimage import zoom as _zoom
        rows, cols = dem.shape
        nan_mask = np.isnan(dem)
        dem_filled = np.where(nan_mask, 0.0, dem)
        zoom_y = HILLSHADE_ROWS / rows
        zoom_x = HILLSHADE_COLS / cols
        dem_ds = _zoom(dem_filled, (zoom_y, zoom_x), order=1)
        # Propagate a nodata mask to the target grid (nearest-neighbour is
        # right here because we want sharp edges on the nodata boundary).
        nan_ds = _zoom(nan_mask.astype(np.float32),
                       (zoom_y, zoom_x), order=0) > 0.5
        dem_ds = np.where(nan_ds, np.nan, dem_ds)
        # Effective resolution after resampling -- used only for hillshade
        # illumination intensity.
        ds_res_x = res_x * (cols / dem_ds.shape[1])
        ds_res_y = res_y * (rows / dem_ds.shape[0])

        # Hillshade needs finite values; the sea/nodata regions get a flat
        # fill for the illumination calculation but will be masked out below.
        filled = np.nan_to_num(dem_ds, nan=0.0)
        ls = LightSource(azdeg=315.0, altdeg=35.0)
        hs = ls.hillshade(filled, vert_exag=3.0, dx=ds_res_x, dy=ds_res_y)

        # Map hillshade [0..1] onto the same greyscale range that
        # matplotlib's pcolormesh uses (vmin=0.2, vmax=1.0 -- see
        # load_dem_hillshade). alpha at 0.35 matches the static figures.
        # Quantising to 32 grey levels gives PNG's run-length compression
        # much more to work with (neighbouring pixels collapse into runs
        # of identical values); at 35% alpha blending under the colour
        # overlay the quantisation is visually imperceptible.
        GREY_LEVELS = 32
        grey_f = np.clip((hs - 0.2) / 0.8, 0.0, 1.0)
        grey_q = np.round(grey_f * (GREY_LEVELS - 1)) / (GREY_LEVELS - 1)
        grey = (grey_q * 255.0).astype(np.uint8)

        # Alpha channel: transparent outside DEM coverage, outside the viewer
        # extent, and outside the site boundary polygon.
        alpha = np.full(grey.shape, 90, dtype=np.uint8)   # ~35% opacity
        alpha[np.isnan(dem_ds)] = 0

        # Site-polygon mask. The viewer canvas has N increasing upward
        # (Y inverted), so build the pixel grid in matching orientation.
        if site_polygon_xy is not None and len(site_polygon_xy) >= 3:
            try:
                from shapely.geometry import Polygon as _SP
                from shapely import contains_xy as _contains_xy
                site_poly = _SP([(float(p[0]), float(p[1]))
                                 for p in site_polygon_xy])
                out_rows, out_cols = grey.shape
                col_edges = np.linspace(EMIN, EMAX, out_cols + 1)
                row_edges = np.linspace(NMAX, NMIN, out_rows + 1)
                col_centres = 0.5 * (col_edges[:-1] + col_edges[1:])
                row_centres = 0.5 * (row_edges[:-1] + row_edges[1:])
                EE, NN = np.meshgrid(col_centres, row_centres)
                inside = _contains_xy(site_poly, EE, NN)
                alpha[~inside] = 0
            except Exception as exc:
                print(f"  [WARNING] Site-mask step skipped: {exc}")

        # RGBA image: R=G=B=grey, A=alpha.
        rgba = np.dstack([grey, grey, grey, alpha])
        img = Image.fromarray(rgba, mode="RGBA")
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        size_kb = len(b64) / 1024
        print(f"  Hillshade: {img.size[0]}x{img.size[1]} px, "
              f"{size_kb:.1f} KB base64")
        return f"data:image/png;base64,{b64}"

    except Exception as exc:
        print(f"  [WARNING] Hillshade build failed: {exc}")
        return ""


def build_dem_grid(site_polygon_xy=None):
    """
    Build a downsampled DEM elevation grid covering the viewer extent, for
    use in the viewer's JS ridge-masking step.

    Returns a dict with 'rows' (int), 'cols' (int), 'data' (flat list of
    elevation values in m AOD, row-major, top-to-bottom), and 'nodata'
    (a sentinel number used where DEM is absent or outside the site polygon).
    If DEM/rasterio is unavailable, returns an empty dict -- the viewer then
    falls back to un-masked interpolation, matching the pre-masking behaviour.

    Grid geometry matches the viewer canvas: row 0 is the top (northernmost),
    columns increase eastward. Cell centres are used; edges implied by
    DEM_GRID_COLS x DEM_GRID_ROWS spanning EMIN..EMAX x NMIN..NMAX.
    """
    EMIN, EMAX = VIEWER_EMIN, VIEWER_EMAX
    NMIN, NMAX = VIEWER_NMIN, VIEWER_NMAX
    NODATA = -9999.0

    try:
        import rasterio
        from rasterio.windows import from_bounds
    except ImportError as exc:
        print(f"  [INFO] DEM grid skipped (missing dependency: {exc}).")
        return {}

    if not DATA_DEM.exists():
        print(f"  [INFO] DEM grid skipped (DEM not found at {DATA_DEM}).")
        return {}

    try:
        with rasterio.open(str(DATA_DEM)) as src:
            window = from_bounds(EMIN, NMIN, EMAX, NMAX, transform=src.transform)
            dem = src.read(1, window=window, boundless=True,
                           fill_value=np.nan).astype(float)
            if src.nodata is not None:
                dem[dem == src.nodata] = np.nan

        # Resample to target grid. scipy.ndimage.zoom with order=1 (bilinear)
        # guarantees the output shape is exactly DEM_GRID_ROWS x DEM_GRID_COLS,
        # irrespective of source resolution. NaN handling matches the hillshade
        # builder: zeros are substituted pre-resample, then a nearest-neighbour
        # nodata mask is reapplied.
        from scipy.ndimage import zoom as _zoom
        rows, cols = dem.shape
        nan_mask = np.isnan(dem)
        dem_filled = np.where(nan_mask, 0.0, dem)
        zoom_y = DEM_GRID_ROWS / rows
        zoom_x = DEM_GRID_COLS / cols
        dem_ds = _zoom(dem_filled, (zoom_y, zoom_x), order=1)
        nan_ds = _zoom(nan_mask.astype(np.float32),
                       (zoom_y, zoom_x), order=0) > 0.5
        dem_ds = np.where(nan_ds, np.nan, dem_ds)

        out_rows, out_cols = dem_ds.shape

        # Site-polygon mask -- we only care about masking *inside* the site,
        # but values outside are harmless (they'd be masked by the viewer's
        # site check anyway).
        if site_polygon_xy is not None and len(site_polygon_xy) >= 3:
            try:
                from shapely.geometry import Polygon as _SP
                from shapely import contains_xy as _contains_xy
                site_poly = _SP([(float(p[0]), float(p[1]))
                                 for p in site_polygon_xy])
                col_edges = np.linspace(EMIN, EMAX, out_cols + 1)
                row_edges = np.linspace(NMAX, NMIN, out_rows + 1)
                col_centres = 0.5 * (col_edges[:-1] + col_edges[1:])
                row_centres = 0.5 * (row_edges[:-1] + row_edges[1:])
                EE, NN = np.meshgrid(col_centres, row_centres)
                inside = _contains_xy(site_poly, EE, NN)
                dem_ds = np.where(inside, dem_ds, np.nan)
            except Exception as exc:
                print(f"  [WARNING] DEM grid site-mask skipped: {exc}")

        # Serialise: replace NaN with sentinel, round to 2 dp, flatten.
        flat = np.where(np.isnan(dem_ds), NODATA, dem_ds).round(2).flatten()
        # Ensure native Python floats for JSON (not numpy.float64).
        data = [float(v) for v in flat]
        size_kb = len(str(data)) / 1024
        print(f"  DEM grid: {out_cols}x{out_rows} cells, "
              f"~{size_kb:.1f} KB JSON")
        return {
            "cols": int(out_cols),
            "rows": int(out_rows),
            "emin": float(EMIN), "emax": float(EMAX),
            "nmin": float(NMIN), "nmax": float(NMAX),
            "nodata": float(NODATA),
            "data": data,
        }

    except Exception as exc:
        print(f"  [WARNING] DEM grid build failed: {exc}")
        return {}


# ============================================================================
# DATA LOADING
# ============================================================================

def _norm(s):
    return str(s).lower().replace(" ", "").replace("-", "").strip()


def load_data():
    """Load and merge all required pipeline intermediates."""
    loc  = pd.read_csv(INT_LOCATIONS)
    loc["id"] = loc["Match_ID"].apply(_norm)
    cl   = pd.read_csv(INT_CLUSTER_STATS)
    cl["id"] = cl["Match_ID"].apply(_norm)
    md   = pd.read_csv(INT_MASTER_DATA)
    md["id"] = md["Name_Original"].apply(_norm)
    elev = pd.read_csv(INT_WELL_ELEVATIONS)
    elev["id"] = elev["Name_norm"].apply(_norm)
    maod = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    maod.columns = [_norm(c) for c in maod.columns]
    maod = maod.loc[MONITOR_START:MONITOR_END]
    clim = pd.read_csv(INT_CLIMATE, parse_dates=["Date"], index_col="Date")
    clim = clim.loc[MONITOR_START:MONITOR_END]
    sy_df = None
    if OUT_18_WELL_SY_TABLE.exists():
        sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
        wcol = ("Well_Normalised" if "Well_Normalised" in sy_df.columns else "Well")
        sy_df["id"] = sy_df[wcol].apply(_norm)
    else:
        warnings.warn(f"{OUT_18_WELL_SY_TABLE.name} not found -- cluster defaults used.")
    return loc, cl, md, elev, maod, clim, sy_df


def build_well_table(loc, cl, md, elev, maod, clim, sy_df):
    """Build per-well table with heads, betas, Sy, and coordinates."""
    P_bar   = clim["P_m"].mean()
    PET_bar = clim["PET"].mean()
    wm = clim[clim.index.month.isin(WINTER_MONTHS)]
    sm = clim[clim.index.month.isin(SUMMER_MONTHS)]
    # Monthly climatology for display in the viewer (in mm/month)
    monthly = clim.groupby(clim.index.month).agg(
        P_m=("P_m", "mean"), PET=("PET", "mean"))
    monthly_P_mm   = (monthly["P_m"] * 1000.0).round(1).to_dict()   # m -> mm
    monthly_PET_mm = (monthly["PET"] * 1000.0).round(1).to_dict()   # m -> mm
    climate_stats = {
        "annual": (P_bar, PET_bar),
        "winter": (wm["P_m"].mean(), wm["PET"].mean()),
        "summer": (sm["P_m"].mean(), sm["PET"].mean()),
        "monthly_P_mm": monthly_P_mm,
        "monthly_PET_mm": monthly_PET_mm,
    }
    wt = loc[["id", "E", "N"]].copy()
    wt = wt.merge(cl[["id", "Cluster"]], on="id", how="left")
    wt = wt.merge(
        md[["id", "beta_1_recharge", "beta_2_atmospheric_draw",
            "beta_3_drainage"]].rename(columns={
            "beta_1_recharge": "b1",
            "beta_2_atmospheric_draw": "b2",
            "beta_3_drainage": "b3",
        }), on="id", how="left")
    # Join DEM ground elevation for viewer ridge masking (mirrors the
    # static-figure approach in map_utils.add_idw_surface).
    if "DEM_Ground_Elev" in elev.columns:
        wt = wt.merge(elev[["id", "DEM_Ground_Elev"]].rename(
            columns={"DEM_Ground_Elev": "dem_g"}), on="id", how="left")
    else:
        wt["dem_g"] = np.nan
    heads_all = maod.mean()
    heads_win = maod[maod.index.month.isin(WINTER_MONTHS)].mean()
    heads_sum = maod[maod.index.month.isin(SUMMER_MONTHS)].mean()
    wt["mh"] = wt["id"].map(heads_all)
    wt["wh"] = wt["id"].map(heads_win)
    wt["sh"] = wt["id"].map(heads_sum)
    if sy_df is not None:
        sy_map = dict(zip(sy_df["id"], sy_df["Sy_median"]))
        wt["sy"] = wt["id"].map(sy_map)
    else:
        wt["sy"] = np.nan
    def fill_sy(row):
        if pd.notna(row["sy"]):
            return row["sy"]
        return SY_DEFAULTS.get(int(row["Cluster"]) if pd.notna(row["Cluster"]) else 3, 0.12)
    wt["sy"] = wt.apply(fill_sy, axis=1)
    wt = wt[~wt["id"].isin(EXCLUDE_WELLS)]
    wt = wt.dropna(subset=["E", "N", "mh"])
    wt = wt.reset_index(drop=True)
    print(f"  Well table: {len(wt)} wells")
    print(f"  beta available: {wt['b1'].notna().sum()} wells")
    print(f"  Forest wells (C4+C5): {((wt['Cluster'] == 4) | (wt['Cluster'] == 5)).sum()}")
    print(f"  P_bar  = {P_bar*1000:.2f} mm/mo   PET_bar = {PET_bar*1000:.2f} mm/mo")
    return wt, climate_stats


# ============================================================================
# KML GEOREFERENCING
# ============================================================================

def load_kml_polygons():
    """
    Load KML polygons and reproject EPSG:4326 to EPSG:27700 via pyproj.
    Uses path constants from utils/paths.py (all pointing to DATA_DIR).
    Falls back to hardcoded coordinates for any polygon whose KML is absent.
    """
    HARDCODED = {
        "clearfell": [[241062,363621],[241170,363796],[241354,363679],
                       [241235,363505],[241062,363621]],
        "broadleaf": [[241298,364491],[241316,364469],[241348,364365],
                       [241428,364295],[241424,364259],[241411,364210],
                       [241406,364158],[241607,364051],[241717,364207],
                       [241692,364218],[241654,364245],[241629,364259],
                       [241539,364315],[241465,364360],[241327,364543],
                       [241298,364491]],
        "lake":      [[242613,364937],[242576,364938],[242543,364924],
                       [242512,364902],[242479,364860],[242457,364849],
                       [242429,364818],[242397,364788],[242360,364764],
                       [242352,364750],[242356,364729],[242384,364730],
                       [242405,364749],[242435,364773],[242476,364786],
                       [242507,364807],[242531,364822],[242554,364832],
                       [242574,364853],[242597,364869],[242619,364882],
                       [242631,364899],[242628,364919],[242613,364937]],
        # Fallback forest polygon (used only when kml load fails). The vertices
        # touching N=365100 were clipped against the old viewer NMAX=365100 and
        # now extend beyond the new NMAX=364800; minor visual issue only since
        # the live KML path is the primary source.
        "forest":    [[241554,364966],[241380,364725],[241715,364622],
                       [241805,364349],[241024,363184],[240920,363331],
                       [240650,363417],[240650,365100],[241409,365100],
                       [241554,364966]],
        "site":      [[241088,362784],[240016,363370],[240000,364300],
                       [240954,365000],[241436,365096],[242932,365034],
                       [243680,364434],[243762,364180],[243604,363794],
                       [243962,363656],[243816,363012],[243036,362266],
                       [242066,362294],[241780,362156],[241088,362784]],
    }
    polys = {}
    try:
        import fiona
        fiona.drvsupport.supported_drivers["KML"] = "rw"
        import geopandas as gpd

        def kml_to_bng(path):
            if path is None or not Path(path).exists():
                return []
            gdf = gpd.read_file(str(path), driver="KML")
            gdf = gdf.set_crs(epsg=4326, allow_override=True).to_crs("EPSG:27700")
            results = []
            for _, row in gdf.iterrows():
                geom = row.geometry
                nm = str(row.get("Name", "")) if "Name" in row.index else ""
                if geom is None:
                    continue
                def pts_from(g):
                    if g.geom_type == "Polygon":
                        return [[round(x), round(y)]
                                for x, y in zip(g.exterior.xy[0], g.exterior.xy[1])]
                    if g.geom_type == "LineString":
                        return [[round(x), round(y)] for x, y in zip(g.xy[0], g.xy[1])]
                    if g.geom_type == "Point":
                        return [[round(geom.x), round(geom.y)]]
                    if "Multi" in g.geom_type:
                        return pts_from(list(g.geoms)[0])
                    return []
                pts = pts_from(geom)
                if pts:
                    results.append({"name": nm, "pts": pts})
            return results

        cf = kml_to_bng(DATA_KML_CLEARFELL)
        if cf:
            polys["clearfell"] = cf[0]["pts"]
            print(f"  clearfell.kml: {len(polys['clearfell'])} pts")

        ft = kml_to_bng(DATA_KML_FEATURES)
        for f in ft:
            nm_lower = f["name"].lower()
            if "llyn" in nm_lower or "rhos" in nm_lower or "lake" in nm_lower:
                polys["lake"] = f["pts"]
            elif "forest" in nm_lower or "plantation" in nm_lower:
                polys["forest_raw"] = f["pts"]
        if ft:
            print(f"  Features.kml: found {[k for k in ('lake','forest_raw') if k in polys]}")

        bl = kml_to_bng(KML_BROADLEAF)
        if bl:
            polys["broadleaf"] = bl[0]["pts"]
            print(f"  broadleaf_restock.kml: {len(polys['broadleaf'])} pts")

        site_path = DATA_DIR / "site_boundary.kml"
        sb = kml_to_bng(site_path)
        if sb:
            try:
                from shapely.geometry import Polygon as _SP
                from shapely.ops import unary_union
                all_p = [_SP([(p[0], p[1]) for p in f["pts"]]) for f in sb if len(f["pts"]) >= 3]
                merged = unary_union(all_p)
                simp = merged.simplify(100, preserve_topology=True)
                if simp.geom_type == "Polygon":
                    polys["site"] = [[round(x), round(y)]
                                     for x, y in zip(simp.exterior.xy[0], simp.exterior.xy[1])]
                else:
                    biggest = max(list(simp.geoms), key=lambda p: p.area)
                    polys["site"] = [[round(x), round(y)]
                                     for x, y in zip(biggest.exterior.xy[0], biggest.exterior.xy[1])]
                print(f"  site_boundary.kml: {len(polys['site'])} pts (simplified)")
            except Exception:
                polys["site"] = max(sb, key=lambda x: len(x["pts"]))["pts"]
                print(f"  site_boundary.kml: {len(polys['site'])} pts")

        if "forest_raw" in polys:
            try:
                from shapely.geometry import Polygon as _FP
                fp = _FP([(p[0], p[1]) for p in polys["forest_raw"]])
                clip = _FP([(VIEWER_EMIN, VIEWER_NMIN), (VIEWER_EMAX, VIEWER_NMIN),
                            (VIEWER_EMAX, VIEWER_NMAX), (VIEWER_EMIN, VIEWER_NMAX)])
                clipped = fp.intersection(clip).simplify(50)
                if not clipped.is_empty:
                    if clipped.geom_type == "Polygon":
                        polys["forest"] = [[round(x), round(y)]
                                            for x, y in zip(clipped.exterior.xy[0], clipped.exterior.xy[1])]
                    else:
                        lg = max(list(clipped.geoms), key=lambda g: g.area)
                        polys["forest"] = [[round(x), round(y)]
                                            for x, y in zip(lg.exterior.xy[0], lg.exterior.xy[1])]
                    print(f"  Forest (clipped): {len(polys['forest'])} pts")
            except Exception as e:
                warnings.warn(f"Forest polygon clip failed: {e}")
            del polys["forest_raw"]

    except ImportError:
        warnings.warn("geopandas/fiona not available -- using hardcoded KML coordinates.")

    for key, coords in HARDCODED.items():
        if key not in polys:
            polys[key] = coords
            print(f"  {key}: using hardcoded coordinates (KML not loaded)")

    return polys


# ============================================================================
# SERIALISATION HELPERS
# ============================================================================

def _r(v, d=4):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return round(float(v), d)


def serialise_wells(wt):
    rows = []
    for _, r in wt.iterrows():
        cl_int = int(r["Cluster"]) if pd.notna(r["Cluster"]) else 3
        rows.append({"n": r["id"], "cl": cl_int,
                     "E": round(float(r["E"])), "N": round(float(r["N"])),
                     "mh": _r(r["mh"],3), "wh": _r(r["wh"],3), "sh": _r(r["sh"],3),
                     "sy": _r(r["sy"],4), "b1": _r(r["b1"],6),
                     "b2": _r(r["b2"],6), "b3": _r(r["b3"],6),
                     "dg": _r(r.get("dem_g"), 2) if pd.notna(r.get("dem_g")) else None})
    return rows


def serialise_climate(wt, climate_stats):
    out = {}
    h_col_map = {"annual": "mh", "winter": "wh", "summer": "sh"}
    for sea_key in ("annual", "winter", "summer"):
        P, PET = climate_stats[sea_key]
        h_col = h_col_map[sea_key]
        cluster_heads = {}
        for cl_int in [1, 2, 3, 4, 5]:
            sub = wt[wt["Cluster"] == cl_int][h_col].dropna()
            cluster_heads[cl_int] = _r(sub.mean(), 4) if len(sub) else 0.0
        out[sea_key] = {"P": _r(P,7), "PET": _r(PET,7), "cluster_heads": cluster_heads}
    # Monthly climatology (mm/month) for baseline display table
    out["monthly"] = {
        "P_mm":   {str(m): float(v) for m, v in climate_stats["monthly_P_mm"].items()},
        "PET_mm": {str(m): float(v) for m, v in climate_stats["monthly_PET_mm"].items()},
    }
    cluster_betas = {}
    for cl_int in [1, 2, 3, 4, 5]:
        sub = wt[(wt["Cluster"] == cl_int) & wt["b1"].notna()]
        if len(sub) == 0:
            sub = wt[wt["Cluster"] == cl_int]
        cluster_betas[cl_int] = {"b1": _r(sub["b1"].mean(),6) if len(sub) else None,
                                  "b2": _r(sub["b2"].mean(),6) if len(sub) else None,
                                  "b3": _r(sub["b3"].mean(),6) if len(sub) else None}
    out["cluster_betas"] = cluster_betas
    return out


# ============================================================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<!-- Newborough Warren Hydrological Scenario Viewer v{viewer_version} -->
<!-- Generated by 19_spatial_groundwater.py -->
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="generator" content="19_spatial_groundwater.py v{viewer_version}">
<meta name="viewer-version" content="{viewer_version}">
<title>Newborough Warren — Hydrological Scenario Viewer v{viewer_version}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{{
  --sand:#f4f0e6; --sand-dark:#e8e0cc; --dune:#c8b878;
  --slate:#3a4a52; --slate-light:#5a6e78;
  --water:#4a7a8a; --water-light:#6a9aaa; --water-pale:#e8f2f5;
  --pine:#3d5c3a; --pine-light:#5a7d56;
  --text:#2a3338; --text-light:#5a6a72; --border:#d4c8a8;
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Source Sans 3',sans-serif;font-weight:400;
     font-size:14px;background:var(--sand);color:var(--text);line-height:1.6;}}

/* Header */
header{{background:var(--slate);color:#fff;padding:1.3rem 1.5rem 1.1rem;
       position:relative;overflow:hidden;}}
header::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;
              background:linear-gradient(90deg,var(--dune),var(--water),var(--pine));}}
.site-label{{font-size:0.68rem;font-weight:600;letter-spacing:0.18em;
            text-transform:uppercase;color:var(--dune);margin-bottom:0.45rem;}}
header h1{{font-family:'Libre Baskerville',Georgia,serif;font-weight:700;
          font-size:clamp(1.05rem,2.8vw,1.4rem);line-height:1.25;
          color:#fff;margin-bottom:0.35rem;}}
header p{{font-size:0.78rem;color:rgba(255,255,255,0.58);font-weight:300;}}

/* Layout grid */
.main{{display:grid;grid-template-columns:215px minmax(0,1fr);gap:12px;
       padding:12px;align-items:start;}}
@media(max-width:640px){{.main{{grid-template-columns:1fr;}}}}

/* Controls sidebar */
.ctrl{{background:#fff;border:1px solid var(--border);border-radius:4px;padding:12px;}}
@media(min-width:641px){{.ctrl{{position:sticky;top:0;max-height:98vh;overflow-y:auto;}}}}
.ch{{font-size:0.65rem;font-weight:600;letter-spacing:0.15em;text-transform:uppercase;
     color:var(--water);border-bottom:1px solid var(--border);
     padding-bottom:4px;margin-bottom:7px;}}
.sc{{display:block;width:100%;text-align:left;padding:5px 8px;margin-bottom:3px;
     background:transparent;border:1px solid var(--border);border-radius:3px;
     cursor:pointer;font-size:11px;color:var(--text);line-height:1.3;
     font-family:'Source Sans 3',sans-serif;}}
.sc:hover{{background:var(--water-pale);border-color:var(--water-light);}}
.sc.on{{border:1.5px solid var(--water);background:var(--water-pale);
        color:var(--water);font-weight:600;}}
.sc-note{{font-size:10px;color:var(--text-light);line-height:1.45;margin-top:6px;
          padding:5px 8px;background:var(--sand);
          border-left:2px solid var(--dune);border-radius:0 3px 3px 0;}}
.srow{{display:flex;align-items:center;gap:5px;margin-bottom:5px;}}
.srow label{{font-size:11px;color:var(--text-light);flex:1;}}
.sv{{font-size:10px;font-weight:600;min-width:34px;text-align:right;color:var(--slate);}}
.srow input[type=range]{{flex:1;min-width:0;accent-color:var(--water);}}
.ckrow{{display:flex;align-items:center;gap:6px;margin-bottom:4px;
        font-size:11px;color:var(--text-light);cursor:pointer;}}
.hr{{height:1px;background:var(--border);margin:8px 0;}}

/* Right column */
.rp{{min-width:0;display:flex;flex-direction:column;gap:10px;}}

/* Season tabs */
.tabs{{display:flex;gap:5px;flex-wrap:wrap;}}
.tab{{padding:4px 11px;border-radius:20px;font-size:11px;border:1px solid var(--border);
      background:transparent;cursor:pointer;color:var(--text-light);
      font-family:'Source Sans 3',sans-serif;}}
.tab.on{{background:var(--slate);color:#fff;border-color:var(--slate);}}

/* Warning banner */
.warn{{background:#fdf5e3;border:1px solid var(--dune);border-left:3px solid var(--dune);
       border-radius:0 3px 3px 0;padding:6px 10px;
       font-size:11px;color:var(--text);line-height:1.45;}}

/* Metric cards */
.metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;}}
@media(max-width:420px){{.metrics{{grid-template-columns:repeat(2,1fr);}}}}
.mc{{background:#fff;border:1px solid var(--border);border-radius:3px;padding:8px 10px;}}
.mc .ml{{font-size:10px;color:var(--text-light);margin-bottom:2px;}}
.mc .mv{{font-size:15px;font-weight:700;}}
.mc .mu{{font-size:10px;color:var(--text-light);}}

/* Panels */
.panel{{background:#fff;border:1px solid var(--border);border-radius:4px;padding:12px;}}
.panel h4{{font-size:11px;font-weight:600;color:var(--slate-light);margin-bottom:6px;
          letter-spacing:0.04em;text-transform:uppercase;}}
.phead{{display:flex;align-items:center;justify-content:space-between;
        margin-bottom:7px;flex-wrap:wrap;gap:5px;}}
.phead h4{{margin:0;}}
.rtabs{{display:flex;gap:4px;flex-wrap:wrap;}}
.rt{{padding:3px 8px;border-radius:3px;font-size:10px;border:1px solid var(--border);
     background:transparent;cursor:pointer;color:var(--text-light);
     font-family:'Source Sans 3',sans-serif;}}
.rt.on{{background:var(--water-pale);border-color:var(--water);
        color:var(--water);font-weight:600;}}

/* Map canvas. Fixed pixel size so the map does not dominate the page on
   wide monitors and does not rescale on desktop when the window is resized.
   On narrow viewports (below 640 px) the wrap shrinks via max-width:100%
   and the canvas follows via width:100%. The aspect ratio (640x440)
   matches the viewer extent E-span / N-span = 3500/2400. */
.mapwrap{{position:relative;width:640px;max-width:100%;height:440px;overflow:hidden;border-radius:3px;}}
.mapwrap canvas{{display:block;width:100%;height:100%;}}
#mapBg{{position:relative;}}
#mapC{{position:absolute;top:0;left:0;cursor:crosshair;}}
.leg{{display:flex;flex-wrap:wrap;align-items:center;gap:7px;
      margin-top:5px;font-size:10px;color:var(--text-light);}}
.ls{{width:10px;height:10px;border-radius:2px;display:inline-block;
     vertical-align:middle;margin-right:2px;}}
.tip{{font-size:11px;color:var(--text-light);margin-top:3px;min-height:14px;}}

/* Chart + table */
.chwrap{{position:relative;width:100%;height:155px;}}
.tblwrap{{overflow-x:auto;}}
.tbl{{display:grid;grid-template-columns:110px repeat(5,minmax(0,1fr));
      gap:2px;min-width:480px;}}
.th{{font-size:10px;color:var(--text-light);text-align:center;padding:3px 2px;font-weight:600;}}
.tl{{font-size:10px;color:var(--text-light);display:flex;align-items:center;
     padding-right:3px;white-space:nowrap;}}
.tc{{border-radius:2px;padding:4px 3px;text-align:center;font-size:10px;
     font-weight:500;background:var(--sand);color:var(--text);}}

/* Footer */
.nav-links{{background:var(--slate-light);border-bottom:1px solid rgba(255,255,255,0.08);
           padding:0.4rem 1rem;display:flex;gap:0;flex-wrap:wrap;
           position:relative;z-index:500;}}
.nav-links a{{display:block;padding:0.45rem 1rem;font-size:0.75rem;font-weight:600;
             letter-spacing:0.05em;text-transform:uppercase;color:rgba(255,255,255,0.65);
             text-decoration:none;white-space:nowrap;}}
.nav-links a:hover{{color:#fff;}}
.nav-links a.active{{color:#fff;border-bottom:2px solid var(--dune);}}
/* Help dropdown */
.nav-dd{{position:relative;display:inline-block;}}
.nav-dd-btn{{display:block;padding:0.45rem 1rem;font-size:0.75rem;font-weight:600;
             letter-spacing:0.05em;text-transform:uppercase;color:rgba(255,255,255,0.65);
             background:transparent;border:none;cursor:pointer;
             white-space:nowrap;font-family:'Source Sans 3',sans-serif;}}
.nav-dd-btn:hover{{color:#fff;}}
.nav-dd-menu{{position:absolute;top:100%;right:0;min-width:180px;
              background:var(--slate);border:1px solid rgba(255,255,255,0.08);
              border-radius:0 0 3px 3px;padding:0.3rem 0;display:none;
              z-index:600;box-shadow:0 4px 12px rgba(0,0,0,0.25);}}
.nav-dd-menu a{{display:block;padding:0.5rem 1rem;font-size:0.72rem;font-weight:500;
                letter-spacing:0.03em;text-transform:none;color:rgba(255,255,255,0.8);
                text-decoration:none;white-space:nowrap;}}
.nav-dd-menu a:hover{{background:var(--slate-light);color:#fff;}}
.nav-dd.open .nav-dd-menu,.nav-dd:hover .nav-dd-menu{{display:block;}}
footer{{background:var(--slate);color:rgba(255,255,255,0.5);
        font-size:10px;padding:12px 18px;line-height:1.6;margin-top:4px;}}
footer a{{color:var(--dune);text-decoration:none;}}
footer a:hover{{text-decoration:underline;}}
</style>
</head>
<body>
<header>
  <div class="site-label">Newborough Warren NNR &middot; Anglesey SAC</div>
  <h1>Hydrological Scenario Viewer</h1>
  <p>{n_wells} dipwells &middot; 2005&#8211;2026 monitoring record &middot;
     SSM state-space model &middot; Hollingham (2026)</p>
</header>

<nav class="nav-links">
  <a href="index.html">&#8592; Home</a>
  <a href="seasonal_extremes_scatter.html">Seasonal extremes</a>
  <a href="scenario_viewer.html" class="active">Scenario viewer &#8594;</a>
  <div class="nav-dd" id="helpDd" style="margin-left:auto;">
    <button type="button" class="nav-dd-btn" onclick="toggleHelp(event)">Help <span style="font-size:0.7em;opacity:0.7;">&#x25BE;</span></button>
    <div class="nav-dd-menu">
      <a href="docs/scenario_viewer/reference_manual.pdf" target="_blank" rel="noopener">Reference Manual</a>
      <a href="docs/scenario_viewer/technical_note.pdf" target="_blank" rel="noopener">Technical Note</a>
    </div>
  </div>
</nav>

<div class="main" id="mainGrid">

<div class="ctrl">
  <div class="ch">Scenarios</div>
  <button class="sc on" id="btn_baseline"    onclick="loadSc('baseline')">Baseline (2005&#8211;2026)</button>
  <button class="sc"    id="btn_ukcp18_2050s" onclick="loadSc('ukcp18_2050s')">UKCP18 2050s (RCP8.5)</button>
  <button class="sc"    id="btn_ukcp18_2080s" onclick="loadSc('ukcp18_2080s')">UKCP18 2080s (RCP8.5)</button>
  <button class="sc"    id="btn_clearfell"   onclick="loadSc('clearfell')">Clearfell (interception&#8594;0, &#946;&#8322;&#8593;)</button>
  <button class="sc"    id="btn_broadleaf"   onclick="loadSc('broadleaf')">Broadleaf conversion</button>
  <button class="sc"    id="btn_thinning"    onclick="loadSc('thinning')">Forest thinning (50%)</button>
  <div class="sc-note">UKCP18 presets are central estimates (50th percentile) under RCP8.5 for Wales, with seasonally-structured perturbations applied to the paper's Winter (Nov&#8211;Mar) and Summer (May&#8211;Sep) climatologies. The equilibrium framework resolves seasonal Delta-h equilibria but not within-year dynamical trajectories.</div>
  <div class="hr"></div>

  <div class="ch">Climate (seasonal)</div>
  <div class="srow"><label>Winter P</label>
    <input type="range" min="0.5" max="1.5" step="0.01" value="1" id="sP_w" oninput="onSl()">
    <span class="sv" id="vP_w">1.00&#215;</span></div>
  <div class="srow"><label>Summer P</label>
    <input type="range" min="0.5" max="1.5" step="0.01" value="1" id="sP_s" oninput="onSl()">
    <span class="sv" id="vP_s">1.00&#215;</span></div>
  <div class="srow"><label>Winter PET</label>
    <input type="range" min="0.5" max="1.5" step="0.01" value="1" id="sPET_w" oninput="onSl()">
    <span class="sv" id="vPET_w">1.00&#215;</span></div>
  <div class="srow"><label>Summer PET</label>
    <input type="range" min="0.5" max="1.5" step="0.01" value="1" id="sPET_s" oninput="onSl()">
    <span class="sv" id="vPET_s">1.00&#215;</span></div>
  <div style="font-size:10px;color:var(--text-light);line-height:1.4;margin-top:3px;">
    Winter&nbsp;=&nbsp;Nov&#8211;Mar. Summer&nbsp;=&nbsp;May&#8211;Sep. Slider range 0.5&#8211;1.5&#215; brackets UKCP18 end-century probabilistic ranges for Wales under RCP8.5, while staying within the linear steady-state domain of the fitted state-space model.</div>
  <div class="hr"></div>

  <div class="ch">C4 Main Forest</div>
  <div class="ch">C5 Coastal Forest</div>
  <div class="srow"><label>Interception</label>
    <input type="range" min="0" max="0.4" step="0.01" value="0.24" id="sI" oninput="onSl()">
    <span class="sv" id="vI">24%</span></div>
  <div class="srow"><label>&#946;&#8322; scaling</label>
    <input type="range" min="0.5" max="2" step="0.05" value="1" id="sB2" oninput="onSl()">
    <span class="sv" id="vB2">1.00&#215;</span></div>
  <div class="hr"></div>

  <div class="ch">Specific yield (storage)</div>
  <div class="srow"><label>Sy endpoint</label>
    <input type="range" min="0" max="1" step="1" value="0" id="sSyMode" oninput="onSl()">
    <span class="sv" id="vSyMode">Fetter</span></div>
  <div style="font-size:10px;color:var(--text-light);line-height:1.4;margin-top:3px;">
    <strong>Fetter</strong> (lower bound): C1&nbsp;8%, C2&#8211;C4&nbsp;12%, C5/C6&nbsp;10% &#8212;
    conservative literature values from Fetter (2001).<br>
    <strong>WTF</strong> (upper bound): per-well WTF medians (scripts 17/18),
    clamped to the cluster floor. Monthly WTF overestimates Sy through
    capillary-fringe conflation (Healy &amp; Cook 2002), so these values
    represent an empirical ceiling.<br>
    Drives the <em>Storage shift</em> row (&#916;h&#8201;&#215;&#8201;Sy, mm of
    equivalent water column). Does not affect &#916;h itself.</div>
  <div class="hr"></div>

  <div class="ch">Map</div>
  <label class="ckrow"><input type="checkbox" id="chkKml" checked onchange="drawMap()">
    KML overlays</label>
  <label class="ckrow"><input type="checkbox" id="chkLbl" onchange="drawMap()">
    Well labels</label>
  <label class="ckrow"><input type="checkbox" id="chkRidge" checked onchange="drawMap()">
    Mask dune ridges <span style="color:var(--text-light);font-size:10px;">(depth view)</span></label>
</div>

<div class="rp">
  <div class="tabs">
    <button class="tab on" id="tab_annual" onclick="setSeas('annual')">Annual</button>
    <button class="tab" id="tab_winter" onclick="setSeas('winter')">Winter (Nov&#8211;Mar)</button>
    <button class="tab" id="tab_summer" onclick="setSeas('summer')">Summer (May&#8211;Sep)</button>
  </div>
  <div id="warnBox" class="warn" style="display:none"></div>
  <div class="metrics" id="mrow"></div>

  <div class="panel">
    <div class="phead">
      <h4>Groundwater surface &#8212; masked to site boundary</h4>
      <div class="rtabs">
        <button class="rt on" id="rt_dh"  onclick="setMM('dh')">&#916;h vs baseline</button>
        <button class="rt"    id="rt_abs" onclick="setMM('abs')">Absolute head</button>
        <button class="rt"    id="rt_dep" onclick="setMM('dep')">Depth below surface</button>
      </div>
    </div>
    <div class="mapwrap" id="mwrap">
      <canvas id="mapBg"></canvas>
      <canvas id="mapC" role="img" aria-label="IDW groundwater head surface, Newborough Warren"></canvas>
    </div>
    <div class="leg" id="legDiv"></div>
    <div class="tip" id="tipDiv"></div>
  </div>

  <div class="panel">
    <div class="phead">
      <h4>Head by cluster</h4>
      <div class="rtabs">
        <button class="rt on" id="ct_dh"  onclick="setCM('dh')">&#916;h (m)</button>
        <button class="rt"    id="ct_abs" onclick="setCM('abs')">Absolute (m AOD)</button>
      </div>
    </div>
    <div class="chwrap"><canvas id="hC" aria-label="Cluster head bar chart"></canvas></div>
  </div>

  <div class="panel">
    <h4>Cluster summary</h4>
    <div class="tblwrap"><div class="tbl" id="tbl"></div></div>
  </div>

  <div class="panel">
    <h4>Baseline monthly climatology (2005&#8211;2026, RAF Valley)</h4>
    <div class="tblwrap"><div class="tbl" id="mtbl"></div></div>
    <div style="font-size:10px;color:var(--text-light);line-height:1.4;margin-top:5px;">
      Monthly mean P and PET over the 2005&#8211;2026 monitoring period. Winter
      (Nov&#8211;Mar, shaded) and Summer (May&#8211;Sep) bins correspond to the
      seasonal multipliers above. UKCP18 2050s/2080s presets apply RCP8.5
      central-estimate seasonal perturbations to these baselines.
    </div>
  </div>
</div>
</div>

<footer>
  <span style="float:right;opacity:0.6;">viewer v{viewer_version}</span>
  &#916;h from SSM increment model using per-well &#946;&#8321;, &#946;&#8322;, &#946;&#8323; (scripts 01&#8211;03).
  Delaunay triangulation + linear barycentric weighting for published figures; viewer renders the same per-well &#916;h field via power-1 eight-nearest-neighbour IDW (see Technical Note for details).
  Interception: Corsican pine 24% (Freeman 2008); broadleaf 15% annual mean (Komatsu et al. 2011).
  K&nbsp;=&nbsp;6&nbsp;m/day (Betson et al. 2002). Sy: WTF medians (scripts 17/18);
  floors C1&nbsp;=&nbsp;6%, C2&#8211;C5&nbsp;=&nbsp;12%.
  CEH14 water balance residual &#945;&nbsp;=&nbsp;+0.222&nbsp;m/month (script 07).
  <a href="https://newbroman.github.io/Newborough_Hydrology/">Newborough Hydrology project site</a>
  &middot; Hollingham (2026) &#8212; <em>Journal of Hydrology: Regional Studies</em>.
</footer>

<script>
var WELLS={wells_json};
var POLYS={polys_json};
var CLIMATE={climate_json};
var SY_FLOOR={sy_floor_json};
var SY_LOWER={sy_lower_json};
var FOREST_INTERCEPTION={forest_interception};
var BROADLEAF_INTERCEPTION={broadleaf_interception};
var DEM_GRID={dem_grid_json};
var RIDGE_THRESH={ridge_threshold};
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
var CL_LABS={{1:'C1 Eastern lake-buffer',2:'C2 Eastern mature dune',
              3:'C3 Western mature dune',4:'C4 Forest',5:'C5 Coastal'}};
var CL_COLS={{1:'#1565C0',2:'#00897B',3:'#E64A19',4:'#558B2F',5:'#6A1B9A'}};
var EMIN={viewer_emin},EMAX={viewer_emax},NMIN={viewer_nmin},NMAX={viewer_nmax};
var HILLSHADE_B64="{hillshade_b64}";
var HILLSHADE_IMG=null;var HILLSHADE_READY=false;
if(HILLSHADE_B64){{HILLSHADE_IMG=new Image();HILLSHADE_IMG.onload=function(){{HILLSHADE_READY=true;if(typeof drawBg==='function'){{drawBg();}}if(typeof drawMap==='function'){{drawMap();}}}};HILLSHADE_IMG.src=HILLSHADE_B64;}}
var SCEN={{
  baseline:     {{sP_w:1,    sP_s:1,    sPET_w:1,    sPET_s:1,    sI:FOREST_INTERCEPTION,     sB2:1}},
  ukcp18_2050s: {{sP_w:1.10, sP_s:0.85, sPET_w:1.05, sPET_s:1.20, sI:FOREST_INTERCEPTION,     sB2:1}},
  ukcp18_2080s: {{sP_w:1.20, sP_s:0.70, sPET_w:1.10, sPET_s:1.35, sI:FOREST_INTERCEPTION,     sB2:1}},
  clearfell:    {{sP_w:1,    sP_s:1,    sPET_w:1,    sPET_s:1,    sI:0,                       sB2:1.20}},
  broadleaf:    {{sP_w:1,    sP_s:1,    sPET_w:1,    sPET_s:1,    sI:BROADLEAF_INTERCEPTION,  sB2:1.00}},
  thinning:     {{sP_w:1,    sP_s:1,    sPET_w:1,    sPET_s:1,    sI:FOREST_INTERCEPTION*0.5, sB2:1.10}},
}};
var WARN={{
  clearfell:    'Post-felling: canopy interception removed, \u03b2\u2082 increases. Study finding: clearfell deepens summer minima \u2014 the dominant control on winter flooding probability.',
  broadleaf:    'Broadleaf conversion (15% annual-mean interception). Steady-state equilibrium response only; the phenological winter-recharge mechanism that drives deeper summer minima under broadleaf is dynamical and not resolved in this framework (see Section 5.4.4).',
  ukcp18_2050s: 'UKCP18 2050s central estimate, RCP8.5, Wales. Winter +10% P / +5% PET, summer \u221215% P / +20% PET. Steady-state equilibrium response to seasonally-perturbed forcing only; within-year dynamical propagation is not resolved.',
  ukcp18_2080s: 'UKCP18 2080s central estimate, RCP8.5, Wales. Winter +20% P / +10% PET, summer \u221230% P / +35% PET. Steady-state equilibrium response only. See Section 5.6 for interpretive caveats.',
}};
var sea='annual',mm='dh',cm='dh',hChart=null;
var DH={{}},SH={{}},CUR_SL={{}};
var MW=0,MH=0;

function gs(){{return{{sP_w:+document.getElementById('sP_w').value,sP_s:+document.getElementById('sP_s').value,sPET_w:+document.getElementById('sPET_w').value,sPET_s:+document.getElementById('sPET_s').value,sI:+document.getElementById('sI').value,sB2:+document.getElementById('sB2').value,sSyMode:+document.getElementById('sSyMode').value}};}}
function rl(){{var s=gs();document.getElementById('vP_w').textContent=s.sP_w.toFixed(2)+'\xd7';document.getElementById('vP_s').textContent=s.sP_s.toFixed(2)+'\xd7';document.getElementById('vPET_w').textContent=s.sPET_w.toFixed(2)+'\xd7';document.getElementById('vPET_s').textContent=s.sPET_s.toFixed(2)+'\xd7';document.getElementById('vI').textContent=(s.sI*100).toFixed(0)+'%';document.getElementById('vB2').textContent=s.sB2.toFixed(2)+'\xd7';document.getElementById('vSyMode').textContent=s.sSyMode>=0.5?'WTF':'Fetter';}}
function onSl(){{rl();go();}}
function loadSc(n){{document.querySelectorAll('.sc').forEach(function(b){{b.classList.remove('on');}});document.getElementById('btn_'+n).classList.add('on');var sc=SCEN[n];['sP_w','sP_s','sPET_w','sPET_s','sI','sB2'].forEach(function(k){{document.getElementById(k).value=sc[k];}});rl();var wb=document.getElementById('warnBox');if(WARN[n]){{wb.textContent=WARN[n];wb.style.display='block';}}else wb.style.display='none';go();}}
function setSeas(s){{sea=s;document.querySelectorAll('.tab').forEach(function(b){{b.classList.remove('on');}});document.getElementById('tab_'+s).classList.add('on');go();}}
function setMM(m){{mm=m;document.querySelectorAll('[id^="rt_"]').forEach(function(b){{b.classList.remove('on');}});document.getElementById('rt_'+m).classList.add('on');drawMap();}}
function setCM(m){{cm=m;document.querySelectorAll('[id^="ct_"]').forEach(function(b){{b.classList.remove('on');}});document.getElementById('ct_'+m).classList.add('on');renderBar();}}
function syEff(w,mode){{if(mode>=0.5){{return Math.max((w.sy!=null?w.sy:(SY_LOWER[w.cl]||0.12)),SY_FLOOR[w.cl]||0.12);}}else{{return SY_LOWER[w.cl]||0.12;}}}}

function go(){{
  var sl=gs();CUR_SL=sl;
  // Seasonal baselines -- always needed so annual can weight winter+summer
  var cldW=CLIMATE.winter,cldS=CLIMATE.summer;
  function dhOne(b1,b2,b3,P_base,PET_base,sP,sPET,h,isForest){{
    var Peff_0=isForest?P_base*(1-FOREST_INTERCEPTION):P_base;
    var net0=b1*Peff_0-b2*PET_base-b3*Math.abs(h);
    var Psc=P_base*sP,PETsc=PET_base*sPET;
    var Peff_sc=isForest?Psc*(1-sl.sI):Psc;
    var b2sc=isForest?b2*sl.sB2:b2;
    return (b1*Peff_sc-b2sc*PETsc-b3*Math.abs(h))-net0;
  }}
  var well_dh={{}};
  for(var i=0;i<WELLS.length;i++){{
    var w=WELLS[i],b1=w.b1,b2=w.b2,b3=w.b3;
    if(b1==null){{var cb=CLIMATE.cluster_betas[w.cl]||{{}};b1=cb.b1;b2=cb.b2;b3=cb.b3;}}
    if(b1==null)continue;
    var h=sea==='annual'?w.mh:sea==='winter'?w.wh:w.sh;
    if(h==null)continue;
    var isForest=(w.cl===4||w.cl===5);
    if(sea==='winter'){{
      well_dh[w.n]=dhOne(b1,b2,b3,cldW.P,cldW.PET,sl.sP_w,sl.sPET_w,h,isForest);
    }}else if(sea==='summer'){{
      well_dh[w.n]=dhOne(b1,b2,b3,cldS.P,cldS.PET,sl.sP_s,sl.sPET_s,h,isForest);
    }}else{{  // annual = month-weighted mean of winter and summer responses
      var dhW=dhOne(b1,b2,b3,cldW.P,cldW.PET,sl.sP_w,sl.sPET_w,h,isForest);
      var dhS=dhOne(b1,b2,b3,cldS.P,cldS.PET,sl.sP_s,sl.sPET_s,h,isForest);
      well_dh[w.n]=0.5*(dhW+dhS);
    }}
  }}
  var dh={{}},sh={{}},cld=CLIMATE[sea];
  for(var cl=1;cl<=5;cl++){{
    var wc=WELLS.filter(function(w){{return w.cl===cl;}}),sum=0,cnt=0;
    for(var i=0;i<wc.length;i++){{if(well_dh[wc[i].n]!=null){{sum+=well_dh[wc[i].n];cnt++;}}}}
    dh[cl]=cnt>0?sum/cnt:0;
    sh[cl]=(cld.cluster_heads[cl]||0)+dh[cl];
  }}
  DH=dh;SH=sh;
  for(var i=0;i<WELLS.length;i++){{
    WELLS[i]._dh=well_dh[WELLS[i].n]!=null?well_dh[WELLS[i].n]:null;
    var hb=sea==='annual'?WELLS[i].mh:sea==='winter'?WELLS[i].wh:WELLS[i].sh;
    WELLS[i]._sh=(hb!=null&&WELLS[i]._dh!=null)?hb+WELLS[i]._dh:null;
  }}
  drawMap();renderBar();renderTable();renderMetrics();
}}

function dhCol(t){{t=Math.max(-1,Math.min(1,t));if(t>0){{var f=t;return[Math.round(255*(1-f*0.75)),Math.round(255*(1-f*0.75)),255];}}if(t<0){{var f=-t;return[255,Math.round(255*(1-f*0.75)),Math.round(255*(1-f*0.75))];}}return[255,255,255];}}
var GS=[[0,'#08306b'],[0.25,'#2171b5'],[0.5,'#74c476'],[0.75,'#fed976'],[1,'#e31a1c']];
function abCol(t){{t=Math.max(0,Math.min(1,t));for(var i=0;i<GS.length-1;i++){{if(t<=GS[i+1][0]){{var f=(t-GS[i][0])/(GS[i+1][0]-GS[i][0]),a=GS[i][1],b=GS[i+1][1];return[Math.round(parseInt(a.slice(1,3),16)+(parseInt(b.slice(1,3),16)-parseInt(a.slice(1,3),16))*f),Math.round(parseInt(a.slice(3,5),16)+(parseInt(b.slice(3,5),16)-parseInt(a.slice(3,5),16))*f),Math.round(parseInt(a.slice(5,7),16)+(parseInt(b.slice(5,7),16)-parseInt(a.slice(5,7),16))*f)];}}}}return[8,48,107];}}
// Depth-below-surface colour ramp, anchored to Curreli et al. (2013) SD15b/SD16
// ecological thresholds. Input d in metres (positive = water table below ground).
// 0.00 m (waterlogged) -> deep blue;  0.10 m (SD15b winter wet flooding limit) -> light blue;
// 0.61 m (SD15b summer wet slack viability limit) -> yellow-green transition;
// 0.98 m (SD16 dry slack viability limit) -> orange;  1.50 m+ -> deep red.
var DEP_MAX=1.5,DEP_T_WET=0.61,DEP_T_DRY=0.98,DEP_FLOOD=0.10;
var DEP_STOPS=[[0.00,'#08306b'],[0.066,'#4a90d0'],[0.407,'#9ecf74'],[0.653,'#f6b94a'],[1.00,'#8b1a1a']];
function depCol(d){{
  if(d==null||!isFinite(d))return null;
  var t=Math.max(0,Math.min(1,d/DEP_MAX));
  for(var i=0;i<DEP_STOPS.length-1;i++){{
    if(t<=DEP_STOPS[i+1][0]){{
      var f=(t-DEP_STOPS[i][0])/(DEP_STOPS[i+1][0]-DEP_STOPS[i][0]),
          a=DEP_STOPS[i][1],b=DEP_STOPS[i+1][1];
      return[Math.round(parseInt(a.slice(1,3),16)+(parseInt(b.slice(1,3),16)-parseInt(a.slice(1,3),16))*f),
             Math.round(parseInt(a.slice(3,5),16)+(parseInt(b.slice(3,5),16)-parseInt(a.slice(3,5),16))*f),
             Math.round(parseInt(a.slice(5,7),16)+(parseInt(b.slice(5,7),16)-parseInt(a.slice(5,7),16))*f)];
    }}
  }}
  return[139,26,26];
}}
function pip(px,py,poly){{var ins=false,n=poly.length;for(var i=0,j=n-1;i<n;j=i++){{var xi=poly[i][0],yi=poly[i][1],xj=poly[j][0],yj=poly[j][1];if(((yi>py)!==(yj>py))&&(px<(xj-xi)*(py-yi)/(yj-yi)+xi))ins=!ins;}}return ins;}}
// Inverse-distance-weighted interpolation, power 1, k=8 nearest neighbours.
// Minimum distance floor of 10 m smooths the immediate well neighbourhood,
// avoiding the power-2 bullseye halo without the divergence risk of a
// zero-distance singularity. If a query point lands within 5 m of a well
// (i.e. inside the well's own pixel block on the viewer canvas), the
// well's own value is returned unchanged -- this keeps the rendered
// colour at well locations visually consistent with the well marker.
// Power 1 gives a gentler falloff than power 2, which substantially
// reduces the halo artefacts previously visible on the delta-h surface.
function idw(px,py,pts){{
  if(!pts.length)return 0;
  var K=Math.min(8,pts.length),DMIN=10,DEXACT=5;
  var ds=new Array(pts.length);
  for(var i=0;i<pts.length;i++){{
    var dx=px-pts[i].E,dy=py-pts[i].N,d=Math.sqrt(dx*dx+dy*dy);
    if(d<DEXACT)return pts[i].v;
    ds[i]={{d:d<DMIN?DMIN:d,v:pts[i].v}};
  }}
  ds.sort(function(a,b){{return a.d-b.d;}});
  var num=0,den=0;
  for(var j=0;j<K;j++){{var w=1/ds[j].d;num+=w*ds[j].v;den+=w;}}
  return den>0?num/den:0;
}}
// Bilinear lookup into the embedded DEM elevation grid. Returns m AOD,
// or null if DEM_GRID is empty (pipeline run without rasterio/DEM) or the
// query point falls on a nodata cell. Called ~once per rendered pixel
// block during ridge-masked interpolation, so kept branch-light.
function demAt(E,N){{
  if(!DEM_GRID||!DEM_GRID.data||!DEM_GRID.cols)return null;
  var cols=DEM_GRID.cols,rows=DEM_GRID.rows,nd=DEM_GRID.nodata;
  // Fractional column (0 at EMIN, cols-1 at EMAX) and row (0 at NMAX top).
  var fx=(E-DEM_GRID.emin)/(DEM_GRID.emax-DEM_GRID.emin)*(cols-1);
  var fy=(DEM_GRID.nmax-N)/(DEM_GRID.nmax-DEM_GRID.nmin)*(rows-1);
  if(fx<0||fx>cols-1||fy<0||fy>rows-1)return null;
  var x0=Math.floor(fx),y0=Math.floor(fy);
  var x1=Math.min(x0+1,cols-1),y1=Math.min(y0+1,rows-1);
  var tx=fx-x0,ty=fy-y0;
  var v00=DEM_GRID.data[y0*cols+x0],v10=DEM_GRID.data[y0*cols+x1];
  var v01=DEM_GRID.data[y1*cols+x0],v11=DEM_GRID.data[y1*cols+x1];
  if(v00===nd||v10===nd||v01===nd||v11===nd)return null;
  return v00*(1-tx)*(1-ty)+v10*tx*(1-ty)+v01*(1-tx)*ty+v11*tx*ty;
}}
function tc(E,N){{return{{x:(E-EMIN)/(EMAX-EMIN)*MW,y:MH-(N-NMIN)/(NMAX-NMIN)*MH}};}}

function sizeMap(){{var wrap=document.getElementById('mwrap');MW=wrap.clientWidth;MH=wrap.clientHeight;['mapBg','mapC'].forEach(function(id){{var c=document.getElementById(id);c.width=MW;c.height=MH;}});}}
function drawBg(){{
  var c=document.getElementById('mapBg'),ctx=c.getContext('2d');
  // Base fill -- shown everywhere, covered by hillshade where DEM is present.
  ctx.fillStyle='#c0ccba';ctx.fillRect(0,0,MW,MH);
  var sp=POLYS.site;
  // Site polygon fill (shows through where hillshade is absent / transparent).
  if(sp&&sp.length){{
    ctx.beginPath();
    var p0=tc(sp[0][0],sp[0][1]);ctx.moveTo(p0.x,p0.y);
    for(var i=1;i<sp.length;i++){{var p=tc(sp[i][0],sp[i][1]);ctx.lineTo(p.x,p.y);}}
    ctx.closePath();ctx.fillStyle='#daebd2';ctx.fill();
  }}
  // Hillshade overlay (transparent PNG, already site-masked server-side).
  if(HILLSHADE_READY&&HILLSHADE_IMG){{ctx.drawImage(HILLSHADE_IMG,0,0,MW,MH);}}
  // Site polygon outline drawn last so it stays crisp over the hillshade.
  if(sp&&sp.length){{
    ctx.beginPath();
    var q0=tc(sp[0][0],sp[0][1]);ctx.moveTo(q0.x,q0.y);
    for(var j=1;j<sp.length;j++){{var q=tc(sp[j][0],sp[j][1]);ctx.lineTo(q.x,q.y);}}
    ctx.closePath();ctx.strokeStyle='#7aaa70';ctx.lineWidth=1.3;ctx.stroke();
  }}
}}
function dpoly(ctx,poly,fill,stroke,lw){{if(!poly||poly.length<2)return;var p0=tc(poly[0][0],poly[0][1]);ctx.beginPath();ctx.moveTo(p0.x,p0.y);for(var i=1;i<poly.length;i++){{var p=tc(poly[i][0],poly[i][1]);ctx.lineTo(p.x,p.y);}}ctx.closePath();if(fill){{ctx.fillStyle=fill;ctx.fill();}}if(stroke){{ctx.strokeStyle=stroke;ctx.lineWidth=lw||1.6;ctx.setLineDash([]);ctx.stroke();}};}}

function drawMap(){{
  if(!MW)return;
  var canvas=document.getElementById('mapC'),ctx=canvas.getContext('2d');
  ctx.clearRect(0,0,MW,MH);
  // Per-well *head* values (always needed; depth mode derives from these).
  // For dh mode the rendered value is Delta-h; for abs and dep modes it
  // is the scenario-adjusted head in m AOD.
  var headPts=[],dhPts=[];
  for(var i=0;i<WELLS.length;i++){{
    var w=WELLS[i];if(!w.E||!w.N)continue;
    if(w._sh!=null)headPts.push({{E:w.E,N:w.N,v:w._sh}});
    dhPts.push({{E:w.E,N:w.N,v:w._dh!=null?w._dh:0}});
  }}
  if(!headPts.length)return;
  // Ridge-mask logic now applies only in depth mode -- for elevation maps
  // (dh, abs) the interpolated surface is physically defined across ridges
  // because the water table is a continuous surface independent of DEM.
  // In depth mode (DEM minus IDW head), ridge cells would report an
  // apparent depth of several metres that reflects the ridge height, not
  // any hydrological feature, and masking them is therefore necessary.
  var chkR=document.getElementById('chkRidge');
  var doRidge=(mm==='dep')&&(chkR&&chkR.checked)&&DEM_GRID&&DEM_GRID.cols;
  var demPts=[];
  if(doRidge){{
    for(var i2=0;i2<WELLS.length;i2++){{var ww=WELLS[i2];if(!ww.E||!ww.N||ww.dg==null)continue;demPts.push({{E:ww.E,N:ww.N,v:ww.dg}});}}
    if(demPts.length<3)doRidge=false;
  }}
  // Colour-scale bounds for absolute head mode.
  var hv=headPts.map(function(p){{return p.v;}}),hMn=Math.min.apply(null,hv),hMx=Math.max.apply(null,hv);
  // Colour-scale bound for dh mode (symmetric diverging).
  var dv=dhPts.map(function(p){{return p.v;}}),dMn=Math.min.apply(null,dv),dMx=Math.max.apply(null,dv);
  var dhMx=Math.max(Math.abs(dMn),Math.abs(dMx),0.005);
  var site=POLYS.site||[],ST=Math.max(10,Math.round(MW/55));
  var img=ctx.createImageData(MW,MH);
  for(var k=0;k<img.data.length;k+=4)img.data[k+3]=0;
  for(var py=0;py<MH;py+=ST){{for(var px=0;px<MW;px+=ST){{
    var E=EMIN+(px/MW)*(EMAX-EMIN),N=NMIN+((MH-py)/MH)*(NMAX-NMIN);
    if(site.length&&!pip(E,N,site))continue;
    if(doRidge){{
      var demHere=demAt(E,N);
      if(demHere!=null){{
        var wellDem=idw(E,N,demPts);
        if(demHere-wellDem>RIDGE_THRESH)continue;
      }}
    }}
    var rgb=null;
    if(mm==='dh'){{
      var dv0=idw(E,N,dhPts);
      rgb=dhCol(dv0/dhMx);
    }}else if(mm==='abs'){{
      var hv0=idw(E,N,headPts);
      rgb=abCol((hv0-hMn)/(hMx-hMn||1));
    }}else{{  // 'dep' -- Option X: per-cell DEM minus IDW-interpolated head.
      var dm=demAt(E,N);
      if(dm==null)continue;
      var hh=idw(E,N,headPts),dep=dm-hh;
      rgb=depCol(dep);
      if(rgb==null)continue;
    }}
    if(rgb==null)continue;
    for(var dy=0;dy<ST&&py+dy<MH;dy++){{for(var dx=0;dx<ST&&px+dx<MW;dx++){{
      if(site.length){{var E2=EMIN+((px+dx)/MW)*(EMAX-EMIN),N2=NMIN+((MH-py-dy)/MH)*(NMAX-NMIN);if(!pip(E2,N2,site))continue;}}
      var idx=4*((py+dy)*MW+(px+dx));img.data[idx]=rgb[0];img.data[idx+1]=rgb[1];img.data[idx+2]=rgb[2];img.data[idx+3]=215;
    }}}}
  }}}}
  ctx.putImageData(img,0,0);
  var kml=document.getElementById('chkKml').checked;
  if(kml){{
    if(POLYS.forest)    dpoly(ctx,POLYS.forest,   'rgba(80,40,130,0.12)','#6a0dad',1.7);
    if(POLYS.broadleaf) dpoly(ctx,POLYS.broadleaf,'rgba(30,120,80,0.35)','#1a7a50',1.8);
    if(POLYS.clearfell) dpoly(ctx,POLYS.clearfell,'rgba(230,100,20,0.45)','#e65014',2.0);
    if(POLYS.lake)      dpoly(ctx,POLYS.lake,     'rgba(20,80,200,0.50)','#1a50b0',1.5);
  }}
  var syV=WELLS.filter(function(w){{return w.sy!=null;}}).map(function(w){{return w.sy;}}),syMn=Math.min.apply(null,syV),syMx=Math.max.apply(null,syV);
  var showLbl=document.getElementById('chkLbl').checked;
  for(var i=0;i<WELLS.length;i++){{
    var w=WELLS[i];if(!w.E||!w.N)continue;
    var p=tc(w.E,w.N),r=w.sy!=null?2.5+((w.sy-syMn)/(syMx-syMn))*3.5:2.5;
    ctx.beginPath();ctx.arc(p.x,p.y,r,0,2*Math.PI);
    ctx.fillStyle='rgba(255,255,255,0.9)';ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.48)';ctx.lineWidth=0.7;ctx.stroke();
    if(showLbl&&MW>360){{ctx.fillStyle='rgba(0,0,0,0.6)';ctx.font='7px sans-serif';ctx.textAlign='left';ctx.fillText(w.n,p.x+r+1,p.y+2.5);}}
  }}
  var ld=document.getElementById('legDiv');
  var kl=kml?'<span><span class="ls" style="background:rgba(230,100,20,0.55);border:1px solid #e65014;"></span>Clearfell</span><span><span class="ls" style="background:rgba(30,120,80,0.45);border:1px solid #1a7a50;"></span>Broadleaf</span><span><span class="ls" style="background:rgba(80,40,130,0.25);border:1px solid #6a0dad;"></span>Forest</span><span><span class="ls" style="background:rgba(20,80,200,0.5);border:1px solid #1a50b0;"></span>Llyn Rhos-ddu</span>':'';
  if(mm==='dh'){{
    ld.innerHTML='<span style="color:#b71c1c">'+dMn.toFixed(3)+'&#8202;m</span><canvas id="lc" width="70" height="9" style="width:70px;height:9px;border-radius:2px;vertical-align:middle;"></canvas><span style="color:#0d47a1">+'+(dMx).toFixed(3)+'&#8202;m</span><span>red&#8202;=&#8202;drier &middot; blue&#8202;=&#8202;wetter</span>'+kl;
    setTimeout(function(){{var c=document.getElementById('lc');if(!c)return;var x=c.getContext('2d'),g=x.createLinearGradient(0,0,70,0);g.addColorStop(0,'rgb(255,100,100)');g.addColorStop(0.5,'rgb(255,255,255)');g.addColorStop(1,'rgb(100,100,255)');x.fillStyle=g;x.fillRect(0,0,70,9);}},30);
  }}else if(mm==='abs'){{
    ld.innerHTML='<span>Low</span><canvas id="lc" width="70" height="9" style="width:70px;height:9px;border-radius:2px;vertical-align:middle;"></canvas><span>High (m AOD)</span>'+kl;
    setTimeout(function(){{var c=document.getElementById('lc');if(!c)return;var x=c.getContext('2d'),g=x.createLinearGradient(0,0,70,0);GS.forEach(function(s){{g.addColorStop(s[0],s[1]);}});x.fillStyle=g;x.fillRect(0,0,70,9);}},30);
  }}else{{  // depth mode
    // Depth legend with ecological threshold tick marks at SD15b (0.61 m)
    // and SD16 (0.98 m) from Curreli et al. (2013).
    ld.innerHTML='<span>0&#8202;m</span><canvas id="lc" width="100" height="9" style="width:100px;height:9px;border-radius:2px;vertical-align:middle;"></canvas><span>'+DEP_MAX.toFixed(1)+'&#8202;m</span><span style="font-size:10px;color:var(--text-light);">depth below surface<br><span style="color:#1565c0;">&#9660;</span>&nbsp;'+DEP_T_WET.toFixed(2)+'&#8202;m wet slack&nbsp;&nbsp;<span style="color:#b71c1c;">&#9660;</span>&nbsp;'+DEP_T_DRY.toFixed(2)+'&#8202;m dry slack</span>'+kl;
    setTimeout(function(){{
      var c=document.getElementById('lc');if(!c)return;
      var x=c.getContext('2d'),g=x.createLinearGradient(0,0,100,0);
      DEP_STOPS.forEach(function(s){{g.addColorStop(s[0],s[1]);}});
      x.fillStyle=g;x.fillRect(0,0,100,9);
      // Threshold tick marks on the gradient.
      var tWet=DEP_T_WET/DEP_MAX*100,tDry=DEP_T_DRY/DEP_MAX*100;
      x.strokeStyle='rgba(0,0,0,0.75)';x.lineWidth=1;
      x.beginPath();x.moveTo(tWet,0);x.lineTo(tWet,9);x.stroke();
      x.beginPath();x.moveTo(tDry,0);x.lineTo(tDry,9);x.stroke();
    }},30);
  }}
}}

document.addEventListener('DOMContentLoaded',function(){{
  document.getElementById('mapC').addEventListener('mousemove',function(e){{
    if(!MW)return;
    var r=this.getBoundingClientRect(),sx=MW/r.width,mx=(e.clientX-r.left)*sx,my=(e.clientY-r.top)*sx;
    var best=null,bd=Infinity;
    for(var i=0;i<WELLS.length;i++){{var w=WELLS[i];if(!w.E||!w.N)continue;var p=tc(w.E,w.N),d=Math.hypot(mx-p.x,my-p.y);if(d<bd){{bd=d;best=w;}}}}
    var tip=document.getElementById('tipDiv');
    if(best&&bd<18){{
      var hb=sea==='annual'?best.mh:sea==='winter'?best.wh:best.sh,dh=best._dh||0;
      // Depth below surface at the well, using the well's own DEM elevation
      // (no IDW here -- this is the well's actual depth reading).
      var depTxt='';
      if(best.dg!=null&&hb!=null){{
        var depBase=best.dg-hb,depSce=best.dg-(hb+dh);
        depTxt=' \u00b7 depth '+depBase.toFixed(2)+'\u2192'+depSce.toFixed(2)+'\u00a0m';
      }}
      tip.textContent=best.n+' \u00b7 C'+best.cl+' \u00b7 baseline '+hb.toFixed(2)+'\u00a0m\u00a0AOD \u00b7 scenario '+(hb+dh).toFixed(2)+'\u00a0m\u00a0AOD \u00b7 \u0394h '+(dh>=0?'+':'')+dh.toFixed(3)+'\u00a0m'+depTxt+(best.sy?' \u00b7 Sy\u00a0'+(best.sy*100).toFixed(1)+'%':'');
    }}else tip.textContent='';
  }});
}});

function renderBar(){{
  var cls=[1,2,3,4,5];if(hChart)hChart.destroy();var ds,yL;
  if(cm==='dh'){{yL='\u0394h (m)';ds=[{{label:'\u0394h vs baseline',data:cls.map(function(c){{return+(DH[c]||0).toFixed(4);}}),backgroundColor:cls.map(function(c){{var v=DH[c]||0;return v>0.001?'rgba(21,101,192,0.65)':v<-0.001?'rgba(183,28,28,0.65)':'rgba(120,120,120,0.3)'}}),borderColor:cls.map(function(c){{var v=DH[c]||0;return v>0.001?'#1565c0':v<-0.001?'#b71c1c':'#aaa'}}),borderWidth:1.5}}];}}
  else{{yL='m AOD';ds=[{{label:'Baseline',data:cls.map(function(c){{return+(CLIMATE[sea].cluster_heads[c]||0).toFixed(3);}}),backgroundColor:'rgba(120,120,120,0.2)',borderColor:'rgba(120,120,120,0.55)',borderWidth:1}},{{label:'Scenario',data:cls.map(function(c){{return+(SH[c]||0).toFixed(3);}}),backgroundColor:cls.map(function(c){{return CL_COLS[c]+'99';}}),borderColor:cls.map(function(c){{return CL_COLS[c];}}),borderWidth:1.5}}];}}
  hChart=new Chart(document.getElementById('hC').getContext('2d'),{{type:'bar',data:{{labels:cls.map(function(c){{return CL_LABS[c];}}),datasets:ds}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{font:{{size:10}},boxWidth:9,padding:7}}}}}},scales:{{y:{{title:{{display:true,text:yL,font:{{size:10}}}},ticks:{{font:{{size:10}}}},grid:{{color:'rgba(0,0,0,0.06)'}}}},x:{{ticks:{{font:{{size:10}},maxRotation:15}}}}}}}}}});
}}

function renderTable(){{
  var cls=[1,2,3,4,5],sl=CUR_SL||{{sP_w:1,sP_s:1,sPET_w:1,sPET_s:1,sSyMode:0,sI:FOREST_INTERCEPTION,sB2:1}},cld=CLIMATE[sea],P=cld.P,PET=cld.PET;
  // Choose multipliers matching the current seasonal view; annual = winter+summer average
  var sP=(sea==='winter')?sl.sP_w:(sea==='summer')?sl.sP_s:0.5*(sl.sP_w+sl.sP_s);
  var sPET=(sea==='winter')?sl.sPET_w:(sea==='summer')?sl.sPET_s:0.5*(sl.sPET_w+sl.sPET_s);
  var rows=[
    {{l:'Baseline (m AOD)',v:cls.map(function(c){{return(cld.cluster_heads[c]||0).toFixed(2);}}),d:false}},
    {{l:'Scenario (m AOD)',v:cls.map(function(c){{return(SH[c]||0).toFixed(2);}}),d:false}},
    {{l:'\u0394 head (m)',v:cls.map(function(c){{return(DH[c]>=0?'+':'')+(DH[c]||0).toFixed(3);}}),d:true}},
    {{l:'Mean Sy (%)',v:cls.map(function(c){{var cw=WELLS.filter(function(w){{return w.cl===c;}});if(!cw.length)return'\u2014';var s=cw.reduce(function(acc,w){{return acc+syEff(w,sl.sSyMode);}},0)/cw.length;return(s*100).toFixed(1)+'%';}}),d:false}},
    {{l:'Storage shift (mm)',v:cls.map(function(c){{var cw=WELLS.filter(function(w){{return w.cl===c;}});if(!cw.length||DH[c]==null)return'\u2014';var s=cw.reduce(function(acc,w){{return acc+syEff(w,sl.sSyMode);}},0)/cw.length;var shift=s*DH[c]*1000;return(shift>=0?'+':'')+shift.toFixed(1);}}),d:true}},
    {{l:'P\u2091\u2091 mm/mo',v:cls.map(function(c){{return(((c===4||c===5)?P*sP*(1-sl.sI):P*sP)*1000).toFixed(1);}}),d:false}},
    {{l:'PET draw mm/mo',v:cls.map(function(c){{var cb=CLIMATE.cluster_betas[c]||{{}},b2=cb.b2||0,b2s=(c===4||c===5)?b2*sl.sB2:b2;return(b2s*PET*sPET*1000).toFixed(1);}}),d:false}},
  ];
  function bg(v,d){{if(!d)return'#f5f5f5';var n=parseFloat(v);return n>0.005?'#c8e6c9':n<-0.005?'#ffcdd2':'#f5f5f5';}}
  function tx(v,d){{if(!d)return'#333';var n=parseFloat(v);return n>0.005?'#1b5e20':n<-0.005?'#b71c1c':'#555';}}
  document.getElementById('tbl').innerHTML='<div class="th"></div>'+cls.map(function(c){{return'<div class="th">C'+c+'</div>';}}).join('')+rows.map(function(r){{return'<div class="tl">'+r.l+'</div>'+r.v.map(function(v){{return'<div class="tc" style="background:'+bg(v,r.d)+';color:'+tx(v,r.d)+'">'+v+'</div>';}}).join('');}}).join('');
}}

function renderMonthlyTable(){{
  // Baseline monthly P/PET climatology -- static, called once at init
  var M=CLIMATE.monthly||{{P_mm:{{}},PET_mm:{{}}}};
  var names=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var WIN={{11:1,12:1,1:1,2:1,3:1}};
  var SUM={{5:1,6:1,7:1,8:1,9:1}};
  var head='<div class="th">Month</div>';
  for(var i=0;i<12;i++){{head+='<div class="th">'+names[i]+'</div>';}}
  function rowOf(label,series,dec){{
    var s='<div class="tl">'+label+'</div>';
    for(var i=0;i<12;i++){{
      var m=i+1,v=series[String(m)];
      var bg=WIN[m]?'#dde9f2':SUM[m]?'#fdeee1':'#f5f5f5';
      s+='<div class="tc" style="background:'+bg+';color:#333">'+((v!=null)?v.toFixed(dec):'\u2014')+'</div>';
    }}
    return s;
  }}
  var el=document.getElementById('mtbl');
  if(!el)return;
  el.style.gridTemplateColumns='1.3fr repeat(12, minmax(0,1fr))';
  el.innerHTML=head+rowOf('P (mm/mo)',M.P_mm,1)+rowOf('PET (mm/mo)',M.PET_mm,1);
}}

function renderMetrics(){{
  var cls=[1,2,3,4,5],sl=CUR_SL||{{sSyMode:0}};
  var mDH=cls.reduce(function(s,c){{return s+(DH[c]||0);}},0)/5;
  var c4DH=DH[4]||0, c5DH=DH[5]||0;
  function dc(v){{return v>0.002?'#0d47a1':v<-0.002?'#b71c1c':'#333';}}
  function mc(l,v,u,col){{return'<div class="mc"><div class="ml">'+l+'</div><div class="mv" style="color:'+col+'">'+v+' <span class="mu">'+u+'</span></div></div>';}}
  var allW=WELLS.filter(function(w){{return cls.indexOf(w.cl)>=0;}});
  var mSy=allW.length?allW.reduce(function(s,w){{return s+syEff(w,sl.sSyMode);}},0)/allW.length:0.12;
  var c4w=WELLS.filter(function(w){{return w.cl===4;}});
  var c5w=WELLS.filter(function(w){{return w.cl===5;}});
  var c4Sy=c4w.length?c4w.reduce(function(s,w){{return s+syEff(w,sl.sSyMode);}},0)/c4w.length:0.12;
  var c5Sy=c5w.length?c5w.reduce(function(s,w){{return s+syEff(w,sl.sSyMode);}},0)/c5w.length:0.12;
  var mShift=mSy*mDH*1000, c4Shift=c4Sy*c4DH*1000, c5Shift=c5Sy*c5DH*1000;
  function fmtShift(v){{return(v>=0?'+':'')+v.toFixed(1);}}
  document.getElementById('mrow').innerHTML=mc('Mean \u0394h',(mDH>=0?'+':'')+mDH.toFixed(3),'m',dc(mDH))+mc('C4 \u0394h',(c4DH>=0?'+':'')+c4DH.toFixed(3),'m',dc(c4DH))+mc('C5 \u0394h',(c5DH>=0?'+':'')+c5DH.toFixed(3),'m',dc(c5DH))+mc('Mean Sy',(mSy*100).toFixed(1),'%','#333')+mc('C4 Sy',(c4Sy*100).toFixed(1),'%','#333')+mc('C5 Sy',(c5Sy*100).toFixed(1),'%','#333')+mc('Mean storage',fmtShift(mShift),'mm',dc(mDH))+mc('C4 storage',fmtShift(c4Shift),'mm',dc(c4DH))+mc('C5 storage',fmtShift(c5Shift),'mm',dc(c5DH));
}}

function applyLayout(){{document.getElementById('mainGrid').style.gridTemplateColumns=window.innerWidth<640?'1fr':'210px minmax(0,1fr)';}}
function toggleHelp(e){{e.stopPropagation();var dd=document.getElementById('helpDd');if(dd)dd.classList.toggle('open');}}
document.addEventListener('click',function(e){{var dd=document.getElementById('helpDd');if(dd&&!dd.contains(e.target))dd.classList.remove('open');}});
function init(){{applyLayout();sizeMap();drawBg();document.getElementById('sI').value=FOREST_INTERCEPTION;rl();renderMonthlyTable();go();}}
setTimeout(init,60);
window.addEventListener('resize',function(){{applyLayout();sizeMap();drawBg();drawMap();}});
</script>
</body>
</html>
"""


# ============================================================================
# SCENARIO SUMMARY (Python mirror of the viewer's JS calculation)
# ============================================================================

def _well_dh(row, sl, P0, PET0, h_col, cluster_betas, season):
    """
    Compute Delta-h (m per unit time) for a single well under one scenario
    and season. Mirrors the JS go() function in the viewer exactly.
    Returns None if beta coefficients or head data are missing.

    season is one of 'annual', 'winter', 'summer'. For 'annual' the result
    is the month-weighted mean of the winter and summer responses.
    """
    b1, b2, b3 = row["b1"], row["b2"], row["b3"]
    cl = int(row["Cluster"]) if pd.notna(row["Cluster"]) else None
    if pd.isna(b1):
        cb = cluster_betas.get(cl, {})
        b1, b2, b3 = cb.get("b1"), cb.get("b2"), cb.get("b3")
    if b1 is None or pd.isna(b1):
        return None
    h = row.get(h_col)
    if pd.isna(h):
        return None

    is_forest = (cl == 4 or cl == 5)

    def _dh_one(P_base, PET_base, sP, sPET):
        Peff_0 = P_base * (1 - FOREST_INTERCEPTION) if is_forest else P_base
        net0 = b1 * Peff_0 - b2 * PET_base - b3 * abs(h)
        Psc = P_base * sP
        PETsc = PET_base * sPET
        Peff_sc = Psc * (1 - sl["sI"]) if is_forest else Psc
        b2_sc = b2 * sl["sB2"] if is_forest else b2
        net_sc = b1 * Peff_sc - b2_sc * PETsc - b3 * abs(h)
        return net_sc - net0

    if season == "winter":
        return _dh_one(P0, PET0, sl["sP_w"], sl["sPET_w"])
    elif season == "summer":
        return _dh_one(P0, PET0, sl["sP_s"], sl["sPET_s"])
    else:  # annual
        # P0/PET0 here are the winter and summer baselines respectively;
        # passed in as a tuple (P_win, P_sum, PET_win, PET_sum).
        # The annual Delta-h is the month-weighted average of the two
        # seasonal Delta-h values. Winter = Nov-Mar (5 months),
        # Summer = May-Sep (5 months), April + October shoulders split evenly.
        P_w, P_s, PET_w, PET_s = P0
        dh_w = _dh_one(P_w, PET_w, sl["sP_w"], sl["sPET_w"])
        dh_s = _dh_one(P_s, PET_s, sl["sP_s"], sl["sPET_s"])
        return 0.5 * (dh_w + dh_s)


def compute_scenario_summary(wt, climate_stats, out_dir):
    """
    For each scenario x season x cluster, compute the mean Delta-h across all
    wells assigned to that cluster (excluding wells with missing beta or head).
    Writes a tidy summary CSV to out_dir and returns the DataFrame.
    """
    cluster_betas = {}
    for cl_int in [1, 2, 3, 4, 5]:
        sub = wt[(wt["Cluster"] == cl_int) & wt["b1"].notna()]
        if len(sub) == 0:
            sub = wt[wt["Cluster"] == cl_int]
        cluster_betas[cl_int] = {
            "b1": sub["b1"].mean() if len(sub) else None,
            "b2": sub["b2"].mean() if len(sub) else None,
            "b3": sub["b3"].mean() if len(sub) else None,
        }

    h_col_map = {"annual": "mh", "winter": "wh", "summer": "sh"}
    P_w, PET_w = climate_stats["winter"]
    P_s, PET_s = climate_stats["summer"]
    rows = []
    for sc_name, sl in SCENARIO_PARAMS.items():
        for sea in SEASONS:
            if sea == "winter":
                P0, PET0 = P_w, PET_w
            elif sea == "summer":
                P0, PET0 = P_s, PET_s
            else:  # annual -- pass tuple of both seasonal baselines
                P0, PET0 = (P_w, P_s, PET_w, PET_s), None
            h_col = h_col_map[sea]
            dh = wt.apply(lambda r: _well_dh(r, sl, P0, PET0, h_col,
                                             cluster_betas, sea), axis=1)
            wt_tmp = wt.assign(_dh=dh)
            for cl_int in [1, 2, 3, 4, 5]:
                sub = wt_tmp[(wt_tmp["Cluster"] == cl_int)
                             & wt_tmp["_dh"].notna()]
                dh_mean = sub["_dh"].mean() if len(sub) else np.nan
                dh_med  = sub["_dh"].median() if len(sub) else np.nan
                rows.append({
                    "scenario":    sc_name,
                    "season":      sea,
                    "cluster":     f"C{cl_int}",
                    "n_wells":     int(len(sub)),
                    "dh_mean_m":   round(dh_mean, 4) if pd.notna(dh_mean) else np.nan,
                    "dh_median_m": round(dh_med,  4) if pd.notna(dh_med)  else np.nan,
                })
            sub_all = wt_tmp[wt_tmp["_dh"].notna()]
            rows.append({
                "scenario":    sc_name,
                "season":      sea,
                "cluster":     "SITE",
                "n_wells":     int(len(sub_all)),
                "dh_mean_m":   round(sub_all["_dh"].mean(),   4) if len(sub_all) else np.nan,
                "dh_median_m": round(sub_all["_dh"].median(), 4) if len(sub_all) else np.nan,
            })

    out = pd.DataFrame(rows)
    out_csv = out_dir / "19_scenario_summary.csv"
    out.to_csv(out_csv, index=False)
    print(f"  Scenario summary CSV: {out_csv.name} "
          f"({len(out)} rows = {len(SCENARIO_PARAMS)} scenarios x "
          f"{len(SEASONS)} seasons x 6 spatial units)")
    return out


# ============================================================================
# MAIN
# ============================================================================

def main(out_path=None):
    make_all_dirs()
    out_path = Path(out_path) if out_path else DIR_19 / "scenario_viewer.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Script 19 -- Scenario Viewer Generator")
    print(f"Output: {out_path}")
    print("=" * 60)

    print("\n[1/4] Loading data...")
    loc, cl, md, elev, maod, clim, sy_df = load_data()

    print("\n[2/4] Building well table...")
    wt, climate_stats = build_well_table(loc, cl, md, elev, maod, clim, sy_df)

    print("\n[3/4] Loading KML polygons from DATA_DIR...")
    print(f"  DATA_DIR = {DATA_DIR}")
    polys = load_kml_polygons()

    print("\n[4/4] Generating HTML...")
    wells_list   = serialise_wells(wt)
    climate_data = serialise_climate(wt, climate_stats)
    sy_floor_js  = {str(k): v for k, v in SY_FLOOR.items()}
    sy_lower_js  = {str(k): v for k, v in SY_DEFAULTS.items()}

    print("  Building DEM hillshade basemap...")
    hillshade_b64 = build_hillshade_base64(polys.get("site"))

    print("  Building DEM grid for ridge masking...")
    dem_grid = build_dem_grid(polys.get("site"))

    html = HTML_TEMPLATE.format(
        n_wells=len(wt),
        wells_json=json.dumps(wells_list, separators=(",", ":")),
        polys_json=json.dumps(polys, separators=(",", ":")),
        climate_json=json.dumps(climate_data, separators=(",", ":")),
        sy_floor_json=json.dumps(sy_floor_js, separators=(",", ":")),
        sy_lower_json=json.dumps(sy_lower_js, separators=(",", ":")),
        forest_interception=FOREST_INTERCEPTION,
        broadleaf_interception=BROADLEAF_INTERCEPTION,
        hillshade_b64=hillshade_b64,
        dem_grid_json=json.dumps(dem_grid, separators=(",", ":")),
        ridge_threshold=RIDGE_MASK_THRESHOLD,
        viewer_emin=VIEWER_EMIN,
        viewer_emax=VIEWER_EMAX,
        viewer_nmin=VIEWER_NMIN,
        viewer_nmax=VIEWER_NMAX,
        viewer_version=__version__,
    )

    out_path.write_text(html, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024

    # Scenario summary CSV -- mirrors the viewer's calculation exactly,
    # providing a citeable output for Section 4.9 of the manuscript.
    compute_scenario_summary(wt, climate_stats, DIR_19)

    print(f"\n  Saved   : {out_path}")
    print(f"  Version : v{__version__}")
    print(f"  Size    : {size_kb:.1f} KB")
    print(f"  Wells   : {len(wt)} total  "
          f"(beta available: {wt['b1'].notna().sum()})")
    print(f"  Extent  : E {VIEWER_EMIN}-{VIEWER_EMAX}, N {VIEWER_NMIN}-{VIEWER_NMAX}")
    print(f"  KML     : {list(polys.keys())}")
    print(f"\n--- Script 19 complete ---")
    print(f"Open {out_path.name} in any browser.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script 19 -- Generate self-contained scenario viewer HTML")
    parser.add_argument(
        "--out", default=None,
        help="Output path (default: outputs/19_spatial_groundwater/"
             "scenario_viewer.html)")
    args = parser.parse_args()
    main(out_path=args.out)
