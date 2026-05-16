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

__version__ = "2.2.0"  # Hollingham (2026) — 2026-05-16
# 2.2.0 — Apply REGIONAL_MEAN_START (2009-02-01) to the regional-mean
#         control series.  CEH4 vs regional-mean Baseline era loses 33
#         pre-2009-02 rows; the Baseline-era mean shifts by ~36 mm in
#         consequence (and so does the apparent Scrape/Felling-era step
#         relative to it).  CEH22 vs regional-mean is unchanged.
# 2.1.0 — Drop "table4"/"Table5" from filename and label.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.paths import (
    make_all_dirs,
    OUT_09_FULL_PARAMS, OUT_09_BETA3_SIG, OUT_09_BACI_SHIFTS,
    OUT_09_NET_BENEFITS, OUT_09_BETA3_ERA_SUMMARY,
    OUT_09_TIER1_DRIFT, OUT_09_TIER2_SIGNAL, OUT_09_BETA3_CI,
    OUT_09_REPORT_NUMBERS,
    OUT_09_TIER1_CUSUM,
)
from utils.scraping_common import (
    SCRAPING_DATE, INTERVENTION_DATE, SCRAPING_DATE_2,
    REGIONAL_MEAN_START,
    WELL_ERAS, CLIMATE_CONTROLS,
    PAIRED_CONTROLS_MAP, TIER1_WELLS, TIER2_WELLS,
    ERA_COLORS, ERA_MARKERS, ERA_LINESTYLES,
    MPL_DEFAULTS, SUMMER_MONTHS,
    era_filter, load_scraping_data,
    format_p_value, significance_stars,
)
from utils.data_utils import calculate_cusum
from utils.config import DRAINAGE_DATUM, HEADLINE_LAG

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.api as sm


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
    df["beta_3"] = df["beta_3_drainage"].round(3)
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

    print("=" * 72)
    print("SCRIPT 09a — HIERARCHICAL PAIRED BACI ANALYSIS")
    print("=" * 72)

    # ── 1. Load data ──────────────────────────────────────────────────────
    print("\n1. Loading Climate and Well Data...")
    wells, climate = load_scraping_data()

    valid_controls = [w for w in CLIMATE_CONTROLS if w in wells.columns]
    control_mean_regional = wells[valid_controls].mean(axis=1)
    # Restrict to the fixed-composition window — pre-2009-02 the regional
    # mean was computed over fewer wells (NW5/6/7 only pre-2006-05;
    # +CEH9 from 2006-05; +WMC2 from 2009-02).  Mixing those compositions
    # introduces spurious step signal in BACI series that use this mean
    # as control.  See scraping_common.py REGIONAL_MEAN_START rationale.
    control_mean_regional = control_mean_regional.where(
        control_mean_regional.index >= REGIONAL_MEAN_START)

    date_2015 = SCRAPING_DATE
    date_felling = INTERVENTION_DATE
    date_2023 = SCRAPING_DATE_2

    # ── 2. Paired statistical analysis ────────────────────────────────────
    print("2. Running Master Statistical Analysis...")
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
                    "beta_1_recharge": round(
                        model_full.params["beta_1_recharge"], 3),
                    "beta_2_atmospheric_draw": round(
                        model_full.params["beta_2_atmospheric_draw"], 3),
                    "beta_3_drainage": round(
                        model_full.params["beta_3_drainage"], 3),
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
                        "Net_Benefit_m": round(after.mean() - before.mean(), 4),
                    })

    # ── 3. Export CSVs ────────────────────────────────────────────────────
    print("3. Exporting CSV files...")
    pd.DataFrame(full_params_results).to_csv(OUT_09_FULL_PARAMS, index=False)
    pd.DataFrame(significance_results).to_csv(OUT_09_BETA3_SIG, index=False)
    pd.DataFrame(baci_results).to_csv(OUT_09_BACI_SHIFTS, index=False)
    pd.DataFrame(net_summary).to_csv(OUT_09_NET_BENEFITS, index=False)
    _export_beta3_era_summary(significance_results)

    # ── 4. Figures ────────────────────────────────────────────────────────
    print("4. Generating the Visual Suite...")
    _plot_tier1(plot_data)
    _plot_tier2(plot_data)
    _plot_beta3_ci(significance_results)

    print("\n--- Absolute Paired-BACI Shifts ---")
    print(pd.DataFrame(baci_results).to_string(index=False))

    # ── 5. Report numbers ─────────────────────────────────────────────────
    print("\nExporting report numbers CSV...")
    _export_report_numbers(plot_data, baci_results, net_summary,
                           significance_results, wells)

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
    for ax in axes.flatten():
        ax.set_xlim(min_date, max_date)
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.setp(ax.get_xticklabels(), rotation=0)
    for ax in axes[0, :]:
        ax.set_xticklabels([])

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
    plt.savefig(OUT_09_TIER1_DRIFT, bbox_inches="tight", dpi=300)
    plt.close()

    # Export final CUSUM values
    cusum_final = {w: float(plot_data[w]["cusum"].iloc[-1])
                   for w in TIER1_WELLS if w in plot_data}
    pd.DataFrame.from_dict(cusum_final, orient="index",
                           columns=["Final_Tier1_CUSUM"]).to_csv(OUT_09_TIER1_CUSUM)
    print(f" -> Saved: {OUT_09_TIER1_DRIFT.name}")


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

    plt.tight_layout()
    fig.suptitle("Tier 2 - Pure Scraping Signal (Paired CUSUM Analysis)",
                 fontsize=16, fontweight="bold", y=1.05)
    plt.savefig(OUT_09_TIER2_SIGNAL, bbox_inches="tight", dpi=300)
    plt.close()
    print(f" -> Saved: {OUT_09_TIER2_SIGNAL.name}")


# ============================================================================
# FIGURE: BETA-3 CONFIDENCE INTERVALS
# ============================================================================

def _plot_beta3_ci(significance_results):
    """β₃ confidence intervals across eras for impact wells."""
    df_sig = pd.DataFrame(significance_results)
    if df_sig.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    wells_to_plot = ["CEH36", "CEH18", "CEH21"]
    df_sig_filtered = df_sig[df_sig["Well"].isin(wells_to_plot)]
    wells_plotted = df_sig_filtered["Well"].unique()
    offsets = [-0.15, 0, 0.15]

    era_order = {
        "1_Baseline": 0, "2_Pure_Scraping": 1, "2_Felling_Pulse": 1,
        "2_Coastal_Drawdown": 1, "3_Felling_Pulse": 2, "3_After_Scraping": 2,
    }

    fill_styles = dict(ERA_COLORS)
    fill_styles["1_Baseline"] = "none"

    for i, w in enumerate(wells_plotted):
        well_data = df_sig_filtered[df_sig_filtered["Well"] == w]
        for j, (_, row) in enumerate(well_data.iterrows()):
            era = row["Era"]
            x_pos = i + offsets[j]
            err_low = row["beta_3_drainage"] - row["Conf_Low"]
            err_high = row["Conf_High"] - row["beta_3_drainage"]
            clean_label = era.split("_", 1)[1].replace("_", " ")
            ax.errorbar(
                x_pos, row["beta_3_drainage"],
                yerr=[[err_low], [err_high]],
                fmt=ERA_MARKERS[era], color=ERA_COLORS[era],
                markerfacecolor=fill_styles[era],
                markeredgecolor=ERA_COLORS[era],
                markersize=8, capsize=5, label=clean_label)

    ax.set_xticks(range(len(wells_plotted)))
    ax.set_xticklabels(wells_plotted)
    ax.set_ylabel(r"Drainage Coefficient ($\beta_3$)")
    ax.set_title(r"Structural Repair ($\beta_3$ Shifts with 95% CI)",
                 fontweight="bold")

    handles, labels = ax.get_legend_handles_labels()
    sorted_items = sorted(zip(labels, handles),
                          key=lambda x: era_order.get(x[0], 99))
    sorted_labels, sorted_handles = zip(*sorted_items)
    by_label = dict(zip(sorted_labels, sorted_handles))
    ax.legend(by_label.values(), by_label.keys(), title="Eras")
    ax.grid(axis="y", ls="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig(OUT_09_BETA3_CI, bbox_inches="tight", dpi=300)
    plt.close()
    print(f" -> Saved: {OUT_09_BETA3_CI.name}")


# ============================================================================
# REPORT NUMBERS EXPORT
# ============================================================================

def _export_report_numbers(plot_data, baci_results, net_summary,
                           significance_results, wells):
    """Export all citable values for §4.5."""
    rows = []

    def rr(parameter, value, unit="m", well="", era="", note=""):
        rows.append({
            "Parameter": parameter, "Well": well, "Era": era,
            "Value": round(value, 4) if pd.notna(value) else "",
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

    report_df = pd.DataFrame(rows)
    report_df.to_csv(OUT_09_REPORT_NUMBERS, index=False)
    print(f" -> Saved: {OUT_09_REPORT_NUMBERS.name} ({len(rows)} rows)")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
