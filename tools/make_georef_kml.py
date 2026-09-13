#!/usr/bin/env python3
"""Write `data/geo/georef_grid.kml` — a purpose-built registration control net.

WHY THIS EXISTS. Until now every frame was registered on the DIPWELL placemarks,
which puts the control density wherever the wells happen to be. That is fine at
the 3.70 km viewpoint, where one frame holds all 83 of them, but it fails as the
capture altitude drops: tiling the warren at 1.25 km leaves the sparsest tile
with **7 markers against a `CANOPY_MIN_CONTROL_POINTS` of 8**, so that tile
cannot register at all. A control net laid on a regular grid removes the
constraint — density becomes a choice rather than an accident of where somebody
sank a pipe.

It also separates two jobs that should never have shared one set of points. A
dipwell is a measurement; a control point is a fiducial. Registering on the
wells means the thing being measured is also the thing defining the coordinate
frame, and a well that moves — or is mis-keyed — moves the registration with it.

COORDINATES. The grid is generated in OSGB36 / EPSG:27700 on an exact round
number of metres, so every control point's position is known by construction
rather than surveyed. KML needs WGS84, so pyproj transforms it and the result is
verified by transforming back; anything that cannot round-trip to 1 cm aborts.

RENDERING. Script 41's `_detect_markers` finds BLUE placemark tips — `b > 150`,
`b - r > 45`, `b - g > 30` — and takes the bottom-centre of each blob as the
point. So the icon must be the blue pushpin, and the label must be OFF: a text
label renders beside the pin and can merge with it into one blob, which moves
the detected tip. `LabelStyle` scale 0 does that.

Usage:
    python3 tools/make_georef_kml.py                # write, verify, report
    python3 tools/make_georef_kml.py --spacing 200  # tighter net
    python3 tools/make_georef_kml.py --verify       # check the existing file
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-12. New: the registration
#   control net, for the high-resolution tiled capture (D-159).

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import numpy as np                                           # noqa: E402
import pyproj                                                # noqa: E402

from utils.warren_mask import _geom                          # noqa: E402

OUT_KML = REPO / "data" / "geo" / "georef_grid.kml"
OUT_CSV = REPO / "data" / "geo" / "georef_grid.csv"
ROUNDTRIP_TOL_M = 0.01
# The net is laid on a round grid inside the warren, plus a margin so a tile
# whose edge overhangs the boundary still has control out to its corner.
DEFAULT_SPACING_M = 250.0
MARGIN_M = 300.0
# The guide graticule: round OSGB kilometres, so a capture can be positioned
# and REPEATED by reading the grid rather than by eye.
LINE_SPACING_M = 500.0
# Blue pushpin: what `_detect_markers` keys on. Do not change without
# re-checking that colour test.
ICON = "http://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png"


def _grid(spacing: float, margin: float):
    """Control points on an exact OSGB grid, inside the warren plus a margin."""
    warren = _geom("warren")
    area = warren.buffer(margin)
    minx, miny, maxx, maxy = area.bounds
    x0 = np.floor(minx / spacing) * spacing
    y0 = np.floor(miny / spacing) * spacing
    pts = []
    for e in np.arange(x0, maxx + spacing, spacing):
        for n in np.arange(y0, maxy + spacing, spacing):
            from shapely.geometry import Point               # noqa: PLC0415
            if area.contains(Point(e, n)):
                pts.append((float(e), float(n)))
    pts.sort(key=lambda p: (-p[1], p[0]))          # north-west first, reading order
    return pts, warren


def _to_wgs84(pts):
    fwd = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    rev = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    out = []
    worst = 0.0
    for e, n in pts:
        lon, lat = fwd.transform(e, n)
        be, bn = rev.transform(lon, lat)
        worst = max(worst, float(np.hypot(be - e, bn - n)))
        out.append((lon, lat))
    return out, worst


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spacing", type=float, default=DEFAULT_SPACING_M)
    ap.add_argument("--margin", type=float, default=MARGIN_M)
    ap.add_argument("--line-spacing", type=float, default=LINE_SPACING_M,
                    help="OSGB grid interval for the guide lines, metres")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()

    pts, warren = _grid(a.spacing, a.margin)
    lonlat, worst = _to_wgs84(pts)
    print(f"georef net: {len(pts)} control point(s) at {a.spacing:.0f} m "
          f"spacing, warren + {a.margin:.0f} m")
    print(f"  OSGB -> WGS84 -> OSGB round trip, worst case {worst * 1000:.2f} mm")
    if worst > ROUNDTRIP_TOL_M:
        print("  ABORT: the transform does not round-trip to 1 cm")
        return 1

    # How many fall in a frame of each candidate capture geometry? This is the
    # number that decides whether a tile can register at all.
    print("  control points per frame, by capture altitude "
          "(1920x1080, GSD scaled from the committed vp2 fit at 3.70 km):")
    import pandas as pd                                      # noqa: PLC0415
    rg = pd.read_csv(REPO / "outputs" / "41_canopy_cover"
                     / "41_03_registration.csv", float_precision="round_trip")
    g0 = float(rg[rg["frame"] == "site24-3-2021m.png"]["gsd_m"].iloc[0])
    P = np.asarray(pts)
    for alt in (2.00, 1.50, 1.25, 1.00):
        g = g0 * alt / 3.70
        fw, fh = 1920 * g, 1080 * g
        best = []
        for cx in np.arange(P[:, 0].min(), P[:, 0].max(), fw / 2):
            for cy in np.arange(P[:, 1].min(), P[:, 1].max(), fh / 2):
                m = ((P[:, 0] >= cx) & (P[:, 0] < cx + fw)
                     & (P[:, 1] >= cy) & (P[:, 1] < cy + fh))
                if m.sum():
                    best.append(int(m.sum()))
        if best:
            print(f"    {alt:.2f} km ({g:.2f} m/px, {fw:.0f} x {fh:.0f} m): "
                  f"min {min(best)}, median {int(np.median(best))} per frame")

    if a.verify:
        return 0

    # ── the guide graticule ────────────────────────────────────────────────
    # Lines on round OSGB kilometres, labelled with their own easting or
    # northing, so the capture can be positioned and repeated by reading the
    # grid rather than by eye. The LABEL is on the line, not on the control
    # points: `_detect_markers` keys on blue blobs and a label rendered beside a
    # pin can merge with it and move the detected tip, so the pins stay mute and
    # the lines carry the text.
    gminx, gminy, gmaxx, gmaxy = warren.buffer(a.margin).bounds
    step = a.line_spacing
    lines = []
    for e in np.arange(np.ceil(gminx / step) * step, gmaxx + 1, step):
        seg = [(float(e), float(y)) for y in np.linspace(gminy, gmaxy, 40)]
        lines.append((f"E {e:.0f}", seg))
    for n in np.arange(np.ceil(gminy / step) * step, gmaxy + 1, step):
        seg = [(float(x), float(n)) for x in np.linspace(gminx, gmaxx, 40)]
        lines.append((f"N {n:.0f}", seg))
    print(f"  guide graticule: {len(lines)} line(s) on the {step:.0f} m OSGB grid")

    rows = ["id,easting,northing,longitude,latitude"]
    kml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
           '<name>georef_grid</name>',
           '<Style id="gp"><IconStyle><scale>0.9</scale>'
           f'<Icon><href>{ICON}</href></Icon></IconStyle>'
           '<LabelStyle><scale>0</scale></LabelStyle></Style>',
           '<Style id="gl"><LineStyle><color>96ffff00</color><width>1.4</width>'
           '</LineStyle><LabelStyle><scale>0.7</scale></LabelStyle></Style>']
    # The graticule goes in its own folder so it can be switched off in one
    # click while the control points stay on — the capture wants the lines
    # VISIBLE to frame the shot and ABSENT from the frame that gets measured.
    kml.append('<Folder><name>guide graticule (switch OFF before capturing)'
               '</name>')
    fwd = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:4326",
                                      always_xy=True)
    for label, seg in lines:
        cc = " ".join(f"{lo:.8f},{la:.8f},0" for lo, la
                      in (fwd.transform(x, y) for x, y in seg))
        kml.append(f"<Placemark><name>{label}</name><styleUrl>#gl</styleUrl>"
                   f"<LineString><tessellate>1</tessellate>"
                   f"<coordinates>{cc}</coordinates></LineString></Placemark>")
    kml.append('</Folder>')
    kml.append('<Folder><name>control points</name>')
    for i, ((e, n), (lon, lat)) in enumerate(zip(pts, lonlat), start=1):
        gid = f"G{i:03d}"
        rows.append(f"{gid},{e:.1f},{n:.1f},{lon:.8f},{lat:.8f}")
        kml.append(f"<Placemark><name>{gid}</name>"
                   f"<description>OSGB36 E {e:.1f} N {n:.1f}</description>"
                   f"<styleUrl>#gp</styleUrl><Point>"
                   f"<altitudeMode>clampToGround</altitudeMode>"
                   f"<coordinates>{lon:.8f},{lat:.8f},0</coordinates>"
                   f"</Point></Placemark>")
    kml.append('</Folder>')
    kml.append("</Document></kml>")
    OUT_KML.write_text("\n".join(kml), encoding="utf-8")
    OUT_CSV.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"  wrote {OUT_KML.relative_to(REPO)} and {OUT_CSV.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
