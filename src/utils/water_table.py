"""
utils/water_table.py — the water table, one implementation (D-205)
==================================================================

The water table (head, m OD) is built one way wherever the pipeline draws or
samples it: ordinary kriging from the dipwells (drift chosen by test), sea anchors
on the HWM at a fitted coastal head, and landward boundary parts each kept only if
they do not worsen the wells near them (the river at channel elevation, Llyn
Rhos-Ddu at its gauged level, the ridge well CEH12 at its measured depth).
Script 01b makes the choices and writes the surfaces; Script 19 uses this module
to build the viewer's kriging weights from 01b's recorded choices. Moved out of
Script 49 unchanged (spec NRG_spec_water_table_kriged_everywhere, rev 2).

Pieces
  geojson_geom, tidal_levels, load_dem, drift_rasters, sample, bilinear
  network_states, well_heads            the three states and the well heads in each
  Surface, fit_coastal_head             kriging with sea and fixed anchors; the coastal head
  sea_anchors                           points on the HWM near the study area
  ridge_depths, boundary_arcs, lake_boundary, channel_level   the landward boundary parts
  kriging_weights                       kriging weights at targets (linear operator)
  recorded_system                       01b's mean-state system from its committed decisions (Script 19)
  depth_surface                         a depth map: the kriged level minus the DEM (D-206)

__version__ : 1.2.0
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) - 2026-09-28. depth_surface(): a depth map as the
#   kriged level (01b's recorded system, anchor heads over the map's months) minus the DEM
#   averaged onto the grid (D-206, spec NRG_spec_depth_maps_level_minus_dem). Additive.
# 1.1.0  # Hollingham (2026) - 2026-09-27. kriging_weights() takes an optional external
#   drift (the weights of ked()), and recorded_system() rebuilds 01b's mean-state system from its
#   committed decisions, with season-dependent lake and ridge-well heads, for the Script 19 viewer.
# 1.0.0 (2026-09-27): New: moved out of Script 49 (now 01b)
#   unchanged, plus sea_anchors() and kriging_weights() (D-205 extended).

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy.linalg import lu_factor, lu_solve
from scipy.ndimage import map_coordinates, minimum_filter, uniform_filter
from scipy.optimize import minimize_scalar
from scipy.spatial.distance import cdist
from shapely.geometry import LineString, Point, shape

from utils import config as C
from utils.console_utils import warn
from utils.kriging import ked, ols_residuals, empirical_variogram, fit_spherical, spherical
from utils.paths import (DATA_DEM, DATA_TIDAL_LEVELS, INT_WELLS_ALL, INT_WELLS_CLEAN,
                         INT_WELL_ELEVATIONS, DATA_KML_FEATURES, DATA_STUDY_AREA_GEOJSON,
                         DATA_COASTLINE_HWM, OUT_01B_REPORT_NUMBERS, OUT_01B_DRIFT_SELECTION,
                         OUT_01B_LOO, OUT_01B_BOUNDARY_ANCHORS)

STATES = ("wet", "mean", "dry")


def _wells_monthly():
    """The D-178 network median, from tools/sentinel_wet_floor (imported, not rewritten)."""
    tools = Path(__file__).resolve().parents[2] / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from sentinel_wet_floor import _wells_monthly as wm   # noqa: PLC0415
    return wm()


def geojson_geom(path):
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


def bilinear(grid_vals, x0, y0, res, x, y):
    """Bilinear sample of a north-up grid whose node (0,0) is at (x0, y0)."""
    cols = (np.asarray(x) - x0) / res
    rows = (y0 - np.asarray(y)) / res
    return map_coordinates(grid_vals, [rows, cols], order=1, mode="constant", cval=np.nan)


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




def sea_anchors(area, coast, src, rasters) -> np.ndarray:
    """Points every SLACK_FLOW_SEA_SPACING_M along the HWM, within SLACK_FLOW_SEA_BUFFER_M
    of the study area and on the DEM."""
    buf = area.buffer(C.SLACK_FLOW_SEA_BUFFER_M)
    a = np.array([coast.interpolate(t).coords[0] for t in np.arange(0, coast.length, C.SLACK_FLOW_SEA_SPACING_M)])
    a = a[[buf.contains(Point(p)) for p in a]]
    return a[np.isfinite(sample(src, rasters["e"], a[:, 0], a[:, 1]))]


def kriging_weights(data_xy: np.ndarray, targets: np.ndarray, vgm: dict, D: np.ndarray | None = None,
                    tD: np.ndarray | None = None, chunk: int = 5000) -> np.ndarray:
    """Kriging weights: row t gives the weight of each data point in the prediction at
    target t (rows sum to 1). Ordinary kriging when D is None; with an external drift D
    (n x k at the data, tD m x k at the targets) the weights are those of ked(), which
    are still independent of the data values. So prediction = W @ z for any values z at
    the same points, which is what lets the viewer add scenario changes at the wells
    and stay exact."""
    n = len(data_xy)
    F = np.ones((n, 1)) if D is None else np.column_stack([np.ones(n), D])
    p = F.shape[1]
    A = np.zeros((n + p, n + p))
    A[:n, :n] = spherical(cdist(data_xy, data_xy), vgm)
    A[:n, n:] = F; A[n:, :n] = F.T
    lu = lu_factor(A)
    W = np.empty((len(targets), n))
    for s in range(0, len(targets), chunk):
        t = targets[s:s + chunk]
        tF = np.ones((len(t), 1)) if tD is None else np.column_stack([np.ones(len(t)), tD[s:s + chunk]])
        b = np.vstack([spherical(cdist(data_xy, t), vgm), tF.T])
        W[s:s + chunk] = lu_solve(lu, b)[:n].T
    return W


def recorded_system(seasons: dict) -> dict:
    """Script 01b's mean-state kriging system, rebuilt from its committed decisions
    rather than re-decided: the drift it selected, its mean-state variogram for that
    drift, the coastal head it fitted, its well set, and the landward boundary parts it
    kept. The anchor heads that vary with the season (the lake at its gauged level, the
    ridge well at its measured depth) are evaluated over each season's months in
    `seasons` ({name: DatetimeIndex}); the sea and the river are fixed.

    Returns {wells: DataFrame (well, E, N, head_<season>), anchor_xy, anchor_head:
    {season: array}, anchor_kind, vgm, drift, drift_at: callable(xy) -> n x k or None}."""
    rn = pd.read_csv(OUT_01B_REPORT_NUMBERS)
    val = lambda k: rn.loc[rn["Parameter"] == k, "Value"].iloc[0]  # noqa: E731
    drift = str(val("drift_selected"))
    head_sea = float(val("coastal_head_m"))
    kept = lambda part: float(val(f"boundary_kept_{part}")) == 1.0  # noqa: E731
    sel = pd.read_csv(OUT_01B_DRIFT_SELECTION).set_index("drift").loc[drift]
    vgm = {"nugget": float(sel["vgm_nugget"]), "psill": float(sel["vgm_psill"]), "range": float(sel["vgm_range_m"])}

    lo = pd.read_csv(OUT_01B_LOO, float_precision="round_trip")
    wells = lo[lo["state"] == "mean"][["well", "E", "N"]].reset_index(drop=True)
    el = pd.read_csv(INT_WELL_ELEVATIONS)
    el["k"] = el["Name_norm"].str.lower()
    el = el.dropna(subset=["ground_elev_m"]).drop_duplicates("k").set_index("k")
    lev = pd.read_csv(INT_WELLS_ALL, index_col=0, float_precision="round_trip")
    lev.index = pd.to_datetime(lev.index)
    lev.columns = lev.columns.str.lower()
    for sn, months in seasons.items():   # the 01b frame: ground + reading, mean over the season's months
        v = lev.reindex(pd.DatetimeIndex(months))[wells["well"]].mean().values
        wells[f"head_{sn}"] = el.loc[wells["well"], "ground_elev_m"].values + v

    area = geojson_geom(DATA_STUDY_AREA_GEOJSON)
    coast = geojson_geom(DATA_COASTLINE_HWM)
    src, Z = load_dem()
    rasters = drift_rasters(Z, float(src.res[0]))
    sea = sea_anchors(area, coast, src, rasters)
    xy, kind = [sea], ["sea"] * len(sea)
    head = {sn: [np.full(len(sea), head_sea)] for sn in seasons}
    ba = pd.read_csv(OUT_01B_BOUNDARY_ANCHORS, float_precision="round_trip")
    if kept("river"):
        r = ba[ba["kind"] == "river"]
        xy.append(r[["E", "N"]].values); kind += ["river"] * len(r)
        for sn in seasons:
            head[sn].append(r["head_mean_m"].values)
    if kept("lake"):
        lxy, llev, _, _ = lake_boundary(seasons)
        xy.append(lxy); kind += ["lake"] * len(lxy)
        for sn in seasons:
            head[sn].append(np.full(len(lxy), llev[sn]))
    rw = C.SLACK_FLOW_RIDGE_WELL
    rdepth = ridge_depths(lev, seasons)
    if kept(f"ridge_well_{rw}") and rw in el.index:
        xy.append(np.array([[el.loc[rw, "E"], el.loc[rw, "N"]]])); kind += ["ridge well"]
        for sn in seasons:
            head[sn].append(np.array([el.loc[rw, "ground_elev_m"] - rdepth[sn][0]]))
    if kept("ridge_line"):
        r = ba[ba["kind"] == "ridge"]
        xy.append(r[["E", "N"]].values); kind += ["ridge"] * len(r)
        for sn in seasons:
            head[sn].append(r["ground_m"].values - rdepth[sn][0])
    drift_at = None if drift == "o" else (lambda q: sample(src, rasters[drift], q[:, 0], q[:, 1])[:, None])
    return {"wells": wells, "anchor_xy": np.vstack(xy), "anchor_kind": np.array(kind),
            "anchor_head": {sn: np.concatenate(h) for sn, h in head.items()},
            "vgm": vgm, "drift": drift, "head_sea": head_sea, "drift_at": drift_at}


def depth_surface(wells: pd.DataFrame, months, grid_m: float, xi=None, yi=None) -> dict:
    """A depth map drawn the way the water table is (D-205, D-206): the wells' LEVEL (m OD)
    kriged with Script 01b's recorded system — its drift, its mean-state variogram, the sea
    at its fitted coastal head, and the river, the lake and the ridge well it kept — then
    subtracted from the ground. The lake and ridge-well heads are taken over `months`, the
    months the mapped statistic draws on.

    wells: DataFrame with columns well, E, N, level (m OD). A ridge-well anchor is dropped
    when that well is already among the data (a duplicate point makes the system singular).
    The ground on the grid is the DEM averaged onto each grid cell; cells outside the site
    mask (map_utils.make_site_mask, D-204), or with ground below mean high water, are NaN.

    Returns {gx, gy, level, se, ground, depth (ground - level, m below ground, +ve down),
    ground_at_wells (DEM cell at each well), n_anchors}."""
    from rasterio.warp import reproject, Resampling          # noqa: PLC0415
    from rasterio.transform import from_origin               # noqa: PLC0415
    from utils.map_utils import make_site_mask               # noqa: PLC0415
    sysd = recorded_system({"map": pd.DatetimeIndex(months)})
    axy, ahead, akind = sysd["anchor_xy"], sysd["anchor_head"]["map"], sysd["anchor_kind"]
    have = set(wells["well"].astype(str).str.lower())
    keep = ~((akind == "ridge well") & (C.SLACK_FLOW_RIDGE_WELL in have))
    axy, ahead = axy[keep], ahead[keep]
    if sysd["drift"] != "o":
        raise NotImplementedError("depth_surface: 01b selected a drift; only ordinary kriging is wired")
    dxy = np.vstack([wells[["E", "N"]].to_numpy(float), axy])
    dz = np.concatenate([wells["level"].to_numpy(float), ahead])

    if xi is None:
        xi = np.arange(C.SITE_MAP_EAST_MIN, C.SITE_MAP_EAST_MAX, grid_m) + grid_m / 2
    if yi is None:
        yi = np.arange(C.SITE_MAP_NORTH_MIN, C.SITE_MAP_NORTH_MAX, grid_m) + grid_m / 2
    gx, gy = np.meshgrid(xi, yi)
    inside = make_site_mask(gx, gy)
    level = np.full(gx.shape, np.nan); se = np.full(gx.shape, np.nan)
    t = np.column_stack([gx[inside], gy[inside]])
    p, e = ked(dxy, dz, None, t, None, sysd["vgm"])
    level[inside] = p; se[inside] = e

    # DEM averaged onto the grid (rows run north to south in the raster; flip back after).
    src, Z = load_dem()
    dst = np.full((len(yi), len(xi)), np.nan)
    reproject(Z, dst, src_transform=src.transform, src_crs=src.crs, src_nodata=src.nodata,
              dst_transform=from_origin(xi[0] - grid_m / 2, yi[-1] + grid_m / 2, grid_m, grid_m),
              dst_crs=src.crs, dst_nodata=np.nan, resampling=Resampling.average)
    ground = dst[::-1]
    # Cells below mean high water are the shore and the channel, not dune: no depth there.
    ground = np.where(inside & (ground >= tidal_levels()["MHW"]), ground, np.nan)
    return {"gx": gx, "gy": gy, "level": level, "se": se, "ground": ground,
            "depth": ground - level,
            "ground_at_wells": sample(src, Z, wells["E"], wells["N"]),
            "n_anchors": int(len(axy))}
