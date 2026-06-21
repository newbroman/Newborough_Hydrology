"""
16_water_bal.py
===============
Mean Monthly Water Balance Decomposition by Cluster — Newborough Warren 2005–2026

Produces the outputs supporting Section 4.2.3 of the report:

  Table 3a (head-space decomposition):
    16_water_bal_table.csv

  Table 3b (volumetric partition):
    16_water_bal_vol_table.csv

  Figure 8 (two-panel combined):
    16_water_bal_fig8_ms.png        — manuscript (white, 300 dpi)
    16_water_bal_fig8_lay.png       — lay version (coloured background)

  Panel (a): Head-space SSM decomposition
    Recharge (β₁·P̄) vs ET draw (β₂·PET̄) + Drainage (β₃·h̄_disp)
    The balance closes to < 2.5% residual in all clusters.

  Panel (b): Volumetric water balance partition
    P vs Losses (ET + Drainage + Interception)
    ET/Drainage boundary bracketed by two independent methods:
      - SSM headspace β₂/β₃ ratio
      - Seasonal recession curve analysis (winter vs summer decline rates)
    Interception (24% of P, forest clusters only; Freeman 2008) appears
    identically on both input and loss bars, cancelling in the net surplus.

Head-space components (m/month):
    Recharge     =  β₁ · P̄             (m head per m rainfall)
    ET draw      =  β₂ · PET̄           (m head per m PET)
    Drainage     =  β₃ · h̄_disp        (m head per m displacement above datum)
    h_disp       =  DRAINAGE_DATUM + h  (displacement above drainage base)

Volumetric water balance (mm/yr):
    P            =  measured rainfall (RAF Valley, identical for all clusters)
    PET          =  Thornthwaite PET (identical for all clusters)
    I            =  0.24 × P (forest only; Freeman 2008)
    Net recharge =  P − I
    ET at WT     =  PET − I (interception consumes PET energy)
    P − PET      =  238 mm/yr net surplus, identical for all clusters

    The ET/Drainage partition is estimated by two independent methods:
      SSM:       ratio of β₂·PET̄ to β₃·h̄_disp from the closed headspace balance
      Recession: ratio of winter to summer hydrograph recession rates

The displacement datum (DRAINAGE_DATUM) is imported from utils/config.py.
It was identified by sensitivity analysis (Script 03, output 03_08) as the
minimum depth below ground at which all five cluster β₃ values are positive
and significant (p < 0.05), ensuring physically consistent Darcy-compatible
drainage behaviour. See Section 3.4.1 of the report.

References:
    Freeman, S. (2008) Hydrological impact of Corsican pine at Newborough Warren.
    Healy, R.W. & Cook, P.G. (2002) Using groundwater levels to estimate recharge.
    Hollingham, M. (2026) Hydrogeological Dynamics... Newborough Warren.
    von Asmuth, J.R. et al. (2002) Transfer function-noise modelling. WRR 38(12).
    Knotters, M. & Bierkens, M.F.P. (2000) Physical basis of time series models
      for water table depths. WRR 36(1), 181–188.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.patches as mpatches

from utils.paths import (
    make_all_dirs, DIR_16, INT_REGIONAL_AVG,
    OUT_16_TABLE, OUT_16_VOL_TABLE, OUT_16_BAR_LAY, OUT_16_BAR_MS,
    OUT_03_MECHANISTIC_TABLE,
)
from utils.config import (
    BW_MODE,
    CLUSTER_LABELS as _CFG_LABELS,
    CLUSTER_COLOURS as _CFG_COLOURS,
    DRAINAGE_DATUM,
    FOREST_INTERCEPTION,
    FOREST_CIDS,
)
make_all_dirs()

# ── Constants ──────────────────────────────────────────────────────────────────
# FOREST_INTERCEPTION imported from config.py (Freeman 2008, 0.24).
# FOREST_CIDS imported from config.py — forested clusters (4, 5).

# Recession analysis seasons (calendar months)
WINTER_MONTHS = [11, 12, 1, 2]
SUMMER_MONTHS = [6, 7, 8, 9]

# ── Figure colours ─────────────────────────────────────────────────────────────
C_RECH  = "#4A90D9"   # blue — recharge
C_ET    = "#E8724A"   # warm orange — ET draw
C_DRAIN = "#7A6B5D"   # brown-grey — drainage
C_INTCP = "#5BA55B"   # green — interception
C_P     = "#4A7FB5"   # steel blue — rainfall

if BW_MODE:
    C_RECH  = "#888888"
    C_ET    = "#444444"
    C_DRAIN = "#aaaaaa"
    C_INTCP = "#cccccc"
    C_P     = "#666666"

# BW hatching patterns for water balance components
H_RECH  = ""      if not BW_MODE else ""
H_ET    = ""      if not BW_MODE else "///"
H_DRAIN = ""      if not BW_MODE else "..."
H_INTCP = ""      if not BW_MODE else "xxx"
H_P     = ""      if not BW_MODE else ""

# ── Label helpers ──────────────────────────────────────────────────────────────
def _two_line(label: str) -> str:
    """'C1 (Lake Edge)' -> 'C1\\n(Lake Edge)' for narrow figure x-axes."""
    if "(" in label:
        ctag, rest = label.split("(", 1)
        return f"{ctag.strip()}\n({rest.strip()}"
    return label

CLUSTER_LABELS_FIG = {cid: _two_line(label) for cid, label in _CFG_LABELS.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_data():
    """Load regional averages and cluster-centroid SSM coefficients.

    Climate (P_mm, PET_mm) is taken directly from 03_regional_averages.csv,
    which already carries these columns — no separate climate file merge.
    Converted to metres in-script for consistency with β units (m/m).

    Betas come from 03_cluster_mechanistic_coefficients.csv (centroid
    headline fit with HEADLINE_LAG and displacement datum). Column names:
    beta_1, beta_2, beta_3, drainage_datum_m.
    """
    df = pd.read_csv(INT_REGIONAL_AVG, parse_dates=["Date"])

    # Convert P and PET from mm to metres (β coefficients are in m/m)
    df["P_m"]  = df["P_mm"]  / 1000.0
    df["PET"]  = df["PET_mm"] / 1000.0

    mech = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
    betas = mech.set_index("Cluster")[["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage",
                                        "LCSC_percent", "drainage_datum_m"]]

    # Verify datum consistency
    file_datum = mech["drainage_datum_m"].iloc[0]
    if abs(file_datum - DRAINAGE_DATUM) > 0.01:
        print(f"  [WARNING] Datum mismatch: config.DRAINAGE_DATUM = {DRAINAGE_DATUM}, "
              f"coefficients file = {file_datum}. Using file value.")

    return df, betas


# ═══════════════════════════════════════════════════════════════════════════════
# HEADSPACE WATER BALANCE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_headspace(df, betas):
    """Compute mean monthly head-space water balance components.

    SSM equation (displacement formulation):
        Δh = β₁·P(t-1) − β₂·PET(t) − β₃·h_disp(t-1)

    where h_disp = DRAINAGE_DATUM + h_depth (displacement above datum).

    Components:
        Recharge  = β₁ · P̄        (mean monthly, m/month)
        ET draw   = β₂ · PET̄      (mean monthly, m/month)
        Drainage  = β₃ · h̄_disp   (mean monthly, m/month)
        Residual  = Recharge − (ET draw + Drainage)
    """
    datum = betas["drainage_datum_m"].iloc[0]

    col_map = {cid: f"C{cid}" for cid in sorted(_CFG_LABELS.keys())
               if f"C{cid}" in df.columns}
    summary = {}

    for cid, col in col_map.items():
        sub = df[[col, "P_m", "PET"]].dropna()
        b1 = betas.loc[cid, "beta_1_recharge"]
        b2 = betas.loc[cid, "beta_2_atmospheric_draw"]
        b3 = betas.loc[cid, "beta_3_drainage"]
        lcsc = betas.loc[cid, "LCSC_percent"]

        P_m   = sub["P_m"].mean()
        PET_m = sub["PET"].mean()
        h_depth_mean = sub[col].mean()            # negative (below surface)
        h_disp_mean  = datum + h_depth_mean        # displacement above datum

        recharge   = b1 * P_m
        et_draw    = b2 * PET_m
        drainage   = b3 * h_disp_mean
        total_loss = et_draw + drainage
        residual   = recharge - total_loss

        drain_pct = 100.0 * drainage / total_loss if total_loss > 0 else 0
        et_pct    = 100.0 * et_draw / total_loss if total_loss > 0 else 0

        summary[cid] = dict(
            lcsc=lcsc, b1=b1, b2=b2, b3=b3,
            P_m=P_m, PET_m=PET_m,
            h_depth_mean=h_depth_mean, h_disp_mean=h_disp_mean,
            recharge=recharge, et_draw=et_draw, drainage=drainage,
            total_loss=total_loss, residual=residual,
            drain_pct=drain_pct, et_pct=et_pct,
        )

    return summary


# ═══════════════════════════════════════════════════════════════════════════════
# RECESSION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_recession_partition(df):
    """Estimate ET/drainage partition from seasonal recession rates.

    Winter recession (Nov–Feb, PET low) ≈ drainage only.
    Summer recession (Jun–Sep, PET high) = drainage + ET.
    Ratio winter/summer gives drainage fraction of summer losses.

    Returns dict {cid: drain_frac} where drain_frac = winter_rate / summer_rate.
    """
    df = df.copy()
    df["month"] = df["Date"].dt.month

    col_map = {cid: f"C{cid}" for cid in sorted(_CFG_LABELS.keys())
               if f"C{cid}" in df.columns}

    recession = {}
    for cid, col in col_map.items():
        s = df[["month", col]].copy()
        s["dh"] = df[col].diff()
        rec = s[s["dh"] < 0]

        w = rec[rec["month"].isin(WINTER_MONTHS)]["dh"].mean()
        sm = rec[rec["month"].isin(SUMMER_MONTHS)]["dh"].mean()

        if pd.notna(w) and pd.notna(sm) and sm < 0:
            recession[cid] = {
                "winter_rate": w,
                "summer_rate": sm,
                "drain_frac": w / sm,    # fraction of summer recession = drainage
                "et_frac": 1 - w / sm,   # fraction = ET
                "n_winter": len(rec[rec["month"].isin(WINTER_MONTHS)]),
                "n_summer": len(rec[rec["month"].isin(SUMMER_MONTHS)]),
            }
        else:
            recession[cid] = {"drain_frac": np.nan, "et_frac": np.nan}

    return recession


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE OUTPUTS
# ═══════════════════════════════════════════════════════════════════════════════

def save_headspace_table(summary, path):
    """Save Table 3a: head-space water balance decomposition."""
    rows = []
    for cid in sorted(summary.keys()):
        s = summary[cid]
        rows.append({
            "Cluster": cid,
            "Label": _CFG_LABELS[cid],
            "beta_1_recharge": s["b1"],
            "beta_2_atmospheric_draw": s["b2"],
            "beta_3_drainage": s["b3"],
            "LCSC_pct": s["lcsc"],
            "P_mean_m_month": s["P_m"],
            "PET_mean_m_month": s["PET_m"],
            "h_disp_mean_m": s["h_disp_mean"],
            "Recharge_m_month": s["recharge"],
            "ET_draw_m_month": s["et_draw"],
            "Drainage_m_month": s["drainage"],
            "Total_loss_m_month": s["total_loss"],
            "Residual_m_month": s["residual"],
            "Drainage_pct": s["drain_pct"],
            "ET_pct": s["et_pct"],
        })
    pd.DataFrame(rows).to_csv(path, index=False, float_format="%.6f")
    print(f"  -> Saved: {path.name}")


def save_volumetric_table(summary, recession, path):
    """Save Table 3b: volumetric water balance partition.

    Shows P, I, and the ET/Drainage partition bracketed by SSM and recession
    methods. No Sy-dependent conversion — the partition is derived from
    headspace ratios (SSM) and observed recession rates.
    """
    P_annual = summary[1]["P_m"] * 12 * 1000   # mm/yr (same for all)
    PET_annual = summary[1]["PET_m"] * 12 * 1000

    rows = []
    for cid in sorted(summary.keys()):
        s = summary[cid]
        r = recession.get(cid, {})

        is_forest = cid in FOREST_CIDS
        I_val = FOREST_INTERCEPTION * P_annual if is_forest else 0.0
        P_net = P_annual - I_val

        # SSM partition (from headspace ratios)
        ssm_drain_frac = s["drain_pct"] / 100.0
        ssm_et_frac = s["et_pct"] / 100.0

        # Recession partition
        rec_drain_frac = r.get("drain_frac", np.nan)
        rec_et_frac = r.get("et_frac", np.nan)

        # Midpoint and range
        if pd.notna(rec_drain_frac):
            df_lo = min(ssm_drain_frac, rec_drain_frac)
            df_hi = max(ssm_drain_frac, rec_drain_frac)
            df_mid = (ssm_drain_frac + rec_drain_frac) / 2
        else:
            df_lo = df_hi = df_mid = ssm_drain_frac

        rows.append({
            "Cluster": cid,
            "Label": _CFG_LABELS[cid],
            "P_mm_yr": P_annual,
            "PET_mm_yr": PET_annual,
            "I_mm_yr": I_val,
            "P_net_mm_yr": P_net,
            "P_minus_PET_mm_yr": P_annual - PET_annual,
            "SSM_drain_frac": ssm_drain_frac,
            "SSM_ET_frac": ssm_et_frac,
            "Rec_drain_frac": rec_drain_frac,
            "Rec_ET_frac": rec_et_frac,
            "Mid_drain_frac": df_mid,
            "ET_mid_mm_yr": P_net * (1 - df_mid),
            "ET_lo_mm_yr": P_net * (1 - df_hi),
            "ET_hi_mm_yr": P_net * (1 - df_lo),
            "Drain_mid_mm_yr": P_net * df_mid,
            "Drain_lo_mm_yr": P_net * df_lo,
            "Drain_hi_mm_yr": P_net * df_hi,
        })

    pd.DataFrame(rows).to_csv(path, index=False, float_format="%.1f")
    print(f"  -> Saved: {path.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE
# ═══════════════════════════════════════════════════════════════════════════════

def make_figure(summary, recession, ms=True):
    """Two-panel Figure 8.

    Panel (a): Head-space SSM decomposition — recharge vs ET + drainage.
    Panel (b): Volumetric partition — P vs losses, with hatched uncertainty
               band at ET/drainage boundary.
    """
    cids = sorted(summary.keys())
    x = np.arange(len(cids))

    P_annual = summary[cids[0]]["P_m"] * 12 * 1000
    PET_annual = summary[cids[0]]["PET_m"] * 12 * 1000

    if ms:
        plt.rcParams.update({"font.family": "sans-serif", "axes.labelsize": 10})
        bg_color = "white"
    else:
        bg_color = "#F5F0E8"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 12), facecolor=bg_color)
    for ax in (ax1, ax2):
        ax.set_facecolor(bg_color)

    # ── Panel (a): Headspace ──────────────────────────────────────────────
    width = 0.35
    rech_vals = [summary[c]["recharge"] for c in cids]
    et_vals   = [summary[c]["et_draw"]  for c in cids]
    drain_vals = [summary[c]["drainage"] for c in cids]

    ax1.bar(x - width/2, rech_vals, width, color=C_RECH, edgecolor="black" if BW_MODE else "white",
            linewidth=0.5, label="Recharge (β₁·P̄)", zorder=3, hatch=H_RECH)
    ax1.bar(x + width/2, et_vals, width, color=C_ET, edgecolor="black" if BW_MODE else "white",
            linewidth=0.5, label="ET draw (β₂·PET̄)", zorder=3, hatch=H_ET)
    ax1.bar(x + width/2, drain_vals, width, bottom=et_vals, color=C_DRAIN,
            edgecolor="black" if BW_MODE else "white", linewidth=0.5,
            label="Drainage (β₃·h̄ᵈⁱˢᵖ)", zorder=3, hatch=H_DRAIN)

    for i, cid in enumerate(cids):
        s = summary[cid]
        # Recharge label above bar
        ax1.text(i - width/2, s["recharge"] + 0.004, f'{s["recharge"]:.3f}',
                 ha='center', va='bottom', fontsize=8, color='#333')
        # ET label inside bar
        if s["et_draw"] > 0.04:
            ax1.text(i + width/2, s["et_draw"]/2, f'{s["et_draw"]:.3f}',
                     ha='center', va='center', fontsize=8, color='white',
                     fontweight='bold')
        # Drainage label inside or above bar
        if s["drainage"] > 0.04:
            ax1.text(i + width/2, s["et_draw"] + s["drainage"]/2,
                     f'{s["drainage"]:.3f}', ha='center', va='center',
                     fontsize=8, color='white', fontweight='bold')
        else:
            ax1.text(i + width/2, s["et_draw"] + s["drainage"] + 0.004,
                     f'{s["drainage"]:.3f}', ha='center', va='bottom',
                     fontsize=8, color='#555')
        # Partition percentages in space below zero line
        ax1.text(i, -0.025,
                 f'D:{s["drain_pct"]:.0f}%  ET:{s["et_pct"]:.0f}%',
                 ha='center', va='center', fontsize=8, color='#555')

    ax1.set_xticks(x)
    ax1.set_xticklabels([CLUSTER_LABELS_FIG[c] for c in cids], fontsize=9.5)
    ax1.set_ylabel("Head-space flux (m/month)", fontsize=11)
    ax1.set_title("(a) Mean monthly head-space water balance decomposition",
                  fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax1.set_xlim(-0.6, len(cids) - 0.4)
    ax1.set_ylim(-0.055, max(rech_vals) * 1.15)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.axhline(0, color='#999', linewidth=0.5, zorder=1)
    ax1.grid(axis='y', alpha=0.3, zorder=0)

    P_mm_mo = summary[cids[0]]["P_m"] * 1000
    PET_mm_mo = summary[cids[0]]["PET_m"] * 1000
    datum = DRAINAGE_DATUM
    max_resid_pct = max(
        100 * abs(summary[c]["residual"]) / summary[c]["total_loss"]
        for c in cids if summary[c]["total_loss"] > 0
    )
    ax1.text(0.5, -0.17,
             f"All clusters receive identical forcing: P̄ = {P_mm_mo:.1f} mm/month, "
             f"PET̄ = {PET_mm_mo:.1f} mm/month. "
             f"Residuals < {max_resid_pct:.1f}% of losses. Datum = {datum:.1f} m b.g.s.",
             transform=ax1.transAxes, ha='center', va='top', fontsize=9,
             color='#666', style='italic')

    # ── Panel (b): Volumetric ─────────────────────────────────────────────
    width_p = 0.30
    width_loss = 0.30
    gap = 0.04

    for i, cid in enumerate(cids):
        is_forest = cid in FOREST_CIDS
        I_val = FOREST_INTERCEPTION * P_annual if is_forest else 0
        P_net = P_annual - I_val

        # Partition fractions
        ssm_df = summary[cid]["drain_pct"] / 100.0
        rec_df = recession.get(cid, {}).get("drain_frac", ssm_df)
        if pd.isna(rec_df):
            rec_df = ssm_df
        df_lo  = min(ssm_df, rec_df)
        df_hi  = max(ssm_df, rec_df)
        df_mid = (ssm_df + rec_df) / 2

        et_mid    = P_net * (1 - df_mid)
        drain_mid = P_net * df_mid
        et_lo     = P_net * (1 - df_hi)    # boundary lowest (most drainage)
        et_hi     = P_net * (1 - df_lo)    # boundary highest (most ET)

        x_p = i - width_p/2 - gap/2
        x_l = i + width_loss/2 + gap/2

        # INPUT bar: P with interception at top
        ax2.bar(x_p, P_net, width_p, color=C_P,
                edgecolor="black" if BW_MODE else "white",
                linewidth=0.5, zorder=3, hatch=H_P)
        if is_forest:
            ax2.bar(x_p, I_val, width_p, bottom=P_net, color=C_INTCP,
                    edgecolor="black" if BW_MODE else "white",
                    linewidth=0.5, zorder=3,
                    hatch=H_INTCP if BW_MODE else '///', alpha=0.85)

        # LOSS bar: ET (bottom) + Drainage (top) + Interception (top)
        ax2.bar(x_l, et_mid, width_loss, color=C_ET,
                edgecolor="black" if BW_MODE else "white",
                linewidth=0.5, zorder=3, hatch=H_ET)
        ax2.bar(x_l, drain_mid, width_loss, bottom=et_mid, color=C_DRAIN,
                edgecolor="black" if BW_MODE else "white",
                linewidth=0.5, zorder=3, hatch=H_DRAIN)
        if is_forest:
            ax2.bar(x_l, I_val, width_loss, bottom=P_net, color=C_INTCP,
                    edgecolor="black" if BW_MODE else "white",
                    linewidth=0.5, zorder=3,
                    hatch=H_INTCP if BW_MODE else '///', alpha=0.85)

        # Uncertainty band: hatched rectangle at ET/drainage boundary
        band_bottom = et_lo
        band_height = et_hi - et_lo
        if band_height > 1:   # only draw if range is visible
            rect = mpatches.FancyBboxPatch(
                (x_l - width_loss/2, band_bottom), width_loss, band_height,
                boxstyle="square,pad=0",
                facecolor='white', edgecolor='#333', linewidth=0.8,
                alpha=0.45, hatch='\\\\\\', zorder=4,
            )
            ax2.add_patch(rect)

        # Value labels
        et_label_y = et_lo / 2 if et_lo > 100 else et_mid / 2
        if et_mid > 120:
            ax2.text(x_l, et_label_y, f'{et_mid:.0f}', ha='center', va='center',
                     fontsize=8.5, color='white', fontweight='bold', zorder=5)
        drain_label_y = (et_hi + (P_net - et_hi) / 2 if (P_net - et_hi) > 100
                         else et_mid + drain_mid / 2)
        if drain_mid > 120:
            ax2.text(x_l, drain_label_y, f'{drain_mid:.0f}', ha='center',
                     va='center', fontsize=8.5, color='white', fontweight='bold',
                     zorder=5)
        elif drain_mid > 50:
            ax2.text(x_l, et_mid + drain_mid/2, f'{drain_mid:.0f}', ha='center',
                     va='center', fontsize=8, color='white', zorder=5)

        # Interception labels
        if is_forest:
            ax2.text(x_p, P_net + I_val/2, f'I={I_val:.0f}', ha='center',
                     va='center', fontsize=8, color='white', fontweight='bold')
            ax2.text(x_l, P_net + I_val/2, f'I={I_val:.0f}', ha='center',
                     va='center', fontsize=8, color='white', fontweight='bold')

        # Column headers
        ax2.text(x_p, P_annual + 30, 'P', ha='center', va='bottom', fontsize=9,
                 color=C_P, fontweight='bold')
        ax2.text(x_l, P_annual + 30, 'Losses', ha='center', va='bottom',
                 fontsize=8.5, color='#444')

    # Reference lines
    ax2.axhline(P_annual, color=C_P, linewidth=0.6, linestyle='--', alpha=0.25,
                zorder=1)
    ax2.axhline(PET_annual, color='#999', linewidth=0.6, linestyle=':', alpha=0.25,
                zorder=1)
    ax2.text(-0.72, P_annual, f'P = {P_annual:.0f}', va='center', fontsize=8.5,
             color=C_P, fontweight='bold')
    ax2.text(-0.72, PET_annual, f'PET = {PET_annual:.0f}', va='center',
             fontsize=8.5, color='#888')

    # Legend
    legend_elements = [
        Patch(facecolor=C_P, edgecolor='white', label='Rainfall (P)'),
        Patch(facecolor=C_ET, edgecolor='white', label='Evapotranspiration'),
        Patch(facecolor=C_DRAIN, edgecolor='white', label='Lateral drainage'),
        Patch(facecolor=C_INTCP, edgecolor='white',
              label='Interception (Freeman 2008)', hatch='///'),
        Patch(facecolor='white', edgecolor='#333',
              label='Partition uncertainty\n(SSM–recession range)',
              hatch='\\\\\\', alpha=0.45, linewidth=0.8),
    ]
    ax2.legend(handles=legend_elements, loc='center right', fontsize=8.5,
               framealpha=0.9)

    ax2.set_xticks(x)
    ax2.set_xticklabels([CLUSTER_LABELS_FIG[c] for c in cids], fontsize=9.5)
    ax2.set_ylabel("Annual flux (mm/yr)", fontsize=11)
    ax2.set_title("(b) Volumetric water balance: ET/drainage partition bracketed "
                  "by SSM and recession analysis",
                  fontsize=12, fontweight='bold')
    ax2.set_xlim(-0.8, len(cids) + 1.2)
    ax2.set_ylim(0, P_annual * 1.12)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.grid(axis='y', alpha=0.3, zorder=0)

    I_pct = int(FOREST_INTERCEPTION * 100)
    ax2.text(0.5, -0.14,
             f"All clusters receive P = {P_annual:.0f} mm/yr. At steady state, "
             f"total losses = P. The hatched band spans the ET/drainage\nboundary "
             f"range between SSM headspace ratios and seasonal recession analysis. "
             f"Forest interception ({I_pct}% of P;\nFreeman 2008) "
             f"appears identically on both bars and cancels in the net surplus.",
             transform=ax2.transAxes, ha='center', va='top', fontsize=8.5,
             color='#666', style='italic')

    plt.tight_layout(h_pad=4.5)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("Starting 16: Water Balance Decomposition...")

    df, betas = load_data()

    # ── Headspace balance ──
    summary = compute_headspace(df, betas)

    print("\n  HEAD-SPACE WATER BALANCE (m/month)")
    print(f"  {'Cluster':<22} {'Rech':>8} {'ET':>8} {'Drain':>8} "
          f"{'Losses':>8} {'Resid':>9} {'D%':>5} {'ET%':>5}")
    for cid in sorted(summary.keys()):
        s = summary[cid]
        print(f"  {_CFG_LABELS[cid]:<22} "
              f"{s['recharge']:>8.4f} {s['et_draw']:>8.4f} {s['drainage']:>8.4f} "
              f"{s['total_loss']:>8.4f} {s['residual']:>+9.4f} "
              f"{s['drain_pct']:>4.0f}% {s['et_pct']:>4.0f}%")

    save_headspace_table(summary, OUT_16_TABLE)

    # ── Recession analysis ──
    recession = compute_recession_partition(df)

    print("\n  RECESSION PARTITION (winter/summer ratio)")
    print(f"  {'Cluster':<22} {'Win Δh':>9} {'Sum Δh':>9} {'D_frac':>7} "
          f"{'n_w':>5} {'n_s':>5}")
    for cid in sorted(recession.keys()):
        r = recession[cid]
        if pd.notna(r.get("winter_rate")):
            print(f"  {_CFG_LABELS[cid]:<22} "
                  f"{r['winter_rate']:>9.4f} {r['summer_rate']:>9.4f} "
                  f"{r['drain_frac']:>7.2f} {r['n_winter']:>5} {r['n_summer']:>5}")

    save_volumetric_table(summary, recession, OUT_16_VOL_TABLE)

    # ── Figure 8 ──
    # Manuscript version
    fig = make_figure(summary, recession, ms=True)
    fig.savefig(OUT_16_BAR_MS, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  -> Saved: {OUT_16_BAR_MS.name}")

    # Lay version
    fig = make_figure(summary, recession, ms=False)
    fig.savefig(OUT_16_BAR_LAY, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  -> Saved: {OUT_16_BAR_LAY.name}")

    print("\n  Done.")


if __name__ == "__main__":
    main()
