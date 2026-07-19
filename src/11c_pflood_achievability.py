"""
11c_pflood_achievability.py — Per-well categorical priority map for
P_flood-based scrape-target identification.

Routed from the 2026-05-29 main-report editorial review (gap C in the
post-review priorities list). Main report §7 Conclusion 4 reads:

    "Priority targets are the C1/C2/C3 transitional wells where the
     aquifer base is stable and P_flood thresholds remain achievable
     (rainfall multiplier λ < 1.5)."

Conclusion 4 names criteria but does not show which wells they identify.
This script consumes the per-well P_flood multipliers already produced by
Script 11b (`11b_03_pflood_per_well.csv`) and produces a single operational
figure that colour-codes each well by achievability category, on the
canonical site DEM + KML overlay.

Categories:
- Achievable (λ < 1.5):   P_flood is reachable in normal-to-mildly-wet winters
- Marginal (1.5 ≤ λ < 2.5): P_flood is reachable only in wet winters
- Unreachable (λ ≥ 2.5):  P_flood is effectively unreachable under current climate

Reads:
- `11b_03_pflood_per_well.csv` (Script 11b, step 12)
- DEM (data/) for hillshade
- KML features (data/) for forest boundary and site features

Writes:
- `11c_pflood_achievability.png` — categorical map (operational figure for §5.9 / Conclusion 4)
- `11c_pflood_achievability_per_well.csv` — per-well lookup with category column
- `11c_pflood_achievability_results.md` — memo with summary tables and report drop-in text

Standalone diagnostic following the 11b naming convention (output sharing
DIR_11B since the input lives there). To enter the orchestrator at Phase 3
as a successor step to 11b, following the 14b → Script 14 pattern.
"""

from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-06-28
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
# 1.1.1 — Output paths now reference the canonical OUT_11C_* constants in
#         paths.py (added same day). Removes the local DIR_11B re-derivation;
#         single source of truth. No change to output filenames or contents.
# 1.1.0 — Map brought into line with the canonical spatial-figure
#         conventions (matches Script 11b siblings):
#           * Map extent now clamped to the canonical site footprint
#             imported from config (SITE_MAP_EAST_MIN/MAX, NORTH_MIN/MAX)
#             instead of letting matplotlib auto-fit to the forest KML.
#           * Equal aspect ratio set (no geometric distortion).
#           * Title styled fontsize=10, fontweight="bold" to match 11b.
#           * Axis labels/ticks sized to 11b convention.
#           * Marker sizes/edges aligned to the 11b sibling maps.
# 1.0.0 — Initial. Categorical achievability map for §5.9 / Conclusion 4.

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path

# ── Pipeline imports ──────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
REPO = _HERE.parent
DATA_DIR = REPO / "data"
sys.path.insert(0, str(_HERE))

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils import paths  # noqa: E402
from utils.map_utils import load_dem_hillshade, add_kml_features  # noqa: E402
from utils.config import (  # noqa: E402
    SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX,
    SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX,
)
from utils.render_utils import render_figure

paths.make_all_dirs()

F_PFLOOD = paths.OUT_11B_PFLOOD_PER_WELL

# Output paths now live in the canonical paths.py (OUT_11C_* constants,
# added 2026-05-29). Reference them directly — single source of truth.
OUT_MAP  = paths.OUT_11C_ACHIEVABILITY_MAP
OUT_CSV  = paths.OUT_11C_PER_WELL
OUT_MEMO = paths.OUT_11C_RESULTS_MEMO

# ── Achievability scheme ──────────────────────────────────────────────────
# Matches Conclusion 4 explicit λ<1.5 criterion. The 1.5-2.5 marginal band
# is the "only wet winters" zone; λ≥2.5 is the "effectively unreachable"
# zone defined by requiring more than 2.5× the climatological winter mean.

LAMBDA_ACHIEVABLE_MAX = 1.5
LAMBDA_MARGINAL_MAX   = 2.5

CATEGORY_COLOURS = {
    "Achievable":  "#3a8f3a",  # forest green
    "Marginal":    "#e6a417",  # amber
    "Unreachable": "#b73030",  # red
}
CATEGORY_DEFS = {
    "Achievable":  "Achievable (λ < 1.5) — reachable in normal-to-mildly-wet winters",
    "Marginal":    "Marginal (1.5 ≤ λ < 2.5) — reachable only in wet winters",
    "Unreachable": "Unreachable (λ ≥ 2.5) — effectively unreachable under current climate",
}


def categorise(lam: float) -> str:
    if lam < LAMBDA_ACHIEVABLE_MAX:
        return "Achievable"
    if lam < LAMBDA_MARGINAL_MAX:
        return "Marginal"
    return "Unreachable"


# ── Load and categorise ───────────────────────────────────────────────────

print("─" * 72)
print("11c — P_flood achievability map (gap C)")
print("─" * 72)

df = pd.read_csv(F_PFLOOD)
df["category"] = df["lambda"].apply(categorise)
print(f"Loaded {len(df)} wells from {F_PFLOOD.relative_to(REPO)}")

# Summary table per cluster × category
print()
print("─── Category counts by cluster ──────────────────────────────────")
counts = pd.crosstab(df["cluster"], df["category"]).reindex(
    columns=["Achievable", "Marginal", "Unreachable"], fill_value=0
)
print(counts.to_string())
print()
print("─── Totals ──────────────────────────────────────────────────────")
total_counts = df["category"].value_counts().reindex(["Achievable", "Marginal", "Unreachable"], fill_value=0)
print(total_counts.to_string())

# Save the augmented per-well CSV
df_out = df[["well", "E", "N", "cluster", "network", "depth_bg",
              "lambda", "pflood_mm", "category"]].copy()
df_out.to_csv(OUT_CSV, index=False)
print(f"\nWrote {OUT_CSV.relative_to(REPO)}")


# ── Figure ────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")

# DEM hillshade
_, ok, *_ = load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
if not ok:
    warn("DEM hillshade unavailable — map may lack context.")

# KML features (forest boundary, etc.)
kml_handles = add_kml_features(ax, DATA_DIR, include_streams=False)

# Wells, coloured by category, marker by network (reference vs extended)
for category in ["Achievable", "Marginal", "Unreachable"]:
    col = CATEGORY_COLOURS[category]
    sub = df[df["category"] == category]
    for net, mk, sz in [("Reference", "o", 60), ("Extended", "D", 48)]:
        sub_net = sub[sub["network"] == net]
        if not sub_net.empty:
            ax.scatter(
                sub_net["E"], sub_net["N"],
                c=col, marker=mk, s=sz,
                edgecolor="black", linewidth=0.6,
                alpha=0.95, zorder=5,
            )

# Compose legend: categories first, then network markers, then KML
legend_items = []
for category in ["Achievable", "Marginal", "Unreachable"]:
    n = (df["category"] == category).sum()
    legend_items.append(
        Patch(facecolor=CATEGORY_COLOURS[category], edgecolor="black",
              label=f"{CATEGORY_DEFS[category]}  (n = {n})")
    )
# Network markers — give them invisible-fill markers as a key
legend_items.append(
    plt.Line2D([], [], marker="o", color="black", linestyle="",
                markerfacecolor="white", markersize=8, label="Reference well")
)
legend_items.append(
    plt.Line2D([], [], marker="D", color="black", linestyle="",
                markerfacecolor="white", markersize=7, label="Extended well")
)
legend_items.extend(kml_handles or [])

ax.legend(handles=legend_items, loc="upper left", fontsize=8,
           framealpha=0.95, ncol=1)

# Title and labels — styled to match the 11b sibling maps
ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
ax.tick_params(labelsize=8)
ax.set_title(
    "P_flood achievability — per-well priority categories for scrape targeting\n"
    "λ = required winter rainfall / climatological mean. Categories follow "
    "Conclusion 4 (main report).",
    fontsize=10, fontweight="bold",
)

# Site-map extent and equal aspect. NOTE: 11c is intentionally left at its
# prior extent (northern edge 365800), NOT the canonical 365500 — by request,
# 11b/11c keep their existing frames. The northern bound is pinned locally so it
# is unaffected by the config SITE_MAP_NORTH_MAX change (now 365500).
_NORTH_MAX_11C = 365800   # local pin; do not repoint to config.SITE_MAP_NORTH_MAX
ax.set_xlim(SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX)
ax.set_ylim(SITE_MAP_NORTH_MIN, _NORTH_MAX_11C)
ax.set_aspect("equal")

fig.tight_layout()
render_figure(fig, OUT_MAP)
plt.close(fig)
print(f"Wrote {OUT_MAP.relative_to(REPO)}")


# ── Memo ──────────────────────────────────────────────────────────────────

memo_lines = [
    "# P_flood achievability — results",
    "",
    "*Diagnostic from `11c_pflood_achievability.py`. Routed from the 2026-05-29",
    "main-report editorial review (gap C: per-well operational priority map for",
    "§5.9 and §7 Conclusion 4).*",
    "",
    "## Categorical scheme",
    "",
    "Three bins on the rainfall multiplier λ from Script 11b (`11b_03_pflood_per_well.csv`).",
    "λ is the cumulative winter-rainfall multiplier required to lift the cluster",
    "summer minimum back above the relevant Curreli (2013) threshold by the end of",
    "the recharge season.",
    "",
    "| Category | λ band | Operational meaning |",
    "|---|---|---|",
    "| **Achievable** | λ < 1.5 | Reachable in normal-to-mildly-wet winters |",
    "| **Marginal** | 1.5 ≤ λ < 2.5 | Reachable only in wet winters |",
    "| **Unreachable** | λ ≥ 2.5 | Effectively unreachable under current climate |",
    "",
    "## Counts by category and cluster",
    "",
    "| Cluster | Achievable | Marginal | Unreachable | Cluster total |",
    "|---|---|---|---|---|",
]
for cl in sorted(counts.index):
    row = counts.loc[cl]
    total = row.sum()
    memo_lines.append(
        f"| C{cl} | {row.get('Achievable', 0)} | {row.get('Marginal', 0)} | {row.get('Unreachable', 0)} | {total} |"
    )
total = counts.sum().sum()
memo_lines.append(
    f"| **All clusters** | **{counts['Achievable'].sum()}** | **{counts['Marginal'].sum()}** | **{counts['Unreachable'].sum()}** | **{total}** |"
)

memo_lines += [
    "",
    "## Reading",
    "",
    f"- **Open dune zone (C1, C2, C3): {counts.loc[[1,2,3], 'Achievable'].sum()} of {counts.loc[[1,2,3]].sum().sum()} wells achievable**, "
    f"with the remaining {counts.loc[[1,2,3], 'Marginal'].sum()} marginal — none unreachable. "
    "This is the operational domain Conclusion 4 identifies for scrape targeting.",
    f"- **Forest zone (C4, C5): {counts.loc[[4,5], 'Achievable'].sum()} of {counts.loc[[4,5]].sum().sum()} wells achievable**, "
    f"with {counts.loc[[4,5], 'Marginal'].sum()} marginal and {counts.loc[[4,5], 'Unreachable'].sum()} unreachable. "
    f"Most forest wells require more than mildly-wet winters; "
    f"the unreachable wells split {counts.loc[5, 'Unreachable']} in C5 Coastal Forest and "
    f"{counts.loc[4, 'Unreachable']} in C4 Main Forest.",
    "",
    "The cluster pattern reflects the underlying mechanism. The open dune clusters",
    "(C1 Lake Edge, C2 Dune, C3 Western Residual) sit on the shallow-substrate or",
    "deep-sponge aquifer parcels where summer minima respond to winter recharge",
    "with high efficiency (β₁ in the 2.5–4.6 range). The forest clusters (C4 Main",
    "Forest, C5 Coastal Forest) carry canopy interception losses and lower β₁",
    "(1.32–2.55), and C5 additionally carries the coastal-retreat gradient (Section",
    "4.8.1), pushing its summer-minimum baseline progressively further below the",
    "Curreli thresholds and increasing the rainfall multiplier required to recover.",
    "",
    "## Drop-in text for §5.9 (Implications for Restoration and Monitoring)",
    "",
    "Insert as a new paragraph in §5.9 after the topographic-scraping discussion,",
    "between the existing \"the operational zone for this intervention\" sentence and",
    "the prediction-equations paragraph:",
    "",
]

# Build a data-driven phrase for the cluster split of unreachable wells, so this
# text can never go stale relative to the committed CSV. Wells are listed in
# upper-case (matches Conclusion-4 / report convention) and sorted by lambda.
_unr = df[df["category"] == "Unreachable"].sort_values("lambda", ascending=False)
_c5_wells = [w.upper() for w in _unr.loc[_unr["cluster"] == 5, "well"]]
_c4_wells = [w.upper() for w in _unr.loc[_unr["cluster"] == 4, "well"]]
def _join(items):
    return items[0] if len(items) == 1 else (", ".join(items[:-1]) + " and " + items[-1])
_parts = []
if _c5_wells:
    _parts.append(f"{len(_c5_wells)} in C5 Coastal Forest ({_join(_c5_wells)})")
if _c4_wells:
    _parts.append(f"{len(_c4_wells)} in C4 Main Forest ({_join(_c4_wells)})")
_unr_split = " and ".join(_parts) if _parts else "none"

memo_lines += [
    "> *Per-well categorisation against the P_flood multiplier (Figure N; `11c_pflood_achievability_per_well.csv`) operationalises the priority criterion identified in Conclusion 4. Of "
    + f"{counts.loc[[1,2,3], 'Achievable'].sum()} wells across the open-dune clusters C1, C2 and C3, "
    + f"all but {counts.loc[[1,2,3], 'Marginal'].sum()} are in the achievable category (λ < 1.5); none are unreachable. "
    + f"By contrast, of the {counts.loc[[4,5]].sum().sum()} forest-zone wells in C4 and C5, only {counts.loc[[4,5], 'Achievable'].sum()} sit in the achievable band and "
    + f"{counts.loc[[4,5], 'Unreachable'].sum()} are in the unreachable band (λ ≥ 2.5): {_unr_split}. The categorisation provides a direct per-well lookup for scrape-targeting decisions: achievable wells in the C1/C2/C3 transitional zone are the operationally feasible candidates; the small number of marginal wells in the open dune (n = "
    + f"{counts.loc[[1,2,3], 'Marginal'].sum()}) define the upper edge of the operational envelope under current climate.*",
    "",
    "## Suggested figure caption",
    "",
    "> *Figure N. Per-well achievability categorisation against the P_flood rainfall multiplier (λ), the cumulative winter-rainfall depth required to lift each well's summer minimum back above the relevant Curreli (2013) threshold by end of recharge season, expressed as a multiple of climatological winter mean. Wells in the achievable category (λ < 1.5, green) are reachable in normal-to-mildly-wet winters; marginal wells (1.5 ≤ λ < 2.5, amber) only in wet winters; unreachable wells (λ ≥ 2.5, red) are effectively unreachable under current climate. The cluster pattern (open-dune C1/C2/C3 dominated by achievable; forest C4/C5 dominated by marginal-to-unreachable) operationalises Conclusion 4's priority criterion for scrape-target identification. Source: `11c_pflood_achievability.png`; per-well lookup table in `11c_pflood_achievability_per_well.csv`.*",
    "",
    "## Caveats",
    "",
    "- The λ values come from Script 11b's per-well calculation; they inherit Script 11b's assumptions about the cluster β coefficients and the climatological winter rainfall baseline. The categorical bin edges (1.5 and 2.5) are operational choices, not derived from any natural break in the data. Conclusion 4's text explicitly identifies the λ < 1.5 boundary; the marginal-vs-unreachable boundary at λ = 2.5 is selected to match the abstract's reference to a 1.5–2.5× rainfall multiplier band as the conservatively wet-winter zone.",
    "- The achievability category describes whether the cluster summer minimum can be raised above the Curreli threshold by winter recharge alone. It does not account for scrape-as-drainage geometry effects (Section 4.5.3) or for forest-management interventions; these are separate degrees of freedom in the scenario framework (Section 4.10).",
    "- Wells flagged as scraped in the existing per-well CSV (CEH36, CEH18, CEH21) retain their categorical assignment based on present-day λ; the category reflects post-intervention behaviour where applicable.",
    "",
    "## Outputs",
    "",
    "- `11c_pflood_achievability.png` — operational map for §5.9 / Conclusion 4.",
    "- `11c_pflood_achievability_per_well.csv` — per-well lookup table with category column.",
    "- `11c_pflood_achievability_results.md` — this memo.",
]

OUT_MEMO.write_text("\n".join(memo_lines))
print(f"Wrote {OUT_MEMO.relative_to(REPO)}")
print()
print("─" * 72)
done()
print("─" * 72)
