"""
21_forestry_scenarios.py
========================
Forest management scenario analysis for Newborough Warren coastal dune aquifer.

Produces two figures:
  OUT_21_HYDROGRAPH   — Synthetic mean-year hydrograph for C4 under each
                         management scenario, with BACI-observed benchmark
  OUT_21_DISTRIBUTIONS — Observed annual summer minimum depth distributions
                          by cluster and C4 phase (pre/post felling)

Method
------
Hydrograph figure:
  The steady-state SSM cannot be run forward from an arbitrary initial
  condition without accumulating drift (the intercept term α that closes
  the water balance is not included in the forward simulation). Instead,
  scenario impacts are expressed as monthly single-step perturbations:

      Δh(m) = β₁·(P_eff_scen(m) − P_eff_base(m))
            − (β₂_scen(m) − β₂_base)·PET(m)

  This is the immediate monthly forcing response — the first-year
  adjustment, not a steady-state prediction. The β₃ drainage term does
  not appear because in the first month after a management change, h has
  not yet moved, so the drainage response to the change is zero.

  These shifts are applied to the observed C4 mean seasonal cycle to produce
  scenario-specific synthetic hydrographs. This approach is grounded in the
  observed record, avoids SSM drift, and produces physically reasonable
  magnitudes (order 0.05–0.10 m/month) comparable to BACI observations.

  Broadleaf conversion uses seasonally-varying β₂ to capture deciduous
  phenology: lower ET in winter (leaves off, Oct-Mar) and higher in summer
  (leaves on, Jun-Sep), combined with reduced annual interception (15% uniform annual average,
  approximating ~20% growing-season interception with zero winter interception, vs 24% pine).

  The BACI-observed clearfell displacement (-0.218 m summer, -0.145 m annual)
  is shown as a benchmark band. The gap between modelled and BACI clearfell
  reflects both the cumulative drainage feedback over multiple years (which
  the single-step perturbation does not capture) and unparameterised water
  balance residual pathways.

Distribution figure:
  Violin/strip plot of observed annual summer minimum depths by cluster
  and C4 phase, from the full 2005-2026 dipwell record. No modelling.

Inputs
------
  03_master_data.csv              — per-well SSM β coefficients and cluster
  01_climate.csv                  — monthly P and PET (RAF Valley)
  03_regional_averages_maod.csv   — cluster-mean maOD heads
  Well_locations_height.csv       — DEM and pipe top elevations
  Newborough_Cleaned_For_Model.csv — raw well depth data (for distributions)

Outputs
-------
  OUT_21_HYDROGRAPH      — 21_forestry_01_hydrograph.png
  OUT_21_DISTRIBUTIONS   — 21_forestry_02_distributions.png

Usage
-----
  python 21_forestry_scenarios.py [--preview]

References
----------
  Curreli et al. (2013) — ecological thresholds SD15b, SD16
  Freeman (2008)        — canopy interception 24% (pine); broadleaf assumed 15% annual average (~20% growing season, zero winter)
  Hollingham (2026)     — BACI clearfell result: -0.145 m annual, -0.218 m summer
"""

import argparse
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

from utils.paths import (
    INT_MASTER_DATA, INT_CLIMATE,
    INT_CLUSTER_AVG_MAOD, INT_WELL_ELEVATIONS,
    INT_WELLS_CLEAN, INT_WELLS_EXTENDED,
    OUT_DIR, make_all_dirs,
    DIR_21,
    OUT_21_HYDROGRAPH, OUT_21_DISTRIBUTIONS, OUT_21_DISTRIBUTIONS_CSV,
    OUT_21_SCRAPING, OUT_21_SCRAPING_CSV, OUT_21_BACI_VIOLIN, OUT_21_BACI_CSV,
)
from utils.config import (
    FOREST_INTERCEPTION, BROADLEAF_INTERCEPTION, REFERENCE_CUTOFF_DATE,
    SD15b, SD15b_REC, SD16, SD16_REC,
)
from utils.model_utils import monthly_perturbation


# ============================================================================
# OUTPUT PATHS
# ============================================================================
from pathlib import Path

# ============================================================================
# CONSTANTS
# ============================================================================
# FOREST_INTERCEPTION, BROADLEAF_INTERCEPTION, SD15b, SD15b_REC, SD16,
# SD16_REC all imported from config.py.

# BACI-observed post-felling displacement (Hollingham 2026, Section 4.6)
BACI_ANNUAL = 0.145  # m — mean annual deepening (positive = deeper)
BACI_SUMMER = 0.218  # m — mean summer deepening

# Clearfell β₂ increase from BACI (Section 4.6.6)
# Derived from zone-mean pre/post β₂ ratios: impact 3.755/3.124 = 1.20,
# edge 3.751/3.123 = 1.20, control 3.696/3.030 = 1.22 (10_cfell_07_coefficient_slopes.csv)
CLEARFELL_B2_MULT = 1.20    # 20% increase in ET draw post-felling
THINNING_B2_MULT  = 1.10    # 50% of clearfell effect (1 + 0.20/2)

# Summer months (Jun-Sep inclusive, 1-based)
SUMMER_MONTHS = [6, 7, 8, 9]
FELLING_DATE  = "2018-01-01"

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

# Figure settings
FIG_DPI    = 300
FIG_FONT   = "Arial"

SCENARIO_COLOURS = {
    "Baseline (Corsican pine)":     "#2166AC",
    "Full clearfell":               "#D73027",
    "50% thinning":                 "#F46D43",
    "Broadleaf conversion":         "#4DAC26",
}
SCENARIO_STYLES = {
    "Baseline (Corsican pine)":     "-",
    "Full clearfell":               "--",
    "50% thinning":                 "-.",
    "Broadleaf conversion":         ":",
}
SCENARIO_LW = {
    "Baseline (Corsican pine)":     2.5,
    "Full clearfell":               2.0,
    "50% thinning":                 2.0,
    "Broadleaf conversion":         2.2,
}

CLUSTER_COLOURS = {
    "C1\nEastern\nlake-buffer":          "#E69F00",
    "C2\nEastern\nmature dune":          "#009E73",
    "C3\nWestern\nmature dune":          "#CC79A7",
    "C4 Forest\npre-felling\n2005–17":   "#56B4E9",
    "C4 Forest\npost-felling\n2018–25":  "#D55E00",
}


# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    master  = pd.read_csv(INT_MASTER_DATA)
    elev    = pd.read_csv(INT_WELL_ELEVATIONS)
    reg     = pd.read_csv(INT_CLUSTER_AVG_MAOD,
                          parse_dates=["Date"]).set_index("Date")
    climate = pd.read_csv(INT_CLIMATE, parse_dates=["Date"]).set_index("Date")

    master["well"]  = master["Name_Original"].str.lower().str.replace(" ", "")
    # INT_WELL_ELEVATIONS has Name_norm already; also derive "well" for compat
    elev["well"]    = elev["Name"].str.lower().str.replace(" ", "")

    return master, elev, reg, climate


def load_raw_well_data():
    """Load well depth data from 01_wells_clean.csv (pipeline output).

    Switched from Newborough_Cleaned_For_Model.csv to ensure the most
    up-to-date quality-controlled data is used, including 2025 field
    readings that were not present in the original raw input file.

    Returns (df, dates, well_names) in a format compatible with all
    downstream functions via get_well_monthly().
    """
    df_main = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    df_main.columns = df_main.columns.str.strip().str.lower().str.replace(" ", "")
    if INT_WELLS_EXTENDED.exists():
        df_ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
        df_ext.columns = df_ext.columns.str.strip().str.lower().str.replace(" ", "")
        new_cols = [c for c in df_ext.columns if c not in df_main.columns]
        df = pd.concat([df_main, df_ext[new_cols]], axis=1)
    else:
        df = df_main
    dates      = df.index
    well_names = df.columns.values
    return df, dates, well_names


def get_well_monthly(w, df, dates, well_names):
    """Return monthly-resampled depth series for a single well.

    Handles both the old raw-file format (df is a 2D array with well
    names in column 0) and the new clean-file format (df is a DataFrame
    with well names as columns).
    """
    if isinstance(df, pd.DataFrame) and w in df.columns:
        return df[w].dropna().resample("MS").mean()
    # Legacy fallback for old raw format
    row = [i for i, n in enumerate(well_names) if n == w]
    if not row:
        return None
    d = pd.to_numeric(df.iloc[row[0] + 2, 1:], errors="coerce").values
    return pd.Series(d, index=dates).dropna().resample("MS").mean()


def get_maod(w, df, dates, well_names, elev):
    """Convert raw depth to maOD: maOD = Pipe_Top_Elev + raw_depth."""
    raw = get_well_monthly(w, df, dates, well_names)
    pt  = elev[elev["well"] == w]["Pipe_Top_Elev"]
    if raw is None or pt.empty:
        return None
    return pt.values[0] + raw


def cluster_summer_mins(cl, master, df, dates, well_names, elev,
                        pre_post="all"):
    """
    Return array of annual summer minimum depths below ground for a cluster.
    pre_post: 'all', 'pre' (before FELLING_DATE), 'post' (after).
    """
    wells = master[master["Cluster"] == cl]["well"].tolist()
    well_depths = []
    for w in wells:
        maod_s = get_maod(w, df, dates, well_names, elev)
        dem_r  = elev[elev["well"] == w]["DEM_Ground_Elev"]
        if maod_s is None or dem_r.empty:
            continue
        depth = dem_r.values[0] - maod_s   # positive = below ground
        if pre_post == "pre":
            depth = depth[depth.index < FELLING_DATE]
        elif pre_post == "post":
            depth = depth[depth.index >= FELLING_DATE]
        well_depths.append(depth)
    if not well_depths:
        return np.array([])
    combined = pd.concat(well_depths, axis=1).mean(axis=1)
    mins = []
    for yr in sorted(combined.index.year.unique()):
        mask = ((combined.index.year == yr) &
                (combined.index.month.isin(SUMMER_MONTHS)))
        d = combined[mask].dropna()
        if len(d) >= 2:
            mins.append(float(d.max()))
    return np.array(mins)


# ============================================================================
# SCENARIO COMPUTATION
# ============================================================================


def build_scenarios(master, climate):
    """Build scenario equilibrium shifts and apply to observed C4 seasonal cycle."""
    b1 = master[master["Cluster"] == 4]["beta_1_recharge"].mean()
    b2 = master[master["Cluster"] == 4]["beta_2_atmospheric_draw"].mean()
    b3 = master[master["Cluster"] == 4]["beta_3_drainage"].mean()

    clim = climate.loc["2005-04-01":REFERENCE_CUTOFF_DATE].copy()
    monthly_P   = clim.groupby(clim.index.month)["P_m"].mean().values
    monthly_PET = clim.groupby(clim.index.month)["PET"].mean().values

    # P_eff variants
    P_base = monthly_P * (1 - FOREST_INTERCEPTION)
    P_cf   = monthly_P.copy()
    P_thin = monthly_P * (1 - FOREST_INTERCEPTION * 0.5)
    P_bl   = monthly_P * (1 - BROADLEAF_INTERCEPTION)

    # β₂ arrays — uniform for pine/clearfell/thinning
    b2_base = np.full(12, b2)
    b2_cf   = np.full(12, b2 * CLEARFELL_B2_MULT)
    b2_thin = np.full(12, b2 * THINNING_B2_MULT)

    # Broadleaf: deciduous phenology — lower ET Oct-Mar (leaves off),
    # higher ET Jun-Sep (leaves on, full LAI)
    b2_bl = np.array([
        b2 * 0.85,   # Jan — leaves off
        b2 * 0.85,   # Feb
        b2 * 0.88,   # Mar — bud burst beginning
        b2 * 0.92,   # Apr — partial leaf
        b2 * 0.98,   # May — approaching full leaf
        b2 * 1.08,   # Jun — full leaf, high ET
        b2 * 1.12,   # Jul
        b2 * 1.15,   # Aug — peak ET draw
        b2 * 1.10,   # Sep — late season, leaves turning
        b2 * 1.02,   # Oct — early leaf fall
        b2 * 0.92,   # Nov — mostly bare
        b2 * 0.87,   # Dec — dormant
    ])

    scenario_shifts = {
        "Baseline (Corsican pine)": np.zeros(12),
        "Full clearfell":  monthly_perturbation(
            b1, b2, b2_cf,   P_base, P_cf,   monthly_PET),
        "50% thinning":    monthly_perturbation(
            b1, b2, b2_thin, P_base, P_thin, monthly_PET),
        "Broadleaf conversion": monthly_perturbation(
            b1, b2, b2_bl,   P_base, P_bl,   monthly_PET),
    }

    return scenario_shifts, monthly_P, monthly_PET, b1, b2, b3


def get_observed_seasonal_cycle(reg, elev, master):
    """
    Return observed C4 mean monthly depth below ground from regional averages.
    """
    c4_wells = master[master["Cluster"] == 4]["well"].tolist()
    c4_dem   = np.mean([
        elev[elev["well"] == w]["DEM_Ground_Elev"].values[0]
        for w in c4_wells
        if not elev[elev["well"] == w].empty
    ])
    depth_c4    = c4_dem - reg["C4"].dropna()
    obs_monthly = depth_c4.groupby(depth_c4.index.month).mean().values  # 12 vals
    return obs_monthly, c4_dem


def get_cluster_obs_cycle(cl, reg, elev, master):
    """Observed mean monthly depth for C1 or C2 (for context lines)."""
    wells = master[master["Cluster"] == cl]["well"].tolist()
    dem   = np.mean([
        elev[elev["well"] == w]["DEM_Ground_Elev"].values[0]
        for w in wells
        if not elev[elev["well"] == w].empty
    ])
    depth = dem - reg[f"C{cl}"].dropna()
    return depth.groupby(depth.index.month).mean().values


# ============================================================================
# FIGURE 1 — SYNTHETIC HYDROGRAPH
# ============================================================================

def plot_hydrograph(scenario_shifts, obs_monthly, monthly_P, monthly_PET,
                    obs_c1, obs_c2, dpi=FIG_DPI):
    """
    Synthetic mean-year hydrograph for C4 under each management scenario.
    Scenario depth = obs_monthly - head_shift (positive shift = shallower).
    BACI-observed clearfell shown as a benchmark band.
    C1 and C2 observed cycles shown for ecological context.
    """
    # Apply shifts to observed seasonal cycle
    depths = {
        name: obs_monthly - shift
        for name, shift in scenario_shifts.items()
    }

    # BACI benchmark — uniform annual shift as lower bound
    baci_annual = obs_monthly + BACI_ANNUAL
    # BACI summer-specific (applied only to summer months)
    baci_summer = obs_monthly.copy()
    for m in [5, 6, 7, 8]:   # 0-based Jun-Sep
        baci_summer[m] += BACI_SUMMER

    x    = np.arange(1, 13)
    YMIN, YMAX = 0.35, 1.45

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(11, 10), facecolor="white",
        gridspec_kw={"height_ratios": [3, 1]})

    # ── Ecological zone shading ───────────────────────────────────────────────
    for ylo, yhi, col in [
        ( 0.00, SD15b,     "#a8d8a8"),
        ( SD15b, SD16,     "#ffffb2"),
        ( SD16,  SD16_REC, "#fd8d3c"),
        ( SD16_REC, 1.45,  "#f4c2a1"),
    ]:
        ax1.axhspan(max(ylo, YMIN), min(yhi, YMAX),
                    alpha=0.18, color=col, zorder=0)

    # Zone labels
    for y, lbl in [(0.48, "SD15b wet slack"), (0.80, "SD16 dry slack"),
                   (1.09, "SD16 recovery"),   (1.35, "Below recovery")]:
        if YMIN < y < YMAX:
            ax1.text(0.62, y, lbl, fontsize=6.5, color="dimgrey",
                     va="center", style="italic")

    # Threshold lines
    for thresh, lbl, col in [
        (SD15b,    f"SD15b  {SD15b} m",    "#005fa3"),
        (SD16,     f"SD16  {SD16} m",      "#a30000"),
        (SD16_REC, f"SD16 recovery",        "#4a0000"),
    ]:
        ax1.axhline(thresh, color=col, lw=0.9, ls="--", alpha=0.85, zorder=1)
        ax1.text(12.25, thresh, lbl, fontsize=7, color=col, va="center")

    # BACI benchmark band — annual shift
    ax1.fill_between(x,
                     depths["Full clearfell"],
                     np.clip(baci_summer, YMIN, YMAX),
                     color="#D73027", alpha=0.08, zorder=2)
    ax1.plot(x, np.clip(baci_summer, YMIN, YMAX),
             color="#D73027", lw=1.3, ls=(0, (3, 1, 1, 1)), alpha=0.6,
             zorder=3,
             label="Clearfell BACI observed (scraping + 2015–16 wet legacy)")

    # C1 and C2 observed for ecological context
    for obs_cl, lbl, col in [(obs_c1, "C1 Eastern lake-buffer (observed)", "#aaa"),
                              (obs_c2, "C2 Eastern mature dune (observed)",  "#666")]:
        ax1.plot(x, np.clip(obs_cl, YMIN, YMAX),
                 color=col, lw=1.0, ls="--", alpha=0.6, zorder=2,
                 label=lbl)

    # Scenario lines
    for name, d in depths.items():
        ax1.plot(x, d, color=SCENARIO_COLOURS[name],
                 lw=SCENARIO_LW[name], ls=SCENARIO_STYLES[name],
                 zorder=4, label=name)

    # Summer shading
    ax1.axvspan(5.5, 9.5, alpha=0.07, color="orange", zorder=0)
    ax1.text(7.5, YMAX - 0.05, "Summer\nwindow", fontsize=7.5,
             ha="center", color="darkorange", alpha=0.9)

    ax1.set_xlim(0.5, 13.8)
    ax1.set_ylim(YMAX, YMIN)   # inverted
    ax1.set_xticks(x)
    ax1.set_xticklabels(MONTHS, fontsize=9, fontname=FIG_FONT)
    ax1.set_ylabel("Depth below ground surface (m)", fontsize=10,
                   fontname=FIG_FONT)
    ax1.set_title(
        "C4 Forest Cluster — Synthetic Mean-Year Hydrograph\n"
        "Forest Management Scenarios  |  Newborough Warren 2005–2026  |  "
        "Ecological thresholds: Curreli et al. (2013)",
        fontsize=10, fontweight="bold", fontname=FIG_FONT)
    ax1.legend(loc="upper left", fontsize=7.5, framealpha=0.92, ncol=3)
    ax1.grid(axis="y", alpha=0.25, lw=0.5)

    ax1.annotate(
        "Modelled lines: equilibrium shift applied to observed C4 seasonal cycle.\n"
        "BACI observed: post-felling depth vs full pre-felling baseline; the baseline\n"
        "includes the wet 2015–16 years and 2015 scraping intervention, which inflate\n"
        "the apparent post-felling deepening (Section 4.6.4).\n"
        "Broadleaf: seasonally-varying β₂ (deciduous phenology) +\n"
        "15% annual-mean interception (Komatsu et al., 2011).\n"
        "C1 and C2 unaffected by any forest management scenario.",
        xy=(0.02, 0.03), xycoords="axes fraction", fontsize=7.0,
        color="dimgrey",
        bbox=dict(boxstyle="round,pad=0.35", fc="white", alpha=0.88))

    # ── Climate forcing panel ─────────────────────────────────────────────────
    width = 0.35
    ax2.bar(x - width/2, monthly_P  * 1000, width,
            color="steelblue", alpha=0.75, label="Mean P (mm)")
    ax2.bar(x + width/2, monthly_PET * 1000, width,
            color="tomato",    alpha=0.75, label="Mean PET (mm)")
    ax2.axvspan(5.5, 9.5, alpha=0.07, color="orange")
    ax2.set_xlim(0.5, 13.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(MONTHS, fontsize=9, fontname=FIG_FONT)
    ax2.set_ylabel("mm / month", fontsize=9, fontname=FIG_FONT)
    ax2.set_title("Mean Monthly Climate Forcing — RAF Valley 2005–2026",
                  fontsize=9, fontname=FIG_FONT)
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(axis="y", alpha=0.25, lw=0.5)

    fig.tight_layout(h_pad=2.5)
    fig.savefig(OUT_21_HYDROGRAPH, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_21_HYDROGRAPH.name}")

    # Print summary table
    print("\n  === Monthly depth below ground — scenario summary (m) ===")
    print(f"  {'Month':<5}", end="")
    for name in scenario_shifts:
        print(f"  {name[:14]:<14}", end="")
    print(f"  {'Observed':>8}")
    for m in range(12):
        print(f"  {MONTHS[m]:<5}", end="")
        for name, d in depths.items():
            print(f"  {d[m]:>14.3f}", end="")
        print(f"  {obs_monthly[m]:>8.3f}")

    print(f"\n  === Summer minimum (Aug, m below ground) ===")
    for name, d in depths.items():
        shift = obs_monthly[7] - d[7]
        print(f"  {name:<30}: {d[7]:.3f}  (shift vs baseline: {shift:>+.3f} m)")
    print(f"  {'BACI summer benchmark':<30}: {baci_summer[7]:.3f}")


# ============================================================================
# FIGURE 2 — SUMMER MINIMA DISTRIBUTIONS
# Five-group three-phase violin/strip plot
# Groups (spatial order, open warren → forest):
#   C1, C2, C3-interior, C3-adjacent, C4
# Phases: pre-scrape (2005–14), scraping era (2015–17), post-felling (2018+)
# C3 split at 550 m from C4 centroid — adjacent wells may show management signal
# ============================================================================

# C3 well lists — split by proximity to C4 centroid
SCRAPE_DATE  = "2015-04-01"   # April 2015 scraping
FELL_DATE_21 = "2018-01-01"   # December 2017 clearfell


def _get_maod_monthly_21(w, df, dates, well_names, elev):
    """Return monthly maOD series for one well."""
    raw = get_well_monthly(w, df, dates, well_names)
    if raw is None:
        return None
    pt = elev[elev["well"] == w]["Pipe_Top_Elev"]
    if pt.empty:
        return None
    return pt.values[0] + raw


def _wells_summer_mins(well_list, df, dates, well_names, elev,
                       master, start=None, end=None):
    """
    Return array of annual summer minimum depths (m below ground)
    for a list of wells over an optional date range.
    """
    SUMMER = [6, 7, 8, 9]
    well_depths = []
    for w in well_list:
        maod = _get_maod_monthly_21(w, df, dates, well_names, elev)
        dem_r = elev[elev["well"] == w]["DEM_Ground_Elev"]
        if maod is None or dem_r.empty:
            continue
        depth = dem_r.values[0] - maod
        if start:
            depth = depth[depth.index >= start]
        if end:
            depth = depth[depth.index < end]
        well_depths.append(depth)
    if not well_depths:
        return np.array([])
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        combined = pd.concat(well_depths, axis=1).mean(axis=1)
    mins = []
    for yr in sorted(combined.index.year.unique()):
        mask = ((combined.index.year == yr) &
                (combined.index.month.isin(SUMMER)))
        d = combined[mask].dropna()
        if len(d) >= 2:
            mins.append(float(d.max()))
    return np.array(mins)


def _cluster_summer_mins_21(cl, df, dates, well_names, elev,
                             master, start=None, end=None):
    wells = master[master["Cluster"] == cl]["well"].tolist()
    return _wells_summer_mins(wells, df, dates, well_names, elev,
                               master, start, end)


def plot_distributions(master, df, dates, well_names, elev, dpi=FIG_DPI):
    """
    Five-group three-phase violin/strip plot of observed annual summer
    minimum depths. Groups in spatial order: C1, C2, C3, C5, C4.
    C4 and C5 are both forested (Corsican pine); C4 is plotted last
    as it is typically the deepest. Three phases: pre-scrape (2005–14),
    scraping era (2015–17), post-felling (2018+). Pure observational —
    no modelling.
    """
    phases = [
        ("Pre-scrape\n2005–14",   None,        SCRAPE_DATE,  "o", 0.50),
        ("Scraping era\n2015–17", SCRAPE_DATE, FELL_DATE_21, "s", 0.38),
        ("Post-felling\n2018+",   FELL_DATE_21, None,        "^", 0.50),
    ]

    groups = [
        ("C1\nEastern\nlake-buffer",
         "#E69F00",
         lambda s, e: _cluster_summer_mins_21(1, df, dates, well_names,
                                               elev, master, s, e)),
        ("C2\nEastern\nmature dune",
         "#009E73",
         lambda s, e: _cluster_summer_mins_21(2, df, dates, well_names,
                                               elev, master, s, e)),
        ("C3\nWarren\ninterior",
         "#CC79A7",
         lambda s, e: _cluster_summer_mins_21(3, df, dates, well_names,
                                               elev, master, s, e)),
        ("C5\nCoastal\nforest",
         "#56B4E9",
         lambda s, e: _cluster_summer_mins_21(5, df, dates, well_names,
                                               elev, master, s, e)),
        ("C4\nMain\nforest",
         "#2166AC",
         lambda s, e: _cluster_summer_mins_21(4, df, dates, well_names,
                                               elev, master, s, e)),
    ]
    c4_phase_cols = ["#9ECAE1", "#2166AC", "#D55E00"]
    c5_phase_cols = ["#B3D9F2", "#56B4E9", "#E8A020"]

    group_centres = np.array([1.0, 2.6, 4.2, 5.8, 7.4])
    offsets       = np.array([-0.48, 0.0, 0.48])
    rng           = np.random.RandomState(42)

    fig, ax = plt.subplots(figsize=(12, 10.5), facecolor="white")
    fig.subplots_adjust(bottom=0.22, top=0.93, left=0.09, right=0.88)

    # Ecological zone shading
    for ylo, yhi, col in [
        (-0.3,      0,       "#1a7abf"),
        (0,         SD15b,   "#a8d8a8"),
        (SD15b,     SD16,    "#ffffb2"),
        (SD16,      SD16_REC,"#fd8d3c"),
        (SD16_REC,  2.8,     "#f4c2a1"),
    ]:
        ax.axhspan(ylo, yhi, alpha=0.15, color=col, zorder=0)

    # Threshold lines — labels inside plot, right-aligned
    for thresh, lbl, col in [
        (SD15b,    "SD15b 0.61 m",     "#005fa3"),
        (SD16,     "SD16 0.98 m",      "#a30000"),
        (SD16_REC, "SD16 rec 1.20 m",  "#4a0000"),
    ]:
        ax.axhline(thresh, color=col, lw=1.0, ls="--", alpha=0.85, zorder=1)
        ax.text(8.28, thresh + 0.04, lbl, fontsize=7.5, color=col,
                va="bottom", ha="right",
                bbox=dict(fc="white", alpha=0.7, edgecolor="none", pad=1))

    # Zone labels — left margin
    for y, lbl in [
        (-0.15, "Flooding"),      (0.30, "SD15b wet slack"),
        (0.80,  "SD16 dry slack"), (1.09, "SD16 recovery"),
        (1.90,  "Below recovery"),
    ]:
        ax.text(0.10, y, lbl, fontsize=6.5, color="dimgrey",
                va="center", style="italic")

    # Spatial gradient arrow
    ax.annotate("", xy=(7.85, -0.28), xytext=(0.15, -0.28),
                arrowprops=dict(arrowstyle="->", color="dimgrey",
                                lw=1.3, mutation_scale=12))
    ax.text(4.0, -0.36,
            "Open dune \u2192 Warren interior \u2192 Forest clusters",
            ha="center", fontsize=8, color="dimgrey", style="italic")

    # Draw violins and strips
    for gi, (grp_lbl, base_col, mins_fn) in enumerate(groups):
        gc     = group_centres[gi]
        is_c4  = "C4" in grp_lbl
        is_c5  = "C5" in grp_lbl

        for pi, (phase_lbl, start, end, mk, alpha) in enumerate(phases):
            pos = gc + offsets[pi]
            arr = mins_fn(start, end)
            col = (c4_phase_cols[pi] if is_c4
                   else c5_phase_cols[pi] if is_c5
                   else base_col)

            if len(arr) == 0:
                continue

            # Violin
            if len(arr) >= 4:
                vp = ax.violinplot(arr, positions=[pos], widths=0.40,
                                   showmedians=False, showextrema=False)
                for body in vp["bodies"]:
                    body.set_facecolor(col)
                    body.set_edgecolor("white")
                    body.set_alpha(alpha)

            # Strip
            jitter = rng.uniform(-0.08, 0.08, size=len(arr))
            ax.scatter(pos + jitter, arr, color=col, s=25, zorder=5,
                       edgecolors="white", lw=0.4, alpha=0.88, marker=mk)

            # Median
            ax.hlines(np.median(arr), pos - 0.16, pos + 0.16,
                      colors=col, lw=2.2, zorder=6)

            # Mean diamond
            ax.scatter([pos], [arr.mean()], marker="D", s=24,
                       color="white", edgecolors=col, lw=1.3, zorder=7)

            # ±1 SD bracket
            mn, sd = arr.mean(), arr.std() if len(arr) > 1 else 0
            if sd > 0:
                ax.vlines(pos + 0.22, mn - sd, mn + sd,
                          colors=col, lw=1.1, alpha=0.55, zorder=4)

            # n label
            ax.text(pos, min(arr) - 0.05, f"n={len(arr)}",
                    ha="center", va="top", fontsize=5.8, color=col)

        # Group label below axis
        ax.text(gc, 2.88, grp_lbl,
                ha="center", va="top", fontsize=8.5,
                fontweight="bold", color=base_col,
                multialignment="center")

    # Forest cluster bracket — C5 + C4 together
    ax.annotate("", xy=(7.84, 3.18), xytext=(5.36, 3.18),
                arrowprops=dict(arrowstyle="|-|", color="#2166AC",
                                lw=1.5, mutation_scale=4))
    ax.text(6.60, 3.23, "Forest clusters (Corsican pine canopy)",
            ha="center", fontsize=7.5, color="#2166AC", style="italic")

    # Phase labels — below C3 bracket, under each group
    for gi in range(len(groups)):
        gc = group_centres[gi]
        for pi, (phase_lbl, _, _, _, _) in enumerate(phases):
            pos = gc + offsets[pi]
            ax.text(pos, 3.38, phase_lbl,
                    ha="center", va="top", fontsize=6.2,
                    color="dimgrey", style="italic",
                    multialignment="center")

    # Cluster dividers
    for x_div in [1.84, 3.44, 5.04, 6.64]:
        ax.axvline(x_div, color="grey", lw=0.8, ls=":", alpha=0.35)

    ax.set_xlim(0.15, 8.5)
    ax.set_ylim(3.85, -0.45)
    ax.set_xticks([])
    ax.set_ylabel("Mean annual summer minimum depth below ground (m)",
                  fontsize=10, fontname=FIG_FONT)
    ax.set_title(
        "Summer Minimum Depth by Management Phase \u2014 All Clusters\n"
        "Newborough Warren 2005\u20132026  |  "
        "Ecological thresholds: Curreli et al. (2013)",
        fontsize=11, fontweight="bold", fontname=FIG_FONT)
    ax.grid(axis="y", alpha=0.2, lw=0.5)

    # Legend — upper right
    legend_elements = [
        Line2D([0],[0], marker="o", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7, label="Pre-scrape 2005\u201314"),
        Line2D([0],[0], marker="s", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7, label="Scraping era 2015\u201317"),
        Line2D([0],[0], marker="^", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7, label="Post-felling 2018+"),
        Line2D([0],[0], color="grey", lw=2.2, label="Median"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="white",
               markeredgecolor="grey", ms=6, label="Mean"),
        mpatches.Patch(facecolor="#a8d8a8", alpha=0.5,
                       label="SD15b (0\u20130.61 m)"),
        mpatches.Patch(facecolor="#ffffb2", alpha=0.5,
                       label="SD16 (0.61\u20130.98 m)"),
        mpatches.Patch(facecolor="#fd8d3c", alpha=0.5,
                       label="SD16 recovery"),
        mpatches.Patch(facecolor="#f4c2a1", alpha=0.5,
                       label="Below recovery"),
    ]
    ax.legend(handles=legend_elements, fontsize=7.5, loc="upper right",
              framealpha=0.92, ncol=2, bbox_to_anchor=(0.995, 0.995))

    # Compute C4 pre/post shift for the text box
    _c4_fn = None
    for grp_lbl, _, mins_fn in groups:
        if "C4" in grp_lbl:
            _c4_fn = mins_fn
            break
    if _c4_fn is not None:
        _c4_pre  = _c4_fn(None, FELL_DATE_21)
        _c4_post = _c4_fn(FELL_DATE_21, None)
        if len(_c4_pre) > 0 and len(_c4_post) > 0:
            _shift_summer = _c4_post.mean() - _c4_pre.mean()
            _shift_text = (
                f"C4 post-felling (orange) narrows\n"
                f"and shifts deeper by {abs(_shift_summer):.3f} m (summer mean)."
            )
        else:
            _shift_text = ""
    else:
        _shift_text = ""

    # Explanation box — at ~2.0 m level, clear of y axis
    ax.text(0.65, 2.02,
            "How to read this figure: Each violin shows the distribution of\n"
            "annual summer minimum depths \u2014 width indicates how many years\n"
            "fell at that depth (wider = more common). Each dot is one year.\n"
            "The bar is the median; the diamond is the mean; bracket = \u00b11 SD.\n"
            "Shapes distinguish phases (\u25cf=pre-scrape, \u25a0=scraping era,\n"
            "\u25b2=post-felling). Scraping era n=3 \u2014 interpret mean only.\n\n"
            "General deepening trend across all groups = background\n"
            f"climate drying signal. {_shift_text}",
            fontsize=7.2, color="dimgrey", va="top",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", alpha=0.92,
                      edgecolor="lightgrey"),
            zorder=10)

    fig.savefig(OUT_21_DISTRIBUTIONS, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_21_DISTRIBUTIONS.name}")

    # Print summary statistics and save CSV
    print("\n  === Summer minimum distributions — summary statistics ===")
    print(f"  {'Group':<28} {'Phase':<20} {'n':>4} {'Mean':>7} "
          f"{'SD':>7} {'%>SD16':>8}")
    print("  " + "-" * 76)
    import pandas as _pd
    dist_rows = []
    for gi, (grp_lbl, _, mins_fn) in enumerate(groups):
        for pi, (phase_lbl, start, end, _, _) in enumerate(phases):
            arr = mins_fn(start, end)
            if len(arr) == 0:
                continue
            p16 = 100 * (arr > SD16).sum() / len(arr)
            g = grp_lbl.replace("\n", " ")
            p = phase_lbl.replace("\n", " ")
            print(f"  {g:<28} {p:<20} {len(arr):>4} "
                  f"{arr.mean():>7.3f} {arr.std():>7.3f} {p16:>7.0f}%")
            dist_rows.append({
                "Group":          g,
                "Phase":          p,
                "Phase_start":    start or "record_start",
                "Phase_end":      end   or "record_end",
                "N_summers":      len(arr),
                "Mean_depth_m":   round(float(arr.mean()),  4),
                "Median_depth_m": round(float(np.median(arr)), 4),
                "SD_depth_m":     round(float(arr.std()),   4) if len(arr) > 1 else None,
                "Min_depth_m":    round(float(arr.min()),   4),
                "Max_depth_m":    round(float(arr.max()),   4),
                "Pct_below_SD16": round(p16, 1),
            })
    _pd.DataFrame(dist_rows).to_csv(OUT_21_DISTRIBUTIONS_CSV, index=False)
    print(f"  Saved: {OUT_21_DISTRIBUTIONS_CSV.name}")


# ============================================================================
# FIGURE 3 — SCRAPING TREATMENT AND CONTROL WELLS BY ERA
# ============================================================================

SCRAPE_DATE_21  = "2015-04-01"   # April 2015 scraping
SCRAPE2_DATE_21 = "2023-10-01"   # October 2023 re-scraping

SCRAPING_WELLS = {
    "CEH36\n(scraped)": "ceh36",
    "CEH18\n(scraped)": "ceh18",
    "CEH21\n(scraped)": "ceh21",
    "CEH4\n(control)":  "ceh4",
}
SCRAPING_COLOURS = {
    "CEH36\n(scraped)": "#2166AC",
    "CEH18\n(scraped)": "#4DAC26",
    "CEH21\n(scraped)": "#8B0AA5",
    "CEH4\n(control)":  "#888888",
}


def _well_summer_mins_era(w, df, dates, well_names, elev,
                           start=None, end=None):
    """Annual summer minimum depths for a single well over an era."""
    SUMMER = [6, 7, 8, 9]
    raw = get_well_monthly(w, df, dates, well_names)
    if raw is None:
        return np.array([])
    pt  = elev[elev["well"] == w]["Pipe_Top_Elev"]
    dem = elev[elev["well"] == w]["DEM_Ground_Elev"]
    if pt.empty or dem.empty:
        return np.array([])
    maod  = pt.values[0] + raw
    depth = dem.values[0] - maod
    if start:
        depth = depth[depth.index >= start]
    if end:
        depth = depth[depth.index < end]
    mins = []
    for yr in sorted(depth.index.year.unique()):
        mask = ((depth.index.year == yr) &
                (depth.index.month.isin(SUMMER)))
        d = depth[mask].dropna()
        if len(d) >= 2:
            mins.append(float(d.max()))
    return np.array(mins)


def plot_scraping_eras(df, dates, well_names, elev, dpi=FIG_DPI):
    """
    Strip/dot plot of annual summer minimum depths for scraping treatment
    wells (CEH36, CEH18, CEH21) and control well (CEH4) across four
    management eras. Each point is one summer. Open symbol = era mean.

    Scraping dates:
      CEH36 — scraped April 2015 and October 2023
      CEH18, CEH21 — scraped October 2023 only
      CEH4  — control, not scraped

    Coloured vertical bands mark each well's specific scraping era.
    The 2015–17 era for CEH18/CEH21 is unscraped monitoring.
    """
    import matplotlib.patches as mpatches

    SCRAPE36_DATE = "2015-04-01"

    eras = [
        ("Pre-2015",              None,          SCRAPE36_DATE, "o"),
        ("2015\u201317",          SCRAPE36_DATE, FELL_DATE_21,  "s"),
        ("Post-fell\n2018\u201323", FELL_DATE_21, SCRAPE2_DATE_21, "^"),
        ("Post-rescrape\n2024+",  SCRAPE2_DATE_21, None,         "D"),
    ]

    wells_cfg = [
        ("CEH36",          "ceh36", "#2166AC"),
        ("CEH18",          "ceh18", "#4DAC26"),
        ("CEH21",          "ceh21", "#8B0AA5"),
        ("CEH4\n(control)","ceh4",  "#888888"),
    ]
    well_positions = [1.0, 2.0, 3.0, 3.9]
    offsets = [-0.30, -0.10, +0.10, +0.30]
    rng = np.random.RandomState(42)

    fig, ax = plt.subplots(figsize=(10, 7.5), facecolor="white")
    fig.subplots_adjust(bottom=0.18, top=0.91, left=0.09, right=0.88)

    # Ecological zones
    for ylo, yhi, col in [
        (-0.3,      0,        "#1a7abf"),
        (0,         SD15b,    "#a8d8a8"),
        (SD15b,     SD16,     "#ffffb2"),
        (SD16,      SD16_REC, "#fd8d3c"),
        (SD16_REC,  1.7,      "#f4c2a1"),
    ]:
        ax.axhspan(ylo, yhi, alpha=0.15, color=col, zorder=0)

    # Threshold lines — labels just inside right spine using axes transform
    for thresh, lbl, col in [
        (SD15b,    "SD15b 0.61 m",    "#005fa3"),
        (SD16,     "SD16 0.98 m",     "#a30000"),
        (SD16_REC, "SD16 rec 1.20 m", "#4a0000"),
    ]:
        ax.axhline(thresh, color=col, lw=0.9, ls="--", alpha=0.8, zorder=1)
        ax.annotate(lbl, xy=(1.0, thresh),
                    xycoords=("axes fraction", "data"),
                    fontsize=7.5, color=col, va="center", ha="right",
                    xytext=(-4, 4), textcoords="offset points",
                    bbox=dict(fc="white", alpha=0.75, edgecolor="none", pad=1))

    # Zone labels left
    for y, lbl in [
        (-0.15, "Flooding"),       (0.30, "SD15b wet slack"),
        (0.80,  "SD16 dry slack"), (1.09, "SD16 recovery"),
        (1.48,  "Below recovery"),
    ]:
        ax.text(0.44, y, lbl, fontsize=6.5, color="dimgrey",
                va="center", style="italic")

    # Control shading and divider
    ax.axvspan(3.52, 4.28, alpha=0.06, color="grey")
    ax.axvline(3.42, color="grey", lw=0.8, ls=":", alpha=0.4)

    # Well-specific scraping era bands
    # CEH36: era 2 (2015-17) = offsets[1]
    x36 = well_positions[0] + offsets[1]
    ax.axvspan(x36 - 0.10, x36 + 0.10, alpha=0.18, color="#2166AC", zorder=0)
    # CEH18 and CEH21: era 4 (2024+) = offsets[3]
    for wi, wcol in [(1, "#4DAC26"), (2, "#8B0AA5")]:
        x4 = well_positions[wi] + offsets[3]
        ax.axvspan(x4 - 0.10, x4 + 0.10, alpha=0.18, color=wcol, zorder=0)

    # Draw data for each well
    for w_pos, (well_lbl, well_id, col) in zip(well_positions, wells_cfg):
        means = []
        for pi, (era_lbl, start, end, mk) in enumerate(eras):
            arr = _well_summer_mins_era(well_id, df, dates, well_names, elev,
                                        start, end)
            x = w_pos + offsets[pi]
            if len(arr) == 0:
                means.append(None)
                continue
            jitter = rng.uniform(-0.04, 0.04, size=len(arr))
            ax.scatter(x + jitter, arr, color=col, s=50, marker=mk,
                       edgecolors="white", lw=0.5, zorder=5, alpha=0.85)
            mn = arr.mean()
            sd = arr.std() if len(arr) > 1 else 0
            ax.scatter([x], [mn], marker=mk, s=85, color="white",
                       edgecolors=col, lw=2.0, zorder=7)
            if sd > 0:
                ax.vlines(x, mn - sd, mn + sd,
                          colors=col, lw=1.5, alpha=0.6, zorder=4)
            means.append(mn)
            ax.text(x, min(arr) - 0.04, f"n={len(arr)}",
                    ha="center", va="top", fontsize=6, color=col)

        # Connect era means
        valid = [(w_pos + offsets[pi], m)
                 for pi, m in enumerate(means) if m is not None]
        if len(valid) >= 2:
            xs, ys = zip(*valid)
            ax.plot(xs, ys, color=col, lw=1.2, ls="-", alpha=0.45, zorder=3)

        # Well label below axes
        ax.text(w_pos, 1.82, well_lbl,
                ha="center", fontsize=9.5, fontweight="bold", color=col,
                multialignment="center")

    ax.set_xlim(0.4, 4.75)
    ax.set_ylim(2.05, -0.55)
    ax.set_xticks([])
    ax.set_ylabel("Summer minimum depth below ground (m)", fontsize=10,
                  fontname=FIG_FONT)
    ax.set_title(
        "Summer Minimum Depth \u2014 Scraping Treatment and Control Wells\n"
        "Newborough Warren  |  CEH36 scraped Apr 2015 & Oct 2023  |  "
        "CEH18 & CEH21 scraped Oct 2023  |  Clearfell Dec 2017",
        fontsize=9.5, fontweight="bold", fontname=FIG_FONT)
    ax.grid(axis="y", alpha=0.2, lw=0.5)

    # Legend — upper left, starting inline with CEH36
    legend_elements = [
        Line2D([0],[0], marker="o", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7, label="Pre-2015 monitoring"),
        Line2D([0],[0], marker="s", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7,
               label="Post-scrape CEH36 2015\u201317"),
        Line2D([0],[0], marker="^", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7, label="Post-felling 2018\u201323"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7,
               label="Post-scrape CEH18 & CEH21 2024+"),
        Line2D([0],[0], marker="o", color="w", markerfacecolor="white",
               markeredgecolor="dimgrey", ms=8, label="Open symbol = era mean"),
        mpatches.Patch(facecolor="#2166AC", alpha=0.4,
                       label="CEH36 scraped Apr 2015"),
        mpatches.Patch(facecolor="#4DAC26", alpha=0.4,
                       label="CEH18 scraped Oct 2023"),
        mpatches.Patch(facecolor="#8B0AA5", alpha=0.4,
                       label="CEH21 scraped Oct 2023"),
    ]
    ax.legend(handles=legend_elements, fontsize=7.2, loc="upper left",
              framealpha=0.92, ncol=1, bbox_to_anchor=(0.14, 0.99))

    # Annotation box — upper right
    ax.text(0.99, 0.99,
            "Each point = one summer (Jun\u2013Sep).\n"
            "Open symbol = era mean; bar = \u00b11 SD.\n"
            "Shaded columns = well-specific scraping eras.\n"
            "CEH18 & CEH21 not scraped in 2015;\n"
            "  their 2015\u201317 era is unscraped monitoring.\n"
            "CEH4: progressive deepening =\n"
            "  background climate drying signal.",
            fontsize=7.2, color="dimgrey", va="top", ha="right",
            transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", alpha=0.92,
                      edgecolor="lightgrey"),
            zorder=10)

    fig.savefig(OUT_21_SCRAPING, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_21_SCRAPING.name}")

    # Export era means and SDs to CSV for reporting verification
    rows = []
    for w_pos, (well_lbl, well_id, col) in zip(well_positions, wells_cfg):
        for pi, (era_lbl, start, end, mk) in enumerate(eras):
            arr = _well_summer_mins_era(well_id, df, dates, well_names, elev,
                                        start, end)
            rows.append({
                "Well":     well_lbl.replace("\n", " ").strip(),
                "Well_ID":  well_id,
                "Era":      era_lbl.replace("\n", " ").strip(),
                "Era_start": start or "record_start",
                "Era_end":   end   or "record_end",
                "N_summers": len(arr),
                "Mean_depth_m": round(float(arr.mean()), 4) if len(arr) > 0 else None,
                "SD_depth_m":   round(float(arr.std()),  4) if len(arr) > 1 else None,
                "Min_depth_m":  round(float(arr.min()),  4) if len(arr) > 0 else None,
                "Max_depth_m":  round(float(arr.max()),  4) if len(arr) > 0 else None,
            })
    import pandas as _pd
    era_df = _pd.DataFrame(rows)
    era_df.to_csv(OUT_21_SCRAPING_CSV, index=False)
    print(f"  Saved: {OUT_21_SCRAPING_CSV.name}")


# ============================================================================
# FIGURE 4 — BACI ZONE SUMMER MINIMUM VIOLIN
# ============================================================================

# BACI experimental zone definitions
BACI_ZONE_WELLS = {
    "Core impact\n(FE2, FE4, WMC3)":
        ["fe2", "fe4", "wmc3"],
    "Edge zone\n(FE1, FE3, CEH31, LIS1,\nCEH20, CEH30, CEH16, NW8B)":
        ["fe1", "fe3", "ceh31", "lis1", "ceh20", "ceh30", "ceh16", "nw8b"],
    "Plantation controls\n(CEH32, CEH34, CEH33, NW10, CEH19)":
        ["ceh32", "ceh34", "ceh33", "nw10", "ceh19"],
    "Open warren controls\n(CEH9, NW7, NW6)":
        ["ceh9", "nw7", "nw6"],
}
BACI_ZONE_COLOURS = {
    "Core impact\n(FE2, FE4, WMC3)":                                   "#D73027",
    "Edge zone\n(FE1, FE3, CEH31, LIS1,\nCEH20, CEH30, CEH16, NW8B)":"#F46D43",
    "Plantation controls\n(CEH32, CEH34, CEH33, NW10, CEH19)":         "#4DAC26",
    "Open warren controls\n(CEH9, NW7, NW6)":                          "#888888",
}


def _zone_summer_mins(wells, df, dates, well_names, elev, start=None, end=None):
    """Zone-mean annual summer minimum depths."""
    SUMMER = [6, 7, 8, 9]
    well_depths = []
    for w in wells:
        raw = get_well_monthly(w, df, dates, well_names)
        if raw is None:
            continue
        pt  = elev[elev["well"] == w]["Pipe_Top_Elev"]
        dem = elev[elev["well"] == w]["DEM_Ground_Elev"]
        if pt.empty or dem.empty:
            continue
        depth = dem.values[0] - (pt.values[0] + raw)
        if start:
            depth = depth[depth.index >= start]
        if end:
            depth = depth[depth.index < end]
        well_depths.append(depth)
    if not well_depths:
        return np.array([])
    combined = pd.concat(well_depths, axis=1).mean(axis=1)
    mins = []
    for yr in sorted(combined.index.year.unique()):
        mask = ((combined.index.year == yr) &
                (combined.index.month.isin(SUMMER)))
        d = combined[mask].dropna()
        if len(d) >= 2:
            mins.append(float(d.max()))
    return np.array(mins)


def plot_baci_zone_violin(df, dates, well_names, elev, dpi=FIG_DPI):
    """
    Three-phase violin plot of annual summer minimum depths by BACI
    experimental zone: pre-2015 baseline, 2015-17 era, post-felling 2018+.

    Core impact pre-2015 violin is hatched — WMC3 only (FE wells installed
    August 2015, insufficient pre-felling record for other core wells).
    """
    BACI_PHASES = [
        ("Pre-2015",          None,         SCRAPE_DATE_21, "o", 0.35),
        ("2015\u201317",      SCRAPE_DATE_21, FELL_DATE_21,  "s", 0.45),
        ("Post-fell\n2018+",  FELL_DATE_21, None,           "^", 0.55),
    ]
    offsets        = [-0.42, 0.0, +0.42]
    group_centres  = np.array([1.0, 2.6, 4.2, 5.8])
    rng            = np.random.RandomState(42)

    fig, ax = plt.subplots(figsize=(13, 8.0), facecolor="white")
    fig.subplots_adjust(bottom=0.22, top=0.91, left=0.09, right=0.88)

    # Ecological zone backgrounds
    for ylo, yhi, col in [
        (-0.3,      0,        "#1a7abf"),
        (0,         SD15b,    "#a8d8a8"),
        (SD15b,     SD16,     "#ffffb2"),
        (SD16,      SD16_REC, "#fd8d3c"),
        (SD16_REC,  2.2,      "#f4c2a1"),
    ]:
        ax.axhspan(ylo, yhi, alpha=0.15, color=col, zorder=0)

    # Threshold lines — flush to right spine
    for thresh, lbl, col in [
        (SD15b,    "SD15b 0.61 m",    "#005fa3"),
        (SD16,     "SD16 0.98 m",     "#a30000"),
        (SD16_REC, "SD16 rec 1.20 m", "#4a0000"),
    ]:
        ax.axhline(thresh, color=col, lw=0.9, ls="--", alpha=0.8, zorder=1)
        ax.annotate(lbl, xy=(1.0, thresh),
                    xycoords=("axes fraction", "data"),
                    fontsize=7.5, color=col, va="center", ha="right",
                    xytext=(-4, 4), textcoords="offset points",
                    bbox=dict(fc="white", alpha=0.75, edgecolor="none", pad=1))

    # Zone labels left
    for y, lbl in [
        (-0.15, "Flooding"),       (0.30, "SD15b wet slack"),
        (0.80,  "SD16 dry slack"), (1.09, "SD16 recovery"),
        (1.70,  "Below recovery"),
    ]:
        ax.text(0.44, y, lbl, fontsize=6.5, color="dimgrey",
                va="center", style="italic")

    # Draw data for each zone
    for gc, (zone_lbl, wells) in zip(group_centres, BACI_ZONE_WELLS.items()):
        col     = BACI_ZONE_COLOURS[zone_lbl]
        is_core = "Core" in zone_lbl

        for pi, (phase_lbl, start, end, mk, alpha) in enumerate(BACI_PHASES):
            arr = _zone_summer_mins(wells, df, dates, well_names, elev,
                                    start, end)
            pos = gc + offsets[pi]
            if len(arr) == 0:
                continue

            if len(arr) >= 4:
                vp = ax.violinplot(arr, positions=[pos], widths=0.60,
                                   showmedians=False, showextrema=False)
                for body in vp["bodies"]:
                    body.set_facecolor(col)
                    body.set_edgecolor("white")
                    if is_core and pi == 0:
                        body.set_hatch("///")
                        body.set_alpha(0.4)
                    else:
                        body.set_alpha(alpha * 0.8)

            jitter = rng.uniform(-0.09, 0.09, size=len(arr))
            ax.scatter(pos + jitter, arr, color=col, s=32, zorder=5,
                       edgecolors="white", lw=0.4, alpha=0.9, marker=mk)
            ax.hlines(np.median(arr), pos - 0.18, pos + 0.18,
                      colors=col, lw=2.2, zorder=6)
            ax.scatter([pos], [arr.mean()], marker="D", s=26,
                       color="white", edgecolors=col, lw=1.4, zorder=7)
            mn = arr.mean()
            sd = arr.std() if len(arr) > 1 else 0
            if sd > 0:
                ax.vlines(pos + 0.23, mn - sd, mn + sd,
                          colors=col, lw=1.1, alpha=0.55, zorder=4)
            ax.text(pos, min(arr) - 0.05, f"n={len(arr)}",
                    ha="center", va="top", fontsize=6, color=col)

        # Zone label below axes
        ax.text(gc, 2.12, zone_lbl,
                ha="center", va="top", fontsize=8,
                fontweight="bold", color=col,
                multialignment="center", fontname=FIG_FONT)

    # Phase labels
    for pi, (phase_lbl, _, _, _, _) in enumerate(BACI_PHASES):
        x_mid = np.mean(group_centres + offsets[pi])
        ax.text(x_mid, 1.97, phase_lbl,
                ha="center", va="top", fontsize=7.5,
                color="dimgrey", style="italic",
                multialignment="center")

    # Zone dividers
    for x_div in [1.82, 3.42, 5.02]:
        ax.axvline(x_div, color="grey", lw=0.7, ls=":", alpha=0.35)

    ax.set_xlim(0.3, 6.7)
    ax.set_ylim(2.30, -0.50)
    ax.set_xticks([])
    ax.set_ylabel("Mean annual summer minimum depth below ground (m)",
                  fontsize=10, fontname=FIG_FONT)
    ax.set_title(
        "Summer Minimum Depth by BACI Experimental Zone\n"
        "Newborough Warren  |  Pre-2015, 2015\u201317, Post-felling 2018+  |  "
        "Curreli et al. (2013) ecological thresholds",
        fontsize=10, fontweight="bold", fontname=FIG_FONT)
    ax.grid(axis="y", alpha=0.2, lw=0.5)

    # Legend — upper right, top at y=0.97
    import matplotlib.patches as mpatches_local
    legend_elements = [
        Line2D([0],[0], marker="o", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7, label="Pre-2015"),
        Line2D([0],[0], marker="s", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7, label="2015\u201317"),
        Line2D([0],[0], marker="^", color="w", markerfacecolor="dimgrey",
               markeredgecolor="dimgrey", ms=7, label="Post-felling 2018+"),
        Line2D([0],[0], color="grey", lw=2.2, label="Median"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="white",
               markeredgecolor="grey", ms=6, label="Mean"),
        mpatches_local.Patch(facecolor="#a8d8a8", alpha=0.5,
                             label="SD15b (0\u20130.61 m)"),
        mpatches_local.Patch(facecolor="#ffffb2", alpha=0.5,
                             label="SD16 (0.61\u20130.98 m)"),
        mpatches_local.Patch(facecolor="#fd8d3c", alpha=0.5,
                             label="SD16 recovery"),
        mpatches_local.Patch(facecolor="#f4c2a1", alpha=0.5,
                             label="Below recovery"),
    ]
    ax.legend(handles=legend_elements, fontsize=7.5, loc="upper right",
              framealpha=0.92, ncol=2, bbox_to_anchor=(0.995, 0.97))

    # Annotation box — upper left, top at same y as legend
    ax.text(0.01, 0.97,
            "Each point = one summer (Jun\u2013Sep). "
            "Median bar; diamond = mean; bar = \u00b11 SD.\n"
            "Core impact pre-2015 violin (hatched) = WMC3 only "
            "(FE wells not installed until Aug 2015).\n"
            "Core impact: FE2, FE4, WMC3.\n"
            "Edge zone: FE1, FE3, CEH31, LIS1, CEH20, CEH30, CEH16, NW8B.\n"
            "Plantation controls: CEH32, CEH34, CEH33, NW10, CEH19.\n"
            "Open warren controls: CEH9, NW7, NW6.\n"
            "All eight control wells = BACI regional control pool (Section 3.5.5).",
            fontsize=7.2, color="dimgrey", va="top", ha="left",
            transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", alpha=0.92,
                      edgecolor="lightgrey"),
            zorder=10)

    fig.savefig(OUT_21_BACI_VIOLIN, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUT_21_BACI_VIOLIN.name}")

    # Summary statistics and CSV export
    print(f"\n  {'Zone':<22} {'Phase':<16} {'n':>4} "
          f"{'Mean':>7} {'SD':>7}")
    print("  " + "-" * 60)
    import pandas as _pd
    baci_rows = []
    for zone_lbl, wells in BACI_ZONE_WELLS.items():
        for phase_lbl, start, end, _, _ in BACI_PHASES:
            arr = _zone_summer_mins(wells, df, dates, well_names, elev,
                                    start, end)
            if len(arr) > 0:
                z = zone_lbl.replace("\n", " ")[:22]
                p = phase_lbl.replace("\n", " ")
                print(f"  {z:<22} {p:<16} {len(arr):>4} "
                      f"{arr.mean():>7.3f} {arr.std():>7.3f}")
                baci_rows.append({
                    "Zone":          z,
                    "Phase":         p,
                    "Phase_start":   start or "record_start",
                    "Phase_end":     end   or "record_end",
                    "N_summers":     len(arr),
                    "Mean_depth_m":  round(float(arr.mean()),     4),
                    "Median_depth_m":round(float(np.median(arr)), 4),
                    "SD_depth_m":    round(float(arr.std()),      4) if len(arr) > 1 else None,
                    "Min_depth_m":   round(float(arr.min()),      4),
                    "Max_depth_m":   round(float(arr.max()),      4),
                })
    _pd.DataFrame(baci_rows).to_csv(OUT_21_BACI_CSV, index=False)
    print(f"  Saved: {OUT_21_BACI_CSV.name}")


# ============================================================================
# MAIN
# ============================================================================

def main(preview=False):
    dpi = 150 if preview else FIG_DPI
    make_all_dirs()

    print("\n=== 21_forestry_scenarios.py ===")
    print(f"  DPI: {dpi}  ({'preview' if preview else 'publication'})")

    print("\n[1/5] Loading data...")
    master, elev, reg, climate = load_data()
    print(f"  Master: {len(master)} wells  |  "
          f"Climate: {climate.index[0].date()} to {climate.index[-1].date()}")

    print("\n[2/5] Building scenarios...")
    scenario_shifts, monthly_P, monthly_PET, b1, b2, b3 = build_scenarios(
        master, climate)
    obs_monthly, c4_dem = get_observed_seasonal_cycle(reg, elev, master)
    obs_c1 = get_cluster_obs_cycle(1, reg, elev, master)
    obs_c2 = get_cluster_obs_cycle(2, reg, elev, master)
    print(f"  C4 mean DEM: {c4_dem:.2f} m AOD")
    print(f"  β₁={b1:.4f}  β₂={b2:.4f}  β₃={b3:.4f}")
    print(f"  Scenarios: {list(scenario_shifts.keys())}")

    print("\n[3/5] Plotting hydrograph figure...")
    plot_hydrograph(scenario_shifts, obs_monthly, monthly_P, monthly_PET,
                    obs_c1, obs_c2, dpi=dpi)

    print("\n[4/5] Loading raw well data...")
    df, dates, well_names = load_raw_well_data()

    print("\n[4/5] Plotting distributions figure...")
    plot_distributions(master, df, dates, well_names, elev, dpi=dpi)

    print("\n[5/5] Plotting scraping eras figure...")
    plot_scraping_eras(df, dates, well_names, elev, dpi=dpi)

    print("\n[5/5] Plotting BACI zone violin figure...")
    plot_baci_zone_violin(df, dates, well_names, elev, dpi=dpi)

    print("\n=== Script 21 complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script 21 \u2014 Forest management scenario analysis")
    parser.add_argument("--preview", action="store_true",
                        help="Render at 150 dpi for quick preview")
    args = parser.parse_args()
    main(preview=args.preview)
