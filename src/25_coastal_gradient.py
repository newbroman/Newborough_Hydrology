"""
25_coastal_gradient.py — Phase 12 (step 27/28)

Coastal-retreat gradient analysis
=================================

Fits a network-scale, physics-based non-linear regression to per-well
water-table trends against perpendicular distance to the eroding
Caernarfon Bay shoreline. Two functional forms are fitted:

    Linear-with-cutoff (Dupuit–Forchheimer strip aquifer):
        δ(d) = max(δ_0 · (1 − d/L), 0) + c

    Exponential decay (diffusive / transient response):
        δ(d) = δ_0 · exp(−d/L) + c

where δ(d) is the rate of water-table change (mm/yr) at distance d (m)
from the western foreshore, δ_0 is the coast-edge anomaly above climate,
L is the inland reach, and c is the far-field climate background.

The fits are produced at three increasingly stringent specifications to
test the forest-cover confound:

    [1] Full network        — all clusters, clearfell-zone wells dropped
    [2] Forest-free network — C1 + C2 + C3 only (drops C4 + C5 entirely)
    [3] C3 only             — single non-forested cluster, c held to the
                              network value because C3 contains no well
                              at d → 0 and a 3-parameter fit on this
                              restricted distance range is under-identified

The script then applies the headline (forest-free linear-capped) fit to:

    - Each cluster's Script 14 summer-minimum slope, producing a
      gradient/climate/residual partition
    - The BACI ANCOVA (Script 10a) easting × time absorption, producing
      a corroboration check showing whether the BACI's spatial
      covariate is absorbing the gradient signal the model predicts

This is a stand-alone analytic step — it reads pipeline intermediates
and a versioned distance-to-coast CSV (data/well_distance_to_coast.csv)
but does not feed downstream pipeline scripts.

Inputs
------
data/well_distance_to_coast.csv        OS perpendicular distances
outputs/01_wells_clean.csv             Reference network water levels
outputs/01_wells_extended.csv          Extended-network water levels
outputs/01_locations.csv               Well coordinates
outputs/01_climate.csv                 RAF Valley P, PET
outputs/03_master_data.csv             Cluster assignments
outputs/14_climate_projections/14_summer_trend_stats.csv
                                       Cluster-centroid summer-min slopes
outputs/10_clearfell_baci/10a_02_ancova_full_coefficients.csv
                                       BACI ANCOVA coefficients

Outputs
-------
25_01_panel_fit_parameters.csv         All fits (3 specs × 2 forms)
25_02_per_well_summer_min_slopes.csv   Per-well OLS slopes
25_03_cluster_partition.csv            Cluster attribution table
25_04_baci_corroboration.csv           BACI absorption vs model prediction
25_05_fit_diagnostic.jpg               Two-panel figure (a) per-well + fits,
                                       (b) cluster stacked bars
25_06_baci_corroboration_chart.jpg     Forest plot of corroboration
25_report_numbers.csv                  Headline numbers in standard format

Provenance of well_distance_to_coast.csv
----------------------------------------
Computed once out-of-pipeline from OS Open Map Local TidalBoundary
(SH_TidalBoundary.shp), using the full Caernarfon Bay MHW (High Water
Mark) classification — two connected lines forming the 15.0 km eroding
shoreline. Menai Strait and Llanddwyn Island HWM excluded. Perpendicular
distance computed via shapely.geometry.Point.distance(LineString) in
EPSG:27700. See data/COASTLINE_PROVENANCE.md.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import least_squares
from scipy.stats import t as t_dist

# ── Pipeline imports ──────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from utils import paths  # noqa: E402
from utils.config import CLUSTER_COLOURS, CLUSTER_LABELS  # noqa: E402
from utils.clearfell_common import (  # noqa: E402
    IMPACT_WELLS, EDGE_WELLS, FOREST_CONTROL_WELLS,
    COASTAL_CONTROL_WELLS, CLIMATE_CONTROL_WELLS,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


# ── Constants ────────────────────────────────────────────────────────────────
# Wells excluded from the panel regression because they are subject to
# direct intervention effects that would contaminate the gradient signal.
FE_WELLS = ["fe1", "fe2", "fe3", "fe4"]
SCRAPED_WELLS = ["ceh36"]
NON_DIPWELLS = ["llyn rhos"]

# BACI clearfell-zone wells (Impact + Edge + Forest controls + Coastal
# controls) — dropped from the full and forest-free panel fits so that
# the felling-induced water-table rise does not appear as a residual.
# These lists are imported from clearfell_common so any update to the
# BACI design propagates automatically.
CLEARFELL_ZONE = list(set(
    IMPACT_WELLS + EDGE_WELLS + FOREST_CONTROL_WELLS + COASTAL_CONTROL_WELLS
))

# Within the C3-only fit, only WMC3 (BACI Impact) is in C3 AND in the
# clearfell zone — drop it. CEH36 is also in C3 but already in
# SCRAPED_WELLS. All other C3 wells are retained.
CLEARFELL_ZONE_IN_C3 = list(
    (set(CLEARFELL_ZONE) & {"wmc3", "ceh19", "ceh17"}) | {"wmc3"}
)

PANEL_OBS_MIN_YEARS = 8  # per-well summer-min slopes require ≥8 years


# ── Models ────────────────────────────────────────────────────────────────────

def model_exp(d, delta_0, L, c):
    """Exponential decay: δ(d) = δ_0 · exp(−d/L) + c."""
    return delta_0 * np.exp(-d / L) + c


def model_linear_capped(d, delta_0, L, c):
    """Linear-with-cutoff (Dupuit–Forchheimer strip):

        δ(d) = max(δ_0 · (1 − d/L), 0) + c    if δ_0 > 0
        δ(d) = min(δ_0 · (1 − d/L), 0) + c    if δ_0 < 0

    The clamp ensures the gradient does not change sign at d > L; it
    simply asymptotes to the climate background c.
    """
    inner = delta_0 * (1.0 - d / L)
    inner = np.where(delta_0 < 0, np.minimum(inner, 0), np.maximum(inner, 0))
    return inner + c


# ── Data loading ──────────────────────────────────────────────────────────────

def load_panel(distances: pd.DataFrame, exclude_forested: bool = False,
                restrict_cluster: int | None = None) -> pd.DataFrame:
    """Build the long-form monthly panel with all needed covariates.

    Parameters
    ----------
    distances : DataFrame with columns [well, dist_coast_m]
    exclude_forested : if True, drop C4 and C5 wells entirely
        (the forest-free network specification)
    restrict_cluster : if set, restrict to a single cluster only
        (the C3-only specification expects 3)
    """
    wc = pd.read_csv(paths.INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    we = pd.read_csv(paths.INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
    wc.columns = [c.strip().lower() for c in wc.columns]
    we.columns = [c.strip().lower() for c in we.columns]
    common = set(wc.columns) & set(we.columns)
    we_only = we[[c for c in we.columns if c not in common]]
    wells = pd.concat([wc, we_only], axis=1)

    long = wells.reset_index()
    long = long.rename(columns={long.columns[0]: "date"})
    long = long.melt(id_vars="date", var_name="well", value_name="h_depth")
    long = long.dropna(subset=["h_depth"])

    locs = pd.read_csv(paths.INT_LOCATIONS)
    locs["well"] = locs["Name"].str.strip().str.lower()
    locs = locs[["well", "E", "N"]].rename(
        columns={"E": "easting", "N": "northing"})

    master = pd.read_csv(paths.INT_MASTER_DATA)
    master["well"] = master["Name_Original"].str.strip().str.lower()
    master = master[["well", "Cluster"]].rename(columns={"Cluster": "cluster"})

    long = long.merge(locs, on="well", how="left")
    long = long.merge(master, on="well", how="left")
    long = long.merge(distances[["well", "dist_coast_m"]], on="well", how="left")

    # Exclusions
    long = long[~long["well"].isin(NON_DIPWELLS + FE_WELLS + SCRAPED_WELLS)]
    if restrict_cluster is not None:
        long = long[long["cluster"] == restrict_cluster]
        if restrict_cluster == 3:
            long = long[~long["well"].isin(CLEARFELL_ZONE_IN_C3)]
    else:
        long = long[~long["well"].isin(CLEARFELL_ZONE)]
        if exclude_forested:
            long = long[~long["cluster"].isin([4, 5])]
    long = long[long["easting"].notna() & long["dist_coast_m"].notna()].copy()
    return long


def load_cwb() -> pd.Series:
    """Centred cumulative water balance (P − PET anomaly cumsum), mm."""
    cl = pd.read_csv(paths.INT_CLIMATE, index_col=0, parse_dates=True).sort_index()
    cl = cl[(cl.index.year >= 2004) & (cl.index.year <= 2026)]
    P_mm = pd.to_numeric(cl["P_m"], errors="coerce") * 1000
    PET_mm = pd.to_numeric(cl["PET"], errors="coerce") * 1000
    wb = (P_mm - PET_mm).dropna()
    cwb = (wb - wb.mean()).cumsum()
    cwb.name = "cwb"
    return cwb


def build_design(long: pd.DataFrame, cwb: pd.Series) -> pd.DataFrame:
    """Merge CWB and add t_years / month covariates."""
    df = long.merge(cwb.to_frame(), left_on="date", right_index=True, how="inner")
    df = df.dropna(subset=["h_depth", "cwb", "dist_coast_m"]).copy()
    df["t_years"] = (df["date"] - df["date"].min()).dt.days / 365.25
    df["month"] = df["date"].dt.month
    return df


# ── Panel fits ───────────────────────────────────────────────────────────────

def _within_demeaned_design(df: pd.DataFrame):
    """Construct the within-well-demeaned linear part of the design
    (CWB + month FE). Returns (h_dm, cwb_dm, M_dm, df_index).
    """
    grp = df.groupby("well")
    h_dm = (df["h_depth"] - grp["h_depth"].transform("mean")).values
    cwb_dm = (df["cwb"] - grp["cwb"].transform("mean")).values
    month_dums = pd.get_dummies(df["month"], prefix="m", drop_first=True)
    month_cols = []
    for c in month_dums.columns:
        dm = (month_dums[c].astype(float)
              - month_dums[c].astype(float).groupby(df["well"]).transform("mean"))
        month_cols.append(dm.values)
    M_dm = np.column_stack(month_cols)
    return h_dm, cwb_dm, M_dm


def fit_panel(df: pd.DataFrame, decay_func, p0, bounds,
              c_fixed: float | None = None, label: str = "") -> dict:
    """Fit a 3-parameter (or 2-parameter, if c_fixed) decay model to the
    panel by profile non-linear least squares.

    The well + month fixed effects and the CWB slope are absorbed by
    within-well demeaning (Frisch–Waugh–Lovell). The decay covariate
    δ(d_w) · t enters as a constrained term whose coefficient is fixed
    at 1; non-linear search runs over the parameters of δ(d_w).
    """
    h_dm, cwb_dm, M_dm = _within_demeaned_design(df)
    d_w = df["dist_coast_m"].values
    t = df["t_years"].values

    def residuals(theta):
        if c_fixed is None:
            delta_0, L, c = theta
        else:
            delta_0, L = theta
            c = c_fixed
        delta_d = decay_func(d_w, delta_0, L, c)
        decay_t = delta_d * t / 1000.0  # mm/yr → m, since h_depth is in m
        decay_t_ser = pd.Series(decay_t, index=df.index)
        decay_t_dm = (decay_t_ser
                      - decay_t_ser.groupby(df["well"]).transform("mean")).values
        y = h_dm - decay_t_dm
        X = np.column_stack([cwb_dm, M_dm])
        try:
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        except np.linalg.LinAlgError:
            return np.full(len(y), 1e6)
        return y - X @ beta

    result = least_squares(residuals, p0, bounds=bounds,
                            method="trf", max_nfev=5000)
    n = len(result.fun); k = len(result.x)
    rss = float(np.sum(result.fun ** 2))
    sigma2 = rss / max(n - k, 1)
    J = result.jac
    try:
        cov = sigma2 * np.linalg.inv(J.T @ J)
        perr = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        perr = np.full(k, np.nan)
    t_crit = t_dist.ppf(0.975, df=max(n - k, 1))
    ci = np.column_stack([result.x - t_crit * perr,
                            result.x + t_crit * perr])
    return {
        "label": label,
        "popt": result.x,
        "perr": perr,
        "ci": ci,
        "rss": rss,
        "n": n,
        "k": k,
        "aic": n * np.log(rss / n) + 2 * k,
        "c_fixed": c_fixed,
    }


# ── Per-well summer-min slopes ───────────────────────────────────────────────

def compute_per_well_slopes(long: pd.DataFrame) -> pd.DataFrame:
    """Per-well annual summer-minimum slope vs hydrological year."""
    SUMMER = [4, 5, 6, 7, 8, 9]
    df = long.copy()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["hydro_year"] = df["year"] + (df["month"] >= 10).astype(int)
    df = df[df["month"].isin(SUMMER)]
    smin = df.groupby(["well", "hydro_year"]).agg(
        h_min=("h_depth", "min"),
        easting=("easting", "first"),
        northing=("northing", "first"),
        cluster=("cluster", "first"),
        dist_coast_m=("dist_coast_m", "first"),
    ).reset_index()
    smin = smin[(smin["hydro_year"] >= 2004) & (smin["hydro_year"] <= 2025)]

    out = []
    for well, g in smin.groupby("well"):
        if g["hydro_year"].nunique() < PANEL_OBS_MIN_YEARS:
            continue
        x = g["hydro_year"].astype(float).values
        y = g["h_min"].astype(float).values
        try:
            res = sm.OLS(y, sm.add_constant(x)).fit()
            out.append({
                "well": well,
                "easting": g["easting"].iloc[0],
                "northing": g["northing"].iloc[0],
                "cluster": (int(g["cluster"].iloc[0])
                             if pd.notna(g["cluster"].iloc[0]) else None),
                "dist_coast_m": g["dist_coast_m"].iloc[0],
                "slope_m_yr": float(res.params[1]),
                "slope_se": float(res.bse[1]),
                "slope_p": float(res.pvalues[1]),
                "r2": float(res.rsquared),
                "n_years": int(len(g)),
            })
        except Exception:
            continue
    return pd.DataFrame(out)


# ── Cluster partition ────────────────────────────────────────────────────────

def cluster_partition(per_well: pd.DataFrame,
                       fit_headline: dict,
                       script14_slopes: pd.DataFrame) -> pd.DataFrame:
    """Apply the headline (forest-free lin-cap) fit to each cluster's
    Script 14 centroid summer-minimum slope and decompose into
    gradient + climate + residual.

    The 'observed' column uses Script 14's cluster-centroid hydrograph
    slope to remain consistent with §4.8.1's existing quoted numbers.
    Per-well mean slopes are also reported alongside for reference.
    """
    d0, L, c = fit_headline["popt"]
    s14 = {}
    for _, r in script14_slopes.iterrows():
        cnum = int(str(r["Cluster"]).replace("C", ""))
        s14[cnum] = float(r["Slope_m_per_yr"])

    rows = []
    for cn, lbl in CLUSTER_LABELS.items():
        sub = per_well[per_well["cluster"] == cn]
        if sub.empty:
            continue
        mean_d = float(sub["dist_coast_m"].mean())
        per_well_mean = float(sub["slope_m_yr"].mean() * 1000)  # mm/yr
        observed_s14 = s14.get(cn, np.nan) * 1000  # mm/yr
        # Gradient component (no c)
        grad_only = float(model_linear_capped(mean_d, d0, L, 0))
        pred_total = grad_only + c
        residual = observed_s14 - pred_total
        pct = (100.0 * grad_only / observed_s14) if observed_s14 != 0 else np.nan
        rows.append({
            "cluster_id": cn,
            "cluster_label": lbl,
            "n_wells": int(len(sub)),
            "mean_dist_coast_m": round(mean_d, 1),
            "observed_centroid_mm_yr": round(observed_s14, 2),
            "observed_per_well_mean_mm_yr": round(per_well_mean, 2),
            "predicted_gradient_mm_yr": round(grad_only, 2),
            "predicted_climate_mm_yr": round(c, 2),
            "predicted_total_mm_yr": round(pred_total, 2),
            "residual_mm_yr": round(residual, 2),
            "gradient_pct_of_observed": (round(pct, 0)
                                          if not np.isnan(pct) else None),
        })
    return pd.DataFrame(rows)


# ── BACI corroboration ──────────────────────────────────────────────────────

def baci_corroboration(distances: pd.DataFrame,
                        fit_headline: dict,
                        baci_csv_path: Path) -> pd.DataFrame:
    """Compare the BACI easting × time coefficient absorption to the
    gradient model's predicted differential between each impact zone
    and each control tier.

    The BACI fits `delta_easting × months_since` as a covariate; its
    coefficient (m per m-easting per month) implies an absorbed
    differential deepening rate of  coef × ΔE × 12 × 1000 mm/yr.

    The gradient model predicts a differential of
        δ(d_impact) − δ(d_control)
    where δ is the headline linear-capped form.

    If the two agree, the BACI's easting × time correction is
    accounting for coastal-retreat drift consistently with the
    independently-fitted gradient. If the BACI absorbs much more,
    its easting × time term is doing more than just coastal-retreat
    correction (likely absorbing other monotonic spatial drift).
    """
    d0_h, L_h, c_h = fit_headline["popt"]
    dists = distances.set_index("well")["dist_coast_m"].to_dict()

    def mean_d(wells):
        return float(np.mean([dists[w] for w in wells if w in dists]))

    def grad_only(d):
        return float(model_linear_capped(d, d0_h, L_h, 0))

    d_imp = mean_d(IMPACT_WELLS)
    d_edge = mean_d(EDGE_WELLS)
    d_forest = mean_d(FOREST_CONTROL_WELLS)
    d_coastal = mean_d(COASTAL_CONTROL_WELLS)
    d_climate = mean_d(CLIMATE_CONTROL_WELLS)

    # Easting too (BACI uses easting, not distance to coast)
    locs = pd.read_csv(paths.INT_LOCATIONS)
    locs["well"] = locs["Name"].str.strip().str.lower()
    E = dict(zip(locs["well"], locs["E"]))

    def mean_E(wells):
        return float(np.mean([E[w] for w in wells if w in E]))

    E_imp = mean_E(IMPACT_WELLS)
    E_edge = mean_E(EDGE_WELLS)
    E_forest = mean_E(FOREST_CONTROL_WELLS)
    E_climate = mean_E(CLIMATE_CONTROL_WELLS)

    # BACI coefficients
    baci = pd.read_csv(baci_csv_path)
    baci = baci[baci["Coefficient"] == "easting_x_time"].copy()

    rows = []
    pairs = [
        ("Forest", "Impact", d_imp, E_imp, d_forest, E_forest),
        ("Forest", "Edge",   d_edge, E_edge, d_forest, E_forest),
        ("Climate", "Impact", d_imp, E_imp, d_climate, E_climate),
        ("Climate", "Edge",   d_edge, E_edge, d_climate, E_climate),
    ]
    for ctl_name, zone_name, d_tgt, E_tgt, d_ctl, E_ctl in pairs:
        # Gradient-model differential (target − control), gradient only
        grad_tgt = grad_only(d_tgt)
        grad_ctl = grad_only(d_ctl)
        model_pred = grad_tgt - grad_ctl  # mm/yr
        # BACI coefficient
        match = baci[(baci["Control"] == ctl_name) & (baci["Zone"] == zone_name)]
        if match.empty:
            continue
        coef = float(match["Value"].iloc[0])  # m / (m_easting × month)
        coef_se = float(match["SE"].iloc[0])
        coef_p = float(match["p"].iloc[0])
        dE = E_tgt - E_ctl
        # Absorbed differential = coef × ΔE × 12 (months/yr) × 1000 (m → mm)
        baci_absorb = coef * dE * 12 * 1000
        baci_absorb_se = coef_se * abs(dE) * 12 * 1000
        # z-test against model prediction (treating model pred as known)
        z = ((baci_absorb - model_pred) / baci_absorb_se
              if baci_absorb_se > 0 else np.nan)
        rows.append({
            "control_tier": ctl_name,
            "impact_zone": zone_name,
            "d_target_m": round(d_tgt, 0),
            "d_control_m": round(d_ctl, 0),
            "delta_E_m": round(dE, 0),
            "baci_coef": coef,
            "baci_coef_se": coef_se,
            "baci_coef_p": coef_p,
            "baci_absorbs_mm_yr": round(baci_absorb, 1),
            "baci_absorbs_se_mm_yr": round(baci_absorb_se, 1),
            "model_predicts_mm_yr": round(model_pred, 1),
            "z_test_baci_vs_model": (round(z, 2)
                                      if not np.isnan(z) else None),
            "consistent": ("yes" if (not np.isnan(z)) and abs(z) < 2
                            else "no"),
        })
    return pd.DataFrame(rows)


# ── Figures ──────────────────────────────────────────────────────────────────

def plot_fit_diagnostic(per_well: pd.DataFrame,
                          fit_full_l: dict, fit_ff_l: dict, fit_c3_l: dict,
                          cluster_partition_df: pd.DataFrame,
                          fig_path: Path) -> None:
    """Two-panel diagnostic:
        (a) per-well summer-min slope vs distance, with the three lin-cap
            fits (full network, forest-free, C3 only) overlaid
        (b) per-cluster stacked decomposition: observed vs gradient +
            climate + residual
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.0))
    ax1, ax2 = axes

    # ── Panel (a) — per-well scatter and fitted curves ──
    for cn, lbl in CLUSTER_LABELS.items():
        sub = per_well[per_well["cluster"] == cn]
        if sub.empty:
            continue
        ax1.errorbar(sub["dist_coast_m"], sub["slope_m_yr"] * 1000,
                      yerr=sub["slope_se"] * 1000,
                      fmt="o", color=CLUSTER_COLOURS[cn], markersize=6,
                      capsize=2, elinewidth=0.5,
                      markeredgecolor="black", markeredgewidth=0.3,
                      label=lbl, alpha=0.9, zorder=3)
    unc = per_well[per_well["cluster"].isna()]
    if not unc.empty:
        ax1.errorbar(unc["dist_coast_m"], unc["slope_m_yr"] * 1000,
                      yerr=unc["slope_se"] * 1000,
                      fmt="o", color="lightgrey", markersize=4,
                      capsize=2, elinewidth=0.4, alpha=0.6,
                      markeredgecolor="grey", markeredgewidth=0.3,
                      label="Unclustered", zorder=2)

    d_grid = np.linspace(0, 2400, 300)

    # Full network
    y_full = model_linear_capped(d_grid, *fit_full_l["popt"])
    d0, L, c = fit_full_l["popt"]
    ax1.plot(d_grid, y_full, "-", color="#222222", linewidth=2.0,
              label=f"Full network: δ₀={d0:+.1f}, L={L:.0f}, c={c:+.1f}",
              zorder=6)
    # Forest-free
    y_ff = model_linear_capped(d_grid, *fit_ff_l["popt"])
    d0, L, c = fit_ff_l["popt"]
    ax1.plot(d_grid, y_ff, "-", color="#2ca02c", linewidth=2.4,
              label=f"Forest-free: δ₀={d0:+.1f}, L={L:.0f}, c={c:+.1f}",
              zorder=7)
    # C3 only (c fixed)
    y_c3 = model_linear_capped(d_grid, fit_c3_l["popt"][0],
                                  fit_c3_l["popt"][1], fit_c3_l["c_fixed"])
    d0, L = fit_c3_l["popt"]
    ax1.plot(d_grid, y_c3, "--", color="#d62728", linewidth=1.8,
              label=f"C3 only (c fixed): δ₀={d0:+.1f}, L={L:.0f}",
              zorder=5)

    ax1.axhline(0, color="black", linewidth=0.4, alpha=0.6)
    ax1.set_xlabel("Perpendicular distance to Caernarfon Bay MHW (m)")
    ax1.set_ylabel("Summer-minimum slope (mm yr⁻¹)")
    ax1.set_title("(a) Per-well summer-minimum slopes vs distance to coast",
                   fontsize=11, loc="left")
    ax1.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax1.grid(alpha=0.3)

    # ── Panel (b) — cluster decomposition ──
    p = cluster_partition_df.sort_values("mean_dist_coast_m").reset_index(drop=True)
    x = np.arange(len(p))
    obs = p["observed_centroid_mm_yr"].values
    grad = p["predicted_gradient_mm_yr"].values
    cli = p["predicted_climate_mm_yr"].values
    res = p["residual_mm_yr"].values

    width = 0.38
    ax2.bar(x - width / 2, obs, width,
             color="#333333", alpha=0.9, label="Observed (Script 14)",
             edgecolor="black", linewidth=0.5)
    ax2.bar(x + width / 2, cli, width,
             color="#4488cc", alpha=0.85, label="Climate (c)",
             edgecolor="black", linewidth=0.5)
    ax2.bar(x + width / 2, grad, width, bottom=cli,
             color="#cc5500", alpha=0.85, label="Coastal-retreat gradient",
             edgecolor="black", linewidth=0.5)
    ax2.bar(x + width / 2, res, width, bottom=cli + grad,
             color="#bbbbbb", alpha=0.85, label="Residual",
             edgecolor="black", linewidth=0.5)

    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.set_xticks(x)
    short_labels = p["cluster_label"].str.extract(r"^(C\d+)")[0]
    ax2.set_xticklabels(short_labels, fontsize=10)
    ax2.set_xlabel("Cluster (coastal → inland)")
    ax2.set_ylabel("Summer-minimum slope (mm yr⁻¹)")
    ax2.set_title("(b) Per-cluster decomposition under forest-free lin-cap fit",
                   fontsize=11, loc="left")
    ax2.legend(loc="lower right", fontsize=8.5, framealpha=0.9)
    ax2.grid(alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(fig_path, dpi=150, bbox_inches="tight",
                 pil_kwargs={"quality": 85})
    plt.close(fig)


def plot_baci_corroboration(baci_df: pd.DataFrame, fig_path: Path) -> None:
    """Forest plot of BACI easting × time absorption vs gradient-model
    prediction, per impact-zone × control-tier comparison.
    """
    fig, ax = plt.subplots(figsize=(10, 4.5))
    labels = [f"{r.control_tier} {r.impact_zone}"
              for r in baci_df.itertuples()]
    y_pos = np.arange(len(baci_df))[::-1]
    for i, r in enumerate(baci_df.itertuples()):
        # BACI absorbed (with SE)
        ax.errorbar(r.baci_absorbs_mm_yr, y_pos[i],
                     xerr=r.baci_absorbs_se_mm_yr,
                     fmt="o", color="#1f77b4", markersize=8, capsize=4,
                     linewidth=1.5,
                     label="BACI easting × time absorbs"
                     if i == 0 else None)
        # Model predicts (point, no error bar)
        ax.scatter(r.model_predicts_mm_yr, y_pos[i],
                    marker="D", color="#cc5500", s=80, zorder=5,
                    edgecolor="black", linewidth=0.5,
                    label="Gradient model predicts" if i == 0 else None)
        # Verdict
        ax.text(0.99, y_pos[i],
                 f"  z = {r.z_test_baci_vs_model:+.2f}  ({r.consistent})",
                 transform=ax.get_yaxis_transform(),
                 va="center", fontsize=9, family="monospace")

    ax.axvline(0, color="grey", linewidth=0.5, alpha=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Differential deepening rate at target zone "
                   "vs control tier (mm yr⁻¹)")
    ax.set_title("BACI easting × time absorption vs coastal-retreat gradient prediction",
                  fontsize=11, loc="left")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.3, axis="x")

    fig.tight_layout()
    fig.savefig(fig_path, dpi=150, bbox_inches="tight",
                 pil_kwargs={"quality": 85})
    plt.close(fig)


# ── Output assembly ──────────────────────────────────────────────────────────

def build_fit_parameters_table(fits: dict) -> pd.DataFrame:
    """Assemble all six fits into a tidy parameter table."""
    rows = []
    for key, fit in fits.items():
        source, model = key
        d0, L = fit["popt"][0], fit["popt"][1]
        d0_se, L_se = fit["perr"][0], fit["perr"][1]
        ci = fit["ci"]
        if fit["c_fixed"] is None:
            c_val = float(fit["popt"][2])
            c_se = float(fit["perr"][2])
        else:
            c_val = float(fit["c_fixed"])
            c_se = np.nan
        rows.append({
            "source": source,
            "model": model,
            "n_obs": fit["n"],
            "AIC": round(fit["aic"], 1),
            "delta_0_mm_yr": round(float(d0), 2),
            "delta_0_se": round(float(d0_se), 2),
            "delta_0_ci_lo": round(float(ci[0, 0]), 2),
            "delta_0_ci_hi": round(float(ci[0, 1]), 2),
            "L_m": round(float(L), 0),
            "L_se": round(float(L_se), 0),
            "L_ci_lo": round(float(ci[1, 0]), 0),
            "L_ci_hi": round(float(ci[1, 1]), 0),
            "c_mm_yr": round(c_val, 2),
            "c_se": (round(c_se, 2) if not np.isnan(c_se) else None),
        })
    return pd.DataFrame(rows)


def build_report_numbers(fits: dict,
                          partition: pd.DataFrame,
                          baci_corr: pd.DataFrame) -> pd.DataFrame:
    """Headline numbers in the project-standard
    `Parameter, Well, Era, Value, Unit, Note` format.
    """
    rows = []
    # Headline fit (forest-free linear-capped)
    ff = fits[("forest_free", "linear_capped")]
    rows.append({"Parameter": "Headline_fit_delta_0",
                  "Well": "", "Era": "2005-2026",
                  "Value": round(float(ff["popt"][0]), 2),
                  "Unit": "mm/yr",
                  "Note": (f"Forest-free linear-capped, "
                            f"SE={ff['perr'][0]:.2f}, "
                            f"95% CI [{ff['ci'][0, 0]:.1f}, "
                            f"{ff['ci'][0, 1]:.1f}]")})
    rows.append({"Parameter": "Headline_fit_L",
                  "Well": "", "Era": "2005-2026",
                  "Value": round(float(ff["popt"][1]), 0),
                  "Unit": "m",
                  "Note": (f"Forest-free linear-capped, "
                            f"SE={ff['perr'][1]:.0f}")})
    rows.append({"Parameter": "Headline_fit_c",
                  "Well": "", "Era": "2005-2026",
                  "Value": round(float(ff["popt"][2]), 2),
                  "Unit": "mm/yr",
                  "Note": (f"Forest-free linear-capped climate background, "
                            f"SE={ff['perr'][2]:.2f}")})
    # AIC comparison
    fe = fits[("forest_free", "exponential")]
    rows.append({"Parameter": "Headline_DeltaAIC_lincap_vs_exp",
                  "Well": "", "Era": "2005-2026",
                  "Value": round(fe["aic"] - ff["aic"], 1),
                  "Unit": "",
                  "Note": "exp − lin-cap; positive favours lin-cap"})
    # C5 attribution
    c5 = partition[partition["cluster_id"] == 5]
    if not c5.empty:
        r = c5.iloc[0]
        rows.append({"Parameter": "C5_gradient_pct_of_observed",
                      "Well": "", "Era": "2005-2026",
                      "Value": float(r["gradient_pct_of_observed"]),
                      "Unit": "%",
                      "Note": (f"Script 14 centroid slope "
                                f"{r['observed_centroid_mm_yr']:+.1f} mm/yr; "
                                f"gradient {r['predicted_gradient_mm_yr']:+.1f}, "
                                f"residual {r['residual_mm_yr']:+.1f}")})
    # BACI corroboration headline (Forest Impact)
    fi = baci_corr[(baci_corr["control_tier"] == "Forest")
                   & (baci_corr["impact_zone"] == "Impact")]
    if not fi.empty:
        r = fi.iloc[0]
        rows.append({"Parameter": "BACI_corroboration_Forest_Impact_z",
                      "Well": "", "Era": "BACI window",
                      "Value": float(r["z_test_baci_vs_model"]),
                      "Unit": "z",
                      "Note": (f"BACI absorbs {r['baci_absorbs_mm_yr']:+.1f} "
                                f"mm/yr, model predicts "
                                f"{r['model_predicts_mm_yr']:+.1f} mm/yr; "
                                f"consistent={r['consistent']}")})
    return pd.DataFrame(rows)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    paths.make_all_dirs()
    paths.DIR_25.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 72)
    print(" Script 25 — Coastal-retreat gradient analysis (Phase 12)")
    print("=" * 72)

    # ── Load distance CSV ──
    if not paths.DATA_DIST_COAST.exists():
        raise FileNotFoundError(
            f"Distance-to-coast CSV not found: {paths.DATA_DIST_COAST}\n"
            "See data/COASTLINE_PROVENANCE.md for how to regenerate from "
            "OS Open Map Local TidalBoundary.")
    distances = pd.read_csv(paths.DATA_DIST_COAST)
    distances["well"] = distances["well"].str.strip().str.lower()
    print(f"\n  Distance source: {paths.DATA_DIST_COAST.name}  "
          f"({len(distances)} wells, "
          f"d range {distances['dist_coast_m'].min():.0f}–"
          f"{distances['dist_coast_m'].max():.0f} m)")

    cwb = load_cwb()

    # ── Fits ──
    print("\n  Fitting [1/3] Full network ...")
    long_full = load_panel(distances, exclude_forested=False)
    df_full = build_design(long_full, cwb)
    fit_full_l = fit_panel(df_full, model_linear_capped,
                            p0=[-30.0, 1000.0, -5.0],
                            bounds=([-200, 100, -30], [50, 10000, 30]),
                            label="full_lincap")
    fit_full_e = fit_panel(df_full, model_exp,
                            p0=[-40.0, 600.0, -5.0],
                            bounds=([-200, 50, -30], [50, 5000, 30]),
                            label="full_exp")

    print("  Fitting [2/3] Forest-free network ...")
    long_ff = load_panel(distances, exclude_forested=True)
    df_ff = build_design(long_ff, cwb)
    fit_ff_l = fit_panel(df_ff, model_linear_capped,
                          p0=[-30.0, 1000.0, -5.0],
                          bounds=([-200, 100, -30], [50, 10000, 30]),
                          label="ff_lincap")
    fit_ff_e = fit_panel(df_ff, model_exp,
                          p0=[-40.0, 600.0, -5.0],
                          bounds=([-200, 50, -30], [50, 5000, 30]),
                          label="ff_exp")

    print("  Fitting [3/3] C3 only (c fixed to forest-free network) ...")
    long_c3 = load_panel(distances, restrict_cluster=3)
    df_c3 = build_design(long_c3, cwb)
    c_fix_l = float(fit_ff_l["popt"][2])
    c_fix_e = float(fit_ff_e["popt"][2])
    fit_c3_l = fit_panel(df_c3, model_linear_capped,
                          p0=[-30.0, 1000.0],
                          bounds=([-200, 100], [50, 10000]),
                          c_fixed=c_fix_l, label="c3_lincap_cfix")
    fit_c3_e = fit_panel(df_c3, model_exp,
                          p0=[-40.0, 600.0],
                          bounds=([-200, 50], [50, 5000]),
                          c_fixed=c_fix_e, label="c3_exp_cfix")

    # ── Print summary to console ──
    print("\n  Fitted parameters (linear-capped form):")
    print(f"    {'Source':<14} {'δ₀ (mm/yr)':>14} {'L (m)':>10} {'c (mm/yr)':>14}")
    for name, fit in [("Full",         fit_full_l),
                       ("Forest-free",  fit_ff_l),
                       ("C3 only",      fit_c3_l)]:
        d0 = fit["popt"][0]; L = fit["popt"][1]
        c = (fit["c_fixed"] if fit["c_fixed"] is not None
              else fit["popt"][2])
        print(f"    {name:<14} {d0:>+7.2f} ± {fit['perr'][0]:.2f}"
              f"   {L:>4.0f} ± {fit['perr'][1]:.0f}"
              f"   {c:>+7.2f}")

    delta_aic = fit_ff_e["aic"] - fit_ff_l["aic"]
    print(f"\n  ΔAIC (forest-free, exp − lin-cap) = {delta_aic:+.1f}  "
          f"({'lin-cap preferred' if delta_aic > 0 else 'exp preferred'})")

    # ── Per-well slopes ──
    print("\n  Computing per-well summer-min slopes ...")
    per_well = compute_per_well_slopes(long_full)
    per_well.to_csv(paths.OUT_25_PER_WELL_SLOPES, index=False)
    print(f"    [OK] {len(per_well)} wells with ≥{PANEL_OBS_MIN_YEARS} years")

    # ── Cluster partition ──
    print("\n  Computing per-cluster attribution ...")
    s14 = pd.read_csv(paths.OUT_14_SUMMER_TREND_CSV)
    # Use FORST-FREE LINCAP as headline
    partition = cluster_partition(per_well, fit_ff_l, s14)
    partition.to_csv(paths.OUT_25_CLUSTER_PARTITION, index=False)
    print(partition[["cluster_label", "mean_dist_coast_m",
                       "observed_centroid_mm_yr",
                       "predicted_gradient_mm_yr",
                       "predicted_climate_mm_yr",
                       "residual_mm_yr",
                       "gradient_pct_of_observed"]].to_string(index=False))

    # ── BACI corroboration ──
    print("\n  Running BACI corroboration check ...")
    baci_corr = baci_corroboration(distances, fit_ff_l,
                                     paths.OUT_10A_FULL_COEFFS)
    baci_corr.to_csv(paths.OUT_25_BACI_CORROBORATION, index=False)
    print(baci_corr[["control_tier", "impact_zone",
                       "baci_absorbs_mm_yr", "model_predicts_mm_yr",
                       "z_test_baci_vs_model", "consistent"]].to_string(index=False))

    # ── Parameters table ──
    fits = {
        ("full", "linear_capped"):         fit_full_l,
        ("full", "exponential"):           fit_full_e,
        ("forest_free", "linear_capped"):  fit_ff_l,
        ("forest_free", "exponential"):    fit_ff_e,
        ("c3_only", "linear_capped_cfix"): fit_c3_l,
        ("c3_only", "exponential_cfix"):   fit_c3_e,
    }
    params = build_fit_parameters_table(fits)
    params.to_csv(paths.OUT_25_FIT_PARAMETERS, index=False)

    # ── Figures ──
    print("\n  Building diagnostic figures ...")
    plot_fit_diagnostic(per_well, fit_full_l, fit_ff_l, fit_c3_l,
                         partition, paths.OUT_25_FIT_DIAGNOSTIC)
    plot_baci_corroboration(baci_corr, paths.OUT_25_BACI_CHART)

    # ── Report numbers ──
    report = build_report_numbers(fits, partition, baci_corr)
    report.to_csv(paths.OUT_25_REPORT_NUMBERS, index=False)

    print(f"\n  Outputs written to: {paths.DIR_25}/")
    print(f"    25_01_panel_fit_parameters.csv")
    print(f"    25_02_per_well_summer_min_slopes.csv")
    print(f"    25_03_cluster_partition.csv")
    print(f"    25_04_baci_corroboration.csv")
    print(f"    25_05_fit_diagnostic.jpg")
    print(f"    25_06_baci_corroboration_chart.jpg")
    print(f"    25_report_numbers.csv")
    print("\n  [OK] Script 25 complete.\n")


if __name__ == "__main__":
    main()
