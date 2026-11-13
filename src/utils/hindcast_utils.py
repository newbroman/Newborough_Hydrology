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

compare_offset_censored() is Ranwell's comparison (Script 44, D-145), shared with Script 50's E9 (D-229):
Ranwell's sites are not at the modern wells, so the mean offset is removed, and a flooded slack reads at
the ground, so readings there are censored and the model is capped at the ground.
"""
from __future__ import annotations

__version__ = "1.3.0"  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b). Model B can be run directly: alpha
#   (default 0.0) on hindcast_well() and equilibrium_depth(), and an optional datum_col on usable_codes() that leaves
#   out a well whose Model B implied datum (03 implied_datum_m = DRAINAGE_DATUM - alpha/beta_3) is not below ground.
#   Every default is unchanged, so no existing caller changes behaviour.
# 1.2.0  # Hollingham (2026) - 2026-10-29 (T-130, D-290). quantile_map() moved here from Script 47 1.9.1
#   unchanged (its tail fraction now an argument, default config.QMAP_TAIL_FRACTION), so Script 47's film calibration
#   and Script 50's E18 transfer test use one map.
# 1.1.0  # Hollingham (2026) - 2026-10-02 (D-229). Adds compare_offset_censored(), Script 44
#   1.8.0's compare() moved here unchanged (offset fitted on the uncensored months, model capped at the
#   ground, NSE after offset) so that Script 50's E9 scores Ranwell exactly as Script 44 does.
# 1.0.0  # Hollingham (2026) - 2026-10-01 (D-222). First issue: load_ccw, observed_series,
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
                  drainage_datum: float = config.DRAINAGE_DATUM, alpha: float = 0.0):
    """Simulate from the start of the climate record and return the window.

    Model B (D-332) is run either at its implied datum (Script 03's implied_datum_m) with alpha=0,
    or at DRAINAGE_DATUM with its fitted alpha; the two are the same recurrence. Never both.

    The simulation runs from the first month of the committed climate record so
    that the initial condition is forgotten long before the comparison window
    opens; `spinup_months` is returned so the claim can be checked rather than
    asserted.
    """
    b1, b2, b3 = betas
    sub = cl.loc[:last_month]
    h = simulate_ssm(h0, sub["P_m"].values, sub["PET"].values,
                     b1 * beta1_scale, b2, b3, drainage_datum=drainage_datum, alpha=alpha)
    sim = pd.Series(h, index=sub.index, name="predicted_m_bg")
    spinup = int((sim.index < first_month).sum())
    return sim.loc[first_month:last_month], spinup


def equilibrium_depth(betas: tuple, p_mean: float, pet_mean: float,
                      drainage_datum: float = config.DRAINAGE_DATUM, alpha: float = 0.0) -> float:
    """Steady-state depth implied by the coefficients under mean forcing.

    Setting the monthly change to zero in the SSM recurrence gives
    h* = (b1*P - b2*PET + alpha)/b3 - D. Used as the starting value, so the run begins
    near its own attractor rather than at an arbitrary level. alpha=0 is Model A, or
    Model B at its implied datum (1.3.0).
    """
    b1, b2, b3 = betas
    if not np.isfinite(b3) or b3 <= 0:
        return np.nan
    return (b1 * p_mean - b2 * pet_mean + alpha) / b3 - drainage_datum


def usable_codes(cmap: pd.DataFrame, md: pd.DataFrame, obs: pd.DataFrame,
                 datum_col: str | None = None):
    """Codes admissible to the headline: confirmed mapping, and a well with a
    committed coefficient triple. Everything else is reported, never pooled.

    datum_col (1.3.0, D-332): the column of md holding the datum the triple runs at
    (Script 03's implied_datum_m for Model B). Given, a well whose datum is not below
    ground (not finite or <= 0) has no Model B and is left out, with the reason. None
    (the default) is the behaviour before 1.3.0."""
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
        elif datum_col is not None and not (np.isfinite(float(md.loc[r.well, datum_col]))
                                            and float(md.loc[r.well, datum_col]) > 0):
            why = f"Model B not defined (implied datum {float(md.loc[r.well, datum_col]):+.2f} m, not below ground)"
        n_c = int(obs.loc[obs["code"] == r.code, "censored_at_pipe_base"].sum())
        n_t = int((obs["code"] == r.code).sum())
        if not why and n_t and n_c / n_t > config.CCW_MAX_CENSORED_FRACTION:
            why = f"censored in {n_c} of {n_t} months"
        rows.append(dict(code=r.code, well=r.well, status=r.status,
                         datum_offset_m=r.datum_offset_m,
                         n_months=n_t, n_censored=n_c,
                         admitted=(why == ""), excluded_because=why))
    return pd.DataFrame(rows)


def compare_offset_censored(obs_month: pd.Series, model_mid: pd.Series, ground_m_od: float):
    """obs monthly means (m OD, PeriodIndex) vs modelled mid-month level (m OD,
    PeriodIndex) over their common months.

    Ranwell's pipe reads the free water surface, so a flooded slack reads at
    the ground: the observation is CENSORED at the surface. The offset is
    therefore fitted on the months that stand at least RANWELL_SURFACE_CENSOR_M
    below the ground, and the offset model is then capped at the ground before
    the metrics — the same instrument-matching cap the 2026-08-22 seasonal-range
    comparison applied to the modern network. Returns n, n censored, offset, r,
    NSE after offset (capped), ranges and the month of the 1951 minimum.
    """
    common = obs_month.index.intersection(model_mid.index)
    o = obs_month.loc[common].astype(float)
    p = model_mid.loc[common].astype(float)
    if len(common) < 3:
        return dict(n=len(common), n_at_surface=0, offset_m=np.nan, r=np.nan, nse_after_offset=np.nan,
                    range_obs_m=np.nan, range_model_m=np.nan, min_month_obs="", min_month_model="")
    free = o <= ground_m_od - config.RANWELL_SURFACE_CENSOR_M
    off = float((o[free] - p[free]).mean()) if free.sum() >= 3 else float((o - p).mean())
    pa = np.minimum(p + off, ground_m_od)
    nse = 1 - float(((o - pa) ** 2).sum() / ((o - o.mean()) ** 2).sum())
    r = float(np.corrcoef(o, pa)[0, 1])
    o51 = o[o.index.year == 1951]
    p51 = p[p.index.year == 1951]
    return dict(n=int(len(common)), n_at_surface=int((~free).sum()), offset_m=off, r=r,
                nse_after_offset=nse,
                range_obs_m=float(o.max() - o.min()), range_model_m=float(pa.max() - pa.min()),
                min_month_obs=str(o51.idxmin()) if len(o51) else "",
                min_month_model=str(p51.idxmin()) if len(p51) else "")


def quantile_map(model, observed, tail_fraction: float | None = None):
    """f(x): a free run's level mapped onto an observed distribution (Script 47's
    calibration, moved here at 1.2.0 unchanged).

    Ranks are kept, so the ORDER of the run is the model's; the mean bias goes; and
    beyond either end of the fitted range the map continues on the outer
    `tail_fraction` of the distribution's own slope rather than flattening.
    Returns (f, sorted model, sorted observed).
    """
    tf = config.QMAP_TAIL_FRACTION if tail_fraction is None else tail_fraction
    m, o = np.sort(np.asarray(model, float)), np.sort(np.asarray(observed, float))
    k = max(5, int(len(m) * tf))
    slo, shi = np.polyfit(m[:k], o[:k], 1)[0], np.polyfit(m[-k:], o[-k:], 1)[0]

    def f(x):
        x = np.asarray(x, float)
        q = np.interp(x, m, o)
        lo, hi = x < m[0], x > m[-1]
        q[lo] = o[0] + slo * (x[lo] - m[0])
        q[hi] = o[-1] + shi * (x[hi] - m[-1])
        return q
    return f, m, o
