"""
20_spatial_figures.py
=====================
Publication-quality spatial figures for Section 4.9 of:

  Hollingham, M. (2026) "Hydrogeological Dynamics, Behavioural Clustering and
  Management Intervention Analysis at Newborough Warren Coastal Sand Dune
  Aquifer, Wales". Journal of Hydrology: Regional Studies.

Two figures are produced:

  Figure 1 — Mean Annual Water Table with Stream Network and Flow Vectors
  -----------------------------------------------------------------------
  Output: outputs/20_spatial_figures/20_head_surface_streams.png

  Mean annual water table (m AOD) as an IDW-interpolated surface over a
  greyscale DEM hillshade, with:
    - SAGA stream network (skeletonised) as connected blue polylines
    - Groundwater flow direction vectors (normalised Darcy quiver)
    - Site feature overlays (forest boundary, lake, clearfell zone, channels)
    - Well symbols coloured by cluster
    - 1 m head contours with labels

  Figure 2 — SSM Water Balance Residual vs Ridge Hillslope Gradient
  -------------------------------------------------------------------
  Output: outputs/20_spatial_figures/20_residual_ssm.png

  Two-panel validation figure:
    Left:  SSM water balance residual — where the water balance requires
           external inflow (β coefficients only, no DEM)
    Right: Ridge hillslope gradient (50 m smoothed DEM) — independent
           topographic evidence consistent with ridge-originating recharge
  Spatial correspondence in the NW forest/ridge zone is consistent with
  ridge-derived water balance residual (CEH14 α computed at runtime).
  Note: there are no natural watercourses on the dune warren; D8 flow
  accumulation was discarded as it does not represent real recharge paths.

Inputs
------
  outputs/01_wells_clean_maod.csv       — per-well monthly maOD heads
  outputs/01_locations.csv              — well coordinates
  outputs/01_well_elevations.csv        — DEM ground elevations
  outputs/03_master_data.csv            — β coefficients, cluster, coordinates
  outputs/01_climate.csv                — monthly P and PET
  data/newborough_dem.tif               — LiDAR DEM (EPSG:27700, 2 m res)
  data/streams.kml                      — SAGA stream network (polygon cells)
  data/Features.kml                     — site feature overlays

Called by
---------
  run_analysis.py  (or standalone: python 20_spatial_figures.py [--preview])

Dependencies
------------
  Standard: numpy, pandas, matplotlib, scipy, rasterio, pyproj
  Spatial:  scikit-image (skimage.morphology, skimage.measure)
            Install: pip install scikit-image

References
----------
  Betson et al. (2002) — K = 6.0 m/day
  Freeman (2008) — 24% canopy interception for C4 Forest
  Curreli et al. (2013) — eco-hydrological thresholds
"""

import argparse
import warnings
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from scipy.interpolate import griddata
from scipy.ndimage import uniform_filter
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path
from pyproj import Transformer
import xml.etree.ElementTree as ET

from utils.paths import (
    make_all_dirs,
    DATA_DIR, DATA_DEM, DATA_KML_FEATURES, DATA_KML_STREAMS,
    DIR_20, OUT_20_HEAD_STREAMS, OUT_20_RESIDUAL_SSM, OUT_20_SLOPE,
    OUT_20_DRAWDOWN,
    INT_WELLS_CLEAN_MAOD, INT_LOCATIONS, INT_WELL_ELEVATIONS,
    INT_MASTER_DATA, INT_CLIMATE, INT_WELLS_EXTENDED,
    INT_PEAR_AUDIT_SITEWIDE, INT_CLUSTER_STATS,
)
from utils.map_utils import load_dem_hillshade
from utils.config import CLUSTER_COLOURS, DRAINAGE_DATUM, FOREST_INTERCEPTION
from utils.data_utils import normalize_well_name

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
XLIM       = (240100, 243900)
YLIM       = (362200, 365000)
GRID_XI    = np.arange(240200, 243800, 50)
GRID_YI    = np.arange(362200, 365000, 50)
KML_NS     = "http://www.opengis.net/kml/2.2"
T_WGS_BNG  = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

# FOREST_INTERCEPTION imported from config.py (Freeman 2008, 0.24).

# Sea boundary anchor constants (matching script 19)
SEA_SOUTH_N      = 362350
SEA_EAST_E       = 243850
SEA_WEST_E       = 239200
SEA_WEST_N_MAX   = 363400
SEA_EAST_N_MAX   = 365000
SEA_ANCHOR_SPACING = 200


def _sea_boundary_points():
    """Zero-head anchor points along sea/estuary boundaries."""
    pts, vals = [], []
    for e in np.arange(SEA_WEST_E, SEA_EAST_E + SEA_ANCHOR_SPACING,
                       SEA_ANCHOR_SPACING):
        pts.append([e, SEA_SOUTH_N]); vals.append(0.0)
    for n in np.arange(SEA_SOUTH_N, SEA_EAST_N_MAX + SEA_ANCHOR_SPACING,
                       SEA_ANCHOR_SPACING):
        pts.append([SEA_EAST_E, n]); vals.append(0.0)
    for n in np.arange(SEA_SOUTH_N, SEA_WEST_N_MAX + SEA_ANCHOR_SPACING,
                       SEA_ANCHOR_SPACING):
        pts.append([SEA_WEST_E, n]); vals.append(0.0)
    return np.array(pts), np.array(vals)


def _site_mask(gx, gy):
    """Rectangular mask clipped to sea boundaries."""
    mask = np.ones(gx.shape, dtype=bool)
    mask[gy < SEA_SOUTH_N] = False
    mask[gx > SEA_EAST_E]  = False
    mask[gx < SEA_WEST_E]  = False
    return mask


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
def load_data():
    """Load all inputs. Returns dict of DataFrames."""
    data = {}

    maod = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    maod.columns = [normalize_well_name(c) for c in maod.columns]
    data["maod"] = maod

    locs = pd.read_csv(INT_LOCATIONS)
    locs["Match_ID"] = locs["Match_ID"].apply(normalize_well_name)
    data["locations"] = locs

    elev = pd.read_csv(INT_WELL_ELEVATIONS)
    elev["Name_norm"] = elev["Name_norm"].apply(normalize_well_name)
    data["elevations"] = elev

    md = pd.read_csv(INT_MASTER_DATA)
    md["Name_Original"] = md["Name_Original"].apply(normalize_well_name)
    data["master"] = md

    clim = pd.read_csv(INT_CLIMATE, parse_dates=["Date"], index_col="Date")
    data["climate"] = clim

    # Extended wells
    if INT_WELLS_EXTENDED.exists():
        ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
        ext.columns = [normalize_well_name(c) for c in ext.columns]
        data["extended"] = ext
    else:
        data["extended"] = None

    if INT_PEAR_AUDIT_SITEWIDE.exists():
        site = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE)
        data["site_audit"] = site
    else:
        data["site_audit"] = None

    return data


def build_well_table(data):
    """
    Build per-well table with coordinates, cluster, mean head, β coefficients,
    and water balance residual. Extended wells are included for spatial
    context (location + cluster) but have no SSM residual.
    """
    maod  = data["maod"]
    locs  = data["locations"]
    elev  = data["elevations"]
    md    = data["master"]
    clim  = data["climate"]
    ext   = data.get("extended")
    site  = data.get("site_audit")

    P_bar   = clim["P_m"].mean()
    PET_bar = clim["PET"].mean()

    wt = locs[["Match_ID", "E", "N"]].rename(
        columns={"Match_ID": "well"}).copy()

    # Merge β coefficients and cluster
    beta = md[["Name_Original", "Cluster",
               "beta_1_recharge", "beta_2_atmospheric_draw",
               "beta_3_drainage"]].rename(columns={
        "Name_Original":           "well",
        "Cluster":                 "cluster",
        "beta_1_recharge":         "beta1",
        "beta_2_atmospheric_draw": "beta2",
        "beta_3_drainage":         "beta3",
    })
    wt = wt.merge(beta, on="well", how="left")

    # DEM ground elevation
    elev_map = dict(zip(elev["Name_norm"], elev["DEM_Ground_Elev"]))
    wt["dem_elev"] = wt["well"].map(elev_map)

    # Pipe-top elevation — needed for displacement formulation
    pipe_map = dict(zip(elev["Name_norm"], elev["Pipe_Top_Elev"]))
    wt["pipe_top"] = wt["well"].map(pipe_map)

    # Mean annual head
    wt["mean_head"] = wt["well"].map(maod.mean(axis=0))

    # Displacement above drainage datum.
    # h_depth = maOD − pipe_top (negative convention, same as 01_wells_clean.csv).
    # h_disp  = DRAINAGE_DATUM + h_depth (positive when water table is above
    #           the drainage base; matches Script 03 SSM fitting formulation).
    wt["mean_depth"] = wt["mean_head"] - wt["pipe_top"]
    wt["h_disp"] = DRAINAGE_DATUM + wt["mean_depth"]

    # Effective P (canopy interception for C4 and C5 — both forested)
    wt["P_eff"] = wt.apply(
        lambda r: P_bar * (1 - FOREST_INTERCEPTION)
        if pd.notna(r.get("cluster")) and int(r["cluster"]) in (4, 5)
        else P_bar, axis=1)

    # SSM water balance residual.
    # At steady state (Δh=0): 0 = β₁·P − β₂·PET − β₃·h_disp
    # Residual = β₂·PET + β₃·h_disp − β₁·P_eff
    # Positive = SSM drainage+ET exceeds recharge → lateral inflow required.
    wt["residual_wb"] = np.where(
        wt["beta1"].notna() & wt["h_disp"].notna(),
        wt["beta2"] * PET_bar + wt["beta3"] * wt["h_disp"]
        - wt["beta1"] * wt["P_eff"],
        np.nan)

    wt["network"] = "Reference"
    wt = wt.dropna(subset=["E", "N", "mean_head"])

    # Extended wells — location + cluster only, no residual
    ext_rows = []
    if ext is not None and site is not None:
        ext_cls = {
            normalize_well_name(r["Well_Normalised"]): int(r["Best_Match_Cluster"])
            for _, r in site[site["Network"] == "Extended"].iterrows()
        }
        pipe_map = dict(zip(elev["Name_norm"], elev["Pipe_Top_Elev"]))
        for wn, cl in ext_cls.items():
            lrow = locs[locs["Match_ID"] == wn]
            if lrow.empty:
                # Try Name column
                name_col = [c for c in locs.columns if c.lower() == "name"]
                if name_col:
                    lrow = locs[locs[name_col[0]].apply(normalize_well_name) == wn]
            if lrow.empty: continue
            pipe_top = pipe_map.get(wn, np.nan)
            if np.isnan(pipe_top): continue
            col = next((c for c in ext.columns if c == wn), None)
            if col is None: continue
            series = pipe_top + ext[col].dropna()
            if len(series) < 5: continue
            ext_rows.append({
                "well": wn, "E": lrow.iloc[0]["E"], "N": lrow.iloc[0]["N"],
                "cluster": cl, "mean_head": series.mean(),
                "residual_wb": np.nan, "network": "Extended",
                "beta1": np.nan, "beta2": np.nan, "beta3": np.nan,
            })

    if ext_rows:
        wt = pd.concat([wt, pd.DataFrame(ext_rows)], ignore_index=True)

    print(f"  Reference wells: {(wt['network']=='Reference').sum()}, "
          f"Extended wells: {(wt['network']=='Extended').sum()}")
    return wt, P_bar, PET_bar


# ─────────────────────────────────────────────────────────────────────────────
# STREAM NETWORK
# ─────────────────────────────────────────────────────────────────────────────
def load_stream_polygons():
    """
    Load SAGA stream cell polygons from streams.kml.
    Returns list of [(e, n), ...] coordinate rings in EPSG:27700,
    or [] if unavailable.  Each element is one polygon's vertex list.
    Rendering these as outlines (matching map_utils.add_kml_features)
    produces a visible stream network; the old centroid-scatter approach
    was too faint to see against the head surface overlay.
    """
    if not DATA_KML_STREAMS.exists():
        return []
    try:
        ns_kml = "http://www.opengis.net/kml/2.2"
        t = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
        tree = ET.parse(str(DATA_KML_STREAMS))
        polys = []
        for pm in tree.getroot().iter(f"{{{ns_kml}}}Placemark"):
            cel = pm.find(f".//{{{ns_kml}}}coordinates")
            if cel is None or not cel.text:
                continue
            ring = []
            for tok in cel.text.strip().split():
                p = tok.split(",")
                if len(p) < 2:
                    continue
                try:
                    e, n = t.transform(float(p[0]), float(p[1]))
                    ring.append((e, n))
                except Exception:
                    continue
            if len(ring) >= 3:
                polys.append(ring)
        print(f"  Stream polygons loaded: {len(polys)}")
        return polys
    except Exception as _e:
        warnings.warn(f"streams.kml load failed: {_e}")
        return []


def draw_stream_network(ax, polys, zorder=6):
    """
    Draw stream cell polygon outlines on ax.  Matches map_utils style:
    dodgerblue edges, no fill, lw=1.8.  Returns a legend handle.
    """
    from matplotlib.collections import PolyCollection
    if not polys:
        return []
    pc = PolyCollection(
        polys, facecolors="none", edgecolors="dodgerblue",
        linewidths=0.8, alpha=0.75, zorder=zorder,
    )
    ax.add_collection(pc)
    return [Line2D([0], [0], color="dodgerblue", lw=1.8,
                   label="DEM-derived flow network")]

# ─────────────────────────────────────────────────────────────────────────────
# KML FEATURES
# ─────────────────────────────────────────────────────────────────────────────
def load_kml_features():
    """
    Parse Features.kml and return list of (name, type, [(x,y)...]) tuples.
    type is 'polygon' or 'line'.
    """
    if not DATA_KML_FEATURES.exists():
        return []
    features = []
    tree = ET.parse(str(DATA_KML_FEATURES))
    for pm in tree.getroot().iter(f"{{{KML_NS}}}Placemark"):
        name_el = pm.find(f"{{{KML_NS}}}name")
        name    = name_el.text.strip() if name_el is not None else ""
        for pg in pm.iter(f"{{{KML_NS}}}Polygon"):
            cel = pg.find(f".//{{{KML_NS}}}coordinates")
            if cel is not None and cel.text:
                pts = _parse_coords(cel.text)
                if pts:
                    features.append((name, "polygon", pts))
        for ls in pm.iter(f"{{{KML_NS}}}LineString"):
            cel = ls.find(f"{{{KML_NS}}}coordinates")
            if cel is not None and cel.text:
                pts = _parse_coords(cel.text)
                if pts:
                    features.append((name, "line", pts))
    return features


def _parse_coords(text):
    pts = []
    for tok in text.strip().split():
        p = tok.split(",")
        if len(p) >= 2:
            try:
                e, n = T_WGS_BNG.transform(float(p[0]), float(p[1]))
                pts.append((e, n))
            except Exception:
                pass
    return pts


def draw_kml_features(ax, features, zorder=5):
    """Draw KML features onto ax. Returns legend handles."""
    handles = {}

    for name, ftype, pts in features:
        if not pts:
            continue
        xs, ys = zip(*pts)
        nl = name.lower()

        if ftype == "polygon":
            if "forest" in nl:
                kw = dict(edgecolor="purple", facecolor="none",
                          lw=1.8, ls="--", zorder=zorder)
                lbl = "Forest boundary"
            elif "llyn" in nl or "rhos" in nl or "lake" in nl:
                kw = dict(edgecolor="dodgerblue", facecolor="dodgerblue",
                          lw=1.2, alpha=0.25, zorder=zorder)
                lbl = "Llyn Rhos Ddu"
            elif "felling" in nl or "experiment" in nl:
                kw = dict(edgecolor="darkorange", facecolor="none",
                          lw=2.0, ls="-.", zorder=zorder)
                lbl = "Clearfell zone"
            else:
                continue
            ax.fill(xs, ys, **kw)
            if lbl not in handles:
                handles[lbl] = mpatches.Patch(
                    facecolor=kw.get("facecolor","none"),
                    edgecolor=kw["edgecolor"], lw=kw["lw"],
                    linestyle=kw.get("ls","-"), label=lbl)

        elif ftype == "line":
            # All line features in Features.kml are paths/tracks — grey dashed
            kw = dict(color="black", lw=0.8, ls="--",
                      alpha=0.7, zorder=zorder)
            lbl = "Paths and roads"
            ax.plot(xs, ys, **kw)
            if lbl not in handles:
                handles[lbl] = Line2D([0],[0], color=kw["color"],
                                      lw=kw["lw"], ls=kw["ls"],
                                      label=lbl)

    return list(handles.values())


# ─────────────────────────────────────────────────────────────────────────────
# SLOPE SURFACE
# ─────────────────────────────────────────────────────────────────────────────
def compute_slope_surface(smooth_m=50):
    """
    Compute hillslope gradient (degrees) from the LiDAR DEM, smoothed to
    suppress individual dune crest noise and reveal broad ridge geometry.

    Parameters
    ----------
    smooth_m : int
        Smoothing window in metres (default 50 m).

    Returns (slope_deg, dem_e, dem_n, res) clipped to study area,
    with values < 1° set to NaN to mask the flat dune plain.
    """
    import rasterio
    with rasterio.open(str(DATA_DEM)) as src:
        dem   = src.read(1).astype(float)
        nd    = src.nodata
        tfm   = src.transform
        res   = abs(tfm.a)
        E0    = tfm.c
        N_top = tfm.f
    if nd is not None:
        dem[dem == nd] = np.nan
    rows, cols = dem.shape
    dem_e = E0   + np.arange(cols) * res
    dem_n = N_top - np.arange(rows) * res

    k = max(1, int(smooth_m / res))
    filled   = np.nan_to_num(dem, nan=0.0)
    smoothed = uniform_filter(filled, size=k)
    smoothed[np.isnan(dem)] = np.nan

    dy, dx = np.gradient(np.nan_to_num(smoothed, nan=0.0), res, res)
    slope_deg = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    slope_deg[np.isnan(dem)] = np.nan

    # Clip to study area and mask flat plain
    clip = ((dem_n[:,None] >= YLIM[0]) & (dem_n[:,None] <= YLIM[1]) &
            (dem_e[None,:] >= XLIM[0]) & (dem_e[None,:] <= XLIM[1]))
    slope_deg[~clip] = np.nan
    slope_deg[slope_deg < 1.0] = np.nan   # flat dune plain → transparent

    return slope_deg, dem_e, dem_n, res


# ─────────────────────────────────────────────────────────────────────────────
# IDW INTERPOLATION
# ─────────────────────────────────────────────────────────────────────────────
def idw_surface(pts, vals, gx, gy, sea_pts=None, sea_vals=None, mask=None):
    """
    IDW to regular grid using scipy griddata (linear).
    Optionally augments with sea boundary anchor points and applies a mask.
    """
    if sea_pts is not None and sea_vals is not None:
        all_pts  = np.vstack([pts, sea_pts])
        all_vals = np.concatenate([vals, sea_vals])
    else:
        all_pts  = pts
        all_vals = vals

    surf = griddata(all_pts, all_vals, (gx, gy), method="linear")

    if mask is not None:
        surf[~mask] = np.nan

    return surf


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 1 — HEAD SURFACE WITH STREAM NETWORK
# ─────────────────────────────────────────────────────────────────────────────
def plot_head_streams(wt, stream_polys, features, dpi=300):
    """
    Figure 1: Mean annual water table (m AOD) with stream cell overlay
    and groundwater flow direction vectors.
    stream_polys: list of polygon vertex lists from load_stream_polygons().
    """
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    mask   = _site_mask(gx, gy)

    # Head surface IDW with sea boundary anchors
    sea_pts, sea_vals = _sea_boundary_points()
    pts  = wt[["E","N"]].values
    vals = wt["mean_head"].values
    surf = idw_surface(pts, vals, gx, gy,
                       sea_pts=sea_pts, sea_vals=sea_vals, mask=mask)

    # Flow vectors from head gradient — suppress on ridge artefacts
    dy, dx = np.gradient(np.nan_to_num(surf, nan=np.nanmean(vals)),
                         GRID_YI[1]-GRID_YI[0], GRID_XI[1]-GRID_XI[0])
    mag = np.sqrt(dx**2 + dy**2)
    mag_thresh = np.nanpercentile(mag[mask], 95)
    arrow_mask = mask & (mag > 0) & (mag < mag_thresh)
    with np.errstate(invalid="ignore"):
        U = np.where(arrow_mask, -dx / mag, np.nan)
        V = np.where(arrow_mask, -dy / mag, np.nan)

    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")

    # Layer 1 — DEM hillshade
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    # Layer 2 — head surface
    vmin, vmax = 2.0, 14.0
    im = ax.pcolormesh(gx, gy, surf, cmap="RdYlBu_r",
                       vmin=vmin, vmax=vmax,
                       shading="auto", alpha=0.55, zorder=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, shrink=0.85)
    cb.set_label("Mean water table (m AOD)", fontsize=9)

    # Head contours at 1 m intervals
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            cs = ax.contour(gx, gy, surf,
                            levels=np.arange(2, 15, 1),
                            colors="black", linewidths=0.6,
                            alpha=0.40, zorder=3)
            ax.clabel(cs, inline=True, fontsize=5,
                      fmt="%.0f m", inline_spacing=2)
        except Exception:
            pass

    # Layer 3 — stream network (polygon outlines, matching map_utils style)
    stream_handles = draw_stream_network(ax, stream_polys, zorder=6)

    # Layer 4 — flow vectors
    skip = 6
    ax.quiver(gx[::skip, ::skip], gy[::skip, ::skip],
              U[::skip, ::skip], V[::skip, ::skip],
              color="white", alpha=0.88, scale=38,
              width=0.004, headwidth=4, zorder=7)

    # Layer 5 — KML features
    kml_handles = draw_kml_features(ax, features, zorder=5)

    # Layer 6 — well symbols
    cluster_handles = {}
    for _, row in wt.iterrows():
        cl  = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        col = CLUSTER_COLOURS.get(cl, "grey")
        ax.scatter(row["E"], row["N"], c=col, s=30,
                   edgecolors="black", lw=0.6, zorder=9)
        if cl not in cluster_handles:
            cluster_handles[cl] = mpatches.Patch(color=col,
                                                  label=f"C{cl}")

    # Legends
    flow_h   = Line2D([0],[0], color="white", lw=0,
                      marker=r"$\rightarrow$", markersize=8,
                      markerfacecolor="white", label="Flow direction")

    l1 = ax.legend(handles=kml_handles + stream_handles + [flow_h],
                   fontsize=7, loc="lower left", framealpha=0.92,
                   title="Site features", title_fontsize=8)
    ax.add_artist(l1)
    ax.legend(handles=list(cluster_handles.values()),
              fontsize=8, loc="lower right",
              title="Cluster", title_fontsize=8)

    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(
        "Mean Annual Water Table (m AOD) — Newborough Warren 2005–2026\n"
        "DEM-derived flow network  |  Groundwater flow direction vectors",
        fontsize=10, fontweight="bold")

    fig.tight_layout()
    fig.savefig(OUT_20_HEAD_STREAMS, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_20_HEAD_STREAMS.name}")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2a — SSM WATER BALANCE RESIDUAL
# ─────────────────────────────────────────────────────────────────────────────
def plot_residual_ssm(wt, features, dpi=300):
    """
    SSM water balance residual — single panel with Darcy flow direction arrows.
    β coefficients only — no DEM physics in the residual surface itself.
    Flow arrows derived independently from mean head gradient.
    """
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    mask   = _site_mask(gx, gy)
    sea_pts, sea_vals = _sea_boundary_points()

    # Residual surface — IDW with sea boundary anchors at zero
    ref      = wt["residual_wb"].notna()
    rpts     = wt.loc[ref, ["E","N"]].values
    rval     = wt.loc[ref, "residual_wb"].values
    resid_surf = idw_surface(rpts, rval, gx, gy,
                             sea_pts=sea_pts,
                             sea_vals=np.zeros(len(sea_vals)),
                             mask=mask)
    vmax_r = np.nanpercentile(np.abs(resid_surf[mask]), 95)
    norm_r = TwoSlopeNorm(vmin=-vmax_r, vcenter=0, vmax=vmax_r)

    # Flow vectors from mean head gradient (independent of residual)
    head_surf = idw_surface(wt[["E","N"]].values, wt["mean_head"].values,
                            gx, gy, sea_pts=sea_pts, sea_vals=sea_vals, mask=mask)
    dy, dx = np.gradient(np.nan_to_num(head_surf, nan=np.nanmean(wt["mean_head"].values)),
                         GRID_YI[1]-GRID_YI[0], GRID_XI[1]-GRID_XI[0])
    U = -dx; V = -dy
    mag = np.sqrt(U**2 + V**2)
    # Suppress arrows where gradient is anomalously large — indicates
    # the IDW surface is interpolating through a ridge with no real saturated
    # zone (produces spurious dome artefacts near Newborough ridge).
    # Threshold = 95th percentile of gradient magnitude within the site mask.
    mag_thresh = np.nanpercentile(mag[mask], 95)
    arrow_mask = mask & (mag > 0) & (mag < mag_thresh) & ~np.isnan(resid_surf)
    with np.errstate(invalid="ignore"):
        U = np.where(arrow_mask, -dx / mag, np.nan)
        V = np.where(arrow_mask, -dy / mag, np.nan)

    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    # Residual surface
    ax.pcolormesh(gx, gy, resid_surf, cmap="RdBu_r",
                  norm=norm_r, shading="auto", alpha=0.52, zorder=2)
    fig.colorbar(
        plt.cm.ScalarMappable(norm=norm_r, cmap="RdBu_r"),
        ax=ax, fraction=0.03, pad=0.02, shrink=0.85
    ).set_label("Water balance residual (m/month)\n+ve = ridge-derived residual",
                fontsize=9)

    # Flow direction arrows (normalised, white)
    skip = 6
    ax.quiver(gx[::skip, ::skip], gy[::skip, ::skip],
              U[::skip, ::skip], V[::skip, ::skip],
              color="white", alpha=0.75, scale=38, width=0.003,
              headwidth=3, headlength=4, zorder=5)

    # Wells coloured by residual value
    ax.scatter(wt.loc[ref,"E"], wt.loc[ref,"N"],
               c=rval, cmap="RdBu_r", norm=norm_r,
               s=55, edgecolors="black", lw=0.6, zorder=9, marker="o")

    # Extended wells — grey diamonds
    ext = wt[wt["network"] == "Extended"]
    if not ext.empty:
        ax.scatter(ext["E"], ext["N"], c="grey", s=30, marker="D",
                   edgecolors="black", lw=0.4, alpha=0.7, zorder=8)

    # Stream network
    stream_polys = load_stream_polygons()
    stream_handles = draw_stream_network(ax, stream_polys, zorder=4)

    kml_h = draw_kml_features(ax, features, zorder=6)
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(
        "SSM Water Balance Residual (m/month) — Newborough Warren 2005–2026\n"
        "(β₂·PET̄ + β₃·h̄_disp − β₁·P̄_eff)  |  β coefficients only  |  "
        "Flow direction arrows from head gradient",
        fontsize=10, fontweight="bold")

    leg_h = kml_h + stream_handles + [
        Line2D([0],[0], marker="o", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=7, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=6, label="Extended well"),
        Line2D([0],[0], color="white", lw=0, marker=r"$\rightarrow$",
               markersize=8, markerfacecolor="white",
               label="Flow direction (head gradient)"),
    ]
    ax.legend(handles=leg_h, fontsize=7, loc="lower left", framealpha=0.9)
    _ceh14_alpha = wt.loc[wt["well"].str.lower() == "ceh14", "residual_wb"]
    _ceh14_str = f"{float(_ceh14_alpha.iloc[0]):+.3f}" if len(_ceh14_alpha) > 0 else "N/A"
    ax.annotate("Residual: SSM β coefficients only — independent of flow arrows.\n"
                "Flow arrows: mean head gradient — independent of β coefficients.\n"
                f"CEH14 water balance residual α = {_ceh14_str} m/month.",
                xy=(0.02, 0.97), xycoords="axes fraction",
                fontsize=7, va="top", color="dimgrey",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85))

    fig.tight_layout()
    fig.savefig(OUT_20_RESIDUAL_SSM, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_20_RESIDUAL_SSM.name}")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2b — RIDGE HILLSLOPE GRADIENT
# ─────────────────────────────────────────────────────────────────────────────
def plot_slope_gradient(wt, features, dpi=300):
    """
    Figure 2b: Ridge hillslope gradient from 50 m smoothed LiDAR DEM.
    DEM only — no SSM coefficients.
    Shows the topographic source of lateral recharge into the dune aquifer.
    """
    print("  Computing hillslope gradient...")
    slope_deg, dem_e, dem_n, res_d = compute_slope_surface(smooth_m=50)
    DEM_E, DEM_N = np.meshgrid(dem_e, dem_n)

    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    im = ax.pcolormesh(DEM_E, DEM_N, slope_deg,
                       cmap="Oranges", vmin=1, vmax=10,
                       shading="auto", alpha=0.80, zorder=2)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, shrink=0.85
                 ).set_label("Hillslope gradient (degrees)\n50 m smoothed DEM",
                              fontsize=9)

    # All wells coloured by cluster
    for _, row in wt.iterrows():
        cl = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        mk = "D" if row.get("network") == "Extended" else "o"
        sz = 30 if mk == "D" else 40
        ax.scatter(row["E"], row["N"],
                   c=CLUSTER_COLOURS.get(cl, "grey"),
                   s=sz, marker=mk,
                   edgecolors="white" if mk == "o" else "black",
                   lw=0.4, zorder=9)

    kml_h = draw_kml_features(ax, features, zorder=5)
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(
        "Ridge Hillslope Gradient — 50 m Smoothed DEM\n"
        "Topographic source of lateral recharge — DEM only  |  "
        "Slopes < 1° masked (flat dune plain)",
        fontsize=10, fontweight="bold")

    cl_handles = [
        mpatches.Patch(color=CLUSTER_COLOURS.get(cl, "grey"), label=f"C{cl}")
        for cl in sorted(CLUSTER_COLOURS.keys())
    ] + [
        Line2D([0],[0], marker="o", color="w", markerfacecolor="grey",
               markeredgecolor="white", markersize=7, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=6, label="Extended well"),
    ]
    ax.legend(handles=kml_h + cl_handles,
              fontsize=7, loc="lower left", framealpha=0.9)
    ax.annotate("DEM gradient (50 m smooth) — no β coefficients used.\n"
                "Slopes < 1° masked (flat dune plain).",
                xy=(0.02, 0.97), xycoords="axes fraction",
                fontsize=7, va="top", color="dimgrey",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85))

    fig.tight_layout()
    fig.savefig(OUT_20_SLOPE, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_20_SLOPE.name}")




# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 3 — FOREST DRAWDOWN PROPAGATION WITH HEAD SURFACE
# ─────────────────────────────────────────────────────────────────────────────
def plot_drawdown_propagation(wt, features, dpi=300):
    """
    Figure 3: Estimated forest drawdown propagation overlaid on mean head
    surface with groundwater flow direction vectors.

    Uses DEM flow-direction-weighted cost-distance (Dijkstra with directional
    and uphill penalties) from the KML forest boundary. The drawdown signal
    h₀·exp(−d/λ) decays with characteristic length λ = √(D/β₃) where
    D = K·b/Sy is the hydraulic diffusivity.

    Layers:
      1. DEM hillshade
      2. IDW mean head surface (RdYlBu_r, semi-transparent)
      3. Drawdown filled contours (Blues, semi-transparent)
      4. Drawdown contour lines with labels
      5. Groundwater flow arrows from head gradient
      6. KML features (forest boundary, lake, felling experiment)
      7. Well symbols coloured by estimated drawdown
      8. Key well annotations with drawdown values
    """
    from heapq import heappush, heappop
    import geopandas as gpd
    import fiona
    import rasterio
    from shapely.geometry import Point, box
    from shapely.prepared import prep

    fiona.drvsupport.supported_drivers["KML"] = "rw"

    # ── Parameters ────────────────────────────────────────────────────────
    K       = 6.0       # m/day (Betson 2002)
    Sy      = 0.25      # (mid-range)
    b       = 5.0       # m saturated thickness
    H0      = 150       # mm forest interception deficit
    BETA3_M = 0.060     # per month (C3 SSM centroid)
    BETA3_D = BETA3_M / 30.0
    lam     = np.sqrt((K * b) / (Sy * BETA3_D))
    OUT_PATH = OUT_20_DRAWDOWN

    print(f"  λ = {lam:.0f} m  (K={K}, Sy={Sy}, b={b}, β₃={BETA3_M}/month)")

    # ── Load DEM and build flow-weighted distance grid ────────────────────
    with rasterio.open(str(DATA_DEM)) as src:
        dem_full = src.read(1).astype(float)
        t = src.transform
        res = abs(t.a)
        if src.nodata is not None:
            dem_full[dem_full == src.nodata] = np.nan

    E_MIN, E_MAX = XLIM[0] + 100, XLIM[1] - 400
    N_MIN, N_MAX = YLIM[0] + 200, YLIM[1] + 200
    col0 = int((E_MIN - t.c) / t.a)
    col1 = int((E_MAX - t.c) / t.a)
    row0 = int((t.f - N_MAX) / abs(t.e))
    row1 = int((t.f - N_MIN) / abs(t.e))
    dem = dem_full[row0:row1, col0:col1]

    ds = 5  # downsample to 10m
    dem_ds = dem[::ds, ::ds]
    nr, nc = dem_ds.shape
    cell = res * ds
    e_arr = t.c + (col0 + np.arange(nc) * ds) * t.a
    n_arr = t.f + (row0 + np.arange(nr) * ds) * t.e

    # DEM gradient for flow direction
    dy, dx = np.gradient(dem_ds, cell)
    flow_E = -dx
    flow_N = -dy
    mag = np.sqrt(flow_E**2 + flow_N**2)
    mag[mag == 0] = 1e-6
    flow_E /= mag
    flow_N /= mag

    # Forest mask from KML
    forest_geom = None
    lake_geom = None
    fell_geom = None
    gdf_kml = gpd.read_file(str(DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
    name_col = gdf_kml["Name"].fillna("").astype(str)
    for idx, row in gdf_kml.iterrows():
        nm = name_col.iloc[idx].lower()
        if "forest" in nm or "boundary" in nm:
            forest_geom = row.geometry
        elif "llyn" in nm or "rhos" in nm:
            lake_geom = row.geometry
        elif "felling" in nm or "fell" in nm:
            fell_geom = row.geometry

    if forest_geom is None:
        print("  [WARNING] Forest polygon not found in KML — skipping drawdown map")
        return

    forest_prep = prep(forest_geom)
    forest_mask = np.zeros((nr, nc), dtype=bool)
    step = 3
    for i in range(0, nr, step):
        for j in range(0, nc, step):
            pt = Point(e_arr[j], n_arr[i])
            if forest_prep.contains(pt):
                r = step // 2 + 1
                forest_mask[max(0, i - r):min(nr, i + r + 1),
                            max(0, j - r):min(nc, j + r + 1)] = True

    # ── Flow-direction-weighted Dijkstra ──────────────────────────────────
    FLOW_WEIGHT    = 0.4
    UPHILL_PENALTY = 2.0
    INF = 1e12

    dist = np.full((nr, nc), INF)
    visited = np.zeros((nr, nc), dtype=bool)
    heap = []

    # Seed forest boundary cells
    for i in range(nr):
        for j in range(nc):
            if forest_mask[i, j]:
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni_, nj_ = i + di, j + dj
                    if 0 <= ni_ < nr and 0 <= nj_ < nc and not forest_mask[ni_, nj_]:
                        dist[i, j] = 0
                        heappush(heap, (0.0, i, j))
                        break
    dist[forest_mask] = 0

    step_geo = {
        (-1,  0): ( 0,  1),   ( 1, 0): ( 0, -1),
        ( 0, -1): (-1,  0),   ( 0, 1): ( 1,  0),
        (-1, -1): (-0.707,  0.707), (-1, 1): ( 0.707,  0.707),
        ( 1, -1): (-0.707, -0.707), ( 1, 1): ( 0.707, -0.707),
    }
    diag = cell * 1.414
    neighbors = [
        (-1, 0, cell), (1, 0, cell), (0, -1, cell), (0, 1, cell),
        (-1, -1, diag), (-1, 1, diag), (1, -1, diag), (1, 1, diag),
    ]

    while heap:
        d, ci, cj = heappop(heap)
        if visited[ci, cj]:
            continue
        visited[ci, cj] = True
        for di, dj, base_dist in neighbors:
            ni_, nj_ = ci + di, cj + dj
            if 0 <= ni_ < nr and 0 <= nj_ < nc and not visited[ni_, nj_]:
                if forest_mask[ni_, nj_]:
                    new_dist = 0.0
                else:
                    se, sn = step_geo[(di, dj)]
                    alignment = se * flow_E[ci, cj] + sn * flow_N[ci, cj]
                    dz = dem_ds[ni_, nj_] - dem_ds[ci, cj]
                    cost = base_dist * (1.0 - FLOW_WEIGHT * alignment) \
                         + max(0, dz) * UPHILL_PENALTY
                    new_dist = d + cost
                if new_dist < dist[ni_, nj_]:
                    dist[ni_, nj_] = new_dist
                    heappush(heap, (new_dist, ni_, nj_))

    dist[forest_mask] = 0
    dd_grid = np.where(forest_mask, H0,
                       np.where(dist < INF, H0 * np.exp(-dist / lam), 0))

    # ── Head surface and GW flow vectors ──────────────────────────────────
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    mask = _site_mask(gx, gy)
    sea_pts, sea_vals = _sea_boundary_points()
    pts  = wt[["E", "N"]].values
    vals = wt["mean_head"].values
    surf = idw_surface(pts, vals, gx, gy,
                       sea_pts=sea_pts, sea_vals=sea_vals, mask=mask)

    hdy, hdx = np.gradient(np.nan_to_num(surf, nan=np.nanmean(vals)),
                           GRID_YI[1] - GRID_YI[0], GRID_XI[1] - GRID_XI[0])
    hmag = np.sqrt(hdx**2 + hdy**2)
    mag_thresh = np.nanpercentile(hmag[mask], 95)
    arrow_ok = mask & (hmag > 0) & (hmag < mag_thresh)
    with np.errstate(invalid="ignore"):
        U = np.where(arrow_ok, -hdx / hmag, np.nan)
        V = np.where(arrow_ok, -hdy / hmag, np.nan)

    # ── Well drawdown values ──────────────────────────────────────────────
    dd_vals = []
    for _, row in wt.iterrows():
        pt = Point(row["E"], row["N"])
        d_euc = forest_geom.exterior.distance(pt)
        inside = forest_prep.contains(pt)
        cj_ = int((row["E"] - e_arr[0]) / cell)
        ci_ = int((n_arr[0] - row["N"]) / cell)
        if inside:
            dd_vals.append(H0)
        elif 0 <= ci_ < nr and 0 <= cj_ < nc and dist[ci_, cj_] < INF:
            dd_vals.append(H0 * np.exp(-dist[ci_, cj_] / lam))
        else:
            dd_vals.append(H0 * np.exp(-d_euc / lam))
    wt = wt.copy()
    wt["dd_mm"] = dd_vals

    # ── Render figure ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")

    # Layer 1 — hillshade
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    # Layer 2 — head surface
    im = ax.pcolormesh(gx, gy, surf, cmap="RdYlBu_r",
                       vmin=2.0, vmax=14.0,
                       shading="auto", alpha=0.45, zorder=2)

    # Layer 3 — drawdown contourf
    E_grid, N_grid = np.meshgrid(e_arr, n_arr)
    dd_levels = [1, 2, 5, 10, 20, 30, 50, 75, 100, 125, 150]
    dd_cmap = plt.cm.Blues
    from matplotlib.colors import BoundaryNorm
    dd_norm = BoundaryNorm(dd_levels, dd_cmap.N, extend="both")
    cf = ax.contourf(E_grid, N_grid, dd_grid, levels=dd_levels,
                     cmap=dd_cmap, norm=dd_norm,
                     alpha=0.38, zorder=3, extend="both")

    # Layer 4 — contour lines
    cs = ax.contour(E_grid, N_grid, dd_grid,
                    levels=[5, 10, 25, 50, 100],
                    colors="midnightblue", linewidths=1.2, alpha=0.8, zorder=4)
    cl = ax.clabel(cs, levels=[5, 10, 25, 100],
                   inline=True, fontsize=10, fmt="%d mm",
                   colors="black", inline_spacing=8)
    for txt in cl:
        txt.set_fontweight("bold")
        txt.set_bbox(dict(facecolor="white", alpha=0.75,
                          edgecolor="none", pad=1.5))

    # Layer 5 — GW flow arrows (white, from head gradient)
    skip = 8
    ax.quiver(gx[::skip, ::skip], gy[::skip, ::skip],
              U[::skip, ::skip], V[::skip, ::skip],
              color="white", alpha=0.85, scale=30,
              width=0.005, headwidth=4, headlength=4, zorder=5)

    # Layer 6 — KML features
    kml_handles = draw_kml_features(ax, features, zorder=6)

    # Layer 7 — wells coloured by drawdown
    cluster_handles = {}
    for _, row in wt.iterrows():
        cl_ = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        col = CLUSTER_COLOURS.get(cl_, "grey")
        ax.scatter(row["E"], row["N"], c=col, s=30,
                   edgecolors="black", lw=0.6, zorder=9)
        if cl_ not in cluster_handles:
            cluster_handles[cl_] = mpatches.Patch(color=col, label=f"C{cl_}")

    # Layer 8 — key well annotations
    key_wells = ["ceh27", "ceh26", "ceh23", "d15", "d5",
                 "ceh10", "ceh24", "ceh5", "ceh6", "l7", "ceh11"]
    for _, w in wt[wt["well"].isin(key_wells)].iterrows():
        dd_str = f"{w['dd_mm']:.0f}" if w["dd_mm"] >= 1 else "<1"
        ax.annotate(
            f"{w['well']} ({dd_str} mm)", (w["E"], w["N"]),
            xytext=(8, 6), textcoords="offset points",
            fontsize=8, color="#222", fontweight="semibold",
            arrowprops=dict(arrowstyle="-", color="#999", lw=0.5),
            zorder=10,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                      alpha=0.8, edgecolor="none"))

    # λ annotation
    ref_e, ref_n = 241805, 364349
    ax.annotate("", xy=(ref_e + lam, ref_n - 100),
                xytext=(ref_e, ref_n - 100),
                arrowprops=dict(arrowstyle="<->", color="#d62728", lw=1.5),
                zorder=10)
    ax.text(ref_e + lam / 2, ref_n - 200, f"λ = {lam:.0f} m",
            ha="center", va="top", fontsize=9, fontweight="bold",
            color="#d62728", zorder=10,
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=2))

    # Colorbars
    cb_dd = fig.colorbar(cf, ax=ax, fraction=0.03, pad=0.06, shrink=0.85)
    cb_dd.set_label("Estimated drawdown Δh (mm)", fontsize=9)
    cb_head = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, shrink=0.85)
    cb_head.set_label("Mean water table (m AOD)", fontsize=9)

    # Legends
    flow_h = Line2D([0], [0], color="white", lw=0,
                    marker=r"$\rightarrow$", markersize=8,
                    markerfacecolor="white", label="GW flow direction")
    l1 = ax.legend(handles=kml_handles + [flow_h],
                   fontsize=7, loc="lower left", framealpha=0.92,
                   title="Site features", title_fontsize=8)
    ax.add_artist(l1)
    ax.legend(handles=list(cluster_handles.values()),
              fontsize=8, loc="lower right",
              title="Cluster", title_fontsize=8, framealpha=0.92)

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.set_title(
        "Forest drawdown propagation with mean head surface\n"
        f"Flow-weighted cost-distance, λ = {lam:.0f} m  |  "
        f"GW flow vectors from IDW head gradient",
        fontsize=10, fontweight="bold", pad=10)

    plt.tight_layout()
    fig.savefig(OUT_PATH, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {OUT_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main(preview=False):
    dpi = 150 if preview else 300
    make_all_dirs()
    DIR_20.mkdir(parents=True, exist_ok=True)

    print("\n=== 20_spatial_figures.py ===")
    print(f"  DPI: {dpi}  ({'preview' if preview else 'publication'})")

    print("\n[1/4] Loading data...")
    data = load_data()

    print("[2/4] Building well table...")
    wt, P_bar, PET_bar = build_well_table(data)
    print(f"  Wells: {len(wt)}  "
          f"(residual available for {wt['residual_wb'].notna().sum()})")
    print(f"  P̄ = {P_bar*1000:.1f} mm/month  "
          f"PET̄ = {PET_bar*1000:.1f} mm/month")

    print("[3/4] Loading stream polygons...")
    stream_polys = load_stream_polygons()

    print("[4/4] Loading KML features...")
    features = load_kml_features()
    print(f"  KML features: {len(features)}")

    print("\nGenerating Figure 1 — Head surface + stream network...")
    plot_head_streams(wt, stream_polys, features, dpi=dpi)

    print("Generating Figure 2a — SSM water balance residual...")
    plot_residual_ssm(wt, features, dpi=dpi)

    print("Generating Figure 2b — Ridge hillslope gradient...")
    plot_slope_gradient(wt, features, dpi=dpi)

    print("Generating Figure 3 — Forest drawdown propagation...")
    plot_drawdown_propagation(wt, features, dpi=dpi)

    print("\n=== Script 20 complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script 20 — Spatial figures for paper Section 4.9")
    parser.add_argument("--preview", action="store_true",
                        help="Render at 150 dpi for quick preview")
    args = parser.parse_args()
    main(preview=args.preview)
