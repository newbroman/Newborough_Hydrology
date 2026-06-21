r"""
====================================================================================
10f — ROBUSTNESS ANALYSES: SSM RESIDUAL & SYNTHETIC CONTROL
====================================================================================
Two independent robustness checks on the ANCOVA-BACI result (10a):

  1. SSM Residual Analysis (per-well forward prediction)
     - Calibrate SSM on pre-scraping data for each network well
     - Forward-iterate post-intervention to generate counterfactual trajectory
     - Residual = observed − predicted; normalise by subtracting control mean
     - Report era-mean residuals and Welch t-test (scraping vs felling eras)

  2. Synthetic Control (zone-level)
     - Construct a synthetic counterfactual from a donor pool of wells outside
       the 5-tier clearfell network
     - OLS weights fitted on pre-scraping baseline
     - Gap = observed zone mean − synthetic; test scraping→felling step

Both analyses use the 5-tier network from clearfell_common.  The SSM
residual uses model_utils.build_ssm_frame() for alignment.

Excluded wells:
  NW8 and NW8B are compromised and excluded from all analyses.

Dependencies:
  utils/clearfell_common.py — well lists, dates, data loading
  utils/model_utils.py      — build_ssm_frame()

Outputs:
  outputs/10_clearfell_baci/10f_01_ssm_residual_results.csv
  outputs/10_clearfell_baci/10f_02_synthetic_control_results.csv
  outputs/10_clearfell_baci/10f_report_numbers.csv
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as sp_stats

from utils.paths import (
    make_all_dirs, DIR_10,
    OUT_10F_SSM_RESIDUAL, OUT_10F_SYNTH_CTRL, OUT_10F_REPORT,
)
from utils.model_utils import build_ssm_frame
from utils.config import DRAINAGE_DATUM, HEADLINE_LAG
from utils.clearfell_common import (
    load_clearfell_data, print_network_summary,
    INTERVENTION_DATE, SCRAPING_DATE,
    IMPACT_WELLS, EDGE_WELLS,
    FOREST_CONTROL_WELLS, COASTAL_CONTROL_WELLS, CLIMATE_CONTROL_WELLS,
    ALL_NETWORK_WELLS,
    ReportNumbers,
)

__version__ = "1.0.0"

# ── Exclusions ──────────────────────────────────────────────────────────────
EXCLUDED_WELLS = {'nw8', 'nw8b'}

# Donor pool for synthetic control — wells outside the 17-well BACI network
# that have long records and no clearfell/scraping treatment.
# NW8/NW8B excluded (compromised).
SYNTH_DONOR_CANDIDATES = [
    'ceh1', 'ceh5', 'ceh6', 'ceh10', 'ceh11', 'ceh24',
]

# Minimum calibration months for SSM residual
MIN_CAL_MONTHS = 36


# ============================================================================
# UTILITIES
# ============================================================================

def _p_fmt(p):
    """Format p-value for console."""
    if pd.isna(p):
        return "N/A"
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def _p_sig(p):
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


# ============================================================================
# ROBUSTNESS 1 — SSM RESIDUAL (per-well forward prediction)
# ============================================================================

def ssm_residual_analysis(wells, climate, valid_tiers, rpt):
    """Calibrate SSM on pre-scraping data, iterate forward, normalise."""
    print("\n2. SSM Residual Analysis — per-well forward prediction...")
    print("   (calibrate on pre-scraping, iterate forward, normalise by control mean)")

    # Build zone map
    zone_map = {}
    for tier, wlist in valid_tiers.items():
        for w in wlist:
            zone_map[w] = tier

    # ── Per-well forward prediction ─────────────────────────────────────────
    resid_records = []
    resid_series_store = {}

    for w in ALL_NETWORK_WELLS:
        if w not in wells.columns or w in EXCLUDED_WELLS:
            continue
        zone = zone_map.get(w, "Unknown")

        h = wells[w].dropna()
        df_full = build_ssm_frame(h, climate, lag=HEADLINE_LAG,
                                  drainage_datum=DRAINAGE_DATUM)
        df_cal = df_full[df_full.index < SCRAPING_DATE]

        if len(df_cal) < MIN_CAL_MONTHS:
            print(f"   {w.upper():<8} [{zone:<14}] SKIP — {len(df_cal)} months < {MIN_CAL_MONTHS}")
            continue

        # Fit no-intercept OLS on calibration period
        X_cal = pd.DataFrame({
            'b1':  df_cal['P'].values,
            'b2': -df_cal['PET'].values,
            'b3': -df_cal['h_disp_prev'].values,
        })
        try:
            ols_cal = sm.OLS(df_cal['Delta_h'].values, X_cal).fit()
        except Exception:
            print(f"   {w.upper():<8} [{zone:<14}] SKIP — OLS failed")
            continue
        betas = ols_cal.params.values  # [b1, b2, b3]

        # Forward-iterate from last calibration observation
        post = df_full[df_full.index >= SCRAPING_DATE].copy()
        if len(post) < 6:
            continue

        h_pred = [float(df_cal['h'].iloc[-1])]  # seed with last cal value
        for _, row in post.iterrows():
            h_prev_pred = h_pred[-1]
            h_disp_pred = DRAINAGE_DATUM + h_prev_pred
            dh_pred = (betas[0] * row['P']
                       - betas[1] * row['PET']
                       - betas[2] * h_disp_pred)
            h_pred.append(h_prev_pred + dh_pred)

        # Residual = observed − predicted (drop seed)
        pred_series = pd.Series(h_pred[1:], index=post.index)
        obs_series = post['h']
        resid = obs_series - pred_series
        resid_series_store[w] = resid

        # Era means
        mask_scrape = ((resid.index >= SCRAPING_DATE) &
                       (resid.index < INTERVENTION_DATE))
        mask_fell = resid.index >= INTERVENTION_DATE
        scrape_mean = float(resid[mask_scrape].mean()) if mask_scrape.any() else np.nan
        fell_mean = float(resid[mask_fell].mean()) if mask_fell.any() else np.nan

        resid_records.append({
            'well': w.upper(), 'zone': zone,
            'scrape_mean': scrape_mean, 'fell_mean': fell_mean,
            'cal_months': len(df_cal), 'r2_cal': float(ols_cal.rsquared),
        })

    # ── Normalise by control mean residual ──────────────────────────────────
    ctrl_tiers = {'Forest Ctrl', 'Coastal Ctrl', 'Climate Ctrl'}
    ctrl_records = [r for r in resid_records if r['zone'] in ctrl_tiers]
    if ctrl_records:
        ctrl_scrape_mean = np.nanmean([r['scrape_mean'] for r in ctrl_records])
        ctrl_fell_mean = np.nanmean([r['fell_mean'] for r in ctrl_records])
    else:
        ctrl_scrape_mean = ctrl_fell_mean = 0.0

    # Build per-well normalised residuals and Welch t-test
    norm_rows = []
    for r in resid_records:
        w_key = r['well'].lower()
        norm_scrape = r['scrape_mean'] - ctrl_scrape_mean
        norm_fell = r['fell_mean'] - ctrl_fell_mean
        step = norm_fell - norm_scrape

        # Welch t-test on monthly normalised residuals
        p_val = np.nan
        if w_key in resid_series_store:
            rs = resid_series_store[w_key]
            # Subtract control mean series
            ctrl_series_list = [resid_series_store[cw]
                                for cw in resid_series_store
                                if zone_map.get(cw, '') in ctrl_tiers]
            if ctrl_series_list:
                ctrl_df = pd.DataFrame(ctrl_series_list).T
                ctrl_mean_ts = ctrl_df.mean(axis=1)
                norm_resid = rs.subtract(ctrl_mean_ts, fill_value=0)
            else:
                norm_resid = rs

            scrape_vals = norm_resid[
                (norm_resid.index >= SCRAPING_DATE) &
                (norm_resid.index < INTERVENTION_DATE)
            ].dropna()
            fell_vals = norm_resid[
                norm_resid.index >= INTERVENTION_DATE
            ].dropna()
            if len(scrape_vals) >= 3 and len(fell_vals) >= 3:
                _, p_val = sp_stats.ttest_ind(fell_vals, scrape_vals,
                                              equal_var=False)

        norm_rows.append({
            'Well': r['well'], 'Zone': r['zone'],
            'Cal_months': r['cal_months'],
            'R2_cal': round(r['r2_cal'], 3),
            'Norm_scrape_m': round(norm_scrape, 4),
            'Norm_fell_m': round(norm_fell, 4),
            'Step_m': round(step, 4),
            'P_value': round(float(p_val), 4) if pd.notna(p_val) else np.nan,
        })

        print(f"   {r['well']:<8} [{r['zone']:<14}] "
              f"scrape={norm_scrape:+.3f}  fell={norm_fell:+.3f}  "
              f"step={step:+.3f}  p={_p_fmt(p_val)} {_p_sig(p_val)}")

    # Zone means
    print()
    for tier in ['Impact', 'Edge', 'Forest Ctrl', 'Coastal Ctrl', 'Climate Ctrl']:
        zr = [r for r in norm_rows if r['Zone'] == tier]
        if zr:
            z_step = np.nanmean([r['Step_m'] for r in zr])
            z_p = np.nanmean([r['P_value'] for r in zr])
            print(f"   {'MEAN':8} [{tier:<14}] step={z_step:+.3f} m  (n={len(zr)})")
            rpt.add(f"SSM_Resid_{tier.replace(' ', '_')}_mean_step",
                    round(z_step, 4), "m", note=f"n={len(zr)}")

    # Export
    df_out = pd.DataFrame(norm_rows)
    df_out.to_csv(OUT_10F_SSM_RESIDUAL, index=False, float_format="%.4f")
    print(f"\n   -> Saved: {OUT_10F_SSM_RESIDUAL.name}")

    return df_out


# ============================================================================
# ROBUSTNESS 2 — SYNTHETIC CONTROL (zone-level)
# ============================================================================

def synthetic_control_analysis(wells, valid_tiers, rpt):
    """Construct synthetic counterfactual from donor pool outside the network."""
    print("\n3. Synthetic Control Analysis — zone-level...")

    # Identify available donors
    network_set = set(ALL_NETWORK_WELLS) | EXCLUDED_WELLS
    synth_donors = [w for w in SYNTH_DONOR_CANDIDATES
                    if w in wells.columns and w not in network_set]
    print(f"   Donor pool: {', '.join(w.upper() for w in synth_donors)} "
          f"(n={len(synth_donors)})")

    if len(synth_donors) < 3:
        print("   [SKIP] Fewer than 3 donors available — synthetic control not reliable")
        rpt.add("Synth_status", 0, "", note="Skipped — insufficient donors")
        pd.DataFrame().to_csv(OUT_10F_SYNTH_CTRL, index=False)
        return pd.DataFrame()

    donor_data = wells[synth_donors].dropna()

    synth_rows = []
    for zone_label, zone_wells in [("Impact", valid_tiers.get('Impact', [])),
                                    ("Edge", valid_tiers.get('Edge', []))]:
        avail = [w for w in zone_wells if w in wells.columns]
        if not avail:
            print(f"   {zone_label}: no wells available — skipping")
            continue

        zone_mean = wells[avail].mean(axis=1).dropna()
        common_idx = zone_mean.index.intersection(donor_data.index)

        baseline_mask = common_idx < SCRAPING_DATE
        baseline_idx = common_idx[baseline_mask]

        if len(baseline_idx) < 24:
            print(f"   {zone_label}: insufficient baseline ({len(baseline_idx)} months)")
            synth_rows.append({
                'Zone': zone_label, 'Gap_scrape_m': np.nan,
                'Gap_fell_m': np.nan, 'Step_m': np.nan, 'P_value': np.nan,
            })
            continue

        # Fit OLS: zone_mean = w₁·donor₁ + w₂·donor₂ + ...  (no intercept)
        X_syn = donor_data.loc[baseline_idx].values
        y_syn = zone_mean.loc[baseline_idx].values
        try:
            ols_syn = sm.OLS(y_syn, X_syn).fit()
            w_syn = ols_syn.params
        except Exception:
            print(f"   {zone_label}: OLS failed for synthetic control")
            synth_rows.append({
                'Zone': zone_label, 'Gap_scrape_m': np.nan,
                'Gap_fell_m': np.nan, 'Step_m': np.nan, 'P_value': np.nan,
            })
            continue

        # Construct synthetic counterfactual over full common period
        synthetic = donor_data.loc[common_idx].values @ w_syn
        gap = zone_mean.loc[common_idx].values - synthetic
        gap_series = pd.Series(gap, index=common_idx)

        gap_scrape = gap_series[
            (gap_series.index >= SCRAPING_DATE) &
            (gap_series.index < INTERVENTION_DATE)
        ]
        gap_fell = gap_series[gap_series.index >= INTERVENTION_DATE]

        mean_gap_scrape = float(gap_scrape.mean()) if len(gap_scrape) > 0 else np.nan
        mean_gap_fell = float(gap_fell.mean()) if len(gap_fell) > 0 else np.nan
        step = (mean_gap_fell - mean_gap_scrape
                if pd.notna(mean_gap_scrape) and pd.notna(mean_gap_fell)
                else np.nan)

        p_val = np.nan
        if len(gap_scrape) >= 3 and len(gap_fell) >= 3:
            _, p_val = sp_stats.ttest_ind(gap_fell, gap_scrape, equal_var=False)

        synth_rows.append({
            'Zone': zone_label,
            'N_donors': len(synth_donors),
            'Baseline_months': len(baseline_idx),
            'Gap_scrape_m': round(mean_gap_scrape, 4),
            'Gap_fell_m': round(mean_gap_fell, 4),
            'Step_m': round(step, 4) if pd.notna(step) else np.nan,
            'P_value': round(float(p_val), 4) if pd.notna(p_val) else np.nan,
        })

        print(f"   {zone_label}: scrape gap={mean_gap_scrape:+.3f}  "
              f"fell gap={mean_gap_fell:+.3f}  "
              f"step={step:+.3f}  p={_p_fmt(p_val)} {_p_sig(p_val)}")

        rpt.add(f"Synth_{zone_label}_step", round(step, 4), "m",
                note=f"p={_p_fmt(p_val)}, n_donors={len(synth_donors)}")

    df_out = pd.DataFrame(synth_rows)
    df_out.to_csv(OUT_10F_SYNTH_CTRL, index=False, float_format="%.4f")
    print(f"\n   -> Saved: {OUT_10F_SYNTH_CTRL.name}")

    return df_out


# ============================================================================
# MAIN
# ============================================================================

def main():
    make_all_dirs()

    print("=" * 72)
    print("SCRIPT 10f — ROBUSTNESS ANALYSES")
    print("=" * 72)

    # ── Load data ────────────────────────────────────────────────────────────
    print("\n1. Loading data...")
    wells, climate, master, well_locations, valid_tiers = load_clearfell_data()
    print_network_summary(valid_tiers)

    rpt = ReportNumbers()

    # ── Run analyses ─────────────────────────────────────────────────────────
    df_resid = ssm_residual_analysis(wells, climate, valid_tiers, rpt)
    df_synth = synthetic_control_analysis(wells, valid_tiers, rpt)

    # ── Export report numbers ────────────────────────────────────────────────
    rpt.save(OUT_10F_REPORT)

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("SCRIPT 10f COMPLETE")
    print("=" * 72)
    print(f"  SSM Residual:     {OUT_10F_SSM_RESIDUAL.name} ({len(df_resid)} wells)")
    print(f"  Synthetic Control: {OUT_10F_SYNTH_CTRL.name} ({len(df_synth)} zones)")
    print(f"  Report numbers:   {OUT_10F_REPORT.name} ({len(rpt.rows)} entries)")
    print("=" * 72)


if __name__ == '__main__':
    main()
