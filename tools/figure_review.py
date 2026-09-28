#!/usr/bin/env python3
"""
tools/figure_review.py — before/after pairs of changed figures, for Martin's approval
====================================================================================

For each figure, BEFORE is the committed version (git HEAD) and AFTER is the working copy
the last run wrote. Figures whose bytes are unchanged are skipped and listed. Each pair is
written side by side, labelled, to notes/findings/figure_review/<stem>.jpg, with an
index.html that shows them in order. Read-only against git (no lock is taken).

Run:  python3 tools/figure_review.py [outputs/…png …]     (default: the 28b proofread batch)
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-28. New (proofread: "I need to see the old and new maps").

import io
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notes" / "findings" / "figure_review"
BATCH_28B = [
    "outputs/02_clustering/02_02_validation_plots.png",
    "outputs/07_spatial_coefficients/07_coeff_04_r2_quality.png",
    "outputs/10_clearfell_baci/10b_spatial_scrape_raw.png",
    "outputs/10_clearfell_baci/10b_spatial_scrape_corrected.png",
    "outputs/10_clearfell_baci/10e_03_coefficient_shifts.png",
    "outputs/20_spatial_figures/20_residual_ssm.png",
    "outputs/20_spatial_figures/20_msl5_change_2017_2023.png",
    "outputs/20_spatial_figures/20_observed_change_2012_2026.png",
    "outputs/20_spatial_figures/20_driver_change_20yr.png",
    "outputs/20_spatial_figures/20_driver_change_2005_2025.png",
    "outputs/26_van_willegen_msl/26_msl_5yr_map.png",
    "outputs/32_differential_movement/32_differential_movement_2011_2025.png",
    "outputs/32_differential_movement/32_differential_movement_2005_2025.png",
    "outputs/37_driver_validation/37_residual_map.png",
]
PANEL_W = 1400   # px per side


def git_bytes(rel: str) -> bytes | None:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    r = subprocess.run(["git", "--no-optional-locks", "show", f"HEAD:{rel}"], cwd=ROOT,
                       capture_output=True, env=env)
    return r.stdout if r.returncode == 0 else None


def head_sha() -> str:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    r = subprocess.run(["git", "--no-optional-locks", "log", "-1", "--format=%h %cd", "--date=short"],
                       cwd=ROOT, capture_output=True, text=True, env=env)
    return r.stdout.strip()


def panel(img: Image.Image, label: str) -> Image.Image:
    img = img.convert("RGB")
    img = img.resize((PANEL_W, int(img.height * PANEL_W / img.width)), Image.LANCZOS)
    bar = 44
    out = Image.new("RGB", (img.width, img.height + bar), "white")
    out.paste(img, (0, bar))
    d = ImageDraw.Draw(out)
    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    except OSError:
        f = ImageFont.load_default()
    d.text((12, 8), label, fill="black", font=f)
    return out


def main():
    rels = sys.argv[1:] or BATCH_28B
    OUT.mkdir(parents=True, exist_ok=True)
    sha = head_sha()
    made, same, missing = [], [], []
    for rel in rels:
        new_p = ROOT / rel
        old = git_bytes(rel)
        if not new_p.exists():
            missing.append(rel); continue
        new = new_p.read_bytes()
        if old is not None and old == new:
            same.append(rel); continue
        a = panel(Image.open(io.BytesIO(old)), f"BEFORE  (committed, {sha})") if old else None
        b = panel(Image.open(io.BytesIO(new)), "AFTER  (this run)")
        w = (a.width if a else 0) + b.width + (20 if a else 0)
        h = max(a.height if a else 0, b.height)
        pair = Image.new("RGB", (w, h), "white")
        if a:
            pair.paste(a, (0, 0))
        pair.paste(b, (w - b.width, 0))
        dst = OUT / f"{Path(rel).stem}.jpg"
        pair.save(dst, quality=85)
        made.append((rel, dst.name))
    html = ["<!doctype html><meta charset='utf-8'><title>Figure review</title>",
            "<style>body{font-family:sans-serif;margin:16px}img{max-width:100%;border:1px solid #ccc}"
            "h2{margin-top:36px}</style>",
            f"<h1>Figure review — before (git HEAD {sha}) and after (this run)</h1>"]
    for rel, name in made:
        html.append(f"<h2>{rel}</h2><img src='{name}'>")
    if same:
        html.append("<h2>Unchanged</h2><ul>" + "".join(f"<li>{r}</li>" for r in same) + "</ul>")
    if missing:
        html.append("<h2>Not found</h2><ul>" + "".join(f"<li>{r}</li>" for r in missing) + "</ul>")
    (OUT / "index.html").write_text("\n".join(html), encoding="utf-8")
    print(f"{len(made)} pair(s), {len(same)} unchanged, {len(missing)} missing -> {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
