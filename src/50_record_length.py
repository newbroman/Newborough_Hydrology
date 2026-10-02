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
  50_report_numbers.csv

Registered in run_analysis.py, Phase 19, tier X, opt-in (--with-supplementary).
Run directly:  python3 src/50_record_length.py [--no-fig]
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) - 2026-10-01 (D-225; Martin: "please spec it" / "I approve your
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
)
from utils.config import (                                    # noqa: E402
    DRAINAGE_DATUM, HEADLINE_LAG, CLUSTER_LABELS, CLUSTER_COLOURS, LCSC_DATA_LIMIT,
    MODEL_AB_SPLIT_DATE, MODEL_AB_MIN_TEST_MONTHS, PASTAS_IDENT_EFOLD_WINDOW_FRAC,
    RECLEN_LENGTHS_MONTHS, RECLEN_MIN_FIT_MONTHS, RECLEN_STABLE_TOL,
    RECLEN_DATUM_NSE_TOL, DATUM_SWEEP_MIN_M, DATUM_SWEEP_MAX_M, DATUM_SWEEP_STEP_M,
    FOREST_INTERCEPTION, UKCP18_SCENARIOS, WINTER_WET_CLIMATE_MONTHS, SUMMER_DRY_CLIMATE_MONTHS,
    RECORD_START_DISPLAY, REFERENCE_CUTOFF_DATE,
)
from utils.data_utils import normalize_well_name              # noqa: E402
from utils.model_utils import (build_ssm_frame, fit_ssm, simulate_ssm, get_metrics,   # noqa: E402
                               sustained_monthly_response, climate_forcing_change_12, response_identified)
from utils.hindcast_utils import (                            # noqa: E402
    load_ccw, observed_series, hindcast_well, equilibrium_depth, usable_codes,
)
from utils.render_utils import MPL_DEFAULTS                   # noqa: E402
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


def plot_datum(ccw_d, split_d, proj_d, best, lo, hi) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), dpi=160)
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
    axes[1].set_title("(b) Within-record split test, median NSE", loc="left", fontsize=9)
    axes[1].legend(fontsize=7)
    p = proj_d[(proj_d["scenario"] == "2080s") & (proj_d["season"] == "summer")]
    q = p.groupby("datum_m")["fall_model_a_m"]
    axes[2].plot(q.median().index, q.median().values, color="0.15", lw=1.4, label="Model A, median")
    axes[2].fill_between(q.quantile(0.1).index, q.quantile(0.1).values, q.quantile(0.9).values, color="0.6", alpha=0.3,
                         lw=0, label="Model A, 10th–90th percentile")
    axes[2].axhline(float(p[np.isclose(p["datum_m"], DRAINAGE_DATUM)]["fall_model_b_m"].median()), color="#2166ac",
                    lw=1.1, ls=":", label="Model B, median")
    axes[2].set_title("(c) 2080s summer level change (m)", loc="left", fontsize=9)
    axes[2].legend(fontsize=7)
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
    ccw_d.to_csv(OUT_50_CCW_DATUM, index=False); saved(f"{OUT_50_CCW_DATUM.name} ({len(ccw_d)} rows)")
    split_d.to_csv(OUT_50_SPLIT_DATUM, index=False); saved(f"{OUT_50_SPLIT_DATUM.name} ({len(split_d)} rows)")
    proj_d.to_csv(OUT_50_PROJ_DATUM, index=False); saved(f"{OUT_50_PROJ_DATUM.name} ({len(proj_d)} rows)")

    phase(7, "Outputs")
    df.to_csv(OUT_50_PER_WELL, index=False); saved(f"{OUT_50_PER_WELL.name} ({len(df)} rows)")
    summ.to_csv(OUT_50_BY_CLUSTER, index=False); saved(f"{OUT_50_BY_CLUSTER.name} ({len(summ)} rows)")
    ccw.to_csv(OUT_50_CCW, index=False); saved(f"{OUT_50_CCW.name} ({len(ccw)} rows)")
    stab.to_csv(OUT_50_STABLE, index=False); saved(f"{OUT_50_STABLE.name} ({len(stab)} rows)")
    rr = report_numbers(df, dev, stab, ccw, summ, checks)
    if len(ccw_d):
        datum_report(rr, ccw_d, split_d, proj_d, checks_d)
    rr.save(OUT_50_REPORT_NUMBERS); saved(f"{OUT_50_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    if not no_fig:
        plot(summ)
        if len(ccw_d):
            plot_datum(ccw_d, split_d, proj_d, best, lo, hi)
    result("record length", f"{df['well'].nunique()} wells; see {OUT_50_BY_CLUSTER.name}")
    done("50")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="What the record length decides")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figure")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
