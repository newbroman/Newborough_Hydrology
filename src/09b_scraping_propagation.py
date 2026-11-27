"""
==========================================================================
09b — SCRAPING PROPAGATION ANALYSIS
==========================================================================
Purpose:
    Evaluates whether the CEH36 scraping event (0.2 m ground lowering,
    April 2015) propagated uphill into the forest as a detectable shift
    in SSM coefficients. Uses split-window SSM fitting with BACI
    correction against distant control wells.

    Companion to Script 09 (hierarchical BACI at the scraping wells
    themselves). Script 09 asks "did scraping work at the scraped site?"
    This script asks "what did scraping do to the neighbours?"

Outputs (to outputs/09_scraping_intervention/):
    CSVs:
        09b_01_individual_well_baci.csv   — per-well BACI-corrected shifts
        09b_02_centroid_summaries.csv      — group centroid BACI shifts
        09b_04_scenario_comparison.csv     — scenario chart values
    Figures:
        09b_03_ceh36_equilibration.jpg     — CEH36 post-scraping trajectory
        09b_04_scenario_comparison.jpg     — scenario comparison bar chart

Reads:
    outputs/01_wells_clean.csv
    outputs/01_wells_extended.csv
    outputs/01_climate.csv
    outputs/01_locations.csv
    outputs/03_master_data.csv
==========================================================================
"""

__version__ = "1.16.0"  # 2026-11-27 (D-348): bar groups and axis labels from CLUSTER_LABELS (C3o, C3f); C5 Sy and bar text read C3f. Was "1.15.0"  # Hollingham (2026) - 2026-11-20 (T-209, D-333; changelog 2026-11-20b). The 'Scraping (nearby)'
#   bars of 09b_04 (BACI delta-beta_3 of split-window refits through 1/beta_3) are dropped: the scrape is detected
#   by the paired contrast at CEH36 (09a) and its propagation is not quantified. _compute_scraping_bars,
#   scrape_bar_n_b3_held_at_bound, the D-333 status column, labels and count key (scenario_n_keys_withdrawn_d333_09b)
#   are gone. Clearfell / Thinning 50% bars now come from scraping_common.compute_scenario_bars 1.14.0 (a share f of
#   the interception, calibrated on the observed BACI step). 09b_04 redrawn: the two text boxes over the C4/C5 bars
#   are one note below the axes.
# 1.14.1  # Hollingham (2026) - 2026-11-19 (J-16, changelog 2026-11-19f). The D-333 withdrawn-key count is
#   emitted as scenario_n_keys_withdrawn_d333_09b: Scripts 09b, 19 and 21 each wrote the same name for their own
#   count (1, 11, 32), which number_ledger reads as one quantity with three values. Nothing reads the key.
# 1.14.0  # Hollingham (2026) - 2026-11-12 (D-333, J-9 phase 2b). The 'Scraping (nearby)' bars (built
#   from the BACI centroid delta-beta_3 of split-window refits) and the Clearfell / Thinning 50% bars (a beta_2
#   multiplier of single-well era refits, clearfell_common.load_clearfell_impact_b2_multiplier) are WITHDRAWN under
#   D-333 pending T-209. No value changes: scrape_bar_n_b3_held_at_bound (a property of the scrape bars) gets
#   config.D333_WITHDRAWN_NOTE appended to its note, a count key scenario_n_keys_withdrawn_d333 is written, one warn()
#   names the withdrawn bars, 09b_04 and 09b_05 gain a `status` column ("withdrawn (D-333)" on those rows), and the
#   two figures' legend entries say "withdrawn (D-333)" (legends moved outside the axes). The delta-beta_3 propagation
#   tests (scrape_propagation_*) are not withdrawn but their notes say "form-dependent (Model A and Model B disagree
#   in sign), not established (D-333)", as D-333 treats Script 33's correlation; the observed CEH36-type scraping bar,
#   Broadleaf and the climate bars are not touched.
# 1.13.0  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b, coordinator follow-up). A scrape bar's
#   post-scrape b3_new = b3*(1 + baci_db3_pct) below config.MODEL_B_BETA3_MIN is held AT the bound (D-332 imposes
#   beta_3 > 0 on Model B as a bound): not withheld, no delta-alpha. Flagged on the console, in the new column
#   b3_held_at_bound of 09b_04_scenario_comparison.csv, and counted (scrape_bar_n_b3_held_at_bound; C4 today).
# 1.12.0  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b). The split-window fits are Model B
#   (fit_ssm(intercept=True), same windows and MIN_OBS_SPLIT; beta_3 bounded at MODEL_B_BETA3_MIN): every pre_/post_/
#   raw_/baci_ coefficient column and the delta-beta3 report numbers now carry Model B. New columns pre_alpha,
#   post_alpha, raw_dalpha, baci_dalpha, pre_/post_b3_bound_binds; Model A kept beside them as pre_b3_model_a,
#   post_b3_model_a, raw_db3_model_a, baci_db3_model_a, baci_db3_pct_model_a, and as _model_a report numbers for every
#   delta-beta3 key (scrape_propagation_near_*, scrape_propagation_uphill_dist_r/p). New key
#   scrape_propagation_n_fits_model_b_bound_binds. The scrape bars run at each cluster's implied datum
#   (scraping_common 1.13.0 h_disp): b3*h_disp against b3_new*(h_disp - GROUND_LOWERING), the base held fixed.
# 1.11.0  # Hollingham (2026) - 2026-10-10. Emit-first (spec NRG_spec_emit_first_report9_2026-10-09):
#   report9 quotes the nearest and farthest uphill-well distance from CEH36; new rows
#   scrape_propagation_uphill_dist_min_m and scrape_propagation_uphill_dist_max_m. Emit-only.
# 1.10.0  # Hollingham (2026) - 2026-10-05. T-108: emits the distance-decay test across the
#   uphill wells (Pearson r and p of BACI-corrected delta-beta3 against distance from CEH36, and n), which
#   report9 4.11 quotes as the reason the modelled reach is not independently resolved. Emit-only.
# 1.9.0  # Hollingham (2026) — 2026-09-26. The uphill propagation test is
#   written out (T-84): 09b_report_numbers.csv gains the near-band one-sample t-test of the
#   BACI-corrected delta-beta3 (wells within config.SCRAPE_PROPAGATION_NEAR_M of CEH36: n,
#   n positive, mean, t, p) that report9 §4.5.5 quotes, and 09b_01 gains baci_db3_pct per
#   well, the percentage the Methods Supplement quotes (the centroid table already had it).
#   The test runs on the unrounded frame. No existing value moves.
# 1.8.0  # Hollingham (2026) — 2026-09-21. Emits 09b_report_numbers.csv:
#   the post-scrape fitting window in months (post_n at CEH36 — April 2015 to the
#   December 2017 clearfell; the "31-month post-scraping record" the front matter
#   and report9 §4.5 quote, which lived only as a repeated column) and the
#   pre-scrape window. OUT_09B_REPORT_NUMBERS had been declared and never written.
# 1.7.0  # Hollingham (2026) — 2026-08-29. FELL_DATE, SCRAPE_DATE
#   and SCRAPE2_DATE were private literals; now imported from clearfell_common
#   (D-084). No value changes.
# v1.6.0  # Hollingham (2026) — 2026-07-02
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(
    _os.path.abspath(__file__)))); del _sys, _os

from utils.paths import (
    INT_WELLS_CLEAN, INT_WELLS_EXTENDED, INT_CLIMATE, INT_LOCATIONS,
    INT_MASTER_DATA, OUT_09B_INDIVIDUAL, OUT_09B_CENTROIDS,
    OUT_09B_TRAJECTORY, OUT_09B_SCENARIO, OUT_09B_SCENARIO_CSV,
    OUT_09B_SUMMER_SCENARIO, OUT_09B_SUMMER_SCENARIO_CSV, OUT_17_SY_TABLE,
    OUT_09B_REPORT_NUMBERS,
)
from utils.report_numbers_utils import ReportNumbers
from utils.config import (FOREST_INTERCEPTION, BW_MODE, CEH36_E, CEH36_N,
                          SCRAPE_PROPAGATION_NEAR_M, CLUSTER_LABELS)
# D-348: the bar groups, keys "C1".."C5" (C5 = C3f, the Western Dune's forest wells), and their axis labels
_GROUP_KEYS = [f"C{c}" for c in CLUSTER_LABELS]
_GROUP_TICKS = {"C1": "C1\nLake Edge", "C2": "C2\nDune", "C3": "C3o\nWestern Dune\nopen",
                "C4": "C4\nMain\nForest", "C5": "C3f\nWestern Dune\nforest"}
from utils.model_utils import fit_ssm
from utils.data_utils import normalize_well_name

import pandas as pd
import numpy as np
import matplotlib

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import render_figure
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats as _stats


# ============================================================================
# CONSTANTS
# ============================================================================
# All three were private literals until 2026-08-29 (D-084). Now the shared
# constants from utils.clearfell_common, which builds them from utils.config.
# Values unchanged.
from utils.clearfell_common import (
    CLEARFELL_DATE as FELL_DATE,
    SCRAPING_DATE as SCRAPE_DATE,
    SCRAPING_DATE_2 as SCRAPE2_DATE,
)

E_CEH36 = CEH36_E   # config.py — documented 2015 dune-scrape site
N_CEH36 = CEH36_N

MIN_OBS_SPLIT = 12

UPHILL_WELLS = [
    "ceh31",
    "wmc3", "nw6", "nw7",
    "ceh30", "ceh20", "ceh33",
    "ceh9", "ceh34",
    "ceh 1",
]

CONTROL_WELLS = ["nw1", "nw2", "nw11", "nw13", "wmc4", "D25", "WMC2"]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _find_well_col(well_name, df):
    norm = normalize_well_name(well_name)
    for c in df.columns:
        if normalize_well_name(c) == norm:
            return c
    return None


def _get_series(well_name, wells_clean, wells_ext):
    col = _find_well_col(well_name, wells_clean)
    if col is not None:
        return wells_clean[col]
    col = _find_well_col(well_name, wells_ext)
    if col is not None:
        return wells_ext[col]
    return None


def _fit_era(series, climate, start, end, intercept=True):
    """1.12.0 (D-332): Model B (free intercept, beta_3 bounded) by default;
    intercept=False is the Model A sensitivity (fixed datum DRAINAGE_DATUM)."""
    era_series = series.copy()
    era_series[(era_series.index < start) | (era_series.index >= end)] = np.nan
    return fit_ssm(era_series, climate, min_obs=MIN_OBS_SPLIT, intercept=intercept)


def _b3a(fit):
    """beta_3 of a Model A fit, NaN when the fit is missing."""
    return fit["beta_3_drainage"] if fit is not None else np.nan


def _well_distance(well_name, locs):
    norm = normalize_well_name(well_name)
    row = locs[locs["match"] == norm]
    if len(row) == 0:
        return np.nan
    return np.sqrt((row.iloc[0]["E"] - E_CEH36)**2 +
                   (row.iloc[0]["N"] - N_CEH36)**2)


def _well_cluster(well_name, master):
    norm = normalize_well_name(well_name)
    row = master[master["match"] == norm]
    if len(row) == 0:
        return -1
    return int(row.iloc[0]["Cluster"])


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def main():
    print("=" * 70)
    print("09b \u2014 Scraping Propagation Analysis")
    print("=" * 70)

    # 1. Load data
    phase(1, "Loading data")
    wells_clean = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells_ext   = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
    climate     = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    locs        = pd.read_csv(INT_LOCATIONS)
    master      = pd.read_csv(INT_MASTER_DATA)

    locs["match"]   = locs["Name"].apply(normalize_well_name)
    master["match"] = master["Name_Original"].apply(normalize_well_name)

    print(f"   Wells (clean): {wells_clean.shape[1]} columns")
    print(f"   Wells (extended): {wells_ext.shape[1]} columns")
    print(f"   Climate: {len(climate)} months")

    # 2. Fit split-window SSMs
    phase(2, "Fitting split-window SSMs")
    print(f"   Pre-scrape window:  start of record "
          f"\u2013 {SCRAPE_DATE.strftime('%b %Y')}")
    print(f"   Post-scrape window: {SCRAPE_DATE.strftime('%b %Y')} "
          f"\u2013 {FELL_DATE.strftime('%b %Y')}")

    all_wells = ["ceh36"] + UPHILL_WELLS + CONTROL_WELLS
    results = []

    for well_name in all_wells:
        series = _get_series(well_name, wells_clean, wells_ext)
        if series is None:
            warn(f"{well_name} not found in well data")
            continue

        pre  = _fit_era(series, climate,
                        pd.Timestamp("2005-01-01"), SCRAPE_DATE)
        post = _fit_era(series, climate,
                        SCRAPE_DATE, FELL_DATE)
        # Model A sensitivity (D-332): the same windows at the fixed datum
        pre_a  = _fit_era(series, climate, pd.Timestamp("2005-01-01"), SCRAPE_DATE, intercept=False)
        post_a = _fit_era(series, climate, SCRAPE_DATE, FELL_DATE, intercept=False)

        if pre is None or post is None:
            warn(f"{well_name} \u2014 insufficient data in one or both windows")
            continue

        dist    = _well_distance(well_name, locs)
        cluster = _well_cluster(well_name, master)
        role    = ("scraped" if well_name == "ceh36"
                   else "uphill" if well_name in UPHILL_WELLS
                   else "control")

        results.append({
            "well": well_name,
            "role": role,
            "cluster": cluster,
            "dist_m": dist,
            "pre_b1":  pre["beta_1_recharge"],
            "pre_b2":  pre["beta_2_atmospheric_draw"],
            "pre_b3":  pre["beta_3_drainage"],
            "pre_r2":  pre["R2"],
            "pre_n":   pre["n"],
            "post_b1": post["beta_1_recharge"],
            "post_b2": post["beta_2_atmospheric_draw"],
            "post_b3": post["beta_3_drainage"],
            "post_r2": post["R2"],
            "post_n":  post["n"],
            "raw_db1": post["beta_1_recharge"] - pre["beta_1_recharge"],
            "raw_db2": post["beta_2_atmospheric_draw"] - pre["beta_2_atmospheric_draw"],
            "raw_db3": post["beta_3_drainage"] - pre["beta_3_drainage"],
            # 1.12.0 (D-332): Model B's intercept and bound flag, and Model A's beta_3 beside it
            "pre_alpha":  pre["alpha"],
            "post_alpha": post["alpha"],
            "raw_dalpha": post["alpha"] - pre["alpha"],
            "pre_b3_bound_binds":  bool(pre.get("beta_3_bound_binds", False)),
            "post_b3_bound_binds": bool(post.get("beta_3_bound_binds", False)),
            "pre_b3_model_a":  _b3a(pre_a),
            "post_b3_model_a": _b3a(post_a),
            "raw_db3_model_a": _b3a(post_a) - _b3a(pre_a),
        })

    df = pd.DataFrame(results)
    print(f"   Fitted {len(df)} wells "
          f"({df['role'].value_counts().to_dict()})")

    # 3. BACI correction
    phase(3, "Computing BACI correction")
    ctrl = df[df["role"] == "control"]
    ctrl_db1 = ctrl["raw_db1"].mean()
    ctrl_db2 = ctrl["raw_db2"].mean()
    ctrl_db3 = ctrl["raw_db3"].mean()
    ctrl_dalpha = ctrl["raw_dalpha"].mean()
    ctrl_db3_a = ctrl["raw_db3_model_a"].mean()

    print(f"   Control centroid raw shifts (n={len(ctrl)} wells):")
    print(f"     \u0394\u03b2\u2081 = {ctrl_db1:+.3f}")
    print(f"     \u0394\u03b2\u2082 = {ctrl_db2:+.3f}")
    print(f"     \u0394\u03b2\u2083 = {ctrl_db3:+.4f} "
          f"({ctrl_db3*1000:+.1f} \u00d7 10\u207b\u00b3)")

    df["baci_db1"] = df["raw_db1"] - ctrl_db1
    df["baci_db2"] = df["raw_db2"] - ctrl_db2
    df["baci_db3"] = df["raw_db3"] - ctrl_db3
    df["baci_dalpha"] = df["raw_dalpha"] - ctrl_dalpha
    # Per-well percentage, on the same convention as the centroid rows below.
    df["baci_db3_pct"] = np.where(df["pre_b3"].abs() > 1e-6,
                                  df["baci_db3"] / df["pre_b3"].abs() * 100, np.nan)
    df["baci_db3_model_a"] = df["raw_db3_model_a"] - ctrl_db3_a
    df["baci_db3_pct_model_a"] = np.where(df["pre_b3_model_a"].abs() > 1e-6,
                                          df["baci_db3_model_a"] / df["pre_b3_model_a"].abs() * 100, np.nan)
    print(f"   Model B fits with beta_3 at the bound: "
          f"{int(df['pre_b3_bound_binds'].sum() + df['post_b3_bound_binds'].sum())} of {2 * len(df)}")

    uphill = df[df["role"] == "uphill"].sort_values("dist_m")
    print("\n   Uphill wells (BACI-corrected):")
    for _, r in uphill.iterrows():
        print(f"     {r['well']:8s}  C{r['cluster']}  "
              f"{r['dist_m']:5.0f}m  "
              f"\u0394\u03b2\u2083={r['baci_db3']*1000:+5.1f}"
              f"\u00d710\u207b\u00b3  "
              f"n_pre={r['pre_n']:.0f}")

    # 4. Centroid summaries
    phase(4, "Computing centroid summaries")
    centroid_groups = {
        "CEH36 (scraped)":
            df[df["role"] == "scraped"],
        "C3+CEH31 (non-forest uphill)":
            uphill[uphill["cluster"].isin([3, 5])],
        "C4 (forest uphill)":
            uphill[uphill["cluster"] == 4],
        "All uphill":
            uphill,
    }

    centroid_rows = []
    for group_name, group_df in centroid_groups.items():
        if len(group_df) == 0:
            continue

        series_list = [_get_series(w, wells_clean, wells_ext)
                       for w in group_df["well"]]
        series_list = [s for s in series_list if s is not None]
        centroid_ts = pd.concat(
            series_list, axis=1, sort=True).mean(axis=1)

        pre  = _fit_era(centroid_ts, climate,
                        pd.Timestamp("2005-01-01"), SCRAPE_DATE)
        post = _fit_era(centroid_ts, climate,
                        SCRAPE_DATE, FELL_DATE)
        pre_a  = _fit_era(centroid_ts, climate, pd.Timestamp("2005-01-01"), SCRAPE_DATE, intercept=False)
        post_a = _fit_era(centroid_ts, climate, SCRAPE_DATE, FELL_DATE, intercept=False)

        if pre and post:
            db1 = (post["beta_1_recharge"] - pre["beta_1_recharge"]) - ctrl_db1
            db2 = (post["beta_2_atmospheric_draw"] - pre["beta_2_atmospheric_draw"]) - ctrl_db2
            db3 = (post["beta_3_drainage"] - pre["beta_3_drainage"]) - ctrl_db3
            pct_b3 = (db3 / abs(pre["beta_3_drainage"]) * 100
                      if abs(pre["beta_3_drainage"]) > 1e-6 else np.nan)
            dalpha = (post["alpha"] - pre["alpha"]) - ctrl_dalpha
            db3_a = (_b3a(post_a) - _b3a(pre_a)) - ctrl_db3_a
            pct_b3_a = (db3_a / abs(_b3a(pre_a)) * 100
                        if abs(_b3a(pre_a)) > 1e-6 else np.nan)

            centroid_rows.append({
                "group":        group_name,
                "n_wells":      len(group_df),
                "pre_b1":       pre["beta_1_recharge"],
                "pre_b2":       pre["beta_2_atmospheric_draw"],
                "pre_b3":       pre["beta_3_drainage"],
                "post_b1":      post["beta_1_recharge"],
                "post_b2":      post["beta_2_atmospheric_draw"],
                "post_b3":      post["beta_3_drainage"],
                "pre_r2":       pre["R2"],
                "post_r2":      post["R2"],
                "baci_db1":     db1,
                "baci_db2":     db2,
                "baci_db3":     db3,
                "baci_db3_pct": pct_b3,
                # 1.12.0 (D-332)
                "pre_alpha":    pre["alpha"],
                "post_alpha":   post["alpha"],
                "baci_dalpha":  dalpha,
                "pre_b3_bound_binds":  bool(pre.get("beta_3_bound_binds", False)),
                "post_b3_bound_binds": bool(post.get("beta_3_bound_binds", False)),
                "pre_b3_model_a":  _b3a(pre_a),
                "post_b3_model_a": _b3a(post_a),
                "baci_db3_model_a": db3_a,
                "baci_db3_pct_model_a": pct_b3_a,
            })

            print(f"   {group_name} ({len(group_df)} wells):")
            print(f"     BACI \u0394\u03b2\u2081={db1:+.3f}  "
                  f"\u0394\u03b2\u2082={db2:+.3f}  "
                  f"\u0394\u03b2\u2083={db3*1000:+.1f}\u00d710\u207b\u00b3 "
                  f"({pct_b3:+.0f}%)")

    centroids_df = pd.DataFrame(centroid_rows)

    # 5. Export CSVs
    phase(5, "Exporting CSVs")
    df.to_csv(OUT_09B_INDIVIDUAL, index=False, float_format="%.4f")
    print(f"   \u2192 {OUT_09B_INDIVIDUAL.name}")
    centroids_df.to_csv(OUT_09B_CENTROIDS, index=False, float_format="%.4f")
    print(f"   \u2192 {OUT_09B_CENTROIDS.name}")
    rr = ReportNumbers()
    _c36 = df.loc[df["well"] == "ceh36"].iloc[0]
    rr.add("scrape_window_months_post", int(_c36["post_n"]), unit="months",
           era=f"{SCRAPE_DATE.strftime('%b %Y')}-{FELL_DATE.strftime('%b %Y')}",
           note="fitted months in the post-scrape window at CEH36 (scrape to clearfell): "
                "the 'N-month post-scraping record' the documents quote")
    rr.add("scrape_window_months_pre", int(_c36["pre_n"]), unit="months",
           era=f"record start-{SCRAPE_DATE.strftime('%b %Y')}",
           note="fitted months in the pre-scrape window at CEH36")
    rr.add("scrape_propagation_n_wells", int(len(df)), unit="count",
           note="CEH36, the uphill transect and the controls fitted in both windows")
    rr.add("scrape_propagation_n_fits_model_b_bound_binds",
           int(df["pre_b3_bound_binds"].sum() + df["post_b3_bound_binds"].sum()), unit="count",
           note="split-window Model B fits (pre and post, over scrape_propagation_n_wells wells) whose beta_3 "
                "sits at the lower bound MODEL_B_BETA3_MIN (kept; D-332)")
    # The near-band propagation test (report9 §4.5.5), on the unrounded frame.
    near = df[(df["role"] == "uphill") & (df["dist_m"] <= SCRAPE_PROPAGATION_NEAR_M)]
    band = f"uphill wells within {SCRAPE_PROPAGATION_NEAR_M:.0f} m of CEH36"
    rr.add("scrape_propagation_near_n_wells", int(len(near)), unit="count", note=band)
    # 1.12.0 (D-332): the headline keys are Model B; the same test on Model A's beta_3 is _model_a.
    _up = df[df["role"] == "uphill"]
    # 1.14.0 (D-333): the two forms disagree in sign here, so the test is reported as form-dependent, not established.
    _fd = "; form-dependent (Model A and Model B disagree in sign), not established (D-333)"
    for _col, _sfx, _form in (("baci_db3", "", "Model B" + _fd), ("baci_db3_model_a", "_model_a", "Model A sensitivity" + _fd)):
        _nb = near[_col].dropna()
        rr.add(f"scrape_propagation_near_n_positive{_sfx}", int((_nb > 0).sum()),
               unit="count", note=f"{band} with a positive BACI-corrected delta-beta3 ({_form})")
        rr.add(f"scrape_propagation_near_db3_mean{_sfx}", float(_nb.mean()),
               unit="per month", note=f"mean BACI-corrected delta-beta3, {band} ({_form})")
        if len(_nb) >= 3:
            _t = _stats.ttest_1samp(_nb, 0.0)
            rr.add(f"scrape_propagation_near_db3_t{_sfx}", float(_t.statistic), unit="-",
                   note=f"one-sample t against zero, df = {len(_nb) - 1} ({_form})")
            rr.add(f"scrape_propagation_near_db3_p{_sfx}", float(_t.pvalue), unit="-",
                   note=f"two-sided p of the one-sample t ({_form})")
        else:
            warn(f"only {len(_nb)} wells in the near band - {_form} t-test not written")
        # T-108: distance decay across the uphill wells (report9 4.11).
        _ub = _up[["dist_m", _col]].dropna()
        if len(_ub) >= 3:
            _pr = _stats.pearsonr(_ub["dist_m"], _ub[_col])
            _n = (f"Pearson r of BACI-corrected delta-beta3 against distance from CEH36, uphill wells "
                  f"(n = {len(_ub)}; {_form})")
            rr.add(f"scrape_propagation_uphill_dist_r{_sfx}", float(_pr[0]), unit="-", note=_n)
            rr.add(f"scrape_propagation_uphill_dist_p{_sfx}", float(_pr[1]), unit="-", note="two-sided p of " + _n)
    if len(_up) >= 3:
        rr.add("scrape_propagation_uphill_n_wells", int(len(_up)), unit="count", note="uphill wells in the distance test")
    # Emit-first (report9): the span of the uphill transect, nearest and farthest well from CEH36.
    if len(_up):
        rr.add("scrape_propagation_uphill_dist_min_m", float(_up["dist_m"].min()), unit="m",
               note="distance from CEH36 to the nearest uphill well of the propagation transect "
                    "(minimum of dist_m over role 'uphill'); report9 quotes it to the nearest 10 m")
        rr.add("scrape_propagation_uphill_dist_max_m", float(_up["dist_m"].max()), unit="m",
               note="distance from CEH36 to the farthest uphill well of the propagation transect "
                    "(maximum of dist_m over role 'uphill'); report9 quotes it to the nearest 10 m")
    # 1.15.0 (T-209, D-333): the 'Scraping (nearby)' bars - a BACI delta-beta_3 of split-window refits propagated
    # through 1/beta_3 - are dropped from 09b_04, with their held-at-bound count and the D-333 withdrawal count.
    # The scrape's detection is the paired contrast at CEH36 (Script 09a); its propagation is not quantified.
    n_rr = rr.save(OUT_09B_REPORT_NUMBERS)
    print(f"   \u2192 {OUT_09B_REPORT_NUMBERS.name} ({n_rr} rows)")

    # 6. Equilibration figure
    phase(6, "Generating CEH36 equilibration figure")
    _plot_equilibration(wells_clean)
    print(f"   \u2192 {OUT_09B_TRAJECTORY.name}")

    # 7. Scenario comparison
    phase(7, "Generating scenario comparison figure")
    _plot_scenario_comparison(centroids_df)

    # 8. Summer minimum scenario comparison
    _summer_scenario(wells_clean, wells_ext, climate)

    print("\nDone.")


# ============================================================================
# FIGURE: CEH36 POST-SCRAPING TRAJECTORY
# ============================================================================

def _plot_equilibration(wells_clean):
    """Plot climate-corrected water table anomaly for CEH36 vs CEH4."""
    ctrl_series = []
    for w in CONTROL_WELLS:
        col = _find_well_col(w, wells_clean)
        if col is not None:
            ctrl_series.append(wells_clean[col])
    ctrl_centroid = pd.concat(ctrl_series, axis=1, sort=True).mean(axis=1)

    def _make_cc(well_col):
        s = well_col.dropna()
        common = s.index.intersection(ctrl_centroid.dropna().index)
        if len(common) == 0:
            return None
        s_c = s[common]
        ctrl_c = ctrl_centroid[common]
        pre = common[common < SCRAPE_DATE]
        if len(pre) < 12:
            return None
        return ((s_c - s_c[pre].mean()) - (ctrl_c - ctrl_c[pre].mean()))

    ceh36_col = _find_well_col("ceh36", wells_clean)
    ceh4_col  = _find_well_col("ceh4", wells_clean)
    if ceh36_col is None or ceh4_col is None:
        warn("CEH36 or CEH4 not found \u2014 skipping trajectory figure")
        return

    ceh36_cc = _make_cc(wells_clean[ceh36_col])
    ceh4_cc  = _make_cc(wells_clean[ceh4_col])
    if ceh36_cc is None or ceh4_cc is None:
        warn("insufficient pre-scraping data \u2014 skipping trajectory figure")
        return

    ceh36_roll = (ceh36_cc.rolling(12, center=True, min_periods=6).mean() * 1000)
    ceh4_roll  = (ceh4_cc.rolling(12, center=True, min_periods=6).mean() * 1000)

    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.plot(ceh36_roll.index, ceh36_roll.values, color="#d62728", linewidth=3.0,
            label="CEH36 (scraped Apr 2015)", zorder=5)
    ax.plot(ceh4_roll.index, ceh4_roll.values, color="#ff7f0e", linewidth=2.5,
            label="CEH4 (unscraped control, 99 m away)", alpha=0.8, zorder=4)
    ax.axhline(0, color="black", linewidth=1.0, label="Pre-scraping baseline")
    ax.axvline(SCRAPE_DATE, color="#DAA520", linewidth=2.5, linestyle="--",
               label="Scraping (Apr 2015)")
    ax.axvline(FELL_DATE, color="brown", linewidth=2.0, linestyle="--",
               label="Clearfell (Dec 2017)", alpha=0.7)
    ax.axvline(SCRAPE2_DATE, color="#e7298a", linewidth=2.0, linestyle="-.",
               label="Re-scrape (Oct 2023)", alpha=0.8)

    ax.annotate("Head surplus\nequilibrates\nvia drainage (\u03b2\u2083)",
                xy=(pd.Timestamp("2016-06"), 80), fontsize=14, fontweight="bold",
                color="#228B22", ha="center", va="bottom")
    ax.annotate("", xy=(pd.Timestamp("2017-09"), 20),
                xytext=(pd.Timestamp("2015-09"), 100),
                arrowprops=dict(arrowstyle="->", color="#228B22", lw=2.5,
                                connectionstyle="arc3,rad=-0.2"))
    ax.annotate("New equilibrium reached;\nresidual decline = coastal\nerosion signal",
                xy=(pd.Timestamp("2022-06"), -30), fontsize=14, fontweight="bold",
                color="#d62728", ha="center", va="top")

    ceh4_late = ceh4_roll["2023-01":"2023-06"]
    ceh4_y = ceh4_late.mean() if len(ceh4_late) > 0 else -350
    ax.annotate("CEH4: steady coastal\nerosion decline\n(no scraping protection)",
                xy=(pd.Timestamp("2023-01"), ceh4_y),
                xytext=(pd.Timestamp("2020-01"), -340),
                fontsize=13, fontweight="bold", color="#ff7f0e",
                arrowprops=dict(arrowstyle="->", color="#ff7f0e", lw=2.0))

    ax.text(0.01, 0.97, "\u2191 shallower (wetter)", transform=ax.transAxes,
            fontsize=12, color="#228B22", fontweight="bold", va="top")
    ax.text(0.01, 0.03, "\u2193 deeper (drier)", transform=ax.transAxes,
            fontsize=12, color="#d62728", fontweight="bold", va="bottom")

    ax.set_xlabel("Date", fontsize=15)
    ax.set_ylabel("Change in water table depth\nrelative to pre-scraping mean (mm)\n"
                  "(climate-corrected, 12-month rolling mean)", fontsize=14)
    ax.set_title("Observed water table response to scraping at CEH36\n"
                 "Head change relative to pre-2015 baseline, "
                 "corrected for climate using distant C3 wells",
                 fontsize=16, fontweight="bold")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(fontsize=12, loc="upper right")
    ax.tick_params(labelsize=13)
    ax.set_xlim(pd.Timestamp("2011-01-01"), pd.Timestamp("2026-03-01"))
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    render_figure(fig, OUT_09B_TRAJECTORY, format="jpeg",
                  pil_kwargs={"quality": 85})
    plt.close(fig)


# ============================================================================
# FIGURE 4 — SCENARIO COMPARISON BAR CHART
# ============================================================================

# 1.15.0 (T-209): GROUND_LOWERING and FRAC_AFFECTED went with the 'Scraping (nearby)' bars.


def _plot_scenario_comparison(centroids_df, dpi=200):
    """
    Grouped bar chart: forest management and climate scenarios.
    Values from compute_scenario_bars() (single source of truth).
    1.15.0 (T-209): the 'Scraping (nearby)' bars are gone (propagation not quantified, D-333); the clearfell
    and thinning bars return a share f of the interception calibrated on the observed BACI step.
    """
    from utils.scraping_common import compute_scenario_bars_from_params

    clusters = list(_GROUP_KEYS)
    cluster_labels = [_GROUP_TICKS.get(c, c) for c in clusters]

    # Non-scraping scenarios from the consolidated pipeline params
    base_scenarios, _, _, _ = compute_scenario_bars_from_params()

    colour_map = {
        "Clearfell": "#8B4513", "Thinning 50%": "#D2691E",
        "Broadleaf": "#228B22",
        "Climate dry": "#FF6347", "Climate wet": "#4169E1",
    }
    bw_colour_map = {
        "Clearfell": "#333333", "Thinning 50%": "#666666",
        "Broadleaf": "#999999",
        "Climate dry": "#444444", "Climate wet": "#cccccc",
    }
    bw_hatch_map = {
        "Clearfell": "xxx", "Thinning 50%": "///",
        "Broadleaf": "...",
        "Climate dry": "\\\\\\", "Climate wet": "",
    }

    # Build ordered scenario dict: {name: (vals_dict, colour, hatch)}
    scenarios = {}
    for s_name in ["Clearfell", "Thinning 50%", "Broadleaf"]:
        if s_name in base_scenarios:
            scenarios[s_name] = (base_scenarios[s_name],
                                 colour_map.get(s_name, "#999"), None)
    for s_name in ["Climate dry", "Climate wet"]:
        if s_name in base_scenarios:
            scenarios[s_name] = (base_scenarios[s_name],
                                 colour_map.get(s_name, "#999"), None)

    n_scen = len(scenarios)
    x = np.arange(len(clusters))
    width = 0.15
    offsets = np.linspace(-(n_scen - 1) / 2 * width,
                           (n_scen - 1) / 2 * width, n_scen)

    fig, ax = plt.subplots(1, 1, figsize=(13, 7))

    for i, (scenario, (vals_dict, colour, hatch)) in enumerate(
            scenarios.items()):
        vals = [vals_dict.get(c, 0) for c in clusters]
        _col = bw_colour_map.get(scenario, colour) if BW_MODE else colour
        _hatch = bw_hatch_map.get(scenario, hatch or "") if BW_MODE else hatch
        _lab = {"Clearfell": "Clearfell (flux sensitivity)",
                "Thinning 50%": "Thinning 50% (at most half)"}.get(scenario, scenario)
        ax.bar(x + offsets[i], vals, width, label=_lab, color=_col,
               edgecolor="black", linewidth=0.5, alpha=0.85, hatch=_hatch)

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cluster_labels, fontsize=14)
    ax.set_ylabel("\u0394 volumetric water table\n"
                  "(mm water equiv. / month)", fontsize=15)
    ax.tick_params(axis="y", labelsize=13)
    ax.set_title(
        "Scenario comparison: forest management and climate (k = 5)\n"
        "Volumetric using WTF-derived, interception-corrected Sy",
        fontsize=15, fontweight="bold")

    # 1.15.0 (T-209): one note, below the axes, clear of the bars
    ax.text(0.0, -0.20,
            "Clearfell: the share of the canopy's interception returned that reproduces the observed BACI step at "
            "the felled well (winter); thinning at most half of it.\n"
            "Scraping is not shown: its effect is detected at CEH36 (paired contrast) and its spread to other "
            "wells is not quantified.",
            transform=ax.transAxes, fontsize=10, va="top", ha="left", color="#444444")

    ax.legend(fontsize=10, loc="upper left", bbox_to_anchor=(1.01, 1.0))   # 1.14.0: outside the axes, off the bars
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    fig.subplots_adjust(bottom=0.24)

    render_figure(fig, OUT_09B_SCENARIO, format="jpeg",
                  pil_kwargs={"quality": 85})
    plt.close(fig)

    # Export CSV
    rows = []
    for scenario, (vals_dict, _, _) in scenarios.items():
        for c in clusters:
            rows.append({"Scenario": scenario, "Cluster": c,
                         "Delta_vol_mm_per_month": round(vals_dict.get(c, 0), 1)})
    pd.DataFrame(rows).to_csv(OUT_09B_SCENARIO_CSV, index=False,
                              float_format="%.1f")
    print(f"   \u2192 {OUT_09B_SCENARIO.name}")
    print(f"   \u2192 {OUT_09B_SCENARIO_CSV.name}")


def _summer_scenario(wells_clean, wells_ext, climate):
    """Volumetric summer-forcing scenario figure: empirical BACI scraping +
    SSM equilibrium forestry/climate bars, all on one volumetric scale.

    Re-based 2026-07-02 (v1.5.0): the previous version converted the monthly
    volumetric flux to a summer-MINIMUM depth via ÷Sy × a mean->minimum
    amplification slope. The SSM equilibrium framework carries no transient
    and cannot resolve a true summer minimum, and the amplification slope is
    least reliable at the forest (the winter-rise/summer-stagnation paradox).
    The amplification step is removed: every bar is now the equilibrium
    volumetric response (mm water-equiv / month), matching Script 09d and the
    monthly figure 09b-04. The scraping bar is the observed BACI shift
    rendered on the same volumetric axis (× cluster Sy)."""
    phase(8, "Generating volumetric summer-forcing scenario comparison")
    SUMMER = [6, 7, 8, 9]
    FELLING_YEAR = 2018
    SCRAPE_YEAR = 2015

    new = [c for c in wells_ext.columns if c not in wells_clean.columns]
    wells = pd.concat([wells_clean, wells_ext[new]], axis=1, sort=False)
    wells.columns = wells.columns.str.lower().str.replace(' ', '')

    clusters = list(_GROUP_KEYS)

    # Cluster Sy (for rendering the empirical scrape head shift on the
    # volumetric axis, and consistency with the monthly figure).
    from utils.scraping_common import scenario_cluster_sy
    SY_FALLBACK = 0.20
    sy_by_cluster = {}
    if OUT_17_SY_TABLE.exists():
        sy_df = pd.read_csv(OUT_17_SY_TABLE)
        sy_by_cluster = scenario_cluster_sy(
            sy_df, clusters=tuple(clusters), fallback=SY_FALLBACK)
        if sy_by_cluster:
            print("   Sy from Script 17: " +
                  ", ".join(f"{c}={v:.3f}" for c, v in sy_by_cluster.items()))
    else:
        warn(f"{OUT_17_SY_TABLE.name} not found \u2014falling back to Sy={SY_FALLBACK}")

    def _annual_summer_min(series):
        mins = {}
        for yr in range(2006, 2026):
            mask = (series.index.year == yr) & (series.index.month.isin(SUMMER))
            s = series[mask].dropna()
            if len(s) >= 2:
                mins[yr] = float(s.min())
        return mins

    # Scraping: CEH36 vs CEH18 observed BACI head shift, rendered volumetric
    scraping_shift_mm = 0.0     # head shift (mm)
    scraping_vol_c5 = 0.0       # volumetric equivalent (mm w.e./month) in C3f (group 5, key "C5")
    if 'ceh36' in wells.columns and 'ceh18' in wells.columns:
        m36 = _annual_summer_min(wells['ceh36'])
        m18 = _annual_summer_min(wells['ceh18'])
        common = sorted(set(m36) & set(m18))
        gap = pd.Series({yr: m36[yr] - m18[yr] for yr in common})
        pre = gap[gap.index < SCRAPE_YEAR]
        post = gap[(gap.index >= SCRAPE_YEAR) & (gap.index < FELLING_YEAR)]
        if len(pre) >= 2 and len(post) >= 2:
            shift = post.mean() - pre.mean()
            _, p_val = _stats.ttest_ind(post.values, pre.values, equal_var=False)
            scraping_shift_mm = shift * 1000
            scraping_vol_c5 = scraping_shift_mm * sy_by_cluster.get('C5', SY_FALLBACK)
            print(f"   Scraping (CEH36 vs CEH18): {scraping_shift_mm:+.0f} mm head "
                  f"({scraping_vol_c5:+.0f} mm w.e./month volumetric)  p = {p_val:.3f}")

    # Forestry + climate scenarios: equilibrium volumetric bars taken DIRECTLY
    # from the monthly CSV (09b-04). No ÷Sy, no amplification.
    summer_data = {
        'Scraping\n(CEH36-type)': {'C1': 0, 'C2': 0, 'C3': 0, 'C4': 0,
                                    'C5': round(scraping_vol_c5, 1)},
    }

    scen_csv = OUT_09B_SCENARIO_CSV
    if scen_csv.exists():
        scen = pd.read_csv(scen_csv)
        for scenario in ['Clearfell', 'Thinning 50%', 'Broadleaf',
                         'Climate dry', 'Climate wet']:
            summer_data[scenario] = {}
            for c in clusters:
                row = scen[(scen['Scenario'] == scenario) & (scen['Cluster'] == c)]
                if not row.empty:
                    summer_data[scenario][c] = round(
                        float(row['Delta_vol_mm_per_month'].iloc[0]), 1)
                else:
                    summer_data[scenario][c] = 0
        for s in ['Clearfell', 'Thinning 50%', 'Broadleaf']:
            if s in summer_data:
                print(f"   {s} volumetric: "
                      f"C4={summer_data[s].get('C4', 0):+.1f}  "
                      f"C3f={summer_data[s].get('C5', 0):+.1f} mm w.e./month")
    else:
        warn(f"{scen_csv.name} not found \u2014forestry bars set to zero")
        for s in ['Clearfell', 'Thinning 50%', 'Broadleaf',
                   'Climate dry', 'Climate wet']:
            summer_data[s] = {c: 0 for c in clusters}

    # Figure
    cluster_labels = [_GROUP_TICKS.get(c, c) for c in clusters]
    colours = {
        'Clearfell': '#8B6914', 'Thinning 50%': '#D2691E',
        'Broadleaf': '#228B22', 'Scraping\n(CEH36-type)': '#DAA520',
        'Climate dry': '#E8726E', 'Climate wet': '#5B9BD5',
    }
    bw_colours = {
        'Clearfell': '#333333', 'Thinning 50%': '#666666',
        'Broadleaf': '#999999', 'Scraping\n(CEH36-type)': '#bbbbbb',
        'Climate dry': '#444444', 'Climate wet': '#cccccc',
    }
    bw_hatches = {
        'Clearfell': 'xxx', 'Thinning 50%': '///',
        'Broadleaf': '...', 'Scraping\n(CEH36-type)': '///',
        'Climate dry': '\\\\\\', 'Climate wet': '',
    }
    hatches = {'Scraping\n(CEH36-type)': '///'}
    scenarios_order = [s for s in ['Clearfell', 'Thinning 50%', 'Broadleaf',
                                    'Scraping\n(CEH36-type)', 'Climate dry', 'Climate wet']
                       if s in summer_data]

    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    n_sc = len(scenarios_order)
    bw = 0.8 / n_sc
    x = np.arange(len(clusters))

    for i, s_name in enumerate(scenarios_order):
        vals = [summer_data[s_name].get(c, 0) for c in clusters]
        offset = (i - n_sc / 2 + 0.5) * bw
        _col = bw_colours.get(s_name, '#999') if BW_MODE else colours.get(s_name, '#999')
        _hatch = bw_hatches.get(s_name, '') if BW_MODE else hatches.get(s_name, '')
        ax.bar(x + offset, vals, bw * 0.9,
               color=_col,
               edgecolor='black',
               linewidth=0.8 if _hatch else 0.5,
               hatch=_hatch, alpha=0.85, label=s_name, zorder=3)
        for j, v in enumerate(vals):
            if abs(v) > 5:
                ax.text(x[j] + offset, v + (1.5 if v > 0 else -1.5),
                        f'{v:+.0f}', ha='center',
                        va='bottom' if v > 0 else 'top',
                        fontsize=7.5, fontweight='bold', color='#333')

    ax.axhline(0, color='black', lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cluster_labels, fontsize=11)
    ax.set_ylabel('\u0394 volumetric water table (mm water equiv. / month)', fontsize=12)
    ax.set_title(
        'Volumetric scenario comparison: forest management, scraping, and climate (five groups)\n'
        'All bars: SSM equilibrium volumetric response  |  scraping = observed BACI \u00d7 Sy',
        fontsize=12, fontweight='bold')
    ax.legend(fontsize=9, loc='upper left', bbox_to_anchor=(1.01, 1.0))   # 1.14.0: outside the axes, off the bars
    ax.grid(axis='y', alpha=0.25, ls='--')
    for sp in ['top', 'right']:
        ax.spines[sp].set_visible(False)
    ax.text(0.02, -0.14,
            f'Scraping: empirical BACI at scraped site (CEH36 vs CEH18, '
            f'{scraping_shift_mm:+.0f} mm head, rendered volumetric \u00d7 C3f Sy). '
            f'Benefit is local.  '
            'Forest management & climate: SSM equilibrium volumetric bars from '
            'the monthly figure (09b-04).\n'
            'Bars are volumetric (mm water-equiv. / month); a head-change '
            'equivalent needs division by an appropriate (uncertain) Sy and is '
            'approximate. Not a summer minimum \u2014 the equilibrium framework '
            'cannot resolve the transient minimum.',
            transform=ax.transAxes, fontsize=7.5, ha='left', va='top',
            color='#555', style='italic')
    plt.tight_layout()
    fig.subplots_adjust(bottom=0.20)
    render_figure(plt.gcf(), OUT_09B_SUMMER_SCENARIO)
    plt.close()
    print(f"   \u2192 {OUT_09B_SUMMER_SCENARIO.name}")

    # Export CSV
    rows = []
    for s_name in scenarios_order:
        for c in clusters:
            rows.append({'Scenario': s_name.replace('\n', ' '),
                         'Cluster': c,
                         'Delta_vol_summer_mm_per_month': summer_data[s_name].get(c, 0)})
    pd.DataFrame(rows).to_csv(OUT_09B_SUMMER_SCENARIO_CSV, index=False)
    print(f"   \u2192 {OUT_09B_SUMMER_SCENARIO_CSV.name}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
