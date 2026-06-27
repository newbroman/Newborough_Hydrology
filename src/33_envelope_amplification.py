"""
33_envelope_amplification.py — Climate-swing amplification and dry-year spring depth
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
  * Exclusions: Llyn Rhos-Ddu lake gauge only. CEH13/CEH14 (MSL5/SSM-excluded for SSM
  *   reasons) are INCLUDED here — the coefficient is observational and does not use the SSM.
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
    33_dry_spring_depth.png           dry-year spring water-table depth (ecological companion)
    33_results.txt                    console summary + robustness table

Version: 1.1.0 (2026-06-27)

Changelog
---------
1.1.0 (2026-06-27)
  * Canonical wet extreme now includes 2016 (config.ENVELOPE_WET_YEARS); 2016 is the
    wettest-antecedent recharge season on record (697 mm Oct-Mar), the mirror of the
    2006 exclusion. Recovers CEH8/CEH15 into the panel with proper multi-year wet
    states. Network-mean swing 752 -> 735 mm; forest/lake anchor unchanged.
  * Added a second, deliberately separate RECENT-window pass (config.ENVELOPE_RECENT_*)
    so the 2014-2017-installed wells (CEH40/41/42, FE1/2/3, NW8b) can be mapped on an
    envelope they actually observed. Renders *_recent.png companions. The recent dry
    extreme is milder than 2011/12, so the recent panels are captioned as a conservative
    recent lower bound and are NOT magnitude-comparable to the canonical panels.
  * Extended wells absent from 03_master_data now take a cluster from the committed
    Script 06 Pearson membership audit (Best_Match_Cluster) — traceable, no hand-labelling.
  * CEH7 (single dry-extreme year) admitted as a flagged marker only
    (config.ENVELOPE_FLAGGED_SINGLE_DRY): shown as a point but excluded from the surface
    AND from the network-mean denominator, so its noisy n_dry=1 swing cannot distort the field.
1.0.0 (2026-06-26)
  * Initial release: climate-swing amplification field + dry-year spring-depth surface.
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
from utils import envelope_metric as em
from utils.map_utils import load_dem_hillshade, add_kml_features, add_idw_surface, add_en_axes
from utils.console_utils import banner, phase, step, info, saved, note, result, done, hr

SCRIPT_ID = "33"
VERSION = "1.1.0"

# --- method constants (from utils.config; spec-locked 2026-06-26 / 2026-06-27) -----
SPRING_MONTHS = config.MSL_SPRING_MONTHS
DRY_YEARS = config.ENVELOPE_DRY_YEARS
WET_YEARS = config.ENVELOPE_WET_YEARS
RECENT_DRY_YEARS = config.ENVELOPE_RECENT_DRY_YEARS
RECENT_WET_YEARS = config.ENVELOPE_RECENT_WET_YEARS
FLAGGED_SINGLE_DRY = set(w.lower() for w in config.ENVELOPE_FLAGGED_SINGLE_DRY)
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
OUT_FIG_DRY_SPRING = paths.OUT_33_FIG_DRY_SPRING
OUT_CSV_RECENT = paths.OUT_33_PER_WELL_RECENT
OUT_FIG_AMP_RECENT = paths.OUT_33_FIG_AMP_RECENT
OUT_FIG_DRY_SPRING_RECENT = paths.OUT_33_FIG_DRY_SPRING_RECENT

IN_WELLS = paths.INT_WELLS_CLEAN
IN_LOCATIONS = paths.INT_LOCATIONS
IN_MASTER = paths.OUT_DIR / "03_master_data.csv"
IN_MEMBERSHIP = paths.OUT_DIR / "06_pear_membership_audit_sitewide.csv"


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
    membership = None
    if IN_MEMBERSHIP.exists():
        membership = pd.read_csv(IN_MEMBERSHIP)
        membership["key"] = membership["Well_Normalised"].astype(str).str.lower().str.strip()
    return levels, loc, master, membership


def fill_clusters_from_pearson(df, membership):
    """Fill any cluster missing from 03_master_data from the committed Script 06 Pearson
    membership audit (Best_Match_Cluster). Extended/short-record wells (FE1/2/3, NW8b, ...)
    are not fitted in the SSM/clustering pipeline, so they carry no master cluster; their
    Pearson best-match is the traceable, committed source of their cluster label."""
    if membership is None:
        return df
    bm = membership.set_index("key")["Best_Match_Cluster"].to_dict()
    miss = df["Cluster"].isna()
    df.loc[miss, "Cluster"] = df.loc[miss, "key"].map(bm)
    return df


def spring_year_table(levels):
    spring = levels[levels.index.month.isin(SPRING_MONTHS)]
    return spring.groupby(spring.index.year).mean(numeric_only=True)


def extreme_states(yr, dry_years, wet_years, excluded, flagged=None, min_years=None):
    """Per-well mean state at the dry and wet extremes, with coverage filter.

    Wells passing the >= min_years gate on BOTH extremes are admitted normally. Wells in
    `flagged` are additionally admitted on a single-year minimum (n>=1 each) but tagged
    flagged=True; callers exclude flagged wells from the interpolated surface and from the
    network-mean denominator (their single-year swing is too noisy to shape the field)."""
    flagged = set(flagged or [])
    min_years = MIN_YEARS_PER_EXTREME if min_years is None else min_years
    dsub, wsub = yr.loc[dry_years], yr.loc[wet_years]
    dry, wet = dsub.mean(skipna=True), wsub.mean(skipna=True)
    nd, nw = dsub.notna().sum(), wsub.notna().sum()
    df = pd.DataFrame({"dry_m": dry, "wet_m": wet, "n_dry": nd, "n_wet": nw})
    df["key"] = df.index.str.lower().str.strip()
    gate = (df.n_dry >= min_years) & (df.n_wet >= min_years)
    flag = df.key.isin(flagged) & (df.n_dry >= 1) & (df.n_wet >= 1) & ~gate
    df = df[gate | flag].copy()
    df = df[~df.key.isin(excluded)].copy()
    df["flagged"] = df.key.isin(flagged) & ~gate.reindex(df.index).fillna(False)
    df["swing_mm"] = (df.wet_m - df.dry_m) * 1000.0
    return df


def add_amplification(df):
    """Amplification = well swing / network-mean swing. The network mean is computed over
    the unflagged wells only, so a noisy single-year (flagged) well cannot move the
    denominator; flagged wells still receive an amplification value for display."""
    ref = df.loc[~df.get("flagged", False), "swing_mm"] if "flagged" in df else df.swing_mm
    net = ref.mean()
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


def linear_surface(GX, GY, px, py, pv, mask=IDW_MASK_M):
    """Linear (triangulation) interpolation of a per-well field — clean regional
    gradients with no IDW bullseyes, so threshold contours separate wells by which
    side they truly fall on. NaN outside the convex hull and beyond `mask` m of any
    well. Used for the Figure 60 envelope panels (the per-well values are unchanged;
    this affects only how the surface is drawn between wells)."""
    from scipy.interpolate import griddata
    Z = griddata(np.column_stack([px, py]), pv, (GX, GY), method="linear")
    nearest = np.full_like(GX, 1e18)
    for x, y in zip(px, py):
        nearest = np.minimum(nearest, np.sqrt((GX - x) ** 2 + (GY - y) ** 2))
    Z[nearest > mask] = np.nan
    return Z


def _finish_map_axes(ax):
    """Easting/Northing axes to scale — restores the OS-grid scale on the report maps.
    Extent is set in _envelope_base; here we only (re)apply aspect + E/N axes."""
    add_en_axes(ax, apply_extent=False, osgb_label=False)


def _sample_dem(px, py, dem_e_arr, dem_n_arr, dem_data):
    """Ground elevation at each well, sampled from the DEM raster (for ridge masking)."""
    from scipy.interpolate import RegularGridInterpolator
    f = RegularGridInterpolator((dem_n_arr[::-1], dem_e_arr), dem_data[::-1, :],
                                method="linear", bounds_error=False, fill_value=np.nan)
    return f(np.column_stack([py, px]))


def _envelope_base(ax, df, value_col, cmap, norm=None, ridge=True):
    """Hillshade base + LINEAR surface (map_utils.add_idw_surface) with the KML features
    on top. When ridge=True, inter-dune ridges (DEM > interpolated well-ground surface by
    >1 m) are masked. Returns (mesh, gx, gy, Zmasked) for the colorbar and contours."""
    _, dem_loaded, dem_e_arr, dem_n_arr, dem_data = load_dem_hillshade(
        ax, paths.DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    add_en_axes(ax, osgb_label=False)
    dfx = df.copy()
    use_ridge = ridge and dem_loaded
    if use_ridge:
        dfx["dem"] = _sample_dem(dfx.E.values, dfx.N.values, dem_e_arr, dem_n_arr, dem_data)
    mesh, gx, gy, Zm = add_idw_surface(
        ax, dfx, value_col=value_col, easting_col="E", northing_col="N", dem_col="dem",
        method="linear", ridge_mask_threshold=1.0 if use_ridge else None,
        dem_e_arr=dem_e_arr if use_ridge else None,
        dem_n_arr=dem_n_arr if use_ridge else None,
        dem_data=dem_data if use_ridge else None,
        cmap=cmap, norm=norm, alpha=1.0, zorder=1.5)
    add_kml_features(ax, paths.DATA_DIR)
    return mesh, gx, gy, Zm


def fig_amplification(df, GX, GY, out_path, title=None):
    colours = config.get_cluster_colours(); labels = config.CLUSTER_LABELS
    norm = TwoSlopeNorm(vcenter=1.0, vmin=0.55, vmax=1.55)
    fig, ax = plt.subplots(figsize=(11, 9))
    flg = df.get("flagged", pd.Series(False, index=df.index)).fillna(False)
    surf_df = df[~flg]                                   # flagged wells excluded from the field
    im, gx, gy, Zm = _envelope_base(ax, surf_df, "amplification", "RdBu_r", norm=norm, ridge=False)
    for cid in sorted(df.Cluster.dropna().unique()):
        s = df[(df.Cluster == cid) & ~flg]
        ax.scatter(s.E, s.N, c=[colours.get(int(cid), "#444")], edgecolor="k",
                   linewidth=0.5, s=48, zorder=5, label=labels.get(int(cid), f"C{int(cid)}"))
    no = df[df.Cluster.isna() & ~flg]
    if len(no):
        ax.scatter(no.E, no.N, facecolor="none", edgecolor="k", marker="s", s=46,
                   linewidths=1.2, zorder=5, label="extended (unclustered)")
    fl = df[flg]
    if len(fl):
        ax.scatter(fl.E, fl.N, facecolor="none", edgecolor="k", marker="^", s=90,
                   linewidths=1.6, zorder=6, label="lower-confidence well\n(Tier B/C; off-surface)")
    _finish_map_axes(ax)
    ax.legend(fontsize=8.5, loc="lower left", framealpha=0.9, title="cluster")
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.01)
    cb.set_label("climate-swing amplification  (well swing / network mean)\n"
                 ">1 amplifies the common swing   <1 damps it", fontsize=9.5)
    if title is None:
        title = ("Newborough Warren: climate-swing amplification field (relative, common-mode removed)\n"
                 "Forest interior amplifies; lake edge damps. Window-independent. Lake gauge excluded.")
    ax.set_title(title, fontsize=10.5, loc="left")
    fig.savefig(out_path, dpi=160, bbox_inches="tight"); plt.close(fig)


def fig_dry_spring_depth(df, GX, GY, out_path, title=None):
    """Dry-year SPRING water-table depth (seasonal high). Curreli summer-minimum
    thresholds overlaid mark where even the spring high has already breached wet/dry
    slack viability. Inter-dune ridges are masked (add_idw_surface ridge mask)."""
    dfx = df.copy(); dfx["dry_mm"] = dfx.dry_m * 1000.0
    fig, ax = plt.subplots(figsize=(11, 9))
    # exclude slack-edge wells (CEH10) and any flagged single-dry-year wells from the
    # SURFACE only; both are kept and shown distinctly as markers
    excl = set(getattr(config, "ENVELOPE_DEPTH_INTERP_EXCLUDE", set()))
    flg = dfx.get("flagged", pd.Series(False, index=dfx.index)).fillna(False)
    interp_df = dfx[~dfx.key.isin(excl) & ~flg]
    im, gx, gy, Zm = _envelope_base(ax, interp_df, "dry_mm", "YlOrBr_r")
    # Curreli thresholds: distinct SOLID colours + white halo, on the ridge-masked grid
    sorted_levels = sorted(ECO_THRESHOLDS_MM)            # [-980 (SD16), -610 (SD15b)]
    level_colour = {ECO_THRESHOLDS_MM[0]: "#00CED1",     # SD15b wet slack  -> turquoise
                    ECO_THRESHOLDS_MM[1]: "#D7191C"}     # SD16 dry slack   -> red
    ax.contour(gx, gy, Zm, levels=sorted_levels, colors="white",
               linewidths=3.4, linestyles="solid", zorder=3.9)
    cs = ax.contour(gx, gy, Zm, levels=sorted_levels,
                    colors=[level_colour[l] for l in sorted_levels],
                    linewidths=1.8, linestyles="solid", zorder=4)
    labels = getattr(config, "ENVELOPE_ECO_THRESHOLD_LABELS", {})
    fmt = {t: labels.get(t, f"{t/1000:.2f} m") for t in ECO_THRESHOLDS_MM}
    ax.clabel(cs, fmt=fmt, fontsize=8)
    # markers: regular wells as dots; slack-edge (diamond) and flagged single-dry (triangle) distinct
    reg = df[~df.key.isin(excl) & ~flg]; edge = df[df.key.isin(excl)]; fl = df[flg]
    ax.scatter(reg.E.values, reg.N.values, c="k", s=12, zorder=5)
    if len(edge):
        ax.scatter(edge.E.values, edge.N.values, facecolor="none", edgecolor="k",
                   marker="D", s=60, linewidths=1.5, zorder=6)
    if len(fl):
        ax.scatter(fl.E.values, fl.N.values, facecolor="none", edgecolor="k",
                   marker="^", s=80, linewidths=1.5, zorder=6)
    from matplotlib.lines import Line2D
    leg1 = ax.legend(handles=[Line2D([0], [0], color=level_colour[ECO_THRESHOLDS_MM[0]], lw=2.2,
                                     label=labels.get(ECO_THRESHOLDS_MM[0], "SD15b")),
                              Line2D([0], [0], color=level_colour[ECO_THRESHOLDS_MM[1]], lw=2.2,
                                     label=labels.get(ECO_THRESHOLDS_MM[1], "SD16"))],
                     fontsize=8.5, loc="lower left", framealpha=0.9, title="Curreli thresholds")
    ax.add_artist(leg1)
    extra = []
    if len(edge):
        extra.append(Line2D([0], [0], marker="D", markerfacecolor="none", markeredgecolor="k",
                            markeredgewidth=1.5, linestyle="none", markersize=8,
                            label="raised inter-slack well\n(slack edge; excluded from surface)"))
    if len(fl):
        extra.append(Line2D([0], [0], marker="^", markerfacecolor="none", markeredgecolor="k",
                            markeredgewidth=1.5, linestyle="none", markersize=8,
                            label="single dry-year well\n(flagged; excluded from surface)"))
    if extra:
        ax.legend(handles=extra, fontsize=8, loc="lower right", framealpha=0.9)
    _finish_map_axes(ax)
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.01)
    cb.set_label("dry-year spring depth to water (mm below ground)", fontsize=9.5)
    if title is None:
        title = ("Newborough Warren: dry-year spring water-table depth (springs 2011/12/19)\n"
                 "Contours: where even the spring high is already below Curreli SD15b/SD16 "
                 "(summer-minimum) thresholds. Inter-dune ridges masked. Lake gauge excluded.")
    ax.set_title(title, fontsize=10.5, loc="left")
    fig.savefig(out_path, dpi=160, bbox_inches="tight"); plt.close(fig)


def build_panel(yr, loc, master, membership, excluded, dry, wet, flagged=None):
    """Assemble the per-well envelope panel for a given dry/wet window: extreme states,
    Pearson cluster fallback for master-absent wells, locations, and amplification.
    Used for the DROUGHT-FLOOR panel (dry_m over the canonical dry years) and the recent
    drought-floor panel."""
    df = extreme_states(yr, dry, wet, excluded, flagged=flagged)
    df = df.merge(master[["key", "Cluster"]], on="key", how="left")
    df = fill_clusters_from_pearson(df, membership)
    df = df.merge(loc[["key", "E", "N"]], on="key", how="left").dropna(subset=["E", "N"])
    df, net = add_amplification(df)
    return df, net


def build_amp_panel(yr, loc, master, membership, excluded, dry_pool, wet_pool):
    """Assemble the AMPLIFICATION panel (Figure 60a) using the shared CO-TEMPORAL coefficient
    (utils.envelope_metric) — artefact-free, the published surface (Option A, 2026-06-27).
    Tier-A wells form the interpolated surface; Tier B/C are held off-surface as markers."""
    df = em.coefficients(yr, dry_pool, wet_pool, excluded, ref_min_wet=config.ENVELOPE_METRIC_REF_MIN_WET)
    df = df.merge(master[["key", "Cluster"]], on="key", how="left")
    df = fill_clusters_from_pearson(df, membership)
    df = df.merge(loc[["key", "E", "N"]], on="key", how="left").dropna(subset=["E", "N"])
    df["amplification"] = df["amp_coefficient"]
    df["flagged"] = df["tier"] != "A"        # Tier B/C off-surface (lower confidence)
    net = df.loc[~df.flagged, "swing_mm"].mean()
    return df, net


def _cluster_report(df):
    by = df[~df.get("flagged", False)].groupby("Cluster")["amplification"].agg(["mean", "count"]).round(2)
    for cid, row in by.iterrows():
        step(f"{config.CLUSTER_LABELS.get(int(cid), f'C{int(cid)}'):20s} "
             f"amplification {row['mean']:.2f}x  (n={int(row['count'])})")
    return by


def main() -> int:
    banner(SCRIPT_ID, "Climate-swing amplification + dry-year spring depth", VERSION)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    phase(1, "Load inputs")
    levels, loc, master, membership = load_inputs()
    yr = spring_year_table(levels)
    # Blanket include (2026-06-27): the envelope is observational, so CEH13/CEH14 (SSM-failures,
    # MSL5-excluded for SSM reasons) are INCLUDED here — only the lake gauge is dropped. The
    # MSL5 exclusion is retained in the SSM/MSL5 analyses (Scripts 20/26), not here.
    excluded = set(config.ENVELOPE_METRIC_EXCLUDE) | LAKE_GAUGE_KEYS
    info(f"canonical: dry {DRY_YEARS}; wet {WET_YEARS}")
    note("2006 excluded from wet extreme (driest-in-record 2004-2005 antecedent); "
         "2016 included (wettest-antecedent recharge season on record)")
    if FLAGGED_SINGLE_DRY:
        note(f"flagged single dry-year wells (marker only, off-surface): {sorted(FLAGGED_SINGLE_DRY)}")

    # ---- Canonical (long-record) panels ------------------------------------------
    phase(2, "Canonical amplification (co-temporal) + drought-floor states")
    # Amplification surface (Fig 60a): shared co-temporal coefficient over the CANONICAL
    # driest/wettest extremes (faithful to "driest and wettest springs"; swing ~0.73 m),
    # artefact-free (Option A). Script 35 uses the wider metric pools for its per-well table.
    df, net = build_amp_panel(yr, loc, master, membership, excluded, DRY_YEARS, WET_YEARS)
    n_off = int(df["flagged"].sum())
    result("amplification wells", f"{len(df)} ({n_off} Tier B/C off-surface)")
    by_cluster = _cluster_report(df)
    # Drought-floor states (Fig 60b): absolute dry-year spring depth over the canonical dry years.
    dep_df, _ = build_panel(yr, loc, master, membership, excluded, DRY_YEARS, WET_YEARS,
                            flagged=FLAGGED_SINGLE_DRY)

    phase(3, "Robustness to extreme-year choice")
    rob_lines = ["robustness — cluster amplification across year-set choices (naive normalisation):"]
    rob_lines.append("  set              " + "  ".join(f"C{c}" for c in [1, 2, 3, 4, 5]))
    for name, (dy, wy) in ROBUSTNESS_SETS.items():
        rdf = extreme_states(yr, dy, wy, excluded).merge(master[["key", "Cluster"]], on="key", how="left")
        rdf = fill_clusters_from_pearson(rdf, membership)
        rdf, _ = add_amplification(rdf)
        means = rdf.groupby("Cluster")["amplification"].mean()
        rob_lines.append(f"  {name:15s}  " + "  ".join(f"{means.get(c, np.nan):.2f}" for c in [1, 2, 3, 4, 5]))
    for ln in rob_lines:
        print(ln)

    phase(4, "Render canonical figures")
    GX, GY = _grid(loc)
    amp_title = ("Newborough Warren: climate-swing amplification field (co-temporal, common-mode removed)\n"
                 "Forest interior amplifies; lake edge damps. Artefact-free co-temporal coefficient. Lake gauge excluded.")
    fig_amplification(df[~df.flagged], GX, GY, OUT_FIG_AMP, title=amp_title); saved(OUT_FIG_AMP)
    fig_dry_spring_depth(dep_df, GX, GY, OUT_FIG_DRY_SPRING); saved(OUT_FIG_DRY_SPRING)

    # ---- Recent (extended-network) panels -----------------------------------------
    phase(5, "Recent-window panels (extended network)")
    info(f"recent: dry {RECENT_DRY_YEARS}; wet {RECENT_WET_YEARS}")
    rdf, rnet = build_amp_panel(yr, loc, master, membership, excluded,
                                RECENT_DRY_YEARS, RECENT_WET_YEARS)
    rdep_df, _ = build_panel(yr, loc, master, membership, excluded, RECENT_DRY_YEARS, RECENT_WET_YEARS)
    result("recent amplification wells", str(len(rdf)))
    _cluster_report(rdf)
    amp_recent_title = (
        f"Newborough Warren (recent, extended network): climate-swing amplification\n"
        f"dry {'/'.join(str(y)[2:] for y in RECENT_DRY_YEARS)} vs wet "
        f"{'/'.join(str(y)[2:] for y in RECENT_WET_YEARS)}. Extended wells clustered via Script 06 "
        f"Pearson. Milder extremes — NOT magnitude-comparable to the long-record panel.")
    dry_recent_title = (
        f"Newborough Warren (recent, extended network): dry-spring water-table depth\n"
        f"springs {'/'.join(str(y)[2:] for y in RECENT_DRY_YEARS)}. RECENT minimum (milder than "
        f"2011/12) — a conservative lower bound. Curreli SD15b/SD16 contours. Ridges masked.")
    fig_amplification(rdf[~rdf.flagged], GX, GY, OUT_FIG_AMP_RECENT, title=amp_recent_title); saved(OUT_FIG_AMP_RECENT)
    fig_dry_spring_depth(rdep_df, GX, GY, OUT_FIG_DRY_SPRING_RECENT, title=dry_recent_title); saved(OUT_FIG_DRY_SPRING_RECENT)

    # ---- Write outputs -----------------------------------------------------------
    phase(6, "Write outputs")
    keep = ["key", "Cluster", "E", "N", "dry_m", "wet_m", "swing_mm", "amplification",
            "n_dry", "n_wet", "flagged"]
    df[[c for c in keep if c in df.columns]].to_csv(OUT_CSV, index=False); saved(OUT_CSV)
    rdf[[c for c in keep if c in rdf.columns]].to_csv(OUT_CSV_RECENT, index=False); saved(OUT_CSV_RECENT)
    OUT_TXT.write_text(
        f"CANONICAL amplification — CO-TEMPORAL coefficient over driest/wettest extremes "
        f"(dry {DRY_YEARS}, wet {WET_YEARS})\n"
        f"Tier-A site-mean swing {net:.0f} mm; wells {len(df)} ({n_off} Tier B/C off-surface)\n"
        f"drought-floor states over canonical dry years {DRY_YEARS}\n\n"
        + by_cluster.to_string() + "\n\n" + "\n".join(rob_lines) + "\n\n"
        f"RECENT amplification (co-temporal; dry {RECENT_DRY_YEARS}, wet {RECENT_WET_YEARS})\n"
        f"Tier-A mean swing {rnet:.0f} mm; wells {len(rdf)}\n"
        f"NOTE: recent dry extreme is milder than 2011/12; recent panel is a conservative\n"
        f"recent lower bound and is NOT magnitude-comparable to the canonical panel.\n")
    saved(OUT_TXT)
    hr()
    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
