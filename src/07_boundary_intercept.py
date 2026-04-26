"""
====================================================================================
07_boundary_intercept.py — Site-Wide Intercept Audit
====================================================================================
Purpose:
    Compares Model A (Strict Mass-Balance SSM, Intercept = 0) against 
    Model B (Unconstrained SSM, Intercept = fitted constant).
    
    Outputs:
        - 07_intercept_metrics.csv
        - outputs/07_boundary_intercept/07_intercept_01_ceh14_showdown.png
        - outputs/07_boundary_intercept/07_intercept_02_plumbing_map.png
        - outputs/07_boundary_intercept/07_intercept_03_nse_penalty_map.png
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    INT_WELLS_CLEAN,
    INT_CLIMATE,
    INT_MASTER_DATA,
    INT_CLUSTER_STATS,
    INT_INTERCEPT_METRICS,
    OUT_07_CEH14_SHOWDOWN,
    OUT_07_CEH14_SHOWDOWN_DATA,
    OUT_07_PLUMBING_MAP,
    OUT_07_NSE_PENALTY_MAP,
    OUT_07_MAPS_MERGED_DATA,
)
from utils.data_utils import normalize_well_name
from utils.model_utils import get_metrics, get_r2
from utils.map_utils import add_kml_features
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS, CLUSTER_MARKERS
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

# ==========================================
# CONFIGURATION & PATHS
# ==========================================

WELLS_PATH = INT_WELLS_CLEAN
CLIMATE_PATH = INT_CLIMATE
MASTER_PATH = INT_MASTER_DATA

LCSC_DATA_LIMIT = 100
EXCLUDED_WELLS_NORM = {'ceh7', 'ceh8', 'ceh37'}

# ==========================================
# AESTHETICS & PUBLICATION SETTINGS
# ==========================================
plt.rcParams.update({
    'font.family': 'sans-serif',
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
})

def compute_intercept_audit(target_well_name, df_clean, df_climate):
    """Compute Model A (No Intercept) vs Model B (Intercept). Returns metrics and plotting payload."""
    target_norm = normalize_well_name(target_well_name)
    target_col = next((c for c in df_clean.columns if normalize_well_name(c) == target_norm), None)

    base_row = {
        'Well': target_norm.upper(),
        'Well_Normalized': target_norm,
        'Status': 'ok',
        'Model_B_Intercept': np.nan,
        'OneStep_R2_Model_A': np.nan,
        'OneStep_R2_Model_B': np.nan,
        'Iterative_NSE_Model_A': np.nan,
        'Iterative_NSE_Model_B': np.nan,
        'NSE_Intercept_Effect': np.nan,
    }

    if target_col is None:
        base_row['Status'] = 'missing_column'
        return base_row, None

    well_series = pd.to_numeric(df_clean[target_col], errors='coerce')
    well_series.index = pd.to_datetime(well_series.index).to_period('M')

    climate = df_climate.copy()
    climate.index = pd.to_datetime(climate.index).to_period('M')

    df = pd.DataFrame({'h': well_series, 'P': pd.to_numeric(climate['P_m'], errors='coerce'), 'PET': pd.to_numeric(climate['PET'], errors='coerce')}).dropna()
    df['h_prev'] = df['h'].shift(1)
    df['Delta_h'] = df['h'] - df['h_prev']
    df = df.dropna()

    if len(df) < LCSC_DATA_LIMIT:
        base_row['Status'] = 'insufficient_data'
        return base_row, None

    df = df.iloc[-LCSC_DATA_LIMIT:].copy()

    # Model Formulations
    x_a = pd.DataFrame({'P': df['P'], 'PET_neg': -df['PET'], 'h_prev_neg': -df['h_prev']})
    x_b = sm.add_constant(x_a, has_constant='add')
    y_fit = df['Delta_h']

    model_a = sm.OLS(y_fit, x_a).fit()
    model_b = sm.OLS(y_fit, x_b).fit()

    p_arr, pet_arr, h_obs = df['P'].values, df['PET'].values, df['h'].values

    # Iterative Forecast
    h_iter_a, h_iter_b = np.full(len(h_obs), np.nan), np.full(len(h_obs), np.nan)
    h_iter_a[0], h_iter_b[0] = h_obs[0], h_obs[0]

    for t in range(1, len(h_obs)):
        dh_a = model_a.params['P']*p_arr[t] - model_a.params['PET_neg']*pet_arr[t] - model_a.params['h_prev_neg']*h_iter_a[t-1]
        dh_b = model_b.params['const'] + model_b.params['P']*p_arr[t] - model_b.params['PET_neg']*pet_arr[t] - model_b.params['h_prev_neg']*h_iter_b[t-1]
        h_iter_a[t] = h_iter_a[t-1] + dh_a
        h_iter_b[t] = h_iter_b[t-1] + dh_b

    # One step R2
    h_one_a, h_one_b = np.full(len(h_obs), np.nan), np.full(len(h_obs), np.nan)
    h_one_a[0], h_one_b[0] = h_obs[0], h_obs[0]
    for t in range(1, len(h_obs)):
        h_one_a[t] = h_obs[t-1] + (model_a.params['P']*p_arr[t] - model_a.params['PET_neg']*pet_arr[t] - model_a.params['h_prev_neg']*h_obs[t-1])
        h_one_b[t] = h_obs[t-1] + (model_b.params['const'] + model_b.params['P']*p_arr[t] - model_b.params['PET_neg']*pet_arr[t] - model_b.params['h_prev_neg']*h_obs[t-1])
        
    nse_a, rmse_a, _ = get_metrics(h_obs, h_iter_a)
    nse_b, rmse_b, _ = get_metrics(h_obs, h_iter_b)
    r2_one_a, r2_one_b = get_r2(h_obs, h_one_a), get_r2(h_obs, h_one_b)

    base_row.update({
        'Model_B_Intercept': model_b.params['const'],
        'OneStep_R2_Model_A': r2_one_a,
        'OneStep_R2_Model_B': r2_one_b,
        'Iterative_NSE_Model_A': nse_a,
        'Iterative_NSE_Model_B': nse_b,
        'NSE_Intercept_Effect': nse_b - nse_a
    })
    
    payload = {
        'index': df.index.to_timestamp(), 'h_obs': h_obs, 'h_one_a': h_one_a, 'h_one_b': h_one_b,
        'h_iter_a': h_iter_a, 'h_iter_b': h_iter_b, 'r2_one_a': r2_one_a, 'r2_one_b': r2_one_b,
        'nse_a': nse_a, 'nse_b': nse_b, 'rmse_a': rmse_a, 'rmse_b': rmse_b, 'well_label': target_norm.upper(),
        'intercept': model_b.params['const']
    }
    return base_row, payload

def plot_dual_showdown(output_path, payload):
    """Render dual-panel showdown figure for specific wells (e.g. CEH14)."""
    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(14, 10), dpi=300, sharex=True)

    # Top Panel: Diagnostic (One-Step)
    ax_top.plot(payload['index'], payload['h_obs'], color='black', lw=2.8, label='Observed')
    ax_top.plot(payload['index'], payload['h_one_a'], color='#0072B2', lw=2.2, ls='--', label=f"Model A: Strict Mass-Balance (R²={payload['r2_one_a']:.3f})")
    ax_top.plot(payload['index'], payload['h_one_b'], color='#D55E00', lw=2.2, ls=':', label=f"Model B: w/ Intercept Residual (R²={payload['r2_one_b']:.3f})")
    ax_top.set_title(f"Target: {payload['well_label']} | Top: Diagnostic Fit (One-Step)", fontweight='bold')
    ax_top.set_ylabel('Water Depth (m)')
    ax_top.grid(True, ls='--', alpha=0.5)
    ax_top.legend(loc='best', frameon=True, edgecolor='black')

    # Bottom Panel: Forecasting (Iterative)
    ax_bottom.plot(payload['index'], payload['h_obs'], color='black', lw=2.8, label='Observed')
    ax_bottom.plot(payload['index'], payload['h_iter_a'], color='#0072B2', lw=2.2, ls='--', 
                   label=f"Model A: Strict Mass-Balance (NSE={payload['nse_a']:.3f}, RMSE={payload['rmse_a']:.3f})")
    ax_bottom.plot(payload['index'], payload['h_iter_b'], color='#D55E00', lw=2.2, ls=':', 
                   label=f"Model B: w/ Intercept Residual (NSE={payload['nse_b']:.3f}, RMSE={payload['rmse_b']:.3f})")
    ax_bottom.set_title(f"Target: {payload['well_label']} | Bottom: Forecasting Stability (Iterative 100-month)", fontweight='bold')
    ax_bottom.set_xlabel('Date')
    ax_bottom.set_ylabel('Water Depth (m)')
    ax_bottom.grid(True, ls='--', alpha=0.5)
    ax_bottom.legend(loc='best', frameon=True, edgecolor='black')

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def export_dual_showdown_data_csv(output_path, payload):
    """Export the exact CEH14 series used in the dual showdown plot."""
    df_export = pd.DataFrame(
        {
            'Date': pd.to_datetime(payload['index']),
            'Observed_h': payload['h_obs'],
            'Model_A_OneStep_h': payload['h_one_a'],
            'Model_B_OneStep_h': payload['h_one_b'],
            'Model_A_Iterative_h': payload['h_iter_a'],
            'Model_B_Iterative_h': payload['h_iter_b'],
        }
    )
    df_export.to_csv(output_path, index=False)

def plot_metric_map(map_df, value_col, title, output_path, cmap, vmin=None, vmax=None):
    """SSM08-style robust mapping with DEM, overlays, and axis/aspect handling."""
    import geopandas as gpd
    import contextily as ctx
    import matplotlib.colors as mcolors
    from matplotlib.lines import Line2D
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from pathlib import Path

    def _safe_read_kml(path_obj):
        try:
            return gpd.read_file(str(path_obj), driver="KML")
        except Exception as exc:
            print(f"  [WARNING] Skipping {Path(path_obj).name}: KML unavailable ({exc})")
            return None

    map_df = map_df.copy()
    required_cols = ['Easting', 'Northing', value_col]
    missing_required = [c for c in required_cols if c not in map_df.columns]
    if missing_required:
        print(f"  [WARNING] Missing required columns for map: {missing_required}. Skipping {output_path.name}")
        return
    if 'Cluster_ID' not in map_df.columns:
        map_df['Cluster_ID'] = 1
    valid = map_df.dropna(subset=['Easting', 'Northing', value_col]).copy()
    if 'Cluster_ID' not in valid.columns:
        valid['Cluster_ID'] = 1
    valid['Cluster_ID'] = pd.to_numeric(valid['Cluster_ID'], errors='coerce').fillna(1).astype(int)
    if valid.empty:
        print(f"  [WARNING] No mappable data for {value_col}. Skipping {output_path.name}")
        return
    # CLUSTER_MARKERS / CLUSTER_LABELS imported from utils.config (k=5 partition).
    dem_layer = None
    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)
    # --- DEM Layer ---
    dem_path = DATA_DIR / "newborough_dem.tif"
    dem_loaded = False
    if dem_path.exists():
        try:
            import rasterio
            with rasterio.open(str(dem_path)) as src:
                dem_data = src.read(1)
                extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
                if src.nodata is not None:
                    dem_data = np.ma.masked_where(dem_data == src.nodata, dem_data)
                terrain_cmap = plt.cm.terrain
                terrain_colors = terrain_cmap(np.linspace(0.25, 1.0, 256))
                custom_topo = mcolors.LinearSegmentedColormap.from_list("custom_topo", terrain_colors)
                custom_topo.set_under("dodgerblue")
                div_norm = mcolors.TwoSlopeNorm(vmin=0, vcenter=12.0, vmax=dem_data.max())
                dem_layer = ax.imshow(dem_data, cmap=custom_topo, alpha=0.45, 
                                      norm=div_norm, extent=extent, origin="upper", zorder=1)
                ax.set_xlim(extent[0], extent[1])
                ax.set_ylim(362000, 365000)
                dem_loaded = True
        except Exception as e:
            print(f"DEM load failed: {e}. Falling back to OSM.")
    # --- Fallback to OSM ---
    if not dem_loaded:
        gdf_tmp = gpd.GeoDataFrame(valid, geometry=gpd.points_from_xy(valid.Easting, valid.Northing), crs="EPSG:27700")
        ctx.add_basemap(ax, crs=gdf_tmp.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik, zorder=1, alpha=0.7)
    # --- KML Features (via map_utils — includes broadleaf restock block) ---
    site_feature_handles = add_kml_features(ax, DATA_DIR)
    # --- Clip NSE_Intercept_Effect asymmetrically before plotting.
    #     The positive tail (CEH3 = +8.93) is clipped to +0.3 to prevent it dominating
    #     the colour scale. The negative tail is clipped to -0.05 to match the actual
    #     data range (worst value = -0.026), giving negative wells proper colour
    #     separation rather than compressing them all into 9% of a ±0.3 scale.
    #     Raw values are preserved in the CSV output.
    # Clip bounds chosen to match the actual data range (excluding CEH3 outlier):
    # negatives reach -0.026; positives reach +0.266 at CEH17 (excl. CEH3).
    # Clipping tightly ensures the bulk of the distribution spreads across the
    # full colour scale rather than being compressed into a narrow central band.
    NSE_CLIP_POS = 0.30   # CEH17 (+0.266) near max; CEH14/CEH21 at ~25-30% — but colormap
    #                        anchors are lightened so even the max is pale, not dark navy
    NSE_CLIP_NEG = -0.03  # CEH32 (-0.026) near max red; mid-range negatives visible
    NSE_CLIP = NSE_CLIP_POS   # retained for colorbar label
    if value_col == 'NSE_Intercept_Effect':
        valid = valid.copy()
        valid[value_col] = valid[value_col].clip(NSE_CLIP_NEG, NSE_CLIP_POS)

    # --- Build colour norm and cmap BEFORE scatter loop so all clusters use them ---
    import matplotlib.colors as mcolors
    if value_col.lower().startswith('model_b_intercept'):
        if vmin is not None and vmax is not None:
            plot_norm = mcolors.TwoSlopeNorm(vmin=float(vmin), vcenter=0.0, vmax=float(vmax))
        else:
            max_abs = np.nanpercentile(np.abs(valid[value_col].to_numpy(dtype=float)), 99)
            max_abs = max(float(max_abs) * 1.15, 0.08)
            plot_norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)
        plot_cmap = cmap
    elif value_col == 'NSE_Intercept_Effect':
        # Asymmetric norm — tight negative clip (-0.03) so negative wells spread
        # across the full red range; positive side up to +0.30.
        plot_norm = mcolors.TwoSlopeNorm(vmin=NSE_CLIP_NEG, vcenter=0.0, vmax=NSE_CLIP_POS)
        # Custom colormap: tops out at pale steel blue so no part of the positive
        # range goes dark navy (which looks identical to dark red at a glance).
        plot_cmap = mcolors.LinearSegmentedColormap.from_list(
            'RdWBu',
            [(0.0,  '#CC0000'),   # medium red      — strongly detrimental
             (0.30, '#FF9999'),   # pale red         — mildly detrimental
             (0.5,  '#FFFFFF'),   # white            — neutral
             (0.70, '#87CEEB'),   # sky blue         — mildly beneficial
             (0.85, '#4A90D9'),   # medium blue      — moderately beneficial
             (1.0,  '#1E6FBF')],  # deeper blue      — strongly beneficial (clipped max)
            N=256)
    else:
        max_abs = np.nanpercentile(np.abs(valid[value_col].to_numpy(dtype=float)), 99)
        max_abs = max(float(max_abs) * 1.15, 0.02)
        plot_norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)
        plot_cmap = cmap

    # --- Plot Wells by Cluster Shape ---
    handles = []
    scatter_kwargs = {'cmap': plot_cmap, 'norm': plot_norm, 'vmin': None, 'vmax': None}
    for cluster_id in sorted(valid['Cluster_ID'].dropna().unique()):
        marker = CLUSTER_MARKERS.get(int(cluster_id), 'o')
        cluster_points = valid[valid['Cluster_ID'] == cluster_id]
        sc = ax.scatter(
            cluster_points['Easting'],
            cluster_points['Northing'],
            c=cluster_points[value_col],
            cmap=scatter_kwargs['cmap'],
            s=120,
            marker=marker,
            edgecolor='black',
            linewidth=0.6,
            alpha=0.9,
            norm=scatter_kwargs['norm'],
            label=CLUSTER_LABELS.get(int(cluster_id), f"C{int(cluster_id)}")
        )
        handles.append(
            plt.Line2D([0], [0], marker=marker, color='w', label=CLUSTER_LABELS.get(int(cluster_id), f"C{int(cluster_id)}"),
                       markerfacecolor='gray', markeredgecolor='black', markersize=12, linestyle='None')
        )

    divider = make_axes_locatable(ax)
    cax_metric = divider.append_axes("right", size="2.75%", pad=0.598)
    cbar = fig.colorbar(sc, cax=cax_metric)
    if value_col == 'NSE_Intercept_Effect':
        cbar.set_label('NSE Intercept Effect (Model B - Model A)\nCEH3 = +8.93; clipped to −0.03 / +0.30', rotation=270, labelpad=32, fontsize=14)
        # Explicit ticks to ensure negative side is labelled — automatic
        # placement puts nearly all ticks on the positive side given the asymmetric norm.
        cbar.set_ticks([-0.03, -0.02, -0.01, 0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
        cbar.set_ticklabels(['-0.03', '-0.02', '-0.01', '0', '+0.05', '+0.10',
                             '+0.15', '+0.20', '+0.25', '+0.30'])
    else:
        cbar.set_label(value_col.replace('_', ' '), rotation=270, labelpad=32, fontsize=14)
    # Place DEM scale to the right of the metric scale.
    if dem_layer is not None:
        cax_dem = divider.append_axes("right", size="2.75%", pad=1.306)
        cbar_dem = fig.colorbar(dem_layer, cax=cax_dem, extend="both")
        cbar_dem.set_label("Elevation (m AOD)", rotation=270, labelpad=32, fontsize=14)
    ax.set_title(title, fontweight='bold')
    ax.set_xlabel('Easting (m)')
    ax.set_ylabel('Northing (m)')
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.set_aspect('equal', adjustable='box')
    # Add cluster shape legend (SSM04 style)
    cluster_legend = ax.legend(handles=handles, title="Core Cluster Assignments", loc='lower left', frameon=True)
    ax.add_artist(cluster_legend)
    if site_feature_handles:
        dedup = {}
        for handle in site_feature_handles:
            dedup[handle.get_label()] = handle
        ax.legend(handles=list(dedup.values()), loc='upper right', title="Site Features", frameon=True)
    # Keep both legends and two colorbars fully visible.
    plt.subplots_adjust(left=0.08, right=0.99, top=0.93, bottom=0.08)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()

if __name__ == '__main__':
    make_all_dirs()
    print('Starting SSM07 Site-Wide Intercept Audit...')
    wells_clean = pd.read_csv(WELLS_PATH, index_col=0, parse_dates=True)
    climate = pd.read_csv(CLIMATE_PATH, index_col=0, parse_dates=True)

    # Load clustered well set from 03_master_data.csv
    try:
        master_df = pd.read_csv(INT_MASTER_DATA)
        clustered_names = set(master_df['Name_Original'].apply(normalize_well_name))
    except Exception as e:
        print(f"[ERROR] Could not load clustered well set from {INT_MASTER_DATA}: {e}")
        clustered_names = set()

    # Filter wells to only those in the clustered set
    all_wells_norm = [normalize_well_name(c) for c in wells_clean.columns]
    candidate_wells = [c for c in wells_clean.columns if normalize_well_name(c) in clustered_names]
    excluded_wells = [c for c in wells_clean.columns if normalize_well_name(c) not in clustered_names]
    print(f" -> Filtered to {len(candidate_wells)} clustered wells from master data.")
    if excluded_wells:
        print(f" -> Excluded {len(excluded_wells)} wells not in cluster set: {', '.join(excluded_wells)}")
    else:
        print(" -> No wells excluded by cluster filter.")

    all_rows = []
    for well_col in candidate_wells:
        row, payload = compute_intercept_audit(well_col, wells_clean, climate)
        all_rows.append(row)
        
        # Plot the specific dual-pane figure for CEH14!
        if payload is not None and row['Well_Normalized'] == 'ceh14':
            plot_dual_showdown(OUT_07_CEH14_SHOWDOWN, payload)
            export_dual_showdown_data_csv(OUT_07_CEH14_SHOWDOWN_DATA, payload)
            print(f" -> Generated CEH14 Showdown Plot (Intercept = {payload['intercept']:.3f} m/month)")

    perf_df = pd.DataFrame(all_rows).dropna(subset=['Model_B_Intercept'])
    
    # Save CSV
    stats_csv = INT_INTERCEPT_METRICS
    perf_df.to_csv(stats_csv, index=False)
    print(f" -> Exported site-wide metrics to: {stats_csv.name}")

    # Merge coordinates for mapping
    if MASTER_PATH.exists():
        master_df = pd.read_csv(MASTER_PATH)
        master_df['Well_Normalized'] = master_df['Name_Original'].apply(normalize_well_name)
        
        # Merge clusters
        cluster_stats_path = INT_CLUSTER_STATS
        if cluster_stats_path.exists():
            cluster_df = pd.read_csv(cluster_stats_path)
            cluster_df['Match_ID'] = cluster_df['Match_ID'].apply(normalize_well_name)
            map_df = perf_df.merge(master_df[['Well_Normalized', 'Easting', 'Northing']], on='Well_Normalized')
            # Use 'Cluster' instead of 'Cluster_ID' for merging
            if 'Cluster' in cluster_df.columns:
                map_df = map_df.merge(cluster_df[['Match_ID', 'Cluster']], left_on='Well_Normalized', right_on='Match_ID', how='left')
                map_df = map_df.rename(columns={'Cluster': 'Cluster_ID'})
            else:
                print(f"[WARNING] 'Cluster' column not found in cluster_df. Available columns: {list(cluster_df.columns)}")
        else:
            map_df = perf_df.merge(master_df[['Well_Normalized', 'Easting', 'Northing']], on='Well_Normalized')

        # Robust symmetric bounds around zero to avoid color saturation in dense tails.
        model_b_abs = np.abs(pd.to_numeric(map_df['Model_B_Intercept'], errors='coerce').dropna().to_numpy(dtype=float))
        if model_b_abs.size:
            bound = max(float(np.nanpercentile(model_b_abs, 99)) * 1.15, 0.08)
        else:
            bound = 0.10

        # Map 1: The Hidden Plumbing (Intercept)
        plot_metric_map(
            map_df, 'Model_B_Intercept', 
            'Unmeasured Water Balance Residuals (Intercept \u03B1, m/month)', 
            OUT_07_PLUMBING_MAP, 
            cmap='RdBu', vmin=-bound, vmax=bound
        )
        
        # Map 2: The Forecasting Collapse (NSE Penalty)
        plot_metric_map(
            map_df, 'NSE_Intercept_Effect', 
            'Intercept Effect on NSE: Change in iterative simulation skill when a boundary term is introduced', 
            OUT_07_NSE_PENALTY_MAP, 
            cmap='RdBu'
        )

        # Merged spreadsheet combining both map datasets
        shared_cols = [c for c in ['Well', 'Easting', 'Northing', 'Cluster_ID'] if c in map_df.columns]
        merged_cols = shared_cols + [c for c in ['Model_B_Intercept', 'NSE_Intercept_Effect'] if c in map_df.columns]
        map_df[merged_cols].to_csv(OUT_07_MAPS_MERGED_DATA, index=False)
        print(" -> Generated Spatial Boundary Maps!")