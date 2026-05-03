"""
====================================================================================
THE OMNIBUS SLACK SCRAPING ANALYSIS: HIERARCHICAL NESTED CONTROL EDITION
====================================================================================
Purpose:
Evaluates slack scraping using a Hierarchical BACI design.
Tier 1: Evaluates Local Controls vs. the Regional Mean (Proves Coastal Drain).
Tier 2: Evaluates Impact Wells vs. Local Controls (Proves Pure Scraping Success).

Outputs:
CSVs: 01 to 04
Plots: 05 to 10
====================================================================================
"""

__version__ = "1.0.0"  # Hollingham (2026) — last revised 2026-04-10

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
from utils.paths import (
    make_all_dirs, DATA_CLIMATE_RAW, DATA_WELLS_RAW,
    INT_WELLS_CLEAN, INT_WELLS_EXTENDED,
    OUT_09_FULL_PARAMS,
    OUT_09_BETA3_SIG,
    OUT_09_BACI_SHIFTS,
    OUT_09_NET_BENEFITS,
    OUT_09_TABLE4_SUMMARY,
    OUT_09_TIER1_DRIFT,
    OUT_09_TIER2_SIGNAL,
    OUT_09_BETA3_CI,
    OUT_09_ROBUSTNESS,
    OUT_09_REPORT_NUMBERS,
    INT_CLIMATE,
    DIR_09
)
from utils.data_utils import parse_met_date, clean_well_series, calculate_cusum
from utils.config import DRAINAGE_DATUM, HEADLINE_LAG
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.api as sm
import sys
import os
from pathlib import Path

def format_p_value(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "<0.001"
    return f"{p:.5f}"


def significance_stars(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def export_table4_beta3_summary(significance_results: list[dict]) -> None:
    """Export manuscript-ready Table 4 from era-specific beta_3 significance rows."""
    if not significance_results:
        pd.DataFrame(columns=["Well", "Role", "Era", "beta_3", "CI_95", "p_value", "Sig"]).to_csv(
            OUT_09_TABLE4_SUMMARY, index=False
        )
        return

    df = pd.DataFrame(significance_results).copy()
    df["Well"] = df["Well"].astype(str).str.upper()

    role_map = {
        "CEH36": "Treatment",
        "CEH18": "Treatment",
        "CEH21": "Treatment",
        "CEH4": "Control",
        "CEH22": "Control",
    }
    era_map = {
        "1_Baseline": "Baseline",
        "2_Pure_Scraping": "Pure Scraping",
        "3_Felling_Pulse": "Felling Pulse",
        "2_Felling_Pulse": "Felling Pulse",
        "2_Coastal_Drawdown": "Coastal Drawdown",
        "3_After_Scraping": "After Scraping",
    }
    well_order = ["CEH36", "CEH18", "CEH21", "CEH4", "CEH22"]
    era_order = {
        "1_Baseline": 1,
        "2_Pure_Scraping": 2,
        "2_Felling_Pulse": 2,
        "2_Coastal_Drawdown": 2,
        "3_Felling_Pulse": 3,
        "3_After_Scraping": 3,
    }

    df = df[df["Well"].isin(well_order)].copy()
    df["Role"] = df["Well"].map(role_map)
    df["Era_Label"] = df["Era"].map(era_map).fillna(df["Era"].astype(str).str.replace("_", " ", regex=False))
    df["CI_95"] = df.apply(lambda r: f"[{r['Conf_Low']:.3f}, {r['Conf_High']:.3f}]", axis=1)
    df["p_value"] = df["P_Value"].apply(format_p_value)
    df["Sig"] = df["P_Value"].apply(significance_stars)
    df["beta_3"] = df["beta_3_drainage"].round(3)
    df["well_rank"] = pd.Categorical(df["Well"], categories=well_order, ordered=True)
    df["era_rank"] = df["Era"].map(era_order).fillna(99)
    df = df.sort_values(["well_rank", "era_rank", "Era_Label"])

    out = df[["Well", "Role", "Era_Label", "beta_3", "CI_95", "p_value", "Sig"]].rename(
        columns={"Era_Label": "Era"}
    )
    out.to_csv(OUT_09_TABLE4_SUMMARY, index=False)


# ====================================================================================
# PATH CONFIGURATION
# ====================================================================================



make_all_dirs()

# Style adjustments for publication
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


# ==========================================
# 1. SETUP EXPERIMENTS & ERAS
# ==========================================
controls = ['ceh9', 'nw8', 'nw8b', 'nw5', 'nw6', 'nw7']

date_2015 = pd.to_datetime('2015-04-01')
date_felling = pd.to_datetime('2017-12-01')  # corrected from 2018-12-01
date_2023 = pd.to_datetime('2023-10-01')

print("1. Loading Climate and Well Data...")
try:
    # Climate — read from pipeline intermediate (Script 01 output).
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    climate = climate.sort_index()

    # Wells — read from pipeline intermediates (Script 01 output).
    # Merge reference and extended networks to get all scraping and control wells.
    wells_main = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells_main.columns = wells_main.columns.str.lower().str.replace(' ', '')
    if INT_WELLS_EXTENDED.exists():
        wells_ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
        wells_ext.columns = wells_ext.columns.str.lower().str.replace(' ', '')
        new_cols = [c for c in wells_ext.columns if c not in wells_main.columns]
        wells = pd.concat([wells_main, wells_ext[new_cols]], axis=1)
    else:
        wells = wells_main

    valid_controls = [w for w in controls if w in wells.columns]
except Exception as e:
    print(f"Data error: {e}")
    sys.exit()

# Hierarchical Well Configuration
well_eras = {
    'ceh36': { # Central Impact
        'Exp': '2015_Scraping_with_KnockOn',
        'Eras': {
            '1_Baseline': lambda df: df[df.index < date_2015],
            '2_Pure_Scraping': lambda df: df[(df.index >= date_2015) & (df.index < date_felling)],
            '3_Felling_Pulse': lambda df: df[df.index >= date_felling]
        }
    },
    'ceh4': { # Central Control (Tracks the 2015/2018 timeline against region)
        'Exp': 'Control_Tracking',
        'Eras': {
            '1_Baseline': lambda df: df[df.index < date_2015],
            '2_Pure_Scraping': lambda df: df[(df.index >= date_2015) & (df.index < date_felling)],
            '3_Felling_Pulse': lambda df: df[df.index >= date_felling]
        }
    },
    'ceh18': { # Boundary Impact
        'Exp': '2023_Scraping_with_Felling_Pulse',
        'Eras': {
            '1_Baseline': lambda df: df[df.index < date_felling],
            '2_Felling_Pulse': lambda df: df[(df.index >= date_felling) & (df.index < date_2023)],
            '3_After_Scraping': lambda df: df[df.index >= date_2023]
        }
    },
    'ceh21': { # Coastal Impact
        'Exp': 'Coastal_Refuge_Scraping',
        'Eras': {
            '1_Baseline': lambda df: df[df.index < date_felling],
            '2_Coastal_Drawdown': lambda df: df[(df.index >= date_felling) & (df.index < date_2023)],
            '3_After_Scraping': lambda df: df[df.index >= date_2023]
        }
    },
    'ceh22': { # Coastal Control
        'Exp': 'Coastal_Control_Tracking',
        'Eras': {
            '1_Baseline': lambda df: df[df.index < date_felling],
            '2_Coastal_Drawdown': lambda df: df[(df.index >= date_felling) & (df.index < date_2023)],
            '3_After_Scraping': lambda df: df[df.index >= date_2023]
        }
    }
}

colors = {'1_Baseline': '#009E73', '2_Pure_Scraping': '#56B4E9', '3_Felling_Pulse': '#CC79A7', 
          '2_Felling_Pulse': '#CC79A7', '2_Coastal_Drawdown': '#E69F00', '3_After_Scraping': '#D55E00'}
markers = {'1_Baseline': 'o', '2_Pure_Scraping': 's', '3_Felling_Pulse': '^', 
           '2_Felling_Pulse': '^', '2_Coastal_Drawdown': 'v', '3_After_Scraping': 'D'}
fill_styles = colors.copy()
fill_styles['1_Baseline'] = 'none' # Keep baseline hollow for contrast
linestyles = {'1_Baseline': ':', '2_Pure_Scraping': '--', '3_Felling_Pulse': '-', 
              '2_Felling_Pulse': '-', '2_Coastal_Drawdown': '--', '3_After_Scraping': '-.'}

# ==========================================
# 2. RUN PAIRED STATISTICAL ANALYSIS
# ==========================================
print("2. Running Master Statistical Analysis...")
full_params_results = []
significance_results = []
baci_results = []
plot_data = {}

control_mean_regional = wells[valid_controls].mean(axis=1)

# Hierarchical Pairings
pairings = {
    'ceh36': 'ceh4',
    'ceh18': 'ceh4',
    'ceh21': 'ceh22',
    'ceh4': 'Regional Mean',   # Controls get evaluated against the macro trend
    'ceh22': 'Regional Mean'
}

for well, config in well_eras.items():
    if well not in wells.columns: continue
    
    if well in pairings and pairings[well] in wells.columns:
        baseline = wells[pairings[well]]
        control_label = pairings[well].upper()
    else:
        baseline = control_mean_regional
        control_label = "Regional Mean"

    baci_series = (wells[well] - baseline).dropna()
    era_baci_means = {}
    
    df = wells[well].to_frame(name='h').join(climate[['P_m', 'PET']], how='inner')
    df['P_m_lag1'] = df['P_m'].shift(HEADLINE_LAG)  # HEADLINE_LAG from config
    df['h_prev'] = df['h'].shift(1)
    df['Delta_h'] = df['h'] - df['h_prev']
    df = df.dropna()

    df['h_disp_prev'] = DRAINAGE_DATUM + df['h_prev']  # displacement above drainage datum
    X_base = pd.DataFrame({'beta_1_recharge': df['P_m_lag1'], 'beta_2_atmospheric_draw': -df['PET'], 'beta_3_drainage': -df['h_disp_prev']})
    res_base = sm.OLS(df['Delta_h'], X_base).fit()
    b1, b2 = res_base.params['beta_1_recharge'], res_base.params['beta_2_atmospheric_draw']
    df['Drainage_Component'] = df['Delta_h'] - (b1 * df['P_m_lag1']) - (b2 * -df['PET'])
    df['neg_h_disp_prev'] = -df['h_disp_prev']
    
    era1_key = list(config['Eras'].keys())[0]
    era1_baci = config['Eras'][era1_key](baci_series)
    baseline_mean = era1_baci.mean() if not era1_baci.empty else 0
    cusum_series = calculate_cusum(baci_series, baseline_mean)
    
    plot_data[well] = {'df': df, 'baci': baci_series, 'cusum': cusum_series, 'means': {}, 'config': config, 'control': control_label}

    for era_name, filter_func in config['Eras'].items():
        baci_sub = filter_func(baci_series)
        mean_val = baci_sub.mean() if not baci_sub.empty else np.nan
        era_baci_means[era_name] = mean_val
        plot_data[well]['means'][era_name] = mean_val
        
        sub = filter_func(df)
        if len(sub) > 6:
            X_full = pd.DataFrame({'beta_1_recharge': sub['P_m_lag1'], 'beta_2_atmospheric_draw': -sub['PET'], 'beta_3_drainage': -sub['h_disp_prev']})
            model_full = sm.OLS(sub['Delta_h'], X_full).fit()
            
            full_params_results.append({
                'Well': well.upper(), 'Era': era_name,
                'beta_1_recharge': round(model_full.params['beta_1_recharge'], 3),
                'beta_2_atmospheric_draw': round(model_full.params['beta_2_atmospheric_draw'], 3),
                'beta_3_drainage': round(model_full.params['beta_3_drainage'], 3)
            })
            
            X_iso = sm.add_constant(sub['neg_h_disp_prev'])
            model_iso = sm.OLS(sub['Drainage_Component'], X_iso).fit()
            ci = model_iso.conf_int().loc['neg_h_disp_prev']
            significance_results.append({
                'Well': well.upper(), 'Era': era_name,
                'beta_3_drainage': model_iso.params['neg_h_disp_prev'],
                'P_Value': model_iso.pvalues['neg_h_disp_prev'],
                'Conf_Low': ci[0], 'Conf_High': ci[1]
            })

    keys = list(era_baci_means.keys())
    for i in range(1, len(keys)):
        shift_name = keys[i].split('_', 1)[1]
        baci_results.append({
            'Well': well.upper(), 'Shift': shift_name, 
            'Delta_m': era_baci_means[keys[i]] - era_baci_means[keys[i-1]],
            'Control': control_label
        })

# Net Benefits Calculation
benchmark_well = 'ceh21'
impact_wells = ['ceh36', 'ceh18']
net_summary = []
if benchmark_well in plot_data:
    for w in impact_wells:
        if w in plot_data:
            relative_benefit = plot_data[w]['baci'] - plot_data[benchmark_well]['baci']
            era_keys = list(plot_data[w]['config']['Eras'].keys())
            for i in range(1, len(era_keys)):
                before = plot_data[w]['config']['Eras'][era_keys[i-1]](relative_benefit)
                after = plot_data[w]['config']['Eras'][era_keys[i]](relative_benefit)
                net_summary.append({
                    'Well': w.upper(), 'Shift': era_keys[i].split('_', 1)[1],
                    'Net_Benefit_m': round(after.mean() - before.mean(), 4)
                })

# ==========================================
# 3. EXPORT CSV DATA (01 to 04)
# ==========================================
print("3. Exporting CSV files...")
pd.DataFrame(full_params_results).to_csv(OUT_09_FULL_PARAMS, index=False)
pd.DataFrame(significance_results).to_csv(OUT_09_BETA3_SIG, index=False)
pd.DataFrame(baci_results).to_csv(OUT_09_BACI_SHIFTS, index=False)
pd.DataFrame(net_summary).to_csv(OUT_09_NET_BENEFITS, index=False)
export_table4_beta3_summary(significance_results)

# ==========================================
# 4. GENERATE THE VISUAL SUITE (05 to 07)
# ==========================================
print("4. Generating the Visual Suite...")

# Define tier wells
tier1_wells = ['ceh4', 'ceh22']  # Controls
tier2_wells = ['ceh36', 'ceh18', 'ceh21']  # Impacts

# ==========================================
# SCRAPE_05: Tier 1 - Background Drift for Controls
# ==========================================
# Collect all series for consistent y-limits
all_baci_tier1 = []
all_cusum_tier1 = []
for well in tier1_wells:
    if well in plot_data:
        all_baci_tier1.append(plot_data[well]['baci'])
        all_cusum_tier1.append(plot_data[well]['cusum'])

if all_baci_tier1:
    baci_min = min(s.min() for s in all_baci_tier1)
    baci_max = max(s.max() for s in all_baci_tier1)
    baci_ylim = (baci_min - 0.05, baci_max + 0.05)  # Small padding
else:
    baci_ylim = (-0.5, 0.5)

if all_cusum_tier1:
    cusum_min = min(s.min() for s in all_cusum_tier1)
    cusum_max = max(s.max() for s in all_cusum_tier1)
    cusum_ylim = (cusum_min - 0.05, cusum_max + 0.05)
else:
    cusum_ylim = (-0.5, 0.5)

fig1, axes1 = plt.subplots(2, 2, figsize=(16, 12), dpi=300)

for i, well in enumerate(tier1_wells):
    if well not in plot_data:
        continue
    data = plot_data[well]
    config = data['config']
    baci_series = data['baci']
    cusum_series = data['cusum']
    control_name = data['control']

    # Top row: BACI Timelines
    ax_baci = axes1[0, i]
    ax_baci.axhline(0, color='black', linewidth=1.5, linestyle='-', alpha=0.3)
    for era_name, filter_func in config['Eras'].items():
        era_data = filter_func(baci_series)
        if era_data.empty:
            continue
        ax_baci.plot(era_data.index, era_data, color=colors[era_name],
                     linestyle=linestyles[era_name], alpha=0.8, linewidth=1.5)
        ax_baci.axhline(data['means'][era_name], color=colors[era_name],
                        linestyle='--', linewidth=2, alpha=0.9)
    ax_baci.set_ylim(baci_ylim)
    if i == 0:  # Only leftmost
        ax_baci.set_ylabel('Δ Water Level (m)\n[CEH WELL - Regional Mean]', fontweight='bold')
    ax_baci.set_title(f"{well.upper()} Performance", fontsize=12, pad=10)
    ax_baci.grid(True, which='both', linestyle=':', alpha=0.4)

    # Bottom row: CUSUM
    ax_cusum = axes1[1, i]
    ax_cusum.axhline(0, color='black', linewidth=1.5, linestyle='-', alpha=0.3)
    for era_name, filter_func in config['Eras'].items():
        era_cusum = filter_func(cusum_series)
        if era_cusum.empty:
            continue
        ax_cusum.fill_between(era_cusum.index, era_cusum, color=colors[era_name], alpha=0.2)
        clean_label = era_name.split('_', 1)[1].replace('_', ' ')
        ax_cusum.plot(era_cusum.index, era_cusum, color=colors[era_name],
                      linewidth=2.5, marker=markers[era_name], markevery=4, label=clean_label)
    ax_cusum.set_ylim(cusum_ylim)
    if i == 0:  # Only leftmost
        ax_cusum.set_ylabel('Cumulative Sum (m)\n[Relative Success]', fontweight='bold')
    ax_cusum.grid(True, which='both', linestyle=':', alpha=0.4)

# Set common x-axis range starting from 2006
min_date = pd.to_datetime('2006-01-01')
max_date = max(plot_data[well]['baci'].index.max() for well in tier1_wells if well in plot_data)
for ax in axes1.flatten():
    ax.set_xlim(min_date, max_date)

# Set x-axis for all subplots: every 2 years
for ax in axes1.flatten():
    ax.xaxis.set_major_locator(mdates.YearLocator(2))  # Every 2 years
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax.get_xticklabels(), rotation=0)

# Hide x-axis labels for top row
for ax in axes1[0, :]:
    ax.set_xticklabels([])

# Collect all unique labels from all subplots in the figure
handles, labels = [], []
for ax in axes1.flat:
    h, l = ax.get_legend_handles_labels()
    handles.extend(h)
    labels.extend(l)

# Strip the numbers (e.g., '2_') from the labels and deduplicate
clean_labels = [lbl.split('_', 1)[1].replace('_', ' ') if '_' in lbl else lbl for lbl in labels]
by_label = dict(zip(clean_labels, handles))

axes1[1, 0].legend(by_label.values(), by_label.keys(), loc='lower left', frameon=True)

plt.tight_layout()
fig1.suptitle("Tier 1 - Background Environmental Drift (CUSUM Analysis)", fontsize=16, fontweight='bold', y=1.05)
plt.savefig(OUT_09_TIER1_DRIFT, bbox_inches='tight', dpi=300)

plt.close()

# Export final Tier 1 CUSUM values for precise citation (after all uses of tier1_wells)
if all_cusum_tier1:
    tier1_cusum_final = {well: float(plot_data[well]['cusum'].iloc[-1]) for well in tier1_wells if well in plot_data}
    out_path = DIR_09 / "09_tier1_final_cusum.csv"
    pd.DataFrame.from_dict(tier1_cusum_final, orient='index', columns=['Final_Tier1_CUSUM']).to_csv(out_path)

# ==========================================
# SCRAPE_06: Tier 2 - Scraping Signal for Impacts
# ==========================================
# Collect all series for consistent y-limits
all_baci_tier2 = []
all_cusum_tier2 = []
for well in tier2_wells:
    if well in plot_data:
        all_baci_tier2.append(plot_data[well]['baci'])
        all_cusum_tier2.append(plot_data[well]['cusum'])

if all_baci_tier2:
    baci_min = min(s.min() for s in all_baci_tier2)
    baci_max = max(s.max() for s in all_baci_tier2)
    baci_ylim = (baci_min - 0.05, baci_max + 0.05)  # Small padding
else:
    baci_ylim = (-0.5, 0.5)

if all_cusum_tier2:
    cusum_min = min(s.min() for s in all_cusum_tier2)
    cusum_max = max(s.max() for s in all_cusum_tier2)
    cusum_ylim = (cusum_min - 0.05, cusum_max + 0.05)
else:
    cusum_ylim = (-0.5, 0.5)

fig2, axes2 = plt.subplots(3, 2, figsize=(14, 18), dpi=300)

for i, well in enumerate(tier2_wells):
    if well not in plot_data:
        continue
    data = plot_data[well]
    config = data['config']
    baci_series = data['baci']
    cusum_series = data['cusum']
    control_name = data['control']

    # BACI Timeline (top of each pair)
    ax_baci = axes2[i, 0]
    ax_baci.axhline(0, color='black', linewidth=1.5, linestyle='-', alpha=0.3)
    for era_name, filter_func in config['Eras'].items():
        era_data = filter_func(baci_series)
        if era_data.empty:
            continue
        ax_baci.plot(era_data.index, era_data, color=colors[era_name],
                     linestyle=linestyles[era_name], alpha=0.8, linewidth=1.5)
        ax_baci.axhline(data['means'][era_name], color=colors[era_name],
                        linestyle='--', linewidth=2, alpha=0.9)
    ax_baci.set_ylim(baci_ylim)
    ax_baci.set_ylabel('Δ Water Level (m)\n[CEH WELL - CEH4]', fontweight='bold')
    ax_baci.set_title(f"{well.upper()} Performance", fontsize=12, pad=10)
    ax_baci.grid(True, which='both', linestyle=':', alpha=0.4)

    # CUSUM (bottom of each pair)
    ax_cusum = axes2[i, 1]
    ax_cusum.axhline(0, color='black', linewidth=1.5, linestyle='-', alpha=0.3)
    for era_name, filter_func in config['Eras'].items():
        era_cusum = filter_func(cusum_series)
        if era_cusum.empty:
            continue
        ax_cusum.fill_between(era_cusum.index, era_cusum, color=colors[era_name], alpha=0.2)
        clean_label = era_name.split('_', 1)[1].replace('_', ' ')
        ax_cusum.plot(era_cusum.index, era_cusum, color=colors[era_name],
                      linewidth=2.5, marker=markers[era_name], markevery=4, label=clean_label)
    ax_cusum.set_ylim(cusum_ylim)
    ax_cusum.set_ylabel('Cumulative Sum (m)\n[Relative Success]', fontweight='bold')
    ax_cusum.grid(True, which='both', linestyle=':', alpha=0.4)
for ax in axes2[1, :]:
    ax.xaxis.set_major_locator(mdates.YearLocator(2))  # Every 2 years
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax.get_xticklabels(), rotation=0)

# Collect all unique labels from all subplots in the figure
handles, labels = [], []
for ax in axes2.flat:
    h, l = ax.get_legend_handles_labels()
    handles.extend(h)
    labels.extend(l)

# Strip the numbers (e.g., '2_') from the labels and deduplicate
clean_labels = [lbl.split('_', 1)[1].replace('_', ' ') if '_' in lbl else lbl for lbl in labels]
by_label = dict(zip(clean_labels, handles))

axes2[1, 0].legend(by_label.values(), by_label.keys(), loc='upper left', frameon=True)

plt.tight_layout()
fig2.suptitle("Tier 2 - Pure Scraping Signal (Paired CUSUM Analysis)", fontsize=16, fontweight='bold', y=1.05)
plt.savefig(OUT_09_TIER2_SIGNAL, bbox_inches='tight', dpi=300)
plt.close()

# ==========================================
# SCRAPE_07: Beta 3 Confidence Intervals
# ==========================================
df_sig = pd.DataFrame(significance_results)
if not df_sig.empty:
    fig3, ax3 = plt.subplots(figsize=(10, 6), dpi=300)
    
    wells_to_plot = ['CEH36', 'CEH18', 'CEH21']
    df_sig_filtered = df_sig[df_sig['Well'].isin(wells_to_plot)]
    
    wells_plotted = df_sig_filtered['Well'].unique()
    offsets = [-0.15, 0, 0.15]
    
    for i, w in enumerate(wells_plotted):
        well_data = df_sig_filtered[df_sig_filtered['Well'] == w]
        for j, (_, row) in enumerate(well_data.iterrows()):
            era = row['Era']
            x_pos = i + offsets[j]
            err_low = row['beta_3_drainage'] - row['Conf_Low']
            err_high = row['Conf_High'] - row['beta_3_drainage']
            clean_label = era.split('_', 1)[1].replace('_', ' ')
            ax3.errorbar(x_pos, row['beta_3_drainage'], yerr=[[err_low], [err_high]],
                        fmt=markers[era], color=colors[era], markerfacecolor=fill_styles[era], 
                        markeredgecolor=colors[era], markersize=8, capsize=5, 
                        label=clean_label)

    ax3.set_xticks(range(len(wells_plotted)))
    ax3.set_xticklabels(wells_plotted)
    ax3.set_ylabel(r'Drainage Coefficient ($\beta_3$)')
    ax3.set_title(r'Structural Repair ($\beta_3$ Shifts with 95% CI)', fontweight='bold')
    # Sort by Era index
    era_order = {'1_Baseline': 0, '2_Pure_Scraping': 1, '2_Felling_Pulse': 1, 
                 '2_Coastal_Drawdown': 1, '3_Felling_Pulse': 2, '3_After_Scraping': 2}
    handles, labels = ax3.get_legend_handles_labels()
    # Sort by era_order
    sorted_items = sorted(zip(labels, handles), key=lambda x: era_order.get(x[0], 99))
    sorted_labels, sorted_handles = zip(*sorted_items)
    by_label = dict(zip(sorted_labels, sorted_handles))
    ax3.legend(by_label.values(), by_label.keys(), title="Eras")
    ax3.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(OUT_09_BETA3_CI, bbox_inches='tight', dpi=300)
    plt.close()

print("\n--- Absolute Paired-BACI Shifts ---")
print(pd.DataFrame(baci_results).to_string(index=False))

# ====================================================================================
# CEH36 SCRAPING ROBUSTNESS FIGURE — three independent methods
# ====================================================================================
# Three independent estimates of the CEH36 Pure Scraping era step change:
#   (1) Raw BACI: CEH36 minus CEH4 (existing approach in main analysis)
#   (2) Synthetic control: CEH36 minus a weighted composite of donor wells
#   (3) SSM forward residual: observed minus model prediction calibrated on
#       the pre-scraping baseline period
#
# Method convergence supports the inference that the +0.13 m benefit at CEH36
# is not an artefact of CEH4's own progressive deepening. Method divergence
# is interpretable: the raw BACI and synthetic control measure the relative
# topographic benefit, while the SSM residual measures deviation from a
# climate-driven trajectory and so reflects whether the benefit is
# structural (permanent ground surface lowering) or hydrodynamic (sustained
# departure from climate forecast).
#
# Convention: raw well depths are negative below ground; a POSITIVE step
# value indicates a beneficial shift (water table closer to surface). This
# matches the convention used elsewhere in Script 09.
print("\nGenerating CEH36 scraping robustness figure...")
try:
    import matplotlib.patches as mpatches
    from matplotlib.lines import Line2D

    # Donor-well pool for synthetic control: long-record wells geographically
    # outside the scraping management footprint, excluding CEH36 (target),
    # CEH4 (already used as raw BACI control), and the felling-zone wells
    # (which underwent their own intervention).
    #
    # CEH23 (C1) and CEH28 (C2) were replaced by CEH11 (C1) and CEH24 (C2)
    # because CEH23 has a 17-month field gap (Oct 2016–Feb 2018) spanning
    # the Pure Scraping/felling boundary, and CEH28 has a 20-month gap
    # (Oct 2018–May 2020) covering the first two post-felling years.
    # CEH11 and CEH24 have complete records through all analysis eras and
    # belong to the same clusters as the wells they replace.
    _donor_candidates = [
        'ceh1', 'ceh2', 'ceh5', 'ceh6', 'ceh9', 'ceh11', 'ceh16',
        'ceh17', 'ceh19', 'ceh22', 'ceh24',
    ]
    _donors = [w for w in _donor_candidates if w in wells.columns]

    # Era boundaries for CEH36
    _baseline_mask = wells.index < date_2015
    _scraping_mask = (wells.index >= date_2015) & (wells.index < date_felling)
    _felling_mask  = (wells.index >= date_felling) & (wells.index < date_2023)
    _post23_mask   = wells.index >= date_2023

    # ── (1) Raw BACI: CEH36 vs CEH4 ───────────────────────────────────────
    _ceh36 = wells['ceh36']
    _ceh4  = wells['ceh4']
    _gap_raw = _ceh36 - _ceh4

    _raw_baseline = _gap_raw[_baseline_mask].mean()
    _raw_scraping = _gap_raw[_scraping_mask].mean()
    _raw_step     = _raw_scraping - _raw_baseline

    # ── (2) Synthetic control: weighted composite from donor wells ────────
    # Weights computed by OLS on the baseline period: which combination of
    # donors best matches CEH36 before scraping?
    _baseline_X = wells.loc[_baseline_mask, _donors].dropna()
    _baseline_y = _ceh36.loc[_baseline_X.index]
    _valid_idx  = _baseline_y.notna()
    _baseline_X = _baseline_X.loc[_valid_idx]
    _baseline_y = _baseline_y.loc[_valid_idx]

    if len(_baseline_X) >= 24:
        # OLS without intercept — keeps the synthetic on the same depth datum
        _ols = sm.OLS(_baseline_y.values, _baseline_X.values).fit()
        _weights = pd.Series(_ols.params, index=_donors)

        # Apply weights across full record to construct the synthetic series
        _synthetic = wells[_donors].dot(_weights)
        _gap_syn   = _ceh36 - _synthetic

        _syn_baseline = _gap_syn[_baseline_mask].mean()
        _syn_scraping = _gap_syn[_scraping_mask].mean()
        _syn_step     = _syn_scraping - _syn_baseline
    else:
        _gap_syn  = pd.Series(np.nan, index=_ceh36.index)
        _syn_step = np.nan
        _weights  = pd.Series(dtype=float)
        print(f"  [WARNING] Insufficient baseline overlap for synthetic control "
              f"({len(_baseline_X)} months, need >=24)")

    # ── (3) SSM forward residual ──────────────────────────────────────────
    # Calibrate Δh = β₁·P − β₂·PET − β₃·h_prev on the baseline period at CEH36,
    # then run forward through scraping/felling/post-2023 eras and compare
    # observed vs predicted.
    _ts = pd.DataFrame({
        'h':   _ceh36,
        'P':   climate['P_m'] * 1000.0,    # m -> mm
        'PET': climate['PET'] * 1000.0,
    }).dropna()

    # Rainfall lag consistent with HEADLINE_LAG from config.
    _ts['P_lag1'] = _ts['P'].shift(HEADLINE_LAG)

    _ts_base = _ts[_ts.index < date_2015].copy()
    _ts_base['h_prev'] = _ts_base['h'].shift(1)
    _ts_base['dh']     = _ts_base['h'] - _ts_base['h_prev']
    _ts_base = _ts_base.dropna()

    if len(_ts_base) >= 36:
        _X_fit = pd.DataFrame({
            'P':       _ts_base['P_lag1'],
            'PET_neg': -_ts_base['PET'],
            'h_neg':   -(DRAINAGE_DATUM + _ts_base['h_prev']),
        })
        _model = sm.OLS(_ts_base['dh'].values, _X_fit.values).fit()
        _b1, _b2, _b3 = _model.params

        # Forward simulation from end-of-baseline through end-of-record.
        # Uses P_lag1 (lagged rainfall per HEADLINE_LAG) at each step.
        _ts_fwd = _ts.copy()
        _ts_fwd['h_pred'] = np.nan
        _idx_list = list(_ts_fwd.index)
        # Initialise at last observed baseline value
        _last_base_dt = _ts_fwd.index[_ts_fwd.index < date_2015].max()
        if pd.notna(_last_base_dt):
            _h_pred = _ts_fwd.loc[_last_base_dt, 'h']
            _ts_fwd.loc[_last_base_dt, 'h_pred'] = _h_pred
            for _dt in _idx_list:
                if _dt <= _last_base_dt:
                    continue
                _P_t   = _ts_fwd.loc[_dt, 'P_lag1']
                _PET_t = _ts_fwd.loc[_dt, 'PET']
                if np.isnan(_P_t) or np.isnan(_PET_t):
                    continue
                _dh_pred = _b1 * _P_t - _b2 * _PET_t - _b3 * (DRAINAGE_DATUM + _h_pred)
                _h_pred  = _h_pred + _dh_pred
                _ts_fwd.loc[_dt, 'h_pred'] = _h_pred

            _ts_fwd['residual'] = _ts_fwd['h'] - _ts_fwd['h_pred']

            # Mask era boundaries against the SSM frame's own index, not the
            # wells frame, because dropna may have removed rows.
            _fwd_baseline_mask = _ts_fwd.index < date_2015
            _fwd_scraping_mask = (
                (_ts_fwd.index >= date_2015) & (_ts_fwd.index < date_felling)
            )

            _ssm_baseline = _ts_fwd.loc[_fwd_baseline_mask, 'residual'].mean()
            _ssm_scraping = _ts_fwd.loc[_fwd_scraping_mask, 'residual'].mean()
            _ssm_step = _ssm_scraping - (_ssm_baseline if pd.notna(_ssm_baseline) else 0.0)
        else:
            _ts_fwd = _ts.copy()
            _ts_fwd['h_pred']   = np.nan
            _ts_fwd['residual'] = np.nan
            _ssm_step = np.nan
    else:
        _ts_fwd = _ts.copy()
        _ts_fwd['h_pred']   = np.nan
        _ts_fwd['residual'] = np.nan
        _ssm_step = np.nan
        print(f"  [WARNING] Insufficient baseline for SSM calibration "
              f"({len(_ts_base)} months, need >=36)")

    # ── FIGURE: three panels ──────────────────────────────────────────────
    _fig = plt.figure(figsize=(13, 11), dpi=300)
    _gs  = _fig.add_gridspec(3, 1, height_ratios=[1.2, 1.0, 0.9], hspace=0.45)

    # Panel (a): raw BACI vs synthetic control gap series
    _ax1 = _fig.add_subplot(_gs[0])
    _ax1.plot(_gap_raw.index, _gap_raw.values,
              color='#8b5a2b', lw=1.6, alpha=0.85,
              label='CEH36 − CEH4 (raw BACI)')
    if not np.isnan(_syn_step):
        _ax1.plot(_gap_syn.index, _gap_syn.values,
                  color='#1f77b4', lw=1.6, alpha=0.85,
                  label='CEH36 − synthetic (donor composite)')

    _ax1.axhline(_raw_baseline, color='#8b5a2b', ls='--', lw=1.0, alpha=0.6)
    if not np.isnan(_syn_step):
        _ax1.axhline(_syn_baseline, color='#1f77b4', ls='--', lw=1.0, alpha=0.6)
        _ax1.axhline(_syn_scraping, color='#1f77b4', ls=':',  lw=1.0, alpha=0.6)
    _ax1.axhline(_raw_scraping, color='#8b5a2b', ls=':', lw=1.0, alpha=0.6)

    _ax1.axvline(date_2015,    color='black', ls='--', lw=0.8, alpha=0.5)
    _ax1.axvline(date_felling, color='black', ls='--', lw=0.8, alpha=0.5)
    _ax1.axvline(date_2023,    color='black', ls='--', lw=0.8, alpha=0.5)
    _ax1.text(date_2015,    _ax1.get_ylim()[1]*0.95, ' 2015 scraping',
              fontsize=8, va='top', alpha=0.7)
    _ax1.text(date_felling, _ax1.get_ylim()[1]*0.95, ' felling',
              fontsize=8, va='top', alpha=0.7)
    _ax1.text(date_2023,    _ax1.get_ylim()[1]*0.95, ' 2023 rescrape',
              fontsize=8, va='top', alpha=0.7)

    _ax1.set_ylabel('CEH36 − reference (m)')
    _ax1.set_title('(a) Raw BACI and synthetic control gap series',
                   loc='left', fontweight='bold', fontsize=10)
    _ax1.legend(loc='lower left', fontsize=8, framealpha=0.9, ncol=2)
    # Extend negative y to give legend clearance
    _a_lo, _a_hi = _ax1.get_ylim()
    _ax1.set_ylim(_a_lo - 0.08, _a_hi)
    _ax1.grid(axis='y', alpha=0.25)
    _ax1.spines['top'].set_visible(False)
    _ax1.spines['right'].set_visible(False)

    # Panel (b): SSM forward residual
    _ax2 = _fig.add_subplot(_gs[1])
    if 'residual' in _ts_fwd.columns and _ts_fwd['residual'].notna().any():
        # Only plot from the prediction start — the baseline period has NaN
        # predictions (the SSM was calibrated there, not run forward), and
        # plotting NaN residuals creates a misleading flat line at zero.
        _resid = _ts_fwd['residual'].dropna()
        _ax2.plot(_resid.index, _resid.values, color='#2c7a3f', lw=1.4, alpha=0.85,
                  label='SSM forward residual (observed − predicted)')
        _ax2.fill_between(_resid.index, 0, _resid.values,
                          where=_resid.values >= 0,
                          color='#2c7a3f', alpha=0.15, interpolate=True,
                          label='Shallower than SSM prediction (beneficial)')
        _ax2.fill_between(_resid.index, 0, _resid.values,
                          where=_resid.values < 0,
                          color='#b85c4a', alpha=0.15, interpolate=True,
                          label='Deeper than SSM prediction')
    _ax2.axhline(0, color='black', lw=0.6, alpha=0.6)
    _ax2.axvline(date_2015,    color='black', ls='--', lw=0.8, alpha=0.5)
    _ax2.axvline(date_felling, color='black', ls='--', lw=0.8, alpha=0.5)
    _ax2.axvline(date_2023,    color='black', ls='--', lw=0.8, alpha=0.5)

    _ax2.set_ylabel('Residual (m)')
    _ax2.set_title('(b) SSM forward residual at CEH36 — calibrated on pre-2015 baseline',
                   loc='left', fontweight='bold', fontsize=10)
    _ax2.legend(loc='lower left', fontsize=7, framealpha=0.9, ncol=3)
    # Extend negative y to give legend clearance
    _b_lo, _b_hi = _ax2.get_ylim()
    _ax2.set_ylim(_b_lo - 0.08, _b_hi)
    _ax2.grid(axis='y', alpha=0.25)
    _ax2.spines['top'].set_visible(False)
    _ax2.spines['right'].set_visible(False)

    # Panel (c): bar chart of step estimates from three methods
    _ax3 = _fig.add_subplot(_gs[2])
    _methods = ['Raw BACI (vs CEH4)', 'Synthetic control (11 donors)', 'SSM forward residual']
    _values  = [_raw_step,
                _syn_step if not np.isnan(_syn_step) else 0.0,
                _ssm_step if not np.isnan(_ssm_step) else 0.0]
    _colours = ['#8b5a2b', '#1f77b4', '#2c7a3f']
    _bars = _ax3.bar(_methods, _values, color=_colours, alpha=0.85,
                     edgecolor='black', linewidth=0.8)

    # Annotate bars with values
    for _bar, _val in zip(_bars, _values):
        _y = _bar.get_height()
        _ax3.text(_bar.get_x() + _bar.get_width() / 2,
                  _y + (0.005 if _y >= 0 else -0.015),
                  f'{_val:+.3f} m',
                  ha='center', va='bottom' if _y >= 0 else 'top',
                  fontsize=9, fontweight='bold')

    _ax3.axhline(0, color='black', lw=0.8)
    _ax3.set_ylabel('Pure Scraping era\nstep change (m)')
    _ax3.set_title('(c) Pure Scraping era step change — three independent methods',
                   loc='left', fontweight='bold', fontsize=10)
    # Extend y-axis so bar annotations don't collide with panel title
    _ymax = max(_values) if max(_values) > 0 else 0.15
    _ax3.set_ylim(min(min(_values), 0) - 0.01, _ymax * 1.35)
    _ax3.spines['top'].set_visible(False)
    _ax3.spines['right'].set_visible(False)
    _ax3.grid(axis='y', alpha=0.2)

    _fig.suptitle(
        'CEH36 Scraping Robustness Analysis — Three Independent Methods\n'
        'Newborough Warren 2005–2026',
        fontsize=11, fontweight='bold', y=0.975)
    # Ensure y-axis labels aren't clipped
    _fig.subplots_adjust(left=0.12)

    plt.savefig(OUT_09_ROBUSTNESS, bbox_inches='tight', dpi=300)
    plt.close()
    print(f" -> Saved: {OUT_09_ROBUSTNESS.name}")
    print(f"   Raw BACI step:    {_raw_step:+.3f} m")
    print(f"   Synthetic step:   {_syn_step:+.3f} m")
    print(f"   SSM residual:     {_ssm_step:+.3f} m")

except Exception as _e:
    print(f"  [WARNING] Robustness figure failed — {_e}")
    import traceback
    traceback.print_exc()


# ====================================================================================
# EXPORT REPORT NUMBERS — single CSV with every value quoted in §4.5
# ====================================================================================
print("\nExporting report numbers CSV...")

_report_rows = []

def _rr(parameter, value, unit="m", well="", era="", note=""):
    """Append a row to the report numbers list."""
    _report_rows.append({
        "Parameter": parameter,
        "Well": well,
        "Era": era,
        "Value": round(value, 4) if pd.notna(value) else "",
        "Unit": unit,
        "Note": note,
    })

# 1. Tier 1 CUSUM terminal values
for _w in tier1_wells:
    if _w in plot_data:
        _final_cusum = float(plot_data[_w]['cusum'].iloc[-1])
        _rr("Tier1_CUSUM_terminal", _final_cusum, well=_w.upper(),
            note="Final cumulative CUSUM vs Regional Mean")

# 2. Tier 2 raw BACI shifts (from baci_results already computed)
for _br in baci_results:
    _rr("Tier2_BACI_shift", _br['Delta_m'],
        well=_br['Well'], era=_br['Shift'],
        note=f"vs {_br['Control']}")

# 3. Tier 1 net benefits (from net_summary already computed)
for _nb in net_summary:
    _rr("Net_benefit", _nb['Net_Benefit_m'],
        well=_nb['Well'], era=_nb['Shift'],
        note="vs CEH21 coastal benchmark")

# 4. Three-method CEH36 estimates (from robustness section)
try:
    _rr("CEH36_raw_BACI_step", _raw_step, well="CEH36", era="Pure_Scraping",
        note="CEH36 minus CEH4")
    _rr("CEH36_synthetic_control_step", _syn_step, well="CEH36", era="Pure_Scraping",
        note=f"Synthetic control ({len(_donors)} donors)")
    _rr("CEH36_SSM_forward_residual_step", _ssm_step, well="CEH36", era="Pure_Scraping",
        note="SSM calibrated on pre-2015 baseline")
except NameError:
    pass  # robustness section failed — variables not defined

# 5. Table 5 β₃ era estimates (from significance_results already computed)
for _sr in significance_results:
    _rr("Table5_beta3_era", _sr['beta_3_drainage'],
        well=_sr['Well'], era=_sr['Era'],
        note=f"CI=[{_sr['Conf_Low']:.4f},{_sr['Conf_High']:.4f}] "
             f"p={format_p_value(_sr['P_Value'])}")

# 6. Summer minimum depths by era for CEH4 and CEH36
_SUMMER_MONTHS = [6, 7, 8, 9]
for _sw in ['ceh4', 'ceh36']:
    if _sw not in wells.columns:
        continue
    _sw_config = well_eras.get(_sw)
    if _sw_config is None:
        continue
    _sw_series = wells[_sw].dropna()
    for _era_name, _era_filter in _sw_config['Eras'].items():
        _era_data = _era_filter(_sw_series)
        _summer = _era_data[_era_data.index.month.isin(_SUMMER_MONTHS)]
        if len(_summer) >= 2:
            # Depths are negative below ground; summer minimum water table =
            # maximum depth value (most negative). We report absolute depth.
            _summer_min_depth = float(_summer.min())
            _rr("Summer_minimum_depth", _summer_min_depth,
                well=_sw.upper(), era=_era_name,
                note="Mean of annual Jun-Sep minima")

# Build and export
_report_df = pd.DataFrame(_report_rows)
_report_df.to_csv(OUT_09_REPORT_NUMBERS, index=False)
print(f" -> Saved: {OUT_09_REPORT_NUMBERS.name} ({len(_report_rows)} rows)")
