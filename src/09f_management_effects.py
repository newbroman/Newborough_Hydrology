r"""
====================================================================================
09f — MANAGEMENT EFFECTS: SPATIAL REACH + MAGNITUDE VS BACKGROUND DRIVERS
====================================================================================
Purpose
-------
A stacked two-panel synthesis figure for the academic summary (and, if wanted,
the §5.8/5.9 discussion). It makes points the per-site scenario charts (09d) and
cross-cluster chart (09b_05) do not show on their face:

  Panel (a) — SPATIAL REACH. Distance-decay of the interventions whose effects
  vary with distance: the dune-scrape drain (a dipole — local benefit at the
  slack, drawdown on the surrounding water table) and the standing/thinned
  forest canopy (a drawdown the canopy imposes, which clearfell would recover),
  both decaying over the leaky-aquifer length scale λ; plus the coastal-retreat
  drawdown (large at the shore, decaying to zero at the reach L). FIVE curves,
  and nothing spatially uniform: the panel is a distance-decay panel, and the
  only terms on it are terms that vary with distance. This is the 2026-07-02
  design; the flat climate line, the crossing and the far-field band that
  successively occupied that space are all withdrawn (D-043), because the
  quantity every one of them rested on is not separately identified (D-039).
  The distance axis runs to the fitted reach L, marked by the L rule — the
  reason it extends past the interventions' λ decay.
  The single measured off-site scrape point (WMC3) is anchored on the curve; the
  wider scrape and coastal fields are modelled scenarios.

  Panel (b) — DEVELOPMENT TIMESCALE. How long each driver takes to develop, on a
  dimensionless %-of-eventual-effect axis chosen so it COMPOSES with panel (a)
  (time-fraction × spatial-magnitude = head at a given time and distance; an mm
  axis would double-count the magnitude). Forest-ops relaxation band, a
  scrape/storm relaxation curve, and a coastal chronic-accumulation ramp, with
  the observed clearfell BACI step as the validation anchor.

All values are read LIVE from committed pipeline outputs, with documented
first-pass fallbacks (pipeline_params._DEFAULTS) so the figure runs on a
first-pass full-pipeline run and resolves to live values on the second pass.

Data sources (all on `main`)
----------------------------
  outputs/20_spatial_figures/20_report_numbers.csv
      — drawdown_lambda (λ) and drawdown_H0 (forest interception deficit at
        the felling edge), for the panel (a) forest and scrape decay curves.
  outputs/25_coastal_gradient/25_01_panel_fit_parameters.csv
      — delta_0_mm_yr, L_m (forest-free linear-capped fit) for the coastal
        curve and the reach-L rule. The fitted constant c is NOT read: it is
        not separately identified (D-039), and nothing on this figure stands
        in for it.
  outputs/09_scraping_intervention/09d_01_scenario_comparison.csv
      — scrape scenario context (on-site + off-site volumetric bars).
  outputs/10_clearfell_baci/10a_report_numbers.csv
      — measured clearfell BACI step (panel (a) r≈0 anchor; panel (b) anchor).
  outputs/10_clearfell_baci/10m_report_numbers.csv
      — WMC3_BACI_DiD_step_2015_scraping: the measured off-cut drawdown at the
        one evidenced off-site point (panel (a) WMC3 anchor).
  outputs/09_scraping_intervention/09b_01_individual_well_baci.csv
      — WMC3 dist_m (CEH36 → WMC3 separation) for the WMC3 anchor's x-position.
  outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv
      — forest/C3 β₃ (panel (b) relaxation half-lives).

Outputs
-------
  09f_management_effects.png        — two-panel figure (report / full)
  09f_management_effects_public.png — public/academic-summary variant (--public)
  09f_01_reach_profile.csv          — panel (a) curve values (traceability):
                                      one column per drawn curve, no more.

Not an SSM-fitting script: it reads equilibrium outputs and does not call
fit_ssm(). No new physics; a re-presentation of existing modelled + measured
fields.

References
----------
Hollingham (2026), §4.5, §4.6.3, §4.9.3, §4.8.2, §5.4.1, §5.4.3, §5.8.
Companion to 09b/09d. PROJECT_NOTE scraping off-site drawdown measured
(2026-07-17) for the WMC3 measured / wider-cone-modelled framing.
====================================================================================
"""

__version__ = "1.9.0"  # Hollingham (2026) — 2026-08-19. D-043: the far-field
#   band of v1.8.0 is WITHDRAWN. Panel (a) is five distance-decay curves plus
#   the measured anchors and the reach-L rule — the 2026-07-02 signed-off
#   design, restored rather than newly decided. Removed: the axhspan band, its
#   two dashed edge lines, the band note, _load_farfield_level_range(), the
#   25_11 read and its two _plot_reach parameters, and the
#   far_field_level_lo/hi_head_mm columns of 09f_01 (retired with nothing
#   drawing them; the identified sum lives in 25_11, its own source). The 900 m
#   axis STAYS — introduced in v1.6.0 for the crossing, kept because it shows
#   the fitted reach L. Panel (b), the development timescale, is untouched.
#
# v1.8.0 (2026-08-19): far-field band replacing the flat climate line and the
#   crossing (D-039, D-042). Superseded by 1.9.0 the same day; the removal of
#   the flat climate line and the crossing STANDS, only the band is withdrawn.
# v1.7.0 (2026-07-18): two-panel reach + development-timescale synthesis figure.
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from utils.paths import (
    make_all_dirs,
    OUT_09D_SCENARIO_CSV, OUT_09B_INDIVIDUAL,
    OUT_20_REPORT_NUMBERS, OUT_25_FIT_PARAMETERS, OUT_10A_REPORT, OUT_10M_REPORT,
    OUT_03_MECHANISTIC_TABLE,
    OUT_09F_EFFECTS, OUT_09F_EFFECTS_PUBLIC,
    OUT_09F_REACH_CSV,
)
from utils.console_utils import banner, phase, info, warn, saved
from utils.site_observations import load_site_observation
from utils.scraping_common import MPL_DEFAULTS
from utils.config import (SCRAPE_RISE_BUFFER_M, COAST_RETREAT_M,
                          DRAWDOWN_H0_MM, COAST_CHRONIC_YEARS,
                          FOREST_CIDS)
from utils.pipeline_params import default_value
from utils.coastal_utils import coastal_edge_h0
from utils.render_utils import render_figure


# ----------------------------------------------------------------------------
# Live-value loaders
# ----------------------------------------------------------------------------
def _load_lambda_and_forest_h0():
    """λ (m) and forest interception-deficit H0 (mm).

    Live from Script 20 (20_report_numbers.csv). On a first-pass run before
    Script 20 has executed, falls back to the documented default λ and the
    config forest H0, with a warning.
    """
    try:
        df = pd.read_csv(OUT_20_REPORT_NUMBERS)
        lam = float(df.loc[df["Parameter"] == "drawdown_lambda", "Value"].iloc[0])
        h0f = float(df.loc[df["Parameter"] == "drawdown_H0", "Value"].iloc[0])
        return lam, h0f
    except (FileNotFoundError, KeyError, IndexError):
        lam = default_value("drawdown_lambda_m")
        warn(f"20_report_numbers.csv unavailable — using default \u03bb = {lam:.0f} m "
             f"and config H0 = {DRAWDOWN_H0_MM:.0f} mm (run Script 20 for live values).")
        return lam, float(DRAWDOWN_H0_MM)


def _load_clearfell_recovery_mm():
    """Measured clearfell BACI step (mm).

    Live from the 10a headline CSV (ANCOVA_Forest_Impact_clearfell_step, impact
    well WMC3, post-felling), converted m -> mm. Falls back to the documented
    default on a first-pass run before Script 10a has executed.
    """
    try:
        df = pd.read_csv(OUT_10A_REPORT)
        key = df.iloc[:, 0].astype(str)
        row = df[key == "ANCOVA_Forest_Impact_clearfell_step"]
        val_col = df.columns[3]   # numeric Value column
        return float(row[val_col].iloc[0]) * 1000.0
    except (FileNotFoundError, KeyError, IndexError):
        v = default_value("clearfell_recovery_mm")
        warn(f"10a_report_numbers.csv unavailable — using default clearfell "
             f"recovery = {v:.0f} mm (run Script 10a for the live value).")
        return float(v)


def _load_scrape_bars():
    """Scrape on-site + off-site volumetric values (mm w.e./month) from 09d_01.

    Falls back to the documented off-site default on a first-pass run before
    Script 09d has executed; the other bars are figure context and default to
    the same construction only when 09d is absent.
    """
    try:
        df = pd.read_csv(OUT_09D_SCENARIO_CSV)
        d = dict(zip(df["Scenario"], df["Delta_vol_mm_per_month"]))
        return {
            "on_site":   float(d["Scraping (observed)"]),
            "off_100":   float(d["Scraping (off-site 100 m)"]),
            "off_250":   float(d.get("Scraping (off-site 250 m)", np.nan)),
            "clearfell": float(d["Clearfell (hypothetical)"]),
            "thinning":  float(d["Thinning 50% (hypothetical)"]),
            "broadleaf": float(d["Broadleaf (hypothetical)"]),
            "climate_dry": float(d["Climate dry"]),
            "climate_wet": float(d["Climate wet"]),
        }
    except (FileNotFoundError, KeyError, IndexError):
        off100 = default_value("scrape_offsite_100m_vol")
        warn("09d_01_scenario_comparison.csv unavailable — scrape bars from "
             f"defaults (off-site 100 m = {off100:.1f} mm w.e./month; "
             "run Script 09d for live values).")
        return {"on_site": np.nan, "off_100": off100, "off_250": np.nan,
                "clearfell": np.nan, "thinning": np.nan, "broadleaf": np.nan,
                "climate_dry": np.nan, "climate_wet": np.nan}


def _load_coast_edge_rate():
    """Absolute coast-edge summer-minimum retreat rate δ₀ (mm/yr) and reach L.

    Live from Script 25 (25_01_panel_fit_parameters.csv), forest-free
    linear-capped fit; δ₀ is a NEGATIVE rate. Falls back to documented
    defaults on a first-pass run before Script 25 has executed (CI set equal
    to δ₀ so no spurious whisker is drawn).
    """
    try:
        df = pd.read_csv(OUT_25_FIT_PARAMETERS)
        row = df[(df["source"] == "forest_free") & (df["model"] == "linear_capped")]
        if row.empty:
            row = df[df["model"] == "linear_capped"]
        d0 = float(row["delta_0_mm_yr"].iloc[0])
        lo = float(row["delta_0_ci_lo"].iloc[0])
        hi = float(row["delta_0_ci_hi"].iloc[0])
        L = float(row["L_m"].iloc[0])
        return d0, lo, hi, L
    except (FileNotFoundError, KeyError, IndexError):
        d0 = default_value("coast_delta0_mm_yr")
        L = default_value("coast_reach_L_m")
        warn(f"25_01_panel_fit_parameters.csv unavailable — using default "
             f"\u03b4\u2080 = {d0:.0f} mm/yr, L = {L:.0f} m "
             "(run Script 25 for live values).")
        return d0, d0, d0, L


def _load_wmc3_drawdown():
    """Measured WMC3 off-cut drawdown (mm, negative) — the one evidenced
    off-site scrape-drainage point.

    Live from Script 10m (10m_report_numbers.csv), the 2015-scrape BACI
    difference-in-differences step (reproduced at the 2023 re-scrape: -54 mm),
    converted m -> mm. Falls back to the documented default on a first-pass run
    before Script 10m has executed.
    """
    try:
        df = pd.read_csv(OUT_10M_REPORT)
        key = df.iloc[:, 0].astype(str)
        row = df[key == "WMC3_BACI_DiD_step_2015_scraping"]
        val_col = df.columns[3]   # numeric Value column
        return float(row[val_col].iloc[0]) * 1000.0
    except (FileNotFoundError, KeyError, IndexError):
        v = default_value("wmc3_drawdown_mm")
        warn(f"10m_report_numbers.csv unavailable — using default WMC3 "
             f"drawdown = {v:.0f} mm (run Script 10m for the live value).")
        return float(v)


def _load_wmc3_distance():
    """CEH36 → WMC3 separation (m) for the WMC3 anchor's x-position.

    Live from Script 09b (09b_01_individual_well_baci.csv, wmc3 dist_m). Falls
    back to the documented default on a first-pass run before Script 09b.
    """
    try:
        df = pd.read_csv(OUT_09B_INDIVIDUAL)
        row = df[df["well"].astype(str).str.lower() == "wmc3"]
        return float(row["dist_m"].iloc[0])
    except (FileNotFoundError, KeyError, IndexError):
        d = default_value("wmc3_distance_m")
        warn(f"09b_01_individual_well_baci.csv unavailable — using default "
             f"WMC3 distance = {d:.0f} m (run Script 09b for the live value).")
        return float(d)


def _load_forest_beta3_range():
    """Forest-cluster drainage coefficient β₃ (per month) and the implied
    approach-to-equilibrium half-life t½ = ln2/β₃ (months).

    Returns (b3_fast, b3_slow, thalf_fast_mo, thalf_slow_mo) spanning the forest
    clusters C4/C5 (the clusters the clearfell/broadleaf drivers act on). Live
    from the committed mechanistic table; falls back to the documented default
    β₃ on a first-pass run before Script 03 has executed.
    """
    try:
        m = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
        b3 = m[m["Cluster"].isin(FOREST_CIDS)]["beta_3_drainage"].astype(float)
        b3_fast, b3_slow = float(b3.max()), float(b3.min())   # fast = larger β₃
        return (b3_fast, b3_slow,
                np.log(2) / b3_fast, np.log(2) / b3_slow)
    except (FileNotFoundError, KeyError, IndexError, ValueError):
        b3 = float(default_value("beta_3"))
        warn(f"03 mechanistic table unavailable — forest β₃ half-life from "
             f"default β₃ = {b3:.3f}/mo (run Script 03 for live values).")
        th = np.log(2) / b3
        return b3, b3, th, th


def _load_c3_beta3():
    """C3 (Western Residual, open-dune) drainage coefficient β₃ (per month) and
    half-life t½ = ln2/β₃ (months). C3 is the propagation medium a scrape or a
    storm-retreat step relaxes through (same cluster Script 20's λ uses), so it
    sets the timescale for the scrape/storm relaxation curve. Live from the
    committed mechanistic table; first-pass fallback to the default β₃."""
    try:
        m = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
        b3 = float(m[m["Cluster"] == 3]["beta_3_drainage"].iloc[0])
        return b3, np.log(2) / b3
    except (FileNotFoundError, KeyError, IndexError, ValueError):
        b3 = float(default_value("beta_3"))
        warn(f"03 mechanistic table unavailable — C3 β₃ from default "
             f"{b3:.3f}/mo (run Script 03 for the live value).")
        return b3, np.log(2) / b3


def _coastal_retreat_edge_head(delta0_abs, L):
    """Edge head drawdown (mm) and reach L (m) for a single COAST_RETREAT_M
    shoreline-retreat event, EXACTLY as Script 20's plot_coastal_erosion:

        h0 = COAST_RETREAT_M * (δ₀ / measured_retreat_rate)  (mm)
        Δh(d) = h0 * (1 - d/L)   (linear-capped, to zero at L)

    Constants match Script 20 module constants (single source of truth).
    """
    h0, _rate, _per_m, _prov = coastal_edge_h0(delta0_abs)
    return h0, L, COAST_RETREAT_M


# ----------------------------------------------------------------------------
# Panel A — spatial reach (distance-decay)
# ----------------------------------------------------------------------------
def _plot_reach(ax, lam, forest_h0_mm, scrape,
                coast_edge_head_6m, coast_L, coast_edge_head_5yr,
                scrape_edge_head,
                wmc3_dist_m, wmc3_drawdown_mm, clearfell_measured_mm=120.0):
    """Distance-decay of scrape dipole, forest drawdown and TWO coastal curves
    on a single continuous y-axis, with the one measured off-site scrape point
    (WMC3) anchored on the reach.

    Curves:
      - Scrape drain (dipole): exp decay over λ; edge = measured CEH36 response.
        This is the wider MODELLED cone; the single measured off-site point is
        WMC3 (below), NOT a network-wide measured halo.
      - Standing pine / thinned forest: canopy drawdown, exp decay over λ.
      - Coastal retreat, 6 m acute storm: single Storm-Brendan-class EVENT,
        linear-capped to zero at L (Script 20 form, ÷ storm-inclusive rate).
      - Coastal retreat, 5-year accumulation: five years of the fitted coast-edge
        trend δ₀, linear-capped to zero at L. Accumulation of the fitted trend,
        not a single event — labelled as such.
    Nothing spatially uniform is drawn. The level the coastal gradient decays
    toward is not separately identified — the Script 25 panel recovers only the
    sum of a constant and the CWB trend (D-039) — so it is neither a curve, nor
    a band, nor a crossing on a distance-decay panel (D-043). Where it needs to
    be quoted, its source is 25_11_matched_window_sensitivity.csv.

    Measured anchors (distinct from the modelled curves): scrape CEH36 rise and
    forest/clearfell drawdown at r≈0, and the WMC3 off-cut drawdown at its
    measured distance — the ONE evidenced off-site point.
    """
    # The reach axis runs well past the interventions' λ decay so the fitted
    # coastal reach L — marked by the L rule below, read live from 25_01 — sits
    # inside the panel. That is the whole reason for its width: it was widened
    # for the retired crossing, and it is kept for L (D-043).
    r = np.linspace(0, 900, 720)

    scrape_head = np.where(
        r <= SCRAPE_RISE_BUFFER_M,
        scrape_edge_head,
        -scrape_edge_head * np.exp(-(r - SCRAPE_RISE_BUFFER_M) / lam))

    forest_standing = -forest_h0_mm * np.exp(-r / lam)
    forest_thinned  = -0.5 * forest_h0_mm * np.exp(-r / lam)

    coastal_6m  = np.where(r <= coast_L,
                           -coast_edge_head_6m * (1.0 - r / coast_L), 0.0)
    coastal_5yr = np.where(r <= coast_L,
                           -coast_edge_head_5yr * (1.0 - r / coast_L), 0.0)

    ax.axhline(0, color="0.4", lw=0.8, zorder=1)
    ax.plot(r, scrape_head, color="#c1272d", lw=2.4,
            label="Scrape drain (dipole, modelled)", zorder=3)
    ax.plot(r, forest_standing, color="#1b5e2a", lw=2.4,
            label="Standing pine (drawdown)", zorder=3)
    ax.plot(r, forest_thinned, color="#6aa84f", lw=2.0, ls="--",
            label="Thinned forest 50% (drawdown)", zorder=3)
    ax.plot(r, coastal_6m, color="#7d5ba6", lw=2.2, ls="-",
            label="Coastal retreat: 6 m acute storm (single event)", zorder=3)
    ax.plot(r, coastal_5yr, color="#7d5ba6", lw=2.4, ls=":",
            label="Coastal retreat: 5-year accumulation (5\u00d7\u03b4\u2080)",
            zorder=3)

    # measured anchors, nudged off the y-spine so the full marker shows
    ax.scatter([6], [scrape_edge_head], s=70, color="#c1272d",
               edgecolor="k", zorder=6, linewidth=0.8)
    ax.scatter([6], [-clearfell_measured_mm], s=70, color="#1b5e2a",
               edgecolor="k", zorder=6, linewidth=0.8)
    ax.annotate("observed clearfell\ndrawdown", xy=(6, -clearfell_measured_mm),
                xytext=(78, -clearfell_measured_mm - 34), fontsize=7.5,
                color="#14401f",
                arrowprops=dict(arrowstyle="->", color="#1b5e2a", lw=0.9))

    # WMC3 — the ONE measured off-site drawdown point (below the modelled dipole)
    ax.scatter([wmc3_dist_m], [wmc3_drawdown_mm], s=80, marker="D",
               color="#c1272d", edgecolor="k", zorder=6, linewidth=0.9)
    ax.annotate(f"WMC3 off-cut drawdown\n({wmc3_drawdown_mm:.0f} mm, measured, "
                f"{wmc3_dist_m:.0f} m)",
                xy=(wmc3_dist_m, wmc3_drawdown_mm),
                xytext=(wmc3_dist_m + 45, -112), fontsize=7.5, color="#7a1a1e",
                arrowprops=dict(arrowstyle="->", color="#c1272d", lw=0.9))

    # reach-L rule: the fitted coastal reach, and the reason the axis is this wide
    ax.axvline(coast_L, color="0.6", lw=0.8, ls=":", zorder=1)
    ax.text(coast_L, -160, "L", fontsize=8, color="0.5", ha="center", va="bottom")

    # near-field band the network cannot resolve (nearest uphill well 247 m)
    ax.axvspan(0, 247, color="0.88", alpha=0.4, zorder=0)
    ax.text(123, 120, "near field —\nno dipwell (nearest 247 m)",
            ha="center", va="center", fontsize=7.2, color="0.45", style="italic")

    ax.set_xlim(-10, 900)
    ax.set_ylim(-165, 140)
    ax.set_xlabel("Distance from intervention (m)", fontsize=11)
    ax.set_ylabel("Equilibrium \u0394h at water table (mm)", fontsize=11)
    ax.set_title("(a) Spatial reach", fontsize=12, loc="left", fontweight="bold")

    main_leg = ax.legend(fontsize=7.6, loc="lower right", framealpha=0.95)
    ax.add_artist(main_leg)
    prox = [Line2D([0], [0], marker="o", color="w", markerfacecolor="0.5",
                   markeredgecolor="k", markersize=8, label="measured anchor"),
            Line2D([0], [0], color="0.5", lw=2, label="modelled steady-state")]
    ax.legend(handles=prox, fontsize=7.5, loc="upper right", framealpha=0.95)

    prof = pd.DataFrame({
        "distance_m": r,
        "scrape_head_mm": scrape_head,
        "standing_pine_head_mm": forest_standing,
        "thinned_forest_head_mm": forest_thinned,
        "coastal_6m_storm_head_mm": coastal_6m,
        "coastal_5yr_head_mm": coastal_5yr,
    })
    prof.to_csv(OUT_09F_REACH_CSV, index=False, float_format="%.2f")


def _plot_timescale(ax, forest_h0_mm, clearfell_measured_mm,
                    thalf_forest_fast_mo, thalf_forest_slow_mo, thalf_c3_mo):
    """Panel (b) — how long the driver effects take to develop.

    Y-axis: percentage of the eventual effect reached (dimensionless). This is
    deliberately dimensionless so it COMPOSES with panel (a): panel (b) gives the
    time-fraction of the eventual effect, panel (a) gives the eventual spatial
    magnitude, and the head at a given time-and-distance is their product (e.g.
    scraping ~75% developed at 2 yr × a ~−65 mm reach value at 200 m ≈ −48 mm).
    An mm y-axis would bake a magnitude into panel (b) and double-count against
    panel (a), so % is the dimensionally consistent choice.

    Three timescale logics, three curve shapes:
      • Forest canopy operations (clearfell / thinning), β₃-governed RELAXATION
        on the FOREST clusters: 1 − e^(−β₃·t), a saturating exponential drawn as
        a BAND spanning the forest half-life range (C5 fast ↔ C4 slow); both edges
        labelled with their t½. The OBSERVED clearfell BACI step is plotted at its
        elapsed time as the fraction of the 150 mm equilibrium it represents — the
        validation anchor (the record sits where the timescale predicts, so the
        mapped equilibrium magnitudes are corroborated once the timescale is
        applied — consistent with, not alarmist).
      • Scrape / storm-retreat event, RELAXATION on the C3 open-dune medium
        (faster than the forest): one curve — a scrape excavation and a single
        storm-retreat step are both instantaneous changes the surrounding aquifer
        relaxes toward, on the same C3 timescale, so in fraction-of-eventual terms
        they coincide.
      • Coastal chronic ACCUMULATION: the coast-edge decline accumulates LINEARLY
        at δ₀/yr — it does not relax to an equilibrium, it grows. A straight ramp
        (the distinct shape is the key contrast with the relaxations).

    Far-field inland propagation (toward the ~900 m reach) is diffusive and slow
    — order-of-magnitude only, NOT a committed number here (see caption).
    """
    t = np.linspace(0, 15, 300)
    tm = t * 12.0                                  # months
    b3_forest_slow = np.log(2) / thalf_forest_slow_mo
    b3_forest_fast = np.log(2) / thalf_forest_fast_mo
    b3_c3          = np.log(2) / thalf_c3_mo

    f_slow    = (1.0 - np.exp(-b3_forest_slow * tm)) * 100.0
    f_fast    = (1.0 - np.exp(-b3_forest_fast * tm)) * 100.0
    c3_relax  = (1.0 - np.exp(-b3_c3 * tm)) * 100.0
    coast_lin = (t / COAST_CHRONIC_YEARS) * 100.0
    ytop = 320.0

    # 100% reference line — equilibrium for the relaxations / 5-yr chronic
    # reference for the coastal ramp.
    ax.axhline(100, color="0.5", lw=0.8, zorder=1)
    ax.text(14.8, 103, "100% = equilibrium (relaxations) / 5-yr chronic (coastal)",
            fontsize=7, color="0.4", style="italic", ha="right")

    # Forest canopy-operations band (clearfell / thinning) — C5 fast ↔ C4 slow.
    ax.fill_between(t, f_slow, f_fast, color="#1b5e2a", alpha=0.16, zorder=2,
                    label="Forest ops (clearfell/thinning) relaxation band")
    ax.plot(t, f_fast, color="#1b5e2a", lw=1.6, zorder=3,
            label=f"  fast edge: C5 t\u00bd = {thalf_forest_fast_mo:.0f} mo")
    ax.plot(t, f_slow, color="#1b5e2a", lw=1.6, ls="--", zorder=3,
            label=f"  slow edge: C4 t\u00bd = {thalf_forest_slow_mo:.0f} mo")

    # Scrape / storm-retreat event — one C3 relaxation curve (coincide in %).
    ax.plot(t, c3_relax, color="#c1272d", lw=2.0, zorder=4,
            label=f"Scrape / storm event (C3 t\u00bd = {thalf_c3_mo:.0f} mo)")

    # Coastal chronic accumulation — linear.
    ax.plot(t, coast_lin, color="#7d5ba6", lw=2.4, ls=":", zorder=4,
            label=f"Coastal chronic accumulation (linear, {COAST_CHRONIC_YEARS:.0f}-yr ref)")

    # Observed clearfell anchor at its elapsed time (Dec 2017 → 2026-02 cutoff).
    elapsed_yr = (2026 + 1/12) - (2017 + 12/12)
    anchor_y = (clearfell_measured_mm / forest_h0_mm) * 100.0
    ax.scatter([elapsed_yr], [anchor_y], s=90, color="#1b5e2a",
               edgecolor="k", zorder=6, linewidth=1.0)
    # Callout anchored bottom-right, arrow to the observed point.
    ax.annotate(f"observed clearfell = {anchor_y:.0f}% of {forest_h0_mm:.0f} mm"
                f"\nat {elapsed_yr:.0f} yr",
                xy=(elapsed_yr, anchor_y),
                xytext=(14.6, 0.04 * ytop),
                fontsize=7.8, color="#14401f", va="bottom", ha="right",
                bbox=dict(boxstyle="round,pad=0.35", fc="white",
                          ec="#1b5e2a", alpha=0.92),
                arrowprops=dict(arrowstyle="->", color="#1b5e2a", lw=1.0,
                                connectionstyle="arc3,rad=0.0"))

    ax.set_xlim(0, 15)
    ax.set_ylim(0, ytop)
    ax.set_xlabel("Years since intervention / onset", fontsize=11)
    ax.set_ylabel("Percentage of the eventual effect reached (%)", fontsize=11)
    ax.set_title("(b) Development timescale", fontsize=12, loc="left", fontweight="bold")
    ax.legend(fontsize=7.2, loc="upper left", framealpha=0.95, ncol=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", action="store_true",
                    help="public/academic-summary variant (same figure, lighter title)")
    args = ap.parse_args()

    make_all_dirs()
    plt.rcParams.update(MPL_DEFAULTS)
    banner("09f", "MANAGEMENT EFFECTS — SPATIAL REACH", version=__version__)

    phase(1, "Loading live values")
    lam, forest_h0 = _load_lambda_and_forest_h0()
    scrape = _load_scrape_bars()
    coast_d0, coast_lo, coast_hi, coast_L = _load_coast_edge_rate()

    # scrape edge head: measured CEH36 pure-scraping BACI response, LIVE from
    # the site-observations registry (same anchor 09d uses); m -> mm. On a
    # first-pass run before the registry exists, fall back to |off-site 100 m|
    # implied edge is not recoverable, so use the documented on-site default.
    try:
        scrape_edge_head = load_site_observation("ceh36_baci_pure_scraping") * 1000.0
        scrape_edge_src = "measured, live"
    except (FileNotFoundError, KeyError, ValueError, TypeError):
        scrape_edge_head = 129.0
        scrape_edge_src = "default (registry unavailable)"
        warn("site-observations registry unavailable — scrape edge head from "
             "default 129 mm (run Script 09a for the live value).")
    clearfell_recovery_mm = _load_clearfell_recovery_mm()

    # 6 m acute-storm edge drawdown (Script 20 construction, ÷ storm rate)
    coast_edge_6m, coast_L, _ = _coastal_retreat_edge_head(abs(coast_d0), coast_L)
    # Chronic accumulation of the fitted trend over COAST_CHRONIC_YEARS: N × δ₀
    # (chronic normaliser cancels, so independent of the assumed retreat rate).
    # Keeps amplitude on one axis. Same construction + horizon as Script 20's
    # driver-change coastal field (config.COAST_CHRONIC_YEARS, shared).
    coast_edge_5yr = COAST_CHRONIC_YEARS * abs(coast_d0)

    # the measured WMC3 off-site anchor
    wmc3_drawdown = _load_wmc3_drawdown()
    wmc3_dist = _load_wmc3_distance()

    b3_fast, b3_slow, thalf_fast, thalf_slow = _load_forest_beta3_range()
    b3_c3, thalf_c3 = _load_c3_beta3()

    info(f"\u03bb = {lam:.1f} m   forest H0 = {forest_h0:.0f} mm")
    info(f"scrape edge head ({scrape_edge_src}) = {scrape_edge_head:.1f} mm")
    info(f"clearfell recovery = {clearfell_recovery_mm:.1f} mm")
    info(f"coast-edge \u03b4\u2080 = {coast_d0:.1f} mm/yr (CI {coast_lo:.1f}, {coast_hi:.1f}), L = {coast_L:.0f} m")
    info(f"coastal 6 m storm edge = {coast_edge_6m:.1f} mm; 5-year (5\u00d7\u03b4\u2080) edge = {coast_edge_5yr:.1f} mm")
    info(f"WMC3 measured off-cut drawdown = {wmc3_drawdown:.1f} mm at {wmc3_dist:.0f} m")
    info(f"forest t\u00bd (C4\u2013C5) = {thalf_slow:.0f}\u2013{thalf_fast:.0f} mo; C3 t\u00bd = {thalf_c3:.0f} mo")

    phase(2, "Plotting reach + timescale figure (stacked)")
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(9.4, 12.2), dpi=300)
    _plot_reach(axA, lam, forest_h0, scrape,
                coast_edge_6m, coast_L, coast_edge_5yr, scrape_edge_head,
                wmc3_dist, wmc3_drawdown,
                clearfell_measured_mm=clearfell_recovery_mm)
    _plot_timescale(axB, forest_h0, clearfell_recovery_mm,
                    thalf_fast, thalf_slow, thalf_c3)

    title = ("Newborough Warren: spatial reach and development timescale "
             "of management interventions and coastal retreat")
    fig.suptitle(title, fontsize=12.5, y=0.99)

    # Caption is NOT baked into the figure — supplied in the report/summary
    # document text (avoids a duplicate caption when placed in LibreOffice).

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    out = OUT_09F_EFFECTS_PUBLIC if args.public else OUT_09F_EFFECTS
    render_figure(fig, out)
    plt.close(fig)
    saved(out.name)
    saved(OUT_09F_REACH_CSV.name)
    print("\nDone.")


if __name__ == "__main__":
    main()
