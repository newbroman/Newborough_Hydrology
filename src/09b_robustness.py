r"""
====================================================================================
09b — CEH36 SCRAPING ROBUSTNESS ANALYSIS
====================================================================================
Purpose
-------
Three independent estimates of the CEH36 Pure Scraping era step change:
  (1) Raw BACI: CEH36 minus CEH4 (paired control)
  (2) Synthetic control: CEH36 minus a weighted composite of donor wells
  (3) SSM forward residual: observed minus model prediction calibrated
      on the pre-scraping baseline period

Method convergence supports the inference that the +0.13 m benefit at
CEH36 is not an artefact of CEH4's own progressive deepening.

Outputs
-------
Figures:
  09_scrape_08_ceh36_robustness.png — 3-panel: gap series, SSM residual, bar

CSVs:
  09b_report_numbers.csv — robustness step estimates for citation

References
----------
Hollingham (2026), §4.5.  Part of the Script 09 scraping analysis suite.
====================================================================================
"""

__version__ = "2.0.0"  # Hollingham (2026) — modularised from monolithic 09

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.paths import (
    make_all_dirs, OUT_09_ROBUSTNESS, OUT_09B_REPORT_NUMBERS,
    INT_CLIMATE,
    INT_WELLS_CLEAN, INT_WELLS_EXTENDED,
)
from utils.scraping_common import (
    SCRAPING_DATE, INTERVENTION_DATE, SCRAPING_DATE_2,
    DONOR_CANDIDATES, MPL_DEFAULTS,
    load_scraping_data,
)
from utils.config import DRAINAGE_DATUM, HEADLINE_LAG

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm


# ============================================================================
# MAIN
# ============================================================================

def main():
    make_all_dirs()
    plt.rcParams.update(MPL_DEFAULTS)

    print("=" * 72)
    print("SCRIPT 09b — CEH36 SCRAPING ROBUSTNESS ANALYSIS")
    print("=" * 72)

    # ── Load data ─────────────────────────────────────────────────────────
    print("\n1. Loading data...")
    wells, climate = load_scraping_data()

    date_2015 = SCRAPING_DATE
    date_felling = INTERVENTION_DATE
    date_2023 = SCRAPING_DATE_2

    donors = [w for w in DONOR_CANDIDATES if w in wells.columns]

    # Era masks
    baseline_mask = wells.index < date_2015
    scraping_mask = (wells.index >= date_2015) & (wells.index < date_felling)
    felling_mask = (wells.index >= date_felling) & (wells.index < date_2023)
    post23_mask = wells.index >= date_2023

    # ── (1) Raw BACI: CEH36 vs CEH4 ──────────────────────────────────────
    print("\n2. Computing raw BACI...")
    ceh36 = wells["ceh36"]
    ceh4 = wells["ceh4"]
    gap_raw = ceh36 - ceh4

    raw_baseline = gap_raw[baseline_mask].mean()
    raw_scraping = gap_raw[scraping_mask].mean()
    raw_step = raw_scraping - raw_baseline

    print(f"   Raw BACI step: {raw_step:+.3f} m")

    # ── (2) Synthetic control ─────────────────────────────────────────────
    print("3. Computing synthetic control...")
    baseline_X = wells.loc[baseline_mask, donors].dropna()
    baseline_y = ceh36.loc[baseline_X.index]
    valid_idx = baseline_y.notna()
    baseline_X = baseline_X.loc[valid_idx]
    baseline_y = baseline_y.loc[valid_idx]

    if len(baseline_X) >= 24:
        ols = sm.OLS(baseline_y.values, baseline_X.values).fit()
        weights = pd.Series(ols.params, index=donors)
        synthetic = wells[donors].dot(weights)
        gap_syn = ceh36 - synthetic
        syn_baseline = gap_syn[baseline_mask].mean()
        syn_scraping = gap_syn[scraping_mask].mean()
        syn_step = syn_scraping - syn_baseline
        print(f"   Synthetic step: {syn_step:+.3f} m ({len(donors)} donors)")
    else:
        gap_syn = pd.Series(np.nan, index=ceh36.index)
        syn_step = np.nan
        syn_baseline = np.nan
        syn_scraping = np.nan
        weights = pd.Series(dtype=float)
        print(f"  [WARNING] Insufficient baseline overlap "
              f"({len(baseline_X)} months, need >=24)")

    # ── (3) SSM forward residual ──────────────────────────────────────────
    print("4. Computing SSM forward residual...")
    ts = pd.DataFrame({
        "h": ceh36,
        "P": climate["P_m"] * 1000.0,
        "PET": climate["PET"] * 1000.0,
    }).dropna()

    ts["P_lag1"] = ts["P"].shift(HEADLINE_LAG)

    ts_base = ts[ts.index < date_2015].copy()
    ts_base["h_prev"] = ts_base["h"].shift(1)
    ts_base["dh"] = ts_base["h"] - ts_base["h_prev"]
    ts_base = ts_base.dropna()

    if len(ts_base) >= 36:
        X_fit = pd.DataFrame({
            "P": ts_base["P_lag1"],
            "PET_neg": -ts_base["PET"],
            "h_neg": -(DRAINAGE_DATUM + ts_base["h_prev"]),
        })
        model = sm.OLS(ts_base["dh"].values, X_fit.values).fit()
        b1, b2, b3 = model.params

        # Forward simulation
        ts_fwd = ts.copy()
        ts_fwd["h_pred"] = np.nan
        idx_list = list(ts_fwd.index)
        last_base_dt = ts_fwd.index[ts_fwd.index < date_2015].max()

        if pd.notna(last_base_dt):
            h_pred = ts_fwd.loc[last_base_dt, "h"]
            ts_fwd.loc[last_base_dt, "h_pred"] = h_pred
            for dt in idx_list:
                if dt <= last_base_dt:
                    continue
                P_t = ts_fwd.loc[dt, "P_lag1"]
                PET_t = ts_fwd.loc[dt, "PET"]
                if np.isnan(P_t) or np.isnan(PET_t):
                    continue
                dh_pred = b1 * P_t - b2 * PET_t - b3 * (DRAINAGE_DATUM + h_pred)
                h_pred = h_pred + dh_pred
                ts_fwd.loc[dt, "h_pred"] = h_pred

            ts_fwd["residual"] = ts_fwd["h"] - ts_fwd["h_pred"]

            fwd_baseline_mask = ts_fwd.index < date_2015
            fwd_scraping_mask = ((ts_fwd.index >= date_2015)
                                 & (ts_fwd.index < date_felling))
            ssm_baseline = ts_fwd.loc[fwd_baseline_mask, "residual"].mean()
            ssm_scraping = ts_fwd.loc[fwd_scraping_mask, "residual"].mean()
            ssm_step = ssm_scraping - (ssm_baseline
                                       if pd.notna(ssm_baseline) else 0.0)
        else:
            ts_fwd["h_pred"] = np.nan
            ts_fwd["residual"] = np.nan
            ssm_step = np.nan
    else:
        ts_fwd = ts.copy()
        ts_fwd["h_pred"] = np.nan
        ts_fwd["residual"] = np.nan
        ssm_step = np.nan
        print(f"  [WARNING] Insufficient baseline for SSM calibration "
              f"({len(ts_base)} months, need >=36)")

    print(f"   SSM residual step: {ssm_step:+.3f} m")

    # ── Figure ────────────────────────────────────────────────────────────
    print("\n5. Generating robustness figure...")
    _plot_robustness(gap_raw, gap_syn, ts_fwd,
                     raw_baseline, raw_scraping, raw_step,
                     syn_baseline, syn_scraping, syn_step,
                     ssm_step, donors)

    # ── Report numbers ────────────────────────────────────────────────────
    print("\n6. Exporting report numbers...")
    report_rows = [
        {"Parameter": "CEH36_raw_BACI_step", "Value": round(raw_step, 4),
         "Unit": "m", "Note": "CEH36 minus CEH4"},
        {"Parameter": "CEH36_synthetic_control_step",
         "Value": round(syn_step, 4) if pd.notna(syn_step) else "",
         "Unit": "m", "Note": f"Synthetic control ({len(donors)} donors)"},
        {"Parameter": "CEH36_SSM_forward_residual_step",
         "Value": round(ssm_step, 4) if pd.notna(ssm_step) else "",
         "Unit": "m", "Note": "SSM calibrated on pre-2015 baseline"},
    ]
    pd.DataFrame(report_rows).to_csv(OUT_09B_REPORT_NUMBERS, index=False)
    print(f" -> Saved: {OUT_09B_REPORT_NUMBERS.name}")

    print("\nDone.")


# ============================================================================
# FIGURE: THREE-PANEL ROBUSTNESS
# ============================================================================

def _plot_robustness(gap_raw, gap_syn, ts_fwd,
                     raw_baseline, raw_scraping, raw_step,
                     syn_baseline, syn_scraping, syn_step,
                     ssm_step, donors):
    """Three-panel robustness figure."""
    date_2015 = SCRAPING_DATE
    date_felling = INTERVENTION_DATE
    date_2023 = SCRAPING_DATE_2

    fig = plt.figure(figsize=(13, 11), dpi=300)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1.0, 0.9], hspace=0.45)

    # Panel (a): raw BACI vs synthetic control gap series
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(gap_raw.index, gap_raw.values,
             color="#8b5a2b", lw=1.6, alpha=0.85,
             label="CEH36 \u2212 CEH4 (raw BACI)")
    if not np.isnan(syn_step):
        ax1.plot(gap_syn.index, gap_syn.values,
                 color="#1f77b4", lw=1.6, alpha=0.85,
                 label="CEH36 \u2212 synthetic (donor composite)")

    ax1.axhline(raw_baseline, color="#8b5a2b", ls="--", lw=1.0, alpha=0.6)
    if not np.isnan(syn_step):
        ax1.axhline(syn_baseline, color="#1f77b4", ls="--", lw=1.0, alpha=0.6)
        ax1.axhline(syn_scraping, color="#1f77b4", ls=":", lw=1.0, alpha=0.6)
    ax1.axhline(raw_scraping, color="#8b5a2b", ls=":", lw=1.0, alpha=0.6)

    for dt, lbl in [(date_2015, " 2015 scraping"),
                    (date_felling, " felling"),
                    (date_2023, " 2023 rescrape")]:
        ax1.axvline(dt, color="black", ls="--", lw=0.8, alpha=0.5)
        ax1.text(dt, ax1.get_ylim()[1] * 0.95, lbl,
                 fontsize=8, va="top", alpha=0.7)

    ax1.set_ylabel("CEH36 \u2212 reference (m)")
    ax1.set_title("(a) Raw BACI and synthetic control gap series",
                   loc="left", fontweight="bold", fontsize=10)
    ax1.legend(loc="lower left", fontsize=8, framealpha=0.9, ncol=2)
    lo, hi = ax1.get_ylim()
    ax1.set_ylim(lo - 0.08, hi)
    ax1.grid(axis="y", alpha=0.25)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Panel (b): SSM forward residual
    ax2 = fig.add_subplot(gs[1])
    if "residual" in ts_fwd.columns and ts_fwd["residual"].notna().any():
        resid = ts_fwd["residual"].dropna()
        ax2.plot(resid.index, resid.values, color="#2c7a3f", lw=1.4, alpha=0.85,
                 label="SSM forward residual (observed \u2212 predicted)")
        ax2.fill_between(resid.index, 0, resid.values,
                         where=resid.values >= 0,
                         color="#2c7a3f", alpha=0.15, interpolate=True,
                         label="Shallower than SSM prediction (beneficial)")
        ax2.fill_between(resid.index, 0, resid.values,
                         where=resid.values < 0,
                         color="#b85c4a", alpha=0.15, interpolate=True,
                         label="Deeper than SSM prediction")
    ax2.axhline(0, color="black", lw=0.6, alpha=0.6)
    for dt in [date_2015, date_felling, date_2023]:
        ax2.axvline(dt, color="black", ls="--", lw=0.8, alpha=0.5)
    ax2.set_ylabel("Residual (m)")
    ax2.set_title("(b) SSM forward residual at CEH36 \u2014 "
                   "calibrated on pre-2015 baseline",
                   loc="left", fontweight="bold", fontsize=10)
    ax2.legend(loc="lower left", fontsize=7, framealpha=0.9, ncol=3)
    lo, hi = ax2.get_ylim()
    ax2.set_ylim(lo - 0.08, hi)
    ax2.grid(axis="y", alpha=0.25)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    # Panel (c): bar chart
    ax3 = fig.add_subplot(gs[2])
    methods = ["Raw BACI (vs CEH4)",
               f"Synthetic control ({len(donors)} donors)",
               "SSM forward residual"]
    values = [raw_step,
              syn_step if not np.isnan(syn_step) else 0.0,
              ssm_step if not np.isnan(ssm_step) else 0.0]
    colours = ["#8b5a2b", "#1f77b4", "#2c7a3f"]
    bars = ax3.bar(methods, values, color=colours, alpha=0.85,
                   edgecolor="black", linewidth=0.8)

    for bar, val in zip(bars, values):
        y = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2,
                 y + (0.005 if y >= 0 else -0.015),
                 f"{val:+.3f} m",
                 ha="center", va="bottom" if y >= 0 else "top",
                 fontsize=9, fontweight="bold")

    ax3.axhline(0, color="black", lw=0.8)
    ax3.set_ylabel("Pure Scraping era\nstep change (m)")
    ax3.set_title("(c) Pure Scraping era step change \u2014 "
                   "three independent methods",
                   loc="left", fontweight="bold", fontsize=10)
    ymax = max(values) if max(values) > 0 else 0.15
    ax3.set_ylim(min(min(values), 0) - 0.01, ymax * 1.35)
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)
    ax3.grid(axis="y", alpha=0.2)

    fig.suptitle(
        "CEH36 Scraping Robustness Analysis \u2014 Three Independent Methods\n"
        "Newborough Warren 2005\u20132026",
        fontsize=11, fontweight="bold", y=0.975)
    fig.subplots_adjust(left=0.12)

    plt.savefig(OUT_09_ROBUSTNESS, bbox_inches="tight", dpi=300)
    plt.close()
    print(f" -> Saved: {OUT_09_ROBUSTNESS.name}")
    print(f"   Raw BACI step:    {raw_step:+.3f} m")
    print(f"   Synthetic step:   {syn_step:+.3f} m")
    print(f"   SSM residual:     {ssm_step:+.3f} m")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
