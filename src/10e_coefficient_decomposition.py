r"""
====================================================================================
10e — SSM COEFFICIENT DECOMPOSITION
====================================================================================
Purpose
-------
Decomposes the clearfell effect into mechanistic pathways via SSM
coefficient shifts (β₁, β₂, β₃) between pre- and post-felling eras.

Method
------
1. For each well in the 17-well network, fit the SSM (contemporaneous
   rainfall, displacement formulation) separately for Before and After
   eras.  "Before" is the record-length-balanced pre-felling window
   (PRE_FELL_START → INTERVENTION_DATE) with a scraping dummy for the
   April 2015 event.  "After" covers INTERVENTION_DATE → end of record.
2. Compute per-well Δβ₁, Δβ₂, Δβ₃ (After − Before).
3. Predicted clearfell effect from coefficient shifts, projected onto
   the post-INTERVENTION_DATE climate (matched to the After era):
     Δh_predicted = Δβ₁ · mean_P_post − Δβ₂ · mean_PET_post − Δβ₃ · mean_h_disp_post
4. Compare Δh_predicted to the observed BACI step from 10a.

Note on interpretation
----------------------
Both Before and After OLS fits include an intercept (α).  The Δh_predicted
formula above captures only the β·X component of the era shift; the
intercept difference Δα absorbs the era-mean residual, which is the
dominant component at most wells (Δα ~ +120 mm at WMC3 vs Δh_predicted
~ -110 mm).  The predicted vs observed comparison is therefore informative
about the mechanistic decomposition (Δβ₁ recharge, Δβ₂ ET-draw, Δβ₃
drainage) but should not be read as a complete reconstruction of the
BACI step.  See Editorial Q3 in CHAPTER_FLAGS_TO_REVIEW.md.

Outputs
-------
CSV:
  10e_01_coefficient_shifts.csv    — per-well before/after coefficients
  10e_02_predicted_vs_observed.csv — predicted vs observed clearfell step
  10e_report_numbers.csv           — all citable values

Figures:
  10e_03_coefficient_shifts.png    — before/after by well, coloured by tier

References
----------
Hollingham (2026), §4.6.  Part of the Script 10 clearfell analysis suite.
====================================================================================
"""

__version__ = "1.2.1"  # Hollingham (2026) — 2026-05-17
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

from utils.clearfell_common import (
    load_clearfell_data,
    apply_ceh34_hindcast,
    IMPACT_WELLS, EDGE_WELLS,
    FOREST_CONTROL_WELLS, COASTAL_CONTROL_WELLS, CLIMATE_CONTROL_WELLS,
    TIERS, ALL_NETWORK_WELLS,
    INTERVENTION_DATE, SCRAPING_DATE,
    PRE_FELL_START,
    TIER_COLOURS, ReportNumbers, print_network_summary, get_tier,
)
from utils.paths import make_all_dirs, DIR_10, INT_CLIMATE
from utils.model_utils import build_ssm_frame, fit_ssm
from utils.config import DRAINAGE_DATUM
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats as sp_stats
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

make_all_dirs()

# ============================================================================
# OUTPUT PATHS
# ============================================================================
OUT_SHIFTS        = DIR_10 / "10e_01_coefficient_shifts.csv"
OUT_PREDICTED     = DIR_10 / "10e_02_predicted_vs_observed.csv"
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
print("=" * 72)
print("SCRIPT 10e — SSM COEFFICIENT DECOMPOSITION")
print("=" * 72)

print("\n1. Loading data...")
wells, climate, master, well_locations, valid_tiers = load_clearfell_data()
wells = apply_ceh34_hindcast(wells)
print_network_summary(valid_tiers)

# ============================================================================
# FIT SSM PER WELL, PER ERA
# ============================================================================
print("2. Fitting per-era SSM coefficients...")

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
        print(f"   [WARNING] SSM frame failed for {w}: {e}")
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
        print(f"   [SKIP] {w.upper()}: before={len(before)}, after={len(after)}")
        continue

    # ── Before era: fit with scraping dummy ──────────────────────────
    before['D_scrape'] = (before.index >= SCRAPING_DATE).astype(float)

    X_before = pd.DataFrame({
        'beta_1_recharge': before['P'],
        'beta_2_atmospheric_draw': -before['PET'],
        'beta_3_drainage': -before['h_disp_prev'],
        'scraping_dummy': before['D_scrape'],
    })
    y_before = before['Delta_h']
    mask_before = X_before.notna().all(axis=1) & y_before.notna()
    X_b = X_before[mask_before]
    y_b = y_before[mask_before]

    if len(y_b) < 8:
        continue

    try:
        # NOTE: 10e fits OLS directly (with sm.add_constant for an
        # intercept α) rather than going through model_utils.fit_ssm(),
        # because (a) the Before fit needs an extra `scraping_dummy`
        # regressor that fit_ssm()'s canonical interface doesn't accept,
        # and (b) the intercept is intentional — the Δα between Before
        # and After is part of the era decomposition the script measures
        # (see "Note on interpretation" in the module docstring; this is
        # a deliberate departure from the no-intercept canonical SSM in
        # model_utils.fit_ssm()).  Column names use the canonical long
        # form so downstream consumers reading 10e_01_coefficient_shifts.csv
        # see the same nomenclature as 03_master_data.csv.
        model_b = sm.OLS(y_b, sm.add_constant(X_b)).fit()
        b1_before = model_b.params['beta_1_recharge']
        b2_before = model_b.params['beta_2_atmospheric_draw']
        b3_before = model_b.params['beta_3_drainage']
        b1_se_before = model_b.bse['beta_1_recharge']
        b2_se_before = model_b.bse['beta_2_atmospheric_draw']
        b3_se_before = model_b.bse['beta_3_drainage']
    except Exception as e:
        print(f"   [WARNING] Before OLS failed for {w}: {e}")
        continue

    # ── After era: standard SSM ──────────────────────────────────────
    X_after = pd.DataFrame({
        'beta_1_recharge': after['P'],
        'beta_2_atmospheric_draw': -after['PET'],
        'beta_3_drainage': -after['h_disp_prev'],
    })
    y_after = after['Delta_h']
    mask_after = X_after.notna().all(axis=1) & y_after.notna()
    X_a = X_after[mask_after]
    y_a = y_after[mask_after]

    if len(y_a) < 6:
        continue

    try:
        model_a = sm.OLS(y_a, sm.add_constant(X_a)).fit()
        b1_after = model_a.params['beta_1_recharge']
        b2_after = model_a.params['beta_2_atmospheric_draw']
        b3_after = model_a.params['beta_3_drainage']
        b1_se_after = model_a.bse['beta_1_recharge']
        b2_se_after = model_a.bse['beta_2_atmospheric_draw']
        b3_se_after = model_a.bse['beta_3_drainage']
    except Exception as e:
        print(f"   [WARNING] After OLS failed for {w}: {e}")
        continue

    # ── Compute deltas ───────────────────────────────────────────────
    db1 = b1_after - b1_before
    db2 = b2_after - b2_before
    db3 = b3_after - b3_before

    # ── Predicted effect from coefficient shifts ─────────────────────
    # Project the per-era β shift onto the climate of the post-fell era —
    # this is the relevant counterfactual for "what would the After-era
    # response have been under the Before-era β's?"  Using full-record
    # (centennial) means is a documentation fossil; post-INTERVENTION
    # means are the methodologically appropriate normalisation.
    #
    # NOTE: this estimator captures only the β·X component of the era
    # shift; the OLS intercept (α) absorbs the era-mean residual which
    # is the dominant component at most wells.  dh_predicted should not
    # be read as a complete decomposition of the BACI step; the residual
    # vs intercept-shift relationship is an open methodological question
    # (see Editorial Q3 / Q24 in CHAPTER_FLAGS_TO_REVIEW.md).
    after_climate = climate.loc[climate.index >= INTERVENTION_DATE]
    mean_P = pd.to_numeric(after_climate['P_m'], errors='coerce').mean()
    mean_PET = pd.to_numeric(after_climate['PET'], errors='coerce').mean()
    after_h = wells[w].loc[wells[w].index >= INTERVENTION_DATE]
    mean_h_disp = (DRAINAGE_DATUM + after_h.shift(1)).mean()

    dh_predicted = db1 * mean_P - db2 * mean_PET - db3 * mean_h_disp

    rows.append({
        'Well': w.upper(),
        'Tier': tier,
        'N_before': len(y_b),
        'N_after': len(y_a),
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
        'mean_P_m': round(mean_P, 4),
        'mean_PET_m': round(mean_PET, 4),
        'mean_h_disp_m': round(mean_h_disp, 4),
        'dh_predicted_m': round(dh_predicted, 4),
    })

    print(f"   {w.upper():<8}  Δβ₁={db1:+.3f}  Δβ₂={db2:+.3f}  "
          f"Δβ₃={db3:+.3f}  Δh_pred={dh_predicted*1000:+.0f} mm")

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
    print(f"  [note] Pipeline params B2 update skipped: {e}")

# ============================================================================
# PREDICTED VS OBSERVED TABLE
# ============================================================================
print("\n3. Building predicted vs observed table...")

# Load 10a report numbers if available for observed ANCOVA steps
ancova_report_path = DIR_10 / "10a_report_numbers.csv"
observed_steps = {}
if ancova_report_path.exists():
    ancova_rpt = pd.read_csv(ancova_report_path)
    for _, row in ancova_rpt.iterrows():
        param = str(row.get('Parameter', ''))
        if 'Forest' in param and 'clearfell_step' in param:
            zone = row.get('Well', '')
            observed_steps[f'Forest_{zone}'] = row.get('Value', np.nan)
        if 'Climate' in param and 'clearfell_step' in param:
            zone = row.get('Well', '')
            observed_steps[f'Climate_{zone}'] = row.get('Value', np.nan)

pred_rows = []
for tier_name, tier_wells in TIERS.items():
    tier_data = shift_df[shift_df['Tier'] == tier_name]
    if tier_data.empty:
        continue
    mean_dh_pred = tier_data['dh_predicted_m'].mean()

    obs_forest = observed_steps.get(f'Forest_{tier_name}', np.nan)
    obs_climate = observed_steps.get(f'Climate_{tier_name}', np.nan)

    pred_rows.append({
        'Tier': tier_name,
        'N_wells': len(tier_data),
        'Mean_dh_predicted_m': round(mean_dh_pred, 4),
        'Mean_dh_predicted_mm': round(mean_dh_pred * 1000, 1),
        'Observed_ANCOVA_forest_m': obs_forest if not pd.isna(obs_forest) else '',
        'Observed_ANCOVA_climate_m': obs_climate if not pd.isna(obs_climate) else '',
        'Mean_db1': round(tier_data['db1'].mean(), 4),
        'Mean_db2': round(tier_data['db2'].mean(), 4),
        'Mean_db3': round(tier_data['db3'].mean(), 4),
    })

pred_df = pd.DataFrame(pred_rows)
pred_df.to_csv(OUT_PREDICTED, index=False)
print(f" -> Saved: {OUT_PREDICTED.name} ({len(pred_df)} rows)")

# ============================================================================
# FIGURE: COEFFICIENT SHIFTS BY TIER
# ============================================================================
print("\n4. Generating coefficient shift figure...")

coeff_labels = [
    ('b1_before', 'b1_after', 'b1_SE_before', 'b1_SE_after', 'β₁ (recharge)'),
    ('b2_before', 'b2_after', 'b2_SE_before', 'b2_SE_after', 'β₂ (atmospheric draw)'),
    ('b3_before', 'b3_after', 'b3_SE_before', 'b3_SE_after', 'β₃ (drainage)'),
]

fig, axes = plt.subplots(1, 4, figsize=(18, 8), dpi=300)
fig.subplots_adjust(wspace=0.35)

for panel_idx, (col_b, col_a, se_b, se_a, ylabel) in enumerate(coeff_labels):
    ax = axes[panel_idx]

    x_pos = 0
    tick_pos = []
    tick_labels = []

    for tier_name in ['Impact', 'Edge', 'Forest Ctrl', 'Climate Ctrl']:
        tier_data = shift_df[shift_df['Tier'] == tier_name].sort_values('Well')
        colour = TIER_COLOURS[tier_name]

        for _, row in tier_data.iterrows():
            # Before
            ax.errorbar(x_pos - 0.15, row[col_b], yerr=1.96*row[se_b],
                        fmt='o', color=colour, ms=5, capsize=3, alpha=0.7)
            # After
            ax.errorbar(x_pos + 0.15, row[col_a], yerr=1.96*row[se_a],
                        fmt='s', color=colour, ms=5, capsize=3, alpha=0.7)
            # Arrow
            ax.annotate('', xy=(x_pos + 0.15, row[col_a]),
                        xytext=(x_pos - 0.15, row[col_b]),
                        arrowprops=dict(arrowstyle='->', color='grey',
                                        lw=0.8, alpha=0.5))

            tick_pos.append(x_pos)
            tick_labels.append(row['Well'])
            x_pos += 1

        x_pos += 0.5  # gap between tiers

    ax.set_xticks(tick_pos)
    ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel(ylabel)
    ax.axhline(0, color='grey', ls=':', lw=0.5)
    ax.set_title(ylabel)

# Summary panel: predicted Δh by tier
ax = axes[3]
tier_order = ['Impact', 'Edge', 'Forest Ctrl', 'Climate Ctrl']
x = np.arange(len(tier_order))
vals = []
colours = []
for t in tier_order:
    td = shift_df[shift_df['Tier'] == t]
    vals.append(td['dh_predicted_m'].mean() * 1000 if len(td) > 0 else 0)
    colours.append(TIER_COLOURS[t])

ax.bar(x, vals, color=colours, width=0.6, edgecolor='white')
ax.set_xticks(x)
ax.set_xticklabels(tier_order, rotation=30, ha='right', fontsize=9)
ax.set_ylabel('Predicted Δh (mm)')
ax.set_title('Predicted clearfell effect\nfrom coefficient shifts')
ax.axhline(0, color='grey', ls=':', lw=0.5)

# Add value labels
for xi, val in zip(x, vals):
    ax.text(xi, val + (2 if val >= 0 else -4), f'{val:+.0f}',
            ha='center', fontsize=9, fontweight='bold')

fig.suptitle(
    'SSM coefficient decomposition: Before vs After clearfell\n'
    '(○ = Before, □ = After, whiskers = 95% CI)',
    fontsize=13, y=0.98)
fig.savefig(OUT_FIG, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f" -> Saved: {OUT_FIG.name}")

# ============================================================================
# EXPORT: REPORT NUMBERS
# ============================================================================
print("\n5. Exporting report numbers...")
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

    rpt.add(f"CoeffShift_{row['Well']}_dh_predicted", row['dh_predicted_m'],
            well=row['Well'], note="Predicted clearfell effect from Δβ")

# Tier means
for tier_name in ['Impact', 'Edge', 'Forest Ctrl', 'Climate Ctrl']:
    tier_data = shift_df[shift_df['Tier'] == tier_name]
    if tier_data.empty:
        continue
    rpt.add(f"CoeffShift_{tier_name}_mean_dh_predicted",
            tier_data['dh_predicted_m'].mean(),
            well=tier_name,
            note=f"n_wells={len(tier_data)}")
    for coeff in ['db1', 'db2', 'db3']:
        rpt.add(f"CoeffShift_{tier_name}_mean_{coeff}",
                tier_data[coeff].mean(),
                well=tier_name)

n_saved = rpt.save(OUT_REPORT)
print(f" -> Saved: {OUT_REPORT.name} ({n_saved} rows)")

# ============================================================================
# CONSOLE SUMMARY
# ============================================================================
print("\n" + "=" * 72)
print("COEFFICIENT DECOMPOSITION SUMMARY")
print("=" * 72)
print(f"\n  {'Tier':<14} {'Δβ₁':>8} {'Δβ₂':>8} {'Δβ₃':>8} {'Δh pred (mm)':>14}")
print(f"  {'-'*56}")
for tier_name in ['Impact', 'Edge', 'Forest Ctrl', 'Climate Ctrl']:
    td = shift_df[shift_df['Tier'] == tier_name]
    if td.empty:
        continue
    print(f"  {tier_name:<14} "
          f"{td['db1'].mean():>+8.3f} "
          f"{td['db2'].mean():>+8.3f} "
          f"{td['db3'].mean():>+8.3f} "
          f"{td['dh_predicted_m'].mean()*1000:>+14.0f}")

print("=" * 72)
print("Script 10e complete.\n")
