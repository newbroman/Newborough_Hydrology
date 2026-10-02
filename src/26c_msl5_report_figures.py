#!/usr/bin/env python3
"""
26c_msl5_report_figures.py
==========================

Report-format figures derived from Scripts 26 and 26b — companions to
the methods-style figures those scripts produce. Two outputs:

  1. fig_msl5_trajectory_report.png  (report Figure 44, two panels)
     (a) Cluster-mean 5-year MSL trajectory from MSL_TRAJECTORY_START_YEAR,
         the van Willegen et al. (2025) vegetation-baseline metric, drawn
         WITHOUT threshold lines: neither paper applies a threshold to it.
     (b) Cluster-mean rolling annual minimum over CURRELI_MIN_WINDOW_YEARS —
         the quantity the Curreli (2013) SD15b/SD16 values are four-year
         means of (D-190) — against those values, SD16 zone shaded, latest
         values labelled at the right of each trajectory.
     Until 1.2.0 this was a single MSL5 panel carrying the thresholds.

  2. fig_msl5_vs_summer_min_projection.png
     Two-panel horizontal-bar comparison of ΔMSL5 against
     Δsummer-minimum under UKCP18 RCP8.5, 2050s (top) and 2080s
     (bottom), for the five clusters. ΔMSL5 from Script 26b;
     Δsummer-minimum from Script 19's scenario summary. This is the
     contrast figure cited in §4.10.1 — it makes the headline point
     that the spring baseline metric is substantially better buffered
     against climate change than the summer-minimum metric.

Inputs (all canonical pipeline outputs)
---------------------------------------
  outputs/26_van_willegen_msl/26_msl_5yr_per_cluster.csv
  outputs/26_van_willegen_msl/26_curreli_min_per_cluster.csv
  outputs/26b_van_willegen_msl_projections/26b_msl5_ukcp18_projection_summary.csv
  outputs/19_spatial_groundwater/19_scenario_summary.csv
  outputs/19_spatial_groundwater/19_scenario_summary_model_a.csv   (1.4.0, D-224)

Outputs
-------
  outputs/26c_msl5_report_figures/fig_msl5_trajectory_report.png
  outputs/26c_msl5_report_figures/fig_msl5_vs_summer_min_projection.png
  outputs/26c_msl5_report_figures/26c_results.txt

Usage
-----
  python src/26c_msl5_report_figures.py

References
----------
van Willegen, L., et al. (2025). Five-year carry-over effects in dune
slack vegetation response to hydrology. Ecological Indicators, 170,
113016. https://doi.org/10.1016/j.ecolind.2024.113016

Curreli, A. et al. (2013). SD15b/SD16 dune-slack hydrological
thresholds.
"""

__version__ = "1.4.0"   # Hollingham (2026) — 2026-10-01 (D-224; Martin: "report both", choice 2).
#   The ΔMSL5-against-Δsummer contrast draws both forms: Model B as filled bars (19_scenario_summary.csv,
#   rows filtered explicitly on response == "level_sustained_model_b") and Model A as hatched bars beside
#   them (19_scenario_summary_model_a.csv, Script 19 2.29.0), on the same wells — Model A is projected only
#   where Model B is (D-224), so C4 is "n.i." under both. The transcript gains the Model A columns.
# 1.3.0   # Hollingham (2026) — 2026-10-01 (D-216). The ΔMSL5-against-Δsummer contrast
#   takes BOTH bars from 19_scenario_summary.csv (its msl5 and summer rows): the same wells, the same
#   Model B coefficients and the same convention — the sustained LEVEL response (Script 19 2.28.0,
#   Script 26b 2.0.0). It set 26b's centroid ΔMSL5 beside Script 19's per-well summer mean, and both
#   were one-month rates. A cluster not projected (Model B beta_3 not identified, C4) is marked
#   "n.i." instead of a bar; the axis is no longer fixed to negative values.
# 1.2.0   # Hollingham (2026) — 2026-09-21. D-190: Figure 44 becomes two
#   panels — (a) MSL5 with no threshold lines, (b) the rolling annual minimum from
#   26_curreli_min_per_cluster.csv against SD15b/SD16. The start year and the
#   y-axis floor stop being literals (config.MSL_TRAJECTORY_START_YEAR; data-driven);
#   cluster labels and colours come from config.CLUSTER_LABELS / CLUSTER_COLOURS.
# 1.1.0   # Hollingham (2026) — 2026-05-27
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# pipeline imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import paths

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import render_figure
from utils import config
from utils.config import SD15b as _SD15b_cfg, SD16 as _SD16_cfg

# ---------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------
# Curreli (2013) eco-hydrological thresholds. config.py holds them as POSITIVE
# depths below ground (SD15b, SD16); this figure plots depth on a negative-down
# axis, so they are negated once here. Never restate the numeric values — a
# sign-flipped local copy will not track a config change.
SD15b = -_SD15b_cfg
SD16  = -_SD16_cfg

# Cluster ordering, labels and colours — the canonical maps (config.py), keyed
# by label as the per-cluster CSVs carry them.
CLUSTERS = [config.CLUSTER_LABELS[k] for k in sorted(config.CLUSTER_LABELS)
            if k in config.CLUSTER_COLOURS and k <= 5]
SHORT = [lbl.split(" ")[0] for lbl in CLUSTERS]
CC = {config.CLUSTER_LABELS[k]: config.CLUSTER_COLOURS[k] for k in config.CLUSTER_LABELS
      if k in config.CLUSTER_COLOURS}
MK = {
    "C1 (Lake Edge)":         "o",
    "C2 (Dune)":              "^",
    "C3 (Western Residual)":  "s",
    "C4 (Main Forest)":       "D",
    "C5 (Coastal Forest)":    "P",
}

COL_MSL = "#185FA5"   # ΔMSL5 bar colour
COL_SUM = "#D85A30"   # Δsummer-min bar colour

# Plot configuration — DejaVu Serif keeps figures in tone with the
# rest of the LibreOffice-typeset report.
PLOT_RC = {
    "font.family": "DejaVu Serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.6,
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.4,
    "grid.linestyle": "-",
    "axes.axisbelow": True,
}


# ---------------------------------------------------------------------
# figure 1 — cluster-mean 5-year MSL trajectory (§4.8.4)
# ---------------------------------------------------------------------
def _draw_cluster_lines(ax, df: pd.DataFrame, ycol: str, start_year: int) -> float:
    """Plot each cluster's trajectory from `start_year`, label its latest
    value at the right, and return the lowest value drawn."""
    lowest = 0.0
    for label in CLUSTERS:
        sub = (df[(df.cluster_label == label) & (df.window_end_year >= start_year)]
               .sort_values("window_end_year"))
        if not len(sub):
            continue
        ax.plot(sub.window_end_year, sub[ycol], marker=MK[label], color=CC[label],
                linewidth=1.7, markersize=5.5, markeredgewidth=0, label=label, zorder=3)
        last = sub.iloc[-1]
        ax.annotate(f"{last[ycol]:.2f}".replace("-", "−"),
                    xy=(last.window_end_year, last[ycol]), xytext=(8, 0),
                    textcoords="offset points", fontsize=9, color=CC[label],
                    va="center", ha="left")
        lowest = min(lowest, float(sub[ycol].min()))
    return lowest


def render_trajectory(per_cluster: pd.DataFrame, per_cluster_min: pd.DataFrame,
                      out_path: Path) -> None:
    """Write report Figure 44 to ``out_path``: (a) MSL5, (b) the rolling
    annual minimum against the Curreli reference values (D-190).

    Parameters
    ----------
    per_cluster : DataFrame
        ``26_msl_5yr_per_cluster.csv`` — ``cluster_label``,
        ``window_end_year``, ``MSL5_m_bg_mean``.
    per_cluster_min : DataFrame
        ``26_curreli_min_per_cluster.csv`` — the same keys plus
        ``window_years`` and ``MINw_m_bg_mean``; the headline window
        (config.CURRELI_MIN_WINDOW_YEARS) is drawn.
    out_path : Path
        Destination PNG.
    """
    start = config.MSL_TRAJECTORY_START_YEAR
    w = config.CURRELI_MIN_WINDOW_YEARS
    mins = per_cluster_min[per_cluster_min.window_years == w]
    end = int(max(per_cluster.window_end_year.max(), mins.window_end_year.max()))

    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(9.0, 8.6), dpi=200, sharex=True)

    # (a) MSL5 — the vegetation-baseline metric; no threshold is defined for it
    low_a = _draw_cluster_lines(ax_a, per_cluster, "MSL5_m_bg_mean", start)
    ax_a.set_ylabel("5-year mean spring water level (m, below ground)")
    ax_a.set_title(f"(a)  Cluster-mean {config.MSL_DEFAULT_WINDOW_YEARS}-year MSL "
                   f"(van Willegen et al. 2025) — window ends {start}–{end}",
                   pad=8, loc="left", fontweight="normal")

    # (b) rolling annual minimum — the quantity SD15b/SD16 are means of
    low_b = _draw_cluster_lines(ax_b, mins, "MINw_m_bg_mean", start)
    floor_b = np.floor((min(low_b, SD16) - 0.15) / 0.2) * 0.2
    ax_b.axhspan(floor_b, SD16, facecolor="#F09595", alpha=0.18, zorder=0)
    for y, col, name in ((SD15b, "#3B6D11", "SD15b (wet slack"),
                         (SD16, "#A32D2D", "SD16 (dry slack")):
        ax_b.axhline(y, color=col, linewidth=1.0, linestyle=(0, (6, 4)), zorder=1)
        ax_b.text(start + 0.1, y + 0.018, f"{name}, {y:.2f} m)".replace("-", "−"),
                  color=col, fontsize=9, va="bottom", ha="left")
    ax_b.set_ylabel(f"{w}-year mean annual minimum (m, below ground)")
    ax_b.set_title(f"(b)  Cluster-mean {w}-year mean annual minimum against the "
                   f"Curreli et al. (2013) reference values — window ends {start}–{end}",
                   pad=8, loc="left", fontweight="normal")
    ax_b.set_xlabel("Hydrology year (window end)")

    ax_a.set_ylim(np.floor((low_a - 0.15) / 0.2) * 0.2, 0.05)
    ax_b.set_ylim(floor_b, 0.05)
    ax_b.set_xlim(start - 0.2, end + 0.9)
    ax_b.set_xticks(range(start, end + 1))
    # (b)'s legend sits in the empty band above SD15b, clear of the C5 label
    for ax, loc in ((ax_a, "lower right"), (ax_b, "upper right")):
        leg = ax.legend(loc=loc, frameon=True, framealpha=0.95,
                        edgecolor="#cccccc", fontsize=9, ncol=1, labelspacing=0.4)
        leg.get_frame().set_linewidth(0.5)

    plt.tight_layout()
    render_figure(plt.gcf(), out_path, facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------
# figure 2 — ΔMSL5 vs Δsummer-min contrast (§4.10.1)
# ---------------------------------------------------------------------
RESP_B = "level_sustained_model_b"     # Script 19's response labels (D-216, D-224)
RESP_A = "level_sustained_model_a"


def _rows(ss: pd.DataFrame, scenario_key: str, season: str) -> pd.DataFrame:
    """One scenario and season of a Script 19 summary, filtered on its response
    column so a file carrying more than one convention can never be mixed."""
    resp = ss["response"].isin([RESP_B, RESP_A]) if "response" in ss else True
    return ss[(ss.scenario == scenario_key) & (ss.season == season) & resp].set_index("cluster")


def _scenario_msl_shifts(ss: pd.DataFrame, scenario_key: str) -> list[float]:
    """ΔMSL5 per cluster (in SHORT order): Script 19's msl5 rows (1.3.0) — the
    per-well sustained spring response, the population of its summer rows, on
    whichever form ``ss`` carries (1.4.0)."""
    s = _rows(ss, scenario_key, "msl5")
    return [float(s.loc[c, "dh_mean_m"]) if c in s.index else np.nan for c in SHORT]


def _scenario_summer_min_shifts(ss: pd.DataFrame, scenario_key: str) -> list[float]:
    """Δh-summer-mean per cluster (in SHORT order) for the given scenario.

    ``ss`` is loaded from ``19_scenario_summary.csv``.  ``scenario_key``
    is the long label that file uses, e.g. ``"ukcp18_2050s"``.

    Script 19's "summer" row is the mean over the SUMMER_MONTHS of the
    sustained level response (2.28.0, D-216) — the monthly model's closest
    correlate of the annual summer minimum.
    """
    s = _rows(ss, scenario_key, "summer")
    return [float(s.loc[c, "dh_mean_m"]) if c in s.index else np.nan for c in SHORT]


def _render_contrast_panel(ax, msl_shifts, sm_shifts, title,
                           msl_a=None, sm_a=None) -> None:
    """Render a single horizontal grouped-bar panel onto ``ax``: per cluster,
    ΔMSL5 and Δsummer-minimum on Model B (filled) and, when given, on Model A
    (hatched, the same colour) — D-224."""
    y = np.arange(len(CLUSTERS))
    both = msl_a is not None and sm_a is not None
    series = ([(msl_shifts, COL_MSL, False), (msl_a, COL_MSL, True),
               (sm_shifts, COL_SUM, False), (sm_a, COL_SUM, True)] if both else
              [(msl_shifts, COL_MSL, False), (sm_shifts, COL_SUM, False)])
    h = 0.8 / len(series)
    offs = (np.arange(len(series)) - (len(series) - 1) / 2) * h
    for k, ((vals, col, hatched), off) in enumerate(zip(series, offs)):
        vals_plot = [v if np.isfinite(v) else 0.0 for v in vals]
        bars = ax.barh(y + off, vals_plot, height=h * 0.92, zorder=3,
                       color="white" if hatched else col, edgecolor=col,
                       hatch="////" if hatched else None, linewidth=0.8)
        for rect, v in zip(bars, vals):
            yc = rect.get_y() + rect.get_height() / 2
            if not np.isfinite(v):
                if k == 0:                              # one mark per withheld cluster
                    ax.text(0, rect.get_y() + h * (len(series) - 1) / 2 + rect.get_height() / 2,
                            " n.i. (not identified)", color="#777", fontsize=8,
                            va="center", ha="left")
                continue
            ax.text(v + (-0.004 if v < 0 else 0.004), yc, f"{int(round(v * 1000)):d} mm",
                    color=col, fontsize=7.5, va="center", ha="right" if v < 0 else "left")

    ax.set_yticks(y)
    ax.set_yticklabels(CLUSTERS)
    ax.invert_yaxis()
    ax.set_title(title, pad=4, loc="left", fontweight="normal", fontsize=11)
    ax.axvline(0, color="#333333", linewidth=0.6, zorder=2)
    allv = list(msl_shifts) + list(sm_shifts) + (list(msl_a) + list(sm_a) if both else [])
    fin = [v for v in allv if np.isfinite(v)] or [0.0]
    lo, hi = min(min(fin), 0.0), max(max(fin), 0.0)
    pad = 0.22 * max(hi - lo, 0.01)
    ax.set_xlim(lo - pad, hi + pad)
    ax.grid(axis="x", color="#dddddd", linewidth=0.4)
    ax.grid(axis="y", visible=False)


def render_contrast(proj: pd.DataFrame,
                    ss: pd.DataFrame,
                    out_path: Path,
                    ss_a: pd.DataFrame = None) -> None:
    """Write the §4.10.1 ΔMSL5 vs Δsummer-min contrast figure: Model B filled,
    Model A hatched beside it when ``ss_a`` is given (1.4.0, D-224)."""
    a = ss_a is not None
    fig, axs = plt.subplots(2, 1, figsize=(9.0, 8.6 if a else 6.4), dpi=200, sharex=True)
    for ax, key, dec in ((axs[0], "ukcp18_2050s", "2050s"), (axs[1], "ukcp18_2080s", "2080s")):
        _render_contrast_panel(
            ax, _scenario_msl_shifts(ss, key), _scenario_summer_min_shifts(ss, key),
            f"{dec} — UKCP18 RCP8.5, 50th percentile",
            msl_a=_scenario_msl_shifts(ss_a, key) if a else None,
            sm_a=_scenario_summer_min_shifts(ss_a, key) if a else None,
        )
    axs[1].set_xlabel("Sustained level shift (m) — negative = deeper; "
                      + ("filled: Model B, hatched: Model A (D-224)" if a else "Model B, D-216"))

    handles = [plt.Rectangle((0, 0), 1, 1, color=COL_MSL),
               plt.Rectangle((0, 0), 1, 1, color=COL_SUM)]
    labels = ["ΔMSL5 (5-yr mean spring water level)", "Δsummer-minimum"]
    if a:
        handles += [plt.Rectangle((0, 0), 1, 1, facecolor="#555555", edgecolor="#555555"),
                    plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="#555555",
                                  hatch="////")]
        labels += ["Model B (intercept form)", "Model A (published form)"]
    fig.legend(handles=handles, labels=labels,
               loc="upper center", bbox_to_anchor=(0.5, 1.005),
               ncol=2, frameon=False, fontsize=10)

    plt.tight_layout(rect=(0, 0, 1, 0.94 if a else 0.96))
    render_figure(plt.gcf(), out_path, facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------
def main() -> int:
    banner("26c", "MSL-5 Report Figures", version=__version__)
    print("Script 26c — MSL5 report-format figures")
    print("=" * 60)

    # ensure output directory
    paths.DIR_26C.mkdir(parents=True, exist_ok=True)

    # load canonical sources
    per_cluster = pd.read_csv(paths.OUT_26_5YR_PER_CLUSTER)
    per_cluster_min = pd.read_csv(paths.OUT_26_CURRELI_MIN_PER_CLUSTER)
    proj        = pd.read_csv(paths.OUT_26B_PROJECTION_TABLE)
    ss          = pd.read_csv(paths.OUT_19_SCENARIO_SUMMARY)
    ss_a        = (pd.read_csv(paths.OUT_19_SCENARIO_SUMMARY_MODEL_A)       # 1.4.0, D-224
                   if paths.OUT_19_SCENARIO_SUMMARY_MODEL_A.exists() else None)
    if ss_a is None:
        warn(f"{paths.OUT_19_SCENARIO_SUMMARY_MODEL_A.name} absent - contrast drawn on Model B "
             f"alone; run Script 19 first")

    print(f"  per-cluster trajectory rows : {len(per_cluster)}")
    print(f"  per-cluster annual-min rows : {len(per_cluster_min)}")
    print(f"  projection summary rows     : {len(proj)}")
    print(f"  scenario summary rows       : {len(ss)}")

    with mpl.rc_context(PLOT_RC):
        render_trajectory(per_cluster, per_cluster_min, paths.OUT_26C_TRAJECTORY)
        print(f"  wrote {paths.OUT_26C_TRAJECTORY.name}")

        render_contrast(proj, ss, paths.OUT_26C_CONTRAST, ss_a=ss_a)
        print(f"  wrote {paths.OUT_26C_CONTRAST.name}")

    # transcript — for provenance, mirroring 26 / 26b convention
    transcript = []
    transcript.append("Script 26c — MSL5 report-format figures")
    transcript.append("=" * 60)
    transcript.append("")
    transcript.append("Sources:")
    transcript.append(f"  {paths.OUT_26_5YR_PER_CLUSTER}")
    transcript.append(f"  {paths.OUT_26_CURRELI_MIN_PER_CLUSTER}")
    transcript.append(f"  {paths.OUT_26B_PROJECTION_TABLE}")
    transcript.append(f"  {paths.OUT_19_SCENARIO_SUMMARY}")
    if ss_a is not None:
        transcript.append(f"  {paths.OUT_19_SCENARIO_SUMMARY_MODEL_A}")
    transcript.append("")
    transcript.append("Outputs:")
    transcript.append(f"  {paths.OUT_26C_TRAJECTORY}")
    transcript.append(f"  {paths.OUT_26C_CONTRAST}")
    transcript.append("")
    transcript.append(f"Curreli (2013) reference values (four-year means of the annual "
                      f"minimum; drawn on the {config.CURRELI_MIN_WINDOW_YEARS}-year "
                      f"mean annual minimum, panel b — D-190):")
    transcript.append(f"  SD15b (wet slack)  : {SD15b:.2f} m below ground")
    transcript.append(f"  SD16  (dry slack)  : {SD16:.2f} m below ground")
    transcript.append("")
    transcript.append("ΔMSL5 vs Δsummer-minimum, UKCP18 RCP8.5 (m, below ground):")
    msl_50 = _scenario_msl_shifts(ss, "ukcp18_2050s")
    msl_80 = _scenario_msl_shifts(ss, "ukcp18_2080s")
    sm_50  = _scenario_summer_min_shifts(ss, "ukcp18_2050s")
    sm_80  = _scenario_summer_min_shifts(ss, "ukcp18_2080s")
    transcript.append(
        f"  {'Cluster':<25s} "
        f"{'ΔMSL5_50s':>10s} {'Δsmin_50s':>10s}   "
        f"{'ΔMSL5_80s':>10s} {'Δsmin_80s':>10s}"
    )
    for i, c in enumerate(CLUSTERS):
        transcript.append(
            f"  {c:<25s} "
            f"{msl_50[i]:>+10.4f} {sm_50[i]:>+10.4f}   "
            f"{msl_80[i]:>+10.4f} {sm_80[i]:>+10.4f}"
        )

    if ss_a is not None:
        transcript.append("")
        transcript.append("The same on Model A (D-224; Model A projected only where Model B is):")
        ma = {k: (_scenario_msl_shifts(ss_a, k), _scenario_summer_min_shifts(ss_a, k))
              for k in ("ukcp18_2050s", "ukcp18_2080s")}
        for i, c in enumerate(CLUSTERS):
            transcript.append(
                f"  {c:<25s} "
                f"{ma['ukcp18_2050s'][0][i]:>+10.4f} {ma['ukcp18_2050s'][1][i]:>+10.4f}   "
                f"{ma['ukcp18_2080s'][0][i]:>+10.4f} {ma['ukcp18_2080s'][1][i]:>+10.4f}"
            )

    paths.OUT_26C_RESULTS_TXT.write_text("\n".join(transcript))
    print(f"  wrote {paths.OUT_26C_RESULTS_TXT.name}")
    print("=== Script 26c complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
