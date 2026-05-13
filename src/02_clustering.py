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
from sklearn.metrics import silhouette_score, calinski_harabasz_score

from utils.config import (
    CLUSTER_COLOURS, CLUSTER_COLOURS_BW, CLUSTER_LABELS,
    REFERENCE_CUTOFF_DATE, BW_MODE, BW_LINESTYLES,
)
from utils.data_utils import normalize_well_name
from utils.paths import (
    make_all_dirs,
    INT_CLIMATE, INT_WELLS_CLEAN, INT_CLUSTER_STATS,
    INT_WELLS_REFERENCE,
    OUT_02_DENDROGRAM, OUT_02_VALIDATION, OUT_02_CLUSTER_HYDRO_WB,
    OUT_02_VALIDATION_EXTENDED, OUT_02_STABILITY_SUMMARY,
    OUT_02_STABILITY_PER_WELL, OUT_02_COASSIGN_HEATMAP,
    OUT_02_MEMBERSHIP_SWEEP,
    OUT_02_AMP_PER_WELL, OUT_02_AMP_SUMMARY, OUT_02_AMP_BOXPLOT,
)

NUM_CLUSTERS = 5
# Ward's k equals the final cluster count: no manual overrides. See the
# CLUSTER_PARTITIONING_CONFIG comment block below for the audit trail of
# how this partition was arrived at.
WARDS_K = 5
REFERENCE_CUTOFF = pd.Timestamp(REFERENCE_CUTOFF_DATE)
MIN_RECORD_MONTHS = 100
DETREND_START = pd.Timestamp("2004-12-01")
DETREND_END = pd.Timestamp("2025-12-01")

# ──────────────────────────────────────────────────────────────────────────────
# CLIMATE NORMALISATION for the amplitude descriptors (Section 4.2).
#
# The post-2018 window is disproportionately drought-weighted relative to the
# pre-window, which inflates raw p90-p10 estimates. These three study-period
# summers were identified empirically from RAF Valley Jun-Sep rainfall totals
# against the 1931-2017 long-term mean (260 mm, sigma 70 mm) using a
# one-sigma-below-mean threshold (~190 mm). They are hard-coded here so
# Script 02 does not need to reparse raw RAF Valley data, and so the
# normalisation is auditable: only change if the RAF Valley data itself is
# updated and the underlying thresholding recomputed.
# ──────────────────────────────────────────────────────────────────────────────
DROUGHT_SUMMERS = (2005, 2018, 2022)

# Amplitude descriptor windows and thresholds.
AMP_SPLIT_DATE        = pd.Timestamp("2018-01-01")
AMP_MIN_OBS_PER_WIN   = 24          # months required for a window stat
AMP_SUMMER_MONTHS     = (6, 7, 8, 9)


# ──────────────────────────────────────────────────────────────────────────────
# CLUSTER PARTITIONING — Ward's k=5 on the 66-well reference network
#
# The reference network is defined in 01_data_prep.py. Four groups of wells
# are excluded from that network on physical grounds (detailed rationale in
# 01_data_prep.py):
#
#   - FE1-4 and LIS1          — post-2017 clearfell non-stationarity
#   - Llyn Rhos               — lake surface, not a water-table response
#   - CEH3 and CEH22          — tidal-signal contamination (Ward's
#                               consistently identifies them as singleton
#                               outliers, resistant to grouping at every k)
#
# Ward's variance-minimisation on (1 - Pearson correlation) distance on the
# resulting 66-well network produces five behaviourally coherent clusters
# that also map onto clean spatial groupings at the site:
#
#   1. Lake              (n=7)   — wells around the eastern lake system
#   2. Dune              (n=26)  — central-east mature dune system
#   3. Western Residual  (n=19)  — mid-west open ground + coastal-adjacent
#   4. Main Forest       (n=9)   — mature inland forest block
#   5. Coastal Forest    (n=5)   — coastal-edge forest strip
#
# The Western Residual cluster contains two geographically distinguishable
# sub-populations (the low-ground southern coastal fringe including ceh4,
# ceh18, ceh21, ceh36, ceh42; and the west-side open dune wells including
# nw1, nw2, nw5-7, nw11, nw13). Ward's on the cleaned pipeline data does
# NOT separate these at any k from 5 to 9 — they share a common behavioural
# signature at the resolution the algorithm achieves. This is noted as a
# landscape/behaviour distinction in the methods section (Section 3.2).
#
# Silhouette at k=5 = 0.39 on this network; Calinski-Harabasz and merge
# distance confirm the five-cluster solution. Bootstrap stability at k=5
# shows high within-cluster co-assignment for the four tight groups (Main
# Forest, Lake, Dune, Coastal Forest — all median stability >= 0.95) with
# moderate stability for the Western Residual (~0.43) reflecting its
# landscape heterogeneity.
#
# Methods note: CEH11 is the weakest member of the Lake cluster (bootstrap
# co-assignment ~0.71); this is flagged in the report as a borderline
# membership.
#
# Cluster IDs are deterministically re-numbered after Ward's by anchor-well
# identity, so the integer IDs are stable across re-runs regardless of the
# arbitrary order fcluster assigns them. The numbering below MUST agree with
# utils/config.CLUSTER_LABELS — the guard immediately after this dict
# asserts that on import.
#
#   Cluster 1 = Lake               (anchors: ceh5, ceh11)
#   Cluster 2 = Dune               (anchors: d10)
#   Cluster 3 = Western Residual   (anchors: nw1)
#   Cluster 4 = Main Forest        (anchors: ceh2)
#   Cluster 5 = Coastal Forest     (anchors: ceh16, nw9)
#
# Human-readable labels are defined in utils/config.CLUSTER_LABELS.
# ──────────────────────────────────────────────────────────────────────────────
CLUSTER_ID_ANCHORS: dict[int, tuple[str, ...]] = {
    1: ("ceh5", "ceh11"),      # Lake (ceh11 weakest member, flag in methods)
    2: ("d10",),               # Dune
    3: ("nw1",),               # Western Residual
    4: ("ceh2",),              # Main Forest
    5: ("ceh16", "nw9"),       # Coastal Forest
}

# Guard: anchors and config labels must describe the same cluster IDs.
# This catches the failure mode where one is updated without the other —
# the previous head-of-file comment block disagreed with config.py for an
# entire run cycle before being noticed downstream.
_anchor_ids = set(CLUSTER_ID_ANCHORS.keys())
_label_ids  = set(CLUSTER_LABELS.keys())
if _anchor_ids != _label_ids:
    raise RuntimeError(
        f"CLUSTER_ID_ANCHORS keys {sorted(_anchor_ids)} disagree with "
        f"utils.config.CLUSTER_LABELS keys {sorted(_label_ids)}. "
        f"One has been updated without the other."
    )
del _anchor_ids, _label_ids

# ──────────────────────────────────────────────────────────────────────────────
# STABILITY DIAGNOSTICS CONFIG
#
# Bootstrap resampling estimates how sensitive cluster assignments are to the
# particular set of wells observed. For each k in K_RANGE_BOOTSTRAP we resample
# the reference wells with replacement N_BOOTSTRAP times, recluster, and
# accumulate co-assignment frequencies. Per-well stability is then the fraction
# of bootstraps in which the well co-assigns with its majority cluster.
#
# N_BOOTSTRAP = 1000 is the value called out in the rebuild handover. Runtime
# with 69 wells, k=4..7, and Ward's on a 69×69 distance matrix is a couple of
# minutes on a typical laptop. Reduce N_BOOTSTRAP for faster iteration; reduce
# K_RANGE_BOOTSTRAP if only interested in a specific k.
# ──────────────────────────────────────────────────────────────────────────────
N_BOOTSTRAP = 1000
K_RANGE_BOOTSTRAP = (4, 5, 6, 7)
BOOTSTRAP_SEED = 20260424

# Local styling for cluster hydrograph panel. Colours and labels come from
# utils/config.py (CLUSTER_COLOURS, CLUSTER_LABELS); line styles and widths
# are specific to this script's hydrograph figure.
LINES = {1: "-", 2: "-", 3: "-", 4: "--", 5: ":", 6: "-."}
LW    = {1: 1.8, 2: 1.8, 3: 1.8, 4: 1.8, 5: 1.5, 6: 1.5}

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


def _remap_cluster_ids_by_anchor(
    raw_labels: np.ndarray,
    well_names: list[str],
    anchors: dict[int, tuple[str, ...]],
) -> dict[int, int]:
    """
    Map fcluster's arbitrary integer IDs to the canonical IDs defined by
    CLUSTER_ID_ANCHORS. For each canonical ID, locate its anchor wells in
    the raw labelling and confirm they share a single raw cluster — that raw
    cluster is mapped to the canonical ID.

    Any raw cluster that doesn't match an anchor is assigned to the one
    canonical ID not already claimed (this is the residual cluster).

    Returns a dict {raw_id: canonical_id}. Raises ValueError if anchor wells
    land in different raw clusters (clustering has changed enough that the
    anchor assumptions are violated — the partition needs re-examining).
    """
    raw_by_well = dict(zip(well_names, raw_labels))
    name_to_norm = {w: normalize_well_name(w) for w in well_names}
    norm_to_raw = {name_to_norm[w]: raw for w, raw in raw_by_well.items()}

    raw_to_canonical: dict[int, int] = {}
    claimed_canonical: set[int] = set()
    for canonical_id, anchor_list in anchors.items():
        raw_ids_for_anchors = set()
        missing_anchors = []
        for anchor in anchor_list:
            anchor_norm = normalize_well_name(anchor)
            if anchor_norm not in norm_to_raw:
                missing_anchors.append(anchor)
                continue
            raw_ids_for_anchors.add(int(norm_to_raw[anchor_norm]))
        if missing_anchors:
            raise ValueError(
                f"Anchor wells {missing_anchors} for canonical cluster "
                f"{canonical_id} not found in the reference network. "
                f"Check the whitelist in 01_data_prep.py."
            )
        if len(raw_ids_for_anchors) != 1:
            raise ValueError(
                f"Anchor wells {anchor_list} for canonical cluster "
                f"{canonical_id} landed in different Ward's clusters "
                f"{raw_ids_for_anchors}. The partition assumptions in "
                f"CLUSTER_ID_ANCHORS may need re-examining."
            )
        raw_id = raw_ids_for_anchors.pop()
        if raw_id in raw_to_canonical:
            raise ValueError(
                f"Raw Ward's cluster {raw_id} already claimed by canonical "
                f"{raw_to_canonical[raw_id]}, cannot also be {canonical_id}. "
                f"Check CLUSTER_ID_ANCHORS for conflicting anchors."
            )
        raw_to_canonical[raw_id] = canonical_id
        claimed_canonical.add(canonical_id)

    # Unclaimed raw clusters -> unclaimed canonical IDs
    all_raw = set(int(x) for x in raw_labels)
    unclaimed_raw = sorted(all_raw - set(raw_to_canonical.keys()))
    all_canonical = set(anchors.keys())
    unclaimed_canonical = sorted(all_canonical - claimed_canonical)
    if len(unclaimed_raw) != len(unclaimed_canonical):
        raise ValueError(
            f"Cannot assign remaining raw clusters {unclaimed_raw} to "
            f"canonical IDs {unclaimed_canonical} — counts differ. This "
            f"means Ward's produced a different number of clusters than "
            f"expected, or the anchor set is inconsistent."
        )
    for raw_id, canonical_id in zip(unclaimed_raw, unclaimed_canonical):
        raw_to_canonical[raw_id] = canonical_id

    return raw_to_canonical


def _correlation_distance(wells: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Return (condensed distance vector, square distance matrix) from 1 - r."""
    corr = wells.corr().fillna(0).values
    square = 1.0 - corr
    # Guard against tiny numerical negatives on the diagonal / near-identical series.
    square = np.clip(square, 0.0, None)
    np.fill_diagonal(square, 0.0)
    # Force symmetry (pandas.corr should already be symmetric to machine precision).
    square = (square + square.T) / 2.0
    condensed = squareform(square, checks=False)
    return condensed, square


def k_sweep_validation(wells_ref: pd.DataFrame, k_values: range) -> pd.DataFrame:
    """
    Evaluate silhouette, Calinski-Harabasz, and Ward merge-distance at every k
    in k_values. Returns a DataFrame indexed by k.

    Silhouette works on the precomputed correlation-distance matrix; Calinski-
    Harabasz works on the raw time-series matrix (wells-as-samples, months-as-
    features). The two metrics can disagree — if they do, that is informative
    about how well the chosen k separates the data.
    """
    _, dist_square = _correlation_distance(wells_ref)
    Z = linkage(squareform(dist_square, checks=False), method="ward")

    # Transpose so rows = wells (samples), columns = months (features). Fill
    # gaps with each well's mean so CH has a dense matrix to work with; this
    # is a diagnostic approximation, not used for clustering itself.
    features = wells_ref.T
    features = features.apply(lambda col: col.fillna(col.mean()), axis=1)
    features_array = features.values

    rows = []
    for k in k_values:
        labels = fcluster(Z, t=k, criterion="maxclust")
        sil = silhouette_score(dist_square, labels, metric="precomputed")
        # Calinski-Harabasz requires at least 2 clusters and more than k samples.
        try:
            ch = calinski_harabasz_score(features_array, labels)
        except ValueError:
            ch = np.nan
        merge_dist = Z[-k, 2] if k <= len(Z) else np.nan
        n_per_cluster = pd.Series(labels).value_counts().sort_index().to_list()
        rows.append({
            "k": k,
            "silhouette": sil,
            "calinski_harabasz": ch,
            "merge_distance": merge_dist,
            "min_cluster_size": min(n_per_cluster),
            "max_cluster_size": max(n_per_cluster),
            "n_singletons": sum(1 for n in n_per_cluster if n == 1),
        })
    return pd.DataFrame(rows).set_index("k")


def bootstrap_cluster_stability(
    wells_ref: pd.DataFrame,
    k: int,
    n_boot: int = N_BOOTSTRAP,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[pd.Series, pd.DataFrame]:
    """
    Bootstrap-resample the columns of wells_ref n_boot times, re-cluster at k,
    accumulate pairwise co-assignment counts, and return:

      per_well_stability : pd.Series indexed by well name, value = fraction of
          bootstraps in which the well was co-assigned with its modal partner
          set (a well's stability is 1.0 if it always groups with the same
          neighbours; lower if its assignment depends on which wells were
          resampled).

      coassign_prob : pd.DataFrame (wells × wells) of pairwise co-assignment
          probability. Diagonal = 1. Off-diagonal in [0, 1].

    Implementation notes:
      - Resampling is with replacement over well columns. Each bootstrap fits
        Ward's on the resampled distance matrix.
      - A well may appear 0, 1, or more times in a given bootstrap. When
        accumulating co-assignment, we count the pair (i,j) each time both
        appear in the bootstrap (denominator) and count co-assignment when
        they land in the same cluster (numerator).
      - Per-well stability is the median of the well's off-diagonal co-
        assignment probabilities with members of its cluster in the reference
        (full-sample) fit. This is the "does this well stick with its
        neighbours" interpretation from the handover.
    """
    rng = np.random.default_rng(seed)
    wells = wells_ref.columns.tolist()
    n_wells = len(wells)
    well_idx = {w: i for i, w in enumerate(wells)}

    # Reference clustering on the full sample — used to label the 'final' cluster
    # for each well, against which stability is judged.
    _, dist_full = _correlation_distance(wells_ref)
    Z_full = linkage(squareform(dist_full, checks=False), method="ward")
    labels_full = fcluster(Z_full, t=k, criterion="maxclust")
    ref_labels = pd.Series(labels_full, index=wells)

    # Accumulators: numerator = #bootstraps where both wells i,j appear and land
    # in the same cluster; denominator = #bootstraps where both appear.
    coassign_num = np.zeros((n_wells, n_wells), dtype=np.int64)
    coassign_den = np.zeros((n_wells, n_wells), dtype=np.int64)

    for b in range(n_boot):
        sample_idx = rng.integers(0, n_wells, size=n_wells)
        sample_wells = [wells[i] for i in sample_idx]
        sample_df = wells_ref.iloc[:, sample_idx]
        # Duplicate column names from resampling with replacement — deduplicate
        # for correlation but remember mapping back to original well indices.
        sample_df = sample_df.copy()
        sample_df.columns = [f"{w}__{j}" for j, w in enumerate(sample_wells)]

        try:
            _, d_square = _correlation_distance(sample_df)
            Z_b = linkage(squareform(d_square, checks=False), method="ward")
            labels_b = fcluster(Z_b, t=k, criterion="maxclust")
        except Exception:
            # Degenerate bootstrap (e.g. all columns identical) — skip.
            continue

        # Map bootstrap column position -> original well index -> cluster label.
        orig_indices = [well_idx[w] for w in sample_wells]
        # Build per-original-well cluster assignments for this bootstrap.
        # If a well was resampled multiple times we take its first appearance;
        # this is the standard treatment and doesn't bias the pairwise counts.
        seen: dict[int, int] = {}
        for pos, oi in enumerate(orig_indices):
            if oi not in seen:
                seen[oi] = labels_b[pos]
        present = list(seen.keys())
        for a_i, a in enumerate(present):
            for b_i in range(a_i, len(present)):
                bwell = present[b_i]
                coassign_den[a, bwell] += 1
                coassign_den[bwell, a] += 1
                if seen[a] == seen[bwell]:
                    coassign_num[a, bwell] += 1
                    coassign_num[bwell, a] += 1

    with np.errstate(invalid="ignore", divide="ignore"):
        coassign_prob = np.where(coassign_den > 0, coassign_num / coassign_den, np.nan)
    # Diagonal should be 1 where the well ever appeared.
    np.fill_diagonal(coassign_prob, 1.0)

    coassign_df = pd.DataFrame(coassign_prob, index=wells, columns=wells)

    # Per-well stability: median co-assignment probability with its reference-fit
    # cluster-mates (excluding itself). If a well is alone in its reference
    # cluster, stability is NaN.
    stability_scores = {}
    for well in wells:
        mates = ref_labels.index[(ref_labels == ref_labels.loc[well]) & (ref_labels.index != well)]
        if len(mates) == 0:
            stability_scores[well] = np.nan
        else:
            stability_scores[well] = coassign_df.loc[well, mates].median()
    per_well_stability = pd.Series(stability_scores, name="stability")

    return per_well_stability, coassign_df


def plot_coassignment_heatmap(coassign_df: pd.DataFrame, ref_labels: pd.Series,
                              k: int, out_path) -> None:
    """Heatmap of pairwise co-assignment, ordered by reference cluster."""
    order = ref_labels.sort_values().index.tolist()
    M = coassign_df.loc[order, order].values

    fig, ax = plt.subplots(figsize=(9, 8), dpi=200)
    im = ax.imshow(M, cmap="RdYlGn", vmin=0, vmax=1, aspect="equal")
    # Cluster boundaries as black lines between groups.
    ordered_labels = ref_labels.loc[order].values
    boundaries = np.where(np.diff(ordered_labels) != 0)[0] + 1
    for bnd in boundaries:
        ax.axhline(bnd - 0.5, color="black", lw=0.8)
        ax.axvline(bnd - 0.5, color="black", lw=0.8)
    ax.set_title(f"Bootstrap co-assignment probability, k={k}\n"
                 f"({N_BOOTSTRAP} resamples; rows/cols ordered by reference cluster)",
                 fontsize=10)
    ax.set_xticks(range(len(order)))
    ax.set_yticks(range(len(order)))
    ax.set_xticklabels(order, rotation=90, fontsize=5)
    ax.set_yticklabels(order, fontsize=5)
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("co-assignment prob.", fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def run_stability_diagnostics(wells_ref: pd.DataFrame) -> None:
    """
    Runs the full stability-diagnostics block:

      1. k-sweep (silhouette, Calinski-Harabasz, merge distance) over k=2..10
      2. Bootstrap stability at each k in K_RANGE_BOOTSTRAP
      3. Writes per-well stability CSV, per-k membership CSVs, summary CSV,
         and a co-assignment heatmap per k
      4. Prints cluster memberships at each candidate k so forest-wells-
         aggregation can be inspected

    Outputs land in outputs/02_clustering/.
    """
    print("\n--- Cluster Stability Diagnostics ---")

    # 1. k-sweep
    print(" -> k-sweep validation (k=2..10)...")
    sweep = k_sweep_validation(wells_ref, range(2, 11))
    print(sweep.round(3).to_string())
    best_sil_k = int(sweep["silhouette"].idxmax())
    best_ch_k  = int(sweep["calinski_harabasz"].idxmax())
    print(f"    Silhouette favours k = {best_sil_k}")
    print(f"    Calinski-Harabasz favours k = {best_ch_k}")

    # Extended validation plot: silhouette, CH, merge distance
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), dpi=200)
    axes[0].plot(sweep.index, sweep["silhouette"], marker="o", color="#D55E00")
    axes[0].axvline(NUM_CLUSTERS, color="red", ls="--", alpha=0.6, label=f"current k={NUM_CLUSTERS}")
    axes[0].axvline(best_sil_k, color="green", ls=":", alpha=0.8, label=f"peak k={best_sil_k}")
    axes[0].set_title("Silhouette (higher = better)", fontweight="bold")
    axes[0].set_xlabel("k"); axes[0].set_ylabel("Silhouette"); axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.4, ls="--")

    axes[1].plot(sweep.index, sweep["calinski_harabasz"], marker="s", color="#0072B2")
    axes[1].axvline(NUM_CLUSTERS, color="red", ls="--", alpha=0.6)
    axes[1].axvline(best_ch_k, color="green", ls=":", alpha=0.8, label=f"peak k={best_ch_k}")
    axes[1].set_title("Calinski-Harabasz (higher = better)", fontweight="bold")
    axes[1].set_xlabel("k"); axes[1].set_ylabel("CH score"); axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.4, ls="--")

    axes[2].plot(sweep.index, sweep["merge_distance"], marker="^", color="#009E73")
    axes[2].axvline(NUM_CLUSTERS, color="red", ls="--", alpha=0.6)
    axes[2].set_title("Ward merge distance (elbow)", fontweight="bold")
    axes[2].set_xlabel("k"); axes[2].set_ylabel("Merge distance")
    axes[2].grid(alpha=0.4, ls="--")

    plt.tight_layout()
    plt.savefig(OUT_02_VALIDATION_EXTENDED, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f" -> Saved: {OUT_02_VALIDATION_EXTENDED.name}")

    # 2. Bootstrap stability across candidate k values
    summary_rows = []
    per_well_by_k = {}
    for k in K_RANGE_BOOTSTRAP:
        print(f" -> Bootstrap stability at k={k} ({N_BOOTSTRAP} resamples)...")
        stability, coassign = bootstrap_cluster_stability(wells_ref, k=k)
        per_well_by_k[k] = stability

        # Reference fit at this k, used for membership table and heatmap ordering.
        _, dist_square = _correlation_distance(wells_ref)
        Z = linkage(squareform(dist_square, checks=False), method="ward")
        ref_labels = pd.Series(fcluster(Z, t=k, criterion="maxclust"),
                               index=wells_ref.columns, name=f"cluster_k{k}")

        # Membership CSV so the forest-wells question can be inspected directly.
        membership = pd.DataFrame({
            "well": wells_ref.columns,
            f"cluster_k{k}": ref_labels.values,
            "stability": stability.reindex(wells_ref.columns).values,
        }).sort_values([f"cluster_k{k}", "well"])
        mem_path = str(OUT_02_MEMBERSHIP_SWEEP).format(k=k)
        membership.to_csv(mem_path, index=False)
        print(f"    Saved membership: {mem_path}")

        # Co-assignment heatmap at this k.
        hm_path = str(OUT_02_COASSIGN_HEATMAP).format(k=k)
        plot_coassignment_heatmap(coassign, ref_labels, k, hm_path)
        print(f"    Saved heatmap:    {hm_path}")

        # Per-cluster summary stats.
        for cid, grp in membership.groupby(f"cluster_k{k}"):
            median_stab = grp["stability"].median()
            min_stab    = grp["stability"].min()
            summary_rows.append({
                "k": k,
                "cluster": int(cid),
                "n_wells": len(grp),
                "median_stability": median_stab,
                "min_stability": min_stab,
                "members": ",".join(grp["well"].tolist()),
            })

        # Print a compact membership view for eyeballing.
        print(f"    Memberships at k={k}:")
        for cid, grp in membership.groupby(f"cluster_k{k}"):
            names = ", ".join(grp["well"].tolist())
            print(f"      C{int(cid)} (n={len(grp)}, median stab="
                  f"{grp['stability'].median():.2f}): {names}")

    # 3. Summary CSV (all k values, per cluster)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_02_STABILITY_SUMMARY, index=False)
    print(f" -> Saved stability summary: {OUT_02_STABILITY_SUMMARY.name}")

    # 4. Per-well stability across k (long form)
    per_well_long = pd.concat(
        [s.rename("stability").to_frame().assign(k=k).reset_index().rename(columns={"index": "well"})
         for k, s in per_well_by_k.items()],
        ignore_index=True,
    )
    per_well_long.to_csv(OUT_02_STABILITY_PER_WELL, index=False)
    print(f" -> Saved per-well stability: {OUT_02_STABILITY_PER_WELL.name}")

    # 5. Quick-look conclusions
    print("\n--- Stability diagnostics: quick look ---")
    for k in K_RANGE_BOOTSTRAP:
        s = per_well_by_k[k].dropna()
        frac_robust    = (s >= 0.9).mean()
        frac_borderline = ((s >= 0.7) & (s < 0.9)).mean()
        frac_fragile   = (s < 0.7).mean()
        print(f"  k={k}: median stab={s.median():.2f}  "
              f"robust (>=0.9): {frac_robust:.0%}  "
              f"borderline (0.7-0.9): {frac_borderline:.0%}  "
              f"fragile (<0.7): {frac_fragile:.0%}")
    print("-----------------------------------------\n")


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
    for cid in range(1, NUM_CLUSTERS + 1):
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
    # Iterate only over clusters that actually have data in `regional` — the
    # final partition has 5 clusters (llyn rhos is excluded in Script 01), so
    # C6 will be absent. Guarding here rather than hard-coding range(1, 6) so
    # the figure remains correct if the partition changes.
    for cid in sorted(int(c[1:]) for c in regional.columns if c.startswith("C")):
        ax_h.plot(
            regional.index,
            regional[f"C{cid}"].values,
            color=CLUSTER_COLOURS[cid],
            label=CLUSTER_LABELS[cid],
            lw=LW.get(cid, 1.6),
            ls=LINES.get(cid, "-"),
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


# =============================================================================
# Cluster amplitude descriptors (Section 4.2).
#
# Pattern-based clustering (Ward's on 1 - Pearson r) is orthogonal to response
# magnitude. This function characterises amplitude as a secondary descriptor
# per cluster, without proposing any change to the k=5 partition. It also
# produces climate-normalised variants in which the four monthly observations
# from each DROUGHT_SUMMERS year's Jun-Sep are excluded from the relevant
# window before p90-p10 is recomputed. The aggregation is median-of-medians
# across wells within each cluster (NOT aggregation on a cluster-mean
# hydrograph — the per-well-then-median approach is the agreed method).
# =============================================================================
def _amp_p90_p10(series: pd.Series, min_obs: int = AMP_MIN_OBS_PER_WIN) -> float:
    """p90 - p10 of a series, NaN if fewer than min_obs non-NA observations."""
    s = series.dropna()
    if len(s) < min_obs:
        return np.nan
    p10, p90 = np.percentile(s, [10, 90])
    return float(p90 - p10)


def _amp_drop_drought_summers(
    series: pd.Series, drought_years: tuple[int, ...]
) -> pd.Series:
    """Remove Jun-Sep monthly values from the listed drought years."""
    idx = series.index
    mask = ~(idx.year.isin(drought_years) & idx.month.isin(AMP_SUMMER_MONTHS))
    return series.loc[mask]


def compute_cluster_amplitude_descriptors(
    wells_ref: pd.DataFrame,
    cluster_df: pd.DataFrame,
) -> None:
    """
    Compute per-well and per-cluster amplitude descriptors, write three
    output files, and print a compact quick-look summary.

    Parameters
    ----------
    wells_ref : DataFrame
        Monthly well series, DatetimeIndex rows x well-name columns.
        Values are depth-below-pipe (negative); p90 - p10 is the positive
        seasonal range in metres.
    cluster_df : DataFrame
        Must contain columns 'Name_Original' (matching wells_ref column names)
        and 'Cluster' (canonical integer IDs as defined by CLUSTER_ID_ANCHORS,
        already mapped via _remap_cluster_ids_by_anchor before being passed
        in). The function asserts this so the output files cannot drift away
        from the canonical numbering.

    Outputs
    -------
    OUT_02_AMP_PER_WELL  — one row per well, raw and climate-normalised stats
    OUT_02_AMP_SUMMARY   — one row per cluster, median-of-medians aggregation
    OUT_02_AMP_BOXPLOT   — post-2018 p90-p10 distribution by cluster
    """
    print("\n--- Cluster Amplitude Descriptors ---")

    # Defensive check: cluster_df must already be in canonical numbering.
    # The amplitude file is consumed by Script 03 and should match the IDs
    # in 02_cluster_stats.csv exactly. If a caller skips the remap, fail
    # loudly here rather than write a file with raw fcluster IDs.
    cluster_ids_seen = set(int(c) for c in cluster_df["Cluster"].dropna().unique())
    canonical_ids    = set(CLUSTER_ID_ANCHORS.keys())
    if not cluster_ids_seen.issubset(canonical_ids):
        raise RuntimeError(
            f"compute_cluster_amplitude_descriptors received cluster IDs "
            f"{sorted(cluster_ids_seen)} which include values outside the "
            f"canonical set {sorted(canonical_ids)}. The cluster_df must be "
            f"remapped via _remap_cluster_ids_by_anchor before being passed "
            f"to this function. See PARTITION_HISTORY.md."
        )

    # Window split for drought-summer filtering (drought years above vs below
    # the 2018 split).
    drought_pre  = tuple(y for y in DROUGHT_SUMMERS if y <  AMP_SPLIT_DATE.year)
    drought_post = tuple(y for y in DROUGHT_SUMMERS if y >= AMP_SPLIT_DATE.year)

    # Map: Name_Original -> canonical cluster ID. Using Name_Original (not
    # Match_ID) because it matches wells_ref column names exactly.
    name_to_cluster = dict(zip(cluster_df["Name_Original"], cluster_df["Cluster"]))

    print(f" -> Computing per-well amplitude stats ({len(wells_ref.columns)} wells)...")
    rows = []
    for well in wells_ref.columns:
        cid = name_to_cluster.get(well)
        if cid is None:
            # Well in reference CSV but not in cluster_df. Skip with a note;
            # this shouldn't happen in a clean pipeline run.
            print(f"    [skip] no cluster assignment for well: {well!r}")
            continue

        s = wells_ref[well]
        pre  = s.loc[s.index <  AMP_SPLIT_DATE]
        post = s.loc[s.index >= AMP_SPLIT_DATE]

        # Climate-normalised variants
        pre_cn  = _amp_drop_drought_summers(pre,  drought_pre)
        post_cn = _amp_drop_drought_summers(post, drought_post)

        # Summer minimum in post-window: most-negative Jun-Sep depth value.
        post_summer = post[post.index.month.isin(AMP_SUMMER_MONTHS)].dropna()
        summer_min_post = float(post_summer.min()) if len(post_summer) >= 6 else np.nan

        rows.append({
            "well":                    well,
            "cluster":                 int(cid),
            "n_months_pre":            int(pre.dropna().shape[0]),
            "n_months_post":           int(post.dropna().shape[0]),
            "p90_p10_full":            _amp_p90_p10(s),
            "p90_p10_pre2018":         _amp_p90_p10(pre),
            "p90_p10_post2018":        _amp_p90_p10(post),
            "p90_p10_pre2018_climnorm":  _amp_p90_p10(pre_cn),
            "p90_p10_post2018_climnorm": _amp_p90_p10(post_cn),
            "std_full":                float(s.dropna().std(ddof=1))
                                         if s.dropna().shape[0] >= AMP_MIN_OBS_PER_WIN
                                         else np.nan,
            "summer_min_post2018":     summer_min_post,
        })

    per_well = pd.DataFrame(rows).sort_values(["cluster", "well"]).reset_index(drop=True)
    per_well.to_csv(OUT_02_AMP_PER_WELL, index=False)
    print(f" -> Saved: {OUT_02_AMP_PER_WELL.name}")

    # Per-cluster aggregation — median across wells within each cluster.
    print(f" -> Aggregating to {per_well['cluster'].nunique()} clusters...")
    print(f" -> Drought summers (climate normalisation): "
          f"{', '.join(str(y) for y in DROUGHT_SUMMERS)}")

    def _cluster_agg(g: pd.DataFrame) -> pd.Series:
        med_pre       = g["p90_p10_pre2018"].median()
        med_post      = g["p90_p10_post2018"].median()
        med_pre_cn    = g["p90_p10_pre2018_climnorm"].median()
        med_post_cn   = g["p90_p10_post2018_climnorm"].median()
        post_vals     = g["p90_p10_post2018"].dropna()
        damping = (100.0 * (med_pre - med_post) / med_pre
                   if pd.notna(med_pre) and pd.notna(med_post) and med_pre > 0
                   else np.nan)
        damping_cn = (100.0 * (med_pre_cn - med_post_cn) / med_pre_cn
                      if pd.notna(med_pre_cn) and pd.notna(med_post_cn) and med_pre_cn > 0
                      else np.nan)
        return pd.Series({
            "n_wells":                       len(g),
            "median_p90_p10_full":           g["p90_p10_full"].median(),
            "median_p90_p10_pre2018":        med_pre,
            "median_p90_p10_post2018":       med_post,
            "median_p90_p10_pre2018_climnorm":  med_pre_cn,
            "median_p90_p10_post2018_climnorm": med_post_cn,
            "median_std_full":               g["std_full"].median(),
            "median_summer_min_post2018":    g["summer_min_post2018"].median(),
            "amplitude_damping_pct":         damping,
            "amplitude_damping_pct_climnorm": damping_cn,
            "post2018_p90_p10_min":          post_vals.min() if len(post_vals) else np.nan,
            "post2018_p90_p10_max":          post_vals.max() if len(post_vals) else np.nan,
            "post2018_p90_p10_range":        (post_vals.max() - post_vals.min())
                                             if len(post_vals) else np.nan,
        })

    summary = per_well.groupby("cluster").apply(_cluster_agg).reset_index()
    summary.insert(1, "cluster_name",
                   summary["cluster"].map(lambda c: CLUSTER_LABELS.get(int(c), f"C{int(c)}")))
    summary = summary.rename(columns={"cluster": "cluster_id"})

    # Round numeric columns for readability; keep n_wells as int.
    num_cols = [c for c in summary.columns
                if c not in ("cluster_id", "cluster_name", "n_wells")]
    summary[num_cols] = summary[num_cols].astype(float).round(3)
    summary.to_csv(OUT_02_AMP_SUMMARY, index=False)
    print(f" -> Saved: {OUT_02_AMP_SUMMARY.name}")

    # Boxplot: post-2018 p90-p10 distribution by cluster.
    order = sorted(per_well["cluster"].unique().tolist())
    data_by_cluster = [
        per_well.loc[per_well["cluster"] == cid, "p90_p10_post2018"].dropna().values
        for cid in order
    ]
    positions = np.arange(len(order))

    fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
    bp = ax.boxplot(
        data_by_cluster,
        positions=positions,
        widths=0.55,
        patch_artist=True,
        medianprops=dict(color="black", linewidth=1.4),
        whiskerprops=dict(color="#555"),
        capprops=dict(color="#555"),
        flierprops=dict(marker="", markersize=0),
        zorder=2,
    )
    for patch, cid in zip(bp["boxes"], order):
        patch.set_facecolor(CLUSTER_COLOURS.get(cid, "#BBBBBB"))
        patch.set_alpha(0.35)
        patch.set_edgecolor(CLUSTER_COLOURS.get(cid, "#555555"))

    # Overlay individual wells (strip with deterministic jitter)
    rng = np.random.default_rng(0)
    for i, (cid, vals) in enumerate(zip(order, data_by_cluster)):
        jitter = rng.uniform(-0.12, 0.12, size=len(vals))
        ax.scatter(
            np.full_like(vals, i, dtype=float) + jitter,
            vals,
            s=32, color=CLUSTER_COLOURS.get(cid, "#444444"),
            edgecolor="black", linewidth=0.6, alpha=0.9, zorder=3,
        )

    xtick_labels = []
    for i, cid in enumerate(order):
        label_full = CLUSTER_LABELS.get(int(cid), f"C{int(cid)}")
        # "C1 (Lake)" -> two-line "C1\nLake"
        if "(" in label_full and label_full.endswith(")"):
            ctag, cname = label_full.split("(", 1)
            ctag = ctag.strip()
            cname = cname.rstrip(")").strip()
        else:
            ctag = f"C{int(cid)}"
            cname = label_full
        xtick_labels.append(f"{ctag}\n{cname}\n(n={len(data_by_cluster[i])})")

    ax.set_xticks(positions)
    ax.set_xticklabels(xtick_labels, fontsize=9)
    ax.set_ylabel("Seasonal amplitude, p90 − p10 (m)")
    ax.set_title("Post-2018 seasonal amplitude by cluster", fontsize=11, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(OUT_02_AMP_BOXPLOT, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f" -> Saved: {OUT_02_AMP_BOXPLOT.name}")

    # Quick-look table.
    print("\n--- Amplitude quick look (post-2018) ---")
    for _, row in summary.iterrows():
        cid       = int(row["cluster_id"])
        name      = CLUSTER_LABELS.get(cid, f"C{cid}")
        n         = int(row["n_wells"])
        med_post  = row["median_p90_p10_post2018"]
        lo        = row["post2018_p90_p10_min"]
        hi        = row["post2018_p90_p10_max"]
        damp      = row["amplitude_damping_pct"]
        damp_cn   = row["amplitude_damping_pct_climnorm"]
        # Sign convention: positive damping = attenuation; negative = enlargement.
        def _fmt(d):
            if pd.isna(d):
                return "n/a"
            sign = "+" if d > 0 else "−"
            return f"{sign}{abs(d):.1f}%"
        print(f"  {name:20s} (n={n}):  median {med_post:.2f}m  "
              f"range {lo:.2f}–{hi:.2f}  "
              f"Δpre/post(raw) {_fmt(damp)}  (climnorm {_fmt(damp_cn)})")
    print("----------------------------------------\n")


if __name__ == "__main__":
    make_all_dirs()
    print("--- Starting 02: Reference Clustering ---")

    if not INT_WELLS_REFERENCE.exists():
        print(f"Reference data not found: {INT_WELLS_REFERENCE}. Run 01 first.")
        sys.exit(1)

    wells_ref = pd.read_csv(INT_WELLS_REFERENCE, index_col=0, parse_dates=True)
    wells_ref = wells_ref.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    print(f" -> Clustering {len(wells_ref.columns)} reference wells...")

    # Build the correlation-distance matrix via the shared helper. The previous
    # version of this block used pdist(1 - corr_matrix), which misinterprets
    # the (1 - r) matrix as an observation-by-feature matrix and computes
    # pairwise Euclidean distances between rows — a completely different
    # distance from correlation distance. The stability diagnostics use
    # _correlation_distance() and so did the old dendrogram's colouring, so
    # the two disagreed on the tree. Using the helper here ensures the main
    # partition, the dendrogram, the validation plots, and the stability
    # diagnostics all agree on Ward's output.
    dist_array, dist_square = _correlation_distance(wells_ref)
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

    # --- Cluster stability diagnostics (Phase 1 validation) ---------------
    # Added per rebuild plan: bootstrap stability across candidate k values,
    # plus extended k-sweep (silhouette + Calinski-Harabasz + merge distance).
    # Runs once per invocation; figures and tables land in outputs/02_clustering/.
    run_stability_diagnostics(wells_ref)

    # --- Cluster assignments -----------------------------------------------
    # Run Ward's at WARDS_K. fcluster returns arbitrary integer IDs; we then
    # remap them to the canonical CLUSTER_ID_ANCHORS numbering so downstream
    # scripts get stable IDs across re-runs. Every canonical ID has at least
    # one anchor well, so under a stable partition all five raw clusters are
    # claimed by anchors directly. The fallback (unanchored raw cluster ->
    # unclaimed canonical ID) only fires if Ward's produces a partition where
    # an anchor well's home cluster picks up additional members beyond what
    # the partition expects — defensive only, not part of normal flow.
    sub_clusters_raw = fcluster(Z, t=WARDS_K, criterion="maxclust")

    raw_to_canonical = _remap_cluster_ids_by_anchor(
        sub_clusters_raw, wells_ref.columns.tolist(), CLUSTER_ID_ANCHORS,
    )
    sub_clusters = np.array([raw_to_canonical[c] for c in sub_clusters_raw])

    cluster_df = pd.DataFrame({
        "Match_ID":      [normalize_well_name(col) for col in wells_ref.columns],
        "Name_Original": [str(col) for col in wells_ref.columns],
        "Cluster":       sub_clusters,
    })
    cluster_df["Cluster_Label"] = cluster_df["Cluster"].map(CLUSTER_LABELS).fillna(
        cluster_df["Cluster"].apply(lambda c: f"C{int(c)}")
    )
    cluster_df.to_csv(INT_CLUSTER_STATS, index=False)
    print(f" -> Saved cluster stats: {INT_CLUSTER_STATS.name}")
    print("     Cluster sizes (canonical IDs):")
    for cid, grp in cluster_df.groupby("Cluster"):
        print(f"       {CLUSTER_LABELS.get(int(cid), f'C{int(cid)}'):30s} n={len(grp)}")

    # --- Dendrogram --------------------------------------------------------
    print(" -> Generating Dendrogram...")
    fig, ax = plt.subplots(figsize=(15, 8), dpi=300)
    ax.set_title("Reference network behavioural clustering (Ward's, k=5)",
                 fontsize=14, fontweight="bold")

    _clr = CLUSTER_COLOURS_BW if BW_MODE else CLUSTER_COLOURS

    dendro = dendrogram(
        Z, labels=wells_ref.columns, leaf_rotation=90.0, leaf_font_size=8.0,
        color_threshold=Z[-WARDS_K, 2], above_threshold_color="#BBBBBB",
        ax=ax,
    )
    label_to_cluster = {}
    for _, row in cluster_df.iterrows():
        label_to_cluster[normalize_well_name(row["Name_Original"])] = int(row["Cluster"])

    # Colour tick labels by cluster
    for tick in ax.get_xmajorticklabels():
        cid = label_to_cluster.get(normalize_well_name(tick.get_text()))
        if cid in _clr:
            tick.set_color(_clr[cid])
            if BW_MODE:
                tick.set_fontweight("bold")

    leaf_clusters = [label_to_cluster.get(normalize_well_name(lbl), None) for lbl in dendro["ivl"]]
    leaf_idx_to_cluster = {i: cid for i, cid in enumerate(leaf_clusters) if cid is not None}

    # BW line style mapping for branches
    _bw_ls = {cid: BW_LINESTYLES[i % len(BW_LINESTYLES)] for i, cid in enumerate(sorted(CLUSTER_LABELS.keys()))}

    for xs, ys in zip(dendro["icoord"], dendro["dcoord"]):
        leaf_xs = [int(round(x)) for x in xs if x % 10 == 5]
        if not leaf_xs:
            continue
        leaf_idx = (min(leaf_xs) - 5) // 10
        cid = leaf_idx_to_cluster.get(leaf_idx, None)
        if BW_MODE and cid in _bw_ls:
            ax.plot(xs, ys, color=_clr.get(cid, "#BBBBBB"), zorder=2,
                    **_bw_ls[cid])
        else:
            ax.plot(xs, ys, color=_clr.get(cid, "#BBBBBB"), lw=2.2, zorder=2)

    # --- Cluster labels on their branch horizontal lines ---
    cluster_leaf_xs = {}
    for i, cid in enumerate(leaf_clusters):
        if cid is not None:
            cluster_leaf_xs.setdefault(cid, []).append(i * 10 + 5)

    # For each cluster, find the highest internal merge (the horizontal line
    # at the top of that cluster's sub-tree) and place the label there.
    for cid in sorted(CLUSTER_LABELS.keys()):
        if cid not in cluster_leaf_xs:
            continue
        xs = cluster_leaf_xs[cid]
        x_min_c = min(xs) - 5
        x_max_c = max(xs) + 5
        # Find the highest merge whose span is within this cluster's leaves
        best_y = 0
        best_x_mid = (min(xs) + max(xs)) / 2
        for ixs, iys in zip(dendro["icoord"], dendro["dcoord"]):
            span_min = min(ixs)
            span_max = max(ixs)
            top_y = max(iys)
            if span_min >= x_min_c and span_max <= x_max_c:
                if top_y > best_y:
                    best_y = top_y
                    # The horizontal segment is at top_y; its x-midpoint
                    best_x_mid = (ixs[1] + ixs[2]) / 2

        short_label = f"C{cid}"
        ax.annotate(
            short_label,
            xy=(best_x_mid, best_y),
            fontsize=10, fontweight="bold",
            color="#333333",
            ha="center", va="bottom",
            xytext=(0, 4), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#666666", alpha=0.85),
            zorder=10,
        )

    # --- Eastern/Western block labels on the main branch lines ---
    _blocks = {
        "Eastern block": [1, 2],
        "Western block": [3, 4, 5],
    }

    for block_name, cids_in_block in _blocks.items():
        all_xs = []
        for cid in cids_in_block:
            if cid in cluster_leaf_xs:
                all_xs.extend(cluster_leaf_xs[cid])
        if not all_xs:
            continue
        x_min_b = min(all_xs) - 5
        x_max_b = max(all_xs) + 5
        # Find the highest merge spanning all leaves in this block
        best_y = 0
        best_x_left = min(all_xs)
        for ixs, iys in zip(dendro["icoord"], dendro["dcoord"]):
            span_min = min(ixs)
            span_max = max(ixs)
            top_y = max(iys)
            if span_min >= x_min_b and span_max <= x_max_b:
                if top_y > best_y:
                    best_y = top_y
                    # Place label on the left side of the horizontal line
                    best_x_left = ixs[0]

        ax.annotate(
            block_name,
            xy=(best_x_left, best_y),
            fontsize=9, fontstyle="italic", fontweight="bold",
            ha="left", va="center",
            xytext=(8, 0), textcoords="offset points",
            color="#333333",
            bbox=dict(boxstyle="round,pad=0.3", fc="#f0f0f0", ec="#999999",
                      alpha=0.9, lw=0.8),
            zorder=10,
        )

    ax.legend(
        handles=[plt.Line2D([0], [0], color=_clr[c], lw=3,
                            label=CLUSTER_LABELS.get(c, f"C{c}"))
                 for c in sorted(CLUSTER_LABELS.keys()) if c in _clr],
        title="Cluster Assignments", loc="upper right", frameon=True,
    )
    ax.set_ylabel("Ward Linkage Distance", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_02_DENDROGRAM)
    plt.close(fig)

    print(" -> Generating Cluster Hydrograph + Water-Balance Figure...")
    make_cluster_hydrograph_wb_figure()

    compute_cluster_amplitude_descriptors(wells_ref, cluster_df)

    print("-> Clustering Complete.")
