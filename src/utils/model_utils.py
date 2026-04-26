"""
utils/model_utils.py
Shared model evaluation helpers and the intercept audit computation
used by 07_boundary_intercept.py and 08_model_benchmarking.py.

Both the intercept audit and the benchmarking use the displacement
formulation (h_disp = DRAINAGE_DATUM + h_depth) and lag-1 rainfall,
matching Script 03's headline SSM specification.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

from utils.config import DRAINAGE_DATUM

LCSC_DATA_LIMIT = 100

# Lag-1 rainfall: matches Script 03's HEADLINE_LAG = 1.
HEADLINE_LAG = 1


def get_metrics(obs, sim):
    """
    Calculate NSE, RMSE, and bias between observed and simulated series.

    Returns:
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


def compute_intercept_audit(target_well_name, df_clean, df_climate):
    """
    Compute Model A (No Intercept / Strict Mass-Balance) vs
    Model B (Unconstrained / Fitted Intercept) for a single well.

    Uses the displacement formulation (h_disp = DRAINAGE_DATUM + h_depth)
    and lag-1 rainfall, matching Script 03.

    Returns:
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

    # Lag-1 rainfall (matching Script 03 HEADLINE_LAG = 1)
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
