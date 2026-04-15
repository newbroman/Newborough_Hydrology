# VERSION: 2026-04-15-JPG
"""
19a_scenario_runner.py  v2026-04-13-clean
==========================================
Clean rewrite. Generates per-field difference maps for each scenario.

Design principles
-----------------
1. Load per-well data from 19_water_balance_summary.csv (baseline + scenario)
2. Subtract well-by-well to get Δ values
3. IDW-interpolate Δ onto grid, masked to study area
4. Plot with RdBu colourmap, auto-scaled from actual data
5. Skip maps where |max Δ| < threshold (genuinely no change)

Colour convention (consistent throughout):
  RED   = scenario HIGHER than baseline (more recharge, higher head, more ET...)
  BLUE  = scenario LOWER than baseline

For the user to interpret:
  Head (m AOD):        RED = higher head = WETTER   BLUE = lower head = DRIER
  Depth below ground:  RED = shallower   = WETTER   BLUE = deeper     = DRIER
  Drainage, ET:        RED = more                    BLUE = less
  Lateral inflow:      RED = more inflow             BLUE = less
  Recharge:            RED = more                    BLUE = less
  Storage:             RED = more                    BLUE = less
"""

import sys, argparse, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.colors import Normalize
from scipy.spatial import cKDTree

SRC_DIR = Path(__file__).parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from utils.paths import OUT_DIR
import importlib

# ── Scenarios ──────────────────────────────────────────────────────────────────
SCENARIOS = [
    ("baseline",       "baseline",
     {},
     "Baseline — 2005–2026 observed mean"),
    ("forest_removal", "forest_removal",
     {"beta2_increase_fraction": 0.15},
     "Full clearfell — β₂ ×1.15, interception removed"),
    ("forest_thinning","forest_thinning",
     {"thinning_fraction": 0.5, "beta2_increase_fraction": 0.15},
     "Forest thinning — 50% of clearfell effect"),
    ("species_change", "species_change",
     {"winter_recharge_reduction": 0.10},
     "Broadleaf conversion — β₁ ×0.90 in autumn"),
    ("climate_change", "climate_dry",
     {"delta_P_mm": -89, "delta_PET_mm": +54},
     "Climate dry — ΔP −10%, ΔPET +10%"),
    ("climate_change", "climate_wet",
     {"delta_P_mm": +89, "delta_PET_mm": -27},
     "Climate wet — ΔP +10%, ΔPET −5%"),
]
FOREST_SCENARIOS  = {"forest_removal", "forest_thinning", "species_change"}
CLIMATE_SCENARIOS = {"climate_dry", "climate_wet"}

# Per-cluster equilibrium Δ depth (m, positive = deeper = drier)
SCENARIO_SHIFTS = {
    "baseline":        {"C1": 0.000, "C2": 0.000, "C3": 0.000, "C4": 0.000},
    "forest_removal":  {"C1": 0.000, "C2": 0.000, "C3": 0.000, "C4":+0.145},
    "forest_thinning": {"C1": 0.000, "C2": 0.000, "C3": 0.000, "C4":+0.073},
    "species_change":  {"C1": 0.000, "C2": 0.000, "C3": 0.000, "C4":+0.003},
    "climate_dry":     {"C1":+0.112, "C2":+0.156, "C3":+0.195, "C4":+0.219},
    "climate_wet":     {"C1":-0.079, "C2":-0.109, "C3":-0.133, "C4":-0.135},
}

# Seasonal cycle: depth below ground (m, positive = below surface)
SEASONAL_CYCLE = {
    "C1": [0.083,0.108,0.166,0.314,0.519,0.676,0.748,0.778,0.810,0.616,0.380,0.261],
    "C2": [0.250,0.270,0.297,0.365,0.593,0.761,0.847,0.923,1.001,0.860,0.622,0.494],
    "C3": [0.691,0.664,0.749,0.756,0.950,1.097,1.137,1.190,1.262,1.242,1.020,0.922],
    "C4": [1.294,1.189,1.254,1.134,1.356,1.529,1.531,1.607,1.702,1.806,1.620,1.566],
}
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
CLUSTER_COLOURS = {"C1":"#E69F00","C2":"#009E73","C3":"#CC79A7","C4":"#D55E00"}
CLUSTER_LABELS  = {
    "C1":"C1 Eastern lake-buffer","C2":"C2 Eastern mature dune",
    "C3":"C3 Western mature dune","C4":"C4 Forest",
}
SCENARIO_COLOURS = {
    "forest_removal":"#D55E00","forest_thinning":"#E69F00",
    "species_change":"#009E73","climate_dry":"#CC79A7","climate_wet":"steelblue",
}

# Fields to difference
# (csv_col, label, units, cmap, min_threshold)
#
# Colour convention throughout:
#   BLUE = wetter than baseline   RED = drier than baseline
#
# RdBu_r: positive Δ → blue (wetter), negative Δ → red (drier)
#   Used for: head (higher = wetter), recharge (more = wetter)
#
# RdBu:   positive Δ → red (drier),  negative Δ → blue (wetter)
#   Used for: depth_bg (deeper = drier), ET (more = drier),
#             drainage (more = drier), lateral inflow (more demand = drier)
#
# YlOrRd: sequential magnitude — storage change (no wetter/drier direction)
#
# RdBu:   positive→BLUE  negative→RED  (use for head, recharge: +Δ = wetter = blue)
# RdBu_r: positive→RED   negative→BLUE (use for ET, drainage, depth: +Δ = drier = red)
# YlOrRd: sequential magnitude for storage
DIFF_FIELDS = [
    ("mean_head",           "Mean water table",           "m AOD",   "RdBu",   0.005),
    ("winter_head",         "Winter mean water table",    "m AOD",   "RdBu",   0.005),
    ("summer_head",         "Summer minimum water table", "m AOD",   "RdBu",   0.005),
    ("recharge_m_mon",      "Recharge",                   "m/month", "RdBu",   0.0005),
    ("et_draw_m_mon",       "ET draw",                    "m/month", "RdBu_r", 0.0005),
    ("drainage_m_mon",      "Drainage",                   "m/month", "RdBu_r", 0.0005),
    ("lateral_inflow_m_mon","Lateral inflow residual",   "m/month", "RdBu_r", 0.005),
    ("storage_change_mm",   "Seasonal storage change",    "mm",      "YlOrRd", 2.0),
    ("winter_depth_bg",     "Winter depth below ground",  "m",       "RdBu_r", 0.005),
    ("summer_depth_bg",     "Summer depth below ground",  "m",       "RdBu_r", 0.005),
]

# Figure constants
FIG_DPI=300; FIG_W=7.09; FIG_H=5.8
FT=9; FL=8; FK=7; FA=6; FC=7

# Output format for difference maps — JPEG only
DIFF_MAP_FORMAT  = "jpg"
DIFF_MAP_QUALITY = 85

# Module-level references set by main() for use in diff map functions
_MOD = None
_FEATURES = None


# ── Runner ─────────────────────────────────────────────────────────────────────
def run_scenario(scenario_key, subfolder, params, label, base_dir, mod):
    d = base_dir / subfolder
    d.mkdir(parents=True, exist_ok=True)
    print(f"\n{'='*70}\n  SCENARIO: {label}\n{'='*70}")
    mod.main(scenario=scenario_key, scenario_params=params,
             output_dir=d, supplementary=True)
    return d


# ── CSV helpers ────────────────────────────────────────────────────────────────
def load_wb(d):
    p = Path(d) / "19_water_balance_summary.csv"
    return pd.read_csv(p) if p.exists() else None

def load_grid(base_dir):
    p = Path(base_dir) / "baseline" / "19_head_surface_mean.csv"
    if not p.exists(): return None, None
    df = pd.read_csv(p)
    E = np.sort(df["Easting"].unique())
    N = np.sort(df["Northing"].unique())
    return np.meshgrid(E, N)


# ── IDW interpolation ──────────────────────────────────────────────────────────
def idw(points, values, gx, gy, k=8, power=2):
    """IDW interpolation of per-well values onto grid."""
    valid = ~np.isnan(values)
    if valid.sum() < 3:
        return np.full(gx.shape, np.nan)
    pts = points[valid]; vals = values[valid]
    tree = cKDTree(pts)
    flat = np.column_stack([gx.ravel(), gy.ravel()])
    dists, idxs = tree.query(flat, k=min(k, len(pts)))
    dists = np.where(dists == 0, 1e-10, dists)
    w = 1.0 / dists**power
    w /= w.sum(axis=1, keepdims=True)
    return (w * vals[idxs]).sum(axis=1).reshape(gx.shape)


# ── Single difference map ──────────────────────────────────────────────────────
def plot_diff_map(col, lbl, units, cmap, delta_vals, pts, gx, gy, label,
                  subfolder, out_path):
    """
    Plot one difference map.
    delta_vals: raw (scenario - baseline) per well.
    cmap: RdBu_r (blue=wetter), RdBu (red=drier), or YlOrRd (storage magnitude).
    Auto-scaled from p5/p95 of actual data.
    """
    valid = ~np.isnan(delta_vals)
    if valid.sum() < 3:
        return

    # Check well-level values BEFORE IDW — if all near zero, skip entirely
    # This prevents IDW numerical noise from producing misleading colour maps
    well_max = np.nanmax(np.abs(delta_vals[valid]))
    if well_max < 1e-5:
        return  # all well values effectively zero — skip

    p5  = float(np.percentile(delta_vals[valid],  5))
    p95 = float(np.percentile(delta_vals[valid], 95))
    spread = max(abs(p5), abs(p95))
    if spread < 1e-6:
        return

    surf = idw(pts, delta_vals, gx, gy)

    # Mask to study area
    if _MOD is not None:
        try:
            mask = _MOD.make_site_mask(gx, gy)
            surf = np.where(mask, surf, np.nan)
        except Exception:
            pass

    # For YlOrRd (storage): sequential from 0 to max magnitude
    if cmap == "YlOrRd":
        norm = Normalize(vmin=0, vmax=spread)
        surf = np.abs(surf)        # magnitude only
        delta_vals = np.abs(delta_vals)
    else:
        norm = Normalize(vmin=-spread, vmax=spread)

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=FIG_DPI)

    # Base map — DEM hillshade first (lowest layer)
    if _MOD is not None:
        try:
            _MOD.load_dem_hillshade(ax, _MOD.DATA_DIR, alpha=0.35)
        except Exception as e:
            warnings.warn(f"DEM hillshade failed: {e}")

    # Difference surface — drawn BEFORE KML overlays so they sit on top
    im = ax.pcolormesh(gx, gy, surf, cmap=cmap,
                       norm=norm, shading="auto", alpha=0.85, zorder=3)

    # KML overlays on top of surface
    if _MOD is not None and _FEATURES:
        try:
            _MOD._base_map(ax, _FEATURES,
                f"Δ {lbl}\n{label} vs Baseline")
        except Exception as e:
            warnings.warn(f"_base_map failed: {e}")
            ax.set_title(f"Δ {lbl} — {label} vs Baseline",
                         fontsize=FT, fontweight="bold")
    else:
        ax.set_title(f"Δ {lbl} — {label} vs Baseline",
                     fontsize=FT, fontweight="bold")

    # Well scatter
    sc = ax.scatter(pts[valid,0], pts[valid,1],
                    c=delta_vals[valid], cmap=cmap, norm=norm,
                    s=40, edgecolors="k", linewidths=0.4, zorder=5)

    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, extend="both")
    if cmap == "YlOrRd":
        cb_txt = f"|Δ| {lbl} ({units})  Magnitude of change"
    elif cmap == "RdBu":
        # positive=blue=wetter, negative=red=drier
        cb_txt = f"Δ {lbl} ({units})  Blue = wetter  |  Red = drier"
    else:
        # RdBu_r: positive=red=drier, negative=blue=wetter
        cb_txt = f"Δ {lbl} ({units})  Red = more/drier  |  Blue = less/wetter"
    cb.set_label(cb_txt, fontsize=FC)
    cb.ax.tick_params(labelsize=FK)

    mean_d = float(np.nanmean(delta_vals[valid]))
    ax.annotate(
        f"Mean Δ = {mean_d:+.4f} {units}\n"
        f"p5 = {p5:+.4f}  p95 = {p95:+.4f}",
        xy=(0.02, 0.02), xycoords="axes fraction", fontsize=FA,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=FL)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=FL)
    ax.tick_params(labelsize=FK)
    fig.tight_layout()
    print(f"    [DEBUG] saving {Path(out_path).name} as {DIFF_MAP_FORMAT} (format={DIFF_MAP_FORMAT})")
    if DIFF_MAP_FORMAT == "jpg":
        fig.savefig(out_path, dpi=FIG_DPI, bbox_inches="tight",
                    format="jpeg", pil_kwargs={"quality": DIFF_MAP_QUALITY})
    else:
        fig.savefig(out_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)


# ── Generate all diff maps for one scenario ────────────────────────────────────
def diff_one_scenario(subfolder, label, base_dir, diff_dir):
    wb_base = load_wb(Path(base_dir) / "baseline")
    wb_scen = load_wb(Path(base_dir) / subfolder)
    if wb_base is None or wb_scen is None:
        warnings.warn(f"Missing CSV for {subfolder} — skipping")
        return

    gx, gy = load_grid(base_dir)
    if gx is None:
        warnings.warn("No baseline grid CSV — skipping")
        return

    # Merge on well name
    mg = wb_base.merge(wb_scen, on="well", suffixes=("_b","_s"))
    pts = mg[["E_b","N_b"]].values

    out_dir = diff_dir / subfolder
    out_dir.mkdir(parents=True, exist_ok=True)

    n_saved = 0
    for col, lbl, units, cmap, thresh in DIFF_FIELDS:
        col_b = col + "_b"
        col_s = col + "_s"
        if col_b not in mg.columns or col_s not in mg.columns:
            print(f"    {col}: not in CSV — skipping (rerun full pipeline)")
            continue

        delta = (mg[col_s] - mg[col_b]).values.astype(float)

        # Skip if well-level values show no meaningful change
        max_abs = np.nanmax(np.abs(delta))
        # Use a relative check too: skip if range < 1% of mean baseline value
        mean_base_val = mg[col+"_b"].abs().mean() if col+"_b" in mg.columns else 1.0
        rel_thresh = max(thresh, mean_base_val * 0.0001)
        if max_abs < rel_thresh:
            print(f"    {col}: max|Δ|={max_abs:.2e} — skipping (no meaningful change)")
            continue

        out = out_dir / f"diff_{subfolder}_{col}.{DIFF_MAP_FORMAT}"
        plot_diff_map(col, lbl, units, cmap, delta, pts, gx, gy, label,
                      subfolder, out)
        print(f"    {col}: saved  (mean Δ = {np.nanmean(delta):+.4f} {units})")
        n_saved += 1

    print(f"  {subfolder}: {n_saved} maps saved")


def plot_difference_maps(base_dir, scenarios, diff_dir, mod=None):
    diff_dir.mkdir(parents=True, exist_ok=True)
    # Remove ALL existing diff map PNGs before regenerating
    # This prevents stale files from previous runs appearing in the viewer
    for sf_dir in diff_dir.iterdir():
        if sf_dir.is_dir():
            for old_file in list(sf_dir.glob("diff_*.png")) + list(sf_dir.glob("diff_*.jpg")):
                old_file.unlink()
                print(f"  Removed stale: {sf_dir.name}/{old_file.name}")
    for _, sf, params, label in scenarios:
        if sf == "baseline":
            continue
        print(f"\n  Difference maps: {label}")
        diff_one_scenario(sf, label, base_dir, diff_dir)


# ── Hydrographs ────────────────────────────────────────────────────────────────
def plot_cluster_hydrographs(base_dir, scenarios, diff_dir):
    diff_dir.mkdir(parents=True, exist_ok=True)
    clusters = ["C1","C2","C3","C4"]
    x = np.arange(1,13)
    fig, axes = plt.subplots(2, 3,
                             figsize=(14.0*1.05, 5.8*1.85),
                             dpi=FIG_DPI, sharex=True, sharey=True)
    axes = axes.ravel()
    for ax, (_, sf, params, slabel) in zip(axes, scenarios):
        for c in clusters:
            base_cyc = np.array(SEASONAL_CYCLE[c])
            shift    = SCENARIO_SHIFTS.get(sf, {}).get(c, 0.0)
            col      = CLUSTER_COLOURS[c]
            ax.plot(x, base_cyc, color=col, lw=0.9, ls="--", alpha=0.4, zorder=2)
            ax.plot(x, base_cyc + shift, color=col, lw=2.0, ls="-",
                    zorder=3, label=CLUSTER_LABELS[c])
        ax.axhline(0.61, color="#1565C0", lw=1.2, ls="--", zorder=4,
                   label="SD15b (0.61 m)")
        ax.axhline(0.98, color="#E65100", lw=1.2, ls="--", zorder=4,
                   label="SD16 (0.98 m)")
        ax.axhline(0.0,  color="navy",   lw=0.7, ls="-",  zorder=4,
                   label="Ground surface")
        ax.axvspan(4.5, 9.5, alpha=0.07, color="gold", zorder=1)
        ax.set_xticks(x)
        ax.set_xticklabels(MONTHS, fontsize=FK+1, rotation=45, ha="right")
        ax.tick_params(labelsize=FK+1)
        ax.grid(axis="y", lw=0.4, color="lightgrey", zorder=0)
        title_col = ("black" if sf == "baseline" else
                     "#8B0000" if any(SCENARIO_SHIFTS.get(sf,{}).get(c,0)>0.05
                                     for c in clusters) else "#004D00")
        ax.set_title(slabel, fontsize=FT+1, fontweight="bold",
                     color=title_col, pad=6)
        if sf in FOREST_SCENARIOS:
            ax.annotate("Direct shift: C4 only", xy=(0.97,0.97),
                        xycoords="axes fraction", fontsize=FA+1,
                        ha="right", va="top",
                        bbox=dict(boxstyle="round,pad=0.3",fc="white",alpha=0.75))
    for ax in axes:
        ax.set_ylim(2.0, -0.15)
    for ax in axes[::3]:
        ax.set_ylabel("Depth below ground (m)\n0 = surface", fontsize=FL)
    hs, ls_ = axes[0].get_legend_handles_labels()
    seen = {}
    for h, l in zip(hs, ls_):
        if l not in seen: seen[l] = h
    cl_i = [(l,h) for l,h in seen.items() if l.startswith("C")]
    th_i = [(l,h) for l,h in seen.items() if not l.startswith("C")]
    proxy = mlines.Line2D([],[],color="grey",lw=0.9,ls="--",alpha=0.5,
                          label="Baseline (dashed)")
    all_h = [h for _,h in cl_i+th_i]+[proxy]
    all_l = [l for l,_ in cl_i+th_i]+["Baseline (dashed)"]
    fig.legend(all_h, all_l, loc="lower center", ncol=min(len(all_h),4),
               fontsize=FA+2, framealpha=0.92, bbox_to_anchor=(0.5,-0.01))
    fig.suptitle(
        "Seasonal Water Table Profiles — Depth Below Ground (m)\n"
        "Solid = scenario  |  Dashed = baseline  |  "
        "Gold = summer  |  Thresholds: Curreli et al. (2013)",
        fontsize=FT+1, fontweight="bold")
    fig.tight_layout(rect=[0,0.07,1,1])
    out = diff_dir / "cluster_hydrographs.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


def plot_scenario_summary(base_dir, scenarios, diff_dir):
    diff_dir.mkdir(parents=True, exist_ok=True)
    clusters = ["C1","C2","C3","C4"]
    non_b = [(sk,sf,p,lb) for sk,sf,p,lb in scenarios if sf!="baseline"]
    x = np.arange(len(clusters))
    n = len(non_b)
    offs = np.linspace(-(n-1)/2,(n-1)/2,n)*0.15
    short = {"forest_removal":"Clearfell","forest_thinning":"Thinning",
             "species_change":"Broadleaf","climate_dry":"Climate dry",
             "climate_wet":"Climate wet"}
    fig, ax = plt.subplots(figsize=(14.0*0.65, 5.8), dpi=FIG_DPI)
    for i,(_,sf,p,lb) in enumerate(non_b):
        ds = [SCENARIO_SHIFTS.get(sf,{}).get(c,0.0) for c in clusters]
        ax.bar(x+offs[i], ds, width=0.13,
               color=SCENARIO_COLOURS.get(sf,"grey"),
               alpha=0.85, zorder=3, label=short.get(sf,sf))
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([CLUSTER_LABELS[c] for c in clusters], fontsize=FK)
    ax.set_ylabel("Δ Summer minimum depth (m)\nPositive = deeper (drier)", fontsize=FL)
    ax.tick_params(labelsize=FK)
    ax.legend(fontsize=FA, loc="lower left", framealpha=0.9)
    ax.grid(axis="y", lw=0.4, color="lightgrey")
    fig.suptitle("Scenario Comparison — Δ Summer Minimum Depth by Cluster",
                 fontsize=FT, fontweight="bold")
    fig.tight_layout()
    out = diff_dir / "scenario_summary.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main(diff_only=False):
    global _MOD, _FEATURES
    base_dir = OUT_DIR / "19_spatial_groundwater"
    diff_dir = base_dir / "difference_maps"
    print("19a_scenario_runner.py  v2026-04-13-clean")

    spec = importlib.util.spec_from_file_location(
        "script19", SRC_DIR / "19_spatial_groundwater.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["script19"] = mod
    spec.loader.exec_module(mod)
    _MOD = mod

    try:
        _FEATURES = mod.load_kml_features()
        print(f"  KML features: {len(_FEATURES)} layers")
    except Exception:
        _FEATURES = None

    if not diff_only:
        for sk, sf, p, lb in SCENARIOS:
            try:
                run_scenario(sk, sf, p, lb, base_dir, mod)
            except Exception as e:
                warnings.warn(f"Scenario '{sf}' failed: {e}")
                import traceback; traceback.print_exc()

    print(f"\n{'='*70}\n  GENERATING DIFFERENCE MAPS\n{'='*70}")
    plot_difference_maps(base_dir, SCENARIOS, diff_dir, mod=mod)
    plot_scenario_summary(base_dir, SCENARIOS, diff_dir)
    plot_cluster_hydrographs(base_dir, SCENARIOS, diff_dir)
    print(f"\nOutputs: {base_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff-only", action="store_true")
    args = parser.parse_args()
    main(diff_only=args.diff_only)
