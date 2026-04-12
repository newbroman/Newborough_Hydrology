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
    OUT_09_FULL_PARAMS,
    OUT_09_BETA3_SIG,
    OUT_09_BACI_SHIFTS,
    OUT_09_NET_BENEFITS,
    OUT_09_TABLE4_SUMMARY,
    OUT_09_TIER1_DRIFT,
    OUT_09_TIER2_SIGNAL,
    OUT_09_BETA3_CI,
    INT_CLIMATE,
    DIR_09
)
from utils.data_utils import parse_met_date, clean_well_series, calculate_cusum
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
    df["beta_3"] = df["beta_3_internal_brake"].round(3)
    df["well_rank"] = pd.Categorical(df["Well"], categories=well_order, ordered=True)
    df["era_rank"] = df["Era"].map(era_order).fillna(99)
    df = df.sort_values(["well_rank", "era_rank", "Era_Label"])

    out = df[["Well", "Role", "Era_Label", "beta_3", "CI_95", "p_value", "Sig"]].rename(
        columns={"Era_Label": "Era"}
    )
    out.to_csv(OUT_09_TABLE4_SUMMARY, index=False)


RAF_VALLEY_LAT_DEG = 53.25


def thornthwaite_pet_m(t_mean: pd.Series, lat_deg: float = RAF_VALLEY_LAT_DEG) -> pd.Series:
    temps_pos = t_mean.clip(lower=0).fillna(0)
    i_monthly = (temps_pos / 5) ** 1.514
    i_annual = i_monthly.groupby(t_mean.index.year).sum()
    I = pd.Series(t_mean.index.year, index=t_mean.index).map(i_annual)
    I = I.replace(0, np.nan)
    alpha = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.792e-2 * I) + 0.49239
    pet_unadj = np.where(
        temps_pos <= 0, 0.0,
        np.where(
            temps_pos < 26.5,
            16.0 * (10.0 * temps_pos / I) ** alpha,
            -415.85 + 32.24 * temps_pos - 0.43 * temps_pos ** 2,
        ),
    )
    lat_rad = np.radians(lat_deg)
    mid_doy = np.array([15, 46, 75, 106, 136, 167, 197, 228, 259, 289, 320, 350])
    decl = np.radians(23.45 * np.sin(np.radians(360 * (mid_doy - 80) / 365)))
    cos_ha = -np.tan(lat_rad) * np.tan(decl[t_mean.index.month - 1])
    N = (24 / np.pi) * np.arccos(np.clip(cos_ha, -1, 1))
    K = (N / 12) * (t_mean.index.days_in_month / 30)
    pet_m = pd.Series(pet_unadj * K / 1000, index=t_mean.index, name="PET")
    pet_m[t_mean.isna()] = np.nan
    return pet_m

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

def clean_well_series(series: pd.Series, max_depth: float = 4.0) -> pd.Series:
    cleaned = series.where(series <= max_depth, np.nan)
    return cleaned.interpolate(method='time', limit=3)

def calculate_cusum(series: pd.Series, baseline_mean: float) -> pd.Series:
    return (series - baseline_mean).cumsum()

# ==========================================
# 1. SETUP EXPERIMENTS & ERAS
# ==========================================
controls = ['ceh9', 'nw8', 'nw8b', 'nw5', 'nw6', 'nw7']

date_2015 = pd.to_datetime('2015-04-01')
date_felling = pd.to_datetime('2018-12-01')
date_2023 = pd.to_datetime('2023-10-01')

print("1. Loading Climate and Well Data...")
try:
    climate = pd.read_csv(INT_CLIMATE)
    def parse_met_date(date_str):
        try:
            m, y = date_str.split()
            year = int(y) + (2000 if int(y) <= 26 else 1900)
            return pd.to_datetime(f"01-{m}-{year}")
        except: return pd.NaT

    # outputs/01_climate.csv already has 'Date', 'P_m', 'PET' columns
    climate['Date'] = pd.to_datetime(climate['Date'])
    climate = climate.set_index('Date')

    wells_raw = pd.read_csv(DATA_WELLS_RAW, header=1)
    wells = wells_raw.set_index(wells_raw.columns[0]).transpose()
    wells.index = pd.to_datetime(wells.index, dayfirst=True, errors='coerce').to_period('M').to_timestamp()
    wells = wells.apply(pd.to_numeric, errors='coerce').groupby(level=0).mean()
    wells.columns = wells.columns.str.lower().str.replace(' ', '')

    for col in wells.columns:
        wells[col] = clean_well_series(wells[col])

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
    df['h_prev'] = df['h'].shift(1)
    df['Delta_h'] = df['h'] - df['h_prev']
    df = df.dropna()

    X_base = pd.DataFrame({'beta_1_recharge': df['P_m'], 'beta_2_atmospheric_draw': -df['PET'], 'beta_3_internal_brake': -df['h_prev']})
    res_base = sm.OLS(df['Delta_h'], X_base).fit()
    b1, b2 = res_base.params['beta_1_recharge'], res_base.params['beta_2_atmospheric_draw']
    df['Drainage_Component'] = df['Delta_h'] - (b1 * df['P_m']) - (b2 * -df['PET'])
    df['neg_h_prev'] = -df['h_prev']
    
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
            X_full = pd.DataFrame({'beta_1_recharge': sub['P_m'], 'beta_2_atmospheric_draw': -sub['PET'], 'beta_3_internal_brake': -sub['h_prev']})
            model_full = sm.OLS(sub['Delta_h'], X_full).fit()
            
            full_params_results.append({
                'Well': well.upper(), 'Era': era_name,
                'beta_1_recharge': round(model_full.params['beta_1_recharge'], 3),
                'beta_2_atmospheric_draw': round(model_full.params['beta_2_atmospheric_draw'], 3),
                'beta_3_internal_brake': round(model_full.params['beta_3_internal_brake'], 3)
            })
            
            X_iso = sm.add_constant(sub['neg_h_prev'])
            model_iso = sm.OLS(sub['Drainage_Component'], X_iso).fit()
            ci = model_iso.conf_int().loc['neg_h_prev']
            significance_results.append({
                'Well': well.upper(), 'Era': era_name,
                'beta_3_internal_brake': model_iso.params['neg_h_prev'],
                'P_Value': model_iso.pvalues['neg_h_prev'],
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
            err_low = row['beta_3_internal_brake'] - row['Conf_Low']
            err_high = row['Conf_High'] - row['beta_3_internal_brake']
            clean_label = era.split('_', 1)[1].replace('_', ' ')
            ax3.errorbar(x_pos, row['beta_3_internal_brake'], yerr=[[err_low], [err_high]],
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