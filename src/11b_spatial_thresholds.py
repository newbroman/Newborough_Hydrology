"""
11b_spatial_thresholds.py
=========================
Spatial maps of per-well eco-hydrological threshold status.

Reads per-well water table time series (reference and extended networks),
computes mean annual summer minima (August-September), converts to depth
below ground, and produces a publication-quality map zoned by Curreli et al.
(2013) eco-hydrological thresholds and scraping recovery limits derived from
the BACI analysis in Hollingham (2026).

Recovery limits are grounded in the BACI scraping benefit of +0.143 m
(Hollingham, 2026, script 09):
    SD15b excavation limit = SD15b + 0.14 = 0.75 m (shallow excavation ~0.14 m achieves SD15b)
    SD16  excavation limit = SD16  + 0.22 = 1.20 m (deeper excavation ~0.22 m achieves SD16)

DEM corrections are applied to two wells that have been scraped since the
LiDAR survey was flown:
    CEH18 (scraped October 2023, ~0.50 m removed): DEM corrected -0.50 m
    CEH21 (scraped October 2023, ~0.70 m removed): DEM corrected -0.70 m
    Both wells use post-2023 data only.

Outputs
-------
    outputs/11b_spatial_thresholds/
        11b_01_summer_minima_depth.png   — main ecological status map

Inputs (all from pipeline outputs/ directory)
-----------------------------------------------
    01_wells_clean_maod.csv         — reference network maOD time series
    01_wells_extended.csv           — extended network raw depths
    01_well_elevations.csv          — well DEM elevations (Pipe_Top_Elev)
    01_locations.csv                — well coordinates
    03_master_data.csv              — reference well cluster assignments
    06_pear_membership_audit_sitewide.csv  — extended well cluster assignments
    data/Features.kml               — site feature overlays

Called by
---------
    run_analysis.py  (or standalone: python 11b_spatial_thresholds.py)

Dependencies
------------
    Standard pipeline: numpy, pandas, matplotlib, scipy
    Spatial: rasterio (via map_utils), geopandas, fiona (via map_utils)
    Skeletonisation: not required (map_utils handles DEM/IDW)
"""

__version__ = "1.0.0"  # Hollingham (2026) — last revised 2026-04-10

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from pathlib import Path

from utils.paths import (
    OUT_DIR,
    DATA_DIR,
    INT_MASTER_DATA,
    INT_LOCATIONS,
    INT_WELLS_CLEAN,
    INT_WELLS_EXTENDED,
    INT_PEAR_AUDIT_SITEWIDE,
)
from utils.map_utils import load_dem_hillshade, add_idw_surface, add_kml_features

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
DIR_11B = OUT_DIR / "11b_spatial_thresholds"
OUT_11B_SUMMER_MAP  = DIR_11B / "11b_01_summer_minima_depth.png"
OUT_11B_WINTER_MAP  = DIR_11B / "11b_02_winter_maxima_depth.png"
OUT_11B_PFLOOD_MAP  = DIR_11B / "11b_03_pflood.png"
OUT_11B_FLOOD_FREQ  = DIR_11B / "11b_04_flood_frequency.png"

# Mean annual winter rainfall (Oct-Mar, monitoring period 2005-2026)
MEAN_WINTER_RAINFALL_MM = 521

# Sea boundary constants — rectangular fallback mask matching script 19
SEA_SOUTH_N = 362350   # m OSGB36 — southern shoreline
SEA_EAST_E  = 243850   # m OSGB36 — eastern Menai Strait
SEA_WEST_E  = 239200   # m OSGB36 — western estuary

INT_WELLS_CLEAN_MAOD = OUT_DIR / "01_wells_clean_maod.csv"
INT_WELL_ELEVATIONS  = OUT_DIR / "01_well_elevations.csv"

# ─────────────────────────────────────────────────────────────────────────────
# ECOLOGICAL THRESHOLDS (Curreli et al., 2013)
# ─────────────────────────────────────────────────────────────────────────────
SD15b     = 0.61   # m below ground — SD15b wet slack viability threshold
SD15b_REC = 0.75   # m below ground — SD15b excavation limit (~0.14 m depth achieves SD15b)
SD16      = 0.98   # m below ground — SD16 dry slack threshold
SD16_REC  = 1.20   # m below ground — SD16 excavation limit (~0.22 m depth achieves SD16)

# ─────────────────────────────────────────────────────────────────────────────
# SCRAPING CORRECTIONS
# Wells scraped since the LiDAR DEM was flown — DEM elevation reduced by the
# depth of material removed, and only post-scraping data used for the summer
# minimum calculation.
# ─────────────────────────────────────────────────────────────────────────────
SCRAPED = {
    "ceh18": {"dem_correction": 0.50, "start_yr": 2023},  # Oct 2023, ~0.50 m
    "ceh21": {"dem_correction": 0.70, "start_yr": 2023},  # Oct 2023, ~0.70 m
}

# ─────────────────────────────────────────────────────────────────────────────
# ZONE COLOURS
# ─────────────────────────────────────────────────────────────────────────────
ZONE_COLOURS = [
    "#1a7abf",  # Blue       — wet slack viable (< SD15b)
    "#a8d8a8",  # Pale green — shallow excavation viable (SD15b recoverable)
    "#ffffb2",  # Yellow     — SD16 dry slack (between excavation limits)
    "#fd8d3c",  # Orange     — deeper excavation viable (SD16 recoverable)
    "#bd0026",  # Dark red   — critical, beyond standard single scraping event
]
ZONE_BOUNDS = [0.0, SD15b, SD15b_REC, SD16, SD16_REC, 3.5]

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER COLOURS (must match utils/config.py CLUSTER_COLOURS)
# ─────────────────────────────────────────────────────────────────────────────
CLUSTER_COLS = {1: "#E377C2", 2: "#17BECF", 3: "#2CA02C", 4: "#1F77B4"}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _make_site_mask(grid_x, grid_y):
    """
    Boolean mask for the interpolation domain.

    Primary: loads site_boundary.kml (dissolved SAGA stream-cell boundary)
    via pure XML + pyproj + shapely — no fiona required.
    Fallback: rectangular mask clipped to sea boundary constants.
    """
    flat = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    # ── Primary: site_boundary.kml via pure XML + pyproj + shapely ───────────
    kml_path = DATA_DIR / "site_boundary.kml"
    if kml_path.exists():
        try:
            import xml.etree.ElementTree as _ET
            from pyproj import Transformer as _Tr
            from shapely.geometry import Polygon as _Poly, MultiPolygon as _MPoly
            from matplotlib.path import Path as _MplPath

            _ns  = "http://www.opengis.net/kml/2.2"
            _tr  = _Tr.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
            tree = _ET.parse(str(kml_path))
            root = tree.getroot()

            polys = []
            for pm in root.iter(f"{{{_ns}}}Placemark"):
                for ring_tag in [f"{{{_ns}}}outerBoundaryIs",
                                  f"{{{_ns}}}LinearRing"]:
                    for ring in pm.iter(ring_tag):
                        cel = ring.find(f".//{{{_ns}}}coordinates")
                        if cel is None or not cel.text:
                            continue
                        pts = []
                        for tok in cel.text.strip().split():
                            parts = tok.split(",")
                            if len(parts) >= 2:
                                try:
                                    lon, lat = float(parts[0]), float(parts[1])
                                    e, n = _tr.transform(lon, lat)
                                    pts.append((e, n))
                                except Exception:
                                    continue
                        if len(pts) >= 4:
                            polys.append(_Poly(pts))

            if polys:
                # Use the largest polygon as the site boundary
                site_poly = max(polys, key=lambda p: p.area)
                coords = list(site_poly.exterior.coords)
                path = _MplPath([(c[0], c[1]) for c in coords])
                inside = path.contains_points(flat)
                return inside.reshape(grid_x.shape)
        except Exception as e:
            import warnings
            warnings.warn(f"site_boundary.kml mask failed ({e}) — "
                          "falling back to rectangular mask.")

    # ── Fallback: rectangular sea-boundary mask ───────────────────────────────
    mask = np.ones(grid_x.shape, dtype=bool)
    mask[grid_y < SEA_SOUTH_N] = False
    mask[grid_x > SEA_EAST_E]  = False
    mask[grid_x < SEA_WEST_E]  = False
    return mask


def _fill_and_mask(surf, gx, gy, df_pts, values):
    """
    Fill NaN gaps in IDW surface (outside convex hull of data points)
    using nearest-neighbour extrapolation, then apply site boundary mask.
    This allows the surface to extend to the full dune system boundary
    rather than being clipped to the convex hull of the well network.
    """
    from scipy.interpolate import griddata as _gd
    filled = surf.copy().astype(float)
    nan_mask = np.isnan(filled)
    if nan_mask.any():
        # Fill with nearest-neighbour where linear interpolation gives NaN
        pts = np.column_stack([df_pts["E"].values, df_pts["N"].values])
        nearest = _gd(pts, values, (gx, gy), method="nearest")
        filled[nan_mask] = nearest[nan_mask]
    # Apply site boundary mask
    site_mask = _make_site_mask(gx, gy)
    filled[~site_mask] = np.nan
    return filled


def _apply_sea_mask(surf, gx, gy):
    """Apply site boundary mask to interpolated surface (no extrapolation)."""
    mask = _make_site_mask(gx, gy)
    masked = surf.copy().astype(float)
    masked[~mask] = np.nan
    return masked


def _norm(s: str) -> str:
    return str(s).lower().replace(" ", "")


def _winter_maxima(series: pd.Series) -> dict:
    """Return {hydro_year: Oct-Mar maximum maOD} for a maOD time series."""
    out = {}
    for yr in series.index.year.unique():
        # Hydrological year: Oct yr-1 to Mar yr
        sub = series[
            ((series.index.year == yr - 1) & series.index.month.isin([10, 11, 12])) |
            ((series.index.year == yr) & series.index.month.isin([1, 2, 3]))
        ].dropna()
        if len(sub) >= 3:
            out[yr] = sub.max()
    return out


def _flood_frequency(series: pd.Series, dem: float) -> float:
    """Return fraction of hydrological years where winter max reached ground surface."""
    maxima = _winter_maxima(series)
    if len(maxima) < 5:
        return np.nan
    flooded = sum(1 for v in maxima.values() if v >= dem)
    return flooded / len(maxima) * 100


def _summer_mins(series: pd.Series, start_yr: int = None) -> dict:
    """Return {year: Aug-Sep minimum} for a maOD time series."""
    out = {}
    for yr in series.index.year.unique():
        if start_yr and yr < start_yr:
            continue
        sub = series[
            (series.index.year == yr) & series.index.month.isin([8, 9])
        ].dropna()
        if len(sub) >= 1:
            out[yr] = sub.min()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
def load_well_data() -> pd.DataFrame:
    """
    Load reference and extended well data, compute mean summer minima, and
    return a combined DataFrame with depth-below-ground for each well.

    Returns
    -------
    DataFrame with columns:
        well, E, N, cluster, dem, depth_bg, scraped, network
    """
    maod_ref = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    ext_raw  = pd.read_csv(INT_WELLS_EXTENDED,   index_col=0, parse_dates=True)
    md       = pd.read_csv(INT_MASTER_DATA)
    site     = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE)
    locs     = pd.read_csv(INT_LOCATIONS)
    elev     = pd.read_csv(INT_WELL_ELEVATIONS)

    ext_cls = {
        _norm(r["Well_Normalised"]): int(r["Best_Match_Cluster"])
        for _, r in site[site["Network"] == "Extended"].iterrows()
    }

    # ── Reference wells ───────────────────────────────────────────────────
    ref_rows = []
    for _, mrow in md.iterrows():
        well = mrow["Name_Original"]
        wn   = _norm(well)
        col  = next((c for c in maod_ref.columns if _norm(c) == wn), None)
        if col is None:
            continue
        lrow = locs[locs["Match_ID"].apply(_norm) == wn]
        erow = elev[elev["Name_norm"].apply(_norm) == wn]
        if lrow.empty or erow.empty:
            continue
        dem_e = erow.iloc[0]["DEM_Ground_Elev"]
        if np.isnan(dem_e):
            continue

        if wn in SCRAPED:
            corr    = SCRAPED[wn]
            mins    = _summer_mins(maod_ref[col], start_yr=corr["start_yr"])
            adj_dem = dem_e - corr["dem_correction"]
        else:
            mins    = _summer_mins(maod_ref[col])
            adj_dem = dem_e

        if len(mins) < 2:
            continue
        mean_sm = np.nanmean(list(mins.values()))
        if np.isnan(mean_sm):
            continue

        ref_rows.append({
            "well":     well,
            "E":        lrow.iloc[0]["E"],
            "N":        lrow.iloc[0]["N"],
            "cluster":  int(mrow["Cluster"]),
            "dem":      adj_dem,
            "depth_bg": adj_dem - mean_sm,
            "scraped":  wn in SCRAPED,
            "network":  "Reference",
        })

    # ── Extended wells ────────────────────────────────────────────────────
    ext_rows = []
    for wn, cl in ext_cls.items():
        col = next((c for c in ext_raw.columns if _norm(c) == wn), None)
        if col is None:
            continue
        lrow = locs[locs["Name"].apply(_norm) == wn]
        erow = elev[elev["Name_norm"].apply(_norm) == wn]
        if lrow.empty or erow.empty:
            continue
        dem_e    = erow.iloc[0]["DEM_Ground_Elev"]
        pipe_top = erow.iloc[0]["Pipe_Top_Elev"]
        if np.isnan(dem_e) or np.isnan(pipe_top):
            continue

        # Extended raw depths are negative (below pipe) → maOD = pipe_top + raw
        maod   = pipe_top + ext_raw[col].dropna()
        mins   = _summer_mins(maod)
        if len(mins) < 2:
            continue
        mean_sm = np.nanmean(list(mins.values()))
        if np.isnan(mean_sm):
            continue

        ext_rows.append({
            "well":     wn,
            "E":        lrow.iloc[0]["E"],
            "N":        lrow.iloc[0]["N"],
            "cluster":  cl,
            "dem":      dem_e,
            "depth_bg": dem_e - mean_sm,
            "scraped":  False,
            "network":  "Extended",
        })

    df = pd.concat(
        [pd.DataFrame(ref_rows), pd.DataFrame(ext_rows)],
        ignore_index=True,
    ).dropna(subset=["depth_bg", "dem"])

    print(
        f"  Wells loaded: {len(df)} total  "
        f"(Reference: {(df['network']=='Reference').sum()}, "
        f"Extended: {(df['network']=='Extended').sum()})"
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE
# ─────────────────────────────────────────────────────────────────────────────
def plot_summer_minima_map(df: pd.DataFrame, dpi: int = 300) -> None:
    """
    Generate the summer minima depth map and save to OUT_11B_SUMMER_MAP.
    """
    DIR_11B.mkdir(parents=True, exist_ok=True)

    above_sd15b = df[df["depth_bg"] < SD15b]["well"].tolist()
    scraped_wells = df[df["scraped"]]["well"].tolist()

    n_tot   = len(df)
    n_wet   = (df["depth_bg"] < SD15b).sum()
    n_sr15b = ((df["depth_bg"] >= SD15b)     & (df["depth_bg"] < SD15b_REC)).sum()
    n_marg  = ((df["depth_bg"] >= SD15b_REC) & (df["depth_bg"] < SD16)).sum()
    n_sr16  = ((df["depth_bg"] >= SD16)      & (df["depth_bg"] < SD16_REC)).sum()
    n_crit  = (df["depth_bg"] >= SD16_REC).sum()

    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")

    # ── 1. Hillshade base ─────────────────────────────────────────────────
    _, ok, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1
    )
    if not ok:
        print("  [WARNING] DEM hillshade unavailable — map may lack context.")

    # ── 2. IDW depth surface with ridge masking ───────────────────────────
    cmap_z = LinearSegmentedColormap.from_list("slack", ZONE_COLOURS, N=256)
    norm_z = BoundaryNorm(ZONE_BOUNDS, ncolors=256)

    mesh, gx, gy, surf_depth = add_idw_surface(
        ax, df,
        value_col="depth_bg",
        dem_col="dem",
        ridge_mask_threshold=1.0,
        dem_e_arr=dem_e_arr,
        dem_n_arr=dem_n_arr,
        dem_data=dem_data,
        cmap=cmap_z,
        norm=norm_z,
        alpha=0.68,
        zorder=2,
    )

    # ── 3. Colourbar ──────────────────────────────────────────────────────
    cb = fig.colorbar(
        mesh, ax=ax, fraction=0.03, pad=0.02, shrink=0.85,
        boundaries=ZONE_BOUNDS,
        ticks=[0, SD15b, SD15b_REC, SD16, SD16_REC, 3.0],
    )
    cb.set_label("Mean summer minimum depth below ground (m)", fontsize=9)
    cb.ax.set_yticklabels([
        "0 m\n(flooding)",
        f"{SD15b} m\nSD15b\nwet slack",
        f"{SD15b_REC} m\nSD15b\nexcavation\nlimit",
        f"{SD16} m\nSD16\ndry slack",
        f"{SD16_REC} m\nSD16\nexcavation\nlimit",
        "3.0 m",
    ], fontsize=7.5)

    # ── 4. Threshold contours ─────────────────────────────────────────────
    for level, col, lw, ls in [
        (SD15b,    "#005fa3", 2.0, "--"),
        (SD15b_REC,"#2e8b2e", 1.8, ":"),
        (SD16,     "#a30000", 2.0, "--"),
        (SD16_REC, "#4a0000", 1.8, "-."),
    ]:
        try:
            ax.contour(gx, gy, surf_depth, levels=[level],
                       colors=[col], linewidths=lw,
                       linestyles=ls, alpha=0.80, zorder=3)
        except Exception:
            pass

    # ── 5. KML feature overlays (zorder=4, below wells and legends) ───────
    kml_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

    # ── 6. Well symbols ───────────────────────────────────────────────────
    for cl, grp in df.groupby("cluster"):
        col_c = CLUSTER_COLS.get(cl, "grey")
        for net, mk, sz in [("Reference", "o", 32), ("Extended", "D", 28)]:
            sub = grp[
                (grp["network"] == net) & (~grp["well"].isin(above_sd15b))
            ]
            scraped_sub = sub[sub["scraped"]]
            rest        = sub[~sub["scraped"]]

            if not rest.empty:
                ax.scatter(rest["E"], rest["N"], c=col_c,
                           s=sz, marker=mk, edgecolors="black",
                           lw=0.5, zorder=5)

            # Scraped wells — red-border square, labelled
            if not scraped_sub.empty:
                ax.scatter(scraped_sub["E"], scraped_sub["N"], c=col_c,
                           s=80, marker="s", edgecolors="red",
                           lw=1.5, zorder=6)
                for _, row in scraped_sub.iterrows():
                    ax.annotate(
                        row["well"].upper() + "\n(scraped 2023)",
                        xy=(row["E"], row["N"]),
                        xytext=(6, 4), textcoords="offset points",
                        fontsize=6.5, color="red",
                        fontweight="bold", zorder=6,
                    )

        # Star symbol for wells above SD15b threshold
        star = grp[grp["well"].isin(above_sd15b)]
        if not star.empty:
            ax.scatter(star["E"], star["N"], c=col_c,
                       s=180, marker="*", edgecolors="black",
                       lw=0.8, zorder=6)
            for _, row in star.iterrows():
                ax.annotate(
                    row["well"].upper(),
                    xy=(row["E"], row["N"]),
                    xytext=(6, 6), textcoords="offset points",
                    fontsize=7, fontweight="bold", zorder=6,
                )

    # ── 7. Stats box — top right ──────────────────────────────────────────
    stats_txt = (
        f"Above SD15b — wet slack viable:              {n_wet}/{n_tot} "
        f"({100*n_wet/n_tot:.0f}%)\n"
        f"SD15b–0.75 m — shallow excavation viable:   {n_sr15b}/{n_tot} "
        f"({100*n_sr15b/n_tot:.0f}%)\n"
        f"0.75–SD16 m  — SD16 dry slack:               {n_marg}/{n_tot} "
        f"({100*n_marg/n_tot:.0f}%)\n"
        f"SD16–1.20 m  — deeper excavation viable:     {n_sr16}/{n_tot} "
        f"({100*n_sr16/n_tot:.0f}%)\n"
        f"Beyond 1.20 m — critical (single scraping):  {n_crit}/{n_tot} "
        f"({100*n_crit/n_tot:.0f}%)\n"
        f"Ref: {(df['network']=='Reference').sum()}  "
        f"Extended: {(df['network']=='Extended').sum()}  "
        f"Total: {n_tot}\n"
        f"CEH21: DEM −0.70 m  |  CEH18: DEM −0.50 m  (both post-2023 only)"
    )
    ax.text(
        0.98, 0.97, stats_txt,
        transform=ax.transAxes, fontsize=7,
        verticalalignment="top", horizontalalignment="right",
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.92),
        zorder=7,
    )

    # ── 8. Legends ────────────────────────────────────────────────────────
    zone_handles = [
        mpatches.Patch(facecolor="#1a7abf", alpha=0.8,
                       label=f"Wet slack — viable (< {SD15b} m)"),
        mpatches.Patch(facecolor="#a8d8a8", alpha=0.8,
                       label=f"Shallow excavation viable — SD15b recoverable ({SD15b}–{SD15b_REC} m)"),
        mpatches.Patch(facecolor="#ffffb2", alpha=0.8,
                       label=f"SD16 dry slack — between excavation limits ({SD15b_REC}–{SD16} m)"),
        mpatches.Patch(facecolor="#fd8d3c", alpha=0.8,
                       label=f"Deeper excavation viable — SD16 recoverable ({SD16}–{SD16_REC} m)"),
        mpatches.Patch(facecolor="#bd0026", alpha=0.8,
                       label=f"Critical — beyond standard single scraping event (> {SD16_REC} m)"),
        Line2D([0], [0], color="#005fa3", lw=2.0, ls="--",
               label=f"SD15b wet slack threshold ({SD15b} m)"),
        Line2D([0], [0], color="#2e8b2e", lw=1.8, ls=":",
               label=f"SD15b excavation limit ~0.14 m depth ({SD15b_REC} m)"),
        Line2D([0], [0], color="#a30000", lw=2.0, ls="--",
               label=f"SD16 dry slack threshold ({SD16} m)"),
        Line2D([0], [0], color="#4a0000", lw=1.8, ls="-.",
               label=f"SD16 excavation limit ~0.22 m depth ({SD16_REC} m)"),
        Line2D([0], [0], marker="*", color="w",
               markerfacecolor="grey", markeredgecolor="black",
               markersize=12, label="Above SD15b on average (★ labelled)"),
        Line2D([0], [0], marker="o", color="w",
               markerfacecolor="grey", markeredgecolor="black",
               markersize=8, label="Reference well"),
        Line2D([0], [0], marker="D", color="w",
               markerfacecolor="grey", markeredgecolor="black",
               markersize=7, label="Extended well"),
        Line2D([0], [0], marker="s", color="w",
               markerfacecolor="grey", markeredgecolor="red",
               markersize=8,
               label="Scraped well — DEM corrected, post-2023 data"),
    ] + kml_handles  # KML feature entries appended at bottom

    cluster_patches = [
        mpatches.Patch(color=v, label=f"C{k}")
        for k, v in CLUSTER_COLS.items()
    ]

    # Zone legend — upper left
    l1 = ax.legend(
        handles=zone_handles, fontsize=7, loc="upper left",
        framealpha=0.95,
        title="Ecological zone / threshold / symbol",
        title_fontsize=8,
    )
    ax.add_artist(l1)

    # Cluster legend — lower right
    ax.legend(
        handles=cluster_patches, fontsize=8, loc="lower right",
        title="Cluster", title_fontsize=8,
    )

    # ── 9. Axes formatting ────────────────────────────────────────────────
    ax.set_xlim(240100, 243900)
    ax.set_ylim(362200, 365800)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(
        "Mean Annual Summer Minimum — Depth Below Ground (m)\n"
        "Newborough Warren 2005–2026  |  "
        "Full network (68 reference + 19 extended)  |  "
        "Dune ridges masked\n"
        "CEH18: DEM −0.50 m  |  CEH21: DEM −0.70 m  "
        "(both post-2023 data only)  |  "
        "Curreli et al. (2013) thresholds  |  "
        "Recovery limits: Hollingham (2026)",
        fontsize=9, fontweight="bold",
    )

    fig.tight_layout()
    fig.savefig(OUT_11B_SUMMER_MAP, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_11B_SUMMER_MAP}")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2 — WINTER MAXIMA DEPTH MAP
# ─────────────────────────────────────────────────────────────────────────────
def plot_winter_maxima_map(df: pd.DataFrame, dpi: int = 300) -> None:
    """Mean annual winter maximum depth below ground surface."""
    DIR_11B.mkdir(parents=True, exist_ok=True)

    # Load full maOD record for winter maxima
    maod_ref = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    ext_raw  = pd.read_csv(INT_WELLS_EXTENDED,   index_col=0, parse_dates=True)
    elev     = pd.read_csv(INT_WELL_ELEVATIONS)

    winter_rows = []
    for _, row in df.iterrows():
        wn = _norm(row["well"])
        dem = row["dem"]

        # Get maOD series
        col_ref = next((c for c in maod_ref.columns if _norm(c) == wn), None)
        if col_ref is not None:
            series = maod_ref[col_ref].dropna()
        else:
            col_ext = next((c for c in ext_raw.columns if _norm(c) == wn), None)
            if col_ext is None:
                continue
            erow = elev[elev["Name_norm"].apply(_norm) == wn]
            if erow.empty:
                continue
            pipe_top = erow.iloc[0]["Pipe_Top_Elev"]
            series = pipe_top + ext_raw[col_ext].dropna()

        maxima = _winter_maxima(series)
        if len(maxima) < 3:
            continue
        mean_wmax = np.nanmean(list(maxima.values()))
        winter_rows.append({
            "E": row["E"], "N": row["N"],
            "cluster": row["cluster"], "network": row["network"],
            "dem": dem,
            "depth_bg": dem - mean_wmax,   # +ve = below surface, -ve = flooding
        })

    if not winter_rows:
        print("  [WARNING] No winter maxima data available")
        return

    wdf = pd.DataFrame(winter_rows)

    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")
    _, ok, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    # Diverging colormap: blue = flooding/near surface, red = deep
    cmap = plt.cm.RdBu_r
    vmin, vmax = -0.25, 1.5
    sc, gx, gy, surf = add_idw_surface(ax, wdf, value_col="depth_bg",
                         easting_col="E", northing_col="N",
                         dem_col="dem",
                         ridge_mask_threshold=1.0,
                         dem_e_arr=dem_e_arr if ok else None,
                         dem_n_arr=dem_n_arr if ok else None,
                         dem_data=dem_data if ok else None,
                         cmap=cmap, vmin=vmin, vmax=vmax,
                         alpha=0.72, zorder=2)
    surf = _fill_and_mask(surf, gx, gy, wdf, wdf["depth_bg"].values)

    # Ecological threshold contours using returned interpolated surface
    WINTER_THRESHOLDS = [
        (0.00, "#1A237E", "-",  2.0, "Flooding (WT at surface, 0 m)"),
        (0.10, "#1565C0", "--", 1.5, "SD15b winter requirement (0.10 m)"),
        (0.25, "#CC0000", "--", 1.5, "SD16 winter requirement (0.25 m)"),
    ]
    for level, col, ls, lw, lbl in WINTER_THRESHOLDS:
        try:
            cs = ax.contour(gx, gy, surf, levels=[level], colors=[col],
                            linestyles=[ls], linewidths=[lw], zorder=5)
            ax.clabel(cs, fmt=f"{level:.2f} m", fontsize=7, inline=True)
        except Exception:
            pass

    # Well symbols
    for _, row in wdf.iterrows():
        mk = "o" if row["network"] == "Reference" else "D"
        ax.scatter(row["E"], row["N"], c=CLUSTER_COLS.get(row["cluster"], "#999"),
                   s=28, marker=mk, zorder=7, linewidths=0.4, edgecolors="white")

    kml_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

    cbar = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02, shrink=0.85)
    cbar.set_label("Mean winter maximum depth below ground (m)\n+ve = below surface, \u2212ve = flooding",
                   fontsize=8)

    # Legend
    legend_patches = [
        mpatches.Patch(color=col, label=lbl)
        for _, col, _, _, lbl in WINTER_THRESHOLDS
    ] + [
        Line2D([0],[0], marker="o", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Extended well"),
    ] + [Line2D([0],[0], marker="o", color="w",
                markerfacecolor=CLUSTER_COLS[c], ms=7, label=f"C{c}")
         for c in sorted(CLUSTER_COLS)]
    ax.legend(handles=legend_patches + kml_handles, fontsize=7,
              loc="upper left", framealpha=0.95, ncol=2)

    ax.set_xlabel("Easting (m, OSGB36)"); ax.set_ylabel("Northing (m, OSGB36)")
    ax.set_title(
        "Mean Annual Winter Maximum — Depth Below Ground (m)\n"
        "Newborough Warren 2005–2026  |  Full network  |  "
        "Dune ridges masked  |  Curreli et al. (2013) winter thresholds",
        fontsize=10, fontweight="bold")
    ax.set_xlim(240100, 243900)
    ax.set_ylim(362100, 365900)
    plt.tight_layout()
    fig.savefig(OUT_11B_WINTER_MAP, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_11B_WINTER_MAP.name}")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 3 — P_FLOOD MAP
# ─────────────────────────────────────────────────────────────────────────────
def plot_pflood_map(df: pd.DataFrame, dpi: int = 300) -> None:
    """P_flood = minimum winter rainfall to reach slack floor from mean summer minimum."""
    DIR_11B.mkdir(parents=True, exist_ok=True)

    md = pd.read_csv(INT_MASTER_DATA)
    beta_lookup = {
        _norm(r["Name_Original"]): {
            "b1": r["beta_1_recharge"],
            "b3": r["beta_3_internal_brake"],
            "cluster": int(r["Cluster"]),
        }
        for _, r in md.iterrows()
    }

    # Cluster-level fallbacks
    cluster_betas = {}
    for cl in [1, 2, 3, 4]:
        sub = md[md["Cluster"] == cl]
        cluster_betas[cl] = {
            "b1": sub["beta_1_recharge"].median(),
            "b3": sub["beta_3_internal_brake"].median(),
        }

    pf_rows = []
    for _, row in df.iterrows():
        wn = _norm(row["well"])
        h_gap = row["depth_bg"]   # mean summer minimum depth below ground
        if np.isnan(h_gap) or h_gap <= 0:
            continue
        betas = beta_lookup.get(wn, None)
        if betas is None:
            betas = cluster_betas.get(row["cluster"], None)
        if betas is None:
            continue
        b1 = betas["b1"]
        b3 = betas["b3"]
        if b1 <= 0:
            continue
        # P_flood = (h_gap + b3 * h_prev) / b1
        # h_prev = h_gap (antecedent = mean summer minimum)
        # Units: b1 in m/mm, h_gap in m → P_flood in mm
        h_prev = h_gap
        pflood = (h_gap + b3 * h_prev) / b1
        pf_rows.append({
            "E": row["E"], "N": row["N"],
            "cluster": row["cluster"], "network": row["network"],
            "dem": row["dem"],
            "pflood": pflood,
            "exceeds_mean": pflood > MEAN_WINTER_RAINFALL_MM,
        })

    if not pf_rows:
        print("  [WARNING] No P_flood data computed")
        return

    pf = pd.DataFrame(pf_rows)

    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")
    _, ok, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    cmap = LinearSegmentedColormap.from_list(
        "pflood", ["#fff5eb", "#fdae6b", "#e6550d", "#a63603", "#67000d"])
    # Scale to data — cap at 2x mean winter rainfall to show structure
    vmin = 0
    vmax = min(pf["pflood"].quantile(0.95), MEAN_WINTER_RAINFALL_MM * 3)
    sc, gx, gy, surf = add_idw_surface(ax, pf, value_col="pflood",
                         easting_col="E", northing_col="N",
                         dem_col="dem",
                         ridge_mask_threshold=1.0,
                         dem_e_arr=dem_e_arr if ok else None,
                         dem_n_arr=dem_n_arr if ok else None,
                         dem_data=dem_data if ok else None,
                         cmap=cmap, vmin=vmin, vmax=vmax,
                         alpha=0.72, zorder=2)
    surf = _fill_and_mask(surf, gx, gy, pf, pf["pflood"].values)

    # Red outline for wells exceeding mean winter rainfall
    for _, row in pf[pf["exceeds_mean"]].iterrows():
        ax.scatter(row["E"], row["N"], c="none", s=55,
                   marker="o" if row["network"] == "Reference" else "D",
                   edgecolors="red", linewidths=1.5, zorder=8)

    # All well symbols
    for _, row in pf.iterrows():
        mk = "o" if row["network"] == "Reference" else "D"
        ax.scatter(row["E"], row["N"], c=CLUSTER_COLS.get(row["cluster"], "#999"),
                   s=28, marker=mk, zorder=7, linewidths=0.4, edgecolors="white")

    kml_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

    cbar = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02, shrink=0.85)
    cbar.ax.axhline(MEAN_WINTER_RAINFALL_MM, color="red", lw=1.5, ls="--")
    cbar.set_label("P_flood — minimum winter rainfall to reach slack floor (mm)", fontsize=8)

    legend_patches = [
        mpatches.Patch(facecolor="#fdae6b", label="Low P_flood — floods readily"),
        mpatches.Patch(facecolor="#a63603", label="High P_flood — rarely floods"),
        Line2D([0],[0], marker="o", color="w", markerfacecolor="none",
               markeredgecolor="red", ms=8, mew=1.5,
               label=f"P_flood > {MEAN_WINTER_RAINFALL_MM} mm (structurally unable to flood)"),
        Line2D([0],[0], marker="o", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Extended well"),
    ] + [Line2D([0],[0], marker="o", color="w",
                markerfacecolor=CLUSTER_COLS[c], ms=7, label=f"C{c}")
         for c in sorted(CLUSTER_COLS)]
    ax.legend(handles=legend_patches + kml_handles, fontsize=7,
              loc="upper left", framealpha=0.95, ncol=2)

    ax.set_xlabel("Easting (m, OSGB36)"); ax.set_ylabel("Northing (m, OSGB36)")
    ax.set_title(
        f"P_flood — Minimum Winter Rainfall to Reach Slack Floor (mm)\n"
        f"Newborough Warren  |  Mean summer minimum antecedent condition  |  "
        f"Dune ridges masked  |  "
        f"Red outline: P_flood > {MEAN_WINTER_RAINFALL_MM} mm (mean annual winter rainfall)",
        fontsize=10, fontweight="bold")
    ax.set_xlim(240100, 243900)
    ax.set_ylim(362100, 365900)
    plt.tight_layout()
    fig.savefig(OUT_11B_PFLOOD_MAP, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_11B_PFLOOD_MAP.name}")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 4 — FLOOD FREQUENCY MAP
# ─────────────────────────────────────────────────────────────────────────────
def plot_flood_frequency_map(df: pd.DataFrame, dpi: int = 300) -> None:
    """Percentage of hydrological years where winter max reached ground surface."""
    DIR_11B.mkdir(parents=True, exist_ok=True)

    maod_ref = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    ext_raw  = pd.read_csv(INT_WELLS_EXTENDED,   index_col=0, parse_dates=True)
    elev     = pd.read_csv(INT_WELL_ELEVATIONS)

    ff_rows = []
    for _, row in df.iterrows():
        wn = _norm(row["well"])
        dem = row["dem"]

        col_ref = next((c for c in maod_ref.columns if _norm(c) == wn), None)
        if col_ref is not None:
            series = maod_ref[col_ref].dropna()
        else:
            col_ext = next((c for c in ext_raw.columns if _norm(c) == wn), None)
            if col_ext is None:
                continue
            erow = elev[elev["Name_norm"].apply(_norm) == wn]
            if erow.empty:
                continue
            pipe_top = erow.iloc[0]["Pipe_Top_Elev"]
            series = pipe_top + ext_raw[col_ext].dropna()

        freq = _flood_frequency(series, dem)
        if np.isnan(freq):
            continue
        ff_rows.append({
            "E": row["E"], "N": row["N"],
            "cluster": row["cluster"], "network": row["network"],
            "dem": row["dem"],
            "freq": freq,
        })

    if not ff_rows:
        print("  [WARNING] No flood frequency data computed")
        return

    ff = pd.DataFrame(ff_rows)

    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")
    _, ok, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    # Red (never floods) → white (50%) → blue (frequently floods)
    cmap = LinearSegmentedColormap.from_list(
        "floodfreq", ["#67001f", "#d73027", "#f4a582", "#f7f7f7",
                      "#92c5de", "#2166ac", "#053061"])
    sc, gx, gy, surf = add_idw_surface(ax, ff, value_col="freq",
                         easting_col="E", northing_col="N",
                         dem_col="dem",
                         ridge_mask_threshold=1.0,
                         dem_e_arr=dem_e_arr if ok else None,
                         dem_n_arr=dem_n_arr if ok else None,
                         dem_data=dem_data if ok else None,
                         cmap=cmap, vmin=0, vmax=100,
                         alpha=0.72, zorder=2)
    surf = _fill_and_mask(surf, gx, gy, ff, ff["freq"].values)

    # Frequency contours using returned interpolated surface
    for level, col, ls, lbl in [
        (25,  "#f0e442", "--", "25% frequency contour"),
        (50,  "#009e73", "--", "50% frequency contour"),
    ]:
        try:
            cs = ax.contour(gx, gy, surf, levels=[level], colors=[col],
                            linestyles=[ls], linewidths=[1.5], zorder=5)
            ax.clabel(cs, fmt=f"{level}%", fontsize=7, inline=True)
        except Exception:
            pass

    for _, row in ff.iterrows():
        mk = "o" if row["network"] == "Reference" else "D"
        ax.scatter(row["E"], row["N"], c=CLUSTER_COLS.get(row["cluster"], "#999"),
                   s=28, marker=mk, zorder=7, linewidths=0.4, edgecolors="white")

    kml_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

    cbar = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02, shrink=0.85)
    cbar.set_label("Winter flooding frequency (%)\nYears water table reached ground surface",
                   fontsize=8)

    legend_patches = [
        mpatches.Patch(facecolor="#67001f", label="Never floods (0%)"),
        mpatches.Patch(facecolor="#f7f7f7", edgecolor="#aaa", label="Occasionally floods (~50%)"),
        mpatches.Patch(facecolor="#053061", label="Frequently floods (>75%)"),
        Line2D([0],[0], color="#f0e442", lw=1.5, ls="--", label="25% frequency contour"),
        Line2D([0],[0], color="#009e73", lw=1.5, ls="--", label="50% frequency contour"),
        Line2D([0],[0], marker="o", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Extended well"),
    ] + [Line2D([0],[0], marker="o", color="w",
                markerfacecolor=CLUSTER_COLS[c], ms=7, label=f"C{c}")
         for c in sorted(CLUSTER_COLS)]
    ax.legend(handles=legend_patches + kml_handles, fontsize=7,
              loc="upper left", framealpha=0.95, ncol=2)

    ax.set_xlabel("Easting (m, OSGB36)"); ax.set_ylabel("Northing (m, OSGB36)")
    ax.set_title(
        "Winter Flooding Frequency (%) — Newborough Warren 2005–2026\n"
        "Years water table reached ground surface  |  Full network  |  "
        "Dune ridges masked  |  Curreli et al. (2013): SD15b requires annual flooding",
        fontsize=10, fontweight="bold")
    ax.set_xlim(240100, 243900)
    ax.set_ylim(362100, 365900)
    plt.tight_layout()
    fig.savefig(OUT_11B_FLOOD_FREQ, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_11B_FLOOD_FREQ.name}")

def main(preview: bool = False) -> None:
    dpi = 150 if preview else 300
    print("\n=== 11b_spatial_thresholds.py ===")
    print("Loading well data...")
    df = load_well_data()
    print("Generating summer minima depth map...")
    plot_summer_minima_map(df, dpi=dpi)
    print("Generating winter maxima depth map...")
    plot_winter_maxima_map(df, dpi=dpi)
    print("Generating P_flood map...")
    plot_pflood_map(df, dpi=dpi)
    print("Generating flood frequency map...")
    plot_flood_frequency_map(df, dpi=dpi)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Spatial eco-hydrological threshold maps — Newborough Warren"
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Render at 150 dpi for quick preview (default: 300 dpi)",
    )
    args = parser.parse_args()
    main(preview=args.preview)
