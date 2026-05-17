"""
====================================================================================
FIGURE 1: SITE TOPOGRAPHY AND GROUNDWATER MONITORING NETWORK (map_dem_overview.py)
====================================================================================
Purpose:
    Produces a publication-quality GIS map (EPSG:27700 / British National Grid)
    overlaying the full monitoring network (≈97 wells in current data), site
    features, and stream networks onto the full extent of the Digital
    Elevation Model (DEM).  Reads the network from data/Well_locations_height.csv;
    the exact count printed at run time is the source of truth.

Outputs:
    outputs/12_figure_site_overview/12_01_dem_site_overview.png
    (PNG @ dpi=300 — preserves DEM hillshade detail and well-label
    text; project convention is PNG @ dpi=300 for spatial / dense
    figures and JPEG @ dpi=200 for hydrograph / scenario panels.)
====================================================================================
"""

__version__ = "1.0.1"  # Hollingham (2026) — 2026-05-17
# 1.0.1 — Doc-sweep S.8: updated docstring well count (was stale "71-well",
#         now "≈97 wells in current data") (Item 11); removed dead
#         out_dir / os.makedirs lines that built an unused ../outputs path
#         (Item 12); added PNG@dpi=300 format note in Outputs docstring
#         (Item 13).  Patch — no functional change.
# 1.0.x — Initial.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    DATA_LOCATIONS_RAW,
    OUT_12_DEM_OVERVIEW,
)
from utils.map_utils import add_kml_features
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import fiona
import warnings
import matplotlib.patches as mpatches

# Enable KML driver in GeoPandas/Fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

# Suppress messy warnings for the reviewer's terminal output
warnings.filterwarnings('ignore')

try:
    import rasterio
    from rasterio.plot import show
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

# Publication-quality typography
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
})

def generate_dem_map():
    print("\n" + "="*60)
    print(" GENERATING FIGURE 1: FULL DEM AND SITE OVERVIEW")
    print("="*60)

    # 1. Load the Well Data
    # (Output paths are sourced from utils.paths; no per-script
    # ../outputs directory is needed.)
    wells_path = DATA_LOCATIONS_RAW
    if not os.path.exists(wells_path):
        print(f"  [ERROR] Could not find {wells_path}. Please check data folder.")
        return

    wells = pd.read_csv(wells_path)
    wells.columns = wells.columns.str.strip()

    # Convert to a GeoDataFrame using British National Grid (EPSG:27700)
    gdf_wells = gpd.GeoDataFrame(
        wells, 
        geometry=gpd.points_from_xy(wells['E'], wells['N']),
        crs="EPSG:27700"
    )

    # 3. Setup the Figure
    fig, ax = plt.subplots(figsize=(12, 12))
    
 # 4. Load and Plot the GeoTIFF DEM (with fallback)
    dem_path   = DATA_DIR / "newborough_dem.tif"
    dem_loaded = False
    
    if RASTERIO_AVAILABLE and os.path.exists(dem_path):
        print("  [INFO] High-resolution local DEM found. Applying native Land/Sea mapping...")
        import matplotlib.colors as mcolors
        import numpy as np
        
        with rasterio.open(dem_path) as src:
            # 1. Read the raw pixels and the bounding box
            dem_data = src.read(1)
            extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
            
            # 2. Safely mask out any "NoData" background pixels
            if src.nodata is not None:
                dem_data = np.ma.masked_where(dem_data == src.nodata, dem_data)
                
            actual_min = dem_data.min()
            actual_max = dem_data.max()
            
            # 3. Create the custom Topo Colormap
            terrain_cmap = plt.cm.terrain
            terrain_colors = terrain_cmap(np.linspace(0.25, 1.0, 256))
            custom_topo = mcolors.LinearSegmentedColormap.from_list('custom_topo', terrain_colors)
            
            # THE MAGIC TRICK: Set the "under" color.
            # Anything below our vmin (0m) will automatically be painted blue on the map,
            # AND the colorbar will show a blue arrow at the bottom!
            custom_topo.set_under('dodgerblue')
            
            # Anchor the bottom strictly at 0m, bend at 12m, max at true ridge height
            div_norm = mcolors.TwoSlopeNorm(vmin=0, vcenter=12.0, vmax=actual_max)
            
            # 4. Plot the DEM (one layer does it all now!)
            dem_layer = ax.imshow(dem_data, cmap=custom_topo, alpha=0.85,
                                  norm=div_norm, extent=extent, origin='upper', zorder=1)
            
            # 5. Add the Colorbar 
            # extend='both' will automatically color the bottom arrow 'dodgerblue'
            cbar = fig.colorbar(dem_layer, ax=ax, shrink=0.5, pad=0.03, extend='both')
            cbar.set_label('Elevation (m AOD)', rotation=270, labelpad=20, 
                           fontsize=12, fontweight='bold')
            cbar.ax.tick_params(labelsize=10)
            
            dem_loaded = True
            
            # 6. CROP THE MAP EXTENT
            ax.set_xlim(extent[0], extent[1])
            # Override the original extent[2] bottom boundary with 362000
            ax.set_ylim(362000, extent[3])
    else:
        print("  [INFO] Local DEM not found. Fetching fallback topographical basemap...")
        ctx.add_basemap(ax, crs=gdf_wells.crs.to_string(), 
                        source=ctx.providers.OpenTopoMap, alpha=0.8, zorder=0)
    # =======================================================
    # 5. KML Site Features (via map_utils — includes broadleaf restock block)
    # =======================================================
    print("  [INFO] Adding KML site features...")
    site_handles = add_kml_features(ax, DATA_DIR)

    # 6. Overlay the Monitoring Wells
    print("  [INFO] Plotting Monitoring Wells...")
    gdf_wells.plot(
        ax=ax, 
        color='red', 
        markersize=30, 
        edgecolor='black', 
        linewidth=1.0,
        zorder=5
    )

    # 6b. Label each well with its name
    print("  [INFO] Adding well name labels...")
    import matplotlib.patheffects as pe
    for _, row in gdf_wells.iterrows():
        ax.annotate(
            row['Name'],
            xy=(row['E'], row['N']),
            xytext=(4, 4),
            textcoords='offset points',
            fontsize=5,
            color='black',
            fontweight='bold',
            zorder=6,
            path_effects=[pe.withStroke(linewidth=1.5, foreground='white')],
        )

    # If DEM didn't load, frame around the wells instead
    if not dem_loaded:
        x_min, y_min, x_max, y_max = gdf_wells.total_bounds
        buffer = 300
        ax.set_xlim(x_min - buffer, x_max + buffer)
        ax.set_ylim(y_min - buffer, y_max + buffer)

  # =======================================================
    # 7. Formatting & Legend
    # =======================================================
    plt.title('Figure 1: Site Topography and Hydrogeological Features', 
              fontweight='bold', fontsize=16, pad=15)
    plt.xlabel('Easting (m, OSGB36)')
    plt.ylabel('Northing (m, OSGB36)')
    
    # Custom Legend — well marker plus site feature handles from add_kml_features
    from matplotlib.lines import Line2D
    well_handle = Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
                         markeredgecolor='black', markersize=8,
                         label=f'Monitoring Wells (n={len(gdf_wells)})')
    ax.legend(handles=[well_handle] + list(site_handles),
              loc='lower left', framealpha=0.9, edgecolor='black')
    
    # Save in high resolution to outputs folder
    output_filename = OUT_12_DEM_OVERVIEW
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"  [SUCCESS] Map saved locally as {output_filename}")
    plt.close()
if __name__ == "__main__":
    make_all_dirs()
    generate_dem_map()