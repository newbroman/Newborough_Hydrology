"""
16_water_bal.py
===============
Mean Monthly Water Balance Decomposition by Cluster — Newborough Warren 2005–2026

Produces four outputs:
    16_water_bal_table.csv      — summary table of mean monthly head-space components
    16_water_bal_bar_lay.png    — lay version (coloured background, key findings box)
    16_water_bal_bar_ms.png     — manuscript version (white background, 300 dpi)
    16_water_bal_volumetric_ms.png  — volumetric chart, manuscript style (white, 300 dpi)
    16_water_bal_volumetric_lay.png — volumetric chart, lay summary style (tinted bg, 150 dpi)

Head-space components (m/month):
    Recharge     =  β₁ · P̄
    Atm. draw    =  β₂ · PET̄
    Drainage     =  β₃ · |h̄|
    Interception =  0.24 · P̄   [Forest only; Freeman, 2008]
    Subsidy      =  Total_Loss − Recharge  (boundary residual)

Volumetric conversion:
    flux (mm/yr) = head-space term (m/month) × 12 × Sy × 1000
    Sy: C1 = 0.08, C2 = C3 = C4 = 0.12  (assumed, pending field measurement)

References:
    Freeman, S. (2008) Hydrological impact of Corsican pine at Newborough Warren.
    Hollingham, M. (2026) Hydrogeological Dynamics... Newborough Warren.
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
from scipy import stats

from utils.paths import (
    make_all_dirs, DIR_16, INT_REGIONAL_AVG, INT_MASTER_DATA, INT_CLIMATE,
    OUT_16_TABLE, OUT_16_VOL_TABLE, OUT_16_BAR_LAY, OUT_16_BAR_MS,
    OUT_16_VOL_MS, OUT_16_VOL_LAY,
)
make_all_dirs()

# ── Constants ──────────────────────────────────────────────────────────────────
FOREST_INTERCEPTION = 0.24   # Freeman (2008)
SUMMER_TRENDS = {1: -0.010, 2: -0.012, 3: -0.015, 4: -0.017}  # m/yr
FLOOD_FREQ    = {1: "67%", 2: "52%", 3: "5%", 4: "n/a"}

CLUSTER_LABELS = {
    1: "C1 Eastern\n(Lake-buffer)",
    2: "C2 Eastern\n(Mature Dune)",
    3: "C3 Western\n(Mature Dune)",
    4: "C4 Forest",
}
CLUSTER_LABELS_VOL = {
    1: "C1 Eastern\nLake-buffer\nSy=8%",
    2: "C2 Eastern\nMature Dune\nSy=12%",
    3: "C3 Western\nMature Dune\nSy=12%",
    4: "C4 Forest\nSy=12%",
}
CLUSTER_LABELS_FLAT = {
    1: "C1_Eastern_Lake-buffer",
    2: "C2_Eastern_Mature_Dune",
    3: "C3_Western_Mature_Dune",
    4: "C4_Forest",
}

# Specific yield for volumetric conversion
SY = {1: 0.08, 2: 0.12, 3: 0.12, 4: 0.12}

# Colours — head-space chart
C_ATM   = "#F4956E"
C_DRAIN = "#A07060"
C_RECH  = "#6BAED6"
C_SUB   = "#B08FCC"
C_INT   = "#74BB77"
C_TEAL  = "#1B6B78"

# Uncertainty p-values and dof (from 03 outputs)
SUBSIDY_PCT_SE = {1: 0.046, 2: 0.103, 3: 0.130, 4: 0.150}


def load_data():
    """Load climate, regional averages and master SSM coefficients.
    All input CSVs live in OUT_DIR (outputs/ root).
    """
    climate  = pd.read_csv(INT_CLIMATE,       parse_dates=["Date"])
    regional = pd.read_csv(INT_REGIONAL_AVG,  parse_dates=["Date"])
    master   = pd.read_csv(INT_MASTER_DATA)
    df = regional.merge(climate[["Date", "P_m", "PET"]], on="Date", how="inner")
    betas = master.groupby("Cluster")[
        ["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_internal_brake"]
    ].median()
    return df, betas


def compute_summary(df, betas):
    """Compute mean monthly head-space water balance components."""
    col_map = {1: "C1", 2: "C2", 3: "C3", 4: "C4"}
    summary = {}
    for cid, col in col_map.items():
        sub = df[[col, "P_m", "PET"]].dropna()
        b1  = betas.loc[cid, "beta_1_recharge"]
        b2  = betas.loc[cid, "beta_2_atmospheric_draw"]
        b3  = abs(betas.loc[cid, "beta_3_internal_brake"])
        lcsc = 100.0 / b1

        P_m   = sub["P_m"].mean()
        PET_m = sub["PET"].mean()
        h_m   = sub[col].abs().mean()

        recharge  = b1 * P_m
        pet_loss  = b2 * PET_m
        drainage  = b3 * h_m
        intercept = FOREST_INTERCEPTION * P_m if cid == 4 else 0.0
        total_loss = pet_loss + drainage
        subsidy    = total_loss - recharge - intercept
        subsidy_se = subsidy * SUBSIDY_PCT_SE[cid]

        summary[cid] = dict(
            lcsc=lcsc, b1=b1, b2=b2, b3=b3,
            P_m=P_m, PET_m=PET_m, h_m=h_m,
            recharge=recharge, pet_loss=pet_loss,
            drainage=drainage, intercept=intercept,
            total_loss=total_loss, subsidy=subsidy,
            subsidy_se=subsidy_se,
        )
    return summary


def export_table(summary, output_dir):
    """Export CSV summary table."""
    rows = []
    for cid, s in summary.items():
        rows.append({
            "Cluster":                  CLUSTER_LABELS_FLAT[cid],
            "LCSC (%)":                 round(s["lcsc"], 1),
            "Recharge (m/month)":       round(s["recharge"], 4),
            "Atm. Draw (m/month)":      round(s["pet_loss"], 4),
            "Drainage (m/month)":       round(s["drainage"], 4),
            "Total Loss (m/month)":     round(s["total_loss"], 4),
            "Boundary Subsidy (m/month)": round(s["subsidy"], 4),
            "Boundary Subsidy (m/year)": round(s["subsidy"] * 12, 3),
        })
    pd.DataFrame(rows).to_csv(output_dir / "16_water_bal_table.csv", index=False)
    print("Table saved → 16_water_bal_table.csv")


def export_vol_table(summary, output_dir):
    """Export volumetric water balance table (mm/year) as CSV."""
    rows = []
    for cid, s in summary.items():
        sy = SY[cid]
        f  = 12 * sy * 1000
        rows.append({
            "Cluster":               CLUSTER_LABELS_FLAT[cid],
            "Sy":                    sy,
            "Recharge (mm/yr)":      round(s["recharge"]  * f),
            "Atm. Draw (mm/yr)":     round(s["pet_loss"]  * f),
            "Drainage (mm/yr)":      round(s["drainage"]  * f),
            "Total Loss (mm/yr)":    round((s["pet_loss"] + s["drainage"]) * f),
            "Subsidy (mm/yr)":       round(s["subsidy"]   * f),
            "Subsidy (% rainfall)":  round(s["subsidy"] * f / 890 * 100),
            "Subsidy SE (mm/yr)":    round(s["subsidy_se"] * f),
        })
    pd.DataFrame(rows).to_csv(output_dir / "16_water_bal_vol_table.csv", index=False)
    print("Volumetric table saved → 16_water_bal_vol_table.csv")


def make_chart_headspace(summary, output_path, manuscript=False):
    """Head-space bar chart (m/month)."""
    clusters = list(summary.keys())
    n = len(clusters)
    w = 0.28; gap = 0.05
    x = np.arange(n)
    x_loss = x - w/2 - gap/2
    x_inp  = x + w/2 + gap/2

    bg = "white" if manuscript else "#F7F4EF"
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg)
    ax.set_facecolor(bg); fig.patch.set_facecolor(bg)
    ymax = 0.60

    for i, cid in enumerate(clusters):
        s = summary[cid]
        # Losses bar
        ax.bar(x_loss[i], s["drainage"], w, color=C_DRAIN, alpha=0.85, edgecolor="white", lw=0.5, zorder=3)
        ax.bar(x_loss[i], s["pet_loss"], w, bottom=s["drainage"], color=C_ATM, alpha=0.85, edgecolor="white", lw=0.5, zorder=3)
        # Inputs bar
        ax.bar(x_inp[i], s["recharge"], w, color=C_RECH, alpha=0.85, edgecolor="white", lw=0.5, zorder=3)
        ax.bar(x_inp[i], s["subsidy"],  w, bottom=s["recharge"], color=C_SUB, alpha=0.78, edgecolor="white", lw=0.5, zorder=3)
        if s["intercept"] > 0:
            ax.bar(x_inp[i], s["intercept"], w, bottom=s["recharge"]+s["subsidy"], color=C_INT, alpha=0.80, edgecolor="white", lw=0.5, zorder=3)

        # Error bar on losses
        loss_top = s["drainage"] + s["pet_loss"]
        ax.errorbar(x_loss[i], loss_top, yerr=s["subsidy_se"],
                    fmt="none", color="#999999", capsize=4, capthick=1.2, elinewidth=1.2, zorder=6)

        # Value labels
        ax.text(x_loss[i], s["drainage"]/2, f"{s['drainage']:.3f}", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
        ax.text(x_loss[i], s["drainage"]+s["pet_loss"]/2, f"{s['pet_loss']:.3f}", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
        ax.text(x_inp[i],  s["recharge"]/2, f"{s['recharge']:.3f}", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
        ax.text(x_inp[i],  s["recharge"]+s["subsidy"]/2, f"{s['subsidy']:.3f}", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
        if s["intercept"] > 0:
            ax.text(x_inp[i], s["recharge"]+s["subsidy"]+s["intercept"]/2, f"{s['intercept']:.3f}", ha="center", va="center", fontsize=6.5, color="white", fontweight="bold")

        # Flooding frequency
        fc = "#1565C0" if cid in [1,2] else ("#B71C1C" if cid==3 else "#888888")
        ax.text(x[i], -0.11, f"Floods: {FLOOD_FREQ[cid]} of years",
                ha="center", va="top", fontsize=7.5, color=fc, fontweight="bold",
                transform=ax.get_xaxis_transform())

    ax.set_xticks(x)
    ax.set_xticklabels([CLUSTER_LABELS[c] for c in clusters], fontsize=9)
    ax.set_ylabel("m month⁻¹  (water table head change)", fontsize=10)
    ax.set_ylim(0, ymax)
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#CCCCCC")
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#EEEEEE", lw=0.7, zorder=0)

    legend_elements = [
        Patch(facecolor=C_DRAIN, alpha=0.85, label="Gravity drainage (β₃·|h̄|)"),
        Patch(facecolor=C_ATM,   alpha=0.85, label="Atmospheric draw (β₂·PET̄)"),
        Patch(facecolor=C_RECH,  alpha=0.85, label="Recharge (β₁·P̄)"),
        Patch(facecolor=C_SUB,   alpha=0.78, label="Boundary subsidy; error bars = ±1 SE"),
        Patch(facecolor=C_INT,   alpha=0.80, label="Canopy interception — C4 only"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=7.5,
              framealpha=1.0, edgecolor="#CCCCCC", ncol=2,
              handlelength=1.2, handletextpad=0.5, columnspacing=0.8, facecolor=bg)

    ax.set_title(
        "Mean Monthly Water Balance Decomposition — Newborough Warren 2005–2026\n"
        "Left bar = losses;  Right bar = inputs.  Bars equal height by construction.\n"
        "All terms in m month⁻¹ (head-space units of the state-space model).",
        fontsize=9, pad=10, color="#1A1A2E")

    dpi = 300 if manuscript else 150
    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor=bg)
    plt.close()
    print(f"Head-space chart saved → {output_path.name}")


def make_chart_volumetric(summary, output_path, manuscript=False):
    """Volumetric bar chart (mm/year, assumed Sy)."""
    clusters = list(summary.keys())
    n = len(clusters)
    w = 0.30; gap = 0.05
    x = np.arange(n)
    x_loss = x - w/2 - gap/2
    x_inp  = x + w/2 + gap/2

    bg = "white" if manuscript else "#F7F4EF"

    # Convert head-space to mm/year
    def v(val, cid): return round(val * 12 * SY[cid] * 1000)

    vol = {}
    for cid, s in summary.items():
        sy = SY[cid]
        vol[cid] = dict(
            drainage  = v(s["drainage"],   cid),
            pet_loss  = v(s["pet_loss"],   cid),
            recharge  = v(s["recharge"],   cid),
            subsidy   = v(s["subsidy"],    cid),
            intercept = v(s["intercept"],  cid),
            subsidy_se= v(s["subsidy_se"], cid),
            total_loss= v(s["drainage"] + s["pet_loss"], cid),
        )

    fig, ax = plt.subplots(figsize=(10, 6.5), facecolor=bg)
    ax.set_facecolor(bg); fig.patch.set_facecolor(bg)
    ymax = max(v["total_loss"] for v in vol.values()) * 1.70

    for i, cid in enumerate(clusters):
        vv = vol[cid]
        # Losses
        ax.bar(x_loss[i], vv["drainage"], w, color=C_DRAIN, alpha=0.82, edgecolor="white", lw=0.5, zorder=3)
        ax.bar(x_loss[i], vv["pet_loss"], w, bottom=vv["drainage"], color=C_ATM, alpha=0.82, edgecolor="white", lw=0.5, zorder=3)
        # Inputs
        ax.bar(x_inp[i], vv["recharge"], w, color=C_RECH, alpha=0.82, edgecolor="white", lw=0.5, zorder=3)
        ax.bar(x_inp[i], vv["subsidy"],  w, bottom=vv["recharge"], color=C_SUB, alpha=0.78, edgecolor="white", lw=0.5, zorder=3)
        if vv["intercept"] > 0:
            ax.bar(x_inp[i], vv["intercept"], w, bottom=vv["recharge"]+vv["subsidy"], color=C_INT, alpha=0.80, edgecolor="white", lw=0.5, zorder=3)

        # Error bar
        ax.errorbar(x_loss[i], vv["total_loss"], yerr=vv["subsidy_se"],
                    fmt="none", color="#999999", capsize=4, capthick=1.2, elinewidth=1.2, zorder=6)

        # Value labels
        ax.text(x_loss[i], vv["drainage"]/2, str(vv["drainage"]), ha="center", va="center", fontsize=7.5, color="white", fontweight="bold")
        ax.text(x_loss[i], vv["drainage"]+vv["pet_loss"]/2, str(vv["pet_loss"]), ha="center", va="center", fontsize=7.5, color="white", fontweight="bold")
        ax.text(x_inp[i],  vv["recharge"]/2, str(vv["recharge"]), ha="center", va="center", fontsize=7.5, color="white", fontweight="bold")
        ax.text(x_inp[i],  vv["recharge"]+vv["subsidy"]/2, str(vv["subsidy"]), ha="center", va="center", fontsize=7.5, color="white", fontweight="bold")
        if vv["intercept"] > 0:
            ax.text(x_inp[i], vv["recharge"]+vv["subsidy"]+vv["intercept"]/2, str(vv["intercept"]), ha="center", va="center", fontsize=7, color="white", fontweight="bold")

        # Subsidy annotation above error bar
        ax.text(x_loss[i], vv["total_loss"] + vv["subsidy_se"] + ymax*0.010,
                f"subsidy {vv['subsidy']}\n±{vv['subsidy_se']}",
                ha="center", va="bottom", fontsize=6.5, color="#555555", style="italic", linespacing=1.3)

        # Flooding frequency
        fc = "#1565C0" if cid in [1,2] else ("#B71C1C" if cid==3 else "#888888")
        ax.text(x[i], -0.12, f"Floods: {FLOOD_FREQ[cid]} of years",
                ha="center", va="top", fontsize=7.8, color=fc, fontweight="bold",
                transform=ax.get_xaxis_transform())

    ax.set_xticks(x)
    ax.set_xticklabels([CLUSTER_LABELS_VOL[c] for c in clusters], fontsize=8.8, linespacing=1.5)
    ax.set_ylabel("mm year⁻¹  (volumetric, assuming Sy)", fontsize=10)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_tick_params(labelsize=8.5)
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#CCCCCC")
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#EEEEEE", lw=0.7, zorder=0)

    legend_elements = [
        Patch(facecolor=C_DRAIN, alpha=0.82, label="Gravity drainage"),
        Patch(facecolor=C_ATM,   alpha=0.82, label="Atmospheric draw"),
        Patch(facecolor=C_RECH,  alpha=0.82, label="Recharge"),
        Patch(facecolor=C_SUB,   alpha=0.78, label="Boundary subsidy (ridge lateral recharge); error bars = ±1 SE"),
        Patch(facecolor=C_INT,   alpha=0.80, label="Canopy interception — C4 only"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=7.5,
              framealpha=1.0, edgecolor="#CCCCCC", ncol=2,
              handlelength=1.2, handletextpad=0.5, columnspacing=0.8, facecolor=bg)

    ax.set_title(
        "Indicative Annual Volumetric Water Balance — Newborough Warren 2005–2026\n"
        "Left bar = losses;  Right bar = inputs.  Bars equal height by construction.\n"
        "C1: Sy = 8%;  C2–C4: Sy = 12%.  Indicative only — Sy values assumed.",
        fontsize=9, pad=10, color="#1A1A2E")

    plt.tight_layout()
    dpi = 300 if manuscript else 150
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor=bg)
    plt.close()
    print(f"Volumetric chart saved → {output_path.name}")


def main():
    # ── Resolve paths ──────────────────────────────────────────────────────────
    out_dir     = DIR_16
    path_table  = OUT_16_TABLE
    path_lay    = OUT_16_BAR_LAY
    path_ms     = OUT_16_BAR_MS
    path_vol_ms = OUT_16_VOL_MS
    path_vol_lay= OUT_16_VOL_LAY

    # ── Run ────────────────────────────────────────────────────────────────────
    print("Loading data...")
    df, betas = load_data()

    print("Computing water balance components...")
    summary = compute_summary(df, betas)

    print("Exporting table...")
    export_table(summary, out_dir)

    print("Exporting volumetric table...")
    export_vol_table(summary, out_dir)

    print("Generating head-space charts...")
    make_chart_headspace(summary, path_lay, manuscript=False)
    make_chart_headspace(summary, path_ms,  manuscript=True)

    print("Generating volumetric charts...")
    make_chart_volumetric(summary, path_vol_ms,  manuscript=True)
    make_chart_volumetric(summary, path_vol_lay, manuscript=False)

    print("\nAll outputs written to", out_dir)


if __name__ == "__main__":
    main()
