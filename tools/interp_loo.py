#!/usr/bin/env python3
"""
tools/interp_loo.py — leave-one-well-out test of the interpolators behind the per-well maps
==========================================================================================

Which interpolator should draw each per-well map? The same test D-205 put to the water
table: drop each well in turn, predict it from the others, and score the error. Methods:

  mean     the mean of the other wells (the no-skill baseline every surface must beat)
  linear   Delaunay piecewise-linear with nearest fill outside the hull — what
           map_utils.add_idw_surface() draws (method="linear", hull_buffer extension)
  idw2     inverse-distance weighting, power 2 (Script 32's inline surface)
  ok       ordinary kriging, spherical variogram refitted in every fold on the other
           wells (utils/kriging.py; bins and max lag as Script 01b, SLACK_FLOW_VGM_*)

For the depth-type metrics (a level against the ground), two further rows interpolate
the LEVEL in maOD and subtract the well's ground (ground_elev_m, 01_locations.csv) —
the route the kriged water table takes:
  linear_head, ok_head

Skill = 1 - MSE / MSE(mean); skill_medae = 1 - MedAE / MedAE(mean) is the same score
on the median absolute error, which one badly-predicted well cannot dominate (the ridge
well CEH12, 20 m above its neighbours, does exactly that to the head rows). A method with skill near zero draws a surface that
carries no information the cluster colours of the markers do not. The all-well
variogram's nugget share (nugget / (nugget + partial sill)) says how much of the
metric's variance is spatially unstructured at the network's spacing.

Reads only committed pipeline outputs; writes nothing into outputs/.
Run:  python3 tools/interp_loo.py [--out notes/findings/NRG_interp_loo_<date>.csv]
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-28. New (proofread: "Kriging or Delaunay").

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import griddata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from utils import config as C  # noqa: E402
from utils.kriging import empirical_variogram, fit_spherical, ked, ols_residuals  # noqa: E402

O = ROOT / "outputs"


def norm(s) -> str:
    return str(s).strip().lower().replace(" ", "")


# (label, script, csv, id col, E col, N col, value col, level_sign, row filter)
# level_sign: +1 if value is a level relative to ground (m, +ve above), -1 if a depth
# below ground (m, +ve below), None if not a level. head = ground + sign*value.
METRICS = [
    ("beta_1_recharge", "07", "03_master_data.csv", "Name_Original", "Easting", "Northing", "beta_1_recharge", None, None),
    ("beta_2_atmospheric_draw", "07", "03_master_data.csv", "Name_Original", "Easting", "Northing", "beta_2_atmospheric_draw", None, None),
    ("beta_3_drainage", "07", "03_master_data.csv", "Name_Original", "Easting", "Northing", "beta_3_drainage", None, None),
    ("Model_R2", "07", "03_master_data.csv", "Name_Original", "Easting", "Northing", "Model_R2", None, None),
    ("scrape_step_cc", "10b", "10_clearfell_baci/10b_spatial_step_data.csv", "well", "E", "N", "scrape_step_cc", None, None),
    ("fell_step_cc", "10b", "10_clearfell_baci/10b_spatial_step_data.csv", "well", "E", "N", "fell_step_cc", None, None),
    ("summer_min_depth_bg", "11b", "11b_spatial_thresholds/11b_03_pflood_per_well.csv", "well", "E", "N", "depth_bg", -1, None),
    ("pflood_mm", "11b", "11b_spatial_thresholds/11b_03_pflood_per_well.csv", "well", "E", "N", "pflood_mm", None, "unreachable"),
    ("msl5_change_2017_2023", "20", "20_spatial_figures/20_msl5_change_perwell.csv", "well", "E", "N", "raw_change_mm", None, None),
    ("Sy_median", "18", "18_wtf_spatial/18_wtf_01_well_sy_estimates.csv", "Well", "Easting", "Northing", "Sy_median", None, None),
    ("residual_wb", "20", "20_spatial_figures/20_residual_perwell.csv", "well", "E", "N", "residual_wb", None, None),
    ("MSL5_m_bg", "26", "26_van_willegen_msl/26_msl_5yr_latest_per_well.csv", "well", None, None, "MSL5_m_bg", +1, "msl5_excluded"),
    ("diff_slope_2011_2025", "32", "32_differential_movement/32_differential_movement_per_well.csv", "key", "E", "N", "slope_mm_yr_2011_2025", None, None),
    ("diff_slope_2005_2025", "32", "32_differential_movement/32_differential_movement_per_well.csv", "key", "E", "N", "slope_mm_yr_2005_2025", None, None),
    ("envelope_swing_mm", "33", "33_envelope_amplification/33_envelope_per_well.csv", "key", "E", "N", "swing_mm", None, "flagged"),
    ("envelope_amplification", "33", "33_envelope_amplification/33_envelope_per_well.csv", "key", "E", "N", "amplification", None, "flagged"),
    ("abs_trend_2005_2025", "36", "36_absolute_climate_trend/36_absolute_climate_trend_per_well.csv", "key", "E", "N", "slope_mm_yr_2005_2025", None, None),
    ("driver_residual_2005_2025", "37", "37_driver_validation/37_driver_validation_per_well.csv", "key", "E", "N", "residual_2005_2025", None, None),
]


def pred_linear(xy, z, t):
    p = griddata(xy, z, t[None, :], method="linear")[0]
    if not np.isfinite(p):
        p = griddata(xy, z, t[None, :], method="nearest")[0]
        return p, False
    return p, True


def pred_idw(xy, z, t, power=2.0):
    d = np.hypot(*(xy - t).T)
    w = 1.0 / np.maximum(d, 1e-6) ** power
    return float((w * z).sum() / w.sum())


def vgm_fit(xy, z):
    r = ols_residuals(z, None)
    lag, gam, cnt = empirical_variogram(xy, r, C.SLACK_FLOW_VGM_BINS, C.SLACK_FLOW_VGM_MAX_LAG_M)
    return fit_spherical(lag, gam, cnt, C.SLACK_FLOW_VGM_MAX_LAG_M)


def pred_ok(xy, z, t):
    v = vgm_fit(xy, z)
    p, _ = ked(xy, z, None, t[None, :], None, v)
    return float(p[0]), v["ok"]


def loo(xy, z, method):
    n = len(z); out = np.empty(n); flag = np.ones(n, bool)
    for i in range(n):
        m = np.arange(n) != i
        if method == "mean":
            out[i] = z[m].mean()
        elif method == "linear":
            out[i], flag[i] = pred_linear(xy[m], z[m], xy[i])
        elif method == "idw2":
            out[i] = pred_idw(xy[m], z[m], xy[i])
        elif method == "ok":
            out[i], flag[i] = pred_ok(xy[m], z[m], xy[i])
    return out, flag


def load(metric, locs):
    label, script, csv, idc, ec, nc, vc, sign, filt = metric
    df = pd.read_csv(O / csv)
    if filt and filt in df.columns:
        df = df[~df[filt].fillna(False).astype(bool)]
    df = df.assign(key=df[idc].map(norm))
    if ec is None:
        df = df.merge(locs[["key", "E", "N"]], on="key", how="left"); ec, nc = "E", "N"
    df = df.merge(locs[["key", "ground"]], on="key", how="left")
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=[ec, nc, vc])
    df = df.drop_duplicates("key")
    return df[["key", ec, nc, vc, "ground"]].set_axis(["key", "E", "N", "v", "ground"], axis=1)


def score(z, p):
    e = p - z
    return dict(rmse=float(np.sqrt(np.mean(e ** 2))), mae=float(np.mean(np.abs(e))),
                medae=float(np.median(np.abs(e))), bias=float(np.mean(e)),
                worst_abs=float(np.max(np.abs(e))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "notes/findings/NRG_interp_loo_2026-09-28.csv"))
    a = ap.parse_args()
    locs = pd.read_csv(O / "01_locations.csv")
    locs = locs.assign(key=locs["Name"].map(norm), ground=locs["ground_elev_m"])
    rows = []
    for met in METRICS:
        label, script, sign = met[0], met[1], met[7]
        df = load(met, locs)
        xy = df[["E", "N"]].to_numpy(float); z = df["v"].to_numpy(float)
        vall = vgm_fit(xy, z)
        nug = vall["nugget"] / max(vall["nugget"] + vall["psill"], 1e-12)
        base = None
        variants = [(m, z, None) for m in ("mean", "linear", "idw2", "ok")]
        if sign is not None and df["ground"].notna().all():
            head = df["ground"].to_numpy(float) + sign * z
            variants += [("linear_head", head, sign), ("ok_head", head, sign)]
        for name, target, sg in variants:
            meth = name.replace("_head", "")
            p, flag = loo(xy, target, meth)
            if sg is not None:            # back to the metric: value = (head - ground)/sign
                p = (p - df["ground"].to_numpy(float)) / sg
            s = score(z, p)
            if name == "mean":
                base = s["rmse"]; base_med = s["medae"]
            worst = df["key"].iloc[int(np.argmax(np.abs(p - z)))]
            rows.append(dict(metric=label, script=script, method=name, n=len(z),
                             **s, worst_well=worst, skill=1 - (s["rmse"] / base) ** 2,
                             skill_medae=1 - s["medae"] / base_med,
                             inside_hull_or_fit_ok=int(flag.sum()),
                             sd=float(z.std(ddof=1)), vgm_nugget_share=nug,
                             vgm_range_m=vall["range"], vgm_ok=vall["ok"]))
        best = max((r for r in rows if r["metric"] == label), key=lambda r: r["skill"])
        print(f"{label:<26} n={len(z):>3} nug {nug:4.2f} best {best['method']:<11} "
              + " ".join(f"{r['method']}={r['skill']:+.2f}/{r['skill_medae']:+.2f}"
                         for r in rows if r["metric"] == label))
    out = pd.DataFrame(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out, index=False)
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
