#!/usr/bin/env python3
"""
54_dry_year_hysteresis.py — does a dry year prime the warren? The 2006-08 excess as hysteresis (E15)

QUESTION
  The water table of 2006-08 stood above the free-running climate model at C2-C5, and no forcing-side
  cause tested so far accounts for it: a second store (E8), a dated change (E8b), a high-water
  threshold (E8c), long rain events (E8d), other evaporation estimates and a beta_1 break (E13).
  Wetter and more drawn-out winters later (2015/16, 2020/21) left no such lump. What still separates
  2006-07 is the year before it: 2005 is among the driest in the RAF Valley record. If a wet spell on a
  dried warren raises the water table more than the same wetness on an ordinary one, the lump should
  recur after the record's other dry-to-wet sequences, and not after ordinary wet years.

METHOD (spec NRG_spec_E15_dry_year_hysteresis_2026-10-25, approved Martin 07:41)
  Hydrological years (Oct-Sep, complete only) are ranked by P - PET over the whole committed climate
  record. A dry-to-wet sequence is a year at or below E15_DRY_PCTL followed within E15_LAG_YEARS by one
  at or above E15_WET_PCTL; a control is a wet year whose two preceding years are both above
  E15_DRY_PCTL. Both lists come from the climate alone.
  The response model is E13's (Script 50): per cluster, the member-mean centroid of the reference and
  extended wells; Model A fitted on its full record; free run from the first month after the climate
  record's last gap, from the record's mean level. Residual = observed - model. Checked to reproduce
  50_report_numbers e13_excess_thornthwaite_full_C* before anything is judged.
  Each window is the E15_WINDOW_MONTHS from the October that opens its first wet year; its response is
  its mean residual minus the mean over every month in no window; it is scored where the centroid has at
  least E15_MIN_WINDOW_COVER of the window.
    Test 1   a later sequence replicates if its response is positive and at least E15_SHARE of the
             2005 sequence's at E15_MIN_CLUSTERS or more of E15_CLUSTERS_JUDGED
    Test 2   the median response over the sequences exceeds the median over the controls at
             E15_MIN_CLUSTERS or more of E15_CLUSTERS_JUDGED
    Verdict  supported (both later sequences replicate, test 2) | partial (one, test 2) | not supported
  C1, which has no excess, is reported and not judged.

OUTPUTS (outputs/54_dry_year_hysteresis/)
  54_01_hydrological_years.csv     every complete hydrological year: P, PET, P - PET, percentile, role
  54_02_windows.csv                each sequence and control: years, window, overlap flags
  54_03_responses_by_cluster.csv   window x cluster: coverage, mean residual, response, scored
  54_04_tests.csv                  per cluster: test 1 per later sequence, test 2
  54_05_residual_monthly.csv       month x cluster residual (observed - model)
  54_06_dry_year_hysteresis.png    residual by cluster with the windows shaded
  54_report_numbers.csv            e15_*

Run directly:  python3 src/54_dry_year_hysteresis.py [--no-fig]
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-25. First issue (E15; Martin 07:38 "what you're talking
#   about is hysteresis here, the 2005 exceptional dry year. Is there a way of testing this?", 07:41 "let's
#   have it as its own script"). Moves into Script 52 when the Script 50 split lands.

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.paths import (                                     # noqa: E402
    DIR_54, OUT_54_YEARS, OUT_54_WINDOWS, OUT_54_RESPONSES, OUT_54_TESTS, OUT_54_RESIDUALS, OUT_54_FIG,
    OUT_54_REPORT_NUMBERS, INT_CLIMATE, INT_MASTER_DATA, INT_WELLS_REFERENCE, INT_WELLS_EXTENDED,
    OUT_50_REPORT_NUMBERS,
)
from utils.config import (                                    # noqa: E402
    E15_DRY_PCTL, E15_WET_PCTL, E15_LAG_YEARS, E15_WINDOW_MONTHS, E15_SHARE, E15_MIN_WINDOW_COVER,
    E15_CLUSTERS_JUDGED, E15_MIN_CLUSTERS, TWO_STORE_EARLY_YEARS, E8E_LATER_YEARS, E13_CLUSTERS,
)
from utils.data_utils import normalize_well_name              # noqa: E402
from utils.model_utils import fit_ssm, simulate_ssm           # noqa: E402
from utils.pastas_utils import continuous_start               # noqa: E402
from utils.console_utils import banner, phase, step, info, warn, saved, note, result, done  # noqa: E402
from utils.render_utils import MPL_DEFAULTS                   # noqa: E402
from utils.report_numbers_utils import ReportNumbers          # noqa: E402


# ── the climate side: which years are dry, wet, sequences and controls ────────────────────────────────
def hydrological_years(cl: pd.DataFrame) -> pd.DataFrame:
    c = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    hy = c.index.year + (c.index.month >= 10)
    g = c.groupby(hy).agg(P_m=("P_m", "sum"), PET=("PET", "sum"), n=("P_m", "size"))
    g = g[g["n"] == 12].drop(columns="n")
    g["W"] = g["P_m"] - g["PET"]
    g["pct"] = g["W"].rank(pct=True) * 100
    g["dry"] = g["pct"] <= E15_DRY_PCTL
    g["wet"] = g["pct"] >= E15_WET_PCTL
    g.index.name = "hydrological_year"
    return g


def windows(years: pd.DataFrame) -> pd.DataFrame:
    rows, seen = [], set()
    for y in years.index[years["dry"]]:
        wets = [z for z in range(y + 1, y + 1 + E15_LAG_YEARS) if z in years.index and years.loc[z, "wet"]]
        if wets and wets[0] not in seen:
            seen.update(wets)
            rows.append(dict(kind="sequence", dry_year=y, wet_years=" ".join(map(str, wets)), first_wet=wets[0]))
    for z in years.index[years["wet"]]:
        prev = [z - 1, z - 2]
        if all(p in years.index for p in prev) and all(not years.loc[p, "dry"] for p in prev):
            rows.append(dict(kind="control", dry_year=np.nan, wet_years=str(z), first_wet=z))
    w = pd.DataFrame(rows)
    w["start"] = [pd.Timestamp(f"{y - 1}-10-01") for y in w["first_wet"]]
    w["end"] = [s + pd.DateOffset(months=E15_WINDOW_MONTHS - 1) for s in w["start"]]
    w["label"] = [(f"{int(d)}→{ws.replace(' ', ',')}" if k == "sequence" else f"control {ws}")
                  for k, d, ws in zip(w["kind"], w["dry_year"], w["wet_years"])]
    return w.sort_values("start").reset_index(drop=True)


# ── the response side: E13's free-running single store per cluster ────────────────────────────────────
def residuals(cl: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    c0 = continuous_start(cl)
    clim = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").loc[c0:].dropna()
    W = pd.concat([pd.read_csv(INT_WELLS_REFERENCE, index_col=0, parse_dates=True),
                   pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)], axis=1)
    W.columns = [normalize_well_name(x) for x in W.columns]
    md = pd.read_csv(INT_MASTER_DATA)
    md["_n"] = md["Name_Original"].astype(str).apply(normalize_well_name)
    md = md.set_index("_n")
    out, fits = {}, {}
    for k in sorted(md["Cluster"].unique()):
        h = W[[w for w in md.index[md["Cluster"] == k] if w in W]].mean(axis=1).loc[:clim.index[-1]]
        f = fit_ssm(h, clim, intercept=False)
        s = pd.Series(simulate_ssm(h.dropna().mean(), clim["P_m"].values, clim["PET"].values,
                                   f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"],
                                   alpha=0.0), index=clim.index)
        out[f"C{int(k)}"] = (h - s)
        fits[f"C{int(k)}"] = f
    return pd.DataFrame(out), fits


def e13_check(res: pd.DataFrame) -> float:
    """Largest |difference| from the committed E13 excess (Thornthwaite, full span, Model A)."""
    rn = pd.read_csv(OUT_50_REPORT_NUMBERS).set_index("Parameter")["Value"]
    e = (f"{TWO_STORE_EARLY_YEARS[0]}-01-01", f"{TWO_STORE_EARLY_YEARS[1]}-12-01")
    l_ = (f"{E8E_LATER_YEARS[0]}-01-01", f"{E8E_LATER_YEARS[1]}-12-01")
    diffs = []
    for k in E13_CLUSTERS:
        r = res[f"C{k}"].dropna()
        mine = float(r.loc[e[0]:e[1]].mean() - r.loc[l_[0]:l_[1]].mean())
        diffs.append(abs(mine - float(rn[f"e13_excess_thornthwaite_full_C{k}"])))
    return max(diffs)


def responses(res: pd.DataFrame, win: pd.DataFrame) -> pd.DataFrame:
    in_any = pd.Series(False, index=res.index)
    for w in win.itertuples():
        in_any |= (res.index >= w.start) & (res.index <= w.end)
    rows = []
    for c in res.columns:
        r = res[c]
        base = float(r[~in_any].dropna().mean())
        for w in win.itertuples():
            seg = r.loc[w.start:w.end]
            cover = float(seg.notna().sum()) / E15_WINDOW_MONTHS
            mean = float(seg.mean()) if seg.notna().any() else np.nan
            rows.append(dict(label=w.label, kind=w.kind, cluster=c, start=w.start.strftime("%Y-%m"),
                             end=w.end.strftime("%Y-%m"), cover=cover, mean_residual_m=mean,
                             baseline_m=base, response_m=mean - base,
                             scored=bool(cover >= E15_MIN_WINDOW_COVER)))
    return pd.DataFrame(rows)


def judge(resp: pd.DataFrame, win: pd.DataFrame):
    sc = resp[resp["scored"]]
    seqs = win[win["kind"] == "sequence"]
    seqs = seqs[seqs["label"].isin(sc["label"])]
    if seqs.empty or not (seqs["dry_year"] == 2005).any():
        raise RuntimeError("the 2005 sequence is not scored: nothing to replicate")
    ref = seqs[seqs["dry_year"] == 2005]["label"].iloc[0]
    later = [l_ for l_ in seqs["label"] if l_ != ref]
    rows, rep = [], {}
    for k in E15_CLUSTERS_JUDGED:
        c = f"C{k}"
        s = sc[sc["cluster"] == c].set_index("label")["response_m"]
        row = dict(cluster=c, ref_response_m=s.get(ref, np.nan))
        for l_ in later:
            v = s.get(l_, np.nan)
            row[f"{l_} response_m"] = v
            row[f"{l_} share"] = v / row["ref_response_m"] if row["ref_response_m"] else np.nan
            ok = bool(np.isfinite(v) and v > 0 and row["ref_response_m"] > 0
                      and v >= E15_SHARE * row["ref_response_m"])
            row[f"{l_} replicates"] = ok
        seq_med = float(s.reindex(seqs["label"]).median())
        ctl = sc[(sc["cluster"] == c) & (sc["kind"] == "control")]["response_m"]
        row.update(seq_median_m=seq_med, control_median_m=float(ctl.median()) if len(ctl) else np.nan,
                   n_controls=int(len(ctl)))
        row["test2_pass"] = bool(np.isfinite(row["control_median_m"]) and seq_med > row["control_median_m"])
        rows.append(row)
    t = pd.DataFrame(rows)
    for l_ in later:
        rep[l_] = int(t[f"{l_} replicates"].sum()) >= E15_MIN_CLUSTERS
    test2 = int(t["test2_pass"].sum()) >= E15_MIN_CLUSTERS
    n_rep = sum(rep.values())
    if test2 and len(later) >= 2 and n_rep == len(later):
        verdict = "supported"
    elif test2 and n_rep >= 1:
        verdict = "partial"
    else:
        verdict = "not supported"
    return t, ref, later, rep, test2, verdict


def plot(res: pd.DataFrame, win: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    r = res.loc["2004-01-01":]
    fig, axes = plt.subplots(len(r.columns), 1, figsize=(11, 1.6 * len(r.columns)), dpi=160, sharex=True)
    for a, c in zip(axes, r.columns):
        for w in win.itertuples():
            if w.end < r.index[0]:
                continue
            a.axvspan(w.start, w.end, color="#b2182b" if w.kind == "sequence" else "#2166ac", alpha=0.12, lw=0)
        a.plot(r.index, r[c], color="0.2", lw=0.8)
        a.axhline(0, color="0.5", lw=0.5)
        a.set_ylabel(c, rotation=0, ha="right", va="center")
    axes[0].set_title("Residual (observed − model, m): red = after a dry year, blue = control wet years", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_54_FIG)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fig", action="store_true")
    args = ap.parse_args()
    banner("54", "Does a dry year prime the warren? (E15)", version=__version__)
    DIR_54.mkdir(parents=True, exist_ok=True)

    phase(1, "Hydrological years, sequences and controls (climate only)")
    cl = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    years = hydrological_years(cl)
    win = windows(years)
    years["role"] = ""
    for w in win.itertuples():
        for y in map(int, w.wet_years.split()):
            years.loc[y, "role"] = "sequence wet" if w.kind == "sequence" else "control"
        if w.kind == "sequence":
            years.loc[int(w.dry_year), "role"] = "sequence dry"
    years.to_csv(OUT_54_YEARS); saved(OUT_54_YEARS.name)
    info(f"{len(years)} complete hydrological years, {years.index.min()}-{years.index.max()}")

    phase(2, "Residuals of the E13 single store")
    res, fits = residuals(cl)
    chk = e13_check(res)
    result("max |excess - committed e13_excess_thornthwaite_full| (m)", f"{chk:.2e}")
    if chk > 1e-6:
        warn("does not reproduce E13 — nothing judged")
        return 1
    res.to_csv(OUT_54_RESIDUALS, index_label="month"); saved(OUT_54_RESIDUALS.name)
    first = res.dropna(how="all").index.min()
    win["in_record"] = win["start"] >= first - pd.DateOffset(months=6)
    for w in win.itertuples():
        overl = [o.label for o in win.itertuples() if o.label != w.label and o.start <= w.end and o.end >= w.start]
        win.loc[w.Index, "overlaps"] = "; ".join(overl)
    win.to_csv(OUT_54_WINDOWS, index=False); saved(OUT_54_WINDOWS.name)
    for w in win[win["start"] >= pd.Timestamp("2000-01-01")].itertuples():
        step(f"{w.label:18s} {w.start:%Y-%m} to {w.end:%Y-%m}"
             + (f"  (overlaps {w.overlaps})" if w.overlaps else ""))

    phase(3, "Responses and the rule")
    resp = responses(res, win)
    resp.to_csv(OUT_54_RESPONSES, index=False); saved(OUT_54_RESPONSES.name)
    t, ref, later, rep, test2, verdict = judge(resp, win)
    t.to_csv(OUT_54_TESTS, index=False); saved(OUT_54_TESTS.name)
    for r in resp[resp["scored"]].sort_values(["cluster", "start"]).itertuples():
        step(f"{r.cluster}  {r.label:18s} response {r.response_m:+.3f} m  (cover {r.cover:.2f})")
    for l_ in later:
        result(f"test 1, {l_}", f"{'replicates' if rep[l_] else 'does not replicate'} "
                                f"({int(t[f'{l_} replicates'].sum())} of {len(t)} clusters)")
    result("test 2 (sequences above controls)", f"{'pass' if test2 else 'FAIL'} ({int(t['test2_pass'].sum())} of {len(t)})")
    result("E15 verdict", verdict)
    unscored = resp[~resp["scored"] & resp["kind"].eq("sequence") & resp["start"].ge("2000-01")]["label"].unique()
    if len(unscored):
        note(f"not scored for want of cover at some clusters: {', '.join(unscored)}")

    if not args.no_fig:
        plot(res, win); saved(OUT_54_FIG.name)

    rr = ReportNumbers()
    N = "E15, spec NRG_spec_E15_dry_year_hysteresis_2026-10-25"
    rr.add("e15_check_vs_e13_max_abs_diff", chk, unit="m", note="the 2006-08 excess reproduced against 50_report_numbers")
    rr.add("e15_n_sequences_scored", int(len([l_ for l_ in [ref] + later])), unit="count", note=N)
    rr.add("e15_n_controls", int((win["kind"] == "control").sum()), unit="count",
           note="control wet years in the whole climate record (scored only where the record covers them)")
    rr.add("e15_later_sequences", "; ".join(later), unit="text", note=N)
    rr.add("e15_controls_scored", "; ".join(sorted(resp[resp["scored"] & (resp["kind"] == "control")]["label"].unique())),
           unit="text", note=N)
    for r in resp[resp["scored"]].itertuples():
        key = r.label.replace("→", "_to_").replace(",", "_").replace("control ", "control_")
        rr.add(f"e15_response_{key}_{r.cluster}", r.response_m, unit="m", note=f"{r.start} to {r.end}; {N}")
    for l_ in later:
        key = l_.replace("→", "_to_").replace(",", "_")
        rr.add(f"e15_replicates_{key}", "yes" if rep[l_] else "no", unit="text",
               note=f"{int(t[f'{l_} replicates'].sum())} of {len(t)} clusters; needs {E15_MIN_CLUSTERS}")
    rr.add("e15_test2", "pass" if test2 else "fail", unit="text", note=f"{int(t['test2_pass'].sum())} of {len(t)} clusters")
    rr.add("e15_verdict", verdict, unit="text", note=f"the rule fixed before the run; {N}")
    rr.save(OUT_54_REPORT_NUMBERS); saved(f"{OUT_54_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    done("54")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
