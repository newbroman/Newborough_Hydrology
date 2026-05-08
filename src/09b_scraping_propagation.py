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

__version__ = "1.2.0"  # 2026-05-08 — hardcoded SCENARIO_VALUES replaced with compute_scenario_bars()

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(
    _os.path.abspath(__file__)))); del _sys, _os

from utils.paths import (
    INT_WELLS_CLEAN, INT_WELLS_EXTENDED, INT_CLIMATE,
    INT_LOCATIONS, INT_MASTER_DATA, INT_REGIONAL_AVG, DIR_09,
    OUT_09B_INDIVIDUAL, OUT_09B_CENTROIDS, OUT_09B_TRAJECTORY,
    OUT_09B_SCENARIO, OUT_09B_SCENARIO_CSV,
    OUT_09B_SUMMER_SCENARIO, OUT_09B_SUMMER_SCENARIO_CSV,
    INT_CLUSTER_AVG_MAOD, OUT_17_SY_TABLE,
)
from utils.config import DRAINAGE_DATUM, HEADLINE_LAG, FOREST_INTERCEPTION, FOREST_CIDS
from utils.model_utils import fit_ssm
from utils.data_utils import normalize_well_name
from utils.clearfell_common import (
    IMPACT_WELLS, EDGE_WELLS, FOREST_CONTROL_WELLS,
)

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from scipy import stats as _stats


# ============================================================================
# CONSTANTS
# ============================================================================
SCRAPE_DATE  = pd.Timestamp("2015-04-01")
FELL_DATE    = pd.Timestamp("2017-12-01")
SCRAPE2_DATE = pd.Timestamp("2023-10-01")

E_CEH36 = 241161.0
N_CEH36 = 363306.0

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


def _fit_era(series, climate, start, end):
    era_series = series.copy()
    era_series[(era_series.index < start) | (era_series.index >= end)] = np.nan
    return fit_ssm(era_series, climate, min_obs=MIN_OBS_SPLIT)


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

    # 2. Fit split-window SSMs
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

    # 3. BACI correction
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

    uphill = df[df["role"] == "uphill"].sort_values("dist_m")
    print(f"\n   Uphill wells (BACI-corrected):")
    for _, r in uphill.iterrows():
        print(f"     {r['well']:8s}  C{r['cluster']}  "
              f"{r['dist_m']:5.0f}m  "
              f"\u0394\u03b2\u2083={r['baci_db3']*1000:+5.1f}"
              f"\u00d710\u207b\u00b3  "
              f"n_pre={r['pre_n']:.0f}")

    # 4. Centroid summaries
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

    # 5. Export CSVs
    print("\n5. Exporting CSVs...")
    df.to_csv(OUT_09B_INDIVIDUAL, index=False, float_format="%.4f")
    print(f"   \u2192 {OUT_09B_INDIVIDUAL.name}")
    centroids_df.to_csv(OUT_09B_CENTROIDS, index=False, float_format="%.4f")
    print(f"   \u2192 {OUT_09B_CENTROIDS.name}")

    # 6. Equilibration figure
    print("\n6. Generating CEH36 equilibration figure...")
    _plot_equilibration(wells_clean)
    print(f"   \u2192 {OUT_09B_TRAJECTORY.name}")

    # 7. Scenario comparison
    print("\n7. Generating scenario comparison figure...")
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
        print("   WARNING: CEH36 or CEH4 not found \u2014 skipping trajectory figure")
        return

    ceh36_cc = _make_cc(wells_clean[ceh36_col])
    ceh4_cc  = _make_cc(wells_clean[ceh4_col])
    if ceh36_cc is None or ceh4_cc is None:
        print("   WARNING: insufficient pre-scraping data \u2014 skipping trajectory figure")
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
    fig.savefig(OUT_09B_TRAJECTORY, dpi=200, format="jpeg",
                pil_kwargs={"quality": 85}, bbox_inches="tight")
    plt.close(fig)


# ============================================================================
# FIGURE 4 — SCENARIO COMPARISON BAR CHART
# ============================================================================

# Scraping ground-lowering depth (m)
GROUND_LOWERING = 0.2

# Fraction of each cluster's wells within 800 m uphill of CEH36.
FRAC_AFFECTED = {"C1": 0.0, "C2": 0.0, "C3": 0.32, "C4": 0.78, "C5": 1.00}


def _compute_scraping_bars(centroids_df):
    """
    Compute scraping scenario bars from BACI-corrected centroid summaries.
    All three coefficient shifts applied. C5 uses C3+CEH31 shifts;
    C4 uses C4 shifts. C1 and C2 are zero.
    """
    from utils.scraping_common import load_cluster_params, load_summer_climate

    cluster_params = load_cluster_params()
    P, PET = load_summer_climate()

    c3_row = centroids_df[centroids_df["group"].str.contains("C3")]
    c4_row = centroids_df[centroids_df["group"].str.contains("C4")]

    if len(c3_row) == 0 or len(c4_row) == 0:
        print("   WARNING: centroid summaries incomplete \u2014 "
              "scraping bars set to zero")
        return {c: 0.0 for c in cluster_params}

    c3_row = c3_row.iloc[0]
    c4_row = c4_row.iloc[0]
    shift_map = {"C3": c3_row, "C4": c4_row, "C5": c3_row}

    scrape_unweighted = {}
    for cname, c in cluster_params.items():
        if cname not in shift_map:
            scrape_unweighted[cname] = 0.0
            continue

        row = shift_map[cname]
        db1 = row["baci_db1"]
        db2 = row["baci_db2"]
        db3_pct = row["baci_db3_pct"] / 100.0

        p_eff = P * (1 - FOREST_INTERCEPTION) if c["forest"] else P
        flux_base = c["b1"] * p_eff - c["b2"] * PET - c["b3"] * c["h_disp"]

        b1_new = c["b1"] + db1
        b2_new = c["b2"] + db2
        b3_new = c["b3"] * (1 + db3_pct)
        h_new  = c["h_disp"] - GROUND_LOWERING

        flux_scen = b1_new * p_eff - b2_new * PET - b3_new * h_new
        scrape_unweighted[cname] = (flux_scen - flux_base) * c["Sy"] * 1000

    scrape_weighted = {c: scrape_unweighted[c] * FRAC_AFFECTED[c]
                       for c in scrape_unweighted}
    return scrape_weighted


def _plot_scenario_comparison(centroids_df, dpi=200):
    """
    Grouped bar chart: forest management, scraping, and climate scenarios.
    Non-scraping values from compute_scenario_bars() (single source of truth).
    Scraping bars from BACI centroid shifts.
    """
    from utils.scraping_common import (
        compute_scenario_bars, load_cluster_params, load_summer_climate,
    )

    clusters = ["C1", "C2", "C3", "C4", "C5"]
    cluster_labels = ["C1\nLake Edge", "C2\nDune", "C3\nWestern",
                      "C4\nMain\nForest", "C5\nCoastal\nForest"]

    # Non-scraping scenarios from the shared function
    cluster_params = load_cluster_params()
    summer_P, summer_PET = load_summer_climate()
    base_scenarios = compute_scenario_bars(cluster_params, summer_P, summer_PET)

    # Scraping bars from centroid BACI shifts
    scrape_w = _compute_scraping_bars(centroids_df)

    colour_map = {
        "Clearfell": "#8B4513", "Thinning 50%": "#D2691E",
        "Broadleaf": "#228B22", "Scraping (nearby)": "#DAA520",
        "Climate dry": "#FF6347", "Climate wet": "#4169E1",
    }
    hatch_map = {"Scraping (nearby)": "///"}

    # Build ordered scenario dict: {name: (vals_dict, colour, hatch)}
    scenarios = {}
    for s_name in ["Clearfell", "Thinning 50%", "Broadleaf"]:
        if s_name in base_scenarios:
            scenarios[s_name] = (base_scenarios[s_name],
                                 colour_map.get(s_name, "#999"), None)
    scenarios["Scraping (nearby)"] = (scrape_w, "#DAA520", "///")
    for s_name in ["Climate dry", "Climate wet"]:
        if s_name in base_scenarios:
            scenarios[s_name] = (base_scenarios[s_name],
                                 colour_map.get(s_name, "#999"), None)

    n_scen = len(scenarios)
    x = np.arange(len(clusters))
    width = 0.12
    offsets = np.linspace(-(n_scen - 1) / 2 * width,
                           (n_scen - 1) / 2 * width, n_scen)

    fig, ax = plt.subplots(1, 1, figsize=(14, 7.5))

    for i, (scenario, (vals_dict, colour, hatch)) in enumerate(
            scenarios.items()):
        vals = [vals_dict.get(c, 0) for c in clusters]
        is_scrape = "Scraping" in scenario
        ax.bar(x + offsets[i], vals, width, label=scenario,
               color=colour,
               edgecolor="black" if is_scrape else "white",
               linewidth=1.5 if is_scrape else 0.5,
               alpha=0.85, hatch=hatch)
        if is_scrape:
            for j, v in enumerate(vals):
                if abs(v) > 0.3:
                    ax.text(x[j] + offsets[i], v - 1.5, f"{v:.1f}",
                            ha="center", fontsize=12, fontweight="bold",
                            color="#8B6914")

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cluster_labels, fontsize=14)
    ax.set_ylabel("\u0394 volumetric water table\n"
                  "(mm water equiv. / month)", fontsize=15)
    ax.tick_params(axis="y", labelsize=13)
    ax.set_title(
        "Scenario comparison: forest management, scraping, "
        "and climate (k = 5)\n"
        "Volumetric using WTF-derived, interception-corrected Sy",
        fontsize=15, fontweight="bold")

    ax.text(0.98, 0.02,
            "Scraping bars: cluster-average monthly impact\n"
            "on unscraped areas, weighted by fraction of cluster\n"
            "within 800 m uphill of CEH36 (C3: 32%, C4: 78%, C5: 100%)",
            transform=ax.transAxes, fontsize=10,
            va="bottom", ha="right",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow",
                      alpha=0.9, edgecolor="#DAA520"))

    ax.text(0.98, 0.98,
            "C5 note: BACI felling step (\u221276 mm)\n"
            "overstates decline due to western\n"
            "positional confound vs C1+C2 control.\n"
            "SSM scenario values are unaffected.",
            transform=ax.transAxes,
            fontsize=9, fontstyle="italic", color="#555555",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#F5F5F5",
                      alpha=0.85, edgecolor="#AAAAAA"),
            ha="right", va="top")

    ax.legend(fontsize=10, loc="lower left", ncol=2, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    fig.savefig(OUT_09B_SCENARIO, dpi=dpi, format="jpeg",
                pil_kwargs={"quality": 85}, bbox_inches="tight")
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
    """Summer minimum scenario figure: empirical BACI + SSM climate amplification."""
    print("\n8. Generating summer minimum scenario comparison...")

    SUMMER = [6, 7, 8, 9]
    FELLING_YEAR = 2018
    SCRAPE_YEAR = 2015

    new = [c for c in wells_ext.columns if c not in wells_clean.columns]
    wells = pd.concat([wells_clean, wells_ext[new]], axis=1)
    wells.columns = wells.columns.str.lower().str.replace(' ', '')

    regional = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    clusters = ['C1', 'C2', 'C3', 'C4', 'C5']

    # Amplification factors
    amp_factors = {}
    for c in clusters:
        if c not in regional.columns:
            continue
        annual, summin = {}, {}
        for yr in range(2006, 2026):
            yr_data = regional.loc[regional.index.year == yr, c].dropna()
            if len(yr_data) >= 8:
                annual[yr] = float(yr_data.mean())
            sm_mask = (regional.index.year == yr) & (regional.index.month.isin(SUMMER))
            sm_data = regional.loc[sm_mask, c].dropna()
            if len(sm_data) >= 2:
                summin[yr] = float(sm_data.min())
        common = sorted(set(annual) & set(summin))
        if len(common) >= 8:
            x = np.array([annual[yr] for yr in common])
            y = np.array([summin[yr] for yr in common])
            slope, _, r, p, _ = _stats.linregress(x, y)
            amp_factors[c] = slope
        else:
            amp_factors[c] = 0.85

    def _annual_summer_min(series):
        mins = {}
        for yr in range(2006, 2026):
            mask = (series.index.year == yr) & (series.index.month.isin(SUMMER))
            s = series[mask].dropna()
            if len(s) >= 2:
                mins[yr] = float(s.min())
        return mins

    # Scraping: CEH36 vs CEH18
    scraping_shift_mm = 0.0
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
            print(f"   Scraping (CEH36 vs CEH18): {scraping_shift_mm:+.0f} mm  p = {p_val:.3f}")

    # Forestry + climate scenarios: all SSM-derived
    # Monthly volumetric (from 09b-04 CSV, which uses compute_scenario_bars)
    # → head (÷ Sy) → summer minimum (× amplification factor)
    # This ensures internal consistency with the monthly figure (09b-04).
    # Scraping remains empirical BACI (observed, not modelled).

    SY_FALLBACK = 0.20
    sy_by_cluster = {}
    if OUT_17_SY_TABLE.exists():
        sy_df = pd.read_csv(OUT_17_SY_TABLE)
        for c in clusters:
            label_col = sy_df["Cluster"].astype(str)
            corr_mask = label_col.str.startswith(c) & label_col.str.contains(
                "corrected", case=False, na=False)
            base_mask = label_col.str.startswith(c) & ~label_col.str.contains(
                "corrected", case=False, na=False)
            row = sy_df[corr_mask] if c in ("C4", "C5") and corr_mask.any() else sy_df[base_mask]
            if not row.empty and pd.notna(row["Sy_event_median"].iloc[0]):
                sy_by_cluster[c] = float(row["Sy_event_median"].iloc[0])
        if sy_by_cluster:
            print(f"   Sy from Script 17: " +
                  ", ".join(f"{c}={v:.3f}" for c, v in sy_by_cluster.items()))
    else:
        print(f"   [warn] {OUT_17_SY_TABLE.name} not found \u2014 "
              f"falling back to Sy={SY_FALLBACK}")

    # Build scenario table — all scenarios from the monthly CSV
    summer_data = {
        'Scraping\n(CEH36-type)': {'C1': 0, 'C2': 0, 'C3': 0, 'C4': 0,
                                    'C5': round(scraping_shift_mm)},
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
                    vol = float(row['Delta_vol_mm_per_month'].iloc[0])
                    sy_c = sy_by_cluster.get(c, SY_FALLBACK)
                    summer_data[scenario][c] = round(vol / sy_c * amp_factors.get(c, 0.85))
                else:
                    summer_data[scenario][c] = 0
        # Print forestry summer values for verification
        for s in ['Clearfell', 'Thinning 50%', 'Broadleaf']:
            if s in summer_data:
                c4_val = summer_data[s].get('C4', 0)
                c5_val = summer_data[s].get('C5', 0)
                print(f"   {s} summer min (SSM-derived): "
                      f"C4={c4_val:+.0f} mm  C5={c5_val:+.0f} mm")
    else:
        print(f"   [warn] {scen_csv.name} not found \u2014 "
              f"forestry bars set to zero")
        for s in ['Clearfell', 'Thinning 50%', 'Broadleaf',
                   'Climate dry', 'Climate wet']:
            summer_data[s] = {c: 0 for c in clusters}

    # Figure
    cluster_labels = ['C1\nLake Edge', 'C2\nDune', 'C3\nWestern',
                       'C4\nMain\nForest', 'C5\nCoastal\nForest']
    colours = {
        'Clearfell': '#8B6914', 'Thinning 50%': '#D2691E',
        'Broadleaf': '#228B22', 'Scraping\n(CEH36-type)': '#DAA520',
        'Climate dry': '#E8726E', 'Climate wet': '#5B9BD5',
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
        hatch = hatches.get(s_name, '')
        ax.bar(x + offset, vals, bw * 0.9,
               color=colours.get(s_name, '#999'),
               edgecolor='black' if hatch else colours.get(s_name, '#999'),
               linewidth=0.8 if hatch else 0.5,
               hatch=hatch, alpha=0.85, label=s_name, zorder=3)
        for j, v in enumerate(vals):
            if abs(v) > 20:
                ax.text(x[j] + offset, v + (4 if v > 0 else -4),
                        f'{v:+.0f}', ha='center',
                        va='bottom' if v > 0 else 'top',
                        fontsize=7.5, fontweight='bold', color='#333')

    ax.axhline(0, color='black', lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cluster_labels, fontsize=11)
    ax.set_ylabel('\u0394 summer minimum depth (mm)', fontsize=12)
    ax.set_title(
        'Summer minimum scenario comparison: forest management, scraping, and climate (k = 5)\n'
        'Scraping: empirical BACI  |  Forest management & climate: SSM equilibrium \u00d7 amplification',
        fontsize=12, fontweight='bold')
    ax.legend(fontsize=9, loc='lower left', framealpha=0.9, ncol=3)
    ax.grid(axis='y', alpha=0.25, ls='--')
    for sp in ['top', 'right']:
        ax.spines[sp].set_visible(False)
    ax.text(0.02, 0.82,
            f'Scraping: empirical BACI at scraped site (CEH36 vs CEH18, {scraping_shift_mm:+.0f} mm, '
            f'p = 0.017). Benefit is local.\n'
            'Forest management: SSM equilibrium \u00d7 summer amplification factor '
            '(consistent with monthly figure 09b-04).\n'
            'Climate: SSM annual-mean prediction \u00d7 empirical summer amplification factor.',
            transform=ax.transAxes, fontsize=7.5, ha='left', va='top',
            color='#555', style='italic')
    plt.tight_layout()
    plt.savefig(OUT_09B_SUMMER_SCENARIO, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"   \u2192 {OUT_09B_SUMMER_SCENARIO.name}")

    # Export CSV
    rows = []
    for s_name in scenarios_order:
        for c in clusters:
            rows.append({'Scenario': s_name.replace('\n', ' '),
                         'Cluster': c,
                         'Delta_summer_min_mm': summer_data[s_name].get(c, 0)})
    pd.DataFrame(rows).to_csv(OUT_09B_SUMMER_SCENARIO_CSV, index=False)
    print(f"   \u2192 {OUT_09B_SUMMER_SCENARIO_CSV.name}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
