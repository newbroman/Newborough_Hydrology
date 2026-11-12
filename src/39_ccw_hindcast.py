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
discarding it (Model B since 1.7.0, Model A beside it as *_model_a columns), over an open-ground panel whose inclusion policy is declared in
open_ground_panel(). Each well is expressed as an anomaly against its OWN
modelled mean over its OWN modern record span, so the curve carries no
observed-to-modelled offset and no cross-well datum assumption.

This is the modern aquifer driven by historic climate, NOT a reconstruction of
the historic aquifer. The coefficients in 03_master_data.csv are fitted on
the last 100 months of each well's record (2017-11 to 2026-02, n = 75-100 per well)
-- NOT on 2005-2026, which this docstring claimed until 1.6.0 -- and are applied
unchanged throughout. Two further windows (pre-2018 and the whole record) are
refitted here and hindcast alongside, so the fitting window's effect is shown
rather than assumed; beta_3 in particular encodes a drainage geometry the
record cannot hold fixed across the span. Any caption must say so.

Model B is the forecaster (D-332, 1.7.0)
---------------------------------------
Since 2026-11-12 the headline hindcast, figure 39_04 and every report number are Model B: the
free-intercept form, Script 03's coefficients (03_16) run at the datum its intercept implies,
DRAINAGE_DATUM - alpha/beta_3. Its beta_3 is bounded below (config.MODEL_B_BETA3_MIN); a bound fit is
kept and counted; a well whose implied datum is not below ground has no Model B and is counted out.
Two fixed-floor forms are reported as tested alternatives: Model A at DRAINAGE_DATUM (the master
store; 39_01's unsuffixed columns, report keys *_model_a), and Model A at each well's depth to mean
high water (ground less Script 01b's tide_mhw_m; 39_02 predicted_mhw_m_bg, keys *_mhw). 39_10 sets
the three side by side per well, scoring dry months as Addendum 2 does. The full-record pass
(39_05-39_07) is Model B too, with Model A in *_model_a columns. Admission and the full-record
panel rest on Model B's coefficients, not Model A's.

Inputs (via utils.paths):
    CCW_DEPTHS        (data/ccw_1989_1996_depths.csv)     historic depths, tidy
    CCW_CODE_MAP      (data/ccw_1989_1996_code_map.csv)   code -> well + status
    INT_CLIMATE       (01_climate.csv)                    P_m, PET in m/month
    INT_MASTER_DATA   (03_master_data.csv)                per-well beta_1/2/3 (Model A)
    OUT_03_MODEL_B_PERSISTENCE (03_16)                    per-well Model B (alpha, beta_*)
    OUT_01B_REPORT_NUMBERS (tide_mhw_m)                   mean high water, the MHW form
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
    39_08_fit_window_scorecard.csv both forms (and A at MHW) by fitting window
    39_09_fit_windows.png          both forms, three fitting windows
    39_10_three_forms_per_well.csv A 3.7 m, A MHW and B per well, dry months scored
    39_results.txt                 console summary
"""

from __future__ import annotations

__version__ = "1.7.0"  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2a). Model B is the headline: every
#   report key keeps its name and now carries Model B (03_16, run at DRAINAGE_DATUM - alpha/beta_3), with Model A at
#   3.7 m beside it as <key>_model_a; B gets its own beta_1 envelope (same scalings; 39_02 predicted_b_lo/hi_m_bg,
#   39_03 *_model_b columns). Bounded beta_3 fits (model_utils 1.14.0) are kept, not dropped, and counted
#   (n_wells_model_b_bound_binds*); a well whose implied datum is not below ground is left out of B's headline and
#   counted (n_wells_model_b_excluded_datum*). Model A at each well's depth to mean high water (Addendum 2): 39_02
#   predicted_mhw_m_bg, the per-well three-form table 39_10 with dry months scored, keys *_mhw. 39_04 shows B only,
#   legend below the panels. 39_01 keeps its Model A columns (Script 50 reads them) and gains *_model_b.
#   Then, on the coordinator's ruling (D-332, Martin 2026-11-12): codes are admitted on Model B (usable_codes_b: 03_16
#   defined), not on Model A's beta_3 (set unchanged); the full-record pass 39_05-39_07 is Model B with Model A in
#   *_model_a columns (nothing outside this script reads them); A's columns are NaN where A cannot be run.
# 1.6.1  # Hollingham (2026) - 2026-11-10. Model B is looked up by the NORMALISED well name
# (utils.data_utils.normalize_well_name), as Script 50 already does. Script 03's 03_16 spells 21 wells in
# capitals (WMC2, L7, T41a...), the admitted-well names are lower case, so the case-sensitive lookup missed
# and wmc2 silently lost its Model B hindcast: the 1989-96 Model B median was over 8 wells, Model A's over 9.
# Martin 2026-11-10: "run the j9 fix here".
# 1.6.0 - 2026-11-08 (J-6). Both model forms refitted over
# three fitting windows (comparison / pre2018 / whole) and hindcast with each, after the figure
# caption was found to claim coefficients "fitted 2005-2026" when the master store it reads is
# the 100-month comparison window. Martin, 2026-11-08: "run both models against the ccw well
# data with the pre 2018 data" and "we should have a whole record trained model".
# 1.5.1  # Hollingham (2026) - 2026-10-01 (D-222). load_ccw, observed_series,
#   hindcast_well, equilibrium_depth and usable_codes moved unchanged to utils/hindcast_utils.py, so
#   Script 50 (record length) runs the same hindcast without a copy. Outputs identical.
# 1.5.0  # Hollingham (2026) - 2026-09-29. T-96 batch 2: write_report_numbers() emits
#   ccw_annual_range_vs_davy_2010_diff_m = config.CCW_ANNUAL_RANGE_DAVY_2010_M - ccw_annual_range_mean_m,
#   after ccw_annual_range_n (report9 SS4.13, the Davy et al. 2010 cross-check). Additive.
# 1.4.1  # Hollingham (2026) — 2026-09-28. T-91, per the signed-off spec
#   NRG_spec_T91_emits_2026-09-28: write_report_numbers() now also emits the
#   open-ground and under-canopy mean NSE (and open-ground mean bias) at each
#   beta_1 scaling in CCW_BETA1_SCALINGS, so the Methods Supplement's
#   sensitivity-to-beta_1 paragraph (Sensitivity to beta_1 section) binds to a
#   committed number instead of the (stale) typed table. Computed from `sens`,
#   already built by main() before this call; nothing else moves.
#

#   NRG_spec_script39_emits_T84_2026-09-26: a new 39_report_numbers.csv carries every
#   statistic report9 §4.14.1 and report10 §5.7.8 quote — the fit summary, the epoch
#   shift, the open-ground medians, the climate contrast over the two windows, the
#   Davy et al. (2010) annual-range cross-check (config.CCW_ANNUAL_RANGE_*), and the
#   midpoint gap with the straight-line division the text quotes only to disclaim.
#   Computed from the per-well table and series already in memory; nothing else moves.
#
# v1.3.0  # Hollingham (2026) — 2026-08-22.  Emits the
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

from utils.model_utils import (simulate_ssm, get_metrics,            # noqa: E402
                               fit_ssm, fit_ssm_intercept,           # noqa: E402  (J-6 pre-2018)
                               dry_bounds)                           # noqa: E402  (1.7.0, MHW form)
from utils.hindcast_utils import (load_ccw, observed_series, hindcast_well,
                                  equilibrium_depth, usable_codes, BETA_COLS)
from utils.console_utils import banner, phase, step, info, warn, saved, note, result, done
from utils.render_utils import render_figure
from utils.data_utils import normalize_well_name                # noqa: E402  (1.6.1)
from utils.report_numbers_utils import ReportNumbers

SCRIPT_ID = "39"
VERSION = __version__

PIPE_BASE_M = config.CCW_PIPE_BASE_M
BETA1_SCALINGS = config.CCW_BETA1_SCALINGS
H0_PROBE_OFFSETS_M = config.CCW_H0_PROBE_OFFSETS_M
DATUM = config.DRAINAGE_DATUM
# J-6: minimum aligned months for an alternative-window refit (below). Deliberately LOWER than
# the pipeline's usual MIN_OBS, because the pre-2018 window is short at some wells by construction
# and a well dropped for want of months is a well whose window comparison cannot be made at all.
# Three years is enough to see a seasonal cycle twice; the emitted n per window says which wells
# are thin, so a reader can discount them rather than having them silently excluded.
MIN_FIT_OBS = 36
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
OUT_REPORT_NUMBERS = paths.OUT_39_REPORT_NUMBERS
OUT_FIT_WINDOWS = paths.OUT_39_FIT_WINDOWS
OUT_FIT_WINDOW_FIG = paths.OUT_39_FIT_WINDOW_FIG
OUT_THREE_FORMS = paths.OUT_39_THREE_FORMS
B3_MIN = config.MODEL_B_BETA3_MIN
# 1.7.0 (D-332): the three forms of the 1989-96 hindcast, as the three-form table names them. B is the
# forecaster; the two fixed-floor forms are tested alternatives, reported under the key suffixes beside.
FORM_SUFFIX = {"B": "", "A_3.7": "_model_a", "A_MHW": "_mhw"}



# ── report numbers (1.4.0, T-84) ─────────────────────────────────────────────
# 1.7.0 (D-332): the per-well columns each model-dependent key is computed from. 39_01 keeps Model A
# in these names (Script 50's identity checks read them) and carries Model B beside them with the
# suffix _model_b; the report keys keep their names and now carry Model B, with Model A's value as
# the sensitivity key <name>_model_a.
MODEL_COLS = ("nse", "rmse_m", "bias_m", "pearson_r", "nse_bias_removed", "residual_mean_m",
              "mean_predicted_m")


def model_view(pw: pd.DataFrame, form: str) -> pd.DataFrame:
    """The per-well table with one form's metrics under the shared column names, restricted to the
    wells that form was run at. form "A" is the 39_01 columns as they stand; "B" the _model_b ones."""
    if pw.empty or form == "A":
        return pw.copy()
    v = pw.copy()
    for c in MODEL_COLS:
        v[c] = pw[f"{c}_model_b"]
    return v[v["nse"].notna()]


def _model_keys(rn, pw, sfx: str, label: str) -> None:
    """The model-dependent statistics §4.14.1 and §5.7.8 quote, for one form (sfx "" = Model B)."""
    op = pw[pw["in_forest"] == False]                       # noqa: E712
    pf = pw[(pw["in_forest"] == True) & (pw["canopy_1989"] == "forest")   # noqa: E712
            & (pw["canopy_changed_since_1989"] == False)]                   # noqa: E712
    rest = pw.drop(pf.index)
    rn.add(f"n_wells_admitted{sfx}", len(pw), unit="wells", note=f"wells hindcast against the CCW record, {label}")
    rn.add(f"n_open{sfx}", len(op), unit="wells", note=f"open ground (in_forest False), {label}")
    rn.add(f"pearson_r_median{sfx}", pw["pearson_r"].median(), unit="", note=f"observed vs predicted, all wells, {label}")
    rn.add(f"pearson_r_min{sfx}", pw["pearson_r"].min(), unit="", note=f"all wells, {label}")
    rn.add(f"pearson_r_max{sfx}", pw["pearson_r"].max(), unit="", note=f"all wells, {label}")
    rn.add(f"n_nse_negative{sfx}", int((pw["nse"] < 0).sum()), unit="wells", note=f"Nash-Sutcliffe below zero, {label}")
    rn.add(f"nse_median{sfx}", pw["nse"].median(), unit="",
           note=f"median per-well NSE over 1989-96 (the 'skill' of Scenario 2), {label}")
    rn.add(f"bias_median_m{sfx}", pw["bias_m"].median(), unit="m",
           note=f"median per-well level bias, predicted less observed (+ = modelled too wet), {label}")
    rn.add(f"nse_bias_removed_min_excl_persistent_forest{sfx}", rest["nse_bias_removed"].min(), unit="",
           note=f"bias-removed NSE, wells other than the one under forest in both epochs, {label}")
    rn.add(f"nse_bias_removed_max_excl_persistent_forest{sfx}", rest["nse_bias_removed"].max(), unit="",
           note=f"as above, {label}")
    for r in pf.itertuples():
        rn.add(f"nse_bias_removed_persistent_forest{sfx}", r.nse_bias_removed, unit="",
               well=str(r.well).upper(), note=f"the well under forest in both epochs, {label}")
    rn.add(f"residual_mean_all{sfx}", pw["residual_mean_m"].mean(), note=f"observed less predicted, mean over wells, {label}")
    rn.add(f"residual_mean_open{sfx}", op["residual_mean_m"].mean(), note=f"as above, open ground, {label}")
    rn.add(f"open_pearson_r_median{sfx}", op["pearson_r"].median(), unit="", note=f"open ground, {label}")
    rn.add(f"open_nse_bias_removed_median{sfx}", op["nse_bias_removed"].median(), unit="", note=f"open ground, {label}")


def write_report_numbers(pw, sr, cl, wells_clean, first_month, last_month, sens, tf=None, extra=None):
    """The statistics §4.14.1 and §5.7.8 quote, as committed cells.

    Open ground is in_forest False, the split the β₁-sensitivity block uses; the
    persistent-forest well is under canopy in 1989 and now, with no change since.

    1.7.0 (D-332): the model-dependent keys carry Model B (the forecaster) under their existing
    names; Model A at the 3.7 m floor follows as <key>_model_a, and the mean-high-water form's
    Scenario 2 numbers as <key>_mhw. tf is the three-form table (dry months scored); extra the
    counts main() gathered (bound binds, wells without a defined Model B, the MHW level used).
    """
    rn = ReportNumbers()
    if pw.empty:
        rn.save(OUT_REPORT_NUMBERS); saved(OUT_REPORT_NUMBERS.name); return
    _model_keys(rn, model_view(pw, "B"), "", "Model B (the forecaster, D-332)")
    _model_keys(rn, model_view(pw, "A"), "_model_a",
                f"Model A at the fixed {DATUM:g} m floor (tested alternative, D-332)")
    rn.add("epoch_shift_min", pw["epoch_shift_m"].max(), note="smallest shift (1989-96 mean less modern mean)")
    rn.add("epoch_shift_max", pw["epoch_shift_m"].min(), note="largest shift")
    rn.add("epoch_shift_median", pw["epoch_shift_m"].median(), note="all wells")
    op = pw[pw["in_forest"] == False]                       # noqa: E712  (observation-only keys below)
    rn.add("open_epoch_shift_median", op["epoch_shift_m"].median(), note="open ground")

    # 1.7.0 (D-332): Model B's definition at these wells, and the three-form table (Addendum 2)
    for k, (v, unit, note_) in (extra or {}).items():
        rn.add(k, v, unit=unit, note=note_)
    if tf is not None and not tf.empty:
        lab = {"B": "Model B", "A_3.7": f"Model A at {DATUM:g} m", "A_MHW": "Model A at mean high water"}
        for form, sfx in FORM_SUFFIX.items():
            g = tf[(tf["form"] == form) & tf["nse"].notna()]
            if form == "A_MHW":       # B's and A 3.7's medians are emitted from 39_01 above
                rn.add("n_wells_admitted_mhw", len(g), unit="wells",
                       note="wells hindcast with Model A at each well's depth to mean high water")
                rn.add("nse_median_mhw", g["nse"].median(), unit="",
                       note="median per-well NSE over 1989-96, Model A at mean high water (Scenario 2)")
                rn.add("bias_median_m_mhw", g["bias_m"].median(), unit="m",
                       note="median per-well level bias, predicted less observed, Model A at mean high water")
                rn.add("datum_mhw_min_m", g["datum_m"].min(), unit="m",
                       note="shallowest floor of the mean-high-water form at these wells (ground less tide_mhw_m)")
                rn.add("datum_mhw_max_m", g["datum_m"].max(), unit="m", note="deepest such floor")
            rn.add(f"rmse_with_dry_median_m{sfx}", g["rmse_with_dry_m"].median(), unit="m",
                   note=f"median typical monthly error, dry months counted only where the run sits above "
                        f"the pipe base (Addendum 2), {lab[form]}")
            rn.add(f"n_wells_best_with_dry{sfx}", int((tf.drop_duplicates("well")["best_form_with_dry"] == form).sum()),
                   unit="wells", note=f"wells at which {lab[form]} has the lowest error counting dry months")

    # the climate contrast between the CCW window and the modern well record
    def _means(a, b):
        c = cl.loc[(cl.index >= a) & (cl.index <= b)]
        return (float(c["P_m"].mean() * 12), float((c["P_m"] - c["PET"]).mean() * 12))
    m0, m1 = wells_clean.index.min(), wells_clean.index.max()
    for tag, (a, b) in (("window", (first_month, last_month)), ("modern", (m0, m1))):
        p, s_ = _means(a, b)
        rn.add(f"rain_mean_{tag}_m_yr", p, unit="m/yr",
               note=f"mean annual rainfall {a:%Y-%m} to {b:%Y-%m}")
        rn.add(f"surplus_mean_{tag}_m_yr", s_, unit="m/yr",
               note=f"mean annual P - PET {a:%Y-%m} to {b:%Y-%m}")

    # the published cross-check (Davy et al. 2010, 1989-95 annual range)
    y0, y1 = config.CCW_ANNUAL_RANGE_YEARS
    s2 = sr.assign(year=sr["month"].str[:4].astype(int))
    s2 = s2[(s2["year"] >= y0) & (s2["year"] <= y1)]
    g = s2.groupby(["well", "year"])["observed_m_bg"].agg(["max", "min", "count"])
    g = g[g["count"] >= config.CCW_ANNUAL_RANGE_MIN_MONTHS]
    rng = g["max"] - g["min"]
    rn.add("ccw_annual_range_mean_m", rng.mean(),
           note=f"per-well calendar-year range {y0}-{y1}, well-years with "
                f">= {config.CCW_ANNUAL_RANGE_MIN_MONTHS} readings")
    rn.add("ccw_annual_range_sd_m", rng.std(), note="as above")
    rn.add("ccw_annual_range_n", len(rng), unit="well-years", note="as above")
    rn.add("ccw_annual_range_vs_davy_2010_diff_m", config.CCW_ANNUAL_RANGE_DAVY_2010_M - rng.mean(),
           note=f"CCW_ANNUAL_RANGE_DAVY_2010_M ({config.CCW_ANNUAL_RANGE_DAVY_2010_M:g} m, Davy et al. 2010; "
                f"SD {config.CCW_ANNUAL_RANGE_DAVY_2010_SD_M:g} m) minus ccw_annual_range_mean_m")

    # the straight-line division report10 §5.7.8 quotes only to reject it
    mid_w = first_month + (last_month - first_month) / 2
    mid_m = m0 + (m1 - m0) / 2
    gap = (mid_m - mid_w).days / 365.25
    rn.add("epoch_midpoint_gap_yr", gap, unit="yr", note="years between the two records' midpoints")
    rn.add("epoch_rate_if_linear_mm_yr", -op["epoch_shift_m"].median() * 1000 / gap, unit="mm/yr",
           note="NOT a rate: the open-ground median shift divided by the midpoint gap, "
                "quoted in the text only to be disclaimed")

    # the beta_1 sensitivity table (T-91): open-ground and under-canopy mean NSE,
    # and open-ground mean bias, at each committed scaling in CCW_BETA1_SCALINGS.
    # `sens` is the per-well/per-scale table main() already built; grouped here,
    # not re-derived from a written CSV. 1.7.0 (D-332): Model B under the existing keys, Model A
    # as _model_a.
    for sc in sorted(sens["beta1_scale"].unique()):
        ssub = sens[sens["beta1_scale"] == sc]
        tag = f"{sc:.2f}"
        for sfx, csfx, lab in (("", "_model_b", "Model B"), ("_model_a", "", f"Model A at {DATUM:g} m")):
            s_f = ssub[ssub[f"nse{csfx}"].notna()]
            op_s = s_f[s_f["in_forest"] == False]                        # noqa: E712
            cf_s = s_f[s_f["in_forest"] == True]                         # noqa: E712
            rn.add(f"open_nse_mean_beta1_scale_{tag}{sfx}", op_s[f"nse{csfx}"].mean(), unit="",
                   era=f"beta1 scale {tag}",
                   note=f"{lab}: open-ground (in_forest False, n={len(op_s)}) mean NSE "
                        f"with beta_1 scaled by {tag} (fitted value at scale 1.00)")
            rn.add(f"open_bias_mean_beta1_scale_{tag}{sfx}", op_s[f"bias_m{csfx}"].mean(), unit="m",
                   era=f"beta1 scale {tag}",
                   note=f"{lab}: open-ground mean bias (predicted less observed, per "
                        f"get_metrics) with beta_1 scaled by {tag}")
            rn.add(f"canopy_nse_mean_beta1_scale_{tag}{sfx}", cf_s[f"nse{csfx}"].mean(), unit="",
                   era=f"beta1 scale {tag}",
                   note=f"{lab}: under-canopy (in_forest True, n={len(cf_s)}) mean NSE "
                        f"with beta_1 scaled by {tag}")

    n = rn.save(OUT_REPORT_NUMBERS)
    saved(f"{OUT_REPORT_NUMBERS.name} ({n} report numbers)")


# ── data ──────────────────────────────────────────────────────────────────────
def load_inputs():
    """Historic depths, the code map, climate, coefficients and elevations."""
    obs, cmap = load_ccw()

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


def modern_mean(wells_clean: pd.DataFrame, well: str) -> float:
    """Mean modern level for one well, for the epoch-shift diagnostic."""
    col = {c.lower().strip(): c for c in wells_clean.columns}.get(well)
    if col is None:
        return np.nan
    s = pd.to_numeric(wells_clean[col], errors="coerce").dropna()
    return float(s.mean()) if len(s) else np.nan


def load_model_b():
    """Model B per well from Script 03's 03_16 (the comparison window): {well: (betas, datum)} run at
    DRAINAGE_DATUM - alpha/beta_3, the wells with no datum below ground {well: datum}, and the wells
    whose beta_3 sits at config.MODEL_B_BETA3_MIN. Keys are normalised well names.

    1.7.0 (D-332): Model B is the forecaster and the headline. A bounded fit is kept; a well whose
    implied datum is not below ground has no Model B (ceh14, -9.39 m, measured 2026-11-07)."""
    mb, mb_undef, mb_binds = {}, {}, set()
    try:
        _mb = pd.read_csv(paths.OUT_03_MODEL_B_PERSISTENCE)
    except OSError as e:
        warn(f"Model B coefficients unavailable ({type(e).__name__}); nothing is admitted")
        return mb, mb_undef, mb_binds
    for _, _r in _mb[_mb["level"] == "well"].iterrows():
        _k = normalize_well_name(_r["well"])
        _b3 = float(_r["beta_3_B"])
        if (str(_r.get("beta_3_bound_binds", "")).strip().lower() in ("true", "1", "1.0")
                or (np.isfinite(_b3) and _b3 <= B3_MIN * (1 + 1e-9))):
            mb_binds.add(_k)
        _d = (float(_r["drainage_datum_m"]) - float(_r["alpha_B"]) / _b3
              if np.isfinite(_b3) and _b3 > 0 else np.nan)
        if not (np.isfinite(_d) and _d > 0):
            mb_undef[_k] = _d
            continue
        mb[_k] = ((float(_r["beta_1_B"]), float(_r["beta_2_B"]), _b3), _d)
    note(f"Model B coefficients for {len(mb)} well(s); {len(mb_binds)} with beta_3 at the bound; "
         f"undefined (datum not below ground) at {len(mb_undef)}: "
         + (", ".join(f"{k} ({v:+.2f} m)" for k, v in mb_undef.items()) or "none"))
    return mb, mb_undef, mb_binds


def usable_codes_b(cmap: pd.DataFrame, mb: dict, mb_undef: dict, obs: pd.DataFrame) -> pd.DataFrame:
    """Codes admissible to the headline, on MODEL B (1.7.0, D-332): confirmed mapping and a well with
    a defined Model B (03_16, implied datum below ground). The same rules, order and censoring test
    as hindcast_utils.usable_codes, which judges Model A's triple and stays as it is for Script 50.
    Everything else is reported, never pooled."""
    rows = []
    for r in cmap.itertuples():
        why = ""
        k = normalize_well_name(r.well) if isinstance(r.well, str) and r.well else ""
        if r.status != "confirmed":
            why = f"mapping {r.status}"
        elif not r.well:
            why = "no well"
        elif k in mb_undef:
            why = f"Model B not defined (implied datum {mb_undef[k]:+.2f} m, not below ground)"
        elif k not in mb:
            why = "no committed coefficients"
        n_c = int(obs.loc[obs["code"] == r.code, "censored_at_pipe_base"].sum())
        n_t = int((obs["code"] == r.code).sum())
        if not why and n_t and n_c / n_t > config.CCW_MAX_CENSORED_FRACTION:
            why = f"censored in {n_c} of {n_t} months"
        rows.append(dict(code=r.code, well=r.well, status=r.status,
                         datum_offset_m=r.datum_offset_m,
                         n_months=n_t, n_censored=n_c,
                         admitted=(why == ""), excluded_because=why))
    return pd.DataFrame(rows)


def model_a_ok(md: pd.DataFrame, well: str) -> bool:
    """Model A (the 3.7 m alternative) can be run at this well: a complete master-store triple with
    beta_3 > 0. Admission no longer depends on it (1.7.0); where it fails, A's columns are NaN."""
    return bool(well in md.index and all(np.isfinite(float(md.loc[well, c])) for c in BETA_COLS)
                and float(md.loc[well, BETA_COLS[2]]) > 0)


def shape_scores(oc: np.ndarray, pc: np.ndarray) -> tuple:
    """Pearson r between observed and predicted, and the NSE with the mean offset removed: the two
    diagnostics that separate a wrong LEVEL from wrong DYNAMICS (0.2.0; a helper since 1.7.0, so
    both forms are scored by the same lines)."""
    if len(oc) <= 2 or not (np.isfinite(oc).all() and np.isfinite(pc).all()):
        return np.nan, np.nan
    r_shape = float(stats.pearsonr(oc, pc).statistic)
    off = float(np.mean(pc - oc))
    denom = float(np.sum((oc - oc.mean()) ** 2))
    nse_db = (1.0 - float(np.sum((oc - (pc - off)) ** 2)) / denom
              if denom > 0 else np.nan)
    return r_shape, nse_db


def mhw_level() -> float:
    """Mean high water (m OD), Script 01b's tide_mhw_m, read as Scripts 48 (mhw_datums) and 50
    (_e16_mhw) read it. NaN when absent: the mean-high-water form is then skipped, not invented."""
    try:
        rn = pd.read_csv(paths.OUT_01B_REPORT_NUMBERS)
        v = rn.loc[rn["Parameter"] == "tide_mhw_m", "Value"]
        return float(v.iloc[0]) if len(v) else np.nan
    except (OSError, KeyError, ValueError):
        return np.nan


def fixed_floor_fit(h: pd.Series, cl: pd.DataFrame, col: str, datum: float):
    """Model A at a given fixed floor, fitted as Script 03 fits the master store and as Script 50's
    E16 fits the mean-high-water form (D-322): dry months censored at the well's dry bounds, the
    last LCSC_DATA_LIMIT calendar months. None where the fit fails."""
    db = dry_bounds(col)
    db = db if (db is not None and len(db)) else None
    try:
        return fit_ssm(h, cl, lag=config.HEADLINE_LAG, window=config.LCSC_DATA_LIMIT,
                       drainage_datum=float(datum), min_obs=config.RECLEN_MIN_FIT_MONTHS,
                       intercept=False, dry_bound=db)
    except Exception as e:                                       # noqa: BLE001
        warn(f"{col}: fixed-floor fit at {datum:.2f} m failed ({type(e).__name__}: {e})")
        return None


def three_form_scores(obs: pd.DataFrame, code: str, offset_m: float, preds: dict) -> list:
    """Each form against every month the code was read, dry months included (Addendum 2).

    A reading held at the pipe base is a lower bound, not a level: a run that sits BELOW the pipe
    base that month agrees with it, and one that sits ABOVE it is wrong by the difference. So read
    months score the full error, and dry months only the part of the run above the pipe base.
    NSE and bias are over the read months alone, as 39_01 scores them.
    """
    g = obs[obs["code"] == code].sort_values("month")
    off = offset_m if np.isfinite(offset_m) else 0.0
    lvl = pd.Series(g["depth_m_bg"].values + off, index=g["month"].values)
    cen = pd.Series(g["censored_at_pipe_base"].astype(bool).values, index=g["month"].values)
    rows = []
    for form, p in preds.items():
        if p is None:
            rows.append(dict(form=form, n_read=int((~cen).sum()), n_dry=int(cen.sum())))
            continue
        c = lvl.index.intersection(p.index)
        e = p.loc[c] - lvl.loc[c]
        cc = cen.loc[c].values
        e_read, e_dry = e[~cc], e[cc].clip(lower=0)
        nse, _rm, bias = get_metrics(lvl.loc[c][~cc], p.loc[c][~cc])
        allerr = pd.concat([e_read, e_dry])
        rows.append(dict(form=form, n_read=int(len(e_read)), n_dry=int(len(e_dry)),
                         nse=float(nse), bias_m=float(bias),
                         rmse_read_m=float(np.sqrt((e_read ** 2).mean())),
                         n_dry_run_above_pipe_base=int((e_dry > 0).sum()),
                         dry_miss_mean_m=float(e_dry.mean()) if len(e_dry) else np.nan,
                         rmse_with_dry_m=float(np.sqrt((allerr ** 2).mean()))))
    return rows


# ── figure ────────────────────────────────────────────────────────────────────
def plot_hindcast(series: pd.DataFrame, adm: pd.DataFrame, fig_path) -> None:
    """The headline 1989-96 hindcast: Model B (the forecaster, D-332) with its beta_1 range.

    1.7.0 (D-332, brief Phase 2 "Legends off the data"): Model A's line leaves this figure -- it
    is a tested alternative, drawn with B in 39_09 and tabled in 39_10 -- and the legend moves
    below the panels (Martin 2026-11-08: "the legend obscures the plots"; in the first panel it
    covered nw11's 1994-95 rise).
    """
    wells = list(dict.fromkeys(series["well"]))
    if not wells:
        return
    ncol = 2
    nrow = int(np.ceil(len(wells) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(9.0, 2.2 * nrow + 0.5), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    for ax, w in zip(axes, wells):
        g = series[series["well"] == w]
        ax.plot(g["month"], g["observed_m_bg"], "o-", ms=3, lw=1.0,
                label="observed (CCW)", color="#1b1b1b")
        has_b = "predicted_b_m_bg" in g and g["predicted_b_m_bg"].notna().any()
        if has_b:
            ax.fill_between(g["month"], g["predicted_b_lo_m_bg"], g["predicted_b_hi_m_bg"],
                            color="#2b6cb0", alpha=0.20, lw=0,
                            label=r"Model B, $\beta_1$ range")
            ax.plot(g["month"], g["predicted_b_m_bg"], "-", lw=1.4,
                    label="Model B", color="#2b6cb0")
        row = adm[adm["well"] == w]
        code = row["code"].iloc[0] if len(row) else "?"
        ax.set_title(f"{w} (CCW {code})" + ("" if has_b else " \u2014 Model B not defined here"),
                     fontsize=10, loc="left")
        ax.axhline(PIPE_BASE_M, color="#777777", lw=0.8, ls=":")
        ax.set_ylabel("m below ground", fontsize=9)
        ax.tick_params(labelsize=9)
    for ax in axes[len(wells):]:
        ax.set_visible(False)
    _h, _l = [], []
    for ax in axes[:len(wells)]:                 # the first panel with every series supplies the legend
        hh, ll = ax.get_legend_handles_labels()
        if len(ll) > len(_l):
            _h, _l = hh, ll
    fig.legend(_h, _l, loc="lower center", ncol=3, fontsize=9, frameon=False,
               bbox_to_anchor=(0.5, 0.0))
    fig.suptitle("SSM hindcast against the 1989\u201396 CCW record: Model B (fitted intercept), "
                 "coefficients fitted on the\nlast 100 months of each well\u2019s record "
                 "(2017\u201311 to 2026\u201302) \u2014 its intercept is a MODERN-RECORD quantity "
                 "applied to a drier decade",
                 fontsize=9)
    fig.tight_layout(rect=(0, 0.4 / fig.get_size_inches()[1], 1, 1))
    render_figure(fig, fig_path)
    plt.close(fig)


def plot_fit_windows(series: pd.DataFrame, adm: pd.DataFrame, fw: pd.DataFrame,
                     fig_path) -> None:
    """Both model forms against the 1989-96 record, from each of three fitting windows.

    J-6, Martin 2026-11-08. Two columns -- Model A (fixed datum) and Model B (fitted
    intercept) -- so the window spread within a form can be read against the gap between
    the forms. The question is which of the two matters more, and the figure answers it
    by putting them on the same axes rather than in two separate figures.

    None of the three windows contains 1989-96: the dipwells did not exist then. The
    windows differ in how far from that decade they sit and in how wet they were.
    """
    wells = list(dict.fromkeys(series["well"]))
    if not wells:
        return
    WINCOL = {"comparison": ("#D95F02", "-"),      # the window this script has always used
              "pre2018":    ("#1b9e77", "--"),     # nearer 1989-96 in time, drier
              "whole":      ("#7570b3", "-.")}     # largest n
    COLS = {("comparison", "A"): "predicted_m_bg",
            ("pre2018", "A"): "predicted_a_pre2018_m_bg",
            ("whole", "A"): "predicted_a_whole_m_bg",
            ("comparison", "B"): "predicted_b_m_bg",
            ("pre2018", "B"): "predicted_b_pre2018_m_bg",
            ("whole", "B"): "predicted_b_whole_m_bg"}
    nrow = len(wells)
    fig, axes = plt.subplots(nrow, 2, figsize=(10.0, 2.0 * nrow),
                             sharex=True, sharey="row", squeeze=False)
    for i, w in enumerate(wells):
        g = series[series["well"] == w]
        row = adm[adm["well"] == w]
        code = row["code"].iloc[0] if len(row) else "?"
        for j, form in enumerate(("A", "B")):
            ax = axes[i][j]
            ax.plot(g["month"], g["observed_m_bg"], "o-", ms=2.5, lw=1.0,
                    label="observed", color="#1b1b1b", zorder=5)
            for win, (c, ls) in WINCOL.items():
                col = COLS.get((win, form))
                if col not in g or not g[col].notna().any():
                    continue
                ax.plot(g["month"], g[col], ls, lw=1.3, alpha=0.92, color=c, label=win)
            ax.axhline(PIPE_BASE_M, color="#777777", lw=0.8, ls=":")
            ax.tick_params(labelsize=9)
            # per-well NSE by window, in the legend's order: short enough to stay at 9 pt and
            # it is the number a reader wants beside the lines. r, bias, RMSE and n are in the
            # scorecard CSV -- putting them in the legend is what tripped the legibility
            # warning on the first attempt, at 6.5 pt authored and ~4 pt placed.
            nses = []
            for win in WINCOL:
                sc = fw[(fw["scope"] == "well") & (fw["well"] == w)
                        & (fw["fit_window"] == win) & (fw["model"] == form)]
                nses.append("n/a" if sc.empty else f"{sc['nse'].iloc[0]:+.2f}")
            ax.set_title(f"{w} (CCW {code}) — Model {form}   NSE " + " / ".join(nses),
                         fontsize=9, loc="left")
            if j == 0:
                ax.set_ylabel("m below ground", fontsize=9)
            # no per-axes legend: one figure-level legend below the suptitle instead, so it
            # cannot sit on top of the data (it did, over nw11, on the first attempt)
    pooled = {}
    for form in ("A", "B"):
        bits = []
        for win in WINCOL:
            r = fw[(fw["scope"] == "pooled") & (fw["fit_window"] == win)
                   & (fw["model"] == form)]
            if not r.empty:
                bits.append(f"{win} NSE {r['nse'].iloc[0]:+.2f} / bias {r['bias_m'].iloc[0]:+.2f} m")
        pooled[form] = "; ".join(bits) if bits else "not scored"
    fig.suptitle(
        "Does the fitting window change the 1989–96 hindcast? Both forms, three windows\n"
        "panel NSE is quoted comparison / pre2018 / whole, the legend’s order\n"
        f"pooled over all paired months — Model A: {pooled['A']}\n"
        f"Model B: {pooled['B']}",
        fontsize=9)
    # Reserve room at the top for the four-line suptitle AND the shared legend. The fraction
    # has to scale with the figure height or the title lands on the first row of panel
    # titles, which is what it did before this was computed rather than guessed.
    _top = 1.0 - (1.05 / fig.get_size_inches()[1])
    fig.tight_layout(rect=[0, 0, 1, _top])
    fig.legend(*axes[0][0].get_legend_handles_labels(), loc="upper center",
               bbox_to_anchor=(0.5, _top + 0.012), ncol=4, fontsize=9, framealpha=0.85)
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
                      wells_clean: pd.DataFrame, mb: dict | None = None,
                      mb_undef: dict | None = None) -> pd.DataFrame:
    """Wells admitted to the full-record panel, with the reason for each refusal.

    The inclusion policy is declared in one place rather than left implicit in a
    filter chain. A well enters when three conditions hold: it is not under
    canopy on the committed land-cover flag; it carries a defined Model B (1.7.0,
    D-332: 03_16, implied datum below ground; until 1.7.0 a Model A triple with a
    positive drainage coefficient); and its modern record reaches
    config.FULL_HINDCAST_MIN_MODERN_MONTHS, which is the baseline the anomaly is
    measured against. Wells failing any condition are returned with the reason
    recorded, never silently dropped. admitted_model_a says whether the Model A
    alternative can also be run there (its master-store triple, beta_3 > 0).
    """
    mb = mb or {}
    mb_undef = mb_undef or {}
    rows = []
    for well in sorted(set(loc.index) & ({normalize_well_name(w) for w in mb} | set(md.index))):
        in_forest = bool(loc.loc[well, "in_forest"]) if "in_forest" in loc.columns else False
        betas = (tuple(pd.to_numeric(pd.Series([md.loc[well, c] for c in BETA_COLS]), errors="coerce"))
                 if well in md.index else (np.nan,) * 3)
        k = normalize_well_name(well)
        bb, db = mb.get(k, ((np.nan,) * 3, mb_undef.get(k, np.nan)))
        first, last, n_mod = modern_span(wells_clean, well)
        reason = ""
        if in_forest:
            reason = "under canopy"
        elif k in mb_undef:
            reason = f"Model B not defined (implied datum {mb_undef[k]:+.2f} m)"
        elif k not in mb:
            reason = "no Model B coefficients"
        elif n_mod < MIN_MODERN_MONTHS:
            reason = f"modern record {n_mod} months, below {MIN_MODERN_MONTHS}"
        a_ok = bool(all(np.isfinite(b) for b in betas) and betas[2] > 0)
        rows.append(dict(well=well, admitted=(reason == ""), excluded_because=reason,
                         beta_1_recharge=betas[0], beta_2_atmospheric_draw=betas[1],
                         beta_3_drainage=betas[2],
                         modern_first=first, modern_last=last, n_modern_months=n_mod,
                         beta_1_model_b=bb[0], beta_2_model_b=bb[1], beta_3_model_b=bb[2],
                         datum_model_b_m=db, admitted_model_a=bool(reason == "" and a_ok)))
    return pd.DataFrame(rows)


def full_hindcast_well(cl: pd.DataFrame, betas: tuple, h0: float, datum: float = DATUM) -> pd.Series:
    """Simulate the whole committed climate record and return every month.

    The same recurrence and the same shared implementation as the windowed
    hindcast; only the returned span differs. The caller supplies the initial
    condition and is responsible for reporting the spin-up.
    """
    b1, b2, b3 = betas
    h = simulate_ssm(h0, cl["P_m"].values, cl["PET"].values, b1, b2, b3,
                     drainage_datum=datum)
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
    ax.set_title("Open-ground water table under the observed climate record, Model B, "
                 "modern coefficients throughout", fontsize=11, loc="left")

    if not epoch.empty:
        idx = np.arange(len(epoch))
        bx.bar(idx - 0.19, epoch["observed_epoch_anomaly_m"], width=0.38,
               color="#1b1b1b", label="observed")
        bx.bar(idx + 0.19, epoch["hindcast_epoch_anomaly_m"], width=0.38,
               color="#2b6cb0", label="hindcast, Model B")
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
    # 1.7.0 (D-332): admission rests on Model B (the forecaster), not on Model A's triple.
    mb, mb_undef, mb_binds = load_model_b()
    adm = usable_codes_b(cmap, mb, mb_undef, obs)
    _adm_a = usable_codes(cmap, md, obs)
    if set(_adm_a.loc[_adm_a["admitted"], "code"]) != set(adm.loc[adm["admitted"], "code"]):
        warn("the Model B admitted set differs from Model A's: A "
             + ", ".join(sorted(_adm_a.loc[_adm_a["admitted"], "code"])) + "; B "
             + ", ".join(sorted(adm.loc[adm["admitted"], "code"])))
    else:
        note("admitted set unchanged from the Model A rule")
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
    # J-6 (Martin, 2026-11-07: "I wanted both Model A and B in scenario 2"). Model B is the same
    # machinery at the datum its own fitted intercept implies, 3.7 - alpha_B/beta_3_B, so nothing
    # new is needed beyond its coefficients. Drawn as a SINGLE LINE, not an envelope: the beta_1
    # envelope is a beta_1 construct with its own documented rationale, and widening it to alpha
    # would invent an uncertainty nobody has quantified. ITS INTERCEPT IS A MODERN-RECORD QUANTITY
    # BEING APPLIED TO A DRIER DECADE, which the caption says and the reader must not forget.
    # One well is excluded by construction: ceh14's implied datum is -9.39 m, a drainage base
    # ABOVE ground, so Model B is not defined there (measured 2026-11-07).
    # J-6, Martin 2026-11-08: "run both models against the ccw well data with the pre 2018 data",
    # and "we should have a whole record trained model against the ccw data and Ranwells".
    #
    # WHY. The coefficients this script has always used come from 03_master_data.csv, which Script
    # 03's own docstring calls "the comparison-window store: n = 100 at every well" -- the most
    # recent 100 months, roughly 2017-11 to 2026-02. The figure caption said "fitted 2005-2026".
    # That was WRONG, and it understated the problem: a hindcast of 1989-96 was being driven by
    # coefficients fitted on the last eight years, about 22 years after the period predicted.
    #
    # So both forms are now fitted over THREE windows and all three are carried, because the
    # question "does the fitting window matter?" is answered by the spread between them, not by
    # an argument about which window is right:
    #
    #   comparison  the last ~100 months, from the master store -- what this script always used
    #   pre2018     the record before MODEL_AB_SPLIT_DATE -- nearer in time to 1989-96, and
    #               excluding the recent wet years that inflate beta_1
    #   whole       every month available -- the largest n, and the fit a reader would assume
    #
    # None of the three sees 1989-96: the dipwells did not exist then. That is the point of the
    # hindcast and the reason the beta_1 envelope exists. If the three windows agree, the envelope
    # is carrying the uncertainty it claims to; if they disagree, the envelope is too narrow.
    FIT_WINDOWS = ("pre2018", "whole")        # "comparison" comes from the master store, above
    fits = {w: {} for w in FIT_WINDOWS}
    # 1.7.0 (D-332): Model B's beta_3 is bounded below (model_utils 1.14.0), so a window refit is no
    # longer dropped for beta_3 <= 0: the bounded fit is kept and counted. A well is still left out
    # where the implied datum is not below ground (alpha/beta_3 large at the bound), and counted.
    win_b_binds = {w: set() for w in FIT_WINDOWS}
    win_b_undef = {w: {} for w in FIT_WINDOWS}
    try:
        _split = pd.Timestamp(config.MODEL_AB_SPLIT_DATE)
        _wc = pd.read_csv(paths.INT_WELLS_CLEAN, index_col=0, parse_dates=True)
        _norm = lambda x: str(x).strip().lower().replace(" ", "")
        _cols = {_norm(c): c for c in _wc.columns}
        for _w in list(md.index):
            _col = _cols.get(_norm(_w))
            if _col is None:
                continue
            _h_all = pd.to_numeric(_wc[_col], errors="coerce").dropna()
            for _win in FIT_WINDOWS:
                _h = _h_all[_h_all.index < _split] if _win == "pre2018" else _h_all
                _c = cl[cl.index < _split] if _win == "pre2018" else cl
                if len(_h) < MIN_FIT_OBS:
                    continue
                _fa = fit_ssm(_h, _c, lag=0, min_obs=MIN_FIT_OBS)
                _fb = fit_ssm_intercept(_h, _c, lag=0, min_obs=MIN_FIT_OBS)
                if _fa and np.isfinite(_fa.get("beta_3_drainage", np.nan)) and _fa["beta_3_drainage"] > 0:
                    fits[_win].setdefault(_w, {})["A"] = (
                        (_fa["beta_1_recharge"], _fa["beta_2_atmospheric_draw"], _fa["beta_3_drainage"]),
                        DATUM, int(_fa.get("n", 0)))
                if _fb and np.isfinite(_fb.get("beta_3_drainage", np.nan)):
                    if _fb.get("beta_3_bound_binds", False):
                        win_b_binds[_win].add(_w)
                    _db2 = (DATUM - _fb.get("alpha", 0.0) / _fb["beta_3_drainage"]
                            if _fb["beta_3_drainage"] > 0 else np.nan)
                    if np.isfinite(_db2) and _db2 > 0:
                        fits[_win].setdefault(_w, {})["B"] = (
                            (_fb["beta_1_recharge"], _fb["beta_2_atmospheric_draw"], _fb["beta_3_drainage"]),
                            _db2, int(_fb.get("n", 0)))
                    else:                     # base at or above ground: Model B undefined here
                        win_b_undef[_win][_w] = _db2
        for _win in FIT_WINDOWS:
            note(f"{_win} fits: {sum('A' in v for v in fits[_win].values())} Model A, "
                 f"{sum('B' in v for v in fits[_win].values())} Model B "
                 f"({len(win_b_binds[_win])} with beta_3 at the bound, {len(win_b_undef[_win])} with no "
                 f"datum below ground), over {len(fits[_win])} well(s)")
    except Exception as _e:
        note(f"window fits unavailable ({type(_e).__name__}: {_e}); "
             f"the window-comparison columns stay empty")

    # 1.7.0 (D-332): Model B (mb, mb_undef, mb_binds) was loaded before admission, load_model_b().

    # 1.7.0 (D-332, Addendum 2 tasks 1-2): Model A at each well's depth to mean high water, the one
    # nameable physical base. MHW is Script 01b's tide_mhw_m, the ground Script 01's (01_locations,
    # as Scripts 48 and 50 read them); fitted as Script 03 fits the master store and Script 50's E16
    # fits this form (dry months censored, the last LCSC_DATA_LIMIT calendar months).
    mhw = mhw_level()
    if np.isfinite(mhw):
        info(f"mean high water {mhw:.3f} m OD (Script 01b tide_mhw_m)")
    else:
        warn("tide_mhw_m not in Script 01b's report numbers: the mean-high-water form is skipped")
    _wc_cols = {c.lower().strip(): c for c in wells_clean.columns}
    mhw_identity = []

    per_well, series_rows, sens_rows, tf_rows = [], [], [], []
    for r in admitted.itertuples():
        a_ok = model_a_ok(md, r.well)
        betas = (tuple(float(md.loc[r.well, c]) for c in BETA_COLS) if a_ok else (np.nan,) * 3)
        h0 = equilibrium_depth(betas, p_mean, pet_mean) if a_ok else np.nan
        if not a_ok:
            note(f"{r.well}: no Model A triple with beta_3 > 0; its Model A columns are left empty")
        o, n_cens = observed_series(obs, r.code, r.datum_offset_m)
        if o.empty:
            note(f"{r.code}: no uncensored observations")
            continue

        # Model B, at each beta_1 scaling (1.7.0: B carries its own envelope, the same scalings)
        kb = normalize_well_name(r.well)
        by_scale_b, b_entry = {}, mb.get(kb)
        if b_entry is not None:
            _bb, _db = b_entry
            _h0b = equilibrium_depth(_bb, p_mean, pet_mean, drainage_datum=_db)
            if np.isfinite(_h0b):
                for sc in BETA1_SCALINGS:
                    by_scale_b[sc], _ = hindcast_well(cl, _bb, _h0b, first_month, last_month, sc,
                                                      drainage_datum=_db)

        by_scale = {}
        for sc in BETA1_SCALINGS:
            if a_ok:
                pred, spinup = hindcast_well(cl, betas, h0, first_month, last_month, sc)
            else:                     # B carries the months; A is NaN on them
                pred, spinup = by_scale_b[sc] * np.nan, int((cl.index < first_month).sum())
            common = o.index.intersection(pred.index)
            nse, rmse, bias = get_metrics(o.loc[common], pred.loc[common])
            m = {"NSE": nse, "RMSE": rmse, "Bias": bias}
            by_scale[sc] = (pred, common, m)
            mb_sc = {}
            if sc in by_scale_b:
                _nb, _rb, _bsb = get_metrics(o.loc[common], by_scale_b[sc].loc[common])
                mb_sc = dict(nse_model_b=float(_nb), rmse_m_model_b=float(_rb), bias_m_model_b=float(_bsb),
                             mean_predicted_m_model_b=float(by_scale_b[sc].loc[common].mean()))
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
                                  mean_predicted_m=float(pred.loc[common].mean()),
                                  **{k_: mb_sc.get(k_, np.nan) for k_ in
                                     ("nse_model_b", "rmse_m_model_b", "bias_m_model_b",
                                      "mean_predicted_m_model_b")}))

        base = 1.0 if 1.0 in by_scale else sorted(by_scale)[0]
        pred, common, m = by_scale[base]
        lo = np.minimum.reduce([by_scale[s][0].loc[common].values for s in by_scale])
        hi = np.maximum.reduce([by_scale[s][0].loc[common].values for s in by_scale])
        pred_b = by_scale_b.get(base)
        if pred_b is not None:
            lo_b = np.minimum.reduce([by_scale_b[s].loc[common].values for s in by_scale_b])
            hi_b = np.maximum.reduce([by_scale_b[s].loc[common].values for s in by_scale_b])
        else:
            lo_b = hi_b = np.full(len(common), np.nan)

        # Model A at this well's depth to mean high water (and the same route at DATUM, which must
        # reproduce the master-store run: the identity check that the route is Script 03's)
        pred_m, d_mhw, fit_m = None, np.nan, None
        _col = _wc_cols.get(r.well)
        _g = float(loc.loc[r.well, "ground_elev_m"]) if r.well in loc.index else np.nan
        if np.isfinite(mhw) and np.isfinite(_g) and _col is not None:
            d_mhw = _g - mhw
            _hh = pd.to_numeric(wells_clean[_col], errors="coerce").dropna()
            fit_m = fixed_floor_fit(_hh, cl, _col, d_mhw)
            if fit_m is not None and fit_m["beta_3_drainage"] > 0:
                _bm = (fit_m["beta_1_recharge"], fit_m["beta_2_atmospheric_draw"], fit_m["beta_3_drainage"])
                _h0m = equilibrium_depth(_bm, p_mean, pet_mean, drainage_datum=d_mhw)
                pred_m, _ = hindcast_well(cl, _bm, _h0m, first_month, last_month, 1.0, drainage_datum=d_mhw)
            _fi = fixed_floor_fit(_hh, cl, _col, DATUM) if a_ok else None
            if _fi is not None and _fi["beta_3_drainage"] > 0:
                _bi = (_fi["beta_1_recharge"], _fi["beta_2_atmospheric_draw"], _fi["beta_3_drainage"])
                _pi, _ = hindcast_well(cl, _bi, equilibrium_depth(_bi, p_mean, pet_mean),
                                       first_month, last_month, base)
                mhw_identity.append(float(np.nanmax(np.abs(_pi.loc[common].values - pred.loc[common].values))))

        # J-6: the same two forms over each alternative fitting window
        wpred = {}                            # (window, form) -> predicted series
        for _win in FIT_WINDOWS:
            for _k in ("A", "B"):
                _ent = fits[_win].get(r.well, {}).get(_k)
                if _ent is None:
                    continue
                _bb, _dd, _ = _ent
                _h0 = equilibrium_depth(_bb, p_mean, pet_mean, drainage_datum=_dd)
                if not np.isfinite(_h0):
                    continue
                _pp, _ = hindcast_well(cl, _bb, _h0, first_month, last_month, 1.0,
                                       drainage_datum=_dd)
                wpred[(_win, _k)] = _pp

        # h0 probe: restart from the equilibrium depth displaced either way and
        # confirm the comparison window has forgotten it.
        h0_spread = 0.0 if a_ok else np.nan
        h0_spread_b = 0.0 if pred_b is not None else np.nan
        for off in H0_PROBE_OFFSETS_M:
            if a_ok:
                alt, _ = hindcast_well(cl, betas, h0 + off, first_month, last_month, base)
                h0_spread = max(h0_spread, float(np.nanmax(np.abs(
                    alt.loc[common].values - pred.loc[common].values))))
            if pred_b is not None:
                _bb, _db = b_entry
                altb, _ = hindcast_well(cl, _bb, equilibrium_depth(_bb, p_mean, pet_mean, drainage_datum=_db) + off,
                                        first_month, last_month, base, drainage_datum=_db)
                h0_spread_b = max(h0_spread_b, float(np.nanmax(np.abs(
                    altb.loc[common].values - pred_b.loc[common].values))))

        # Level and dynamics are separate failures and NSE conflates them: a
        # hindcast that tracks the swing against the wrong datum scores worse
        # than one that misses the swing entirely. The correlation answers
        # whether the dynamics are right; the bias-removed NSE answers what the
        # fit would be if the level were. The epoch shift is the data-quality
        # companion — a well whose historic mean sits on the opposite side of
        # its modern mean from the rest of the network is telling us something
        # about its datum or its identity, not about the model.
        oc, pc = o.loc[common].values, pred.loc[common].values
        r_shape, nse_db = shape_scores(oc, pc)
        m_mod = modern_mean(wells_clean, r.well)
        epoch_shift = float(oc.mean() - m_mod) if np.isfinite(m_mod) else np.nan
        bcols = {f"{c}_model_b": np.nan for c in MODEL_COLS}
        bcols.update(beta_1_model_b=np.nan, beta_2_model_b=np.nan, beta_3_model_b=np.nan,
                     datum_model_b_m=(mb_undef.get(kb, np.nan) if b_entry is None else b_entry[1]),
                     beta_3_bound_binds_model_b=bool(kb in mb_binds),
                     model_b_defined=bool(pred_b is not None), h0_sensitivity_m_model_b=h0_spread_b)
        if pred_b is not None:
            pcb = pred_b.loc[common].values
            _nb, _rb, _bsb = get_metrics(o.loc[common], pred_b.loc[common])
            _rsb, _ndb = shape_scores(oc, pcb)
            bcols.update(nse_model_b=float(_nb), rmse_m_model_b=float(_rb), bias_m_model_b=float(_bsb),
                         pearson_r_model_b=_rsb, nse_bias_removed_model_b=_ndb,
                         residual_mean_m_model_b=float(np.mean(oc - pcb)),
                         mean_predicted_m_model_b=float(np.mean(pcb)),
                         beta_1_model_b=b_entry[0][0], beta_2_model_b=b_entry[0][1],
                         beta_3_model_b=b_entry[0][2])

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
            epoch_shift_m=epoch_shift if np.isfinite(epoch_shift) else np.nan,
            **bcols))

        # the three-form table (Addendum 2): every observed month, dry ones scored
        _tf = three_form_scores(obs, r.code, r.datum_offset_m,
                                {"B": pred_b, "A_3.7": pred if a_ok else None, "A_MHW": pred_m})
        _dat = {"B": bcols["datum_model_b_m"], "A_3.7": DATUM, "A_MHW": d_mhw}
        _bet = {"B": (b_entry[0] if b_entry is not None else (np.nan,) * 3), "A_3.7": betas,
                "A_MHW": ((fit_m["beta_1_recharge"], fit_m["beta_2_atmospheric_draw"], fit_m["beta_3_drainage"])
                          if fit_m is not None else (np.nan,) * 3)}
        for t_ in _tf:
            f_ = t_["form"]
            tf_rows.append(dict(well=r.well, code=r.code, **t_, datum_m=_dat[f_],
                                beta_1=_bet[f_][0], beta_2=_bet[f_][1], beta_3=_bet[f_][2],
                                beta_3_bound_binds=(bool(kb in mb_binds) if f_ == "B" else False)))

        for t in common:
            series_rows.append(dict(
                well=r.well, code=r.code, month=t.strftime("%Y-%m"),
                observed_m_bg=float(o.loc[t]),
                predicted_m_bg=float(pred.loc[t]),
                predicted_lo_m_bg=float(lo[common.get_loc(t)]),
                predicted_hi_m_bg=float(hi[common.get_loc(t)]),
                predicted_b_m_bg=(float(pred_b.loc[t])
                                  if pred_b is not None and t in pred_b.index else np.nan),
                **{f"predicted_{_k.lower()}_{_win}_m_bg":
                   (float(wpred[(_win, _k)].loc[t])
                    if (_win, _k) in wpred and t in wpred[(_win, _k)].index else np.nan)
                   for _win in FIT_WINDOWS for _k in ("A", "B")},
                residual_m=float(o.loc[t] - pred.loc[t]),
                # 1.7.0 (D-332): appended, so no existing column moves (Script 53 reads 39_02)
                predicted_b_lo_m_bg=float(lo_b[common.get_loc(t)]),
                predicted_b_hi_m_bg=float(hi_b[common.get_loc(t)]),
                predicted_mhw_m_bg=(float(pred_m.loc[t])
                                    if pred_m is not None and t in pred_m.index else np.nan)))
        result(f"{r.well} ({r.code})",
               (f"Model B NSE {bcols['nse_model_b']:+.3f}  r {bcols['pearson_r_model_b']:+.3f}  "
                f"bias {bcols['bias_m_model_b']:+.3f} m  |  " if pred_b is not None else "Model B undefined  |  ")
               + f"Model A NSE {m['NSE']:+.3f}  r {r_shape:+.3f}  "
               f"NSE(level removed) {nse_db:+.3f}  bias {m['Bias']:+.3f} m  "
               f"epoch shift {epoch_shift:+.3f} m  n {len(common)}")

    pw = pd.DataFrame(per_well)
    sr = pd.DataFrame(series_rows)
    sens = pd.DataFrame(sens_rows)
    tf = pd.DataFrame(tf_rows)
    if not tf.empty:
        _best = (tf.dropna(subset=["rmse_with_dry_m"]).sort_values("rmse_with_dry_m")
                 .drop_duplicates("well").set_index("well")["form"])
        tf["best_form_with_dry"] = tf["well"].map(_best)
        for _w, _f in _best.items():
            note(f"{_w}: lowest error counting dry months under {_f}")

    # 1.7.0 (D-332): how Model B is defined at the admitted wells, and the mean-high-water level
    _adm_k = {normalize_well_name(w) for w in pw["well"]} if not pw.empty else set()
    extra = {
        "n_wells_model_b_bound_binds": (len(_adm_k & mb_binds), "wells",
            f"admitted wells whose Model B beta_3 sits at the lower bound MODEL_B_BETA3_MIN ({B3_MIN:g}/month), "
            "fit kept (D-332)"),
        "n_wells_model_b_excluded_datum": (len(_adm_k & set(mb_undef)), "wells",
            "admitted wells left out of the Model B headline: implied datum DRAINAGE_DATUM - alpha/beta_3 "
            "not below ground" + (" (" + ", ".join(sorted(_adm_k & set(mb_undef))) + ")"
                                  if _adm_k & set(mb_undef) else "")),
        "n_wells_model_b_bound_binds_network": (len(mb_binds), "wells",
            "every well in Script 03's 03_16 whose Model B beta_3 sits at the lower bound"),
        "n_wells_model_b_excluded_datum_network": (len(mb_undef), "wells",
            "every well in 03_16 whose implied datum is not below ground: "
            + (", ".join(f"{k} {v:+.2f} m" for k, v in sorted(mb_undef.items())) or "none")),
    }
    for _win in FIT_WINDOWS:
        _bk = {normalize_well_name(w) for w in win_b_binds[_win]}
        _uk = {normalize_well_name(w) for w in win_b_undef[_win]}
        extra[f"n_wells_model_b_bound_binds_{_win}"] = (len(_adm_k & _bk), "wells",
            f"admitted wells whose {_win}-window Model B refit binds at the beta_3 bound (fit kept)")
        extra[f"n_wells_model_b_excluded_datum_{_win}"] = (len(_adm_k & _uk), "wells",
            f"admitted wells whose {_win}-window Model B refit has no datum below ground (left out)")
    if np.isfinite(mhw):
        extra["tide_mhw_m_used"] = (mhw, "m OD", "mean high water the MHW form is run at (Script 01b tide_mhw_m)")
    if mhw_identity:
        extra["mhw_route_identity_max_abs_diff_m"] = (max(mhw_identity), "m",
            f"identity check: the MHW form's fitting route run at {DATUM:g} m less the master-store "
            f"Model A run, max over {len(mhw_identity)} wells and the comparison months (expected ~0)")

    phase(4, "Write outputs")
    pw.to_csv(OUT_PER_WELL, index=False); saved(OUT_PER_WELL.name)
    sr.to_csv(OUT_SERIES, index=False); saved(OUT_SERIES.name)
    sens.to_csv(OUT_SENSITIVITY, index=False); saved(OUT_SENSITIVITY.name)
    tf.to_csv(OUT_THREE_FORMS, index=False); saved(OUT_THREE_FORMS.name)

    # J-6: score every (window, form) run against the observed 1989-96 record, per well and
    # pooled. The comparison-window runs are the columns this script always wrote; the other two
    # are the refits above. Pooling is over all paired months at once -- NOT a mean of per-well
    # NSEs, which would weight a well with eight observations like one with ninety.
    RUNS = (("comparison", "A", "predicted_m_bg"), ("comparison", "B", "predicted_b_m_bg"),
            ("comparison", "A_MHW", "predicted_mhw_m_bg"),                 # 1.7.0 (D-332)
            ("pre2018", "A", "predicted_a_pre2018_m_bg"), ("pre2018", "B", "predicted_b_pre2018_m_bg"),
            ("whole", "A", "predicted_a_whole_m_bg"), ("whole", "B", "predicted_b_whole_m_bg"))
    fw_rows = []
    if not sr.empty:
        def _score(o_, p_):
            if len(o_) < 3 or not np.isfinite(o_).all() or not np.isfinite(p_).all():
                return {}
            den = float(((o_ - o_.mean()) ** 2).sum())
            return dict(n=int(len(o_)),
                        r=(float(np.corrcoef(o_, p_)[0, 1]) if o_.std() > 0 and p_.std() > 0
                           else np.nan),
                        nse=(1.0 - float(((o_ - p_) ** 2).sum()) / den if den > 0 else np.nan),
                        bias_m=float((p_ - o_).mean()),
                        rmse_m=float(np.sqrt(((o_ - p_) ** 2).mean())))
        for _win, _form, _col in RUNS:
            if _col not in sr.columns:
                continue
            for _w, _g in sr.groupby("well"):
                _m = _g[["observed_m_bg", _col]].dropna()
                _sc = _score(_m["observed_m_bg"].values, _m[_col].values)
                if _sc:
                    fw_rows.append(dict(scope="well", well=_w, fit_window=_win,
                                        model=_form, **_sc))
            _m = sr[["observed_m_bg", _col]].dropna()
            _sc = _score(_m["observed_m_bg"].values, _m[_col].values)
            if _sc:
                fw_rows.append(dict(scope="pooled", well="(all)", fit_window=_win,
                                    model=_form, **_sc))
            # POOLED NSE IS NOT THE SKILL A READER THINKS IT IS. Pooling across wells puts the
            # ACROSS-well variance in the denominator, which here is far larger than the
            # within-well variance, so the pooled NSE comes out around +0.55 while most
            # individual wells score NEGATIVE -- worse than predicting their own mean. Both
            # numbers are arithmetically correct and they answer different questions. The
            # within-well-centred version below removes each well's own observed mean from
            # both series first, so it scores the DYNAMICS the hindcast is for, and it is the
            # pooled number to quote. Measured 2026-11-08; quoting the uncentred one alone
            # would overstate the hindcast.
            _c = sr[["well", "observed_m_bg", _col]].dropna()
            if len(_c) >= 3:
                _o = (_c["observed_m_bg"]
                      - _c.groupby("well")["observed_m_bg"].transform("mean")).values
                _p = (_c[_col] - _c.groupby("well")[_col].transform("mean")).values
                _sc = _score(_o, _p)
                if _sc:
                    fw_rows.append(dict(scope="pooled_centred", well="(all)",
                                        fit_window=_win, model=_form, **_sc))
    fw = pd.DataFrame(fw_rows)
    fw.to_csv(OUT_FIT_WINDOWS, index=False); saved(OUT_FIT_WINDOWS.name)

    write_report_numbers(pw, sr, cl, wells_clean, first_month, last_month, sens, tf=tf, extra=extra)
    if not sr.empty:
        sr_plot = sr.copy()
        sr_plot["month"] = pd.PeriodIndex(sr_plot["month"], freq="M").to_timestamp()
        plot_hindcast(sr_plot, admitted, OUT_FIG); saved(OUT_FIG.name)
        if not fw.empty:
            plot_fit_windows(sr_plot, admitted, fw, OUT_FIT_WINDOW_FIG)
            saved(OUT_FIT_WINDOW_FIG.name)


    phase(5, "Full-record hindcast")
    # 1.7.0 (D-332): the full-record pass is Model B, each well at its own implied datum. Model A is
    # run beside it on the wells where it can be, as the *_model_a columns. Nothing outside this
    # script reads 39_05-39_07 (checked 2026-11-12), so the unsuffixed columns change meaning.
    panel = open_ground_panel(md, loc, wells_clean, mb, mb_undef)
    adm_panel = panel[panel["admitted"]]
    for r in panel[~panel["admitted"]].itertuples():
        note(f"{r.well} not in panel: {r.excluded_because}")
    result("panel wells", f"{len(adm_panel)} of {len(panel)} candidates "
                          f"(Model A alternative at {int(adm_panel['admitted_model_a'].sum())})")

    def _anoms(form):
        an, mm = {}, {}
        for r in adm_panel.itertuples():
            if form == "B":
                betas, dd = (r.beta_1_model_b, r.beta_2_model_b, r.beta_3_model_b), r.datum_model_b_m
            else:
                if not r.admitted_model_a:
                    continue
                betas, dd = (r.beta_1_recharge, r.beta_2_atmospheric_draw, r.beta_3_drainage), DATUM
            h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=dd)
            sim = full_hindcast_well(cl, betas, h0, dd)
            ref = sim.loc[r.modern_first:r.modern_last]
            if ref.empty:
                note(f"{r.well}: modern span falls outside the climate record")
                continue
            mm[r.well] = float(ref.mean())
            an[r.well] = sim - float(ref.mean())
        return an, mm

    anomalies, modelled_modern = _anoms("B")
    anomalies_a, modelled_modern_a = _anoms("A")

    def _site(an):
        anom = pd.DataFrame(an)
        st = pd.DataFrame({
            "month": anom.index,
            "site_anomaly_m": anom.mean(axis=1).values,
            "site_sd_m": anom.std(axis=1, ddof=1).values,
            "n_wells": anom.notna().sum(axis=1).values,
            "P_m": cl.loc[anom.index, "P_m"].values,
            "PET": cl.loc[anom.index, "PET"].values,
        })
        st["site_anomaly_smoothed_m"] = (
            st["site_anomaly_m"].rolling(SMOOTH_MONTHS, center=True,
                                         min_periods=SMOOTH_MONTHS).mean())
        dec = (anom.index.year // 10) * 10
        dw = anom.groupby(dec).mean().stack().reset_index()
        dw.columns = ["decade", "well", "mean_anomaly_m"]
        dw["scope"] = "well"
        ds = anom.mean(axis=1).groupby(dec).mean().reset_index()
        ds.columns = ["decade", "mean_anomaly_m"]
        ds["well"] = "SITE"
        ds["scope"] = "site"
        de = pd.concat([ds[["decade", "well", "scope", "mean_anomaly_m"]],
                        dw[["decade", "well", "scope", "mean_anomaly_m"]]], ignore_index=True)
        return anom, st, de

    site = pd.DataFrame(columns=["month"])
    decadal = pd.DataFrame()
    epoch = pd.DataFrame()
    if anomalies:
        anom, site, decadal = _site(anomalies)
        if anomalies_a:
            anom_a, site_a, dec_a = _site(anomalies_a)
            site = site.merge(site_a[["month", "site_anomaly_m", "site_sd_m", "n_wells",
                                      "site_anomaly_smoothed_m"]],
                              on="month", how="left", suffixes=("", "_model_a"))
            decadal = decadal.merge(dec_a, on=["decade", "well", "scope"], how="left",
                                    suffixes=("", "_model_a"))
        else:
            anom_a = pd.DataFrame()

        rows = []
        for r in pw.itertuples():
            if r.well not in anom.columns:
                continue
            hind = anom[r.well].loc[first_month:last_month]
            if hind.empty:
                continue
            hind_a = (anom_a[r.well].loc[first_month:last_month]
                      if r.well in anom_a.columns else pd.Series(dtype=float))
            rows.append(dict(well=r.well, code=r.code,
                             observed_epoch_anomaly_m=r.epoch_shift_m,
                             hindcast_epoch_anomaly_m=float(hind.mean()),
                             modelled_modern_mean_m=modelled_modern[r.well],
                             observed_modern_mean_m=r.mean_modern_m,
                             hindcast_epoch_anomaly_m_model_a=(float(hind_a.mean()) if len(hind_a) else np.nan)))
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
             "Per well, Model B (the forecaster, D-332; beta_1 at its fitted value):"]
    for r in pw.itertuples():
        if not r.model_b_defined:
            lines.append(f"  {r.well:<6} ({r.code})  Model B not defined (implied datum "
                         f"{r.datum_model_b_m:+.2f} m, not below ground)")
            continue
        lines.append(f"  {r.well:<6} ({r.code})  NSE {r.nse_model_b:+.3f}  r {r.pearson_r_model_b:+.3f}  "
                     f"NSE with the level offset removed {r.nse_bias_removed_model_b:+.3f}  "
                     f"bias {r.bias_m_model_b:+.3f} m  RMSE {r.rmse_m_model_b:.3f} m  "
                     f"n {r.n_months}  censored dropped {r.n_censored}")
    lines += ["", f"Per well, Model A at the fixed {DATUM:g} m floor (tested alternative):"]
    for r in pw.itertuples():
        lines.append(f"  {r.well:<6} ({r.code})  NSE {r.nse:+.3f}  r {r.pearson_r:+.3f}  "
                     f"NSE with the level offset removed {r.nse_bias_removed:+.3f}  "
                     f"bias {r.bias_m:+.3f} m  RMSE {r.rmse_m:.3f} m  "
                     f"n {r.n_months}  censored dropped {r.n_censored}")
    if not tf.empty:
        lines += ["", "Three forms, typical monthly error counting dry months (a run above the pipe base "
                      "in a dry month is wrong by the difference), m:",
                  "  well    B       A 3.7 m  A MHW   (MHW floor)  best"]
        for _w, _g in tf.groupby("well", sort=False):
            _v = _g.set_index("form")
            _f = lambda k: (f"{_v.loc[k, 'rmse_with_dry_m']:.3f}" if k in _v.index
                            and np.isfinite(_v.loc[k, "rmse_with_dry_m"]) else "  n/a")
            _dm = _v.loc["A_MHW", "datum_m"] if "A_MHW" in _v.index else np.nan
            lines.append(f"  {_w:<6}  {_f('B')}   {_f('A_3.7')}    {_f('A_MHW')}   ({_dm:5.2f} m)    "
                         f"{_g['best_form_with_dry'].iloc[0]}")
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
                  f"mean residual (observed minus hindcast) across wells: Model B "
                  f"{pw.residual_mean_m_model_b.mean():+.3f} m, Model A {pw.residual_mean_m.mean():+.3f} m",
                  "  positive means the record sits SHALLOWER than the "
                  "climate-only hindcast",
                  f"largest initial-condition sensitivity over the window: "
                  f"{pw.h0_sensitivity_m.max():.2e} m — the spin-up has "
                  f"forgotten the starting value",
                  "",
                  "beta_1 sensitivity (the coefficients are fitted on the last 100 months of each well's record (2017-11 to 2026-02, n = 75-100 per well) and "
                  "the site-wide beta_1 decline means 1989 values were plausibly "
                  "higher):"]
        for sc, g in sens.groupby("beta1_scale"):
            og = g[g["in_forest"] == False]          # noqa: E712 — None must not match
            cg = g[g["in_forest"] == True]           # noqa: E712
            ogb, cgb = og[og.nse_model_b.notna()], cg[cg.nse_model_b.notna()]
            lines.append(
                f"  scale {sc:.2f}:  Model B open ground (n={len(ogb)}) mean NSE "
                f"{ogb.nse_model_b.mean():+.3f}, mean bias {ogb.bias_m_model_b.mean():+.3f} m"
                f"   |  under canopy (n={len(cgb)}) mean NSE {cgb.nse_model_b.mean():+.3f}, "
                f"mean bias {cgb.bias_m_model_b.mean():+.3f} m")
            lines.append(
                f"              Model A open ground (n={len(og)}) mean NSE "
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
                  "Full-record hindcast, Model B (open-ground panel, modern coefficients "
                  "applied to the whole committed climate record; Model A in brackets):",
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
            lines.append(f"    {int(r.decade)}s  {r.mean_anomaly_m:+.3f}   "
                         f"({getattr(r, 'mean_anomaly_m_model_a', np.nan):+.3f})")
        if not epoch.empty:
            lines += ["",
                      "  Epoch check over the CCW window, each series against its "
                      "own modern mean:"]
            for r in epoch.itertuples():
                lines.append(f"    {r.well:<6} ({r.code})  observed "
                             f"{r.observed_epoch_anomaly_m:+.3f} m   hindcast "
                             f"{r.hindcast_epoch_anomaly_m:+.3f} m   "
                             f"(Model A {r.hindcast_epoch_anomaly_m_model_a:+.3f} m)")
        lines += ["",
                  "  The coefficients are fitted on the last 100 months of each well's record (2017-11 to 2026-02, n = 75-100 per well)"
                  " and are applied unchanged across the whole record.",
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
