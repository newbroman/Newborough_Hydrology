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
  ridge-derived water balance residual (CEH14 α = +0.222 m/month).
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
    INT_WELLS_CLEAN_MAOD, INT_LOCATIONS, INT_WELL_ELEVATIONS,
    INT_MASTER_DATA, INT_CLIMATE, INT_WELLS_EXTENDED,
    INT_PEAR_AUDIT_SITEWIDE, INT_CLUSTER_STATS,
)
from utils.map_utils import load_dem_hillshade
from utils.config import CLUSTER_COLOURS
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

FOREST_INTERCEPTION = 0.24   # Freeman (2008)

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
               "beta_3_internal_brake"]].rename(columns={
        "Name_Original":           "well",
        "Cluster":                 "cluster",
        "beta_1_recharge":         "beta1",
        "beta_2_atmospheric_draw": "beta2",
        "beta_3_internal_brake":   "beta3",
    })
    wt = wt.merge(beta, on="well", how="left")

    # DEM ground elevation
    elev_map = dict(zip(elev["Name_norm"], elev["DEM_Ground_Elev"]))
    wt["dem_elev"] = wt["well"].map(elev_map)

    # Mean annual head
    wt["mean_head"] = wt["well"].map(maod.mean(axis=0))

    # Effective P (canopy interception for C4)
    wt["P_eff"] = wt.apply(
        lambda r: P_bar * (1 - FOREST_INTERCEPTION)
        if pd.notna(r.get("cluster")) and int(r["cluster"]) == 4
        else P_bar, axis=1)

    # SSM water balance residual
    wt["residual_wb"] = np.where(
        wt["beta1"].notna(),
        wt["beta2"] * PET_bar + wt["beta3"] * wt["mean_head"].abs()
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
def load_stream_cells():
    """
    Load SAGA stream cell centroids directly from streams.kml.
    Returns (es, ns) arrays in EPSG:27700, or ([], []) if unavailable.
    Matches the approach used in map_utils.add_kml_features and script 19
    — does NOT skeletonise or rebuild polylines.
    """
    if not DATA_KML_STREAMS.exists():
        return [], []
    try:
        ns_kml = "http://www.opengis.net/kml/2.2"
        t = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
        tree = ET.parse(str(DATA_KML_STREAMS))
        es, ns = [], []
        for pm in tree.getroot().iter(f"{{{ns_kml}}}Placemark"):
            cel = pm.find(f".//{{{ns_kml}}}coordinates")
            if cel is None or not cel.text:
                continue
            toks = cel.text.strip().split()
            if not toks:
                continue
            p = toks[0].split(",")
            if len(p) < 2:
                continue
            try:
                e, n = t.transform(float(p[0]), float(p[1]))
                es.append(e); ns.append(n)
            except Exception:
                continue
        print(f"  Stream cells loaded: {len(es)}")
        return es, ns
    except Exception as _e:
        warnings.warn(f"streams.kml load failed: {_e}")
        return [], []

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
def plot_head_streams(wt, stream_cells, features, dpi=300):
    """
    Figure 1: Mean annual water table (m AOD) with stream cell overlay
    and groundwater flow direction vectors.
    stream_cells: (es, ns) tuple from load_stream_cells().
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

    # Layer 3 — stream cells (direct from streams.kml, matching all other maps)
    es_s, ns_s = stream_cells
    if es_s:
        ax.scatter(es_s, ns_s, c="#5B8DB8", s=0.5,
                   alpha=0.45, linewidths=0, marker="s", zorder=6)

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
    stream_h = Line2D([0],[0], color="#5B8DB8", lw=1.5,
                      label="DEM-derived flow network")
    flow_h   = Line2D([0],[0], color="white", lw=0,
                      marker=r"$\rightarrow$", markersize=8,
                      markerfacecolor="white", label="Flow direction")

    l1 = ax.legend(handles=kml_handles + [stream_h, flow_h],
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

    # Stream cells
    _es_s, _ns_s = load_stream_cells()
    if _es_s:
        ax.scatter(_es_s, _ns_s, c="#5B8DB8", s=0.5,
                   alpha=0.45, linewidths=0, marker="s", zorder=4)

    kml_h = draw_kml_features(ax, features, zorder=6)
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(
        "SSM Water Balance Residual (m/month) — Newborough Warren 2005–2026\n"
        "(β₂·PET̄ + β₃·|h̄| − β₁·P̄_eff)  |  β coefficients only  |  "
        "Flow direction arrows from head gradient",
        fontsize=10, fontweight="bold")

    leg_h = kml_h + [
        Line2D([0],[0], marker="o", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=7, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=6, label="Extended well"),
        Line2D([0],[0], color="white", lw=0, marker=r"$\rightarrow$",
               markersize=8, markerfacecolor="white",
               label="Flow direction (head gradient)"),
    ]
    ax.legend(handles=leg_h, fontsize=7, loc="lower left", framealpha=0.9)
    ax.annotate("Residual: SSM β coefficients only — independent of flow arrows.\n"
                "Flow arrows: mean head gradient — independent of β coefficients.\n"
                "CEH14 water balance residual α = +0.222 m/month.",
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

    print("[3/4] Loading stream cells...")
    stream_cells = load_stream_cells()

    print("[4/4] Loading KML features...")
    features = load_kml_features()
    print(f"  KML features: {len(features)}")

    print("\nGenerating Figure 1 — Head surface + stream network...")
    plot_head_streams(wt, stream_cells, features, dpi=dpi)

    print("Generating Figure 2a — SSM water balance residual...")
    plot_residual_ssm(wt, features, dpi=dpi)

    print("Generating Figure 2b — Ridge hillslope gradient...")
    plot_slope_gradient(wt, features, dpi=dpi)

    print("\n=== Script 20 complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script 20 — Spatial figures for paper Section 4.9")
    parser.add_argument("--preview", action="store_true",
                        help="Render at 150 dpi for quick preview")
    args = parser.parse_args()
    main(preview=args.preview)
