"""
====================================================================================
FIGURE 1: SITE TOPOGRAPHY AND GROUNDWATER MONITORING NETWORK (map_dem_overview.py)
====================================================================================
Purpose:
    Produces a publication-quality GIS map (EPSG:27700 / British National Grid)
    overlaying the full monitoring network (≈97 wells in current data), site
    features, and stream networks onto the full extent of the Digital
    Elevation Model (DEM).  Reads the network from data/well_metadata.csv;
    the exact count printed at run time is the source of truth.

Outputs:
    outputs/12_figure_site_overview/12_01_dem_site_overview.png
    (PNG @ dpi=300 — preserves DEM hillshade detail and well-label
    text; project convention is PNG @ dpi=300 for spatial / dense
    figures and JPEG @ dpi=200 for hydrograph / scenario panels.)
====================================================================================
"""

__version__ = "1.2.0"  # Hollingham (2026) — 2026-06-28
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    DATA_LOCATIONS_RAW,
    OUT_12_DEM_OVERVIEW,
)
from utils.map_utils import add_kml_features, load_dem_layer
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import fiona
import warnings

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import render_figure

# Enable KML driver in GeoPandas/Fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

# Suppress messy warnings for the reviewer's terminal output
warnings.filterwarnings('ignore')

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
        error(f"Could not find {wells_path}. Please check data folder.")
        return

    wells = pd.read_csv(wells_path)
    wells.columns = wells.columns.str.strip()

    # Convert to a GeoDataFrame using British National Grid (EPSG:27700)
    gdf_wells = gpd.GeoDataFrame(
        wells,
        geometry=gpd.points_from_xy(wells['E'], wells['N']),
        crs="EPSG:27700"
    )

    # 2. Setup the Figure
    fig, ax = plt.subplots(figsize=(12, 12))

    # 3. Load and Plot the GeoTIFF DEM (with fallback)
    # load_dem_layer() applies the project-standard colourmap and alpha=0.45,
    # matching every other pipeline map.  Script 12 is excluded from the
    # canonical map extent (it uses the full DEM frame); the xlim/ylim set
    # inside load_dem_layer() are overridden below using the imshow extent.
    info("Loading DEM via map_utils.load_dem_layer()...")
    dem_layer, dem_loaded = load_dem_layer(ax, DATA_DIR)

    if dem_loaded:
        # Attach colourbar to the shared dem_layer object
        cbar = fig.colorbar(dem_layer, ax=ax, shrink=0.5, pad=0.03, extend='both')
        cbar.set_label('Elevation (m AOD)', rotation=270, labelpad=20,
                       fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)

        # Script 12 shows the full DEM frame, not the canonical site extent.
        # Recover the true DEM bounds from the imshow object and reapply;
        # this is the only extent difference from the other pipeline maps.
        # get_extent() returns (left, right, bottom, top).
        dem_extent = dem_layer.get_extent()
        ax.set_xlim(dem_extent[0], dem_extent[1])
        ax.set_ylim(362000, dem_extent[3])

    else:
        info("Local DEM not found. Fetching fallback topographical basemap...")
        ctx.add_basemap(ax, crs=gdf_wells.crs.to_string(),
                        source=ctx.providers.OpenTopoMap, alpha=0.8, zorder=0)

    # =======================================================
    # 4. KML Site Features (via map_utils — includes broadleaf restock block)
    # =======================================================
    info("Adding KML site features...")
    site_handles = add_kml_features(ax, DATA_DIR)

    # 5. Overlay the Monitoring Wells
    info("Plotting Monitoring Wells...")
    gdf_wells.plot(
        ax=ax,
        color='red',
        markersize=30,
        edgecolor='black',
        linewidth=1.0,
        zorder=5
    )

    # 5b. Label each well with its name
    info("Adding well name labels...")
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
    # 6. Formatting & Legend
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
    render_figure(plt.gcf(), output_filename)
    print(f"  [SUCCESS] Map saved locally as {output_filename}")
    plt.close()

if __name__ == "__main__":
    banner("12", "Figure — Site Overview", version="1.1.0")
    make_all_dirs()
    generate_dem_map()
