"""
utils/render_utils.py
======================
Centralised figure rendering and saving for the Newborough pipeline.

Purpose
-------
Every report figure is placed in an A4 document with a fixed text-block width.
Historically each script chose its own ``savefig`` dpi (150/160/180/200/300),
so figures drawn at 14-16 inches wide were saved at 3000-4000 px and placed at
~160 mm — an effective 500+ dpi that bloats the PDF without adding any print
resolution. ``render_figure`` computes a save dpi so that *every* figure lands
at the same on-paper resolution (``FIG_TARGET_PRINT_DPI``) regardless of the
figsize the script happened to use, capping the pixel dimensions at what A4 at
that dpi can show.

Design
------
The save dpi is::

    dpi = min(FIG_TARGET_PRINT_DPI,
              FIG_MAX_WIDTH_PX  / fig_width_in,
              FIG_MAX_HEIGHT_PX / fig_height_in)   # height only if full_page

so a 16-inch-wide panel saves at ~118 dpi and an 8-inch one at ~236 dpi; both
come out <= FIG_MAX_WIDTH_PX and look identical once placed at 160 mm. The pixel
caps derive from three config constants (FIG_TARGET_WIDTH_MM / _HEIGHT_MM /
_PRINT_DPI), so changing the target is a one-line config edit plus a pipeline
rerun — no per-script edits.

This module does NOT change figsize, layout, or fonts. A figure authored at 14
inches wide still has small-looking text when placed at 160 mm; that is a
separate per-figure re-authoring task. To surface those candidates, this module
emits a console warning (via console_utils.warn) whenever the effective placed
font size of the smallest tick label would fall below LEGIBILITY_MIN_PT. The
warning is a *detector* for that later font pass, not a fix.

MPL_DEFAULTS
------------
The house-style rcParams dict formerly in scraping_common.py now lives here
(a single home for figure styling). scraping_common re-exports it for backwards
compatibility. New code should import from render_utils.

Public API
----------
render_figure(fig, out_path, *, full_page=False, quiet=False, **savefig_kwargs)
    -> int   (the dpi actually used)
apply_house_style()   -> None    (rcParams.update(MPL_DEFAULTS))
MPL_DEFAULTS          -> dict

Version
-------
1.0.0  2026-07-19  Initial: A4-capped render_figure, MPL_DEFAULTS relocation,
                   apply_house_style, legibility detector.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from utils import config
from utils import console_utils

__version__ = "1.0.0"

# ── House-style rcParams (relocated from scraping_common.py) ──────────────────
MPL_DEFAULTS = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
}

# ── Derived pixel caps (from config target width/height/dpi) ─────────────────
_MM_PER_INCH = 25.4
FIG_MAX_WIDTH_PX = int(
    round(config.FIG_TARGET_WIDTH_MM / _MM_PER_INCH * config.FIG_TARGET_PRINT_DPI)
)
FIG_MAX_HEIGHT_PX = int(
    round(config.FIG_TARGET_HEIGHT_MM / _MM_PER_INCH * config.FIG_TARGET_PRINT_DPI)
)

# ── Legibility detector threshold ─────────────────────────────────────────────
# Smallest placed font (pt) below which a figure is flagged for the later
# font-re-authoring pass. Derived from the placed-width shrink factor:
# a font of F pt drawn on a W-inch figure placed at FIG_TARGET_WIDTH_MM prints
# at F * (FIG_TARGET_WIDTH_MM / (W * 25.4)) pt.
LEGIBILITY_MIN_PT = 5.5


def apply_house_style() -> None:
    """Apply the house-style rcParams. Call once near the top of a script."""
    plt.rcParams.update(MPL_DEFAULTS)


def _smallest_font_pt(fig) -> float:
    """Smallest tick/label font (pt) currently set on the figure's axes.

    Used only for the legibility heuristic; falls back to the rcParam tick size.
    """
    sizes = []
    for ax in fig.get_axes():
        for lab in (*ax.get_xticklabels(), *ax.get_yticklabels()):
            sz = lab.get_fontsize()
            if sz:
                sizes.append(sz)
    if not sizes:
        sizes.append(plt.rcParams.get("xtick.labelsize", 10))
    # rcParams may store a string alias (e.g. "medium"); ignore non-numeric.
    numeric = [s for s in sizes if isinstance(s, (int, float))]
    return float(min(numeric)) if numeric else 10.0


def _placed_width_mm(fig, full_page: bool) -> float:
    """The width (mm) the figure will occupy once placed in the document."""
    # Width-driven placement is the norm; a full_page figure that is
    # height-limited is placed narrower, but for the legibility check the
    # width-at-target is the worst case, so use FIG_TARGET_WIDTH_MM.
    return config.FIG_TARGET_WIDTH_MM


def render_figure(
    fig,
    out_path,
    *,
    full_page: bool = False,
    quiet: bool = False,
    **savefig_kwargs,
) -> int:
    """Save ``fig`` to ``out_path`` at an A4-capped dpi.

    Parameters
    ----------
    fig
        A matplotlib Figure. For call sites that used ``plt.savefig``, pass
        ``plt.gcf()``.
    out_path : str | Path
        Destination. Extension drives the format (``.png`` default; ``.jpg`` /
        ``.jpeg`` honoured). PNGs are saved with ``optimize=True`` unless the
        caller overrides ``pil_kwargs``.
    full_page : bool, default False
        If True, also cap the height at FIG_MAX_HEIGHT_PX (for tall/portrait
        full-page figures). If False, only the width cap binds.
    quiet : bool, default False
        Suppress the console 'Saved' line (for buffer-less internal renders /
        tests).
    **savefig_kwargs
        Passed through to ``fig.savefig`` (e.g. ``format``, ``pil_kwargs``,
        ``facecolor``). ``dpi`` and ``bbox_inches`` are managed here and will be
        overridden if supplied.

    Returns
    -------
    int
        The dpi actually used.
    """
    out_path = Path(out_path)
    w_in, h_in = fig.get_size_inches()

    # Effective save dpi: never exceed the print ceiling, and cap so the saved
    # raster does not exceed the A4 pixel budget in the binding dimension(s).
    dpi = float(config.FIG_TARGET_PRINT_DPI)
    if w_in > 0:
        dpi = min(dpi, FIG_MAX_WIDTH_PX / w_in)
    if full_page and h_in > 0:
        dpi = min(dpi, FIG_MAX_HEIGHT_PX / h_in)
    dpi = int(max(1, round(dpi)))

    # bbox_inches="tight" trims surrounding whitespace before the pixel count is
    # realised, so the caps above are a safe ceiling rather than an exact size.
    savefig_kwargs.pop("dpi", None)
    savefig_kwargs.pop("bbox_inches", None)
    # Drop explicit None values (call sites pass format=None / pil_kwargs=None for
    # their PNG branch); this lets the PNG-optimise default below still apply.
    if savefig_kwargs.get("format", "sentinel") is None:
        savefig_kwargs.pop("format")
    if savefig_kwargs.get("pil_kwargs", "sentinel") is None:
        savefig_kwargs.pop("pil_kwargs")

    # Default PNG optimisation (only when the caller has not set pil_kwargs and
    # the target is a PNG).
    fmt = savefig_kwargs.get("format")
    is_png = (fmt == "png") or (fmt is None and out_path.suffix.lower() == ".png")
    if is_png and "pil_kwargs" not in savefig_kwargs:
        savefig_kwargs["pil_kwargs"] = {"optimize": True}

    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", **savefig_kwargs)

    # Legibility detector — flag figures whose smallest label would print below
    # the threshold once placed. This is the work-order for the later font pass.
    smallest_pt = _smallest_font_pt(fig)
    placed_mm = _placed_width_mm(fig, full_page)
    shrink = placed_mm / (w_in * _MM_PER_INCH) if w_in > 0 else 1.0
    placed_pt = smallest_pt * shrink
    if placed_pt < LEGIBILITY_MIN_PT and not quiet:
        console_utils.warn(
            f"Legibility: {out_path.name} smallest label ~{placed_pt:.1f} pt "
            f"when placed at {placed_mm:.0f} mm (figsize {w_in:.1f}×{h_in:.1f} in). "
            f"Flag for font re-authoring pass."
        )

    if not quiet:
        console_utils.saved(out_path.name, extra=f"{dpi} dpi")

    return dpi
