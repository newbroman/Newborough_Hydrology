"""
37_driver_validation.py
=======================
Predicted-vs-observed validation of the modelled 2011–2025 driver-change field
against Script 36 climate-removed per-well secular trends (n ≤ 55).

For each well in the Script 36 primary (2011–2025) coverage set:
  1. Samples four driver fields from Script 20 at the well's (E, N) location,
     plus an inline SLR erfc contribution.
  2. Applies per-well, window-matched temporal corrections via β₃ (month⁻¹):
       Ramp drivers  — factor = 1 − (1 − exp(−β₃T)) / (β₃T)   [coastal, broadleaf]
       Step drivers  — factor = 1 − exp(−β₃ t)                  [clearfell, scrapes]
  3. Compares total_pred (mm) against Script 36 slope × window span (mm).
  4. Outputs a validation scatter, IDW residual map, per-well CSV, and results text.

Driver fields (positive = head loss → negative Δh, except SLR and clearfell):
  • Coastal chronic retreat  — ramp, R-calibrated amplitude (COAST_RETREAT_EFFECTIVE_M)
  • Sea-level rise (SLR)     — erfc diffusion, 4 mm/yr × 14 yr = 56 mm, positive (rise)
  • Clearfell recovery       — step, Path B (BACI-observed +120 mm), positive (rise)
  • Scraping drawdown        — step per epoch (Feb 2013 / Apr 2015 / Oct 2023)
  • Broadleaf increment      — ramp, 2011→2025 canopy fraction window

SLR is omitted from the 5-yr driver-change map but included here for the 14-yr
window where it contributes ≈ +20–55 mm across the site.

Named exclusions (shown in scatter but excluded from r/RMSE):
  CEH4  — scrape-beneficiary / BACI control-well contamination
  WMC2  — anomalous wetting, no identifiable mechanism
  NW9   — relic slack, topographic amplification of coastal drying
  CEH20 — forest hollow, topographic amplification of clearfell recovery

Step 40/46, Phase 15 — Observed Differential Change, Envelope, and Validation.
"""

__version__ = "1.1.0"
# 1.1.0 — 2011–2025 window (55 wells); calibrated coastal amplitude
#          (COAST_RETREAT_EFFECTIVE_M = 105 m, R × δ₀/rate); SLR erfc field
#          added; broadleaf fraction corrected for 2011 window start; four
#          named exclusions (CEH4/WMC2/NW9/CEH20) flagged with reasons.
# 1.0.3 — write_results fix: per-well table used ':2d' on a ternary returning
#          str '?'; pre-compute c_lbl and use ':>2'.
# 1.0.2 — load_master_b3 fix: 03_master_data.csv stores well name in
#          Name_Original; derive key via .lower().strip() per Script 36.
# 1.0.1 — clearfell geometry fix: use felling polygon (not forest boundary),
#          matching _driver_change_net() in Script 20 v1.32.0.
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
from matplotlib.lines import Line2D
from pathlib import Path
from scipy.stats import pearsonr
from scipy.special import erfc as _erfc

from utils import config, paths
from utils.paths import (
    INT_LOCATIONS, INT_MASTER_DATA, INT_WELLS_CLEAN,
    OUT_36_PER_WELL,
    OUT_10A_REPORT,
    OUT_25_FIT_PARAMETERS,
)
from utils.config import (
    CLUSTER_LABELS, CLUSTER_MARKERS,
    DRAWDOWN_H0_MM, DRAWDOWN_K_MDAY, DRAWDOWN_B_M,
    BL_CANOPY_FRACTION_2005, BL_CANOPY_FRACTION_2025,
    COAST_RETREAT_EFFECTIVE_M,
    COAST_RETREAT_RATE,
)
from utils.clearfell_common import (
    INTERVENTION_DATE,
    SCRAPING_DATE_0,
    SCRAPING_DATE,
    SCRAPING_DATE_2,
)
from utils.console_utils import banner, phase, step, info, warn, result, saved, note
from utils.map_utils import (
    load_dem_hillshade,
    add_idw_surface,
    add_en_axes,
    add_kml_features,
)

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
DIR_37           = paths.DIR_37
OUT_PER_WELL     = paths.OUT_37_PER_WELL
OUT_SCATTER      = paths.OUT_37_SCATTER
OUT_RESIDUAL_MAP = paths.OUT_37_RESIDUAL_MAP
OUT_RESULTS      = paths.OUT_37_RESULTS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_ID      = "37"
WINDOW_START   = pd.Timestamp("2011-01-01")   # 2011–2025 analysis window
WINDOW_END     = pd.Timestamp("2025-12-01")
DAYS_PER_MONTH = 30.4375

# Slope column read from Script 36 per-well CSV
SLOPE_COL = "slope_mm_yr_2011_2025"

# Reference window duration for COAST_RETREAT_EFFECTIVE_M scaling (years)
# R scales linearly: R_window = COAST_RETREAT_EFFECTIVE_M × (T_window_yr / REF_WINDOW_YR)
REF_WINDOW_YR = 20.0

# Broadleaf canopy fraction at the window start (2011)
# f(t) = BL_CANOPY_FRACTION_2005 + (t-2005)/20 × (f_2025 − f_2005); t=2011 → f=0.58
_f2011 = BL_CANOPY_FRACTION_2005 + (2011 - 2005) / 20.0 * (BL_CANOPY_FRACTION_2025 - BL_CANOPY_FRACTION_2005)
BL_WINDOW_FRACTION = (BL_CANOPY_FRACTION_2025 - _f2011) / max(BL_CANOPY_FRACTION_2025 - BL_CANOPY_FRACTION_2005, 1e-9)
# = 0.42 / 0.60 = 0.70 for the 2011-2025 window

# SLR: representative specific yield for diffusivity estimate
_SY_REP = 0.06   # median reference-network Sy (pipeline_params C3 default)

# Epoch label → event Timestamp
SCRAPE_EPOCH_DATES: dict[str, pd.Timestamp] = {
    "Feb 2013":   SCRAPING_DATE_0,
    "April 2015": SCRAPING_DATE,
    "Oct 2023":   SCRAPING_DATE_2,
}

# Named exclusions: excluded from r/RMSE, still plotted with distinct marker
EXCL_NAMED: dict[str, str] = {
    "ceh4":  "scrape-beneficiary / BACI control-well contamination",
    "wmc2":  "anomalous wetting — no identifiable mechanism",
    "nw9":   "relic slack — topographic amplification of coastal drying",
    "ceh20": "forest hollow — topographic amplification of clearfell recovery",
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

def load_script36_wells() -> pd.DataFrame:
    """Load Script 36 per-well CSV; return wells with a 2011–2025 slope.

    The Script 36 base frame is initialised from the 2005–2025 set, so
    2011–2025-only wells arrive with NaN in col/Cluster/E/N.  Patch these
    from INT_LOCATIONS (coordinates) and INT_MASTER_DATA (cluster, label).
    """
    df = pd.read_csv(OUT_36_PER_WELL)
    df["key"] = df["key"].str.strip().str.lower()
    if SLOPE_COL not in df.columns:
        raise KeyError(
            f"Column '{SLOPE_COL}' not found in Script 36 CSV. "
            "Ensure Script 36 was run with the 2011–2025 period enabled."
        )
    df = df.dropna(subset=[SLOPE_COL]).copy()

    # Patch E/N from INT_LOCATIONS for new wells
    if df[["E", "N"]].isna().any().any():
        try:
            locs = pd.read_csv(INT_LOCATIONS)
            # normalise key column (may be Name_Original or key)
            id_col = next((c for c in ("key", "col", "Name_Original")
                           if c in locs.columns), None)
            if id_col:
                locs["_key"] = locs[id_col].astype(str).str.strip().str.lower()
                locs_lut = locs.set_index("_key")[["E", "N"]].to_dict("index")
                for idx, row in df[df["E"].isna()].iterrows():
                    if row["key"] in locs_lut:
                        df.loc[idx, "E"] = locs_lut[row["key"]]["E"]
                        df.loc[idx, "N"] = locs_lut[row["key"]]["N"]
        except Exception as exc:
            warn(f"could not patch E/N from INT_LOCATIONS: {exc}")

    # Patch Cluster and col from INT_MASTER_DATA
    if df[["Cluster", "col"]].isna().any().any():
        try:
            master = pd.read_csv(INT_MASTER_DATA)
            id_col = next((c for c in ("Name_Original", "key", "col")
                           if c in master.columns), None)
            if id_col:
                master["_key"] = master[id_col].astype(str).str.strip().str.lower()
                for idx, row in df[df["Cluster"].isna() | df["col"].isna()].iterrows():
                    m = master[master["_key"] == row["key"]]
                    if not m.empty:
                        if pd.isna(row.get("Cluster")):
                            df.loc[idx, "Cluster"] = m["Cluster"].iloc[0]
                        if pd.isna(row.get("col")):
                            # col = display name; fall back to Name_Original or key
                            for src in ("col", "Name_Original", "name"):
                                if src in m.columns:
                                    df.loc[idx, "col"] = str(m[src].iloc[0])
                                    break
        except Exception as exc:
            warn(f"could not patch Cluster/col from INT_MASTER_DATA: {exc}")

    # Final fallback: use key as col for any still-NaN col values
    df["col"] = df["col"].fillna(df["key"])

    n_still_nan_en = df[["E","N"]].isna().any(axis=1).sum()
    if n_still_nan_en:
        warn(f"{n_still_nan_en} wells still have NaN E/N after patching — "
             "they will have zero spatial factors")
    info(f"Script 36 wells (2011–2025 coverage): {len(df)}")
    return df


def load_master_b3(well_keys: list[str]) -> dict[str, float]:
    """Return {key: beta_3_drainage (month⁻¹)} from INT_MASTER_DATA."""
    master = pd.read_csv(INT_MASTER_DATA)
    if "Name_Original" in master.columns:
        master["key"] = master["Name_Original"].astype(str).str.lower().str.strip()
    elif "key" in master.columns:
        master["key"] = master["key"].astype(str).str.lower().str.strip()
    elif "col" in master.columns:
        master["key"] = master["col"].astype(str).str.lower().str.strip()
    else:
        warn(f"03_master_data.csv: no Name_Original/key/col column. "
             f"Columns: {list(master.columns)[:8]}")
        return {k: np.nan for k in well_keys}
    lut = dict(zip(master["key"], master["beta_3_drainage"]))
    return {k: float(lut.get(k, np.nan)) for k in well_keys}


def load_well_spans(well_keys: list[str]) -> pd.DataFrame:
    """Compute each well's observation span within the 2011–2025 window."""
    levels = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    levels.columns = [c.strip().lower() for c in levels.columns]
    records = []
    for key in well_keys:
        if key not in levels.columns:
            warn(f"well {key} not in INT_WELLS_CLEAN — skipping")
            records.append(dict(key=key, first_obs=pd.NaT, last_obs=pd.NaT, T_months=np.nan))
            continue
        ser = levels[key].dropna()
        ser = ser[(ser.index >= WINDOW_START) & (ser.index <= WINDOW_END)]
        if ser.empty:
            warn(f"well {key}: no observations in 2011–2025 window")
            records.append(dict(key=key, first_obs=pd.NaT, last_obs=pd.NaT, T_months=np.nan))
            continue
        first = max(ser.index.min(), WINDOW_START)
        last  = ser.index.max()
        T     = (last - WINDOW_START).days / DAYS_PER_MONTH
        records.append(dict(key=key, first_obs=first, last_obs=last, T_months=T))
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Spatial-factor builder
# ---------------------------------------------------------------------------

def build_spatial_factors(
    s20,
    well_E: np.ndarray,
    well_N: np.ndarray,
    clearfell_step_mm: float,
    T_months: float,
    L_coast: float,
) -> dict:
    """Call Script 20 field builders at well coordinates and compute SLR field.

    Returns a dict of 1-D arrays (length = n_wells):
        coast_unit   — max(1−d/L, 0) spatial factor (dimensionless)
        clearfell    — clearfell_step_mm × exp(−d_fell/λ) [mm equilibrium]
        scr_2013/2015/2023  — scrape drawdown per epoch [mm loss]
        broadleaf    — full 2005→2025 increment field [mm loss]
        slr          — SLR wetting at each well (mm, positive)
    """
    gx = np.asarray(well_E, dtype=float)
    gy = np.asarray(well_N, dtype=float)
    n  = len(gx)
    zeros = np.zeros(n)

    info(f"building spatial factors at {n} well locations via Script 20 …")

    # --- Coastal unit field (h0_mm=1.0 → max(1−d/L, 0)) ---------------------
    coast_result = s20._erosion_field(gx, gy, h0_mm=1.0)
    coast_unit   = np.nan_to_num(coast_result[0], nan=0.0) if coast_result[0] is not None else zeros.copy()

    # --- SLR: erfc diffusion from western coastal front ----------------------
    # Rate from Script 20 constants (SLR_RISE_M / SLR_WINDOW_YEARS × 1000)
    slr_rate_mm_yr = float(s20.SLR_RISE_M) / float(s20.SLR_WINDOW_YEARS) * 1000.0
    slr_total_mm   = slr_rate_mm_yr * (T_months / 12.0)
    _D_M2DAY       = DRAWDOWN_K_MDAY * DRAWDOWN_B_M / _SY_REP   # ≈ 500 m²/day
    diff_len        = np.sqrt(_D_M2DAY * (T_months / 12.0) * 365.0)
    d_coast         = np.where(coast_unit > 0.001,
                                (1.0 - coast_unit) * L_coast,
                                L_coast + 500.0)   # inland: approximate d > L
    slr = slr_total_mm * _erfc(d_coast / (2.0 * diff_len))
    info(f"  SLR: {slr_total_mm:.0f} mm total  diff_len={diff_len:.0f} m  "
         f"site range {slr.min():.0f}–{slr.max():.0f} mm")

    # --- λ from forest field (for clearfell felling-polygon distance) ---------
    for_result = s20._forest_field(gx, gy)
    fLam = float(for_result[2]) if for_result[2] is not None else None

    # --- Clearfell: felling polygon × exp(−d_fell/λ) -------------------------
    clearfell = zeros.copy()
    if fLam is not None:
        try:
            import geopandas as gpd
            from shapely.geometry import Point as _Pt
            gdf = gpd.read_file(str(paths.DATA_KML_FEATURES),
                                driver="KML").to_crs("EPSG:27700")
            name_col  = gdf["Name"].fillna("").astype(str)
            fell_geom = None
            for idx, gdf_row in gdf.iterrows():
                nm = name_col.iloc[idx].lower()
                if "felling" in nm or "experiment" in nm:
                    fell_geom = gdf_row.geometry
                    break
            if fell_geom is not None:
                d_fell    = np.array([fell_geom.distance(_Pt(x, y))
                                      for x, y in zip(gx.ravel(), gy.ravel())])
                clearfell = clearfell_step_mm * np.exp(-d_fell / fLam)
            else:
                warn("felling polygon not found in KML — clearfell zeroed")
        except Exception as exc:
            warn(f"clearfell field failed ({exc}) — zeroed")

    # --- Scrape fields per epoch ---------------------------------------------
    def _get_scrape(epoch_set: set[str]) -> np.ndarray:
        res = s20._scrape_field(gx, gy, epochs=epoch_set)
        if res[0] is None:
            return zeros.copy()
        return np.nan_to_num(res[0], nan=0.0)

    scr_2013 = _get_scrape({"Feb 2013"})
    scr_2015 = _get_scrape({"April 2015"})
    scr_2023 = _get_scrape({"Oct 2023"})

    # --- Broadleaf field (full 2005→2025 increment) --------------------------
    bl_result = s20._broadleaf_field(gx, gy)
    broadleaf = np.nan_to_num(bl_result[0], nan=0.0) if bl_result[0] is not None else zeros.copy()

    info(f"  coast_unit range: {coast_unit.min():.3f}–{coast_unit.max():.3f}")
    info(f"  clearfell range:  {clearfell.min():.1f}–{clearfell.max():.1f} mm")
    info(f"  scrape-2015 range: {scr_2015.min():.1f}–{scr_2015.max():.1f} mm")
    info(f"  broadleaf range:  {broadleaf.min():.1f}–{broadleaf.max():.1f} mm")

    return dict(
        coast_unit=coast_unit,
        clearfell=clearfell,
        scr_2013=scr_2013,
        scr_2015=scr_2015,
        scr_2023=scr_2023,
        broadleaf=broadleaf,
        slr=slr,
    )


# ---------------------------------------------------------------------------
# Core per-well prediction
# ---------------------------------------------------------------------------

def compute_predictions(
    df36: pd.DataFrame,
    spans: pd.DataFrame,
    b3_lut: dict[str, float],
    spatial: dict,
    delta0: float,
) -> pd.DataFrame:
    """Compute predicted and observed Δh (mm) for each well.

    Coastal amplitude uses the calibrated formula:
        h0_mm = COAST_RETREAT_EFFECTIVE_M × (T_yr / REF_WINDOW_YR) × δ₀ / retreat_rate

    Sign convention: positive = head rise, negative = head fall.
    """
    records    = []
    spans_lut  = dict(zip(spans["key"], spans.itertuples(index=False)))
    well_list  = list(df36.itertuples(index=False))

    for idx, row in enumerate(well_list):
        key = row.key

        sp = spans_lut.get(key)
        if sp is None or pd.isna(getattr(sp, "T_months", np.nan)):
            warn(f"  {key}: no observation span — skipping")
            continue
        first_obs = sp.first_obs
        last_obs  = sp.last_obs
        T_months  = float(sp.T_months)

        b3       = float(b3_lut.get(key, np.nan))
        b3_valid = (not np.isnan(b3)) and (b3 > 0.0)
        b3_eff   = b3 if b3_valid else 0.0

        # Spatial factors at this well
        coast_unit_i = float(spatial["coast_unit"][idx])
        cf_h_inf     = float(spatial["clearfell"][idx])
        s13          = float(spatial["scr_2013"][idx])
        s15          = float(spatial["scr_2015"][idx])
        s23          = float(spatial["scr_2023"][idx])
        bl_full      = float(spatial["broadleaf"][idx])
        slr_i        = float(spatial["slr"][idx])        # positive

        # === COASTAL (ramp, calibrated amplitude) ============================
        h0_coast     = (COAST_RETREAT_EFFECTIVE_M
                        * (T_months / 12.0 / REF_WINDOW_YR)
                        * delta0 / COAST_RETREAT_RATE)
        coast_linear = h0_coast * coast_unit_i
        coast_rf     = _ramp_factor(b3_eff if b3_valid else 0.0, T_months)
        coast_pred   = -coast_linear * (coast_rf if b3_valid else 1.0)

        # === SLR (positive — wetting) ========================================
        slr_pred = slr_i   # already computed per-well in build_spatial_factors

        # === CLEARFELL (step, Path B) =========================================
        if isinstance(first_obs, pd.Timestamp) and first_obs > INTERVENTION_DATE:
            clearfell_pred = 0.0
        else:
            t_cf           = max(0.0, (last_obs - INTERVENTION_DATE).days / DAYS_PER_MONTH)
            cf_step_f      = _step_factor(b3_eff, t_cf) if b3_valid else 1.0
            clearfell_pred = cf_h_inf * cf_step_f

        # === SCRAPES (step, per epoch) ========================================
        def _scr_contrib(event_date, scr_spatial):
            if event_date > last_obs:
                return 0.0
            t   = max(0.0, (last_obs - event_date).days / DAYS_PER_MONTH)
            f   = _step_factor(b3_eff, t) if b3_valid else 1.0
            return -float(scr_spatial) * f

        scr_2013_pred = _scr_contrib(SCRAPE_EPOCH_DATES["Feb 2013"],   s13)
        scr_2015_pred = _scr_contrib(SCRAPE_EPOCH_DATES["April 2015"], s15)
        scr_2023_pred = _scr_contrib(SCRAPE_EPOCH_DATES["Oct 2023"],   s23)
        scr_total     = scr_2013_pred + scr_2015_pred + scr_2023_pred

        # === BROADLEAF (ramp, 2011→2025 window fraction) =====================
        # BL_WINDOW_FRACTION = 0.70 for the 2011-2025 window (canopy 0.58→1.0)
        T_bl_months = (last_obs - WINDOW_START).days / DAYS_PER_MONTH
        bl_window   = bl_full * BL_WINDOW_FRACTION
        bl_linear   = bl_window  # full window-increment is the linear accumulation
        bl_rf       = _ramp_factor(b3_eff if b3_valid else 0.0, T_bl_months)
        bl_pred     = -bl_linear * (bl_rf if b3_valid else 1.0)

        # === TOTALS ===========================================================
        total_pred  = coast_pred + slr_pred + clearfell_pred + scr_total + bl_pred
        observed_dh = getattr(row, SLOPE_COL) * (T_months / 12.0)
        residual    = total_pred - observed_dh

        excl_reason = EXCL_NAMED.get(key, "")

        records.append(dict(
            key=key,
            col=getattr(row, "col", key),
            Cluster=int(row.Cluster) if not pd.isna(row.Cluster) else np.nan,
            E=float(row.E), N=float(row.N),
            first_obs=first_obs, last_obs=last_obs,
            T_months=round(T_months, 1),
            b3_drainage=b3,
            b3_correction_valid=b3_valid,
            exclude_named=bool(excl_reason),
            exclude_reason=excl_reason,
            coast_pred=round(coast_pred, 1),
            slr_pred=round(slr_pred, 1),
            clearfell_pred=round(clearfell_pred, 1),
            scr_2013_pred=round(scr_2013_pred, 1),
            scr_2015_pred=round(scr_2015_pred, 1),
            scr_2023_pred=round(scr_2023_pred, 1),
            bl_pred=round(bl_pred, 1),
            total_pred=round(total_pred, 1),
            observed_dh=round(observed_dh, 1),
            residual=round(residual, 1),
        ))

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Scatter plot
# ---------------------------------------------------------------------------

def plot_scatter(df: pd.DataFrame, dpi: int = 150) -> None:
    """Predicted-vs-observed scatter; named exclusions shown as hollow markers."""
    with plt.rc_context(MPL_RC):
        fig, ax = plt.subplots(figsize=(7.5, 7.5))

        colours  = config.get_cluster_colours()
        in_stats = df[df["b3_correction_valid"] & ~df["exclude_named"]].copy()
        b3_flag  = df[~df["b3_correction_valid"]].copy()
        excl     = df[df["exclude_named"]].copy()

        # Stats
        if len(in_stats) >= 3:
            r_val, p_val = pearsonr(in_stats["total_pred"], in_stats["observed_dh"])
            rmse         = float(np.sqrt(np.mean(in_stats["residual"] ** 2)))
        else:
            r_val = p_val = rmse = np.nan

        # Reference lines
        all_vals = pd.concat([df["total_pred"], df["observed_dh"]]).dropna()
        lim = max(abs(all_vals.min()), abs(all_vals.max())) * 1.15
        lim = max(lim, 100.0)
        ax.plot([-lim, lim], [-lim, lim], color="#999999", lw=0.9, ls="--",
                zorder=1, label="1:1")
        ax.axhline(0, color="#cccccc", lw=0.6, zorder=0)
        ax.axvline(0, color="#cccccc", lw=0.6, zorder=0)

        # In-stats wells (cluster colours)
        for cid in sorted(in_stats["Cluster"].dropna().unique()):
            sub = in_stats[in_stats["Cluster"] == cid]
            col = colours.get(int(cid), "#444444")
            mrk = CLUSTER_MARKERS.get(int(cid), "o")
            ax.scatter(sub["total_pred"], sub["observed_dh"],
                       c=col, marker=mrk, edgecolor="k", lw=0.6, s=60, zorder=4,
                       label=CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))

        # β₃ ≤ 0 flagged
        if not b3_flag.empty:
            ax.scatter(b3_flag["total_pred"], b3_flag["observed_dh"],
                       facecolor="none", edgecolor="#888888", lw=1.5,
                       marker="^", s=60, zorder=4, label="β₃ ≤ 0 (invalid corr.)")

        # Named exclusions
        if not excl.empty:
            ax.scatter(excl["total_pred"], excl["observed_dh"],
                       facecolor="none", edgecolor="#cc0000", lw=1.5,
                       marker="s", s=80, zorder=4, label="named exclusion")
            for _, ow in excl.iterrows():
                ax.annotate(ow["col"].upper(),
                            xy=(ow["total_pred"], ow["observed_dh"]),
                            xytext=(4, 4), textcoords="offset points",
                            fontsize=7.5, color="#cc0000")

        # Outlier labels (in-stats set)
        if not np.isnan(rmse):
            thresh   = OUTLIER_THRESHOLD * rmse
            outliers = in_stats[in_stats["residual"].abs() > thresh]
            for _, ow in outliers.iterrows():
                ax.annotate(ow["col"].upper(),
                            xy=(ow["total_pred"], ow["observed_dh"]),
                            xytext=(4, 4), textcoords="offset points",
                            fontsize=7.5, color="#333333")

        # Stats box
        if not np.isnan(r_val):
            stat_txt = (f"r = {r_val:.2f}  (n = {len(in_stats)})\n"
                        f"RMSE = {rmse:.0f} mm")
            ax.text(0.05, 0.95, stat_txt, transform=ax.transAxes,
                    fontsize=9, va="top",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec="#aaaaaa", alpha=0.9))

        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xlabel("Modelled Δh 2011–2025 (mm)", fontsize=10)
        ax.set_ylabel("Observed Δh 2011–2025 (mm, Script 36)", fontsize=10)
        ax.set_title("Driver-change map validation — predicted vs observed (2011–2025)",
                     fontsize=11, pad=8)
        ax.legend(fontsize=8, loc="lower right", framealpha=0.9)
        fig.tight_layout()
        fig.savefig(OUT_SCATTER, dpi=dpi)
        plt.close(fig)
    saved(OUT_SCATTER)


# ---------------------------------------------------------------------------
# Residual map
# ---------------------------------------------------------------------------

def plot_residual_map(df: pd.DataFrame, dpi: int = 150) -> None:
    """IDW map of residual = (total_pred − observed_dh) in mm."""
    # Drop any wells with NaN coordinates or residual (failed span lookups)
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
        cbar.set_label("Residual (mm): model − observed", fontsize=9)
        ax.set_title(
            "Driver validation residual map — 2011–2025\n"
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

def write_results(df: pd.DataFrame) -> None:
    """Write summary statistics and per-well table to OUT_RESULTS."""
    in_stats = df[df["b3_correction_valid"] & ~df["exclude_named"]]
    b3_flag  = df[~df["b3_correction_valid"]]
    excl_nmd = df[df["exclude_named"]]
    lines    = ["37_driver_validation — results summary (2011–2025)", "=" * 57]

    lines.append(f"n total          : {len(df)}")
    lines.append(f"n in r/RMSE      : {len(in_stats)}  (β₃ > 0 and not named exclusion)")
    lines.append(f"n β₃ ≤ 0 flagged : {len(b3_flag)}")
    lines.append(f"n named exclusions: {len(excl_nmd)}")

    if excl_nmd.shape[0] > 0:
        lines.append("\nNamed exclusions:")
        for _, ow in excl_nmd.iterrows():
            lines.append(f"  {ow['col'].upper():8s} — {ow['exclude_reason']}")

    if len(in_stats) >= 3:
        r_val, p_val = pearsonr(in_stats["total_pred"], in_stats["observed_dh"])
        rmse         = float(np.sqrt(np.mean(in_stats["residual"] ** 2)))
        lines.append(f"\nr (Pearson, in-stats): {r_val:.3f}  (p = {p_val:.4f})")
        lines.append(f"RMSE (in-stats)       : {rmse:.1f} mm")
    else:
        lines.append("\nInsufficient in-stats wells for r/RMSE.")
        rmse = np.nan

    lines.append("\nPer-cluster means (mm, all wells):")
    for cid in sorted(df["Cluster"].dropna().unique()):
        sub = df[df["Cluster"] == cid]
        lbl = CLUSTER_LABELS.get(int(cid), f"C{int(cid)}")
        lines.append(f"  {lbl:20s}  pred {sub['total_pred'].mean():+7.1f}  "
                     f"obs {sub['observed_dh'].mean():+7.1f}  "
                     f"resid {sub['residual'].mean():+7.1f}  n={len(sub)}")

    if not np.isnan(rmse):
        thresh  = OUTLIER_THRESHOLD * rmse
        outs    = in_stats[in_stats["residual"].abs() > thresh].sort_values(
                      "residual", key=abs, ascending=False)
        if not outs.empty:
            lines.append(f"\nOutliers (|resid| > {OUTLIER_THRESHOLD:.1f} × RMSE = {thresh:.0f} mm):")
            for _, ow in outs.iterrows():
                lines.append(
                    f"  {ow['col'].upper():8s}  pred {ow['total_pred']:+7.1f}  "
                    f"obs {ow['observed_dh']:+7.1f}  resid {ow['residual']:+7.1f}  "
                    f"C{int(ow['Cluster']) if not pd.isna(ow['Cluster']) else '?'}")

    lines.append("\n" + "-" * 57)
    lines.append(f"{'well':8s}  {'C':2s}  {'T_yr':5s}  {'coast':7s}  {'slr':5s}  "
                 f"{'cf':7s}  {'scr':7s}  {'bl':7s}  {'total':7s}  {'obs':7s}  {'resid':7s}")
    for _, ow in df.sort_values("residual").iterrows():
        scr_sum = ow["scr_2013_pred"] + ow["scr_2015_pred"] + ow["scr_2023_pred"]
        flag = ""
        if not ow["b3_correction_valid"]:
            flag = " *"
        elif ow["exclude_named"]:
            flag = " !"
        c_lbl = str(int(ow["Cluster"])) if not pd.isna(ow["Cluster"]) else "?"
        lines.append(
            f"{str(ow['col']).upper():8s}  {c_lbl:>2}  "
            f"{ow['T_months']/12:5.1f}  {ow['coast_pred']:+7.1f}  "
            f"{ow['slr_pred']:+5.1f}  {ow['clearfell_pred']:+7.1f}  "
            f"{scr_sum:+7.1f}  {ow['bl_pred']:+7.1f}  {ow['total_pred']:+7.1f}  "
            f"{ow['observed_dh']:+7.1f}  {ow['residual']:+7.1f}{flag}"
        )

    lines.append("\n* β₃ ≤ 0: correction = 1.0; excluded from r/RMSE.")
    lines.append("! named exclusion: excluded from r/RMSE (see table above).")
    OUT_RESULTS.write_text("\n".join(lines) + "\n")
    saved(OUT_RESULTS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    banner("37", "Driver-Change Map Validation — Predicted vs Observed", version=__version__)

    phase(1, "Load Script 36 per-well data and well spans (2011–2025, n≤55)")
    df36  = load_script36_wells()
    keys  = list(df36["key"])
    spans = load_well_spans(keys)
    b3    = load_master_b3(keys)

    n_b3_invalid = sum(1 for v in b3.values() if np.isnan(v) or v <= 0.0)
    n_named_excl = sum(1 for k in keys if k in EXCL_NAMED)
    if n_b3_invalid:
        note(f"{n_b3_invalid} wells have β₃ ≤ 0 or NaN — flagged, corrections set to 1.0")
    if n_named_excl:
        note(f"{n_named_excl} named exclusions: {', '.join(k.upper() for k in keys if k in EXCL_NAMED)}")

    phase(2, "Load live parameters from upstream CSVs")
    delta0, L_coast = _load_coastal_fit()
    clearfell_step  = _load_clearfell_step()

    # Representative T_months for SLR (use modal window length ≈ 179 months)
    modal_T = float(spans["T_months"].dropna().median())
    info(f"median T_months: {modal_T:.1f}  "
         f"(BL_WINDOW_FRACTION={BL_WINDOW_FRACTION:.3f}  "
         f"COAST_RETREAT_EFFECTIVE_M={COAST_RETREAT_EFFECTIVE_M} m)")

    phase(3, "Load Script 20 and build spatial factors")
    step("importing Script 20 via importlib …")
    s20 = _load_s20()
    info("Script 20 loaded")

    spatial = build_spatial_factors(
        s20, df36["E"].values, df36["N"].values,
        clearfell_step, modal_T, L_coast
    )

    phase(4, "Compute per-well predictions with β₃ temporal corrections")
    df_pred = compute_predictions(df36, spans, b3, spatial, delta0)
    info(f"predictions computed for {len(df_pred)} wells")

    in_stats = df_pred[df_pred["b3_correction_valid"] & ~df_pred["exclude_named"]]
    if len(in_stats) >= 3:
        r_val, _ = pearsonr(in_stats["total_pred"], in_stats["observed_dh"])
        rmse     = float(np.sqrt(np.mean(in_stats["residual"] ** 2)))
        result("Pearson r (in-stats)", f"{r_val:.3f}  (n={len(in_stats)})")
        result("RMSE (in-stats)", f"{rmse:.1f} mm")
    for cid in sorted(df_pred["Cluster"].dropna().unique()):
        sub = df_pred[df_pred["Cluster"] == cid]
        result(f"C{int(cid)} mean residual",
               f"{sub['residual'].mean():+.1f} mm  (n={len(sub)})")

    phase(5, "Save outputs")
    DIR_37.mkdir(parents=True, exist_ok=True)
    df_pred.to_csv(OUT_PER_WELL, index=False)
    saved(OUT_PER_WELL)

    plot_scatter(df_pred)
    plot_residual_map(df_pred)
    write_results(df_pred)

    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
