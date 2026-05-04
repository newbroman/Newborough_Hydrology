r"""
====================================================================================
09d — SCRAPING SCENARIO COMPARISON
====================================================================================
Purpose
-------
Grouped bar chart comparing forest management, scraping, and climate
scenarios across all k=5 clusters.  Shows the relative magnitude of
scraping benefit against other intervention options.

Two figures:
  1. Monthly volumetric Δ water table (mm w.e./month) — equilibrium SSM
  2. Summer minimum Δ depth (mm) — empirical BACI + SSM amplification

All cluster parameters (β coefficients, Sy, mean head displacement) are
read from upstream pipeline outputs (Scripts 03 and 17), not hardcoded.
Non-scraping scenario values come from Script 21.

Outputs
-------
CSVs:
  09d_01_scenario_comparison.csv        — monthly scenario values
  09d_02_summer_scenario_comparison.csv — summer minimum scenario values

Figures:
  09d_01_scenario_comparison.jpg        — monthly grouped bar chart
  09d_02_summer_scenario_comparison.png — summer minimum grouped bar chart

References
----------
Hollingham (2026), §4.5.  Part of the Script 09 scraping analysis suite.
====================================================================================
"""

__version__ = "2.1.0"  # Hollingham (2026) — reads all params from pipeline

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.paths import (
    make_all_dirs,
    OUT_09B_CENTROIDS, INT_REGIONAL_AVG,
    OUT_09D_SCENARIO, OUT_09D_SCENARIO_CSV,
    OUT_09D_SUMMER_SCENARIO, OUT_09D_SUMMER_SCENARIO_CSV,
    OUT_03_MECHANISTIC_TABLE, INT_MASTER_DATA,
    INT_WTF_WELL_SY, INT_WELLS_CLEAN, INT_CLIMATE,
    OUT_21_SCENARIO_CSV,
)
from utils.scraping_common import (
    SCRAPING_DATE, INTERVENTION_DATE,
    SUMMER_MONTHS, MPL_DEFAULTS,
    load_scraping_data,
)
from utils.config import DRAINAGE_DATUM, FOREST_INTERCEPTION

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as _stats


# ============================================================================
# CONSTANTS (scraping-specific, not available from upstream)
# ============================================================================
GROUND_LOWERING = 0.2   # scraping depth (m) — physical constant
E_CEH36 = 241161.0
N_CEH36 = 363306.0
AFFECTED_RADIUS = 800   # metres from CEH36


# ============================================================================
# DATA LOADING — read everything from pipeline outputs
# ============================================================================

def _load_cluster_params():
    """Load cluster SSM coefficients, Sy, and mean head from pipeline.

    Sources:
      - β coefficients: Script 03 cluster mechanistic table
      - Sy: Script 17 WTF per-well estimates → cluster mean
      - h_disp: Script 01 wells + config.DRAINAGE_DATUM → cluster mean
      - Forest flag: clusters 4 and 5
    """
    # β coefficients from Script 03
    coeff = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
    coeff["cl"] = coeff["Cluster"].astype(int)

    # Sy from Script 17 — cluster means of per-well median Sy
    sy_df = pd.read_csv(INT_WTF_WELL_SY)
    sy_by_cluster = sy_df.groupby("Cluster")["Sy_median"].mean()

    # Mean head displacement from wells
    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells.columns = wells.columns.str.lower().str.replace(" ", "")
    master = pd.read_csv(INT_MASTER_DATA)
    master["match"] = master["Name_Original"].str.lower().str.replace(" ", "")

    params = {}
    for _, row in coeff.iterrows():
        cl = int(row["cl"])
        cname = f"C{cl}"

        # Cluster mean depth → displacement
        cl_wells = master[master["Cluster"] == cl]["match"].tolist()
        available = [w for w in cl_wells if w in wells.columns]
        if available:
            mean_depth = wells[available].mean().mean()
        else:
            mean_depth = -0.5  # fallback
        h_disp = DRAINAGE_DATUM + mean_depth

        params[cname] = {
            "b1": row["beta_1_recharge"],
            "b2": row["beta_2_atmospheric_draw"],
            "b3": row["beta_3_drainage"],
            "Sy": float(sy_by_cluster.get(cl, 0.25)),
            "h_disp": h_disp,
            "forest": cl in (4, 5),
        }

    print(f"   Loaded cluster parameters from pipeline:")
    for c, p in params.items():
        print(f"     {c}: b1={p['b1']:.3f}  b2={p['b2']:.3f}  "
              f"b3={p['b3']:.4f}  Sy={p['Sy']:.3f}  "
              f"h_disp={p['h_disp']:.3f}m  forest={p['forest']}")

    return params


def _load_scenario_values():
    """Load non-scraping scenario values from Script 21 output."""
    if not OUT_21_SCENARIO_CSV.exists():
        print("   [WARNING] Script 21 scenario CSV not found — "
              "using empty scenario values")
        return {}

    df = pd.read_csv(OUT_21_SCENARIO_CSV)
    scenarios = {}
    for scenario in df["Scenario"].unique():
        if "Scraping" in scenario:
            continue  # we compute our own scraping bars
        sub = df[df["Scenario"] == scenario]
        scenarios[scenario] = {
            row["Cluster"]: row["Delta_vol_mm_per_month"]
            for _, row in sub.iterrows()
        }

    print(f"   Loaded {len(scenarios)} non-scraping scenarios from Script 21")
    return scenarios


def _compute_frac_affected():
    """Compute fraction of each cluster within AFFECTED_RADIUS of CEH36."""
    master = pd.read_csv(INT_MASTER_DATA)
    master["dist"] = np.sqrt(
        (master["Easting"] - E_CEH36)**2 +
        (master["Northing"] - N_CEH36)**2
    )
    fracs = {}
    for cl in [1, 2, 3, 4, 5]:
        sub = master[master["Cluster"] == cl]
        n_total = len(sub)
        n_within = (sub["dist"] <= AFFECTED_RADIUS).sum()
        fracs[f"C{cl}"] = n_within / n_total if n_total > 0 else 0.0
    print(f"   Fraction within {AFFECTED_RADIUS}m of CEH36: "
          + "  ".join(f"{c}={v:.0%}" for c, v in fracs.items()))
    return fracs


def _compute_summer_climate():
    """Compute summer mean P and PET from pipeline climate data."""
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    summer = climate[climate.index.month.isin(SUMMER_MONTHS)]
    return float(summer["P_m"].mean()), float(summer["PET"].mean())


# ============================================================================
# MAIN
# ============================================================================

def main():
    make_all_dirs()
    plt.rcParams.update(MPL_DEFAULTS)

    print("=" * 72)
    print("SCRIPT 09d — SCRAPING SCENARIO COMPARISON")
    print("=" * 72)

    # ── 1. Load all parameters from pipeline ──────────────────────────────
    print("\n1. Loading parameters from pipeline outputs...")

    cluster_params = _load_cluster_params()
    scenario_values = _load_scenario_values()
    frac_affected = _compute_frac_affected()
    summer_P, summer_PET = _compute_summer_climate()
    print(f"   Summer climate: P={summer_P:.6f}  PET={summer_PET:.6f} m/month")

    # ── 2. Load centroid summaries ────────────────────────────────────────
    print("\n2. Loading centroid summaries...")
    if not OUT_09B_CENTROIDS.exists():
        print("   [ERROR] 09b_02_centroid_summaries.csv not found — "
              "run 09b_scraping_propagation.py first")
        return
    centroids_df = pd.read_csv(OUT_09B_CENTROIDS)
    print(f"   Loaded {len(centroids_df)} centroid groups")

    # ── 3. Monthly scenario comparison ────────────────────────────────────
    print("\n3. Computing monthly scenario comparison...")
    scrape_weighted = _compute_scraping_bars(
        centroids_df, cluster_params, frac_affected,
        summer_P, summer_PET)
    _plot_scenario_comparison(scenario_values, scrape_weighted,
                              frac_affected)

    # ── 4. Summer minimum scenario comparison ─────────────────────────────
    print("\n4. Computing summer minimum scenario comparison...")
    _summer_scenario(cluster_params, summer_P, summer_PET)

    print("\nDone.")


# ============================================================================
# MONTHLY SCENARIO — SCRAPING BARS
# ============================================================================

def _compute_scraping_bars(centroids_df, cluster_params, frac_affected,
                           summer_P, summer_PET):
    """Compute scraping scenario bars from BACI-corrected centroid shifts."""
    c3_row = centroids_df[centroids_df["group"].str.contains("C3")]
    c4_row = centroids_df[centroids_df["group"].str.contains("C4")]

    if len(c3_row) == 0 or len(c4_row) == 0:
        print("   WARNING: centroid summaries incomplete")
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

        p_eff = summer_P * (1 - FOREST_INTERCEPTION) if c["forest"] else summer_P

        flux_base = (c["b1"] * p_eff - c["b2"] * summer_PET
                     - c["b3"] * c["h_disp"])
        b1_new = c["b1"] + db1
        b2_new = c["b2"] + db2
        b3_new = c["b3"] * (1 + db3_pct)
        h_new = c["h_disp"] - GROUND_LOWERING
        flux_scen = b1_new * p_eff - b2_new * summer_PET - b3_new * h_new

        scrape_unweighted[cname] = (flux_scen - flux_base) * c["Sy"] * 1000

    return {c: scrape_unweighted[c] * frac_affected.get(c, 0.0)
            for c in scrape_unweighted}


def _plot_scenario_comparison(scenario_values, scrape_weighted,
                              frac_affected):
    """Grouped bar chart: forest, scraping, and climate scenarios."""
    clusters = ["C1", "C2", "C3", "C4", "C5"]
    cluster_labels = ["C1\nLake Edge", "C2\nDune", "C3\nWestern",
                      "C4\nMain\nForest", "C5\nCoastal\nForest"]

    scenarios = {}
    colour_map = {
        "Clearfell": ("#8B4513", None), "Thinning 50%": ("#D2691E", None),
        "Broadleaf": ("#228B22", None),
        "Climate dry": ("#FF6347", None), "Climate wet": ("#4169E1", None),
    }
    for s_name, vals in scenario_values.items():
        colour, hatch = colour_map.get(s_name, ("#999", None))
        scenarios[s_name] = (vals, colour, hatch)

    # Insert scraping after Broadleaf
    ordered = {}
    for k, v in scenarios.items():
        ordered[k] = v
        if k == "Broadleaf":
            ordered["Scraping (nearby)"] = (scrape_weighted, "#DAA520", "///")
    if "Scraping (nearby)" not in ordered:
        ordered["Scraping (nearby)"] = (scrape_weighted, "#DAA520", "///")
    scenarios = ordered

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

    ax.axhline(0, color="black", lw=0.8)
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

    # Annotation
    scrape_offset = offsets[list(scenarios.keys()).index("Scraping (nearby)")]
    frac_note = ", ".join(
        f"{c}: {frac_affected.get(c, 0):.0%}"
        for c in ["C3", "C4", "C5"] if frac_affected.get(c, 0) > 0)
    ax.annotate(
        f"Scraping bars: cluster-average\n"
        f"monthly impact on unscraped areas,\n"
        f"weighted by fraction of cluster\n"
        f"within {AFFECTED_RADIUS} m uphill of CEH36\n"
        f"({frac_note})",
        xy=(x[2] + scrape_offset, scrape_weighted.get("C3", 0)),
        xytext=(x[0] - 0.55, -8),
        fontsize=13,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow",
                  alpha=0.9, edgecolor="#DAA520"),
        arrowprops=dict(arrowstyle="->", color="#8B6914", lw=2.0))

    ax.legend(fontsize=12, loc="lower right", ncol=2)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    fig.savefig(OUT_09D_SCENARIO, dpi=200, format="jpeg",
                pil_kwargs={"quality": 85}, bbox_inches="tight")
    plt.close(fig)

    # Export CSV
    rows = []
    for scenario, (vals_dict, _, _) in scenarios.items():
        for c in clusters:
            rows.append({"Scenario": scenario, "Cluster": c,
                         "Delta_vol_mm_per_month": round(
                             vals_dict.get(c, 0), 1)})
    pd.DataFrame(rows).to_csv(OUT_09D_SCENARIO_CSV, index=False,
                              float_format="%.1f")
    print(f"   -> {OUT_09D_SCENARIO.name}")
    print(f"   -> {OUT_09D_SCENARIO_CSV.name}")


# ============================================================================
# SUMMER MINIMUM SCENARIO
# ============================================================================

def _summer_scenario(cluster_params, summer_P, summer_PET):
    """Summer minimum scenario figure: empirical BACI + SSM amplification."""
    wells, climate = load_scraping_data()

    FELLING_YEAR = 2017
    SCRAPE_YEAR = 2015
    clusters = ["C1", "C2", "C3", "C4", "C5"]

    regional = pd.read_csv(INT_REGIONAL_AVG, index_col=0, parse_dates=True)

    # ── Amplification factors ─────────────────────────────────────────────
    amp_factors = {}
    for c in clusters:
        if c not in regional.columns:
            continue
        annual, summin = {}, {}
        for yr in range(2006, 2026):
            yr_data = regional.loc[regional.index.year == yr, c].dropna()
            if len(yr_data) >= 8:
                annual[yr] = float(yr_data.mean())
            sm_mask = ((regional.index.year == yr)
                       & (regional.index.month.isin(SUMMER_MONTHS)))
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

    # ── Helper ────────────────────────────────────────────────────────────
    def _annual_summer_min(series):
        mins = {}
        for yr in range(2006, 2026):
            mask = ((series.index.year == yr)
                    & (series.index.month.isin(SUMMER_MONTHS)))
            s = series[mask].dropna()
            if len(s) >= 2:
                mins[yr] = float(s.min())
        return mins

    # ── Scraping: CEH36 vs CEH18 ─────────────────────────────────────────
    scraping_shift_mm = 0.0
    if "ceh36" in wells.columns and "ceh18" in wells.columns:
        m36 = _annual_summer_min(wells["ceh36"])
        m18 = _annual_summer_min(wells["ceh18"])
        common = sorted(set(m36) & set(m18))
        gap = pd.Series({yr: m36[yr] - m18[yr] for yr in common})
        pre = gap[gap.index < SCRAPE_YEAR]
        post = gap[(gap.index >= SCRAPE_YEAR) & (gap.index < FELLING_YEAR)]
        if len(pre) >= 2 and len(post) >= 2:
            shift = post.mean() - pre.mean()
            _, p_val = _stats.ttest_ind(post.values, pre.values,
                                        equal_var=False)
            scraping_shift_mm = shift * 1000
            print(f"   Scraping (CEH36 vs CEH18): "
                  f"{scraping_shift_mm:+.0f} mm  p = {p_val:.3f}")

    # ── Clearfell: WMC3 + edge wells vs 7-well forest control ─────────────
    clearfell_wells = ["wmc3", "ceh31", "ceh20", "ceh30", "ceh16"]
    forest_ctrls = ["ceh32", "ceh34", "ceh33", "nw10", "ceh19",
                    "ceh2", "ceh17"]
    avail_cf = [w for w in clearfell_wells if w in wells.columns]
    avail_fc = [w for w in forest_ctrls if w in wells.columns]

    fell_shift_mm = 0.0
    if avail_cf and len(avail_fc) >= 2:
        forest_sm = {}
        for yr in range(2006, 2026):
            mask = ((wells.index.year == yr)
                    & (wells.index.month.isin(SUMMER_MONTHS)))
            vals = [wells.loc[mask, w].dropna().min() for w in avail_fc
                    if len(wells.loc[mask, w].dropna()) >= 2]
            if len(vals) >= 2:
                forest_sm[yr] = np.mean(vals)

        well_shifts = []
        for w in avail_cf:
            w_sm = _annual_summer_min(wells[w])
            common_w = sorted(set(w_sm) & set(forest_sm))
            if len(common_w) < 5:
                continue
            gap_w = pd.Series({yr: w_sm[yr] - forest_sm[yr]
                               for yr in common_w})
            pre_w = gap_w[gap_w.index < FELLING_YEAR]
            post_w = gap_w[gap_w.index >= FELLING_YEAR]
            if len(pre_w) >= 5 and len(post_w) >= 3:
                well_shifts.append(post_w.mean() - pre_w.mean())
        if well_shifts:
            fell_shift_mm = np.mean(well_shifts) * 1000
            print(f"   Clearfell (vs forest ctrl): "
                  f"{fell_shift_mm:+.0f} mm (n={len(well_shifts)} wells)")

    # ── Scenario table ────────────────────────────────────────────────────
    summer_data = {
        "Clearfell": {c: (round(fell_shift_mm) if c in ["C4", "C5"]
                          else 0) for c in clusters},
        "Thinning 50%": {c: (round(fell_shift_mm * 0.5) if c in ["C4", "C5"]
                             else 0) for c in clusters},
        "Broadleaf": {c: 0 for c in clusters},
        "Scraping\n(CEH36-type)": {"C1": 0, "C2": 0, "C3": 0, "C4": 0,
                                    "C5": round(scraping_shift_mm)},
    }

    # Climate: SSM vol → head (÷ Sy) → summer min (× amplification)
    if OUT_09D_SCENARIO_CSV.exists():
        scen = pd.read_csv(OUT_09D_SCENARIO_CSV)
        for scenario in ["Climate dry", "Climate wet"]:
            summer_data[scenario] = {}
            for c in clusters:
                row = scen[(scen["Scenario"] == scenario)
                           & (scen["Cluster"] == c)]
                if not row.empty:
                    vol = float(row["Delta_vol_mm_per_month"].iloc[0])
                    sy = cluster_params.get(c, {}).get("Sy", 0.20)
                    summer_data[scenario][c] = round(
                        vol / sy * amp_factors.get(c, 0.85))
                else:
                    summer_data[scenario][c] = 0

    # ── Figure ────────────────────────────────────────────────────────────
    cluster_labels = ["C1\nLake Edge", "C2\nDune", "C3\nWestern",
                      "C4\nMain\nForest", "C5\nCoastal\nForest"]
    colours = {
        "Clearfell": "#8B6914", "Thinning 50%": "#D2691E",
        "Broadleaf": "#228B22", "Scraping\n(CEH36-type)": "#DAA520",
        "Climate dry": "#E8726E", "Climate wet": "#5B9BD5",
    }
    hatches = {"Scraping\n(CEH36-type)": "///"}
    scenarios_order = [s for s in ["Clearfell", "Thinning 50%", "Broadleaf",
                                    "Scraping\n(CEH36-type)",
                                    "Climate dry", "Climate wet"]
                       if s in summer_data]

    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    n_sc = len(scenarios_order)
    bw = 0.8 / n_sc
    x = np.arange(len(clusters))

    for i, s_name in enumerate(scenarios_order):
        vals = [summer_data[s_name].get(c, 0) for c in clusters]
        offset = (i - n_sc / 2 + 0.5) * bw
        hatch = hatches.get(s_name, "")
        ax.bar(x + offset, vals, bw * 0.9,
               color=colours.get(s_name, "#999"),
               edgecolor="black" if hatch else colours.get(s_name, "#999"),
               linewidth=0.8 if hatch else 0.5,
               hatch=hatch, alpha=0.85, label=s_name, zorder=3)
        for j, v in enumerate(vals):
            if abs(v) > 20:
                ax.text(x[j] + offset, v + (4 if v > 0 else -4),
                        f"{v:+.0f}", ha="center",
                        va="bottom" if v > 0 else "top",
                        fontsize=7.5, fontweight="bold", color="#333")

    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cluster_labels, fontsize=11)
    ax.set_ylabel("\u0394 summer minimum depth (mm)", fontsize=12)
    ax.set_title(
        "Summer minimum scenario comparison: forest management, "
        "scraping, and climate (k = 5)\n"
        "Forest management: empirical BACI  |  Climate: SSM equilibrium "
        "\u00d7 amplification factor",
        fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, loc="lower left", framealpha=0.9, ncol=3)
    ax.grid(axis="y", alpha=0.25, ls="--")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.text(0.98, 0.02,
            f"Scraping: empirical BACI at scraped site "
            f"(CEH36 vs CEH18, {scraping_shift_mm:+.0f} mm). "
            f"Benefit is local.\n"
            f"Forest management: empirical BACI "
            f"(WMC3 + 4 edge wells vs 7-well forest control, "
            f"{fell_shift_mm:+.0f} mm).\n"
            "Climate: SSM annual-mean prediction "
            "\u00d7 empirical summer amplification factor.",
            transform=ax.transAxes, fontsize=7.5, ha="right", va="bottom",
            color="#555", style="italic")
    plt.tight_layout()
    plt.savefig(OUT_09D_SUMMER_SCENARIO, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"   -> {OUT_09D_SUMMER_SCENARIO.name}")

    # Export CSV
    rows = []
    for s_name in scenarios_order:
        for c in clusters:
            rows.append({"Scenario": s_name.replace("\n", " "),
                         "Cluster": c,
                         "Delta_summer_min_mm":
                             summer_data[s_name].get(c, 0)})
    pd.DataFrame(rows).to_csv(OUT_09D_SUMMER_SCENARIO_CSV, index=False)
    print(f"   -> {OUT_09D_SUMMER_SCENARIO_CSV.name}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
