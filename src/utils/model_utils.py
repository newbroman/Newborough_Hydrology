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

# Script 01's month bucketing. THE implementation is utils.buckets, which imports
# nothing heavy so that the pipeline's first script and the lint can both have it;
# this re-export keeps `from utils.model_utils import month_bucket` working and
# keeps the rule visible on the SSM module's own surface (T-32).
from utils.buckets import month_bucket                            # noqa: F401,E402


__version__ = "1.12.0"  # Hollingham (2026) — 2026-10-27 (D-281; Martin 01:53 "A your recommendation, B wells
#   deepest reading, c both"). (1) The comparison window is a fixed calendar span: build_ssm_frame's `window`
#   counts calendar months ending at the last aligned row, not valid rows, and last_calendar_months() gives the
#   same cut for callers that tail a frame. (2) fit_ssm_censored(): dry months enter as levels below a bound
#   (Tobit-type maximum likelihood, GHK orthant on fixed Sobol draws); with no dry month it returns fit_ssm's
#   result unchanged. dry_bounds(well) builds the bounds from Script 01's intermediates (pipe-top dry depth less
#   the upstand; the well's floor where no depth was recorded). censored_fill() gives a dry month's expected
#   level for the cluster centroids.
# 1.11.0  # Hollingham (2026) — 2026-10-27 (D-280; Martin 01:21 "Add the depth-dependent model as a
#   third projection beside Model A and Model B, in Script 50 and the viewer"). periodic_steady_state_ddp() and
#   sustained_monthly_response_ddp(): the sustained response of the depth-dependent SSM, which has no closed
#   form, as the difference of two periodic steady states; at kappa = 0 it equals the closed form. Additive.
# 1.10.0  # Hollingham (2026) — 2026-10-08. simulate_ssm() takes alpha=0.0, the free intercept
#   of Model B, so Script 08 can free-run Model B with the shared recurrence (D-244). Default 0 leaves every
#   existing caller's result unchanged.
# 1.9.0  # Hollingham (2026) — 2026-10-03 (D-238; Martin: "WE NEED TO ENSURE INTERCEPTION IS NOT
#   DOUBLE counted", "Let's do the fix"). climate_forcing_change_12() no longer multiplies a rainfall
#   CHANGE by (1 − I): beta_1 was fitted on gross rainfall, so the canopy is already inside it
#   (INTERCEPTION_TREATMENT §3). A change of canopy enters as beta_1·sP·P·(I − I_scen), and a beta_2
#   multiplier per month is accepted; with neither, and no interception, the result is bit-identical.
# 1.8.0  # Hollingham (2026) — 2026-10-01 (D-216). A sustained climate shift as a
#   LEVEL: scenario_delta_series() runs the difference between a perturbed and a baseline SSM run,
#   d(t) = (1 - b3)·d(t-1) + Δf(t), in which the intercept and the drainage datum cancel exactly;
#   sustained_monthly_response() is its periodic steady state for a 12-month forcing change (the
#   climatology in force every year); response_identified() is Script 48's identifiability rule
#   (config.PASTAS_IDENT_*) applied to a fitted beta_3 and its p-value; fit_ssm(with_corr=True) adds
#   the coefficient correlations and the means behind the loss partition (D-217); climate_forcing_change_12()
#   is the monthly forcing change both scripts feed it. monthly_perturbation() is
#   unchanged and stays the one-month RATE (its docstring now says so). Additive.
# 1.7.1  # Hollingham (2026) — 2026-09-26. pflood_lambda docstring: the
#   h_target example named -0.10 m as SD15b; it now points at config (D-201). Docstring only.
# 1.7.0  # Hollingham (2026) — 2026-09-25 (D-195). build_ssm_frame()
#   differences on the monthly CALENDAR. It used to dropna() first and shift the
#   surviving rows, so a month without a level paired the next month with the last
#   measured one: Delta_h spanned two or more months and was fitted to one month's
#   P, PET and start-of-month displacement (151 of 13,211 reference-network pairs,
#   2-23 months). exclude_interpolated had the same flaw: it dropped the bridged
#   month and then differenced straight across it. Now h, P and PET sit on one row
#   per month, the shifts are taken there, and incomplete rows are dropped after.
# 1.6.0  Hollingham (2026) — 2026-09-16. month_bucket(): Script
#   01's field-convention month bucketing, in ONE place (T-32). A reading on
#   day > 15 belongs to that month, day <= 15 to the previous one. The tree
#   carried FIVE correct implementations and THREE written as
#   `d - pd.offsets.MonthBegin(1)`, which is a no-op for days 2-15 and had cost
#   49 of 110 Sentinel scenes their month; the same defect was fixed once on
#   2026-09-13 and reintroduced two days later, because the rule lived in a
#   comment at each call site. Equivalence to every correct variant is proved
#   exhaustively over 1990-2040 by tools/month_bucket_lint.py, a check_all gate.
# v1.5.0  # Hollingham (2026) — 2026-08-16. LCSC_DATA_LIMIT is now
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

def _on_monthly_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """One row per calendar month between the frame's first and last month, so a
    shift of one row is a shift of one month (D-195). The original index values
    are kept for every month that had a row; inserted months (none in practice
    once the climate record is joined, which covers every month) carry NaN."""
    df = df[~df.index.duplicated(keep="first")].sort_index()
    if len(df) < 2:
        return df
    idx = df.index
    per = idx if isinstance(idx, pd.PeriodIndex) else pd.DatetimeIndex(idx).to_period("M")
    if per.has_duplicates:
        raise ValueError("build_ssm_frame: two rows fall in one calendar month; "
                         "bucket the series with month_bucket() first")
    full = pd.period_range(per.min(), per.max(), freq="M")
    if len(full) == len(per):
        return df
    out = df.set_axis(per).reindex(full)
    orig = dict(zip(per, idx))
    if isinstance(idx, pd.PeriodIndex):
        return out
    return out.set_axis(pd.DatetimeIndex([orig.get(q, q.to_timestamp()) for q in full],
                                         name=idx.name))


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
        Keep only the rows in the last `window` calendar months of the aligned
        record (1.12.0, D-281; before, the last `window` valid rows, which reached
        further back at a well with gaps). None returns the full aligned record.
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
    })
    df = _on_monthly_calendar(df)

    # Mask interpolated months of h BEFORE differencing if requested. Both
    # the current-month h and the previous-month h_prev must be measured for
    # Δh to be a genuine measurement difference: the masked month drops, and
    # so does the month after it, because the shift below is taken on the
    # calendar and its h_prev is NaN (D-195; it used to difference across).
    if exclude_interpolated and provenance is not None:
        prov_aligned = provenance.reindex(df.index)
        interp_mask = (prov_aligned == "interpolated")
        if interp_mask.any():
            df.loc[interp_mask, "h"] = np.nan

    # Displacement above drainage datum
    df["h_disp"] = drainage_datum + df["h"]
    df["h_disp_prev"] = df["h_disp"].shift(1)

    # First differences (datum cancels)
    df["h_prev"] = df["h"].shift(1)
    df["Delta_h"] = df["h"] - df["h_prev"]

    # Rainfall lag
    if lag > 0:
        df["P"] = df["P"].shift(lag)

    df = df.dropna(subset=["h", "Delta_h", "P", "PET", "h_disp_prev"])

    if window is not None and len(df):
        # 1.12.0 (D-281): the last `window` CALENDAR months ending at the frame's last
        # row, not the last `window` valid rows. A well with gaps now covers the same
        # months as a well without them (Martin 2026-10-27: "The gaps are a surprise.
        # and I think it is inconsistent."); a complete record is unchanged.
        df = last_calendar_months(df, window)

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# OLS FITTING — MODEL A (NO INTERCEPT)
# ═══════════════════════════════════════════════════════════════════════════════

def fit_ssm(h_series=None, climate=None, lag=None, window=None,
            drainage_datum=DRAINAGE_DATUM, min_obs=MIN_OBS,
            intercept=False, extra_regressors=None, pre_built_frame=None,
            provenance=None, exclude_interpolated=False, fixed_beta_3=None,
            with_corr=False, dry_bound=None):
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
        Calendar months ending at the last aligned row (see build_ssm_frame).
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
        If with_corr=True (1.8.0, D-217):
            corr_beta_2_beta_3 (and corr_alpha_beta_3 with an intercept) — the
            correlation of the coefficient estimates; mean_PET and
            mean_h_disp_prev — the means over the fitted months, from which the
            loss partition each form implies is computed

    dry_bound : pd.Series or None
        1.12.0 (D-281). Upper bounds on h for the months the well was found
        dry (dry_bounds(well) builds them). When given, the fit is
        fit_ssm_censored(): dry months enter as levels below the bound instead
        of being dropped. With no dry month in the window the result is this
        function's own. Not combinable with pre_built_frame, extra_regressors,
        fixed_beta_3 or exclude_interpolated.

    Returns None if insufficient data or OLS fails.

    Notes
    -----
    fit_ssm_intercept(...) is preserved as a thin wrapper around
    fit_ssm(intercept=True, ...) for backward compatibility with Scripts
    07, 08, 22, 24.
    """
    if dry_bound is not None:
        if pre_built_frame is not None or extra_regressors or fixed_beta_3 is not None \
                or exclude_interpolated:
            raise ValueError("fit_ssm: dry_bound (the censored fit) does not combine with "
                             "pre_built_frame, extra_regressors, fixed_beta_3 or exclude_interpolated")
        return fit_ssm_censored(h_series, climate, dry_bound, lag=lag, window=window,
                                drainage_datum=drainage_datum, min_obs=min_obs,
                                intercept=intercept, with_corr=with_corr)
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

    if with_corr:                                   # 1.8.0, D-217 — opt-in, additive
        cov = model.cov_params()

        def _corr(a, b):
            if a not in cov.index or b not in cov.index:
                return float("nan")
            den = np.sqrt(cov.loc[a, a] * cov.loc[b, b])
            return float(cov.loc[a, b] / den) if den > 0 else float("nan")
        result["corr_beta_2_beta_3"] = _corr("beta_2_atmospheric_draw", "beta_3_drainage")
        if intercept:
            result["corr_alpha_beta_3"] = _corr("const", "beta_3_drainage")
        # the design matrix carries −PET and −h_disp_prev
        result["mean_PET"] = float(-X["beta_2_atmospheric_draw"].mean())
        result["mean_h_disp_prev"] = float(-X["beta_3_drainage"].mean()) if "beta_3_drainage" in X else float("nan")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# OLS FITTING — MODEL B (WITH INTERCEPT)
# ═══════════════════════════════════════════════════════════════════════════════

def fit_ssm_intercept(h_series, climate, lag=None, window=None,
                      drainage_datum=DRAINAGE_DATUM, min_obs=MIN_OBS, dry_bound=None):
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
                   intercept=True, dry_bound=dry_bound)


# ═══════════════════════════════════════════════════════════════════════════════
# CENSORED FIT — DRY MONTHS AS LEVELS BELOW A BOUND (1.12.0, D-281)
# ═══════════════════════════════════════════════════════════════════════════════
#
# A dipwell found dry says the water table was below the bottom of the pipe that
# month: an observation h <= c, not a missing value. Dropping it removes the
# driest months from the fit, which is a selection on the response itself. The
# censored fit keeps them. The state equation of the SSM,
#     h(t) = (1 - b3)·h(t-1) + b1·P(t) - b2·PET(t) - b3·z0 [+ alpha] + e(t),
# e ~ N(0, sigma^2), is linear-Gaussian, so a run of J dry months between two
# readings is a Gaussian vector conditioned on the readings either side, and its
# likelihood is the density of the reading after the run times the probability
# that every latent month in the run lies below its bound. That probability is a
# multivariate normal orthant, computed by the GHK simulator on a fixed set of
# scrambled Sobol draws (common random numbers, so the likelihood is smooth in the
# parameters and the fit is deterministic). A run of one month is exact. With no
# dry month in the window the fit IS fit_ssm (returned unchanged), so the published
# coefficients move only where a well was found dry.

from scipy.optimize import minimize as _minimize                  # noqa: E402
from scipy.stats import qmc as _qmc                                # noqa: E402
from scipy.special import log_ndtr as _log_ndtr, ndtri as _ndtri  # noqa: E402
_LOG_SQRT_2PI = 0.5 * np.log(2 * np.pi)


def _logpdf(x, loc=0.0, scale=1.0):
    z = (np.asarray(x) - loc) / scale
    return -0.5 * z * z - np.log(scale) - _LOG_SQRT_2PI


def _psf(z):
    """Two-sided normal p-value for a z statistic."""
    return float(2.0 * np.exp(_log_ndtr(-abs(z))))

CENSORED_STATES = ("dry_recorded", "dry_inferred")
CENSORED_GHK_DRAWS = 2048          # Sobol points (a power of two) for the GHK orthant
CENSORED_GHK_SEED = 20261027       # fixed: the fit must be reproducible run to run
_GHK_CACHE: dict = {}
_BOUND_CACHE: dict = {}


def _ghk_uniforms(dim: int) -> np.ndarray:
    if dim not in _GHK_CACHE:
        u = _qmc.Sobol(d=dim, scramble=True, seed=CENSORED_GHK_SEED).random(CENSORED_GHK_DRAWS)
        _GHK_CACHE[dim] = np.clip(u, 1e-12, 1 - 1e-12)
    return _GHK_CACHE[dim]


def _ghk(mu, S, c, want_mean=False):
    """log P(x <= c) for x ~ N(mu, S), and optionally E[x | x <= c] (GHK)."""
    J = len(mu)
    if J == 1:
        s = float(np.sqrt(S[0, 0])); a = (c[0] - mu[0]) / s
        lp = float(_log_ndtr(a))
        if not want_mean:
            return lp, None
        lam = float(np.exp(_logpdf(a) - lp))
        return lp, np.array([mu[0] - s * lam])
    L = np.linalg.cholesky(S + 1e-18 * np.eye(J))
    U = _ghk_uniforms(J)
    R = U.shape[0]
    z = np.zeros((R, J)); logw = np.zeros(R)
    for k in range(J):
        b = (c[k] - mu[k] - z[:, :k] @ L[k, :k]) / L[k, k]
        lpk = _log_ndtr(b)
        logw += lpk
        z[:, k] = _ndtri(np.clip(U[:, k] * np.exp(lpk), 1e-300, 1 - 1e-16))
        z[:, k] = np.minimum(z[:, k], b)
    m = logw.max()
    w = np.exp(logw - m)
    lp = float(m + np.log(w.mean()))
    if not want_mean:
        return lp, None
    x = mu + z @ L.T
    return lp, (w[:, None] * x).sum(axis=0) / w.sum()


def _run_moments(h0, u, a, sig2, has_after):
    """Mean and covariance of the latent path x_1..x_J (and the reading after it,
    as the last element, when has_after) started from the reading h0."""
    n = len(u)
    m = np.empty(n); prev = h0
    for k in range(n):
        prev = a * prev + u[k]; m[k] = prev
    i = np.arange(n)
    M = np.where(i[:, None] >= i[None, :], a ** np.clip(i[:, None] - i[None, :], 0, None), 0.0)
    return m, sig2 * (M @ M.T)


def dry_bounds(well: str) -> pd.Series:
    """Upper bounds on the ground-referenced level (m, negative below ground) for
    each month the well was found dry, indexed by month. The bound is the dry
    depth recorded that month where there is one; dry depths are sounded from the
    pipe top, so the upstand is subtracted. A dry month with no recorded depth
    takes the well's floor: the deeper of its deepest measured reading and its
    deepest recorded dry depth, either of which shows the pipe base lies at least
    that deep (D-281, Martin 2026-10-27 "B wells deepest reading"). Read from
    Script 01's intermediates, never from raw data. Empty if the well was never dry."""
    from utils.paths import (INT_OBSERVATION_STATES, INT_DRY_DEPTHS, INT_WELL_ELEVATIONS,
                             INT_WELLS_CLEAN, INT_WELLS_PROVENANCE)
    if not _BOUND_CACHE:
        st = pd.read_csv(INT_OBSERVATION_STATES, index_col=0, parse_dates=True)
        _BOUND_CACHE["states"] = st.rename(columns=str.lower)
        dd = pd.read_csv(INT_DRY_DEPTHS, parse_dates=["month"])
        dd["well"] = dd["well"].str.lower()
        _BOUND_CACHE["depths"] = dd
        el = pd.read_csv(INT_WELL_ELEVATIONS)
        _BOUND_CACHE["upstand"] = {str(n).lower(): (float(u) if pd.notna(u) else 0.0)
                                  for n, u in zip(el["Name_norm"], el["Upstand_m"])}
        wc = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True).rename(columns=str.lower)
        pv = pd.read_csv(INT_WELLS_PROVENANCE, index_col=0, parse_dates=True).rename(columns=str.lower)
        _BOUND_CACHE["deepest"] = {c: float(-wc[c].where(pv.reindex(index=wc.index)[c] == "measured").min())
                                   if c in pv.columns else float(-wc[c].min()) for c in wc.columns}
    w = str(well).lower()
    st = _BOUND_CACHE["states"]
    if w not in st.columns:
        return pd.Series(dtype=float, name=w)
    dry = st.index[st[w].isin(CENSORED_STATES)]
    if not len(dry):
        return pd.Series(dtype=float, name=w)
    up = _BOUND_CACHE["upstand"].get(w, 0.0)
    dd = _BOUND_CACHE["depths"]
    ground = (dd.loc[dd["well"] == w].set_index("month")["dry_depth_m"] - up)
    ground = ground[~ground.index.duplicated(keep="first")]
    floor = np.nanmax([_BOUND_CACHE["deepest"].get(w, np.nan),
                       ground.max() if len(ground) else np.nan])
    depth = ground.reindex(dry).fillna(floor)
    return (-depth).dropna().rename(w)


def _censored_layout(h_series, climate, dry_bound, lag, window):
    df = pd.DataFrame({"h": pd.to_numeric(h_series, errors="coerce"),
                       "P": pd.to_numeric(climate["P_m"], errors="coerce"),
                       "PET": pd.to_numeric(climate["PET"], errors="coerce")})
    df = _on_monthly_calendar(df)
    if lag and lag > 0:
        df["P"] = df["P"].shift(lag)
    per = pd.DatetimeIndex(df.index).to_period("M")
    cb = pd.Series(np.nan, index=per)
    if dry_bound is not None and len(dry_bound):
        b = pd.Series(np.asarray(dry_bound, dtype=float),
                      index=pd.DatetimeIndex(dry_bound.index).to_period("M"))
        b = b[~b.index.duplicated(keep="first")]
        cb = b.reindex(per)
    clim_ok = (df["P"].notna() & df["PET"].notna()).values
    cvals = cb.values
    hv = df["h"].values.copy()
    hv[~np.isnan(cvals)] = np.nan          # a dry month's filled value is not a reading
    status = np.where(~clim_ok, "x", np.where(~np.isnan(cvals), "c", np.where(np.isnan(hv), "x", "o")))
    live = np.where(status != "x")[0]
    if not len(live):
        return None
    last = live[-1]
    first_row = 0 if window is None else max(0, last - int(window) + 1)
    return dict(df=df, per=per, h=hv, c=cvals, status=status, first_row=first_row, last=last)


def _censored_pieces(lay):
    """Walk the window: one-step transitions between readings, and runs of dry
    months anchored on the reading before them (closed by the reading after, or
    open at a gap or the end of the record)."""
    st, h = lay["status"], lay["h"]
    trans, runs = [], []
    anchor, run = None, []
    for t in range(max(lay["first_row"] - 1, 0), lay["last"] + 1):
        in_win = t >= lay["first_row"]
        s = st[t]
        if s == "x":
            if anchor is not None and run:
                runs.append((anchor, run, None))
            anchor, run = None, []
        elif s == "c":
            if anchor is not None and in_win:
                run.append(t)
        else:
            if anchor is not None and in_win:
                if run:
                    runs.append((anchor, run, t))
                else:
                    trans.append(t)
            anchor, run = t, []
    if anchor is not None and run:
        runs.append((anchor, run, None))
    return np.array(trans, dtype=int), runs


def _censored_negll(theta, lay, trans, runs, z0, intercept):
    b1, b2, b3 = theta[:3]
    alpha = theta[3] if intercept else 0.0
    sig = float(np.exp(theta[-1])); sig2 = sig * sig
    P, E, h, c = lay["df"]["P"].values, lay["df"]["PET"].values, lay["h"], lay["c"]
    a = 1.0 - b3
    u = b1 * P - b2 * E - b3 * z0 + alpha
    ll = 0.0
    if len(trans):
        e = h[trans] - (a * h[trans - 1] + u[trans])
        ll += float(np.sum(_logpdf(e, scale=sig)))
    for anc, run, after in runs:
        idx = run + ([after] if after is not None else [])
        m, S = _run_moments(h[anc], u[idx], a, sig2, after is not None)
        J = len(run)
        if after is not None:
            myy, Syy = m[J], S[J, J]
            ll += float(_logpdf(h[after], loc=myy, scale=np.sqrt(Syy)))
            Sxy = S[:J, J]
            mu = m[:J] + Sxy * (h[after] - myy) / Syy
            Sc = S[:J, :J] - np.outer(Sxy, Sxy) / Syy
        else:
            mu, Sc = m, S
        ll += _ghk(mu, Sc, c[run])[0]
    return -ll if np.isfinite(ll) else 1e300


def fit_ssm_censored(h_series, climate, dry_bound, lag=None, window=None,
                     drainage_datum=DRAINAGE_DATUM, min_obs=MIN_OBS,
                     intercept=False, with_corr=False, force_ml=False):
    """
    Fit the SSM with dry months treated as censored observations (D-281).

    Same model, alignment, calendar window and return keys as fit_ssm, plus
    n_censored, n_transitions, sigma, loglik, converged and method. `dry_bound`
    is a Series of upper bounds on h indexed by month (dry_bounds(well) gives it);
    `window` counts calendar months ending at the last month that is either a
    reading or a dry month. Maximum likelihood: readings enter through the
    one-step state equation exactly as in OLS; each run of dry months enters
    through the reading after it and the GHK orthant probability. Standard errors
    come from the numerical Hessian of the log-likelihood; p-values are normal.
    With no dry month in the window this returns fit_ssm's own result, unless
    force_ml (the identity check: ML on readings alone reproduces OLS).
    """
    if lag is None:
        lag = HEADLINE_LAG
    lay = _censored_layout(h_series, climate, dry_bound, lag, window)
    if lay is None:
        return None
    h_masked = pd.Series(lay["h"], index=lay["df"].index)
    win = (lay["first_row"], lay["last"])
    trans, runs = _censored_pieces(lay)
    n_cens = int(sum(len(r[1]) for r in runs))

    def _ols():
        sub = h_masked.iloc[max(win[0] - 1, 0): win[1] + 1]
        return fit_ssm(sub, climate, lag=lag, window=None, drainage_datum=drainage_datum,
                       min_obs=min_obs, intercept=intercept, with_corr=with_corr)
    if n_cens == 0 and not force_ml:
        if dry_bound is None or not np.isfinite(lay["c"]).any():
            return fit_ssm(h_series, climate, lag=lag, window=window, drainage_datum=drainage_datum,
                           min_obs=min_obs, intercept=intercept, with_corr=with_corr)
        out = _ols()
        if out is not None:
            out.update(n_censored=0, n_transitions=out["n"], method="ols")
        return out
    if len(trans) + n_cens < min_obs:
        return None
    start = _ols()
    if start is None:
        return None
    th0 = [start["beta_1_recharge"], start["beta_2_atmospheric_draw"], start["beta_3_drainage"]]
    if intercept:
        th0.append(start["alpha"])
    th0.append(np.log(max(float(np.std(start["resid"])), 1e-6)))
    th0 = np.array(th0, dtype=float)
    z0 = float(drainage_datum)
    fn = lambda th: _censored_negll(th, lay, trans, runs, z0, intercept)
    res = _minimize(fn, th0, method="BFGS", options={"gtol": 1e-6, "maxiter": 2000})
    if not res.success:
        res2 = _minimize(fn, res.x, method="Nelder-Mead",
                         options={"xatol": 1e-10, "fatol": 1e-12, "maxiter": 40000, "maxfev": 80000})
        if res2.fun <= res.fun:
            res = res2
    th = res.x
    # Hessian by central differences (the GHK draws are fixed, so this is smooth)
    k = len(th); H = np.empty((k, k)); step = 1e-4 * np.maximum(np.abs(th), 1e-2)
    for i in range(k):
        for j in range(i, k):
            ei = np.zeros(k); ej = np.zeros(k); ei[i] = step[i]; ej[j] = step[j]
            H[i, j] = H[j, i] = (fn(th + ei + ej) - fn(th + ei - ej) - fn(th - ei + ej)
                                 + fn(th - ei - ej)) / (4 * step[i] * step[j])
    n_used = int(len(trans) + n_cens + sum(1 for r in runs if r[2] is not None))
    try:
        # ML variance carries 1/n; scale to OLS's 1/(n - p) so the standard errors of
        # the two paths are comparable (with no dry month they then agree)
        p_beta = 4 if intercept else 3
        cov = np.linalg.inv(H) * (n_used / max(n_used - p_beta, 1))
        se = np.sqrt(np.clip(np.diag(cov), 0, None))
    except np.linalg.LinAlgError:
        cov = np.full((k, k), np.nan); se = np.full(k, np.nan)
    pv = lambda i: _psf(th[i] / se[i]) if se[i] > 0 else float("nan")
    b1, b2, b3 = th[:3]; alpha = th[3] if intercept else 0.0
    fr = lay["df"]
    P, E, h = fr["P"].values, fr["PET"].values, lay["h"]
    y = h[trans] - h[trans - 1]
    yhat = b1 * P[trans] - b2 * E[trans] - b3 * (z0 + h[trans - 1]) + alpha
    ssr = float(np.sum((y - yhat) ** 2))
    sst = float(np.sum((y - y.mean()) ** 2)) if intercept else float(np.sum(y ** 2))
    out = {
        "beta_1_recharge": float(b1), "beta_2_atmospheric_draw": float(b2), "beta_3_drainage": float(b3),
        "pvalue_beta_1": pv(0), "pvalue_beta_2": pv(1), "pvalue_beta_3": pv(2),
        "se_beta_1": float(se[0]), "se_beta_2": float(se[1]), "se_beta_3": float(se[2]),
        "R2": 1.0 - ssr / sst if sst > 0 else float("nan"),
        "n": n_used,
        "resid": pd.Series(y - yhat, index=fr.index[trans], name="resid"),
        "n_censored": n_cens, "n_transitions": int(len(trans)),
        "sigma": float(np.exp(th[-1])), "loglik": float(-res.fun),
        "converged": bool(res.success), "method": "censored_ml_ghk",
    }
    if intercept:
        out.update(alpha=float(alpha), pvalue_alpha=pv(3), se_alpha=float(se[3]))
    if with_corr:
        d = np.sqrt(np.diag(cov))
        out["corr_beta_2_beta_3"] = float(cov[1, 2] / (d[1] * d[2])) if d[1] * d[2] > 0 else float("nan")
        if intercept:
            out["corr_alpha_beta_3"] = float(cov[3, 2] / (d[3] * d[2])) if d[3] * d[2] > 0 else float("nan")
        out["mean_PET"] = float(np.mean(E[trans]))
        out["mean_h_disp_prev"] = float(np.mean(z0 + h[trans - 1]))
    return out


def censored_fill(h_series, climate, dry_bound, fit, lag=None, drainage_datum=DRAINAGE_DATUM):
    """The well's level series with each dry month set to its expected level under
    `fit` given the readings either side and its bound, E[h | readings, h <= c].
    Used to build cluster centroids without the driest members dropping out."""
    if lag is None:
        lag = HEADLINE_LAG
    lay = _censored_layout(h_series, climate, dry_bound, lag, None)
    out = pd.to_numeric(h_series, errors="coerce").copy()
    if lay is None or fit is None:
        return out
    _, runs = _censored_pieces(dict(lay, first_row=0))
    b1, b2, b3 = fit["beta_1_recharge"], fit["beta_2_atmospheric_draw"], fit["beta_3_drainage"]
    alpha = fit.get("alpha", 0.0) or 0.0
    sig2 = float(fit.get("sigma", np.std(fit["resid"]))) ** 2
    fr = lay["df"]; h, c = lay["h"], lay["c"]
    u = b1 * fr["P"].values - b2 * fr["PET"].values - b3 * float(drainage_datum) + alpha
    a = 1.0 - b3
    for anc, run, after in runs:
        idx = run + ([after] if after is not None else [])
        m, S = _run_moments(h[anc], u[idx], a, sig2, after is not None)
        J = len(run)
        if after is not None:
            Sxy = S[:J, J]
            mu = m[:J] + Sxy * (h[after] - m[J]) / S[J, J]
            Sc = S[:J, :J] - np.outer(Sxy, Sxy) / S[J, J]
        else:
            mu, Sc = m, S
        _, ex = _ghk(mu, Sc, c[run], want_mean=True)
        out.loc[fr.index[run]] = ex
    return out


def donor_censored_fill(h_series, dry_bound, donors, fit=None, climate=None, min_overlap=None,
                        min_r=None, lag=None, drainage_datum=DRAINAGE_DATUM):
    """Fill each dry month of a well with its expected level below the bound, centred on its nearest
    cluster-mate's reading (D-281; Martin 2026-10-27 "use nearest neighbour to fill dry members with their
    censored expected level"). `donors` is a list of (name, series), nearest first, each with its own dry
    months already blank. A donor qualifies by Script 51's rule: at least `min_overlap` months read at both
    wells and r >= `min_r` over them. For a dry month the first qualifying donor read that month gives
    mu = a + b·h_donor from the straight line over the overlap, with s its residual standard deviation, and
    the fill is E[h | h ~ N(mu, s^2), h <= c]. A dry month no qualifying donor was read in falls back on the
    well's own censored fit (censored_fill), when `fit` is given. Returns (filled series, audit DataFrame)."""
    from utils.config import DONOR_MIN_OVERLAP_MONTHS, DONOR_MIN_R
    min_overlap = DONOR_MIN_OVERLAP_MONTHS if min_overlap is None else min_overlap
    min_r = DONOR_MIN_R if min_r is None else min_r
    h = pd.to_numeric(h_series, errors="coerce").copy()
    b = dry_bound.dropna() if dry_bound is not None else pd.Series(dtype=float)
    b = b[b.index.isin(h.index)]
    h_read = h.copy(); h_read.loc[b.index] = np.nan
    lines = []
    for name, d in donors:
        d = pd.to_numeric(d, errors="coerce").reindex(h.index)
        ok = h_read.notna() & d.notna()
        if ok.sum() < min_overlap:
            continue
        r = float(np.corrcoef(h_read[ok], d[ok])[0, 1])
        if not np.isfinite(r) or r < min_r:
            continue
        slope, icpt = np.polyfit(d[ok].values, h_read[ok].values, 1)
        res = h_read[ok].values - (icpt + slope * d[ok].values)
        lines.append((name, d, float(icpt), float(slope), float(np.std(res, ddof=2)), r, int(ok.sum())))
    out = h_read.copy()
    rows, left = [], []
    for t, c in b.items():
        hit = next((ln for ln in lines if pd.notna(ln[1].get(t))), None)
        if hit is None:
            left.append(t)
            continue
        name, d, a_, b_, s_, r_, n_ = hit
        mu = a_ + b_ * float(d.loc[t])
        z = (c - mu) / s_
        val = float(mu - s_ * np.exp(_logpdf(z) - _log_ndtr(z)))
        out.loc[t] = val
        rows.append(dict(month=t, bound_m=float(c), fill_m=val, mu_m=float(mu), s_m=s_, source="donor",
                         donor=name, donor_r=r_, donor_overlap=n_))
    if left:
        if fit is not None and climate is not None:
            mf = censored_fill(h_read, climate, b, fit, lag=lag, drainage_datum=drainage_datum)
            for t in left:
                v = mf.get(t)
                ok = v is not None and pd.notna(v)
                if ok:
                    out.loc[t] = float(v)
                rows.append(dict(month=t, bound_m=float(b.loc[t]), fill_m=float(v) if ok else np.nan, mu_m=np.nan,
                                 s_m=np.nan, source="model" if ok else "unfilled", donor="", donor_r=np.nan,
                                 donor_overlap=0))
        else:
            for t in left:
                rows.append(dict(month=t, bound_m=float(b.loc[t]), fill_m=np.nan, mu_m=np.nan, s_m=np.nan,
                                 source="unfilled", donor="", donor_r=np.nan, donor_overlap=0))
    return out, pd.DataFrame(rows)


def apply_dry_fill(wells: pd.DataFrame) -> pd.DataFrame:
    """The level frame cluster centroids are built from (D-281): `wells` with each dry
    member-month replaced by the level Script 03 filled it with (03_21_dry_member_fill.csv:
    its expected level below the bound, centred on its nearest cluster-mate). Any script that
    averages members into a centroid reads this rather than re-deriving the fill, so every
    centroid in the pipeline is the same one. Unchanged if the fill file is absent."""
    from utils.paths import OUT_03_DRY_FILL
    out = wells.copy()
    if not OUT_03_DRY_FILL.exists():
        return out
    f = pd.read_csv(OUT_03_DRY_FILL)
    if f.empty:
        return out
    f = f[f["fill_m"].notna()]
    cols = {str(c).lower(): c for c in out.columns}
    idx = pd.DatetimeIndex(out.index)
    for w, g in f.groupby(f["well"].astype(str).str.lower()):
        c = cols.get(w)
        if c is None:
            continue
        m = pd.to_datetime(g["month"].astype(str) + "-01")
        ok = m.isin(idx)
        out.loc[m[ok].values, c] = g.loc[ok.values, "fill_m"].values
    return out


def last_calendar_months(frame: pd.DataFrame, n: int) -> pd.DataFrame:
    """The rows of an SSM frame that fall in its last `n` calendar months (D-281).
    The comparison window is a fixed calendar span, not the last n valid rows, so a
    well with gaps covers the same months as a well without them."""
    if n is None or not len(frame):
        return frame
    per = pd.DatetimeIndex(frame.index).to_period("M") if not isinstance(frame.index, pd.PeriodIndex) \
        else frame.index
    return frame[np.asarray(per > per.max() - int(n))]


# ═══════════════════════════════════════════════════════════════════════════════
# FORWARD SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

def horizon_months(peak_month: int) -> list:
    """[10, 11, ..., peak_month] as a sequence of calendar months.

    The forecast horizon runs from October to a cluster's historical
    peak-of-record month. Hoisted here 2026-08-28 (T-14 D5, S.9) from two
    byte-identical copies in `11_forecasting_thresholds.py` and
    `11b_spatial_thresholds.py`.

    Two copies of a function that visibly disagree are recoverable; a shared
    helper that later diverges silently is not, which is the risk this project
    weighed before hoisting. It is taken because the horizon defines what
    P_flood integrates over, and two definitions of that would be a numerical
    difference between the per-well and the spatial tool with nothing to catch
    it.
    """
    months, m = [], 10
    for _ in range(12):
        months.append(m)
        if m == peak_month:
            return months
        m = (m % 12) + 1
    return months


def simulate_ssm(h0, P, PET, b1, b2, b3,
                 drainage_datum=DRAINAGE_DATUM, alpha=0.0):
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
        dh = alpha + b1 * P[t] - b2 * PET[t] - b3 * h_disp
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
        Target head (m), positive up. 0 = ground surface (the P_flood target);
        the Curreli winter levels are -config.SD15b_WINTER (above ground) and
        -config.SD16_WINTER (below ground).
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
    adjustment, not a steady-state prediction. It is a RATE (m/month), not a
    level: a shift held year after year accumulates through the drainage term,
    and the level it reaches is sustained_monthly_response() (D-216). The β₃ drainage term
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


def scenario_delta_series(b3, forcing_change, d0=0.0):
    """Level difference between a perturbed and a baseline SSM run (D-216).

    Both runs obey h(t) = (1 - β₃)·h(t-1) + β₁·P(t) − β₂·PET(t) − β₃·D [+ α], so
    their difference d = h_scen − h_base obeys

        d(t) = (1 − β₃)·d(t−1) + Δf(t),   Δf(t) = β₁·ΔP(t) − β₂·ΔPET(t)

    in which the intercept α (Model B) and the drainage datum D (Model A) cancel
    exactly. ``forcing_change`` is the monthly Δf series (m/month); ``d0`` the
    difference before the first month (0 = both runs start from the same state;
    pass the sustained value to start from a climatology already in force).
    Returns the level difference (m) after each month.
    """
    f = np.asarray(forcing_change, dtype=float)
    out = np.empty(len(f))
    d = float(d0)
    r = 1.0 - float(b3)
    for t in range(len(f)):
        d = r * d + f[t]
        out[t] = d
    return out


def sustained_monthly_response(b3, forcing_change_12):
    """Periodic steady state of scenario_delta_series() for a forcing change that
    repeats every year: the level difference (m) in each calendar month, index
    0 = January, once the shifted climatology has been in force long enough for
    the memory to forget the start (D-216). Requires 0 < β₃ < 2."""
    f = np.asarray(forcing_change_12, dtype=float)
    if f.shape != (12,):
        raise ValueError("forcing_change_12 must have 12 monthly values")
    r = 1.0 - float(b3)
    if not abs(r) < 1.0:
        raise ValueError(f"beta_3 = {b3!r} has no steady state (needs 0 < beta_3 < 2)")
    k = np.arange(12)
    return np.array([np.sum(r ** k * f[(m - k) % 12]) for m in range(12)]) / (1.0 - r ** 12)


def periodic_steady_state_ddp(b1, b2, b3, kappa, P12, PET12, drainage_datum, b2_mult12=None,
                              rain_mult12=None, tol=1e-12, max_years=20000, h0=0.0):
    """1.11.0 (D-280): the periodic steady state (m, ground-referenced, index 0 = January) of the
    depth-dependent SSM run on a repeating 12-month climatology:

        h(t) = h(t-1) + β₁·r(m)·P(m) − β₂·m₂(m)·exp(−κ·max(−h(t-1), 0))·PET(m) − β₃·(z₀ + h(t-1))

    with r(m) the rainfall multiplier and m₂(m) the PET multiplier. Iterated year by year until no
    month moves by more than `tol` between successive years. Returns (levels_12, years_used); raises
    if it does not converge, so a well never returns a silent NaN. At κ = 0 the model is linear and
    the difference of two steady states equals sustained_monthly_response() exactly."""
    P12, PET12 = np.asarray(P12, dtype=float), np.asarray(PET12, dtype=float)
    m2 = np.ones(12) if b2_mult12 is None else np.asarray(b2_mult12, dtype=float)
    rm = np.ones(12) if rain_mult12 is None else np.asarray(rain_mult12, dtype=float)
    b1, b2, b3, kap, z0 = float(b1), float(b2), float(b3), float(kappa), float(drainage_datum)
    h = float(h0)
    prev = None
    for year in range(1, max_years + 1):
        cur = np.empty(12)
        for m in range(12):
            d = max(-h, 0.0)
            h = h + b1 * rm[m] * P12[m] - b2 * m2[m] * np.exp(-kap * d) * PET12[m] - b3 * (z0 + h)
            cur[m] = h
        if prev is not None and np.max(np.abs(cur - prev)) < tol:
            return cur, year
        prev = cur
    raise RuntimeError(f"depth-dependent steady state did not converge in {max_years} years "
                       f"(b3={b3:g}, kappa={kap:g})")


def sustained_monthly_response_ddp(b1, b2, b3, kappa, P12, PET12, sP12, sPET12, drainage_datum,
                                   interception=0.0, interception_scen=None, b2_mult12=None):
    """1.11.0 (D-280): the sustained level response (m, index 0 = January) of the depth-dependent
    SSM to a scaled climatology: the scenario's periodic steady state less the baseline's. The
    forcing follows climate_forcing_change_12() term for term — rainfall scaled by
    sP·(1 + I − I_s), PET by m₂·sPET — so at κ = 0 the result equals
    sustained_monthly_response(b3, climate_forcing_change_12(...)) to rounding. Returns
    (response_12, years_used) with years_used the larger of the two runs."""
    sP12, sPET12 = np.asarray(sP12, dtype=float), np.asarray(sPET12, dtype=float)
    i0 = float(interception)
    i_s = i0 if interception_scen is None else float(interception_scen)
    m2 = np.ones(12) if b2_mult12 is None else np.asarray(b2_mult12, dtype=float)
    base, y0 = periodic_steady_state_ddp(b1, b2, b3, kappa, P12, PET12, drainage_datum)
    scen, y1 = periodic_steady_state_ddp(b1, b2, b3, kappa, P12, PET12, drainage_datum,
                                         b2_mult12=m2 * sPET12, rain_mult12=sP12 * (1.0 + i0 - i_s),
                                         h0=float(base[-1]))
    return scen - base, max(y0, y1)


def climate_forcing_change_12(b1, b2, P12, PET12, sP12, sPET12, interception=0.0,
                              interception_scen=None, b2_mult12=None):
    """Monthly forcing change Δf (m/month, index 0 = January) when the 12-month
    climatology P12 / PET12 is scaled by sP12 / sPET12 and, at a forest well, the
    canopy's interception moves from `interception` (I, the baseline canopy) to
    `interception_scen` (I_s; default I) and its draw is scaled by `b2_mult12`:

        Δf(m) = β₁·P(m)·[(sP(m) − 1) + sP(m)·(I − I_s)] − β₂·PET(m)·[m₂(m)·sPET(m) − 1]

    β₁ and β₂ were fitted on gross rainfall and above-canopy PET, so the canopy is
    already inside them: a rainfall CHANGE passes through β₁ unreduced, and only a
    change OF canopy adds β₁·sP·P·(I − I_s), the recharge gain of case (b) in
    INTERCEPTION_TREATMENT.md (D-022, D-238). Before 1.9.0 the climate change was
    multiplied by (1 − I) at forest wells, subtracting the canopy a second time.
    With I = I_s and no multiplier this is β₁·P·(sP − 1) − β₂·PET·(sPET − 1) at
    every well, bit-identical to the old expression wherever I was 0.

    The one-month RATE of D-216's level response; Scripts 19 and 26b share it."""
    P12, PET12 = np.asarray(P12, dtype=float), np.asarray(PET12, dtype=float)
    sP12, sPET12 = np.asarray(sP12, dtype=float), np.asarray(sPET12, dtype=float)
    if interception_scen is None and b2_mult12 is None:
        return (float(b1) * P12 * (sP12 - 1.0)
                - float(b2) * PET12 * (sPET12 - 1.0))
    i0 = float(interception)
    i_s = i0 if interception_scen is None else float(interception_scen)
    m2 = np.ones(12) if b2_mult12 is None else np.asarray(b2_mult12, dtype=float)
    return (float(b1) * P12 * ((sP12 - 1.0) + sP12 * (i0 - i_s))
            - float(b2) * PET12 * (m2 * sPET12 - 1.0))


def response_identified(beta_3, pvalue_beta_3, n_months, n_params):
    """Script 48's identifiability rule on a fitted drainage coefficient: the
    e-fold time −1/ln(1 − β₃) no longer than PASTAS_IDENT_EFOLD_WINDOW_FRAC of the
    fitted months, and the relative standard error of β₃ (recovered from its
    two-sided p-value on n_months − n_params degrees of freedom) no larger than
    PASTAS_IDENT_MAX_REL_SE. Returns (identified, efold_months, rel_se)."""
    from scipy import stats as _st                            # noqa: PLC0415
    from utils.config import (PASTAS_IDENT_EFOLD_WINDOW_FRAC,  # noqa: PLC0415
                              PASTAS_IDENT_MAX_REL_SE)
    b = float(beta_3)
    if not (0.0 < b < 1.0) or not np.isfinite(pvalue_beta_3):
        return False, np.nan, np.nan
    efold = -1.0 / np.log(1.0 - b)
    dof = max(int(n_months) - int(n_params), 1)
    p = min(max(float(pvalue_beta_3), 1e-300), 1.0)
    t = _st.t.isf(p / 2.0, dof)
    rel_se = 1.0 / t if t > 0 else np.inf
    ok = (efold <= PASTAS_IDENT_EFOLD_WINDOW_FRAC * n_months) and (rel_se <= PASTAS_IDENT_MAX_REL_SE)
    return bool(ok), float(efold), float(rel_se)


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
