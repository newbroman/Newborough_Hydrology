"""
14b_year_of_crossing.py — Bootstrap year-of-crossing for the per-cluster
annual mean spring level (MSL) against the handbook's community MSL levels.
Context only (D-296, D-349 (14)).

3.2.0 (D-349 (14), B12; Martin, 2026-11-27): the year of crossing is computed
on the MEAN SPRING LEVEL from January 2010 (D-347's window, config.RECORD_FIT_START),
not on the summer minimum from 2005. The summer-minimum crossing years were the
2005-09 high stand: from 2011 every summer slope is non-significant (14's robust
column), and D-347 (4) makes the mean spring level Paper 1's long-term change.
Every cluster's spring level has risen since 2010, though not significantly, so the
expected result is "no crossing".

Procedure:
1. Load Script 14's per-cluster annual mean spring level (`14_annual_extremes.csv`,
   Season "Spring_Mean", the fixed-effects cluster series; Script 14 1.17.0), years
   from RECORD_FIT_START's year.
2. For each cluster: fit a linear trend (level = a + b·year).
3. Bootstrap by resampling years with replacement (n = 1000); for each resample
   refit the trend and classify it against each threshold: "crosses" (in a year
   after the last observed year, up to YEAR_CAP), "already beyond" (the fitted level
   at the last observed year is already past the threshold), "no crossing" (the
   level is not falling) or "beyond horizon" (falling, but past YEAR_CAP). The
   2080 sentinel of 3.1.0 read "already beyond" as "never"; the states replace it.
4. Tabulate the point-estimate state and, over the resamples that cross, the
   5th / 50th / 95th percentile crossing years, beside the share of resamples in
   each state.

Thresholds are the handbook's mean spring levels of the two slack communities
(config.HB_SD15b_MSL, HB_SD16_MSL; Denning et al. 2024 Table 2), the levels drawn
on spring-level series. They are COMMUNITY levels: D-296 keeps them out of tests
without a surveyed floor, so this table is reported as context, never as a test,
and is run on demand only.

Limitations:
- Linear extrapolation is fragile beyond the observed window, and the bootstrap
  captures sampling uncertainty only, not model-form uncertainty.
- The cluster series averages wells of different ground elevation, so the threshold
  is an effective one against the cluster series, not against any well.
"""

from __future__ import annotations

__version__ = "3.2.0"  # 2026-11-27 (D-349 (14), B12; A14): the year of crossing is on the mean spring level from RECORD_FIT_START (Script 14 1.17.0's Spring_Mean rows), against the handbook's community MSL levels (HB_SD15b_MSL, HB_SD16_MSL), labelled context (D-296); explicit states ("crosses", "already beyond", "no crossing", "beyond horizon") replace the 2080 sentinel, which read a cluster already past a threshold as "never"; every sentence of the memo is generated from the table and Script 14's spring trend table. Was "3.1.0"  # 2026-11-27 (D-348): the memo names C3f (key C5) and C3o; the hard-coded steepest-decline sentence is marked as a k = 5 statement to check. Was "3.0.0"  # Hollingham (2026) - 2026-11-03 (D-296 retirement pass; Martin 2026-11-03 "b"). On demand only
#   (run_analysis 2.29.0, `--step 14b`); withdrawn from the report. The 1.2.1 cluster bootstrap is restored, unchanged,
#   so the step that stays registered still runs: 2.0.0 (D-294, per-well crossing counts) read
#   14_per_well_extremes.csv, which Script 14 1.14.0 no longer writes, and is retired with it. Its outputs
#   (14b_year_of_crossing.csv, .png, _results.md) are written only when the step is asked for and are not committed.
# 2.0.0  # Hollingham (2026) - 2026-11-01 (D-294): per-well crossing counts (retired 2026-11-03).
# 1.2.1  # Hollingham (2026) - 2026-09-28. Text only: the crossing-year conclusion is now §7 Conclusion 13 (was 11).
# 1.2.0  # Hollingham (2026) — 2026-05-29
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ── Pipeline imports ──────────────────────────────────────────────────────
def main():
    _HERE = Path(__file__).resolve().parent
    REPO = _HERE.parent
    sys.path.insert(0, str(_HERE))

    from utils.console_utils import (
        banner, phase, step, info, saved, warn, error, note, done, result,
        hr, skipped,
    )
    from utils import paths  # noqa: E402
    from utils.config import (  # noqa: E402
        CLUSTER_LABELS, CLUSTER_COLOURS,
        get_cluster_colour, BW_MODE,
        HB_SD15b_MSL, HB_SD16_MSL, HB_SOURCE,
        RECORD_FIT_START, MSL_SPRING_MONTHS,
    )
    from scipy import stats
    from utils.render_utils import render_figure

    paths.make_all_dirs()

    # Script 14's annual table; its Spring_Mean rows are the fixed-effects mean spring level (Script 14 1.17.0)
    F_ANNUAL  = paths.OUT_14_ANNUAL_EXTREMES
    F_SPRING_TREND = paths.OUT_14_SPRING_TREND_CSV

    # Outputs — canonical OUT_14B_* constants in paths.py (share Script 14's
    # directory). Single source of truth.
    OUT_CSV   = paths.OUT_14B_CROSSING_CSV
    OUT_FIG   = paths.OUT_14B_CROSSING_FIG
    OUT_MEMO  = paths.OUT_14B_RESULTS_MEMO

    # The handbook's community mean spring levels (config; positive = below ground), signed to the data
    # convention (negative below ground). Community levels: context only (D-296).
    THRESHOLDS = {
        "SD15b": -HB_SD15b_MSL,
        "SD16":  -HB_SD16_MSL,
    }
    FIT_START = pd.Timestamp(RECORD_FIT_START).year   # D-347
    YEAR_CAP = 2080                                    # the projection horizon; a state, not a sentinel value
    N_BOOT  = 1000
    RNG     = np.random.default_rng(20260529)
    _SPRING = "-".join(pd.Timestamp(2000, m + 1, 1).strftime("%b") for m in (MSL_SPRING_MONTHS[0], MSL_SPRING_MONTHS[-1]))

    # ── Procedure ─────────────────────────────────────────────────────────────

    print("─" * 72)
    print(f"14b — Bootstrap year-of-crossing for the per-cluster mean spring level, from {FIT_START} (context)")
    print("─" * 72)

    ann = pd.read_csv(F_ANNUAL)
    sm  = ann[(ann["Season"] == "Spring_Mean") & (pd.to_numeric(ann["HydroYear"], errors="coerce") >= FIT_START)].copy()
    if sm.empty:
        error(f"{F_ANNUAL.name} has no Spring_Mean rows from {FIT_START}: run Script 14 (1.17.0 or later) first")
        return
    print(f"Loaded {len(sm)} spring-mean rows across {sm['Cluster'].nunique()} clusters, {FIT_START} on")

    def crossing_state(year_arr, depth_arr, threshold_val, b=None, a=None):
        """(state, year) for a linear fit y = a + b·x against threshold_val (levels negative below ground).

        "already beyond": the fitted level at the last observed year is at or past the threshold;
        "no crossing":    the level is not falling (b >= 0) and is above the threshold;
        "crosses":        falling, crossing after the last observed year and by YEAR_CAP (year returned);
        "beyond horizon": falling, crossing after YEAR_CAP;
        "no fit":         too few distinct years, or the fit failed."""
        if b is None:
            if len(np.unique(year_arr)) < 3:
                return "no fit", np.nan
            try:
                b, a = np.polyfit(year_arr, depth_arr, deg=1)
            except (np.linalg.LinAlgError, ValueError):
                return "no fit", np.nan
        last = float(np.max(year_arr))
        if a + b * last <= threshold_val:
            return "already beyond", np.nan
        if b >= 0:
            return "no crossing", np.nan
        yr = (threshold_val - a) / b
        return ("crosses", float(yr)) if yr <= YEAR_CAP else ("beyond horizon", np.nan)

    STATES = ("crosses", "already beyond", "no crossing", "beyond horizon")
    rows = []
    boot_traces = {}  # for figure

    for cluster in sorted(sm["Cluster"].unique()):
        sub = sm[sm["Cluster"] == cluster].dropna(subset=["Value_m", "HydroYear"])
        sub = sub.sort_values("HydroYear")
        years  = sub["HydroYear"].astype(float).values
        depths = sub["Value_m"].astype(float).values
        n_yr   = len(years)

        if n_yr < 5:
            print(f"{cluster}: only {n_yr} years — skipping")
            continue

        # Point-estimate fit on the series from FIT_START
        lr = stats.linregress(years, depths)
        b_pt, a_pt = float(lr.slope), float(lr.intercept)

        # Bootstrap: resample years with replacement
        boot_state = {name: [] for name in THRESHOLDS}
        boot_yc = {name: [] for name in THRESHOLDS}
        boot_b  = np.full(N_BOOT, np.nan)
        boot_a  = np.full(N_BOOT, np.nan)
        for k in range(N_BOOT):
            idx = RNG.integers(0, n_yr, size=n_yr)
            if len(np.unique(years[idx])) < 3:     # pathological resample (rare)
                continue
            try:
                b_k, a_k = np.polyfit(years[idx], depths[idx], 1)
            except (np.linalg.LinAlgError, ValueError):
                continue
            boot_b[k] = b_k
            boot_a[k] = a_k
            for name, tval in THRESHOLDS.items():
                st, yc = crossing_state(years, depths, tval, b=b_k, a=a_k)
                boot_state[name].append(st)
                if st == "crosses":
                    boot_yc[name].append(yc)

        boot_traces[cluster] = {
            "years": years, "depths": depths,
            "a_pt": a_pt, "b_pt": b_pt,
            "boot_a": boot_a[~np.isnan(boot_a)],
            "boot_b": boot_b[~np.isnan(boot_b)],
        }

        for tname, tval in THRESHOLDS.items():
            st_pt, yc_pt = crossing_state(years, depths, tval, b=b_pt, a=a_pt)
            yc_boot = np.asarray(boot_yc[tname], float)
            n_res = len(boot_state[tname])
            pcts = np.percentile(yc_boot, [5, 50, 95]) if len(yc_boot) else [np.nan] * 3
            row = {
                "Cluster":           cluster,
                "Cluster_ID":        int(str(cluster)[1:]),    # the "C{id}" key Script 14 writes
                "Threshold":         tname,
                "Threshold_m":       tval,
                "threshold_source":  "handbook community mean spring level (context only, D-296)",
                "fit_start":         FIT_START,
                "n_years_obs":       n_yr,
                "slope_pt_m_per_yr": b_pt,
                "slope_pt_p":        float(lr.pvalue),
                "intercept_pt":      a_pt,
                "level_fit_last_year": a_pt + b_pt * float(years.max()),
                "last_year":         int(years.max()),
                "state_pt":          st_pt,
                "year_crossing_pt":  yc_pt,
                "year_crossing_5":   pcts[0],
                "year_crossing_50":  pcts[1],
                "year_crossing_95":  pcts[2],
                "n_boot_resolved":   n_res,
            }
            for stn in STATES:
                row[f"share_boot_{stn.replace(' ', '_')}"] = (boot_state[tname].count(stn) / n_res) if n_res else np.nan
            rows.append(row)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV.relative_to(REPO)}")

    # ── Console summary ───────────────────────────────────────────────────────
    print()
    print("─── Year of crossing on the mean spring level (context only) ───")
    print(f"{'Cluster':6} {'Threshold':10} {'slope (mm/yr)':>15} {'state':>16} {'crossing yr (5–50–95)':>26}")
    print("-" * 78)
    for _, r in out.iterrows():
        rng = ("—" if pd.isna(r['year_crossing_50'])
               else f"{r['year_crossing_5']:>5.0f} – {r['year_crossing_50']:>5.0f} – {r['year_crossing_95']:>5.0f}")
        slp = r['slope_pt_m_per_yr'] * 1000  # mm/yr
        print(f"{r['Cluster']:6} {r['Threshold']:10} {slp:>+15.2f} {r['state_pt']:>16} {rng:>26}")

    # ── Figure: 3-over-2 stacked per-cluster panels ───────────────────────────
    from matplotlib.lines import Line2D     # noqa: E402
    from matplotlib.patches import Patch    # noqa: E402

    clusters_sorted = sorted(boot_traces.keys())
    x_proj = np.arange(FIT_START, 2061)

    # 2 rows × 3 cols, filled row-major: C1/C2/C3o on top, C4/C3f on the bottom (D-348; keys C1..C5).
    # The sixth cell (bottom-right) is reserved for a shared legend.
    fig, axgrid = plt.subplots(2, 3, figsize=(15, 9), sharey=True,
                               facecolor="white")
    axes_flat = axgrid.flatten()
    left_col_axes = {axgrid[0, 0], axgrid[1, 0]}  # only these show the y-axis label

    for i, cluster in enumerate(clusters_sorted):
        ax = axes_flat[i]
        trace = boot_traces[cluster]
        cnum = int(cluster.replace("C", "")) if cluster.startswith("C") else None
        col  = get_cluster_colour(cnum) if cnum is not None else "#444"
        label = CLUSTER_LABELS.get(cnum, cluster)

        # Observed
        ax.scatter(trace["years"], trace["depths"], s=26,
                    color=col, alpha=0.85, edgecolor="white", linewidth=0.5,
                    label="Observed", zorder=3)
        # Point-estimate trend
        y_pt = trace["a_pt"] + trace["b_pt"] * x_proj
        ax.plot(x_proj, y_pt, color=col, linewidth=2.0, zorder=2,
                 label="OLS trend")
        # 5-95 % bootstrap band (a 90 % interval; 3.2.0 names it so)
        boot_pred = np.array([
            trace["boot_a"][j] + trace["boot_b"][j] * x_proj
            for j in range(min(len(trace["boot_a"]), len(trace["boot_b"])))
        ])
        if len(boot_pred) > 0:
            lo = np.percentile(boot_pred, 5, axis=0)
            hi = np.percentile(boot_pred, 95, axis=0)
            ax.fill_between(x_proj, lo, hi, color=col, alpha=0.18,
                             linewidth=0, label="5–95% band", zorder=1)

        # Threshold lines — labelled inside the panel (right edge) so the text
        # does not spill into the adjacent panel of the grid.
        for tname, tval in THRESHOLDS.items():
            ax.axhline(tval, color="black", linewidth=0.7, linestyle="--", alpha=0.7)
            ax.text(2059, tval, tname, fontsize=8, va="bottom", ha="right",
                     color="#333")

        # Crossing-year median + 5–95 band from the table
        sub_rows = out[out["Cluster"] == cluster]
        for _, r in sub_rows.iterrows():
            if r["state_pt"] == "crosses" and pd.notna(r["year_crossing_50"]) and r["year_crossing_50"] < 2061:
                ax.axvspan(r["year_crossing_5"], r["year_crossing_95"],
                            alpha=0.15, color="black", linewidth=0)
                ax.axvline(r["year_crossing_50"], color="black",
                            linewidth=0.8, alpha=0.6)

        ax.set_title(label, fontsize=11, fontweight="bold", pad=8)
        ax.set_xlabel("Year")
        ax.set_xlim(FIT_START, 2060)
        ax.grid(alpha=0.3, linewidth=0.4)
        if ax in left_col_axes:
            ax.set_ylabel(f"Mean spring level ({_SPRING})\n(m, negative below ground)")
        else:
            ax.tick_params(labelleft=False)

    # Hide any unused panels (the sixth cell) and host the shared legend there.
    for ax in axes_flat[len(clusters_sorted):]:
        ax.axis("off")

    legend_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#666",
               markeredgecolor="white", markersize=8,
               label="Observed annual mean spring level"),
        Line2D([0], [0], color="#444", linewidth=2.0,
               label="OLS trend (point estimate)"),
        Patch(facecolor="#888", alpha=0.18, label="5–95% bootstrap band"),
        Line2D([0], [0], color="black", linewidth=0.8, linestyle="--",
               label="Handbook community MSL (context)"),
        Patch(facecolor="black", alpha=0.15, label="Crossing-year 5–95% band"),
        Line2D([0], [0], color="black", linewidth=0.8, alpha=0.6,
               label="Crossing-year median"),
    ]
    legend_host = axes_flat[-1]  # the hidden sixth cell
    legend_host.legend(handles=legend_handles, loc="center", fontsize=9,
                       framealpha=0.95, title="Legend", title_fontsize=10)

    fig.suptitle(f"Bootstrap year-of-crossing for the per-cluster mean spring level from {FIT_START} "
                 "against the handbook's community levels (context only, D-296)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    render_figure(fig, OUT_FIG, facecolor="white")
    print(f"\nWrote {OUT_FIG.relative_to(REPO)}")


    # ── Memo ──────────────────────────────────────────────────────────────────
    # 3.2.0 (D-349 (14), A14): every sentence below is generated from `out` and Script 14's spring trend table.
    def _lab(c):
        return CLUSTER_LABELS.get(int(str(c)[1:]), str(c))

    def _rng(r):
        if r["state_pt"] != "crosses" or pd.isna(r["year_crossing_50"]):
            return "—"
        return f"{r['year_crossing_5']:.0f} — {r['year_crossing_50']:.0f} — {r['year_crossing_95']:.0f}"

    memo_lines = ["# Bootstrap year-of-crossing on the mean spring level — results\n",
                  "",
                  f"*Diagnostic from `14b_year_of_crossing.py` {__version__}, run on demand. CONTEXT, not a test: the "
                  "thresholds are community levels, which D-296 keeps out of tests without a surveyed floor "
                  "(D-349 (14)).*",
                  "",
                  f"- Series: the annual mean spring level ({_SPRING}) of each cluster's fixed-effects series "
                  f"(Script 14), {FIT_START} on (D-347).",
                  f"- Thresholds: {HB_SOURCE}, mean spring level, "
                  + ", ".join(f"{t} {v:+.2f} m" for t, v in THRESHOLDS.items()) + ".",
                  f"- {N_BOOT} bootstrap resamples of the years; crossing years are percentiles over the resamples "
                  f"that cross by {YEAR_CAP}.",
                  "",
                  "## Headline table",
                  "",
                  "| Cluster | Threshold | Slope (mm/yr) | p | Fitted level, last year (m) | State | "
                  "Crossing year (5 — 50 — 95) | Resamples crossing |",
                  "|---|---|---|---|---|---|---|---|"]
    for _, r in out.iterrows():
        memo_lines.append(
            f"| {_lab(r['Cluster'])} | {r['Threshold']} | {r['slope_pt_m_per_yr'] * 1000:+.2f} | "
            f"{r['slope_pt_p']:.3f} | {r['level_fit_last_year']:+.2f} ({int(r['last_year'])}) | {r['state_pt']} | "
            f"{_rng(r)} | {r['share_boot_crosses']:.0%} |")

    # The reading, from the table: count the states and name the clusters in each
    memo_lines += ["", "## Reading", ""]
    sl = out.drop_duplicates("Cluster")
    rising = sl[sl["slope_pt_m_per_yr"] > 0]
    sig = sl[sl["slope_pt_p"] < 0.05]
    memo_lines.append(
        f"- The mean spring level is rising from {FIT_START} at {len(rising)} of {len(sl)} clusters"
        + (f" ({', '.join(_lab(c) for c in rising['Cluster'])})" if len(rising) else "")
        + f"; {len(sig)} of {len(sl)} slopes are significant at p < 0.05"
        + (f" ({', '.join(_lab(c) for c in sig['Cluster'])})" if len(sig) else "") + ".")
    for tname in THRESHOLDS:
        t = out[out["Threshold"] == tname]
        parts = []
        for stn in STATES:
            cs = t[t["state_pt"] == stn]["Cluster"]
            if len(cs):
                parts.append(f"{stn}: {', '.join(_lab(c) for c in cs)}")
        memo_lines.append(f"- {tname} ({THRESHOLDS[tname]:+.2f} m), point estimate — " + "; ".join(parts) + ".")
    crossing = out[out["state_pt"] == "crosses"]
    if crossing.empty:
        memo_lines.append(f"- No cluster crosses either threshold on its point-estimate trend by {YEAR_CAP}.")
    else:
        for _, r in crossing.iterrows():
            memo_lines.append(f"- {_lab(r['Cluster'])} crosses {r['Threshold']} on its point estimate in "
                              f"{r['year_crossing_pt']:.0f} (bootstrap {_rng(r)}; {r['share_boot_crosses']:.0%} of "
                              "resamples cross).")
    if F_SPRING_TREND.exists():
        st = pd.read_csv(F_SPRING_TREND)
        if {"Cluster", "Slope_m_per_yr_fit", "p_value_fit", "fit_start"} <= set(st.columns):
            memo_lines.append(
                "- Script 14's spring trend table (14_spring_trend_stats.csv, from "
                f"{int(st['fit_start'].iloc[0])}): "
                + "; ".join(f"{_lab(r.Cluster)} {r.Slope_m_per_yr_fit * 1000:+.1f} mm/yr (p {r.p_value_fit:.2f})"
                            for r in st.itertuples()) + ".")

    memo_lines += [
        "",
        "## Caveats",
        "",
        "- Context only. The thresholds are community levels (the handbook's nine-year means at Newborough and "
        "Ainsdale), not limits, and a cluster series is not a slack's floor: D-296 keeps them out of tests.",
        "- Linear extrapolation. The bootstrap captures sampling uncertainty in slope and intercept; it does NOT "
        "capture model-form uncertainty.",
        "- The cluster series averages wells with different ground elevations, so the threshold is an effective "
        "threshold against the cluster series, not against any well.",
        "- Year-resampling does not preserve year-to-year autocorrelation, so its intervals may be narrower than a "
        "block bootstrap's.",
        "",
        "## Outputs",
        "",
        "- `14b_year_of_crossing.csv` — per-cluster × threshold table (states, crossing years, bootstrap shares).",
        "- `14b_year_of_crossing.png` — per-cluster panels: observed spring levels, OLS trend + 90% band, "
        "thresholds, crossing-year bands where a cluster crosses.",
        "- `14b_year_of_crossing_results.md` — this memo.",
    ]
    OUT_MEMO.write_text("\n".join(memo_lines))
    print(f"Wrote {OUT_MEMO.relative_to(REPO)}")
    print()
    print("─" * 72)
    done()
    print("─" * 72)


if __name__ == "__main__":
    main()
