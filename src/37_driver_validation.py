"""
37_driver_validation.py
=======================
Sequential driver calibration on a spring-MAM basis.

Each driver is calibrated in its virgin window — the earliest window where that
driver acts alone — frozen, then subtracted before the next driver is fitted.
This breaks the collinearity between coastal, scrape, and clearfell signals
that made the v1.x single-window simultaneous calibration unstable.

Stage | Window      | New driver isolated              | Calibrate                | Well set
------+-------------+----------------------------------+--------------------------+---------------------------
  1   | 2006–2012   | Coastal retreat + SLR            | δ₀·R (effective retreat) | coastal-exposed ref-net wells with pre-2006 data
  2   | 2015–2017   | CEH36 scrape (Apr 2015)          | scrape amplitude scale   | CEH36 / CEH18 / CEH21 only
  3   | 2017–2025   | Clearfell (Dec 2017)             | clearfell amplitude + λ  | forest wells (C4/C5)

Inputs:
  36_absolute_climate_trend_per_well.csv — spring-MAM slopes for each calibration
      window (slope_mm_yr_2006_2012, slope_mm_yr_2015_2017, slope_mm_yr_2017_2025).
      FAIL-FAST if any required column is absent (rerun Script 36 with the
      sequential windows in config.ACT_PERIODS).

Key outputs:
  37_calibration_table.csv   — driver → window → fitted value → 90 % CI
  37_per_well.csv            — per-stage observed, frozen-subtracted, residual
  37_scatter_stage1.png      — Stage 1 coastal scatter (2006–2012)
  37_scatter_stage2.png      — Stage 2 scrape scatter (2015–2017)
  37_scatter_stage3.png      — Stage 3 clearfell scatter (2017–2025)
  37_scatter_fullwindow.png  — full-window validation with calibrated constants
  37_residual_map.png        — IDW residual map (2005–2025 full window)
  37_results.txt             — summary statistics and calibrated constants

v1.x findings are NOT overwritten — they inform the paper as motivation for the
sequential approach (2005–2025 r=0.595; 2011–2025 r=0.285).

Step 40/46, Phase 15 — Observed Differential Change, Envelope, and Validation.
"""

__version__ = "2.1.0"  # 2026-07-06: consume climate-corrected endpoint difference
#                       dh_corr_<window> (mm) from Script 36 v1.1.0+ as the driver
#                       signal, replacing slope_mm_yr × T_years (which overfit short
#                       windows). Stages 1/2/3 read dh_corr directly; full-window
#                       validation keeps the long-window 2005–2025 slope × 20yr.
# 2.0.4 — 2026-07-06: results title, scatter box, full-window labels use __version__.
                       # result labels now use __version__ dynamically (were
                       # hard-coded "v2.0.0", making every results file falsely
                       # report v2.0.0 regardless of actual version).
# 2.0.3 — 2026-07-06: cap bootstrap block size at nobs//2.
                       # to fix shape mismatch on small Stage 3 well sets (n=5–7).
# 2.0.2 — 2026-07-06: add CEH13 to EXCL_NAMED (rock ridge).
                       # near-zero β₃, hydraulically decoupled from main dune
                       # aquifer. CEH14 already excluded via β₃ ≤ 0 flag.
# 2.0.1 — 2026-07-06: degraded-mode operation when Stage 1/2 slope columns absent.
                       # slope columns are absent from Script 36 CSV. Stage 3
                       # (2017_2025) remains hard-required. Stages 1/2 absent
                       # → warn and use config priors (R=COAST_RETREAT_EFFECTIVE_M,
                       # scrape scale=1.0). Full calibration still runs when all
                       # columns are present.
# 2.0.0 — 2026-07-06: full replacement — sequential driver calibration.
# 2.0.0 — 2026-07-06: full replacement — sequential driver calibration on
#          spring-MAM basis (Stage 1: coastal 2006–2012; Stage 2: CEH36
#          scrape 2015–2017; Stage 3: clearfell 2017–2025). Requires Script 36
#          to emit slope_mm_yr_2006_2012, slope_mm_yr_2015_2017,
#          slope_mm_yr_2017_2025.  Stage-3 λ diagnostic-only (never written to
#          config.py).  COAST_RETREAT_EFFECTIVE_M updated in config.py from
#          Stage-1 calibration.  Bootstrap CI 90 % (5th–95th percentile).
# 1.1.0 — 2026-07-06: 2011–2025 window; COAST_RETREAT_EFFECTIVE_M calibrated;
#          SLR erfc; four named exclusions. (superseded by 2.0.0)
# 1.0.3 — write_results fix.
# 1.0.2 — load_master_b3 key fix.
# 1.0.1 — clearfell felling-polygon geometry.
# 1.0.0 — initial release.

import os
import sys
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path
from scipy.stats import pearsonr

from utils import config, paths
from utils.paths import (
    INT_LOCATIONS, INT_MASTER_DATA, INT_WELLS_CLEAN,
    OUT_36_PER_WELL,
    OUT_10A_REPORT,
    OUT_25_FIT_PARAMETERS,
)
from utils.config import (
    CLUSTER_LABELS, CLUSTER_MARKERS,
    DRAWDOWN_K_MDAY, DRAWDOWN_B_M,
    BL_CANOPY_FRACTION_2005, BL_CANOPY_FRACTION_2025,
    COAST_RETREAT_RATE,
)
from utils.clearfell_common import (
    INTERVENTION_DATE,
    SCRAPING_DATE, SCRAPING_DATE_2, SCRAPING_DATE_0,
)
from utils.map_utils import (
    load_dem_hillshade, add_idw_surface, add_en_axes, add_kml_features,
)
from utils.console_utils import banner, phase, step, info, note, warn, result, saved, done

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
DIR_37           = paths.DIR_37
OUT_CAL_TABLE    = DIR_37 / "37_calibration_table.csv"
OUT_PER_WELL     = paths.OUT_37_PER_WELL         # 37_driver_validation_per_well.csv
OUT_SCATTER_S1   = DIR_37 / "37_scatter_stage1.png"
OUT_SCATTER_S2   = DIR_37 / "37_scatter_stage2.png"
OUT_SCATTER_S3   = DIR_37 / "37_scatter_stage3.png"
OUT_SCATTER_FULL = paths.OUT_37_SCATTER          # 37_predicted_vs_observed.png
OUT_RESIDUAL_MAP = paths.OUT_37_RESIDUAL_MAP
OUT_RESULTS      = paths.OUT_37_RESULTS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_ID      = "37"
DAYS_PER_MONTH = 30.4375

# Required slope columns from Script 36 (fail-fast if absent)
# Driver signal columns (Script 36 v1.1.0+): climate-corrected endpoint
# difference dh_corr_<window> (mm) — already a Δh, NOT a rate. Replaces the
# slope_mm_yr × T_years product, which overfit on short windows.
DH_CORR_COLS = {
    "stage1": "dh_corr_mm_2006_2012",
    "stage2": "dh_corr_mm_2015_2017",
    "stage3": "dh_corr_mm_2017_2025",
}
# Full-window validation still uses the long-window secular slope × T (the
# 2005–2025 slope is well-conditioned and physical).
FULL5_SLOPE_COL = "slope_mm_yr_2005_2025"
FULL5_T_YEARS   = 20.0

# Columns Script 37 requires from the Script 36 CSV (fail-fast checks these)
REQUIRED_COLS = {
    "stage1": DH_CORR_COLS["stage1"],
    "stage2": DH_CORR_COLS["stage2"],
    "stage3": DH_CORR_COLS["stage3"],
    "full5":  FULL5_SLOPE_COL,
}

# Analysis windows: (start_date, end_date, T_years)
WINDOWS = {
    "stage1": (pd.Timestamp("2006-01-01"), pd.Timestamp("2012-12-01"), 7.0),
    "stage2": (pd.Timestamp("2015-01-01"), pd.Timestamp("2017-12-01"), 3.0),
    "stage3": (pd.Timestamp("2017-01-01"), pd.Timestamp("2025-12-01"), 9.0),
    "full5":  (pd.Timestamp("2005-01-01"), pd.Timestamp("2025-12-01"), 20.0),
}

# Stage 2: restricted to CEH36/CEH18/CEH21 scraping wells only
STAGE2_KEYS = {"ceh36", "ceh18", "ceh21"}

# Stage 1: exclude wells with first observations after 2006 (no virgin coastal
# signal); coastal-exposed = C3 (Western Residual) + C5 (Coastal Forest)
STAGE1_COASTAL_CLUSTERS = {3, 5}

# SLR rate at Holyhead (~4 mm/yr); held fixed in Stage 1, not calibrated
SLR_RATE_MM_YR = 4.0

# Bootstrap settings (90 % CI, 5th–95th percentile — supplement convention)
BOOT_N     = int(config.DIFF_BOOT_N)
BOOT_BLOCK = int(config.DIFF_BOOT_BLOCK)
BOOT_SEED  = int(config.DIFF_BOOT_SEED)
BOOT_LO    = 5.0
BOOT_HI    = 95.0

# Named exclusions: shown in scatter but excluded from calibration / r/RMSE
EXCL_NAMED: dict[str, str] = {
    "ceh4":  "scrape-beneficiary / BACI control-well contamination",
    "wmc2":  "anomalous wetting — no identifiable mechanism",
    "nw9":   "relic slack — topographic amplification of coastal drying",
    "ceh20": "forest hollow — topographic amplification of clearfell recovery",
    "ceh13": "rock ridge — near-zero β₃ indicating hydraulic decoupling from main dune aquifer",
}

OUTLIER_THRESHOLD = 1.5

MPL_RC = {
    "font.family":       "sans-serif",
    "font.size":         10,
    "axes.spines.top":   False,
    "axes.spines.right": False,
}

# ---------------------------------------------------------------------------
# Script 20 import
# ---------------------------------------------------------------------------

def _load_s20():
    """Load Script 20 spatial figures module via importlib (numeric filename)."""
    path = Path(__file__).parent / "20_spatial_figures.py"
    spec = importlib.util.spec_from_file_location("_s20_spatial", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Live-value loaders
# ---------------------------------------------------------------------------

def _load_coastal_fit() -> tuple[float, float]:
    """δ₀ (mm/yr) and L (m) from Script 25 forest-free linear-capped row."""
    snapshot = (29.39, 971.0)
    try:
        df  = pd.read_csv(OUT_25_FIT_PARAMETERS)
        row = df[(df["source"] == "forest_free") & (df["model"] == "linear_capped")]
        if row.empty:
            row = df[(df["source"] == "full") & (df["model"] == "linear_capped")]
        if row.empty:
            warn("Script 25 CSV: no linear_capped row — using snapshot")
            return snapshot
        d0 = abs(float(row["delta_0_mm_yr"].iloc[0]))
        L  = float(row["L_m"].iloc[0])
        info(f"coastal fit (live): δ₀={d0:.2f} mm/yr, L={L:.0f} m")
        return d0, L
    except Exception as exc:
        warn(f"cannot read Script 25 fit ({exc}) — using snapshot")
        return snapshot


def _load_clearfell_step() -> float:
    """Clearfell ANCOVA step (mm) — Path B, from 10a_report_numbers.csv."""
    snapshot_mm = 119.6
    try:
        df      = pd.read_csv(OUT_10A_REPORT)
        key_col = df.iloc[:, 0].astype(str)
        row     = df[key_col == "ANCOVA_Forest_Impact_clearfell_step"]
        val_mm  = float(row.iloc[0, 3]) * 1000.0
        info(f"clearfell step (Path B, live): {val_mm:.1f} mm")
        return val_mm
    except Exception as exc:
        warn(f"cannot read 10a clearfell step ({exc}) — using {snapshot_mm:.1f} mm")
        return snapshot_mm


# ---------------------------------------------------------------------------
# β₃ temporal correction factors
# ---------------------------------------------------------------------------

def _ramp_factor(b3: float, T_months: float) -> float:
    """Fraction of linear ramp accumulation realised after T_months.
    Returns 1.0 when b3 ≤ 0 or T_months ≤ 0."""
    if b3 <= 0.0 or T_months <= 0.0:
        return 1.0
    x = b3 * T_months
    if x > 50.0:
        return 1.0
    return float(1.0 - (1.0 - np.exp(-x)) / x)


def _step_factor(b3: float, t_months: float) -> float:
    """Fraction of step-change equilibrium realised after t_months.
    Returns 0.0 for b3 ≤ 0; 1.0 for t_months ≤ 0."""
    if b3 <= 0.0:
        return 0.0
    if t_months <= 0.0:
        return 1.0
    return float(1.0 - np.exp(-b3 * t_months))


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _check_slope_columns(df: pd.DataFrame) -> set[str]:
    """Return set of stage labels whose slope column is absent from df.

    Stage 3 (2017_2025) is required — hard-fail if absent.
    Stages 1 and 2 are optional — warn and degrade to config priors.
    """
    missing_labels: set[str] = set()
    for label, col in REQUIRED_COLS.items():
        if col not in df.columns:
            missing_labels.add(label)
    if "stage3" in missing_labels:
        raise KeyError(
            f"Script 36 CSV is missing '{REQUIRED_COLS['stage3']}' (Stage 3 — required).\n"
            "Rerun Script 36 v1.1.0+ (step 39) with '2017_2025': (2017, 2025) in\n"
            "config.ACT_PERIODS so the climate-corrected dh_corr columns are emitted,\n"
            "then rerun Script 37."
        )
    for label in missing_labels - {"full5"}:
        warn(
            f"Driver column '{REQUIRED_COLS[label]}' absent from Script 36 CSV — "
            f"Stage '{label}' will use config priors (degraded mode)."
        )
    return missing_labels


def load_script36() -> tuple[pd.DataFrame, set[str]]:
    """Load Script 36 per-well CSV with all calibration window slopes.

    Returns (df, missing_labels) where missing_labels is the set of stage
    labels whose slope column was absent (empty set = all columns present).
    Stage 3 absent → raises KeyError.  Stages 1/2 absent → degraded mode.
    """
    df = pd.read_csv(OUT_36_PER_WELL)
    df["key"] = df["key"].str.strip().str.lower()
    missing = _check_slope_columns(df)

    # Patch E/N from INT_LOCATIONS for any wells missing coordinates
    if df[["E", "N"]].isna().any().any():
        try:
            locs = pd.read_csv(INT_LOCATIONS)
            id_col = next((c for c in ("key", "col", "Name_Original")
                           if c in locs.columns), None)
            if id_col:
                locs["_key"] = locs[id_col].astype(str).str.strip().str.lower()
                lut = locs.set_index("_key")[["E", "N"]].to_dict("index")
                for idx, row in df[df["E"].isna()].iterrows():
                    if row["key"] in lut:
                        df.loc[idx, "E"] = lut[row["key"]]["E"]
                        df.loc[idx, "N"] = lut[row["key"]]["N"]
        except Exception as exc:
            warn(f"could not patch E/N: {exc}")

    # Patch col display name
    df["col"] = df["col"].fillna(df["key"])
    return df, missing


def load_master_b3(well_keys: list[str]) -> dict[str, float]:
    """Return {key: beta_3_drainage (month⁻¹)} from INT_MASTER_DATA."""
    master = pd.read_csv(INT_MASTER_DATA)
    if "Name_Original" in master.columns:
        master["key"] = master["Name_Original"].astype(str).str.lower().str.strip()
    elif "key" in master.columns:
        master["key"] = master["key"].astype(str).str.lower().str.strip()
    else:
        warn("03_master_data.csv: no Name_Original/key column")
        return {k: np.nan for k in well_keys}
    lut = dict(zip(master["key"], master["beta_3_drainage"]))
    return {k: float(lut.get(k, np.nan)) for k in well_keys}


def load_well_spans(well_keys: list[str],
                    win_start: pd.Timestamp,
                    win_end: pd.Timestamp) -> dict[str, float]:
    """Return {key: T_months} observation span within [win_start, win_end]."""
    levels = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    levels.columns = [c.strip().lower() for c in levels.columns]
    out = {}
    for key in well_keys:
        if key not in levels.columns:
            out[key] = np.nan
            continue
        ser = levels[key].dropna()
        ser = ser[(ser.index >= win_start) & (ser.index <= win_end)]
        if ser.empty:
            out[key] = np.nan
            continue
        T = (ser.index.max() - win_start).days / DAYS_PER_MONTH
        out[key] = float(T)
    return out


# ---------------------------------------------------------------------------
# Bootstrap CI (90 %, 5th–95th percentile)
# ---------------------------------------------------------------------------

def _bootstrap_ci(x: np.ndarray, y: np.ndarray,
                  estimator, n: int = BOOT_N,
                  block: int = BOOT_BLOCK,
                  seed: int = BOOT_SEED) -> tuple[float, float]:
    """90 % CI via moving-block bootstrap on residuals of estimator(x, y).

    Block size is capped at max(1, nobs//2) when nobs < block to avoid
    shape mismatches on small calibration well sets (n=5–7).
    """
    rng  = np.random.default_rng(seed)
    hat  = estimator(x, y)
    res  = y - _predict(x, hat)
    nobs = len(res)
    blk  = min(block, max(1, nobs // 2))  # cap block for small n
    boots = []
    for _ in range(n):
        starts = rng.integers(0, max(nobs - blk + 1, 1), size=max(nobs // blk, 1))
        idx = np.concatenate([np.arange(s, min(s + blk, nobs)) for s in starts])[:nobs]
        y_b = _predict(x, hat) + res[idx]
        boots.append(estimator(x, y_b))
    boots = np.array(boots)
    return float(np.percentile(boots, BOOT_LO)), float(np.percentile(boots, BOOT_HI))


def _predict(x: np.ndarray, params) -> np.ndarray:
    """Linear prediction: params is a scalar multiplier or (intercept, slope)."""
    if np.isscalar(params):
        return params * x
    return params[0] + params[1] * x


def _ols_scale(x: np.ndarray, y: np.ndarray) -> float:
    """Single-parameter OLS: minimise ||y − a·x||². Returns scalar a."""
    denom = float(np.dot(x, x))
    if denom < 1e-12:
        return 1.0
    return float(np.dot(x, y)) / denom


def _ols_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Two-parameter OLS: y = intercept + slope·x. Returns (intercept, slope)."""
    A = np.column_stack([np.ones_like(x), x])
    try:
        coeffs, *_ = np.linalg.lstsq(A, y, rcond=None)
        return float(coeffs[0]), float(coeffs[1])
    except Exception:
        return 0.0, 1.0


# ---------------------------------------------------------------------------
# Spatial factors (reused from Script 20 field builders)
# ---------------------------------------------------------------------------

def _build_spatial(s20, E: np.ndarray, N: np.ndarray,
                   clearfell_step_mm: float, L_coast: float) -> dict:
    """
    Build equilibrium spatial fields at well locations.

    Returns dict with keys:
        coast_unit  — max(1−d/L, 0) [dimensionless]
        clearfell   — clearfell_step_mm × exp(−d_fell/λ) [mm]
        scr_2015    — scrape drawdown April 2015 [mm loss]
        broadleaf   — full 2005→2025 broadleaf increment [mm loss]
        fLam        — forest λ (m), for Stage-3 λ diagnostic
    """
    gx = np.asarray(E, dtype=float)
    gy = np.asarray(N, dtype=float)
    n  = len(gx)
    zeros = np.zeros(n)

    # Coastal unit field
    coast_res  = s20._erosion_field(gx, gy, h0_mm=1.0)
    coast_unit = np.nan_to_num(coast_res[0], nan=0.0) if coast_res[0] is not None else zeros.copy()

    # Forest λ
    for_result = s20._forest_field(gx, gy)
    fLam = float(for_result[2]) if (for_result[2] is not None) else None

    # Clearfell: felling polygon × exp(−d_fell/λ)
    clearfell = zeros.copy()
    if fLam is not None:
        try:
            import geopandas as gpd
            from shapely.geometry import Point as _Pt
            gdf = gpd.read_file(str(paths.DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
            name_col  = gdf["Name"].fillna("").astype(str)
            fell_geom = None
            for idx2, gdf_row in gdf.iterrows():
                nm = name_col.iloc[idx2].lower()
                if "felling" in nm or "experiment" in nm:
                    fell_geom = gdf_row.geometry
                    break
            if fell_geom is not None:
                d_fell    = np.array([fell_geom.distance(_Pt(x, y))
                                      for x, y in zip(gx.ravel(), gy.ravel())])
                clearfell = clearfell_step_mm * np.exp(-d_fell / fLam)
            else:
                warn("felling polygon not found in KML — clearfell spatial field zeroed")
        except Exception as exc:
            warn(f"clearfell field failed ({exc}) — zeroed")

    # Scrape April 2015 only (Stage 2 calibration target)
    def _scr(epoch_set):
        res = s20._scrape_field(gx, gy, epochs=epoch_set)
        if res[0] is None:
            return zeros.copy()
        return np.nan_to_num(res[0], nan=0.0)

    scr_2015 = _scr({"April 2015"})

    # Broadleaf full 2005→2025 increment
    bl_res    = s20._broadleaf_field(gx, gy)
    broadleaf = np.nan_to_num(bl_res[0], nan=0.0) if bl_res[0] is not None else zeros.copy()

    info(f"  coast_unit: {coast_unit.min():.3f}–{coast_unit.max():.3f}"
         f"  clearfell: {clearfell.min():.0f}–{clearfell.max():.0f} mm"
         f"  fLam={fLam:.0f} m" if fLam else "  fLam=None")

    return dict(coast_unit=coast_unit, clearfell=clearfell,
                scr_2015=scr_2015, broadleaf=broadleaf, fLam=fLam)


# ---------------------------------------------------------------------------
# Per-window observed Δh computation
# ---------------------------------------------------------------------------

def _observed_dh(df36: pd.DataFrame, slope_col: str, T_yrs: float) -> pd.Series:
    """Observed Δh (mm) = slope_mm_yr × T_years, indexed by key."""
    return df36.set_index("key")[slope_col] * T_yrs


# ---------------------------------------------------------------------------
# Stage 1: coastal + SLR (2006–2012)
# ---------------------------------------------------------------------------

def stage1_coastal(df36: pd.DataFrame,
                   b3_lut: dict[str, float],
                   spatial: dict,
                   delta0: float,
                   L_coast: float,
                   degraded: bool = False) -> dict:
    """
    Calibrate effective coastal retreat R from the 2006–2012 virgin window.

    If degraded=True (slope column absent from Script 36 CSV), skips
    calibration and returns R = config.COAST_RETREAT_EFFECTIVE_M (prior).

    Observed Δh (MAM, climate-removed) = coastal_pred + SLR_pred.
    SLR is fixed at SLR_RATE_MM_YR × T_yr (not calibrated).

    Coastal prediction per well:
        coast_eq   = R × δ₀/retreat_rate × coast_unit  [mm equilibrium amplitude]
        coast_pred = −coast_eq × ramp_factor(β₃, T_months)

    Calibrate R by single-parameter OLS: minimise ||y_residual − a × x_coast||²
    where y_residual = observed_dh − slr_pred.

    Returns dict with calibrated constants and per-well arrays.
    """
    R_prior = float(config.COAST_RETREAT_EFFECTIVE_M)
    if degraded:
        warn(f"Stage 1 degraded: using config prior R = {R_prior:.1f} m (no 2006–2012 slopes)")
        return dict(R_fit=R_prior, ci_lo=np.nan, ci_hi=np.nan,
                    df=pd.DataFrame(), delta0=delta0, L_coast=L_coast)

    win_start, win_end, T_yr = WINDOWS["stage1"]
    T_months = T_yr * 12.0
    dh_col = DH_CORR_COLS["stage1"]

    # Filter: wells with 2006–2012 dh_corr AND in coastal/western clusters
    mask = df36[dh_col].notna()
    mask &= df36["Cluster"].isin(STAGE1_COASTAL_CLUSTERS)
    mask &= ~df36["key"].isin(EXCL_NAMED)
    sub = df36[mask].copy()
    info(f"Stage 1 well set: {len(sub)} wells (C3/C5, 2006–2012 coverage)")
    if len(sub) < 3:
        warn("Stage 1: fewer than 3 wells — coastal calibration unreliable")

    keys = list(sub["key"])
    spans = load_well_spans(keys, win_start, win_end)

    rows = []
    for _, row in sub.iterrows():
        key = row["key"]
        T_m = spans.get(key, T_months)
        if np.isnan(T_m):
            T_m = T_months
        b3 = b3_lut.get(key, np.nan)
        b3v = (not np.isnan(b3)) and (b3 > 0.0)
        b3e = b3 if b3v else 0.0

        idx = list(df36["key"]).index(key)
        cu  = float(spatial["coast_unit"][idx])

        # SLR fixed contribution
        slr_pred = SLR_RATE_MM_YR * T_yr   # uniform positive

        # Coastal unit equilibrium amplitude (with R=1, will be scaled by OLS)
        # coast_unit_eq = δ₀/retreat_rate × coast_unit × ramp_factor
        coast_unit_eq = (delta0 / COAST_RETREAT_RATE) * cu * _ramp_factor(b3e, T_m)

        obs_dh   = float(row[dh_col])   # climate-corrected endpoint diff (mm), already a Δh
        residual = obs_dh - slr_pred   # y to explain with coastal field

        rows.append(dict(key=key, col=row.get("col", key),
                         Cluster=int(row["Cluster"]),
                         E=float(row["E"]), N=float(row["N"]),
                         T_months=T_m,
                         coast_unit_eq=coast_unit_eq,
                         slr_pred=slr_pred,
                         obs_dh=obs_dh,
                         y_residual=residual))

    df_s1 = pd.DataFrame(rows)

    # OLS: minimise ||y_residual − R × (−coast_unit_eq)||²
    # coast prediction is negative (drying), so x = −coast_unit_eq
    x = -df_s1["coast_unit_eq"].values
    y = df_s1["y_residual"].values
    # Filter out zeros (wells with zero coastal field — shouldn't be in C3/C5 but guard)
    valid = np.abs(x) > 1e-6
    if valid.sum() < 2:
        warn("Stage 1: insufficient non-zero coastal field — R defaulted to 50.0")
        R_fit = 50.0
        ci_lo, ci_hi = np.nan, np.nan
    else:
        R_fit = _ols_scale(x[valid], y[valid])
        try:
            ci_lo, ci_hi = _bootstrap_ci(x[valid], y[valid], _ols_scale)
        except Exception as exc:
            warn(f"Stage 1 bootstrap failed ({exc})")
            ci_lo, ci_hi = np.nan, np.nan

    R_fit = max(R_fit, 0.0)   # physical constraint: R ≥ 0
    info(f"Stage 1 calibrated R = {R_fit:.1f} m  (90% CI: {ci_lo:.1f}–{ci_hi:.1f} m)")
    result("Stage 1 R (effective coastal retreat, m)", f"{R_fit:.1f}")

    # Add per-well predictions with calibrated R
    df_s1["coast_pred"] = -R_fit * df_s1["coast_unit_eq"]
    df_s1["total_pred"] = df_s1["coast_pred"] + df_s1["slr_pred"]
    df_s1["stage1_residual"] = df_s1["total_pred"] - df_s1["obs_dh"]

    return dict(R_fit=R_fit, ci_lo=ci_lo, ci_hi=ci_hi, df=df_s1,
                delta0=delta0, L_coast=L_coast)


# ---------------------------------------------------------------------------
# Stage 2: scrape amplitude (2015–2017)
# ---------------------------------------------------------------------------

def stage2_scrape(df36: pd.DataFrame,
                  b3_lut: dict[str, float],
                  spatial: dict,
                  stage1: dict,
                  degraded: bool = False) -> dict:
    """
    Calibrate scrape amplitude scale from the 2015–2017 virgin window.

    Well set: CEH36, CEH18, CEH21 only (monitoring wells with confirmed
    pre-scrape baselines per working rules; Feb 2013 / Scrapes A/B excluded).

    Observed Δh − frozen_coastal_SLR = scrape_pred × scale.
    Fit scale by single-parameter OLS.
    """
    if degraded:
        warn("Stage 2 degraded: using scrape amplitude scale = 1.0 (no 2015–2017 slopes)")
        return dict(scale_fit=1.0, ci_lo=np.nan, ci_hi=np.nan, df=pd.DataFrame())

    win_start, win_end, T_yr = WINDOWS["stage2"]
    dh_col = DH_CORR_COLS["stage2"]

    mask = df36[dh_col].notna()
    mask &= df36["key"].isin(STAGE2_KEYS)
    sub = df36[mask].copy()
    info(f"Stage 2 well set: {len(sub)} wells ({', '.join(sorted(sub['key']))})")
    if len(sub) < 2:
        warn("Stage 2: fewer than 2 wells — scrape calibration unreliable; scale=1.0")

    R_fit   = stage1["R_fit"]
    delta0  = stage1["delta0"]
    L_coast = stage1["L_coast"]

    keys  = list(sub["key"])
    spans = load_well_spans(keys, win_start, win_end)

    rows = []
    for _, row in sub.iterrows():
        key = row["key"]
        T_m = spans.get(key, T_yr * 12.0)
        if np.isnan(T_m):
            T_m = T_yr * 12.0
        b3 = b3_lut.get(key, np.nan)
        b3v = (not np.isnan(b3)) and (b3 > 0.0)
        b3e = b3 if b3v else 0.0

        idx = list(df36["key"]).index(key)
        cu  = float(spatial["coast_unit"][idx])

        # Frozen coastal + SLR contribution over Stage-2 window
        coast_eq_frozen = (R_fit * delta0 / COAST_RETREAT_RATE) * cu * _ramp_factor(b3e, T_m)
        frozen_coast    = -coast_eq_frozen
        frozen_slr      = SLR_RATE_MM_YR * T_yr

        # Scrape Apr 2015 spatial equilibrium amplitude
        s15  = float(spatial["scr_2015"][idx])
        t_sc = max(0.0, (win_end - SCRAPING_DATE).days / DAYS_PER_MONTH)
        scr_eq = -s15 * _step_factor(b3e, t_sc)

        obs_dh   = float(row[dh_col])   # climate-corrected endpoint diff (mm)
        y_resid  = obs_dh - frozen_coast - frozen_slr   # residual for scrape to explain

        rows.append(dict(key=key, col=row.get("col", key),
                         Cluster=int(row["Cluster"]) if not pd.isna(row["Cluster"]) else np.nan,
                         E=float(row["E"]), N=float(row["N"]),
                         T_months=T_m,
                         frozen_coast=frozen_coast, frozen_slr=frozen_slr,
                         scr_eq=scr_eq,
                         obs_dh=obs_dh, y_residual=y_resid))

    df_s2 = pd.DataFrame(rows)

    x = df_s2["scr_eq"].values
    y = df_s2["y_residual"].values
    valid = np.abs(x) > 1e-6
    if valid.sum() < 2:
        scale_fit = 1.0
        ci_lo, ci_hi = np.nan, np.nan
        warn("Stage 2: insufficient scrape signal — scale defaulted to 1.0")
    else:
        scale_fit = _ols_scale(x[valid], y[valid])
        try:
            ci_lo, ci_hi = _bootstrap_ci(x[valid], y[valid], _ols_scale)
        except Exception as exc:
            warn(f"Stage 2 bootstrap failed ({exc})")
            ci_lo, ci_hi = np.nan, np.nan

    info(f"Stage 2 scrape amplitude scale = {scale_fit:.3f}  (90% CI: {ci_lo:.3f}–{ci_hi:.3f})")
    result("Stage 2 scrape amplitude scale", f"{scale_fit:.3f}")

    df_s2["scr_pred"]       = scale_fit * df_s2["scr_eq"]
    df_s2["total_pred"]     = df_s2["frozen_coast"] + df_s2["frozen_slr"] + df_s2["scr_pred"]
    df_s2["stage2_residual"]= df_s2["total_pred"] - df_s2["obs_dh"]

    return dict(scale_fit=scale_fit, ci_lo=ci_lo, ci_hi=ci_hi, df=df_s2)


# ---------------------------------------------------------------------------
# Stage 3: clearfell amplitude + λ diagnostic (2017–2025)
# ---------------------------------------------------------------------------

def stage3_clearfell(df36: pd.DataFrame,
                     b3_lut: dict[str, float],
                     spatial: dict,
                     stage1: dict,
                     stage2: dict,
                     clearfell_step_mm: float) -> dict:
    """
    Calibrate clearfell amplitude scale and λ (diagnostic only) from 2017–2025.

    Well set: forest clusters C4/C5.
    Frozen contributions: coastal + SLR + scaled scrape.
    Fit: single-parameter scale on the clearfell field (λ fixed at config value).
    λ diagnostic: report fitted λ vs equilibrium λ from config.DRAWDOWN_K_MDAY × DRAWDOWN_B_M.

    IMPORTANT: λ from this fit is NEVER written back to config.py.
    It is reported in Stage-3 output only (diagnostic of transient mound extent).
    """
    win_start, win_end, T_yr = WINDOWS["stage3"]
    dh_col = DH_CORR_COLS["stage3"]

    mask = df36[dh_col].notna()
    mask &= df36["Cluster"].isin({4, 5})   # forest clusters
    mask &= ~df36["key"].isin(EXCL_NAMED)
    sub = df36[mask].copy()
    info(f"Stage 3 well set: {len(sub)} wells (C4/C5 forest, 2017–2025 coverage)")
    if len(sub) < 3:
        warn("Stage 3: fewer than 3 forest wells — clearfell calibration unreliable")

    R_fit      = stage1["R_fit"]
    delta0     = stage1["delta0"]
    L_coast    = stage1["L_coast"]
    scr_scale  = stage2["scale_fit"]
    fLam_eq    = spatial["fLam"]  # equilibrium λ from config
    equil_lam  = float(DRAWDOWN_K_MDAY * DRAWDOWN_B_M) if fLam_eq is None else float(fLam_eq)

    keys  = list(sub["key"])
    spans = load_well_spans(keys, win_start, win_end)

    rows = []
    for _, row in sub.iterrows():
        key = row["key"]
        T_m = spans.get(key, T_yr * 12.0)
        if np.isnan(T_m):
            T_m = T_yr * 12.0
        b3 = b3_lut.get(key, np.nan)
        b3v = (not np.isnan(b3)) and (b3 > 0.0)
        b3e = b3 if b3v else 0.0

        idx = list(df36["key"]).index(key)
        cu  = float(spatial["coast_unit"][idx])
        s15 = float(spatial["scr_2015"][idx])
        cf  = float(spatial["clearfell"][idx])   # = clearfell_step_mm × exp(−d/λ_eq)

        # Frozen coastal
        coast_eq_frozen = (R_fit * delta0 / COAST_RETREAT_RATE) * cu * _ramp_factor(b3e, T_m)
        frozen_coast    = -coast_eq_frozen
        # Frozen SLR
        frozen_slr      = SLR_RATE_MM_YR * T_yr
        # Frozen scrape (Apr 2015 scrape, scaled)
        t_sc = max(0.0, (win_end - SCRAPING_DATE).days / DAYS_PER_MONTH)
        frozen_scr = scr_scale * (-s15) * _step_factor(b3e, t_sc)

        # Clearfell equilibrium field at this well
        t_cf = max(0.0, (win_end - INTERVENTION_DATE).days / DAYS_PER_MONTH)
        cf_eq = cf * _step_factor(b3e, t_cf)

        obs_dh  = float(row[dh_col])   # climate-corrected endpoint diff (mm)
        y_resid = obs_dh - frozen_coast - frozen_slr - frozen_scr

        rows.append(dict(key=key, col=row.get("col", key),
                         Cluster=int(row["Cluster"]) if not pd.isna(row["Cluster"]) else np.nan,
                         E=float(row["E"]), N=float(row["N"]),
                         T_months=T_m,
                         frozen_coast=frozen_coast, frozen_slr=frozen_slr,
                         frozen_scr=frozen_scr,
                         cf_eq=cf_eq,
                         obs_dh=obs_dh, y_residual=y_resid))

    df_s3 = pd.DataFrame(rows)

    x = df_s3["cf_eq"].values
    y = df_s3["y_residual"].values
    valid = np.abs(x) > 1e-6
    if valid.sum() < 2:
        scale_fit = 1.0
        ci_lo, ci_hi = np.nan, np.nan
        warn("Stage 3: insufficient clearfell signal — scale defaulted to 1.0")
    else:
        scale_fit = _ols_scale(x[valid], y[valid])
        try:
            ci_lo, ci_hi = _bootstrap_ci(x[valid], y[valid], _ols_scale)
        except Exception as exc:
            warn(f"Stage 3 bootstrap failed ({exc})")
            ci_lo, ci_hi = np.nan, np.nan

    info(f"Stage 3 clearfell amplitude scale = {scale_fit:.3f}  (90% CI: {ci_lo:.3f}–{ci_hi:.3f})")
    result("Stage 3 clearfell amplitude scale", f"{scale_fit:.3f}")

    # λ DIAGNOSTIC: fit implied λ via non-linear residual scan (diagnostic only)
    # Tries a grid of λ values (100–3000 m); picks the one minimising ||residuals||².
    # Never written to config.py.
    lam_fitted = equil_lam
    try:
        import geopandas as gpd
        from shapely.geometry import Point as _Pt
        gdf = gpd.read_file(str(paths.DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
        fell_geom = None
        for idx2, gdf_row in gdf.iterrows():
            nm = str(gdf_row.get("Name", "")).lower()
            if "felling" in nm or "experiment" in nm:
                fell_geom = gdf_row.geometry
                break
        if fell_geom is not None:
            E_arr = df_s3["E"].values
            N_arr = df_s3["N"].values
            b3_arr = np.array([b3_lut.get(k, 0.0) for k in df_s3["key"]])
            d_fell = np.array([fell_geom.distance(_Pt(x, y))
                               for x, y in zip(E_arr, N_arr)])
            t_cf_arr = np.array([
                max(0.0, (win_end - INTERVENTION_DATE).days / DAYS_PER_MONTH)
                for _ in df_s3["key"]
            ])
            sf_arr = np.array([_step_factor(float(b), float(t))
                                for b, t in zip(b3_arr, t_cf_arr)])
            y_target = df_s3["y_residual"].values

            lam_grid = np.linspace(100, 3000, 60)
            best_sse = np.inf
            for lam in lam_grid:
                cf_trial = clearfell_step_mm * np.exp(-d_fell / lam) * sf_arr
                s_ = _ols_scale(cf_trial, y_target)
                resid = y_target - s_ * cf_trial
                sse = float(np.dot(resid, resid))
                if sse < best_sse:
                    best_sse = sse
                    lam_fitted = lam

            info(f"Stage 3 λ diagnostic: {lam_fitted:.0f} m  (equilibrium λ = {equil_lam:.0f} m)")
            result("Stage 3 λ fitted (diagnostic only — NOT written to config)",
                   f"{lam_fitted:.0f} m vs equilibrium {equil_lam:.0f} m")
    except Exception as exc:
        warn(f"Stage 3 λ diagnostic failed ({exc}) — using equilibrium λ")

    df_s3["cf_pred"]        = scale_fit * df_s3["cf_eq"]
    df_s3["total_pred"]     = (df_s3["frozen_coast"] + df_s3["frozen_slr"]
                                + df_s3["frozen_scr"] + df_s3["cf_pred"])
    df_s3["stage3_residual"]= df_s3["total_pred"] - df_s3["obs_dh"]

    return dict(scale_fit=scale_fit, ci_lo=ci_lo, ci_hi=ci_hi,
                lam_fitted=lam_fitted, equil_lam=equil_lam, df=df_s3)


# ---------------------------------------------------------------------------
# Full-window validation (2005–2025) with all calibrated constants
# ---------------------------------------------------------------------------

def full_window_validation(df36: pd.DataFrame,
                            b3_lut: dict[str, float],
                            spatial: dict,
                            stage1: dict, stage2: dict, stage3: dict,
                            clearfell_step_mm: float) -> pd.DataFrame:
    """
    Rebuild 2005–2025 prediction using all calibrated constants.

    Compares against slope_mm_yr_2005_2025 × 20 yr.
    Reports r vs the v1.x baselines (2005–2025 r=0.595, 2011–2025 r=0.285).
    """
    win_start, win_end, T_yr = WINDOWS["full5"]
    slope_col = FULL5_SLOPE_COL   # long-window secular slope is well-conditioned
    T_months  = T_yr * 12.0

    R_fit     = stage1["R_fit"]
    delta0    = stage1["delta0"]
    scr_scale = stage2["scale_fit"]
    cf_scale  = stage3["scale_fit"]
    fLam_eq   = spatial["fLam"]

    mask = df36[slope_col].notna()
    sub  = df36[mask].copy()
    keys = list(sub["key"])
    spans = load_well_spans(keys, win_start, win_end)

    rows = []
    for _, row in sub.iterrows():
        key = row["key"]
        T_m = spans.get(key, T_months)
        if np.isnan(T_m):
            T_m = T_months
        b3 = b3_lut.get(key, np.nan)
        b3v = (not np.isnan(b3)) and (b3 > 0.0)
        b3e = b3 if b3v else 0.0

        idx = list(df36["key"]).index(key)
        cu  = float(spatial["coast_unit"][idx])
        cf  = float(spatial["clearfell"][idx])
        s15 = float(spatial["scr_2015"][idx])
        bl  = float(spatial["broadleaf"][idx])

        # Coastal (calibrated R)
        coast_eq  = (R_fit * delta0 / COAST_RETREAT_RATE) * cu * _ramp_factor(b3e, T_m)
        coast_pred = -coast_eq

        # SLR (fixed)
        slr_pred = SLR_RATE_MM_YR * T_yr

        # Clearfell (calibrated scale)
        if pd.Timestamp("2005-01-01") > INTERVENTION_DATE:
            cf_pred = 0.0
        else:
            t_cf   = max(0.0, (win_end - INTERVENTION_DATE).days / DAYS_PER_MONTH)
            cf_pred = cf_scale * cf * _step_factor(b3e, t_cf)

        # Scrape Apr 2015 (calibrated scale)
        t_sc   = max(0.0, (win_end - SCRAPING_DATE).days / DAYS_PER_MONTH)
        scr_pred = scr_scale * (-s15) * _step_factor(b3e, t_sc)

        # Broadleaf (full 2005→2025 increment; not calibrated)
        # canopy fraction increment over the window
        f_start = BL_CANOPY_FRACTION_2005
        f_end   = BL_CANOPY_FRACTION_2025
        bl_inc  = (f_end - f_start) * bl / max(f_end - f_start, 1e-9)
        bl_rf   = _ramp_factor(b3e, T_m)
        bl_pred = -bl_inc * bl_rf

        total_pred  = coast_pred + slr_pred + cf_pred + scr_pred + bl_pred
        obs_dh      = float(row[slope_col]) * T_yr
        residual    = total_pred - obs_dh

        excl_reason = EXCL_NAMED.get(key, "")
        rows.append(dict(
            key=key, col=row.get("col", key),
            Cluster=int(row["Cluster"]) if not pd.isna(row["Cluster"]) else np.nan,
            E=float(row["E"]), N=float(row["N"]),
            T_months=round(T_m, 1),
            b3_drainage=b3_lut.get(key, np.nan),
            b3_correction_valid=b3v,
            exclude_named=bool(excl_reason),
            exclude_reason=excl_reason,
            coast_pred=round(coast_pred, 1),
            slr_pred=round(slr_pred, 1),
            clearfell_pred=round(cf_pred, 1),
            scr_pred=round(scr_pred, 1),
            bl_pred=round(bl_pred, 1),
            total_pred=round(total_pred, 1),
            observed_dh=round(obs_dh, 1),
            residual=round(residual, 1),
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Calibration table
# ---------------------------------------------------------------------------

def build_calibration_table(stage1: dict, stage2: dict, stage3: dict) -> pd.DataFrame:
    rows = [
        dict(driver="Coastal retreat", stage="Stage 1", window="2006–2012",
             parameter="R_effective_m", fitted=round(stage1["R_fit"], 1),
             ci_lo_90=round(stage1["ci_lo"], 1) if not np.isnan(stage1["ci_lo"]) else np.nan,
             ci_hi_90=round(stage1["ci_hi"], 1) if not np.isnan(stage1["ci_hi"]) else np.nan,
             notes="calibrated; SLR fixed at 4 mm/yr"),
        dict(driver="SLR", stage="Stage 1", window="2006–2012",
             parameter="SLR_rate_mm_yr", fitted=SLR_RATE_MM_YR,
             ci_lo_90=np.nan, ci_hi_90=np.nan,
             notes="fixed (Holyhead ~4 mm/yr; not calibrated)"),
        dict(driver="Scrape Apr 2015", stage="Stage 2", window="2015–2017",
             parameter="amplitude_scale", fitted=round(stage2["scale_fit"], 3),
             ci_lo_90=round(stage2["ci_lo"], 3) if not np.isnan(stage2["ci_lo"]) else np.nan,
             ci_hi_90=round(stage2["ci_hi"], 3) if not np.isnan(stage2["ci_hi"]) else np.nan,
             notes=f"CEH36/18/21 only; n={len(stage2['df'])}"),
        dict(driver="Clearfell Dec 2017", stage="Stage 3", window="2017–2025",
             parameter="amplitude_scale", fitted=round(stage3["scale_fit"], 3),
             ci_lo_90=round(stage3["ci_lo"], 3) if not np.isnan(stage3["ci_lo"]) else np.nan,
             ci_hi_90=round(stage3["ci_hi"], 3) if not np.isnan(stage3["ci_hi"]) else np.nan,
             notes=f"C4/C5; n={len(stage3['df'])}"),
        dict(driver="Clearfell λ (DIAGNOSTIC ONLY)", stage="Stage 3", window="2017–2025",
             parameter="lambda_m",
             fitted=round(stage3["lam_fitted"], 0),
             ci_lo_90=np.nan, ci_hi_90=np.nan,
             notes=f"NOT written to config.py; equilibrium λ = {stage3['equil_lam']:.0f} m"),
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def _scatter_stage(df: pd.DataFrame, obs_col: str, pred_col: str,
                   out_path: Path, title: str, xlabel: str, ylabel: str,
                   dpi: int = 150) -> tuple[float, float]:
    """Generic stage scatter. Returns (r, rmse) for in-stats wells."""
    colours = config.get_cluster_colours()
    with plt.rc_context(MPL_RC):
        fig, ax = plt.subplots(figsize=(6.5, 6.5))
        in_s = df[obs_col].notna() & df[pred_col].notna()
        x = df.loc[in_s, pred_col].values
        y = df.loc[in_s, obs_col].values

        lim = max(np.abs(np.concatenate([x, y])).max() * 1.15, 50.0)
        ax.plot([-lim, lim], [-lim, lim], color="#999999", lw=0.9, ls="--", zorder=1)
        ax.axhline(0, color="#cccccc", lw=0.6, zorder=0)
        ax.axvline(0, color="#cccccc", lw=0.6, zorder=0)

        for cid in sorted(df["Cluster"].dropna().unique()):
            sub_c = df[(df["Cluster"] == cid) & in_s]
            col = colours.get(int(cid), "#444444")
            mrk = CLUSTER_MARKERS.get(int(cid), "o")
            ax.scatter(sub_c[pred_col], sub_c[obs_col],
                       c=col, marker=mrk, edgecolor="k", lw=0.6, s=60, zorder=4,
                       label=CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))
            for _, ow in sub_c.iterrows():
                ax.annotate(str(ow["col"]).upper(),
                            xy=(ow[pred_col], ow[obs_col]),
                            xytext=(4, 4), textcoords="offset points",
                            fontsize=7, color="#444444")

        r_val = rmse = np.nan
        if len(x) >= 3:
            r_val, _ = pearsonr(x, y)
            rmse     = float(np.sqrt(np.mean((x - y) ** 2)))
            ax.text(0.05, 0.95, f"r = {r_val:.2f}  n = {len(x)}\nRMSE = {rmse:.0f} mm",
                    transform=ax.transAxes, fontsize=9, va="top",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#aaa", alpha=0.9))

        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=10, pad=8)
        ax.legend(fontsize=8, loc="lower right", framealpha=0.9)
        fig.tight_layout()
        fig.savefig(out_path, dpi=dpi)
        plt.close(fig)
    saved(out_path)
    return r_val, rmse


def plot_full_scatter(df: pd.DataFrame, dpi: int = 150) -> tuple[float, float]:
    """Full-window predicted-vs-observed scatter with named exclusions."""
    colours = config.get_cluster_colours()
    with plt.rc_context(MPL_RC):
        fig, ax = plt.subplots(figsize=(7.5, 7.5))

        in_stats = df[df["b3_correction_valid"] & ~df["exclude_named"]].copy()
        b3_flag  = df[~df["b3_correction_valid"]].copy()
        excl     = df[df["exclude_named"]].copy()

        r_val = rmse = np.nan
        if len(in_stats) >= 3:
            r_val, _ = pearsonr(in_stats["total_pred"], in_stats["observed_dh"])
            rmse     = float(np.sqrt(np.mean(in_stats["residual"] ** 2)))

        all_vals = pd.concat([df["total_pred"], df["observed_dh"]]).dropna()
        lim = max(abs(all_vals.min()), abs(all_vals.max())) * 1.15
        lim = max(lim, 100.0)

        ax.plot([-lim, lim], [-lim, lim], color="#999999", lw=0.9, ls="--", zorder=1)
        ax.axhline(0, color="#cccccc", lw=0.6, zorder=0)
        ax.axvline(0, color="#cccccc", lw=0.6, zorder=0)

        for cid in sorted(in_stats["Cluster"].dropna().unique()):
            sub = in_stats[in_stats["Cluster"] == cid]
            col = colours.get(int(cid), "#444444")
            mrk = CLUSTER_MARKERS.get(int(cid), "o")
            ax.scatter(sub["total_pred"], sub["observed_dh"],
                       c=col, marker=mrk, edgecolor="k", lw=0.6, s=60, zorder=4,
                       label=CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))

        if not b3_flag.empty:
            ax.scatter(b3_flag["total_pred"], b3_flag["observed_dh"],
                       facecolor="none", edgecolor="#888888", lw=1.5,
                       marker="^", s=60, zorder=4, label="β₃ ≤ 0 (invalid corr.)")

        if not excl.empty:
            ax.scatter(excl["total_pred"], excl["observed_dh"],
                       facecolor="none", edgecolor="#cc0000", lw=1.5,
                       marker="s", s=80, zorder=4, label="named exclusion")
            for _, ow in excl.iterrows():
                ax.annotate(str(ow["col"]).upper(),
                            xy=(ow["total_pred"], ow["observed_dh"]),
                            xytext=(4, 4), textcoords="offset points",
                            fontsize=7.5, color="#cc0000")

        if not np.isnan(rmse):
            thresh   = OUTLIER_THRESHOLD * rmse
            outliers = in_stats[in_stats["residual"].abs() > thresh]
            for _, ow in outliers.iterrows():
                ax.annotate(str(ow["col"]).upper(),
                            xy=(ow["total_pred"], ow["observed_dh"]),
                            xytext=(4, 4), textcoords="offset points",
                            fontsize=7.5, color="#333333")

        if not np.isnan(r_val):
            stat_txt = (f"r = {r_val:.2f}  (n = {len(in_stats)})\n"
                        f"RMSE = {rmse:.0f} mm\n"
                        f"[sequential calibration v{__version__}]\n"
                        f"[v1.x baselines: 2005–2025 r=0.595, 2011–2025 r=0.285]")
            ax.text(0.05, 0.95, stat_txt, transform=ax.transAxes,
                    fontsize=8.5, va="top",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec="#aaaaaa", alpha=0.9))

        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xlabel("Modelled Δh 2005–2025 (mm, sequential calibration)", fontsize=10)
        ax.set_ylabel("Observed Δh 2005–2025 (mm, Script 36)", fontsize=10)
        ax.set_title("Sequential driver calibration — full-window validation (2005–2025)",
                     fontsize=11, pad=8)
        ax.legend(fontsize=8, loc="lower right", framealpha=0.9)
        fig.tight_layout()
        fig.savefig(OUT_SCATTER_FULL, dpi=dpi)
        plt.close(fig)
    saved(OUT_SCATTER_FULL)
    return r_val, rmse


def plot_residual_map(df: pd.DataFrame, dpi: int = 150) -> None:
    """IDW residual map (model − observed) for the full 2005–2025 window."""
    df_map = df.dropna(subset=["E", "N", "residual"]).copy()
    with plt.rc_context(MPL_RC):
        fig, ax = plt.subplots(figsize=(11, 9))
        vmax = max(float(np.nanpercentile(df_map["residual"].abs(), 95)), 50.0)
        norm = TwoSlopeNorm(vcenter=0.0, vmin=-vmax, vmax=vmax)

        load_dem_hillshade(ax, paths.DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
        add_idw_surface(ax, df_map, value_col="residual",
                        easting_col="E", northing_col="N",
                        cmap=plt.cm.RdBu, norm=norm,
                        alpha=0.55, zorder=1.5, apply_site_mask=True)
        add_kml_features(ax, paths.DATA_DIR)
        add_en_axes(ax, osgb_label=False)

        colours = config.get_cluster_colours()
        for cid in sorted(df["Cluster"].dropna().unique()):
            sub = df[df["Cluster"] == cid]
            col = colours.get(int(cid), "#444444")
            mrk = CLUSTER_MARKERS.get(int(cid), "o")
            ax.scatter(sub["E"], sub["N"], c=col, marker=mrk,
                       edgecolor="k", lw=0.6, s=55, zorder=5,
                       label=CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))

        sm = plt.cm.ScalarMappable(cmap=plt.cm.RdBu, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.028, pad=0.04)
        cbar.set_label("Residual (mm): model − observed  (2005–2025)", fontsize=9)
        ax.set_title(
            "Sequential driver calibration — residual map (2005–2025)\n"
            "Blue = model over-predicts wetting; Red = model over-predicts drying",
            fontsize=10, pad=8)
        ax.legend(fontsize=8, loc="lower left", framealpha=0.9, title="cluster")
        fig.tight_layout()
        fig.savefig(OUT_RESIDUAL_MAP, dpi=dpi)
        plt.close(fig)
    saved(OUT_RESIDUAL_MAP)


# ---------------------------------------------------------------------------
# Results text
# ---------------------------------------------------------------------------

def write_results(stage1: dict, stage2: dict, stage3: dict,
                  df_full: pd.DataFrame, cal_table: pd.DataFrame,
                  r_full: float, rmse_full: float) -> None:
    lines = [
        f"37_driver_validation v{__version__} — Sequential Driver Calibration",
        "=" * 65,
        "",
        "CALIBRATION SUMMARY",
        "-" * 65,
    ]

    for _, row in cal_table.iterrows():
        lo = f"{row['ci_lo_90']:.3g}" if not pd.isna(row["ci_lo_90"]) else "—"
        hi = f"{row['ci_hi_90']:.3g}" if not pd.isna(row["ci_hi_90"]) else "—"
        lines.append(
            f"  {row['driver']:35s}  {row['parameter']:20s}  "
            f"{row['fitted']:8.3g}  90%CI [{lo}, {hi}]  — {row['notes']}"
        )

    lines += ["", "FULL-WINDOW VALIDATION (2005–2025, calibrated constants)", "-" * 65]
    if not np.isnan(r_full):
        in_stats = df_full[df_full["b3_correction_valid"] & ~df_full["exclude_named"]]
        lines.append(f"  r (Pearson)  : {r_full:.3f}  (n={len(in_stats)})")
        lines.append(f"  RMSE         : {rmse_full:.1f} mm")
        lines.append(f"  v1.x baselines: 2005–2025 r=0.595 (35% var); 2011–2025 r=0.285 (8% var)")
        lines.append(f"  r² improvement: {r_full**2:.3f} vs 0.354 (2005–2025 v1.x)")

    lines += ["", "PER-CLUSTER MEANS (full-window, mm)", "-" * 65]
    for cid in sorted(df_full["Cluster"].dropna().unique()):
        sub = df_full[df_full["Cluster"] == cid]
        lbl = CLUSTER_LABELS.get(int(cid), f"C{int(cid)}")
        lines.append(
            f"  {lbl:20s}  pred {sub['total_pred'].mean():+7.1f}  "
            f"obs {sub['observed_dh'].mean():+7.1f}  "
            f"resid {sub['residual'].mean():+7.1f}  n={len(sub)}"
        )

    lines += ["", "λ DIAGNOSTIC (Stage 3)", "-" * 65]
    lines.append(
        f"  Fitted λ     : {stage3['lam_fitted']:.0f} m  (DIAGNOSTIC ONLY — never written to config.py)"
    )
    lines.append(
        f"  Equilibrium λ: {stage3['equil_lam']:.0f} m  (from config: DRAWDOWN_K_MDAY × DRAWDOWN_B_M)"
    )
    ratio = stage3["lam_fitted"] / max(stage3["equil_lam"], 1.0)
    lines.append(
        f"  Ratio fitted/equil: {ratio:.2f}×  "
        "— ratio > 1 indicates transient pressure mound overruns equilibrium reach"
    )

    lines += ["", "STAGE WELL COUNTS", "-" * 65]
    lines.append(f"  Stage 1 (2006–2012, coastal): {len(stage1['df'])} wells (C3/C5)")
    lines.append(f"  Stage 2 (2015–2017, scrape) : {len(stage2['df'])} wells (CEH36/18/21)")
    lines.append(f"  Stage 3 (2017–2025, clearfell): {len(stage3['df'])} wells (C4/C5)")

    OUT_RESULTS.write_text("\n".join(lines) + "\n")
    saved(OUT_RESULTS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    banner("37", "Sequential Driver Calibration — spring-MAM basis", version=__version__)

    DIR_37.mkdir(parents=True, exist_ok=True)

    # ── Phase 1: load Script 36 data ─────────────────────────────────────────
    phase(1, "Load Script 36 per-well data")
    df36, missing_cols = load_script36()
    info(f"Script 36 wells loaded: {len(df36)} total")
    for wlabel, col in REQUIRED_COLS.items():
        if col in df36.columns:
            n = df36[col].notna().sum()
            info(f"  {wlabel} ({col}): {n} wells with coverage")
        else:
            info(f"  {wlabel} ({col}): ABSENT — degraded mode")
    deg1 = "stage1" in missing_cols
    deg2 = "stage2" in missing_cols
    if deg1 or deg2:
        note(f"Degraded mode: missing stages {missing_cols & {'stage1','stage2'}} — "
             "rerun Script 36 with sequential windows to enable full calibration")

    keys  = list(df36["key"])
    b3    = load_master_b3(keys)
    n_b3  = sum(1 for v in b3.values() if np.isnan(v) or v <= 0.0)
    if n_b3:
        note(f"{n_b3} wells have β₃ ≤ 0 or NaN (temporal corrections set to 1.0)")

    # ── Phase 2: live parameters ─────────────────────────────────────────────
    phase(2, "Load live parameters from upstream CSVs")
    delta0, L_coast     = _load_coastal_fit()
    clearfell_step_mm   = _load_clearfell_step()

    # ── Phase 3: spatial factors ─────────────────────────────────────────────
    phase(3, "Build spatial factors via Script 20")
    step("importing Script 20 via importlib …")
    s20 = _load_s20()
    info("Script 20 loaded")
    spatial = _build_spatial(s20, df36["E"].values, df36["N"].values,
                             clearfell_step_mm, L_coast)

    # ── Phase 4: Stage 1 ─────────────────────────────────────────────────────
    phase(4, "Stage 1 — Coastal retreat + SLR (2006–2012)")
    stage1 = stage1_coastal(df36, b3, spatial, delta0, L_coast, degraded=deg1)
    if not deg1 and not stage1["df"].empty:
        r_s1, rmse_s1 = _scatter_stage(
            stage1["df"], obs_col="obs_dh", pred_col="total_pred",
            out_path=OUT_SCATTER_S1,
            title="Stage 1: Coastal + SLR calibration (2006–2012)",
            xlabel="Predicted Δh coastal+SLR (mm)",
            ylabel="Observed Δh 2006–2012 MAM (mm, Script 36)",
        )
        result("Stage 1 scatter r", f"{r_s1:.3f}" if not np.isnan(r_s1) else "n/a")
    else:
        note("Stage 1 scatter skipped (degraded mode)")

    # ── Phase 5: Stage 2 ─────────────────────────────────────────────────────
    phase(5, "Stage 2 — Scrape amplitude (2015–2017)")
    stage2 = stage2_scrape(df36, b3, spatial, stage1, degraded=deg2)
    if not deg2 and not stage2["df"].empty:
        r_s2, rmse_s2 = _scatter_stage(
            stage2["df"], obs_col="obs_dh", pred_col="total_pred",
            out_path=OUT_SCATTER_S2,
            title="Stage 2: Scrape calibration (2015–2017)",
            xlabel="Predicted Δh frozen+scrape (mm)",
            ylabel="Observed Δh 2015–2017 MAM (mm, Script 36)",
        )
        result("Stage 2 scatter r", f"{r_s2:.3f}" if not np.isnan(r_s2) else "n/a (≤2 wells)")
    else:
        note("Stage 2 scatter skipped (degraded mode)")

    # ── Phase 6: Stage 3 ─────────────────────────────────────────────────────
    phase(6, "Stage 3 — Clearfell amplitude + λ diagnostic (2017–2025)")
    stage3 = stage3_clearfell(df36, b3, spatial, stage1, stage2, clearfell_step_mm)
    r_s3, rmse_s3 = _scatter_stage(
        stage3["df"], obs_col="obs_dh", pred_col="total_pred",
        out_path=OUT_SCATTER_S3,
        title="Stage 3: Clearfell calibration (2017–2025)",
        xlabel="Predicted Δh frozen+clearfell (mm)",
        ylabel="Observed Δh 2017–2025 MAM (mm, Script 36)",
    )
    result("Stage 3 scatter r", f"{r_s3:.3f}" if not np.isnan(r_s3) else "n/a")

    # ── Phase 7: full-window validation ──────────────────────────────────────
    phase(7, "Full-window validation (2005–2025, all calibrated constants)")
    df_full = full_window_validation(df36, b3, spatial, stage1, stage2, stage3,
                                      clearfell_step_mm)
    r_full, rmse_full = plot_full_scatter(df_full)
    if not np.isnan(r_full):
        result(f"Full-window r (v{__version__})", f"{r_full:.3f}")
        result(f"Full-window RMSE (v{__version__})", f"{rmse_full:.1f} mm")
        result("r² gain vs v1.x 2005–2025 baseline",
               f"{r_full**2 - 0.354:+.3f}  (0.354 = 0.595²)")

    # ── Phase 8: write outputs ────────────────────────────────────────────────
    phase(8, "Write outputs")
    cal_table = build_calibration_table(stage1, stage2, stage3)
    cal_table.to_csv(OUT_CAL_TABLE, index=False)
    saved(OUT_CAL_TABLE)

    df_full.to_csv(OUT_PER_WELL, index=False)
    saved(OUT_PER_WELL)

    plot_residual_map(df_full)
    write_results(stage1, stage2, stage3, df_full, cal_table, r_full, rmse_full)

    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
