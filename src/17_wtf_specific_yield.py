"""
17_wtf_specific_yield.py
========================
Water Table Fluctuation (WTF) Method — Cluster-Level Specific Yield Estimation
Newborough Warren Coastal Sand Dune Aquifer, 2005–2026

Produces cluster-level WTF Sy estimates (Approaches A and B) for C1–C4 and,
for the Forest cluster (C4), an additional interception-corrected variant
following Freeman (2008). The corrected value populates Table 3c of the
manuscript and feeds the WTF-Sy volumetric water balance (Table 3d, Figure 8b).

Individual well-level WTF analysis and spatial mapping are in script 18.

Outputs:
    17_wtf_01_sy_estimates.csv   — cluster Sy estimates, inc. C4 corrected row
    17_wtf_02_regression.png     — OLS regression plots for Approach A
    17_wtf_03_event_boxplot.png  — Sy distribution plots for Approach B
    17_wtf_04_summary.txt        — plain-text summary for manuscript

References:
    Healy, R.W. and Cook, P.G. (2002) Hydrogeology Journal 10, 91-109.
    Scanlon, B.R., Healy, R.W. and Cook, P.G. (2002) Hydrogeology Journal 10, 18-39.
    Freeman, S. (2008) Hydrological impact of Corsican pine at Newborough Warren.

See wtf_interception_methodology.md for full derivation of the interception
handling, including why reducing only P (not PET) is not double-counting.
"""

import sys
import os

from utils.config import (
    CLUSTER_LABELS, CLUSTER_COLOURS as _CFG_CLUSTER_COLOURS,
    FOREST_INTERCEPTION, FOREST_CIDS as _FOREST_CIDS_INT,
)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import stats

from utils.paths import (
    make_all_dirs, OUT_DIR, DIR_17,
    INT_WELLS_CLEAN, INT_CLIMATE, INT_CLUSTER_STATS, INT_MASTER_DATA,
    INT_REGIONAL_AVG,
    OUT_17_SY_TABLE, OUT_17_REGRESSION, OUT_17_BOXPLOT, OUT_17_SUMMARY,
    INT_WTF_WELL_SY,
)
make_all_dirs()

# ── Constants ──────────────────────────────────────────────────────────────────
WINTER_MONTHS       = [11, 12, 1, 2, 3]   # Nov–Mar: PET negligible
PET_MAX_WINTER      = 0.025                # m/month — exclude months above this
MIN_RISE_M          = 0.005                # minimum detectable water table rise (m)
MIN_NET_RECH        = 0.010                # minimum net recharge for event method (m)
# FOREST_INTERCEPTION imported from config.py (Freeman 2008, 0.24).
# FOREST_CIDS as string keys for column-name compatibility with regional_averages CSV.
FOREST_CIDS = tuple(f"C{cid}" for cid in _FOREST_CIDS_INT)
SY_MIN_PLAUSIBLE    = 0.01                 # physical-plausibility lower bound
SY_MAX_PLAUSIBLE    = 0.50                 # physical-plausibility upper bound

# String-keyed views of utils.config for the 'C1'..'CN' column convention used
# by the regional_averages CSV. Update config.CLUSTER_LABELS — not these — to
# change labels.
CLUSTER_LABELS = {
    f"C{cid}": label for cid, label in CLUSTER_LABELS.items()
}
CLUSTER_COLOURS = {
    f"C{cid}": colour for cid, colour in _CFG_CLUSTER_COLOURS.items()
    if cid in {1, 2, 3, 4, 5}   # exclude reserved C6 colour from the working partition
}
ALL_CIDS = sorted(CLUSTER_LABELS.keys(), key=lambda s: int(s[1:]))   # ['C1','C2','C3','C4','C5']

# Assumed Sy for comparison (Fetter mass-balance method).
# C1 = 0.08 (lake-adjacent silty); C2..C5 = 0.12.
# See PARTITION_HISTORY.md for derivation.
SY_ASSUMED = {"C1": 0.08, "C2": 0.12, "C3": 0.12, "C4": 0.12, "C5": 0.12}

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
})


def load_data():
    """Load climate and cluster-mean water table data.

    Reads canonical pipeline intermediates by name (no developer-specific
    fallback paths). If either file is missing, raises FileNotFoundError
    with a clear message — Script 01 and Script 03 must run first.
    """
    if not INT_CLIMATE.exists():
        raise FileNotFoundError(
            f"{INT_CLIMATE} not found. Run Script 01 first.")
    if not INT_REGIONAL_AVG.exists():
        raise FileNotFoundError(
            f"{INT_REGIONAL_AVG} not found. Run Script 03 first.")

    climate  = pd.read_csv(INT_CLIMATE,      parse_dates=["Date"])
    regional = pd.read_csv(INT_REGIONAL_AVG, parse_dates=["Date"])
    df = regional.merge(climate[["Date", "P_m", "PET"]], on="Date", how="inner")
    df = df.sort_values("Date").reset_index(drop=True)

    # Compute net recharge (m/month) and month
    df["net_R"]  = df["P_m"] - df["PET"]
    df["month"]  = df["Date"].dt.month

    # Compute ΔhC1..C4 (change in cluster-mean head, m/month)
    for cid in ALL_CIDS:
        df[f"dh_{cid}"] = df[cid].diff()

    return df


def approach_a_ols(df):
    """
    Approach A: Corrected WTF regression accounting for storage decay.

    The observed Δh reflects both recharge and drainage:
        Δh = (R / Sy) - β₃·|h_prev|

    Rearranging:
        R = Sy · (Δh + β₃·|h_prev|)

    So: Sy = R / (Δh + β₃·|h_prev|)

    We load cluster-median β₃ values from the SSM output and use them to
    correct the observed Δh before computing Sy.
    """
    from pathlib import Path

    # Load beta3 values from pipeline outputs
    # Load beta3 values from pipeline outputs.
    # Built dynamically over whatever cluster IDs appear in INT_MASTER_DATA
    # (typically 1..5 under the current k=5 partition); this avoids drift if
    # the partition changes.
    try:
        from pathlib import Path as _Path
        master_path = INT_MASTER_DATA
        master = pd.read_csv(master_path)
        b3 = master.groupby("Cluster")["beta_3_drainage"].median()
        beta3 = {int(cid): abs(val) for cid, val in b3.items()}
    except Exception:
        print("  [WARNING] Could not load beta3 values — using uncorrected Δh")
        beta3 = None

    results = {}
    winter = df[
        (df["month"].isin(WINTER_MONTHS)) &
        (df["PET"] < PET_MAX_WINTER)
    ].copy()

    for cid in ALL_CIDS:
        sub = winter[["net_R", f"dh_{cid}", cid]].dropna()
        sub = sub[sub["net_R"] > 0]

        if len(sub) < 10:
            results[cid] = dict(sy=np.nan, r2=np.nan, n=len(sub), se=np.nan)
            continue

        # Correct Δh for drainage: Δh_corrected = Δh + β₃·|h_prev|
        if beta3 is not None:
            b3_val = beta3[int(cid[1:])]
            dh_corrected = sub[f"dh_{cid}"] + b3_val * sub[cid].abs()
        else:
            dh_corrected = sub[f"dh_{cid}"]

        # Only use months where corrected Δh is positive (net recharge signal)
        mask = dh_corrected > MIN_RISE_M
        X = dh_corrected[mask].values
        y = sub["net_R"][mask].values

        if len(X) < 8:
            results[cid] = dict(sy=np.nan, r2=np.nan, n=len(X), se=np.nan)
            continue

        # Sy = R / Δh_corrected — OLS through origin
        slope = np.sum(X * y) / np.sum(X**2)
        Sy = 1.0 / slope if slope > 0 else np.nan

        y_pred = slope * X
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        n = len(X)
        mse = ss_res / max(n - 1, 1)
        se_slope = np.sqrt(mse / np.sum(X**2))
        # SE of Sy via delta method: SE(Sy) ≈ SE(slope)/slope² * Sy²
        se_sy = (se_slope / slope**2) if slope > 0 else np.nan

        results[cid] = dict(
            sy=round(Sy, 4), r2=round(r2, 3), n=n,
            se=round(se_sy, 4), data=sub,
            dh_corrected=dh_corrected[mask], b3=beta3[int(cid[1:])] if beta3 else None
        )
        b3_str = f"{b3_val:.3f}" if beta3 is not None else "n/a"
        print(f"  {CLUSTER_LABELS[cid]}: Sy = {Sy:.3f}  R² = {r2:.3f}  "
              f"n = {n}  SE = {se_sy:.4f}  β₃ = {b3_str}")

    return results


def approach_b_events(df):
    """
    Approach B: Event-based median Sy from rising limb months.
    Sy_i = net_R / Δh for months where Δh > MIN_RISE and net_R > MIN_NET_RECH,
    filtered to the physically plausible range SY_MIN_PLAUSIBLE < Sy < SY_MAX_PLAUSIBLE.

    For the forested clusters (FOREST_CIDS, currently C4 and C5), both
    uncorrected and interception-corrected variants are computed. The
    corrected variant uses
        R_effective = (1 − FOREST_INTERCEPTION)·P − PET
    following Freeman (2008). The interception fraction was measured at C5
    and is applied across all forested clusters. The PET term is not reduced
    — Thornthwaite PET is an energy-based atmospheric demand (independent of
    land cover), so reducing only P is not double-counting (see
    wtf_interception_methodology.md). The corrected medians are reported as
    separate "<cid>_corrected" entries alongside the uncorrected entries to
    populate Table 3c of the manuscript.
    """
    results = {}

    # Precompute corrected net recharge (same formula for every forested cluster).
    df = df.copy()
    df["net_R_forest_corrected"] = df["P_m"] * (1.0 - FOREST_INTERCEPTION) - df["PET"]

    # ── All clusters: uncorrected ─────────────────────────────────────────────
    for cid in ALL_CIDS:
        sub = df[["net_R", f"dh_{cid}"]].dropna().copy()
        events = sub[
            (sub["net_R"]      > MIN_NET_RECH) &
            (sub[f"dh_{cid}"] > MIN_RISE_M)
        ].copy()
        events["sy_i"] = events["net_R"] / events[f"dh_{cid}"]
        events = events[(events["sy_i"] > SY_MIN_PLAUSIBLE) &
                        (events["sy_i"] < SY_MAX_PLAUSIBLE)]

        med = events["sy_i"].median()
        q25 = events["sy_i"].quantile(0.25)
        q75 = events["sy_i"].quantile(0.75)
        n   = len(events)

        results[cid] = dict(
            sy_median=round(med, 4), q25=round(q25, 4), q75=round(q75, 4),
            n=n, sy_values=events["sy_i"].values, corrected=False
        )
        print(f"  {CLUSTER_LABELS[cid]}: Sy median = {med:.3f}  "
              f"IQR [{q25:.3f}, {q75:.3f}]  n = {n}")

    # ── Forested clusters: interception-corrected variants (Freeman, 2008) ─────
    for cid in FOREST_CIDS:
        sub_c = df[["net_R_forest_corrected", f"dh_{cid}"]].dropna().copy()
        events_c = sub_c[
            (sub_c["net_R_forest_corrected"] > MIN_NET_RECH) &
            (sub_c[f"dh_{cid}"]               > MIN_RISE_M)
        ].copy()
        events_c["sy_i"] = events_c["net_R_forest_corrected"] / events_c[f"dh_{cid}"]
        events_c = events_c[(events_c["sy_i"] > SY_MIN_PLAUSIBLE) &
                            (events_c["sy_i"] < SY_MAX_PLAUSIBLE)]

        med_c = events_c["sy_i"].median()
        q25_c = events_c["sy_i"].quantile(0.25)
        q75_c = events_c["sy_i"].quantile(0.75)
        n_c   = len(events_c)

        results[f"{cid}_corrected"] = dict(
            sy_median=round(med_c, 4), q25=round(q25_c, 4), q75=round(q75_c, 4),
            n=n_c, sy_values=events_c["sy_i"].values, corrected=True
        )
        print(f"  {CLUSTER_LABELS[cid]} (interception-corrected): "
              f"Sy median = {med_c:.3f}  IQR [{q25_c:.3f}, {q75_c:.3f}]  n = {n_c}")

    return results


def plot_regression(df, a_results, out_path):
    """Figure: OLS regression plots for Approach A."""
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), facecolor="white")
    fig.patch.set_facecolor("white")
    flat_axes = axes.flatten()

    for ax, cid in zip(flat_axes, ALL_CIDS):
        r = a_results[cid]
        col = CLUSTER_COLOURS[cid]

        if np.isnan(r["sy"]) or "dh_corrected" not in r:
            ax.text(0.5, 0.5, "Insufficient data", transform=ax.transAxes,
                    ha="center", va="center")
            ax.set_title(CLUSTER_LABELS[cid], fontweight="bold")
            continue

        dh_c = r["dh_corrected"] * 1000
        net_r = r["data"].loc[r["dh_corrected"].index, "net_R"] * 1000

        ax.scatter(dh_c, net_r, color=col, alpha=0.65, s=35, zorder=3,
                   label=f"Winter months (n={r['n']})")

        if not np.isnan(r["sy"]):
            xline = np.linspace(0, dh_c.max(), 100)
            ax.plot(xline, xline / r["sy"], color="black", lw=1.8, zorder=4,
                    label=f"WTF: Sy = {r['sy']:.3f} ± {r['se']:.3f}")
            ax.fill_between(xline,
                            xline / (r["sy"] + 2*r["se"]),
                            xline / (r["sy"] - 2*r["se"]) if r["sy"] > 2*r["se"] else xline*0,
                            color=col, alpha=0.15, zorder=2)

        ax.axline((0, 0), slope=1/SY_ASSUMED[cid], color="gray",
                  lw=1.2, ls="--", label=f"Assumed Sy = {SY_ASSUMED[cid]:.2f}")

        ax.set_xlabel("Corrected water table rise Δh + β₃|h|  (mm/month)")
        ax.set_ylabel("Net recharge P − PET  (mm/month)")
        ax.set_title(CLUSTER_LABELS[cid], fontweight="bold")
        ax.legend(fontsize=8, framealpha=0.9)
        ax.axhline(0, color="#CCCCCC", lw=0.8)
        ax.axvline(0, color="#CCCCCC", lw=0.8)
        ax.set_facecolor("#FAFAFA")
        ax.grid(True, lw=0.4, alpha=0.5)

        if not np.isnan(r["r2"]):
            ax.text(0.97, 0.07, f"R² = {r['r2']:.3f}",
                    transform=ax.transAxes, ha="right", fontsize=9,
                    color="black", style="italic")

    # Hide any unused panels (e.g. the 6th in a 2x3 grid with 5 clusters).
    for ax in flat_axes[len(ALL_CIDS):]:
        ax.set_visible(False)

    fig.suptitle(
        "Approach A — WTF Specific Yield: Drainage-Corrected OLS Regression\n"
        "Newborough Warren 2005–2026  |  Winter months (Nov–Mar, PET < 25 mm/month)\n"
        "Δh corrected for storage decay: Δh_corr = Δh + β₃·|h_prev|",
        fontsize=10, fontweight="bold", y=1.02
    )
    plt.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Regression figure saved → {out_path.name}")


def plot_event_boxplot(b_results, out_path):
    """Figure: Sy distribution from Approach B event method."""
    fig, ax = plt.subplots(figsize=(9, 5), facecolor="white")
    ax.set_facecolor("#FAFAFA")

    cids = ALL_CIDS
    positions = list(range(1, len(cids) + 1))

    bp = ax.boxplot(
        [b_results[c]["sy_values"] for c in cids],
        positions=positions, widths=0.5, patch_artist=True,
        medianprops=dict(color="black", lw=2),
        whiskerprops=dict(lw=1.2), capprops=dict(lw=1.2),
        flierprops=dict(marker="o", markersize=3, alpha=0.4)
    )
    for patch, cid in zip(bp["boxes"], cids):
        patch.set_facecolor(CLUSTER_COLOURS[cid])
        patch.set_alpha(0.7)

    # Add assumed Sy markers
    for i, cid in enumerate(cids):
        ax.scatter(positions[i] + 0.3, SY_ASSUMED[cid],
                   marker="D", color="black", s=40, zorder=5,
                   label="Assumed Sy" if i == 0 else "")
        ax.text(positions[i], b_results[cid]["sy_median"] + 0.005,
                f"{b_results[cid]['sy_median']:.3f}",
                ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.set_xticks(positions)
    ax.set_xticklabels([CLUSTER_LABELS[c] for c in cids], fontsize=9)
    ax.set_ylabel("Specific yield Sy  (dimensionless)")
    ax.set_ylim(0, 0.45)
    ax.axhline(0.12, color="gray", lw=1.0, ls=":", alpha=0.7,
               label="Assumed Sy C2–C5 = 0.12")
    ax.axhline(0.08, color="gray", lw=1.0, ls="--", alpha=0.7,
               label="Assumed Sy C1 = 0.08")
    ax.legend(fontsize=8.5, framealpha=0.9)
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    ax.set_title(
        "Approach B — WTF Specific Yield: Event-Based Estimates\n"
        "Distribution of monthly Sy estimates from rising-limb events (Δh > 5 mm, net R > 10 mm)",
        fontsize=11, fontweight="bold"
    )
    plt.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Boxplot figure saved → {out_path.name}")


def export_csv(a_results, b_results, out_path):
    """Export summary CSV. Includes uncorrected and interception-corrected
    rows for every forested cluster (FOREST_CIDS)."""
    rows = []
    for cid in ALL_CIDS:
        a = a_results[cid]
        b = b_results[cid]
        rows.append({
            "Cluster":               CLUSTER_LABELS[cid],
            "Corrected":             False,
            "Sy_assumed":            SY_ASSUMED[cid],
            "Sy_OLS_winter":         a["sy"],
            "Sy_OLS_SE":             a["se"],
            "Sy_OLS_R2":             a["r2"],
            "Sy_OLS_n":              a["n"],
            "Sy_event_median":       b["sy_median"],
            "Sy_event_Q25":          b["q25"],
            "Sy_event_Q75":          b["q75"],
            "Sy_event_n":            b["n"],
        })
    # Interception-corrected rows for forested clusters (Freeman 2008)
    for cid in FOREST_CIDS:
        b_c = b_results[f"{cid}_corrected"]
        rows.append({
            "Cluster":               f"{CLUSTER_LABELS[cid]} (corrected)",
            "Corrected":             True,
            "Sy_assumed":            SY_ASSUMED[cid],
            "Sy_OLS_winter":         np.nan,   # OLS variant not computed for corrected
            "Sy_OLS_SE":             np.nan,
            "Sy_OLS_R2":             np.nan,
            "Sy_OLS_n":              np.nan,
            "Sy_event_median":       b_c["sy_median"],
            "Sy_event_Q25":          b_c["q25"],
            "Sy_event_Q75":          b_c["q75"],
            "Sy_event_n":            b_c["n"],
        })
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"CSV saved → {out_path.name}")


def write_summary(a_results, b_results, out_path):
    """Plain-text summary for manuscript."""
    lines = [
        "=" * 70,
        "SPECIFIC YIELD ESTIMATION — WATER TABLE FLUCTUATION METHOD",
        "Newborough Warren 2005-2026",
        "=" * 70,
        "",
        "Method: Healy and Cook (2002)",
        "  Sy = R / dh",
        "  R = net recharge (P - PET, winter months Nov-Mar, PET < 25 mm/month)",
        "  dh = corresponding water table rise",
        "",
        "APPROACH A — OLS Regression (winter months, origin-forced)",
        "-" * 70,
    ]
    for cid in ALL_CIDS:
        a = a_results[cid]
        lines.append(
            f"  {CLUSTER_LABELS[cid]:<30}  Sy = {a['sy']:.3f}  "
            f"±{a['se']:.4f} (SE)  R² = {a['r2']:.3f}  n = {a['n']}"
        )

    lines += [
        "",
        "APPROACH B — Event Median (rising limb months)",
        "-" * 70,
    ]
    for cid in ALL_CIDS:
        b = b_results[cid]
        lines.append(
            f"  {CLUSTER_LABELS[cid]:<30}  Sy = {b['sy_median']:.3f}  "
            f"IQR [{b['q25']:.3f}, {b['q75']:.3f}]  n = {b['n']}"
        )
    # Interception-corrected variants for forested clusters
    for cid in FOREST_CIDS:
        b_c = b_results[f"{cid}_corrected"]
        lines.append(
            f"  {CLUSTER_LABELS[cid] + ' (corrected)':<30}  Sy = {b_c['sy_median']:.3f}  "
            f"IQR [{b_c['q25']:.3f}, {b_c['q75']:.3f}]  n = {b_c['n']}   "
            f"[Freeman 2008; R_eff = (1 − 0.24)·P − PET]"
        )

    lines += [
        "",
        "COMPARISON WITH ASSUMED VALUES",
        "-" * 70,
        f"  {'Cluster':<30}  {'Assumed':>8}  {'OLS':>8}  {'Event':>8}",
    ]
    for cid in ALL_CIDS:
        a = a_results[cid]; b = b_results[cid]
        lines.append(
            f"  {CLUSTER_LABELS[cid]:<30}  {SY_ASSUMED[cid]:>8.3f}  "
            f"{a['sy']:>8.3f}  {b['sy_median']:>8.3f}"
        )
    for cid in FOREST_CIDS:
        b_c = b_results[f"{cid}_corrected"]
        lines.append(
            f"  {CLUSTER_LABELS[cid] + ' (corrected)':<30}  {SY_ASSUMED[cid]:>8.3f}  "
            f"{'n/a':>8}  {b_c['sy_median']:>8.3f}"
        )

    lines += [
        "",
        "NOTES",
        "-" * 70,
        "- Monthly resolution means individual storm events cannot be isolated.",
        "- Winter OLS (Approach A) is most defensible: PET negligible so",
        "  net recharge approximates actual recharge well.",
        "- Event method (Approach B) is noisier but provides uncertainty bounds.",
        "- Forested clusters (C4 Main Forest, C5 Coastal Forest) are reported as",
        "  both uncorrected and interception-corrected (Freeman 2008) variants.",
        "  The corrected variant applies R_effective = (1 − 0.24)·P − PET. PET",
        "  is not reduced because Thornthwaite PET is an energy-based atmospheric",
        "  demand (independent of land cover), so reducing only P is physically",
        "  consistent and not double-counting. The interception fraction was",
        "  measured at C5 and applied across both forested clusters. The",
        "  corrected medians may exceed uncorrected through interaction with",
        "  the Sy < 0.50 plausibility filter, which readmits previously-excluded",
        "  high-Sy months into the event pool (see wtf_interception_methodology.md).",
        "- Both approaches give indicative Sy only; slug tests or pumping tests",
        "  at representative wells per cluster remain the gold standard.",
        "- Reference: Healy, R.W. and Cook, P.G. (2002) Hydrogeology Journal",
        "  10, 91-109. doi:10.1007/s10040-001-0178-0",
        "- Reference: Freeman, S. (2008) Hydrological impact of Corsican pine",
        "  at Newborough Warren.",
        "",
    ]

    out_path.write_text("\n".join(lines))
    print(f"Summary saved → {out_path.name}")


def main():
    # ── Paths ──────────────────────────────────────────────────────────────────
    script_dir   = Path(__file__).parent
    project_root = script_dir.parent

    out_root     = OUT_DIR
    out_dir      = DIR_17
    path_table   = OUT_17_SY_TABLE
    path_reg     = OUT_17_REGRESSION
    path_box     = OUT_17_BOXPLOT
    path_summary = OUT_17_SUMMARY

    # ── Run ────────────────────────────────────────────────────────────────────
    print("Loading data...")
    df = load_data()
    print(f"  {len(df)} monthly records, "
          f"{df['Date'].min().date()} to {df['Date'].max().date()}")

    print("\nApproach A — OLS regression (winter months, drainage-corrected):")
    a_results = approach_a_ols(df)

    print("\nApproach B — Event-based median:")
    b_results = approach_b_events(df)

    print("\nGenerating figures...")
    plot_regression(df, a_results, path_reg)
    plot_event_boxplot(b_results, path_box)

    print("\nExporting outputs...")
    export_csv(a_results, b_results, path_table)
    write_summary(a_results, b_results, path_summary)

    # Update consolidated pipeline params with Sy values
    try:
        from utils.pipeline_params import update_specific_yield
        sy_df = pd.read_csv(path_table)
        sy_dict = {}
        for cid in range(1, 6):
            label = CLUSTER_LABELS.get(cid, f"C{cid}")
            # Prefer interception-corrected for forest clusters
            corr_row = sy_df[sy_df["Cluster"].str.contains("corrected", case=False)
                             & sy_df["Cluster"].str.startswith(label)]
            base_row = sy_df[~sy_df["Cluster"].str.contains("corrected", case=False, na=False)
                             & sy_df["Cluster"].str.startswith(label)]
            row = corr_row if cid in FOREST_CIDS and not corr_row.empty else base_row
            if not row.empty and pd.notna(row["Sy_event_median"].iloc[0]):
                sy_dict[cid] = float(row["Sy_event_median"].iloc[0])
        if sy_dict:
            update_specific_yield(sy_dict)
    except Exception as e:
        print(f"  [note] Pipeline params Sy update skipped: {e}")

    print("\nAll outputs written to", out_dir)


if __name__ == '__main__':
    main()
