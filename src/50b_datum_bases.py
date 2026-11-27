"""
50b_datum_bases.py — Which datum and drainage base the record supports (D-225, D-229, D-286, D-287).

Script 50 suite, step 50b (J-15, T-208; Martin 2026-11-24: five families, numbered 50a-50e,
all opt-in). Split from 50_record_length.py 1.30.0, whose full version history is kept in git and in
50a_record_length.py; every function moved whole with its dated comments. Shared helpers live in
utils/reclen_common.py.
"""
from __future__ import annotations

__version__ = "1.2.0"  # 2026-11-27 (D-349 (1), A3): every fit states its window; the levels come cut at RECORD_FIT_START from reclen_common.load_inputs() 1.1.0, so E6's and the split series' reverse tests score 2010-17, not 2005-17 (forward train 2010-17); the full-record bases are D-347's; the split figure's panel titles say so. Was "1.1.0"  # 2026-11-27 (D-348): the E17 cluster bases, cluster table and per-cluster verdict tests, and the per-cluster e-fold medians from cluster-level wells (site-wide counts keep every well); cluster loop over CLUSTER_LABELS, not range(1, 6). Was "1.0.0"  # Hollingham (2026) - 2026-11-24 (J-15, T-208). Split from Script 50 1.30.0.

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
    DIR_50B, OUT_50B_REPORT_NUMBERS, OUT_50_PER_WELL, OUT_50_BY_CLUSTER, OUT_50_CCW, OUT_50_STABLE, OUT_50_FIG,
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
    RECORD_START_DISPLAY, REFERENCE_CUTOFF_DATE, RECORD_FIT_START,
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
# 1.1.0 (D-225): which datum does the drier past support?
# ──────────────────────────────────────────────────────────────────────────────
def datum_grid() -> np.ndarray:
    """Script 03's datum sweep: DATUM_SWEEP_MIN_M to DATUM_SWEEP_MAX_M by DATUM_SWEEP_STEP_M."""
    return np.round(np.arange(DATUM_SWEEP_MIN_M, DATUM_SWEEP_MAX_M + DATUM_SWEEP_STEP_M / 2,
                              DATUM_SWEEP_STEP_M), 6)


def ccw_by_datum(lev, lev_cols, cl, loc_forest) -> pd.DataFrame:
    """E5: Model A refitted at every datum (comparison window and full record) and run through
    Script 39's hindcast at that datum over the CCW 1989-96 readings."""
    if not (paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()):
        warn("CCW historic inputs not present — the datum hindcast is skipped")
        return pd.DataFrame()
    obs, cmap = load_ccw()
    md = _model_a_store(pd.read_csv(INT_MASTER_DATA))
    md["k"] = md["Name_Original"].astype(str).str.lower().str.strip()
    md = md.set_index("k")
    adm = usable_codes(cmap, md, obs)
    adm = adm[adm["admitted"]]
    clh = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    p_mean, pet_mean = float(clh["P_m"].mean()), float(clh["PET"].mean())
    first_month, last_month = obs["month"].min(), obs["month"].max()
    rows = []
    for r in track(list(adm.itertuples()), "CCW by datum", min_seconds=5.0):
        col = lev_cols.get(normalize_well_name(r.well))
        if col is None:
            continue
        o, _n = observed_series(obs, r.code, r.datum_offset_m)
        if o.empty:
            continue
        h = lev[col].dropna()
        db = dry_bounds(col)                             # 1.24.0 (D-322): censored, calendar windows
        for D in datum_grid():
            for basis, win in (("comparison_window", LCSC_DATA_LIMIT), ("full_record", None)):
                f = _censored_well_fit(h, cl, db, win, False, datum=float(D), start=RECORD_FIT_START)
                row = {"well": r.well, "code": r.code, "cluster": int(md.loc[r.well, "Cluster"]),
                       "in_forest": bool(loc_forest.get(normalize_well_name(r.well), False)),
                       "basis": basis, "datum_m": float(D)}
                if f is None or not (f["beta_3_drainage"] > 0):
                    rows.append(row)
                    continue
                betas = (f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"])
                h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=float(D))
                pred, _s = hindcast_well(clh, betas, h0, first_month, last_month, 1.0, drainage_datum=float(D))
                common = o.index.intersection(pred.index)
                nse, rmse, bias = get_metrics(o.loc[common], pred.loc[common])
                oc, pc = o.loc[common].values, pred.loc[common].values
                off = float(np.mean(pc - oc))
                den = float(np.sum((oc - oc.mean()) ** 2))
                row.update({"beta_3": f["beta_3_drainage"], "p_beta_3": f["pvalue_beta_3"], "n_fit": int(f["n"]),
                            "n_test": int(len(common)), "nse": float(nse), "bias_m": float(bias),
                            "pearson_r": float(np.corrcoef(oc, pc)[0, 1]) if len(oc) > 2 else np.nan,
                            "nse_bias_removed": (1.0 - float(np.sum((oc - (pc - off)) ** 2)) / den) if den > 0 else np.nan})
                rows.append(row)
    return pd.DataFrame(rows)


def split_by_datum(lev, lev_cols, cl, master) -> pd.DataFrame:
    """E6: Script 48's split-sample test for Model A at every datum."""
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    rows = []
    for _, r in track(list(master.iterrows()), "split by datum", min_seconds=5.0):
        col = lev_cols.get(r["_n"])
        if col is None:
            continue
        h = lev[col].dropna()
        pre_h, post_h = h[h.index < split], h[h.index >= split]   # D-349 (A3): h is cut at RECORD_FIT_START (load_inputs), so "pre" is 2010-17
        for D in datum_grid():
            for direction, tr, te in (("fwd", pre_h, post_h), ("rev", post_h, pre_h)):
                fr = build_ssm_frame(tr, cl, lag=HEADLINE_LAG, drainage_datum=float(D))
                f = fit_frame(fr, False)
                res = free_run(te, cl, f, False, base=float(D))
                rows.append({"well": r["_n"], "cluster": int(r["Cluster"]), "datum_m": float(D),
                             "direction": direction, "nse": res["nse"], "n_test": res["n_test"]})
    return pd.DataFrame(rows)


def split_series(lev, lev_cols, cl, master, mhw: dict | None = None) -> pd.DataFrame:
    """J-6: the Jan-2018 split-sample free run kept MONTH BY MONTH, for BOTH forms.

    `split_by_datum` (E6) sweeps the datum and keeps only the NSE, so scenario 1 -- the case INSIDE
    the recorded climate, the one Model B is supposed to win -- has 10,032 rows of skill and no
    series anyone can plot. Every hindcast figure in the corpus therefore shows ONE form, while the
    argument the figures are there to support is that the two forms answer different questions.

    Here the datum is the project's (Model A is run at DRAINAGE_DATUM; Model B at the datum its own
    fitted intercept implies, via run_datum) and the sweep is dropped, so the output is one row per
    well, form, direction and month rather than a grid. Emit-only: the fit, the free run and the
    datum convention are exactly `split_by_datum`'s, so the NSE recomputed from these series
    reproduces 50_07 at DRAINAGE_DATUM for Model A.

    1.25.0 (D-332): with `mhw` ({well: depth to mean high water}), the MHW form "M" is kept too: Model A
    fitted on a frame built at the well's own MHW datum and run there.
    """
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    mhw = mhw or {}
    rows = []
    for _, r in master.iterrows():
        col = lev_cols.get(r["_n"])
        if col is None:
            continue
        h = lev[col].dropna()
        pre_h, post_h = h[h.index < split], h[h.index >= split]   # D-349 (A3): h is cut at RECORD_FIT_START (load_inputs), so "pre" is 2010-17
        D_m = mhw.get(r["_n"])
        for direction, tr, te in (("fwd", pre_h, post_h), ("rev", post_h, pre_h)):
            fr = build_ssm_frame(tr, cl, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM)
            forms = [("A", False, DRAINAGE_DATUM, fr), ("B", True, DRAINAGE_DATUM, fr)]
            if D_m is not None and np.isfinite(D_m):
                forms.append((FORM_MHW, False, float(D_m),
                              build_ssm_frame(tr, cl, lag=HEADLINE_LAG, drainage_datum=float(D_m))))
            for form, intercept, D, fr_ in forms:
                f = fit_frame(fr_, intercept)
                if f is None:
                    continue
                t = te.dropna()
                if len(t) < MODEL_AB_MIN_TEST_MONTHS + 1:
                    continue
                months = pd.date_range(t.index[0], t.index[-1], freq="MS")
                clim = cl.reindex(months)
                if clim[["P_m", "PET"]].iloc[1:].isna().any().any():
                    continue
                sim = pd.Series(simulate_ssm(float(t.iloc[0]), clim["P_m"].values[1:],
                                             clim["PET"].values[1:], f["beta_1_recharge"],
                                             f["beta_2_atmospheric_draw"], f["beta_3_drainage"],
                                             drainage_datum=run_datum(f, intercept, D)),
                                index=months[1:])
                obs = t.iloc[1:]
                for m in sim.index:
                    if m not in obs.index:
                        continue
                    rows.append({"well": r["_n"], "cluster": int(r["Cluster"]), "form": form,
                                 "direction": direction, "month": m.strftime("%Y-%m"),
                                 "observed_m": float(obs.loc[m]), "predicted_m": float(sim.loc[m])})
    return pd.DataFrame(rows)


def plot_split_series(series: pd.DataFrame) -> None:
    """J-6: the January 2018 split drawn, BOTH forms, BOTH directions.

    1a (backward) is the comparable case: fitted on 2018-26 and run back over 2010-17, the same
    shape of test as the 1989-96 and 1951-53 hindcasts, which also run modern coefficients into an
    earlier period. 1b (forward) is the forecasting case -- fitted on 2010-17 and run forward --
    and is the only one of the four that tests the model the way it would actually be used.
    1a leads because it is the one scenarios 2 and 3 can be read against.

    THE WELL SHOWN IS THE CLUSTER'S MEDIAN-NSE WELL, NOT ITS LONGEST. The first version of this
    figure took the well with the most test months, and at C4 that well (ceh34, Model A 0.06 /
    Model B 0.38) gave the OPPOSITE ranking to its own cluster (median A 0.21 / B 0.08). C4 is
    wildly heterogeneous -- ceh14 scores -22.3 -- so a single well cannot stand for it honestly
    unless it is chosen to sit in the middle, and the cluster medians are annotated beside it.
    1.26.0 (D-332): the median is taken over Model B's NSE (it was Model A's), Model B being the model.
    """
    if series is None or series.empty:
        return
    import matplotlib                                  # deferred, as every figure here does
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    apply_house_style()                                # T-178: the house style, not an inline dict

    def _nse(g):
        o, p = g["observed_m"].values, g["predicted_m"].values
        return 1 - ((o - p) ** 2).sum() / ((o - o.mean()) ** 2).sum()

    # 1.2.0 (D-349, A3): both sides lie on D-347's window (reclen_common.load_inputs cuts the levels at 2010)
    panels = [("rev", "1a \u2014 backward: fitted 2018\u201326, run back over 2010\u201317 "
                      "(the case scenarios 2 and 3 compare with)"),
              ("fwd", "1b \u2014 forward: fitted 2010\u201317, run forward over 2018\u201326 "
                      "(the forecasting case)")]
    clusters = sorted(series["cluster"].unique())
    fig, axes = plt.subplots(len(clusters), 2, figsize=(14.0, 2.7 * len(clusters)), squeeze=False)

    # ONE SHARED Y SCALE ON EVERY PANEL (Martin, 2026-11-07), so the clusters can be read against
    # one another rather than each against its own stretch. He asked for 0 to -2; that would clip
    # real data on 7 of the 10 panels -- C1's median well reaches +0.71 m, water ABOVE ground,
    # which is the ecologically interesting part, and C4's forward well reaches -2.60 m. So the
    # range is taken from the plotted series and rounded outward to the half metre: same scale
    # everywhere, nothing hidden.
    _plotted = []
    for direction, _ in panels:
        d_ = series[series["direction"] == direction]
        for cid in clusters:
            dc = d_[d_["cluster"] == cid]
            if dc.empty:
                continue
            per_ = {w: _nse(g) for w, g in dc[dc["form"] == "B"].groupby("well")}   # 1.26.0: by Model B
            w_ = min(per_, key=lambda k: abs(per_[k] - np.median(list(per_.values()))))
            g_ = dc[dc["well"] == w_]
            _plotted += [g_["observed_m"].min(), g_["observed_m"].max(),
                         g_["predicted_m"].min(), g_["predicted_m"].max()]
    ylo = np.floor(min(_plotted) * 2) / 2 if _plotted else -3.0
    yhi = np.ceil(max(_plotted) * 2) / 2 if _plotted else 1.0

    for col, (direction, head) in enumerate(panels):
        d = series[series["direction"] == direction]
        axes[0][col].set_title(head, fontsize=9, loc="left")
        for row, cid in enumerate(clusters):
            ax = axes[row][col]
            dc = d[d["cluster"] == cid]
            if dc.empty:
                ax.set_visible(False)
                continue
            per = {w: _nse(g) for w, g in dc[dc["form"] == "B"].groupby("well")}    # 1.26.0 (D-332): by Model B
            med = {f: (float(np.median([_nse(g) for _, g in dc[dc["form"] == f].groupby("well")]))
                       if (dc["form"] == f).any() else np.nan)
                   for f in ("A", "B", FORM_MHW)}
            # the median-NSE well stands for the cluster
            w = min(per, key=lambda k: abs(per[k] - np.median(list(per.values()))))
            g = dc[dc["well"] == w]
            obs = g[g["form"] == "B"][["month", "observed_m"]].drop_duplicates("month")
            ax.plot(pd.to_datetime(obs["month"]), obs["observed_m"].values, color="black",
                    lw=1.7, label="observed", zorder=3)
            # 1.25.0 (D-332): the MHW form beside the other two; each line's own NSE moves into the title,
            # and the one legend goes below the panels (no legend over the data)
            _own = []
            for form, colr, lab in (("A", "#c2452d", "Model A, floor 3.7 m"),
                                    (FORM_MHW, "#d9822b", "Model A, floor at mean high water"),
                                    ("B", "#2b6cb0", "Model B")):
                f_ = g[g["form"] == form].drop_duplicates("month")
                if f_.empty:
                    continue
                ax.plot(pd.to_datetime(f_["month"]), f_["predicted_m"].values, color=colr,
                        lw=1.2, alpha=0.9, label=lab)
                _own.append(f"{'A MHW' if form == FORM_MHW else form} {_nse(f_):.2f}")
            ax.set_title((head + "\n" if row == 0 else "")      # row 0 carries the column's heading too
                         + f"C{int(cid)} \u2014 {w} (median well): {'  '.join(_own)}\n"
                         f"cluster median NSE: A 3.7 m {med['A']:.2f}  A MHW {med[FORM_MHW]:.2f}  B {med['B']:.2f}",
                         fontsize=8, loc="left")
            ax.set_ylabel("head (m)", fontsize=8)
            ax.set_ylim(ylo, yhi)                      # the shared scale
            ax.axhline(0.0, color="#888888", lw=0.8, ls=":", zorder=1)   # ground surface
    _h = {}
    for a in axes.ravel():
        for hh, ll in zip(*a.get_legend_handles_labels()):
            _h.setdefault(ll, hh)
    fig.legend(list(_h.values()), list(_h.keys()), loc="lower center", ncol=4, frameon=False, fontsize=9)
    fig.suptitle("Scenario 1 \u2014 the modern split at January 2018, three forms, both directions\n"
                 "the well shown is each cluster's MEDIAN-NSE well (Model B); the cluster medians are given above it",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    render_figure(fig, OUT_50_SPLIT_FIG)
    plt.close(fig)


def scenario_scales_12(s: dict) -> tuple[np.ndarray, np.ndarray]:
    """The UKCP18 seasonal multipliers of one scenario as 12 monthly factors for P and PET: winter months
    take the winter factor, summer months the summer factor, the shoulder months the mean of the two."""
    sP, sPET = np.ones(12), np.ones(12)
    for m in WINTER_WET_CLIMATE_MONTHS:
        sP[m - 1], sPET[m - 1] = s["sP_w"], s["sPET_w"]
    for m in SUMMER_DRY_CLIMATE_MONTHS:
        sP[m - 1], sPET[m - 1] = s["sP_s"], s["sPET_s"]
    for m in range(1, 13):
        if m not in WINTER_WET_CLIMATE_MONTHS and m not in SUMMER_DRY_CLIMATE_MONTHS:
            sP[m - 1], sPET[m - 1] = 0.5 * (s["sP_w"] + s["sP_s"]), 0.5 * (s["sPET_w"] + s["sPET_s"])
    return sP, sPET


def water_balance_report(rr, cl) -> None:
    """1.15.0: the annual water-balance shift (P - PET, mm/yr) each UKCP18 scenario applies to the modern
    climatology the projections scale, beside the shift of the CCW 1989-96 epoch from the same modern mean,
    so Paper M can say which scenario the drier-decade hindcast has tested (D-279)."""
    clim = cl.loc[RECORD_START_DISPLAY:REFERENCE_CUTOFF_DATE]
    P12 = clim.groupby(clim.index.month)["P_m"].mean().reindex(range(1, 13)).values
    PET12 = clim.groupby(clim.index.month)["PET"].mean().reindex(range(1, 13)).values
    base = float(np.sum(P12 - PET12)) * 1000.0
    for scen in UKCP18_SCENARIOS:
        sP, sPET = scenario_scales_12(UKCP18_SCENARIOS[scen])
        rr.add(f"projection_{scen}_annual_wb_shift_mm_yr", float(np.sum(P12 * sP - PET12 * sPET)) * 1000.0 - base,
               unit="mm/yr", note=f"UKCP18 {scen} change in annual P - PET applied to the modern monthly climatology "
                                  f"({RECORD_START_DISPLAY[:7]} to {REFERENCE_CUTOFF_DATE[:7]})")
    if paths.CCW_DEPTHS.exists():
        months = pd.read_csv(paths.CCW_DEPTHS)["month"].dropna()
        ep = cl.loc[f"{months.min()}-01":f"{months.max()}-01"]
        rr.add("ccw_epoch_annual_wb_shift_mm_yr", float((ep["P_m"] - ep["PET"]).mean() - (clim["P_m"] - clim["PET"]).mean()) * 12000.0,
               unit="mm/yr", note=f"annual P - PET over the CCW epoch ({months.min()} to {months.max()}, n = {len(ep)} months) "
                                  "less the modern mean, as 12 x the monthly mean difference")


def ddp_identity_check() -> float:
    """1.16.0: sustained_monthly_response_ddp at 1/L_E = 0 against the closed form, over a small grid of
    coefficients spanning the fitted range and both scenarios, with and without interception.
    1.27.0 (D-332): kept at DRAINAGE_DATUM on purpose. It checks the function, not a fitted set: at
    1/L_E = 0 the model is linear and the sustained response does not depend on the datum (or on α),
    so any datum tests the same identity."""
    P12 = np.linspace(0.04, 0.12, 12); PET12 = np.linspace(0.005, 0.09, 12)
    worst = 0.0
    for scen in UKCP18_SCENARIOS:
        sP, sPET = scenario_scales_12(UKCP18_SCENARIOS[scen])
        for b1, b2, b3 in ((4.5, 0.9, 0.09), (3.7, 1.6, 0.06), (2.4, 2.6, 0.012)):
            for I_ in (0.0, FOREST_INTERCEPTION):
                cf = sustained_monthly_response(b3, climate_forcing_change_12(b1, b2, P12, PET12, sP, sPET, interception=I_))
                dd = sustained_monthly_response_ddp(b1, b2, b3, 0.0, P12, PET12, sP, sPET, DRAINAGE_DATUM, interception=I_)[0]
                worst = max(worst, float(np.max(np.abs(cf - dd))))
    return worst


def ddp_sets():
    """1.27.0 (D-332): Script 15's identified per-well depth-dependent sets (15_05, comparison window,
    cluster inv_L_E) as {well: (b1, b2, b3, inv_L_E, z)}, z the set's Model B implied base
    (implied_datum_m; DRAINAGE_DATUM for a 15_05 written before Script 15 1.11.0, which was Model A).
    Returns (sets, excluded) with excluded {well: z} for the sets whose base is not below ground."""
    if not OUT_15_DDP_PER_WELL.exists():
        return {}, {}
    _d = pd.read_csv(OUT_15_DDP_PER_WELL)
    _d = _d[_d["level"] == "well"]
    z = (pd.to_numeric(_d["implied_datum_m"], errors="coerce") if "implied_datum_m" in _d.columns
         else pd.Series(float(DRAINAGE_DATUM), index=_d.index))
    below = z > 0
    excluded = {str(w): float(v) for w, v in zip(_d.loc[~below, "well"], z[~below])}
    keep = _d["identified"].astype(bool) & below
    sets = {str(w): (float(a), float(b_), float(c), float(k), float(zz))
            for w, a, b_, c, k, zz in zip(_d.loc[keep, "well"], _d.loc[keep, "b1"], _d.loc[keep, "b2"],
                                          _d.loc[keep, "b3"], _d.loc[keep, "inv_L_E"], z[keep])}
    return sets, excluded


def projection_by_datum(lev, lev_cols, cl, master, loc_forest) -> pd.DataFrame:
    """E7: the UKCP18 sustained level response (Script 19's functions, climatology, seasons and
    forest interception) on Model A's comparison-window fit at every datum, where Model B also
    projects the well (D-224 pairing), with the room left above the datum at the projected summer
    minimum. Model B's response is carried on each row for the pair."""
    clim = cl.loc[RECORD_START_DISPLAY:REFERENCE_CUTOFF_DATE]
    P12 = clim.groupby(clim.index.month)["P_m"].mean().reindex(range(1, 13)).values
    PET12 = clim.groupby(clim.index.month)["PET"].mean().reindex(range(1, 13)).values
    seasons = {"annual": list(range(1, 13)), "winter": list(WINTER_WET_CLIMATE_MONTHS),
               "summer": list(SUMMER_DRY_CLIMATE_MONTHS)}
    mb = pd.read_csv(OUT_03_MODEL_B_PERSISTENCE)
    mb = mb[mb["level"] == "well"].copy()
    mb["_n"] = mb["well"].astype(str).apply(normalize_well_name)
    mb = mb.set_index("_n")
    # 1.16.0 (D-280): the depth-dependent set per well (Script 15, comparison window, cluster inv_L_E),
    # projected at the project datum only -- the form is fitted on the network datum, not swept.
    dd, _ = ddp_sets()                                  # 1.27.0 (D-332): each set at its implied base
    rows = []
    for _, r in track(list(master.iterrows()), "projection by datum", min_seconds=5.0):
        col = lev_cols.get(r["_n"])
        if col is None or r["_n"] not in mb.index:
            continue
        b = mb.loc[r["_n"]]
        if not response_identified(b["beta_3_B"], b["pvalue_beta_3_B"], b["n"], 4)[0]:
            continue                                    # D-224: a pair only where Model B projects
        h = lev[col].dropna()
        hs = h[h.index.month.isin(list(SUMMER_DRY_CLIMATE_MONTHS))]
        summer_min = float(hs.groupby(hs.index.year).min().mean()) if len(hs) else np.nan
        I_ = FOREST_INTERCEPTION if loc_forest.get(r["_n"], False) else 0.0
        db = dry_bounds(col)                            # 1.18.0 (D-281): dry months censored
        db = db if len(db) else None
        for D in datum_grid():
            try:
                f = fit_ssm(h, cl, lag=HEADLINE_LAG, window=LCSC_DATA_LIMIT, drainage_datum=float(D),
                            min_obs=RECLEN_MIN_FIT_MONTHS, dry_bound=db,
                            start=RECORD_FIT_START)   # 1.2.0 (D-349 (1)): the comparison window lies inside it
            except Exception:
                f = None
            if f is None or not response_identified(f["beta_3_drainage"], f["pvalue_beta_3"], f["n"], 3)[0]:
                continue
            for scen in UKCP18_SCENARIOS:
                sP, sPET = scenario_scales_12(UKCP18_SCENARIOS[scen])
                ssA = sustained_monthly_response(f["beta_3_drainage"], climate_forcing_change_12(
                    f["beta_1_recharge"], f["beta_2_atmospheric_draw"], P12, PET12, sP, sPET, interception=I_))
                ssB = sustained_monthly_response(b["beta_3_B"], climate_forcing_change_12(
                    b["beta_1_B"], b["beta_2_B"], P12, PET12, sP, sPET, interception=I_))
                ssD = None
                if np.isclose(D, DRAINAGE_DATUM) and r["_n"] in dd:
                    d1, d2, d3, dk, dz = dd[r["_n"]]
                    ssD = sustained_monthly_response_ddp(d1, d2, d3, dk, P12, PET12, sP, sPET,
                                                         dz, interception=I_)[0]
                for sea, months in seasons.items():
                    idx = [m - 1 for m in months]
                    row = {"well": r["_n"], "cluster": int(r["Cluster"]), "datum_m": float(D),
                           "scenario": scen, "season": sea, "beta_3": f["beta_3_drainage"],
                           "fall_model_a_m": float(np.mean(ssA[idx])), "fall_model_b_m": float(np.mean(ssB[idx])),
                           "fall_ddp_m": float(np.mean(ssD[idx])) if ssD is not None else np.nan}
                    if sea == "summer":
                        row["room_left_m"] = float(D + summer_min + np.mean(ssA[idx]))
                    rows.append(row)
    return pd.DataFrame(rows)


def supported_datum(ccw: pd.DataFrame, subset=None, metric="nse"):
    """The rule fixed before the run (D-225): the datum maximizing the median CCW NSE on the
    comparison-window fits, and every datum within RECLEN_DATUM_NSE_TOL of that maximum. With
    metric='abs_bias', the datum minimizing the median |bias| and the datums within the same
    tolerance (in metres) of that minimum — reported as a check, not as the rule."""
    c = ccw[(ccw["basis"] == "comparison_window") & ccw["nse"].notna()]
    if subset is not None:
        c = c[subset(c)]
    if c.empty:
        return np.nan, np.nan, np.nan, pd.Series(dtype=float)
    if metric == "nse":
        med = c.groupby("datum_m")["nse"].median()
        best = float(med.idxmax())
        band = med[med >= med.max() - RECLEN_DATUM_NSE_TOL].index
    else:
        med = c.assign(ab=c["bias_m"].abs()).groupby("datum_m")["ab"].median()
        best = float(med.idxmin())
        band = med[med <= med.min() + RECLEN_DATUM_NSE_TOL].index
    return best, float(min(band)), float(max(band)), med


# ──────────────────────────────────────────────────────────────────────────────
# E9: Ranwell 1951-53, the second drier epoch (1.2.0, D-229)
# ──────────────────────────────────────────────────────────────────────────────
RANWELL_DRY_YEAR = 1953          # Ranwell's dry year: below the surface at the sites read through it (D-059)


VERDICT_CODE = {"consistent": 1, "does not discriminate": 0, "disagrees": -1}


def ranwell_by_datum(lev, lev_cols, cl) -> pd.DataFrame:
    """E9: every Script 44 pairing, Model A at every datum and Model B, on the comparison window and the
    full record, hindcast from the start of the climate record and scored as Script 44 scores it."""
    if not (RANWELL_LEVELS.exists() and OUT_44_METRICS.exists()):
        warn("Ranwell readings or Script 44's pairings not present — E9 is skipped")
        return pd.DataFrame()
    lv = pd.read_csv(RANWELL_LEVELS, parse_dates=["date"])
    lv["month"] = lv["date"].dt.to_period("M")
    obs_month = lv.groupby(["site_no", "month"])["level_m_od"].mean()
    pairs = pd.read_csv(OUT_44_METRICS)
    clh = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    p_mean, pet_mean = float(clh["P_m"].mean()), float(clh["PET"].mean())
    first = pd.Timestamp(f"{obs_month.index.get_level_values('month').min().year - 1}-12-01")
    last = obs_month.index.get_level_values("month").max().to_timestamp()

    def score(om, betas, run_d, ground):
        h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=run_d)
        sim, spin = hindcast_well(clh, betas, h0, first, last, 1.0, drainage_datum=run_d)
        mid = (sim + sim.shift(1)) / 2
        mid.index = mid.index.to_period("M")
        mid = mid.dropna()
        m = compare_offset_censored(om, mid, ground)
        od = om[om.index.year == RANWELL_DRY_YEAR]
        dry = compare_offset_censored(od, mid, ground) if len(od) >= 3 else {"nse_after_offset": np.nan, "n": len(od)}
        return m, dry, spin

    rows = []
    for pr in track(list(pairs.itertuples()), "Ranwell by datum", min_seconds=5.0):
        col = lev_cols.get(normalize_well_name(pr.well))
        if col is None or int(pr.site_no) not in obs_month.index.get_level_values(0):
            continue
        om = obs_month.loc[int(pr.site_no)]
        h = lev[col].dropna()
        base = {"site_no": int(pr.site_no), "sketch_slack": pr.sketch_slack, "well": normalize_well_name(pr.well),
                "headline": bool(pr.headline), "dist_m": float(pr.dist_m), "ground_m_od": float(pr.ground_m_od)}
        for D in datum_grid():
            for basis, win in (("comparison_window", LCSC_DATA_LIMIT), ("full_record", None)):   # 1.24.0 (D-322)
                for form, intercept in FORMS:
                    # Model B does not depend on the datum it is built at (the intercept absorbs it):
                    # it is fitted once, at the project datum, and run at its own zero-drainage datum.
                    if intercept and not np.isclose(D, DRAINAGE_DATUM):
                        continue
                    f = _censored_well_fit(h, cl, dry_bounds(col), win, intercept, datum=D, start=RECORD_FIT_START)
                    row = dict(base, form=form, basis=basis, datum_m=float(D) if not intercept else np.nan)
                    if f is None or not (f["beta_3_drainage"] > 0):
                        rows.append(row)
                        continue
                    betas = (f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"])
                    run_d = run_datum(f, intercept, base=float(D))
                    m, dry, spin = score(om, betas, run_d, float(pr.ground_m_od))
                    row.update(run_datum_m=run_d, beta_1=betas[0], beta_2=betas[1], beta_3=betas[2],
                               n=m["n"], n_at_surface=m["n_at_surface"], r=m["r"],
                               nse_after_offset=m["nse_after_offset"],
                               range_ratio=(m["range_model_m"] / m["range_obs_m"]
                                            if m.get("range_obs_m") and np.isfinite(m["range_obs_m"]) and m["range_obs_m"] > 0
                                            else np.nan),
                               nse_dry_year=dry["nse_after_offset"], n_dry_year=dry["n"], spinup_months=spin)
                    rows.append(row)
    return pd.DataFrame(rows)


def ranwell_supported(rw: pd.DataFrame, headline_only: bool = True, metric: str = "nse_after_offset"):
    """The rule fixed before the run (D-229): Model A, comparison window, median over the headline
    pairings; the best datum and the band within RECLEN_DATUM_NSE_TOL; no datum when the median moves by
    less than the tolerance over the whole grid. Returns (best, lo, hi, spread, med)."""
    c = rw[(rw["form"] == "A") & (rw["basis"] == "comparison_window") & rw[metric].notna()]
    if headline_only:
        c = c[c["headline"]]
    if c.empty:
        return np.nan, np.nan, np.nan, np.nan, pd.Series(dtype=float)
    med = c.groupby("datum_m")[metric].median()
    spread = float(med.max() - med.min())
    if spread < RECLEN_DATUM_NSE_TOL:
        return np.nan, np.nan, np.nan, spread, med
    band = med[med >= med.max() - RECLEN_DATUM_NSE_TOL].index
    return float(med.idxmax()), float(min(band)), float(max(band)), spread, med


def ranwell_verdict(lo, hi, ccw_lo, ccw_hi) -> str:
    if not np.isfinite(lo):
        return "does not discriminate"
    if not (np.isfinite(ccw_lo) and np.isfinite(ccw_hi)):
        return "does not discriminate"
    return "consistent" if (lo <= ccw_hi and ccw_lo <= hi) else "disagrees"


def ranwell_report(rr, rw: pd.DataFrame, ccw_lo: float, ccw_hi: float) -> str:
    best, lo, hi, spread, med = ranwell_supported(rw)
    verdict = ranwell_verdict(lo, hi, ccw_lo, ccw_hi)
    nh = int(rw[rw["headline"]]["site_no"].nunique()) if len(rw) else 0
    rr.add("datum_ranwell_supported_m", best, unit="m",
           note=f"datum maximizing the median Ranwell 1951-53 NSE after offset over the {nh} headline pairings, "
                "Model A on the comparison window (rule fixed before the run, D-229); empty when the curve is flat")
    rr.add("datum_ranwell_band_min_m", lo, unit="m", note=f"shallowest datum within {RECLEN_DATUM_NSE_TOL:g} NSE of the best (D-229)")
    rr.add("datum_ranwell_band_max_m", hi, unit="m", note=f"deepest datum within {RECLEN_DATUM_NSE_TOL:g} NSE of the best (D-229)")
    rr.add("datum_ranwell_nse_spread", spread, unit="",
           note=f"max minus min of the median headline NSE over the datum grid; below {RECLEN_DATUM_NSE_TOL:g} the record does not discriminate")
    rr.add("datum_ranwell_verdict", VERDICT_CODE[verdict], unit="code",
           note=f"{verdict} (1 consistent with the CCW band, 0 does not discriminate, -1 disagrees; D-229)")
    a = rw[(rw["form"] == "A") & (rw["basis"] == "comparison_window") & rw["headline"]]
    b = rw[(rw["form"] == "B") & (rw["basis"] == "comparison_window") & rw["headline"]]
    for tag, D in (("project", DRAINAGE_DATUM), ("supported", best)):
        q = a[np.isclose(a["datum_m"], D)] if np.isfinite(D) else a.iloc[0:0]
        for col, key, what in (("nse_after_offset", "nse", "NSE after offset"),
                               ("nse_dry_year", "nse_dry_year", f"NSE after offset, {RANWELL_DRY_YEAR} only"),
                               ("range_ratio", "range_ratio", "model range / observed range")):
            rr.add(f"ranwell_{key}_median_at_{tag}", float(q[col].median()) if len(q) else np.nan, unit="",
                   note=f"median {what}, headline pairings, Model A at datum {D:g} m, comparison window")
    for col, key, what in (("nse_after_offset", "nse", "NSE after offset"),
                           ("nse_dry_year", "nse_dry_year", f"NSE after offset, {RANWELL_DRY_YEAR} only"),
                           ("range_ratio", "range_ratio", "model range / observed range")):
        rr.add(f"ranwell_{key}_median_model_b", float(b[col].median()) if len(b) else np.nan, unit="",
               note=f"median {what}, headline pairings, Model B (its own zero-drainage datum), comparison window")
    b_all, _, _, _, _ = ranwell_supported(rw, headline_only=False)
    rr.add("datum_ranwell_supported_all_pairings_m", b_all, unit="m",
           note="the same rule over every Script 44 pairing (check, D-229)")
    d_dry, _, _, _, _ = ranwell_supported(rw, metric="nse_dry_year")
    rr.add("datum_ranwell_supported_dry_year_m", d_dry, unit="m",
           note=f"the same rule on {RANWELL_DRY_YEAR} alone, below the surface (check against D-059, D-229)")
    return verdict


def ranwell_identity_check(rw: pd.DataFrame) -> float:
    """Model A, comparison window, at the project datum against Script 44's committed NSE (expected ~0:
    the same coefficients and scoring; the starting level differs, forgotten over the 1930 spin-up)."""
    if not len(rw) or not OUT_44_METRICS.exists():
        return np.nan
    m44 = pd.read_csv(OUT_44_METRICS)
    m44["well"] = m44["well"].astype(str).apply(normalize_well_name)
    m44 = m44.set_index(["site_no", "well"])["nse_after_offset"]
    a = rw[(rw["form"] == "A") & (rw["basis"] == "comparison_window") & np.isclose(rw["datum_m"].fillna(-1), DRAINAGE_DATUM)]
    d = [abs(r.nse_after_offset - m44.loc[(r.site_no, r.well)]) for r in a.itertuples()
         if (r.site_no, r.well) in m44.index and np.isfinite(r.nse_after_offset)]
    return float(max(d)) if d else np.nan


def datum_report(rr, ccw_d, split_d, proj_d, checks_d):
    """Report numbers for 1.1.0."""
    best, lo, hi, med = supported_datum(ccw_d)
    rr.add("datum_ccw_supported_m", best, unit="m",
           note=f"datum maximizing the median CCW 1989-96 hindcast NSE, Model A on the comparison window "
                f"(rule fixed before the run, D-225); n wells per datum up to {ccw_d['well'].nunique() if len(ccw_d) else 0}")
    rr.add("datum_ccw_band_min_m", lo, unit="m", note=f"shallowest datum within {RECLEN_DATUM_NSE_TOL:g} NSE of the best (D-225)")
    rr.add("datum_ccw_band_max_m", hi, unit="m", note=f"deepest datum within {RECLEN_DATUM_NSE_TOL:g} NSE of the best (D-225)")
    for D in (best, DRAINAGE_DATUM):
        if np.isfinite(D) and D in med.index:
            rr.add(f"datum_ccw_nse_median_at_D{_dkey(D)}", float(med.loc[D]), unit="",
                   note=f"median CCW hindcast NSE, Model A at datum {D:g} m, comparison window")
    b2, lo2, hi2, _ = supported_datum(ccw_d, metric="abs_bias")
    rr.add("datum_ccw_best_abs_bias_m", b2, unit="m", note="datum minimizing the median |CCW bias| (check, D-225)")
    b3, lo3, hi3, _ = supported_datum(ccw_d, subset=lambda c: ~c["in_forest"])
    rr.add("datum_ccw_supported_open_ground_m", b3, unit="m",
           note="datum maximizing the median CCW NSE over the open-ground wells only (check, D-225)")
    if len(split_d):
        for d_ in ("fwd", "rev"):
            s = split_d[split_d["direction"] == d_].groupby("datum_m")["nse"].median()
            for D in (best, DRAINAGE_DATUM):
                if np.isfinite(D) and D in s.index:
                    rr.add(f"datum_split_nse_{d_}_median_at_D{_dkey(D)}", float(s.loc[D]), unit="",
                           note=f"median split-sample NSE ({d_}), Model A at datum {D:g} m")
    if len(proj_d):
        for scen in ("2080s", "2050s"):                 # 1.15.0: the 2050s beside the 2080s (D-279)
            p = proj_d[(proj_d["scenario"] == scen) & (proj_d["season"] == "summer")]
            for tag, D in (("supported", best), ("band_min", lo), ("band_max", hi), ("project", DRAINAGE_DATUM)):
                q = p[np.isclose(p["datum_m"], D)] if np.isfinite(D) else p.iloc[0:0]
                rr.add(f"projection_{scen}_summer_fall_median_at_{tag}", float(q["fall_model_a_m"].median()) if len(q) else np.nan,
                       unit="m", note=f"median {scen} summer sustained level response, Model A at datum {D:g} m; "
                                      f"n = {len(q)} wells (forest withheld, D-224 pairing)")
                rr.add(f"projection_{scen}_summer_room_left_min_at_{tag}", float(q["room_left_m"].min()) if len(q) else np.nan,
                       unit="m", note=f"smallest room left above the datum at the projected {scen} summer minimum, datum {D:g} m")
            q = p[np.isclose(p["datum_m"], DRAINAGE_DATUM)]
            rr.add(f"projection_{scen}_summer_fall_median_model_b", float(q["fall_model_b_m"].median()) if len(q) else np.nan,
                   unit="m", note=f"median {scen} summer sustained level response, Model B, the same wells")
            rr.add(f"projection_{scen}_n_wells_pair", float(len(q)), unit="count",
                   note=f"wells projected under both forms at the project datum ({scen}, forest withheld, D-224)")
            # 1.16.0 (D-280): the trio -- wells where Model A, Model B and the depth-dependent form all
            # project -- with each form's median on those same wells.
            if "fall_ddp_m" in q.columns:
                t = q[q["fall_ddp_m"].notna()]
                rr.add(f"projection_{scen}_n_wells_trio", float(len(t)), unit="count",
                       note=f"wells projected under Model A, Model B and the depth-dependent form ({scen}, project datum)")
                for col, tag in (("fall_model_a_m", "model_a"), ("fall_model_b_m", "model_b"), ("fall_ddp_m", "ddp")):
                    rr.add(f"projection_{scen}_summer_fall_median_trio_{tag}", float(t[col].median()) if len(t) else np.nan,
                           unit="m", note=f"median {scen} summer sustained level response, {tag}, on the trio wells")
    for k, v in checks_d.items():
        rr.add(f"reclen_check_{k}", v, unit="", note="identity check at the project datum (expected 0)")
    _dx = ddp_sets()[1]                                  # 1.27.0 (D-332)
    rr.add("projection_ddp_n_sets_excluded_datum", float(len(_dx)), unit="count",
           note="15_05 per-well depth-dependent sets left out of E7: Model B implied base DRAINAGE_DATUM - "
                "alpha/beta_3 not below ground (D-332)"
                + (" (" + ", ".join(f"{w} {v:+.1f} m" for w, v in sorted(_dx.items())) + ")" if _dx else ""))
    rr.add("projection_check_ddp_k0_vs_closed_form", ddp_identity_check(), unit="m",
           note="identity check: the depth-dependent sustained response at 1/L_E = 0 less the closed form, "
                "max over a coefficient grid (expected 0 to 1e-9)")


def datum_identity_checks(ccw_d, split_d, proj_d) -> dict:
    out = {}
    if len(ccw_d) and OUT_39_PER_WELL.exists():
        p39 = pd.read_csv(OUT_39_PER_WELL).set_index("well")
        c = ccw_d[(ccw_d["basis"] == "comparison_window") & np.isclose(ccw_d["datum_m"], DRAINAGE_DATUM)]
        d = [abs(r["nse"] - p39.loc[r["well"], "nse"]) for _, r in c.iterrows() if r["well"] in p39.index and np.isfinite(r["nse"])]
        out["datum_vs39_max_abs_nse_diff"] = float(max(d)) if d else np.nan
    if len(split_d) and OUT_48_MODEL_AB.exists():
        ab = pd.read_csv(OUT_48_MODEL_AB)
        ab["well"] = ab["well"].astype(str).apply(normalize_well_name)
        ab = ab.set_index("well")
        s = split_d[np.isclose(split_d["datum_m"], DRAINAGE_DATUM)]
        d = [abs(r["nse"] - ab.loc[r["well"], f"nse_{r['direction']}_A"]) for _, r in s.iterrows()
             if r["well"] in ab.index and np.isfinite(r["nse"]) and np.isfinite(ab.loc[r["well"], f"nse_{r['direction']}_A"])]
        out["datum_vs48_max_abs_nse_diff"] = float(max(d)) if d else np.nan
    if len(proj_d) and OUT_19_SCENARIO_PERWELL_MODEL_A.exists():
        a19 = pd.read_csv(OUT_19_SCENARIO_PERWELL_MODEL_A)
        a19 = a19[(a19["scenario"] == "ukcp18_2080s") & (a19["season"] == "summer")].set_index("well")["dh_m"]
        p = proj_d[np.isclose(proj_d["datum_m"], DRAINAGE_DATUM) & (proj_d["scenario"] == "2080s") & (proj_d["season"] == "summer")]
        d = [abs(r["fall_model_a_m"] - a19.loc[r["well"]]) for _, r in p.iterrows() if r["well"] in a19.index]
        out["datum_vs19_max_abs_fall_diff_m"] = float(max(d)) if d else np.nan
    return out


def plot_datum(ccw_d, split_d, proj_d, best, lo, hi, rw=None) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    # 1.2.0: 2 x 2 - (a) CCW 1989-96, (b) Ranwell 1951-53 (E9, D-229), (c) split test, (d) projection
    fig, ax4 = plt.subplots(2, 2, figsize=(9.0, 6.8), dpi=160)
    axes = [ax4[0, 0], ax4[1, 0], ax4[1, 1]]
    axr = ax4[0, 1]
    c = ccw_d[(ccw_d["basis"] == "comparison_window")]
    g = c.groupby("datum_m")
    ax = axes[0]
    ax.plot(g["nse"].median().index, g["nse"].median().values, color="0.15", lw=1.4, label="median NSE")
    ax2 = ax.twinx()
    ax2.plot(g["bias_m"].median().index, g["bias_m"].median().values, color="#b2182b", lw=1.1, ls="--", label="median bias")
    ax2.axhline(0, color="#b2182b", lw=0.5, alpha=0.5)
    ax2.set_ylabel("median bias (m)", color="#b2182b", fontsize=8)
    ax.set_title(f"(a) CCW 1989–96 hindcast, {c['well'].nunique()} wells", loc="left", fontsize=9)
    ax.set_ylabel("median NSE")
    s = split_d.groupby(["direction", "datum_m"])["nse"].median()
    for d_, ls in (("fwd", "-"), ("rev", "--")):
        if d_ in s.index.get_level_values(0):
            axes[1].plot(s.loc[d_].index, s.loc[d_].values, color="0.15", ls=ls, lw=1.2,
                         label="forecast after split" if d_ == "fwd" else "hindcast before split")
    axes[1].set_title("(c) Within-record split test, median NSE", loc="left", fontsize=9)
    axes[1].legend(fontsize=7)
    p = proj_d[(proj_d["scenario"] == "2080s") & (proj_d["season"] == "summer")]
    q = p.groupby("datum_m")["fall_model_a_m"]
    axes[2].plot(q.median().index, q.median().values, color="0.15", lw=1.4, label="Model A, median")
    axes[2].fill_between(q.quantile(0.1).index, q.quantile(0.1).values, q.quantile(0.9).values, color="0.6", alpha=0.3,
                         lw=0, label="Model A, 10th–90th percentile")
    axes[2].axhline(float(p[np.isclose(p["datum_m"], DRAINAGE_DATUM)]["fall_model_b_m"].median()), color="#2166ac",
                    lw=1.1, ls=":", label="Model B, median")
    axes[2].set_title("(d) 2080s summer level change (m)", loc="left", fontsize=9)
    axes[2].legend(fontsize=7)
    if rw is not None and len(rw):
        ra = rw[(rw["form"] == "A") & (rw["basis"] == "comparison_window")]
        hm = ra[ra["headline"]].groupby("datum_m")["nse_after_offset"].median()
        am = ra.groupby("datum_m")["nse_after_offset"].median()
        dm = ra[ra["headline"]].groupby("datum_m")["nse_dry_year"].median()
        axr.plot(hm.index, hm.values, color="0.15", lw=1.4, label="headline pairings, median")
        axr.plot(am.index, am.values, color="0.15", lw=1.0, ls="--", label="all pairings, median")
        axr.plot(dm.index, dm.values, color="#8c510a", lw=1.0, ls="-.", label=f"{RANWELL_DRY_YEAR} only, headline")
        rb = rw[(rw["form"] == "B") & (rw["basis"] == "comparison_window") & rw["headline"]]["nse_after_offset"]
        if len(rb.dropna()):
            axr.axhline(float(rb.median()), color="#2166ac", lw=1.1, ls=":", label="Model B, headline median")
        rbest, rlo, rhi, _sp, _m = ranwell_supported(rw)
        if np.isfinite(rlo):
            axr.axvspan(rlo, rhi, facecolor="none", edgecolor="#5e3c99", hatch="///", lw=0, alpha=0.6)
        n_s = int(ra[ra["headline"]]["site_no"].nunique())
        axr.set_title(f"(b) Ranwell 1951–53 hindcast, {n_s} sites (offset removed)", loc="left", fontsize=9)
        axr.set_ylabel("median NSE after offset")
        axr.legend(fontsize=6.5, loc="lower right")
        axes = axes + [axr]
    else:
        axr.set_visible(False)
    for a in axes:
        a.set_xlabel("datum (m below ground)")
        a.grid(alpha=0.3)
        if np.isfinite(lo):
            a.axvspan(lo, hi, color="#fdb863", alpha=0.25, lw=0)
        a.axvline(DRAINAGE_DATUM, color="0.4", lw=0.8, ls=":")
    fig.tight_layout()
    fig.savefig(OUT_50_DATUM_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_50_DATUM_FIG.name)


def e16_specs() -> list:
    """(kind, z0, label): the depth datum, every z0 of Script 03's DATUM_AOD_SWEEP_* grid, and mean high water."""
    specs = [("depth", np.nan, f"depth {DRAINAGE_DATUM:g} m")]
    grid = np.arange(DATUM_AOD_SWEEP_MIN_M, DATUM_AOD_SWEEP_MAX_M + DATUM_AOD_SWEEP_STEP_M / 2, DATUM_AOD_SWEEP_STEP_M)
    specs += [("elevation", round(float(z), 6), f"{float(z):g} m AOD") for z in grid]
    mhw = _e16_mhw()
    if np.isfinite(mhw):
        specs.append(("mhw", mhw, f"MHW {mhw:g} m AOD"))
    return specs


def _e16_datum(kind: str, z0: float, ground: float) -> float:
    return DRAINAGE_DATUM if kind == "depth" else ground - z0


def elevation_datum_tests(lev, lev_cols, cl, master, specs=None, datum_of=None) -> pd.DataFrame:
    """E16: one row per well x datum x test (ccw, ranwell, split_fwd, split_rev, fit). Model A, comparison window,
    as E5/E9/E6 fit it; the depth rows reproduce 50_06/50_10/50_07 at DRAINAGE_DATUM (identity check).
    E17 (1.20.0) passes its own specs and datum_of(kind, z0, ground, cluster), a base per cluster."""
    grounds = _e16_grounds()
    specs = e16_specs() if specs is None else specs
    if datum_of is None:
        def datum_of(kind, z0, g, c):
            return _e16_datum(kind, z0, g)
    clh = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    p_mean, pet_mean = float(clh["P_m"].mean()), float(clh["PET"].mean())
    rows = []

    def _base(test, well, cluster, kind, z0, D):
        return {"test": test, "well": well, "cluster": cluster, "datum_kind": kind, "z0_m_aod": z0, "datum_m": D}

    # fit diagnostics and the split test: every reference well
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    for _, r in master.iterrows():
        col = lev_cols.get(r["_n"])
        if col is None or r["_n"] not in grounds:
            continue
        h = lev[col].dropna()
        g = grounds[r["_n"]]
        pre_h, post_h = h[h.index < split], h[h.index >= split]   # D-349 (A3): h is cut at RECORD_FIT_START (load_inputs), so "pre" is 2010-17
        for kind, z0, _lab in specs:
            D = datum_of(kind, z0, g, int(r["Cluster"]))
            f = _censored_well_fit(h, cl, dry_bounds(col), LCSC_DATA_LIMIT, False, datum=D, start=RECORD_FIT_START)   # 1.24.0 (D-322)
            row = _base("fit", r["_n"], int(r["Cluster"]), kind, z0, D)
            if f is not None:
                b3 = f["beta_3_drainage"]
                row.update(beta_1=f["beta_1_recharge"], beta_2=f["beta_2_atmospheric_draw"], beta_3=b3,
                           p_beta_3=f["pvalue_beta_3"], R2=f["R2"], n_fit=int(f["n"]),
                           efold_months=(1.0 / b3) if b3 > 0 else np.nan,
                           mean_h_disp_prev=f["mean_h_disp_prev"])
            rows.append(row)
            for direction, tr, te in (("split_fwd", pre_h, post_h), ("split_rev", post_h, pre_h)):
                ft = fit_frame(build_ssm_frame(tr, cl, lag=HEADLINE_LAG, drainage_datum=float(D)), False)
                res = free_run(te, cl, ft, False, base=float(D))
                rows.append(dict(_base(direction, r["_n"], int(r["Cluster"]), kind, z0, D),
                                 nse=res["nse"], bias_m=res["bias_m"], n_test=res["n_test"]))

    # the CCW 1989-96 hindcast: E5's wells, scoring and comparison-window fit
    if paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists():
        obs, cmap = load_ccw()
        md = _model_a_store(pd.read_csv(INT_MASTER_DATA))
        md["k"] = md["Name_Original"].astype(str).str.lower().str.strip()
        md = md.set_index("k")
        adm = usable_codes(cmap, md, obs)
        adm = adm[adm["admitted"]]
        first_month, last_month = obs["month"].min(), obs["month"].max()
        for r in adm.itertuples():
            k = normalize_well_name(r.well)
            col = lev_cols.get(k)
            if col is None or k not in grounds:
                continue
            o, _n = observed_series(obs, r.code, r.datum_offset_m)
            if o.empty:
                continue
            h = lev[col].dropna()
            for kind, z0, _lab in specs:
                D = datum_of(kind, z0, grounds[k], int(md.loc[r.well, "Cluster"]))
                f = _censored_well_fit(h, cl, dry_bounds(col), LCSC_DATA_LIMIT, False, datum=D, start=RECORD_FIT_START)   # 1.24.0 (D-322)
                row = _base("ccw", k, int(md.loc[r.well, "Cluster"]), kind, z0, D)
                row["code"] = r.code
                if f is not None and f["beta_3_drainage"] > 0:
                    betas = (f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"])
                    h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=float(D))
                    pred, _s = hindcast_well(clh, betas, h0, first_month, last_month, 1.0, drainage_datum=float(D))
                    common = o.index.intersection(pred.index)
                    nse, _rmse, bias = get_metrics(o.loc[common], pred.loc[common])
                    row.update(nse=float(nse), bias_m=float(bias), n_test=int(len(common)), beta_3=f["beta_3_drainage"])
                rows.append(row)
    else:
        warn("CCW historic inputs not present — E16's CCW test is skipped")

    # Ranwell 1951-53: E9's pairings and scoring, Model A, comparison window
    if RANWELL_LEVELS.exists() and OUT_44_METRICS.exists():
        lv = pd.read_csv(RANWELL_LEVELS, parse_dates=["date"])
        lv["month"] = lv["date"].dt.to_period("M")
        obs_month = lv.groupby(["site_no", "month"])["level_m_od"].mean()
        pairs = pd.read_csv(OUT_44_METRICS)
        first = pd.Timestamp(f"{obs_month.index.get_level_values('month').min().year - 1}-12-01")
        last = obs_month.index.get_level_values("month").max().to_timestamp()
        for pr in pairs.itertuples():
            k = normalize_well_name(pr.well)
            col = lev_cols.get(k)
            if col is None or k not in grounds or int(pr.site_no) not in obs_month.index.get_level_values(0):
                continue
            om = obs_month.loc[int(pr.site_no)]
            h = lev[col].dropna()
            cl_k = master.loc[master["_n"] == k, "Cluster"]
            for kind, z0, _lab in specs:
                D = datum_of(kind, z0, grounds[k], int(cl_k.iloc[0]) if len(cl_k) else -1)
                f = _censored_well_fit(h, cl, dry_bounds(col), LCSC_DATA_LIMIT, False, datum=D, start=RECORD_FIT_START)   # 1.24.0 (D-322)
                row = _base("ranwell", k, int(cl_k.iloc[0]) if len(cl_k) else -1, kind, z0, D)
                row.update(site_no=int(pr.site_no), headline=bool(pr.headline))
                if f is not None and f["beta_3_drainage"] > 0:
                    betas = (f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"])
                    h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=float(D))
                    sim, _spin = hindcast_well(clh, betas, h0, first, last, 1.0, drainage_datum=float(D))
                    mid = (sim + sim.shift(1)) / 2
                    mid.index = mid.index.to_period("M")
                    m = compare_offset_censored(om, mid.dropna(), float(pr.ground_m_od))
                    row.update(nse=m["nse_after_offset"], n_test=m["n"], beta_3=f["beta_3_drainage"])
                rows.append(row)
    else:
        warn("Ranwell readings or Script 44's pairings not present — E16's Ranwell test is skipped")
    return pd.DataFrame(rows)


def elevation_datum_summary(t: pd.DataFrame) -> pd.DataFrame:
    """One row per datum: the medians each test is judged on, beta_3's identification, and the topography check."""
    out = []
    for (kind, z0), g in t.groupby(["datum_kind", "z0_m_aod"], dropna=False, sort=False):
        fit = g[g["test"] == "fit"]
        ok = fit[fit["beta_3"].notna()]
        ccw = g[(g["test"] == "ccw") & g["nse"].notna()]
        rw = g[(g["test"] == "ranwell") & g["nse"].notna()]
        rw = rw[rw["headline"].astype(bool)] if "headline" in rw.columns else rw.iloc[0:0]
        sp = g[g["test"].isin(["split_fwd", "split_rev"]) & g["nse"].notna()]
        pos = ok[ok["beta_3"] > 0]
        rho = (float(pos[["beta_3", "datum_m"]].corr(method="spearman").iloc[0, 1])
               if len(pos) > 5 and pos["datum_m"].nunique() > 1 else np.nan)
        out.append({
            "datum_kind": kind, "z0_m_aod": z0,
            "n_wells_fit": int(len(ok)), "n_beta3_nonpositive": int((ok["beta_3"] <= 0).sum()),
            "n_beta3_not_sig": int(((ok["beta_3"] <= 0) | (ok["p_beta_3"] >= SIG_P)).sum()),
            "r2_median": float(ok["R2"].median()) if len(ok) else np.nan,
            "efold_median_months": float(pos["efold_months"].median()) if len(pos) else np.nan,
            "rho_beta3_vs_datum": rho,
            "ccw_n": int(len(ccw)), "ccw_nse_median": float(ccw["nse"].median()) if len(ccw) else np.nan,
            "ccw_abs_bias_median_m": float(ccw["bias_m"].abs().median()) if len(ccw) else np.nan,
            "ccw_bias_median_m": float(ccw["bias_m"].median()) if len(ccw) else np.nan,
            "ranwell_n": int(len(rw)), "ranwell_nse_median": float(rw["nse"].median()) if len(rw) else np.nan,
            "split_n": int(len(sp)), "split_nse_median": float(sp["nse"].median()) if len(sp) else np.nan,
        })
        _pos_l = _lvl_rows(pos) if len(pos) else pos    # D-348: cluster medians over cluster-level wells
        for c in sorted(CLUSTER_LABELS):
            pc = _pos_l[_pos_l["cluster"] == c]
            out[-1][f"efold_median_C{c}_months"] = float(pc["efold_months"].median()) if len(pc) else np.nan
    return pd.DataFrame(out)


def elevation_datum_verdict(s: pd.DataFrame) -> dict:
    """The rule fixed before the run (D-286): z0* maximizes the median CCW NSE over the elevation grid (D-225's
    choice rule), among the datums that score the same wells as the depth datum (added after the first run). A(ii) is adopted only if, at z0*, against Model A at the depth datum on the same wells:
    (1) the median CCW NSE is at least as high; (2) the median CCW |bias| is no larger; (3) the median Ranwell
    NSE after offset and (4) the median split-sample NSE are no lower by more than RECLEN_DATUM_NSE_TOL; and
    (5) no more wells have beta_3 <= 0."""
    dep = s[s["datum_kind"] == "depth"].iloc[0]
    # Like for like (corrected after the first run, D-286): only datums at which every CCW well and Ranwell pairing
    # scored at the depth datum is still scored. A datum where beta_3 fails drops those wells from the medians, and
    # the first run's rule chose 7 m AOD on 5 of the 9 CCW wells.
    el = s[(s["datum_kind"] == "elevation") & s["ccw_nse_median"].notna()
           & (s["ccw_n"] == dep["ccw_n"]) & (s["ranwell_n"] == dep["ranwell_n"])]
    if el.empty or not np.isfinite(dep["ccw_nse_median"]):
        return {"verdict": "not run", "z0": np.nan, "tests": {}}
    best = el.loc[el["ccw_nse_median"].idxmax()]
    tol = RECLEN_DATUM_NSE_TOL
    tests = {
        "ccw_nse": bool(best["ccw_nse_median"] >= dep["ccw_nse_median"]),
        "ccw_bias": bool(best["ccw_abs_bias_median_m"] <= dep["ccw_abs_bias_median_m"]),
        "ranwell": bool(not np.isfinite(dep["ranwell_nse_median"])
                        or best["ranwell_nse_median"] >= dep["ranwell_nse_median"] - tol),
        "split": bool(best["split_nse_median"] >= dep["split_nse_median"] - tol),
        "identified": bool(best["n_beta3_nonpositive"] <= dep["n_beta3_nonpositive"]),
    }
    return {"verdict": "adopted" if all(tests.values()) else "not adopted", "z0": float(best["z0_m_aod"]),
            "tests": tests, "best": best, "depth": dep}


def e16_identity_check(t: pd.DataFrame) -> float:
    """The depth rows against E5's committed comparison-window CCW NSE at DRAINAGE_DATUM (expected 0)."""
    if not OUT_50_CCW_DATUM.exists():
        return np.nan
    e5 = pd.read_csv(OUT_50_CCW_DATUM)
    e5 = e5[(e5["basis"] == "comparison_window") & np.isclose(e5["datum_m"], DRAINAGE_DATUM) & e5["nse"].notna()]
    e5 = e5.assign(k=e5["well"].astype(str).apply(normalize_well_name)).groupby(["k", "code"])["nse"].first()
    d = t[(t["test"] == "ccw") & (t["datum_kind"] == "depth") & t["nse"].notna()].groupby(["well", "code"])["nse"].first()
    j = pd.concat([e5.rename("a"), d.rename("b")], axis=1, join="inner")
    return float((j["a"] - j["b"]).abs().max()) if len(j) else np.nan


def e16_report(rr, s: pd.DataFrame, v: dict, ident: float, t: pd.DataFrame | None = None) -> None:
    code = {"adopted": 1, "not adopted": 0, "not run": -1}[v["verdict"]]
    rr.add("e16_verdict", code, unit="code",
           note=f"Model A(ii), one drainage base in elevation: {v['verdict']} (1 adopted, 0 not adopted, -1 not run); "
                "rule fixed before the run (D-286)")
    if v["verdict"] == "not run":
        return
    b, d = v["best"], v["depth"]
    rr.add("e16_z0_best_m_aod", v["z0"], unit="m AOD",
           note="the elevation datum maximizing the median CCW 1989-96 NSE, Model A, comparison window, among the datums "
                "that score the same wells as the depth datum (E16, D-286)")
    el = s[(s["datum_kind"] == "elevation") & s["ccw_nse_median"].notna()]
    if len(el):
        rr.add("e16_z0_best_any_coverage_m_aod", float(el.loc[el["ccw_nse_median"].idxmax(), "z0_m_aod"]), unit="m AOD",
               note="the same choice without the like-for-like condition (the first run's rule), for the record")
    for key, col, unit, what in (("ccw_nse_median", "ccw_nse_median", "", "median CCW 1989-96 NSE"),
                                 ("ccw_abs_bias_median", "ccw_abs_bias_median_m", "m", "median CCW |bias|"),
                                 ("ranwell_nse_median", "ranwell_nse_median", "", "median Ranwell NSE after offset, headline pairings"),
                                 ("split_nse_median", "split_nse_median", "", "median split-sample NSE, both directions"),
                                 ("n_beta3_nonpositive", "n_beta3_nonpositive", "count", "wells with beta_3 <= 0, comparison window"),
                                 ("efold_median_months", "efold_median_months", "months", "median 1/beta_3 over wells with beta_3 > 0"),
                                 ("rho_beta3_vs_datum", "rho_beta3_vs_datum", "", "Spearman rho of beta_3 against the per-well datum")):
        rr.add(f"e16_{key}_at_best", float(b[col]), unit=unit, note=f"{what}, at the best elevation datum (E16)")
        rr.add(f"e16_{key}_at_depth", float(d[col]), unit=unit, note=f"{what}, at the depth datum {DRAINAGE_DATUM:g} m (E16)")
    for name, ok in v["tests"].items():
        rr.add(f"e16_test_{name}_pass", int(ok), unit="flag", note=f"E16 adoption test '{name}' passed at the best elevation datum (D-286)")
    m = s[s["datum_kind"] == "mhw"]
    if len(m):
        m = m.iloc[0]
        for key, col in (("ccw_nse_median", "ccw_nse_median"), ("rho_beta3_vs_datum", "rho_beta3_vs_datum"),
                         ("efold_median_months", "efold_median_months")):
            rr.add(f"e16_{key}_at_mhw", float(m[col]), unit="", note=f"{col} with every well's base at mean high water (E16)")
    if t is not None and v["verdict"] != "not run":
        # 1.20.0: per cluster, so Paper M can quote the split by cluster as fields (D-286)
        z = v["z0"]
        sel = {"depth": t["datum_kind"] == "depth",
               "best": (t["datum_kind"] == "elevation") & np.isclose(t["z0_m_aod"].astype(float), z)}
        ccw = t[(t["test"] == "ccw") & t["nse"].notna()]
        for c in sorted(CLUSTER_LABELS):
            for tag, m in sel.items():
                x = ccw[m.reindex(ccw.index, fill_value=False) & (ccw["cluster"] == c)]
                if len(x):
                    rr.add(f"e16_ccw_nse_median_C{c}_at_{tag}", float(x["nse"].median()), unit="",
                           note=f"median CCW 1989-96 NSE, C{c}, {'depth datum' if tag == 'depth' else 'best elevation datum'} (E16)")
            n = int(((ccw["cluster"] == c) & sel["depth"].reindex(ccw.index, fill_value=False)).sum())
            if n:
                rr.add(f"e16_ccw_n_C{c}", n, unit="count", note=f"CCW wells in C{c} (E16)")
            fit = t[(t["test"] == "fit") & sel["best"] & (t["cluster"] == c) & (t["beta_3"] > 0)]
            if len(fit):
                rr.add(f"e16_efold_median_C{c}_months_at_best", float(fit["efold_months"].median()), unit="months",
                       note=f"median 1/beta_3, C{c}, at the best elevation datum (E16)")
        a = ccw[sel["depth"].reindex(ccw.index, fill_value=False)].set_index(["well", "code"])["nse"]
        b = ccw[sel["best"].reindex(ccw.index, fill_value=False)].set_index(["well", "code"])["nse"]
        j = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner")
        rr.add("e16_ccw_n_better_at_best", int((j["b"] >= j["a"]).sum()), unit="count",
               note="CCW wells whose NSE is as high or higher at the best elevation datum than at the depth datum (E16)")
        rr.add("e16_r2_median_at_best", float(v["best"]["r2_median"]), unit="", note="median R2, comparison window, best elevation datum (E16)")
        rr.add("e16_r2_median_at_depth", float(v["depth"]["r2_median"]), unit="", note="median R2, comparison window, depth datum (E16)")
        rr.add("e16_ranwell_n", int(v["best"]["ranwell_n"]), unit="count", note="Ranwell headline pairings scored (E16)")
    rr.add("e16_identity_ccw_max_abs_dnse", ident, unit="",
           note="max |NSE difference|, E16 depth rows against E5 (50_06) at the project datum; expected 0")


def run_e16(lev, lev_cols, cl, master):
    """E16's tests, summary, verdict and identity check; writes 50_41 and 50_42. The report numbers are added
    by the caller (main's Outputs phase, or --only-e16, which replaces only the e16_* rows)."""
    t = elevation_datum_tests(lev, lev_cols, cl, master)
    s = elevation_datum_summary(t)
    v = elevation_datum_verdict(s)
    ident = e16_identity_check(t)
    step(f"identity: depth rows against E5 at {DRAINAGE_DATUM:g} m, max |dNSE| = {ident:.2e}")
    if v["verdict"] != "not run":
        b, d = v["best"], v["depth"]
        step(f"best elevation datum {v['z0']:g} m AOD: CCW NSE {b['ccw_nse_median']:.3f} (depth {d['ccw_nse_median']:.3f}), "
             f"|bias| {b['ccw_abs_bias_median_m']:.3f} m ({d['ccw_abs_bias_median_m']:.3f}), Ranwell {b['ranwell_nse_median']:.3f} "
             f"({d['ranwell_nse_median']:.3f}), split {b['split_nse_median']:.3f} ({d['split_nse_median']:.3f}), "
             f"beta_3 <= 0 at {int(b['n_beta3_nonpositive'])} ({int(d['n_beta3_nonpositive'])})")
        step(f"beta_3 against the per-well datum at {v['z0']:g} m AOD: Spearman rho {b['rho_beta3_vs_datum']:+.2f}")
    step(f"E16 verdict: {v['verdict']}  {v['tests']}")
    t.to_csv(OUT_50_ELEV_DATUM_TESTS, index=False); saved(f"{OUT_50_ELEV_DATUM_TESTS.name} ({len(t)} rows)")
    s.to_csv(OUT_50_ELEV_DATUM_SUMMARY, index=False); saved(f"{OUT_50_ELEV_DATUM_SUMMARY.name} ({len(s)} rows)")
    return t, s, v, ident


# ──────────────────────────────────────────────────────────────────────────────
# E17: a drainage base per cluster, chosen from the modern record alone (1.20.0, D-287)
# ──────────────────────────────────────────────────────────────────────────────
# E16 found one base in elevation suits the western block (C3) and fails the open dune (C2). E17 gives each cluster
# its own base z_c m AOD, every well in the cluster at datum ground - z_c, with the base chosen from the modern record
# only (spec NRG_spec_E16_paperM_and_E17_cluster_base_2026-10-28, Martin 04:28 "S"):
#   S  the z of E16's elevation grid maximizing the median within-record split NSE of the cluster's wells (primary);
#   R  the median over member wells of the R2-maximizing datum as an elevation (03_09, max_R2_datum);
#   B  the median over member wells of Model B's zero-drainage level as an elevation (48_04, base_depth_B_m).
# The drier epochs (CCW 1989-96, Ranwell 1951-53) then test the primary candidate against the depth datum, cluster by
# cluster, by the rule fixed before the run (e17_verdict). C4 has no drier-epoch wells and is reported as untested.
def _lvl_rows(df: pd.DataFrame, col: str = "well") -> pd.DataFrame:
    """D-348: the rows of a per-well table a cluster-level quantity uses - every well but the reference wells
    Script 02 holds out of cluster level (In_Cluster_Level false: the boundary wells and the set-aside WMC3)."""
    from utils.cluster_series import in_cluster_level
    md = pd.read_csv(INT_MASTER_DATA)
    off = set(md.loc[~in_cluster_level(md), "Name_Original"].map(normalize_well_name))
    return df[~df[col].astype(str).map(normalize_well_name).isin(off)]


def _e17_cluster_of(master) -> dict:
    return {r["_n"]: int(r["Cluster"]) for _, r in _lvl_rows(master, "_n").iterrows()}   # D-348: cluster level


def e17_bases(t16: pd.DataFrame, master) -> pd.DataFrame:
    grounds = _e16_grounds()
    cof = _e17_cluster_of(master)
    t16 = _lvl_rows(t16)                               # D-348: each cluster's base from its cluster-level wells
    sp = t16[t16["test"].isin(["split_fwd", "split_rev"]) & (t16["datum_kind"] == "elevation") & t16["nse"].notna()]
    med = sp.groupby(["cluster", "z0_m_aod"])["nse"].median()

    def _elev(df, col):
        out = {}
        for w, d in zip(df["well"], df[col]):
            k = normalize_well_name(w)
            if k in grounds and k in cof and np.isfinite(d):
                out.setdefault(cof[k], []).append(grounds[k] - float(d))
        return {c: float(np.median(v)) for c, v in out.items()}

    base_r = _elev(pd.read_csv(OUT_03_WELL_OPTIMAL_DATUMS), "max_R2_datum")
    base_b = _elev(pd.read_csv(OUT_48_MODEL_AB), "base_depth_B_m")
    rows = []
    for c in sorted(CLUSTER_LABELS):
        mc = med.loc[c] if c in med.index.get_level_values(0) else pd.Series(dtype=float)
        rows.append({"cluster": c,
                     "base_S_m_aod": float(mc.idxmax()) if len(mc) else np.nan,
                     "split_nse_median_at_S": float(mc.max()) if len(mc) else np.nan,
                     "base_R_m_aod": base_r.get(c, np.nan), "base_B_m_aod": base_b.get(c, np.nan),
                     "n_member_wells": int(sum(1 for v in cof.values() if v == c))})
    return pd.DataFrame(rows)


def _e17_key(df: pd.DataFrame) -> pd.Series:
    tag = df["code"].astype(str) if "code" in df.columns else ""
    if "site_no" in df.columns:
        tag = np.where(df["test"] == "ranwell", df["site_no"].astype(str), tag)
    return df["well"].astype(str) + "|" + pd.Series(tag, index=df.index).astype(str)


def e17_cluster_table(t: pd.DataFrame) -> pd.DataFrame:
    """Per cluster and candidate: the drier-epoch medians, and the primary candidate's pass/fail against the depth datum."""
    t = _lvl_rows(t)                                   # D-348: cluster medians over cluster-level wells
    t = t.assign(key=_e17_key(t))
    rows = []
    for c in sorted(CLUSTER_LABELS):
        for kind in ("depth",) + tuple(E17_CANDIDATES):
            g = t[(t["cluster"] == c) & (t["datum_kind"] == kind)]
            ccw = g[(g["test"] == "ccw") & g["nse"].notna()]
            rw = g[(g["test"] == "ranwell") & g["nse"].notna()]
            rw = rw[rw["headline"].astype(bool)] if "headline" in rw.columns else rw.iloc[0:0]
            sp = g[g["test"].isin(["split_fwd", "split_rev"]) & g["nse"].notna()]
            fit = g[(g["test"] == "fit") & g["beta_3"].notna()]
            pos = fit[fit["beta_3"] > 0]
            rows.append({"cluster": c, "candidate": kind,
                         "datum_m_median": float(g.loc[g["test"] == "fit", "datum_m"].median()),
                         "ccw_n": int(len(ccw)), "ccw_nse_median": float(ccw["nse"].median()) if len(ccw) else np.nan,
                         "ccw_abs_bias_median_m": float(ccw["bias_m"].abs().median()) if len(ccw) else np.nan,
                         "ranwell_n": int(len(rw)), "ranwell_nse_median": float(rw["nse"].median()) if len(rw) else np.nan,
                         "split_nse_median": float(sp["nse"].median()) if len(sp) else np.nan,
                         "n_beta3_nonpositive": int((fit["beta_3"] <= 0).sum()),
                         "efold_median_months": float(pos["efold_months"].median()) if len(pos) else np.nan})
    return pd.DataFrame(rows)


def e17_verdict(t: pd.DataFrame) -> dict:
    """The rule fixed before the run (D-287). For the primary candidate, a cluster with drier-epoch wells passes if,
    on every drier-epoch test it has (CCW for C2, C3, C5 - D-348: C3o, C3f; Ranwell headline pairings for C1, C3), every well scored at
    the depth datum is still scored, the median NSE is at least as high as at the depth datum, and (CCW) the median
    |bias| is no larger. Supported: every testable cluster passes and no more wells site-wide have beta_3 <= 0.
    Not supported: more than half the testable clusters fail. Not resolved: otherwise."""
    prim = E17_PRIMARY_CANDIDATE
    t_all = t
    t = _lvl_rows(t).assign(key=_e17_key(_lvl_rows(t)))   # D-348: the per-cluster tests over cluster-level wells
    per = {}
    for c in sorted(CLUSTER_LABELS):
        checks = []
        for test in ("ccw", "ranwell"):
            sub = t[(t["test"] == test) & (t["cluster"] == c)]
            if test == "ranwell" and "headline" in sub.columns:
                sub = sub[sub["headline"].astype(bool)]
            dep = sub[(sub["datum_kind"] == "depth") & sub["nse"].notna()]
            if dep.empty:
                continue
            can = sub[(sub["datum_kind"] == prim) & sub["nse"].notna()]
            ok = set(dep["key"]) <= set(can["key"]) and can["nse"].median() >= dep["nse"].median()
            if test == "ccw" and ok:
                ok = can["bias_m"].abs().median() <= dep["bias_m"].abs().median()
            checks.append((test, bool(ok)))
        if checks:
            per[c] = {"tests": checks, "pass": all(ok for _t, ok in checks)}
    fit = t_all[(t_all["test"] == "fit") & t_all["beta_3"].notna()]   # site-wide count: every well, as before
    nonpos = {k: int((fit.loc[fit["datum_kind"] == k, "beta_3"] <= 0).sum()) for k in ("depth", prim)}
    ident = nonpos[prim] <= nonpos["depth"]
    n_fail = sum(1 for v in per.values() if not v["pass"])
    if per and n_fail == 0 and ident:
        verdict = "supported"
    elif per and n_fail > len(per) / 2:
        verdict = "not supported"
    elif per:
        verdict = "not resolved"
    else:
        verdict = "not run"
    return {"verdict": verdict, "per": per, "identified": ident, "nonpos": nonpos, "primary": prim}


def e17_report(rr, bases: pd.DataFrame, ctab: pd.DataFrame, v: dict) -> None:
    code = {"supported": 1, "not resolved": 0, "not supported": -1, "not run": -2}[v["verdict"]]
    rr.add("e17_verdict", code, unit="code",
           note=f"a drainage base per cluster, candidate {v['primary']}: {v['verdict']} (1 supported, 0 not resolved, "
                "-1 not supported, -2 not run); rule fixed before the run (D-287)")
    for r in bases.itertuples():
        for kind in E17_CANDIDATES:
            rr.add(f"e17_base_{kind}_C{r.cluster}_m_aod", getattr(r, f"base_{kind}_m_aod"), unit="m AOD",
                   note=f"C{r.cluster} drainage base under candidate {kind} (E17, chosen from the modern record only)")
    for r in ctab.itertuples():
        tag = "depth" if r.candidate == "depth" else r.candidate
        for col, unit in (("ccw_nse_median", ""), ("ccw_abs_bias_median_m", "m"), ("ranwell_nse_median", ""),
                          ("split_nse_median", ""), ("efold_median_months", "months")):
            val = getattr(r, col)
            if np.isfinite(val):
                rr.add(f"e17_{col}_C{r.cluster}_{tag}", val, unit=unit,
                       note=f"C{r.cluster}, {col.replace('_', ' ')}, {'depth datum' if tag == 'depth' else 'candidate ' + tag} (E17)")
        for col in ("ccw_n", "ranwell_n"):
            if getattr(r, col) and tag == "depth":
                rr.add(f"e17_{col}_C{r.cluster}", getattr(r, col), unit="count", note=f"C{r.cluster} wells or pairings in the {col[:-2]} test (E17)")
    for c, d in v["per"].items():
        rr.add(f"e17_cluster_pass_C{c}", int(d["pass"]), unit="flag",
               note=f"C{c}: candidate {v['primary']} passes the drier-epoch tests it has ({', '.join(t_ for t_, _ in d['tests'])}) (D-287)")
    for k, n in v["nonpos"].items():
        rr.add(f"e17_n_beta3_nonpositive_{k}", n, unit="count", note=f"wells with beta_3 <= 0, comparison window, {k} (E17)")


def run_e17(lev, lev_cols, cl, master, t16: pd.DataFrame | None = None):
    if t16 is None:
        if not OUT_50_ELEV_DATUM_TESTS.exists():
            warn("E16's tests are not on disk — E17 needs them for its split-chosen bases; run E16 first")
            return None
        t16 = pd.read_csv(OUT_50_ELEV_DATUM_TESTS)
    bases = e17_bases(t16, master)
    bmap = {k: dict(zip(bases["cluster"], bases[f"base_{k}_m_aod"])) for k in E17_CANDIDATES}
    for r in bases.itertuples():
        step(f"C{r.cluster}: base S {r.base_S_m_aod:g}, R {r.base_R_m_aod:.2f}, B {r.base_B_m_aod:.2f} m AOD")
    specs = [("depth", np.nan, f"depth {DRAINAGE_DATUM:g} m")] + [(k, np.nan, f"base {k}") for k in E17_CANDIDATES]

    def datum_of(kind, z0, g, c):
        if kind == "depth":
            return DRAINAGE_DATUM
        b = bmap[kind].get(c, np.nan)
        return g - b if np.isfinite(b) else np.nan

    t = elevation_datum_tests(lev, lev_cols, cl, master, specs=specs, datum_of=datum_of)
    ctab = e17_cluster_table(t)
    v = e17_verdict(t)
    for c, d in v["per"].items():
        step(f"C{c} ({', '.join(t_ for t_, _ in d['tests'])}): {'pass' if d['pass'] else 'fail'}")
    step(f"beta_3 <= 0: depth {v['nonpos']['depth']}, {v['primary']} {v['nonpos'][v['primary']]}")
    step(f"E17 verdict: {v['verdict']}")
    t.to_csv(OUT_50_CLUSTER_BASE_TESTS, index=False); saved(f"{OUT_50_CLUSTER_BASE_TESTS.name} ({len(t)} rows)")
    out = ctab.merge(bases, on="cluster", how="left")
    out.to_csv(OUT_50_CLUSTER_BASE_SUMMARY, index=False); saved(f"{OUT_50_CLUSTER_BASE_SUMMARY.name} ({len(out)} rows)")
    return bases, ctab, v


# ──────────────────────────────────────────────────────────────────────────────
def main(no_fig: bool = False) -> int:
    banner("50b", "Which datum and drainage base the record supports (D-225, D-229, D-286, D-287)", version=__version__)
    DIR_50B.mkdir(parents=True, exist_ok=True)

    phase(1, "Inputs")
    lev, lev_cols, cl, master = load_inputs()
    info(f"{len(master)} reference wells; lengths {', '.join(LENGTHS)} (fitted monthly changes); "
         f"split {MODEL_AB_SPLIT_DATE}; stability tolerance {RECLEN_STABLE_TOL:g}")

    mhw = mhw_depths()          # the MHW form's per-well datum (split series)
    phase(2, "Which datum does the drier past support? (1.1.0, D-225)")
    locs = pd.read_csv(INT_LOCATIONS)
    loc_forest = {normalize_well_name(n): bool(f) for n, f in zip(locs["Name"], locs["in_forest"])}
    ccw_d = ccw_by_datum(lev, lev_cols, cl, loc_forest)
    split_d = split_by_datum(lev, lev_cols, cl, master)
    proj_d = projection_by_datum(lev, lev_cols, cl, master, loc_forest)
    best, lo, hi, _med = supported_datum(ccw_d) if len(ccw_d) else (np.nan, np.nan, np.nan, None)
    step(f"CCW-supported datum {best:g} m (band {lo:g}–{hi:g} m, within {RECLEN_DATUM_NSE_TOL:g} NSE of the best)")
    checks_d = datum_identity_checks(ccw_d, split_d, proj_d)
    for k, v in checks_d.items():
        (step if (np.isfinite(v) and v < 1e-9) else warn)(f"{k}: {v:.3g}")
    rw = ranwell_by_datum(lev, lev_cols, cl)
    verdict = None
    if len(rw):
        rbest, rlo, rhi, rspread, _ = ranwell_supported(rw)
        verdict = ranwell_verdict(rlo, rhi, lo, hi)
        step(f"Ranwell 1951-53 (E9, D-229): {rw['site_no'].nunique()} sites, {rw['well'].nunique()} wells; "
             + (f"supported datum {rbest:g} m (band {rlo:g}–{rhi:g} m)" if np.isfinite(rbest)
                else f"median NSE moves {rspread:.3f} over the grid") + f" — {verdict}")
        v44 = ranwell_identity_check(rw)
        checks_d["datum_vs44_max_abs_nse_diff"] = v44
        (step if (np.isfinite(v44) and v44 < 1e-6) else warn)(f"datum_vs44_max_abs_nse_diff: {v44:.3g}")
        rw.to_csv(OUT_50_RANWELL_DATUM, index=False); saved(f"{OUT_50_RANWELL_DATUM.name} ({len(rw)} rows)")
    ccw_d.to_csv(OUT_50_CCW_DATUM, index=False); saved(f"{OUT_50_CCW_DATUM.name} ({len(ccw_d)} rows)")
    split_d.to_csv(OUT_50_SPLIT_DATUM, index=False); saved(f"{OUT_50_SPLIT_DATUM.name} ({len(split_d)} rows)")
    # J-6: the same split, kept month by month for both forms, so scenario 1 can be drawn
    split_s = split_series(lev, lev_cols, cl, master, mhw=mhw)
    split_s.to_csv(OUT_50_SPLIT_SERIES, index=False); saved(f"{OUT_50_SPLIT_SERIES.name} ({len(split_s)} rows)")
    plot_split_series(split_s); saved(OUT_50_SPLIT_FIG.name)
    proj_d.to_csv(OUT_50_PROJ_DATUM, index=False); saved(f"{OUT_50_PROJ_DATUM.name} ({len(proj_d)} rows)")

    phase(3, "Model A(ii): one drainage base in elevation, scored on the forward tests (E16, 1.19.0, D-286)")
    e16 = run_e16(lev, lev_cols, cl, master)

    phase(4, "A drainage base per cluster, chosen from the modern record (E17, 1.20.0, D-287)")
    e17 = run_e17(lev, lev_cols, cl, master, e16[0])

    phase(5, "Outputs")
    rr = ReportNumbers()
    beta3_bound_report(rr, {"ranwell": (rw, "beta_3", "E9's Ranwell hindcast (50_10)")})   # 1.25.0 (D-332)
    if len(ccw_d):
        datum_report(rr, ccw_d, split_d, proj_d, checks_d)
    water_balance_report(rr, cl)
    if len(rw):
        ranwell_report(rr, rw, lo, hi)
    e16_report(rr, e16[1], e16[2], e16[3], e16[0])
    if e17 is not None:
        e17_report(rr, *e17)
    rr.save(OUT_50B_REPORT_NUMBERS); saved(f"{OUT_50B_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    if not no_fig and len(ccw_d):
        plot_datum(ccw_d, split_d, proj_d, best, lo, hi, rw)
    done("50b")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Which datum and drainage base the record supports (D-225, D-229, D-286, D-287)")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figure")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
