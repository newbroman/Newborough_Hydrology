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

Notes:
    - C4 Forest wells receive interception correction: R_eff = (1-0.24)*P - PET
    - C5 (tidal) and C6 (lake) excluded as physically unreliable
    - Extended wells use Best_Match_Cluster from 06_pear_membership_audit_sitewide.csv
    - Extended wells shown as open symbols on extended contour map
    - Forest contour values carry additional uncertainty (Freeman, 2008)

References:
    Healy, R.W. and Cook, P.G. (2002) Hydrogeology Journal 10, 91-109.
    Freeman, S. (2008) Hydrological impact of Corsican pine at Newborough Warren.
"""

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
    INT_MASTER_DATA, INT_WELL_ELEVATIONS, DATA_DIR,
    OUT_18_WELL_SY_TABLE, OUT_18_SY_MAP, OUT_18_SY_CONTOUR,
    OUT_18_SY_CONTOUR_EXT, INT_WTF_WELL_SY,
)
make_all_dirs()

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
FOREST_INTERCEPTION = 0.24    # Freeman (2008)
EXCLUDE_CLUSTERS    = [5, 6]  # tidal / lake
MIN_RISE_M          = 0.005   # m
MIN_NET_RECH        = 0.010   # m
MIN_EVENTS          = 15      # minimum qualifying events for confidence flag

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'axes.labelsize': 11, 'axes.titlesize': 11,
    'xtick.labelsize': 9,  'ytick.labelsize': 9,
})


def load_well_data(out_root):
    """Load individual well time series, climate, locations and cluster assignments."""
    from pathlib import Path as _Path
    if not (out_root / "01_wells_clean.csv").exists():
        out_root = _Path("/mnt/project")

    wells_df   = pd.read_csv(out_root / "01_wells_clean.csv",
                              index_col=0, parse_dates=True)
    climate    = pd.read_csv(out_root / "01_climate.csv", parse_dates=["Date"])
    cluster_df = pd.read_csv(out_root / "02_cluster_stats.csv")
    locations  = pd.read_csv(out_root / "01_locations.csv")

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

        # Interception correction for Forest cluster
        if cluster == 4:
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

    plot_metric_map = None
    data_dir = DATA_DIR

    if plot_metric_map is None:
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
                       "C4 Forest values corrected for 24% canopy interception "
                       "(Freeman, 2008); spatial canopy variability means "
                       "Forest estimates are approximate"),
        output_path = out_path,
        cmap        = "RdYlGn",
        data_dir    = data_dir,
        vmin        = 0.10,
        vmax        = 0.40,
    )
    print(f"  Point map saved → {out_path.name}")


def plot_contour_map(well_results, out_path):
    """
    IDW-interpolated contour surface of WTF Sy across the site.
    Uses OSM basemap + KML overlays (no DEM — avoids competing colour dimensions).
    Forest cluster wells hatched to signal interception uncertainty.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

    from scipy.spatial import ConvexHull
    from matplotlib.path import Path as MplPath

    # ── Load map utilities ────────────────────────────────────────────────────
    add_osm  = None
    add_kml  = None
    data_dir = Path(__file__).parent.parent / "data"
    try:
        import geopandas as gpd
        from utils.map_utils import add_osm_basemap, add_kml_features
        from utils.paths import DATA_DIR
        add_osm  = add_osm_basemap
        add_kml  = add_kml_features
        data_dir = DATA_DIR
    except ImportError:
        gpd = None

    # ── Interpolation ─────────────────────────────────────────────────────────
    x  = well_results["Easting"].values
    y  = well_results["Northing"].values
    sy = well_results["Sy_median"].values

    margin = 200
    xi = np.linspace(x.min()-margin, x.max()+margin, 300)
    yi = np.linspace(y.min()-margin, y.max()+margin, 300)
    Xi, Yi = np.meshgrid(xi, yi)

    def idw(xq, yq, xs, ys, vs, power=2):
        dist = np.sqrt((xq - xs[:,None,None])**2 + (yq - ys[:,None,None])**2)
        dist = np.where(dist == 0, 1e-10, dist)
        weights = 1.0 / dist**power
        return np.sum(weights * vs[:,None,None], axis=0) / np.sum(weights, axis=0)

    Zi = idw(Xi, Yi, x, y, sy)

    # Convex hull mask
    hull = ConvexHull(np.column_stack([x, y]))
    hull_path = MplPath(np.column_stack([x[hull.vertices], y[hull.vertices]]))
    mask = ~hull_path.contains_points(
        np.column_stack([Xi.ravel(), Yi.ravel()])
    ).reshape(Xi.shape)
    Zi_masked = np.ma.masked_where(mask, Zi)

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white", dpi=200)
    ax.set_facecolor("#EEF2F6")

    # OSM basemap — must set axis limits first so contextily knows extent
    ax.set_xlim(x.min()-margin, x.max()+margin)
    ax.set_ylim(y.min()-margin, y.max()+margin)
    ax.set_aspect("equal")

    if add_osm is not None and gpd is not None:
        try:
            gdf_tmp = gpd.GeoDataFrame(
                well_results,
                geometry=gpd.points_from_xy(
                    well_results["Easting"], well_results["Northing"]),
                crs="EPSG:27700")
            add_osm(ax, gdf_tmp)
            print("  OSM basemap added")
        except Exception as e:
            print(f"  [WARNING] OSM basemap failed: {e}")

    # Contour fill (semi-transparent over basemap)
    cf = ax.contourf(Xi, Yi, Zi_masked, levels=20,
                     cmap="RdYlGn", vmin=0.10, vmax=0.40,
                     alpha=0.70, zorder=2)

    # Contour lines
    cl = ax.contour(Xi, Yi, Zi_masked, levels=10,
                    colors="white", linewidths=0.6, alpha=0.6, zorder=3)
    ax.clabel(cl, fmt="%.2f", fontsize=7, colors="white")

    # KML features (forest boundary, clearfell, streams)
    site_feature_handles = []
    if add_kml is not None:
        try:
            site_feature_handles = add_kml(ax, data_dir)
            print(f"  KML features added ({len(site_feature_handles)} layers)")
        except Exception as e:
            print(f"  [WARNING] KML features failed: {e}")

    # Colourbar
    cbar = fig.colorbar(cf, ax=ax, fraction=0.025, pad=0.01, shrink=0.75)
    cbar.set_label("Specific yield Sy  (WTF event median, IDW interpolation)",
                   fontsize=10, labelpad=10)

    # Cluster colours and markers matching config.py
    CLUSTER_COLOURS = {1:"#E69F00", 2:"#009E73", 3:"#CC79A7", 4:"#D55E00"}
    CLUSTER_MARKERS = {1:"o", 2:"s", 3:"^", 4:"D"}
    CLUSTER_LABELS  = {
        1:"C1 Eastern Lake-buffer",
        2:"C2 Eastern Mature Dune",
        3:"C3 Western Mature Dune",
        4:"C4 Forest (interception-corrected)"
    }

    cluster_handles = []
    for cid in [1, 2, 3, 4]:
        sub = well_results[well_results["Cluster"] == cid]
        if sub.empty:
            continue
        sizes  = 60 + (sub["n_events"] - 20) * 1.2
        hatch  = "//" if cid == 4 else None
        ax.scatter(sub["Easting"], sub["Northing"],
                   c=CLUSTER_COLOURS[cid],
                   s=sizes, marker=CLUSTER_MARKERS[cid],
                   edgecolors="black", linewidths=0.8,
                   alpha=0.92, zorder=5, hatch=hatch)
        from matplotlib.lines import Line2D
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
        ax.legend(
            handles=site_feature_handles, title="Site Features",
            loc="upper right", fontsize=8,
            framealpha=0.95, edgecolor="#CCCCCC")

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=10)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=10)
    ax.set_title(
        "Interpolated WTF Specific Yield Surface — Newborough Warren 2005–2026\n"
        "IDW interpolation (power=2) of event-based median Sy per well  |  "
        "OSM basemap + KML overlays\n"
        "C4 Forest values interception-corrected (Freeman, 2008) — "
        "contours in Forest zone are approximate",
        fontsize=9, fontweight="bold", pad=10)

    ax.grid(True, lw=0.3, alpha=0.2, color="#CCCCCC")
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
    from pathlib import Path as _Path

    try:
        if not (out_root / "01_wells_extended.csv").exists():
            out_root = _Path("/mnt/project")
        wells_ext  = pd.read_csv(out_root / "01_wells_extended.csv",
                                  index_col=0, parse_dates=True)
        membership = pd.read_csv(out_root / "06_pear_membership_audit_sitewide.csv")
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

        if cluster == 4:
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
    Extended wells shown as open symbols to distinguish from reference wells.
    Otherwise identical layout to plot_contour_map.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

    from scipy.spatial import ConvexHull
    from matplotlib.path import Path as MplPath

    # ── Map utilities ─────────────────────────────────────────────────────────
    add_osm  = None
    add_kml  = None
    gpd_mod  = None
    data_dir = Path(__file__).parent.parent / "data"
    try:
        import geopandas as _gpd
        from utils.map_utils import add_osm_basemap, add_kml_features
        from utils.paths import DATA_DIR
        add_osm  = add_osm_basemap
        add_kml  = add_kml_features
        data_dir = DATA_DIR
        gpd_mod  = _gpd
    except ImportError:
        gpd_mod = None

    # Add Network column to ref_results if missing
    ref = ref_results.copy()
    if 'Network' not in ref.columns:
        ref['Network'] = 'Reference'
    if 'Ridge_Flag' not in ref.columns:
        ref['Ridge_Flag'] = False

    ext = ext_results.copy()
    if 'Ridge_Flag' not in ext.columns:
        ext['Ridge_Flag'] = False

    # Exclude ridge wells from interpolation — shown separately on map
    ext_interp = ext[~ext['Ridge_Flag']].copy()
    ext_ridge  = ext[ext['Ridge_Flag']].copy()

    # Combined for interpolation (reference + non-ridge extended)
    combined = pd.concat([ref, ext_interp], ignore_index=True)

    x  = combined['Easting'].values
    y  = combined['Northing'].values
    sy = combined['Sy_median'].values

    margin = 200
    xi = np.linspace(x.min()-margin, x.max()+margin, 300)
    yi = np.linspace(y.min()-margin, y.max()+margin, 300)
    Xi, Yi = np.meshgrid(xi, yi)

    def idw(xq, yq, xs, ys, vs, power=2):
        dist = np.sqrt((xq - xs[:,None,None])**2 + (yq - ys[:,None,None])**2)
        dist = np.where(dist == 0, 1e-10, dist)
        w = 1.0 / dist**power
        return np.sum(w * vs[:,None,None], axis=0) / np.sum(w, axis=0)

    Zi = idw(Xi, Yi, x, y, sy)

    hull = ConvexHull(np.column_stack([x, y]))
    hull_path = MplPath(np.column_stack([x[hull.vertices], y[hull.vertices]]))
    mask = ~hull_path.contains_points(
        np.column_stack([Xi.ravel(), Yi.ravel()])).reshape(Xi.shape)
    Zi_masked = np.ma.masked_where(mask, Zi)

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 10), facecolor='white', dpi=200)
    ax.set_facecolor('#EEF2F6')
    ax.set_xlim(x.min()-margin, x.max()+margin)
    ax.set_ylim(y.min()-margin, y.max()+margin)
    ax.set_aspect('equal')

    if add_osm is not None and gpd_mod is not None:
        try:
            gdf_tmp = gpd_mod.GeoDataFrame(
                combined,
                geometry=gpd_mod.points_from_xy(
                    combined['Easting'], combined['Northing']),
                crs='EPSG:27700')
            add_osm(ax, gdf_tmp)
            print("  OSM basemap added")
        except Exception as e:
            print(f"  [WARNING] OSM basemap failed: {e}")

    cf = ax.contourf(Xi, Yi, Zi_masked, levels=20,
                     cmap='RdYlGn', vmin=0.10, vmax=0.40,
                     alpha=0.70, zorder=2)
    cl = ax.contour(Xi, Yi, Zi_masked, levels=10,
                    colors='white', linewidths=0.6, alpha=0.6, zorder=3)
    ax.clabel(cl, fmt='%.2f', fontsize=7, colors='white')

    site_feature_handles = []
    if add_kml is not None:
        try:
            site_feature_handles = add_kml(ax, data_dir)
            print(f"  KML features added ({len(site_feature_handles)} layers)")
        except Exception as e:
            print(f"  [WARNING] KML features failed: {e}")

    cbar = fig.colorbar(cf, ax=ax, fraction=0.025, pad=0.01, shrink=0.75)
    cbar.set_label('Specific yield Sy  (WTF event median, IDW interpolation)',
                   fontsize=10, labelpad=10)

    CLUSTER_COLOURS = {1:'#E69F00', 2:'#009E73', 3:'#CC79A7', 4:'#D55E00'}
    CLUSTER_MARKERS = {1:'o', 2:'s', 3:'^', 4:'D'}
    CLUSTER_LABELS  = {
        1:'C1 Eastern Lake-buffer',   2:'C2 Eastern Mature Dune',
        3:'C3 Western Mature Dune',   4:'C4 Forest (interception-corrected)',
    }

    from matplotlib.lines import Line2D
    cluster_handles = []

    # Reference wells — filled
    for cid in [1, 2, 3, 4]:
        sub = ref[ref['Cluster'] == cid]
        if sub.empty:
            continue
        sizes = 60 + (sub['n_events'] - 20) * 1.2
        hatch = '//' if cid == 4 else None
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
    for cid in [1, 2, 3, 4]:
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
        # Reason labels per well
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
        'OSM basemap + KML overlays\n'
        'Filled markers = reference wells; open markers = extended wells  |  '
        'C4 Forest interception-corrected (Freeman, 2008)',
        fontsize=9, fontweight='bold', pad=10)

    ax.grid(True, lw=0.3, alpha=0.2, color='#CCCCCC')
    ax.tick_params(labelsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Extended contour map saved → {out_path.name}")


def main(supplementary=False):
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
    else:
        print("\nSupplementary contour maps skipped "
              "(pass --supplementary to generate)")

    print(f"\nAll outputs written to {out_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Script 18 — WTF Spatial Analysis")
    parser.add_argument("--supplementary", action="store_true",
                        help="Also generate Sy IDW contour maps for supplementary "
                             "materials. Default: point map only.")
    args = parser.parse_args()
    main(supplementary=args.supplementary)
