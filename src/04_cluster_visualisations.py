"""
04_cluster_visualisations.py
Inputs:  02_cluster_stats.csv, 01_locations.csv
Outputs: outputs/04_cluster_visualisations/04_01_core_architecture_map.png
"""

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-12
#
# This module previously carried no __version__ constant; 1.0.0 marks its
# introduction, not the start of the module's history. Prior revisions are the
# dated notes and changelog entries elsewhere in the repository.

# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap).
# 2026-07-19 (legibility hand pass): well labels 8 -> 8.5 pt; map axis
#   labels gain +1 pt via map_utils v1.6.0 add_en_axes defaults.
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import fiona
from adjustText import adjust_text
from matplotlib.lines import Line2D

from utils.config import CLUSTER_COLOURS, CLUSTER_LABELS, CLUSTER_MARKERS, BW_MODE
from utils.data_utils import normalize_well_name
from utils.map_utils import load_dem_layer, add_kml_features, add_osm_basemap, add_en_axes
from utils.paths import make_all_dirs, DATA_DIR, INT_CLUSTER_STATS, INT_LOCATIONS, OUT_04_ARCHITECTURE_MAP

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import render_figure

fiona.drvsupport.supported_drivers["KML"] = "rw"

def cluster_id_from_value(value):
    text = str(value).strip()
    if text.startswith("C") and len(text) > 1 and text[1].isdigit():
        digits = "".join(ch for ch in text[1:] if ch.isdigit())
        return int(digits) if digits else None
    if text.isdigit(): return int(text)
    try: return int(float(text))
    except (TypeError, ValueError): return None

def main():
    banner("04", "Cluster Visualisations", version=__version__)
    make_all_dirs()
    print("--- Starting 04: Core Visualization ---")
    cluster_df = pd.read_csv(INT_CLUSTER_STATS)
    cluster_df["Match_ID"]   = cluster_df["Match_ID"].apply(normalize_well_name)
    cluster_df["Cluster_ID"] = cluster_df["Cluster"].apply(cluster_id_from_value)
    loc_df = pd.read_csv(INT_LOCATIONS)
    loc_df["Match_ID"] = loc_df["Match_ID"].apply(normalize_well_name)
    map_df = cluster_df.merge(loc_df[["Match_ID","E","N"]], on="Match_ID", how="inner")
    map_df = map_df.dropna(subset=["E","N","Cluster_ID"])
    if map_df.empty: print("Error: No valid coordinates."); return

    fig, ax = plt.subplots(figsize=(14,11), dpi=300)
    dem_layer, dem_loaded = load_dem_layer(ax, DATA_DIR)
    if not dem_loaded:
        add_osm_basemap(ax, gpd.GeoDataFrame(map_df, geometry=gpd.points_from_xy(map_df.E, map_df.N), crs="EPSG:27700"))
    site_feature_handles = add_kml_features(ax, DATA_DIR)
    for cid in sorted(map_df["Cluster_ID"].dropna().astype(int).unique()):
        subset = map_df[map_df["Cluster_ID"] == cid]
        ax.scatter(subset["E"], subset["N"],
                   c=CLUSTER_COLOURS.get(cid, "grey"),
                   marker=CLUSTER_MARKERS.get(cid, "o"),
                   s=150, edgecolor="black", linewidth=1.2, alpha=0.95, zorder=5)
    texts = [ax.text(row["E"], row["N"], row["Match_ID"].upper(), fontsize=8.5, fontweight="bold", zorder=10) for _, row in map_df.iterrows()]
    adjust_text(texts, arrowprops=dict(arrowstyle="-", color="black", lw=0.5), ax=ax)
    ax.set_title("Spatial Mapping of Groundwater Clusters at Newborough Warren", fontsize=15, fontweight="bold")
    add_en_axes(ax)
    if dem_layer is not None and not BW_MODE:
        fig.colorbar(dem_layer, ax=ax, shrink=0.55, pad=0.02, extend="both").set_label("Elevation (m AOD)", rotation=270, labelpad=18)
    cluster_handles = [Line2D([0],[0], marker=CLUSTER_MARKERS.get(c, "o"), color="w", label=CLUSTER_LABELS.get(c,f"C{c}"),
                              markerfacecolor=CLUSTER_COLOURS[c], markeredgecolor="black", markersize=10)
                       for c in sorted(map_df["Cluster_ID"].dropna().astype(int).unique())]
    cl = ax.legend(handles=cluster_handles, loc="lower left", title="Core Cluster Assignments", frameon=True)
    ax.add_artist(cl)
    if site_feature_handles:
        # Site Features moved to the left side (upper-left): under the canonical
        # extent's trimmed northern edge an upper-right key overlaps the topmost
        # wells, whereas the NW corner is clear.
        ax.legend(handles=site_feature_handles, loc="upper left", title="Site Features", frameon=True)
    plt.tight_layout()
    add_en_axes(ax)
    render_figure(plt.gcf(), OUT_04_ARCHITECTURE_MAP); plt.close()
    saved(f"{OUT_04_ARCHITECTURE_MAP.name}")

if __name__ == "__main__": main()
