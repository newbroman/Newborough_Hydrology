"""
utils/envelope_metric.py — co-temporal per-well amplification coefficient (shared)
==================================================================================

Single source of truth for the co-temporal spring climate-sensitivity coefficient used by
both Script 33 (the published Figure 60a amplification SURFACE) and Script 35 (the per-well
coefficient TABLE + CIs + SSM calibration).

The coefficient is each well's dry-to-wet spring swing divided by a reference-core swing
RECOMPUTED over that well's own available extreme years (co-temporal normalisation). This
cancels the common climate signal window-by-window so wells measured on different extreme-year
subsets stay comparable, and removes the coverage artefacts that the naive panel-mean
normalisation produced on the interpolated surface (e.g. the CEH9/CEH39 step, where CEH39
lacks the extreme 2012 spring).

See SPEC_script35_per_well_amplification_metric.md.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from . import config


def spring_year_table(levels, spring_months=None):
    sm = config.MSL_SPRING_MONTHS if spring_months is None else spring_months
    spring = levels[levels.index.month.isin(sm)]
    return spring.groupby(spring.index.year).mean(numeric_only=True)


def reference_core(yr, dry_pool, wet_pool, ref_min_wet):
    """Wells with FULL dry coverage (all dry_pool years) and >= ref_min_wet wet years."""
    ds = yr.reindex(dry_pool); ws = yr.reindex(wet_pool)
    return [c for c in yr.columns
            if ds[c].notna().sum() == len(dry_pool) and ws[c].notna().sum() >= ref_min_wet]


def _ref_swing(yr, core, dyrs, wyrs):
    ds = yr.reindex(dyrs)[core].mean(axis=1).mean()
    ws = yr.reindex(wyrs)[core].mean(axis=1).mean()
    return (ws - ds) * 1000.0


def single_year_sigma(yr, dry_pool):
    """Empirical within-state single-year deviation (mm) from multi-year wells — used to widen
    the CI for singleton (n=1) states where the jackknife alone under-counts uncertainty."""
    ds = yr.reindex(dry_pool); devs = []
    for c in yr.columns:
        s = ds[c].dropna()
        if len(s) >= 2:
            devs.extend(((s - s.mean()) * 1000.0).abs().values)
    return float(np.std(devs)) if devs else 0.0


def coefficients(yr, dry_pool, wet_pool, excluded, ref_min_wet=2, with_ci=False, ci_z=1.645):
    """Per-well co-temporal amplification coefficient.

    Returns a DataFrame: key, dry_m, wet_m, swing_mm, amp_coefficient, n_dry, n_wet, tier,
    dry_2012_present (+ ci_lo, ci_hi, se when with_ci). Wells in `excluded` are dropped;
    any well with >= 1 dry and >= 1 wet pool-year is admitted.
    """
    excluded = set(excluded or [])
    core = reference_core(yr, dry_pool, wet_pool, ref_min_wet)
    sigma_year = single_year_sigma(yr, dry_pool) if with_ci else 0.0
    ds = yr.reindex(dry_pool); ws = yr.reindex(wet_pool)
    rows = []
    for col in yr.columns:
        key = col.lower().strip()
        if key in excluded:
            continue
        dyrs = [y for y in dry_pool if not pd.isna(ds.loc[y, col])]
        wyrs = [y for y in wet_pool if not pd.isna(ws.loc[y, col])]
        if len(dyrs) < 1 or len(wyrs) < 1:
            continue
        dry_m = ds.loc[dyrs, col].mean(); wet_m = ws.loc[wyrs, col].mean()
        swing = (wet_m - dry_m) * 1000.0
        ref = _ref_swing(yr, core, dyrs, wyrs)
        amp = swing / ref
        tier = ("A" if (len(dyrs) >= 2 and len(wyrs) >= 2)
                else ("C" if (len(dyrs) == 1 and len(wyrs) == 1) else "B"))
        row = dict(key=key, dry_m=dry_m, wet_m=wet_m, swing_mm=swing, amp_coefficient=amp,
                   n_dry=len(dyrs), n_wet=len(wyrs), tier=tier, dry_2012_present=(2012 in dyrs))
        if with_ci:
            reps = []
            for y in dyrs:
                if len(dyrs) > 1:
                    dd = [x for x in dyrs if x != y]
                    reps.append(((ws.loc[wyrs, col].mean() - ds.loc[dd, col].mean()) * 1000.0)
                                / _ref_swing(yr, core, dd, wyrs))
            for y in wyrs:
                if len(wyrs) > 1:
                    we = [x for x in wyrs if x != y]
                    reps.append(((ws.loc[we, col].mean() - ds.loc[dyrs, col].mean()) * 1000.0)
                                / _ref_swing(yr, core, dyrs, we))
            n = len(reps)
            se_j = np.sqrt((n - 1) / n * np.sum((np.array(reps) - np.mean(reps)) ** 2)) if n >= 2 else 0.0
            var_s = 0.0
            if len(dyrs) == 1:
                var_s += (sigma_year / abs(ref)) ** 2
            if len(wyrs) == 1:
                var_s += (sigma_year / abs(ref)) ** 2
            se = float(np.sqrt(se_j ** 2 + var_s))
            row.update(se=se, ci_lo=amp - ci_z * se, ci_hi=amp + ci_z * se)
        rows.append(row)
    df = pd.DataFrame(rows)
    df.attrs["reference_core_n"] = len(core)
    df.attrs["sigma_year_mm"] = sigma_year
    return df
