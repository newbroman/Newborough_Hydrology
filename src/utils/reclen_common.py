"""
reclen_common.py — the helpers the Script 50 suite (50a-50e) shares: inputs, fitting, free runs, the
datum runs and the beta_3-bound count. Moved whole from 50_record_length.py 1.30.0 (J-15, T-208).
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-11-24 (J-15, T-208).

import argparse
import importlib.util
import warnings
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils import paths                                       # noqa: E402
from utils.paths import (                                     # noqa: E402
    OUT_50_PER_WELL, OUT_50_BY_CLUSTER, OUT_50_CCW, OUT_50_STABLE, OUT_50_FIG,
    INT_WELLS_CLEAN, INT_CLIMATE, INT_MASTER_DATA,
    OUT_03_PER_WELL_WINDOW_SENS, OUT_48_MODEL_AB, OUT_39_PER_WELL,
    OUT_03_MODEL_B_PERSISTENCE, OUT_19_SCENARIO_PERWELL_MODEL_A, INT_LOCATIONS, OUT_15_DDP_PER_WELL,
    OUT_50_CCW_DATUM, OUT_50_SPLIT_DATUM, OUT_50_SPLIT_SERIES, OUT_50_SPLIT_FIG,
    OUT_50_NEIGHBOUR, OUT_50_NEIGHBOUR_FIG, OUT_50_TRANSFER_RULE, OUT_50_TRANSFER_FIG, OUT_50_DECISION_FIG,
    OUT_50_PROJ_DATUM, OUT_50_DATUM_FIG,
    OUT_50_RANWELL_DATUM, OUT_44_METRICS, RANWELL_LEVELS,
    OUT_50_TWO_STORE, OUT_50_TWO_STORE_WELL, OUT_50_TWO_STORE_FIG, INT_REGIONAL_AVG,
    OUT_50_CHANGE, OUT_50_SURFACE, OUT_50_CHANGE_SURFACE_FIG,
    MIDAS_RAIN_DIR, OUT_50_RAIN_EVENTS, OUT_50_EVENT_STRESS, OUT_50_RAIN_EVENTS_FIG,
    OUT_50_FELLING_DIST, OUT_50_NW9_TIMING, OUT_50_FELLING_FIG,
    OUT_50_CLEARANCE_STEP, OUT_50_CLEARANCE_FIG, DATA_SHORE_CLEARANCE_2015,
    OUT_03_MECHANISTIC_TABLE, OUT_50_PRECANOPY, OUT_41_INDEX, OUT_50_FOREST_FORCING,
    OUT_50_RANWELL_NEED, OUT_50_RANWELL_EPOCH, OUT_50_BASIS, OUT_50_PLACEMENT, OUT_50_PET_ALT, OUT_50_E13_PET, OUT_50_E13_BREAK, OUT_50_E13_WEATHER,
    OUT_50_E13_FIG, OUT_50_ELEV_DATUM_TESTS, OUT_50_ELEV_DATUM_SUMMARY, OUT_01B_REPORT_NUMBERS, OUT_50_CLUSTER_BASE_TESTS, OUT_50_CLUSTER_BASE_SUMMARY, OUT_03_WELL_OPTIMAL_DATUMS, OUT_50_CCW_QMAP, OUT_50_CCW_FILM_MAP, OUT_50_CCW_FILM_MAP_YEARS, OUT_50_E13B_CMP, OUT_50_E13B_FIG, OUT_50_E13B_RESID, OUT_50_E13B_INPUTS, INT_24_CLIMATOLOGY_TABLE, MIDAS_WEATHER_DIR, INT_WELLS_REFERENCE, INT_WELLS_EXTENDED, RANWELL_PARC_MAWR_RAIN, RANWELL_EPOCH_CANDIDATES, DATA_FOREST_BOUNDARY, OUT_20_REPORT_NUMBERS,
)
from utils.config import (                                    # noqa: E402
    DRAINAGE_DATUM, HEADLINE_LAG, CLUSTER_LABELS, CLUSTER_COLOURS, LCSC_DATA_LIMIT,
    MODEL_AB_SPLIT_DATE, MODEL_AB_MIN_TEST_MONTHS, PASTAS_IDENT_EFOLD_WINDOW_FRAC,
    TRANSFER_R2_TOL, TRANSFER_BIAS_TOL_M,
    RECLEN_LENGTHS_MONTHS, RECLEN_MIN_FIT_MONTHS, RECLEN_STABLE_TOL,
    RECLEN_DATUM_NSE_TOL, DATUM_SWEEP_MIN_M, DATUM_SWEEP_MAX_M, DATUM_SWEEP_STEP_M,
    DATUM_AOD_SWEEP_MIN_M, DATUM_AOD_SWEEP_MAX_M, DATUM_AOD_SWEEP_STEP_M, E17_CANDIDATES, E17_PRIMARY_CANDIDATE,
    E18_RMSE_CUT_M, E18_BASES, E18_PRIMARY_BASIS, QMAP_MIN_MONTHS, QMAP_MIN_WELLS, E19_MIN_MONTHS_PER_YEAR,
    FOREST_INTERCEPTION, UKCP18_SCENARIOS, WINTER_WET_CLIMATE_MONTHS, SUMMER_DRY_CLIMATE_MONTHS,
    RECORD_START_DISPLAY, REFERENCE_CUTOFF_DATE,
    TWO_STORE_FAST_INIT_DAYS, TWO_STORE_FAST_BOUNDS_DAYS, TWO_STORE_SLOW_INIT_DAYS,
    TWO_STORE_SLOW_BOUNDS_DAYS, TWO_STORE_SLOW_SHARE_INIT, TWO_STORE_EARLY_YEARS,
    TWO_STORE_EARLY_REDUCTION, TWO_STORE_LATER_RMSE_TOL_M, TWO_STORE_CCW_BIAS_TOL_M,
    TWO_STORE_CHECK_WELL, TWO_STORE_CHECK_CLUSTER, TWO_STORE_FLOOD_WINTERS, TWO_STORE_NEAR_WINTERS,
    TWO_STORE_DRY_WINTERS, TWO_STORE_SURFACE_TOL_M, TWO_STORE_NEAR_TOL_M, DAYS_PER_MONTH,
    TWO_STORE_SHARE_MIN, TWO_STORE_BOUND_TOL, BASIS_TOL_NSE, BASIS_TOL_BIAS_M, PLACEMENT_LENGTHS_MONTHS,
    TWO_STORE_BIC_STRONG, CHANGE_TSTART_INIT, CHANGE_TSTART_BOUNDS, CHANGE_SPLIT_DIRECTIONS,
    CHANGE_GRID_COARSE_MONTHS, SURFACE_THRESHOLD_GRID,
    SURFACE_BAND_M, SURFACE_THRESHOLD_MAX_DEPTH_M,
    E8D_PRIMARY_GAUGE, E8D_CHECK_GAUGE, E8D_WET_DAY_MM, E8D_EVENT_MIN_DAYS, E8D_EVENT_PCTL,
    E8D_BASELINE_END_YEAR, E8D_WINTER_MONTHS, E8D_MAX_MISSING_FRAC, E8D_UNUSUAL_PCTL, E8D_UNUSUAL_MIN_COUNT,
    E8D_TEST_WINTERS, E8D_FLOOD_WINTER, E8D_LATER_WINTERS, E8D_FIT_START, E8D_FIT_END,
    E8D_RESIDUAL_REDUCTION, E8D_CLUSTERS_WITH_EXCESS,
    E8E_MIN_EARLY_MONTHS, E8E_LATER_YEARS, E8E_P, E8E_NEAR_M, E8E_FAR_M, E8E_TIMING_BASE_YEARS,
    E8E_TIMING_TOL_YEARS, E8E_CHECK_WELL, E8E_CANOPY_REGION, E8E_CANOPY_VIEWPOINT, LAKE_GAUGE_KEYS,
    E8F_STEP_WINDOW, E8F_MIN_SIDE_MONTHS, E8F_NEAR_M, E8F_FAR_M, E8F_CONTROL_WELLS, E8F_PLACEBO_MAX_FRAC,
    E8F_WIDE_WINDOW, E8F_WIDE_STEP_MONTHS,
    PRECANOPY_ANALOGUE, PRECANOPY_PLANTING_YEARS, PRECANOPY_CLOSURE_YEARS, PRECANOPY_W_TAILS,
    PRECANOPY_SLOW_STARTS_DAYS, PRECANOPY_SHARE_STARTS,
    FORCING_NSE_GAIN, FOREST_FORCING_CLUSTERS, FOREST_FORCING_EDGE_REGION, FOREST_FORCING_BASE_REGION,
    RANWELL_NEED_K1_GRID, RANWELL_NEED_K2_GRID, RANWELL_NEED_K3_GRID, RANWELL_NEED_NSE_TOL, RANWELL_PIPE_FOOT_M,
    RANWELL_SEASON_WINDOW_YEARS, RANWELL_ANTECEDENT_YEARS, RANWELL_MEMORY_MONTHS, RANWELL_SURFACE_CENSOR_M,
    CLEARFELL_DATE_ISO, RAF_VALLEY_LAT_DEG,
    E13_EXCESS_SHARE, E13_RMSE_TOL, E13_CLUSTERS, E13_BREAK_WINDOW, E13_MIN_LATER_MONTHS,
    E13B_WINDOW_YEARS, E13B_SEASON_A_MONTHS, E13B_SEASON_B_MONTHS, E13B_RESID_SUMMER_MONTHS, E13B_RESID_WINTER_MONTHS, E13B_RESID_WINTER_PHASE,
    RESIDUAL_DIAG_MIN_MONTHS, MIDAS_MONTH_MIN_DAYS, MODEL_B_BETA3_MIN,
)
from utils.data_utils import normalize_well_name              # noqa: E402
from utils.model_utils import (build_ssm_frame, fit_ssm, fit_ssm_intercept, simulate_ssm, get_metrics,   # noqa: E402
                               sustained_monthly_response, climate_forcing_change_12, response_identified,
                               sustained_monthly_response_ddp, dry_bounds)
from utils.hindcast_utils import (                            # noqa: E402
    load_ccw, observed_series, hindcast_well, equilibrium_depth, usable_codes, compare_offset_censored,
    quantile_map,
)
from utils.render_utils import (MPL_DEFAULTS, apply_house_style,   # noqa: E402
                                render_figure)                     # noqa: E402  (J-6)
from utils.pastas_utils import spread_daily, continuous_start  # noqa: E402
from utils.midas_rain import read_daily  # noqa: E402
from utils.pet_alternatives import monthly_radiation_pet, midas_monthly_pm, midas_span, read_raf_monthly  # noqa: E402
from utils.clearfell_common import EDGE_WELLS  # noqa: E402
from utils.report_numbers_utils import ReportNumbers          # noqa: E402
from utils.console_utils import (banner, done, info, phase, result, saved, step, track,  # noqa: E402
                                 warn)                                                   # noqa: E402

FORMS = (("A", False), ("B", True))
# 1.25.0 (D-332): the MHW form -- Model A at each well's depth to mean high water (Script 48's form M). It runs
# where a well has a ground level, at that well's own datum, so it is not a member of FORMS (whose fits are all
# built at DRAINAGE_DATUM); REPORT_FORMS is FORMS plus it, for the summaries and report numbers.
FORM_MHW = "M"
REPORT_FORMS = FORMS + ((FORM_MHW, False),)
FULL = "full"
LENGTHS = tuple(str(L) for L in RECLEN_LENGTHS_MONTHS) + (FULL,)
SIG_P = 0.05


# ──────────────────────────────────────────────────────────────────────────────
# Fitting and running one record
# ──────────────────────────────────────────────────────────────────────────────
def fit_frame(frame: pd.DataFrame, intercept: bool):
    """The SSM on exactly the rows of `frame` (a slice of build_ssm_frame's output)."""
    if frame is None or len(frame) < RECLEN_MIN_FIT_MONTHS:
        return None
    try:
        return fit_ssm(pre_built_frame=frame, intercept=intercept,
                       min_obs=RECLEN_MIN_FIT_MONTHS, with_corr=True)
    except Exception:
        return None


def _censored_well_fit(h: pd.Series, cl: pd.DataFrame, db, window, intercept: bool,
                       datum: float = DRAINAGE_DATUM):
    """1.24.0 (D-322): one well fitted as Script 03 fits it: dry months censored (dry_bound), over calendar
    months (window = the last N, None = all of h). None where the fit fails, as fit_frame returns."""
    db = db if (db is not None and len(db)) else None
    try:
        return fit_ssm(h, cl, lag=HEADLINE_LAG, window=window, drainage_datum=float(datum),
                       min_obs=RECLEN_MIN_FIT_MONTHS, intercept=intercept, with_corr=True, dry_bound=db)
    except Exception:
        return None


def run_datum(fit: dict, intercept: bool, base: float = DRAINAGE_DATUM) -> float:
    """The datum a fit is run at: Model B is Model A at base - alpha/beta_3 (base is the datum the
    frame was built at)."""
    b3 = fit["beta_3_drainage"]
    return base - (fit["alpha"] / b3 if intercept else 0.0)


def describe(fit: dict, intercept: bool, frame: pd.DataFrame) -> dict:
    """Coefficients and the quantities derived from them, for one fit."""
    if fit is None:
        return {"fitted": False}
    b1, b2, b3 = fit["beta_1_recharge"], fit["beta_2_atmospheric_draw"], fit["beta_3_drainage"]
    efold = (-1.0 / np.log(1.0 - b3)) if 0 < b3 < 1 else np.nan
    drain = b3 * fit["mean_h_disp_prev"] - (fit["alpha"] if intercept else 0.0)
    et = b2 * fit["mean_PET"]
    ident = bool(b3 > 0 and fit["pvalue_beta_3"] < SIG_P)
    if intercept:
        ident = ident and bool(np.isfinite(efold) and efold < PASTAS_IDENT_EFOLD_WINDOW_FRAC * fit["n"])
    return {
        "fitted": True, "n_fit": int(fit["n"]),
        "fit_start": frame.index.min().strftime("%Y-%m"), "fit_end": frame.index.max().strftime("%Y-%m"),
        "beta_1": b1, "beta_2": b2, "beta_3": b3, "p_beta_3": fit["pvalue_beta_3"],
        "alpha": fit.get("alpha", np.nan), "R2": fit["R2"],
        "efold_months": efold,
        "t_half_months": (np.log(2.0) / b3) if b3 > 0 else np.nan,
        "rho_ar1_expected": ((1.0 - b3) ** 12) if b3 < 1 else np.nan,
        "drainage_share": drain / (drain + et) if (drain + et) > 0 else np.nan,
        "identified": ident,
        # 1.25.0 (D-332): Model B's beta_3 held at MODEL_B_BETA3_MIN (model_utils 1.14.0); never True for Model A
        "beta_3_bound": bool(fit.get("beta_3_bound_binds", False)),
    }


def free_run(h_test: pd.Series, cl: pd.DataFrame, fit: dict, intercept: bool,
             base: float = DRAINAGE_DATUM) -> dict:
    """A free run over the observed months of h_test from its first reading, at the datum the
    form was fitted with — the same procedure as Script 48's _free_run_nse."""
    out = {"n_test": 0, "nse": np.nan, "rmse_m": np.nan, "bias_m": np.nan}
    h = h_test.dropna()
    if fit is None or len(h) < MODEL_AB_MIN_TEST_MONTHS + 1:
        return out
    months = pd.date_range(h.index[0], h.index[-1], freq="MS")
    clim = cl.reindex(months)
    if clim[["P_m", "PET"]].iloc[1:].isna().any().any():
        return out
    sim = pd.Series(simulate_ssm(float(h.iloc[0]), clim["P_m"].values[1:], clim["PET"].values[1:],
                                 fit["beta_1_recharge"], fit["beta_2_atmospheric_draw"],
                                 fit["beta_3_drainage"], drainage_datum=run_datum(fit, intercept, base)),
                    index=months[1:])
    obs = h.iloc[1:]
    s_ = sim.reindex(obs.index)
    ok = s_.notna()
    out["n_test"] = int(ok.sum())
    if ok.sum() < MODEL_AB_MIN_TEST_MONTHS:
        return out
    o, m = obs[ok], s_[ok]
    den = float(((o - o.mean()) ** 2).sum())
    out["nse"] = 1.0 - float(((o - m) ** 2).sum()) / den if den > 0 else np.nan
    out["rmse_m"] = float(np.sqrt(((o - m) ** 2).mean()))
    out["bias_m"] = float((m - o).mean())
    return out


# ──────────────────────────────────────────────────────────────────────────────
# The experiments
# ──────────────────────────────────────────────────────────────────────────────
def _model_a_store(df: pd.DataFrame) -> pd.DataFrame:
    """1.28.0 (D-332, phase 2b): a Script 03 coefficient table as its MODEL A store. Script 03 1.31.0 writes
    Model B in the unsuffixed columns and Model A in <column>_model_a. Every committed-coefficient read in this
    script means Model A (Script 39's admission rule via usable_codes, T-173b's coefficient differences, E11's
    open-ground ratios, E8g's centroids); Model B is always this script's own fit. So each *_model_a column takes
    its unsuffixed name here, and Cluster, names and n pass through."""
    ren = {c: c[:-len("_model_a")] for c in df.columns if c.endswith("_model_a")}
    return df.drop(columns=[v for v in ren.values() if v in df.columns]).rename(columns=ren)


def load_inputs():
    lev = pd.read_csv(INT_WELLS_CLEAN, index_col=0)
    lev.index = pd.to_datetime(lev.index)
    cl = pd.read_csv(INT_CLIMATE, index_col=0)
    cl.index = pd.to_datetime(cl.index)
    master = _model_a_store(pd.read_csv(INT_MASTER_DATA))
    master["_n"] = master["Name_Original"].astype(str).apply(normalize_well_name)
    lev_cols = {normalize_well_name(c): c for c in lev.columns}
    return lev, lev_cols, cl, master


def _dkey(D: float) -> str:
    return f"{D:g}"


def _nse(o: pd.Series, s: pd.Series) -> float:
    o, s = o.align(s, join="inner")
    ok = o.notna() & s.notna()
    o, s = o[ok], s[ok]
    den = float(((o - o.mean()) ** 2).sum())
    return 1.0 - float(((o - s) ** 2).sum()) / den if len(o) > 2 and den > 0 else np.nan


# ──────────────────────────────────────────────────────────────────────────────
# E16: Model A(ii) — one drainage base in elevation for every well (1.19.0, D-286)
# ──────────────────────────────────────────────────────────────────────────────
# Model A refers each well's head to a depth below its own ground (DRAINAGE_DATUM). Model A(ii) refers every
# well to ONE level z0 above Ordnance Datum, a per-well datum of ground - z0 (Script 03's datum_aod_sweep, D-163
# route 4). Script 03 found the two indistinguishable on fit (D-256). Since Model A's job is now the forward run
# (D-230, D-283), E16 scores A(ii) on the forward tests: the CCW 1989-96 hindcast, Ranwell 1951-53 and the
# within-record split, on the same code paths as E5, E9 and E6, against Model A at the depth datum on the same
# wells. It also measures how far beta_3 under each datum only restates the height above that datum (Spearman
# rho of beta_3 against the per-well datum), which is what Martin asked of A(ii)'s beta_3 (2026-10-28 03:15).
# The adoption rule is fixed before the run (E16_* in config, D-286).
def _e16_grounds() -> dict:
    loc = pd.read_csv(INT_LOCATIONS)
    g = pd.to_numeric(loc["ground_elev_m"], errors="coerce")
    return {normalize_well_name(n): float(v) for n, v in zip(loc["Name"], g) if np.isfinite(v)}


def _e16_mhw() -> float:
    if not OUT_01B_REPORT_NUMBERS.exists():
        return np.nan
    r = pd.read_csv(OUT_01B_REPORT_NUMBERS)
    v = r.loc[r["Parameter"] == "tide_mhw_m", "Value"]
    return float(v.iloc[0]) if len(v) else np.nan


def mhw_depths() -> dict:
    """1.25.0 (D-332): each well's depth from ground to mean high water (m), the MHW form's datum: E16's grounds
    (01_locations ground_elev_m) less 01b's tide_mhw_m, as Script 48's form M takes it. Empty if MHW is absent."""
    mhw = _e16_mhw()
    if not np.isfinite(mhw):
        warn("tide_mhw_m not in 01b's report numbers - the MHW form is skipped")
        return {}
    return {k: float(g - mhw) for k, g in _e16_grounds().items()}


def beta3_bound_report(rr, tables: dict) -> None:
    """1.25.0 (D-332): how many Model B fits hold beta_3 at MODEL_B_BETA3_MIN (model_utils 1.14.0), per test.
    Before the bound these fits were dropped (beta_3 <= 0) or ran with a negative beta_3; now they are kept,
    flagged and counted. A bound fit's beta_3 is exactly the bound, so the count reads it from the value."""
    for name, (t, col, what) in tables.items():
        if t is None or not len(t) or col not in t.columns or "form" not in t.columns:
            continue
        b = pd.to_numeric(t.loc[t["form"] == "B", col], errors="coerce")
        n_b = int(b.notna().sum())
        rr.add(f"beta3_bound_B_n_{name}", float((b == MODEL_B_BETA3_MIN).sum()), unit="count",
               note=f"Model B fits with beta_3 held at its lower bound {MODEL_B_BETA3_MIN:g}, of {n_b} fitted: {what}")
