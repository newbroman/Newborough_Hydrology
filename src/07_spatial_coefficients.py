"""
====================================================================================
07_spatial_coefficients.py — Spatial Mapping of SSM Coefficients
====================================================================================
Purpose:
    Maps the per-well SSM coefficients (β₁ recharge sensitivity, β₂ atmospheric
    draw, β₃ drainage rate) from 03_master_data.csv across the site as
    IDW-interpolated surfaces over a DEM hillshade, showing how the three
    mechanistic processes vary spatially.

    This script replaces the former 07_boundary_intercept.py. The old intercept
    audit (Model A vs Model B with/without a fitted constant) was superseded by
    the displacement formulation: the SSM now fits well across all clusters
    (Script 08 median iterative NSE = 0.77), and the intercept test added little
    beyond what direct coefficient mapping reveals more clearly.

    β₃ (drainage) maps show proximity to drainage boundaries and hydraulic
    conductivity variation — the spatial pattern that the old intercept map
    was a proxy for. β₂ (ET) maps show the vegetation/microclimate imprint.
    β₁ (recharge) maps test whether infiltration is spatially uniform or
    varies with soil/surface properties.

Data source:
    All coefficients come from Script 03's per-well SSM fits stored in
    03_master_data.csv. These are displacement-formulation fits (β₃ fitted
    on h_disp = DRAINAGE_DATUM + h_depth), but β₁, β₂, β₃ values are
    numerically identical regardless of whether the fit uses raw depth or
    displacement — only the intercept differs.

Outputs:
    - 07_coefficient_summary.csv
    - outputs/07_spatial_coefficients/07_coeff_01_beta1_recharge.png
    - outputs/07_spatial_coefficients/07_coeff_02_beta2_atm_draw.png
    - outputs/07_spatial_coefficients/07_coeff_03_beta3_drainage.png
    - outputs/07_spatial_coefficients/07_coeff_04_r2_quality.png
    - outputs/07_spatial_coefficients/07_coeff_maps_data.csv
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    OUT_DIR,
    INT_MASTER_DATA,
    INT_WELL_ELEVATIONS,
)
from utils.map_utils import (
    load_dem_hillshade,
    add_idw_surface,
    add_kml_features,
)
from utils.data_utils import normalize_well_name
from utils.config import (
    CLUSTER_LABELS,
    CLUSTER_COLOURS,
    CLUSTER_MARKERS,
)
from pathlib import Path
import warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

# ==========================================
# OUTPUT PATHS
# ==========================================
DIR_07 = OUT_DIR / "07_spatial_coefficients"
DIR_07.mkdir(parents=True, exist_ok=True)

OUT_SUMMARY_CSV  = OUT_DIR / "07_coefficient_summary.csv"
OUT_BETA1_MAP    = DIR_07 / "07_coeff_01_beta1_recharge.png"
OUT_BETA2_MAP    = DIR_07 / "07_coeff_02_beta2_atm_draw.png"
OUT_BETA3_MAP    = DIR_07 / "07_coeff_03_beta3_drainage.png"
OUT_R2_MAP       = DIR_07 / "07_coeff_04_r2_quality.png"
OUT_MAPS_DATA    = DIR_07 / "07_coeff_maps_data.csv"

# ==========================================
# GRID — matches scripts 11b / 19 / 20
# ==========================================
GRID_XI = np.arange(240200, 243800, 50)
GRID_YI = np.arange(362200, 365800, 50)
XLIM = (240400, 243600)
YLIM = (362400, 365400)

# ==========================================
# AESTHETICS
# ==========================================
DPI = 200
plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
})


# ------------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------------

def load_coefficient_data():
    """
    Load per-well SSM coefficients and merge DEM ground elevations for
    ridge masking.

    Returns a DataFrame with columns E, N, dem, Cluster_ID, and all
    coefficient / p-value / R² columns from 03_master_data.csv.
    """
    master = pd.read_csv(INT_MASTER_DATA)
    elev = pd.read_csv(INT_WELL_ELEVATIONS)

    master["wn"] = master["Name_Original"].apply(normalize_well_name)
    elev["wn"] = elev["Name"].apply(normalize_well_name)

    df = master.merge(
        elev[["wn", "DEM_Ground_Elev"]],
        on="wn", how="left",
    )
    df = df.rename(columns={
        "Easting": "E",
        "Northing": "N",
        "DEM_Ground_Elev": "dem",
        "Cluster": "Cluster_ID",
    })
    return df


# ------------------------------------------------------------------
# SINGLE MAP GENERATOR
# ------------------------------------------------------------------

def make_coefficient_map(
    df,
    value_col,
    title,
    output_path,
    cmap,
    cbar_label,
    vmin=None,
    vmax=None,
    log_scale=False,
    contour_levels=None,
    contour_fmt="%.2f",
):
    """
    Render one IDW-interpolated coefficient surface over DEM hillshade
    with well markers, KML features, and a colorbar.
    """
    plot_df = df.dropna(subset=["E", "N", value_col]).copy()
    if plot_df.empty:
        print(f"  [WARNING] No data for {value_col}. Skipping {output_path.name}")
        return

    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")

    # Layer 1 — DEM hillshade
    _, ok, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1,
    )
    if not ok:
        print("  [WARNING] DEM hillshade unavailable — map will lack terrain context.")

    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    # Colour norm
    vals = plot_df[value_col].to_numpy(dtype=float)
    if log_scale:
        floor = max(vals[vals > 0].min() * 0.5, 1e-4) if (vals > 0).any() else 1e-4
        plot_df = plot_df.copy()
        plot_df[value_col] = plot_df[value_col].clip(lower=floor)
        vals = plot_df[value_col].to_numpy(dtype=float)
        _vmin = vmin if vmin is not None else float(np.nanmin(vals)) * 0.8
        _vmax = vmax if vmax is not None else float(np.nanmax(vals)) * 1.1
        norm = mcolors.LogNorm(vmin=_vmin, vmax=_vmax)
    else:
        _vmin = vmin if vmin is not None else float(np.nanpercentile(vals, 1)) * 0.95
        _vmax = vmax if vmax is not None else float(np.nanpercentile(vals, 99)) * 1.05
        norm = mcolors.Normalize(vmin=_vmin, vmax=_vmax)

    # Layer 2 — IDW surface with ridge masking
    mesh, gx, gy, surf = add_idw_surface(
        ax, plot_df,
        value_col=value_col,
        easting_col="E",
        northing_col="N",
        dem_col="dem",
        xi=GRID_XI,
        yi=GRID_YI,
        method="linear",
        ridge_mask_threshold=1.0,
        dem_e_arr=dem_e_arr,
        dem_n_arr=dem_n_arr,
        dem_data=dem_data,
        cmap=cmap,
        norm=norm,
        alpha=0.65,
        zorder=2,
    )

    # Colorbar
    cb = fig.colorbar(mesh, ax=ax, fraction=0.03, pad=0.02, shrink=0.85)
    cb.set_label(cbar_label, fontsize=9)

    # Contours
    if contour_levels is not None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                cs = ax.contour(
                    gx, gy, surf,
                    levels=contour_levels,
                    colors="black", linewidths=0.6,
                    alpha=0.45, zorder=3,
                )
                ax.clabel(cs, inline=True, fontsize=6,
                          fmt=contour_fmt, inline_spacing=2)
            except Exception:
                pass

    # Layer 3 — KML features
    kml_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

    # Layer 4 — well markers by cluster
    cluster_handles = {}
    for _, row in plot_df.iterrows():
        cid = int(row["Cluster_ID"]) if pd.notna(row.get("Cluster_ID")) else 1
        col = CLUSTER_COLOURS.get(cid, "grey")
        marker = CLUSTER_MARKERS.get(cid, "o")
        ax.scatter(
            row["E"], row["N"],
            c=col, s=30, marker=marker,
            edgecolors="black", linewidths=0.5, zorder=9,
        )
        if cid not in cluster_handles:
            cluster_handles[cid] = Line2D(
                [0], [0], marker=marker, color="w",
                label=CLUSTER_LABELS.get(cid, f"C{cid}"),
                markerfacecolor=col, markeredgecolor="black",
                markersize=9, linestyle="None",
            )

    # Legends
    if kml_handles:
        l1 = ax.legend(
            handles=kml_handles, fontsize=7,
            loc="lower left", framealpha=0.92,
            title="Site features", title_fontsize=8,
        )
        ax.add_artist(l1)

    ax.legend(
        handles=[cluster_handles[k] for k in sorted(cluster_handles)],
        fontsize=8, loc="lower right",
        title="Cluster", title_fontsize=8,
    )

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(title, fontsize=11, fontweight="bold")

    fig.tight_layout()
    fig.savefig(output_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> Saved {output_path.name} ({output_path.stat().st_size // 1024} KB)")


# ------------------------------------------------------------------
# CLUSTER SUMMARY TABLE
# ------------------------------------------------------------------

def make_cluster_summary(master):
    """Print and export cluster-level summary statistics."""
    print("\n  Cluster-level SSM coefficient summary")
    print("  " + "-" * 78)
    header = (
        f"  {'Cluster':<22s} {'n':>3s}  {'β₁ mean':>8s} {'β₂ mean':>8s} "
        f"{'β₃ mean':>8s} {'R² mean':>7s}"
    )
    print(header)
    print("  " + "-" * 78)

    rows = []
    for cid in sorted(master["Cluster"].unique()):
        sub = master[master["Cluster"] == cid]
        label = CLUSTER_LABELS.get(int(cid), f"C{int(cid)}")
        print(
            f"  {label:<22s} {len(sub):3d}  "
            f"{sub['beta_1_recharge'].mean():8.3f} "
            f"{sub['beta_2_atmospheric_draw'].mean():8.3f} "
            f"{sub['beta_3_drainage'].mean():8.4f} "
            f"{sub['Model_R2'].mean():7.3f}"
        )
        rows.append({
            "Cluster": cid,
            "Label": label,
            "n_wells": len(sub),
            "beta_1_mean": sub["beta_1_recharge"].mean(),
            "beta_1_std": sub["beta_1_recharge"].std(),
            "beta_1_min": sub["beta_1_recharge"].min(),
            "beta_1_max": sub["beta_1_recharge"].max(),
            "beta_2_mean": sub["beta_2_atmospheric_draw"].mean(),
            "beta_2_std": sub["beta_2_atmospheric_draw"].std(),
            "beta_2_min": sub["beta_2_atmospheric_draw"].min(),
            "beta_2_max": sub["beta_2_atmospheric_draw"].max(),
            "beta_3_mean": sub["beta_3_drainage"].mean(),
            "beta_3_std": sub["beta_3_drainage"].std(),
            "beta_3_min": sub["beta_3_drainage"].min(),
            "beta_3_max": sub["beta_3_drainage"].max(),
            "R2_mean": sub["Model_R2"].mean(),
            "R2_std": sub["Model_R2"].std(),
        })
    print("  " + "-" * 78)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------

if __name__ == "__main__":
    make_all_dirs()
    DIR_07.mkdir(parents=True, exist_ok=True)

    print("Starting SSM07 Spatial Coefficient Mapping...")

    # Load data
    df = load_coefficient_data()
    master = pd.read_csv(INT_MASTER_DATA)
    print(f"  Loaded {len(df)} wells from {INT_MASTER_DATA.name}")

    # Summary table
    summary_df = make_cluster_summary(master)
    summary_df.to_csv(OUT_SUMMARY_CSV, index=False)
    print(f"  -> Exported cluster summary to {OUT_SUMMARY_CSV.name}")

    # ------------------------------------------------------------------
    # Map 1: β₁ Recharge Sensitivity
    # ------------------------------------------------------------------
    make_coefficient_map(
        df, "beta_1_recharge",
        title=(
            "β₁ Recharge Sensitivity (mm water-table rise per mm rainfall)\n"
            "Per-well SSM coefficient — Newborough Warren"
        ),
        output_path=OUT_BETA1_MAP,
        cmap="YlGnBu",
        cbar_label="β₁ (mm / mm rainfall)",
        contour_levels=np.arange(2.0, 6.5, 0.5),
        contour_fmt="%.1f",
    )

    # ------------------------------------------------------------------
    # Map 2: β₂ Atmospheric Draw (ET sensitivity)
    # ------------------------------------------------------------------
    make_coefficient_map(
        df, "beta_2_atmospheric_draw",
        title=(
            "β₂ Atmospheric Draw (mm water-table decline per mm PET)\n"
            "Per-well SSM coefficient — Newborough Warren"
        ),
        output_path=OUT_BETA2_MAP,
        cmap="YlOrRd",
        cbar_label="β₂ (mm / mm PET)",
        contour_levels=np.arange(0.5, 3.5, 0.5),
        contour_fmt="%.1f",
    )

    # ------------------------------------------------------------------
    # Map 3: β₃ Drainage Rate (log scale)
    # ------------------------------------------------------------------
    # β₃ spans nearly two orders of magnitude (C4 Forest: ~0.008; C1 Lake
    # Edge: ~0.09–0.12). Log scale gives proper visual separation.
    make_coefficient_map(
        df, "beta_3_drainage",
        title=(
            "β₃ Drainage Rate (month⁻¹, log scale)\n"
            "Per-well SSM coefficient — Newborough Warren"
        ),
        output_path=OUT_BETA3_MAP,
        cmap="plasma",
        cbar_label="β₃ (month⁻¹, log scale)",
        log_scale=True,
    )

    # ------------------------------------------------------------------
    # Map 4: R² Model Quality
    # ------------------------------------------------------------------
    make_coefficient_map(
        df, "Model_R2",
        title=(
            "Per-Well SSM Fit Quality (R²)\n"
            "Newborough Warren"
        ),
        output_path=OUT_R2_MAP,
        cmap="RdYlGn",
        cbar_label="R²",
        vmin=0.40,
        vmax=0.90,
        contour_levels=np.arange(0.50, 0.90, 0.10),
        contour_fmt="%.2f",
    )

    # ------------------------------------------------------------------
    # Export map data
    # ------------------------------------------------------------------
    export_cols = [
        "Name_Original", "Cluster_ID", "E", "N", "dem",
        "beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage",
        "pvalue_beta_1", "pvalue_beta_2", "pvalue_beta_3",
        "Model_R2", "n",
    ]
    df[[c for c in export_cols if c in df.columns]].to_csv(
        OUT_MAPS_DATA, index=False,
    )
    print(f"  -> Exported map data to {OUT_MAPS_DATA.name}")

    print("\nSSM07 Spatial Coefficient Mapping complete.")
