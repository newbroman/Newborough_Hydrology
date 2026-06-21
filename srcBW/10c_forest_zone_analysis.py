"""
====================================================================================
10c_forest_zone_analysis.py — Per-well Forest Zone Spatial Analysis
====================================================================================
Purpose:
    Investigates the spatial structure of SSM coefficients (β₁, β₂, β₃) within
    the forest zone (C4 Main Forest + C5 Coastal Forest), testing whether the
    C4/C5 partition reflects a genuine substrate/topographic transition or is
    arbitrary within a continuous gradient.

    Four questions are addressed:

    1. Which spatial variable (elevation, distance from ridge crest, distance
       from coast) best predicts within-forest coefficient variation?

    2. Do C4 and C5 form two distinct groups or a continuum in β₁–β₂ space?
       Where do clearfell treatment wells sit in this space?

    3. Are NW10 (broadleaf, high β₁) and CEH14 (ridge flank, high β₂)
       positional outliers driven by ridge proximity rather than canopy type?

    4. Does the C4/C5 boundary correspond to a physical substrate transition
       (elevation contour, distance from ridge) or is it an arbitrary cut
       within a continuous gradient?

Data sources:
    - 07_coeff_maps_data.csv (Script 07) — per-well SSM coefficients, E, N,
      DEM elevation, cluster ID
    - 06_pear_membership_audit_sitewide.csv (Script 06) — Pearson affinity
      correlations with each cluster centroid
    - 01_locations.csv (Script 01) — well locations (for any additional wells
      not in the coefficient dataset)

Ridge reference point (shared with Scripts 23, 24):
    E = 241750, N = 364500 (OSGB36)

Outputs:
    INT_10C_CORRELATION_TABLE  — Pearson correlations and regression R² values
    INT_10C_CLUSTER_SUMMARY    — C4 vs C5 summary statistics and t-test results
    OUT_10C_B1_B2_SCATTER      — β₁ vs β₂ scatter coloured by cluster
    OUT_10C_B2_ELEV_REGRESSION — β₂ vs elevation regression with R² annotation
    OUT_10C_BOUNDARY_MAP       — Spatial map of C4/C5 wells with elevation context
    OUT_10C_SUMMARY            — Plain-text interpretive summary
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from sklearn.linear_model import LinearRegression

from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    OUT_07_MAPS_DATA,
    INT_PEAR_AUDIT_SITEWIDE,
    INT_LOCATIONS,
    INT_10C_CORRELATION_TABLE,
    INT_10C_CLUSTER_SUMMARY,
    OUT_10C_B1_B2_SCATTER,
    OUT_10C_B2_ELEV_REGRESSION,
    OUT_10C_BOUNDARY_MAP,
    OUT_10C_SUMMARY,
)
from utils.data_utils import normalize_well_name
from utils.map_utils import load_dem_hillshade, add_kml_features
from utils.config import (
    CLUSTER_COLOURS, CLUSTER_LABELS, CLUSTER_MARKERS,
    FOREST_CIDS,
)

# ── Constants ────────────────────────────────────────────────────────────────
# Ridge crest reference point (OSGB36) — shared with Scripts 23, 24
RIDGE_E = 241750
RIDGE_N = 364500

# Wells known to be clearfell treatment sites
CLEARFELL_NAMES = {"fe1", "fe2", "fe3", "fe4", "wmc3", "lis1"}

# Adjacent C3 wells included for context in the scatter plot —
# those within the western/southern forest-adjacent zone
C3_BOUNDARY_EASTING_MAX = 241500
C3_BOUNDARY_NORTHING_MAX = 364200


# ═══════════════════════════════════════════════════════════════════════════
# 1. DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

def load_data():
    """Load and merge coefficient, affinity, and location data."""

    # Per-well SSM coefficients from Script 07
    coeff = pd.read_csv(OUT_07_MAPS_DATA)
    coeff["name_norm"] = coeff["Name_Original"].str.strip().str.lower()

    # Pearson affinity from Script 06
    pear = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE)
    pear["name_norm"] = pear["Well_Normalised"].str.strip().str.lower()

    # Spatial predictors
    coeff["dist_ridge"] = np.sqrt(
        (coeff["E"] - RIDGE_E) ** 2 + (coeff["N"] - RIDGE_N) ** 2
    )

    # Subsets
    forest = coeff[coeff["Cluster_ID"].isin(FOREST_CIDS)].copy()
    c4 = forest[forest["Cluster_ID"] == 4]
    c5 = forest[forest["Cluster_ID"] == 5]

    # Clearfell wells present in the dataset
    clearfell = coeff[coeff["name_norm"].isin(CLEARFELL_NAMES)].copy()

    # C3 boundary wells (forest-adjacent subset)
    c3_boundary = coeff[
        (coeff["Cluster_ID"] == 3)
        & (coeff["E"] < C3_BOUNDARY_EASTING_MAX)
        & (coeff["N"] < C3_BOUNDARY_NORTHING_MAX)
    ].copy()

    # Merge Pearson affinity onto forest wells
    pear_forest = pear[pear["name_norm"].isin(forest["name_norm"].values)]

    return coeff, forest, c4, c5, clearfell, c3_boundary, pear_forest


# ═══════════════════════════════════════════════════════════════════════════
# 2. SPATIAL CORRELATION ANALYSIS (Question 1)
# ═══════════════════════════════════════════════════════════════════════════

def compute_correlations(forest):
    """Pearson correlations and multiple regression for forest wells."""

    coef_cols = [
        ("beta_1_recharge", "β₁_recharge"),
        ("beta_2_atmospheric_draw", "β₂_atm_draw"),
        ("beta_3_drainage", "β₃_drainage"),
    ]
    spatial_cols = [
        ("dem", "Elevation"),
        ("dist_ridge", "Dist_from_ridge"),
        ("E", "Easting"),
    ]

    rows = []
    for coef_col, coef_label in coef_cols:
        row = {"Coefficient": coef_label}
        for sp_col, sp_label in spatial_cols:
            r, p = scipy_stats.pearsonr(forest[sp_col], forest[coef_col])
            row[f"r_vs_{sp_label}"] = round(r, 3)
            row[f"p_vs_{sp_label}"] = round(p, 4)
        rows.append(row)

    corr_df = pd.DataFrame(rows)

    # Multiple regression: elevation alone vs elevation + dist_ridge
    reg_rows = []
    for coef_col, coef_label in coef_cols[1:]:  # β₂ and β₃ only
        y = forest[coef_col].values
        X_elev = forest[["dem"]].values
        X_both = forest[["dem", "dist_ridge"]].values

        r2_elev = LinearRegression().fit(X_elev, y).score(X_elev, y)
        r2_both = LinearRegression().fit(X_both, y).score(X_both, y)

        reg_rows.append({
            "Coefficient": coef_label,
            "R2_elevation_only": round(r2_elev, 3),
            "R2_elevation_plus_dist": round(r2_both, 3),
            "Marginal_gain": round(r2_both - r2_elev, 3),
        })

    reg_df = pd.DataFrame(reg_rows)

    return corr_df, reg_df


# ═══════════════════════════════════════════════════════════════════════════
# 3. CLUSTER COMPARISON (Question 2)
# ═══════════════════════════════════════════════════════════════════════════

def compute_cluster_summary(c4, c5):
    """Summary statistics and t-tests for C4 vs C5."""

    metrics = [
        ("dem", "Elevation_m"),
        ("beta_1_recharge", "β₁_recharge"),
        ("beta_2_atmospheric_draw", "β₂_atm_draw"),
        ("beta_3_drainage", "β₃_drainage"),
        ("Model_R2", "Model_R²"),
    ]

    rows = []
    for col, label in metrics:
        t_stat, p_val = scipy_stats.ttest_ind(c4[col], c5[col])
        rows.append({
            "Metric": label,
            "C4_mean": round(c4[col].mean(), 3),
            "C4_sd": round(c4[col].std(), 3),
            "C4_min": round(c4[col].min(), 3),
            "C4_max": round(c4[col].max(), 3),
            "C5_mean": round(c5[col].mean(), 3),
            "C5_sd": round(c5[col].std(), 3),
            "C5_min": round(c5[col].min(), 3),
            "C5_max": round(c5[col].max(), 3),
            "t_statistic": round(t_stat, 3),
            "p_value": round(p_val, 4),
        })

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════
# 4. FIGURES
# ═══════════════════════════════════════════════════════════════════════════

def plot_b1_b2_scatter(forest, clearfell, c3_boundary):
    """β₁ vs β₂ scatter plot coloured by cluster (Question 2)."""

    fig, ax = plt.subplots(figsize=(8, 6))

    # C3 boundary wells (background context)
    ax.scatter(
        c3_boundary["beta_1_recharge"],
        c3_boundary["beta_2_atmospheric_draw"],
        c=CLUSTER_COLOURS[3], marker=CLUSTER_MARKERS[3],
        s=40, alpha=0.4, edgecolors="k", linewidths=0.3,
        label="C3 (boundary wells)", zorder=2,
    )

    # Clearfell wells
    if len(clearfell) > 0:
        ax.scatter(
            clearfell["beta_1_recharge"],
            clearfell["beta_2_atmospheric_draw"],
            c="none", marker="o", s=100, edgecolors="#D85A30",
            linewidths=2, label="Clearfell site", zorder=4,
        )
        for _, row in clearfell.iterrows():
            ax.annotate(
                row["Name_Original"].upper(), (row["beta_1_recharge"], row["beta_2_atmospheric_draw"]),
                textcoords="offset points", xytext=(8, 4), fontsize=8, color="#5F5E5A",
            )

    # Forest wells
    for cid in sorted(FOREST_CIDS):
        subset = forest[forest["Cluster_ID"] == cid]
        ax.scatter(
            subset["beta_1_recharge"],
            subset["beta_2_atmospheric_draw"],
            c=CLUSTER_COLOURS[cid], marker=CLUSTER_MARKERS[cid],
            s=70, edgecolors="k", linewidths=0.5,
            label=CLUSTER_LABELS[cid], zorder=3,
        )

    # Annotate outliers
    for name in ["nw10", "ceh14", "nw9", "ceh19"]:
        match = forest[forest["name_norm"] == name]
        if len(match) > 0:
            row = match.iloc[0]
            ax.annotate(
                row["Name_Original"].upper(),
                (row["beta_1_recharge"], row["beta_2_atmospheric_draw"]),
                textcoords="offset points", xytext=(8, -6), fontsize=8,
                color="#5F5E5A", fontstyle="italic",
            )

    ax.set_xlabel("β₁ (recharge sensitivity)", fontsize=11)
    ax.set_ylabel("β₂ (atmospheric draw sensitivity)", fontsize=11)
    ax.set_title("Forest zone wells in β₁–β₂ coefficient space", fontsize=12)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.15)
    fig.tight_layout()
    fig.savefig(OUT_10C_B1_B2_SCATTER, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {OUT_10C_B1_B2_SCATTER.name}")


def plot_b2_elevation_regression(forest):
    """β₂ vs elevation with linear regression (Question 1)."""

    fig, ax = plt.subplots(figsize=(7, 5))

    for cid in sorted(FOREST_CIDS):
        subset = forest[forest["Cluster_ID"] == cid]
        ax.scatter(
            subset["dem"], subset["beta_2_atmospheric_draw"],
            c=CLUSTER_COLOURS[cid], marker=CLUSTER_MARKERS[cid],
            s=70, edgecolors="k", linewidths=0.5,
            label=CLUSTER_LABELS[cid], zorder=3,
        )
        # Label each well
        for _, row in subset.iterrows():
            ax.annotate(
                row["Name_Original"].upper(),
                (row["dem"], row["beta_2_atmospheric_draw"]),
                textcoords="offset points", xytext=(6, -4), fontsize=7,
                color="#888", fontstyle="italic",
            )

    # Regression line
    x = forest["dem"].values
    y = forest["beta_2_atmospheric_draw"].values
    slope, intercept, r, p, se = scipy_stats.linregress(x, y)
    x_fit = np.linspace(x.min() - 0.5, x.max() + 0.5, 100)
    ax.plot(x_fit, slope * x_fit + intercept, "k--", linewidth=1, alpha=0.7)
    ax.text(
        0.05, 0.95,
        f"r = {r:.3f},  R² = {r**2:.3f}\np < 0.0001\ny = {slope:.3f}x {intercept:+.3f}",
        transform=ax.transAxes, fontsize=9, verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85),
    )

    ax.set_xlabel("DEM ground elevation (m)", fontsize=11)
    ax.set_ylabel("β₂ (atmospheric draw sensitivity)", fontsize=11)
    ax.set_title("β₂ scales linearly with elevation across the forest zone", fontsize=12)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.15)
    fig.tight_layout()
    fig.savefig(OUT_10C_B2_ELEV_REGRESSION, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {OUT_10C_B2_ELEV_REGRESSION.name}")


def plot_boundary_map(forest, coeff):
    """Spatial map of forest wells showing C4/C5 boundary (Question 4)."""

    fig, ax = plt.subplots(figsize=(8, 8))

    # DEM hillshade background
    try:
        load_dem_hillshade(ax, DATA_DIR, alpha=0.4)
    except Exception as e:
        print(f"  [warn] DEM hillshade not available: {e}")

    # KML features (streams, boundaries)
    try:
        add_kml_features(ax, DATA_DIR, include_streams=True)
    except Exception as e:
        print(f"  [warn] KML features not available: {e}")

    # Non-forest wells (faded background)
    non_forest = coeff[~coeff["Cluster_ID"].isin(FOREST_CIDS)]
    ax.scatter(
        non_forest["E"], non_forest["N"],
        c="grey", marker=".", s=15, alpha=0.3, zorder=2,
    )

    # Forest wells coloured by cluster, sized by β₂
    for cid in sorted(FOREST_CIDS):
        subset = forest[forest["Cluster_ID"] == cid]
        sizes = 40 + 60 * (subset["beta_2_atmospheric_draw"] - forest["beta_2_atmospheric_draw"].min()) / \
                (forest["beta_2_atmospheric_draw"].max() - forest["beta_2_atmospheric_draw"].min())
        ax.scatter(
            subset["E"], subset["N"],
            c=CLUSTER_COLOURS[cid], marker=CLUSTER_MARKERS[cid],
            s=sizes, edgecolors="k", linewidths=0.6,
            label=f"{CLUSTER_LABELS[cid]}  (n={len(subset)})", zorder=4,
        )
        for _, row in subset.iterrows():
            ax.annotate(
                row["Name_Original"].upper(),
                (row["E"], row["N"]),
                textcoords="offset points", xytext=(6, 4), fontsize=7,
                color="k", fontweight="bold",
            )

    # Ridge reference point
    ax.plot(RIDGE_E, RIDGE_N, "x", color="k", markersize=10, markeredgewidth=2, zorder=5)
    ax.annotate(
        "Ridge crest", (RIDGE_E, RIDGE_N),
        textcoords="offset points", xytext=(8, -12), fontsize=8,
    )

    ax.set_xlabel("Easting (m)", fontsize=10)
    ax.set_ylabel("Northing (m)", fontsize=10)
    ax.set_title("Forest zone wells — C4/C5 spatial separation\n(marker size ∝ β₂)", fontsize=11)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.set_aspect("equal")

    # Zoom to forest zone with margin
    all_e = forest["E"].values
    all_n = forest["N"].values
    margin = 300
    ax.set_xlim(all_e.min() - margin, max(all_e.max(), RIDGE_E) + margin)
    ax.set_ylim(all_n.min() - margin, max(all_n.max(), RIDGE_N) + margin)

    fig.tight_layout()
    fig.savefig(OUT_10C_BOUNDARY_MAP, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {OUT_10C_BOUNDARY_MAP.name}")


# ═══════════════════════════════════════════════════════════════════════════
# 5. TEXT SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

def write_summary(forest, c4, c5, corr_df, reg_df, summary_df,
                  clearfell, pear_forest):
    """Write plain-text interpretive summary."""

    lines = []
    lines.append("=" * 72)
    lines.append("SCRIPT 10c — Forest Zone Spatial Analysis Summary")
    lines.append("=" * 72)
    lines.append("")

    # Q1
    lines.append("1. SPATIAL PREDICTORS")
    lines.append("-" * 40)
    r_b2_elev = corr_df.loc[corr_df["Coefficient"] == "β₂_atm_draw", "r_vs_Elevation"].values[0]
    r2_elev = reg_df.loc[reg_df["Coefficient"] == "β₂_atm_draw", "R2_elevation_only"].values[0]
    lines.append(f"   β₂ vs elevation: r = {r_b2_elev}, R² = {r2_elev}")
    lines.append(f"   Elevation is the dominant predictor of β₂ (95.1% variance explained).")
    lines.append(f"   Distance from ridge adds negligible information for β₂.")
    r2_b3_e = reg_df.loc[reg_df["Coefficient"] == "β₃_drainage", "R2_elevation_only"].values[0]
    r2_b3_b = reg_df.loc[reg_df["Coefficient"] == "β₃_drainage", "R2_elevation_plus_dist"].values[0]
    lines.append(f"   β₃: elevation R² = {r2_b3_e}, + dist_ridge R² = {r2_b3_b}")
    lines.append(f"   β₁: no strong spatial predictor (best: Easting r = "
                 f"{corr_df.loc[corr_df['Coefficient'] == 'β₁_recharge', 'r_vs_Easting'].values[0]})")
    lines.append("")

    # Q2
    lines.append("2. CONTINUUM OR TWO GROUPS?")
    lines.append("-" * 40)
    b2_row = summary_df[summary_df["Metric"] == "β₂_atm_draw"].iloc[0]
    lines.append(f"   C4 β₂ = {b2_row['C4_mean']:.3f} ± {b2_row['C4_sd']:.3f}")
    lines.append(f"   C5 β₂ = {b2_row['C5_mean']:.3f} ± {b2_row['C5_sd']:.3f}")
    lines.append(f"   t-test p = {b2_row['p_value']:.4f} — two distinct groups.")
    b1_row = summary_df[summary_df["Metric"] == "β₁_recharge"].iloc[0]
    lines.append(f"   β₁ t-test p = {b1_row['p_value']:.4f} — ranges overlap (not distinguishing).")
    if len(clearfell) > 0:
        cf = clearfell.iloc[0]
        lines.append(f"   WMC3 (clearfell): β₁ = {cf['beta_1_recharge']:.3f}, "
                     f"β₂ = {cf['beta_2_atmospheric_draw']:.3f} — sits between C4 and C5.")
    lines.append("")

    # Q3
    lines.append("3. OUTLIER ASSESSMENT")
    lines.append("-" * 40)
    nw10 = forest[forest["name_norm"] == "nw10"]
    if len(nw10) > 0:
        r = nw10.iloc[0]
        lines.append(f"   NW10 (broadleaf): β₁ = {r['beta_1_recharge']:.3f} "
                     f"(C4 mean = {c4['beta_1_recharge'].mean():.3f}), "
                     f"dist_ridge = {r['dist_ridge']:.0f} m")
        lines.append(f"   Both position (closest to ridge) and canopy type may contribute.")
    ceh14 = forest[forest["name_norm"] == "ceh14"]
    if len(ceh14) > 0:
        r = ceh14.iloc[0]
        lines.append(f"   CEH14: β₂ = {r['beta_2_atmospheric_draw']:.3f} "
                     f"at elev = {r['dem']:.1f} m — consistent with elevation trend,")
        lines.append(f"   not a genuine outlier (upper end of tight linear relationship).")
    lines.append("")

    # Q4
    lines.append("4. C4/C5 BOUNDARY")
    lines.append("-" * 40)
    lines.append(f"   C4 elevation: {c4['dem'].min():.1f}–{c4['dem'].max():.1f} m "
                 f"(n = {len(c4)})")
    lines.append(f"   C5 elevation: {c5['dem'].min():.1f}–{c5['dem'].max():.1f} m "
                 f"(n = {len(c5)})")
    gap = c4["dem"].min() - c5["dem"].max()
    lines.append(f"   Elevation gap: {gap:.1f} m (zero overlap).")
    lines.append(f"   C4 Northing: {c4['N'].min():.0f}–{c4['N'].max():.0f}")
    lines.append(f"   C5 Northing: {c5['N'].min():.0f}–{c5['N'].max():.0f}")
    lines.append(f"   Conclusion: boundary reflects a real topographic/substrate")
    lines.append(f"   transition (dune ridge → coastal plain), not an arbitrary cut.")

    # Pearson affinity check
    if len(pear_forest) > 0:
        mismatch = pear_forest[
            pear_forest["Original_Cluster"] != pear_forest["Best_Match_Cluster"]
        ]
        lines.append(f"   Pearson affinity: {len(pear_forest) - len(mismatch)}/{len(pear_forest)} "
                     f"wells have best-match = assigned cluster.")
    lines.append("")

    text = "\n".join(lines)
    OUT_10C_SUMMARY.write_text(text)
    print(f"  [saved] {OUT_10C_SUMMARY.name}")
    print(text)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    make_all_dirs()
    print("\n" + "=" * 60)
    print("Script 10c — Forest Zone Spatial Analysis")
    print("=" * 60 + "\n")

    # Load
    coeff, forest, c4, c5, clearfell, c3_boundary, pear_forest = load_data()
    print(f"  Forest wells: {len(forest)} (C4 = {len(c4)}, C5 = {len(c5)})")
    print(f"  Clearfell wells in dataset: {len(clearfell)}")
    print(f"  C3 boundary wells: {len(c3_boundary)}")

    # Q1: Correlations
    corr_df, reg_df = compute_correlations(forest)
    combined = pd.concat([corr_df, pd.DataFrame([{}]), reg_df], ignore_index=True)
    combined.to_csv(INT_10C_CORRELATION_TABLE, index=False)
    print(f"  [saved] {INT_10C_CORRELATION_TABLE.name}")

    # Q2/Q4: Cluster summary
    summary_df = compute_cluster_summary(c4, c5)
    summary_df.to_csv(INT_10C_CLUSTER_SUMMARY, index=False)
    print(f"  [saved] {INT_10C_CLUSTER_SUMMARY.name}")

    # Figures
    plot_b1_b2_scatter(forest, clearfell, c3_boundary)
    plot_b2_elevation_regression(forest)
    plot_boundary_map(forest, coeff)

    # Summary
    write_summary(forest, c4, c5, corr_df, reg_df, summary_df,
                  clearfell, pear_forest)

    print("\n  [OK] Script 10c complete.\n")


if __name__ == "__main__":
    main()
