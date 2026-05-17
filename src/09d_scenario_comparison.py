r"""
====================================================================================
09d — CEH36 SCENARIO COMPARISON
====================================================================================
Purpose
-------
Compares the observed scraping benefit at CEH36 against what alternative
interventions would have achieved at the same well.  Uses CEH36's own SSM
coefficients, Sy, and mean head displacement to compute equilibrium responses
for clearfell, thinning, broadleaf conversion, and UKCP18 climate scenarios.

This answers the management question: "was scraping a good choice for this
site compared to alternatives?"

Two figures:
  1. Monthly equilibrium Δh (mm) at CEH36 under each scenario
  2. Summer minimum Δ depth (mm) at CEH36 — scraping (observed BACI)
     vs alternatives (SSM equilibrium × amplification)

All parameters read from upstream pipeline outputs (Scripts 01, 03, 17).
Forestry and climate scenario constants from config.py.

Outputs
-------
CSVs:
  09d_01_ceh36_scenario_comparison.csv  — monthly values
  09d_02_ceh36_summer_scenario.csv      — summer minimum values

Figures:
  09d_01_scenario_comparison.jpg        — monthly bar chart
  09d_02_summer_scenario_comparison.png — summer minimum bar chart

References
----------
Hollingham (2026), §4.5.  Part of the Script 09 scraping analysis suite.
====================================================================================
"""

__version__ = "3.2.0"  # Hollingham (2026) — 2026-05-16
# 3.2.0 — Replace hardcoded SCRAPE_BACI_STEP = 0.131 with a
#         load_site_observation("ceh36_baci_pure_scraping") call.
#         The value is now produced by 09a and stored in the
#         pipeline_site_observations.csv registry.  Closes Item 9
#         in flags log.
# 3.1.0 — B2 multiplier via clearfell_common loader.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.paths import (
    make_all_dirs,
    OUT_09_BACI_SHIFTS,
    OUT_09D_SCENARIO, OUT_09D_SCENARIO_CSV,
    OUT_09D_SUMMER_SCENARIO, OUT_09D_SUMMER_SCENARIO_CSV,
    INT_MASTER_DATA, INT_WTF_WELL_SY, INT_WELLS_CLEAN,
    INT_REGIONAL_AVG,
)
from utils.scraping_common import (
    SCRAPING_DATE, INTERVENTION_DATE,
    SUMMER_MONTHS, MPL_DEFAULTS,
    load_scraping_data,
    load_cluster_params, load_summer_climate,
)
from utils.config import (
    BW_MODE,
    DRAINAGE_DATUM,
    FOREST_INTERCEPTION, BROADLEAF_INTERCEPTION, BROADLEAF_B2_SUMMER,
    UKCP18_DRY_P_SUMMER, UKCP18_DRY_PET_SUMMER,
    UKCP18_WET_P_SUMMER, UKCP18_WET_PET_SUMMER,
)
from utils.clearfell_common import load_clearfell_b2_multiplier

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as _stats


# ============================================================================
# CONSTANTS
# ============================================================================
# The CEH36 Pure_Scraping BACI step is read from the pipeline site-
# observations registry (utils/site_observations.py).  The producer is
# Script 09a; the consumer here just loads it.  This replaces an earlier
# hardcoded value (0.131 m) which drifted from 09a's actual output as
# the analysis evolved (Item 9 in flags log).  If 09a has not yet been
# run on this clone, load_site_observation() returns the default and
# prints a one-line warning recommending a fresh pipeline run.
WELL = "ceh36"

# BW-mode scenario bar styling
_BW_SCENARIO_COLOURS = {
    "Scraping\n(observed)": "#bbbbbb",
    "Clearfell\n(hypothetical)": "#333333",
    "Thinning 50%\n(hypothetical)": "#666666",
    "Broadleaf\n(hypothetical)": "#999999",
    "Climate dry": "#444444",
    "Climate wet": "#cccccc",
}
_BW_SCENARIO_HATCHES = {
    "Scraping\n(observed)": "///",
    "Clearfell\n(hypothetical)": "xxx",
    "Thinning 50%\n(hypothetical)": "///",
    "Broadleaf\n(hypothetical)": "...",
    "Climate dry": "\\\\\\",
    "Climate wet": "",
}


def _bar_style(name, colours, hatches):
    """Return (colour, hatch, edgecolor) respecting BW_MODE."""
    if BW_MODE:
        return (_BW_SCENARIO_COLOURS.get(name, "#999"),
                _BW_SCENARIO_HATCHES.get(name, ""),
                "black")
    return (colours.get(name, "#999"),
            hatches.get(name, ""),
            "black" if hatches.get(name) else colours.get(name, "#999"))


# ============================================================================
# DATA LOADING
# ============================================================================

def _load_ceh36_params():
    """Load CEH36's parameters from the shared cluster params loader."""
    all_params = load_cluster_params()

    # Get CEH36's cluster assignment
    master = pd.read_csv(INT_MASTER_DATA)
    master["match"] = master["Name_Original"].str.lower().str.replace(" ", "")
    row = master[master["match"] == WELL]
    if row.empty:
        raise ValueError(f"{WELL} not found in master data")
    row = row.iloc[0]
    cluster = int(row["Cluster"])

    # Get CEH36's own well-level Sy (more precise than cluster median)
    sy_df = pd.read_csv(INT_WTF_WELL_SY)
    sy_row = sy_df[sy_df["Well"].str.lower() == WELL]
    well_sy = float(sy_row["Sy_median"].iloc[0]) if not sy_row.empty else 0.30

    # Get CEH36's own mean depth for h_disp
    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells.columns = wells.columns.str.lower().str.replace(" ", "")
    mean_depth = float(wells[WELL].mean()) if WELL in wells.columns else -0.7

    params = {
        "b1": float(row["beta_1_recharge"]),
        "b2": float(row["beta_2_atmospheric_draw"]),
        "b3": float(row["beta_3_drainage"]),
        "Sy": well_sy,
        "h_disp": DRAINAGE_DATUM + mean_depth,
        "cluster": cluster,
    }
    print(f"   CEH36: b1={params['b1']:.3f}  b2={params['b2']:.3f}  "
          f"b3={params['b3']:.4f}  Sy={params['Sy']:.3f}  "
          f"h_disp={params['h_disp']:.3f}m  cluster=C{params['cluster']}")
    return params


# ============================================================================
# MAIN
# ============================================================================

def main():
    make_all_dirs()
    plt.rcParams.update(MPL_DEFAULTS)

    print("=" * 72)
    print("SCRIPT 09d — CEH36 SCENARIO COMPARISON")
    print("=" * 72)

    # ── 1. Load CEH36 parameters ──────────────────────────────────────────
    print("\n1. Loading CEH36 parameters from pipeline...")
    params = _load_ceh36_params()
    summer_P, summer_PET = load_summer_climate()
    print(f"   Summer climate: P={summer_P:.6f}  PET={summer_PET:.6f} m/month")

    # ── 2. Compute scenarios at CEH36 ─────────────────────────────────────
    print("\n2. Computing scenario responses at CEH36...")
    scenarios = _compute_ceh36_scenarios(params, summer_P, summer_PET)

    # ── 3. Monthly figure ─────────────────────────────────────────────────
    print("\n3. Plotting monthly scenario comparison...")
    _plot_monthly(scenarios, params)

    # ── 4. Summer minimum figure ──────────────────────────────────────────
    print("\n4. Plotting summer minimum scenario comparison...")
    _plot_summer(scenarios, params, summer_P, summer_PET)

    print("\nDone.")


# ============================================================================
# SCENARIO COMPUTATION — all at CEH36
# ============================================================================

def _compute_ceh36_scenarios(params, summer_P, summer_PET):
    """Compute monthly equilibrium Δh at CEH36 for each scenario.

    CEH36 is in C3 (not forested), so forestry scenarios show what would
    happen *if* CEH36's location had pine canopy and were then managed.
    This is hypothetical but gives a like-for-like comparison of
    intervention magnitudes at the same hydrogeological setting.

    Returns dict {scenario_name: Δh_mm_per_month}.
    """
    b1, b2, b3 = params["b1"], params["b2"], params["b3"]
    h_disp = params["h_disp"]
    Sy = params["Sy"]

    # Load BACI-corrected β₂ multipliers — prefer pipeline params file
    try:
        from utils.pipeline_params import load_params
        _p = load_params(warn_defaults=False)
        clearfell_b2_mult = _p["clearfell_b2_mult"]
        thinning_b2_mult = _p["thinning_b2_mult"]
    except (FileNotFoundError, KeyError):
        clearfell_b2_mult, thinning_b2_mult, _ = load_clearfell_b2_multiplier()
    print(f"   β₂ multipliers: clearfell={clearfell_b2_mult:.4f}  "
          f"thinning={thinning_b2_mult:.4f}")

    # Baseline: CEH36 is unforested, so P_base = raw P
    P_base = summer_P
    flux_base = b1 * P_base - b2 * summer_PET - b3 * h_disp

    def _scenario_dh(P_eff_scen, b2_scen, PET_scen):
        flux_scen = b1 * P_eff_scen - b2_scen * PET_scen - b3 * h_disp
        return round((flux_scen - flux_base) * Sy * 1000, 1)

    scenarios = {}

    # Scraping: observed BACI step, converted to volumetric
    from utils.site_observations import load_site_observation
    scrape_baci_step = load_site_observation("ceh36_baci_pure_scraping")
    scenarios["Scraping\n(observed)"] = round(scrape_baci_step * Sy * 1000, 1)

    # Hypothetical: if CEH36 had pine and was clearfelled
    P_pine_base = summer_P * (1 - FOREST_INTERCEPTION)
    flux_pine_base = b1 * P_pine_base - b2 * summer_PET - b3 * h_disp
    # Clearfell: full P restored, β₂ increases
    flux_cf = b1 * summer_P - b2 * clearfell_b2_mult * summer_PET - b3 * h_disp
    scenarios["Clearfell\n(hypothetical)"] = round(
        (flux_cf - flux_pine_base) * Sy * 1000, 1)

    # Thinning 50%
    P_thin = summer_P * (1 - FOREST_INTERCEPTION * 0.5)
    flux_thin = b1 * P_thin - b2 * thinning_b2_mult * summer_PET - b3 * h_disp
    scenarios["Thinning 50%\n(hypothetical)"] = round(
        (flux_thin - flux_pine_base) * Sy * 1000, 1)

    # Broadleaf conversion — seasonal β₂ profile: deciduous canopy has
    # higher transpiration in summer (full leaf) than evergreen pine.
    # BROADLEAF_B2_SUMMER (1.1125) is the Jun-Sep mean from Script 21's
    # monthly profile; using flat b2 would miss the summer ET penalty.
    P_bl = summer_P * (1 - BROADLEAF_INTERCEPTION)
    flux_bl = b1 * P_bl - b2 * BROADLEAF_B2_SUMMER * summer_PET - b3 * h_disp
    scenarios["Broadleaf\n(hypothetical)"] = round(
        (flux_bl - flux_pine_base) * Sy * 1000, 1)

    # Climate scenarios — applied to CEH36's actual (unforested) state
    scenarios["Climate dry"] = _scenario_dh(
        summer_P * UKCP18_DRY_P_SUMMER, b2, summer_PET * UKCP18_DRY_PET_SUMMER)
    scenarios["Climate wet"] = _scenario_dh(
        summer_P * UKCP18_WET_P_SUMMER, b2, summer_PET * UKCP18_WET_PET_SUMMER)

    print(f"   Scenario responses at CEH36 (mm w.e./month):")
    for name, val in scenarios.items():
        print(f"     {name.replace(chr(10), ' '):30s}  {val:+.1f}")

    return scenarios


# ============================================================================
# FIGURE 1 — MONTHLY BAR CHART
# ============================================================================

def _plot_monthly(scenarios, params):
    """Bar chart: monthly equilibrium Δh at CEH36 under each scenario."""
    names = list(scenarios.keys())
    vals = [scenarios[n] for n in names]
    display_names = [n.replace("\n", "\n") for n in names]

    colours = {
        "Scraping\n(observed)": "#DAA520",
        "Clearfell\n(hypothetical)": "#8B4513",
        "Thinning 50%\n(hypothetical)": "#D2691E",
        "Broadleaf\n(hypothetical)": "#228B22",
        "Climate dry": "#FF6347",
        "Climate wet": "#4169E1",
    }
    hatches = {"Scraping\n(observed)": "///"}
    edge_colours = {"Scraping\n(observed)": "black"}

    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    x = np.arange(len(names))

    for i, (name, val) in enumerate(zip(names, vals)):
        is_scrape = "Scraping" in name
        _col, _hatch, _ec = _bar_style(name, colours, hatches)
        ax.bar(x[i], val, 0.65,
               color=_col,
               edgecolor=_ec,
               linewidth=1.5 if is_scrape else 0.5,
               hatch=_hatch,
               alpha=0.85, zorder=3)
        ax.text(x[i], val + (1.5 if val >= 0 else -1.5),
                f"{val:+.1f}",
                ha="center", va="bottom" if val >= 0 else "top",
                fontsize=11, fontweight="bold", color="#333")

    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(display_names, fontsize=10, ha="center")
    ax.set_ylabel("\u0394 volumetric water table\n(mm water equiv. / month)",
                  fontsize=13)
    ax.set_title(
        "Scenario comparison at CEH36 (scraped site)\n"
        f"SSM coefficients: \u03b2\u2081={params['b1']:.2f}  "
        f"\u03b2\u2082={params['b2']:.2f}  "
        f"\u03b2\u2083={params['b3']:.3f}  "
        f"Sy={params['Sy']:.2f}",
        fontsize=13, fontweight="bold")

    ax.grid(axis="y", alpha=0.25, ls="--")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)

    ax.text(0.02, 0.02,
            "Scraping: observed paired BACI step (+131 mm) "
            "\u00d7 Sy.\n"
            "Forestry scenarios are hypothetical: what if CEH36 "
            "had pine canopy?\n"
            "Climate: UKCP18 RCP8.5 2050s central estimates.",
            transform=ax.transAxes, fontsize=8,
            ha="left", va="bottom", color="#555", style="italic")

    plt.tight_layout()
    fig.savefig(OUT_09D_SCENARIO, dpi=200, format="jpeg",
                pil_kwargs={"quality": 85}, bbox_inches="tight")
    plt.close(fig)
    print(f"   -> {OUT_09D_SCENARIO.name}")

    # Export CSV
    rows = [{"Scenario": n.replace("\n", " "), "Delta_vol_mm_per_month": v}
            for n, v in scenarios.items()]
    pd.DataFrame(rows).to_csv(OUT_09D_SCENARIO_CSV, index=False,
                              float_format="%.1f")
    print(f"   -> {OUT_09D_SCENARIO_CSV.name}")


# ============================================================================
# FIGURE 2 — SUMMER MINIMUM
# ============================================================================

def _plot_summer(scenarios, params, summer_P, summer_PET):
    """Summer minimum comparison at CEH36: observed scraping vs alternatives."""
    wells, climate = load_scraping_data()

    SCRAPE_YEAR = SCRAPING_DATE.year
    FELLING_YEAR = INTERVENTION_DATE.year

    # ── Amplification factor for CEH36 ────────────────────────────────────
    regional = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)
    cluster_col = f"C{params['cluster']}"
    amp = 0.85  # fallback
    if cluster_col in regional.columns:
        annual, summin = {}, {}
        for yr in range(2006, 2026):
            yr_data = regional.loc[regional.index.year == yr, cluster_col].dropna()
            if len(yr_data) >= 8:
                annual[yr] = float(yr_data.mean())
            sm = regional.loc[(regional.index.year == yr) &
                              (regional.index.month.isin(SUMMER_MONTHS)),
                              cluster_col].dropna()
            if len(sm) >= 2:
                summin[yr] = float(sm.min())
        common = sorted(set(annual) & set(summin))
        if len(common) >= 8:
            slope, _, _, _, _ = _stats.linregress(
                [annual[yr] for yr in common],
                [summin[yr] for yr in common])
            amp = slope
    print(f"   Summer amplification factor (C{params['cluster']}): {amp:.3f}")

    # ── Observed scraping summer minimum BACI ─────────────────────────────
    scrape_summer_mm = 0.0
    if WELL in wells.columns and "ceh4" in wells.columns:
        def _ann_sum_min(s):
            mins = {}
            for yr in range(2006, 2026):
                mask = (s.index.year == yr) & (s.index.month.isin(SUMMER_MONTHS))
                sub = s[mask].dropna()
                if len(sub) >= 2:
                    mins[yr] = float(sub.min())
            return mins
        m36 = _ann_sum_min(wells[WELL])
        m4 = _ann_sum_min(wells["ceh4"])
        common = sorted(set(m36) & set(m4))
        gap = pd.Series({yr: m36[yr] - m4[yr] for yr in common})
        pre = gap[gap.index < SCRAPE_YEAR]
        post = gap[(gap.index >= SCRAPE_YEAR) & (gap.index < FELLING_YEAR)]
        if len(pre) >= 2 and len(post) >= 2:
            scrape_summer_mm = (post.mean() - pre.mean()) * 1000
            print(f"   Observed scraping summer min shift "
                  f"(CEH36 vs CEH4): {scrape_summer_mm:+.0f} mm")

    # ── Convert monthly scenarios to summer minimum equivalents ───────────
    Sy = params["Sy"]
    summer_data = {}

    # Scraping: use observed summer BACI directly
    summer_data["Scraping\n(observed)"] = round(scrape_summer_mm)

    # Forestry and climate: monthly vol ÷ Sy → head, × amplification
    for name, vol in scenarios.items():
        if "Scraping" in name:
            continue
        head_mm = vol / Sy  # mm head per month
        summer_data[name] = round(head_mm * amp)

    # ── Figure ────────────────────────────────────────────────────────────
    names = list(summer_data.keys())
    vals = [summer_data[n] for n in names]
    display_names = [n.replace("\n", "\n") for n in names]

    colours = {
        "Scraping\n(observed)": "#DAA520",
        "Clearfell\n(hypothetical)": "#8B4513",
        "Thinning 50%\n(hypothetical)": "#D2691E",
        "Broadleaf\n(hypothetical)": "#228B22",
        "Climate dry": "#FF6347",
        "Climate wet": "#4169E1",
    }
    hatches = {"Scraping\n(observed)": "///"}
    edge_colours = {"Scraping\n(observed)": "black"}

    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    x = np.arange(len(names))

    for i, (name, val) in enumerate(zip(names, vals)):
        is_scrape = "Scraping" in name
        _col, _hatch, _ec = _bar_style(name, colours, hatches)
        ax.bar(x[i], val, 0.65,
               color=_col,
               edgecolor=_ec,
               linewidth=1.5 if is_scrape else 0.5,
               hatch=_hatch,
               alpha=0.85, zorder=3)
        if abs(val) > 5:
            ax.text(x[i], val + (3 if val >= 0 else -3),
                    f"{val:+.0f}",
                    ha="center", va="bottom" if val >= 0 else "top",
                    fontsize=11, fontweight="bold", color="#333")

    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(display_names, fontsize=10, ha="center")
    ax.set_ylabel("\u0394 summer minimum depth (mm)", fontsize=13)
    ax.set_title(
        "Summer minimum scenario comparison at CEH36 (scraped site)\n"
        "Scraping: observed BACI  |  "
        "Alternatives: SSM equilibrium \u00d7 amplification",
        fontsize=13, fontweight="bold")

    ymin = min(min(vals), 0) - 15
    ymax = max(max(vals), 0) + 15
    ax.set_ylim(ymin, ymax)

    ax.grid(axis="y", alpha=0.25, ls="--")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)

    ax.text(0.02, 0.02,
            f"Scraping: observed paired BACI summer minimum shift "
            f"(CEH36 vs CEH4, {scrape_summer_mm:+.0f} mm).\n"
            "Forestry: hypothetical — what if CEH36 had pine canopy "
            "and was then managed.\n"
            f"Climate: UKCP18 RCP8.5 \u00d7 amplification factor "
            f"({amp:.2f}).",
            transform=ax.transAxes, fontsize=8,
            ha="left", va="bottom", color="#555", style="italic")

    plt.tight_layout()
    plt.savefig(OUT_09D_SUMMER_SCENARIO, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"   -> {OUT_09D_SUMMER_SCENARIO.name}")

    # Export CSV
    rows = [{"Scenario": n.replace("\n", " "), "Delta_summer_min_mm": v}
            for n, v in summer_data.items()]
    pd.DataFrame(rows).to_csv(OUT_09D_SUMMER_SCENARIO_CSV, index=False)
    print(f"   -> {OUT_09D_SUMMER_SCENARIO_CSV.name}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
