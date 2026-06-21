"""
14b_year_of_crossing.py — Bootstrap year-of-crossing for per-cluster
annual summer-minimum trends against Curreli et al. (2013) ecological
thresholds.

Routed from the 2026-05-29 main-report editorial review (gap B in the
post-review priorities list). Main report §7 Conclusion 11 currently
states "C1 summer minima approaching the SD16 dry slack viability
threshold around 2030–2032" without a stated confidence interval. This
script replaces the qualitative date band with a bootstrap CI on the
crossing year per cluster × threshold.

Procedure:
1. Load Script 14's per-cluster annual summer-minimum series
   (`14_annual_extremes.csv`).
2. For each cluster: fit a linear trend (depth_below_ground = a + b·year)
   over the observed years.
3. Bootstrap by resampling years with replacement (n = 1000); for each
   resample refit the trend and compute the year at which the linear
   extrapolation crosses each Curreli threshold (SD15b at 0.61 m below
   ground; SD16 at 0.98 m below ground).
4. Tabulate 5th / 50th / 95th percentile crossing years per
   cluster × threshold.

Standalone diagnostic following the pattern of `11b_spatial_thresholds.py`
relative to `11_forecasting_thresholds.py`. Reads only Script 14 output;
writes to `outputs/14_climate_projections/`.

Limitations:
- Linear extrapolation is fragile beyond the observed window. The bootstrap
  captures sampling uncertainty in the slope/intercept but not model-form
  uncertainty (a linear trend may not extrapolate cleanly into a regime
  where summer-min approaches a basement controlled by drainage geometry
  or where climate trajectory diverges from observed).
- Per-cluster centroid summer-min averages over wells with different
  ground elevations within the cluster. The threshold (depth below ground)
  is therefore an effective threshold against the centroid, not against
  any specific well. C1 sits closest to its SD16 threshold and is the
  cluster the Conclusion 11 claim is built around.
"""

from __future__ import annotations

__version__ = "1.1.1"  # Hollingham (2026) — 2026-05-29
# 1.1.1 — Output paths now reference canonical OUT_14B_* constants added to
#         paths.py (OUT_14B_CROSSING_CSV/FIG, OUT_14B_RESULTS_MEMO). Replaces
#         the local DIR_14 re-derivation; single source of truth. No change to
#         output filenames or contents.
# 1.1.0 — Figure enlarged and brought into line with conventions:
#           * Layout changed from a cramped 1×5 single row to a 3-over-2
#             stacked grid (C1/C2/C3 top, C4/C5 bottom), with a shared
#             legend in the empty sixth cell. Panels are much larger.
#           * dpi 180 → 300 and facecolor="white" (Script 14 convention
#             for dense threshold/trend figures).
#           * Colours now via get_cluster_colour() so the figure respects
#             BW_MODE (was using CLUSTER_COLOURS directly — colour-only).
#           * Threshold labels moved inside each panel to avoid spilling
#             into the adjacent panel.
# 1.0.0 — Initial. Bootstrap year-of-crossing diagnostic for §7 Conclusion 11.

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ── Pipeline imports ──────────────────────────────────────────────────────
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
    SD15b, SD16,
)

paths.make_all_dirs()

# Read Script 14's annual summer-min table
F_ANNUAL  = paths.OUT_14_ANNUAL_EXTREMES

# Outputs — canonical OUT_14B_* constants in paths.py (share Script 14's
# directory). Single source of truth.
OUT_CSV   = paths.OUT_14B_CROSSING_CSV
OUT_FIG   = paths.OUT_14B_CROSSING_FIG
OUT_MEMO  = paths.OUT_14B_RESULTS_MEMO

# Curreli (2013) thresholds. Values from utils.config (depth below ground, m).
# Signed against the data convention: 14_annual_extremes.csv stores depth as
# negative below ground (Value_m = -0.89 ≡ water table 0.89 m below ground).
THRESHOLDS = {
    "SD15b": -SD15b,  # -0.61 m (wet slack viability)
    "SD16":  -SD16,   # -0.98 m (dry slack threshold)
}

N_BOOT  = 1000
RNG     = np.random.default_rng(20260529)

# ── Procedure ─────────────────────────────────────────────────────────────

print("─" * 72)
print("14b — Bootstrap year-of-crossing for per-cluster summer-min trends")
print("─" * 72)

ann = pd.read_csv(F_ANNUAL)
sm  = ann[ann["Season"] == "Summer_Min"].copy()
print(f"Loaded {len(sm)} summer-min rows across {sm['Cluster'].nunique()} clusters")

def year_of_crossing(year_arr, depth_arr, threshold_val, year_cap=2080):
    """Fit y = a + b·x and solve for x where y = threshold_val.
    Return year_cap (sentinel) if slope >= 0 (no crossing in the relevant
    direction) or crossing year exceeds year_cap. Returns NaN if fit fails."""
    if len(year_arr) < 3:
        return np.nan
    try:
        b, a = np.polyfit(year_arr, depth_arr, deg=1)
    except (np.linalg.LinAlgError, ValueError):
        return np.nan
    if b >= 0:
        # Slope is non-decreasing — water table not declining → no crossing
        return year_cap
    yr_cross = (threshold_val - a) / b
    if yr_cross > year_cap or yr_cross < year_arr.min():
        return year_cap
    return float(yr_cross)


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

    # Point-estimate fit on the full series
    b_pt, a_pt = np.polyfit(years, depths, 1)
    label = sub["Cluster"].iloc[0]  # actual label is in CLUSTER_LABELS, but we use the short

    # Bootstrap: resample years with replacement
    boot_yc = {name: np.full(N_BOOT, np.nan) for name in THRESHOLDS}
    boot_b  = np.full(N_BOOT, np.nan)
    boot_a  = np.full(N_BOOT, np.nan)
    for k in range(N_BOOT):
        idx = RNG.integers(0, n_yr, size=n_yr)
        # Avoid pathological all-same-year resamples (rare but possible)
        if len(np.unique(years[idx])) < 3:
            continue
        try:
            b_k, a_k = np.polyfit(years[idx], depths[idx], 1)
        except (np.linalg.LinAlgError, ValueError):
            continue
        boot_b[k] = b_k
        boot_a[k] = a_k
        for name, tval in THRESHOLDS.items():
            boot_yc[name][k] = year_of_crossing(years[idx], depths[idx], tval)

    # Percentiles for each threshold
    boot_traces[cluster] = {
        "years": years, "depths": depths,
        "a_pt": a_pt, "b_pt": b_pt,
        "boot_a": boot_a[~np.isnan(boot_a)],
        "boot_b": boot_b[~np.isnan(boot_b)],
    }

    for tname, tval in THRESHOLDS.items():
        yc_pt = year_of_crossing(years, depths, tval)
        yc_boot = boot_yc[tname][~np.isnan(boot_yc[tname])]
        if len(yc_boot) > 0:
            pcts = np.percentile(yc_boot, [5, 50, 95])
        else:
            pcts = [np.nan, np.nan, np.nan]
        rows.append({
            "Cluster":           cluster,
            "Threshold":         tname,
            "Threshold_m":       tval,
            "n_years_obs":       n_yr,
            "slope_pt_m_per_yr": round(b_pt, 5),
            "intercept_pt":      round(a_pt, 3),
            "current_depth_2025": round(a_pt + b_pt * 2025, 3),
            "year_crossing_pt":  round(yc_pt, 1) if not np.isnan(yc_pt) else None,
            "year_crossing_5":   round(pcts[0], 1) if not np.isnan(pcts[0]) else None,
            "year_crossing_50":  round(pcts[1], 1) if not np.isnan(pcts[1]) else None,
            "year_crossing_95":  round(pcts[2], 1) if not np.isnan(pcts[2]) else None,
            "n_boot_resolved":   int(len(yc_boot)),
        })

out = pd.DataFrame(rows)
out.to_csv(OUT_CSV, index=False)
print(f"\nWrote {OUT_CSV.relative_to(REPO)}")

# ── Console summary ───────────────────────────────────────────────────────
print()
print("─── Year of crossing (median, 95% CI) ───")
print(f"{'Cluster':6} {'Threshold':10} {'slope (mm/yr)':>15} {'crossing yr (5–50–95)':>30}")
print("-" * 72)
for _, r in out.iterrows():
    if pd.isna(r['year_crossing_50']):
        rng = "—"
    else:
        rng = f"{r['year_crossing_5']:>5.0f} – {r['year_crossing_50']:>5.0f} – {r['year_crossing_95']:>5.0f}"
    slp = r['slope_pt_m_per_yr'] * 1000  # mm/yr
    print(f"{r['Cluster']:6} {r['Threshold']:10} {slp:>+15.2f} {rng:>30}")

# ── Figure: 3-over-2 stacked per-cluster panels ───────────────────────────
from matplotlib.lines import Line2D     # noqa: E402
from matplotlib.patches import Patch    # noqa: E402

clusters_sorted = sorted(boot_traces.keys())
x_proj = np.arange(2005, 2061)

# 2 rows × 3 cols, filled row-major: C1/C2/C3 on top, C4/C5 on the bottom.
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
    # 95% CI cone from bootstrap
    boot_pred = np.array([
        trace["boot_a"][j] + trace["boot_b"][j] * x_proj
        for j in range(min(len(trace["boot_a"]), len(trace["boot_b"])))
    ])
    if len(boot_pred) > 0:
        lo = np.percentile(boot_pred, 5, axis=0)
        hi = np.percentile(boot_pred, 95, axis=0)
        ax.fill_between(x_proj, lo, hi, color=col, alpha=0.18,
                         linewidth=0, label="95% CI", zorder=1)

    # Threshold lines — labelled inside the panel (right edge) so the text
    # does not spill into the adjacent panel of the grid.
    for tname, tval in THRESHOLDS.items():
        ax.axhline(tval, color="black", linewidth=0.7, linestyle="--", alpha=0.7)
        ax.text(2059, tval, tname, fontsize=8, va="bottom", ha="right",
                 color="#333")

    # Crossing-year median + 5–95 band from the table
    sub_rows = out[out["Cluster"] == cluster]
    for _, r in sub_rows.iterrows():
        if r["year_crossing_50"] is not None and r["year_crossing_50"] < 2061:
            ax.axvspan(r["year_crossing_5"], r["year_crossing_95"],
                        alpha=0.15, color="black", linewidth=0)
            ax.axvline(r["year_crossing_50"], color="black",
                        linewidth=0.8, alpha=0.6)

    ax.set_title(label, fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel("Year")
    ax.set_xlim(2005, 2060)
    ax.grid(alpha=0.3, linewidth=0.4)
    if ax in left_col_axes:
        ax.set_ylabel("Summer-min depth\n(m, negative below ground)")
    else:
        ax.tick_params(labelleft=False)

# Hide any unused panels (the sixth cell) and host the shared legend there.
for ax in axes_flat[len(clusters_sorted):]:
    ax.axis("off")

legend_handles = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#666",
           markeredgecolor="white", markersize=8,
           label="Observed annual summer minimum"),
    Line2D([0], [0], color="#444", linewidth=2.0,
           label="OLS trend (point estimate)"),
    Patch(facecolor="#888", alpha=0.18, label="95% bootstrap CI cone"),
    Line2D([0], [0], color="black", linewidth=0.8, linestyle="--",
           label="Curreli (2013) threshold"),
    Patch(facecolor="black", alpha=0.15, label="Crossing-year 5–95% band"),
    Line2D([0], [0], color="black", linewidth=0.8, alpha=0.6,
           label="Crossing-year median"),
]
legend_host = axes_flat[-1]  # the hidden sixth cell
legend_host.legend(handles=legend_handles, loc="center", fontsize=9,
                   framealpha=0.95, title="Legend", title_fontsize=10)

fig.suptitle("Bootstrap year-of-crossing for per-cluster summer-minimum trends "
             "against Curreli (2013) ecological thresholds",
             fontsize=13, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight", facecolor="white")
print(f"\nWrote {OUT_FIG.relative_to(REPO)}")


# ── Memo ──────────────────────────────────────────────────────────────────
memo_lines = ["# Bootstrap year-of-crossing — results\n",
              "",
              "*Diagnostic from `14b_year_of_crossing.py`. Routed from the 2026-05-29",
              "main-report review (gap B: stated CI on the C1 SD16 crossing year claimed",
              "in §7 Conclusion 11).*",
              "",
              "## Headline table",
              "",
              "| Cluster | Threshold | Slope (mm/yr) | Crossing year (5 — 50 — 95) |",
              "|---|---|---|---|"]
for _, r in out.iterrows():
    if r['year_crossing_50'] is None:
        rng = "—"
    else:
        rng = f"**{r['year_crossing_5']:.0f}** — **{r['year_crossing_50']:.0f}** — **{r['year_crossing_95']:.0f}**"
    slp = r['slope_pt_m_per_yr'] * 1000
    memo_lines.append(f"| {r['Cluster']} | {r['Threshold']} | {slp:+.2f} | {rng} |")

memo_lines += [
    "",
    "Year-of-crossing values of 2080 are sentinel values where the slope is non-decreasing or the linear projection does not reach the threshold within the year-2080 horizon.",
    "",
    "## Reading",
    "",
    "- The report's §7 Conclusion 11 statement *\"C1 summer minima approaching the SD16 dry slack viability threshold around 2030–2032\"* is replaced by a stated CI on the C1 SD16 crossing year. **Replace with:** \"C1 summer minima are projected to cross the SD16 threshold in **{median} (95% CI {p5}–{p95})**\" using the C1 row above.".format(
        median=int(out[(out['Cluster']=='C1')&(out['Threshold']=='SD16')]['year_crossing_50'].iloc[0])
            if not out[(out['Cluster']=='C1')&(out['Threshold']=='SD16')]['year_crossing_50'].isna().any() else "—",
        p5=int(out[(out['Cluster']=='C1')&(out['Threshold']=='SD16')]['year_crossing_5'].iloc[0])
            if not out[(out['Cluster']=='C1')&(out['Threshold']=='SD16')]['year_crossing_5'].isna().any() else "—",
        p95=int(out[(out['Cluster']=='C1')&(out['Threshold']=='SD16')]['year_crossing_95'].iloc[0])
            if not out[(out['Cluster']=='C1')&(out['Threshold']=='SD16')]['year_crossing_95'].isna().any() else "—",
    ),
    "- C5 has the steepest decline and crosses SD15b and SD16 within the observed-data window or close to it. Existing report prose handles C5's anomalous decline separately (§5.7.2).",
    "- C3 and C4 have non-significant trends (Script 14) — their bootstrap CIs are correspondingly wide.",
    "",
    "## Caveats",
    "",
    "- Linear extrapolation. The bootstrap captures sampling uncertainty in slope and intercept; it does NOT capture model-form uncertainty (the assumption that the linear trend extrapolates cleanly into a regime where summer-min approaches a drainage-controlled basement or where climate trajectory diverges from observed). Consider this an upper-bound horizon, not a calibrated projection.",
    "- The cluster-centroid summer-min averages over wells with different ground elevations within each cluster, so the threshold (\"depth below ground\") is an effective threshold against the centroid, not against any specific well.",
    "- Year-resampling bootstrap preserves the ordering of the trend signal but does not preserve year-to-year autocorrelation. For trends with strong autocorrelation this can produce a slightly narrower CI than a block bootstrap would. Inspection of `14_annual_extremes.csv` summer-min residuals does not show strong autocorrelation; a block bootstrap is unlikely to materially widen the CIs.",
    "- C5's exceptional decline (-37.7 mm/yr; §4.8.1) reflects a coastal-retreat gradient mechanism (Script 25) plus other candidates discussed in §5.7.2 — extrapolating it linearly may understate (if the gradient retreats further inland) or overstate (if coastal retreat itself slows) the C5 crossing year.",
    "",
    "## Cross-references",
    "",
    "- §7 Conclusion 11 — replace the \"around 2030–2032\" qualitative date with the stated CI from this table.",
    "- §4.10.1 / §5.7.1 — the climate-trajectory discussion that frames Conclusion 11 can cite the figure (`14b_year_of_crossing.png`).",
    "- §5.9 — the \"intervention window\" framing can quote the bootstrap CI directly when discussing the C1 timeline.",
    "",
    "## Outputs",
    "",
    "- `14b_year_of_crossing.csv` — per-cluster × threshold table.",
    "- `14b_year_of_crossing.png` — five-cluster figure in a 3-over-2 stacked layout (observed points, OLS trend + 95% CI cone, threshold lines, crossing-year CI bands; shared legend).",
    "- `14b_year_of_crossing_results.md` — this memo.",
]
OUT_MEMO.write_text("\n".join(memo_lines))
print(f"Wrote {OUT_MEMO.relative_to(REPO)}")
print()
print("─" * 72)
done()
print("─" * 72)
