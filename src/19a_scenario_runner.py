"""
19a_scenario_runner.py
======================
Scenario comparison wrapper for script 19 (Spatial Groundwater Analysis).

For each scenario defined in SCENARIOS:
  1. Runs main() from 19_spatial_groundwater.py with the scenario redirected
     to a dedicated output subfolder
  2. Saves all standard script 19 figures to that subfolder
  3. After all scenarios complete, generates difference maps comparing each
     scenario to the baseline

Output structure
----------------
outputs/
  19_spatial_groundwater/
    baseline/          ← standard script 19 baseline output
    forest_removal/    ← full clearfell scenario
    forest_thinning/   ← 50% thinning scenario
    species_change/    ← broadleaf conversion scenario
    climate_dry/       ← −10% rainfall, +10% PET
    climate_wet/       ← +10% rainfall, −5% PET
    difference_maps/   ← scenario minus baseline comparison figures

Usage
-----
  python 19a_scenario_runner.py          # run all scenarios
  python 19a_scenario_runner.py --diff-only  # regenerate difference maps only
"""

import sys
import argparse
import shutil
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, SymLogNorm
from matplotlib.lines import Line2D

# ── Ensure src/ is on path ────────────────────────────────────────────────────
SRC_DIR = Path(__file__).parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.paths import OUT_DIR
import importlib

# ── Scenario definitions ──────────────────────────────────────────────────────
# Each entry: (scenario_key, subfolder_name, params_dict, display_label)
SCENARIOS = [
    (
        "baseline",
        "baseline",
        {},
        "Baseline (2005–2026 observed mean)",
    ),
    (
        "forest_removal",
        "forest_removal",
        {"beta2_increase_fraction": 0.15},
        "Full clearfell (β₂ ×1.15, interception removed)",
    ),
    (
        "forest_thinning",
        "forest_thinning",
        {"thinning_fraction": 0.5, "beta2_increase_fraction": 0.15},
        "Forest thinning — 50% of removal effect",
    ),
    (
        "species_change",
        "species_change",
        {"winter_recharge_reduction": 0.10},
        "Broadleaf conversion (β₁ ×0.90 in autumn)",
    ),
    (
        "climate_change",
        "climate_dry",
        {"delta_P_mm": -89, "delta_PET_mm": +54},   # −10%, +10% of site means
        "Climate change — dry (ΔP −10%, ΔPET +10%)",
    ),
    (
        "climate_change",
        "climate_wet",
        {"delta_P_mm": +89, "delta_PET_mm": -27},   # +10%, −5%
        "Climate change — wet (ΔP +10%, ΔPET −5%)",
    ),
]

# Figures that are scenario-sensitive (head, flux, water balance, depth, winter)
# Thickness, beta fields and residual comparison don't change between scenarios
SCENARIO_SENSITIVE_FIGS = [
    "19_head_surface_mean.png",
    "19_head_surface_seasonal.png",
    "19_water_balance.png",
    "19_lateral_flux.png",
    "19_storage_change.png",
    "19_depth_to_watertable.png",
    "19_winter_flooding.png",
    "19_head_surface_mean.csv",
    "19_water_balance_summary.csv",
]

# DPI and figure constants — match script 19
FIG_DPI        = 300
FIG_SINGLE_W   = 7.09
FIG_SINGLE_H   = 5.8
FIG_TWO_PANEL_W = 14.0
FIG_TWO_PANEL_H = 5.8
FIG_THREE_W     = 14.0
FIG_THREE_H     = 5.2
FIG_FOUR_W      = 18.0
FIG_FOUR_H      = 5.0
FIG_FONT_TITLE = 9
FIG_FONT_LABEL = 8
FIG_FONT_TICK  = 7
FIG_FONT_ANNOT = 6
FIG_FONT_CB    = 7


# ============================================================================
# SCENARIO RUNNER
# ============================================================================

def run_scenario(scenario_key, subfolder, params, label, base_dir, mod):
    """
    Run script 19 main() for one scenario, directing all outputs to a
    dedicated subfolder via the output_dir argument. Returns the subfolder Path.
    """
    scenario_dir = base_dir / subfolder
    scenario_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"  SCENARIO: {label}")
    print(f"  Output:   {scenario_dir}")
    print(f"{'='*70}")

    mod.main(scenario=scenario_key,
             scenario_params=params,
             output_dir=scenario_dir)

    return scenario_dir


# ── Per-cluster equilibrium head shifts (Δh_eq, m) ───────────────────────────
# Derived analytically from SSM: h_eq = (β₁·P_eff − β₂·PET) / β₃
# Forest scenarios only affect C4; climate scenarios affect all clusters.
# Species_change uses broadleaf interception (15%) not zero.
# Positive shift = deeper water table (drier). Negative = shallower (wetter).
SCENARIO_SHIFTS = {
    "baseline":        {"C1":  0.000, "C2":  0.000, "C3":  0.000, "C4":  0.000},
    "forest_removal":  {"C1":  0.000, "C2":  0.000, "C3":  0.000, "C4": +0.145},
    "forest_thinning": {"C1":  0.000, "C2":  0.000, "C3":  0.000, "C4": +0.073},
    "species_change":  {"C1":  0.000, "C2":  0.000, "C3":  0.000, "C4": +0.003},  # +ve: broadleaf intercepts less than pine annually (15% vs 24%)
    "climate_dry":     {"C1": +0.112, "C2": +0.156, "C3": +0.195, "C4": +0.219},
    "climate_wet":     {"C1": -0.079, "C2": -0.109, "C3": -0.133, "C4": -0.135},
}

# Observed seasonal cycle (mean monthly depth below ground, upstand-corrected)
# from 03_regional_averages.csv — negative = below ground, positive = flooding
# Positive convention: depth below ground in metres (deeper = larger positive value)
# Flooding = 0 or negative. Converted from the negative upstand-corrected records.
SEASONAL_CYCLE = {
    "C1": [0.083, 0.108, 0.166, 0.314, 0.519, 0.676, 0.748, 0.778, 0.810,
           0.616, 0.380, 0.261],
    "C2": [0.250, 0.270, 0.297, 0.365, 0.593, 0.761, 0.847, 0.923, 1.001,
           0.860, 0.622, 0.494],
    "C3": [0.691, 0.664, 0.749, 0.756, 0.950, 1.097, 1.137, 1.190, 1.262,
           1.242, 1.020, 0.922],
    "C4": [1.294, 1.189, 1.254, 1.134, 1.356, 1.529, 1.531, 1.607, 1.702,
           1.806, 1.620, 1.566],
}
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]
CLUSTER_COLOURS_SCEN = {
    "C1": "#E69F00", "C2": "#009E73", "C3": "#CC79A7", "C4": "#D55E00"
}
CLUSTER_LABELS_SCEN = {
    "C1": "C1 Eastern lake-buffer",
    "C2": "C2 Eastern mature dune",
    "C3": "C3 Western mature dune",
    "C4": "C4 Forest",
}


# ============================================================================
# DIFFERENCE MAPS
# ============================================================================

def load_head_csv(scenario_dir):
    """Load 19_head_surface_mean.csv from a scenario directory."""
    csv = scenario_dir / "19_head_surface_mean.csv"
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    return df


# Forest scenarios — use analytical per-cluster equilibrium shift
# The PDE solver dilutes forest-zone β changes across the whole grid via IDW,
# producing near-zero differences. The analytical approach applies the correct
# per-well equilibrium shift directly within the forest cluster.
FOREST_SCENARIOS = {"forest_removal", "forest_thinning", "species_change"}


def compute_analytical_delta_head(subfolder, df_base, base_dir):
    """
    Compute Δhead for forest scenarios using the per-cluster analytical
    equilibrium shift from SCENARIO_SHIFTS. Shifts are applied only to
    cells whose IDW head is dominated by C4 wells (approximated by spatial
    proximity to C4 well locations).

    Returns (grid_x, grid_y, delta_head_2d).
    """
    E_vals = np.sort(df_base["Easting"].unique())
    N_vals = np.sort(df_base["Northing"].unique())
    grid_x, grid_y = np.meshgrid(E_vals, N_vals)

    shifts = SCENARIO_SHIFTS.get(subfolder, {})
    # For forest scenarios only C4 has a non-zero shift
    # Reconstruct which grid cells are "in" C4 by loading the baseline
    # head CSV and the water balance summary
    wb_csv = base_dir / "baseline" / "19_water_balance_summary.csv"
    if not wb_csv.exists():
        return None, None, None

    wb = pd.read_csv(wb_csv)
    c4_wells = wb[wb["cluster"] == 4][["E","N"]].values

    if len(c4_wells) == 0:
        return None, None, None

    # For each grid cell, compute distance to nearest C4 well
    # and nearest non-C4 well — assign C4 zone where C4 is closer
    all_wells = wb.dropna(subset=["cluster"])[["E","N","cluster"]].values
    flat = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    from scipy.spatial import cKDTree
    tree_c4  = cKDTree(c4_wells)
    tree_all = cKDTree(all_wells[:, :2])

    d_c4,  _ = tree_c4.query(flat,  k=1)
    d_all, i = tree_all.query(flat, k=1)
    nearest_cluster = all_wells[i, 2]

    # Grid cells where nearest well is C4
    c4_mask_flat = (nearest_cluster == 4)
    c4_shift     = shifts.get("C4", 0.0)

    delta_flat = np.where(c4_mask_flat, c4_shift, 0.0)
    delta_2d   = delta_flat.reshape(grid_x.shape)

    return grid_x, grid_y, delta_2d


def compute_pde_delta_head(base_dir, subfolder, mod):
    """
    Compute Δhead = h_scenario - h_baseline.

    Strategy:
    - Forest scenarios (forest_removal, forest_thinning, species_change):
        Use analytical per-cluster equilibrium shift applied spatially
        to the C4 zone. The PDE solver dilutes forest β changes across
        the whole grid via IDW interpolation, giving near-zero differences
        that understate the real cluster-level effect.
    - Climate scenarios (climate_dry, climate_wet):
        Use the steady-state PDE solver. Climate perturbations affect all
        clusters uniformly and the PDE correctly propagates the site-wide
        change through the transmissivity field.

    Returns (grid_x, grid_y, delta_head_2d) or (None, None, None) on failure.
    """
    base_csv = base_dir / "baseline" / "19_head_surface_mean.csv"
    scen_csv = base_dir / subfolder  / "19_head_surface_mean.csv"
    if not base_csv.exists():
        return None, None, None

    df_base = pd.read_csv(base_csv)

    # ── Forest scenarios: analytical spatial shift ────────────────────────
    if subfolder in FOREST_SCENARIOS:
        return compute_analytical_delta_head(subfolder, df_base, base_dir)

    # ── Climate scenarios: PDE solver ─────────────────────────────────────
    try:
        E_vals = np.sort(df_base["Easting"].unique())
        N_vals = np.sort(df_base["Northing"].unique())
        grid_x, grid_y = np.meshgrid(E_vals, N_vals)

        data    = mod.load_data()
        wt_base, P_bar, PET_bar = mod.build_well_table(data)
        mask    = mod.make_site_mask(grid_x, grid_y)
        sea_pts, sea_vals = mod._sea_boundary_points()
        thickness = mod.build_thickness_surface(wt_base, grid_x, grid_y, mask)

        ref = wt_base["beta1"].notna()
        rpts = wt_base.loc[ref, ["E", "N"]].values
        beta1_s = mod.interpolate_surface(rpts, wt_base.loc[ref,"beta1"].values, grid_x, grid_y, mask)
        beta2_s = mod.interpolate_surface(rpts, wt_base.loc[ref,"beta2"].values, grid_x, grid_y, mask)
        beta3_s = mod.interpolate_surface(rpts, wt_base.loc[ref,"beta3"].values, grid_x, grid_y, mask)

        P_eff_b, PET_b = mod.build_source_sink_surfaces(
            wt_base, grid_x, grid_y, mask, P_bar, PET_bar)
        h_base = mod.solve_steady_state_head(
            grid_x, grid_y, mask, thickness,
            beta1_s, beta2_s, beta3_s,
            P_eff_b, PET_b, wt_base, sea_pts, sea_vals)

        sc_key = next((s for s in SCENARIOS if s[1] == subfolder), None)
        if sc_key is None:
            return None, None, None
        scenario_key, _, params, _ = sc_key
        wt_scen, P_mod, PET_mod, _ = mod.apply_scenario(
            wt_base, P_bar, PET_bar,
            scenario=scenario_key, params=params)

        ref_s  = wt_scen["beta1"].notna()
        rpts_s = wt_scen.loc[ref_s, ["E","N"]].values
        beta1_ss = mod.interpolate_surface(rpts_s, wt_scen.loc[ref_s,"beta1"].values, grid_x, grid_y, mask)
        beta2_ss = mod.interpolate_surface(rpts_s, wt_scen.loc[ref_s,"beta2"].values, grid_x, grid_y, mask)
        beta3_ss = mod.interpolate_surface(rpts_s, wt_scen.loc[ref_s,"beta3"].values, grid_x, grid_y, mask)
        P_eff_s, PET_s = mod.build_source_sink_surfaces(
            wt_scen, grid_x, grid_y, mask, P_mod, PET_mod)
        h_scen = mod.solve_steady_state_head(
            grid_x, grid_y, mask, thickness,
            beta1_ss, beta2_ss, beta3_ss,
            P_eff_s, PET_s, wt_scen, sea_pts, sea_vals)

        delta = h_scen - h_base
        return grid_x, grid_y, delta

    except Exception as e:
        warnings.warn(f"PDE delta computation failed for {subfolder}: {e}")
        import traceback; traceback.print_exc()
        return None, None, None


def load_wb_csv(scenario_dir):
    """Load 19_water_balance_summary.csv from a scenario directory."""
    csv = scenario_dir / "19_water_balance_summary.csv"
    if not csv.exists():
        return None
    return pd.read_csv(csv)


def build_head_grid(df):
    """
    Reconstruct a regular 2D grid from the head CSV.
    The CSV drops NaN cells (dropna on save), so we reconstruct the full
    grid extent and fill missing cells with NaN before pivoting.
    Returns (grid_x, grid_y, head_2d).
    """
    if df is None:
        return None, None, None

    # Infer grid spacing from the data
    E_vals = np.sort(df["Easting"].unique())
    N_vals = np.sort(df["Northing"].unique())

    # Build full grid and reindex — missing cells become NaN
    full_idx = pd.MultiIndex.from_product(
        [N_vals, E_vals], names=["Northing", "Easting"])
    head_series = df.set_index(["Northing", "Easting"])["Head_maOD"]
    head_full = head_series.reindex(full_idx)
    head_2d = head_full.values.reshape(len(N_vals), len(E_vals))

    grid_x, grid_y = np.meshgrid(E_vals, N_vals)
    return grid_x, grid_y, head_2d


def plot_difference_maps(base_dir, scenarios, diff_dir, mod=None):
    """
    For each non-baseline scenario, generate a two-panel difference map:
      Left:  Δhead = scenario_head − baseline_head (m)
      Right: Δwater_balance = scenario WB metric − baseline WB metric
    """
    diff_dir.mkdir(parents=True, exist_ok=True)

    # Load baseline
    base_scenario_dir = base_dir / "baseline"
    df_base = load_head_csv(base_scenario_dir)
    wb_base = load_wb_csv(base_scenario_dir)
    if df_base is None:
        warnings.warn("Baseline head CSV not found — cannot generate difference maps.")
        return
    grid_x, grid_y, head_base = build_head_grid(df_base)

    for scenario_key, subfolder, params, label in scenarios:
        if subfolder == "baseline":
            continue

        scenario_dir = base_dir / subfolder
        df_scen = load_head_csv(scenario_dir)
        wb_scen = load_wb_csv(scenario_dir)
        if df_scen is None:
            warnings.warn(f"Head CSV not found for {subfolder} — skipping difference map.")
            continue

        # Prefer PDE-based delta (physically consistent, no IDW artefacts)
        # Falls back to CSV subtraction if module unavailable
        if mod is not None:
            grid_x_pde, grid_y_pde, delta_head = compute_pde_delta_head(
                base_dir, subfolder, mod)
            if delta_head is None:
                warnings.warn(f"PDE delta failed for {subfolder} — using CSV subtraction")
                _, _, head_scen = build_head_grid(df_scen)
                if head_scen is None or head_base is None:
                    continue
                delta_head = head_scen - head_base
                grid_x_pde, grid_y_pde = grid_x, grid_y
            else:
                grid_x, grid_y = grid_x_pde, grid_y_pde
        else:
            _, _, head_scen = build_head_grid(df_scen)
            if head_scen is None or head_base is None:
                continue
            delta_head = head_scen - head_base

        # ── Figure ────────────────────────────────────────────────────────
        fig, axes = plt.subplots(1, 2,
                                 figsize=(FIG_TWO_PANEL_W, FIG_TWO_PANEL_H),
                                 dpi=FIG_DPI)

        # Left — Δhead spatial map
        ax = axes[0]
        delta_range = np.nanmax(np.abs(delta_head)) if np.any(~np.isnan(delta_head)) else 0
        if delta_range < 0.0005:
            ax.text(0.5, 0.5,
                    "No head difference detected.\n"
                    "Re-run 19a_scenario_runner.py.",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=FIG_FONT_LABEL, color="grey",
                    bbox=dict(boxstyle="round", fc="white", alpha=0.8))
        else:
            # Symmetric log scale — linear within ±linthresh, log outside.
            # This makes small forest-zone differences visible alongside
            # large climate changes without distorting the colour mapping.
            # linthresh = 0.005 m (5 mm) — anything smaller is noise.
            # vmax fixed at 0.35 m so all scenarios share the same scale.
            DIFF_VMAX  = 0.35
            LINTHRESH  = 0.005   # linear region ±5 mm
            norm = SymLogNorm(linthresh=LINTHRESH, linscale=0.5,
                              vmin=-DIFF_VMAX, vmax=DIFF_VMAX, base=10)
            im = ax.pcolormesh(grid_x, grid_y, delta_head,
                               cmap="RdBu_r", norm=norm,
                               shading="auto", alpha=0.85, zorder=2)
            cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02,
                              extend="both")
            # Manually set clean tick positions on the symlog scale
            cb_ticks = [-0.35, -0.1, -0.03, -0.01, 0, 0.01, 0.03, 0.1, 0.35]
            cb.set_ticks([t for t in cb_ticks if abs(t) <= DIFF_VMAX])
            cb.set_ticklabels([f"{t:+.3g}" for t in cb_ticks
                               if abs(t) <= DIFF_VMAX])
            cb.set_label("Δ Head (m;  symlog scale;  blue = wetter)",
                         fontsize=FIG_FONT_CB)
            cb.ax.tick_params(labelsize=FIG_FONT_TICK)
            # Zero-change contour
            try:
                ax.contour(grid_x, grid_y, delta_head, levels=[0],
                           colors=["k"], linewidths=0.6,
                           linestyles=["--"], zorder=5)
            except Exception:
                pass
            # Load baseline summer head to draw SD threshold contours
            # SD15b summer limit: water table within 0.61 m of surface
            # SD16  summer limit: water table within 0.98 m of surface
            # In maOD space these depend on local ground elevation —
            # draw contours on the DELTA surface at ±0.1 m and ±0.25 m
            # as guide lines showing where the shift crosses a threshold
            try:
                df_bsum = load_head_csv(base_dir / "baseline")
                if df_bsum is not None and "Head_maOD" in df_bsum.columns:
                    # Also need summer head — use head CSV as proxy
                    # Contour: where scenario head crosses SD15b/SD16 threshold
                    # i.e. where |delta| >= (threshold - baseline_depth_to_threshold)
                    # Simpler: just show the ±0.061 and ±0.098 m contours
                    ax.contour(grid_x, grid_y, delta_head,
                               levels=[-0.061, 0.061],
                               colors=["steelblue"], linewidths=0.7,
                               linestyles=[":", ":"], zorder=6,
                               alpha=0.8)
                    ax.contour(grid_x, grid_y, delta_head,
                               levels=[-0.098, 0.098],
                               colors=["darkorange"], linewidths=0.7,
                               linestyles=[":", ":"], zorder=6,
                               alpha=0.8)
            except Exception:
                pass

        ax.set_xlabel("Easting (m, OSGB36)", fontsize=FIG_FONT_LABEL)
        ax.set_ylabel("Northing (m, OSGB36)", fontsize=FIG_FONT_LABEL)
        ax.tick_params(labelsize=FIG_FONT_TICK)
        ax.set_title("Δ Summer minimum head (m)\nScenario minus baseline",
                     fontsize=FIG_FONT_TITLE, fontweight="bold")

        # Stats annotation
        n_wet  = np.sum(delta_head > 0.01)
        n_dry  = np.sum(delta_head < -0.01)
        n_tot  = np.sum(~np.isnan(delta_head))
        mean_d = np.nanmean(delta_head)
        ax.annotate(
            f"Mean Δh = {mean_d:+.3f} m\n"
            f"Wetter cells (>+1 cm): {n_wet/n_tot:.0%}\n"
            f"Drier cells  (<-1 cm): {n_dry/n_tot:.0%}",
            xy=(0.02, 0.02), xycoords="axes fraction",
            fontsize=FIG_FONT_ANNOT, color="dimgrey",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

        # Right — per-well water balance comparison
        ax = axes[1]
        if wb_base is not None and wb_scen is not None:
            wb_merged = wb_base[["well", "E", "N", "cluster",
                                  "lateral_inflow_m_mon"]].merge(
                wb_scen[["well", "lateral_inflow_m_mon"]],
                on="well", suffixes=("_base", "_scen"))
            wb_merged["delta_lateral"] = (wb_merged["lateral_inflow_m_mon_scen"]
                                          - wb_merged["lateral_inflow_m_mon_base"])
            vlim = max(abs(wb_merged["delta_lateral"].quantile(0.05)),
                       abs(wb_merged["delta_lateral"].quantile(0.95)), 0.02)
            sc = ax.scatter(
                wb_merged["E"], wb_merged["N"],
                c=wb_merged["delta_lateral"],
                cmap="RdBu", vmin=-vlim, vmax=vlim,
                s=60, edgecolors="k", linewidths=0.4, zorder=5)
            cb2 = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
            cb2.set_label("Δ Lateral inflow (m/month;  blue = gain)",
                          fontsize=FIG_FONT_CB)
            cb2.ax.tick_params(labelsize=FIG_FONT_TICK)
            ax.set_title("Δ Lateral inflow per well (m/month)\nScenario minus baseline",
                         fontsize=FIG_FONT_TITLE, fontweight="bold")

            # Cluster means annotation
            txt = "Cluster mean Δ lateral inflow (m/month):\n"
            for cid, clab in [(1,"C1"),(2,"C2"),(3,"C3"),(4,"C4")]:
                sub = wb_merged[wb_merged["cluster"] == cid]["delta_lateral"]
                if len(sub):
                    txt += f"  {clab}: {sub.mean():+.4f}\n"
            ax.annotate(txt.strip(), xy=(0.02, 0.02), xycoords="axes fraction",
                        fontsize=FIG_FONT_ANNOT, color="dimgrey",
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))
        else:
            ax.text(0.5, 0.5, "Water balance CSV not available",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=FIG_FONT_LABEL, color="grey")

        ax.set_xlabel("Easting (m, OSGB36)", fontsize=FIG_FONT_LABEL)
        ax.set_ylabel("Northing (m, OSGB36)", fontsize=FIG_FONT_LABEL)
        ax.tick_params(labelsize=FIG_FONT_TICK)

        fig.suptitle(
            f"Difference Map: {label}\nvs Baseline (2005–2026 observed mean)",
            fontsize=FIG_FONT_TITLE + 1, fontweight="bold")
        fig.tight_layout()

        out_path = diff_dir / f"diff_{subfolder}.png"
        fig.savefig(out_path, dpi=FIG_DPI, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved: {out_path.name}  (mean Δh = {mean_d:+.3f} m)")


# ============================================================================
# SUMMARY COMPARISON FIGURE
# ============================================================================

def plot_scenario_summary(base_dir, scenarios, diff_dir):
    """
    Summary bar chart: Δ(summer minimum depth) by cluster for each scenario.
    Summer minimum = mean of May-Sep months (index 4-8, 0-based).
    Positive bar = deeper summer water table (drier/worse for slacks).
    Negative bar = shallower (wetter/better).
    SD15b and SD16 summer limits shown as reference lines where applicable.
    """
    diff_dir.mkdir(parents=True, exist_ok=True)

    SUMMER_IDX = [4, 5, 6, 7, 8]   # May-Sep (0-based)
    clusters = ["C1", "C2", "C3", "C4"]
    short_labels = {
        "forest_removal":  "Clearfell",
        "forest_thinning": "Thinning 50%",
        "species_change":  "Broadleaf",
        "climate_dry":     "Climate dry",
        "climate_wet":     "Climate wet",
    }
    cc = CLUSTER_COLOURS_SCEN
    non_baseline = [(sk, sf, p, lb) for sk, sf, p, lb in scenarios
                    if sf != "baseline"]
    n_scen = len(non_baseline)
    x = np.arange(len(clusters))
    width = 0.15
    offsets = np.linspace(-(n_scen-1)/2, (n_scen-1)/2, n_scen) * width

    # Scenario colours matching hydrograph
    scen_colours = {
        "forest_removal":  "#D55E00",
        "forest_thinning": "#E69F00",
        "species_change":  "#009E73",
        "climate_dry":     "#CC79A7",
        "climate_wet":     "steelblue",
    }

    fig, ax = plt.subplots(figsize=(FIG_TWO_PANEL_W * 0.7, FIG_SINGLE_H),
                           dpi=FIG_DPI)

    for i, (sk, sf, p, lb) in enumerate(non_baseline):
        delta_summer = []
        for c in clusters:
            base_summer = np.mean([SEASONAL_CYCLE[c][m] for m in SUMMER_IDX])
            shift = SCENARIO_SHIFTS.get(sf, {}).get(c, 0.0)
            scen_summer = base_summer + shift
            delta_summer.append(scen_summer - base_summer)  # = shift

        bars = ax.bar(x + offsets[i], delta_summer,
                      width=width * 0.85,
                      color=scen_colours.get(sf, "grey"),
                      alpha=0.85, zorder=3,
                      label=short_labels.get(sf, sf))

    ax.axhline(0, color="k", lw=0.8, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([CLUSTER_LABELS_SCEN[c] for c in clusters],
                       fontsize=FIG_FONT_TICK)
    ax.set_ylabel("Δ Summer minimum depth (m)\nPositive = deeper (drier)",
                  fontsize=FIG_FONT_LABEL)
    ax.tick_params(labelsize=FIG_FONT_TICK)
    ax.legend(fontsize=FIG_FONT_ANNOT, loc="lower left", framealpha=0.9)
    ax.grid(axis="y", lw=0.4, color="lightgrey", zorder=0)
    fig.suptitle(
        "Scenario Comparison — Δ Summer Minimum Depth by Cluster\n"
        "Positive = deeper water table (worse for wet slacks)",
        fontsize=FIG_FONT_TITLE, fontweight="bold")
    fig.tight_layout()
    out = diff_dir / "scenario_summary.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ============================================================================
# MAIN
# ============================================================================

def plot_cluster_hydrographs(base_dir, scenarios, diff_dir):
    """
    Seasonal hydrograph comparison.

    Layout: one panel per scenario (6 panels, 2×3 grid), each showing all
    four cluster profiles. This lets the reader compare:
      - Which clusters are near the SD threshold under baseline
      - How each scenario shifts the profiles relative to baseline
      - Whether forest interventions affect non-C4 clusters (they do not
        directly via the SSM equilibrium — that caveat is annotated)

    Slack thresholds (Curreli et al. 2013):
      SD15b summer limit: -0.61 m
      SD16  dry slack summer limit: -0.98 m
    """
    diff_dir.mkdir(parents=True, exist_ok=True)

    clusters = ["C1", "C2", "C3", "C4"]
    x = np.arange(1, 13)

    # Scenario display order and labels
    scen_order = [s[1] for s in scenarios]
    scen_labels = {s[1]: s[3] for s in scenarios}

    fig, axes = plt.subplots(2, 3,
                             figsize=(FIG_FOUR_W, FIG_TWO_PANEL_H * 2),
                             dpi=FIG_DPI,
                             sharex=True)
    axes = axes.ravel()

    for ax, (scenario_key, subfolder, params, slabel) in zip(axes, scenarios):
        for cluster in clusters:
            baseline_cycle = np.array(SEASONAL_CYCLE[cluster])
            shift = SCENARIO_SHIFTS.get(subfolder, {}).get(cluster, 0.0)
            cycle = baseline_cycle + shift
            color = CLUSTER_COLOURS_SCEN[cluster]
            clabel = CLUSTER_LABELS_SCEN[cluster]

            # Baseline as thin dashed line for comparison
            ax.plot(x, baseline_cycle,
                    color=color, lw=0.9, ls="--", alpha=0.4, zorder=2)
            # Scenario as solid line
            ax.plot(x, cycle,
                    color=color, lw=2.0, ls="-", zorder=3,
                    label=clabel)

        # SD threshold lines
        ax.axhline(-0.61, color="#1565C0", lw=1.1, ls="--", zorder=4,
                   label="SD15b summer (−0.61 m)")
        ax.axhline(-0.98, color="#E65100", lw=1.1, ls="--", zorder=4,
                   label="SD16 summer (−0.98 m)")
        ax.axhline(0,     color="navy",    lw=0.7, ls="-",  zorder=4)

        # Summer shading
        ax.axvspan(4.5, 9.5, alpha=0.07, color="gold", zorder=1)

        ax.set_xticks(x)
        ax.set_xticklabels(MONTHS, fontsize=FIG_FONT_TICK + 1, rotation=45, ha="right")
        ax.tick_params(labelsize=FIG_FONT_TICK + 1)
        ax.grid(axis="y", lw=0.4, color="lightgrey", zorder=0)


        # Title — highlight if scenario differs from baseline
        title_col = "black" if subfolder == "baseline" else "#8B0000"             if any(SCENARIO_SHIFTS.get(subfolder,{}).get(c,0) < -0.05
                   for c in clusters) else "#006400"
        ax.set_title(slabel, fontsize=FIG_FONT_TITLE + 1,
                     fontweight="bold", color=title_col, pad=6)

        # Annotate forest-only caveat
        if subfolder in {"forest_removal", "forest_thinning", "species_change"}:
            ax.annotate("Direct shift: C4 only\n(lateral effects not modelled)",
                        xy=(0.02, 0.02), xycoords="axes fraction",
                        fontsize=FIG_FONT_ANNOT + 1, color="dimgrey",
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.75))

    # Shared y-label
    for ax in axes[::3]:
        ax.set_ylabel("Depth below ground (m;  +ve = flooding)",
                      fontsize=FIG_FONT_LABEL)

    # Set consistent y-axis on all panels after the loop
    for ax in axes:
        ax.set_ylim(-2.2, 0.2)   # deep at bottom, flooding at top

    # Single legend from last panel (all lines defined there)
    handles, labels = axes[-1].get_legend_handles_labels()
    # Deduplicate
    seen = {}
    for h, l in zip(handles, labels):
        if l not in seen:
            seen[l] = h
    # Cluster lines first, then thresholds
    cluster_items = [(h, l) for l, h in seen.items()
                     if l.startswith("C")]
    thresh_items  = [(h, l) for l, h in seen.items()
                     if not l.startswith("C")]
    final_h = [h for h,l in cluster_items + thresh_items]
    final_l = [l for h,l in cluster_items + thresh_items]

    # Add baseline dashed line to legend
    import matplotlib.lines as mlines
    baseline_proxy = mlines.Line2D([], [], color="grey", lw=0.9, ls="--",
                                   alpha=0.5, label="Baseline profile (all panels)")
    final_h.append(baseline_proxy)
    final_l.append("Baseline profile (all panels)")

    fig.legend(final_h, final_l,
               loc="lower center",
               ncol=len(final_h),
               fontsize=FIG_FONT_ANNOT + 2,
               handlelength=3.0,
               handleheight=1.2,
               framealpha=0.92,
               bbox_to_anchor=(0.5, -0.02))

    fig.suptitle(
        "Seasonal Water Table Profiles — All Scenarios and Clusters\n"
        "Solid = scenario  |  Dashed = baseline  |  "
        "Shading = summer window (May–Sep)  |  "
        "Thresholds: Curreli et al. (2013)",
        fontsize=FIG_FONT_TITLE + 1, fontweight="bold")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    # Re-apply ylim AFTER tight_layout — tight_layout can reset axis limits
    for ax in axes:
        ax.set_ylim(-2.2, 0.2)
    out = diff_dir / "cluster_hydrographs.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")



def main(diff_only=False):
    base_dir = OUT_DIR / "19_spatial_groundwater"
    diff_dir = base_dir / "difference_maps"

    print("19a_scenario_runner.py  v2026-04-02  (ylim fix)")
    # Always load script 19 as a module — needed for PDE delta computation
    spec = importlib.util.spec_from_file_location(
        "script19",
        SRC_DIR / "19_spatial_groundwater.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["script19"] = mod
    spec.loader.exec_module(mod)

    if not diff_only:
        for scenario_key, subfolder, params, label in SCENARIOS:
            try:
                run_scenario(scenario_key, subfolder, params, label,
                             base_dir, mod)
            except Exception as e:
                warnings.warn(f"Scenario '{subfolder}' failed: {e}")
                import traceback; traceback.print_exc()

    print(f"\n{'='*70}")
    print("  GENERATING DIFFERENCE MAPS")
    print(f"{'='*70}")
    plot_difference_maps(base_dir, SCENARIOS, diff_dir, mod=mod)
    plot_scenario_summary(base_dir, SCENARIOS, diff_dir)
    plot_cluster_hydrographs(base_dir, SCENARIOS, diff_dir)
    print(f"\nAll outputs written to: {base_dir}")
    print(f"Difference maps:        {diff_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run all script 19 scenarios and generate difference maps.")
    parser.add_argument("--diff-only", action="store_true",
                        help="Skip scenario runs; regenerate difference maps only")
    args = parser.parse_args()
    main(diff_only=args.diff_only)
