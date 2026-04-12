"""
====================================================================================
EXPERIMENTAL SETUP MAPPING: HIERARCHICAL BACI DESIGN
====================================================================================
Purpose:
    Produces a publication-quality GIS map (EPSG:27700 / British National Grid)
    showing the spatial arrangement of monitoring wells relative to the two major
    anthropogenic interventions. 
    
    NEW IN THIS VERSION:
    Visualizes the Hierarchical Nested Control logic used in the scraping analysis 
    by physically drawing paired-control linkages between impact wells and their 
    designated geomorphological benchmarks.

Outputs:
    outputs/13_figure_experimental_design/13_01_experimental_setup_map.png
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    DATA_LOCATIONS_RAW,
    OUT_13_EXPERIMENTAL_MAP,
)
from utils.map_utils import add_kml_features
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd
import contextily as ctx
import fiona
from adjustText import adjust_text
from matplotlib.lines import Line2D

# Enable KML driver in GeoPandas/Fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

# ====================================================================================
# PATH CONFIGURATION
# ====================================================================================



make_all_dirs()

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

# ==========================================
# 1. LOAD SPATIAL DATASETS
# ==========================================
print("1. Loading spatial datasets...")

locs = pd.read_csv(DATA_LOCATIONS_RAW)
locs.rename(columns=lambda x: str(x).strip(), inplace=True)
locs['Match_ID'] = locs['Name'].astype(str).str.lower().str.replace(' ', '')
locs_clean = locs.dropna(subset=['E', 'N'])

# Restrict spatial extent to the study area
locs_clean = locs_clean[locs_clean['Match_ID'] != 'ceh12']
locs_clean = locs_clean[
    (locs_clean['E'] >= 240000) & (locs_clean['E'] <= 244000) &
    (locs_clean['N'] >= 362500) & (locs_clean['N'] <= 365000)
]

# Convert to GeoDataFrame
gdf_wells = gpd.GeoDataFrame(
    locs_clean,
    geometry=gpd.points_from_xy(locs_clean['E'], locs_clean['N']),
    crs="EPSG:27700"
)

# Load Clear-Fell KML Boundary
kml_file = DATA_DIR / 'clearfell.kml'
kml_clearfell_exists = os.path.exists(kml_file)
if kml_clearfell_exists:
    gdf_clearfell = gpd.read_file(kml_file, driver='KML').to_crs("EPSG:27700")

# ==========================================
# 2. CATEGORISE WELLS BY EXPERIMENTAL ROLE
# ==========================================
cf_impact = ['fe2', 'fe4', 'wmc3']
cf_edge = ['fe1', 'fe3', 'ceh31', 'lis1', 'ceh20', 'ceh30', 'ceh16', 'nw8b']
cf_control = ['ceh32', 'ceh34', 'ceh33', 'nw10', 'ceh19', 'ceh9', 'nw7', 'nw6']

scrape_impact  = ['ceh36', 'ceh18', 'ceh21']
scrape_local_control = ['ceh4', 'ceh22'] # The Local/Paired Controls
scrape_regional_control = ['ceh9', 'nw5', 'nw6', 'nw7', 'nw8', 'nw8b'] # The Regional Baseline

def assign_category(match_id: str) -> str:
    if match_id in cf_impact:      return 'Clear-Fell Impact'
    elif match_id in cf_edge: return 'Transition / Edge Zone'
    elif match_id in cf_control: return 'Regional Forest/Dune Controls'
    elif match_id in scrape_impact:  return 'Scraped Impact Site'
    elif match_id in scrape_local_control: return 'Local Paired Control'
    elif match_id in scrape_regional_control: return 'Regional Control Network'
    else:                          return 'Background Network'

gdf_wells['Category'] = gdf_wells['Match_ID'].apply(assign_category)

# The Hierarchical Linkages (Impact -> Local Control)
pairings = {
    'ceh36': 'ceh4',
    'ceh18': 'ceh4',
    'ceh21': 'ceh22'
}

# ==========================================
# 3. COLOUR-BLIND SAFE PALETTE
# ==========================================
CATEGORIES = [
    'Background Network',
    'Transition / Edge Zone',
    'Regional Forest/Dune Controls',
    'Clear-Fell Impact',
    'Regional Control Network',
    'Local Paired Control',
    'Scraped Impact Site',
]

COLORS = {
    'Clear-Fell Impact': '#D55E00',  # Vermillion
    'Transition / Edge Zone': '#FFB000',  # Lighter orange transition zone
    'Regional Forest/Dune Controls': '#009E73',  # Green
    'Scraped Impact Site': '#0072B2',  # Dark Blue
    'Local Paired Control': '#56B4E9',  # Sky blue
    'Regional Control Network': '#6F2DBD',  # Distinct purple vs forest/dune controls
    'Background Network':  '#A0A0A0',  # Grey
}

MARKERS = {
    'Clear-Fell Impact':   '^',   
    'Transition / Edge Zone': 'o',
    'Regional Forest/Dune Controls': 'o',
    'Scraped Impact Site': 's',   # Square
    'Local Paired Control':'D',   # Diamond
    'Regional Control Network': 'o', # Circle
    'Background Network':  'o',   
}

SIZES = {
    'Clear-Fell Impact':   150,
    'Transition / Edge Zone': 105,
    'Regional Forest/Dune Controls': 110,
    'Scraped Impact Site': 180,
    'Local Paired Control':150,
    'Regional Control Network': 100,
    'Background Network':   60,
}

# ==========================================
# 4. GENERATE FIGURE
# ==========================================
print("2. Generating figure...")
fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
texts = []
MAP_XMIN, MAP_XMAX = 240500, 243500
MAP_YMIN, MAP_YMAX = 362700, 364800

# Layer 1: Clear-fell polygon
if kml_clearfell_exists:
    gdf_clearfell.plot(ax=ax, facecolor='#D55E00', edgecolor='darkred', alpha=0.15, linewidth=2, zorder=1)

# Layer 2: Draw the Paired-Control Linkages
print("   -> Drawing hierarchical pairings...")
pairing_lines = [] # <--- ADD THIS LIST
for impact_id, control_id in pairings.items():
    impact_row = gdf_wells[gdf_wells['Match_ID'] == impact_id]
    control_row = gdf_wells[gdf_wells['Match_ID'] == control_id]
    
    if not impact_row.empty and not control_row.empty:
        x_vals = [impact_row.iloc[0]['E'], control_row.iloc[0]['E']]
        y_vals = [impact_row.iloc[0]['N'], control_row.iloc[0]['N']]
        
        # Save the line object as it draws
        line, = ax.plot(x_vals, y_vals, color='red', linestyle='--', linewidth=2.5, alpha=0.8, zorder=2)
        pairing_lines.append(line)

ax.plot([], [], color='red', linestyle='--', linewidth=2.5, alpha=0.8, label='BACI Paired Linkage')

# Layer 3: Well markers
for cat in CATEGORIES:
    subset = gdf_wells[gdf_wells['Category'] == cat]
    if subset.empty: continue
    
    # Don't add 'Background Network' to the legend to keep it clean, just plot it
    label_val = cat if cat != 'Background Network' else "_nolegend_"
    
    subset.plot(ax=ax, color=COLORS[cat], marker=MARKERS[cat], markersize=SIZES[cat], 
                edgecolor='black', label=label_val, alpha=0.9, zorder=3)
    
    for _, row in subset.iterrows():
        is_bg = (cat == 'Background Network')
        # Only label wells inside the displayed map window; clip labels to axes.
        if (MAP_XMIN <= row['E'] <= MAP_XMAX) and (MAP_YMIN <= row['N'] <= MAP_YMAX):
            texts.append(ax.text(row['E'], row['N'], row['Name'], 
                                 fontsize=8 if is_bg else 10, fontweight='normal' if is_bg else 'bold',
                                 color='#555555' if is_bg else 'black', zorder=4, clip_on=True))


# --- DEM Basemap Layer ---
import matplotlib.colors as mcolors
import numpy as np
dem_path = DATA_DIR / "newborough_dem.tif"
dem_loaded = False
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
                              norm=div_norm, extent=extent, origin="upper", zorder=0)
        cbar_dem = fig.colorbar(dem_layer, ax=ax, shrink=0.55, pad=0.02, extend="both")
        cbar_dem.set_label("Elevation (m AOD)", rotation=270, labelpad=18)
        dem_loaded = True
except Exception as e:
    print(f"DEM load failed: {e}. Falling back to OSM.")
    import contextily as ctx
    ctx.add_basemap(ax, crs=gdf_wells.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik, zorder=0, alpha=0.7)

# --- KML Site Features (via map_utils — includes broadleaf restock block) ---
add_kml_features(ax, DATA_DIR)

# --- Clearfell centroid marker ---
CENTROID_E, CENTROID_N = 241177, 363645
ax.plot(CENTROID_E, CENTROID_N, marker='+', color='darkred',
        markersize=14, markeredgewidth=2.5, zorder=6)
ax.annotate('Clearfell\ncentroid', xy=(CENTROID_E, CENTROID_N),
            xytext=(CENTROID_E - 180, CENTROID_N - 120),
            fontsize=8, color='darkred',
            arrowprops=dict(arrowstyle='-', color='darkred', lw=0.8))

# --- Clearfell transect: CEH2 → CEH34 → WMC3 ---
transect_wells = ['ceh2', 'ceh34', 'wmc3']
transect_coords = []
for wid in transect_wells:
    row = gdf_wells[gdf_wells['Match_ID'] == wid]
    if not row.empty:
        transect_coords.append((row.iloc[0]['E'], row.iloc[0]['N'], wid))

if len(transect_coords) == 3:
    xs = [c[0] for c in transect_coords]
    ys = [c[1] for c in transect_coords]
    ax.plot(xs, ys, color='#AACC00', linestyle='--', linewidth=2.0,
            alpha=0.85, zorder=5, label='Clearfell transect')
    # Annotate distances from centroid
    import math
    for ex, ny, wid in transect_coords:
        dist = math.sqrt((ex - CENTROID_E)**2 + (ny - CENTROID_N)**2)
        ax.annotate(f'{dist:.0f} m', xy=(ex, ny),
                    xytext=(ex + 60, ny + 60),
                    fontsize=7, color='#AACC00',
                    arrowprops=dict(arrowstyle='-', color='#AACC00', lw=0.5))

# ==========================================
# 5. FORMATTING
# ==========================================
ax.set_xlim(MAP_XMIN, MAP_XMAX)
ax.set_ylim(MAP_YMIN, MAP_YMAX)

plt.title('Hierarchical Experimental Design: Clear-Fell and Topographical Interventions', fontsize=14, fontweight='bold', pad=12)
plt.xlabel('Easting (m, OSGB36)')
plt.ylabel('Northing (m, OSGB36)')

legend_handles = [
    Line2D([], [], linestyle='none', label='Clear-Fell Experiment (BACI)'),
    Line2D([], [], marker='^', linestyle='None', markerfacecolor=COLORS['Clear-Fell Impact'], markeredgecolor='black', markersize=9, label='Impact (Felled Zone)'),
    Line2D([], [], marker='o', linestyle='None', markerfacecolor=COLORS['Transition / Edge Zone'], markeredgecolor='black', markersize=9, label='Transition / Edge Zone'),
    Line2D([], [], marker='o', linestyle='None', markerfacecolor=COLORS['Regional Forest/Dune Controls'], markeredgecolor='black', markersize=9, label='Regional Controls (8 wells)'),
    Line2D([], [], color='darkorange', linestyle='-.', linewidth=2.2, label='Clear-Fell Boundary'),
    Line2D([], [], marker='+', linestyle='None', color='darkred', markersize=10, markeredgewidth=2.5, label='Clearfell centroid'),
    Line2D([], [], color='#AACC00', linestyle='--', linewidth=2.0, label='Clearfell transect (CEH2→CEH34→WMC3)'),
    Line2D([], [], linestyle='none', label='Topographical Scraping'),
    Line2D([], [], marker='s', linestyle='None', markerfacecolor=COLORS['Scraped Impact Site'], markeredgecolor='black', markersize=9, label='Scraped Impact Site'),
    Line2D([], [], marker='D', linestyle='None', markerfacecolor=COLORS['Local Paired Control'], markeredgecolor='black', markersize=9, label='Local Paired Control'),
    Line2D([], [], marker='o', linestyle='None', markerfacecolor=COLORS['Regional Control Network'], markeredgecolor='black', markersize=9, label='Regional Control Network'),
    Line2D([], [], linestyle='none', label='Analytical Linkages'),
    Line2D([], [], color='red', linestyle='--', linewidth=2.5, alpha=0.8, label='BACI Paired Linkage'),
]
ax.legend(
    handles=legend_handles,
    title='Monitoring Role & Logic',
    fontsize=10,
    title_fontsize=11,
    loc='upper right',
    bbox_to_anchor=(0.98, 0.98),
    frameon=True,
    facecolor='white',
    edgecolor='black'
)

plt.grid(True, linestyle='--', alpha=0.4)

print("4. Repelling text labels...")
adjust_text(texts, arrowprops=dict(arrowstyle="-", color='gray', lw=0.5), ax=ax)

plt.tight_layout()
output_file = OUT_13_EXPERIMENTAL_MAP
plt.savefig(output_file, bbox_inches='tight', dpi=300)
plt.close(fig)

print(f"\nSuccess! Reviewer-ready GIS map saved as '{output_file}'.")