"""community_bands — community water levels compared WELL BY WELL, never with a cluster mean (D-294).

Why this module exists (Martin, 2026-11-01): the clusters are Ward's groups on SSM coefficient behaviour, not on
water-table depth, so a cluster holds wells at every topographic position. A community level (Curreli et al. 2013,
Table 4; the Dune Managers Handbook v2, Table 2) describes where the water table sits relative to the ground at a
slack. It is therefore compared only with one well's level, for the quantity the level is a mean of (D-190, D-291),
and results are counted per well, optionally grouped by cluster.

A band is the interval between consecutive community levels, wettest first. "Above" the first level means strictly
wetter than it and "below" the last strictly drier; a value exactly on a level otherwise counts in the band that level
bounds from below, so a well ON SD15b or ON SD16 counts as between the two (as Script 26's _hb_band_counts and
msl9_band already count). Levels are in the depth frame of the pipeline: metres relative to ground, negative below.

"""
from __future__ import annotations

import numpy as np
import pandas as pd

from utils import config

__version__ = "1.0.0"  # Hollingham (2026) - 2026-11-01. First version (D-294).

# (name, level in m relative to ground, negative below), wettest first. Values are config's, never typed here.
CURRELI_SUMMER = (("SD15b", -config.SD15b), ("SD16", -config.SD16))
CURRELI_WINTER = (("SD15b", -config.SD15b_WINTER), ("SD16", -config.SD16_WINTER))


def _slug(name: str) -> str:
    return str(name).lower().replace(" ", "_")


def band_names(edges) -> list[str]:
    """Band labels for a set of edges, wettest first: above_<first>, <a>_to_<b>, ..., below_<last>."""
    e = list(edges)
    return ([f"above_{_slug(e[0][0])}"] + [f"{_slug(a)}_to_{_slug(b)}" for (a, _x), (b, _y) in zip(e, e[1:])]
            + [f"below_{_slug(e[-1][0])}"])


def band(value: float, edges) -> str | None:
    """The band a level falls in, or None for a missing value."""
    if value is None or not np.isfinite(value):
        return None
    e = list(edges)
    names = band_names(e)
    if value > e[0][1]:
        return names[0]
    for i in range(1, len(e)):
        if value >= e[i][1]:
            return names[i]
    return names[-1]


def band_counts(values, edges) -> dict:
    """{band: count} over the finite values, every band present (zero when empty), plus 'n'."""
    v = pd.Series(values, dtype=float).dropna()
    out = {b: 0 for b in band_names(edges)}
    for x in v:
        out[band(float(x), edges)] += 1
    out["n"] = int(len(v))
    return out
