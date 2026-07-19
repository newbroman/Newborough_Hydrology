#!/usr/bin/env python3
"""
26c_msl5_report_figures.py
==========================

Report-format figures derived from Scripts 26 and 26b — companions to
the methods-style figures those scripts produce. Two outputs:

  1. fig_msl5_trajectory_report.png
     Cluster-mean 5-year MSL trajectory 2014–2025 against the Curreli
     (2013) SD15b/SD16 reference values, with the SD16 dry-slack zone
     shaded and per-cluster 2025 values labelled at the right of each
     trajectory. Differs from Script 26's
     `26_msl_5yr_trajectory.png` (which retains intervention markers
     for the methods context) by emphasising the threshold-crossing
     reading: the SD16 zone is shaded; intervention markers are
     omitted; thresholds are labelled in-figure rather than only in
     the legend. This is the version cited in §4.8.4 of the main
     report.

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

__version__ = "1.1.0"   # Hollingham (2026) — 2026-05-27
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
                         # v1.0.0: Initial release.
                         #   Two report-format figures for §4.8.4 and
                         #   §4.10.1 of the main report. Reads canonical
                         #   pipeline outputs only; no recomputation.

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

# ---------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------
SD15b = -0.61   # Curreli (2013) wet-slack threshold (m, below ground)
SD16  = -0.98   # Curreli (2013) dry-slack threshold (m, below ground)

# Cluster ordering and styling — matches existing report convention
CLUSTERS = [
    "C1 (Lake Edge)",
    "C2 (Dune)",
    "C3 (Western Residual)",
    "C4 (Main Forest)",
    "C5 (Coastal Forest)",
]
SHORT = ["C1", "C2", "C3", "C4", "C5"]

CC = {
    "C1 (Lake Edge)":         "#185FA5",   # blue 600
    "C2 (Dune)":              "#3B6D11",   # green 600
    "C3 (Western Residual)":  "#A32D2D",   # red 600
    "C4 (Main Forest)":       "#534AB7",   # purple 600
    "C5 (Coastal Forest)":    "#854F0B",   # amber 600
}
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
def render_trajectory(per_cluster: pd.DataFrame, out_path: Path) -> None:
    """Write the §4.8.4 trajectory figure to ``out_path``.

    Parameters
    ----------
    per_cluster : DataFrame
        Loaded from ``26_msl_5yr_per_cluster.csv``. Required columns:
        ``cluster_label``, ``window_end_year``, ``MSL5_m_bg_mean``.
    out_path : Path
        Destination PNG.
    """
    fig, ax = plt.subplots(figsize=(9.0, 5.0), dpi=200)

    # SD16 dry-slack zone — shaded down to the y-axis floor
    Y_FLOOR = -1.8
    ax.axhspan(Y_FLOOR, SD16, facecolor="#F09595", alpha=0.18, zorder=0)

    # threshold reference lines
    ax.axhline(SD15b, color="#3B6D11", linewidth=1.0,
               linestyle=(0, (6, 4)), zorder=1)
    ax.axhline(SD16, color="#A32D2D", linewidth=1.0,
               linestyle=(0, (6, 4)), zorder=1)

    # cluster trajectories (window_end_year ≥ 2014 to match the
    # canonical reporting window; earlier window-ends have too few C2/C3
    # wells to be cluster-representative).
    for label in CLUSTERS:
        sub = (per_cluster[per_cluster.cluster_label == label]
               .sort_values("window_end_year"))
        sub = sub[sub.window_end_year >= 2014]
        if not len(sub):
            continue
        ax.plot(
            sub.window_end_year, sub.MSL5_m_bg_mean,
            marker=MK[label], color=CC[label],
            linewidth=1.7, markersize=5.5, markeredgewidth=0,
            label=label, zorder=3,
        )
        # 2025 value label at trajectory's right end
        last = sub.iloc[-1]
        ax.annotate(
            f"{last.MSL5_m_bg_mean:.2f}",
            xy=(last.window_end_year, last.MSL5_m_bg_mean),
            xytext=(8, 0), textcoords="offset points",
            fontsize=9, color=CC[label], va="center", ha="left",
        )

    # in-figure threshold labels (top-left)
    ax.text(2014.1, SD15b + 0.018,
            "SD15b (wet slack, −0.61 m)",
            color="#3B6D11", fontsize=9, va="bottom", ha="left")
    ax.text(2014.1, SD16 + 0.018,
            "SD16 (dry slack, −0.98 m)",
            color="#A32D2D", fontsize=9, va="bottom", ha="left")

    ax.set_xlabel("Hydrology year (window end)")
    ax.set_ylabel("5-year mean spring water level (m, below ground)")
    ax.set_xlim(2013.8, 2025.9)
    ax.set_ylim(Y_FLOOR, 0.05)
    ax.set_xticks(range(2014, 2026))

    leg = ax.legend(
        loc="lower right", frameon=True, framealpha=0.95,
        edgecolor="#cccccc", fontsize=9, ncol=1, labelspacing=0.4,
    )
    leg.get_frame().set_linewidth(0.5)

    ax.set_title(
        "Cluster-mean 5-year MSL (van Willegen et al. 2025) — "
        "window ends 2014–2025",
        pad=8, loc="left", fontweight="normal",
    )

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
    banner("26c", "MSL-5 Report Figures", version="1.0.0")
    print("Script 26c — MSL5 report-format figures")
    print("=" * 60)

    # ensure output directory
    paths.DIR_26C.mkdir(parents=True, exist_ok=True)

    # load canonical sources
    per_cluster = pd.read_csv(paths.OUT_26_5YR_PER_CLUSTER)
    proj        = pd.read_csv(paths.OUT_26B_PROJECTION_TABLE)
    ss          = pd.read_csv(paths.OUT_19_SCENARIO_SUMMARY)

    print(f"  per-cluster trajectory rows : {len(per_cluster)}")
    print(f"  projection summary rows     : {len(proj)}")
    print(f"  scenario summary rows       : {len(ss)}")

    with mpl.rc_context(PLOT_RC):
        render_trajectory(per_cluster, paths.OUT_26C_TRAJECTORY)
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
    transcript.append(f"  {paths.OUT_26B_PROJECTION_TABLE}")
    transcript.append(f"  {paths.OUT_19_SCENARIO_SUMMARY}")
    transcript.append("")
    transcript.append("Outputs:")
    transcript.append(f"  {paths.OUT_26C_TRAJECTORY}")
    transcript.append(f"  {paths.OUT_26C_CONTRAST}")
    transcript.append("")
    transcript.append("Curreli (2013) reference values:")
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
