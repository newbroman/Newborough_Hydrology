"""
utils/kriging.py — kriging with an external drift, in numpy and scipy only
==========================================================================

Universal kriging in the variogram form. The drift is a constant plus any number
of external covariates, so ordinary kriging is the case with no covariate and
kriging with an external drift (KED; Desbarats et al. 2002, J. Hydrol. 255,
25–38) is the case with one. Written here, not imported, so the pipeline takes
on no new dependency: freeze_requirements gates the venv. Script 01b (was 49) checks it
against pykrige in a scratch environment (spec NRG_spec_slack_flow_C).

Pieces
  empirical_variogram(xy, r, ...)  binned semivariance of residuals r
  fit_spherical(lags, gam, n)      weighted least squares, nugget/psill/range
  spherical(h, vgm)                the model
  ked(...)                          prediction and kriging standard error at targets
  ols_residuals(z, D)              residuals of z on [1, D], for the variogram

A variogram fit that fails to converge is reported, not hidden: fit_spherical
returns ok=False, and the caller decides the fallback and says so.

__version__ : 1.0.1
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) - 2026-09-27. 1.0.1: docstring names Script 01b (Script 49
#   renamed, D-205 extended); no code change. 1.0.0: New: KED for Script 49 (D-205 pending).

import numpy as np
from scipy.linalg import lu_factor, lu_solve
from scipy.optimize import least_squares
from scipy.spatial.distance import cdist


def ols_residuals(z: np.ndarray, D: np.ndarray | None) -> np.ndarray:
    """Residuals of z on [1, D] (D: n x k covariates, or None for a constant)."""
    X = np.ones((len(z), 1)) if D is None else np.column_stack([np.ones(len(z)), D])
    beta, *_ = np.linalg.lstsq(X, z, rcond=None)
    return z - X @ beta


def empirical_variogram(xy: np.ndarray, r: np.ndarray, n_bins: int, max_lag: float):
    """Binned semivariance: (lag centres, gamma, pair counts), empty bins dropped."""
    d = cdist(xy, xy)
    iu = np.triu_indices(len(r), 1)
    h, g = d[iu], 0.5 * (r[iu[0]] - r[iu[1]]) ** 2
    edges = np.linspace(0.0, max_lag, n_bins + 1)
    idx = np.digitize(h, edges) - 1
    lag, gam, cnt = [], [], []
    for b in range(n_bins):
        m = idx == b
        if m.sum():
            lag.append(h[m].mean()); gam.append(g[m].mean()); cnt.append(int(m.sum()))
    return np.array(lag), np.array(gam), np.array(cnt)


def spherical(h, vgm: dict):
    """Spherical model; gamma(0) = 0 exactly (the nugget is a jump at h > 0)."""
    h = np.asarray(h, float)
    a, c0, c = vgm["range"], vgm["nugget"], vgm["psill"]
    s = np.where(h < a, 1.5 * h / a - 0.5 * (h / a) ** 3, 1.0)
    out = c0 + c * s
    return np.where(h == 0.0, 0.0, out)


def fit_spherical(lag, gam, cnt, max_lag: float) -> dict:
    """WLS fit (weights = pair counts / gamma^2, Cressie 1985). Returns the model
    dict with ok=False when the optimiser does not converge or the bins are too few."""
    if len(lag) < 4:
        return {"nugget": 0.0, "psill": float(np.var(gam)) or 1e-6, "range": max_lag, "ok": False,
                "why": f"{len(lag)} non-empty bins"}
    w = np.sqrt(cnt) / np.maximum(gam, 1e-9)

    def resid(p):
        return w * (spherical(lag, {"nugget": p[0], "psill": p[1], "range": p[2]}) - gam)

    g_max = float(gam.max())
    p0 = [0.1 * g_max, 0.9 * g_max, 0.5 * max_lag]
    lo, hi = [0.0, 1e-9, 0.02 * max_lag], [g_max * 2, g_max * 4, 3 * max_lag]
    try:
        r = least_squares(resid, p0, bounds=(lo, hi))
        ok = bool(r.success)
        p = r.x
        why = "" if ok else r.message
    except Exception as e:  # noqa: BLE001 - reported to the caller, never swallowed
        ok, p, why = False, p0, str(e)
    return {"nugget": float(p[0]), "psill": float(p[1]), "range": float(p[2]), "ok": ok, "why": why}


def ked(xy: np.ndarray, z: np.ndarray, D: np.ndarray | None, txy: np.ndarray,
        tD: np.ndarray | None, vgm: dict, chunk: int = 5000):
    """Universal kriging (constant + external drift D) at targets txy.

    Returns (prediction, kriging standard error). D / tD: n x k and m x k covariates
    at the data and target points, or None for ordinary kriging.
    """
    n = len(z)
    F = np.ones((n, 1)) if D is None else np.column_stack([np.ones(n), D])
    p = F.shape[1]
    A = np.zeros((n + p, n + p))
    A[:n, :n] = spherical(cdist(xy, xy), vgm)
    A[:n, n:] = F
    A[n:, :n] = F.T
    lu = lu_factor(A)
    zp = np.concatenate([z, np.zeros(p)])
    pred = np.empty(len(txy)); se = np.empty(len(txy))
    for s in range(0, len(txy), chunk):
        t = txy[s:s + chunk]
        Ft = np.ones((len(t), 1)) if tD is None else np.column_stack([np.ones(len(t)), tD[s:s + chunk]])
        b = np.vstack([spherical(cdist(xy, t), vgm), Ft.T])
        w = lu_solve(lu, b)
        pred[s:s + chunk] = zp @ w
        se[s:s + chunk] = np.sqrt(np.maximum((w * b).sum(0), 0.0))
    return pred, se
