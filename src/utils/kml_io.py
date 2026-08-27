#!/usr/bin/env python3
"""
kml_io.py — one way to read a KML, for a tree that had six.

WHY THIS EXISTS

  On 2026-08-27 `29_c3_within_variance_check.py` died on line 144:

      fiona.errors.DriverError: unsupported driver: 'LIBKML'

  Not a data fault and not a regression in the script. `gpd.read_file(path)`
  with no `driver=` lets fiona sniff, fiona picks LIBKML for a .kml, and LIBKML
  is a separate GDAL build option that Ubuntu's packaged GDAL does not enable.
  Every other KML reader in this tree registers the driver first and asks for
  `KML` by name:

      fiona.drvsupport.supported_drivers["KML"] = "rw"
      gpd.read_file(path, driver="KML")

  Scripts 04, 05, 06, 08, 12, 13, 19 and 20 do that. Three did not:

    29_c3_within_variance_check.py  crashed — the visible one
    24b_residual_climatology.py     bare read inside a try/except that returns
                                    None, so the forest-edge distance predictor
                                    QUIETLY BECAME NaN instead of failing
    utils/mask_streams_to_land.py   registers both drivers at line 130 and reads
                                    at line 43, eighty-seven lines earlier

  The quiet one is the worst of the three. A crash gets fixed the same evening.

WHAT THIS DOES

  Three attempts, in order, and it says which one worked:

    1. driver="KML"      the driver Ubuntu's GDAL actually ships
    2. driver="LIBKML"   richer, present on some builds
    3. pure XML          ElementTree + pyproj + shapely, no GDAL driver at all

  The third is the point. `11b_spatial_thresholds` already parses
  site_boundary.kml that way and has never depended on a driver; this generalises
  it to polygons, lines and points, so a missing GDAL build option can degrade
  the speed of a read and never its result.

  KML is WGS84 by definition, so a file with no declared CRS is assigned
  EPSG:4326 rather than guessed at.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-27.

import warnings
import xml.etree.ElementTree as ET
from pathlib import Path

KML_NS = "http://www.opengis.net/kml/2.2"
WGS84 = "EPSG:4326"


def _register() -> None:
    """Ask fiona for both KML drivers. Harmless when neither is built."""
    try:
        import fiona
        for name in ("KML", "LIBKML"):
            fiona.drvsupport.supported_drivers[name] = "rw"
    except Exception:                                    # noqa: BLE001
        pass


def _coords(text: str) -> list[tuple[float, float]]:
    pts = []
    for tok in (text or "").split():
        parts = tok.split(",")
        if len(parts) >= 2:
            try:
                pts.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    return pts


def _read_xml(path: Path):
    """(names, geometries in EPSG:4326) parsed without any GDAL driver."""
    from shapely.geometry import LineString, Point, Polygon

    root = ET.parse(str(path)).getroot()
    names, geoms = [], []
    for pm in root.iter(f"{{{KML_NS}}}Placemark"):
        nm_el = pm.find(f"{{{KML_NS}}}name")
        name = (nm_el.text or "").strip() if nm_el is not None else ""

        # Polygons first: a Polygon also contains a LinearRing, and taking the
        # ring instead would silently turn every area into a line.
        made = False
        for poly in pm.iter(f"{{{KML_NS}}}Polygon"):
            outer = poly.find(f".//{{{KML_NS}}}outerBoundaryIs"
                              f"//{{{KML_NS}}}coordinates")
            if outer is None or not outer.text:
                continue
            shell = _coords(outer.text)
            if len(shell) < 4:
                continue
            holes = []
            for inner in poly.findall(f".//{{{KML_NS}}}innerBoundaryIs"
                                      f"//{{{KML_NS}}}coordinates"):
                ring = _coords(inner.text or "")
                if len(ring) >= 4:
                    holes.append(ring)
            names.append(name)
            geoms.append(Polygon(shell, holes))
            made = True
        if made:
            continue

        for ls in pm.iter(f"{{{KML_NS}}}LineString"):
            c = ls.find(f"{{{KML_NS}}}coordinates")
            pts = _coords(c.text if c is not None else "")
            if len(pts) >= 2:
                names.append(name)
                geoms.append(LineString(pts))
                made = True
        if made:
            continue

        for pt in pm.iter(f"{{{KML_NS}}}Point"):
            c = pt.find(f"{{{KML_NS}}}coordinates")
            pts = _coords(c.text if c is not None else "")
            if pts:
                names.append(name)
                geoms.append(Point(pts[0]))
    return names, geoms


def read_kml(path, target_crs: str | None = "EPSG:27700", *, quiet: bool = False):
    """A GeoDataFrame from `path`, whatever GDAL was built with.

    target_crs=None returns the file's own WGS84 coordinates unprojected.
    Raises RuntimeError only if all three routes fail, naming each attempt —
    a driver problem should never present as an empty result.
    """
    import geopandas as gpd

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    _register()

    tried = []
    for driver in ("KML", "LIBKML"):
        try:
            gdf = gpd.read_file(str(p), driver=driver)
            if len(gdf):
                if gdf.crs is None:
                    gdf = gdf.set_crs(WGS84)
                return gdf.to_crs(target_crs) if target_crs else gdf
            tried.append(f"{driver}: read 0 features")
        except Exception as e:                            # noqa: BLE001
            tried.append(f"{driver}: {type(e).__name__} {e}")

    try:
        names, geoms = _read_xml(p)
        if geoms:
            if not quiet:
                warnings.warn(
                    f"{p.name}: no working GDAL KML driver "
                    f"({'; '.join(tried)}) — parsed {len(geoms)} feature(s) "
                    "from the XML instead. The result is the same; install "
                    "GDAL with KML support to take the fast path.")
            gdf = gpd.GeoDataFrame({"Name": names}, geometry=geoms, crs=WGS84)
            return gdf.to_crs(target_crs) if target_crs else gdf
        tried.append("xml: no Placemark geometry found")
    except Exception as e:                                # noqa: BLE001
        tried.append(f"xml: {type(e).__name__} {e}")

    raise RuntimeError(f"could not read {p}: " + "; ".join(tried))
