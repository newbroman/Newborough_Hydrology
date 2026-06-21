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

Method
------
Monthly Δh perturbation pattern (Script 21 / model_utils convention).
For each cluster and each scenario:

    Δh_shift(m) = β₁·(P_scen(m) − P_base(m)) − β₂·(PET_scen(m) − PET_base(m))

where β₁ and β₂ are the cluster's SSM coefficients (Script 03), and
P_scen(m) = P_base(m) · sP(m), PET_scen(m) = PET_base(m) · sPET(m).

The UKCP18 multipliers sP / sPET are seasonal (Nov-Mar winter window;
May-Sep summer window; April and October as shoulder months get the mean
of the two). The full UKCP18 RCP8.5 Wales 50th-percentile central
estimates from Script 19's SCENARIO_PARAMS dict drive each scenario:

    2050s:   P_winter ×1.10   P_summer ×0.85   PET_winter ×1.05   PET_summer ×1.20
    2080s:   P_winter ×1.20   P_summer ×0.70   PET_winter ×1.10   PET_summer ×1.35

Because the perturbation is linear in P and PET and the multipliers are
constant year-on-year (climatology shift, not interannual sequence), the
resulting MSL5 shift is a single constant per cluster per scenario:

    ΔMSL5 = mean(Δh_Mar, Δh_Apr, Δh_May)

The projected MSL5 trajectory is therefore the observed Script 26
trajectory shifted down by this constant. The figure shows the
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

__version__ = "1.1.0"  # Hollingham (2026) — 2026-05-27
# 1.1.0 — Parallel per-well aggregation pathway added.  The centroid-fitted
#         pathway and all its outputs (figure, OUT_TABLE, OUT_DELTAS,
#         OUT_TXT) are unchanged byte-for-byte; this version adds a second
#         routine, compute_perwell_msl5_summary(), which iterates over the
#         66 per-well β coefficients in 03_master_data.csv (the same file
#         Script 19 reads), applies the same canonical pure-climate
#         perturbation formula
#               Δh(m) = β₁·P(m)·(sP(m)−1) − β₂·PET(m)·(sPET(m)−1)
#         per well, takes the spring (Mar/Apr/May) mean, then aggregates
#         to a cluster mean weighted by well count.  Writes a second
#         summary CSV (OUT_26B_PROJECTION_TABLE_PERWELL) with the same
#         schema as the centroid table plus per-well count.
#
#         This serves two purposes.  First, it gives the Script 19 v2.8.0
#         viewer ΔMSL5 row a defined validation target that matches the
#         viewer's own well-mean β aggregation (the centroid-fitted
#         summary differs from this by 0.5–2 mm per cluster per scenario
#         because cluster-centroid OLS and per-well OLS averaged are not
#         algebraically equivalent — both valid summaries, just different
#         aggregations of the same SSM).  Second, it makes the per-well
#         lineage a documented project artefact alongside the centroid
#         lineage, so any future report decision on aggregation choice has
#         both CSVs to compare against.
#
#         The centroid table remains the primary output and the basis for
#         Script 26c, §3.7.5, §4.8.4 and §4.10.1 numbers in the report.
#         Per Martin (2026-05-27 chat) the per-well pathway is an
#         additional artefact, not a replacement.
#
#         No upstream consumer of 26b's existing outputs is affected.
__version__previous__ = "1.0.2"  # Hollingham (2026) — 2026-05-20
# 1.0.2 — Figure rework. Per-panel auto-scaled y-axis (the 1-4 cm Δh shift
#         was invisible on the shared ~1.8 m y-range used in v1.0.0/1.0.1).
#         Replaced the cell-6 legend with a ΔMSL5 bar chart (cm units,
#         coloured by cluster, hatched for 2080s vs solid 2050s) which is
#         the canonical magnitude view for a constant per-cluster shift.
#         Per-panel ΔMSL5 annotation boxes removed (now redundant with the
#         bar panel). Legend moved to a horizontal strip below the suptitle.
#         No change to the underlying numbers or output CSVs.
__version__previous__ = "1.0.1"  # Hollingham (2026) — 2026-05-20
# 1.0.1 — Switch baseline trajectory from Method A (per-well aggregation) to
#         Method B (cluster centroid from 03_regional_averages.csv) to be
#         internally consistent with the SSM β coefficients driving the
#         perturbation. Both baselines are produced by Script 26 v1.1.2;
#         this script now reads OUT_26_5YR_PER_CLUSTER_CENTROID rather than
#         OUT_26_5YR_PER_CLUSTER. Δh shift magnitudes are unchanged (linear
#         perturbation), only absolute MSL5 levels in the figure differ.
#         Figure title and legend updated to make the Method-B baseline
#         transparent.
__version__previous__ = "1.0.0"  # Hollingham (2026) — 2026-05-20
# 1.0.0 — Initial implementation. Tool B of the MSL forecasting pair, paired
#         with Script 11 Section 5 (Tool A, v1.1.1). Single-step monthly Δh
#         perturbation pattern (Script 21 method) applied to UKCP18 RCP8.5
#         2050s and 2080s multipliers. Produces a 5-panel small-multiple
#         figure (one panel per cluster) showing observed MSL5 trajectory
#         alongside the two scenario-perturbed equivalents, plus a summary
#         CSV with the projected vs observed MSL5 means per cluster per
#         scenario.

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
UKCP18_SCENARIOS = {
    "2050s": {"sP_w": 1.10, "sP_s": 0.85, "sPET_w": 1.05, "sPET_s": 1.20},
    "2080s": {"sP_w": 1.20, "sP_s": 0.70, "sPET_w": 1.10, "sPET_s": 1.35},
}

SCENARIO_STYLES = {
    "2050s": {"linestyle": (0, (4, 2)),       "linewidth": 1.4, "alpha": 0.85,
              "label": "UKCP18 RCP8.5 2050s (50th %ile)"},
    "2080s": {"linestyle": (0, (1.5, 1.5)),   "linewidth": 1.4, "alpha": 0.85,
              "label": "UKCP18 RCP8.5 2080s (50th %ile)"},
}

WINTER_MONTHS = [11, 12, 1, 2, 3]
SUMMER_MONTHS = [5, 6, 7, 8, 9]
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


def _compute_projected_msl5_trajectory(
        observed_traj: pd.DataFrame,
        delta_h: np.ndarray,
) -> pd.DataFrame:
    """
    Apply the per-month Δh perturbation to the observed MSL5 trajectory.

    Because the perturbation is linear in P and PET and the multipliers
    are constant year-on-year (UKCP18 climatology shift, not an
    interannual sequence), the resulting MSL5 shift is a constant per
    cluster per scenario equal to the mean of the spring Δh values:

        ΔMSL5 = mean(Δh_Mar, Δh_Apr, Δh_May)

    The projected trajectory is therefore the observed trajectory shifted
    down by this constant. This keeps the figure's observed line
    byte-identical to Script 26's published trajectory; the scenario lines
    are vertical translations.

    Parameters
    ----------
    observed_traj : pd.DataFrame
        From Script 26's 26_msl_5yr_per_cluster.csv subset for one cluster,
        columns: window_end_year, MSL5_observed.
    delta_h : np.ndarray, length 12
        Monthly Δh shifts (m), indexed 0=Jan ... 11=Dec.

    Returns
    -------
    pd.DataFrame with columns: window_end_year, MSL5_perturbed, msl5_shift.
    """
    # Spring (Mar, Apr, May) Δh values — calendar indices 2, 3, 4
    msl5_shift = float(np.mean(delta_h[[2, 3, 4]]))

    out = observed_traj.copy()
    out["MSL5_perturbed"] = out["MSL5_observed"] + msl5_shift
    out["msl5_shift"] = msl5_shift
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
        bars_2050.append(float(p50["msl5_shift"].iloc[0]) * 100.0
                         if p50 is not None and len(p50) else 0.0)
        bars_2080.append(float(p80["msl5_shift"].iloc[0]) * 100.0
                         if p80 is not None and len(p80) else 0.0)

    # Colour each bar by its cluster
    colours = [config.CLUSTER_COLOURS.get(cid, "#444")
               for cid in cluster_ids_present]
    ax.bar(x - width / 2, bars_2050, width=width, color=colours,
           edgecolor="black", linewidth=0.5,
           label="UKCP18 RCP8.5 2050s")
    ax.bar(x + width / 2, bars_2080, width=width, color=colours,
           edgecolor="black", linewidth=0.5, hatch="//",
           label="UKCP18 RCP8.5 2080s")

    # Numeric labels at the bar ends
    for xi, v in zip(x - width / 2, bars_2050):
        ax.text(xi, v - 0.1, f"{v:+.1f}", ha="center", va="top",
                fontsize=7.5, color="#222")
    for xi, v in zip(x + width / 2, bars_2080):
        ax.text(xi, v - 0.1, f"{v:+.1f}", ha="center", va="top",
                fontsize=7.5, color="#222")

    ax.set_xticks(x)
    ax.set_xticklabels(cluster_labels, fontsize=9)
    ax.set_ylabel("Projected ΔMSL5 (cm)", fontsize=9)
    ax.set_title("Projected ΔMSL5 by cluster and scenario", fontsize=10)
    ax.axhline(0, color="#333", lw=0.5)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(labelsize=8)
    # Floor the y-axis a bit below the deepest bar so the labels don't clip
    y_lo = min(bars_2080) - 1.0
    ax.set_ylim(y_lo, 0.5)


def render_projection_figure(
        observed_trajectories: dict[int, pd.DataFrame],
        projected_trajectories: dict[tuple[int, str], pd.DataFrame],
        out_path: Path,
) -> None:
    """
    Render the projection figure as a 2x3 small-multiple layout:
      • 5 trajectory panels (one per cluster), per-panel auto-scaled y-axis
        so the 1-4 cm scenario shift is visible at the panel's own scale
      • 1 summary bar chart (bottom-right) showing ΔMSL5 per cluster ×
        scenario in centimetres

    A figure-level horizontal legend strip sits below the suptitle.

    Visual note. The Δh perturbation is small (1-4 cm) and constant per
    cluster per scenario. On a panel with ~50 cm of inter-year variability
    in MSL5, three trajectories drawn from the same dataset offset by 1 cm
    are visually indistinguishable. Per-panel auto-scaling raises the
    apparent shift; the bar chart provides the canonical magnitude view.
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

        for scen in ["2050s", "2080s"]:
            proj = projected_trajectories.get((cid, scen))
            if proj is None or proj.empty:
                continue
            sty = SCENARIO_STYLES[scen]
            ax.plot(proj["window_end_year"], proj["MSL5_perturbed"],
                    color=col, marker="s", markersize=3.5,
                    linestyle=sty["linestyle"], linewidth=sty["linewidth"],
                    alpha=sty["alpha"], label=sty["label"], zorder=4)

        # Curreli reference lines — drawn but only included in the y-range
        # if they're inside the observed envelope; otherwise the per-panel
        # auto-scale would zoom out to include them and lose the shift detail
        all_y = obs["MSL5_observed"].tolist()
        for scen in ["2050s", "2080s"]:
            p = projected_trajectories.get((cid, scen))
            if p is not None and len(p):
                all_y.extend(p["MSL5_perturbed"].tolist())
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

        ax.set_xlabel("Hydrology year (window end)", fontsize=9)
        ax.set_ylabel("5-year MSL (m, below ground)", fontsize=9)
        ax.set_title(f"{lbl}", fontsize=10)
        ax.grid(alpha=0.25)
        ax.tick_params(labelsize=8)

    # 6th panel: ΔMSL5 bar chart (replaces the legend cell)
    bar_ax = axes_flat[len(cluster_ids_present)]
    _render_bar_panel(bar_ax, projected_trajectories, cluster_ids_present)

    # Figure-level legend strip
    legend_handles = [
        plt.Line2D([0], [0], color="#444", marker="o", lw=1.8, markersize=4.5,
                   label="Observed (Method B baseline, Script 26 v1.1.2)"),
        plt.Line2D([0], [0], color="#444", marker="s", lw=1.4, markersize=3.5,
                   linestyle=SCENARIO_STYLES["2050s"]["linestyle"],
                   label="UKCP18 RCP8.5 2050s (central estimate)"),
        plt.Line2D([0], [0], color="#444", marker="s", lw=1.4, markersize=3.5,
                   linestyle=SCENARIO_STYLES["2080s"]["linestyle"],
                   label="UKCP18 RCP8.5 2080s (central estimate)"),
        plt.Line2D([0], [0], color="#1a7a1a", lw=0.8, ls="--",
                   label=f"SD15b (−{config.SD15b:.2f} m, summer ref.)"),
        plt.Line2D([0], [0], color="#cc0000", lw=0.8, ls="--",
                   label=f"SD16 (−{config.SD16:.2f} m, summer ref.)"),
    ]
    fig.legend(handles=legend_handles, loc="upper center",
               bbox_to_anchor=(0.5, 0.945), ncol=5, fontsize=8,
               frameon=False)

    fig.suptitle("Per-cluster MSL5 trajectory under UKCP18 RCP8.5 climate "
                 "scenarios\n"
                 "Cluster-centroid baseline (Method B, Script 26 v1.1.2) "
                 "overlaid with monthly Δh perturbation from each scenario",
                 fontsize=11, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    saved(f"{out_path.name}")


# ── v1.1.0 per-well aggregation pathway ──────────────────────────────────────
def compute_perwell_msl5_summary(
    monthly_P_m: np.ndarray,
    monthly_PET_m: np.ndarray,
    master_csv_path,
    out_csv_path,
) -> pd.DataFrame:
    """
    Compute per-cluster ΔMSL5 under each UKCP18 scenario using **per-well
    β coefficients** averaged within each cluster, rather than the
    cluster-centroid β used by the main pathway.

    Algorithm
    ---------
    1. Read 03_master_data.csv (the same file Script 19 reads).
    2. For each well with non-null β₁, compute the 12-month Δh array using
       the same pure-climate formulation as _compute_monthly_delta_h.
    3. Take the spring (Mar/Apr/May) mean → per-well ΔMSL5.
    4. Aggregate to cluster mean (simple mean over the wells in each
       cluster); a SITE-level row is the well-count-weighted mean across
       all clusters.

    The output CSV schema mirrors the centroid summary but adds an
    n_wells column and replaces the centroid-fitted β columns with the
    per-cluster mean of the per-well β.  An additional row per scenario
    aggregates to a SITE level (well-count weighted).

    Notes
    -----
    - Forest interception is **not** applied (this is the canonical
      pure-climate perturbation, matching the centroid pathway exactly).
    - Wells with null β₁ are silently skipped, matching Script 19's
      `wt["b1"].notna()` filter.
    - The well-cluster assignment in 03_master_data.csv is set by Script
      03 from the same clustering output Script 19 uses for its
      cluster-stats join, so the per-cluster well populations are
      byte-identical between Script 19 and this function.
    - This routine is independent of the centroid pathway: it does not
      mutate any state used elsewhere in main(), and the centroid
      OUT_TABLE / OUT_DELTAS / OUT_FIG remain unchanged.

    Returns the DataFrame written to out_csv_path.
    """
    md = pd.read_csv(master_csv_path)
    # Filter to wells with valid β₁ (matches Script 19 build_well_table)
    md = md[md["beta_1_recharge"].notna() & md["beta_2_atmospheric_draw"].notna()]
    if md.empty:
        warn("compute_perwell_msl5_summary: no wells with valid β")
        return pd.DataFrame()

    cluster_labels_map = {1: "C1 (Lake Edge)", 2: "C2 (Dune)",
                          3: "C3 (Western Residual)", 4: "C4 (Main Forest)",
                          5: "C5 (Coastal Forest)"}

    records = []
    print(f"  Per-well ΔMSL5 aggregation: {len(md)} wells across "
          f"{md['Cluster'].nunique()} clusters")
    for scen_key in ["2050s", "2080s"]:
        sP, sPET = _monthly_multipliers(scen_key)

        # Compute per-well ΔMSL5
        well_msl5 = {}
        for _, well in md.iterrows():
            b1 = float(well["beta_1_recharge"])
            b2 = float(well["beta_2_atmospheric_draw"])
            delta_h = _compute_monthly_delta_h(
                b1, b2, monthly_P_m, monthly_PET_m, sP, sPET
            )
            well_msl5[well["Name_Original"]] = (
                int(well["Cluster"]),
                b1, b2,
                float(np.mean(delta_h[[2, 3, 4]])),     # spring mean
            )

        # Cluster aggregation
        total_wells = 0
        site_weighted_sum = 0.0
        for cid in sorted(cluster_labels_map.keys()):
            in_cluster = [(b1, b2, m) for (c, b1, b2, m) in well_msl5.values()
                          if c == cid]
            if not in_cluster:
                continue
            n_cl = len(in_cluster)
            mean_b1 = float(np.mean([b1 for b1, _, _ in in_cluster]))
            mean_b2 = float(np.mean([b2 for _, b2, _ in in_cluster]))
            mean_msl5 = float(np.mean([m for _, _, m in in_cluster]))
            median_msl5 = float(np.median([m for _, _, m in in_cluster]))
            records.append({
                "cluster_id":             cid,
                "cluster_label":          cluster_labels_map[cid],
                "scenario":               scen_key,
                "beta_1_recharge_mean":   mean_b1,
                "beta_2_atmospheric_draw_mean": mean_b2,
                "spring_delta_h_mean_m":  mean_msl5,
                "spring_delta_h_median_m": median_msl5,
                "n_wells":                n_cl,
                "aggregation":            "perwell",
            })
            total_wells += n_cl
            site_weighted_sum += mean_msl5 * n_cl
            print(f"    {scen_key}  C{cid}: n={n_cl:2d}  "
                  f"β₁̄={mean_b1:.4f}  β₂̄={mean_b2:.4f}  "
                  f"ΔMSL5 = {mean_msl5:+.4f} m")

        # SITE-level row (well-count weighted)
        if total_wells > 0:
            records.append({
                "cluster_id":             None,
                "cluster_label":          "SITE",
                "scenario":               scen_key,
                "beta_1_recharge_mean":   np.nan,
                "beta_2_atmospheric_draw_mean": np.nan,
                "spring_delta_h_mean_m":  site_weighted_sum / total_wells,
                "spring_delta_h_median_m": np.nan,
                "n_wells":                total_wells,
                "aggregation":            "perwell",
            })

    out_df = pd.DataFrame(records)
    out_df.to_csv(out_csv_path, index=False)
    saved(f"{out_csv_path.name}")
    return out_df


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    banner("26b", "van Willegen MSL Scenarios", version="1.1.0")
    print("=" * 72)
    print("Script 26b — UKCP18 MSL5 climate projections (Tool B)")
    print("=" * 72)
    print()
    print("  Method: monthly Δh perturbation overlay on observed climatology")
    print("  Convention: van Willegen 2025 5-year MSL (window-ends from "
          "Script 26)")
    print("  Scenarios: UKCP18 RCP8.5 Wales 50th %ile — 2050s and 2080s")
    print()

    # ── Load inputs ──────────────────────────────────────────────────────────
    coeffs = pd.read_csv(paths.OUT_03_MECHANISTIC_TABLE)
    print(f"  {paths.OUT_03_MECHANISTIC_TABLE.name:<48s} : {len(coeffs)} clusters")

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

        b1 = float(row["beta_1_recharge"])
        b2 = float(row["beta_2_atmospheric_draw"])
        b3 = float(row["beta_3_drainage"])

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
        print(f"    β₁ = {b1:.4f}   β₂ = {b2:.4f}   β₃ = {b3:.4f}")

        # For each scenario, compute the 12-month Δh array and project
        for scen_key in ["2050s", "2080s"]:
            sP, sPET = _monthly_multipliers(scen_key)
            delta_h = _compute_monthly_delta_h(
                b1, b2, monthly_P_m, monthly_PET_m, sP, sPET
            )
            # Record per-month Δh for the deltas CSV
            for m_idx in range(12):
                delta_h_records.append({
                    "cluster_id": cid,
                    "cluster_label": row["Cluster_Label"],
                    "scenario": scen_key,
                    "calendar_month": m_idx + 1,
                    "delta_h_m": float(delta_h[m_idx]),
                    "sP": float(sP[m_idx]),
                    "sPET": float(sPET[m_idx]),
                })

            # Apply Δh as a vertical shift to the Script 26 observed
            # trajectory. The shift is constant per cluster per scenario
            # (mean of spring Δh values).
            traj = _compute_projected_msl5_trajectory(obs_traj, delta_h)
            projected_trajectories[(cid, scen_key)] = traj

            # Summary across all observed window-ends (the perturbed
            # trajectory is on the same window-end grid by construction)
            mean_shift = float(traj["msl5_shift"].iloc[0])
            spring_delta_h = float(np.mean(delta_h[[2, 3, 4]]))  # Mar/Apr/May
            print(f"    {scen_key}: spring Δh mean = "
                  f"{spring_delta_h:+.4f} m/month;  "
                  f"projected ΔMSL5 = {mean_shift:+.3f} m")

            summary_records.append({
                "cluster_id":            cid,
                "cluster_label":         row["Cluster_Label"],
                "scenario":              scen_key,
                "beta_1_recharge":       b1,
                "beta_2_atmospheric_draw": b2,
                "spring_delta_h_mean_m": spring_delta_h,
                "msl5_observed_window_mean_m": float(obs_traj["MSL5_observed"].mean()),
                "msl5_perturbed_window_mean_m": float(traj["MSL5_perturbed"].mean()),
                "msl5_shift_mean_m":     mean_shift,
                "n_common_window_ends":  int(len(traj)),
            })
        print()

    # ── Persist outputs ──────────────────────────────────────────────────────
    pd.DataFrame(summary_records).to_csv(OUT_TABLE, index=False)
    saved(f"{OUT_TABLE.name}")
    pd.DataFrame(delta_h_records).to_csv(OUT_DELTAS, index=False)
    saved(f"{OUT_DELTAS.name}")

    # ── v1.1.0 per-well-aggregation pathway ──────────────────────────────────
    # Secondary artefact, independent of the centroid pathway above.  Serves
    # as the validation target for the Script 19 v2.8.0 viewer ΔMSL5 row.
    # See docstring on compute_perwell_msl5_summary for the full rationale.
    print()
    print("  Per-well aggregation pathway (v1.1.0):")
    compute_perwell_msl5_summary(
        monthly_P_m=monthly_P_m,
        monthly_PET_m=monthly_PET_m,
        master_csv_path=paths.INT_MASTER_DATA,
        out_csv_path=OUT_TABLE_PERWELL,
    )

    # ── Figure ───────────────────────────────────────────────────────────────
    render_projection_figure(observed_trajectories, projected_trajectories,
                              OUT_FIG)

    # ── Transcript ───────────────────────────────────────────────────────────
    with OUT_TXT.open("w") as fh:
        fh.write("Script 26b — UKCP18 MSL5 climate projections\n")
        fh.write("=" * 60 + "\n\n")
        fh.write("Method: Monthly Δh perturbation overlay on observed "
                 "climatology.\n")
        fh.write("Δh(m) = β₁·(P_scen(m) − P_base(m)) − β₂·(PET_scen(m) − "
                 "PET_base(m))\n\n")
        fh.write("This is NOT a forward time projection. The trajectories\n")
        fh.write("show what observed MSL5 over 2014–2025 would have been\n")
        fh.write("under each UKCP18 scenario's perturbed climatology.\n\n")
        fh.write("Per-cluster results:\n")
        fh.write("-" * 60 + "\n")
        for rec in summary_records:
            fh.write(f"Cluster {rec['cluster_id']} ({rec['cluster_label']})  "
                     f"{rec['scenario']}:\n")
            fh.write(f"  β₁ = {rec['beta_1_recharge']:.4f}   "
                     f"β₂ = {rec['beta_2_atmospheric_draw']:.4f}\n")
            fh.write(f"  Spring Δh mean (Mar/Apr/May): "
                     f"{rec['spring_delta_h_mean_m']:+.4f} m/month\n")
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
