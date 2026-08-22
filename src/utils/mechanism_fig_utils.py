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
    gen_climate.py       (v0.2.0)  uniform signed offset (continuous Dupuit, pond-only fill)
    gen_grid.py          (v0.8.0)  cell compositing helpers + grid layout
    gen_reach_discont.py (v0.5.0)  coastal reach body (continuous 900 m scale)
    gen_grid_combined.py (v0.2.0)  THE report figure compositor (starting states +
                                   interventions + full-width reach panel)

The chained-segment water-table solver was developed and LOCKED on the coastal figure;
edit it HERE only. Per-mechanism functions add mechanism-specific shapes on top.

Physics vs figure-design
------------------------
PHYSICAL amplitudes are read LIVE from committed CSVs (no hardcoded amplitudes):
    09f_01_reach_profile.csv ROW 0 — one edge amplitude per driver (forest standing,
        coastal 5-yr/storm, scrape cut rise, thinned), and the full reach columns
        for the coastal reach panel (coastal 20-yr decay =
        (MECHANISM_HORIZON_YEARS / COAST_CHRONIC_YEARS) x |coastal_5yr(d)|).
    10m_report_numbers.csv — WMC3_BACI_DiD_step_2015_scraping: the ONE measured
        off-cut drawdown point (-55 mm; reproducible -54 mm in 2023).
    10a_report_numbers.csv — clearfell BACI steps (annual + summer) for the grid's
        clearfell magnitude line.

NO spatially uniform far-field term is drawn on any of these figures. The fitted
constant c of the Script 25 coastal decay is a COMPENSATING window statistic, not a
site-wide driver: across fixed-length rolling windows it correlates at about -0.8 with
the CWB covariate's trend contribution (25_13_rolling_window.csv), so when the covariate
takes more of the decline c takes less. It carries no independent information about a
site-wide driver, and drawing it beside the coastal curve invites a comparison it cannot
support. 25_01_panel_fit_parameters.csv is therefore no longer read here.
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

"""
from __future__ import annotations

__version__ = "1.11.0"
# CHANGELOG
#   1.11.0 (2026-08-21): two reach-panel rendering defects Martin found in the
#       regenerated figures.
#       (a) PHYSICAL. The storm and 5-yr water-table curves ran ABOVE the drawn
#           dune surface from roughly 80 m to 250 m — up to 11.5 px on the
#           standalone reach — and above the undisturbed table with them, which
#           says coastal retreat RAISES a head. Cause: _flat_pond() and
#           segmented() level a flooded slack by different rules, and for the
#           shallow curves _flat_pond()'s level came out above the slack's own
#           seaward outlet rim. Retreat curves now go through the new
#           subsurface(), which clamps them to the undisturbed table; np.maximum
#           is monotone so storm <= 5-yr <= 20-yr survives, and the seam anchors
#           are untouched. Clamping to the GROUND as well was tried and rejected:
#           it pinned the storm curve to the dune over 40 % of its length. Instead
#           the reach panel now draws the standing water in its slacks
#           (_inland_ponds(), plus _reach_ponds() on the reach body), which every
#           cross-section cell has always done via water(); the reach was the only
#           member of the figure set carrying a water table but no water, which is
#           why the same geometry read as a wet slack in the cells and as a
#           floating line on the reach. A head at or below the undisturbed table is
#           therefore at or below the drawn water surface. The dotted undisturbed
#           reference is deliberately NOT clamped: it IS a water table. New
#           reach_clearance() rebuilds the curves through the same helpers and
#           returns the margins, which Script 09g prints and fails on.
#       (b) The delta-0 annotation sat at the leader's midpoint, crossed by the
#           dotted rule and crowded by 'sea' at grid scale. It and the mm label are
#           now one centred two-line callout stacked above the leader, each line on
#           a white backing plate sized by the new shared text_width().
#       No amplitude, scale, colour or axis changes; the surface geometry did not
#       move.
#   1.10.0 (2026-08-20): the far-field term is REMOVED from every 09g figure, on
#       new evidence — D-043's amendment (which restored it) is reversed, and its
#       original withdrawal stands. The fixed-length rolling-window sweep
#       (25_13_rolling_window.csv) measures corr(c, CWB trend contribution) at
#       about -0.8 at every window length: c is a compensating term that absorbs
#       whatever the covariate does not take, so it carries no independent
#       site-wide signal to draw. Gone: _load_far_field_term(), the far_field_mm /
#       far_field_c_mm_yr keys of load_reach(), uniform_offset_table() (with
#       PIN_A / PIN_B), the FARF palette entry, the 'far_field' branch of
#       build_reach_panel(), the third panel of build_reach_stack(), and the
#       far-field curve, boxed callout and legend swatch of build_reach_body().
#       The OUT_25_FIT_PARAMETERS import goes with them. The grid title now COUNTS
#       the drawn drivers (DRIVERS) rather than spelling a fixed number, so a
#       driver cannot be retired again while the title still claims it. NOT
#       touched: the coastal curve, the undisturbed table, the ghosted retreat
#       wedges and the 900 m axis (D-043: the axis marks the fitted reach L).
#   1.9.0 (2026-08-19): D-043 amended. The far-field term is RESTORED as a driver
#       (Martin: marginal, but worth showing), read straight from 25_01 by the new
#       _load_far_field_term() rather than through 09f, which no longer carries it.
#       It is drawn SIGNED — the HEAD render's "-4 mm everywhere" came from an abs()
#       on a POSITIVE c — and is labelled the fitted far-field term, marginal and not
#       separately identified, never a climate rate. The band stays withdrawn and no
#       crossing returns. uniform_offset_table() and the FARF palette entry come back
#       with it; the panel takes 'far_field' again and the stack is three panels.
#       Three rendering defects fixed, all of them older than the D-039 work:
#       (a) the scrape head stepped 11.2 px off the pond surface at the cut's inland
#           edge — both flanks now rise out of the pool on the flat-pond smoothstep,
#           anchored on the cross-section edge and the next flooded slack;
#       (b) the storm / 5-yr / 20-yr retreat curves ran straight through the slacks —
#           they are now routed through _flat_pond() on the same per-curve basis the
#           inland continuation already used;
#       (c) the undisturbed panel's water table stopped at the cross-section boundary
#           — it now runs the whole 900 m slice.
#   1.8.0 (2026-08-19): D-043. The far-field band of 1.7.0 is WITHDRAWN, so the
#       reach carries one thing: the coastal driver. build_reach_panel() takes
#       'undisturbed' or 'coastal'; the stack and the lay figure are two panels;
#       build_reach_body() drops the band, its boxed callout and its legend
#       swatch. uniform_offset_table() (with PIN_A / PIN_B), svg_band() and the
#       FARF palette entry go with them — nothing draws a spatially uniform term
#       on this figure any more. load_reach() no longer emits far_field_* keys.
#       The 1.7.0 removal of the flat climate line and the crossing STANDS.
#   1.7.0 (2026-08-19): D-039. The flat "climate" line and the coastal-vs-climate
#       crossing retired; load_reach() stopped emitting crossing_m, climate_mm
#       and climate_c_mm_yr, and the unused geo_climate_after() /
#       climate_fill_ponds() climate-cell pair was removed. Its replacement band
#       is superseded by 1.8.0.
#   1.6.6: this module's state before it carried an inline changelog.

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
COAST = '#3d1f66'; INK = '#26261f'
TAGCOL = {'accumulating': '#8a5a2b', 'settles': '#2b6a8a'}

# ==== driver register ===========================================================================
# The drivers these figures draw, in drawn order. The grid title COUNTS this register
# rather than spelling a number, so retiring or adding a driver moves the title with it
# (D-011: no asserted results in code). LOCAL_DRIVERS are the two management panels of
# grid row 2; REACH_DRIVERS are the site-wide terms on the full-width reach panel, which
# is the coastal term alone — the fitted far-field constant is a compensating window
# statistic, not a driver, and is not drawn (see the module docstring).
LOCAL_DRIVERS = ('scrape', 'clearfell')
REACH_DRIVERS = ('coastal',)
DRIVERS = LOCAL_DRIVERS + REACH_DRIVERS
REACH_STACK_PANELS = ('undisturbed',) + REACH_DRIVERS

_COUNT_WORDS = ('Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven')

def count_word(n):
    """Spell a small count for a figure title; digits beyond the table (a rendering
    convenience, not a stored quantity)."""
    return _COUNT_WORDS[n] if 0 <= n < len(_COUNT_WORDS) else f"{n}"

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
    'coastal_storm':   'mech_coastal_storm_mm',
    'scrape_offslack': 'wmc3_drawdown_mm',       # measured WMC3 off-cut (shared with 09f)
}
_09F_COLMAP = {                  # EDGE_DH_MM key -> 09f_01 column (row 0 = distance 0)
    'forest_standing': 'standing_pine_head_mm',
    'coastal_5yr':     'coastal_5yr_head_mm',
    'scrape_cut_rise': 'scrape_head_mm',
    'thinned':         'thinned_forest_head_mm',
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
    """Coastal reach quantities, fully derived from committed 09f_01 columns.

    Returns dict:
        coastal_dd(d)      : 20-yr coastal drawdown (mm, +ve) =
                             (MECHANISM_HORIZON_YEARS / COAST_CHRONIC_YEARS) x |coastal_5yr(d)|
        c5_dd(d)           : 5-yr coastal drawdown (mm, +ve) = |coastal_5yr(d)|
        storm_dd(d)        : single 6 m storm drawdown (mm, +ve) = |coastal_6m_storm(d)|
        reach_L_m, delta0_mm_yr, source

    Coastal retreat is the ONLY driver this dict carries. The retired keys `crossing_m`,
    `climate_mm`, `climate_c_mm_yr`, `far_field_lo/hi_mm`, `far_field_mm` and
    `far_field_c_mm_yr` are deliberately NOT emitted: a stale reader raises KeyError
    instead of silently reading something else. The fitted constant c is a compensating
    window statistic rather than a site-wide driver (see the module docstring), so
    nothing here reads it and no figure draws it.

    All three drawdown interpolators cover the full 0..900 m reach, so the drawn
    near-shore curves can be seam-anchored to the same values the inland
    continuation plots (exact continuity at the cross-section boundary).

    Fallback (CSV absent): reconstructed from the documented 25_01 fit defaults
    (delta_0, L via pipeline_params; storm amplitude from
    mech_coastal_storm_mm), with a warning.
    """
    n20 = MECHANISM_HORIZON_YEARS / COAST_CHRONIC_YEARS      # 4.0 on current config
    try:
        df = pd.read_csv(OUT_09F_REACH_CSV)
        d   = df['distance_m'].to_numpy(float)
        c5  = df['coastal_5yr_head_mm'].to_numpy(float)
        st  = df['coastal_6m_storm_head_mm'].to_numpy(float)
        edge5 = abs(float(c5[0]))
        Lfit = float(d[np.max(np.where(np.abs(c5) > 0.0))]) if np.any(np.abs(c5) > 0) \
            else float(default_value('coast_reach_L_m'))
        def c5_dd(dd):
            return np.abs(np.interp(np.asarray(dd, float), d, c5))
        def storm_dd(dd):
            return np.abs(np.interp(np.asarray(dd, float), d, st))
        def coastal_dd(dd):
            return n20 * c5_dd(dd)
        return {'coastal_dd': coastal_dd, 'c5_dd': c5_dd, 'storm_dd': storm_dd,
                'reach_L_m': Lfit,
                'delta0_mm_yr': edge5 / COAST_CHRONIC_YEARS,
                'source': f"committed 09f ({OUT_09F_REACH_CSV.name})"}
    except (FileNotFoundError, KeyError, IndexError):
        L  = float(default_value('coast_reach_L_m'))
        d0 = abs(float(default_value('coast_delta0_mm_yr')))
        s0 = abs(float(default_value('mech_coastal_storm_mm')))
        def _ramp_dd(dd, amp):
            dd = np.asarray(dd, float)
            return np.where(dd < L, amp * (1.0 - dd / L), 0.0)
        def c5_dd(dd):     return _ramp_dd(dd, COAST_CHRONIC_YEARS * d0)
        def storm_dd(dd):  return _ramp_dd(dd, s0)
        def coastal_dd(dd): return n20 * c5_dd(dd)
        warn(f"09f_01_reach_profile.csv unavailable — reach from documented defaults "
             f"(L={L:.0f} m, delta0={d0:.1f} mm/yr; run Script 09f for live values).")
        return {'coastal_dd': coastal_dd, 'c5_dd': c5_dd, 'storm_dd': storm_dd,
                'reach_L_m': L, 'delta0_mm_yr': d0,
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

TEXT_WIDTH_PER_PT = 0.517        # mean advance of the base sans, as a fraction of font size

def text_width(s, size):
    """Estimated rendered width of `s` at `size` px in the base sans stack.

    One shared estimate, so a label's white backing plate and the build-time collision
    check cannot disagree about how wide a label is. The constant is lbl()'s long-standing
    12 px figure (6.2 px per character) expressed per point; an estimate is enough here
    because every use has margin designed around it, and measuring real glyph advances
    would need a font library this module deliberately does not depend on."""
    return len(str(s)) * TEXT_WIDTH_PER_PT * float(size)


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
# a RISE at the cut (CEH36 BACI vs CEH4 — the headward cut reaches ground where the
# regional inland-rising head is naturally HIGHER, not an excavation lift) and the MEASURED
# WMC3 near-field off-cut drawdown (reproducible BACI DiD; both magnitudes are read
# live from 09f_01_reach_profile.csv / 10m, with first-pass fallbacks in
# pipeline_params._DEFAULTS). There
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
    inland slack toward — not below — its floor. Returns (wt, (pool_l, pool_r)).

    The head MEETS the pond surface at both edges. Stamping the pool flat and leaving the
    ambient table either side left an 11 px step at the cut's inland edge — the line leapt
    off the water surface instead of running out of it — so each flank now rises out of the
    pool on the smoothstep the flat-pond solver uses (zero slope at both ends, no kink).
    The flank anchors are geometry the module already names: seaward the cross-section edge,
    inland the seaward edge of the next flooded slack, so the blend stops where the ambient
    pond begins rather than flattening it."""
    y0, steps = segmented(110.0, 78.0, nudge_seg2=True)
    y = y0.copy()
    offcut_px = mm_px(EDGE_DH_MM['scrape_offslack'])
    dd = offcut_px * np.exp(-((X - OFFCUT_C) / OFFCUT_W) ** 2)
    dd[X < CUT_HEADWARD] = 0.0
    y = y + dd
    amb = y.copy()                                  # ambient (drawn-down) table, un-stamped
    pool = scrape_pool_level()
    xl = SLACK_C[0]
    while xl > XC and _sg1(xl - 0.5) > pool: xl -= 0.5
    xr = CUT_HEADWARD
    while xr < XE and _sg1(xr + 0.5) > pool: xr += 0.5
    m = (X >= xl) & (X <= xr); y[m] = pool

    def _rise_out(edge, anchor):
        """smoothstep from the pond surface at `edge` to the ambient table at `anchor`."""
        lo, hi = (anchor, edge) if anchor < edge else (edge, anchor)
        span = (X > lo) & (X < hi)
        if hi - lo < 1e-6 or not span.any():
            return
        f = np.clip(np.abs(X[span] - edge) / (hi - lo), 0.0, 1.0)
        y[span] = pool - (pool - amb[span]) * (f * f * (3.0 - 2.0 * f))

    _rise_out(xl, XC)                               # seaward: out to the cross-section edge
    _inland = [s_xl for (s_xl, _sxr, _sL, _sp) in steps if s_xl > xr]
    _rise_out(xr, min(_inland) if _inland else XE)  # inland: to the next flooded slack
    return y, (xl, xr)

# The spatially-uniform-offset table (uniform_offset_table, with its PIN_A / PIN_B sea
# pin) lived here and drew the fitted far-field term. It is retired: c is a compensating
# window statistic, not a site-wide driver, so nothing on these figures offsets the whole
# profile by a constant. See the module docstring.

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
    """undisturbed 'before' — coastal and scrape share this starting state."""
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
# Coastal REACH body (from gen_reach_discont v0.5.0; continuous 900 m scale)
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
    smooth once coastal drawdown has recovered inland), and each edge of the far-field
    band only where that edge floods — which is why the band's two edges are passed
    through separately rather than offset from one filled shape. Returns y for array dd."""
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


def subsurface(y, und):
    """Clamp a drawn RETREAT head to the undisturbed table (y-down canvas).

    **Coastal retreat never raises a head**, so no retreat curve may sit above the
    undisturbed table: `y >= und`. `_flat_pond()` did not enforce this, and that is the
    whole of the defect it caused. It set a flooded slack's level from the raw surface
    just seaward of the flooded run, while the undisturbed table takes its level from
    `segmented()`'s chained rule (the parabola one segment seaward of the slack centre).
    The two rules disagree, and for the shallow storm / 5-yr curves `_flat_pond()`'s
    level came out ABOVE the slack's own seaward outlet rim — and so above the
    undisturbed table, and above the dune — which is why those curves rode over the
    surface between roughly 80 m and 250 m.

    The ground is deliberately NOT a second clamp here. Where the undisturbed table
    stands above the illustrative ground the slack is WET, and the reach panel now draws
    that standing water (see `_reach_ponds()` / `_inland_ponds()`), exactly as the
    cross-section cells always have via `water()`. A head at or below the undisturbed
    table is therefore at or below the drawn water surface, never floating. Clamping to
    the ground instead was tried and rejected: it pinned the storm curve to the dune
    surface over 40 % of its length, which states a head the fit does not give.

    `np.maximum` is monotone, so applying it to an already-ordered family preserves the
    storm <= 5-yr <= 20-yr drawdown ordering the panel exists to show. The seam anchors
    are untouched: at the cross-section boundary every curve sits well below the
    undisturbed table, so the clamp is inactive there and continuity is unaffected.
    """
    return np.maximum(np.asarray(y, float), np.asarray(und, float))


def reach_clearance(reach, multiples=True):
    """Clearance of every plotted retreat head below the surfaces it may not cross, px.

    Rebuilds the curves through the same helpers `build_reach_body()` draws them with,
    and returns {curve: (min_vs_drawn_surface, min_vs_undisturbed)} over the near-shore
    and inland halves together. Positive means below.

    `min_vs_drawn_surface` is measured against the composite the reader actually sees:
    the illustrative ground where the slack is dry, and the DRAWN WATER SURFACE (the
    undisturbed table) where it is wet, since the reach panel now fills its slacks. A
    head may sit above a slack floor — that is standing water — but never above the
    ground in the open, and never above the water surface. Script 09g prints this and
    fails the run if either value goes negative: a water table drawn above the dune is a
    physical error, not an untidiness, and image-view does not catch it reliably
    in-session.
    """
    coastal_dd = reach['coastal_dd']
    _und = segmented(110.0, 78.0, nudge_seg2=True)[0]
    _grd = ground(X)
    _gap_px = SEA - float(np.interp(SH['20yr'], X, _und))
    _RPX = _gap_px / coastal_dd(0.0)
    _dd_at = {'storm': reach['storm_dd'], '5yr': reach['c5_dd'], '20yr': coastal_dd}
    _und_seam = float(np.interp(XE, X, _und))
    keys = ('storm', '5yr', '20yr') if multiples else ('20yr',)
    di = np.linspace(_R_DN, 900, 240)
    _und_raw = _r_und_in(di); _grd_in = _r_ground_in(di)
    _undf = _flat_pond(di, _und_raw, _grd_in)
    # the surface a reader sees: ground where dry, water surface where the slack is wet
    _surf_near = np.minimum(_grd, _und)
    _surf_in = np.minimum(_grd_in, _undf)
    out = {}
    for k in keys:
        hg = SEA - (_und_seam + _dd_at[k](_R_DN) * _RPX)
        near = subsurface(grandf(SH[k], hg)(X), _und)
        m = X >= SH[k]
        inl = subsurface(_und_raw + np.array([_dd_at[k](d) for d in di], float) * _RPX,
                         _undf)
        out[k] = (float(min((near[m] - _surf_near[m]).min(), (inl - _surf_in).min())),
                  float(min((near[m] - _und[m]).min(), (inl - _undf).min())))
    return out

def _r_txt(x, y, s, sz=12, w='400', c=INK, a='start', it=False):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT_STACK}" font-size="{sz}" '
            f'font-weight="{w}" fill="{c}" text-anchor="{a}"'
            f'{" font-style=\"italic\"" if it else ""}>{s}</text>')

def _reach_base(s, pth, draw_erosion):
    """Shared reach profile — sea, dune, near-shore cross-section (0..330 m) joined to
    the inland ground (330..900 m) — drawn identically for the technical figure and
    the lay stack. `draw_erosion` toggles the retreat-ghost fore-dune (on for coastal,
    off for the plain undisturbed panel). Returns the undisturbed water table array
    `_und` for callers that overlay drivers."""
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


def _inland_ponds(di, wt, gxi, grd):
    """Blue standing water in the INLAND slacks (330..900 m), the counterpart of
    `_reach_ponds()` for the near-shore third.

    Fills between the water surface `wt` and the ground `grd` wherever the ground dips
    below the table. Without it the reach panel was the only member of the figure set
    that carried a water table but no water: the cross-section cells have always drawn
    their slack water with `water()`, so the same geometry that reads as a wet slack in
    the cells read as a line floating over the dune on the reach. Drawn once, from the
    undisturbed table, beneath every driver curve — it is the panel's starting wetness,
    not a per-scenario result."""
    out = []
    fl = np.asarray(grd, float) > np.asarray(wt, float) + 0.2
    i, n = 0, len(di)
    while i < n:
        if fl[i]:
            j = i
            while j < n and fl[j]:
                j += 1
            seg = range(i, j)
            pts = " ".join(f"{gxi[k]:.1f},{wt[k]:.1f}" for k in seg) + " " + \
                  " ".join(f"{gxi[k]:.1f},{grd[k]:.1f}" for k in reversed(seg))
            out.append(f'<polygon points="{pts}" fill="{SEA_BLUE}"/>')
            i = j
        else:
            i += 1
    return "".join(out)


def build_reach_panel(reach, driver, title=None, show_axis=True, register="technical"):
    """A single reach panel on the shared profile, full 0..900 m. `driver` is one of
    REACH_STACK_PANELS — 'undisturbed' or 'coastal'. Used by the lay stacked figure so
    the lay panels share the technical figure's exact profile and amplitudes; only one
    thing is drawn per panel. `register` toggles technical-only annotation (the
    storm/5yr/20yr retreat-band labels on the coastal panel).

    There is no 'far_field' panel: the fitted constant c is a compensating window
    statistic rather than a site-wide driver (module docstring), so nothing on the reach
    offsets the whole profile by a constant. Returns the panel body SVG (no wrapper)."""
    coastal_dd = reach['coastal_dd']
    def pth(xs, ys): return "M " + " L ".join(f"{a:.1f},{b:.1f}" for a, b in zip(xs, ys))
    s = []
    if title:
        s.append(_r_txt(_R_NL, 20, title, 13, '600'))
    _und, di, gxi = _reach_base(s, pth, draw_erosion=(driver == 'coastal'))
    _und_raw = _r_und_in(di); _grd = _r_ground_in(di)         # per-curve flood base
    _undf = _flat_pond(di, _und_raw, _grd)                     # reference: floods where und does
    def _pond_g(off_fn):                        # und + drawdown(mm, +ve), clamped sub-surface
        surf = _und_raw + np.array([mm_px(off_fn(d)) for d in di], float)
        return subsurface(surf, _undf)
    xs = [_r_nx(x) for x in X]

    # pond fill in the near-shore slacks (the undisturbed panel carries the wet 'before';
    # coastal near-shore is eroded, so its ponds are subsumed by the retreat ghosting)
    if driver == 'undisturbed':
        s.append(_reach_ponds(_und, pth))
    # the inland slacks' standing water, on EVERY panel. Without it the inland coastal
    # curve ran up to 0.9 px over the dune with nothing drawn under it — the same defect
    # as the near-shore one, in the lay figure. Drawn from the undisturbed table, under
    # whatever the panel draws on top.
    s.append(_inland_ponds(di, _undf, gxi, _grd))

    # undisturbed reference — dashed grey, on every panel
    s.append(f'<path d="{pth(xs, list(_und))}" fill="none" stroke="{REF_GREY}" '
             f'stroke-width="1.3" stroke-dasharray="2 3"/>')
    s.append(f'<path d="{pth(gxi, list(_undf))}" fill="none" stroke="{REF_GREY}" '
             f'stroke-width="1.3" stroke-dasharray="2 3"/>')

    if driver == 'coastal':
        # 20-yr coastal drawdown: near-shore parabola seam-anchored, inland continuation
        _und_seam = float(np.interp(XE, X, _und))
        hg = SEA - (_und_seam + mm_px(coastal_dd(_R_DN)))
        # clamped sub-surface on the same basis as the inland continuation (see subsurface)
        wt = subsurface(grandf(SH['20yr'], hg)(X), _und); m = X >= SH['20yr']
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
    elif driver == 'undisturbed':
        # draw the wet table line so the ponds read as water, not gaps — across the WHOLE
        # slice. The near-shore path alone stopped the blue line at the cross-section
        # boundary, leaving the inland two thirds carrying only the dashed reference.
        s.append(f'<path d="{pth(xs, list(_und))}" fill="none" stroke="{WT_BLUE}" '
                 f'stroke-width="2.0"/>')
        s.append(f'<path d="{pth(gxi, list(_undf))}" fill="none" stroke="{WT_BLUE}" '
                 f'stroke-width="2.0"/>')
        s.append(_r_txt(_r_nx(120), BASE - 46, 'sea', 10, c='#5f5e5a'))
    else:
        # A retired driver name ('climate', 'far_field') must not fall through to an
        # undisturbed panel wearing someone else's title.
        raise ValueError(f"build_reach_panel: unknown driver {driver!r} — "
                         f"expected one of {REACH_STACK_PANELS}")

    if show_axis:
        for d in (0, 150, 300, 450, 600, 750, 900):
            s.append(_r_txt(_r_ix(d), BASE + 16, f'{d:.0f}' + (' m' if d == 900 else ''), 9,
                            c='#888', a='middle'))
    return "".join(s)


def build_reach_stack(reach, register="technical"):
    """Stacked reach: one panel per REACH_STACK_PANELS entry (undisturbed / coastal) on
    the SHARED profile, full 0..900 m, vertically aligned on one distance axis.
    `register` is 'technical' (mm amplitudes, precise labels) or 'lay' (plain language).
    Used by Script 09g (technical) and gen_grid_lay (lay), so both registers share one
    geometry.

    Coastal retreat is the only driver on the stack: no spatially uniform far-field term
    is drawn, so nothing is compared across panels and no crossing is marked. Returns a
    complete <svg> string."""
    coastal_dd = reach['coastal_dd']
    shore_mm = coastal_dd(0.0)
    lay = (register == "lay")

    panels = REACH_STACK_PANELS
    PW = REACH_W
    CROP_TOP, CROP_BOT = 96, int(BASE) + 24
    CROP_H = CROP_BOT - CROP_TOP
    HDR = 52
    TITLE_H = 18
    GAP = 10
    W = PW
    ROW = TITLE_H + CROP_H
    H = HDR + len(panels) * ROW + (len(panels) - 1) * GAP + 30

    if lay:
        head = "What the coast does to the water table"
        sub = ("one long slice from the shore inland, on the same scale - "
               "simple diagram, not to scale")
        titles = {
            'undisturbed': "Undisturbed dune (the starting point)",
            'coastal': "With coastal retreat - deepest near the shore, fading inland",
        }
        foot = ("The sea's retreat bites hardest near the shore and fades inland. "
                "Further inland it makes almost no difference.")
    else:
        head = "Coastal retreat along the reach"
        sub = ("undisturbed / coastal on one continuous scale to the fitted reach L "
               "\u00b7 shared amplitude scale \u00b7 no site-wide term is drawn")
        titles = {
            'undisturbed': "Undisturbed water table",
            'coastal': f"Coastal retreat: -{shore_mm:.0f} mm at shore over "
                       f"{MECHANISM_HORIZON_YEARS:.0f} yr, tapering to 0 by "
                       f"~{reach['reach_L_m']:.0f} m "
                       f"(\u03b4\u2080 -{reach['delta0_mm_yr']:.0f} mm/yr)",
        }
        foot = ("Coastal retreat is the only identified distance-dependent term, and "
                "the only driver drawn on the reach: the fitted far-field constant is a "
                "compensating window statistic, not a site-wide driver, so no uniform "
                "term is drawn beside it.")

    s = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'xmlns="http://www.w3.org/2000/svg"><rect width="{W}" height="{H}" fill="#fff"/>']
    s.append(_r_txt(_R_NL, 26, head, 16, '600'))
    s.append(_r_txt(_R_NL, 43, sub, 11, c='#888780'))

    for i, driver in enumerate(panels):
        row_top = HDR + i * (ROW + GAP)
        s.append(_r_txt(_R_NL, row_top + 13, titles[driver], 12, '600'))
        axis = (i == len(panels) - 1)         # distance axis on the bottom panel only
        body = build_reach_panel(reach, driver, title=None, show_axis=axis,
                                 register=register)
        s.append(f'<svg x="0" y="{row_top + TITLE_H:.1f}" width="{W}" height="{CROP_H}" '
                 f'viewBox="0 {CROP_TOP} {PW} {CROP_H}">{body}</svg>')

    s.append(_r_txt(W / 2, H - 8, foot, 10, '600', c='#3a3a33', a='middle', it=True))
    s.append('</svg>')
    return "".join(s)


def build_reach_body(reach, multiples=False):
    """all reach-figure drawing at native coords (0..REACH_W, 0..REACH_H), WITHOUT the
    <svg> wrapper/background. `reach` = load_reach() dict. `multiples=True` draws the
    storm / 5-yr / 20-yr Dupuit water-table curves (used in the grid's reach panel);
    `multiples=False` (standalone reach) draws only the single 20-yr horizon that the
    paper reviewer asked for, with the retreat sequence carried by the ghost shades."""
    coastal_dd = reach['coastal_dd']
    _und = segmented(110.0, 78.0, nudge_seg2=True)[0]
    # LOCAL reach amplitude scale (Martin): rather than lift the dune/water-table geometry
    # (which would decouple this figure from the management diagrams that share ground()/
    # segmented()), we take the EXISTING drawn gap between the undisturbed line and the
    # sea-level 20-yr erosion toe at the nose and DEFINE it as the modelled shore drawdown
    # (coastal_dd(0) = the committed shore amplitude). Everything else on the figure —
    # inland drawdown curves, the 100 mm scale bar — is then drawn to this same scale, so
    # it is internally consistent without touching the shared geometry. The global
    # PX_PER_MM (0.10, shared with 09f) is untouched.
    _gap_px = SEA - float(np.interp(SH['20yr'], X, _und))     # undisturbed -> sea at the nose
    _RPX = _gap_px / coastal_dd(0.0)                          # reach px per mm
    def _rpx(mm): return mm * _RPX
    _EXAG = round(_RPX * 1000.0 / _R_PXM)                     # vertical exaggeration factor
    # Seam-anchored retreat curves: the parabola's inland end (shared XE = 330 m on the
    # reach scale) is pinned to the SAME committed drawdown the inland continuation plots,
    # so every curve is exactly continuous at the cross-section boundary. (The coastal
    # GRID cell keeps its schematic MECH_FIG_RETREAT_HIN anchors — it has no distance
    # scale to be continuous with.)
    _dd_at = {'storm': reach['storm_dd'], '5yr': reach['c5_dd'], '20yr': coastal_dd}
    _und_seam = float(np.interp(XE, X, _und))
    _hg = {k: SEA - (_und_seam + _rpx(_dd_at[k](_R_DN))) for k in ('storm', '5yr', '20yr')}
    # Each retreat curve is clamped to the undisturbed table and to the drawn ground —
    # see subsurface() for why the previous per-curve _flat_pond() treatment put the
    # shallow storm and 5-yr curves ABOVE the dune between roughly 80 m and 250 m.
    _ret = {k: subsurface(grandf(SH[k], _hg[k])(X), _und)
            for k in ('storm', '5yr', '20yr')}
    SEALV = 250.0
    def pth(xs, ys): return "M " + " L ".join(f"{a:.1f},{b:.1f}" for a, b in zip(xs, ys))
    s = []
    s.append(_r_txt(_R_NL, 26,
                    'Coastal retreat along the reach inland',
                    15, '600'))
    s.append(_r_txt(_R_NL, 42,
                    'water-table curves and 900 m reach to committed scale; dune surface '
                    f'illustrative; vertical exaggerated x{_EXAG}', 10, c='#888780'))
    s.append(_r_txt(_R_NL, 55,
                    'conceptual reach built from the fitted d0 and L (Section 4.11); no '
                    'spatially uniform far-field term is drawn', 9.5,
                    c='#9a968a', it=True))

    # ==== near-shore: coastal erosion ghosting + retreat curves (shared solver) ====
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
    # standing water in the near-shore slacks, from the undisturbed table — the wetness
    # the panel starts from. Drawn under the curves so a head at or below the table is
    # visibly IN the water rather than floating over the dune. Landward of the 20-yr
    # shoreline only: seaward of it the slack has been eroded away and its water is
    # carried by the ghosted sea.
    s.append(_reach_ponds(np.where(X >= SH['20yr'], _und, ground(X)), pth))
    s.append(f'<path d="{pth(xs, list(_und))}" fill="none" stroke="{REF_GREY}" '
             f'stroke-width="1.3" stroke-dasharray="2 3"/>')
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

    # ==== inland: 20-yr coastal drawdown recovers to the reach L; no crossing ====
    di = np.linspace(_R_DN, 900, 240); gxi = [_r_ix(d) for d in di]
    _und_raw = _r_und_in(di); _grd = _r_ground_in(di)         # per-curve flood base
    _undf = _flat_pond(di, _und_raw, _grd)                     # reference: floods where und does
    def _pond(off_arr):                          # und + drawdown(mm, +ve), clamped sub-surface
        return subsurface(_und_raw + np.asarray(off_arr, float) * _RPX, _undf)
    s.append(f'<path d="{pth(gxi, [_r_ground_in(d) for d in di])} L{_r_ix(900):.1f},{BASE} '
             f'L{_r_ix(_R_DN):.1f},{BASE} Z" fill="{DUNE}"/>')
    s.append(f'<path d="{pth(gxi, [_r_ground_in(d) for d in di])}" fill="none" '
             f'stroke="#C4A867" stroke-width="1"/>')
    s.append(_inland_ponds(di, _undf, gxi, _grd))   # the inland slacks' standing water
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
    # Two-line callout, STACKED ABOVE the leader in the sky over the fore dune. The
    # delta-0 line used to sit at the leader's midpoint, where the dotted rule ran
    # through it, the ghost wedges sat behind it and the 'sea' label crowded it at grid
    # scale; it rendered as an unreadable overlap. Both lines now share one centred
    # column clear of the rule, each on its own white backing plate so nothing drawn
    # afterwards can cross them — the plate is needed because the wider second line
    # overhangs the dune crest and would otherwise sit on the tan fill.
    _mm_txt = f"{coastal_dd(0.0):.0f} mm"
    _d0_txt = (f"(δ₀ {reach['delta0_mm_yr']:.2f} mm/yr x "
               f"{MECHANISM_HORIZON_YEARS:.0f} yr)")
    for _t, _sz, _wt, _dy in ((_mm_txt, 9, '600', 19.0), (_d0_txt, 7, '400', 8.0)):
        _w = text_width(_t, _sz) + 6.0
        s.append(f'<rect x="{x_nose - _w / 2:.1f}" y="{y_und - _dy - _sz + 1:.1f}" '
                 f'width="{_w:.1f}" height="{_sz + 3:.1f}" rx="2" fill="#fff" '
                 f'opacity="0.85"/>')
        s.append(_r_txt(x_nose, y_und - _dy, _t, _sz, _wt, c=COAST, a='middle'))
    # The far-field term's boxed callout stood in the clear space beside its line. Both
    # are retired: c compensates the CWB covariate rather than measuring a site-wide
    # driver, so there is nothing spatially uniform left to call out.
    # 100 mm vertical scale bar (100 * PX_PER_MM px), far-right clear space
    _sbx = _r_ix(880); _sby = 120.0; _sbh = _rpx(100)
    s.append(f'<line x1="{_sbx:.0f}" y1="{_sby:.0f}" x2="{_sbx:.0f}" y2="{_sby+_sbh:.0f}" '
             f'stroke="#444" stroke-width="1.4"/>')
    s.append(f'<line x1="{_sbx-3:.0f}" y1="{_sby:.0f}" x2="{_sbx+3:.0f}" y2="{_sby:.0f}" '
             f'stroke="#444" stroke-width="1.4"/>')
    s.append(f'<line x1="{_sbx-3:.0f}" y1="{_sby+_sbh:.0f}" x2="{_sbx+3:.0f}" y2="{_sby+_sbh:.0f}" '
             f'stroke="#444" stroke-width="1.4"/>')
    s.append(_r_txt(_sbx - 6, _sby + _sbh / 2 + 3, '100 mm', 8.5, '600', c='#444', a='end'))

    # No crossing marker and no 'coastal deeper' / 'climate deeper' halves of the
    # axis: there is only one identified term on this reach (D-039, D-043).
    s.append(_r_txt(_r_ix(450), 78,
                    'coastal retreat is the only identified distance-dependent term',
                    10, '600', c=COAST, a='middle'))
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
    # The far-field swatch sat between these two; with it retired the undisturbed entry
    # closes up rather than leaving a gap where a legend key used to be.
    s.append(f'<line x1="{_R_NL+250}" y1="{yL}" x2="{_R_NL+276}" y2="{yL}" stroke="{REF_GREY}" '
             f'stroke-width="1.3" stroke-dasharray="2 3"/>' + _r_txt(_R_NL + 282, yL + 4, 'undisturbed table', 10.5))
    # Kept to roughly the retired sentence's length: at 9 px centred on REACH_W this
    # footer is already close to the canvas width, and a longer one runs to the edges.
    s.append(_r_txt(REACH_W / 2, REACH_H - 8,
                    'Near-shore shows the coastal retreat and erosion (ghosted); the '
                    'drawdown tapers to zero at the fitted reach. No spatially uniform '
                    'term is drawn.',
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
    resolved EDGE_DH_MM (call load_amplitudes() first).

    The title COUNTS the drivers actually drawn \u2014 the two local panels of row 2 plus
    REACH_DRIVERS on the full-width reach \u2014 rather than spelling a fixed number, so a
    driver cannot be retired while the title still claims it (D-011)."""
    cf_a, cf_ap, cf_s, cf_sp = clearfell
    cut = EDGE_DH_MM['scrape_cut_rise']
    offc = EDGE_DH_MM['scrape_offslack']
    mag_scrape = (f'cut {cut:+.0f} mm \u00b7 off-cut {offc:.0f} mm (WMC3) \u00b7 both measured')
    mag_fell = (f'{cf_a:+.2f} m over the year ({cf_ap}) \u00b7 '
                f'{cf_s:+.2f} m summer ({cf_sp})')
    # row 2 \u2014 local interventions (scrape under undisturbed | clearfell under standing
    # forest). Built here, before the title, because the title counts them.
    locals_ = [('Dune scrape', geo_scrape_after, mag_scrape, 'settles', 'observed'),
               ('Clearfell', lambda: geo_forest(True), mag_fell, 'settles', 'observed')]
    n_drivers = len(locals_) + len(REACH_DRIVERS)
    s = [f'<svg width="{GRID_W}" height="{GRID_H:.0f}" viewBox="0 0 {GRID_W} {GRID_H:.0f}" '
         f'xmlns="http://www.w3.org/2000/svg">'
         f'<rect width="{GRID_W}" height="{GRID_H:.0f}" fill="#fff"/>']
    s.append(txt(_G_ML, 24,
                 f'{count_word(n_drivers)} drivers of water-table change at Newborough',
                 size=15, w='600'))
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

    # row 3 — embedded reach panel (full width; the coastal driver alone)
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
