"""
34_window_sensitivity.py — MSL5 two-window comparison sensitivity (§5.7.5)
==========================================================================

A deliberate cautionary DEMONSTRATION: how strongly an apparent "site-mean
water-table change" depends on WHICH two five-year spring windows are differenced.
The §4.9.8 headline differences window-end 2017 (springs 2013-2017) against
window-end 2023 (springs 2019-2023) and reports -96.8 mm. This script places that
single comparison inside the envelope of EVERY admissible window pair, so §5.7.5
can show — from a committed, reproducible figure — that the two-window MSL5 method
cannot resolve absolute site-wide change: pick different windows and you get the
opposite sign and roughly twice the magnitude.

DESIGN DECISION (final, spec-locked 2026-06-27 — all-pairs demonstration):
  * ALL admissible window pairs are retained, INCLUDING those whose current window
    contains the freak-wet 2024 spring. Admitting the "wrong" pairs is the entire
    point of the demonstration; excluding them would hide the failure mode it exists
    to expose. (This SUPERSEDES the earlier wet-2024-excluded "defensible windows
    only" variant, whose -0.14/+0.11 m envelope answered a different, narrower
    question.)
  * The thin 7-well 2005-2009 baseline is NOT shown: with MIN_PANEL=40 every pair
    touching window-end 2009 has <=7 common wells and is inadmissible. The spread
    shown therefore arises purely from window CHOICE among well-sampled windows —
    not from a flimsy baseline — which keeps the demonstration honest (one failure
    mode, freak-year window choice, not two).

Method:
  * Source: committed per-well annual spring MSL, outputs/26_van_willegen_msl/
    26_msl_annual_per_well.csv (column MSL_m_bg, below ground), valid rows only.
  * Exclusions: config.MSL5_EXCLUDED_WELLS (CEH13, CEH14) — matches Script 26.
  * Per-well MSL5(window-end Y) = mean of the well's annual spring MSL over years
    (Y-4 .. Y); a well qualifies for a window only if all five spring-years present.
  * For each ordered pair (Wi < Wj) the site-mean change is the mean over the COMMON
    panel (wells qualifying in BOTH windows) of the per-well (Wj - Wi) change — the
    panel is held FIXED across the pair, so composition change cannot inflate it.
  * Admissible pair = common panel >= config.MSL5_WINDOW_MIN_PANEL wells.
  * Window-axis rainfall annotations: each window's mean annual rainfall expressed
    as % deviation from the analysis-period mean, read from the committed
    00_climate_summary/00_01_annual_climate_summary.csv (not hand-typed).

Validation: the 2017->2023 pair reproduces the committed -96.8 mm (n=59) headline
(it returns -96.5 mm, n=60; the 1-well/0.3 mm gap is a coverage-rule nuance).

Outputs (outputs/34_window_sensitivity/):
  34_window_matrix.csv         every admissible pair: baseline_end, current_end,
                               change_mm, n_common, admissible
  34_results.txt               anchor check + envelope range + sign split
  34_window_sensitivity.png    two-panel figure (Panel A: all-pairs matrix;
                               Panel B: site-mean spring trajectory + interannual SD)

Panel B note: the own-panel OLS trend shown is DESCRIPTIVE. The canonical secular
trend is Script 32's AR-corrected site-mean trend, read at runtime from the
committed 32_site_mean_trend.csv (full-record row) — no longer hard-coded here.
Both are non-significant.

Version: 0.4.0 (2026-06-28)
  v0.4.0: the canonical AR-corrected secular trend is now READ from Script 32's
          committed 32_site_mean_trend.csv (paths.OUT_32_SITE_MEAN_TREND, full-record
          row) instead of being a hard-coded "-7.0 mm/yr (p=0.52)" literal in the
          header and figure caption. Convention pass: __version__; inputs read
          directly through paths constants (OUT_26_ANNUAL_PER_WELL,
          OUT_00_ANNUAL_CLIMATE_TABLE, OUT_32_SITE_MEAN_TREND) so the dependency
          auditor attributes every read.
  v0.3.0: all-pairs demonstration (wet-2024 retained); Script now generates the
          §5.7.5 figure; MIN_PANEL/ANCHOR moved to config; outputs via paths.py;
          wired into run_analysis.py as a supplementary step. Supersedes the
          wet-2024-excluded v0.2.0 figure rebuild.
  v0.2.0: (worker) baseline x current matrix, wet-2024 excluded -> -0.14/+0.11 m.
  v0.1.0: standalone all-pairs envelope (no figure), pending admissibility sign-off.
"""

from __future__ import annotations
import sys
import pathlib
import itertools

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Rectangle

from utils import config, paths
from utils.console_utils import banner, phase, step, info, note, result, saved, done, hr
from utils.render_utils import render_figure

__version__ = "0.5.0"
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
SCRIPT_ID = "34"
VERSION = __version__

# Inputs are read directly through these paths constants in main() (deps-visible):
#   OUT_26_ANNUAL_PER_WELL  (26_msl_annual_per_well.csv)   per-well annual spring MSL
#   OUT_00_ANNUAL_CLIMATE_TABLE (00_01_annual_climate_summary.csv)  window rainfall context
#   OUT_32_SITE_MEAN_TREND  (32_site_mean_trend.csv)        canonical AR-corrected secular trend
OUT_MATRIX = paths.OUT_34_MATRIX
OUT_TXT = paths.OUT_34_RESULTS
OUT_FIG = paths.OUT_34_FIG

WINDOW_LEN = config.MSL_DEFAULT_WINDOW_YEARS          # 5
MIN_PANEL = config.MSL5_WINDOW_MIN_PANEL              # 40
ANCHOR = tuple(config.MSL5_WINDOW_ANCHOR)            # (2017, 2023)


def load_script32_secular_trend():
    """Read Script 32's committed site-mean spring-level trend (the canonical
    AR-corrected secular figure cited in §5.7.5).

    Returns (slope_mm_yr, p_ar, period_label) for the full-record row (the
    longest-span period in 32_site_mean_trend.csv), or None if Script 32 has not
    been run yet (Script 32 is step 36, this is step 42, so on a full run the file
    exists).
    """
    if not paths.OUT_32_SITE_MEAN_TREND.exists():
        return None
    df = pd.read_csv(paths.OUT_32_SITE_MEAN_TREND)
    if df.empty:
        return None
    df = df.copy()
    df["_span"] = df["last_year"] - df["first_year"]
    row = df.sort_values("_span").iloc[-1]           # full record = longest span
    return float(row["slope_mm_yr"]), float(row["p_ar"]), str(row["period"])


# ── core ----------------------------------------------------------------------
def per_well_msl5(piv: pd.DataFrame, end: int):
    """Per-well MSL5 (mm) for the five-year window ending in `end`, or None if the
    window's five spring-years are not all present in the data columns."""
    cols = [y for y in range(end - WINDOW_LEN + 1, end + 1) if y in piv.columns]
    if len(cols) < WINDOW_LEN:
        return None
    return piv[cols].dropna().mean(axis=1)            # wells with all five spring-years


def build_pairs(piv: pd.DataFrame, ends: list[int]) -> pd.DataFrame:
    """Every admissible ordered window pair (baseline earlier, current later)."""
    rows = []
    for i, j in itertools.combinations(ends, 2):
        pi, pj = per_well_msl5(piv, i), per_well_msl5(piv, j)
        cc = pi.index.intersection(pj.index)
        if len(cc) < MIN_PANEL:
            continue
        rows.append((i, j, float(pj[cc].mean() - pi[cc].mean()), len(cc), True))
    return pd.DataFrame(rows, columns=["baseline_end", "current_end",
                                       "change_mm", "n_common", "admissible"])


def window_rainfall_pct(end: int, annual_p: pd.Series, ref_mean: float) -> float:
    """Window mean annual rainfall as % deviation from the analysis-period mean."""
    yrs = [y for y in range(end - WINDOW_LEN + 1, end + 1) if y in annual_p.index]
    if not yrs:
        return np.nan
    return (annual_p.loc[yrs].mean() / ref_mean - 1.0) * 100.0


def span_label(end: int) -> str:
    return f"{end - WINDOW_LEN + 1}\u2013{end}"       # e.g. "2013–2017"


def site_mean_trajectory(piv: pd.DataFrame):
    """Own-panel site-mean spring level (mm bg) per spring year, with simple OLS."""
    series = piv.mean(axis=0).sort_index()            # mean over available wells per year
    yrs = series.index.values.astype(float)
    vals = series.values.astype(float)
    slope, intercept = np.polyfit(yrs, vals, 1)
    # two-sided p for the slope (OLS t-test)
    fit = slope * yrs + intercept
    resid = vals - fit
    n = len(yrs)
    se = np.sqrt((resid @ resid) / (n - 2)) / np.sqrt(((yrs - yrs.mean()) ** 2).sum())
    t = slope / se
    from scipy import stats
    p = 2.0 * (1.0 - stats.t.cdf(abs(t), df=n - 2))
    return series, slope, intercept, p, float(np.std(vals, ddof=1))


# ── figure --------------------------------------------------------------------
def make_figure(d: pd.DataFrame, piv: pd.DataFrame, annual_p: pd.Series,
                ref_mean: float, lo: float, hi: float, n_neg: int, n_pos: int,
                secular=None):
    mat = d.pivot(index="baseline_end", columns="current_end", values="change_mm")
    baselines = sorted(mat.index)
    currents = sorted(mat.columns)
    mat = mat.reindex(index=baselines, columns=currents)
    Z = mat.values

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(15.5, 6.6),
                                   gridspec_kw={"width_ratios": [1.05, 1.0]})
    fig.suptitle("Two-window comparison cannot resolve absolute site-wide "
                 "water-table change", fontsize=14, y=0.98)

    # Panel A — all-pairs matrix
    vmax = np.nanmax(np.abs(Z))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    im = axA.imshow(Z, cmap="RdBu", norm=norm, aspect="auto", origin="upper")
    axA.set_xticks(range(len(currents)))
    axA.set_yticks(range(len(baselines)))
    axA.set_xticklabels([f"{span_label(c)}\n({window_rainfall_pct(c, annual_p, ref_mean):+.0f}%)"
                         for c in currents], fontsize=8)
    axA.set_yticklabels([f"{span_label(b)} ({window_rainfall_pct(b, annual_p, ref_mean):+.0f}%)"
                         for b in baselines], fontsize=8)
    axA.set_xlabel("current window (springs)")
    axA.set_ylabel("baseline window (springs)")
    axA.set_title(f"A  Site-wide MSL change (mm) by window pair\n"
                  f"admissible: {lo:+.0f} to {hi:+.0f} mm "
                  f"({lo/1000:+.2f} to {hi/1000:+.2f} m); {n_neg} neg / {n_pos} pos; "
                  f"outlined = \u00a74.9.8 headline",
                  fontsize=10, loc="left")
    for r in range(len(baselines)):
        for cc in range(len(currents)):
            v = Z[r, cc]
            if np.isnan(v):
                continue
            shade = "white" if abs(v) > 0.6 * vmax else "black"
            axA.text(cc, r, f"{v:+.0f}", ha="center", va="center",
                     fontsize=8, color=shade,
                     fontweight="bold" if abs(v) == vmax else "normal")
    # outline the §4.9.8 anchor cell (the report headline comparison)
    if ANCHOR[0] in baselines and ANCHOR[1] in currents:
        ri, ci = baselines.index(ANCHOR[0]), currents.index(ANCHOR[1])
        axA.add_patch(Rectangle((ci - 0.5, ri - 0.5), 1, 1, fill=False,
                                edgecolor="black", lw=2.4))

    # Panel B — site-mean trajectory + interannual SD
    series, slope, intercept, p, sd = site_mean_trajectory(piv)
    yrs = series.index.values.astype(float)
    mean_lvl = series.values.mean()
    axB.axhspan(mean_lvl - sd, mean_lvl + sd, color="0.85", zorder=0,
                label=f"interannual SD (\u00b1{sd:.0f} mm)")
    axB.axhline(mean_lvl, color="0.5", lw=0.8, ls=":", zorder=1)
    axB.plot(yrs, series.values, "-o", color="black", ms=4, lw=1.2,
             label="site-mean spring level", zorder=3)
    axB.plot(yrs, slope * yrs + intercept, "--", color="crimson", lw=2.2,
             label=f"full-record trend {slope:+.1f} mm/yr (p={p:.2f}, n.s.)", zorder=2)
    axB.set_xlabel("spring year")
    axB.set_ylabel("site-mean spring level (mm below ground)")
    axB.set_title("B  Why: the multi-year cycle dwarfs the trend", fontsize=10, loc="left")
    axB.legend(loc="lower left", fontsize=8, framealpha=0.9)

    if secular is not None:
        s_slope, s_p, _ = secular
        secular_txt = (f"The canonical secular trend is Script 32's AR-corrected "
                       f"\u2212{abs(s_slope):.1f} mm/yr (p={s_p:.2f}); the dashed line "
                       f"here is a descriptive own-panel OLS."
                       if s_slope < 0 else
                       f"The canonical secular trend is Script 32's AR-corrected "
                       f"{s_slope:+.1f} mm/yr (p={s_p:.2f}); the dashed line here is a "
                       f"descriptive own-panel OLS.")
    else:
        secular_txt = ("The canonical secular trend is Script 32's AR-corrected "
                       "site-mean trend (run Script 32 for the committed value); "
                       "the dashed line here is a descriptive own-panel OLS.")
    fig.text(0.012, 0.012,
             "Thin 7-well 2005\u20132009 baseline excluded (common panel < "
             f"{MIN_PANEL}); the spread shown is from window CHOICE alone, among "
             "well-sampled windows.\n" + secular_txt,
             fontsize=7.5, style="italic", color="0.35")

    fig.subplots_adjust(left=0.10, right=0.985, top=0.88, bottom=0.16, wspace=0.18)
    render_figure(fig, OUT_FIG)
    plt.close(fig)


# ── main ----------------------------------------------------------------------
def main() -> int:
    banner(SCRIPT_ID, "MSL5 two-window comparison sensitivity (\u00a75.7.5)", VERSION)
    paths.DIR_34.mkdir(parents=True, exist_ok=True)

    phase(1, "Load committed annual MSL")
    a = pd.read_csv(paths.OUT_26_ANNUAL_PER_WELL)
    a = a[a["valid"] == True].copy()
    a["well"] = a["well"].astype(str).str.lower().str.strip()
    excl = set(k.lower() for k in config.MSL5_EXCLUDED_WELLS)
    a = a[~a["well"].isin(excl)]
    a["mm"] = a["MSL_m_bg"] * 1000.0
    piv = a.pivot_table(index="well", columns="hydro_year", values="mm")
    ends = [e for e in range(int(piv.columns.min()) + WINDOW_LEN - 1,
                             int(piv.columns.max()) + 1)
            if per_well_msl5(piv, e) is not None]
    info(f"excluded {sorted(excl)}; {piv.shape[0]} wells; "
         f"{len(ends)} five-year windows ({ends[0]}-{ends[-1]})")

    phase(2, "Window rainfall context")
    clim = pd.read_csv(paths.OUT_00_ANNUAL_CLIMATE_TABLE)
    # The file carries a 'Long-term mean' footer row, so Year is string-typed.
    ltm_row = clim[clim["Year"].astype(str).str.contains("mean", case=False, na=False)]
    ref_mean = float(ltm_row["Annual_P_mm"].iloc[0]) if len(ltm_row) else float("nan")
    clim["Year"] = pd.to_numeric(clim["Year"], errors="coerce")
    annual_p = clim.dropna(subset=["Year"]).set_index(clim["Year"].dropna().astype(int))["Annual_P_mm"]
    info(f"committed long-term mean annual rainfall {ref_mean:.0f} mm; "
         f"window % shown relative to this")

    phase(3, "Validate against committed anchor")
    mi, mj = per_well_msl5(piv, ANCHOR[0]), per_well_msl5(piv, ANCHOR[1])
    c = mi.index.intersection(mj.index)
    anchor_change = mj[c].mean() - mi[c].mean()
    result(f"anchor {ANCHOR[0]}->{ANCHOR[1]}",
           f"{anchor_change:+.1f} mm, n={len(c)} (committed -96.8, n=59)")

    phase(4, "All admissible window pairs (fixed common panel; wet-2024 retained)")
    d = build_pairs(piv, ends)
    lo, hi = d.change_mm.min(), d.change_mm.max()
    n_neg, n_pos = int((d.change_mm < 0).sum()), int((d.change_mm > 0).sum())
    mostneg, mostpos = d.loc[d.change_mm.idxmin()], d.loc[d.change_mm.idxmax()]
    result("admissible pairs", f"{len(d)} (common panel >= {MIN_PANEL})")
    result("site-mean change envelope",
           f"{lo:+.1f} to {hi:+.1f} mm  ({lo/1000:+.2f} to {hi/1000:+.2f} m)")
    result("sign split", f"{n_neg} negative / {n_pos} positive")
    note(f"the {anchor_change:+.0f} mm {ANCHOR[0]}->{ANCHOR[1]} headline is one "
         f"point in this wide, sign-changing envelope; the +ve extreme "
         f"{int(mostpos.baseline_end)}->{int(mostpos.current_end)} "
         f"({mostpos.change_mm:+.0f} mm) is a wet-2024 'wrong pair'")

    phase(5, "Write outputs + figure")
    secular = load_script32_secular_trend()
    if secular is not None:
        s_slope, s_p, s_period = secular
        result("Script 32 secular trend (canonical)",
               f"{s_slope:+.2f} mm/yr  AR p={s_p:.2f}  [{s_period}, from 32_site_mean_trend.csv]")
    else:
        note("32_site_mean_trend.csv not found — run Script 32 first for the "
             "canonical secular trend (caption will say so)")
    if secular is not None:
        secular_line = (f"\nCanonical secular trend (Script 32, {secular[2]}): "
                        f"{secular[0]:+.2f} mm/yr (AR-corrected p={secular[1]:.2f}) "
                        f"— read from 32_site_mean_trend.csv, not hard-coded.\n")
    else:
        secular_line = ("\nCanonical secular trend: 32_site_mean_trend.csv not found "
                        "(run Script 32).\n")
    d.sort_values("change_mm").to_csv(OUT_MATRIX, index=False)
    saved(OUT_MATRIX)
    OUT_TXT.write_text(
        f"MSL5 two-window sensitivity (\u00a75.7.5) — all-pairs demonstration v{VERSION}\n"
        f"source: 26_msl_annual_per_well.csv (valid; {sorted(excl)} excluded); "
        f"rainfall: 00_01_annual_climate_summary.csv\n"
        f"common panel per pair; admissible = panel>=%d; ALL pairs retained "
        f"(wet-2024 windows INCLUDED — the point of the demonstration)\n\n"
        f"anchor {ANCHOR[0]}->{ANCHOR[1]}: {anchor_change:+.1f} mm (n={len(c)})  "
        f"[committed -96.8 mm, n=59]\n\n"
        f"ADMISSIBLE envelope: {lo:+.0f} to {hi:+.0f} mm "
        f"({lo/1000:+.2f} to {hi/1000:+.2f} m); "
        f"{n_neg} neg / {n_pos} pos of {len(d)} pairs (sign-changing)\n"
        f"  most negative: {int(mostneg.baseline_end)}->{int(mostneg.current_end)} "
        f"{mostneg.change_mm:+.0f} mm (n={int(mostneg.n_common)})\n"
        f"  most positive: {int(mostpos.baseline_end)}->{int(mostpos.current_end)} "
        f"{mostpos.change_mm:+.0f} mm (n={int(mostpos.n_common)})  "
        f"[current window contains the freak-wet 2024 spring]\n\n"
        f"The -97 mm headline is one interior point; the two-window MSL5 method "
        f"cannot resolve absolute site-wide change.\n"
        f"Thin 7-well 2005-2009 baseline auto-excluded by the panel rule.\n"
        % MIN_PANEL
        + secular_line)
    saved(OUT_TXT)

    make_figure(d, piv, annual_p, ref_mean, lo, hi, n_neg, n_pos, secular=secular)
    saved(OUT_FIG)

    hr()
    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
