r"""
====================================================================================
10b — SPATIAL STEP-CHANGE MAPS: SCRAPING & CLEARFELL INTERVENTIONS
====================================================================================
Four publication-quality figures:
  1. Raw step change — Scraping   (scrape-era mean minus pre-scrape mean)
  2. Raw step change — Clearfell  (post-felling mean minus scrape-era mean)
  3. Climate-corrected — Scraping (C3W controls median subtracted)
  4. Climate-corrected — Clearfell (C3W controls median subtracted)

Climate correction:
  Uses a western C3 subset (NW5, NW6, NW7, CEH1) — intentionally different
  from the ANCOVA climate controls in clearfell_common.  These 4 wells share
  the western climate signal AND coastal position with the intervention zones,
  absorbing most of the coastal erosion signal in one step.

Uses the full well network (~75 wells), IDW interpolation with DEM hillshade,
ridge masking, and KML overlays. Right-side vertical colourbar matches the
report's other spatial figures (plot_metric_map convention).

Well labels annotated for all 5-tier BACI network wells (Impact, Edge,
C4 Forest Ctrl, C5 Coastal Ctrl) from clearfell_common.

Depth convention: negative = shallower (water table rose); positive = deeper.

Dependencies:
  utils/clearfell_common.py — intervention dates, well tier lists

Outputs:
  outputs/10_clearfell_baci/10b_spatial_scrape_raw.png
  outputs/10_clearfell_baci/10b_spatial_fell_raw.png
  outputs/10_clearfell_baci/10b_spatial_scrape_corrected.png
  outputs/10_clearfell_baci/10b_spatial_fell_corrected.png
  outputs/10_clearfell_baci/10b_spatial_step_data.csv
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1 import make_axes_locatable

from utils.paths import (
    make_all_dirs, INT_WELLS_CLEAN, INT_WELLS_EXTENDED,
    INT_MASTER_DATA, DATA_DIR, DATA_LOCATIONS_RAW,
    OUT_10B_SCRAPE_RAW, OUT_10B_FELL_RAW,
    OUT_10B_SCRAPE_CORRECTED, OUT_10B_FELL_CORRECTED,
    OUT_10B_STEP_DATA,
)
from utils.data_utils import clean_well_series, normalize_well_name
from utils.map_utils import (
    load_dem_hillshade, add_idw_surface, add_kml_features,
)
from utils.config import (
    CLUSTER_COLOURS, CLUSTER_LABELS, CLUSTER_MARKERS,
)
from utils.clearfell_common import (
    INTERVENTION_DATE, SCRAPING_DATE,
    IMPACT_WELLS, EDGE_WELLS,
    FOREST_CONTROL_WELLS, COASTAL_CONTROL_WELLS, CLIMATE_CONTROL_WELLS,
)

__version__ = "1.1.0"

# ── Output paths (imported from utils.paths) ────────────────────────────────
# OUT_10B_SCRAPE_RAW, OUT_10B_FELL_RAW, OUT_10B_SCRAPE_CORRECTED,
# OUT_10B_FELL_CORRECTED, OUT_10B_STEP_DATA

# ── Era boundaries ──────────────────────────────────────────────────────────
# SCRAPING_DATE and INTERVENTION_DATE imported from clearfell_common
MIN_MONTHS        = 6   # minimum observations per era for inclusion

# Climate reference wells — C3 western subset for spatial correction.
# Intentionally different from the ANCOVA climate controls (clearfell_common):
# these 4 wells share the western climate signal AND coastal position with
# the intervention zones, absorbing most of the coastal erosion signal.
CLIMATE_REF_WELLS = ['nw5', 'nw6', 'nw7', 'ceh1']

# Wells excluded from plotting (retained in exported CSV)
PLOT_EXCLUDE = {'ceh37', 'ceh8', 'fe1', 'fe2', 'fe3', 'fe4'}  # data quality / short records

# Map extent
XLIM = (240200, 243800)
YLIM = (362200, 365000)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
})


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    make_all_dirs()

    # ══════════════════════════════════════════════════════════════════════════
    # 1. LOAD DATA
    # ══════════════════════════════════════════════════════════════════════════
    print("1. Loading well time series...")
    wells_main = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells_main.columns = [normalize_well_name(c) for c in wells_main.columns]
    wells_ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
    wells_ext.columns = [normalize_well_name(c) for c in wells_ext.columns]
    new_cols = [c for c in wells_ext.columns if c not in wells_main.columns]
    wells = pd.concat([wells_main, wells_ext[new_cols]], axis=1)
    for col in wells.columns:
        wells[col] = clean_well_series(wells[col])
    print(f"   {len(wells.columns)} well columns loaded")

    # Well locations
    locs = pd.read_csv(DATA_LOCATIONS_RAW)
    locs["match"] = locs["Name"].apply(normalize_well_name)

    # Master data for cluster assignments
    master = pd.read_csv(INT_MASTER_DATA)
    master["match"] = master["Name_Original"].apply(normalize_well_name)


    # ══════════════════════════════════════════════════════════════════════════════
    # 2. COMPUTE STEP CHANGES FOR ALL WELLS
    # ══════════════════════════════════════════════════════════════════════════════
    print("2. Computing step changes...")

    mask_pre    = wells.index < SCRAPING_DATE
    mask_scrape = (wells.index >= SCRAPING_DATE) & (wells.index < INTERVENTION_DATE)
    mask_post   = wells.index >= INTERVENTION_DATE

    rows = []
    for col in wells.columns:
        s = wells[col]
        n_pre    = s[mask_pre].notna().sum()
        n_scrape = s[mask_scrape].notna().sum()
        n_post   = s[mask_post].notna().sum()

        mean_pre    = s[mask_pre].mean()    if n_pre >= MIN_MONTHS    else np.nan
        mean_scrape = s[mask_scrape].mean() if n_scrape >= MIN_MONTHS else np.nan
        mean_post   = s[mask_post].mean()   if n_post >= MIN_MONTHS   else np.nan

        scrape_step = mean_scrape - mean_pre    if pd.notna(mean_scrape) and pd.notna(mean_pre) else np.nan
        fell_step   = mean_post - mean_scrape   if pd.notna(mean_post) and pd.notna(mean_scrape) else np.nan

        loc_match = locs[locs["match"] == col]
        if loc_match.empty:
            continue
        lr = loc_match.iloc[0]

        m_match = master[master["match"] == col]
        cluster = int(m_match.iloc[0]["Cluster"]) if not m_match.empty else 0

        rows.append({
            "well": col,
            "E": lr["E"],
            "N": lr["N"],
            "dem": lr["DEM_Ground_Elev"],
            "cluster": cluster,
            "mean_pre": mean_pre,
            "mean_scrape": mean_scrape,
            "mean_post": mean_post,
            "scrape_step": scrape_step,
            "fell_step": fell_step,
            "n_pre": n_pre,
            "n_scrape": n_scrape,
            "n_post": n_post,
        })

    df = pd.DataFrame(rows)

    # ── Climate correction (C3W controls) ────────────────────────────────────
    ref_mask = df["well"].isin(CLIMATE_REF_WELLS)
    climate_scrape = df.loc[ref_mask, "scrape_step"].median()
    climate_fell   = df.loc[ref_mask, "fell_step"].median()
    n_ref = int(ref_mask.sum())

    print(f"   Climate reference (C3W controls, n={n_ref}: "
          f"{', '.join(w.upper() for w in CLIMATE_REF_WELLS)}):")
    print(f"     Scraping baseline: {climate_scrape:+.4f} m")
    print(f"     Clearfell baseline: {climate_fell:+.4f} m")

    df["scrape_step_cc"] = df["scrape_step"] - climate_scrape
    df["fell_step_cc"]   = df["fell_step"]   - climate_fell

    df_scrape = df.dropna(subset=["scrape_step"]).copy()
    df_scrape = df_scrape[~df_scrape["well"].isin(PLOT_EXCLUDE)]
    df_fell   = df.dropna(subset=["fell_step"]).copy()
    df_fell   = df_fell[~df_fell["well"].isin(PLOT_EXCLUDE)]
    print(f"   Scrape step: {len(df_scrape)} wells")
    print(f"   Clearfell step: {len(df_fell)} wells")


    # ══════════════════════════════════════════════════════════════════════════════
    # 3. COLOUR SCALES (shared across raw / corrected pairs)
    # ══════════════════════════════════════════════════════════════════════════════
    all_raw = pd.concat([df_scrape["scrape_step"], df_fell["fell_step"]])
    vmax_raw = float(np.nanpercentile(np.abs(all_raw), 97)) * 1.15
    vmax_raw = max(vmax_raw, 0.10)
    norm_raw = mcolors.TwoSlopeNorm(vmin=-vmax_raw, vcenter=0.0, vmax=vmax_raw)

    all_cc = pd.concat([df_scrape["scrape_step_cc"], df_fell["fell_step_cc"]])
    vmax_cc = float(np.nanpercentile(np.abs(all_cc.dropna()), 97)) * 1.15
    vmax_cc = max(vmax_cc, 0.08)
    norm_cc = mcolors.TwoSlopeNorm(vmin=-vmax_cc, vcenter=0.0, vmax=vmax_cc)

    CMAP = "RdBu"


    # ══════════════════════════════════════════════════════════════════════════════
    # 4. PLOTTING FUNCTION
    # ══════════════════════════════════════════════════════════════════════════════
    # Labels for clearfell-area wells (always annotated)
    # Uses the full 5-tier BACI network from clearfell_common
    HIGHLIGHT_WELLS = set(
        IMPACT_WELLS + EDGE_WELLS +
        FOREST_CONTROL_WELLS + COASTAL_CONTROL_WELLS
    )


    def plot_spatial_step(panel_df, value_col, norm, title, cbar_label, out_path):
        """
        Single publication-quality spatial step-change map.

        Right-side vertical colourbar to match report convention (plot_metric_map).
        """
        fig, ax = plt.subplots(figsize=(14, 11), dpi=300)

        # ── Hillshade background ────────────────────────────────────────────────
        hs_mesh, dem_ok, dem_e, dem_n, dem_data = load_dem_hillshade(
            ax, DATA_DIR, alpha=0.9, vert_exag=3.0, zorder=1,
        )

        # ── IDW surface ─────────────────────────────────────────────────────────
        xi = np.arange(XLIM[0], XLIM[1], 40)
        yi = np.arange(YLIM[0], YLIM[1], 40)
        mesh, gx, gy, surf = add_idw_surface(
            ax, panel_df, value_col,
            easting_col="E", northing_col="N", dem_col="dem",
            xi=xi, yi=yi, method="linear",
            ridge_mask_threshold=1.0,
            dem_e_arr=dem_e, dem_n_arr=dem_n, dem_data=dem_data,
            cmap=CMAP, norm=norm, alpha=0.55, zorder=2,
        )

        # ── KML overlays ────────────────────────────────────────────────────────
        feat_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

        # ── Well scatter (cluster-coded markers) ────────────────────────────────
        cluster_handles = []
        for cid in sorted(panel_df["cluster"].unique()):
            sub = panel_df[panel_df["cluster"] == cid]
            marker = CLUSTER_MARKERS.get(cid, "o") if cid > 0 else "o"
            label  = CLUSTER_LABELS.get(cid, "Extended") if cid > 0 else "Extended"
            edgecol = "black" if cid > 0 else "dimgrey"
            ax.scatter(
                sub["E"], sub["N"],
                c=sub[value_col], cmap=CMAP, norm=norm,
                s=100, marker=marker, edgecolor=edgecol,
                linewidth=0.6, alpha=0.95, zorder=5,
            )
            cluster_handles.append(
                Line2D([0], [0], marker=marker, color="w",
                       markerfacecolor="grey", markeredgecolor=edgecol,
                       markersize=10, linestyle="None", label=label)
            )

        # ── Well labels for clearfell-area wells ────────────────────────────────
        for _, r in panel_df.iterrows():
            if r["well"] in HIGHLIGHT_WELLS and YLIM[0] <= r["N"] <= YLIM[1]:
                ax.annotate(
                    r["well"].upper(), (r["E"], r["N"]),
                    textcoords="offset points", xytext=(6, 5),
                    fontsize=7, color="black", fontweight="bold",
                    bbox=dict(fc="white", alpha=0.7, pad=1.0, edgecolor="none"),
                    zorder=6,
                )

        # ── Axes ────────────────────────────────────────────────────────────────
        ax.set_xlim(*XLIM)
        ax.set_ylim(*YLIM)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("Easting (m)")
        ax.set_ylabel("Northing (m)")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_title(title, fontweight="bold")

        # ── RIGHT-SIDE COLOURBAR (report convention) ────────────────────────────
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="2.75%", pad=0.6)
        cbar = fig.colorbar(mesh, cax=cax, extend="both")
        cbar.set_label(cbar_label, rotation=270, labelpad=28, fontsize=12)
        cbar.ax.tick_params(labelsize=10)

        # ── Legends ─────────────────────────────────────────────────────────────
        if cluster_handles:
            leg_c = ax.legend(
                handles=cluster_handles, title="Cluster",
                loc="lower left", frameon=True, framealpha=0.9,
                fontsize=9, title_fontsize=10,
            )
            ax.add_artist(leg_c)
        if feat_handles:
            leg_f = ax.legend(
                handles=feat_handles, title="Site Features",
                loc="upper right", frameon=True, framealpha=0.9,
                fontsize=9, title_fontsize=10,
            )
            ax.add_artist(leg_f)

        # ── Summary stats box ───────────────────────────────────────────────────
        mean_val = panel_df[value_col].mean()
        med_val  = panel_df[value_col].median()
        sd_val   = panel_df[value_col].std()
        n_wells  = len(panel_df)
        stats_text = (f"n = {n_wells} wells\n"
                      f"Mean: {mean_val:+.3f} m\n"
                      f"Median: {med_val:+.3f} m\n"
                      f"SD: {sd_val:.3f} m")
        ax.text(0.02, 0.52, stats_text, transform=ax.transAxes,
                fontsize=9, va="top", ha="left", family="monospace",
                bbox=dict(fc="white", alpha=0.85, edgecolor="lightgrey", pad=4),
                zorder=7)

        # ── Save ────────────────────────────────────────────────────────────────
        plt.subplots_adjust(left=0.08, right=0.99, top=0.93, bottom=0.08)
        plt.savefig(out_path, bbox_inches="tight", dpi=300)
        plt.close(fig)
        print(f" -> Saved: {out_path.name}")


    # ══════════════════════════════════════════════════════════════════════════════
    # 5. GENERATE FOUR FIGURES
    # ══════════════════════════════════════════════════════════════════════════════
    print("3. Building four spatial figures...")

    # ── Figure 1: Raw scraping ──────────────────────────────────────────────────
    plot_spatial_step(
        df_scrape, "scrape_step", norm_raw,
        "Raw Step Change After Scraping\n"
        "(Scrape era mean − Pre-scrape mean, Apr 2015 – Dec 2017 vs pre-2015)",
        "Step change in depth (m)",
        OUT_10B_SCRAPE_RAW,
    )

    # ── Figure 2: Raw clearfell ─────────────────────────────────────────────────
    plot_spatial_step(
        df_fell, "fell_step", norm_raw,
        "Raw Step Change After Clearfell\n"
        "(Post-felling mean − Scrape era mean, Dec 2017 onward vs 2015–2017)",
        "Step change in depth (m)",
        OUT_10B_FELL_RAW,
    )

    # ── Figure 3: Climate-corrected scraping ────────────────────────────────────
    plot_spatial_step(
        df_scrape, "scrape_step_cc", norm_cc,
        "Climate-Corrected Step Change: Scraping\n"
        f"(C3W controls median {climate_scrape:+.3f} m subtracted)",
        "Climate-corrected step (m)",
        OUT_10B_SCRAPE_CORRECTED,
    )

    # ── Figure 4: Climate-corrected clearfell ───────────────────────────────────
    plot_spatial_step(
        df_fell, "fell_step_cc", norm_cc,
        "Climate-Corrected Step Change: Clearfell\n"
        f"(C3W controls median {climate_fell:+.3f} m subtracted)",
        "Climate-corrected step (m)",
        OUT_10B_FELL_CORRECTED,
    )


    # ══════════════════════════════════════════════════════════════════════════════
    # 6. EXPORT DATA
    # ══════════════════════════════════════════════════════════════════════════════
    export_df = df[[
        "well", "E", "N", "cluster",
        "scrape_step", "fell_step",
        "scrape_step_cc", "fell_step_cc",
        "n_pre", "n_scrape", "n_post",
    ]].copy()
    export_df.to_csv(OUT_10B_STEP_DATA, index=False, float_format="%.4f")
    print(f" -> Saved step data: {OUT_10B_STEP_DATA.name}")


    # ══════════════════════════════════════════════════════════════════════════════
    # 7. CONSOLE SUMMARY
    # ══════════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("SPATIAL STEP-CHANGE SUMMARY")
    print("=" * 72)

    # Clearfell zone vs quadrants
    cx, cy = 241177, 363645
    df["dist"] = np.sqrt((df["E"] - cx) ** 2 + (df["N"] - cy) ** 2)
    cf = df[df["dist"] < 350].dropna(subset=["fell_step"])
    outer = df[df["dist"] >= 350].dropna(subset=["fell_step"]).copy()
    outer["quad"] = ""
    outer.loc[(outer["E"] < cx)  & (outer["N"] >= cy), "quad"] = "NW"
    outer.loc[(outer["E"] >= cx) & (outer["N"] >= cy), "quad"] = "NE"
    outer.loc[(outer["E"] >= cx) & (outer["N"] <  cy), "quad"] = "SE"
    outer.loc[(outer["E"] < cx)  & (outer["N"] <  cy), "quad"] = "SW"

    print(f"\nClearfell zone (<350 m from centroid): n={len(cf)}")
    print(f"  Raw fell step:  mean={cf['fell_step'].mean():+.4f} m, "
          f"median={cf['fell_step'].median():+.4f} m")
    print(f"  Corrected:      mean={cf['fell_step_cc'].mean():+.4f} m, "
          f"median={cf['fell_step_cc'].median():+.4f} m")

    print(f"\nC3W reference: n={ref_mask.sum()}")
    c12 = df[ref_mask].dropna(subset=["fell_step"])
    print(f"  Raw fell step:  mean={c12['fell_step'].mean():+.4f} m, "
          f"median={c12['fell_step'].median():+.4f} m")

    print(f"\nClearfell vs C3W: {cf['fell_step'].mean() - c12['fell_step'].mean():+.4f} m "
          f"(negative = clearfell wetter)")

    print("\nQuadrant comparison (raw fell step):")
    for q in ["NW", "NE", "SE", "SW"]:
        sub = outer[outer["quad"] == q]
        if len(sub) == 0:
            continue
        diff = cf["fell_step"].mean() - sub["fell_step"].mean()
        print(f"  {q}: n={len(sub):2d}  mean={sub['fell_step'].mean():+.4f} m  "
              f"Clearfell − {q} = {diff:+.4f} m")

    print("\n" + "=" * 72)
    print("Outputs:")
    for p in [OUT_10B_SCRAPE_RAW, OUT_10B_FELL_RAW, OUT_10B_SCRAPE_CORRECTED, OUT_10B_FELL_CORRECTED, OUT_10B_STEP_DATA]:
        print(f"  {p}")
    print("=" * 72)


if __name__ == '__main__':
    main()
