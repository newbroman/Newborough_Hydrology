#!/usr/bin/env python3
"""
tools/depth_map_preview.py — preview of a depth map drawn as the kriged level minus the DEM
===========================================================================================

Side-by-side preview for Martin's decision (spec NRG_spec_depth_maps_level_minus_dem):
left, the summer-minimum depth map as Script 11b draws it now (piecewise-linear depth
surface, 1 m ridge mask); right, the same wells drawn by water_table.depth_surface()
(level in m OD kriged with Script 01b's recorded system, anchors over Aug-Sep, minus the
DEM averaged onto the grid). Same zone bands. Reads committed outputs only; writes the PNG
and a per-well check CSV to notes/findings/.

Run:  python3 tools/depth_map_preview.py [--grid 10]
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-28. New (spec NRG_spec_depth_maps_level_minus_dem).

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from utils import config as C  # noqa: E402
from utils import paths as P  # noqa: E402
from utils.map_utils import load_dem_hillshade, add_idw_surface, add_en_axes, add_kml_features  # noqa: E402
from utils.water_table import depth_surface  # noqa: E402

ZONE_COLOURS = ["#1a7abf", "#a8d8a8", "#ffffb2", "#fd8d3c", "#bd0026"]   # as Script 11b
ZONE_BOUNDS = [0.0, C.SD15b, C.SD15b_REC, C.SD16, C.SD16_REC, 3.5]
OUT = ROOT / "notes" / "findings"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", type=float, default=10.0)
    a = ap.parse_args()
    df = pd.read_csv(P.OUT_DIR / "11b_spatial_thresholds" / "11b_03_pflood_per_well.csv") \
        if hasattr(P, "OUT_DIR") else pd.read_csv(ROOT / "outputs/11b_spatial_thresholds/11b_03_pflood_per_well.csv")
    df = df.dropna(subset=["E", "N", "dem", "depth_bg"]).copy()
    df["level"] = df["dem"] - df["depth_bg"]
    lev = pd.read_csv(P.INT_WELLS_ALL, index_col=0, parse_dates=True)
    months = lev.index[lev.index.month.isin([8, 9])]
    r = depth_surface(df[["well", "E", "N", "level"]], months, a.grid)

    # at the wells: the map's depth in the well's cell against the well's own depth
    ix = np.clip(np.searchsorted(r["gx"][0], df["E"]) - 1, 0, r["gx"].shape[1] - 1)
    iy = np.clip(np.searchsorted(r["gy"][:, 0], df["N"]) - 1, 0, r["gy"].shape[0] - 1)
    chk = pd.DataFrame({"well": df["well"], "depth_bg_well": df["depth_bg"],
                        "depth_map_cell": r["depth"][iy, ix],
                        "well_ground": df["dem"], "dem_cell_at_well": r["ground_at_wells"]})
    chk["map_minus_well_m"] = chk["depth_map_cell"] - chk["depth_bg_well"]
    chk.to_csv(OUT / "depth_preview_summer_min_wells.csv", index=False)
    d = chk["map_minus_well_m"].dropna()
    print(f"anchors {r['n_anchors']}; at the wells the map minus the well depth: median {d.median():+.3f} m, "
          f"IQR {d.quantile(.25):+.3f} to {d.quantile(.75):+.3f} m, |>0.25 m| at {int((d.abs() > 0.25).sum())} of {len(d)}")

    cmap = LinearSegmentedColormap.from_list("slack", ZONE_COLOURS, N=256)
    norm = BoundaryNorm(ZONE_BOUNDS, ncolors=256)
    fig, axs = plt.subplots(1, 3, figsize=(31, 10.5), facecolor="white")
    for k, ax in enumerate(axs):
        _, ok, de, dn, dd = load_dem_hillshade(ax, P.DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
        if k == 0:
            mesh, *_ = add_idw_surface(ax, df, value_col="depth_bg", dem_col="dem", ridge_mask_threshold=1.0,
                                       dem_e_arr=de, dem_n_arr=dn, dem_data=dd, cmap=cmap, norm=norm,
                                       alpha=0.68, zorder=2)
            ax.set_title("Now: piecewise-linear depth surface, 1 m ridge mask", fontsize=12, fontweight="bold")
        else:
            off = 0.0 if k == 1 else float(np.nanmedian(chk["dem_cell_at_well"] - chk["well_ground"]))
            dep = r["depth"] - off
            depth = np.clip(dep, ZONE_BOUNDS[0] - 1, ZONE_BOUNDS[-1])
            mesh = ax.pcolormesh(r["gx"], r["gy"], np.ma.masked_invalid(depth), cmap=cmap, norm=norm,
                                 alpha=0.68, zorder=2, shading="auto")
            for lv, col, ls in [(C.SD15b, "#005fa3", "--"), (C.SD16, "#a30000", "--")]:
                ax.contour(r["gx"], r["gy"], dep, levels=[lv], colors=[col], linewidths=0.9,
                           linestyles=ls, alpha=0.8, zorder=3)
            ax.set_title((f"Option 1: kriged level (D-205 system, Aug–Sep anchors) minus DEM, {a.grid:g} m grid"
                          if k == 1 else
                          f"Option 1 with the DEM lowered by {off:.2f} m\n(median DEM-above-well-ground at the wells)"),
                         fontsize=12, fontweight="bold")
        add_kml_features(ax, P.DATA_DIR, include_streams=False, include_scrapes=False)
        ax.scatter(df["E"], df["N"], c=df["depth_bg"], cmap=cmap, norm=norm, s=40, edgecolor="k",
                   linewidth=0.6, zorder=6)
        add_en_axes(ax)
    cb = fig.colorbar(mesh, ax=axs, fraction=0.015, pad=0.01, boundaries=ZONE_BOUNDS,
                      ticks=[0, C.SD15b, C.SD15b_REC, C.SD16, C.SD16_REC, 3.5])
    cb.set_label("Mean summer minimum depth below ground (m); ≤ 0 = at or above ground", fontsize=10)
    fig.suptitle(f"Summer-minimum depth: current map vs level-minus-DEM preview (n = {len(df)} wells; "
                 f"markers = the wells' own depth)", fontsize=13)
    out = OUT / "depth_preview_summer_min.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
