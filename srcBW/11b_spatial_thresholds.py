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

P_FLOOD MAP (plot_pflood_map) — Section 3.6.3 of Hollingham (2026)
------------------------------------------------------------------
Revised 2026-04: iterated closed-form P_flood supersedes the earlier
single-step inversion. For each well:
    - cluster-level \u03b2 coefficients are taken from
      03_03_cluster_mechanistic_coefficients.csv (hybrid architecture per
      Section 3.6.3: cluster-\u03b2 provides dynamics, well-specific mean
      summer minimum provides spatial resolution);
    - the SSM is iterated from h_0 over a cluster-specific horizon
      (October to the cluster's historical peak month, loaded from
      03_cluster_peak_months.csv) with RAF Valley monthly PET and
      rainfall climatology;
    - closed-form solution for the rainfall multiplier \u03bb gives P_flood
      in mm directly comparable to the 521 mm mean annual winter total.

Wells whose cluster lacks an entry in CLUSTER_PEAK_MONTH or in the
mechanistic coefficients table are omitted from the P_flood map (the
check is data-driven, not hardcoded to specific cluster IDs).

Outputs
-------
    outputs/11b_spatial_thresholds/
        11b_01_summer_minima_depth.png   \u2014 main ecological status map
        11b_02_winter_maxima_depth.png   \u2014 winter peak depth map
        11b_03_pflood.png                \u2014 P_flood spatial map (iterated)
        11b_03_pflood_per_well.csv       \u2014 per-well P_flood CSV (new)
        11b_04_flood_frequency.png       \u2014 winter flooding frequency map

Inputs (all from pipeline outputs/ directory)
-----------------------------------------------
    01_wells_clean_maod.csv                    \u2014 reference network maOD time series
    01_wells_extended.csv                      \u2014 extended network raw depths
    01_well_elevations.csv                     \u2014 well DEM elevations (Pipe_Top_Elev)
    01_locations.csv                           \u2014 well coordinates
    03_master_data.csv                         \u2014 reference well cluster assignments
    03_03_cluster_mechanistic_coefficients.csv \u2014 cluster-level SSM \u03b2 coefficients
    03_regional_averages.csv                   \u2014 monthly P, PET and cluster means (for climatology)
    06_pear_membership_audit_sitewide.csv      \u2014 extended well cluster assignments
    data/Features.kml                          \u2014 site feature overlays

Called by
---------
    run_analysis.py  (or standalone: python 11b_spatial_thresholds.py)

Dependencies
------------
    Standard pipeline: numpy, pandas, matplotlib, scipy
    Spatial: rasterio (via map_utils), geopandas, fiona (via map_utils)
    Skeletonisation: not required (map_utils handles DEM/IDW)
"""

__version__ = "1.1.0"  # Hollingham (2026) — last revised 2026-04-23
#                        1.1.0: iterated P_flood (Section 3.6.3 revision)
#                        1.0.0: single-step P_flood (superseded)

import argparse
import json
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
    INT_WELLS_CLEAN_MAOD,
    INT_WELLS_EXTENDED,
    INT_WELL_ELEVATIONS,
    INT_PEAR_AUDIT_SITEWIDE,
    INT_REGIONAL_AVG,
    INT_CLUSTER_PEAK_MONTHS,
    OUT_03_MECHANISTIC_TABLE,
    OUT_11_TABLE8_THRESHOLDS,
    OUT_11_TABLE6_WINTER,
    OUT_11_TABLE7_SUMMER,
    DIR_11B,
    OUT_11B_SUMMER_MAP,
    OUT_11B_WINTER_MAP,
    OUT_11B_PFLOOD_MAP,
    OUT_11B_PFLOOD_PER_WELL,
    OUT_11B_FLOOD_FREQ,
    OUT_11B_TABLE10,
    OUT_11B_FORECASTER_HTML,
    SRC_FORECASTER_TEMPLATE,
)
from utils.map_utils import load_dem_hillshade, add_idw_surface, add_kml_features, _safe_read_kml
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS, DRAINAGE_DATUM, SD15b, SD15b_REC, SD16, SD16_REC
from utils.model_utils import pflood_lambda

# ─────────────────────────────────────────────────────────────────────────────
# LOCAL ALIASES
# The two constants below are readability aliases for paths.py entries whose
# names in paths.py don't match the names used throughout this script's
# plotting functions. Kept here rather than renamed in paths.py to avoid
# ripple-changes elsewhere in the pipeline.
# ─────────────────────────────────────────────────────────────────────────────
INT_CLUSTER_MECHANISTIC = OUT_03_MECHANISTIC_TABLE   # 03_03_cluster_mechanistic_coefficients.csv
INT_REGIONAL_AVERAGES   = INT_REGIONAL_AVG           # 03_regional_averages.csv

# Mean annual winter rainfall (Oct-Mar, monitoring period 2005-2026)
MEAN_WINTER_RAINFALL_MM = 521

# Sea boundary constants — rectangular fallback mask matching script 19
SEA_SOUTH_N = 362350   # m OSGB36 — southern shoreline
SEA_EAST_E  = 243850   # m OSGB36 — eastern Menai Strait
SEA_WEST_E  = 239200   # m OSGB36 — western estuary

# ─────────────────────────────────────────────────────────────────────────────
# ECOLOGICAL THRESHOLDS (Curreli et al., 2013)
# Imported from utils.config: SD15b, SD15b_REC, SD16, SD16_REC
# ─────────────────────────────────────────────────────────────────────────────

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
# Wells whose Best_Match_Cluster is a "nearest-cluster" pattern match, NOT a
# statement that the SSM model is valid for the well. These wells sit outside
# the SSM operational domain (tidal boundary, upstream-script exclusions etc.)
# but appear in the sitewide audit because their hydrograph happens to
# correlate with one of the canonical cluster centroids. They are still
# included in the forecaster — but flagged so the user knows the cluster
# label is "nearest type", not "core member".
#
# Provenance (carried over from Scripts 07 / 22):
#   ceh3, ceh4 — tidal boundary; outside SSM operational domain (report S4.4.2)
#   ceh7, ceh8 — upstream exclusions
#   ceh37     — same
# ─────────────────────────────────────────────────────────────────────────────
NEAREST_CLUSTER_ONLY_WELLS: set[str] = {"ceh3", "ceh4", "ceh7", "ceh8", "ceh37"}


# ─────────────────────────────────────────────────────────────────────────────
# P_FLOOD (iterated, Section 3.6.3 of Hollingham 2026) — CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
def _load_cluster_peak_months_int() -> dict[int, int]:
    """
    Load CLUSTER_PEAK_MONTH (integer cluster-id → peak month) from
    INT_CLUSTER_PEAK_MONTHS (written by Script 03's
    export_cluster_peak_months). 11b uses integer keys throughout, unlike 11
    which uses 'C{n}' string keys; both load from the same file.
    """
    if not INT_CLUSTER_PEAK_MONTHS.exists():
        raise FileNotFoundError(
            f"Cluster peak-months file not found:\n  {INT_CLUSTER_PEAK_MONTHS}\n"
            f"Run script 03 (state-space model) first — it produces this file "
            f"as part of its regional-averages exports."
        )
    df = pd.read_csv(INT_CLUSTER_PEAK_MONTHS)
    if not {"cluster_id", "peak_month"}.issubset(df.columns):
        raise RuntimeError(
            f"{INT_CLUSTER_PEAK_MONTHS.name} is missing expected columns "
            f"'cluster_id' and 'peak_month'. Re-run script 03 to regenerate."
        )
    return {int(row["cluster_id"]): int(row["peak_month"]) for _, row in df.iterrows()}


# Cluster-specific horizon: months from October to historical peak-of-record.
# Loaded from INT_CLUSTER_PEAK_MONTHS (script 03 output) so the values stay
# in sync with the partition.
CLUSTER_PEAK_MONTH = _load_cluster_peak_months_int()

# Slack-floor target (0 = ground surface = full flooding)
P_FLOOD_H_TARGET_M = 0.0

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

# Curreli WINTER thresholds (depth below ground at winter peak)
W_FLOOD   = 0.00   # m — water table at surface (flooding)
W_SD15b   = 0.10   # m — SD15b winter requirement
W_SD16    = 0.25   # m — SD16 winter requirement

# Winter Curreli zone colourmap (depth below ground at winter maximum)
WINTER_ZONE_COLOURS = [
    "#1A237E",  # Dark blue  — flooding (WT at or above surface, < 0 m)
    "#1565C0",  # Blue       — SD15b winter met (< 0.10 m)
    "#a8d8a8",  # Pale green — between SD15b and SD16 (0.10–0.25 m)
    "#fd8d3c",  # Orange     — below SD16 winter (> 0.25 m)
]
WINTER_ZONE_BOUNDS = [-.10, W_FLOOD, W_SD15b, W_SD16, 1.5]

# ─────────────────────────────────────────────────────────────────────────────
# CLUSTER COLOURS — imported from utils/config.py (single source of truth)
# ─────────────────────────────────────────────────────────────────────────────
CLUSTER_COLS = CLUSTER_COLOURS


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
        pts = np.column_stack([df_pts["E"].values, df_pts["N"].values])
        nearest = _gd(pts, values, (gx, gy), method="nearest")
        filled[nan_mask] = nearest[nan_mask]
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
# P_FLOOD HELPERS (iterated closed form — Section 3.6.3)
# ─────────────────────────────────────────────────────────────────────────────
def _horizon_months(peak_month: int) -> list:
    """Return [10, 11, ..., peak_month] as a sequence of calendar months."""
    months, m = [], 10
    for _ in range(12):
        months.append(m)
        if m == peak_month:
            return months
        m = (m % 12) + 1
    return months


def _load_cluster_coefficients() -> dict:
    """
    Load cluster-level \u03b2\u2081, \u03b2\u2082, \u03b2\u2083 from 03_03_cluster_mechanistic_coefficients.csv
    and convert to the unit convention used by 11b's downstream P_flood code:
    metres of head change per *millimetre* of forcing.

    Script 03 fits the SSM in m head per m forcing (rainfall and PET in
    m/month, head in m), so \u03b2\u2081 and \u03b2\u2082 in the CSV are dimensionless m/m.
    11b's _p_flood_iterated and _load_climatology work in mm rainfall (the
    P_mm / PET_mm columns of 03_regional_averages.csv), so we divide by
    1000 here to convert m/m -> m/mm. \u03b2\u2083 is the per-month drainage fraction
    (no unit conversion needed) and is stored negative in the CSV; the SSM
    applies \u03b1 = 1 - |\u03b2\u2083| so we take the absolute value.

    The Cluster column is read defensively because Script 03 writes integer
    cluster IDs while Script 11 writes 'C1'-style strings; this loader
    accepts either.
    """
    cc = pd.read_csv(INT_CLUSTER_MECHANISTIC)
    coeffs = {}
    for _, r in cc.iterrows():
        cluster_int = _coerce_cluster_int(r["Cluster"])
        if cluster_int is None:
            continue
        b3_val = float(r["beta_3_drainage"])
        if b3_val < 0:
            print(f"  [WARNING] Cluster {cluster_int}: β₃ = {b3_val:.4f} is negative "
                  f"(expected positive under displacement formulation)")
        coeffs[cluster_int] = {
            "b1": float(r["beta_1_recharge"]) / 1000.0,
            "b2": float(r["beta_2_atmospheric_draw"]) / 1000.0,
            "b3": abs(b3_val),
        }
    return coeffs


def _coerce_cluster_int(value) -> int | None:
    """
    Coerce a Cluster column entry to an integer cluster ID.

    Handles: integer (1..N), numpy integer, string '1', and 'C1'-style
    string. Returns None if the value cannot be parsed (e.g. NaN).
    """
    if pd.isna(value):
        return None
    # Integer or numpy integer
    if isinstance(value, (int,)) or (hasattr(value, "__int__") and not isinstance(value, str)):
        return int(value)
    s = str(value).strip()
    if not s:
        return None
    # 'C1'-style string -> 1
    if s[:1].upper() == "C" and s[1:].isdigit():
        return int(s[1:])
    # Plain digit string -> int
    if s.isdigit():
        return int(s)
    return None


def _load_climatology() -> tuple:
    """Return (P_clim, PET_clim) as dicts keyed by calendar month 1..12."""
    ra = pd.read_csv(INT_REGIONAL_AVERAGES, parse_dates=["Date"]).set_index("Date")
    P_clim   = ra.groupby(ra.index.month)["P_mm"].mean().to_dict()
    PET_clim = ra.groupby(ra.index.month)["PET_mm"].mean().to_dict()
    return P_clim, PET_clim


def _p_flood_iterated(
    h_target: float,
    h_0:      float,
    b1:       float,
    b2:       float,
    b3:       float,
    months:   list,
    P_clim:   dict,
    PET_clim: dict,
) -> dict:
    """Thin wrapper around model_utils.pflood_lambda for backward compatibility."""
    return pflood_lambda(
        h_target=h_target, h_0=h_0, b1=b1, b2=b2, b3=b3,
        months=months, P_clim=P_clim, PET_clim=PET_clim,
    )


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
            "cluster":  _coerce_cluster_int(mrow["Cluster"]),
            "dem":      adj_dem,
            "depth_bg": adj_dem - mean_sm,
            "scraped":  wn in SCRAPED,
            "network":  "Reference",
            # Per-well SSM coefficients from Script 03 (HEADLINE_LAG, m/m units).
            # Converted to m/mm (÷ 1000) at point of use by P_flood routines.
            "well_b1_mm":  float(mrow["beta_1_recharge"]),          # m/m
            "well_b2_mm":  float(mrow["beta_2_atmospheric_draw"]),  # m/m
            "well_b3":     float(mrow["beta_3_drainage"]),          # dimensionless
            "well_r2":     float(mrow["Model_R2"]),
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
            # No per-well SSM fit for extended wells (not in reference network)
            "well_b1_mm":  np.nan,
            "well_b2_mm":  np.nan,
            "well_b3":     np.nan,
            "well_r2":     np.nan,
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
# FIGURE 1 — SUMMER MINIMA DEPTH MAP
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

    _, ok, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1
    )
    if not ok:
        print("  [WARNING] DEM hillshade unavailable — map may lack context.")

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

    kml_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

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
               markersize=12, label="Above SD15b on average (\u2605 labelled)"),
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
    ] + kml_handles

    cluster_patches = [
        mpatches.Patch(color=CLUSTER_COLS[k], label=f"C{k}")
        for k in sorted(CLUSTER_LABELS)
    ]

    l1 = ax.legend(
        handles=zone_handles, fontsize=7, loc="upper left",
        framealpha=0.95,
        title="Ecological zone / threshold / symbol",
        title_fontsize=8,
    )
    ax.add_artist(l1)

    ax.legend(
        handles=cluster_patches, fontsize=8, loc="lower right",
        title="Cluster", title_fontsize=8,
    )

    ax.set_xlim(240100, 243900)
    ax.set_ylim(362200, 365800)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(
        "Mean Annual Summer Minimum — Depth Below Ground (m)\n"
        "Newborough Warren 2005–2026  |  "
        f"Full network ({(df['network']=='Reference').sum()} reference + "
        f"{(df['network']=='Extended').sum()} extended)  |  "
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
# FIGURE 2 — WINTER MAXIMA DEPTH MAP
# ─────────────────────────────────────────────────────────────────────────────
def plot_winter_maxima_map(df: pd.DataFrame, dpi: int = 300) -> None:
    """
    Mean annual winter maximum depth below ground surface, with Curreli
    et al. (2013) winter eco-hydrological threshold zones.

    Zones (depth below ground at winter peak):
      - Flooding:     < 0.00 m (WT at or above surface)
      - SD15b winter: < 0.10 m
      - SD16 winter:  < 0.25 m
      - Below SD16:   > 0.25 m
    """
    DIR_11B.mkdir(parents=True, exist_ok=True)

    maod_ref = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    ext_raw  = pd.read_csv(INT_WELLS_EXTENDED,   index_col=0, parse_dates=True)
    elev     = pd.read_csv(INT_WELL_ELEVATIONS)

    winter_rows = []
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

        maxima = _winter_maxima(series)
        if len(maxima) < 3:
            continue
        mean_wmax = np.nanmean(list(maxima.values()))
        depth_bg = dem - mean_wmax
        winter_rows.append({
            "well": row["well"],
            "E": row["E"], "N": row["N"],
            "cluster": row["cluster"], "network": row["network"],
            "dem": dem,
            "depth_bg": depth_bg,
        })

    if not winter_rows:
        print("  [WARNING] No winter maxima data available")
        return

    wdf = pd.DataFrame(winter_rows)

    # Zone summary counts
    n_flood = (wdf["depth_bg"] <= W_FLOOD).sum()
    n_sd15b = ((wdf["depth_bg"] > W_FLOOD) & (wdf["depth_bg"] <= W_SD15b)).sum()
    n_sd16  = ((wdf["depth_bg"] > W_SD15b) & (wdf["depth_bg"] <= W_SD16)).sum()
    n_below = (wdf["depth_bg"] > W_SD16).sum()

    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")
    _, ok, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    # Curreli zonal colourmap for winter thresholds
    cmap_w = LinearSegmentedColormap.from_list("winter_slack", WINTER_ZONE_COLOURS, N=256)
    norm_w = BoundaryNorm(WINTER_ZONE_BOUNDS, ncolors=256)

    mesh, gx, gy, surf = add_idw_surface(
        ax, wdf, value_col="depth_bg",
        easting_col="E", northing_col="N",
        dem_col="dem",
        ridge_mask_threshold=1.0,
        dem_e_arr=dem_e_arr if ok else None,
        dem_n_arr=dem_n_arr if ok else None,
        dem_data=dem_data if ok else None,
        cmap=cmap_w, norm=norm_w,
        alpha=0.72, zorder=2)
    surf = _fill_and_mask(surf, gx, gy, wdf, wdf["depth_bg"].values)

    # Threshold contour lines
    for level, col, lw, ls in [
        (W_FLOOD, "#1A237E", 2.0, "-"),
        (W_SD15b, "#1565C0", 1.8, "--"),
        (W_SD16,  "#CC0000", 1.8, "--"),
    ]:
        try:
            cs = ax.contour(gx, gy, surf, levels=[level],
                            colors=[col], linewidths=lw,
                            linestyles=ls, alpha=0.80, zorder=5)
            ax.clabel(cs, fmt=f"{level:.2f} m", fontsize=7, inline=True)
        except Exception:
            pass

    for _, row in wdf.iterrows():
        mk = "o" if row["network"] == "Reference" else "D"
        ax.scatter(row["E"], row["N"], c=CLUSTER_COLS.get(row["cluster"], "#999"),
                   s=28, marker=mk, zorder=7, linewidths=0.4, edgecolors="white")

    kml_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

    # Colourbar with Curreli zone labels — inverted so flooding (0 m) is at top
    cb = fig.colorbar(
        mesh, ax=ax, fraction=0.03, pad=0.02, shrink=0.85,
        boundaries=WINTER_ZONE_BOUNDS,
        ticks=[W_FLOOD, W_SD15b, W_SD16],
    )
    cb.ax.invert_yaxis()
    cb.set_label("Mean winter maximum depth below ground (m)", fontsize=9)
    cb.ax.set_yticklabels([
        f"{W_FLOOD:.2f} m\nFlooding",
        f"{W_SD15b:.2f} m\nSD15b\nwinter",
        f"{W_SD16:.2f} m\nSD16\nwinter",
    ], fontsize=7.5)

    # Legend
    legend_patches = [
        mpatches.Patch(color=WINTER_ZONE_COLOURS[0],
                       label=f"Flooding (WT at surface, n={n_flood})"),
        mpatches.Patch(color=WINTER_ZONE_COLOURS[1],
                       label=f"SD15b winter met (<{W_SD15b} m, n={n_sd15b})"),
        mpatches.Patch(color=WINTER_ZONE_COLOURS[2],
                       label=f"SD16 winter met (<{W_SD16} m, n={n_sd16})"),
        mpatches.Patch(color=WINTER_ZONE_COLOURS[3],
                       label=f"Below SD16 winter (>{W_SD16} m, n={n_below})"),
        Line2D([0],[0], marker="o", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Extended well"),
    ] + [Line2D([0],[0], marker="o", color="w",
                markerfacecolor=CLUSTER_COLS[c], ms=7, label=f"C{c}")
         for c in sorted(CLUSTER_LABELS)]
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
# FIGURE 3 — P_FLOOD MAP  (iterated closed form, Section 3.6.3)
# ─────────────────────────────────────────────────────────────────────────────
def plot_pflood_map(df: pd.DataFrame, dpi: int = 300) -> None:
    """
    Per-well P_flood spatial map.

    P_flood = cumulative winter rainfall (mm) required to raise the water
    table from each well's mean summer minimum to the slack-floor target
    (h_target = 0 m), using the cluster-specific horizon from October to
    historical peak month.

    Coefficient source priority:
      1. Per-well SSM coefficients (HEADLINE_LAG, from Script 03's
         03_master_data.csv) — used for all reference-network wells.
      2. Cluster-centroid SSM coefficients (from
         03_03_cluster_mechanistic_coefficients.csv) — fallback for
         extended-network wells that lack per-well fits.

    Wells are excluded from the map if:
      - their cluster lacks an entry in CLUSTER_PEAK_MONTH,
      - neither per-well nor cluster-level coefficients are available.
    """
    DIR_11B.mkdir(parents=True, exist_ok=True)

    P_clim, PET_clim = _load_climatology()
    cluster_coeffs = _load_cluster_coefficients()

    # ── Compute per-well P_flood ─────────────────────────────────────────
    pf_rows = []
    unreachable_n = 0
    skipped_cluster = 0
    skipped_beta = 0
    for _, row in df.iterrows():
        cluster = int(row["cluster"])
        if cluster not in CLUSTER_PEAK_MONTH:
            skipped_cluster += 1
            continue

        depth_bg = row["depth_bg"]
        if np.isnan(depth_bg) or depth_bg <= 0:
            continue

        # Per-well beta from Script 03 (m/m units in the DataFrame).
        # Convert to m/mm for the P_flood closed form.
        wb1_mm = row.get("well_b1_mm", np.nan)
        wb2_mm = row.get("well_b2_mm", np.nan)
        wb3    = row.get("well_b3", np.nan)
        has_per_well = (np.isfinite(wb1_mm) and wb1_mm > 0
                        and np.isfinite(wb2_mm)
                        and np.isfinite(wb3))

        if has_per_well:
            b1 = wb1_mm / 1000.0    # m/m -> m/mm
            b2 = wb2_mm / 1000.0    # m/m -> m/mm
            if wb3 < 0:
                print(f"  [WARNING] {row.get('well', '?')}: β₃ = {wb3:.4f} is negative "
                      f"(expected positive under displacement formulation)")
            b3 = abs(wb3)            # dimensionless, ensure positive
            coeff_source = "per-well"
        elif cluster in cluster_coeffs:
            cc = cluster_coeffs[cluster]
            b1 = cc["b1"]            # already m/mm from _load_cluster_coefficients
            b2 = cc["b2"]
            b3 = cc["b3"]
            coeff_source = "cluster"
        else:
            skipped_beta += 1
            continue

        # SSM sign convention: h in metres, negative below surface
        h_0 = -abs(depth_bg)

        months = _horizon_months(CLUSTER_PEAK_MONTH[cluster])
        res = _p_flood_iterated(
            P_FLOOD_H_TARGET_M, h_0,
            b1, b2, b3,
            months, P_clim, PET_clim,
        )

        if not np.isfinite(res["P_flood_mm"]) or res["lam"] < 0:
            unreachable_n += 1
            pflood_val   = np.nan
            lam_val      = res["lam"] if np.isfinite(res["lam"]) else np.nan
            unreachable  = True
        else:
            pflood_val   = res["P_flood_mm"]
            lam_val      = res["lam"]
            unreachable  = False

        pf_rows.append({
            "well":         row["well"],
            "E":            row["E"],
            "N":            row["N"],
            "cluster":      cluster,
            "network":      row["network"],
            "dem":          row["dem"],
            "depth_bg":     depth_bg,
            "h_0_m":        h_0,
            "coeff_source": coeff_source,
            "horizon_n":    res["n"],
            "alpha":        res["alpha"],
            "S_P_mm":       res["S_P"],
            "S_E_mm":       res["S_E"],
            "lambda":       lam_val,
            "pflood_mm":    pflood_val,
            "exceeds_mean": (pflood_val > res["P_clim_total"]) if not unreachable else True,
            "unreachable":  unreachable,
        })

    if not pf_rows:
        print("  [WARNING] No P_flood data computed")
        return

    pf = pd.DataFrame(pf_rows)
    n_reachable = (~pf["unreachable"]).sum()
    n_per_well = sum(1 for r in pf_rows if r["coeff_source"] == "per-well")
    n_cluster  = sum(1 for r in pf_rows if r["coeff_source"] == "cluster")
    print(f"  P_flood computed for {len(pf)} wells "
          f"({n_per_well} per-well, {n_cluster} cluster-level; "
          f"{n_reachable} reachable, {unreachable_n} unreachable; "
          f"{skipped_cluster} skipped — no peak month; "
          f"{skipped_beta} skipped — invalid beta)")

    # Export per-well CSV for citation in report
    pf.to_csv(OUT_11B_PFLOOD_PER_WELL, index=False)

    # ── Figure ───────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")
    _, ok, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    # Colour anchored on operational thresholds:
    #   green  = reachable in average winter (P_flood < ~500 mm)
    #   yellow = marginal — needs a wet winter (500–800 mm)
    #   orange = difficult — needs exceptional winter (800–1200 mm)
    #   red    = structurally unreachable (>1200 mm)
    cmap = LinearSegmentedColormap.from_list(
        "pflood", [
            (0.00, "#1a9850"),   # 0 mm — easy (green)
            (0.25, "#91cf60"),   # ~375 mm
            (0.40, "#d9ef8b"),   # ~600 mm — still reachable
            (0.50, "#fee08b"),   # ~750 mm — marginal
            (0.65, "#fc8d59"),   # ~975 mm — difficult
            (0.80, "#d73027"),   # ~1200 mm — very difficult
            (1.00, "#67001f"),   # 1500+ mm — unreachable
        ])

    pf_reachable = pf[~pf["unreachable"]].copy()
    if len(pf_reachable) < 3:
        print("  [WARNING] Too few reachable wells for IDW surface; "
              "plotting markers only.")
        sc = None
        gx = gy = surf = None
    else:
        # Colourbar range: cap at 3x mean annual winter rainfall to retain
        # contrast across the reachable domain.
        vmax = min(pf_reachable["pflood_mm"].quantile(0.95), 1500)
        sc, gx, gy, surf = add_idw_surface(
            ax, pf_reachable, value_col="pflood_mm",
            easting_col="E", northing_col="N",
            dem_col="dem",
            ridge_mask_threshold=1.0,
            dem_e_arr=dem_e_arr if ok else None,
            dem_n_arr=dem_n_arr if ok else None,
            dem_data=dem_data if ok else None,
            cmap=cmap, vmin=0, vmax=vmax,
            alpha=0.72, zorder=2,
        )
        surf = _fill_and_mask(surf, gx, gy, pf_reachable,
                              pf_reachable["pflood_mm"].values)

    # Wells: filled dot in cluster colour.
    for _, row in pf.iterrows():
        mk = "o" if row["network"] == "Reference" else "D"
        ax.scatter(row["E"], row["N"],
                   c=CLUSTER_COLS.get(row["cluster"], "#999"),
                   s=28, marker=mk, zorder=9, linewidths=0.4, edgecolors="white")

    kml_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

    if sc is not None:
        cbar = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02, shrink=0.85)
        # Two reference lines: one per recharge horizon
        P_CLIM_5MO = 464   # C1/C2: Oct–Feb
        P_CLIM_6MO = 524   # C3/C4/C5: Oct–Mar
        cbar.ax.axhline(P_CLIM_5MO, color="#1a6faf", lw=1.5, ls="--")
        cbar.ax.axhline(P_CLIM_6MO, color="#d62728", lw=1.5, ls="--")
        cbar.set_label(
            f"P_flood — cumulative winter rainfall (mm)\n"
            f"Blue dashed: C1/C2 mean ({P_CLIM_5MO} mm, Oct–Feb)\n"
            f"Red dashed: C3–C5 mean ({P_CLIM_6MO} mm, Oct–Mar)",
            fontsize=7.5)

    legend_patches = [
        mpatches.Patch(facecolor="#91cf60",
                       label="Reachable under climatological winter"),
        mpatches.Patch(facecolor="#fc8d59",
                       label="Requires wet winter (> climatology)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Reference well"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Extended well"),
    ] + [Line2D([0], [0], marker="o", color="w",
                markerfacecolor=CLUSTER_COLS[c], ms=7, label=f"C{c}")
         for c in sorted(CLUSTER_LABELS)]
    ax.legend(handles=legend_patches + kml_handles, fontsize=7,
              loc="upper left", framealpha=0.95, ncol=2)

    ax.set_xlabel("Easting (m, OSGB36)")
    ax.set_ylabel("Northing (m, OSGB36)")
    ax.set_title(
        "P_flood — Cumulative Winter Rainfall Required to Reach Slack Floor (mm)\n"
        "Newborough Warren  |  Iterated closed-form SSM  |  "
        "Per-well & cluster-level \u03b2 \u00b7 per-well summer minimum  |  Dune ridges masked",
        fontsize=10, fontweight="bold",
    )
    ax.set_xlim(240100, 243900)
    ax.set_ylim(362100, 365900)
    plt.tight_layout()
    fig.savefig(OUT_11B_PFLOOD_MAP, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_11B_PFLOOD_MAP.name}")
    print(f"  Saved: {OUT_11B_PFLOOD_PER_WELL.name}")


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

    cmap = LinearSegmentedColormap.from_list(
        "floodfreq", [
            (0.0,  "#8c510a"),   # 0% — dry brown (never floods)
            (0.15, "#d8b365"),   # ~15% — tan
            (0.35, "#f6e8c3"),   # ~35% — pale sand
            (0.50, "#c7eae5"),   # 50% — light teal (occasionally)
            (0.65, "#5ab4ac"),   # ~65% — mid teal
            (0.80, "#01665e"),   # ~80% — dark teal
            (1.0,  "#003c30"),   # 100% — deep blue-green (always floods)
        ])
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

    for level, col, ls, lw, lbl in [
        (25,  "white",  "--", 2.0, "25% frequency contour"),
        (50,  "black",  "-",  2.0, "50% frequency contour"),
    ]:
        try:
            cs = ax.contour(gx, gy, surf, levels=[level], colors=[col],
                            linestyles=[ls], linewidths=[lw], zorder=5)
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
        mpatches.Patch(facecolor="#8c510a", label="Never floods (0%)"),
        mpatches.Patch(facecolor="#c7eae5", edgecolor="#aaa", label="Occasionally floods (~50%)"),
        mpatches.Patch(facecolor="#003c30", label="Frequently floods (>75%)"),
        Line2D([0],[0], color="white", lw=2.0, ls="--", label="25% frequency contour"),
        Line2D([0],[0], color="black", lw=2.0, ls="-", label="50% frequency contour"),
        Line2D([0],[0], marker="o", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="#999",
               markeredgecolor="grey", ms=6, label="Extended well"),
    ] + [Line2D([0],[0], marker="o", color="w",
                markerfacecolor=CLUSTER_COLS[c], ms=7, label=f"C{c}")
         for c in sorted(CLUSTER_LABELS)]
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


# ─────────────────────────────────────────────────────────────────────────────
# TABLE 10 EXPORT — spreadsheet-ready collapsed-form P_flood equations
# ─────────────────────────────────────────────────────────────────────────────
def export_table10_spreadsheet() -> None:
    """
    Re-export the collapsed-form P_flood equations from Script 11's full
    threshold CSV as a compact report-ready table. The full CSV contains
    20+ columns of derivation detail; Table 10 in the report shows only
    the cluster, horizon, linear-form expression, climatological rainfall
    total, and spreadsheet cell formula.

    Reads:  OUT_11_TABLE8_THRESHOLDS  (11_forecast_pflood_threshold_equations.csv)
    Writes: OUT_11B_TABLE10           (11b_05_table10_pflood_spreadsheet.csv)

    Relies on slope_A, intercept_B, spreadsheet_formula, P_clim_total_mm,
    horizon_months, peak_month columns written by Script 11 Section 3.
    """
    DIR_11B.mkdir(parents=True, exist_ok=True)

    if not OUT_11_TABLE8_THRESHOLDS.exists():
        print(f"  [WARNING] Script 11 output not found at {OUT_11_TABLE8_THRESHOLDS}; "
              "cannot generate Table 10. Run Script 11 first.")
        return

    full = pd.read_csv(OUT_11_TABLE8_THRESHOLDS)

    required = {"Cluster", "Label", "slope_A", "intercept_B",
                "spreadsheet_formula", "P_clim_total_mm",
                "horizon_months", "peak_month"}
    missing = required - set(full.columns)
    if missing:
        print(f"  [WARNING] Script 11 output is missing expected columns: {missing}. "
              "Run the updated Script 11 to regenerate the full CSV.")
        return

    MONTH_ABBREV = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]

    rows = []
    for _, r in full.iterrows():
        peak_abbrev = MONTH_ABBREV[int(r["peak_month"]) - 1]
        horizon_str = f"Oct\u2013{peak_abbrev} ({int(r['horizon_months'])} mo)"
        pflood_expr = f"{r['slope_A']:.2f}\u00b7d + {r['intercept_B']:.2f}"
        rows.append({
            "Cluster":              r["Cluster"],
            "Label":                r["Label"],
            "Horizon":              horizon_str,
            "P_flood_equation":     pflood_expr,
            "Sum_P_clim_mm":        round(float(r["P_clim_total_mm"]), 0),
            "Spreadsheet_formula":  r["spreadsheet_formula"],
        })

    table10 = pd.DataFrame(rows)
    table10.to_csv(OUT_11B_TABLE10, index=False)

    print(f"  Saved: {OUT_11B_TABLE10.name}")
    print(f"\n  Table 10 contents (spreadsheet-ready, report paste-in):")
    for _, r in table10.iterrows():
        print(f"    {r['Cluster']:6s}  {r['Horizon']:18s}  "
              f"P_flood = {r['P_flood_equation']:28s}  "
              f"\u03a3P\u0304\u1d62 = {r['Sum_P_clim_mm']:.0f} mm")


# ─────────────────────────────────────────────────────────────────────────────
# FORECASTER HTML BUILD
# ─────────────────────────────────────────────────────────────────────────────
def _raf_valley_winter_mean(fallback: float = 521.0) -> float:
    """
    Fetch the Met Office RAF Valley monthly record at build time and compute
    the mean Oct-Mar winter total over complete hydrological years 2006-2025
    (i.e., winters starting Oct 2005 through Oct 2024). This is the
    authoritative climatology the report cites as ~521 mm.

    If the fetch fails (offline build, Met Office unreachable, format
    change), fall back to the supplied value and emit a warning. The
    forecaster itself does its own live fetch at page load, so a missing
    climatology constant at build time is not fatal for the tool.
    """
    import urllib.request, urllib.error
    url = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/valleydata.txt"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  [INFO] Met Office fetch failed ({e}); using report-cited "
              f"climatology {fallback} mm as fallback.")
        return fallback

    # Parse: each data line is "yyyy mm tmax tmin af rain sun"
    totals = {}   # hy -> list of monthly mm
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) < 6:
            continue
        try:
            yr, mo = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        if not (1900 <= yr <= 2100 and 1 <= mo <= 12):
            continue
        rain_tok = parts[5]
        if rain_tok == "---":
            continue
        try:
            rain = float(rain_tok.replace("*", "").replace("#", ""))
        except ValueError:
            continue
        if mo in (10, 11, 12, 1, 2, 3):
            hy = yr + 1 if mo >= 10 else yr
            totals.setdefault(hy, []).append(rain)

    complete = [sum(v) for hy, v in totals.items()
                if 2006 <= hy <= 2025 and len(v) == 6]
    if not complete:
        print(f"  [INFO] Met Office data parsed but no complete winters found; "
              f"using fallback {fallback} mm.")
        return fallback
    mean_mm = sum(complete) / len(complete)
    print(f"  Met Office RAF Valley Oct-Mar mean: {mean_mm:.0f} mm "
          f"(n={len(complete)} complete winters, 2006-2025)")
    return float(mean_mm)


def _build_forecaster_data_bundle() -> dict:
    """
    Assemble the runtime data bundle for the interactive forecaster from
    pipeline CSVs. This is the single source of truth for the forecaster —
    if the pipeline is re-run, the forecaster updates with it.

    Returns a dict matching the structure the forecaster template expects:
      {
        cluster_coeffs: {C1..C5: {label, b1, b2, b3, peak_month,
                                   slope_A, intercept_B, P_clim_total_mm,
                                   horizon_months}},
        block_tf: {Lake_Edge|Eastern_Block|Western_Block|Forest|Coastal_Forest:
                   {winter: {...}, summer: {...}}},
        P_clim: {1..12: mm},
        wells: [{name, display_name, E, N, ground_elev, cluster,
                 nearest_cluster_only, default_h_prev, default_h_max}],
      }

    Cluster scope (k=5 partition):
      All five clusters are included. The old k=6 partition had two
      small-n groups (old C5 Coastal n=1, old C6 Lake n=1) that were
      dropped at the partition step; they do not correspond to any
      current cluster ID.

    The nearest_cluster_only flag marks wells whose cluster assignment is a
    pattern-match nearest-type only — they sit outside the SSM operational
    domain (tidal/boundary/upstream-excluded) but are still included with
    their best-matching cluster's coefficients. The UI should communicate
    this to the user.

    Block schema change:
      Under k=5 each cluster is its own block (one-to-one), so block_tf
      now has 5 keys instead of the previous 3 (Eastern/Western/Forest).
      The forecaster_template.html iterates with Object.entries so the
      schema move is transparent to the JS.
    """
    bundle = {}

    # ── Cluster coefficients (Script 03) merged with collapsed P_flood (Script 11) ──
    cc = pd.read_csv(INT_CLUSTER_MECHANISTIC)
    pf = pd.read_csv(OUT_11_TABLE8_THRESHOLDS)
    # Script 11 writes 'C1'-style strings in the Cluster column; keep that as
    # the bundle key convention since the forecaster template indexes
    # DATA.cluster_coeffs by 'C1' / 'C2' / ... etc.
    pf_by_cluster = {r["Cluster"]: r for _, r in pf.iterrows()}

    # String-keyed labels from utils.config (k=5 partition).
    cluster_labels = {f"C{cid}": label for cid, label in CLUSTER_LABELS.items()}

    cluster_coeffs = {}
    for _, r in cc.iterrows():
        # Script 03 writes the Cluster column as integer; coerce to 'C{n}' so
        # the bundle key style matches Script 11's. _coerce_cluster_int
        # handles both int and 'C1'-string inputs defensively.
        cid_int = _coerce_cluster_int(r["Cluster"])
        if cid_int is None:
            continue
        c = f"C{cid_int}"
        if c not in cluster_labels:
            continue   # skip any cluster outside the canonical k=5 set
        pfr = pf_by_cluster.get(c)
        if pfr is None:
            print(f"  [WARNING] No P_flood entry for {c}; skipping.")
            continue
        b3_fc = float(r["beta_3_drainage"])
        if b3_fc < 0:
            print(f"  [WARNING] {c}: β₃ = {b3_fc:.4f} is negative "
                  f"(expected positive under displacement formulation)")
        cluster_coeffs[c] = {
            "label":             cluster_labels[c],
            "b1":                float(r["beta_1_recharge"]) / 1000.0,
            "b2":                float(r["beta_2_atmospheric_draw"]) / 1000.0,
            "b3":                abs(b3_fc),
            "peak_month":        int(pfr["peak_month"]),
            "slope_A":           float(pfr["slope_A"]),
            "intercept_B":       float(pfr["intercept_B"]),
            "P_clim_total_mm":   float(pfr["P_clim_total_mm"]),
            "horizon_months":    int(pfr["horizon_months"]),
        }
    bundle["cluster_coeffs"] = cluster_coeffs

    # ── Block transfer functions (Script 11 Tables 6 & 7) ──
    t6 = pd.read_csv(OUT_11_TABLE6_WINTER)   # peak flood
    t7 = pd.read_csv(OUT_11_TABLE7_SUMMER)   # summer drought

    # Under the k=5 partition each cluster is its own block (no macro-
    # aggregation). The block names below mirror BLOCK_MAP in Script 03 and
    # the column names in 03_regional_averages.csv.
    block_clusters = {
        "Lake_Edge":      ["C1"],
        "Eastern_Block":  ["C2"],
        "Western_Block":  ["C3"],
        "Forest":         ["C4"],
        "Coastal_Forest": ["C5"],
    }
    # CSV "Block" column matches the dict key directly under k=5.
    csv_block_names = {block: block for block in block_clusters}

    block_tf = {}
    for block, cs in block_clusters.items():
        csv_name = csv_block_names[block]
        w = t6[t6["Block"] == csv_name]
        s = t7[t7["Block"] == csv_name]
        if w.empty or s.empty:
            print(f"  [WARNING] Transfer-function row missing for block {block}; skipping.")
            continue
        wr, sr = w.iloc[0], s.iloc[0]
        block_tf[block] = {
            "winter": {
                "b1":       float(wr["beta_1_P_winter"]),
                "b2":       float(wr["beta_2_h_min"]),
                "c":        float(wr["intercept"]),
                "r2":       float(wr["R2"]),
                "clusters": cs,
            },
            "summer": {
                "b1":       float(sr["beta_1_P_summer"]),
                "b2":       float(sr["beta_2_h_max_winter"]),
                "c":        float(sr["intercept"]),
                "r2":       float(sr["R2"]),
                "clusters": cs,
            },
        }
    bundle["block_tf"] = block_tf

    # ── Climatology: monthly P from 03_regional_averages.csv, 2005–2026 baseline ──
    ra = pd.read_csv(INT_REGIONAL_AVERAGES, parse_dates=["Date"]).set_index("Date")
    P_clim = ra.groupby(ra.index.month)["P_mm"].mean()
    PET_clim = ra.groupby(ra.index.month)["PET_mm"].mean()
    # Serialize keyed by string month (JSON-friendly; JS reads DATA.P_clim[m] with number key)
    bundle["P_clim"] = {int(m): float(v) for m, v in P_clim.items()}
    bundle["PET_clim"] = {int(m): float(v) for m, v in PET_clim.items()}

    # Authoritative Oct-Mar winter climatology: fetched from the Met Office
    # RAF Valley monthly record at build time. The climatology in
    # 03_regional_averages.csv has gaps where groundwater data is missing
    # which biases any rainfall average computed from it downwards. The
    # Met Office file has no such gaps for 2005-2026.
    bundle["winter_climatology_mm"] = _raf_valley_winter_mean(fallback=521.0)

    # ── Well list: merge locations, elevations, cluster assignments, summer/winter defaults ──
    locs  = pd.read_csv(INT_LOCATIONS)
    elev  = pd.read_csv(INT_WELL_ELEVATIONS)
    md    = pd.read_csv(INT_MASTER_DATA)         # reference cluster assignments
    site  = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE) # extended cluster assignments

    # Build cluster defaults for the reading input pre-fill
    cluster_default_h_prev = {}
    cluster_default_h_max  = {}
    # default_h_prev = cluster mean month-of-minimum head (most negative monthly mean)
    # default_h_max  = cluster mean month-of-maximum head
    for c in cluster_coeffs:
        if c in ra.columns:
            monthly = ra.groupby(ra.index.month)[c].mean()
            cluster_default_h_prev[c] = float(monthly.min())
            cluster_default_h_max[c]  = float(monthly.max())

    # Reference-network wells — cluster comes from INT_MASTER_DATA
    ref_clusters = {
        _norm(r["Name_Original"]): f"C{int(r['Cluster'])}"
        for _, r in md.iterrows()
    }
    # Extended-network wells — cluster comes from sitewide audit
    ext_clusters = {
        _norm(r["Well_Normalised"]): f"C{int(r['Best_Match_Cluster'])}"
        for _, r in site[site["Network"] == "Extended"].iterrows()
    }

    # Locations + elevations by normalised well name
    loc_by_norm = {}
    for _, r in locs.iterrows():
        for col in ("Match_ID", "Name"):
            if col in r and pd.notna(r.get(col)):
                loc_by_norm[_norm(r[col])] = r
                break
    elev_by_norm = {_norm(r["Name_norm"]): r for _, r in elev.iterrows()}

    wells = []
    # Per-well SSM coefficients from master_data (reference wells only)
    well_betas = {}
    for _, mr in md.iterrows():
        wn_md = _norm(mr["Name_Original"])
        b1_raw = mr.get("beta_1_recharge", np.nan)
        b2_raw = mr.get("beta_2_atmospheric_draw", np.nan)
        b3_raw = mr.get("beta_3_drainage", np.nan)
        if (pd.notna(b1_raw) and float(b1_raw) > 0
                and pd.notna(b2_raw) and pd.notna(b3_raw)):
            b3_v = float(b3_raw)
            if b3_v < 0:
                print(f"  [WARNING] {wn_md}: β₃ = {b3_v:.4f} is negative "
                      f"(expected positive under displacement formulation)")
            well_betas[wn_md] = {
                "b1": float(b1_raw) / 1000.0,   # m/m -> m/mm
                "b2": float(b2_raw) / 1000.0,
                "b3": abs(b3_v),
            }

    for wn, cluster in {**ref_clusters, **ext_clusters}.items():
        if cluster not in cluster_coeffs:
            continue   # skip wells whose cluster is outside the canonical k=5 set
        if wn not in loc_by_norm or wn not in elev_by_norm:
            continue
        lrow, erow = loc_by_norm[wn], elev_by_norm[wn]
        ground = erow.get("DEM_Ground_Elev")
        if pd.isna(ground):
            continue
        display = str(lrow.get("Match_ID") or lrow.get("Name") or wn)
        # nearest_cluster_only=True means the cluster label is a pattern-match
        # nearest-type assignment, not a core-member assignment. The SSM
        # forecast is still computed (using the matched cluster's coefficients)
        # but the UI should make clear the user's interpretation should be
        # tempered.
        nearest_only = wn in NEAREST_CLUSTER_ONLY_WELLS

        # Per-well P_flood coefficients (slope_A_well, intercept_B_well)
        # computed from the well's own beta if available.
        wb = well_betas.get(wn)
        well_pflood = {}
        if wb is not None:
            cc_cluster = cluster_coeffs[cluster]
            peak_month = cc_cluster["peak_month"]
            months = _horizon_months(peak_month)
            n = len(months)
            alpha_w = 1.0 - wb["b3"]
            alpha_n_w = alpha_w ** n
            S_P_w = sum(alpha_w ** (n - 1 - i) * P_clim[m]
                        for i, m in enumerate(months))
            S_E_w = sum(alpha_w ** (n - 1 - i) * PET_clim[m]
                        for i, m in enumerate(months))
            P_clim_total = sum(P_clim[m] for m in months)
            denom = wb["b1"] * S_P_w
            if abs(denom) > 1e-12:
                well_pflood = {
                    "slope_A_well":      (alpha_n_w * P_clim_total) / denom,
                    "intercept_B_well":  (wb["b2"] * S_E_w * P_clim_total) / denom,
                    "b1_well":           wb["b1"],
                    "b2_well":           wb["b2"],
                    "b3_well":           wb["b3"],
                }

        wells.append({
            "name":            wn,
            "display_name":    display,
            "E":               float(lrow["E"]),
            "N":               float(lrow["N"]),
            "ground_elev":     float(ground),
            "cluster":         cluster,
            "nearest_cluster_only": bool(nearest_only),
            "default_h_prev":  cluster_default_h_prev.get(cluster, -1.0),
            "default_h_max":   cluster_default_h_max.get(cluster, -0.5),
            **well_pflood,
        })
    wells.sort(key=lambda w: (w["cluster"], w["name"]))
    bundle["wells"] = wells

    # ── Base layer: hillshade image + KML feature polylines ──────────────
    # These are embedded into the bundle so the forecaster HTML can render
    # a proper spatial context behind the well dots.
    bundle["base_layer"] = _build_base_layer()

    return bundle


def _build_base_layer() -> dict:
    """
    Build the forecaster base layer data: a base64-encoded hillshade PNG
    and KML feature polylines as coordinate arrays in OSGB36.

    Uses the same fixed map extent as the 11b PNG maps:
    E 240100–243900, N 362100–365900.
    """
    import base64
    from io import BytesIO

    EXTENT = {
        "eMin": 240100, "eMax": 243900,
        "nMin": 362100, "nMax": 365900,
    }
    result = {"extent": EXTENT, "hillshade_png": None, "features": []}

    # ── Hillshade ────────────────────────────────────────────────────────
    dem_path = DATA_DIR / "newborough_dem.tif"
    if dem_path.exists():
        try:
            import rasterio
            from matplotlib.colors import LightSource

            with rasterio.open(str(dem_path)) as src:
                raw = src.read(1).astype(float)
                transform = src.transform
                res_x = abs(transform.a)
                res_y = abs(transform.e)
                dem_e = transform.c + np.arange(raw.shape[1]) * transform.a
                dem_n = transform.f + np.arange(raw.shape[0]) * transform.e
                if src.nodata is not None:
                    raw[raw == src.nodata] = np.nan

            filled = np.nan_to_num(raw, nan=0.0)
            ls = LightSource(azdeg=315, altdeg=35)
            hs = ls.hillshade(filled, vert_exag=3.0, dx=res_x, dy=res_y)

            # Crop to map extent
            e_mask = (dem_e >= EXTENT["eMin"]) & (dem_e <= EXTENT["eMax"])
            n_mask = (dem_n >= EXTENT["nMin"]) & (dem_n <= EXTENT["nMax"])
            hs_crop = hs[np.ix_(n_mask, e_mask)]

            # Render to PNG via matplotlib (no axes, no border)
            fig_hs, ax_hs = plt.subplots(figsize=(8, 8), dpi=150)
            ax_hs.imshow(hs_crop, cmap="gray", vmin=0.2, vmax=1.0,
                         origin="upper", aspect="equal")
            ax_hs.axis("off")
            fig_hs.subplots_adjust(left=0, right=1, top=1, bottom=0)
            buf = BytesIO()
            fig_hs.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                           pad_inches=0, transparent=False)
            plt.close(fig_hs)
            buf.seek(0)
            result["hillshade_png"] = base64.b64encode(buf.read()).decode("ascii")
            print("  Forecaster base layer: hillshade embedded OK")
        except Exception as exc:
            print(f"  [WARNING] Hillshade embed failed: {exc}")
    else:
        print(f"  [WARNING] DEM not found at {dem_path}; forecaster will lack hillshade")

    # ── KML features ─────────────────────────────────────────────────────
    kml_layers = [
        {"file": "Features.kml",  "filter": "forest|plantation|wood|boundary",
         "colour": "purple",      "width": 2.2, "dash": "",     "label": "Forest Boundary"},
        {"file": "Features.kml",  "filter": "lake|llyn|rhos",
         "colour": "dodgerblue",  "width": 1.8, "dash": "",     "label": "Lake",
         "fill": "rgba(30,144,255,0.15)"},
        {"file": "Features.kml",  "filter": "broadleaf|restock",
         "colour": "#228B22",     "width": 2.0, "dash": "6,3",  "label": "Broadleaf Restock"},
        {"file": "Features.kml",  "filter": None,
         "colour": "black",       "width": 1.3, "dash": "5,3",  "label": "Other Features"},
        {"file": "clearfell.kml", "filter": None,
         "colour": "darkorange",  "width": 2.2, "dash": "6,2,2,2", "label": "Felling Area"},
    ]

    for layer in kml_layers:
        kml_path = DATA_DIR / layer["file"]
        if not kml_path.exists():
            continue
        try:
            gdf = _safe_read_kml(kml_path)
            if gdf is None or gdf.empty:
                continue
            gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
            gdf = gdf.to_crs("EPSG:27700")

            # Apply filter
            if layer["filter"] is not None:
                name_col = gdf.get("Name", pd.Series("", index=gdf.index)).fillna("").astype(str)
                desc_col = gdf.get("description", pd.Series("", index=gdf.index)).fillna("").astype(str)
                combined = name_col + " " + desc_col
                mask = combined.str.contains(layer["filter"], case=False, na=False)
                # "Other Features" is the negation of all named filters
                if layer["label"] == "Other Features":
                    lake_m = combined.str.contains("lake|llyn|rhos", case=False, na=False)
                    forest_m = combined.str.contains("forest|plantation|wood|boundary", case=False, na=False)
                    broad_m = combined.str.contains("broadleaf|restock", case=False, na=False)
                    mask = ~(lake_m | forest_m | broad_m)
                gdf = gdf[mask]

            if gdf.empty:
                continue

            # Extract coordinate arrays from geometries
            polys = []
            for geom in gdf.geometry:
                if geom is None:
                    continue
                coords_list = _extract_coords(geom)
                for coords in coords_list:
                    polys.append([[round(c[0], 1), round(c[1], 1)] for c in coords])

            if polys:
                feat = {
                    "coords":  polys,
                    "colour":  layer["colour"],
                    "width":   layer["width"],
                    "dash":    layer.get("dash", ""),
                    "label":   layer["label"],
                }
                if "fill" in layer:
                    feat["fill"] = layer["fill"]
                result["features"].append(feat)

        except Exception as exc:
            print(f"  [WARNING] KML layer '{layer['file']}' failed: {exc}")

    n_feat = sum(len(f["coords"]) for f in result["features"])
    print(f"  Forecaster base layer: {n_feat} KML polylines from "
          f"{len(result['features'])} layers")

    return result


def _extract_coords(geom) -> list:
    """Extract coordinate arrays from a shapely geometry (any type)."""
    from shapely.geometry import (
        Polygon, MultiPolygon, LineString, MultiLineString,
        GeometryCollection, Point, MultiPoint,
    )
    results = []
    if isinstance(geom, Polygon):
        results.append(list(geom.exterior.coords))
    elif isinstance(geom, MultiPolygon):
        for poly in geom.geoms:
            results.append(list(poly.exterior.coords))
    elif isinstance(geom, LineString):
        results.append(list(geom.coords))
    elif isinstance(geom, MultiLineString):
        for line in geom.geoms:
            results.append(list(line.coords))
    elif isinstance(geom, GeometryCollection):
        for sub in geom.geoms:
            results.extend(_extract_coords(sub))
    # Points/MultiPoints ignored — no polylines to draw
    return results


def build_forecaster_html() -> None:
    """
    Generate forecaster.html by injecting the pipeline-derived data bundle
    into the forecaster HTML template. The template (src/forecaster_template.html)
    contains all UI logic; this function only provides the data.

    Live Met Office rainfall is fetched client-side at page load, so the
    forecaster self-updates after pipeline runs stop. Script 11 and Script 03
    outputs must exist before this runs.
    """
    DIR_11B.mkdir(parents=True, exist_ok=True)

    if not SRC_FORECASTER_TEMPLATE.exists():
        print(f"  [WARNING] Forecaster template not found at {SRC_FORECASTER_TEMPLATE}; "
              "skipping forecaster HTML generation.")
        return
    for needed in (OUT_11_TABLE8_THRESHOLDS, INT_CLUSTER_MECHANISTIC,
                   OUT_11_TABLE6_WINTER, OUT_11_TABLE7_SUMMER,
                   INT_REGIONAL_AVERAGES):
        if not needed.exists():
            print(f"  [WARNING] Required input missing: {needed}. "
                  "Run Scripts 03 and 11 first; skipping forecaster.")
            return

    bundle = _build_forecaster_data_bundle()

    n_wells = len(bundle["wells"])
    n_clusters = len(bundle["cluster_coeffs"])
    n_blocks = len(bundle["block_tf"])
    if n_wells == 0 or n_clusters == 0 or n_blocks == 0:
        print(f"  [WARNING] Empty data bundle ({n_wells} wells, {n_clusters} "
              f"clusters, {n_blocks} blocks); skipping forecaster HTML.")
        return

    # JSON encoder: default=str handles any stray numpy scalar or Timestamp;
    # allow_nan=False would be stricter but we don't expect NaNs here.
    data_js = "const DATA = " + json.dumps(bundle, indent=2, default=str) + ";"

    template = SRC_FORECASTER_TEMPLATE.read_text(encoding="utf-8")
    marker = "/*__DATA_BUNDLE__*/"
    if marker not in template:
        print(f"  [ERROR] Template marker '{marker}' not found in "
              f"{SRC_FORECASTER_TEMPLATE}; cannot inject data.")
        return
    html = template.replace(marker, data_js)

    OUT_11B_FORECASTER_HTML.write_text(html, encoding="utf-8")

    print(f"  Saved: {OUT_11B_FORECASTER_HTML.name}")
    print(f"    wells: {n_wells}  clusters: {n_clusters}  "
          f"blocks: {n_blocks}  template size: {len(template):,} chars "
          f"\u2192 rendered size: {len(html):,} chars")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main(preview: bool = False) -> None:
    dpi = 150 if preview else 300
    print("\n=== 11b_spatial_thresholds.py ===")
    print("Loading well data...")
    df = load_well_data()
    print("Generating summer minima depth map...")
    plot_summer_minima_map(df, dpi=dpi)
    print("Generating winter maxima depth map...")
    plot_winter_maxima_map(df, dpi=dpi)
    print("Generating P_flood map (iterated, Section 3.6.3)...")
    plot_pflood_map(df, dpi=dpi)
    print("Generating flood frequency map...")
    plot_flood_frequency_map(df, dpi=dpi)
    print("Exporting Table 10 (spreadsheet-ready P_flood equations)...")
    export_table10_spreadsheet()
    print("Building interactive forecaster HTML...")
    build_forecaster_html()
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
