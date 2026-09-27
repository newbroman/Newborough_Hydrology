#!/usr/bin/env python3
"""
49_slack_flow.py — the water table by kriging with an external drift, and how
water moves between the slacks, wet, mean and dry
==============================================================================

WHAT THIS IS

  Spec NRG_spec_slack_flow_C_2026-09-27 (revision 5; Martin signed off
  2026-09-27). The streams on the maps were put there as a Tóth-style indication
  of groundwater movement, and cannot give it: streams.kml is surface routing
  (D-082), which spills each closed slack over its saddle, and T-66 measured it
  ~50° off the head surface. This step builds the water table from what measures
  it — the dipwells, and the sea as a boundary — with topography entering as a
  DRIFT chosen by test, and shows flow as arrows of -grad h. Sentinel-2 is a
  check, not data: 2026-09-27's quicklooks found 22 % of the ever-wet cells imply
  heads over a metre above the wells (perched, lake-fed or vegetation wetness)
  and that routing a surface built from them followed noise.

  1. States. Wet, mean and dry: the months in the top / bottom decile of the
     network-median level (the D-178 definition, imported from
     tools/sentinel_wet_floor.py, not rewritten) and all months.
  2. Data. Every well with a surveyed ground (reference + extended), its mean head
     in the state; sea anchors along the committed HWM line at the coastal head.
  3. Drift, chosen by test: none (ordinary kriging), the raw DEM, the DEM smoothed
     at HEAD_DEM_HEADLINE_SMOOTHING_M (T-66), and the slack-floor lower envelope.
     Judged by leave-one-well-out (well out of the fit AND the variogram) and a
     physical test (water table above the ground outside ever-wet cells).
  4. Coastal head: FITTED to the coastal wells in [mean tide level, mean high
     water] from the Admiralty levels (Martin: "the headline follow the wells");
     0 m, mean tide level, the midpoint and MHW run as fixed sensitivities.
  5. Sentinel check: each ever-wet cell's implied head against the wet surface,
     with the LiDAR slack-floor offset measured here at the wells (D-165 measured
     it independently at 0.302 m). The cells above the surface by more than
     SLACK_FLOW_PERCHED_M are the wetness the aquifer does not explain. A cell is
     tested only where a dipwell lies within SLACK_FLOW_WELL_SUPPORT_M; beyond it
     the surface is interpolation between sea anchors and distant wells, and the
     cell is "unconstrained" (Martin, 2026-09-27: 83 % of the first run's
     "perched" cells were of this kind). A tested cell more than
     SLACK_FLOW_PERCHED_M above the surface is then explained, in order, as
     "shadow" (in cast terrain shadow at the lowest-sun scene of the D-178 winter
     fit: a cell's switching level is set by its first wet reading, so one
     shadowed scene suffices), "reached by well" (its floor is at or below the
     nearest well's wet-state head: the surface, not the cell, is low there) or
     "floor edge" (steeper than SLACK_FLOW_EDGE_SLOPE_PCTL of the consistent
     cells: a mixed floor-and-dune pixel). What survives all three is "perched".
     The sun comes from the scene manifest dates at SLACK_FLOW_S2_ACQ_UTC_H (NOAA
     solar position equations); the shadow from the DEM by horizon search.
  5b. Coastal check: does the sea set the level at the coastal wells? The
     wet-minus-dry range against distance from the HWM, per sector, with ground
     height partialled out; the perched floors against their nearest well; the
     Sentinel excess by distance and support. Nothing is extrapolated to the
     shoreline, whose head the network does not identify.
  6. Arrows of -grad h, length on a log scale of |grad h|, in all three states:
     drainage continues when the warren is dry (Martin). Per slack, its mean
     direction in each state and the wet-to-dry turn.
  7. Transects: a radial fan from the wet-state water-table high, and a
     coast-normal series along Caernarfon Bay placed where the network supports
     it (not at a fixed interval); one radial merges into the series.

  REGISTERED 2026-09-27 (D-205): Phase 20 of run_analysis.py, tier A, default pass;
  documented in the Methods Supplement, S.23e.

INPUTS — all committed
  outputs/01_wells_all.csv, 01_well_elevations.csv; data/geo/newborough_dem.tif,
  coastline_hwm.geojson, study_area.geojson (D-203), tidal_levels_caernarfon_bar.csv
  (NP201B-26); data/sentinel/cell_thresholds.npz and sentinel_scene_manifest.csv (D-178).

OUTPUTS — outputs/49_slack_flow/ (paths.OUT_49_*)
  49_water_table_<state>.tif, 49_kriging_se_<state>.tif ... surfaces, m OD / m
  49_01_drift_selection.csv ... 4 drifts x 3 states: LOO median |e|, bias, p90;
                                above-ground share; variogram; fitted head
  49_02_loo_per_well.csv ...... per well, selected drift, per state
  49_03_slack_directions.csv .. per slack and state: direction, gradient, turn
  49_04_sentinel_check.csv .... per ever-wet cell: implied head, surface, class
  49_05_sensitivity.csv ....... fixed heads and the runner-up drift vs headline
  49_06_transects.csv, 49_07_transect_profiles.csv
  49_08_coastal_head_fit.csv .. the LOO error curve over the coastal head
  49_09_coastal_wells.csv ..... per well: distance to HWM, wet-dry range, perched cells nearest it
  49_10_coastal_tests.csv ..... seasonal damping per sector: Spearman and partial
  49_11_coastal_excess.csv .... Sentinel minus kriged head by distance from HWM and support
  49_slack_flow_<state>.kml, 49_unexplained_wetness.kml
  49_01..05 figures; 49_report_numbers.csv

USAGE
  python3 src/49_slack_flow.py [--no-fig]
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) - 2026-09-27. 1.0.1: registered (Phase 20, tier A,
#   default; D-205); docstring only, no behaviour change. 1.0.0: new, per spec NRG_spec_slack_flow_C
#   (revision 5, signed off 2026-09-27).

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
for _p in (REPO / "src", REPO / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np                                             # noqa: E402
import pandas as pd                                            # noqa: E402
import rasterio                                                # noqa: E402
from rasterio.transform import from_origin                     # noqa: E402
from scipy.ndimage import label, minimum_filter, uniform_filter, map_coordinates  # noqa: E402
from scipy.optimize import minimize_scalar                     # noqa: E402
from scipy.spatial import cKDTree                              # noqa: E402
from scipy.stats import rankdata, spearmanr                    # noqa: E402
import shapely                                                 # noqa: E402
from shapely.geometry import LineString, Point, shape          # noqa: E402
from shapely.ops import unary_union                            # noqa: E402
from pyproj import Transformer                                 # noqa: E402

from utils import config as C                                  # noqa: E402
from utils.paths import (                                      # noqa: E402
    DATA_DEM, DATA_COASTLINE_HWM, DATA_STUDY_AREA_GEOJSON, DATA_TIDAL_LEVELS,
    DATA_KML_STREAMS, SENTINEL_CELL_THRESHOLDS, SENTINEL_SCENE_MANIFEST, INT_WELLS_ALL, INT_WELLS_CLEAN, INT_WELL_ELEVATIONS, DATA_KML_FEATURES,
    DIR_49, OUT_49_DRIFT_SELECTION, OUT_49_LOO, OUT_49_SLACK_DIRECTIONS,
    OUT_49_SENTINEL_CHECK, OUT_49_SENSITIVITY, OUT_49_TRANSECTS, OUT_49_TRANSECT_PROFILES,
    OUT_49_COASTAL_HEAD, OUT_49_REPORT_NUMBERS, OUT_49_FIG_FLOW, OUT_49_FIG_TRANSECTS,
    OUT_49_FIG_DRIFT, OUT_49_FIG_WETNESS, OUT_49_KML_UNEXPLAINED,
    OUT_49_COASTAL_WELLS, OUT_49_COASTAL_TESTS, OUT_49_COASTAL_EXCESS, OUT_49_FIG_COASTAL,
    OUT_49_BOUNDARY_ANCHORS, OUT_49_BOUNDARY_TEST,
    out_49_surface, out_49_se, out_49_kml,
)
from utils.kriging import ked, ols_residuals, empirical_variogram, fit_spherical  # noqa: E402
from utils.report_numbers_utils import ReportNumbers           # noqa: E402
from utils.console_utils import banner, done, info, phase, result, saved, warn  # noqa: E402
from sentinel_wet_floor import _wells_monthly                  # noqa: E402  the D-178 network median

SCRIPT_ID = "49"
STATES = ("wet", "mean", "dry")
DRIFTS = ("o", "s", "e", "r")          # simplicity order for ties: none < smoothed < envelope < raw
DRIFT_NAME = {"o": "ordinary kriging (no drift)", "s": f"DEM smoothed {C.HEAD_DEM_HEADLINE_SMOOTHING_M} m",
              "e": f"slack-floor envelope {C.SLACK_FLOW_ENVELOPE_R_M:g} m", "r": "raw DEM"}


# ═══════════════════════════════════════════════════════════════════════════
# INPUTS
# ═══════════════════════════════════════════════════════════════════════════
def _geojson_geom(path):
    with open(path, encoding="utf-8") as f:
        return shape(json.load(f)["features"][0]["geometry"])


def tidal_levels() -> dict:
    t = pd.read_csv(DATA_TIDAL_LEVELS).set_index("level")["od_m"]
    return {"MTL": float(t[["MHWS", "MHWN", "MLWN", "MLWS"]].mean()),
            "MHW": float(t[["MHWS", "MHWN"]].mean())}


def load_dem():
    src = rasterio.open(DATA_DEM)
    return src, src.read(1).astype(float)


def drift_rasters(Z: np.ndarray, dres: float) -> dict:
    """The three covariate rasters on the DEM grid (keys s, e, r); dres the DEM cell size (m)."""
    cells = lambda m: max(1, int(round(m / dres)))             # noqa: E731  DEM cells
    zl = np.where(Z > 0, Z, 0.0)
    s = uniform_filter(zl, size=cells(C.HEAD_DEM_HEADLINE_SMOOTHING_M), mode="nearest")
    w = 2 * cells(C.SLACK_FLOW_ENVELOPE_R_M) + 1
    e = uniform_filter(minimum_filter(zl, size=w, mode="nearest"), size=w, mode="nearest")
    return {"r": Z, "s": s, "e": e}


def sun_position(dates, lat_deg: float, lon_deg: float, hour_utc: float):
    """Solar elevation and azimuth (degrees; azimuth clockwise from north) at hour_utc
    on each date: the NOAA general solar position equations (Spencer's series)."""
    t = pd.to_datetime(pd.Series(dates))
    doy = t.dt.dayofyear.values.astype(float)
    g = 2 * np.pi / 365.0 * (doy - 1 + (hour_utc - 12) / 24)
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g)
                    - 0.040849 * np.sin(2 * g))
    tst = hour_utc * 60 + eqt + 4 * lon_deg
    ha = np.radians(tst / 4 - 180)
    lat = np.radians(lat_deg)
    cz = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(ha)
    el = 90 - np.degrees(np.arccos(np.clip(cz, -1, 1)))
    az = (np.degrees(np.arctan2(np.sin(ha), np.cos(ha) * np.sin(lat) - np.tan(decl) * np.cos(lat))) + 180) % 360
    return el, az


def cast_shadow(Z: np.ndarray, dres: float, az_deg: float, el_deg: float) -> np.ndarray:
    """Cells in cast shadow with the sun at (az, el): some ground toward the sun rises
    above the sun's line. The search reaches as far as the DEM's relief can throw a shadow."""
    ux, uy = np.sin(np.radians(az_deg)), np.cos(np.radians(az_deg))
    tan_el = np.tan(np.radians(el_deg))
    reach = (float(np.nanmax(Z)) - float(np.nanmin(Z))) / tan_el
    lowest = float(np.nanmin(Z)) - 1.0 - reach * tan_el       # below anything: pads the shifted edge
    Zf = np.where(np.isfinite(Z), Z, lowest)
    shade = np.zeros(Z.shape, bool)
    for d in np.arange(dres, reach + dres, dres):
        dc, dr = int(round(ux * d / dres)), -int(round(uy * d / dres))
        S = np.full(Z.shape, lowest)
        r0, r1 = max(0, -dr), min(Z.shape[0], Z.shape[0] - dr)
        c0, c1 = max(0, -dc), min(Z.shape[1], Z.shape[1] - dc)
        if r1 > r0 and c1 > c0:
            S[r0:r1, c0:c1] = Zf[r0 + dr:r1 + dr, c0 + dc:c1 + dc]
        shade |= (S - Zf) > tan_el * d
    return shade


def cell_blocks(A: np.ndarray, mask: np.ndarray, rr0: int, cc0: int, k: int, fn) -> np.ndarray:
    """fn over the k x k DEM block under each masked Sentinel cell (NaN elsewhere)."""
    H, W = mask.shape
    out = np.full((H, W), np.nan)
    for i in range(H):
        r0 = rr0 + i * k
        if r0 < 0 or r0 + k > A.shape[0]:
            continue
        for j in np.where(mask[i])[0]:
            c0 = cc0 + j * k
            if 0 <= c0 and c0 + k <= A.shape[1]:
                out[i, j] = fn(A[r0:r0 + k, c0:c0 + k])
    return out


def sample(src, A: np.ndarray, x, y) -> np.ndarray:
    """Nearest-cell value of array A (on src's grid) at points; NaN off the grid."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    r = np.floor((src.bounds.top - y) / src.res[1]).astype(int)
    c = np.floor((x - src.bounds.left) / src.res[0]).astype(int)
    ok = (r >= 0) & (r < A.shape[0]) & (c >= 0) & (c < A.shape[1])
    out = np.full(len(x), np.nan)
    out[ok] = A[r[ok], c[ok]]
    return out


def network_states():
    """Months per state from the D-178 network-median level."""
    M = _wells_monthly()["h_median"].dropna()
    M.index = pd.to_datetime(M.index)
    q = C.SLACK_FLOW_STATE_DECILE
    return M, {"wet": M.index[M >= M.quantile(1 - q)], "dry": M.index[M <= M.quantile(q)], "mean": M.index}


def well_heads(states: dict) -> dict:
    el = pd.read_csv(INT_WELL_ELEVATIONS)
    el["k"] = el["Name_norm"].str.lower()
    el = el.dropna(subset=["ground_elev_m"]).drop_duplicates("k").set_index("k")
    lev = pd.read_csv(INT_WELLS_ALL, index_col=0, float_precision="round_trip")
    lev.index = pd.to_datetime(lev.index)
    lev.columns = lev.columns.str.lower()
    ks = [k for k in lev.columns if k in el.index]
    n_rec = lev[ks].notna().sum()
    # One well set for all three states, so the surfaces differ only by the state:
    # a well enters only if it has SLACK_FLOW_MIN_STATE_MONTHS in every state.
    enough = {st: lev.reindex(months)[ks].notna().sum() >= C.SLACK_FLOW_MIN_STATE_MONTHS
              for st, months in states.items()}
    keep = [k for k in ks if all(enough[st][k] for st in states)]
    out = {}
    for st, months in states.items():
        v = lev.reindex(months)[ks]
        n = v.notna().sum()
        out[st] = pd.DataFrame({"well": keep, "E": el.loc[keep, "E"].values, "N": el.loc[keep, "N"].values,
                                "ground": el.loc[keep, "ground_elev_m"].values,
                                "head": el.loc[keep, "ground_elev_m"].values + v[keep].mean().values,
                                "n_months": n[keep].values, "n_record": n_rec[keep].values})
    return out, lev, el


# ═══════════════════════════════════════════════════════════════════════════
# KRIGING
# ═══════════════════════════════════════════════════════════════════════════
class Surface:
    """One drift choice: data assembly, variogram, prediction, leave-one-out."""

    def __init__(self, wells: pd.DataFrame, anchors: np.ndarray, drift: str, rasters: dict, src, fixed=None):
        """anchors: sea anchors, all at the coastal head; fixed: (xy, z) boundary anchors with their own heads."""
        self.wells, self.anchors, self.drift, self.rasters, self.src = wells, anchors, drift, rasters, src
        self.fixed = fixed if fixed is not None and len(fixed[0]) else None
        self.dw = None if drift == "o" else sample(src, rasters[drift], wells.E, wells.N)[:, None]
        self.da = None if drift == "o" else sample(src, rasters[drift], anchors[:, 0], anchors[:, 1])[:, None]
        self.df = (None if drift == "o" or self.fixed is None
                   else sample(src, rasters[drift], self.fixed[0][:, 0], self.fixed[0][:, 1])[:, None])

    def _vgm(self, keep: np.ndarray) -> dict:
        w = self.wells[keep]
        r = ols_residuals(w["head"].values, None if self.dw is None else self.dw[keep])
        lag, gam, cnt = empirical_variogram(w[["E", "N"]].values, r, C.SLACK_FLOW_VGM_BINS,
                                            C.SLACK_FLOW_VGM_MAX_LAG_M)
        return fit_spherical(lag, gam, cnt, C.SLACK_FLOW_VGM_MAX_LAG_M)

    def _system(self, keep, head_sea):
        w = self.wells[keep]
        xy = np.vstack([w[["E", "N"]].values, self.anchors])
        z = np.concatenate([w["head"].values, np.full(len(self.anchors), head_sea)])
        D = None if self.dw is None else np.vstack([self.dw[keep], self.da])
        if self.fixed is not None:
            xy = np.vstack([xy, self.fixed[0]]); z = np.concatenate([z, self.fixed[1]])
            D = None if D is None else np.vstack([D, self.df])
        return xy, z, D

    def predict(self, head_sea, txy, tD, keep=None):
        keep = np.ones(len(self.wells), bool) if keep is None else keep
        vgm = self._vgm(keep)
        xy, z, D = self._system(keep, head_sea)
        p, se = ked(xy, z, D, txy, tD, vgm)
        return p, se, vgm

    def loo(self, head_sea, idx=None) -> np.ndarray:
        """Prediction minus observation at each well (or at wells idx), the well out
        of both the kriging system and the variogram."""
        idx = range(len(self.wells)) if idx is None else idx
        err = {}
        for i in idx:
            keep = np.ones(len(self.wells), bool); keep[i] = False
            t = self.wells.iloc[[i]]
            tD = None if self.dw is None else self.dw[[i]]
            p, _, _ = self.predict(head_sea, t[["E", "N"]].values, tD, keep)
            err[i] = p[0] - t["head"].values[0]
        return pd.Series(err)


def fit_coastal_head(surf: Surface, coastal_idx, lo, hi):
    """The head in [lo, hi] minimising the median |LOO error| at the coastal wells,
    with the error curve on a regular grid for the output."""
    f = lambda h: float(np.median(np.abs(surf.loo(h, coastal_idx))))  # noqa: E731
    grid = np.linspace(lo, hi, C.SLACK_FLOW_HEAD_GRID_N)
    curve = pd.DataFrame({"head_m": grid, "median_abs_err_m": [f(h) for h in grid]})
    r = minimize_scalar(f, bounds=(lo, hi), method="bounded", options={"xatol": C.SLACK_FLOW_HEAD_XATOL_M})
    flat = (curve["median_abs_err_m"].max() - curve["median_abs_err_m"].min()) <= C.SLACK_FLOW_LOO_TIE_M
    return float(r.x), float(r.fun), curve, bool(flat)


# ═══════════════════════════════════════════════════════════════════════════
# GEOMETRY HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def grad_field(H: np.ndarray, res: float):
    """-grad h on the grid (rows run north to south). Returns (east, north) components."""
    gy, gx = np.gradient(H, res)            # d/drow, d/dcol
    return -gx, gy                            # -dh/dE ; -dh/dN = +dh/drow (rows go south)


def az_of(u, v):
    return (np.degrees(np.arctan2(u, v)) + 360.0) % 360.0


def ang_diff(a, b):
    d = np.abs((np.asarray(a) - np.asarray(b) + 180.0) % 360.0 - 180.0)
    return d


def bilinear(grid_vals, x0, y0, res, x, y):
    """Bilinear sample of a north-up grid whose node (0,0) is at (x0, y0)."""
    cols = (np.asarray(x) - x0) / res
    rows = (y0 - np.asarray(y)) / res
    return map_coordinates(grid_vals, [rows, cols], order=1, mode="constant", cval=np.nan)


def _kml(path, placemarks: list[str], name: str):
    body = "\n".join(placemarks)
    path.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">'
                    f"<Document><name>{name}</name>\n{body}\n</Document></kml>\n", encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# TRANSECTS
# ═══════════════════════════════════════════════════════════════════════════
def coast_points(coast: LineString, area, inland_pt):
    """Candidate starts along the Caernarfon Bay HWM with the local landward normal."""
    out = []
    shapely.prepare(area)
    step_m, half = C.SLACK_FLOW_TRANSECT_COAST_STEP_M, C.SLACK_FLOW_SHORE_TANGENT_M / 2
    for t in np.arange(half, coast.length - half, step_m):
        p = coast.interpolate(t)
        if p.distance(area) > C.SLACK_FLOW_TRANSECT_BAND_M:
            continue
        a, b = coast.interpolate(t - half), coast.interpolate(t + half)
        tx, ty = b.x - a.x, b.y - a.y
        n1 = np.array([-ty, tx]) / np.hypot(tx, ty)
        probe = Point(p.x + C.SLACK_FLOW_SEA_PROBE_M * n1[0], p.y + C.SLACK_FLOW_SEA_PROBE_M * n1[1])
        n = n1 if area.contains(probe) else -n1
        az = az_of(n[0], n[1])
        lo, hi = C.SLACK_FLOW_BAY_LANDWARD_AZ
        if lo <= az <= hi:
            out.append((p.x, p.y, az))
    return out


def ray(x0, y0, az, area_b, max_len=C.SLACK_FLOW_RAY_MAX_M):
    """From (x0, y0) along az, within the (buffered, prepared) study area, to where it
    first leaves it."""
    a = np.radians(az)
    ln = LineString([(x0, y0), (x0 + max_len * np.sin(a), y0 + max_len * np.cos(a))])
    seg = ln.intersection(area_b)
    if seg.is_empty:
        return None
    parts = list(seg.geoms) if hasattr(seg, "geoms") else [seg]
    first = min(parts, key=lambda g: Point(x0, y0).distance(g))
    c = list(first.coords)
    far = max(c, key=lambda q: np.hypot(q[0] - x0, q[1] - y0))
    return LineString([(x0, y0), far])


def wells_on(line: LineString, wells: pd.DataFrame):
    """Wells within the band: index, distance along the line."""
    pts = shapely.points(wells.E.values, wells.N.values)
    near = shapely.distance(line, pts) <= C.SLACK_FLOW_TRANSECT_BAND_M
    idx = list(wells.index[near])
    along = list(shapely.line_locate_point(line, pts[near]))
    return idx, along


def supported(line, wells):
    idx, along = wells_on(line, wells)
    if len(idx) < C.SLACK_FLOW_TRANSECT_MIN_WELLS:
        return False, idx
    span = (max(along) - min(along)) / line.length
    return span >= C.SLACK_FLOW_TRANSECT_MIN_SPAN, idx


def choose_transects(coast, area, wells, high_xy):
    """The radial fan and the network-supported coast-normal series (one radial merged)."""
    inland = Point(high_xy)
    area_b = area.buffer(C.SLACK_FLOW_TRANSECT_BAND_M)
    shapely.prepare(area_b)
    cpts = coast_points(coast, area, inland)
    cands = []
    for x, y, az in cpts:
        for d in np.arange(-C.SLACK_FLOW_TRANSECT_AZ_TOL_DEG, C.SLACK_FLOW_TRANSECT_AZ_TOL_DEG + 1e-9,
                           C.SLACK_FLOW_TRANSECT_AZ_STEP_DEG):
            ln = ray(x, y, (az + d) % 360, area_b)
            if ln is None or ln.length < C.SLACK_FLOW_TRANSECT_MIN_LEN_M:
                continue
            ok, idx = supported(ln, wells)
            if ok:
                cands.append({"line": ln, "start": (x, y), "az": (az + d) % 360, "normal_az": az, "idx": idx})
    # radials
    radials = []
    for az in C.SLACK_FLOW_RADIAL_AZ:
        a = np.radians(az)
        ln = LineString([high_xy, (high_xy[0] + C.SLACK_FLOW_RAY_MAX_M * np.sin(a),
                                   high_xy[1] + C.SLACK_FLOW_RAY_MAX_M * np.cos(a))])
        ln = ln.intersection(area_b)
        if ln.is_empty:
            continue
        if hasattr(ln, "geoms"):
            ln = min(ln.geoms, key=lambda g: inland.distance(g))
        radials.append({"az": az, "line": LineString([high_xy, ln.coords[-1]])})
    # merged radial: the fan azimuth closest to the local normal (reversed: landward) where it meets the coast
    merged = None
    best = None
    for rd in radials:
        end = Point(rd["line"].coords[-1])
        near = min(cpts or [(0, 0, 0)],
                   key=lambda q: end.distance(Point(q[0], q[1])))
        if end.distance(Point(near[0], near[1])) > C.SLACK_FLOW_MERGE_REACH_STEPS * C.SLACK_FLOW_TRANSECT_COAST_STEP_M:
            continue
        dev = ang_diff((rd["az"] + 180) % 360, near[2])
        ok, idx = supported(rd["line"], wells)
        if dev <= C.SLACK_FLOW_TRANSECT_AZ_TOL_DEG and ok and (best is None or dev < best):
            best, merged = dev, {**rd, "idx": idx, "start": (end.x, end.y), "normal_az": near[2]}
    chosen, covered = [], set()
    w_rec = wells["n_record"]
    if merged is not None:
        chosen.append({"kind": "coast-normal (merged radial)", **merged}); covered |= set(merged["idx"])
    while True:
        best_c, best_gain = None, 0.0
        for c in cands:
            if any(Point(c["start"]).distance(Point(k["start"])) < C.SLACK_FLOW_TRANSECT_MIN_SEP_M for k in chosen):
                continue
            new = set(c["idx"]) - covered
            if len(new) < C.SLACK_FLOW_TRANSECT_MIN_NEW_WELLS:
                continue
            gain = float(w_rec.loc[list(new)].sum())
            if gain > best_gain:
                best_c, best_gain = c, gain
        if best_c is None:
            break
        chosen.append({"kind": "coast-normal", **best_c}); covered |= set(best_c["idx"])
    fan = [r for r in radials if merged is None or r["az"] != merged["az"]]
    for r in fan:
        r["idx"], _ = wells_on(r["line"], wells)
    return chosen, fan, merged is not None


def ridge_depths(lev: pd.DataFrame, states: dict) -> dict:
    """Depth of the water table below ground at the ridge well, per state: the mean over its
    months in the state, or, with too few, its record's extreme in the state's direction."""
    s = lev[C.SLACK_FLOW_RIDGE_WELL].dropna()
    out = {}
    for st, months in states.items():
        v = s.reindex(pd.DatetimeIndex(months)).dropna()
        if len(v) >= C.SLACK_FLOW_RIDGE_MIN_MONTHS:
            out[st] = (float(-v.mean()), f"mean of {len(v)} {st}-state months")
        elif st == "wet":
            out[st] = (float(-s.max()), "shallowest reading (no wet-state month in the record)")
        else:
            out[st] = (float(-s.min()), f"deepest reading (no {st}-state month in the record): a lower bound")
    return out


def boundary_arcs(area, coast, src, Z):
    """Points every SLACK_FLOW_SEA_SPACING_M along the study-area boundary from the river start:
    downstream to the HWM (river), and the other way along the divide until the coast is within
    SLACK_FLOW_COASTAL_WELL_M or the DEM ends (ridge). Returns (ridge_xy, river_xy)."""
    ring = LineString(area.exterior.coords)
    Lr = ring.length
    s0 = ring.project(Point(C.STUDY_AREA_RIVER_START))
    zat = lambda t: sample(src, Z, [ring.interpolate(t % Lr).x], [ring.interpolate(t % Lr).y])[0]  # noqa: E731
    down = 1 if zat(s0 + C.SLACK_FLOW_RIVER_PROBE_M) < zat(s0 - C.SLACK_FLOW_RIVER_PROBE_M) else -1
    step = C.SLACK_FLOW_SEA_SPACING_M
    river, ridge = [], []
    for k in range(int(Lr // step)):
        p = ring.interpolate((s0 + down * k * step) % Lr)
        if coast.distance(p) <= step:
            break
        river.append((p.x, p.y))
    for k in range(1, int(Lr // step)):
        p = ring.interpolate((s0 - down * k * step) % Lr)
        if coast.distance(p) <= C.SLACK_FLOW_COASTAL_WELL_M or not np.isfinite(sample(src, Z, [p.x], [p.y])[0]):
            break
        ridge.append((p.x, p.y))
    return np.array(ridge).reshape(-1, 2), np.array(river).reshape(-1, 2)


def lake_boundary(states: dict):
    """Llyn Rhos-Ddu: points every SLACK_FLOW_SEA_SPACING_M round its Features.kml outline, and its
    level per state from the lake gauge (gauge datum + reading, the wells' convention), with the
    gauge record's mean for the LiDAR check. Returns (xy, {state: level}, outline, record mean)."""
    from utils.kml_io import read_kml                          # noqa: PLC0415
    feats = read_kml(DATA_KML_FEATURES, quiet=True)
    hit = [g for n, g in zip(feats["Name"], feats.geometry) if str(n).strip() == C.RANWELL_PENLON_NAME]
    if not hit:
        warn(f"lake: no '{C.RANWELL_PENLON_NAME}' placemark in {DATA_KML_FEATURES.name}; no lake boundary")
        return np.zeros((0, 2)), {}, None, np.nan
    lake = hit[0]
    ring = LineString(lake.exterior.coords)
    xy = np.array([ring.interpolate(t).coords[0][:2] for t in np.arange(0, ring.length, C.SLACK_FLOW_SEA_SPACING_M)])
    wc = pd.read_csv(INT_WELLS_CLEAN, index_col=0)
    wc.index = pd.to_datetime(wc.index)
    col = next((c for c in wc.columns if c.strip().lower() in C.LAKE_GAUGE_KEYS), None)
    el = pd.read_csv(INT_WELL_ELEVATIONS)
    row = el[el["Name"].str.strip().str.lower().isin(C.LAKE_GAUGE_KEYS)]
    if col is None or row.empty:
        warn("lake: gauge record or gauge datum not found; no lake boundary")
        return np.zeros((0, 2)), {}, lake, np.nan
    rec = wc[col].dropna() + float(row["ground_elev_m"].iloc[0])
    lev = {st: float(rec.reindex(pd.DatetimeIndex(m)).dropna().mean()) for st, m in states.items()}
    return xy, lev, lake, float(rec.mean())


def channel_level(src, Z, xy: np.ndarray) -> np.ndarray:
    """Lowest DEM within SLACK_FLOW_RIVER_SNAP_M of each point: the channel, not its bank."""
    dres = float(src.res[0]); k = max(1, int(round(C.SLACK_FLOW_RIVER_SNAP_M / dres)))
    out = np.full(len(xy), np.nan)
    for i, (x, y) in enumerate(xy):
        r = int((src.bounds.top - y) / dres); c = int((x - src.bounds.left) / dres)
        blk = Z[max(r - k, 0):r + k + 1, max(c - k, 0):c + k + 1]
        if blk.size:
            out[i] = float(np.nanmin(blk))
    return out


def arrow_length(grad):
    """Arrow length (m) on a log scale of |grad h|, shared by the figures and the KML."""
    L0 = C.SLACK_FLOW_ARROW_GRID_M * C.SLACK_FLOW_ARROW_LEN_FRAC
    f = np.clip((np.log10(np.asarray(grad, float)) - np.log10(C.SLACK_FLOW_MIN_GRADIENT))
                / C.SLACK_FLOW_ARROW_DECADES, 0, 1)
    return L0 * (C.SLACK_FLOW_ARROW_MIN_FRAC + (1 - C.SLACK_FLOW_ARROW_MIN_FRAC) * f)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main(no_fig: bool = False) -> int:
    banner(SCRIPT_ID, "The water table by kriging with an external drift, and slack flow", __version__)
    DIR_49.mkdir(parents=True, exist_ok=True)
    rn = ReportNumbers()

    phase(1, "Inputs, states and tidal levels")
    area = _geojson_geom(DATA_STUDY_AREA_GEOJSON)
    coast = _geojson_geom(DATA_COASTLINE_HWM)
    tide = tidal_levels()
    src, Z = load_dem()
    M, states = network_states()
    heads, lev, el = well_heads(states)
    for st in STATES:
        info(f"{st}: {len(states[st])} months, {len(heads[st])} wells")
    mid = 0.5 * (tide["MTL"] + tide["MHW"])
    hwm_pts = [coast.interpolate(t) for t in np.arange(0, coast.length, C.SLACK_FLOW_HWM_SAMPLE_M)]
    hwm_z = sample(src, Z, [p.x for p in hwm_pts], [p.y for p in hwm_pts])
    hwm_med = float(np.nanmedian(hwm_z))
    info(f"tides (NP201B-26): mean tide level {tide['MTL']:.3f} m, MHW {tide['MHW']:.3f} m OD; "
         f"LiDAR along the HWM line {hwm_med:.3f} m")
    if abs(hwm_med - tide["MHW"]) > C.SLACK_FLOW_HWM_OFFSET_TOL_M:
        warn(f"the committed HWM line reads {hwm_med:.3f} m on the LiDAR, {tide['MHW'] - hwm_med:.3f} m below "
             f"the Admiralty mean high water — the anchors sit on the line whatever head they carry")
    rn.add("tide_mean_tide_level_m", tide["MTL"], note="mean of MHWS, MHWN, MLWN, MLWS, NP201B-26 Caernarfon Bar")
    rn.add("tide_mhw_m", tide["MHW"], note="mean of MHWS and MHWN, NP201B-26 Caernarfon Bar")
    rn.add("hwm_line_lidar_median_m", hwm_med, note="median LiDAR elevation along coastline_hwm.geojson")

    phase(2, "Drift rasters, grid and sea anchors")
    dres = float(src.res[0])
    rasters = drift_rasters(Z, dres)
    res = C.SLACK_FLOW_GRID_M
    x0 = np.floor(area.bounds[0] / res) * res; x1 = np.ceil(area.bounds[2] / res) * res
    y1 = np.ceil(area.bounds[3] / res) * res; y0 = np.floor(area.bounds[1] / res) * res
    gx = np.arange(x0 + res / 2, x1, res); gy = np.arange(y1 - res / 2, y0, -res)
    GX, GY = np.meshgrid(gx, gy)
    inside = shapely.contains_xy(area, GX, GY)
    on_dem = np.isfinite(sample(src, rasters["e"], GX.ravel(), GY.ravel())).reshape(GX.shape)
    node = inside & on_dem
    txy = np.column_stack([GX[node], GY[node]])
    tD = {k: sample(src, rasters[k], txy[:, 0], txy[:, 1])[:, None] for k in ("s", "e", "r")}
    tD["o"] = None
    Zb = uniform_filter(Z, size=max(1, int(round(res / dres))), mode="nearest")
    ground_t = sample(src, Zb, txy[:, 0], txy[:, 1])
    info(f"grid {res} m: {node.sum()} nodes in the study area on the DEM "
         f"({(inside & ~on_dem).sum()} study-area nodes off the DEM, not estimated)")
    rn.add("grid_nodes_off_dem", int((inside & ~on_dem).sum()), unit="nodes",
           note="study-area nodes west of the DEM (the hand-drawn west end, D-203); not estimated")
    buf = area.buffer(C.SLACK_FLOW_SEA_BUFFER_M)
    anchors = np.array([coast.interpolate(t).coords[0] for t in np.arange(0, coast.length, C.SLACK_FLOW_SEA_SPACING_M)])
    anchors = anchors[[buf.contains(Point(p)) for p in anchors]]
    anchors = anchors[np.isfinite(sample(src, rasters["e"], anchors[:, 0], anchors[:, 1]))]
    info(f"{len(anchors)} sea anchors on the DEM within {C.SLACK_FLOW_SEA_BUFFER_M:g} m of the study area")
    ridge_xy, river_xy = boundary_arcs(area, coast, src, Z)
    rdepth = ridge_depths(lev, states)
    lake_xy, lake_lev, lake_poly, lake_rec = lake_boundary(states)
    if len(lake_xy):
        rp = lake_poly.representative_point()
        lz = float(sample(src, Z, [rp.x], [rp.y])[0])
        info(f"lake: {len(lake_xy)} points; level wet {lake_lev['wet']:.3f}, mean {lake_lev['mean']:.3f}, "
             f"dry {lake_lev['dry']:.3f} m OD (gauge); LiDAR water surface {lz:.3f} m OD")
        for st in STATES:
            rn.add(f"lake_level_{st}_m", lake_lev[st], era=st, note="Llyn Rhos-Ddu gauge, mean of the state's months")
        rn.add("lake_lidar_m", float(lz), note="LiDAR at a point inside the lake outline (the water surface at survey)")
        rn.add("lake_gauge_record_mean_m", lake_rec)
    ridge_ground = sample(src, Z, ridge_xy[:, 0], ridge_xy[:, 1])
    river_z = channel_level(src, Z, river_xy)
    fixed_b = {st: (np.vstack([ridge_xy, river_xy]),
                    np.concatenate([ridge_ground - rdepth[st][0], river_z])) for st in STATES}
    for st in STATES:
        info(f"ridge depth, {st}: {rdepth[st][0]:.3f} m below ground ({rdepth[st][1]})")
        rn.add(f"ridge_depth_{st}_m", rdepth[st][0], era=st, note=f"{C.SLACK_FLOW_RIDGE_WELL}: {rdepth[st][1]}")
    info(f"{len(ridge_xy)} ridge anchors (ground {np.nanmin(ridge_ground):.1f}-{np.nanmax(ridge_ground):.1f} m OD), "
         f"{len(river_xy)} river anchors (channel {np.nanmin(river_z):.2f}-{np.nanmax(river_z):.2f} m OD)")
    rn.add("n_ridge_anchors", len(ridge_xy), unit="anchors"); rn.add("n_river_anchors", len(river_xy), unit="anchors")
    ba = pd.DataFrame({"E": np.r_[ridge_xy[:, 0], river_xy[:, 0], lake_xy[:, 0]],
                       "N": np.r_[ridge_xy[:, 1], river_xy[:, 1], lake_xy[:, 1]],
                       "kind": ["ridge"] * len(ridge_xy) + ["river"] * len(river_xy) + ["lake"] * len(lake_xy),
                       "ground_m": np.r_[ridge_ground, sample(src, Z, river_xy[:, 0], river_xy[:, 1]),
                                         sample(src, Z, lake_xy[:, 0], lake_xy[:, 1])]})
    for st in STATES:
        ba[f"head_{st}_m"] = np.r_[fixed_b[st][1], np.full(len(lake_xy), lake_lev.get(st, np.nan))]
    ba.to_csv(OUT_49_BOUNDARY_ANCHORS, index=False); saved(OUT_49_BOUNDARY_ANCHORS)

    # Sentinel ever-wet cells (10 m) and their floors
    z = np.load(SENTINEL_CELL_THRESHOLDS)
    L, B, R, T, sres = [int(v) for v in z["grid"]]
    s_cell = z["h_wet_floor"]; ever = np.isfinite(s_cell) & z["floor"]
    H, W = s_cell.shape
    cx = L + (np.arange(W) + 0.5) * sres; cy = T - (np.arange(H) + 0.5) * sres
    CX, CY = np.meshgrid(cx, cy)
    kk = int(round(sres / dres))
    rr0 = int(round((src.bounds.top - T) / dres)); cc0 = int(round((L - src.bounds.left) / dres))
    zf = cell_blocks(Z, ever, rr0, cc0, kk, lambda b: np.percentile(b, C.SLACK_FLOW_FLOOR_PCTL))
    ever_node = np.zeros(len(txy), bool); floor_node = np.zeros(len(txy), bool)
    ci = np.floor((txy[:, 0] - L) / sres).astype(int); ri = np.floor((T - txy[:, 1]) / sres).astype(int)
    okc = (ri >= 0) & (ri < H) & (ci >= 0) & (ci < W)
    ever_node[okc] = ever[ri[okc], ci[okc]]
    floor_node[okc] = z["floor"][ri[okc], ci[okc]]
    # The physical test is judged only where Sentinel can see the ground (its floor
    # mask: canopy and non-floor excluded), and outside the cells it has seen wet.
    # Martin 2026-09-27: under canopy Sentinel cannot tell wet forest floor from dry,
    # so counting it as a fault penalised the drift-free surface for ground no one
    # observed.
    test_node = floor_node & ~ever_node
    info(f"physical test on {test_node.sum()} nodes Sentinel observes and never saw wet")

    phase(3, "Landward boundary: each part kept only if it does not worsen the wells near it")
    wm = heads["mean"]
    rw = C.SLACK_FLOW_RIDGE_WELL
    rw_xy = np.array([[el.loc[rw, "E"], el.loc[rw, "N"]]]) if rw in el.index else np.zeros((0, 2))
    rw_z = {st: (np.array([el.loc[rw, "ground_elev_m"] - rdepth[st][0]]) if len(rw_xy) else np.zeros(0))
            for st in STATES}
    parts = [   # in order; each is judged given the parts already kept
        ("river", river_xy, {st: river_z for st in STATES}),
        ("lake", lake_xy, {st: np.full(len(lake_xy), lake_lev.get(st, np.nan)) for st in STATES}),
        (f"ridge well {rw}", rw_xy, rw_z),
        ("ridge line", ridge_xy, {st: ridge_ground - rdepth[st][0] for st in STATES}),
    ]
    b_all = np.vstack([p_[1] for p_ in parts if len(p_[1])])
    b_pts = shapely.multipoints(b_all) if len(b_all) else None   # points, not a line: the parts are separate
    near_b = ([] if b_pts is None else
              list(np.where(shapely.distance(b_pts, shapely.points(wm.E.values, wm.N.values))
                            <= C.SLACK_FLOW_BOUNDARY_TEST_M)[0]))

    def fixed_of(kept, st):
        if not kept:
            return None
        return (np.vstack([p_[1] for p_ in kept]), np.concatenate([p_[2][st] for p_ in kept]))

    def near_loo(kept):
        e = Surface(wm, anchors, "o", rasters, src, fixed_of(kept, "mean")).loo(mid, near_b)
        return float(np.median(np.abs(e))), float(np.percentile(np.abs(e), C.SLACK_FLOW_LOO_PCTL))

    kept, bt = [], []
    base_m, base_p = near_loo(kept)
    bt.append({"step": "none", "n_wells": len(near_b), "median_abs_m": base_m,
               f"p{C.SLACK_FLOW_LOO_PCTL}_abs_m": base_p, "kept": True})
    for part in parts:
        if not len(part[1]):
            continue
        m_, p_ = near_loo(kept + [part])
        ok_ = m_ <= base_m + C.SLACK_FLOW_LOO_TIE_M
        bt.append({"step": f"+ {part[0]}", "n_wells": len(near_b), "median_abs_m": m_,
                   f"p{C.SLACK_FLOW_LOO_PCTL}_abs_m": p_, "kept": ok_})
        result(f"boundary: {part[0]}", f"{'kept' if ok_ else 'dropped'} (near-boundary LOO {m_:.3f} m against "
               f"{base_m:.3f}; p{C.SLACK_FLOW_LOO_PCTL} {p_:.3f} m)")
        rn.add(f"boundary_kept_{part[0].replace(' ', '_')}", bool(ok_), unit="",
               note=f"near-boundary LOO {m_:.3f} m against {base_m:.3f} m, {len(near_b)} wells")
        if ok_:
            kept.append(part); base_m, base_p = m_, p_
    if len(rw_xy) and rw in lev.columns:
        obs_rw = float(el.loc[rw, "ground_elev_m"] + lev[rw].mean())
        p_rw, _, _ = Surface(wm, anchors, "o", rasters, src).predict(mid, rw_xy, None)
        bt.append({"step": f"check: {rw} predicted without any boundary", "observed_m": obs_rw,
                   "predicted_m": float(p_rw[0]), "error_m": float(p_rw[0] - obs_rw)})
        rn.add("ridge_well_head_m", obs_rw, note=f"{rw}, mean of its record")
        rn.add("ridge_well_error_without_boundary_m", float(p_rw[0] - obs_rw),
               note="kriged surface without the boundary minus the ridge well's head")
    pd.DataFrame(bt).to_csv(OUT_49_BOUNDARY_TEST, index=False); saved(OUT_49_BOUNDARY_TEST)
    kept_names = [p_[0] for p_ in kept]
    info(f"landward boundary kept: {', '.join(kept_names) if kept_names else 'none'}")
    fixed = {st: fixed_of(kept, st) for st in STATES}
    ridge_line_kept = "ridge line" in kept_names

    phase(4, "Drift selection: coastal head fitted per drift, leave-one-well-out, physical test")
    dist_coast = np.array([coast.distance(Point(e, n)) for e, n in zip(wm.E, wm.N)])
    coastal_idx = list(np.where(dist_coast <= C.SLACK_FLOW_COASTAL_WELL_M)[0])
    info(f"{len(coastal_idx)} coastal wells within {C.SLACK_FLOW_COASTAL_WELL_M:g} m of the HWM decide the head")
    rows, curves, fits = [], [], {}
    for d in DRIFTS:
        S = Surface(wm, anchors, d, rasters, src, fixed["mean"])
        h_fit, e_fit, curve, flat = fit_coastal_head(S, coastal_idx, tide["MTL"], tide["MHW"])
        h_use = mid if flat else h_fit
        curve["drift"] = d; curves.append(curve)
        p, se, vgm = S.predict(h_use, txy, tD[d])
        above = (p - ground_t > C.SLACK_FLOW_ABOVE_GROUND_TOL_M) & test_node
        share = float(above.sum() / max(test_node.sum(), 1))
        row = {"drift": d, "drift_name": DRIFT_NAME[d], "coastal_head_fit_m": h_fit, "coastal_head_used_m": h_use,
               "coastal_curve_flat": flat, "above_ground_share": share,
               "passes_physical": share <= C.SLACK_FLOW_ABOVE_GROUND_MAX,
               "vgm_nugget": vgm["nugget"], "vgm_psill": vgm["psill"], "vgm_range_m": vgm["range"], "vgm_ok": vgm["ok"]}
        for st in STATES:
            Sst = Surface(heads[st], anchors, d, rasters, src, fixed[st])
            e = Sst.loo(h_use)
            row[f"loo_median_abs_{st}_m"] = float(np.median(np.abs(e)))
            row[f"loo_bias_{st}_m"] = float(np.median(e))
            row[f"loo_p{C.SLACK_FLOW_LOO_PCTL}_abs_{st}_m"] = float(np.percentile(np.abs(e), C.SLACK_FLOW_LOO_PCTL))
            if st == "mean":
                fits[d] = {"loo": e}
        rows.append(row)
        result(f"drift {d}", f"head {h_use:.3f} m{' (wells cannot choose: midpoint)' if flat else ''}; "
               f"LOO {row['loo_median_abs_mean_m']:.3f} m; above ground {share:.3f}; vgm ok={vgm['ok']}")
        if not vgm["ok"]:
            warn(f"drift {d}: variogram fit did not converge ({vgm.get('why', '')}); the starting model was used")
    sel = pd.DataFrame(rows)
    sel.to_csv(OUT_49_DRIFT_SELECTION, index=False); saved(OUT_49_DRIFT_SELECTION)
    pd.concat(curves).to_csv(OUT_49_COASTAL_HEAD, index=False); saved(OUT_49_COASTAL_HEAD)
    passing = sel[sel["passes_physical"]]
    pool = passing if len(passing) else sel
    if not len(passing):
        warn("no drift passes the physical test; the best by leave-one-out is used and the report says so")
    best_loo = pool["loo_median_abs_mean_m"].min()
    tied = pool[pool["loo_median_abs_mean_m"] <= best_loo + C.SLACK_FLOW_LOO_TIE_M]
    chosen = min(tied["drift"], key=DRIFTS.index)
    ranked = pool.sort_values("loo_median_abs_mean_m")["drift"].tolist()
    runner = next((d for d in ranked if d != chosen), None)
    head_sea = float(sel.set_index("drift").loc[chosen, "coastal_head_used_m"])
    result("selected drift", f"{DRIFT_NAME[chosen]}; coastal head {head_sea:.3f} m OD; runner-up {runner}")
    rn.add("drift_selected", chosen, unit="", note=DRIFT_NAME[chosen])
    rn.add("coastal_head_m", head_sea, note="fitted to the coastal wells in [mean tide level, MHW]")
    rn.add("coastal_head_flat", bool(sel.set_index("drift").loc[chosen, "coastal_curve_flat"]), unit="",
           note="True: the coastal wells could not choose and the midpoint is used")
    for st in STATES:
        rn.add(f"loo_median_abs_{st}_m", sel.set_index("drift").loc[chosen, f"loo_median_abs_{st}_m"], era=st)
        rn.add(f"loo_bias_{st}_m", sel.set_index("drift").loc[chosen, f"loo_bias_{st}_m"], era=st)
    rn.add("n_coastal_wells", len(coastal_idx), unit="wells")

    phase(5, "The surfaces, wet, mean and dry")
    grids, ses = {}, {}
    tr = from_origin(x0, y1, res, res)
    loo_rows = []
    for st in STATES:
        S = Surface(heads[st], anchors, chosen, rasters, src, fixed[st])
        p, se, _ = S.predict(head_sea, txy, tD[chosen])
        G = np.full(GX.shape, np.nan); G[node] = p
        E = np.full(GX.shape, np.nan); E[node] = se
        grids[st], ses[st] = G, E
        for arr, path in ((G, out_49_surface(st)), (E, out_49_se(st))):
            with rasterio.open(path, "w", driver="GTiff", height=G.shape[0], width=G.shape[1], count=1,
                               dtype="float32", crs=C.SLACK_FLOW_CRS, transform=tr,
                               nodata=C.SLACK_FLOW_TIF_NODATA) as o:
                o.write(np.where(np.isfinite(arr), arr, C.SLACK_FLOW_TIF_NODATA).astype("float32"), 1)
            saved(path)
        e = S.loo(head_sea)
        for i, v in e.items():
            w = heads[st].iloc[i]
            loo_rows.append({"state": st, "well": w.well, "E": w.E, "N": w.N, "observed_m": w["head"],
                             "predicted_m": w["head"] + v, "error_m": v})
    pd.DataFrame(loo_rows).to_csv(OUT_49_LOO, index=False); saved(OUT_49_LOO)
    # the radial fan starts at the highest dipwell in the wet state, not at the surface maximum,
    # which the ridge boundary would move onto the ridge
    wh = heads["wet"].loc[heads["wet"]["head"].idxmax()]
    high_xy = (float(wh.E), float(wh.N))
    rn.add("wet_high_E", high_xy[0], unit="m"); rn.add("wet_high_N", high_xy[1], unit="m")
    rn.add("wet_high_head_m", float(wh["head"]), era="wet", well=wh.well, note="highest dipwell, wet state")

    phase(6, "The Sentinel check")
    s_range = (float(np.nanmin(s_cell[ever])), float(np.nanmax(s_cell[ever])))
    in_rng = M[(M >= s_range[0]) & (M <= s_range[1])]
    offs = []
    ex, ey, ez, es = CX[ever], CY[ever], zf[ever], s_cell[ever]
    for _, w in heads["mean"].iterrows():
        near = (np.hypot(ex - w.E, ey - w.N) <= C.SLACK_FLOW_BIAS_RADIUS_M) & np.isfinite(ez)
        if near.sum() < C.SLACK_FLOW_BIAS_MIN_CELLS or w.well not in lev.columns:
            continue
        obs = (w.ground + lev[w.well]).reindex(in_rng.index).dropna()
        if len(obs) < C.SLACK_FLOW_BIAS_MIN_MONTHS:
            continue
        pred = np.array([np.median(ez[near] + m - es[near]) for m in in_rng.reindex(obs.index)])
        offs.append(float(np.mean(pred - obs.values)))
    bias = float(np.median(offs)) if offs else 0.0
    info(f"cell-to-well offset {bias:.3f} m from {len(offs)} wells (D-165 measured 0.302 m independently)")
    rn.add("sentinel_offset_m", bias, note=f"median cell-minus-well head offset at {len(offs)} wells, in-range months")
    rn.add("sentinel_offset_wells", len(offs), unit="wells")
    m_wet = float(M.reindex(states["wet"]).mean())
    Hc = ez + m_wet - es - bias
    surf_c = bilinear(grids["wet"], x0 + res / 2, y1 - res / 2, res, ex, ey)
    diff = Hc - surf_c
    # a cell is tested only where a dipwell constrains the surface (SLACK_FLOW_WELL_SUPPORT_M)
    wset = heads["mean"]
    d_well = cKDTree(wset[["E", "N"]].values).query(np.column_stack([ex, ey]))[0]
    d_hwm = shapely.distance(coast, shapely.points(ex, ey))
    # terrain shadow at the lowest-sun scene of the D-178 winter fit
    man = pd.read_csv(SENTINEL_SCENE_MANIFEST, comment="#")
    man = man[man["winter"] & man["used_in_fit"] & ~man["excluded"]]
    lon_c, lat_c = Transformer.from_crs(C.SLACK_FLOW_CRS, C.SLACK_FLOW_LONLAT_CRS,
                                        always_xy=True).transform(area.centroid.x, area.centroid.y)
    el_s, az_s = sun_position(man["date"], lat_c, lon_c, C.SLACK_FLOW_S2_ACQ_UTC_H)
    lo_i = int(np.argmin(el_s))
    info(f"{len(man)} winter scenes: sun {el_s.min():.1f}-{el_s.max():.1f} deg high, azimuth "
         f"{az_s.min():.0f}-{az_s.max():.0f} deg; shadow cast at the lowest ({man['date'].iloc[lo_i]}, "
         f"{el_s[lo_i]:.1f} deg at {az_s[lo_i]:.0f} deg)")
    rn.add("shadow_sun_elevation_min_deg", float(el_s[lo_i]), unit="deg", note=f"scene {man['date'].iloc[lo_i]}")
    rn.add("shadow_sun_azimuth_deg", float(az_s[lo_i]), unit="deg")
    rn.add("shadow_sun_elevation_max_deg", float(el_s.max()), unit="deg")
    rn.add("shadow_winter_scenes", len(man), unit="scenes")
    shade = cast_shadow(Z, dres, float(az_s[lo_i]), float(el_s[lo_i]))
    gy_, gx_ = np.gradient(Z, dres)
    slope = np.degrees(np.arctan(np.hypot(gx_, gy_)))
    sh_c = cell_blocks(shade.astype(float), ever, rr0, cc0, kk, np.mean)[ever]
    sl_c = cell_blocks(slope, ever, rr0, cc0, kk, np.mean)[ever]
    _, iw = cKDTree(heads["wet"][["E", "N"]].values).query(np.column_stack([ex, ey]))
    near_wet = heads["wet"]["head"].values[iw]
    base_cls = np.where(~np.isfinite(diff), "no surface",
               np.where(d_well > C.SLACK_FLOW_WELL_SUPPORT_M, "unconstrained",
               np.where(np.abs(diff) <= C.SLACK_FLOW_SENTINEL_TOL_M, "consistent",
               np.where(diff > C.SLACK_FLOW_PERCHED_M, "above", "other"))))
    edge_slope = float(np.percentile(sl_c[base_cls == "consistent"], C.SLACK_FLOW_EDGE_SLOPE_PCTL))
    above = base_cls == "above"
    cls = base_cls.astype(object)                             # labels longer than the base ones
    cls[above & (sh_c > C.SLACK_FLOW_SHADOW_FRAC)] = "shadow"
    cls[(cls == "above") & (ez <= near_wet)] = "reached by well"
    cls[(cls == "above") & (sl_c > edge_slope)] = "floor edge"
    cls[cls == "above"] = "perched"
    rn.add("edge_slope_deg", edge_slope, unit="deg",
           note=f"{C.SLACK_FLOW_EDGE_SLOPE_PCTL}th percentile of the consistent cells' mean slope")
    chk = pd.DataFrame({"E": ex, "N": ey, "floor_m": ez, "h_wet_floor": es, "implied_head_m": Hc,
                        "surface_m": surf_c, "difference_m": diff, "d_well_m": d_well, "d_hwm_m": d_hwm,
                        "shadow_frac": sh_c, "slope_deg": sl_c, "nearest_well": heads["wet"]["well"].values[iw],
                        "nearest_well_wet_m": near_wet, "class": cls})
    chk.to_csv(OUT_49_SENTINEL_CHECK, index=False); saved(OUT_49_SENTINEL_CHECK)
    ok = np.isfinite(diff)
    for c in ("consistent", "unconstrained", "other", "shadow", "reached by well", "floor edge", "perched"):
        share = float((cls[ok] == c).mean())
        result(f"cells {c}", f"{share:.3f} of {ok.sum()}")
        rn.add(f"sentinel_share_{c.replace(' ', '_')}", share, unit="",
               note=f"share of {ok.sum()} ever-wet cells with a surface")
        rn.add(f"sentinel_cells_{c.replace(' ', '_')}", int((cls[ok] == c).sum()), unit="cells")
    above_all = ok & (diff > C.SLACK_FLOW_PERCHED_M)
    rn.add("sentinel_above_share_unsupported", float((d_well[above_all] > C.SLACK_FLOW_WELL_SUPPORT_M).mean()), unit="",
           note=f"of cells more than {C.SLACK_FLOW_PERCHED_M:g} m above the surface, the share with no well within "
                f"{C.SLACK_FLOW_WELL_SUPPORT_M} m")

    phase(7, "Coastal check")
    _coastal_check(heads, coast, chk, rn)

    phase(8, "Arrows and slack directions")
    sub = C.SLACK_FLOW_ARROW_GRID_M // res
    arrows = {}
    for st in STATES:
        u, v = grad_field(grids[st], res)
        g = np.hypot(u, v)
        rs, cs = np.meshgrid(np.arange(sub // 2, GX.shape[0], sub), np.arange(sub // 2, GX.shape[1], sub), indexing="ij")
        rs, cs = rs.ravel(), cs.ravel()
        m = node[rs, cs] & np.isfinite(g[rs, cs]) & (g[rs, cs] > C.SLACK_FLOW_MIN_GRADIENT)
        arrows[st] = pd.DataFrame({"E": GX[rs[m], cs[m]], "N": GY[rs[m], cs[m]], "u": u[rs[m], cs[m]],
                                   "v": v[rs[m], cs[m]], "grad": g[rs[m], cs[m]]})
        arrows[st]["az"] = az_of(arrows[st].u, arrows[st].v)
        rn.add(f"arrows_{st}", len(arrows[st]), unit="arrows", era=st)
        rn.add(f"median_gradient_{st}", float(arrows[st]["grad"].median()), unit="m/m", era=st)
    keep_cells = ever & np.isfinite(zf)
    keep_cells[ever] &= ~np.isin(cls, ["shadow", "floor edge", "perched"])
    lab, n = label(keep_cells, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())
    slack_rows = []
    fields = {st: grad_field(grids[st], res) for st in STATES}
    for sid in range(1, n + 1):
        if sizes[sid] < C.SLACK_FLOW_MIN_SLACK_CELLS:
            continue
        mm = lab == sid
        sx, sy = CX[mm], CY[mm]
        rec = {"slack": sid, "E": float(sx.mean()), "N": float(sy.mean()), "cells": int(mm.sum())}
        for st in STATES:
            u, v = fields[st]
            uu = bilinear(u, x0 + res / 2, y1 - res / 2, res, sx, sy)
            vv = bilinear(v, x0 + res / 2, y1 - res / 2, res, sx, sy)
            okk = np.isfinite(uu) & np.isfinite(vv)
            if not okk.any():
                rec[f"az_{st}"] = np.nan; rec[f"grad_{st}"] = np.nan; continue
            mu, mv = uu[okk].mean(), vv[okk].mean()
            rec[f"az_{st}"] = float(az_of(mu, mv)); rec[f"grad_{st}"] = float(np.hypot(uu[okk], vv[okk]).mean())
        rec["turn_wet_dry_deg"] = float(ang_diff(rec["az_wet"], rec["az_dry"]))
        rec["turn_flag"] = bool(rec["turn_wet_dry_deg"] > C.SLACK_FLOW_TURN_DEG)
        slack_rows.append(rec)
    slacks = pd.DataFrame(slack_rows)
    slacks.to_csv(OUT_49_SLACK_DIRECTIONS, index=False); saved(OUT_49_SLACK_DIRECTIONS)
    rn.add("n_slacks", len(slacks), unit="slacks", note="connected ever-wet cells passing the Sentinel check")
    rn.add("slacks_turning", int(slacks["turn_flag"].sum()), unit="slacks",
           note=f"wet-to-dry direction change > {C.SLACK_FLOW_TURN_DEG:g} deg")
    rn.add("median_turn_wet_dry_deg", float(slacks["turn_wet_dry_deg"].median()), unit="deg")

    phase(9, "Sensitivity")
    base_u, base_v = fields["mean"]
    coast_node = np.array([coast.distance(Point(e, n)) <= C.SLACK_FLOW_COASTAL_WELL_M for e, n in txy])
    Cn = np.zeros(GX.shape, bool); Cn[node] = coast_node
    sens = []
    fx = fixed["mean"]
    runs = [("head 0 m", chosen, 0.0, fx), ("head mean tide level", chosen, tide["MTL"], fx),
            ("head midpoint", chosen, mid, fx), ("head MHW", chosen, tide["MHW"], fx)]
    if runner:
        runs.append((f"runner-up drift {runner}", runner,
                     float(sel.set_index('drift').loc[runner, 'coastal_head_used_m']), fx))
    others = [p_ for p_ in kept if p_[0] != "ridge line"]
    for dz in C.SLACK_FLOW_RIDGE_DEPTH_SENS_M:
        ridge_dz = ("ridge line", ridge_xy, {st: ridge_ground - dz for st in STATES})
        runs.append((f"ridge line {dz:g} m below ground", chosen, head_sea, fixed_of(others + [ridge_dz], "mean")))
    runs.append(("no landward boundary", chosen, head_sea, None))
    base_az = az_of(base_u, base_v)
    mask_g = node & (np.hypot(base_u, base_v) > C.SLACK_FLOW_MIN_GRADIENT)
    for name, d, h, fxr in runs:
        S = Surface(heads["mean"], anchors, d, rasters, src, fxr)
        p, _, _ = S.predict(h, txy, tD[d])
        G = np.full(GX.shape, np.nan); G[node] = p
        u, v = grad_field(G, res)
        dd = ang_diff(az_of(u, v), base_az)
        row = {"run": name, "drift": d, "coastal_head_m": h,
               "median_angle_change_deg": float(np.nanmedian(dd[mask_g])),
               "median_angle_change_coastal_deg": float(np.nanmedian(dd[mask_g & Cn])) if (mask_g & Cn).any() else np.nan}
        turned = 0
        for _, sl in slacks.iterrows():
            mm = lab == sl.slack
            uu = bilinear(u, x0 + res / 2, y1 - res / 2, res, CX[mm], CY[mm])
            vv = bilinear(v, x0 + res / 2, y1 - res / 2, res, CX[mm], CY[mm])
            okk = np.isfinite(uu) & np.isfinite(vv)
            if okk.any() and ang_diff(az_of(uu[okk].mean(), vv[okk].mean()), sl["az_mean"]) > C.SLACK_FLOW_TURN_DEG:
                turned += 1
        row["share_slacks_turning"] = turned / max(len(slacks), 1)
        sens.append(row)
        result(name, f"median arrow change {row['median_angle_change_deg']:.1f} deg "
               f"(coastal {row['median_angle_change_coastal_deg']:.1f}); slacks turning {row['share_slacks_turning']:.3f}")
    pd.DataFrame(sens).to_csv(OUT_49_SENSITIVITY, index=False); saved(OUT_49_SENSITIVITY)
    for r in sens:
        key = r["run"].replace(" ", "_").replace("-", "_")
        rn.add(f"sens_{key}_angle_deg", r["median_angle_change_deg"], unit="deg")

    phase(10, "Transects")
    wells_all = heads["mean"].reset_index(drop=True)
    series, fan, merged = choose_transects(coast, area, wells_all, high_xy)
    for nm, a0, a1 in C.SLACK_FLOW_EXTRA_TRANSECTS:
        ln = LineString([a0, a1]); idx, _ = wells_on(ln, wells_all)
        series.append({"kind": f"named: {nm}", "line": ln, "az": float(az_of(a1[0] - a0[0], a1[1] - a0[1])),
                       "start": a0, "idx": idx})
    rows_t, prof = [], []
    all_t = [(f"C{i + 1}", t) for i, t in enumerate(series)] + [(f"R{t['az']}", {**t, "kind": "radial"}) for t in fan]
    for tid, t in all_t:
        ln = t["line"]; idx = t.get("idx", [])
        anchor = ln.coords[0]              # where the transect was built from: the coast (C) or the high (R)
        if ln.coords[0][0] > ln.coords[-1][0]:
            ln = LineString(ln.coords[::-1])   # every profile reads west to east (Martin, 2026-09-27)
        rows_t.append({"transect": tid, "kind": t["kind"], "E0": ln.coords[0][0], "N0": ln.coords[0][1],
                       "E1": ln.coords[-1][0], "N1": ln.coords[-1][1], "anchor_E": anchor[0], "anchor_N": anchor[1],
                       "azimuth_deg": t["az"], "length_m": ln.length,
                       "n_wells": len(idx), "wells": " ".join(wells_all.loc[idx, "well"])})
        d = np.arange(0, ln.length, C.SLACK_FLOW_TRANSECT_STEP_M)
        px = np.array([ln.interpolate(q).x for q in d]); py = np.array([ln.interpolate(q).y for q in d])
        pr = {"transect": tid, "distance_m": d, "E": px, "N": py, "ground_m": sample(src, Z, px, py)}
        for st in STATES:
            pr[f"{st}_m"] = bilinear(grids[st], x0 + res / 2, y1 - res / 2, res, px, py)
            pr[f"{st}_se_m"] = bilinear(ses[st], x0 + res / 2, y1 - res / 2, res, px, py)
        prof.append(pd.DataFrame(pr))
    tdf = pd.DataFrame(rows_t)
    tdf["spacing_to_next_m"] = np.nan
    ser = tdf[tdf.kind.str.startswith("coast")].copy()
    if len(ser) > 1:
        ptsS = [Point(r.anchor_E, r.anchor_N) for r in ser.itertuples()]
        proj = np.array([coast.project(p) for p in ptsS]); o = np.argsort(proj)
        for a_, b_ in zip(o, o[1:]):
            tdf.loc[ser.index[a_], "spacing_to_next_m"] = proj[b_] - proj[a_]
    tdf.to_csv(OUT_49_TRANSECTS, index=False); saved(OUT_49_TRANSECTS)
    pd.concat(prof).to_csv(OUT_49_TRANSECT_PROFILES, index=False); saved(OUT_49_TRANSECT_PROFILES)
    reached = set(sum([t.get("idx", []) for _, t in all_t], []))
    unreached = sorted(set(wells_all.index) - reached)
    rn.add("n_coast_normal_transects", int(tdf.kind.str.startswith("coast").sum()), unit="transects")
    rn.add("radial_merged", bool(merged), unit="")
    rn.add("wells_on_transects", len(reached), unit="wells")
    rn.add("wells_on_no_transect", len(unreached), unit="wells", note=" ".join(wells_all.loc[unreached, "well"]))
    result("transects", f"{int(tdf.kind.str.startswith('coast').sum())} coast-normal "
           f"({'one merged radial' if merged else 'no radial merged'}), {len(fan)} radial; "
           f"{len(reached)} wells covered, {len(unreached)} not")

    phase(11, "KML")
    to_ll = Transformer.from_crs(C.SLACK_FLOW_CRS, C.SLACK_FLOW_LONLAT_CRS, always_xy=True)
    for st in STATES:
        pm = []
        a = arrows[st]
        hf, hr = C.SLACK_FLOW_ARROW_HEAD_FRAC, C.SLACK_FLOW_ARROW_HEAD_RAD
        for r, ln_ in zip(a.itertuples(), arrow_length(a.grad)):
            ux, uy = r.u / r.grad, r.v / r.grad
            x_1, y_1 = r.E + ux * ln_, r.N + uy * ln_
            hx1, hy1 = x_1 - ln_ * hf * (ux * np.cos(hr) - uy * np.sin(hr)), y_1 - ln_ * hf * (uy * np.cos(hr) + ux * np.sin(hr))
            hx2, hy2 = x_1 - ln_ * hf * (ux * np.cos(-hr) - uy * np.sin(-hr)), y_1 - ln_ * hf * (uy * np.cos(-hr) + ux * np.sin(-hr))
            pts = [to_ll.transform(*q) for q in ((r.E, r.N), (x_1, y_1), (hx1, hy1), (x_1, y_1), (hx2, hy2))]
            coords = " ".join(f"{q[0]:.7f},{q[1]:.7f},0" for q in pts)
            pm.append(f"<Placemark><name>{r.az:.0f} deg</name><LineString><coordinates>{coords}</coordinates></LineString></Placemark>")
        _kml(out_49_kml(st), pm, f"Groundwater flow arrows, {st} state (Script 49)"); saved(out_49_kml(st))
    pm = []
    per = chk[chk["class"].isin(["shadow", "reached by well", "floor edge", "perched"])]
    for e_, n_, d_, k_ in zip(per.E, per.N, per.difference_m, per["class"]):
        x_, y_ = to_ll.transform(e_, n_)
        pm.append(f"<Placemark><name>{k_}: +{d_:.2f} m</name><Point><coordinates>{x_:.7f},{y_:.7f},0</coordinates></Point></Placemark>")
    _kml(OUT_49_KML_UNEXPLAINED, pm, "Sentinel wetness the aquifer does not explain (Script 49)"); saved(OUT_49_KML_UNEXPLAINED)

    if not no_fig:
        phase(12, "Figures")
        _figures(src, Z, area, coast, grids, ses, arrows, heads, slacks, chk, sel, chosen, head_sea, tdf,
                 pd.concat(prof), series, fan, wells_all, high_xy, x0, y1, res, GX, GY,
                 ridge_xy if ridge_line_kept else None, river_xy if "river" in kept_names else None,
                 rw_xy if f"ridge well {rw}" in kept_names else None,
                 lake_xy if "lake" in kept_names else None)
        _figure_coastal(chk, area)

    rn.save(OUT_49_REPORT_NUMBERS); saved(OUT_49_REPORT_NUMBERS)
    done(SCRIPT_ID)
    return 0


CLASS_STYLE = {   # Sentinel cell classes: colour, legend label (display only)
    "consistent": ("#4393c3", "consistent (within {tol:g} m of the water table)"),
    "other": ("#bdbdbd", "between the thresholds"),
    "unconstrained": ("#fdae61", "no dipwell within {sup} m (not tested)"),
    "shadow": ("#6a3d9a", "over {pm:g} m above: terrain shadow, lowest winter sun"),
    "reached by well": ("#1b9e77", "over {pm:g} m above: nearest well reaches the floor"),
    "floor edge": ("#a6761d", "over {pm:g} m above: floor edge (slope over {edge})"),
    "perched": ("#e31a1c", "over {pm:g} m above, unexplained (perched?)"),
}


def _class_label(k: str, edge: str = "") -> str:
    return CLASS_STYLE[k][1].format(tol=C.SLACK_FLOW_SENTINEL_TOL_M, sup=C.SLACK_FLOW_WELL_SUPPORT_M,
                                    pm=C.SLACK_FLOW_PERCHED_M, edge=edge)


def _partial_spearman(x, y, z):
    """Spearman correlation of x and y with z partialled out of both ranks (rho, p)."""
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    ex_ = rx - np.polyval(np.polyfit(rz, rx, 1), rz)
    ey_ = ry - np.polyval(np.polyfit(rz, ry, 1), rz)
    r = spearmanr(ex_, ey_)
    return float(r[0]), float(r[1])


def _coastal_check(heads, coast, chk, rn) -> None:
    """Does the sea set the level at the coastal wells, and where does the Sentinel excess sit?

    1. Seasonal damping: the wet-minus-dry head against distance from the HWM, per
       sector, with ground height partialled out (and the reverse). A sea-controlled
       coastal well swings less than an inland one; a well held up by the dune alone
       need not. Nothing is extrapolated to the shoreline: the nearest well is well
       inland, and the shoreline head is not identified by the network.
    2. Perched cells (a well within SLACK_FLOW_WELL_SUPPORT_M) against their nearest
       well: the floor minus that well's wet-state head.
    3. The Sentinel-minus-kriged excess by distance from the HWM, split by well support.
    """
    w = heads["wet"].set_index("well")[["E", "N", "ground", "head"]].rename(columns={"head": "wet_m"})
    w = w.join(heads["dry"].set_index("well")["head"].rename("dry_m"))
    w = w.join(heads["mean"].set_index("well")["head"].rename("mean_m")).dropna(subset=["wet_m", "dry_m"])
    w["range_m"] = w.wet_m - w.dry_m
    w["d_hwm_m"] = shapely.distance(coast, shapely.points(w.E.values, w.N.values))
    w["sector"] = np.where(w.E < C.SLACK_FLOW_COAST_SECTOR_E, "south-west", "east")
    per = chk[chk["class"] == "perched"]
    if len(per):
        _, i = cKDTree(w[["E", "N"]].values).query(per[["E", "N"]].values)
        pw = per.assign(well=w.index[i]).groupby("well").agg(perched_cells=("E", "size"), perched_floor_m=("floor_m", "median"))
        w = w.join(pw)
    else:
        w["perched_cells"] = np.nan; w["perched_floor_m"] = np.nan
    w["perched_cells"] = w["perched_cells"].fillna(0).astype(int)
    w["perched_floor_minus_wet_m"] = w.perched_floor_m - w.wet_m
    w.reset_index().to_csv(OUT_49_COASTAL_WELLS, index=False); saved(OUT_49_COASTAL_WELLS)

    rows = []
    for name, m in (("south-west", w.sector == "south-west"), ("east", w.sector == "east"), ("all", w.sector != "")):
        s_ = w[m]
        if len(s_) < C.SLACK_FLOW_COAST_MIN_WELLS:
            warn(f"coastal check: {name} has {len(s_)} wells, not tested"); continue
        r1 = spearmanr(s_.range_m, s_.d_hwm_m)
        r2 = _partial_spearman(s_.range_m.values, s_.d_hwm_m.values, s_.ground.values)
        r3 = _partial_spearman(s_.range_m.values, s_.ground.values, s_.d_hwm_m.values)
        rows.append({"sector": name, "n_wells": len(s_), "nearest_well_to_hwm_m": float(s_.d_hwm_m.min()),
                     "rho_range_distance": float(r1[0]), "p_range_distance": float(r1[1]),
                     "partial_rho_distance_given_ground": r2[0], "p_distance_given_ground": r2[1],
                     "partial_rho_ground_given_distance": r3[0], "p_ground_given_distance": r3[1]})
        result(f"damping, {name}", f"rho {r1[0]:.3f} (p {r1[1]:.3g}); given ground {r2[0]:.3f} (p {r2[1]:.3g}); "
               f"ground given distance {r3[0]:.3f} (p {r3[1]:.3g}); n {len(s_)}")
        key = name.replace("-", "_")
        rn.add(f"damping_rho_{key}", float(r1[0]), unit="", note=f"Spearman, wet-dry range vs distance from HWM, n={len(s_)}")
        rn.add(f"damping_p_{key}", float(r1[1]), unit="")
        rn.add(f"damping_partial_rho_{key}", r2[0], unit="", note="ground height partialled out")
        rn.add(f"damping_partial_p_{key}", r2[1], unit="")
        rn.add(f"ground_partial_rho_{key}", r3[0], unit="", note="distance from HWM partialled out")
        rn.add(f"ground_partial_p_{key}", r3[1], unit="")
        rn.add(f"nearest_well_to_hwm_{key}_m", float(s_.d_hwm_m.min()), unit="m")
    pd.DataFrame(rows).to_csv(OUT_49_COASTAL_TESTS, index=False); saved(OUT_49_COASTAL_TESTS)

    for name in ("south-west", "east"):
        pk = w[(w.perched_cells > 0) & (w.sector == name)]
        key = name.replace("-", "_")
        rn.add(f"perched_cells_{key}", int(pk.perched_cells.sum()), unit="cells")
        if len(pk):
            rn.add(f"perched_floor_minus_well_wet_{key}_m",
                   float(np.average(pk.perched_floor_minus_wet_m, weights=pk.perched_cells)), unit="m",
                   note="perched-cell floor minus the nearest well's wet-state head, cell-weighted mean")

    c = chk[np.isfinite(chk.difference_m)].copy()
    bins = np.arange(0, C.SLACK_FLOW_COAST_BIN_MAX_M + C.SLACK_FLOW_COAST_BIN_M, C.SLACK_FLOW_COAST_BIN_M)
    c["bin"] = pd.cut(c.d_hwm_m, bins)
    c["support"] = np.where(c.d_well_m <= C.SLACK_FLOW_WELL_SUPPORT_M, "well within support", "no well within support")
    ex_ = (c.groupby(["support", "bin"], observed=True)
           .agg(cells=("E", "size"), excess_q25_m=("difference_m", lambda v: v.quantile(0.25)),
                excess_median_m=("difference_m", "median"), excess_q75_m=("difference_m", lambda v: v.quantile(0.75)))
           .reset_index())
    ex_["d_from_m"] = [b.left for b in ex_["bin"]]; ex_["d_to_m"] = [b.right for b in ex_["bin"]]
    ex_.drop(columns="bin").to_csv(OUT_49_COASTAL_EXCESS, index=False); saved(OUT_49_COASTAL_EXCESS)


def _figure_coastal(chk, area) -> None:
    import matplotlib                                          # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                            # noqa: PLC0415
    from matplotlib.lines import Line2D                        # noqa: PLC0415
    from utils.render_utils import render_figure, apply_house_style  # noqa: PLC0415
    from utils.map_utils import add_en_axes                    # noqa: PLC0415
    apply_house_style()
    FS_S, FS_T = C.SLACK_FLOW_FONT_PT
    FS = FS_S + 1
    w = pd.read_csv(OUT_49_COASTAL_WELLS); ex_ = pd.read_csv(OUT_49_COASTAL_EXCESS)
    fig = plt.figure(figsize=(11, 10), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.35])
    ax = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])]
    for nm, mk in (("south-west", "o"), ("east", "s")):
        s_ = w[w.sector == nm]
        sc = ax[0].scatter(s_.d_hwm_m, s_.range_m, c=s_.ground, marker=mk, cmap="viridis",
                           vmin=float(w.ground.min()), vmax=float(w.ground.max()),
                           edgecolor="k", lw=0.3, s=28, label=f"{nm} wells")
    cb = fig.colorbar(sc, ax=ax[0], shrink=0.8); cb.set_label("ground (m OD)", fontsize=FS)
    cb.ax.tick_params(labelsize=FS_S)
    ax[0].set_xlabel("distance from the high-water mark (m)", fontsize=FS)
    ax[0].set_ylabel("wet-state minus dry-state head (m)", fontsize=FS)
    ax[0].legend(fontsize=FS_S, loc="lower right"); ax[0].tick_params(labelsize=FS_S)
    ax[0].set_title("(a) seasonal range against distance from the sea", fontsize=FS_T)
    for sup, col in (("well within support", "#2166ac"), ("no well within support", "#d6604d")):
        e = ex_[ex_.support == sup]
        mid = (e.d_from_m + e.d_to_m) / 2
        ax[1].plot(mid, e.excess_median_m, color=col, lw=1.5, marker="o", ms=3,
                   label=f"{'a' if sup.startswith('well') else 'no'} dipwell within {C.SLACK_FLOW_WELL_SUPPORT_M} m")
        ax[1].fill_between(mid, e.excess_q25_m, e.excess_q75_m, color=col, alpha=0.2, lw=0)
    ax[1].axhline(C.SLACK_FLOW_PERCHED_M, color="k", ls="--", lw=0.8)
    ax[1].axhline(0, color="k", lw=0.5)
    ax[1].set_xlabel("distance from the high-water mark (m)", fontsize=FS)
    ax[1].set_ylabel("Sentinel-implied minus kriged\nwet-state head (m); median and IQR", fontsize=FS)
    ax[1].legend(handles=ax[1].get_legend_handles_labels()[0] + [Line2D([0], [0], color="k", ls="--", lw=0.8)],
                 labels=ax[1].get_legend_handles_labels()[1] + [f"perched threshold ({C.SLACK_FLOW_PERCHED_M:g} m)"],
                 fontsize=FS_S, loc="upper right")
    ax[1].tick_params(labelsize=FS_S)
    ax[1].set_title("(b) Sentinel excess over the kriged surface", fontsize=FS_T)
    c = chk[np.isfinite(chk.difference_m)]
    for k, (col, _) in CLASS_STYLE.items():
        s_ = c[c["class"] == k]
        ax[2].scatter(s_.E, s_.N, s=1.2, c=col, lw=0, zorder=2 if k in ("consistent", "other", "unconstrained") else 3)
    ax[2].scatter(w.E, w.N, marker="^", s=12, c="lime", edgecolor="k", lw=0.3, zorder=4)
    ax[2].plot(*area.exterior.xy, color="m", lw=0.8)
    edge = f"{float(c.loc[c['class'] == 'consistent', 'slope_deg'].quantile(C.SLACK_FLOW_EDGE_SLOPE_PCTL / 100)):.1f} deg"
    ax[2].legend(handles=[Line2D([0], [0], marker="o", color="w", markerfacecolor=col, markersize=6,
                                 label=_class_label(k, edge)) for k, (col, _) in CLASS_STYLE.items()]
                 + [Line2D([0], [0], marker="^", color="w", markerfacecolor="lime", markeredgecolor="k",
                           markersize=7, label="dipwell")], fontsize=FS_S, loc="center left",
                 bbox_to_anchor=(1.02, 0.5), ncol=1, frameon=False)
    with rasterio.open(DATA_DEM) as dem_:
        ax[2].set_xlim(max(area.bounds[0] - C.SLACK_FLOW_MAP_PAD_M, dem_.bounds.left),
                       area.bounds[2] + C.SLACK_FLOW_MAP_PAD_M)
    ax[2].set_ylim(area.bounds[1] - C.SLACK_FLOW_MAP_PAD_M, area.bounds[3] + C.SLACK_FLOW_MAP_PAD_M)
    for axis in (ax[2].xaxis, ax[2].yaxis):
        axis.set_major_locator(matplotlib.ticker.MultipleLocator(C.SLACK_FLOW_MAP_TICK_M))
    add_en_axes(ax[2], apply_extent=False, labelsize=FS_S, label_fontsize=FS)
    ax[2].set_title("(c) Sentinel wet cells by class, wet state", fontsize=FS_T)
    fig.suptitle("Coastal check: the sea and the coastal wells, and where the Sentinel excess lies", fontsize=FS_T + 1)
    render_figure(fig, OUT_49_FIG_COASTAL, bbox_inches="tight"); plt.close(fig)


def _figures(src, Z, area, coast, grids, ses, arrows, heads, slacks, chk, sel, chosen, head_sea, tdf,
             prof, series, fan, wells, high_xy, x0, y1, res, GX, GY, ridge_xy=None, river_xy=None,
             ridge_well_xy=None, lake_xy=None):
    import matplotlib                                          # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                            # noqa: PLC0415
    import matplotlib.ticker                                   # noqa: PLC0415
    from matplotlib.colors import LightSource, LogNorm        # noqa: PLC0415
    from matplotlib.lines import Line2D                       # noqa: PLC0415
    from matplotlib.patches import Patch                      # noqa: PLC0415
    from utils.render_utils import render_figure, apply_house_style  # noqa: PLC0415
    from utils.map_utils import add_en_axes                    # noqa: PLC0415
    from utils.kml_io import read_kml                         # noqa: PLC0415
    apply_house_style()
    FS_S, FS_T = C.SLACK_FLOW_FONT_PT                           # small and panel-title font sizes (pt)
    Zs = rasterio.open(DATA_DEM) if src is None else src
    ext = [Zs.bounds.left, Zs.bounds.right, Zs.bounds.bottom, Zs.bounds.top]
    dres = float(Zs.res[0])
    l_az, l_alt, l_ve = C.SLACK_FLOW_DEM_LIGHT
    hs = LightSource(l_az, l_alt).hillshade(np.where(Z > 0, Z, 0), vert_exag=l_ve, dx=dres, dy=dres)
    gext = [x0, x0 + GX.shape[1] * res, y1 - GX.shape[0] * res, y1]
    try:
        streams = read_kml(DATA_KML_STREAMS, quiet=True)
    except Exception as e:  # noqa: BLE001
        warn(f"streams.kml not drawn ({e})"); streams = None
    # maps start at the DEM's west edge: the hand-drawn west end beyond it (D-203) has no
    # ground data and no estimate, so it is left off the page
    pad = C.SLACK_FLOW_MAP_PAD_M
    xlim = (max(area.bounds[0] - pad, Zs.bounds.left), area.bounds[2] + pad)
    ylim = (area.bounds[1] - pad, area.bounds[3] + pad)
    norm = LogNorm(vmin=C.SLACK_FLOW_MIN_GRADIENT, vmax=C.SLACK_FLOW_GRADIENT_VMAX)
    C_WET, C_MEAN, C_DRY = "#2166ac", "#1a1a1a", "#d6604d"
    C_COAST_T, C_RADIAL_T = "#b2182b", "#3f007d"             # transect lines: red, dark purple (clear of the pale DEM)

    def axes_en(ax):
        """The project's E/N map axes (map_utils.add_en_axes) at this figure's own extent."""
        ax.set_xlim(*xlim); ax.set_ylim(*ylim)
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_locator(matplotlib.ticker.MultipleLocator(C.SLACK_FLOW_MAP_TICK_M))
        add_en_axes(ax, apply_extent=False, labelsize=FS_S, label_fontsize=FS_S)

    def base(ax, st, contours=True):
        ax.imshow(hs, extent=ext, cmap="gray", vmin=0, vmax=1.2)
        if streams is not None:
            streams.plot(ax=ax, color="#6a51a3", lw=0.3, alpha=0.3)
        if contours:
            top = float(np.nanmax(grids[st]))
            cs = ax.contour(grids[st], levels=np.arange(0, top + 1, C.SLACK_FLOW_CONTOUR_M), extent=[gext[0], gext[1], gext[2], gext[3]],
                            origin="upper", colors="#8c510a", linewidths=0.5, alpha=0.85)
            lab = ax.clabel(cs, levels=np.arange(0, top + 1, C.SLACK_FLOW_CONTOUR_LABEL_M), fmt="%d m", fontsize=FS_S - 1, inline_spacing=2)
            placed = []
            for t in lab:   # thin crowded labels (the steep ground by the ridge)
                xy_ = np.array(t.get_position())
                if any(np.hypot(*(xy_ - q)) < C.SLACK_FLOW_LABEL_MIN_SEP_M for q in placed):
                    t.remove(); continue
                placed.append(xy_)
                t.set_bbox(dict(facecolor="white", edgecolor="none", alpha=0.6, pad=0.3))
        ax.plot(*area.exterior.xy, color="m", lw=1.0)
        ax.plot(*coast.xy, color="teal", lw=0.9)
        axes_en(ax)

    wtree = cKDTree(wells[["E", "N"]].values)
    support = unary_union([Point(e, n).buffer(C.SLACK_FLOW_FLOW_SUPPORT_M) for e, n in zip(wells.E, wells.N)])
    support = support.intersection(area)

    def quiv(ax, a):
        scale = arrow_length(a.grad)
        U, V = a.u / a.grad * scale, a.v / a.grad * scale
        near = wtree.query(a[["E", "N"]].values)[0] <= C.SLACK_FLOW_FLOW_SUPPORT_M
        kw = dict(cmap="viridis_r", norm=norm, angles="xy", scale_units="xy", scale=1, width=0.0032,
                  headwidth=3.0, headlength=3.2, headaxislength=2.9, zorder=5)
        if (~near).any():   # beyond well support: the boundary, not data, sets these
            ax.quiver(a.E[~near], a.N[~near], U[~near], V[~near], a.grad[~near], alpha=0.3, **kw)
        return ax.quiver(a.E[near], a.N[near], U[near], V[near], a.grad[near], **kw)

    def boundary_marks(ax):
        for g in getattr(support, "geoms", [support]):
            ax.plot(*g.exterior.xy, color="k", ls=":", lw=0.9, zorder=6)
        if ridge_xy is not None and len(ridge_xy):
            ax.scatter(ridge_xy[:, 0], ridge_xy[:, 1], s=6, c="#8c2d04", marker="s", lw=0, zorder=6)
        if river_xy is not None and len(river_xy):
            ax.scatter(river_xy[:, 0], river_xy[:, 1], s=6, c="#08519c", marker="s", lw=0, zorder=6)
        if lake_xy is not None and len(lake_xy):
            ax.scatter(lake_xy[:, 0], lake_xy[:, 1], s=6, c="#41b6c4", marker="s", lw=0, zorder=6)
        if ridge_well_xy is not None and len(ridge_well_xy):
            ax.scatter(ridge_well_xy[:, 0], ridge_well_xy[:, 1], s=40, c="#8c2d04", marker="^", edgecolor="k",
                       lw=0.5, zorder=7)

    map_legend = [Line2D([0], [0], color="#8c510a", lw=1, label=f"water table, {C.SLACK_FLOW_CONTOUR_M:g} m contours (m OD)"),
                  Line2D([0], [0], marker=r"$\rightarrow$", color="#35608d", lw=0, markersize=12,
                         label="groundwater flow (-grad h); colour and length = gradient"),
                  Line2D([0], [0], marker="^", color="w", markerfacecolor="lime", markeredgecolor="k", markersize=7,
                         label="dipwell"),
                  Line2D([0], [0], color="m", lw=1, label="study area (D-203)"),
                  Line2D([0], [0], color="teal", lw=1, label="high-water mark"),
                  Line2D([0], [0], color="#6a51a3", lw=1, alpha=0.5, label="surface routing (streams.kml), context only"),
                  Line2D([0], [0], color="k", ls=":", lw=0.9,
                         label=f"limit of well support ({C.SLACK_FLOW_FLOW_SUPPORT_M} m); fainter arrows beyond it"),
                  Line2D([0], [0], marker="^", color="w", markerfacecolor="#8c2d04", markeredgecolor="k", markersize=7,
                         label=f"ridge well {C.SLACK_FLOW_RIDGE_WELL.upper()} (bedrock ridge, 2006-2010)"),
                  Line2D([0], [0], marker="s", color="w", markerfacecolor="#08519c", markersize=5,
                         label="river boundary: channel elevation"),
                  Line2D([0], [0], marker="s", color="w", markerfacecolor="#41b6c4", markersize=5,
                         label="Llyn Rhos-Ddu: gauged lake level")]

    # ── Figure 1: flow in three states, and the wet-to-dry change ──────────────
    fig, axs = plt.subplots(2, 2, figsize=(11.5, 11.5), constrained_layout=True)
    for ax, st in zip(axs.flat[:3], STATES):
        base(ax, st)
        q = quiv(ax, arrows[st])
        boundary_marks(ax)
        ax.scatter(heads[st].E, heads[st].N, marker="^", s=12, c="lime", edgecolor="k", lw=0.3, zorder=6)
        ax.set_title(f"({'abc'[STATES.index(st)]}) {st} state", fontsize=FS_T)
    ax = axs.flat[3]
    base(ax, "mean", contours=False)
    aw, ad = arrows["wet"].set_index(["E", "N"]), arrows["dry"].set_index(["E", "N"])
    j = aw.join(ad, lsuffix="_w", rsuffix="_d", how="inner")
    turn = ang_diff(j["az_w"], j["az_d"])
    ratio = (j["grad_d"] / j["grad_w"]).clip(0, 2)
    sc = ax.scatter([i[0] for i in j.index], [i[1] for i in j.index], c=turn, s=8 + 22 * ratio,
                    cmap="magma_r", vmin=0, vmax=2 * C.SLACK_FLOW_TURN_DEG, zorder=5, edgecolor="none")
    ax.set_title("(d) change in flow direction, wet to dry", fontsize=FS_T)
    cb = fig.colorbar(sc, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label("direction change (degrees)", fontsize=FS_S); cb.ax.tick_params(labelsize=FS_S)
    size_leg = [Line2D([0], [0], marker="o", color="w", markerfacecolor="0.4", markersize=np.sqrt(8 + 22 * r),
                       label=f"dry gradient = {r:g} x wet") for r in (0.5, 1, 1.5)]
    ax.legend(handles=size_leg, loc="lower right", fontsize=FS_S - 1, framealpha=0.9, title="dot size",
              title_fontsize=FS_S - 1)
    cb = fig.colorbar(q, ax=axs[0, 1], shrink=0.8, pad=0.02)
    cb.set_label("head gradient (m per m)", fontsize=FS_S); cb.ax.tick_params(labelsize=FS_S)
    fig.legend(handles=map_legend, loc="lower center", ncol=3, fontsize=FS_S, frameon=False,
               bbox_to_anchor=(0.5, -0.07))
    fig.suptitle(f"Groundwater flow at Newborough Warren: water table by {DRIFT_NAME[chosen]}, "
                 f"coastal head {head_sea:.2f} m OD", fontsize=FS_T + 1)
    render_figure(fig, OUT_49_FIG_FLOW, full_page=True, bbox_inches="tight"); plt.close(fig)

    # ── Figure 2: transects ─────────────────────────────────────────────────────
    tlist = list(tdf.itertuples())
    ncol = 3; nrow = int(np.ceil(len(tlist) / ncol))
    fig = plt.figure(figsize=(11.5, 5.2 + 3.1 * nrow), constrained_layout=True)
    gs = fig.add_gridspec(nrow + 1, ncol, height_ratios=[2.2] + [1] * nrow)
    axm = fig.add_subplot(gs[0, :2])
    # colour-shaded DEM here only: the location map carries no coloured data layer, so
    # ground height can take the colour; the flow maps keep the grey hillshade so their
    # gradient and direction colour scales are the only colour on the page
    zmax = float(np.nanpercentile(Z[Z > 0], C.SLACK_FLOW_DEM_CLIP_PCTL))
    # gamma < 1 spreads the 2-15 m dune range, which is most of the site, instead of
    # spending the colour scale on the ridge
    # low to high: blue, green, yellow, brown, white (hypsometric), mixed with white so the
    # transect lines carry the colour and the ground stays in the background
    dem_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "dem49", C.SLACK_FLOW_DEM_COLOURS, N=256)
    pale = C.SLACK_FLOW_DEM_PALE
    dem_cmap = matplotlib.colors.ListedColormap(
        (1 - pale) * dem_cmap(np.linspace(0.0, 1.0, 256))[:, :3] + pale)
    dem_norm = matplotlib.colors.PowerNorm(gamma=C.SLACK_FLOW_DEM_GAMMA, vmin=0, vmax=zmax)
    rgb = LightSource(l_az, l_alt).shade(np.clip(np.where(Z > 0, Z, 0), 0, zmax), cmap=dem_cmap, norm=dem_norm,
                                         blend_mode="soft", vert_exag=l_ve, dx=dres, dy=dres)
    rgb[Z <= 0, :3] = matplotlib.colors.to_rgb("#d9d9d9")    # sea and DEM no-data: grey, not low ground
    axm.imshow(rgb, extent=ext)
    sm = matplotlib.cm.ScalarMappable(norm=dem_norm, cmap=dem_cmap)
    cb = fig.colorbar(sm, ax=axm, shrink=0.6, pad=0.01)
    cb.set_ticks([t for t in C.SLACK_FLOW_DEM_TICKS_M if t <= zmax])
    cb.set_label("ground (m OD, LiDAR DTM)", fontsize=FS_S); cb.ax.tick_params(labelsize=FS_S - 1)
    axm.plot(*area.exterior.xy, color="m", lw=1); axm.plot(*coast.xy, color="teal", lw=0.9)
    axm.scatter(wells.E, wells.N, marker="^", s=14, c="lime", edgecolor="k", lw=0.4, zorder=5)
    axm.scatter(*high_xy, marker="*", s=220, c="yellow", edgecolor="k", zorder=6)
    d_hi = np.hypot(wells.E - high_xy[0], wells.N - high_xy[1])
    hi_well = wells.well.iloc[int(np.argmin(d_hi.values))].upper() if d_hi.min() <= res else None
    if hi_well:
        axm.annotate(hi_well, high_xy, xytext=(-10, 8), textcoords="offset points", ha="right",
                     fontsize=FS_S, weight="bold", bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=0.4))
    for r in tlist:
        col = C_COAST_T if r.kind.startswith("coast") else C_RADIAL_T
        axm.plot([r.E0, r.E1], [r.N0, r.N1], color=col, lw=1.8)
        # label the coast end of a coast-normal transect and the far end of a radial
        far = (r.E1, r.N1) if np.hypot(r.E0 - r.anchor_E, r.N0 - r.anchor_N) < 1 else (r.E0, r.N0)
        lx, ly = far if (r.kind == "radial" or "merged" in r.kind) else (r.anchor_E, r.anchor_N)
        axm.annotate(r.transect, (lx, ly), fontsize=FS_S, weight="bold", color=col,
                     xytext=(3, -3 if r.kind == "radial" else -10), textcoords="offset points",
                     bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=0.4))
    axes_en(axm)
    axm.set_title("(a) transect locations", fontsize=FS_T)
    axl = fig.add_subplot(gs[0, 2]); axl.axis("off")
    leg = [Line2D([0], [0], color=C_COAST_T, lw=2, label="coast-normal transect (C),\nspaced where wells support it"),
           Line2D([0], [0], color=C_RADIAL_T, lw=2, label="radial transect (R) from the\nwet-state water-table high"),
           Line2D([0], [0], marker="*", color="w", markerfacecolor="yellow", markeredgecolor="k", markersize=13,
                  label="wet-state water-table high" + (f" (at {hi_well})" if hi_well else "")),
           Line2D([0], [0], marker="^", color="w", markerfacecolor="lime", markeredgecolor="k", markersize=7,
                  label="dipwell (map)"),
           Patch(facecolor="#e6d8b8", label="ground (LiDAR DTM, profiles)"),
           Line2D([0], [0], color=C_WET, lw=1.5, label="water table, wet state"),
           Line2D([0], [0], color=C_MEAN, lw=1.5, label="water table, mean state"),
           Line2D([0], [0], color=C_DRY, lw=1.5, label="water table, dry state"),
           Patch(facecolor="0.6", alpha=0.3, label="± kriging standard error"),
           Line2D([0], [0], marker="^", color="w", markerfacecolor=C_WET, markeredgecolor="k", markersize=8,
                  label="dipwell head, wet (labelled)"),
           Line2D([0], [0], marker="^", color="w", markerfacecolor=C_DRY, markeredgecolor="k", markersize=8,
                  label="dipwell head, dry"),
           Line2D([0], [0], marker="o", color="w", markerfacecolor=CLASS_STYLE["consistent"][0], markersize=5,
                  label="Sentinel wet cell, consistent"),
           Line2D([0], [0], marker="x", color=CLASS_STYLE["shadow"][0], lw=0, markersize=7,
                  label="Sentinel wet cell, terrain shadow"),
           Line2D([0], [0], marker="x", color=CLASS_STYLE["floor edge"][0], lw=0, markersize=7,
                  label="Sentinel wet cell, floor edge"),
           Line2D([0], [0], marker="x", color=CLASS_STYLE["reached by well"][0], lw=0, markersize=7,
                  label="Sentinel wet cell, reached by the nearest well"),
           Line2D([0], [0], marker="x", color=CLASS_STYLE["perched"][0], lw=0, markersize=7,
                  label="Sentinel wet cell, unexplained"),
           Line2D([0], [0], color="teal", ls="--", lw=1, label=f"coastal head ({head_sea:.2f} m OD)")]
    axl.legend(handles=leg, loc="center left", fontsize=FS_S, frameon=False)
    chk_xy = chk[np.isfinite(chk["difference_m"])]
    ymax = min(C.SLACK_FLOW_PROFILE_YMAX_M, float(np.nanmax(prof["ground_m"])) + 1)
    for k_, r in enumerate(tlist):
        ax = fig.add_subplot(gs[1 + k_ // ncol, k_ % ncol])
        p = prof[prof.transect == r.transect]
        ax.fill_between(p.distance_m, p.ground_m, -3, color="#e6d8b8", lw=0)
        for st, col in (("wet", C_WET), ("mean", C_MEAN), ("dry", C_DRY)):
            ax.plot(p.distance_m, p[f"{st}_m"], color=col, lw=1.2)
            ax.fill_between(p.distance_m, p[f"{st}_m"] - p[f"{st}_se_m"], p[f"{st}_m"] + p[f"{st}_se_m"],
                            color=col, alpha=0.1, lw=0)
        ln = LineString([(r.E0, r.N0), (r.E1, r.N1)])
        labelled = []
        for st, col in (("wet", C_WET), ("dry", C_DRY)):
            for w_ in heads[st].itertuples():
                pt = Point(w_.E, w_.N)
                if ln.distance(pt) <= C.SLACK_FLOW_TRANSECT_BAND_M:
                    a_ = ln.project(pt)
                    ax.scatter(a_, w_.head, marker="^", s=26, c=col, edgecolor="k", lw=0.4, zorder=6)
                    if st == "wet" and all(abs(a_ - b) > 0.06 * ln.length for b in labelled):
                        edge = "left" if a_ < 0.08 * ln.length else ("right" if a_ > 0.92 * ln.length else "center")
                        dx = {"left": 2, "right": -2, "center": 0}[edge]
                        ax.annotate(w_.well.upper(), (a_, w_.head), xytext=(dx, 6), textcoords="offset points",
                                    fontsize=FS_S - 1, ha=edge,
                                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.6, pad=0.2))
                        labelled.append(a_)
        near = chk_xy[shapely.distance(ln, shapely.points(chk_xy.E.values, chk_xy.N.values))
                      <= C.SLACK_FLOW_TRANSECT_CELL_BAND_M]
        if len(near):
            al = shapely.line_locate_point(ln, shapely.points(near.E.values, near.N.values))
            for k in ("consistent", "shadow", "reached by well", "floor edge", "perched"):
                m_ = (near["class"] == k).values
                if m_.any():
                    ax.scatter(al[m_], near.implied_head_m.values[m_], s=4 if k == "consistent" else 10,
                               marker="o" if k == "consistent" else "x", c=CLASS_STYLE[k][0],
                               alpha=0.5 if k == "consistent" else 1, lw=0 if k == "consistent" else 0.8)
        ax.axhline(head_sea, color="teal", lw=0.8, ls="--")
        pad = 0.05 * ln.length                                 # keeps end-of-line wells and labels off the axes
        ax.set_ylim(-1, ymax); ax.set_xlim(-pad, ln.length + pad)
        merged_note = " (merged radial)" if "merged" in r.kind else ""
        nw = int(r.n_wells)
        ax.set_title(f"({'bcdefghijklmnop'[k_]}) {r.transect}{merged_note}: {r.azimuth_deg:.0f}°, "
                     f"{nw} well{'s' if nw != 1 else ''}",
                     fontsize=FS_S + 1)
        ax.set_xlabel("distance from west end (m)", fontsize=FS_S - 1); ax.set_ylabel("m OD", fontsize=FS_S - 1)
        ax.tick_params(labelsize=FS_S - 1)
    fig.suptitle("Water-table transects: coast-normal series and radial fan", fontsize=FS_T + 1)
    render_figure(fig, OUT_49_FIG_TRANSECTS, full_page=True, bbox_inches="tight"); plt.close(fig)

    # ── Figure 3: drift selection ───────────────────────────────────────────────
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.3), constrained_layout=True)
    x = np.arange(len(sel)); names = [DRIFT_NAME[d].replace(" (", "\n(").replace("smoothed ", "smoothed\n")
                                      .replace("envelope ", "envelope\n") for d in sel.drift]
    for k_, (st, col) in enumerate((("wet", C_WET), ("mean", C_MEAN), ("dry", C_DRY))):
        axs[0].bar(x + (k_ - 1) * 0.26, sel[f"loo_median_abs_{st}_m"], 0.26, color=col, label=f"{st} state")
    axs[0].set_xticks(x); axs[0].set_xticklabels(names, fontsize=FS_S - 1)
    axs[0].set_ylabel("leave-one-well-out\nmedian |error| (m)", fontsize=FS_S)
    axs[0].legend(fontsize=FS_S - 1); axs[0].set_title("(a) accuracy at the wells", fontsize=FS_T)
    axs[1].bar(x, 100 * sel["above_ground_share"],
               color=["#1a9850" if p_ else "#d73027" for p_ in sel.passes_physical])
    axs[1].axhline(100 * C.SLACK_FLOW_ABOVE_GROUND_MAX, color="k", ls="--", lw=0.8)
    axs[1].set_xticks(x); axs[1].set_xticklabels(names, fontsize=FS_S - 1)
    axs[1].set_ylabel("observed ground with water\ntable above it (%)", fontsize=FS_S)
    axs[1].legend(handles=[Patch(color="#1a9850", label="passes"), Patch(color="#d73027", label="fails"),
                           Line2D([0], [0], color="k", ls="--", label="limit")], fontsize=FS_S - 1)
    axs[1].set_title("(b) physical test", fontsize=FS_T)
    for a in axs:
        a.tick_params(axis="y", labelsize=FS_S)
    fig.suptitle(f"Drift selection: {DRIFT_NAME[chosen]} chosen", fontsize=FS_T + 1)
    render_figure(fig, OUT_49_FIG_DRIFT); plt.close(fig)

    # ── Figure 4: unexplained wetness ───────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True)
    base(ax, "wet")
    c = chk[np.isfinite(chk.difference_m)]
    for k, (col, _) in CLASS_STYLE.items():
        if k == "other":
            continue
        s_ = c[c["class"] == k]
        ax.scatter(s_.E, s_.N, s=1.5 if k in ("consistent", "unconstrained") else 4, c=col, lw=0,
                   zorder=4 if k in ("consistent", "unconstrained") else 5)
    ax.scatter(wells.E, wells.N, marker="^", s=14, c="lime", edgecolor="k", lw=0.4, zorder=6)
    edge = f"{float(c.loc[c['class'] == 'consistent', 'slope_deg'].quantile(C.SLACK_FLOW_EDGE_SLOPE_PCTL / 100)):.1f} deg"
    leg = [Line2D([0], [0], marker="o", color="w", markerfacecolor=col, markersize=6, label=_class_label(k, edge))
           for k, (col, _) in CLASS_STYLE.items() if k != "other"] \
        + [h for h in map_legend if not any(k in h.get_label() for k in ("flow", "support", "boundary:"))]
    # inside the frame, at the top left, where the ground lies outside the study area and carries no data
    ax.legend(handles=leg, loc="upper left", fontsize=FS_S - 1, framealpha=0.9, borderpad=0.4, labelspacing=0.3)
    ax.set_title("Sentinel-2 wetness the aquifer does not explain (wet state)", fontsize=FS_T)
    render_figure(fig, OUT_49_FIG_WETNESS); plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--no-fig", action="store_true")
    raise SystemExit(main(ap.parse_args().no_fig))
