r"""
====================================================================================
09a — HIERARCHICAL PAIRED BACI ANALYSIS
====================================================================================
Purpose
-------
Core scraping analysis using a Hierarchical BACI design.
Tier 1: Evaluates Local Controls vs. the Regional Mean (proves Coastal Drain).
Tier 2: Evaluates Impact Wells vs. Local Controls (proves Pure Scraping Success).

Includes per-era SSM fitting for β₃ significance testing, and net benefit
calculation against a coastal benchmark (CEH21).

Outputs
-------
CSVs:
  09_scrape_01_full_parameters.csv    — per-well, per-era SSM coefficients
  09_scrape_02_beta3_significance.csv — β₃ isolated estimates with CIs
  09_scrape_03_baci_shifts.csv        — paired BACI step changes
  09_scrape_04_net_benefits.csv       — net benefits vs CEH21 benchmark
  09_scrape_04b_beta3_era_summary.csv — formatted β₃ era summary
  09_tier1_final_cusum.csv            — terminal CUSUM values for Tier 1
  09_scrape_09_monthly_step_trend.csv — monthly step / step+trend HAC fits
  09_scrape_10_detectability.csv      — the smallest step each record could see

Figures:
  09_scrape_05_tier1_background_drift.png — Tier 1 BACI + CUSUM
  09_scrape_06_tier2_scraping_signal.png  — Tier 2 BACI + CUSUM
  09_scrape_07_beta3_confidence.png       — β₃ CIs across eras
  09_scrape_report_numbers.csv            — all citable values for §4.5

References
----------
Hollingham (2026), §4.5.  Part of the Script 09 scraping analysis suite.
====================================================================================
"""

__version__ = "2.9.0"  # Hollingham (2026) — 2026-08-31. THE STEP NOW TRAVELS
#   WITH ITS OWN DETECTION FLOOR. 09_scrape_03's CEH21 / After_Scraping
#   contrast is nominally significant, sits below the smallest step this design
#   could reliably detect, and does not survive a linear trend that the
#   PRE-intervention window independently supports. The academic summary already
#   said as much in words; all three clauses were assertions, and the third was
#   quietly contradicted by this script's own committed output. They are now
#   measurements, emitted from the same script as the number they qualify -
#   because a caveat emitted elsewhere is how a number gets cited without it.
#
#   Three pairs in a registry (BACI_DETECT_PAIRS), so a fourth needs no code.
#   CEH36/CEH4 is in as a POSITIVE CONTROL, not as a result: it changes nothing
#   about the 2015 finding, and it is what makes the 2023 nulls readable as a
#   statement about those records rather than a property of the method.
#
#   THE ASSERTION THAT MAKES THE REST ADMISSIBLE: where the fitting window is
#   exactly the two named eras, the step-only HAC coefficient MUST reproduce
#   this script's own era contrast. It does, to 1e-12 m. That is what makes the
#   regression the SAME estimator rather than a different one landing nearby,
#   and it raises rather than warns. No rate is formed and no existing output
#   changes. New outputs 09_scrape_09 and 09_scrape_10. See D-103.
#
# v2.8.0  # Hollingham (2026) — 2026-08-29. CLEARFELL_DATE rename (T-17).
#   No value changes; verified by re-run against the 2026-08-29 pipeline outputs.
# v2.7.3  # Hollingham (2026) -- 2026-08-18. Store-time rounding removed (D-035): these values
#   are written to CSV at the precision they were computed, and rounding
#   happens where they are displayed. Three decimals is a display rule for
#   quantities of order one; applied at storage it costs a significant
#   figure on the small ones - beta_3 ~ 0.018, Sy ~ 0.31 - and the loss
#   compounds through every statistic taken afterwards.
#
# v2.7.2  # Hollingham (2026) — 2026-07-19
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.paths import (
    make_all_dirs,
    OUT_09_FULL_PARAMS, OUT_09_BETA3_SIG, OUT_09_BACI_SHIFTS,
    OUT_09_NET_BENEFITS, OUT_09_BETA3_ERA_SUMMARY,
    OUT_09_TIER1_DRIFT, OUT_09_TIER2_SIGNAL, OUT_09_BETA3_CI,
    OUT_09_REPORT_NUMBERS,
    OUT_09_TIER1_CUSUM,
    OUT_09_STEP_TREND, OUT_09_DETECTABILITY,
)
from utils.scraping_common import (
    REGIONAL_MEAN_START,
    WELL_ERAS, CLIMATE_CONTROLS,
    PAIRED_CONTROLS_MAP, TIER1_WELLS, TIER2_WELLS,
    ERA_COLORS, ERA_MARKERS, ERA_LINESTYLES,
    MPL_DEFAULTS, SUMMER_MONTHS,
    SCRAPING_DATE, CLEARFELL_DATE, SCRAPING_DATE_2,
    era_filter, load_scraping_data,
    format_p_value, significance_stars,
)
from utils.data_utils import calculate_cusum
from utils.config import (DRAINAGE_DATUM, HEADLINE_LAG,
                          DETECTABILITY_ALPHA, DETECTABILITY_POWER,
                          BACI_DETECT_MIN_ERA_MONTHS,
                          BACI_DETECT_HORIZON_YEARS)

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.api as sm
from scipy import stats as _sps
from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import bump_fig_fonts, bump_label_and_legend_fonts, render_figure



# ============================================================================
# THE STEP, AND THE SMALLEST STEP THIS RECORD COULD HAVE SEEN
# ============================================================================
# The registry. (impact, control, event date, window start, label, note).
# Data, not code: a fourth pair is a row. Dates come from scraping_common, never
# typed. `window_start = None` means the full paired record.
#
# CEH36/CEH4 IS A POSITIVE CONTROL, NOT A RESULT. It changes nothing about the
# 2015 finding and is not re-reported as one. Its job is to show the method
# firing on a record that has the length to support it, so the two 2023 nulls
# read as a statement about THOSE records rather than as a property of the
# procedure. Without it a reader cannot tell the two apart.
BACI_DETECT_PAIRS = [
    ("ceh21", "ceh22", SCRAPING_DATE_2, CLEARFELL_DATE,
     "CEH21 vs CEH22, 2023 re-scrape",
     "the coastal pair; the contrast this analysis exists to qualify"),
    ("ceh18", "ceh4", SCRAPING_DATE_2, CLEARFELL_DATE,
     "CEH18 vs CEH4, 2023 re-scrape",
     "the boundary pair; same event, independent control"),
    ("ceh36", "ceh4", SCRAPING_DATE, None,
     "CEH36 vs CEH4, 2015 scrape (positive control)",
     "POSITIVE CONTROL, not a result: a record long enough for the method to "
     "fire on, so the 2023 nulls are readable"),
]

# The era-contrast reproduction tolerance. Not a scientific parameter: the two
# quantities are the same arithmetic by construction (OLS on a single 0/1
# indicator returns the difference of group means exactly), so anything above
# float noise means the windows have stopped agreeing and the check has caught
# it. 1e-12 m is a picometre.
ERA_CONTRAST_TOL_M = 1e-12


def _hac_lags(n):
    """Newey-West lag truncation, the standard floor(4*(n/100)^(2/9)) rule.

    Written once and used by every fit here, so the step fit and the trend fit
    cannot silently disagree about how much autocorrelation they are allowing
    for - which would make their standard errors incomparable, and the
    detectability floor is a ratio of exactly those.
    """
    return int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))


def _era_contrast_for(wells, impact, control, event):
    """This script's own era contrast for the pair, and whether it is comparable.

    Returns (contrast_m, comparable, reason). The contrast is only the same
    quantity as the step-only coefficient when the fitting window is EXACTLY the
    union of the two named eras that meet at the event. For CEH21 and CEH18 it
    is: the window opens at CLEARFELL_DATE, which is the start of the era before
    the event, and the later era runs to the end of record. For CEH36 the window
    is the full record and the post side spans TWO eras (Pure_Scraping and
    Felling_Pulse), so the step-only coefficient is a different contrast from
    the committed Pure_Scraping one and must NOT be asserted equal to it. That
    is reported, not hidden, and it is why this returns a flag rather than a
    number alone.
    """
    eras = WELL_ERAS.get(impact)
    if not eras:
        return float("nan"), False, "no era definition for this well"
    names = list(eras.keys())
    d = (wells[impact] - wells[control]).dropna()
    idx = [i for i, nm in enumerate(names) if eras[nm][0] == event]
    if not idx:
        return float("nan"), False, "event is not an era boundary for this well"
    j = idx[0]
    prev_name, post_name = names[j - 1], names[j]
    prev_start, _ = eras[prev_name]
    _, post_end = eras[post_name]
    contrast = float(era_filter(d, *eras[post_name]).mean()
                     - era_filter(d, *eras[prev_name]).mean())
    # comparable only if the window is exactly these two eras and nothing else
    comparable = (post_end is None) and (j == len(names) - 1)
    reason = "" if comparable else (
        f"window spans more than {prev_name} and {post_name} "
        f"(the post side continues past this era), so the step-only "
        f"coefficient is a different contrast and is NOT asserted equal")
    return contrast, comparable, reason


def _mde_mm(se_step_m, phi, n_pre, n_post, extra_years):
    """Minimum detectable step, at DETECTABILITY_ALPHA / DETECTABILITY_POWER.

    The base is the FITTED standard error of the step in the step+trend model,
    so the residual scale, the HAC autocorrelation correction and the step/trend
    collinearity inflation are all MEASURED from the fit rather than assumed
    (D-089's rule, applied here). Extrapolating to a longer record then scales
    that base by the design factor alone:

        se  proportional to  sqrt( 1 / ( n_eff * p * (1 - p) ) )

    with n_eff = n(1-phi)/(1+phi) the autocorrelation-adjusted count and
    p = n_post/n the post-window share. The ratio of design factors is what is
    applied; everything else is held at its measured value.

    HOLDING THE INFLATION CONSTANT IS CONSERVATIVE, and deliberately so.
    Collinearity between the step and the trend EASES as the post-window grows,
    so the real future standard error falls faster than this says. The forward
    floors are therefore if anything pessimistic - they cannot make a record
    look better able to detect a step than it will be.
    """
    z = (_sps.norm.ppf(1.0 - DETECTABILITY_ALPHA / 2.0)
         + _sps.norm.ppf(DETECTABILITY_POWER))
    n_now = n_pre + n_post
    n_post2 = n_post + int(round(extra_years * 12))
    n_tot = n_pre + n_post2
    scale = (1.0 - phi) / (1.0 + phi)
    p_now, p_new = n_post / n_now, n_post2 / n_tot
    df_now = np.sqrt(1.0 / (n_now * scale * p_now * (1.0 - p_now)))
    df_new = np.sqrt(1.0 / (n_tot * scale * p_new * (1.0 - p_new)))
    return z * se_step_m * (df_new / df_now) * 1000.0, n_post2, n_tot * scale


def _monthly_step_trend(wells):
    """Per pair: step-only, step+trend, and the pre-window trend, HAC throughout.

    The series is the paired monthly difference (impact minus control) that this
    script already uses for its era means, restricted to the pair's window. The
    three fits answer three separate questions and are reported together because
    the second and third are what qualify the first:

        M1  d ~ 1 + post                  the step, on its own
        M2  d ~ 1 + years_since + post    the step, once a linear trend is
                                          allowed for
        M3  d[pre] ~ 1 + years_since      whether the PRE-intervention window
                                          supports such a trend on its own
                                          evidence, which is what admits M2

    A pair is WITHHELD WITH A REASON (D-085) rather than omitted: a missing row
    relies on the next reader noticing the absence, and this script's whole
    point is that a caveat has to travel with its number.
    """
    rows, det_rows = [], []
    for impact, control, event, wstart, label, pair_note in BACI_DETECT_PAIRS:
        withheld = []
        if impact not in wells.columns or control not in wells.columns:
            withheld.append(f"{impact} or {control} absent from the well frame")
            d = pd.Series(dtype=float)
        else:
            d = (wells[impact] - wells[control]).dropna()
            if wstart is not None:
                d = d[d.index >= wstart]
        post_mask = (d.index >= event) if len(d) else np.array([], dtype=bool)
        n_pre, n_post = int((~post_mask).sum()), int(post_mask.sum())
        if n_pre < BACI_DETECT_MIN_ERA_MONTHS:
            withheld.append(f"pre-window {n_pre} months is under "
                            f"{BACI_DETECT_MIN_ERA_MONTHS} — a step estimated "
                            f"from less than an annual cycle carries the "
                            f"seasonal cycle with it")
        if n_post < BACI_DETECT_MIN_ERA_MONTHS:
            withheld.append(f"post-window {n_post} months is under "
                            f"{BACI_DETECT_MIN_ERA_MONTHS} — as above")

        contrast, comparable, contrast_reason = (
            _era_contrast_for(wells, impact, control, event)
            if len(d) else (float("nan"), False, "no paired record"))

        row = {"pair": label, "impact_well": impact.upper(),
               "control_well": control.upper(),
               "event_date": pd.Timestamp(event).date().isoformat(),
               "window_start": ("full paired record" if wstart is None
                                else pd.Timestamp(wstart).date().isoformat()),
               "n_months": len(d), "n_pre": n_pre, "n_post": n_post,
               "note": pair_note}

        if withheld:
            row.update({"withheld": True,
                        "withheld_reason": "; ".join(withheld)})
            rows.append(row)
            warn(f"{label}: WITHHELD — {'; '.join(withheld)}")
            continue

        n = len(d)
        lags = _hac_lags(n)
        years_since = (d.index - pd.Timestamp(event)).days / 365.25
        post = post_mask.astype(float)

        X1 = sm.add_constant(pd.DataFrame({"post": post}, index=d.index))
        m1 = sm.OLS(d, X1).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
        X2 = sm.add_constant(pd.DataFrame({"years_since_event": years_since,
                                           "post": post}, index=d.index))
        m2 = sm.OLS(d, X2).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
        pre = d[~post_mask]
        Xp = sm.add_constant(pd.DataFrame(
            {"years_since_event": (pre.index - pd.Timestamp(event)).days / 365.25},
            index=pre.index))
        m3 = sm.OLS(pre, Xp).fit(cov_type="HAC",
                                 cov_kwds={"maxlags": _hac_lags(len(pre))})

        resid = np.asarray(m2.resid, dtype=float)
        phi = float(pd.Series(resid).autocorr(1))
        resid_sd = float(np.std(resid, ddof=len(m2.params)))

        # THE ASSERTION. Where the window is exactly the two named eras, OLS on
        # a single 0/1 indicator returns the difference of group means exactly,
        # so the step-only coefficient IS this script's era contrast. If that
        # ever stops holding, the two are no longer the same estimator and the
        # script must fail rather than emit a number that looks like a
        # restatement of the committed one and is not.
        step_only = float(m1.params["post"])
        if comparable:
            dev = abs(step_only - contrast)
            if dev > ERA_CONTRAST_TOL_M:
                raise RuntimeError(
                    f"{label}: the step-only coefficient {step_only:.12f} m does "
                    f"not reproduce this script's era contrast {contrast:.12f} m "
                    f"(differs by {dev:.3e} m > {ERA_CONTRAST_TOL_M:.0e}). The "
                    f"monthly fit is no longer the same estimator as the era "
                    f"means in {OUT_09_BACI_SHIFTS.name}; refusing to emit.")
            info(f"{label}: step-only reproduces the era contrast "
                 f"({step_only * 1000:+.4f} mm, |diff| {dev:.2e} m)")
        else:
            note(f"{label}: era contrast not comparable — {contrast_reason}")

        row.update({
            "withheld": False, "withheld_reason": "",
            "maxlags": lags, "resid_lag1_phi": phi, "resid_sd_m": resid_sd,
            "step_only_m": step_only,
            "step_only_se_m": float(m1.bse["post"]),
            "step_only_p": float(m1.pvalues["post"]),
            "step_with_trend_m": float(m2.params["post"]),
            "step_with_trend_se_m": float(m2.bse["post"]),
            "step_with_trend_p": float(m2.pvalues["post"]),
            "trend_m_per_yr": float(m2.params["years_since_event"]),
            "trend_se_m_per_yr": float(m2.bse["years_since_event"]),
            "trend_p": float(m2.pvalues["years_since_event"]),
            "pre_trend_m_per_yr": float(m3.params["years_since_event"]),
            "pre_trend_se_m_per_yr": float(m3.bse["years_since_event"]),
            "pre_trend_p": float(m3.pvalues["years_since_event"]),
            "era_contrast_m": contrast,
            "era_contrast_comparable": comparable,
            "era_contrast_check": ("reproduced to "
                                   f"{ERA_CONTRAST_TOL_M:.0e} m" if comparable
                                   else contrast_reason),
            "collinearity_inflation": float(m2.bse["post"] / m1.bse["post"]),
            "estimator": "paired monthly difference, OLS with Newey-West (HAC) errors",
        })
        rows.append(row)
        step(f"{label}: step {step_only*1000:+.1f} mm (p={m1.pvalues['post']:.4g}) "
             f"-> {m2.params['post']*1000:+.1f} mm with a trend "
             f"(p={m2.pvalues['post']:.4g}); pre-window trend "
             f"{m3.params['years_since_event']*1000:+.1f} mm/yr "
             f"(p={m3.pvalues['years_since_event']:.4g})")

        se2 = float(m2.bse["post"])
        for extra in BACI_DETECT_HORIZON_YEARS:
            mde, n_post2, n_eff = _mde_mm(se2, phi, n_pre, n_post, extra)
            observed = float(m2.params["post"]) * 1000.0
            det_rows.append({
                "pair": label, "impact_well": impact.upper(),
                "control_well": control.upper(),
                "extra_years": extra, "n_post": n_post2,
                "n_eff": n_eff, "mde_mm": mde,
                "observed_step_mm": observed,
                "observed_below_floor": bool(abs(observed) < mde),
                "note": ("smallest step distinguishable from zero at alpha="
                         f"{DETECTABILITY_ALPHA}, power={DETECTABILITY_POWER}; "
                         "observed_step_mm is the step+trend estimate, the same "
                         "model this floor is derived from. The step/trend "
                         "collinearity inflation is held at its measured value "
                         "as the record is extrapolated, which is CONSERVATIVE "
                         "— that collinearity eases as the post-window grows, "
                         "so the forward floors are if anything pessimistic"),
            })
        below = [r for r in det_rows if r["pair"] == label and r["extra_years"] == 0]
        if below:
            b = below[0]
            (warn if b["observed_below_floor"] else info)(
                f"    floor now {b['mde_mm']:.1f} mm against an observed "
                f"{b['observed_step_mm']:+.1f} mm — "
                f"{'BELOW the floor' if b['observed_below_floor'] else 'above the floor'}")
    return pd.DataFrame(rows), pd.DataFrame(det_rows)


# ============================================================================
# β₃ ERA SUMMARY EXPORT HELPER
# ============================================================================

def _export_beta3_era_summary(significance_results):
    """Format and export the β₃ era summary table for the main report."""
    df = pd.DataFrame(significance_results)
    if df.empty:
        return

    well_order = ["CEH36", "CEH4", "CEH18", "CEH21", "CEH22"]
    role_map = {
        "CEH36": "Impact (scraped)", "CEH4": "Control (paired)",
        "CEH18": "Impact (boundary)", "CEH21": "Impact (coastal)",
        "CEH22": "Control (coastal)",
    }
    era_order = {
        "1_Baseline": 1, "2_Pure_Scraping": 2, "2_Felling_Pulse": 2,
        "2_Coastal_Drawdown": 2, "3_Felling_Pulse": 3, "3_After_Scraping": 3,
    }

    df = df[df["Well"].isin(well_order)].copy()
    df["Role"] = df["Well"].map(role_map)
    df["Era_Label"] = (df["Era"].astype(str)
                       .str.split("_", n=1).str[1]
                       .str.replace("_", " ", regex=False))
    df["CI_95"] = df.apply(
        lambda r: f"[{r['Conf_Low']:.3f}, {r['Conf_High']:.3f}]", axis=1)
    df["p_value"] = df["P_Value"].apply(format_p_value)
    df["Sig"] = df["P_Value"].apply(significance_stars)
    df["beta_3"] = df["beta_3_drainage"].astype(float)
    df["well_rank"] = pd.Categorical(df["Well"], categories=well_order,
                                     ordered=True)
    df["era_rank"] = df["Era"].map(era_order).fillna(99)
    df = df.sort_values(["well_rank", "era_rank", "Era_Label"])

    out = df[["Well", "Role", "Era_Label", "beta_3", "CI_95",
              "p_value", "Sig"]].rename(columns={"Era_Label": "Era"})
    out.to_csv(OUT_09_BETA3_ERA_SUMMARY, index=False)


# ============================================================================
# MAIN
# ============================================================================

def main():
    make_all_dirs()
    plt.rcParams.update(MPL_DEFAULTS)

    banner("09a", "HIERARCHICAL PAIRED BACI ANALYSIS", version=__version__)

    # ── 1. Load data ──────────────────────────────────────────────────────
    phase(1, "Loading Climate and Well Data")
    wells, _wells_prov, climate = load_scraping_data()

    valid_controls = [w for w in CLIMATE_CONTROLS if w in wells.columns]
    control_mean_regional = wells[valid_controls].mean(axis=1)
    # Restrict to the fixed-composition window — pre-2009-02 the regional
    # mean was computed over fewer wells (NW5/6/7 only pre-2006-05;
    # +CEH9 from 2006-05; +WMC2 from 2009-02).  Mixing those compositions
    # introduces spurious step signal in BACI series that use this mean
    # as control.  See scraping_common.py REGIONAL_MEAN_START rationale.
    control_mean_regional = control_mean_regional.where(
        control_mean_regional.index >= REGIONAL_MEAN_START)

    # ── 2. Paired statistical analysis ────────────────────────────────────
    phase(2, "Running Master Statistical Analysis")
    full_params_results = []
    significance_results = []
    baci_results = []
    plot_data = {}

    pairings = dict(PAIRED_CONTROLS_MAP)
    pairings["ceh4"] = "Regional Mean"
    pairings["ceh22"] = "Regional Mean"

    for well, era_defs in WELL_ERAS.items():
        if well not in wells.columns:
            continue

        if well in pairings and pairings[well] in wells.columns:
            baseline = wells[pairings[well]]
            control_label = pairings[well].upper()
        else:
            baseline = control_mean_regional
            control_label = "Regional Mean"

        baci_series = (wells[well] - baseline).dropna()
        era_baci_means = {}

        df = (wells[well].to_frame(name="h")
              .join(climate[["P_m", "PET"]], how="inner"))
        df["P_m_lag1"] = df["P_m"].shift(HEADLINE_LAG)
        df["h_prev"] = df["h"].shift(1)
        df["Delta_h"] = df["h"] - df["h_prev"]
        df = df.dropna()

        df["h_disp_prev"] = DRAINAGE_DATUM + df["h_prev"]
        X_base = pd.DataFrame({
            "beta_1_recharge": df["P_m_lag1"],
            "beta_2_atmospheric_draw": -df["PET"],
            "beta_3_drainage": -df["h_disp_prev"],
        })
        res_base = sm.OLS(df["Delta_h"], X_base).fit()
        b1 = res_base.params["beta_1_recharge"]
        b2 = res_base.params["beta_2_atmospheric_draw"]
        df["Drainage_Component"] = (df["Delta_h"]
                                    - b1 * df["P_m_lag1"]
                                    - b2 * (-df["PET"]))
        df["neg_h_disp_prev"] = -df["h_disp_prev"]

        # CUSUM
        first_era_name = list(era_defs.keys())[0]
        start, end = era_defs[first_era_name]
        era1_baci = era_filter(baci_series, start, end)
        baseline_mean = era1_baci.mean() if not era1_baci.empty else 0
        cusum_series = calculate_cusum(baci_series, baseline_mean)

        plot_data[well] = {
            "df": df, "baci": baci_series, "cusum": cusum_series,
            "means": {}, "eras": era_defs, "control": control_label,
        }

        for era_name, (start, end) in era_defs.items():
            baci_sub = era_filter(baci_series, start, end)
            mean_val = baci_sub.mean() if not baci_sub.empty else np.nan
            era_baci_means[era_name] = mean_val
            plot_data[well]["means"][era_name] = mean_val

            sub = era_filter(df.iloc[:, 0], start, end)
            sub = df.loc[sub.index]
            if len(sub) > 6:
                X_full = pd.DataFrame({
                    "beta_1_recharge": sub["P_m_lag1"],
                    "beta_2_atmospheric_draw": -sub["PET"],
                    "beta_3_drainage": -sub["h_disp_prev"],
                })
                model_full = sm.OLS(sub["Delta_h"], X_full).fit()

                full_params_results.append({
                    "Well": well.upper(), "Era": era_name,
                    "beta_1_recharge": float(model_full.params["beta_1_recharge"]),
                    "beta_2_atmospheric_draw": float(model_full.params["beta_2_atmospheric_draw"]),
                    "beta_3_drainage": float(model_full.params["beta_3_drainage"]),
                })

                X_iso = sm.add_constant(sub["neg_h_disp_prev"])
                model_iso = sm.OLS(sub["Drainage_Component"], X_iso).fit()
                ci = model_iso.conf_int().loc["neg_h_disp_prev"]
                significance_results.append({
                    "Well": well.upper(), "Era": era_name,
                    "beta_3_drainage": model_iso.params["neg_h_disp_prev"],
                    "P_Value": model_iso.pvalues["neg_h_disp_prev"],
                    "Conf_Low": ci[0], "Conf_High": ci[1],
                })

        keys = list(era_baci_means.keys())
        for i in range(1, len(keys)):
            shift_name = keys[i].split("_", 1)[1]
            baci_results.append({
                "Well": well.upper(), "Shift": shift_name,
                "Delta_m": era_baci_means[keys[i]] - era_baci_means[keys[i-1]],
                "Control": control_label,
            })

    # Net benefits
    benchmark_well = "ceh21"
    impact_wells = ["ceh36", "ceh18"]
    net_summary = []
    if benchmark_well in plot_data:
        for w in impact_wells:
            if w in plot_data:
                relative_benefit = (plot_data[w]["baci"]
                                    - plot_data[benchmark_well]["baci"])
                era_keys = list(plot_data[w]["eras"].keys())
                for i in range(1, len(era_keys)):
                    _, end_prev = plot_data[w]["eras"][era_keys[i-1]]
                    start_cur, end_cur = plot_data[w]["eras"][era_keys[i]]
                    before = era_filter(relative_benefit,
                                        *plot_data[w]["eras"][era_keys[i-1]])
                    after = era_filter(relative_benefit, start_cur, end_cur)
                    net_summary.append({
                        "Well": w.upper(),
                        "Shift": era_keys[i].split("_", 1)[1],
                        "Net_Benefit_m": float(after.mean() - before.mean()),
                    })

    # ── 3. Export CSVs ────────────────────────────────────────────────────
    phase(3, "Exporting CSV files")
    pd.DataFrame(full_params_results).to_csv(OUT_09_FULL_PARAMS, index=False)
    pd.DataFrame(significance_results).to_csv(OUT_09_BETA3_SIG, index=False)
    pd.DataFrame(baci_results).to_csv(OUT_09_BACI_SHIFTS, index=False)
    pd.DataFrame(net_summary).to_csv(OUT_09_NET_BENEFITS, index=False)
    _export_beta3_era_summary(significance_results)

    # The step, with the trend it has to survive and the floor it has to clear.
    # Emitted here rather than from a new script: D-088 makes a new top-level
    # step a deliberate act and this does not earn one, both quantities fall out
    # of a fit this script is already doing, and a caveat emitted from somewhere
    # else is how a number gets cited without it.
    step_trend_df, detect_df = _monthly_step_trend(wells)
    step_trend_df.to_csv(OUT_09_STEP_TREND, index=False)
    saved(f"{OUT_09_STEP_TREND.name} ({len(step_trend_df)} pairs)")
    detect_df.to_csv(OUT_09_DETECTABILITY, index=False)
    saved(f"{OUT_09_DETECTABILITY.name} ({len(detect_df)} rows)")

    # Update site-wide observations registry — CEH36 BACI step values
    # are consumed downstream (09d) for scenario comparison.  See
    # utils/site_observations.py for the registered observation keys.
    from utils.site_observations import update_site_observation
    for row in baci_results:
        if row["Well"] == "CEH36" and row["Shift"] == "Pure_Scraping":
            update_site_observation("ceh36_baci_pure_scraping",
                                    row["Delta_m"], producer_script="09a")
        elif row["Well"] == "CEH36" and row["Shift"] == "Felling_Pulse":
            update_site_observation("ceh36_baci_felling_pulse",
                                    row["Delta_m"], producer_script="09a")

    # ── 4. Figures ────────────────────────────────────────────────────────
    phase(4, "Generating the Visual Suite")
    _plot_tier1(plot_data)
    _plot_tier2(plot_data)
    _plot_beta3_ci(significance_results)

    print("\n--- Absolute Paired-BACI Shifts ---")
    print(pd.DataFrame(baci_results).to_string(index=False))

    # ── 5. Report numbers ─────────────────────────────────────────────────
    print("\nExporting report numbers CSV...")
    _export_report_numbers(plot_data, baci_results, net_summary,
                           significance_results, wells,
                           step_trend_df, detect_df)

    print("\nDone.")


# ============================================================================
# FIGURE: TIER 1 — BACKGROUND DRIFT
# ============================================================================

def _plot_tier1(plot_data):
    """Tier 1: controls vs regional mean — BACI timelines + CUSUM."""
    all_baci = [plot_data[w]["baci"] for w in TIER1_WELLS if w in plot_data]
    all_cusum = [plot_data[w]["cusum"] for w in TIER1_WELLS if w in plot_data]

    if not all_baci:
        return

    baci_ylim = (min(s.min() for s in all_baci) - 0.05,
                 max(s.max() for s in all_baci) + 0.05)
    cusum_ylim = (min(s.min() for s in all_cusum) - 0.05,
                  max(s.max() for s in all_cusum) + 0.05) if all_cusum else (-0.5, 0.5)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=300)

    for i, well in enumerate(TIER1_WELLS):
        if well not in plot_data:
            continue
        data = plot_data[well]

        # Top row: BACI
        ax_baci = axes[0, i]
        ax_baci.axhline(0, color="black", lw=1.5, ls="-", alpha=0.3)
        for era_name, (start, end) in data["eras"].items():
            era_data = era_filter(data["baci"], start, end)
            if era_data.empty:
                continue
            ax_baci.plot(era_data.index, era_data, color=ERA_COLORS[era_name],
                         ls=ERA_LINESTYLES[era_name], alpha=0.8, lw=1.5)
            ax_baci.axhline(data["means"][era_name],
                            color=ERA_COLORS[era_name], ls="--", lw=2, alpha=0.9)
        ax_baci.set_ylim(baci_ylim)
        if i == 0:
            ax_baci.set_ylabel("Δ Water Level (m)\n[CEH WELL - Regional Mean]",
                               fontweight="bold")
        ax_baci.set_title(f"{well.upper()} Performance", fontsize=12, pad=10)
        ax_baci.grid(True, which="both", ls=":", alpha=0.4)

        # Bottom row: CUSUM
        ax_cusum = axes[1, i]
        ax_cusum.axhline(0, color="black", lw=1.5, ls="-", alpha=0.3)
        for era_name, (start, end) in data["eras"].items():
            era_cusum = era_filter(data["cusum"], start, end)
            if era_cusum.empty:
                continue
            ax_cusum.fill_between(era_cusum.index, era_cusum,
                                  color=ERA_COLORS[era_name], alpha=0.2)
            clean_label = era_name.split("_", 1)[1].replace("_", " ")
            ax_cusum.plot(era_cusum.index, era_cusum,
                          color=ERA_COLORS[era_name], lw=2.5,
                          marker=ERA_MARKERS[era_name], markevery=4,
                          label=clean_label)
        ax_cusum.set_ylim(cusum_ylim)
        if i == 0:
            ax_cusum.set_ylabel("Cumulative Sum (m)\n[Relative Success]",
                                fontweight="bold")
        ax_cusum.grid(True, which="both", ls=":", alpha=0.4)

    # Axis formatting
    min_date = pd.to_datetime("2006-01-01")
    max_date = max(plot_data[w]["baci"].index.max()
                   for w in TIER1_WELLS if w in plot_data)

    # Intervention markers: scrape epochs + clearfell. April-2015 covers CEH36
    # and Scrape A/B (same event); October-2023 covers CEH18/CEH21 (re-scrape).
    event_markers = [
        (SCRAPING_DATE,     "#1a4e80", "Apr 2015 scrape — CEH36, Scrape A, Scrape B"),
        (CLEARFELL_DATE, "#1b5e20", "Dec 2017 clearfell"),
        (SCRAPING_DATE_2,   "#7a3a8c", "Oct 2023 re-scrape — CEH18, CEH21"),
    ]
    for ax in axes.flatten():
        ax.set_xlim(min_date, max_date)
        for _d, _c, _ in event_markers:
            ax.axvline(_d, color=_c, ls="-.", lw=1.6, alpha=0.85, zorder=1.5)
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.setp(ax.get_xticklabels(), rotation=0)
    for ax in axes[0, :]:
        ax.set_xticklabels([])

    # Intervention-marker legend (top-left panel; era legend sits bottom-left)
    from matplotlib.lines import Line2D
    marker_handles = [Line2D([0], [0], color=_c, ls="-.", lw=1.6, label=_lbl)
                      for _d, _c, _lbl in event_markers]
    axes[0, 0].legend(handles=marker_handles, loc="upper left",
                      fontsize=8, frameon=True, framealpha=0.9,
                      title="Interventions", title_fontsize=8)

    # Legend
    handles, labels = [], []
    for ax in axes.flat:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
    clean_labels = [lbl.split("_", 1)[1].replace("_", " ")
                    if "_" in lbl else lbl for lbl in labels]
    by_label = dict(zip(clean_labels, handles))
    axes[1, 0].legend(by_label.values(), by_label.keys(),
                      loc="lower left", frameon=True)

    plt.tight_layout()
    fig.suptitle("Tier 1 - Background Environmental Drift (CUSUM Analysis)",
                 fontsize=16, fontweight="bold", y=1.05)
    bump_fig_fonts(plt.gcf(), 2.0)  # legibility reviews: all text +2 pt
    bump_label_and_legend_fonts(plt.gcf(), 1.0)  # review: labels+legend +1 more
    render_figure(plt.gcf(), OUT_09_TIER1_DRIFT)
    plt.close()

    # Export final CUSUM values
    cusum_final = {w: float(plot_data[w]["cusum"].iloc[-1])
                   for w in TIER1_WELLS if w in plot_data}
    pd.DataFrame.from_dict(cusum_final, orient="index",
                           columns=["Final_Tier1_CUSUM"]).to_csv(OUT_09_TIER1_CUSUM)
    saved(f"{OUT_09_TIER1_DRIFT.name}")


# ============================================================================
# FIGURE: TIER 2 — SCRAPING SIGNAL
# ============================================================================

def _plot_tier2(plot_data):
    """Tier 2: impacts vs paired controls — BACI + CUSUM."""
    all_baci = [plot_data[w]["baci"] for w in TIER2_WELLS if w in plot_data]
    all_cusum = [plot_data[w]["cusum"] for w in TIER2_WELLS if w in plot_data]

    if not all_baci:
        return

    baci_ylim = (min(s.min() for s in all_baci) - 0.05,
                 max(s.max() for s in all_baci) + 0.05)
    cusum_ylim = (min(s.min() for s in all_cusum) - 0.05,
                  max(s.max() for s in all_cusum) + 0.05) if all_cusum else (-0.5, 0.5)

    fig, axes = plt.subplots(3, 2, figsize=(14, 18), dpi=300)

    for i, well in enumerate(TIER2_WELLS):
        if well not in plot_data:
            continue
        data = plot_data[well]

        ax_baci = axes[i, 0]
        ax_baci.axhline(0, color="black", lw=1.5, ls="-", alpha=0.3)
        for era_name, (start, end) in data["eras"].items():
            era_data = era_filter(data["baci"], start, end)
            if era_data.empty:
                continue
            ax_baci.plot(era_data.index, era_data, color=ERA_COLORS[era_name],
                         ls=ERA_LINESTYLES[era_name], alpha=0.8, lw=1.5)
            ax_baci.axhline(data["means"][era_name],
                            color=ERA_COLORS[era_name], ls="--", lw=2, alpha=0.9)
        ax_baci.set_ylim(baci_ylim)
        ax_baci.set_ylabel("Δ Water Level (m)\n[CEH WELL - CEH4]",
                           fontweight="bold")
        ax_baci.set_title(f"{well.upper()} Performance", fontsize=12, pad=10)
        ax_baci.grid(True, which="both", ls=":", alpha=0.4)

        ax_cusum = axes[i, 1]
        ax_cusum.axhline(0, color="black", lw=1.5, ls="-", alpha=0.3)
        for era_name, (start, end) in data["eras"].items():
            era_cusum = era_filter(data["cusum"], start, end)
            if era_cusum.empty:
                continue
            ax_cusum.fill_between(era_cusum.index, era_cusum,
                                  color=ERA_COLORS[era_name], alpha=0.2)
            clean_label = era_name.split("_", 1)[1].replace("_", " ")
            ax_cusum.plot(era_cusum.index, era_cusum,
                          color=ERA_COLORS[era_name], lw=2.5,
                          marker=ERA_MARKERS[era_name], markevery=4,
                          label=clean_label)
        ax_cusum.set_ylim(cusum_ylim)
        ax_cusum.set_ylabel("Cumulative Sum (m)\n[Relative Success]",
                            fontweight="bold")
        ax_cusum.grid(True, which="both", ls=":", alpha=0.4)

    for ax in axes[1, :]:
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.setp(ax.get_xticklabels(), rotation=0)

    handles, labels = [], []
    for ax in axes.flat:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
    clean_labels = [lbl.split("_", 1)[1].replace("_", " ")
                    if "_" in lbl else lbl for lbl in labels]
    by_label = dict(zip(clean_labels, handles))
    axes[1, 0].legend(by_label.values(), by_label.keys(),
                      loc="upper left", frameon=True)

    # Intervention markers (scrape epochs + clearfell), same as Tier 1.
    # April 2015 covers CEH36 + Scrape A/B; October 2023 covers CEH18/CEH21.
    event_markers = [
        (SCRAPING_DATE,     "#1a4e80", "Apr 2015 scrape — CEH36, Scrape A, Scrape B"),
        (CLEARFELL_DATE, "#1b5e20", "Dec 2017 clearfell"),
        (SCRAPING_DATE_2,   "#7a3a8c", "Oct 2023 re-scrape — CEH18, CEH21"),
    ]
    for ax in axes.flatten():
        _xl = ax.get_xlim()
        for _d, _c, _ in event_markers:
            ax.axvline(_d, color=_c, ls="-.", lw=1.6, alpha=0.85, zorder=1.5)
        ax.set_xlim(_xl)
    from matplotlib.lines import Line2D
    _marker_handles = [Line2D([0], [0], color=_c, ls="-.", lw=1.6, label=_lbl)
                       for _d, _c, _lbl in event_markers]
    axes[0, 0].legend(handles=_marker_handles, loc="upper left",
                      fontsize=8, frameon=True, framealpha=0.9,
                      title="Interventions", title_fontsize=8)

    plt.tight_layout()
    fig.suptitle("Tier 2 - Pure Scraping Signal (Paired CUSUM Analysis)",
                 fontsize=16, fontweight="bold", y=1.05)
    render_figure(plt.gcf(), OUT_09_TIER2_SIGNAL)
    plt.close()
    saved(f"{OUT_09_TIER2_SIGNAL.name}")


# ============================================================================
# FIGURE: BETA-3 CONFIDENCE INTERVALS
# ============================================================================

def _plot_beta3_ci(significance_results):
    """β₃ confidence intervals across eras for impact wells."""
    df_sig = pd.DataFrame(significance_results)
    if df_sig.empty:
        return

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

    # Impact (scraped) wells, a gap, then the unscraped controls. β₃ is each
    # well's OWN drainage coefficient, so the two groups are directly comparable;
    # the controls are drawn faded on a shaded backdrop to read as the
    # counterfactual. CEH4 controls CEH36/CEH18; CEH22 controls CEH21.
    impact_set = {"CEH36", "CEH18", "CEH21"}
    well_x = {"CEH36": 0.0, "CEH18": 1.0, "CEH21": 2.0, "CEH4": 3.2, "CEH22": 4.2}
    plot_order = ["CEH36", "CEH18", "CEH21", "CEH4", "CEH22"]
    df_sig_filtered = df_sig[df_sig["Well"].isin(well_x)]
    present = set(df_sig_filtered["Well"])
    wells_plotted = [w for w in plot_order if w in present]
    offsets = [-0.15, 0, 0.15]

    era_order = {
        "1_Baseline": 0, "2_Pure_Scraping": 1, "2_Felling_Pulse": 1,
        "2_Coastal_Drawdown": 1, "3_Felling_Pulse": 2, "3_After_Scraping": 2,
    }

    fill_styles = dict(ERA_COLORS)
    fill_styles["1_Baseline"] = "none"

    # shaded backdrop + separator marking the control group
    ax.axvspan(2.6, 4.9, color="grey", alpha=0.08, zorder=0)
    ax.axvline(2.6, color="grey", ls=":", lw=1.2, alpha=0.7, zorder=1)

    eras_present = []
    for w in wells_plotted:
        well_data = df_sig_filtered[df_sig_filtered["Well"] == w]
        is_ctrl = w not in impact_set
        for j, (_, row) in enumerate(well_data.iterrows()):
            era = row["Era"]
            if era not in eras_present:
                eras_present.append(era)
            x_pos = well_x[w] + offsets[j]
            err_low = row["beta_3_drainage"] - row["Conf_Low"]
            err_high = row["Conf_High"] - row["beta_3_drainage"]
            ax.errorbar(
                x_pos, row["beta_3_drainage"],
                yerr=[[err_low], [err_high]],
                fmt=ERA_MARKERS[era], color=ERA_COLORS[era],
                markerfacecolor=fill_styles[era],
                markeredgecolor=ERA_COLORS[era],
                markersize=8, capsize=5,
                alpha=0.5 if is_ctrl else 1.0, zorder=3)

    ax.set_xticks([well_x[w] for w in wells_plotted])
    ax.set_xticklabels(wells_plotted)
    ax.set_xlim(-0.6, 4.9)
    ax.set_ylabel(r"Drainage Coefficient ($\beta_3$)")
    ax.set_title(r"Structural Repair ($\beta_3$ Shifts with 95% CI)" "\n"
                 + "impact (scraped) wells vs unscraped controls",
                 fontweight="bold")

    # group labels beneath the well names
    ax.annotate("Impact (scraped)", xy=(1.0, -0.12),
                xycoords=("data", "axes fraction"),
                ha="center", va="top", fontsize=10, fontweight="bold")
    ax.annotate("Controls (unscraped)", xy=(3.7, -0.12),
                xycoords=("data", "axes fraction"),
                ha="center", va="top", fontsize=10, fontweight="bold",
                color="#666")

    # era legend with full-colour swatches (sorted by era stage, deduped by label)
    from matplotlib.lines import Line2D
    eras_present.sort(key=lambda e: era_order.get(e, 99))
    legend_handles, _seen = [], set()
    for e in eras_present:
        lbl = e.split("_", 1)[1].replace("_", " ")
        if lbl in _seen:
            continue
        _seen.add(lbl)
        legend_handles.append(
            Line2D([0], [0], marker=ERA_MARKERS[e], color=ERA_COLORS[e],
                   markerfacecolor=fill_styles[e], markeredgecolor=ERA_COLORS[e],
                   linestyle="none", markersize=8, label=lbl))
    ax.legend(handles=legend_handles, title="Eras", loc="best")
    ax.grid(axis="y", ls="--", alpha=0.7)

    plt.tight_layout()
    render_figure(plt.gcf(), OUT_09_BETA3_CI)
    plt.close()
    saved(f"{OUT_09_BETA3_CI.name}")


# ============================================================================
# REPORT NUMBERS EXPORT
# ============================================================================

def _export_report_numbers(plot_data, baci_results, net_summary,
                           significance_results, wells,
                           step_trend_df=None, detect_df=None):
    """Export all citable values for §4.5."""
    rows = []

    def rr(parameter, value, unit="m", well="", era="", note=""):
        rows.append({
            "Parameter": parameter, "Well": well, "Era": era,
            "Value": float(value) if pd.notna(value) else "",
            "Unit": unit, "Note": note,
        })

    # 1. Tier 1 CUSUM terminal values
    for w in TIER1_WELLS:
        if w in plot_data:
            final_cusum = float(plot_data[w]["cusum"].iloc[-1])
            rr("Tier1_CUSUM_terminal", final_cusum, well=w.upper(),
               note="Final cumulative CUSUM vs Regional Mean")

    # 2. Tier 2 raw BACI shifts
    for br in baci_results:
        rr("Tier2_BACI_shift", br["Delta_m"],
           well=br["Well"], era=br["Shift"],
           note=f"vs {br['Control']}")

    # 3. Net benefits
    for nb in net_summary:
        rr("Net_benefit", nb["Net_Benefit_m"],
           well=nb["Well"], era=nb["Shift"],
           note="vs CEH21 coastal benchmark")

    # 4. β₃ era estimates (per well, per era)
    for sr in significance_results:
        rr("beta3_era", sr["beta_3_drainage"],
           well=sr["Well"], era=sr["Era"],
           note=f"CI=[{sr['Conf_Low']:.4f},{sr['Conf_High']:.4f}] "
                f"p={format_p_value(sr['P_Value'])}")

    # 5. Summer minimum depths by era
    for sw in ["ceh4", "ceh36"]:
        if sw not in wells.columns or sw not in WELL_ERAS:
            continue
        sw_series = wells[sw].dropna()
        for era_name, (start, end) in WELL_ERAS[sw].items():
            era_data = era_filter(sw_series, start, end)
            summer = era_data[era_data.index.month.isin(SUMMER_MONTHS)]
            if len(summer) >= 2:
                summer_min_depth = float(summer.min())
                rr("Summer_minimum_depth", summer_min_depth,
                   well=sw.upper(), era=era_name,
                   note="Mean of annual Jun-Sep minima")

    # 6. The step with its trend and its floor — beside the shift rows above,
    #    so a reader who finds Tier2_BACI_shift finds the qualification too.
    if step_trend_df is not None and len(step_trend_df):
        for _, sr in step_trend_df.iterrows():
            if sr.get("withheld", False):
                rr("BACI_step_withheld", np.nan, unit="",
                   well=sr["impact_well"], era=sr["pair"],
                   note=f"WITHHELD (D-085): {sr['withheld_reason']}")
                continue
            rr("BACI_step_with_trend", sr["step_with_trend_m"],
               well=sr["impact_well"], era=sr["pair"],
               note=f"step once a linear trend is allowed for; HAC se="
                    f"{sr['step_with_trend_se_m']:.6f} m, "
                    f"p={format_p_value(sr['step_with_trend_p'])}; "
                    f"step-only was {sr['step_only_m']:.6f} m "
                    f"(p={format_p_value(sr['step_only_p'])})")
            rr("BACI_pre_window_trend", sr["pre_trend_m_per_yr"], unit="m/yr",
               well=sr["impact_well"], era=sr["pair"],
               note=f"trend fitted on the PRE-intervention window ALONE, "
                    f"p={format_p_value(sr['pre_trend_p'])} — this is the "
                    f"evidence on which the step+trend model is admitted, not "
                    f"a preference for it")
    if detect_df is not None and len(detect_df):
        for _, dr in detect_df[detect_df["extra_years"] == 0].iterrows():
            rr("BACI_min_detectable_step", dr["mde_mm"], unit="mm",
               well=dr["impact_well"], era=dr["pair"],
               note=f"smallest step this record could distinguish from zero at "
                    f"alpha={DETECTABILITY_ALPHA}, power={DETECTABILITY_POWER}; "
                    f"the observed step+trend estimate "
                    f"{dr['observed_step_mm']:+.1f} mm lies "
                    f"{'BELOW' if dr['observed_below_floor'] else 'above'} it")
            rr("BACI_step_below_floor", 1.0 if dr["observed_below_floor"] else 0.0,
               unit="flag", well=dr["impact_well"], era=dr["pair"],
               note="1 = the observed step is smaller than the smallest step "
                    "this record could reliably detect")

    report_df = pd.DataFrame(rows)
    report_df.to_csv(OUT_09_REPORT_NUMBERS, index=False)
    saved(f"{OUT_09_REPORT_NUMBERS.name} ({len(rows)} rows)")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
