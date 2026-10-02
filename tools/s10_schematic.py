#!/usr/bin/env python3
"""
s10_schematic — draw Supplementary Material Figure S10.1, the network-change construction
schematic, with its figure numbers READ from tools/figure_map.csv.

WHY. The schematic was a one-off PNG (2026-08-14) with the report's figure numbers typed into
the picture. The report renumbered and the picture did not: on 2026-10-02 it said Figures 63-66
while its own caption and figure_map.csv said 73-76, and two labels ran past their boxes. A
picture cannot be linted for a stale number, so the number is not typed here either: each box
names the OUTPUT FILE it stands for, and figure_map.csv says which report figure carries it.
Renumber the report, run this, swap the image (odt_edit.replace_image).

Fails loudly when an output is not in figure_map.csv, or appears more than once, rather than
drawing a box with no number; and when any label overruns its box.

Writes notes/figures/S10_network_change_schematic.png (3000 x 1080 px, the aspect of the frame
it is placed in, 15.921 x 5.731 cm).

Usage:
    python3 tools/s10_schematic.py            # draw it
    python3 tools/s10_schematic.py --check    # exit 1 if the committed PNG's numbers are stale
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) — 2026-10-02. --check also requires the drawn PNG to be the
#   image embedded in the newest Supplementary Material, so a redraw that never reached the
#   document is not green. ship_regen_lint exempts it: the fix is a document edit.
# 1.0.0  # Hollingham (2026) — 2026-10-02. First version: replaces the hand-drawn
#   S10_network_change_schematic.png, whose typed figure numbers had gone stale (63-66 for 73-76).

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from utils import console_utils as cu  # noqa: E402
from utils.render_utils import apply_house_style  # noqa: E402

FIGURE_MAP = REPO / "tools" / "figure_map.csv"
OUT = REPO / "notes" / "figures" / "S10_network_change_schematic.png"
STAMP = OUT.with_suffix(".json")          # the numbers the PNG was drawn with, for --check
W_IN, H_IN, DPI = 10.0, 3.6, 300           # 3000 x 1080 px

# frame -> [(output file below outputs/, title, script, what it measures)]
PRODUCTS = {
    ("Remove common mode", "subtract the network-mean spring"): [
        ("32_differential_movement/32_differential_movement_2011_2025.png",
         "Differential movement", 32,
         "secular trend of the anomaly: who moves against the site (mm yr⁻¹)"),
        ("33_envelope_amplification/33_amplification_field.png",
         "Amplification field", 33,
         "dry–wet swing ÷ network-mean swing (dimensionless ×)"),
    ],
    ("Keep the absolute frame", "each well on its own terms"): [
        ("36_absolute_climate_trend/36_absolute_climate_trend_2005_2025.png",
         "Absolute climate-removed trend", 36,
         "per-well secular rate, shared climate signal removed (mm yr⁻¹)"),
        ("33_envelope_amplification/33_dry_spring_depth.png",
         "Dry-year spring depth", 33,
         "depth below ground in the dry extreme springs (m)"),
    ],
}


def figure_numbers() -> dict[str, str]:
    """output path -> report figure number, from figure_map.csv; refuses a missing or
    ambiguous output rather than drawing an unnumbered box."""
    rows = list(csv.DictReader(FIGURE_MAP.open(encoding="utf-8")))
    out = {}
    for frame in PRODUCTS.values():
        for src, *_ in frame:
            hits = [r["number"] for r in rows if r["source"].strip() == f"outputs/{src}"]
            if len(hits) != 1:
                raise SystemExit(f"  ABORT: outputs/{src} is in figure_map.csv {len(hits)}x, "
                                 f"expected exactly 1")
            out[src] = hits[0]
    return out


def newest_supplementary() -> Path | None:
    sys.path.insert(0, str(REPO / "tools"))
    from refresh_mirrors import _version_key
    found = sorted((REPO / "docs" / "report").glob("Supplementary_Material_v*.odt"), key=_version_key)
    return found[-1] if found else None


def embedded(odt: Path) -> bool:
    """Is the drawn PNG, byte for byte, one of the document's pictures?"""
    import hashlib
    import zipfile
    want = hashlib.md5(OUT.read_bytes()).hexdigest()
    with zipfile.ZipFile(odt) as z:
        return any(hashlib.md5(z.read(n)).hexdigest() == want
                   for n in z.namelist() if n.startswith("Pictures/"))


def _fits(fig, text, box) -> bool:
    r = fig.canvas.get_renderer()
    t, b = text.get_window_extent(r), box.get_window_extent(r)
    return t.x0 >= b.x0 and t.x1 <= b.x1 and t.y0 >= b.y0 and t.y1 <= b.y1


def draw(nums: dict[str, str]) -> None:
    apply_house_style()
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100.8); ax.set_ylim(-0.6, 37.2); ax.axis("off")
    grey, blue, ink, soft = "#f2f3f5", "#1f6fb2", "#1a1a1a", "#4d4d4d"
    checks = []

    def box(x, y, w, h, title, sub, edge, face, bold, fs_t, fs_s):
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8",
                           fc=face, ec=edge, lw=1.4 if edge == blue else 1.0)
        ax.add_patch(p)
        cx = x + w / 2 if edge != blue else x + 1.6
        ha = "center" if edge != blue else "left"
        t1 = ax.text(cx, y + h * 0.64, title, ha=ha, va="center", fontsize=fs_t,
                     fontweight="bold" if bold else "normal", color=ink)
        t2 = ax.text(cx, y + h * 0.30, sub, ha=ha, va="center", fontsize=fs_s, color=soft)
        checks.extend([(t1, p), (t2, p)])
        return p

    def arrow(x0, y0, x1, y1, rad):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12,
                                     connectionstyle=f"arc3,rad={rad}", lw=1.1, color="#555555"))

    # source
    box(1.5, 14.0, 20.0, 8.0, "Per-well spring series", "mean of Mar–May readings, per year",
        "#8c8c8c", grey, True, 10, 7.5)
    ys = {0: 25.0, 1: 3.0}                       # frame rows
    prod_y = {0: [30.0, 21.5], 1: [8.5, 0.0]}
    for i, ((ftitle, fsub), prods) in enumerate(PRODUCTS.items()):
        fy = ys[i] + 0.5
        box(29.0, fy, 21.0, 6.5, ftitle, fsub, "#8c8c8c", grey, False, 9.5, 7.5)
        arrow(21.5, 18.0 + (2.0 if i == 0 else -2.0), 29.0, fy + 3.25, -0.25 if i == 0 else 0.25)
        for j, (src, title, script, sub) in enumerate(prods):
            py = prod_y[i][j] + 0.6
            box(55.0, py, 44.5, 5.6, f"Figure {nums[src]} · {title} (Script {script})", sub,
                blue, "white", True, 9, 7.5)
            arrow(50.0, fy + 3.25 + (1.2 if j == 0 else -1.2), 55.0, py + 2.8,
                  -0.2 if j == 0 else 0.2)

    fig.canvas.draw()
    bad = [t.get_text() for t, p in checks if not _fits(fig, t, p)]
    if bad:
        raise SystemExit("  ABORT: label overruns its box: " + "; ".join(bad))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=DPI, facecolor="white")
    plt.close(fig)
    STAMP.write_text(json.dumps({"tool": __version__, "figures": nums}, indent=1) + "\n",
                     encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when figure_map.csv no longer gives the numbers the PNG shows")
    a = ap.parse_args(argv[1:])
    nums = figure_numbers()
    if a.check:
        drawn = json.loads(STAMP.read_text(encoding="utf-8"))["figures"] if STAMP.is_file() else {}
        if drawn != nums:
            print(f"  s10_schematic: STALE — drawn with {sorted(drawn.values())}, "
                  f"figure_map.csv gives {sorted(nums.values())}. Run tools/s10_schematic.py "
                  f"and swap the image (odt_edit.replace_image).")
            return 1
        odt = newest_supplementary()
        if odt is None:
            print("  s10_schematic: note — no Supplementary Material ODT here (no Drive copy); "
                  "the embedded image is not checked")
        elif not embedded(odt):
            print(f"  s10_schematic: STALE — {OUT.name} is not the image embedded in {odt.name}. "
                  f"Swap it: odt_edit.replace_image(<{odt.name}>, <next version>, <member>, {OUT.name}).")
            return 1
        print(f"  s10_schematic: OK — Figures {', '.join(sorted(nums.values(), key=int))}"
              + (f"; embedded in {odt.name}" if odt else ""))
        return 0
    cu.banner("s10_schematic", "Supplementary Material Figure S10.1", __version__)
    draw(nums)
    cu.saved(OUT, f"Figures {', '.join(sorted(nums.values(), key=int))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
