r"""

====================================================================================
09c — SUMMER MINIMA ANALYSIS (DUAL CONTROL)
====================================================================================
Purpose
-------
Evaluates the scraping effect on the ecologically critical annual summer
minimum depth (Jun–Sep) at CEH36 and secondary impact wells (CEH18, CEH21).
Runs against both climate and paired control centroids.  Each well's gap
(well summer min − control centroid summer min) is compared pre- vs post-
scraping via Welch t-test.

Mirrors the methodology of Script 10d (clearfell summer minima) but
applied to the scraping intervention timeline.

The ecological question: does scraping improve the critical summer low
(which determines dune slack habitat viability), not just the annual mean?

Outputs
-------
CSVs:
  09c_01_summer_minima.csv           — per-well, per-year summer minima
  09c_02_summer_minima_shifts.csv    — per-well pre/post shift summary
  09c_report_numbers.csv             — all citable values

Figures:
  09c_03_summer_minima_climate_ctrl.png — 3-panel: raw, impact gap, control gap
  09c_04_summer_minima_paired.png       — paired BACI: CEH36 vs CEH4

References
----------
Hollingham (2026), §4.5.  Part of the Script 09 scraping analysis suite.
====================================================================================
"""

__version__ = "1.4.0"  # Hollingham (2026) — 2026-07-14
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)

from utils.paths import (
    make_all_dirs,
    OUT_09C_SUMMER_MINIMA, OUT_09C_SUMMER_SHIFTS, OUT_09C_REPORT_NUMBERS,
    OUT_09C_FIG_CLIMATE, OUT_09C_FIG_PAIRED,
)
from utils.scraping_common import (
    SCRAPING_DATE, INTERVENTION_DATE, SCRAPING_DATE_2, CLIMATE_CONTROLS, SUMMER_MONTHS,
    TIER1_WELLS, TIER2_WELLS, PAIRED_CONTROLS_MAP,
    MPL_DEFAULTS,
    load_scraping_data, format_p_value, significance_stars,
)
from utils.clearfell_common import (
    annual_summer_minimum, forest_control_centroid_summer_min,
)
from utils.config import EQUIL_RESIDUAL_WINDOW_YEARS, EQUIL_MIN_FIT_POINTS
from utils.render_utils import render_figure

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as sp_stats


def equilibration_stats(gap_by_year, event_year, resid_window, min_pts):
    """Characterise a post-intervention summer-minimum relaxation transient.

    Parameters
    ----------
    gap_by_year : dict {year: gap_m}
        Annual summer-minimum gap (well - control centroid), in metres.
    event_year : int
        Intervention year; the peak is searched strictly after this year.
    resid_window : int
        Residual plateau = mean of the final ``resid_window`` summer years.
    min_pts : int
        Minimum annual points required to report an OLS slope.

    Returns
    -------
    dict or None
        peak / peak_year / residual / resid_start / resid_end / last, plus
        ``from_peak`` and ``from_event`` slope dicts (or None). Each slope dict:
        slope_m_per_yr, p, r2, n, start, end. ``from_peak`` is None when the
        peak is the final year (degenerate — no post-peak decay to fit).
    """
    yrs = sorted(y for y in gap_by_year
                 if gap_by_year[y] == gap_by_year[y])  # drop NaN
    if not yrs:
        return None
    g = {y: gap_by_year[y] for y in yrs}
    last = yrs[-1]
    post_years = [y for y in yrs if y > event_year]
    if not post_years:
        return None
    peak_year = max(post_years, key=lambda y: g[y])
    resid_years = [y for y in yrs if y >= last - resid_window + 1]
    residual = float(np.mean([g[y] for y in resid_years])) if resid_years else float("nan")

    def _slope(start):
        xs = [y for y in yrs if y >= start]
        if len(xs) < min_pts:
            return None
        ys = [g[y] for y in xs]
        r = sp_stats.linregress(xs, ys)
        return {"slope_m_per_yr": float(r.slope), "p": float(r.pvalue),
                "r2": float(r.rvalue ** 2), "n": len(xs),
                "start": int(start), "end": int(last)}

    return {
        "peak": float(g[peak_year]), "peak_year": int(peak_year),
        "residual": residual,
        "resid_start": int(last - resid_window + 1), "resid_end": int(last),
        "last": int(last),
        "from_peak": _slope(peak_year) if peak_year < last else None,
        "from_event": _slope(event_year + 1),
    }


def main():
    make_all_dirs()
    plt.rcParams.update(MPL_DEFAULTS)

    banner("09c", "SUMMER MINIMA ANALYSIS (DUAL CONTROL)")

    phase(1, "Loading data")
    wells, wells_provenance, climate = load_scraping_data()
    all_wells = sorted(set(TIER1_WELLS + TIER2_WELLS))
    # Year range — annual analyses use 2011+ rather than 2006+.
    # Rationale: 2011 is the first year every scraping-suite well
    # (impacts + paired controls + 5 regional climate controls) has
    # complete observed Jun–Sep coverage.  CEH36 starts 2011-01-01 so
    # its first full summer is 2011; CEH21/CEH22 first full summer is
    # 2010, but CEH36's binding constraint pulls the network start to
    # 2011 if every well is to contribute a balanced summer minimum.
    # This script does NOT use the CEH34 donor-regression hindcast —
    # different well network and different methodological asymmetry
    # (annual extremes don't tolerate hindcasts as well as monthly
    # analyses do; see 10d v1.2.0 changelog).
    first_year = max(2011, wells.index.min().year)
    last_year = min(2025, wells.index.max().year)

    phase(2, "Computing annual summer minima")
    # Per Defect E fix (scraping_common v1.3.0, 2026-05-19): pass
    # provenance to annual_summer_minimum so that years with fewer than
    # 2 measured Jun-Sep months for a given well are excluded. This
    # drops the phantom 2019 summer minima for NW6 and NW7 (both in
    # CLIMATE_CONTROLS) that arose from the old limit=3 interpolation
    # policy.
    well_mins = {}
    n_interpolated_per_well_year = {}
    for w in all_wells:
        if w in wells.columns:
            prov_w = (wells_provenance[w]
                      if w in wells_provenance.columns else None)
            well_mins[w] = annual_summer_minimum(
                wells[w], first_year, last_year,
                provenance=prov_w, min_measured=2,
            )
            # Diagnostic count of interpolated Jun-Sep cells per year
            # (cells that, under limit=1, are still in the cleaned
            # series but are flagged interpolated). They count toward
            # the minimum because limit=1 retains them, but reviewers
            # can see them via the n_interpolated column below.
            if prov_w is not None:
                for yr in range(first_year, last_year + 1):
                    mask = ((wells[w].index.year == yr)
                            & (wells[w].index.month.isin(SUMMER_MONTHS)))
                    n_interp = int((prov_w[mask] == 'interpolated').sum())
                    n_interpolated_per_well_year[(w, yr)] = n_interp

    climate_centroid_mins = forest_control_centroid_summer_min(
        wells, CLIMATE_CONTROLS, first_year, last_year,
        wells_provenance=wells_provenance, min_measured=2)
    paired_mins = {}
    for ctrl in sorted(set(PAIRED_CONTROLS_MAP.values())):
        if ctrl in wells.columns:
            prov_ctrl = (wells_provenance[ctrl]
                         if ctrl in wells_provenance.columns else None)
            paired_mins[ctrl] = annual_summer_minimum(
                wells[ctrl], first_year, last_year,
                provenance=prov_ctrl, min_measured=2,
            )

    print(f"   {len(well_mins)} wells, {len(climate_centroid_mins)} centroid years")

    # ── 3. Export per-well summer minima ───────────────────────────────────
    phase(3, "Exporting per-well summer minima")
    data_rows = []
    for w in all_wells:
        if w not in well_mins:
            continue
        for yr, val in well_mins[w].items():
            row = {
                "Well": w.upper(),
                "Year": yr,
                "Summer_min_m": round(val, 4),
                "n_interpolated": n_interpolated_per_well_year.get((w, yr), 0),
            }
            if yr in climate_centroid_mins:
                row["Climate_ctrl_centroid_m"] = round(climate_centroid_mins[yr], 4)
                row["Gap_climate_m"] = round(val - climate_centroid_mins[yr], 4)
            ctrl = PAIRED_CONTROLS_MAP.get(w)
            if ctrl and ctrl in paired_mins and yr in paired_mins[ctrl]:
                row["Paired_ctrl_m"] = round(paired_mins[ctrl][yr], 4)
                row["Gap_paired_m"] = round(val - paired_mins[ctrl][yr], 4)
            data_rows.append(row)
    data_df = pd.DataFrame(data_rows)
    data_df.to_csv(OUT_09C_SUMMER_MINIMA, index=False)
    saved(f"{OUT_09C_SUMMER_MINIMA.name} ({len(data_df)} rows)")

    # ── 4. Compute pre/post shifts ────────────────────────────────────────
    phase(4, "Computing pre/post shifts")
    POST_YEAR = SCRAPING_DATE.year
    shift_rows = []
    report_rows = []

    for w in all_wells:
        if w not in well_mins:
            continue
        for ctrl_label, centroid_mins in [
            ("Climate", climate_centroid_mins),
            ("Paired", paired_mins.get(PAIRED_CONTROLS_MAP.get(w, ""), {})),
        ]:
            if not centroid_mins:
                continue
            gaps_pre, gaps_post = [], []
            for yr, val in well_mins[w].items():
                if yr not in centroid_mins:
                    continue
                gap = val - centroid_mins[yr]
                (gaps_pre if yr < POST_YEAR else gaps_post).append(gap)
            if len(gaps_pre) < 2 or len(gaps_post) < 2:
                continue
            pre_mean = np.mean(gaps_pre)
            post_mean = np.mean(gaps_post)
            shift = post_mean - pre_mean
            t_stat, p_val = sp_stats.ttest_ind(gaps_post, gaps_pre, equal_var=False)
            shift_rows.append({
                "Well": w.upper(), "Control": ctrl_label,
                "N_pre": len(gaps_pre), "N_post": len(gaps_post),
                "Pre_mean_gap_m": round(pre_mean, 4),
                "Post_mean_gap_m": round(post_mean, 4),
                "Shift_m": round(shift, 4), "Shift_mm": round(shift * 1000, 1),
                "t_stat": round(t_stat, 3), "p_value": p_val,
                "Sig": significance_stars(p_val),
            })
            report_rows.append({
                "Parameter": "Summer_min_BACI_shift", "Well": w.upper(),
                "Control": ctrl_label, "Value": round(shift, 4), "Unit": "m",
                "Note": f"n_pre={len(gaps_pre)}, n_post={len(gaps_post)}, p={format_p_value(p_val)}",
            })

    shift_df = pd.DataFrame(shift_rows)
    shift_df.to_csv(OUT_09C_SUMMER_SHIFTS, index=False)
    saved(f"{OUT_09C_SUMMER_SHIFTS.name} ({len(shift_df)} rows)")

    print("\n   Summer minimum shifts (mm):")
    for ctrl_label in ["Climate", "Paired"]:
        ctrl_shifts = shift_df[shift_df["Control"] == ctrl_label]
        if ctrl_shifts.empty:
            continue
        print(f"\n   {ctrl_label} control:")
        for _, row in ctrl_shifts.iterrows():
            sig = " *" if row["p_value"] < 0.05 else ""
            print(f"     {row['Well']:<8}  shift = {row['Shift_mm']:+6.0f} mm  "
                  f"p = {format_p_value(row['p_value'])}{sig}")

    # ── 4b. Scrape equilibration (decay) characterisation at CEH36 ────────
    # Characterise the summer-minimum-gap relaxation transient: peak, residual
    # plateau, and post-peak / from-scrape OLS decay slopes. Emitted for the
    # climate-corrected gap (headline) and the CEH36-CEH4 paired gap
    # (robustness). Reported soft; windows derive from SCRAPING_DATE, the
    # observed peak, and last_year (no hardcoded years).
    info("Characterising scrape equilibration (decay) at CEH36")
    if "ceh36" in well_mins:
        c36 = well_mins["ceh36"]
        equil_specs = [("Climate", climate_centroid_mins)]
        ceh36_paired = PAIRED_CONTROLS_MAP.get("ceh36")
        if ceh36_paired and ceh36_paired in paired_mins:
            equil_specs.append(("Paired", paired_mins[ceh36_paired]))
        for ctrl_label, centroid in equil_specs:
            gap = {yr: c36[yr] - centroid[yr]
                   for yr in c36 if yr in centroid}
            eq = equilibration_stats(gap, SCRAPING_DATE.year,
                                     EQUIL_RESIDUAL_WINDOW_YEARS,
                                     EQUIL_MIN_FIT_POINTS)
            if eq is None:
                warn(f"CEH36 {ctrl_label}: insufficient data for equilibration")
                continue
            no_turnover = eq["peak_year"] >= eq["last"]
            report_rows.append({
                "Parameter": "Scrape_equilibration_peak", "Well": "CEH36",
                "Control": ctrl_label, "Value": round(eq["peak"], 4), "Unit": "m",
                "Note": (f"year={eq['peak_year']}"
                         + (" (series maximum is the final year \u2014 no turnover)"
                            if no_turnover else "")),
            })
            report_rows.append({
                "Parameter": "Scrape_equilibration_residual", "Well": "CEH36",
                "Control": ctrl_label, "Value": round(eq["residual"], 4), "Unit": "m",
                "Note": (f"mean {eq['resid_start']}-{eq['resid_end']} "
                         f"(final {EQUIL_RESIDUAL_WINDOW_YEARS} yr)"),
            })
            if eq["from_peak"]:
                fp = eq["from_peak"]
                report_rows.append({
                    "Parameter": "Scrape_equilibration_slope_from_peak",
                    "Well": "CEH36", "Control": ctrl_label,
                    "Value": round(fp["slope_m_per_yr"], 5), "Unit": "m/yr",
                    "Note": (f"OLS {fp['start']}-{fp['end']}, "
                             f"p={format_p_value(fp['p'])}, "
                             f"R2={fp['r2']:.2f}, n={fp['n']} (plain OLS, no AR1)"),
                })
            else:
                report_rows.append({
                    "Parameter": "Scrape_equilibration_slope_from_peak",
                    "Well": "CEH36", "Control": ctrl_label,
                    "Value": "", "Unit": "m/yr",
                    "Note": "degenerate \u2014 peak at final year (no post-peak decay)",
                })
            if eq["from_event"]:
                fe = eq["from_event"]
                report_rows.append({
                    "Parameter": "Scrape_equilibration_slope_from_scrape",
                    "Well": "CEH36", "Control": ctrl_label,
                    "Value": round(fe["slope_m_per_yr"], 5), "Unit": "m/yr",
                    "Note": (f"OLS {fe['start']}-{fe['end']}, "
                             f"p={format_p_value(fe['p'])}, "
                             f"R2={fe['r2']:.2f}, n={fe['n']} (plain OLS, no AR1)"),
                })
            fp_txt = (f"{eq['from_peak']['slope_m_per_yr']*1000:+.1f} mm/yr"
                      if eq["from_peak"] else "n/a (peak at final yr)")
            fe_txt = (f"{eq['from_event']['slope_m_per_yr']*1000:+.1f} mm/yr"
                      if eq["from_event"] else "n/a")
            print(f"     [{ctrl_label}] peak {eq['peak']*1000:+.0f} mm @ "
                  f"{eq['peak_year']}  residual {eq['residual']*1000:+.0f} mm  "
                  f"slope(peak\u2192) {fp_txt}  slope(scrape\u2192) {fe_txt}")
    else:
        warn("CEH36 not in well_mins \u2014 skipping equilibration characterisation")

    # ── 5. Figures ────────────────────────────────────────────────────────
    phase(5, "Generating figures")
    _plot_climate_control(well_mins, climate_centroid_mins, POST_YEAR)
    _plot_paired(well_mins, paired_mins, POST_YEAR)

    # ── 6. Report numbers ─────────────────────────────────────────────────
    phase(6, "Exporting report numbers")
    pd.DataFrame(report_rows).to_csv(OUT_09C_REPORT_NUMBERS, index=False)
    saved(f"{OUT_09C_REPORT_NUMBERS.name} ({len(report_rows)} rows)")
    print("\nDone.")


# ============================================================================
# FIGURES
# ============================================================================

def _plot_climate_control(well_mins, climate_centroid_mins, post_year):
    years = sorted(climate_centroid_mins.keys())
    ctrl_vals = [climate_centroid_mins[yr] for yr in years]
    show_wells = ["ceh36", "ceh4", "ceh18", "ceh21", "ceh22"]
    wc = {"ceh36": "#d62728", "ceh4": "#ff7f0e", "ceh18": "#2ca02c",
          "ceh21": "#1f77b4", "ceh22": "#9467bd"}

    fig, axes = plt.subplots(3, 1, figsize=(14, 14), dpi=300, sharex=True)

    ax = axes[0]
    ax.plot(years, ctrl_vals, "k--", lw=2, alpha=0.6, label="Climate ctrl centroid", zorder=3)
    for w in show_wells:
        if w not in well_mins:
            continue
        wy = sorted(well_mins[w].keys())
        ax.plot(wy, [well_mins[w][yr] for yr in wy], "o-", color=wc.get(w, "#999"),
                lw=1.5, ms=5, alpha=0.8, label=w.upper())
    ax.axvline(post_year - 0.5, color="#DAA520", ls="--", lw=2, alpha=0.7, label="Scraping (Apr 2015)")
    ax.axvline(INTERVENTION_DATE.year + 0.5, color="#1b5e20", ls="-.", lw=2, alpha=0.8, label="Clearfell (Dec 2017)")
    ax.axvline(SCRAPING_DATE_2.year + 0.5, color="#e7298a", ls="-.", lw=2, alpha=0.8, label="Re-scrape (Oct 2023)")
    ax.axhline(-0.61, color="green", ls=":", alpha=0.4, label="Wet slack threshold")
    ax.axhline(-0.98, color="brown", ls=":", alpha=0.4, label="Dry slack threshold")
    ax.set_ylabel("Summer minimum depth (m)")
    ax.set_title("(a) Raw annual summer minimum (Jun\u2013Sep)", loc="left", fontweight="bold")
    ax.legend(fontsize=8, ncol=3, loc="lower left",
              bbox_to_anchor=(INTERVENTION_DATE.year + 0.5, 0.0),
              bbox_transform=ax.get_xaxis_transform(), framealpha=0.9)
    ax.grid(axis="y", alpha=0.25)
    ax.invert_yaxis()

    ax = axes[1]
    for w in ["ceh36", "ceh18", "ceh21"]:
        if w not in well_mins:
            continue
        common = sorted(set(well_mins[w].keys()) & set(climate_centroid_mins.keys()))
        gaps = [well_mins[w][yr] - climate_centroid_mins[yr] for yr in common]
        ax.plot(common, gaps, "o-", color=wc.get(w, "#999"), lw=1.5, ms=5, alpha=0.8, label=w.upper())
        pre = [g for yr, g in zip(common, gaps) if yr < post_year]
        post = [g for yr, g in zip(common, gaps) if yr >= post_year]
        if pre:
            ax.axhline(np.mean(pre), color=wc.get(w, "#999"), ls=":", lw=1, alpha=0.5)
        if post:
            ax.axhline(np.mean(post), color=wc.get(w, "#999"), ls="--", lw=1, alpha=0.5)
    ax.axvline(post_year - 0.5, color="#DAA520", ls="--", lw=2, alpha=0.7)
    ax.axvline(INTERVENTION_DATE.year + 0.5, color="#1b5e20", ls="-.", lw=2, alpha=0.8)
    ax.axvline(SCRAPING_DATE_2.year + 0.5, color="#e7298a", ls="-.", lw=2, alpha=0.8)
    ax.axhline(0, color="black", lw=0.6, alpha=0.5)
    ax.set_ylabel("Gap: well \u2212 climate ctrl (m)")
    ax.set_title("(b) Impact well gaps vs climate control centroid", loc="left", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.25)

    ax = axes[2]
    for w in ["ceh4", "ceh22"]:
        if w not in well_mins:
            continue
        common = sorted(set(well_mins[w].keys()) & set(climate_centroid_mins.keys()))
        gaps = [well_mins[w][yr] - climate_centroid_mins[yr] for yr in common]
        ax.plot(common, gaps, "o-", color=wc.get(w, "#999"), lw=1.5, ms=5, alpha=0.8, label=w.upper())
    ax.axvline(post_year - 0.5, color="#DAA520", ls="--", lw=2, alpha=0.7)
    ax.axvline(INTERVENTION_DATE.year + 0.5, color="#1b5e20", ls="-.", lw=2, alpha=0.8)
    ax.axvline(SCRAPING_DATE_2.year + 0.5, color="#e7298a", ls="-.", lw=2, alpha=0.8)
    ax.axhline(0, color="black", lw=0.6, alpha=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Gap: well \u2212 climate ctrl (m)")
    ax.set_title("(c) Control well gaps vs climate control centroid", loc="left", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.25)

    fig.suptitle("Summer Minimum Analysis \u2014 Scraping Intervention\n"
                 "Annual Jun\u2013Sep minimum depth vs climate control centroid",
                 fontsize=13, fontweight="bold", y=0.995)
    plt.tight_layout()
    render_figure(plt.gcf(), OUT_09C_FIG_CLIMATE)
    plt.close()
    saved(f"{OUT_09C_FIG_CLIMATE.name}")


def _plot_paired(well_mins, paired_mins, post_year):
    if "ceh36" not in well_mins or "ceh4" not in paired_mins:
        warn("CEH36 or CEH4 missing — skipping paired figure")
        return
    ceh4_mins = paired_mins["ceh4"]
    common = sorted(set(well_mins["ceh36"].keys()) & set(ceh4_mins.keys()))
    if len(common) < 5:
        warn("Insufficient overlap for paired figure")
        return
    gap = [well_mins["ceh36"][yr] - ceh4_mins[yr] for yr in common]
    pre_gap = [g for yr, g in zip(common, gap) if yr < post_year]
    post_gap = [g for yr, g in zip(common, gap) if yr >= post_year]

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), dpi=300, sharex=True)
    ax = axes[0]
    ax.plot(common, [well_mins["ceh36"][yr] for yr in common], "o-", color="#d62728", lw=2, ms=7, label="CEH36 (scraped)")
    ax.plot(common, [ceh4_mins[yr] for yr in common], "s-", color="#ff7f0e", lw=2, ms=7, label="CEH4 (paired control)")
    ax.axvline(post_year - 0.5, color="#DAA520", ls="--", lw=2.5, alpha=0.7, label="Scraping (Apr 2015)")
    ax.axvline(INTERVENTION_DATE.year + 0.5, color="#1b5e20", ls="-.", lw=2.5, alpha=0.8, label="Clearfell (Dec 2017)")
    ax.axvline(SCRAPING_DATE_2.year + 0.5, color="#e7298a", ls="-.", lw=2.5, alpha=0.8, label="Re-scrape (Oct 2023)")
    ax.axhline(-0.61, color="green", ls=":", lw=1.5, alpha=0.4, label="Wet slack threshold (\u22120.61 m)")
    ax.axhline(-0.98, color="brown", ls=":", lw=1.5, alpha=0.4, label="Dry slack threshold (\u22120.98 m)")
    ax.set_ylabel("Summer minimum depth (m)")
    ax.set_title("(a) Annual summer minimum: CEH36 vs CEH4", loc="left", fontweight="bold")
    ax.legend(fontsize=9, ncol=2)
    ax.grid(axis="y", alpha=0.25)
    ax.invert_yaxis()

    ax = axes[1]
    ax.bar(common, gap, color=["#56B4E9" if yr < post_year else "#CC79A7" for yr in common],
           edgecolor="black", lw=0.5, alpha=0.8)
    if pre_gap:
        ax.axhline(np.mean(pre_gap), color="#56B4E9", ls="--", lw=2,
                    label=f"Pre-scraping mean: {np.mean(pre_gap)*1000:+.0f} mm")
    if post_gap:
        ax.axhline(np.mean(post_gap), color="#CC79A7", ls="--", lw=2,
                    label=f"Post-scraping mean: {np.mean(post_gap)*1000:+.0f} mm")
    ax.axvline(post_year - 0.5, color="#DAA520", ls="--", lw=2.5, alpha=0.7)
    ax.axvline(INTERVENTION_DATE.year + 0.5, color="#1b5e20", ls="-.", lw=2.5, alpha=0.8)
    ax.axvline(SCRAPING_DATE_2.year + 0.5, color="#e7298a", ls="-.", lw=2.5, alpha=0.8)
    ax.axhline(0, color="black", lw=0.6, alpha=0.5)
    if len(pre_gap) >= 2 and len(post_gap) >= 2:
        _, p = sp_stats.ttest_ind(post_gap, pre_gap, equal_var=False)
        shift = np.mean(post_gap) - np.mean(pre_gap)
        ax.text(0.98, 0.95, f"BACI shift: {shift*1000:+.0f} mm\np = {format_p_value(p)}",
                transform=ax.transAxes, fontsize=11, fontweight="bold", ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="#DAA520", alpha=0.9))
    ax.set_xlabel("Year")
    ax.set_ylabel("Gap: CEH36 \u2212 CEH4 (m)")
    ax.set_title("(b) Paired BACI gap (summer minimum)", loc="left", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.25)

    fig.suptitle("Summer Minimum Paired BACI \u2014 CEH36 (scraped) vs CEH4 (control)\n"
                 "Newborough Warren, annual Jun\u2013Sep minimum depth",
                 fontsize=13, fontweight="bold", y=0.995)
    plt.tight_layout()
    render_figure(plt.gcf(), OUT_09C_FIG_PAIRED)
    plt.close()
    saved(f"{OUT_09C_FIG_PAIRED.name}")


if __name__ == "__main__":
    main()
