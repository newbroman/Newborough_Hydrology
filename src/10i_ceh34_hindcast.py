r"""
====================================================================================
10i — CEH34 DONOR-REGRESSION HINDCAST
====================================================================================
Purpose
-------
Produce a donor-regression hindcast of CEH34 covering the pre-CEH34-record
window (2006-05 to 2010-07), so that downstream BACI analyses can include
CEH34 in a pre-fell window that starts before its 2010-08-01 first
observation.

Why CEH9 as donor (not CEH2)?
-----------------------------
CEH2 has a stronger empirical correlation with CEH34 (r²=0.97 vs r²=0.89
for CEH9), but CEH2 is itself a Forest Control well that already
contributes to the BACI Forest Control centroid.  Hindcasting CEH34
against CEH2 and then adding both to the Forest Control set would amount
to upweighting CEH2's contribution to the pre-fell baseline — a partial
double-count.

CEH9 is a Climate Control well — independent of the Forest Control set —
and so its use as donor adds genuinely independent information to the
hindcast.  The r²=0.89 reflects the strong site-wide groundwater
synchrony at Newborough; the noise band is documented in
``10i_02_donor_regression.csv``.

Method
------
1. Load wells and climate via ``load_clearfell_data()``.
2. OLS fit on the pre-clearfell overlap (2010-08-01 to 2017-11-30):
       CEH34(t) = α + β · CEH9(t) + ε
   Pre-clearfell only — fitting in the post-fell era would risk
   inheriting any clearfell-related divergence between the two wells
   into the calibrated relationship.
3. Apply the fitted relationship to CEH9's pre-CEH34 record to produce
   synthetic CEH34 values for dates < 2010-08-01.
4. Splice: synthetic for dates < 2010-08-01, observed for dates >= 2010-08-01.

Outputs
-------
CSV:
  10i_01_ceh34_hindcast.csv     — spliced series with `source` flag
                                  (``'hindcast'`` or ``'observed'``)
  10i_02_donor_regression.csv   — fit parameters, residual diagnostics
  10i_report_numbers.csv        — citable values

Figures:
  10i_03_hindcast_diagnostic.png — three-panel diagnostic figure

Downstream consumption
----------------------
The spliced series is exposed via
``clearfell_common.load_ceh34_hindcast_series()`` (added in
clearfell_common v1.2.0).  Scripts that opt in call that loader
explicitly; the data path remains untouched for scripts that do not
opt in.

References
----------
Hollingham (2026), §4.6 (clearfell BACI analysis).  Part of the Script 10
clearfell analysis suite.
====================================================================================
"""

__version__ = "1.0.0"  # Hollingham (2026) — 2026-05-16

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.clearfell_common import (
    load_clearfell_data,
    INTERVENTION_DATE,
    ReportNumbers,
)
from utils.paths import (
    make_all_dirs,
    OUT_10I_HINDCAST, OUT_10I_REGRESSION,
    OUT_10I_DIAGNOSTIC, OUT_10I_REPORT,
)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

make_all_dirs()

# ============================================================================
# CONFIGURATION
# ============================================================================
TARGET_WELL   = 'ceh34'
DONOR_WELL    = 'ceh9'
CAL_START     = pd.Timestamp('2010-08-01')   # CEH34 first observation
CAL_END       = INTERVENTION_DATE             # exclusive — pre-clearfell only

# ============================================================================
# OUTPUT PATHS (from utils.paths)
# ============================================================================
OUT_HINDCAST    = OUT_10I_HINDCAST
OUT_REGRESSION  = OUT_10I_REGRESSION
OUT_DIAGNOSTIC  = OUT_10I_DIAGNOSTIC
OUT_REPORT      = OUT_10I_REPORT

# ============================================================================
# MATPLOTLIB DEFAULTS
# ============================================================================
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
})


def main():
    print("=" * 72)
    print("SCRIPT 10i — CEH34 DONOR-REGRESSION HINDCAST")
    print("=" * 72)

    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    print("\n1. Loading data...")
    wells, climate, master, well_locations, valid_tiers = load_clearfell_data()

    if TARGET_WELL not in wells.columns:
        raise RuntimeError(f"Target well '{TARGET_WELL}' not present in wells DataFrame.")
    if DONOR_WELL not in wells.columns:
        raise RuntimeError(f"Donor well '{DONOR_WELL}' not present in wells DataFrame.")

    target = wells[TARGET_WELL].dropna()
    donor  = wells[DONOR_WELL].dropna()
    print(f"   {TARGET_WELL.upper():<8} record: {target.index.min().date()} → "
          f"{target.index.max().date()}  ({len(target)} months)")
    print(f"   {DONOR_WELL.upper():<8} record: {donor.index.min().date()} → "
          f"{donor.index.max().date()}  ({len(donor)} months)")

    # ------------------------------------------------------------------
    # 2. Calibration: fit OLS on pre-clearfell overlap
    # ------------------------------------------------------------------
    print(f"\n2. Fitting donor regression on pre-clearfell overlap "
          f"({CAL_START.date()} to {(CAL_END - pd.Timedelta(days=1)).date()})...")

    overlap = pd.concat([target, donor], axis=1, join='inner').dropna()
    overlap.columns = [TARGET_WELL, DONOR_WELL]
    cal = overlap.loc[(overlap.index >= CAL_START) & (overlap.index < CAL_END)]
    n_cal = len(cal)

    if n_cal < 30:
        raise RuntimeError(f"Insufficient calibration data: only {n_cal} months "
                           f"of {TARGET_WELL.upper()} × {DONOR_WELL.upper()} overlap "
                           f"in pre-clearfell window.")

    X = sm.add_constant(cal[DONOR_WELL].values)
    y = cal[TARGET_WELL].values
    model = sm.OLS(y, X).fit()
    alpha, beta = float(model.params[0]), float(model.params[1])
    alpha_se, beta_se = float(model.bse[0]), float(model.bse[1])
    r2 = float(model.rsquared)
    rmse = float(np.sqrt(model.mse_resid))

    print(f"   Fit: {TARGET_WELL.upper()} = {alpha:+.4f} + {beta:+.4f} · {DONOR_WELL.upper()}")
    print(f"   α = {alpha:+.4f}  (SE {alpha_se:.4f}, p = {model.pvalues[0]:.4f})")
    print(f"   β = {beta:+.4f}   (SE {beta_se:.4f}, p < 1e-30)")
    print(f"   r² = {r2:.4f}     RMSE = {rmse*1000:.1f} mm     n_cal = {n_cal}")

    # ------------------------------------------------------------------
    # 3. Hindcast: project backwards over donor's pre-target record
    # ------------------------------------------------------------------
    print(f"\n3. Hindcasting {TARGET_WELL.upper()} over pre-record window...")

    hind_dates = donor.index[donor.index < target.index.min()]
    if len(hind_dates) == 0:
        raise RuntimeError(f"No pre-target donor coverage — nothing to hindcast.")
    hindcast_values = alpha + beta * donor.loc[hind_dates].values
    hindcast_series = pd.Series(hindcast_values, index=hind_dates,
                                name=TARGET_WELL)
    print(f"   Hindcast covers {len(hindcast_series)} months: "
          f"{hindcast_series.index.min().date()} → {hindcast_series.index.max().date()}")

    # ------------------------------------------------------------------
    # 4. Splice: hindcast (synthetic) + observed (real)
    # ------------------------------------------------------------------
    print(f"\n4. Splicing hindcast with observed record...")

    spliced = pd.concat([hindcast_series, target]).sort_index()
    spliced = spliced[~spliced.index.duplicated(keep='last')]

    source = pd.Series('observed', index=spliced.index)
    source.loc[source.index < target.index.min()] = 'hindcast'

    spliced_df = pd.DataFrame({
        'Date':   spliced.index,
        'CEH34':  spliced.values,
        'source': source.values,
        'donor_value':  np.where(source.values == 'hindcast',
                                 donor.reindex(spliced.index).values,
                                 np.nan),
    })
    spliced_df.to_csv(OUT_HINDCAST, index=False)
    n_hindcast = int((spliced_df['source'] == 'hindcast').sum())
    n_observed = int((spliced_df['source'] == 'observed').sum())
    print(f"   -> Saved: {OUT_HINDCAST.name}  "
          f"({n_hindcast} hindcast + {n_observed} observed = {len(spliced_df)} months)")

    # ------------------------------------------------------------------
    # 5. Export regression diagnostics
    # ------------------------------------------------------------------
    print(f"\n5. Exporting regression diagnostics...")

    reg_df = pd.DataFrame([{
        'target':         TARGET_WELL.upper(),
        'donor':          DONOR_WELL.upper(),
        'cal_start':      CAL_START.date(),
        'cal_end':        (CAL_END - pd.Timedelta(days=1)).date(),
        'n_cal':          n_cal,
        'alpha':          round(alpha, 5),
        'alpha_SE':       round(alpha_se, 5),
        'alpha_p':        round(float(model.pvalues[0]), 5),
        'beta':           round(beta, 5),
        'beta_SE':        round(beta_se, 5),
        'beta_p':         f"{float(model.pvalues[1]):.2e}",
        'r2':             round(r2, 5),
        'rmse_m':         round(rmse, 5),
        'pred_interval_95_m': round(rmse * 1.96, 5),
        'n_hindcast':     n_hindcast,
        'n_observed':     n_observed,
        'hindcast_start': hindcast_series.index.min().date(),
        'hindcast_end':   hindcast_series.index.max().date(),
    }])
    reg_df.to_csv(OUT_REGRESSION, index=False)
    print(f"   -> Saved: {OUT_REGRESSION.name}")

    # ------------------------------------------------------------------
    # 6. Diagnostic figure (three panels)
    # ------------------------------------------------------------------
    print(f"\n6. Generating diagnostic figure...")

    fig, axes = plt.subplots(3, 1, figsize=(12, 11), dpi=300)

    # Panel A: paired scatter with fit line
    ax = axes[0]
    ax.scatter(cal[DONOR_WELL], cal[TARGET_WELL],
               s=22, alpha=0.65, edgecolor='none', color='#1f4e79',
               label=f'Calibration ({n_cal} months)')
    xline = np.linspace(cal[DONOR_WELL].min(), cal[DONOR_WELL].max(), 100)
    yline = alpha + beta * xline
    ax.plot(xline, yline, color='#cc0000', lw=1.6,
            label=f'OLS: {TARGET_WELL.upper()} = {alpha:+.3f} + {beta:+.3f} · {DONOR_WELL.upper()}')
    ax.fill_between(xline, yline - 1.96*rmse, yline + 1.96*rmse,
                    color='#cc0000', alpha=0.10,
                    label=f'±1.96·RMSE  (±{rmse*1.96*1000:.0f} mm)')
    ax.set_xlabel(f'{DONOR_WELL.upper()} depth (m)')
    ax.set_ylabel(f'{TARGET_WELL.upper()} depth (m)')
    ax.set_title(f'A. Calibration scatter — r² = {r2:.3f}, RMSE = {rmse*1000:.1f} mm')
    ax.legend(loc='lower right', frameon=False)
    ax.grid(alpha=0.3)

    # Panel B: residuals over calibration window
    ax = axes[1]
    residuals = cal[TARGET_WELL].values - (alpha + beta * cal[DONOR_WELL].values)
    ax.plot(cal.index, residuals * 1000, color='#1f4e79', lw=1.1, marker='o',
            ms=3, alpha=0.8)
    ax.axhline(0, color='black', lw=0.5)
    ax.axhline(rmse * 1000, color='#cc0000', ls=':', lw=0.8, alpha=0.6,
               label=f'±RMSE  (±{rmse*1000:.0f} mm)')
    ax.axhline(-rmse * 1000, color='#cc0000', ls=':', lw=0.8, alpha=0.6)
    ax.set_xlabel('Date')
    ax.set_ylabel(f'{TARGET_WELL.upper()} − predicted (mm)')
    ax.set_title('B. Calibration residuals  (observed − predicted from donor)')
    ax.legend(loc='upper right', frameon=False)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Panel C: spliced time series
    ax = axes[2]
    mask_hind = spliced.index < target.index.min()
    mask_obs = ~mask_hind
    # Prediction band on hindcast portion
    ax.fill_between(spliced.index[mask_hind],
                    (spliced.values[mask_hind] - 1.96*rmse),
                    (spliced.values[mask_hind] + 1.96*rmse),
                    color='#cc0000', alpha=0.13, label='Hindcast ±95% pred. band')
    ax.plot(spliced.index[mask_hind], spliced.values[mask_hind],
            color='#cc0000', lw=1.2, label='Hindcast (synthetic)')
    ax.plot(spliced.index[mask_obs], spliced.values[mask_obs],
            color='#1f4e79', lw=1.2, label='Observed CEH34')
    # Mark splice point
    ax.axvline(target.index.min(), color='black', ls='--', lw=0.8,
               alpha=0.7, label=f'Splice  ({target.index.min().date()})')
    ax.axvline(INTERVENTION_DATE, color='#222', ls='-', lw=1.0,
               alpha=0.7, label='Clearfell  (Dec 2017)')
    ax.set_xlabel('Date')
    ax.set_ylabel('CEH34 depth (m)')
    ax.set_title(f'C. Spliced series — hindcast (2006-05 to {(target.index.min() - pd.Timedelta(days=1)).date()}) + observed')
    ax.legend(loc='lower left', frameon=False, fontsize=8)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    fig.suptitle(f'CEH34 donor-regression hindcast — donor = {DONOR_WELL.upper()} '
                 f'(Climate Control cluster)',
                 fontsize=13, y=1.00)
    fig.tight_layout()
    fig.savefig(OUT_DIAGNOSTIC, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"   -> Saved: {OUT_DIAGNOSTIC.name}")

    # ------------------------------------------------------------------
    # 7. Report numbers
    # ------------------------------------------------------------------
    print(f"\n7. Exporting report numbers...")

    rpt = ReportNumbers()
    rpt.add("CEH34_hindcast_donor", DONOR_WELL.upper(), unit="",
            note="Donor well identity for CEH34 hindcast")
    rpt.add("CEH34_hindcast_alpha", alpha, unit="m",
            note=f"OLS intercept (SE {alpha_se:.4f})")
    rpt.add("CEH34_hindcast_beta", beta, unit="",
            note=f"OLS slope (SE {beta_se:.4f})")
    rpt.add("CEH34_hindcast_r2", r2, unit="",
            note=f"OLS r² on {n_cal}-month pre-clearfell calibration")
    rpt.add("CEH34_hindcast_rmse_m", rmse, unit="m",
            note="Residual standard error")
    rpt.add("CEH34_hindcast_pred_interval_95_m", rmse * 1.96, unit="m",
            note="±1.96·RMSE 95% prediction band")
    rpt.add("CEH34_hindcast_n_calibration", n_cal, unit="months",
            note="Calibration sample size")
    rpt.add("CEH34_hindcast_n_synthetic", n_hindcast, unit="months",
            note="Synthetic-extension record length")
    pd.DataFrame(rpt.rows).to_csv(OUT_REPORT, index=False)
    print(f"   -> Saved: {OUT_REPORT.name}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("HINDCAST SUMMARY")
    print("=" * 72)
    print(f"  Target well : {TARGET_WELL.upper()}")
    print(f"  Donor well  : {DONOR_WELL.upper()}  (Climate Control — independent of Forest Control set)")
    print(f"  Calibration : {n_cal} months, pre-clearfell overlap")
    print(f"  Fit quality : r² = {r2:.3f}, RMSE = {rmse*1000:.1f} mm")
    print(f"  Hindcast    : {n_hindcast} months  "
          f"({hindcast_series.index.min().date()} → {hindcast_series.index.max().date()})")
    print(f"  Pred. band  : ±{rmse*1.96*1000:.0f} mm at 95% confidence per month")
    print("=" * 72)
    print("Script 10i complete.\n")


if __name__ == '__main__':
    main()
