"""
39_ccw_hindcast.py — SSM hindcast against the 1989–96 CCW record
================================================================

Predicts the water table over June 1989 to April 1996 from RAF Valley climate
alone, using SSM coefficients fitted on 2005–2026, and compares the prediction
with the CCW dipwell record recovered from `fc and ccw waterlevels`.

Why this exists
---------------
Every test of the SSM reported so far lies inside its own calibration window.
This is the first out-of-sample one: sixteen years before that window opens, in
an epoch whose annual water balance sits well below the calibration period's.
It tests predicted LEVELS against observed levels, so unlike a trend comparison
it does not depend on the network resolving a rate.

The second question it answers is the older one. The 1989–95 water table was
recorded as depressed, and that depression has been read since as a forest
signal, a drought signal, or a compound of both that the data of the day could
not separate. The hindcast supplies the climate-only expectation directly; the
residual between it and the observation is the part climate does not explain.
This script computes the residual and reports it. It does not attribute it —
the canopy state of 1989 is not observed, and the attribution needs that.

What it does NOT establish
--------------------------
Coefficient stationarity, which it assumes and which the corpus contradicts:
the site-wide beta_1 decline means beta_1 in 1989 was plausibly higher than the
fitted value. Run with the fitted value alone, the hindcast under-predicts
recharge and places the table too deep, pushing the residual toward "observed
wetter than modelled". The direction is knowable, so the script reports a
sensitivity envelope over a range of beta_1 scalings rather than a single
number, and every headline is quoted as an envelope.

Method
------
  * Forcing: committed RAF Valley monthly P and PET, from the start of that
    record, so the initial condition is forgotten long before 1989. Spin-up
    length and the h0 sensitivity are both reported, not assumed.
  * Recurrence: utils.model_utils.simulate_ssm — the shared implementation, not
    a local copy. Coefficients are read per well from the committed master data.
  * Observations: the CCW block as a tidy committed CSV, bucketed to months by
    the project rule (reading on day <= 15 belongs to the previous month), which
    every one of these readings satisfies.
  * Datum: historic depths are carried onto the modern ground datum by a
    per-well offset in the code map. Where derivable the offset is the 1989
    ground elevation implied by the workbook's own derived level columns, less
    the committed DGPS value; it is at most 0.061 m. This is equivalent to
    reducing the original dip against today's measured upstand provided the pipe
    has not moved, which the size of the offsets supports and which nothing here
    can prove. Wells with no derivable offset are carried unadjusted and flagged.
  * Censoring: readings at the pipe base (-2.000 m) are excluded from every
    metric and counted in the output. They are left-censored, not missing, so
    including them would bias the comparison toward the model.
  * Mapping: codes are mapped to wells through the committed code map, which
    carries a status per code. Only `confirmed` codes enter the headline; the
    disputed and unidentified ones are reported separately and never pooled.

Registered, and what it reads
-----------------------------
Registered in run_analysis.py (Phase 16, analytical tier, runs by default). It
reads a raw input — the CCW block — that no pipeline step produces; the
exception is recorded as D-051 and the evaluation basis as RB-14. The step
SKIPS cleanly when that input is absent, so a default full run cannot fail over
it. It can also be run directly:  python3 src/39_ccw_hindcast.py

The full-record pass
--------------------
The recurrence already ran the whole committed climate record as spin-up before
the comparison window opened. The full-record pass keeps that series instead of
discarding it, over an open-ground panel whose inclusion policy is declared in
open_ground_panel(). Each well is expressed as an anomaly against its OWN
modelled mean over its OWN modern record span, so the curve carries no
observed-to-modelled offset and no cross-well datum assumption.

This is the modern aquifer driven by historic climate, NOT a reconstruction of
the historic aquifer. The coefficients are fitted 2005-2026 and applied
unchanged throughout; beta_3 in particular encodes a drainage geometry the
record cannot hold fixed across the span. Any caption must say so.

Inputs (via utils.paths):
    CCW_DEPTHS        (data/ccw_1989_1996_depths.csv)     historic depths, tidy
    CCW_CODE_MAP      (data/ccw_1989_1996_code_map.csv)   code -> well + status
    INT_CLIMATE       (01_climate.csv)                    P_m, PET in m/month
    INT_MASTER_DATA   (03_master_data.csv)                per-well beta_1/2/3
    INT_LOCATIONS     (01_locations.csv)                  ground elevation
    INT_WELLS_CLEAN   (01_wells_clean.csv)                modern levels, context

Outputs (outputs/39_ccw_hindcast/):
    39_01_hindcast_per_well.csv    NSE, bias, RMSE, n, censored, per well
    39_02_hindcast_series.csv      observed and predicted, monthly, per well
    39_03_beta1_sensitivity.csv    metrics across the beta_1 scaling range
    39_04_hindcast.png             observed vs predicted, one panel per well
    39_05_full_hindcast_site.csv   full-record site anomaly, monthly, with n_wells
    39_06_full_hindcast_decadal.csv  per-decade mean anomaly, per well and site
    39_07_full_hindcast.png        full-record panel + the CCW epoch check
    39_results.txt                 console summary
"""

from __future__ import annotations

__version__ = "1.3.0"  # Hollingham (2026) — 2026-08-22.  Emits the
#   full-record hindcast alongside the CCW comparison. The recurrence already
#   ran the whole committed climate record as spin-up and discarded all but
#   the comparison window; this issue keeps it. Three new artefacts, an
#   open-ground panel whose inclusion policy is declared in one function, and
#   an epoch check that puts the observed and hindcast contrasts over the CCW
#   window side by side so the curve is anchored where there is data. Each
#   well is expressed against its OWN modelled mean over its own modern span,
#   so no observed-to-modelled offset enters the anomaly. Nothing in the
#   existing outputs moves.
#
# v1.2.0  # Hollingham (2026) — 2026-08-22.
#   Store-time rounding removed from the twenty-two stored columns of the per-well and
#   per-month frames — every metric this script emits (D-035): the store now
#   carries what the pipeline computed and rounding happens where the number
#   is displayed. No published value moves — the stored precision was at or
#   above the displayed precision at every site — but rounding_lint counts
#   these and the count had gone up, which is how 304 accepted sites
#   accumulated across the pipeline in the first place.
#
# v1.1.0  # Hollingham (2026) — 2026-08-21.  Joins the committed
#   canopy history, so each well's 1989 canopy state and felling year travel
#   with its result and the bias split is reported against them rather than
#   against the modern land-cover flag. The modern flag answers "is this well
#   under canopy now", which is the wrong question for a 1989-96 comparison:
#   five of these wells were felled around 1995 and one in 2017, so their
#   fitted coefficients describe a canopy that did not exist over the window
#   being hindcast. Optional input — absent, the columns come back blank and
#   nothing else changes.
#
# v1.0.0  # Hollingham (2026) — 2026-08-21.  Registered in the
#   pipeline (Phase 16, tier A, default). Two changes go with registration:
#   the run now SKIPS cleanly when the CCW inputs are absent, since a default
#   step must not fail a full run over an optional raw input; and the code map
#   carries Martin's correction that wmc3 is 2C and wmc2 is 2G, restoring the
#   CCW Wells header. The first issue ran 2G against wmc3 and produced the only
#   epoch shift in the network with the wrong sign — that anomaly was the
#   mis-assignment, not a datum fault, and it is gone.
#
# v0.2.0  # Hollingham (2026) — 2026-08-21.  Adds the three
#   diagnostics that separate a wrong LEVEL from wrong DYNAMICS, after the
#   first issue's canopy reading proved too neat: the observed-to-predicted
#   correlation, the NSE with the mean offset removed, and the epoch shift
#   between each well's historic and modern means with a sign-anomaly flag.
#   NSE alone cannot tell a model that mistimes the swing from one that tracks
#   it against the wrong datum, and both are present in this record.
#
# v0.1.0  # Hollingham (2026) — 2026-08-21. First issue.

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import config, paths
from scipy import stats

from utils.model_utils import simulate_ssm, get_metrics
from utils.console_utils import banner, phase, step, info, warn, saved, note, result, done
from utils.render_utils import render_figure

SCRIPT_ID = "39"
VERSION = __version__

PIPE_BASE_M = config.CCW_PIPE_BASE_M
BETA1_SCALINGS = config.CCW_BETA1_SCALINGS
H0_PROBE_OFFSETS_M = config.CCW_H0_PROBE_OFFSETS_M
DATUM = config.DRAINAGE_DATUM
MIN_MODERN_MONTHS = config.FULL_HINDCAST_MIN_MODERN_MONTHS
SMOOTH_MONTHS = config.FULL_HINDCAST_SMOOTH_MONTHS

OUT_DIR = paths.DIR_39
OUT_PER_WELL = paths.OUT_39_PER_WELL
OUT_SERIES = paths.OUT_39_SERIES
OUT_SENSITIVITY = paths.OUT_39_BETA1_SENSITIVITY
OUT_FIG = paths.OUT_39_FIG
OUT_TXT = paths.OUT_39_RESULTS
OUT_FULL_SITE = paths.OUT_39_FULL_SITE
OUT_FULL_DECADAL = paths.OUT_39_FULL_DECADAL
OUT_FULL_FIG = paths.OUT_39_FULL_FIG

BETA_COLS = ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage")


# ── data ──────────────────────────────────────────────────────────────────────
def load_inputs():
    """Historic depths, the code map, climate, coefficients and elevations."""
    obs = pd.read_csv(paths.CCW_DEPTHS)
    obs["month"] = pd.PeriodIndex(obs["month"], freq="M").to_timestamp()

    cmap = pd.read_csv(paths.CCW_CODE_MAP)
    cmap["well"] = cmap["well"].fillna("").astype(str).str.lower().str.strip()

    cl = pd.read_csv(paths.INT_CLIMATE, index_col=0, parse_dates=True)
    cl = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()

    md = pd.read_csv(paths.INT_MASTER_DATA)
    md["k"] = md["Name_Original"].astype(str).str.lower().str.strip()
    md = md.set_index("k")

    loc = pd.read_csv(paths.INT_LOCATIONS)
    loc["k"] = loc["Name"].astype(str).str.lower().str.strip()
    loc = loc.set_index("k")

    # Canopy history is optional: without it the two columns come back blank and
    # every other output is unchanged. With it, the 1989 state is available and
    # the modern land-cover flag stops standing in for a question it cannot
    # answer.
    if paths.CANOPY_HISTORY.exists():
        ch = pd.read_csv(paths.CANOPY_HISTORY)
        ch["well"] = ch["well"].astype(str).str.lower().str.strip()
        ch = ch.set_index("well")
    else:
        ch = pd.DataFrame(columns=["canopy_1989", "felled_year"])
    return obs, cmap, cl, md, loc, ch


def observed_series(obs: pd.DataFrame, code: str, offset_m: float):
    """Monthly observed depth for one code, on the modern ground datum.

    Returns (series, n_censored). Censored readings are dropped from the series
    and counted, because a reading held at the pipe base is a lower bound rather
    than a level and would drag any metric toward the model.
    """
    g = obs[obs["code"] == code].sort_values("month")
    n_cens = int(g["censored_at_pipe_base"].sum())
    g = g[~g["censored_at_pipe_base"]]
    s = pd.Series(g["depth_m_bg"].values, index=g["month"].values, name=code)
    if np.isfinite(offset_m):
        s = s + offset_m
    return s, n_cens


def modern_mean(wells_clean: pd.DataFrame, well: str) -> float:
    """Mean modern level for one well, for the epoch-shift diagnostic."""
    col = {c.lower().strip(): c for c in wells_clean.columns}.get(well)
    if col is None:
        return np.nan
    s = pd.to_numeric(wells_clean[col], errors="coerce").dropna()
    return float(s.mean()) if len(s) else np.nan


# ── hindcast ──────────────────────────────────────────────────────────────────
def hindcast_well(cl: pd.DataFrame, betas: tuple, h0: float,
                  first_month, last_month, beta1_scale: float = 1.0):
    """Simulate from the start of the climate record and return the window.

    The simulation runs from the first month of the committed climate record so
    that the initial condition is forgotten long before the comparison window
    opens; `spinup_months` is returned so the claim can be checked rather than
    asserted.
    """
    b1, b2, b3 = betas
    sub = cl.loc[:last_month]
    h = simulate_ssm(h0, sub["P_m"].values, sub["PET"].values,
                     b1 * beta1_scale, b2, b3, drainage_datum=DATUM)
    sim = pd.Series(h, index=sub.index, name="predicted_m_bg")
    spinup = int((sim.index < first_month).sum())
    return sim.loc[first_month:last_month], spinup


def equilibrium_depth(betas: tuple, p_mean: float, pet_mean: float) -> float:
    """Steady-state depth implied by the coefficients under mean forcing.

    Setting the monthly change to zero in the SSM recurrence gives
    h* = (b1*P - b2*PET)/b3 - D. Used as the starting value, so the run begins
    near its own attractor rather than at an arbitrary level.
    """
    b1, b2, b3 = betas
    if not np.isfinite(b3) or b3 <= 0:
        return np.nan
    return (b1 * p_mean - b2 * pet_mean) / b3 - DATUM


def usable_codes(cmap: pd.DataFrame, md: pd.DataFrame, obs: pd.DataFrame):
    """Codes admissible to the headline: confirmed mapping, and a well with a
    committed coefficient triple. Everything else is reported, never pooled."""
    rows = []
    for r in cmap.itertuples():
        why = ""
        if r.status != "confirmed":
            why = f"mapping {r.status}"
        elif not r.well:
            why = "no well"
        elif r.well not in md.index:
            why = "no committed coefficients"
        elif not all(np.isfinite(md.loc[r.well, c]) for c in BETA_COLS):
            why = "coefficient triple incomplete"
        elif md.loc[r.well, BETA_COLS[2]] <= 0:
            why = "non-positive drainage coefficient"
        n_c = int(obs.loc[obs["code"] == r.code, "censored_at_pipe_base"].sum())
        n_t = int((obs["code"] == r.code).sum())
        if not why and n_t and n_c / n_t > config.CCW_MAX_CENSORED_FRACTION:
            why = f"censored in {n_c} of {n_t} months"
        rows.append(dict(code=r.code, well=r.well, status=r.status,
                         datum_offset_m=r.datum_offset_m,
                         n_months=n_t, n_censored=n_c,
                         admitted=(why == ""), excluded_because=why))
    return pd.DataFrame(rows)


# ── figure ────────────────────────────────────────────────────────────────────
def plot_hindcast(series: pd.DataFrame, adm: pd.DataFrame, fig_path) -> None:
    wells = list(dict.fromkeys(series["well"]))
    if not wells:
        return
    ncol = 2
    nrow = int(np.ceil(len(wells) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(9.0, 2.2 * nrow), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    for ax, w in zip(axes, wells):
        g = series[series["well"] == w]
        ax.plot(g["month"], g["observed_m_bg"], "o-", ms=3, lw=1.0,
                label="observed", color="#1b1b1b")
        ax.plot(g["month"], g["predicted_m_bg"], "-", lw=1.4,
                label="hindcast", color="#D95F02")
        ax.fill_between(g["month"], g["predicted_lo_m_bg"], g["predicted_hi_m_bg"],
                        color="#D95F02", alpha=0.20, lw=0,
                        label=r"$\beta_1$ range")
        row = adm[adm["well"] == w]
        code = row["code"].iloc[0] if len(row) else "?"
        ax.set_title(f"{w} (CCW {code})", fontsize=10, loc="left")
        ax.axhline(PIPE_BASE_M, color="#777777", lw=0.8, ls=":")
        ax.set_ylabel("m below ground", fontsize=9)
        ax.tick_params(labelsize=9)
    for ax in axes[len(wells):]:
        ax.set_visible(False)
    axes[0].legend(fontsize=9, loc="lower right", framealpha=0.9)
    fig.suptitle("SSM hindcast against the 1989–96 CCW record "
                 "(coefficients fitted 2005–2026)", fontsize=11)
    fig.tight_layout()
    render_figure(fig, fig_path)
    plt.close(fig)



# ── full-record panel ─────────────────────────────────────────────────────────
def modern_span(wells_clean: pd.DataFrame, well: str):
    """First and last month of a well's modern committed record, and its length.

    Returns (first, last, n_months); all NaT/0 when the well has no column or no
    readings. The span defines the reference window that the full-record anomaly
    is taken against, so it is read from the record rather than assumed.
    """
    col = {c.lower().strip(): c for c in wells_clean.columns}.get(well)
    if col is None:
        return pd.NaT, pd.NaT, 0
    s = pd.to_numeric(wells_clean[col], errors="coerce").dropna()
    if s.empty:
        return pd.NaT, pd.NaT, 0
    return s.index.min(), s.index.max(), int(len(s))


def open_ground_panel(md: pd.DataFrame, loc: pd.DataFrame,
                      wells_clean: pd.DataFrame) -> pd.DataFrame:
    """Wells admitted to the full-record panel, with the reason for each refusal.

    The inclusion policy is declared in one place rather than left implicit in a
    filter chain. A well enters when three conditions hold: it is not under
    canopy on the committed land-cover flag; it carries a committed coefficient
    triple with a positive drainage coefficient; and its modern record reaches
    config.FULL_HINDCAST_MIN_MODERN_MONTHS, which is the baseline the anomaly is
    measured against. Wells failing any condition are returned with the reason
    recorded, never silently dropped.
    """
    rows = []
    for well in sorted(set(md.index) & set(loc.index)):
        in_forest = bool(loc.loc[well, "in_forest"]) if "in_forest" in loc.columns else False
        betas = tuple(pd.to_numeric(pd.Series([md.loc[well, c] for c in BETA_COLS]),
                                    errors="coerce"))
        first, last, n_mod = modern_span(wells_clean, well)
        reason = ""
        if in_forest:
            reason = "under canopy"
        elif not all(np.isfinite(b) for b in betas):
            reason = "no committed coefficient triple"
        elif not betas[2] > 0:
            reason = "non-positive drainage coefficient"
        elif n_mod < MIN_MODERN_MONTHS:
            reason = f"modern record {n_mod} months, below {MIN_MODERN_MONTHS}"
        rows.append(dict(well=well, admitted=(reason == ""), excluded_because=reason,
                         beta_1_recharge=betas[0], beta_2_atmospheric_draw=betas[1],
                         beta_3_drainage=betas[2],
                         modern_first=first, modern_last=last, n_modern_months=n_mod))
    return pd.DataFrame(rows)


def full_hindcast_well(cl: pd.DataFrame, betas: tuple, h0: float) -> pd.Series:
    """Simulate the whole committed climate record and return every month.

    The same recurrence and the same shared implementation as the windowed
    hindcast; only the returned span differs. The caller supplies the initial
    condition and is responsible for reporting the spin-up.
    """
    b1, b2, b3 = betas
    h = simulate_ssm(h0, cl["P_m"].values, cl["PET"].values, b1, b2, b3,
                     drainage_datum=DATUM)
    return pd.Series(h, index=cl.index, name="predicted_m_bg")


def plot_full_hindcast(site: pd.DataFrame, epoch: pd.DataFrame,
                       first_month, last_month, fig_path) -> None:
    """Two panels: the full-record site anomaly, and the epoch check against it."""
    fig, (ax, bx) = plt.subplots(
        2, 1, figsize=(9.0, 6.4),
        gridspec_kw=dict(height_ratios=[2.3, 1.0]))

    ax.axhline(0.0, color="#777777", lw=0.8, ls="-")
    ax.plot(site["month"], site["site_anomaly_m"], lw=0.6, color="#9ecae1")
    ax.plot(site["month"], site["site_anomaly_smoothed_m"], lw=1.6, color="#08519c")
    ax.fill_between(site["month"],
                    site["site_anomaly_m"] - site["site_sd_m"],
                    site["site_anomaly_m"] + site["site_sd_m"],
                    color="#9ecae1", alpha=0.25, lw=0)
    ax.axvspan(first_month, last_month, color="#D95F02", alpha=0.14, lw=0)
    ax.annotate("CCW record", xy=(first_month, ax.get_ylim()[1]),
                xytext=(4, -10), textcoords="offset points",
                fontsize=9, color="#8c3b02", va="top")
    ax.set_ylabel("anomaly vs modelled modern mean (m)", fontsize=9)
    ax.tick_params(labelsize=9)
    ax.set_title("Open-ground water table under the observed climate record, "
                 "modern coefficients throughout", fontsize=11, loc="left")

    if not epoch.empty:
        idx = np.arange(len(epoch))
        bx.bar(idx - 0.19, epoch["observed_epoch_anomaly_m"], width=0.38,
               color="#1b1b1b", label="observed")
        bx.bar(idx + 0.19, epoch["hindcast_epoch_anomaly_m"], width=0.38,
               color="#D95F02", label="hindcast")
        bx.set_xticks(idx)
        bx.set_xticklabels(epoch["well"], fontsize=9)
        bx.axhline(0.0, color="#777777", lw=0.8)
        bx.set_ylabel("epoch anomaly (m)", fontsize=9)
        bx.tick_params(labelsize=9)
        bx.legend(fontsize=9, framealpha=0.9)
        bx.set_title(f"Epoch contrast over {first_month:%Y-%m} to {last_month:%Y-%m}, "
                     "each series against its own modern mean",
                     fontsize=10, loc="left")
    fig.tight_layout()
    render_figure(fig, fig_path)
    plt.close(fig)


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    banner(SCRIPT_ID, "SSM hindcast against the 1989–96 CCW record", VERSION)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    phase(1, "Load inputs")
    missing = [q for q in (paths.CCW_DEPTHS, paths.CCW_CODE_MAP) if not q.exists()]
    if missing:
        warn("CCW historic inputs not present: "
             + ", ".join(q.name for q in missing))
        note("skipping — the 1989-96 block is an optional raw input and its "
             "absence is not a pipeline failure")
        return 0
    obs, cmap, cl, md, loc, ch = load_inputs()
    wells_clean = pd.read_csv(paths.INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    first_month = obs["month"].min()
    last_month = obs["month"].max()
    info(f"CCW record: {len(obs)} readings, {obs['code'].nunique()} codes, "
         f"{first_month:%Y-%m} to {last_month:%Y-%m}")
    info(f"climate forcing available from {cl.index.min():%Y-%m}")
    p_mean, pet_mean = float(cl["P_m"].mean()), float(cl["PET"].mean())

    phase(2, "Admit codes")
    adm = usable_codes(cmap, md, obs)
    for r in adm.itertuples():
        if r.admitted:
            step(f"{r.code} -> {r.well}")
        else:
            note(f"{r.code} excluded: {r.excluded_because}")
    admitted = adm[adm["admitted"]]
    if admitted.empty:
        warn("no admissible codes; nothing to hindcast")
        return 1
    result("codes admitted", f"{len(admitted)} of {len(adm)}")

    phase(3, "Hindcast")
    per_well, series_rows, sens_rows = [], [], []
    for r in admitted.itertuples():
        betas = tuple(float(md.loc[r.well, c]) for c in BETA_COLS)
        h0 = equilibrium_depth(betas, p_mean, pet_mean)
        o, n_cens = observed_series(obs, r.code, r.datum_offset_m)
        if o.empty:
            note(f"{r.code}: no uncensored observations")
            continue

        by_scale = {}
        for sc in BETA1_SCALINGS:
            pred, spinup = hindcast_well(cl, betas, h0, first_month, last_month, sc)
            common = o.index.intersection(pred.index)
            nse, rmse, bias = get_metrics(o.loc[common], pred.loc[common])
            m = {"NSE": nse, "RMSE": rmse, "Bias": bias}
            by_scale[sc] = (pred, common, m)
            sens_rows.append(dict(well=r.well, code=r.code, beta1_scale=sc,
                                  in_forest=(bool(loc.loc[r.well, "in_forest"])
                                             if r.well in loc.index else None),
                                  canopy_changed_since_1989=(
                                      bool(r.well in ch.index
                                           and pd.notna(ch.loc[r.well, "felled_year"]))),
                                  n=len(common),
                                  nse=float(m["NSE"]),
                                  rmse_m=float(m["RMSE"]),
                                  bias_m=float(m["Bias"]),
                                  mean_observed_m=float(o.loc[common].mean()),
                                  mean_predicted_m=float(pred.loc[common].mean())))

        base = 1.0 if 1.0 in by_scale else sorted(by_scale)[0]
        pred, common, m = by_scale[base]
        lo = np.minimum.reduce([by_scale[s][0].loc[common].values for s in by_scale])
        hi = np.maximum.reduce([by_scale[s][0].loc[common].values for s in by_scale])

        # h0 probe: restart from the equilibrium depth displaced either way and
        # confirm the comparison window has forgotten it.
        h0_spread = 0.0
        for off in H0_PROBE_OFFSETS_M:
            alt, _ = hindcast_well(cl, betas, h0 + off, first_month, last_month, base)
            h0_spread = max(h0_spread, float(np.nanmax(np.abs(
                alt.loc[common].values - pred.loc[common].values))))

        # Level and dynamics are separate failures and NSE conflates them: a
        # hindcast that tracks the swing against the wrong datum scores worse
        # than one that misses the swing entirely. The correlation answers
        # whether the dynamics are right; the bias-removed NSE answers what the
        # fit would be if the level were. The epoch shift is the data-quality
        # companion — a well whose historic mean sits on the opposite side of
        # its modern mean from the rest of the network is telling us something
        # about its datum or its identity, not about the model.
        oc, pc = o.loc[common].values, pred.loc[common].values
        r_shape = float(stats.pearsonr(oc, pc).statistic) if len(oc) > 2 else np.nan
        off = float(np.mean(pc - oc))
        denom = float(np.sum((oc - oc.mean()) ** 2))
        nse_db = (1.0 - float(np.sum((oc - (pc - off)) ** 2)) / denom
                  if denom > 0 else np.nan)
        m_mod = modern_mean(wells_clean, r.well)
        epoch_shift = float(oc.mean() - m_mod) if np.isfinite(m_mod) else np.nan

        per_well.append(dict(
            well=r.well, code=r.code, n_months=len(common), n_censored=n_cens,
            in_forest=bool(loc.loc[r.well, "in_forest"]) if r.well in loc.index else None,
            canopy_1989=(str(ch.loc[r.well, "canopy_1989"])
                         if r.well in ch.index else ""),
            felled_year=(str(ch.loc[r.well, "felled_year"])
                         if r.well in ch.index
                         and pd.notna(ch.loc[r.well, "felled_year"]) else ""),
            canopy_changed_since_1989=(bool(r.well in ch.index
                                            and pd.notna(ch.loc[r.well, "felled_year"]))),
            beta_1=betas[0], beta_2=betas[1], beta_3=betas[2],
            datum_offset_m=r.datum_offset_m,
            h0_equilibrium_m=h0, spinup_months=spinup,
            h0_sensitivity_m=h0_spread,
            mean_observed_m=float(o.loc[common].mean()),
            mean_predicted_m=float(pred.loc[common].mean()),
            residual_mean_m=float((o.loc[common] - pred.loc[common]).mean()),
            nse=float(m["NSE"]), rmse_m=float(m["RMSE"]),
            bias_m=float(m["Bias"]),
            pearson_r=r_shape if np.isfinite(r_shape) else np.nan,
            nse_bias_removed=nse_db if np.isfinite(nse_db) else np.nan,
            mean_modern_m=m_mod if np.isfinite(m_mod) else np.nan,
            epoch_shift_m=epoch_shift if np.isfinite(epoch_shift) else np.nan))

        for t in common:
            series_rows.append(dict(
                well=r.well, code=r.code, month=t.strftime("%Y-%m"),
                observed_m_bg=float(o.loc[t]),
                predicted_m_bg=float(pred.loc[t]),
                predicted_lo_m_bg=float(lo[common.get_loc(t)]),
                predicted_hi_m_bg=float(hi[common.get_loc(t)]),
                residual_m=float(o.loc[t] - pred.loc[t])))
        result(f"{r.well} ({r.code})",
               f"NSE {m['NSE']:+.3f}  r {r_shape:+.3f}  "
               f"NSE(level removed) {nse_db:+.3f}  bias {m['Bias']:+.3f} m  "
               f"epoch shift {epoch_shift:+.3f} m  n {len(common)}")

    pw = pd.DataFrame(per_well)
    sr = pd.DataFrame(series_rows)
    sens = pd.DataFrame(sens_rows)

    phase(4, "Write outputs")
    pw.to_csv(OUT_PER_WELL, index=False); saved(OUT_PER_WELL.name)
    sr.to_csv(OUT_SERIES, index=False); saved(OUT_SERIES.name)
    sens.to_csv(OUT_SENSITIVITY, index=False); saved(OUT_SENSITIVITY.name)
    if not sr.empty:
        sr_plot = sr.copy()
        sr_plot["month"] = pd.PeriodIndex(sr_plot["month"], freq="M").to_timestamp()
        plot_hindcast(sr_plot, admitted, OUT_FIG); saved(OUT_FIG.name)


    phase(5, "Full-record hindcast")
    panel = open_ground_panel(md, loc, wells_clean)
    adm_panel = panel[panel["admitted"]]
    for r in panel[~panel["admitted"]].itertuples():
        note(f"{r.well} not in panel: {r.excluded_because}")
    result("panel wells", f"{len(adm_panel)} of {len(panel)} candidates")

    anomalies, modelled_modern = {}, {}
    for r in adm_panel.itertuples():
        betas = (r.beta_1_recharge, r.beta_2_atmospheric_draw, r.beta_3_drainage)
        h0 = equilibrium_depth(betas, p_mean, pet_mean)
        sim = full_hindcast_well(cl, betas, h0)
        ref = sim.loc[r.modern_first:r.modern_last]
        if ref.empty:
            note(f"{r.well}: modern span falls outside the climate record")
            continue
        modelled_modern[r.well] = float(ref.mean())
        anomalies[r.well] = sim - float(ref.mean())

    site = pd.DataFrame(columns=["month"])
    decadal = pd.DataFrame()
    epoch = pd.DataFrame()
    if anomalies:
        anom = pd.DataFrame(anomalies)
        site = pd.DataFrame({
            "month": anom.index,
            "site_anomaly_m": anom.mean(axis=1).values,
            "site_sd_m": anom.std(axis=1, ddof=1).values,
            "n_wells": anom.notna().sum(axis=1).values,
            "P_m": cl.loc[anom.index, "P_m"].values,
            "PET": cl.loc[anom.index, "PET"].values,
        })
        site["site_anomaly_smoothed_m"] = (
            site["site_anomaly_m"].rolling(SMOOTH_MONTHS, center=True,
                                           min_periods=SMOOTH_MONTHS).mean())

        dec = (anom.index.year // 10) * 10
        dw = anom.groupby(dec).mean().stack().reset_index()
        dw.columns = ["decade", "well", "mean_anomaly_m"]
        dw["scope"] = "well"
        ds = anom.mean(axis=1).groupby(dec).mean().reset_index()
        ds.columns = ["decade", "mean_anomaly_m"]
        ds["well"] = "SITE"
        ds["scope"] = "site"
        decadal = pd.concat([ds[["decade", "well", "scope", "mean_anomaly_m"]],
                             dw[["decade", "well", "scope", "mean_anomaly_m"]]],
                            ignore_index=True)

        rows = []
        for r in pw.itertuples():
            if r.well not in anom.columns:
                continue
            hind = anom[r.well].loc[first_month:last_month]
            if hind.empty:
                continue
            rows.append(dict(well=r.well, code=r.code,
                             observed_epoch_anomaly_m=r.epoch_shift_m,
                             hindcast_epoch_anomaly_m=float(hind.mean()),
                             modelled_modern_mean_m=modelled_modern[r.well],
                             observed_modern_mean_m=r.mean_modern_m))
        epoch = pd.DataFrame(rows)

    if not site.empty:
        site.to_csv(OUT_FULL_SITE, index=False); saved(OUT_FULL_SITE.name)
        decadal.to_csv(OUT_FULL_DECADAL, index=False); saved(OUT_FULL_DECADAL.name)
        plot_full_hindcast(site, epoch, first_month, last_month, OUT_FULL_FIG)
        saved(OUT_FULL_FIG.name)

    lines = [f"39_ccw_hindcast v{VERSION}",
             f"comparison window {first_month:%Y-%m} to {last_month:%Y-%m}",
             f"climate forcing from {cl.index.min():%Y-%m}",
             "",
             "Per well (beta_1 at its fitted value):"]
    for r in pw.itertuples():
        lines.append(f"  {r.well:<6} ({r.code})  NSE {r.nse:+.3f}  r {r.pearson_r:+.3f}  "
                     f"NSE with the level offset removed {r.nse_bias_removed:+.3f}  "
                     f"bias {r.bias_m:+.3f} m  RMSE {r.rmse_m:.3f} m  "
                     f"n {r.n_months}  censored dropped {r.n_censored}")
    lines += ["",
              "Read r against NSE. r is whether the hindcast reproduces the SHAPE",
              "of the record — the timing and size of the seasonal and interannual",
              "swing. NSE additionally penalises the LEVEL. A well with high r and",
              "poor NSE has the dynamics right and the datum wrong, which is a",
              "statement about the record rather than about the model."]
    if not pw.empty and pw.epoch_shift_m.notna().any():
        med = float(pw.epoch_shift_m.median())
        lines += ["",
                  "Epoch shift, each well's 1989-96 mean less its modern mean "
                  f"(network median {med:+.3f} m):"]
        for r in pw.itertuples():
            flag = ""
            if (pd.notna(r.epoch_shift_m) and med != 0
                    and np.sign(r.epoch_shift_m) != np.sign(med)):
                flag = ("   <-- opposite sign to the rest of the network: "
                        "check this well's datum and its code assignment")
            lines.append(f"  {r.well:<6} ({r.code})  {r.epoch_shift_m:+.3f} m{flag}")
    if not pw.empty:
        lines += ["",
                  f"mean residual (observed minus hindcast) across wells: "
                  f"{pw.residual_mean_m.mean():+.3f} m",
                  "  positive means the record sits SHALLOWER than the "
                  "climate-only hindcast",
                  f"largest initial-condition sensitivity over the window: "
                  f"{pw.h0_sensitivity_m.max():.2e} m — the spin-up has "
                  f"forgotten the starting value",
                  "",
                  "beta_1 sensitivity (the coefficients are fitted 2005-2026 and "
                  "the site-wide beta_1 decline means 1989 values were plausibly "
                  "higher):"]
        for sc, g in sens.groupby("beta1_scale"):
            og = g[g["in_forest"] == False]          # noqa: E712 — None must not match
            cg = g[g["in_forest"] == True]           # noqa: E712
            lines.append(
                f"  scale {sc:.2f}:  open ground (n={len(og)}) mean NSE "
                f"{og.nse.mean():+.3f}, mean bias {og.bias_m.mean():+.3f} m"
                f"   |  under canopy (n={len(cg)}) mean NSE {cg.nse.mean():+.3f}, "
                f"mean bias {cg.bias_m.mean():+.3f} m")
        lines += ["",
                  "The two groups are reported apart because the canopy state of "
                  "1989 is not observed and the coefficients are fitted over "
                  "2005-2026, which for the clearfell-zone wells spans the felling. "
                  "Transfer of a canopy well's coefficients to 1989 is therefore "
                  "an assumption the open-ground wells do not require."]
    lines += ["",
              "Codes not admitted:"]
    for r in adm[~adm["admitted"]].itertuples():
        lines.append(f"  {r.code:<3} {r.well or '(none)':<6} {r.excluded_because}")
    if not site.empty:
        lines += ["",
                  "Full-record hindcast (open-ground panel, modern coefficients "
                  "applied to the whole committed climate record):",
                  f"  panel {len(adm_panel)} wells of {len(panel)} candidates; "
                  f"forcing {cl.index.min():%Y-%m} to {cl.index.max():%Y-%m}",
                  "  each well is expressed as an anomaly against its own modelled "
                  "mean over its modern record span,",
                  "  so the curve is internally consistent and carries no "
                  "observed-to-modelled offset.",
                  "",
                  "  Decadal site anomaly (m):"]
        ds = decadal[decadal["scope"] == "site"]
        for r in ds.itertuples():
            lines.append(f"    {int(r.decade)}s  {r.mean_anomaly_m:+.3f}")
        if not epoch.empty:
            lines += ["",
                      "  Epoch check over the CCW window, each series against its "
                      "own modern mean:"]
            for r in epoch.itertuples():
                lines.append(f"    {r.well:<6} ({r.code})  observed "
                             f"{r.observed_epoch_anomaly_m:+.3f} m   hindcast "
                             f"{r.hindcast_epoch_anomaly_m:+.3f} m")
        lines += ["",
                  "  The coefficients are fitted 2005-2026 and are applied "
                  "unchanged across the whole record.",
                  "  This is the modern aquifer driven by historic climate, not a "
                  "reconstruction of the historic aquifer:",
                  "  the drainage coefficient encodes a drainage geometry that the "
                  "record cannot hold fixed."]
    OUT_TXT.write_text("\n".join(lines) + "\n")
    saved(OUT_TXT.name)

    done()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
