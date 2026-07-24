"""
18_wtf_spatial.py
=================
Water Table Fluctuation (WTF) Method — Individual Well Analysis and Spatial Mapping
Newborough Warren Coastal Sand Dune Aquifer, 2005–2026

Outputs:
    18_wtf_01_well_sy_estimates.csv      — reference well Sy table (Table S1)
    18_wtf_02_spatial_sy_map.png         — point map (plot_metric_map, as script 04)
    18_wtf_03_sy_contour.png             — IDW contour surface, reference wells only
    18_wtf_04_sy_contour_extended.png    — IDW contour surface, reference + extended wells
    18_wtf_05_drainage_timescale_map.png — IDW contour of τ = Sy / β₃ (months)
    18_wtf_05_drainage_timescale.csv     — per-well τ values with Sy, β₃, cluster
    18_wtf_06_aquifer_diagnostic_synthesis.png — τ vs ΔNSE scatter sized by Sy

Notes:
    - Forest clusters (C4 Main Forest, C5 Coastal Forest) receive interception
      correction: R_eff = (1-0.24)*P - PET. Interception fraction measured at
      C5 and applied across both forested clusters.
    - Under the k=5 partition all clusters are analytically usable; the old
      EXCLUDE_CLUSTERS list (tidal / lake) is empty.
    - Extended wells use Best_Match_Cluster from 06_pear_membership_audit_sitewide.csv
    - Extended wells shown as open symbols on extended contour map
    - Forest contour values carry additional uncertainty (Freeman, 2008)

References:
    Healy, R.W. and Cook, P.G. (2002) Hydrogeology Journal 10, 91-109.
    Freeman, S. (2008) Hydrological impact of Corsican pine at Newborough Warren.
"""

__version__ = "1.7.0"  # Hollingham (2026) — 2026-07-24
# 1.7.0 (2026-07-24): Emit the drainage decay half-life to the committed CSV.
#         build_tau_table() now writes a `half_life_months` column
#         (t½ = ln(2)/β₃) alongside the existing `tau_months`. Closes a
#         traceability gap: Paper 1 Table 7 and Figures 14/15 report t½, but the
#         cited source file 18_wtf_05_drainage_timescale.csv carried only
#         `tau_months` (the storage–drainage index τ = Sy/β₃) — a different
#         quantity that the manuscripts deliberately do not report. t½ was
#         computed at render time in rb3_df but never committed, so a reader
#         following the provenance chain could not read it. Same exclusion mask
#         as τ (ridge/bedrock, negative β₃, near-zero β₃). Existing columns and
#         their order are unchanged apart from the insertion; no downstream
#         script consumes this CSV. Console cluster summary now also prints the
#         per-cluster t½ median and range, directly checkable against Table 7.
#         The `drainage_timescale` filename stem is historical and retained
#         deliberately — do not rename.
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
# 1.5.0 (2026-07-01): map_utils refactor.
#         make_site_mask() removed from this script — moved to map_utils v1.4.0
#         (single shared implementation). SEA_SOUTH_N/SEA_EAST_E/SEA_WEST_E
#         module constants removed (now _SEA_* in map_utils). All four IDW
#         contour-map functions (plot_contour_map, plot_contour_map_extended,
#         plot_halflife_map, plot_drainage_timescale_map) refactored to route
#         through add_idw_surface() + make_site_mask from map_utils, replacing
#         four identical inline power-2 IDW implementations and four local grid
#         definitions. Interpolation method changes from power-2 IDW to linear
#         griddata (map_utils standard); surface rendered as pcolormesh with
#         contour lines overlaid. plot_drainage_timescale_map() removed — dead
#         code since v1.4.0 (τ CSV still written; only the figure is gone).
#         Hardcoded "2005–2026" year strings in all map titles replaced with
#         dynamic end_year from REFERENCE_CUTOFF_DATE. REFERENCE_CUTOFF_DATE
#         added to config import. add_idw_surface and make_site_mask added to
#         map_utils import.
# 1.4.0 (2026-06-29): Replace τ map with drainage decay half-life map
#         (t½ = ln(2)/β₃). Fig 46 now shows t½ (single panel). Fig 48
#         synthesis scatter y-axis changed from τ to t½. τ = Sy/β₃ retained
#         as intermediate CSV only (discussion reference). New function:
#         plot_halflife_map(). Synthesis scatter refactored to accept rb3_df
#         directly; Sy loaded from OUT_18_WELL_SY_TABLE. paths.py: renamed
#         OUT_18_HALFLIFE_MAP (18_wtf_05_halflife_map.png); removed
#         OUT_18_DRAINAGE_TIMESCALE map path (CSV path retained).
#         18_report_numbers.csv gains t½ mean/min/max per cluster.
#         (18_wtf_05_drainage_timescale_map.png): "Drainage timescale" →
#         "Storage–drainage index" — missed instance from the v1.1.0
#         terminology sweep. Map title and scatter y-axis were already
#         correct; colourbar was the sole outstanding inconsistency.
# 1.2.0 (2026-06-21): §4.9 traceability — emit 18_report_numbers.csv with the
#         cited τ wells (CEH13/CEH14) and per-cluster reference-network τ
#         ranges (Fig 44). No change to the τ CSV or maps.
# 1.1.1 — data/geo/ reorg: site-boundary/streams via DATA_KML_SITE_BOUNDARY,
#         DATA_KML_STREAMS (data/geo/). No functional change.
# 1.1.0 — Terminology update: "drainage timescale" → "storage–drainage index"
#         in all rendered figure text:
#         * 18_wtf_05_drainage_timescale_map.png title updated to
#           "Characteristic Storage–Drainage Index τ = Sy / β₃";
#           subtitle note added: "τ is not a residence time (t_R = 1/β₃)".
#         * 18_wtf_06_aquifer_diagnostic_synthesis.png y-axis label and
#           subtitle updated accordingly.
#         Function names, CSV column names, and output filenames unchanged
#         to avoid breaking downstream pipeline dependencies.
# 1.0.1 — Doc-sweep S.12: updated stale "C4 Forest values corrected" plot
#         title to "Forest cluster values (C4, C5) corrected" (S12-A,
#         matches live code and Script 18 docstring line 17 — interception
#         correction applies to both forest clusters under the k=5
#         partition); added __version__ constant (S12-B).  Patch — no
#         functional change.
# 1.0.x — Initial.

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

import pandas as pd
import numpy as np
import matplotlib

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils.paths import (
    make_all_dirs, OUT_DIR, DIR_18, INT_WELLS_CLEAN, INT_CLIMATE,
    INT_LOCATIONS, INT_CLUSTER_STATS, INT_MASTER_DATA, INT_WELLS_EXTENDED,
    INT_PEAR_AUDIT_SITEWIDE, DATA_DIR, DATA_KML_SITE_BOUNDARY, DATA_KML_STREAMS,
    INT_LCSC_MODEL_STATS,
    OUT_18_WELL_SY_TABLE, OUT_18_SY_MAP, OUT_18_SY_CONTOUR,
    OUT_18_SY_CONTOUR_EXT, INT_WTF_WELL_SY, OUT_18_HALFLIFE_MAP,
    OUT_18_DRAINAGE_TIMESCALE_CSV,
    OUT_18_AQUIFER_SYNTHESIS, OUT_18_REPORT_NUMBERS,
)
from utils.report_numbers_utils import ReportNumbers
from utils.config import (
    CLUSTER_LABELS, CLUSTER_COLOURS, CLUSTER_MARKERS,
    FOREST_INTERCEPTION, FOREST_CIDS,
    BW_MODE, get_cmap, REFERENCE_CUTOFF_DATE,
)
from utils.render_utils import render_figure
make_all_dirs()

# ── Dynamic end year for map titles ───────────────────────────────────────────
_END_YEAR = pd.Timestamp(REFERENCE_CUTOFF_DATE).year


# Wells excluded from contour interpolation — physically outside sand aquifer
# CEH12 sits on the bedrock ridge in a forested area; its WTF Sy reflects
# fractured rock response rather than dune sand storage and must not be
# interpolated onto the sand aquifer Sy surface.
# Wells excluded from contour interpolation — physically anomalous settings
# CEH12: sits on the bedrock ridge in a forested area; WTF Sy reflects
#         fractured rock response rather than dune sand storage.
# CEH15: forest well located in a low-lying slack within the plantation;
#         slack topography dominates water table dynamics, WTF underestimates
#         Sy relative to upland forest sand. Interception correction also
#         unreliable for a partially-open slack canopy setting.
RIDGE_EXCLUDE = ['ceh12', 'ceh15']
# Additional exclusion for τ = Sy / β₃ map only:
# CEH13: extremely low β₃ (0.002) gives τ ≈ 124 months — a >10× outlier
#         that dominates the colourbar and masks meaningful spatial variation
#         in the 2–15 month range. The near-zero β₃ likely reflects minimal
#         hydraulic gradient rather than genuine aquifer sluggishness.
TAU_EXCLUDE = ['ceh13']
# FOREST_INTERCEPTION and FOREST_CIDS imported from config.py.
EXCLUDE_CLUSTERS    = []         # under k=5 all clusters are analytically usable
MIN_RISE_M          = 0.005      # m
MIN_NET_RECH        = 0.010      # m
MIN_EVENTS          = 15         # minimum qualifying events for confidence flag

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'axes.labelsize': 11, 'axes.titlesize': 11,
    'xtick.labelsize': 9,  'ytick.labelsize': 9,
})


def load_well_data(out_root):
    """Load individual well time series, climate, locations and cluster assignments."""
    wells_df   = pd.read_csv(INT_WELLS_CLEAN,
                              index_col=0, parse_dates=True)
    climate    = pd.read_csv(INT_CLIMATE, parse_dates=["Date"])
    cluster_df = pd.read_csv(INT_CLUSTER_STATS)
    locations  = pd.read_csv(INT_LOCATIONS)

    climate    = climate.set_index("Date")
    wells_df.index = pd.to_datetime(wells_df.index)

    cluster_df["norm"] = cluster_df["Match_ID"].str.lower().str.strip()
    locations["norm"]  = locations["Match_ID"].str.lower().str.strip()

    return wells_df, climate, cluster_df, locations


def wtf_individual_wells(wells_df, climate, cluster_df, locations):
    """
    Event-based WTF Sy for every individual reference well.
    Returns DataFrame sorted by cluster then well name.
    """
    rows = []

    for well in wells_df.columns:
        well_norm = well.lower().strip().replace(" ", "")

        # Cluster lookup
        match = cluster_df[cluster_df["norm"].str.replace(" ","") == well_norm]
        if match.empty:
            continue
        cluster = int(match["Cluster"].iloc[0])
        if cluster in EXCLUDE_CLUSTERS:
            continue

        # Align with climate
        merged = wells_df[[well]].join(climate[["P_m","PET"]], how="inner").dropna()
        if len(merged) < 24:
            continue

        merged = merged.sort_index()
        merged["dh"] = merged[well].diff()

        # Interception correction for Forest clusters
        if cluster in FOREST_CIDS:
            merged["net_R"] = merged["P_m"] * (1 - FOREST_INTERCEPTION) - merged["PET"]
            corrected = True
        else:
            merged["net_R"] = merged["P_m"] - merged["PET"]
            corrected = False

        # Event selection
        events = merged[
            (merged["net_R"] > MIN_NET_RECH) &
            (merged["dh"]    > MIN_RISE_M)
        ].copy()
        events["sy_i"] = events["net_R"] / events["dh"]
        events = events[(events["sy_i"] > 0.01) & (events["sy_i"] < 0.50)]

        n = len(events)
        if n < 5:
            continue

        # Location lookup
        loc = locations[locations["norm"].str.replace(" ","") == well_norm]
        if loc.empty:
            continue

        rows.append({
            "Well":      well,
            "Cluster":   cluster,
            "Easting":   float(loc["E"].iloc[0]),
            "Northing":  float(loc["N"].iloc[0]),
            "Sy_median": round(events["sy_i"].median(), 4),
            "Sy_Q25":    round(events["sy_i"].quantile(0.25), 4),
            "Sy_Q75":    round(events["sy_i"].quantile(0.75), 4),
            "n_events":  n,
            "Corrected": corrected,
            "Confidence": "High" if n >= MIN_EVENTS else "Low",
        })

    df = pd.DataFrame(rows).sort_values(["Cluster","Well"]).reset_index(drop=True)
    print(f"  {len(df)} wells processed  "
          f"({len(df[df['Confidence']=='High'])} high confidence)")
    return df


def plot_spatial_map(well_results, out_path):
    """
    Point map of well-level WTF Sy using plot_metric_map from map_utils.
    Identical infrastructure to script 04 — DEM/OSM base, KML overlays,
    cluster markers.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

    data_dir = DATA_DIR

    try:
        from utils.map_utils import plot_metric_map
    except ImportError:
        warn("map_utils not available — skipping point map")
        return

    map_df = well_results.rename(columns={
        "Cluster": "Cluster_ID",
        "Sy_median": "WTF_Sy_median",
    })[["Easting","Northing","Cluster_ID","WTF_Sy_median"]].copy()

    plot_metric_map(
        map_df      = map_df,
        value_col   = "WTF_Sy_median",
        title       = (f"WTF Specific Yield (event median) — Newborough Warren 2005–{_END_YEAR}\n"
                       "Forest cluster values (C4, C5) corrected for 24% canopy interception "
                       "(Freeman, 2008); spatial canopy variability means "
                       "Forest estimates are approximate"),
        output_path = out_path,
        cmap        = get_cmap("RdYlGn"),
        data_dir    = data_dir,
        vmin        = 0.10,
        vmax        = 0.40,
    )
    print(f"  Point map saved → {out_path.name}")


def plot_contour_map(well_results, out_path):
    """
    IDW-interpolated contour surface of WTF Sy across the site.
    Greyscale hillshade DEM background (load_dem_hillshade) with semi-transparent
    Sy pcolormesh surface overlaid. Interpolation (linear griddata via
    add_idw_surface) clipped to the NNR site boundary via make_site_mask.
    Forest cluster wells hatched to signal interception uncertainty.
    """
    from matplotlib.lines import Line2D
    from utils.map_utils import (
        load_dem_hillshade, add_kml_features, add_en_axes, add_idw_surface,
    )

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white", dpi=200)
    add_en_axes(ax)

    # Layer 1 — greyscale hillshade DEM
    _, dem_loaded, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=0.35, vert_exag=3.0, zorder=1)
    if not dem_loaded:
        warn("DEM hillshade unavailable — plain background used")
        ax.set_facecolor("#EEF2F6")

    # Layer 2 — semi-transparent Sy surface (pcolormesh + contour lines)
    mesh, gx, gy, surf_masked = add_idw_surface(
        ax, well_results, "Sy_median",
        easting_col="Easting", northing_col="Northing",
        cmap=get_cmap("RdYlGn"), vmin=0.10, vmax=0.40,
        alpha=0.65, zorder=2, apply_site_mask=True,
    )
    cl = ax.contour(gx, gy, surf_masked, levels=10,
                    colors="black" if BW_MODE else "white",
                    linewidths=0.6, alpha=0.6, zorder=3)
    ax.clabel(cl, fmt="%.2f", fontsize=7,
              colors="black" if BW_MODE else "white")

    # Layer 3 — KML site features
    site_feature_handles = []
    try:
        site_feature_handles = add_kml_features(ax, DATA_DIR)
        print(f"  KML features added ({len(site_feature_handles)} layers)")
    except Exception as e:
        warn(f"KML features failed: {e}")

    # Colourbar
    cbar = fig.colorbar(mesh, ax=ax, fraction=0.025, pad=0.01, shrink=0.75)
    cbar.set_label("Specific yield Sy  (WTF event median, linear interpolation)",
                   fontsize=10, labelpad=10)

    cluster_handles = []
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = well_results[well_results["Cluster"] == cid]
        if sub.empty:
            continue
        sizes = 60 + (sub["n_events"] - 20) * 1.2
        hatch = "//" if cid in FOREST_CIDS else None
        ax.scatter(sub["Easting"], sub["Northing"],
                   c=CLUSTER_COLOURS[cid],
                   s=sizes, marker=CLUSTER_MARKERS[cid],
                   edgecolors="black", linewidths=0.8,
                   alpha=0.92, zorder=5, hatch=hatch)
        cluster_handles.append(Line2D(
            [0],[0], marker=CLUSTER_MARKERS[cid], color="w",
            markerfacecolor=CLUSTER_COLOURS[cid],
            markeredgecolor="black", markersize=10,
            label=CLUSTER_LABELS[cid]))

    # Sy value labels
    for _, row in well_results.iterrows():
        ax.annotate(f"{row['Sy_median']:.2f}",
                    (row["Easting"], row["Northing"]),
                    xytext=(4, 4), textcoords="offset points",
                    fontsize=6, color="#111111", zorder=6)

    # Legends
    cluster_leg = ax.legend(
        handles=cluster_handles, loc="lower left",
        title="Cluster  (// = interception correction applied)",
        fontsize=8, framealpha=0.95, edgecolor="#CCCCCC")
    ax.add_artist(cluster_leg)
    if site_feature_handles:
        ax.legend(handles=site_feature_handles, title="Site Features",
                  loc="upper left", fontsize=8,
                  framealpha=0.95, edgecolor="#CCCCCC")

    ax.set_title(
        f"Interpolated WTF Specific Yield Surface — Newborough Warren 2005–{_END_YEAR}\n"
        "Linear griddata interpolation of event-based median Sy per well  |  "
        "Greyscale hillshade DEM + KML overlays\n"
        "Forest cluster values (C4, C5) interception-corrected (Freeman, 2008) — "
        "interpolation in Forest zone is approximate",
        fontsize=9, fontweight="bold", pad=10)

    ax.tick_params(labelsize=8)
    plt.tight_layout()
    render_figure(fig, out_path, facecolor="white")
    plt.close()
    print(f"  Contour map saved → {out_path.name}")


def wtf_extended_wells(climate, locations, out_root):
    """
    Apply event-based WTF Sy to the 20 extended network wells.
    Cluster assignments from 06_pear_membership_audit_sitewide.csv
    (Best_Match_Cluster column). Interception correction applied to C4 wells.
    Returns DataFrame in same format as wtf_individual_wells(), with
    Network='Extended' column added.
    """
    try:
        wells_ext  = pd.read_csv(INT_WELLS_EXTENDED,
                                  index_col=0, parse_dates=True)
        membership = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE)
    except Exception as e:
        warn(f"Could not load extended well data: {e}")
        return None

    wells_ext.index = pd.to_datetime(wells_ext.index)
    membership['norm'] = (membership['Well_Normalised']
                          .str.lower().str.strip().str.replace(' ',''))
    locations_copy = locations.copy()
    locations_copy['norm'] = (locations_copy['Match_ID']
                               .str.lower().str.strip().str.replace(' ',''))

    # Keep only extended wells
    ext_only = membership[membership['Network'] == 'Extended'].copy()

    rows = []
    for well in wells_ext.columns:
        well_norm = well.lower().strip().replace(' ','')

        # Cluster from sitewide membership audit
        match = ext_only[ext_only['norm'] == well_norm]
        if match.empty:
            continue
        cluster = int(match['Best_Match_Cluster'].iloc[0])
        if cluster in EXCLUDE_CLUSTERS:
            continue

        # Align with climate
        merged = wells_ext[[well]].join(
            climate[['P_m','PET']], how='inner').dropna()
        if len(merged) < 24:
            continue

        merged = merged.sort_index()
        merged['dh'] = merged[well].diff()

        if cluster in FOREST_CIDS:
            merged['net_R'] = merged['P_m'] * (1 - FOREST_INTERCEPTION) - merged['PET']
            corrected = True
        else:
            merged['net_R'] = merged['P_m'] - merged['PET']
            corrected = False

        events = merged[
            (merged['net_R'] > MIN_NET_RECH) &
            (merged['dh']    > MIN_RISE_M)
        ].copy()
        events['sy_i'] = events['net_R'] / events['dh']
        events = events[(events['sy_i'] > 0.01) & (events['sy_i'] < 0.50)]

        n = len(events)
        if n < 5:
            continue

        loc = locations_copy[locations_copy['norm'] == well_norm]
        if loc.empty:
            continue

        rows.append({
            'Well':       well,
            'Cluster':    cluster,
            'Network':    'Extended',
            'Easting':    float(loc['E'].iloc[0]),
            'Northing':   float(loc['N'].iloc[0]),
            'Sy_median':  round(events['sy_i'].median(), 4),
            'Sy_Q25':     round(events['sy_i'].quantile(0.25), 4),
            'Sy_Q75':     round(events['sy_i'].quantile(0.75), 4),
            'n_events':   n,
            'Corrected':  corrected,
            'Confidence': 'High' if n >= MIN_EVENTS else 'Low',
            'Ridge_Flag': well_norm in RIDGE_EXCLUDE,
        })

    if not rows:
        warn("No extended well results produced")
        return None

    df = pd.DataFrame(rows).sort_values(['Cluster','Well']).reset_index(drop=True)
    print(f"  {len(df)} extended wells processed  "
          f"({len(df[df['Confidence']=='High'])} high confidence)")
    return df


def plot_contour_map_extended(ref_results, ext_results, out_path):
    """
    Linear griddata surface using reference + extended wells combined.
    Greyscale hillshade DEM background; interpolation clipped to NNR site
    boundary via make_site_mask (add_idw_surface apply_site_mask=True).
    Extended wells shown as open symbols to distinguish from reference wells.
    """
    from matplotlib.lines import Line2D
    from utils.map_utils import (
        load_dem_hillshade, add_kml_features, add_en_axes, add_idw_surface,
    )

    # Add Network/Ridge_Flag columns to ref_results if missing
    ref = ref_results.copy()
    if 'Network' not in ref.columns:
        ref['Network'] = 'Reference'
    if 'Ridge_Flag' not in ref.columns:
        ref['Ridge_Flag'] = False

    ext = ext_results.copy()
    if 'Ridge_Flag' not in ext.columns:
        ext['Ridge_Flag'] = False

    ext_interp = ext[~ext['Ridge_Flag']].copy()
    ext_ridge  = ext[ext['Ridge_Flag']].copy()

    combined = pd.concat([ref, ext_interp], ignore_index=True)

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 10), facecolor='white', dpi=200)
    add_en_axes(ax)

    # Layer 1 — greyscale hillshade DEM
    _, dem_loaded, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=0.35, vert_exag=3.0, zorder=1)
    if not dem_loaded:
        warn("DEM hillshade unavailable — plain background used")
        ax.set_facecolor('#EEF2F6')

    # Layer 2 — semi-transparent Sy surface (pcolormesh + contour lines)
    mesh, gx, gy, surf_masked = add_idw_surface(
        ax, combined, 'Sy_median',
        easting_col='Easting', northing_col='Northing',
        cmap=get_cmap('RdYlGn'), vmin=0.10, vmax=0.40,
        alpha=0.65, zorder=2, apply_site_mask=True,
    )
    cl = ax.contour(gx, gy, surf_masked, levels=10,
                    colors='white', linewidths=0.6, alpha=0.6, zorder=3)
    ax.clabel(cl, fmt='%.2f', fontsize=7, colors='white')

    # Layer 3 — KML site features
    site_feature_handles = []
    try:
        site_feature_handles = add_kml_features(ax, DATA_DIR)
        print(f"  KML features added ({len(site_feature_handles)} layers)")
    except Exception as e:
        warn(f"KML features failed: {e}")

    cbar = fig.colorbar(mesh, ax=ax, fraction=0.025, pad=0.01, shrink=0.75)
    cbar.set_label('Specific yield Sy  (WTF event median, linear interpolation)',
                   fontsize=10, labelpad=10)

    cluster_handles = []

    # Reference wells — filled
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = ref[ref['Cluster'] == cid]
        if sub.empty:
            continue
        sizes = 60 + (sub['n_events'] - 20) * 1.2
        hatch = '//' if cid in FOREST_CIDS else None
        ax.scatter(sub['Easting'], sub['Northing'],
                   c=CLUSTER_COLOURS[cid], s=sizes,
                   marker=CLUSTER_MARKERS[cid],
                   edgecolors='black', linewidths=0.8,
                   alpha=0.92, zorder=5, hatch=hatch)
        for _, row in sub.iterrows():
            ax.annotate(f"{row['Sy_median']:.2f}",
                        (row['Easting'], row['Northing']),
                        xytext=(4,4), textcoords='offset points',
                        fontsize=6, color='#111111', zorder=6)
        cluster_handles.append(Line2D(
            [0],[0], marker=CLUSTER_MARKERS[cid], color='w',
            markerfacecolor=CLUSTER_COLOURS[cid],
            markeredgecolor='black', markersize=10,
            label=CLUSTER_LABELS[cid]))

    # Extended wells — open symbols (non-ridge only)
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = ext_interp[ext_interp['Cluster'] == cid]
        if sub.empty:
            continue
        lc = sub['Confidence'].map({'High': 1.8, 'Low': 1.2})
        ax.scatter(sub['Easting'], sub['Northing'],
                   facecolors='none',
                   edgecolors=CLUSTER_COLOURS[cid],
                   s=110, marker=CLUSTER_MARKERS[cid],
                   linewidths=lc, alpha=0.90, zorder=5)
        for _, row in sub.iterrows():
            ax.annotate(f"{row['Sy_median']:.2f}",
                        (row['Easting'], row['Northing']),
                        xytext=(4,4), textcoords='offset points',
                        fontsize=6, color='#555555',
                        style='italic', zorder=6)

    ext_handles = [
        Line2D([0],[0], marker='o', color='w',
               markerfacecolor='none', markeredgecolor='#555555',
               markeredgewidth=1.8, markersize=10,
               label='Extended wells (open = high conf., thin = low conf.)'),
    ]

    # Ridge wells — shown as flagged crosses, excluded from interpolation
    if not ext_ridge.empty:
        ax.scatter(ext_ridge['Easting'], ext_ridge['Northing'],
                   marker='x', c='red', s=120,
                   linewidths=2.0, zorder=7)
        reasons = {
            'ceh12': 'ridge/bedrock',
            'ceh15': 'forest slack floor',
        }
        for _, row in ext_ridge.iterrows():
            reason = reasons.get(row['Well'].lower().strip(), 'excluded')
            ax.annotate(f"{row['Well'].upper()}\n{row['Sy_median']:.2f} ({reason})",
                        (row['Easting'], row['Northing']),
                        xytext=(6, 6), textcoords='offset points',
                        fontsize=6, color='red', style='italic', zorder=8)
        ext_handles.append(
            Line2D([0],[0], marker='x', color='red', markersize=9,
                   linewidth=2, linestyle='none',
                   label='Excluded from interpolation\n(ridge/bedrock or slack-floor setting)'))

    cluster_leg = ax.legend(
        handles=cluster_handles + ext_handles,
        loc='lower left',
        title='Cluster  (// = interception correction applied)',
        fontsize=8, framealpha=0.95, edgecolor='#CCCCCC')
    ax.add_artist(cluster_leg)

    if site_feature_handles:
        ax.legend(handles=site_feature_handles, title='Site Features',
                  loc='upper left', fontsize=8,
                  framealpha=0.95, edgecolor='#CCCCCC')

    ax.set_title(
        f'Interpolated WTF Specific Yield Surface — Reference + Extended Network\n'
        f'Newborough Warren 2005–{_END_YEAR}  |  Linear griddata interpolation  |  '
        'Greyscale hillshade DEM + KML overlays\n'
        'Filled markers = reference wells; open markers = extended wells  |  '
        'Forest clusters (C4, C5) interception-corrected (Freeman, 2008)',
        fontsize=9, fontweight='bold', pad=10)

    ax.tick_params(labelsize=8)
    plt.tight_layout()
    render_figure(fig, out_path, facecolor='white')
    plt.close()
    print(f"  Extended contour map saved → {out_path.name}")


def compute_drainage_timescale(well_results):
    """
    Compute per-well characteristic drainage timescale τ = Sy / β₃ (months).

    Joins WTF-derived Sy (from well_results) with SSM β₃ (from 03_master_data.csv).
    Excludes:
      - CEH12 (bedrock ridge — Sy not representative of sand aquifer)
      - CEH15 (forest slack floor — anomalous Sy)
      - CEH14 (negative β₃ — τ undefined)
      - CEH13 (near-zero β₃ — τ ≈ 124 months, >10× outlier distorting colourbar)
      - Any well where β₃ ≤ 0

    Returns
    -------
    tau_df : pd.DataFrame
        Columns: Well, Cluster, Easting, Northing, Sy_median, beta_3, tau_months,
                 half_life_months, n_events, Corrected, Confidence, Excluded,
                 Exclude_Reason
    """
    # Load β₃ from master data
    master = pd.read_csv(INT_MASTER_DATA)
    master["well_norm"] = master["Name_Original"].str.lower().str.strip()

    # Build normalised key on well_results
    wr = well_results.copy()
    wr["well_norm"] = wr["Well"].str.lower().str.strip()

    # Merge on normalised well name
    merged = wr.merge(
        master[["well_norm", "beta_3_drainage"]],
        on="well_norm", how="inner"
    )

    # Flag exclusions
    merged["Excluded"] = False
    merged["Exclude_Reason"] = ""

    ridge_norms = [w.lower().strip() for w in RIDGE_EXCLUDE]
    ridge_mask = merged["well_norm"].isin(ridge_norms)
    merged.loc[ridge_mask, "Excluded"] = True
    merged.loc[ridge_mask, "Exclude_Reason"] = "ridge/bedrock or slack-floor setting"

    neg_b3 = merged["beta_3_drainage"] <= 0
    merged.loc[neg_b3 & ~merged["Excluded"], "Excluded"] = True
    merged.loc[neg_b3 & ~ridge_mask, "Exclude_Reason"] = "negative β₃"

    tau_norms = [w.lower().strip() for w in TAU_EXCLUDE]
    tau_mask = merged["well_norm"].isin(tau_norms) & ~merged["Excluded"]
    merged.loc[tau_mask, "Excluded"] = True
    merged.loc[tau_mask, "Exclude_Reason"] = "near-zero β₃ (τ outlier)"

    # Compute τ and t½ for non-excluded wells.
    # τ = Sy/β₃ is the storage–drainage index: a storage-weighted composite
    # diagnostic, NOT a residence time. t½ = ln(2)/β₃ is the drainage decay
    # half-life — Sy CANCELS, so it is specific-yield-independent, and it is the
    # quantity reported in the manuscripts (Paper 1 Table 7, Figures 14 and 15).
    # Both are emitted so the committed CSV is self-describing; previously t½ was
    # computed only at render time and could not be read from this file.
    merged["tau_months"] = np.nan
    merged["half_life_months"] = np.nan
    valid = ~merged["Excluded"]
    merged.loc[valid, "tau_months"] = (
        merged.loc[valid, "Sy_median"] / merged.loc[valid, "beta_3_drainage"]
    )
    merged.loc[valid, "half_life_months"] = (
        np.log(2) / merged.loc[valid, "beta_3_drainage"]
    )

    # Tidy up output columns
    tau_df = merged[[
        "Well", "Cluster", "Easting", "Northing",
        "Sy_median", "beta_3_drainage", "tau_months", "half_life_months",
        "n_events", "Corrected", "Confidence",
        "Excluded", "Exclude_Reason",
    ]].copy()
    tau_df = tau_df.rename(columns={"beta_3_drainage": "beta_3"})
    tau_df = tau_df.sort_values(["Cluster", "Well"]).reset_index(drop=True)

    n_valid = valid.sum()
    n_excluded = merged["Excluded"].sum()
    excluded_wells = merged.loc[merged["Excluded"], "Well"].tolist()
    print(f"  τ and t½ computed for {n_valid} wells; {n_excluded} excluded "
          f"({', '.join(w.upper() for w in excluded_wells)})")

    # Cluster summary
    for cid in sorted(tau_df.loc[~tau_df["Excluded"], "Cluster"].unique()):
        sub = tau_df[(tau_df["Cluster"] == cid) & (~tau_df["Excluded"])]
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        print(f"    {label}: τ = {sub['tau_months'].mean():.1f} months "
              f"(range {sub['tau_months'].min():.1f}–{sub['tau_months'].max():.1f}, "
              f"n={len(sub)})")
        print(f"      t½ = {sub['half_life_months'].median():.1f} months "
              f"(range {sub['half_life_months'].min():.1f}–"
              f"{sub['half_life_months'].max():.1f})")

    return tau_df


def compute_recip_beta3():
    """
    Compute per-well recession e-folding time t_R = 1 / β₃ (months).

    Loads β₃, Easting, Northing, and Cluster directly from 03_master_data.csv.
    Excludes:
      - CEH14 (negative β₃ — 1/β₃ undefined)
      - CEH13 (near-zero β₃ — 1/β₃ ≈ 526 months, extreme outlier)
      - Any well where β₃ ≤ 0

    Returns
    -------
    rb3_df : pd.DataFrame
        Columns: Well, Cluster, Easting, Northing, beta_3, recip_beta3_months,
                 Excluded, Exclude_Reason
    """
    master = pd.read_csv(INT_MASTER_DATA)
    master["well_norm"] = master["Name_Original"].str.lower().str.strip()

    rb3_df = master[[
        "Name_Original", "Cluster", "Easting", "Northing", "beta_3_drainage", "well_norm"
    ]].copy()
    rb3_df = rb3_df.rename(columns={"Name_Original": "Well", "beta_3_drainage": "beta_3"})

    rb3_df["Excluded"] = False
    rb3_df["Exclude_Reason"] = ""

    # Negative / zero β₃
    neg_mask = rb3_df["beta_3"] <= 0
    rb3_df.loc[neg_mask, "Excluded"] = True
    rb3_df.loc[neg_mask, "Exclude_Reason"] = "negative or zero β₃"

    # CEH13 outlier (near-zero β₃ → 1/β₃ ≈ 526 months)
    ceh13_mask = rb3_df["well_norm"] == "ceh13"
    rb3_df.loc[ceh13_mask & ~rb3_df["Excluded"], "Excluded"] = True
    rb3_df.loc[ceh13_mask & ~rb3_df["Excluded"], "Exclude_Reason"] = (
        "near-zero β₃ (1/β₃ ≈ 526 months outlier)"
    )

    # Compute t_R and t½ for non-excluded wells
    rb3_df["recip_beta3_months"] = np.nan
    rb3_df["half_life_months"]   = np.nan
    valid = ~rb3_df["Excluded"]
    rb3_df.loc[valid, "recip_beta3_months"] = 1.0 / rb3_df.loc[valid, "beta_3"]
    rb3_df.loc[valid, "half_life_months"]   = np.log(2) / rb3_df.loc[valid, "beta_3"]

    rb3_df = rb3_df.rename(columns={"beta_3_drainage": "beta_3"})
    rb3_df = rb3_df[[
        "Well", "Cluster", "Easting", "Northing",
        "beta_3", "recip_beta3_months", "half_life_months",
        "Excluded", "Exclude_Reason",
    ]]
    rb3_df = rb3_df.sort_values(["Cluster", "Well"]).reset_index(drop=True)

    n_valid = valid.sum()
    n_excl = rb3_df["Excluded"].sum()
    excl_wells = rb3_df.loc[rb3_df["Excluded"], "Well"].tolist()
    print(f"  1/β₃ computed for {n_valid} wells; {n_excl} excluded "
          f"({', '.join(w.upper() for w in excl_wells)})")

    for cid in sorted(rb3_df.loc[~rb3_df["Excluded"], "Cluster"].unique()):
        sub = rb3_df[(rb3_df["Cluster"] == cid) & (~rb3_df["Excluded"])]
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        hl  = pd.to_numeric(sub["half_life_months"], errors="coerce").dropna()
        rb3 = pd.to_numeric(sub["recip_beta3_months"], errors="coerce").dropna()
        print(f"    {label}: t½ = {hl.mean():.1f} months "
              f"(range {hl.min():.1f}–{hl.max():.1f}), "
              f"1/β₃ = {rb3.mean():.1f} months")

    return rb3_df


def plot_halflife_map(rb3_df, out_path):
    """
    Linear griddata surface of drainage decay half-life t½ = ln(2)/β₃ (months).

    Fig 46. The half-life is the time for excess groundwater storage above the
    drainage datum to drain to half its initial value through natural discharge
    alone. Surface rendered as pcolormesh via add_idw_surface, clipped to the
    NNR site boundary via make_site_mask. CEH13 and CEH14 excluded from
    interpolation and shown as red crosses.
    """
    from matplotlib.lines import Line2D
    from utils.map_utils import (
        load_dem_hillshade, add_kml_features, add_en_axes, add_idw_surface,
    )

    valid    = rb3_df[~rb3_df["Excluded"]].copy()
    excluded = rb3_df[rb3_df["Excluded"]].copy()

    hl     = valid["half_life_months"].values
    hl_min = np.floor(hl.min())
    hl_max = np.ceil(hl.max())
    cmap   = get_cmap("RdYlBu_r")  # blue = short half-life (fast), red = long (slow)

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white", dpi=200)
    add_en_axes(ax)

    # Layer 1 — greyscale hillshade DEM
    _, dem_loaded, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=0.35, vert_exag=3.0, zorder=1)
    if not dem_loaded:
        warn("DEM hillshade unavailable — plain background used")
        ax.set_facecolor("#EEF2F6")

    # Layer 2 — semi-transparent t½ surface (pcolormesh + contour lines)
    mesh, gx, gy, surf_masked = add_idw_surface(
        ax, valid, "half_life_months",
        easting_col="Easting", northing_col="Northing",
        cmap=cmap, vmin=hl_min, vmax=hl_max,
        alpha=0.65, zorder=2, apply_site_mask=True,
    )
    cl = ax.contour(gx, gy, surf_masked, levels=10,
                    colors="black" if BW_MODE else "white",
                    linewidths=0.6, alpha=0.6, zorder=3)
    ax.clabel(cl, fmt="%.1f", fontsize=7,
              colors="black" if BW_MODE else "white")

    # Layer 3 — KML site features
    site_feature_handles = []
    try:
        site_feature_handles = add_kml_features(ax, DATA_DIR)
        print(f"  KML features added ({len(site_feature_handles)} layers)")
    except Exception as e:
        warn(f"KML features failed: {e}")

    # Colourbar
    cbar = fig.colorbar(mesh, ax=ax, fraction=0.025, pad=0.01, shrink=0.75)
    cbar.set_label("Drainage decay half-life  t½ = ln(2)/β₃  (months)",
                   fontsize=10, labelpad=10)

    # ── Well markers ──────────────────────────────────────────────────────────
    cluster_handles = []
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = valid[valid["Cluster"] == cid]
        if sub.empty:
            continue
        hatch = "//" if cid in FOREST_CIDS else None
        ax.scatter(sub["Easting"], sub["Northing"],
                   c=CLUSTER_COLOURS[cid],
                   s=60, marker=CLUSTER_MARKERS[cid],
                   edgecolors="black", linewidths=0.8,
                   alpha=0.92, zorder=5, hatch=hatch)
        cluster_handles.append(Line2D(
            [0], [0], marker=CLUSTER_MARKERS[cid], color="w",
            markerfacecolor=CLUSTER_COLOURS[cid],
            markeredgecolor="black", markersize=10,
            label=CLUSTER_LABELS[cid]))

    # t½ value labels
    for _, row in valid.iterrows():
        ax.annotate(f"{row['half_life_months']:.1f}",
                    (row["Easting"], row["Northing"]),
                    xytext=(4, 4), textcoords="offset points",
                    fontsize=6, color="#111111", zorder=6)

    # Excluded wells — red crosses
    exclude_handles = []
    if not excluded.empty:
        ax.scatter(excluded["Easting"], excluded["Northing"],
                   marker="x", c="red", s=120,
                   linewidths=2.0, zorder=7)
        for _, row in excluded.iterrows():
            reason = row["Exclude_Reason"] if row["Exclude_Reason"] else "excluded"
            ax.annotate(f"{row['Well'].upper()}\n({reason})",
                        (row["Easting"], row["Northing"]),
                        xytext=(6, 6), textcoords="offset points",
                        fontsize=6, color="red", style="italic", zorder=8)
        exclude_handles.append(
            Line2D([0], [0], marker="x", color="red", markersize=9,
                   linewidth=2, linestyle="none",
                   label="Excluded (negative or near-zero β₃)"))

    # ── Legends ───────────────────────────────────────────────────────────────
    cluster_leg = ax.legend(
        handles=cluster_handles + exclude_handles, loc="lower left",
        title="Cluster  (// = forest interception correction)",
        fontsize=8, framealpha=0.95, edgecolor="#CCCCCC")
    ax.add_artist(cluster_leg)

    if site_feature_handles:
        ax.legend(handles=site_feature_handles, title="Site Features",
                  loc="upper left", fontsize=8,
                  framealpha=0.95, edgecolor="#CCCCCC")

    ax.set_title(
        f"Drainage Decay Half-life  t½ = ln(2)/β₃  — Newborough Warren 2005–{_END_YEAR}\n"
        "Linear griddata interpolation  |  β₃ from SSM per-well fit (Section 3.4.3)\n"
        "High t½ (red): excess groundwater persists longer after recharge  |  "
        "CEH13, CEH14 excluded",
        fontsize=9, fontweight="bold", pad=10)

    ax.tick_params(labelsize=8)
    plt.tight_layout()
    render_figure(fig, out_path, facecolor="white")
    plt.close()
    print(f"  Half-life map saved → {out_path.name}")


# plot_drainage_timescale_map() removed in v1.5.0 — dead code since v1.4.0.
# The τ CSV (OUT_18_DRAINAGE_TIMESCALE_CSV) is still written by
# compute_drainage_timescale(); only the figure function has been removed.

def plot_aquifer_diagnostic_synthesis(rb3_df, out_path):
    """
    Scatter plot of drainage decay half-life (t½ = ln(2)/β₃) vs iterative NSE
    improvement (ΔNSE = NSE_SSM − NSE_TLM), with points coloured by cluster
    and sized by WTF-derived Sy.

    Synthesises three independently derived per-well diagnostics into a
    single aquifer architecture characterisation. Cluster-mean markers
    (larger stars) anchor the pattern. t½ replaces τ = Sy/β₃ on the y-axis
    as the directly interpretable drainage decay timescale (v1.4.0).

    Excludes wells flagged in rb3_df (CEH13, CEH14).
    """
    from matplotlib.lines import Line2D

    # ── Load ΔNSE and Sy ──────────────────────────────────────────────────────
    nse_df = pd.read_csv(INT_LCSC_MODEL_STATS)
    nse_df["norm"] = nse_df["Well_Normalized"].str.lower().str.strip()

    sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
    sy_df["norm"] = sy_df["Well"].str.lower().str.strip()

    valid = rb3_df[~rb3_df["Excluded"]].copy()
    valid["norm"] = valid["Well"].str.lower().str.strip()

    # Merge ΔNSE
    merged = valid.merge(
        nse_df[["norm", "Iterative_NSE_Improvement"]],
        on="norm", how="inner"
    )
    merged = merged.rename(columns={"Iterative_NSE_Improvement": "dNSE"})

    # Merge Sy
    merged = merged.merge(sy_df[["norm", "Sy_median"]], on="norm", how="left")

    n_matched = len(merged)
    n_missed  = len(valid) - n_matched
    if n_missed > 0:
        missed = set(valid["norm"]) - set(merged["norm"])
        print(f"  [WARNING] {n_missed} wells missing ΔNSE data: "
              f"{', '.join(sorted(missed))}")
    print(f"  {n_matched} wells with t½ + ΔNSE + Sy for synthesis scatter")

    # ── Compute cluster means ─────────────────────────────────────────────────
    cmeans = merged.groupby("Cluster").agg(
        hl_mean=("half_life_months", "mean"),
        dNSE_mean=("dNSE", "mean"),
        Sy_mean=("Sy_median", "mean"),
    ).reset_index()

    # ── Figure ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 7.5), facecolor="white", dpi=200)

    # Size scaling: map Sy range to marker area range
    sy_min, sy_max = merged["Sy_median"].min(), merged["Sy_median"].max()
    size_min, size_max = 40, 220
    def sy_to_size(sy):
        if sy_max == sy_min:
            return (size_min + size_max) / 2
        return size_min + (sy - sy_min) / (sy_max - sy_min) * (size_max - size_min)

    # Individual wells — scatter by cluster
    legend_handles = []
    for cid in sorted(CLUSTER_LABELS.keys()):
        sub = merged[merged["Cluster"] == cid]
        if sub.empty:
            continue
        sizes = sub["Sy_median"].apply(sy_to_size)
        ax.scatter(sub["dNSE"], sub["half_life_months"],
                   c=CLUSTER_COLOURS[cid],
                   s=sizes, marker=CLUSTER_MARKERS[cid],
                   edgecolors="black", linewidths=0.5,
                   alpha=0.75, zorder=4)
        legend_handles.append(Line2D(
            [0], [0], marker=CLUSTER_MARKERS[cid], color="w",
            markerfacecolor=CLUSTER_COLOURS[cid],
            markeredgecolor="black", markersize=10,
            label=CLUSTER_LABELS[cid]))

    # Cluster means — larger star markers
    for _, row in cmeans.iterrows():
        cid = int(row["Cluster"])
        ax.scatter(row["dNSE_mean"], row["hl_mean"],
                   c=CLUSTER_COLOURS[cid],
                   s=300, marker="*",
                   edgecolors="black", linewidths=1.5,
                   alpha=0.95, zorder=6)

    legend_handles.append(Line2D(
        [0], [0], marker="*", color="w",
        markerfacecolor="#AAAAAA",
        markeredgecolor="black", markeredgewidth=1.5,
        markersize=14, label="Cluster mean"))

    # Sy size legend — three representative sizes
    sy_legend_vals = [0.20, 0.30, 0.40]
    sy_legend_handles = []
    for sv in sy_legend_vals:
        if sv < sy_min or sv > sy_max + 0.02:
            continue
        sy_legend_handles.append(Line2D(
            [0], [0], marker="o", color="w",
            markerfacecolor="#CCCCCC",
            markeredgecolor="black",
            markersize=np.sqrt(sy_to_size(sv)) * 0.65,
            label=f"Sy = {sv:.2f}"))

    # ── Annotation regions ────────────────────────────────────────────────────
    annotations = {
        1: ("shallow pan\n(lake boundary)",    0.12, -0.08),
        4: ("deep sponge\n(impeded drainage)", -0.06,  0.06),
        5: ("coastal forest\n(deeper sand)",    0.08, -0.06),
    }
    for cid, (text, dx_frac, dy_frac) in annotations.items():
        cm = cmeans[cmeans["Cluster"] == cid]
        if cm.empty:
            continue
        x_pos = cm["dNSE_mean"].iloc[0]
        y_pos = cm["hl_mean"].iloc[0]
        x_range = merged["dNSE"].max() - merged["dNSE"].min()
        y_range = merged["half_life_months"].max() - merged["half_life_months"].min()
        ax.annotate(text,
                    (x_pos, y_pos),
                    xytext=(x_pos + dx_frac * x_range,
                            y_pos + dy_frac * y_range),
                    fontsize=8, fontstyle="italic", color="#444444",
                    ha="center",
                    arrowprops=dict(arrowstyle="->", color="#999999",
                                   lw=0.8, connectionstyle="arc3,rad=0.15"),
                    zorder=7)

    # ── Axes and labels ───────────────────────────────────────────────────────
    ax.set_xlabel("ΔNSE  (iterative NSE improvement: SSM − TLM)", fontsize=11)
    ax.set_ylabel("Drainage decay half-life  t½ = ln(2)/β₃  (months)", fontsize=11)
    ax.set_title(
        f"Aquifer Diagnostic Synthesis — Newborough Warren 2005–{_END_YEAR}\n"
        "Three independently derived parameters triangulate aquifer architecture\n"
        "t½ (drainage decay half-life) vs ΔNSE (drainage sensitivity), "
        "point size ∝ Sy (storage capacity)",
        fontsize=10, fontweight="bold", pad=12)

    x_pad = (merged["dNSE"].max() - merged["dNSE"].min()) * 0.12
    y_pad = (merged["half_life_months"].max() - merged["half_life_months"].min()) * 0.10
    ax.set_xlim(merged["dNSE"].min() - x_pad,
                merged["dNSE"].max() + x_pad)
    ax.set_ylim(max(0, merged["half_life_months"].min() - y_pad),
                merged["half_life_months"].max() + y_pad * 2)

    ax.grid(True, alpha=0.3, linestyle="--")

    # ── Legends ───────────────────────────────────────────────────────────────
    cluster_leg = ax.legend(
        handles=legend_handles, loc="upper left",
        title="Cluster", fontsize=9, title_fontsize=10,
        framealpha=0.95, edgecolor="#CCCCCC")
    ax.add_artist(cluster_leg)

    if sy_legend_handles:
        ax.legend(handles=sy_legend_handles, loc="center right",
                  title="Point size = Sy", fontsize=8, title_fontsize=9,
                  framealpha=0.95, edgecolor="#CCCCCC")

    plt.tight_layout()
    render_figure(fig, out_path, facecolor="white")
    plt.close()
    print(f"  Aquifer diagnostic synthesis saved → {out_path.name}")


def main(supplementary=True):
    # ── Paths ──────────────────────────────────────────────────────────────────
    banner("18", "WTF Spatial Analysis", version=__version__)
    out_root         = OUT_DIR
    out_dir          = DIR_18
    path_well_sy     = OUT_18_WELL_SY_TABLE
    path_sy_map      = OUT_18_SY_MAP
    path_contour     = OUT_18_SY_CONTOUR
    path_contour_ext = OUT_18_SY_CONTOUR_EXT

    hr()
    print("  18: WTF Spatial Analysis — Individual Well Sy and Mapping")
    print(f"  Supplementary figures: {'yes' if supplementary else 'no'}")
    hr()

    print("\nLoading well data...")
    try:
        wells_df, climate, cluster_df, locations = load_well_data(out_root)
    except Exception as e:
        error(f"Could not load well data: {e}")
        return

    print("\nRunning reference well WTF analysis...")
    well_results = wtf_individual_wells(wells_df, climate, cluster_df, locations)

    print("\nExporting reference well Sy table...")
    well_results.to_csv(path_well_sy, index=False)
    print(f"  Saved → {path_well_sy.name}")
    well_results.to_csv(INT_WTF_WELL_SY, index=False)
    print(f"  Intermediate copy → {INT_WTF_WELL_SY.name}")

    # ── Paper figure — always generated ──────────────────────────────────
    print("\nGenerating spatial point map (reference wells)...")
    plot_spatial_map(well_results, path_sy_map)

    # ── Supplementary figures — only with --supplementary flag ────────────
    if supplementary:
        print("\nGenerating Sy contour map (reference wells only)...")
        plot_contour_map(well_results, path_contour)

        print("\nRunning extended well WTF analysis...")
        ext_results = wtf_extended_wells(climate, locations, out_root)
        if ext_results is not None:
            print("\nGenerating Sy contour map (reference + extended wells)...")
            plot_contour_map_extended(well_results, ext_results, path_contour_ext)
        else:
            print("  Skipping extended contour map — no extended well results")

        # ── Fig 46 — Drainage decay half-life map (t½ = ln(2)/β₃) ───────
        print("\nComputing drainage decay half-life (t½ = ln(2)/β₃)...")
        rb3_df = compute_recip_beta3()

        print("\nGenerating half-life map (Fig 46)...")
        plot_halflife_map(rb3_df, OUT_18_HALFLIFE_MAP)

        # τ = Sy/β₃ retained as intermediate CSV for discussion-section
        # reference and Paper 1; no figure emitted (v1.4.0).
        print("\nComputing storage–drainage index (τ = Sy/β₃) — CSV only...")
        tau_df = compute_drainage_timescale(well_results)
        tau_df.to_csv(OUT_18_DRAINAGE_TIMESCALE_CSV, index=False)
        print(f"  Saved → {OUT_18_DRAINAGE_TIMESCALE_CSV.name}")

        # ── Fig 48 — Aquifer diagnostic synthesis scatter ─────────────────
        print("\nGenerating aquifer diagnostic synthesis scatter (Fig 48)...")
        plot_aquifer_diagnostic_synthesis(rb3_df, OUT_18_AQUIFER_SYNTHESIS)

        # ── §4.9.3 traceable report numbers ───────────────────────────────
        # Per-cluster t½, 1/β₃, and τ ranges. CEH13/CEH14 excluded from
        # t½ and 1/β₃ maps; τ CSV retains them as excluded rows.
        rpt = ReportNumbers()

        # Excluded wells
        excl_notes = {
            "ceh13": "near-zero β₃ outlier (excluded from half-life map)",
            "ceh14": "negative β₃ (excluded from half-life map)",
        }
        for w, why in excl_notes.items():
            wr = rb3_df[rb3_df["Well"].str.lower() == w]
            if len(wr):
                rpt.add(f"recip_b3_{w}",
                        float(wr["recip_beta3_months"].iloc[0])
                        if pd.notna(wr["recip_beta3_months"].iloc[0]) else np.nan,
                        unit="months", well=w.upper(),
                        era="excluded" if bool(wr["Excluded"].iloc[0]) else "",
                        note=why)

        # Per-cluster t½ min/max
        rb3_ok = rb3_df[~rb3_df["Excluded"]]
        for cid, grp in rb3_ok.groupby("Cluster"):
            hl  = pd.to_numeric(grp["half_life_months"],   errors="coerce").dropna()
            rb3 = pd.to_numeric(grp["recip_beta3_months"], errors="coerce").dropna()
            n   = len(hl)
            if n:
                rpt.add(f"C{int(cid)}_halflife_min", float(hl.min()), unit="months",
                        note=f"min t½, C{int(cid)}, reference network, n={n}")
                rpt.add(f"C{int(cid)}_halflife_max", float(hl.max()), unit="months",
                        note=f"max t½, C{int(cid)}, reference network, n={n}")
                rpt.add(f"C{int(cid)}_halflife_mean", float(hl.mean()), unit="months",
                        note=f"mean t½, C{int(cid)}, reference network, n={n}")
                rpt.add(f"C{int(cid)}_recip_b3_mean", float(rb3.mean()), unit="months",
                        note=f"mean 1/β₃, C{int(cid)}, reference network, n={n}")

        # Per-cluster τ min/max (discussion reference only)
        ok = tau_df[~tau_df["Excluded"]]
        for cid, grp in ok.groupby("Cluster"):
            taus = pd.to_numeric(grp["tau_months"], errors="coerce").dropna()
            if len(taus):
                rpt.add(f"C{int(cid)}_tau_min", float(taus.min()), unit="months",
                        note=f"min τ, C{int(cid)}, reference network, n={len(taus)}")
                rpt.add(f"C{int(cid)}_tau_max", float(taus.max()), unit="months",
                        note=f"max τ, C{int(cid)}, reference network, n={len(taus)}")

        n_saved = rpt.save(OUT_18_REPORT_NUMBERS)
        print(f"  Saved → {OUT_18_REPORT_NUMBERS.name} ({n_saved} report numbers)")


    else:
        print("\nSupplementary contour maps skipped "
              "(pass --supplementary to generate)")

    print(f"\nAll outputs written to {out_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Script 18 — WTF Spatial Analysis")
    parser.add_argument("--no-supplementary", action="store_false",
                        dest="supplementary",
                        help="Skip Sy IDW contour maps for supplementary materials.")
    parser.set_defaults(supplementary=True)
    args = parser.parse_args()
    main(supplementary=args.supplementary)
