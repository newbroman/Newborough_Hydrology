#!/usr/bin/env python3
"""
14_climate_projections.py
--------------------------------------------------------------------------
Produces climate trajectory projection figures for Newborough Warren.

Reads observed data from 03_regional_averages.csv, fits OLS linear
regressions to annual summer minima for all five clusters (C1–C5),
and plots observed winter maxima against ecohydrological flooding
thresholds (Curreli et al. 2013).

Outputs:
    outputs/14_climate_projections/14_climate_trajectory_summer.png
    outputs/14_climate_projections/14_climate_trajectory_winter_flooding.png
    outputs/14_climate_projections/14_climate_trajectory_stacked.png

Reviewer-facing method summary:
    - Summer panel: observed annual summer minima with OLS trend and 95% CI
      for all five clusters (C1 Lake Edge, C2 Dune, C3 Western Residual,
      C4 Main Forest, C5 Coastal Forest).
    - Winter panel: observed annual winter maxima only (no projection), with
      threshold exceedance frequencies shown in an annotation box.
"""

from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — last revised 2026-04-26

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

_SRC = Path(__file__).resolve().parent
if not (_SRC / "utils").is_dir():
    _SRC = _SRC.parent / "src"
sys.path.insert(0, str(_SRC))

from utils.paths import (
    INT_REGIONAL_AVG, DIR_14,
    OUT_14_CLIMATE_STACKED, OUT_14_CLIMATE_SUMMER, OUT_14_CLIMATE_WINTER,
    OUT_14_SUMMER_TREND_CSV, OUT_14_ANNUAL_EXTREMES, OUT_14_WINTER_EXCEED,
    OUT_14_SEASONAL_SCATTER,
    OUT_00_WELL_NETWORK_TABLE, INT_CLUSTER_STATS,
    make_all_dirs,
)
from utils.config import (
    CLUSTER_LABELS as _CFG_LABELS,
    CLUSTER_COLOURS as _CFG_COLOURS,
    CLUSTER_MARKERS as _CFG_MARKERS,
    SD15b, SD16, SD15b_WINTER, SD16_WINTER,
)

OBS_START = 2004
OBS_END = 2025
PROJ_END = 2040
YEAR_MIN = 2000
YEAR_MAX = 2045
SUMMER_MONTHS = [4, 5, 6, 7, 8, 9]
WINTER_MONTHS = [10, 11, 12, 1, 2, 3]
MIN_MONTHS = 3

# Curreli et al. (2013) eco-hydrological thresholds (negative = below ground)
# Canonical positive-down values imported from config; negated here for
# script 14's depth-axis sign convention.
WET_SLACK_SUMMER = -SD15b          # m  SD15b summer viability limit
DRY_SLACK_SUMMER = -SD16           # m  SD16 summer viability limit
WET_SLACK_WINTER = -SD15b_WINTER   # m  SD15b winter flooding threshold
DRY_SLACK_WINTER = -SD16_WINTER    # m  SD16 winter flooding threshold

# ── Cluster styling — single source of truth in utils.config ─────────────────
# String-keyed adapters because this script consumes the 'C{n}' column
# convention from 03_regional_averages.csv. Update utils.config to change.
CLUSTER_COLOURS: dict[str, str] = {f"C{cid}": v for cid, v in _CFG_COLOURS.items()}
CLUSTER_LABELS:  dict[str, str] = {f"C{cid}": v for cid, v in _CFG_LABELS.items()}
CLUSTER_MARKERS: dict[str, str] = {f"C{cid}": v for cid, v in _CFG_MARKERS.items()}

# Clusters that get fitted trajectory trends in the summer/winter figures.
# All five clusters under the k=5 partition. C4 and C5 (forested) are
# included for completeness — future management may alter their canopy.
TRAJECTORY_CLUSTERS: tuple[str, ...] = ("C1", "C2", "C3", "C4", "C5")


def _compute_winter_exceedance(filepath: Path) -> dict:
    """
    Compute winter wet-slack and dry-slack exceedance counts from observed
    cluster centroid data. Uses hydrological year (Oct 1 – Sep 30).

    Returns dict {cluster: {"wet": n_wet, "dry": n_dry, "n": n_years}}.
    """
    df = pd.read_csv(filepath, index_col="Date", parse_dates=True).sort_index()
    df["hydro_year"] = df.index.year + (df.index.month >= 10).astype(int)
    df = df[(df.index.year >= OBS_START) & (df.index.year <= OBS_END)]

    result = {}
    for c in TRAJECTORY_CLUSTERS:
        if c not in df.columns:
            continue
        wet_count = 0
        dry_count = 0
        n_years = 0
        for year, grp in df.groupby("hydro_year"):
            winter = grp[grp.index.month.isin(WINTER_MONTHS)][c].dropna()
            if len(winter) < MIN_MONTHS:
                continue
            n_years += 1
            wmax = winter.max()
            if wmax >= WET_SLACK_WINTER:
                wet_count += 1
            if wmax >= DRY_SLACK_WINTER:
                dry_count += 1
        result[c] = {"wet": wet_count, "dry": dry_count, "n": n_years}
    return result


def build_winter_exceedance_text(exceedance: dict) -> str:
    """Create a stable, reviewer-readable summary string for the inset box."""
    lines = ["Wet slack flooding frequency (SD15b threshold):"]
    for c in TRAJECTORY_CLUSTERS:
        stats_c = exceedance.get(c)
        if stats_c is None:
            continue
        pct_wet = int(round(100 * stats_c["wet"] / stats_c["n"]))
        lines.append(
            f"  {CLUSTER_LABELS[c]:<30} {stats_c['wet']:>2} / {stats_c['n']:<2} years  ({pct_wet:>2}%)"
        )
    return "\n".join(lines)


def add_winter_background(ax: plt.Axes) -> None:
    """Add winter threshold zones and reference lines shared by both figures."""
    ax.axhspan(0.10, WET_SLACK_WINTER, alpha=0.06, color="#1a7a1a", zorder=0)
    ax.axhspan(WET_SLACK_WINTER, DRY_SLACK_WINTER, alpha=0.06, color="#ff9900", zorder=0)
    ax.axhspan(DRY_SLACK_WINTER, -1.35, alpha=0.04, color="#cc0000", zorder=0)

    ax.axhline(0.00, color="#aaaaaa", linewidth=0.8, linestyle=":", zorder=2)
    ax.text(
        YEAR_MIN + 0.5,
        0.005,
        "Ground Surface (0.00 m)",
        color="#999999",
        fontsize=7.5,
        va="bottom",
        zorder=7,
    )
    ax.axhline(
        WET_SLACK_WINTER,
        color="#1a7a1a",
        linewidth=1.4,
        linestyle="--",
        zorder=3,
        label=f"Wet slack winter limit SD15b ({WET_SLACK_WINTER} m)",
    )
    ax.axhline(
        DRY_SLACK_WINTER,
        color="#7a3e00",
        linewidth=1.4,
        linestyle="--",
        zorder=3,
        label=f"Dry slack winter limit SD16 ({DRY_SLACK_WINTER} m)",
    )
    ax.axvspan(2030, 2039, color="#888888", alpha=0.07, zorder=1, label="2030s intervention window")


def add_winter_exceedance_box(ax: plt.Axes, exceedance: dict) -> None:
    """Render the standardized exceedance frequency inset."""
    ax.text(
        0.99,
        0.97,
        build_winter_exceedance_text(exceedance),
        transform=ax.transAxes,
        fontsize=8.0,
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="#cccccc", alpha=0.92),
        va="top",
        ha="right",
        zorder=9,
    )

def load_annual_extremes(filepath: Path) -> tuple[dict, dict]:
    """
    Load 03_regional_averages.csv and extract annual summer minima and
    winter maxima per cluster.

    Returns data for ALL clusters present in CLUSTER_COLOURS (so all five
    under the current k=5 partition); the caller then chooses which subset
    to fit trajectories for via TRAJECTORY_CLUSTERS.

    Returns
    -------
    summer_min : dict  {cluster: pd.Series(hydro_year -> min)}
    winter_max : dict  {cluster: pd.Series(hydro_year -> max)}
    """
    df = pd.read_csv(filepath, index_col="Date", parse_dates=True).sort_index()
    df["hydro_year"] = df.index.year + (df.index.month >= 10).astype(int)
    df = df[(df.index.year >= OBS_START) & (df.index.year <= OBS_END)]

    summer_min = {c: {} for c in CLUSTER_COLOURS}
    winter_max = {c: {} for c in CLUSTER_COLOURS}

    for year, grp in df.groupby("hydro_year"):
        for c in CLUSTER_COLOURS:
            if c not in df.columns:
                continue
            summer = grp[grp.index.month.isin(SUMMER_MONTHS)][c].dropna()
            winter = grp[grp.index.month.isin(WINTER_MONTHS)][c].dropna()
            if len(summer) >= MIN_MONTHS:
                summer_min[c][year] = summer.min()
            if len(winter) >= MIN_MONTHS:
                winter_max[c][year] = winter.max()

    return (
        {c: pd.Series(v).sort_index() for c, v in summer_min.items()},
        {c: pd.Series(v).sort_index() for c, v in winter_max.items()},
    )


def fit_trend(years: np.ndarray, values: np.ndarray, proj_end: int = PROJ_END):
    """
    Fit OLS linear regression and return projection arrays with 95% CI.

    Returns
    -------
    years_proj  : np.ndarray  — continuous year array from first obs to proj_end
    trend_proj  : np.ndarray  — fitted trend values over years_proj
    ci_upper    : np.ndarray  — 95% CI upper bound
    ci_lower    : np.ndarray  — 95% CI lower bound
    slope       : float
    intercept   : float
    r2          : float
    """
    slope, intercept, r, p_value, _ = stats.linregress(years, values)
    years_proj = np.linspace(years[0], proj_end, 500)
    trend_proj = intercept + slope * years_proj

    # Confidence interval for fitted mean response
    n = len(years)
    x_bar = np.mean(years)
    ss_xx = np.sum((years - x_bar) ** 2)
    s_e = np.sqrt(np.sum((values - (intercept + slope * years)) ** 2) / (n - 2))
    t_star = stats.t.ppf(0.975, df=n - 2)
    se_fit = s_e * np.sqrt(1.0 / n + (years_proj - x_bar) ** 2 / ss_xx)
    ci_upper = trend_proj + t_star * se_fit
    ci_lower = trend_proj - t_star * se_fit

    r2 = r ** 2
    return years_proj, trend_proj, ci_upper, ci_lower, slope, intercept, r2, p_value



def render_summer_figure(
    summer_data: dict,
    out_path: Path,
) -> None:
    """
    summer_data: {cluster: (years_obs, values_obs, years_proj, trend_proj,
                             ci_upper, ci_lower, slope, r2, p_value)}
                 — all TRAJECTORY_CLUSTERS get an entry here.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Threshold bands
    ax.axhspan(WET_SLACK_SUMMER, 0.10, alpha=0.06, color="#1155aa", zorder=0)
    ax.axhspan(DRY_SLACK_SUMMER, WET_SLACK_SUMMER, alpha=0.06, color="#ff9900", zorder=0)
    ax.axhspan(-2.10, DRY_SLACK_SUMMER, alpha=0.04, color="#cc0000", zorder=0)

    for c, (yobs, vobs, yproj, tproj, cu, cl, slope, *_extra) in summer_data.items():
        colour = CLUSTER_COLOURS[c]
        label = CLUSTER_LABELS[c]
        marker = CLUSTER_MARKERS.get(c, "o")
        ax.fill_between(yproj, cu, cl, color=colour, alpha=0.10, linewidth=0, zorder=2)
        ax.plot(
            yproj,
            tproj,
            color=colour,
            linewidth=2.0,
            solid_capstyle="round",
            zorder=4,
            label=f"{label}  (trend {slope:+.4f} m yr\u207b\xb9)",
        )
        ax.scatter(yobs, vobs, color=colour, marker=marker, s=30, zorder=5, alpha=0.85)

    # Threshold lines
    ax.axhline(
        WET_SLACK_SUMMER,
        color="#1155aa",
        linewidth=1.4,
        linestyle="--",
        zorder=3,
        label=f"Wet slack summer limit SD15b ({WET_SLACK_SUMMER} m)",
    )
    ax.axhline(
        DRY_SLACK_SUMMER,
        color="#7a3e00",
        linewidth=1.4,
        linestyle="--",
        zorder=3,
        label=f"Dry slack summer limit SD16 ({DRY_SLACK_SUMMER} m)",
    )

    # Intervention window
    ax.axvspan(2030, 2039, color="#cc3333", alpha=0.07, zorder=1, label="Critical intervention window (2030\u20132039)")

    # Threshold annotations
    ax.text(
        YEAR_MIN + 0.5,
        WET_SLACK_SUMMER + 0.025,
        "Wet slack viability limit (SD15b)",
        color="#1155aa",
        fontsize=7.8,
        va="bottom",
        zorder=7,
    )
    ax.text(
        YEAR_MIN + 0.5,
        DRY_SLACK_SUMMER + 0.025,
        "Dry slack viability limit (SD16)",
        color="#7a3e00",
        fontsize=7.8,
        va="bottom",
        zorder=7,
    )

    ax.set_xlim(YEAR_MIN, YEAR_MAX)
    ax.set_ylim(-2.10, 0.10)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Summer Minimum Water Table Depth (m)", fontsize=11)
    ax.set_title(
        "Projected Summer Minimum Trajectory vs Ecological Thresholds: Newborough Warren",
        fontsize=12,
        pad=10,
    )
    ax.yaxis.grid(True, color="#eaeaea", linewidth=0.5, linestyle="-", zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="best", fontsize=8.2, frameon=True, framealpha=0.92, edgecolor="#cccccc", ncol=1)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  [14] Saved: {out_path.name}")


def render_winter_figure(
    winter_data: dict,
    out_path: Path,
    exceedance: dict,
) -> None:
    """
    Plot observed annual winter maxima for all trajectory clusters against
    ecological flooding thresholds. No projection lines — the figure presents
    the observed flooding record and annotates threshold exceedance
    frequencies directly.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    add_winter_background(ax)

    # Observed scatter per cluster
    for c, (yobs, vobs) in winter_data.items():
        colour = CLUSTER_COLOURS[c]
        marker = CLUSTER_MARKERS.get(c, "o")
        ax.scatter(
            yobs,
            vobs,
            color=colour,
            marker=marker,
            s=30,
            zorder=5,
            alpha=0.85,
            label=CLUSTER_LABELS[c],
        )
        # Mean and median horizontal lines
        mean_val   = np.mean(vobs)
        median_val = np.median(vobs)
        x_start = min(yobs) - 0.3
        x_end   = max(yobs) + 0.3
        ax.plot([x_start, x_end], [mean_val,   mean_val],
                color=colour, linewidth=1.2, linestyle="--",
                alpha=0.75, zorder=4)
        ax.plot([x_start, x_end], [median_val, median_val],
                color=colour, linewidth=1.0, linestyle=":",
                alpha=0.75, zorder=4)
        ax.annotate(
            f"  μ={mean_val:.2f}",
            xy=(x_end, mean_val), fontsize=6.5,
            color=colour, va="center", zorder=5,
        )
        ax.annotate(
            f"  ø={median_val:.2f}",
            xy=(x_end, median_val), fontsize=6.5,
            color=colour, va="center", zorder=5,
        )

        # C5 has a significant winter declining trend (p=0.035) — show it
        if c == "C5":
            from scipy import stats as _st
            w_slope, w_int, w_r, w_p, _ = _st.linregress(yobs, vobs)
            if w_p < 0.05:
                yr_line = np.array([min(yobs), max(yobs)])
                ax.plot(yr_line, w_slope * yr_line + w_int,
                        color=colour, linewidth=2.0, linestyle="-",
                        alpha=0.85, zorder=6)

    add_winter_exceedance_box(ax, exceedance)

    ax.set_xlim(YEAR_MIN, YEAR_MAX)
    ax.set_ylim(-1.35, 0.25)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Winter Maximum Water Table Depth (m)", fontsize=11)
    ax.set_title(
        "(B) Observed Winter Maximum Water Table vs Flooding Thresholds",
        fontsize=12,
        pad=10,
    )
    ax.yaxis.grid(True, color="#eaeaea", linewidth=0.5, linestyle="-", zorder=0)
    ax.set_axisbelow(True)
    # Add mean/median legend entries
    from matplotlib.lines import Line2D as _L2D
    extra_handles = [
        _L2D([0], [0], color="grey", linewidth=1.2, linestyle="--", label="Cluster mean"),
        _L2D([0], [0], color="grey", linewidth=1.0, linestyle=":",  label="Cluster median"),
    ]
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles + extra_handles,
              loc="lower right", fontsize=8.2, frameon=True, framealpha=0.92, edgecolor="#cccccc")

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  [14] Saved: {out_path.name}")


def render_stacked_figure(
    summer_data: dict,
    winter_data: dict,
    out_path: Path,
    exceedance: dict,
) -> None:
    """
    Two-panel stacked figure (summer trajectory above, winter observed below).
    """
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(12, 11), sharex=True)
    fig.patch.set_facecolor("white")

    # --- Top panel: summer ---
    ax_top.set_facecolor("white")
    ax_top.axhspan(WET_SLACK_SUMMER, 0.10, alpha=0.06, color="#1155aa", zorder=0)
    ax_top.axhspan(DRY_SLACK_SUMMER, WET_SLACK_SUMMER, alpha=0.06, color="#ff9900", zorder=0)
    ax_top.axhspan(-2.10, DRY_SLACK_SUMMER, alpha=0.04, color="#cc0000", zorder=0)

    for c, (yobs, vobs, yproj, tproj, cu, cl, slope, *_extra) in summer_data.items():
        colour = CLUSTER_COLOURS[c]
        label = CLUSTER_LABELS[c]
        marker = CLUSTER_MARKERS.get(c, "o")
        ax_top.fill_between(yproj, cu, cl, color=colour, alpha=0.10, linewidth=0, zorder=2)
        ax_top.plot(
            yproj,
            tproj,
            color=colour,
            linewidth=2.0,
            solid_capstyle="round",
            zorder=4,
            label=f"{label}  (trend {slope:+.4f} m yr\u207b\xb9)",
        )
        ax_top.scatter(yobs, vobs, color=colour, marker=marker, s=30, zorder=5, alpha=0.85)

    ax_top.axhline(
        WET_SLACK_SUMMER,
        color="#1155aa",
        linewidth=1.4,
        linestyle="--",
        zorder=3,
        label=f"Wet slack summer limit SD15b ({WET_SLACK_SUMMER} m)",
    )
    ax_top.axhline(
        DRY_SLACK_SUMMER,
        color="#7a3e00",
        linewidth=1.4,
        linestyle="--",
        zorder=3,
        label=f"Dry slack summer limit SD16 ({DRY_SLACK_SUMMER} m)",
    )
    ax_top.axvspan(2030, 2039, color="#cc3333", alpha=0.07, zorder=1, label="Critical intervention window (2030\u20132039)")
    ax_top.set_xlim(YEAR_MIN, YEAR_MAX)
    ax_top.set_ylim(-2.10, 0.10)
    ax_top.set_ylabel("Summer Minimum Depth (m)", fontsize=11)
    ax_top.set_title("(A) Summer Minimum Trajectory vs Ecological Thresholds", fontsize=12, pad=10)
    ax_top.yaxis.grid(True, color="#eaeaea", linewidth=0.5, zorder=0)
    ax_top.set_axisbelow(True)
    ax_top.legend(loc="best", fontsize=8.0, frameon=True, framealpha=0.92, edgecolor="#cccccc")

    # --- Bottom panel: winter ---
    ax_bot.set_facecolor("white")
    add_winter_background(ax_bot)

    for c, (yobs, vobs) in winter_data.items():
        colour = CLUSTER_COLOURS[c]
        marker = CLUSTER_MARKERS.get(c, "o")
        ax_bot.scatter(
            yobs,
            vobs,
            color=colour,
            marker=marker,
            s=30,
            zorder=5,
            alpha=0.85,
            label=CLUSTER_LABELS[c],
        )
        # Mean and median horizontal lines
        mean_val   = np.mean(vobs)
        median_val = np.median(vobs)
        x_start = min(yobs) - 0.3
        x_end   = max(yobs) + 0.3
        ax_bot.plot([x_start, x_end], [mean_val,   mean_val],
                    color=colour, linewidth=1.2, linestyle="--",
                    alpha=0.75, zorder=4)
        ax_bot.plot([x_start, x_end], [median_val, median_val],
                    color=colour, linewidth=1.0, linestyle=":",
                    alpha=0.75, zorder=4)
        ax_bot.annotate(
            f"  μ={mean_val:.2f}",
            xy=(x_end, mean_val), fontsize=6.5,
            color=colour, va="center", zorder=5,
        )
        ax_bot.annotate(
            f"  ø={median_val:.2f}",
            xy=(x_end, median_val), fontsize=6.5,
            color=colour, va="center", zorder=5,
        )

        # C5 has a significant winter declining trend (p=0.035) — show it
        if c == "C5":
            from scipy import stats as _st
            w_slope, w_int, w_r, w_p, _ = _st.linregress(yobs, vobs)
            if w_p < 0.05:
                yr_line = np.array([min(yobs), max(yobs)])
                ax_bot.plot(yr_line, w_slope * yr_line + w_int,
                            color=colour, linewidth=2.0, linestyle="-",
                            alpha=0.85, zorder=6)

    add_winter_exceedance_box(ax_bot, exceedance)

    ax_bot.set_xlim(YEAR_MIN, YEAR_MAX)
    ax_bot.set_ylim(-1.35, 0.25)
    ax_bot.set_xlabel("Year", fontsize=11)
    ax_bot.set_ylabel("Winter Maximum Depth (m)", fontsize=11)
    ax_bot.set_title("(B) Observed Winter Maximum Water Table vs Flooding Thresholds", fontsize=12, pad=10)
    ax_bot.yaxis.grid(True, color="#eaeaea", linewidth=0.5, zorder=0)
    ax_bot.set_axisbelow(True)
    # Add mean/median legend entries
    from matplotlib.lines import Line2D as _L2D
    extra_handles = [
        _L2D([0], [0], color="grey", linewidth=1.2, linestyle="--", label="Cluster mean"),
        _L2D([0], [0], color="grey", linewidth=1.0, linestyle=":",  label="Cluster median"),
    ]
    handles, labels = ax_bot.get_legend_handles_labels()
    ax_bot.legend(handles=handles + extra_handles,
                  loc="lower right", fontsize=8.0, frameon=True, framealpha=0.92, edgecolor="#cccccc")

    fig.suptitle(
        "Projected Climate Trajectory vs Ecological/Flooding Thresholds: Newborough Warren",
        fontsize=13,
        y=0.985,
    )

    plt.tight_layout(rect=[0, 0.015, 1, 0.97])
    plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  [14] Saved: {out_path.name}")


def main() -> None:
    make_all_dirs()
    print("\n[14] Loading observed data and fitting summer trends per cluster...")

    summer_min, winter_max = load_annual_extremes(INT_REGIONAL_AVG)

    # Compute winter exceedance from observed data (replaces old hardcoded dict)
    winter_exceedance = _compute_winter_exceedance(INT_REGIONAL_AVG)
    for c in TRAJECTORY_CLUSTERS:
        if c in winter_exceedance:
            exc = winter_exceedance[c]
            pct = int(round(100 * exc["wet"] / exc["n"])) if exc["n"] > 0 else 0
            print(f"  {c} winter exceedance: wet={exc['wet']}/{exc['n']} ({pct}%), "
                  f"dry={exc['dry']}/{exc['n']}")

    summer_data = {}
    winter_data = {}

    for c in TRAJECTORY_CLUSTERS:
        # Summer — fit trend
        if c in summer_min and len(summer_min[c]) >= 5:
            s_years = summer_min[c].index.to_numpy(dtype=float)
            s_vals = summer_min[c].values
            s_yp, s_tp, s_cu, s_cl, s_slope, _, s_r2, s_pval = fit_trend(s_years, s_vals)
            print(
                f"  {c} summer trend: {s_slope:+.4f} m yr\u207b\xb9  "
                f"(R\u00b2={s_r2:.3f}, p={s_pval:.4f}, n={len(s_years)})"
            )
            summer_data[c] = (s_years, s_vals, s_yp, s_tp, s_cu, s_cl, s_slope, s_r2, s_pval)

        # Winter — observed only, no projection
        if c in winter_max and len(winter_max[c]) >= 5:
            w_years = winter_max[c].index.to_numpy(dtype=float)
            w_vals = winter_max[c].values
            w_slope, _, w_r, _, _ = stats.linregress(w_years, w_vals)
            print(
                f"  {c} winter observed trend (descriptive only): "
                f"{w_slope:+.4f} m yr\u207b\xb9  (R\u00b2={w_r**2:.3f})"
            )
            winter_data[c] = (w_years, w_vals)

    render_summer_figure(summer_data, OUT_14_CLIMATE_SUMMER)
    render_winter_figure(winter_data, OUT_14_CLIMATE_WINTER,
                         exceedance=winter_exceedance)
    render_stacked_figure(summer_data, winter_data, OUT_14_CLIMATE_STACKED,
                          exceedance=winter_exceedance)

    # ── Export summer trend stats and annual extremes to CSV ─────────────────

    # Summer trend summary
    trend_rows = []
    for c in TRAJECTORY_CLUSTERS:
        if c in summer_data:
            yobs, vobs, *_, s_slope, s_r2, s_pval = summer_data[c]
            trend_rows.append({
                "Cluster": c,
                "Label": CLUSTER_LABELS[c],
                "n_years": len(yobs),
                "Slope_m_per_yr": round(s_slope, 4),
                "R2": round(s_r2, 3),
                "p_value": round(s_pval, 4),
            })
    pd.DataFrame(trend_rows).to_csv(OUT_14_SUMMER_TREND_CSV, index=False)
    print(f"  -> Saved: 14_summer_trend_stats.csv")

    # Annual summer minima and winter maxima
    annual_rows = []
    for c in TRAJECTORY_CLUSTERS:
        if c in summer_min:
            for yr, val in summer_min[c].items():
                annual_rows.append({"Cluster": c, "HydroYear": yr, "Season": "Summer_Min", "Value_m": round(val, 4)})
        if c in winter_max:
            for yr, val in winter_max[c].items():
                annual_rows.append({"Cluster": c, "HydroYear": yr, "Season": "Winter_Max", "Value_m": round(val, 4)})
    pd.DataFrame(annual_rows).to_csv(OUT_14_ANNUAL_EXTREMES, index=False)
    print(f"  -> Saved: 14_annual_extremes.csv")

    # Winter exceedance summary
    exc_rows = []
    for c, stats_c in winter_exceedance.items():
        exc_rows.append({
            "Cluster": c,
            "Wet_Slack_Exceedances": stats_c["wet"],
            "Dry_Slack_Exceedances": stats_c["dry"],
            "n_years": stats_c["n"],
            "Wet_Slack_Pct": round(100 * stats_c["wet"] / stats_c["n"], 1),
        })
    pd.DataFrame(exc_rows).to_csv(OUT_14_WINTER_EXCEED, index=False)
    print(f"  -> Saved: 14_winter_exceedance.csv")


    # Seasonal extremes scatter plot (interactive HTML)
    render_seasonal_scatter(OUT_14_SEASONAL_SCATTER)
    print("\n[14] Climate projection figures complete.\n")



# Cluster colours and labels for the seasonal-extremes scatter — same source
# as the trajectory dicts (utils.config). Under the k=5 partition the legacy
# 'C5/C6 Boundary' grey aliases have been retired; ceh3 etc. (boundary wells)
# get their nearest-cluster label from INT_CLUSTER_STATS (or fall through to
# UNKNOWN if the audit didn't reach them).
_SCATTER_COLOURS: dict[str, str] = {f"C{cid}": v for cid, v in _CFG_COLOURS.items()}
_SCATTER_LABELS:  dict[str, str] = {f"C{cid}": v for cid, v in _CFG_LABELS.items()}

# Fallback styling for wells whose cluster cannot be resolved from
# INT_CLUSTER_STATS (e.g. extended-network wells outside the audit, or
# wells that legitimately don't belong to any canonical cluster).
_SCATTER_UNKNOWN_KEY    = "UNKNOWN"
_SCATTER_UNKNOWN_COLOUR = "#888780"
_SCATTER_UNKNOWN_LABEL  = "Unassigned"


def render_seasonal_scatter(out_html: Path) -> None:
    """
    Produce an interactive HTML scatter plot of mean annual summer minimum
    vs mean annual winter maximum water table depth, coloured by cluster,
    with Curreli et al. (2013) ecological threshold lines overlaid.

    Reads:
        OUT_00_WELL_NETWORK_TABLE  — per-well Mean_Summer_Min_m, Mean_Winter_Max_m
        INT_CLUSTER_STATS          — per-well cluster assignment
    """
    import json

    # Load well network summary (requires updated script 00 with new columns)
    try:
        net = pd.read_csv(OUT_00_WELL_NETWORK_TABLE)
    except FileNotFoundError:
        print(f"  [14] Warning: well network table not found — skipping scatter plot")
        return

    if "Mean_Summer_Min_m" not in net.columns:
        print(f"  [14] Warning: Mean_Summer_Min_m column missing from well network table")
        print(f"       Run updated script 00 first to generate these columns.")
        return

    # Load cluster assignments. INT_CLUSTER_STATS has columns Match_ID,
    # Name_Original, Cluster (integer), Cluster_Label. We want the integer
    # so we can convert to the canonical 'C{n}' string used by the styling
    # dicts; we don't trust Cluster_Label because it's a free-text field.
    try:
        clusters = pd.read_csv(INT_CLUSTER_STATS)
        # Pick the well-name column. Match_ID is preferred (it's the
        # canonical key); fall back to Name_Original or any column literally
        # named 'well'.
        well_col_candidates = ["Match_ID", "Name_Original", "Well", "Name", "Well_ID"]
        well_col = next(
            (c for c in well_col_candidates if c in clusters.columns), None
        )
        if well_col is None:
            raise IndexError("no recognised well-name column in cluster stats")
        if "Cluster" not in clusters.columns:
            raise IndexError("'Cluster' column missing from cluster stats")
        clusters["Well_norm"] = clusters[well_col].astype(str).str.strip().str.lower()
        # Coerce Cluster to integer, then format as 'C{n}'. NaN / unparseable
        # values become None and skip the map (well falls through to UNKNOWN).
        cluster_int = pd.to_numeric(clusters["Cluster"], errors="coerce")
        cluster_str = cluster_int.apply(
            lambda v: f"C{int(v)}" if pd.notna(v) else None
        )
        cluster_map = dict(zip(clusters["Well_norm"], cluster_str))
        # Drop any None entries so .map() returns NaN and .fillna() can flag them
        cluster_map = {k: v for k, v in cluster_map.items() if v is not None}
    except (FileNotFoundError, IndexError) as e:
        print(f"  [14] Warning: cluster stats not loadable ({e}) — "
              f"all wells will be marked UNKNOWN")
        cluster_map = {}

    net["Well_norm"] = net["Well"].astype(str).str.strip().str.lower()
    # Wells without a cluster assignment fall through to UNKNOWN — explicit
    # rather than silently coerced to a real cluster (the previous code
    # defaulted to C2 which would mis-attribute boundary / unaudited wells
    # into the Eastern Block Mature Dune cluster).
    net["Cluster"] = net["Well_norm"].map(cluster_map).fillna(_SCATTER_UNKNOWN_KEY)

    # Build point data for JS
    points = []
    for _, row in net.iterrows():
        s = row.get("Mean_Summer_Min_m")
        w = row.get("Mean_Winter_Max_m")
        if pd.isna(s) or pd.isna(w):
            continue
        c = str(row["Cluster"])
        if c == _SCATTER_UNKNOWN_KEY:
            label  = _SCATTER_UNKNOWN_LABEL
            colour = _SCATTER_UNKNOWN_COLOUR
        else:
            label  = _SCATTER_LABELS.get(c, c)
            colour = _SCATTER_COLOURS.get(c, _SCATTER_UNKNOWN_COLOUR)
        points.append({
            "well": str(row["Well"]),
            "summer_min": round(float(s), 3),
            "winter_max": round(float(w), 3),
            "cluster": c,
            "label": label,
            "color": colour,
        })

    # Build legend entries (unique clusters present)
    seen = {}
    for p in points:
        if p["cluster"] not in seen:
            seen[p["cluster"]] = {"label": p["label"], "color": p["color"]}
    legend_items = [{"cluster": k, **v} for k, v in sorted(seen.items())]

    points_json = json.dumps(points)
    legend_json = json.dumps(legend_items)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Seasonal extremes — Newborough Warren well network</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; margin: 20px; background: #fff; color: #333; }}
  h2 {{ font-size: 14px; font-weight: 500; margin-bottom: 4px; }}
  p.caption {{ font-size: 11px; color: #666; margin-top: 6px; max-width: 740px; }}
  #legend {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px; font-size: 12px; }}
  #legend span {{ display: flex; align-items: center; gap: 5px; }}
  #legend .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  #search-row {{ display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }}
  #search-row input {{ font-size: 13px; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; width: 260px; }}
  #search-row button {{ font-size: 12px; padding: 4px 10px; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; background: #f5f5f5; }}
  #searchResult {{ font-size: 12px; color: #555; }}
  #chart-wrap {{ position: relative; width: 100%; max-width: 740px; height: 460px; }}
</style>
</head>
<body>
<h2>Mean annual summer minimum vs winter maximum water table depth — Newborough Warren 2005–2026</h2>
<div id="legend"></div>
<div id="search-row">
  <input type="text" id="wellSearch" placeholder="Search well e.g. CEH36, NW10...">
  <button onclick="clearSearch()">Clear</button>
  <span id="searchResult"></span>
</div>
<div id="chart-wrap">
  <canvas id="chart" role="img"
    aria-label="Scatter plot of mean annual summer minimum versus winter maximum water table depth for the reference well network, coloured by hydrogeological cluster, with Curreli et al. ecological threshold lines.">
    Wells plotted by summer minimum depth (x-axis) and winter maximum depth (y-axis), coloured by hydrogeological cluster.
  </canvas>
</div>
<p class="caption">
  Dashed lines: Curreli et al. (2013) eco-hydrological thresholds.
  SD15b wet slack: summer minimum &gt; {WET_SLACK_SUMMER} m (vertical green dashed), winter maximum &gt; {WET_SLACK_WINTER} m (horizontal green dashed).
  SD16 dry slack: summer minimum &gt; {DRY_SLACK_SUMMER} m (vertical red dashed), winter maximum &gt; {DRY_SLACK_WINTER} m (horizontal red dashed).
  Hover over any point to see well name and values. Use the search box to highlight a specific well.
  Generated by 14_climate_projections.py (Hollingham, 2026).
</p>
<script>
const allWells = {points_json};
const legendItems = {legend_json};

const clusterColors = {{}};
legendItems.forEach(item => {{ clusterColors[item.cluster] = item.color; }});

const legendDiv = document.getElementById('legend');
legendItems.forEach(item => {{
  const span = document.createElement('span');
  span.innerHTML = '<span class="dot" style="background:' + item.color + '"></span>' + item.label;
  legendDiv.appendChild(span);
}});

function buildDatasets(highlight) {{
  const byCluster = {{}};
  allWells.forEach(d => {{
    if (!byCluster[d.cluster]) byCluster[d.cluster] = [];
    byCluster[d.cluster].push(d);
  }});
  return Object.entries(byCluster).map(([c, pts]) => ({{
    label: c,
    data: pts.map(d => ({{ x: d.summer_min, y: d.winter_max, well: d.well }})),
    backgroundColor: pts.map(d => {{
      if (!highlight) return d.color + 'CC';
      return d.well.toLowerCase() === highlight ? '#ff6600' : d.color + '33';
    }}),
    borderColor: pts.map(d => {{
      if (!highlight) return d.color;
      return d.well.toLowerCase() === highlight ? '#cc4400' : d.color + '33';
    }}),
    borderWidth: 1.5,
    pointRadius: pts.map(d => (highlight && d.well.toLowerCase() === highlight) ? 13 : 6),
    pointHoverRadius: 9,
  }}));
}}

const thresholdPlugin = {{
  id: 'thresholds',
  afterDraw(chart) {{
    const {{ctx, scales:{{x, y}}}} = chart;
    [{WET_SLACK_SUMMER}, {DRY_SLACK_SUMMER}].forEach((val, i) => {{
      const color = i === 0 ? '#1a7a1a' : '#cc0000';
      ctx.save(); ctx.beginPath();
      ctx.strokeStyle = color; ctx.lineWidth = 1.3;
      ctx.setLineDash([6,3]); ctx.globalAlpha = 0.75;
      const px = x.getPixelForValue(val);
      ctx.moveTo(px, y.top); ctx.lineTo(px, y.bottom);
      ctx.stroke(); ctx.restore();
    }});
    [{WET_SLACK_WINTER}, {DRY_SLACK_WINTER}].forEach((val, i) => {{
      const color = i === 0 ? '#1a7a1a' : '#cc0000';
      ctx.save(); ctx.beginPath();
      ctx.strokeStyle = color; ctx.lineWidth = 1.3;
      ctx.setLineDash([4,4]); ctx.globalAlpha = 0.75;
      const py = y.getPixelForValue(val);
      ctx.moveTo(x.left, py); ctx.lineTo(x.right, py);
      ctx.stroke(); ctx.restore();
    }});
  }}
}};

const chart = new Chart(document.getElementById('chart'), {{
  type: 'scatter',
  data: {{ datasets: buildDatasets(null) }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          label: item => item.raw.well.toUpperCase() + ': summer ' + item.raw.x.toFixed(2) + ' m, winter ' + item.raw.y.toFixed(2) + ' m'
        }}
      }}
    }},
    scales: {{
      x: {{ title: {{display:true, text:'Mean annual summer minimum (m below pipe top)', font:{{size:12}}}}, min:-2.6, max:0.65, ticks:{{callback: v => v.toFixed(1)}} }},
      y: {{ title: {{display:true, text:'Mean annual winter maximum (m below pipe top)', font:{{size:12}}}}, min:-2.2, max:0.65, ticks:{{callback: v => v.toFixed(1)}} }}
    }}
  }},
  plugins: [thresholdPlugin]
}});

document.getElementById('wellSearch').addEventListener('input', function() {{
  const term = this.value.trim().toLowerCase();
  if (!term) {{ clearSearch(); return; }}
  const match = allWells.find(d => d.well.toLowerCase().includes(term));
  const resultEl = document.getElementById('searchResult');
  if (match) {{
    chart.data.datasets = buildDatasets(match.well.toLowerCase());
    chart.update();
    resultEl.style.color = '#333';
    resultEl.textContent = match.well.toUpperCase() + ' — summer min: ' + match.summer_min.toFixed(2) + ' m, winter max: ' + match.winter_max.toFixed(2) + ' m (' + match.cluster + ')';
  }} else {{
    chart.data.datasets = buildDatasets(null);
    chart.update();
    resultEl.style.color = '#888';
    resultEl.textContent = 'No match found';
  }}
}});

function clearSearch() {{
  document.getElementById('wellSearch').value = '';
  document.getElementById('searchResult').textContent = '';
  chart.data.datasets = buildDatasets(null);
  chart.update();
}}
</script>
</body>
</html>"""

    out_html.write_text(html, encoding="utf-8")
    print(f"  [14] Saved: {out_html.name}")


if __name__ == "__main__":
    main()
