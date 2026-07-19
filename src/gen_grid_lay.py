#!/usr/bin/env python3
"""
gen_grid_lay.py — LAY variant of the mechanism diagrams, for the public summary
(English / Welsh / Polish). NOT a pipeline step: it is a public-summary asset
that imports its geometry from the pipeline module `mechanism_fig_utils` so the
lay and technical figures cannot drift apart. Script 09g owns the pipeline's
display need (technical grid + reach); this generator adds only the
plain-language, leaflet-friendly cut alongside it.

Design decisions (Martin, 2026-07-18):
  1. Separate generator (this file), not a register flag on the shared builder.
  2. One plain sentence instead of the footing table.
  3. Simpler than the technical grid, BUT the starting ("before") state must be
     visible to a lay reader — the dashed reference line alone does not carry
     it. So the four drivers are split into TWO before/after figures, each with
     the undisturbed / forested starting state drawn explicitly above the after:
       A — management changes : undisturbed -> dune scrape | forest -> clearfell
       B — site-wide drivers  : undisturbed -> coastal     | undisturbed -> climate
  4. Output labelled "lay" and written ALONGSIDE the technical outputs
     (same outputs/09_scraping_intervention/ folder).

Register (differs from the technical grid — geometry is byte-identical, only the
drawn text changes): rounded plain-language magnitudes; no well names, no
p-values, no mm, no script references; the one modelled driver (coastal) flagged
in plain words as "expected, not yet directly measured"; base-sans-font
characters only, enforced by a build-time glyph guard (matters most for the
translated Welsh/Polish builds).

CHANGELOG
    1.1.0  2026-07-18  Split into two before/after figures (A management,
                       B drivers) so the starting state is explicit; the earlier
                       single 2x2 hid the "before" (Martin's review).
    1.0.0  2026-07-18  New. 2x2 lay driver grid on the shared solver/profile.
"""
from __future__ import annotations

__version__ = "1.1.0"

import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from utils.console_utils import banner, phase, info, saved
from utils.paths import (
    make_all_dirs,
    OUT_09G_LAY_MGMT_SVG, OUT_09G_LAY_MGMT_PNG,
    OUT_09G_LAY_DRIVERS_SVG, OUT_09G_LAY_DRIVERS_PNG,
)
import utils.mechanism_fig_utils as M


# ------------------------------------------------------------------------------------------------
# Layout — two 2-column figures. Each column is one driver shown as before (top) -> after (bottom),
# so the starting state is always on the page. Section cells reuse the pipeline geometry builders.
# ------------------------------------------------------------------------------------------------
LAY_W = 900
_L_ML, _L_MR, _L_GAP = 16, 16, 16
_L_COLW = (LAY_W - _L_ML - _L_MR - _L_GAP) // 2
_L_COLX = [_L_ML, _L_ML + _L_COLW + _L_GAP]
_L_TITLE_H = 48
_L_HDR_H = 22                          # column header (driver name)
_L_SEC_H = 120                         # one cross-section cell
_L_BA_GAP = 14                         # before->after gap (holds the "after felling" tag)
_L_ONELINE_H = 30
_L_CAPTION_H = 34


def _sec(geo, colx, top):
    """place a native cross-section into a lay cell."""
    return M.place(geo, colx + 10, top, _L_COLW - 20, _L_SEC_H - 8)


def _figure(title, subtitle, columns, caption):
    """A 2-column before/after figure.

    columns : list of (driver_title, before_geo_fn, after_geo_fn, before_tag,
              after_tag, oneliner).
    """
    y_hdr = _L_TITLE_H
    y_before = y_hdr + _L_HDR_H
    y_after = y_before + _L_SEC_H + _L_BA_GAP
    y_oneline = y_after + _L_SEC_H + 4
    height = y_oneline + _L_ONELINE_H + _L_CAPTION_H

    s = [f'<svg width="{LAY_W}" height="{height:.0f}" viewBox="0 0 {LAY_W} {height:.0f}" '
         f'xmlns="http://www.w3.org/2000/svg">'
         f'<rect width="{LAY_W}" height="{height:.0f}" fill="#fff"/>']
    s.append(M.txt(_L_ML, 26, title, size=16, w='600'))
    s.append(M.txt(_L_ML, 43, subtitle, size=11, col='#888780'))

    for i, (dtitle, before_fn, after_fn, before_tag, after_tag, oneliner) in enumerate(columns):
        colx = _L_COLX[i]
        cx = colx + _L_COLW / 2
        s.append(M.txt(cx, y_hdr + 15, dtitle, size=13, w='600', anchor='middle'))
        # before
        s.append(M.txt(colx + 12, y_before + 12, before_tag, size=9.5, w='600',
                       col='#9a968a'))
        s.append(_sec(before_fn(), colx, y_before))
        # after
        s.append(M.txt(colx + 12, y_after + 12, after_tag, size=9.5, w='600', col='#2b6a8a'))
        s.append(_sec(after_fn(), colx, y_after))
        # one-liner
        s.append(M.txt(cx, y_oneline + 14, oneliner, size=10, col='#4a4a42', anchor='middle'))

    if caption:
        s.append(M.txt(LAY_W / 2, height - 12, caption, size=11, w='600',
                       col='#3a3a33', anchor='middle', style=' font-style="italic"'))
    s.append('</svg>')
    return "".join(s)


def build_management_svg():
    """Figure A — the two management changes, each from its own starting state."""
    return _figure(
        "What management does to the water table",
        "simple diagrams - not to scale",
        [
            ("Dune scrape",
             M.geo_wet_before, M.geo_scrape_after,
             "before: undisturbed dune", "after scraping",
             "A cut slack fills with water; a spot just inland drops a little."),
            ("Clearing the forest",
             lambda: M.geo_forest(False), lambda: M.geo_forest(True),
             "before: standing forest", "after felling",
             "Felling lifts the table back over the year, but not the summer low."),
        ],
        "Both are local: they change the slack that is worked and its close "
        "neighbours, not the whole site.")


def build_drivers_svg():
    """Figure B — the two site-wide drivers, both from the undisturbed dune."""
    return _figure(
        "What coast and climate do to the water table",
        "simple diagrams - not to scale",
        [
            ("Coastal retreat",
             M.geo_wet_before, M.geo_coastal_after,
             "before: undisturbed dune", "after the shore retreats",
             "The retreating shore pulls the table down near the coast "
             "(expected, not yet directly measured)."),
            ("A changing climate",
             M.geo_wet_before, M.geo_climate_after,
             "before: undisturbed dune", "after climate drying",
             "A slow, steady fall across the whole site, drying every slack."),
        ],
        "The slow, site-wide climate fall is the biggest overall change; "
        "the sea's retreat matters most near the shore.")


# ------------------------------------------------------------------------------------------------
# Glyph guard — every drawn character must be in the base sans font (no missing-glyph boxes).
# ------------------------------------------------------------------------------------------------
# Codepoints the technical render exposed as boxes in cairosvg's default font, plus the wider
# symbol families most likely to re-enter through translation. Extend if a new box appears.
_FORBIDDEN = {
    0x2192, 0x2190, 0x2194,          # arrows
    0x2248, 0x2260, 0x2264, 0x2265,  # approx / relational maths
    0x2032, 0x2033,                  # prime / double-prime
    0x2212,                          # MINUS SIGN (use plain hyphen in lay text)
    0x00d7,                          # multiplication sign
}


def _assert_glyph_safe(svg, which):
    """fail the build if any drawn <text> content carries a forbidden codepoint."""
    texts = re.findall(r'<text[^>]*>(.*?)</text>', svg, flags=re.S)
    bad = {}
    for t in texts:
        for ch in t:
            if ord(ch) in _FORBIDDEN:
                bad.setdefault(hex(ord(ch)), t.strip())
    if bad:
        raise ValueError(
            f"gen_grid_lay [{which}]: forbidden glyph(s) in drawn text — would "
            f"render as a missing-glyph box: {bad}. Replace with base-font "
            "characters (plain hyphen, 'about', spelled-out words).")


_FIGURES = [
    ("management", build_management_svg, OUT_09G_LAY_MGMT_SVG, OUT_09G_LAY_MGMT_PNG),
    ("drivers",    build_drivers_svg,    OUT_09G_LAY_DRIVERS_SVG, OUT_09G_LAY_DRIVERS_PNG),
]


def render_all(png_width=1400):
    """Build, glyph-check and render both lay figures. Returns the list of
    (png_name, ok) render results. Callable standalone or from Script 09g."""
    make_all_dirs()
    results = []
    for which, builder, svg_path, png_path in _FIGURES:
        svg = builder()
        _assert_glyph_safe(svg, which)
        ok = M.render_svg(svg, svg_path, png_path, png_width=png_width)
        results.append((png_path.name, ok))
    return results


def main():
    banner("Lay mechanism diagrams (public summary)", __version__)
    make_all_dirs()
    for n, (which, builder, svg_path, png_path) in enumerate(_FIGURES, 1):
        phase(n, f"Building lay figure: {which} (before -> after, 2 columns)")
        svg = builder()
        _assert_glyph_safe(svg, which)
        info("register: plain-language, rounded, no well names / p-values / script refs")
        info("glyph guard: passed (all drawn text in base sans font)")
        M.render_svg(svg, svg_path, png_path, png_width=1400)
        saved(f"{svg_path.name} + {png_path.name}")


if __name__ == "__main__":
    main()
