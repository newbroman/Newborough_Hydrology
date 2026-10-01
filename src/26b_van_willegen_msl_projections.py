#!/usr/bin/env python3
"""
26b_van_willegen_msl_projections.py
====================================
Long-horizon MSL5 climate projections under UKCP18 RCP8.5 scenarios.

Purpose
-------
Tool B of the spring-water-level forecasting pair. Companion to Script 26
(observed van Willegen 2025 5-year mean spring water level) and to
Section 5 of Script 11 (single-year MSL transfer function — Tool A).

This script projects how each cluster's MSL5 trajectory would shift under
UKCP18 RCP8.5 climate scenarios for the 2050s and 2080s. Output is a
per-cluster trajectory plot showing the observed 2014-2025 MSL5 alongside
the climate-perturbed equivalents.

Method (2.0.0, D-216)
---------------------
For each cluster and each scenario the monthly forcing change over the observed
climate record is

    Δf(t) = β₁·P(t)·(sP(m) − 1) − β₂·PET(t)·(sPET(m) − 1)

and the LEVEL it produces is the difference between a perturbed and a baseline
SSM run, d(t) = (1 − β₃)·d(t−1) + Δf(t) (model_utils.scenario_delta_series), in
which the intercept and the drainage datum cancel. The run starts from the
sustained state (model_utils.sustained_monthly_response): the scenario
climatology is taken to have been in force before the record began. β₁, β₂, β₃
are the cluster's MODEL B coefficients (03_16_model_b_persistence.csv): the
response is governed by the memory, and Model B's β₃ is datum-free.

The UKCP18 multipliers sP / sPET are seasonal (Nov-Mar winter window;
May-Sep summer window; April and October as shoulder months get the mean
of the two). The full UKCP18 RCP8.5 Wales 50th-percentile central
estimates from Script 19's SCENARIO_PARAMS dict drive each scenario:

    2050s:   P_winter ×1.10   P_summer ×0.85   PET_winter ×1.05   PET_summer ×1.20
    2080s:   P_winter ×1.20   P_summer ×0.70   PET_winter ×1.10   PET_summer ×1.35

Each window's ΔMSL5 is the mean of d over the spring months
(config.MSL_SPRING_MONTHS, D-189) of the window's springs, so it varies a little
from window to window with the observed sequence; its long-run value is the
sustained spring response (msl5_shift_sustained_m). Until 2.0.0 this script
added one month's Δf — a rate — as a level, over March-May. The figure shows the
unmodified Script 26 line (same colours and markers) plus two
scenario-shifted versions per cluster.

What this projection IS and IS NOT
----------------------------------
This is a perturbation overlay, NOT a forward-in-time simulation:

  • It tells you "what would the observed MSL5 trajectory have looked
    like over 2014-2025 if the UKCP18 2050s climate had been in force
    throughout that period?"

  • The horizontal offset between the observed and projected trajectories
    is the scenario sensitivity at each cluster.

  • The year-to-year shape is the observed climatology — same wet years,
    same dry years, same intervention markers visible in the same places.

  • This is consistent with the steady-state SSM limitations documented
    in Script 21: the SSM cannot be run forward from an arbitrary initial
    condition without accumulating drift (the water-balance intercept α is
    not in the forward integration). The single-step monthly perturbation
    approach avoids this drift by working as a forcing-shift overlay on
    the observed record rather than an integrated time projection.

  • This is NOT a forecast of what MSL5 will be observed in 2050. UKCP18
    projects shifts in climatology, not shifts in interannual variability;
    the actual 2050 record could include wetter or drier individual years
    than any observed in 2014-2025. The projected trajectory is the
    climatological response, not a single-realisation forecast.

The figure caption and any cite of this script in the report must reflect
this framing. Authors should also note the established UKCP18 caveat: the
multipliers are 50th-percentile central estimates, and end-century 5th-95th
percentile ranges span much wider intervals (Met Office, 2018).

Inputs
------
  03_03_cluster_mechanistic_coefficients.csv  — cluster SSM β coefficients
  01_climate.csv                              — RAF Valley monthly P, PET
  26_msl_5yr_per_cluster_centroid.csv         — observed MSL5 baseline (Method B,
                                                cluster centroid from Script 03;
                                                same network composition as the
                                                SSM coefficients driving the
                                                perturbation, see Script 26 v1.1.2)

Outputs
-------
  OUT_26B_PROJECTION_FIG       — projected MSL5 trajectory figure
  OUT_26B_PROJECTION_TABLE     — per-cluster scenario summary CSV
                                  (CANONICAL, centroid-fitted β; consumed
                                  by Script 26c and the report §3.7.5 /
                                  §4.8.4 / §4.10.1)
  OUT_26B_PROJECTION_TABLE_PERWELL — secondary per-cluster summary CSV
                                  built from per-well β (mean of the per-
                                  well spring Δh within each cluster);
                                  added v1.1.0; serves as the validation
                                  target for the Script 19 v2.8.0 viewer
                                  ΔMSL5 row.  NOT consumed by 26c.
  OUT_26B_DELTA_H_PER_CLUSTER  — per-cluster monthly Δh shifts (12 months × 2 scenarios)
  OUT_26B_RESULTS_TXT          — run transcript

Cross-references
----------------
  utils/model_utils.monthly_perturbation()        — canonical Δh pattern
  utils/config.UKCP18_*                           — 2050s scenario multipliers
  Script 19 SCENARIO_PARAMS                       — 2080s multipliers (not in config)
  Script 21 build_scenarios()                     — canonical β₂ change pattern
  Script 26 plot_cluster_trajectory()             — observed-trajectory layout this script extends
"""

__version__ = "2.0.0"  # Hollingham (2026) - 2026-10-01 (D-216; Martin: "Sustained, Model B").
#   Two corrections. (1) SPRING MONTHS: delta_h[[2, 3, 4]] was March-May; D-189 moved spring to the
#   bucketed February-April (config.MSL_SPRING_MONTHS) and this script was never moved. (2) A RATE
#   WAS ADDED AS A LEVEL: the shift was one month's forcing change, beta_1*dP - beta_2*dPET (m/month),
#   added to the MSL5 trajectory as if it were metres. A climate held every year accumulates through
#   the drainage term; the shift is now the LEVEL difference between a perturbed and a baseline SSM
#   run over the observed climate record (model_utils.scenario_delta_series, started from the
#   sustained state so the first windows are not spun up from zero), averaged over each window's
#   springs, so it varies a little by window. Coefficients are MODEL B (03_16 centroids): the
#   response is set by the memory, and Model B's beta_3 is the datum-free one (D-109, D-216). A
#   cluster whose Model B beta_3 fails Script 48's identifiability rule (C4) is withheld, not
#   projected. The old quantity is kept as a diagnostic column (spring_one_month_rate_model_a_m).
#   The per-well pathway (Script 19's validation target) follows the same convention. Figure: the
#   2050s / 2080s lines carry different markers (square / triangle) and every line is named at its
#   right-hand end; legend samples lengthened (Martin: "you cant tell which line is which").
# 1.4.0  # Hollingham (2026) - 2026-09-28. T-91: added report-number
#   emits (no analysis change) - per (cluster, scenario) msl5_shift_mean_m and
#   the largest-shift cluster per scenario, written to 26b_report_numbers.csv
#   so the Methods Supplement S.18b.3 sentence binds to a citation row.
#
# 1.3.0  # Hollingham (2026) - 2026-08-31. SUMMER_MONTHS now imported from config.SUMMER_DRY_CLIMATE_MONTHS.
#   Batch two of the seasonal-windows migration (D-100): the window's
#   MONTHS ARE UNCHANGED and the constant is asserted equal to the literal it
#   replaced, in value and in type, read mechanically out of git HEAD. No
#   committed value moves.
#
# v1.2.2  # Hollingham (2026) — 2026-08-30. WINTER_MONTHS now imported
#   from config.WINTER_WET_CLIMATE_MONTHS — same months, one definition
#   (D-100). No behavioural change; asserted equal to the literal it replaced.
#
# v1.2.1  # Hollingham (2026) -- 2026-08-18. UKCP18_SCENARIOS now
#   imported from utils.config; this script and Script 19 each held a copy.
#
# v1.2.0  # Hollingham (2026) — 2026-05-27
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)

from utils import config, paths
from utils.render_utils import render_figure
from utils.model_utils import (scenario_delta_series, sustained_monthly_response,
                               response_identified, climate_forcing_change_12)

# Spring (D-189): the bucketed months config.MSL_SPRING_MONTHS, as 0-based calendar
# indices into the 12-month arrays. Was a literal [2, 3, 4] (March-May) until 2.0.0.
SPRING_IDX = [int(m) - 1 for m in config.MSL_SPRING_MONTHS]
MODEL_B_N_PARAMS = 4          # beta_1, beta_2, beta_3 and the intercept

# ── Output paths ──────────────────────────────────────────────────────────────
paths.DIR_26B.mkdir(parents=True, exist_ok=True)

OUT_FIG    = paths.OUT_26B_PROJECTION_FIG
OUT_TABLE  = paths.OUT_26B_PROJECTION_TABLE
OUT_TABLE_PERWELL = paths.OUT_26B_PROJECTION_TABLE_PERWELL   # v1.1.0
OUT_DELTAS = paths.OUT_26B_DELTA_H_PER_CLUSTER
OUT_TXT    = paths.OUT_26B_RESULTS_TXT

# ── UKCP18 RCP8.5 Wales seasonal multipliers ──────────────────────────────────
# Source: Script 19's canonical SCENARIO_PARAMS dict. The 2050s multipliers
# match the UKCP18_{DRY,WET} ranges in utils.config (central 2050s estimates
# from the UKCP18 Regional 12 km ensemble for Wales under RCP8.5, 50th
# percentile). The 2080s multipliers come from Script 19's SCENARIO_PARAMS
# (not currently in utils.config but documented there).
#
# Convention (matches Script 19 viewer):
#   Winter = Nov-Mar  (months 11, 12, 1, 2, 3)
#   Summer = May-Sep  (months  5, 6, 7, 8, 9)
#   Shoulder = Apr, Oct  — these get the mean of winter and summer multipliers
# Imported from config rather than mirrored here: Script 19 held an identical
# copy, and two copies of a published scenario parameter is one too many.
from utils.config import UKCP18_SCENARIOS

SCENARIO_STYLES = {
    "2050s": {"linestyle": (0, (4, 2)),       "linewidth": 1.4, "alpha": 0.85, "marker": "s",
              "label": "UKCP18 RCP8.5 2050s (50th %ile)"},
    "2080s": {"linestyle": (0, (1.5, 1.5)),   "linewidth": 1.4, "alpha": 0.85, "marker": "^",
              "label": "UKCP18 RCP8.5 2080s (50th %ile)"},
}

WINTER_MONTHS = list(config.WINTER_WET_CLIMATE_MONTHS)   # Nov-Mar wet-season
                                                        # climate (D-100)
SUMMER_MONTHS = list(config.SUMMER_DRY_CLIMATE_MONTHS)   # May-Sep dry-season
                                                        # climate (D-100)
SHOULDER_MONTHS = [4, 10]

def _monthly_multipliers(scenario_key: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert seasonal UKCP18 multipliers into a 12-element monthly array.
    Shoulder months (April, October) get the mean of the winter and summer
    multipliers — a documented choice for transitional months that straddle
    the canonical winter / summer windows.
    """
    s = UKCP18_SCENARIOS[scenario_key]
    sP   = np.ones(12)
    sPET = np.ones(12)
    for m in WINTER_MONTHS:
        sP[m - 1]   = s["sP_w"]
        sPET[m - 1] = s["sPET_w"]
    for m in SUMMER_MONTHS:
        sP[m - 1]   = s["sP_s"]
        sPET[m - 1] = s["sPET_s"]
    for m in SHOULDER_MONTHS:
        sP[m - 1]   = 0.5 * (s["sP_w"]   + s["sP_s"])
        sPET[m - 1] = 0.5 * (s["sPET_w"] + s["sPET_s"])
    return sP, sPET

def _compute_monthly_delta_h(b1: float, b2: float,
                              monthly_P_m: np.ndarray,
                              monthly_PET_m: np.ndarray,
                              sP: np.ndarray,
                              sPET: np.ndarray) -> np.ndarray:
    """
    Single-step monthly Δh perturbation under a pure climate scenario
    (no land-use change, so β₂ is unchanged):

        Δh(m) = β₁·(P_scen(m) − P_base(m)) − β₂·(PET_scen(m) − PET_base(m))

    Returns a 12-element array indexed 0=Jan, 1=Feb, ..., 11=Dec.

    Note on units: the cluster β coefficients in Script 03 are fitted on
    raw climate (P in m, PET in m). The monthly_P_m and monthly_PET_m
    arrays here must therefore also be in m, not mm. The function does
    not convert — the caller is responsible for unit consistency.
    """
    delta_P   = monthly_P_m   * (sP   - 1.0)
    delta_PET = monthly_PET_m * (sPET - 1.0)
    return b1 * delta_P - b2 * delta_PET

def _spring_shift_by_year(b1, b2, b3, clim_window, sP, sPET,
                          monthly_P_m, monthly_PET_m) -> tuple[pd.Series, float]:
    """(spring level shift per calendar year, sustained spring shift) under one
    scenario — the D-216 level response. Spring months are calendar Feb-Apr, which
    Script 26 assigns to the hydrology year of the same calendar year."""
    m_idx = clim_window.index.month.values - 1
    dF = (b1 * clim_window["P_m"].values * (sP[m_idx] - 1.0)
          - b2 * clim_window["PET"].values * (sPET[m_idx] - 1.0))
    dF12 = climate_forcing_change_12(b1, b2, monthly_P_m, monthly_PET_m, sP, sPET)
    ss = sustained_monthly_response(b3, dF12)
    d0 = float(ss[(int(clim_window.index[0].month) - 2) % 12])   # the month before the record
    d = pd.Series(scenario_delta_series(b3, dF, d0=d0), index=clim_window.index)
    spr = d[d.index.month.isin(config.MSL_SPRING_MONTHS)]
    return spr.groupby(spr.index.year).mean(), float(np.mean(ss[SPRING_IDX]))


def _compute_projected_msl5_trajectory(
        observed_traj: pd.DataFrame,
        spring_shift_by_year: pd.Series,
) -> pd.DataFrame:
    """
    Shift the observed MSL5 trajectory by each window's mean spring level shift
    (2.0.0, D-216): window ending in hydrology year y averages the spring shifts of
    y − MSL_DEFAULT_WINDOW_YEARS + 1 … y. The observed line stays byte-identical
    to Script 26's published trajectory.

    Parameters
    ----------
    observed_traj : pd.DataFrame
        From Script 26's 26_msl_5yr_per_cluster.csv subset for one cluster,
        columns: window_end_year, MSL5_observed.
    spring_shift_by_year : pd.Series
        Spring level shift (m) per calendar year, from _spring_shift_by_year.

    Returns
    -------
    pd.DataFrame with columns: window_end_year, MSL5_perturbed, msl5_shift.
    """
    W = int(config.MSL_DEFAULT_WINDOW_YEARS)
    out = observed_traj.copy()
    out["msl5_shift"] = [
        float(spring_shift_by_year.reindex(range(int(y) - W + 1, int(y) + 1)).mean())
        for y in out["window_end_year"]]
    out["MSL5_perturbed"] = out["MSL5_observed"] + out["msl5_shift"]
    return out[["window_end_year", "MSL5_perturbed", "msl5_shift"]]

def _render_bar_panel(ax, projected_trajectories, cluster_ids_present):
    """
    Render the ΔMSL5 summary bar chart in the figure's 6th panel.
    One group per cluster, two bars per group (2050s, 2080s). Bars are
    coloured by cluster (matches the trajectory panels above) and
    hatched to distinguish scenarios. Y-axis is in centimetres for
    readability at this scale.
    """
    width = 0.38
    x = np.arange(len(cluster_ids_present))

    bars_2050 = []
    bars_2080 = []
    cluster_labels = []
    for cid in cluster_ids_present:
        cluster_labels.append(f"C{cid}")
        p50 = projected_trajectories.get((cid, "2050s"))
        p80 = projected_trajectories.get((cid, "2080s"))
        bars_2050.append(float(p50["msl5_shift"].mean()) * 100.0
                         if p50 is not None and len(p50) else np.nan)
        bars_2080.append(float(p80["msl5_shift"].mean()) * 100.0
                         if p80 is not None and len(p80) else np.nan)

    # Colour each bar by its cluster
    colours = [config.CLUSTER_COLOURS.get(cid, "#444")
               for cid in cluster_ids_present]
    ax.bar(x - width / 2, bars_2050, width=width, color=colours,
           edgecolor="black", linewidth=0.5,
           label="UKCP18 RCP8.5 2050s")
    ax.bar(x + width / 2, bars_2080, width=width, color=colours,
           edgecolor="black", linewidth=0.5, hatch="//",
           label="UKCP18 RCP8.5 2080s")

    # Numeric labels at the bar ends; a withheld cluster (Model B beta_3 not
    # identified, 2.0.0) is marked rather than drawn as a zero
    for xs, vals in ((x - width / 2, bars_2050), (x + width / 2, bars_2080)):
        for xi, v in zip(xs, vals):
            if not np.isfinite(v):
                ax.text(xi, 0, "n.i.", ha="center", va="bottom", fontsize=7, color="#666")
                continue
            ax.text(xi, v, f"{v:+.1f}", ha="center", va="top" if v < 0 else "bottom",
                    fontsize=7.5, color="#222")

    ax.set_xticks(x)
    ax.set_xticklabels(cluster_labels, fontsize=9)
    ax.set_ylabel("Projected ΔMSL5 (cm)", fontsize=9)
    ax.set_title("Projected ΔMSL5 by cluster and scenario", fontsize=10)
    ax.axhline(0, color="#333", lw=0.5)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(labelsize=8)
    # Room for labels on both sides of zero (shifts can be positive, 2.0.0)
    finite = [v for v in bars_2050 + bars_2080 if np.isfinite(v)] or [0.0]
    span = max(max(finite) - min(min(finite), 0.0), 1.0)
    ax.set_ylim(min(min(finite), 0.0) - 0.15 * span, max(max(finite), 0.0) + 0.15 * span)

def render_projection_figure(
        observed_trajectories: dict[int, pd.DataFrame],
        projected_trajectories: dict[tuple[int, str], pd.DataFrame],
        out_path: Path,
) -> None:
    """
    Render the projection figure as a 2x3 small-multiple layout:
      • 5 trajectory panels (one per cluster), per-panel auto-scaled y-axis
        so the scenario shift is visible at the panel's own scale
      • 1 summary bar chart (bottom-right) showing ΔMSL5 per cluster ×
        scenario in centimetres

    A figure-level horizontal legend strip sits below the suptitle.

    The scenario lines are the observed trajectory shifted by each window's
    sustained level response (2.0.0, D-216); a cluster whose Model B β₃ is not
    identified carries no scenario line. The bar chart gives the mean shift.
    """
    cluster_ids_present = sorted(observed_trajectories.keys())

    fig, axes = plt.subplots(2, 3, figsize=(14, 8.0), squeeze=False)
    axes_flat = axes.flatten()

    for ax, cid in zip(axes_flat, cluster_ids_present):
        col = config.CLUSTER_COLOURS.get(cid, "#444")
        lbl = config.CLUSTER_LABELS.get(cid, f"C{cid}")

        obs = observed_trajectories[cid].sort_values("window_end_year")
        ax.plot(obs["window_end_year"], obs["MSL5_observed"],
                color=col, marker="o", linewidth=1.8, markersize=4.5,
                label="Observed", zorder=5)
        _lo = obs.iloc[-1]
        ax.annotate("observed", (_lo["window_end_year"], _lo["MSL5_observed"]),
                    xytext=(5, 0), textcoords="offset points", va="center",
                    fontsize=7, color=col, fontweight="bold")

        for scen in ["2050s", "2080s"]:
            proj = projected_trajectories.get((cid, scen))
            if proj is None or proj.empty:
                continue
            sty = SCENARIO_STYLES[scen]
            ax.plot(proj["window_end_year"], proj["MSL5_perturbed"],
                    color=col, marker=sty["marker"], markersize=4,
                    markerfacecolor="white", markeredgecolor=col,
                    linestyle=sty["linestyle"], linewidth=sty["linewidth"],
                    alpha=sty["alpha"], label=sty["label"], zorder=4)
            # name the line at its right-hand end (2.0.0; Martin: "you cant tell which line is which")
            last = proj.dropna(subset=["MSL5_perturbed"])
            if len(last):
                last = last.sort_values("window_end_year").iloc[-1]
                ax.annotate(scen, (last["window_end_year"], last["MSL5_perturbed"]),
                            xytext=(5, 0), textcoords="offset points", va="center",
                            fontsize=7, color=col)

        # Curreli reference lines — drawn but only included in the y-range
        # if they're inside the observed envelope; otherwise the per-panel
        # auto-scale would zoom out to include them and lose the shift detail
        all_y = obs["MSL5_observed"].tolist()
        for scen in ["2050s", "2080s"]:
            p = projected_trajectories.get((cid, scen))
            if p is not None and len(p):
                all_y.extend(p["MSL5_perturbed"].dropna().tolist())
        y_min = float(min(all_y))
        y_max = float(max(all_y))
        y_range = y_max - y_min
        y_pad = max(0.05 * y_range, 0.02)
        y_lo = y_min - y_pad
        y_hi = y_max + y_pad
        # Conditionally include thresholds if they're within or close to range
        for thr in (-config.SD15b, -config.SD16):
            if y_lo - 0.05 < thr < y_hi + 0.05:
                pass  # already in range; line will be drawn
        ax.axhline(-config.SD15b, ls="--", color="#1a7a1a", lw=0.8,
                   alpha=0.7, zorder=2)
        ax.axhline(-config.SD16,  ls="--", color="#cc0000", lw=0.8,
                   alpha=0.7, zorder=2)
        ax.set_ylim(y_lo, y_hi)
        ax.set_xlim(right=float(obs["window_end_year"].max()) + 2.6)   # room for line names
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

        ax.set_xlabel("Hydrology year (window end)", fontsize=9)
        ax.set_ylabel("5-year MSL (m, below ground)", fontsize=9)
        if not any(projected_trajectories.get((cid, s_)) is not None
                   and projected_trajectories[(cid, s_)]["msl5_shift"].notna().any()
                   for s_ in ("2050s", "2080s")):
            ax.text(0.5, 0.94, "no projection: Model B β₃ not identified", transform=ax.transAxes,
                    ha="center", va="top", fontsize=8, color="#666")
        ax.set_title(f"{lbl}", fontsize=10)
        ax.grid(alpha=0.25)
        ax.tick_params(labelsize=8)

    # 6th panel: ΔMSL5 bar chart (replaces the legend cell)
    bar_ax = axes_flat[len(cluster_ids_present)]
    _render_bar_panel(bar_ax, projected_trajectories, cluster_ids_present)

    # Figure-level legend strip
    legend_handles = [
        plt.Line2D([0], [0], color="#444", marker="o", lw=1.8, markersize=4.5,
                   label="Observed (Script 26 cluster centroid)"),
        plt.Line2D([0], [0], color="#444", marker="s", lw=1.4, markersize=4,
                   markerfacecolor="white",
                   linestyle=SCENARIO_STYLES["2050s"]["linestyle"],
                   label="UKCP18 RCP8.5 2050s (central estimate)"),
        plt.Line2D([0], [0], color="#444", marker="^", lw=1.4, markersize=4,
                   markerfacecolor="white",
                   linestyle=SCENARIO_STYLES["2080s"]["linestyle"],
                   label="UKCP18 RCP8.5 2080s (central estimate)"),
        plt.Line2D([0], [0], color="#1a7a1a", lw=0.8, ls="--",
                   label=f"SD15b (−{config.SD15b:.2f} m, summer ref.)"),
        plt.Line2D([0], [0], color="#cc0000", lw=0.8, ls="--",
                   label=f"SD16 (−{config.SD16:.2f} m, summer ref.)"),
    ]
    fig.legend(handles=legend_handles, loc="upper center",
               bbox_to_anchor=(0.5, 0.945), ncol=5, fontsize=8,
               frameon=False, handlelength=4.5)

    fig.suptitle("Per-cluster MSL5 trajectory under UKCP18 RCP8.5 climate "
                 "scenarios\n"
                 "Cluster-centroid baseline (Script 26) shifted by the sustained level "
                 "response to each scenario (Model B SSM, D-216)",
                 fontsize=11, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    render_figure(fig, out_path)
    plt.close(fig)
    saved(f"{out_path.name}")

# ── v1.1.0 per-well aggregation pathway ──────────────────────────────────────
def compute_perwell_msl5_summary(
    monthly_P_m: np.ndarray,
    monthly_PET_m: np.ndarray,
    model_b_csv_path,
    out_csv_path,
) -> pd.DataFrame:
    """
    Per-cluster ΔMSL5 from PER-WELL Model B coefficients (2.0.0, D-216): each
    reference well's sustained spring level response to the scenario climatology,
    averaged within its cluster. The validation target for Script 19's ΔMSL5 row,
    which computes the same quantity with the same model_utils functions.

    1. Read the well rows of 03_16_model_b_persistence.csv (comparison window).
    2. Keep wells whose Model B β₃ passes Script 48's identifiability rule
       (model_utils.response_identified); the rest are counted as withheld.
    3. Per well: mean over config.MSL_SPRING_MONTHS of
       sustained_monthly_response(β₃, climate_forcing_change_12(...)) — pure
       climate, no canopy interception (the van Willegen convention).
    4. Cluster mean and median; a SITE row weighted by identified wells.
    """
    mb = pd.read_csv(model_b_csv_path)
    mb = mb[(mb["level"] == "well") & mb["beta_1_B"].notna() & mb["beta_3_B"].notna()]
    if mb.empty:
        warn("compute_perwell_msl5_summary: no wells with Model B coefficients")
        return pd.DataFrame()

    records = []
    print(f"  Per-well ΔMSL5 (Model B, sustained): {len(mb)} wells across "
          f"{mb['Cluster'].nunique()} clusters")
    for scen_key in ["2050s", "2080s"]:
        sP, sPET = _monthly_multipliers(scen_key)
        per_well = []
        for _, w in mb.iterrows():
            ok, _ef, _rse = response_identified(w["beta_3_B"], w["pvalue_beta_3_B"],
                                                w["n"], MODEL_B_N_PARAMS)
            shift = np.nan
            if ok:
                dF12 = climate_forcing_change_12(w["beta_1_B"], w["beta_2_B"],
                                                 monthly_P_m, monthly_PET_m, sP, sPET)
                shift = float(np.mean(sustained_monthly_response(w["beta_3_B"], dF12)[SPRING_IDX]))
            per_well.append((int(w["Cluster"]), shift))

        total, site_sum = 0, 0.0
        for cid in sorted(config.CLUSTER_LABELS.keys()):
            vals = [v for c, v in per_well if c == cid]
            if not vals:
                continue
            ok_vals = [v for v in vals if np.isfinite(v)]
            mean_ = float(np.mean(ok_vals)) if ok_vals else np.nan
            records.append({
                "cluster_id": cid, "cluster_label": config.CLUSTER_LABELS[cid],
                "scenario": scen_key,
                "msl5_shift_sustained_mean_m": mean_,
                "msl5_shift_sustained_median_m": float(np.median(ok_vals)) if ok_vals else np.nan,
                "n_wells": len(ok_vals), "n_withheld_not_identified": len(vals) - len(ok_vals),
                "model": "B", "aggregation": "perwell",
            })
            if ok_vals:
                total += len(ok_vals); site_sum += mean_ * len(ok_vals)
            print(f"    {scen_key}  C{cid}: n={len(ok_vals):2d} (+{len(vals) - len(ok_vals)} withheld)  "
                  f"ΔMSL5 = {mean_:+.4f} m")
        if total:
            records.append({
                "cluster_id": None, "cluster_label": "SITE", "scenario": scen_key,
                "msl5_shift_sustained_mean_m": site_sum / total,
                "msl5_shift_sustained_median_m": np.nan,
                "n_wells": total, "n_withheld_not_identified": np.nan,
                "model": "B", "aggregation": "perwell",
            })

    out_df = pd.DataFrame(records)
    out_df.to_csv(out_csv_path, index=False)
    saved(f"{out_csv_path.name}")
    return out_df

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    banner("26b", "van Willegen MSL Scenarios", version=__version__)
    print("=" * 72)
    print("Script 26b — UKCP18 MSL5 climate projections (Tool B)")
    print("=" * 72)
    print()
    print("  Method: sustained level response (Model B SSM, D-216) over the observed climate")
    print("  Convention: van Willegen 2025 5-year MSL (window-ends from "
          "Script 26)")
    print("  Scenarios: UKCP18 RCP8.5 Wales 50th %ile — 2050s and 2080s")
    print()

    # ── Load inputs ──────────────────────────────────────────────────────────
    # Model B centroids drive the projection (2.0.0, D-216); Model A's published
    # coefficients feed only the one-month-rate diagnostic column.
    mb_all = pd.read_csv(paths.OUT_03_MODEL_B_PERSISTENCE)
    coeffs = mb_all[mb_all["level"] == "centroid"].copy()
    print(f"  {paths.OUT_03_MODEL_B_PERSISTENCE.name:<48s} : {len(coeffs)} Model B centroids")
    coeffs_a = pd.read_csv(paths.OUT_03_MECHANISTIC_TABLE).set_index("Cluster")
    print(f"  {paths.OUT_03_MECHANISTIC_TABLE.name:<48s} : {len(coeffs_a)} clusters (diagnostic)")

    climate = pd.read_csv(paths.INT_CLIMATE)
    climate["Date"] = pd.to_datetime(climate["Date"])
    climate = climate.set_index("Date").sort_index()
    print(f"  {paths.INT_CLIMATE.name:<48s} : {len(climate)} monthly rows")

    observed_cluster = pd.read_csv(paths.OUT_26_5YR_PER_CLUSTER_CENTROID)
    print(f"  {paths.OUT_26_5YR_PER_CLUSTER_CENTROID.name:<48s} : "
          f"{len(observed_cluster)} (cluster, end_year) rows")

    # ── Climatology over the monitoring period ───────────────────────────────
    # Use the cluster-aligned climate window (matches Script 21's clim slice).
    clim_window = climate.loc["2005-04-01":config.REFERENCE_CUTOFF_DATE].copy()
    monthly_P   = clim_window.groupby(clim_window.index.month)["P_m"].mean()
    # In 01_climate.csv PET is in m (per Script 03 convention).
    monthly_PET = clim_window.groupby(clim_window.index.month)["PET"].mean()
    # Ensure 12-element arrays indexed 1..12, in calendar order
    monthly_P_m   = np.array([monthly_P.get(m, 0.0)   for m in range(1, 13)])
    monthly_PET_m = np.array([monthly_PET.get(m, 0.0) for m in range(1, 13)])

    print()
    print(f"  Monthly P climatology mean ({clim_window.index.min().year}-"
          f"{clim_window.index.max().year}): "
          f"{monthly_P_m.mean()*1000:.1f} mm/month")
    print(f"  Monthly PET climatology mean: "
          f"{monthly_PET_m.mean()*1000:.1f} mm/month")
    print()

    # ── Compute monthly Δh per cluster per scenario ──────────────────────────
    delta_h_records = []
    summary_records = []
    projected_trajectories: dict[tuple[int, str], pd.DataFrame] = {}
    observed_trajectories: dict[int, pd.DataFrame] = {}

    for _, row in coeffs.iterrows():
        cid = int(row["Cluster"])

        b1 = float(row["beta_1_B"])
        b2 = float(row["beta_2_B"])
        b3 = float(row["beta_3_B"])
        ident, efold, rel_se = response_identified(b3, row["pvalue_beta_3_B"], row["n"],
                                                   MODEL_B_N_PARAMS)
        a1 = float(coeffs_a.loc[cid, "beta_1_recharge"])
        a2 = float(coeffs_a.loc[cid, "beta_2_atmospheric_draw"])

        # Observed MSL5 trajectory for this cluster (from Script 26)
        obs = observed_cluster[observed_cluster["cluster_id"] == cid].copy()
        if obs.empty:
            warn(f"no observed MSL5 trajectory for cluster {cid}")
            continue
        obs_traj = (obs[["window_end_year", "MSL5_m_bg_centroid"]]
                    .rename(columns={"MSL5_m_bg_centroid": "MSL5_observed"})
                    .sort_values("window_end_year")
                    .reset_index(drop=True))
        observed_trajectories[cid] = obs_traj

        print(f"  Cluster {cid} ({row['Cluster_Label']}):")
        print(f"    Model B  β₁ = {b1:.4f}   β₂ = {b2:.4f}   β₃ = {b3:.4f}   "
              f"e-fold {efold:.1f} mo, rel SE {rel_se:.2f}"
              + ("" if ident else "   -> NOT identified: withheld"))

        # For each scenario, compute the 12-month Δh array and project
        for scen_key in ["2050s", "2080s"]:
            sP, sPET = _monthly_multipliers(scen_key)
            dF12 = climate_forcing_change_12(b1, b2, monthly_P_m, monthly_PET_m, sP, sPET)
            ss12 = sustained_monthly_response(b3, dF12) if 0.0 < b3 < 1.0 else np.full(12, np.nan)
            rate_a = _compute_monthly_delta_h(a1, a2, monthly_P_m, monthly_PET_m, sP, sPET)
            for m_idx in range(12):
                delta_h_records.append({
                    "cluster_id": cid,
                    "cluster_label": row["Cluster_Label"],
                    "scenario": scen_key,
                    "calendar_month": m_idx + 1,
                    "forcing_change_m_per_month": float(dF12[m_idx]),
                    "level_shift_sustained_m": float(ss12[m_idx]) if ident else np.nan,
                    "one_month_rate_model_a_m_per_month": float(rate_a[m_idx]),
                    "sP": float(sP[m_idx]),
                    "sPET": float(sPET[m_idx]),
                })

            if ident:
                by_year, sustained = _spring_shift_by_year(
                    b1, b2, b3, clim_window, sP, sPET, monthly_P_m, monthly_PET_m)
                traj = _compute_projected_msl5_trajectory(obs_traj, by_year)
            else:
                sustained = np.nan
                traj = obs_traj.assign(MSL5_perturbed=np.nan, msl5_shift=np.nan)[
                    ["window_end_year", "MSL5_perturbed", "msl5_shift"]]
            projected_trajectories[(cid, scen_key)] = traj
            mean_shift = float(traj["msl5_shift"].mean()) if ident else np.nan
            rate_a_spring = float(np.mean(rate_a[SPRING_IDX]))
            print(f"    {scen_key}: ΔMSL5 mean over windows = {mean_shift:+.3f} m "
                  f"(sustained {sustained:+.3f} m; one-month Model A rate "
                  f"{rate_a_spring:+.4f} m/month)")

            summary_records.append({
                "cluster_id":            cid,
                "cluster_label":         row["Cluster_Label"],
                "scenario":              scen_key,
                "model":                 "B",
                "beta_1_recharge":       b1,
                "beta_2_atmospheric_draw": b2,
                "beta_3_drainage":       b3,
                "efold_months":          efold,
                "rel_se_beta_3":         rel_se,
                "identified":            bool(ident),
                "msl5_observed_window_mean_m": float(obs_traj["MSL5_observed"].mean()),
                "msl5_perturbed_window_mean_m": float(traj["MSL5_perturbed"].mean()) if ident else np.nan,
                "msl5_shift_mean_m":     mean_shift,
                "msl5_shift_min_m":      float(traj["msl5_shift"].min()) if ident else np.nan,
                "msl5_shift_max_m":      float(traj["msl5_shift"].max()) if ident else np.nan,
                "msl5_shift_sustained_m": sustained,
                "spring_one_month_rate_model_a_m": rate_a_spring,
                "n_common_window_ends":  int(len(traj)),
            })
        print()

    # ── Persist outputs ──────────────────────────────────────────────────────
    pd.DataFrame(summary_records).to_csv(OUT_TABLE, index=False)
    saved(f"{OUT_TABLE.name}")
    pd.DataFrame(delta_h_records).to_csv(OUT_DELTAS, index=False)
    saved(f"{OUT_DELTAS.name}")

    # T-91: committed report-numbers trace for the Methods Supplement S.18b.3
    # sentence quoting per-cluster/scenario MSL5 shifts (e.g. "Main Forest
    # (C4) has the largest shift"). Computed from summary_records already in
    # memory (no re-read of OUT_TABLE).
    from utils.report_numbers_utils import ReportNumbers
    rpt = ReportNumbers()
    _sdf = pd.DataFrame(summary_records)
    for _, rec in _sdf.iterrows():
        _lab = str(rec["cluster_label"]).lower().replace(" ", "_").replace("(", "").replace(")", "")
        if not rec["identified"]:
            continue
        rpt.add(f"msl5_shift_mean_m_{_lab}_{rec['scenario']}", rec["msl5_shift_mean_m"],
                unit="m", well=str(rec["cluster_label"]), era=str(rec["scenario"]),
                note="Mean over window-ends of the MSL5 shift: sustained level response, Model B "
                     "(D-216; 26b_msl5_ukcp18_projection_summary.csv, msl5_shift_mean_m).")
        rpt.add(f"msl5_shift_sustained_m_{_lab}_{rec['scenario']}", rec["msl5_shift_sustained_m"],
                unit="m", well=str(rec["cluster_label"]), era=str(rec["scenario"]),
                note="Sustained spring level response to the scenario climatology, Model B (D-216).")
    _wh = _sdf.loc[~_sdf["identified"], "cluster_label"].drop_duplicates()
    rpt.add("msl5_projection_n_clusters_withheld", float(len(_wh)), unit="count",
            note="clusters whose Model B beta_3 fails Script 48's identifiability rule and are "
                 "not projected: " + (", ".join(_wh) or "none"))
    for _scen, _g in _sdf[_sdf["identified"]].groupby("scenario"):
        _imax = _g["msl5_shift_mean_m"].abs().idxmax()
        _row = _g.loc[_imax]
        rpt.add(f"msl5_shift_largest_cluster_{_scen}", str(_row["cluster_label"]),
                unit="", era=str(_scen),
                note="Cluster with the largest-magnitude msl5_shift_mean_m for this scenario.")
    rpt.save(paths.OUT_26B_REPORT_NUMBERS)
    saved(f"{paths.OUT_26B_REPORT_NUMBERS.name}")

    # ── v1.1.0 per-well-aggregation pathway ──────────────────────────────────
    # Secondary artefact, independent of the centroid pathway above.  Serves
    # as the validation target for the Script 19 v2.8.0 viewer ΔMSL5 row.
    # See docstring on compute_perwell_msl5_summary for the full rationale.
    print()
    print("  Per-well aggregation pathway (v1.1.0):")
    compute_perwell_msl5_summary(
        monthly_P_m=monthly_P_m,
        monthly_PET_m=monthly_PET_m,
        model_b_csv_path=paths.OUT_03_MODEL_B_PERSISTENCE,
        out_csv_path=OUT_TABLE_PERWELL,
    )

    # ── Figure ───────────────────────────────────────────────────────────────
    render_projection_figure(observed_trajectories, projected_trajectories,
                              OUT_FIG)

    # ── Transcript ───────────────────────────────────────────────────────────
    with OUT_TXT.open("w") as fh:
        fh.write("Script 26b — UKCP18 MSL5 climate projections\n")
        fh.write("=" * 60 + "\n\n")
        fh.write("Method (2.0.0, D-216): sustained level response, Model B SSM.\n")
        fh.write("Δf(t) = β₁·P(t)·(sP−1) − β₂·PET(t)·(sPET−1);  d(t) = (1−β₃)·d(t−1) + Δf(t)\n")
        fh.write("Spring = config.MSL_SPRING_MONTHS (D-189).\n\n")
        fh.write("This is NOT a forward time projection. The trajectories\n")
        fh.write("show what observed MSL5 over 2014–2025 would have been\n")
        fh.write("under each UKCP18 scenario's perturbed climatology.\n\n")
        fh.write("Per-cluster results:\n")
        fh.write("-" * 60 + "\n")
        for rec in summary_records:
            fh.write(f"Cluster {rec['cluster_id']} ({rec['cluster_label']})  "
                     f"{rec['scenario']}:\n")
            fh.write(f"  Model B β₁ = {rec['beta_1_recharge']:.4f}   "
                     f"β₂ = {rec['beta_2_atmospheric_draw']:.4f}   "
                     f"β₃ = {rec['beta_3_drainage']:.4f}   identified: {rec['identified']}\n")
            fh.write(f"  Sustained spring shift:       "
                     f"{rec['msl5_shift_sustained_m']:+.3f} m\n")
            fh.write(f"  Observed window MSL5 mean:    "
                     f"{rec['msl5_observed_window_mean_m']:+.3f} m\n")
            fh.write(f"  Perturbed window MSL5 mean:   "
                     f"{rec['msl5_perturbed_window_mean_m']:+.3f} m\n")
            fh.write(f"  Mean shift:                   "
                     f"{rec['msl5_shift_mean_m']:+.3f} m  "
                     f"(over {rec['n_common_window_ends']} "
                     f"common window-ends)\n\n")
    saved(f"{OUT_TXT.name}")
    print()
    done()
    return 0

if __name__ == "__main__":
    sys.exit(main())
