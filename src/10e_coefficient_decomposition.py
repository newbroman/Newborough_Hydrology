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
   pre-felling window (PRE_FELL_START → INTERVENTION_DATE) with a
   scraping dummy for the April 2015 event.  "After" covers
   INTERVENTION_DATE → end of record.
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

__version__ = "1.5.0"  # Hollingham (2026) — 2026-05-31
# 1.5.0 — Figure 10e_03 redesigned for legibility. Replaced the single-row
#         1x4 panel (illegible when embedded at column width) with a vertical
#         stack of three horizontal before/after dumbbell panels (β₁, β₂, β₃),
#         wells on the y-axis grouped and coloured by tier (all five tiers now
#         shown, incl. Coastal Ctrl), open circle = before / filled square =
#         after, 95% CI whiskers. Summary panel changed from absolute mean Δβ
#         (which let the tiny-absolute β₃ vanish and over-magnified β₂ on a
#         narrow shared axis) to a per-tier β₁/β₂ shift as % of the before
#         value; β₃ dropped from the summary (its % swings are noise-dominated
#         and already shown on its own dumbbell panel). FIGURE-ONLY change:
#         shift_df, the 10e_01 CSV, and downstream consumers (Scripts 19/21
#         β₂ multiplier) are untouched. New imports: GridSpec, Line2D.
# 1.4.0 — Option A resolution of the 10e predicted-vs-observed problem.
#         REMOVED the predicted-vs-observed comparison entirely:
#           * dropped the Δh_predicted column and all its inputs
#             (mean_P_m, mean_PET_m, mean_h_disp_m);
#           * dropped the 10e_02_predicted_vs_observed.csv output (no
#             downstream consumer — verified across src/ and run_*.py);
#           * dropped the import of 10a_report_numbers.csv observed
#             ANCOVA steps and the summer-suffix predicate logic;
#           * the summary figure's 4th panel is replaced by a per-tier
#             mean-Δβ panel.
#         REVERTED the Before/After era fits from the intercept-bearing
#         Model B to the canonical no-intercept Model A (fit_ssm() with
#         the default intercept=False), consistent with Script 03 and
#         Methods Supplement S.3.
#         RATIONALE: the per-era per-well SSM β-projection and the 10a
#         ANCOVA BACI step are estimates of different quantities — the
#         10a step is a control-differenced centroid coefficient,
#         whereas Δh_predicted had no control subtraction and a
#         different projection basis. The comparison was not a valid
#         reconciliation; earlier versions could only close it by
#         absorbing the gap into an intercept shift Δα of unidentified
#         physical content. 10e is hereby a mechanistic-DIRECTION
#         diagnostic (which pathway shifted, in which direction); the
#         clearfell magnitude result is, and remains, the 10a BACI step.
#         Decision: report editorial chat, 2026-05-24 (Option A);
#         supersedes HANDOVER_10e_intercept_export.md (which proposed
#         Option C, the Δα export — not adopted). Closes Editorial Q3.
#         CONSEQUENCE: 10e_01 b1/b2/b3 columns shift slightly vs v1.3.0
#         (no-intercept vs with-intercept fit) — NOT byte-identical to
#         v1.3.0, by design. b2_before/b2_after still feed the Script
#         19/21 β₂ forestry multiplier via clearfell_common; the
#         multiplier recomputes on every call, so it tracks the new
#         values automatically.
# 1.3.0 — Migrate Before-era and After-era OLS fits from inline
#         sm.OLS(...sm.add_constant(...)) to the canonical
#         model_utils.fit_ssm() interface, using the v1.1.0 keywords
#         intercept=True and extra_regressors={'scraping_dummy': ...}
#         for the Before era's four-column design matrix.  Closes
#         Item 3 in CHAPTER_FLAGS_TO_REVIEW.md (model_utils
#         consolidation).  No functional change: byte-identical β,
#         SE, p-value, and intercept outputs to v1.2.2 (verified
#         empirically against pre-edit pipeline run).  Minor — the
#         provenance comment block at the OLS call sites is replaced
#         by a shorter inline note pointing to the v1.1.0 fit_ssm()
#         interface.
# 1.2.2 — Defect 15 fix.  observed_steps loader (~line 315) was using a
#         substring predicate (`'Forest' in param and 'clearfell_step'
#         in param`) which matched both the headline annual row
#         (`ANCOVA_Forest_Impact_clearfell_step`) and the summer-band
#         rows added by Defect 14 (`..._clearfell_step_summer` and
#         `..._clearfell_step_summer_noCWB`).  Last-write-wins put the
#         noCWB sensitivity (0.2384 m) into observed_steps['Forest_
#         Impact'] instead of the canonical annual headline (0.1362 m).
#         Tightened the predicate to require '_clearfell_step' as a
#         SUFFIX (startswith/endswith), which rejects the summer
#         variants and any future named variants.  Regenerating
#         10e_02_predicted_vs_observed.csv produces the correct
#         comparison values.  Bug was latent in Script 10e v1.x; it
#         was triggered by Script 10a v1.3.0 (Defect 14) adding the
#         summer rows.  Affected one cell: Impact tier Observed_ANCOVA_
#         forest_m (0.2384 m → 0.1362 m).  All other cells were
#         correct.  Patch.
# 1.2.1 — Added inline provenance comment at the first OLS call site
#         explaining why 10e fits directly with sm.add_constant() rather
#         than going through model_utils.fit_ssm() (Item 1 in flags log).
# 1.2.0 — Adopt CEH34 hindcast via apply_ceh34_hindcast().  Companion to
#         PRE_FELL_START = 2010-07-01 in clearfell_common v1.2.0.
# 1.1.0 — Apply PRE_FELL_START record-length-balance cutoff to Before
#         era; switch dh_predicted normalisation from full-record
#         (centennial) climate means to post-INTERVENTION means.
#         Updated docstring with note on intercept vs β decomposition.
# 1.0.0 — Initial.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)

from utils.clearfell_common import (
    load_clearfell_data, apply_ceh34_hindcast, ALL_NETWORK_WELLS,
    INTERVENTION_DATE, SCRAPING_DATE, PRE_FELL_START, TIER_COLOURS,
    ReportNumbers, print_network_summary, get_tier,
)
from utils.paths import make_all_dirs, DIR_10
from utils.model_utils import build_ssm_frame, fit_ssm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

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
banner("10e", "SSM COEFFICIENT DECOMPOSITION")

phase(1, "Loading data")
wells, _wells_prov, climate, master, well_locations, valid_tiers = load_clearfell_data()
wells = apply_ceh34_hindcast(wells)
print_network_summary(valid_tiers)

# ============================================================================
# FIT SSM PER WELL, PER ERA
# ============================================================================
phase(2, "Fitting per-era SSM coefficients")
# The "Before" era is the record-length-balanced pre-felling window
# (PRE_FELL_START → INTERVENTION_DATE) with a scraping dummy.
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
                       (ssm_frame.index < INTERVENTION_DATE)].copy()
    after = ssm_frame[ssm_frame.index >= INTERVENTION_DATE].copy()

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

# summary panel: per-tier β1 / β2 shift as % of the before value (β3 omitted —
# its % swings are noise-dominated; the absolute β3 shifts are on panel 3)
ax = fig.add_subplot(gs[3])
specs = [('db1', 'b1_before', 'Δβ₁', '#1b7837'),
         ('db2', 'b2_before', 'Δβ₂', '#762a83')]
ty = np.arange(len(TIER_ORDER))[::-1]
bw = 0.32
for j, (col, bcol, lab, c) in enumerate(specs):
    vals = []
    for t in TIER_ORDER:
        td = sdf[sdf['Tier'] == t]
        vals.append(100.0 * td[col].mean() / td[bcol].mean() if len(td) > 0 else 0.0)
    off = ((len(specs) - 1) / 2.0 - j) * bw
    ax.barh(ty + off, vals, height=bw, color=c, edgecolor='white', label=lab)
ax.axvline(0, color='0.4', lw=0.8)
ax.set_yticks(ty)
ax.set_yticklabels(TIER_ORDER, fontsize=9)
ax.set_xlabel('Mean coefficient shift (% of before value)', fontsize=10)
ax.grid(axis='x', color='0.92', lw=0.6)
ax.legend(fontsize=8, ncol=2, loc='lower right')

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
fig.savefig(OUT_FIG, dpi=200, bbox_inches='tight', facecolor='white')
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

# Tier means
for tier_name in ['Impact', 'Edge', 'Forest Ctrl', 'Climate Ctrl']:
    tier_data = shift_df[shift_df['Tier'] == tier_name]
    if tier_data.empty:
        continue
    for coeff in ['db1', 'db2', 'db3']:
        rpt.add(f"CoeffShift_{tier_name}_mean_{coeff}",
                tier_data[coeff].mean(),
                well=tier_name,
                note=f"n_wells={len(tier_data)}")

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
