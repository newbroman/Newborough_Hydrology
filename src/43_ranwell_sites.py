#!/usr/bin/env python3
"""Script 43 - Ranwell (1959) historical water-table sites: hand placement over a
georeferenced sketch, height-checked against the DEM, basin-tested (W95; D-140).

Ranwell (1959) Fig 3 (J. Ecology 47(3), p.577) is a field sketch: topologically
right, not metrically registrable (found 2026-09-07, D-140 revisited). v2
therefore places the seventeen pipe sites by four routes, in this order of
authority:

  Route M -- HEADLINE.  Martin's hand placement in Google Earth over his own
    georeferenced warp of the sketch (data/geo/ranwell_1959_sites_martin.csv;
    the GeoTIFF itself is in-copyright and local-only, D-081).  The numeral
    positions read off the warp (ranwell_1959_sites_georef_px.csv) are carried
    as columns so the hand move from them is visible.

  Route H -- HEIGHT CHECK and refinement.  Ranwell levelled every site to OD.
    On gentle ground a single datum offset (DEM minus Ranwell) is fitted; each
    site is then moved within RANWELL_H_SEARCH_M to the cell minimising
    (height residual / RANWELL_H_SIGMA_M)^2 + (move / RANWELL_D_SIGMA_M)^2.  The
    heights CORROBORATE the placement; they resolve position only where the
    ground slopes, and the per-site `resolvability` says which.

  Route T -- TOPOLOGY, a basin test.  The DEM is segmented into closed basins
    (Gaussian smoothing RANWELL_DEM_SMOOTH_M, h-minima RANWELL_BASIN_HMIN_M,
    watershed).  Sites the sketch draws in one slack should share a basin, or
    sit in adjacent ones.  Ridge crests are the basin divides.  Ranwell's slack
    OUTLINES are not tested: the 2026-09-08 sweep showed they resolve on the DEM
    only where a slack is a closed trough (AS), so the outline is not a metric
    object either.

  Route F -- SLACK FLOORS, diagnostic.  Per sketch group, the ground within
    RANWELL_SLACK_DELTA_M[group] of each site's local floor (the
    RANWELL_FLOOR_PCT percentile within RANWELL_FLOOR_WINDOW_M), clipped to the
    group's basins and to RANWELL_SLACK_REACH_M of the sites; the CSV flags
    whether each floor is bounded by the ground or by the reach.

  Route A -- RETIRED, kept as a diagnostic.  v1's similarity registration
    (Penlon Lake anchor, scale bar, grid-north-up assumed), run so the record
    shows how far it was wrong (60-460 m).

Tier D (display/utility) -- no fit; Script 44 reads 43_01 for basins and
positions.  Skips cleanly when Route M's input is absent.
"""
__version__ = "2.0.0"  # Hollingham (2026) - 2026-09-08. D-140 revisited: sketch
#   found non-metric; Route A retired to a diagnostic; Routes M (hand placement
#   over Martin's georeference), H (height check + refinement, global offset),
#   T (DEM basin test; ridge crests = divides) and F (per-group slack floors at
#   documented delta) adopted.  All 17 sites placed (2, 3, 7 recovered; 9 from
#   R9.kml).  New outputs 43_03b (floor stats), 43_06 (floors + divides
#   GeoJSON), 43_07 (every modern well's basin, read by Script 44); 43_01
#   carries every route side by side; report numbers re-keyed.
# 1.0.1 (2026-09-06): D-035 - drop store-time round() at 8 sites.
# 1.0.0 (2026-09-06): W95 first issue, Routes A and B.

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from utils.paths import (  # noqa: E402
    DIR_43,
    OUT_43_SITES,
    OUT_43_NEAREST,
    OUT_43_DIAGNOSTIC,
    OUT_43_OVERLAY,
    OUT_43_VECTOR,
    OUT_43_FLOORS,
    OUT_43_FLOOR_STATS,
    OUT_43_WELL_BASINS,
    OUT_43_REPORT_NUMBERS,
    DATA_RANWELL_CONTROL,
    DATA_RANWELL_SITES_PX,
    DATA_RANWELL_SITES_MARTIN,
    DATA_RANWELL_SITES_GEOREF_PX,
    DATA_KML_RANWELL_FEATURES,
    DATA_KML_RANWELL_RIDGE,
    DATA_KML_FEATURES,
    DATA_DEM,
    INT_LOCATIONS,
    INT_WELLS_REFERENCE,
    INT_WELLS_EXTENDED,
)
from utils.config import (  # noqa: E402
    RANWELL_SCALEBAR_M,
    RANWELL_PENLON_NAME,
    RANWELL_ANALOGUE_RADIUS_M,
    RANWELL_H_SIGMA_M,
    RANWELL_D_SIGMA_M,
    RANWELL_H_SEARCH_M,
    RANWELL_H_ACCEPT_M,
    RANWELL_GENTLE_SLOPE,
    RANWELL_SLOPE_SMOOTH_M,
    RANWELL_FLAT_CELLS,
    RANWELL_DEM_SMOOTH_M,
    RANWELL_BASIN_HMIN_M,
    RANWELL_DEM_MARGIN_M,
    RANWELL_FLOOR_WINDOW_M,
    RANWELL_FLOOR_PCT,
    RANWELL_SLACK_DELTA_M,
    RANWELL_SLACK_REACH_M,
    RANWELL_SLACK_GROUPS,
)
from utils.console_utils import banner, phase, step, info, warn, saved  # noqa: E402
from utils.render_utils import apply_house_style, render_figure  # noqa: E402

N_SITES_EXPECTED = 17  # Ranwell numbered 1-16 and 18; there is no site 17


def _skip(msg):
    warn(f"Script 43 skipped: {msg}")
    return 0


# ── DEM window ────────────────────────────────────────────────────────────────
class DemWindow:
    """The DEM cut to the sites plus RANWELL_DEM_MARGIN_M, as a numpy array with
    row/col <-> E/N helpers.  NaN cells filled with the window maximum so the
    watershed treats no-data as high ground."""

    def __init__(self, sites_en):
        import rasterio
        self.src = rasterio.open(str(DATA_DEM))
        band = self.src.read(1).astype(float)
        if self.src.nodata is not None:
            band[band == self.src.nodata] = np.nan
        self.px = float(self.src.transform.a)
        rc = [self.src.index(e, n) for e, n in sites_en]
        m = int(RANWELL_DEM_MARGIN_M / self.px)
        rs = [r for r, _ in rc]
        cs = [c for _, c in rc]
        self.r0 = max(min(rs) - m, 0)
        self.r1 = min(max(rs) + m, band.shape[0])
        self.c0 = max(min(cs) - m, 0)
        self.c1 = min(max(cs) + m, band.shape[1])
        sub = band[self.r0:self.r1, self.c0:self.c1]
        self.nan = np.isnan(sub)
        self.dem = np.where(self.nan, np.nanmax(sub), sub)
        self.shape = self.dem.shape

    def rc(self, e, n):
        r, c = self.src.index(e, n)
        return r - self.r0, c - self.c0

    def en(self, r, c):
        e, n = self.src.xy(r + self.r0, c + self.c0)
        return float(e), float(n)

    def inside(self, r, c):
        return 0 <= r < self.shape[0] and 0 <= c < self.shape[1]

    def value(self, e, n):
        r, c = self.rc(e, n)
        if not self.inside(r, c) or self.nan[r, c]:
            return np.nan
        return float(self.dem[r, c])

    def _slope_grid(self):
        """|grad| of the DEM smoothed at RANWELL_SLOPE_SMOOTH_M (m/m); cached."""
        if not hasattr(self, "_slope"):
            from scipy import ndimage as ndi
            sd = ndi.gaussian_filter(self.dem, RANWELL_SLOPE_SMOOTH_M / self.px)
            gy, gx = np.gradient(sd, self.px)
            self._slope = np.hypot(gx, gy)
        return self._slope

    def slope(self, r, c):
        if not self.inside(r, c):
            return np.nan
        return float(self._slope_grid()[r, c])

    def value_bilinear(self, e, n):
        """DEM height at (E, N) by bilinear interpolation of the window."""
        from scipy import ndimage as ndi
        rr, cc = self.src.index(e, n, op=lambda v: v)  # fractional row/col
        rr, cc = float(rr) - self.r0 - 0.5, float(cc) - self.c0 - 0.5
        if not (0 <= rr <= self.shape[0] - 1 and 0 <= cc <= self.shape[1] - 1):
            return np.nan
        return float(ndi.map_coordinates(self.dem, [[rr], [cc]], order=1, mode="nearest")[0])

    def extent(self):
        """[E0, E1, N0, N1] of the window for imshow."""
        e0, n1 = self.src.xy(self.r0, self.c0, offset="ul")
        e1, n0 = self.src.xy(self.r1, self.c1, offset="ul")
        return [float(e0), float(e1), float(n0), float(n1)]

    def transform(self):
        from rasterio.transform import Affine
        t = self.src.transform
        return t * Affine.translation(self.c0, self.r0)


# ── Route M ───────────────────────────────────────────────────────────────────
def _load_route_m():
    """Martin's placement; hard fail on a missing site, height or sketch group."""
    m = pd.read_csv(DATA_RANWELL_SITES_MARTIN)
    need = {"site_no", "sketch_slack", "easting", "northing", "height_m_od"}
    missing = need - set(m.columns)
    if missing:
        raise RuntimeError(f"{DATA_RANWELL_SITES_MARTIN.name} lacks {sorted(missing)}")
    m["site_no"] = m["site_no"].astype(int)
    if len(m) != N_SITES_EXPECTED or m["site_no"].duplicated().any():
        raise RuntimeError(f"expected {N_SITES_EXPECTED} distinct sites, got {len(m)}")
    if m[["easting", "northing", "height_m_od"]].isna().any().any():
        raise RuntimeError("a site has no position or no height")
    bad = set(m["sketch_slack"].astype(str)) - set(RANWELL_SLACK_GROUPS)
    if bad:
        raise RuntimeError(f"unknown sketch_slack group(s) {sorted(bad)}")
    m = m.sort_values("site_no").reset_index(drop=True)
    if DATA_RANWELL_SITES_GEOREF_PX.exists():
        g = pd.read_csv(DATA_RANWELL_SITES_GEOREF_PX)[["site_no", "easting", "northing"]]
        g = g.rename(columns={"easting": "georef_easting", "northing": "georef_northing"})
        m = m.merge(g, on="site_no", how="left")
        m["hand_move_m"] = np.hypot(m["easting"] - m["georef_easting"],
                                    m["northing"] - m["georef_northing"])
    else:
        m["georef_easting"] = np.nan
        m["georef_northing"] = np.nan
        m["hand_move_m"] = np.nan
    return m


# ── Route H ───────────────────────────────────────────────────────────────────
def _route_h(m, dw):
    """Global datum offset on gentle ground; per-site cost-minimising move."""
    rows = []
    rr = int(RANWELL_H_SEARCH_M / dw.px)
    yy, xx = np.mgrid[-rr:rr + 1, -rr:rr + 1]
    dist = np.hypot(yy, xx) * dw.px
    disk = dist <= RANWELL_H_SEARCH_M
    # pass 1: DEM at the hand position, slope, offset on gentle sites
    dem_at = []
    slopes = []
    for r in m.itertuples():
        i, j = dw.rc(r.easting, r.northing)
        dem_at.append(dw.value_bilinear(r.easting, r.northing))
        slopes.append(dw.slope(i, j))
    m = m.assign(dem_m=dem_at, slope=slopes)
    gentle = m[(m["slope"] < RANWELL_GENTLE_SLOPE) & m["dem_m"].notna()]
    resid_g = gentle["dem_m"] - gentle["height_m_od"]
    offset = float(resid_g.median()) if len(gentle) else 0.0
    offset_mad = float((resid_g - offset).abs().median()) if len(gentle) else np.nan
    # pass 2: per-site refinement against target = Ranwell + offset
    for r in m.itertuples():
        i, j = dw.rc(r.easting, r.northing)
        target = r.height_m_od + offset
        best = None
        n_accept = 0
        for di in range(-rr, rr + 1):
            for dj in range(-rr, rr + 1):
                if not disk[di + rr, dj + rr]:
                    continue
                ii, jj = i + di, j + dj
                if not dw.inside(ii, jj) or dw.nan[ii, jj]:
                    continue
                dz = dw.dem[ii, jj] - target
                d = dist[di + rr, dj + rr]
                if abs(dz) <= RANWELL_H_ACCEPT_M:
                    n_accept += 1
                cost = (dz / RANWELL_H_SIGMA_M) ** 2 + (d / RANWELL_D_SIGMA_M) ** 2
                if best is None or cost < best[0]:
                    best = (cost, ii, jj, dz, d)
        if best is None:
            rows.append(dict(refined_easting=np.nan, refined_northing=np.nan,
                             refined_move_m=np.nan, refined_resid_m=np.nan,
                             matching_cells_within_R=0, resolvability="outside_dem"))
            continue
        _, ii, jj, dz, d = best
        e2, n2 = dw.en(ii, jj)
        if r.slope >= RANWELL_GENTLE_SLOPE:
            res = "flank"
        elif n_accept >= RANWELL_FLAT_CELLS:
            res = "flat_floor"
        else:
            res = "sparse_match"
        rows.append(dict(refined_easting=e2, refined_northing=n2, refined_move_m=d,
                         refined_resid_m=dz, matching_cells_within_R=n_accept,
                         resolvability=res))
    m = pd.concat([m, pd.DataFrame(rows)], axis=1)
    m["resid_m"] = m["dem_m"] - m["height_m_od"]
    m["resid_after_offset_m"] = m["resid_m"] - offset
    return m, offset, offset_mad, len(gentle)


# ── Route T and F ─────────────────────────────────────────────────────────────
def _basins(dw):
    """Watershed basins of the smoothed DEM; returns (labels, divides)."""
    from scipy import ndimage as ndi
    from skimage.segmentation import watershed, find_boundaries
    from skimage.morphology import h_minima
    sd = ndi.gaussian_filter(dw.dem, RANWELL_DEM_SMOOTH_M / dw.px)
    markers, _ = ndi.label(h_minima(sd, RANWELL_BASIN_HMIN_M))
    lab = watershed(sd, markers=markers).astype(np.int32)
    div = find_boundaries(lab, mode="inner")
    return lab, div


def _route_t(m, dw, lab):
    """Basin id per site; whether it shares (or neighbours) a basin with its
    sketch group."""
    from scipy import ndimage as ndi
    ids = []
    for r in m.itertuples():
        i, j = dw.rc(r.easting, r.northing)
        ids.append(int(lab[i, j]) if dw.inside(i, j) else -1)
    m = m.assign(basin_id=ids)
    # adjacency of basins: dilate each label by one cell
    dil = ndi.grey_dilation(lab, size=(3, 3))
    ero = ndi.grey_erosion(lab, size=(3, 3))
    adj = set()
    for a, b in zip(lab[dil != lab], dil[dil != lab]):
        adj.add((int(a), int(b)))
        adj.add((int(b), int(a)))
    for a, b in zip(lab[ero != lab], ero[ero != lab]):
        adj.add((int(a), int(b)))
        adj.add((int(b), int(a)))
    shared, adjacent = [], []
    for r in m.itertuples():
        others = m[(m["sketch_slack"] == r.sketch_slack) & (m["site_no"] != r.site_no)]
        shared.append(bool((others["basin_id"] == r.basin_id).any()))
        adjacent.append(bool(any((r.basin_id, b) in adj for b in others["basin_id"])))
    m["basin_shared_with_group"] = shared
    m["basin_adjacent_to_group"] = adjacent
    m["basin_consistent"] = m["basin_shared_with_group"] | m["basin_adjacent_to_group"]
    return m


def _route_f(m, dw, lab):
    """Per-group slack floors; returns (mask by group, rows of floor stats,
    per-site distance to its group's floor)."""
    from scipy import ndimage as ndi
    yy, xx = np.mgrid[0:dw.shape[0], 0:dw.shape[1]]
    masks, stats = {}, []
    win = (RANWELL_FLOOR_WINDOW_M / dw.px) ** 2
    reach = (RANWELL_SLACK_REACH_M / dw.px) ** 2
    dist_to = pd.Series(np.nan, index=m.index)
    for g in RANWELL_SLACK_GROUPS:
        members = m[m["sketch_slack"] == g]
        if members.empty:
            continue
        basins = set(int(b) for b in members["basin_id"] if b >= 0)
        inb = np.isin(lab, list(basins))
        slack = np.zeros(dw.shape, bool)
        reach_any = np.zeros(dw.shape, bool)
        floors = []
        for r in members.itertuples():
            i, j = dw.rc(r.easting, r.northing)
            d2 = (yy - i) ** 2 + (xx - j) ** 2
            dk = (d2 <= win) & ~dw.nan
            fl = float(np.percentile(dw.dem[dk], RANWELL_FLOOR_PCT))
            floors.append(fl)
            cand = (dw.dem <= fl + RANWELL_SLACK_DELTA_M[g]) & inb & (d2 <= reach)
            cl, _ = ndi.label(cand, structure=np.ones((3, 3)))
            touched = set(cl[dk & cand].tolist()) - {0}
            slack |= np.isin(cl, list(touched))
            reach_any |= d2 <= reach
        slack = ndi.binary_closing(slack, iterations=2) & inb
        # bounded by the ground or by the reach: does the floor touch the reach rim?
        rim = reach_any & ~ndi.binary_erosion(reach_any, iterations=2)
        bounded_by = "reach" if (slack & rim).any() else "dem"
        edt = ndi.distance_transform_edt(~slack) * dw.px
        for idx, r in members.iterrows():
            i, j = dw.rc(r.easting, r.northing)
            dist_to.loc[idx] = float(edt[i, j]) if dw.inside(i, j) else np.nan
        masks[g] = slack
        stats.append(dict(group=g, n_sites=len(members), delta_m=RANWELL_SLACK_DELTA_M[g],
                          floor_m=float(np.median(floors)), area_ha=float(slack.sum()) * dw.px ** 2 / 1e4,
                          bounded_by=bounded_by,
                          n_sites_on_floor=int((dist_to.loc[members.index] == 0).sum())))
    m["dist_to_slack_floor_m"] = dist_to
    return masks, pd.DataFrame(stats), m


# ── Route A (retired) ─────────────────────────────────────────────────────────
def _route_a(m):
    """v1's similarity registration, for the record; NaN when its inputs are gone."""
    if not (DATA_RANWELL_CONTROL.exists() and DATA_RANWELL_SITES_PX.exists()
            and DATA_KML_FEATURES.exists()):
        info("Route A inputs absent; diagnostic columns blank")
        return m.assign(routeA_easting=np.nan, routeA_northing=np.nan, routeA_error_m=np.nan), np.nan
    try:
        from utils.kml_io import read_kml
        gdf = read_kml(DATA_KML_FEATURES)
        sel = gdf[gdf["Name"].astype(str).str.strip() == RANWELL_PENLON_NAME]
        c = sel.geometry.iloc[0].centroid
        pe, pn = float(c.x), float(c.y)
        control = pd.read_csv(DATA_RANWELL_CONTROL)
        ctrl = {r["role"]: (float(r["px_x"]), float(r["px_y"])) for _, r in control.iterrows()}
        p_px = ctrl["penlon_lake_centroid"]
        bar_px = float(np.hypot(*(np.array(ctrl["scalebar_quarter"]) - np.array(ctrl["scalebar_zero"]))))
        m_per_px = RANWELL_SCALEBAR_M / bar_px
        px = pd.read_csv(DATA_RANWELL_SITES_PX).dropna(subset=["px_x", "px_y"])
        px["routeA_easting"] = pe + (px["px_x"] - p_px[0]) * m_per_px
        px["routeA_northing"] = pn - (px["px_y"] - p_px[1]) * m_per_px
        m = m.merge(px[["site_no", "routeA_easting", "routeA_northing"]], on="site_no", how="left")
    except Exception as exc:
        warn(f"Route A diagnostic not computed ({exc})")
        return m.assign(routeA_easting=np.nan, routeA_northing=np.nan, routeA_error_m=np.nan), np.nan
    m["routeA_error_m"] = np.hypot(m["routeA_easting"] - m["easting"],
                                   m["routeA_northing"] - m["northing"])
    rms = float(np.sqrt(np.nanmean(m["routeA_error_m"] ** 2)))
    return m, rms


# ── modern network ────────────────────────────────────────────────────────────
def _modern_network():
    loc = pd.read_csv(INT_LOCATIONS)
    ec = next(c for c in loc.columns if c.lower() in ("e", "easting", "x"))
    nc = next(c for c in loc.columns if c.lower() in ("n", "northing", "y"))
    idc = next(c for c in loc.columns if c.lower() in ("name", "well", "id"))
    loc = loc[[idc, ec, nc]].rename(columns={idc: "well", ec: "E", nc: "N"})
    loc = loc.dropna(subset=["E", "N"]).copy()

    def _ids(path):
        try:
            return {str(c).strip().lower() for c in pd.read_csv(path, nrows=0).columns}
        except Exception:
            return set()

    ref, ext = _ids(INT_WELLS_REFERENCE), _ids(INT_WELLS_EXTENDED)
    loc["network"] = loc["well"].map(
        lambda w: "reference" if str(w).strip().lower() in ref
        else "extended" if str(w).strip().lower() in ext else "other")
    return loc


def _nearest(m, net, dw, lab):
    """Three nearest wells per site with a same-basin flag."""
    wb = {}
    for w in net.itertuples():
        i, j = dw.rc(w.E, w.N)
        wb[w.well] = int(lab[i, j]) if dw.inside(i, j) else -1
    net = net.assign(basin_id=net["well"].map(wb))
    rows = []
    for r in m.itertuples():
        d = np.hypot(net["E"] - r.easting, net["N"] - r.northing)
        order = np.argsort(d.values)[:3]
        top = net.iloc[order]
        td = d.values[order]
        rows.append(dict(
            ranwell_site=int(r.site_no),
            nearest_well=top.iloc[0]["well"],
            nearest_well_network=top.iloc[0]["network"],
            nearest_well_dist_m=float(td[0]),
            nearest_well_same_basin=bool(top.iloc[0]["basin_id"] == r.basin_id),
            nearest_3_wells="; ".join(
                f"{w} ({dist:.0f} m{', same basin' if b == r.basin_id else ''})"
                for w, dist, b in zip(top["well"], td, top["basin_id"])),
        ))
    return pd.DataFrame(rows), net


# ── vectors and figure ────────────────────────────────────────────────────────
def _write_vectors(sites, masks, floor_stats, div, dw):
    import geopandas as gpd
    from shapely.geometry import Point, shape
    from rasterio import features
    gv = gpd.GeoDataFrame(sites.copy(),
                          geometry=[Point(e, n) for e, n in zip(sites["easting"], sites["northing"])],
                          crs="EPSG:27700")
    gv.to_file(OUT_43_VECTOR, driver="GeoJSON")
    saved(OUT_43_VECTOR.name)
    recs = []
    t = dw.transform()
    for g, mask in masks.items():
        st = floor_stats.set_index("group").loc[g]
        polys = [shape(geom) for geom, v in features.shapes(mask.astype(np.uint8), mask=mask, transform=t) if v == 1]
        if polys:
            from shapely.ops import unary_union
            recs.append(dict(layer="slack_floor", group=g, delta_m=float(st["delta_m"]),
                             floor_m=float(st["floor_m"]), area_ha=float(st["area_ha"]),
                             bounded_by=st["bounded_by"], geometry=unary_union(polys)))
    dpolys = [shape(geom) for geom, v in features.shapes(div.astype(np.uint8), mask=div, transform=t) if v == 1]
    if dpolys:
        from shapely.ops import unary_union
        recs.append(dict(layer="basin_divide", group="", delta_m=np.nan, floor_m=np.nan,
                         area_ha=np.nan, bounded_by="", geometry=unary_union(dpolys)))
    gpd.GeoDataFrame(recs, crs="EPSG:27700").to_file(OUT_43_FLOORS, driver="GeoJSON")
    saved(OUT_43_FLOORS.name)


def _kml_lines_osgb(path):
    """LineString coordinate lists of a KML, in OSGB, via kml_io or a plain XML
    read with pyproj (Google Earth KMLs are WGS84 lon,lat[,alt])."""
    try:
        from utils.kml_io import read_kml
        return [geom.xy for geom in read_kml(path).geometry]
    except Exception:
        import xml.etree.ElementTree as ET
        from pyproj import Transformer
        tr = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
        ns = "{http://www.opengis.net/kml/2.2}"
        out = []
        for ls in ET.parse(path).iter(f"{ns}LineString"):
            coords = ls.find(f"{ns}coordinates").text.split()
            lon = [float(c.split(",")[0]) for c in coords]
            lat = [float(c.split(",")[1]) for c in coords]
            xs, ys = tr.transform(lon, lat)
            out.append((list(xs), list(ys)))
        return out


def _overlay(sites, masks, div, dw, net):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8.0, 10.5))
    ext = dw.extent()
    gy, gx = np.gradient(dw.dem, dw.px)
    az, alt = np.radians(315), np.radians(45)
    sl = np.arctan(np.hypot(gx, gy))
    asp = np.arctan2(-gx, gy)
    hs = np.sin(alt) * np.cos(sl) + np.cos(alt) * np.sin(sl) * np.cos(az - asp)
    ax.imshow(hs, cmap="gray", extent=ext, vmin=0, vmax=1.2, zorder=1)
    cols = {"BS": "#1f77b4", "AS": "#ff7f0e", "CG": "#2ca02c", "PL": "#9467bd"}
    X = np.linspace(ext[0], ext[1], dw.shape[1])
    Y = np.linspace(ext[3], ext[2], dw.shape[0])
    for g, mask in masks.items():
        ax.contourf(X, Y, mask.astype(int), levels=[0.5, 1.5], colors=[cols[g]], alpha=0.35, zorder=2)
        ax.contour(X, Y, mask.astype(int), levels=[0.5], colors=[cols[g]], linewidths=0.8,
                   linestyles="dotted", zorder=2)
    ax.contour(X, Y, div.astype(int), levels=[0.5], colors=["black"], linewidths=0.7, zorder=3)
    # Martin's traced outlines, for comparison only
    for p, c in ((DATA_KML_RANWELL_FEATURES, "white"), (DATA_KML_RANWELL_RIDGE, "yellow")):
        if not p.exists():
            continue
        try:
            for xs, ys in _kml_lines_osgb(p):
                ax.plot(xs, ys, color=c, lw=0.8, ls="--", zorder=4)
        except Exception as exc:
            info(f"traced outline {p.name} not drawn ({exc})")
    inwin = net[(net["E"] > ext[0]) & (net["E"] < ext[1]) & (net["N"] > ext[2]) & (net["N"] < ext[3])]
    ax.scatter(inwin["E"], inwin["N"], s=12, marker="^", c="red", zorder=5, label="Modern dipwells")
    ok = sites["routeA_easting"].notna()
    ax.scatter(sites.loc[ok, "routeA_easting"], sites.loc[ok, "routeA_northing"], s=18,
               c="grey", zorder=5, label="Route A (retired)")
    for r in sites[ok].itertuples():
        ax.annotate("", xy=(r.easting, r.northing), xytext=(r.routeA_easting, r.routeA_northing),
                    arrowprops=dict(arrowstyle="-", color="grey", lw=0.5), zorder=5)
    ax.scatter(sites["refined_easting"], sites["refined_northing"], s=16, marker="x",
               c="black", zorder=6, label="Route H refined")
    for g in cols:
        s = sites[sites["sketch_slack"] == g]
        ax.scatter(s["easting"], s["northing"], s=40, c=cols[g], edgecolor="white",
                   linewidths=0.8, zorder=7, label=f"Ranwell sites, {g}")
    for r in sites.itertuples():
        ax.annotate(f"R{int(r.site_no)}", (r.easting, r.northing), textcoords="offset points",
                    xytext=(4, 4), fontsize=7, color="white", zorder=8)
    ax.set_xlim(ext[0], ext[1])
    ax.set_ylim(ext[2], ext[3])
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    ax.set_aspect("equal")
    ax.legend(loc="lower right", fontsize=7, framealpha=0.9)
    ax.set_title("Ranwell (1959) sites: hand placement (M), height refinement (H), "
                 "DEM basin divides (black) and slack floors (F)", fontsize=9)
    render_figure(fig, OUT_43_OVERLAY)
    saved(OUT_43_OVERLAY.name)


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    apply_house_style()
    banner("43", "Ranwell (1959) historical water-table sites, placed and checked",
           version=__version__)
    for p in (DATA_RANWELL_SITES_MARTIN, DATA_DEM, INT_LOCATIONS):
        if not p.exists():
            return _skip(f"missing input {p.name}")
    DIR_43.mkdir(parents=True, exist_ok=True)

    phase(1, "Route M - Martin's hand placement over the georeferenced sketch")
    m = _load_route_m()
    step(f"{len(m)} sites; groups "
         + ", ".join(f"{g} {int((m['sketch_slack'] == g).sum())}" for g in RANWELL_SLACK_GROUPS)
         + (f"; median hand move from the numeral positions {m['hand_move_m'].median():.0f} m"
            if m["hand_move_m"].notna().any() else ""))
    dw = DemWindow(list(zip(m["easting"], m["northing"])))
    info(f"DEM window {dw.shape[0]}x{dw.shape[1]} cells at {dw.px:.1f} m")

    phase(2, "Route H - Ranwell's levelled heights against the DEM")
    m, offset, offset_mad, n_gentle = _route_h(m, dw)
    within = int((m["resid_after_offset_m"].abs() <= 0.3).sum())
    step(f"datum offset {offset:+.3f} m (MAD {offset_mad:.3f}, {n_gentle} gentle sites); "
         f"{within}/{len(m)} sites within 0.3 m before refinement; "
         f"refined moves median {m['refined_move_m'].median():.1f} m, max {m['refined_move_m'].max():.1f} m")
    for r in m.itertuples():
        info(f"  site {int(r.site_no):2d} {r.sketch_slack}: resid {r.resid_after_offset_m:+.2f} -> "
             f"{r.refined_resid_m:+.2f} m after {r.refined_move_m:.0f} m; {r.resolvability}")

    phase(3, "Route T - DEM basins against the sketch grouping")
    lab, div = _basins(dw)
    m = _route_t(m, dw, lab)
    n_cons = int(m["basin_consistent"].sum())
    exc = ", ".join(str(int(s)) for s in m.loc[~m["basin_consistent"], "site_no"])
    step(f"{lab.max()} basins; {n_cons}/{len(m)} sites share or neighbour a basin with their "
         f"sketch group" + (f"; exceptions: {exc}" if exc else ""))

    phase(4, "Route F - slack floors per sketch group (diagnostic)")
    masks, floor_stats, m = _route_f(m, dw, lab)
    for s in floor_stats.itertuples():
        step(f"{s.group}: floor {s.floor_m:.1f} m + {s.delta_m:.2f} m -> {s.area_ha:.1f} ha, "
             f"bounded by {s.bounded_by}, {s.n_sites_on_floor}/{s.n_sites} sites on the floor")

    phase(5, "Route A (retired) and the modern network")
    m, routeA_rms = _route_a(m)
    if routeA_rms == routeA_rms:
        step(f"Route A rms error against Route M {routeA_rms:.0f} m "
             f"(range {m['routeA_error_m'].min():.0f}-{m['routeA_error_m'].max():.0f} m)")
    net = _modern_network()
    nearest, net = _nearest(m, net, dw, lab)
    m = m.merge(nearest[["ranwell_site", "nearest_well", "nearest_well_dist_m", "nearest_well_same_basin"]],
                left_on="site_no", right_on="ranwell_site", how="left").drop(columns="ranwell_site")
    analog = []
    for w in net.itertuples():
        d = np.hypot(m["easting"] - w.E, m["northing"] - w.N)
        j = int(np.argmin(d.values))
        if d.values[j] <= RANWELL_ANALOGUE_RADIUS_M and m.iloc[j]["basin_id"] == w.basin_id:
            analog.append(w.well)
    step(f"{len(analog)} modern well(s) within {RANWELL_ANALOGUE_RADIUS_M:.0f} m of a 1950s site "
         f"in the same basin")

    phase(6, "Outputs")
    cols = ["site_no", "sketch_slack", "easting", "northing", "georef_easting", "georef_northing",
            "hand_move_m", "height_m_od", "dem_m", "resid_m", "resid_after_offset_m",
            "refined_easting", "refined_northing", "refined_move_m", "refined_resid_m", "slope",
            "matching_cells_within_R", "resolvability", "basin_id", "basin_shared_with_group",
            "basin_adjacent_to_group", "basin_consistent", "dist_to_slack_floor_m",
            "routeA_easting", "routeA_northing", "routeA_error_m", "nearest_well",
            "nearest_well_dist_m", "nearest_well_same_basin", "source"]
    out = m[[c for c in cols if c in m.columns]].copy()
    out.to_csv(OUT_43_SITES, index=False)
    saved(OUT_43_SITES.name)
    nearest.to_csv(OUT_43_NEAREST, index=False)
    saved(OUT_43_NEAREST.name)
    net[["well", "network", "E", "N", "basin_id"]].to_csv(OUT_43_WELL_BASINS, index=False)
    saved(OUT_43_WELL_BASINS.name)
    diag = pd.DataFrame([dict(
        n_sites=len(m), datum_offset_m=offset, datum_offset_mad_m=offset_mad, n_gentle_sites=n_gentle,
        h_sigma_m=RANWELL_H_SIGMA_M, d_sigma_m=RANWELL_D_SIGMA_M, search_radius_m=RANWELL_H_SEARCH_M,
        n_sites_within_0p3m=within, n_sites_flank=int((m["resolvability"] == "flank").sum()),
        n_basins=int(lab.max()), n_sites_basin_consistent=n_cons, basin_exceptions=exc,
        routeA_rms_error_m=routeA_rms,
        rotation_assumption_v1="grid-north-up (retired 2026-09-08; sketch non-metric)")])
    diag.to_csv(OUT_43_DIAGNOSTIC, index=False)
    saved(OUT_43_DIAGNOSTIC.name)
    floor_stats.to_csv(OUT_43_FLOOR_STATS, index=False)
    saved(OUT_43_FLOOR_STATS.name)
    try:
        _write_vectors(out, masks, floor_stats, div, dw)
    except Exception as exc_:
        warn(f"vectors not written ({exc_})")
    try:
        _overlay(out, masks, div, dw, net)
    except Exception as exc_:
        warn(f"overlay figure not written ({exc_})")

    rn = pd.DataFrame([
        ("ranwell_sites_total", len(m), "count", "water-table pipe sites in Ranwell 1959 Fig 3 (1-16, 18)"),
        ("ranwell_sites_placed", len(m), "count", "sites with a Route M position"),
        ("ranwell_datum_offset_m", offset, "m", "median DEM minus Ranwell OD height on gentle ground"),
        ("ranwell_sites_within_0p3m", within, "count", "sites whose hand position is within 0.3 m of the DEM after the offset"),
        ("ranwell_sites_flank", int((m["resolvability"] == "flank").sum()), "count", "sites on sloping ground, where the height resolves position"),
        ("ranwell_sites_basin_consistent", n_cons, "count", "sites sharing or neighbouring a DEM basin with their sketch group"),
        ("ranwell_routeA_rms_error_m", routeA_rms, "m", "rms distance of the retired similarity registration from Route M"),
        ("ranwell_modern_wells_with_analogue", len(analog), "count",
         f"modern wells within {RANWELL_ANALOGUE_RADIUS_M:.0f} m of a 1950s site in the same basin"),
    ], columns=["key", "value", "unit", "note"])
    rn.to_csv(OUT_43_REPORT_NUMBERS, index=False)
    saved(OUT_43_REPORT_NUMBERS.name)
    dw.src.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
