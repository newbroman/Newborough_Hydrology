"""
09b_plot_scenario_comparison_REPLACEMENT.py
===========================================
Drop-in replacement for _plot_scenario_comparison() in 09b_scraping_propagation.py.

Also includes the updated _compute_scraping_bars() that loads params directly
instead of using the deleted module-level globals.

INSTRUCTIONS:
1. In 09b, delete SCENARIO_VALUES dict, _init_scenario_globals(), and the three
   module-level None variables (SUMMER_P_MEAN, SUMMER_PET_MEAN, CLUSTER_PARAMS)
2. Replace _compute_scraping_bars() with the version below
3. Replace _plot_scenario_comparison() with the version below
"""


def _compute_scraping_bars(centroids_df):
    """
    Compute scraping scenario bars from BACI-corrected centroid summaries.

    Applies all three coefficient shifts (Δβ₁, Δβ₂, Δβ₃) to each cluster's
    baseline SSM, computes the net monthly flux change, converts to
    volumetric using Sy, and weights by fraction of cluster affected.

    C5 uses C3+CEH31 centroid shifts (same western coastal zone);
    C4 uses C4 centroid shifts. C1 and C2 are zero (too distant).
    """
    from utils.scraping_common import load_cluster_params, load_summer_climate
    from utils.config import FOREST_INTERCEPTION

    cluster_params = load_cluster_params()
    P   = load_summer_climate()[0]
    PET = load_summer_climate()[1]

    # Extract centroid shifts from CSV
    c3_row = centroids_df[centroids_df["group"].str.contains("C3")]
    c4_row = centroids_df[centroids_df["group"].str.contains("C4")]

    if len(c3_row) == 0 or len(c4_row) == 0:
        print("   WARNING: centroid summaries incomplete — "
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
    Grouped bar chart: forest management, scraping, and climate scenarios
    across all k=5 clusters. Non-scraping values from compute_scenario_bars()
    (single source of truth). Scraping bars from BACI centroid shifts.
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from utils.scraping_common import (
        compute_scenario_bars, load_cluster_params, load_summer_climate,
    )
    from utils.paths import OUT_09B_SCENARIO, OUT_09B_SCENARIO_CSV

    clusters = ["C1", "C2", "C3", "C4", "C5"]
    cluster_labels = ["C1\nLake Edge", "C2\nDune", "C3\nWestern",
                      "C4\nMain\nForest", "C5\nCoastal\nForest"]

    # Get non-scraping scenario values from the shared function
    cluster_params = load_cluster_params()
    summer_P, summer_PET = load_summer_climate()
    base_scenarios = compute_scenario_bars(cluster_params, summer_P, summer_PET)

    # Compute scraping bars from centroid BACI shifts
    scrape_w = _compute_scraping_bars(centroids_df)

    scenarios = {}
    for s_name in ["Clearfell", "Thinning 50%", "Broadleaf",
                    "Climate dry", "Climate wet"]:
        if s_name in base_scenarios:
            scenarios[s_name] = (base_scenarios[s_name], {
                "Clearfell": "#8B4513", "Thinning 50%": "#D2691E",
                "Broadleaf": "#228B22", "Climate dry": "#FF6347",
                "Climate wet": "#4169E1",
            }.get(s_name, "#999"), None)

    scenarios["Scraping (nearby)"] = (scrape_w, "#DAA520", "///")

    # Reorder: forestry, scraping, climate
    ordered = ["Clearfell", "Thinning 50%", "Broadleaf",
               "Scraping (nearby)", "Climate dry", "Climate wet"]
    scenarios_ordered = {k: scenarios[k] for k in ordered if k in scenarios}

    n_scen = len(scenarios_ordered)
    x = np.arange(len(clusters))
    width = 0.12
    offsets = np.linspace(-(n_scen - 1) / 2 * width,
                           (n_scen - 1) / 2 * width, n_scen)

    fig, ax = plt.subplots(1, 1, figsize=(14, 7.5))

    for i, (scenario, (vals_dict, colour, hatch)) in enumerate(
            scenarios_ordered.items()):
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
            fontsize=9, fontstyle="italic",
            color="#555555",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#F5F5F5",
                      alpha=0.85, edgecolor="#AAAAAA"),
            ha="right", va="top")

    ax.legend(fontsize=10, loc="lower left", ncol=2, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    fig.savefig(OUT_09B_SCENARIO, dpi=dpi, format="jpeg",
                pil_kwargs={"quality": 85}, bbox_inches="tight")
    plt.close(fig)

    # --- Export CSV ---
    rows = []
    for scenario, (vals_dict, _, _) in scenarios_ordered.items():
        for c in clusters:
            rows.append({"Scenario": scenario, "Cluster": c,
                         "Delta_vol_mm_per_month": round(vals_dict.get(c, 0), 1)})
    pd.DataFrame(rows).to_csv(OUT_09B_SCENARIO_CSV, index=False,
                              float_format="%.1f")
    print(f"   \u2192 {OUT_09B_SCENARIO.name}")
    print(f"   \u2192 {OUT_09B_SCENARIO_CSV.name}")
