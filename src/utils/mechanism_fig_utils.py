"""
mechanism_fig_utils.py — shared solver, profile, amplitude loaders, SVG helpers and cell
geometry for the Script 09g public-summary mechanism diagrams (§5.8 conceptual figure).

Consolidates the locked dev generators (2026-07-17 sign-off) into one pipeline module:

    dune_fig_common.py   (v0.4.0)  chained short-Dupuit-segment solver + shared profile +
                                   09f amplitude scale + SVG helpers
    gen_coast_seg3.py               coastal retreat cell geometry (retreat states + ghosting)
    gen_scrape.py        (v0.3.0)  scrape after-table (pool marginally higher, measured
                                   WMC3 off-cut, NO network-wide cone)
    gen_forest.py        (v0.1.0)  forest / clearfell tables + trees
    gen_climate.py       (v0.2.0)  uniform climate lowering (continuous Dupuit, pond-only fill)
    gen_grid.py          (v0.8.0)  cell compositing helpers + grid layout
    gen_reach_discont.py (v0.5.0)  coastal-vs-climate reach body (continuous 900 m scale)
    gen_grid_combined.py (v0.2.0)  THE report figure compositor (starting states +
                                   interventions + full-width reach panel)

The chained-segment water-table solver was developed and LOCKED on the coastal figure;
edit it HERE only. Per-mechanism functions add mechanism-specific shapes on top.

Physics vs figure-design
------------------------
PHYSICAL amplitudes are read LIVE from committed CSVs (no hardcoded amplitudes):
    09f_01_reach_profile.csv ROW 0 — one edge amplitude per driver (forest standing,
        coastal 5-yr/storm, scrape cut rise, thinned, climate 20-yr), and the full
        reach columns for the coastal-vs-climate reach panel (coastal 20-yr decay =
        (MECHANISM_HORIZON_YEARS / COAST_CHRONIC_YEARS) x |coastal_5yr(d)|, flat climate
        = |climate_20yr|, crossing where |coastal_5yr| == |climate_5yr| ~= 698 m).
    10m_report_numbers.csv — WMC3_BACI_DiD_step_2015_scraping: the ONE measured
        off-cut drawdown point (-55 mm; reproducible -54 mm in 2023).
    10a_report_numbers.csv — clearfell BACI steps (annual + summer) for the grid's
        clearfell magnitude line.
First-pass fallbacks live in pipeline_params._DEFAULTS (read via default_value())
with console warnings — the 09b/09d/09f precedent. Script 09g runs after 09f in
Phase 17, so fallbacks engage only on a partial/interrupted run.

FIGURE-DESIGN geometry (schematic, vertically exaggerated, not to scale) comes from
config.py (MECH_FIG_*): shared profile, PX_PER_MM amplitude scale, retreat states,
ghosting fractions, reach inland dune body. Remaining per-mechanism drawing
coordinates (slack cut spans, tree spacing, label positions, canvas layout) are
module-level named constants below — internal drawing coordinates of this figure,
not scientific parameters.

All builders are PURE (return SVG strings); Script 09g orchestrates, prints the
numeric verification checks (image-view is unreliable in-session — verify by the
printed checks) and writes the outputs via paths.py.

CHANGELOG
    1.6.6  2026-07-19  Inland flat-pond revision (Martin's review of the v1.6.5 render):
                       (a) per-curve flooding — the flat-pond flatten (_r_und_flat)
                       generalised to _flat_pond(dd, surf, grd), applied to EACH curve
                       against its OWN drawn-down surface. The reference floods where the
                       undisturbed table does; coastal floods only where the drawn-down
                       coastal surface still stands above the floor (so it no longer steps
                       under the far slack once coastal drawdown has recovered); climate,
                       drawn below every inland floor, floods nowhere and stays a smooth
                       declining line. (b) flat pond now spans only the TRULY flooded
                       width (where the ground floor is below the pond level), matching
                       segmented(); the regional table rises out on the landward flank,
                       not inside the slack — fixes "slack 3 not flat across the whole
                       slack". (c) sqrt bend -> smoothstep (zero slope at both ends) so
                       the flat->rise join has no kink — fixes the "step where climate and
                       coastal meet" at the ~698 m crossing. Verified: crossing meet is
                       smooth, coastal max adjacent step 0.49 px, seam continuity at 330 m
                       preserved. Management figures and global PX_PER_MM unaffected.
    1.6.5  2026-07-19  Inland slacks now read like the near-shore slacks. New
                       _r_und_flat() draws the inland undisturbed table as a FLAT pond
                       surface across each wet slack with a sqrt Dupuit bend down from
                       the landward (uphill) rim, instead of the smooth interpolator
                       sloping straight through. The reach reference line AND both
                       drawdown curves (coastal, climate; plus the grid's storm/5-yr
                       lines) are drawn on this base, in build_reach_body (standalone +
                       grid) and build_reach_panel (lay drivers figure), so all five
                       slacks read consistently (Martin: full consistency with the
                       reference). Climate never ponds inland (drawn-down table sits
                       below every slack floor) so its shape only reshapes slightly;
                       the coastal line still ponds in the far-landward slack and now
                       renders as a flat pond there rather than sloping through. Seam
                       continuity at 330 m preserved (330 m is dry, flat base == raw).
                       Config slack floors left at the raised values (Martin); global
                       PX_PER_MM and the management figures unaffected.
    1.6.4  2026-07-18  Fixed the flat climate curve introduced by the local reach
                       scale: climate_build_after_table now lowers the ACTUAL undisturbed
                       table (which already carries the near-shore ponds) rather than a
                       fresh smooth parabola that, at the smaller local drop, sat above
                       the slack floors and clamped into one long flat pond. Also fixed a
                       sign bug — the local px scale now takes abs() like the global
                       mm_px, so the near-shore climate drops the right way and meets the
                       inland climate exactly at the seam (179.6 == 179.6). Management
                       climate figure unaffected.
    1.6.3  2026-07-18  Reach figure rescaled instead of reshaped (Martin): the dune and
                       water-table geometry are LEFT ALONE (so they still match the
                       management diagrams that share ground()/segmented()). The existing
                       drawn gap between the undisturbed line and the sea-level 20-yr
                       erosion toe at the nose is DEFINED as coastal_dd(0)=581 mm, giving
                       a local reach amplitude scale _RPX; the climate offset, inland
                       drawdown curves and (now recomputed) exaggeration factor are all
                       drawn to that scale. The 581 mm marker is a DOTTED line at the toe
                       spanning that gap. Global PX_PER_MM (0.10, shared with 09f)
                       untouched; management figures unchanged.
    1.6.2  2026-07-18  Standalone reach near-shore labels tidied: storm / 5-yr / 20-yr
                       are labelled directly under their own ghost band (aligned where
                       the tick marks pointed), the "shoreline retreating" caption
                       moved to its own line below, and the tick marks removed. The
                       earlier inline "shoreline retreating: storm / 5 yr / 20 yr" had
                       displaced the state labels away from their bands. Grid reach
                       panel (multiples=True) unchanged — keeps the storm/5-yr Dupuit
                       curves.
    1.6.1  2026-07-18  build_reach_body gains a `multiples` flag so the grid's reach
                       panel and the standalone paper reach diverge as needed:
                       - grid (multiples=True): storm / 5-yr / 20-yr Dupuit curves
                         restored (near-shore + inland), each state labelled directly
                         UNDER its ghost band with NO tick marks, legend names all
                         three states;
                       - standalone (multiples=False): unchanged — single 20-yr
                         horizon, consolidated inline label, colour ticks (the paper
                         reviewer's decluttered version).
                       Fixes the grid: retreat labels no longer offset, ticks removed,
                       storm/5-yr lines back.
    1.6.0  2026-07-18  Two cosmetic follow-ups: (a) FONT_STACK pins
                       'Liberation Sans','DejaVu Sans',sans-serif on every text
                       element, so Greek/subscript glyphs render instead of falling
                       back to a box font; "d0" -> delta0 in the reach and technical-
                       stack coastal labels to match Section 4.11 notation; (b) the
                       near-shore storm/5-yr/20-yr band labels are consolidated from
                       three stacked colour labels into one compact inline
                       "shoreline retreating: storm / 5 yr / 20 yr" (each state in its
                       colour) with small colour ticks under the ghost bands — de-
                       clutters the shore while keeping the single 20-yr water-table
                       horizon.
    1.5.1  2026-07-18  Reach figure — second review pass:
                       (a) coastal measure bar re-anchored at the COAST EDGE where the
                       full -581 mm applies (was drawn near 300 m, where the taper is
                       ~386 mm, contradicting its "at shore" label); (b) arithmetic
                       made self-consistent — "d0 29.03 mm/yr x 20 yr" = 581 (unrounded
                       product; 29.0 x 20 = 580 would mismatch the 581 label);
                       (c) -127 mm annotation moved into a boxed callout in clear space
                       (was running across the dotted undisturbed line and the crossover
                       marker); near-shore already at a single 20-yr horizon (storm/5yr
                       are ghosted shoreline + band labels only), exaggeration x104
                       confirmed from actual axis scaling (103.93). NOTE: d0/c kept as
                       ASCII (not the delta0/c glyphs) because the cairosvg render font
                       fallback boxes some non-ASCII; revisit if a glyph-complete font
                       is pinned in the render step.
    1.5.0  2026-07-18  Technical reach figure sharpened (reviewer concerns):
                       (a) vertical quantified — a 100 mm scale bar plus direct
                       amplitude annotations (coastal shore -581 mm = d0 29.0 x 20;
                       climate -127 mm = c 6.35 x 20), the numbers that make the
                       crossover legible; (b) framing fixed — "water-table curves and
                       900 m reach to committed scale; dune surface illustrative;
                       vertical exaggerated x104", tied to the fitted d0/L/climate
                       (Section 4.11), no longer "schematic, not to scale";
                       (c) near-shore multiples resolved — only the 20-yr water-table
                       curve is drawn (storm/5-yr remain as ghosted shoreline + band
                       labels), so there is one unambiguous purple line; (d) x-ticks
                       regularised to 150 m; (e) crossover reworded to "climate
                       drawdown exceeds coastal"; solid/dashed/dotted confirmed
                       BW-safe (distinct luminance AND pattern).
    1.4.1  2026-07-18  Retreat-state legend removed from the technical reach figures;
                       storm / 5-yr / 20-yr are now labelled directly under their own
                       ghost shade (each band = one shoreline position), staggered in
                       depth with a colour tick, in both the overlaid reach and the
                       stacked technical coastal panel (build_reach_panel gains a
                       register flag; labels are technical-only, absent from lay). The
                       generic "shoreline retreating" band underline is dropped; a
                       "shoreline retreating (storm to 20-yr)" summary line remains.
    1.4.0  2026-07-18  Added build_reach_stack(reach, register): the stacked 3-panel
                       coastal-vs-climate figure (undisturbed/coastal/climate) now
                       lives here and serves BOTH registers — 'technical' (mm
                       amplitudes, d0/c, precise crossing; new 09g output) and 'lay'
                       (plain language; gen_grid_lay wraps it). The lay drivers figure
                       is unchanged bar the crossing tag now reading "~698 m".
    1.3.1  2026-07-18  build_reach_panel() gains near-shore pond fill (_reach_ponds):
                       the undisturbed and climate lay panels now show standing water
                       in the flooded slacks, not just a line. build_reach_body still
                       byte-identical (ponds are on the panel path only).
    1.3.0  2026-07-18  Added build_reach_panel() + _reach_base(): a single-driver
                       reach panel (undisturbed / coastal / climate) on the SHARED
                       profile, factored out of build_reach_body so the lay stacked
                       figure (gen_grid_lay) reuses the exact technical geometry
                       instead of a hand-rolled profile. build_reach_body unchanged
                       in output.
    1.2.0  2026-07-18  Render + register fixes (Martin's review, second pass):
                       (a) crossing computed at FULL precision from the CSV edge +
                       reach length rather than interpolating the 2-dp-rounded
                       coastal column, so 09g and 09f both report 698 m (the true
                       line crossing; 697 was a CSV-rounding artefact);
                       (b) grid title/subtitle reflowed onto two left-aligned lines
                       (were overlapping); (c) box-rendering glyphs removed from the
                       drawn labels — U+2192 arrow after "shoreline retreating" and
                       U+2248 before the crossing label (cairosvg's sans font lacks
                       them); (d) reach footer de-registered: internal "09f / 25_01"
                       pipeline reference and the "-581 mm not drawn here" note
                       removed (provenance belongs in the caption, not the figure).
    1.1.0  2026-07-18  Reach-panel seam continuity (Martin's render review): near-shore
                       retreat parabolas (storm / 5-yr / 20-yr) are now anchored at the
                       330 m cross-section boundary to the SAME committed 09f_01
                       drawdowns the inland side plots (previously schematic
                       MECH_FIG_RETREAT_HIN endpoints -> visible 1.4 px step on the
                       20-yr line); storm and 5-yr curves now CONTINUE inland to 900 m
                       from their committed CSV columns (previously stopped dead at
                       330 m). load_reach() gains c5_dd()/storm_dd() interpolators
                       (+ default-based fallbacks). The coastal GRID cell keeps its
                       schematic HIN anchors (no distance scale there). Continuity at
                       the seam is exact by construction and checked by Script 09g.
    1.0.0  2026-07-18  First pipeline version: dev generators consolidated, console
                       shim replaced by console_utils, ALL physical amplitudes
                       de-hardcoded to committed CSVs with pipeline_params
                       fallbacks, figure-design constants promoted to config.py
                       (MECH_FIG_*), reach fully derived from 09f_01 columns.
"""
from __future__ import annotations

__version__ = "1.6.6"

import numpy as np
import pandas as pd

from utils.console_utils import info, warn
from utils.pipeline_params import default_value
from utils.paths import OUT_09F_REACH_CSV, OUT_10M_REPORT, OUT_10A_REPORT
from utils.config import (
    MECHANISM_HORIZON_YEARS, COAST_CHRONIC_YEARS,
    MECH_FIG_PX_PER_MM, MECH_FIG_PROFILE_GX, MECH_FIG_PROFILE_GY,
    MECH_FIG_SLACK_CENTRES, MECH_FIG_RETREAT_SHORE, MECH_FIG_RETREAT_HIN,
    MECH_FIG_ERODE_LIGHTEN, MECH_FIG_SEA_LIGHTEN,
    MECH_FIG_INLAND_GROUND_PTS, MECH_FIG_INLAND_UND_PTS,
)

# ================================================================================================
# Shared schematic geometry (config-sourced) + canvas layout
# ================================================================================================
XC, XE = 110.0, 640.0            # cross-section x-extent (canvas px)
SEA = 250.0                      # sea level (canvas y)
# Font stack pins a glyph-complete sans first, so mathematical/Greek glyphs (delta,
# subscripts) can't fall back to a font that renders them as missing-glyph boxes.
# 'Liberation Sans' and 'DejaVu Sans' both cover delta, subscript digits, x and ~.
FONT_STACK = "'Liberation Sans','DejaVu Sans',sans-serif"
off, BASE = 300, 300             # two-panel after-offset, ground baseline (singles; grid rescales)
ORIG_SHORE = 110.0

gx, gy = MECH_FIG_PROFILE_GX, MECH_FIG_PROFILE_GY
def ground(x): return np.interp(x, gx, gy)
SLACK_C = list(MECH_FIG_SLACK_CENTRES)          # [257.0, 459.0] seaward, inland
X = np.linspace(XC, XE, 700)

SH  = dict(MECH_FIG_RETREAT_SHORE)              # coastal retreat: shoreline x per state
HIN = dict(MECH_FIG_RETREAT_HIN)                # coastal retreat: inland-head param per state
ERODE_LIGHTEN = dict(MECH_FIG_ERODE_LIGHTEN)
SEA_LIGHTEN   = dict(MECH_FIG_SEA_LIGHTEN)

# ==== palette ===================================================================================
DUNE = '#E8D9B5'                 # intact dune fill
SEA_BLUE = '#7FB2D9'             # sea fill
WT_BLUE = '#185FA5'              # water-table stroke
REF_GREY = '#6B7280'             # reference / no-change dotted
GHOST_BROWN = '#B48A50'          # ghost dune dashed
COL = {'storm': '#9b86bf', '5yr': '#6b3fa0', '20yr': '#3d1f66'}   # retreat-state strokes
COAST = '#3d1f66'; CLIMC = '#8a5a2b'; INK = '#26261f'
TAGCOL = {'accumulating': '#8a5a2b', 'settles': '#2b6a8a'}

def lighten(hexc, f):
    """blend a hex colour toward white by fraction f (0..1)."""
    r, g, b = int(hexc[1:3], 16), int(hexc[3:5], 16), int(hexc[5:7], 16)
    r, g, b = [int(v + (255 - v) * f) for v in (r, g, b)]
    return f'#{r:02X}{g:02X}{b:02X}'

# ================================================================================================
# Physical amplitudes — LIVE from committed CSVs, pipeline_params fallbacks
# ================================================================================================
# 09f-faithful vertical amplitude scale: PX_PER_MM (config) is reduced from the raw 09f
# scale so the largest amplitude just clips the schematic slack floors; the 09f RATIOS
# between mechanisms are preserved (that is what makes the four cells comparable).
PX_PER_MM = MECH_FIG_PX_PER_MM

def mm_px(mm):
    """magnitude in px on the shared cross-mechanism scale."""
    return abs(mm) * PX_PER_MM

_EDGE_FALLBACK_KEYS = {          # EDGE_DH_MM key -> pipeline_params._DEFAULTS key
    'forest_standing': 'mech_forest_standing_mm',
    'coastal_5yr':     'mech_coastal_5yr_mm',
    'scrape_cut_rise': 'mech_scrape_cut_rise_mm',
    'thinned':         'mech_thinned_mm',
    'climate_20yr':    'mech_climate_20yr_mm',
    'coastal_storm':   'mech_coastal_storm_mm',
    'scrape_offslack': 'wmc3_drawdown_mm',       # measured WMC3 off-cut (shared with 09f)
}
_09F_COLMAP = {                  # EDGE_DH_MM key -> 09f_01 column (row 0 = distance 0)
    'forest_standing': 'standing_pine_head_mm',
    'coastal_5yr':     'coastal_5yr_head_mm',
    'scrape_cut_rise': 'scrape_head_mm',
    'thinned':         'thinned_forest_head_mm',
    'climate_20yr':    'climate_20yr_head_mm',
    'coastal_storm':   'coastal_6m_storm_head_mm',
}

# initialised to documented first-pass defaults; load_amplitudes() resolves live values
EDGE_DH_MM = {k: float(default_value(v)) for k, v in _EDGE_FALLBACK_KEYS.items()}


def load_amplitudes():
    """Resolve EDGE_DH_MM from the committed CSVs (09f_01 row 0 + 10m WMC3).

    Falls back to pipeline_params defaults with a warning where a CSV is absent
    (partial/interrupted run — 09g normally runs after 09f in the same pass).
    Returns a copy of the resolved dict.
    """
    try:
        row0 = pd.read_csv(OUT_09F_REACH_CSV).iloc[0]
        for k, col in _09F_COLMAP.items():
            EDGE_DH_MM[k] = float(row0[col])
        info(f"edge amplitudes sourced from committed 09f ({OUT_09F_REACH_CSV.name} row 0)")
    except (FileNotFoundError, KeyError, IndexError) as e:
        warn(f"09f_01_reach_profile.csv unavailable ({e.__class__.__name__}) — mechanism "
             "amplitudes from first-pass defaults (run Script 09f for live values).")
    try:
        df = pd.read_csv(OUT_10M_REPORT)
        v = float(df.loc[df["Parameter"] == "WMC3_BACI_DiD_step_2015_scraping", "Value"].iloc[0])
        EDGE_DH_MM['scrape_offslack'] = v * 1000.0   # m -> mm
        info(f"scrape_offslack = {EDGE_DH_MM['scrape_offslack']:.1f} mm (measured WMC3 BACI, 10m)")
    except (FileNotFoundError, KeyError, IndexError):
        warn(f"10m_report_numbers.csv unavailable — scrape off-cut from default "
             f"{EDGE_DH_MM['scrape_offslack']:.1f} mm (measured WMC3; run Script 10m for live).")
    return dict(EDGE_DH_MM)


def load_reach():
    """Coastal-vs-climate reach quantities, fully derived from committed 09f_01 columns.

    Returns dict:
        coastal_dd(d) : 20-yr coastal drawdown (mm, +ve) =
                        (MECHANISM_HORIZON_YEARS / COAST_CHRONIC_YEARS) x |coastal_5yr(d)|
        c5_dd(d)      : 5-yr coastal drawdown (mm, +ve) = |coastal_5yr(d)|
        storm_dd(d)   : single 6 m storm drawdown (mm, +ve) = |coastal_6m_storm(d)|
        climate_mm    : flat 20-yr climate amplitude (mm, +ve) = |climate_20yr|
        crossing_m    : d where |coastal_5yr| == |climate_5yr| (horizon-free)
        source        : provenance string for the console check

    All three drawdown interpolators cover the full 0..900 m reach, so the drawn
    near-shore curves can be seam-anchored to the same values the inland
    continuation plots (exact continuity at the cross-section boundary).

    Fallback (CSV absent): reconstructed from the documented 25_01 fit defaults
    (delta_0, L, c via pipeline_params; storm amplitude from
    mech_coastal_storm_mm), with a warning.
    """
    n20 = MECHANISM_HORIZON_YEARS / COAST_CHRONIC_YEARS      # 4.0 on current config
    try:
        df = pd.read_csv(OUT_09F_REACH_CSV)
        d   = df['distance_m'].to_numpy(float)
        c5  = df['coastal_5yr_head_mm'].to_numpy(float)
        st  = df['coastal_6m_storm_head_mm'].to_numpy(float)
        cl5 = df['climate_5yr_head_mm'].to_numpy(float)
        climate_mm = abs(float(df['climate_20yr_head_mm'].iloc[0]))
        # Crossing at FULL precision. The committed coastal_5yr column is a linear
        # taper stored at 2 dp; interpolating the rounded column shifts the zero-
        # crossing ~1 m (reads 697 where the true line crossing is 698). Reconstruct
        # the taper from its own edge + reach length so 09g and 09f agree at 698.
        edge5 = abs(float(c5[0]))
        Lfit = float(d[np.max(np.where(np.abs(c5) > 0.0))]) if np.any(np.abs(c5) > 0) \
            else float(default_value('coast_reach_L_m'))
        rr = np.linspace(0.0, Lfit, 4001)
        taper = edge5 * (1.0 - rr / Lfit)
        dif = taper - abs(float(cl5[0]))
        xi = np.where(np.diff(np.sign(dif)))[0]
        if len(xi):
            i = xi[0]
            crossing = float(np.interp(0.0, [dif[i], dif[i + 1]], [rr[i], rr[i + 1]]))
        else:                                                # curves do not cross on-file
            L  = float(default_value('coast_reach_L_m'))
            d0 = abs(float(default_value('coast_delta0_mm_yr')))
            crossing = L * (1.0 - (climate_mm / MECHANISM_HORIZON_YEARS) / d0)
        def c5_dd(dd):
            return np.abs(np.interp(np.asarray(dd, float), d, c5))
        def storm_dd(dd):
            return np.abs(np.interp(np.asarray(dd, float), d, st))
        def coastal_dd(dd):
            return n20 * c5_dd(dd)
        return {'coastal_dd': coastal_dd, 'c5_dd': c5_dd, 'storm_dd': storm_dd,
                'climate_mm': climate_mm, 'crossing_m': crossing,
                'source': f"committed 09f ({OUT_09F_REACH_CSV.name})"}
    except (FileNotFoundError, KeyError, IndexError):
        L  = float(default_value('coast_reach_L_m'))
        d0 = abs(float(default_value('coast_delta0_mm_yr')))
        c  = abs(float(default_value('climate_c_mm_yr')))
        s0 = abs(float(default_value('mech_coastal_storm_mm')))
        climate_mm = c * MECHANISM_HORIZON_YEARS
        crossing = L * (1.0 - c / d0)
        def _ramp(dd, amp):
            dd = np.asarray(dd, float)
            return np.where(dd < L, amp * (1.0 - dd / L), 0.0)
        def c5_dd(dd):     return _ramp(dd, COAST_CHRONIC_YEARS * d0)
        def storm_dd(dd):  return _ramp(dd, s0)
        def coastal_dd(dd): return n20 * c5_dd(dd)
        warn(f"09f_01_reach_profile.csv unavailable — reach from documented defaults "
             f"(L={L:.0f} m, delta0={d0:.1f} mm/yr, climate={climate_mm:.0f} mm, "
             f"crossing={crossing:.0f} m; run Script 09f for live values).")
        return {'coastal_dd': coastal_dd, 'c5_dd': c5_dd, 'storm_dd': storm_dd,
                'climate_mm': climate_mm, 'crossing_m': crossing,
                'source': 'first-pass defaults (09f_01 absent)'}


def load_clearfell_steps():
    """Clearfell BACI steps for the grid magnitude line, live from 10a_report_numbers.csv.

    Returns (annual_m, annual_ptxt, summer_m, summer_ptxt): headline annual step
    (ANCOVA_Forest_Impact_clearfell_step) and the summer subset
    (..._clearfell_step_summer), with display-ready p strings ("p<0.001" / "n.s.").
    Fallback: documented defaults via pipeline_params, with a warning.
    """
    def _ptxt(note):
        # Note field carries e.g. "p=<0.001, CI=[...]" or "p=0.4363, CI=[...]"
        p = note.split("p=")[1].split(",")[0].strip()
        if p.startswith("<"):
            return f"p{p}"
        pv = float(p)
        return f"p={pv:.2f}" if pv < 0.05 else "n.s."
    try:
        df = pd.read_csv(OUT_10A_REPORT)
        key = df.iloc[:, 0].astype(str)
        r_a = df[key == "ANCOVA_Forest_Impact_clearfell_step"].iloc[0]
        r_s = df[key == "ANCOVA_Forest_Impact_clearfell_step_summer"].iloc[0]
        return (float(r_a["Value"]), _ptxt(str(r_a["Note"])),
                float(r_s["Value"]), _ptxt(str(r_s["Note"])))
    except (FileNotFoundError, KeyError, IndexError):
        a = default_value("clearfell_recovery_mm") / 1000.0
        s = default_value("clearfell_summer_step_mm") / 1000.0
        warn(f"10a_report_numbers.csv unavailable — clearfell steps from defaults "
             f"({a:+.3f} m p<0.001; {s:+.3f} m n.s.; run Script 10a for live values).")
        return a, "p<0.001", s, "n.s."


# ================================================================================================
# Chained short-Dupuit-segment solver (LOCKED on the coastal figure — edit here only)
# ================================================================================================
SEG2_START_NUDGE_PX = 5.0        # before-panel seg-2 inland nudge (coastal FIX 1)

def grandf(shore, Hg):
    """grand Dupuit parabola anchored at sea level at the (retreated) shoreline."""
    return lambda x: (lambda xx: np.where(
        xx >= shore, SEA - Hg * np.sqrt(np.clip((xx - shore) / (XE - shore), 0, 1)), SEA))(
        np.asarray(x, float))

def g1(x): return float(ground(np.array([x]))[0])

def wateredges(c, L):
    """seaward/landward waterlines: walk out from slack centre c until ground rises above L."""
    xl = c
    while xl > XC and g1(xl - 0.5) > L + 0.15: xl -= 0.5
    xr = c
    while xr < XE and g1(xr + 0.5) > L + 0.15: xr += 0.5
    return xl, xr

def segmented(shore, Hg, graze_floor_seaward=False, nudge_seg2=False):
    """Chained short Dupuit segments through FLOODED slacks only.
    Returns (table_y_over_X, steps) with steps = [(xl, xr, level, is_pond), ...]."""
    G = grandf(shore, Hg)
    y = G(X).copy()
    steps = []
    for si, c in enumerate(SLACK_C):
        floorc = g1(c)
        L = float(G(np.array([max(shore, c - 42)]))[0])
        is_seaward = (si == 0)
        if graze_floor_seaward and is_seaward:
            Lf = floorc
            xl = c
            while xl > shore and float(G(np.array([xl - 0.5]))[0]) < Lf: xl -= 0.5
            xr = c
            while xr < XE and abs(g1(xr + 0.5) - floorc) < 0.5: xr += 0.5
            steps.append((xl, xr, Lf, False))
        elif floorc > L + 1.0:
            xl, xr = wateredges(c, L)
            steps.append((xl, xr, L, True))
    for i, (xl, xr, L, is_pond) in enumerate(steps):
        nudge = SEG2_START_NUDGE_PX if (nudge_seg2 and i == 0 and is_pond) else 0.0
        seg_start = xr + nudge
        flat_end = seg_start if nudge else xr
        m = (X >= xl) & (X <= flat_end); y[m] = L
        nxL = steps[i + 1][0] if i + 1 < len(steps) else XE
        nyL = steps[i + 1][2] if i + 1 < len(steps) else float(G(np.array([XE]))[0])
        m2 = (X > seg_start) & (X <= nxL)
        if nxL > seg_start:
            y[m2] = L - (L - nyL) * np.sqrt(np.clip((X[m2] - seg_start) / (nxL - seg_start), 0, 1))
    return y, steps

def dupuit_segment(x0, y0, x1, y1):
    """fresh short Dupuit parabola from fixed head (x0,y0) to (x1,y1) over X (NaN elsewhere)."""
    out = np.full_like(X, np.nan)
    m = (X >= x0) & (X <= x1)
    if x1 > x0:
        out[m] = y0 - (y0 - y1) * np.sqrt(np.clip((X[m] - x0) / (x1 - x0), 0, 1))
    return out

# ================================================================================================
# SVG helpers
# ================================================================================================
def Pth(xs, ys): return "M " + " L ".join(f"{a:.1f},{b:.1f}" for a, b in zip(xs, ys))

def water(gf, wy, yoff, xmin, skip_spans=()):
    """fill where ground dips below the table (standing water)."""
    g = gf(X); fl = (g > wy + 0.2) & (X >= xmin)
    for (a, b) in skip_spans:
        fl &= ~((X >= a - 1) & (X <= b + 1))
    out = []; i = 0; n = len(X)
    while i < n:
        if fl[i]:
            j = i
            while j < n and fl[j]: j += 1
            seg = range(i, j)
            out.append('<polygon points="' +
                       " ".join(f"{X[k]:.1f},{wy[k]+yoff:.1f}" for k in seg) + " " +
                       " ".join(f"{X[k]:.1f},{g[k]+yoff:.1f}" for k in reversed(seg)) +
                       '" fill="#7FB2D9"/>'); i = j
        else:
            i += 1
    return "".join(out)

def sea(y, x1): return (f'<polygon points="40,{y:.0f} {x1:.0f},{y:.0f} {x1:.0f},{y+40:.0f} 40,{y+40:.0f}" '
                        f'fill="#7FB2D9"/><line x1="40" y1="{y:.0f}" x2="{x1:.0f}" y2="{y:.0f}" '
                        f'stroke="#3B8BD4" stroke-width="1"/>')

def lbl(x, y, s, b=False, a='start', col=None):
    w = len(s) * 6.2 + 10; x0 = x - 5 if a == 'start' else (x - w + 5 if a == 'end' else x - w / 2)
    c = col if col else ("#26261f" if b else "#5f5e5a")
    return (f'<rect x="{x0:.0f}" y="{y-12:.0f}" width="{w:.0f}" height="17" rx="3" fill="#fff" opacity="0.9"/>'
            f'<text x="{x:.0f}" y="{y:.0f}" font-family="{FONT_STACK}" font-size="12" '
            f'font-weight="{"600" if b else "400"}" fill="{c}" text-anchor="{a}">{s}</text>')

def ld(x1, y1, x2, y2): return (f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                                f'stroke="#9a988f" stroke-width="0.7" stroke-dasharray="3 3"/>')

def tick(x, yb): return (f'<line x1="{x:.0f}" y1="{yb-5:.0f}" x2="{x:.0f}" y2="{yb+5:.0f}" '
                         f'stroke="#3B8BD4" stroke-width="1.4"/>')

def txt(x, y, s, size=12, w='400', col='#26261f', anchor='start', style='', escape=True):
    if escape:
        s = str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT_STACK}" font-size="{size}" '
            f'font-weight="{w}" fill="{col}" text-anchor="{anchor}"{style}>{s}</text>')

# ================================================================================================
# FOREST / CLEARFELL cell (from gen_forest v0.1.0)
# ================================================================================================
# figure-design geometry (schematic drawing coordinates, not physical parameters)
FOREST_START = 300.0             # trees landward of here; bare coast seaward
FOREST_RAMP  = 40.0              # suppression ramps in over this length
FELL_L, FELL_R = 415.0, 505.0    # felled span (upper/inland slack 440-478 + margins)
FELL_RAMP    = 24.0              # recovery tapers over this length at the felled edges
TREE_STEP    = 21.0

def _ramp(x, a, b): return np.clip((x - a) / (b - a), 0.0, 1.0)          # 0 at a -> 1 at b
def _trap(x, L, R, r):                                                   # 1 in [L,R], ramps over r
    return np.minimum(_ramp(x, L - r, L), _ramp(-x, -(R + r), -R))

def forest_build_tables():
    """(wt_notree, wt_forest, wt_fell): no-tree reference (both slacks wet), forest-suppressed
    (-EDGE_DH_MM['forest_standing'] on the shared scale), and clearfell-recovered tables."""
    suppress_px = mm_px(EDGE_DH_MM['forest_standing'])
    wt_notree = segmented(110.0, 78.0, nudge_seg2=True)[0]
    supp = suppress_px * _ramp(X, FOREST_START, FOREST_START + FOREST_RAMP)
    wt_forest = wt_notree + supp
    rec = _trap(X, FELL_L, FELL_R, FELL_RAMP)
    wt_fell = wt_notree + supp * (1.0 - rec)
    return wt_notree, wt_forest, wt_fell

def _pine(x, ygnd, yoff):
    b = ygnd + yoff
    return (f'<line x1="{x:.0f}" y1="{b:.0f}" x2="{x:.0f}" y2="{b-5:.0f}" stroke="#6B4A2B" stroke-width="1.6"/>'
            f'<polygon points="{x-7:.0f},{b-5:.0f} {x+7:.0f},{b-5:.0f} {x:.0f},{b-16:.0f}" fill="#2E7D32"/>'
            f'<polygon points="{x-6:.0f},{b-11:.0f} {x+6:.0f},{b-11:.0f} {x:.0f},{b-21:.0f}" fill="#357E38"/>')

def forest_trees(yoff, felled=False):
    out = []
    for x in np.arange(FOREST_START + 8, XE - 2, TREE_STEP):
        if felled and (FELL_L <= x <= FELL_R):   # canopy gap over the felled slack
            continue
        out.append(_pine(float(x), g1(float(x)), yoff))
    return "".join(out)

# ================================================================================================
# DUNE SCRAPE cell (from gen_scrape v0.3.0)
# ================================================================================================
# Mechanism (corrected, SCRAPING_EFFECTS_KNOWLEDGE.md): the phreatic surface does NOT move on
# excavation — the cut meets the water table and becomes a pool. The measured, robust effects:
# a RISE at the cut (+129 mm, CEH36 BACI vs CEH4 — the headward cut reaches ground where the
# regional inland-rising head is naturally HIGHER, not an excavation lift) and the MEASURED
# WMC3 near-field off-cut drawdown (-55 mm 2015 / -54 mm 2023, reproducible BACI DiD). There
# is NO evidenced network-wide drawdown cone; the off-cut signal is localised near-field only.
CUT_SEAWARD  = 204.0             # seaward edge of the excavated floor
CUT_HEADWARD = 335.0             # bite into the LANDWARD EDGE of the seaward slack
CUT_FLOOR    = 221.0             # excavated floor (below pool level -> shallow wet pool)
OFFCUT_C     = 445.0             # centre of the near-field drawdown (around the inland slack)
OFFCUT_W     = 88.0              # width of the localised drawdown (NOT a network-wide cone)
POOL_RISE_PX = 3.5               # marginal, illustrative within-slack rise (measured value in label)

_scrape_gx = [110, 138, 170, 200, CUT_SEAWARD, CUT_HEADWARD, 370, 400, 440, 478, 520, 640]

def _scrape_gy():
    inland_floor = g1(SLACK_C[1])
    return [250, 200, 210, 210, CUT_FLOOR, CUT_FLOOR, 182, 196, inland_floor, inland_floor, 178, 160]

def scrape_ground(x): return np.interp(x, _scrape_gx, _scrape_gy())
def _sg1(x): return float(scrape_ground(np.array([x]))[0])

def scrape_pool_level():
    """pool = marginally higher than the seaward-slack level (headward cut reaches the
    inland-higher head; measured +129 mm at CEH36). Drawn rise CAPPED within the slack
    (below the seaward spill rim) on the exaggerated scale; measured value lives in labels."""
    before = segmented(110.0, 78.0, nudge_seg2=True)[0]
    seaward_lvl = float(np.interp(SLACK_C[0], X, before))
    seaward_rim = float(g1(206.0))                 # foredune back-shelf = seaward spill rim
    return max(seaward_lvl - POOL_RISE_PX, seaward_rim + 1.0)

def scrape_build_after_table():
    """After scraping: pool at the (marginally higher) fixed head across the submerged cut;
    off the cut, the MEASURED WMC3 near-field drawdown (localised, tapering) brings the
    inland slack toward — not below — its floor. Returns (wt, (pool_l, pool_r))."""
    y = segmented(110.0, 78.0, nudge_seg2=True)[0].copy()
    offcut_px = mm_px(EDGE_DH_MM['scrape_offslack'])
    dd = offcut_px * np.exp(-((X - OFFCUT_C) / OFFCUT_W) ** 2)
    dd[X < CUT_HEADWARD] = 0.0
    y = y + dd
    pool = scrape_pool_level()
    xl = SLACK_C[0]
    while xl > 110 and _sg1(xl - 0.5) > pool: xl -= 0.5
    xr = CUT_HEADWARD
    while xr < XE and _sg1(xr + 0.5) > pool: xr += 0.5
    m = (X >= xl) & (X <= xr); y[m] = pool
    return y, (xl, xr)

# ================================================================================================
# CLIMATE cell (from gen_climate v0.2.0)
# ================================================================================================
PIN_A, PIN_B = 160.0, 215.0      # drop ramps 0 (sea pin) -> full over the fore dune

def climate_build_after_table(wt_before, px_per_mm=None):
    """Lower the CONTINUOUS grand Dupuit curve by the spatially-uniform 20-yr climate
    amplitude (ramped from the sea pin so the shore stays at sea level). The table only
    STEPS to a flat pond where the lowered curve still meets the surface; at c x 20 yr
    (-127 mm) both slacks are dry. Returns (wt, drop, ponds=[(xl, xr, level), ...]).
    `px_per_mm` overrides the global mm scale (for the reach figure's local scale)."""
    _pxmm = mm_px if px_per_mm is None else (lambda mm: abs(mm) * px_per_mm)
    drop_px = _pxmm(EDGE_DH_MM['climate_20yr'])
    drop = drop_px * _ramp(X, PIN_A, PIN_B)
    # Lower the ACTUAL undisturbed table (wt_before, which already carries the correct
    # near-shore slack ponds) by the ramped climate drop — not a fresh smooth parabola,
    # which at a small drop would sit above the slack floors and clamp into one long flat
    # pond (the "flat climate curve" bug). Re-pond only where the lowered table still
    # floods a slack.
    wt = np.asarray(wt_before, float).copy() + drop
    ponds = []
    for c in SLACK_C:
        floor = g1(c)
        lvl = float(np.interp(c, X, wt))
        if lvl < floor - 0.5:                        # head above floor => flooded
            xl, xr = wateredges(c, lvl)
            m = (X >= xl) & (X <= xr); wt[m] = lvl
            ponds.append((xl, xr, lvl))
    return wt, drop, ponds

def climate_fill_ponds(gf, wt, yoff, ponds):
    """standing-water polygons for genuinely-flooded spans only (NOT generic ground>table
    fill, which would paint a spurious sliver where the dry curve grazes a floor edge)."""
    out = []
    for (xl, xr, lvl) in ponds:
        m = (X >= xl) & (X <= xr); xs = X[m]; g = gf(xs)
        out.append('<polygon points="' + " ".join(f"{x:.1f},{lvl+yoff:.1f}" for x in xs) + " " +
                   " ".join(f"{x:.1f},{gv+yoff:.1f}" for x, gv in zip(reversed(xs), reversed(g))) +
                   '" fill="#7FB2D9"/>')
    return "".join(out)

# ================================================================================================
# Cell geometry builders (from gen_grid v0.8.0; native panel coords, no text)
# ================================================================================================
def _topline(gf):   return f'<path d="{Pth(X, gf(X))}" fill="none" stroke="#C4A867" stroke-width="1"/>'
def _dunefill(gf):  return f'<path d="{Pth(X, gf(X))} L640,{BASE} L110,{BASE} Z" fill="{DUNE}"/>'
def _wt(wy, col=WT_BLUE, w=2.4): return (f'<path d="{Pth(X, wy)}" fill="none" stroke="{col}" '
                                         f'stroke-width="{w}" stroke-linecap="round"/>')
def _refline(wy):   return (f'<path d="{Pth(X, wy)}" fill="none" stroke="{REF_GREY}" '
                            f'stroke-width="1.4" stroke-dasharray="2 3"/>')

def geo_wet_before():
    """undisturbed 'before' — coastal / scrape / climate share this starting state."""
    wt = segmented(110.0, 78.0, nudge_seg2=True)[0]
    return sea(250, 110) + _dunefill(ground) + water(ground, wt, 0, 110) + _topline(ground) + _wt(wt)

def geo_coastal_after():
    """ghost sea + eroded-dune ghosts + intact dune + storm fill + 3 retreat curves."""
    wt_before = segmented(110.0, 78.0, nudge_seg2=True)[0]
    wt_storm, steps_s = segmented(SH['storm'], HIN['storm'], graze_floor_seaward=True)
    wt_5yr  = grandf(SH['5yr'],  HIN['5yr'])(X)
    wt_20yr = grandf(SH['20yr'], HIN['20yr'])(X)
    rz = [(ORIG_SHORE, SH['storm'], 'storm'), (SH['storm'], SH['5yr'], '5yr'),
          (SH['5yr'], SH['20yr'], '20yr')]
    SEALV = 250.0
    p = [sea(250, int(ORIG_SHORE))]
    for (xa, xb, k) in rz:   # ghost sea across retreat zone (progressive shore retreat)
        p.append(f'<rect x="{xa:.1f}" y="{SEALV:.1f}" width="{xb-xa:.1f}" height="40" '
                 f'fill="{lighten(SEA_BLUE, SEA_LIGHTEN[k])}"/>')
    for (xa, xb, k) in rz:   # eroded-dune ghost (lighter more seaward)
        xs = X[(X >= xa) & (X <= xb)]
        p.append(f'<path d="{Pth(xs, ground(xs))} L{xb:.1f},{SEALV:.1f} L{xa:.1f},{SEALV:.1f} Z" '
                 f'fill="{lighten(DUNE, ERODE_LIGHTEN[k])}"/>')
    xs_i = X[X >= SH['20yr']]   # intact dune landward of the 20 yr shoreline
    p.append(f'<path d="{Pth(xs_i, ground(xs_i))} L640,{BASE} L{SH["20yr"]:.1f},{BASE} Z" fill="{DUNE}"/>')
    skip = [(a, b) for (a, b, L, is_pond) in steps_s if not is_pond]
    p.append(water(ground, wt_storm, 0, SH['20yr'], skip_spans=skip))
    p.append(f'<path d="{Pth(X[X>=ORIG_SHORE], ground(X[X>=ORIG_SHORE]))}" fill="none" '
             f'stroke="#C4A867" stroke-width="1"/>')
    p.append(_refline(wt_before))
    for k, wy in [('storm', wt_storm), ('5yr', wt_5yr), ('20yr', wt_20yr)]:
        m = X >= SH[k]; lw = {'storm': 1.8, '5yr': 2.3, '20yr': 2.8}[k]
        p.append(f'<line x1="{SH[k]:.0f}" y1="245" x2="{SH[k]:.0f}" y2="255" '
                 f'stroke="#3B8BD4" stroke-width="1.4"/>')
        p.append(f'<path d="{Pth(X[m], wy[m])}" fill="none" stroke="{COL[k]}" '
                 f'stroke-width="{lw}" stroke-linecap="round"/>')
    p.append(f'<line x1="120" y1="278" x2="{SH["20yr"]-2:.0f}" y2="278" '
             f'stroke="#712B13" stroke-width="1.5"/>')  # retreat cue bar
    return "".join(p)

def geo_scrape_after():
    """pool at the (marginally higher) fixed head, headward cut, measured WMC3 off-cut."""
    wt_before = segmented(110.0, 78.0, nudge_seg2=True)[0]
    wt_after, _ = scrape_build_after_table()
    return (sea(250, 110)
            + f'<path d="{Pth(X, scrape_ground(X))} L640,{BASE} L110,{BASE} Z" fill="{DUNE}"/>'
            + water(scrape_ground, wt_after, 0, 110) + _topline(scrape_ground)
            + _refline(wt_before) + _wt(wt_after))

def geo_forest(felled):
    """standing forest (felled=False) or after clearfell of the upper slack (felled=True)."""
    wt_notree, wt_forest, wt_fell = forest_build_tables()
    wt = wt_fell if felled else wt_forest
    return (sea(250, 110) + _dunefill(ground) + water(ground, wt, 0, 110) + _topline(ground)
            + forest_trees(0, felled=felled) + _refline(wt_notree) + _wt(wt))

def geo_climate_after():
    """whole table lowered uniformly (continuous Dupuit; ponds only where it meets the
    surface) — at the 20-yr amplitude both slacks dry, no flat pond steps."""
    wt_before = segmented(110.0, 78.0, nudge_seg2=True)[0]
    wt_after, _, ponds = climate_build_after_table(wt_before)
    return (sea(250, 110) + _dunefill(ground) + climate_fill_ponds(ground, wt_after, 0, ponds)
            + _topline(ground) + _refline(wt_before) + _wt(wt_after))

# native content box (x0, y0, x1, y1) of a cell geometry; includes tree tops
NATIVE = (40.0, 134.0, 640.0, 302.0)

def place(geo, ix, iy, iw, ih):
    """drop native-coordinate cell geometry into a grid cell via an SVG transform."""
    nx0, ny0, nx1, ny1 = NATIVE
    nw, nh = nx1 - nx0, ny1 - ny0
    S = min(iw / nw, ih / nh)
    dw, dh = nw * S, nh * S
    cx, cy = ix + (iw - dw) / 2, iy + (ih - dh) / 2
    TX, TY = cx - S * nx0, cy - S * ny0
    return f'<g transform="translate({TX:.2f},{TY:.2f}) scale({S:.4f})">{geo}</g>'

# ================================================================================================
# Coastal-vs-climate REACH body (from gen_reach_discont v0.5.0; continuous 900 m scale)
# ================================================================================================
REACH_W, REACH_H = 920, 384      # native reach-panel size
_R_NL = 34                       # reach left margin
_R_DN = 330.0                    # near-shore cross-section spans 0..330 m of the reach scale
_R_PXM = (REACH_W - _R_NL - 20) / 900.0      # px per metre over the continuous 0..900 m

def _r_ix(d): return _R_NL + d * _R_PXM                       # distance (m) -> canvas x
def _r_nx(sx): return _r_ix((sx - 110.0) / 530.0 * _R_DN)     # near-shore shared x -> canvas x

_IN_GD = list(zip(*MECH_FIG_INLAND_GROUND_PTS))               # ([d...], [y...])
_IN_UD = list(zip(*MECH_FIG_INLAND_UND_PTS))

def _r_ground_in(d): return np.interp(d, _IN_GD[0], _IN_GD[1])
def _r_und_in(d):    return np.interp(d, _IN_UD[0], _IN_UD[1])

def _flat_pond(dd, surf, grd):
    """Draw a water surface `surf` (y over dd, y-down canvas) as flat ponds like the
    near-shore slacks (segmented()): wherever the surface stands above the ground `grd`
    (a slack floods), a FLAT pond sits at the seaward-rim level across the truly flooded
    width — the part where the ground floor is actually below the pond level — and the
    regional table then rises out of the pond up the landward flank via a smoothstep
    (zero slope at both ends, so the flat->rise join has no kink). Landward of the pond,
    and everywhere the surface is below ground, the smooth surface is kept unchanged.

    Called PER CURVE: the undisturbed reference floods where the undisturbed table does,
    the coastal curve only where the drawn-down coastal surface still floods (so it stays
    smooth once coastal drawdown has recovered inland), and the climate curve only where
    it floods (which, drawn below every inland floor, is nowhere — so climate stays a
    smooth declining line). Returns y for array dd."""
    dd = np.asarray(dd, float)
    surf = np.asarray(surf, float)
    grd = np.asarray(grd, float)
    wet = surf < grd                                   # surface above the slack floor (a pond)
    out = surf.copy(); n = len(dd); i = 0
    while i < n:
        if wet[i]:
            j = i
            while j < n and wet[j]:
                j += 1
            L = surf[i - 1] if i > 0 else surf[i]          # pond level = seaward rim (outlet)
            k = i
            while k < j and grd[k] > L:                    # flooded width: ground below pond level
                k += 1
            out[i:k] = L                                    # flat pond across the flooded width
            if k < j:                                       # shallow landward tail: rise out of pond
                landward = surf[j] if j < n else surf[j - 1]
                d0, d1 = dd[k], dd[j - 1]
                m = (dd >= d0) & (dd <= d1)
                f = np.clip((dd[m] - d0) / max(d1 - d0, 1e-6), 0, 1)
                out[m] = L - (L - landward) * (f * f * (3.0 - 2.0 * f))   # smoothstep, no kink
            i = j
        else:
            i += 1
    return out

def _r_und_flat(dd):
    """Undisturbed inland reference on the flat-pond base (thin wrapper over _flat_pond)."""
    dd = np.asarray(dd, float)
    return _flat_pond(dd, _r_und_in(dd), _r_ground_in(dd))

def _r_txt(x, y, s, sz=12, w='400', c=INK, a='start', it=False):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT_STACK}" font-size="{sz}" '
            f'font-weight="{w}" fill="{c}" text-anchor="{a}"'
            f'{" font-style=\"italic\"" if it else ""}>{s}</text>')

def _reach_base(s, pth, draw_erosion):
    """Shared reach profile — sea, dune, near-shore cross-section (0..330 m) joined to
    the inland ground (330..900 m) — drawn identically for the technical figure and
    the lay stack. `draw_erosion` toggles the retreat-ghost fore-dune (on for coastal,
    off for the plain undisturbed / climate panels). Returns the undisturbed water
    table array `_und` for callers that overlay drivers."""
    _und = segmented(110.0, 78.0, nudge_seg2=True)[0]
    SEALV = 250.0
    xs = [_r_nx(x) for x in X]
    rz = [(ORIG_SHORE, SH['storm'], 'storm'), (SH['storm'], SH['5yr'], '5yr'),
          (SH['5yr'], SH['20yr'], '20yr')]
    # sea block
    s.append(f'<polygon points="{_r_nx(40):.0f},{SEALV:.0f} {_r_nx(110):.0f},{SEALV:.0f} '
             f'{_r_nx(110):.0f},{SEALV+40:.0f} {_r_nx(40):.0f},{SEALV+40:.0f}" fill="{SEA_BLUE}"/>')
    if draw_erosion:
        for (xa, xb, k) in rz:
            s.append(f'<rect x="{_r_nx(xa):.1f}" y="{SEALV:.1f}" width="{_r_nx(xb)-_r_nx(xa):.1f}" '
                     f'height="40" fill="{lighten(SEA_BLUE, SEA_LIGHTEN[k])}"/>')
        for (xa, xb, k) in rz:
            xseg = X[(X >= xa) & (X <= xb)]
            s.append(f'<path d="{pth([_r_nx(x) for x in xseg], [ground(x) for x in xseg])} '
                     f'L{_r_nx(xb):.1f},{SEALV:.1f} L{_r_nx(xa):.1f},{SEALV:.1f} Z" '
                     f'fill="{lighten(DUNE, ERODE_LIGHTEN[k])}"/>')
        xstart = SH['20yr']
    else:
        xstart = ORIG_SHORE
    # intact dune (near-shore cross-section)
    xsi = X[X >= xstart]
    s.append(f'<path d="{pth([_r_nx(x) for x in xsi], [ground(x) for x in xsi])} '
             f'L{_r_nx(640):.1f},{BASE} L{_r_nx(xstart):.1f},{BASE} Z" fill="{DUNE}"/>')
    s.append(f'<path d="{pth([_r_nx(x) for x in xsi], [ground(x) for x in xsi])}" '
             f'fill="none" stroke="#C4A867" stroke-width="1"/>')
    # inland ground (330..900 m)
    di = np.linspace(_R_DN, 900, 240); gxi = [_r_ix(d) for d in di]
    s.append(f'<path d="{pth(gxi, [_r_ground_in(d) for d in di])} L{_r_ix(900):.1f},{BASE} '
             f'L{_r_ix(_R_DN):.1f},{BASE} Z" fill="{DUNE}"/>')
    s.append(f'<path d="{pth(gxi, [_r_ground_in(d) for d in di])}" fill="none" '
             f'stroke="#C4A867" stroke-width="1"/>')
    return _und, di, gxi


def _reach_ponds(wt, pth):
    """Blue pond fill for the near-shore slacks in REACH coordinates: fill where the
    ground dips below the water-table array `wt` (shared X), mapped through _r_nx.
    Mirrors water() but in the reach's mapped x-space so the lay/technical reach
    panels show standing water in the flooded slacks, not just a line."""
    g = ground(X)
    fl = g > wt + 0.2
    out = []
    i, n = 0, len(X)
    while i < n:
        if fl[i]:
            j = i
            while j < n and fl[j]:
                j += 1
            seg = range(i, j)
            top = [(_r_nx(X[k]), wt[k]) for k in seg]
            bot = [(_r_nx(X[k]), g[k]) for k in reversed(seg)]
            pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in top + bot)
            out.append(f'<polygon points="{pts}" fill="{SEA_BLUE}"/>')
            i = j
        else:
            i += 1
    return "".join(out)


def build_reach_panel(reach, driver, title=None, show_axis=True, show_crossing_note=False,
                      register="technical"):
    """A single-driver reach panel on the shared profile, full 0..900 m. `driver` is
    one of 'undisturbed', 'coastal', 'climate'. Used by the lay stacked figure so the
    lay panels share the technical figure's exact profile and amplitudes; only one
    driver line is drawn per panel. `register` toggles technical-only annotation (the
    storm/5yr/20yr retreat-band labels on the coastal panel). Returns the panel body
    SVG (no wrapper)."""
    coastal_dd, CLIM, CROSS = reach['coastal_dd'], reach['climate_mm'], reach['crossing_m']
    def pth(xs, ys): return "M " + " L ".join(f"{a:.1f},{b:.1f}" for a, b in zip(xs, ys))
    s = []
    if title:
        s.append(_r_txt(_R_NL, 20, title, 13, '600'))
    _und, di, gxi = _reach_base(s, pth, draw_erosion=(driver == 'coastal'))
    _und_raw = _r_und_in(di); _grd = _r_ground_in(di)         # per-curve flood base
    def _pond_g(off_fn):                                       # flat-pond flatten of und + offset(mm)
        surf = _und_raw + np.array([mm_px(off_fn(d)) for d in di], float)
        return _flat_pond(di, surf, _grd)
    _undf = _flat_pond(di, _und_raw, _grd)                     # reference: floods where und does
    xs = [_r_nx(x) for x in X]

    # pond fill in the near-shore slacks (undisturbed / climate share the wet 'before';
    # coastal near-shore is eroded, so its ponds are subsumed by the retreat ghosting)
    if driver == 'undisturbed':
        s.append(_reach_ponds(_und, pth))
    elif driver == 'climate':
        _clm = climate_build_after_table(_und)[0]
        s.append(_reach_ponds(_clm, pth))

    # undisturbed reference — dashed grey, on every panel
    s.append(f'<path d="{pth(xs, list(_und))}" fill="none" stroke="{REF_GREY}" '
             f'stroke-width="1.3" stroke-dasharray="2 3"/>')
    s.append(f'<path d="{pth(gxi, list(_undf))}" fill="none" stroke="{REF_GREY}" '
             f'stroke-width="1.3" stroke-dasharray="2 3"/>')

    if driver == 'coastal':
        # 20-yr coastal drawdown: near-shore parabola seam-anchored, inland continuation
        _und_seam = float(np.interp(XE, X, _und))
        hg = SEA - (_und_seam + mm_px(coastal_dd(_R_DN)))
        wt = grandf(SH['20yr'], hg)(X); m = X >= SH['20yr']
        s.append(f'<path d="{pth([_r_nx(x) for x in X[m]], [v for v in wt[m]])}" '
                 f'fill="none" stroke="{COAST}" stroke-width="2.6"/>')
        s.append(f'<path d="{pth(gxi, list(_pond_g(coastal_dd)))}" '
                 f'fill="none" stroke="{COAST}" stroke-width="2.6"/>')
        s.append(_r_txt(_r_nx(120), BASE - 46, 'sea', 10, c='#5f5e5a'))
        if register == "technical":
            # label each retreat band under its own ghost shade, in the state's colour
            _prev = ORIG_SHORE
            for k, lab in (('storm', 'storm'), ('5yr', '5 yr'), ('20yr', '20 yr')):
                xmid = (_r_nx(_prev) + _r_nx(SH[k])) / 2
                s.append(_r_txt(xmid, BASE + 2, lab, 8, '600', c=COL[k], a='middle'))
                _prev = SH[k]
    elif driver == 'climate':
        _clm = climate_build_after_table(_und)[0]
        s.append(f'<path d="{pth(xs, list(_clm))}" fill="none" stroke="{CLIMC}" '
                 f'stroke-width="2.4" stroke-dasharray="7 3"/>')
        s.append(f'<path d="{pth(gxi, list(_pond_g(lambda d: CLIM)))}" fill="none" '
                 f'stroke="{CLIMC}" stroke-width="2.4" stroke-dasharray="7 3"/>')
        s.append(_r_txt(_r_nx(120), BASE - 46, 'sea', 10, c='#5f5e5a'))
    else:  # undisturbed — draw the wet table line so the ponds read as water, not gaps
        s.append(f'<path d="{pth(xs, list(_und))}" fill="none" stroke="{WT_BLUE}" '
                 f'stroke-width="2.0"/>')
        s.append(_r_txt(_r_nx(120), BASE - 46, 'sea', 10, c='#5f5e5a'))

    if show_crossing_note:
        xc = _r_ix(CROSS)
        s.append(f'<line x1="{xc:.0f}" y1="24" x2="{xc:.0f}" y2="{BASE:.0f}" stroke="#444" '
                 f'stroke-width="1" stroke-dasharray="2 3"/>')
        s.append(_r_txt(xc, 18, f'about {CROSS:.0f} m', 9, '600', c='#444', a='middle'))

    if show_axis:
        for d in (0, 150, 300, 450, 600, 750, 900):
            s.append(_r_txt(_r_ix(d), BASE + 16, f'{d:.0f}' + (' m' if d == 900 else ''), 9,
                            c='#888', a='middle'))
    return "".join(s)


def build_reach_stack(reach, register="technical"):
    """Stacked coastal-vs-climate reach: three panels (undisturbed / coastal / climate)
    on the SHARED profile, full 0..900 m, vertically aligned on one distance axis with
    the crossing marked. `register` is 'technical' (mm amplitudes, precise labels) or
    'lay' (plain language). Used by Script 09g (technical) and gen_grid_lay (lay), so
    both registers share one geometry. Returns a complete <svg> string."""
    CLIM, CROSS = reach['climate_mm'], reach['crossing_m']
    coastal_dd = reach['coastal_dd']
    shore_mm = coastal_dd(0.0)
    lay = (register == "lay")

    PW = REACH_W
    CROP_TOP, CROP_BOT = 96, int(BASE) + 24
    BAND = CROP_BOT - CROP_TOP
    HDR = 52
    TITLE_H = 18
    GAP = 10
    W = PW
    ROW = TITLE_H + BAND
    H = HDR + 3 * ROW + 2 * GAP + 30

    if lay:
        head = "What coast and climate do to the water table"
        sub = ("one long slice from the shore inland, on the same scale - "
               "simple diagram, not to scale")
        titles = {
            'undisturbed': "Undisturbed dune (the starting point)",
            'coastal': "With coastal retreat - deepest near the shore, fading inland",
            'climate': "With climate drying - the same fall across the whole site",
        }
        foot = ("Climate is the biggest change overall because it lowers the whole "
                "site; the sea's retreat bites hardest near the shore and fades by "
                f"about {CROSS:.0f} m inland.")
    else:
        head = "Coastal retreat vs climate along the reach (stacked)"
        sub = (f"undisturbed / coastal / climate on one continuous 900 m scale \u00b7 "
               f"shared amplitude scale \u00b7 crossing at ~{CROSS:.0f} m")
        titles = {
            'undisturbed': "Undisturbed water table",
            'coastal': f"Coastal retreat: -{shore_mm:.0f} mm at shore over 20 yr, "
                       f"tapering to 0 by ~894 m (\u03b4\u2080 -29 mm/yr)",
            'climate': f"Climate: uniform -{CLIM:.0f} mm over 20 yr (c -6.35 mm/yr)",
        }
        foot = (f"Coastal is deeper shoreward of ~{CROSS:.0f} m; climate (uniform "
                f"-{CLIM:.0f} mm) is deeper inland and carries the larger site-wide mean.")

    s = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'xmlns="http://www.w3.org/2000/svg"><rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(_r_txt(_R_NL, 26, head, 16, '600'))
    s.append(_r_txt(_R_NL, 43, sub, 11, c='#888780'))

    order = [('undisturbed', False), ('coastal', True), ('climate', True)]
    for i, (driver, mark) in enumerate(order):
        row_top = HDR + i * (ROW + GAP)
        s.append(_r_txt(_R_NL, row_top + 13, titles[driver], 12, '600'))
        if mark:
            xc = _r_ix(CROSS)
            s.append(f'<line x1="{xc:.0f}" y1="{row_top + TITLE_H:.0f}" x2="{xc:.0f}" '
                     f'y2="{row_top + TITLE_H + BAND:.0f}" stroke="#444" stroke-width="1" '
                     f'stroke-dasharray="2 3"/>')
            s.append(_r_txt(xc, row_top + 12, f"~{CROSS:.0f} m", 9, '600', c='#444', a='middle'))
        axis = (driver == 'climate')
        body = build_reach_panel(reach, driver, title=None, show_axis=axis,
                                 show_crossing_note=False, register=register)
        s.append(f'<svg x="0" y="{row_top + TITLE_H:.1f}" width="{W}" height="{BAND}" '
                 f'viewBox="0 {CROP_TOP} {PW} {BAND}">{body}</svg>')

    s.append(_r_txt(W / 2, H - 8, foot, 10, '600', c='#3a3a33', a='middle', it=True))
    s.append('</svg>')
    return "".join(s)


def build_reach_body(reach, multiples=False):
    """all reach-figure drawing at native coords (0..REACH_W, 0..REACH_H), WITHOUT the
    <svg> wrapper/background. `reach` = load_reach() dict. `multiples=True` draws the
    storm / 5-yr / 20-yr Dupuit water-table curves (used in the grid's reach panel);
    `multiples=False` (standalone reach) draws only the single 20-yr horizon that the
    paper reviewer asked for, with the retreat sequence carried by the ghost shades."""
    coastal_dd, CLIM, CROSS = reach['coastal_dd'], reach['climate_mm'], reach['crossing_m']
    _und = segmented(110.0, 78.0, nudge_seg2=True)[0]
    # LOCAL reach amplitude scale (Martin): rather than lift the dune/water-table geometry
    # (which would decouple this figure from the management diagrams that share ground()/
    # segmented()), we take the EXISTING drawn gap between the undisturbed line and the
    # sea-level 20-yr erosion toe at the nose and DEFINE it as the modelled shore drawdown
    # (coastal_dd(0) = 581 mm). Everything else on the figure — climate offset, inland
    # drawdown curves, the 100 mm scale bar — is then drawn to this same scale, so it is
    # internally consistent without touching the shared geometry. The global PX_PER_MM
    # (0.10, shared with 09f) is untouched.
    _gap_px = SEA - float(np.interp(SH['20yr'], X, _und))     # undisturbed -> sea at the nose
    _RPX = _gap_px / coastal_dd(0.0)                          # reach px per mm
    def _rpx(mm): return mm * _RPX
    _EXAG = round(_RPX * 1000.0 / _R_PXM)                     # vertical exaggeration factor
    _clm = climate_build_after_table(_und, px_per_mm=_RPX)[0]
    # Seam-anchored retreat curves: the parabola's inland end (shared XE = 330 m on the
    # reach scale) is pinned to the SAME committed drawdown the inland continuation plots,
    # so every curve is exactly continuous at the cross-section boundary. (The coastal
    # GRID cell keeps its schematic MECH_FIG_RETREAT_HIN anchors — it has no distance
    # scale to be continuous with.)
    _dd_at = {'storm': reach['storm_dd'], '5yr': reach['c5_dd'], '20yr': coastal_dd}
    _und_seam = float(np.interp(XE, X, _und))
    _hg = {k: SEA - (_und_seam + _rpx(_dd_at[k](_R_DN))) for k in ('storm', '5yr', '20yr')}
    _ret = {k: grandf(SH[k], _hg[k])(X) for k in ('storm', '5yr', '20yr')}
    SEALV = 250.0
    def pth(xs, ys): return "M " + " L ".join(f"{a:.1f},{b:.1f}" for a, b in zip(xs, ys))
    s = []
    s.append(_r_txt(_R_NL, 26, 'Coastal retreat vs climate along the reach inland', 15, '600'))
    s.append(_r_txt(_R_NL, 42,
                    'water-table curves and 900 m reach to committed scale; dune surface '
                    f'illustrative; vertical exaggerated x{_EXAG}', 10, c='#888780'))
    s.append(_r_txt(_R_NL, 55,
                    'conceptual reach built from the fitted d0, L and climate background '
                    '(Section 4.11)', 9.5, c='#9a968a', it=True))

    # ==== near-shore: coastal erosion ghosting + retreat curves + climate (shared solver) ====
    xs = [_r_nx(x) for x in X]
    rz = [(ORIG_SHORE, SH['storm'], 'storm'), (SH['storm'], SH['5yr'], '5yr'),
          (SH['5yr'], SH['20yr'], '20yr')]
    s.append(f'<polygon points="{_r_nx(40):.0f},{SEALV:.0f} {_r_nx(110):.0f},{SEALV:.0f} '
             f'{_r_nx(110):.0f},{SEALV+40:.0f} {_r_nx(40):.0f},{SEALV+40:.0f}" fill="{SEA_BLUE}"/>')
    for (xa, xb, k) in rz:
        s.append(f'<rect x="{_r_nx(xa):.1f}" y="{SEALV:.1f}" width="{_r_nx(xb)-_r_nx(xa):.1f}" '
                 f'height="40" fill="{lighten(SEA_BLUE, SEA_LIGHTEN[k])}"/>')
    for (xa, xb, k) in rz:   # eroded-dune ghosts (original fore-dune + seaward slack)
        xseg = X[(X >= xa) & (X <= xb)]
        s.append(f'<path d="{pth([_r_nx(x) for x in xseg], [ground(x) for x in xseg])} '
                 f'L{_r_nx(xb):.1f},{SEALV:.1f} L{_r_nx(xa):.1f},{SEALV:.1f} Z" '
                 f'fill="{lighten(DUNE, ERODE_LIGHTEN[k])}"/>')
    xsi = X[X >= SH['20yr']]
    s.append(f'<path d="{pth([_r_nx(x) for x in xsi], [ground(x) for x in xsi])} '
             f'L{_r_nx(640):.1f},{BASE} L{_r_nx(SH["20yr"]):.1f},{BASE} Z" fill="{DUNE}"/>')
    s.append(f'<path d="{pth([_r_nx(x) for x in xsi], [ground(x) for x in xsi])}" '
             f'fill="none" stroke="#C4A867" stroke-width="1"/>')
    s.append(f'<path d="{pth(xs, list(_und))}" fill="none" stroke="{REF_GREY}" '
             f'stroke-width="1.3" stroke-dasharray="2 3"/>')
    s.append(f'<path d="{pth(xs, list(_clm))}" fill="none" stroke="{CLIMC}" '
             f'stroke-width="2.4" stroke-dasharray="7 3"/>')
    # near-shore water-table curves. multiples=True (grid): all three storm/5-yr/20-yr
    # Dupuit lines. multiples=False (standalone/paper): only the 20-yr horizon, with the
    # retreat sequence carried by the ghost shades + consolidated label.
    _ks = ('storm', '5yr', '20yr') if multiples else ('20yr',)
    for k in _ks:
        m = X >= SH[k]; lw = {'storm': 1.8, '5yr': 2.3, '20yr': 2.6}[k]
        s.append(f'<line x1="{_r_nx(SH[k]):.0f}" y1="245" x2="{_r_nx(SH[k]):.0f}" y2="255" '
                 f'stroke="#3B8BD4" stroke-width="1.3"/>')
        s.append(f'<path d="{pth([_r_nx(x) for x in X[m]], [v for v in _ret[k][m]])}" '
                 f'fill="none" stroke="{COL[k]}" stroke-width="{lw}" stroke-linecap="round"/>')
    s.append(_r_txt(_r_nx(120), BASE - 46, 'sea', 10, c='#5f5e5a'))
    s.append(_r_txt(_r_nx(500), 150, 'inland slack', 9.5, c='#5f5e5a', a='middle', it=True))
    # retreat-state labels. multiples=True (grid): each state labelled directly UNDER its
    # own ghost band, no tick marks (the coloured shade + coloured label is the link).
    # multiples=False (standalone): one compact inline "shoreline retreating: .../.../..."
    if multiples:
        _prev = ORIG_SHORE
        for k, lab in (('storm', 'storm'), ('5yr', '5 yr'), ('20yr', '20 yr')):
            xmid = (_r_nx(_prev) + _r_nx(SH[k])) / 2
            s.append(_r_txt(xmid, 272, lab, 8, '600', c=COL[k], a='middle'))
            _prev = SH[k]
    else:
        # storm / 5-yr / 20-yr labelled directly under their own ghost band (aligned where
        # the tick marks used to point), each in its state colour; the "shoreline
        # retreating" caption sits on its own line below. No tick marks.
        _prev = ORIG_SHORE
        for k, lab in (('storm', 'storm'), ('5yr', '5 yr'), ('20yr', '20 yr')):
            xmid = (_r_nx(_prev) + _r_nx(SH[k])) / 2
            s.append(_r_txt(xmid, 268, lab, 8, '600', c=COL[k], a='middle'))
            _prev = SH[k]
        s.append(_r_txt((_r_nx(ORIG_SHORE) + _r_nx(SH['20yr'])) / 2, 284,
                        'shoreline retreating', 8, '600', c='#712B13', a='middle'))

    # ==== inland: 20-yr coastal drawdown recovers, climate flat, crossing ====
    di = np.linspace(_R_DN, 900, 240); gxi = [_r_ix(d) for d in di]
    _und_raw = _r_und_in(di); _grd = _r_ground_in(di)         # per-curve flood base
    def _pond(off_arr):                                        # flat-pond flatten of und + offset(mm)
        return _flat_pond(di, _und_raw + np.asarray(off_arr, float) * _RPX, _grd)
    _undf = _flat_pond(di, _und_raw, _grd)                     # reference: floods where und does
    s.append(f'<path d="{pth(gxi, [_r_ground_in(d) for d in di])} L{_r_ix(900):.1f},{BASE} '
             f'L{_r_ix(_R_DN):.1f},{BASE} Z" fill="{DUNE}"/>')
    s.append(f'<path d="{pth(gxi, [_r_ground_in(d) for d in di])}" fill="none" '
             f'stroke="#C4A867" stroke-width="1"/>')
    s.append(f'<path d="{pth(gxi, list(_undf))}" fill="none" stroke="{REF_GREY}" '
             f'stroke-width="1.3" stroke-dasharray="2 3"/>')
    # inland coastal horizon(s). multiples: storm / 5-yr continue inland too; otherwise
    # only the 20-yr line (paper reviewer's single unambiguous horizon). Each floods only
    # where its own drawn-down surface still stands above the slack floor (per-curve).
    if multiples:
        _dd_in = {'storm': reach['storm_dd'], '5yr': reach['c5_dd']}
        for k, lw in (('storm', 1.8), ('5yr', 2.3)):
            _c = _pond([_dd_in[k](d) for d in di])
            s.append(f'<path d="{pth(gxi, list(_c))}" '
                     f'fill="none" stroke="{COL[k]}" stroke-width="{lw}" stroke-linecap="round"/>')
    _coast = _pond([coastal_dd(d) for d in di])
    s.append(f'<path d="{pth(gxi, list(_coast))}" '
             f'fill="none" stroke="{COAST}" stroke-width="2.6"/>')
    _clim = _pond(np.full(len(di), CLIM))
    s.append(f'<path d="{pth(gxi, list(_clim))}" fill="none" '
             f'stroke="{CLIMC}" stroke-width="2.4" stroke-dasharray="7 3"/>')

    # ==== drawdown marker: dotted line at the TOE of the 20-yr erosion (the eroded nose),
    # spanning the undisturbed line down to the sea-level toe — the gap that DEFINES the
    # local scale as 581 mm. Everything else on the figure is drawn to this same scale.
    x_nose = _r_nx(SH['20yr'])                       # toe of the 20-yr erosion / eroded nose
    y_und = float(np.interp(SH['20yr'], X, _und))    # undisturbed at the nose
    y_dd = SEA                                        # 20-yr erosion toe (sea level)
    s.append(f'<line x1="{x_nose:.0f}" y1="{y_und:.1f}" x2="{x_nose:.0f}" y2="{y_dd:.1f}" '
             f'stroke="{COAST}" stroke-width="1.2" stroke-dasharray="2 2"/>')
    for yy in (y_und, y_dd):
        s.append(f'<line x1="{x_nose-3:.0f}" y1="{yy:.1f}" x2="{x_nose+3:.0f}" y2="{yy:.1f}" '
                 f'stroke="{COAST}" stroke-width="1.0"/>')
    s.append(_r_txt(x_nose, y_und - 6, '581 mm', 9, '600', c=COAST, a='middle'))
    s.append(_r_txt(x_nose + 6, (y_und + y_dd) / 2 + 3, '(δ₀ 29.03 mm/yr x 20 yr)',
                    7, '400', c=COAST))
    # climate amplitude — boxed callout in clear space above the flat line
    _cbx, _cby = _r_ix(430), 150.0
    s.append(f'<rect x="{_cbx-4:.0f}" y="{_cby-11:.0f}" width="196" height="16" rx="2.5" '
             f'fill="#fff" opacity="0.82"/>')
    s.append(_r_txt(_cbx, _cby, '-127 mm everywhere (c 6.35 mm/yr x 20 yr)', 8.5, '600', c=CLIMC))
    # 100 mm vertical scale bar (100 * PX_PER_MM px), far-right clear space
    _sbx = _r_ix(880); _sby = 120.0; _sbh = _rpx(100)
    s.append(f'<line x1="{_sbx:.0f}" y1="{_sby:.0f}" x2="{_sbx:.0f}" y2="{_sby+_sbh:.0f}" '
             f'stroke="#444" stroke-width="1.4"/>')
    s.append(f'<line x1="{_sbx-3:.0f}" y1="{_sby:.0f}" x2="{_sbx+3:.0f}" y2="{_sby:.0f}" '
             f'stroke="#444" stroke-width="1.4"/>')
    s.append(f'<line x1="{_sbx-3:.0f}" y1="{_sby+_sbh:.0f}" x2="{_sbx+3:.0f}" y2="{_sby+_sbh:.0f}" '
             f'stroke="#444" stroke-width="1.4"/>')
    s.append(_r_txt(_sbx - 6, _sby + _sbh / 2 + 3, '100 mm', 8.5, '600', c='#444', a='end'))

    xc = _r_ix(CROSS); yc = _r_und_in(CROSS) + _rpx(CLIM)
    s.append(f'<line x1="{xc:.0f}" y1="84" x2="{xc:.0f}" y2="{BASE:.0f}" stroke="#444" '
             f'stroke-width="1" stroke-dasharray="2 3"/>')
    s.append(f'<circle cx="{xc:.0f}" cy="{yc:.1f}" r="3.4" fill="#444"/>')
    s.append(_r_txt(xc, 78, f'~{CROSS:.0f} m: climate drawdown exceeds coastal', 10, '600',
                    c='#444', a='middle'))
    s.append(_r_txt(_r_ix(340), BASE + 18, 'coastal deeper', 9.5, '600', c=COAST, a='middle'))
    s.append(_r_txt(_r_ix(810), BASE + 18, 'climate deeper', 9.5, '600', c=CLIMC, a='middle'))
    for d in (0, 150, 300, 450, 600, 750, 900):
        s.append(_r_txt(_r_ix(d), BASE + 34, f'{d:.0f}' + (' m' if d == 900 else ''), 9,
                        c='#888', a='middle'))
    s.append(_r_txt(_r_ix(450), BASE + 46, 'distance inland from shore', 9, c='#a8a498',
                    a='middle', it=True))
    yL = REACH_H - 26
    _coastal_leg = ('coastal water table (storm / 5-yr / 20-yr)' if multiples
                    else 'coastal water table (retreat / 20 yr)')
    s.append(f'<line x1="{_R_NL}" y1="{yL}" x2="{_R_NL+26}" y2="{yL}" stroke="{COAST}" '
             f'stroke-width="2.6"/>' + _r_txt(_R_NL + 32, yL + 4, _coastal_leg, 10.5))
    s.append(f'<line x1="{_R_NL+250}" y1="{yL}" x2="{_R_NL+276}" y2="{yL}" stroke="{CLIMC}" '
             f'stroke-width="2.4" stroke-dasharray="7 3"/>' + _r_txt(_R_NL + 282, yL + 4, 'climate water table (20 yr)', 10.5))
    s.append(f'<line x1="{_R_NL+470}" y1="{yL}" x2="{_R_NL+496}" y2="{yL}" stroke="{REF_GREY}" '
             f'stroke-width="1.3" stroke-dasharray="2 3"/>' + _r_txt(_R_NL + 502, yL + 4, 'undisturbed table', 10.5))
    s.append(_r_txt(REACH_W / 2, REACH_H - 8,
                    f'Near-shore shows the coastal retreat and erosion (ghosted); '
                    f'coastal and climate curves cross at about {CROSS:.0f} m from the shore.',
                    9, c='#888780', a='middle'))
    return "".join(s)

def build_reach_svg(reach, png_width=1520):
    """standalone reach figure: full <svg> wrapping build_reach_body()."""
    body = build_reach_body(reach)
    return (f'<svg width="{REACH_W}" height="{REACH_H}" viewBox="0 0 {REACH_W} {REACH_H}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="{REACH_W}" height="{REACH_H}" fill="#fff"/>{body}</svg>')

# ================================================================================================
# Combined grid compositor (from gen_grid_combined v0.2.0 — THE report figure)
# ================================================================================================
GRID_W = 948
_G_ML, _G_MR, _G_GAP = 14, 14, 14
_G_COLW = (GRID_W - _G_ML - _G_MR - _G_GAP) // 2
_G_COLX = [_G_ML, _G_ML + _G_COLW + _G_GAP]
_G_TITLE_H, _G_START_H, _G_LOCAL_H = 40, 132, 168
_G_RSC = (GRID_W - 2 * _G_ML) / REACH_W          # scale the reach panel to the grid width
_G_Y_START = _G_TITLE_H
_G_Y_LOCAL = _G_Y_START + _G_START_H
_G_Y_REACH = _G_Y_LOCAL + _G_LOCAL_H
GRID_H = _G_Y_REACH + REACH_H * _G_RSC + 8

def _g_xsec(geo, colx, top):
    return place(geo, colx + 10, top + 22, _G_COLW - 20, 95)

def build_grid_combined_svg(reach, clearfell):
    """THE §5.8 report figure: starting states + interventions + full-width reach panel.

    `reach` = load_reach() dict; `clearfell` = load_clearfell_steps() tuple
    (annual_m, annual_ptxt, summer_m, summer_ptxt). Scrape magnitudes come from the
    resolved EDGE_DH_MM (call load_amplitudes() first)."""
    cf_a, cf_ap, cf_s, cf_sp = clearfell
    cut = EDGE_DH_MM['scrape_cut_rise']
    offc = EDGE_DH_MM['scrape_offslack']
    mag_scrape = (f'cut {cut:+.0f} mm \u00b7 off-cut {offc:.0f} mm (WMC3) \u00b7 both measured')
    mag_fell = (f'{cf_a:+.2f} m over the year ({cf_ap}) \u00b7 '
                f'{cf_s:+.2f} m summer ({cf_sp})')
    s = [f'<svg width="{GRID_W}" height="{GRID_H:.0f}" viewBox="0 0 {GRID_W} {GRID_H:.0f}" '
         f'xmlns="http://www.w3.org/2000/svg">'
         f'<rect width="{GRID_W}" height="{GRID_H:.0f}" fill="#fff"/>']
    s.append(txt(_G_ML, 24, 'Four drivers of water-table change at Newborough', size=15, w='600'))
    s.append(txt(_G_ML, 40, 'schematic \u00b7 not to scale', size=10.5, col='#888780'))

    # row 1 — starting states
    for cxi, (title, geo) in enumerate([('Undisturbed \u2014 wet slacks', geo_wet_before),
                                        ('Standing forest', lambda: geo_forest(False))]):
        colx = _G_COLX[cxi]
        s.append(txt(colx + _G_COLW / 2, _G_Y_START + 16, title, size=11.5, w='600',
                     col='#6a6656', anchor='middle'))
        s.append(_g_xsec(geo(), colx, _G_Y_START))
    s.append(txt(GRID_W / 2, _G_Y_START + _G_START_H - 6,
                 'starting states  \u00b7  the dashed line in every panel below is the undisturbed table',
                 size=9.5, col='#a8a498', anchor='middle', style=' font-style="italic"'))
    s.append(f'<line x1="{_G_ML}" y1="{_G_Y_LOCAL:.0f}" x2="{GRID_W-_G_MR}" y2="{_G_Y_LOCAL:.0f}" '
             f'stroke="#ECE7DA" stroke-width="1"/>')

    # row 2 — local interventions (scrape under undisturbed | clearfell under standing forest)
    locals_ = [('Dune scrape', geo_scrape_after, mag_scrape, 'settles', 'observed'),
               ('Clearfell', lambda: geo_forest(True), mag_fell, 'settles', 'observed')]
    for cxi, (title, geo, mag, tstag, evtag) in enumerate(locals_):
        colx = _G_COLX[cxi]
        s.append(txt(colx + _G_COLW / 2, _G_Y_LOCAL + 16, title, size=12.5, w='600', anchor='middle'))
        s.append(_g_xsec(geo(), colx, _G_Y_LOCAL))
        s.append(txt(colx + _G_COLW / 2, _G_Y_LOCAL + _G_LOCAL_H - 22, mag, size=9.5,
                     col='#3a3a33', anchor='middle'))
        s.append(txt(colx + _G_COLW / 2, _G_Y_LOCAL + _G_LOCAL_H - 8, f'{tstag} \u00b7 {evtag}',
                     size=10, w='600', col=TAGCOL[tstag], anchor='middle'))
    s.append(f'<line x1="{_G_ML}" y1="{_G_Y_REACH:.0f}" x2="{GRID_W-_G_MR}" y2="{_G_Y_REACH:.0f}" '
             f'stroke="#ECE7DA" stroke-width="1"/>')

    # row 3 — embedded reach panel (full width; carries the coastal + climate drivers)
    s.append(f'<g transform="translate({_G_ML},{_G_Y_REACH:.1f}) scale({_G_RSC:.4f})">'
             f'{build_reach_body(reach, multiples=True)}</g>')
    s.append('</svg>')
    return "".join(s)

# ================================================================================================
# Render helper
# ================================================================================================
def render_svg(svg_str, svg_path, png_path, png_width=1520):
    """write the SVG master and rasterise a PNG placement copy (cairosvg). Returns True
    if the PNG rendered, False (with an info note) if cairosvg is unavailable."""
    with open(svg_path, 'w') as fh:
        fh.write(svg_str)
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=png_width)
        return True
    except Exception as e:                           # noqa: BLE001 — report and continue
        info(f"PNG render skipped ({e}); SVG written")
        return False
