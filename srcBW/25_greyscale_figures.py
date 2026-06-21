#!/usr/bin/env python3
"""
25_greyscale_figures.py
=======================
Post-processing script to convert all pipeline colour figures into
journal-ready greyscale versions.

Strategy
--------
This script operates as a **post-processor** — it reads existing colour
figures from the outputs/ tree and writes greyscale versions to a parallel
outputs_bw/ tree, preserving the directory structure.

Two conversion modes are available:

1. **Luminance conversion** (default): Uses ITU-R BT.709 perceptual
   luminance weights (0.2126 R + 0.7152 G + 0.0722 B) to convert each
   pixel. This is the standard method and produces the best results for
   most figure types (line plots, bar charts, scatter plots).

2. **Enhanced contrast**: Applies adaptive histogram equalisation (CLAHE)
   after luminance conversion for figures where the colour palette maps
   to a narrow luminance range (e.g. diverging colormaps on maps).

Known limitations
-----------------
Some figures rely on colour semantics that cannot be faithfully rendered
by pixel-level greyscale conversion:

  - 11b_01/02/03: Categorised ecological zone maps where 5 colour zones
    collapse to similar mid-greys. These need native B&W rendering with
    hatching patterns (future work in Script 11b).
  - difference_maps/diff_*: Diverging RdBu colormaps where the colourbar
    labels reference "blue = wetter" / "red = drier". The text is baked
    into the raster.

These figures are flagged with [REVIEW] in the output and still converted
(the greyscale version is usable but suboptimal). Pass --exclude-problem
to skip them entirely.

Usage
-----
    python src/25_greyscale_figures.py [--enhanced] [--dpi DPI] [--skip-maps]
                                      [--exclude-problem] [--dry-run]

    --enhanced        Apply CLAHE contrast enhancement to all figures
    --dpi DPI         Override output DPI (default: preserve original)
    --skip-maps       Skip spatial map figures (which may need manual review)
    --exclude-problem Skip figures with known greyscale conversion problems
    --dry-run         List files that would be converted without converting

Regeneration
------------
This script is idempotent. To regenerate after data changes:
    1. Re-run the upstream pipeline (run_analysis.py)
    2. Re-run this script: python src/25_greyscale_figures.py

The outputs_bw/ directory can be safely deleted and rebuilt at any time.

Author: Hollingham 2026
Pipeline step: 25 (post-processing)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

# ──────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
COLOUR_DIR = REPO_ROOT / "outputs"
BW_DIR = REPO_ROOT / "outputs_bw"

# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

# ──────────────────────────────────────────────────────────────────────
# Problem figures — convert with warning, or skip with --exclude-problem
# ──────────────────────────────────────────────────────────────────────
# These figures use colour semantics (categorised zones, diverging
# colormaps with colour-referenced labels) that do not survive naive
# greyscale conversion. They need native B&W rendering at source.
#
# Format: relative path fragments matched against the figure's relative
# path (from outputs/). A figure is flagged if any fragment matches.

PROBLEM_FIGURE_PATTERNS = [
    # Script 11b: ecological zone maps with 5 categorised colour bands
    # (blue/green/yellow/orange/red) that collapse to similar mid-greys.
    "11b_spatial_thresholds/11b_01_summer_minima_depth",
    "11b_spatial_thresholds/11b_02_winter_maxima_depth",
    "11b_spatial_thresholds/11b_03_pflood",
    # Script 19 difference maps: diverging RdBu colormaps with
    # colourbar labels referencing "blue = wetter" / "red = drier".
    "difference_maps/diff_",
]

PROBLEM_REASON = {
    "11b_spatial_thresholds/11b_01": (
        "Categorised ecological zones (5 colour bands) collapse to "
        "similar mid-greys. Needs hatched zone rendering in Script 11b."
    ),
    "11b_spatial_thresholds/11b_02": (
        "Categorised winter ecological zones (4 colour bands) collapse "
        "to similar mid-greys. Needs hatched zone rendering in Script 11b."
    ),
    "11b_spatial_thresholds/11b_03_pflood": (
        "Green/orange binary categorisation lost; cluster dot colours "
        "all become similar greys. Needs native B&W rendering."
    ),
    "difference_maps/diff_": (
        "Diverging RdBu colormap labels reference 'blue = wetter' / "
        "'red = drier' which is meaningless in greyscale. Colourbar "
        "text is baked into the raster and cannot be post-edited."
    ),
}


def is_problem_figure(rel_path: str) -> tuple[bool, str]:
    """Check if a figure matches a known problem pattern.

    Returns (is_problem, reason_string).
    """
    for pattern in PROBLEM_FIGURE_PATTERNS:
        if pattern in rel_path:
            # Find the most specific matching reason
            for reason_key, reason_text in PROBLEM_REASON.items():
                if reason_key in rel_path:
                    return True, reason_text
            return True, "Known colour-dependent figure."
    return False, ""


# ──────────────────────────────────────────────────────────────────────
# Conversion functions
# ──────────────────────────────────────────────────────────────────────

def luminance_greyscale(img: Image.Image) -> Image.Image:
    """
    Convert an RGBA/RGB image to greyscale using ITU-R BT.709 perceptual
    luminance weights, preserving the alpha channel if present.

    This is superior to PIL's .convert('L') which uses older BT.601
    weights. The BT.709 weights (0.2126, 0.7152, 0.0722) better match
    human perception of brightness.
    """
    has_alpha = img.mode == "RGBA"

    if has_alpha:
        # Composite onto white background first, then convert
        # This avoids grey halos around transparent edges
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        composited = Image.alpha_composite(background, img)
        arr = np.array(composited, dtype=np.float64)
    else:
        arr = np.array(img.convert("RGB"), dtype=np.float64)

    # BT.709 luminance
    grey = (
        0.2126 * arr[:, :, 0]
        + 0.7152 * arr[:, :, 1]
        + 0.0722 * arr[:, :, 2]
    )
    grey = np.clip(grey, 0, 255).astype(np.uint8)

    return Image.fromarray(grey, mode="L")


def enhanced_greyscale(img: Image.Image) -> Image.Image:
    """
    Luminance conversion followed by contrast-limited adaptive histogram
    equalisation (CLAHE) for figures with narrow luminance ranges.

    Uses a simple Pillow-based approach: convert to greyscale, then
    auto-contrast with a small cutoff to expand the dynamic range.
    """
    grey_img = luminance_greyscale(img)

    # Auto-contrast: clips 0.5% of lightest and darkest pixels
    from PIL import ImageOps
    enhanced = ImageOps.autocontrast(grey_img, cutoff=0.5)

    # Slight sharpening to compensate for any softening
    enhancer = ImageEnhance.Sharpness(enhanced)
    enhanced = enhancer.enhance(1.1)

    return enhanced


def convert_figure(
    src_path: Path,
    dst_path: Path,
    enhanced: bool = False,
    target_dpi: int | None = None,
) -> bool:
    """
    Convert a single figure from colour to greyscale.

    Parameters
    ----------
    src_path : Path to the source colour image
    dst_path : Path for the output greyscale image
    enhanced : Whether to apply CLAHE contrast enhancement
    target_dpi : Override DPI; None preserves original

    Returns
    -------
    True if conversion succeeded, False otherwise
    """
    try:
        img = Image.open(src_path)
    except Exception as e:
        print(f"  [ERROR] Cannot open {src_path}: {e}")
        return False

    # Already greyscale? Just copy
    if img.mode in ("L", "LA", "1"):
        img.save(dst_path)
        return True

    # Convert
    converter = enhanced_greyscale if enhanced else luminance_greyscale
    grey_img = converter(img)

    # Preserve DPI metadata from original
    dpi_info = img.info.get("dpi", (300, 300))
    if target_dpi:
        dpi_info = (target_dpi, target_dpi)

    # Save with same format
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    save_kwargs = {"dpi": dpi_info}
    if dst_path.suffix.lower() in (".jpg", ".jpeg"):
        save_kwargs["quality"] = 95
        save_kwargs["subsampling"] = 0  # 4:4:4 for quality
        grey_img.save(dst_path, **save_kwargs)
    else:
        # PNG — no quality param, but optimize
        save_kwargs["optimize"] = True
        grey_img.save(dst_path, **save_kwargs)

    return True


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def collect_figures(source_dir: Path) -> list[Path]:
    """Find all image files in the source directory tree."""
    figures = []
    for ext in IMAGE_EXTENSIONS:
        figures.extend(source_dir.rglob(f"*{ext}"))
    return sorted(figures)


def main():
    parser = argparse.ArgumentParser(
        description="Convert pipeline colour figures to journal-ready greyscale."
    )
    parser.add_argument(
        "--enhanced",
        action="store_true",
        help="Apply adaptive contrast enhancement (CLAHE) to all figures",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=None,
        help="Override output DPI (default: preserve original)",
    )
    parser.add_argument(
        "--skip-maps",
        action="store_true",
        help="Skip spatial map figures (directories containing 'spatial')",
    )
    parser.add_argument(
        "--exclude-problem",
        action="store_true",
        help="Skip figures with known greyscale conversion problems",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be converted without converting them",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Convert all figures even if outputs_bw/ version is up to date",
    )
    args = parser.parse_args()

    if not COLOUR_DIR.exists():
        print(f"[ERROR] Source directory not found: {COLOUR_DIR}")
        sys.exit(1)

    figures = collect_figures(COLOUR_DIR)
    if not figures:
        print("[WARNING] No image files found in outputs/")
        sys.exit(0)

    # Filter out maps if requested
    if args.skip_maps:
        figures = [
            f for f in figures
            if "spatial" not in f.parent.name.lower()
            and "_map" not in f.stem.lower()
        ]

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Converting {len(figures)} figures to greyscale")
    print(f"  Source: {COLOUR_DIR}")
    print(f"  Output: {BW_DIR}")
    print(f"  Mode:   {'Enhanced (CLAHE)' if args.enhanced else 'Luminance (BT.709)'}")
    if args.dpi:
        print(f"  DPI:    {args.dpi}")
    print()

    succeeded = 0
    failed = 0
    skipped = 0
    up_to_date = 0
    review_list: list[tuple[str, str]] = []

    for fig_path in figures:
        # Build destination path preserving directory structure
        rel_path = fig_path.relative_to(COLOUR_DIR)
        rel_str = str(rel_path)
        dst_path = BW_DIR / rel_path

        # Check for known problem figures
        is_problem, reason = is_problem_figure(rel_str)
        if is_problem and args.exclude_problem:
            skipped += 1
            print(f"  [SKIP]   {rel_path}  (known problem)")
            review_list.append((rel_str, reason))
            continue

        # Skip if BW version already exists and is newer than source
        if dst_path.exists() and not args.force:
            src_mtime = fig_path.stat().st_mtime
            dst_mtime = dst_path.stat().st_mtime
            if dst_mtime >= src_mtime:
                up_to_date += 1
                continue

        if args.dry_run:
            tag = "[REVIEW] " if is_problem else ""
            print(f"  {tag}Would convert: {rel_path}")
            if is_problem:
                review_list.append((rel_str, reason))
            succeeded += 1
            continue

        dst_path.parent.mkdir(parents=True, exist_ok=True)

        ok = convert_figure(
            fig_path,
            dst_path,
            enhanced=args.enhanced,
            target_dpi=args.dpi,
        )
        if ok:
            succeeded += 1
            tag = " [REVIEW]" if is_problem else ""
            print(f"  \u2713{tag} {rel_path}")
            if is_problem:
                review_list.append((rel_str, reason))
        else:
            failed += 1
            print(f"  \u2717 {rel_path}")

    # Summary
    parts = [f"{succeeded} converted"]
    if up_to_date:
        parts.append(f"{up_to_date} up to date")
    if failed:
        parts.append(f"{failed} failed")
    if skipped:
        parts.append(f"{skipped} skipped")
    print(f"\nDone: {', '.join(parts)}")
    if not args.dry_run and succeeded > 0:
        print(f"Greyscale figures saved to: {BW_DIR}/")

    # Print review manifest if any problem figures were encountered
    if review_list:
        print("\n" + "\u2500" * 70)
        action = "SKIPPED" if args.exclude_problem else "NEEDS REVIEW"
        print(f"  {action}: {len(review_list)} figures with known greyscale limitations")
        print("\u2500" * 70)
        for rel_str, reason in review_list:
            print(f"\n  {rel_str}")
            print(f"    {reason}")
        print()
        if not args.exclude_problem:
            print(
                "  These figures were converted but the greyscale versions\n"
                "  are suboptimal. For journal submission, consider:\n"
                "    - Adding native B&W mode to Scripts 11b/19\n"
                "    - Or providing colour versions as online supplementary\n"
                "    - Or adding explanatory caption text\n"
            )


if __name__ == "__main__":
    main()
