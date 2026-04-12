"""
03_state_space_model.py
Purpose: Calculates Lumped Catchment Storage Coefficients (LCSC) and fits the
State-Space Multivariate Regression Model for each well.

Inputs:
    01_locations.csv, 01_climate.csv, 01_wells_clean.csv, 01_well_elevations.csv, 02_cluster_stats.csv

Outputs (intermediate):
    03_master_data.csv
    03_regional_averages.csv

Outputs (final — outputs/03_state_space_model/):
    03_01_mechanistic_signatures.png
"""

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
del _sys, _os

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt

from utils.data_utils import normalize_well_name
from utils.paths import (
    make_all_dirs,
    INT_LOCATIONS, INT_CLIMATE, INT_WELLS_CLEAN, INT_WELL_ELEVATIONS, INT_CLUSTER_STATS,
    INT_MASTER_DATA, INT_REGIONAL_AVG, INT_CLUSTER_AVG_MAOD,
    INT_WELLS_CLEAN_MAOD,
    OUT_03_SIGNATURES, OUT_03_CLUSTER_SUMMARY, OUT_03_MECHANISTIC_TABLE,
)

LCSC_DATA_LIMIT = 100

# C6 (Lake) excluded from block aggregation — lake-buffered hydraulic head
# violates the free-draining assumptions used for block time-series.
BLOCK_MAP = {
    1: "Eastern Block",
    2: "Eastern Block",
    3: "Western Block",
    4: "Forest",
    5: "Coastal",
}


def create_full_coefficient_figure(master_df: pd.DataFrame) -> None:
    print("\n -> Generating 3-Panel State-Space Coefficient Chart...")
    plot_df = master_df.copy()
    plot_df["Cluster"] = pd.to_numeric(plot_df["Cluster"], errors="coerce")
    cluster_summary = (
        plot_df[plot_df["Cluster"].isin([1, 2, 3, 4, 5, 6])]
        .groupby("Cluster")[["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_internal_brake"]]
        .mean()
        .reindex([1, 2, 3, 4, 5, 6])
    )
    if cluster_summary.dropna(how="all").empty:
        print(" -> Skipped (no valid C1–C6 coefficients).")
        return

    labels = ["C1\nEast-Buf", "C2\nEast-Till", "C3\nWest-Sand", "C4\nWest-For", "C5\nTidal", "C6\nLake"]
    colors = ["#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#0072B2"]
    b1 = cluster_summary["beta_1_recharge"].to_numpy()
    b2 = cluster_summary["beta_2_atmospheric_draw"].to_numpy()
    b3 = cluster_summary["beta_3_internal_brake"].to_numpy()

    fig, axes = plt.subplots(1, 3, figsize=(15, 6), dpi=300)
    fig.suptitle("State-Space Mechanistic Signatures by Hydrogeological Cluster",
                 fontsize=18, fontweight="bold", y=1.02)
    for ax, vals, title, ylabel in [
        (axes[0], b1, r"Recharge Sensitivity ($\beta_1$)", "Water Table Rise per mm Rain"),
        (axes[1], b2, r"Atmospheric Draw ($\beta_2$)",     "Water Table Drop per mm PET"),
        (axes[2], b3, r"Internal Drainage Brake ($\beta_3$)", "Proportional Decay Rate"),
    ]:
        ax.bar(labels, vals, color=colors, edgecolor="black", linewidth=1.2, zorder=3)
        ax.set_title(title, fontsize=14, pad=10)
        ax.set_ylabel(ylabel, fontsize=12)
        fmt = ".4f" if ax != axes[2] else ".3f"
        offset = 0.0001 if ax != axes[2] else 0.01
        for i, v in enumerate(vals):
            if np.isfinite(v):
                ax.text(i, v + offset, f"{v:{fmt}}", ha="center", va="bottom", fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=0)
        ax.tick_params(axis="x", rotation=30)
        ax.set_facecolor("#f8f9fa")

    plt.tight_layout()
    plt.savefig(OUT_03_SIGNATURES, bbox_inches="tight")
    plt.close()
    print(f" -> Saved: {OUT_03_SIGNATURES.name}")


def export_cluster_summary_table(cluster_df: pd.DataFrame, centroid_fits: dict) -> None:
    """Export manuscript-style cluster summary table.

    LCSC and R² come from centroid_fits (SSM fitted to cluster average hydrograph)
    so the table is consistent with the methods: one model per cluster centroid,
    not an average of individual well fits.
    """
    if not centroid_fits:
        print(" -> Skipped cluster summary export (no centroid fit results).")
        return

    counts = (
        pd.to_numeric(cluster_df["Cluster"], errors="coerce")
        .dropna()
        .astype(int)
        .value_counts()
        .rename_axis("Cluster")
        .rename("n")
    )

    label_map = {
        1: "Eastern Block Lake-buffer",
        2: "Eastern Block Mature Dune",
        3: "Western Block Mature Dune",
        4: "Forest",
        5: "Coastal",
        6: "Lake",
    }
    location_map = {
        1: "NE sector, Llyn Rhos-ddu",
        2: "Central and SE sector",
        3: "Central-W sector",
        4: "NW sector, plantation",
        5: "SW coastal margin",
        6: "Llyn Rhos-ddu",
    }

    cluster_ids = [1, 2, 3, 4, 5, 6]
    out = pd.DataFrame(
        {
            "Cluster": [f"C{i}" for i in cluster_ids],
            "Label":   [label_map[i] for i in cluster_ids],
            "n":       [int(counts.get(i, 0)) for i in cluster_ids],
            "Location":[location_map[i] for i in cluster_ids],
            "LCSC (%)": [
                round(100.0 / centroid_fits[i]["beta_1"], 1)
                if i in centroid_fits
                   and pd.notna(centroid_fits[i].get("beta_1"))
                   and centroid_fits[i]["beta_1"] > 0
                else np.nan
                for i in cluster_ids
            ],
            "R2": [
                centroid_fits[i]["R2"] if i in centroid_fits else np.nan
                for i in cluster_ids
            ],
        }
    )

    out["LCSC (%)"] = out["LCSC (%)"].map(lambda v: f"{v:.1f}" if pd.notna(v) else "—")
    out.loc[out["Cluster"] == "C6", "LCSC (%)"] = (
        out.loc[out["Cluster"] == "C6", "LCSC (%)"].astype(str) + "*"
    )
    out["R2"] = out["R2"].map(lambda v: f"{v:.1f}" if pd.notna(v) else "—")

    out.to_csv(OUT_03_CLUSTER_SUMMARY, index=False)
    print(f" -> Saved: {OUT_03_CLUSTER_SUMMARY.name}")


def export_cluster_mechanistic_table(cluster_ts: dict[str, pd.Series], climate: pd.DataFrame) -> None:
    """Export Table 2: cluster-level mechanistic coefficients (no-intercept OLS) with p-values."""
    label_map = {
        1: "C1: Eastern Block Lake",
        2: "C2: Eastern Block Mature Dune",
        3: "C3: Western Block Mature Dune",
        4: "C4: Forest",
        5: "C5: Coastal",
        6: "C6: Lake",
    }

    rows = []
    for cid in [1, 2, 3, 4, 5, 6]:
        c_key = f"C{cid}"
        series = cluster_ts.get(c_key)

        if series is None:
            rows.append(
                {
                    "Cluster": c_key,
                    "Label": label_map[cid],
                    "beta_1_mm_wt_rise_per_mm_rain": np.nan,
                    "pvalue_beta_1": np.nan,
                    "beta_2_mm_wt_drop_per_mm_pet": np.nan,
                    "pvalue_beta_2": np.nan,
                    "beta_3_drain_rate": np.nan,
                    "pvalue_beta_3": np.nan,
                    "R2": np.nan,
                    "n": np.nan,
                }
            )
            continue

        df = series.to_frame(name="h").join(climate[["P_m", "PET"]], how="inner")
        df["h_prev"] = df["h"].shift(1)
        df["Delta_h"] = df["h"] - df["h_prev"]
        df = df.dropna(subset=["Delta_h", "P_m", "PET", "h_prev"])

        n_obs = int(len(df))
        if n_obs <= 30:
            rows.append(
                {
                    "Cluster": c_key,
                    "Label": label_map[cid],
                    "beta_1_mm_wt_rise_per_mm_rain": np.nan,
                    "pvalue_beta_1": np.nan,
                    "beta_2_mm_wt_drop_per_mm_pet": np.nan,
                    "pvalue_beta_2": np.nan,
                    "beta_3_drain_rate": np.nan,
                    "pvalue_beta_3": np.nan,
                    "R2": np.nan,
                    "n": n_obs if n_obs > 0 else np.nan,
                }
            )
            continue

        # In mAOD space: higher h_prev = higher water table = more drainage pressure.
        # The drainage term in the SSM is -β₃*h_prev, so the X column is +h_prev
        # and β₃ will be positive (higher mAOD → more drainage → Δh negative).
        # β₁ and β₂ signs are unchanged: rainfall raises mAOD (+), PET lowers it (-).
        X = pd.DataFrame(
            {
                "beta_1_recharge": df["P_m"],
                "beta_2_atmospheric_draw": -df["PET"],
                "beta_3_internal_brake": df["h_prev"],   # +h_prev in mAOD space
            }
        )
        model = sm.OLS(df["Delta_h"], X).fit()

        rows.append(
            {
                "Cluster": c_key,
                "Label": label_map[cid],
                "beta_1_mm_wt_rise_per_mm_rain": model.params["beta_1_recharge"],
                "pvalue_beta_1": model.pvalues["beta_1_recharge"],
                "beta_2_mm_wt_drop_per_mm_pet": model.params["beta_2_atmospheric_draw"],
                "pvalue_beta_2": model.pvalues["beta_2_atmospheric_draw"],
                "beta_3_drain_rate": model.params["beta_3_internal_brake"],
                "pvalue_beta_3": model.pvalues["beta_3_internal_brake"],
                "R2": model.rsquared,
                "n": n_obs,
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_03_MECHANISTIC_TABLE, index=False)
    print(f" -> Saved: {OUT_03_MECHANISTIC_TABLE.name}")

    # Return per-cluster centroid coefficients so the summary table uses
    # coefficients from the centroid fit rather than averaged individual well fits.
    return {
        int(r["Cluster"][1:]): {
            "beta_1": r["beta_1_mm_wt_rise_per_mm_rain"],
            "beta_2": r["beta_2_mm_wt_drop_per_mm_pet"],
            "beta_3": r["beta_3_drain_rate"],
            "R2":     r["R2"],
        }
        for r in rows
    }


if __name__ == "__main__":
    make_all_dirs()
    print("Starting 03: State-Space Regression & LCSC...")

    locs_clean  = pd.read_csv(INT_LOCATIONS)
    cluster_df  = pd.read_csv(INT_CLUSTER_STATS)
    climate     = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    wells_clean = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)

    # Load upstand lookup for centroid datum correction.
    # Before averaging into cluster centroids, each well's depth series is shifted
    # by subtracting its upstand so all wells share a common ground-surface datum.
    # Individual well SSM fits use first-differenced Δh so the offset cancels there.
    upstand_lookup = {}
    if INT_WELL_ELEVATIONS.exists():
        elev_df = pd.read_csv(INT_WELL_ELEVATIONS)
        elev_df.columns = [c.strip() for c in elev_df.columns]
        if "Name_norm" in elev_df.columns and "Upstand_m" in elev_df.columns:
            for _, row in elev_df.iterrows():
                if pd.notna(row.get("Upstand_m")):
                    upstand_lookup[str(row["Name_norm"])] = float(row["Upstand_m"])
        print(f" -> Upstand lookup loaded: {len(upstand_lookup)} wells.")
    else:
        print(" -> [WARNING] Elevation file not found. Centroid upstand correction skipped.")

    locs_clean["Match_ID"] = locs_clean["Match_ID"].apply(normalize_well_name)
    cluster_df["Match_ID"] = cluster_df["Match_ID"].apply(normalize_well_name)
    cluster_ids = sorted(
        pd.to_numeric(cluster_df["Cluster"], errors="coerce").dropna().astype(int).unique()
    )

    if "Name_Original" not in cluster_df.columns:
        cluster_df = cluster_df.merge(locs_clean[["Match_ID", "Name"]], on="Match_ID", how="left")
        cluster_df.rename(columns={"Name": "Name_Original"}, inplace=True)

    map_data = pd.merge(cluster_df, locs_clean, on="Match_ID", how="inner")
    well_col_lookup = {normalize_well_name(col): col for col in wells_clean.columns}

    print(" -> Calculating LCSC and fitting State-Space Models...")
    results = []
    for _, row in map_data.iterrows():
        well_name  = row["Name_Original"]
        target_col = well_col_lookup.get(normalize_well_name(well_name))
        if target_col is None:
            continue

        df = wells_clean[target_col].to_frame(name="h").join(climate[["P_m", "PET"]], how="inner")
        df["h_prev"]  = df["h"].shift(1)
        df["Delta_h"] = df["h"] - df["h_prev"]
        df = df.dropna(subset=["Delta_h", "P_m", "PET", "h_prev"])
        if len(df) > LCSC_DATA_LIMIT:
            df = df.iloc[-LCSC_DATA_LIMIT:]

        recharge_events    = df[df["Delta_h"] > 0.02].copy()
        avg_lcsc_empirical = np.nan
        if len(recharge_events) > 10:
            recharge_events["LCSC_raw"] = recharge_events["P_m"] / recharge_events["Delta_h"]
            valid_lcsc = recharge_events[
                (recharge_events["LCSC_raw"] > 0.05) & (recharge_events["LCSC_raw"] <= 1.0)
            ]
            if len(valid_lcsc) > 0:
                avg_lcsc_empirical = valid_lcsc["LCSC_raw"].mean() * 100

        b1, b2, b3, r2, lcsc_regression = np.nan, np.nan, np.nan, np.nan, np.nan
        if len(df) > 30:
            X = pd.DataFrame({
                "beta_1_recharge":        df["P_m"],
                "beta_2_atmospheric_draw": -df["PET"],
                "beta_3_internal_brake":  -df["h_prev"],
            })
            model = sm.OLS(df["Delta_h"], X).fit()
            b1, b2, b3, r2 = (model.params["beta_1_recharge"],
                               model.params["beta_2_atmospheric_draw"],
                               model.params["beta_3_internal_brake"],
                               model.rsquared)
            lcsc_regression = (1 / b1) * 100 if b1 > 0 else np.nan

        results.append({
            "Name_Original":         target_col,
            "Cluster":               row["Cluster"],
            "Easting":               row["E"],
            "Northing":              row["N"],
            "LCSC_Empirical_Percent":  avg_lcsc_empirical,
            "LCSC_Regression_Percent": lcsc_regression,
            "beta_1_recharge":         b1,
            "beta_2_atmospheric_draw": b2,
            "beta_3_internal_brake":   b3,
            "Model_R2":                r2,
        })

    master_df = pd.DataFrame(results)
    master_df.to_csv(INT_MASTER_DATA, index=False)
    print(f" -> Saved: {INT_MASTER_DATA.name}")

    create_full_coefficient_figure(master_df)

    print("\n" + "=" * 70)
    print(f"   AVERAGE STATISTICS BY CLUSTER ({len(cluster_ids)} Clusters, limit {LCSC_DATA_LIMIT}mo)")
    print("=" * 70)
    print(master_df.groupby("Cluster")[
        ["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_internal_brake",
         "LCSC_Regression_Percent", "LCSC_Empirical_Percent", "Model_R2"]
    ].mean().round(3))

    # Summary table called after mechanistic table to receive centroid_fits

    # Regional averages
    print("\n -> Exporting regional cluster time-series...")
    cluster_ts = {}
    for cid in sorted(
        pd.to_numeric(cluster_df["Cluster"], errors="coerce").dropna().astype(int).unique()
    ):
        c_wells = cluster_df[
            pd.to_numeric(cluster_df["Cluster"], errors="coerce") == cid
        ]["Match_ID"].astype(str).values
        # Resolve normalized Match_ID values back to real wells_clean columns.
        available = [
            well_col_lookup.get(normalize_well_name(w))
            for w in c_wells
            if well_col_lookup.get(normalize_well_name(w)) is not None
        ]
        # Fallback: try stripping spaces (catches "llyn rhos" → "llynrhos")
        if not available:
            available = [
                well_col_lookup.get(normalize_well_name(w.replace(" ", "")))
                for w in c_wells
                if well_col_lookup.get(normalize_well_name(w.replace(" ", ""))) is not None
            ]
        if available:
            if upstand_lookup:
                # Apply upstand correction: shift each well's depth series by its upstand
                # so all wells reference ground surface rather than pipe top.
                corrected = {}
                n_corrected = 0
                for col in available:
                    col_norm = normalize_well_name(col).lower().replace(" ", "").replace("_", "")
                    upstand = upstand_lookup.get(col_norm, None)
                    if upstand is not None:
                        corrected[col] = wells_clean[col] - upstand
                        n_corrected += 1
                    else:
                        corrected[col] = wells_clean[col]
                n_uncorrected = len(available) - n_corrected
                cluster_ts[f"C{cid}"] = pd.DataFrame(corrected).mean(axis=1)
                print(f"    C{cid}: {n_corrected} wells upstand-corrected, {n_uncorrected} uncorrected")
            else:
                cluster_ts[f"C{cid}"] = wells_clean[available].mean(axis=1)

    centroid_fits = export_cluster_mechanistic_table(cluster_ts, climate)
    export_cluster_summary_table(cluster_df, centroid_fits)

    df_export = pd.DataFrame(cluster_ts)
    df_export.index.name = "Date"
    for label, cols in [("Western_Block", ["C3"]), ("Eastern_Block", ["C1", "C2"]),
                         ("Forest", ["C4"]), ("Coastal", ["C5"])]:
        available = [c for c in cols if c in df_export.columns]
        df_export[label] = df_export[available].mean(axis=1)

    master_df["Macro_Block"] = pd.to_numeric(master_df["Cluster"], errors="coerce").map(BLOCK_MAP)
    block_stats = master_df.groupby("Macro_Block")["LCSC_Regression_Percent"].mean()
    print("\n" + "=" * 50)
    print("   FINAL MANUSCRIPT LCSC PERCENTAGES")
    print("=" * 50)
    for block, val in block_stats.items():
        if pd.notna(block):
            print(f" {block:15} : {val:.1f}%")
    print("=" * 50)

    df_export = df_export.join(climate[["P_m", "PET"]])
    df_export.rename(columns={"P_m": "P_mm", "PET": "PET_mm"}, inplace=True)
    df_export["P_mm"]   *= 1000
    df_export["PET_mm"] *= 1000
    df_export.to_csv(INT_REGIONAL_AVG)
    print(f" -> Saved: {INT_REGIONAL_AVG.name}")

    # ── maOD cluster averages ─────────────────────────────────────────────────
    # Compute cluster-mean heads in metres above OD by averaging per-well maOD
    # series from 01_wells_clean_maod.csv across cluster members.
    # This file is consumed by scripts 21 (forestry scenarios) and any other
    # script needing absolute head values rather than depth from pipe top.
    if INT_WELLS_CLEAN_MAOD.exists():
        try:
            maod_df = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0,
                                   parse_dates=True)
            maod_df.columns = [normalize_well_name(c) for c in maod_df.columns]
            cluster_maod_ts = {}
            for cid in sorted(
                pd.to_numeric(cluster_df["Cluster"], errors="coerce")
                .dropna().astype(int).unique()
            ):
                c_wells = cluster_df[
                    pd.to_numeric(cluster_df["Cluster"], errors="coerce") == cid
                ]["Match_ID"].astype(str).values
                available = [
                    normalize_well_name(w) for w in c_wells
                    if normalize_well_name(w) in maod_df.columns
                ]
                if available:
                    cluster_maod_ts[f"C{cid}"] = maod_df[available].mean(axis=1)
            if cluster_maod_ts:
                df_maod = pd.DataFrame(cluster_maod_ts)
                df_maod.index.name = "Date"
                df_maod = df_maod.join(climate[["P_m", "PET"]])
                df_maod.rename(columns={"P_m": "P_mm", "PET": "PET_mm"},
                               inplace=True)
                df_maod["P_mm"]   *= 1000
                df_maod["PET_mm"] *= 1000
                df_maod.to_csv(INT_CLUSTER_AVG_MAOD)
                print(f" -> Saved: {INT_CLUSTER_AVG_MAOD.name}")
            else:
                print("    [WARNING] No maOD cluster averages computed — "
                      "check well name matching")
        except Exception as exc:
            print(f"    [WARNING] maOD cluster averages not written: {exc}")
    else:
        print(f"    [WARNING] {INT_WELLS_CLEAN_MAOD.name} not found — "
              f"run script 01 first. Script 21 will fail without maOD file.")

    print("03 Complete.")
