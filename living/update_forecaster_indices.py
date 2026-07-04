#!/usr/bin/env python3
"""
update_forecaster_indices.py
============================

Build the forecaster's structural ecohydrology feed (`forecaster_indices.json`)
from frozen Script 26 outputs: per-well Equilibrium Wetness Index (EWI) and a
projected Ellenberg-F (EbF).

Unlike the current-levels / MSL5 feeds (which are living, recomputed from the
hub), EWI and EbF are STRUCTURAL — derived from the wells' SSM coefficients and,
for EbF, from the 18-well vegetation calibration. They change only when the
pipeline reruns; regenerating this feed monthly is harmless (same inputs).

EbF projection
--------------
EbF is measured for only 18 vegetation-surveyed wells. For the rest it is
projected from EWI_annual, the strongest structural predictor (leave-one-out
Q2 ~= 0.58; per-well EWI_m_bg and MSL5 give ~0 skill and are NOT used).

EWI_annual = (b1*P_ann - b2*PET_ann)/b3 - DRAINAGE_DATUM. The betas are per-well
(from the EWI CSV); the two climate constants P_ann, PET_ann are recovered by
least squares from the 18 wells whose EWI_annual the pipeline already reports,
which reproduces the pipeline's EWI_annual exactly (self-checked below). Nothing
is hardcoded.

Each well's EbF carries a tier so the forecaster never presents them as equal:
    measured      - one of the 18 surveyed wells (uses the surveyed EbF)
    projected     - modelled, within the calibration EWI range
    extrapolated  - modelled, beyond the calibration EWI range (lower confidence)
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

DRAINAGE_DATUM = 3.7  # config.py; datum for equilibrium displacement


def _norm(s):
    return "".join(ch for ch in str(s).strip().lower() if ch.isalnum())


def load_ewi(path):
    d = pd.read_csv(path)
    need = {"well", "beta_1_recharge", "beta_2_atmospheric_draw",
            "beta_3_drainage", "EWI_m_bg", "cluster_id"}
    missing = need - set(d.columns)
    if missing:
        raise ValueError(f"{path} missing column(s): {sorted(missing)}")
    d["k"] = d["well"].map(_norm)
    return d


def load_ebf(path):
    d = pd.read_csv(path)
    need = {"piezo", "EbF", "EWI_annual"}
    missing = need - set(d.columns)
    if missing:
        raise ValueError(f"{path} missing column(s): {sorted(missing)}")
    d["k"] = d["piezo"].map(_norm)
    return d


def recover_climate_constants(ewi, ebf):
    """Back out (P_ann, PET_ann) from the wells whose EWI_annual is known, so
    EWI_annual can be reproduced for every well from its betas."""
    j = ebf[["k", "EWI_annual"]].merge(
        ewi[["k", "beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage"]],
        on="k").dropna()
    lhs = (j["EWI_annual"] + DRAINAGE_DATUM) * j["beta_3_drainage"]
    A = np.column_stack([j["beta_1_recharge"].to_numpy(),
                         -j["beta_2_atmospheric_draw"].to_numpy()])
    (p_ann, pet_ann), *_ = np.linalg.lstsq(A, lhs.to_numpy(), rcond=None)
    return float(p_ann), float(pet_ann), j


def ewi_annual(ewi, p_ann, pet_ann):
    return ((ewi["beta_1_recharge"] * p_ann
             - ewi["beta_2_atmospheric_draw"] * pet_ann)
            / ewi["beta_3_drainage"] - DRAINAGE_DATUM)


def loo_q2_rmse(x, y):
    x, y = np.asarray(x), np.asarray(y)
    pred = np.array([np.polyval(np.polyfit(np.delete(x, i), np.delete(y, i), 1), x[i])
                     for i in range(len(x))])
    ss_res = float(((pred - y) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return 1 - ss_res / ss_tot, float(np.sqrt(ss_res / len(y)))


def build(ewi_path, ebf_path):
    ewi = load_ewi(ewi_path)
    ebf = load_ebf(ebf_path)

    p_ann, pet_ann, joined = recover_climate_constants(ewi, ebf)
    ewi["EWI_annual"] = ewi_annual(ewi, p_ann, pet_ann)

    # self-check: reproduced EWI_annual must match the pipeline's for the 18
    chk = ebf[["k", "EWI_annual"]].merge(ewi[["k", "EWI_annual"]], on="k",
                                         suffixes=("_ref", "_rep")).dropna()
    max_diff = float((chk["EWI_annual_ref"] - chk["EWI_annual_rep"]).abs().max())
    if max_diff > 1e-3:
        raise ValueError(f"EWI_annual reproduction failed (max diff {max_diff:.4f}); "
                         "climate subset likely differs — check inputs.")

    # calibrate EbF ~ EWI_annual on the surveyed wells
    cal = ebf[["k", "EbF"]].merge(ewi[["k", "EWI_annual"]], on="k").dropna()
    slope, intercept = np.polyfit(cal["EWI_annual"], cal["EbF"], 1)
    q2, rmse = loo_q2_rmse(cal["EWI_annual"].to_numpy(), cal["EbF"].to_numpy())
    ewi_lo, ewi_hi = float(cal["EWI_annual"].min()), float(cal["EWI_annual"].max())
    ebf_lo, ebf_hi = float(cal["EbF"].min()), float(cal["EbF"].max())
    measured = dict(zip(ebf["k"], ebf["EbF"]))

    wells = {}
    cl_ewi, cl_ebf = {}, {}
    for _, r in ewi.iterrows():
        k = r["k"]
        ewa = float(r["EWI_annual"])
        if k in measured and pd.notna(measured[k]):
            ebf_val, tier = float(measured[k]), "measured"
        else:
            ebf_val = float(intercept + slope * ewa)
            tier = "extrapolated" if (ewa < ewi_lo or ewa > ewi_hi) else "projected"
        wells[k] = {
            "EWI_m_bg": round(float(r["EWI_m_bg"]), 3),
            "EWI_annual": round(ewa, 3),
            "EbF": round(ebf_val, 2),
            "EbF_tier": tier,
        }
        cid = r.get("cluster_id")
        if pd.notna(cid):
            ck = f"C{int(cid)}"
            cl_ewi.setdefault(ck, []).append(float(r["EWI_m_bg"]))
            cl_ebf.setdefault(ck, []).append(ebf_val)

    clusters = {ck: {"mean_EWI_m_bg": round(float(np.mean(cl_ewi[ck])), 3),
                     "mean_EbF": round(float(np.mean(cl_ebf[ck])), 2),
                     "n": len(cl_ewi[ck])}
                for ck in sorted(cl_ewi)}

    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": ("EWI: equilibrium wetness index (m below ground) from SSM "
                   "coefficients. EbF: measured for surveyed wells, else projected "
                   "from EWI_annual (EbF = a + b*EWI_annual). Tiers: measured / "
                   "projected / extrapolated."),
        "ebf_calibration": {
            "n": int(len(cal)),
            "slope": round(float(slope), 4),
            "intercept": round(float(intercept), 4),
            "loo_q2": round(q2, 3),
            "loo_rmse": round(rmse, 3),
            "ewi_annual_range": [round(ewi_lo, 3), round(ewi_hi, 3)],
            "ebf_range": [round(ebf_lo, 2), round(ebf_hi, 2)],
        },
        "n_wells": len(wells),
        "wells": dict(sorted(wells.items())),
        "clusters": clusters,
    }


def main():
    ap = argparse.ArgumentParser(
        description="Build forecaster_indices.json (EWI + projected EbF) from Script 26 CSVs.")
    ap.add_argument("--ewi", required=True,
                    help="26_equilibrium_wetness_index_per_well.csv")
    ap.add_argument("--ebf", required=True, help="26_ebf_comparison.csv")
    ap.add_argument("--out", required=True, help="Path to write forecaster_indices.json")
    args = ap.parse_args()

    try:
        feed = build(args.ewi, args.ebf)
    except Exception as e:  # noqa: BLE001
        print(f"  [ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(feed, f, indent=2)
        f.write("\n")

    c = feed["ebf_calibration"]
    tiers = {}
    for w in feed["wells"].values():
        tiers[w["EbF_tier"]] = tiers.get(w["EbF_tier"], 0) + 1
    print(f"  Forecaster indices written: {args.out}")
    print(f"    wells        : {feed['n_wells']}")
    print(f"    EbF tiers    : " + ", ".join(f"{k}={v}" for k, v in sorted(tiers.items())))
    print(f"    EbF fit      : EbF = {c['intercept']} + {c['slope']}*EWI_annual "
          f"(n={c['n']}, LOO-Q2={c['loo_q2']}, RMSE={c['loo_rmse']})")


if __name__ == "__main__":
    main()
