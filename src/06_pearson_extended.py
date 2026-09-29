"""
====================================================================================
PHASE 2: PEARSON MEMBERSHIP AFFINITY AUDIT
====================================================================================
Purpose:
    Bridges the gap between the strict 2026 Reference Network and the 
    shorter-record Extended Network (FE/LIS). Calculates standardised centroids 
    from the Reference model and uses Pearson correlation to classify and map 
    all remaining wells.
====================================================================================
"""
__version__ = "1.5.0"  # Hollingham (2026) - 2026-09-29. T-96 (batch 2): emits
#   n_ref_reclassified_at_delta, one row per threshold in config.PEARSON_DELTA_SENS (Era = the
#   threshold) - the reference wells (best match = assigned cluster) whose Core/Fuzzy tier differs
#   between that threshold and PEARSON_DELTA_THRESH, from the unrounded margins (report8 SS3.3.2,
#   "16 wells at 0.03, 14 at 0.10"). Additive; no existing output changes.
# 1.4.0  Hollingham (2026) - 2026-09-29. T-96: emits the
#   membership-tier counts from audit_df's Status and MCA_Flag columns -
#   n_ref_core, n_ref_fuzzy, n_ref_spy, n_ref_confirmed (core + fuzzy),
#   n_ref_mca_flagged (report9 §4.3, reference network) and n_ext_core,
#   n_ext_fuzzy (report9 §4.3, extended network). The reference-network tiers
#   are the same classification Script 05 writes (identical Class/Status and
#   MCA_Flag at all 66 wells), counted here because Script 05 has no
#   report-numbers file. Additive; no existing output changes.
# 1.3.0  Hollingham (2026) - 2026-09-28. T-91: emits
#   06_report_numbers.csv — LIS1 and FE1's Pearson r against the C4 centroid
#   template (report9 §4.3), read from audit_df already in memory. No
#   existing output changes.
# 1.2.0  Hollingham (2026) - 2026-09-09. DELTA_THRESH and
#   MCA_THRESH now alias config.PEARSON_DELTA_THRESH / PEARSON_MCA_THRESH
#   rather than carrying their own literals. This script already used the >=
#   form the report documents; Script 05 did not, and the two are now one.
#   No behaviour change here.
#   label placement is bounded by ITERATIONS, not the clock (W145): the explicit
#   time_lim=5.0 is REPLACED by iter_lim=config.LABEL_ADJUST_ITER_LIM (not added
#   beside it — adjustText warns when both are set and uses whichever is faster,
#   which puts the clock straight back). Five seconds of wall clock made this
#   figure differ run to run. Placement only; no data, no other output.
# v1.0.0  # Hollingham (2026) — 2026-08-12
#
# This module previously carried no __version__ constant; 1.0.0 marks its
# introduction, not the start of the module's history. Prior revisions are the
# dated notes below and remain the record for anything before this date.
#
# 2026-08-12: well labels — adjust_text() was passing 0.8-era keyword names
#   (expand_text, expand_points, force_points, lim, only_move 'points' key)
#   which adjustText 1.4.0 absorbs into **kwargs silently, with no exception
#   and no warning. The tuning block was therefore inert and the solver ran on
#   defaults. More seriously, no arrowprops was supplied, so displaced labels
#   carried no leader line back to their markers — WMC4, sitting in the
#   NW11/NW1/NW2/NW13 knot, read as belonging to the wrong well. Ported to the
#   1.4.0 parameter names, arrowprops added, min_arrow_len lowered to 3, and
#   the +14 m data-unit pre-offset dropped (adjust_text owns placement).
#   Settings match Script 05 v1.3.1 so the two Pearson maps behave identically.
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap).
# 2026-07-19 (legibility hand pass): 06_pear_01 affinity chart text +1 pt
#   (bump_fig_fonts); 06_pear_02 map well labels 8 -> 8.5 pt; map axis
#   labels gain +1 pt via map_utils v1.6.0 add_en_axes defaults.
# 2026-07-19 (review revisions): 06_pear_01 axis labels and legend +1 pt
#   more (bump_label_and_legend_fonts); 06_pear_02 well-label white
#   background boxes removed.

# Revision note:
#   2026-06-21 — Membership map now calls add_kml_features(..., include_scrapes=False).
#     The shared feature overlay draws the GPS-traced scrape footprints by default;
#     on this dense membership map they overlap the well markers and hinder reading,
#     so they are suppressed here. Figure only; classification unchanged.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    INT_WELLS_REFERENCE,
    INT_WELLS_EXTENDED,
    INT_CLUSTER_STATS,
    INT_LOCATIONS,
    INT_PEAR_AUDIT_SITEWIDE,
    OUT_06_AFFINITY_CHART,
    OUT_06_INTEGRATION_MAP,
    OUT_06_REPORT_NUMBERS,
)
from utils.config import (
    PEARSON_DELTA_THRESH, PEARSON_MCA_THRESH, PEARSON_DELTA_SENS,
    CLUSTER_COLOURS, CLUSTER_COLOURS_BW, CLUSTER_LABELS, BW_MODE,
    LABEL_ADJUST_ITER_LIM,
)
from utils.data_utils import normalize_well_name
from utils.map_utils import load_dem_layer, add_kml_features, add_en_axes
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import contextily as ctx
import fiona
from adjustText import adjust_text
from matplotlib.lines import Line2D

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import bump_fig_fonts, bump_label_and_legend_fonts, render_figure
from utils.report_numbers_utils import ReportNumbers

fiona.drvsupport.supported_drivers["KML"] = "rw"

# ==========================================
# CONFIGURATION & PATHS
# ==========================================

# Inputs from Phase 1
REF_WELLS_PATH = INT_WELLS_REFERENCE
EXT_WELLS_PATH = INT_WELLS_EXTENDED
CLUSTER_PATH = INT_CLUSTER_STATS
LOCATION_PATH = INT_LOCATIONS

# Phase 2 Outputs
OUT_BAR = OUT_06_AFFINITY_CHART
OUT_MAP = OUT_06_INTEGRATION_MAP

EXPECTED_CLUSTERS = sorted(CLUSTER_LABELS.keys())
DELTA_THRESH = PEARSON_DELTA_THRESH   # config.py is the one home (2026-09-09)
MCA_THRESH   = PEARSON_MCA_THRESH

# Aesthetics
plt.rcParams.update({'font.family': 'sans-serif', 'axes.labelsize': 11, 'legend.fontsize': 9})

# DEM colour scale is identical across all PEAR map products because
# map_utils.load_dem_layer() applies config.DEM_VMIN / DEM_VCENTER / DEM_VMAX
# internally. Do not mirror those values here.

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def wells_to_row_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure wells are rows and timestamps are columns."""
    matrix = df.copy()
    matrix = matrix.apply(pd.to_numeric, errors='coerce')
    matrix = matrix.T
    matrix.index = [normalize_well_name(w) for w in matrix.index]
    return matrix

def zscore_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score standardisation by row to extract the pure rhythmic pulse."""
    mean = df.mean(axis=1)
    std = df.std(axis=1, ddof=0)
    return df.sub(mean, axis=0).div(std.replace(0, np.nan), axis=0)

def safe_pearson(a: pd.Series, b: pd.Series) -> float:
    """Calculates Pearson r, ignoring gaps where timestamps don't overlap.

    Requires at least 24 months of shared record — matching the extended network
    minimum — to avoid spurious correlations from very short overlaps.
    """
    pair = pd.concat([a, b], axis=1, sort=False).dropna()
    if len(pair) < 24 or pair.iloc[:, 0].std(ddof=0) == 0 or pair.iloc[:, 1].std(ddof=0) == 0:
        return np.nan
    return pair.iloc[:, 0].corr(pair.iloc[:, 1], method='pearson')


def create_affinity_bar_plot(audit_df: pd.DataFrame) -> None:
    """Create extended-network affinity chart with LCSC-aligned colors and full labels."""
    if audit_df.empty:
        return

    r_cols = [f"r_C{c}" for c in EXPECTED_CLUSTERS if f"r_C{c}" in audit_df.columns]
    if not r_cols:
        return

    preferred = ["ceh1", "nw1", "ceh8", "ceh19", "d15", "ceh17", "lis1", "lis2",
                 "fe1", "fe2", "fe3", "fe4"]
    # Guard against duplicate well ids in audit output to keep plotting vectors aligned.
    audit_idx = audit_df.drop_duplicates(subset=["Well_Normalised"], keep="first").set_index("Well_Normalised")
    available = [w for w in preferred if w in audit_idx.index]

    if len(available) < 3:
        ranked = audit_idx["Delta"].abs().sort_values(ascending=False)
        available = [w for w in ranked.index][:8]

    if not available:
        return

    plot_df = audit_idx.loc[available, r_cols].copy()
    plot_df.columns = [c.replace("r_", "") for c in plot_df.columns]  # r_C1 -> C1

    fig, ax = plt.subplots(figsize=(16, 7), dpi=300)
    x = np.arange(len(available))
    width = 0.12
    n_bars = len(plot_df.columns)

    for i, col in enumerate(plot_df.columns):
        cid = int(col.replace("C", "")) if col.replace("C", "").isdigit() else None
        ax.bar(
            x + (i - (n_bars - 1) / 2) * width,
            plot_df[col].values,
            width=width,
            label=CLUSTER_LABELS.get(cid, col),
            color=CLUSTER_COLOURS.get(cid, "#808080"),
            edgecolor="black",
            linewidth=0.6,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([w.upper() for w in available])
    ax.set_ylabel("Pearson Correlation (r)")
    ax.set_title("Extended Network Membership Affinity by Cluster", fontweight="bold")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    y_max = float(np.nanmax(plot_df.values)) if not plot_df.empty else 1.0
    y_min = min(0.0, float(np.nanmin(plot_df.values)) - 0.02) if not plot_df.empty else 0.0
    ax.set_ylim(y_min, min(1.05, y_max + 0.22))
    ax.legend(title="Cluster", loc="lower right", frameon=True)

    plt.tight_layout()
    bump_fig_fonts(plt.gcf(), 1.0)  # legibility hand pass: all text +1 pt
    bump_label_and_legend_fonts(plt.gcf(), 1.0)  # review: labels+legend +1 more
    render_figure(plt.gcf(), OUT_BAR)
    plt.close(fig)

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    banner("06", "Pearson Affinity — Extended Network", version=__version__)
    make_all_dirs()
    print("--- Starting Phase 2: Pearson Affinity Audit ---")

    # 1. Load Data
    try:
        ref_wells = pd.read_csv(REF_WELLS_PATH, index_col=0, parse_dates=True)
        ext_wells = pd.read_csv(EXT_WELLS_PATH, index_col=0, parse_dates=True)
        ref_clusters = pd.read_csv(CLUSTER_PATH)
        loc_df = pd.read_csv(LOCATION_PATH)
    except FileNotFoundError as e:
        print(f"Error loading Phase 1 files. Ensure LCSC01 and LCSC02 have been run. Details: {e}")
        return

    # Clean inputs
    ref_wells = wells_to_row_matrix(ref_wells)
    ext_wells = wells_to_row_matrix(ext_wells)
    ref_clusters['Match_ID'] = ref_clusters['Match_ID'].apply(normalize_well_name)
    loc_df['Match_ID'] = loc_df['Match_ID'].apply(normalize_well_name)

    well_to_cluster = ref_clusters.set_index('Match_ID')['Cluster'].to_dict()

    # 2. Standardisation & Template Building
    all_wells = pd.concat([ref_wells, ext_wells]).apply(pd.to_numeric, errors='coerce')
    z_all = zscore_rows(all_wells)

    z_ref = z_all.loc[ref_wells.index]
    centroids = {}
    for c in EXPECTED_CLUSTERS:
        members = [w for w, assigned in well_to_cluster.items() if assigned == c and w in z_ref.index]
        centroids[c] = z_ref.loc[members].mean(axis=0, skipna=True) if members else pd.Series(np.nan, index=z_ref.columns)
    
    centroid_df = pd.DataFrame(centroids)

    # 3. Correlation Audit
    step("Running correlation matrix against Reference Templates...")
    audit_rows = []
    _unrounded_corrs = {}  # T-91: full-precision corrs, keyed by well_id — audit_rows rounds to 4dp
    
    for well_id, series in z_all.iterrows():
        is_ref = well_id in ref_wells.index
        assigned_c = well_to_cluster.get(well_id, np.nan)
        
        corrs = {c: safe_pearson(series, centroid_df[c]) for c in EXPECTED_CLUSTERS}
        _unrounded_corrs[well_id] = corrs
        valid_corrs = {k: v for k, v in corrs.items() if pd.notna(v)}
        
        if not valid_corrs:
            continue
            
        sorted_corrs = sorted(valid_corrs.items(), key=lambda x: x[1], reverse=True)
        best_c, best_r = sorted_corrs[0]
        runner_up_c = sorted_corrs[1][0] if len(sorted_corrs) > 1 else np.nan
        runner_up_r = sorted_corrs[1][1] if len(sorted_corrs) > 1 else 0
        delta = best_r - runner_up_r

        # Classification
        if is_ref and pd.notna(assigned_c):
            if best_c != assigned_c: status = "Ref_Spy"
            elif delta < DELTA_THRESH: status = "Ref_Fuzzy"
            else: status = "Ref_Core"
        else:
            status = "Ext_Fuzzy" if delta < DELTA_THRESH else "Ext_Core"

        mca_count = sum(1 for v in valid_corrs.values() if v > MCA_THRESH)

        rec = {
            "Well_Normalised": well_id, "Network": "Reference" if is_ref else "Extended",
            "Original_Cluster": assigned_c, "Best_Match_Cluster": best_c, "Secondary_Cluster": runner_up_c,
            "Best_r": round(best_r, 4), "Delta": round(delta, 4), "Status": status, "MCA_Flag": mca_count >= 3
        }
        rec.update({f"r_C{k}": round(v, 4) for k, v in corrs.items()})
        audit_rows.append(rec)

    audit_columns = [
        'Well_Normalised', 'Network', 'Original_Cluster', 'Best_Match_Cluster',
        'Secondary_Cluster', 'Best_r', 'Delta', 'Status', 'MCA_Flag'
    ] + [f'r_C{k}' for k in EXPECTED_CLUSTERS]
    audit_df = pd.DataFrame(audit_rows, columns=audit_columns)
    audit_df.to_csv(INT_PEAR_AUDIT_SITEWIDE, index=False)
    ext_count = int((audit_df['Network'] == 'Extended').sum()) if 'Network' in audit_df.columns else 0
    step(f"Audit saved. Found {ext_count} Extended wells.")

    # T-91: report9 §4.3 cites the extended-network wells' Pearson affinity
    # against the C4 (Main Forest) centroid template by name (LIS1, FE1).
    # Read from _unrounded_corrs captured during the audit loop above (full
    # precision — audit_df/audit_rows round to 4dp), not by re-reading the CSV
    # just written.
    rpt = ReportNumbers()
    for _w in ("lis1", "fe1"):
        if _w in _unrounded_corrs and 4 in _unrounded_corrs[_w] and pd.notna(_unrounded_corrs[_w][4]):
            rpt.add(f"{_w}_r_C4", float(_unrounded_corrs[_w][4]), unit="",
                    well=_w.upper(),
                    note=f"Pearson r of {_w.upper()} (Extended network) against the "
                         f"C4 (Main Forest) reference-well centroid template, unrounded")
    # T-96: membership-tier counts (report9 §4.3). Reference tiers use the
    # same thresholds as Script 05 (config.PEARSON_DELTA_THRESH /
    # PEARSON_MCA_THRESH) and reproduce its Class and MCA_Flag well for well.
    _ref = audit_df[audit_df["Network"] == "Reference"]
    _ext = audit_df[audit_df["Network"] == "Extended"]
    _n_ref, _n_ext = int(len(_ref)), int(len(_ext))
    for _key, _status, _n, _desc in (
        ("n_ref_core", "Ref_Core", _n_ref, "reference wells classed Core (best match = assigned cluster, "
                                           f"dr >= {DELTA_THRESH:g})"),
        ("n_ref_fuzzy", "Ref_Fuzzy", _n_ref, "reference wells classed Fuzzy (best match = assigned cluster, "
                                             f"dr < {DELTA_THRESH:g})"),
        ("n_ref_spy", "Ref_Spy", _n_ref, "reference wells classed Spy (best match differs from assigned cluster)"),
        ("n_ext_core", "Ext_Core", _n_ext, f"extended wells classed Ext_Core (dr >= {DELTA_THRESH:g})"),
        ("n_ext_fuzzy", "Ext_Fuzzy", _n_ext, f"extended wells classed Ext_Fuzzy (dr < {DELTA_THRESH:g})"),
    ):
        rpt.add(_key, int((audit_df["Status"] == _status).sum()), unit="wells",
                note=f"{_desc}, of n={_n}")
    rpt.add("n_ref_confirmed", int(_ref["Status"].isin(["Ref_Core", "Ref_Fuzzy"]).sum()), unit="wells",
            note=f"reference wells whose best-match cluster is their assigned cluster (Core + Fuzzy), "
                 f"of n={_n_ref}")
    rpt.add("n_ref_mca_flagged", int(_ref["MCA_Flag"].astype(bool).sum()), unit="wells",
            note=f"reference wells with r > {MCA_THRESH:g} to three or more cluster centroids "
                 f"(MCA_Flag), of n={_n_ref}")
    # T-96 (batch 2): the Core/Fuzzy threshold sensitivity (report8 SS3.3.2). A
    # reference well that is not a Spy changes tier at threshold d when its
    # margin falls on different sides of d and of DELTA_THRESH. Margins from
    # the unrounded correlations, not the 4 dp Delta column.
    def _margin(_w):
        _v = sorted((v for v in _unrounded_corrs[_w].values() if pd.notna(v)), reverse=True)
        return _v[0] - _v[1] if len(_v) > 1 else np.nan
    _conf = _ref[_ref["Status"].isin(["Ref_Core", "Ref_Fuzzy"])]
    _margins = pd.Series({_w: _margin(_w) for _w in _conf["Well_Normalised"]}, dtype=float)
    for _d in PEARSON_DELTA_SENS:
        _n_moved = int(((_margins >= _d) != (_margins >= DELTA_THRESH)).sum())
        rpt.add("n_ref_reclassified_at_delta", _n_moved, unit="wells", era=f"{_d:g}",
                note=(f"reference wells (best match = assigned cluster) whose Core/Fuzzy tier changes "
                      f"when the dr threshold moves from {DELTA_THRESH:g} to {_d:g}, of n={len(_margins)}"))
    n_saved = rpt.save(OUT_06_REPORT_NUMBERS)
    step(f"Exported {n_saved} report numbers to {OUT_06_REPORT_NUMBERS.name}")

    create_affinity_bar_plot(audit_df)

    if audit_df.empty:
        fig, ax = plt.subplots(figsize=(10, 6), dpi=200)
        ax.axis('off')
        ax.text(0.5, 0.5, 'No Extended wells available for Pearson integration.', ha='center', va='center', fontsize=14)
        plt.tight_layout()
        render_figure(plt.gcf(), OUT_MAP)
        plt.close(fig)
        print(f"Success: Integration Map saved to {OUT_MAP.name}")
        return

    # 4. Generate Fresh Integration Map
    step("Generating Pearson Integration Map...")
    map_df = audit_df.merge(loc_df[['Match_ID', 'E', 'N']], left_on='Well_Normalised', right_on='Match_ID', how='inner')
    map_df = map_df.dropna(subset=['E', 'N'])

    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)

    # Base Map (DEM + KMLs)
    dem_layer, dem_loaded = load_dem_layer(ax, DATA_DIR)
    if not dem_loaded:
        try:
            ctx.add_basemap(ax, crs="EPSG:27700", source=ctx.providers.OpenStreetMap.Mapnik, zorder=1, alpha=0.7)
        except Exception:
            pass
    add_en_axes(ax)
    if dem_layer is not None and not BW_MODE:
        fig.colorbar(dem_layer, ax=ax, shrink=0.55, pad=0.02, extend="both").set_label("Elevation (m AOD)", rotation=270, labelpad=18)

    site_feature_handles = add_kml_features(ax, DATA_DIR, include_scrapes=False)

    # Plot Wells — cluster identity shown by marker SHAPE, not colour.
    # Fill: reference=dark grey, extended=light grey, spy=white with bold edge.
    from utils.config import CLUSTER_MARKERS
    _clr = CLUSTER_COLOURS_BW if BW_MODE else CLUSTER_COLOURS
    for _, row in map_df.iterrows():
        cid = int(row['Best_Match_Cluster'])
        status = row['Status']
        is_ext = "Ext" in status
        is_spy = "Spy" in status

        marker = CLUSTER_MARKERS.get(cid, "o")
        if is_spy:
            facecolor = "white"
            edgewidth = 2.5
            size = 200
            zorder = 7
        elif is_ext:
            facecolor = "#cccccc"
            edgewidth = 1.0
            size = 120
            zorder = 4
        else:
            facecolor = _clr.get(cid, "grey") if not BW_MODE else "#666666"
            edgewidth = 1.2
            size = 130
            zorder = 5

        ax.scatter(row['E'], row['N'], c=[facecolor], marker=marker, s=size,
                   edgecolor="black", linewidth=edgewidth,
                   alpha=0.9, zorder=zorder)

    # Labels start on their markers; adjust_text() owns placement from there and
    # draws a leader line back to the well wherever a label has been displaced.
    label_x = map_df['E'].to_numpy(dtype=float)
    label_y = map_df['N'].to_numpy(dtype=float)
    texts = [
        ax.text(
            r['E'],
            r['N'],
            r['Well_Normalised'].upper(),
            fontsize=8.5,
            fontweight='bold',
            zorder=10,
        )
        for _, r in map_df.iterrows()
    ]
    adjust_text(
        texts,
        x=label_x,
        y=label_y,
        ax=ax,
        expand=(1.15, 1.35),
        force_text=(0.4, 0.8),
        force_static=(0.3, 0.6),
        min_arrow_len=3,
        iter_lim=LABEL_ADJUST_ITER_LIM,
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.5),
    )

    # Legends
    ax.set_title("Pearson Integration Map: Reference vs. Extended Networks", fontsize=15, fontweight='bold')

    handles_status = [
        Line2D([0], [0], marker='o', color='w', label='Reference well (dark fill)',
               markerfacecolor='#666666', markeredgecolor='black', markersize=9),
        Line2D([0], [0], marker='o', color='w', label='Extended well (light fill)',
               markerfacecolor='#cccccc', markeredgecolor='black', markersize=9),
        Line2D([0], [0], marker='o', color='w', label='Behavioural Spy (bold edge)',
               markerfacecolor='white', markeredgecolor='black', markersize=9, markeredgewidth=2.5),
    ]
    ax.add_artist(ax.legend(handles=handles_status, loc='upper left', title="Network Classification", frameon=True))
    
    from utils.config import CLUSTER_MARKERS
    handles_clusters = [
        Line2D([0], [0], marker=CLUSTER_MARKERS.get(c, 'o'), color='w',
               label=CLUSTER_LABELS.get(c, f"C{c}"),
               markerfacecolor='grey', markeredgecolor='black', markersize=10)
        for c in EXPECTED_CLUSTERS
    ]
    cluster_legend = ax.legend(handles=handles_clusters, loc='lower left', title="Calculated Cluster Affinity", frameon=True)
    ax.add_artist(cluster_legend)

    if site_feature_handles:
        dedup = {}
        for handle in site_feature_handles:
            dedup[handle.get_label()] = handle
        ax.legend(handles=list(dedup.values()), loc='upper right', title="Site Features", frameon=True)

    plt.tight_layout()
    render_figure(plt.gcf(), OUT_MAP)
    print(f"Success: Integration Map saved to {OUT_MAP.name}")

if __name__ == "__main__":
    main()