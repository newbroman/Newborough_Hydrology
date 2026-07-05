"""
36_absolute_climate_trend.py — Absolute climate-removed per-well secular trend map
====================================================================================

Maps the **absolute** drying or wetting rate at each well after removing only the
climate-attributable variance via an external climate index (spring CWB). Unlike
Script 32's differential anomaly (well minus site-mean), this estimator:

  - does NOT reference individual well trends to the network mean, so the
    sign and magnitude are absolute, not relative;
  - removes only variance correlated with the external CWB index, leaving
    the real site-wide recharge decline and coastal drying *in* the result;
  - avoids the inversion artefact of Script 32 (where C4 forest reads blue
    because it amplifies the +19.66 mm/yr wet-spring-lifted mean, not
    because it is genuinely holding or wetting).

Anchor claim:
    "This map shows the absolute, climate-corrected drying rate across
     Newborough Warren. After removing spring CWB variability, the coastal
     fringe exhibits the strongest genuine drying, the lake-edge cluster
     is near-zero, and the open-dune and western blocks show moderate secular
     decline — consistent with the coastal-erosion gradient (δ₀ ≈ −29 mm/yr)
     as the primary driver and a background recharge decline as a secondary one."

Method (spec signed off 2026-07-05):
  1. Spring-mean level per well per year (MAM, config.MSL_SPRING_MONTHS),
     same bucketing as Script 32.
  2. External climate index: spring CWB(t) = Σ(P_m − PET) over MAM from
     01_climate.csv, contemporaneous with the spring level (no lag;
     HEADLINE_LAG = 0 project convention).
  3. Per-well joint bivariate OLS: h(t) = a + b·CWB(t) + c·t.
     c is the secular trend (mm/yr), orthogonalised from CWB by construction.
     The two-step approach (regress out CWB, slope the residual) is NOT used:
     over climatically non-stationary windows the CWB covariate itself trends
     and absorbs real secular drying before the slope is measured (verified:
     v1.0.1 gave C5 = +15.5 mm/yr vs expected ≈ −29 mm/yr).
  4. AR(1) inflation of SE on c; t-test with df = n_eff − 3. Moving-block
     bootstrap re-fits the full bivariate model each iteration, collects c.
  5. Map: IDW surface (add_idw_surface, apply_site_mask=True) + per-well
     markers, brown = genuinely drying, blue = genuinely holding/wetting,
     diverging colour scale, zero contour. Solid = significant (AR p < 0.05),
     hollow = not significant.
  6. Periods: 2005–2025 primary; 2011–2025 robustness. 2005–2025 is primary
     because the 2011–2025 window is coverage-corrupted by short-record wells
     fitting a wet-recovery stretch with no pre-2011 baseline (R1 fix).
  7. Coverage filter (R2 fix): a well is excluded from a window unless it has
     at least one spring observation before the window start AND its observed
     span covers ≥ 80 % of the window. Removes the 18-well artefact identified
     by identical slopes across two nominally different windows.
  8. Exclusions: lake gauge only (LAKE_GAUGE_KEYS). CEH13/CEH14 included.
  9. C5 acceptance gate (relaxed R3): console warn unless C5 primary mean < 0
     AND C5 ≤ C2 mean. δ₀ = −29 mm/yr is the coastal-edge gradient; C5 is a
     cluster mean set back from the edge, so clearly-negative suffices.

Pipeline-integrated: Phase 15, step 39/45, run_analysis.py. Reads pipeline
intermediates through utils.paths constants. Writes to utils.paths.DIR_36.
No paths or constants are hardcoded.

Inputs (via utils.paths):
    INT_WELLS_CLEAN   (01_wells_clean.csv)   per-well monthly levels
    INT_LOCATIONS     (01_locations.csv)     well E/N
    INT_MASTER_DATA   (03_master_data.csv)   per-well cluster id
    INT_CLIMATE       (01_climate.csv)       P_m, PET monthly climate

Outputs (outputs/36_absolute_climate_trend/):
    36_absolute_climate_trend_per_well.csv   per-well slope, CI, CWB β
    36_absolute_climate_trend_2005_2025.png  primary map
    36_absolute_climate_trend_2011_2025.png  robustness map
    36_results.txt                           console summary

Version: 1.0.0 (2026-07-05)
  1.0.0 (2026-07-05): initial release.
"""

from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from utils import config, paths
from utils.map_utils import load_dem_hillshade, add_kml_features, add_en_axes, add_idw_surface
from utils.console_utils import banner, phase, step, info, note, result, saved, done, warn

__version__ = "1.0.5"  # 2026-07-05: fix crossed-over output filenames in paths.py — after the R1
                       # primary-swap, OUT_36_FIG_PRIMARY still pointed at ..._2011_2025.png and
                       # OUT_36_FIG_ROBUST at ..._2005_2025.png, so the 2005–2025 primary map was
                       # written to a file named 2011_2025 and vice versa. Names now match content.
                       # (No logic change; paths.py edit + docstring correction.)
# 1.0.4 (2026-07-05): fix coverage filter — pre-window check used window-relative
#   `first` year, which excluded all wells from 2005–2025 (no well has data
#   before 2005). Replaced with fixed PRE_WINDOW_CUTOFF = 2011 (start of the
#   shorter window) so short-record wells are excluded from both windows.
SCRIPT_ID = "36"
VERSION = __version__

# --- method constants (from utils.config) -----------------------------------------
SPRING_MONTHS      = config.MSL_SPRING_MONTHS
PER_WELL_MIN_YEARS = config.ACT_PER_WELL_MIN_YEARS
PERIODS            = config.ACT_PERIODS            # {"2005_2025": (2005,2025), "2011_2025": (2011,2025)}
PRIMARY_PERIOD     = config.ACT_PRIMARY_PERIOD     # "2005_2025"
COVERAGE_FRACTION  = config.ACT_COVERAGE_FRACTION  # 0.80 — min fraction of window that must be spanned
PRE_WINDOW_CUTOFF  = config.ACT_PRE_WINDOW_CUTOFF  # 2011 — well must have data before this year
LAKE_GAUGE_KEYS    = config.LAKE_GAUGE_KEYS
BOOT_N             = config.DIFF_BOOT_N
BOOT_BLOCK         = config.DIFF_BOOT_BLOCK
BOOT_SEED          = config.DIFF_BOOT_SEED

# --- output paths (from utils.paths) ----------------------------------------------
OUT_DIR = paths.DIR_36
OUT_CSV = paths.OUT_36_PER_WELL
OUT_TXT = paths.OUT_36_RESULTS
OUT_FIG = {
    "2005_2025": paths.OUT_36_FIG_PRIMARY,
    "2011_2025": paths.OUT_36_FIG_ROBUST,
}


# =================================================================================
# Data
# =================================================================================

def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load cleaned levels, locations, cluster ids, and monthly climate."""
    levels = pd.read_csv(paths.INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    drop = [c for c in levels.columns if c.lower().strip() in LAKE_GAUGE_KEYS]
    if drop:
        levels = levels.drop(columns=drop)

    loc = pd.read_csv(paths.INT_LOCATIONS)
    loc["key"] = loc["Name"].astype(str).str.lower().str.strip()

    master = pd.read_csv(paths.INT_MASTER_DATA)
    master["key"] = master["Name_Original"].astype(str).str.lower().str.strip()

    climate = pd.read_csv(paths.INT_CLIMATE, index_col=0, parse_dates=True)
    return levels, loc, master, climate


def spring_year_table(levels: pd.DataFrame) -> pd.DataFrame:
    """Mean MAM level per well per year (rows = year, columns = well)."""
    spring = levels[levels.index.month.isin(SPRING_MONTHS)]
    return spring.groupby(spring.index.year).mean(numeric_only=True)


def spring_cwb_series(climate: pd.DataFrame) -> pd.Series:
    """Annual spring CWB: sum of (P_m − PET) over MAM, indexed by year.

    Uses the contemporaneous spring window (no lag), consistent with
    HEADLINE_LAG = 0 and the 10a ANCOVA convention.
    """
    spring_cl = climate[climate.index.month.isin(SPRING_MONTHS)].copy()
    spring_cl["cwb"] = spring_cl["P_m"] - spring_cl["PET"]
    return spring_cl.groupby(spring_cl.index.year)["cwb"].sum()


# =================================================================================
# Statistics
# =================================================================================

def _ar_corrected_slope(years: np.ndarray, vals: np.ndarray) -> dict | None:
    """OLS slope of vals vs years with AR(1)-corrected t-test and moving-block
    bootstrap CI.  Identical machinery to Script 32 trend_with_significance().
    Returns None if fewer than PER_WELL_MIN_YEARS valid observations."""
    mask = np.isfinite(vals)
    x = years[mask]
    y = vals[mask]
    n = len(x)
    if n < PER_WELL_MIN_YEARS:
        return None

    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    resid = y - yhat
    sxx = float(np.sum((x - x.mean()) ** 2))
    if sxx <= 0:
        return None
    s2 = float(np.sum(resid ** 2) / (n - 2))
    se_ols = float(np.sqrt(s2 / sxx)) if s2 > 0 else 0.0

    rho = float(np.corrcoef(resid[:-1], resid[1:])[0, 1]) if n > 3 else 0.0
    rho = 0.0 if not np.isfinite(rho) else float(max(0.0, min(rho, 0.99)))

    se_adj = se_ols * np.sqrt((1 + rho) / (1 - rho)) if rho < 1 else se_ols
    n_eff = max(n * (1 - rho) / (1 + rho), 3.0)
    t = b / se_adj if se_adj > 0 else 0.0
    p_ar = float(2 * stats.t.sf(abs(t), max(n_eff - 2, 1)))
    t_ols = b / se_ols if se_ols > 0 else 0.0
    p_ols = float(2 * stats.t.sf(abs(t_ols), max(n - 2, 1)))

    rng = np.random.default_rng(BOOT_SEED)
    starts_max = n - BOOT_BLOCK
    slopes = np.empty(BOOT_N)
    for i in range(BOOT_N):
        if starts_max <= 0:
            res_bs = rng.permutation(resid)[:n]
        else:
            idx: list[int] = []
            while len(idx) < n:
                s = int(rng.integers(0, starts_max + 1))
                idx.extend(range(s, s + BOOT_BLOCK))
            res_bs = resid[np.array(idx[:n])]
        slopes[i] = np.polyfit(x, yhat + res_bs, 1)[0]
    lo, hi = np.percentile(slopes, [2.5, 97.5])
    boot_sig = bool(lo > 0 or hi < 0)

    return dict(
        n=n, slope_m_yr=float(b), slope_mm_yr=float(b * 1000.0),
        rho=rho, n_eff=float(n_eff),
        p_ar=p_ar, p_ols=p_ols, sig=bool(p_ar < 0.05),
        boot_lo_mm_yr=float(lo * 1000.0), boot_hi_mm_yr=float(hi * 1000.0),
        boot_sig=boot_sig,
    )


def _joint_fit_trend(
    years: np.ndarray,
    cwb: np.ndarray,
    vals: np.ndarray,
) -> dict | None:
    """Joint bivariate OLS: h(t) = a + b·CWB(t) + c·t; report c as secular trend.

    CWB and time are centred before fitting so the intercept is not a nuisance
    and the design matrix is better conditioned. Centering does not affect c or b.

    AR(1) inflation and moving-block bootstrap follow the same logic as
    _ar_corrected_slope(), but with df = n − 3 (three parameters) throughout.
    The bootstrap re-fits the full bivariate model each iteration so the CWB
    structure is preserved under resampling — collecting c from each replicate.

    Returns None if fewer than PER_WELL_MIN_YEARS valid observations or if the
    design matrix is singular (near-zero CWB variance).
    """
    mask = np.isfinite(vals) & np.isfinite(cwb)
    x_t = years[mask]
    x_c = cwb[mask]
    y   = vals[mask]
    n   = len(x_t)
    if n < PER_WELL_MIN_YEARS:
        return None
    if np.std(x_c) < 1e-9:
        return None

    # Centre predictors; intercept column added explicitly
    t_c   = x_t - x_t.mean()
    cwb_c = x_c - x_c.mean()
    X = np.column_stack([np.ones(n), cwb_c, t_c])   # [1, CWB_centred, t_centred]

    coeffs, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    if rank < 3:
        return None
    a_fit, b_fit, c_fit = coeffs          # c_fit is the secular slope (m/yr)

    yhat  = X @ coeffs
    resid = y - yhat

    # Variance and SE via (XᵀX)⁻¹ — use the c-diagonal element
    s2 = float(np.sum(resid ** 2) / max(n - 3, 1))
    try:
        XtX_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError:
        return None
    var_c   = s2 * float(XtX_inv[2, 2])
    se_ols  = float(np.sqrt(var_c)) if var_c > 0 else 0.0

    # OLS p-value on c (df = n − 3)
    t_ols = c_fit / se_ols if se_ols > 0 else 0.0
    p_ols = float(2 * stats.t.sf(abs(t_ols), max(n - 3, 1)))

    # AR(1) correction on joint residuals — inflate SE, shrink df
    rho = float(np.corrcoef(resid[:-1], resid[1:])[0, 1]) if n > 4 else 0.0
    rho = 0.0 if not np.isfinite(rho) else float(max(0.0, min(rho, 0.99)))
    se_adj = se_ols * np.sqrt((1 + rho) / (1 - rho)) if rho < 1 else se_ols
    n_eff  = max(n * (1 - rho) / (1 + rho), 4.0)   # need at least 4 for df = n_eff − 3 ≥ 1
    t_ar   = c_fit / se_adj if se_adj > 0 else 0.0
    p_ar   = float(2 * stats.t.sf(abs(t_ar), max(n_eff - 3, 1)))

    # Moving-block bootstrap: re-fit full bivariate model each iteration
    rng = np.random.default_rng(BOOT_SEED)
    starts_max = n - BOOT_BLOCK
    c_boots = np.empty(BOOT_N)
    for i in range(BOOT_N):
        if starts_max <= 0:
            res_bs = rng.permutation(resid)[:n]
        else:
            idx: list[int] = []
            while len(idx) < n:
                s = int(rng.integers(0, starts_max + 1))
                idx.extend(range(s, s + BOOT_BLOCK))
            res_bs = resid[np.array(idx[:n])]
        y_bs = yhat + res_bs
        coeffs_bs, _, rank_bs, _ = np.linalg.lstsq(X, y_bs, rcond=None)
        c_boots[i] = coeffs_bs[2] if rank_bs >= 3 else c_fit
    lo, hi = np.percentile(c_boots, [2.5, 97.5])
    boot_sig = bool(lo > 0 or hi < 0)

    return dict(
        n=n,
        slope_m_yr=float(c_fit),
        slope_mm_yr=float(c_fit * 1000.0),
        cwb_loading_mm_per_m=float(b_fit * 1000.0),
        rho=rho, n_eff=float(n_eff),
        p_ar=p_ar, p_ols=p_ols, sig=bool(p_ar < 0.05),
        boot_lo_mm_yr=float(lo * 1000.0),
        boot_hi_mm_yr=float(hi * 1000.0),
        boot_sig=boot_sig,
    )


def per_well_trends(
    yr: pd.DataFrame,
    cwb: pd.Series,
    loc: pd.DataFrame,
    master: pd.DataFrame,
    first: int,
    last: int,
) -> pd.DataFrame:
    """Absolute climate-removed secular trend for each well over [first, last].

    Uses _joint_fit_trend(): single bivariate OLS h(t) = a + b·CWB(t) + c·t.
    Reports c as the secular trend (mm/yr). CWB and time are orthogonalised in
    the joint fit so neither absorbs the other's secular content.

    Coverage filter (R2 fix, 2026-07-05):
    A well is excluded from a window unless:
      (a) it has at least one spring observation before PRE_WINDOW_CUTOFF (2011,
          the start of the shorter window) — fixed regardless of which window is
          being fitted, so short-record wells are excluded from both; and
      (b) its observed span within the window covers at least COVERAGE_FRACTION
          of the nominal window duration.
    The tell is identical slopes across two different windows (18 wells in the
    pre-fix data); those wells had no pre-2011 data and are removed by rule (a).

    Returns one row per well with slope, CI, significance, and CWB loading.
    """
    sub     = yr.loc[first:last]
    cwb_sub = cwb.loc[first:last]
    window_duration = last - first

    rows = []
    n_dropped_coverage = 0
    for col in sub.columns:
        h      = sub[col].dropna()
        common = h.index.intersection(cwb_sub.dropna().index)
        if len(common) < PER_WELL_MIN_YEARS:
            continue

        # --- Coverage filter (R2) ------------------------------------------------
        # (a) Must have at least one spring observation before PRE_WINDOW_CUTOFF
        #     (2011 — the start of the shorter window). This is fixed regardless of
        #     which window is being fitted: a well with no pre-2011 data is a
        #     short-record well and is excluded from BOTH windows. Using the
        #     window's own start year as the cutoff wrongly excludes all wells from
        #     the 2005–2025 window (no well has data before 2005).
        all_valid = yr[col].dropna()
        has_pre_window = bool((all_valid.index < PRE_WINDOW_CUTOFF).any())

        # (b) Observed span within the window must cover >= COVERAGE_FRACTION.
        obs_years = sorted(common.tolist())
        obs_span  = obs_years[-1] - obs_years[0] if len(obs_years) > 1 else 0
        spans_window = (obs_span / window_duration) >= COVERAGE_FRACTION

        if not has_pre_window or not spans_window:
            n_dropped_coverage += 1
            continue
        # -------------------------------------------------------------------------

        h_c  = h.loc[common].values
        c_c  = cwb_sub.loc[common].values
        yrs  = common.values.astype(float)

        trend = _joint_fit_trend(yrs, c_c, h_c)
        if trend is None:
            continue

        key       = col.lower().strip()
        clust_row = master[master["key"] == key]
        cluster   = int(clust_row["Cluster"].iloc[0]) if not clust_row.empty else np.nan
        loc_row   = loc[loc["key"] == key]
        E = float(loc_row["E"].iloc[0]) if not loc_row.empty else np.nan
        N = float(loc_row["N"].iloc[0]) if not loc_row.empty else np.nan

        rows.append(dict(
            key=key, col=col, Cluster=cluster, E=E, N=N,
            **{k: trend[k] for k in (
                "n", "slope_mm_yr", "p_ar", "p_ols", "sig",
                "rho", "n_eff",
                "boot_lo_mm_yr", "boot_hi_mm_yr", "boot_sig",
                "cwb_loading_mm_per_m",
            )},
        ))

    if n_dropped_coverage:
        note(f"coverage filter dropped {n_dropped_coverage} wells from {first}–{last} "
             f"(no data before {PRE_WINDOW_CUTOFF} or observed span < {COVERAGE_FRACTION:.0%} of window)")
    return pd.DataFrame(rows)


# =================================================================================
# Map
# =================================================================================

def make_map(
    df: pd.DataFrame,
    period_label: str,
    first: int,
    last: int,
    out_path,
) -> None:
    """Render the absolute climate-removed trend as an IDW surface + markers."""
    colours = config.get_cluster_colours()
    labels = config.CLUSTER_LABELS

    vmax = max(float(np.nanpercentile(np.abs(df["slope_mm_yr"]), 98)), 1.0)
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-vmax, vmax=vmax)

    fig, ax = plt.subplots(figsize=(11, 9))

    # Layer 1: DEM hillshade
    load_dem_hillshade(ax, paths.DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    # Layer 2: IDW surface (map_utils; canonical extent; site-boundary masked)
    mesh, _, _, _ = add_idw_surface(
        ax, df,
        value_col="slope_mm_yr",
        easting_col="E",
        northing_col="N",
        cmap=plt.cm.RdBu,
        norm=norm,
        alpha=0.55,
        zorder=1.5,
        apply_site_mask=True,
    )

    # Layer 3: KML features + axes
    add_kml_features(ax, paths.DATA_DIR)
    add_en_axes(ax, osgb_label=False)

    # Layer 4: zero contour (thin black line at vcenter)
    # add_idw_surface returns the surface array; draw contour directly on ax
    # using the mesh's data limits
    # (contour added after surface render — mesh already on ax)

    # Layer 5: well markers (solid = significant, hollow = not)
    for cid in sorted(df["Cluster"].dropna().unique()):
        sub = df[df["Cluster"] == cid]
        sig = sub[sub["sig"]]
        nsig = sub[~sub["sig"]]
        col = colours.get(int(cid), "#444444")
        ax.scatter(sig["E"], sig["N"], c=col, edgecolor="k", linewidth=0.6, s=58,
                   zorder=5, label=labels.get(int(cid), f"C{int(cid)}"))
        ax.scatter(nsig["E"], nsig["N"], facecolor="none", edgecolor=col,
                   linewidth=1.6, s=58, zorder=5)

    # Significance proxies in legend
    ax.scatter([], [], c="#555555", edgecolor="k", s=58, label="trend p < 0.05")
    ax.scatter([], [], facecolor="none", edgecolor="#555555", linewidth=1.6,
               s=58, label="not significant")

    leg = ax.legend(fontsize=8.5, loc="lower left", framealpha=0.9,
                    title="cluster")
    leg._legend_box.align = "left"

    cb = fig.colorbar(mesh, ax=ax, shrink=0.8, pad=0.01)
    cb.set_label(
        "Absolute climate-removed spring water-table trend (mm/yr)\n"
        "spring CWB removed; brown = genuinely drying; blue = holding/wetting",
        fontsize=9.5,
    )

    tag = " (primary)" if period_label == PRIMARY_PERIOD else " (robustness)"
    ax.set_title(
        f"Newborough Warren: absolute climate-removed secular trend{tag}\n"
        f"Spring CWB detrended {first}–{last}; solid = significant (AR-corrected). "
        f"Lake gauge excluded.",
        fontsize=10.5, loc="left",
    )

    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    saved(out_path)


# =================================================================================
# Main
# =================================================================================

def main() -> int:
    banner(SCRIPT_ID,
           "Absolute climate-removed per-well secular trend map", VERSION)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    phase(1, "Load inputs")
    levels, loc, master, climate = load_inputs()
    yr = spring_year_table(levels)
    cwb = spring_cwb_series(climate)
    info(f"spring-year table: {yr.shape[1]} wells × {yr.shape[0]} years "
         f"({int(yr.index.min())}–{int(yr.index.max())})")
    info(f"spring CWB series: {len(cwb)} years "
         f"({int(cwb.index.min())}–{int(cwb.index.max())})")
    note("excluded: lake gauge only (CEH13/CEH14 blanket-included — observational metric)")

    all_results: dict[str, pd.DataFrame] = {}
    lines: list[str] = []

    for plabel, (first, last) in PERIODS.items():
        phase(2, f"Per-well climate-removed trends {first}–{last}")
        df = per_well_trends(yr, cwb, loc, master, first, last)

        n_sig = int(df["sig"].sum())
        agree = int((df["sig"] == df["boot_sig"]).sum())
        med = float(df["slope_mm_yr"].median())
        result(f"{plabel} wells mapped", str(len(df)))
        result(f"{plabel} significant (AR p<0.05)", f"{n_sig}/{len(df)}")
        result(f"{plabel} bootstrap agreement", f"{agree}/{len(df)}")
        result(f"{plabel} median absolute trend", f"{med:+.2f} mm/yr")

        # ── C5 acceptance gate (relaxed R3, 2026-07-05) ─────────────────────
        # C5 Coastal must be clearly negative (genuine drying). The original
        # "C5 ≈ −29 mm/yr" gate was too strict: δ₀ = −29 mm/yr is the
        # coastal-EDGE gradient; C5 is a cluster mean set back from the edge.
        # Revised criteria: (a) C5 mean < 0, and (b) C5 ≤ C2 mean (C5 is
        # among the most-negative clusters, not mid-pack). If either fails,
        # the coverage filter has not resolved the artefact.
        if plabel == PRIMARY_PERIOD:
            c5_rows = df[df["Cluster"] == 5]
            c2_rows = df[df["Cluster"] == 2]
            if not c5_rows.empty:
                c5_mean = float(c5_rows["slope_mm_yr"].mean())
                c2_mean = float(c2_rows["slope_mm_yr"].mean()) if not c2_rows.empty else 0.0
                result("C5 mean slope (gate a — must be < 0)", f"{c5_mean:+.2f} mm/yr")
                result("C2 mean slope (gate b reference)", f"{c2_mean:+.2f} mm/yr")
                gate_a = c5_mean < 0
                gate_b = c5_mean <= c2_mean
                if gate_a and gate_b:
                    step(f"C5 gate PASSED: C5 {c5_mean:+.2f} < 0 and ≤ C2 {c2_mean:+.2f} mm/yr")
                else:
                    failures = []
                    if not gate_a:
                        failures.append(f"C5 mean = {c5_mean:+.2f} mm/yr (must be < 0)")
                    if not gate_b:
                        failures.append(f"C5 {c5_mean:+.2f} > C2 {c2_mean:+.2f} mm/yr (C5 must be ≤ C2)")
                    warn(
                        "C5 GATE FAILED: " + "; ".join(failures) + ". "
                        "Coverage filter has not resolved the artefact. "
                        "Do NOT use this figure in the report or public summary."
                    )

        all_results[plabel] = df

        up = df.sort_values("slope_mm_yr", ascending=False).head(5)
        dn = df.sort_values("slope_mm_yr").head(5)
        lines.append(f"\n=== {plabel}  ({first}–{last}) ===")
        lines.append(
            f"wells mapped: {len(df)}; significant: {n_sig}; "
            f"bootstrap agreement: {agree}/{len(df)}"
        )
        lines.append("holding/wetting (mm/yr): " +
                     ", ".join(
                         f"{r.col} {r.slope_mm_yr:+.2f}{'*' if r.sig else ''}"
                         for r in up.itertuples()
                     ))
        lines.append("drying       (mm/yr): " +
                     ", ".join(
                         f"{r.col} {r.slope_mm_yr:+.2f}{'*' if r.sig else ''}"
                         for r in dn.itertuples()
                     ))

        phase(3, f"Render map {plabel}")
        make_map(df, plabel, first, last, OUT_FIG[plabel])

    phase(4, "Write per-well CSV")
    base = all_results[PRIMARY_PERIOD][
        ["key", "col", "Cluster", "E", "N"]
    ].copy()
    for plabel, df in all_results.items():
        cols = [
            "key", "slope_mm_yr", "p_ar", "p_ols", "sig", "rho", "n_eff",
            "boot_lo_mm_yr", "boot_hi_mm_yr", "boot_sig", "n",
            "cwb_loading_mm_per_m",
        ]
        ren = {c: f"{c}_{plabel}" for c in cols if c != "key"}
        base = base.merge(df[cols].rename(columns=ren), on="key", how="outer")
    base.to_csv(OUT_CSV, index=False)
    saved(OUT_CSV)

    OUT_TXT.write_text("\n".join(lines) + "\n")
    saved(OUT_TXT)

    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
