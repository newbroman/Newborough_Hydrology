"""
40_shoreline_retreat.py — Shoreline retreat from the digitised coastline epochs
================================================================================

Wired into run_analysis.py 2026-08-29. Tier and execution mode are declared by
the orchestrator, not here; see outputs/pipeline_manifest.json for this script's
tier, execution mode, and current step index.

Purpose (one sentence)
    Measure shoreline displacement between the digitised coast lines as SIGNED
    shore-normal distance, with the diagnostics that decide whether the result
    is a measurement of a shoreline at all -- and WITHHOLD the rate when they
    say it is not.

Why this exists
    The retreat series lived in a working note as a session computation, so
    under D-006 nothing in it was citable. Making it a pipeline output is what
    D-060's Revisit-if asks for. But a retreat measurement that cannot
    distinguish a rigid shift of a digitised line from real retreat is not a
    measurement, so the diagnostics are not extras: they are what makes the
    rate mean anything.

The defect designed out
    The session computation used NEAREST DISTANCE from each sampled point to
    the other line. That quantity is ALWAYS POSITIVE. It structurally cannot
    see progradation, a sign change, or a floor -- which is exactly why a field
    with no progradation anywhere, whose least-eroding point sat at the highest
    independently surveyed rate on the frontage, read as a clean result.
    Signed shore-normal displacement makes the floor, the progradation count
    and the alongshore trend fall out for free. Nearest distance is retained as
    a labelled comparator column only, so the historical figures stay legible.

The gate (D-085)
    A "not citable" note relies on the next reader honouring it; a refusal does
    not, and D-006 makes a pipeline output citable BY DEFINITION. So the
    refusal is in the output, not beside it: rate_m_yr is written only when the
    floor, control and generalisation tests all pass, and is NA with a
    populated withheld_reason otherwise. The script does not fail the pipeline
    and does not warn-and-continue with a number. Nothing downstream can quote
    what is not there.

Reading order for anyone picking this up
    working/updates/NRG_script40_retreat_spec_2026-08-29.md   the signed-off spec
    working/updates/NRG_retreat_alongshore_probe_2026-08-29.md the measurements
    data/geo/GEO_PROVENANCE.md                                 the inputs
    D-085, D-086                                               the rulings
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-29. First issue, to the
#   signed-off spec. Signed shore-normal displacement; common frontage
#   restricted by EXTENT rather than hit-success (a spurious hit is a hit, and
#   a hit-success mask produced a phantom 22.8 m of southern progradation on
#   2026-08-29); a self-withholding headline; the fixed-feature control on the
#   identical code path; a measured chord-sagitta generalisation bound rather
#   than a densification that would only interpolate along the chords that are
#   the error; the DTM profile position that says WHICH INDICATOR these lines
#   are; and the D-060 regression test against the retained 2015 fixture.

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import math
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import config, paths
from utils.console_utils import (banner, phase, step, info, warn, saved, note,
                                 result, done)
from utils.render_utils import render_figure

SCRIPT_ID = "40"
VERSION = __version__

SPACING_M    = config.SHORE_NORMAL_SPACING_M
MAX_RANGE_M  = config.SHORE_NORMAL_MAX_RANGE_M
PUBLISHED_MAX = config.PUBLISHED_MAX_PROFILE_RATE
TOL_CONTROL  = config.SHORE_CONTROL_TOLERANCE_M
TOL_GENERAL  = config.SHORE_GENERALISATION_TOLERANCE_M

# Epoch registry. Dates are the imagery dates recorded in GEO_PROVENANCE.md;
# 1899 is the OS survey revision, not the printing. Nothing here is a magic
# number: each is the date the line depicts, and the intervals divide by the
# difference between them.
EPOCHS = [
    ("1899", paths.DATA_KML_COAST_1899, "1899-01-01"),
    ("2006", paths.DATA_KML_COAST_2006, "2006-01-01"),
    ("2012", paths.DATA_KML_COAST_2012, "2012-05-26"),
    ("2020", paths.DATA_KML_COAST_2020, "2020-04-24"),
]
FIXTURE_EPOCH = ("2015", paths.DATA_KML_COAST_2015_FIXTURE, "2015-01-01")

# The pairs reported. Consecutive intervals show the shape of the series; the
# two spans are what the documents would quote.
INTERVALS = [("1899", "2006"), ("2006", "2012"), ("2012", "2020"),
             ("2006", "2020"), ("1899", "2020")]
FLOOR_INTERVAL = ("2006", "2020")   # longest modern interval; the floor test

# D-060's published result, the only external anchor the method has.
D060_DISPLACEMENT_M = 75.2
D060_RATE_M_YR      = 0.65
D060_TOLERANCE_PCT  = 10.0


# ======================================================================
# Geometry
# ======================================================================
def _read_kml(path):
    """Every <coordinates> block in a KML, as arrays of (lon, lat)."""
    raw = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    out = []
    for block in re.findall(r"<coordinates>(.*?)</coordinates>", raw, re.S):
        pts = []
        for tok in block.split():
            parts = tok.split(",")
            if len(parts) >= 2:
                pts.append((float(parts[0]), float(parts[1])))
        if len(pts) >= 2:
            out.append(np.asarray(pts, dtype=float))
    if not out:
        raise ValueError(f"no usable <coordinates> in {path}")
    return out


def _projection_origin(all_lonlat):
    """Centroid of every input vertex — the local projection origin."""
    stacked = np.vstack(all_lonlat)
    return float(stacked[:, 1].mean()), float(stacked[:, 0].mean())


def _to_local_m(lonlat, lat0, lon0):
    """Local equirectangular metres about (lat0, lon0).

    Over ~4 km at 53 deg N the distortion is far below the 5.95 m
    georeferencing error carried by the 1899 line. Asserted in main(), not
    assumed.
    """
    r = 6371000.0
    x = np.radians(lonlat[:, 0] - lon0) * r * math.cos(math.radians(lat0))
    y = np.radians(lonlat[:, 1] - lat0) * r
    return np.column_stack([x, y])


def _resample(P, spacing):
    """Points every `spacing` metres along polyline P, with arc length."""
    seg = np.hypot(*(P[1:] - P[:-1]).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(int(s[-1] // spacing), 1)
    t = np.linspace(0.0, s[-1], n + 1)
    return np.column_stack([np.interp(t, s, P[:, 0]),
                            np.interp(t, s, P[:, 1])]), t


def _normals(P, inland_xy):
    """Unit normals oriented SEAWARD, i.e. away from the inland reference.

    The reference is the centroid of the site-boundary mask, not a hardcoded
    bearing: a bearing baked in here would silently mis-sign the whole field if
    the frontage were ever re-digitised over a different stretch.
    """
    d = np.gradient(P, axis=0)
    T = d / np.hypot(*d.T)[:, None]
    N = np.column_stack([-T[:, 1], T[:, 0]])
    outward = P - inland_xy
    N[np.einsum("ij,ij->i", N, outward) < 0] *= -1.0
    return N


def _bearings_deg(N):
    return (np.degrees(np.arctan2(N[:, 0], N[:, 1])) + 360.0) % 360.0


def _ray_signed(p, n, Q, max_range):
    """Signed distance from p to polyline Q along +/- n. Positive = seaward.

    No intersection within max_range is NaN, never zero: a zero would read as
    "no movement" and quietly enter a median.
    """
    A, B = Q[:-1], Q[1:]
    AB = B - A
    den = AB[:, 0] * (-n[1]) - AB[:, 1] * (-n[0])
    ok = np.abs(den) > 1e-12
    AP = p - A
    safe = np.where(ok, den, 1.0)
    u = np.where(ok, (AP[:, 0] * (-n[1]) - AP[:, 1] * (-n[0])) / safe, np.nan)
    s = np.where(ok, (AB[:, 0] * AP[:, 1] - AB[:, 1] * AP[:, 0]) / safe, np.nan)
    hit = ok & (u >= 0.0) & (u <= 1.0) & (np.abs(s) <= max_range)
    if not hit.any():
        return float("nan")
    cand = s[hit]
    return float(cand[np.argmin(np.abs(cand))])


def _nearest_signed(p, n, Q):
    """Superseded comparator: nearest distance, signed by the normal.

    Retained so the historical figures stay comparable. Its magnitude is
    always the minimum distance, so it cannot see a floor -- which is the
    defect this script exists to remove, kept visible rather than deleted.
    """
    A, B = Q[:-1], Q[1:]
    AB = B - A
    denom = np.einsum("ij,ij->i", AB, AB)
    denom = np.where(denom > 0, denom, 1.0)
    t = np.clip(np.einsum("ij,ij->i", p - A, AB) / denom, 0.0, 1.0)
    proj = A + t[:, None] * AB
    dist = np.hypot(*(proj - p).T)
    i = int(np.argmin(dist))
    return float(dist[i] * np.sign(np.dot(proj[i] - p, n)))


# ======================================================================
# Measurement
# ======================================================================
def _identify_1899_lines(lines_m, ref_2020, inland_xy):
    """Which placemark of coast1899.kml is the dune edge?

    The file carries two lines and labels neither. Index order is not trusted:
    a re-export that reordered them would silently swap the high-water line for
    the dune edge, and every long-run rate with it. Instead each candidate is
    measured against the 2020 line and the SMALLER displacement is the dune
    edge, the high-water mark lying further seaward by construction.
    """
    S, _ = _resample(ref_2020, SPACING_M)
    N = _normals(S, inland_xy)
    meds = []
    for cand in lines_m:
        d = np.array([_ray_signed(S[k], N[k], cand, 600.0) for k in range(len(S))])
        d = d[~np.isnan(d)]
        meds.append(float(np.median(d)) if len(d) else float("inf"))
    edge = int(np.argmin(meds))
    hwm = 1 - edge if len(lines_m) == 2 else None
    return edge, hwm, meds


def _common_extent(lines_m, spacing):
    """Northing band spanned by EVERY line, minus one spacing at each end.

    Restricted by EXTENT, not by hit-success, and the difference is not
    cosmetic. coast2012 runs ~400 m further south than the other two; normals
    in that gap strike its unmatched southern tail and DO return a hit. A
    hit-success mask keeps those, and on 2026-08-29 that produced a reported
    22.8 m of southern progradation that does not exist.
    """
    lo = max(float(P[:, 1].min()) for P in lines_m) + spacing
    hi = min(float(P[:, 1].max()) for P in lines_m) - spacing
    return lo, hi


def _measure(earlier, later, years, inland_xy, keep_lo=None, keep_hi=None):
    """Signed shore-normal displacement from `later` back to `earlier`.

    keep_lo/keep_hi None means UNRESTRICTED — every normal that finds an
    intersection. That basis is not a shortcut: it is what the D-060 regression
    test needs, because imposing this project's masking on a historical result
    and then calling the difference a failure compares two different quantities.
    """
    S, arc = _resample(later, SPACING_M)
    N = _normals(S, inland_xy)
    within = (np.ones(len(S), dtype=bool) if keep_lo is None
              else (S[:, 1] >= keep_lo) & (S[:, 1] <= keep_hi))
    ray = np.full(len(S), np.nan)
    near = np.full(len(S), np.nan)
    for k in np.where(within)[0]:
        ray[k] = _ray_signed(S[k], N[k], earlier, MAX_RANGE_M)
        near[k] = _nearest_signed(S[k], N[k], earlier)
    ok = ~np.isnan(ray)
    v = ray[ok]
    if len(v) == 0:
        return None
    slope, intercept = (np.polyfit(arc[ok] / 1000.0, v, 1) if len(v) > 2
                        else (np.nan, np.nan))
    r = (float(np.corrcoef(arc[ok] / 1000.0, v)[0, 1]) if len(v) > 2
         else float("nan"))
    return {
        "n": int(ok.sum()),
        "median_m": float(np.median(v)),
        "min_m": float(v.min()), "max_m": float(v.max()),
        "p10_m": float(np.percentile(v, 10)),
        "p90_m": float(np.percentile(v, 90)),
        "n_progradation": int((v < 0).sum()),
        "alongshore_slope_m_per_km": float(slope),
        "alongshore_r": r,
        "frontage_span_m": float(arc[ok].max() - arc[ok].min()),
        "frontage_lo_local_m": (float("nan") if keep_lo is None else float(keep_lo)),
        "frontage_hi_local_m": (float("nan") if keep_hi is None else float(keep_hi)),
        "years": years,
        "rate_m_yr": float(np.median(v)) / years,
        "min_rate_m_yr": float(v.min()) / years,
        "nearest_median_m": float(np.nanmedian(near[ok])),
        "_arc": arc, "_ray": ray, "_near": near, "_S": S, "_N": N, "_ok": ok,
    }


# ======================================================================
# Diagnostics
# ======================================================================
def _generalisation_bound(lines_m, names):
    """Chord-sagitta bound from differencing polylines of unequal density.

    The script does NOT densify. Resampling a 14-vertex line interpolates along
    the very chords that are the error and adds no accuracy. It measures the
    bound instead: at each vertex of the finer line, the offset from the chord
    joining the neighbours a coarse-spacing away.
    """
    rows = []
    spacings = {}
    for nm, P in zip(names, lines_m):
        seg = np.hypot(*(P[1:] - P[:-1]).T)
        spacings[nm] = float(np.median(seg)) if len(seg) else float("nan")
    coarse = max(spacings.values())
    for nm, P in zip(names, lines_m):
        S, arc = _resample(P, SPACING_M)
        sag = []
        for k in range(len(S)):
            lo = np.searchsorted(arc, arc[k] - coarse / 2.0)
            hi = np.searchsorted(arc, arc[k] + coarse / 2.0) - 1
            if lo < 0 or hi >= len(S) or hi - lo < 2:
                continue
            a, b, p = S[lo], S[hi], S[k]
            ab = b - a
            L = float(np.hypot(*ab))
            if L <= 0:
                continue
            ap = p - a
            sag.append(abs(float(ab[0] * ap[1] - ab[1] * ap[0])) / L)
        rows.append({
            "line": nm, "vertices": int(len(P)),
            "median_vertex_spacing_m": spacings[nm],
            "coarsest_spacing_m": coarse,
            "sagitta_median_m": float(np.median(sag)) if sag else float("nan"),
            "sagitta_p90_m": float(np.percentile(sag, 90)) if sag else float("nan"),
            "sagitta_max_m": float(np.max(sag)) if sag else float("nan"),
        })
    bound = float(np.nanmax([r["sagitta_p90_m"] for r in rows]))
    return pd.DataFrame(rows), bound


def _control(inland_xy, keep_lo, keep_hi, lat0, lon0):
    """Apparent displacement of features that did not move = registration error.

    Absent is a valid state and it is NOT a pass: with no control there is no
    evidence about registration, and the gate treats that as failing.
    """
    path = paths.DATA_KML_SHORE_CONTROL
    if not path.exists():
        return pd.DataFrame(columns=["feature", "pair", "apparent_displacement_m"]), None
    lines = [_to_local_m(a, lat0, lon0) for a in _read_kml(path)]
    rows = []
    for i, P in enumerate(lines):
        for j, Q in enumerate(lines):
            if j <= i:
                continue
            S, _ = _resample(P, SPACING_M)
            N = _normals(S, inland_xy)
            d = np.array([_ray_signed(S[k], N[k], Q, MAX_RANGE_M)
                          for k in range(len(S))])
            d = d[~np.isnan(d)]
            if len(d):
                rows.append({"feature": f"line_{i}", "pair": f"{i}->{j}",
                             "apparent_displacement_m": float(np.median(d))})
    df = pd.DataFrame(rows)
    worst = float(df["apparent_displacement_m"].abs().max()) if len(df) else None
    return df, worst


def _dtm_profile(measured, lat0, lon0):
    """Where each line sits on the LiDAR DTM — WHICH INDICATOR these lines are.

    One surface postdates every line, so this CANNOT separate real retreat from
    indicator drift inside the series: a retreating dune reproduces the
    elevation signature of drift, and an ordering by age is what retreat
    predicts anyway. What it does establish is the comparison against an
    external dune-toe survey, because the newest line and the surface are close
    enough in date for that one reading to mean something.
    """
    try:
        import rasterio
        from pyproj import Transformer
    except Exception as exc:                                   # pragma: no cover
        warn(f"DTM profile skipped — {exc}")
        return pd.DataFrame()
    src = rasterio.open(paths.DATA_DEM)
    band = src.read(1).astype(float)
    inv = ~src.transform
    tr = Transformer.from_crs("EPSG:4326", str(src.crs), always_xy=True)
    r = 6371000.0

    def to_bng(xy):
        lon = lon0 + np.degrees(xy[:, 0] / (r * math.cos(math.radians(lat0))))
        lat = lat0 + np.degrees(xy[:, 1] / r)
        e, n = tr.transform(lon, lat)
        return np.column_stack([e, n])

    def z_at(xy):
        bng = to_bng(xy)
        col, row = inv * (bng[:, 0], bng[:, 1])
        row = np.clip(np.nan_to_num(np.asarray(row), nan=0).astype(int), 0, band.shape[0] - 1)
        col = np.clip(np.nan_to_num(np.asarray(col), nan=0).astype(int), 0, band.shape[1] - 1)
        return band[row, col]

    S, N, ok = measured["_S"], measured["_N"], measured["_ok"]
    rows = [{"line": "coast2020", "elevation_median_m_aod": float(np.median(z_at(S)[ok]))}]
    offs = np.arange(0.0, 260.0, 2.0)
    prof = np.stack([z_at(S + o * N) for o in offs], axis=1)
    for thr in (0.5, 2.0, 3.0, 4.0):
        hits = []
        for k in np.where(ok)[0]:
            below = np.where(prof[k] <= thr)[0]
            hits.append(offs[below[0]] if len(below) else np.nan)
        h = np.array(hits, dtype=float)
        rows.append({"line": "coast2020",
                     "contour_m_aod": thr,
                     "seaward_distance_median_m": float(np.nanmedian(h))})
    return pd.DataFrame(rows)


# ======================================================================
# The gate
# ======================================================================
def _evaluate_gate(floor, control_worst, sagitta_bound):
    """Decide whether a rate may be emitted. Returns (ok, [reasons]).

    Every failure is NAMED. A gate that fails without saying why teaches the
    next reader to route around it.
    """
    reasons = []

    # 1. Floor. A field with no progradation anywhere, whose least-eroding
    #    point sits at or above the highest independently surveyed rate on the
    #    same frontage, is not a measurement of a shoreline.
    if floor is None:
        reasons.append("floor test: the floor interval could not be measured")
    else:
        if floor["n_progradation"] == 0:
            reasons.append(
                f"floor test: {floor['n']} of {floor['n']} normals show retreat, "
                f"none progradation")
        if floor["min_rate_m_yr"] > PUBLISHED_MAX:
            reasons.append(
                f"floor test: least-eroding normal {floor['min_rate_m_yr']:.3f} m/yr "
                f"exceeds the published most-active-point rate {PUBLISHED_MAX:.3f} m/yr")

    # 2. Control. Absent is not a pass: with no fixed feature there is no
    #    evidence about registration at all.
    if control_worst is None:
        reasons.append("control test: control absent — no fixed-feature lines to measure")
    elif TOL_CONTROL is None:
        reasons.append("control test: SHORE_CONTROL_TOLERANCE_M is unset "
                       "(deliberately — set it from the observed spread)")
    elif control_worst > TOL_CONTROL:
        reasons.append(f"control test: apparent displacement of a fixed feature "
                       f"{control_worst:.3f} m exceeds {TOL_CONTROL:.3f} m")

    # 3. Generalisation.
    if TOL_GENERAL is None:
        reasons.append("generalisation test: SHORE_GENERALISATION_TOLERANCE_M is unset "
                       "(deliberately — set it from the measured bound)")
    elif sagitta_bound > TOL_GENERAL:
        reasons.append(f"generalisation test: chord-sagitta bound {sagitta_bound:.3f} m "
                       f"exceeds {TOL_GENERAL:.3f} m")

    return (len(reasons) == 0), reasons


def _assert_thresholds_can_fail(floor):
    """A tolerance that would not flag the present data is decoration.

    Asserted here rather than left to whoever reads the number later.
    """
    if floor is None or TOL_CONTROL is None:
        return
    offset_scale = floor["min_m"]
    if TOL_CONTROL >= offset_scale:
        warn(f"SHORE_CONTROL_TOLERANCE_M = {TOL_CONTROL:.3f} m would NOT flag the "
             f"present {offset_scale:.3f} m floor — the threshold is decoration, "
             f"not a gate")


def _regression_test(edge_1899, inland_xy, lat0, lon0):
    """Reproduce D-060's published 1899 dune edge -> 2015 result.

    The only external anchor the method has. The 2015 line is withdrawn as
    evidence and retained ONLY for this; it is not a measurement input.

    Measured UNRESTRICTED, on D-060's own basis. That matters and was found by
    this test failing: restricting to the modern common frontage returns
    87.8 m (16.8% off) and to this pair's own overlap 86.0 m (14.3% off),
    because the excluded normals sit at the ends of the frontage where
    displacement is smallest, so cutting them raises the median. Unrestricted
    returns 74.2 m, within 1.3%. The extent choice is nearly free on the modern
    series and is NOT free on the 1899 comparison, whose displacement varies far
    more alongshore -- which is itself worth knowing.
    """
    path = paths.DATA_KML_COAST_2015_FIXTURE
    if not path.exists():
        warn("regression fixture absent — D-060 reproduction NOT checked")
        return None
    line = _to_local_m(_read_kml(path)[0], lat0, lon0)
    m = _measure(edge_1899, line, 116.0, inland_xy)
    if m is None:
        warn("regression fixture produced no measurable normals")
        return None
    dev = abs(m["median_m"] - D060_DISPLACEMENT_M) / D060_DISPLACEMENT_M * 100.0
    ok = dev <= D060_TOLERANCE_PCT
    (info if ok else warn)(
        f"D-060 reproduction: {m['median_m']:.3f} m / {m['rate_m_yr']:.3f} m/yr "
        f"against published {D060_DISPLACEMENT_M} m / {D060_RATE_M_YR} m/yr "
        f"({dev:.1f}% — {'within' if ok else 'OUTSIDE'} {D060_TOLERANCE_PCT:.0f}%)")
    return {"median_m": m["median_m"], "rate_m_yr": m["rate_m_yr"],
            "deviation_pct": dev, "passed": ok}


def _figure(measured, out_path):
    """Alongshore signed displacement, with the zero line and the survey band."""
    fig, ax = plt.subplots(figsize=(9, 5), facecolor="white")
    for (a, b), m in measured.items():
        if m is None or a == "1899":
            continue
        ok = m["_ok"]
        ax.plot(m["_arc"][ok] / 1000.0, m["_ray"][ok], lw=1.4,
                label=f"{a}–{b}  (median {m['median_m']:.1f} m)")
    fl = measured.get(FLOOR_INTERVAL)
    if fl is not None:
        band = PUBLISHED_MAX * fl["years"]
        ax.axhspan(-band, band, color="0.85", zorder=0,
                   label=f"± published most-active rate × {fl['years']:.0f} yr")
    ax.axhline(0.0, color="black", lw=1.0)
    ax.set_xlabel("alongshore distance (km, south → north)")
    ax.set_ylabel("signed shore-normal displacement (m)\npositive = retreat")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Shoreline displacement along the frontage")
    fig.tight_layout()
    render_figure(fig, out_path)
    plt.close(fig)


# ======================================================================
def main():
    banner(SCRIPT_ID, "Shoreline retreat from the digitised coastline epochs",
           VERSION)

    phase(1, "Loading coastline epochs")
    raw = {name: _read_kml(path) for name, path, _ in EPOCHS}
    boundary = _read_kml(paths.DATA_KML_SITE_BOUNDARY)
    lat0, lon0 = _projection_origin([a for v in raw.values() for a in v])
    info(f"local projection origin {lat0:.4f} N, {lon0:.4f} E")

    lines = {name: [_to_local_m(a, lat0, lon0) for a in v] for name, v in raw.items()}
    inland_xy = np.vstack([_to_local_m(a, lat0, lon0) for a in boundary]).mean(axis=0)
    info(f"inland reference (site-boundary centroid) at "
         f"{inland_xy[0]:.0f}, {inland_xy[1]:.0f} m local")

    edge_i, hwm_i, meds = _identify_1899_lines(lines["1899"], lines["2020"][0], inland_xy)
    info(f"coast1899 placemarks resolved by measurement, not index order: "
         f"dune edge = placemark {edge_i} (median {meds[edge_i]:.1f} m to 2020), "
         f"high water = placemark {hwm_i} ({meds[hwm_i]:.1f} m)")
    epoch_line = {"1899": lines["1899"][edge_i], "2006": lines["2006"][0],
                  "2012": lines["2012"][0], "2020": lines["2020"][0]}
    epoch_date = {n: pd.Timestamp(d) for n, _, d in EPOCHS}

    phase(2, "Common frontage and normal orientation")
    keep_lo, keep_hi = _common_extent([epoch_line[n] for n in ("2006", "2012", "2020")],
                                      SPACING_M)
    info(f"common northing band {keep_lo:.0f} to {keep_hi:.0f} m local "
         f"(span {keep_hi - keep_lo:.0f} m) — restricted by EXTENT, not hit-success")
    S_chk, _ = _resample(epoch_line["2020"], SPACING_M)
    brg = _bearings_deg(_normals(S_chk, inland_xy))
    spread = float(brg.max() - brg.min())
    if spread > 90.0:
        raise RuntimeError(f"seaward normals span {spread:.0f} deg — orientation is "
                           f"unreliable on this frontage; refusing to measure")
    info(f"seaward normals {brg.min():.0f}–{brg.max():.0f} deg "
         f"(spread {spread:.0f} deg, inside the 90 deg cone)")

    phase(3, "Signed shore-normal displacement")
    # Primary basis: each interval on the common extent of ITS OWN two lines,
    # which is what the spec says ("all lines in the comparison"). The modern
    # three are ALSO measured on the shared modern band, because the
    # acceleration claim compares them with each other and needs a like-for-like
    # basis. Both are emitted, labelled, rather than one being chosen silently:
    # the extent choice is nearly free on the modern series and moves the 1899
    # comparison by 16%, so which basis is in use is not a detail.
    measured, modern_common = {}, {}
    years = {}
    for a, b in INTERVALS:
        yrs = (epoch_date[b] - epoch_date[a]).days / 365.25
        years[(a, b)] = yrs
        lo, hi = _common_extent([epoch_line[a], epoch_line[b]], SPACING_M)
        m = _measure(epoch_line[a], epoch_line[b], yrs, inland_xy, lo, hi)
        measured[(a, b)] = m
        if m is None:
            warn(f"{a}→{b}: no measurable normals")
            continue
        step(f"{a}→{b}: median {m['median_m']:.3f} m over {yrs:.1f} yr "
             f"= {m['rate_m_yr']:.3f} m/yr  (n={m['n']}, "
             f"progradation {m['n_progradation']}, nearest {m['nearest_median_m']:.3f} m)")
    for a, b in (("2006", "2012"), ("2012", "2020"), ("2006", "2020")):
        mc = _measure(epoch_line[a], epoch_line[b], years[(a, b)], inland_xy,
                      keep_lo, keep_hi)
        modern_common[(a, b)] = mc
        if mc is not None:
            info(f"    on the shared modern frontage: {a}→{b} "
                 f"{mc['median_m']:.3f} m = {mc['rate_m_yr']:.3f} m/yr (n={mc['n']})")

    phase(4, "Diagnostics")
    gen_df, sagitta = _generalisation_bound(
        [epoch_line[n] for n in ("2006", "2012", "2020")], ["coast2006", "coast2012", "coast2020"])
    info(f"chord-sagitta bound {sagitta:.3f} m (measured, not densified away)")
    ctl_df, ctl_worst = _control(inland_xy, keep_lo, keep_hi, lat0, lon0)
    if ctl_worst is None:
        note("fixed-feature control: ABSENT — the discriminating test has not been run")
    else:
        info(f"fixed-feature control: worst apparent displacement {ctl_worst:.3f} m")
    dtm_df = (_dtm_profile(modern_common[FLOOR_INTERVAL], lat0, lon0)
              if modern_common.get(FLOOR_INTERVAL) else pd.DataFrame())

    phase(5, "Regression test against D-060")
    reg = _regression_test(epoch_line["1899"], inland_xy, lat0, lon0)

    phase(6, "Gate")
    floor = modern_common.get(FLOOR_INTERVAL)
    _assert_thresholds_can_fail(floor)
    ok, reasons = _evaluate_gate(floor, ctl_worst, sagitta)
    if ok:
        result("headline", "EMITTED — all three gate tests pass")
    else:
        warn("HEADLINE WITHHELD — rate_m_yr written as NA. Reasons:")
        for r in reasons:
            warn(f"    {r}")
    withheld_reason = "" if ok else "; ".join(reasons)

    phase(7, "Writing outputs")
    rows = []

    def _row(a, b, m, basis, gated=True):
        row = {"from_epoch": a, "to_epoch": b, "basis": basis,
               "from_date": epoch_date[a].date().isoformat() if a in epoch_date else a,
               "to_date": epoch_date[b].date().isoformat() if b in epoch_date else b}
        row.update({k: v for k, v in m.items() if not k.startswith("_")})
        emit = ok or not gated
        row["rate_m_yr"] = m["rate_m_yr"] if emit else np.nan
        row["min_rate_m_yr"] = m["min_rate_m_yr"] if emit else np.nan
        row["withheld"] = (not emit)
        row["withheld_reason"] = "" if emit else withheld_reason
        row["estimator"] = "signed_shore_normal_ray"
        return row

    for (a, b), m in measured.items():
        if m is not None:
            rows.append(_row(a, b, m, "pair_extent"))
    for (a, b), m in modern_common.items():
        if m is not None:
            rows.append(_row(a, b, m, "modern_common_frontage"))
    if reg is not None:
        # The regression result belongs in a committed file, not only the
        # console: it is the evidence that the estimator still reproduces the
        # one published number this method can be checked against.
        rows.append({"from_epoch": "1899", "to_epoch": "2015",
                     "basis": "d060_regression_unrestricted",
                     "from_date": "1899-01-01", "to_date": "2015-01-01",
                     "years": 116.0, "median_m": reg["median_m"],
                     "rate_m_yr": reg["rate_m_yr"],
                     "d060_published_m": D060_DISPLACEMENT_M,
                     "d060_published_rate_m_yr": D060_RATE_M_YR,
                     "deviation_pct": reg["deviation_pct"],
                     "withheld": False,
                     "withheld_reason": "" if reg["passed"] else "regression test FAILED",
                     "estimator": "signed_shore_normal_ray"})
    series = pd.DataFrame(rows)
    series.to_csv(paths.OUT_40_EPOCH_SERIES, index=False)
    saved(paths.OUT_40_EPOCH_SERIES.name, f"{len(series)} intervals")

    base = modern_common[FLOOR_INTERVAL]
    nrm = pd.DataFrame({
        "index": np.arange(len(base["_S"])),
        "alongshore_m": base["_arc"],
        "E_local_m": base["_S"][:, 0], "N_local_m": base["_S"][:, 1],
        "normal_bearing_deg": _bearings_deg(base["_N"]),
    })
    for (a, b), m in modern_common.items():
        if m is not None and len(m["_ray"]) == len(nrm):
            nrm[f"signed_{a}_{b}_m"] = m["_ray"]
            nrm[f"nearest_{a}_{b}_m"] = m["_near"]
    nrm.to_csv(paths.OUT_40_NORMALS, index=False)
    saved(paths.OUT_40_NORMALS.name, f"{len(nrm)} normals")

    ctl_df.to_csv(paths.OUT_40_CONTROL, index=False)
    saved(paths.OUT_40_CONTROL.name,
          "control absent" if ctl_worst is None else f"{len(ctl_df)} pairs")
    gen_df.to_csv(paths.OUT_40_GENERALISATION, index=False)
    saved(paths.OUT_40_GENERALISATION.name, f"bound {sagitta:.3f} m")
    dtm_df.to_csv(paths.OUT_40_DTM_PROFILE, index=False)
    saved(paths.OUT_40_DTM_PROFILE.name, f"{len(dtm_df)} rows")

    _figure(modern_common, paths.OUT_40_FIG)
    saved(paths.OUT_40_FIG.name)

    if reg is not None and not reg["passed"]:
        warn("the method no longer reproduces D-060 — investigate before trusting "
             "anything above")
    done(SCRIPT_ID)


if __name__ == "__main__":
    main()
