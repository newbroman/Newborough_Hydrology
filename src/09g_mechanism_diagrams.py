r"""
====================================================================================
09g — MECHANISM DIAGRAMS: FOUR-DRIVER SCHEMATIC GRID + COASTAL-VS-CLIMATE REACH
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
      a full-width coastal-vs-climate reach panel carrying the two accumulating
      drivers (coastal retreat near-shore with erosion ghosting; the spatially
      uniform climate decline; their crossing at ~698 m, beyond which climate is
      the deeper driver).

  09g_coastal_vs_climate_reach  The reach panel standalone (same body).

Schematic, not to scale, illustrative: amplitudes sit on the shared 09f-derived
scale and illustrate mechanism and direction, not measured section geometry. The
quantitative treatment lives in Scripts 09f (reach), 20 (λ), 25 (δ₀, L, c) and
37b (site footing); the report caption carries the observed/modelled split (only
the coastal water-table drawdown is modelled; the warren-wide climate fall, the
clearfell step and both scrape terms are observed).

All PHYSICAL amplitudes are read live from committed pipeline outputs via
utils/mechanism_fig_utils (no hardcoded amplitudes), with documented first-pass
fallbacks (pipeline_params._DEFAULTS) — the 09b/09d/09f precedent. 09g runs
after 09f in Phase 17, so on a normal full run every input already exists.

Data sources (all on `main`)
----------------------------
  outputs/09_scraping_intervention/09f_01_reach_profile.csv
      — row 0: edge amplitudes per driver (standing pine, coastal 5-yr/storm,
        scrape cut rise, thinned, climate 20-yr); full columns: the coastal
        20-yr decay (= (20/5) x |coastal_5yr(d)|), the flat climate line
        (|climate_20yr|) and the coastal-vs-climate crossing (~698 m).
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
(slack wet/dry states, pool level, off-cut drawdown, crossing distance).

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

__version__ = "1.2.0"  # Hollingham (2026) — 2026-07-18
# 1.2.0 — Now also renders the two lay public-summary figures (phase 3, via
#         gen_grid_lay.render_all): management (before/after) and drivers
#         (before/after). Keeps the lay and technical figures in one run so they
#         cannot fall out of sync. Still display-only; no analytical-headline change.
# 1.1.0 — Reach seam continuity: numeric checks now verify near == inland at the
#         330 m boundary for all three retreat states (mechanism_fig_utils v1.1.0
#         anchors the parabolas to the committed drawdowns; storm/5-yr continue
#         inland to 900 m). Replaces the old ~1 px "break match" print.
# 1.0.0 — New. Consolidates the locked dev mechanism-figure generators
#         (dune_fig_common 0.4.0; gen_scrape 0.3.0; gen_forest 0.1.0;
#         gen_climate 0.2.0; gen_grid 0.8.0; gen_reach_discont 0.5.0;
#         gen_grid_combined 0.2.0 — 2026-07-17 sign-off) into one tier-D
#         pipeline step on utils/mechanism_fig_utils. Shipped outputs are the
#         combined grid + the standalone reach; the four singles / technical
#         grid / lay variant remain dev-only. All amplitudes de-hardcoded to
#         committed CSVs (09f_01 row 0 + full reach columns; 10m WMC3; 10a
#         clearfell steps) with pipeline_params first-pass fallbacks; schematic
#         drawing constants centralised in config.py (MECH_FIG_*).

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

    # climate
    wt_clim, _, ponds = M.climate_build_after_table(wt_before)
    info(f"climate uniform drop {M.mm_px(M.EDGE_DH_MM['climate_20yr']):.1f} px "
         f"({M.EDGE_DH_MM['climate_20yr']:.0f} mm x 20-yr basis); ponds remaining: "
         f"{[(round(a), round(b)) for a, b, _l in ponds] if ponds else 'none (both slacks dry)'}")

    # reach
    cdd = reach['coastal_dd']
    info(f"reach ({reach['source']}): coastal shore {-cdd(0.0):.0f} mm, "
         f"climate flat {-reach['climate_mm']:.0f} mm, crossing {reach['crossing_m']:.0f} m")
    for d in (0.0, reach['crossing_m'], 900.0):
        info(f"  d={d:5.0f} m  coastal_dd={cdd(d):6.1f} mm  \u2192 "
             f"{'coastal' if cdd(d) > reach['climate_mm'] else 'climate'} deeper")
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
        description="09g — four-driver mechanism grid + coastal-vs-climate reach (display)")
    parser.parse_args()

    banner("09g", "MECHANISM DIAGRAMS \u2014 FOUR-DRIVER GRID + COASTAL-VS-CLIMATE REACH")
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
