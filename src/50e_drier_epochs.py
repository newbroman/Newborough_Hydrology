"""
50e_drier_epochs.py — Drier epochs and forcing (E10, E11, E13/E13b, E19: D-260, D-261, D-273, D-274, D-292).

Script 50 suite, step 50e (J-15, T-208; Martin 2026-11-24: five families, numbered 50a-50e,
all opt-in). Split from 50_record_length.py 1.30.0, whose full version history is kept in git and in
50a_record_length.py; every function moved whole with its dated comments. Shared helpers live in
utils/reclen_common.py.
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) — 2026-11-26 (D-347 (5)): the E13 fits (_e13_run, e13_break) keep
#   the whole record (start=None); their subject is the 2006-08 excess. Nothing else changes.
# 1.0.0  # Hollingham (2026) - 2026-11-24 (J-15, T-208). Split from Script 50 1.30.0.

import argparse
import importlib.util
import warnings
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils import paths                                       # noqa: E402
from utils.paths import (                                     # noqa: E402
    DIR_50E, OUT_50E_REPORT_NUMBERS, OUT_50_PER_WELL, OUT_50_BY_CLUSTER, OUT_50_CCW, OUT_50_STABLE, OUT_50_FIG,
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
from utils.reclen_common import (   # noqa: E402  (the suite's shared helpers, J-15)
    _censored_well_fit, _dkey, _e16_grounds, _e16_mhw, _model_a_store,
    _nse, beta3_bound_report, describe, fit_frame, free_run,
    load_inputs, mhw_depths, run_datum,
)


# ── E10 (1.9.0, D-260): is the forest's poor forecasting the drainage or the forcing? ──────────────────
FORCING_VARIANTS = ("F0", "F1", "F2", "F3")


# Post hoc (Martin 2026-10-13, after the rule's run): outside the rule, reported separately.
# F2e: only the clearfell edge wells' forcing changes (inner wells' canopy held at 1, so they fit as F0);
# F2s: a placebo for the inner wells' gain - their canopy replaced by one step at the felling to the region's
# post-felling mean, which tests whether that gain is a one-off shift rather than the canopy tracked.
FORCING_POSTHOC = ("F2e", "F2s")


FOREST_FORCING_VERDICT = {"supported": 2, "not resolved": 1, "not supported": 0}


def canopy_monthly(index: pd.DatetimeIndex) -> dict:
    """Script 41's canopy ratio for the edge and base regions, monthly on `index`: the mean over viewpoints
    per imagery date, divided by the region's median before CLEARFELL_DATE_ISO (closed canopy = 1), clipped
    to [0, 1], interpolated linearly between imagery dates and held beyond them."""
    d = pd.read_csv(OUT_41_INDEX, parse_dates=["imagery_date"])
    d = d[d["ratio_to_conifer"].notna()]
    fell = pd.Timestamp(CLEARFELL_DATE_ISO)
    out = {}
    for reg in (FOREST_FORCING_EDGE_REGION, FOREST_FORCING_BASE_REGION):
        g = d[d["region"] == reg].groupby("imagery_date")["ratio_to_conifer"].mean().sort_index()
        ref = float(g[g.index < fell].median())
        c = (g / ref).clip(0.0, 1.0)
        x = c.index.map(pd.Timestamp.toordinal).to_numpy(float)
        out[reg] = pd.Series(np.interp(index.map(pd.Timestamp.toordinal).to_numpy(float), x, c.to_numpy()),
                             index=index)
    return out


def _forcing_climate(cl: pd.DataFrame, variant: str, canopy: pd.Series) -> pd.DataFrame:
    """The climate frame a forest well is fitted with: F0 as observed; F1 rainfall less FOREST_INTERCEPTION;
    F2 and F3 rainfall less FOREST_INTERCEPTION scaled by the canopy (interception goes with the canopy)."""
    c = cl.copy()
    if variant == "F1":
        c["P_m"] = c["P_m"] * (1.0 - FOREST_INTERCEPTION)
    elif variant in ("F2", "F3") + FORCING_POSTHOC:
        c["P_m"] = c["P_m"] * (1.0 - FOREST_INTERCEPTION * canopy.reindex(c.index).fillna(1.0))
    return c


def _post_fell_fit(frame: pd.DataFrame, intercept: bool, post: pd.Series):
    """F3 at a clearfell edge well: the SSM with one extra regressor, -PET in the months after felling, so felled
    ground takes its own evaporation coefficient. Ordinary least squares on build_ssm_frame's columns (the
    alignment is not reimplemented); returns the coefficients, the residuals and the BIC."""
    X = np.column_stack([frame["P"], -frame["PET"], -frame["h_disp_prev"], -frame["PET"] * post.reindex(frame.index).fillna(0.0)])
    if intercept:
        X = np.column_stack([X, np.ones(len(frame))])
    y = frame["Delta_h"].to_numpy(float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return beta, pd.Series(resid, index=frame.index), _bic(resid, X.shape[1])


def _bic(resid, k: int) -> float:
    r = np.asarray(resid, float)
    r = r[np.isfinite(r)]
    n = len(r)
    return float(n * np.log(np.sum(r ** 2) / n) + k * np.log(n)) if n > k else np.nan


def _ssm_resid(fit: dict, frame: pd.DataFrame, intercept: bool) -> pd.Series:
    pred = (fit["beta_1_recharge"] * frame["P"] - fit["beta_2_atmospheric_draw"] * frame["PET"]
            - fit["beta_3_drainage"] * frame["h_disp_prev"] + (fit.get("alpha", 0.0) if intercept else 0.0))
    return frame["Delta_h"] - pred


def _season_contrast(resid: pd.Series) -> float:
    """Summer minus winter mean residual (m), the statistic of Script 24, on the one-step residuals."""
    m = resid.index.month
    s_ = resid[np.isin(m, SUMMER_DRY_CLIMATE_MONTHS)].mean()
    w_ = resid[np.isin(m, WINTER_WET_CLIMATE_MONTHS)].mean()
    return float(s_ - w_)


def forest_forcing(lev, lev_cols, cl, master, df_full):
    """E10 (D-260): every C4/C5 reference well under four forcings, both forms; F0 identity-checked against the
    full-record fits of the record-length experiment (df_full)."""
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    fell = pd.Timestamp(CLEARFELL_DATE_ISO)
    canopy = canopy_monthly(cl.index)
    post = pd.Series((cl.index >= fell).astype(float), index=cl.index)
    rows = []
    sub = master[master["Cluster"].isin(FOREST_FORCING_CLUSTERS)]
    for k, cluster in zip(sub["_n"], sub["Cluster"]):
        if k not in lev_cols:
            continue
        h = lev[lev_cols[k]].dropna()
        edge = k in EDGE_WELLS
        can = canopy[FOREST_FORCING_EDGE_REGION if edge else FOREST_FORCING_BASE_REGION]
        base = canopy[FOREST_FORCING_BASE_REGION]
        posthoc_can = {"F2e": can if edge else pd.Series(1.0, index=cl.index),
                       "F2s": can if edge else pd.Series(np.where(cl.index >= fell, float(base[base.index >= fell].mean()),
                                                                  1.0), index=cl.index)}
        for variant in FORCING_VARIANTS + FORCING_POSTHOC:
            clv = _forcing_climate(cl, variant, posthoc_can.get(variant, can))
            full = build_ssm_frame(h, clv, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM)
            pre = build_ssm_frame(h[h.index < split], clv, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM)
            postf = build_ssm_frame(h[h.index >= split], clv, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM)
            for form, icpt in FORMS:
                row = {"well": k, "cluster": int(cluster), "edge": edge, "variant": variant, "form": form}
                f = fit_frame(full, icpt)
                row.update({f"full_{a}": b for a, b in describe(f, icpt, full).items()})
                if f is not None:
                    res = _ssm_resid(f, full, icpt)
                    row["bic"] = _bic(res, 3 + int(icpt))
                    row["season_contrast_m"] = _season_contrast(res)
                if variant == "F3" and edge and full is not None and len(full):
                    beta, res, bic = _post_fell_fit(full, icpt, post)
                    row.update(bic=bic, season_contrast_m=_season_contrast(res), beta_2_post_fell=float(beta[3]),
                               full_beta_2=float(beta[1]), full_beta_3=float(beta[2]))
                # split tests: F3's extra coefficient cannot be estimated on either side of the split (the
                # felling falls at it), so F3 forecasts as F2 does
                fp, fq = fit_frame(pre, icpt), fit_frame(postf, icpt)
                row["fwd_nse"] = free_run(h[h.index >= split], clv, fp, icpt)["nse"]
                row["rev_nse"] = free_run(h[h.index < split], clv, fq, icpt)["nse"]
                rows.append(row)
    tab = pd.DataFrame(rows)
    # identity check: F0 must reproduce the record-length experiment's full-record fits
    chk = np.nan
    if len(df_full):
        ref = df_full[(df_full["experiment"] == "stability") & (df_full["length"] == FULL)].set_index(["well", "form"])["beta_3"]
        f0 = tab[tab["variant"] == "F0"].set_index(["well", "form"])["full_beta_3"]
        both = pd.concat([f0, ref], axis=1, join="inner").dropna()
        chk = float((both.iloc[:, 0] - both.iloc[:, 1]).abs().max()) if len(both) else np.nan
    return tab, chk


def forest_forcing_verdicts(tab: pd.DataFrame) -> dict:
    """The rule fixed before the run (Martin 2026-10-13): per cluster, the best of F1-F3 by summed Model A BIC is
    'supported' if it raises the median Model A forward NSE by FORCING_NSE_GAIN over F0, makes Model B's beta_3
    identified at a majority of wells, and shrinks |summer - winter residual|; 'not supported' if no variant raises
    the median forward NSE; 'not resolved' otherwise."""
    out = {}
    for c in sorted(tab["cluster"].unique()):
        g = tab[tab["cluster"] == c]
        A, B = g[g["form"] == "A"], g[g["form"] == "B"]
        med = lambda d, v, col: float(d[d["variant"] == v][col].median())
        bic = {v: float(A[A["variant"] == v]["bic"].sum()) for v in FORCING_VARIANTS}  # post hoc excluded
        best = min(("F1", "F2", "F3"), key=lambda v: bic[v])
        n_w = int(B[B["variant"] == best]["well"].nunique())
        n_id = int(B[(B["variant"] == best) & (B["full_identified"] == True)]["well"].nunique())  # noqa: E712
        gains = {v: med(A, v, "fwd_nse") - med(A, "F0", "fwd_nse") for v in ("F1", "F2", "F3")}
        t1 = gains[best] >= FORCING_NSE_GAIN
        t2 = n_id > n_w / 2
        t3 = abs(med(A, best, "season_contrast_m")) < abs(med(A, "F0", "season_contrast_m"))
        v = ("supported" if (t1 and t2 and t3) else
             "not supported" if max(gains.values()) <= 0 else "not resolved")
        out[c] = {"verdict": v, "best": best, "gain": gains[best], "gains": gains, "n_identified": n_id, "n_wells": n_w,
                  "n_identified_F0": int(B[(B["variant"] == "F0") & (B["full_identified"] == True)]["well"].nunique()),  # noqa: E712
                  "fwd_F0": med(A, "F0", "fwd_nse"), "fwd_best": med(A, best, "fwd_nse"),
                  "season_F0": med(A, "F0", "season_contrast_m"), "season_best": med(A, best, "season_contrast_m"),
                  "dbic_best": bic["F0"] - bic[best], "tests": (t1, t2, t3),
                  "posthoc": {(v, part): float(A[(A["variant"] == v) & (A["edge"] == e)]["fwd_nse"].median())
                              for v in ("F0", "F2") + FORCING_POSTHOC for part, e in (("inner", False), ("edge", True))},
                  "posthoc_all": {v: med(A, v, "fwd_nse") for v in FORCING_POSTHOC}}
    return out


def forest_forcing_report(rr, ver: dict, chk: float) -> None:
    code = {"F0": 0, "F1": 1, "F2": 2, "F3": 3}
    for c, v in ver.items():
        rr.add(f"forest_forcing_verdict_C{c}", FOREST_FORCING_VERDICT[v["verdict"]], unit="code",
               note=f"C{c}: {v['verdict']} (2 supported, 1 not resolved, 0 not supported); E10, the forest forcing test, "
                    f"rule fixed before the run (D-260)")
        rr.add(f"forest_forcing_best_variant_C{c}", code[v["best"]], unit="code",
               note=f"C{c}: best of F1-F3 by summed Model A BIC (1 interception, 2 interception with the canopy, "
                    f"3 and a post-felling evaporation coefficient)")
        rr.add(f"forest_forcing_fwd_nse_F0_median_C{c}", v["fwd_F0"], unit="", note=f"C{c}: median forward NSE, Model A, observed forcing")
        rr.add(f"forest_forcing_fwd_nse_best_median_C{c}", v["fwd_best"], unit="", note=f"C{c}: median forward NSE, Model A, best forcing")
        for var, g in v["gains"].items():
            rr.add(f"forest_forcing_fwd_gain_{var}_C{c}", g, unit="", note=f"C{c}: median forward NSE gain over F0, Model A, {var}")
        rr.add(f"forest_forcing_n_identified_B_best_C{c}", v["n_identified"], unit="wells",
               note=f"C{c}: wells whose Model B beta_3 is identified under the best forcing (of {v['n_wells']})")
        rr.add(f"forest_forcing_n_identified_B_F0_C{c}", v["n_identified_F0"], unit="wells",
               note=f"C{c}: wells whose Model B beta_3 is identified under the observed forcing")
        rr.add(f"forest_forcing_season_contrast_F0_median_C{c}", v["season_F0"], unit="m",
               note=f"C{c}: median summer-minus-winter one-step residual, Model A, observed forcing")
        rr.add(f"forest_forcing_season_contrast_best_median_C{c}", v["season_best"], unit="m",
               note=f"C{c}: median summer-minus-winter one-step residual, Model A, best forcing")
        rr.add(f"forest_forcing_dbic_best_C{c}", v["dbic_best"], unit="BIC",
               note=f"C{c}: summed Model A BIC of F0 minus the best forcing's (positive favours the forcing)")
    for c, v in ver.items():
        for (var, part), x in v["posthoc"].items():
            rr.add(f"forest_forcing_posthoc_fwd_nse_{var}_{part}_C{c}", x, unit="",
                   note=f"C{c}: POST HOC, outside the D-260 rule - median forward NSE, Model A, {var}, {part} wells "
                        f"(edge = clearfell_common.EDGE_WELLS)")
        for var, x in v["posthoc_all"].items():
            rr.add(f"forest_forcing_posthoc_fwd_nse_{var}_C{c}", x, unit="",
                   note=f"C{c}: POST HOC, outside the D-260 rule - median forward NSE, Model A, {var}, all wells")
    rr.add("forest_forcing_check_max_abs_beta3_diff", chk, unit="",
           note="identity: F0 against the record-length experiment's full-record beta_3, both forms, forest wells")


# ── E11 (1.10.0, D-261): what Ranwell's 1951-53 readings need of the model, and what could supply it ──────
# Exploration, not a test (Martin 2026-10-14 07:30): the results were seen before this step was written. The need is
# found by scaling each coefficient of Script 44's pairings; each candidate is then sized against it, from the record
# where it can be measured and from the literature (data/ranwell_epoch_candidates.csv) where it cannot.

def _e11_inputs(cl):
    lv = pd.read_csv(RANWELL_LEVELS, parse_dates=["date"])
    lv["month"] = lv["date"].dt.to_period("M")
    obs_month = lv.groupby(["site_no", "month"])["level_m_od"].mean()
    foot = (lv.groupby("site_no")["depth_below_surface_cm"].max() / 100.0).clip(lower=RANWELL_PIPE_FOOT_M)
    pairs = pd.read_csv(OUT_44_METRICS)
    clh = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    months = obs_month.index.get_level_values("month")
    first = pd.Timestamp(f"{months.min().year - 1}-12-01")
    last = months.max().to_timestamp()
    return obs_month, foot, pairs, clh, first, last


def _e11_score(om, clh, betas, k, first, last, ground, foot=None):
    """Script 44's hindcast with each coefficient scaled by k, scored as Script 44 scores it; with `foot`, the
    model is also capped at the pipe's foot, as the instrument would have read it."""
    b = (betas[0] * k[0], betas[1] * k[1], betas[2] * k[2])
    h0 = equilibrium_depth(b, float(clh["P_m"].mean()), float(clh["PET"].mean()), drainage_datum=DRAINAGE_DATUM)
    sim, _ = hindcast_well(clh, b, h0, first, last, 1.0, drainage_datum=DRAINAGE_DATUM)
    mid = (sim + sim.shift(1)) / 2
    mid.index = mid.index.to_period("M")
    mid = mid.dropna() + ground
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # a flat model at the grid's extremes has no correlation
        m = compare_offset_censored(om, mid, ground)
        if foot is not None:
            # the pipe cannot read below its foot: cap the offset model there, as the instrument would have seen it
            o, pa = _offset_model(om, mid, ground)
            pa = np.maximum(pa, ground - foot)
            m = dict(m, nse_after_offset=1 - float(((o - pa) ** 2).sum() / ((o - o.mean()) ** 2).sum()),
                     range_model_m=float(pa.max() - pa.min()))
    m["mid"] = mid
    return m


def _offset_model(om, mid, ground):
    """The model as compare_offset_censored scores it: offset fitted on the uncensored months, capped at the ground."""
    common = om.index.intersection(mid.index)
    o, p = om.loc[common].astype(float), mid.loc[common].astype(float)
    free = o <= ground - RANWELL_SURFACE_CENSOR_M
    off = float((o[free] - p[free]).mean()) if free.sum() >= 3 else float((o - p).mean())
    return o, np.minimum(p + off, ground)


def ranwell_need(cl):
    """Every Script 44 pairing over RANWELL_NEED_K1/K2/K3_GRID; identity: k = 1 reproduces Script 44's NSE."""
    if not (RANWELL_LEVELS.exists() and OUT_44_METRICS.exists()):
        warn("Ranwell readings or Script 44's pairings not present — E11 is skipped")
        return pd.DataFrame(), np.nan
    obs_month, foot, pairs, clh, first, last = _e11_inputs(cl)
    rows, chk = [], []
    for pr in pairs.itertuples():
        s = int(pr.site_no)
        if s not in obs_month.index.get_level_values(0):
            continue
        om = obs_month.loc[s]
        betas = (float(pr.beta_1), float(pr.beta_2), float(pr.beta_3))
        base = dict(site_no=s, sketch_slack=pr.sketch_slack, well=normalize_well_name(pr.well), headline=bool(pr.headline))
        for k1 in RANWELL_NEED_K1_GRID:
            for k2 in RANWELL_NEED_K2_GRID:
                for k3 in RANWELL_NEED_K3_GRID:
                    m = _e11_score(om, clh, betas, (k1, k2, k3), first, last, float(pr.ground_m_od))
                    rows.append(dict(base, k1=k1, k2=k2, k3=k3, pipe_foot=False, nse=m["nse_after_offset"],
                                     range_ratio=m["range_obs_m"] / m["range_model_m"] if m["range_model_m"] else np.nan,
                                     n=m["n"], n_at_surface=m["n_at_surface"]))
                    if k1 == 1.0 and k2 == 1.0 and k3 == 1.0:
                        chk.append(abs(m["nse_after_offset"] - float(pr.nse_after_offset)))
        # the instrument: the same single-coefficient profiles with the model capped at the pipe's foot
        for kk in ([(k, 1.0, 1.0) for k in RANWELL_NEED_K1_GRID] + [(1.0, k, 1.0) for k in RANWELL_NEED_K2_GRID]
                   + [(1.0, 1.0, k) for k in RANWELL_NEED_K3_GRID]):
            m = _e11_score(om, clh, betas, kk, first, last, float(pr.ground_m_od), foot=float(foot.loc[s]))
            rows.append(dict(base, k1=kk[0], k2=kk[1], k3=kk[2], pipe_foot=True, nse=m["nse_after_offset"],
                             range_ratio=m["range_obs_m"] / m["range_model_m"] if m["range_model_m"] else np.nan,
                             n=m["n"], n_at_surface=m["n_at_surface"]))
    return pd.DataFrame(rows), (float(max(chk)) if chk else np.nan)


def _single_profile(g: pd.DataFrame, k: str) -> pd.Series:
    others = [c for c in ("k1", "k2", "k3") if c != k]
    sub = g[(g[others[0]] == 1.0) & (g[others[1]] == 1.0)]
    return sub.groupby(k)["nse"].median()


def ranwell_need_summary(grid: pd.DataFrame) -> dict:
    g = grid[~grid["pipe_foot"]]
    med = g.groupby(["k1", "k2", "k3"])["nse"].median()
    best = med.idxmax()
    near = med[med >= med.max() - RANWELL_NEED_NSE_TOL].reset_index()
    out = dict(n_pairs=int(g.groupby(["site_no", "well"]).ngroups), nse_base=float(med.loc[(1.0, 1.0, 1.0)]),
               joint=dict(k1=float(best[0]), k2=float(best[1]), k3=float(best[2]), nse=float(med.max())),
               near={c: (float(near[c].min()), float(near[c].max())) for c in ("k1", "k2", "k3")}, single={})
    for k in ("k1", "k2", "k3"):
        p = _single_profile(g, k)
        out["single"][k] = dict(k=float(p.idxmax()), nse=float(p.max()))
    per = g.groupby(["site_no", "well"]).apply(
        lambda d: _single_profile(d, "k3").idxmax(), include_groups=False)
    out["k3_pairs_faster"] = int((per > 1).sum())
    out["k3_pairs_slower"] = int((per < 1).sum())
    pf = grid[grid["pipe_foot"] & (grid["k1"] == 1.0) & (grid["k2"] == 1.0) & (grid["k3"] == 1.0)]["nse"]
    out["nse_pipe_foot"] = float(pf.median())
    return out


def ranwell_epoch_context(cl, lev, lev_cols, need: dict) -> tuple[pd.DataFrame, dict]:
    """The measured checks (seasonality, the years before, the model's memory, on-site rain, the swing then and
    now, the pipe's foot) and the literature candidates, each sized against the need."""
    obs_month, foot, pairs, clh, first, last = _e11_inputs(cl)
    y0, y1 = obs_month.index.get_level_values("month").min().year, obs_month.index.get_level_values("month").max().year
    ctx, rows = {}, []
    # seasonality: the readings' years against every window of the same length after the climate record's last gap
    c = (clh * 1000.0).copy()
    c["yr"], c["mo"] = c.index.year, c.index.month
    full = c.groupby("yr").filter(lambda d: len(d) == 12)
    def season(w):
        s_, w_ = w[w.mo.isin(SUMMER_DRY_CLIMATE_MONTHS)], w[w.mo.isin(WINTER_WET_CLIMATE_MONTHS)]
        n = w.yr.nunique()
        return dict(P_summer=s_.P_m.sum() / n, P_winter=w_.P_m.sum() / n, PET_summer=s_.PET.sum() / n,
                    net_summer=(s_.P_m - s_.PET).sum() / n, net_winter=(w_.P_m - w_.PET).sum() / n,
                    contrast=((w_.P_m - w_.PET).sum() - (s_.P_m - s_.PET).sum()) / n)
    yrs = sorted(full.yr.unique())
    win = {a: season(full[(full.yr >= a) & (full.yr < a + RANWELL_SEASON_WINDOW_YEARS)])
           for a in yrs if all(b in yrs for b in range(a, a + RANWELL_SEASON_WINDOW_YEARS))}
    W = pd.DataFrame(win).T
    ep = W.loc[y0]
    ctx["season_pct"] = {k: float((W[k] < ep[k]).mean() * 100) for k in W.columns}
    ann = full.groupby("yr").apply(lambda d: (d.P_m - d.PET).sum(), include_groups=False)
    roll = ann.rolling(RANWELL_ANTECEDENT_YEARS).sum().dropna()
    ctx["antecedent_net_mm"] = float(roll.loc[y0 - 1])
    ctx["antecedent_pct"] = float((roll < roll.loc[y0 - 1]).mean() * 100)
    hl = pairs[pairs["headline"]]
    ctx["memory"] = {normalize_well_name(r.well): float((1 - r.beta_3) ** RANWELL_MEMORY_MONTHS) for r in hl.itertuples()}
    # on-site rain (Parc Mawr) in place of RAF Valley where both exist
    pm = pd.read_csv(RANWELL_PARC_MAWR_RAIN)
    pm.index = pd.to_datetime(dict(year=pm["year"], month=pm["month"], day=1))
    clp = clh.copy()
    common = clp.index.intersection(pm.index)
    clp.loc[common, "P_m"] = pm.loc[common, "rain_mm"].values / 1000.0
    loc_rain, swing = [], []
    for pr in pairs.itertuples():
        s = int(pr.site_no)
        om = obs_month.loc[s]
        betas = (float(pr.beta_1), float(pr.beta_2), float(pr.beta_3))
        loc_rain.append(_e11_score(om, clp, betas, (1, 1, 1), first, last, float(pr.ground_m_od))["nse_after_offset"])
        if pr.headline:
            col = lev_cols.get(normalize_well_name(pr.well))
            hobs = lev[col].dropna().clip(upper=0.0) if col is not None else pd.Series(dtype=float)
            if len(hobs):
                h0 = equilibrium_depth(betas, float(clh["P_m"].mean()), float(clh["PET"].mean()), drainage_datum=DRAINAGE_DATUM)
                sim, _ = hindcast_well(clh, betas, h0, hobs.index.min(), hobs.index.max(), 1.0, drainage_datum=DRAINAGE_DATUM)
                sim = sim.clip(upper=0.0).reindex(hobs.index)
                m = _e11_score(om, clh, betas, (1, 1, 1), first, last, float(pr.ground_m_od))
                o, pa = _offset_model(om, m["mid"], float(pr.ground_m_od))
                swing.append(dict(well=normalize_well_name(pr.well), site_no=s, modern=float(hobs.std() / sim.std()),
                                  epoch=float(o.std() / pa.std()), n_modern=int(sim.notna().sum()), n_epoch=int(len(o))))
    ctx["local_rain_nse"] = float(np.nanmedian(loc_rain))
    ctx["local_rain_n_better"] = int(sum(1 for a, b in zip(loc_rain, pairs["nse_after_offset"]) if a > b))
    ctx["n_pairs"] = len(loc_rain)
    ctx["swing"] = swing
    # candidates from the literature, sized at the ends of their range (single coefficient, others 1)
    cand = pd.read_csv(RANWELL_EPOCH_CANDIDATES)
    hbar = float(np.nanmedian([lev[lev_cols[normalize_well_name(w)]].mean() for w in hl["well"]
                               if normalize_well_name(w) in lev_cols]))
    idx = {"beta_1": 0, "beta_2": 1, "beta_3": 2}
    for cd in cand.itertuples():
        ks = []
        if pd.notna(cd.k_low):
            ks = [float(cd.k_low), float(cd.k_high)]
        elif pd.notna(cd.base_shift_m_low):
            # a deeper base: beta_3 scales roughly as 1/(z0 + mean h) on the plateau (Paper M Section 2.2)
            ks = [(DRAINAGE_DATUM + hbar) / (DRAINAGE_DATUM + float(sh) + hbar)
                  for sh in (cd.base_shift_m_low, cd.base_shift_m_high)]
        need_k = need["joint"]["k" + str(idx[cd.coefficient] + 1)]   # the need is the jointly best cell
        need_dir = "up" if need_k > 1 else "down" if need_k < 1 else "none"
        nse = []
        for kv in ks:
            vals = []
            for pr in pairs.itertuples():
                kk = [1.0, 1.0, 1.0]
                kk[idx[cd.coefficient]] = kv
                vals.append(_e11_score(obs_month.loc[int(pr.site_no)], clh, (float(pr.beta_1), float(pr.beta_2),
                                       float(pr.beta_3)), tuple(kk), first, last, float(pr.ground_m_od))["nse_after_offset"])
            nse.append(float(np.nanmedian(vals)))
        rows.append(dict(item=cd.candidate, kind="literature", coefficient=cd.coefficient, direction=cd.direction,
                         k_low=ks[0] if ks else np.nan, k_high=ks[1] if ks else np.nan, need_k=need_k,
                         direction_matches_need=bool(cd.direction == need_dir),
                         nse_at_k_low=nse[0] if nse else np.nan, nse_at_k_high=nse[1] if nse else np.nan,
                         nse_base=need["nse_base"], evidence=cd.evidence, source=cd.source))
    # the forest planted since: today's coefficients near it carry its drawdown, which 1951-53 lacked. Sized from the
    # open-ground wells (clusters outside FOREST_FORCING_CLUSTERS, not under canopy): the median of each coefficient
    # beyond the drawdown reach (drawdown_lambda, Script 20) over its median within it, applied to the pairs within it
    import json
    from shapely.geometry import Point, shape
    from shapely.ops import unary_union
    forest = unary_union([shape(f["geometry"]) for f in json.load(open(DATA_FOREST_BOUNDARY))["features"]])
    lam = float(pd.read_csv(OUT_20_REPORT_NUMBERS).set_index("Parameter").loc["drawdown_lambda", "Value"])
    loc = pd.read_csv(INT_LOCATIONS)
    loc["_n"] = loc["Name"].astype(str).apply(normalize_well_name)
    dist = loc.drop_duplicates("_n").set_index("_n").apply(lambda r: forest.distance(Point(r["E"], r["N"])), axis=1)
    md = _model_a_store(pd.read_csv(INT_MASTER_DATA))
    md["_n"] = md["Name_Original"].astype(str).apply(normalize_well_name)
    md["d"] = md["_n"].map(dist)
    op = md[~md["Cluster"].isin(FOREST_FORCING_CLUSTERS) & (md["d"] > 0)]
    near, far = op[op["d"] <= lam], op[op["d"] > lam]
    kf = tuple(float(far[c].median() / near[c].median())
               for c in ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage"))
    within = [pr for pr in pairs.itertuples() if dist.get(normalize_well_name(pr.well), np.inf) <= lam]
    vals = []
    for pr in pairs.itertuples():
        kk = kf if (int(pr.site_no), pr.well) in {(int(w.site_no), w.well) for w in within} else (1.0, 1.0, 1.0)
        vals.append(_e11_score(obs_month.loc[int(pr.site_no)], clh, (float(pr.beta_1), float(pr.beta_2), float(pr.beta_3)),
                               kk, first, last, float(pr.ground_m_od))["nse_after_offset"])
    need_dirs = [need["joint"][k] for k in ("k1", "k2", "k3")]
    ctx["forest"] = dict(lam=lam, k=kf, n_near=len(near), n_far=len(far), n_pairs_within=len(within),
                         sites_within=sorted({int(pr.site_no) for pr in within}),
                         dist_min=float(min(dist.get(normalize_well_name(pr.well)) for pr in pairs.itertuples())),
                         nse=float(np.nanmedian(vals)), shift_pct_max=float(max(abs(1 - x) for x in kf) * 100))
    rows.append(dict(item="modern_forest", kind="measured", coefficient="beta_1, beta_2, beta_3",
                     direction="/".join("up" if x > 1 else "down" for x in kf), k_low=min(kf), k_high=max(kf),
                     need_k=np.nan, direction_matches_need=all((x > 1) == (n > 1) for x, n in zip(kf, need_dirs)),
                     nse_at_k_low=ctx["forest"]["nse"], nse_at_k_high=np.nan, nse_base=need["nse_base"],
                     evidence=(f"open-ground wells beyond the forest's drawdown reach ({len(far)}) against those within it "
                               f"({len(near)}): beta_1 x{kf[0]:.3f}, beta_2 x{kf[1]:.3f}, beta_3 x{kf[2]:.3f}, applied to the "
                               f"{len(within)} pairs within the reach (sites {sorted({int(pr.site_no) for pr in within})})"),
                     source="data/geo/forest_boundary.geojson; 03_master_data.csv; drawdown_lambda (Script 20)"))
    rows.append(dict(item="on_site_rain", kind="measured", coefficient="P", direction="", k_low=np.nan, k_high=np.nan,
                     need_k=np.nan, direction_matches_need=bool(ctx["local_rain_nse"] > need["nse_base"]),
                     nse_at_k_low=ctx["local_rain_nse"], nse_at_k_high=np.nan, nse_base=need["nse_base"],
                     evidence="Parc Mawr monthly rain in place of RAF Valley's", source="Ranwell (1959) Fig. 2"))
    rows.append(dict(item="pipe_foot", kind="measured", coefficient="", direction="", k_low=np.nan, k_high=np.nan,
                     need_k=np.nan, direction_matches_need=bool(need["nse_pipe_foot"] > need["nse_base"] + RANWELL_NEED_NSE_TOL),
                     nse_at_k_low=need["nse_pipe_foot"], nse_at_k_high=np.nan, nse_base=need["nse_base"],
                     evidence="model capped at the pipe's foot (RANWELL_PIPE_FOOT_M, or the deepest reading)",
                     source="data/RANWELL_PROVENANCE.md"))
    return pd.DataFrame(rows), ctx


def ranwell_epoch_report(rr, need: dict, ctx: dict, cand: pd.DataFrame, chk: float) -> None:
    N = "E11, exploration not a test (D-261)"
    rr.add("ranwell_need_n_pairs", need["n_pairs"], unit="pairs", note=f"Script 44 site-well pairings scored ({N})")
    rr.add("ranwell_need_nse_base_median", need["nse_base"], unit="", note=f"median NSE after offset, coefficients as fitted ({N})")
    rr.add("ranwell_need_identity_max_abs_dnse", chk, unit="", note="identity: k = 1 against Script 44's NSE, every pair")
    for k, lab in (("k1", "recharge beta_1"), ("k2", "atmospheric draw beta_2"), ("k3", "drainage beta_3")):
        rr.add(f"ranwell_need_single_{k}", need["single"][k]["k"], unit="x",
               note=f"best scale of {lab} alone (others unchanged), by median NSE ({N})")
        rr.add(f"ranwell_need_single_{k}_nse", need["single"][k]["nse"], unit="", note=f"median NSE at that scale ({N})")
        rr.add(f"ranwell_need_joint_{k}", need["joint"][k], unit="x", note=f"{lab} at the jointly best cell ({N})")
        rr.add(f"ranwell_need_near_{k}_min", need["near"][k][0], unit="x",
               note=f"{lab}: lowest scale among cells within RANWELL_NEED_NSE_TOL of the joint best ({N})")
        rr.add(f"ranwell_need_near_{k}_max", need["near"][k][1], unit="x",
               note=f"{lab}: highest scale among cells within RANWELL_NEED_NSE_TOL of the joint best ({N})")
    rr.add("ranwell_need_joint_nse", need["joint"]["nse"], unit="", note=f"median NSE at the jointly best cell ({N})")
    rr.add("ranwell_need_k3_pairs_faster", need["k3_pairs_faster"], unit="pairs", note="pairs whose best drainage scale alone is above 1")
    rr.add("ranwell_need_k3_pairs_slower", need["k3_pairs_slower"], unit="pairs", note="pairs whose best drainage scale alone is below 1")
    rr.add("ranwell_need_nse_pipe_foot", need["nse_pipe_foot"], unit="", note="median NSE with the model capped at the pipe's foot, coefficients as fitted")
    for k, v in ctx["season_pct"].items():
        rr.add(f"ranwell_epoch_season_pct_{k}", v, unit="%", note=f"1951-53 {k} against every RANWELL_SEASON_WINDOW_YEARS window of the climate record ({N})")
    rr.add("ranwell_epoch_season_pct_min", min(ctx["season_pct"].values()), unit="%", note="lowest of the seasonal percentiles")
    rr.add("ranwell_epoch_season_pct_max", max(ctx["season_pct"].values()), unit="%", note="highest of the seasonal percentiles")
    rr.add("ranwell_epoch_antecedent_net_mm", ctx["antecedent_net_mm"], unit="mm", note="P - PET over the RANWELL_ANTECEDENT_YEARS before the readings")
    rr.add("ranwell_epoch_antecedent_pct", ctx["antecedent_pct"], unit="%", note="its percentile among all such windows")
    for w, v in ctx["memory"].items():
        rr.add(f"ranwell_epoch_memory_{w}", v, unit="", note=f"(1 - beta_3)^RANWELL_MEMORY_MONTHS at headline pair {w}")
    rr.add("ranwell_epoch_memory_min", min(ctx["memory"].values()), unit="", note="lowest share of a departure left after RANWELL_MEMORY_MONTHS")
    rr.add("ranwell_epoch_memory_max", max(ctx["memory"].values()), unit="", note="highest share of a departure left after RANWELL_MEMORY_MONTHS")
    rr.add("ranwell_epoch_local_rain_nse_median", ctx["local_rain_nse"], unit="", note="median NSE with Parc Mawr rain in place of RAF Valley's")
    rr.add("ranwell_epoch_local_rain_n_better", ctx["local_rain_n_better"], unit="pairs", note=f"pairs it improves (of {ctx['n_pairs']})")
    smaller = []
    for sw in ctx["swing"]:
        rr.add(f"ranwell_epoch_swing_ratio_modern_{sw['well']}", sw["modern"], unit="", note="SD observed / SD modelled, modern record")
        rr.add(f"ranwell_epoch_swing_ratio_epoch_{sw['well']}", sw["epoch"], unit="", note="SD observed / SD modelled, 1951-53")
        smaller.append((1 - sw["epoch"] / sw["modern"]) * 100)
    if smaller:
        rr.add("ranwell_epoch_swing_smaller_pct_min", min(smaller), unit="%", note="1951-53 swing relative to the model, smaller than today's by at least")
        rr.add("ranwell_epoch_swing_smaller_pct_max", max(smaller), unit="%", note="and by at most")
    f = ctx["forest"]
    for i, c in enumerate(("beta1", "beta2", "beta3")):
        rr.add(f"ranwell_epoch_forest_k_{c}", f["k"][i], unit="x",
               note="open-ground wells beyond the forest's drawdown reach over those within it, median coefficient")
    rr.add("ranwell_epoch_forest_shift_pct_max", f["shift_pct_max"], unit="%", note="largest of those differences")
    rr.add("ranwell_epoch_forest_n_pairs_within", f["n_pairs_within"], unit="pairs", note="pairs within the drawdown reach of today's forest")
    rr.add("ranwell_epoch_forest_n_sites_within", len(f["sites_within"]), unit="sites", note=f"Ranwell sites with a pair within it ({f['sites_within']})")
    rr.add("ranwell_epoch_forest_nse_median", f["nse"], unit="", note="median NSE with the forest's difference removed at the pairs within its reach")
    for r in cand.itertuples():
        for end in ("low", "high"):
            v = getattr(r, f"nse_at_k_{end}")
            if pd.notna(v):
                rr.add(f"ranwell_epoch_cand_{r.item}_nse_at_k_{end}", v, unit="", note=f"{r.item}: median NSE at the {end} end of its range")
            kv = getattr(r, f"k_{end}")
            if pd.notna(kv):
                rr.add(f"ranwell_epoch_cand_{r.item}_k_{end}", kv, unit="x", note=f"{r.item}: {r.coefficient} scale, {end} end")


# ──────────────────────────────────────────────────────────────────────────────
# E13 (1.13.0, D-273): does another evaporation estimate, or a recharge break, explain the 2006-08 excess?
# ──────────────────────────────────────────────────────────────────────────────
E13_PETS_RADIATION = ("Hargreaves", "Priestley-Taylor", "Makkink")


E13_PETS_PM = ("Penman-Monteith", "PM, wind at its mean", "PM, humidity at its mean")


E13_THORN = "Thornthwaite"


def _e13_window(years) -> tuple[str, str]:
    return f"{years[0]}-01-01", f"{years[1]}-12-01"


def _e13_inputs(cl: pd.DataFrame, master: pd.DataFrame):
    """The monthly climate from the first month after its last gap, the reference and extended wells,
    the member-well-mean centroid of each cluster (as the scratch run, Martin 2026-10-23), and the
    confirmed, uncensored CCW 1989-96 readings with their cluster."""
    c0 = continuous_start(cl)
    clim = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").loc[c0:].dropna()
    W = pd.concat([pd.read_csv(INT_WELLS_REFERENCE, index_col=0, parse_dates=True),
                   pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)], axis=1)
    W.columns = [normalize_well_name(x) for x in W.columns]
    md = master.set_index("_n")
    cent = {int(k): W[[w for w in md.index[md["Cluster"] == k] if w in W]].mean(axis=1)
            for k in sorted(md["Cluster"].unique())}
    ccw = pd.DataFrame()
    if paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists():
        obs, cmap = load_ccw()
        cmap = cmap[cmap["status"] == "confirmed"][["code", "well"]]
        ccw = obs.merge(cmap, on="code")
        ccw = ccw[~ccw["censored_at_pipe_base"]].copy()
        ccw["well"] = ccw["well"].apply(normalize_well_name)
        ccw = ccw[ccw["well"].isin(md.index)]
        ccw["Cluster"] = ccw["well"].map(md["Cluster"]).astype(int)
    return clim, W, cent, ccw


def _e13_run(h: pd.Series, clim: pd.DataFrame, pet: pd.Series, intercept: bool, fit_before=None):
    """Model A or B fitted on h (before `fit_before` if given) with `pet`, free-run over the whole climate
    span from the record's mean level. Returns (fit, run) or (None, None)."""
    c = pd.DataFrame({"P_m": clim["P_m"], "PET": pet})
    hf = h if fit_before is None else h[h.index < pd.Timestamp(fit_before)]
    f = fit_ssm(hf, c, intercept=intercept, start=None)   # D-347 (5): E13's subject is the 2006-08 excess
    if f is None:
        return None, None
    s = pd.Series(simulate_ssm(h.dropna().mean(), c["P_m"].values, c["PET"].values, f["beta_1_recharge"],
                               f["beta_2_atmospheric_draw"], f["beta_3_drainage"],
                               alpha=f.get("alpha", 0.0) if intercept else 0.0), index=c.index)
    return f, s


def _e13_excess(h: pd.Series, s: pd.Series) -> float:
    """Mean residual over TWO_STORE_EARLY_YEARS minus the mean residual over E8E_LATER_YEARS."""
    r = (h - s).dropna()
    e, l_ = _e13_window(TWO_STORE_EARLY_YEARS), _e13_window(E8E_LATER_YEARS)
    return float(r.loc[e[0]:e[1]].mean() - r.loc[l_[0]:l_[1]].mean())


def _e13_table(cent: dict, clim: pd.DataFrame, pets: dict, ccw: pd.DataFrame, set_name: str) -> pd.DataFrame:
    """Every cluster x form x PET series: the coefficients, the excess, the forward RMSE, the CCW bias, and each
    against Thornthwaite on the same span; the rule per row."""
    rows = []
    for k, h in cent.items():
        h = h.loc[:clim.index[-1]]
        for form, icpt in FORMS:
            for name, pet in pets.items():
                f, s = _e13_run(h, clim, pet, icpt)
                if f is None:
                    continue
                _, sf = _e13_run(h, clim, pet, icpt, fit_before=MODEL_AB_SPLIT_DATE)
                oos = (h - sf).loc[MODEL_AB_SPLIT_DATE:].dropna()
                cw = ccw[ccw["Cluster"] == k] if len(ccw) else ccw
                bias = (float(np.mean([s.get(t, np.nan) - v for t, v in zip(cw["month"], cw["depth_m_bg"])]))
                        if len(cw) else np.nan)
                rows.append(dict(set=set_name, cluster=f"C{k}", form=form, pet=name, beta_1=f["beta_1_recharge"],
                                 beta_2=f["beta_2_atmospheric_draw"], beta_3=f["beta_3_drainage"], R2=f["R2"],
                                 excess_m=_e13_excess(h, s), fwd_rmse_m=float(np.sqrt((oos ** 2).mean())),
                                 ccw_n=len(cw), ccw_bias_m=bias, span_start=clim.index[0].strftime("%Y-%m"),
                                 span_end=clim.index[-1].strftime("%Y-%m")))
    t = pd.DataFrame(rows)
    base = t[t["pet"] == E13_THORN].set_index(["cluster", "form"])
    key = list(zip(t["cluster"], t["form"]))
    t["excess_share_removed"] = [1 - x / base.loc[k_, "excess_m"] for x, k_ in zip(t["excess_m"], key)]
    t["fwd_rmse_change"] = [x / base.loc[k_, "fwd_rmse_m"] - 1 for x, k_ in zip(t["fwd_rmse_m"], key)]
    t["ccw_abs_bias_change_m"] = [abs(x) - abs(base.loc[k_, "ccw_bias_m"]) for x, k_ in zip(t["ccw_bias_m"], key)]
    # a fit with beta_3 <= 0 has no restoring drainage: its free run drifts without bound, so it is flagged and
    # never read (the recursion's own stability condition, not a threshold)
    t["stable"] = t["beta_3"] > 0
    t["passes"] = (t["stable"] & (t["excess_share_removed"] >= E13_EXCESS_SHARE)
                   & (t["fwd_rmse_change"] <= E13_RMSE_TOL) & ~(t["ccw_abs_bias_change_m"] > 0))
    return t


def e13_verdict(tab: pd.DataFrame, pet: str) -> str:
    """The rule (fixed before the run): Model A, every cluster in E13_CLUSTERS."""
    s = tab[(tab["pet"] == pet) & (tab["form"] == "A") & tab["cluster"].isin([f"C{c}" for c in E13_CLUSTERS])]
    if len(s) and s["passes"].all():
        return "explains"
    if s["passes"].any():
        return "partial: " + ",".join(s[s["passes"]]["cluster"])
    return "not supported"


def e13_evaporation(cl: pd.DataFrame, master: pd.DataFrame):
    """E13 parts 1 and 3: radiation-based PET on the full climate span; Penman-Monteith and its two
    decomposition runs on the MIDAS span, with Thornthwaite re-run there as the baseline."""
    clim, W, cent, ccw = _e13_inputs(cl, master)
    alt = monthly_radiation_pet(clim.index, RAF_VALLEY_LAT_DEG)
    if alt.isna().any().any():
        raise RuntimeError(f"E13: radiation-based PET has gaps after filling: {alt.isna().sum().to_dict()}")
    pets = {E13_THORN: clim["PET"]}
    scaled_max = 0.0
    for k in E13_PETS_RADIATION:
        pets[k] = alt[k]
    rad = _e13_table(cent, clim, pets, ccw, "radiation")
    # identity: rescaling a series to Thornthwaite's long-term mean changes only beta_2, not the run
    for k in E13_PETS_RADIATION:
        sc = alt[k] * clim["PET"].mean() / alt[k].mean()
        for c_ in E13_CLUSTERS:
            for _, icpt in FORMS:
                h = cent[c_]
                _, s1 = _e13_run(h, clim, alt[k], icpt)
                _, s2 = _e13_run(h, clim, sc, icpt)
                if s1 is not None and s2 is not None:
                    scaled_max = max(scaled_max, float((s1 - s2).abs().max()))
    a, b = midas_span(MIDAS_WEATHER_DIR)
    cm = clim.loc[a:b]
    mon, n_filled = midas_monthly_pm(MIDAS_WEATHER_DIR, RAF_VALLEY_LAT_DEG, cm["PET"])
    pm_pets = {E13_THORN: mon["thornthwaite"], "Penman-Monteith": mon["pm"],
               "PM, wind at its mean": mon["pm_wind_clim"], "PM, humidity at its mean": mon["pm_hum_clim"]}
    cent_pm = {k: h.loc[:b] for k, h in cent.items()}
    pm = _e13_table(cent_pm, cm, pm_pets, ccw, "penman-monteith")
    e, l_ = _e13_window(TWO_STORE_EARLY_YEARS), _e13_window(E8E_LATER_YEARS)

    def mean(s, w):
        return float(s.loc[w[0]:w[1]].mean())
    wx = dict(u2_early_ms=mean(mon["u2_ms"], e), u2_later_ms=mean(mon["u2_ms"], l_),
              ea_early_kpa=mean(mon["ea_kpa"], e), ea_later_kpa=mean(mon["ea_kpa"], l_),
              pm_early_mm_yr=12 * 1000 * mean(mon["pm"], e), pm_later_mm_yr=12 * 1000 * mean(mon["pm"], l_),
              th_early_mm_yr=12 * 1000 * mean(mon["thornthwaite"], e),
              th_later_mm_yr=12 * 1000 * mean(mon["thornthwaite"], l_))
    wx["pm_minus_th_shift_mm_yr"] = ((wx["pm_early_mm_yr"] - wx["th_early_mm_yr"])
                                     - (wx["pm_later_mm_yr"] - wx["th_later_mm_yr"]))
    an = mon["u2_ms"] - mon["u2_ms"].groupby(mon.index.month).transform("mean")
    for c_ in E13_CLUSTERS:
        _, s = _e13_run(cent_pm[c_], cm, mon["thornthwaite"], False)
        r = (cent_pm[c_] - s).diff().dropna()
        j = r.index.intersection(an.dropna().index)
        wx[f"wind_resid_corr_C{c_}"] = float(np.corrcoef(an[j], r[j])[0, 1])
    wx["pm_months_filled"] = n_filled
    wx["pm_months"] = len(mon)
    wx["scaled_identity_max_m"] = scaled_max
    monthly = pd.concat([pd.DataFrame({"P_m": clim["P_m"], "thornthwaite": clim["PET"]}), alt,
                         mon.drop(columns="thornthwaite").add_prefix("midas_")], axis=1)
    monthly.index.name = "month"
    return rad, pm, wx, monthly, (clim, W)


def e13_break(clim: pd.DataFrame, W: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    """E13 part 2: per well, Model A with beta_1 allowed to differ before a break month profiled over
    E13_BREAK_WINDOW (least squares), run against the same without the break."""
    e, l_ = _e13_window(TWO_STORE_EARLY_YEARS), _e13_window(E8E_LATER_YEARS)
    md = master.set_index("_n")
    grid = pd.date_range(E13_BREAK_WINDOW[0], E13_BREAK_WINDOW[1], freq="MS")
    wells = [w for w in W if W[w].loc[e[0]:e[1]].notna().sum() >= E8E_MIN_EARLY_MONTHS
             and W[w].loc[l_[0]:l_[1]].notna().sum() >= E13_MIN_LATER_MONTHS]
    P, E = clim["P_m"].values, clim["PET"].values
    rows = []
    for w in wells:
        h = W[w].loc[:clim.index[-1]]
        idx = build_ssm_frame(h, clim).index
        f0, s0 = _e13_run(h, clim, clim["PET"], False)
        best = None
        for b in grid:
            x = (clim["P_m"].reindex(idx) * (idx < b)).values
            f = fit_ssm(h, clim, extra_regressors={"d_beta1_pre": x}, start=None)   # D-347 (5): a break in 2006-08
            if f is None:
                continue
            sse = float((np.asarray(f["resid"]) ** 2).sum())
            if best is None or sse < best[0]:
                best = (sse, b, f)
        if best is None or s0 is None:
            continue
        _, b, f = best
        b1pre = f["beta_1_recharge"] + f["d_beta1_pre"]
        pre = clim.index < b
        ht = h.dropna().mean()
        sim = []
        for t in range(len(clim)):
            b1 = b1pre if pre[t] else f["beta_1_recharge"]
            ht = ht + b1 * P[t] - f["beta_2_atmospheric_draw"] * E[t] - f["beta_3_drainage"] * (DRAINAGE_DATUM + ht)
            sim.append(ht)
        s1 = pd.Series(sim, index=clim.index)
        e0, e1 = _e13_excess(h, s0), _e13_excess(h, s1)
        se = f["se_d_beta1_pre"]
        rows.append(dict(well=w, cluster=int(md["Cluster"][w]) if w in md.index else np.nan,
                         break_month=b.strftime("%Y-%m"), beta_3_no_break=f0["beta_3_drainage"],
                         beta_3=f["beta_3_drainage"], stable=bool(f0["beta_3_drainage"] > 0 and f["beta_3_drainage"] > 0),
                         beta_1_after=f["beta_1_recharge"],
                         d_beta_1_before=f["d_beta1_pre"], ci_lo=f["d_beta1_pre"] - 1.96 * se,
                         ci_hi=f["d_beta1_pre"] + 1.96 * se, excess_no_break_m=e0, excess_with_break_m=e1,
                         share_removed=(1 - e1 / e0) if e0 else np.nan))
    return pd.DataFrame(rows)


def e13_break_verdict(br: pd.DataFrame) -> dict:
    """Stable fits only (beta_3 > 0 with and without the break): an unstable free run carries no excess to share."""
    ok = br[br["stable"]]
    n, pos = len(ok), int((ok["ci_lo"] > 0).sum())
    med = float(ok["share_removed"].median()) if n else np.nan
    return dict(n=n, n_dropped=len(br) - n, n_higher_before=int((ok["d_beta_1_before"] > 0).sum()), n_resolved=pos,
                resolved=sorted(ok[ok["ci_lo"] > 0]["well"]), median_share=med,
                median_d_beta_1=float(ok["d_beta_1_before"].median()) if n else np.nan,
                median_rel_d_beta_1=float((ok["d_beta_1_before"] / ok["beta_1_after"]).median()) if n else np.nan,
                verdict="supported" if (pos > n / 2 and med >= E13_EXCESS_SHARE) else "not supported")


def e13_report(rr, rad, pm, br_v, wx) -> None:
    for tab, pets in ((rad, E13_PETS_RADIATION), (pm, E13_PETS_PM[:1])):
        for p_ in pets:
            k = p_.lower().replace("-", "_").replace(" ", "_")
            rr.add(f"e13_verdict_{k}", e13_verdict(tab, p_), unit="text",
                   note=f"E13 {p_}: the rule at {', '.join(f'C{c}' for c in E13_CLUSTERS)}, Model A (D-273)")
    for tab, pets in ((rad, E13_PETS_RADIATION), (pm, E13_PETS_PM)):
        for r in tab[(tab["form"] == "A") & tab["pet"].isin(pets)
                     & tab["cluster"].isin([f"C{c}" for c in E13_CLUSTERS])].itertuples():
            k = r.pet.lower().replace("-", "_").replace(",", "").replace(" ", "_")
            rr.add(f"e13_share_removed_{k}_{r.cluster}", r.excess_share_removed, unit="fraction",
                   note=f"E13 {r.pet}, Model A, {r.cluster}: share of the 2006-08 excess removed (D-273)")
            rr.add(f"e13_fwd_rmse_change_{k}_{r.cluster}", r.fwd_rmse_change, unit="fraction",
                   note=f"E13 {r.pet}, Model A, {r.cluster}: change in forward RMSE against Thornthwaite (D-273)")
    for tab, s in ((rad, "full"), (pm, "midas")):
        for r in tab[(tab["form"] == "A") & (tab["pet"] == E13_THORN)
                     & tab["cluster"].isin([f"C{c}" for c in E13_CLUSTERS])].itertuples():
            rr.add(f"e13_excess_thornthwaite_{s}_{r.cluster}", r.excess_m,
                   note=f"E13: the Thornthwaite 2006-08 excess, Model A, {r.cluster}, {r.span_start} to {r.span_end} (D-273)")
    rr.add("e13_break_verdict", br_v["verdict"], unit="text", note="E13: the beta_1 break, by the rule (D-273)")
    for k in ("n", "n_dropped", "n_higher_before", "n_resolved"):
        rr.add(f"e13_break_{k}", br_v[k], unit="wells", note=f"E13 beta_1 break: {k} (D-273)")
    rr.add("e13_break_resolved_wells", " ".join(w.upper() for w in br_v["resolved"]), unit="text",
           note="E13 beta_1 break: wells whose 95% interval excludes zero (D-273)")
    rr.add("e13_break_median_share", br_v["median_share"], unit="fraction",
           note="E13 beta_1 break: median share of the excess removed; high by construction (D-273)")
    rr.add("e13_break_median_d_beta_1", br_v["median_d_beta_1"], unit="",
           note="E13 beta_1 break: median rise in beta_1 before the break (D-273)")
    rr.add("e13_break_median_rel_d_beta_1", br_v["median_rel_d_beta_1"], unit="fraction",
           note="E13 beta_1 break: median rise in beta_1 before the break, relative to beta_1 after (D-273)")
    units = {"ms": "m/s", "kpa": "kPa", "mm_yr": "mm/yr"}
    for k, v in wx.items():
        u = next((uu for s, uu in units.items() if k.endswith(s)), "m" if k.endswith("_m") else "")
        rr.add(f"e13_{k}", v, unit=u or ("months" if "months" in k else "r"), note="E13 weather and identity (D-273)")


def plot_e13(rad, pm, br) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6), dpi=160, gridspec_kw={"width_ratios": [1.3, 1]})
    pets = list(E13_PETS_RADIATION) + list(E13_PETS_PM)
    both = pd.concat([rad, pm])
    both = both[both["pet"].isin(pets)]   # Thornthwaite is in both tables (each span's baseline)
    w = 0.8 / len(E13_CLUSTERS)
    for i, c in enumerate(E13_CLUSTERS):
        s = both[(both["form"] == "A") & (both["cluster"] == f"C{c}")].set_index("pet").reindex(pets)
        a1.bar(np.arange(len(pets)) + (i - (len(E13_CLUSTERS) - 1) / 2) * w, s["excess_share_removed"], w,
               color=CLUSTER_COLOURS.get(c, "0.5"), label=CLUSTER_LABELS.get(c, f"C{c}"))
    a1.axhline(E13_EXCESS_SHARE, color="k", lw=0.8, ls="--")
    a1.axhline(0, color="0.4", lw=0.6)
    a1.set_xticks(np.arange(len(pets)))
    a1.set_xticklabels(pets, rotation=30, ha="right", fontsize=7)
    a1.set_ylabel("share of the 2006-08 excess removed (Model A)")
    a1.set_title("E13: other evaporation estimates. Dashed: the rule's bar", loc="left", fontsize=8)
    a1.legend(fontsize=7)
    a1.grid(alpha=0.3, axis="y")
    b = br[br["stable"].astype(bool)].sort_values("d_beta_1_before").reset_index(drop=True)
    res = b["ci_lo"] > 0
    a2.errorbar(b["d_beta_1_before"], np.arange(len(b)), xerr=[b["d_beta_1_before"] - b["ci_lo"], b["ci_hi"] - b["d_beta_1_before"]],
                fmt="o", ms=3, color="0.4", ecolor="0.6", elinewidth=0.7)
    a2.plot(b["d_beta_1_before"][res], np.arange(len(b))[res], "o", ms=6, color="#b2182b")
    a2.set_yticks(np.arange(len(b)))
    a2.set_yticklabels([x.upper() for x in b["well"]], fontsize=6)
    a2.axvline(0, color="0.4", lw=0.6)
    a2.set_xlabel("change in beta_1 before the break (95%)")
    a2.set_title("E13: a beta_1 break, per stable well. Red: interval excludes zero", loc="left", fontsize=8)
    a2.grid(alpha=0.3, axis="x")
    fig.tight_layout()
    fig.savefig(OUT_50_E13_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_50_E13_FIG.name)


# ──────────────────────────────────────────────────────────────────────────────
# E13b (1.14.0, D-274): Penman-Monteith against Thornthwaite at Valley, and Script 24's residual seasonality under each
# ──────────────────────────────────────────────────────────────────────────────
E13B_SERIES = {"thornthwaite": "Thornthwaite", "midas_pm": "Penman-Monteith", "Hargreaves": "Hargreaves",
               "Priestley-Taylor": "Priestley-Taylor", "Makkink": "Makkink"}


def _complete_years(s: pd.Series) -> pd.Series:
    """Annual totals (mm) of the calendar years with all twelve months."""
    s = s.dropna()
    g = s.groupby(s.index.year)
    return (g.sum() * 1000)[g.size() == 12]


def e13b_comparison(mon: pd.DataFrame) -> pd.DataFrame:
    """Each PET series against Thornthwaite over the MIDAS span (`all`) and over the complete years in which every
    month has measured radiation (`measured`): annual mean and ratio, each calendar month's mean and ratio,
    correlations (monthly, monthly anomaly, annual), OLS trend, the first and last E13B_WINDOW_YEARS means and the
    elasticity to mean temperature over the same windows (as report section 5.3 computes it for Thornthwaite)."""
    from scipy.stats import linregress
    raf = read_raf_monthly()
    m = mon.dropna(subset=["midas_pm"]).copy()
    m["t_mean"] = ((raf["tx"] + raf["tn"]) / 2).reindex(m.index)
    meas = m["midas_rs_days_measured"] >= MIDAS_MONTH_MIN_DAYS
    yrs_meas = [y for y, g in meas.groupby(m.index.year) if len(g) == 12 and g.all()]
    rows = []

    def add(basis, pet, q, v, unit=""):
        rows.append(dict(basis=basis, pet=pet, quantity=q, value=float(v), unit=unit))

    for basis, sub in (("all", m), ("measured", m[m.index.year.isin(yrs_meas)])):
        add(basis, "", "first_year", sub.index.year.min(), "year")
        add(basis, "", "last_year", sub.index.year.max(), "year")
        th = sub["thornthwaite"]
        th_y = _complete_years(th)
        t_y = sub["t_mean"].groupby(sub.index.year).mean()[th_y.index]
        n = len(th_y)
        w = min(E13B_WINDOW_YEARS, n // 2)
        first, last = th_y.index[:w], th_y.index[-w:]
        dT = t_y[last].mean() / t_y[first].mean() - 1
        add(basis, "", "t_first_window_c", t_y[first].mean(), "C")
        add(basis, "", "t_last_window_c", t_y[last].mean(), "C")
        add(basis, "", "window_years", w, "years")
        for col, name in E13B_SERIES.items():
            s = sub[col]
            y = _complete_years(s)
            add(basis, name, "annual_mean_mm", y.mean(), "mm/yr")
            add(basis, name, "ratio_to_thornthwaite", y.mean() / th_y.mean(), "ratio")
            add(basis, name, "pct_diff_annual", 100 * (y.mean() / th_y.mean() - 1), "%")
            for lab, months in (("season_a", E13B_SEASON_A_MONTHS), ("season_b", E13B_SEASON_B_MONTHS)):
                ms = s.index.month.isin(months)
                add(basis, name, f"pct_diff_{lab}", 100 * (s[ms].sum() / th[ms].sum() - 1), "%")
            add(basis, name, "corr_monthly", s.corr(th), "r")
            an = s - s.groupby(s.index.month).transform("mean")
            an_t = th - th.groupby(th.index.month).transform("mean")
            add(basis, name, "corr_monthly_anomaly", an.corr(an_t), "r")
            add(basis, name, "corr_annual", y.corr(th_y), "r")
            r = linregress(y.index.values, y.values)
            add(basis, name, "trend_mm_per_decade", 10 * r.slope, "mm/decade")
            add(basis, name, "trend_p", r.pvalue, "p")
            add(basis, name, "first_window_mean_mm", y[first].mean(), "mm/yr")
            add(basis, name, "last_window_mean_mm", y[last].mean(), "mm/yr")
            dP = y[last].mean() / y[first].mean() - 1
            add(basis, name, "window_change_frac", dP, "fraction")
            add(basis, name, "elasticity_to_temperature", dP / dT, "ratio")
            clim = s.groupby(s.index.month).mean() * 1000
            clim_t = th.groupby(th.index.month).mean() * 1000
            for mo in range(1, 13):
                add(basis, name, f"month_{mo:02d}_mean_mm", clim[mo], "mm/month")
                add(basis, name, f"month_{mo:02d}_ratio", clim[mo] / clim_t[mo], "ratio")
    return pd.DataFrame(rows)


def e13b_annual_inputs(mon: pd.DataFrame) -> pd.DataFrame:
    """Per calendar year of the MIDAS span: mean wind at 2 m, vapour pressure, dew point and daily minimum
    temperature (and their difference), pressure, the days of each radiation source, and annual Thornthwaite and
    Penman-Monteith. Shows where the Penman-Monteith inputs are not homogeneous (instrument changes), which bears on
    reading any trend in it."""
    m = mon.dropna(subset=["midas_pm"])
    g = m.groupby(m.index.year)
    out = pd.DataFrame({"u2_ms": g["midas_u2_ms"].mean(), "ea_kpa": g["midas_ea_kpa"].mean(),
                        "td_c": g["midas_td_c"].mean(), "tn_c": g["midas_tn_c"].mean(), "p_kpa": g["midas_p_kpa"].mean(),
                        "rs_days_measured": g["midas_rs_days_measured"].sum(),
                        "rs_days_hourly_sunshine": g["midas_rs_days_hourly_sunshine"].sum(),
                        "rs_days_monthly_sunshine": g["midas_rs_days_monthly_sunshine"].sum(),
                        "months": g.size(),
                        "thornthwaite_mm": g["thornthwaite"].sum() * 1000, "penman_monteith_mm": g["midas_pm"].sum() * 1000})
    out["td_minus_tn_c"] = out["td_c"] - out["tn_c"]
    out.index.name = "year"
    return out


def _sinusoid(mm: pd.Series):
    """Script 24's sinusoid on twelve monthly means: amplitude and phase month (identical arithmetic)."""
    mo = np.arange(1, 13)
    y = mm.values
    ok = np.isfinite(y)
    if ok.sum() < 8:
        return np.nan, np.nan
    X = np.column_stack([np.ones(12), np.cos(2 * np.pi * mo / 12), np.sin(2 * np.pi * mo / 12)])
    c = np.linalg.lstsq(X[ok], y[ok], rcond=None)[0]
    ph = (np.arctan2(c[2], c[1]) / (2 * np.pi) * 12) % 12
    return float(np.hypot(c[1], c[2])), float(12.0 if ph == 0 else ph)


def _resid_row(resid: pd.Series) -> dict:
    mm = resid.groupby(resid.index.month).mean().reindex(range(1, 13))
    amp, ph = _sinusoid(mm)
    return dict(summer_minus_winter=float(mm.reindex(list(E13B_RESID_SUMMER_MONTHS)).mean()
                                          - mm.reindex(list(E13B_RESID_WINTER_MONTHS)).mean()),
                amplitude=amp, phase_month=ph, resid_rmse=float(np.sqrt((resid ** 2).mean())), n_obs=len(resid))


def e13b_residual_seasonality(lev: pd.DataFrame, lev_cols: dict, cl: pd.DataFrame, pm: pd.Series):
    """Script 24's test (Model B per well, its well set from its committed table, its minimum record), with
    Thornthwaite on the full record (identity against 24_residual_climatology.csv), and with Thornthwaite and
    Penman-Monteith on the MIDAS span. Returns (rows, identity max |difference|)."""
    ref = pd.read_csv(INT_24_CLIMATOLOGY_TABLE)
    clim_full = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce")
    end = pm.index[-1]
    runs = {"thornthwaite_full": clim_full,
            "thornthwaite": clim_full.loc[:end],
            "penman_monteith": pd.DataFrame({"P_m": clim_full["P_m"], "PET": pm}).dropna()}
    rows, ident = [], 0.0
    for r in ref.itertuples():
        col = lev_cols.get(r.Well_Normalized)
        if col is None:
            continue
        for name, c in runs.items():
            h = lev[col] if name == "thornthwaite_full" else lev[col].loc[:end]
            f = fit_ssm_intercept(h, c, min_obs=RESIDUAL_DIAG_MIN_MONTHS)
            if f is None:
                continue
            row = _resid_row(f["resid"])
            rows.append(dict(well=r.Well_Normalized, cluster=r.Cluster, pet=name, **row))
            if name == "thornthwaite_full":
                ident = max(ident, abs(row["amplitude"] - r.amplitude),
                            abs(row["summer_minus_winter"] - r.summer_minus_winter))
    return pd.DataFrame(rows), ident


def e13b_resid_summary(rs: pd.DataFrame) -> dict:
    """Per cluster and PET: n, mean summer-minus-winter, its sign-rank p, median amplitude and RMSE; the rule:
    PM resolves the seasonality if, against Thornthwaite on the same span, it lowers the median amplitude, leaves no
    cluster whose summer-minus-winter contrast is significant at SIG_P where Thornthwaite's is, and does not raise
    the median residual RMSE."""
    from scipy.stats import wilcoxon
    out = {"clusters": {}}
    for (c, pet), g in rs.groupby(["cluster", "pet"]):
        x = g["summer_minus_winter"].dropna()
        p = float(wilcoxon(x).pvalue) if len(x) >= 5 else np.nan
        out["clusters"][(int(c), pet)] = dict(n=len(g), smw_mean=float(x.mean()), smw_p=p,
                                              amp_median=float(g["amplitude"].median()),
                                              rmse_median=float(g["resid_rmse"].median()))
    w = rs.pivot_table(index="well", columns="pet", values=["amplitude", "resid_rmse", "phase_month"])
    both = w.dropna(subset=[("amplitude", "thornthwaite"), ("amplitude", "penman_monteith")])
    out["n_wells"] = len(both)
    out["amp_ratio_median"] = float((both[("amplitude", "penman_monteith")] / both[("amplitude", "thornthwaite")]).median())
    out["n_amp_lower"] = int((both[("amplitude", "penman_monteith")] < both[("amplitude", "thornthwaite")]).sum())
    out["n_rmse_lower"] = int((both[("resid_rmse", "penman_monteith")] < both[("resid_rmse", "thornthwaite")]).sum())
    for pet in ("thornthwaite", "penman_monteith"):
        ph = both[("phase_month", pet)]
        out[f"n_phase_winter_{pet}"] = int(((ph >= E13B_RESID_WINTER_PHASE[0]) | (ph <= E13B_RESID_WINTER_PHASE[1])).sum())
    sig = {pet: {c for (c, p_), v in out["clusters"].items() if p_ == pet and v["smw_p"] < SIG_P}
           for pet in ("thornthwaite", "penman_monteith")}
    out["sig_thornthwaite"], out["sig_penman_monteith"] = sorted(sig["thornthwaite"]), sorted(sig["penman_monteith"])
    amp_lower = (rs[rs.pet == "penman_monteith"]["amplitude"].median() < rs[rs.pet == "thornthwaite"]["amplitude"].median())
    rmse_ok = (rs[rs.pet == "penman_monteith"]["resid_rmse"].median() <= rs[rs.pet == "thornthwaite"]["resid_rmse"].median())
    sig_ok = not (sig["thornthwaite"] & sig["penman_monteith"])
    out["verdict"] = "resolves" if (amp_lower and rmse_ok and sig_ok) else "does not resolve"
    return out


def e13b_report(rr, cmp_: pd.DataFrame, rsum: dict, ident: float) -> None:
    keep = ("annual_mean_mm", "ratio_to_thornthwaite", "pct_diff_annual", "pct_diff_season_a", "pct_diff_season_b", "corr_monthly", "corr_monthly_anomaly", "corr_annual",
            "trend_mm_per_decade", "trend_p", "first_window_mean_mm", "last_window_mean_mm", "elasticity_to_temperature")
    for r in cmp_.itertuples():
        if r.pet == "":
            rr.add(f"e13b_{r.basis}_{r.quantity}", r.value, unit=r.unit, note=f"E13b span ({r.basis}) (D-274)")
        elif r.pet in ("Thornthwaite", "Penman-Monteith") and (r.quantity in keep or r.quantity.startswith("month_")):
            k = "pm" if r.pet == "Penman-Monteith" else "th"
            rr.add(f"e13b_{r.basis}_{k}_{r.quantity}", r.value, unit=r.unit,
                   note=f"E13b {r.pet}, {r.basis} years: {r.quantity} (D-274)")
    rr.add("e13b_resid_verdict", rsum["verdict"], unit="text",
           note="E13b: does Penman-Monteith resolve Script 24's residual seasonality? The rule (D-274)")
    for k in ("n_wells", "amp_ratio_median", "n_amp_lower", "n_rmse_lower", "n_phase_winter_thornthwaite",
              "n_phase_winter_penman_monteith"):
        rr.add(f"e13b_resid_{k}", rsum[k], unit="ratio" if "ratio" in k else "wells", note="E13b residual seasonality (D-274)")
    for (c, pet), v in rsum["clusters"].items():
        for q, u in (("smw_mean", "m"), ("smw_p", "p"), ("amp_median", "m"), ("rmse_median", "m")):
            rr.add(f"e13b_resid_{pet}_C{c}_{q}", v[q], unit=u, note=f"E13b residual seasonality, C{c}, {pet} (D-274)")
    rr.add("e13b_resid_identity_vs24_max", ident, unit="m",
           note="E13b identity: Thornthwaite, full record, against 24_residual_climatology.csv (D-274)")


def plot_e13b(mon: pd.DataFrame, rs: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    m = mon.dropna(subset=["midas_pm"])
    fig, ax = plt.subplots(2, 2, figsize=(11, 8), dpi=160)
    cols = {"thornthwaite": ("Thornthwaite", "#b2182b"), "midas_pm": ("Penman-Monteith (FAO-56)", "#2166ac")}
    a = ax[0, 0]
    for c, (lab, col) in cols.items():
        a.plot(range(1, 13), m[c].groupby(m.index.month).mean() * 1000, "o-", color=col, label=lab)
    a.set_xticks(range(1, 13))
    a.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    a.set_ylabel("mean monthly PET (mm)")
    a.set_title(f"(a) Valley, {m.index.year.min()}-{m.index.year.max()}: the mean year", loc="left", fontsize=8)
    a.legend(fontsize=7)
    a = ax[0, 1]
    for c, (lab, col) in cols.items():
        y = _complete_years(m[c])
        a.plot(y.index, y.values, color=col, lw=0.9, label=lab)
        k = np.polyfit(y.index.values, y.values, 1)
        a.plot(y.index, np.polyval(k, y.index.values), color=col, lw=0.8, ls="--")
    meas = m["midas_rs_days_measured"] >= MIDAS_MONTH_MIN_DAYS
    y_meas = [y_ for y_, g_ in meas.groupby(m.index.year) if g_.all()]
    if y_meas:
        a.axvspan(m.index.year.min(), min(y_meas), color="0.9", zorder=0)
    a.set_ylabel("annual PET (mm)")
    a.set_title("(b) annual totals, OLS trends dashed. Shaded: before measured radiation, wind and dew point not "
                "homogeneous", loc="left", fontsize=7)
    a = ax[1, 0]
    r = m["midas_pm"].groupby(m.index.month).mean() / m["thornthwaite"].groupby(m.index.month).mean()
    a.bar(range(1, 13), r.values, color="0.55")
    a.axhline(1, color="k", lw=0.7)
    a.set_xticks(range(1, 13))
    a.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    a.set_ylabel("Penman-Monteith / Thornthwaite")
    a.set_title("(c) the ratio, month by month", loc="left", fontsize=8)
    a = ax[1, 1]
    for pet, col, off in (("thornthwaite", "#b2182b", -0.15), ("penman_monteith", "#2166ac", 0.15)):
        s = rs[rs["pet"] == pet]
        for c in sorted(s["cluster"].dropna().unique()):
            v = s[s["cluster"] == c]["summer_minus_winter"] * 1000
            a.plot(np.full(len(v), c + off), v, "o", ms=3, color=col, alpha=0.5)
            a.plot([c + off - 0.1, c + off + 0.1], [v.mean()] * 2, color=col, lw=2)
    a.axhline(0, color="0.4", lw=0.6)
    a.set_xticks(sorted(rs["cluster"].dropna().unique()))
    a.set_xticklabels([CLUSTER_LABELS.get(int(c), f"C{int(c)}") for c in sorted(rs["cluster"].dropna().unique())],
                      rotation=20, ha="right", fontsize=7)
    a.set_ylabel("residual, summer minus winter (mm/month)")
    a.set_title("(d) Script 24's test, same span: red Thornthwaite, blue Penman-Monteith", loc="left", fontsize=8)
    for a in ax.flat:
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_50_E13B_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_50_E13B_FIG.name)


# ──────────────────────────────────────────────────────────────────────────────
# E19: does the FILM's correction transfer? (1.22.0, T-133, D-292)
# ──────────────────────────────────────────────────────────────────────────────
E19_ARMS = ("raw", "mapped", "offset")


def _script47():
    """Script 47 by path (numeric filename; the Script 30 precedent). Its functions build the film's run and map; E19
    reuses them unchanged so it tests what the film does, not a copy of it."""
    path = Path(__file__).resolve().parent / "47_hindcast_film.py"
    spec = importlib.util.spec_from_file_location("_s47", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _hydro_year(idx: pd.PeriodIndex) -> np.ndarray:
    """D-207's MSL hydrology year: bucketed months May to April, labelled by the April's year."""
    return np.where(idx.month <= 4, idx.year, idx.year + 1)


def e19_tests():
    """The film's run and map (Script 47, unchanged) against the median of the admitted CCW wells. Returns
    (months table, modern-calibration stats, composition check) or (empty, None, None) when inputs are absent."""
    if not (paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()):
        warn("CCW historic inputs not present — E19 is skipped")
        return pd.DataFrame(), None, None
    s47 = _script47()
    clim = s47.load_climate()
    warren = s47.load_warren()
    wells = s47.load_wells()
    lvl = s47.run_recurrence(clim, warren).merge(s47.observed_median(wells), on="month", how="left")
    cal, stats, _q = s47.calibrate(lvl)
    if stats is None:
        warn("the film's map was refused (too few calibration months) — E19 is not run")
        return pd.DataFrame(), None, None
    ok = lvl["median_level_observed_m"].notna() & (lvl["n_wells_observed"] >= QMAP_MIN_WELLS)
    offset = float((lvl.loc[ok, "median_level_observed_m"] - lvl.loc[ok, "median_level_modelled_m"]).mean())
    run = pd.DataFrame({"raw": lvl["median_level_modelled_m"].to_numpy(float), "mapped": cal,
                        "offset": lvl["median_level_modelled_m"].to_numpy(float) + offset},
                       index=pd.PeriodIndex(lvl["month"], freq="M"))
    stats = dict(stats, offset_m=offset)

    obs, cmap = load_ccw()
    mdk = _model_a_store(pd.read_csv(INT_MASTER_DATA))
    mdk["k"] = mdk["Name_Original"].astype(str).str.lower().str.strip()
    adm = usable_codes(cmap, mdk.set_index("k"), obs)
    adm = adm[adm["admitted"]]
    cols, n_cens = {}, 0
    for r in adm.itertuples():
        o, nc = observed_series(obs, r.code, r.datum_offset_m)
        if not o.empty:
            cols[normalize_well_name(r.well)] = o
            n_cens += int(nc)
    C = pd.DataFrame(cols)
    C.index = pd.PeriodIndex(C.index, freq="M")
    full = C.notna().all(axis=1)          # every admitted well reads uncensored: the dry tail is clipped, as Script 39
    tgt = C[full].median(axis=1)
    rows = pd.DataFrame({"month": tgt.index.astype(str), "hydro_year": _hydro_year(tgt.index),
                         "ccw_median_m": tgt.to_numpy(float), "n_wells": C[full].notna().sum(axis=1).to_numpy(int)})
    for a in E19_ARMS:
        rows[f"{a}_m"] = run[a].reindex(tgt.index).to_numpy(float)

    # composition: the CCW wells' own median against the network median over the modern record (context, not scored)
    ref = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    names = {normalize_well_name(c): c for c in ref.columns}
    sub = [names[k] for k in C.columns if k in names]
    d = (ref[sub].median(axis=1) - ref[list(wells["well"])].median(axis=1)).dropna()
    comp = {"n_wells": len(sub), "n_months": int(len(d)), "mean": float(d.mean()), "sd": float(d.std()),
            "n_censored": n_cens, "n_months_dropped": int((~full).sum()), "n_wells_ccw": int(C.shape[1])}
    return rows, stats, comp


def e19_years(rows: pd.DataFrame) -> pd.DataFrame:
    out = []
    for y, g in rows.groupby("hydro_year"):
        r = {"hydro_year": int(y), "n_months": int(len(g))}
        for a in E19_ARMS:
            r[f"rmse_{a}_m"] = float(get_metrics(g["ccw_median_m"], g[f"{a}_m"])[1])
        out.append(r)
    return pd.DataFrame(out)


def e19_verdict(rows: pd.DataFrame, years: pd.DataFrame) -> dict:
    """The rule fixed before the run (D-292, E18's with years for wells), per corrected arm: kept if the RMSE falls by
    at least E18_RMSE_CUT_M, the arm lowers RMSE in a majority of the years with >= E19_MIN_MONTHS_PER_YEAR scored
    months, and its |bias| is no larger than raw. Outcome: 'map' if the map passes, else 'offset' if the offset passes,
    else 'neither'."""
    if rows.empty:
        return {"outcome": "not run", "per": {}}
    m = {}
    for a in E19_ARMS:
        nse, rmse, bias = get_metrics(rows["ccw_median_m"], rows[f"{a}_m"])
        m[a] = {"nse": float(nse), "rmse": float(rmse), "bias": float(bias)}
    yy = years[years["n_months"] >= E19_MIN_MONTHS_PER_YEAR]
    per = {}
    for a in ("mapped", "offset"):
        d = dict(m[a])
        d["rmse_cut"] = m["raw"]["rmse"] - m[a]["rmse"]
        d["n_years"] = int(len(yy))
        d["n_improved"] = int((yy[f"rmse_{a}_m"] < yy["rmse_raw_m"]).sum())
        d["tests"] = {"rmse_cut": d["rmse_cut"] >= E18_RMSE_CUT_M,
                      "majority": d["n_improved"] > d["n_years"] / 2,
                      "bias": abs(m[a]["bias"]) <= abs(m["raw"]["bias"])}
        d["pass"] = all(d["tests"].values())
        per[a] = d
    outcome = "map" if per["mapped"]["pass"] else ("offset" if per["offset"]["pass"] else "neither")
    return {"outcome": outcome, "per": per, "raw": m["raw"], "n_months": int(len(rows))}


def e19_report(rr, rows, years, v, stats, comp) -> None:
    if v.get("outcome") == "not run":
        return
    code = {"map": 2, "offset": 1, "neither": 0}[v["outcome"]]
    _n = f"film's warren run against the median of the admitted CCW wells, {v['n_months']} months 1989-96 (E19, D-292)"
    rr.add("e19_outcome", code, unit="",
           note="E19 outcome (D-292): 2 = the film's quantile map transfers, 1 = only the offset does, 0 = neither (the film keeps its map, caveated)")
    rr.add("e19_rmse_cut_threshold_m", E18_RMSE_CUT_M, unit="m", note="E19 rule: RMSE must fall by at least this (config.E18_RMSE_CUT_M, D-292)")
    rr.add("e19_n_months", v["n_months"], unit="months", note=f"CCW months scored, every admitted well uncensored; {_n}")
    rr.add("e19_n_months_dropped", comp["n_months_dropped"], unit="months", note="CCW months dropped because an admitted well was censored at its pipe base (E19)")
    rr.add("e19_n_wells_ccw", comp["n_wells_ccw"], unit="wells", note="admitted CCW wells in the median (Script 39's admission, E19)")
    for k, lab in (("rmse", "RMSE"), ("bias", "bias (modelled minus observed)"), ("nse", "NSE")):
        rr.add(f"e19_{k}_raw" + ("_m" if k != "nse" else ""), v["raw"][k], unit="m" if k != "nse" else "", note=f"{lab}, raw run, {_n}")
    for a, key in (("mapped", "map"), ("offset", "offset")):
        d = v["per"][a]
        for k, lab in (("rmse", "RMSE"), ("bias", "bias (modelled minus observed)"), ("nse", "NSE"), ("rmse_cut", "raw RMSE less this arm's")):
            rr.add(f"e19_{k}_{key}" + ("_m" if k != "nse" else ""), d[k], unit="m" if k != "nse" else "", note=f"{lab}, {a} arm, {_n}")
        rr.add(f"e19_n_years_improved_{key}", d["n_improved"], unit="years", note=f"hydrology years where the {a} arm lowers RMSE (E19)")
        rr.add(f"e19_pass_{key}", int(d["pass"]), unit="", note=f"E19 rule on the {a} arm: kept (1) or not (0), D-292")
    rr.add("e19_n_years", v["per"]["mapped"]["n_years"], unit="years",
           note="D-207 hydrology years with at least E19_MIN_MONTHS_PER_YEAR scored months (E19)")
    rr.add("e19_offset_m", stats["offset_m"], unit="m", note="the offset arm: mean observed minus modelled over the film's calibration months (E19)")
    for k, lab in (("bias_raw", "bias, raw"), ("bias_mapped", "bias, mapped"), ("rmse_raw", "RMSE, raw"),
                   ("rmse_mapped", "RMSE, mapped"), ("wet_end_bias_raw", "wet-end bias, raw"),
                   ("wet_end_bias_mapped", "wet-end bias, mapped")):
        rr.add(f"e19_modern_{k}_m", float(stats[k]), unit="m",
               note=f"{lab}: the film's calibration over its {stats['n_months']} modern months (Script 47's calibrate, read by E19)")
    for k, lab in (("level_max_raw", "raw"), ("level_max_mapped", "mapped")):
        rr.add(f"e19_century_{k}_m", float(stats[k]), unit="m",
               note=f"highest monthly level of the film's century run, {lab} (Script 47's calibrate, read by E19)")
    rr.add("e19_composition_mean_m", comp["mean"], unit="m",
           note=f"modern record: the CCW wells' median less the network median, mean over {comp['n_months']} months (context, not scored)")
    rr.add("e19_composition_sd_m", comp["sd"], unit="m", note="the same difference, standard deviation (E19 context)")


def run_e19():
    rows, stats, comp = e19_tests()
    if rows.empty:
        return rows, pd.DataFrame(), {"outcome": "not run"}, stats, comp
    years = e19_years(rows)
    v = e19_verdict(rows, years)
    r = v["raw"]
    step(f"{v['n_months']} CCW months ({comp['n_months_dropped']} dropped, censored), {comp['n_wells_ccw']} wells; "
         f"raw RMSE {r['rmse']:.3f} m, bias {r['bias']:+.3f}, NSE {r['nse']:.2f}")
    for a, d in v["per"].items():
        step(f"{a}: RMSE {d['rmse']:.3f} (cut {d['rmse_cut']:+.3f}), bias {d['bias']:+.3f}, NSE {d['nse']:.2f}, "
             f"better in {d['n_improved']}/{d['n_years']} years: {'pass' if d['pass'] else 'fail'} "
             f"{ {k: bool(x) for k, x in d['tests'].items()} }")
    step(f"composition (modern): CCW wells' median less network median {comp['mean']:+.3f} m, sd {comp['sd']:.3f}")
    step(f"E19 outcome: {v['outcome']}")
    rows.to_csv(OUT_50_CCW_FILM_MAP, index=False); saved(f"{OUT_50_CCW_FILM_MAP.name} ({len(rows)} rows)")
    years.to_csv(OUT_50_CCW_FILM_MAP_YEARS, index=False); saved(f"{OUT_50_CCW_FILM_MAP_YEARS.name} ({len(years)} rows)")
    return rows, years, v, stats, comp


# ──────────────────────────────────────────────────────────────────────────────
def main(no_fig: bool = False) -> int:
    banner("50e", "Drier epochs and forcing (E10, E11, E13/E13b, E19: D-260, D-261, D-273, D-274, D-292)", version=__version__)
    DIR_50E.mkdir(parents=True, exist_ok=True)

    phase(1, "Inputs")
    lev, lev_cols, cl, master = load_inputs()
    info(f"{len(master)} reference wells; lengths {', '.join(LENGTHS)} (fitted monthly changes); "
         f"split {MODEL_AB_SPLIT_DATE}; stability tolerance {RECLEN_STABLE_TOL:g}")

    # E10 compares against the record-length fits; since the split they come from 50a's saved per-well table
    # float_precision="round_trip": the default parser can miss a double's last bit, and E10's identity check
    # (forest_forcing_check_max_abs_beta3_diff) must still read exactly 0 against the in-memory frame it used to get
    df = pd.read_csv(OUT_50_PER_WELL, float_precision="round_trip")
    phase(2, "Is the forest's poor forecasting the drainage or the forcing? (E10, 1.9.0, D-260)")
    ff_tab, ff_chk = forest_forcing(lev, lev_cols, cl, master, df)
    ff_ver = forest_forcing_verdicts(ff_tab)
    step(f"identity: F0 against the full-record fits, max |d beta_3| = {ff_chk:.2e}")
    for c, v in ff_ver.items():
        step(f"C{c}: best {v['best']}, forward NSE {v['fwd_F0']:.3f} -> {v['fwd_best']:.3f} (gain {v['gain']:+.3f}); "
             f"Model B identified {v['n_identified_F0']} -> {v['n_identified']} of {v['n_wells']}; "
             f"summer-winter {v['season_F0']*1000:+.1f} -> {v['season_best']*1000:+.1f} mm; dBIC {v['dbic_best']:+.1f}")
        result(f"E10 verdict C{c}", v["verdict"])
        p_ = v["posthoc"]
        step(f"C{c} POST HOC forward NSE, inner / edge: F0 {p_[('F0','inner')]:.3f} / {p_[('F0','edge')]:.3f}; "
             f"F2 {p_[('F2','inner')]:.3f} / {p_[('F2','edge')]:.3f}; F2s (step placebo) {p_[('F2s','inner')]:.3f}; "
             f"F2e (edge only) all wells {v['posthoc_all']['F2e']:.3f}")
    ff_tab.to_csv(OUT_50_FOREST_FORCING, index=False); saved(f"{OUT_50_FOREST_FORCING.name} ({len(ff_tab)} rows)")

    phase(3, "What Ranwell's 1951-53 readings need, and what could supply it (E11, 1.10.0, D-261)")
    rn_grid, rn_chk = ranwell_need(cl)
    if len(rn_grid):
        rn_need = ranwell_need_summary(rn_grid)
        rn_cand, rn_ctx = ranwell_epoch_context(cl, lev, lev_cols, rn_need)
        step(f"identity: k = 1 against Script 44, max |dNSE| = {rn_chk:.2e}; {rn_need['n_pairs']} pairs")
        j = rn_need["joint"]
        step(f"need: median NSE {rn_need['nse_base']:.3f} as fitted; alone, beta_1 x{rn_need['single']['k1']['k']:.2f}, "
             f"beta_2 x{rn_need['single']['k2']['k']:.2f}, beta_3 x{rn_need['single']['k3']['k']:.2f}; jointly "
             f"x{j['k1']:.2f}, x{j['k2']:.2f}, x{j['k3']:.2f} -> {j['nse']:.3f}")
        for r in rn_cand.itertuples():
            step(f"{r.item}: {r.kind}, {r.coefficient or '-'} {r.direction or ''}; matches the need: {r.direction_matches_need}; "
                 f"NSE {r.nse_at_k_low:.3f}" + ("" if pd.isna(r.nse_at_k_high) else f" / {r.nse_at_k_high:.3f}"))
        rn_grid.to_csv(OUT_50_RANWELL_NEED, index=False); saved(f"{OUT_50_RANWELL_NEED.name} ({len(rn_grid)} rows)")
        rn_cand.to_csv(OUT_50_RANWELL_EPOCH, index=False); saved(f"{OUT_50_RANWELL_EPOCH.name} ({len(rn_cand)} rows)")

    phase(4, "Does another evaporation estimate, or a recharge break, explain the 2006-08 excess? (E13, 1.13.0, D-273)")
    e13_rad, e13_pm, e13_wx, e13_mon, (e13_clim, e13_W) = e13_evaporation(cl, master)
    e13_br = e13_break(e13_clim, e13_W, master)
    e13_bv = e13_break_verdict(e13_br)
    (step if e13_wx["scaled_identity_max_m"] < 1e-6 else warn)(
        f"identity: scaled against raw PET, max |run difference| {e13_wx['scaled_identity_max_m']:.2e} m")
    for p_ in E13_PETS_RADIATION:
        result(f"E13 {p_}", e13_verdict(e13_rad, p_))
    result("E13 Penman-Monteith", e13_verdict(e13_pm, "Penman-Monteith"))
    step(f"weather 2006-08 against {E8E_LATER_YEARS[0]}-{E8E_LATER_YEARS[1]}: wind {e13_wx['u2_early_ms']:.2f} / "
         f"{e13_wx['u2_later_ms']:.2f} m/s, vapour pressure {e13_wx['ea_early_kpa']:.2f} / {e13_wx['ea_later_kpa']:.2f} kPa, "
         f"PM - Thornthwaite shift {e13_wx['pm_minus_th_shift_mm_yr']:+.1f} mm/yr; PM months filled "
         f"{e13_wx['pm_months_filled']} of {e13_wx['pm_months']}")
    step(f"beta_1 break: {e13_bv['n']} wells ({e13_bv['n_dropped']} dropped), higher before at {e13_bv['n_higher_before']}, "
         f"resolved at {e13_bv['n_resolved']} ({' '.join(w.upper() for w in e13_bv['resolved'])}); median share "
         f"{e13_bv['median_share']:.2f}")
    result("E13 beta_1 break", e13_bv["verdict"])
    e13_mon.to_csv(OUT_50_PET_ALT); saved(f"{OUT_50_PET_ALT.name} ({len(e13_mon)} rows)")
    pd.concat([e13_rad, e13_pm]).to_csv(OUT_50_E13_PET, index=False); saved(f"{OUT_50_E13_PET.name}")
    e13_br.to_csv(OUT_50_E13_BREAK, index=False); saved(f"{OUT_50_E13_BREAK.name} ({len(e13_br)} rows)")
    pd.Series(e13_wx, name="value").to_csv(OUT_50_E13_WEATHER, index_label="quantity"); saved(OUT_50_E13_WEATHER.name)

    phase(5, "Penman-Monteith against Thornthwaite, and Script 24's residual seasonality under each (E13b, 1.14.0, D-274)")
    e13b_cmp = e13b_comparison(e13_mon)
    e13b_rs, e13b_ident = e13b_residual_seasonality(lev, lev_cols, cl, e13_mon["midas_pm"].dropna())
    e13b_sum = e13b_resid_summary(e13b_rs)
    (step if e13b_ident < 1e-9 else warn)(f"identity: Thornthwaite full record against Script 24, max |difference| {e13b_ident:.2e} m")
    v = e13b_cmp.set_index(["basis", "pet", "quantity"])["value"]
    for b in ("all", "measured"):
        step(f"{b} years {v[(b, '', 'first_year')]:.0f}-{v[(b, '', 'last_year')]:.0f}: annual Thornthwaite "
             f"{v[(b, 'Thornthwaite', 'annual_mean_mm')]:.0f} mm, Penman-Monteith {v[(b, 'Penman-Monteith', 'annual_mean_mm')]:.0f} mm "
             f"(ratio {v[(b, 'Penman-Monteith', 'ratio_to_thornthwaite')]:.3f}); trends {v[(b, 'Thornthwaite', 'trend_mm_per_decade')]:+.1f} / "
             f"{v[(b, 'Penman-Monteith', 'trend_mm_per_decade')]:+.1f} mm/decade")
    step(f"residual seasonality, {e13b_sum['n_wells']} wells: PM/Thornthwaite amplitude median ratio {e13b_sum['amp_ratio_median']:.2f}, "
         f"lower at {e13b_sum['n_amp_lower']}; RMSE lower at {e13b_sum['n_rmse_lower']}; significant summer-minus-winter: "
         f"Thornthwaite {e13b_sum['sig_thornthwaite']}, PM {e13b_sum['sig_penman_monteith']}")
    result("E13b residual seasonality", e13b_sum["verdict"])
    e13b_cmp.to_csv(OUT_50_E13B_CMP, index=False); saved(f"{OUT_50_E13B_CMP.name} ({len(e13b_cmp)} rows)")
    e13b_in = e13b_annual_inputs(e13_mon)
    e13b_in.to_csv(OUT_50_E13B_INPUTS); saved(f"{OUT_50_E13B_INPUTS.name} ({len(e13b_in)} rows)")
    e13b_rs.to_csv(OUT_50_E13B_RESID, index=False); saved(f"{OUT_50_E13B_RESID.name} ({len(e13b_rs)} rows)")

    phase(6, "Does the film's correction transfer to CCW 1989-96? (E19, 1.22.0, D-292)")
    e19 = run_e19()

    phase(7, "Outputs")
    rr = ReportNumbers()
    beta3_bound_report(rr, {   # 1.25.0 (D-332)
        "forest_forcing": (ff_tab, "full_beta_3", "E10's full-record fits (50_27)"),
        "e13": (pd.concat([e13_rad, e13_pm]), "beta_3", "E13's centroid fits under each evaporation estimate (50_32)"),
    })
    forest_forcing_report(rr, ff_ver, ff_chk)
    if len(rn_grid):
        ranwell_epoch_report(rr, rn_need, rn_ctx, rn_cand, rn_chk)
    e13_report(rr, e13_rad, e13_pm, e13_bv, e13_wx)
    e13b_report(rr, e13b_cmp, e13b_sum, e13b_ident)
    e19_report(rr, *e19)
    rr.save(OUT_50E_REPORT_NUMBERS); saved(f"{OUT_50E_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    if not no_fig:
        plot_e13(e13_rad, e13_pm, e13_br)
        plot_e13b(e13_mon, e13b_rs)
    done("50e")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Drier epochs and forcing (E10, E11, E13/E13b, E19: D-260, D-261, D-273, D-274, D-292)")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figure")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
