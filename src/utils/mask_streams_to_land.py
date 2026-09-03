"""
Mask a GRASS stream network to land — drop any vertex run at or below the
land threshold, and emit the surviving runs as a new LineString collection.

This is a PROVENANCE UTILITY, not a pipeline step. It is the tool that made
`data/geo/streams.kml`, kept so that file's derivation is documented in code
rather than only in prose. `run_analysis.py` never calls it and nothing
imports it.

Inputs:
  data/geo/streams_raw.kml       the GRASS r.watershed line export (4181
                                 LineStrings). NOT COMMITTED — see the
                                 provenance note below.
  data/geo/newborough_dem.tif    2 m LiDAR DEM, EPSG:27700, -2.06 to 53.46 m
                                 (paths.DATA_DEM)

Output:
  data/geo/streams_masked.kml    a NEW file. Promoting it over the live
                                 data/geo/streams.kml is a deliberate manual
                                 step, never a side effect of running this.

PROVENANCE: THE CHAIN IS DOCUMENTED, THE INTERMEDIATE IS NOT COMMITTED.
  GEO_PROVENANCE.md records `streams.kml` as derived from `site_boundary.kml`
  (D-082, confirmed by Martin 2026-08-29). That file holds **11,715 Polygons**;
  this module reads **LineStrings**, and the committed `streams.kml` holds
  3,045 of them. So site_boundary.kml is not the file this module was run on —
  there was a line export between the two, and it is not in the repository.
  `streams.kml` is therefore not reproducible from the committed tree, which
  Martin accepted on 2026-09-03: full traceability would be better, and the
  derivation is at least written down in GEO_PROVENANCE.md and here. Pointing
  INPUT_KML at site_boundary.kml would fail on `line.coords`, so it is not
  pointed there.

THRESHOLD: 0.0 m, SETTLED.
  This docstring said 1.0 m until 2026-09-03 while the code said 0.0. The code
  is what produced the committed artefact, and Martin ruled the same day that
  0.0 is correct and `streams.kml` stands as it is; the docstring is corrected
  to match the code. Everything at or below 0.0 m AOD is treated as
  sea/intertidal.

WHY THE __main__ GUARD MATTERS HERE MORE THAN ANYWHERE ELSE.
  Every statement below used to sit at module level, so importing this module
  RAN it — the `1 raise` in `import_audit`, harmless only because the sandbox
  input path did not exist. Repointing the paths at `data/` WITHOUT the guard
  would have converted a harmless raise into a silent rewrite of a committed
  geometry file that Scripts 18, 20 and `map_utils` all read. D-120.

Usage:
    python3 src/utils/mask_streams_to_land.py [--force]
"""
import warnings
warnings.filterwarnings("ignore")

__version__ = "1.1.0"  # Hollingham (2026) — 2026-09-03. Body wrapped in main()
#   with a __main__ guard, and the two /mnt/user-data sandbox paths repointed
#   into data/geo via paths.py. Output goes to a NEW file and refuses to
#   overwrite without --force; a missing input reports rather than tracebacks.
#   The masking algorithm is untouched, and the 0.0 m threshold stands
#   (Martin, 2026-09-03). D-120; work register T17.

import sys
from pathlib import Path

import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import LineString

# Resolve data locations from paths.py (single source of truth) rather than
# hardcoded absolute paths. This module lives in src/utils/ alongside paths.py;
# add that directory to sys.path so the import resolves when the utility is run
# standalone from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DATA_DEM, DATA_GEO_DIR                       # noqa: E402

# Configuration
INPUT_KML  = DATA_GEO_DIR / "streams_raw.kml"
DEM_TIF    = DATA_DEM                      # data/geo/newborough_dem.tif
OUTPUT_KML = DATA_GEO_DIR / "streams_masked.kml"
LAND_THRESHOLD_M = 0.0
MIN_VERTICES_PER_LINE = 2  # need at least 2 vertices to form a line


def main(force: bool = False) -> int:
    if not INPUT_KML.exists():
        print(f"input not found: {INPUT_KML}")
        print("  The GRASS line export is not committed — see the provenance "
              "gap in this module's docstring and data/geo/GEO_PROVENANCE.md.")
        return 2
    if OUTPUT_KML.exists() and not force:
        print(f"refusing to overwrite {OUTPUT_KML} — pass --force")
        return 2

    # Read the stream lines and reproject to EPSG:27700 (DEM CRS).
    # read_kml registers both drivers and falls back to XML.
    print(f"Reading streams from: {INPUT_KML}")
    from kml_io import read_kml                                # noqa: E402
    gdf_in_27700 = read_kml(INPUT_KML, "EPSG:27700")
    print(f"  Input lines: {len(gdf_in_27700)}")
    total_in_length_km = gdf_in_27700.geometry.length.sum() / 1000.0
    print(f"  Input total length: {total_in_length_km:.2f} km")

    # Open DEM
    print(f"\nOpening DEM: {DEM_TIF}")
    dem_src = rasterio.open(DEM_TIF)
    print(f"  CRS: {dem_src.crs}, resolution: {dem_src.res}, "
          f"threshold: {LAND_THRESHOLD_M} m")

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
    print("\n=== Masking summary ===")
    print(f"Threshold:               {LAND_THRESHOLD_M} m AOD")
    print(f"Input lines:             {len(gdf_in_27700)}")
    print(f"  Unchanged (all land):  {n_lines_unchanged}")
    print(f"  Trimmed (run ends):    {n_lines_trimmed}")
    print(f"  Split (gaps):          {n_lines_split}")
    print(f"  Dropped (all sea):     {n_lines_dropped}")
    print(f"Output line segments:    {n_segments_out}")
    total_out_length_km = gdf_out_27700.geometry.length.sum() / 1000.0
    print(f"\nLength retained:         {total_out_length_km:.2f} km of "
          f"{total_in_length_km:.2f} km "
          f"({100*total_out_length_km/total_in_length_km:.1f}%)")
    print(f"\nOutput written to: {OUTPUT_KML}")
    print("  This is a NEW file. Promoting it over data/geo/streams.kml is a "
          "deliberate step — Scripts 18, 20 and map_utils all read that file.")
    return 0


if __name__ == "__main__":
    sys.exit(main(force="--force" in sys.argv[1:]))
