"""
11c_pflood_achievability.py — Per-well categorical priority map for
P_flood-based scrape-target identification.

Routed from the 2026-05-29 main-report editorial review (gap C in the
post-review priorities list). Main report §7 Conclusion 6 reads:

    "Priority targets are the C1/C2/C3o transitional wells where the
     aquifer base is stable and P_flood thresholds remain achievable
     (rainfall multiplier m_P < 1.5)."

Conclusion 6 names criteria but does not show which wells they identify.
This script consumes the per-well P_flood multipliers already produced by
Script 11b (`11b_03_pflood_per_well.csv`) and produces a single operational
figure that colour-codes each well by achievability category, on the
canonical site DEM + KML overlay.

Categories:
- Achievable (m_P < 1.5):   P_flood is reachable in normal-to-mildly-wet winters
- Marginal (1.5 ≤ m_P < 2.5): P_flood is reachable only in wet winters
- Unreachable (m_P ≥ 2.5):  P_flood is effectively unreachable under current climate

Reads:
- `11b_03_pflood_per_well.csv` (Script 11b)
- DEM (data/) for hillshade
- KML features (data/) for forest boundary and site features

Writes:
- `11c_pflood_achievability.png` — categorical map (operational figure for §5.9 / Conclusion 6)
- `11c_pflood_achievability_per_well.csv` — per-well lookup with category column
- `11c_pflood_achievability_results.md` — memo with summary tables and report drop-in text

Standalone diagnostic following the 11b naming convention (output sharing
DIR_11B since the input lives there). Wired into run_analysis.py as a successor
step to 11b, following the 14b → Script 14 pattern; the canonical phase and step
index are in outputs/pipeline_manifest.json.
"""

from __future__ import annotations

__version__ = "1.10.0"  # 2026-11-27 (D-349 A14, (8)): the memo's beta_1 ranges from the group centroids at run time (were typed, stale: 2.5-4.6 / 1.32-2.55); the open zone's unreachable count read, not asserted; no cross-reference to a report section; the open/forest tallies leave out the edge wells (cluster_series.is_edge) in place of LANDCOVER_SET_ASIDE_WELLS.
# 1.9.0  # 2026-11-27 (D-348): open/forest zone tallies from FOREST_CIDS (open = C1, C2, C3o; forest = C4, C3f) with the set-aside well left out, no KeyError on a missing group; memo text names C3o and C3f. Was "1.8.1"  # Hollingham (2026) — 2026-11-26 (D-347): the figure text names C3 Western Dune.
# 1.8.0  # Hollingham (2026) - 2026-10-06. T-96: emits the summer-minimum depth range
#   (depth_bg min / max) of the wells in each category, which report10 quotes for the Unreachable wells. Emit-only.
# 1.7.0  # Hollingham (2026) - 2026-10-04 (changelog 2026-10-04d). The class edges are now
#   config.MP_ACHIEVABLE_MAX / MP_MARGINAL_MAX, shared with the Forecaster (11b 1.19.0). No value moves.
# 1.6.0  # Hollingham (2026) - 2026-09-29. T-96 (batch 2): first report-numbers file,
#   11c_report_numbers.csv (paths.OUT_11C_REPORT_NUMBERS) - achievability_n and achievability_share_pct
#   per category (Well = the category) over the wells of 11b_03 (report10 SS5.8.1: 59 / 24 / 5 of 88).
#   The class edges LAMBDA_ACHIEVABLE_MAX / LAMBDA_MARGINAL_MAX stay local for now. Additive.
# 1.5.1  # Hollingham (2026) - 2026-09-28. Text only: the m_P < 1.5 criterion is now §7 Conclusion 6 (was 4).
# 1.5.0  # Hollingham (2026) — 2026-09-28. The categories are also drawn as a surface:
#   m_P on the house linear surface (D-206), banded at 1.5 / 2.5, ridge-masked (1 m) and clipped to the
#   site, under the well markers (Martin, proofread: "should be a surface and ridge masked"). Display only.
# 1.4.0  # Hollingham (2026) — 2026-09-28. Title drops "Categories follow Conclusion 6
#   (main report)": the criterion is Conclusion 6, and conclusion numbers belong in the report text,
#   not a figure (proofread). Display only.
# 1.3.0  # Hollingham (2026) — 2026-09-24. Display symbol λ → m_P: the figure
#   title and legend said λ for the P_flood rainfall multiplier while the report
#   (§4.7.4, §5.9, the Notation table) says m_P, and λ is the forest drawdown reach
#   everywhere else in the corpus. Caught by the 2026-09-24 caption-against-figure
#   proof pass (Figure 83); Martin: "the header in the figure needs updating". The
#   `lambda` COLUMN in 11c_01 is unchanged (consumers key on it); only the rendered
#   strings and this docstring move. Re-run to regenerate the PNG.
# 1.2.0  # 2026-06-28
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path

# ── Pipeline imports ──────────────────────────────────────────────────────
def main():
    _HERE = Path(__file__).resolve().parent
    REPO = _HERE.parent
    DATA_DIR = REPO / "data"
    sys.path.insert(0, str(_HERE))

    from utils.console_utils import (
        banner, phase, step, info, saved, warn, error, note, done, result,
        hr, skipped,
    )
    from utils import paths  # noqa: E402
    from utils.map_utils import load_dem_hillshade, add_kml_features, add_idw_surface  # noqa: E402
    from matplotlib.colors import ListedColormap, BoundaryNorm  # noqa: E402
    from utils.config import (  # noqa: E402
        SITE_MAP_EAST_MIN, SITE_MAP_EAST_MAX,
        SITE_MAP_NORTH_MIN, SITE_MAP_NORTH_MAX,
        MP_ACHIEVABLE_MAX, MP_MARGINAL_MAX,
        CLUSTER_LABELS, CLUSTER_SHORT, FOREST_CIDS,
    )
    from utils.cluster_series import is_edge   # 1.10.0 (D-349 (8)): the edge rule replaces the set-aside list
    from utils.render_utils import render_figure
    from utils.report_numbers_utils import ReportNumbers

    paths.make_all_dirs()

    F_PFLOOD = paths.OUT_11B_PFLOOD_PER_WELL

    # Output paths now live in the canonical paths.py (OUT_11C_* constants,
    # added 2026-05-29). Reference them directly — single source of truth.
    OUT_MAP  = paths.OUT_11C_ACHIEVABILITY_MAP
    OUT_CSV  = paths.OUT_11C_PER_WELL
    OUT_MEMO = paths.OUT_11C_RESULTS_MEMO

    # ── Achievability scheme ──────────────────────────────────────────────────
    # Matches Conclusion 6 explicit m_P<1.5 criterion. The 1.5-2.5 marginal band
    # is the "only wet winters" zone; m_P≥2.5 is the "effectively unreachable"
    # zone defined by requiring more than 2.5× the climatological winter mean.

    LAMBDA_ACHIEVABLE_MAX = MP_ACHIEVABLE_MAX
    LAMBDA_MARGINAL_MAX   = MP_MARGINAL_MAX

    CATEGORY_COLOURS = {
        "Achievable":  "#3a8f3a",  # forest green
        "Marginal":    "#e6a417",  # amber
        "Unreachable": "#b73030",  # red
    }
    CATEGORY_DEFS = {
        "Achievable":  "Achievable (m_P < 1.5) — reachable in normal-to-mildly-wet winters",
        "Marginal":    "Marginal (1.5 ≤ m_P < 2.5) — reachable only in wet winters",
        "Unreachable": "Unreachable (m_P ≥ 2.5) — effectively unreachable under current climate",
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
    # D-348: the open (groups 1-3) and forest (FOREST_CIDS: C4, C3f) zone tallies of the memo. 1.10.0 (D-349 (8)):
    # a per-well forest/open comparison leaves out the EDGE wells (cluster_series.is_edge: inside, or within
    # config.LANDCOVER_EDGE_M of, the 2017 clearfell or the 1995 broadleaf restock), which replaces the single
    # set-aside well WMC3; the per-cluster table above keeps every well.
    _edge = df["well"].astype(str).map(is_edge)
    _zone_df = df[~_edge]
    print(f"Edge wells left out of the open/forest tallies (D-349): "
          f"{', '.join(sorted(df.loc[_edge, 'well'].astype(str).str.upper())) or 'none'}")
    zone_counts = pd.crosstab(_zone_df["cluster"], _zone_df["category"]).reindex(
        index=sorted(CLUSTER_LABELS), columns=["Achievable", "Marginal", "Unreachable"], fill_value=0)
    _OPEN = [c for c in sorted(CLUSTER_LABELS) if c not in FOREST_CIDS]
    _FOREST = [c for c in sorted(CLUSTER_LABELS) if c in FOREST_CIDS]

    # Save the augmented per-well CSV
    df_out = df[["well", "E", "N", "cluster", "network", "depth_bg",
                  "lambda", "pflood_mm", "category"]].copy()
    df_out.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV.relative_to(REPO)}")

    # Report numbers (T-96): the category counts and shares report10 SS5.8.1
    # quotes, over every well in the 11b per-well table. Shares unrounded (D-035).
    rpt = ReportNumbers()
    _n_all = int(total_counts.sum())
    for _cat, _n in total_counts.items():
        rpt.add("achievability_n", int(_n), unit="wells", well=_cat,
                note=f"wells in the {_cat} category ({CATEGORY_DEFS[_cat].split(' — ')[0]}), of n={_n_all}")
    for _cat, _n in total_counts.items():
        rpt.add("achievability_share_pct", 100.0 * float(_n) / _n_all, unit="%", well=_cat,
                note=f"share of the n={_n_all} wells in the {_cat} category")
    # T-96: the summer-minimum depth range of each category's wells (report10 SS5.8.1).
    for _cat, _g in df_out.groupby("category"):
        _dz = _g["depth_bg"].dropna()
        if len(_dz):
            rpt.add("achievability_depth_bg_min_m", float(_dz.min()), unit="m", well=_cat,
                    note=f"shallowest summer-minimum depth below ground (depth_bg) among the {_cat} wells, n={len(_dz)}")
            rpt.add("achievability_depth_bg_max_m", float(_dz.max()), unit="m", well=_cat,
                    note=f"deepest summer-minimum depth below ground (depth_bg) among the {_cat} wells, n={len(_dz)}")
    _n_saved = rpt.save(paths.OUT_11C_REPORT_NUMBERS)
    saved(f"{paths.OUT_11C_REPORT_NUMBERS.name} ({_n_saved} rows)")


    # ── Figure ────────────────────────────────────────────────────────────────

    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")

    # DEM hillshade
    _, ok, dem_e, dem_n, dem_data = load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    if not ok:
        warn("DEM hillshade unavailable — map may lack context.")

    # 1.5.0: the categories as a surface — m_P interpolated with the house linear
    # surface (D-206; P_flood has leave-one-well-out skill ~0.7), banded at the two
    # category limits, ridge-masked like the 11b P_flood map and clipped to the site.
    _cat_cmap = ListedColormap([CATEGORY_COLOURS[c] for c in ["Achievable", "Marginal", "Unreachable"]])
    _cat_norm = BoundaryNorm([0.0, LAMBDA_ACHIEVABLE_MAX, LAMBDA_MARGINAL_MAX, 1e6], _cat_cmap.N)
    add_idw_surface(
        ax, df, value_col="lambda", dem_col="dem",
        method="linear", ridge_mask_threshold=1.0,
        dem_e_arr=dem_e, dem_n_arr=dem_n, dem_data=dem_data,
        cmap=_cat_cmap, norm=_cat_norm, alpha=0.40, zorder=2,
        apply_site_mask=True,
    )

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
        "m_P = required winter rainfall / climatological mean.",   # 1.4.0: hard-typed conclusion number dropped
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
        "§5.9 and §7 Conclusion 6).*",
        "",
        "## Categorical scheme",
        "",
        "Three bins on the rainfall multiplier m_P from Script 11b (`11b_03_pflood_per_well.csv`).",
        "m_P is the cumulative winter-rainfall multiplier required to lift the cluster",
        "summer minimum back above the relevant Curreli (2013) threshold by the end of",
        "the recharge season.",
        "",
        "| Category | m_P band | Operational meaning |",
        "|---|---|---|",
        "| **Achievable** | m_P < 1.5 | Reachable in normal-to-mildly-wet winters |",
        "| **Marginal** | 1.5 ≤ m_P < 2.5 | Reachable only in wet winters |",
        "| **Unreachable** | m_P ≥ 2.5 | Effectively unreachable under current climate |",
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
            f"| {CLUSTER_SHORT.get(int(cl), f'C{cl}')} | {row.get('Achievable', 0)} | {row.get('Marginal', 0)} | {row.get('Unreachable', 0)} | {total} |"
        )
    total = counts.sum().sum()
    memo_lines.append(
        f"| **All clusters** | **{counts['Achievable'].sum()}** | **{counts['Marginal'].sum()}** | **{counts['Unreachable'].sum()}** | **{total}** |"
    )

    # 1.10.0 (D-349 A14): the beta_1 ranges are the group centroids' (pipeline_params.load_params, Script 03's Model B
    # cluster-level centroids) read at run time; the text held stale typed ranges (2.5-4.6 open, 1.32-2.55 forest,
    # 1.32 being C3f's beta_2) that matched no committed value. And the open zone's unreachable count is read, not
    # asserted.
    from utils.pipeline_params import load_params
    _cl = load_params(warn_defaults=False)["clusters"]
    _b1 = {int(k[1:]): float(v["b1"]) for k, v in _cl.items() if str(k)[1:].isdigit()}
    def _rng(ids):
        v = [_b1[i] for i in ids if i in _b1]
        return f"{min(v):.2f}–{max(v):.2f}" if v else "n/a"
    _b1_open, _b1_forest = _rng(_OPEN), _rng(_FOREST)
    _open_unr = int(zone_counts.loc[_OPEN, 'Unreachable'].sum())
    _n_edge = int(_edge.sum())

    memo_lines += [
        "",
        "## Reading",
        "",
        f"The open and forest zone tallies leave out the {_n_edge} edge wells (within the D-349 edge distance of the "
        "2017 clearfell or the 1995 broadleaf restock); the cluster table above keeps them.",
        "",
        f"- **Open dune zone (C1, C2, C3o): {zone_counts.loc[_OPEN, 'Achievable'].sum()} of {zone_counts.loc[_OPEN].sum().sum()} wells achievable**, "
        f"with {zone_counts.loc[_OPEN, 'Marginal'].sum()} marginal and "
        + (f"none unreachable. " if _open_unr == 0 else f"{_open_unr} unreachable. ")
        + "This is the operational domain Conclusion 6 identifies for scrape targeting.",
        f"- **Forest zone (C4, C3f): {zone_counts.loc[_FOREST, 'Achievable'].sum()} of {zone_counts.loc[_FOREST].sum().sum()} wells achievable**, "
        f"with {zone_counts.loc[_FOREST, 'Marginal'].sum()} marginal and {zone_counts.loc[_FOREST, 'Unreachable'].sum()} unreachable. "
        f"Most forest wells require more than mildly-wet winters; "
        f"the unreachable wells split {zone_counts.loc[5, 'Unreachable']} in C3f (Western Dune, forest) and "
        f"{zone_counts.loc[4, 'Unreachable']} in C4 Main Forest.",
        "",
        "The cluster pattern reflects the underlying mechanism. The open dune groups",
        "(C1 Lake Edge, C2 Dune, C3o Western Dune, open) sit on the shallow-substrate or",
        "deep-sponge aquifer parcels where summer minima respond to winter recharge",
        f"with high efficiency (group-centroid β₁ {_b1_open}). The forest groups (C4 Main",
        f"Forest, C3f Western Dune forest) carry canopy interception losses and lower β₁",
        f"({_b1_forest}), and C3f additionally carries the coastal-retreat gradient (Script",
        "25), pushing its summer-minimum baseline progressively further below the",
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
    _unr = _zone_df[_zone_df["category"] == "Unreachable"].sort_values("lambda", ascending=False)   # 1.10.0: same wells as the tallies
    _c5_wells = [w.upper() for w in _unr.loc[_unr["cluster"] == 5, "well"]]
    _c4_wells = [w.upper() for w in _unr.loc[_unr["cluster"] == 4, "well"]]
    def _join(items):
        return items[0] if len(items) == 1 else (", ".join(items[:-1]) + " and " + items[-1])
    _parts = []
    if _c5_wells:
        _parts.append(f"{len(_c5_wells)} in C3f (Western Dune, forest) ({_join(_c5_wells)})")
    if _c4_wells:
        _parts.append(f"{len(_c4_wells)} in C4 Main Forest ({_join(_c4_wells)})")
    _unr_split = " and ".join(_parts) if _parts else "none"

    memo_lines += [
        "> *Per-well categorisation against the P_flood multiplier (Figure N; `11c_pflood_achievability_per_well.csv`) operationalises the priority criterion identified in Conclusion 6. Of "
        + f"{zone_counts.loc[_OPEN].sum().sum()} wells across the open-dune groups C1, C2 and C3o, "
        + f"{zone_counts.loc[_OPEN, 'Achievable'].sum()} are in the achievable category (m_P < 1.5) and "
        + ("none are unreachable. " if _open_unr == 0 else f"{_open_unr} are unreachable. ")
        + f"By contrast, of the {zone_counts.loc[_FOREST].sum().sum()} forest-zone wells in C4 and C3f, only {zone_counts.loc[_FOREST, 'Achievable'].sum()} sit in the achievable band and "
        + f"{zone_counts.loc[_FOREST, 'Unreachable'].sum()} are in the unreachable band (m_P ≥ 2.5): {_unr_split}. The categorisation provides a direct per-well lookup for scrape-targeting decisions: achievable wells in the C1/C2/C3 transitional zone are the operationally feasible candidates; the small number of marginal wells in the open dune (n = "
        + f"{zone_counts.loc[_OPEN, 'Marginal'].sum()}) define the upper edge of the operational envelope under current climate.*",
        "",
        "## Suggested figure caption",
        "",
        "> *Figure N. Per-well achievability categorisation against the P_flood rainfall multiplier (m_P), the cumulative winter-rainfall depth required to lift each well's summer minimum back above the relevant Curreli (2013) threshold by end of recharge season, expressed as a multiple of climatological winter mean. Wells in the achievable category (m_P < 1.5, green) are reachable in normal-to-mildly-wet winters; marginal wells (1.5 ≤ m_P < 2.5, amber) only in wet winters; unreachable wells (m_P ≥ 2.5, red) are effectively unreachable under current climate. The cluster pattern (open-dune C1/C2/C3o dominated by achievable; forest C4/C3f dominated by marginal-to-unreachable) operationalises Conclusion 6's priority criterion for scrape-target identification. Source: `11c_pflood_achievability.png`; per-well lookup table in `11c_pflood_achievability_per_well.csv`.*",
        "",
        "## Caveats",
        "",
        "- The m_P values come from Script 11b's per-well calculation; they inherit Script 11b's assumptions about the cluster β coefficients and the climatological winter rainfall baseline. The categorical bin edges (1.5 and 2.5) are operational choices, not derived from any natural break in the data. Conclusion 6's text explicitly identifies the λ < 1.5 boundary; the marginal-vs-unreachable boundary at λ = 2.5 is selected to match the abstract's reference to a 1.5–2.5× rainfall multiplier band as the conservatively wet-winter zone.",
        "- The achievability category describes whether the cluster summer minimum can be raised above the Curreli threshold by winter recharge alone. It does not account for scrape-as-drainage geometry effects (Script 20's drain cone) or for forest-management interventions (Scripts 19 and 21); these are separate degrees of freedom in the scenario framework.",
        "- Wells flagged as scraped in the existing per-well CSV (CEH36, CEH18, CEH21) retain their categorical assignment based on present-day λ; the category reflects post-intervention behaviour where applicable.",
        "",
        "## Outputs",
        "",
        "- `11c_pflood_achievability.png` — operational map for §5.9 / Conclusion 6.",
        "- `11c_pflood_achievability_per_well.csv` — per-well lookup table with category column.",
        "- `11c_pflood_achievability_results.md` — this memo.",
    ]

    OUT_MEMO.write_text("\n".join(memo_lines))
    print(f"Wrote {OUT_MEMO.relative_to(REPO)}")
    print()
    print("─" * 72)
    done()
    print("─" * 72)


if __name__ == "__main__":
    main()
