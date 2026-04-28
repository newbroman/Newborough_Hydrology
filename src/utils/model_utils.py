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

    where D = DRAINAGE_DATUM (3.7 m below ground surface)
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
compute_intercept_audit — Model A vs B comparison for a single well
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.config import DRAINAGE_DATUM, HEADLINE_LAG

# ── Minimum data thresholds ──────────────────────────────────────────────────

# Minimum observations for a per-well SSM fit (after differencing + dropna).
MIN_OBS = 30

# Most-recent-window length for per-well fits in the intercept audit
# and benchmarking (Scripts 07, 08).
LCSC_DATA_LIMIT = 100


# ═══════════════════════════════════════════════════════════════════════════════
# DATA ALIGNMENT
# ═══════════════════════════════════════════════════════════════════════════════

def build_ssm_frame(h_series, climate, lag=None, window=None,
                    drainage_datum=DRAINAGE_DATUM):
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

def fit_ssm(h_series, climate, lag=None, window=None,
            drainage_datum=DRAINAGE_DATUM, min_obs=MIN_OBS):
    """
    Fit the headline SSM (no intercept) to a single water-level series.

    Model (displacement formulation):
        Δh(t) = β₁·P(t−lag) + β₂·(−PET(t)) + β₃·(−h_disp_prev(t))

    Sign convention:
        β₁ > 0  — rainfall raises water table              [hard assertion]
        β₂ > 0  — PET draws water table down                [hard assertion]
        β₃ > 0  — drainage increases with head above datum  [soft assertion]

    Parameters
    ----------
    h_series : pd.Series
        Water level in ground-surface depth convention (negative = below
        ground). For per-well fits the caller must apply upstand correction
        before passing so that displacement is relative to ground, not
        pipe top.
    climate : pd.DataFrame
        With columns 'P_m' (rainfall, m/month) and 'PET' (PET, m/month),
        indexed by datetime.
    lag : int or None
        Rainfall lag in months. None → HEADLINE_LAG from config.py.
    window : int or None
        Keep only the most recent `window` observations after alignment.
        None disables windowing and fits on the full record.
    drainage_datum : float
        Reference depth for displacement (default from config).
    min_obs : int
        Minimum number of aligned rows required. Returns None if fewer.

    Returns
    -------
    dict with keys: beta_1, beta_2, beta_3, pvalue_beta_1, pvalue_beta_2,
    pvalue_beta_3, R2, n, resid (residual Series) — or None if insufficient
    data or OLS fails.
    """
    df = build_ssm_frame(h_series, climate, lag=lag, window=window,
                         drainage_datum=drainage_datum)

    if len(df) < min_obs:
        return None

    X = pd.DataFrame({
        "beta_1": df["P"].values,
        "beta_2": -df["PET"].values,
        "beta_3": -df["h_disp_prev"].values,
    }, index=df.index)
    y = df["Delta_h"].values

    try:
        model = sm.OLS(y, X).fit()
    except Exception:
        return None

    return {
        "beta_1":        float(model.params["beta_1"]),
        "beta_2":        float(model.params["beta_2"]),
        "beta_3":        float(model.params["beta_3"]),
        "pvalue_beta_1": float(model.pvalues["beta_1"]),
        "pvalue_beta_2": float(model.pvalues["beta_2"]),
        "pvalue_beta_3": float(model.pvalues["beta_3"]),
        "R2":            float(model.rsquared),
        "n":             int(len(df)),
        "resid":         pd.Series(model.resid, index=df.index, name="resid"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# OLS FITTING — MODEL B (WITH INTERCEPT)
# ═══════════════════════════════════════════════════════════════════════════════

def fit_ssm_intercept(h_series, climate, lag=None, window=None,
                      drainage_datum=DRAINAGE_DATUM, min_obs=MIN_OBS):
    """
    Fit the SSM with a constant intercept term (Model B).

    Model:
        Δh(t) = α + β₁·P(t−lag) + β₂·(−PET(t)) + β₃·(−h_disp_prev(t))

    Used by Scripts 07, 08 (intercept audit), 22 (residual diagnostics),
    and 24 (residual seasonality). The intercept α captures any constant
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
    Or None if insufficient data.
    """
    df = build_ssm_frame(h_series, climate, lag=lag, window=window,
                         drainage_datum=drainage_datum)

    if len(df) < min_obs:
        return None

    X = pd.DataFrame({
        "P":             df["P"].values,
        "PET_neg":       -df["PET"].values,
        "h_disp_neg":    -df["h_disp_prev"].values,
    }, index=df.index)
    X = sm.add_constant(X, has_constant="add")
    y = df["Delta_h"].values

    try:
        model = sm.OLS(y, X).fit()
    except Exception:
        return None

    return {
        "alpha":         float(model.params["const"]),
        "pvalue_alpha":  float(model.pvalues["const"]),
        "beta_1":        float(model.params["P"]),
        "beta_2":        float(model.params["PET_neg"]),
        "beta_3":        float(model.params["h_disp_neg"]),
        "pvalue_beta_1": float(model.pvalues["P"]),
        "pvalue_beta_2": float(model.pvalues["PET_neg"]),
        "pvalue_beta_3": float(model.pvalues["h_disp_neg"]),
        "R2":            float(model.rsquared),
        "n":             int(len(df)),
        "resid":         pd.Series(model.resid, index=df.index, name="resid"),
    }


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
    if not (fit["beta_1"] > 0):
        hard.append(
            f"[HARD VIOLATION] {context}: β₁ = {fit['beta_1']:.6f} ≤ 0 "
            f"(rainfall must raise water table)"
        )
    if not (fit["beta_2"] > 0):
        hard.append(
            f"[HARD VIOLATION] {context}: β₂ = {fit['beta_2']:.6f} ≤ 0 "
            f"(PET must draw water table down)"
        )
    if not (fit["beta_3"] > 0):
        soft.append(
            f"[SOFT WARNING] {context}: β₃ = {fit['beta_3']:.6f} ≤ 0 "
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


# ═══════════════════════════════════════════════════════════════════════════════
# INTERCEPT AUDIT (SCRIPTS 07, 08)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_intercept_audit(target_well_name, df_clean, df_climate):
    """
    Compute Model A (No Intercept) vs Model B (With Intercept) for a
    single well, including one-step and iterative simulations.

    Uses the displacement formulation (h_disp = DRAINAGE_DATUM + h_depth)
    and HEADLINE_LAG rainfall, matching Script 03.

    Parameters
    ----------
    target_well_name : str
        Well name to look up in df_clean columns.
    df_clean : pd.DataFrame
        Clean well data (columns = well names, index = datetime).
    df_climate : pd.DataFrame
        Climate data with 'P_m' and 'PET' columns.

    Returns
    -------
    (metrics_row dict, plotting_payload dict | None)
    """
    from utils.data_utils import normalize_well_name

    target_norm = normalize_well_name(target_well_name)
    target_col = next(
        (c for c in df_clean.columns if normalize_well_name(c) == target_norm), None
    )

    base_row = {
        "Well": target_norm.upper(),
        "Well_Normalized": target_norm,
        "Status": "ok",
        "Model_B_Intercept": np.nan,
        "OneStep_R2_Model_A": np.nan,
        "OneStep_R2_Model_B": np.nan,
        "Iterative_NSE_Model_A": np.nan,
        "Iterative_NSE_Model_B": np.nan,
        "NSE_Penalty_For_Intercept": np.nan,
    }

    if target_col is None:
        base_row["Status"] = "missing_column"
        return base_row, None

    well_series = pd.to_numeric(df_clean[target_col], errors="coerce")
    well_series.index = pd.to_datetime(well_series.index).to_period("M")

    climate = df_climate.copy()
    climate.index = pd.to_datetime(climate.index).to_period("M")

    df = pd.DataFrame(
        {
            "h": well_series,
            "P": pd.to_numeric(climate["P_m"], errors="coerce"),
            "PET": pd.to_numeric(climate["PET"], errors="coerce"),
        }
    ).dropna()

    # Rainfall lag (HEADLINE_LAG from config)
    if HEADLINE_LAG > 0:
        df["P"] = df["P"].shift(HEADLINE_LAG)

    df["h_prev"] = df["h"].shift(1)
    df["Delta_h"] = df["h"] - df["h_prev"]

    # Displacement formulation: h_disp = DRAINAGE_DATUM + h_depth
    df["h_disp_prev"] = DRAINAGE_DATUM + df["h_prev"]

    df = df.dropna()

    if len(df) < LCSC_DATA_LIMIT:
        base_row["Status"] = "insufficient_data"
        return base_row, None

    df = df.iloc[-LCSC_DATA_LIMIT:].copy()

    # Model A: no intercept; Model B: with intercept
    # Both use displacement for the drainage predictor
    x_a = pd.DataFrame(
        {"P": df["P"], "PET_neg": -df["PET"], "h_disp_prev_neg": -df["h_disp_prev"]}
    )
    x_b = sm.add_constant(x_a, has_constant="add")
    y_fit = df["Delta_h"]

    model_a = sm.OLS(y_fit, x_a).fit()
    model_b = sm.OLS(y_fit, x_b).fit()

    p_arr = df["P"].values
    pet_arr = df["PET"].values
    h_obs = df["h"].values

    # Iterative simulation
    h_iter_a = np.full(len(h_obs), np.nan)
    h_iter_b = np.full(len(h_obs), np.nan)
    h_iter_a[0] = h_obs[0]
    h_iter_b[0] = h_obs[0]

    for t in range(1, len(h_obs)):
        h_disp_sim_a = DRAINAGE_DATUM + h_iter_a[t - 1]
        h_disp_sim_b = DRAINAGE_DATUM + h_iter_b[t - 1]
        dh_a = (
            model_a.params["P"] * p_arr[t]
            - model_a.params["PET_neg"] * pet_arr[t]
            - model_a.params["h_disp_prev_neg"] * h_disp_sim_a
        )
        dh_b = (
            model_b.params["const"]
            + model_b.params["P"] * p_arr[t]
            - model_b.params["PET_neg"] * pet_arr[t]
            - model_b.params["h_disp_prev_neg"] * h_disp_sim_b
        )
        h_iter_a[t] = h_iter_a[t - 1] + dh_a
        h_iter_b[t] = h_iter_b[t - 1] + dh_b

    # One-step simulation
    h_one_a = np.full(len(h_obs), np.nan)
    h_one_b = np.full(len(h_obs), np.nan)
    h_one_a[0] = h_obs[0]
    h_one_b[0] = h_obs[0]
    for t in range(1, len(h_obs)):
        h_disp_prev_obs = DRAINAGE_DATUM + h_obs[t - 1]
        h_one_a[t] = h_obs[t - 1] + (
            model_a.params["P"] * p_arr[t]
            - model_a.params["PET_neg"] * pet_arr[t]
            - model_a.params["h_disp_prev_neg"] * h_disp_prev_obs
        )
        h_one_b[t] = h_obs[t - 1] + (
            model_b.params["const"]
            + model_b.params["P"] * p_arr[t]
            - model_b.params["PET_neg"] * pet_arr[t]
            - model_b.params["h_disp_prev_neg"] * h_disp_prev_obs
        )

    nse_a, rmse_a, _ = get_metrics(h_obs, h_iter_a)
    nse_b, rmse_b, _ = get_metrics(h_obs, h_iter_b)
    r2_one_a = get_r2(h_obs, h_one_a)
    r2_one_b = get_r2(h_obs, h_one_b)

    base_row.update(
        {
            "Model_B_Intercept": model_b.params["const"],
            "OneStep_R2_Model_A": r2_one_a,
            "OneStep_R2_Model_B": r2_one_b,
            "Iterative_NSE_Model_A": nse_a,
            "Iterative_NSE_Model_B": nse_b,
            "NSE_Penalty_For_Intercept": nse_a - nse_b,
        }
    )

    payload = {
        "index": df.index.to_timestamp(),
        "h_obs": h_obs,
        "h_one_a": h_one_a,
        "h_one_b": h_one_b,
        "h_iter_a": h_iter_a,
        "h_iter_b": h_iter_b,
        "r2_one_a": r2_one_a,
        "r2_one_b": r2_one_b,
        "nse_a": nse_a,
        "nse_b": nse_b,
        "rmse_a": rmse_a,
        "rmse_b": rmse_b,
        "well_label": target_norm.upper(),
        "intercept": model_b.params["const"],
    }
    return base_row, payload
