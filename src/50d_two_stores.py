"""
50d_two_stores.py — Two stores and non-climatic change (E8-E8g: D-231 to D-236, D-255).

Script 50 suite, step 50d (J-15, T-208; Martin 2026-11-24: five families, numbered 50a-50e,
all opt-in). Split from 50_record_length.py 1.30.0, whose full version history is kept in git and in
50a_record_length.py; every function moved whole with its dated comments. Shared helpers live in
utils/reclen_common.py.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-11-24 (J-15, T-208). Split from Script 50 1.30.0.

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
    DIR_50D, OUT_50D_REPORT_NUMBERS, OUT_50_PER_WELL, OUT_50_BY_CLUSTER, OUT_50_CCW, OUT_50_STABLE, OUT_50_FIG,
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


# ──────────────────────────────────────────────────────────────────────────────
# E8: two drainage time scales per cluster (1.3.0, D-231)
# ──────────────────────────────────────────────────────────────────────────────
TS_FORMS = (("single", False), ("double", True))


TS_VERDICT = {"regional field": 2, "two stores supported": 1, "not resolved": 0}


def _ts_model(ps, head: pd.Series, P, E, double: bool, noise: bool, name: str):
    ml = ps.Model(head, name=name)
    rf = ps.DoubleExponential() if double else ps.Exponential()
    ps.RechargeModel(ml, P, E, rfunc=rf, name="rch", recharge=ps.rch.Linear())
    if double:
        ml.set_parameter("rch_a1", initial=TWO_STORE_FAST_INIT_DAYS,
                         pmin=TWO_STORE_FAST_BOUNDS_DAYS[0], pmax=TWO_STORE_FAST_BOUNDS_DAYS[1])
        ml.set_parameter("rch_a2", initial=TWO_STORE_SLOW_INIT_DAYS,
                         pmin=TWO_STORE_SLOW_BOUNDS_DAYS[0], pmax=TWO_STORE_SLOW_BOUNDS_DAYS[1])
        ml.set_parameter("rch_alpha", initial=TWO_STORE_SLOW_SHARE_INIT, pmin=0.0, pmax=1.0)
    if noise:
        ps.ArNoiseModel(model=ml)        # registers itself; add_noisemodel goes in pastas 2.4
    return ml


def _ts_solve(ml, P, tmin=None, tmax=None):
    start = pd.Timestamp(tmin) if tmin is not None else ml.oseries.series.index[0]
    ml.solve(tmin=tmin, tmax=tmax, report=False, warmup=int((start - P.index[0]).days))
    return ml


def _ts_sim(ml, P, a, b) -> pd.Series:
    a, b = pd.Timestamp(a), pd.Timestamp(b)
    return ml.simulate(tmin=a, tmax=b, warmup=int((a - P.index[0]).days))


def _winter_max(s: pd.Series) -> pd.Series:
    w = s[s.index.month.isin([10, 11, 12, 1, 2, 3])]
    lab = np.where(w.index.month >= 10, w.index.year + 1, w.index.year)
    return w.groupby(lab).max()


def _identify(row: dict, dbl: bool) -> dict:
    """1.11.0 (D-266): blank the e-fold of a store the fit does not identify; flag one that sits on its bound."""
    s = float(row.get("slow_share", 0.0)) if dbl else 0.0
    for store, share, bounds in (("fast", 1.0 - s, TWO_STORE_FAST_BOUNDS_DAYS),
                                 ("slow", s, TWO_STORE_SLOW_BOUNDS_DAYS)):
        key = f"{store}_efold_months"
        raw = row.get(key, np.nan)
        row[f"{key}_raw"] = raw
        present = dbl or store == "fast"
        ident = bool(present and np.isfinite(raw) and share >= TWO_STORE_SHARE_MIN)
        row[f"{store}_identified"] = ident
        at = ""
        if ident and dbl:
            for side, b in (("lower", bounds[0]), ("upper", bounds[1])):
                if abs(np.log(raw / (b / DAYS_PER_MONTH))) <= np.log1p(TWO_STORE_BOUND_TOL):
                    at = side
        row[f"{store}_at_bound"] = at
        if not ident:
            row[key] = np.nan
            if f"{key}_se" in row:
                row[f"{key}_se"] = np.nan
    return row


def two_store(lev, lev_cols, cl, master):
    """E8 (D-231): per cluster centroid, single against double exponential; the tests of the spec."""
    import pastas as ps
    ps.set_log_level("ERROR")
    ra = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    start = continuous_start(cl)
    P, E = spread_daily(cl, start)
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    md = master.set_index("_n")
    ccw_ok = paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()
    if ccw_ok:
        obs, cmap = load_ccw()
        mdk = _model_a_store(pd.read_csv(INT_MASTER_DATA))
        mdk["k"] = mdk["Name_Original"].astype(str).str.lower().str.strip()
        adm = usable_codes(cmap, mdk.set_index("k"), obs)
        adm = adm[adm["admitted"]]
    rows, models, sims = [], {}, {}
    clusters = [int(c[1:]) for c in ra.columns if c.startswith("C") and c[1:].isdigit()]
    for c in track(clusters, "E8 two-store, per cluster", min_seconds=5.0):
        h = ra[f"C{c}"].dropna()
        hm = h.copy(); hm.index = hm.index + pd.offsets.MonthEnd(0)
        for form, dbl in TS_FORMS:
            for noise in (False, True):
                ml = _ts_solve(_ts_model(ps, hm, P, E, dbl, noise, f"C{c}_{form}_{int(noise)}"), P)
                o, se = ml.parameters["optimal"], ml.parameters["stderr"]
                sim = _ts_sim(ml, P, hm.index[0], hm.index[-1]).reindex(hm.index)
                res = hm - sim
                yr = res.groupby(res.index.year).mean()
                early = yr.loc[TWO_STORE_EARLY_YEARS[0]:TWO_STORE_EARLY_YEARS[1]]
                later = res[res.index.year > TWO_STORE_EARLY_YEARS[1]]
                a_fast = float(o["rch_a1"] if dbl else o["rch_a"])
                row = {"cluster": c, "form": form, "noise_ar1": noise, "n_obs": int(hm.notna().sum()),
                       "warmup_from": f"{start:%Y-%m}",
                       "fast_efold_months": a_fast / DAYS_PER_MONTH,
                       "slow_efold_months": float(o["rch_a2"]) / DAYS_PER_MONTH if dbl else np.nan,
                       "slow_efold_months_se": float(se["rch_a2"]) / DAYS_PER_MONTH if dbl else np.nan,
                       "slow_share": float(o["rch_alpha"]) if dbl else 0.0,
                       "slow_share_se": float(se["rch_alpha"]) if dbl else np.nan,
                       "gain": float(o["rch_A"]) / DAYS_PER_MONTH, "f_evap": float(o["rch_f"]),
                       "aic": float(ml.stats.aic()), "bic": float(ml.stats.bic()), "rsq": float(ml.stats.rsq()),
                       "early_resid_m": float(early.mean()) if len(early) else np.nan,
                       "later_rmse_m": float(np.sqrt((later ** 2).mean())) if len(later) else np.nan}
                if not noise:
                    models[(c, form)] = (ml, hm)
                    sims[(c, form)] = sim
                    nses = []
                    for d_, kw, test in (("fwd", {"tmax": split - pd.Timedelta(days=1)}, hm[hm.index >= split]),
                                         ("rev", {"tmin": split}, hm[hm.index < split])):
                        try:
                            m2 = _ts_solve(_ts_model(ps, hm, P, E, dbl, False, f"C{c}_{form}_{d_}"), P, **kw)
                            s2 = _ts_sim(m2, P, hm.index[0], hm.index[-1]).reindex(test.index)
                            v = _nse(test, s2)
                        except Exception:
                            v = np.nan
                        row[f"split_nse_{d_}"] = v
                        nses.append(v)
                    row["split_nse_median"] = float(np.nanmedian(nses)) if np.isfinite(nses).any() else np.nan
                    # test 2: the CCW drier decade at this cluster's CCW wells
                    biases = []
                    if ccw_ok:
                        for r in adm.itertuples():
                            k = normalize_well_name(r.well)
                            if k not in md.index or int(md.loc[k, "Cluster"]) != c or k not in lev_cols:
                                continue
                            ob, _n = observed_series(obs, r.code, r.datum_offset_m)
                            if ob.empty:
                                continue
                            wl = lev[lev_cols[k]].dropna()
                            common = wl.index.intersection(h.index)
                            shift = float(wl.loc[common].mean() - h.loc[common].mean())
                            obm = ob.copy(); obm.index = pd.DatetimeIndex(obm.index) + pd.offsets.MonthEnd(0)
                            pr = _ts_sim(ml, P, obm.index[0], obm.index[-1]).reindex(obm.index) + shift
                            ok = pr.notna() & obm.notna()
                            if ok.any():
                                biases.append(float((pr[ok] - obm[ok]).mean()))
                    row["ccw_n_wells"] = len(biases)
                    row["ccw_bias_median_m"] = float(np.median(biases)) if biases else np.nan
                rows.append(_identify(row, dbl))
    tab = pd.DataFrame(rows)

    # NW9 (test 4b): the check cluster's models run at the check well
    wrows, nw = [], {}
    k = normalize_well_name(TWO_STORE_CHECK_WELL)
    if k in lev_cols and (TWO_STORE_CHECK_CLUSTER, "double") in models:
        wl = lev[lev_cols[k]].dropna()
        h = ra[f"C{TWO_STORE_CHECK_CLUSTER}"].dropna()
        common = wl.index.intersection(h.index)
        shift = float(wl.loc[common].mean() - h.loc[common].mean())
        wm = wl.copy(); wm.index = wm.index + pd.offsets.MonthEnd(0)
        out = pd.DataFrame({"observed_m": wm})
        for form, _d in TS_FORMS:
            ml, _hm = models[(TWO_STORE_CHECK_CLUSTER, form)]
            out[f"{form}_m"] = _ts_sim(ml, P, wm.index[0], wm.index[-1]).reindex(wm.index) + shift
        out.index.name = "month_end"
        wmax = out.apply(_winter_max)
        for form, _d in TS_FORMS:
            col = f"{form}_m"
            fl = all(wmax.loc[y, col] >= -TWO_STORE_SURFACE_TOL_M for y in TWO_STORE_FLOOD_WINTERS if y in wmax.index)
            nr = all(wmax.loc[y, col] >= -TWO_STORE_NEAR_TOL_M for y in TWO_STORE_NEAR_WINTERS if y in wmax.index)
            dr = all(wmax.loc[y, col] < -TWO_STORE_SURFACE_TOL_M for y in TWO_STORE_DRY_WINTERS if y in wmax.index)
            nw[form] = {"flood": fl, "near": nr, "dry": dr, "pass": bool(fl and nr and dr)}
        wrows = out.reset_index()
        wrows["shift_m"] = shift
        nw["winter_max"] = wmax
    nw["sims"] = sims
    return tab, (pd.DataFrame(wrows) if len(wrows) else pd.DataFrame()), nw, start


def two_store_verdict(tab: pd.DataFrame, nw: dict) -> tuple[str, pd.DataFrame]:
    """The rule fixed before the run (spec section 3)."""
    base = tab[~tab["noise_ar1"]].set_index(["cluster", "form"])
    ar1 = tab[tab["noise_ar1"]].set_index(["cluster", "form"])
    per = []
    for c in sorted(tab["cluster"].unique()):
        s, d = base.loc[(c, "single")], base.loc[(c, "double")]
        t1 = bool(d["bic"] < s["bic"] and d["split_nse_median"] >= s["split_nse_median"])
        t2 = (bool(abs(d["ccw_bias_median_m"]) <= TWO_STORE_CCW_BIAS_TOL_M and t1)
              if np.isfinite(d["ccw_bias_median_m"]) else np.nan)
        es, ed = abs(s["early_resid_m"]), abs(d["early_resid_m"])
        t4 = bool(es > 0 and (es - ed) / es >= TWO_STORE_EARLY_REDUCTION
                  and d["later_rmse_m"] <= s["later_rmse_m"] + TWO_STORE_LATER_RMSE_TOL_M)
        if c == TWO_STORE_CHECK_CLUSTER and "double" in nw:
            t4 = bool(t4 and nw["double"]["pass"])
        a = ar1.loc[(c, "double")] if (c, "double") in ar1.index else None
        per.append({"cluster": c, "test1": t1, "test2": t2, "test4": t4,
                    "slow_efold_months_ar1": float(a["slow_efold_months"]) if a is not None else np.nan,
                    "slow_efold_months_ar1_se": float(a["slow_efold_months_se"]) if a is not None else np.nan})
    per = pd.DataFrame(per)

    def majority(col):
        v = per[col].dropna().astype(bool)
        return bool(len(v) and v.sum() > len(v) / 2)
    supported = majority("test1") and majority("test2") and majority("test4")
    p1 = per[per["test1"]]
    regional = False
    if len(p1) >= 2:
        lo = p1["slow_efold_months_ar1"] - 1.96 * p1["slow_efold_months_ar1_se"]
        hi = p1["slow_efold_months_ar1"] + 1.96 * p1["slow_efold_months_ar1_se"]
        regional = bool(np.isfinite(lo).all() and np.isfinite(hi).all() and lo.max() <= hi.min())
    per["test3_regional"] = regional
    verdict = ("regional field" if supported and regional else
               "two stores supported" if supported else "not resolved")
    return verdict, per


def two_store_report(rr, tab, per, nw, verdict) -> None:
    rr.add("two_store_verdict", TS_VERDICT[verdict], unit="code",
           note=f"{verdict} (2 regional field, 1 two stores supported, 0 not resolved; the rule fixed before the run, D-231)")
    base = tab[~tab["noise_ar1"]]
    for c in sorted(base["cluster"].unique()):
        s = base[(base.cluster == c) & (base.form == "single")].iloc[0]
        d = base[(base.cluster == c) & (base.form == "double")].iloc[0]
        p = per[per.cluster == c].iloc[0]
        for key, val, unit, note in (
                ("slow_share", d["slow_share"], "", "share of the recharge through the slow store, double exponential"),
                ("slow_efold_months", d["slow_efold_months"], "months", "slow store's e-folding time, double exponential; "
                 f"blank where the store carries under {TWO_STORE_SHARE_MIN:g} of the response (not identified, D-266)"),
                ("bic_double_minus_single", d["bic"] - s["bic"], "", "BIC, double minus single (negative favours two stores)"),
                ("split_nse_single", s["split_nse_median"], "", "median split-test NSE, single exponential"),
                ("split_nse_double", d["split_nse_median"], "", "median split-test NSE, double exponential"),
                ("early_resid_single_m", s["early_resid_m"], "m", f"mean residual {TWO_STORE_EARLY_YEARS[0]}-{TWO_STORE_EARLY_YEARS[1]}, single"),
                ("early_resid_double_m", d["early_resid_m"], "m", f"mean residual {TWO_STORE_EARLY_YEARS[0]}-{TWO_STORE_EARLY_YEARS[1]}, double"),
                ("ccw_bias_single_m", s["ccw_bias_median_m"], "m", "median CCW 1989-96 bias at the cluster's CCW wells, single"),
                ("ccw_bias_double_m", d["ccw_bias_median_m"], "m", "median CCW 1989-96 bias at the cluster's CCW wells, double"),
                ("test1", float(p["test1"]), "flag", "test 1 passed (1) or not (0)"),
                ("test4", float(p["test4"]), "flag", "test 4 passed (1) or not (0)")):
            rr.add(f"two_store_C{c}_{key}", val, unit=unit, note=f"C{c}: {note} (E8, D-231)")
    if "winter_max" in nw:
        wm = nw["winter_max"]
        for y in TWO_STORE_FLOOD_WINTERS + TWO_STORE_NEAR_WINTERS + TWO_STORE_DRY_WINTERS:
            if y in wm.index:
                for col in wm.columns:
                    rr.add(f"two_store_{TWO_STORE_CHECK_WELL}_winter{y}_max_{col}", float(wm.loc[y, col]), unit="m",
                           note=f"{TWO_STORE_CHECK_WELL}: highest level, winter ending {y} ({col.replace('_m', '')}; E8, D-231)")
        for form in ("single", "double"):
            if form in nw:
                rr.add(f"two_store_{TWO_STORE_CHECK_WELL}_{form}_pass", float(nw[form]["pass"]), unit="flag",
                       note=f"{TWO_STORE_CHECK_WELL} winters reproduced by the C{TWO_STORE_CHECK_CLUSTER} {form} model (test 4b)")


def plot_two_store(tab, wtab, nw, warmup_start) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    ra = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    fig, axes = plt.subplots(3, 2, figsize=(9.0, 8.4), dpi=160, sharex=True)
    clusters = sorted(tab["cluster"].unique())
    for ax, c in zip(axes.ravel(), clusters):
        h = ra[f"C{c}"].dropna()
        ax.plot(h.index, h.values, "o", ms=1.6, color="0.35", label="observed")
        for form, col, ls in (("single", "0.15", "-"), ("double", "#2166ac", "--")):
            sm = nw.get("sims", {}).get((c, form))
            if sm is not None:
                ax.plot(sm.index, sm.values, color=col, lw=0.9, ls=ls,
                        label="single store" if form == "single" else "two stores")
        ax.axvspan(pd.Timestamp(f"{TWO_STORE_EARLY_YEARS[0]}-01-01"), pd.Timestamp(f"{TWO_STORE_EARLY_YEARS[1]}-12-31"),
                   color="#fdb863", alpha=0.25, lw=0)
        b = tab[(tab.cluster == c) & (~tab.noise_ar1)].set_index("form")
        ax.set_title(f"({'abcde'[clusters.index(c)]}) {CLUSTER_LABELS.get(c, f'C{c}')}: slow share "
                     f"{b.loc['double', 'slow_share']:.2f}, ΔBIC {b.loc['double', 'bic'] - b.loc['single', 'bic']:+.0f}",
                     loc="left", fontsize=8.5)
        ax.grid(alpha=0.3)
    ax = axes.ravel()[len(clusters)]
    if len(wtab):
        t = pd.to_datetime(wtab["month_end"])
        ax.plot(t, wtab["observed_m"], "o", ms=1.6, color="0.35", label="observed")
        ax.plot(t, wtab["single_m"], color="0.15", lw=1.0, label="single store")
        ax.plot(t, wtab["double_m"], color="#2166ac", lw=1.0, ls="--", label="two stores")
        ax.axhline(0, color="#b2182b", lw=0.8)
        for y in TWO_STORE_FLOOD_WINTERS + TWO_STORE_NEAR_WINTERS + TWO_STORE_DRY_WINTERS:
            ax.axvspan(pd.Timestamp(f"{y - 1}-10-01"), pd.Timestamp(f"{y}-03-31"), color="0.85", lw=0)
        ax.set_title(f"(f) {TWO_STORE_CHECK_WELL.upper()} (C{TWO_STORE_CHECK_CLUSTER} models at the well)", loc="left", fontsize=8.5)
        ax.legend(fontsize=6.5, loc="lower left")
        ax.grid(alpha=0.3)
    for a in axes[:, 0]:
        a.set_ylabel("level (m, ground = 0)")
    fig.tight_layout()
    fig.savefig(OUT_50_TWO_STORE_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_50_TWO_STORE_FIG.name)


# ──────────────────────────────────────────────────────────────────────────────
# E8b and E8c (1.4.0, D-232): a non-climatic change, and surface flow
# ──────────────────────────────────────────────────────────────────────────────
CHANGE_FORMS = ("step", "relax", "trend")


SURFACE_FORMS = ("tarso", "threshold")


CHANGE_VERDICT = {"site-wide change": 2, "cluster-specific change": 1, "no non-climatic term needed": 0}


SURFACE_VERDICT = {"surface flow supported": 1, "not supported": 0}


def _ordinal(d) -> int:
    return pd.Timestamp(d).toordinal()


def _from_ordinal(x) -> pd.Timestamp:
    return pd.Timestamp.fromordinal(int(round(float(x)))) if np.isfinite(x) else pd.NaT


def _single(ps, hm, P, E, name, noise=False):
    return _ts_model(ps, hm, P, E, False, noise, name)


def _change_model(ps, hm, P, E, form: str, name: str, fixed: dict, noise=False):
    """The single store plus one non-climatic term, its date(s) FIXED at `fixed` (profiled by _profile)."""
    ml = _single(ps, hm, P, E, name, noise)
    if form in ("step", "relax"):
        ps.StepModel(ml, tstart=CHANGE_TSTART_INIT, rfunc=ps.One() if form == "step" else ps.Exponential(),
                     name="step")
    else:
        ps.LinearTrend(ml, tstart=CHANGE_TSTART_BOUNDS[0], tend=CHANGE_TSTART_BOUNDS[1], name="trend")
    for k, v in fixed.items():
        ml.set_parameter(k, initial=v, vary=False)
    return ml


def _surface_model(ps, hm, P, E, form: str, name: str, fixed: dict | None = None, noise=False):
    if form == "tarso":
        ml = ps.Model(hm, name=name, constant=False)
        ps.TarsoModel(ml, P, E, oseries=hm, name="tarso")
        if noise:
            ps.ArNoiseModel(model=ml)        # registers itself; add_noisemodel goes in pastas 2.4
        return ml
    ml = _single(ps, hm, P, E, name, noise)
    tr = ps.ThresholdTransform(ml, value=-SURFACE_BAND_M, vmin=-2 * SURFACE_THRESHOLD_MAX_DEPTH_M, vmax=0.5,
                               name="transform")
    for k, v in (fixed or {}).items():     # a transform's parameters reach ml.parameters only at solve
        tr.parameters.loc[k, ["initial", "vary"]] = [v, False]
    return ml


def _month_grid(a, b, step_months: int) -> list[int]:
    return [_ordinal(d) for d in pd.date_range(a, b, freq=f"{step_months}MS")]


def _change_grid(form: str):
    """Coarse grid for the profiled date(s); _profile refines around the best point."""
    a, b = CHANGE_TSTART_BOUNDS
    if form in ("step", "relax"):
        return [{"step_tstart": t} for t in _month_grid(a, b, CHANGE_GRID_COARSE_MONTHS)]
    g = _month_grid(a, b, 12)
    return [{"trend_tstart": t0, "trend_tend": t1} for t0 in g for t1 in g if t1 > t0]


def _refine(best: dict, form: str):
    """Monthly points around the coarse optimum (quarterly for the two dates of a trend)."""
    lo, hi = (_ordinal(d) for d in CHANGE_TSTART_BOUNDS)
    if form in ("step", "relax"):
        t = _from_ordinal(best["step_tstart"])
        pts = [_ordinal(t + pd.DateOffset(months=k)) for k in range(-CHANGE_GRID_COARSE_MONTHS, CHANGE_GRID_COARSE_MONTHS + 1)]
        return [{"step_tstart": x} for x in pts if lo <= x <= hi]
    t0, t1 = _from_ordinal(best["trend_tstart"]), _from_ordinal(best["trend_tend"])
    out = []
    for k0 in range(-6, 7, 3):
        for k1 in range(-6, 7, 3):
            x0, x1 = _ordinal(t0 + pd.DateOffset(months=k0)), _ordinal(t1 + pd.DateOffset(months=k1))
            if lo <= x0 < x1 <= hi:
                out.append({"trend_tstart": x0, "trend_tend": x1})
    return out


def _profile(make, P, grid, refine=None, tmin=None, tmax=None):
    """Fit `make(fixed)` at every point of `grid` (then of `refine(best)`), keeping the least-squares best.

    WHY: Pastas cannot optimize a change date or a threshold transform's level — the simulation is daily
    and stepwise in them, so the finite-difference gradient is zero and the optimizer returns the initial
    value with a standard error of 0 (seen 2026-10-02 on a synthetic step). Profiling fixes the parameter,
    fits the rest, and keeps the best. The 95% interval is the profile's: every point with
    n_eff * ln(SSE/SSE_min) <= 3.84, n_eff the residuals' AR(1)-adjusted sample size n(1-r)/(1+r)."""
    rows, models = [], {}
    def run(fx):
        key = tuple(sorted(fx.items()))
        if key in models:
            return
        try:
            ml = _ts_solve(make(fx), P, tmin, tmax)
            res = ml.residuals().dropna()
            rows.append({**fx, "sse": float((res ** 2).sum()), "n": len(res)})
            models[key] = ml
        except Exception:
            pass
    for fx in grid:
        run(fx)
    if not rows:
        return None, pd.DataFrame()
    if refine is not None:
        b = min(rows, key=lambda r: r["sse"])
        for fx in refine({k: v for k, v in b.items() if k not in ("sse", "n")}):
            run(fx)
    prof = pd.DataFrame(rows)
    b = prof.loc[prof["sse"].idxmin()]
    keys = [k for k in prof.columns if k not in ("sse", "n")]
    best = models[tuple(sorted((k, b[k]) for k in keys))]
    res = best.residuals().dropna()
    r1 = float(res.autocorr(1)) if len(res) > 2 else 0.0
    n_eff = len(res) * (1 - r1) / (1 + r1) if r1 < 1 else 1.0
    prof["inside95"] = n_eff * np.log(prof["sse"] / b["sse"]) <= 3.84
    return best, prof


def _interval(prof: pd.DataFrame, key: str):
    """The 95% profile interval of one profiled parameter (its extent among the points inside)."""
    g = prof[prof["inside95"]]
    return (float(g[key].min()), float(g[key].max())) if len(g) else (np.nan, np.nan)


def _bic_profiled(ml, k_extra: int) -> float:
    """Pastas's BIC counts only varying parameters; a profiled one was estimated too."""
    return float(ml.stats.bic()) + k_extra * np.log(len(ml.residuals().dropna()))


def _split_nses(fit, hm, P, directions):
    """Split-test NSE at MODEL_AB_SPLIT_DATE. `fit(tmin, tmax)` returns a model solved on the training
    half (profiled there, for a term with a profiled date), which is then run over the other half."""
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    out = {}
    for d_ in ("fwd", "rev"):
        tmin, tmax = (None, split - pd.Timedelta(days=1)) if d_ == "fwd" else (split, None)
        test = hm[hm.index >= split] if d_ == "fwd" else hm[hm.index < split]
        try:
            m2 = fit(tmin, tmax)
            out[d_] = _nse(test, _ts_sim(m2, P, hm.index[0], hm.index[-1]).reindex(test.index)) if m2 is not None else np.nan
        except Exception:
            out[d_] = np.nan
    used = [out[d] for d in directions if np.isfinite(out[d])]
    out["rule"] = float(np.median(used)) if used else np.nan
    return out


def _ccw_bias_cluster(ml, P, c, ctx) -> tuple[float, int]:
    if ctx is None:
        return np.nan, 0
    adm, obs, md, lev, lev_cols, h = ctx
    biases = []
    for r in adm.itertuples():
        k = normalize_well_name(r.well)
        if k not in md.index or int(md.loc[k, "Cluster"]) != c or k not in lev_cols:
            continue
        ob, _n = observed_series(obs, r.code, r.datum_offset_m)
        if ob.empty:
            continue
        wl = lev[lev_cols[k]].dropna()
        common = wl.index.intersection(h.index)
        shift = float(wl.loc[common].mean() - h.loc[common].mean())
        obm = ob.copy(); obm.index = pd.DatetimeIndex(obm.index) + pd.offsets.MonthEnd(0)
        pr = _ts_sim(ml, P, obm.index[0], obm.index[-1]).reindex(obm.index) + shift
        ok = pr.notna() & obm.notna()
        if ok.any():
            biases.append(float((pr[ok] - obm[ok]).mean()))
    return (float(np.median(biases)) if biases else np.nan), len(biases)


def _well_winters(ml, P, wl, h) -> pd.Series:
    common = wl.index.intersection(h.index)
    shift = float(wl.loc[common].mean() - h.loc[common].mean())
    wm = wl.copy(); wm.index = wm.index + pd.offsets.MonthEnd(0)
    return _winter_max(_ts_sim(ml, P, wm.index[0], wm.index[-1]).reindex(wm.index) + shift)


def _winters_pass(wmax: pd.Series) -> bool:
    fl = all(wmax.get(y, -9) >= -TWO_STORE_SURFACE_TOL_M for y in TWO_STORE_FLOOD_WINTERS)
    nr = all(wmax.get(y, -9) >= -TWO_STORE_NEAR_TOL_M for y in TWO_STORE_NEAR_WINTERS)
    dr = all(wmax.get(y, 9) < -TWO_STORE_SURFACE_TOL_M for y in TWO_STORE_DRY_WINTERS)
    return bool(fl and nr and dr)


def _residual_stats(ml, P, hm) -> dict:
    sim = _ts_sim(ml, P, hm.index[0], hm.index[-1]).reindex(hm.index)
    res = hm - sim
    yr = res.groupby(res.index.year).mean()
    early = yr.loc[TWO_STORE_EARLY_YEARS[0]:TWO_STORE_EARLY_YEARS[1]]
    later = res[res.index.year > TWO_STORE_EARLY_YEARS[1]]
    near = hm.shift(1) >= -SURFACE_BAND_M
    return {"early_resid_m": float(early.mean()) if len(early) else np.nan,
            "later_rmse_m": float(np.sqrt((later ** 2).mean())) if len(later) else np.nan,
            "near_surface_resid_m": float(res[near].mean()) if near.any() else np.nan,
            "near_surface_n": int(near.sum()),
            "other_rmse_m": float(np.sqrt((res[~near] ** 2).mean())) if (~near).any() else np.nan,
            "sim": sim}


def change_and_surface(lev, lev_cols, cl, master):
    """E8b and E8c (D-232) on each cluster centroid; the rule of the spec."""
    import pastas as ps
    ps.set_log_level("ERROR")
    ra = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    P, E = spread_daily(cl, continuous_start(cl))
    md = master.set_index("_n")
    ctx_base = None
    if paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists():
        obs, cmap = load_ccw()
        mdk = _model_a_store(pd.read_csv(INT_MASTER_DATA))
        mdk["k"] = mdk["Name_Original"].astype(str).str.lower().str.strip()
        adm = usable_codes(cmap, mdk.set_index("k"), obs)
        ctx_base = (adm[adm["admitted"]], obs, md, lev, lev_cols)
    kw_ = normalize_well_name(TWO_STORE_CHECK_WELL)
    check_well = lev[lev_cols[kw_]].dropna() if kw_ in lev_cols else None
    rw = None
    if RANWELL_LEVELS.exists() and OUT_44_METRICS.exists():
        lv = pd.read_csv(RANWELL_LEVELS, parse_dates=["date"])
        lv["month"] = lv["date"].dt.to_period("M")
        rw = (lv.groupby(["site_no", "month"])["level_m_od"].mean(), pd.read_csv(OUT_44_METRICS))
    crow, srow, sims = [], [], {}
    clusters = [int(c[1:]) for c in ra.columns if c.startswith("C") and c[1:].isdigit()]
    for c in track(clusters, "E8b/E8c change and surface flow, per cluster", min_seconds=5.0):
        h = ra[f"C{c}"].dropna()
        hm = h.copy(); hm.index = hm.index + pd.offsets.MonthEnd(0)
        ctx = (*ctx_base, h) if ctx_base else None
        base = _ts_solve(_single(ps, hm, P, E, f"C{c}_single"), P)
        bst = _residual_stats(base, P, hm)
        single_fit = lambda tmin, tmax: _ts_solve(_single(ps, hm, P, E, f"C{c}_single_s"), P, tmin, tmax)
        bsplit = _split_nses(single_fit, hm, P, CHANGE_SPLIT_DIRECTIONS)
        bsplit_s = _split_nses(single_fit, hm, P, ("fwd", "rev"))
        bccw, nccw = _ccw_bias_cluster(base, P, c, ctx)
        sims[(c, "single")] = bst["sim"]
        common = {"cluster": c, "bic_single": float(base.stats.bic()), "ccw_n_wells": nccw}
        # E8b — the change date(s) profiled (see _profile)
        for form in CHANGE_FORMS:
            row = dict(common, form=form)
            info(f"E8b C{c} {form}")
            try:
                mk = lambda fx, f=form: _change_model(ps, hm, P, E, f, f"C{c}_{f}", fx)
                fitp = lambda tmin, tmax, f=form: _profile(
                    lambda fx: _change_model(ps, hm, P, E, f, f"C{c}_{f}_s", fx), P, _change_grid(f),
                    lambda bb: _refine(bb, f), tmin, tmax)[0]
                ml, prof = _profile(mk, P, _change_grid(form), lambda bb, f=form: _refine(bb, f))
                o = ml.parameters["optimal"]
                st = _residual_stats(ml, P, hm)
                sp = _split_nses(fitp, hm, P, CHANGE_SPLIT_DIRECTIONS)
                tkey = "step_tstart" if form != "trend" else "trend_tstart"
                lo95, hi95 = _interval(prof, tkey)
                if form in ("step", "relax"):
                    size = float(o["step_A"])
                else:
                    size = float(o["trend_a"]) * float(o["trend_tend"] - o["trend_tstart"])
                row.update(bic=_bic_profiled(ml, 2 if form == "trend" else 1), aic=float(ml.stats.aic()),
                           rsq=float(ml.stats.rsq()), tstart=_from_ordinal(o[tkey]),
                           tstart_lo95=_from_ordinal(lo95), tstart_hi95=_from_ordinal(hi95),
                           tstart_at_bound=bool(o[tkey] <= _ordinal(CHANGE_TSTART_BOUNDS[0])
                                                or o[tkey] >= _month_grid(*CHANGE_TSTART_BOUNDS, 1)[-1]),
                           tend=_from_ordinal(o["trend_tend"]) if form == "trend" else pd.NaT,
                           relax_efold_months=float(o["step_a"]) / DAYS_PER_MONTH if form == "relax" else np.nan,
                           change_m=size, split_nse_fwd=sp["fwd"], split_nse_rev=sp["rev"], split_nse_rule=sp["rule"],
                           single_split_nse_rule=bsplit["rule"],
                           early_resid_m=st["early_resid_m"], early_resid_single_m=bst["early_resid_m"],
                           later_rmse_m=st["later_rmse_m"], later_rmse_single_m=bst["later_rmse_m"],
                           ccw_bias_m=_ccw_bias_cluster(ml, P, c, ctx)[0], ccw_bias_single_m=bccw,
                           profile_points=len(prof))
                if c == TWO_STORE_CHECK_CLUSTER and check_well is not None:
                    wm = _well_winters(ml, P, check_well, h)
                    row["check_well_pass"] = _winters_pass(wm)
                    for y in TWO_STORE_FLOOD_WINTERS + TWO_STORE_NEAR_WINTERS + TWO_STORE_DRY_WINTERS:
                        row[f"check_well_winter{y}_max_m"] = float(wm.get(y, np.nan))
                sims[(c, form)] = st["sim"]
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"[:200]
            crow.append(row)
        # E8c — TARSO fits its threshold; the transform's level is profiled
        for form in SURFACE_FORMS:
            row = dict(common, form=form)
            info(f"E8c C{c} {form}")
            try:
                if form == "tarso":
                    ml = _ts_solve(_surface_model(ps, hm, P, E, form, f"C{c}_{form}"), P)
                    fitp = lambda tmin, tmax: _ts_solve(_surface_model(ps, hm, P, E, "tarso", f"C{c}_tarso_s"), P, tmin, tmax)
                    tkey, kx = "tarso_d1", 0
                    pmn, pmx = ml.parameters.loc[tkey, "pmin"], ml.parameters.loc[tkey, "pmax"]
                else:
                    grid = [{"transform_d": v} for v in SURFACE_THRESHOLD_GRID]
                    ml, _p = _profile(lambda fx: _surface_model(ps, hm, P, E, "threshold", f"C{c}_thr", fx), P, grid)
                    fitp = lambda tmin, tmax: _profile(
                        lambda fx: _surface_model(ps, hm, P, E, "threshold", f"C{c}_thr_s", fx), P, grid,
                        None, tmin, tmax)[0]
                    tkey, kx = "transform_d", 1
                    pmn, pmx = SURFACE_THRESHOLD_GRID[0], SURFACE_THRESHOLD_GRID[-1]
                o = ml.parameters["optimal"]
                st = _residual_stats(ml, P, hm)
                sp = _split_nses(fitp, hm, P, ("fwd", "rev"))
                thr = float(o[tkey])
                row.update(bic=_bic_profiled(ml, kx), aic=float(ml.stats.aic()), rsq=float(ml.stats.rsq()),
                           threshold_m=thr, threshold_at_bound=bool(np.isclose(thr, pmn) or np.isclose(thr, pmx)),
                           split_nse_fwd=sp["fwd"], split_nse_rev=sp["rev"], split_nse_rule=sp["rule"],
                           single_split_nse_rule=bsplit_s["rule"],
                           near_surface_resid_m=st["near_surface_resid_m"], near_surface_n=st["near_surface_n"],
                           near_surface_resid_single_m=bst["near_surface_resid_m"],
                           other_rmse_m=st["other_rmse_m"], other_rmse_single_m=bst["other_rmse_m"],
                           ccw_bias_m=_ccw_bias_cluster(ml, P, c, ctx)[0], ccw_bias_single_m=bccw)
                if c == 1 and rw is not None:
                    row.update(_ranwell_check(ml, base, P, rw))
                sims[(c, form)] = st["sim"]
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"[:200]
            srow.append(row)
    return pd.DataFrame(crow), pd.DataFrame(srow), sims


def _ranwell_check(ml, base, P, rw) -> dict:
    """E8c check: the C1 centroid's surface-flow and single models at Ranwell's C1 headline sites, scored as
    Script 44 scores them (offset removed, censored at the ground)."""
    obs_month, pairs = rw
    out = {}
    for tag, m in (("surface", ml), ("single", base)):
        vals = []
        for pr in pairs[pairs["headline"]].itertuples():
            if int(pr.site_no) not in obs_month.index.get_level_values(0):
                continue
            om = obs_month.loc[int(pr.site_no)]
            a = om.index.min().to_timestamp() - pd.offsets.MonthEnd(1)
            b = om.index.max().to_timestamp() + pd.offsets.MonthEnd(0)
            sim = _ts_sim(m, P, a, b)
            mid = sim.resample("ME").last()
            mid = (mid + mid.shift(1)) / 2
            mid.index = mid.index.to_period("M")
            vals.append(compare_offset_censored(om, mid.dropna(), float(pr.ground_m_od))["nse_after_offset"])
        out[f"ranwell_nse_{tag}"] = float(np.nanmedian(vals)) if vals else np.nan
    return out


def change_surface_verdicts(ch: pd.DataFrame, sf: pd.DataFrame):
    per_c, per_s = [], []
    for c in sorted(ch["cluster"].unique()):
        g = ch[(ch.cluster == c) & ch["bic"].notna()]
        if g.empty:
            per_c.append({"cluster": c, "earns": False}); continue
        b = g.loc[g["bic"].idxmin()]
        earns = bool(b["bic_single"] - b["bic"] >= TWO_STORE_BIC_STRONG
                     and b["split_nse_rule"] >= b["single_split_nse_rule"])
        per_c.append({"cluster": c, "best_form": b["form"], "earns": earns, "drop": bool(b["change_m"] < 0),
                      "tstart": b["tstart"], "tstart_lo95": b["tstart_lo95"], "tstart_hi95": b["tstart_hi95"],
                      "tstart_at_bound": b["tstart_at_bound"],
                      "check_well_pass": b.get("check_well_pass", np.nan)})
    per_c = pd.DataFrame(per_c)
    e = per_c[per_c["earns"]]
    common_date = pd.NaT
    if len(e) >= 2 and e["tstart_lo95"].notna().all() and e["tstart_hi95"].notna().all():
        lo, hi = max(e["tstart_lo95"]), min(e["tstart_hi95"])
        if lo <= hi:
            common_date = lo + (hi - lo) / 2
    verdict_c = ("site-wide change" if (len(e) > len(per_c) / 2 and pd.notna(common_date)) else
                 "cluster-specific change" if len(e) else "no non-climatic term needed")
    for c in sorted(sf["cluster"].unique()):
        g = sf[(sf.cluster == c) & sf["bic"].notna()]
        if g.empty:
            per_s.append({"cluster": c, "passes": False}); continue
        b = g.loc[g["bic"].idxmin()]
        t1 = bool(b["bic_single"] - b["bic"] >= TWO_STORE_BIC_STRONG and b["split_nse_rule"] >= b["single_split_nse_rule"])
        ns, ns0 = abs(b["near_surface_resid_m"]), abs(b["near_surface_resid_single_m"])
        t2 = bool(np.isfinite(ns0) and ns0 > 0 and (ns0 - ns) / ns0 >= 0.5
                  and b["other_rmse_m"] <= b["other_rmse_single_m"] + TWO_STORE_LATER_RMSE_TOL_M)
        t3 = bool(b["threshold_m"] >= -SURFACE_THRESHOLD_MAX_DEPTH_M and not b["threshold_at_bound"])
        per_s.append({"cluster": c, "best_form": b["form"], "test1": t1, "test2": t2, "test3": t3,
                      "passes": bool(t1 and t2 and t3), "threshold_m": b["threshold_m"]})
    per_s = pd.DataFrame(per_s)
    verdict_s = "surface flow supported" if per_s["passes"].sum() > len(per_s) / 2 else "not supported"
    return verdict_c, per_c, common_date, verdict_s, per_s


def change_surface_report(rr, verdict_c, per_c, common_date, verdict_s, per_s) -> None:
    rr.add("change_verdict", CHANGE_VERDICT[verdict_c], unit="code",
           note=f"{verdict_c} (2 site-wide, 1 cluster-specific, 0 none; E8b, rule fixed before the run, D-232)")
    rr.add("change_common_date", common_date.strftime("%Y-%m") if pd.notna(common_date) else np.nan, unit="month",
           note="midpoint of the overlap of the change dates' 95% intervals across the clusters that need a term (E8b)")
    for r in per_c.itertuples():
        rr.add(f"change_C{r.cluster}_earns", float(r.earns), unit="flag", note=f"C{r.cluster}: a non-climatic term earns its place (E8b)")
        if getattr(r, "best_form", None):
            rr.add(f"change_C{r.cluster}_tstart", r.tstart.strftime("%Y-%m") if pd.notna(r.tstart) else np.nan,
                   unit="month", note=f"C{r.cluster}: fitted change date, best form {r.best_form} (E8b)")
    rr.add("surface_verdict", SURFACE_VERDICT[verdict_s], unit="code",
           note=f"{verdict_s} (1 supported at a majority of clusters, 0 not; E8c, D-232)")
    for r in per_s.itertuples():
        rr.add(f"surface_C{r.cluster}_passes", float(r.passes), unit="flag", note=f"C{r.cluster}: surface flow passes tests 1-3 (E8c)")
        if getattr(r, "best_form", None):
            rr.add(f"surface_C{r.cluster}_threshold_m", r.threshold_m, unit="m",
                   note=f"C{r.cluster}: fitted surface-flow threshold, best form {r.best_form}, level relative to ground (E8c)")


def plot_change_surface(ch, sf, sims, per_c, per_s) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    ra = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    clusters = sorted(ch["cluster"].unique())
    fig, axes = plt.subplots(3, 2, figsize=(9.0, 8.4), dpi=160, sharex=True)
    for ax, c in zip(axes.ravel(), clusters):
        h = ra[f"C{c}"].dropna()
        ax.plot(h.index, h.values, "o", ms=1.6, color="0.35", label="observed")
        pc = per_c[per_c.cluster == c].iloc[0]
        ps_ = per_s[per_s.cluster == c].iloc[0]
        for key, col, ls, lab in ((("single"), "0.15", "-", "single store"),
                                  (pc.get("best_form"), "#b2182b", "--", f"with {pc.get('best_form')}"),
                                  (ps_.get("best_form"), "#2166ac", ":", f"{ps_.get('best_form')}")):
            sm = sims.get((c, key))
            if sm is not None:
                ax.plot(sm.index, sm.values, color=col, lw=0.9, ls=ls, label=lab)
        ax.axhline(-SURFACE_BAND_M, color="#2166ac", lw=0.5, alpha=0.6)
        ax.set_title(f"({'abcde'[clusters.index(c)]}) {CLUSTER_LABELS.get(c, f'C{c}')}: change "
                     f"{'yes' if pc['earns'] else 'no'}, surface flow {'yes' if ps_['passes'] else 'no'}",
                     loc="left", fontsize=8.5)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=6, loc="lower left")
    axes.ravel()[-1].set_visible(False)
    axes[1, 1].xaxis.set_tick_params(labelbottom=True)   # panel (d) sits above the hidden panel, which took its labels
    for a in axes[:, 0]:
        a.set_ylabel("level (m, ground = 0)")
    fig.tight_layout()
    fig.savefig(OUT_50_CHANGE_SURFACE_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_50_CHANGE_SURFACE_FIG.name)


# ── E8d (1.5.0, D-234): rain event structure ─────────────────────────────────────────────────────────
E8D_VERDICT = {"event structure supported": 2, "unusual rain, but it does not explain the excess": 1,
               "not supported": 0}


def _winter_of(idx: pd.DatetimeIndex) -> np.ndarray:
    """October-March winter label: the year of its January."""
    return np.where(idx.month >= 10, idx.year + 1, idx.year)


def rain_events(gauge: str):
    """Per gauge: the long-event threshold from its own baseline, a per-winter table of the event measures
    with their baseline percentiles, and the day-level long-event flag."""
    s = read_daily(MIDAS_RAIN_DIR / gauge)
    full = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"))
    wet = (full >= E8D_WET_DAY_MM).fillna(False)
    run = (wet != wet.shift(fill_value=False)).cumsum()          # a missing day is not wet, so it ends a run
    ev = full[wet].groupby(run[wet]).agg(["size", "sum"]).rename(columns={"size": "ndays", "sum": "total"})
    ev["start"] = full[wet].index.to_series().groupby(run[wet].to_numpy()).min().to_numpy()
    multi = ev[ev["ndays"] >= E8D_EVENT_MIN_DAYS]
    base = multi[pd.DatetimeIndex(multi["start"]).year <= E8D_BASELINE_END_YEAR]
    thr = float(np.percentile(base["total"], E8D_EVENT_PCTL))
    long_ids = multi.index[multi["total"] >= thr]
    in_long = wet & run.isin(long_ids)
    win = pd.Series(_winter_of(full.index), index=full.index)
    inwin = full.index.month.isin(E8D_WINTER_MONTHS)
    rows = []
    for w, idx in full[inwin].groupby(win[inwin]).groups.items():
        d = full.loc[idx]
        n_exp = len(pd.date_range(f"{w - 1}-10-01", f"{w}-03-31", freq="D"))
        miss = 1 - d.notna().sum() / n_exp
        tot = float(d.sum())
        spell = run[idx][wet[idx]].value_counts()
        rows.append({"gauge": gauge, "winter": int(w), "days_present": int(d.notna().sum()),
                     "missing_frac": miss, "total_mm": tot,
                     "long_event_mm": float(d[in_long[idx]].sum()),
                     "event_share": float(d[in_long[idx]].sum()) / tot if tot > 0 else np.nan,
                     "longest_wet_spell_days": int(spell.max()) if len(spell) else 0,
                     "days_ge_20mm": int((d >= 20).sum())})
    tab = pd.DataFrame(rows)
    tab["complete"] = tab["missing_frac"] <= E8D_MAX_MISSING_FRAC
    bl = tab[(tab["winter"] <= E8D_BASELINE_END_YEAR) & tab["complete"]]
    for col in ("event_share", "longest_wet_spell_days", "days_ge_20mm", "total_mm"):
        ref = bl[col].to_numpy()
        tab[f"{col}_pctl"] = [float((ref <= x).mean() * 100) if np.isfinite(x) else np.nan for x in tab[col]]
    tab["baseline_n_winters"] = len(bl)
    tab["long_event_threshold_mm"] = thr
    return tab, in_long, full


def monthly_event_share(in_long: pd.Series, full: pd.Series) -> pd.Series:
    """The share of each month's rain that fell in long events (months missing more than the tolerance are
    NaN), on the YYYY-MM-01 month stamps the climate frame uses."""
    m = full.groupby(full.index.to_period("M"))
    tot = m.sum(); n = m.count(); exp = pd.Series([p.days_in_month for p in tot.index], index=tot.index)
    lon = full.where(in_long).groupby(full.index.to_period("M")).sum()
    sh = (lon / tot).where((1 - n / exp) <= E8D_MAX_MISSING_FRAC)
    sh.index = sh.index.to_timestamp()
    return sh


def event_stress(cl, share: pd.Series):
    """Test 3: the single store with and without a long-event stress (RAF Valley monthly rain x the gauge's
    long-event share), per cluster centroid, fitted E8D_FIT_START..E8D_FIT_END."""
    import pastas as ps
    ps.set_log_level("ERROR")
    ra = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    start = continuous_start(cl)
    P, E = spread_daily(cl, start)
    # a month with no usable share (before the gauge, or too many missing days) takes that calendar month's
    # mean share over the gauge's complete months - a neutral fill, reported as fill_months
    clim = share.groupby(share.index.month).mean()
    sh = share.reindex(cl.index)
    fill = sh.isna() & cl["P_m"].notna()
    sh = sh.fillna(pd.Series(cl.index.month.map(clim), index=cl.index))
    cll = cl.copy(); cll["P_m"] = cl["P_m"] * sh
    PL, _ = spread_daily(cll, start)
    end = pd.Timestamp(E8D_FIT_END)
    rows = []
    for c in [int(k[1:]) for k in ra.columns if k.startswith("C") and k[1:].isdigit()]:
        h = ra[f"C{c}"].dropna()
        hm = h.copy(); hm.index = hm.index + pd.offsets.MonthEnd(0)
        hm = hm[(hm.index >= pd.Timestamp(E8D_FIT_START)) & (hm.index <= end)]
        info(f"E8d C{c}")

        def with_stress(name):
            ml = _single(ps, hm, P, E, name)
            ps.StressModel(ml, PL, rfunc=ps.Exponential(), name="longev", settings="prec")
            return ml
        row = {"cluster": c, "fill_months": int(fill.loc[start:end].sum())}
        try:
            base = _ts_solve(_single(ps, hm, P, E, f"C{c}_e8d_single"), P)
            ml = _ts_solve(with_stress(f"C{c}_e8d_event"), P)
            o, se = ml.parameters["optimal"], ml.parameters["stderr"]
            b0, b1 = _residual_stats(base, P, hm), _residual_stats(ml, P, hm)
            sp0 = _split_nses(lambda a, b: _ts_solve(_single(ps, hm, P, E, f"C{c}_e8d_s0"), P, a, b), hm, P, ("fwd",))
            sp1 = _split_nses(lambda a, b: _ts_solve(with_stress(f"C{c}_e8d_s1"), P, a, b), hm, P, ("fwd",))
            gain, gse = float(o["longev_A"]), float(se["longev_A"])
            red = ((b0["early_resid_m"] - b1["early_resid_m"]) / b0["early_resid_m"]
                   if b0["early_resid_m"] and b0["early_resid_m"] > 0 else np.nan)
            row.update(gain=gain, gain_se=gse,
                       gain_lo95=gain - 1.96 * gse, gain_hi95=gain + 1.96 * gse,
                       efold_days=float(o["longev_a"]),
                       bic_single=float(base.stats.bic()), bic=float(ml.stats.bic()),
                       dbic=float(base.stats.bic() - ml.stats.bic()),
                       split_nse_fwd=sp1["fwd"], split_nse_fwd_single=sp0["fwd"],
                       early_resid_m=b1["early_resid_m"], early_resid_single_m=b0["early_resid_m"],
                       early_reduction=red,
                       later_rmse_m=b1["later_rmse_m"], later_rmse_single_m=b0["later_rmse_m"])
            row["earns"] = bool(row["gain_lo95"] > 0 and row["dbic"] >= TWO_STORE_BIC_STRONG
                                and sp1["fwd"] >= sp0["fwd"] and np.isfinite(red)
                                and red >= E8D_RESIDUAL_REDUCTION)
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"[:200]
            row["earns"] = False
        rows.append(row)
    return pd.DataFrame(rows)


def e8d_verdict(prim: pd.DataFrame, chk: pd.DataFrame, st: pd.DataFrame):
    t = prim.set_index("winter")
    test = [w for w in E8D_TEST_WINTERS if w in t.index and t.loc[w, "complete"]]
    unusual = [w for w in test if t.loc[w, "event_share_pctl"] >= E8D_UNUSUAL_PCTL]
    t1 = len(unusual) >= E8D_UNUSUAL_MIN_COUNT
    c = chk.set_index("winter")
    cw = [w for w in E8D_TEST_WINTERS if w in c.index and c.loc[w, "complete"]]
    check_agrees = bool(cw) and float(np.mean([c.loc[w, "event_share_pctl"] for w in cw])) > 50
    later = [w for w in E8D_LATER_WINTERS if w in t.index and t.loc[w, "complete"]]
    t2 = (E8D_FLOOD_WINTER in t.index and bool(later)
          and all(t.loc[w, "event_share"] < t.loc[E8D_FLOOD_WINTER, "event_share"] for w in later))
    ex = st[st["cluster"].isin(E8D_CLUSTERS_WITH_EXCESS)]
    n_earn = int(ex["earns"].sum())
    t3 = n_earn > len(ex) / 2
    verdict = ("event structure supported" if (t1 and t3) else
               "unusual rain, but it does not explain the excess" if t1 else "not supported")
    return verdict, {"test1": t1, "unusual_winters": unusual, "check_gauge_agrees": check_agrees,
                     "test2": bool(t2), "later_winters_used": later, "test3": t3, "clusters_earning": n_earn,
                     "clusters_tested": len(ex)}


def e8d_report(rr, prim, chk, st, verdict, info_d) -> None:
    rr.add("e8d_verdict", E8D_VERDICT[verdict], unit="code",
           note=f"{verdict} (2 supported, 1 unusual rain but no explanation, 0 not supported; E8d, D-234)")
    rr.add("e8d_long_event_threshold_mm", float(prim["long_event_threshold_mm"].iloc[0]), unit="mm",
           note=f"long-event threshold at {E8D_PRIMARY_GAUGE}: the {E8D_EVENT_PCTL}th percentile of multi-day event totals, baseline to {E8D_BASELINE_END_YEAR}")
    t = prim.set_index("winter")
    for w in sorted(set(E8D_TEST_WINTERS) | set(E8D_LATER_WINTERS)):
        if w in t.index:
            rr.add(f"e8d_event_share_{w}", t.loc[w, "event_share"], unit="fraction",
                   note=f"share of the {w - 1}/{str(w)[2:]} winter's rain in long events at {E8D_PRIMARY_GAUGE}")
            rr.add(f"e8d_event_share_pctl_{w}", t.loc[w, "event_share_pctl"], unit="percentile",
                   note=f"{w - 1}/{str(w)[2:]} event share against the gauge's own baseline winters")
    rr.add("e8d_test1_unusual", float(info_d["test1"]), unit="flag", note="E8d test 1: 2005-08 winters unusual in event share")
    rr.add("e8d_test2_later_lower", float(info_d["test2"]), unit="flag", note="E8d test 2: later wet winters below 2006/07")
    rr.add("e8d_clusters_earning", info_d["clusters_earning"], unit="count",
           note=f"E8d test 3: clusters (of {info_d['clusters_tested']}, C2-C5) where the long-event stress earns its place")
    rr.add("e8d_check_gauge_agrees", float(info_d["check_gauge_agrees"]), unit="flag",
           note=f"{E8D_CHECK_GAUGE} points the same way on the test winters (reported, not the rule)")


def plot_rain_events(prim, chk) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    fig, axes = plt.subplots(2, 1, figsize=(9.0, 6.4), dpi=160, sharex=True)
    for ax, tab, lab in ((axes[0], prim, E8D_PRIMARY_GAUGE), (axes[1], chk, E8D_CHECK_GAUGE)):
        t = tab[tab["complete"]]
        bl = t[t["winter"] <= E8D_BASELINE_END_YEAR]["event_share"]
        ax.axhspan(np.percentile(bl, 20), np.percentile(bl, 80), color="0.85", label="baseline 20th-80th percentile")
        ax.plot(t["winter"], t["event_share"], "o-", ms=3, lw=0.8, color="0.3", label="winter event share")
        for w in E8D_TEST_WINTERS:
            if w in set(t["winter"]):
                ax.plot(w, t.set_index("winter").loc[w, "event_share"], "o", ms=7, color="#b2182b")
        for w in E8D_LATER_WINTERS:
            if w in set(t["winter"]):
                ax.plot(w, t.set_index("winter").loc[w, "event_share"], "s", ms=7, color="#2166ac")
        ax.set_title(f"{lab}: share of October-March rain in long events "
                     f"(threshold {tab['long_event_threshold_mm'].iloc[0]:.0f} mm)", loc="left", fontsize=9)
        ax.set_ylabel("share of winter rain")
        ax.grid(alpha=0.3); ax.legend(fontsize=7, loc="upper left")
    axes[1].set_xlabel("winter (labelled by January); red: 2005-08, blue: later wet winters")
    fig.tight_layout()
    fig.savefig(OUT_50_RAIN_EVENTS_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_50_RAIN_EVENTS_FIG.name)


# ── E8e (1.6.0, D-235): the felling north of NW9, and the pine's return ──────────────────────────────
E8E_VERDICT = {"felling and regrowth supported (local)": 2, "consistent in place, timing not resolved": 1,
               "not supported": 0}


def _decimal_year(t) -> float:
    t = pd.Timestamp(t)
    y0 = pd.Timestamp(year=t.year, month=1, day=1)
    return t.year + (t - y0).days / (pd.Timestamp(year=t.year + 1, month=1, day=1) - y0).days


def felling_by_well(lev, lev_cols, cl):
    """Per well: the E8 single store on the full record, its 2006-08 excess and later level, and the two
    distances from 01_locations.csv. Returns the table and NW9's monthly residual."""
    import pastas as ps
    ps.set_log_level("ERROR")
    start = continuous_start(cl)
    P, E = spread_daily(cl, start)
    loc = pd.read_csv(INT_LOCATIONS)
    loc["_n"] = loc["Name"].astype(str).apply(normalize_well_name)
    loc = loc.drop_duplicates("_n").set_index("_n")
    y0, y1 = TWO_STORE_EARLY_YEARS
    rows, nw9_res = [], None
    for k, col in sorted(lev_cols.items()):
        if k in LAKE_GAUGE_KEYS or k not in loc.index:
            continue
        h = lev[col].dropna()
        n_early = int(((h.index.year >= y0) & (h.index.year <= y1)).sum())
        if n_early < E8E_MIN_EARLY_MONTHS:
            continue
        hm = h.copy(); hm.index = hm.index + pd.offsets.MonthEnd(0)
        row = {"well": k, "n_obs": int(len(hm)), "n_early_months": n_early,
               "first": f"{hm.index[0]:%Y-%m}", "last": f"{hm.index[-1]:%Y-%m}",
               "dist_1998_felling_m": float(loc.loc[k, "dist_1998_replant_m"]),
               "in_1998_felling": str(loc.loc[k, "in_1998_replant"]) if pd.notna(loc.loc[k, "in_1998_replant"]) else "",
               "dist_coast_m": float(loc.loc[k, "dist_coast_m"]),
               "in_forest": bool(loc.loc[k, "in_forest"])}
        try:
            ml = _ts_solve(_single(ps, hm, P, E, f"{k}_e8e"), P)
            sim = _ts_sim(ml, P, hm.index[0], hm.index[-1]).reindex(hm.index)
            res = hm - sim
            yr = res.groupby(res.index.year).mean()
            row.update(excess_m=float(yr.loc[y0:y1].mean()),
                       later_m=float(yr.loc[E8E_LATER_YEARS[0]:E8E_LATER_YEARS[1]].mean()),
                       rsq=float(ml.stats.rsq()), efold_months=float(ml.parameters.loc["rch_a", "optimal"]) / DAYS_PER_MONTH)
            if k == normalize_well_name(E8E_CHECK_WELL):
                nw9_res = res
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"[:200]
        rows.append(row)
    tab = pd.DataFrame(rows)
    tab["near"] = tab["dist_1998_felling_m"] <= E8E_NEAR_M
    tab["far_open"] = (tab["dist_1998_felling_m"] > E8E_FAR_M) & ~tab["in_forest"]
    return tab, nw9_res


def canopy_halfway():
    """The canopy frames of E8E_CANOPY_REGION at E8E_CANOPY_VIEWPOINT, and the decimal year the ratio is first
    halfway from its first frame to its highest (linear between frames)."""
    ci = pd.read_csv(paths.OUT_41_INDEX)
    f = ci[(ci["region"] == E8E_CANOPY_REGION) & (ci["viewpoint"] == E8E_CANOPY_VIEWPOINT)
           & ci["ratio_to_conifer"].notna()].copy()
    f["t"] = pd.to_datetime(f["imagery_date"])
    f = f.sort_values("t").reset_index(drop=True)
    f["year"] = f["t"].apply(_decimal_year)
    v0, vmax = float(f["ratio_to_conifer"].iloc[0]), float(f["ratio_to_conifer"].max())
    target = v0 + 0.5 * (vmax - v0)
    yr = np.nan
    for i in range(1, len(f)):
        a, b = f.loc[i - 1], f.loc[i]
        if b["ratio_to_conifer"] >= target:
            yr = a["year"] + (target - a["ratio_to_conifer"]) / (b["ratio_to_conifer"] - a["ratio_to_conifer"]) * (b["year"] - a["year"])
            break
    return f[["imagery_date", "frame", "leaf_state", "ratio_to_conifer", "year"]], v0, vmax, target, yr


def e8e_tests(tab, nw9_res):
    from scipy.stats import spearmanr, mannwhitneyu
    t = tab[tab["excess_m"].notna()]
    rf = spearmanr(t["dist_1998_felling_m"], t["excess_m"])
    rc = spearmanr(t["dist_coast_m"], t["excess_m"])
    near, rest = t[t["near"]]["excess_m"], t[~t["near"]]["excess_m"]
    mw = mannwhitneyu(near, rest, alternative="greater") if len(near) and len(rest) else None
    t1 = bool(rf.statistic < 0 and rf.pvalue < E8E_P and abs(rf.statistic) > abs(rc.statistic))
    # checks, reported and never the rule: the two distances are themselves correlated, so each is also
    # taken with the other held fixed (Spearman partial, on ranks), and the open-dune wells alone
    rk = {c: pd.Series(t[c]).rank().to_numpy() for c in ("excess_m", "dist_1998_felling_m", "dist_coast_m")}

    def _partial(y, x, z):
        A = np.c_[np.ones(len(z)), z]
        ry = y - A @ np.linalg.lstsq(A, y, rcond=None)[0]
        rx = x - A @ np.linalg.lstsq(A, x, rcond=None)[0]
        return float(np.corrcoef(ry, rx)[0, 1])
    rho_dd = float(spearmanr(t["dist_1998_felling_m"], t["dist_coast_m"]).statistic)
    pf = _partial(rk["excess_m"], rk["dist_1998_felling_m"], rk["dist_coast_m"])
    pc = _partial(rk["excess_m"], rk["dist_coast_m"], rk["dist_1998_felling_m"])
    op = t[~t["in_forest"]]
    ro = spearmanr(op["dist_1998_felling_m"], op["excess_m"]) if len(op) > 2 else None
    frames, v0, vmax, target, can_year = canopy_halfway()
    # NW9: annual means; the first year after the base years below half their mean
    nw = {"base_m": np.nan, "half_year": np.nan}
    ann = pd.Series(dtype=float)
    if nw9_res is not None:
        ann = nw9_res.groupby(nw9_res.index.year).mean()
        base = float(ann.loc[E8E_TIMING_BASE_YEARS[0]:E8E_TIMING_BASE_YEARS[1]].mean())
        after = ann[ann.index > E8E_TIMING_BASE_YEARS[1]]
        below = after[after < base / 2]
        nw = {"base_m": base, "half_year": float(below.index[0]) if base > 0 and len(below) else np.nan}
    # the residual year Y is the calendar year's mean: centred at Y + 0.5
    gap = (nw["half_year"] + 0.5 - can_year) if np.isfinite(nw["half_year"]) and np.isfinite(can_year) else np.nan
    t2 = bool(np.isfinite(gap) and abs(gap) <= E8E_TIMING_TOL_YEARS)
    far = t[t["far_open"]]["excess_m"]
    verdict = ("felling and regrowth supported (local)" if (t1 and t2) else
               "consistent in place, timing not resolved" if t1 else "not supported")
    info_e = {"n": len(t), "rho_felling": float(rf.statistic), "p_felling": float(rf.pvalue),
              "rho_coast": float(rc.statistic), "p_coast": float(rc.pvalue),
              "n_near": len(near), "n_rest": len(rest), "median_near_m": float(near.median()) if len(near) else np.nan,
              "median_rest_m": float(rest.median()) if len(rest) else np.nan,
              "mw_p": float(mw.pvalue) if mw is not None else np.nan,
              "n_far_open": len(far), "median_far_open_m": float(far.median()) if len(far) else np.nan,
              "test1": t1, "test2": t2, "nw9_base_m": nw["base_m"], "nw9_half_year": nw["half_year"],
              "canopy_first": v0, "canopy_max": vmax, "canopy_target": target, "canopy_half_year": can_year,
              "timing_gap_years": gap, "rho_distances": rho_dd, "partial_felling": pf, "partial_coast": pc,
              "n_open": len(op), "rho_open_felling": float(ro.statistic) if ro is not None else np.nan}
    timing = pd.concat([
        pd.DataFrame({"series": "nw9_annual_residual_m", "year": ann.index.astype(float) + 0.5, "value": ann.values}),
        pd.DataFrame({"series": f"canopy_ratio_{E8E_CANOPY_REGION}_{E8E_CANOPY_VIEWPOINT}", "year": frames["year"],
                      "value": frames["ratio_to_conifer"], "imagery_date": frames["imagery_date"],
                      "frame": frames["frame"], "leaf_state": frames["leaf_state"]})], ignore_index=True)
    return verdict, info_e, timing


def e8e_report(rr, verdict, ie) -> None:
    rr.add("e8e_verdict", E8E_VERDICT[verdict], unit="code",
           note=f"{verdict} (2 supported, 1 place only, 0 not supported; E8e, D-235)")
    rr.add("e8e_n_wells", ie["n"], unit="count", note=f"wells with at least {E8E_MIN_EARLY_MONTHS} readings in 2006-08 and a single-store fit")
    rr.add("e8e_rho_felling", ie["rho_felling"], unit="rho", note="Spearman rho, 2006-08 excess against distance to the nearest 1998 felling")
    rr.add("e8e_p_felling", ie["p_felling"], unit="p", note="its p-value")
    rr.add("e8e_rho_coast", ie["rho_coast"], unit="rho", note="Spearman rho, 2006-08 excess against distance to the coast")
    rr.add("e8e_p_coast", ie["p_coast"], unit="p", note="its p-value")
    rr.add("e8e_median_near_m", ie["median_near_m"], unit="m", note=f"median 2006-08 excess, wells within {E8E_NEAR_M:.0f} m of a 1998 felling (n {ie['n_near']})")
    rr.add("e8e_median_rest_m", ie["median_rest_m"], unit="m", note=f"median 2006-08 excess, the other wells (n {ie['n_rest']})")
    rr.add("e8e_mw_p", ie["mw_p"], unit="p", note="Mann-Whitney, near greater than the rest (reported, not the rule)")
    rr.add("e8e_median_far_open_m", ie["median_far_open_m"], unit="m",
           note=f"median 2006-08 excess, open-dune wells beyond {E8E_FAR_M:.0f} m (n {ie['n_far_open']}; test 3, reported)")
    rr.add("e8e_rho_between_distances", ie["rho_distances"], unit="rho",
           note="Spearman rho between the two distances over the same wells (check, not the rule)")
    rr.add("e8e_partial_felling", ie["partial_felling"], unit="rho",
           note="excess against felling distance with coast distance held fixed (Spearman partial; check)")
    rr.add("e8e_partial_coast", ie["partial_coast"], unit="rho",
           note="excess against coast distance with felling distance held fixed (Spearman partial; check)")
    rr.add("e8e_rho_open_felling", ie["rho_open_felling"], unit="rho",
           note=f"excess against felling distance, open-dune wells only (n {ie['n_open']}; check)")
    rr.add("e8e_nw9_half_year", ie["nw9_half_year"], unit="year", note="first year NW9's annual mean residual is below half its 2006-07 mean")
    rr.add("e8e_canopy_half_year", ie["canopy_half_year"], unit="year",
           note=f"year {E8E_CANOPY_REGION}'s canopy ratio ({E8E_CANOPY_VIEWPOINT}) is halfway from its first frame to its highest")
    rr.add("e8e_timing_gap_years", ie["timing_gap_years"], unit="years", note="NW9 half year (mid-year) minus the canopy half year")


def plot_felling(tab, timing, ie) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    fig = plt.figure(figsize=(9.0, 7.0), dpi=160)
    gs = fig.add_gridspec(2, 2)
    t = tab[tab["excess_m"].notna()]
    k = normalize_well_name(E8E_CHECK_WELL)
    for j, (col, lab, rho, p) in enumerate((("dist_1998_felling_m", "distance to the nearest 1998 felling (m)", ie["rho_felling"], ie["p_felling"]),
                                            ("dist_coast_m", "distance to the coast (m)", ie["rho_coast"], ie["p_coast"]))):
        ax = fig.add_subplot(gs[0, j])
        for forest, mk, c in ((False, "o", "#b8860b"), (True, "^", "#1b7837")):
            s = t[t["in_forest"] == forest]
            ax.plot(s[col], s["excess_m"], mk, ms=5, color=c, alpha=0.8, label="forest" if forest else "open")
        if k in set(t["well"]):
            r = t[t["well"] == k].iloc[0]
            ax.annotate(E8E_CHECK_WELL.upper(), (r[col], r["excess_m"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
        ax.axhline(0, color="0.5", lw=0.6)
        if j == 0:
            ax.axvline(E8E_NEAR_M, color="0.6", lw=0.6, ls="--")
        ax.set_xlabel(lab); ax.set_ylabel("2006-08 mean residual (m)")
        ax.set_title(f"Spearman rho {rho:+.2f} (" + ("p < 0.001" if p < 0.001 else f"p {p:.3f}") + ")",
                     loc="left", fontsize=9)
        ax.grid(alpha=0.3); ax.legend(fontsize=7)
    ax = fig.add_subplot(gs[1, :])
    r = timing[timing["series"] == "nw9_annual_residual_m"]
    ax.bar(r["year"], r["value"], width=0.8, color="#2166ac", alpha=0.7, label=f"{E8E_CHECK_WELL.upper()} annual mean residual")
    ax.axhline(0, color="0.5", lw=0.6)
    if np.isfinite(ie["nw9_half_year"]):
        ax.axvline(ie["nw9_half_year"] + 0.5, color="#2166ac", ls="--", lw=0.8)
    ax.set_ylabel("residual of the single store (m)"); ax.set_xlabel("year")
    ax2 = ax.twinx()
    c = timing[timing["series"].str.startswith("canopy_ratio")]
    ax2.plot(c["year"], c["value"], "o-", color="#1b7837", ms=4, lw=1, label=f"canopy ratio, {E8E_CANOPY_REGION} ({E8E_CANOPY_VIEWPOINT})")
    if np.isfinite(ie["canopy_half_year"]):
        ax2.axvline(ie["canopy_half_year"], color="#1b7837", ls="--", lw=0.8)
    ax2.set_ylabel("canopy texture ratio to mature conifer")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper right")
    ax.set_title("Dashed: NW9 at half its 2006-07 residual; the canopy halfway to its highest", loc="left", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_50_FELLING_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_50_FELLING_FIG.name)


# ── E8f (1.7.0, D-236): the 2014/15 shore clearance — a step in the wells around it? ──────────────────
E8F_VERDICT = {"clearance step at the controls": 2, "no clearance step at the controls": 1, "site-wide 2015 shift": 0}


def clearance_steps(lev, lev_cols, cl):
    """Per well near the clearance (and placebo wells far from it): the E8 single store against the same with one
    step (One) whose date is profiled monthly over E8F_STEP_WINDOW."""
    import pastas as ps
    from shapely.geometry import Point
    from utils.kml_io import read_kml
    ps.set_log_level("ERROR")
    strip = read_kml(DATA_SHORE_CLEARANCE_2015, quiet=True).geometry.union_all()
    start = continuous_start(cl)
    P, E = spread_daily(cl, start)
    loc = pd.read_csv(INT_LOCATIONS)
    loc["_n"] = loc["Name"].astype(str).apply(normalize_well_name)
    loc = loc.drop_duplicates("_n").set_index("_n")
    w0, w1 = (pd.Timestamp(x) for x in E8F_STEP_WINDOW)
    grid = [{"step_tstart": _ordinal(t)} for t in pd.date_range(w0, w1, freq="MS")]
    lake = {normalize_well_name(x) for x in LAKE_GAUGE_KEYS} | set(LAKE_GAUGE_KEYS)
    rows = []
    for k, col in sorted(lev_cols.items()):
        if k in lake or k not in loc.index:
            continue
        d = float(strip.distance(Point(loc.loc[k, "E"], loc.loc[k, "N"])))
        role = "near" if d <= E8F_NEAR_M else "placebo" if d > E8F_FAR_M else None
        if role is None:
            continue
        h = lev[col].dropna()
        hm = h.copy(); hm.index = hm.index + pd.offsets.MonthEnd(0)
        n_before, n_after = int((hm.index < w0).sum()), int((hm.index > w1).sum())
        row = {"well": k, "role": role, "control": k in E8F_CONTROL_WELLS, "dist_clearance_m": d,
               "n_before": n_before, "n_after": n_after}
        if min(n_before, n_after) < E8F_MIN_SIDE_MONTHS:
            row["skipped"] = f"fewer than {E8F_MIN_SIDE_MONTHS} months on one side"
            rows.append(row); continue
        info(f"E8f {k} ({role}, {d:.0f} m)")
        try:
            base = _ts_solve(_single(ps, hm, P, E, f"{k}_e8f0"), P)
            best, prof = _profile(lambda fx: _change_model(ps, hm, P, E, "step", f"{k}_e8f1", fx), P, grid)
            if best is None:
                raise RuntimeError("no profile point solved")
            o, se = best.parameters["optimal"], best.parameters["stderr"]
            a, s_ = float(o["step_A"]), float(se["step_A"])
            lo_t, hi_t = _interval(prof, "step_tstart")
            row.update(step_m=a, step_se_m=s_, step_lo95_m=a - 1.96 * s_, step_hi95_m=a + 1.96 * s_,
                       step_date=f"{_from_ordinal(best.parameters.loc['step_tstart', 'optimal']):%Y-%m}",
                       step_date_lo95=f"{_from_ordinal(lo_t):%Y-%m}", step_date_hi95=f"{_from_ordinal(hi_t):%Y-%m}",
                       bic_single=float(base.stats.bic()), bic_step=_bic_profiled(best, 1))
            row["dbic"] = row["bic_single"] - row["bic_step"]
            row["has_step"] = bool(row["dbic"] >= TWO_STORE_BIC_STRONG
                                   and (row["step_lo95_m"] > 0 or row["step_hi95_m"] < 0))
            if role == "near" and row["has_step"]:
                wg = [{"step_tstart": _ordinal(t)} for t in pd.date_range(*E8F_WIDE_WINDOW, freq=f"{E8F_WIDE_STEP_MONTHS}MS")]
                wb, wp = _profile(lambda fx: _change_model(ps, hm, P, E, "step", f"{k}_e8fw", fx), P, wg)
                if wb is not None:
                    wd = _from_ordinal(wb.parameters.loc["step_tstart", "optimal"])
                    row.update(wide_step_date=f"{wd:%Y-%m}", wide_step_m=float(wb.parameters.loc["step_A", "optimal"]),
                               wide_in_window=bool(w0 - pd.DateOffset(months=E8F_WIDE_STEP_MONTHS) <= wd <= w1 + pd.DateOffset(months=E8F_WIDE_STEP_MONTHS)),
                               wide_sse_ratio=float(wp["sse"].min() / prof["sse"].min()))
                    # second check: the wide step held at its date, a SECOND step profiled in the clearance window
                    t1_ = float(wb.parameters.loc["step_tstart", "optimal"])

                    def two(fx, _t1=t1_, _k=k):
                        ml = _change_model(ps, hm, P, E, "step", f"{_k}_e8f2", {"step_tstart": _t1})
                        ps.StepModel(ml, tstart=E8F_STEP_WINDOW[0], rfunc=ps.One(), name="clr")
                        ml.set_parameter("clr_tstart", initial=fx["clr_tstart"], vary=False)
                        return ml
                    g2 = [{"clr_tstart": _ordinal(t)} for t in pd.date_range(w0, w1, freq="MS")]
                    b2, p2 = _profile(two, P, g2)
                    if b2 is not None:
                        a2, s2 = float(b2.parameters.loc["clr_A", "optimal"]), float(b2.parameters.loc["clr_A", "stderr"])
                        dbic2 = _bic_profiled(wb, 1) - _bic_profiled(b2, 2)
                        row.update(step2_m=a2, step2_lo95_m=a2 - 1.96 * s2, step2_hi95_m=a2 + 1.96 * s2,
                                   step2_date=f"{_from_ordinal(b2.parameters.loc['clr_tstart', 'optimal']):%Y-%m}",
                                   step2_dbic=dbic2,
                                   step2_has=bool(dbic2 >= TWO_STORE_BIC_STRONG and (a2 - 1.96 * s2 > 0 or a2 + 1.96 * s2 < 0)))
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"[:200]
        rows.append(row)
    return pd.DataFrame(rows)


def e8f_verdict(tab: pd.DataFrame):
    from scipy.stats import spearmanr
    ok = tab[tab.get("has_step").notna()] if "has_step" in tab.columns else tab.iloc[0:0]
    ctrl = ok[ok["control"]]
    plc = ok[ok["role"] == "placebo"]
    near = ok[ok["role"] == "near"]
    t1 = bool(ctrl["has_step"].any()) if len(ctrl) else False
    frac = float(plc["has_step"].mean()) if len(plc) else np.nan
    t2 = bool(np.isfinite(frac) and frac <= E8F_PLACEBO_MAX_FRAC)
    rho = spearmanr(near["dist_clearance_m"], near["step_m"]) if len(near) > 2 else None
    verdict = ("site-wide 2015 shift" if not t2 else
               "clearance step at the controls" if t1 else "no clearance step at the controls")
    return verdict, {"test1": t1, "test2": t2, "placebo_frac": frac, "n_placebo": len(plc), "n_near": len(near),
                     "controls_tested": list(ctrl["well"]), "controls_with_step": list(ctrl[ctrl["has_step"]]["well"]),
                     "near_with_step": int(near["has_step"].sum()),
                     "near_step_wide_in_window": int(near.get("wide_in_window", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()),
                     "near_step2": int(near.get("step2_has", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()),
                     "controls_step2": list(ctrl[ctrl.get("step2_has", pd.Series(False, index=ctrl.index)).fillna(False).astype(bool)]["well"]),
                     "rho_step_distance": float(rho.statistic) if rho is not None else np.nan,
                     "p_step_distance": float(rho.pvalue) if rho is not None else np.nan}


def e8f_report(rr, tab, verdict, iv) -> None:
    rr.add("e8f_verdict", E8F_VERDICT[verdict], unit="code",
           note=f"{verdict} (2 step at the controls, 1 none, 0 site-wide shift; E8f, D-236)")
    rr.add("e8f_n_near", iv["n_near"], unit="count", note=f"wells within {E8F_NEAR_M:.0f} m of the shore clearance that could be tested")
    rr.add("e8f_near_with_step", iv["near_with_step"], unit="count", note="of those, wells with a step by the rule")
    rr.add("e8f_near_step_wide_in_window", iv["near_step_wide_in_window"], unit="count",
           note=f"of the near wells with a step, those whose step date profiled over {E8F_WIDE_WINDOW[0][:4]}-{E8F_WIDE_WINDOW[1][:4]} still lands in the clearance window (check, not the rule)")
    rr.add("e8f_near_step2", iv["near_step2"], unit="count",
           note="near wells with a clearance-window step IN ADDITION to their wide-window step (check, not the rule)")
    rr.add("e8f_controls_step2", len(iv["controls_step2"]), unit="count",
           note=f"of {', '.join(E8F_CONTROL_WELLS)}: controls with that additional step (check, not the rule)")
    rr.add("e8f_n_placebo", iv["n_placebo"], unit="count", note=f"placebo wells beyond {E8F_FAR_M:.0f} m that could be tested")
    rr.add("e8f_placebo_frac_with_step", iv["placebo_frac"], unit="fraction", note="share of placebo wells with a step (test 2)")
    rr.add("e8f_rho_step_distance", iv["rho_step_distance"], unit="rho", note="Spearman rho, step size against distance to the clearance, near wells (reported)")
    t = tab.set_index("well")
    for w in E8F_CONTROL_WELLS:
        if w in t.index and pd.notna(t.loc[w].get("step_m", np.nan)):
            rr.add(f"e8f_step_{w}_m", t.loc[w, "step_m"], unit="m", note=f"{w}: fitted step at {t.loc[w, 'step_date']} (95% {t.loc[w, 'step_lo95_m']:+.3f} to {t.loc[w, 'step_hi95_m']:+.3f} m)")
            rr.add(f"e8f_has_step_{w}", float(bool(t.loc[w, "has_step"])), unit="flag", note=f"{w}: step by the rule (BIC and interval)")
    if "wmc3" in t.index and pd.notna(t.loc["wmc3"].get("step_m", np.nan)):
        rr.add("e8f_step_wmc3_m", t.loc["wmc3", "step_m"], unit="m", note="WMC3 (clearfell impact): fitted step in the clearance window (reported)")


def plot_clearance_steps(tab) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    t = tab[tab.get("step_m").notna()] if "step_m" in tab.columns else tab.iloc[0:0]
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=160)
    for role, c in (("near", "#b2182b"), ("placebo", "0.5")):
        s = t[t["role"] == role]
        ax.errorbar(s["dist_clearance_m"], s["step_m"], yerr=1.96 * s["step_se_m"], fmt="o", ms=4, color=c,
                    ecolor=c, elinewidth=0.7, alpha=0.85, label=f"{role} wells")
        hs = s[s["has_step"].astype(bool)]
        ax.plot(hs["dist_clearance_m"], hs["step_m"], "o", ms=9, mfc="none", mec="k", lw=0.8)
    if "step2_m" in t.columns:
        s2 = t[t["step2_m"].notna()]
        ax.errorbar(s2["dist_clearance_m"] + 8, s2["step2_m"], yerr=[s2["step2_m"] - s2["step2_lo95_m"], s2["step2_hi95_m"] - s2["step2_m"]],
                    fmt="D", ms=4, color="#2166ac", ecolor="#2166ac", elinewidth=0.7,
                    label="near wells: a second step in the window, the wide-window step held (check)")
        hs2 = s2[s2["step2_has"].astype(bool)]
        ax.plot(hs2["dist_clearance_m"] + 8, hs2["step2_m"], "D", ms=10, mfc="none", mec="#2166ac", lw=0.8)
    for r in t[t["control"] | t["well"].isin(["wmc3", "ceh36", "ceh3"])].itertuples():
        ax.annotate(r.well.upper(), (r.dist_clearance_m, r.step_m), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.axhline(0, color="0.4", lw=0.7)
    ax.axvline(E8F_NEAR_M, color="0.7", lw=0.6, ls="--"); ax.axvline(E8F_FAR_M, color="0.7", lw=0.6, ls="--")
    ax.set_xlabel("distance to the 2014/15 shore clearance (m)")
    ax.set_ylabel("fitted step, Oct 2014 to Apr 2015 (m, 95%)")
    ax.set_title("E8f: a step at the clearance? Ringed: a step by the rule. Red: the rule's step; blue: the same "
                 "test after the 2008-11 step is allowed for", loc="left", fontsize=8)
    ax.grid(alpha=0.3); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(OUT_50_CLEARANCE_FIG, dpi=160); plt.close(fig)
    saved(OUT_50_CLEARANCE_FIG.name)


# ──────────────────────────────────────────────────────────────────────────────
# ── E8g (1.8.0, T-121, D-255): a store drawn down by the plantation? The pre-canopy test ───────────────
PRECANOPY_VERDICT = {"supported": 2, "not resolved": 1, "not supported": 0}


def canopy_share(t: pd.DatetimeIndex, planting: int, closure: int) -> np.ndarray:
    """The forest share of the coefficients: a logistic equal to PRECANOPY_W_TAILS at planting and at
    closure (planting + closure years). Ones throughout when `planting` is None (forest throughout)."""
    if planting is None:
        return np.ones(len(t))
    w0, w1 = PRECANOPY_W_TAILS
    k = (np.log(w1 / (1 - w1)) - np.log(w0 / (1 - w0))) / closure
    t_mid = planting + np.log(1 / w0 - 1) / k        # w(planting) = w0; = planting + closure/2 for symmetric tails
    yr = t.year + (t.dayofyear - 0.5) / 365.25
    return 1.0 / (1.0 + np.exp(-k * (np.asarray(yr) - t_mid)))


def precanopy_stress(P: pd.Series, E: pd.Series, b_an: pd.Series, b_fo: pd.Series, planting, closure) -> pd.Series:
    """R(t) = beta_1(t) P(t) - beta_2(t) PET(t), each coefficient moved along the canopy share from the
    open-dune analogue's to the forest cluster's (both at DRAINAGE_DATUM). beta_3 cannot vary inside a
    Pastas response, so the drainage time scales are fitted, as in E8."""
    w = canopy_share(P.index, planting, closure)
    b1 = (1 - w) * b_an["beta_1_recharge"] + w * b_fo["beta_1_recharge"]
    b2 = (1 - w) * b_an["beta_2_atmospheric_draw"] + w * b_fo["beta_2_atmospheric_draw"]
    E = E.reindex(P.index)
    return pd.Series(b1 * P.to_numpy() - b2 * E.to_numpy(), index=P.index, name="R").dropna()


def _stress_model(ps, head: pd.Series, R: pd.Series, double: bool, name: str,
                  slow_init=TWO_STORE_SLOW_INIT_DAYS, share_init=TWO_STORE_SLOW_SHARE_INIT):
    ml = ps.Model(head, name=name)
    rf = ps.DoubleExponential() if double else ps.Exponential()
    ps.StressModel(ml, R, rfunc=rf, name="rch", settings="prec")
    if double:
        ml.set_parameter("rch_a1", initial=TWO_STORE_FAST_INIT_DAYS,
                         pmin=TWO_STORE_FAST_BOUNDS_DAYS[0], pmax=TWO_STORE_FAST_BOUNDS_DAYS[1])
        ml.set_parameter("rch_a2", initial=slow_init,
                         pmin=TWO_STORE_SLOW_BOUNDS_DAYS[0], pmax=TWO_STORE_SLOW_BOUNDS_DAYS[1])
        ml.set_parameter("rch_alpha", initial=share_init, pmin=0.0, pmax=1.0)
    return ml


def _stress_fit(ps, head, R, double: bool, name: str, tmin=None, tmax=None):
    """Solved model; a two-store fit from every PRECANOPY_SLOW_STARTS_DAYS x PRECANOPY_SHARE_STARTS start,
    the lowest BIC kept (the fit is multi-modal). Returns (model, number of starts that converged)."""
    starts = ([(a, s) for a in PRECANOPY_SLOW_STARTS_DAYS for s in PRECANOPY_SHARE_STARTS] if double
              else [(TWO_STORE_SLOW_INIT_DAYS, TWO_STORE_SLOW_SHARE_INIT)])
    best, n_ok = None, 0
    for a, s in starts:
        try:
            ml = _ts_solve(_stress_model(ps, head, R, double, name, a, s), R, tmin, tmax)
        except Exception:
            continue
        n_ok += 1
        if best is None or float(ml.stats.bic()) < float(best.stats.bic()):
            best = ml
    if best is None:
        raise RuntimeError("no start converged")
    return best, n_ok


def precanopy(cl):
    """E8g (T-121): at each forest cluster centroid, the single and two-store responses to the effective
    recharge of a canopy closing along a logistic after planting, against the same with the forest
    coefficients throughout; every planting year x closure age. The rule was fixed before the run."""
    import pastas as ps
    ps.set_log_level("ERROR")
    ra = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    co = _model_a_store(pd.read_csv(OUT_03_MECHANISTIC_TABLE)).set_index("Cluster")   # 1.28.0: Model A
    if not np.allclose(co["drainage_datum_m"], DRAINAGE_DATUM):
        raise ValueError(f"{OUT_03_MECHANISTIC_TABLE.name} is not at DRAINAGE_DATUM")
    start = continuous_start(cl)
    P, E = spread_daily(cl, start)
    cases = [(None, None)] + [(p_, c_) for p_ in PRECANOPY_PLANTING_YEARS for c_ in PRECANOPY_CLOSURE_YEARS]
    rows = []
    for c, an in sorted(PRECANOPY_ANALOGUE.items()):
        if f"C{c}" not in ra.columns:
            continue
        hm = ra[f"C{c}"].dropna(); hm.index = hm.index + pd.offsets.MonthEnd(0)
        for planting, closure in cases:
            R = precanopy_stress(P, E, co.loc[an], co.loc[c], planting, closure)
            w_rec = float(canopy_share(pd.DatetimeIndex([hm.index[0]]), planting, closure)[0])
            for form, dbl in TS_FORMS:
                info(f"E8g C{c} {form} planting {planting or 'none'} closure {closure or '-'}")
                row = {"cluster": c, "analogue": an,
                       "case": "forest_throughout" if planting is None else f"{planting}_{closure}",
                       "planting_year": planting if planting is not None else np.nan,
                       "closure_years": closure if closure is not None else np.nan,
                       "form": form, "warmup_from": f"{start:%Y-%m}", "n_obs": int(hm.notna().sum()),
                       "w_at_record_start": w_rec}
                try:
                    ml, n_ok = _stress_fit(ps, hm, R, dbl, f"C{c}_{form}_{row['case']}")
                    o = ml.parameters["optimal"]
                    st = _residual_stats(ml, R, hm)
                    fitp = lambda tmin, tmax, d=dbl, nm=row["case"]: _stress_fit(
                        ps, hm, R, d, f"C{c}_{form}_{nm}_s", tmin, tmax)[0]
                    row["starts_converged"] = n_ok
                    sp = _split_nses(fitp, hm, R, CHANGE_SPLIT_DIRECTIONS)
                    row.update(bic=float(ml.stats.bic()), aic=float(ml.stats.aic()), rsq=float(ml.stats.rsq()),
                               fast_efold_months=float(o["rch_a1"] if dbl else o["rch_a"]) / DAYS_PER_MONTH,
                               slow_efold_months=float(o["rch_a2"]) / DAYS_PER_MONTH if dbl else np.nan,
                               slow_share=float(o["rch_alpha"]) if dbl else 0.0,
                               split_nse_fwd=sp["fwd"], split_nse_rule=sp["rule"],
                               early_resid_m=st["early_resid_m"], later_rmse_m=st["later_rmse_m"])
                    _identify(row, dbl)
                except Exception as exc:
                    row["error"] = f"{type(exc).__name__}: {exc}"[:200]
                rows.append(row)
    tab = pd.DataFrame(rows)
    # the rule: each pre-canopy two-store fit against the better (by BIC) forest-throughout fit
    tab["dbic_vs_forest"] = np.nan
    tab["case_pass"] = pd.Series([pd.NA] * len(tab), dtype="boolean")
    for c in tab["cluster"].unique():
        base = tab[(tab.cluster == c) & (tab.case == "forest_throughout") & tab["bic"].notna()]
        if base.empty:
            continue
        b = base.loc[base["bic"].idxmin()]
        tab.loc[tab.cluster == c, "baseline_form"] = b["form"]
        idx = tab.index[(tab.cluster == c) & (tab.case != "forest_throughout")]
        tab.loc[idx, "dbic_vs_forest"] = b["bic"] - tab.loc[idx, "bic"]
        for i in idx:
            r = tab.loc[i]
            if r["form"] != "double" or not np.isfinite(r.get("bic", np.nan)):
                continue
            t1 = bool(r["dbic_vs_forest"] >= TWO_STORE_BIC_STRONG)
            t2 = bool(np.isfinite(r["split_nse_rule"]) and r["split_nse_rule"] >= b["split_nse_rule"])
            t3 = bool(abs(r["early_resid_m"]) < abs(b["early_resid_m"]))
            tab.loc[i, ["test1_bic", "test2_split", "test3_early"]] = [t1, t2, t3]
            tab.loc[i, "case_pass"] = bool(t1 and t2 and t3)
    return tab


def precanopy_verdicts(tab: pd.DataFrame) -> dict:
    out = {}
    n_cases = len(PRECANOPY_PLANTING_YEARS) * len(PRECANOPY_CLOSURE_YEARS)
    for c in sorted(tab["cluster"].unique()):
        g = tab[(tab.cluster == c) & (tab.form == "double") & (tab.case != "forest_throughout")]
        npass = int(g["case_pass"].fillna(False).astype(bool).sum())
        complete = len(g) == n_cases and g["case_pass"].notna().all()
        v = ("supported" if complete and npass == n_cases else "not supported" if npass == 0 else "not resolved")
        out[c] = {"verdict": v, "n_pass": npass, "n_cases": n_cases,
                  "dbic_min": float(g["dbic_vs_forest"].min()) if len(g) else np.nan,
                  "dbic_max": float(g["dbic_vs_forest"].max()) if len(g) else np.nan}
    return out


def precanopy_report(rr, ver: dict) -> None:
    for c, v in ver.items():
        rr.add(f"precanopy_verdict_C{c}", PRECANOPY_VERDICT[v["verdict"]], unit="code",
               note=f"C{c}: {v['verdict']} (2 supported, 1 not resolved, 0 not supported); a store drawn down by "
                    f"the plantation, pre-canopy test E8g, strict rule fixed before the run (T-121, D-255)")
        rr.add(f"precanopy_n_cases_pass_C{c}", v["n_pass"], unit="count",
               note=f"C{c}: cases (of {v['n_cases']}, planting year x closure age) in which the pre-canopy two-store "
                    f"fit passes all three tests (E8g)")
        rr.add(f"precanopy_dbic_min_C{c}", v["dbic_min"], unit="BIC",
               note=f"C{c}: smallest BIC gain of the pre-canopy two-store fit over the forest-throughout fit, "
                    f"across the cases (E8g; positive favours the pre-canopy fit)")
        rr.add(f"precanopy_dbic_max_C{c}", v["dbic_max"], unit="BIC",
               note=f"C{c}: largest BIC gain of the pre-canopy two-store fit over the forest-throughout fit (E8g)")


# ──────────────────────────────────────────────────────────────────────────────
def main(no_fig: bool = False) -> int:
    banner("50d", "Two stores and non-climatic change (E8-E8g: D-231 to D-236, D-255)", version=__version__)
    DIR_50D.mkdir(parents=True, exist_ok=True)

    phase(1, "Inputs")
    lev, lev_cols, cl, master = load_inputs()
    info(f"{len(master)} reference wells; lengths {', '.join(LENGTHS)} (fitted monthly changes); "
         f"split {MODEL_AB_SPLIT_DATE}; stability tolerance {RECLEN_STABLE_TOL:g}")

    phase(2, "Two drainage time scales per cluster (1.3.0, E8, D-231)")
    ts_tab, ts_well, ts_nw, ts_start = two_store(lev, lev_cols, cl, master)
    ts_verdict, ts_per = two_store_verdict(ts_tab, ts_nw)
    for r in ts_per.itertuples():
        b = ts_tab[(ts_tab.cluster == r.cluster) & (~ts_tab.noise_ar1) & (ts_tab.form == "double")].iloc[0]
        step(f"C{r.cluster}: slow share {b.slow_share:.2f}, slow e-fold {b.slow_efold_months:.0f} months; "
             f"test 1 {'pass' if r.test1 else 'fail'}, test 2 "
             f"{'n/a' if pd.isna(r.test2) else ('pass' if r.test2 else 'fail')}, test 4 {'pass' if r.test4 else 'fail'}")
    if "double" in ts_nw:
        step(f"{TWO_STORE_CHECK_WELL}: single {'pass' if ts_nw['single']['pass'] else 'fail'}, "
             f"two stores {'pass' if ts_nw['double']['pass'] else 'fail'} (test 4b)")
    result("E8 verdict", f"{ts_verdict} (warm-up from {ts_start:%Y-%m})")
    ts_tab.to_csv(OUT_50_TWO_STORE, index=False); saved(f"{OUT_50_TWO_STORE.name} ({len(ts_tab)} rows)")
    if len(ts_well):
        ts_well.to_csv(OUT_50_TWO_STORE_WELL, index=False); saved(f"{OUT_50_TWO_STORE_WELL.name} ({len(ts_well)} rows)")

    phase(3, "A non-climatic change (E8b) and surface flow (E8c), per cluster (1.4.0, D-232)")
    cs_ch, cs_sf, cs_sims = change_and_surface(lev, lev_cols, cl, master)
    cs_vc, cs_pc, cs_date, cs_vs, cs_ps = change_surface_verdicts(cs_ch, cs_sf)
    for r in cs_pc.itertuples():
        step(f"C{r.cluster} E8b: best {getattr(r, 'best_form', '-')}, earns {'yes' if r.earns else 'no'}"
             + (f", change {r.tstart:%Y-%m}" if pd.notna(getattr(r, 'tstart', pd.NaT)) else ""))
    for r in cs_ps.itertuples():
        step(f"C{r.cluster} E8c: best {getattr(r, 'best_form', '-')}, passes {'yes' if r.passes else 'no'}")
    result("E8b verdict", f"{cs_vc}" + (f" (common date {cs_date:%Y-%m})" if pd.notna(cs_date) else ""))
    result("E8c verdict", cs_vs)
    cs_ch.to_csv(OUT_50_CHANGE, index=False); saved(f"{OUT_50_CHANGE.name} ({len(cs_ch)} rows)")
    cs_sf.to_csv(OUT_50_SURFACE, index=False); saved(f"{OUT_50_SURFACE.name} ({len(cs_sf)} rows)")

    phase(4, "Rain event structure (E8d), per winter and per cluster (1.5.0, D-234)")
    e8_prim, e8_inlong, e8_full = rain_events(E8D_PRIMARY_GAUGE)
    e8_chk, _, _ = rain_events(E8D_CHECK_GAUGE)
    e8_share = monthly_event_share(e8_inlong, e8_full)
    e8_st = event_stress(cl, e8_share)
    e8_verdict, e8_info = e8d_verdict(e8_prim, e8_chk, e8_st)
    tw = e8_prim.set_index("winter")
    for w in sorted(set(E8D_TEST_WINTERS) | set(E8D_LATER_WINTERS)):
        if w in tw.index:
            step(f"winter {w - 1}/{str(w)[2:]}: event share {tw.loc[w, 'event_share']:.2f} "
                 f"(baseline percentile {tw.loc[w, 'event_share_pctl']:.0f})")
    for r in e8_st.itertuples():
        step(f"C{r.cluster} E8d: earns {'yes' if r.earns else 'no'}")
    result("E8d verdict", e8_verdict)
    pd.concat([e8_prim, e8_chk], ignore_index=True).to_csv(OUT_50_RAIN_EVENTS, index=False)
    saved(f"{OUT_50_RAIN_EVENTS.name} ({len(e8_prim) + len(e8_chk)} rows)")
    e8_st.to_csv(OUT_50_EVENT_STRESS, index=False); saved(f"{OUT_50_EVENT_STRESS.name} ({len(e8_st)} rows)")

    phase(5, "The felling north of NW9 and its regrowth (E8e), per well (1.6.0, D-235)")
    fe_tab, fe_nw9 = felling_by_well(lev, lev_cols, cl)
    fe_verdict, fe_info, fe_timing = e8e_tests(fe_tab, fe_nw9)
    step(f"place: rho {fe_info['rho_felling']:+.2f} (p {fe_info['p_felling']:.3f}) against the felling, "
         f"{fe_info['rho_coast']:+.2f} (p {fe_info['p_coast']:.3f}) against the coast, n {fe_info['n']}; "
         f"test 1 {'pass' if fe_info['test1'] else 'fail'}")
    step(f"timing: {E8E_CHECK_WELL} half year {fe_info['nw9_half_year']}, canopy half year "
         f"{fe_info['canopy_half_year']:.1f}; test 2 {'pass' if fe_info['test2'] else 'fail'}")
    step(f"control: open-dune wells beyond {E8E_FAR_M:.0f} m, median excess {fe_info['median_far_open_m']:+.3f} m "
         f"(n {fe_info['n_far_open']}); near wells {fe_info['median_near_m']:+.3f} m (n {fe_info['n_near']})")
    step(f"checks: distances rho {fe_info['rho_distances']:+.2f}; partial felling {fe_info['partial_felling']:+.2f}, "
         f"coast {fe_info['partial_coast']:+.2f}; open-dune wells alone {fe_info['rho_open_felling']:+.2f} (n {fe_info['n_open']})")
    result("E8e verdict", fe_verdict)
    fe_tab.to_csv(OUT_50_FELLING_DIST, index=False); saved(f"{OUT_50_FELLING_DIST.name} ({len(fe_tab)} rows)")
    fe_timing.to_csv(OUT_50_NW9_TIMING, index=False); saved(f"{OUT_50_NW9_TIMING.name} ({len(fe_timing)} rows)")

    phase(6, "The 2014/15 shore clearance: a step in the wells around it? (E8f, 1.7.0, D-236)")
    cf_tab = clearance_steps(lev, lev_cols, cl)
    cf_verdict, cf_info = e8f_verdict(cf_tab)
    for r in cf_tab[cf_tab["control"]].itertuples():
        if pd.notna(getattr(r, "step_m", np.nan)):
            step(f"{r.well} ({r.dist_clearance_m:.0f} m): step {r.step_m:+.3f} m at {r.step_date}, dBIC {r.dbic:.1f}; "
                 f"{'a step' if r.has_step else 'no step'} by the rule")
    for r in cf_tab[cf_tab.get("wide_step_date", pd.Series(index=cf_tab.index, dtype=object)).notna()].itertuples():
        step(f"  {r.well}: date free over {E8F_WIDE_WINDOW[0][:4]}-{E8F_WIDE_WINDOW[1][:4]} -> {r.wide_step_date} "
             f"({r.wide_step_m:+.3f} m){'' if r.wide_in_window else ', outside the clearance window'}; "
             + (f"a second step in the window {r.step2_m:+.3f} m, {'a step' if r.step2_has else 'no step'} by the rule"
                if pd.notna(getattr(r, "step2_m", np.nan)) else "second step not fitted"))
    step(f"near wells with a step: {cf_info['near_with_step']} of {cf_info['n_near']}; placebo "
         f"{cf_info['placebo_frac']:.2f} of {cf_info['n_placebo']} (test 2 {'pass' if cf_info['test2'] else 'fail'})")
    result("E8f verdict", cf_verdict)
    cf_tab.to_csv(OUT_50_CLEARANCE_STEP, index=False); saved(f"{OUT_50_CLEARANCE_STEP.name} ({len(cf_tab)} rows)")

    phase(7, "A store drawn down by the plantation? The pre-canopy test (E8g, 1.8.0, T-121, D-255)")
    pc_tab = precanopy(cl)
    pc_ver = precanopy_verdicts(pc_tab)
    for r in pc_tab[pc_tab["form"] == "double"].itertuples():
        if pd.notna(getattr(r, "bic", np.nan)):
            step(f"C{r.cluster} {r.case}: slow share {r.slow_share:.2f}, slow e-fold {r.slow_efold_months:.0f} months, "
                 f"dBIC {r.dbic_vs_forest:+.1f}, split NSE {r.split_nse_rule:.3f}, early residual {r.early_resid_m:+.3f} m"
                 + ("" if pd.isna(r.case_pass) else f"; {'pass' if r.case_pass else 'fail'}"))
    for c, v in pc_ver.items():
        result(f"E8g verdict C{c}", f"{v['verdict']} ({v['n_pass']} of {v['n_cases']} cases pass)")
    pc_tab.to_csv(OUT_50_PRECANOPY, index=False); saved(f"{OUT_50_PRECANOPY.name} ({len(pc_tab)} rows)")

    phase(8, "Outputs")
    rr = ReportNumbers()
    two_store_report(rr, ts_tab, ts_per, ts_nw, ts_verdict)
    change_surface_report(rr, cs_vc, cs_pc, cs_date, cs_vs, cs_ps)
    e8d_report(rr, e8_prim, e8_chk, e8_st, e8_verdict, e8_info)
    e8e_report(rr, fe_verdict, fe_info)
    e8f_report(rr, cf_tab, cf_verdict, cf_info)
    precanopy_report(rr, pc_ver)
    rr.save(OUT_50D_REPORT_NUMBERS); saved(f"{OUT_50D_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    if not no_fig:
        plot_two_store(ts_tab, ts_well, ts_nw, ts_start)
        plot_change_surface(cs_ch, cs_sf, cs_sims, cs_pc, cs_ps)
        plot_rain_events(e8_prim, e8_chk)
        plot_felling(fe_tab, fe_timing, fe_info)
        plot_clearance_steps(cf_tab)
    done("50d")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Two stores and non-climatic change (E8-E8g: D-231 to D-236, D-255)")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figure")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
