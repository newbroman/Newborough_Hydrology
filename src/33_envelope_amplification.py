"""
33_envelope_amplification.py — Climate-swing amplification and the drought-floor surface
========================================================================================

Maps the *envelope* the spring water table moves between — its dry extreme and its
wet extreme — and from it two robust, window-independent products:

  (A) the climate-swing AMPLIFICATION field: each well's wet-minus-dry swing divided
      by the network-mean swing, with the common-mode (site-wide) swing removed. A
      relative measure of how much each area magnifies (>1) or damps (<1) the shared
      climate forcing. The slow-draining forest interior amplifies (~1.5x); the
      lake edge damps (~0.6x).
  (B) the DROUGHT-FLOOR surface: raw depth to water at the dry extreme, with the
      ecological threshold contoured. Kept in absolute depth deliberately — the
      Curreli threshold is an absolute distance to surface, not a relative quantity.

This is the robust observed-behaviour companion to the window-sensitivity caution
(it compares genuine end-members, not two marginal windows) and to Script 32's
secular differential drift (this is climate-response structure, not secular change).

Anchor claim (report Step 1, envelope figure):
    "Between its dry and wet spring extremes the Warren water table swings ~0.75 m;
     this swing is amplified to ~1.5x in the slow-draining forest interior and damped
     to ~0.6x at the lake edge — a window-independent measure of each area's climate
     sensitivity, with the forest the most volatile zone and the lake the most buffered."

Method (locked spec, 2026-06-26):
  * Spring value per well-year = mean of available MAM (config.MSL_SPRING_MONTHS).
  * Extreme years chosen by site-mean spring extremity AND antecedent-rainfall
    consistency, within the full-network period:
       DRY = {2011, 2012, 2019}   WET = {2014, 2021, 2024}
    2006 is excluded as a wet extreme: its 2004-2005 antecedent was the driest in the
    record (-19% in 2005), so the slow-tau forest wells had not refilled by spring 2006
    and it is not an antecedent-matched wet state.
  * Per-well state = mean over the extreme years (require >= MIN_YEARS_PER_EXTREME of 3).
  * swing = wet_state - dry_state (mm).  amplification = swing / network-mean swing.
  * Drought-floor = dry_state depth to water (mm below ground), threshold contoured.
  * Exclusions: config.MSL5_EXCLUDED_WELLS (CEH13/CEH14) + Llyn Rhos-Ddu gauge.
  * IDW power 2, 50 m grid, 450 m mask.

Standalone diagnostic — NOT wired into run_analysis.py / paths.py / config.py.
Pipeline integration (paths/config constants, orchestrator slot, map_utils hillshade
base, the actual Curreli SD15b/SD16 threshold values) deferred to the Step 3/5 decision.

Inputs (read at runtime; nothing hardcoded):
    outputs/01_wells_clean.csv     per-well monthly levels (depth below ground)
    outputs/01_locations.csv       well E/N
    outputs/03_master_data.csv     per-well cluster id

Outputs (outputs/33_envelope_amplification/):
    33_envelope_per_well.csv          dry/wet state, swing, amplification, cluster
    33_amplification_field.png        relative amplification map (headline)
    33_drought_floor.png              raw drought-floor surface (ecological companion)
    33_results.txt                    console summary + robustness table

Version: 1.0.0 (2026-06-26)
"""

from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from utils import config, paths
from utils.console_utils import banner, phase, step, info, saved, note, result, done, hr

SCRIPT_ID = "33"
VERSION = "1.0.0"

# --- method constants (from utils.config; spec-locked 2026-06-26) -----------------
SPRING_MONTHS = config.MSL_SPRING_MONTHS
DRY_YEARS = config.ENVELOPE_DRY_YEARS
WET_YEARS = config.ENVELOPE_WET_YEARS
MIN_YEARS_PER_EXTREME = config.ENVELOPE_MIN_YEARS_PER_EXTREME
LAKE_GAUGE_KEYS = config.LAKE_GAUGE_KEYS
IDW_POWER = config.DIFF_IDW_POWER
IDW_GRID_M = config.DIFF_IDW_GRID_M
IDW_MASK_M = config.DIFF_IDW_MASK_M
ECO_THRESHOLDS_MM = config.ENVELOPE_ECO_THRESHOLDS_MM
# robustness: alternative extreme-year sets to demonstrate stability / 2006 distortion
ROBUSTNESS_SETS = {
    "primary":        (DRY_YEARS,              WET_YEARS),
    "wet_2016_swap":  (DRY_YEARS,              [2016, 2021, 2024]),
    "dry_no_2019":    ([2011, 2012],           WET_YEARS),
    "wet_incl_2006":  (DRY_YEARS,              [2006, 2021, 2024]),  # shows 2006 distortion
}

# --- output paths (from utils.paths) ----------------------------------------------
OUT_DIR = paths.DIR_33
OUT_CSV = paths.OUT_33_PER_WELL
OUT_TXT = paths.OUT_33_RESULTS
OUT_FIG_AMP = paths.OUT_33_FIG_AMP
OUT_FIG_FLOOR = paths.OUT_33_FIG_FLOOR

IN_WELLS = paths.INT_WELLS_CLEAN
IN_LOCATIONS = paths.INT_LOCATIONS
IN_MASTER = paths.OUT_DIR / "03_master_data.csv"


# =================================================================================
# Data
# =================================================================================
def load_inputs():
    levels = pd.read_csv(IN_WELLS, index_col=0, parse_dates=True)
    drop = [c for c in levels.columns if c.lower().strip() in LAKE_GAUGE_KEYS]
    if drop:
        levels = levels.drop(columns=drop)
    loc = pd.read_csv(IN_LOCATIONS)
    loc["key"] = loc["Name"].astype(str).str.lower().str.strip()
    master = pd.read_csv(IN_MASTER)
    master["key"] = master["Name_Original"].astype(str).str.lower().str.strip()
    return levels, loc, master


def spring_year_table(levels):
    spring = levels[levels.index.month.isin(SPRING_MONTHS)]
    return spring.groupby(spring.index.year).mean(numeric_only=True)


def extreme_states(yr, dry_years, wet_years, excluded):
    """Per-well mean state at the dry and wet extremes, with coverage filter."""
    dsub, wsub = yr.loc[dry_years], yr.loc[wet_years]
    dry, wet = dsub.mean(skipna=True), wsub.mean(skipna=True)
    nd, nw = dsub.notna().sum(), wsub.notna().sum()
    df = pd.DataFrame({"dry_m": dry, "wet_m": wet, "n_dry": nd, "n_wet": nw})
    df["key"] = df.index.str.lower().str.strip()
    df = df[(df.n_dry >= MIN_YEARS_PER_EXTREME) & (df.n_wet >= MIN_YEARS_PER_EXTREME)]
    df = df[~df.key.isin(excluded)].copy()
    df["swing_mm"] = (df.wet_m - df.dry_m) * 1000.0
    return df


def add_amplification(df):
    net = df.swing_mm.mean()
    df = df.copy()
    df["amplification"] = df.swing_mm / net
    return df, net


# =================================================================================
# IDW + figures
# =================================================================================
def _grid(loc):
    E, N = loc["E"].values, loc["N"].values
    gx = np.arange(np.nanmin(E) - 150, np.nanmax(E) + 150, IDW_GRID_M)
    gy = np.arange(np.nanmin(N) - 150, np.nanmax(N) + 150, IDW_GRID_M)
    return np.meshgrid(gx, gy)


def idw(GX, GY, px, py, pv, power=IDW_POWER, mask=IDW_MASK_M):
    num = np.zeros_like(GX); den = np.zeros_like(GX); nearest = np.full_like(GX, 1e18)
    for x, y, v in zip(px, py, pv):
        dd = np.sqrt((GX - x) ** 2 + (GY - y) ** 2)
        dd = np.where(dd < 1e-6, 1e-6, dd)
        w = 1.0 / dd ** power
        num += w * v; den += w; nearest = np.minimum(nearest, dd)
    Z = num / den
    Z[nearest > mask] = np.nan
    return Z


def fig_amplification(df, GX, GY, out_path):
    colours = config.get_cluster_colours()
    labels = config.CLUSTER_LABELS
    Z = idw(GX, GY, df.E.values, df.N.values, df.amplification.values)
    norm = TwoSlopeNorm(vcenter=1.0, vmin=0.55, vmax=1.55)
    fig, ax = plt.subplots(figsize=(9.5, 9))
    im = ax.pcolormesh(GX, GY, Z, cmap="RdBu_r", norm=norm, shading="auto", alpha=0.93)
    for cid in sorted(df.Cluster.dropna().unique()):
        s = df[df.Cluster == cid]
        ax.scatter(s.E, s.N, c=[colours.get(int(cid), "#444")], edgecolor="k",
                   linewidth=0.5, s=48, zorder=5, label=labels.get(int(cid), f"C{int(cid)}"))
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.legend(fontsize=8.5, loc="lower left", framealpha=0.9, title="cluster")
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.01)
    cb.set_label("climate-swing amplification  (well swing / network mean)\n"
                 ">1 amplifies the common swing   <1 damps it", fontsize=9.5)
    ax.set_title("Newborough Warren: climate-swing amplification field (relative, common-mode removed)\n"
                 "Forest interior amplifies; lake edge damps. Window-independent. CEH13/14 excluded.",
                 fontsize=10.5, loc="left")
    fig.savefig(out_path, dpi=160, bbox_inches="tight"); plt.close(fig)


def fig_drought_floor(df, GX, GY, out_path):
    Z = idw(GX, GY, df.E.values, df.N.values, (df.dry_m * 1000.0).values)
    fig, ax = plt.subplots(figsize=(9.5, 9))
    im = ax.pcolormesh(GX, GY, Z, cmap="YlOrBr_r", shading="auto", alpha=0.93)
    cs = ax.contour(GX, GY, Z, levels=sorted(ECO_THRESHOLDS_MM), colors="k", linewidths=1.1)
    ax.clabel(cs, fmt={t: f"{t/1000:.1f} m" for t in ECO_THRESHOLDS_MM}, fontsize=8)
    ax.scatter(df.E, df.N, c="k", s=10, zorder=5)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.01)
    cb.set_label("drought-floor depth to water (mm below ground)", fontsize=9.5)
    ax.set_title("Newborough Warren: drought-floor surface (raw depth, dry extreme 2011/12/19)\n"
                 "Contours illustrative — set Curreli SD15b/SD16 thresholds at integration.",
                 fontsize=10.5, loc="left")
    fig.savefig(out_path, dpi=160, bbox_inches="tight"); plt.close(fig)


# =================================================================================
# Main
# =================================================================================
def main() -> int:
    banner(SCRIPT_ID, "Climate-swing amplification + drought-floor surface", VERSION)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    phase(1, "Load inputs")
    levels, loc, master = load_inputs()
    yr = spring_year_table(levels)
    excluded = set(k.lower() for k in config.MSL5_EXCLUDED_WELLS) | LAKE_GAUGE_KEYS
    info(f"dry extreme years {DRY_YEARS}; wet extreme years {WET_YEARS}")
    note(f"2006 excluded from wet extreme (driest-in-record 2004-2005 antecedent)")

    phase(2, "Extreme states + amplification")
    df = extreme_states(yr, DRY_YEARS, WET_YEARS, excluded)
    df = df.merge(master[["key", "Cluster"]], on="key", how="left")
    df = df.merge(loc[["key", "E", "N"]], on="key", how="left").dropna(subset=["E", "N"])
    df, net = add_amplification(df)
    result("wells mapped", str(len(df)))
    result("network-mean swing", f"{net:.0f} mm")
    by_cluster = df.groupby("Cluster")["amplification"].agg(["mean", "count"]).round(2)
    for cid, row in by_cluster.iterrows():
        step(f"{config.CLUSTER_LABELS.get(int(cid), f'C{int(cid)}'):20s} "
             f"amplification {row['mean']:.2f}x  (n={int(row['count'])})")

    phase(3, "Robustness to extreme-year choice")
    rob_lines = ["robustness — cluster amplification across year-set choices:"]
    header = "  set              " + "  ".join(f"C{c}" for c in [1, 2, 3, 4, 5])
    rob_lines.append(header)
    for name, (dy, wy) in ROBUSTNESS_SETS.items():
        rdf = extreme_states(yr, dy, wy, excluded).merge(master[["key", "Cluster"]], on="key", how="left")
        rdf, _ = add_amplification(rdf)
        means = rdf.groupby("Cluster")["amplification"].mean()
        rob_lines.append(f"  {name:15s}  " + "  ".join(f"{means.get(c, np.nan):.2f}" for c in [1, 2, 3, 4, 5]))
    for ln in rob_lines:
        print(ln)

    phase(4, "Render figures")
    GX, GY = _grid(loc)
    fig_amplification(df, GX, GY, OUT_FIG_AMP); saved(OUT_FIG_AMP)
    fig_drought_floor(df, GX, GY, OUT_FIG_FLOOR); saved(OUT_FIG_FLOOR)

    phase(5, "Write outputs")
    out = df[["key", "Cluster", "E", "N", "dry_m", "wet_m", "swing_mm",
              "amplification", "n_dry", "n_wet"]].copy()
    out.to_csv(OUT_CSV, index=False); saved(OUT_CSV)
    OUT_TXT.write_text(
        f"network-mean swing {net:.0f} mm; wells {len(df)}\n\n"
        + by_cluster.to_string() + "\n\n" + "\n".join(rob_lines) + "\n")
    saved(OUT_TXT)
    hr()
    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
