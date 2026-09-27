#!/usr/bin/env python3
"""Write `data/geo/site_outline.geojson` — the study-site mask outline as one polygon.

WHY. `data/geo/site_boundary.kml` (12 MB) is one outline stored as a polygonised
raster: 11,715 pieces (81 inter-stream blocks, 11,634 stream cells, D-082). Their
union is a single polygon, and that union is what every consumer wants. Until
D-204 each consumer rebuilt it for itself from the 12 MB file, in five different
ways. This tool builds it once; `utils.map_utils.load_site_outline()` serves it.

HOW. `kml_io.read_kml` (EPSG:27700) and one `unary_union` of every piece — the
same two calls Scripts 20, 41 and 45 made — so the committed polygon is the
geometry those scripts already used, not an approximation of it. No simplify
and no buffer here: those are rendering choices and stay in each consumer.
GeoJSON keeps coordinates as JSON floats, which round-trip exactly.

Usage:
    python3 tools/make_site_outline.py            # build and write
    python3 tools/make_site_outline.py --check    # rebuild, compare with the committed file (a gate)
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-27. New: the single site
#   outline (spec NRG_spec_site_outline_B_2026-09-27, D-204).

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from shapely.geometry import mapping, shape                   # noqa: E402
from shapely.ops import unary_union                           # noqa: E402

from utils.kml_io import read_kml                             # noqa: E402
from utils.paths import DATA_KML_SITE_BOUNDARY, DATA_SITE_OUTLINE  # noqa: E402


def build():
    pieces = [g for g in read_kml(DATA_KML_SITE_BOUNDARY, quiet=True).geometry if g is not None]
    return unary_union(pieces), len(pieces)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="rebuild and compare; write nothing")
    args = ap.parse_args()
    if args.check:
        if not DATA_SITE_OUTLINE.exists():
            print(f"make_site_outline --check: FAIL — {DATA_SITE_OUTLINE.name} is missing")
            return 1
        with open(DATA_SITE_OUTLINE, encoding="utf-8") as f:
            fc = json.load(f)
        recorded = fc["features"][0]["properties"].get("source_sha256")
        if recorded == _sha(DATA_KML_SITE_BOUNDARY):
            print(f"make_site_outline --check: OK — {DATA_KML_SITE_BOUNDARY.name} unchanged since "
                  f"{DATA_SITE_OUTLINE.name} was built")
            return 0
        poly, _ = build()
        same = shape(fc["features"][0]["geometry"]).equals_exact(poly, 0.0)
        print(f"make_site_outline --check: {'OK' if same else 'FAIL'} — {DATA_KML_SITE_BOUNDARY.name} "
              f"changed; the rebuilt outline {'matches' if same else 'differs — rerun this tool'}")
        return 0 if same else 1
    poly, n = build()
    fc = {
        "type": "FeatureCollection",
        "name": "site_outline",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::27700"}},
        "features": [{
            "type": "Feature",
            "properties": {
                "source": f"data/geo/{DATA_KML_SITE_BOUNDARY.name}",
                "source_sha256": _sha(DATA_KML_SITE_BOUNDARY),
                "method": f"kml_io.read_kml (EPSG:27700), unary_union of {n} pieces; no simplify, no buffer",
                "tool": "tools/make_site_outline.py " + __version__,
                "decision": "D-204",
                "made": date.today().isoformat(),
            },
            "geometry": mapping(poly),
        }],
    }
    with open(DATA_SITE_OUTLINE, "w", encoding="utf-8") as f:
        json.dump(fc, f)
    print(f"wrote {DATA_SITE_OUTLINE}: {poly.geom_type}, {poly.area / 1e6:.3f} km², "
          f"{len(poly.exterior.coords) if poly.geom_type == 'Polygon' else '?'} vertices, "
          f"{len(getattr(poly, 'interiors', []))} holes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
