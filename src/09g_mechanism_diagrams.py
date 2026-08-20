r"""
====================================================================================
09g — MECHANISM DIAGRAMS: SCHEMATIC GRID + COASTAL REACH
====================================================================================
Purpose
-------
Display/utility step (tier D, Phase 17 — like 09f/27): emits the §5.8 conceptual
mechanism figure set for the report and public summaries.

  09g_mechanism_grid            THE report figure. A composited grid of schematic
      cross-sections drawn on ONE shared, vertically exaggerated dune profile and
      a common vertical amplitude scale (so the four drivers' relative magnitudes
      compare): row 1 the two starting states (undisturbed wet slacks; standing
      forest), row 2 the two local interventions (dune scrape; clearfell), row 3
      a full-width reach panel carrying the two site-wide drivers: coastal
      retreat near-shore with erosion ghosting, tapering to zero at the fitted
      reach L, and the spatially uniform far-field term. The far-field term is
      drawn SIGNED and is marginal — on the committed fit a slight rise, which
      is why it is worth showing — but it is never labelled a climate rate:
      only the sum of the constant and the CWB trend is identified (D-039), so
      the two drivers are never compared, no crossing is drawn (D-042), and no
      band stands in for the term (D-043).

  09g_coastal_vs_climate_reach  The reach panel standalone (same body). Filename
      retained so committed report/paper figure references keep resolving.

Schematic, not to scale, illustrative: amplitudes sit on the shared 09f-derived
scale and illustrate mechanism and direction, not measured section geometry. The
quantitative treatment lives in Scripts 09f (reach), 20 (λ), 25 (δ₀, L and the
identified far-field sum) and 37b (site footing); the report caption carries the
observed/modelled split (only the coastal water-table drawdown is modelled; the
clearfell step and both scrape terms are observed; the far-field term is
neither — it is fitted, marginal and not separately identified).

All PHYSICAL amplitudes are read live from committed pipeline outputs via
utils/mechanism_fig_utils (no hardcoded amplitudes), with documented first-pass
fallbacks (pipeline_params._DEFAULTS) — the 09b/09d/09f precedent. 09g runs
after 09f in Phase 17, so on a normal full run every input already exists.

Data sources (all on `main`)
----------------------------
  outputs/09_scraping_intervention/09f_01_reach_profile.csv
      — row 0: edge amplitudes per driver (standing pine, coastal 5-yr/storm,
        scrape cut rise, thinned); full columns: the coastal 20-yr decay
        (= (20/5) x |coastal_5yr(d)|). No crossing is read or computed.
  outputs/25_coastal_gradient/25_01_panel_fit_parameters.csv
      — c_mm_yr (forest-free linear-capped), SIGNED, drawn as the spatially
        uniform far-field term. Read here rather than through 09f, whose panel
        no longer carries it (D-043).
  outputs/10_clearfell_baci/10m_report_numbers.csv
      — WMC3_BACI_DiD_step_2015_scraping: the one measured off-cut drawdown
        (-55 mm; reproducible -54 mm in 2023).
  outputs/10_clearfell_baci/10a_report_numbers.csv
      — clearfell BACI steps (annual + summer) for the grid magnitude line.

Outputs
-------
  09g_mechanism_grid.svg / .png            — composited grid (report §5.8 figure)
  09g_coastal_vs_climate_reach.svg / .png  — standalone reach figure

Verification
------------
Image-view is unreliable in-session — verify by the printed numeric checks
(slack wet/dry states, pool level, off-cut drawdown, coastal reach, far-field
term and seams).

No SSM fitting, no new physics: a schematic re-presentation of existing
modelled + measured fields. Captions are supplied in the document text, not
baked into the figures (avoids duplication when placed in LibreOffice).

References
----------
Hollingham (2026), §5.8. Companion to 09f (quantitative reach) and 37b
(comparative footing). SCRAPING_EFFECTS_KNOWLEDGE.md (scrape framing);
HANDOVER_mechanism_figs_to_pipeline_2026-07-17 (signed-off design).
====================================================================================
"""

__version__ = "1.5.0"  # Hollingham (2026) — 2026-08-19. D-043 amended: the
#   far-field term is RESTORED as a driver, drawn SIGNED (the earlier render
#   showed it falling because an abs() was applied to a positive c) and labelled
#   as fitted, marginal and not separately identified. The stack is three panels
#   again and the numeric checks report the term's amplitude and its ponds. The
#   band stays withdrawn and no crossing returns. Follows mechanism_fig_utils
#   v1.9.0; Script 09f is unchanged at v1.9.0 (its panel (a) keeps five curves).
#
# v1.4.0 (2026-08-19): far-field driver removed entirely; two-panel stack.
#   Superseded by 1.5.0 the same day — the removal was broader than intended.
# v1.3.0 (2026-08-19): flat climate line and crossing retired (D-039), replaced
#   by a far-field band. Band superseded by 1.4.0.
# v1.2.0 (2026-07-18): four-driver mechanism grid + reach, live amplitudes.
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import argparse

import numpy as np

from utils.paths import (
    make_all_dirs,
    OUT_09G_GRID_SVG, OUT_09G_GRID_PNG, OUT_09G_REACH_SVG, OUT_09G_REACH_PNG,
)
from utils.console_utils import banner, phase, info, saved
import utils.mechanism_fig_utils as M


def _at(arr, x):
    return float(np.interp(x, M.X, arr))


def _print_numeric_checks(reach):
    """the printed verification the dev generators carried — image-view is unreliable."""
    seaward_c, inland_c = M.SLACK_C
    inland_floor = M.g1(inland_c)

    # forest / clearfell
    wt_notree, wt_forest, wt_fell = M.forest_build_tables()
    info(f"forest suppression {M.mm_px(M.EDGE_DH_MM['forest_standing']):.1f} px "
         f"({M.EDGE_DH_MM['forest_standing']:.0f} mm on the shared scale)")
    info(f"  inland slack @ {inland_c:.0f}: no-tree {_at(wt_notree, inland_c):.1f} (wet)  "
         f"forest {_at(wt_forest, inland_c):.1f} "
         f"({'DRY' if _at(wt_forest, inland_c) > inland_floor else 'wet'})  "
         f"felled {_at(wt_fell, inland_c):.1f} "
         f"({'wet again' if _at(wt_fell, inland_c) < inland_floor else 'still dry'})")

    # scrape
    wt_before = M.segmented(110.0, 78.0, nudge_seg2=True)[0]
    wt_scrape, (pool_l, pool_r) = M.scrape_build_after_table()
    pool = M.scrape_pool_level()
    info(f"scrape pool level {pool:.1f} ({_at(wt_before, seaward_c) - pool:+.1f} px vs seaward "
         f"slack — measured {M.EDGE_DH_MM['scrape_cut_rise']:+.0f} mm rise, drawn capped in-slack); "
         f"span {pool_l:.0f}\u2013{pool_r:.0f}")
    info(f"  off-cut drawdown (measured WMC3 {M.EDGE_DH_MM['scrape_offslack']:.0f} mm = "
         f"{M.mm_px(M.EDGE_DH_MM['scrape_offslack']):.1f} px, localised near-field); "
         f"inland slack after {_at(wt_scrape, inland_c):.1f} "
         f"({'DRY' if _at(wt_scrape, inland_c) > inland_floor else 'still wet'}, "
         f"{_at(wt_scrape, inland_c) - inland_floor:+.1f} vs floor {inland_floor:.0f})")

    # far-field term — SIGNED, so the sign printed here is the sign drawn (D-043)
    ff = reach['far_field_mm']
    _, _, ff_ponds = M.uniform_offset_table(wt_before, ff)
    info(f"far-field term {ff:+.1f} mm over {M.MECHANISM_HORIZON_YEARS:.0f} yr "
         f"(c {reach['far_field_c_mm_yr']:+.2f} mm/yr, "
         f"{'rise' if ff > 0 else 'fall'}); ponds remaining: "
         f"{[(round(a), round(b)) for a, b, _l in ff_ponds] if ff_ponds else 'none (both slacks dry)'}")

    # reach
    cdd = reach['coastal_dd']
    info(f"reach ({reach['source']}): coastal shore {-cdd(0.0):.0f} mm, tapering to "
         f"zero at the fitted reach L = {reach['reach_L_m']:.0f} m "
         f"(\u03b4\u2080 {-reach['delta0_mm_yr']:.2f} mm/yr); far-field term "
         f"{ff:+.1f} mm, not separately identified, no crossing computed")
    for d in (0.0, reach['reach_L_m'] / 2.0, reach['reach_L_m']):
        info(f"  d={d:5.0f} m  coastal_dd={cdd(d):6.1f} mm")
    # seam continuity: near-shore parabolas are anchored to the committed drawdowns at
    # the 330 m boundary, so near == inland exactly for every retreat state (v1.1.0 fix)
    dd_at = {'storm': reach['storm_dd'], '5yr': reach['c5_dd'], '20yr': cdd}
    und_seam = float(np.interp(M.XE, M.X, M.segmented(110.0, 78.0, nudge_seg2=True)[0]))
    for k in ('storm', '5yr', '20yr'):
        hg = M.SEA - (und_seam + M.mm_px(dd_at[k](M._R_DN)))
        near = _at(M.grandf(M.SH[k], hg)(M.X), M.XE)
        inland = M._r_und_in(M._R_DN) + M.mm_px(dd_at[k](M._R_DN))
        flag = 'OK' if abs(near - inland) < 0.05 else 'MISMATCH'
        info(f"reach seam @330 m [{k:>5s}]: near {near:.2f} px  inland {inland:.2f} px  "
             f"\u0394={near - inland:+.2f} px  {flag} "
             f"(dd={dd_at[k](M._R_DN):.1f} mm; storm/5-yr continue to 900 m)")


def main():
    parser = argparse.ArgumentParser(
        description="09g — mechanism grid + coastal reach (display)")
    parser.parse_args()

    banner("09g", "MECHANISM DIAGRAMS \u2014 SCHEMATIC GRID + COASTAL REACH", version=__version__)
    make_all_dirs()

    phase(1, "Loading committed amplitudes")
    M.load_amplitudes()
    reach = M.load_reach()
    clearfell = M.load_clearfell_steps()
    cf_a, cf_ap, cf_s, cf_sp = clearfell
    info(f"clearfell steps: {cf_a:+.3f} m annual ({cf_ap}); {cf_s:+.3f} m summer ({cf_sp})")
    _print_numeric_checks(reach)

    phase(2, "Compositing figures")
    grid_svg = M.build_grid_combined_svg(reach, clearfell)
    ok_g = M.render_svg(grid_svg, OUT_09G_GRID_SVG, OUT_09G_GRID_PNG, png_width=1580)
    saved(OUT_09G_GRID_SVG.name + (" + " + OUT_09G_GRID_PNG.name if ok_g else ""))

    reach_svg = M.build_reach_svg(reach)
    ok_r = M.render_svg(reach_svg, OUT_09G_REACH_SVG, OUT_09G_REACH_PNG, png_width=1520)
    saved(OUT_09G_REACH_SVG.name + (" + " + OUT_09G_REACH_PNG.name if ok_r else ""))

    phase(3, "Rendering lay public-summary figures")
    import gen_grid_lay
    for png_name, ok in gen_grid_lay.render_all():
        saved(png_name + ("" if ok else " (svg only)"))

    print("\nDone.")


if __name__ == "__main__":
    main()
