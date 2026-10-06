#!/usr/bin/env python3
"""
survey_round.py — the reduced field round (T-109)
=================================================

Martin, 2026-10-04: "is there a minimum number of wells that I could survey to keep the
survey going? ... we do need to keep an eye on the clearfell and scraping experiments ...
if I can keep the number down, I must make the round less than a 9-hour job".
2026-10-06: "Approved, but no report text" — so this is a TOOL, not a pipeline step: it
reads the committed outputs, writes to the private repository (working/fieldwork/), and
adds nothing to the published corpus or the pipeline's step count.

What it does
------------
1. Must-keep wells, from the pipeline's own lists (never typed here): every clearfell
   tier in utils.clearfell_common, the scraped wells and their controls in
   utils.scraping_common, and config.SURVEY_MUST_KEEP_EXTRA (CEH40-42).
2. Cluster cover. For each k = 5 cluster (02_cluster_stats.csv), the fewest extra
   reference wells, added greedily, whose mean holds the full cluster's monthly anomaly,
   trend and annual summer minimum within config.SURVEY_TOL_* on years the selection has
   not seen. The anomaly is each well's departure from its own training-period mean.
3. Stability: the selection is repeated for every split in config.SURVEY_SPLIT_ENDS;
   each well's selection frequency is reported. The round uses the primary split.
4. Coefficient recovery: Model A (utils.model_utils.fit_ssm) on the cluster-mean series
   of the reduced set against the full set; the difference in beta_1, beta_2, beta_3.
5. Route and time: the shortest open walking path (nearest neighbour + 2-opt, best start)
   through the round, and a time estimate calibrated on the full round:
      hours = path_km * SURVEY_PATH_FACTOR / SURVEY_WALK_KMH + n_wells * minutes_per_well / 60,
   with minutes_per_well solved from SURVEY_FULL_ROUND_HOURS over the wells read in the
   last twelve months of the record.

Outputs (working/fieldwork/, private repository):
    survey_round_wells.csv      the round in walking order: well, cluster, reason, frequency
    survey_round_clusters.csv   per cluster: wells, tolerances met, beta recovery
    survey_round_summary.txt    counts, distances, the time estimate
    survey_round_map.png        the wells and the route

Usage:
    python3 tools/survey_round.py            # from the repo root, in the built environment
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-10-06. T-109, design approved by Martin.

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import numpy as np
import pandas as pd

from utils import config as C
from utils.console_utils import banner, phase, info, saved, warn, result, track
from utils import clearfell_common as CF
from utils import scraping_common as SC
from utils.model_utils import fit_ssm

OUT = REPO / "working" / "fieldwork"
F_WELLS_REF = REPO / "outputs" / "01_wells_reference.csv"
F_WELLS_ALL = REPO / "outputs" / "01_wells_clean.csv"
F_CLUSTERS = REPO / "outputs" / "02_cluster_stats.csv"
F_LOC = REPO / "outputs" / "01_locations.csv"
F_CLIMATE = REPO / "outputs" / "01_climate.csv"
BETAS = ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage")


def must_keep() -> dict[str, str]:
    """well -> reason, from the analyses' own lists."""
    keep: dict[str, str] = {}
    for w in CF.IMPACT_WELLS:
        keep[w] = "clearfell: impact"
    for w in CF.EDGE_WELLS:
        keep.setdefault(w, "clearfell: edge")
    for w in CF.FOREST_CONTROL_WELLS:
        keep.setdefault(w, "clearfell: forest control")
    for w in CF.COASTAL_CONTROL_WELLS:
        keep.setdefault(w, "clearfell: coastal control")
    for w in CF.CLIMATE_CONTROL_WELLS:
        keep.setdefault(w, "clearfell: climate control")
    for w in getattr(CF, "FE_SYNTH_WELLS", ["fe1", "fe2"]):
        keep.setdefault(w.lower(), "clearfell: synthetic extension")
    for w in SC.IMPACT_WELLS:
        keep.setdefault(w, "scraping: scraped well")
    for w in SC.TIER1_WELLS:
        keep.setdefault(w, "scraping: paired control")
    for w in C.SURVEY_MUST_KEEP_EXTRA:
        keep.setdefault(w, "scraping: read since cut")
    return keep


def trend_mm_yr(s: pd.Series) -> float:
    s = s.dropna()
    t = (s.index - s.index[0]).days / 365.25
    return float(np.polyfit(t, s.values, 1)[0] * 1000)


def summer_min(s: pd.Series) -> pd.Series:
    s = s.dropna()
    s = s[s.index.month.isin(list(C.SUMMER_MINIMUM_MONTHS))]
    return s.groupby(s.index.year).min()


def cover(A: pd.DataFrame, wells: list[str], start: list[str], train, test):
    """Greedy cluster cover from `start`; returns (chosen, metrics)."""
    full = A[wells].mean(axis=1)

    def metrics(ch):
        sub = A[ch].mean(axis=1)
        e = (sub - full).loc[test]
        return (float(np.sqrt((e ** 2).mean()) * 1000),
                trend_mm_yr(sub.loc[test]) - trend_mm_yr(full.loc[test]),
                float((summer_min(sub.loc[test]) - summer_min(full.loc[test])).abs().mean() * 1000))

    def ok(m):
        return (m[0] <= C.SURVEY_TOL_RMSE_MM and abs(m[1]) <= C.SURVEY_TOL_TREND_MM_YR
                and m[2] <= C.SURVEY_TOL_SUMMER_MIN_MM)

    chosen = [w for w in start if w in wells]
    rest = [w for w in wells if w not in chosen]
    m = metrics(chosen) if chosen else (np.inf, np.inf, np.inf)
    while not ok(m) and rest:
        best = min(rest, key=lambda c: float(np.sqrt(((A[chosen + [c]].mean(axis=1) - full).loc[train] ** 2).mean())))
        chosen.append(best)
        rest.remove(best)
        m = metrics(chosen)
    return chosen, m, ok(m)


def route(names: list[str], loc: pd.DataFrame):
    """Shortest open path (nearest neighbour from every start, then 2-opt). km, order."""
    P = np.array([[loc.loc[n, "E"], loc.loc[n, "N"]] for n in names])
    n = len(P)
    D = np.hypot(P[:, None, 0] - P[None, :, 0], P[:, None, 1] - P[None, :, 1])
    best = (np.inf, None)
    for s in range(n):
        t = [s]
        left = set(range(n)) - {s}
        while left:
            j = min(left, key=lambda j: D[t[-1], j])
            t.append(j)
            left.remove(j)
        improved = True
        while improved:
            improved = False
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    a, b, c = t[i - 1], t[i], t[j]
                    d = t[j + 1] if j + 1 < n else None
                    old = D[a, b] + (D[c, d] if d is not None else 0)
                    new = D[a, c] + (D[b, d] if d is not None else 0)
                    if new < old - 1e-6:
                        t[i:j + 1] = t[i:j + 1][::-1]
                        improved = True
        L = sum(D[t[i], t[i + 1]] for i in range(n - 1))
        if L < best[0]:
            best = (L, t)
    return best[0] / 1000, [names[i] for i in best[1]]


def main() -> int:
    banner("survey_round", "the reduced field round (T-109)", __version__)
    OUT.mkdir(parents=True, exist_ok=True)

    ref = pd.read_csv(F_WELLS_REF, index_col=0, parse_dates=True)
    ref.columns = [c.lower() for c in ref.columns]
    allw = pd.read_csv(F_WELLS_ALL, index_col=0, parse_dates=True)
    allw.columns = [c.lower() for c in allw.columns]
    cs = pd.read_csv(F_CLUSTERS)
    cl = dict(zip(cs.Match_ID.str.lower(), cs.Cluster))
    lab = dict(zip(cs.Cluster, cs.Cluster_Label))
    loc = pd.read_csv(F_LOC)
    loc["k"] = loc.Name.str.lower()
    loc = loc.set_index("k")
    climate = pd.read_csv(F_CLIMATE, index_col=0, parse_dates=True)

    # The current round: wells read in the last twelve months of the record.
    last = allw.index.max()
    recent = [c for c in allw.columns if c in loc.index and c != "llyn rhos"
              and allw[c].loc[last - pd.DateOffset(months=12):].notna().any()]
    keep = must_keep()
    missing = [w for w in keep if w not in loc.index]
    if missing:
        warn(f"must-keep wells with no location (left out): {missing}")
    keep = {w: r for w, r in keep.items() if w in loc.index}
    phase(1, f"Must-keep: {len(keep)} wells from the experiment lists; current round {len(recent)} wells")

    # Cluster cover, every split.
    phase(2, "Cluster cover across the train/test splits")
    W = ref.loc[C.SURVEY_FIT_START:]
    freq: dict[str, int] = {}
    primary: dict[int, tuple] = {}
    for split in track(C.SURVEY_SPLIT_ENDS, label="splits", lines=True):
        train = slice(C.SURVEY_FIT_START, split)
        test = slice(pd.Timestamp(split) + pd.Timedelta(days=1), None)
        for k in sorted(set(cl.values())):
            wells = [c for c in W.columns if cl.get(c) == k
                     and W[c].loc[train].notna().sum() >= 60 and W[c].loc[test].notna().sum() >= 24]
            A = W[wells] - W[wells].loc[train].mean()
            chosen, m, ok = cover(A, wells, [w for w in keep if w in wells], train, test)
            for w in chosen:
                if w not in keep:
                    freq[w] = freq.get(w, 0) + 1
            if split == C.SURVEY_PRIMARY_SPLIT_END:
                primary[k] = (wells, chosen, m, ok)

    # Coefficient recovery (Model A) on the full-record cluster means.
    phase(3, "Coefficient recovery: reduced against full cluster means (Model A)")
    rows = []
    round_wells = dict(keep)
    for k, (wells, chosen, m, ok) in primary.items():
        for w in chosen:
            round_wells.setdefault(w, f"cluster cover: {lab[k]}")
        full_fit = fit_ssm(ref[wells].mean(axis=1), climate, drainage_datum=C.DRAINAGE_DATUM)
        red_fit = fit_ssm(ref[chosen].mean(axis=1), climate, drainage_datum=C.DRAINAGE_DATUM)
        row = {"cluster": lab[k], "wells_in_cluster": len(wells), "wells_in_round": len(chosen),
               "test_rmse_mm": m[0], "test_trend_err_mm_yr": m[1], "test_summer_min_err_mm": m[2],
               "tolerances_met": ok}
        for b in BETAS:
            f, r = full_fit.get(b) if full_fit else np.nan, red_fit.get(b) if red_fit else np.nan
            row[f"{b}_full"] = f
            row[f"{b}_round"] = r
            row[f"{b}_diff_pct"] = (r - f) / f * 100 if f else np.nan
        rows.append(row)
    clusters = pd.DataFrame(rows)
    clusters.to_csv(OUT / "survey_round_clusters.csv", index=False)
    saved("working/fieldwork/survey_round_clusters.csv")

    # Route and time.
    phase(4, "Route and time")
    names = [w for w in round_wells if w in loc.index]
    km_round, order = route(names, loc)
    km_full, _ = route(recent, loc)
    walk_full_h = km_full * C.SURVEY_PATH_FACTOR / C.SURVEY_WALK_KMH
    min_per_well = (C.SURVEY_FULL_ROUND_HOURS - walk_full_h) * 60 / len(recent)
    hours = km_round * C.SURVEY_PATH_FACTOR / C.SURVEY_WALK_KMH + len(names) * min_per_well / 60

    out = pd.DataFrame({"order": range(1, len(order) + 1), "well": [w.upper() for w in order],
                        "cluster": [lab.get(cl.get(w), "") for w in order],
                        "reason": [round_wells[w] for w in order],
                        "cover_selected_in_splits": [freq.get(w, "") for w in order]})
    out.to_csv(OUT / "survey_round_wells.csv", index=False)
    saved("working/fieldwork/survey_round_wells.csv")

    marginal = sorted(w for w, n in freq.items() if w in round_wells and n < len(C.SURVEY_SPLIT_ENDS))
    lines = [
        f"survey_round {__version__} — {pd.Timestamp.now():%Y-%m-%d %H:%M}",
        f"current round (read in the last 12 months to {last:%b %Y}): {len(recent)} wells, "
        f"straight-line route {km_full:.1f} km",
        f"calibration: {C.SURVEY_FULL_ROUND_HOURS:.1f} h for the full round; walking at "
        f"{C.SURVEY_WALK_KMH} km/h on {C.SURVEY_PATH_FACTOR}x the straight line = {walk_full_h:.1f} h; "
        f"{min_per_well:.1f} min per well",
        f"reduced round: {len(names)} wells ({len(keep)} must-keep + {len(names) - len(keep)} cluster cover), "
        f"straight-line route {km_round:.1f} km, estimated {hours:.1f} h "
        f"(limit {C.SURVEY_MAX_ROUND_HOURS:.0f} h: {'within' if hours <= C.SURVEY_MAX_ROUND_HOURS else 'OVER'})",
        f"cluster-cover wells not chosen in every split: {', '.join(w.upper() for w in marginal) or 'none'}",
        "",
        clusters[["cluster", "wells_in_cluster", "wells_in_round", "test_rmse_mm", "test_trend_err_mm_yr",
                  "test_summer_min_err_mm", "tolerances_met"]
                 + [f"{b}_diff_pct" for b in BETAS]].round(2).to_string(index=False),
    ]
    (OUT / "survey_round_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    saved("working/fieldwork/survey_round_summary.txt")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.scatter(loc.loc[recent, "E"], loc.loc[recent, "N"], s=10, c="0.75", label="current round, not kept")
        xy = np.array([[loc.loc[w, "E"], loc.loc[w, "N"]] for w in order])
        ax.plot(xy[:, 0], xy[:, 1], "-", c="0.4", lw=0.8)
        for i, w in enumerate(order):
            colour = "tab:red" if w in keep else "tab:blue"
            ax.scatter(*xy[i], s=28, c=colour, zorder=3)
            ax.annotate(f"{i + 1} {w.upper()}", xy[i], fontsize=6, xytext=(3, 3), textcoords="offset points")
        ax.scatter([], [], c="tab:red", s=28, label="experiment wells")
        ax.scatter([], [], c="tab:blue", s=28, label="cluster cover")
        ax.set_aspect("equal")
        ax.set_title(f"Reduced round: {len(names)} wells, ~{hours:.1f} h")
        ax.legend(fontsize=7, loc="lower left")
        fig.savefig(OUT / "survey_round_map.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        saved("working/fieldwork/survey_round_map.png")
    except Exception as e:  # the map is a convenience; the list is the deliverable
        warn(f"map not drawn: {e}")

    result("round", f"{len(names)} wells, {km_round:.1f} km straight-line, ~{hours:.1f} h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
