r"""

====================================================================================
10e — SSM COEFFICIENT DECOMPOSITION
====================================================================================
Purpose
-------
Mechanistic-direction diagnostic for the clearfell effect.  For each
well, fits the canonical SSM separately on the pre- and post-felling
eras and reports how each coefficient (β₁ recharge, β₂ ET-draw,
β₃ drainage) shifted.  The output characterises *which SSM pathway*
moved at each tier after felling, as a direction-and-pattern result.

Method
------
1. For each well in the 17-well network, fit the canonical no-intercept
   SSM (contemporaneous rainfall, displacement formulation — Model A,
   as used by Script 03 and the headline analysis) separately for the
   Before and After eras.  "Before" is the record-length-balanced
   pre-felling window (PRE_FELL_START → CLEARFELL_DATE) with a
   scraping dummy for the April 2015 event.  "After" covers
   CLEARFELL_DATE → end of record.
2. Compute per-well Δβ₁, Δβ₂, Δβ₃ (After − Before).
3. Report Δβ per well and per tier — sign and magnitude of the
   coefficient shift.  This is a qualitative mechanistic diagnostic:
   it answers "which pathway shifted, and in which direction".

Scope — what this script does NOT do
-------------------------------------
This script does NOT attempt to predict or reconstruct the observed
BACI step from 10a, and does NOT produce a predicted-vs-observed
comparison.  That comparison was removed in v1.4.0.  The reason: the
per-era per-well SSM fit and the 10a ANCOVA BACI step are estimates of
different quantities.  The 10a step is a *control-differenced centroid*
coefficient (felled-minus-control), with regional climate forcing
removed by construction; a per-era per-well β-projection has no control
subtraction and is on a different projection basis.  A Δβ·climate
projection therefore cannot be reconciled term-by-term against the 10a
step, and earlier versions that attempted this could only close the
arithmetic by absorbing the gap into an intercept shift Δα of
unidentified physical content.  See the v1.4.0 changelog entry and
Editorial Q3 / Q24 in CHAPTER_FLAGS_TO_REVIEW.md (Q3 closed by this
change).  The clearfell magnitude result is, and remains, the 10a
ANCOVA BACI step; 10e is a complementary mechanistic diagnostic, not a
second estimator of that magnitude.

Note on the model form
----------------------
The era fits use the canonical no-intercept SSM (`fit_ssm()` with the
default `intercept=False`), consistent with Script 03 and Methods
Supplement S.3.  Versions 1.0.0–1.3.0 fitted the intercept-bearing
Model B; the intercept existed only to serve the predicted-vs-observed
comparison and is not needed once that comparison is removed.

Outputs
-------
CSV:
  10e_01_coefficient_shifts.csv    — per-well before/after coefficients
                                     and Δβ (consumed by Scripts 19/21
                                     via clearfell_common for the β₂
                                     forestry multiplier)
  10e_report_numbers.csv           — all citable values

Figures:
  10e_03_coefficient_shifts.png    — before/after β by well, coloured
                                     by tier

References
----------
Hollingham (2026), §4.6.  Part of the Script 10 clearfell analysis suite.
====================================================================================
"""

__version__ = "1.14.0"  # Hollingham (2026) - 2026-10-04 (T-97, D-239). Two additions, no existing value moves:
#   (1) B2_multiplier_*_impact - the felled well's measured beta_2 change net of the Climate controls, which the
#   forestry scenarios of Scripts 19 and 21 now use (clearfell_common.load_clearfell_impact_b2_multiplier);
#   (2) the shielding test, shielding_seasonal_b2(): per well in the Impact, Edge and Climate-control tiers and
#   per era, the draw coefficient split into canopy-on (config.CANOPY_ON_MONTHS) and canopy-off months with beta_3
#   fixed at the well's full-record value; 10e_04_shielding_seasonal_b2.csv and the shield_* keys.
# 1.13.0  # Hollingham (2026) - 2026-09-29. T-96: 10e_report_numbers carries
#   CoeffShift_Network_n_wells (the 17-well count, Note-only before; report9 Section 4.6.4)
#   and CoeffShift_Forest Ctrl_pine_mean_db2, the Forest Ctrl mean Δβ₂ over the wells outside
#   the broadleaf restock block (dist_broadleaf_restock_m > 0 in 01_locations.csv; report10
#   Section 5.6.2). Reads 01_locations.csv (Script 01) for that flag. No other output moves.
# 1.12.0  # Hollingham (2026) - 2026-09-28. Panel (d) prints beside each bar the p
#   of that tier-mean shift against zero (two-sided z-test on the per-well fit SEs, tier_shift_p),
#   and 10e_report_numbers carries them as CoeffShift_<tier>_mean_d<b>_p (Martin, proofread:
#   "if β3 is noise in panel d then maybe it needs p figures"). No other output moves.
# 1.11.0  # Hollingham (2026) - 2026-09-28. Figure 10e_03 panel (d) adds the
#   per-tier Δβ₃ beside Δβ₁ and Δβ₂, all as % of the before value (Martin, proofread: "β₃ is at
#   the wrong scale, perhaps panel d should be % change"). Display only; no CSV moves.
# 1.10.0  # Hollingham (2026) - 2026-09-28. T-91: 10e_report_numbers also carries the
#   β₂ scenario multipliers (clearfell, thinning) and the per-tier b2_after/b2_before ratios they
#   are built from (Edge, Climate Ctrl, …), which the Methods Supplement quotes.
# 1.9.0  # Hollingham (2026) - 2026-09-28. T-91: emit Coastal Ctrl
#   tier mean coefficient shifts (previously the only tier missing an aggregate
#   row), plus network-wide (17-well BACI network, excl. Far-field Ctrl) mean
#   b1_before/b1_after/db1 and per-tier/network mean-of-per-well %-change in b1,
#   so the report9/report10 Section 4.6.6/5.5.1 narrative values bind to a
#   citation row. No analysis change.
# v1.8.0  # Hollingham (2026) - 2026-09-11.
#   UNSILENCED (D-155): the blanket warnings.filterwarnings('ignore') is
#   removed. It hid every DeprecationWarning and RuntimeWarning this script
#   raised, which is the class of signal that would have flagged the fiona
#   1.10 KML change and the pyogrio/fiona engine split before either broke a
#   run. Python's default shows each unique warning once per location.
# v1.7.0  # Hollingham (2026) — 2026-08-29. CLEARFELL_DATE rename (T-17).
#   No value changes; verified by re-run against the 2026-08-29 pipeline outputs.
# v1.6.0  # Hollingham (2026) — 2026-05-31
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)

from utils.clearfell_common import (
    load_clearfell_data, apply_ceh34_hindcast, ALL_NETWORK_WELLS,
    CLEARFELL_DATE, SCRAPING_DATE, PRE_FELL_START, TIER_COLOURS,
    ReportNumbers, print_network_summary, get_tier,
)
from utils.paths import make_all_dirs, DIR_10, INT_LOCATIONS, OUT_10E_SHIELDING
from utils.config import CANOPY_ON_MONTHS
from utils.model_utils import build_ssm_frame, fit_ssm
from utils.render_utils import render_figure
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

def tier_shift_p(td: pd.DataFrame, coeff: str) -> float:
    """Two-sided p of a tier's mean coefficient shift against zero (1.12.0).

    The before and after fits are independent windows, so each well's shift has
    variance SE_before^2 + SE_after^2; the tier mean's SE is the root of their sum
    over n. A z-test, since the per-well SEs come from fits of 60+ months each."""
    from scipy.stats import norm
    n = len(td)
    se = np.sqrt((td[f'{coeff}_SE_before'] ** 2 + td[f'{coeff}_SE_after'] ** 2).sum()) / n
    if not np.isfinite(se) or se <= 0:
        return np.nan
    return float(2.0 * norm.sf(abs(td[f'd{coeff}'].mean() / se)))


def shielding_seasonal_b2(wells, climate):
    """1.14.0 (T-97, D-239): canopy-on and canopy-off draw before and after the 2017 felling.

    Per well of the Impact, Edge and Climate-control tiers, beta_3 is fixed at the well's full-record
    Model A value (so the split cannot trade against drainage), and per era

        Δh + β₃·h_disp_prev = β₁·P − β₂on·PET·[month in CANOPY_ON_MONTHS] − β₂off·PET·[otherwise]
                              (+ the scraping dummy in the Before era, as the main era fits carry)

    is fitted by least squares with no intercept. Loss of the canopy's shielding predicts β₂on rising
    after felling at the felled well, relative to the climate controls."""
    import numpy as _np
    out = []
    tiers = ("Impact", "Edge", "Climate Ctrl")
    for w in ALL_NETWORK_WELLS:
        if w not in wells.columns or get_tier(w) not in tiers:
            continue
        try:
            fr = build_ssm_frame(wells[w], climate)
            b3 = fit_ssm(pre_built_frame=fr, min_obs=8)["beta_3_drainage"]
        except Exception as e:
            warn(f"shielding fit skipped for {w}: {e}")
            continue
        for era, sub in (("before", fr[(fr.index >= PRE_FELL_START) & (fr.index < CLEARFELL_DATE)]),
                         ("after", fr[fr.index >= CLEARFELL_DATE])):
            if len(sub) < 24:
                continue
            on = sub.index.month.isin(CANOPY_ON_MONTHS).astype(float)
            y = (sub["Delta_h"] + b3 * sub["h_disp_prev"]).values
            cols = [sub["P"].values, -sub["PET"].values * on, -sub["PET"].values * (1 - on)]
            if era == "before":
                cols.append((sub.index >= SCRAPING_DATE).astype(float))
            X = _np.column_stack(cols)
            coef, *_ = _np.linalg.lstsq(X, y, rcond=None)
            out.append({"well": w, "tier": get_tier(w), "era": era, "n": int(len(sub)),
                        "beta_3_fixed": float(b3), "beta_1": float(coef[0]),
                        "beta_2_canopy_on": float(coef[1]), "beta_2_canopy_off": float(coef[2])})
    return pd.DataFrame(out)


def _shielding_report_numbers(rpt, sh):
    """shield_* keys: per tier, the after/before ratio of tier-mean canopy-on and canopy-off draw, and the
    Impact and Edge ratios net of the Climate controls (ratio − Climate Ctrl ratio + 1, as the multipliers)."""
    if sh.empty:
        return
    ratios = {}
    for tier, g in sh.groupby("tier"):
        b, a = g[g["era"] == "before"], g[g["era"] == "after"]
        for part in ("canopy_on", "canopy_off"):
            col = f"beta_2_{part}"
            if len(b) and len(a) and b[col].mean() != 0:
                r = a[col].mean() / b[col].mean()
                ratios[(tier, part)] = r
                rpt.add(f"shield_ratio_{part}", float(r), "", well=tier,
                        note=f"tier-mean {col} after / before the felling, beta_3 fixed (10e_04)")
    for tier in ("Impact", "Edge"):
        for part in ("canopy_on", "canopy_off"):
            if (tier, part) in ratios and ("Climate Ctrl", part) in ratios:
                rpt.add(f"shield_ratio_{part}_net", float(ratios[(tier, part)] - ratios[("Climate Ctrl", part)] + 1.0),
                        "", well=tier, note="ratio − Climate Ctrl ratio + 1 (10e_04)")


def main():
    make_all_dirs()

    # ============================================================================
    # OUTPUT PATHS
    # ============================================================================
    OUT_SHIFTS        = DIR_10 / "10e_01_coefficient_shifts.csv"
    OUT_REPORT        = DIR_10 / "10e_report_numbers.csv"
    OUT_FIG           = DIR_10 / "10e_03_coefficient_shifts.png"

    # ============================================================================
    # MATPLOTLIB DEFAULTS
    # ============================================================================
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
    })


    def format_p(p):
        if pd.isna(p):
            return "NA"
        if p < 0.001:
            return "<0.001"
        return f"{p:.4f}"


    # ============================================================================
    # LOAD DATA
    # ============================================================================
    banner("10e", "SSM COEFFICIENT DECOMPOSITION", version=__version__)

    phase(1, "Loading data")
    wells, _wells_prov, climate, master, well_locations, valid_tiers = load_clearfell_data()
    wells = apply_ceh34_hindcast(wells)
    print_network_summary(valid_tiers)

    # ============================================================================
    # FIT SSM PER WELL, PER ERA
    # ============================================================================
    phase(2, "Fitting per-era SSM coefficients")
    # The "Before" era is the record-length-balanced pre-felling window
    # (PRE_FELL_START → CLEARFELL_DATE) with a scraping dummy.
    # The "After" era runs from felling to end of record.

    COEFF_NAMES = ['beta_1_recharge', 'beta_2_atmospheric_draw', 'beta_3_drainage']

    rows = []
    for w in ALL_NETWORK_WELLS:
        if w not in wells.columns:
            continue

        tier = get_tier(w)

        # Build SSM frame for this well (full record)
        try:
            ssm_frame = build_ssm_frame(wells[w], climate)
        except Exception as e:
            warn(f"SSM frame failed for {w}: {e}")
            continue

        if len(ssm_frame) < 12:
            continue

        # Split into Before (pre-felling) and After (post-felling).
        # PRE_FELL_START enforces record-length balance — every well's Before
        # era starts on the same date.  See clearfell_common.py docstring.
        before = ssm_frame[(ssm_frame.index >= PRE_FELL_START) &
                           (ssm_frame.index < CLEARFELL_DATE)].copy()
        after = ssm_frame[ssm_frame.index >= CLEARFELL_DATE].copy()

        if len(before) < 12 or len(after) < 6:
            skipped(f"{w.upper()}: before={len(before)}, after={len(after)}")
            continue

        # ── Before era: fit with scraping dummy ──────────────────────────
        before['D_scrape'] = (before.index >= SCRAPING_DATE).astype(float)

        try:
            # Canonical no-intercept SSM (Model A), consistent with Script 03
            # and Methods Supplement S.3. The Before-era four-column design
            # matrix carries a scraping_dummy via extra_regressors for the
            # April 2015 event. Column names match 03_master_data.csv.
            # (v1.4.0: intercept=True removed — see module changelog. The
            # intercept-bearing Model B was used only for the now-removed
            # predicted-vs-observed comparison.)
            before_fit = fit_ssm(
                pre_built_frame=before,
                extra_regressors={'scraping_dummy': before['D_scrape'].values},
                min_obs=8,
            )
            if before_fit is None:
                warn(f"Before fit returned None for {w}")
                continue
            b1_before    = before_fit['beta_1_recharge']
            b2_before    = before_fit['beta_2_atmospheric_draw']
            b3_before    = before_fit['beta_3_drainage']
            b1_se_before = before_fit['se_beta_1']
            b2_se_before = before_fit['se_beta_2']
            b3_se_before = before_fit['se_beta_3']
        except Exception as e:
            warn(f"Before fit_ssm failed for {w}: {e}")
            continue

        # ── After era: canonical no-intercept SSM (Model A) ─────────────
        try:
            after_fit = fit_ssm(
                pre_built_frame=after,
                min_obs=6,
            )
            if after_fit is None:
                warn(f"After fit returned None for {w}")
                continue
            b1_after    = after_fit['beta_1_recharge']
            b2_after    = after_fit['beta_2_atmospheric_draw']
            b3_after    = after_fit['beta_3_drainage']
            b1_se_after = after_fit['se_beta_1']
            b2_se_after = after_fit['se_beta_2']
            b3_se_after = after_fit['se_beta_3']
        except Exception as e:
            warn(f"After fit_ssm failed for {w}: {e}")
            continue

        # ── Compute deltas ───────────────────────────────────────────────
        db1 = b1_after - b1_before
        db2 = b2_after - b2_before
        db3 = b3_after - b3_before

        rows.append({
            'Well': w.upper(),
            'Tier': tier,
            'N_before': before_fit['n'],
            'N_after': after_fit['n'],
            'b1_before': round(b1_before, 4),
            'b1_after': round(b1_after, 4),
            'db1': round(db1, 4),
            'b1_SE_before': round(b1_se_before, 4),
            'b1_SE_after': round(b1_se_after, 4),
            'b2_before': round(b2_before, 4),
            'b2_after': round(b2_after, 4),
            'db2': round(db2, 4),
            'b2_SE_before': round(b2_se_before, 4),
            'b2_SE_after': round(b2_se_after, 4),
            'b3_before': round(b3_before, 4),
            'b3_after': round(b3_after, 4),
            'db3': round(db3, 4),
            'b3_SE_before': round(b3_se_before, 4),
            'b3_SE_after': round(b3_se_after, 4),
        })

        print(f"   {w.upper():<8}  Δβ₁={db1:+.3f}  Δβ₂={db2:+.3f}  "
              f"Δβ₃={db3:+.3f}")

    shift_df = pd.DataFrame(rows)
    shift_df.to_csv(OUT_SHIFTS, index=False)
    print(f"\n -> Saved: {OUT_SHIFTS.name} ({len(shift_df)} rows)")

    # Update consolidated pipeline params with β₂ multipliers
    try:
        from utils.clearfell_common import load_clearfell_b2_multiplier
        from utils.pipeline_params import update_b2_multipliers
        cf_mult, thin_mult, _ = load_clearfell_b2_multiplier(verbose=False)
        update_b2_multipliers(cf_mult, thin_mult)
    except Exception as e:
        note(f"Pipeline params B2 update skipped: {e}")

    # ============================================================================
    # FIGURE: COEFFICIENT SHIFTS BY TIER
    # ============================================================================
    phase(3, "Generating coefficient shift figure")
    coeffs = [('b1_before', 'b1_after', 'b1_SE_before', 'b1_SE_after', 'β₁  (recharge)'),
              ('b2_before', 'b2_after', 'b2_SE_before', 'b2_SE_after', 'β₂  (atmospheric draw)'),
              ('b3_before', 'b3_after', 'b3_SE_before', 'b3_SE_after', 'β₃  (drainage)')]

    TIER_ORDER = ['Impact', 'Edge', 'Forest Ctrl', 'Coastal Ctrl', 'Climate Ctrl']

    # order wells top->bottom by tier, then by well within tier
    sdf = shift_df.copy()
    sdf['_t'] = sdf['Tier'].map({t: i for i, t in enumerate(TIER_ORDER)})
    sdf = sdf.dropna(subset=['_t']).sort_values(['_t', 'Well']).reset_index(drop=True)
    n = len(sdf)
    ypos = np.arange(n)[::-1]          # first row at top

    fig = plt.figure(figsize=(8.4, 14.5), dpi=200)
    gs = GridSpec(4, 1, height_ratios=[1, 1, 1, 0.55], hspace=0.18)

    for p, (cb, ca, seb, sea, lab) in enumerate(coeffs):
        ax = fig.add_subplot(gs[p])
        for y, (_, r) in zip(ypos, sdf.iterrows()):
            c = TIER_COLOURS[r['Tier']]
            ax.plot([r[cb], r[ca]], [y, y], color=c, lw=1.4, alpha=0.55, zorder=1)
            ax.errorbar(r[cb], y, xerr=1.96 * r[seb], fmt='none', ecolor=c,
                        elinewidth=0.8, capsize=2, alpha=0.45, zorder=2)
            ax.errorbar(r[ca], y, xerr=1.96 * r[sea], fmt='none', ecolor=c,
                        elinewidth=0.8, capsize=2, alpha=0.45, zorder=2)
            ax.scatter(r[cb], y, s=42, facecolors='white', edgecolors=c,
                       linewidths=1.3, zorder=3)                       # before
            ax.scatter(r[ca], y, s=40, facecolors=c, edgecolors=c,
                       marker='s', zorder=3)                            # after
        bounds = sdf.groupby('_t').apply(lambda g: (ypos[g.index].min(),
                                                    ypos[g.index].max()))
        for t, (ylo, yhi) in bounds.items():
            if ylo > ypos.min():
                ax.axhline(ylo - 0.5, color='0.85', lw=0.7, zorder=0)
        ax.set_yticks(ypos)
        ax.set_yticklabels(sdf['Well'], fontsize=9)
        ax.set_ylim(ypos.min() - 0.6, ypos.max() + 0.6)
        ax.set_xlabel(lab, fontsize=11)
        ax.grid(axis='x', color='0.92', lw=0.6, zorder=0)
        ax.tick_params(labelsize=9)
        for t, (ylo, yhi) in bounds.items():
            ax.text(1.02, (ylo + yhi) / 2, TIER_ORDER[int(t)],
                    transform=ax.get_yaxis_transform(), rotation=0,
                    va='center', ha='left', fontsize=8.5,
                    color=TIER_COLOURS[TIER_ORDER[int(t)]], fontweight='bold',
                    clip_on=False)

    # summary panel: per-tier β1 / β2 / β3 shift as % of the before value, so the
    # three coefficients share one scale (1.11.0: β3 added — in absolute terms it is
    # two orders of magnitude smaller than β1/β2 and could not share an axis)
    ax = fig.add_subplot(gs[3])
    specs = [('db1', 'b1_before', 'Δβ₁', '#1b7837'),
             ('db2', 'b2_before', 'Δβ₂', '#762a83'),
             ('db3', 'b3_before', 'Δβ₃', '#737373')]
    ty = np.arange(len(TIER_ORDER))[::-1]
    bw = 0.26
    for j, (col, bcol, lab, c) in enumerate(specs):
        vals, pvals = [], []
        for t in TIER_ORDER:
            td = sdf[sdf['Tier'] == t]
            vals.append(100.0 * td[col].mean() / td[bcol].mean() if len(td) > 0 else 0.0)
            pvals.append(tier_shift_p(td, col[1:]) if len(td) > 0 else np.nan)
        off = ((len(specs) - 1) / 2.0 - j) * bw
        ax.barh(ty + off, vals, height=bw, color=c, edgecolor='white', label=lab)
        # 1.12.0: p of each tier-mean shift against zero, at the bar's end
        for yy, v, pv in zip(ty + off, vals, pvals):
            if np.isfinite(pv):
                ax.text(v + (0.4 if v >= 0 else -0.4), yy, f"p={pv:.2f}", va='center',
                        ha='left' if v >= 0 else 'right', fontsize=6.5, color='0.25')
    ax.axvline(0, color='0.4', lw=0.8)
    ax.set_yticks(ty)
    ax.set_yticklabels(TIER_ORDER, fontsize=9)
    ax.set_xlabel('Mean coefficient shift (% of before value); p = tier-mean shift against zero',
                  fontsize=10)
    _xl = ax.get_xlim(); ax.set_xlim(_xl[0] - 4, _xl[1] + 4)   # room for the p labels
    ax.grid(axis='x', color='0.92', lw=0.6)
    ax.legend(fontsize=8, ncol=3, loc='lower left')   # lower right covered the Climate Ctrl bars

    leg = [Line2D([], [], marker='o', mfc='white', mec='0.3', ls='', ms=8,
                  label='Before clearfell'),
           Line2D([], [], marker='s', mfc='0.3', mec='0.3', ls='', ms=8,
                  label='After clearfell')]
    fig.legend(handles=leg, loc='upper center', ncol=2, fontsize=10,
               bbox_to_anchor=(0.5, 0.995), frameon=False)
    fig.suptitle('SSM coefficient decomposition: before vs after clearfell\n'
                 '(whiskers = 95% CI; wells grouped by BACI tier)',
                 fontsize=12.5, y=0.965)
    fig.subplots_adjust(top=0.93, left=0.13, right=0.85, bottom=0.045)
    render_figure(fig, OUT_FIG, facecolor='white', full_page=True)
    plt.close(fig)
    saved(f"{OUT_FIG.name}")

    # ============================================================================
    # EXPORT: REPORT NUMBERS
    # ============================================================================
    phase(4, "Exporting report numbers")
    rpt = ReportNumbers()

    for _, row in shift_df.iterrows():
        for coeff in ['b1', 'b2', 'b3']:
            rpt.add(f"CoeffShift_{row['Well']}_{coeff}_before", row[f'{coeff}_before'],
                    well=row['Well'], era="Before",
                    note=f"SE={row[f'{coeff}_SE_before']:.4f}")
            rpt.add(f"CoeffShift_{row['Well']}_{coeff}_after", row[f'{coeff}_after'],
                    well=row['Well'], era="After",
                    note=f"SE={row[f'{coeff}_SE_after']:.4f}")
            rpt.add(f"CoeffShift_{row['Well']}_d{coeff}", row[f'd{coeff}'],
                    well=row['Well'], era="Delta")

    # Tier means (T-91: Coastal Ctrl added -- it previously had no aggregate
    # row here even though the other four BACI-network tiers did).
    for tier_name in ['Impact', 'Edge', 'Forest Ctrl', 'Coastal Ctrl', 'Climate Ctrl']:
        tier_data = shift_df[shift_df['Tier'] == tier_name]
        if tier_data.empty:
            continue
        for coeff in ['db1', 'db2', 'db3']:
            rpt.add(f"CoeffShift_{tier_name}_mean_{coeff}",
                    tier_data[coeff].mean(),
                    well=tier_name,
                    note=f"n_wells={len(tier_data)}")
            # 1.12.0: the p printed beside the panel (d) bar
            rpt.add(f"CoeffShift_{tier_name}_mean_{coeff}_p",
                    tier_shift_p(tier_data, coeff[1:]), "",
                    well=tier_name,
                    note=("two-sided z-test of the tier-mean shift against zero, "
                          "SE = sqrt(sum(SE_before^2 + SE_after^2))/n from the per-well fits "
                          f"(independent windows), n_wells={len(tier_data)}"))
        # T-91: mean of each well's OWN %change in b1 (After-Before)/Before*100,
        # then averaged across the tier's wells -- this is the formula behind
        # the per-tier percentages quoted in report10.md S.5.5.1 (distinct from
        # the ratio-of-tier-means used in the summary bar-chart panel above).
        pct_per_well_b1 = 100.0 * tier_data['db1'] / tier_data['b1_before']
        n_decline = int((tier_data['db1'] < 0).sum())
        rpt.add(f"CoeffShift_{tier_name}_mean_db1_pct_of_before",
                pct_per_well_b1.mean(),
                well=tier_name,
                note=(f"mean of per-well pct change in b1 "
                      f"(After-Before)/Before*100, n_wells={len(tier_data)}, "
                      f"n_decline={n_decline}"))

    # Network-wide (T-91): the seventeen-well BACI network excludes the
    # Far-field Ctrl tier (see report10.md S.5.5.1, and the module docstring's
    # "17-well network" scope). Percentage here is the ratio of the network
    # mean db1 to the network mean b1_before -- the formula behind the
    # network-mean %-reduction quoted in report10.md S.5.5.1 (distinct from
    # the per-tier mean-of-per-well-pct formula just above).
    network_data = shift_df[shift_df['Tier'] != 'Far-field Ctrl']
    if not network_data.empty:
        net_b1_before = network_data['b1_before'].mean()
        net_b1_after = network_data['b1_after'].mean()
        net_db1 = network_data['db1'].mean()
        n_net = len(network_data)
        n_decline_net = int((network_data['db1'] < 0).sum())
        rpt.add("CoeffShift_Network_mean_b1_before", net_b1_before,
                well="Network", era="Before",
                note=f"mean b1_before across n={n_net} BACI-network wells "
                     f"(excl. Far-field Ctrl)")
        rpt.add("CoeffShift_Network_mean_b1_after", net_b1_after,
                well="Network", era="After",
                note=f"mean b1_after across n={n_net} BACI-network wells "
                     f"(excl. Far-field Ctrl)")
        rpt.add("CoeffShift_Network_mean_db1", net_db1,
                well="Network", era="Delta",
                note=f"mean db1 across n={n_net} BACI-network wells "
                     f"(excl. Far-field Ctrl), n_decline={n_decline_net}")
        # T-96: the count itself, as a Value (report9 Section 4.6.4).
        rpt.add("CoeffShift_Network_n_wells", float(n_net), "wells",
                well="Network",
                note="BACI-network wells in 10e_01_coefficient_shifts.csv, "
                     "excl. Far-field Ctrl: " + ", ".join(
                         f"{t} {int((network_data['Tier'] == t).sum())}"
                         for t in network_data['Tier'].unique()))
        if net_b1_before:
            rpt.add("CoeffShift_Network_mean_db1_pct_of_before",
                    100.0 * net_db1 / net_b1_before,
                    well="Network",
                    note="ratio of network mean db1 to network mean "
                         "b1_before, x100")

    # T-96: Forest Ctrl mean Δβ₂ over the intact-pine wells only -- the Forest
    # Ctrl wells outside the broadleaf restock block, identified from Script
    # 01's dist_broadleaf_restock_m (0 = inside the block), not by name
    # (report10 Section 5.6.2).
    if INT_LOCATIONS.exists():
        _loc = pd.read_csv(INT_LOCATIONS)
        if {'Match_ID', 'dist_broadleaf_restock_m'}.issubset(_loc.columns):
            _bl = {str(m).lower().replace(' ', '')
                   for m, d in zip(_loc['Match_ID'], _loc['dist_broadleaf_restock_m'])
                   if pd.notna(d) and float(d) <= 0.0}
            _fc = shift_df[shift_df['Tier'] == 'Forest Ctrl']
            _pine = _fc[~_fc['Well'].str.lower().isin(_bl)]
            _dropped = sorted(set(_fc['Well']) - set(_pine['Well']))
            if not _pine.empty:
                rpt.add("CoeffShift_Forest Ctrl_pine_mean_db2", _pine['db2'].mean(),
                        well="Forest Ctrl", era="Delta",
                        note=(f"mean db2 over Forest Ctrl wells outside the broadleaf "
                              f"restock block ({', '.join(_pine['Well'])}), "
                              f"n_wells={len(_pine)}; excluded: "
                              f"{', '.join(_dropped) or 'none'}"))
        else:
            warn(f"{INT_LOCATIONS.name} lacks dist_broadleaf_restock_m -- "
                 f"pine-only Forest Ctrl Δβ₂ not emitted")
    else:
        warn(f"{INT_LOCATIONS.name} not found -- pine-only Forest Ctrl Δβ₂ not emitted")

    # T-91: the β₂ scenario multiplier and the tier ratios it is built from
    # (utils.clearfell_common.load_clearfell_b2_multiplier), which the Methods
    # Supplement quotes (Edge ratio, Climate Ctrl drift, clearfell multiplier).
    try:
        from utils.clearfell_common import load_clearfell_b2_multiplier
        _cf, _thin, _ratios = load_clearfell_b2_multiplier(verbose=False)
        for _tier, _ratio in _ratios.items():
            rpt.add("B2_tier_ratio_after_over_before", float(_ratio), "",
                    well=_tier,
                    note="tier-mean b2_after / tier-mean b2_before from 10e_01_coefficient_shifts.csv")
        rpt.add("B2_multiplier_clearfell", float(_cf), "",
                note="Edge ratio − Climate Ctrl ratio + 1.0 (BACI-corrected); used by Script 09d (the scraping "
                     "suite); the forestry scenarios use B2_multiplier_clearfell_impact (D-239)")
        rpt.add("B2_multiplier_thinning", float(_thin), "",
                note="1 + (clearfell multiplier − 1)/2")
    except Exception as e:
        note(f"β₂ multiplier report numbers skipped: {e}")

    # 1.14.0 (T-97, D-239): the multipliers the forestry scenarios use - the felled well's own change
    try:
        from utils.clearfell_common import load_clearfell_impact_b2_multiplier
        _cfi, _thini, _ri = load_clearfell_impact_b2_multiplier(verbose=False)
        rpt.add("B2_multiplier_clearfell_impact", float(_cfi), "",
                note="Impact ratio (WMC3) − Climate Ctrl ratio + 1.0; used by the forestry scenarios of Scripts 19 "
                     "and 21 and the shared forestry bars, with no interception recharge term (D-239)")
        rpt.add("B2_multiplier_thinning_impact", float(_thini), "",
                note="1 + (B2_multiplier_clearfell_impact − 1)/2")
    except Exception as e:
        note(f"Impact β₂ multiplier report numbers skipped: {e}")

    # 1.14.0 (T-97, D-239): the shielding test
    phase(4, "Shielding test: canopy-on and canopy-off draw, before and after felling")
    sh = shielding_seasonal_b2(wells, climate)
    sh.to_csv(OUT_10E_SHIELDING, index=False)
    saved(f"{OUT_10E_SHIELDING.name} ({len(sh)} rows)")
    _shielding_report_numbers(rpt, sh)

    n_saved = rpt.save(OUT_REPORT)
    saved(f"{OUT_REPORT.name} ({n_saved} rows)")

    # ============================================================================
    # CONSOLE SUMMARY
    # ============================================================================
    print("\n" + "=" * 72)
    print("COEFFICIENT SHIFT SUMMARY (mechanistic direction diagnostic)")
    print("=" * 72)
    print(f"\n  {'Tier':<14} {'Δβ₁':>8} {'Δβ₂':>8} {'Δβ₃':>8}")
    print(f"  {'-'*40}")
    for tier_name in ['Impact', 'Edge', 'Forest Ctrl', 'Climate Ctrl']:
        td = shift_df[shift_df['Tier'] == tier_name]
        if td.empty:
            continue
        print(f"  {tier_name:<14} "
              f"{td['db1'].mean():>+8.3f} "
              f"{td['db2'].mean():>+8.3f} "
              f"{td['db3'].mean():>+8.3f}")

    print("=" * 72)
    print("Script 10e complete.\n")


if __name__ == "__main__":
    main()
