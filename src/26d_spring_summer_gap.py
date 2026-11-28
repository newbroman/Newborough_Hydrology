"""
26d_spring_summer_gap.py — spring level against summer minimum since 2010
==========================================================================

The question (Martin, 2026-11-27): "perhaps i was too keen to throw out summer minima ... there did seem to be a
widening gap between msl and summer minima. Perhaps we need to do the summer minima with the wells that have full
summer records, against msl"; then "let's include the numbers, add a pipeline step". D-347 (4) made the spring level
the long-term measure in Paper 1 and the summer-minimum trend a sentence; this step supplies that sentence's numbers.

Method:
  * Source: Script 26's per-well annual table (26_msl_annual_per_well.csv). The spring level is MSL_m_bg on rows
    Script 26 marks valid (every MSL_SPRING_MONTHS month); the summer minimum is the lowest monthly level of the
    SUMMER_MINIMUM_MONTHS of the same year, admitted only with every one of them present: the summer that follows that
    spring. (Script 26's own MIN_m_bg spans its May-to-April year, so the latest summer would wait for April.) The gap is spring minus summer minimum, in m. Levels are below ground
    (negative down), as Script 26 writes them.
  * Window: hydrological years from config.RECORD_FIT_START (D-347) to the last year with a summer.
  * Panel: a well enters when both quantities are valid in at least config.SPRING_SUMMER_GAP_MIN_YEARS years.
  * Per well: OLS slopes of spring, summer minimum and gap on year (mm/yr) with p; Theil-Sen slope of the gap.
  * Groups (D-348): cluster-level wells (In_Cluster_Level) by group, C1, C2, C3o, C4, C3f; the network uses every
    panel well. Median slope over wells; the count whose gap widens; a two-sided sign test on that count.
  * Robustness, with years chosen from the data, not typed: without the year of the lowest network-median spring;
    without that year and the year of the highest; from three years after the window opens.
  * Dry summers (sensitivity): a summer month with no reading because the well was dry (01_dry_depths.csv) enters
    as its bound, level = -dry depth, and the summer minimum is recomputed from the monthly levels. That admits
    years the main panel drops, the driest summers among them.
  * Long record (D-347 (5): 2005-09 is kept where it is the subject): wells read from
    config.SPRING_SUMMER_GAP_LONG_START with at least SPRING_SUMMER_GAP_LONG_MIN_YEARS valid years, the first by 2007.
    The 2005-25 slopes, and the change in the mean of each quantity from 2005-09 to the D-347 window, which
    separates the 2009 step from a trend.

Outputs (outputs/26d_spring_summer_gap/):
  26d_per_well.csv, 26d_group_summary.csv, 26d_by_year.csv, 26d_robustness.csv, 26d_long_record.csv,
  26d_report_numbers.csv, 26d_results.txt, 26d_spring_summer_gap.png
"""
from __future__ import annotations

__version__ = "1.1.0"  # 2026-11-28 (Martin: "shouldnt it be the post 2010 record?"): the robustness tests (all years; without the lowest spring; without the lowest and highest; from y0+3) for every group on its cluster-level wells, and counts of falling and significantly falling wells; network rows and keys unchanged. Was "1.0.0"  # 2026-11-27 (D-347 (4) Note; Martin 2026-11-27 "include the numbers, add a pipeline step"). First issue.
SCRIPT_ID = "26d"
VERSION = __version__

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import config, paths
from utils.cluster_series import in_cluster_level
from utils.console_utils import banner, phase, info, note, result, saved, done, hr
from utils.render_utils import render_figure
from utils.report_numbers_utils import ReportNumbers

# Inputs are read through these paths constants in main() (deps-visible):
#   OUT_26_ANNUAL_PER_WELL (26_msl_annual_per_well.csv)  per-well annual spring level and summer minimum
#   INT_CLUSTER_STATS      (02_cluster_stats.csv)        groups and cluster-level wells (D-348)
#   INT_WELLS_CLEAN        (01_wells_clean.csv)          monthly levels, for the dry-summer sensitivity
#   INT_DRY_DEPTHS         (01_dry_depths.csv)           the months a well was dry, and its depth

QUANTITIES = ("spring", "summer_min", "gap")


def _slope(years, values):
    """OLS slope in mm/yr and its p; NaN when fewer than three points."""
    if len(years) < 3:
        return np.nan, np.nan
    t = stats.linregress(years, values)
    return t.slope * 1000.0, t.pvalue


def _sign_p(k: int, n: int) -> float:
    return float(stats.binomtest(int(k), int(n)).pvalue) if n else np.nan


def per_well_slopes(annual: pd.DataFrame, years: list[int], min_years: int) -> pd.DataFrame:
    """One row per well with at least min_years valid years among `years`."""
    rows = []
    a = annual[annual["hydro_year"].isin(years)]
    for well, g in a.groupby("well"):
        g = g.sort_values("hydro_year")
        if len(g) < min_years:
            continue
        y = g["hydro_year"].to_numpy(float)
        r = {"well": well, "n_years": len(g), "first_year": int(y.min()), "last_year": int(y.max())}
        for q in QUANTITIES:
            r[f"{q}_mm_yr"], r[f"{q}_p"] = _slope(y, g[q].to_numpy(float))
        r["gap_theil_sen_mm_yr"] = float(stats.theilslopes(g["gap"].to_numpy(float), y)[0]) * 1000.0
        r["gap_mean_m"] = float(g["gap"].mean())
        rows.append(r)
    return pd.DataFrame(rows)


def summarise(w: pd.DataFrame, label: str) -> dict:
    n = len(w)
    k = int((w["gap_mm_yr"] > 0).sum())
    return {"group": label, "n_wells": n,
            "spring_median_mm_yr": float(w["spring_mm_yr"].median()) if n else np.nan,
            "summer_min_median_mm_yr": float(w["summer_min_mm_yr"].median()) if n else np.nan,
            "gap_median_mm_yr": float(w["gap_mm_yr"].median()) if n else np.nan,
            "gap_theil_sen_median_mm_yr": float(w["gap_theil_sen_mm_yr"].median()) if n else np.nan,
            "n_gap_widening": k, "n_gap_widening_p05": int(((w["gap_mm_yr"] > 0) & (w["gap_p"] < 0.05)).sum()),
            "sign_test_p": _sign_p(k, n),
            "gap_mean_median_m": float(w["gap_mean_m"].median()) if n else np.nan,
            # 1.1.0 (Martin 2026-11-28): how many wells fall, and how many of those falls are significant
            "n_spring_falling": int((w["spring_mm_yr"] < 0).sum()) if n else 0,
            "n_spring_falling_p05": int(((w["spring_mm_yr"] < 0) & (w["spring_p"] < 0.05)).sum()) if n else 0,
            "n_summer_min_falling": int((w["summer_min_mm_yr"] < 0).sum()) if n else 0,
            "n_summer_min_falling_p05": int(((w["summer_min_mm_yr"] < 0) & (w["summer_min_p"] < 0.05)).sum()) if n else 0}


def summer_minima(fill_dry: bool) -> tuple[pd.DataFrame, int]:
    """The summer minimum of each well and year: the lowest of the config.SUMMER_MINIMUM_MONTHS monthly levels of that
    year, admitted only when every one of those months has a value. The months are the bucketed labels Script 26 and
    every other script use (D-207), so the summer of year y follows the spring Script 26 assigns to year y.
    fill_dry: a month with no reading because the well was dry (01_dry_depths.csv) enters as its bound, -dry depth."""
    lv = pd.read_csv(paths.INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    lv.columns = [str(c).lower().strip() for c in lv.columns]
    n_filled = 0
    if fill_dry:
        dry = pd.read_csv(paths.INT_DRY_DEPTHS, parse_dates=["month"])
        dry["well"] = dry["well"].astype(str).str.lower().str.strip()
        for r in dry.itertuples(index=False):
            if r.well in lv.columns and r.month in lv.index and pd.isna(lv.at[r.month, r.well]):
                lv.at[r.month, r.well] = -float(r.dry_depth_m)
                n_filled += 1
    months = list(config.SUMMER_MINIMUM_MONTHS)
    summer = lv[lv.index.month.isin(months)]
    rows = []
    for y, block in summer.groupby(summer.index.year):
        complete = block.notna().sum() == len(months)
        mins = block.min()
        rows += [(well, int(y), float(mins[well])) for well in complete.index[complete]]
    return pd.DataFrame(rows, columns=["well", "hydro_year", "summer_min"]), n_filled


def main() -> int:
    banner(SCRIPT_ID, "Spring level against summer minimum since 2010 (D-347 (4))", VERSION)
    paths.DIR_26D.mkdir(parents=True, exist_ok=True)
    rpt = ReportNumbers()
    lines = [f"Script 26d v{VERSION}: spring level against summer minimum (D-347 (4) Note)", ""]

    phase(1, "Load Script 26's annual table and the groups")
    raw = pd.read_csv(paths.OUT_26_ANNUAL_PER_WELL)
    raw["well"] = raw["well"].astype(str).str.lower().str.strip()
    truthy = lambda s: s.astype(str).str.lower().isin({"true", "1", "1.0"})
    spring = raw[truthy(raw["valid"])][["well", "hydro_year", "MSL_m_bg"]].rename(columns={"MSL_m_bg": "spring"})
    # The summer minimum is read from the monthly levels, not from Script 26's MIN_m_bg: Script 26's minimum spans its
    # May-to-April year, so the latest summer cannot enter until that year closes. "hydro_year" is the spring's year.
    summer, _ = summer_minima(fill_dry=False)
    annual = spring.merge(summer, on=["well", "hydro_year"], how="inner")
    annual["gap"] = annual["spring"] - annual["summer_min"]
    y0 = int(pd.Timestamp(config.RECORD_FIT_START).year)
    y1 = int(min(summer["hydro_year"].max(), spring["hydro_year"].max()))
    years = list(range(y0, y1 + 1))
    cs = pd.read_csv(paths.INT_CLUSTER_STATS)
    cs["well"] = cs["Name_Original"].astype(str).str.lower().str.strip()
    cs["cluster_level"] = in_cluster_level(cs).to_numpy()
    group = dict(zip(cs["well"], pd.to_numeric(cs["Cluster"], errors="coerce")))
    level = dict(zip(cs["well"], cs["cluster_level"]))
    info(f"window {y0}-{y1} ({len(years)} years); panel rule: both valid in >= {config.SPRING_SUMMER_GAP_MIN_YEARS}")

    phase(2, "Per-well slopes and group summaries")
    w = per_well_slopes(annual, years, config.SPRING_SUMMER_GAP_MIN_YEARS)
    w["group_id"] = w["well"].map(group)
    w["cluster_level"] = w["well"].map(level).fillna(False).astype(bool)
    w["group"] = w["group_id"].map(lambda g: config.CLUSTER_SHORT.get(int(g), "") if pd.notna(g) else "")
    w.sort_values(["group_id", "well"]).to_csv(paths.OUT_26D_PER_WELL, index=False)
    saved(paths.OUT_26D_PER_WELL)
    summ = [summarise(w, "network")]
    for gid in sorted(config.CLUSTER_SHORT):
        summ.append(summarise(w[(w["group_id"] == gid) & w["cluster_level"]], config.CLUSTER_SHORT[gid]))
    S = pd.DataFrame(summ)
    S.to_csv(paths.OUT_26D_GROUP_SUMMARY, index=False)
    saved(paths.OUT_26D_GROUP_SUMMARY)
    net = S.iloc[0]
    result("network", f"{int(net.n_wells)} wells: spring {net.spring_median_mm_yr:+.1f}, summer minimum "
           f"{net.summer_min_median_mm_yr:+.1f}, gap {net.gap_median_mm_yr:+.1f} mm/yr; widening at "
           f"{int(net.n_gap_widening)} (sign p = {net.sign_test_p:.2g})")
    for r in S.itertuples(index=False):
        tag = r.group
        rpt.add(f"gap_n_wells · {tag}", r.n_wells, unit="wells",
                note=f"{tag}: wells with spring level and summer minimum both valid in >= {config.SPRING_SUMMER_GAP_MIN_YEARS} "
                     f"of the {len(years)} years {y0}-{y1}" + ("" if tag == "network" else ", cluster-level wells (D-348)"))
        for col, unit, what in (("spring_median_mm_yr", "mm/yr", "median per-well OLS slope of the spring level"),
                                ("summer_min_median_mm_yr", "mm/yr", "median per-well OLS slope of the summer minimum"),
                                ("gap_median_mm_yr", "mm/yr", "median per-well OLS slope of the gap (spring minus summer minimum)"),
                                ("gap_theil_sen_median_mm_yr", "mm/yr", "median per-well Theil-Sen slope of the gap"),
                                ("n_gap_widening", "wells", "wells whose gap slope is positive"),
                                ("n_gap_widening_p05", "wells", "wells whose gap slope is positive with p < 0.05"),
                                ("sign_test_p", "", "two-sided sign test on the count of widening gaps"),
                                ("gap_mean_median_m", "m", "median over wells of the mean gap")):
            rpt.add(f"gap_{col} · {tag}", getattr(r, col), unit=unit, note=f"{tag}, {y0}-{y1}: {what}")
    lines.append(f"Window {y0}-{y1}; panel: both valid in >= {config.SPRING_SUMMER_GAP_MIN_YEARS} years.")
    lines.append(S.round(4).to_string(index=False))

    phase(3, "Year by year (network panel)")
    a = annual[annual["well"].isin(w["well"]) & annual["hydro_year"].isin(years)]
    by = (a.groupby("hydro_year").agg(n_wells=("well", "size"), spring_median_m=("spring", "median"),
                                      summer_min_median_m=("summer_min", "median"), gap_median_m=("gap", "median"))
          .reset_index())
    by.to_csv(paths.OUT_26D_BY_YEAR, index=False)
    saved(paths.OUT_26D_BY_YEAR)
    lo_year = int(by.loc[by["spring_median_m"].idxmin(), "hydro_year"])
    hi_year = int(by.loc[by["spring_median_m"].idxmax(), "hydro_year"])
    smin_range = (float(by["summer_min_median_m"].min()), float(by["summer_min_median_m"].max()))
    spring_range = (float(by["spring_median_m"].min()), float(by["spring_median_m"].max()))
    r_gap_spring = float(stats.pearsonr(by["spring_median_m"], by["gap_median_m"])[0])
    result("lowest / highest network spring", f"{lo_year} / {hi_year}")
    result("summer-minimum median range", f"{smin_range[0]:.2f} to {smin_range[1]:.2f} m; spring {spring_range[0]:.2f} to {spring_range[1]:.2f} m")
    rpt.add("gap_lowest_spring_year", lo_year, unit="year", note="hydrological year of the lowest network-median spring level (26d_by_year.csv)")
    rpt.add("gap_highest_spring_year", hi_year, unit="year", note="hydrological year of the highest network-median spring level")
    rpt.add("gap_summer_min_median_lo_m", smin_range[0], note="lowest annual network-median summer minimum, m below ground (negative down)")
    rpt.add("gap_summer_min_median_hi_m", smin_range[1], note="highest annual network-median summer minimum")
    rpt.add("gap_spring_median_lo_m", spring_range[0], note="lowest annual network-median spring level")
    rpt.add("gap_spring_median_hi_m", spring_range[1], note="highest annual network-median spring level")
    rpt.add("gap_lowest_spring_year_gap_m", float(by.loc[by["hydro_year"] == lo_year, "gap_median_m"].iloc[0]),
            note="network-median gap in the year of the lowest spring")
    rpt.add("gap_vs_spring_r_by_year", r_gap_spring, unit="",
            note="Pearson r, annual network-median gap against annual network-median spring level")
    lines += ["", f"Year by year: lowest spring {lo_year}, highest {hi_year}; r(gap, spring) = {r_gap_spring:.2f}",
              by.round(3).to_string(index=False)]

    phase(4, "Robustness: the years that carry the trend")
    tests = [("all years", years),
             (f"without {lo_year}", [y for y in years if y != lo_year]),
             (f"without {lo_year} and {hi_year}", [y for y in years if y not in (lo_year, hi_year)]),
             (f"from {y0 + 3}", [y for y in years if y >= y0 + 3])]
    # 1.1.0 (Martin 2026-11-28, "shouldnt it be the post 2010 record?"): the same tests for every group, on its
    # cluster-level wells, so Table 7 can carry them; the network rows and their keys are unchanged.
    keys = ("all", "without_lowest", "without_lowest_highest", "from_plus3")
    panels = [("network", set(w["well"]))] + [
        (config.CLUSTER_SHORT[gid], set(w.loc[(w["group_id"] == gid) & w["cluster_level"], "well"]))
        for gid in sorted(config.CLUSTER_SHORT)]
    rob = []
    for tag, wells in panels:
        for key, (label, ys) in zip(keys, tests):
            ww = per_well_slopes(annual[annual["well"].isin(wells)], ys, 3)
            s = summarise(ww, tag); s["key"] = key; s["test"] = label; s["years"] = f"{min(ys)}-{max(ys)} ({len(ys)})"
            rob.append(s)
    R = pd.DataFrame(rob)[["group", "key", "test", "years", "n_wells", "spring_median_mm_yr", "summer_min_median_mm_yr",
                          "gap_median_mm_yr", "n_gap_widening", "sign_test_p", "n_spring_falling", "n_spring_falling_p05",
                          "n_summer_min_falling", "n_summer_min_falling_p05"]]
    R.to_csv(paths.OUT_26D_ROBUSTNESS, index=False)
    saved(paths.OUT_26D_ROBUSTNESS)
    for r in R.itertuples(index=False):
        sfx = "" if r.group == "network" else f" · {r.group}"
        if r.group == "network":
            result(r.test, f"gap {r.gap_median_mm_yr:+.1f} mm/yr; widening {int(r.n_gap_widening)}/{int(r.n_wells)} "
                           f"(p = {r.sign_test_p:.2g}); summer minimum {r.summer_min_median_mm_yr:+.1f}, falling at "
                           f"{int(r.n_summer_min_falling)} ({int(r.n_summer_min_falling_p05)} with p < 0.05)")
        for col, unit in (("spring_median_mm_yr", "mm/yr"), ("summer_min_median_mm_yr", "mm/yr"),
                          ("gap_median_mm_yr", "mm/yr"), ("n_gap_widening", "wells"), ("n_wells", "wells"), ("sign_test_p", ""),
                          ("n_spring_falling", "wells"), ("n_spring_falling_p05", "wells"),
                          ("n_summer_min_falling", "wells"), ("n_summer_min_falling_p05", "wells")):
            rpt.add(f"gap_robust_{r.key}_{col}{sfx}", getattr(r, col), unit=unit,
                    note=f"{r.group} panel{'' if r.group == 'network' else ' (cluster-level wells)'}, {r.test} ({r.years}): {col}")
    lines += ["", "Robustness (network and group panels, per-well OLS):", R.round(4).to_string(index=False)]

    phase(5, "Dry summers as bounds (sensitivity)")
    sdry, n_filled = summer_minima(fill_dry=True)
    db = spring.merge(sdry, on=["well", "hydro_year"], how="inner")
    db["gap"] = db["spring"] - db["summer_min"]
    wd = per_well_slopes(db, years, config.SPRING_SUMMER_GAP_MIN_YEARS)
    sd = summarise(wd, "network")
    n_dry_wells = int(pd.read_csv(paths.INT_DRY_DEPTHS).assign(m=lambda d: pd.to_datetime(d["month"]))
                      .query("m.dt.year >= @y0 and m.dt.month in @config.SUMMER_MINIMUM_MONTHS", engine="python")["well"].nunique())
    result("dry as bound", f"{sd['n_wells']} wells: gap {sd['gap_median_mm_yr']:+.1f} mm/yr; widening {sd['n_gap_widening']}/{sd['n_wells']}")
    rpt.add("gap_drybound_n_wells", sd["n_wells"], unit="wells", note="panel with each dry summer month entered as its bound (-dry depth)")
    rpt.add("gap_drybound_gap_median_mm_yr", sd["gap_median_mm_yr"], unit="mm/yr", note="median per-well gap slope, dry months as bounds")
    rpt.add("gap_drybound_n_gap_widening", sd["n_gap_widening"], unit="wells", note="wells whose gap widens, dry months as bounds")
    rpt.add("gap_n_wells_dry_summer", n_dry_wells, unit="wells", note=f"wells with a dry summer month from {y0} (01_dry_depths.csv)")
    lines += ["", f"Dry summers as bounds: {n_filled} dry months filled; {n_dry_wells} wells with a dry summer month from {y0}; "
              f"{sd['n_wells']} wells, gap {sd['gap_median_mm_yr']:+.1f} mm/yr, widening {sd['n_gap_widening']}/{sd['n_wells']}"]

    phase(6, "Long record: the 2009 step against a trend")
    ly = list(range(config.SPRING_SUMMER_GAP_LONG_START, y1 + 1))
    lw = per_well_slopes(annual, ly, config.SPRING_SUMMER_GAP_LONG_MIN_YEARS)
    lw = lw[lw["first_year"] <= config.SPRING_SUMMER_GAP_LONG_START + 2]
    la = annual[annual["well"].isin(lw["well"])]
    pre = la[la["hydro_year"] < y0].groupby("well")[list(QUANTITIES)].mean()
    post = la[la["hydro_year"] >= y0].groupby("well")[list(QUANTITIES)].mean()
    step = (post - pre).dropna()
    L = pd.DataFrame([{"n_wells": len(lw),
                       **{f"{q}_median_mm_yr": float(lw[f"{q}_mm_yr"].median()) for q in QUANTITIES},
                       "n_gap_widening": int((lw["gap_mm_yr"] > 0).sum()),
                       "sign_test_p": _sign_p(int((lw["gap_mm_yr"] > 0).sum()), len(lw)),
                       **{f"{q}_step_median_m": float(step[q].median()) for q in QUANTITIES},
                       "n_step_wells": len(step)}])
    L.to_csv(paths.OUT_26D_LONG_RECORD, index=False)
    saved(paths.OUT_26D_LONG_RECORD)
    l = L.iloc[0]
    result("long record", f"{int(l.n_wells)} wells {ly[0]}-{y1}: summer minimum {l.summer_min_median_mm_yr:+.1f} mm/yr; "
           f"step {y0}-{y1} minus {ly[0]}-{y0 - 1}: spring {l.spring_step_median_m:+.2f}, summer minimum "
           f"{l.summer_min_step_median_m:+.2f}, gap {l.gap_step_median_m:+.2f} m")
    for col in L.columns:
        unit = "wells" if col.startswith("n_") else ("m" if col.endswith("_m") else ("mm/yr" if col.endswith("mm_yr") else ""))
        rpt.add(f"gap_long_{col}", float(l[col]), unit=unit,
                note=f"wells read from {ly[0]} (>= {config.SPRING_SUMMER_GAP_LONG_MIN_YEARS} valid years, first by "
                     f"{config.SPRING_SUMMER_GAP_LONG_START + 2}), {ly[0]}-{y1}; *_step_*: mean {y0}-{y1} minus mean {ly[0]}-{y0 - 1}")
    lines += ["", "Long record:", L.round(4).to_string(index=False)]

    phase(7, "Figure and report numbers")
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.fill_between(by["hydro_year"], by["summer_min_median_m"], by["spring_median_m"], color="0.85", label="gap")
    ax.plot(by["hydro_year"], by["spring_median_m"], "o-", color="tab:blue", label="spring level (MSL)")
    ax.plot(by["hydro_year"], by["summer_min_median_m"], "s-", color="tab:red", label="summer minimum that followed")
    ax.set_xlabel("year of the spring"); ax.set_ylabel("network median, m relative to ground")
    ax.set_title(f"Spring level and summer minimum, {len(w)} wells, {y0}-{y1}", fontsize=10)
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=False); ax.grid(alpha=0.3)
    render_figure(fig, paths.OUT_26D_FIG)
    plt.close(fig)
    saved(paths.OUT_26D_FIG)
    rpt.save(paths.OUT_26D_REPORT_NUMBERS)
    saved(paths.OUT_26D_REPORT_NUMBERS)
    paths.OUT_26D_RESULTS.write_text("\n".join(lines) + "\n")
    saved(paths.OUT_26D_RESULTS)
    note("context, not a test of a threshold: the summer minimum is reported beside the spring level (D-347 (4))")
    hr()
    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
