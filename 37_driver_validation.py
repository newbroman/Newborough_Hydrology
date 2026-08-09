"""
37_driver_validation.py
=======================
Per-driver scale-factor regression validating Script 20's modelled
driver-change field against Script 36's climate-corrected per-well
secular trends.

Design document: SPEC_script37_scale_factor_regression_2026-07-06.md,
Part A only (items 1-7 signed off; Part B deferred).

Method
------
Observed signal (UNCHANGED from v2.1.0, reused not refit): dh_corr,i per well
is Script 36's climate-corrected endpoint difference — b_hat fit once on
config.ACT_BHAT_WINDOW = (2005, 2017), h_corr(t) = h(t) - b_hat*CWB(t), then a
non-overlapping endpoint-mean difference with config.ACT_ENDPOINT_FRACTION
(1/3). Reused directly from Script 36's committed CSV; not refit here.

Modelling step (CHANGED, v2.x -> v3.0.0): each window is a separate OLS
regression of dh_corr on the modelled driver fields as SEPARATE regressors,
with a free spatially-uniform intercept:

    dh_corr,i = s_coast * coast_i + s_cf * clearfell_i + c + eps_i

  - coast_i, clearfell_i are the modelled amplitudes (mm) for that window,
    beta_3-corrected per well, so each scale factor s is DIMENSIONLESS
    (s = 1 => aquifer feels exactly the modelled amplitude; s < 1 => modelled
    amplitude overstated; s > 1 => understated).
  - c is a FREE uniform intercept. It absorbs the site-wide beta_1 decline
    (present at the unfelled Climate Control tier) so background drying
    cannot be laundered into s_coast. This is the key identification move
    relative to v2.x's single summed prediction.
  - Coastal amplitude per window = delta_0 * dt_mid * shape_i, where dt_mid is
    the difference between Script 36's own endpoint-group centroid years for
    that well/window (built to match Script 36's construction exactly - see
    _endpoint_group_centroids() below). delta_0 read live from
    OUT_25_FIT_PARAMETERS (forest-free linear-capped row). NOT the raw window
    length, NOT a fixed 20-yr figure.
  - Clearfell amplitude = clearfell_step_mm * exp(-d_fell/lambda), step read
    live from OUT_10A_REPORT (ANCOVA_Forest_Impact_clearfell_step x 1000,
    observed +120 mm BACI). Zero for wells first observed after the Dec-2017
    clearfell (no pre-event baseline to attribute a gain against).
  - HC3 heteroskedasticity-robust SEs specifically (statsmodels
    get_robustcov_results('HC3'), not HC0/HC1) - well counts are small enough
    that the distinction matters.

Windows
-------
  2006_2012 : regressors {coast, c}            - pre-everything, clean coast
                                                  + background.
  2018_2025 : regressors {coast, clearfell, c}  - clearfell isolated (window
                                                  starts the year after the
                                                  Dec-2017 event so no
                                                  pre-clearfell spring
                                                  observation falls inside the
                                                  endpoint groups); coast as
                                                  covariate. Broadleaf is an
                                                  optional covariate here ONLY
                                                  (flagged; reported with and
                                                  without; never headline).
  2005_2025 : regressors {coast, clearfell, c}  - full-record summary /
                                                  robustness.
  2015_2017 : NOT regressed. 3-point scrape window, unidentifiable. Scraping
                                                  is owned by BACI evidence
                                                  (CEH36 +129.5 mm on-site;
                                                  WMC3 -55/-54 mm DiD), not
                                                  this regression.

Independent (falsifiable) test - delta_0(t) trajectory
--------------------------------------------------------
Shape (delta_0, L) is fit from this same well network, so the shape test
above is partly self-confirming (flagged in results.txt). The independent
test is temporal: the coast-only regression re-run on EXPANDING windows
(2005-2010, ->2013, ->2016, ->2019, ->2022, ->2025). For each, implied
delta_0 = s_coast * delta_0_assumed. Flat at ~29 mm/yr supports chronic
linear accumulation; a rising/falling trajectory would not.

Reused unchanged from v2.1.0 / Script 20 v1.32.0
-------------------------------------------------
  - dh_corr,i observed signal (Script 36's endpoint-difference method).
  - Unit field builders via importlib: _erosion_field() [coastal shape],
    felling-polygon clearfell shape (clearfell_step_mm x exp(-d_fell/lambda)),
    _broadleaf_field() [broadleaf covariate].
  - Per-well beta_3 temporal attenuation: ramp 1 - (1-exp(-b3*T))/(b3*T);
    step 1 - exp(-b3*t). Wells with beta_3 <= 0 flagged
    b3_correction_valid = False and excluded from the fit (shown, not used).
  - Named exclusions (EXCL_NAMED) carried forward unchanged from v2.1.0 as a
    documented data-quality convention (not part of the new spec; a
    continuity choice - flag to Martin if a spec-only build is wanted).

Does NOT claim
--------------
Does not resolve scraping (BACI owns it). Does not close the coastal budget
(first-order test). Shape test partly self-confirming; only the delta_0(t)
trajectory is independent. Broadleaf a covariate at most, never a headline
scale factor. C1 Lake wells are EXCLUDED from the fit (ADDENDUM 1 — sluice-
managed lake level; still shown in the CSV/scatter for transparency); C2
(Dune) is the negative control.

Outputs (outputs/37_driver_validation/):
  37_scale_factors_by_window.csv    [NEW] window, s_coast, s_cf, c, HC3 CIs,
                                     R^2, n (+ with/without-broadleaf rows for
                                     2018_2025).
  37_driver_validation_per_well.csv per-well regressors, fitted, residual,
                                     per window (window-suffixed columns).
  37_predicted_vs_observed.png      per-window predicted-vs-observed panels.
  37_residual_map.png               IDW residual map (2005-2025 window,
                                     canonical - largest, most complete well
                                     set).
  37_implied_delta0_trajectory.png  [NEW] expanding-window delta_0(t) test.
  37_results.txt                   scale-factor table, negative-control block
                                     (C2), excluded-sluice block (C1),
                                     self-confirmation caveat.

Observed Differential Change, Envelope, and Validation. Runs after Script 36
in the driver-validation phase; step index in outputs/pipeline_manifest.json.
"""

__version__ = "3.2.0"  # 2026-07-06: ADDENDUM 1 —
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import os
import sys
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import statsmodels.api as sm
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
from utils.config import CLUSTER_LABELS, CLUSTER_MARKERS
from utils.clearfell_common import INTERVENTION_DATE
from utils.map_utils import (
    load_dem_hillshade, add_idw_surface, add_en_axes, add_kml_features,
)
from utils.console_utils import banner, phase, step, info, note, warn, result, saved, done
from utils.render_utils import render_figure

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
DIR_37              = paths.DIR_37
OUT_SCALE_FACTORS   = paths.OUT_37_SCALE_FACTORS     # 37_scale_factors_by_window.csv [NEW]
OUT_PER_WELL        = paths.OUT_37_PER_WELL          # 37_driver_validation_per_well.csv
OUT_SCATTER_FULL    = paths.OUT_37_SCATTER           # 37_predicted_vs_observed.png
OUT_RESIDUAL_MAP    = paths.OUT_37_RESIDUAL_MAP
OUT_DELTA0_TRAJ     = paths.OUT_37_DELTA0_TRAJECTORY # 37_implied_delta0_trajectory.png [NEW]
OUT_RESULTS         = paths.OUT_37_RESULTS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_ID      = "37"
DAYS_PER_MONTH = 30.4375

# Regression windows and the regressors each uses. Date bounds mirror
# config.ACT_PERIODS; T_years is used only for the results-table label.
WINDOWS: dict[str, tuple[pd.Timestamp, pd.Timestamp, float]] = {
    "2006_2012": (pd.Timestamp("2006-01-01"), pd.Timestamp("2012-12-01"), 7.0),
    "2018_2025": (pd.Timestamp("2018-01-01"), pd.Timestamp("2025-12-01"), 8.0),
    "2005_2025": (pd.Timestamp("2005-01-01"), pd.Timestamp("2025-12-01"), 20.0),
}
REGRESSORS_BY_WINDOW: dict[str, tuple[str, ...]] = {
    "2006_2012": ("coast_i",),
    "2018_2025": ("coast_i", "clearfell_i"),
    "2005_2025": ("coast_i", "clearfell_i"),
}
DH_CORR_COLS = {w: f"dh_corr_mm_{w}" for w in WINDOWS}
REQUIRED_COLS = list(DH_CORR_COLS.values())

# Expanding windows for the independent delta_0(t) trajectory test
# (config.ACT_PERIODS; Script 36 v1.2.0+). Coast-only regression re-run on
# each; implied delta_0 = s_coast x delta_0_assumed, plotted vs window end.
TRAJECTORY_WINDOWS   = ["2005_2010", "2005_2013", "2005_2016",
                        "2005_2019", "2005_2022", "2005_2025"]
TRAJECTORY_END_YEARS = [2010, 2013, 2016, 2019, 2022, 2025]
TRAJECTORY_STARTS    = {w: (pd.Timestamp("2005-01-01"),
                            pd.Timestamp(f"{y}-12-01"), float(y - 2005))
                        for w, y in zip(TRAJECTORY_WINDOWS, TRAJECTORY_END_YEARS)}

# ACT_BHAT_WINDOW / ACT_ENDPOINT_FRACTION (Script 36's endpoint-group
# construction) - reused here ONLY to reconstruct the same endpoint-group
# YEARS per well/window for dt_mid. b_hat / h_corr themselves are NOT refit.
BHAT_WINDOW       = config.ACT_BHAT_WINDOW
ENDPOINT_FRACTION = config.ACT_ENDPOINT_FRACTION

# Named exclusions carried forward unchanged from v2.1.0: shown in scatter/
# CSV but excluded from the regression fit. Continuity convention, not part
# of the new spec.
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

BROADLEAF_VARIANT_LABEL = "with_broadleaf_covariate"
PRIMARY_VARIANT_LABEL   = "primary"


def _cluster_id_from_label(label: str) -> int | None:
    """Resolve a 'C1'/'C2'-style label to its numeric cluster id via
    config.CLUSTER_LABELS (e.g. {1: "C1 (Lake Edge)", ...}) — never a
    hardcoded id. Returns None if no match."""
    for cid, full_label in CLUSTER_LABELS.items():
        if str(full_label).strip().upper().startswith(label.strip().upper()):
            return int(cid)
    return None


# ADDENDUM 1 (2026-07-06, v3.1.0): negative control C1 → C2; C1 (sluice-
# controlled lake level) excluded from the fit. Resolved from config via
# CLUSTER_LABELS — never a literal well list.
NEG_CONTROL_CLUSTER_ID  = _cluster_id_from_label(config.ACT_NEG_CONTROL_CLUSTER)
FIT_EXCLUDE_CLUSTER_IDS = {
    cid for lbl in config.ACT_FIT_EXCLUDE_CLUSTERS
    if (cid := _cluster_id_from_label(lbl)) is not None
}
FIT_EXCLUDE_REASON = config.ACT_FIT_EXCLUDE_REASON

# ---------------------------------------------------------------------------
# Script 20 / Script 36 imports (numeric filenames)
# ---------------------------------------------------------------------------

def _load_s20():
    """Load Script 20 spatial figures module via importlib (numeric filename)."""
    path = Path(__file__).parent / "20_spatial_figures.py"
    spec = importlib.util.spec_from_file_location("_s20_spatial", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_s36():
    """Load Script 36 module via importlib. Used ONLY for its yr/cwb table
    loaders, to reconstruct the same endpoint-group YEARS Script 36 used when
    computing dh_corr — never to refit b_hat or h_corr."""
    path = Path(__file__).parent / "36_absolute_climate_trend.py"
    spec = importlib.util.spec_from_file_location("_s36_climate_trend", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Live-value loaders (no hardcoded values)
# ---------------------------------------------------------------------------

def _load_coastal_fit() -> tuple[float, float]:
    """δ₀ (mm/yr, positive magnitude) and L (m) — Script 25 forest-free
    linear-capped row."""
    snapshot = (29.03, 894.0)
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
# β₃ temporal correction factors (unchanged from v2.1.0)
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
# Endpoint-group centroid years (NEW — mirrors Script 36's construction
# exactly, to build dt_mid; does NOT refit b_hat or h_corr)
# ---------------------------------------------------------------------------

def _endpoint_group_centroids(h: pd.Series, cwb: pd.Series,
                              first: int, last: int,
                              endpoint_fraction: float = ENDPOINT_FRACTION
                              ):
    """Mirror Script 36's climate_corrected_endpoint_diff() non-overlapping
    endpoint-group construction EXACTLY (same n, k, and overlap fallback),
    returning (first_group_centroid_yr, last_group_centroid_yr) instead of the
    endpoint-mean difference. Used only to build dt_mid for the coastal
    regressor's amplitude — b_hat and h_corr themselves are read from Script
    36's committed CSV, never refit here."""
    hh = h.dropna()
    hh = hh[(hh.index >= first) & (hh.index <= last)]
    common = hh.index.intersection(cwb.dropna().index)
    if len(common) < 2:
        return None, None
    common = common.sort_values()
    n = len(common)
    k = max(1, int(round(n * endpoint_fraction)))
    if 2 * k > n:
        k = n // 2
    if k < 1:
        return None, None
    first_yrs = common[:k].values.astype(float)
    last_yrs  = common[-k:].values.astype(float)
    return float(np.mean(first_yrs)), float(np.mean(last_yrs))


def build_dt_mid_lut(s36, keys, first: int, last: int) -> dict:
    """{key: dt_mid (years)} for every well in `keys`, for window [first,last].
    dt_mid = last_group_centroid_yr − first_group_centroid_yr, built on the
    SAME yr/cwb tables Script 36 used (its own load_inputs/spring_year_table/
    spring_cwb_series loaders — reused unchanged, called via importlib)."""
    levels, loc, master, climate = s36.load_inputs()
    yr  = s36.spring_year_table(levels)
    cwb = s36.spring_cwb_series(climate)
    out = {}
    cols_lower = {c.lower().strip(): c for c in yr.columns}
    for key in keys:
        col = cols_lower.get(key)
        if col is None:
            out[key] = np.nan
            continue
        c0, c1 = _endpoint_group_centroids(yr[col], cwb, first, last)
        out[key] = (c1 - c0) if (c0 is not None and c1 is not None) else np.nan
    return out


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_script36_wells() -> pd.DataFrame:
    """Load Script 36 per-well CSV; fail-fast if any required dh_corr column
    is absent (rerun Script 36 v1.2.0+ with the Part-A windows in
    config.ACT_PERIODS)."""
    df = pd.read_csv(OUT_36_PER_WELL)
    df["key"] = df["key"].str.strip().str.lower()
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise KeyError(
            f"Script 36 CSV is missing required column(s): {missing}.\n"
            "Rerun Script 36 v1.2.0+ with the Part-A windows "
            "(2006_2012, 2018_2025, 2005_2025) in config.ACT_PERIODS, "
            "then rerun Script 37."
        )
    missing_traj = [f"dh_corr_mm_{w}" for w in TRAJECTORY_WINDOWS
                    if f"dh_corr_mm_{w}" not in df.columns]
    if missing_traj:
        warn(f"trajectory windows missing from Script 36 CSV: {missing_traj} — "
             "δ₀(t) trajectory test will be incomplete")

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

    df["col"] = df["col"].fillna(df["key"])
    return df


def load_master_b3(well_keys: list) -> dict:
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


def load_well_spans(well_keys: list,
                    win_start: pd.Timestamp,
                    win_end: pd.Timestamp) -> dict:
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


def load_first_obs_dates(well_keys: list) -> dict:
    """Return {key: first valid observation date} from INT_WELLS_CLEAN. Used
    to zero the clearfell regressor for wells with no pre-clearfell baseline."""
    levels = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    levels.columns = [c.strip().lower() for c in levels.columns]
    out = {}
    for key in well_keys:
        if key not in levels.columns:
            out[key] = pd.NaT
            continue
        ser = levels[key].dropna()
        out[key] = ser.index.min() if not ser.empty else pd.NaT
    return out


# ---------------------------------------------------------------------------
# Spatial factors (reused from Script 20 field builders)
# ---------------------------------------------------------------------------

def _build_spatial(s20, E: np.ndarray, N: np.ndarray,
                   clearfell_step_mm: float) -> dict:
    """
    Build equilibrium spatial fields at well locations.

    Returns dict with keys:
        coast_unit  — max(1−d/L, 0) [dimensionless shape, 0..1]
        clearfell   — clearfell_step_mm × exp(−d_fell/λ) [mm, positive gain]
        broadleaf   — full 2005→2025 broadleaf increment [mm, positive loss
                      magnitude — negated when used as a regressor]
        fLam        — forest λ (m)
    """
    gx = np.asarray(E, dtype=float)
    gy = np.asarray(N, dtype=float)
    n  = len(gx)
    zeros = np.zeros(n)

    coast_res  = s20._erosion_field(gx, gy, h0_mm=1.0)
    coast_unit = np.nan_to_num(coast_res[0], nan=0.0) if coast_res[0] is not None else zeros.copy()

    for_result = s20._forest_field(gx, gy)
    fLam = float(for_result[2]) if (for_result[2] is not None) else None

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

    bl_res    = s20._broadleaf_field(gx, gy)
    broadleaf = np.nan_to_num(bl_res[0], nan=0.0) if bl_res[0] is not None else zeros.copy()

    lam_txt = f"{fLam:.0f} m" if fLam else "None"
    info(f"  coast_unit: {coast_unit.min():.3f}–{coast_unit.max():.3f}"
         f"  clearfell: {clearfell.min():.0f}–{clearfell.max():.0f} mm"
         f"  fLam={lam_txt}")

    return dict(coast_unit=coast_unit, clearfell=clearfell,
                broadleaf=broadleaf, fLam=fLam)


# ---------------------------------------------------------------------------
# Per-window regressor construction
# ---------------------------------------------------------------------------

def build_window_frame(df36: pd.DataFrame, window: str,
                       b3_lut: dict, spatial: dict,
                       delta0: float, clearfell_step_mm: float,
                       first_obs: dict, dt_mid_lut: dict) -> pd.DataFrame:
    """Build the per-well regressor frame for one window: dh_corr, coast_i,
    clearfell_i (if used), broadleaf_i (2018_2025 only, covariate), plus
    b3_correction_valid / exclude_named flags. Sign convention: coast_i is
    NEGATIVE (drying), clearfell_i POSITIVE (wetting), broadleaf_i NEGATIVE
    (drying) — matching dh_corr's sign (positive = climate-corrected rise)."""
    win_start, win_end, T_yr = WINDOWS[window]
    dh_col = DH_CORR_COLS[window]
    regressors = REGRESSORS_BY_WINDOW[window]

    mask = df36[dh_col].notna()
    sub  = df36[mask].copy()
    keys = list(sub["key"])
    spans = load_well_spans(keys, win_start, win_end)

    rows = []
    for _, row in sub.iterrows():
        key = row["key"]
        idx = list(df36["key"]).index(key)

        T_m = spans.get(key, np.nan)
        if np.isnan(T_m):
            T_m = (win_end - win_start).days / DAYS_PER_MONTH
        b3  = b3_lut.get(key, np.nan)
        b3v = (not np.isnan(b3)) and (b3 > 0.0)
        b3e = b3 if b3v else 0.0

        dt_mid = dt_mid_lut.get(key, np.nan)

        # --- Coastal regressor: -delta0 * dt_mid * shape * ramp_factor ------
        coast_i = np.nan
        if "coast_i" in regressors and not np.isnan(dt_mid):
            cu = float(spatial["coast_unit"][idx])
            coast_i = -1.0 * delta0 * dt_mid * cu * _ramp_factor(b3e, T_m)

        # --- Clearfell regressor: +clearfell_step*exp(-d/lam)*step_factor ---
        clearfell_i = np.nan
        if "clearfell_i" in regressors:
            fobs = first_obs.get(key, pd.NaT)
            if pd.isna(fobs) or fobs > INTERVENTION_DATE:
                clearfell_i = 0.0  # no pre-clearfell baseline to attribute a gain against
            else:
                cf   = float(spatial["clearfell"][idx])
                t_cf = max(0.0, (win_end - INTERVENTION_DATE).days / DAYS_PER_MONTH)
                clearfell_i = cf * _step_factor(b3e, t_cf)

        # --- Broadleaf covariate (2018_2025 only): -H0_incr*ramp_factor -----
        broadleaf_i = np.nan
        if window == "2018_2025":
            bl = float(spatial["broadleaf"][idx])
            broadleaf_i = -1.0 * bl * _ramp_factor(b3e, T_m)

        cluster_val = row["Cluster"] if not pd.isna(row["Cluster"]) else np.nan
        excl_reason = EXCL_NAMED.get(key, "")
        if (not excl_reason) and (not pd.isna(cluster_val)) and (int(cluster_val) in FIT_EXCLUDE_CLUSTER_IDS):
            excl_reason = FIT_EXCLUDE_REASON
        rows.append(dict(
            key=key, col=row.get("col", key),
            Cluster=cluster_val,
            E=float(row["E"]), N=float(row["N"]),
            T_months=round(T_m, 1),
            dt_mid_yr=round(dt_mid, 2) if not np.isnan(dt_mid) else np.nan,
            b3_drainage=b3, b3_correction_valid=b3v,
            exclude_named=bool(excl_reason), exclude_reason=excl_reason,
            coast_i=coast_i, clearfell_i=clearfell_i, broadleaf_i=broadleaf_i,
            dh_corr=float(row[dh_col]),
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# HC3 scale-factor regression
# ---------------------------------------------------------------------------

def fit_scale_regression(frame: pd.DataFrame, regressor_cols: list,
                         y_col: str = "dh_corr") -> dict:
    """OLS of y_col on regressor_cols + free intercept, HC3-robust SEs/CIs.

    `frame` must already be restricted to in-fit wells (b3_correction_valid
    and not exclude_named). Returns dict with params (Series incl. 'const'),
    ci (DataFrame lo/hi), rsquared, nobs, fittedvalues/resid indexed like
    `frame`.
    """
    X = frame[list(regressor_cols)].astype(float)
    X = sm.add_constant(X, has_constant="add")
    y = frame[y_col].astype(float)
    ols  = sm.OLS(y, X, missing="drop").fit()
    rob  = ols.get_robustcov_results(cov_type="HC3")
    ci   = pd.DataFrame(rob.conf_int(alpha=0.05), index=X.columns, columns=["lo", "hi"])
    return dict(
        params=pd.Series(rob.params, index=X.columns),
        bse=pd.Series(rob.bse, index=X.columns),
        ci=ci,
        rsquared=float(rob.rsquared),
        nobs=int(rob.nobs),
        fittedvalues=pd.Series(np.asarray(rob.fittedvalues), index=frame.index),
        resid=pd.Series(np.asarray(rob.resid), index=frame.index),
    )


def run_window(df36: pd.DataFrame, window: str,
              b3_lut: dict, spatial: dict,
              delta0: float, clearfell_step_mm: float,
              first_obs: dict, dt_mid_lut: dict) -> dict:
    """Build the regressor frame for `window`, fit the HC3 scale-factor
    regression on in-fit wells, apply fitted coefficients to ALL wells
    (including beta_3-invalid / named-excluded, for full transparency in the
    scatter/CSV), and return everything needed downstream."""
    regressors = list(REGRESSORS_BY_WINDOW[window])
    frame = build_window_frame(df36, window, b3_lut, spatial, delta0,
                               clearfell_step_mm, first_obs, dt_mid_lut)
    info(f"{window}: {len(frame)} wells with dh_corr coverage")

    in_fit = frame[frame["b3_correction_valid"] & ~frame["exclude_named"]].copy()
    n_excl_b3   = int((~frame["b3_correction_valid"]).sum())
    n_excl_name = int(frame["exclude_named"].sum())
    if n_excl_b3 or n_excl_name:
        note(f"{window}: excluded from fit — {n_excl_b3} β₃≤0, "
             f"{n_excl_name} named ({len(in_fit)} remain)")

    fit = fit_scale_regression(in_fit, regressors)
    result(f"{window} s_coast", f"{fit['params'].get('coast_i', float('nan')):.3f}")
    if "clearfell_i" in fit["params"].index:
        result(f"{window} s_cf", f"{fit['params']['clearfell_i']:.3f}")
    result(f"{window} c (intercept, mm)", f"{fit['params']['const']:.1f}")
    result(f"{window} R² (n={fit['nobs']})", f"{fit['rsquared']:.3f}")

    # Apply fitted coefficients to ALL wells (predicted col = regression
    # fitted value, per spec's Outputs section).
    X_all = sm.add_constant(frame[regressors].astype(float), has_constant="add")
    coef  = fit["params"].reindex(X_all.columns).values
    frame["fitted"]   = X_all.values @ coef
    frame["residual"] = frame["fitted"] - frame["dh_corr"]
    in_fit = frame.loc[in_fit.index]  # refresh: pick up fitted/residual added above

    return dict(window=window, regressors=regressors, frame=frame,
                in_fit=in_fit, fit=fit)


def run_broadleaf_variant(df36: pd.DataFrame, window: str,
                          b3_lut: dict, spatial: dict,
                          delta0: float, clearfell_step_mm: float,
                          first_obs: dict, dt_mid_lut: dict) -> dict:
    """Robustness variant: {coast, clearfell, broadleaf} + intercept, for the
    2018_2025 window ONLY. Flagged, reported alongside the primary — never a
    headline scale factor."""
    frame = build_window_frame(df36, window, b3_lut, spatial, delta0,
                               clearfell_step_mm, first_obs, dt_mid_lut)
    in_fit = frame[frame["b3_correction_valid"] & ~frame["exclude_named"]].copy()
    regressors = ["coast_i", "clearfell_i", "broadleaf_i"]
    fit = fit_scale_regression(in_fit, regressors)
    note(f"{window} WITH broadleaf covariate (robustness, NOT headline): "
         f"s_coast={fit['params']['coast_i']:.3f}  "
         f"s_cf={fit['params']['clearfell_i']:.3f}  "
         f"s_bl={fit['params']['broadleaf_i']:.3f}  R²={fit['rsquared']:.3f}")
    return dict(window=window, regressors=regressors, frame=frame,
                in_fit=in_fit, fit=fit)


# ---------------------------------------------------------------------------
# Independent test: implied δ₀(t) expanding-window trajectory
# ---------------------------------------------------------------------------

def run_delta0_trajectory(df36: pd.DataFrame, b3_lut: dict,
                          spatial: dict, delta0: float,
                          s36) -> pd.DataFrame:
    """Coast-only regression re-run on expanding windows 2005→{2010..2025}.
    Implied δ₀(window) = s_coast × δ₀_assumed. Returns a tidy DataFrame for
    plotting and results.txt; skips windows whose dh_corr column is absent
    from the Script 36 CSV."""
    rows = []
    for w, end_yr in zip(TRAJECTORY_WINDOWS, TRAJECTORY_END_YEARS):
        dh_col = f"dh_corr_mm_{w}"
        if dh_col not in df36.columns:
            continue
        win_start, win_end, _ = TRAJECTORY_STARTS[w]
        mask = df36[dh_col].notna()
        sub  = df36[mask].copy()
        keys = list(sub["key"])
        dt_mid_lut_w = build_dt_mid_lut(s36, keys, 2005, end_yr)
        spans = load_well_spans(keys, win_start, win_end)

        recs = []
        for _, row in sub.iterrows():
            key = row["key"]
            if key in EXCL_NAMED:
                continue
            cluster_val = row["Cluster"] if not pd.isna(row["Cluster"]) else np.nan
            if (not pd.isna(cluster_val)) and (int(cluster_val) in FIT_EXCLUDE_CLUSTER_IDS):
                continue  # sluice-controlled (ADDENDUM 1) — excluded from all fits
            b3  = b3_lut.get(key, np.nan)
            b3v = (not np.isnan(b3)) and (b3 > 0.0)
            if not b3v:
                continue
            idx = list(df36["key"]).index(key)
            T_m = spans.get(key, np.nan)
            if np.isnan(T_m):
                T_m = (win_end - win_start).days / DAYS_PER_MONTH
            dt_mid = dt_mid_lut_w.get(key, np.nan)
            if np.isnan(dt_mid):
                continue
            cu = float(spatial["coast_unit"][idx])
            coast_i = -1.0 * delta0 * dt_mid * cu * _ramp_factor(b3, T_m)
            recs.append(dict(key=key, coast_i=coast_i, dh_corr=float(row[dh_col])))

        wdf = pd.DataFrame(recs)
        if len(wdf) < 4:
            note(f"δ₀(t) trajectory: {w} has only {len(wdf)} wells — skipped")
            continue
        fit = fit_scale_regression(wdf, ["coast_i"])
        s_coast   = float(fit["params"]["coast_i"])
        ci_lo, ci_hi = fit["ci"].loc["coast_i", "lo"], fit["ci"].loc["coast_i", "hi"]
        rows.append(dict(
            window=w, window_end_year=end_yr, n=fit["nobs"],
            s_coast=s_coast,
            implied_delta0_mm_yr=s_coast * delta0,
            ci_lo_implied_delta0=ci_lo * delta0,
            ci_hi_implied_delta0=ci_hi * delta0,
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Scale-factor table
# ---------------------------------------------------------------------------

def build_scale_factor_table(results: dict, broadleaf_result) -> pd.DataFrame:
    rows = []
    for window, res in results.items():
        fit = res["fit"]
        p, ci = fit["params"], fit["ci"]
        rows.append(dict(
            window=window, variant=PRIMARY_VARIANT_LABEL,
            s_coast=round(float(p.get("coast_i", np.nan)), 4),
            s_coast_ci_lo=round(float(ci.loc["coast_i", "lo"]), 4) if "coast_i" in ci.index else np.nan,
            s_coast_ci_hi=round(float(ci.loc["coast_i", "hi"]), 4) if "coast_i" in ci.index else np.nan,
            s_cf=round(float(p.get("clearfell_i", np.nan)), 4) if "clearfell_i" in p.index else np.nan,
            s_cf_ci_lo=round(float(ci.loc["clearfell_i", "lo"]), 4) if "clearfell_i" in ci.index else np.nan,
            s_cf_ci_hi=round(float(ci.loc["clearfell_i", "hi"]), 4) if "clearfell_i" in ci.index else np.nan,
            c=round(float(p["const"]), 1),
            c_ci_lo=round(float(ci.loc["const", "lo"]), 1),
            c_ci_hi=round(float(ci.loc["const", "hi"]), 1),
            r_squared=round(fit["rsquared"], 3),
            n=fit["nobs"],
        ))
    if broadleaf_result is not None:
        fit = broadleaf_result["fit"]
        p, ci = fit["params"], fit["ci"]
        rows.append(dict(
            window=broadleaf_result["window"], variant=BROADLEAF_VARIANT_LABEL,
            s_coast=round(float(p["coast_i"]), 4),
            s_coast_ci_lo=round(float(ci.loc["coast_i", "lo"]), 4),
            s_coast_ci_hi=round(float(ci.loc["coast_i", "hi"]), 4),
            s_cf=round(float(p["clearfell_i"]), 4),
            s_cf_ci_lo=round(float(ci.loc["clearfell_i", "lo"]), 4),
            s_cf_ci_hi=round(float(ci.loc["clearfell_i", "hi"]), 4),
            c=round(float(p["const"]), 1),
            c_ci_lo=round(float(ci.loc["const", "lo"]), 1),
            c_ci_hi=round(float(ci.loc["const", "hi"]), 1),
            r_squared=round(fit["rsquared"], 3),
            n=fit["nobs"],
        ))
        rows[-1]["s_bl"] = round(float(p["broadleaf_i"]), 4)
        rows[-1]["s_bl_ci_lo"] = round(float(ci.loc["broadleaf_i", "lo"]), 4)
        rows[-1]["s_bl_ci_hi"] = round(float(ci.loc["broadleaf_i", "hi"]), 4)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Negative-control block (ADDENDUM 1, 2026-07-06: C1 → C2) and the
# excluded-from-fit sluice block (former C1), reported separately for
# transparency.
# ---------------------------------------------------------------------------

def neg_control_block(results: dict) -> pd.DataFrame:
    """Negative-control cluster (config.ACT_NEG_CONTROL_CLUSTER = C2): driver-
    free wells, reported per window as a check that the climate correction is
    unbiased (near-zero mean residual expected) — framed as 'consistent with',
    never 'confirms'."""
    rows = []
    for window, res in results.items():
        frame = res["frame"]
        ctrl = frame[frame["Cluster"] == NEG_CONTROL_CLUSTER_ID]
        if ctrl.empty:
            continue
        rows.append(dict(
            window=window, n=len(ctrl),
            mean_coast_i=round(float(ctrl["coast_i"].mean()), 1)
                if ctrl["coast_i"].notna().any() else np.nan,
            mean_clearfell_i=round(float(ctrl["clearfell_i"].mean()), 1)
                if ctrl["clearfell_i"].notna().any() else np.nan,
            mean_dh_corr=round(float(ctrl["dh_corr"].mean()), 1),
            mean_residual=round(float(ctrl["residual"].mean()), 1),
        ))
    return pd.DataFrame(rows)


def excluded_sluice_block(results: dict) -> pd.DataFrame:
    """Former control cluster (C1, Lake Edge) — EXCLUDED from the fit
    (ADDENDUM 1: sluice-managed lake level), reported here for transparency
    only. `residual` is fitted-from-the-C1-excluded-model minus observed, so
    it still shows how far the management-held lake sits from the natural
    background."""
    rows = []
    for window, res in results.items():
        frame = res["frame"]
        excl = frame[frame["Cluster"].isin(FIT_EXCLUDE_CLUSTER_IDS)]
        if excl.empty:
            continue
        rows.append(dict(
            window=window, n=len(excl),
            mean_coast_i=round(float(excl["coast_i"].mean()), 1)
                if excl["coast_i"].notna().any() else np.nan,
            mean_clearfell_i=round(float(excl["clearfell_i"].mean()), 1)
                if excl["clearfell_i"].notna().any() else np.nan,
            mean_dh_corr=round(float(excl["dh_corr"].mean()), 1),
            mean_residual=round(float(excl["residual"].mean()), 1),
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_scale_scatters(results: dict, dpi: int = 150) -> None:
    """Per-window predicted-vs-observed panels in one figure."""
    colours = config.get_cluster_colours()
    n_panels = len(results)
    with plt.rc_context(MPL_RC):
        fig, axes = plt.subplots(1, n_panels, figsize=(6.2 * n_panels, 6.0))
        if n_panels == 1:
            axes = [axes]
        for ax, (window, res) in zip(axes, results.items()):
            frame  = res["frame"]
            in_fit = res["in_fit"]
            fit    = res["fit"]

            all_vals = pd.concat([frame["fitted"], frame["dh_corr"]]).dropna()
            lim = max(float(all_vals.abs().max()) * 1.15, 50.0) if not all_vals.empty else 100.0

            ax.plot([-lim, lim], [-lim, lim], color="#999999", lw=0.9, ls="--", zorder=1)
            ax.axhline(0, color="#cccccc", lw=0.6, zorder=0)
            ax.axvline(0, color="#cccccc", lw=0.6, zorder=0)

            plotted = frame[frame["b3_correction_valid"] & ~frame["exclude_named"]]
            for cid in sorted(plotted["Cluster"].dropna().unique()):
                sub_c = plotted[plotted["Cluster"] == cid]
                col = colours.get(int(cid), "#444444")
                mrk = CLUSTER_MARKERS.get(int(cid), "o")
                ax.scatter(sub_c["fitted"], sub_c["dh_corr"],
                           c=col, marker=mrk, edgecolor="k", lw=0.6, s=55, zorder=4,
                           label=CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))

            b3_flag = frame[~frame["b3_correction_valid"]]
            if not b3_flag.empty:
                ax.scatter(b3_flag["fitted"], b3_flag["dh_corr"],
                           facecolor="none", edgecolor="#888888", lw=1.3,
                           marker="^", s=55, zorder=4, label="β₃ ≤ 0 (excluded)")

            excl = frame[frame["exclude_named"]]
            if not excl.empty:
                ax.scatter(excl["fitted"], excl["dh_corr"],
                           facecolor="none", edgecolor="#cc0000", lw=1.3,
                           marker="s", s=70, zorder=4, label="named exclusion")

            r_val = rmse = np.nan
            if len(in_fit) >= 3:
                r_val, _ = pearsonr(in_fit["fitted"], in_fit["dh_corr"])
                rmse = float(np.sqrt(np.mean(in_fit["residual"] ** 2)))
                s_coast_txt = f"s_coast={fit['params'].get('coast_i', np.nan):.2f}"
                s_cf_txt = (f"  s_cf={fit['params']['clearfell_i']:.2f}"
                            if "clearfell_i" in fit["params"].index else "")
                stat_txt = (f"r = {r_val:.2f}  n = {len(in_fit)}\n"
                            f"RMSE = {rmse:.0f} mm  R² = {fit['rsquared']:.2f}\n"
                            f"{s_coast_txt}{s_cf_txt}  c={fit['params']['const']:.0f} mm")
                ax.text(0.05, 0.95, stat_txt, transform=ax.transAxes,
                        fontsize=8, va="top",
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#aaa", alpha=0.9))

            ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
            ax.set_aspect("equal")
            ax.set_xlabel(f"Fitted Δh {window.replace('_', '–')} (mm)", fontsize=9)
            ax.set_ylabel("Observed Δh_corr (mm, Script 36)", fontsize=9)
            ax.set_title(f"{window.replace('_', '–')}  [{', '.join(res['regressors'])}]",
                        fontsize=9.5, pad=6)
            ax.legend(fontsize=6.5, loc="lower right", framealpha=0.9)
        fig.suptitle(f"Per-driver scale-factor regression v{__version__} — "
                     "predicted vs observed, by window", fontsize=11)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        render_figure(fig, OUT_SCATTER_FULL)
        plt.close(fig)
    saved(OUT_SCATTER_FULL)


def plot_residual_map(frame: pd.DataFrame, window: str, dpi: int = 150) -> None:
    """IDW residual map (model − observed) for the canonical window
    (2005–2025 — largest, most complete well set)."""
    df_map = frame.dropna(subset=["E", "N", "residual"]).copy()
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
        for cid in sorted(frame["Cluster"].dropna().unique()):
            sub = frame[frame["Cluster"] == cid]
            col = colours.get(int(cid), "#444444")
            mrk = CLUSTER_MARKERS.get(int(cid), "o")
            ax.scatter(sub["E"], sub["N"], c=col, marker=mrk,
                       edgecolor="k", lw=0.6, s=55, zorder=5,
                       label=CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))

        sm_map = plt.cm.ScalarMappable(cmap=plt.cm.RdBu, norm=norm)
        sm_map.set_array([])
        cbar = fig.colorbar(sm_map, ax=ax, fraction=0.028, pad=0.04)
        cbar.set_label(f"Residual (mm): fitted − observed  ({window.replace('_', '–')})", fontsize=9)
        ax.set_title(
            f"Scale-factor regression — residual map ({window.replace('_', '–')}, canonical)\n"
            "Blue = model over-predicts wetting; Red = model over-predicts drying",
            fontsize=10, pad=8)
        ax.legend(fontsize=8, loc="lower left", framealpha=0.9, title="cluster")
        fig.tight_layout()
        render_figure(fig, OUT_RESIDUAL_MAP)
        plt.close(fig)
    saved(OUT_RESIDUAL_MAP)


def plot_delta0_trajectory(traj: pd.DataFrame, delta0: float, dpi: int = 150) -> None:
    with plt.rc_context(MPL_RC):
        fig, ax = plt.subplots(figsize=(8, 5.5))
        if traj.empty:
            ax.text(0.5, 0.5, "insufficient data for δ₀(t) trajectory",
                    ha="center", va="center", transform=ax.transAxes)
        else:
            ax.axhline(delta0, color="#999999", lw=1.0, ls="--",
                      label=f"assumed δ₀ = {delta0:.1f} mm/yr")
            ax.errorbar(traj["window_end_year"], traj["implied_delta0_mm_yr"],
                       yerr=[traj["implied_delta0_mm_yr"] - traj["ci_lo_implied_delta0"],
                             traj["ci_hi_implied_delta0"] - traj["implied_delta0_mm_yr"]],
                       fmt="o-", color="#1a5276", capsize=4, lw=1.4, ms=6, zorder=3)
            at_risk = traj[traj["window_end_year"] >= 2019]
            if not at_risk.empty:
                ax.scatter(at_risk["window_end_year"], at_risk["implied_delta0_mm_yr"],
                          facecolor="none", edgecolor="#cc6600", lw=1.8, s=140,
                          zorder=4, label="post-2017 window (clearfell unmodelled — upper bound)")
            for _, r in traj.iterrows():
                ax.annotate(f"n={r['n']:.0f}", xy=(r["window_end_year"], r["implied_delta0_mm_yr"]),
                          xytext=(0, 8), textcoords="offset points",
                          fontsize=7.5, ha="center", color="#444444")
            ax.legend(fontsize=8.5, loc="best")
        ax.set_xlabel("Window end year (2005 → end year)", fontsize=10)
        ax.set_ylabel("Implied δ₀ = s_coast × δ₀_assumed (mm/yr)", fontsize=10)
        ax.set_title("Independent test: implied δ₀(t) on expanding windows\n"
                    "Flat ≈ 29 mm/yr supports chronic-linear coastal drying; "
                    "shape (δ₀, L) itself is fit from this well network (partly self-confirming)",
                    fontsize=9.5, pad=8)
        fig.tight_layout()
        render_figure(fig, OUT_DELTA0_TRAJ)
        plt.close(fig)
    saved(OUT_DELTA0_TRAJ)


# ---------------------------------------------------------------------------
# Per-well consolidated CSV
# ---------------------------------------------------------------------------

def write_per_well_csv(results: dict) -> pd.DataFrame:
    base = None
    for window, res in results.items():
        frame = res["frame"].copy()
        keep = ["key", "col", "Cluster", "E", "N", "coast_i", "clearfell_i",
                "broadleaf_i", "dh_corr", "fitted", "residual",
                "b3_correction_valid", "exclude_named", "exclude_reason",
                "T_months", "dt_mid_yr"]
        keep = [c for c in keep if c in frame.columns]
        ren = {c: f"{c}_{window}" for c in keep
               if c not in ("key", "col", "Cluster", "E", "N")}
        sub = frame[keep].rename(columns=ren)
        base = sub if base is None else base.merge(sub, on=["key", "col", "Cluster", "E", "N"], how="outer")
    base.to_csv(OUT_PER_WELL, index=False)
    saved(OUT_PER_WELL)
    return base


# ---------------------------------------------------------------------------
# Results text
# ---------------------------------------------------------------------------

def write_results(scale_table: pd.DataFrame, ctrl_block: pd.DataFrame,
                  excl_block: pd.DataFrame,
                  traj: pd.DataFrame, delta0: float, clearfell_step_mm: float
                  ) -> None:
    lines = [
        f"37_driver_validation v{__version__} — Per-Driver Scale-Factor Regression",
        "=" * 70,
        "",
        "LIVE PARAMETERS",
        "-" * 70,
        f"  δ₀ (Script 25, forest-free linear-capped): {delta0:.2f} mm/yr",
        f"  clearfell step (10a ANCOVA, Path B, observed BACI): {clearfell_step_mm:.1f} mm",
        "",
        "SCALE-FACTOR TABLE (HC3 robust SEs, 95% CI)",
        "-" * 70,
    ]
    for _, row in scale_table.iterrows():
        lines.append(f"  window={row['window']:12s} variant={row['variant']:22s} n={row['n']}")
        lines.append(f"    s_coast = {row['s_coast']:7.3f}  95%CI [{row['s_coast_ci_lo']:.3f}, {row['s_coast_ci_hi']:.3f}]")
        if not pd.isna(row.get("s_cf", np.nan)):
            lines.append(f"    s_cf    = {row['s_cf']:7.3f}  95%CI [{row['s_cf_ci_lo']:.3f}, {row['s_cf_ci_hi']:.3f}]")
        if "s_bl" in row.index and not pd.isna(row.get("s_bl", np.nan)):
            lines.append(f"    s_bl    = {row['s_bl']:7.3f}  95%CI [{row['s_bl_ci_lo']:.3f}, {row['s_bl_ci_hi']:.3f}]  (robustness only — NOT headline)")
        lines.append(f"    c       = {row['c']:7.1f} mm  95%CI [{row['c_ci_lo']:.1f}, {row['c_ci_hi']:.1f}]")
        lines.append(f"    R²      = {row['r_squared']:.3f}")
        lines.append("")

    ctrl_label = CLUSTER_LABELS.get(NEG_CONTROL_CLUSTER_ID, config.ACT_NEG_CONTROL_CLUSTER)
    lines += [f"NEGATIVE CONTROL — {ctrl_label} (included in fit, ADDENDUM 1 2026-07-06)",
              "-" * 70]
    if ctrl_block.empty:
        lines.append(f"  no {ctrl_label} wells with dh_corr coverage in any window")
    else:
        for _, row in ctrl_block.iterrows():
            cf_txt = f"{row['mean_clearfell_i']:+.1f}" if not pd.isna(row['mean_clearfell_i']) else "n/a (no clearfell regressor this window)"
            lines.append(
                f"  {row['window']:12s} n={row['n']}  "
                f"mean coast_i={row['mean_coast_i']:+.1f}  "
                f"mean clearfell_i={cf_txt}  "
                f"mean dh_corr={row['mean_dh_corr']:+.1f}  "
                f"mean residual={row['mean_residual']:+.1f}"
            )
    lines.append(
        f"  {ctrl_label} wells feel no coastal or clearfell field (all covered "
        "wells carry a modelled amplitude below 5 mm) — a near-zero mean "
        "residual here is CONSISTENT WITH an unbiased climate correction on "
        "driver-free wells (not 'confirms'; see ADDENDUM 1 for the n=6 caveat)."
    )

    lines += ["", "EXCLUDED FROM FIT — sluice (C1, Lake Edge; ADDENDUM 1)", "-" * 70]
    lines.append(f"  reason: {FIT_EXCLUDE_REASON}")
    if excl_block.empty:
        lines.append("  no C1 wells with dh_corr coverage in any window")
    else:
        for _, row in excl_block.iterrows():
            cf_txt = f"{row['mean_clearfell_i']:+.1f}" if not pd.isna(row['mean_clearfell_i']) else "n/a (no clearfell regressor this window)"
            lines.append(
                f"  {row['window']:12s} n={row['n']}  "
                f"mean coast_i={row['mean_coast_i']:+.1f}  "
                f"mean clearfell_i={cf_txt}  "
                f"mean dh_corr={row['mean_dh_corr']:+.1f}  "
                f"mean residual={row['mean_residual']:+.1f}"
            )
    lines.append(
        "  C1's level is management-set (sluice on Llyn Rhos-Ddu), not a read "
        "on natural hydrology — shown here for transparency (e.g. 2006–2012: "
        "held near a −269 mm mean against a uniform background well below "
        "it), not because C1 is anomalous. Excluding it from the fit moves "
        "every coefficient by ≲0.15 of its SE (see ADDENDUM 1)."
    )

    lines += ["", "INDEPENDENT TEST — implied δ₀(t) expanding-window trajectory", "-" * 70]
    if traj.empty:
        lines.append("  insufficient data — trajectory not computed")
    else:
        for _, row in traj.iterrows():
            flag = " †" if int(row["window_end_year"]) >= 2019 else ""
            lines.append(
                f"  2005–{int(row['window_end_year'])}  n={int(row['n'])}  "
                f"implied δ₀ = {row['implied_delta0_mm_yr']:+.1f} mm/yr  "
                f"95%CI [{row['ci_lo_implied_delta0']:+.1f}, {row['ci_hi_implied_delta0']:+.1f}]{flag}"
            )
    lines.append(
        f"  Assumed δ₀ = {delta0:.1f} mm/yr. A flat trajectory near this value "
        "supports the chronic-linear coastal-drying assumption; a rising or "
        "falling trajectory would not."
    )
    lines.append(
        "  † Per spec this test is COAST-ONLY (no clearfell regressor). Windows "
        "whose end year is >= 2019 span the Dec-2017 clearfell without a term to "
        "absorb its wetting signal, so their implied δ₀ may be inflated upward by "
        "un-modelled clearfell recovery, not genuine coastal-drying acceleration. "
        "Only 2005–2010/2013/2016 (fully pre-clearfell) are clean coast-only reads; "
        "treat 2005–2019/2022/2025 as upper bounds on the coastal signal alone."
    )

    lines += ["", "CAVEATS", "-" * 70]
    lines.append(
        "  Shape (δ₀, L) is fit from THIS SAME well network via Script 25 — "
        "the scale-factor test above is therefore partly self-confirming. "
        "The δ₀(t) trajectory (above) is the genuinely independent check."
    )
    lines.append(
        "  Does not resolve scraping (owned by BACI: CEH36 on-site BACI, "
        "WMC3 DiD). Does not close the coastal budget (first-order test). "
        "Broadleaf is a covariate at most, never a headline scale factor."
    )
    lines.append(
        "  If the residual map shows a coherent spatial gradient, a "
        "distance-decayed GLS is a candidate ROBUSTNESS variant — not built "
        "here, and would not replace the OLS headline."
    )

    OUT_RESULTS.write_text("\n".join(lines) + "\n")
    saved(OUT_RESULTS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    banner("37", "Per-Driver Scale-Factor Regression", version=__version__)
    DIR_37.mkdir(parents=True, exist_ok=True)

    # ── Phase 1: load Script 36 data ─────────────────────────────────────────
    phase(1, "Load Script 36 per-well data")
    df36 = load_script36_wells()
    info(f"Script 36 wells loaded: {len(df36)} total")
    for w, col in DH_CORR_COLS.items():
        info(f"  {w} ({col}): {df36[col].notna().sum()} wells with coverage")

    keys = list(df36["key"])
    b3   = load_master_b3(keys)
    n_b3 = sum(1 for v in b3.values() if np.isnan(v) or v <= 0.0)
    if n_b3:
        note(f"{n_b3} wells have β₃ ≤ 0 or NaN (excluded from all fits)")
    first_obs = load_first_obs_dates(keys)

    # ── Phase 2: live parameters ─────────────────────────────────────────────
    phase(2, "Load live parameters from upstream CSVs")
    delta0, L_coast   = _load_coastal_fit()
    clearfell_step_mm = _load_clearfell_step()

    # ── Phase 3: spatial factors ─────────────────────────────────────────────
    phase(3, "Build spatial factors via Script 20")
    step("importing Script 20 via importlib …")
    s20 = _load_s20()
    info("Script 20 loaded")
    spatial = _build_spatial(s20, df36["E"].values, df36["N"].values, clearfell_step_mm)

    step("importing Script 36 via importlib (for endpoint-group years only) …")
    s36 = _load_s36()
    info("Script 36 loaded")

    # ── Phase 4: per-window regressions ──────────────────────────────────────
    phase(4, "Per-window scale-factor regressions")
    results = {}
    for window in WINDOWS:
        win_start_yr = int(window.split("_")[0])
        win_end_yr   = int(window.split("_")[1])
        dt_mid_lut = build_dt_mid_lut(s36, keys, win_start_yr, win_end_yr)
        results[window] = run_window(df36, window, b3, spatial, delta0,
                                     clearfell_step_mm, first_obs, dt_mid_lut)

    # ── Phase 5: broadleaf covariate robustness (2018_2025 only) ────────────
    phase(5, "Broadleaf covariate — robustness variant (2018_2025 only)")
    dt_mid_2018 = build_dt_mid_lut(s36, keys, 2018, 2025)
    broadleaf_result = run_broadleaf_variant(
        df36, "2018_2025", b3, spatial, delta0, clearfell_step_mm,
        first_obs, dt_mid_2018)

    # ── Phase 6: independent δ₀(t) trajectory test ───────────────────────────
    phase(6, "Independent test — implied δ₀(t) expanding-window trajectory")
    traj = run_delta0_trajectory(df36, b3, spatial, delta0, s36)

    # ── Phase 7: outputs ──────────────────────────────────────────────────────
    phase(7, "Write outputs")
    scale_table = build_scale_factor_table(results, broadleaf_result)
    scale_table.to_csv(OUT_SCALE_FACTORS, index=False)
    saved(OUT_SCALE_FACTORS)

    write_per_well_csv(results)

    plot_scale_scatters(results)
    plot_residual_map(results["2005_2025"]["frame"], "2005_2025")
    plot_delta0_trajectory(traj, delta0)

    c1_block = neg_control_block(results)
    excl_block = excluded_sluice_block(results)
    write_results(scale_table, c1_block, excl_block, traj, delta0, clearfell_step_mm)

    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
