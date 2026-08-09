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

Font autoscaling — OPT-IN per call site (v1.2.0)
------------------------------------------------
v1.1.0 applied text enlargement to every undersized figure by default. In
practice the placed-width heuristic over-fired: figures whose labels read
acceptably on paper (e.g. 02_03_cluster_hydrographs_wb) were enlarged past
taste. v1.2.0 restores the v1.0.0 default — figures are saved exactly as
authored — and keeps the scaling machinery as a per-call-site opt-in for the
hand pass over the genuinely illegible figures:

    render_figure(fig, path, autoscale_fonts=True)                 # target 6.5 pt
    render_figure(fig, path, autoscale_fonts=True, min_placed_pt=6.0)

When opted in, every text element in the figure (tick labels, axis labels,
titles, legends, annotations, suptitles, colorbar labels, offset texts) is
enlarged by a single common factor so the smallest tick label prints at
``min_placed_pt`` (default ``config.FIG_MIN_PLACED_PT``) at the placed width,
capped at ``config.FIG_MAX_FONT_SCALE``. Relative size hierarchy within the
figure is preserved; figsize and layout are untouched. Scaling is applied at
most once per Figure (attribute guard), so double saves do not compound.

The legibility detector is unchanged from v1.0.0 and remains *advisory*: it
warns when the smallest tick label would print below ``LEGIBILITY_MIN_PT``
(5.5 pt) at the placed width. It is a candidate list, not a verdict — placed
size understates real-world legibility for some figures.

MPL_DEFAULTS
------------
The house-style rcParams dict formerly in scraping_common.py now lives here
(a single home for figure styling). scraping_common re-exports it for backwards
compatibility. New code should import from render_utils.

Public API
----------
render_figure(fig, out_path, *, full_page=False, quiet=False,
              autoscale_fonts=False, min_placed_pt=None,
              **savefig_kwargs) -> int   (the dpi actually used)
bump_fig_fonts(fig, delta_pt)  -> None  (all text elements +delta_pt)
bump_label_and_legend_fonts(fig, delta_pt) -> None  (axis labels + legends only)
apply_house_style()   -> None    (rcParams.update(MPL_DEFAULTS))
MPL_DEFAULTS          -> dict

"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.text as mtext

from utils import config
from utils import console_utils

__version__ = "1.4.0"

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

# ── Legibility detector threshold (ADVISORY) ─────────────────────────────────
# Smallest placed font (pt) below which a figure is flagged as a candidate for
# per-figure font attention. A font of F pt drawn on a W-inch figure placed at
# FIG_TARGET_WIDTH_MM prints at F * (FIG_TARGET_WIDTH_MM / (W * 25.4)) pt.
# Advisory only — placed size understates real legibility for some figures.
LEGIBILITY_MIN_PT = 5.5

# Attribute set on a Figure once fonts have been autoscaled (idempotence guard).
_FONT_SCALE_ATTR = "_render_utils_font_scale"


def apply_house_style() -> None:
    """Apply the house-style rcParams. Call once near the top of a script."""
    plt.rcParams.update(MPL_DEFAULTS)


def _smallest_font_pt(fig) -> float:
    """Smallest tick/label font (pt) currently set on the figure's axes.

    Basis for the legibility heuristic and opt-in scaling; falls back to the
    rcParam tick size when the figure has no tick labels (e.g. axes-off maps).
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


def _scale_fig_fonts(fig, factor: float) -> None:
    """Enlarge every text element on ``fig`` by ``factor`` (post-layout).

    Tick labels are lazily regenerated by matplotlib on draw, so the scaled
    size must also be pushed through ``tick_params`` (per axis, per direction)
    or the next draw would revert them. All other Text artists — axis labels,
    titles, legends, annotations, suptitles, colorbar labels, offset texts —
    hold their size once set.
    """
    # Realise tick labels so current sizes are readable.
    fig.canvas.draw()

    # Record per-axis tick sizes BEFORE the generic pass (so we scale the
    # authored size once, not a size the generic pass already touched).
    tick_sizes = []
    for ax in fig.get_axes():
        for axis_name in ("x", "y"):
            labs = getattr(ax, f"get_{axis_name}ticklabels")()
            szs = [
                lab.get_fontsize()
                for lab in labs
                if isinstance(lab.get_fontsize(), (int, float))
            ]
            if szs:
                tick_sizes.append((ax, axis_name, min(szs)))

    # Generic pass: every Text artist in the figure tree.
    for txt in fig.findobj(mtext.Text):
        sz = txt.get_fontsize()
        if isinstance(sz, (int, float)):
            txt.set_fontsize(sz * factor)

    # Durable tick sizes (survive the savefig draw).
    for ax, axis_name, sz in tick_sizes:
        ax.tick_params(axis=axis_name, labelsize=sz * factor)


def bump_fig_fonts(fig, delta_pt: float) -> None:
    """Enlarge every text element on ``fig`` by ``delta_pt`` points (additive).

    Companion to the multiplicative opt-in autoscaling: use this when a figure
    is styled by rc defaults (or mixed sizes) and the instruction is "one font
    size up" — title 14 -> 15, ticks 10 -> 11, and so on, preserving the
    authored size differences exactly. Call after the figure is fully built and
    before ``render_figure``. Same tick-durability handling as the scaler
    (sizes pushed through ``tick_params`` so the savefig draw does not revert
    them). Not idempotence-guarded: call it once per figure.
    """
    fig.canvas.draw()

    tick_sizes = []
    for ax in fig.get_axes():
        for axis_name in ("x", "y"):
            labs = getattr(ax, f"get_{axis_name}ticklabels")()
            szs = [
                lab.get_fontsize()
                for lab in labs
                if isinstance(lab.get_fontsize(), (int, float))
            ]
            if szs:
                tick_sizes.append((ax, axis_name, min(szs)))

    for txt in fig.findobj(mtext.Text):
        sz = txt.get_fontsize()
        if isinstance(sz, (int, float)):
            txt.set_fontsize(sz + delta_pt)

    for ax, axis_name, sz in tick_sizes:
        ax.tick_params(axis=axis_name, labelsize=sz + delta_pt)


def bump_label_and_legend_fonts(fig, delta_pt: float) -> None:
    """Enlarge only the axis labels and legend text/titles by ``delta_pt``.

    Targeted companion to ``bump_fig_fonts`` for review revisions of the form
    "legend and axis labels up another point" — tick labels, titles, and
    annotations are left alone. Stacks with a prior ``bump_fig_fonts`` call.
    """
    for ax in fig.get_axes():
        for lbl in (ax.xaxis.label, ax.yaxis.label):
            sz = lbl.get_fontsize()
            if isinstance(sz, (int, float)):
                lbl.set_fontsize(sz + delta_pt)
        leg = ax.get_legend()
        if leg is not None:
            for txt in leg.get_texts():
                sz = txt.get_fontsize()
                if isinstance(sz, (int, float)):
                    txt.set_fontsize(sz + delta_pt)
            title = leg.get_title()
            if title is not None and title.get_text():
                sz = title.get_fontsize()
                if isinstance(sz, (int, float)):
                    title.set_fontsize(sz + delta_pt)


def render_figure(
    fig,
    out_path,
    *,
    full_page: bool = False,
    quiet: bool = False,
    autoscale_fonts: bool = False,
    min_placed_pt: float | None = None,
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
        Suppress the console 'Saved' and legibility lines (for buffer-less
        internal renders / tests).
    autoscale_fonts : bool, default False
        OPT-IN. If True and the smallest tick label would print below the
        target at the placed width, enlarge all figure text by a common factor
        (capped at ``config.FIG_MAX_FONT_SCALE``) before saving. Default False:
        the figure is saved exactly as authored.
    min_placed_pt : float, optional
        Per-call target for the smallest printed label when
        ``autoscale_fonts=True``. Defaults to ``config.FIG_MIN_PLACED_PT``.
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

    # ── Opt-in font autoscaling (before the save draw) ───────────────────────
    placed_mm = _placed_width_mm(fig, full_page)
    shrink = placed_mm / (w_in * _MM_PER_INCH) if w_in > 0 else 1.0
    applied_scale = getattr(fig, _FONT_SCALE_ATTR, None)
    if autoscale_fonts and applied_scale is None:
        target_pt = (
            float(min_placed_pt)
            if min_placed_pt is not None
            else config.FIG_MIN_PLACED_PT
        )
        placed_pt = _smallest_font_pt(fig) * shrink
        if placed_pt < target_pt:
            factor = min(config.FIG_MAX_FONT_SCALE, target_pt / placed_pt)
            _scale_fig_fonts(fig, factor)
            setattr(fig, _FONT_SCALE_ATTR, factor)
            applied_scale = factor

    # ── Effective save dpi ───────────────────────────────────────────────────
    # Never exceed the print ceiling, and cap so the saved raster does not
    # exceed the A4 pixel budget in the binding dimension(s).
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

    # Legibility detector (advisory) — flag figures whose smallest label would
    # print below the threshold once placed. Candidate list for per-figure font
    # attention, not a verdict.
    smallest_pt = _smallest_font_pt(fig)
    placed_pt = smallest_pt * shrink
    if placed_pt < LEGIBILITY_MIN_PT and not quiet:
        detail = (
            f"after ×{applied_scale:.2f} font scale (cap)"
            if applied_scale is not None
            else "as authored"
        )
        console_utils.warn(
            f"Legibility: {out_path.name} smallest label ~{placed_pt:.1f} pt "
            f"{detail} when placed at {placed_mm:.0f} mm "
            f"(figsize {w_in:.1f}×{h_in:.1f} in)."
        )

    if not quiet:
        extra = f"{dpi} dpi"
        if applied_scale is not None:
            extra += f", fonts ×{applied_scale:.2f}"
        console_utils.saved(out_path.name, extra=extra)

    return dpi
