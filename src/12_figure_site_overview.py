"""
====================================================================================
FIGURE 1: SITE TOPOGRAPHY AND GROUNDWATER MONITORING NETWORK (map_dem_overview.py)
====================================================================================
Purpose:
    Produces a publication-quality GIS map (EPSG:27700 / British National Grid)
    overlaying the full monitoring network (≈97 wells in current data), site
    features, and stream networks onto the full extent of the Digital
    Elevation Model (DEM).  Reads the network from data/well_metadata.csv;
    the exact count printed at run time is the source of truth.

Outputs:
    outputs/12_figure_site_overview/12_01_dem_site_overview.png
    (PNG @ dpi=300 — preserves DEM hillshade detail and well-label
    text; project convention is PNG @ dpi=300 for spatial / dense
    figures and JPEG @ dpi=200 for hydrograph / scenario panels.)
    outputs/12_figure_site_overview/12_02_break_in_slope.csv
    outputs/12_figure_site_overview/12_02_break_in_slope.png
    outputs/12_figure_site_overview/12_report_numbers.csv

The northern break in slope (v1.4.0, D-099)
    Script 12 already reads the DEM and owns the site topographic overview, so
    the break is an emission from an existing step rather than a new pipeline
    step: no _DOCUMENTED_COUNTS move and no manifest-guard trip. It does make
    Script 12 a NUMERIC emitter for the first time, which is why a
    report-numbers file appears here.

    12_01_dem_site_overview.png is REPORT FIGURE 1 and is not touched. The
    break line gets its own map. Overlaying it on Figure 1 is available and is
    Martin's call, not a side effect.
====================================================================================
"""

__version__ = "1.4.0"  # Hollingham (2026) — 2026-08-30
#
# Changelog
#   1.4.0 (2026-08-30) — THE NORTHERN BREAK IN SLOPE. Script 12 becomes a
#         numeric emitter. Per easting column of the 2 m DEM, inside a window
#         that covers the massif-to-plain transition and nothing else, the
#         north-south profile is smoothed and the break is the first sample,
#         walking north to south, within BREAK_RELATIVE_M of the column's own
#         10th-percentile "plain" elevation. Break northings are then median
#         filtered across columns.
#
#         THE RULE IS PERCENTILE-RELATIVE, AND THAT IS THE WHOLE DESIGN. Two
#         other rules were built and rejected on measurement, not taste:
#           * "first flattening walking south" catches an upper BENCH on the
#             massif, 557 m north of the lake — a real flattening, the wrong
#             feature;
#           * "steepest sustained descent" catches individual DUNE FACES and
#             scatters the toe elevation by 8 m.
#         Both fail because they look for a shape. Measuring height above the
#         column's own low ground looks for the surface instead, which is what
#         the boundary actually is.
#
#         GATED, D-085/D-089 shape. The result is WITHHELD with a stated reason
#         if too few columns resolve or if the break-elevation sd exceeds
#         config.BREAK_ELEV_SD_TOL_M — an incoherent line means the rule found
#         different features in different columns, and an average of those is
#         plausible and meaningless. The tolerance is BREAK_RELATIVE_M itself,
#         the band that defines the feature; the rejected rules sit 2.7x outside
#         it. See config.py and D-099.
#
#         WHAT IT DOES NOT CLAIM. It is a CANDIDATE landward limit for the sand
#         aquifer, flagged modelled and unconfirmed. It emits no cluster-relative
#         column: the C1 association was tested and rejected as definitional
#         (D-099).
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).
#
# Changelog
#   1.3.0 (2026-08-12) — Well-name labels now placed by adjustText rather than
#         a fixed (4, 4) pt offset, resolving the label collisions that the 7 pt
#         size exposed in the western forest block, the nw11/wmc4/nw1/nw2 knot
#         and the T41 group. Leader lines drawn where a label is displaced.
#         Brings Script 12 into line with Scripts 04/05/06/13, which have used
#         adjustText throughout, and with the report Methods, which already
#         states that label placement and occlusion avoidance use adjustText.
#         Font size, halo, figsize and marker size unchanged from 1.2.1.
#   1.2.1 (2026-08-12) — Well-name labels raised from 5 pt to 7 pt for
#         legibility at print size; matches the 7 pt bold well labels used on
#         the Script 11b maps of the same frame. Halo stroke, label offset and
#         figsize deliberately unchanged. Fixed banner() version literal, which
#         had been reporting 1.1.0 since the 1.2.0 bump — now reads __version__.
#   1.2.0 (2026-06-28) — see CHANGELOG.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    DATA_LOCATIONS_RAW,
    INT_LOCATIONS,
    OUT_12_DEM_OVERVIEW,
    OUT_12_BREAK_IN_SLOPE,
    OUT_12_BREAK_FIG,
    OUT_12_REPORT_NUMBERS,
)
from utils.map_utils import add_kml_features, load_dem_layer, load_dem_hillshade
from utils import config
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import fiona
from adjustText import adjust_text
import warnings

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import render_figure

# Enable KML driver in GeoPandas/Fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

# Suppress messy warnings for the reviewer's terminal output
warnings.filterwarnings('ignore')

# Publication-quality typography
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
})

def generate_dem_map():
    print("\n" + "="*60)
    print(" GENERATING FIGURE 1: FULL DEM AND SITE OVERVIEW")
    print("="*60)

    # 1. Load the Well Data
    # (Output paths are sourced from utils.paths; no per-script
    # ../outputs directory is needed.)
    wells_path = DATA_LOCATIONS_RAW
    if not os.path.exists(wells_path):
        error(f"Could not find {wells_path}. Please check data folder.")
        return

    wells = pd.read_csv(wells_path)
    wells.columns = wells.columns.str.strip()

    # Convert to a GeoDataFrame using British National Grid (EPSG:27700)
    gdf_wells = gpd.GeoDataFrame(
        wells,
        geometry=gpd.points_from_xy(wells['E'], wells['N']),
        crs="EPSG:27700"
    )

    # 2. Setup the Figure
    fig, ax = plt.subplots(figsize=(12, 12))

    # 3. Load and Plot the GeoTIFF DEM (with fallback)
    # load_dem_layer() applies the project-standard colourmap and alpha=0.45,
    # matching every other pipeline map.  Script 12 is excluded from the
    # canonical map extent (it uses the full DEM frame); the xlim/ylim set
    # inside load_dem_layer() are overridden below using the imshow extent.
    info("Loading DEM via map_utils.load_dem_layer()...")
    dem_layer, dem_loaded = load_dem_layer(ax, DATA_DIR)

    if dem_loaded:
        # Attach colourbar to the shared dem_layer object
        cbar = fig.colorbar(dem_layer, ax=ax, shrink=0.5, pad=0.03, extend='both')
        cbar.set_label('Elevation (m AOD)', rotation=270, labelpad=20,
                       fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)

        # Script 12 shows the full DEM frame, not the canonical site extent.
        # Recover the true DEM bounds from the imshow object and reapply;
        # this is the only extent difference from the other pipeline maps.
        # get_extent() returns (left, right, bottom, top).
        dem_extent = dem_layer.get_extent()
        ax.set_xlim(dem_extent[0], dem_extent[1])
        ax.set_ylim(362000, dem_extent[3])

    else:
        info("Local DEM not found. Fetching fallback topographical basemap...")
        ctx.add_basemap(ax, crs=gdf_wells.crs.to_string(),
                        source=ctx.providers.OpenTopoMap, alpha=0.8, zorder=0)

    # =======================================================
    # 4. KML Site Features (via map_utils — includes broadleaf restock block)
    # =======================================================
    info("Adding KML site features...")
    site_handles = add_kml_features(ax, DATA_DIR)

    # 5. Overlay the Monitoring Wells
    info("Plotting Monitoring Wells...")
    gdf_wells.plot(
        ax=ax,
        color='red',
        markersize=30,
        edgecolor='black',
        linewidth=1.0,
        zorder=5
    )

    # 5b. Label each well with its name
    #
    # Labels are collected here and positioned by adjustText after the site
    # features are drawn (see step 6b), so the solver sees the final artist
    # set.  The white halo is retained — unlike the Script 13 design map,
    # these labels sit directly on the DEM colour ramp.
    info("Adding well name labels...")
    import matplotlib.patheffects as pe
    well_labels = [
        ax.text(
            row['E'], row['N'], row['Name'],
            fontsize=7,
            color='black',
            fontweight='bold',
            zorder=6,
            clip_on=True,
            path_effects=[pe.withStroke(linewidth=1.5, foreground='white')],
        )
        for _, row in gdf_wells.iterrows()
    ]

    # If DEM didn't load, frame around the wells instead
    if not dem_loaded:
        x_min, y_min, x_max, y_max = gdf_wells.total_bounds
        buffer = 300
        ax.set_xlim(x_min - buffer, x_max + buffer)
        ax.set_ylim(y_min - buffer, y_max + buffer)

    # =======================================================
    # 6. Formatting & Legend
    # =======================================================
    plt.title('Figure 1: Site Topography and Hydrogeological Features',
              fontweight='bold', fontsize=16, pad=15)
    plt.xlabel('Easting (m, OSGB36)')
    plt.ylabel('Northing (m, OSGB36)')

    # Custom Legend — well marker plus site feature handles from add_kml_features
    from matplotlib.lines import Line2D
    well_handle = Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
                         markeredgecolor='black', markersize=8,
                         label=f'Monitoring Wells (n={len(gdf_wells)})')
    ax.legend(handles=[well_handle] + list(site_handles),
              loc='lower left', framealpha=0.9, edgecolor='black')

    # =======================================================
    # 6b. Label decluttering
    # =======================================================
    # Repel overlapping well labels and draw a leader line back to the marker
    # wherever a label has been displaced.  Placement is solved against the
    # markers and the axis frame, not hard-coded per well, so the figure stays
    # correct if the network or the map extent changes.
    info(f"Repelling {len(well_labels)} well name labels...")
    adjust_text(
        well_labels,
        arrowprops=dict(arrowstyle="-", color='gray', lw=0.5),
        ax=ax,
    )

    # Save in high resolution to outputs folder
    output_filename = OUT_12_DEM_OVERVIEW
    plt.tight_layout()
    render_figure(plt.gcf(), output_filename)
    print(f"  [SUCCESS] Map saved locally as {output_filename}")
    plt.close()

# ======================================================================
# The northern break in slope (D-099)
# ======================================================================
def _boxcar(a, w):
    """Moving average of `a` over `w` samples, padded by EDGE REPETITION.

    Zero-padding would drag the ends of every profile toward zero and invent a
    break at the window edge, which is the one place a break must not be
    invented: the window edge is an artefact of where the window was drawn.
    """
    return np.convolve(np.pad(a, w // 2, mode="edge"),
                       np.ones(w) / w, mode="valid")


def _detect_break(dem_e_arr, dem_n_arr, dem_data):
    """Per-easting-column break in slope. Returns a DataFrame, possibly empty.

    THE RULE, and why it is percentile-relative.

      For each column, the plain reference is the 10th percentile of the
      smoothed north-south profile — not its minimum, which is one pixel and
      follows any hollow. The break is the first sample, WALKING NORTH TO SOUTH,
      that comes within BREAK_RELATIVE_M of that reference: the southern edge of
      the northern massif.

      Two rules that look more natural were built first and both fail, on
      measurement rather than taste. "First flattening walking south" finds an
      upper BENCH on the massif 557 m north of the lake: a real flattening, the
      wrong feature. "Steepest sustained descent" finds individual DUNE FACES
      and scatters the toe elevation by 8 m. Both search for a SHAPE, and the
      massif has many shapes. Height above the column's own low ground searches
      for the SURFACE, which is what the physiographic boundary is.

    Coordinates are CELL CENTRES. dem_e_arr / dem_n_arr as returned by
    load_dem_hillshade are cell origins; half a cell is 1 m here and the break
    is reported to the metre, so the offset is applied rather than ignored.
    """
    from scipy.ndimage import median_filter

    half_e = abs(float(dem_e_arr[1] - dem_e_arr[0])) / 2.0
    half_n = abs(float(dem_n_arr[1] - dem_n_arr[0])) / 2.0
    e_cent = dem_e_arr + half_e
    # dem_n_arr descends (north to south), so row order IS the walk direction
    # and no reversal is needed. Asserted rather than assumed: a DEM written
    # south-up would silently invert the rule.
    if not dem_n_arr[0] > dem_n_arr[-1]:
        raise RuntimeError("DEM rows are not north-to-south; the break rule "
                           "walks north to south and would be inverted")
    n_cent = dem_n_arr - half_n

    cm = ((e_cent >= config.BREAK_WINDOW_E_MIN)
          & (e_cent < config.BREAK_WINDOW_E_MAX))
    rm = ((n_cent >= config.BREAK_WINDOW_N_MIN)
          & (n_cent < config.BREAK_WINDOW_N_MAX))
    ecols, nrows = e_cent[cm], n_cent[rm]
    sub = dem_data[np.ix_(rm, cm)]
    info(f"break window {config.BREAK_WINDOW_E_MIN:.0f}-{config.BREAK_WINDOW_E_MAX:.0f} E, "
         f"{config.BREAK_WINDOW_N_MIN:.0f}-{config.BREAK_WINDOW_N_MAX:.0f} N "
         f"— {sub.shape[1]} columns x {sub.shape[0]} rows of the DEM")

    rows, skipped_counts = [], {"nodata": 0, "no_plain": 0, "no_relief": 0,
                                "no_break": 0, "starts_on_plain": 0}
    for j in range(sub.shape[1]):
        col = sub[:, j]
        if np.isnan(col).all():
            skipped_counts["nodata"] += 1
            continue
        sm = _boxcar(col, config.BREAK_SMOOTH_SAMPLES)
        plain = float(np.nanpercentile(sm, config.BREAK_PLAIN_PERCENTILE))
        if plain > config.BREAK_MAX_PLAIN_ELEV_M:
            skipped_counts["no_plain"] += 1
            continue
        if float(np.nanmax(sm)) - plain < config.BREAK_MIN_RELIEF_M:
            skipped_counts["no_relief"] += 1
            continue
        hit = np.where(sm <= plain + config.BREAK_RELATIVE_M)[0]
        if len(hit) == 0:
            skipped_counts["no_break"] += 1
            continue
        i = int(hit[0])
        if i < config.BREAK_MIN_INDEX:
            skipped_counts["starts_on_plain"] += 1
            continue
        rows.append({"easting_m": float(ecols[j]),
                     "break_northing_raw_m": float(nrows[i]),
                     "break_elevation_m": float(sm[i]),
                     "plain_elevation_m": plain,
                     "relief_m": float(np.nanmax(sm)) - plain})
    for k, v in skipped_counts.items():
        if v:
            step(f"skipped {v} column(s): {k}")
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).sort_values("easting_m").reset_index(drop=True)
    # Outlier rejection ACROSS columns, on the northings. A single column that
    # found the wrong feature moves the line by hundreds of metres and would
    # otherwise stand in the emitted geometry.
    df["break_northing_m"] = median_filter(
        df["break_northing_raw_m"].to_numpy(),
        size=config.BREAK_MEDIAN_COLUMNS, mode="reflect")
    return df


def _break_gate(df):
    """Withhold the break with a NAMED reason, D-085/D-089 shape.

    An incoherent line is the failure this gate exists for: the rule found
    different features in different columns, and their average is plausible and
    describes nothing. That has to fail loudly, because it is exactly what the
    two rejected rules did.
    """
    reasons = []
    if len(df) == 0:
        return False, ["no column in the window resolved a break"], float("nan")
    sd = float(df["break_elevation_m"].std(ddof=1))
    if len(df) < config.BREAK_MIN_COLUMNS:
        reasons.append(
            f"coverage: {len(df)} column(s) resolved, below the "
            f"{config.BREAK_MIN_COLUMNS} required "
            f"({config.BREAK_MEDIAN_COLUMNS}-column filter x 5)")
    if sd > config.BREAK_ELEV_SD_TOL_M:
        reasons.append(
            f"coherence: break-elevation sd {sd:.3f} m exceeds "
            f"{config.BREAK_ELEV_SD_TOL_M:.3f} m — the columns are not on one "
            f"surface, so the line is an average of different features")
    return (len(reasons) == 0), reasons, sd


def _break_report_numbers(df, sd, lake):
    """The citable values. Every one read from the frame this run produced."""
    e = df["easting_m"].to_numpy()
    z = df["break_elevation_m"].to_numpy()
    nf = df["break_northing_m"].to_numpy()
    k = int(np.argmin(np.abs(e - lake["E"])))
    lake_break_n, lake_break_z = float(nf[k]), float(z[k])
    rows = [
        ("break_n_columns", len(df), "count",
         "easting columns of the 2 m DEM resolving a break inside the window"),
        ("break_elevation_median_m", float(np.median(z)), "m AOD",
         "median elevation of the northern break in slope"),
        ("break_elevation_p10_m", float(np.percentile(z, 10)), "m AOD", "10th percentile"),
        ("break_elevation_p90_m", float(np.percentile(z, 90)), "m AOD", "90th percentile"),
        ("break_elevation_sd_m", sd, "m",
         "coherence statistic; the gate withholds above "
         f"config.BREAK_ELEV_SD_TOL_M = {config.BREAK_ELEV_SD_TOL_M}"),
        ("break_northing_min_m", float(nf.min()), "m OSGB36", "median-filtered"),
        ("break_northing_max_m", float(nf.max()), "m OSGB36", "median-filtered"),
        ("break_easting_min_m", float(e.min()), "m OSGB36",
         "westernmost resolving column"),
        ("break_easting_max_m", float(e.max()), "m OSGB36",
         "easternmost resolving column"),
        ("break_lake_offset_north_m", lake_break_n - float(lake["N"]), "m",
         "the break lies this far north of Llyn Rhos-Ddu at the lake's easting; "
         "lake position from 01_locations.csv, not typed"),
        ("break_lake_offset_vertical_m", lake_break_z - float(lake["Z"]), "m",
         "the break stands this far above the lake surface at the lake's easting"),
    ]
    return pd.DataFrame([
        {"Parameter": n, "Well": "", "Era": "",
         "Value": v, "Unit": u, "Note": note_txt}
        for n, v, u, note_txt in rows])


def _break_figure(df, lake, out_path):
    """The break on its own map. NOT an overlay on Figure 1.

    load_dem_hillshade() needs an `ax` because it draws. There is no bare
    array-only DEM loader in map_utils, so rather than open the raster
    independently this figure's own axes are created FIRST and the loader draws
    the hillshade it is meant to draw; the arrays it returns are what the
    detection ran on. One read, one loader, no duplicate raster access.
    """
    fig, ax = plt.subplots(figsize=(11, 7), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=0.55)
    ax.plot(df["easting_m"], df["break_northing_m"], color="crimson", lw=2.0,
            zorder=6, label=f"Northern break in slope (n={len(df)} columns)")
    ax.plot(df["easting_m"], df["break_northing_raw_m"], color="crimson",
            lw=0.5, alpha=0.35, zorder=5,
            label="before the alongshore median filter")
    ax.plot([lake["E"]], [lake["N"]], marker="o", ms=8, color="dodgerblue",
            markeredgecolor="black", zorder=7, ls="none", label="Llyn Rhos-Ddu")
    ax.set_xlim(config.BREAK_WINDOW_E_MIN, config.BREAK_WINDOW_E_MAX)
    ax.set_ylim(config.BREAK_WINDOW_N_MIN, config.BREAK_WINDOW_N_MAX)
    ax.set_xlabel("Easting (m, OSGB36)")
    ax.set_ylabel("Northing (m, OSGB36)")
    ax.set_title("Northern break in slope — the dune massif against the "
                 "Malltraeth plain\n(northern boundary only; a CANDIDATE "
                 "aquifer limit, modelled and unconfirmed)",
                 fontsize=11, fontweight="bold")
    ax.legend(loc="lower left", framealpha=0.9, edgecolor="black", fontsize=8)
    fig.tight_layout()
    render_figure(fig, out_path)
    plt.close(fig)


def measure_break_in_slope():
    """Detect, gate, and emit the northern break in slope."""
    phase(2, "Northern break in slope")

    locs = pd.read_csv(INT_LOCATIONS)
    key = locs["Name"].astype(str).str.strip().str.lower()
    hit = locs[key.isin({k.lower() for k in config.LAKE_GAUGE_KEYS})]
    if hit.empty:
        warn("Llyn Rhos-Ddu not found in 01_locations.csv — break offsets "
             "cannot be computed; skipping the break measurement")
        return
    lr = hit.iloc[0]
    lake = {"E": float(lr["E"]), "N": float(lr["N"]),
            "Z": float(lr["ground_elev_m"])}
    info(f"Llyn Rhos-Ddu from 01_locations.csv: E {lake['E']:.3f}, "
         f"N {lake['N']:.3f}, {lake['Z']:.2f} m AOD")

    # The loader draws, so it needs axes. This throwaway figure exists only to
    # satisfy that signature; the real map is drawn in _break_figure() from the
    # same loader. Noted rather than hidden — see that function's docstring.
    fig_tmp, ax_tmp = plt.subplots()
    _hs, dem_loaded, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax_tmp, DATA_DIR)
    plt.close(fig_tmp)
    if not dem_loaded:
        warn("DEM unavailable — the break in slope cannot be measured; "
             "skipping (this is a valid state in a clone without the raster)")
        return

    df = _detect_break(dem_e_arr, dem_n_arr, dem_data)
    ok, reasons, sd = _break_gate(df)
    if not ok:
        warn("BREAK IN SLOPE WITHHELD. Reasons:")
        for r in reasons:
            warn(f"    {r}")
        out = df.copy() if len(df) else pd.DataFrame()
        if len(out):
            out["withheld"] = True
            out["withheld_reason"] = "; ".join(reasons)
            out.to_csv(OUT_12_BREAK_IN_SLOPE, index=False)
            saved(OUT_12_BREAK_IN_SLOPE.name, "WITHHELD")
        return

    z = df["break_elevation_m"]
    result("break", f"{len(df)} columns; elevation median {z.median():.3f} m AOD "
                    f"(p10 {z.quantile(0.10):.3f}, p90 {z.quantile(0.90):.3f}, "
                    f"sd {sd:.3f} m)")
    info(f"    northing {df['break_northing_m'].min():.0f} to "
         f"{df['break_northing_m'].max():.0f}, easting "
         f"{df['easting_m'].min():.0f} to {df['easting_m'].max():.0f}")

    df_out = df.copy()
    df_out["withheld"] = False
    df_out["withheld_reason"] = ""
    df_out.to_csv(OUT_12_BREAK_IN_SLOPE, index=False)
    saved(OUT_12_BREAK_IN_SLOPE.name, f"{len(df_out)} columns")

    rn = _break_report_numbers(df, sd, lake)
    rn.to_csv(OUT_12_REPORT_NUMBERS, index=False)
    saved(OUT_12_REPORT_NUMBERS.name, f"{len(rn)} value(s)")
    for nm in ("break_lake_offset_north_m", "break_lake_offset_vertical_m"):
        v = float(rn.loc[rn.Parameter == nm, "Value"].iloc[0])
        info(f"    {nm}: {v:.2f}")
    note("a CANDIDATE landward limit for the sand aquifer — modelled and "
         "unconfirmed, and the NORTHERN boundary only")

    _break_figure(df, lake, OUT_12_BREAK_FIG)
    saved(OUT_12_BREAK_FIG.name)


if __name__ == "__main__":
    banner("12", "Figure — Site Overview", version=__version__)
    make_all_dirs()
    phase(1, "Site overview map (report Figure 1)")
    generate_dem_map()
    measure_break_in_slope()
    done("12")
