r"""

====================================================================================
10n — FOREST-NORMALISED SYNTHETIC CONTROL (difference-in-differences)
====================================================================================
Purpose
-------
Supplies the estimator that D-050 left the suite without.

WHAT WENT WRONG WITHOUT IT

  Script 10f builds a synthetic counterfactual for the Impact zone from a donor
  pool of six untreated wells and reports a step of +99.3 mm (p = 0.001). That
  figure was offered — in report9 §4.6.7, report10 §5.7 and the Methods
  Supplement S.7 — as an estimator that corroborates the clearfell headline
  without passing through the easting × time covariate.

  It does not corroborate it, because it does not estimate the same thing. The
  donor pool is

      ceh1 (C3), ceh5 (C1), ceh6 (C1), ceh10 (C2), ceh11 (C1), ceh24 (C2)

  and not one of the six is in C4 or C5. The counterfactual is therefore OPEN
  DUNE. The clearfell headline is estimated against the Forest control tier
  (ceh2, ceh32, ceh33, ceh34, nw10 — all C4), i.e. against UNFELLED FOREST. The
  difference between those two counterfactuals is the canopy, which is the whole
  reason the Forest tier exists. 10f's step is a gross step; the headline is a
  forest-normalised one. Agreement or disagreement between them carries no
  evidential weight.

  report9 §4.6.7 already says this — "they differ on how much survives
  normalization against the unfelled forest controls" — and then nobody
  performed the normalisation. This script performs it.

WHY NOT SIMPLY USE FOREST DONORS

  Because there are not enough. All fourteen C4/C5 wells in the network are
  already committed to the design: four in Edge (treated), five in Forest
  control, two in Coastal control. Three are uncommitted — ceh13, ceh14 and nw9
  — against a floor of three donors, and nw9 is one of the western coastal
  sinkers, so it would import the retreat signal into the counterfactual that
  exists to exclude it. The donor pool is not the fixable part.

THE ESTIMATOR

  Each zone gets its own synthetic from the SAME donor pool, and the two gaps
  are differenced:

      gap_z(t)  =  zone_mean_z(t)  −  Σ w_i,z · donor_i(t)
      Δ(t)      =  gap_Impact(t)   −  gap_ForestCtrl(t)
      step      =  mean(Δ | post-fell)  −  mean(Δ | scrape-to-fell)

  This is a difference-in-differences on synthetic counterfactuals. It touches
  easting nowhere, and it normalises against unfelled forest, so it answers the
  same question as the headline ANCOVA by a different route.

  DIFFERENCING THE SERIES, NOT THE STEPS. The two gaps are built from the same
  six donors and are strongly correlated, so a step-minus-step difference would
  need their covariance and a naive sum of variances would be wrong. Forming
  Δ(t) first and testing on it handles the correlation by construction.

  AUTOCORRELATION. Monthly water-table series are heavily autocorrelated, so the
  Welch t-test 10f uses on monthly values overstates significance. The step here
  is fitted as a regression of Δ(t) on a post-felling dummy with Newey–West HAC
  errors. The Welch p is reported beside it for comparability with 10f's rows,
  NOT as the inferential statement.

WHAT IT IS NOT

  Not Abadie's synthetic control. The donor weights are unrestricted OLS on
  levels with no intercept — they may be negative and need not sum to one — and
  that is 10f's construction, kept deliberately so the two are comparable. It is
  a donor-regression counterfactual.

PLACEBOS

  A DiD earns its keep from falsification, so two are run:

    in-space  Climate Ctrl − Forest Ctrl. Neither tier was felled, so a
              felling-dated step here is a fault in the estimator.
    in-time   the same Impact − Forest Ctrl contrast with the intervention
              moved to a date inside the pre-felling record. A step here means
              the estimator responds to the window, not the intervention.

  Far-field Ctrl is NOT usable as a placebo: ceh5 and ceh6 are in both that tier
  and the donor pool (deliberately — see 10f v1.2.0), so the contrast would
  regress a tier partly on itself. The script detects the overlap rather than
  trusting this comment, and refuses any contrast that has it.

Outputs
-------
CSV:
  10n_01_zone_gaps.csv          — per-zone synthetic gap steps (the inputs)
  10n_02_did_contrasts.csv      — the DiD contrasts, HAC and Welch
  10n_03_placebo.csv            — in-space and in-time falsification
  10n_04_pretrend.csv           — parallel-trends test and the trend-adjusted step
  10n_report_numbers.csv        — citable values

References
----------
Hollingham (2026), §4.6.7. D-050; report9 §4.6.7; Script 10f.
====================================================================================
"""

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-24.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as sp_stats

from utils.console_utils import banner, phase, skipped
from utils.paths import make_all_dirs, OUT_10F_SYNTH_CTRL
from utils.clearfell_common import (
    load_clearfell_data, print_network_summary, INTERVENTION_DATE,
    SCRAPING_DATE, CORE_NETWORK_WELLS, ReportNumbers,
)

# The donor pool and its exclusions are 10f's, read from 10f's own module so
# the two cannot drift apart. Duplicating the list here is how the pool and the
# analysis that reads it end up disagreeing after one of them is edited.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "_r10f", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                           "10f_robustness.py"))
# NOTE: 10f executes nothing at import time (its work is under main()), so this
# is a safe read of the constant rather than a run of the script.
_r10f = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_r10f)
SYNTH_DONOR_CANDIDATES = _r10f.SYNTH_DONOR_CANDIDATES
EXCLUDED_WELLS = _r10f.EXCLUDED_WELLS

OUTDIR = OUT_10F_SYNTH_CTRL.parent
OUT_ZONE_GAPS = OUTDIR / "10n_01_zone_gaps.csv"
OUT_DID = OUTDIR / "10n_02_did_contrasts.csv"
OUT_PLACEBO = OUTDIR / "10n_03_placebo.csv"
OUT_TREND = OUTDIR / "10n_04_pretrend.csv"
OUT_REPORT = OUTDIR / "10n_report_numbers.csv"

MIN_BASELINE_MONTHS = 24
MIN_WINDOW_MONTHS = 6


def _p_fmt(p):
    if pd.isna(p):
        return "N/A"
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def _p_sig(p):
    if pd.isna(p):
        return ""
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"


def _nw_maxlags(n):
    """Newey–West automatic bandwidth, floor(4 (n/100)^(2/9))."""
    return max(1, int(np.floor(4 * (n / 100.0) ** (2.0 / 9.0))))


# ============================================================================
# ZONE SYNTHETICS
# ============================================================================

def donor_pool(wells):
    network_set = set(CORE_NETWORK_WELLS) | set(EXCLUDED_WELLS)
    donors = [w for w in SYNTH_DONOR_CANDIDATES
              if w in wells.columns and w not in network_set]
    return donors


def zone_gap(wells, donors, zone_wells, fit_end=SCRAPING_DATE):
    """Synthetic gap series for one zone.

    Returns (gap_series, diagnostics) or (None, reason).
    """
    avail = [w for w in zone_wells if w in wells.columns]
    if not avail:
        return None, "no wells available"

    overlap = sorted(set(avail) & set(donors))
    if overlap:
        # A tier that is partly its own donor pool would be regressed on
        # itself. Refuse rather than report a number that cannot mean anything.
        return None, f"tier shares wells with the donor pool: {', '.join(overlap)}"

    donor_data = wells[donors].dropna()
    zone_mean = wells[avail].mean(axis=1).dropna()
    common_idx = zone_mean.index.intersection(donor_data.index)
    baseline_idx = common_idx[common_idx < fit_end]
    if len(baseline_idx) < MIN_BASELINE_MONTHS:
        return None, f"insufficient baseline ({len(baseline_idx)} months)"

    X = donor_data.loc[baseline_idx].values
    y = zone_mean.loc[baseline_idx].values
    try:
        ols = sm.OLS(y, X).fit()
    except Exception as exc:                                # pragma: no cover
        return None, f"OLS failed: {exc}"

    synthetic = donor_data.loc[common_idx].values @ ols.params
    gap = pd.Series(zone_mean.loc[common_idx].values - synthetic, index=common_idx)
    diag = {
        "n_wells": len(avail),
        "wells": " ".join(avail),
        "baseline_months": len(baseline_idx),
        "baseline_R2": float(ols.rsquared),
        "baseline_rmse_m": float(np.sqrt(np.mean(ols.resid ** 2))),
    }
    return gap, diag


def pretrend(series, pre_start, pre_end):
    """Slope of the contrast series BEFORE the intervention.

    A difference-in-differences is identified by parallel pre-trends. If the two
    zones were already diverging, a step measured as post-mean minus pre-mean is
    partly the continuation of that divergence, and reporting it as a level
    shift attributes to the intervention something that was under way without
    it. This is the assumption the estimator rests on, so it is tested rather
    than asserted.
    """
    pre = series[(series.index >= pre_start) & (series.index < pre_end)].dropna()
    if len(pre) < 3 * MIN_WINDOW_MONTHS:
        return None, f"pre-period too short ({len(pre)} months)"
    t = (pre.index - pre.index[0]).days.values / 365.25
    fit = sm.OLS(pre.values, sm.add_constant(t)).fit(
        cov_type="HAC", cov_kwds={"maxlags": _nw_maxlags(len(pre)),
                                  "use_correction": True})
    return {"pre_months": len(pre),
            "slope_m_yr": float(fit.params[1]),
            "se_hac_m_yr": float(fit.bse[1]),
            "p_hac": float(fit.pvalues[1])}, None


def step_net_of_trend(series, pre_start, post_start):
    """The step estimated as a discontinuity on top of a common linear trend.

    Where `step_on` compares two window means, this fits

        Δ(t) = a + b·t + c·1[t ≥ fell] + ε

    so c is the jump at the felling date net of whatever linear divergence runs
    through both windows. If c and the window-mean step disagree, the difference
    is the pre-trend, and c is the one to believe.
    """
    s = series[series.index >= pre_start].dropna()
    if len(s) < 4 * MIN_WINDOW_MONTHS:
        return None, f"series too short ({len(s)} months)"
    t = (s.index - s.index[0]).days.values / 365.25
    d = np.asarray(s.index >= post_start, dtype=float)
    fit = sm.OLS(s.values, sm.add_constant(np.column_stack([t, d]))).fit(
        cov_type="HAC", cov_kwds={"maxlags": _nw_maxlags(len(s)),
                                  "use_correction": True})
    step, se = float(fit.params[2]), float(fit.bse[2])
    return {"n_months": len(s),
            "trend_m_yr": float(fit.params[1]),
            "trend_p": float(fit.pvalues[1]),
            "step_m": step, "se_hac_m": se,
            "ci_lo_m": step - 1.96 * se, "ci_hi_m": step + 1.96 * se,
            "p_hac": float(fit.pvalues[2])}, None


def step_on(series, pre_start, pre_end, post_start, post_end=None):
    """Level shift in `series` between two windows, HAC and Welch.

    The HAC fit is the inferential statement; Welch is reported for
    comparability with 10f, which uses it on monthly values.
    """
    pre = series[(series.index >= pre_start) & (series.index < pre_end)]
    post = series[series.index >= post_start]
    if post_end is not None:
        post = post[post.index < post_end]
    if len(pre) < MIN_WINDOW_MONTHS or len(post) < MIN_WINDOW_MONTHS:
        return None, f"windows too short (pre={len(pre)}, post={len(post)})"

    y = np.concatenate([pre.values, post.values])
    d = np.concatenate([np.zeros(len(pre)), np.ones(len(post))])
    X = sm.add_constant(d)
    n = len(y)
    L = _nw_maxlags(n)
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": True})
    _t, p_welch = sp_stats.ttest_ind(post.values, pre.values, equal_var=False)

    step = float(fit.params[1])
    se = float(fit.bse[1])
    return {
        "pre_months": len(pre),
        "post_months": len(post),
        "pre_mean_m": float(pre.mean()),
        "post_mean_m": float(post.mean()),
        "step_m": step,
        "se_hac_m": se,
        "ci_lo_m": step - 1.96 * se,
        "ci_hi_m": step + 1.96 * se,
        "p_hac": float(fit.pvalues[1]),
        "p_welch": float(p_welch),
        "nw_maxlags": L,
    }, None


# ============================================================================
# MAIN
# ============================================================================

def main():
    make_all_dirs()
    banner("10n", "FOREST-NORMALISED SYNTHETIC CONTROL (DiD)", version=__version__)

    phase(1, "Loading data")
    wells, _prov, _climate, _master, _loc, valid_tiers = load_clearfell_data()
    print_network_summary(valid_tiers)

    rpt = ReportNumbers()
    donors = donor_pool(wells)
    print(f"\n   Donor pool: {', '.join(w.upper() for w in donors)} (n={len(donors)})")
    if len(donors) < 3:
        skipped("Fewer than 3 donors — nothing to build")
        return 1

    # ── Zone synthetics ─────────────────────────────────────────────────────
    phase(2, "Zone synthetics from the shared donor pool")
    gaps, gap_rows = {}, []
    for zone in ("Impact", "Edge", "Forest Ctrl", "Climate Ctrl",
                 "Coastal Ctrl", "Far-field Ctrl"):
        g, diag = zone_gap(wells, donors, valid_tiers.get(zone, []))
        if g is None:
            print(f"   {zone:16} REFUSED — {diag}")
            gap_rows.append({"Zone": zone, "Status": f"refused: {diag}"})
            continue
        gaps[zone] = g
        st, why = step_on(g, SCRAPING_DATE, INTERVENTION_DATE, INTERVENTION_DATE)
        row = {"Zone": zone, "Status": "ok", **diag}
        if st:
            row.update({"gross_step_m": st["step_m"],
                        "gross_p_hac": st["p_hac"],
                        "gross_p_welch": st["p_welch"]})
            print(f"   {zone:16} n={diag['n_wells']} baseline R²={diag['baseline_R2']:.3f} "
                  f"gross step={st['step_m']*1000:+7.1f} mm  "
                  f"p_HAC={_p_fmt(st['p_hac'])}")
        gap_rows.append(row)
    pd.DataFrame(gap_rows).to_csv(OUT_ZONE_GAPS, index=False)
    print(f"\n   -> {OUT_ZONE_GAPS.name}")

    # ── The DiD contrasts ───────────────────────────────────────────────────
    phase(3, "Forest-normalised contrasts")
    CONTRASTS = [("Impact", "Forest Ctrl"), ("Edge", "Forest Ctrl")]
    did_rows = []
    for treat, ctrl in CONTRASTS:
        if treat not in gaps or ctrl not in gaps:
            print(f"   {treat} − {ctrl}: unavailable")
            continue
        delta = (gaps[treat] - gaps[ctrl]).dropna()
        st, why = step_on(delta, SCRAPING_DATE, INTERVENTION_DATE, INTERVENTION_DATE)
        if st is None:
            print(f"   {treat} − {ctrl}: {why}")
            continue
        did_rows.append({"Contrast": f"{treat} - {ctrl}", "Basis": "scrape-to-fell vs post-fell",
                         **st})
        print(f"   {treat:12} − {ctrl:12}  step={st['step_m']*1000:+7.1f} mm  "
              f"95% CI [{st['ci_lo_m']*1000:+.1f}, {st['ci_hi_m']*1000:+.1f}]  "
              f"p_HAC={_p_fmt(st['p_hac'])} {_p_sig(st['p_hac'])}  "
              f"(p_Welch={_p_fmt(st['p_welch'])})")
        key = treat.replace(" ", "")
        rpt.add(f"SynthDiD_{key}_step", st["step_m"], "m",
                note=f"vs Forest Ctrl, HAC p={_p_fmt(st['p_hac'])}, "
                     f"maxlags={st['nw_maxlags']}")
        rpt.add(f"SynthDiD_{key}_se", st["se_hac_m"], "m",
                note="Newey-West HAC")

        # sensitivity: full pre-felling record as the reference window
        st2, _ = step_on(delta, delta.index.min(), INTERVENTION_DATE, INTERVENTION_DATE)
        if st2:
            did_rows.append({"Contrast": f"{treat} - {ctrl}",
                             "Basis": "all pre-fell vs post-fell",
                             **st2})
            print(f"   {'':12}   {'(all pre-fell)':12}  step={st2['step_m']*1000:+7.1f} mm  "
                  f"p_HAC={_p_fmt(st2['p_hac'])}")
    pd.DataFrame(did_rows).to_csv(OUT_DID, index=False)
    print(f"\n   -> {OUT_DID.name}")

    # ── The identifying assumption, tested ──────────────────────────────────
    phase(4, "Parallel pre-trends, and the step net of any trend")
    trend_rows = []
    for treat, ctrl in CONTRASTS:
        if treat not in gaps or ctrl not in gaps:
            continue
        delta = (gaps[treat] - gaps[ctrl]).dropna()
        label = f"{treat} - {ctrl}"

        # The pre-felling record spans the April 2015 scrape, and this
        # estimator carries no scraping term (10a's ANCOVA does). A divergence
        # measured across the scrape could therefore be the scrape rather than
        # a trend, so it is measured on both sides of that question: over the
        # whole pre-felling record, and over the post-scrape part of it alone.
        for span, start, note in (
                ("pre-trend (all pre-fell)", delta.index.min(),
                 "spans the April 2015 scrape"),
                ("pre-trend (post-scrape only)", SCRAPING_DATE,
                 "scrape excluded; short window")):
            pt, why = pretrend(delta, start, INTERVENTION_DATE)
            if pt is None:
                print(f"   {label:26} {span}: {why}")
                continue
            verdict = ("PARALLEL TRENDS FAIL" if pt["p_hac"] < 0.05
                       else "no significant pre-trend")
            print(f"   {label:26} {span:30} {pt['slope_m_yr']*1000:+7.1f} mm/yr  "
                  f"p_HAC={_p_fmt(pt['p_hac'])}  -> {verdict}")
            trend_rows.append({"Contrast": label, "Test": span, "Note": note,
                               **pt, "Verdict": verdict})
            if span.startswith("pre-trend (all"):
                rpt.add(f"SynthDiD_{treat.replace(' ', '')}_pretrend",
                        pt["slope_m_yr"], "m/yr",
                        note=f"HAC p={_p_fmt(pt['p_hac'])}; {verdict}")

        sn, why = step_net_of_trend(delta, delta.index.min(), INTERVENTION_DATE)
        if sn is None:
            print(f"   {label}: trend-adjusted step {why}")
            continue
        print(f"   {label:26} step net of trend {sn['step_m']*1000:+7.1f} mm  "
              f"95% CI [{sn['ci_lo_m']*1000:+.1f}, {sn['ci_hi_m']*1000:+.1f}]  "
              f"p_HAC={_p_fmt(sn['p_hac'])} {_p_sig(sn['p_hac'])}")
        trend_rows.append({"Contrast": label, "Test": "step net of linear trend",
                           **sn})
        rpt.add(f"SynthDiD_{treat.replace(' ', '')}_step_detrended",
                sn["step_m"], "m",
                note=f"discontinuity net of a common linear trend, "
                     f"HAC p={_p_fmt(sn['p_hac'])}")
    pd.DataFrame(trend_rows).to_csv(OUT_TREND, index=False)
    print(f"\n   -> {OUT_TREND.name}")

    # ── Placebos ────────────────────────────────────────────────────────────
    phase(5, "Falsification")
    pl_rows = []

    # in-space: two untreated tiers
    for treat, ctrl in [("Climate Ctrl", "Forest Ctrl"), ("Coastal Ctrl", "Forest Ctrl")]:
        if treat not in gaps or ctrl not in gaps:
            print(f"   in-space {treat} − {ctrl}: unavailable")
            continue
        delta = (gaps[treat] - gaps[ctrl]).dropna()
        st, why = step_on(delta, SCRAPING_DATE, INTERVENTION_DATE, INTERVENTION_DATE)
        if st is None:
            continue
        pl_rows.append({"Placebo": "in-space", "Contrast": f"{treat} - {ctrl}",
                        "Pseudo_date": str(INTERVENTION_DATE.date()),
                        **st})
        print(f"   in-space  {treat:14} − {ctrl:12} step={st['step_m']*1000:+7.1f} mm  "
              f"p_HAC={_p_fmt(st['p_hac'])} {_p_sig(st['p_hac'])}")

    # in-time: move the intervention back inside the pre-felling record
    if "Impact" in gaps and "Forest Ctrl" in gaps:
        delta = (gaps["Impact"] - gaps["Forest Ctrl"]).dropna()
        pre_only = delta[delta.index < INTERVENTION_DATE]
        for frac, label in ((0.50, "midpoint"), (0.70, "70%")):
            if len(pre_only) < 4 * MIN_WINDOW_MONTHS:
                break
            cut = pre_only.index[int(len(pre_only) * frac)]
            st, why = step_on(pre_only, pre_only.index.min(), cut, cut)
            if st is None:
                print(f"   in-time   {label}: {why}")
                continue
            pl_rows.append({"Placebo": "in-time", "Contrast": "Impact - Forest Ctrl",
                            "Pseudo_date": str(pd.Timestamp(cut).date()),
                            **st})
            print(f"   in-time   pseudo-fell {pd.Timestamp(cut).date()}      "
                  f"step={st['step_m']*1000:+7.1f} mm  "
                  f"p_HAC={_p_fmt(st['p_hac'])} {_p_sig(st['p_hac'])}")

    pd.DataFrame(pl_rows).to_csv(OUT_PLACEBO, index=False)
    print(f"\n   -> {OUT_PLACEBO.name}")

    n = rpt.save(OUT_REPORT)
    print(f"   -> {OUT_REPORT.name} ({n} keys)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
