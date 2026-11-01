"""
14b_year_of_crossing.py — how many wells are below each Curreli et al. (2013) summer level now, and how many would be
by a horizon year on their own summer-minimum trends (D-294).

Until 2.0.0 this script bootstrapped the year at which each CLUSTER's summer-minimum trend crossed SD15b and SD16.
The clusters are Ward's groups on SSM coefficient behaviour, not on water-table depth, so a cluster series averages
wells at every topographic position and a community level cannot be set against it (D-294, Martin 2026-11-01). The
question is now asked of each well:

1. Each reference well's own annual summer minimum (Script 14 1.12.0, 14_per_well_extremes.csv: the cluster series'
   months, hydrological year and month count).
2. Wells with at least config.CROSSING_MIN_YEARS years get an OLS trend, depth = a + b·year.
3. "Now" is the trend's value at the well's last year of record; the horizon is config.CROSSING_HORIZON_YEAR. At the
   horizon the config.CROSSING_CI confidence interval of the fitted mean is computed (t, n − 2).
4. Each well is banded against SD15b and SD16 (utils.community_bands) now and at the horizon, and at the horizon is
   also classed against SD16 as below (the whole interval below the level), above (the whole interval above) or
   unresolved (the interval spans it).
5. Counts by cluster and for all wells go to 14b_report_numbers.csv; the per-well table and the counts to CSVs; one
   figure shows every well, now and at the horizon, against the two levels.

Limitations (stated with the result): a straight line is a description of the record, not a forecast; extrapolating
it past the record assumes the recent climate's direction continues, and the interval covers the sampling
uncertainty of the line, not that assumption. Reads only Script 14 output.
"""

from __future__ import annotations

__version__ = "2.0.0"  # Hollingham (2026) - 2026-11-01 (D-294; Martin 2026-11-01 "redo the year of crossing analysis but
#   with a per well count"). Per-well trends and counts replace the per-cluster bootstrap crossing year. Writes
#   14b_per_well_trends.csv, 14b_crossing_counts.csv, 14b_per_well_crossing.png and 14b_report_numbers.csv. The old
#   14b_year_of_crossing.csv, 14b_year_of_crossing.png and
#   14b_year_of_crossing_results.md are no longer written; they stay committed until the documents that
#   cite them are rewritten (D-294 document batch), then retire.
# 1.2.1  # Hollingham (2026) - 2026-09-28. Text only: the crossing-year conclusion is now §7 Conclusion 13 (was 11).

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from utils.console_utils import banner, phase, step, info, saved, warn, done   # noqa: E402
from utils import paths                                                         # noqa: E402
from utils.config import (                                                      # noqa: E402
    CLUSTER_LABELS, CLUSTER_COLOURS, CROSSING_MIN_YEARS, CROSSING_HORIZON_YEAR, CROSSING_CI,
)
from utils.community_bands import CURRELI_SUMMER, band, band_names, band_counts   # noqa: E402
from utils.render_utils import render_figure                                      # noqa: E402
from utils.report_numbers_utils import ReportNumbers                              # noqa: E402

CLUSTERS = [f"C{k}" for k in sorted(CLUSTER_LABELS)]
SD16_NAME, SD16_LEVEL = CURRELI_SUMMER[-1]


def well_trend(g: pd.DataFrame) -> dict | None:
    """OLS of the annual summer minimum on year; the fitted value now and at the horizon, with the interval there."""
    g = g.dropna(subset=["summer_min_m"]).sort_values("hydro_year")
    n = len(g)
    if n < CROSSING_MIN_YEARS:
        return None
    x, y = g["hydro_year"].to_numpy(float), g["summer_min_m"].to_numpy(float)
    fit = stats.linregress(x, y)
    resid = y - (fit.intercept + fit.slope * x)
    s = np.sqrt(np.sum(resid ** 2) / (n - 2))
    xh = float(CROSSING_HORIZON_YEAR)
    se_h = s * np.sqrt(1.0 / n + (xh - x.mean()) ** 2 / np.sum((x - x.mean()) ** 2))
    t = stats.t.ppf(0.5 + CROSSING_CI / 2.0, n - 2)
    now_year = int(x.max())
    now = float(fit.intercept + fit.slope * now_year)
    hz = float(fit.intercept + fit.slope * xh)
    lo, hi = hz - t * se_h, hz + t * se_h
    sd16 = "below" if hi < SD16_LEVEL else ("above" if lo >= SD16_LEVEL else "unresolved")
    return {"n_years": n, "first_year": int(x.min()), "last_year": now_year, "slope_m_per_yr": float(fit.slope),
            "p_value": float(fit.pvalue), "fitted_now_m": now, "fitted_horizon_m": hz,
            "horizon_ci_lo_m": float(lo), "horizon_ci_hi_m": float(hi),
            "band_now": band(now, CURRELI_SUMMER), "band_horizon": band(hz, CURRELI_SUMMER),
            "horizon_vs_sd16": sd16}


def counts(t: pd.DataFrame, cl: str) -> dict:
    d = {"cluster": cl, "n_wells": int(len(t))}
    for when in ("now", "horizon"):
        bc = band_counts(t[f"fitted_{when}_m"], CURRELI_SUMMER)
        for b in band_names(CURRELI_SUMMER):
            d[f"{when}_{b}"] = bc[b]
    for k in ("below", "above", "unresolved"):
        d[f"horizon_sd16_{k}"] = int((t["horizon_vs_sd16"] == k).sum())
    below = f"below_{SD16_NAME.lower()}"
    d["cross_sd16_by_horizon"] = int(((t["band_now"] != below) & (t["band_horizon"] == below)).sum())
    d["declining"] = int((t["slope_m_per_yr"] < 0).sum())
    return d


def plot(t: pd.DataFrame, out: Path) -> None:
    fig, axes = plt.subplots(len(CLUSTERS), 1, figsize=(11, 2.6 * len(CLUSTERS)), sharey=True)
    for ax, cl in zip(np.atleast_1d(axes), CLUSTERS):
        g = t[t["cluster"] == cl].sort_values("fitted_now_m", ascending=False).reset_index(drop=True)
        col = CLUSTER_COLOURS.get(int(cl[1:]), "#444")
        xs = np.arange(len(g))
        ax.vlines(xs, g["horizon_ci_lo_m"], g["horizon_ci_hi_m"], color=col, alpha=0.35, lw=3)
        ax.scatter(xs, g["fitted_now_m"], color=col, marker="o", s=22, zorder=3,
                   label="Trend value, last year of record")
        ax.scatter(xs, g["fitted_horizon_m"], color=col, marker="v", s=26, zorder=3,
                   label=f"Trend value in {CROSSING_HORIZON_YEAR} ({int(round(CROSSING_CI * 100))}% interval)")
        for name, lev in CURRELI_SUMMER:
            ax.axhline(lev, color="0.35", lw=0.9, ls=(0, (6, 4)))
            ax.text(1.003, lev, f"{name} {lev:.2f} m".replace("-", "−"), transform=ax.get_yaxis_transform(),
                    va="center", ha="left", fontsize=8, color="0.25")
        ax.set_xticks(xs)
        ax.set_xticklabels([w.upper() for w in g["well"]], rotation=90, fontsize=6.5)
        ax.set_title(CLUSTER_LABELS[int(cl[1:])], fontsize=10, loc="left")
        ax.set_ylabel("Summer minimum (m)")
        ax.yaxis.grid(True, color="#eaeaea", lw=0.5)
        ax.set_axisbelow(True)
    np.atleast_1d(axes)[0].legend(loc="lower left", fontsize=8, frameon=False)
    fig.suptitle("Each well's own summer-minimum trend against the Curreli et al. (2013) levels", fontsize=12)
    fig.tight_layout(rect=[0, 0, 0.95, 0.98])
    render_figure(fig, out, facecolor="white")
    plt.close(fig)


def main() -> int:
    banner("14b", "Wells below the Curreli summer levels, now and at the horizon", version=__version__)
    paths.make_all_dirs()
    phase(1, "Per-well trends")
    pw = pd.read_csv(paths.OUT_14_PER_WELL_EXTREMES)
    rows = []
    for (w, cl), g in pw.groupby(["well", "cluster"]):
        r = well_trend(g)
        if r is not None:
            rows.append({"well": w, "cluster": cl, **r})
    t = pd.DataFrame(rows)
    info(f"{len(t)} of {pw['well'].nunique()} wells with >= {CROSSING_MIN_YEARS} years; horizon {CROSSING_HORIZON_YEAR}, "
         f"{int(round(CROSSING_CI * 100))}% interval")
    t.to_csv(paths.OUT_14B_PER_WELL_TRENDS, index=False)
    saved(f"{paths.OUT_14B_PER_WELL_TRENDS.name} ({len(t)} wells)")

    phase(2, "Counts by cluster")
    c = pd.DataFrame([counts(t[t["cluster"] == cl], cl) for cl in CLUSTERS] + [counts(t, "all")])
    c.to_csv(paths.OUT_14B_CROSSING_COUNTS, index=False)
    saved(f"{paths.OUT_14B_CROSSING_COUNTS.name}")
    for _, r in c.iterrows():
        step(f"{r['cluster']:>3}: {r['n_wells']:>2} wells; below SD16 now {r['now_below_sd16']:>2}, in "
             f"{CROSSING_HORIZON_YEAR} {r['horizon_below_sd16']:>2} (interval wholly below {r['horizon_sd16_below']}, "
             f"unresolved {r['horizon_sd16_unresolved']}); crossing by then {r['cross_sd16_by_horizon']}")

    rn = ReportNumbers()
    rn.add("crossing_horizon_year", CROSSING_HORIZON_YEAR, unit="year", note="config.CROSSING_HORIZON_YEAR (D-294)")
    rn.add("crossing_min_years", CROSSING_MIN_YEARS, unit="years", note="config.CROSSING_MIN_YEARS (D-294)")
    rn.add("crossing_ci_pct", CROSSING_CI * 100.0, unit="%", note="config.CROSSING_CI (D-294)")
    for _, r in c.iterrows():
        for k, v in r.items():
            if k == "cluster":
                continue
            rn.add(f"crossing_{k}", int(v), unit="wells", well=r["cluster"],
                   note="per-well summer-minimum trend counts against the Curreli levels (14b_crossing_counts.csv, D-294)")
    rn.save(paths.OUT_14B_REPORT_NUMBERS)
    saved(f"{paths.OUT_14B_REPORT_NUMBERS.name}")

    phase(3, "Figure")
    plot(t, paths.OUT_14B_PER_WELL_FIG)
    done("14b")
    return 0


if __name__ == "__main__":
    sys.exit(main())
