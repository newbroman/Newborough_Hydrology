"""
hindcast_utils.py — the CCW 1989-96 hindcast, shared (D-222).

One implementation of the out-of-sample hindcast against the CCW 1989-96 dipwell
record, used by Script 39 (the published hindcast, coefficients from the
comparison window) and Script 50 (the record-length experiment, coefficients
fitted on records of many lengths and placements). Before 2026-10-01 these
functions lived in Script 39 alone; they moved here unchanged so that Script 50
does not copy them. Script 39's outputs are identical before and after the move.

The one addition is the `drainage_datum` argument of equilibrium_depth() and
hindcast_well(), defaulting to config.DRAINAGE_DATUM (Script 39's behaviour). A
free-intercept fit (Model B) is Model A at the datum DRAINAGE_DATUM - alpha/beta_3,
and is run at that datum.

What the hindcast is, and what it assumes, is set out in Script 39's docstring.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-01 (D-222). First issue: load_ccw, observed_series,
#   hindcast_well, equilibrium_depth and usable_codes moved from Script 39 1.5.0 unchanged, with a
#   drainage_datum argument (default DRAINAGE_DATUM) on the two that use the datum.

import numpy as np
import pandas as pd

from utils import config, paths
from utils.model_utils import simulate_ssm

BETA_COLS = ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage")


def load_ccw():
    """The CCW historic depths (month-bucketed) and the code map."""
    obs = pd.read_csv(paths.CCW_DEPTHS)
    obs["month"] = pd.PeriodIndex(obs["month"], freq="M").to_timestamp()
    cmap = pd.read_csv(paths.CCW_CODE_MAP)
    cmap["well"] = cmap["well"].fillna("").astype(str).str.lower().str.strip()
    return obs, cmap


def observed_series(obs: pd.DataFrame, code: str, offset_m: float):
    """Monthly observed depth for one code, on the modern ground datum.

    Returns (series, n_censored). Censored readings are dropped from the series
    and counted, because a reading held at the pipe base is a lower bound rather
    than a level and would drag any metric toward the model.
    """
    g = obs[obs["code"] == code].sort_values("month")
    n_cens = int(g["censored_at_pipe_base"].sum())
    g = g[~g["censored_at_pipe_base"]]
    s = pd.Series(g["depth_m_bg"].values, index=g["month"].values, name=code)
    if np.isfinite(offset_m):
        s = s + offset_m
    return s, n_cens


def hindcast_well(cl: pd.DataFrame, betas: tuple, h0: float,
                  first_month, last_month, beta1_scale: float = 1.0,
                  drainage_datum: float = config.DRAINAGE_DATUM):
    """Simulate from the start of the climate record and return the window.

    The simulation runs from the first month of the committed climate record so
    that the initial condition is forgotten long before the comparison window
    opens; `spinup_months` is returned so the claim can be checked rather than
    asserted.
    """
    b1, b2, b3 = betas
    sub = cl.loc[:last_month]
    h = simulate_ssm(h0, sub["P_m"].values, sub["PET"].values,
                     b1 * beta1_scale, b2, b3, drainage_datum=drainage_datum)
    sim = pd.Series(h, index=sub.index, name="predicted_m_bg")
    spinup = int((sim.index < first_month).sum())
    return sim.loc[first_month:last_month], spinup


def equilibrium_depth(betas: tuple, p_mean: float, pet_mean: float,
                      drainage_datum: float = config.DRAINAGE_DATUM) -> float:
    """Steady-state depth implied by the coefficients under mean forcing.

    Setting the monthly change to zero in the SSM recurrence gives
    h* = (b1*P - b2*PET)/b3 - D. Used as the starting value, so the run begins
    near its own attractor rather than at an arbitrary level.
    """
    b1, b2, b3 = betas
    if not np.isfinite(b3) or b3 <= 0:
        return np.nan
    return (b1 * p_mean - b2 * pet_mean) / b3 - drainage_datum


def usable_codes(cmap: pd.DataFrame, md: pd.DataFrame, obs: pd.DataFrame):
    """Codes admissible to the headline: confirmed mapping, and a well with a
    committed coefficient triple. Everything else is reported, never pooled."""
    rows = []
    for r in cmap.itertuples():
        why = ""
        if r.status != "confirmed":
            why = f"mapping {r.status}"
        elif not r.well:
            why = "no well"
        elif r.well not in md.index:
            why = "no committed coefficients"
        elif not all(np.isfinite(md.loc[r.well, c]) for c in BETA_COLS):
            why = "coefficient triple incomplete"
        elif md.loc[r.well, BETA_COLS[2]] <= 0:
            why = "non-positive drainage coefficient"
        n_c = int(obs.loc[obs["code"] == r.code, "censored_at_pipe_base"].sum())
        n_t = int((obs["code"] == r.code).sum())
        if not why and n_t and n_c / n_t > config.CCW_MAX_CENSORED_FRACTION:
            why = f"censored in {n_c} of {n_t} months"
        rows.append(dict(code=r.code, well=r.well, status=r.status,
                         datum_offset_m=r.datum_offset_m,
                         n_months=n_t, n_censored=n_c,
                         admitted=(why == ""), excluded_because=why))
    return pd.DataFrame(rows)
