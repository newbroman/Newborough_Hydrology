#!/usr/bin/env python3
"""
50_record_length.py — what the record length decides: the coefficients, forecasting and hindcasting
=====================================================================================================
WHAT THIS IS
  The monthly state-space model (Script 03) is fitted on two records: the cluster centroids on the
  full record, and each reference well on a common comparison window of LCSC_DATA_LIMIT months. Its
  coefficients belong to the record they were fitted on, and the network was installed
  progressively, so "the record" is not one thing. This step measures how much that matters (D-222;
  spec working/updates/NRG_spec_record_length_2026-10-01.md, approved by Martin 2026-10-01).

  At every reference well, Model A (no intercept, datum DRAINAGE_DATUM) and Model B (free
  intercept, which is Model A at the fitted datum DRAINAGE_DATUM - alpha/beta_3) are fitted on
  records of each length L in RECLEN_LENGTHS_MONTHS and on the full record. L counts fitted
  monthly changes (rows of the SSM frame), so a gap in a record lengthens its calendar span but
  not L. Four experiments:

    forecast         fitted on the L months before MODEL_AB_SPLIT_DATE; free-run over every
                     month after it from the first reading there (Script 48's split-sample
                     forward test, which the full-length row reproduces exactly).
    hindcast_within  fitted on the L months from MODEL_AB_SPLIT_DATE; free-run over the months
                     before it from their first reading (Script 48's reverse test).
    ccw_hindcast     at the wells Script 39 admits: fitted on the first L months of the modern
                     record ("start") or the last L ("end"), then run through Script 39's hindcast
                     unchanged (utils/hindcast_utils.py) over the CCW 1989-96 readings, which no
                     fit ever sees. L = LCSC_DATA_LIMIT at the end is exactly the published
                     coefficients, and reproduces Script 39.
    stability        every non-overlapping placement of L months within the record, from its
                     start; beta_3 against the full-record beta_3 of the same form.

  A well's STABLE LENGTH (per form) is the shortest L from which the median over placements of
  |beta_3(L)/beta_3(full) - 1| stays below RECLEN_STABLE_TOL at every longer L. Divided by the
  well's full-record Model B mean-reversion time, it answers whether the record a drainage
  coefficient needs is a fixed number of months or a multiple of the response.

  The same run emits, on the full record, the expected spring persistence (1 - beta_3)^12 of both
  forms (D-221), so the methods paper can quote persistence and mean-reversion time on one record,
  and (T-103) the per-well ratio of the comparison-window beta_3 to the full-record beta_3 from
  Script 03's 03_15.

WHAT IT DOES NOT DO
  It fits nothing Script 03 publishes and changes no other output. Fits shorter than SSM_MIN_OBS
  are deliberate here (RECLEN_MIN_FIT_MONTHS) and are confined to this step.

INPUTS — all committed
  01_wells_clean.csv, 01_climate.csv, 03_master_data.csv (reference membership and clusters),
  03_15_per_well_window_sensitivity.csv (T-103), data/ccw_1989_1996_depths.csv and
  data/ccw_1989_1996_code_map.csv (the CCW hindcast; skipped cleanly when absent, as Script 39).
  For the identity checks only, when present: 48_04_model_a_b_diagnostics.csv, 39_01_hindcast_per_well.csv.

OUTPUTS (outputs/50_record_length/)
  50_01_record_length_per_well.csv   one row per well x form x experiment x length x placement
  50_02_record_length_by_cluster.csv medians and 10th/90th percentiles by cluster (and all)
  50_03_ccw_hindcast_by_length.csv   the CCW hindcast per well x form x length x end
  50_05_stable_length_per_well.csv   each well's stable length, in months and in mean-reversion times
  50_04_record_length.png            stability, forecast, within-record and CCW hindcast against L
  50_18 .. 50_20                     E8d, rain event structure (D-234)
  50_21 .. 50_23                     E8e, the 1998 felling north of NW9 and its regrowth (D-235)
  50_24 .. 50_25                     E8f, the 2014/15 shore clearance step (D-236)
  50_report_numbers.csv

Registered in run_analysis.py, Phase 19, tier X, opt-in (--with-supplementary).
Run directly:  python3 src/50_record_length.py [--no-fig]
"""
from __future__ import annotations

__version__ = "1.7.0"  # Hollingham (2026) - 2026-10-03 (D-236; Martin: "Otherwise I approve", 07:49, spec
#   NRG_spec_E8f_shore_clearance_step_2026-10-03). E8f: did the 2014/15 shore clearance put a step into the wells
#   around it? Per well within E8F_NEAR_M of the strip, and placebo wells beyond E8F_FAR_M, the E8 single store against
#   the same with one step whose date is profiled monthly over E8F_STEP_WINDOW; test 1, a step at the BACI coastal
#   controls or the scrape control (E8F_CONTROL_WELLS); test 2, at most E8F_PLACEBO_MAX_FRAC of the placebo wells
#   step. 50_24_clearance_step_by_well.csv, 50_25_clearance_step.png; e8f_* report numbers. Phase 11 E8f, outputs 12.
# 1.6.0  # Hollingham (2026) - 2026-10-02 (D-235; Martin: "e8e spec approve", 23:33, spec
#   NRG_spec_E8e_felling_regrowth_2026-10-02). E8e: was the 2006-08 high water at NW9 the 1998 felling north of
#   it and the pine's return? Per well, the E8 single store on the full record (wells with E8E_MIN_EARLY_MONTHS
#   readings in 2006-08): test 1, the excess falls with 01_locations dist_1998_replant_m (Spearman, p < E8E_P)
#   more strongly than with dist_coast_m; test 2, NW9's half-decline year against the year Script 41's canopy
#   ratio over felling_1998_1 (vp1) is halfway to its highest; test 3 (reported), open-dune wells beyond
#   E8E_FAR_M. 50_21_felling_distance_by_well.csv, 50_22_nw9_regrowth_timing.csv, 50_23_felling_regrowth.png;
#   e8e_* report numbers. Phase 10 E8e, outputs become phase 11.
# 1.5.0  # Hollingham (2026) - 2026-10-02 (D-234; Martin: "approve", spec
#   NRG_spec_E8d_rain_event_structure_2026-10-02). E8d: did long rain events, which a monthly total hides, drive
#   the 2006-08 excess? Daily MIDAS gauges (Llyn Alaw primary, RAF Valley check; utils/midas_rain.py, a
#   documented raw-input exception): per winter the share of rain in long events against the gauge's own
#   1974-2005 baseline (tests 1-2), and per cluster centroid a long-event stress on the single store
#   (test 3). 50_18_rain_events_by_winter.csv, 50_19_event_stress_by_cluster.csv, 50_20_rain_events.png;
#   e8d_* report numbers. Phase 9 E8d, outputs become phase 10.
# 1.4.0  # Hollingham (2026) - 2026-10-02 (D-232; Martin: "go ahead with e8b and e8c" / "approve").
#   E8b: one non-climatic term on E8's single store per cluster centroid - a step (ps.StepModel, One), a
#   relaxing step (StepModel, Exponential), a linear trend (ps.LinearTrend) - its date fitted inside
#   CHANGE_TSTART_BOUNDS; the best by BIC is kept if it beats the single store by TWO_STORE_BIC_STRONG and
#   holds the split test (CHANGE_SPLIT_DIRECTIONS); direction, a common date across clusters, the NW9 winters,
#   and the CCW check. E8c: surface flow - ps.TarsoModel (a second drainage above a fitted level) and the
#   single store with ps.ThresholdTransform - judged by BIC, the split test, the bias of months starting within
#   SURFACE_BAND_M of the ground, a threshold within SURFACE_THRESHOLD_MAX_DEPTH_M of it; CCW and Ranwell's C1
#   sites as checks. 50_15_two_store_change.csv, 50_16_surface_flow.csv, 50_17_change_and_surface.png.
#   Spec NRG_spec_E8b_E8c_2026-10-02, with its two amendments made before any real fit was read: E8b's split
#   test is forward only (Martin, 13:20, "yes"; the reverse half trains after every admissible change date),
#   and change dates and the threshold transform's level are PROFILED (_profile), because Pastas returns
#   them at their initial value with a standard error of 0; the 95% intervals are profile intervals.
# 1.3.0  # Hollingham (2026) - 2026-10-02 (D-231; Martin: "I approve the spec of the E8 model").
#   E8: two drainage time scales per cluster. Pastas Exponential (term for term Model B) against
#   DoubleExponential (two parallel linear stores sharing the recharge), fitted to each cluster centroid,
#   warmed up over the climate record from its last gap (utils/pastas_utils), so no starting level is
#   fitted; with and without the AR(1) noise model. The four tests and the verdict are the rule fixed
#   before the run (config TWO_STORE_*; spec NRG_spec_E8_two_store_2026-10-02): BIC and the split test;
#   the CCW drier-decade bias at the cluster's CCW wells; agreement of the slow time scales; the 2006-08
#   residual and the NW9 winters. C4 and C5 fitted whole (felling years in) and reported separately.
#   50_12_two_store_by_cluster.csv, 50_13_two_store_check_well.csv, 50_14_two_store.png.
# 1.2.0  # Hollingham (2026) - 2026-10-02 (D-229; Martin: "Spec adding Ranwell" / "Approve").
#   E9: Ranwell's 1951-53 readings as the second drier epoch. Model A refitted at every datum and Model B,
#   comparison window and full record, hindcast from the 1930 spin-up at Script 44's pairings and scored as
#   Script 44 scores them (utils/hindcast_utils.compare_offset_censored: offset removed, censored at the
#   ground). The rule fixed before the run: the datum maximizing the median NSE over the headline pairings
#   (Model A, comparison window), the band within RECLEN_DATUM_NSE_TOL; "does not discriminate" when the
#   median moves by less than that tolerance over the whole grid; otherwise "consistent" with CCW when the
#   bands overlap, "disagrees" when they do not. Checks, never the rule: all pairings, the dry year 1953
#   alone, the amplitude ratio, the full record. Identity check against Script 44 at the project datum.
#   50_10_ranwell_hindcast_by_datum.csv; 50_09 gains the Ranwell panel. Spec
#   NRG_spec_ranwell_by_datum_2026-10-02.
# 1.1.0  # Hollingham (2026) - 2026-10-01 (D-225; Martin: "please spec it" / "I approve your
#   choices"). Which datum does the drier past support? Model A refitted at every datum of Script 03's
#   sweep: the CCW 1989-96 hindcast (comparison window and full record), the within-record split test,
#   and the UKCP18 sustained projection with each well's room left above the datum (forest withheld by
#   the D-224 pairing). The supported datum is fixed by a rule stated before the run: the datum
#   maximizing the median CCW NSE on the comparison window, and the band within RECLEN_DATUM_NSE_TOL of
#   it. Three identity checks at DRAINAGE_DATUM (Scripts 39, 48 and 19). Spec
#   NRG_spec_datum_against_the_drier_past_2026-10-01.
# 1.0.0  # Hollingham (2026) - 2026-10-01 (D-222). First issue, to the approved spec
#   NRG_spec_record_length_2026-10-01 (Martin: "approved"). Numbered 50 because 49 is the former name
#   of 01b_water_table.py and is still cited by that name in the records.

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils import paths                                       # noqa: E402
from utils.paths import (                                     # noqa: E402
    DIR_50, OUT_50_PER_WELL, OUT_50_BY_CLUSTER, OUT_50_CCW, OUT_50_STABLE, OUT_50_FIG,
    OUT_50_REPORT_NUMBERS, INT_WELLS_CLEAN, INT_CLIMATE, INT_MASTER_DATA,
    OUT_03_PER_WELL_WINDOW_SENS, OUT_48_MODEL_AB, OUT_39_PER_WELL,
    OUT_03_MODEL_B_PERSISTENCE, OUT_19_SCENARIO_PERWELL_MODEL_A, INT_LOCATIONS,
    OUT_50_CCW_DATUM, OUT_50_SPLIT_DATUM, OUT_50_PROJ_DATUM, OUT_50_DATUM_FIG,
    OUT_50_RANWELL_DATUM, OUT_44_METRICS, RANWELL_LEVELS,
    OUT_50_TWO_STORE, OUT_50_TWO_STORE_WELL, OUT_50_TWO_STORE_FIG, INT_REGIONAL_AVG,
    OUT_50_CHANGE, OUT_50_SURFACE, OUT_50_CHANGE_SURFACE_FIG,
    MIDAS_RAIN_DIR, OUT_50_RAIN_EVENTS, OUT_50_EVENT_STRESS, OUT_50_RAIN_EVENTS_FIG,
    OUT_50_FELLING_DIST, OUT_50_NW9_TIMING, OUT_50_FELLING_FIG,
    OUT_50_CLEARANCE_STEP, OUT_50_CLEARANCE_FIG, DATA_SHORE_CLEARANCE_2015,
)
from utils.config import (                                    # noqa: E402
    DRAINAGE_DATUM, HEADLINE_LAG, CLUSTER_LABELS, CLUSTER_COLOURS, LCSC_DATA_LIMIT,
    MODEL_AB_SPLIT_DATE, MODEL_AB_MIN_TEST_MONTHS, PASTAS_IDENT_EFOLD_WINDOW_FRAC,
    RECLEN_LENGTHS_MONTHS, RECLEN_MIN_FIT_MONTHS, RECLEN_STABLE_TOL,
    RECLEN_DATUM_NSE_TOL, DATUM_SWEEP_MIN_M, DATUM_SWEEP_MAX_M, DATUM_SWEEP_STEP_M,
    FOREST_INTERCEPTION, UKCP18_SCENARIOS, WINTER_WET_CLIMATE_MONTHS, SUMMER_DRY_CLIMATE_MONTHS,
    RECORD_START_DISPLAY, REFERENCE_CUTOFF_DATE,
    TWO_STORE_FAST_INIT_DAYS, TWO_STORE_FAST_BOUNDS_DAYS, TWO_STORE_SLOW_INIT_DAYS,
    TWO_STORE_SLOW_BOUNDS_DAYS, TWO_STORE_SLOW_SHARE_INIT, TWO_STORE_EARLY_YEARS,
    TWO_STORE_EARLY_REDUCTION, TWO_STORE_LATER_RMSE_TOL_M, TWO_STORE_CCW_BIAS_TOL_M,
    TWO_STORE_CHECK_WELL, TWO_STORE_CHECK_CLUSTER, TWO_STORE_FLOOD_WINTERS, TWO_STORE_NEAR_WINTERS,
    TWO_STORE_DRY_WINTERS, TWO_STORE_SURFACE_TOL_M, TWO_STORE_NEAR_TOL_M, DAYS_PER_MONTH,
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
)
from utils.data_utils import normalize_well_name              # noqa: E402
from utils.model_utils import (build_ssm_frame, fit_ssm, simulate_ssm, get_metrics,   # noqa: E402
                               sustained_monthly_response, climate_forcing_change_12, response_identified)
from utils.hindcast_utils import (                            # noqa: E402
    load_ccw, observed_series, hindcast_well, equilibrium_depth, usable_codes, compare_offset_censored,
)
from utils.render_utils import MPL_DEFAULTS                   # noqa: E402
from utils.pastas_utils import spread_daily, continuous_start  # noqa: E402
from utils.midas_rain import read_daily  # noqa: E402
from utils.report_numbers_utils import ReportNumbers          # noqa: E402
from utils.console_utils import banner, done, info, phase, result, saved, step, warn   # noqa: E402

FORMS = (("A", False), ("B", True))
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
def load_inputs():
    lev = pd.read_csv(INT_WELLS_CLEAN, index_col=0)
    lev.index = pd.to_datetime(lev.index)
    cl = pd.read_csv(INT_CLIMATE, index_col=0)
    cl.index = pd.to_datetime(cl.index)
    master = pd.read_csv(INT_MASTER_DATA)
    master["_n"] = master["Name_Original"].astype(str).apply(normalize_well_name)
    lev_cols = {normalize_well_name(c): c for c in lev.columns}
    return lev, lev_cols, cl, master


def well_experiments(well: str, cluster: int, h: pd.Series, cl: pd.DataFrame) -> list:
    """forecast, hindcast_within and stability rows for one well, both forms."""
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    full = build_ssm_frame(h, cl, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM)
    pre = build_ssm_frame(h[h.index < split], cl, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM)
    post = build_ssm_frame(h[h.index >= split], cl, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM)
    te = {"forecast": h[h.index >= split], "hindcast_within": h[h.index < split]}
    side = {"forecast": (pre, "tail"), "hindcast_within": (post, "head")}
    rows = []
    base = {"well": well, "cluster": cluster}
    for form, icpt in FORMS:
        for exp in ("forecast", "hindcast_within"):
            fr_all, end = side[exp]
            for L in LENGTHS:
                if L == FULL:
                    fr = fr_all
                elif len(fr_all) >= int(L):
                    fr = fr_all.tail(int(L)) if end == "tail" else fr_all.head(int(L))
                else:
                    continue
                f = fit_frame(fr, icpt)
                row = dict(base, form=form, experiment=exp, length=L, placement="adjacent")
                row.update(describe(f, icpt, fr))
                row.update(free_run(te[exp], cl, f, icpt))
                rows.append(row)
        for L in LENGTHS:
            if L == FULL:
                frames = [("all", full)]
            else:
                k = len(full) // int(L)
                frames = [(str(i), full.iloc[i * int(L):(i + 1) * int(L)]) for i in range(k)]
            for plc, fr in frames:
                f = fit_frame(fr, icpt)
                row = dict(base, form=form, experiment="stability", length=L, placement=plc)
                row.update(describe(f, icpt, fr))
                rows.append(row)
    return rows


def ccw_experiment(lev, lev_cols, cl, master):
    """The CCW 1989-96 hindcast at every length, from the start and from the end of the modern
    record, both forms. Script 39's admission, seeding, spin-up, censoring and offsets, unchanged."""
    if not (paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()):
        warn("CCW historic inputs not present — the ccw_hindcast experiment is skipped")
        return pd.DataFrame()
    obs, cmap = load_ccw()
    md = pd.read_csv(INT_MASTER_DATA)
    md["k"] = md["Name_Original"].astype(str).str.lower().str.strip()
    md = md.set_index("k")
    adm = usable_codes(cmap, md, obs)
    adm = adm[adm["admitted"]]
    clh = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    p_mean, pet_mean = float(clh["P_m"].mean()), float(clh["PET"].mean())
    first_month, last_month = obs["month"].min(), obs["month"].max()
    rows = []
    for r in adm.itertuples():
        col = lev_cols.get(normalize_well_name(r.well))
        if col is None:
            continue
        o, _n_cens = observed_series(obs, r.code, r.datum_offset_m)
        if o.empty:
            continue
        full = build_ssm_frame(lev[col].dropna(), cl, lag=HEADLINE_LAG, drainage_datum=DRAINAGE_DATUM)
        cluster = int(md.loc[r.well, "Cluster"]) if "Cluster" in md.columns else -1
        for form, icpt in FORMS:
            for L in LENGTHS:
                for end in ("start", "end"):
                    if L == FULL:
                        if end == "start":
                            continue                       # the full record has one placement
                        fr = full
                    elif len(full) >= int(L):
                        fr = full.head(int(L)) if end == "start" else full.tail(int(L))
                    else:
                        continue
                    f = fit_frame(fr, icpt)
                    row = {"well": r.well, "code": r.code, "cluster": cluster, "form": form,
                           "length": L, "end": end if L != FULL else "all"}
                    row.update(describe(f, icpt, fr))
                    if f is None or not (f["beta_3_drainage"] > 0):
                        rows.append(row)
                        continue
                    betas = (f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"])
                    datum = run_datum(f, icpt)
                    h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=datum)
                    pred, _spin = hindcast_well(clh, betas, h0, first_month, last_month, 1.0,
                                                drainage_datum=datum)
                    common = o.index.intersection(pred.index)
                    nse, rmse, bias = get_metrics(o.loc[common], pred.loc[common])
                    oc, pc = o.loc[common].values, pred.loc[common].values
                    r_shape = float(np.corrcoef(oc, pc)[0, 1]) if len(oc) > 2 else np.nan
                    off = float(np.mean(pc - oc))
                    den = float(np.sum((oc - oc.mean()) ** 2))
                    row.update({"n_test": int(len(common)), "nse": float(nse), "rmse_m": float(rmse),
                                "bias_m": float(bias), "pearson_r": r_shape,
                                "nse_bias_removed": (1.0 - float(np.sum((oc - (pc - off)) ** 2)) / den)
                                if den > 0 else np.nan})
                    rows.append(row)
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Summaries
# ──────────────────────────────────────────────────────────────────────────────
def relative_deviation(df: pd.DataFrame) -> pd.DataFrame:
    """Per well x form x length: median over placements of |beta_3(L)/beta_3(full) - 1|."""
    st = df[(df["experiment"] == "stability") & df["fitted"].fillna(False).astype(bool)]
    ref = st[st["length"] == FULL].set_index(["well", "form"])["beta_3"]
    st = st[st["length"] != FULL].copy()
    st["b3_full"] = [ref.get((w, f), np.nan) for w, f in zip(st["well"], st["form"])]
    st["rel_dev"] = (st["beta_3"] / st["b3_full"] - 1.0).abs()
    st.loc[~(st["b3_full"] > 0), "rel_dev"] = np.nan
    g = st.groupby(["well", "cluster", "form", "length"])
    return g["rel_dev"].median().rename("rel_dev_median").reset_index().merge(
        g["identified"].mean().rename("identified_share").reset_index(),
        on=["well", "cluster", "form", "length"])


def stable_lengths(dev: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Each well's stable length per form, and that length in full-record Model B mean-reversion times."""
    efold_b = (df[(df["experiment"] == "stability") & (df["length"] == FULL) & (df["form"] == "B")]
               .set_index("well")["efold_months"])
    rows = []
    for (w, c, form), g in dev.groupby(["well", "cluster", "form"]):
        g = g.assign(L=g["length"].astype(int)).sort_values("L")
        ok = (g["rel_dev_median"] < RECLEN_STABLE_TOL).values
        stable = np.nan
        for i in range(len(g)):
            if ok[i:].all():
                stable = float(g["L"].iloc[i])
                break
        ef = float(efold_b.get(w, np.nan))
        rows.append({"well": w, "cluster": c, "form": form, "stable_length_months": stable,
                     "longest_length_tested": float(g["L"].max()), "efold_B_full_months": ef,
                     "stable_length_in_efolds": stable / ef if (np.isfinite(stable) and ef > 0) else np.nan})
    return pd.DataFrame(rows)


def groups(df: pd.DataFrame):
    yield "all", df
    for c, g in df.groupby("cluster"):
        if int(c) > 0:
            yield f"C{int(c)}", g


def by_cluster(df: pd.DataFrame, dev: pd.DataFrame, ccw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    def stats_(v):
        v = pd.to_numeric(v, errors="coerce").dropna()
        if not len(v):
            return np.nan, np.nan, np.nan, 0
        return float(v.median()), float(np.percentile(v, 10)), float(np.percentile(v, 90)), int(len(v))
    for exp in ("forecast", "hindcast_within"):
        sub = df[df["experiment"] == exp]
        for gname, g in groups(sub):
            for (form, L), gg in g.groupby(["form", "length"]):
                for metric in ("nse", "bias_m", "beta_3", "efold_months", "drainage_share"):
                    m, p10, p90, n = stats_(gg[metric])
                    rows.append(dict(group=gname, experiment=exp, form=form, length=L, end="",
                                     metric=metric, median=m, p10=p10, p90=p90, n_wells=n))
                rows.append(dict(group=gname, experiment=exp, form=form, length=L, end="",
                                 metric="identified_share", median=float(gg["identified"].fillna(False).astype(bool).mean()),
                                 p10=np.nan, p90=np.nan, n_wells=int(len(gg))))
    for gname, g in groups(dev):
        for (form, L), gg in g.groupby(["form", "length"]):
            for metric in ("rel_dev_median", "identified_share"):
                m, p10, p90, n = stats_(gg[metric])
                rows.append(dict(group=gname, experiment="stability", form=form, length=L, end="",
                                 metric=metric, median=m, p10=p10, p90=p90, n_wells=n))
    if len(ccw):
        for (form, L, end), gg in ccw.groupby(["form", "length", "end"]):
            for metric in ("nse", "bias_m", "pearson_r", "nse_bias_removed"):
                m, p10, p90, n = stats_(gg[metric])
                rows.append(dict(group="all", experiment="ccw_hindcast", form=form, length=L, end=end,
                                 metric=metric, median=m, p10=p10, p90=p90, n_wells=n))
    out = pd.DataFrame(rows)
    order = {L: i for i, L in enumerate(LENGTHS)}
    return out.sort_values(["experiment", "group", "form", "metric", "end"],
                           key=lambda s: s.map(order) if s.name == "length" else s,
                           kind="stable").reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# Identity checks: the full-length rows must reproduce Scripts 48 and 39
# ──────────────────────────────────────────────────────────────────────────────
def identity_checks(df: pd.DataFrame, ccw: pd.DataFrame) -> dict:
    out = {"vs48_max_abs_diff": np.nan, "vs48_n": 0, "vs39_max_abs_diff": np.nan, "vs39_n": 0}
    if OUT_48_MODEL_AB.exists():
        ab = pd.read_csv(OUT_48_MODEL_AB)
        ab["well"] = ab["well"].astype(str).apply(normalize_well_name)
        ab = ab.set_index("well")
        diffs = []
        for exp, d_ in (("forecast", "fwd"), ("hindcast_within", "rev")):
            f = df[(df["experiment"] == exp) & (df["length"] == FULL)]
            for _, r in f.iterrows():
                col = f"nse_{d_}_{r['form']}"
                w = normalize_well_name(r["well"])
                if w in ab.index and col in ab.columns and np.isfinite(r["nse"]) and np.isfinite(ab.loc[w, col]):
                    diffs.append(abs(r["nse"] - ab.loc[w, col]))
        if diffs:
            out.update(vs48_max_abs_diff=float(max(diffs)), vs48_n=len(diffs))
    if len(ccw) and OUT_39_PER_WELL.exists():
        p39 = pd.read_csv(OUT_39_PER_WELL).set_index("well")
        c = ccw[(ccw["form"] == "A") & (ccw["length"] == str(LCSC_DATA_LIMIT)) & (ccw["end"] == "end")]
        diffs = [abs(r["nse"] - p39.loc[r["well"], "nse"]) for _, r in c.iterrows()
                 if r["well"] in p39.index and np.isfinite(r.get("nse", np.nan))]
        if diffs:
            out.update(vs39_max_abs_diff=float(max(diffs)), vs39_n=len(diffs))
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Report numbers
# ──────────────────────────────────────────────────────────────────────────────
def report_numbers(df, dev, stab, ccw, summ, checks) -> ReportNumbers:
    rr = ReportNumbers()
    def get(exp, group, form, L, metric, end=""):
        s = summ[(summ.experiment == exp) & (summ.group == group) & (summ.form == form)
                 & (summ.length == L) & (summ.metric == metric) & (summ.end == end)]
        return (float(s["median"].iloc[0]), int(s["n_wells"].iloc[0])) if len(s) else (np.nan, 0)
    gnames = ["all"] + [f"C{c}" for c in sorted(int(x) for x in df["cluster"].unique() if int(x) > 0)]
    for exp, tag in (("forecast", "fwd"), ("hindcast_within", "rev")):
        for g in gnames:
            for form, _ in FORMS:
                for L in LENGTHS:
                    v, n = get(exp, g, form, L, "nse")
                    if n:
                        rr.add(f"reclen_nse_{tag}_{form}_median_L{L}_{g}", v, unit="",
                               note=f"median free-run NSE, Model {form}, fitted on {L} months "
                                    + ("before" if tag == "fwd" else "from")
                                    + f" {MODEL_AB_SPLIT_DATE}; n = {n} wells ({g})")
    for g in gnames:
        for form, _ in FORMS:
            for L in LENGTHS[:-1]:
                v, n = get("stability", g, form, L, "rel_dev_median")
                if n:
                    rr.add(f"reclen_beta3_reldev_{form}_median_L{L}_{g}", v, unit="fraction",
                           note=f"median over wells of the median over placements of |beta_3(L)/beta_3(full) - 1|, "
                                f"Model {form}, L = {L}; n = {n} wells ({g})")
                v, n = get("stability", g, form, L, "identified_share")
                if n:
                    rr.add(f"reclen_identified_share_{form}_median_L{L}_{g}", v, unit="fraction",
                           note=f"median over wells of the share of placements of {L} months on which Model {form}'s "
                                f"beta_3 is identified; n = {n} wells ({g})")
    for g, gg in groups(stab):
        for form, _ in FORMS:
            s = gg[gg["form"] == form]
            for col, unit, lab in (("stable_length_months", "months", "stable length"),
                                   ("stable_length_in_efolds", "", "stable length in full-record Model B mean-reversion times")):
                v = pd.to_numeric(s[col], errors="coerce").dropna()
                rr.add(f"reclen_{col}_{form}_median_{g}", float(v.median()) if len(v) else np.nan, unit=unit,
                       note=f"median {lab}, Model {form} (tolerance {RECLEN_STABLE_TOL:g}); "
                            f"{len(v)} of {len(s)} wells reach it within the lengths tested ({g})")
            rr.add(f"reclen_stable_n_wells_reached_{form}_{g}",
                   float(pd.to_numeric(s["stable_length_months"], errors="coerce").notna().sum()), unit="count",
                   note=f"wells whose Model {form} beta_3 becomes stable within the lengths tested ({g})")
    if len(ccw):
        for form, _ in FORMS:
            for L in LENGTHS:
                for end in (("all",) if L == FULL else ("start", "end")):
                    for metric in ("nse", "bias_m", "pearson_r"):
                        v, n = get("ccw_hindcast", "all", form, L, metric, end)
                        if n:
                            rr.add(f"reclen_ccw_{metric}_{form}_median_L{L}_{end}", v,
                                   unit="m" if metric == "bias_m" else "",
                                   note=f"CCW 1989-96 hindcast, Model {form} fitted on {L} months from the "
                                        f"{end} of the modern record; median over n = {n} wells")
    full = df[(df["experiment"] == "stability") & (df["length"] == FULL)]
    for g, gg in groups(full):
        for form, _ in FORMS:
            s = gg[gg["form"] == form]
            for col, unit, lab in (("rho_ar1_expected", "", "expected spring persistence (1 - beta_3)^12 (D-221)"),
                                   ("efold_months", "months", "mean-reversion time -1/ln(1 - beta_3)")):
                v = pd.to_numeric(s[col], errors="coerce").dropna()
                rr.add(f"reclen_{col}_full_{form}_median_{g}", float(v.median()) if len(v) else np.nan, unit=unit,
                       note=f"median {lab}, Model {form}, full record; n = {len(v)} wells ({g})")
    # T-103: the comparison window against the full record, per well (Script 03's 03_15)
    ws = pd.read_csv(OUT_03_PER_WELL_WINDOW_SENS)
    pv = ws.pivot_table(index=["Name_Original", "Cluster"], columns="basis", values="beta_3_drainage").reset_index()
    if {"comparison_window", "full_record"} <= set(pv.columns):
        pv["ratio"] = pv["comparison_window"] / pv["full_record"]
        pv.loc[~(pv["full_record"] > 0), "ratio"] = np.nan
        pv = pv.rename(columns={"Cluster": "cluster"})
        for g, gg in groups(pv):
            v = gg["ratio"].dropna()
            for q, val in (("median", v.median()), ("p10", np.percentile(v, 10) if len(v) else np.nan),
                           ("p90", np.percentile(v, 90) if len(v) else np.nan)):
                rr.add(f"window_full_beta3_ratio_{q}_{g}", float(val), unit="",
                       note=f"per-well beta_3 on the comparison window ({LCSC_DATA_LIMIT} months) over beta_3 on the "
                            f"full record, Model A (03_15); {q} over n = {len(v)} wells ({g}); T-103")
    rr.add("reclen_check_vs48_max_abs_nse_diff", checks["vs48_max_abs_diff"], unit="",
           note=f"identity check: full-length forecast / hindcast_within NSE against Script 48's split-sample NSE; "
                f"largest absolute difference over {checks['vs48_n']} well-form-direction pairs (expected 0)")
    rr.add("reclen_check_vs39_max_abs_nse_diff", checks["vs39_max_abs_diff"], unit="",
           note=f"identity check: CCW hindcast NSE, Model A on the last {LCSC_DATA_LIMIT} months, against Script 39; "
                f"largest absolute difference over {checks['vs39_n']} wells (expected 0)")
    return rr


# ──────────────────────────────────────────────────────────────────────────────
# 1.1.0 (D-225): which datum does the drier past support?
# ──────────────────────────────────────────────────────────────────────────────
def datum_grid() -> np.ndarray:
    """Script 03's datum sweep: DATUM_SWEEP_MIN_M to DATUM_SWEEP_MAX_M by DATUM_SWEEP_STEP_M."""
    return np.round(np.arange(DATUM_SWEEP_MIN_M, DATUM_SWEEP_MAX_M + DATUM_SWEEP_STEP_M / 2,
                              DATUM_SWEEP_STEP_M), 6)


def _dkey(D: float) -> str:
    return f"{D:g}"


def ccw_by_datum(lev, lev_cols, cl, loc_forest) -> pd.DataFrame:
    """E5: Model A refitted at every datum (comparison window and full record) and run through
    Script 39's hindcast at that datum over the CCW 1989-96 readings."""
    if not (paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()):
        warn("CCW historic inputs not present — the datum hindcast is skipped")
        return pd.DataFrame()
    obs, cmap = load_ccw()
    md = pd.read_csv(INT_MASTER_DATA)
    md["k"] = md["Name_Original"].astype(str).str.lower().str.strip()
    md = md.set_index("k")
    adm = usable_codes(cmap, md, obs)
    adm = adm[adm["admitted"]]
    clh = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    p_mean, pet_mean = float(clh["P_m"].mean()), float(clh["PET"].mean())
    first_month, last_month = obs["month"].min(), obs["month"].max()
    rows = []
    for r in adm.itertuples():
        col = lev_cols.get(normalize_well_name(r.well))
        if col is None:
            continue
        o, _n = observed_series(obs, r.code, r.datum_offset_m)
        if o.empty:
            continue
        h = lev[col].dropna()
        for D in datum_grid():
            frame = build_ssm_frame(h, cl, lag=HEADLINE_LAG, drainage_datum=float(D))
            for basis, fr in (("comparison_window", frame.tail(LCSC_DATA_LIMIT)), ("full_record", frame)):
                f = fit_frame(fr, False)
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
    for _, r in master.iterrows():
        col = lev_cols.get(r["_n"])
        if col is None:
            continue
        h = lev[col].dropna()
        pre_h, post_h = h[h.index < split], h[h.index >= split]
        for D in datum_grid():
            for direction, tr, te in (("fwd", pre_h, post_h), ("rev", post_h, pre_h)):
                fr = build_ssm_frame(tr, cl, lag=HEADLINE_LAG, drainage_datum=float(D))
                f = fit_frame(fr, False)
                res = free_run(te, cl, f, False, base=float(D))
                rows.append({"well": r["_n"], "cluster": int(r["Cluster"]), "datum_m": float(D),
                             "direction": direction, "nse": res["nse"], "n_test": res["n_test"]})
    return pd.DataFrame(rows)


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
    rows = []
    for _, r in master.iterrows():
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
        for D in datum_grid():
            fr = build_ssm_frame(h, cl, lag=HEADLINE_LAG, drainage_datum=float(D)).tail(LCSC_DATA_LIMIT)
            f = fit_frame(fr, False)
            if f is None or not response_identified(f["beta_3_drainage"], f["pvalue_beta_3"], f["n"], 3)[0]:
                continue
            for scen in UKCP18_SCENARIOS:
                s = UKCP18_SCENARIOS[scen]
                sP, sPET = np.ones(12), np.ones(12)
                for m in WINTER_WET_CLIMATE_MONTHS:
                    sP[m - 1], sPET[m - 1] = s["sP_w"], s["sPET_w"]
                for m in SUMMER_DRY_CLIMATE_MONTHS:
                    sP[m - 1], sPET[m - 1] = s["sP_s"], s["sPET_s"]
                for m in range(1, 13):
                    if m not in WINTER_WET_CLIMATE_MONTHS and m not in SUMMER_DRY_CLIMATE_MONTHS:
                        sP[m - 1], sPET[m - 1] = 0.5 * (s["sP_w"] + s["sP_s"]), 0.5 * (s["sPET_w"] + s["sPET_s"])
                ssA = sustained_monthly_response(f["beta_3_drainage"], climate_forcing_change_12(
                    f["beta_1_recharge"], f["beta_2_atmospheric_draw"], P12, PET12, sP, sPET, interception=I_))
                ssB = sustained_monthly_response(b["beta_3_B"], climate_forcing_change_12(
                    b["beta_1_B"], b["beta_2_B"], P12, PET12, sP, sPET, interception=I_))
                for sea, months in seasons.items():
                    idx = [m - 1 for m in months]
                    row = {"well": r["_n"], "cluster": int(r["Cluster"]), "datum_m": float(D),
                           "scenario": scen, "season": sea, "beta_3": f["beta_3_drainage"],
                           "fall_model_a_m": float(np.mean(ssA[idx])), "fall_model_b_m": float(np.mean(ssB[idx]))}
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
    for pr in pairs.itertuples():
        col = lev_cols.get(normalize_well_name(pr.well))
        if col is None or int(pr.site_no) not in obs_month.index.get_level_values(0):
            continue
        om = obs_month.loc[int(pr.site_no)]
        h = lev[col].dropna()
        base = {"site_no": int(pr.site_no), "sketch_slack": pr.sketch_slack, "well": normalize_well_name(pr.well),
                "headline": bool(pr.headline), "dist_m": float(pr.dist_m), "ground_m_od": float(pr.ground_m_od)}
        for D in datum_grid():
            frame = build_ssm_frame(h, cl, lag=HEADLINE_LAG, drainage_datum=float(D))
            for basis, fr in (("comparison_window", frame.tail(LCSC_DATA_LIMIT)), ("full_record", frame)):
                for form, intercept in FORMS:
                    # Model B does not depend on the datum it is built at (the intercept absorbs it):
                    # it is fitted once, at the project datum, and run at its own zero-drainage datum.
                    if intercept and not np.isclose(D, DRAINAGE_DATUM):
                        continue
                    f = fit_frame(fr, intercept)
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
        ml.add_noisemodel(ps.ArNoiseModel(ml))
    return ml


def _ts_solve(ml, P, tmin=None, tmax=None):
    start = pd.Timestamp(tmin) if tmin is not None else ml.oseries.series.index[0]
    ml.solve(tmin=tmin, tmax=tmax, report=False, warmup=int((start - P.index[0]).days))
    return ml


def _ts_sim(ml, P, a, b) -> pd.Series:
    a, b = pd.Timestamp(a), pd.Timestamp(b)
    return ml.simulate(tmin=a, tmax=b, warmup=int((a - P.index[0]).days))


def _nse(o: pd.Series, s: pd.Series) -> float:
    o, s = o.align(s, join="inner")
    ok = o.notna() & s.notna()
    o, s = o[ok], s[ok]
    den = float(((o - o.mean()) ** 2).sum())
    return 1.0 - float(((o - s) ** 2).sum()) / den if len(o) > 2 and den > 0 else np.nan


def _winter_max(s: pd.Series) -> pd.Series:
    w = s[s.index.month.isin([10, 11, 12, 1, 2, 3])]
    lab = np.where(w.index.month >= 10, w.index.year + 1, w.index.year)
    return w.groupby(lab).max()


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
        mdk = pd.read_csv(INT_MASTER_DATA)
        mdk["k"] = mdk["Name_Original"].astype(str).str.lower().str.strip()
        adm = usable_codes(cmap, mdk.set_index("k"), obs)
        adm = adm[adm["admitted"]]
    rows, models, sims = [], {}, {}
    clusters = [int(c[1:]) for c in ra.columns if c.startswith("C") and c[1:].isdigit()]
    for c in clusters:
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
                rows.append(row)
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
                ("slow_efold_months", d["slow_efold_months"], "months", "slow store's e-folding time, double exponential"),
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
            ml.add_noisemodel(ps.ArNoiseModel(ml))
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
        mdk = pd.read_csv(INT_MASTER_DATA)
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
    for c in clusters:
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
        p = proj_d[(proj_d["scenario"] == "2080s") & (proj_d["season"] == "summer")]
        for tag, D in (("supported", best), ("band_min", lo), ("band_max", hi), ("project", DRAINAGE_DATUM)):
            q = p[np.isclose(p["datum_m"], D)] if np.isfinite(D) else p.iloc[0:0]
            rr.add(f"projection_2080s_summer_fall_median_at_{tag}", float(q["fall_model_a_m"].median()) if len(q) else np.nan,
                   unit="m", note=f"median 2080s summer sustained level response, Model A at datum {D:g} m; "
                                  f"n = {len(q)} wells (forest withheld, D-224 pairing)")
            rr.add(f"projection_2080s_summer_room_left_min_at_{tag}", float(q["room_left_m"].min()) if len(q) else np.nan,
                   unit="m", note=f"smallest room left above the datum at the projected 2080s summer minimum, datum {D:g} m")
        q = p[np.isclose(p["datum_m"], DRAINAGE_DATUM)]
        rr.add("projection_2080s_summer_fall_median_model_b", float(q["fall_model_b_m"].median()) if len(q) else np.nan,
               unit="m", note="median 2080s summer sustained level response, Model B, the same wells")
    for k, v in checks_d.items():
        rr.add(f"reclen_check_{k}", v, unit="", note="identity check at the project datum (expected 0)")


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


# ──────────────────────────────────────────────────────────────────────────────
# Figure
# ──────────────────────────────────────────────────────────────────────────────
def plot(summ: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    Ls = [L for L in LENGTHS if L != FULL]
    x = np.array([int(L) for L in Ls], dtype=float)
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 6.6), dpi=160)
    panels = ((axes[0, 0], "stability", "rel_dev_median", "(a) |β₃(L)/β₃(full) − 1|, median over wells"),
              (axes[0, 1], "forecast", "nse", f"(b) Forecast NSE after {MODEL_AB_SPLIT_DATE[:4]}"),
              (axes[1, 0], "hindcast_within", "nse", f"(c) Hindcast NSE before {MODEL_AB_SPLIT_DATE[:4]}"))
    clusters = sorted(int(g[1:]) for g in summ["group"].unique() if g.startswith("C"))
    for ax, exp, metric, title in panels:
        for c in clusters:
            for form, ls in (("A", "-"), ("B", "--")):
                s = summ[(summ.experiment == exp) & (summ.group == f"C{c}") & (summ.form == form)
                         & (summ.metric == metric)].set_index("length").reindex(Ls)
                ax.plot(x, s["median"].values, ls=ls, marker="o", ms=3, lw=1.1,
                        color=CLUSTER_COLOURS.get(c, "0.4"),
                        label=(CLUSTER_LABELS.get(c, f"C{c}") if form == "A" else None))
        ax.set_title(title, loc="left", fontsize=9)
        ax.set_xlabel("record fitted, L (months)")
        ax.grid(alpha=0.3)
    axes[0, 0].axhline(RECLEN_STABLE_TOL, color="0.4", lw=0.8, ls=":")
    axes[0, 0].set_ylim(bottom=0)
    for ax in (axes[0, 1], axes[1, 0]):
        ax.axhline(0, color="0.5", lw=0.7)
        ax.set_ylim(-1, 1)
    ax = axes[1, 1]
    for form, ls in (("A", "-"), ("B", "--")):
        for end, mk in (("end", "o"), ("start", "s")):
            s = summ[(summ.experiment == "ccw_hindcast") & (summ.group == "all") & (summ.form == form)
                     & (summ.metric == "nse") & (summ.end == end)].set_index("length").reindex(Ls)
            ax.plot(x, s["median"].values, ls=ls, marker=mk, ms=3, lw=1.1, color="0.25",
                    label=f"Model {form}, L from the {end}")
    ax.axhline(0, color="0.5", lw=0.7)
    n_ccw = int(summ[(summ.experiment == "ccw_hindcast") & (summ.metric == "nse")]["n_wells"].max() or 0)
    ax.set_title(f"(d) CCW 1989–96 hindcast NSE, median of {n_ccw} wells", loc="left", fontsize=9)
    ax.set_xlabel("record fitted, L (months)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=6.5, loc="lower right")
    axes[0, 1].legend(fontsize=6.5, loc="lower right", title="solid Model A, dashed Model B", title_fontsize=6.5)
    for a in axes.ravel():
        a.set_xlim(x.min() - 6, x.max() + 6)
    fig.tight_layout()
    fig.savefig(OUT_50_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_50_FIG.name)


# ──────────────────────────────────────────────────────────────────────────────
def main(no_fig: bool = False) -> int:
    banner("50", "What the record length decides", version=__version__)
    DIR_50.mkdir(parents=True, exist_ok=True)

    phase(1, "Inputs")
    lev, lev_cols, cl, master = load_inputs()
    info(f"{len(master)} reference wells; lengths {', '.join(LENGTHS)} (fitted monthly changes); "
         f"split {MODEL_AB_SPLIT_DATE}; stability tolerance {RECLEN_STABLE_TOL:g}")

    phase(2, "Forecast, within-record hindcast and stability, both forms, every well")
    rows = []
    for _, r in master.iterrows():
        col = lev_cols.get(r["_n"])
        if col is None:
            warn(f"{r['Name_Original']}: no level column")
            continue
        rows += well_experiments(r["_n"], int(r["Cluster"]), lev[col].dropna(), cl)
    df = pd.DataFrame(rows)
    df["fitted"] = df["fitted"].fillna(False).astype(bool)
    info(f"{len(df)} fits ({int(df['fitted'].sum())} succeeded)")

    phase(3, "The CCW 1989-96 hindcast at every length")
    ccw = ccw_experiment(lev, lev_cols, cl, master)
    if len(ccw):
        info(f"{ccw['well'].nunique()} admitted wells, {len(ccw)} hindcasts")

    phase(4, "Stable lengths and the cluster summary")
    dev = relative_deviation(df)
    stab = stable_lengths(dev, df)
    summ = by_cluster(df, dev, ccw)
    for form, _ in FORMS:
        s = stab[stab["form"] == form]
        v = s["stable_length_months"].dropna()
        e = s["stable_length_in_efolds"].dropna()
        step(f"Model {form}: stable length median {v.median():.0f} months "
             f"({len(v)} of {len(s)} wells reach it); in mean-reversion times, median {e.median():.2f}")

    phase(5, "Identity checks against Scripts 48 and 39")
    checks = identity_checks(df, ccw)
    for k in ("vs48", "vs39"):
        d, n = checks[f"{k}_max_abs_diff"], checks[f"{k}_n"]
        (step if (n and d < 1e-9) else warn)(f"{k}: largest |ΔNSE| {d:.3g} over {n} comparisons")

    phase(6, "Which datum does the drier past support? (1.1.0, D-225)")
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
    proj_d.to_csv(OUT_50_PROJ_DATUM, index=False); saved(f"{OUT_50_PROJ_DATUM.name} ({len(proj_d)} rows)")

    phase(7, "Two drainage time scales per cluster (1.3.0, E8, D-231)")
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

    phase(8, "A non-climatic change (E8b) and surface flow (E8c), per cluster (1.4.0, D-232)")
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

    phase(9, "Rain event structure (E8d), per winter and per cluster (1.5.0, D-234)")
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

    phase(10, "The felling north of NW9 and its regrowth (E8e), per well (1.6.0, D-235)")
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

    phase(11, "The 2014/15 shore clearance: a step in the wells around it? (E8f, 1.7.0, D-236)")
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

    phase(12, "Outputs")
    df.to_csv(OUT_50_PER_WELL, index=False); saved(f"{OUT_50_PER_WELL.name} ({len(df)} rows)")
    summ.to_csv(OUT_50_BY_CLUSTER, index=False); saved(f"{OUT_50_BY_CLUSTER.name} ({len(summ)} rows)")
    ccw.to_csv(OUT_50_CCW, index=False); saved(f"{OUT_50_CCW.name} ({len(ccw)} rows)")
    stab.to_csv(OUT_50_STABLE, index=False); saved(f"{OUT_50_STABLE.name} ({len(stab)} rows)")
    rr = report_numbers(df, dev, stab, ccw, summ, checks)
    if len(ccw_d):
        datum_report(rr, ccw_d, split_d, proj_d, checks_d)
    if len(rw):
        ranwell_report(rr, rw, lo, hi)
    two_store_report(rr, ts_tab, ts_per, ts_nw, ts_verdict)
    change_surface_report(rr, cs_vc, cs_pc, cs_date, cs_vs, cs_ps)
    e8d_report(rr, e8_prim, e8_chk, e8_st, e8_verdict, e8_info)
    e8e_report(rr, fe_verdict, fe_info)
    e8f_report(rr, cf_tab, cf_verdict, cf_info)
    rr.save(OUT_50_REPORT_NUMBERS); saved(f"{OUT_50_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    if not no_fig:
        plot(summ)
        if len(ccw_d):
            plot_datum(ccw_d, split_d, proj_d, best, lo, hi, rw)
        plot_two_store(ts_tab, ts_well, ts_nw, ts_start)
        plot_change_surface(cs_ch, cs_sf, cs_sims, cs_pc, cs_ps)
        plot_rain_events(e8_prim, e8_chk)
        plot_felling(fe_tab, fe_timing, fe_info)
        plot_clearance_steps(cf_tab)
    result("record length", f"{df['well'].nunique()} wells; see {OUT_50_BY_CLUSTER.name}")
    done("50")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="What the record length decides")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figure")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
