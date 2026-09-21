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

__version__ = "1.2.0"   # Hollingham (2026) — 2026-09-21. D-190: Figure 44 becomes two
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
def _scenario_msl_shifts(proj: pd.DataFrame, scenario: str) -> list[float]:
    """ΔMSL5 per cluster (in CLUSTERS order) for the given scenario.

    ``proj`` is loaded from
    ``26b_msl5_ukcp18_projection_summary.csv``. ``scenario`` is the
    short label ``"2050s"`` or ``"2080s"`` matching that file's
    ``scenario`` column.
    """
    s = proj[proj.scenario == scenario].set_index("cluster_label")
    return [s.loc[c, "msl5_shift_mean_m"] for c in CLUSTERS]


def _scenario_summer_min_shifts(ss: pd.DataFrame, scenario_key: str) -> list[float]:
    """Δh-summer-mean per cluster (in SHORT order) for the given scenario.

    ``ss`` is loaded from ``19_scenario_summary.csv``.  ``scenario_key``
    is the long label that file uses, e.g. ``"ukcp18_2050s"``.

    Note: Script 19's "summer" row is the *seasonal mean* of monthly Δh
    over the SUMMER_MONTHS window. We treat this as the projected
    summer-minimum shift in keeping with the perturbation framework used
    throughout §4.10 — the SSM is a monthly-resolution model and the
    seasonal-mean Δh is its closest available correlate to the annual
    summer minimum.
    """
    s = ss[(ss.scenario == scenario_key) & (ss.season == "summer")]
    s = s.set_index("cluster")
    return [s.loc[c, "dh_mean_m"] for c in SHORT]


def _render_contrast_panel(ax, msl_shifts, sm_shifts, title) -> None:
    """Render a single horizontal paired-bar panel onto ``ax``."""
    y = np.arange(len(CLUSTERS))
    h = 0.36

    b1 = ax.barh(y - h / 2, msl_shifts, height=h, color=COL_MSL,
                 label="ΔMSL5", zorder=3)
    b2 = ax.barh(y + h / 2, sm_shifts, height=h, color=COL_SUM,
                 label="Δsummer-minimum", zorder=3)

    for bars, vals, col in [(b1, msl_shifts, COL_MSL),
                            (b2, sm_shifts, COL_SUM)]:
        for rect, v in zip(bars, vals):
            ax.text(
                v - 0.0025,
                rect.get_y() + rect.get_height() / 2,
                f"{int(round(v * 1000)):d} mm",
                color=col, fontsize=8.5, va="center", ha="right",
            )

    ax.set_yticks(y)
    ax.set_yticklabels(CLUSTERS)
    ax.invert_yaxis()
    ax.set_title(title, pad=4, loc="left", fontweight="normal", fontsize=11)
    ax.axvline(0, color="#333333", linewidth=0.6, zorder=2)
    ax.set_xlim(-0.155, 0.005)
    ax.grid(axis="x", color="#dddddd", linewidth=0.4)
    ax.grid(axis="y", visible=False)


def render_contrast(proj: pd.DataFrame,
                    ss: pd.DataFrame,
                    out_path: Path) -> None:
    """Write the §4.10.1 ΔMSL5 vs Δsummer-min contrast figure."""
    msl_50 = _scenario_msl_shifts(proj, "2050s")
    msl_80 = _scenario_msl_shifts(proj, "2080s")
    sm_50  = _scenario_summer_min_shifts(ss, "ukcp18_2050s")
    sm_80  = _scenario_summer_min_shifts(ss, "ukcp18_2080s")

    fig, axs = plt.subplots(2, 1, figsize=(9.0, 6.4), dpi=200, sharex=True)

    _render_contrast_panel(
        axs[0], msl_50, sm_50,
        "2050s — UKCP18 RCP8.5, 50th percentile",
    )
    _render_contrast_panel(
        axs[1], msl_80, sm_80,
        "2080s — UKCP18 RCP8.5, 50th percentile",
    )
    axs[1].set_xlabel("Δh (m, below ground) — negative = drier")

    fig.legend(
        handles=[
            plt.Rectangle((0, 0), 1, 1, color=COL_MSL),
            plt.Rectangle((0, 0), 1, 1, color=COL_SUM),
        ],
        labels=[
            "ΔMSL5 (5-yr mean spring water level)",
            "Δsummer-minimum",
        ],
        loc="upper center", bbox_to_anchor=(0.5, 1.005),
        ncol=2, frameon=False, fontsize=10,
    )

    plt.tight_layout(rect=(0, 0, 1, 0.96))
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

    print(f"  per-cluster trajectory rows : {len(per_cluster)}")
    print(f"  per-cluster annual-min rows : {len(per_cluster_min)}")
    print(f"  projection summary rows     : {len(proj)}")
    print(f"  scenario summary rows       : {len(ss)}")

    with mpl.rc_context(PLOT_RC):
        render_trajectory(per_cluster, per_cluster_min, paths.OUT_26C_TRAJECTORY)
        print(f"  wrote {paths.OUT_26C_TRAJECTORY.name}")

        render_contrast(proj, ss, paths.OUT_26C_CONTRAST)
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
    msl_50 = _scenario_msl_shifts(proj, "2050s")
    msl_80 = _scenario_msl_shifts(proj, "2080s")
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

    paths.OUT_26C_RESULTS_TXT.write_text("\n".join(transcript))
    print(f"  wrote {paths.OUT_26C_RESULTS_TXT.name}")
    print("=== Script 26c complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
