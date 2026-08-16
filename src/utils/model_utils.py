"""
utils/model_utils.py
====================
Shared model functions for the Newborough Warren SSM pipeline.

This module is the single source of truth for the state-space model
specification. All scripts that fit OLS regressions, run forward
simulations, or compute P_flood thresholds should call functions from
here rather than maintaining local copies.

SSM equation (displacement formulation):

    Δh(t) = β₁·P(t−lag) − β₂·PET(t) − β₃·(D + h(t−1))

    where D = DRAINAGE_DATUM (config.py; metres below ground surface)
          h is in negative-below-ground convention

Design matrix (no-intercept OLS):

    y  = Δh
    X  = [P_lag,  −PET,  −h_disp_prev]
          β₁      β₂     β₃

    All three coefficients are expected positive for physically
    consistent behaviour (β₁, β₂ hard-asserted; β₃ soft-asserted).

Functions
---------
build_ssm_frame    — align well + climate data, compute SSM predictors
fit_ssm            — no-intercept OLS (Model A / headline SSM)
fit_ssm_intercept  — with-intercept OLS (Model B)
simulate_ssm       — iterative forward simulation
pflood_lambda      — P_flood closed-form threshold (iterated)
monthly_perturbation — single-step monthly forcing response
get_metrics        — NSE, RMSE, bias between two series
get_r2             — R² from Pearson correlation
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.config import (
    DRAINAGE_DATUM, HEADLINE_LAG, SSM_MIN_OBS,
    LCSC_DATA_LIMIT as _LCSC_DATA_LIMIT,
)


__version__ = "1.5.0"  # Hollingham (2026) — 2026-08-16. LCSC_DATA_LIMIT is now
#   imported from config.py rather than declared here; the name survives as a
#   re-export so existing importers resolve unchanged (D-016). Value unchanged.
#   Also clears three attributions left stale by v1.4.0: the LCSC_DATA_LIMIT
#   comment and the fit_ssm_intercept docstring both named the removed intercept
#   audit and Script 07, which performs no fit, and an empty section banner for
#   the removed function was still standing at the end of the file.
#
# v1.4.0  # Hollingham (2026) — 2026-08-16. Removes
#   compute_intercept_audit, which had no caller anywhere in the tree. Its
#   docstring and Methods Supplement §S.3 both attributed a live per-well
#   intercept audit to Script 07; Script 07 reads 03_master_data.csv and
#   visualises it, performing no fit. Removed rather than deprecated so a
#   stale importer fails loudly.
#
# v1.3.0  # Hollingham (2026) — 2026-06-21
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).


# ── Minimum data thresholds ──────────────────────────────────────────────────

# Minimum observations for a per-well SSM fit (after differencing + dropna).
# Sourced from config.py; the alias is retained so existing importers of
# model_utils.MIN_OBS continue to resolve.
MIN_OBS = SSM_MIN_OBS

# Most-recent-window length, in months, for per-well SSM fits. Sourced from
# config.py; the alias is retained so existing importers of
# model_utils.LCSC_DATA_LIMIT continue to resolve. Consumed by Scripts 03, 08
# and 30 — NOT by Script 07, which reads 03_master_data.csv and visualises it
# without fitting. Centroid fits pass window=None (full record). See the
# config.py comment for the window policy and D-006/D-016.
LCSC_DATA_LIMIT = _LCSC_DATA_LIMIT


# ═══════════════════════════════════════════════════════════════════════════════
# DATA ALIGNMENT
# ═══════════════════════════════════════════════════════════════════════════════

def build_ssm_frame(h_series, climate, lag=None, window=None,
                    drainage_datum=DRAINAGE_DATUM,
                    provenance=None, exclude_interpolated=False):
    """
    Align well and climate data and compute SSM predictor columns.

    This is the most reusable piece — the bit that every script previously
    duplicated. It handles: type coercion, datetime alignment, rainfall lag
    shift, displacement computation, first-differencing, dropna, and
    windowing.

    Parameters
    ----------
    h_series : pd.Series
        Water level in ground-surface depth convention (negative = below
        ground). Index should be datetime-like or PeriodIndex.
    climate : pd.DataFrame
        Must contain columns 'P_m' (rainfall, m/month) and 'PET'
        (PET, m/month). Index should be datetime-like or PeriodIndex.
    lag : int or None
        Month lag applied to rainfall. None defaults to HEADLINE_LAG
        from config.py.
    window : int or None
        Keep only the most recent `window` observations after alignment.
        None disables windowing and returns the full aligned record.
    drainage_datum : float
        Reference depth (m below ground surface) for displacement.
    provenance : pd.Series or None
        Optional per-cell provenance flags aligned to ``h_series`` from
        the Defect E fix (values in {"measured", "interpolated",
        "missing"}). When supplied together with
        ``exclude_interpolated=True``, rows whose ``h`` cell was
        flagged ``interpolated`` are dropped before differencing. The
        h_prev term retains its physical interpretation: a row whose
        h_prev cell is interpolated is also dropped (a measured Δh
        cannot be computed without a measured h_prev). Default None.
    exclude_interpolated : bool
        If True and a provenance series is supplied, exclude
        interpolated cells from the fit. Default False (preserves the
        canonical published β₁/β₂/β₃ coefficient table; see Defect E
        Q1, Martin's call 2026-05-19).

    Returns
    -------
    pd.DataFrame with columns:
        h            — water level (m, negative below ground)
        h_prev       — h shifted by one month
        Delta_h      — h − h_prev
        P            — rainfall (m/month), after lag shift
        PET          — PET (m/month), contemporaneous
        h_disp_prev  — displacement above datum = drainage_datum + h_prev
    Rows with any NaN in these columns are dropped.
    Returns empty DataFrame if insufficient data after alignment.
    """
    if lag is None:
        lag = HEADLINE_LAG

    df = pd.DataFrame({
        "h":   pd.to_numeric(h_series, errors="coerce"),
        "P":   pd.to_numeric(climate["P_m"], errors="coerce"),
        "PET": pd.to_numeric(climate["PET"], errors="coerce"),
    }).dropna()

    # Mask interpolated rows of h BEFORE differencing if requested.
    # Both the current-month h and the previous-month h_prev must be
    # measured for Δh to be a genuine measurement difference. Masking
    # to NaN before the diff step ensures the subsequent dropna step
    # discards those rows naturally.
    if exclude_interpolated and provenance is not None:
        prov_aligned = provenance.reindex(df.index)
        interp_mask = (prov_aligned == "interpolated")
        if interp_mask.any():
            df.loc[interp_mask, "h"] = np.nan
            df = df.dropna(subset=["h"])

    # Displacement above drainage datum
    df["h_disp"] = drainage_datum + df["h"]
    df["h_disp_prev"] = df["h_disp"].shift(1)

    # First differences (datum cancels)
    df["h_prev"] = df["h"].shift(1)
    df["Delta_h"] = df["h"] - df["h_prev"]

    # Rainfall lag
    if lag > 0:
        df["P"] = df["P"].shift(lag)

    df = df.dropna(subset=["Delta_h", "P", "PET", "h_disp_prev"])

    if window is not None and len(df) > window:
        df = df.iloc[-window:]

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# OLS FITTING — MODEL A (NO INTERCEPT)
# ═══════════════════════════════════════════════════════════════════════════════

def fit_ssm(h_series=None, climate=None, lag=None, window=None,
            drainage_datum=DRAINAGE_DATUM, min_obs=MIN_OBS,
            intercept=False, extra_regressors=None, pre_built_frame=None,
            provenance=None, exclude_interpolated=False, fixed_beta_3=None):
    """
    Fit the SSM to a single water-level series via OLS.

    Model (displacement formulation, no intercept by default):
        Δh(t) = β₁·P(t−lag) + β₂·(−PET(t)) + β₃·(−h_disp_prev(t))
                [+ α               if intercept=True]
                [+ Σ γ_k·X_k(t)    if extra_regressors provided]

    Sign convention:
        β₁ > 0  — rainfall raises water table              [hard assertion]
        β₂ > 0  — PET draws water table down                [hard assertion]
        β₃ > 0  — drainage increases with head above datum  [soft assertion]

    Parameters
    ----------
    h_series : pd.Series or None
        Water level in ground-surface depth convention (negative = below
        ground). Indexed by datetime. Ignored if pre_built_frame is given.
    climate : pd.DataFrame or None
        With columns 'P_m' (rainfall, m/month) and 'PET' (PET, m/month),
        indexed by datetime. Ignored if pre_built_frame is given.
    lag : int or None
        Rainfall lag in months. None → HEADLINE_LAG from config.py.
        Ignored if pre_built_frame is given.
    window : int or None
        Keep only the most recent `window` observations after alignment.
        None disables windowing. Ignored if pre_built_frame is given.
    drainage_datum : float
        Reference depth for displacement (default from config). Ignored
        if pre_built_frame is given.
    min_obs : int
        Minimum number of aligned rows required. Returns None if fewer.
    intercept : bool
        If True, include a constant α in the regression (Model B form).
        Default False (Model A / headline SSM).
    extra_regressors : dict or None
        Optional additional predictor columns to include in the design
        matrix. Keys are column names (e.g. 'scraping_dummy'); values are
        array-like aligned to the SSM frame's index. Each becomes a
        separate γ_k coefficient in the fit. Default None.
    pre_built_frame : pd.DataFrame or None
        If provided, skip the build_ssm_frame call and use this frame
        directly. Must contain 'Delta_h', 'P', 'PET', 'h_disp_prev'
        columns. Useful when the caller pre-slices on a date or applies
        custom data preparation. Default None.
    provenance : pd.Series or None
        Optional per-cell provenance flags aligned to ``h_series`` from
        the Defect E fix (values in {"measured", "interpolated",
        "missing"}). Forwarded to ``build_ssm_frame``. Ignored if
        ``pre_built_frame`` is given. Default None.
    exclude_interpolated : bool
        If True and ``provenance`` is supplied, exclude interpolated
        cells from the fit (measured-only sensitivity path). Default
        False: the canonical published β₁/β₂/β₃ coefficient table is
        produced with interpolated rows retained (Defect E Q1 — Martin's
        call 2026-05-19). Ignored if ``pre_built_frame`` is given.
    fixed_beta_3 : float or None
        If provided, β₃ is NOT estimated — it is held at this value and
        only β₁/β₂ are fitted. The drainage term β₃·(−h_disp_prev) is
        moved to the left-hand side as a known offset, so the regression
        solves Δh + fixed_beta_3·h_disp_prev = β₁·P + β₂·(−PET). The
        returned ``beta_3_drainage`` is the supplied value; its p-value
        and standard error are NaN (it was not estimated). This supports
        substrate-triangulation-anchored constrained fits (e.g. the C4
        Forest sensitivity, where the unconstrained β₃ is degenerate).
        Default None (β₃ estimated as normal). Combinable with
        ``intercept`` and ``extra_regressors``.

    Returns
    -------
    dict with keys:
        beta_1_recharge, beta_2_atmospheric_draw, beta_3_drainage   — coefficients
        pvalue_beta_1, pvalue_beta_2, pvalue_beta_3                — p-values
        se_beta_1, se_beta_2, se_beta_3                             — standard errors
        R2                                                          — fit R²
        n                                                           — number of observations
        resid                                                       — residual Series

    Conditional additional keys:
        If intercept=True:
            alpha, pvalue_alpha, se_alpha
        If extra_regressors provided:
            For each user-supplied column 'foo':
                foo, pvalue_foo, se_foo

    Returns None if insufficient data or OLS fails.

    Notes
    -----
    fit_ssm_intercept(...) is preserved as a thin wrapper around
    fit_ssm(intercept=True, ...) for backward compatibility with Scripts
    07, 08, 22, 24.
    """
    if pre_built_frame is not None:
        df = pre_built_frame
        # Validate the pre-built frame has the required columns
        required = {"Delta_h", "P", "PET", "h_disp_prev"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"pre_built_frame missing required columns: {missing}"
            )
    else:
        if h_series is None or climate is None:
            raise ValueError(
                "Either pre_built_frame or both (h_series, climate) must be "
                "provided."
            )
        df = build_ssm_frame(h_series, climate, lag=lag, window=window,
                             drainage_datum=drainage_datum,
                             provenance=provenance,
                             exclude_interpolated=exclude_interpolated)

    if len(df) < min_obs:
        return None

    # Build base design matrix
    X = pd.DataFrame({
        "beta_1_recharge":         df["P"].values,
        "beta_2_atmospheric_draw": -df["PET"].values,
        "beta_3_drainage":         -df["h_disp_prev"].values,
    }, index=df.index)

    # Constrained-β₃ mode: hold β₃ fixed, drop its column, move the drainage
    # term to the LHS as a known offset (only β₁/β₂ are then estimated).
    if fixed_beta_3 is not None:
        X = X.drop(columns=["beta_3_drainage"])

    # Append extra regressors if provided
    if extra_regressors:
        for col_name, col_values in extra_regressors.items():
            X[col_name] = np.asarray(col_values, dtype=float)

    # Add intercept if requested
    if intercept:
        X = sm.add_constant(X, has_constant="add")

    y = df["Delta_h"].values
    if fixed_beta_3 is not None:
        # Δh − β₃·(−h_disp_prev) = Δh + β₃·h_disp_prev  → known LHS offset
        y = y + float(fixed_beta_3) * df["h_disp_prev"].values

    # Drop any rows where extra regressors introduced NaNs (only needed if
    # extra_regressors or intercept-with-constant path may have introduced
    # NaNs — the canonical no-intercept, no-extras path uses build_ssm_frame
    # which has already dropna'd, so we skip the mask construction there to
    # preserve byte-identical floating-point order with v1.0.0).
    if extra_regressors or intercept or fixed_beta_3 is not None:
        mask = X.notna().all(axis=1) & pd.notna(y)
        if mask.sum() < min_obs:
            return None
        X = X[mask]
        y = y[mask]

    try:
        model = sm.OLS(y, X).fit()
    except Exception:
        return None

    # β₃ is either estimated or held at the supplied fixed value
    if fixed_beta_3 is not None:
        _b3, _pb3, _sb3 = float(fixed_beta_3), float("nan"), float("nan")
    else:
        _b3  = float(model.params["beta_3_drainage"])
        _pb3 = float(model.pvalues["beta_3_drainage"])
        _sb3 = float(model.bse["beta_3_drainage"])

    result = {
        "beta_1_recharge":         float(model.params["beta_1_recharge"]),
        "beta_2_atmospheric_draw": float(model.params["beta_2_atmospheric_draw"]),
        "beta_3_drainage":         _b3,
        "pvalue_beta_1":           float(model.pvalues["beta_1_recharge"]),
        "pvalue_beta_2":           float(model.pvalues["beta_2_atmospheric_draw"]),
        "pvalue_beta_3":           _pb3,
        "se_beta_1":               float(model.bse["beta_1_recharge"]),
        "se_beta_2":               float(model.bse["beta_2_atmospheric_draw"]),
        "se_beta_3":               _sb3,
        "R2":                      float(model.rsquared),
        "n":                       int(len(X)),
        "resid":                   pd.Series(model.resid, index=X.index, name="resid"),
    }

    if intercept:
        result["alpha"]        = float(model.params["const"])
        result["pvalue_alpha"] = float(model.pvalues["const"])
        result["se_alpha"]     = float(model.bse["const"])

    if extra_regressors:
        for col_name in extra_regressors:
            result[col_name]              = float(model.params[col_name])
            result[f"pvalue_{col_name}"]  = float(model.pvalues[col_name])
            result[f"se_{col_name}"]      = float(model.bse[col_name])

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# OLS FITTING — MODEL B (WITH INTERCEPT)
# ═══════════════════════════════════════════════════════════════════════════════

def fit_ssm_intercept(h_series, climate, lag=None, window=None,
                      drainage_datum=DRAINAGE_DATUM, min_obs=MIN_OBS):
    """
    Fit the SSM with a constant intercept term (Model B).

    Model:
        Δh(t) = α + β₁·P(t−lag) + β₂·(−PET(t)) + β₃·(−h_disp_prev(t))

    Used by Scripts 22 (residual diagnostics) and 24 (residual
    seasonality). The intercept α captures any constant
    bias (e.g. net lateral inflow/outflow not represented by the three
    mechanistic terms).

    Parameters
    ----------
    Same as fit_ssm().

    Returns
    -------
    dict with all fit_ssm keys plus:
        alpha        — fitted intercept value (m/month)
        pvalue_alpha — p-value for the intercept
        se_alpha     — standard error of the intercept
    Or None if insufficient data.

    Notes
    -----
    Since model_utils v1.1.0 this is a thin wrapper around
    fit_ssm(intercept=True, ...). Preserved as a separate public function
    for backward compatibility with its callers (Scripts 22 and 24).
    """
    return fit_ssm(h_series, climate, lag=lag, window=window,
                   drainage_datum=drainage_datum, min_obs=min_obs,
                   intercept=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FORWARD SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

def simulate_ssm(h0, P, PET, b1, b2, b3,
                 drainage_datum=DRAINAGE_DATUM):
    """
    Iterative forward simulation of the SSM from an initial condition.

    Implements the displacement recurrence:
        h(t) = h(t-1) + β₁·P(t) − β₂·PET(t) − β₃·(D + h(t-1))
             = (1−β₃)·h(t-1) + β₁·P(t) − β₂·PET(t) − β₃·D

    The rainfall array P should already be lag-aligned by the caller
    (i.e. P[t] corresponds to the rainfall that drives month t's
    water-table change).

    Parameters
    ----------
    h0 : float
        Initial water table (negative convention, m below ground surface).
    P : array-like
        Precipitation (m/month), lag-aligned.
    PET : array-like
        PET (m/month), contemporaneous.
    b1, b2, b3 : float
        SSM coefficients (all positive under correct specification).
    drainage_datum : float
        Reference depth for displacement (default from config).

    Returns
    -------
    np.ndarray of simulated h values, length = len(P).
    h[0] is the result of the first timestep (not the initial condition).
    """
    P = np.asarray(P, dtype=float)
    PET = np.asarray(PET, dtype=float)
    n = len(P)
    h = np.full(n, np.nan)
    h_t = h0

    for t in range(n):
        h_disp = drainage_datum + h_t
        dh = b1 * P[t] - b2 * PET[t] - b3 * h_disp
        h_t = h_t + dh
        h[t] = h_t

    return h


# ═══════════════════════════════════════════════════════════════════════════════
# P_FLOOD THRESHOLD (ITERATED CLOSED FORM)
# ═══════════════════════════════════════════════════════════════════════════════

def pflood_lambda(h_target, h_0, b1, b2, b3,
                  months, P_clim, PET_clim,
                  drainage_datum=DRAINAGE_DATUM):
    """
    Iterated closed-form P_flood (Section 3.6.3 of Hollingham 2026).

    Given the monthly recurrence:
        h(t) = (1−β₃)·h(t−1) + β₁·λ·P_clim(t) − β₂·PET_clim(t) − β₃·D

    solves for the rainfall multiplier λ that brings h from h_0 to
    h_target over the specified horizon (sequence of calendar months).

    The corrected formula (with datum drain term):
        α = 1 − β₃
        λ = (h_target − h₀·αⁿ + β₂·S_E + D·(1−αⁿ)) / (β₁·S_P)

    where:
        S_P = Σᵢ α^(n-1-i) · P_clim(mᵢ)    — weighted rainfall sum
        S_E = Σᵢ α^(n-1-i) · PET_clim(mᵢ)  — weighted PET sum

    Parameters
    ----------
    h_target : float
        Target head (m). 0 = ground surface; -0.10 = SD15b; -0.25 = SD16.
    h_0 : float
        Antecedent head (m, negative = below ground).
    b1, b2, b3 : float
        Cluster SSM coefficients. b1, b2 in SSM-native units (m per mm
        for P/PET inputs in mm; or m per m if inputs in m — must be
        consistent with P_clim/PET_clim units). b3 dimensionless, positive.
    months : list[int]
        Sequence of calendar months forming the forecast horizon
        (e.g. [10, 11, 12, 1] for Oct through Jan).
    P_clim : dict
        Monthly rainfall climatology keyed by calendar month 1..12.
        Units must match b1.
    PET_clim : dict
        Monthly PET climatology keyed by calendar month 1..12.
        Units must match b2.
    drainage_datum : float
        Displacement reference depth (m below ground surface).

    Returns
    -------
    dict with keys:
        lam            — rainfall multiplier λ
        P_flood_mm     — λ × Σ P_clim (total required rainfall, mm)
        slope_A        — collapsed linear form: P_flood = A·d + B
        intercept_B    — collapsed linear form intercept
        S_P, S_E       — weighted sums
        alpha, alpha_n — α and αⁿ
        n              — horizon length
        horizon        — month sequence (echoed back)
        P_clim_total   — unweighted climatological rainfall total
        PET_clim_total — unweighted climatological PET total

    Notes
    -----
    lam < 0 or non-finite indicates an unreachable target (the well
    cannot be brought to h_target from h_0 under positive rainfall
    given the drainage balance). Callers should check np.isfinite(lam)
    and lam > 0.
    """
    n = len(months)
    alpha = 1.0 - b3
    alpha_n = alpha ** n

    S_P = sum(alpha ** (n - 1 - i) * P_clim[m]   for i, m in enumerate(months))
    S_E = sum(alpha ** (n - 1 - i) * PET_clim[m] for i, m in enumerate(months))
    P_clim_total   = sum(P_clim[m]   for m in months)
    PET_clim_total = sum(PET_clim[m] for m in months)

    # Datum drain correction: under the displacement formulation the
    # constant term −β₃·D accumulates over n steps as −D·(1−αⁿ),
    # entering as a positive addend in the numerator.
    D = drainage_datum
    datum_correction = D * (1.0 - alpha_n)

    denom = b1 * S_P
    if denom == 0 or not np.isfinite(denom):
        lam = float("nan")
        pflood = float("nan")
        slope_A = float("nan")
        intercept_B = float("nan")
    else:
        lam = (h_target - h_0 * alpha_n + b2 * S_E + datum_correction) / denom
        pflood = lam * P_clim_total

        # Collapsed linear form: P_flood = A·d + B  (d = positive depth
        # below ground, h_0 = −d, h_target = 0).
        #   λ = (d·αⁿ + β₂·S_E + D·(1−αⁿ)) / (β₁·S_P)
        #   P_flood = λ · P_clim_total
        slope_A     = (alpha_n * P_clim_total) / denom
        intercept_B = ((b2 * S_E + datum_correction) * P_clim_total) / denom

    return {
        "lam":            lam,
        "P_flood_mm":     pflood,
        "slope_A":        slope_A,
        "intercept_B":    intercept_B,
        "S_P":            S_P,
        "S_E":            S_E,
        "alpha":          alpha,
        "alpha_n":        alpha_n,
        "n":              n,
        "horizon":        months,
        "P_clim_total":   P_clim_total,
        "PET_clim_total": PET_clim_total,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SEASONAL PERTURBATION (SCRIPT 21 REPLACEMENT)
# ═══════════════════════════════════════════════════════════════════════════════

def monthly_perturbation(b1, b2_base, b2_scen_arr,
                         P_eff_base, P_eff_scen, monthly_PET):
    """
    Single-step monthly perturbation: how does each month's Δh change
    when forcing shifts from baseline to scenario?

    Δh_shift(m) = β₁·(P_scen(m) − P_base(m)) − (β₂_scen(m) − β₂_base)·PET(m)

    This is the immediate monthly forcing response — the first-year
    adjustment, not a steady-state prediction. The β₃ drainage term
    does not appear because in the first month after a change, h hasn't
    moved yet, so the drainage response to the *change* is zero.

    This gives physically reasonable numbers (order 0.01–0.05 m/month,
    cumulating to seasonal totals of 0.1–0.5 m) that are directly
    comparable to BACI observations.

    Parameters
    ----------
    b1 : float
        Recharge coefficient (β₁).
    b2_base : float
        Baseline atmospheric draw coefficient (β₂, scalar).
    b2_scen_arr : array-like, length 12
        Scenario β₂ values per calendar month (allows seasonal
        variation, e.g. broadleaf phenology).
    P_eff_base : array-like, length 12
        Baseline effective precipitation per month (after interception).
    P_eff_scen : array-like, length 12
        Scenario effective precipitation per month.
    monthly_PET : array-like, length 12
        Climatological PET per month.

    Returns
    -------
    np.ndarray of 12 monthly head shifts (positive = shallower water
    table = wetter conditions = ecologically favourable).
    """
    b2_scen_arr = np.asarray(b2_scen_arr)
    P_eff_base  = np.asarray(P_eff_base)
    P_eff_scen  = np.asarray(P_eff_scen)
    monthly_PET = np.asarray(monthly_PET)

    dP  = P_eff_scen - P_eff_base
    dB2 = b2_scen_arr - b2_base
    return b1 * dP - dB2 * monthly_PET


# ═══════════════════════════════════════════════════════════════════════════════
# PHYSICAL SIGN ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def assert_physical_signs(fit, context=""):
    """
    Check physical-sign assertions on a fit result.

    Hard assertions (β₁ > 0, β₂ > 0): violations should halt the pipeline.
    Soft assertion (β₃ > 0): violation is warned but does not halt.
    Under the displacement formulation, β₃ > 0 is physically expected
    (Darcy-consistent drainage). A negative β₃ is anomalous and worth
    investigating but not pipeline-fatal.

    Parameters
    ----------
    fit : dict or None
        Result from fit_ssm() or fit_ssm_intercept().
    context : str
        Label for error messages (e.g. "C1 Lake Edge").

    Returns
    -------
    (hard_violations, soft_warnings) — both lists of strings.
    """
    hard = []
    soft = []
    if fit is None:
        return hard, soft
    if not (fit["beta_1_recharge"] > 0):
        hard.append(
            f"[HARD VIOLATION] {context}: β₁ = {fit['beta_1_recharge']:.6f} ≤ 0 "
            f"(rainfall must raise water table)"
        )
    if not (fit["beta_2_atmospheric_draw"] > 0):
        hard.append(
            f"[HARD VIOLATION] {context}: β₂ = {fit['beta_2_atmospheric_draw']:.6f} ≤ 0 "
            f"(PET must draw water table down)"
        )
    if not (fit["beta_3_drainage"] > 0):
        soft.append(
            f"[SOFT WARNING] {context}: β₃ = {fit['beta_3_drainage']:.6f} ≤ 0 "
            f"(displacement drainage expected positive)"
        )
    return hard, soft


# ═══════════════════════════════════════════════════════════════════════════════
# EVALUATION METRICS
# ═══════════════════════════════════════════════════════════════════════════════

def get_metrics(obs, sim):
    """
    Calculate NSE, RMSE, and bias between observed and simulated series.

    Returns
    -------
    (nse, rmse, bias) — all NaN if no valid pairs exist.
    """
    obs_arr = np.asarray(obs, dtype=float)
    sim_arr = np.asarray(sim, dtype=float)
    mask = ~np.isnan(obs_arr) & ~np.isnan(sim_arr)
    if mask.sum() == 0:
        return np.nan, np.nan, np.nan
    o, s = obs_arr[mask], sim_arr[mask]
    mse = np.mean((o - s) ** 2)
    denom = np.sum((o - np.mean(o)) ** 2)
    nse = np.nan if denom == 0 else 1 - (np.sum((o - s) ** 2) / denom)
    return nse, np.sqrt(mse), np.mean(s - o)


def get_r2(obs, sim):
    """Coefficient of determination based on Pearson correlation."""
    obs_arr = np.asarray(obs, dtype=float)
    sim_arr = np.asarray(sim, dtype=float)
    mask = ~np.isnan(obs_arr) & ~np.isnan(sim_arr)
    if mask.sum() < 2:
        return np.nan
    return np.corrcoef(obs_arr[mask], sim_arr[mask])[0, 1] ** 2
