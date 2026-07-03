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

__version__ = "3.6.0"  # Hollingham (2026) — 2026-07-02
# 3.6.0 — SCRAPE_RISE_BUFFER_M now imported from config.py (promoted there with
#         config + Script 20 v1.28.0) instead of a local literal. No behavioural
#         change.
# 3.5.0 — Off-site scraping bar now also shows the 250 m drawdown as a
#         dark reference line drawn ACROSS the 100 m bar (milder, more
#         distant neighbour drawdown), with an inline label. Same drain
#         model / volumetric conversion; 250 m value stashed under a
#         non-plotted "_offsite_far_vol" key and also emitted as an explicit
#         "Scraping (off-site 250 m)" CSV row. Caption updated. Applies to
#         both figures (scrape bars are forcing-independent). No change to
#         the forestry/climate bars or the two-forcing structure of v3.4.0.
# 3.4.0 — Unit-consistent scenario figures + off-site scraping drawdown.
#         Supersedes the in-session v3.3.0 (head re-basis), which is
#         withdrawn. Resolution agreed 2026-07-02:
#         (1) BOTH figures now use ONE volumetric scale (mm water-equiv
#             per month): 09d_01 under annual-mean forcing, 09d_02 under
#             summer (Jul-Sep) forcing. Directly comparable; no head bars,
#             so no head/flux units trap. 09d_02's amplification-to-summer-
#             minimum conversion stays REMOVED (the equilibrium framework
#             cannot resolve a true summer minimum); it is simply the
#             equilibrium volumetric response under summer inputs.
#         (2) Both figures gain a "Scraping (off-site 100 m)" bar: the
#             modelled neighbour drawdown the scrape drain imposes on the
#             surrounding water table, from the same drain cone that feeds
#             the Script 20 maps — H0 anchored to the measured CEH36
#             response, decaying as exp(-(d-buffer)/λ), λ read live from
#             20_report_numbers.csv. Rendered on the volumetric axis (×Sy)
#             to match the other bars.
#         (3) Captions (baked footnote + report caption) now: name the
#             CEH36 SSM coefficients and Sy the volumetric flux is derived
#             from; note that converting to a head change requires dividing
#             by an appropriate (uncertain) Sy and is only approximate;
#             and note that the off-site drawdown decays to the same
#             MAGNITUDE as the clearfell bar (~13.5 mm w.e./month) at
#             ~282 m — i.e. equal to the recharge the standing forest
#             suppresses (a flux comparison, not a head comparison).
#         CSV columns: 09d_01 Delta_vol_mm_per_month (unchanged);
#         09d_02 Delta_summer_min_mm -> Delta_vol_summer_mm_per_month.
#         REPORT IMPACT: Fig 26/27 captions, §4.5.6 and §3.5.3 text revised
#         separately (walk-through before ODT).
# 3.2.0 — Replace hardcoded SCRAPE_BACI_STEP = 0.131 with a
#         load_site_observation("ceh36_baci_pure_scraping") call.
#         The value is now produced by 09a and stored in the
#         pipeline_site_observations.csv registry.  Closes Item 9
#         in flags log.
# 3.1.0 — B2 multiplier via clearfell_common loader.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.paths import (
    make_all_dirs, OUT_09D_SCENARIO, OUT_09D_SCENARIO_CSV,
    OUT_09D_SUMMER_SCENARIO, OUT_09D_SUMMER_SCENARIO_CSV, INT_MASTER_DATA,
    INT_WTF_WELL_SY, INT_WELLS_CLEAN,
    OUT_20_REPORT_NUMBERS,
)
from utils.site_observations import load_site_observation
from utils.scraping_common import (
    MPL_DEFAULTS,
    load_summer_climate,
    load_annual_climate,
)
from utils.config import (
    BW_MODE,
    DRAINAGE_DATUM,
    FOREST_INTERCEPTION, BROADLEAF_INTERCEPTION, BROADLEAF_B2_SUMMER,
    UKCP18_DRY_P_SUMMER, UKCP18_DRY_PET_SUMMER,
    UKCP18_WET_P_SUMMER, UKCP18_WET_PET_SUMMER,
    SCRAPE_RISE_BUFFER_M,
)
from utils.clearfell_common import load_clearfell_b2_multiplier

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)



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

# ----------------------------------------------------------------------------
# Off-site scraping drawdown (neighbour effect)
# ----------------------------------------------------------------------------
# The scrape acts as a local drain: the slack fills (measured on-site benefit)
# while the surrounding water table is drawn DOWN toward it. That neighbour
# drawdown is modelled by the same steady-state drain cone that feeds the
# Script 20 spatial maps:  dd_head(d) = H0 * exp(-(d - buffer) / λ), with
#   H0     = scrape-edge head drawdown = measured CEH36 response (mm),
#   λ      = leaky-aquifer decay length, read LIVE from 20_report_numbers.csv
#            (drawdown_lambda) so this script never re-derives it,
#   buffer = SCRAPE_RISE_BUFFER_M, radius of the rise (slack) zone.
# On the figures the head drawdown is rendered on the volumetric axis (× Sy),
# matching the on-site scraping bar's own head→volumetric conversion.
# 100 m is a representative near-field distance inside the band the 88-well
# network cannot resolve (nearest uphill well 247 m); the bar is therefore a
# MODELLED quantity, flagged as such in the captions.
OFFSITE_DIST_M       = 100.0
OFFSITE_FAR_M        = 250.0    # marker line inside the 100 m bar (near nearest well)
# SCRAPE_RISE_BUFFER_M now imported from config.py
CLEARFELL_MATCH_HINT = 282.0    # ~distance where off-site vol drawdown = clearfell bar


def _load_drawdown_lambda():
    """Read leaky-aquifer decay length λ (m) live from Script 20 output.

    Falls back to 225 m (with a one-line warning) only if Script 20 has not
    been run on this clone, so a figure is still produced but flagged.
    """
    try:
        df = pd.read_csv(OUT_20_REPORT_NUMBERS)
        row = df[df["Parameter"] == "drawdown_lambda"]
        if not row.empty:
            return float(row["Value"].iloc[0])
    except (FileNotFoundError, KeyError, ValueError):
        pass
    warn("20_report_numbers.csv not found — using fallback λ = 225 m. "
         "Run Script 20 for the live value.")
    return 225.0


def _offsite_scrape_head_mm(scrape_edge_head_mm, dist_m=OFFSITE_DIST_M):
    """Modelled neighbour head drawdown (mm, positive magnitude) at dist_m."""
    lam = _load_drawdown_lambda()
    d_eff = max(dist_m - SCRAPE_RISE_BUFFER_M, 0.0)
    return scrape_edge_head_mm * np.exp(-d_eff / lam)


# BW-mode scenario bar styling
_BW_SCENARIO_COLOURS = {
    "Scraping\n(observed)": "#bbbbbb",
    "Scraping\n(off-site 100 m)": "#dddddd",
    "Clearfell\n(hypothetical)": "#333333",
    "Thinning 50%\n(hypothetical)": "#666666",
    "Broadleaf\n(hypothetical)": "#999999",
    "Climate dry": "#444444",
    "Climate wet": "#cccccc",
}
_BW_SCENARIO_HATCHES = {
    "Scraping\n(observed)": "///",
    "Scraping\n(off-site 100 m)": "\\\\\\",
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

    banner("09d", "CEH36 SCENARIO COMPARISON")

    # ── 1. Load CEH36 parameters + both climate forcings ──────────────────
    phase(1, "Loading CEH36 parameters and climate forcings")
    params = _load_ceh36_params()
    annual_P, annual_PET = load_annual_climate()
    summer_P, summer_PET = load_summer_climate()
    print(f"   Annual-mean climate: P={annual_P:.6f}  PET={annual_PET:.6f} m/month")
    print(f"   Summer-mean climate: P={summer_P:.6f}  PET={summer_PET:.6f} m/month")

    # ── 2. Compute scenarios under each forcing ───────────────────────────
    phase(2, "Computing scenario responses at CEH36 (annual + summer forcing)")
    print("   Annual-mean forcing:")
    scen_annual = _compute_ceh36_scenarios(params, annual_P, annual_PET)
    print("   Summer forcing:")
    scen_summer = _compute_ceh36_scenarios(params, summer_P, summer_PET)

    # ── 3. Annual-forcing figure ──────────────────────────────────────────
    phase(3, "Plotting annual-mean forcing scenario comparison")
    _plot_scenarios(scen_annual, params, forcing="annual")

    # ── 4. Summer-forcing figure ──────────────────────────────────────────
    phase(4, "Plotting summer forcing scenario comparison")
    _plot_scenarios(scen_summer, params, forcing="summer")

    print("\nDone.")


# ============================================================================
# SCENARIO COMPUTATION — all at CEH36
# ============================================================================

def _compute_ceh36_scenarios(params, P_force, PET_force):
    """Equilibrium volumetric Δh at CEH36 for each scenario under a given
    climate forcing (P_force, PET_force in m/month).

    Called twice by main(): once with annual-mean climate (Figure 26) and
    once with summer-mean climate (Figure 27). CEH36 is in C3 (not forested),
    so the forestry scenarios show what would happen *if* CEH36's location
    had pine canopy and were then managed — a like-for-like comparison of
    intervention magnitudes at one hydrogeological setting.

    Returns dict {scenario_name: Δh_mm_water_equiv_per_month}.
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
    print(f"     β₂ multipliers: clearfell={clearfell_b2_mult:.4f}  "
          f"thinning={thinning_b2_mult:.4f}")

    # Baseline: CEH36 is unforested, so P_base = raw P
    P_base = P_force
    flux_base = b1 * P_base - b2 * PET_force - b3 * h_disp

    def _scenario_dh(P_eff_scen, b2_scen, PET_scen):
        flux_scen = b1 * P_eff_scen - b2_scen * PET_scen - b3 * h_disp
        return round((flux_scen - flux_base) * Sy * 1000, 1)

    scenarios = {}

    # Scraping: observed BACI step, converted to volumetric
    scrape_baci_step = load_site_observation("ceh36_baci_pure_scraping")
    scenarios["Scraping\n(observed)"] = round(scrape_baci_step * Sy * 1000, 1)

    # Off-site (100 m) neighbour drawdown: the drain draws the surrounding
    # water table down. Modelled head drawdown (from the Script 20 drain
    # cone, anchored to the measured on-site response), then rendered on the
    # same volumetric axis (× Sy) as the on-site bar.
    onsite_edge_head_mm = scrape_baci_step * 1000
    offsite_head_mm = _offsite_scrape_head_mm(onsite_edge_head_mm)  # positive mag
    scenarios["Scraping\n(off-site 100 m)"] = round(
        -(offsite_head_mm / 1000) * Sy * 1000, 1)   # negative = drawdown

    # Far-distance (250 m) drawdown, stashed under a non-plotted key so the
    # plot can draw it as a reference line INSIDE the 100 m bar. Same drain
    # model, same volumetric conversion.
    far_head_mm = _offsite_scrape_head_mm(onsite_edge_head_mm, dist_m=OFFSITE_FAR_M)
    scenarios["_offsite_far_vol"] = round(-(far_head_mm / 1000) * Sy * 1000, 1)

    # Hypothetical: if CEH36 had pine and was clearfelled
    P_pine_base = P_force * (1 - FOREST_INTERCEPTION)
    flux_pine_base = b1 * P_pine_base - b2 * PET_force - b3 * h_disp
    # Clearfell: full P restored, β₂ increases
    flux_cf = b1 * P_force - b2 * clearfell_b2_mult * PET_force - b3 * h_disp
    scenarios["Clearfell\n(hypothetical)"] = round(
        (flux_cf - flux_pine_base) * Sy * 1000, 1)

    # Thinning 50%
    P_thin = P_force * (1 - FOREST_INTERCEPTION * 0.5)
    flux_thin = b1 * P_thin - b2 * thinning_b2_mult * PET_force - b3 * h_disp
    scenarios["Thinning 50%\n(hypothetical)"] = round(
        (flux_thin - flux_pine_base) * Sy * 1000, 1)

    # Broadleaf conversion — seasonal β₂ profile: deciduous canopy has
    # higher transpiration in summer (full leaf) than evergreen pine.
    P_bl = P_force * (1 - BROADLEAF_INTERCEPTION)
    flux_bl = b1 * P_bl - b2 * BROADLEAF_B2_SUMMER * PET_force - b3 * h_disp
    scenarios["Broadleaf\n(hypothetical)"] = round(
        (flux_bl - flux_pine_base) * Sy * 1000, 1)

    # Climate scenarios — applied to CEH36's actual (unforested) state
    scenarios["Climate dry"] = _scenario_dh(
        P_force * UKCP18_DRY_P_SUMMER, b2, PET_force * UKCP18_DRY_PET_SUMMER)
    scenarios["Climate wet"] = _scenario_dh(
        P_force * UKCP18_WET_P_SUMMER, b2, PET_force * UKCP18_WET_PET_SUMMER)

    print("     scenario responses (mm w.e./month):")
    for name, val in scenarios.items():
        if name.startswith("_"):
            continue
        print(f"       {name.replace(chr(10), ' '):30s}  {val:+.1f}")

    return scenarios



# ============================================================================
# FIGURE — VOLUMETRIC SCENARIO BAR CHART (annual or summer forcing)
# ============================================================================

_COLOURS = {
    "Scraping\n(observed)": "#DAA520",
    "Scraping\n(off-site 100 m)": "#E6B84D",
    "Clearfell\n(hypothetical)": "#8B4513",
    "Thinning 50%\n(hypothetical)": "#D2691E",
    "Broadleaf\n(hypothetical)": "#228B22",
    "Climate dry": "#FF6347",
    "Climate wet": "#4169E1",
}
_HATCHES = {"Scraping\n(observed)": "///"}


def _plot_scenarios(scenarios, params, forcing):
    """Volumetric scenario bar chart at CEH36 under a single climate forcing.

    forcing = "annual"  -> Figure 26 (annual-mean P and PET), output 09d_01
    forcing = "summer"  -> Figure 27 (summer Jul-Sep P and PET), output 09d_02

    Both figures use ONE volumetric scale (mm water-equivalent per month) so
    they are directly comparable. Converting a bar to a water-table head
    change requires dividing by an appropriate (uncertain) specific yield and
    is only approximate — noted on the figure and in the report caption.
    """
    is_summer = (forcing == "summer")
    out_fig = OUT_09D_SUMMER_SCENARIO if is_summer else OUT_09D_SCENARIO
    out_csv = OUT_09D_SUMMER_SCENARIO_CSV if is_summer else OUT_09D_SCENARIO_CSV
    col_name = ("Delta_vol_summer_mm_per_month" if is_summer
                else "Delta_vol_mm_per_month")

    # Pull the 250 m far-distance marker value out of the plotted set.
    far_vol = scenarios.get("_offsite_far_vol", None)
    plot_items = [(k, v) for k, v in scenarios.items() if not k.startswith("_")]
    names = [k for k, _ in plot_items]
    vals = [v for _, v in plot_items]
    display_names = [n for n in names]
    offsite_idx = (names.index("Scraping\n(off-site 100 m)")
                   if "Scraping\n(off-site 100 m)" in names else None)

    fig, ax = plt.subplots(figsize=(12, 6.8), dpi=300)
    x = np.arange(len(names))

    for i, (name, val) in enumerate(zip(names, vals)):
        is_scrape = "Scraping" in name
        _col, _hatch, _ec = _bar_style(name, _COLOURS, _HATCHES)
        ax.bar(x[i], val, 0.65, color=_col, edgecolor=_ec,
               linewidth=1.5 if is_scrape else 0.5,
               hatch=_hatch, alpha=0.85, zorder=3)
        ax.text(x[i], val + (1.5 if val >= 0 else -1.5),
                f"{val:+.1f}",
                ha="center", va="bottom" if val >= 0 else "top",
                fontsize=11, fontweight="bold", color="#333")

    # 250 m reference line drawn ACROSS the 100 m off-site bar: shows the
    # milder, more-distant neighbour drawdown as a marker inside the near bar.
    if offsite_idx is not None and far_vol is not None:
        bar_half = 0.65 / 2
        ax.plot([x[offsite_idx] - bar_half, x[offsite_idx] + bar_half],
                [far_vol, far_vol],
                color="#7a4f00", lw=2.0, ls="-", zorder=5)
        ax.text(x[offsite_idx] + bar_half + 0.04, far_vol,
                f"250 m: {far_vol:+.1f}",
                ha="left", va="center", fontsize=8.5,
                fontweight="bold", color="#7a4f00")

    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(display_names, fontsize=10, ha="center")
    ax.set_ylabel("\u0394 volumetric water table\n(mm water equiv. / month)",
                  fontsize=13)

    forcing_label = ("summer (Jul\u2013Sep) forcing" if is_summer
                     else "annual-mean forcing")
    ax.set_title(
        f"Scenario comparison at CEH36 (scraped site) \u2014 {forcing_label}\n"
        f"SSM coefficients: \u03b2\u2081={params['b1']:.2f}  "
        f"\u03b2\u2082={params['b2']:.2f}  "
        f"\u03b2\u2083={params['b3']:.3f}  "
        f"Sy={params['Sy']:.2f}",
        fontsize=13, fontweight="bold")

    ax.grid(axis="y", alpha=0.25, ls="--")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)

    # Shared caveat + forcing-specific note, placed BELOW the axis so it never
    # overlaps the bars (in particular the off-site drawdown bar).
    lam = _load_drawdown_lambda()
    caveat = (
        "Bars are volumetric (mm water-equiv. / month) from CEH36's SSM "
        "coefficients and Sy. A head-change equivalent (mm) needs division "
        "by an appropriate Sy \u2014 uncertain, so approximate.\n"
        "Scraping off-site: modelled neighbour drawdown from the drain cone "
        f"(\u03bb = {lam:.0f} m, live from Script 20); bar = 100 m, dark line "
        "across it = 250 m (milder, more distant)."
    )
    if is_summer:
        caveat += (
            "\nSummer forcing = equilibrium response to Jul\u2013Sep P and "
            "PET, NOT a summer minimum (the equilibrium framework cannot "
            "resolve the transient minimum)."
        )
    else:
        caveat += (
            "\nOff-site drawdown decays with distance; at ~282 m it equals "
            "the clearfell bar in magnitude \u2014 i.e. the recharge the "
            "standing forest itself suppresses."
        )
    ax.text(0.0, -0.16, caveat, transform=ax.transAxes, fontsize=8,
            ha="left", va="top", color="#555", style="italic")

    plt.tight_layout()
    fig.subplots_adjust(bottom=0.24)
    if is_summer:
        fig.savefig(out_fig, dpi=300)
    else:
        fig.savefig(out_fig, dpi=200, format="jpeg",
                    pil_kwargs={"quality": 85})
    plt.close(fig)
    step(f"{out_fig.name}")

    rows = [{"Scenario": n.replace("\n", " "), col_name: v}
            for n, v in scenarios.items() if not n.startswith("_")]
    if far_vol is not None:
        rows.append({"Scenario": "Scraping (off-site 250 m)", col_name: far_vol})
    pd.DataFrame(rows).to_csv(out_csv, index=False, float_format="%.1f")
    step(f"{out_csv.name}")




# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
