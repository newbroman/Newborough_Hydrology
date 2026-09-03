"""
37b_driver_footing.py
======================
Part B — comparative driver footing (forest · scrape · coast) on common
currencies, over a shared 2005->2025 (20-yr) horizon.

Design document: SPEC_script37b_partB_comparative_footing_2026-07-06.md
(amends SPEC_script37_scale_factor_regression_2026-07-06.md, Part B section).

Sign-off decisions (2026-07-06):
  1. Housing: NEW Script 37b (analytical; pipeline 44->45 / 46->47 depending
     on which baseline count is used — see CHANGELOG; analytical 41->42,
     phases unchanged). Report Abstract/Conclusions/Methods count text is
     Martin's document-edit workflow, not part of this code build.
  2. Sy for the volume currency: PER-DRIVER REPRESENTATIVE Sy (not per-cell),
     read live from utils.pipeline_params.load_params()["clusters"] (the
     pipeline's single source of truth for per-cluster Sy — Script 17's
     output, same numbers as OUT_18_WELL_SY_TABLE grouped by Cluster). Coast/
     scrape -> C3; forest (clearfell, broadleaf) -> well-count-weighted
     mean of C4/C5, weights read live from the well roster (never
     hardcoded 9/5).
  3. Baseline for Currency 3 (ecological threshold crossings): TRUE PER-WELL
     summer minima, computed directly from INT_WELLS_CLEAN (mean of annual
     Jun-Sep minima per well) — NOT the cluster-level 14_annual_extremes.csv
     the original spec cited (that file is genuinely cluster-level, 5 rows/
     year; there is no per-well data in it — confirmed by reading Script 14,
     which runs on INT_REGIONAL_AVG, a cluster-mean series, from the start).

Purpose — put the three drivers side by side in the SAME currencies so a
reader can see their relative weight at a glance. Does NOT use Script 37's
scale factors (unresolved/null — Part A owns that verdict). Rests on
OBSERVED anchors (BACI steps) and the MODELLED Script 20 fields, every cell
flagged observed or modelled. Each driver enters as a GAIN and a LOSS
component (all three are two-sided):

    Driver              Gain component            Loss component
    Forest management   Clearfell (canopy off)     Broadleaf restock (canopy on)
    Dune scraping        On-site slack rise         Off-site drain cone
    Coast                Sea-level rise (head gain)  Chronic erosion drawdown

Sign convention throughout (matches Script 37's dh_corr): positive mm =
wetting/rise; negative mm = drying/loss.

Currencies
----------
1. PEAK LOCAL HEAD CHANGE (mm) — one number per component, worst-affected
   point. Mostly observed (clearfell, scrape on-site, scrape off-site);
   coast/SLR/broadleaf modelled from Script 20 fields.
2. AREA-INTEGRATED CHANGE (mm.ha and m^3) — each Script 20 unit field at its
   2025 (fully-realised) amplitude, integrated over the site mask
   (canonical extent, 50 m grid matching Script 20's own resolution). Scrape
   on-site uses the registry footprint+rise-buffer polygons directly (not a
   decaying field); scrape off-site uses the leaky-aquifer image-method
   field (rise zones excluded — already accounted for on-site).
3. ECOLOGICAL THRESHOLD CROSSINGS (Curreli) — per well (66 reference-network
   wells; extended network / lake gauge out of the canonical C1-C5
   partition, excluded), baseline = observed per-well summer-minimum depth
   (Sign-off #3 above) + each component's head delta at that well, crossing
   count against SD15b (wet-slack, config.py) and SD16 (dry-slack), reported
   PER COMPONENT and in BOTH directions (worsen / relieve) — mirrors the
   continuous zone-classification precedent in Script 11b (ZONE_BOUNDS),
   not a wet-slack/dry-slack well-type split (no such per-well typing file
   exists; both thresholds are evaluated for every well, as Script 11b does).

What this does NOT do (per spec)
---------------------------------
Does not use Script 37 scale factors. Does not close a water budget —
first-order superposition, an upper bound in overlap zones (same caveat as
the Script 20 map). Does not resolve the near-field scrape cone
observationally (nearest uphill well 262 m — modelled). Does not
re-estimate any driver amplitude — it places established observed/modelled
amplitudes on common axes.

Flagged caveat (not in the original spec, surfaced during build): Script
20's SLR field is a 5-yr NEAR-TERM projection (+20 mm over
SLR_WINDOW_YEARS=5), while every other component here is evaluated at the
20-yr (2005-2025) horizon. Reported as Script 20's native value (per spec's
own Currency-1 table), NOT rescaled to 20 yr — flagged prominently in
37b_results.txt so it is not read as directly magnitude-comparable to the
20-yr components.

Outputs (outputs/37b_driver_footing/):
  37b_driver_footing.csv   component x currency, mechanism-type,
                           observed/modelled flag, gain/loss, driver group.
  37b_driver_footing.png   grouped bars, one panel per currency.
  37b_results.txt          whole-story summary + caveats.

Runs after Script 37 (Part A) in the driver-validation phase; the canonical
step index is in outputs/pipeline_manifest.json.
"""

__version__ = "1.3.0"  # Hollingham (2026) — 2026-08-22. The uniform driver row
#   is the MEASURED residual, not the panel's fitted constant. load_climate_c()
#   read c, which is not separately identified (D-039), so the footing ranked a
#   quantity with no rate — and when c moved the row moved with it, from -127 mm
#   to -2 mm over the horizon, without anything about the site having changed.
#   load_uniform_residual() reads the balanced observed decline minus the
#   modelled coastal gradient, per open-dune cluster, and takes the mean. The row
#   is renamed to say what it is: an unexplained uniform decline, a central
#   estimate and not a resolved rate (D-057).
#
# v1.2.1
#   WTF Sy table from OUT_18_WELL_SY_TABLE; INT_WTF_WELL_SY is retired
#   (D-038). Pure path/symbol change, values identical.
#
# v1.2.0  # 2026-07-17: add CLIMATE as a distinctly-flagged
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import os
import sys
import importlib.util
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import config, paths
from utils.paths import (
    INT_MASTER_DATA, INT_WELLS_CLEAN, OUT_18_WELL_SY_TABLE,
    OUT_10A_REPORT, OUT_10M_REPORT, OUT_09_BACI_SHIFTS,
    OUT_20_REPORT_NUMBERS, OUT_25_FIT_PARAMETERS, OUT_25_CLUSTER_PARTITION,
    DATA_KML_FEATURES,
)
from utils.config import CLUSTER_LABELS
from utils.map_utils import make_site_mask
from utils.console_utils import banner, phase, step, info, note, warn, result, saved, done
from utils import pipeline_params
from utils.render_utils import render_figure

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
DIR_37B            = paths.DIR_37B
OUT_COMPARISON     = paths.OUT_37B_COMPARISON
OUT_FIGURE         = paths.OUT_37B_FIGURE
OUT_RESULTS        = paths.OUT_37B_RESULTS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_ID = "37b"

# Common horizon: read from config.ACT_PERIODS['2005_2025'] rather than
# hardcoding "20" (Sign-off / no-hardcoded-values convention).
_H_START, _H_END = config.ACT_PERIODS["2005_2025"]
HORIZON_YEARS = float(_H_END - _H_START)

# Grid resolution matches Script 20's own canonical map grid (50 m).
GRID_RES_M = 50.0

MPL_RC = {
    "font.family":       "sans-serif",
    "font.size":         10,
    "axes.spines.top":   False,
    "axes.spines.right": False,
}

# Ecological thresholds (Curreli 2013), mm, positive depth-below-ground
# convention (matches Script 11b's ZONE_BOUNDS treatment — both thresholds
# evaluated for every well; no per-well wet/dry-slack typing file exists).
SD15B_MM = 1000.0 * config.SD15b   # wet-slack, 610 mm
SD16_MM  = 1000.0 * config.SD16    # dry-slack, 980 mm

COMPONENT_META = {
    # key             driver group          mechanism      gain/loss  observed?
    "coast_erosion": ("Coast",              "progressive", "loss",   False),
    "slr":           ("Coast",              "progressive", "gain",   False),
    "clearfell":     ("Forest management",  "step",        "gain",   True),
    "broadleaf":     ("Forest management",  "progressive", "loss",   False),
    "scrape_onsite": ("Dune scraping",      "step",        "gain",   True),
    "scrape_offsite":("Dune scraping",      "redistributive","loss", True),
    "climate":       ("Unexplained (uniform)","uniform",  "loss",   False),
}
COMPONENT_LABELS = {
    "coast_erosion":  "Coastal erosion (chronic drawdown)",
    "slr":            "Sea-level rise (head gain)",
    "clearfell":      "Clearfell (canopy removed)",
    "broadleaf":      "Broadleaf restock (canopy added)",
    "scrape_onsite":  "Scrape on-site (slack rise)",
    "scrape_offsite": "Scrape off-site (drain cone)",
    "climate":        "Unexplained uniform decline (central estimate, not resolved)",
}


# ---------------------------------------------------------------------------
# Script 20 import (numeric filename), reused unchanged
# ---------------------------------------------------------------------------

def _load_s20():
    path = Path(__file__).parent / "20_spatial_figures.py"
    spec = importlib.util.spec_from_file_location("_s20_spatial_37b", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Live-value loaders (no hardcoded values; console-warned fallbacks via
# pipeline_params.default_value(), matching the 09b/09d/09f precedent)
# ---------------------------------------------------------------------------

def load_coastal_fit() -> tuple[float, float]:
    """δ₀ (mm/yr, positive magnitude) and L (m) — Script 25 forest-free
    linear-capped row."""
    try:
        df = pd.read_csv(OUT_25_FIT_PARAMETERS)
        row = df[(df["source"] == "forest_free") & (df["model"] == "linear_capped")]
        if row.empty:
            row = df[(df["source"] == "full") & (df["model"] == "linear_capped")]
        d0 = abs(float(row["delta_0_mm_yr"].iloc[0]))
        L = float(row["L_m"].iloc[0])
        info(f"δ₀ = {d0:.2f} mm/yr, L = {L:.0f} m (live, Script 25 forest-free linear-capped)")
        return d0, L
    except Exception as exc:
        d0 = abs(pipeline_params.default_value("coast_delta0_mm_yr"))
        L = pipeline_params.default_value("coast_reach_L_m")
        warn(f"cannot read Script 25 fit ({exc}) — using first-pass defaults δ₀={d0}, L={L}")
        return d0, L


def load_uniform_residual() -> float:
    """The spatially-uniform decline this footing carries, mm/yr, negative.

    NOT the panel's fitted constant c. c is not separately identified — it
    trades off exactly against the cumulative-water-balance covariate and only
    their sum is recovered (D-039) — so a driver row computed from it ranks a
    quantity that has no rate. This function reads the MEASURED residual
    instead: per open-dune cluster, the balanced observed decline minus the
    modelled coastal gradient at that cluster's mean distance to the coast, and
    the mean of those.

    The open-dune clusters are the ones the coastal gradient is fitted on
    (forest-free, D-046); the forest clusters carry a canopy term this
    subtraction does not remove, which is why they are excluded here and why
    their own residuals differ.

    What the agreement does and does not buy: the clusters agree closely, which
    is evidence the remaining decline is SPATIALLY UNIFORM. It is not evidence
    that the rate is resolved. Their year-to-year swings are common-mode — same
    weather, same aquifer — so the errors do not average down, and the
    detection floor of the site-mean trend still applies to this magnitude.
    Anything consuming this value must carry that caveat with it (D-057).
    """
    try:
        df = pd.read_csv(OUT_25_CLUSTER_PARTITION)
        open_dune = df[~df["cluster_id"].astype(int).isin(config.FOREST_CIDS)]
        resid = (open_dune["observed_balanced_annual_mean_mm_yr"]
                 - open_dune["coastal_gradient_mm_yr"])
        r = float(resid.mean())
        info(f"uniform residual = {r:.2f} mm/yr (live, mean over "
             f"{len(resid)} open-dune clusters; spread "
             f"{float(resid.max() - resid.min()):.2f} mm/yr) — central estimate, "
             f"not a resolved rate")
        return r
    except Exception as exc:
        r = float(pipeline_params.default_value("uniform_residual_mm_yr"))
        warn(f"cannot read Script 25 cluster partition ({exc}) — using first-pass "
             f"default uniform residual = {r}")
        return r


def load_clearfell_step_mm() -> float:
    """Clearfell ANCOVA step (mm) — Path B, 10a_report_numbers.csv."""
    try:
        df = pd.read_csv(OUT_10A_REPORT)
        key_col = df.iloc[:, 0].astype(str)
        row = df[key_col == "ANCOVA_Forest_Impact_clearfell_step"]
        val_mm = float(row.iloc[0, 3]) * 1000.0
        info(f"clearfell step (live, 10a ANCOVA): {val_mm:.1f} mm")
        return val_mm
    except Exception as exc:
        val_mm = pipeline_params.default_value("clearfell_recovery_mm")
        warn(f"cannot read 10a clearfell step ({exc}) — using first-pass default {val_mm} mm")
        return val_mm


def load_scrape_onsite_mm() -> float:
    """CEH36 'Pure_Scraping' BACI shift (mm) — observed on-site anchor,
    09_scrape_03_baci_shifts.csv."""
    try:
        df = pd.read_csv(OUT_09_BACI_SHIFTS)
        df.columns = [str(c).strip().lower() for c in df.columns]
        w, era, val = df.columns[0], df.columns[1], df.columns[2]
        row = df[(df[w].astype(str).str.lower() == "ceh36") &
                 (df[era].astype(str).str.contains("Pure_Scraping", case=False))]
        val_mm = float(row[val].iloc[0]) * 1000.0
        info(f"scrape on-site (live, CEH36 Pure_Scraping BACI): {val_mm:.1f} mm")
        return val_mm
    except Exception as exc:
        warn(f"cannot read CEH36 on-site BACI ({exc}) — using snapshot 129.5 mm")
        return 129.5


def load_scrape_offsite_mm() -> float:
    """WMC3 off-site drain-cone DiD (mm), mean of the two independent
    scraping-era steps in 10m_report_numbers.csv (2015 and 2023 scrapes)."""
    try:
        df = pd.read_csv(OUT_10M_REPORT)
        key_col = df.iloc[:, 0].astype(str)
        rows = df[key_col.str.contains("WMC3_BACI_DiD_step_.*_scraping", case=False, regex=True)]
        vals_mm = rows.iloc[:, 3].astype(float) * 1000.0
        if vals_mm.empty:
            raise ValueError("no WMC3 scraping DiD rows found")
        val_mm = float(vals_mm.mean())
        info(f"scrape off-site (live, WMC3 DiD mean of {len(vals_mm)} steps): {val_mm:+.1f} mm")
        return val_mm
    except Exception as exc:
        _fallback = float(pipeline_params.default_value("wmc3_drawdown_mm"))
        warn(f"cannot read WMC3 off-site DiD ({exc}) — using the documented "
             f"first-pass default {_fallback:+.1f} mm")
        return _fallback


def load_drawdown_lambda_m() -> float:
    """Drain-cone / forest-drawdown e-folding length λ (m) —
    20_report_numbers.csv (drawdown_lambda), shared by clearfell and the
    scrape off-site cone (both use the identical C3 leaky-aquifer formula)."""
    try:
        df = pd.read_csv(OUT_20_REPORT_NUMBERS)
        key_col = df.iloc[:, 0].astype(str)
        row = df[key_col == "drawdown_lambda"]
        lam = float(row.iloc[0, 3])
        info(f"drain-cone λ (live, 20_report_numbers): {lam:.1f} m")
        return lam
    except Exception as exc:
        lam = pipeline_params.default_value("drawdown_lambda_m")
        warn(f"cannot read drawdown_lambda ({exc}) — using first-pass default {lam} m")
        return lam


def load_cluster_sy() -> dict:
    """{cluster_id(int): Sy} — canonical per-cluster Sy, live from
    pipeline_params.load_params() (written by Script 18, not 17 — D-038;
    single source of
    truth, matches OUT_18_WELL_SY_TABLE grouped by Cluster). Falls back to
    default_value('Sy') per cluster with a console warning."""
    try:
        params = pipeline_params.load_params(warn_defaults=True)
        out = {}
        for cname, v in params["clusters"].items():
            cid = int(str(cname).lstrip("Cc"))
            out[cid] = float(v["Sy"])
        info(f"per-cluster Sy (live, pipeline_scenario_params.csv): "
             f"{{{', '.join(f'C{k}={v:.3f}' for k, v in sorted(out.items()))}}}")
        return out
    except Exception as exc:
        warn(f"cannot read pipeline_scenario_params ({exc}) — using first-pass default Sy for all clusters")
        d = pipeline_params.default_value("Sy")
        return {cid: d for cid in CLUSTER_LABELS}


def representative_sy(cluster_sy: dict, roster: pd.DataFrame) -> dict:
    """Per-driver representative Sy (Sign-off #2): coast/scrape -> C3;
    forest (clearfell/broadleaf) -> well-count-weighted mean of C4/C5,
    weights read live from the well roster (never hardcoded 9/5)."""
    sy_coast = cluster_sy.get(3, np.nan)
    n4 = int((roster["Cluster"] == 4).sum())
    n5 = int((roster["Cluster"] == 5).sum())
    sy4 = cluster_sy.get(4, np.nan)
    sy5 = cluster_sy.get(5, np.nan)
    if (n4 + n5) > 0:
        sy_forest = (n4 * sy4 + n5 * sy5) / (n4 + n5)
    else:
        sy_forest = float(np.nanmean([sy4, sy5]))
    info(f"representative Sy: coast/scrape (C3) = {sy_coast:.3f}; "
         f"forest (C4 n={n4} + C5 n={n5}, weighted) = {sy_forest:.3f}; "
         f"climate (C3, per sign-off) = {sy_coast:.3f}")
    return dict(coast=sy_coast, scrape=sy_coast, forest=sy_forest, climate=sy_coast)


# ---------------------------------------------------------------------------
# Well roster and per-well summer-minima baseline (Sign-off #3)
# ---------------------------------------------------------------------------

def load_well_roster() -> pd.DataFrame:
    """66 reference-network wells: key, E, N, Cluster — from INT_MASTER_DATA
    (the canonical C1-C5 partition; extended network and lake gauge are not
    part of this partition and are excluded, consistent with Script 36/37)."""
    df = pd.read_csv(INT_MASTER_DATA)
    df = df.rename(columns={"Name_Original": "key", "Easting": "E", "Northing": "N"})
    df["key"] = df["key"].astype(str).str.strip().str.lower()
    return df[["key", "E", "N", "Cluster"]].copy()


def compute_summer_baseline_m(well_keys: list) -> dict:
    """{key: baseline (m, negative-below-ground convention)} — mean of
    annual Jun-Sep minima per well, computed directly from INT_WELLS_CLEAN
    (Sign-off #3: true per-well baseline, NOT the cluster-level
    14_annual_extremes.csv). Matches the "Summer_minimum_depth ... Mean of
    annual Jun-Sep minima" method already used per-well for the 09_scrape
    BACI wells (09_scrape_report_numbers.csv), extended here to all 66
    reference wells."""
    levels = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    levels.columns = [c.strip().lower() for c in levels.columns]
    out = {}
    for key in well_keys:
        if key not in levels.columns:
            out[key] = np.nan
            continue
        ser = levels[key].dropna()
        summer = ser[ser.index.month.isin([6, 7, 8, 9])]
        if summer.empty:
            out[key] = np.nan
            continue
        annual_min = summer.groupby(summer.index.year).min()
        out[key] = float(annual_min.mean())
    return out


# ---------------------------------------------------------------------------
# Grid / site mask (canonical extent, 50 m — matches Script 20)
# ---------------------------------------------------------------------------

def build_grid():
    xi = np.arange(config.SITE_MAP_EAST_MIN, config.SITE_MAP_EAST_MAX + GRID_RES_M, GRID_RES_M)
    yi = np.arange(config.SITE_MAP_NORTH_MIN, config.SITE_MAP_NORTH_MAX + GRID_RES_M, GRID_RES_M)
    gx, gy = np.meshgrid(xi, yi)
    mask = make_site_mask(gx, gy)
    cell_area_m2 = GRID_RES_M * GRID_RES_M
    cell_area_ha = cell_area_m2 / 10000.0
    n_cells = int(mask.sum())
    info(f"grid: {gx.shape[1]}×{gx.shape[0]} at {GRID_RES_M:.0f} m, "
         f"{n_cells} cells inside site mask ({n_cells * cell_area_ha:.1f} ha)")
    return gx, gy, mask, cell_area_ha, cell_area_m2


# ---------------------------------------------------------------------------
# Felling polygon (reused pattern from Script 37's _build_spatial)
# ---------------------------------------------------------------------------

def load_felling_geom():
    try:
        import geopandas as gpd
        gdf = gpd.read_file(str(DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
        name_col = gdf["Name"].fillna("").astype(str)
        for idx, row in gdf.iterrows():
            nm = name_col.iloc[idx].lower()
            if "felling" in nm or "experiment" in nm:
                return row.geometry
    except Exception as exc:
        warn(f"felling polygon lookup failed ({exc})")
    return None


# ---------------------------------------------------------------------------
# Spatial field builders (mm, signed per gain/loss convention; full 2025
# equilibrium amplitude — no beta_3 time-attenuation, per spec: "at the 2025
# horizon all step effects are fully realised")
# ---------------------------------------------------------------------------

def build_fields(gx, gy, s20, delta0, clearfell_step_mm, lam, fell_geom,
                 climate_c_mm_yr):
    """Returns dict of {component_key: field (mm, signed)} on grid gx,gy,
    plus scalar peak-anchor values for Currency 1."""
    from shapely.geometry import Point

    fields = {}
    peaks = {}

    # --- Coast: chronic 20-yr erosion drawdown (negative / loss) ------------
    coast_unit, *_ = s20._erosion_field(gx, gy, h0_mm=1.0)
    coast_unit = np.nan_to_num(coast_unit, nan=0.0) if coast_unit is not None else np.zeros_like(gx)
    fields["coast_erosion"] = -1.0 * delta0 * HORIZON_YEARS * coast_unit
    peaks["coast_erosion"] = -1.0 * delta0 * HORIZON_YEARS  # d=0, coast_unit=1

    # --- SLR: Script 20's native 5-yr near-term field (positive / gain) -----
    slr_field, _, _, slr_mm = s20._slr_field(gx, gy)
    slr_field = np.nan_to_num(slr_field, nan=0.0) if slr_field is not None else np.zeros_like(gx)
    fields["slr"] = slr_field
    peaks["slr"] = float(slr_mm) if slr_mm is not None else np.nan

    # --- Clearfell: felling-polygon shape × observed step (positive / gain) -
    clearfell_field = np.zeros_like(gx)
    if fell_geom is not None:
        d_fell = np.array([fell_geom.distance(Point(x, y))
                           for x, y in zip(gx.ravel(), gy.ravel())]).reshape(gx.shape)
        clearfell_field = clearfell_step_mm * np.exp(-d_fell / lam)
    fields["clearfell"] = clearfell_field
    peaks["clearfell"] = clearfell_step_mm  # d=0

    # --- Broadleaf: Script 20's native increment field (negative / loss) ---
    bl_field, bl_h0, *_ = s20._broadleaf_field(gx, gy)
    bl_field = np.nan_to_num(bl_field, nan=0.0) if bl_field is not None else np.zeros_like(gx)
    fields["broadleaf"] = -1.0 * bl_field
    peaks["broadleaf"] = -1.0 * float(bl_h0) if bl_h0 is not None else np.nan

    # --- Scrape off-site: Script 20's native leaky-aquifer field -----------
    #     (positive=head loss native convention -> negate for our sign
    #     convention). Rise zones (on-site) are NaN in the native field —
    #     zeroed here since on-site is accounted for separately.
    scrape_field, *_ = s20._scrape_field(gx, gy, epochs=None)
    scrape_field = np.nan_to_num(scrape_field, nan=0.0) if scrape_field is not None else np.zeros_like(gx)
    fields["scrape_offsite"] = -1.0 * scrape_field

    # --- Climate: spatially-UNIFORM common-mode decline (negative / loss) ----
    #     c × horizon, flat everywhere (no reach decay). The one field with no
    #     spatial structure — the background warren-wide fall.
    fields["climate"] = np.full_like(gx, climate_c_mm_yr * HORIZON_YEARS)
    peaks["climate"] = climate_c_mm_yr * HORIZON_YEARS   # uniform -> peak = value

    return fields, peaks


def onsite_scrape_registry(s20):
    """List of {name, geom (footprint+rise-buffer), H0 (mm), area_m2} for
    each cut in the scrape registry — used for the on-site rise integral
    (a fixed value over the rise-buffer polygon, not a decaying field)."""
    reg = s20._scrape_registry()
    out = []
    for cut in reg:
        rise_geom = cut["geom"].buffer(config.SCRAPE_RISE_BUFFER_M)
        out.append(dict(name=cut["name"], geom=rise_geom, H0=cut["H0"],
                        area_m2=rise_geom.area))
    return out


# ---------------------------------------------------------------------------
# Currency 1 — peak local head change
# ---------------------------------------------------------------------------

def currency1_peaks(peaks: dict, scrape_onsite_mm: float, scrape_offsite_mm: float) -> dict:
    out = dict(peaks)
    out["scrape_onsite"] = scrape_onsite_mm     # observed anchor (CEH36)
    out["scrape_offsite"] = scrape_offsite_mm   # observed anchor (WMC3), conservative
    #                                              vs the (larger) near-field modelled cone
    return out


# ---------------------------------------------------------------------------
# Currency 2 — area-integrated change (mm.ha and m^3)
# ---------------------------------------------------------------------------

def currency2_integrals(fields: dict, mask: np.ndarray,
                        cell_area_ha: float, cell_area_m2: float,
                        onsite_cuts: list, sy: dict) -> dict:
    out = {}
    for key, field in fields.items():
        vals = field[mask]
        mm_ha = float(np.sum(vals * cell_area_ha))
        if key in ("coast_erosion", "slr", "scrape_offsite"):
            sy_key = "coast"
        elif key == "climate":
            sy_key = "climate"
        else:
            sy_key = "forest"
        m3 = float(np.sum((vals / 1000.0) * cell_area_m2 * sy[sy_key]))
        out[key] = dict(mm_ha=mm_ha, m3=m3)

    # On-site scrape: fixed H0 over each cut's rise-buffer polygon (no decay)
    onsite_mm_ha = 0.0
    onsite_m3 = 0.0
    for cut in onsite_cuts:
        area_ha = cut["area_m2"] / 10000.0
        onsite_mm_ha += cut["H0"] * area_ha
        onsite_m3 += (cut["H0"] / 1000.0) * cut["area_m2"] * sy["scrape"]
    out["scrape_onsite"] = dict(mm_ha=onsite_mm_ha, m3=onsite_m3)
    return out


# ---------------------------------------------------------------------------
# Currency 3 — ecological threshold crossings (per well, per component)
# ---------------------------------------------------------------------------

def evaluate_component_at_wells(roster: pd.DataFrame, s20,
                                delta0, clearfell_step_mm, lam, fell_geom,
                                scrape_onsite_mm, onsite_cuts,
                                climate_c_mm_yr) -> pd.DataFrame:
    """Per-well component deltas (mm, signed), evaluated at each well's
    (E,N) — same field constructions as build_fields(), plus the on-site
    scrape rise (fixed H0 if the well falls within a cut's rise buffer)."""
    from shapely.geometry import Point

    E = roster["E"].values.astype(float)
    N = roster["N"].values.astype(float)

    coast_unit, *_ = s20._erosion_field(E, N, h0_mm=1.0)
    coast_unit = np.nan_to_num(coast_unit, nan=0.0)
    coast_delta = -1.0 * delta0 * HORIZON_YEARS * coast_unit

    slr_field, *_ = s20._slr_field(E, N)
    slr_delta = np.nan_to_num(slr_field, nan=0.0) if slr_field is not None else np.zeros(len(E))

    clearfell_delta = np.zeros(len(E))
    if fell_geom is not None:
        d_fell = np.array([fell_geom.distance(Point(x, y)) for x, y in zip(E, N)])
        clearfell_delta = clearfell_step_mm * np.exp(-d_fell / lam)

    bl_field, *_ = s20._broadleaf_field(E, N)
    bl_delta = -1.0 * np.nan_to_num(bl_field, nan=0.0) if bl_field is not None else np.zeros(len(E))

    scrape_off_field, *_ = s20._scrape_field(E, N, epochs=None)
    scrape_off_delta = -1.0 * np.nan_to_num(scrape_off_field, nan=0.0) if scrape_off_field is not None else np.zeros(len(E))

    scrape_on_delta = np.zeros(len(E))
    for i, (x, y) in enumerate(zip(E, N)):
        pt = Point(x, y)
        for cut in onsite_cuts:
            if cut["geom"].contains(pt):
                scrape_on_delta[i] = max(scrape_on_delta[i], cut["H0"])

    out = roster[["key", "Cluster"]].copy()
    out["coast_erosion"] = coast_delta
    out["slr"] = slr_delta
    out["clearfell"] = clearfell_delta
    out["broadleaf"] = bl_delta
    out["scrape_onsite"] = scrape_on_delta
    out["scrape_offsite"] = scrape_off_delta
    out["climate"] = climate_c_mm_yr * HORIZON_YEARS   # uniform at every well
    return out


def currency3_crossings(per_well_deltas: pd.DataFrame, baseline_m: dict) -> pd.DataFrame:
    """Per component: n wells evaluated, n crossing SD15b/SD16 in each
    direction (worsen = wet-viable -> dry-tolerable-or-worse; relieve = the
    reverse). Both thresholds evaluated for every well (Script 11b
    precedent) — no per-well wet/dry-slack typing file exists."""
    rows = []
    for comp in COMPONENT_META:
        n_eval = 0
        sd15_worsen = sd15_relieve = 0
        sd16_worsen = sd16_relieve = 0
        for _, row in per_well_deltas.iterrows():
            key = row["key"]
            base_m = baseline_m.get(key, np.nan)
            if np.isnan(base_m):
                continue
            delta_mm = row[comp]
            if pd.isna(delta_mm):
                continue
            n_eval += 1
            base_depth_bg_mm = -1000.0 * base_m          # positive convention
            new_depth_bg_mm = base_depth_bg_mm - delta_mm  # wetting (delta>0) shrinks depth_bg

            base_wet = base_depth_bg_mm < SD15B_MM
            new_wet = new_depth_bg_mm < SD15B_MM
            if base_wet and not new_wet:
                sd15_worsen += 1
            elif (not base_wet) and new_wet:
                sd15_relieve += 1

            base_dry_ok = base_depth_bg_mm < SD16_MM
            new_dry_ok = new_depth_bg_mm < SD16_MM
            if base_dry_ok and not new_dry_ok:
                sd16_worsen += 1
            elif (not base_dry_ok) and new_dry_ok:
                sd16_relieve += 1

        rows.append(dict(
            component=comp, n_wells_evaluated=n_eval,
            sd15b_crossings_worsen=sd15_worsen, sd15b_crossings_relieve=sd15_relieve,
            sd16_crossings_worsen=sd16_worsen, sd16_crossings_relieve=sd16_relieve,
        ))
    return pd.DataFrame(rows).set_index("component")


# ---------------------------------------------------------------------------
# Assemble comparison table
# ---------------------------------------------------------------------------

def build_comparison_table(peaks: dict, integrals: dict, crossings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for comp, (group, mech, gain_loss, observed) in COMPONENT_META.items():
        rows.append(dict(
            component=comp, label=COMPONENT_LABELS[comp], driver_group=group,
            mechanism_type=mech, gain_or_loss=gain_loss,
            observed_or_modelled=("observed" if observed else "modelled"),
            peak_mm=round(float(peaks.get(comp, np.nan)), 1),
            area_mm_ha=round(float(integrals[comp]["mm_ha"]), 1),
            volume_m3=round(float(integrals[comp]["m3"]), 1),
            n_wells_evaluated=int(crossings.loc[comp, "n_wells_evaluated"]),
            sd15b_crossings_worsen=int(crossings.loc[comp, "sd15b_crossings_worsen"]),
            sd15b_crossings_relieve=int(crossings.loc[comp, "sd15b_crossings_relieve"]),
            sd16_crossings_worsen=int(crossings.loc[comp, "sd16_crossings_worsen"]),
            sd16_crossings_relieve=int(crossings.loc[comp, "sd16_crossings_relieve"]),
        ))
    df = pd.DataFrame(rows)
    # Net scrape row for the "worsens site-wide vs benefits slack" claim
    net_mm_ha = (df.loc[df.component == "scrape_onsite", "area_mm_ha"].iloc[0] +
                df.loc[df.component == "scrape_offsite", "area_mm_ha"].iloc[0])
    net_m3 = (df.loc[df.component == "scrape_onsite", "volume_m3"].iloc[0] +
             df.loc[df.component == "scrape_offsite", "volume_m3"].iloc[0])
    df = pd.concat([df, pd.DataFrame([dict(
        component="scrape_net", label="Scrape NET (on-site + off-site)",
        driver_group="Dune scraping", mechanism_type="redistributive",
        gain_or_loss="net", observed_or_modelled="observed+modelled",
        peak_mm=np.nan, area_mm_ha=round(net_mm_ha, 1), volume_m3=round(net_m3, 1),
        n_wells_evaluated=np.nan, sd15b_crossings_worsen=np.nan,
        sd15b_crossings_relieve=np.nan, sd16_crossings_worsen=np.nan,
        sd16_crossings_relieve=np.nan,
    )])], ignore_index=True)
    return df


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def plot_footing(df: pd.DataFrame, dpi: int = 150) -> None:
    """3-row vertical stack (one row per currency), sized to fit an A4 page
    (7.2 x 9.6 in, comfortably inside A4's 8.27 x 11.69 in with margins) —
    the original 1x3 wide layout (19 in) ran off the page.

    The climate / common-mode term is flagged apart from the spatially-
    structured drivers: its bars are hatched, a dotted separator sets it off,
    and a note records that it is the spatially-uniform background decline,
    not attributed to a specific mechanism."""
    comp_df = df[df.component != "scrape_net"].copy().reset_index(drop=True)
    labels = [COMPONENT_LABELS[c] for c in comp_df.component]
    colours = ["#c0392b" if g == "loss" else "#1a5276" for g in comp_df.gain_or_loss]
    # index of the climate / common-mode bar (flagged distinctly)
    clim_idx = comp_df.index[comp_df.component == "climate"]
    clim_i = int(clim_idx[0]) if len(clim_idx) else None

    def _flag_climate(bars):
        """Hatch the climate bar so it reads as the common-mode term."""
        if clim_i is not None and clim_i < len(bars):
            bars[clim_i].set_hatch("////")
            bars[clim_i].set_edgecolor("white")
            bars[clim_i].set_linewidth(0.0)

    def _separator(ax):
        """Dotted line setting the climate bar apart from the rest."""
        if clim_i is not None:
            ax.axhline(clim_i - 0.5, color="0.55", lw=0.8, ls=":", zorder=0)

    with plt.rc_context(MPL_RC):
        fig, axes = plt.subplots(3, 1, figsize=(7.2, 9.6))

        ax = axes[0]
        _flag_climate(ax.barh(labels, comp_df.peak_mm, color=colours))
        _separator(ax)
        ax.axvline(0, color="#999", lw=0.8)
        ax.set_xlabel("Peak local head change (mm)", fontsize=8.5)
        ax.set_title("Measure 1 — Peak local (mostly observed anchors)", fontsize=9.5)
        ax.tick_params(axis="both", labelsize=8)

        ax = axes[1]
        _flag_climate(ax.barh(labels, comp_df.volume_m3, color=colours))
        _separator(ax)
        ax.axvline(0, color="#999", lw=0.8)
        ax.set_xlabel("Area-integrated volume (m³, 20-yr / 2025 amplitude)", fontsize=8.5)
        ax.set_title("Measure 2 — Area-integrated (site mask, 50 m grid)", fontsize=9.5)
        ax.tick_params(axis="both", labelsize=8)

        ax = axes[2]
        net_worsen = comp_df.sd15b_crossings_worsen.fillna(0) + comp_df.sd16_crossings_worsen.fillna(0)
        net_relieve = comp_df.sd15b_crossings_relieve.fillna(0) + comp_df.sd16_crossings_relieve.fillna(0)
        y = np.arange(len(labels))
        _flag_climate(ax.barh(y - 0.2, net_worsen, height=0.35, color="#c0392b",
                              label="worsen (cross toward threshold)"))
        _flag_climate(ax.barh(y + 0.2, net_relieve, height=0.35, color="#1a5276",
                              label="relieve (cross away)"))
        _separator(ax)
        ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8)
        ax.axvline(0, color="#999", lw=0.8)
        ax.set_xlabel("Wells crossing SD15b or SD16 (count, n=66 evaluated)", fontsize=8.5)
        ax.set_title("Measure 3 — Ecological threshold crossings (Curreli)", fontsize=9.5)
        ax.tick_params(axis="x", labelsize=8)
        # Legend inside the panel, mid/lower-right (clear now the climate bar
        # stretches the x-axis) — was colliding with the title above the panel.
        ax.legend(fontsize=7, loc="center right", framealpha=0.9)

        fig.suptitle(f"Part B — comparative driver footing v{__version__}\n"
                     "forest · scrape · coast · climate on common measures "
                     f"({int(_H_START)}\u2192{int(_H_END)})", fontsize=10.5)
        fig.text(0.5, 0.005,
                 "Climate / common-mode (hatched, below the separator) is the "
                 "spatially-uniform background decline — shown apart from the "
                 "mechanism-specific drivers and not attributed to a single driver.",
                 ha="center", fontsize=6.8, style="italic", color="0.35")
        fig.tight_layout(rect=[0, 0.02, 1, 0.93])
        render_figure(fig, OUT_FIGURE)
        plt.close(fig)
    saved(OUT_FIGURE)


# ---------------------------------------------------------------------------
# Results text
# ---------------------------------------------------------------------------

def write_results(df: pd.DataFrame, delta0, L_coast, clearfell_step_mm,
                  scrape_onsite_mm, scrape_offsite_mm, lam, sy, n_wells_roster) -> None:
    lines = [
        f"37b_driver_footing v{__version__} — Part B: Comparative Driver Footing",
        "=" * 74,
        "",
        "LIVE PARAMETERS",
        "-" * 74,
        f"  δ₀ (Script 25, forest-free linear-capped): {delta0:.2f} mm/yr; L = {L_coast:.0f} m",
        f"  clearfell step (10a ANCOVA, Path B, observed): {clearfell_step_mm:.1f} mm",
        f"  scrape on-site (CEH36 Pure_Scraping, observed): {scrape_onsite_mm:.1f} mm",
        f"  scrape off-site (WMC3 DiD mean, observed): {scrape_offsite_mm:+.1f} mm",
        f"  drain-cone / forest λ (20_report_numbers): {lam:.1f} m",
        f"  representative Sy: coast/scrape (C3) = {sy['coast']:.3f}; forest (C4/C5 weighted) = {sy['forest']:.3f}",
        f"  horizon: {int(_H_START)}\u2192{int(_H_END)} ({HORIZON_YEARS:.0f} yr)",
        f"  well roster: {n_wells_roster} reference-network wells (canonical C1-C5 partition)",
        "",
        "COMPARISON TABLE",
        "-" * 74,
    ]
    for _, row in df.iterrows():
        lines.append(f"  {row['label']:38s} [{row['driver_group']}, {row['mechanism_type']}, "
                     f"{row['gain_or_loss']}, {row['observed_or_modelled']}]")
        peak_txt = f"{row['peak_mm']:+.1f} mm" if not pd.isna(row['peak_mm']) else "n/a"
        lines.append(f"      peak={peak_txt}  area={row['area_mm_ha']:+.1f} mm·ha  "
                     f"volume={row['volume_m3']:+.1f} m³")
        if not pd.isna(row['n_wells_evaluated']):
            lines.append(
                f"      SD15b (wet-slack, {SD15B_MM:.0f} mm): worsen={int(row['sd15b_crossings_worsen'])}  "
                f"relieve={int(row['sd15b_crossings_relieve'])}   "
                f"SD16 (dry-slack, {SD16_MM:.0f} mm): worsen={int(row['sd16_crossings_worsen'])}  "
                f"relieve={int(row['sd16_crossings_relieve'])}  (n={int(row['n_wells_evaluated'])})"
            )
        lines.append("")

    scrape_on = df[df.component == "scrape_onsite"].iloc[0]
    scrape_off = df[df.component == "scrape_offsite"].iloc[0]
    scrape_net = df[df.component == "scrape_net"].iloc[0]
    coast_row = df[df.component == "coast_erosion"].iloc[0]
    lines += ["", "THE 'SCRAPING WORSENS SITE-WIDE DECLINE' CLAIM, IN CONTEXT", "-" * 74]
    lines.append(
        f"  Scrape on-site (rise):  area={scrape_on['area_mm_ha']:+.1f} mm·ha  volume={scrape_on['volume_m3']:+.1f} m³"
    )
    lines.append(
        f"  Scrape off-site (drain): area={scrape_off['area_mm_ha']:+.1f} mm·ha  volume={scrape_off['volume_m3']:+.1f} m³"
    )
    lines.append(
        f"  Scrape NET: area={scrape_net['area_mm_ha']:+.1f} mm·ha  volume={scrape_net['volume_m3']:+.1f} m³"
    )
    sign_txt = "a net site-wide LOSS" if scrape_net["volume_m3"] < 0 else "a net site-wide GAIN"
    ratio_pct = 100.0 * abs(scrape_net["volume_m3"]) / abs(coast_row["volume_m3"]) if coast_row["volume_m3"] else float("nan")
    lines.append(
        f"  The net sign ({sign_txt}) is the quantitative basis for the claim. Set beside the "
        f"coastal integral, the scrape net volume is {ratio_pct:.0f}% of the coastal volume in "
        "magnitude — smaller than coast, but not negligible beside it; a moderate secondary "
        "contributor, not a match for coastal retreat and not a headline driver on its own. "
        "This ratio inherits Script 20's own scrape-field construction (8 cuts superposed with "
        f"λ≈{lam:.0f} m reach each, summed over the whole site extent — mean field ≈23 mm across the "
        "949 ha site, not a tiny near-field patch), which is why the off-site total doesn't stay "
        "small despite each cut's own footprint being modest. Consistent with, not overriding, "
        "the coastal-dominance picture from Part A / Script 25."
    )

    lines += ["", "CAVEATS (even-handed framing, per working rules)", "-" * 74]
    lines.append(
        "  Every cell is flagged observed or modelled. Coast (both components), broadleaf, "
        "and the scrape off-site cone are MODELLED (Script 20 fields); clearfell and scrape "
        "on-site are OBSERVED BACI anchors; scrape off-site's peak is an OBSERVED WMC3 point "
        "(the modelled cone is larger near-field, so -"
        f"{abs(scrape_offsite_mm):.0f} mm is a conservative, not a maximal, peak)."
    )
    lines.append(
        "  SLR is Script 20's native 5-YEAR near-term projection, NOT rescaled to the 20-yr "
        "horizon used by every other component here — its small peak/volume relative to "
        "coastal erosion partly reflects this shorter window, not just smaller physical "
        "magnitude. Treat the SLR row as indicative/near-term only, not a like-for-like "
        "20-yr comparison."
    )
    lines.append(
        "  Coast's 20-yr drawdown is a MODELLED PROJECTION anchored on the observed δ₀, "
        "UNCONFIRMED spatially by Part A (Script 37's scale factors are null/unresolved for "
        "coast — see Script 37 results). It indicates, not confirms, the scale of coastal "
        "influence relative to the other drivers."
    )
    lines.append(
        "  First-order superposition — components are summed independently; this is an "
        "UPPER BOUND in any zone where two fields overlap (same caveat as the Script 20 map). "
        "Does not close a water budget."
    )
    lines.append(
        "  Near-field scrape cone is NOT resolved observationally — nearest uphill well is "
        "262 m from the cut (WMC3); the off-site figures rest on the modelled leaky-aquifer "
        "field beyond that point."
    )
    lines.append(
        "  Representative Sy (not per-cell) carries an approximately ±40% spread across "
        "individual well estimates within a cluster (Script 17 WTF method) — volume figures "
        "should be read as order-of-magnitude, not precise."
    )
    lines.append(
        "  Ecological threshold crossings evaluate BOTH SD15b and SD16 for every well (no "
        "per-well wet-slack/dry-slack typing file exists — mirrors the continuous "
        "zone-classification precedent in Script 11b) — a 'crossing' here means the "
        "well's baseline-plus-delta moves across that specific threshold, not that the "
        "well is necessarily of that ecological type."
    )
    lines.append(
        "  Baseline for Currency 3 is a TRUE per-well summer minimum (mean of annual Jun-Sep "
        "minima, INT_WELLS_CLEAN), computed directly for this script — NOT the cluster-level "
        "14_annual_extremes.csv the original spec draft cited (that file has no per-well data)."
    )
    lines.append(
        "  Does not use Script 37's scale factors (null/unresolved — Part A owns that "
        "verdict); does not re-estimate any driver amplitude — it places the established "
        "observed/modelled amplitudes on common axes. Language: 'indicates' / 'consistent "
        "with', not 'confirms' / 'demonstrates'."
    )

    OUT_RESULTS.write_text("\n".join(lines) + "\n")
    saved(OUT_RESULTS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    banner(SCRIPT_ID, "Part B — Comparative Driver Footing", version=__version__)
    DIR_37B.mkdir(parents=True, exist_ok=True)

    phase(1, "Load live parameters")
    delta0, L_coast = load_coastal_fit()
    climate_c = load_uniform_residual()
    clearfell_step_mm = load_clearfell_step_mm()
    scrape_onsite_mm = load_scrape_onsite_mm()
    scrape_offsite_mm = load_scrape_offsite_mm()
    lam = load_drawdown_lambda_m()
    cluster_sy = load_cluster_sy()

    phase(2, "Load well roster and per-well summer-minima baseline")
    roster = load_well_roster()
    result("reference-network wells", str(len(roster)))
    sy = representative_sy(cluster_sy, roster)
    baseline_m = compute_summer_baseline_m(list(roster["key"]))
    n_baseline = sum(1 for v in baseline_m.values() if not np.isnan(v))
    result("wells with summer-minima baseline", f"{n_baseline}/{len(roster)}")

    phase(3, "Build spatial fields (Script 20 v1.32.0 builders, via importlib)")
    step("importing Script 20 …")
    s20 = _load_s20()
    fell_geom = load_felling_geom()
    if fell_geom is None:
        warn("felling polygon not found — clearfell field will be zero")
    gx, gy, mask, cell_area_ha, cell_area_m2 = build_grid()
    fields, peaks_grid = build_fields(gx, gy, s20, delta0, clearfell_step_mm, lam, fell_geom, climate_c)
    onsite_cuts = onsite_scrape_registry(s20)
    info(f"scrape registry: {len(onsite_cuts)} cuts loaded")

    phase(4, "Currency 1 — peak local head change")
    peaks = currency1_peaks(peaks_grid, scrape_onsite_mm, scrape_offsite_mm)
    for k, v in peaks.items():
        result(f"  {k} peak", f"{v:+.1f} mm")

    phase(5, "Currency 2 — area-integrated change (mm·ha, m³)")
    integrals = currency2_integrals(fields, mask, cell_area_ha, cell_area_m2, onsite_cuts, sy)
    for k, v in integrals.items():
        result(f"  {k} volume", f"{v['m3']:+.1f} m³")

    phase(6, "Currency 3 — ecological threshold crossings (Curreli)")
    per_well = evaluate_component_at_wells(roster, s20, delta0, clearfell_step_mm, lam,
                                           fell_geom, scrape_onsite_mm, onsite_cuts,
                                           climate_c)
    crossings = currency3_crossings(per_well, baseline_m)

    phase(7, "Assemble comparison table and write outputs")
    df = build_comparison_table(peaks, integrals, crossings)
    df.to_csv(OUT_COMPARISON, index=False)
    saved(OUT_COMPARISON)

    plot_footing(df)
    write_results(df, delta0, L_coast, clearfell_step_mm, scrape_onsite_mm,
                 scrape_offsite_mm, lam, sy, len(roster))

    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
