"""
02_clustering.py
Purpose: Performs Ward's Variance Minimisation on the 2026 Reference Network
to establish the core hydrogeological clusters.

Inputs:
    01_wells_reference.csv

Outputs (intermediate):
    02_cluster_stats.csv

Outputs (final — outputs/02_clustering/):
    02_01_dendrogram.png
    02_02_validation_plots.png
"""

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
del _sys, _os

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import silhouette_score

from utils.config import CLUSTER_COLOURS
from utils.data_utils import normalize_well_name
from utils.paths import (
    make_all_dirs,
    INT_CLIMATE, INT_WELLS_CLEAN, INT_CLUSTER_STATS,
    INT_WELLS_REFERENCE,
    OUT_02_DENDROGRAM, OUT_02_VALIDATION, OUT_02_CLUSTER_HYDRO_WB,
)

NUM_CLUSTERS = 6
REFERENCE_CUTOFF = pd.Timestamp("2026-02-01")
MIN_RECORD_MONTHS = 100
DETREND_START = pd.Timestamp("2004-12-01")
DETREND_END = pd.Timestamp("2025-12-01")

COLOURS = {
    1: "#E69F00",
    2: "#009E73",
    3: "#CC79A7",
    4: "#D55E00",
    5: "#56B4E9",
    6: "#0072B2",
}
LABELS = {
    1: "C1: Eastern Block Lake-buffer",
    2: "C2: Eastern Block Mature Dune",
    3: "C3: Western Block Mature Dune",
    4: "C4: Forest",
    5: "C5: Coastal",
    6: "C6: Lake",
}
LINES = {1: "-", 2: "-", 3: "-", 4: "--", 5: ":", 6: "-."}
LW = {1: 1.8, 2: 1.8, 3: 1.8, 4: 1.8, 5: 1.5, 6: 1.5}

plt.rcParams.update({"font.family": "sans-serif", "axes.labelsize": 12})


def cluster_id_from_value(value) -> int | None:
    text = str(value).strip()
    if text.startswith("C") and len(text) > 1 and text[1].isdigit():
        digits = "".join(ch for ch in text[1:] if ch.isdigit())
        return int(digits) if digits else None
    if text.isdigit():
        return int(text)
    try:
        return int(float(text))
    except Exception:
        return None


def make_cluster_hydrograph_wb_figure() -> None:
    """Create 02_03 with top panel matching script 00 short water-balance panel."""
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True).sort_index()
    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True).sort_index()
    wells = wells.apply(pd.to_numeric, errors="coerce")

    # Match script 00 short-profile well selection and overlap window exactly.
    subset = wells.loc[wells.index <= REFERENCE_CUTOFF].copy()
    valid_counts = subset.notna().sum(axis=0)
    keep = valid_counts[valid_counts >= MIN_RECORD_MONTHS].index.tolist()
    wells_short = wells[keep].copy()
    row_has_any_obs = wells_short.notna().any(axis=1)
    if not row_has_any_obs.any():
        raise ValueError("No valid well observations found for short-profile overlap window.")

    overlap_idx = wells_short.index[row_has_any_obs]
    analysis_start = overlap_idx.min()
    analysis_end = overlap_idx.max()

    climate_clip = climate.loc[(climate.index >= analysis_start) & (climate.index <= analysis_end)].copy()
    climate_clip["P_mm"] = climate_clip["P_m"] * 1000.0
    climate_clip["PET_mm"] = climate_clip["PET"] * 1000.0

    # Match script 00 short-profile detrending baseline.
    full_balance = (climate["P_m"] * 1000.0) - (climate["PET"] * 1000.0)
    detrend_window = full_balance.loc[(full_balance.index >= DETREND_START) & (full_balance.index <= DETREND_END)]
    if detrend_window.empty:
        raise ValueError("No climate rows in detrending window Dec 2004-Dec 2025.")
    detrend_mean = float(detrend_window.mean(skipna=True))

    net_balance = climate_clip["P_mm"] - climate_clip["PET_mm"]
    net_corrected = net_balance - detrend_mean
    cum_balance_corrected = net_corrected.fillna(0).cumsum()
    net_roll_12 = net_corrected.rolling(12, min_periods=6).mean()

    # Suppress 12-month trend in first 12 months, same as script 00 short.
    if len(climate_clip.index) >= 12:
        trend_mask = np.arange(len(climate_clip.index)) >= 12
        net_roll_12_plot = net_roll_12.where(trend_mask, np.nan)
    else:
        net_roll_12_plot = net_roll_12 * np.nan

    # Build cluster hydrographs directly from wells_clean and cluster assignments
    # so this figure is self-contained and independent of script 03 output.
    # Uses raw depth-to-water (not mAOD) so the y-axis reflects actual water
    # table depth below ground surface.
    cluster_df_local = pd.read_csv(INT_CLUSTER_STATS)
    wells_all = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells_all = wells_all.apply(pd.to_numeric, errors="coerce")

    regional = pd.DataFrame(index=wells_all.index)
    for cid in range(1, 7):
        members = cluster_df_local[
            pd.to_numeric(cluster_df_local["Cluster"], errors="coerce") == cid
        ]["Name_Original"].astype(str).values
        available = [c for c in members if c in wells_all.columns]
        if available:
            regional[f"C{cid}"] = wells_all[available].mean(axis=1)

    regional = regional.loc[
        (regional.index >= "2006-12-01") & (regional.index <= "2025-12-01")
    ]

    dates = climate_clip.index
    print(
        f"Long-term mean P-PET ({DETREND_START.date()} to {DETREND_END.date()}): "
        f"{detrend_mean:.2f} mm/month"
    )
    print(
        f"Study period: {dates.min().date()} to {dates.max().date()} "
        f"({len(dates)} months)"
    )
    print(
        f"Cumulative anomaly range: {cum_balance_corrected.min():.1f} to "
        f"{cum_balance_corrected.max():.1f} mm"
    )

    fig = plt.figure(figsize=(13, 8), dpi=300)
    gs = GridSpec(2, 1, height_ratios=[1, 2.8], hspace=0.08)

    ax_wb = fig.add_subplot(gs[0])
    ax_h = fig.add_subplot(gs[1], sharex=ax_wb)

    # Panel (a): copied styling/logic from script 00 short water-balance panel.
    ax_wb.plot(dates, cum_balance_corrected, color="#0072B2", linewidth=2.2, label="Leveled cumulative (P-PET)")
    ax_wb.plot(
        dates,
        net_roll_12_plot,
        color="#D55E00",
        linewidth=1.5,
        linestyle="--",
        label="12-month rolling mean (corrected net)",
    )
    ax_wb.axhline(0, color="black", linestyle=":", linewidth=1.0, alpha=0.7)
    ax_wb.set_ylabel("Water balance (mm)", fontsize=9)
    ax_wb.grid(axis="y", linestyle=":", alpha=0.35)
    ax_wb.legend(loc="upper left", frameon=False, ncol=1, fontsize=8)
    ax_wb.tick_params(labelbottom=False, bottom=False)
    ax_wb.set_title("(a)", fontsize=9, loc="left", pad=3)
    ax_wb.xaxis.set_major_locator(mdates.YearLocator(5))
    ax_wb.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax_wb.tick_params(axis="x", rotation=45)
    ax_wb.text(
        0.99,
        0.96,
        f"Detrending mean (Dec 2004-Dec 2025): {detrend_mean:+.2f} mm/month",
        transform=ax_wb.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7, "pad": 2.0},
    )

    # Panel (b): cluster hydrographs.
    for cid in range(1, 7):
        ax_h.plot(
            regional.index,
            regional[f"C{cid}"].values,
            color=COLOURS[cid],
            label=LABELS[cid],
            lw=LW[cid],
            ls=LINES[cid],
            alpha=0.92,
        )

    ax_h.axhline(0, color="black", lw=0.7, ls=":", alpha=0.35)
    ax_h.set_ylabel("Relative water level (m)", fontsize=9)
    ax_h.set_xlabel("Date", fontsize=9)
    ax_h.yaxis.set_major_locator(ticker.MultipleLocator(0.25))
    ax_h.legend(fontsize=7.8, loc="lower right", framealpha=0.92, ncol=2)
    ax_h.set_title("(b)", fontsize=9, loc="left", pad=3)
    for sp in ["top", "right"]:
        ax_h.spines[sp].set_visible(False)
    ax_h.grid(True, axis="y", lw=0.4, ls="--", alpha=0.4)
    ax_h.xaxis.set_major_locator(mdates.YearLocator(2))
    ax_h.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.setp(ax_h.xaxis.get_majorticklabels(), rotation=0, ha="center", fontsize=8)

    plt.savefig(OUT_02_CLUSTER_HYDRO_WB, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f" -> Saved: {OUT_02_CLUSTER_HYDRO_WB.name}")


if __name__ == "__main__":
    make_all_dirs()
    print("--- Starting 02: Reference Clustering ---")

    if not INT_WELLS_REFERENCE.exists():
        print(f"Reference data not found: {INT_WELLS_REFERENCE}. Run 01 first.")
        sys.exit(1)

    wells_ref = pd.read_csv(INT_WELLS_REFERENCE, index_col=0, parse_dates=True)
    wells_ref = wells_ref.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    print(f" -> Clustering {len(wells_ref.columns)} reference wells...")

    corr_matrix = wells_ref.corr()
    dist_array  = pdist(1 - corr_matrix.fillna(0))
    dist_square = squareform(dist_array)
    Z = linkage(dist_array, method="ward")

    # Validation plots
    print(" -> Generating Cluster Validation Plots...")
    cluster_range      = range(2, 11)
    silhouette_scores  = []
    linkage_distances  = []
    for k in cluster_range:
        labels = fcluster(Z, t=k, criterion="maxclust")
        silhouette_scores.append(silhouette_score(dist_square, labels, metric="precomputed"))
        linkage_distances.append(Z[-k, 2])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
    ax1.plot(cluster_range, linkage_distances, marker="o", color="#0072B2")
    ax1.axvline(x=NUM_CLUSTERS, color="red", linestyle="--", label=f"Chosen k={NUM_CLUSTERS}")
    ax1.set_title("Elbow Method (Ward's Distance)", fontweight="bold")
    ax1.set_xlabel("Number of Clusters (k)"); ax1.set_ylabel("Merge Distance")
    ax1.grid(True, linestyle="--", alpha=0.6); ax1.legend()
    ax2.plot(cluster_range, silhouette_scores, marker="s", color="#D55E00")
    ax2.axvline(x=NUM_CLUSTERS, color="red", linestyle="--", label=f"Chosen k={NUM_CLUSTERS}")
    ax2.set_title("Silhouette Score Validation", fontweight="bold")
    ax2.set_xlabel("Number of Clusters (k)"); ax2.set_ylabel("Silhouette Coefficient")
    ax2.grid(True, linestyle="--", alpha=0.6); ax2.legend()
    plt.tight_layout()
    plt.savefig(OUT_02_VALIDATION)
    plt.close()
    print(f" -> Saved: {OUT_02_VALIDATION.name}")

    # Cluster assignments
    sub_clusters = fcluster(Z, t=NUM_CLUSTERS, criterion="maxclust")
    user_labels = {
        1: "C1 Eastern Block Lake",
        2: "C2 Eastern Block Mature Dune",
        3: "C3 Western Block Mature Dune",
        4: "C4 Forest",
        5: "C5 Coastal",
        6: "C6 Lake",
    }
    cluster_df = pd.DataFrame({
        "Match_ID":     [normalize_well_name(col) for col in wells_ref.columns],
        "Name_Original": [str(col) for col in wells_ref.columns],
        "Cluster":      sub_clusters,
    })
    cluster_df["Cluster_Label"] = cluster_df["Cluster"].map(user_labels).fillna(
        cluster_df["Cluster"].apply(lambda c: f"C{int(c)}")
    )
    cluster_df.to_csv(INT_CLUSTER_STATS, index=False)
    print(f" -> Saved cluster stats: {INT_CLUSTER_STATS.name}")

    # Dendrogram
    print(" -> Generating Dendrogram...")
    plt.figure(figsize=(15, 8), dpi=300)
    plt.title("Reference Network Behavioural Clustering (2026 Baseline)",
              fontsize=14, fontweight="bold")
    dendro = dendrogram(
        Z, labels=wells_ref.columns, leaf_rotation=90.0, leaf_font_size=8.0,
        color_threshold=Z[-NUM_CLUSTERS, 2], above_threshold_color="#BBBBBB",
    )
    label_to_cluster = {}
    for _, row in cluster_df.iterrows():
        cid = cluster_id_from_value(row["Cluster_Label"])
        if cid is not None:
            label_to_cluster[normalize_well_name(row["Name_Original"])] = cid
    for tick in plt.gca().get_xmajorticklabels():
        cid = label_to_cluster.get(normalize_well_name(tick.get_text()))
        if cid in CLUSTER_COLOURS:
            tick.set_color(CLUSTER_COLOURS[cid])
    leaf_clusters = [label_to_cluster.get(normalize_well_name(lbl), None) for lbl in dendro["ivl"]]
    leaf_idx_to_cluster = {i: cid for i, cid in enumerate(leaf_clusters) if cid is not None}
    ax = plt.gca()
    for xs, ys in zip(dendro["icoord"], dendro["dcoord"]):
        leaf_xs = [int(round(x)) for x in xs if x % 10 == 5]
        if not leaf_xs:
            continue
        leaf_idx = (min(leaf_xs) - 5) // 10
        cid = leaf_idx_to_cluster.get(leaf_idx, None)
        ax.plot(xs, ys, color=CLUSTER_COLOURS.get(cid, "#BBBBBB"), lw=2.2, zorder=2)
    plt.legend(
        handles=[plt.Line2D([0], [0], color=CLUSTER_COLOURS[c], lw=3,
                            label=user_labels.get(c, f"C{c}"))
                 for c in sorted(CLUSTER_COLOURS.keys())],
        title="Cluster Assignments", loc="upper left", frameon=True,
    )
    plt.ylabel("Ward Linkage Distance", fontsize=12)
    plt.tight_layout()
    plt.savefig(OUT_02_DENDROGRAM)
    plt.close()

    print(" -> Generating Cluster Hydrograph + Water-Balance Figure...")
    make_cluster_hydrograph_wb_figure()

    print("-> Clustering Complete.")
