"""
50c_transfer.py — Transfer between wells: neighbour, cluster and placement (T-173, D-268, D-282, D-290).

Script 50 suite, step 50c (J-15, T-208; Martin 2026-11-24: five families, numbered 50a-50e,
all opt-in). Split from 50_record_length.py 1.30.0, whose full version history is kept in git and in
50a_record_length.py; every function moved whole with its dated comments. Shared helpers live in
utils/reclen_common.py.
"""
from __future__ import annotations

__version__ = "1.2.0"  # 2026-11-27 (D-349 (1), A3, D-348 leftovers): every fit states its window; the levels come cut at RECORD_FIT_START (reclen_common 1.1.0) and E12's centroid series is cut the same way, so the reverse split scores 2010-17 and E12's shift covers the months the fit saw (N7); T-173's centroids are medians over cluster-level wells (every well still a target), its per-cluster medians over cluster-level wells and its open-dune/forest medians without edge wells (D-349 (8)). Was "1.1.0"  # 2026-11-27 (D-348): E12b placement centroids from cluster-level members (every well still placed); diagram names C3o and C3f. Was "1.0.0"  # Hollingham (2026) - 2026-11-24 (J-15, T-208). Split from Script 50 1.30.0.

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
    DIR_50C, OUT_50C_REPORT_NUMBERS, OUT_50_PER_WELL, OUT_50_BY_CLUSTER, OUT_50_CCW, OUT_50_STABLE, OUT_50_FIG,
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


def transfer_report(rr, trule=None, nbt_mhw=None, nbt_b=None) -> None:
    """J-15: the transfer keys, moved whole from Script 50's report_numbers() (lines kept as they were)."""
    # 1.29.0 (J-23, T-173 under Model B): per cluster and the open dune / forest, the median r2 and |bias| with
    # own and neighbour coefficients, and the criterion Martin set before the numbers were seen (2026-11-20):
    # shape transfers where the median neighbour r2 is within TRANSFER_R2_TOL of own, level where the median
    # |bias| is within TRANSFER_BIAS_TOL_M of own. C4 is reported, not claimed (beta_3 not identified).
    if nbt_b is not None and not nbt_b.empty:
        _b = nbt_b.assign(abs_bias_m=nbt_b["bias_m"].abs())
        # 1.2.0 (D-348, D-349 (8)): a cluster's median over its cluster-level wells; open dune / forest without the
        # edge wells; "all" keeps every well
        _lvl = _b["in_cluster_level"].astype(bool) if "in_cluster_level" in _b.columns else pd.Series(True, index=_b.index)
        _edge = _b["edge"].astype(bool) if "edge" in _b.columns else pd.Series(False, index=_b.index)
        _grp = [(f"C{int(c)}", g) for c, g in _b[_lvl].groupby("cluster")]
        _grp += [("open_dune", _b[~_b["in_forest"].astype(bool) & ~_edge]),
                 ("forest", _b[_b["in_forest"].astype(bool) & ~_edge]),
                 ("all", _b)]
        for _g, _d in _grp:
            _pv = _d.pivot_table(index="well", columns="source", values=["r2", "abs_bias_m"])
            if ("r2", "own") not in _pv.columns or ("r2", "neighbour") not in _pv.columns:
                continue
            _pv = _pv.dropna(subset=[("r2", "own"), ("r2", "neighbour")])
            if _pv.empty:
                continue
            _n = len(_pv)
            med = {(m, s_): float(_pv[(m, s_)].median()) for m in ("r2", "abs_bias_m")
                   for s_ in ("own", "neighbour", "centroid") if (m, s_) in _pv.columns}
            for (m, s_), v in med.items():
                rr.add(f"transfer_B_median_{m}_{s_}_{_g}", v, unit="m" if m == "abs_bias_m" else "",
                       note=f"Model B neighbour transfer (T-173): median post-2018 {'|bias|' if m == 'abs_bias_m' else 'r2'}, "
                            f"{s_} coefficients (intercept borrowed with the betas); n = {_n} wells ({_g})")
            d_r2 = med[("r2", "neighbour")] - med[("r2", "own")]
            d_b = med[("abs_bias_m", "neighbour")] - med[("abs_bias_m", "own")]
            rr.add(f"transfer_B_d_r2_{_g}", d_r2, unit="", note=f"median neighbour r2 less median own r2, Model B ({_g})")
            rr.add(f"transfer_B_d_abs_bias_m_{_g}", d_b, unit="m",
                   note=f"median neighbour |bias| less median own |bias|, Model B ({_g})")
            rr.add(f"transfer_B_shape_holds_{_g}", float(d_r2 >= -TRANSFER_R2_TOL), unit="flag",
                   note=f"1 if the median neighbour r2 is within {TRANSFER_R2_TOL:g} of own (Martin's criterion, 2026-11-20)")
            rr.add(f"transfer_B_level_holds_{_g}", float(d_b <= TRANSFER_BIAS_TOL_M), unit="flag",
                   note=f"1 if the median neighbour |bias| is within {TRANSFER_BIAS_TOL_M:g} m of own (Martin's criterion)")
            rr.add(f"transfer_B_wells_n_{_g}", float(_n), unit="count", note=f"wells in the Model B transfer test ({_g})")
        _d = _b[_b["source"] == "neighbour"]["distance_m"].dropna()
        if len(_d):
            rr.add("transfer_B_neighbour_distance_median_m", float(_d.median()), unit="m",
                   note="median distance from a well to its borrowed neighbour (nearest other well with a pre-2018 fit)")
    # T-173b (2026-11-08): the transfer rule's quotable values, so Paper 1 can carry them as
    # number fields rather than typed literals (D-220). Keys mirror 50_52's own columns.
    if trule is not None and not trule.empty:
        _pred = trule[trule["scope"] == "predictor"]
        for _, _r in _pred.iterrows():
            rr.add(f"transfer_rho_{_r['well']}", float(_r["gain_nse"]), unit="",
                   note="Spearman of this predictor against the change in NSE from borrowing")
        _pairs = trule[trule["scope"] == "pair"]
        if not _pairs.empty:
            rr.add("transfer_pairs_n", float(len(_pairs)), unit="",
                   note="well-neighbour pairs in the transfer test")
            for _src, _tag in (("own_nse", "own"), ("neighbour_nse", "neighbour"),
                               ("centroid_nse", "centroid")):
                if _src in _pairs.columns and _pairs[_src].notna().any():
                    rr.add(f"transfer_median_nse_{_tag}", float(_pairs[_src].median()), unit="",
                           note=f"median post-2018 NSE, {_tag} coefficients")
            rr.add("transfer_fail_neighbour_n",
                   float((_pairs["neighbour_nse"] < -1).sum()), unit="",
                   note="wells where a neighbour's coefficients score below -1 NSE")
            rr.add("transfer_fail_own_n", float((_pairs["own_nse"] < -1).sum()), unit="",
                   note="wells where their OWN coefficients score below -1 NSE")
            _pl = (_pairs[_pairs["in_cluster_level"].astype(bool)] if "in_cluster_level" in _pairs.columns
                   else _pairs)    # 1.2.0 (D-348): a cluster's median over its cluster-level wells
            for _c, _g in _pl.groupby("cluster"):
                if pd.notna(_c):
                    rr.add(f"transfer_median_gain_C{int(_c)}", float(_g["gain_nse"].median()),
                           unit="", note="median change in NSE from borrowing, this cluster")
        # 1.25.0 (D-332): the same three medians with Model A at mean high water. Every fit at the fitted well's
        # MHW floor, every run at the TARGET well's; the centroid is the median of its members' MHW-floor
        # coefficients run at the target's floor (a centroid has no ground level, so no floor of its own).
        if nbt_mhw is not None and not nbt_mhw.empty:
            _pm = nbt_mhw.pivot_table(index=["well", "cluster"], columns="source", values="nse")
            for _tag in ("own", "neighbour", "centroid"):
                if _tag in _pm.columns and _pm[_tag].notna().any():
                    rr.add(f"transfer_median_nse_{_tag}_mhw", float(_pm[_tag].median()), unit="",
                           note=f"median post-2018 NSE, {_tag} coefficients, Model A at each well's depth to mean "
                                f"high water (run at the target well's floor); n = {int(_pm[_tag].notna().sum())} wells")
                    rr.add(f"transfer_fail_{_tag}_n_mhw", float((_pm[_tag] < -1).sum()), unit="",
                           note=f"wells scoring below -1 NSE on {_tag} coefficients, Model A at mean high water")
            rr.add("transfer_wells_n_mhw", float(len(_pm)), unit="",
                   note="wells in the neighbour transfer test at mean high water (a ground level and a pre-2018 fit)")
        for _, _r in trule[trule["scope"] == "band"].iterrows():
            _k = (str(_r["well"]).replace("<", "lt").replace(">", "gt")
                  .replace(".", "p").replace(" m", "").replace("-", "_"))
            rr.add(f"transfer_band_{_k}_median", float(_r["gain_nse"]), unit="",
                   note="median change in NSE, this band of mean-depth difference")
            rr.add(f"transfer_band_{_k}_frac_lose", float(_r["neighbour_nse"]), unit="fraction",
                   note="share of pairs in this band losing more than 0.25 NSE")


def transfer_rule(nbt, lev, lev_cols, master) -> pd.DataFrame:
    """T-173b, Martin 2026-11-08: "work out why this difference is occurring and how other
    managers at other sites can see where it's worth borrowing against a neighbour or not".

    T-173 showed that borrowing a neighbour's coefficients is nearly free in some clusters
    and ruinous in others. This asks WHICH MEASURABLE PROPERTY of a pair of wells decides
    that, and it tests the candidates against the measured outcome rather than asserting one:

        d_mean_depth_m   how far apart the two wells sit in MEAN water-table depth
        r_records        how well the two observed records correlate, pre-2018
        distance_m       how far apart they are on the ground
        d_beta_1/2/3     how different their fitted coefficients are
        d_amplitude_m    how different their seasonal ranges are

    Every predictor is computed on the PRE-2018 side only -- the side the fits were taken
    from -- so a user of the rule needs nothing from the period they want to predict.

    The banded rows (scope="band") are the usable form: the median change in NSE, and the
    share of pairs losing more than 0.25, for each band of mean-depth difference. A site
    with two dipwells and a tape measure can place itself in that table without fitting
    anything, which is the point of the exercise.
    """
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    piv = nbt.pivot_table(index="well", columns="source", values="nse")
    if "own" not in piv.columns or "neighbour" not in piv.columns:
        return pd.DataFrame()
    nb = nbt[nbt["source"] == "neighbour"].set_index("well")
    coef = {}
    for _, r in master.iterrows():
        try:
            coef[r["_n"]] = (float(r["beta_1_recharge"]), float(r["beta_2_atmospheric_draw"]),
                             float(r["beta_3_drainage"]))
        except (KeyError, TypeError, ValueError):
            pass

    rows = []
    for w in piv.index:
        if w not in nb.index:
            continue
        n = nb.loc[w, "neighbour"]
        ca, cb = lev_cols.get(w), lev_cols.get(n)
        if not isinstance(n, str) or ca is None or cb is None:
            continue
        both = lev[[ca, cb]]
        both = both[both.index < split].dropna()
        if len(both) < 24:          # two seasons of overlap, or the comparison means nothing
            continue
        a, b = both[ca], both[cb]
        rec = dict(scope="pair", well=w, neighbour=n,
                   cluster=int(nb.loc[w, "cluster"]) if pd.notna(nb.loc[w, "cluster"]) else None,
                   in_cluster_level=bool(nb.loc[w, "in_cluster_level"]) if "in_cluster_level" in nb.columns else True,
                   n_shared_months=int(len(both)),
                   own_nse=float(piv.loc[w, "own"]),
                   neighbour_nse=float(piv.loc[w, "neighbour"]),
                   centroid_nse=(float(piv.loc[w, "centroid"])
                                 if "centroid" in piv.columns else np.nan),
                   # neighbour MINUS own: an improvement is positive, as in 50_51
                   gain_nse=float(piv.loc[w, "neighbour"] - piv.loc[w, "own"]),
                   distance_m=float(nb.loc[w, "distance_m"]) if pd.notna(nb.loc[w, "distance_m"]) else np.nan,
                   d_mean_depth_m=float(abs(a.mean() - b.mean())),
                   r_records=float(a.corr(b)),
                   d_amplitude_m=float(abs((a.max() - a.min()) - (b.max() - b.min()))))
        if w in coef and n in coef:
            for i, k in enumerate(("d_beta_1", "d_beta_2", "d_beta_3")):
                rec[k] = float(abs(coef[w][i] - coef[n][i]))
        rows.append(rec)
    pairs = pd.DataFrame(rows)
    if pairs.empty:
        return pairs

    # which predictor actually decides it
    for c in ("d_mean_depth_m", "r_records", "distance_m", "d_amplitude_m",
              "d_beta_1", "d_beta_2", "d_beta_3"):
        if c not in pairs.columns:
            continue
        g = pairs[[c, "gain_nse"]].dropna()
        if len(g) > 4:
            rows.append(dict(scope="predictor", well=c, n_shared_months=len(g),
                             gain_nse=float(g[c].corr(g["gain_nse"], method="spearman"))))

    # the banded rule
    edges = [0.0, 0.1, 0.2, 0.4, 0.8, np.inf]
    names = ["<0.1 m", "0.1-0.2 m", "0.2-0.4 m", "0.4-0.8 m", ">0.8 m"]
    pairs["_band"] = pd.cut(pairs["d_mean_depth_m"], bins=edges, labels=names,
                            include_lowest=True)
    for bname, g in pairs.groupby("_band", observed=True):
        rows.append(dict(scope="band", well=str(bname), n_shared_months=int(len(g)),
                         gain_nse=float(g["gain_nse"].median()),
                         own_nse=float(g["gain_nse"].min()),
                         neighbour_nse=float((g["gain_nse"] < -0.25).mean())))
    out = pd.DataFrame(rows).drop(columns=["_band"], errors="ignore")
    return out


def plot_transfer_rule(tr) -> None:
    """T-173b: the predictor that decides transfer, and the rule it gives.

    Left, the relationship itself -- the change in NSE against how far apart the two wells
    sit in mean water-table depth, coloured by cluster. Right, the same thing as the table a
    manager would use: median change and the share of pairs that lose more than 0.25 NSE,
    by band of depth difference.
    """
    import matplotlib
    import matplotlib.pyplot as plt
    if tr is None or tr.empty:
        return
    pairs = tr[tr["scope"] == "pair"]
    bands = tr[tr["scope"] == "band"]
    if pairs.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.6),
                             gridspec_kw={"width_ratios": [1.15, 1.0]})

    ax = axes[0]
    for c in sorted(pairs["cluster"].dropna().unique()):
        g = pairs[pairs["cluster"] == c]
        ax.scatter(g["d_mean_depth_m"], g["gain_nse"], s=30, alpha=0.9,
                   color=CLUSTER_COLOURS.get(int(c), "#777777"),
                   edgecolors="white", linewidths=0.4,
                   label=f"{CLUSTER_LABELS.get(int(c), f'C{int(c)}')}  n={len(g)}")
    ax.axhline(0.0, color="#777777", lw=0.9, ls=":")
    ax.set_yscale("symlog", linthresh=1.0, linscale=1.2)
    _a = float(np.nanmax(np.abs(pairs["gain_nse"].values)))
    ax.set_ylim(-max(3.0, _a * 1.2), max(3.0, _a * 1.2))
    ax.set_yticks([-30, -10, -3, -1, 0, 1, 3, 10, 30])
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlabel("difference in MEAN water-table depth between the two wells (m)", fontsize=9)
    ax.set_ylabel("change in NSE from borrowing (neighbour \u2212 own)", fontsize=9)
    ax.tick_params(labelsize=9)
    # upper right: the lower left sits over the C2/C3 points that make the trend
    ax.legend(fontsize=7.5, loc="upper right", framealpha=0.92, labelspacing=0.3)
    _rho = tr[(tr["scope"] == "predictor") & (tr["well"] == "d_mean_depth_m")]
    _r = f"{_rho['gain_nse'].iloc[0]:+.2f}" if not _rho.empty else "n/a"
    ax.set_title(f"Mean-depth difference decides it  (Spearman \u03c1 = {_r})\n"
                 "above the line the neighbour's fit is BETTER; below it, POORER",
                 fontsize=9, loc="left")

    ax = axes[1]
    if not bands.empty:
        order = ["<0.1 m", "0.1-0.2 m", "0.2-0.4 m", "0.4-0.8 m", ">0.8 m"]
        b = bands.set_index("well").reindex([o for o in order if o in set(bands["well"])])
        y = np.arange(len(b))
        ax.barh(y, b["neighbour_nse"] * 100.0, color="#b2182b", alpha=0.85, height=0.6)
        for i, (_, r) in enumerate(b.iterrows()):
            ax.text(2, i, f"n={int(r['n_shared_months'])}, median {r['gain_nse']:+.2f} NSE",
                    va="center", ha="left", fontsize=8.5, color="white"
                    if r["neighbour_nse"] * 100 > 35 else "#333333")
        ax.set_yticks(y)
        ax.set_yticklabels(b.index, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(0, 105)
        ax.set_xlabel("% of pairs that lose more than 0.25 NSE by borrowing", fontsize=9)
        ax.set_ylabel("difference in mean depth", fontsize=9)
        ax.tick_params(labelsize=9)
        ax.set_title("The rule, as a site without a model could use it", fontsize=9, loc="left")
    fig.suptitle("T-173b \u2014 what decides whether a neighbour's model transfers?\n"
                 "not distance, not how well the two records correlate, not how alike the "
                 "fitted coefficients are \u2014 how far apart the wells sit in MEAN DEPTH",
                 fontsize=9)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    render_figure(fig, OUT_50_TRANSFER_FIG)
    plt.close(fig)


def plot_neighbour_transfer(nbt) -> None:
    """T-173, Laurence Jones's question: can a well be modelled from a NEIGHBOUR's fit?

    Three sources, every one fitted pre-2018 and scored post-2018, so none has seen the
    period it is judged on: the well's OWN fit, its nearest neighbour's, and its cluster
    CENTROID's. The paired design is the point -- each well appears three times, so the
    comparison is within a well and the panel can be read down a column.

    Drawn as paired points rather than three box plots: a box plot would answer "how do the
    three distributions compare", which is not the question. The question is whether the
    SAME well does worse on a borrowed fit, and that is a line between two points.
    """
    import matplotlib
    import matplotlib.pyplot as plt
    if nbt is None or nbt.empty:
        return
    piv = nbt.pivot_table(index="well", columns="source", values="nse")
    piv = piv.dropna(subset=["own"])
    order = [c for c in ("own", "neighbour", "centroid") if c in piv.columns]
    if len(order) < 2:
        return
    COL = {"own": "#1b1b1b", "neighbour": "#1b9e77", "centroid": "#7570b3"}
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.4),
                             gridspec_kw={"width_ratios": [1.25, 1.0]})

    ax = axes[0]
    xs = list(range(len(order)))
    for _, row in piv.iterrows():
        ys = [row.get(k, np.nan) for k in order]
        ax.plot(xs, ys, "-", color="#999999", lw=0.6, alpha=0.55, zorder=1)
    for i, k in enumerate(order):
        v = piv[k].dropna()
        ax.scatter([i] * len(v), v, s=22, color=COL[k], zorder=3, label=None)
        ax.plot([i - 0.22, i + 0.22], [v.median()] * 2, "-", color=COL[k], lw=2.6, zorder=4)
        # get_xaxis_transform(): x in DATA coords (the category position), y in AXES coords.
        # transAxes for both put the third label at x=2 of a 0-1 axis -- off the panel, and it
        # dragged tight_layout into squashing the axes to fit the stray text.
        ax.text(i, 0.97, f"median {v.median():+.2f}", ha="center", va="top",
                fontsize=9, color=COL[k], transform=ax.get_xaxis_transform())
    ax.set_xticks(xs)
    ax.set_xticklabels(["own fit", "nearest\nneighbour", "cluster\ncentroid"], fontsize=9)
    ax.set_ylabel("NSE post-2018 (fitted pre-2018)", fontsize=9)
    ax.axhline(0.0, color="#777777", lw=0.9, ls=":")
    # SYMLOG, not a clip. A linear axis cropped at -1 hid the finding: borrowing does not
    # merely cost a little at the median, it FAILS OUTRIGHT at a fifth of wells (14 of 66
    # below -1 NSE on a neighbour's fit, four below -13, against 2 on a well's own). Those
    # are the wells a reader most needs to see, and they were the ones off the axis.
    # Linear from +1 down to -1, logarithmic below, so the bulk keeps its resolution and
    # the failures stay on the page.
    ax.set_yscale("symlog", linthresh=1.0, linscale=1.2)
    _lo = float(np.nanmin(piv[order].values))
    ax.set_ylim(min(-30.0, _lo * 1.2), 1.0)
    ax.set_yticks([1, 0.5, 0, -0.5, -1, -3, -10, -30])
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: f"{v:g}"))
    ax.tick_params(labelsize=9)
    _bad = {k: int((piv[k] < -1).sum()) for k in order}
    # the counts ride the suptitle: appended here the title overran the right panel's
    ax.set_title("Every well, three sources of coefficients", fontsize=10, loc="left")

    ax = axes[1]
    if "neighbour" in piv.columns and "distance_m" in nbt.columns:
        nb = nbt[nbt["source"] == "neighbour"].set_index("well")
        # neighbour MINUS own, so an improvement reads as a POSITIVE change in NSE
        # (Martin, 2026-11-08). The other way round a gain plotted below the line, which
        # is the opposite of how anyone reads a skill axis.
        m = pd.DataFrame({"d": nb["distance_m"].reindex(piv.index),
                          "gain": piv["neighbour"] - piv["own"],
                          "cluster": nb["cluster"].reindex(piv.index)}).dropna()
        # Coloured by CLUSTER (Martin, 2026-11-08: "indicate which side is a better fit and
        # which side is a poorer fit, so that we can see where the clusters actually end
        # up"). A single colour answered "how big is the loss"; it could not answer whether
        # the wells that transfer badly belong to one part of the site.
        for c in sorted(m["cluster"].unique()):
            g = m[m["cluster"] == c]
            # the cluster's MEDIAN loss rides its legend entry: the question this panel is
            # asked is where the clusters end up, and a median answers it in one number
            # where a scatter of five points does not
            ax.scatter(g["d"], g["gain"], s=30, alpha=0.9,
                       color=CLUSTER_COLOURS.get(int(c), "#777777"),
                       edgecolors="white", linewidths=0.4,
                       label=f"{CLUSTER_LABELS.get(int(c), f'C{int(c)}')}  "
                             f"n={len(g)}, median {g['gain'].median():+.2f}")
        ax.axhline(0.0, color="#777777", lw=0.9, ls=":")
        ax.set_yscale("symlog", linthresh=1.0, linscale=1.2)
        _a = float(np.nanmax(np.abs(m["gain"].values))) if len(m) else 1.0
        _lim = max(3.0, _a * 1.2)
        ax.set_ylim(-_lim, _lim)
        ax.set_yticks([-10, -3, -1, 0, 1, 3, 10, 30])
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(
            lambda v, _: f"{v:g}"))
        # Which way is which, carried by the AXIS rather than by text in the panel: two
        # corner labels and a five-entry legend cannot share the same corners, and a reader
        # should not have to work out the sign of "own - neighbour" before reading the plot.
        ax.set_xlabel("distance to the nearest neighbour (m)", fontsize=9)
        # NOT in the ylabel: it is rotated 90 degrees, so arrow glyphs turn with it and the
        # two halves read bottom-to-top, which put "worse" at the bottom of a plot where
        # worse is at the top. The title cannot rotate and cannot collide with the legend.
        ax.set_ylabel("change in NSE from borrowing (neighbour \u2212 own)", fontsize=9)
        ax.tick_params(labelsize=9)
        # upper right: lower right sat on the "BELOW the line" label, and the upper-left
        # corner carries the "ABOVE" one
        ax.legend(fontsize=7.5, loc="upper right", framealpha=0.92, labelspacing=0.3,
                  title="cluster \u2014 median change in NSE", title_fontsize=7.5)
        if len(m) > 2:
            rho = m["d"].corr(m["gain"], method="spearman")   # ALL wells, not a clipped view
            ax.set_title("Does borrowing help or hurt, and where?  distance explains "
                         f"little (Spearman \u03c1 = {rho:+.2f})\n"
                         "above the dotted line the neighbour's fit is BETTER than the "
                         "well's own; below it, POORER",
                         fontsize=9, loc="left")

    fig.suptitle("T-173 — can a well be modelled from a neighbour's coefficients?\n"
                 "all fits are pre-2018 and every score is post-2018, so no fit has seen "
                 "what it is judged on\n"
                 + "wells scoring below −1 NSE (an outright failure): "
                 + ", ".join(f"{k} {v}" for k, v in _bad.items())
                 + f" of {len(piv)}", fontsize=9)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    render_figure(fig, OUT_50_NEIGHBOUR_FIG)
    plt.close(fig)


def neighbour_transfer(lev, lev_cols, cl, master, datum_of: dict | None = None,
                       intercept: bool = False) -> pd.DataFrame:
    """T-173: fit the model on a NEIGHBOURING well and run it here. Laurence Jones's test.

    Section 4.5 holds two results and neither is this one. Its paragraph 2 scores group numbers
    against each well's own on forecast skill; paragraph 3 reconstructs a well's average spring
    LEVEL from its nearest neighbour -- an MSL scalar, which Martin's correction of 2026-11-07
    notes is not a like-for-like water-level record, so it demonstrates record-FILLING. Neither
    reports r2 or mean error, and neither runs a neighbour's coefficients over this well's monthly
    series. That is what is built here.

    Three sources of coefficients, all fitted on the pre-2018 side and scored on the post-2018
    side, so every one is out of sample:
        own        the well's own fit             -- the ceiling
        neighbour  the nearest other well's fit   -- the transfer test
        centroid   the well's cluster centroid    -- the group number already in use

    Scored per month on r2 (shape and timing), bias (level, m) and NSE, so the three can be
    separated: a neighbour's coefficients may hold the shape while missing the level, and only
    the split says so. Reported per cluster, and the open dune separately, the forest being the
    known exception.

    1.25.0 (D-332): with `datum_of` ({well: datum, m}) every well is fitted at its own datum and every set of
    coefficients -- own, neighbour's or centroid -- is run at the TARGET well's datum; wells without one are left
    out. Passed each well's depth to mean high water, this is the MHW form's transfer test. The centroid is then
    the median of its members' coefficients at their own floors, run at the target's floor: a centroid has no
    ground level, so no MHW floor of its own, and this is a design choice (brief, Addendum 3). Without
    `datum_of` every datum is DRAINAGE_DATUM and the test is unchanged.

    1.29.0 (J-23, T-173 under Model B; Martin 2026-11-20): with intercept=True every fit is Model B and a
    borrowed set carries its intercept with its betas (full transfer: each set runs at its own implied datum,
    base - alpha/beta_3), so r2 says whether the shape transfers and bias whether the level does. The neighbour
    is still the nearest other well with a pre-2018 fit, whatever its cluster; the centroid is the median of its
    members' betas AND intercepts.
    """
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    if datum_of is not None:
        master = master[master["_n"].isin(datum_of)]

    def dat(w):
        return DRAINAGE_DATUM if datum_of is None else float(datum_of[w])
    loc = pd.read_csv(INT_LOCATIONS)
    # NB the key column must NOT start with an underscore: itertuples() renames such columns to
    # positional names, so r._k raises AttributeError (measured, 2026-11-07).
    loc["wkey"] = loc["Name"].map(normalize_well_name)
    xy = {r.wkey: (float(r.E), float(r.N)) for r in loc.itertuples()
          if pd.notna(r.E) and pd.notna(r.N)}
    forest = {r.wkey: bool(getattr(r, "in_forest", False)) for r in loc.itertuples()}
    # 1.2.0 (D-348, D-349 (8)): the centroid is built from cluster-level wells; every well is still a target
    from utils.cluster_series import in_cluster_level, is_edge
    lvl = set(master.loc[in_cluster_level(master), "_n"])

    # one pre-2018 fit per well, and per cluster centroid, reused for every target
    # 1.2.0 (D-349, A3): h is cut at RECORD_FIT_START (load_inputs), so "pre" is 2010-17
    fits, post, clust = {}, {}, {}
    for _, r in master.iterrows():
        col = lev_cols.get(r["_n"])
        if col is None:
            continue
        h = lev[col].dropna()
        pre, pst = h[h.index < split], h[h.index >= split]
        f = fit_frame(build_ssm_frame(pre, cl, lag=HEADLINE_LAG, drainage_datum=dat(r["_n"])), intercept)
        if f is None or len(pst.dropna()) < MODEL_AB_MIN_TEST_MONTHS + 1:
            continue
        fits[r["_n"]], post[r["_n"]], clust[r["_n"]] = f, pst, int(r["Cluster"])

    cent = {}
    for cid in sorted(set(clust.values())):
        members = [w for w, c in clust.items() if c == cid and w in lvl]
        if not members:
            continue
        cent[cid] = {k: float(np.median([fits[w][k] for w in members]))
                     for k in ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage")}
        cent[cid]["alpha"] = (float(np.median([fits[w]["alpha"] for w in members])) if intercept
                              else 0.0)          # 1.29.0: Model B's centroid carries the median intercept

    rows = []
    for w, pst in post.items():
        k = normalize_well_name(w)
        here = xy.get(k)
        nb = None
        if here is not None:
            cand = [(np.hypot(here[0] - p[0], here[1] - p[1]), ow)
                    for ow, f in fits.items()
                    for p in [xy.get(normalize_well_name(ow))] if p is not None and ow != w]
            if cand:
                nb = min(cand)
        for source, fit, extra in (("own", fits[w], {}),
                                   ("neighbour", fits[nb[1]] if nb else None,
                                    # D-035: store what was computed; the 0.1 m rounding that
                                    # used to be here was a display choice in a stored value
                                    {"neighbour": nb[1], "distance_m": nb[0]} if nb else {}),
                                   ("centroid", cent.get(clust[w]), {})):
            if fit is None:
                continue
            res = free_run(pst, cl, fit, intercept, base=dat(w))
            t = pst.dropna()
            months = pd.date_range(t.index[0], t.index[-1], freq="MS")
            clim = cl.reindex(months)
            if clim[["P_m", "PET"]].iloc[1:].isna().any().any():
                continue
            sim = pd.Series(simulate_ssm(float(t.iloc[0]), clim["P_m"].values[1:], clim["PET"].values[1:],
                                         fit["beta_1_recharge"], fit["beta_2_atmospheric_draw"],
                                         fit["beta_3_drainage"],
                                         drainage_datum=run_datum(fit, intercept, dat(w))),   # 1.29.0
                            index=months[1:])
            obs = t.iloc[1:].reindex(sim.index).dropna()
            if len(obs) < MODEL_AB_MIN_TEST_MONTHS:
                continue
            pr = sim.reindex(obs.index)
            rows.append({"well": w, "cluster": clust[w], "in_forest": forest.get(k, False),
                         "in_cluster_level": w in lvl, "edge": bool(is_edge(w)),
                         "source": source, "n": len(obs),
                         "r2": float(np.corrcoef(obs.values, pr.values)[0, 1] ** 2),
                         "bias_m": float((pr.values - obs.values).mean()),
                         "nse": float(res["nse"]), **extra})
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# E12: per well or per cluster? (1.12.0, D-268)
# ──────────────────────────────────────────────────────────────────────────────
BASIS_TESTS = ("ccw", "ranwell", "split")


def _centroid_fit(ra: pd.DataFrame, c: int, cl, intercept: bool, span: str, split=None):
    """The cluster centroid fitted on the same span as the per-well fit it stands in for: 'full' (the
    full record), 'window' (the last LCSC_DATA_LIMIT months), 'pre' or 'post' (either side of the split).
    Returns (fit, centroid series)."""
    h = ra[f"C{c}"].dropna()
    h = h[h.index >= pd.Timestamp(RECORD_FIT_START)]   # 1.2.0 (D-349 (1), A3, N7): D-347's window, as the wells are cut
    if span == "pre":
        h = h[h.index < split]
    elif span == "post":
        h = h[h.index >= split]
    if span == "window":   # 1.24.0 (D-322): the last LCSC_DATA_LIMIT calendar months, not rows
        f = _censored_well_fit(h, cl, None, LCSC_DATA_LIMIT, intercept, start=RECORD_FIT_START)
    else:
        f = fit_frame(build_ssm_frame(h, cl, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM), intercept)
    return (f if f is not None and f["beta_3_drainage"] > 0 else None), h


def basis_experiment(lev, lev_cols, cl, master, placement=None):
    """E12 (D-268): each hindcast and forecast on each well's own coefficients (as published) and on its
    cluster centroid's, fitted on the same span. On the cluster basis the run is shifted by the mean
    difference between the well and its centroid over the months the fit saw (as E8 runs a centroid at a
    well), so the test scores the dynamics, not the cluster's mean level; the Ranwell scoring removes the
    offset anyway. Returns (rows, identity checks).

    With `placement` = (L, {side: {well: placed cluster}}) (E12b, 1.17.0, D-282) the one arm run is 'placed':
    the cluster the well's first L months choose, shifted to that centroid over those L months alone, which is
    all a new well would have. The hindcasts are fitted on the full modern record, so side 'all' places them
    from the first L months of record; the split-sample test places and shifts from the first L months of its
    training side ('pre' forward, 'post' in reverse), so no tested month informs the placement. Wells the
    placement leaves out (records shorter than L) are skipped."""
    ra = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    bases = ("well", "cluster") if placement is None else ("placed",)
    p_len, p_map = (None, {}) if placement is None else placement

    def cluster_of(k, side="all"):
        if placement is None:
            return int(md.loc[k, "Cluster"])
        return p_map.get(side, {}).get(k)

    def shift_well(hw):
        return hw if placement is None else hw.iloc[:p_len]
    md = master.set_index("_n")
    clh = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    p_mean, pet_mean = float(clh["P_m"].mean()), float(clh["PET"].mean())
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    cache = {}

    def cfit(c, icpt, span):
        k = (c, icpt, span)
        if k not in cache:
            cache[k] = _centroid_fit(ra, c, cl, icpt, span, split)
        return cache[k]

    def shift_of(h_well, h_cent):
        common = h_well.index.intersection(h_cent.index)
        return float(h_well.loc[common].mean() - h_cent.loc[common].mean()) if len(common) else np.nan

    rows, chk = [], {}
    # 1. CCW 1989-96, fitted on the full modern record (Paper M 6.4)
    if paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists():
        obs, cmap = load_ccw()
        mdk = _model_a_store(pd.read_csv(INT_MASTER_DATA))
        mdk["k"] = mdk["Name_Original"].astype(str).str.lower().str.strip()
        adm = usable_codes(cmap, mdk.set_index("k"), obs)
        adm = adm[adm["admitted"]]
        first_month, last_month = obs["month"].min(), obs["month"].max()
        for r in adm.itertuples():
            k = normalize_well_name(r.well)
            col = lev_cols.get(k)
            if col is None or k not in md.index:
                continue
            o, _n = observed_series(obs, r.code, r.datum_offset_m)
            if o.empty:
                continue
            c = cluster_of(k)
            if c is None:
                continue
            hw = lev[col].dropna()
            for form, icpt in FORMS:
                for basis in bases:
                    if basis == "well":
                        f = _censored_well_fit(hw, cl, dry_bounds(col), None, icpt, start=RECORD_FIT_START)      # 1.24.0 (D-322)
                        f = f if f is not None and f["beta_3_drainage"] > 0 else None
                        sh = 0.0
                    else:
                        f, hc = cfit(c, icpt, "full")
                        sh = shift_of(shift_well(hw), hc)
                    row = {"test": "ccw", "well": k, "site_no": np.nan, "headline": np.nan, "cluster": c,
                           "form": form, "basis": basis, "direction": "", "shift_m": sh}
                    if f is not None:
                        betas = (f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"])
                        datum = run_datum(f, icpt)
                        h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=datum)
                        pred, _s = hindcast_well(clh, betas, h0, first_month, last_month, 1.0, drainage_datum=datum)
                        pred = pred + sh
                        common = o.index.intersection(pred.index)
                        nse, rmse, bias = get_metrics(o.loc[common], pred.loc[common])
                        row.update(n_test=int(len(common)), nse=float(nse), bias_m=float(bias), rmse_m=float(rmse),
                                   beta_1=betas[0], beta_2=betas[1], beta_3=betas[2])
                    rows.append(row)
    # 2. Ranwell 1951-53, fitted on the comparison window, scored as Script 44 scores it
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
            if col is None or k not in md.index or int(pr.site_no) not in obs_month.index.get_level_values(0):
                continue
            om = obs_month.loc[int(pr.site_no)]
            c = cluster_of(k)
            if c is None:
                continue
            hw = lev[col].dropna()
            for form, icpt in FORMS:
                for basis in bases:
                    if basis == "well":
                        f = _censored_well_fit(hw, cl, dry_bounds(col), LCSC_DATA_LIMIT, icpt, start=RECORD_FIT_START)   # 1.24.0 (D-322)
                        f = f if f is not None and f["beta_3_drainage"] > 0 else None
                    else:
                        f, _hc = cfit(c, icpt, "window")
                    row = {"test": "ranwell", "well": k, "site_no": int(pr.site_no), "headline": bool(pr.headline),
                           "cluster": c, "form": form, "basis": basis, "direction": "", "shift_m": np.nan}
                    if f is not None:
                        betas = (f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"])
                        run_d = run_datum(f, icpt)
                        h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=run_d)
                        sim, _spin = hindcast_well(clh, betas, h0, first, last, 1.0, drainage_datum=run_d)
                        mid = (sim + sim.shift(1)) / 2
                        mid.index = mid.index.to_period("M")
                        m = compare_offset_censored(om, mid.dropna(), float(pr.ground_m_od))
                        rr_ = (m["range_model_m"] / m["range_obs_m"]
                               if m.get("range_obs_m") and np.isfinite(m["range_obs_m"]) and m["range_obs_m"] > 0 else np.nan)
                        row.update(n_test=int(m["n"]), nse=float(m["nse_after_offset"]), r=float(m["r"]), range_ratio=rr_,
                                   beta_1=betas[0], beta_2=betas[1], beta_3=betas[2])
                    rows.append(row)
    # 3. the split-sample test (Script 48's), both directions
    for k, r in md.iterrows():
        col = lev_cols.get(k)
        if col is None:
            continue
        hw = lev[col].dropna()
        pre_h, post_h = hw[hw.index < split], hw[hw.index >= split]   # D-349 (A3): hw is cut at RECORD_FIT_START (load_inputs), so the reverse test scores 2010-17
        for form, icpt in FORMS:
            for direction, tr, te, span in (("fwd", pre_h, post_h, "pre"), ("rev", post_h, pre_h, "post")):
                c = cluster_of(k, span)
                if c is None:
                    continue
                for basis in bases:
                    if basis == "well":
                        # The split is a forecast test, D-281 tier 2, fitted as Script 48 fits it
                        # (dry months dropped): D-322 does not reach it (1.24.0 reverted this arm).
                        f = fit_frame(build_ssm_frame(tr, cl, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM), icpt)
                        sh = 0.0
                    elif basis == "cluster":
                        f, hc = cfit(c, icpt, span)
                        sh = shift_of(tr, hc)
                    else:   # placed: placement and shift from the first L months of the training side alone
                        f, hc = cfit(c, icpt, span)
                        sh = shift_of(shift_well(tr), hc)
                    res = free_run(te - sh, cl, f, icpt) if (f is not None and np.isfinite(sh)) else \
                        {"n_test": 0, "nse": np.nan, "rmse_m": np.nan, "bias_m": np.nan}
                    rows.append({"test": "split", "well": k, "site_no": np.nan, "headline": np.nan, "cluster": c,
                                 "form": form, "basis": basis, "direction": direction, "shift_m": sh,
                                 "n_test": res["n_test"], "nse": res["nse"], "bias_m": res["bias_m"],
                                 "rmse_m": res["rmse_m"]})
    tab = pd.DataFrame(rows)
    if placement is not None:
        if len(tab):
            tab["placement_months"] = p_len
            tab["true_cluster"] = tab["well"].map(lambda w: int(md.loc[w, "Cluster"]) if w in md.index else np.nan)
        return tab, chk
    # identity: the per-well arm reproduces what is published
    if len(tab) and OUT_48_MODEL_AB.exists():
        ab = pd.read_csv(OUT_48_MODEL_AB)
        ab["well"] = ab["well"].astype(str).apply(normalize_well_name)
        ab = ab.set_index("well")
        s = tab[(tab.test == "split") & (tab.basis == "well")]
        d = [abs(x.nse - ab.loc[x.well, f"nse_{x.direction}_{x.form}"]) for x in s.itertuples()
             if x.well in ab.index and np.isfinite(x.nse) and np.isfinite(ab.loc[x.well, f"nse_{x.direction}_{x.form}"])]
        chk["basis_vs48_max_abs_nse_diff"] = float(max(d)) if d else np.nan
    if len(tab) and OUT_44_METRICS.exists():
        p44 = pd.read_csv(OUT_44_METRICS)
        p44["k"] = p44["well"].astype(str).apply(normalize_well_name)
        p44 = p44.set_index(["site_no", "k"])["nse_after_offset"]
        s = tab[(tab.test == "ranwell") & (tab.basis == "well") & (tab.form == "A")]
        d = [abs(x.nse - p44.loc[(x.site_no, x.well)]) for x in s.itertuples() if (x.site_no, x.well) in p44.index and np.isfinite(x.nse)]
        chk["basis_vs44_max_abs_nse_diff"] = float(max(d)) if d else np.nan
    return tab, chk


def basis_verdict(tab: pd.DataFrame) -> dict:
    """The rule fixed before the run (D-268), per form: on each test the cluster basis holds if its median
    score is within BASIS_TOL_NSE of the per-well basis or better (CCW: and its median |bias| within
    BASIS_TOL_BIAS_M or smaller; split: in both directions; Ranwell: Script 44's headline pairings). Verdict 2
    'cluster better for transfer' (holds on all three and better by more than BASIS_TOL_NSE on CCW or Ranwell),
    1 'basis-robust' (holds on all three), 0 'basis matters'."""
    out = {}
    for form in ("A", "B"):
        t = tab[tab.form == form]
        med = {}
        for test in BASIS_TESTS:
            s = t[t.test == test]
            if test == "ranwell":
                s = s[s.headline.astype(bool)]
            for basis in ("well", "cluster"):
                b = s[s.basis == basis]
                if test == "split":
                    for d_ in ("fwd", "rev"):
                        med[(test, basis, d_)] = float(b[b.direction == d_]["nse"].median())
                else:
                    med[(test, basis, "")] = float(b["nse"].median())
                if test == "ccw":
                    med[(test, basis, "absbias")] = float(b["bias_m"].abs().median())
        hold, better = {}, {}
        for test in BASIS_TESTS:
            dirs = ("fwd", "rev") if test == "split" else ("",)
            gaps = [med[(test, "cluster", d_)] - med[(test, "well", d_)] for d_ in dirs]
            h = all(np.isfinite(g) and g >= -BASIS_TOL_NSE for g in gaps)
            if test == "ccw":
                h = h and med[("ccw", "cluster", "absbias")] <= med[("ccw", "well", "absbias")] + BASIS_TOL_BIAS_M
            hold[test] = bool(h)
            better[test] = bool(all(np.isfinite(g) and g > BASIS_TOL_NSE for g in gaps))
        code = (2 if all(hold.values()) and (better["ccw"] or better["ranwell"]) else
                1 if all(hold.values()) else 0)
        out[form] = {"med": med, "hold": hold, "better": better, "code": code}
    return out


BASIS_VERDICT = {2: "cluster better for transfer", 1: "basis-robust", 0: "basis matters"}


def place_wells(lev, lev_cols, master, length: int, side: str = "all") -> pd.DataFrame:
    """E12b (1.17.0, D-282): each reference well placed from its first `length` months of record alone, by its
    Pearson r with each cluster centroid built from that cluster's other members (Script 06's allocation, with
    the well itself left out so it cannot vote for its own cluster). `side` 'pre' or 'post' takes the first
    months on that side of MODEL_AB_SPLIT_DATE instead. Wells with a shorter record there are left out."""
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    md = master.set_index("_n")
    cols = {k: lev_cols[k] for k in md.index if k in lev_cols}
    # D-348: the centroids are built from each group's cluster-level members (boundary and set-aside wells out);
    # every well is still placed against them.
    from utils.cluster_series import in_cluster_level
    _lv = in_cluster_level(md)
    members = {int(c): [cols[k] for k in md.index[(md["Cluster"] == c) & _lv] if k in cols]
               for c in sorted(md["Cluster"].dropna().unique())}
    rows = []
    for k, col in cols.items():
        h = lev[col].dropna()
        if side == "pre":
            h = h[h.index < split]
        elif side == "post":
            h = h[h.index >= split]
        if len(h) < length:
            continue
        seg = h.iloc[:length]
        r = {}
        for c, mem in members.items():
            others = [m for m in mem if m != col]
            if not others:
                continue
            cent = lev[others].mean(axis=1).reindex(seg.index)
            ok = cent.notna()
            r[c] = float(seg[ok].corr(cent[ok])) if ok.sum() >= 3 else np.nan
        best = max((c for c in r if np.isfinite(r[c])), key=lambda c: r[c], default=None)
        rows.append({"well": k, "placement_months": length, "side": side, "true_cluster": int(md.loc[k, "Cluster"]),
                     "placed_cluster": best, "placed_r": r.get(best, np.nan),
                     "first_month": seg.index.min().strftime("%Y-%m"), "last_month": seg.index.max().strftime("%Y-%m"),
                     **{f"r_C{c}": v for c, v in r.items()}})
    return pd.DataFrame(rows)


def placement_experiment(lev, lev_cols, cl, master, bs_tab):
    """E12b: for each length, place every well, run E12's three tests on the placed cluster, and apply E12's
    rule against the per-well rows E12 already ran (bs_tab). Returns (placements, test rows, verdicts)."""
    plc, tabs, ver = [], [], {}
    well_rows = bs_tab[bs_tab["basis"] == "well"]
    for L in PLACEMENT_LENGTHS_MONTHS:
        pmap = {}
        for side in ("all", "pre", "post"):
            p = place_wells(lev, lev_cols, master, L, side)
            plc.append(p)
            pmap[side] = {r.well: int(r.placed_cluster) for r in p.itertuples() if pd.notna(r.placed_cluster)}
        t, _ = basis_experiment(lev, lev_cols, cl, master, placement=(L, pmap))
        tabs.append(t)
        # E12's rule on the same wells and directions the placed arm could run
        keys = set(zip(t["test"], t["well"], t["direction"].fillna("")))
        wr = well_rows[[k in keys for k in zip(well_rows["test"], well_rows["well"], well_rows["direction"].fillna(""))]]
        both = pd.concat([wr, t.assign(basis="cluster")], ignore_index=True)
        ver[L] = basis_verdict(both)
    return pd.concat(plc, ignore_index=True), pd.concat(tabs, ignore_index=True), ver


def placement_report(rr, plc: pd.DataFrame, ver: dict) -> None:
    for L, g in plc[plc["side"] == "all"].groupby("placement_months"):
        ok = g["placed_cluster"] == g["true_cluster"]
        rr.add(f"placement_L{L}_n_wells", int(len(g)), unit="wells",
               note=f"E12b: reference wells with at least {L} months of record, placed from their first {L} months (D-282)")
        rr.add(f"placement_L{L}_share_correct_pct", 100.0 * float(ok.mean()), unit="%",
               note=f"E12b: share of wells whose first {L} months place them in their own cluster (D-282)")
        for c, gc in g.groupby("true_cluster"):
            rr.add(f"placement_L{L}_share_correct_pct_C{int(c)}", 100.0 * float((gc["placed_cluster"] == c).mean()), unit="%",
                   note=f"E12b: share of C{int(c)} wells placed in C{int(c)} from their first {L} months (D-282)")
        for form, v in ver[L].items():
            rr.add(f"placement_L{L}_verdict_{form}", v["code"], unit="code",
                   note=f"E12b, Model {form}, placed from {L} months: {BASIS_VERDICT[v['code']]} against the per-well basis "
                        f"(E12's rule, D-282)")
            for test in BASIS_TESTS:
                rr.add(f"placement_L{L}_{test}_holds_{form}", float(v["hold"][test]), unit="flag",
                       note=f"E12b, Model {form}, {test}, placed from {L} months: holds (1) or not (0), D-282")
            for (test, basis, d_), val in v["med"].items():
                if basis != "cluster":
                    continue
                if d_ == "absbias":
                    rr.add(f"placement_L{L}_{test}_absbias_median_{form}", val, unit="m",
                           note=f"E12b, Model {form}, CCW 1989-96, placed from {L} months: median |bias| (D-282)")
                else:
                    sfx = f"_{d_}" if d_ else ""
                    rr.add(f"placement_L{L}_{test}_nse_median_{form}{sfx}", val,
                           note=f"E12b, Model {form}, {test}{' ' + d_ if d_ else ''}, placed from {L} months: median NSE (D-282)")


def basis_report(rr, tab: pd.DataFrame, ver: dict, chk: dict) -> None:
    for form, v in ver.items():
        rr.add(f"basis_verdict_{form}", v["code"], unit="code",
               note=f"Model {form}: {BASIS_VERDICT[v['code']]} (2 cluster better for transfer, 1 basis-robust, 0 basis matters; "
                    f"the rule fixed before the run, D-268)")
        for test in BASIS_TESTS:
            rr.add(f"basis_{test}_holds_{form}", float(v["hold"][test]), unit="flag",
                   note=f"Model {form}, {test}: the cluster basis holds (1) or not (0), E12, D-268")
        for (test, basis, d_), val in v["med"].items():
            if d_ == "absbias":
                rr.add(f"basis_{test}_absbias_median_{basis}_{form}", val, unit="m",
                       note=f"Model {form}, CCW 1989-96: median |bias| on the {basis} basis, E12, D-268")
            else:
                sfx = f"_{d_}" if d_ else ""
                what = {"ccw": "CCW 1989-96 hindcast", "ranwell": "Ranwell 1951-53 hindcast, headline pairings, NSE after the offset",
                        "split": f"split-sample test ({d_})"}[test]
                rr.add(f"basis_{test}_nse_median_{basis}_{form}{sfx}", val,
                       note=f"Model {form}, {what}: median NSE on the {basis} basis, E12, D-268")
    rw = tab[(tab.test == "ranwell")]
    for form in ("A", "B"):
        for basis in ("well", "cluster"):
            s = rw[(rw.form == form) & (rw.basis == basis)]
            rr.add(f"basis_ranwell_nse_median_all_{basis}_{form}", float(s["nse"].median()),
                   note=f"Model {form}, Ranwell 1951-53, all {len(s)} pairings: median NSE after the offset on the {basis} basis, E12, D-268")
            rr.add(f"basis_ranwell_range_ratio_median_{basis}_{form}", float(s["range_ratio"].median()),
                   note=f"Model {form}, Ranwell 1951-53, all pairings: median model/observed seasonal range on the {basis} basis, E12, D-268")
    for k, v in chk.items():
        rr.add(k, v, note="E12 identity: the per-well arm against the published script (D-268)")


def plot_decision_tree() -> None:
    """Paper M Section 4.6 as a tree (J-25, Martin 2026-11-20: "for 4.6 a decision tree showing the NSE would be nice").

    Every value is read back from the report-number CSVs this run has just written (Script 50's, and Script 48's for
    the full-record forward NSE), never passed in or typed, so the figure and the prose's fields share one source.
    A tested leaf is marked by Script 50's own verdict flag (basis_*_holds_B, placement_L*_*_holds_B: the rule fixed
    before the run). The own-coefficient leaves are the reference those rules compare against, so their skill rows
    carry no mark; their drier-shift rows are marked against BASIS_TOL_BIAS_M, the same level tolerance.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    def table(path):
        t = pd.read_csv(path)
        return dict(zip(t["Parameter"].astype(str), pd.to_numeric(t["Value"], errors="coerce")))
    # J-15: the tree's values now come from three suite steps (50a record length, 50b Ranwell by datum,
    # 50c transfer), read after this step has saved its own
    r50 = {**table(paths.OUT_50A_REPORT_NUMBERS), **table(paths.OUT_50B_REPORT_NUMBERS),
           **table(OUT_50C_REPORT_NUMBERS)}
    r48 = table(paths.OUT_48_REPORT_NUMBERS)
    L = f"L{RECLEN_MIN_FIT_MONTHS}"
    def v(key, src=r50):
        x = src.get(key, np.nan)
        return float(x) if np.isfinite(x) else np.nan
    def flag(key):
        x = v(key)
        return None if not np.isfinite(x) else bool(x >= 0.5)
    def nse(x):
        return "—" if not np.isfinite(x) else f"NSE {x:.2f}"
    def high(x, basis):
        return "—" if not np.isfinite(x) else f"{abs(x):.2f} m too high\n{basis}"
    def lvl(x):
        return None if not np.isfinite(x) else bool(abs(x) <= BASIS_TOL_BIAS_M)
    ROWS = ("the coming years", "another climate's seasons", "a lasting drier shift")
    leaves = [
        ("Own coefficients,\nfull record",
         [(nse(v("modelab_nse_fwd_B_median_all", r48)), None),
          (nse(v("ranwell_nse_median_model_b")), None),
          (high(v("reclen_ccw_bias_m_B_median_L100_start"), "(100-month fits)"), lvl(v("reclen_ccw_bias_m_B_median_L100_start")))]),
        (f"Own coefficients,\n{RECLEN_MIN_FIT_MONTHS} months",
         [(nse(v(f"reclen_nse_fwd_B_median_{L}_all")), None),
          ("not tested", None),
          (high(v("reclen_ccw_bias_m_B_median_L36_start"), "(36-month fits)"), lvl(v("reclen_ccw_bias_m_B_median_L36_start")))]),
        ("Cluster coefficients",
         [(nse(v("basis_split_nse_median_cluster_B_fwd")), flag("basis_split_holds_B")),
          (nse(v("basis_ranwell_nse_median_cluster_B")), flag("basis_ranwell_holds_B")),
          (f"median |bias|\n{v('basis_ccw_absbias_median_cluster_B'):.2f} m", flag("basis_ccw_holds_B"))]),
        (f"New well, placed in its\ncluster from {RECLEN_MIN_FIT_MONTHS} months",
         [(nse(v(f"placement_{L}_split_nse_median_B_fwd")), flag(f"placement_{L}_split_holds_B")),
          (nse(v(f"placement_{L}_ranwell_nse_median_B")), flag(f"placement_{L}_ranwell_holds_B")),
          (f"median |bias|\n{v(f'placement_{L}_ccw_absbias_median_B'):.2f} m", flag(f"placement_{L}_ccw_holds_B"))]),
    ]
    INK, OK, NO, MUTED = "#1b1b1b", "#1a7f37", "#b42318", "#6b7280"
    fig, ax = plt.subplots(figsize=(7.5, 6.0), dpi=160)
    ax.set_xlim(0, 100); ax.set_ylim(2, 98); ax.axis("off")
    def box(x, y, w, h, text, fc="#f4f6f8", ec="#9aa4ae", fs=8, weight="normal", color=INK):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                    fc=fc, ec=ec, lw=0.8))
        ax.text(x, y, text, ha="center", va="center", fontsize=fs, weight=weight, color=color)
    def arrow(x0, y0, x1, y1, color=MUTED):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=0.8, shrinkA=0, shrinkB=0))
    box(50, 93, 30, 6, "A well's record\n(groups C1, C2, C3o and C3f)", weight="bold")
    box(87, 93, 18, 6, "C4 Main Forest:\nstop", fc="#fdecea", ec=NO, color=NO, weight="bold")
    ax.text(87, 87.5, "drainage not identified;\nforecast fails (Section 5.2)", ha="center", va="top", fontsize=6.5, color=NO)
    arrow(66, 93, 76.5, 93, NO)
    box(26, 78, 30, 5.5, "Use the well's own coefficients")
    box(74, 78, 30, 5.5, "Use its cluster's coefficients")
    arrow(42, 89.8, 28, 81); arrow(58, 89.8, 72, 81)
    xs = [12.5, 37.5, 62.5, 87.5]
    for x, (head, rows) in zip(xs, leaves):
        arrow(26 if x < 50 else 74, 75.2, x, 66.5)
        box(x, 63, 21, 6.5, head, fc="#ffffff", weight="bold", fs=7.2)
        for k, (txt, ok) in enumerate(rows):
            y = 52 - 15 * k
            fc, ec, col = ("#f4f6f8", "#c4cbd2", INK) if ok is None else (("#e7f5ec", OK, INK) if ok else ("#fdecea", NO, INK))
            box(x, y, 21, 8.5, txt, fc=fc, ec=ec, color=col, fs=7.2)
            if ok is not None:
                ax.text(x + 9.6, y + 3.0, "✓" if ok else "✗", ha="right", va="center", fontsize=9,
                        color=OK if ok else NO, weight="bold")
    for k, name in enumerate(ROWS):
        ax.text(0.5, 52 - 15 * k + 6.4, name, ha="left", va="center", fontsize=7, color=MUTED, style="italic")
    ax.text(50, 9, f"✓ / ✗: the cluster and placement tests against each well's own coefficients, on a rule fixed\n"
                   f"before the run (NSE within {BASIS_TOL_NSE:g}; median absolute bias within {BASIS_TOL_BIAS_M:g} m). Own-coefficient "
                   f"drier-shift rows\nare marked against the same {BASIS_TOL_BIAS_M:g} m; unmarked rows are the reference the tests "
                   "compare against.\nModel B throughout; medians over the reference wells.",
            ha="center", va="center", fontsize=6.3, color=MUTED)
    fig.suptitle("What the model lets you predict", fontsize=10, weight="bold", y=0.985)
    render_figure(fig, OUT_50_DECISION_FIG)
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# E18: does a calibration fitted on the modern record transfer? (1.21.0, T-130, D-290)
# ──────────────────────────────────────────────────────────────────────────────
def e18_tests(lev, lev_cols, cl, master) -> pd.DataFrame:
    """Per admitted CCW well x basis: Model A at the project datum fitted on the full modern record (basis 'well',
    Script 39's protocol) or the well's cluster centroid fitted on the same span and shifted to the well (basis
    'cluster', E12's arm); one continuous run from the start of the climate record at the equilibrium seed; the
    quantile map fitted on that run against the well's modern readings, applied unchanged to the run over 1989-96.
    Scored raw and mapped on the uncensored CCW months."""
    if not (paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()):
        warn("CCW historic inputs not present — E18 is skipped")
        return pd.DataFrame()
    obs, cmap = load_ccw()
    mdk = _model_a_store(pd.read_csv(INT_MASTER_DATA))
    mdk["k"] = mdk["Name_Original"].astype(str).str.lower().str.strip()
    adm = usable_codes(cmap, mdk.set_index("k"), obs)
    adm = adm[adm["admitted"]]
    md = master.set_index("_n")
    ra = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    clh = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    p_mean, pet_mean = float(clh["P_m"].mean()), float(clh["PET"].mean())
    first_month, last_month = obs["month"].min(), obs["month"].max()
    cache, rows = {}, []
    for r in adm.itertuples():
        k = normalize_well_name(r.well)
        col = lev_cols.get(k)
        if col is None or k not in md.index:
            continue
        o, n_cens = observed_series(obs, r.code, r.datum_offset_m)
        if o.empty:
            continue
        c = int(md.loc[k, "Cluster"])
        hw = lev[col].dropna()
        for basis in E18_BASES:
            row = {"well": k, "code": r.code, "cluster": c, "basis": basis, "n_censored_ccw": int(n_cens)}
            if basis == "well":
                f = _censored_well_fit(hw, cl, dry_bounds(col), None, False, start=RECORD_FIT_START)   # 1.24.0 (D-322)
                f = f if f is not None and f["beta_3_drainage"] > 0 else None
                sh = 0.0
            else:
                if c not in cache:
                    cache[c] = _centroid_fit(ra, c, cl, False, "full")
                f, hc = cache[c]
                common = hw.index.intersection(hc.index)
                sh = float(hw.loc[common].mean() - hc.loc[common].mean()) if len(common) else np.nan
            row["shift_m"] = sh
            if f is None or not np.isfinite(sh):
                rows.append(row)
                continue
            betas = (f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"])
            h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=DRAINAGE_DATUM)
            run, _s = hindcast_well(clh, betas, h0, clh.index.min(), max(hw.index.max(), last_month), 1.0,
                                    drainage_datum=DRAINAGE_DATUM)
            run = run + sh
            cm = hw.index.intersection(run.index)
            cc = o.index.intersection(run.index)
            row.update(beta_1=betas[0], beta_2=betas[1], beta_3=betas[2],
                       n_modern=int(len(cm)), n_test=int(len(cc)))
            nse0, rmse0, bias0 = get_metrics(o.loc[cc], run.loc[cc])
            row.update(nse_raw=float(nse0), rmse_raw_m=float(rmse0), bias_raw_m=float(bias0))
            if len(cm) < QMAP_MIN_MONTHS or len(cc) < MODEL_AB_MIN_TEST_MONTHS:
                rows.append(row)
                continue
            qm, _m, _o = quantile_map(run.loc[cm].to_numpy(float), hw.loc[cm].to_numpy(float))
            mapped = pd.Series(qm(run.loc[cc].to_numpy(float)), index=cc)
            nse1, rmse1, bias1 = get_metrics(o.loc[cc], mapped)
            row.update(nse_mapped=float(nse1), rmse_mapped_m=float(rmse1), bias_mapped_m=float(bias1),
                       rmse_cut_m=float(rmse0 - rmse1), improved=bool(rmse1 < rmse0))
            rows.append(row)
    return pd.DataFrame(rows)


def e18_verdict(t: pd.DataFrame) -> dict:
    """The rule fixed before the run (D-290), per basis: 'transfers' if the median RMSE falls by at least
    E18_RMSE_CUT_M, the map lowers RMSE at a majority of wells, and the median |bias| is no larger than raw;
    otherwise 'does not transfer'. The primary basis is the verdict."""
    per = {}
    for basis in E18_BASES:
        g = t[(t["basis"] == basis)].dropna(subset=["rmse_mapped_m"]) if len(t) else pd.DataFrame()
        if g.empty:
            per[basis] = {"verdict": "not run", "n": 0}
            continue
        d = {"n": int(len(g)),
             "rmse_raw": float(g["rmse_raw_m"].median()), "rmse_mapped": float(g["rmse_mapped_m"].median()),
             "abs_bias_raw": float(g["bias_raw_m"].abs().median()),
             "abs_bias_mapped": float(g["bias_mapped_m"].abs().median()),
             "nse_raw": float(g["nse_raw"].median()), "nse_mapped": float(g["nse_mapped"].median()),
             "n_improved": int(g["improved"].astype(bool).sum())}
        d["rmse_cut"] = d["rmse_raw"] - d["rmse_mapped"]
        d["tests"] = {"rmse_cut": d["rmse_cut"] >= E18_RMSE_CUT_M,
                      "majority": d["n_improved"] > d["n"] / 2,
                      "bias": d["abs_bias_mapped"] <= d["abs_bias_raw"]}
        d["verdict"] = "transfers" if all(d["tests"].values()) else "does not transfer"
        per[basis] = d
    return {"per": per, "verdict": per.get(E18_PRIMARY_BASIS, {}).get("verdict", "not run")}


def e18_report(rr, t: pd.DataFrame, v: dict) -> None:
    rr.add("e_qm_rmse_cut_threshold_m", E18_RMSE_CUT_M, unit="m",
           note="E18 rule: the median RMSE must fall by at least this (config.E18_RMSE_CUT_M, D-290)")
    rr.add("e_qm_transfers", int(v["verdict"] == "transfers"), unit="",
           note=f"E18 verdict on the {E18_PRIMARY_BASIS} basis: a modern-record quantile map transfers to CCW 1989-96 (1) or not (0), D-290")
    for basis, d in v["per"].items():
        if d.get("verdict") == "not run":
            continue
        _n = f"CCW 1989-96, Model A at the project datum, {basis} basis, {d['n']} wells (E18, D-290)"
        rr.add(f"e_qm_n_wells_{basis}", d["n"], unit="wells", note=f"wells scored, {_n}")
        rr.add(f"e_qm_n_improved_{basis}", d["n_improved"], unit="wells", note=f"wells where the map lowers RMSE, {_n}")
        for key, lab, unit in (("rmse_raw", "median RMSE, raw run", "m"), ("rmse_mapped", "median RMSE, mapped", "m"),
                               ("rmse_cut", "median raw RMSE less median mapped RMSE", "m"),
                               ("abs_bias_raw", "median |bias|, raw run", "m"),
                               ("abs_bias_mapped", "median |bias|, mapped", "m"),
                               ("nse_raw", "median NSE, raw run", ""), ("nse_mapped", "median NSE, mapped", "")):
            rr.add(f"e_qm_{key}_{basis}" + ("_m" if unit == "m" else ""), d[key], unit=unit, note=f"{lab}, {_n}")
        rr.add(f"e_qm_transfers_{basis}", int(d["verdict"] == "transfers"), unit="",
               note=f"E18 rule on the {basis} basis: transfers (1) or not (0), D-290")
    if len(t):
        n_cens = t[t["basis"] == E18_PRIMARY_BASIS]["n_censored_ccw"]
        rr.add("e_qm_n_censored_months", int(n_cens.sum()), unit="months",
               note="CCW months censored at the pipe base and dropped, summed over the E18 wells (as Script 39)")


def run_e18(lev, lev_cols, cl, master):
    t = e18_tests(lev, lev_cols, cl, master)
    v = e18_verdict(t)
    for basis, d in v["per"].items():
        if d.get("verdict") == "not run":
            step(f"{basis} basis: not run")
            continue
        step(f"{basis} basis, {d['n']} wells: median RMSE {d['rmse_raw']:.3f} -> {d['rmse_mapped']:.3f} m "
             f"(cut {d['rmse_cut']:.3f}), improved at {d['n_improved']}, median |bias| {d['abs_bias_raw']:.3f} -> "
             f"{d['abs_bias_mapped']:.3f} m, NSE {d['nse_raw']:.2f} -> {d['nse_mapped']:.2f}: {d['verdict']} "
             f"{ {k: bool(x) for k, x in d['tests'].items()} }")
    step(f"E18 verdict ({E18_PRIMARY_BASIS} basis): {v['verdict']}")
    if len(t):
        t.to_csv(OUT_50_CCW_QMAP, index=False); saved(f"{OUT_50_CCW_QMAP.name} ({len(t)} rows)")
    return t, v


# ──────────────────────────────────────────────────────────────────────────────
def main(no_fig: bool = False) -> int:
    banner("50c", "Transfer between wells: neighbour, cluster and placement (T-173, D-268, D-282, D-290)", version=__version__)
    DIR_50C.mkdir(parents=True, exist_ok=True)

    phase(1, "Inputs")
    lev, lev_cols, cl, master = load_inputs()
    info(f"{len(master)} reference wells; lengths {', '.join(LENGTHS)} (fitted monthly changes); "
         f"split {MODEL_AB_SPLIT_DATE}; stability tolerance {RECLEN_STABLE_TOL:g}")

    mhw = mhw_depths()          # the MHW form's per-well datum (T-173 at mean high water)
    phase(2, "A neighbour's coefficients at this well (T-173), and the transfer rule (T-173b)")
    # T-173: fit on a neighbour, run here (Laurence Jones's test)
    nbt = neighbour_transfer(lev, lev_cols, cl, master)
    # 1.25.0 (D-332): the same test with Model A at each well's depth to mean high water; 50_50 gains a form
    # column (A rows first, unchanged). The transfer rule and the figure stay on Model A at 3.7 m.
    nbt_m = neighbour_transfer(lev, lev_cols, cl, master, datum_of=mhw) if mhw else pd.DataFrame()
    # 1.29.0 (J-23): the same test under Model B, the borrowed intercept travelling with the betas
    nbt_b = neighbour_transfer(lev, lev_cols, cl, master, intercept=True)
    pd.concat([nbt.assign(form="A"), nbt_m.assign(form=FORM_MHW), nbt_b.assign(form="B")],
              ignore_index=True).to_csv(OUT_50_NEIGHBOUR, index=False)
    saved(f"{OUT_50_NEIGHBOUR.name} ({len(nbt)} rows at 3.7 m, {len(nbt_m)} at mean high water, "
          f"{len(nbt_b)} Model B)")
    if len(nbt_m):
        _pm = nbt_m.pivot_table(index="well", columns="source", values="nse").median()
        step("T-173 at mean high water: median own " + ", ".join(f"{k} {_pm.get(k, np.nan):.2f}"
                                                                  for k in ("own", "neighbour", "centroid")))
    plot_neighbour_transfer(nbt); saved(OUT_50_NEIGHBOUR_FIG.name)
    # T-173b: why transfer works where it does, and the rule that follows
    trule = transfer_rule(nbt, lev, lev_cols, master)
    if not trule.empty:
        trule.to_csv(OUT_50_TRANSFER_RULE, index=False)
        saved(f"{OUT_50_TRANSFER_RULE.name} ({int((trule['scope'] == 'pair').sum())} pairs)")
        plot_transfer_rule(trule); saved(OUT_50_TRANSFER_FIG.name)
        _p = trule[trule["scope"] == "predictor"].sort_values("gain_nse", key=abs, ascending=False)
        for _, r in _p.iterrows():
            step(f"  predictor {r['well']:16s} Spearman {r['gain_nse']:+.3f}  (n={int(r['n_shared_months'])})")

    phase(3, "Per well or per cluster? Hindcast and forecast skill on both bases (E12, 1.12.0, D-268)")
    bs_tab, bs_chk = basis_experiment(lev, lev_cols, cl, master)
    bs_ver = basis_verdict(bs_tab)
    for k, v in bs_chk.items():   # Script 44 runs its own hindcast loop, matched to 1e-6 as E9's check is
        (step if (np.isfinite(v) and v < (1e-6 if "vs44" in k else 1e-9)) else warn)(f"{k}: {v:.3g}")
    for form, v in bs_ver.items():
        m = v["med"]
        step(f"Model {form}: CCW NSE {m[('ccw', 'well', '')]:.3f} well / {m[('ccw', 'cluster', '')]:.3f} cluster, "
             f"|bias| {m[('ccw', 'well', 'absbias')]:.3f} / {m[('ccw', 'cluster', 'absbias')]:.3f} m; Ranwell {m[('ranwell', 'well', '')]:.3f} / "
             f"{m[('ranwell', 'cluster', '')]:.3f}; split fwd {m[('split', 'well', 'fwd')]:.3f} / {m[('split', 'cluster', 'fwd')]:.3f}, "
             f"rev {m[('split', 'well', 'rev')]:.3f} / {m[('split', 'cluster', 'rev')]:.3f}")
        result(f"E12 Model {form}", f"{BASIS_VERDICT[v['code']]}; holds: " + ", ".join(f"{t} {'yes' if h else 'no'}" for t, h in v["hold"].items()))
    bs_tab.to_csv(OUT_50_BASIS, index=False); saved(f"{OUT_50_BASIS.name} ({len(bs_tab)} rows)")

    phase(4, "Can a short record place a new well? Placement from the first months, then E12's tests (E12b, 1.17.0, D-282)")
    pl_plc, pl_tab, pl_ver = placement_experiment(lev, lev_cols, cl, master, bs_tab)
    for L, g in pl_plc[pl_plc["side"] == "all"].groupby("placement_months"):
        step(f"{L} months: {len(g)} wells, {100.0 * (g.placed_cluster == g.true_cluster).mean():.1f} % placed in their own cluster")
        for form, v in pl_ver[L].items():
            m = v["med"]
            result(f"E12b {L} months, Model {form}",
                   f"{BASIS_VERDICT[v['code']]}; CCW NSE {m[('ccw', 'cluster', '')]:.3f} (well {m[('ccw', 'well', '')]:.3f}), "
                   f"|bias| {m[('ccw', 'cluster', 'absbias')]:.3f} (well {m[('ccw', 'well', 'absbias')]:.3f}) m; split fwd "
                   f"{m[('split', 'cluster', 'fwd')]:.3f} (well {m[('split', 'well', 'fwd')]:.3f}); holds: "
                   + ", ".join(f"{t} {'yes' if h else 'no'}" for t, h in v["hold"].items()))
    pl_tab["side"] = np.where(pl_tab["test"] == "split", np.where(pl_tab["direction"] == "fwd", "pre", "post"), "all")
    pl_out = pl_tab.merge(pl_plc[["well", "placement_months", "side", "placed_cluster", "placed_r", "first_month", "last_month"]],
                          on=["well", "placement_months", "side"], how="left")
    pl_out.to_csv(OUT_50_PLACEMENT, index=False); saved(f"{OUT_50_PLACEMENT.name} ({len(pl_out)} rows)")

    phase(5, "Does a modern-record calibration transfer to CCW 1989-96? (E18, 1.21.0, D-290)")
    e18 = run_e18(lev, lev_cols, cl, master)

    phase(6, "Outputs")
    rr = ReportNumbers()
    transfer_report(rr, trule=trule, nbt_mhw=nbt_m, nbt_b=nbt_b)
    beta3_bound_report(rr, {"basis": (bs_tab, "beta_3",
                                      "E12's CCW and Ranwell fits, well and cluster basis (50_30)")})   # 1.25.0 (D-332)
    basis_report(rr, bs_tab, bs_ver, bs_chk)
    placement_report(rr, pl_plc, pl_ver)
    e18_report(rr, *e18)
    rr.save(OUT_50C_REPORT_NUMBERS); saved(f"{OUT_50C_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    if not no_fig:
        plot_decision_tree()                   # J-25: reads the report numbers saved by 50a, 50b and this step
    done("50c")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Transfer between wells: neighbour, cluster and placement (T-173, D-268, D-282, D-290)")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figure")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
