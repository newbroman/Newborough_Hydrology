#!/usr/bin/env python3
"""
Reproject a WGS84 KML polygon to an EPSG:27700 GeoJSON.

Writes a GeoJSON whose structure MATCHES data/geo/forest_boundary.geojson: a
FeatureCollection carrying an EPSG:27700 CRS, one Feature, and a Polygon whose
outer ring is [[E, N], ...] so that Script 01's _replant_proximity() and
_in_forest() can read it as features[0].geometry.coordinates[0] with pure numpy
and no CRS dependency at pipeline time.

This tool DOES use geopandas (gpd.read_file(...).to_crs("EPSG:27700")) and so is
meant to run on a machine with the geo stack (the L14), NOT inside the pipeline.
Run it once to produce the committed GeoJSON; the pipeline then reads only the
committed file.

Usage
-----
  # One file:
  reproject_kml_to_osgb_geojson.py IN.kml OUT.geojson

  # Several files in one call (repeatable):
  reproject_kml_to_osgb_geojson.py --pair IN1.kml OUT1.geojson \
                                   --pair IN2.kml OUT2.geojson

  # The four W96 / D-141 canopy-confound layers, by convention, from the
  # committed KMLs under data/geo/ to the committed GeoJSON the pipeline reads:
  reproject_kml_to_osgb_geojson.py --canopy-set

Each felling_1998_N.kml is already a single polygon; a KML holding a
MultiGeometry or several placemarks is unioned, and if that yields disjoint
polygons the largest is used with a warning (each input here is one polygon).
"""
import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union

TARGET_CRS = "EPSG:27700"
CRS_URN = "urn:ogc:def:crs:EPSG::27700"

# repo root = the parent of tools/
REPO = Path(__file__).resolve().parent.parent
GEO = REPO / "data" / "geo"

# The W96 / D-141 canopy-confound layers: committed KML -> committed GeoJSON.
CANOPY_SET = [
    (GEO / "felling_1998_1.kml", GEO / "felling_1998_1.geojson"),
    (GEO / "felling_1998_2.kml", GEO / "felling_1998_2.geojson"),
    (GEO / "felling_1998_3.kml", GEO / "felling_1998_3.geojson"),
    (GEO / "broadleaf_restock.kml", GEO / "broadleaf_restock.geojson"),
]


def kml_to_ring(kml_path: Path):
    """Return the polygon outer ring [[E, N], ...] in EPSG:27700 from a KML."""
    gdf = gpd.read_file(kml_path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")   # KML is WGS84 lon/lat by definition
    gdf = gdf.to_crs(TARGET_CRS)

    polys = []
    for geom in gdf.geometry:
        if geom is None:
            continue
        gt = geom.geom_type
        if gt == "Polygon":
            polys.append(geom)
        elif gt == "MultiPolygon":
            polys.extend(list(geom.geoms))
        elif gt in ("LineString", "LinearRing") and len(geom.coords) >= 4:
            polys.append(Polygon(geom.coords))
    if not polys:
        raise ValueError(f"{kml_path}: no polygon geometry found")

    merged = unary_union(polys)
    if merged.geom_type == "MultiPolygon":
        parts = sorted(merged.geoms, key=lambda g: g.area, reverse=True)
        print(f"  WARNING: {kml_path.name} yields {len(parts)} disjoint polygons; "
              f"using the largest ({parts[0].area:.0f} m^2)")
        merged = parts[0]

    return [[float(c[0]), float(c[1])] for c in merged.exterior.coords]


def write_geojson(ring, out_path: Path, source_kml: Path):
    """Write the ring as a forest_boundary.geojson-shaped FeatureCollection."""
    fc = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": CRS_URN}},
        "features": [{
            "type": "Feature",
            "properties": {
                "name": out_path.stem,
                "source": f"data/geo/{source_kml.name}",
                "note": ("WGS84 KML polygon reprojected to EPSG:27700 once and "
                         "committed so the pipeline needs no CRS dependency (same "
                         "pattern as forest_boundary.geojson). Produced by "
                         "tools/reproject_kml_to_osgb_geojson.py."),
            },
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        }],
    }
    out_path.write_text(json.dumps(fc, indent=1) + "\n", encoding="utf-8")
    print(f"  wrote {out_path}  ({len(ring)} ring vertices)")


def reproject(kml_path: Path, out_path: Path):
    kml_path = Path(kml_path)
    out_path = Path(out_path)
    if not kml_path.exists():
        raise FileNotFoundError(kml_path)
    print(f"{kml_path.name} -> {out_path.name}")
    ring = kml_to_ring(kml_path)
    write_geojson(ring, out_path, kml_path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kml", nargs="?", help="input KML path (single-file mode)")
    ap.add_argument("geojson", nargs="?", help="output GeoJSON path (single-file mode)")
    ap.add_argument("--pair", nargs=2, action="append", metavar=("KML", "GEOJSON"),
                    default=[], help="an input/output pair; repeatable")
    ap.add_argument("--canopy-set", action="store_true",
                    help="reproject the four W96/D-141 layers under data/geo/")
    args = ap.parse_args(argv)

    jobs = []
    if args.canopy_set:
        jobs.extend(CANOPY_SET)
    for kml, gj in args.pair:
        jobs.append((Path(kml), Path(gj)))
    if args.kml and args.geojson:
        jobs.append((Path(args.kml), Path(args.geojson)))

    if not jobs:
        ap.error("nothing to do: give KML GEOJSON, --pair, or --canopy-set")

    for kml_path, out_path in jobs:
        reproject(kml_path, out_path)
    print(f"done ({len(jobs)} file(s))")


if __name__ == "__main__":
    sys.exit(main())
