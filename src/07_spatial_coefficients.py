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
    - outputs/07_spatial_coefficients/07_coeff_05_cluster_ranges.csv  (per-cluster beta ranges; Paper 1 Table 6)
    - outputs/07_spatial_coefficients/07_cluster_coeff_means.csv  (per-cluster mean β₁/β₂/β₃; §4.9)
    - outputs/07_spatial_coefficients/07_report_numbers.csv
    - outputs/07_spatial_coefficients/07_05_clusters_vs_covariates.csv  (T-73: per-well β
      regressed on six site covariates with and without the cluster dummies —
      nested F-test, ΔR²adj, ΔAIC; "all" and "forest_free" panels)
====================================================================================
"""

__version__ = "1.4.0"  # Hollingham (2026) — 2026-09-23. Clusters vs covariates
#   (T-73): new clusters_vs_covariates() regresses each per-well SSM
#   coefficient (β₁, β₂, β₃; the reference wells in 03_master_data.csv) on six
#   site covariates from 01_locations.csv (dist_coast_m, dist_lake_m,
#   ground_elev_m, in_forest, E, N) with and without C(Cluster), and emits the
#   nested F-test, ΔR²adj and ΔAIC per coefficient for the full panel and the
#   forest-free panel (six rows) to 07_05_clusters_vs_covariates.csv. The three
#   full-panel F p-values and ΔAIC also go to 07_report_numbers.csv (the CSV is
#   the primary artefact). Existing outputs unchanged.
#
# 1.3.0 (2026-09-23): Progress reporting
#   (T-76): the four sequential make_coefficient_map() calls (beta_1, beta_2,
#   beta_3, R2) turned into a tracked builder list (console_utils.track,
#   lines=True — each builder already prints its own "Saved ..." step()), the
#   Script 20 precedent for a script whose time is a sequence of builder calls.
#   No output changes. Martin, 2026-09-23: a script that runs past 30 s shows
#   progress (T-76).
#
# 1.2.1 (2026-08-16): map-extent note only, no behaviour change (GRID_YI
#   northern edge 365800 vs config.SITE_MAP_NORTH_MAX 365500; see the note
#   at GRID_YI and DECISION_LOG D-013).
# 1.2.0 (2026-06-21): prior state.
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    OUT_DIR,
    INT_MASTER_DATA,
    INT_WELL_ELEVATIONS,
    INT_LOCATIONS,
    OUT_07_CLUSTER_COEFF_MEANS,
    OUT_07_REPORT_NUMBERS,
    OUT_07_CLUSTERS_VS_COVARIATES,
)
from utils.report_numbers_utils import ReportNumbers
from utils.map_utils import (
    load_dem_hillshade,
    add_idw_surface,
    add_kml_features,
    add_en_axes,
)
from utils.data_utils import normalize_well_name
from utils.config import (
    DRAINAGE_DATUM,
    LAKE_GAUGE_KEYS,
    CLUSTER_LABELS,
    CLUSTER_COLOURS,
    CLUSTER_MARKERS,
    BW_MODE,
    get_cmap,
)
import warnings
import matplotlib

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped, track,
)
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

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
OUT_CLUSTER_RANGES = DIR_07 / "07_coeff_05_cluster_ranges.csv"

# ==========================================
# GRID — matches scripts 11b / 19 / 20
# ==========================================
GRID_XI = np.arange(240200, 243800, 50)
# NOTE (2026-08-16): the northern edge here is 365800, NOT config.SITE_MAP_NORTH_MAX
# (365500). Retained deliberately - Martin's call - so this figure's framing is
# unchanged by the config extent revision, matching the explicit local pin in
# 11c_pflood_achievability.py (_NORTH_MAX_11C). Do NOT repoint to config without
# a decision: it re-frames the rendered maps. See DECISION_LOG D-013.
GRID_YI = np.arange(362200, 365800, 50)

# ==========================================
# AESTHETICS
# ==========================================
# Font sizes chosen so that everything remains ≥ 6 pt when the figure
# is scaled to half an A4 page width (210 mm).  Scale factor ≈ 0.69,
# so 9 pt in-figure → 6.2 pt on page.  Nothing below 9 pt.
DPI = 200
plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.labelsize": 11,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
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
        elev[["wn", "ground_elev_m"]],
        on="wn", how="left",
    )
    df = df.rename(columns={
        "Easting": "E",
        "Northing": "N",
        "ground_elev_m": "dem",
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
        warn(f"No data for {value_col}. Skipping {output_path.name}")
        return

    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")

    # Layer 1 — DEM hillshade
    _, ok, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1,
    )
    if not ok:
        warn("DEM hillshade unavailable — map will lack terrain context.")

    add_en_axes(ax, label_fontsize=11, labelsize=10)

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
    # BW mode: disable ridge mask for cleaner contour visibility
    _ridge_thresh = None if BW_MODE else 1.0
    mesh, gx, gy, surf = add_idw_surface(
        ax, plot_df,
        value_col=value_col,
        easting_col="E",
        northing_col="N",
        dem_col="dem",
        xi=GRID_XI,
        yi=GRID_YI,
        method="linear",
        ridge_mask_threshold=_ridge_thresh,
        dem_e_arr=dem_e_arr,
        dem_n_arr=dem_n_arr,
        dem_data=dem_data,
        cmap=cmap,
        norm=norm,
        alpha=0.65,
        zorder=2,
    )
    if BW_MODE:
        ax.annotate(
            "Note: interpolation extends across dune ridges;\n"
            "ridge-top values should be interpreted with caution.",
            xy=(0.02, 0.02), xycoords="axes fraction", fontsize=7,
            color="#444444", fontstyle="italic",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85, ec="#aaaaaa"),
            zorder=10,
        )

    # Colorbar
    cb = fig.colorbar(mesh, ax=ax, fraction=0.03, pad=0.02, shrink=0.85)
    cb.set_label(cbar_label, fontsize=11)

    # Contours
    if contour_levels is not None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                cs = ax.contour(
                    gx, gy, surf,
                    levels=contour_levels,
                    colors="black", linewidths=1.2,
                    alpha=0.7, zorder=3,
                )
                ax.clabel(cs, inline=True, fontsize=9,
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
                markersize=10, linestyle="None",
            )

    # Legends
    if kml_handles:
        l1 = ax.legend(
            handles=kml_handles, fontsize=10,
            loc="lower left", framealpha=0.92,
            title="Site features", title_fontsize=10,
        )
        ax.add_artist(l1)

    ax.legend(
        handles=[cluster_handles[k] for k in sorted(cluster_handles)],
        fontsize=10, loc="lower right",
        title="Cluster", title_fontsize=10,
    )

    ax.set_title(title, fontsize=13, fontweight="bold")

    fig.tight_layout()
    fig.savefig(output_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    step(f"Saved {output_path.name} ({output_path.stat().st_size // 1024} KB)")


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
# CLUSTERS VS COVARIATES (T-73)
# ------------------------------------------------------------------

# Per-well SSM coefficient columns of 03_master_data.csv, in the order the
# rows of 07_05_clusters_vs_covariates.csv are emitted.
_CVC_COEFFICIENTS = ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage")

# The six site covariates of Model 0 (formula terms, in column order) and the
# short names their covariate-only p-values are emitted under.
_CVC_COVARIATES = (
    ("dist_coast_m",  "p_dist_coast"),
    ("dist_lake_m",   "p_dist_lake"),
    ("ground_elev_m", "p_ground_elev"),
    ("in_forest",     "p_in_forest"),
    ("E",             "p_easting"),
    ("N",             "p_northing"),
)


def load_well_covariates(master):
    """
    Attach the six Model 0 covariates from 01_locations.csv to the per-well
    SSM coefficient table.

    Wells are matched on normalize_well_name(Name_Original) against the
    location file's Match_ID. dist_lake_m is the Euclidean distance from the
    well to the Llyn Rhos-Ddu gauge row of the same file (found through
    config.LAKE_GAUGE_KEYS, the Script 12 precedent — its coordinates are never
    typed). in_forest is carried as 0/1.
    """
    loc = pd.read_csv(INT_LOCATIONS)
    loc["wn"] = loc["Match_ID"].astype(str).apply(normalize_well_name)

    lake_key = loc["Name"].astype(str).str.strip().str.lower()
    lake = loc[lake_key.isin({k.lower() for k in LAKE_GAUGE_KEYS})]
    if lake.empty:
        raise ValueError(
            f"Llyn Rhos-Ddu gauge not found in {INT_LOCATIONS.name} "
            f"(config.LAKE_GAUGE_KEYS); dist_lake_m cannot be computed"
        )
    lake_e = float(lake["E"].iloc[0])
    lake_n = float(lake["N"].iloc[0])
    loc["dist_lake_m"] = np.hypot(loc["E"] - lake_e, loc["N"] - lake_n)
    loc["in_forest"] = loc["in_forest"].astype(bool).astype(int)

    cov_cols = ["wn", "E", "N", "ground_elev_m", "dist_coast_m", "dist_lake_m", "in_forest"]
    df = master.copy()
    df["wn"] = df["Name_Original"].apply(normalize_well_name)
    df = df.merge(loc[cov_cols], on="wn", how="left", validate="one_to_one")

    missing = df[df[cov_cols[1:]].isna().any(axis=1)]
    if len(missing):
        warn(f"{len(missing)} well(s) lack a covariate in {INT_LOCATIONS.name} "
             f"and are dropped from the covariate comparison: "
             f"{', '.join(missing['Name_Original'].astype(str))}")
        df = df.drop(missing.index)
    return df


def clusters_vs_covariates(df):
    """
    Do the cluster labels carry structure in the per-well SSM coefficients
    beyond six continuous / land-cover covariates?

    For each of β₁, β₂, β₃:
        Model 0:  β ~ 1 + dist_coast_m + dist_lake_m + ground_elev_m
                        + in_forest + E + N
        Model 1:  Model 0 + C(Cluster)
    and the nested F-test of the cluster dummies (statsmodels
    compare_f_test), ΔR²adj and ΔAIC (Model 1 − Model 0). Run on the full
    reference panel ("all") and again on the forest-free panel
    (in_forest == 0, "forest_free"), where in_forest is constant and so drops
    out of both models — the reviewer's question of whether the cluster
    effect is only the forest flag. Nothing is centred or scaled: a nested
    comparison is invariant to it.

    Returns the six-row DataFrame written to 07_05_clusters_vs_covariates.csv.
    """
    panels = [
        ("all", df),
        ("forest_free", df[df["in_forest"] == 0]),
    ]
    rows = []
    for panel, sub in panels:
        sub = sub.copy()
        if panel == "forest_free":
            # in_forest is identically zero here; keep the design full-rank.
            sub = sub.drop(columns=["in_forest"])
            terms = [(t, p) for t, p in _CVC_COVARIATES if t != "in_forest"]
        else:
            terms = list(_CVC_COVARIATES)
        rhs0 = " + ".join(t for t, _ in terms)
        for coef in _CVC_COEFFICIENTS:
            m0 = smf.ols(f"{coef} ~ {rhs0}", data=sub).fit()
            m1 = smf.ols(f"{coef} ~ {rhs0} + C(Cluster)", data=sub).fit()
            f_stat, f_p, df_num = m1.compare_f_test(m0)
            row = {
                "panel": panel,
                "coefficient": coef,
                "n": int(m1.nobs),
                "n_clusters": int(sub["Cluster"].nunique()),
                "R2_adj_covariates": float(m0.rsquared_adj),
                "R2_adj_with_clusters": float(m1.rsquared_adj),
                "delta_R2_adj": float(m1.rsquared_adj - m0.rsquared_adj),
                "AIC_covariates": float(m0.aic),
                "AIC_with_clusters": float(m1.aic),
                "delta_AIC": float(m1.aic - m0.aic),
                "F_stat": float(f_stat),
                "F_pvalue": float(f_p),
                "df_num": int(df_num),
                "df_den": int(m1.df_resid),
            }
            for term, pcol in _CVC_COVARIATES:
                row[pcol] = float(m0.pvalues[term]) if term in m0.pvalues.index else np.nan
            rows.append(row)
            step(
                f"{panel:<11s} {coef:<24s} n={row['n']:2d}  "
                f"R²adj {row['R2_adj_covariates']:.3f} → {row['R2_adj_with_clusters']:.3f}  "
                f"ΔAIC {row['delta_AIC']:+.1f}  "
                f"F({row['df_num']},{row['df_den']}) = {row['F_stat']:.2f}, p = {row['F_pvalue']:.3g}"
            )
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
    step(f"Exported cluster summary to {OUT_SUMMARY_CSV.name}")

    # β₃ spans nearly two orders of magnitude (C4 Forest: ~0.8%; C1 Lake
    # Edge: ~9–12%). Log scale gives proper visual separation.
    # Convert to percentage for intuitive reading. (Computed ahead of the
    # builder list below so Map 3's builder can be a plain lambda.)
    df["beta_3_pct"] = df["beta_3_drainage"] * 100

    # Four map builders in one tracked sequence (console_utils.track 1.2.0,
    # T-76): a script past 30 s prints a completion line per map with elapsed
    # and remaining time, per Martin's rule that a long run must show it is
    # running.
    map_builders = [
        # ------------------------------------------------------------------
        # Map 1: β₁ Recharge Sensitivity
        # ------------------------------------------------------------------
        ("β1 recharge sensitivity", lambda: make_coefficient_map(
            df, "beta_1_recharge",
            title=(
                "β₁ Recharge Sensitivity (mm water-table rise per mm rainfall)\n"
                "Per-well SSM coefficient — Newborough Warren"
            ),
            output_path=OUT_BETA1_MAP,
            cmap=get_cmap("YlGnBu"),
            cbar_label="β₁ (mm / mm rainfall)",
            contour_levels=np.arange(2.0, 6.5, 0.5),
            contour_fmt="%.1f",
        )),
        # ------------------------------------------------------------------
        # Map 2: β₂ Atmospheric Draw (ET sensitivity)
        # ------------------------------------------------------------------
        ("β2 atmospheric draw", lambda: make_coefficient_map(
            df, "beta_2_atmospheric_draw",
            title=(
                "β₂ Atmospheric Draw (mm water-table decline per mm PET)\n"
                "Per-well SSM coefficient — Newborough Warren"
            ),
            output_path=OUT_BETA2_MAP,
            cmap=get_cmap("YlOrRd"),
            cbar_label="β₂ (mm / mm PET)",
            contour_levels=np.arange(0.5, 3.5, 0.5),
            contour_fmt="%.1f",
        )),
        # ------------------------------------------------------------------
        # Map 3: β₃ Drainage Rate (log scale, expressed as %)
        # ------------------------------------------------------------------
        ("β3 drainage rate (log scale)", lambda: make_coefficient_map(
            df, "beta_3_pct",
            title=(
                "β₃ Drainage Rate (% head drained / month, log scale)\n"
                "Per-well SSM coefficient — Newborough Warren"
            ),
            output_path=OUT_BETA3_MAP,
            cmap=get_cmap("plasma"),
            cbar_label="β₃ (% head drained / month)",
            log_scale=True,
            contour_levels=[0.5, 1.0, 2.0, 5.0, 10.0],
            contour_fmt="%.1f",
        )),
        # ------------------------------------------------------------------
        # Map 4: R² Model Quality
        # ------------------------------------------------------------------
        ("R² model quality", lambda: make_coefficient_map(
            df, "Model_R2",
            title=(
                "Per-Well SSM Fit Quality (R²)\n"
                "Newborough Warren"
            ),
            output_path=OUT_R2_MAP,
            cmap=get_cmap("RdYlGn"),
            cbar_label="R²",
            vmin=0.40,
            vmax=0.90,
            contour_levels=np.arange(0.50, 0.90, 0.10),
            contour_fmt="%.2f",
        )),
    ]
    for _label, _build in track(map_builders, lambda b: b[0], lines=True):
        _build()

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
    step(f"Exported map data to {OUT_MAPS_DATA.name}")

    # ------------------------------------------------------------------
    # Export per-cluster coefficient ranges (Paper 1 Table 6)
    # Per-cluster min/max of the per-well SSM coefficients, so the
    # tabulated ranges have a findable source CSV.
    # ------------------------------------------------------------------
    _coef_cols = ["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage"]
    _range_rows = []
    for _cid, _grp in df.groupby("Cluster_ID"):
        _row = {
            "Cluster_ID": int(_cid),
            "Cluster": CLUSTER_LABELS.get(int(_cid), f"C{int(_cid)}"),
            "n": int(len(_grp)),
        }
        for _c in _coef_cols:
            _row[f"{_c}_min"] = float(_grp[_c].min())
            _row[f"{_c}_max"] = float(_grp[_c].max())
        _range_rows.append(_row)
    pd.DataFrame(_range_rows).sort_values("Cluster_ID").to_csv(
        OUT_CLUSTER_RANGES, index=False,
    )
    step(f"Exported per-cluster coefficient ranges to {OUT_CLUSTER_RANGES.name}")

    # ------------------------------------------------------------------
    # §4.9 traceability: per-cluster MEAN coefficients + report numbers
    # Means of the per-well SSM coefficients (uniform DRAINAGE_DATUM, read
    # from 03_master_data.csv), so the cited §4.9 cluster means have a
    # findable source. β₃ also reported as % head drained / month.
    # ------------------------------------------------------------------
    _mean_rows = []
    for _cid, _grp in df.groupby("Cluster_ID"):
        _row = {
            "Cluster_ID": int(_cid),
            "Cluster": CLUSTER_LABELS.get(int(_cid), f"C{int(_cid)}"),
            "n": int(len(_grp)),
        }
        for _c in _coef_cols:
            _row[f"{_c}_mean"] = float(_grp[_c].mean())
        _row["beta_3_pct_mean"] = float(_grp["beta_3_drainage"].mean()) * 100.0
        _mean_rows.append(_row)
    _means_df = pd.DataFrame(_mean_rows).sort_values("Cluster_ID")
    _means_df.to_csv(OUT_07_CLUSTER_COEFF_MEANS, index=False)
    step(f"Exported per-cluster coefficient means to {OUT_07_CLUSTER_COEFF_MEANS.name}")

    # ------------------------------------------------------------------
    # Clusters vs covariates (T-73): do the cluster labels explain the
    # per-well β beyond six site covariates? Nested F-test per coefficient,
    # full panel and forest-free panel.
    # ------------------------------------------------------------------
    hr()
    info("Clusters vs covariates (T-73): per-well β on six site covariates, "
         "with and without C(Cluster)")
    cvc_df = clusters_vs_covariates(load_well_covariates(master))
    cvc_df.to_csv(OUT_07_CLUSTERS_VS_COVARIATES, index=False)
    saved(OUT_07_CLUSTERS_VS_COVARIATES)
    hr()

    rpt = ReportNumbers()
    for _, _r in _means_df.iterrows():
        _cl = f"C{int(_r['Cluster_ID'])}"
        rpt.add(f"{_cl}_beta1_mean", _r["beta_1_recharge_mean"], unit="mm/mm",
                note=f"mean β₁ recharge, {_cl}, {DRAINAGE_DATUM:g} m datum, n={int(_r['n'])}")
        rpt.add(f"{_cl}_beta2_mean", _r["beta_2_atmospheric_draw_mean"], unit="mm/mm",
                note=f"mean β₂ atmospheric draw, {_cl}, {DRAINAGE_DATUM:g} m datum, n={int(_r['n'])}")
        rpt.add(f"{_cl}_beta3_mean", _r["beta_3_drainage_mean"], unit="/month",
                note=f"mean β₃ drainage, {_cl}, {DRAINAGE_DATUM:g} m datum, n={int(_r['n'])}")
        rpt.add(f"{_cl}_beta3_pct_mean", _r["beta_3_pct_mean"], unit="%/month",
                note=f"mean β₃ as % head drained/month, {_cl}")
    # CEH14: cited negative β₃ (lateral recharge from the rock ridge)
    _ceh14 = df[df["Name_Original"].astype(str).str.lower().str.replace(" ", "") == "ceh14"]
    if len(_ceh14):
        rpt.add("CEH14_beta3", float(_ceh14["beta_3_drainage"].iloc[0]), unit="/month",
                well="CEH14", note="negative β₃ — lateral recharge from rock ridge (C4)")
        rpt.add("CEH14_beta3_pct", float(_ceh14["beta_3_drainage"].iloc[0]) * 100.0,
                unit="%/month", well="CEH14", note="negative β₃ as %")
    # T-73: clusters vs covariates, full panel only — the nested F-test p-value
    # and ΔAIC for C(Cluster) over the six covariates, per coefficient. The
    # primary artefact is 07_05_clusters_vs_covariates.csv.
    _cvc_short = {"beta_1_recharge": "beta_1", "beta_2_atmospheric_draw": "beta_2",
                  "beta_3_drainage": "beta_3"}
    for _, _r in cvc_df[cvc_df["panel"] == "all"].iterrows():
        _b = _cvc_short[_r["coefficient"]]
        rpt.add(f"clusters_vs_covariates_F_p_{_b}", _r["F_pvalue"], unit="",
                note=(f"nested F-test p, C(Cluster) over six site covariates, per-well "
                      f"{_r['coefficient']}, n={int(_r['n'])}, "
                      f"F({int(_r['df_num'])},{int(_r['df_den'])}); 07_05_clusters_vs_covariates.csv"))
        rpt.add(f"clusters_vs_covariates_dAIC_{_b}", _r["delta_AIC"], unit="",
                note=(f"AIC(covariates + C(Cluster)) − AIC(covariates), per-well "
                      f"{_r['coefficient']}, n={int(_r['n'])}; negative favours clusters"))
    n_saved = rpt.save(OUT_07_REPORT_NUMBERS)
    step(f"Exported {n_saved} report numbers to {OUT_07_REPORT_NUMBERS.name}")

    print("\nSSM07 Spatial Coefficient Mapping complete.")
