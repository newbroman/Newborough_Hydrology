#!/usr/bin/env python3
"""
53_ccw_forest_drift.py — did the water table near the forest fall through the CCW epoch? (E14)

QUESTION
  The CCW 1989-96 hindcast (Script 39) is close to unbiased over the network, but well by well it
  splits: the climate model is too wet at the wells nearest the forest and too dry on the open
  warren. Looked at year by year (chat, 2026-10-25, before this spec), the near-forest shortfall grew
  from about 0.1 m in 1989 to about 0.5 m in 1993-94. This script asks, by a rule fixed before the
  run, whether that drift is real and tied to the forest, and only then where in time it sits.

  The pattern was SEEN before the rule was written, so a pass is weaker evidence than a blind test
  (as D-261). The grouping is by measured distance, not by eye; every well is dropped in turn; and
  the result must hold on a second coefficient basis.

METHOD (spec NRG_spec_E14_ccw_forest_side_drift_2026-10-25, approved Martin 07:36)
  Per admitted CCW well (Script 39's admission, uncensored months only), the CCW hindcast is rebuilt
  with Script 39's own functions on two coefficient bases: the comparison window (03_master_data,
  Script 39's headline, checked to reproduce 39_02) and the full record (03_15). The residual is
  model minus observed, so a rising residual is a water table falling below the model.
    slope       OLS of the monthly residual on time over E14_SPAN (m/yr); AR(1)-adjusted SE reported
    distance    to today's forest edge (data/geo/forest_boundary.geojson); inside counts as 0
    Test 1      Spearman rho(distance, slope) < 0, one-sided p < E8E_P by exact permutation
    Test 2      median slope of near wells (distance <= E14_NEAR_M) minus far wells > 0, and its
                bootstrap 95% interval (wells resampled within each group) excludes zero
    Test 3      with each well dropped: both signs kept, and test 2's interval clear of zero at
                E14_LOO_MIN_PASS or more of the drops
    Test 4      tests 1 and 2 pass on the full-record basis
    Verdict     supported (1-4) | suggested (1 and 2 on the headline, 3 or 4 failing) | not supported
  Dating, reported and never judged: a relaxing step (level change approaching its full size with
  e-fold time tau) fitted to the monthly near-minus-far residual difference, the start month and tau
  profiled on grids, with a 95% profile interval for the start month (AR(1)-adjusted n).

OUTPUTS (outputs/53_ccw_forest_drift/)
  53_01_per_well_slopes.csv   per well and basis: distance, group, slope, SE, n, mean residual
  53_02_tests.csv             per basis: the four tests' statistics and pass flags
  53_03_leave_one_out.csv     per dropped well: rho, p, median difference and interval
  53_04_dating_profile.csv    SSR by start month (best tau), with the profile interval flag
  53_05_forest_side_drift.png residual by month, near against far; slope against distance
  53_report_numbers.csv       e14_*

Run directly:  python3 src/53_ccw_forest_drift.py [--no-fig]
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-25. First issue (E14; Martin 07:32 "we need to have it
#   as a proper test", 07:36 spec approved, 07:38 "if it needs to be a separate script, then let it be").

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils import paths                                       # noqa: E402
from utils.paths import (                                     # noqa: E402
    DIR_53, OUT_53_PER_WELL, OUT_53_TESTS, OUT_53_LOO, OUT_53_DATING, OUT_53_FIG,
    OUT_53_REPORT_NUMBERS, INT_CLIMATE, INT_MASTER_DATA, OUT_03_PER_WELL_WINDOW_SENS,
    OUT_39_SERIES, DATA_FOREST_BOUNDARY, DATA_WELL_METADATA,
)
from utils.config import (                                    # noqa: E402
    E14_NEAR_M, E14_SPAN, E14_N_BOOT, E14_SEED, E14_LOO_MIN_PASS, E14_STEP_TAU_MONTHS, E8E_P,
)
from utils.hindcast_utils import (                            # noqa: E402
    load_ccw, observed_series, hindcast_well, equilibrium_depth, usable_codes, BETA_COLS,
)
from utils.console_utils import banner, phase, step, info, warn, saved, note, result, done  # noqa: E402
from utils.render_utils import MPL_DEFAULTS                   # noqa: E402
from utils.report_numbers_utils import ReportNumbers          # noqa: E402

BASES = ("comparison_window", "full_record")


# ── inputs ────────────────────────────────────────────────────────────────────────────────────────
def coefficients(basis: str) -> pd.DataFrame:
    """Per-well coefficient triples, indexed by lower-case well name."""
    if basis == "comparison_window":
        md = pd.read_csv(INT_MASTER_DATA)
    else:
        md = pd.read_csv(OUT_03_PER_WELL_WINDOW_SENS)
        md = md[md["basis"] == "full_record"]
    md["k"] = md["Name_Original"].astype(str).str.lower().str.strip()
    return md.set_index("k")


def forest_distance(names) -> dict:
    """Distance (m) from each well to today's forest edge; 0 inside the forest."""
    gj = json.loads(Path(DATA_FOREST_BOUNDARY).read_text())
    ring = gj["features"][0]["geometry"]["coordinates"][0]
    meta = pd.read_csv(DATA_WELL_METADATA)
    meta["k"] = meta["Name"].astype(str).str.lower().str.strip()
    meta = meta.set_index("k")
    out = {}
    for w in names:
        x, y = float(meta.loc[w, "E"]), float(meta.loc[w, "N"])
        inside, best = False, math.inf
        for (x1, y1, *_), (x2, y2, *_) in zip(ring, ring[1:]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
            dx, dy = x2 - x1, y2 - y1
            L = dx * dx + dy * dy
            t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L))
            best = min(best, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
        out[w] = 0.0 if inside else best
    return out


def residual_series(basis: str, obs, cmap, cl) -> dict:
    """{well: monthly residual (model - observed)} over E14_SPAN, Script 39's way."""
    md = coefficients(basis)
    adm = usable_codes(cmap, md, obs)
    adm = adm[adm["admitted"]]
    first, last = pd.Timestamp(E14_SPAN[0]), pd.Timestamp(E14_SPAN[1])
    p_mean, pet_mean = float(cl["P_m"].mean()), float(cl["PET"].mean())
    out = {}
    for r in adm.itertuples():
        betas = tuple(float(md.loc[r.well, c]) for c in BETA_COLS)
        h0 = equilibrium_depth(betas, p_mean, pet_mean)
        o, _ = observed_series(obs, r.code, r.datum_offset_m)
        pred, _ = hindcast_well(cl, betas, h0, obs["month"].min(), obs["month"].max())
        common = o.index.intersection(pred.index)
        res = (pred.loc[common] - o.loc[common]).loc[first:last]
        out[r.well] = res.sort_index()
    return out


# ── statistics ────────────────────────────────────────────────────────────────────────────────────
def slope(res: pd.Series) -> dict:
    t = (res.index.year + (res.index.month - 0.5) / 12.0).values.astype(float)
    y = res.values.astype(float)
    n = len(y)
    X = np.column_stack([np.ones(n), t - t.mean()])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    s2 = float(e @ e) / max(n - 2, 1)
    se = math.sqrt(s2 / float(((t - t.mean()) ** 2).sum()))
    rho1 = float(np.corrcoef(e[:-1], e[1:])[0, 1]) if n > 3 else 0.0
    rho1 = max(min(rho1, 0.99), 0.0)
    n_eff = n * (1 - rho1) / (1 + rho1)
    se_adj = se * math.sqrt((n - 2) / max(n_eff - 2, 1.0))
    return dict(slope_m_per_yr=float(b[1]), se_m_per_yr=se, se_ar1_m_per_yr=se_adj,
                ar1=rho1, n_months=n, mean_residual_m=float(y.mean()))


def _ranks(v):
    return pd.Series(v).rank().values


def spearman_exact(dist, slopes):
    """Spearman rho and its one-sided exact permutation p for rho <= observed."""
    rd, rs = _ranks(dist), _ranks(slopes)
    obs = float(np.corrcoef(rd, rs)[0, 1])
    perms = np.array(list(itertools.permutations(rs)), dtype=float)
    rdc = rd - rd.mean()
    pc = perms - perms.mean(axis=1, keepdims=True)
    rhos = (pc @ rdc) / (np.sqrt((pc ** 2).sum(axis=1)) * math.sqrt((rdc ** 2).sum()))
    return obs, float((rhos <= obs + 1e-12).mean())


def median_diff_ci(near, far, rng):
    near, far = np.asarray(near, float), np.asarray(far, float)
    diff = float(np.median(near) - np.median(far))
    bn = rng.choice(near, size=(E14_N_BOOT, len(near)), replace=True)
    bf = rng.choice(far, size=(E14_N_BOOT, len(far)), replace=True)
    d = np.median(bn, axis=1) - np.median(bf, axis=1)
    lo, hi = np.percentile(d, [2.5, 97.5])
    return diff, float(lo), float(hi)


def tests(tab: pd.DataFrame, rng) -> dict:
    rho, p = spearman_exact(tab["distance_m"].values, tab["slope_m_per_yr"].values)
    near = tab.loc[tab["group"] == "near", "slope_m_per_yr"]
    far = tab.loc[tab["group"] == "far", "slope_m_per_yr"]
    diff, lo, hi = median_diff_ci(near, far, rng)
    return dict(n_wells=len(tab), n_near=len(near), n_far=len(far), rho=rho, p=p,
                test1_pass=bool(rho < 0 and p < E8E_P),
                near_median_slope=float(np.median(near)), far_median_slope=float(np.median(far)),
                diff=diff, ci_lo=lo, ci_hi=hi, test2_pass=bool(diff > 0 and lo > 0))


def dating(res: dict, groups: dict) -> tuple[pd.DataFrame, dict]:
    """Relaxing step fitted to the near-minus-far monthly difference; profiled, reported only."""
    df = pd.DataFrame(res)
    near = df[[w for w in df if groups[w] == "near"]].mean(axis=1)
    far = df[[w for w in df if groups[w] == "far"]].mean(axis=1)
    d = (near - far).dropna()
    y = d.values
    n = len(y)
    idx = np.arange(n, dtype=float)
    rows = []
    for k0 in range(3, n - 3):
        best = None
        for tau in E14_STEP_TAU_MONTHS:
            x = np.where(idx >= k0, 1.0 - np.exp(-(idx - k0 + 1) / tau), 0.0)
            X = np.column_stack([np.ones(n), x])
            b, *_ = np.linalg.lstsq(X, y, rcond=None)
            ssr = float(((y - X @ b) ** 2).sum())
            if best is None or ssr < best[0]:
                best = (ssr, tau, float(b[1]))
        rows.append(dict(start_month=d.index[k0].strftime("%Y-%m"), ssr=best[0], tau_months=best[1],
                         step_m=best[2]))
    prof = pd.DataFrame(rows)
    e = y - y.mean()
    rho1 = max(min(float(np.corrcoef(e[:-1], e[1:])[0, 1]), 0.99), 0.0)
    n_eff = n * (1 - rho1) / (1 + rho1)
    i = int(prof["ssr"].idxmin())
    smin = float(prof.loc[i, "ssr"])
    crit = smin * (1 + 3.841 / max(n_eff - 4, 1.0))
    prof["in_95_interval"] = prof["ssr"] <= crit
    inside = prof[prof["in_95_interval"]]
    return prof, dict(start=prof.loc[i, "start_month"], tau=int(prof.loc[i, "tau_months"]),
                      step=float(prof.loc[i, "step_m"]), lo=inside["start_month"].min(),
                      hi=inside["start_month"].max(), n_months=n, n_eff=n_eff,
                      contiguous=bool(inside.index.max() - inside.index.min() + 1 == len(inside)))


# ── figure ────────────────────────────────────────────────────────────────────────────────────────
def plot(res: dict, tab: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    col = {"near": "#b2182b", "far": "#2166ac"}
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6), dpi=160, gridspec_kw={"width_ratios": [1.7, 1]})
    a = ax[0]
    groups = tab.set_index("well")["group"]
    df = pd.DataFrame(res)
    for w in df:
        a.plot(df.index, df[w], color=col[groups[w]], lw=0.7, alpha=0.3)
    for g in ("near", "far"):
        m = df[[w for w in df if groups[w] == g]].mean(axis=1)
        a.plot(m.index, m.values, color=col[g], lw=2.2,
               label=f"within {E14_NEAR_M:.0f} m of the forest edge" if g == "near" else
               f"beyond {E14_NEAR_M:.0f} m")
    a.axhline(0, color="0.4", lw=0.6)
    a.set_ylabel("model − observed (m)")
    a.set_title("(a) CCW hindcast residual, comparison-window coefficients", fontsize=9)
    a.legend(fontsize=7, frameon=False)
    b = ax[1]
    for r in tab.itertuples():
        b.plot(r.distance_m, r.slope_m_per_yr, "o", color=col[r.group])
        b.annotate(r.well.upper(), (r.distance_m, r.slope_m_per_yr), fontsize=6,
                   xytext=(3, 3), textcoords="offset points")
    b.axvline(E14_NEAR_M, color="0.5", ls="--", lw=0.8)
    b.axhline(0, color="0.4", lw=0.6)
    b.set_xlabel("distance to today's forest edge (m; inside = 0)")
    b.set_ylabel(f"residual slope {E14_SPAN[0][:4]}–{E14_SPAN[1][:4]} (m/yr)")
    b.set_title("(b) drift against distance", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_53_FIG)
    plt.close(fig)


# ── main ──────────────────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fig", action="store_true")
    args = ap.parse_args()
    banner("53", "Forest-side drift in the CCW epoch (E14)", version=__version__)
    if not (paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()):
        warn("CCW historic inputs not present")
        note("skipping — the 1989-96 block is an optional raw input")
        return 0
    DIR_53.mkdir(parents=True, exist_ok=True)

    phase(1, "Rebuild the CCW hindcast on both coefficient bases")
    obs, cmap = load_ccw()
    cl = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    cl = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    res = {b: residual_series(b, obs, cmap, cl) for b in BASES}
    s39 = pd.read_csv(OUT_39_SERIES, parse_dates=["month"])
    chk = []
    for w, r in res["comparison_window"].items():
        g = s39[s39["well"] == w].set_index("month")
        ref = (g["predicted_m_bg"] - g["observed_m_bg"]).reindex(r.index)
        chk.append(float((ref - r).abs().max()))
    check_vs39 = max(chk) if chk else np.nan
    info(f"wells: {len(res['comparison_window'])} (comparison window), "
         f"{len(res['full_record'])} (full record)")
    result("max |residual - 39_02| on the headline basis (m)", f"{check_vs39:.2e}")
    if not np.isfinite(check_vs39) or check_vs39 > 1e-6:
        warn("the headline basis does not reproduce Script 39 — tests not run")
        return 1

    phase(2, "Per-well slopes and distances")
    wells = sorted(set(res["comparison_window"]) | set(res["full_record"]))
    dist = forest_distance(wells)
    rows = []
    for b in BASES:
        for w, r in res[b].items():
            rows.append(dict(well=w, basis=b, distance_m=dist[w],
                             group="near" if dist[w] <= E14_NEAR_M else "far", **slope(r)))
    per = pd.DataFrame(rows)
    per.to_csv(OUT_53_PER_WELL, index=False); saved(OUT_53_PER_WELL.name)
    for r in per[per["basis"] == "comparison_window"].sort_values("distance_m").itertuples():
        step(f"{r.well:6s} {r.distance_m:6.0f} m  {r.group:4s}  slope {r.slope_m_per_yr:+.3f} m/yr "
             f"(AR1 SE {r.se_ar1_m_per_yr:.3f})")

    phase(3, "Tests 1, 2 and 4")
    rng = np.random.default_rng(E14_SEED)
    tt = {b: tests(per[per["basis"] == b].reset_index(drop=True), rng) for b in BASES}
    pd.DataFrame([dict(basis=b, **v) for b, v in tt.items()]).to_csv(OUT_53_TESTS, index=False)
    saved(OUT_53_TESTS.name)
    for b, v in tt.items():
        step(f"{b:17s} rho {v['rho']:+.2f} (p {v['p']:.4f}) test 1 {'pass' if v['test1_pass'] else 'FAIL'}; "
             f"near-far {v['diff']:+.3f} m/yr [{v['ci_lo']:+.3f}, {v['ci_hi']:+.3f}] "
             f"test 2 {'pass' if v['test2_pass'] else 'FAIL'}")

    phase(4, "Test 3: leave one out (headline basis)")
    head = per[per["basis"] == "comparison_window"].reset_index(drop=True)
    loo = []
    for w in head["well"]:
        sub = head[head["well"] != w].reset_index(drop=True)
        if sub["group"].nunique() < 2:
            continue
        v = tests(sub, rng)
        loo.append(dict(dropped=w, rho=v["rho"], p=v["p"], diff=v["diff"], ci_lo=v["ci_lo"],
                        ci_hi=v["ci_hi"], rho_negative=v["rho"] < 0, diff_positive=v["diff"] > 0,
                        ci_clear=v["ci_lo"] > 0))
    loo = pd.DataFrame(loo)
    loo.to_csv(OUT_53_LOO, index=False); saved(OUT_53_LOO.name)
    n_clear = int(loo["ci_clear"].sum())
    test3 = bool(loo["rho_negative"].all() and loo["diff_positive"].all() and n_clear >= E14_LOO_MIN_PASS)
    result("test 3", f"{'pass' if test3 else 'FAIL'}: signs kept at {int((loo['rho_negative'] & loo['diff_positive']).sum())} "
                     f"of {len(loo)} drops; interval clear at {n_clear} (needs {E14_LOO_MIN_PASS})")

    h, f = tt["comparison_window"], tt["full_record"]
    test4 = bool(f["test1_pass"] and f["test2_pass"])
    if h["test1_pass"] and h["test2_pass"] and test3 and test4:
        verdict = "supported"
    elif h["test1_pass"] and h["test2_pass"]:
        verdict = "suggested"
    else:
        verdict = "not supported"
    result("E14 verdict", verdict)

    phase(5, "Dating (reported, never judged)")
    groups = head.set_index("well")["group"].to_dict()
    prof, dt = dating(res["comparison_window"], groups)
    prof.to_csv(OUT_53_DATING, index=False); saved(OUT_53_DATING.name)
    if verdict == "not supported":
        note("verdict is not supported: the dating is written to its file but carries no report key")
    else:
        result("relaxing step", f"from {dt['start']} (95% profile {dt['lo']} to {dt['hi']}"
                                f"{'' if dt['contiguous'] else ', not contiguous'}), "
                                f"size {dt['step']:+.2f} m, e-fold {dt['tau']} months")

    if not args.no_fig:
        plot(res["comparison_window"], head); saved(OUT_53_FIG.name)

    rr = ReportNumbers()
    N = "E14, spec NRG_spec_E14_ccw_forest_side_drift_2026-10-25"
    rr.add("e14_n_wells", h["n_wells"], unit="wells", note=N)
    rr.add("e14_n_near", h["n_near"], unit="wells", note=f"within E14_NEAR_M of today's forest edge; {N}")
    rr.add("e14_n_far", h["n_far"], unit="wells", note=N)
    for b, tag in (("comparison_window", ""), ("full_record", "_full")):
        v = tt[b]
        rr.add(f"e14{tag}_rho", v["rho"], unit="rho", note=f"Spearman, distance to the forest edge against residual slope; {b}")
        rr.add(f"e14{tag}_p", v["p"], unit="p", note=f"one-sided exact permutation; {b}")
        rr.add(f"e14{tag}_near_median_slope", v["near_median_slope"], unit="m/yr", note=f"model - observed; {b}")
        rr.add(f"e14{tag}_far_median_slope", v["far_median_slope"], unit="m/yr", note=f"model - observed; {b}")
        rr.add(f"e14{tag}_diff", v["diff"], unit="m/yr", note=f"near minus far median slope; {b}")
        rr.add(f"e14{tag}_ci_lo", v["ci_lo"], unit="m/yr", note=f"bootstrap 95% lower; {b}")
        rr.add(f"e14{tag}_ci_hi", v["ci_hi"], unit="m/yr", note=f"bootstrap 95% upper; {b}")
    rr.add("e14_loo_ci_clear_n", n_clear, unit="count", note=f"of {len(loo)} single-well drops")
    rr.add("e14_test3", "pass" if test3 else "fail", unit="text", note=N)
    rr.add("e14_test4", "pass" if test4 else "fail", unit="text", note=N)
    rr.add("e14_verdict", verdict, unit="text", note=f"the rule fixed before the run; {N}")
    rr.add("e14_check_vs39_max_abs_diff", check_vs39, unit="m", note="headline basis against 39_02")
    if verdict != "not supported":
        rr.add("e14_step_start", dt["start"], unit="text", note="relaxing step on near minus far; reported, never judged")
        rr.add("e14_step_lo", dt["lo"], unit="text", note="95% profile interval, lower")
        rr.add("e14_step_hi", dt["hi"], unit="text", note="95% profile interval, upper")
        rr.add("e14_step_size", dt["step"], unit="m", note="full size of the relaxing step")
        rr.add("e14_step_tau", dt["tau"], unit="months", note="e-fold time")
    rr.save(OUT_53_REPORT_NUMBERS); saved(f"{OUT_53_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    done("53")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
