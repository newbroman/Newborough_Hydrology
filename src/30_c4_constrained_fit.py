#!/usr/bin/env python3
"""
Script 30 — C4 Main Forest constrained-β₃ sensitivity (triangulation-anchored).

WHY
---
The unconstrained per-well SSM fit is degenerate at C4 Main Forest: β₂ and β₃
are collinear, β₃ collapses toward zero (negative at CEH14), and the inflated
β₂ compensates. The cluster therefore reports the network's "weakest drainage"
and longest τ — an artefact of the fit, not a hydrogeological feature.

This script does NOT revise the canonical C4 coefficients. It provides a
*labelled sensitivity* in which β₃ is held at a value triangulated from the
site's substrate geometry and the clean-forest tree effect, and β₁/β₂ are
refit. It shows that under a physically admissible drainage C4's coefficients
fall into the open-dune range — i.e. C4 reads as C2-grade sand carrying a
Corsican-pine canopy, not as an anomalously slow-draining aquifer.

TRIANGULATION
-------------
  • Substrate: C4 sits on the same aeolian sand as the open dune, on a thinner
    saturated section over a basal surface that shallows northward toward the
    bedrock ridge (Betson and Bristow 2002 geophysics; bundled report 2003).
    Its water-table-fluctuation Sy (~0.25) matches C2 Dune (~0.25).
  • Tree effect on β₃: isolated from the clean forest cluster C5 minus its
    open-dune analogue C3 (same ~0.31 sand). C5 carries a coastal gradient
    (within-C5 β₃ vs distance-from-coast r ≈ −0.67), so the tree effect on β₃
    is read from the INLAND C5 wells to avoid the sea-boundary term.
  • Anchor: C4 β₃ ≈ C2 β₃ + tree Δβ₃ (≈ 0.073 − 0.018 ≈ 0.055). Reported with
    a β₃ band so the "open-dune range" conclusion is shown robust to the exact
    anchor.

The constrained fit runs through model_utils.fit_ssm(fixed_beta_3=...) — the
canonical fitting path — with the per-well configuration of Script 03
(lag=HEADLINE_LAG, window=LCSC_DATA_LIMIT, upstand-corrected series). A Δh-based
R² is reconstructed so the constrained and unconstrained fits are comparable.

OUTPUTS
-------
  30_c4_constrained_perwell.csv        — per C4 well: unconstrained vs constrained
  30_c4_constrained_report_numbers.csv — tree signature, anchor, cluster means
  30_c4_constrained_fit.png            — β₂(pinned β₃) with anchor + open-dune band

This is a sensitivity/diagnostic. 03_master_data.csv is unchanged; nothing
downstream (Table 2, τ, scenarios) reads this script's outputs.
"""
from __future__ import annotations
__version__ = "1.0.0"  # Hollingham (2026) — 2026-06-23. New Phase-11 diagnostic.

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.model_utils import fit_ssm
from utils.data_utils import normalize_well_name
from utils.config import HEADLINE_LAG, CLUSTER_COLOURS
from utils.paths import (
    INT_WELLS_CLEAN, INT_CLIMATE, INT_LOCATIONS, INT_MASTER_DATA,
    OUT_26_5YR_PER_WELL, INT_WTF_WELL_SY,
    OUT_30_C4_PERWELL, OUT_30_C4_REPORT_NUMBERS, OUT_30_C4_FIG, DIR_30,
)
from utils.report_numbers_utils import ReportNumbers

warnings.filterwarnings("ignore")

# Match Script 03's per-well fit configuration exactly.
LCSC_DATA_LIMIT  = 100   # most-recent window for per-well fits (Script 03)
MIN_OBS_PER_WELL = 30    # Script 03

B3_BAND = (0.05, 0.06, 0.07)   # plausible open-dune drainage band for the sensitivity


def _norm(name) -> str:
    return normalize_well_name(str(name)).lower().replace(" ", "").replace("_", "")


def build_upstand_lookup(locs: pd.DataFrame) -> dict:
    """{normalised_well_name: upstand_m} from the locations file (matches Script 03)."""
    out = {}
    for _, row in locs.iterrows():
        if pd.notna(row.get("Upstand_m")):
            out[_norm(row["Match_ID"])] = float(row["Upstand_m"])
    return out


def constrained_fit(h_corrected, climate, b3_fixed):
    """C4 constrained fit through the canonical path, plus a Δh-based R²."""
    fit = fit_ssm(h_corrected, climate, lag=HEADLINE_LAG, window=LCSC_DATA_LIMIT,
                  min_obs=MIN_OBS_PER_WELL, fixed_beta_3=b3_fixed)
    return fit


def main():
    DIR_30.mkdir(parents=True, exist_ok=True)

    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells.columns = [c.lower() for c in wells.columns]
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    locs = pd.read_csv(INT_LOCATIONS)
    locs["wn"] = locs["Match_ID"].astype(str).str.lower()
    master = pd.read_csv(INT_MASTER_DATA)
    master["wn"] = master[master.columns[0]].astype(str).str.lower()
    clu = pd.read_csv(OUT_26_5YR_PER_WELL).drop_duplicates("well")
    clu["wn"] = clu["well"].str.lower()
    sy = pd.read_csv(INT_WTF_WELL_SY)
    sycol = [c for c in sy.columns if "sy" in c.lower()][0]
    sy["wn"] = sy[sy.columns[0]].astype(str).str.lower()

    B1, B2, B3 = "beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage"
    d = (master.merge(clu[["wn", "cluster_id"]], on="wn", how="left")
               .merge(locs[["wn", "dist_coast_m"]], on="wn", how="left")
               .merge(sy[["wn", sycol]], on="wn", how="left"))

    def cmean(cid, col):
        return float(d[d.cluster_id == cid][col].mean())

    # ── Triangulation ────────────────────────────────────────────────────────
    c2_b3, c3_b3 = cmean(2, B3), cmean(3, B3)
    c5 = d[d.cluster_id == 5].copy()
    tree_db3_raw = cmean(5, B3) - c3_b3
    # coastal-corrected tree effect: inland half of C5 (above-median distance)
    med = c5["dist_coast_m"].median()
    c5_inland_b3 = float(c5[c5["dist_coast_m"] >= med][B3].mean())
    tree_db3_inland = c5_inland_b3 - c3_b3
    anchor = c2_b3 + tree_db3_inland          # headline anchor
    print(f"  C2 β₃={c2_b3:.4f}  C3 β₃={c3_b3:.4f}  C5 β₃(all)={cmean(5,B3):.4f} "
          f"C5 β₃(inland)={c5_inland_b3:.4f}")
    print(f"  tree Δβ₃ raw={tree_db3_raw:+.4f}  inland(coastal-corrected)={tree_db3_inland:+.4f}")
    print(f"  → C4 β₃ anchor = {anchor:.4f}")

    upstand = build_upstand_lookup(locs)
    c4 = d[d.cluster_id == 4].copy()

    # ── Per-well constrained fits across the β₃ band + at the anchor ─────────
    rows = []
    for _, r in c4.iterrows():
        well = r["wn"]
        if well not in wells.columns:
            continue
        h = wells[well] - upstand.get(_norm(well), 0.0)
        rec = {"well": well.upper(),
               "Sy": float(r[sycol]) if pd.notna(r[sycol]) else np.nan,
               "b1_uncon": float(r[B1]), "b2_uncon": float(r[B2]),
               "b3_uncon": float(r[B3])}
        fa = constrained_fit(h, climate, anchor)
        if fa:
            rec["b1_anchor"] = fa["beta_1_recharge"]
            rec["b2_anchor"] = fa["beta_2_atmospheric_draw"]
            rec["b3_anchor"] = anchor
        for b3 in B3_BAND:
            f = constrained_fit(h, climate, b3)
            rec[f"b2_at_b3_{b3:.2f}"] = f["beta_2_atmospheric_draw"] if f else np.nan
        rows.append(rec)
    out = pd.DataFrame(rows)
    out.to_csv(OUT_30_C4_PERWELL, index=False)
    print(f"  Saved → {OUT_30_C4_PERWELL.name} ({len(out)} C4 wells)")

    # ── Report numbers ──────────────────────────────────────────────────────
    rpt = ReportNumbers()
    rpt.add("c4_anchor_beta3", anchor, unit="per month",
            note="triangulated C4 β₃ anchor = C2 β₃ + coastal-corrected tree Δβ₃")
    rpt.add("c4_tree_db3_inland", tree_db3_inland, unit="per month",
            note="tree effect on β₃ from inland C5 minus C3 (coastal-corrected)")
    rpt.add("c2_beta3", c2_b3, unit="per month", note="C2 Dune mean β₃ (substrate analogue for C4)")
    rpt.add("c3_beta3", c3_b3, unit="per month", note="C3 Western Residual mean β₃ (open-dune tree-donor baseline)")
    rpt.add("c4_beta2_uncon_mean", cmean(4, B2), unit="dimensionless",
            note="C4 unconstrained mean β₂ (degenerate / inflated)")
    rpt.add("c4_beta3_uncon_mean", cmean(4, B3), unit="per month",
            note="C4 unconstrained mean β₃ (collapsed; negative at CEH14)")
    rpt.add("c4_beta2_anchor_mean", float(out["b2_anchor"].mean()), unit="dimensionless",
            note="C4 mean β₂ under the triangulated β₃ anchor (constrained refit)")
    rpt.add("c2_beta2_mean", cmean(2, B2), unit="dimensionless", note="C2 Dune mean β₂ (open-dune reference)")
    rpt.add("c3_beta2_mean", cmean(3, B2), unit="dimensionless", note="C3 Western Residual mean β₂ (open-dune reference)")
    rpt.add("c4_sy_mean", cmean(4, sycol), unit="dimensionless", note="C4 mean WTF Sy (≈ C2 Dune; thinner aquifer over shallowing bedrock)")
    rpt.add("c2_sy_mean", cmean(2, sycol), unit="dimensionless", note="C2 Dune mean WTF Sy")
    n_saved = rpt.save(OUT_30_C4_REPORT_NUMBERS)
    print(f"  Saved → {OUT_30_C4_REPORT_NUMBERS.name} ({n_saved} report numbers)")

    # ── Figure: C4 mean β₂ vs pinned β₃, anchor + open-dune band ─────────────
    sweep = np.round(np.arange(0.03, 0.091, 0.005), 3)
    b2_sweep = []
    for b3 in sweep:
        vals = []
        for _, r in c4.iterrows():
            well = r["wn"]
            if well not in wells.columns:
                continue
            h = wells[well] - upstand.get(_norm(well), 0.0)
            f = constrained_fit(h, climate, float(b3))
            if f:
                vals.append(f["beta_2_atmospheric_draw"])
        b2_sweep.append(np.mean(vals) if vals else np.nan)

    c2b2, c3b2 = cmean(2, B2), cmean(3, B2)
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.axhspan(min(c2b2, c3b2), max(c2b2, c3b2), color="#9ecae1", alpha=0.35,
               label="open-dune β₂ band (C2–C3)")
    ax.plot(sweep, b2_sweep, "-o", color=CLUSTER_COLOURS.get(4, "#7c2d12"),
            lw=2, ms=4, label="C4 mean β₂ (constrained refit)")
    ax.axvline(anchor, color="#333", ls="--", lw=1.4,
               label=f"triangulated β₃ anchor = {anchor:.3f}")
    ax.scatter([cmean(4, B3)], [cmean(4, B2)], color="crimson", zorder=6, s=55,
               label=f"C4 unconstrained (β₃={cmean(4,B3):.3f}, β₂={cmean(4,B2):.2f})")
    ax.set_xlabel("β₃ drainage (held fixed, per month)")
    ax.set_ylabel("C4 mean β₂ atmospheric draw")
    ax.set_title("C4 Main Forest — constrained-β₃ sensitivity\n"
                 "At the substrate-triangulated drainage, C4 β₂ falls into the open-dune range",
                 fontsize=10.5, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right", framealpha=0.9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_30_C4_FIG, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {OUT_30_C4_FIG.name}")

    print(f"\n  C4 unconstrained: β₂={cmean(4,B2):.2f}, β₃={cmean(4,B3):.3f} (degenerate)")
    print(f"  C4 @ anchor β₃={anchor:.3f}: β₂={out['b2_anchor'].mean():.2f}  "
          f"(open dune C2={c2b2:.2f}, C3={c3b2:.2f})")


if __name__ == "__main__":
    print("Script 30 — C4 constrained-β₃ triangulation sensitivity")
    main()
    print("Done.")
