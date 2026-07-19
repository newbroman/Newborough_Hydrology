"""
28_c3_detrend_check.py — Diagnostic: is C3 mechanistically C2 + coastal-erosion drift?

Routed from HANDOVER_c3_detrend_check.md (2026-05-29).

Cluster-framework diagnostic. Enters run_analysis.py at Phase 14, Step 31.
Read-only on pipeline outputs; writes to outputs/28_c3_detrend/.

Procedure (per handover):
1. For each well, compute the predicted coastal-erosion drift rate
   δ(d) = δ₀ × max(0, 1 − d/L) using the live Script 25 forest-free
   linear-capped fit.
2. De-trend the well's monthly hydrograph by subtracting the linear
   trend of slope δ(d) (since δ is negative = decline, this adds a
   positive correction over time, undoing the decline).
3. Re-classify the de-trended hydrograph against the *un-de-trended*
   cluster centroids (correlation distance over month-anomaly series).
4. Tabulate per-well: original best-match, de-trended best-match,
   sensitivity outcomes.

Decision:
- ≥17 of 21 C3 wells move to C2 → H1 strongly supported.
- 11–16 → partial.
- ≤10 → H0 confirmed.
"""

from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-05-29
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
# 1.1.0 — Re-wired to paths.py and outputs/28_c3_detrend/ canonical
#         directory. Entered run_analysis.py at Phase 14 Step 31. No
#         change to procedure; outputs byte-identical to the standalone
#         outputs/diagnostics/ version it replaces.
# 1.0.x — Initial standalone diagnostic.

import sys
import pandas as pd
import numpy as np
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
from utils.render_utils import render_figure

paths.make_all_dirs()

F_CLUSTER   = paths.INT_CLUSTER_STATS
F_WELLS     = paths.INT_WELLS_CLEAN_MAOD
F_CENTROIDS = paths.INT_REGIONAL_AVG
F_FIT       = paths.OUT_25_FIT_PARAMETERS
F_SLOPES    = paths.OUT_25_PER_WELL_SLOPES

OUT_CSV  = paths.OUT_28_DETREND_TABLE
OUT_MEMO = paths.OUT_28_DETREND_MEMO
OUT_FIG  = paths.OUT_28_DETREND_PANEL

CENT_LABELS = ["C1", "C2", "C3", "C4", "C5"]


# ── Helpers ────────────────────────────────────────────────────────────────

def norm_well_id(x) -> str:
    return str(x).strip().lower().replace(" ", "")


def anomaly(series: pd.Series) -> pd.Series:
    return series - series.mean()


def correlation_distance(a: pd.Series, b: pd.Series) -> float:
    """Pearson 1 − r over aligned non-NaN months; requires ≥12 common months."""
    aligned = pd.concat([a, b], axis=1, sort=False).dropna()
    if len(aligned) < 12:
        return np.nan
    aa = aligned.iloc[:, 0] - aligned.iloc[:, 0].mean()
    bb = aligned.iloc[:, 1] - aligned.iloc[:, 1].mean()
    num = (aa * bb).sum()
    den = np.sqrt((aa ** 2).sum() * (bb ** 2).sum())
    if den == 0:
        return np.nan
    return 1.0 - num / den


def predicted_delta(d_m: float, delta_0_mm_yr: float, L_m: float) -> float:
    """Script 25 linear-capped: δ(d) = δ₀ · max(0, 1 − d/L). Returns mm/yr."""
    if pd.isna(d_m):
        return np.nan
    return delta_0_mm_yr * max(0.0, 1.0 - d_m / L_m)


def detrend(hydro: pd.Series, delta_per_year_m: float,
            summer_only: bool = False) -> pd.Series:
    """
    De-trend a monthly hydrograph by subtracting a linear time trend of
    slope `delta_per_year_m` (m/yr). Anchor t = 0 at the first valid month.

    If delta_per_year_m < 0 (the typical case — summer minima decline),
    the subtraction adds a positive correction over time, undoing the
    drift downward.

    summer_only=True applies the correction only in Jun–Sep.
    """
    if pd.isna(delta_per_year_m):
        return hydro.copy()
    dates = hydro.index
    t0 = dates.min()
    years = (dates - t0).days / 365.25
    correction = -delta_per_year_m * years  # subtract slope×t → add |slope|×t when slope<0
    if summer_only:
        is_summer = dates.month.isin([6, 7, 8, 9]).astype(float)
        correction = correction * is_summer
    return hydro - delta_per_year_m * years if not summer_only else (
        hydro + pd.Series(correction.values, index=hydro.index)
    )


def best_match(well_series: pd.Series, centroid_anoms: dict) -> tuple:
    """Return (best_label, {label: distance})."""
    w_anom = anomaly(well_series.dropna())
    dists = {label: correlation_distance(w_anom, cent)
             for label, cent in centroid_anoms.items()}
    # Argmin ignoring NaN
    valid = {k: v for k, v in dists.items() if pd.notna(v)}
    if not valid:
        return "n/a", dists
    best = min(valid, key=valid.get)
    return best, dists


# ── Load ───────────────────────────────────────────────────────────────────

print("─" * 72)
print("c3_detrend_check — diagnostic for HANDOVER_c3_detrend_check.md")
print("─" * 72)

fit = pd.read_csv(F_FIT)
forest_free = fit[(fit["source"] == "forest_free") & (fit["model"] == "linear_capped")].iloc[0]
full        = fit[(fit["source"] == "full")        & (fit["model"] == "linear_capped")].iloc[0]
DELTA0_FF, L_FF     = forest_free["delta_0_mm_yr"], forest_free["L_m"]
DELTA0_FULL, L_FULL = full["delta_0_mm_yr"],         full["L_m"]
print(f"Live fit (forest-free linear-capped): δ₀ = {DELTA0_FF:.2f} mm/yr, L = {L_FF:.0f} m")
print(f"Live fit (full linear-capped):        δ₀ = {DELTA0_FULL:.2f} mm/yr, L = {L_FULL:.0f} m")

slopes = pd.read_csv(F_SLOPES)
slopes["mid"] = slopes["well"].apply(norm_well_id)

clust = pd.read_csv(F_CLUSTER)
clust["mid"] = clust["Match_ID"].apply(norm_well_id)
print(f"Cluster assignments loaded: n = {len(clust)} wells")

wells_df = pd.read_csv(F_WELLS, index_col=0, parse_dates=True)
wells_df.columns = [norm_well_id(c) for c in wells_df.columns]
print(f"Hydrographs loaded: {wells_df.shape[1]} wells × {wells_df.shape[0]} months")

centroids = pd.read_csv(F_CENTROIDS, index_col="Date", parse_dates=True)
centroid_anoms = {label: anomaly(centroids[label].dropna()) for label in CENT_LABELS}
print(f"Centroids loaded: {CENT_LABELS} × {centroids.shape[0]} months")
print()


# ── Per-well loop ──────────────────────────────────────────────────────────

rows = []
for _, row in clust.iterrows():
    mid = row["mid"]
    cluster = int(row["Cluster"])
    label   = row["Cluster_Label"]
    if cluster == 1:
        continue  # skip C1 (lake-buffered, mechanistically different per handover)

    if mid not in wells_df.columns:
        continue

    sr = slopes[slopes["mid"] == mid]
    if len(sr) == 0:
        d_coast, emp_slope = np.nan, np.nan
    else:
        d_coast  = float(sr["dist_coast_m"].iloc[0])
        emp_slope = float(sr["slope_m_yr"].iloc[0])

    h_obs = wells_df[mid].dropna()
    if len(h_obs) < 24:
        continue
    obs_years = (h_obs.index.max() - h_obs.index.min()).days / 365.25

    # Modelled δ(d) for each sensitivity branch
    d_ff       = predicted_delta(d_coast, DELTA0_FF,   L_FF)
    d_full     = predicted_delta(d_coast, DELTA0_FULL, L_FULL)
    d_L_low    = predicted_delta(d_coast, DELTA0_FF,   500.0)
    d_L_high   = predicted_delta(d_coast, DELTA0_FF,   1500.0)

    # Original best-match
    best_orig, dist_orig = best_match(h_obs, centroid_anoms)

    # De-trended variants
    def _do(d_mm_yr, summer=False):
        if pd.isna(d_mm_yr):
            return "n/a", {l: np.nan for l in CENT_LABELS}
        h_dt = detrend(h_obs, d_mm_yr / 1000.0, summer_only=summer)
        return best_match(h_dt, centroid_anoms)

    best_dt_ff,     dist_dt_ff     = _do(d_ff)
    best_dt_summer, _              = _do(d_ff, summer=True)
    best_dt_full,   _              = _do(d_full)
    best_dt_Llow,   _              = _do(d_L_low)
    best_dt_Lhigh,  _              = _do(d_L_high)

    rows.append({
        "Match_ID":            row["Match_ID"],
        "Original_Cluster":    f"C{cluster}",
        "Cluster_Label":       label,
        "dist_coast_m":        d_coast,
        "empirical_slope_m_yr": emp_slope,
        "model_delta_mm_yr":   d_ff,
        "obs_years":           obs_years,
        "total_drift_m":       (d_ff / 1000.0 * obs_years) if pd.notna(d_ff) else np.nan,
        "Best_Original":       best_orig,
        "Best_Detrended_FF":   best_dt_ff,
        "Best_Detrended_Summer": best_dt_summer,
        "Best_Detrended_Full":   best_dt_full,
        "Best_Detrended_L500":   best_dt_Llow,
        "Best_Detrended_L1500":  best_dt_Lhigh,
        "D_C1": dist_orig["C1"],
        "D_C2": dist_orig["C2"],
        "D_C3": dist_orig["C3"],
        "D_C4": dist_orig["C4"],
        "D_C5": dist_orig["C5"],
        "D_C2_DT": dist_dt_ff.get("C2"),
        "D_C3_DT": dist_dt_ff.get("C3"),
        "Margin_C3_C2_Orig":    dist_orig["C3"] - dist_orig["C2"],
        "Margin_C3_C2_DT":      (dist_dt_ff.get("C3") - dist_dt_ff.get("C2")
                                 if pd.notna(dist_dt_ff.get("C2")) else np.nan),
    })

result = pd.DataFrame(rows)
result.to_csv(OUT_CSV, index=False)
print(f"Wrote {OUT_CSV.relative_to(REPO)}: {len(result)} rows")


# ── Headline + sanity checks ───────────────────────────────────────────────

def cluster_summary(df, orig_label):
    sub = df[df["Original_Cluster"] == orig_label]
    has_drift = sub.dropna(subset=["model_delta_mm_yr"])
    n_total = len(sub)
    n_drift = len(has_drift)
    moves = has_drift["Best_Detrended_FF"].value_counts().to_dict()
    return {
        "n_total":        n_total,
        "n_with_drift":   n_drift,
        "n_excluded":     n_total - n_drift,
        "moves":          moves,
        "stays_in_self":  moves.get(orig_label, 0),
        "moves_to_C2":    moves.get("C2", 0),
    }

c3 = cluster_summary(result, "C3")
c2 = cluster_summary(result, "C2")
c4 = cluster_summary(result, "C4")
c5 = cluster_summary(result, "C5")

print()
print("─── HEADLINE C3 result ──────────────────────────────────────────")
print(f"C3 wells with hydrograph + dist data: {c3['n_with_drift']} of {c3['n_total']}")
print(f"After forest-free de-trending:")
for lab, n in sorted(c3["moves"].items()):
    pct = n / c3["n_with_drift"] * 100 if c3["n_with_drift"] else 0
    saved(f"{lab:4}: {n:3} ({pct:.0f}%)")

print()
print("─── Sanity checks (proportion staying in original cluster) ──────")
for lab, ck in [("C2", c2), ("C4", c4), ("C5", c5)]:
    if ck["n_with_drift"]:
        pct = ck["stays_in_self"] / ck["n_with_drift"] * 100
        print(f"  {lab}: stays in {lab} = {ck['stays_in_self']}/{ck['n_with_drift']} ({pct:.0f}%)  "
              f"[excluded: {ck['n_excluded']}]")
    else:
        print(f"  {lab}: no wells with drift data  [excluded: {ck['n_excluded']}]")

excluded = result[result["model_delta_mm_yr"].isna()]
if len(excluded):
    print()
    print("─── Excluded wells (no dist_coast_m) ──")
    for _, r in excluded.iterrows():
        print(f"  {r['Match_ID']:10}  {r['Cluster_Label']}")

# Sensitivities — C3 only
print()
print("─── C3 sensitivity ─────────────────────────────────────────────")
c3_rows = result[result["Original_Cluster"] == "C3"].dropna(subset=["model_delta_mm_yr"])
for col, label in [("Best_Detrended_FF",     "forest-free, monthly-uniform (HEADLINE)"),
                   ("Best_Detrended_Summer", "forest-free, summer-only Jun–Sep"),
                   ("Best_Detrended_Full",   "full δ₀ (includes forest)"),
                   ("Best_Detrended_L500",   "L = 500 m"),
                   ("Best_Detrended_L1500",  "L = 1500 m")]:
    to_c2  = (c3_rows[col] == "C2").sum()
    to_c3  = (c3_rows[col] == "C3").sum()
    other  = len(c3_rows) - to_c2 - to_c3
    print(f"  {label:45} → C2: {to_c2:2}  C3: {to_c3:2}  other: {other}")


# ── Memo ───────────────────────────────────────────────────────────────────

def decision_text(n_c2, n_total):
    pct = n_c2 / n_total if n_total else 0
    if pct >= 17/21:
        return "**H1 strongly supported.** Cluster structure is dominated by the coastal-erosion gradient."
    elif pct >= 11/21:
        return "**H1 partially supported.** The gradient explains most of C2/C3 distinction but residual structure remains."
    else:
        return "**H0 confirmed.** C3 is a genuinely distinct cluster; gradient adds drift but is not the constitutive mechanism."

memo = f"""# C3 de-trending check — results

*Diagnostic from `28_c3_detrend_check.py`, routed from
`HANDOVER_c3_detrend_check.md`.*

## Live fit values (forest-free linear-capped, Script 25)

| Parameter | Value |
|---|---|
| δ₀ (coast-edge slope) | **{DELTA0_FF:.2f} mm/yr** |
| L (decay length)      | **{L_FF:.0f} m** |
| Sensitivity δ₀ (full fit) | {DELTA0_FULL:.2f} mm/yr |
| Sensitivity L (full fit)  | {L_FULL:.0f} m |

## Headline result — C3 hydrographs after forest-free monthly-uniform de-trending

**{c3['n_with_drift']} of {c3['n_total']} C3 wells** carry a Script 25 dist_coast and
hydrograph (excluded: {c3['n_excluded']} wells without coastal-distance metadata —
typically the forest-zone or heavily perturbed wells dropped from Script 25's
forest-free fit, e.g. CEH36 and WMC3).

After de-trending against the un-de-trended cluster centroids:

| Destination | n | % of n_with_drift |
|---|---|---|
"""

for lab in CENT_LABELS:
    n = c3["moves"].get(lab, 0)
    pct = n / c3["n_with_drift"] * 100 if c3["n_with_drift"] else 0
    memo += f"| **→ {lab}** | {n} | {pct:.0f}% |\n"

memo += f"""
**Verdict.** {decision_text(c3['moves_to_C2'], c3['n_with_drift'])}

## Sanity checks

| Source cluster | n (with drift) | Stays in cluster | % retained |
|---|---|---|---|
| C2 | {c2['n_with_drift']} | {c2['stays_in_self']} | {(c2['stays_in_self']/c2['n_with_drift']*100) if c2['n_with_drift'] else 0:.0f}% |
| C4 | {c4['n_with_drift']} | {c4['stays_in_self']} | {(c4['stays_in_self']/c4['n_with_drift']*100) if c4['n_with_drift'] else 0:.0f}% |
| C5 | {c5['n_with_drift']} | {c5['stays_in_self']} | {(c5['stays_in_self']/c5['n_with_drift']*100) if c5['n_with_drift'] else 0:.0f}% |

A high C2 retention is required for the procedure to be valid (C2 wells should
not be perturbed by a small δ(d) correction). Low C2 retention would indicate
the procedure is contaminating hydrographs rather than testing a hypothesis.

## Sensitivities (C3 only)

| Variant | → C2 | → C3 | Other |
|---|---|---|---|
"""

for col, label in [("Best_Detrended_FF",     "forest-free, monthly-uniform (HEADLINE)"),
                   ("Best_Detrended_Summer", "forest-free, summer-only Jun–Sep"),
                   ("Best_Detrended_Full",   "full δ₀ (includes forest)"),
                   ("Best_Detrended_L500",   "L = 500 m"),
                   ("Best_Detrended_L1500",  "L = 1500 m")]:
    to_c2  = int((c3_rows[col] == "C2").sum())
    to_c3  = int((c3_rows[col] == "C3").sum())
    other  = len(c3_rows) - to_c2 - to_c3
    memo += f"| {label} | {to_c2} | {to_c3} | {other} |\n"

memo += f"""
## Excluded wells (no dist_coast_m available)

"""
if len(excluded):
    for _, r in excluded.iterrows():
        memo += f"- `{r['Match_ID']}` ({r['Cluster_Label']})\n"
else:
    memo += "*(none)*\n"

memo += """
## Next step

See *What follows from the result* in `HANDOVER_c3_detrend_check.md`. Headline
verdict above maps onto either the H1-follow-on (report reframing) or the
H0-follow-on (single sentence in §5.4.3 noting the check was performed).

Per-well detail in `c3_detrend_check.csv`. Figure (if generated): `c3_detrend_check_panel.png`.
"""

OUT_MEMO.write_text(memo)
print()
print(f"Wrote {OUT_MEMO.relative_to(REPO)}")


# ── Figure ─────────────────────────────────────────────────────────────────

c3_rows_for_fig = result[result["Original_Cluster"] == "C3"].dropna(subset=["model_delta_mm_yr"]).reset_index(drop=True)
n_panels = len(c3_rows_for_fig)
if n_panels > 0:
    ncols = 5
    nrows = int(np.ceil(n_panels / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3.0, nrows * 2.2), sharex=True)
    axes = np.atleast_2d(axes).flatten()

    c2_anom = centroid_anoms["C2"]
    c3_anom = centroid_anoms["C3"]

    for i, (_, row) in enumerate(c3_rows_for_fig.iterrows()):
        ax = axes[i]
        mid = norm_well_id(row["Match_ID"])
        h = wells_df[mid].dropna()
        d_mm_yr = row["model_delta_mm_yr"]
        h_dt = detrend(h, d_mm_yr / 1000.0)

        h_a    = anomaly(h)
        h_dt_a = anomaly(h_dt)

        ax.plot(c2_anom.index, c2_anom.values, color="#2ca02c", lw=0.8, alpha=0.7, label="C2 centroid")
        ax.plot(c3_anom.index, c3_anom.values, color="#d62728", lw=0.8, alpha=0.7, label="C3 centroid")
        ax.plot(h_a.index,    h_a.values,    color="#444",    lw=1.0, alpha=0.6, label="orig")
        ax.plot(h_dt_a.index, h_dt_a.values, color="#000",    lw=1.2,            label="detrend")

        ax.set_title(f"{row['Match_ID']}  ({row['Best_Original']}→{row['Best_Detrended_FF']})",
                     fontsize=9)
        ax.tick_params(axis='both', labelsize=7)
        ax.grid(alpha=0.25, lw=0.4)

    # Hide unused panels
    for j in range(n_panels, len(axes)):
        axes[j].set_visible(False)

    # Single legend in last visible cell or top-right
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right", fontsize=8, ncol=4, frameon=False)
    fig.suptitle("C3 wells: original vs de-trended anomaly hydrographs against C2 / C3 centroids",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    render_figure(fig, OUT_FIG)
    print(f"Wrote {OUT_FIG.relative_to(REPO)}")

print()
print("─" * 72)
done()
print("─" * 72)
