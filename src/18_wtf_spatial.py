"""
18_wtf_spatial.py
=================
Water Table Fluctuation (WTF) Method — Individual Well Analysis and Spatial Mapping
Newborough Warren Coastal Sand Dune Aquifer, 2005–2026

Outputs:
    18_wtf_01_well_sy_estimates.csv      — reference well Sy table (Table S1)
    18_wtf_02_spatial_sy_map.png         — point map (plot_metric_map, as script 04)
    18_wtf_03_sy_contour.png             — IDW contour surface, reference wells only
    18_wtf_04_sy_contour_extended.png    — IDW contour surface, reference + extended wells
    18_wtf_05_drainage_timescale_map.png — IDW contour of τ = Sy / β₃ (months)
    18_wtf_05_drainage_timescale.csv     — per-well τ values with Sy, β₃, cluster
    18_wtf_06_aquifer_diagnostic_synthesis.png — τ vs ΔNSE scatter sized by Sy

Notes:
    - Forest clusters (C4 Main Forest, C5 Coastal Forest) receive interception
      correction: R_eff = (1-0.24)*P - PET. Interception fraction measured at
      C5 and applied across both forested clusters.
    - Under the k=5 partition all clusters are analytically usable; the old
      EXCLUDE_CLUSTERS list (tidal / lake) is empty.
    - Extended wells use Best_Match_Cluster from 06_pear_membership_audit_sitewide.csv
    - Extended wells shown as open symbols on extended contour map
    - Forest contour values carry additional uncertainty (Freeman, 2008)

References:
    Healy, R.W. and Cook, P.G. (2002) Hydrogeology Journal 10, 91-109.
    Freeman, S. (2008) Hydrological impact of Corsican pine at Newborough Warren.
"""

__version__ = "1.0.1"  # Hollingham (2026) — 2026-05-17
# 1.0.1 — Doc-sweep S.12: updated stale "C4 Forest values corrected" plot
#         title to "Forest cluster values (C4, C5) corrected" (S12-A,
#         matches live code and Script 18 docstring line 17 — interception
#         correction applies to both forest clusters under the k=5
#         partition); added __version__ constant (S12-B).  Patch — no
#         functional change.
# 1.0.x — Initial.

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

from utils.paths import (
    make_all_dirs, OUT_DIR, DIR_18,
    INT_WELLS_CLEAN, INT_CLIMATE, INT_LOCATIONS, INT_CLUSTER_STATS,
    INT_MASTER_DATA, INT_WELL_ELEVATIONS, INT_WELLS_EXTENDED,
    INT_PEAR_AUDIT_SITEWIDE, DATA_DIR, INT_LCSC_MODEL_STATS,
    OUT_18_WELL_SY_TABLE, OUT_18_SY_MAP, OUT_18_SY_CONTOUR,
    OUT_18_SY_CONTOUR_EXT, INT_WTF_WELL_SY,
    OUT_18_DRAINAGE_TIMESCALE, OUT_18_DRAINAGE_TIMESCALE_CSV,
    OUT_18_AQUIFER_SYNTHESIS,
)
from utils.config import (
    CLUSTER_LABELS, CLUSTER_COLOURS, CLUSTER_MARKERS,
    FOREST_INTERCEPTION, FOREST_CIDS,
    BW_MODE, get_cmap,
)
make_all_dirs()

# ── Site boundary constants (shared with script 19) ───────────────────────────
SEA_SOUTH_N = 362350   # m OSGB36 — southern shoreline Northing
SEA_EAST_E  = 243850   # m OSGB36 — eastern (Menai Strait) Easting
SEA_WEST_E  = 239200   # m OSGB36 — western estuary Easting


def make_site_mask(grid_x, grid_y):
    """
    Boolean mask for the IDW interpolation domain, clipped to the actual
    site boundary.

    Primary: pure XML + pyproj + shapely parse of site_boundary.kml
    (falls back to streams.kml). No fiona/KML driver needed.
    Fallback: rectangular clip to the three sea-boundary lines.
    """
    import warnings
    flat = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    _bnd_path = DATA_DIR / "site_boundary.kml"
    if not _bnd_path.exists():
        _bnd_path = DATA_DIR / "streams.kml"
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

    # Fallback: rectangular clip to sea boundaries
    mask = np.ones(grid_x.shape, dtype=bool)
    mask[grid_y < SEA_SOUTH_N] = False
    mask[grid_x > SEA_EAST_E]  = False
    mask[grid_x < SEA_WEST_E]  = False
    return mask


# Wells excluded from contour interpolation — physically outside sand aquifer
# CEH12 sits on the bedrock ridge in a forested area; its WTF Sy reflects
# fractured rock response rather than dune sand storage and must not be
# interpolated onto the sand aquifer Sy surface.
# Wells excluded from contour interpolation — physically anomalous settings
# CEH12: sits on the bedrock ridge in a forested area; WTF Sy reflects
#         fractured rock response rather than dune sand storage.
# CEH15: forest well located in a low-lying slack within the plantation;
#         slack topography dominates water table dynamics, WTF underestimates
#         Sy relative to upland forest sand. Interception correction also
#         unreliable for a partially-open slack canopy setting.
RIDGE_EXCLUDE = ['ceh12', 'ceh15']
# Additional exclusion for τ = Sy / β₃ map only:
# CEH13: extremely low β₃ (0.002) gives τ ≈ 124 months — a >10× outlier
#         that dominates the colourbar and masks meaningful spatial variation
#         in the 2–15 month range. The near-zero β₃ likely reflects minimal
#         hydraulic gradient rather than genuine aquifer sluggishness.
TAU_EXCLUDE = ['ceh13']
# FOREST_INTERCEPTION and FOREST_CIDS imported from config.py.
EXCLUDE_CLUSTERS    = []         # under k=5 all clusters are analytically usable
MIN_RISE_M          = 0.005      # m
MIN_NET_RECH        = 0.010      # m
MIN_EVENTS          = 15         # minimum qualifying events for confidence flag

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'axes.labelsize': 11, 'axes.titlesize': 11,
    'xtick.labelsize': 9,  'ytick.labelsize': 9,
})


def load_well_data(out_root):
    """Load individual well time series, climate, locations and cluster assignments."""
    wells_df   = pd.read_csv(INT_WELLS_CLEAN,
                              index_col=0, parse_dates=True)
    climate    = pd.read_csv(INT_CLIMATE, parse_dates=["Date"])
    cluster_df = pd.read_csv(INT_CLUSTER_STATS)
    locations  = pd.read_csv(INT_LOCATIONS)

    climate    = climate.set_index("Date")
    wells_df.index = pd.to_datetime(wells_df.index)

    cluster_df["norm"] = cluster_df["Match_ID"].str.lower().str.strip()
    locations["norm"]  = locations["Match_ID"].str.lower().str.strip()

    return wells_df, climate, cluster_df, locations


def wtf_individual_wells(wells_df, climate, cluster_df, locations):
    """
    Event-based WTF Sy for every individual reference well.
    Returns DataFrame sorted by cluster then well name.
    """
    rows = []

    for well in wells_df.columns:
        well_norm = well.lower().strip().replace(" ", "")

        # Cluster lookup
        match = cluster_df[cluster_df["norm"].str.replace(" ","") == well_norm]
        if match.empty:
            continue
        cluster = int(match["Cluster"].iloc[0])
        if cluster in EXCLUDE_CLUSTERS:
            continue

        # Align with climate
        merged = wells_df[[well]].join(climate[["P_m","PET"]], how="inner").dropna()
        if len(merged) < 24:
            continue

        merged = merged.sort_index()
        merged["dh"] = merged[well].diff()

        # Interception correction for Forest clusters
        if cluster in FOREST_CIDS:
            merged["net_R"] = merged["P_m"] * (1 - FOREST_INTERCEPTION) - merged["PET"]
            corrected = True
        else:
            merged["net_R"] = merged["P_m"] - merged["PET"]
            corrected = False

        # Event selection
        events = merged[
            (merged["net_R"] > MIN_NET_RECH) &
            (merged["dh"]    > MIN_RISE_M)
        ].copy()
        events["sy_i"] = events["net_R"] / events["dh"]
        events = events[(events["sy_i"] > 0.01) & (events["sy_i"] < 0.50)]

        n = len(events)
        if n < 5:
            continue

        # Location lookup
        loc = locations[locations["norm"].str.replace(" ","") == well_norm]
        if loc.empty:
            continue

        rows.append({
            "Well":      well,
            "Cluster":   cluster,
            "Easting":   float(loc["E"].iloc[0]),
            "Northing":  float(loc["N"].iloc[0]),
            "Sy_median": round(events["sy_i"].median(), 4),
            "Sy_Q25":    round(events["sy_i"].quantile(0.25), 4),
            "Sy_Q75":    round(events["sy_i"].quantile(0.75), 4),
            "n_events":  n,
            "Corrected": corrected,
            "Confidence": "High" if n >= MIN_EVENTS else "Low",
        })

    df = pd.DataFrame(rows).sort_values(["Cluster","Well"]).reset_index(drop=True)
    print(f"  {len(df)} wells processed  "
          f"({len(df[df['Confidence']=='High'])} high confidence)")
    return df


def plot_spatial_map(well_results, out_path):
    """
    Point map of well-level WTF Sy using plot_metric_map from map_utils.
    Identical infrastructure to script 04 — DEM/OSM base, KML overlays,
    cluster markers.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

    data_dir = DATA_DIR

    try:
        from utils.map_utils import plot_metric_map
    except ImportError:
        print("  [WARNING] map_utils not available — skipping point map")
        return

    map_df = well_results.rename(columns={
        "Cluster": "Cluster_ID",
        "Sy_median": "WTF_Sy_median",
    })[["Easting","Northing","Cluster_ID","WTF_Sy_median"]].copy()

    plot_metric_map(
        map_df      = map_df,
        value_col   = "WTF_Sy_median",
        title       = ("WTF Specific Yield (event median) — Newborough Warren 2005–2026\n"
                       "Forest cluster values (C4, C5) corrected for 24% canopy interception "
                       "(Freeman, 2008); spatial canopy variability means "
                       "Forest estimates are approximate"),
        output_path = out_path,
        cmap        = get_cmap("RdYlGn"),
        data_dir    = data_dir,
        vmin        = 0.10,
        vmax        = 0.40,
    )
    print(f"  Point map saved → {out_path.name}")


def plot_contour_map(well_results, out_path):
    """
    IDW-interpolated contour surface of WTF Sy across the site.
    Greyscale hillshade DEM background (load_dem_hillshade) with semi-transparent
    Sy surface overlaid. Interpolation clipped to fixed study area bounds
    (E 240200–243800, N 362200–365800) matching the rest of the pipeline.
    Forest cluster wells hatched to signal interception uncertainty.
    """
    from matplotlib.lines import Line2D
    from utils.map_utils import load_dem_hillshade, add_kml_features

    # ── Study area bounds (consistent with add_idw_surface defaults) ──────────
    XI_MIN, XI_MAX = 240200, 243800
    YI_MIN, YI_MAX = 362200, 365800
    GRID_STEP = 50

    x  = well_results["Easting"].values
    y  = well_results["Northing"].values
    sy = well_results["Sy_median"].values

    xi = np.arange(XI_MIN, XI_MAX, GRID_STEP)
    yi = np.arange(YI_MIN, YI_MAX, GRID_STEP)
    Xi, Yi = np.meshgrid(xi, yi)

    def idw(xq, yq, xs, ys, vs, power=2):
        dist = np.sqrt((xq - xs[:,None,None])**2 + (yq - ys[:,None,None])**2)
        dist = np.where(dist == 0, 1e-10, dist)
        w = 1.0 / dist**power
        return np.sum(w * vs[:,None,None], axis=0) / np.sum(w, axis=0)

    Zi = idw(Xi, Yi, x, y, sy)
    site_mask = make_site_mask(Xi, Yi)
    Zi_masked = np.ma.masked_where(~site_mask | np.isnan(Zi), Zi)

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white", dpi=200)
    ax.set_xlim(XI_MIN, XI_MAX)
    ax.set_ylim(YI_MIN, YI_MAX)
    ax.set_aspect("equal")

    # Layer 1 — greyscale hillshade DEM
    _, dem_loaded, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=0.35, vert_exag=3.0, zorder=1)
    if not dem_loaded:
        print("  [WARNING] DEM hillshade unavailable — plain background used")
        ax.set_facecolor("#EEF2F6")

    # Layer 2 — semi-transparent Sy surface
    cf = ax.contourf(Xi, Yi, Zi_masked, levels=20,
                     cmap=get_cmap("RdYlGn"), vmin=0.10, vmax=0.40,
                     alpha=0.65, zorder=2)
    cl = ax.contour(Xi, Yi, Zi_masked, levels=10,
                    colors="black" if BW_MODE else "white", linewidths=0.6, alpha=0.6, zorder=3)
    ax.clabel(cl, fmt="%.2f", fontsize=7, colors="black" if BW_MODE else "white")

    # Layer 3 — KML site features
    site_feature_handles = []
    try:
        site_feature_handles = add_kml_features(ax, DATA_DIR)
        print(f"  KML features added ({len(site_feature_handles)} layers)")
    except Exception as e:
        print(f"  [WARNING] KML features failed: {e}")

    # Colourbar
    cbar = fig.colorbar(cf, ax=ax, fraction=0.025, pad=0.01, shrink=0.75)
    cbar.set_label("Specific yield Sy  (WTF event median, IDW interpolation)",
                   fontsize=10, labelpad=10)

    # CLUSTER_COLOURS / CLUSTER_LABELS / CLUSTER_MARKERS imported from utils.config.

    cluster_handles = []
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = well_results[well_results["Cluster"] == cid]
        if sub.empty:
            continue
        sizes = 60 + (sub["n_events"] - 20) * 1.2
        hatch = "//" if cid in FOREST_CIDS else None
        ax.scatter(sub["Easting"], sub["Northing"],
                   c=CLUSTER_COLOURS[cid],
                   s=sizes, marker=CLUSTER_MARKERS[cid],
                   edgecolors="black", linewidths=0.8,
                   alpha=0.92, zorder=5, hatch=hatch)
        cluster_handles.append(Line2D(
            [0],[0], marker=CLUSTER_MARKERS[cid], color="w",
            markerfacecolor=CLUSTER_COLOURS[cid],
            markeredgecolor="black", markersize=10,
            label=CLUSTER_LABELS[cid]))

    # Sy value labels
    for _, row in well_results.iterrows():
        ax.annotate(f"{row['Sy_median']:.2f}",
                    (row["Easting"], row["Northing"]),
                    xytext=(4, 4), textcoords="offset points",
                    fontsize=6, color="#111111", zorder=6)

    # Legends
    cluster_leg = ax.legend(
        handles=cluster_handles, loc="lower left",
        title="Cluster  (// = interception correction applied)",
        fontsize=8, framealpha=0.95, edgecolor="#CCCCCC")
    ax.add_artist(cluster_leg)
    if site_feature_handles:
        ax.legend(handles=site_feature_handles, title="Site Features",
                  loc="upper right", fontsize=8,
                  framealpha=0.95, edgecolor="#CCCCCC")

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=10)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=10)
    ax.set_title(
        "Interpolated WTF Specific Yield Surface — Newborough Warren 2005–2026\n"
        "IDW interpolation (power=2) of event-based median Sy per well  |  "
        "Greyscale hillshade DEM + KML overlays\n"
        "Forest cluster values (C4, C5) interception-corrected (Freeman, 2008) — "
        "contours in Forest zone are approximate",
        fontsize=9, fontweight="bold", pad=10)

    ax.tick_params(labelsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Contour map saved → {out_path.name}")


def wtf_extended_wells(climate, locations, out_root):
    """
    Apply event-based WTF Sy to the 20 extended network wells.
    Cluster assignments from 06_pear_membership_audit_sitewide.csv
    (Best_Match_Cluster column). Interception correction applied to C4 wells.
    Returns DataFrame in same format as wtf_individual_wells(), with
    Network='Extended' column added.
    """
    try:
        wells_ext  = pd.read_csv(INT_WELLS_EXTENDED,
                                  index_col=0, parse_dates=True)
        membership = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE)
    except Exception as e:
        print(f"  [WARNING] Could not load extended well data: {e}")
        return None

    wells_ext.index = pd.to_datetime(wells_ext.index)
    membership['norm'] = (membership['Well_Normalised']
                          .str.lower().str.strip().str.replace(' ',''))
    locations_copy = locations.copy()
    locations_copy['norm'] = (locations_copy['Match_ID']
                               .str.lower().str.strip().str.replace(' ',''))

    # Keep only extended wells
    ext_only = membership[membership['Network'] == 'Extended'].copy()

    rows = []
    for well in wells_ext.columns:
        well_norm = well.lower().strip().replace(' ','')

        # Cluster from sitewide membership audit
        match = ext_only[ext_only['norm'] == well_norm]
        if match.empty:
            continue
        cluster = int(match['Best_Match_Cluster'].iloc[0])
        if cluster in EXCLUDE_CLUSTERS:
            continue

        # Align with climate
        merged = wells_ext[[well]].join(
            climate[['P_m','PET']], how='inner').dropna()
        if len(merged) < 24:
            continue

        merged = merged.sort_index()
        merged['dh'] = merged[well].diff()

        if cluster in FOREST_CIDS:
            merged['net_R'] = merged['P_m'] * (1 - FOREST_INTERCEPTION) - merged['PET']
            corrected = True
        else:
            merged['net_R'] = merged['P_m'] - merged['PET']
            corrected = False

        events = merged[
            (merged['net_R'] > MIN_NET_RECH) &
            (merged['dh']    > MIN_RISE_M)
        ].copy()
        events['sy_i'] = events['net_R'] / events['dh']
        events = events[(events['sy_i'] > 0.01) & (events['sy_i'] < 0.50)]

        n = len(events)
        if n < 5:
            continue

        loc = locations_copy[locations_copy['norm'] == well_norm]
        if loc.empty:
            continue

        rows.append({
            'Well':       well,
            'Cluster':    cluster,
            'Network':    'Extended',
            'Easting':    float(loc['E'].iloc[0]),
            'Northing':   float(loc['N'].iloc[0]),
            'Sy_median':  round(events['sy_i'].median(), 4),
            'Sy_Q25':     round(events['sy_i'].quantile(0.25), 4),
            'Sy_Q75':     round(events['sy_i'].quantile(0.75), 4),
            'n_events':   n,
            'Corrected':  corrected,
            'Confidence': 'High' if n >= MIN_EVENTS else 'Low',
            'Ridge_Flag': well_norm in RIDGE_EXCLUDE,
        })

    if not rows:
        print("  [WARNING] No extended well results produced")
        return None

    df = pd.DataFrame(rows).sort_values(['Cluster','Well']).reset_index(drop=True)
    print(f"  {len(df)} extended wells processed  "
          f"({len(df[df['Confidence']=='High'])} high confidence)")
    return df


def plot_contour_map_extended(ref_results, ext_results, out_path):
    """
    IDW contour surface using reference + extended wells combined.
    Greyscale hillshade DEM background; interpolation clipped to fixed study
    area bounds (E 240200–243800, N 362200–365800).
    Extended wells shown as open symbols to distinguish from reference wells.
    """
    from matplotlib.lines import Line2D
    from utils.map_utils import load_dem_hillshade, add_kml_features

    # ── Study area bounds ─────────────────────────────────────────────────────
    XI_MIN, XI_MAX = 240200, 243800
    YI_MIN, YI_MAX = 362200, 365800
    GRID_STEP = 50

    # Add Network column to ref_results if missing
    ref = ref_results.copy()
    if 'Network' not in ref.columns:
        ref['Network'] = 'Reference'
    if 'Ridge_Flag' not in ref.columns:
        ref['Ridge_Flag'] = False

    ext = ext_results.copy()
    if 'Ridge_Flag' not in ext.columns:
        ext['Ridge_Flag'] = False

    ext_interp = ext[~ext['Ridge_Flag']].copy()
    ext_ridge  = ext[ext['Ridge_Flag']].copy()

    combined = pd.concat([ref, ext_interp], ignore_index=True)

    x  = combined['Easting'].values
    y  = combined['Northing'].values
    sy = combined['Sy_median'].values

    xi = np.arange(XI_MIN, XI_MAX, GRID_STEP)
    yi = np.arange(YI_MIN, YI_MAX, GRID_STEP)
    Xi, Yi = np.meshgrid(xi, yi)

    def idw(xq, yq, xs, ys, vs, power=2):
        dist = np.sqrt((xq - xs[:,None,None])**2 + (yq - ys[:,None,None])**2)
        dist = np.where(dist == 0, 1e-10, dist)
        w = 1.0 / dist**power
        return np.sum(w * vs[:,None,None], axis=0) / np.sum(w, axis=0)

    Zi = idw(Xi, Yi, x, y, sy)
    site_mask = make_site_mask(Xi, Yi)
    Zi_masked = np.ma.masked_where(~site_mask | np.isnan(Zi), Zi)

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 10), facecolor='white', dpi=200)
    ax.set_xlim(XI_MIN, XI_MAX)
    ax.set_ylim(YI_MIN, YI_MAX)
    ax.set_aspect('equal')

    # Layer 1 — greyscale hillshade DEM
    _, dem_loaded, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=0.35, vert_exag=3.0, zorder=1)
    if not dem_loaded:
        print("  [WARNING] DEM hillshade unavailable — plain background used")
        ax.set_facecolor('#EEF2F6')

    # Layer 2 — semi-transparent Sy surface
    cf = ax.contourf(Xi, Yi, Zi_masked, levels=20,
                     cmap=get_cmap('RdYlGn'), vmin=0.10, vmax=0.40,
                     alpha=0.65, zorder=2)
    cl = ax.contour(Xi, Yi, Zi_masked, levels=10,
                    colors='white', linewidths=0.6, alpha=0.6, zorder=3)
    ax.clabel(cl, fmt='%.2f', fontsize=7, colors='white')

    # Layer 3 — KML site features
    site_feature_handles = []
    try:
        site_feature_handles = add_kml_features(ax, DATA_DIR)
        print(f"  KML features added ({len(site_feature_handles)} layers)")
    except Exception as e:
        print(f"  [WARNING] KML features failed: {e}")

    cbar = fig.colorbar(cf, ax=ax, fraction=0.025, pad=0.01, shrink=0.75)
    cbar.set_label('Specific yield Sy  (WTF event median, IDW interpolation)',
                   fontsize=10, labelpad=10)

    # CLUSTER_COLOURS / CLUSTER_LABELS / CLUSTER_MARKERS imported from utils.config.

    cluster_handles = []

    # Reference wells — filled
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = ref[ref['Cluster'] == cid]
        if sub.empty:
            continue
        sizes = 60 + (sub['n_events'] - 20) * 1.2
        hatch = '//' if cid in FOREST_CIDS else None
        ax.scatter(sub['Easting'], sub['Northing'],
                   c=CLUSTER_COLOURS[cid], s=sizes,
                   marker=CLUSTER_MARKERS[cid],
                   edgecolors='black', linewidths=0.8,
                   alpha=0.92, zorder=5, hatch=hatch)
        for _, row in sub.iterrows():
            ax.annotate(f"{row['Sy_median']:.2f}",
                        (row['Easting'], row['Northing']),
                        xytext=(4,4), textcoords='offset points',
                        fontsize=6, color='#111111', zorder=6)
        cluster_handles.append(Line2D(
            [0],[0], marker=CLUSTER_MARKERS[cid], color='w',
            markerfacecolor=CLUSTER_COLOURS[cid],
            markeredgecolor='black', markersize=10,
            label=CLUSTER_LABELS[cid]))

    # Extended wells — open symbols (non-ridge only)
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = ext_interp[ext_interp['Cluster'] == cid]
        if sub.empty:
            continue
        lc = sub['Confidence'].map({'High': 1.8, 'Low': 1.2})
        ax.scatter(sub['Easting'], sub['Northing'],
                   facecolors='none',
                   edgecolors=CLUSTER_COLOURS[cid],
                   s=110, marker=CLUSTER_MARKERS[cid],
                   linewidths=lc, alpha=0.90, zorder=5)
        for _, row in sub.iterrows():
            ax.annotate(f"{row['Sy_median']:.2f}",
                        (row['Easting'], row['Northing']),
                        xytext=(4,4), textcoords='offset points',
                        fontsize=6, color='#555555',
                        style='italic', zorder=6)

    ext_handles = [
        Line2D([0],[0], marker='o', color='w',
               markerfacecolor='none', markeredgecolor='#555555',
               markeredgewidth=1.8, markersize=10,
               label='Extended wells (open = high conf., thin = low conf.)'),
    ]

    # Ridge wells — shown as flagged crosses, excluded from interpolation
    if not ext_ridge.empty:
        ax.scatter(ext_ridge['Easting'], ext_ridge['Northing'],
                   marker='x', c='red', s=120,
                   linewidths=2.0, zorder=7)
        reasons = {
            'ceh12': 'ridge/bedrock',
            'ceh15': 'forest slack floor',
        }
        for _, row in ext_ridge.iterrows():
            reason = reasons.get(row['Well'].lower().strip(), 'excluded')
            ax.annotate(f"{row['Well'].upper()}\n{row['Sy_median']:.2f} ({reason})",
                        (row['Easting'], row['Northing']),
                        xytext=(6, 6), textcoords='offset points',
                        fontsize=6, color='red', style='italic', zorder=8)
        ext_handles.append(
            Line2D([0],[0], marker='x', color='red', markersize=9,
                   linewidth=2, linestyle='none',
                   label='Excluded from interpolation\n(ridge/bedrock or slack-floor setting)'))

    cluster_leg = ax.legend(
        handles=cluster_handles + ext_handles,
        loc='lower left',
        title='Cluster  (// = interception correction applied)',
        fontsize=8, framealpha=0.95, edgecolor='#CCCCCC')
    ax.add_artist(cluster_leg)

    if site_feature_handles:
        ax.legend(handles=site_feature_handles, title='Site Features',
                  loc='upper right', fontsize=8,
                  framealpha=0.95, edgecolor='#CCCCCC')

    ax.set_xlabel('Easting (m, OSGB36)', fontsize=10)
    ax.set_ylabel('Northing (m, OSGB36)', fontsize=10)
    ax.set_title(
        'Interpolated WTF Specific Yield Surface — Reference + Extended Network\n'
        'Newborough Warren 2005–2026  |  IDW interpolation (power=2)  |  '
        'Greyscale hillshade DEM + KML overlays\n'
        'Filled markers = reference wells; open markers = extended wells  |  '
        'Forest clusters (C4, C5) interception-corrected (Freeman, 2008)',
        fontsize=9, fontweight='bold', pad=10)

    ax.tick_params(labelsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Extended contour map saved → {out_path.name}")


def compute_drainage_timescale(well_results):
    """
    Compute per-well characteristic drainage timescale τ = Sy / β₃ (months).

    Joins WTF-derived Sy (from well_results) with SSM β₃ (from 03_master_data.csv).
    Excludes:
      - CEH12 (bedrock ridge — Sy not representative of sand aquifer)
      - CEH15 (forest slack floor — anomalous Sy)
      - CEH14 (negative β₃ — τ undefined)
      - CEH13 (near-zero β₃ — τ ≈ 124 months, >10× outlier distorting colourbar)
      - Any well where β₃ ≤ 0

    Returns
    -------
    tau_df : pd.DataFrame
        Columns: Well, Cluster, Easting, Northing, Sy_median, beta_3, tau_months,
                 n_events, Corrected, Confidence, Excluded, Exclude_Reason
    """
    # Load β₃ from master data
    master = pd.read_csv(INT_MASTER_DATA)
    master["well_norm"] = master["Name_Original"].str.lower().str.strip()

    # Build normalised key on well_results
    wr = well_results.copy()
    wr["well_norm"] = wr["Well"].str.lower().str.strip()

    # Merge on normalised well name
    merged = wr.merge(
        master[["well_norm", "beta_3_drainage"]],
        on="well_norm", how="inner"
    )

    # Flag exclusions
    merged["Excluded"] = False
    merged["Exclude_Reason"] = ""

    ridge_norms = [w.lower().strip() for w in RIDGE_EXCLUDE]
    ridge_mask = merged["well_norm"].isin(ridge_norms)
    merged.loc[ridge_mask, "Excluded"] = True
    merged.loc[ridge_mask, "Exclude_Reason"] = "ridge/bedrock or slack-floor setting"

    neg_b3 = merged["beta_3_drainage"] <= 0
    merged.loc[neg_b3 & ~merged["Excluded"], "Excluded"] = True
    merged.loc[neg_b3 & ~ridge_mask, "Exclude_Reason"] = "negative β₃"

    tau_norms = [w.lower().strip() for w in TAU_EXCLUDE]
    tau_mask = merged["well_norm"].isin(tau_norms) & ~merged["Excluded"]
    merged.loc[tau_mask, "Excluded"] = True
    merged.loc[tau_mask, "Exclude_Reason"] = "near-zero β₃ (τ outlier)"

    # Compute τ for non-excluded wells
    merged["tau_months"] = np.nan
    valid = ~merged["Excluded"]
    merged.loc[valid, "tau_months"] = (
        merged.loc[valid, "Sy_median"] / merged.loc[valid, "beta_3_drainage"]
    )

    # Tidy up output columns
    tau_df = merged[[
        "Well", "Cluster", "Easting", "Northing",
        "Sy_median", "beta_3_drainage", "tau_months",
        "n_events", "Corrected", "Confidence",
        "Excluded", "Exclude_Reason",
    ]].copy()
    tau_df = tau_df.rename(columns={"beta_3_drainage": "beta_3"})
    tau_df = tau_df.sort_values(["Cluster", "Well"]).reset_index(drop=True)

    n_valid = valid.sum()
    n_excluded = merged["Excluded"].sum()
    excluded_wells = merged.loc[merged["Excluded"], "Well"].tolist()
    print(f"  τ computed for {n_valid} wells; {n_excluded} excluded "
          f"({', '.join(w.upper() for w in excluded_wells)})")

    # Cluster summary
    for cid in sorted(tau_df.loc[~tau_df["Excluded"], "Cluster"].unique()):
        sub = tau_df[(tau_df["Cluster"] == cid) & (~tau_df["Excluded"])]
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        print(f"    {label}: τ = {sub['tau_months'].mean():.1f} months "
              f"(range {sub['tau_months'].min():.1f}–{sub['tau_months'].max():.1f}, "
              f"n={len(sub)})")

    return tau_df


def plot_drainage_timescale_map(tau_df, out_path):
    """
    IDW-interpolated contour surface of drainage timescale τ = Sy / β₃ (months).

    Layout mirrors plot_contour_map(): greyscale hillshade DEM base, semi-transparent
    τ surface, KML overlays, cluster-coloured well markers with τ value labels.
    Excluded wells (CEH12, CEH15, CEH14) shown as red crosses outside interpolation.
    """
    from matplotlib.lines import Line2D
    from utils.map_utils import load_dem_hillshade, add_kml_features

    # ── Study area bounds ─────────────────────────────────────────────────────
    XI_MIN, XI_MAX = 240200, 243800
    YI_MIN, YI_MAX = 362200, 365800
    GRID_STEP = 50

    # Separate included vs excluded
    valid = tau_df[~tau_df["Excluded"]].copy()
    excluded = tau_df[tau_df["Excluded"]].copy()

    x   = valid["Easting"].values
    y   = valid["Northing"].values
    tau = valid["tau_months"].values

    xi = np.arange(XI_MIN, XI_MAX, GRID_STEP)
    yi = np.arange(YI_MIN, YI_MAX, GRID_STEP)
    Xi, Yi = np.meshgrid(xi, yi)

    def idw(xq, yq, xs, ys, vs, power=2):
        dist = np.sqrt((xq - xs[:, None, None])**2 + (yq - ys[:, None, None])**2)
        dist = np.where(dist == 0, 1e-10, dist)
        w = 1.0 / dist**power
        return np.sum(w * vs[:, None, None], axis=0) / np.sum(w, axis=0)

    Zi = idw(Xi, Yi, x, y, tau)
    site_mask = make_site_mask(Xi, Yi)
    Zi_masked = np.ma.masked_where(~site_mask | np.isnan(Zi), Zi)

    # ── Colourmap and range ───────────────────────────────────────────────────
    tau_min = np.floor(tau.min())
    tau_max = np.ceil(tau.max())
    # Use a diverging-ish scheme: fast drainage (low τ) = cool, sluggish = warm
    cmap = get_cmap("RdYlBu_r")  # colour: red = high τ (sluggish), blue = low τ (fast)
                                  # BW: light grey = low τ (fast), dark = high τ (sluggish)

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white", dpi=200)
    ax.set_xlim(XI_MIN, XI_MAX)
    ax.set_ylim(YI_MIN, YI_MAX)
    ax.set_aspect("equal")

    # Layer 1 — greyscale hillshade DEM
    _, dem_loaded, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=0.35, vert_exag=3.0, zorder=1)
    if not dem_loaded:
        print("  [WARNING] DEM hillshade unavailable — plain background used")
        ax.set_facecolor("#EEF2F6")

    # Layer 2 — semi-transparent τ surface
    cf = ax.contourf(Xi, Yi, Zi_masked, levels=20,
                     cmap=cmap, vmin=tau_min, vmax=tau_max,
                     alpha=0.65, zorder=2)
    cl = ax.contour(Xi, Yi, Zi_masked, levels=10,
                    colors="black" if BW_MODE else "white", linewidths=0.6, alpha=0.6, zorder=3)
    ax.clabel(cl, fmt="%.1f", fontsize=7, colors="black" if BW_MODE else "white")

    # Layer 3 — KML site features
    site_feature_handles = []
    try:
        site_feature_handles = add_kml_features(ax, DATA_DIR)
        print(f"  KML features added ({len(site_feature_handles)} layers)")
    except Exception as e:
        print(f"  [WARNING] KML features failed: {e}")

    # Colourbar
    cbar = fig.colorbar(cf, ax=ax, fraction=0.025, pad=0.01, shrink=0.75)
    cbar.set_label("Drainage timescale  τ = Sy / β₃  (months)",
                   fontsize=10, labelpad=10)

    # ── Well markers ──────────────────────────────────────────────────────────
    cluster_handles = []
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = valid[valid["Cluster"] == cid]
        if sub.empty:
            continue
        sizes = 60 + (sub["n_events"] - 20) * 1.2
        hatch = "//" if cid in FOREST_CIDS else None
        ax.scatter(sub["Easting"], sub["Northing"],
                   c=CLUSTER_COLOURS[cid],
                   s=sizes, marker=CLUSTER_MARKERS[cid],
                   edgecolors="black", linewidths=0.8,
                   alpha=0.92, zorder=5, hatch=hatch)
        cluster_handles.append(Line2D(
            [0], [0], marker=CLUSTER_MARKERS[cid], color="w",
            markerfacecolor=CLUSTER_COLOURS[cid],
            markeredgecolor="black", markersize=10,
            label=CLUSTER_LABELS[cid]))

    # τ value labels on included wells
    for _, row in valid.iterrows():
        ax.annotate(f"{row['tau_months']:.1f}",
                    (row["Easting"], row["Northing"]),
                    xytext=(4, 4), textcoords="offset points",
                    fontsize=6, color="#111111", zorder=6)

    # Excluded wells — red crosses
    exclude_handles = []
    if not excluded.empty:
        ax.scatter(excluded["Easting"], excluded["Northing"],
                   marker="x", c="red", s=120,
                   linewidths=2.0, zorder=7)
        for _, row in excluded.iterrows():
            reason = row["Exclude_Reason"] if row["Exclude_Reason"] else "excluded"
            ax.annotate(f"{row['Well'].upper()}\n({reason})",
                        (row["Easting"], row["Northing"]),
                        xytext=(6, 6), textcoords="offset points",
                        fontsize=6, color="red", style="italic", zorder=8)
        exclude_handles.append(
            Line2D([0], [0], marker="x", color="red", markersize=9,
                   linewidth=2, linestyle="none",
                   label="Excluded (negative β₃ or\nridge/slack-floor setting)"))

    # ── Legends ───────────────────────────────────────────────────────────────
    cluster_leg = ax.legend(
        handles=cluster_handles + exclude_handles, loc="lower left",
        title="Cluster  (// = forest interception correction)",
        fontsize=8, framealpha=0.95, edgecolor="#CCCCCC")
    ax.add_artist(cluster_leg)

    if site_feature_handles:
        ax.legend(handles=site_feature_handles, title="Site Features",
                  loc="upper right", fontsize=8,
                  framealpha=0.95, edgecolor="#CCCCCC")

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=10)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=10)
    ax.set_title(
        "Characteristic Drainage Timescale  τ = Sy / β₃  — Newborough Warren 2005–2026\n"
        "IDW interpolation (power=2)  |  Sy from WTF method (Section 3.7.3), "
        "β₃ from SSM (Section 3.4)\n"
        "Low τ (blue) = rapid aquifer turnover; "
        "high τ (red) = sluggish drainage  |  "
        "CEH13 excluded (τ ≈ 124 mo outlier)",
        fontsize=9, fontweight="bold", pad=10)

    ax.tick_params(labelsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Drainage timescale map saved → {out_path.name}")


def plot_aquifer_diagnostic_synthesis(tau_df, out_path):
    """
    Scatter plot of drainage timescale (τ = Sy / β₃) vs iterative NSE
    improvement (ΔNSE = NSE_SSM − NSE_TLM), with points coloured by cluster
    and sized by WTF-derived Sy.

    Synthesises three independently derived per-well diagnostics into a
    single aquifer architecture characterisation. Cluster-mean markers
    (larger, black-outlined diamonds) anchor the pattern.

    Excludes wells already flagged in tau_df (CEH12, CEH13, CEH14, CEH15).
    """
    from matplotlib.lines import Line2D

    # ── Load ΔNSE ─────────────────────────────────────────────────────────────
    nse_df = pd.read_csv(INT_LCSC_MODEL_STATS)
    nse_df["norm"] = nse_df["Well_Normalized"].str.lower().str.strip()

    # Work with non-excluded wells only
    valid = tau_df[~tau_df["Excluded"]].copy()
    valid["norm"] = valid["Well"].str.lower().str.strip()

    # Merge ΔNSE
    merged = valid.merge(
        nse_df[["norm", "Iterative_NSE_Improvement"]],
        on="norm", how="inner"
    )
    merged = merged.rename(columns={"Iterative_NSE_Improvement": "dNSE"})

    n_matched = len(merged)
    n_missed = len(valid) - n_matched
    if n_missed > 0:
        missed = set(valid["norm"]) - set(merged["norm"])
        print(f"  [WARNING] {n_missed} wells missing ΔNSE data: "
              f"{', '.join(sorted(missed))}")
    print(f"  {n_matched} wells with τ + ΔNSE + Sy for synthesis scatter")

    # ── Compute cluster means ─────────────────────────────────────────────────
    cmeans = merged.groupby("Cluster").agg(
        tau_mean=("tau_months", "mean"),
        dNSE_mean=("dNSE", "mean"),
        Sy_mean=("Sy_median", "mean"),
    ).reset_index()

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 7.5), facecolor="white", dpi=200)

    # Size scaling: map Sy range to marker area range
    sy_min, sy_max = merged["Sy_median"].min(), merged["Sy_median"].max()
    size_min, size_max = 40, 220
    def sy_to_size(sy):
        if sy_max == sy_min:
            return (size_min + size_max) / 2
        return size_min + (sy - sy_min) / (sy_max - sy_min) * (size_max - size_min)

    # Individual wells — scatter by cluster
    legend_handles = []
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = merged[merged["Cluster"] == cid]
        if sub.empty:
            continue
        sizes = sub["Sy_median"].apply(sy_to_size)
        ax.scatter(sub["dNSE"], sub["tau_months"],
                   c=CLUSTER_COLOURS[cid],
                   s=sizes, marker=CLUSTER_MARKERS[cid],
                   edgecolors="black", linewidths=0.5,
                   alpha=0.75, zorder=4)
        legend_handles.append(Line2D(
            [0], [0], marker=CLUSTER_MARKERS[cid], color="w",
            markerfacecolor=CLUSTER_COLOURS[cid],
            markeredgecolor="black", markersize=10,
            label=CLUSTER_LABELS[cid]))

    # Cluster means — larger star markers
    for _, row in cmeans.iterrows():
        cid = int(row["Cluster"])
        ax.scatter(row["dNSE_mean"], row["tau_mean"],
                   c=CLUSTER_COLOURS[cid],
                   s=300, marker="*",
                   edgecolors="black", linewidths=1.5,
                   alpha=0.95, zorder=6)

    legend_handles.append(Line2D(
        [0], [0], marker="*", color="w",
        markerfacecolor="#AAAAAA",
        markeredgecolor="black", markeredgewidth=1.5,
        markersize=14, label="Cluster mean"))

    # Sy size legend — three representative sizes
    sy_legend_vals = [0.20, 0.30, 0.40]
    sy_legend_handles = []
    for sv in sy_legend_vals:
        if sv < sy_min or sv > sy_max + 0.02:
            continue
        sy_legend_handles.append(Line2D(
            [0], [0], marker="o", color="w",
            markerfacecolor="#CCCCCC",
            markeredgecolor="black",
            markersize=np.sqrt(sy_to_size(sv)) * 0.65,
            label=f"Sy = {sv:.2f}"))

    # ── Annotation regions ────────────────────────────────────────────────────
    # Place interpretive text near cluster centroids
    annotations = {
        1: ("shallow pan\n(lake boundary)", 0.12, -0.08),
        4: ("deep sponge\n(impeded drainage)", -0.06, 0.06),
        5: ("coastal forest\n(deeper sand)", 0.08, -0.06),
    }
    for cid, (text, dx_frac, dy_frac) in annotations.items():
        cm = cmeans[cmeans["Cluster"] == cid]
        if cm.empty:
            continue
        x_pos = cm["dNSE_mean"].iloc[0]
        y_pos = cm["tau_mean"].iloc[0]
        # Offset in data coordinates scaled to axis range
        x_range = merged["dNSE"].max() - merged["dNSE"].min()
        y_range = merged["tau_months"].max() - merged["tau_months"].min()
        ax.annotate(text,
                    (x_pos, y_pos),
                    xytext=(x_pos + dx_frac * x_range,
                            y_pos + dy_frac * y_range),
                    fontsize=8, fontstyle="italic", color="#444444",
                    ha="center",
                    arrowprops=dict(arrowstyle="->", color="#999999",
                                   lw=0.8, connectionstyle="arc3,rad=0.15"),
                    zorder=7)

    # ── Axes and labels ───────────────────────────────────────────────────────
    ax.set_xlabel("ΔNSE  (iterative NSE improvement: SSM − TLM)", fontsize=11)
    ax.set_ylabel("τ = Sy / β₃  (drainage timescale, months)", fontsize=11)
    ax.set_title(
        "Aquifer Diagnostic Synthesis — Newborough Warren 2005–2026\n"
        "Three independently derived parameters triangulate aquifer architecture\n"
        "τ (drainage memory) vs ΔNSE (drainage sensitivity), point size ∝ Sy (storage)",
        fontsize=10, fontweight="bold", pad=12)

    # Pad axes slightly
    x_pad = (merged["dNSE"].max() - merged["dNSE"].min()) * 0.12
    y_pad = (merged["tau_months"].max() - merged["tau_months"].min()) * 0.10
    ax.set_xlim(merged["dNSE"].min() - x_pad,
                merged["dNSE"].max() + x_pad)
    ax.set_ylim(max(0, merged["tau_months"].min() - y_pad),
                merged["tau_months"].max() + y_pad * 2)

    ax.grid(True, alpha=0.3, linestyle="--")

    # ── Legends ───────────────────────────────────────────────────────────────
    cluster_leg = ax.legend(
        handles=legend_handles, loc="upper left",
        title="Cluster", fontsize=9, title_fontsize=10,
        framealpha=0.95, edgecolor="#CCCCCC")
    ax.add_artist(cluster_leg)

    if sy_legend_handles:
        ax.legend(handles=sy_legend_handles, loc="center right",
                  title="Point size = Sy", fontsize=8, title_fontsize=9,
                  framealpha=0.95, edgecolor="#CCCCCC")

    plt.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  Aquifer diagnostic synthesis saved → {out_path.name}")


def main(supplementary=True):
    # ── Paths ──────────────────────────────────────────────────────────────────
    script_dir   = Path(__file__).parent
    project_root = script_dir.parent

    out_root         = OUT_DIR
    out_dir          = DIR_18
    path_well_sy     = OUT_18_WELL_SY_TABLE
    path_sy_map      = OUT_18_SY_MAP
    path_contour     = OUT_18_SY_CONTOUR
    path_contour_ext = OUT_18_SY_CONTOUR_EXT

    print("=================================================================")
    print("  18: WTF Spatial Analysis — Individual Well Sy and Mapping")
    print(f"  Supplementary figures: {'yes' if supplementary else 'no'}")
    print("=================================================================")

    print("\nLoading well data...")
    try:
        wells_df, climate, cluster_df, locations = load_well_data(out_root)
    except Exception as e:
        print(f"  [ERROR] Could not load well data: {e}")
        return

    print("\nRunning reference well WTF analysis...")
    well_results = wtf_individual_wells(wells_df, climate, cluster_df, locations)

    print("\nExporting reference well Sy table...")
    well_results.to_csv(path_well_sy, index=False)
    print(f"  Saved → {path_well_sy.name}")
    well_results.to_csv(INT_WTF_WELL_SY, index=False)
    print(f"  Intermediate copy → {INT_WTF_WELL_SY.name}")

    # ── Paper figure — always generated ──────────────────────────────────
    print("\nGenerating spatial point map (reference wells)...")
    plot_spatial_map(well_results, path_sy_map)

    # ── Supplementary figures — only with --supplementary flag ────────────
    if supplementary:
        print("\nGenerating Sy contour map (reference wells only)...")
        plot_contour_map(well_results, path_contour)

        print("\nRunning extended well WTF analysis...")
        ext_results = wtf_extended_wells(climate, locations, out_root)
        if ext_results is not None:
            print("\nGenerating Sy contour map (reference + extended wells)...")
            plot_contour_map_extended(well_results, ext_results, path_contour_ext)
        else:
            print("  Skipping extended contour map — no extended well results")

        # ── Drainage timescale map (τ = Sy / β₃) ─────────────────────────
        print("\nComputing drainage timescale (τ = Sy / β₃)...")
        tau_df = compute_drainage_timescale(well_results)
        tau_df.to_csv(OUT_18_DRAINAGE_TIMESCALE_CSV, index=False)
        print(f"  Saved → {OUT_18_DRAINAGE_TIMESCALE_CSV.name}")

        print("\nGenerating drainage timescale contour map...")
        plot_drainage_timescale_map(tau_df, OUT_18_DRAINAGE_TIMESCALE)

        print("\nGenerating aquifer diagnostic synthesis scatter...")
        plot_aquifer_diagnostic_synthesis(tau_df, OUT_18_AQUIFER_SYNTHESIS)
    else:
        print("\nSupplementary contour maps skipped "
              "(pass --supplementary to generate)")

    print(f"\nAll outputs written to {out_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Script 18 — WTF Spatial Analysis")
    parser.add_argument("--no-supplementary", action="store_false",
                        dest="supplementary",
                        help="Skip Sy IDW contour maps for supplementary materials.")
    parser.set_defaults(supplementary=True)
    args = parser.parse_args()
    main(supplementary=args.supplementary)
