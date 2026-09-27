#!/usr/bin/env python3
"""Write `data/geo/study_area.geojson` — the study-area boundary, from the DEM.

WHAT IT REPLACES. `data/geo/hydrological study area.kml` is Martin's hand-drawn
polygon (2026-09-20, E27), drawn roughly on catchment boundaries. This tool puts
the landward edges on the catchments themselves, so the boundary is reproducible
from committed inputs, and keeps the hand-drawn line only where the DEM cannot
decide. The edges, as Martin set them on 2026-09-27 (D-203):

  north     the ridge-crest divides: the GRASS surface basins listed in
            BASIN_SEEDS (the north-west basin is deliberately not among them);
  east      the river channel: the single-flow path from RIVER_START, the point
            where the ridge-foot drain meets the northern divide, down into the
            estuary; everything east of it is outside;
  south-east the hand-drawn edge, unchanged (hand vertices HAND_SE);
  south-west the Caernarfon Bay high-water mark (coastline_hwm.geojson);
  west      the hand-drawn line, west of WEST_LIMIT_E — the western basin runs
            into the DEM's edge at 240,000 E, so the DEM cannot place it.

RECIPE. GRASS 8.3.2 on the committed 2 m DEM, the same single-flow routing that
reproduces streams.kml (D-082):
    r.watershed -s elevation=dem threshold=BASIN_THRESHOLD basin=bas drainage=dir
    r.path input=dir start_coordinates=RIVER_START vector_path=river
The basin raster is polygonised in Python, the selected basins are dissolved,
then clipped to the land side of the HWM, cut along the river and along the
hand-drawn south-east edge, and joined to the hand-drawn west end. Basins are
chosen by SEED COORDINATE, never by basin number: GRASS numbers basins in
processing order, which is not a property of the terrain.

NOT A PIPELINE STEP. It needs GRASS, which the pipeline machine does not carry;
run it wherever GRASS is installed. The committed GeoJSON is the artefact the
pipeline reads, and `--check` rebuilds it and compares.

Usage:
    python3 tools/make_study_area.py            # build and write
    python3 tools/make_study_area.py --check    # rebuild, compare with the committed file
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-27. New: the DEM-derived
#   study-area boundary (D-203), approved by Martin 2026-09-27.

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import geopandas as gpd                                       # noqa: E402
import numpy as np                                            # noqa: E402
import rasterio                                               # noqa: E402
from rasterio.features import shapes                          # noqa: E402
from shapely.geometry import (LineString, Point, Polygon,     # noqa: E402
                              box, mapping, shape)
from shapely.ops import linemerge, split, unary_union         # noqa: E402

from utils.kml_io import read_kml                             # noqa: E402
from utils.paths import (DATA_COASTLINE_HWM, DATA_DEM,        # noqa: E402
                         DATA_KML_STUDY_AREA, DATA_STUDY_AREA_GEOJSON)

# ── The boundary's definition (D-203). Coordinates are EPSG:27700 metres. ──────
BASIN_THRESHOLD = 100_000          # cells (40 ha at 2 m): the basin scale Martin chose from
BASIN_SEEDS = [                     # one interior point per included basin
    (242525, 364637), (243224, 363091), (240306, 363045), (240488, 363271),
    (240836, 364279), (240296, 363993), (241155, 363549), (242710, 363024),
    (242334, 363655), (242135, 362957), (241430, 363204), (242363, 361891),
]
RIVER_START = (243181, 364711)     # ridge-foot drain at the northern divide
HAND_SE = [(242295, 362076), (242574, 362302), (242949, 362588),
           (243274, 362787), (243526, 362972), (243771, 363272)]
WEST_LIMIT_E = 240200              # hand-drawn line west of this easting
WEST_BAND_N = (363300, 364700)     # northing band of the western hand-drawn stretch
INLAND_POINT = (242000, 364500)    # any point certainly on land, to pick the land side
FAR = 20_000                       # m: how far cut lines are carried beyond the site
CHECK_TOL_M2 = 1.0                 # --check: symmetric difference allowed, m²


def _grass(script: str, workdir: Path) -> None:
    """Run a GRASS shell script in a throwaway EPSG:27700 location."""
    exe = shutil.which("grass")
    if exe is None:
        sys.exit("make_study_area: GRASS is not installed here (it is not on the pipeline "
                 "machine by design); run this where `grass` is on PATH.")
    loc = workdir / "loc"
    subprocess.run([exe, "-c", "EPSG:27700", "-e", str(loc)], check=True,
                   capture_output=True)
    sh = workdir / "run.sh"
    sh.write_text(script)
    subprocess.run([exe, str(loc / "PERMANENT"), "--exec", "bash", str(sh)], check=True,
                   capture_output=True)


def build() -> Polygon:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        bas_tif, river_gpkg = td / "bas.tif", td / "river.gpkg"
        _grass(f"""set -e
r.in.gdal -o input="{DATA_DEM}" output=dem --q
g.region raster=dem
r.watershed -s elevation=dem threshold={BASIN_THRESHOLD} basin=bas drainage=dir --q
r.path input=dir format=auto start_coordinates={RIVER_START[0]},{RIVER_START[1]} vector_path=river --q
r.out.gdal -c input=bas output="{bas_tif}" --q
v.out.ogr input=river output="{river_gpkg}" format=GPKG --q
""", td)
        with rasterio.open(bas_tif) as src:
            B = src.read(1)
            ids = set()
            for x, y in BASIN_SEEDS:
                r, c = src.index(x, y)
                ids.add(int(B[r, c]))
            nodata = src.nodata
            if nodata is not None and int(nodata) in ids:
                sys.exit("make_study_area: a basin seed fell on nodata — the basins moved")
            sel = np.isin(B, sorted(ids)).astype("uint8")
            basins = unary_union([shape(g) for g, _ in
                                  shapes(sel, mask=sel == 1, transform=src.transform)])
        river = unary_union(list(gpd.read_file(river_gpkg).geometry))
        if river.geom_type == "MultiLineString":
            river = linemerge(river)
    if river.geom_type != "LineString":
        sys.exit(f"make_study_area: the river path is a {river.geom_type}, expected one line")

    x0, y0, x1, y1 = basins.bounds
    world = box(x0 - FAR, y0 - FAR, x1 + FAR, y1 + FAR)

    # land side of the HWM: carry the line's ends out horizontally and split
    with open(DATA_COASTLINE_HWM, encoding="utf-8") as f:
        cj = json.load(f)
    cc = list(shape(cj["features"][0]["geometry"]).coords)
    coast = LineString([(cc[0][0] - FAR, cc[0][1])] + cc + [(cc[-1][0] + FAR, cc[-1][1])])
    land = next(p for p in split(world, coast).geoms if p.contains(Point(INLAND_POINT)))

    # east of the river is outside: carry the path north from its start and east from its end
    rc = list(river.coords)
    cut = LineString([(rc[0][0], y1 + FAR)] + rc + [(x1 + FAR, rc[-1][1])])
    east = next(p for p in split(world, cut).geoms if not p.contains(Point(INLAND_POINT)))

    # south-east of the hand-drawn edge is outside
    se = Polygon(HAND_SE + [(x1 + FAR, HAND_SE[-1][1]), (x1 + FAR, y0 - FAR),
                            (HAND_SE[0][0], y0 - FAR)])

    area = basins.intersection(land).difference(east).difference(se)

    # the hand-drawn west end
    hand = unary_union(list(read_kml(DATA_KML_STUDY_AREA, quiet=True).geometry))
    west = hand.intersection(box(x0 - FAR, WEST_BAND_N[0], WEST_LIMIT_E, WEST_BAND_N[1]))
    area = unary_union([area, west.intersection(land)])
    if area.geom_type == "MultiPolygon":
        area = max(area.geoms, key=lambda p: p.area)
    return Polygon(area.exterior)


def _feature(poly: Polygon) -> dict:
    return {
        "type": "FeatureCollection",
        "name": "study_area",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::27700"}},
        "features": [{
            "type": "Feature",
            "properties": {
                "source": "tools/make_study_area.py " + __version__,
                "method": ("GRASS r.watershed -s basins (threshold "
                           f"{BASIN_THRESHOLD}) by seed; east edge the r.path river from "
                           f"{RIVER_START}; HWM coast; hand-drawn south-east edge and west end"),
                "decision": "D-203",
                "made": date.today().isoformat(),
                "area_m2": poly.area,
            },
            "geometry": mapping(poly),
        }],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="rebuild and compare, write nothing")
    args = ap.parse_args()
    poly = build()
    if args.check:
        if not DATA_STUDY_AREA_GEOJSON.exists():
            print(f"make_study_area --check: {DATA_STUDY_AREA_GEOJSON.name} is missing")
            return 1
        with open(DATA_STUDY_AREA_GEOJSON, encoding="utf-8") as f:
            old = shape(json.load(f)["features"][0]["geometry"])
        diff = old.symmetric_difference(poly).area
        ok = diff <= CHECK_TOL_M2
        print(f"make_study_area --check: {'OK' if ok else 'FAIL'} — rebuilt {poly.area / 1e4:.3f} ha, "
              f"committed {old.area / 1e4:.3f} ha, symmetric difference {diff:.3f} m²")
        return 0 if ok else 1
    with open(DATA_STUDY_AREA_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(_feature(poly), f)
    print(f"wrote {DATA_STUDY_AREA_GEOJSON}: {poly.area / 1e4:.3f} ha, "
          f"{len(poly.exterior.coords)} vertices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
