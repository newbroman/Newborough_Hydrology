"""
Mask streams.kml to land — drop any segment below 1 m elevation.

Reads the raw GRASS r.watershed stream network and the LiDAR DEM, samples
elevation at each vertex of each LineString, and emits only the contiguous
land-side (DEM > 1 m) runs of vertices as a new LineString collection.

Inputs:
  /mnt/user-data/uploads/streams.kml    raw GRASS r.watershed output (4181 lines)
  data/newborough_dem.tif               2 m LiDAR DEM, EPSG:27700, range -2.06 to 53.46 m

Output:
  /mnt/user-data/outputs/streams.kml    masked replacement for data/streams.kml

Threshold: 1.0 m (everything below 1 m is treated as sea/intertidal).
"""
import warnings
warnings.filterwarnings("ignore")

import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import LineString
from pathlib import Path

# Configuration
INPUT_KML = Path("/mnt/user-data/uploads/streams.kml")
DEM_TIF   = Path("/home/claude/Newborough_Hydrology/data/newborough_dem.tif")
OUTPUT_KML = Path("/mnt/user-data/outputs/streams.kml")
LAND_THRESHOLD_M = 0.0
MIN_VERTICES_PER_LINE = 2  # need at least 2 vertices to form a line

# Read streams.kml and reproject to EPSG:27700 (DEM CRS)
print(f"Reading streams from: {INPUT_KML}")
gdf_in = gpd.read_file(INPUT_KML)
if gdf_in.crs is None:
    gdf_in.set_crs(epsg=4326, inplace=True)
gdf_in_27700 = gdf_in.to_crs("EPSG:27700")
print(f"  Input lines: {len(gdf_in_27700)}")
total_in_length_km = gdf_in_27700.geometry.length.sum() / 1000.0
print(f"  Input total length: {total_in_length_km:.2f} km")

# Open DEM
print(f"\nOpening DEM: {DEM_TIF}")
dem_src = rasterio.open(DEM_TIF)
print(f"  CRS: {dem_src.crs}, resolution: {dem_src.res}, threshold: {LAND_THRESHOLD_M} m")

# Mask each LineString
out_geoms = []
n_lines_unchanged = 0
n_lines_split = 0
n_lines_dropped = 0
n_lines_trimmed = 0
n_segments_out = 0

for idx, geom in enumerate(gdf_in_27700.geometry):
    if geom is None or geom.is_empty:
        n_lines_dropped += 1
        continue

    # All input features are LineString per our inspection; handle defensively
    lines = [geom] if geom.geom_type == "LineString" else list(geom.geoms)

    for line in lines:
        coords = list(line.coords)
        if len(coords) < 2:
            continue

        # Sample DEM at each vertex
        elevs = np.array([v[0] for v in dem_src.sample(coords)], dtype=float)
        is_land = elevs > LAND_THRESHOLD_M
        n_land = int(is_land.sum())

        if n_land == len(coords):
            # All vertices above threshold — keep whole line
            out_geoms.append(line)
            n_lines_unchanged += 1
            n_segments_out += 1
            continue

        if n_land == 0:
            # All vertices below threshold — drop entire line
            n_lines_dropped += 1
            continue

        # Mixed — extract contiguous runs of land vertices
        runs = []
        cur = []
        for c, on_land in zip(coords, is_land):
            if on_land:
                cur.append(c)
            else:
                if len(cur) >= MIN_VERTICES_PER_LINE:
                    runs.append(cur)
                cur = []
        if len(cur) >= MIN_VERTICES_PER_LINE:
            runs.append(cur)

        if not runs:
            n_lines_dropped += 1
            continue

        if len(runs) == 1 and len(runs[0]) < len(coords):
            n_lines_trimmed += 1
        elif len(runs) > 1:
            n_lines_split += 1
        else:
            n_lines_unchanged += 1

        for run in runs:
            out_geoms.append(LineString(run))
            n_segments_out += 1

dem_src.close()

# Build output GeoDataFrame and write KML
gdf_out_27700 = gpd.GeoDataFrame(geometry=out_geoms, crs="EPSG:27700")
gdf_out_4326 = gdf_out_27700.to_crs("EPSG:4326")

# Make sure KML driver is enabled
import fiona
fiona.drvsupport.supported_drivers["KML"] = "rw"
fiona.drvsupport.supported_drivers["LIBKML"] = "rw"

OUTPUT_KML.parent.mkdir(parents=True, exist_ok=True)
# Remove pre-existing output to ensure clean write
if OUTPUT_KML.exists():
    OUTPUT_KML.unlink()
gdf_out_4326.to_file(OUTPUT_KML, driver="KML")

# Summary
print(f"\n=== Masking summary ===")
print(f"Threshold:               {LAND_THRESHOLD_M} m AOD")
print(f"Input lines:             {len(gdf_in_27700)}")
print(f"  Unchanged (all land):  {n_lines_unchanged}")
print(f"  Trimmed (run ends):    {n_lines_trimmed}")
print(f"  Split (gaps):          {n_lines_split}")
print(f"  Dropped (all sea):     {n_lines_dropped}")
print(f"Output line segments:    {n_segments_out}")
total_out_length_km = gdf_out_27700.geometry.length.sum() / 1000.0
print(f"\nLength retained:         {total_out_length_km:.2f} km of {total_in_length_km:.2f} km "
      f"({100*total_out_length_km/total_in_length_km:.1f}%)")
print(f"\nOutput written to: {OUTPUT_KML}")
