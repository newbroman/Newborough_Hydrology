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
            db1 = (post["beta_1_recharge"] - pre["beta_1_recharge"]) - ctrl_db1
            db2 = (post["beta_2_atmospheric_draw"] - pre["beta_2_atmospheric_draw"]) - ctrl_db2
            db3 = (post["beta_3_drainage"] - pre["beta_3_drainage"]) - ctrl_db3
            pct_b3 = (db3 / abs(pre["beta_3_drainage"]) * 100
                      if abs(pre["beta_3_drainage"]) > 1e-6 else np.nan)

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
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
