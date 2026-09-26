"""
utils/cluster_series.py
=======================
Composition-robust cluster series (D-202).

A cluster "mean" taken over whichever member wells report in a month or a
window moves whenever a well joins or leaves the network. Before 2010 the
reference network is a few early wells per cluster (C5's 2006/07 winter was
NW9 alone), so annual extremes, their trends and rolling-window metrics built
from the plain mean inherit the network's installation history.

The fix is a two-way fixed-effects decomposition of the member panel,

    x(w, t) = a_w + g_t,

fitted by alternating means over the observed cells (an unbalanced panel:
each time step uses the wells present). The cluster series is g_t placed at
the mean level of ALL members, g_t + mean(a_w), so a late-joining well moves
nothing. Where every member reports, it equals the plain mean.

Used by Script 14 (monthly depths -> extremes, trends, exceedance) and
Script 26 (per-well MSL5 and rolling-minimum windows -> cluster trajectories).
D-004 keeps the plain mean for the SSM coefficients, where membership growth
averages out.
"""
from __future__ import annotations

import pandas as pd

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-26. D-202: fixed_effect_series and
#   fixed_effect_centroids lifted from Script 14 1.8.0 so Scripts 14 and 26 share one
#   implementation. No value change for Script 14.

FE_MAX_ITER = 500
FE_TOL = 1e-10


def fixed_effect_series(panel: pd.DataFrame,
                        max_iter: int = FE_MAX_ITER,
                        tol: float = FE_TOL) -> pd.Series:
    """Cluster series from a time x well panel (NaN where a well is absent).

    Returns g_t + mean(a_w) on the panel's index, NaN where no well reports.
    """
    X = panel.dropna(how="all")
    X = X.loc[:, X.notna().any()]
    if X.shape[1] == 0:
        return pd.Series(dtype=float, index=panel.index)
    a = pd.Series(0.0, index=X.columns)
    for _ in range(max_iter):
        g = X.sub(a, axis=1).mean(axis=1)
        a_new = X.sub(g, axis=0).mean(axis=0)
        converged = (a_new - a).abs().max() < tol
        a = a_new
        if converged:
            break
    g = X.sub(a, axis=1).mean(axis=1)
    return (g + a.mean()).reindex(panel.index)


def cluster_membership(cluster_stats: pd.DataFrame, columns) -> dict:
    """{cluster id (int): [normalised member names present in `columns`]} from
    02_cluster_stats (Match_ID, Cluster)."""
    cols = set(columns)
    k = cluster_stats["Match_ID"].astype(str).str.strip().str.lower().str.replace(" ", "")
    cid = pd.to_numeric(cluster_stats["Cluster"], errors="coerce")
    out = {}
    for c, name in zip(cid, k):
        if pd.notna(c) and name in cols:
            out.setdefault(int(c), []).append(name)
    return out


def fixed_effect_centroids(wells: pd.DataFrame, cluster_stats: pd.DataFrame) -> pd.DataFrame:
    """Monthly fixed-effects cluster series, columns 'C{n}', from a wells frame
    (DatetimeIndex x well) and 02_cluster_stats. Well names are normalised
    (lower case, no spaces)."""
    w = wells.copy()
    w.columns = w.columns.astype(str).str.strip().str.lower().str.replace(" ", "")
    out = {f"C{c}": fixed_effect_series(w[members])
           for c, members in sorted(cluster_membership(cluster_stats, w.columns).items())}
    df = pd.DataFrame(out)
    df.index.name = "Date"
    return df
