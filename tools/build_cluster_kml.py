#!/usr/bin/env python3
"""
Build data/geo/cluster_regions.kml — the five SSM clusters as non-overlapping
polygons, for overlay on the difference maps.

Method (ruled by Martin, 2026-09-02): nearest-well (Voronoi) regions over the 66
reference wells, clipped to the KML site boundary, then dissolved by cluster.

Why not hulls: the clusters are defined by SSM coefficient behaviour, not by
geography, and they interdigitate. C1 in particular contains CEH11, 2.1 km from
the rest of the cluster, so any hull would inflate C1 across wells belonging to
other clusters. A Voronoi partition asserts only what is defensible — "the
nearest monitored reference well here belongs to Cn" — and leaves CEH11 as its
own detached piece rather than dragging a boundary across the reserve.

Basis and limits, which any caption using this layer must carry:
  * 66 reference wells only. The 22 extended wells are not in the k=5 partition
    (03_master_data.csv carries the reference network), so they do not seed cells.
  * The regions are a rendering of well membership, NOT a mapped hydrological
    boundary. A cell edge is midway between two wells and moves if the network
    changes.
"""
import sys
import numpy as np
import pandas as pd
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union
from pyproj import Transformer

sys.path.insert(0, '/home/claude/NRG/src')
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS       # noqa: E402
from utils import kml_io                                        # noqa: E402

REPO = '/home/claude/NRG'
OUT_KML = f'{REPO}/data/geo/cluster_regions.kml'

# ── wells ────────────────────────────────────────────────────────────────────
md = pd.read_csv(f'{REPO}/outputs/03_master_data.csv')
pts = md[['Easting', 'Northing']].to_numpy(float)
clusters = md['Cluster'].to_numpy(int)
names = md['Name_Original'].tolist()
print(f'seed wells: {len(pts)}')

# ── site boundary ────────────────────────────────────────────────────────────
gdf = kml_io.read_kml(f'{REPO}/data/geo/site_boundary.kml', "EPSG:27700")
polys = [g for g in gdf.geometry if g is not None and g.geom_type in ('Polygon', 'MultiPolygon')]
if not polys:
    # boundary supplied as a closed line: rebuild the polygon from its ring
    polys = [Polygon(g.coords) for g in gdf.geometry
             if g is not None and g.geom_type == 'LineString' and len(g.coords) > 3]
site = unary_union(polys).buffer(0)
print(f'site boundary: {site.geom_type}, area {site.area/1e6:.2f} km2')

# ── Voronoi, with distant mirror points so every cell is finite ──────────────
span = float(max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]))) * 10
centre = pts.mean(axis=0)
far = np.array([centre + [span, span], centre + [span, -span],
                centre + [-span, span], centre + [-span, -span]])
vor = Voronoi(np.vstack([pts, far]))
clip = box(*site.bounds).buffer(span / 10)

cells = {}
for i in range(len(pts)):
    region = vor.regions[vor.point_region[i]]
    if not region or -1 in region:
        print(f'  ! unbounded cell for {names[i]} — skipped')
        continue
    cell = Polygon(vor.vertices[region]).buffer(0).intersection(clip)
    cell = cell.intersection(site)
    if not cell.is_empty:
        cells.setdefault(clusters[i], []).append(cell)

regions = {c: unary_union(v).buffer(0) for c, v in sorted(cells.items())}
total = sum(r.area for r in regions.values())
print(f'\ndissolved into {len(regions)} cluster regions, '
      f'{total/1e6:.2f} km2 total ({total/site.area*100:.1f}% of the site)')
for c, r in regions.items():
    n = len(r.geoms) if isinstance(r, MultiPolygon) else 1
    print(f'  {CLUSTER_LABELS[c]:24s} {r.area/1e6:6.2f} km2  {n} part(s)  '
          f'{int((clusters == c).sum())} wells')

# ── write KML (WGS84) ────────────────────────────────────────────────────────
to_wgs = Transformer.from_crs('EPSG:27700', 'EPSG:4326', always_xy=True)


def ring(coords):
    lon, lat = to_wgs.transform(*zip(*coords))
    return ' '.join(f'{x:.7f},{y:.7f},0' for x, y in zip(lon, lat))


def polygon_xml(p):
    inner = ''.join(
        f'<innerBoundaryIs><LinearRing><coordinates>{ring(i.coords)}'
        f'</coordinates></LinearRing></innerBoundaryIs>' for i in p.interiors)
    return (f'<Polygon><outerBoundaryIs><LinearRing><coordinates>'
            f'{ring(p.exterior.coords)}</coordinates></LinearRing>'
            f'</outerBoundaryIs>{inner}</Polygon>')


def abgr(hexcol, alpha='ff'):
    h = hexcol.lstrip('#')
    return alpha + h[4:6] + h[2:4] + h[0:2]      # KML is aabbggrr


styles, places = [], []
for c, r in regions.items():
    styles.append(
        f'<Style id="c{c}"><LineStyle><color>{abgr(CLUSTER_COLOURS[c])}</color>'
        f'<width>2</width></LineStyle>'
        f'<PolyStyle><color>{abgr(CLUSTER_COLOURS[c], "26")}</color>'
        f'<fill>1</fill><outline>1</outline></PolyStyle></Style>')
    geoms = r.geoms if isinstance(r, MultiPolygon) else [r]
    body = ''.join(polygon_xml(p) for p in geoms)
    if len(list(geoms)) > 1:
        body = f'<MultiGeometry>{body}</MultiGeometry>'
    wells = ', '.join(n for n, cl in zip(names, clusters) if cl == c)
    places.append(
        f'<Placemark><name>{CLUSTER_LABELS[c]}</name>'
        f'<description>Nearest-well (Voronoi) region of the {int((clusters==c).sum())} '
        f'reference wells in this cluster, clipped to the site boundary. '
        f'Wells: {wells}. This is a rendering of well membership, not a mapped '
        f'hydrological boundary.</description>'
        f'<styleUrl>#c{c}</styleUrl>{body}</Placemark>')

kml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
       '<name>SSM cluster regions (k=5)</name>'
       '<description>Nearest-well (Voronoi) regions over the 66 reference '
       'dipwells, dissolved by cluster and clipped to the site boundary. '
       'Generated from outputs/03_master_data.csv; regenerate if the partition '
       'or the reference network changes. Not a hydrological boundary.'
       '</description>'
       + ''.join(styles) + ''.join(places) +
       '</Document></kml>\n')

with open(OUT_KML, 'w') as f:
    f.write(kml)
print(f'\nwritten {OUT_KML}')

# read back — the artefact is not verified until it has been re-read
check = kml_io.read_kml(OUT_KML, "EPSG:27700")
print(f'read back: {len(check)} placemarks, '
      f'{check.geometry.area.sum()/1e6:.2f} km2 total')
print(check[['Name']].to_string(index=False) if 'Name' in check.columns
      else check.columns.tolist())
