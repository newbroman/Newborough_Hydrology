"""
====================================================================================
PHASE 2: PEARSON MEMBERSHIP AFFINITY AUDIT
====================================================================================
Purpose:
    Bridges the gap between the strict 2026 Reference Network and the 
    shorter-record Extended Network (FE/LIS). Calculates standardised centroids 
    from the Reference model and uses Pearson correlation to classify and map 
    all remaining wells.
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    INT_WELLS_REFERENCE,
    INT_WELLS_EXTENDED,
    INT_CLUSTER_STATS,
    INT_LOCATIONS,
    INT_PEAR_AUDIT_SITEWIDE,
    OUT_06_AFFINITY_CHART,
    OUT_06_INTEGRATION_MAP,
)
from utils.config import CLUSTER_COLOURS, CLUSTER_LABELS
from utils.data_utils import normalize_well_name
from utils.map_utils import load_dem_layer, add_kml_features, add_osm_basemap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import geopandas as gpd
import contextily as ctx
import fiona
from pathlib import Path
from adjustText import adjust_text
from matplotlib.lines import Line2D

fiona.drvsupport.supported_drivers["KML"] = "rw"

# ==========================================
# CONFIGURATION & PATHS
# ==========================================

# Inputs from Phase 1
REF_WELLS_PATH = INT_WELLS_REFERENCE
EXT_WELLS_PATH = INT_WELLS_EXTENDED
CLUSTER_PATH = INT_CLUSTER_STATS
LOCATION_PATH = INT_LOCATIONS

# Phase 2 Outputs
OUT_BAR = OUT_06_AFFINITY_CHART
OUT_MAP = OUT_06_INTEGRATION_MAP

EXPECTED_CLUSTERS = sorted(CLUSTER_LABELS.keys())
DELTA_THRESH = 0.05
MCA_THRESH = 0.90

# Aesthetics
plt.rcParams.update({'font.family': 'sans-serif', 'axes.labelsize': 11, 'legend.fontsize': 9})

# Keep DEM scale identical across PEAR map products.
DEM_VMIN = 0.0
DEM_VCENTER = 12.0
DEM_VMAX = 35.0

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def wells_to_row_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure wells are rows and timestamps are columns."""
    matrix = df.copy()
    matrix = matrix.apply(pd.to_numeric, errors='coerce')
    matrix = matrix.T
    matrix.index = [normalize_well_name(w) for w in matrix.index]
    return matrix

def zscore_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score standardisation by row to extract the pure rhythmic pulse."""
    mean = df.mean(axis=1)
    std = df.std(axis=1, ddof=0)
    return df.sub(mean, axis=0).div(std.replace(0, np.nan), axis=0)

def safe_pearson(a: pd.Series, b: pd.Series) -> float:
    """Calculates Pearson r, ignoring gaps where timestamps don't overlap.

    Requires at least 24 months of shared record — matching the extended network
    minimum — to avoid spurious correlations from very short overlaps.
    """
    pair = pd.concat([a, b], axis=1).dropna()
    if len(pair) < 24 or pair.iloc[:, 0].std(ddof=0) == 0 or pair.iloc[:, 1].std(ddof=0) == 0:
        return np.nan
    return pair.iloc[:, 0].corr(pair.iloc[:, 1], method='pearson')


def create_affinity_bar_plot(audit_df: pd.DataFrame) -> None:
    """Create extended-network affinity chart with LCSC-aligned colors and full labels."""
    if audit_df.empty:
        return

    r_cols = [f"r_C{c}" for c in EXPECTED_CLUSTERS if f"r_C{c}" in audit_df.columns]
    if not r_cols:
        return

    preferred = ["ceh1", "nw1", "ceh8", "ceh19", "d15", "ceh17", "lis1", "lis2",
                 "fe1", "fe2", "fe3", "fe4"]
    # Guard against duplicate well ids in audit output to keep plotting vectors aligned.
    audit_idx = audit_df.drop_duplicates(subset=["Well_Normalised"], keep="first").set_index("Well_Normalised")
    available = [w for w in preferred if w in audit_idx.index]

    if len(available) < 3:
        ranked = audit_idx["Delta"].abs().sort_values(ascending=False)
        available = [w for w in ranked.index][:8]

    if not available:
        return

    plot_df = audit_idx.loc[available, r_cols].copy()
    plot_df.columns = [c.replace("r_", "") for c in plot_df.columns]  # r_C1 -> C1

    fig, ax = plt.subplots(figsize=(16, 7), dpi=300)
    x = np.arange(len(available))
    width = 0.12

    for i, col in enumerate(plot_df.columns):
        cid = int(col.replace("C", "")) if col.replace("C", "").isdigit() else None
        ax.bar(
            x + (i - 2.5) * width,
            plot_df[col].values,
            width=width,
            label=CLUSTER_LABELS.get(cid, col),
            color=CLUSTER_COLOURS.get(cid, "#808080"),
            edgecolor="black",
            linewidth=0.6,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([w.upper() for w in available])
    ax.set_ylabel("Pearson Correlation (r)")
    ax.set_title("Extended Network Membership Affinity by Cluster", fontweight="bold")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    y_max = float(np.nanmax(plot_df.values)) if not plot_df.empty else 1.0
    y_min = min(0.0, float(np.nanmin(plot_df.values)) - 0.02) if not plot_df.empty else 0.0
    ax.set_ylim(y_min, min(1.05, y_max + 0.22))
    ax.legend(title="Cluster", loc="lower right", frameon=True)

    plt.tight_layout()
    plt.savefig(OUT_BAR, dpi=300, bbox_inches="tight")
    plt.close(fig)

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    make_all_dirs()
    print("--- Starting Phase 2: Pearson Affinity Audit ---")

    # 1. Load Data
    try:
        ref_wells = pd.read_csv(REF_WELLS_PATH, index_col=0, parse_dates=True)
        ext_wells = pd.read_csv(EXT_WELLS_PATH, index_col=0, parse_dates=True)
        ref_clusters = pd.read_csv(CLUSTER_PATH)
        loc_df = pd.read_csv(LOCATION_PATH)
    except FileNotFoundError as e:
        print(f"Error loading Phase 1 files. Ensure LCSC01 and LCSC02 have been run. Details: {e}")
        return

    # Clean inputs
    ref_wells = wells_to_row_matrix(ref_wells)
    ext_wells = wells_to_row_matrix(ext_wells)
    ref_clusters['Match_ID'] = ref_clusters['Match_ID'].apply(normalize_well_name)
    loc_df['Match_ID'] = loc_df['Match_ID'].apply(normalize_well_name)

    well_to_cluster = ref_clusters.set_index('Match_ID')['Cluster'].to_dict()

    # 2. Standardisation & Template Building
    all_wells = pd.concat([ref_wells, ext_wells]).apply(pd.to_numeric, errors='coerce')
    z_all = zscore_rows(all_wells)

    z_ref = z_all.loc[ref_wells.index]
    centroids = {}
    for c in EXPECTED_CLUSTERS:
        members = [w for w, assigned in well_to_cluster.items() if assigned == c and w in z_ref.index]
        centroids[c] = z_ref.loc[members].mean(axis=0, skipna=True) if members else pd.Series(np.nan, index=z_ref.columns)
    
    centroid_df = pd.DataFrame(centroids)

    # 3. Correlation Audit
    print(" -> Running correlation matrix against Reference Templates...")
    audit_rows = []
    
    for well_id, series in z_all.iterrows():
        is_ref = well_id in ref_wells.index
        assigned_c = well_to_cluster.get(well_id, np.nan)
        
        corrs = {c: safe_pearson(series, centroid_df[c]) for c in EXPECTED_CLUSTERS}
        valid_corrs = {k: v for k, v in corrs.items() if pd.notna(v)}
        
        if not valid_corrs:
            continue
            
        sorted_corrs = sorted(valid_corrs.items(), key=lambda x: x[1], reverse=True)
        best_c, best_r = sorted_corrs[0]
        runner_up_c = sorted_corrs[1][0] if len(sorted_corrs) > 1 else np.nan
        runner_up_r = sorted_corrs[1][1] if len(sorted_corrs) > 1 else 0
        delta = best_r - runner_up_r

        # Classification
        if is_ref and pd.notna(assigned_c):
            if best_c != assigned_c: status = "Ref_Spy"
            elif delta < DELTA_THRESH: status = "Ref_Fuzzy"
            else: status = "Ref_Core"
        else:
            status = "Ext_Fuzzy" if delta < DELTA_THRESH else "Ext_Core"

        mca_count = sum(1 for v in valid_corrs.values() if v > MCA_THRESH)

        rec = {
            "Well_Normalised": well_id, "Network": "Reference" if is_ref else "Extended",
            "Original_Cluster": assigned_c, "Best_Match_Cluster": best_c, "Secondary_Cluster": runner_up_c,
            "Best_r": round(best_r, 4), "Delta": round(delta, 4), "Status": status, "MCA_Flag": mca_count >= 3
        }
        rec.update({f"r_C{k}": round(v, 4) for k, v in corrs.items()})
        audit_rows.append(rec)

    audit_columns = [
        'Well_Normalised', 'Network', 'Original_Cluster', 'Best_Match_Cluster',
        'Secondary_Cluster', 'Best_r', 'Delta', 'Status', 'MCA_Flag'
    ] + [f'r_C{k}' for k in EXPECTED_CLUSTERS]
    audit_df = pd.DataFrame(audit_rows, columns=audit_columns)
    audit_df.to_csv(INT_PEAR_AUDIT_SITEWIDE, index=False)
    ext_count = int((audit_df['Network'] == 'Extended').sum()) if 'Network' in audit_df.columns else 0
    print(f" -> Audit saved. Found {ext_count} Extended wells.")

    create_affinity_bar_plot(audit_df)

    if audit_df.empty:
        fig, ax = plt.subplots(figsize=(10, 6), dpi=200)
        ax.axis('off')
        ax.text(0.5, 0.5, 'No Extended wells available for Pearson integration.', ha='center', va='center', fontsize=14)
        plt.tight_layout()
        plt.savefig(OUT_MAP, bbox_inches='tight')
        plt.close(fig)
        print(f"Success: Integration Map saved to {OUT_MAP.name}")
        return

    # 4. Generate Fresh Integration Map
    print(" -> Generating Pearson Integration Map...")
    map_df = audit_df.merge(loc_df[['Match_ID', 'E', 'N']], left_on='Well_Normalised', right_on='Match_ID', how='inner')
    map_df = map_df.dropna(subset=['E', 'N'])

    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)

    # Base Map (DEM + KMLs)
    dem_path = DATA_DIR / "newborough_dem.tif"
    if dem_path.exists():
        try:
            import rasterio
            with rasterio.open(str(dem_path)) as src:
                dem_data, extent = src.read(1), [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
                dem_data = np.ma.masked_where(dem_data == src.nodata, dem_data) if src.nodata is not None else dem_data
                cmap = mcolors.LinearSegmentedColormap.from_list("custom", plt.cm.terrain(np.linspace(0.25, 1.0, 256)))
                cmap.set_under("dodgerblue")
                img = ax.imshow(
                    dem_data,
                    cmap=cmap,
                    alpha=0.45,
                    norm=mcolors.TwoSlopeNorm(vmin=DEM_VMIN, vcenter=DEM_VCENTER, vmax=DEM_VMAX),
                    extent=extent,
                    origin="upper",
                    zorder=1,
                )
                fig.colorbar(img, ax=ax, shrink=0.55, pad=0.02, extend="both").set_label("Elevation (m AOD)", rotation=270, labelpad=18)
                ax.set_xlim(extent[0], extent[1]); ax.set_ylim(362000, 365000)
        except Exception:
            pass
    else:
        ctx.add_basemap(ax, crs="EPSG:27700", source=ctx.providers.OpenStreetMap.Mapnik, zorder=1, alpha=0.7)

    site_feature_handles = add_kml_features(ax, DATA_DIR)

    # Plot Wells
    for status in map_df['Status'].unique():
        sub = map_df[map_df['Status'] == status]
        is_ext = "Ext" in status
        
        # Extended wells get a distinct marker (Square) and dashed edge to separate them from the core.
        if is_ext: marker, size, edge_ls = "s", 160, "--"
        elif "Spy" in status: marker, size, edge_ls = "*", 220, "-"
        elif "Fuzzy" in status: marker, size, edge_ls = "D", 120, "-"
        else: marker, size, edge_ls = "o", 120, "-"
        
        colors = [CLUSTER_COLOURS.get(int(c), "grey") for c in sub['Best_Match_Cluster']]
        ax.scatter(sub['E'], sub['N'], c=colors, marker=marker, s=size, edgecolor='black', linewidth=1.2, linestyle=edge_ls, alpha=0.9, zorder=5)

    # Start labels with a slight offset, then use strong repulsion to reduce overlaps in dense zones.
    label_x = map_df['E'].to_numpy(dtype=float)
    label_y = map_df['N'].to_numpy(dtype=float)
    texts = [
        ax.text(
            r['E'] + 14,
            r['N'] + 14,
            r['Well_Normalised'].upper(),
            fontsize=8,
            fontweight='bold',
            zorder=10,
            bbox=dict(boxstyle='round,pad=0.12', facecolor='white', edgecolor='none', alpha=0.65),
        )
        for _, r in map_df.iterrows()
    ]
    adjust_text(
        texts,
        x=label_x,
        y=label_y,
        ax=ax,
        expand_text=(1.18, 1.26),
        expand_points=(1.32, 1.40),
        force_text=(0.85, 1.05),
        force_points=(1.00, 1.20),
        only_move={'text': 'xy', 'points': 'xy'},
        lim=400,
    )

    # Legends
    ax.set_title("Pearson Integration Map: Reference vs. Extended Networks", fontsize=15, fontweight='bold')
    ax.set_xlabel("Easting (m)"); ax.set_ylabel("Northing (m)")

    handles_status = [
        Line2D([0], [0], marker='o', color='w', label='Ref: Core Assignment', markerfacecolor='grey', markeredgecolor='black', markersize=9),
        Line2D([0], [0], marker='s', color='w', label='Ext: Shorter Record (FE/LIS)', markerfacecolor='lightgrey', markeredgecolor='black', markersize=10, linestyle='--'),
        Line2D([0], [0], marker='*', color='w', label='Ref: Behavioural Spy', markerfacecolor='grey', markeredgecolor='black', markersize=14)
    ]
    ax.add_artist(ax.legend(handles=handles_status, loc='upper left', title="Network Classification", frameon=True))
    
    handles_clusters = [Line2D([0], [0], marker='o', color='w', label=CLUSTER_LABELS.get(c, f"C{c}"), markerfacecolor=CLUSTER_COLOURS[c], markeredgecolor='black', markersize=10) for c in EXPECTED_CLUSTERS]
    cluster_legend = ax.legend(handles=handles_clusters, loc='lower left', title="Calculated Cluster Affinity", frameon=True)
    ax.add_artist(cluster_legend)

    if site_feature_handles:
        dedup = {}
        for handle in site_feature_handles:
            dedup[handle.get_label()] = handle
        ax.legend(handles=list(dedup.values()), loc='upper right', title="Site Features", frameon=True)

    plt.tight_layout()
    plt.savefig(OUT_MAP, bbox_inches='tight')
    print(f"Success: Integration Map saved to {OUT_MAP.name}")

if __name__ == "__main__":
    main()