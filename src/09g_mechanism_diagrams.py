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
      a common vertical amplitude scale (so the drivers' relative magnitudes
      compare): row 1 the two starting states (undisturbed wet slacks; standing
      forest), row 2 the two local interventions (dune scrape; clearfell), row 3
      a full-width reach panel carrying the one site-wide driver: coastal retreat
      near-shore with erosion ghosting, tapering to zero at the fitted reach L.
      The grid title COUNTS the drivers drawn rather than spelling a number
      (mechanism_fig_utils.DRIVERS), so it cannot outlive one of them.

      NO spatially uniform far-field term is drawn. The fitted constant c of the
      Script 25 coastal decay compensates the cumulative-water-balance covariate
      rather than measuring a driver: across fixed-length rolling windows the two
      correlate at about -0.8 (25_13_rolling_window.csv), so when the covariate
      takes more of the decline the constant takes less. Drawing it beside the
      coastal curve invites a comparison it cannot support.

  09g_coastal_vs_climate_reach  The reach panel standalone (same body). Filename
      retained so committed report/paper figure references keep resolving.

Schematic, not to scale, illustrative: amplitudes sit on the shared 09f-derived
scale and illustrate mechanism and direction, not measured section geometry. The
quantitative treatment lives in Scripts 09f (reach), 20 (λ), 25 (δ₀ and L) and
37b (site footing); the report caption carries the observed/modelled split (only
the coastal water-table drawdown is modelled; the clearfell step and both scrape
terms are observed).

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
(slack wet/dry states, pool level, off-cut drawdown, coastal reach and seams).

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

__version__ = "1.7.0"  # Hollingham (2026) — 2026-08-21. Two reach-panel render
#   defects Martin found in the regenerated figures, both fixed in
#   mechanism_fig_utils v1.11.0: the storm and 5-yr water-table curves ran above
#   the drawn dune surface between roughly 80 m and 250 m (a head drawn as
#   standing water, and drawn as if retreat RAISED it), and the delta-0
#   annotation was unreadable under the leader line. This script gains the
#   sub-surface assertion: it prints each retreat curve's clearance below the
#   ground and below the undisturbed table and RAISES if any is negative, because
#   image-view does not catch a curve over the dune reliably in-session.
#
# v1.6.0 (2026-08-20). The far-field term is
#   REMOVED from every figure this script emits, reversing the 1.5.0 restoration
#   on new evidence: the fixed-length rolling-window sweep (25_13) measures
#   corr(c, CWB trend contribution) at about -0.8 at every window length, so c
#   compensates the covariate rather than carrying a site-wide signal of its own.
#   The grid's reach row and the standalone reach lose the far-field curve, its
#   callout and its legend swatch; the lay drivers figure loses its third panel;
#   the numeric checks lose the far-field block; 25_01 is no longer read. The
#   grid title now counts the drivers it draws. Follows mechanism_fig_utils
#   v1.10.0 and gen_grid_lay v1.7.0. Script 09f is untouched at v1.9.0.
#
# v1.5.0 (2026-08-19): D-043 amended: the
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

    # reach — coastal retreat is the only driver drawn; no spatially uniform term
    cdd = reach['coastal_dd']
    info(f"reach ({reach['source']}): coastal shore {-cdd(0.0):.0f} mm, tapering to "
         f"zero at the fitted reach L = {reach['reach_L_m']:.0f} m "
         f"(\u03b4\u2080 {-reach['delta0_mm_yr']:.2f} mm/yr); no far-field term "
         f"drawn, no crossing computed")
    info(f"drivers drawn: {M.count_word(len(M.DRIVERS)).lower()} "
         f"({', '.join(M.DRIVERS)}) \u2014 the grid title counts this register")

    # Sub-surface guarantee. A water-table curve drawn above the dune, or above the
    # water standing in a slack, is a physical error \u2014 coastal retreat lowers heads, it
    # does not raise them \u2014 and image-view does not catch it reliably in-session, so it
    # is asserted rather than looked at. The first margin is against the surface a
    # reader sees (ground where the slack is dry, water surface where it is wet); the
    # second is against the undisturbed table the drawdowns are measured from. Both
    # cover the near-shore and inland halves together.
    clearance = M.reach_clearance(reach, multiples=True)
    worst = min(min(v) for v in clearance.values())
    for k, (vs_s, vs_u) in clearance.items():
        info(f"  clearance [{k:>5s}]: {vs_s:+6.2f} px below the drawn surface, "
             f"{vs_u:+6.2f} px below the undisturbed table")
    if worst < 0.0:
        raise AssertionError(
            f"09g: a retreat curve is drawn {abs(worst):.2f} px above a surface it may "
            "not cross \u2014 see mechanism_fig_utils.subsurface()")
    info(f"sub-surface check: OK, minimum clearance {worst:+.2f} px")
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
