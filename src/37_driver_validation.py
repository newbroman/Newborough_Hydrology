"""
37_driver_validation.py
=======================
Predicted-vs-observed validation of the modelled 2005–2025 driver-change field
against Script 36 climate-removed per-well secular trends (n ≈ 30).

For each well in the Script 36 primary (2005–2025) coverage set:
  1. Samples four driver fields from Script 20 at the well's (E, N) location.
  2. Applies per-well, window-matched temporal corrections via β₃ (month⁻¹):
       Ramp drivers  — factor = 1 − (1 − exp(−β₃T)) / (β₃T)      [coastal, broadleaf]
       Step drivers  — factor = 1 − exp(−β₃ t)                     [clearfell, scrapes]
  3. Compares total_pred (mm) against Script 36 slope × window span (mm).
  4. Outputs a validation scatter, IDW residual map, per-well CSV, and results text.

Driver fields (positive = head loss, converted to signed Δh):
  • Coastal chronic retreat  — ramp, Script 25 δ₀/L, β₃-corrected over well's window
  • Clearfell recovery       — step, Path B (+120 mm BACI), sign-reversed (gain)
  • Scraping drawdown        — step per epoch (Feb 2013 / Apr 2015 / Oct 2023)
  • Broadleaf increment      — ramp from 2005, _broadleaf_field() full increment

SLR omitted (small signal over the 20-yr window; not a driver-change component here).
Standing-pine canopy omitted (equilibrium both epochs, cancels).

Step 40/46, Phase 15 — Observed Differential Change, Envelope, and Validation.
"""

__version__ = "1.0.2"
# 1.0.2 — load_master_b3 fix (2026-07-06): 03_master_data.csv stores the
#          well name in Name_Original; derive key via
#          Name_Original.str.lower().str.strip() following Script 36
#          load_inputs() convention. Fallback chain: Name_Original → key → col.
# 1.0.1
# 1.0.1 — clearfell geometry fix (2026-07-06): spatial factor now uses the
#          felling polygon (KML "felling"/"experiment" feature) instead of the
#          forest boundary, matching _driver_change_net() in Script 20 v1.32.0.
#          Lambda still taken from _forest_field()[2]. No change to any other
#          driver field, temporal corrections, or output columns.
# 1.0.0 — initial release (2026-07-06).  Per-well predicted-vs-observed
#          validation with β₃-based ramp/step temporal corrections. Imports
#          Script 20 field builders via importlib; all constants from config.py
#          and paths.py; Path B clearfell from 10a_report_numbers.csv.

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
    OUT_03_MECHANISTIC_TABLE,
    INT_WTF_WELL_SY,
)
from utils.config import (
    CLUSTER_LABELS, CLUSTER_MARKERS,
    DRAWDOWN_H0_MM,
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
# Output paths (defined in paths.py)
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
WINDOW_START   = pd.Timestamp("2005-01-01")
WINDOW_END     = pd.Timestamp("2025-12-01")
DAYS_PER_MONTH = 30.4375
FULL_WINDOW_MONTHS = 20 * 12  # 240 — the nominal 2005→2025 broadleaf-ramp length

# Epoch label → event Timestamp (for per-epoch scrape step corrections)
SCRAPE_EPOCH_DATES: dict[str, pd.Timestamp] = {
    "Feb 2013":   SCRAPING_DATE_0,
    "April 2015": SCRAPING_DATE,
    "Oct 2023":   SCRAPING_DATE_2,
}

# Outlier labelling threshold (fraction of RMSE)
OUTLIER_THRESHOLD = 1.5

MPL_RC = {
    "font.family":        "sans-serif",
    "font.size":          10,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
}

# ---------------------------------------------------------------------------
# Script 20 import via importlib (numeric filename not importable directly)
# ---------------------------------------------------------------------------

def _load_s20():
    """Load Script 20 spatial figures module for field-builder access.

    Uses importlib.util so the numeric filename is not a barrier. The module's
    own sys.path.insert puts utils/ in scope, so all its constants and helper
    functions resolve correctly.
    """
    path = Path(__file__).parent / "20_spatial_figures.py"
    spec = importlib.util.spec_from_file_location("_s20_spatial", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Live-value loaders (same source CSVs as Script 20 / Script 09f)
# ---------------------------------------------------------------------------

def _load_coastal_fit() -> tuple[float, float]:
    """δ₀ (mm/yr, positive magnitude) and L (m) — Script 25 forest-free
    linear-capped row.  Falls back to a documented snapshot on first-pass run."""
    snapshot = (29.39, 971.0)
    try:
        df  = pd.read_csv(OUT_25_FIT_PARAMETERS)
        row = df[(df["source"] == "forest_free") & (df["model"] == "linear_capped")]
        if row.empty:
            row = df[(df["source"] == "full") & (df["model"] == "linear_capped")]
        if row.empty:
            warn("Script 25 CSV has no linear_capped row — using snapshot")
            return snapshot
        d0 = abs(float(row["delta_0_mm_yr"].iloc[0]))
        L  = float(row["L_m"].iloc[0])
        info(f"coastal fit (live): δ₀ = {d0:.2f} mm/yr, L = {L:.0f} m")
        return d0, L
    except Exception as exc:
        warn(f"cannot read Script 25 fit ({exc}) — using snapshot")
        return snapshot


def _load_clearfell_step() -> float:
    """Clearfell ANCOVA step (mm) from 10a_report_numbers.csv — Path B.

    Row: ANCOVA_Forest_Impact_clearfell_step.  Value column index 3 (numeric).
    Falls back to pipeline default on a first-pass run before Script 10a."""
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
    """Fraction of linear ramp accumulation (r × T) realised after T_months.

    Derivation: for a boundary head declining at constant rate r (mm/month),
    the SSM well-head response after T months is:

        Δh(T) = r × T × [1 − (1 − exp(−β₃ T)) / (β₃ T)]

    so the correction factor f = 1 − (1 − exp(−β₃ T)) / (β₃ T).
    Limits: f → 1 as β₃ T → ∞ (fast wells track the boundary);
            f → β₃ T / 2 as β₃ T → 0 (slow wells lag far behind).

    Returns 1.0 when b3 ≤ 0 or T_months ≤ 0 (flag wells separately).
    """
    if b3 <= 0.0 or T_months <= 0.0:
        return 1.0
    x = b3 * T_months
    if x > 50.0:          # exp(−x) ≈ 0; factor → 1
        return 1.0
    return float(1.0 - (1.0 - np.exp(-x)) / x)


def _step_factor(b3: float, t_months: float) -> float:
    """Fraction of step-change equilibrium amplitude realised after t_months.

        factor = 1 − exp(−β₃ t)

    Returns 0.0 for b3 ≤ 0 (β₃ correction undefined; caller should flag).
    Returns 1.0 for t_months ≤ 0 (event not in window or at window end).
    """
    if b3 <= 0.0:
        return 0.0
    if t_months <= 0.0:
        return 1.0
    return float(1.0 - np.exp(-b3 * t_months))


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_script36_wells() -> pd.DataFrame:
    """Load Script 36 per-well CSV; return one row per well that passed the
    2005–2025 coverage filter (slope_mm_yr_2005_2025 is not NaN)."""
    df = pd.read_csv(OUT_36_PER_WELL)
    df["key"] = df["key"].str.strip().str.lower()
    col = "slope_mm_yr_2005_2025"
    if col not in df.columns:
        raise KeyError(
            f"Column '{col}' not found in Script 36 CSV. "
            "Run Script 36 (step 39) before Script 37."
        )
    df = df.dropna(subset=[col]).copy()
    info(f"Script 36 wells (2005–2025 coverage): {len(df)}")
    return df


def load_master_b3(well_keys: list[str]) -> dict[str, float]:
    """Return {key: beta_3_drainage (month⁻¹)} for each well in well_keys.

    Reads INT_MASTER_DATA (03_master_data.csv), beta_3_drainage column.
    The CSV stores the well name in Name_Original (Script 36 convention);
    falls back to 'key' or 'col' for robustness across pipeline versions.
    Keys not in the master get NaN; the caller must flag these."""
    master = pd.read_csv(INT_MASTER_DATA)
    # Derive the 'key' column following Script 36 load_inputs() convention
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
    """Compute each well's actual observation span within the 2005–2025 window.

    Reads INT_WELLS_CLEAN monthly level series; clamps to WINDOW_START /
    WINDOW_END.  Returns DataFrame with columns:
        key, first_obs (Timestamp), last_obs (Timestamp), T_months (float)
    """
    levels = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    levels.columns = [c.strip().lower() for c in levels.columns]
    records = []
    for key in well_keys:
        if key not in levels.columns:
            warn(f"well {key} not in INT_WELLS_CLEAN — skipping span")
            records.append(dict(key=key, first_obs=pd.NaT,
                                last_obs=pd.NaT, T_months=np.nan))
            continue
        ser = levels[key].dropna()
        ser = ser[(ser.index >= WINDOW_START) & (ser.index <= WINDOW_END)]
        if ser.empty:
            warn(f"well {key} has no observations in 2005–2025 window")
            records.append(dict(key=key, first_obs=pd.NaT,
                                last_obs=pd.NaT, T_months=np.nan))
            continue
        first = max(ser.index.min(), WINDOW_START)
        last  = ser.index.max()
        T     = (last - WINDOW_START).days / DAYS_PER_MONTH
        records.append(dict(key=key, first_obs=first, last_obs=last, T_months=T))
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Spatial-factor builder (calls Script 20 field builders at well coordinates)
# ---------------------------------------------------------------------------

def build_spatial_factors(
    s20,
    well_E: np.ndarray,
    well_N: np.ndarray,
    clearfell_step_mm: float,
) -> dict:
    """Call Script 20 field builders at the 30 well coordinates (not a full grid).

    Returns a dict of 1-D numpy arrays (length = n_wells), each representing
    a UNIT or FULL spatial factor at every well location:

        coast_unit   — max(1 − d/L, 0), i.e. _erosion_field() with h0_mm=1.0
        clearfell    — clearfell_step_mm × exp(−d/λ)  [mm equilibrium; rise]
        scr_2013     — scrape drawdown field, Feb 2013 cuts only  [mm loss]
        scr_2015     — scrape drawdown field, April 2015 cuts     [mm loss]
        scr_2023     — scrape drawdown field, Oct 2023 cuts       [mm loss]
        broadleaf    — full 2005→2025 increment field             [mm loss]
        H0_for       — forest-field source amplitude (mm; for scaling check)
    """
    gx = np.asarray(well_E, dtype=float)
    gy = np.asarray(well_N, dtype=float)
    n  = len(gx)
    zeros = np.zeros(n)

    info(f"building spatial factors at {n} well locations via Script 20 …")

    # --- Coastal unit field -------------------------------------------------
    coast_result = s20._erosion_field(gx, gy, h0_mm=1.0)
    coast_unit   = np.nan_to_num(coast_result[0], nan=0.0) if coast_result[0] is not None else zeros.copy()

    # --- lambda from forest field -------------------------------------------
    # _forest_field() provides the propagation length lambda (m); the clearfell
    # SPATIAL factor uses the felling polygon (not the forest boundary), matching
    # _driver_change_net() in Script 20 v1.32.0+.
    for_result = s20._forest_field(gx, gy)
    fLam       = float(for_result[2]) if for_result[2] is not None else None

    # --- Clearfell field: clearfell_mm x exp(-d_fell/lambda) ---------------
    # Distance from each well to the felling-polygon edge (KML "felling" or
    # "experiment" feature), with clearfell_step_mm as the Path B source amplitude.
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
                warn("felling polygon not found in KML -- clearfell contribution zeroed")
        except Exception as exc:
            warn(f"clearfell field failed ({exc}) -- contribution zeroed")

    # --- Scrape fields per epoch -------------------------------------------
    def _get_scrape(epoch_set: set[str]) -> np.ndarray:
        res = s20._scrape_field(gx, gy, epochs=epoch_set)
        if res[0] is None:
            return zeros.copy()
        return np.nan_to_num(res[0], nan=0.0)

    scr_2013 = _get_scrape({"Feb 2013"})
    scr_2015 = _get_scrape({"April 2015"})
    scr_2023 = _get_scrape({"Oct 2023"})

    # --- Broadleaf field (full 2005→2025 increment) ------------------------
    bl_result = s20._broadleaf_field(gx, gy)
    if bl_result[0] is not None:
        broadleaf = np.nan_to_num(bl_result[0], nan=0.0)
    else:
        warn("_broadleaf_field() returned None — broadleaf contribution zeroed")
        broadleaf = zeros.copy()

    info(f"  coast range: {coast_unit.min():.3f}–{coast_unit.max():.3f} (unit)")
    info(f"  clearfell range: {clearfell.min():.1f}–{clearfell.max():.1f} mm")
    info(f"  scrape 2015 range: {scr_2015.min():.1f}–{scr_2015.max():.1f} mm")
    info(f"  broadleaf range: {broadleaf.min():.1f}–{broadleaf.max():.1f} mm")

    return dict(
        coast_unit=coast_unit,
        clearfell=clearfell,
        scr_2013=scr_2013,
        scr_2015=scr_2015,
        scr_2023=scr_2023,
        broadleaf=broadleaf,
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
    """Compute predicted Δh (mm) and observed Δh (mm) for each well.

    Signed convention: positive = head rise, negative = head fall.
    Columns in output DataFrame:
        key, col, Cluster, E, N, first_obs, last_obs, T_months,
        b3_drainage, b3_correction_valid,
        coast_pred, clearfell_pred, scr_2013_pred, scr_2015_pred, scr_2023_pred,
        bl_pred, total_pred, observed_dh, residual
    """
    slope_col = "slope_mm_yr_2005_2025"
    records   = []
    spans_lut = dict(zip(spans["key"], spans.itertuples(index=False)))
    well_list = list(df36.itertuples(index=False))

    for idx, row in enumerate(well_list):
        key = row.key

        # --- Observation span ---
        sp = spans_lut.get(key)
        if sp is None or pd.isna(getattr(sp, "T_months", np.nan)):
            warn(f"  {key}: no observation span — skipping")
            continue
        first_obs = sp.first_obs
        last_obs  = sp.last_obs
        T_months  = float(sp.T_months)

        # --- β₃ ---
        b3       = float(b3_lut.get(key, np.nan))
        b3_valid = (not np.isnan(b3)) and (b3 > 0.0)

        # --- Spatial amplitudes at this well ---
        coast_unit = float(spatial["coast_unit"][idx])
        cf_h_inf   = float(spatial["clearfell"][idx])    # mm equilibrium
        s13        = float(spatial["scr_2013"][idx])      # mm loss
        s15        = float(spatial["scr_2015"][idx])
        s23        = float(spatial["scr_2023"][idx])
        bl_full    = float(spatial["broadleaf"][idx])     # full 2005→2025 mm loss

        b3_eff = b3 if b3_valid else 0.0   # use 0 only for step factor (→1.0)

        # === COASTAL CHRONIC (ramp) ========================================
        coast_linear = (T_months / 12.0) * delta0 * coast_unit   # mm linear
        coast_rf     = _ramp_factor(b3_eff if b3_valid else 0.0, T_months)
        coast_pred   = -coast_linear * (coast_rf if b3_valid else 1.0)   # loss → negative

        # === CLEARFELL (step) =============================================
        if isinstance(first_obs, pd.Timestamp) and first_obs > INTERVENTION_DATE:
            clearfell_pred = 0.0
        else:
            t_cf            = max(0.0, (last_obs - INTERVENTION_DATE).days / DAYS_PER_MONTH)
            cf_step_f       = _step_factor(b3_eff, t_cf) if b3_valid else 1.0
            clearfell_pred  = cf_h_inf * cf_step_f        # gain → positive

        # === SCRAPES (step, per epoch) =====================================
        scr_total = 0.0
        for epoch_name, scr_spatial in [
            ("Feb 2013",   s13),
            ("April 2015", s15),
            ("Oct 2023",   s23),
        ]:
            event_date = SCRAPE_EPOCH_DATES[epoch_name]
            if event_date > last_obs:
                continue   # event hasn't happened in this well's window
            t_scr   = max(0.0, (last_obs - event_date).days / DAYS_PER_MONTH)
            scr_f   = _step_factor(b3_eff, t_scr) if b3_valid else 1.0
            scr_total -= scr_spatial * scr_f         # loss → negative

        # === BROADLEAF INCREMENT (ramp from 2005) =========================
        # All 30 wells have pre-2005 data (Script 36 filter), so the ramp
        # starts at WINDOW_START for every well.
        T_bl_months = (last_obs - WINDOW_START).days / DAYS_PER_MONTH
        bl_fraction = T_bl_months / float(FULL_WINDOW_MONTHS)   # portion of 20-yr ramp seen
        bl_linear   = bl_full * bl_fraction
        bl_rf       = _ramp_factor(b3_eff if b3_valid else 0.0, T_bl_months)
        bl_pred     = -bl_linear * (bl_rf if b3_valid else 1.0)   # loss → negative

        # === TOTALS ========================================================
        # Per-epoch scrape predictions extracted for the CSV
        def _scr_epoch(epoch_name, scr_spatial):
            ed  = SCRAPE_EPOCH_DATES[epoch_name]
            if ed > last_obs:
                return 0.0
            t   = max(0.0, (last_obs - ed).days / DAYS_PER_MONTH)
            f   = _step_factor(b3_eff, t) if b3_valid else 1.0
            return -float(scr_spatial) * f

        scr_2013_pred = _scr_epoch("Feb 2013",   s13)
        scr_2015_pred = _scr_epoch("April 2015", s15)
        scr_2023_pred = _scr_epoch("Oct 2023",   s23)

        total_pred  = coast_pred + clearfell_pred + scr_total + bl_pred
        observed_dh = getattr(row, slope_col) * (T_months / 12.0)
        residual    = total_pred - observed_dh

        records.append(dict(
            key=key,
            col=getattr(row, "col", key),
            Cluster=int(row.Cluster) if not pd.isna(row.Cluster) else np.nan,
            E=float(row.E),
            N=float(row.N),
            first_obs=first_obs,
            last_obs=last_obs,
            T_months=round(T_months, 1),
            b3_drainage=b3,
            b3_correction_valid=b3_valid,
            coast_pred=round(coast_pred, 1),
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
    """Predicted-vs-observed scatter with 1:1 line, cluster colours, outlier labels."""
    with plt.rc_context(MPL_RC):
        fig, ax = plt.subplots(figsize=(7, 7))

        colours = config.get_cluster_colours()
        valid   = df[df["b3_correction_valid"]].copy()
        flagged = df[~df["b3_correction_valid"]].copy()

        # --- Stats (valid wells only) ---
        if len(valid) >= 3:
            r_val, p_val = pearsonr(valid["total_pred"], valid["observed_dh"])
            rmse         = float(np.sqrt(np.mean(valid["residual"] ** 2)))
        else:
            r_val = p_val = rmse = np.nan

        # --- 1:1 reference line ---
        all_vals = pd.concat([df["total_pred"], df["observed_dh"]]).dropna()
        lim      = max(abs(all_vals.min()), abs(all_vals.max())) * 1.15
        lim      = max(lim, 50.0)
        ax.plot([-lim, lim], [-lim, lim], color="#999999", lw=0.9,
                ls="--", zorder=1, label="1:1")
        ax.axhline(0, color="#cccccc", lw=0.6, zorder=0)
        ax.axvline(0, color="#cccccc", lw=0.6, zorder=0)

        # --- Cluster markers (valid wells) ---
        for cid in sorted(valid["Cluster"].dropna().unique()):
            sub = valid[valid["Cluster"] == cid]
            col = colours.get(int(cid), "#444444")
            mrk = CLUSTER_MARKERS.get(int(cid), "o")
            ax.scatter(sub["total_pred"], sub["observed_dh"],
                       c=col, marker=mrk, edgecolor="k", linewidth=0.6,
                       s=60, zorder=4,
                       label=CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))

        # --- Flagged wells (hollow) ---
        if not flagged.empty:
            ax.scatter(flagged["total_pred"], flagged["observed_dh"],
                       facecolor="none", edgecolor="#888888",
                       linewidth=1.5, s=60, marker="^", zorder=4,
                       label="β₃ ≤ 0 (invalid correction)")

        # --- Outlier labels ---
        if not np.isnan(rmse):
            thresh   = OUTLIER_THRESHOLD * rmse
            outliers = valid[valid["residual"].abs() > thresh]
            for _, ow in outliers.iterrows():
                ax.annotate(ow["col"].upper(),
                            xy=(ow["total_pred"], ow["observed_dh"]),
                            xytext=(4, 4), textcoords="offset points",
                            fontsize=7.5, color="#333333")

        # --- Stats box ---
        if not np.isnan(r_val):
            stat_txt = f"r = {r_val:.2f}  (n = {len(valid)})\nRMSE = {rmse:.0f} mm"
            ax.text(0.05, 0.95, stat_txt, transform=ax.transAxes,
                    fontsize=9, va="top", ha="left",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec="#aaaaaa", alpha=0.9))

        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xlabel("Modelled Δh 2005–2025 (mm)", fontsize=10)
        ax.set_ylabel("Observed Δh 2005–2025 (mm, Script 36)", fontsize=10)
        ax.set_title("Driver-change map validation — predicted vs observed",
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
    """IDW map of residual = (total_pred − observed_dh) in mm.

    Positive residual (blue): model predicts more head gain / less drying.
    Negative residual (brown/red): model predicts more drying.
    """
    with plt.rc_context(MPL_RC):
        fig, ax = plt.subplots(figsize=(11, 9))

        vmax = max(float(np.nanpercentile(df["residual"].abs(), 95)), 50.0)
        norm = TwoSlopeNorm(vcenter=0.0, vmin=-vmax, vmax=vmax)

        # Layer 1: DEM hillshade
        load_dem_hillshade(ax, paths.DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

        # Layer 2: IDW residual surface
        add_idw_surface(
            ax, df,
            value_col="residual",
            easting_col="E",
            northing_col="N",
            cmap=plt.cm.RdBu,
            norm=norm,
            alpha=0.55,
            zorder=1.5,
            apply_site_mask=True,
        )

        # Layer 3: KML features + axes
        add_kml_features(ax, paths.DATA_DIR)
        add_en_axes(ax, osgb_label=False)

        # Layer 4: well markers coloured by residual sign / cluster
        colours = config.get_cluster_colours()
        for cid in sorted(df["Cluster"].dropna().unique()):
            sub = df[df["Cluster"] == cid]
            col = colours.get(int(cid), "#444444")
            mrk = CLUSTER_MARKERS.get(int(cid), "o")
            ax.scatter(sub["E"], sub["N"], c=col, marker=mrk,
                       edgecolor="k", linewidth=0.6, s=55, zorder=5,
                       label=CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))

        # Colourbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.RdBu, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.028, pad=0.04)
        cbar.set_label("Residual (mm):  model − observed", fontsize=9)

        ax.set_title(
            "Driver validation residual map — 2005–2025\n"
            "Positive (blue) = model over-predicts wetting; "
            "negative (red) = model over-predicts drying",
            fontsize=10, pad=8,
        )
        ax.legend(fontsize=8, loc="lower left", framealpha=0.9,
                  title="cluster")
        fig.tight_layout()
        fig.savefig(OUT_RESIDUAL_MAP, dpi=dpi)
        plt.close(fig)
    saved(OUT_RESIDUAL_MAP)


# ---------------------------------------------------------------------------
# Results text
# ---------------------------------------------------------------------------

def write_results(df: pd.DataFrame) -> None:
    """Write summary statistics and per-well table to OUT_RESULTS."""
    valid   = df[df["b3_correction_valid"]]
    flagged = df[~df["b3_correction_valid"]]
    lines   = ["37_driver_validation — results summary", "=" * 55]

    n_total = len(df)
    n_valid = len(valid)
    lines.append(f"n total  : {n_total}")
    lines.append(f"n valid  : {n_valid}  (β₃ > 0)")
    lines.append(f"n flagged: {len(flagged)}  (β₃ ≤ 0, excluded from r/RMSE)")

    if n_valid >= 3:
        r_val, p_val = pearsonr(valid["total_pred"], valid["observed_dh"])
        rmse         = float(np.sqrt(np.mean(valid["residual"] ** 2)))
        lines.append(f"\nr (Pearson, valid only): {r_val:.3f}  (p = {p_val:.4f})")
        lines.append(f"RMSE (valid only)       : {rmse:.1f} mm")
    else:
        lines.append("\nInsufficient valid wells for r/RMSE.")
        rmse = np.nan

    # Per-cluster means
    lines.append("\nPer-cluster means (mm):")
    for cid in sorted(df["Cluster"].dropna().unique()):
        sub  = df[df["Cluster"] == cid]
        lbl  = CLUSTER_LABELS.get(int(cid), f"C{int(cid)}")
        p_m  = sub["total_pred"].mean()
        o_m  = sub["observed_dh"].mean()
        r_m  = sub["residual"].mean()
        lines.append(f"  {lbl:20s}  pred {p_m:+7.1f}  obs {o_m:+7.1f}  resid {r_m:+7.1f}  n={len(sub)}")

    # Largest residuals
    if not np.isnan(rmse):
        thresh  = OUTLIER_THRESHOLD * rmse
        outs    = df[df["residual"].abs() > thresh].sort_values("residual", key=abs, ascending=False)
        if not outs.empty:
            lines.append(f"\nOutliers (|residual| > {OUTLIER_THRESHOLD:.1f} × RMSE = {thresh:.0f} mm):")
            for _, ow in outs.iterrows():
                lines.append(f"  {ow['col'].upper():8s}  pred {ow['total_pred']:+7.1f}  obs {ow['observed_dh']:+7.1f}"
                             f"  resid {ow['residual']:+7.1f}  C{int(ow['Cluster']) if not pd.isna(ow['Cluster']) else '?'}")

    # Per-well table
    lines.append("\n" + "-" * 55)
    lines.append("Per-well table (mm):")
    lines.append(f"{'well':8s}  {'C':2s}  {'T_yr':5s}  {'coast':7s}  {'cf':7s}  "
                 f"{'scr':7s}  {'bl':7s}  {'total':7s}  {'obs':7s}  {'resid':7s}")
    for _, ow in df.sort_values("residual").iterrows():
        scr_sum = ow["scr_2013_pred"] + ow["scr_2015_pred"] + ow["scr_2023_pred"]
        flag    = "" if ow["b3_correction_valid"] else " *"
        lines.append(
            f"{str(ow['col']).upper():8s}  {int(ow['Cluster']) if not pd.isna(ow['Cluster']) else '?':2d}  "
            f"{ow['T_months']/12:5.1f}  {ow['coast_pred']:+7.1f}  {ow['clearfell_pred']:+7.1f}  "
            f"{scr_sum:+7.1f}  {ow['bl_pred']:+7.1f}  {ow['total_pred']:+7.1f}  "
            f"{ow['observed_dh']:+7.1f}  {ow['residual']:+7.1f}{flag}"
        )

    lines.append("\n* β₃ ≤ 0: correction factor set to 1.0 (linear/asymptotic); excluded from r/RMSE.")
    OUT_RESULTS.write_text("\n".join(lines) + "\n")
    saved(OUT_RESULTS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    banner(SCRIPT_ID, "Driver-Change Map Validation — Predicted vs Observed",
           __version__)

    phase(1, "Load Script 36 per-well data and well spans")
    df36  = load_script36_wells()
    keys  = list(df36["key"])
    spans = load_well_spans(keys)
    b3    = load_master_b3(keys)

    n_b3_invalid = sum(1 for v in b3.values() if np.isnan(v) or v <= 0.0)
    if n_b3_invalid:
        note(f"{n_b3_invalid} wells have β₃ ≤ 0 or NaN — flagged, corrections set to 1.0")

    phase(2, "Load live parameters from upstream CSVs")
    delta0, L_coast = _load_coastal_fit()
    clearfell_step  = _load_clearfell_step()

    phase(3, "Load Script 20 and build spatial factors")
    step("importing Script 20 via importlib …")
    s20 = _load_s20()
    info("Script 20 loaded")

    well_E  = df36["E"].values
    well_N  = df36["N"].values
    spatial = build_spatial_factors(s20, well_E, well_N, clearfell_step)

    phase(4, "Compute per-well predictions with β₃ temporal corrections")
    df_pred = compute_predictions(df36, spans, b3, spatial, delta0)
    info(f"predictions computed for {len(df_pred)} wells")

    valid = df_pred[df_pred["b3_correction_valid"]]
    if len(valid) >= 3:
        r_val, _ = pearsonr(valid["total_pred"], valid["observed_dh"])
        rmse     = float(np.sqrt(np.mean(valid["residual"] ** 2)))
        result("Pearson r (valid wells)", f"{r_val:.3f}")
        result("RMSE (valid wells)", f"{rmse:.1f} mm")
    for cid in sorted(df_pred["Cluster"].dropna().unique()):
        sub = df_pred[df_pred["Cluster"] == cid]
        result(f"C{int(cid)} mean residual", f"{sub['residual'].mean():+.1f} mm (n={len(sub)})")

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
