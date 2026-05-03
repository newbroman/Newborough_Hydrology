"""
==========================================================================
09b \u2014 SCRAPING PROPAGATION ANALYSIS
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
        09b_01_individual_well_baci.csv   \u2014 per-well BACI-corrected shifts
        09b_02_centroid_summaries.csv      \u2014 group centroid BACI shifts
    Figures:
        09b_03_ceh36_equilibration.jpg     \u2014 CEH36 post-scraping trajectory
        09b_04_scenario_comparison.jpg     \u2014 scenario bar chart with scraping

Reads:
    outputs/01_wells_clean.csv
    outputs/01_wells_extended.csv
    outputs/01_climate.csv
    outputs/01_locations.csv
    outputs/03_master_data.csv
==========================================================================
"""

__version__ = "1.0.0"  # Hollingham (2026)

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(
    _os.path.abspath(__file__)))); del _sys, _os

from utils.paths import (
    INT_WELLS_CLEAN, INT_WELLS_EXTENDED, INT_CLIMATE,
    INT_LOCATIONS, INT_MASTER_DATA, DIR_09,
    OUT_09B_INDIVIDUAL, OUT_09B_CENTROIDS, OUT_09B_TRAJECTORY,
)

# Output paths for scenario comparison (not yet in paths.py;
# defined here until paths.py is updated)
OUT_09B_SCENARIO     = DIR_09 / "09b_04_scenario_comparison.jpg"
OUT_09B_SCENARIO_CSV = DIR_09 / "09b_04_scenario_comparison.csv"
from utils.config import DRAINAGE_DATUM, HEADLINE_LAG
from utils.model_utils import fit_ssm
from utils.data_utils import normalize_well_name

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path


# ============================================================================
# KEY NAME COMPATIBILITY
# ============================================================================
# model_utils.fit_ssm() may return short keys (beta_1, beta_2, beta_3)
# or long keys (beta_1_recharge, beta_2_atmospheric_draw, beta_3_drainage)
# depending on the version. This helper normalises to short names.

def _get_b(result, param):
    """Get SSM coefficient from fit_ssm result, handling both key formats."""
    _KEY_MAP = {
        "b1": ["beta_1_recharge", "beta_1"],
        "b2": ["beta_2_atmospheric_draw", "beta_2"],
        "b3": ["beta_3_drainage", "beta_3"],
    }
    for key in _KEY_MAP[param]:
        if key in result:
            return result[key]
    raise KeyError(f"Cannot find {param} in fit_ssm result: {list(result.keys())}")


# ============================================================================
# CONSTANTS
# ============================================================================
SCRAPE_DATE  = pd.Timestamp("2015-04-01")
FELL_DATE    = pd.Timestamp("2017-12-01")
SCRAPE2_DATE = pd.Timestamp("2023-10-01")

# CEH36 coordinates (scraping site)
E_CEH36 = 241161.0
N_CEH36 = 363306.0

# Minimum observations for split-window SSM fit.
# The post-scraping/pre-felling window is only 31 months, so we
# cannot use the default MIN_OBS = 30 from model_utils.
MIN_OBS_SPLIT = 12

# Wells north/northwest (uphill) of CEH36, directionally correct for
# groundwater propagation into the forest interior.
# Outer C5 coastal wells (NW9, CEH16, CEH19, CEH17) excluded \u2014
# western coastal boundary confound (see SCRAPING_PROPAGATION_SUMMARY.md).
# FE wells and LIS1 excluded \u2014 no pre-scraping data.
UPHILL_WELLS = [
    "ceh31",                          # C5 inner (875 m from W coast)
    "wmc3", "nw6", "nw7",            # C3
    "ceh30", "ceh20", "ceh33",        # C4
    "ceh9", "ceh39", "ceh34",         # C3 / C4
    "ceh 1",                          # C3
]

# Distant C3 control wells (850\u20131100 m from CEH36).
# Well beyond expected scraping influence; used for BACI correction.
CONTROL_WELLS = ["nw1", "nw2", "nw11", "nw13", "wmc4", "D25", "WMC2"]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _find_well_col(well_name, df):
    """Find the column name in a DataFrame matching a well name."""
    norm = normalize_well_name(well_name)
    for c in df.columns:
        if normalize_well_name(c) == norm:
            return c
    return None


def _get_series(well_name, wells_clean, wells_ext):
    """Get a well series, preferring clean network over extended."""
    col = _find_well_col(well_name, wells_clean)
    if col is not None:
        return wells_clean[col]
    col = _find_well_col(well_name, wells_ext)
    if col is not None:
        return wells_ext[col]
    return None


def _fit_era(series, climate, start, end):
    """
    Fit SSM to a well series within a date range.

    Masks values outside [start, end) to NaN so that fit_ssm() only
    sees the target window. Uses model_utils.fit_ssm() for consistency
    with Script 03 and the rest of the pipeline.
    """
    era_series = series.copy()
    era_series[(era_series.index < start) | (era_series.index >= end)] = np.nan
    return fit_ssm(era_series, climate, min_obs=MIN_OBS_SPLIT)


def _well_distance(well_name, locs):
    """Compute Euclidean distance from CEH36 for a well."""
    norm = normalize_well_name(well_name)
    row = locs[locs["match"] == norm]
    if len(row) == 0:
        return np.nan
    return np.sqrt((row.iloc[0]["E"] - E_CEH36)**2 +
                   (row.iloc[0]["N"] - N_CEH36)**2)


def _well_cluster(well_name, master):
    """Get cluster assignment for a well from the master data."""
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

    # \u2500\u2500 1. Load data \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n1. Loading data...")
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

    # \u2500\u2500 2. Fit split-window SSMs \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n2. Fitting split-window SSMs...")
    print(f"   Pre-scrape window:  start of record "
          f"\u2013 {SCRAPE_DATE.strftime('%b %Y')}")
    print(f"   Post-scrape window: {SCRAPE_DATE.strftime('%b %Y')} "
          f"\u2013 {FELL_DATE.strftime('%b %Y')}")

    all_wells = ["ceh36"] + UPHILL_WELLS + CONTROL_WELLS
    results = []

    for well_name in all_wells:
        series = _get_series(well_name, wells_clean, wells_ext)
        if series is None:
            print(f"   WARNING: {well_name} not found in well data")
            continue

        pre  = _fit_era(series, climate,
                        pd.Timestamp("2005-01-01"), SCRAPE_DATE)
        post = _fit_era(series, climate,
                        SCRAPE_DATE, FELL_DATE)

        if pre is None or post is None:
            print(f"   WARNING: {well_name} \u2014 insufficient data "
                  f"in one or both windows")
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
            "pre_b1":  _get_b(pre, "b1"),
            "pre_b2":  _get_b(pre, "b2"),
            "pre_b3":  _get_b(pre, "b3"),
            "pre_r2":  pre["R2"],
            "pre_n":   pre["n"],
            "post_b1": _get_b(post, "b1"),
            "post_b2": _get_b(post, "b2"),
            "post_b3": _get_b(post, "b3"),
            "post_r2": post["R2"],
            "post_n":  post["n"],
            "raw_db1": _get_b(post, "b1") - _get_b(pre, "b1"),
            "raw_db2": _get_b(post, "b2") - _get_b(pre, "b2"),
            "raw_db3": _get_b(post, "b3") - _get_b(pre, "b3"),
        })

    df = pd.DataFrame(results)
    print(f"   Fitted {len(df)} wells "
          f"({df['role'].value_counts().to_dict()})")

    # \u2500\u2500 3. BACI correction \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n3. Computing BACI correction...")

    ctrl = df[df["role"] == "control"]
    ctrl_db1 = ctrl["raw_db1"].mean()
    ctrl_db2 = ctrl["raw_db2"].mean()
    ctrl_db3 = ctrl["raw_db3"].mean()

    print(f"   Control centroid raw shifts (n={len(ctrl)} wells):")
    print(f"     \u0394\u03b2\u2081 = {ctrl_db1:+.3f}")
    print(f"     \u0394\u03b2\u2082 = {ctrl_db2:+.3f}")
    print(f"     \u0394\u03b2\u2083 = {ctrl_db3:+.4f} "
          f"({ctrl_db3*1000:+.1f} \u00d7 10\u207b\u00b3)")

    df["baci_db1"] = df["raw_db1"] - ctrl_db1
    df["baci_db2"] = df["raw_db2"] - ctrl_db2
    df["baci_db3"] = df["raw_db3"] - ctrl_db3

    # Print individual uphill wells
    uphill = df[df["role"] == "uphill"].sort_values("dist_m")
    print(f"\n   Uphill wells (BACI-corrected):")
    for _, r in uphill.iterrows():
        print(f"     {r['well']:8s}  C{r['cluster']}  "
              f"{r['dist_m']:5.0f}m  "
              f"\u0394\u03b2\u2083={r['baci_db3']*1000:+5.1f}"
              f"\u00d710\u207b\u00b3  "
              f"n_pre={r['pre_n']:.0f}")

    # \u2500\u2500 4. Centroid summaries \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n4. Computing centroid summaries...")

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

        # Build centroid: average well series, then fit SSM to centroid
        series_list = [_get_series(w, wells_clean, wells_ext)
                       for w in group_df["well"]]
        series_list = [s for s in series_list if s is not None]
        centroid_ts = pd.concat(
            series_list, axis=1, sort=True).mean(axis=1)

        pre  = _fit_era(centroid_ts, climate,
                        pd.Timestamp("2005-01-01"), SCRAPE_DATE)
        post = _fit_era(centroid_ts, climate,
                        SCRAPE_DATE, FELL_DATE)

        if pre and post:
            db1 = (_get_b(post, "b1") - _get_b(pre, "b1")) - ctrl_db1
            db2 = (_get_b(post, "b2") - _get_b(pre, "b2")) - ctrl_db2
            db3 = (_get_b(post, "b3") - _get_b(pre, "b3")) - ctrl_db3
            pct_b3 = (db3 / abs(_get_b(pre, "b3")) * 100
                      if abs(_get_b(pre, "b3")) > 1e-6 else np.nan)

            centroid_rows.append({
                "group":        group_name,
                "n_wells":      len(group_df),
                "pre_b1":       _get_b(pre, "b1"),
                "pre_b2":       _get_b(pre, "b2"),
                "pre_b3":       _get_b(pre, "b3"),
                "post_b1":      _get_b(post, "b1"),
                "post_b2":      _get_b(post, "b2"),
                "post_b3":      _get_b(post, "b3"),
                "pre_r2":       pre["R2"],
                "post_r2":      post["R2"],
                "baci_db1":     db1,
                "baci_db2":     db2,
                "baci_db3":     db3,
                "baci_db3_pct": pct_b3,
            })

            print(f"   {group_name} ({len(group_df)} wells):")
            print(f"     BACI \u0394\u03b2\u2081={db1:+.3f}  "
                  f"\u0394\u03b2\u2082={db2:+.3f}  "
                  f"\u0394\u03b2\u2083={db3*1000:+.1f}\u00d710\u207b\u00b3 "
                  f"({pct_b3:+.0f}%)")

    centroids_df = pd.DataFrame(centroid_rows)

    # \u2500\u2500 5. Export CSVs \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n5. Exporting CSVs...")

    df.to_csv(OUT_09B_INDIVIDUAL, index=False, float_format="%.4f")
    print(f"   \u2192 {OUT_09B_INDIVIDUAL.name}")

    centroids_df.to_csv(OUT_09B_CENTROIDS, index=False,
                        float_format="%.4f")
    print(f"   \u2192 {OUT_09B_CENTROIDS.name}")

    # \u2500\u2500 6. Figure: CEH36 equilibration trajectory \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n6. Generating CEH36 equilibration figure...")

    _plot_equilibration(wells_clean)

    print(f"   \u2192 {OUT_09B_TRAJECTORY.name}")

    # \u2500\u2500 7. Figure: Scenario comparison bar chart \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n7. Generating scenario comparison chart...")

    _plot_scenario_comparison()

    print("\nDone.")


# ============================================================================
# FIGURE: CEH36 POST-SCRAPING TRAJECTORY
# ============================================================================

def _plot_equilibration(wells_clean):
    """
    Plot climate-corrected water table anomaly for CEH36 (scraped) vs
    CEH4 (unscraped control, 99 m away).

    Shows three phases:
    1. Scraping creates a head surplus (water table too high for new
       drainage equilibrium).
    2. Surplus equilibrates over ~2 years via increased drainage.
    3. New equilibrium reached; residual decline = coastal erosion
       background signal.

    CEH4 (unscraped, 99 m south) shows the coastal erosion baseline:
    steady decline from -50 mm to -400 mm over 2010-2024. CEH36
    holds near zero, demonstrating scraping protection.
    """
    # Build control centroid from distant C3 wells
    ctrl_series = []
    for w in CONTROL_WELLS:
        col = _find_well_col(w, wells_clean)
        if col is not None:
            ctrl_series.append(wells_clean[col])
    ctrl_centroid = pd.concat(
        ctrl_series, axis=1, sort=True).mean(axis=1)

    def _make_cc(well_col):
        """Climate-correct a well against the control centroid."""
        s = well_col.dropna()
        common = s.index.intersection(ctrl_centroid.dropna().index)
        if len(common) == 0:
            return None
        s_c = s[common]
        ctrl_c = ctrl_centroid[common]
        pre = common[common < SCRAPE_DATE]
        if len(pre) < 12:
            return None
        return ((s_c - s_c[pre].mean()) -
                (ctrl_c - ctrl_c[pre].mean()))

    ceh36_col = _find_well_col("ceh36", wells_clean)
    ceh4_col  = _find_well_col("ceh4", wells_clean)

    if ceh36_col is None or ceh4_col is None:
        print("   WARNING: CEH36 or CEH4 not found "
              "\u2014 skipping trajectory figure")
        return

    ceh36_cc = _make_cc(wells_clean[ceh36_col])
    ceh4_cc  = _make_cc(wells_clean[ceh4_col])

    if ceh36_cc is None or ceh4_cc is None:
        print("   WARNING: insufficient pre-scraping data "
              "\u2014 skipping trajectory figure")
        return

    # 12-month rolling means (mm)
    ceh36_roll = (ceh36_cc.rolling(12, center=True, min_periods=6)
                  .mean() * 1000)
    ceh4_roll  = (ceh4_cc.rolling(12, center=True, min_periods=6)
                  .mean() * 1000)

    fig, ax = plt.subplots(1, 1, figsize=(14, 7))

    ax.plot(ceh36_roll.index, ceh36_roll.values,
            color="#d62728", linewidth=3.0,
            label="CEH36 (scraped Apr 2015)", zorder=5)
    ax.plot(ceh4_roll.index, ceh4_roll.values,
            color="#ff7f0e", linewidth=2.5,
            label="CEH4 (unscraped control, 99 m away)",
            alpha=0.8, zorder=4)

    ax.axhline(0, color="black", linewidth=1.0,
               label="Pre-scraping baseline")
    ax.axvline(SCRAPE_DATE, color="#DAA520", linewidth=2.5,
               linestyle="--", label="Scraping (Apr 2015)")
    ax.axvline(FELL_DATE, color="brown", linewidth=2.0,
               linestyle="--", label="Clearfell (Dec 2017)",
               alpha=0.7)

    # Phase 1: head surplus equilibrates
    ax.annotate(
        "Head surplus\nequilibrates\n"
        "via drainage (\u03b2\u2083)",
        xy=(pd.Timestamp("2016-06"), 80),
        fontsize=14, fontweight="bold", color="#228B22",
        ha="center", va="bottom")
    ax.annotate(
        "", xy=(pd.Timestamp("2017-09"), 20),
        xytext=(pd.Timestamp("2015-09"), 100),
        arrowprops=dict(arrowstyle="->", color="#228B22", lw=2.5,
                        connectionstyle="arc3,rad=-0.2"))

    # Phase 2: new equilibrium + coastal erosion
    ax.annotate(
        "New equilibrium reached;\n"
        "residual decline = coastal\n"
        "erosion signal",
        xy=(pd.Timestamp("2022-06"), -30),
        fontsize=14, fontweight="bold", color="#d62728",
        ha="center", va="top")

    # CEH4 annotation
    ceh4_late = ceh4_roll["2023-01":"2023-06"]
    ceh4_y = (ceh4_late.mean()
              if len(ceh4_late) > 0 else -350)
    ax.annotate(
        "CEH4: steady coastal\nerosion decline\n"
        "(no scraping protection)",
        xy=(pd.Timestamp("2023-01"), ceh4_y),
        xytext=(pd.Timestamp("2020-01"), -340),
        fontsize=13, fontweight="bold", color="#ff7f0e",
        arrowprops=dict(arrowstyle="->",
                        color="#ff7f0e", lw=2.0))

    # Axis direction helpers
    ax.text(0.01, 0.97,
            "\u2191 shallower (wetter)",
            transform=ax.transAxes, fontsize=12,
            color="#228B22", fontweight="bold", va="top")
    ax.text(0.01, 0.03,
            "\u2193 deeper (drier)",
            transform=ax.transAxes, fontsize=12,
            color="#d62728", fontweight="bold", va="bottom")

    ax.set_xlabel("Date", fontsize=15)
    ax.set_ylabel(
        "Change in water table depth\n"
        "relative to pre-scraping mean (mm)\n"
        "(climate-corrected, 12-month rolling mean)",
        fontsize=14)
    ax.set_title(
        "Observed water table response to scraping at CEH36\n"
        "Head change relative to pre-2015 baseline, "
        "corrected for climate using distant C3 wells",
        fontsize=16, fontweight="bold")

    # Date axis: year-only labels (long time series)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.legend(fontsize=12, loc="upper right")
    ax.tick_params(labelsize=13)
    ax.set_xlim(pd.Timestamp("2011-01-01"),
                pd.Timestamp("2026-03-01"))
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    fig.savefig(OUT_09B_TRAJECTORY, dpi=200, format="jpeg",
                pil_kwargs={"quality": 85}, bbox_inches="tight")
    plt.close(fig)


# ============================================================================
# FIGURE: SCENARIO COMPARISON BAR CHART
# ============================================================================

# Existing scenario values (mm water equiv / month) from make_scenario_chart.py
_EXISTING_SCENARIOS = {
    "Clearfell":     {"C1":  0.0, "C2":  0.0, "C3":  0.0, "C4": -2.2, "C5": +4.5},
    "Thinning 50%":  {"C1":  0.0, "C2":  0.0, "C3":  0.0, "C4": -1.1, "C5": +2.2},
    "Broadleaf":     {"C1":  0.0, "C2":  0.0, "C3":  0.0, "C4": +3.6, "C5": +4.1},
    "Climate dry":   {"C1": -7.9, "C2":-11.0, "C3":-12.3, "C4": -9.0, "C5": -6.7},
    "Climate wet":   {"C1": +7.4, "C2": +9.1, "C3": +9.8, "C4": +6.0, "C5": +5.1},
}

# Cluster baseline parameters (from Script 03 / scenario_viewer.html)
_CLUSTER_PARAMS = {
    "C1": {"b1": 5.019, "b2": 0.613, "b3": 0.104, "Sy": 0.211,
            "h_aod": 8.2824, "forest": False},
    "C2": {"b1": 4.148, "b2": 1.661, "b3": 0.070, "Sy": 0.267,
            "h_aod": 7.3043, "forest": False},
    "C3": {"b1": 3.526, "b2": 1.677, "b3": 0.061, "Sy": 0.328,
            "h_aod": 6.9624, "forest": False},
    "C4": {"b1": 2.472, "b2": 2.634, "b3": 0.016, "Sy": 0.254,
            "h_aod": 9.3806, "forest": True},
    "C5": {"b1": 2.305, "b2": 1.191, "b3": 0.046, "Sy": 0.308,
            "h_aod": 4.4499, "forest": True},
}

# Summer climate means (m/month)
_SUMMER_P   = 0.0641552
_SUMMER_PET = 0.0882963

# Forest interception fraction (Corsican pine)
_FOREST_INT = 0.24

# Ground lowering from scraping (m)
_GROUND_LOWERING = 0.2

# Fraction of each cluster within 800 m uphill of CEH36
# C3: 6/19 = 32%, C4: 7/9 = 78%, C5: 5/5 = 100%.
#
# NOTE — C5 coastal retreat confound:
# The four outer C5 wells (NW9, CEH16, CEH17, CEH19) sit on the western
# coastal margin (605–788 m from the W coast, elev 4.8–6.2 m). Their
# pre-intervention water-table records are dominated by a 2006–2008
# recharge spike (ridge-proximal pathway) whose hangover produces steep
# apparent declines that are not coastal erosion. CEH4 (C3, 4.5 m elev,
# same western zone) shows a genuine residual decline of −28 mm/yr even
# after trimming to 2010+, consistent with progressive coastal boundary
# retreat, but the C5 wells' trimmed (2010+) differential slopes are
# near zero (NW9: −3, CEH16: +7, CEH17: −10, CEH19: −18, CEH31: +1 mm/yr,
# none significant).
#
# The C1+C2 BACI control (eastern clusters) does not share the western
# positional signal, so the Script 10 BACI felling step for C5 (−76 mm)
# overstates the intervention-attributable decline. A sensitivity test
# using NW5–7 (western C3, unforested, un-scraped) as control halves the
# C5 felling step to −33 mm; using CEH4 flips it to +23 mm.
#
# The scraping propagation analysis (this script) already excluded the
# outer four C5 wells from the uphill well set, retaining only CEH31
# (875 m from coast, 6.5 m elev). The FRAC_AFFECTED value of 1.00 is
# geometrically correct (all five C5 wells are within 800 m of CEH36)
# but should be interpreted cautiously: the coefficient shifts applied
# to C5 come from the individual well median, not from the outer four
# wells directly. The C5 scraping bar reflects the mechanistic SSM
# perturbation at C5's mean coefficients, weighted by the geometric
# fraction, not an empirical observation at all five wells.
#
# The SSM-derived scenario values are computed from coefficient
# perturbations and are independent of the coastal confound. They
# represent the expected intervention effect at C5 in the absence of
# boundary retreat.
_FRAC_AFFECTED = {"C1": 0.0, "C2": 0.0, "C3": 0.32, "C4": 0.78, "C5": 1.00}


def _plot_scenario_comparison():
    """
    Scenario comparison bar chart: forest management, scraping, and climate
    across all k=5 clusters.

    Scraping bars use the BACI-corrected median proportional beta_3 shift
    from individual well analysis (beta_3 only, no beta_1/beta_2
    compensation). The beta_1 and beta_2 shifts from the split-window
    analysis are not applied because the short 31-month post-scraping
    window causes the SSM to redistribute real drainage signal across
    coefficients, producing compensation that contradicts the clearfell
    BACI evidence.

    Values are weighted by the fraction of each cluster's monitoring
    network within 800 m uphill of CEH36.
    """
    clusters = ["C1", "C2", "C3", "C4", "C5"]
    cluster_labels = ["C1\nLake Edge", "C2\nDune", "C3\nWestern",
                      "C4\nMain\nForest", "C5\nCoastal\nForest"]

    # --- Compute scraping bars from individual well median beta_3 shift ---
    # We apply ONLY the beta_3 shift, not beta_1 or beta_2. The beta_1 and
    # beta_2 shifts from the split-window analysis absorb real drainage
    # signal as apparent coefficient changes in the short 31-month post-
    # scraping window. Including them produces positive bars that contradict
    # the clearfell BACI evidence showing drainage propagation costs the
    # neighbours. The beta_3 drainage increase is the primary physical
    # mechanism; beta_1 and beta_2 adjustment is an equilibrium response
    # that occurs over time at the SCRAPED site, not at the neighbours.
    scrape_unweighted = {c: 0.0 for c in clusters}

    # Read individual well BACI shifts
    indiv_df = pd.read_csv(OUT_09B_INDIVIDUAL)
    uphill_df = indiv_df[
        (indiv_df["role"] == "uphill") &
        (indiv_df["well"] != "ceh39")   # exclude: n_pre=24, unreliable
    ]

    if len(uphill_df) >= 5:
        # Median proportional beta_3 shift across individual wells
        uphill_df = uphill_df.copy()
        uphill_df["db3_pct"] = (
            uphill_df["baci_db3"] / uphill_df["pre_b3"].abs()
        )
        med_db3_pct = uphill_df["db3_pct"].median()

        for cname in ["C3", "C4", "C5"]:
            c = _CLUSTER_PARAMS[cname]
            p_eff = (_SUMMER_P * (1 - _FOREST_INT)
                     if c["forest"] else _SUMMER_P)

            flux_base = (c["b1"] * p_eff
                         - c["b2"] * _SUMMER_PET
                         - c["b3"] * c["h_aod"])

            # Only beta_3 changes; beta_1 and beta_2 unchanged
            b3_new = c["b3"] * (1 + med_db3_pct)
            h_new  = c["h_aod"] - _GROUND_LOWERING

            flux_scen = (c["b1"] * p_eff
                         - c["b2"] * _SUMMER_PET
                         - b3_new * h_new)

            scrape_unweighted[cname] = (
                (flux_scen - flux_base) * c["Sy"] * 1000)

        print(f"   Median proportional \u0394\u03b2\u2083 = "
              f"{med_db3_pct*100:+.1f}% (n={len(uphill_df)} wells)")
        print(f"   Scraping (unweighted): "
              f"C3={scrape_unweighted['C3']:+.1f}  "
              f"C4={scrape_unweighted['C4']:+.1f}  "
              f"C5={scrape_unweighted['C5']:+.1f}")
    else:
        print("   WARNING: insufficient individual well data "
              "\u2014 scraping bars set to zero")

    # Weight by fraction of cluster affected
    scrape_w = {c: scrape_unweighted[c] * _FRAC_AFFECTED[c]
                for c in clusters}

    print(f"   Scraping (weighted):   "
          f"C3={scrape_w['C3']:+.1f}  "
          f"C4={scrape_w['C4']:+.1f}  "
          f"C5={scrape_w['C5']:+.1f}")

    # --- Build scenario dict ---
    scenarios = {
        "Clearfell":         (_EXISTING_SCENARIOS["Clearfell"],
                              "#8B4513", None),
        "Thinning 50%":      (_EXISTING_SCENARIOS["Thinning 50%"],
                              "#D2691E", None),
        "Broadleaf":         (_EXISTING_SCENARIOS["Broadleaf"],
                              "#228B22", None),
        "Scraping (nearby)": (scrape_w, "#DAA520", "///"),
        "Climate dry":       (_EXISTING_SCENARIOS["Climate dry"],
                              "#FF6347", None),
        "Climate wet":       (_EXISTING_SCENARIOS["Climate wet"],
                              "#4169E1", None),
    }

    # --- Plot ---
    n_scen = len(scenarios)
    x = np.arange(len(clusters))
    width = 0.12
    offsets = np.linspace(-(n_scen - 1) / 2 * width,
                          (n_scen - 1) / 2 * width, n_scen)

    fig, ax = plt.subplots(1, 1, figsize=(14, 7))

    for i, (scenario, (vals_dict, colour, hatch)) in enumerate(
            scenarios.items()):
        vals = [vals_dict[c] for c in clusters]
        is_scrape = "Scraping" in scenario
        ax.bar(x + offsets[i], vals, width, label=scenario,
               color=colour,
               edgecolor="black" if is_scrape else "white",
               linewidth=1.2 if is_scrape else 0.5,
               alpha=0.85, hatch=hatch)
        if is_scrape:
            for j, v in enumerate(vals):
                if abs(v) > 0.3:
                    offset_y = -0.4 if v < 0 else 0.2
                    ax.text(x[j] + offsets[i], v + offset_y,
                            f"{v:.1f}", ha="center",
                            va="top" if v < 0 else "bottom",
                            fontsize=10, fontweight="bold",
                            color="#8B6914")

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cluster_labels, fontsize=13)
    ax.set_ylabel("\u0394 volumetric water table\n"
                  "(mm water equiv. / month)", fontsize=14)
    ax.tick_params(axis="y", labelsize=12)
    ax.set_title(
        "Scenario comparison: forest management, scraping, "
        "and climate (k = 5)\n"
        "Volumetric using WTF-derived, "
        "interception-corrected Sy",
        fontsize=14, fontweight="bold")

    ax.legend(fontsize=11, loc="lower right", ncol=3,
              framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    # Footnote strip below the axes
    fig.text(0.02, 0.01,
             "Scraping bars: median \u0394\u03b2\u2083 from individual "
             "well BACI, weighted by fraction of cluster within "
             "800 m uphill of CEH36 (C3: 32%, C4: 78%, C5: 100%).  "
             "C5 BACI felling step (\u221276 mm) overstates decline "
             "due to western positional confound; SSM scenario values "
             "are unaffected.",
             fontsize=9, fontstyle="italic", color="#555555",
             wrap=True)

    fig.subplots_adjust(bottom=0.15)

    fig.savefig(OUT_09B_SCENARIO, dpi=200, format="jpeg",
                pil_kwargs={"quality": 85}, bbox_inches="tight")
    plt.close(fig)

    # --- Export CSV ---
    rows = []
    for scenario, (vals_dict, _, _) in scenarios.items():
        for c in clusters:
            rows.append({"Scenario": scenario, "Cluster": c,
                         "Delta_vol_mm_per_month": round(vals_dict[c], 1)})
    pd.DataFrame(rows).to_csv(OUT_09B_SCENARIO_CSV, index=False,
                              float_format="%.1f")
    print(f"   \u2192 {OUT_09B_SCENARIO.name}")
    print(f"   \u2192 {OUT_09B_SCENARIO_CSV.name}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
