"""
38_coastal_transect.py — Coast-to-inland MAM transect (observational delta_0 test)
====================================================================================

Opt-in diagnostic tier (Phase 16) — wired into run_analysis.py 2026-07-08;
runs with --with-supplementary or the menu option 1 prompt. Not part of the
analytical core (ANALYTICAL_STEP_COUNT is unaffected by this or any other
opt-in step). See outputs/pipeline_manifest.json for the current step index.

Purpose (one sentence)
    Test whether the coast-to-inland MAM head gradient grows through time
    (coastal erosion — a moving boundary) or stays a constant offset with
    climate wobble (static clay-dip geometry) — a model-free, collinearity-free
    observational read on delta_0, since it measures one gradient's growth
    rather than separating collinear driver fields.

Why this works where the regression didn't
    Static substrate geometry sets a fixed transmissivity gradient -> constant
    coast-inland head difference (wobbles with climate, no trend). Coastal
    erosion is a moving boundary -> the coastal drawdown grows -> the head
    difference trends progressively more negative. Only erosion produces a
    growing gradient. So the trend in the coast-inland MAM head difference is
    an observational estimate of the ongoing delta_0; a flat-with-wobble
    difference means delta_0 is not detectable on this line.

Transect (coast -> inland, bearing ~45 deg SW->NE, ~1 km)
    CEH22  coastal anchor           ("sea/SD13", most coastal; installed ~2013
                                     per site record, though the cleaned MAOD
                                     series opens 2010 — see load_inputs())
    NW5    interior                 (C3)
    CEH40  interior, profile only   (Feb-2013 eastern scrape; sits at
                                     post-scrape offset for the whole window
                                     -> no in-series step; annotated, never in
                                     the headline metric)
    CEH41  interior, profile only   (also a scraped slack, same eastern-scrape
                                     episode as CEH40; added as a second
                                     annotated corroborator point alongside
                                     CEH40 and used, per the signed-off window
                                     rule, in the window-start computation
                                     below — never in the headline metric)
    NW4    inland anchor            (C2, ~1 km inland, outside the
                                     L ~= 894 m drawdown band)

Anchor choice already settled: CEH22 (not CEH17/19, which sit near the forest
margin and would import forest signal — the contamination this line exists to
avoid).

Window — computed, not assumed
    Start = first-valid MAM year of the HEADLINE wells only (CEH22, NW4) —
    v1.1.0 change, see changelog: v1.0.0 additionally gated the start on
    CEH41's first-valid MAM, which truncated five real years of CEH22/NW4
    data (2010-2014) for no benefit, since CEH41 never enters the headline
    metric. CEH40/CEH41 are still shown in the profile plot for whatever
    years they have data — they just no longer gate the window.
    End   = last MAM year strictly before Oct-2023 (the CEH21/CEH18 western
    scrape). MAM ends in May, so MAM 2023 precedes that cut and is included
    when present.
    Both ends are further capped by whatever data the coast/inland anchors
    actually have, so the window never extends past real coverage.

Method
    1. MAM spring mean per well per year (config.MSL_SPRING_MONTHS) — same
       seasonal frame as Script 36. No summer-minimum machinery.
    2. Water level in m AOD, read directly from the pipeline's committed
       01_wells_clean_maod.csv (upstand/datum already applied there).
    3. Headline metric: Delta_coast_inland(t) = h_CEH22(t) - h_NW4(t) per MAM
       year, both clean/unscraped wells. AR(1)-corrected OLS trend (reused,
       not reimplemented, from Script 36's _ar_corrected_slope()) -> slope in
       mm/yr with a moving-block-bootstrap CI. This slope is the
       observational delta_0 estimate; compared against Script 25's delta_0
       (forest_free, linear_capped fit), loaded live from
       OUT_25_FIT_PARAMETERS — never hardcoded.
    4. Discriminator read (written to results.txt): monotonic negative slope,
       CI excluding 0 -> erosion-consistent growing gradient; slope ~ 0 with
       residual wobble -> static geometry / delta_0 not detectable here.

Clearfell (Dec 2017) is deliberately NOT excluded from the window. The felled
compartment is in the western forest (C4/C5); forest perturbations propagate
south-westward toward Caernarfon Bay, not into this open-dune line (site
geography, fixed convention) — so the transect is not materially in the
clearfell's reach. This is a geographic argument specific to this line, not a
general claim that clearfell never matters.

Caveats (also embedded in 38_results.txt)
    - The window opens after coastal drawdown was already underway, so the
      slope is the ongoing rate over the window, not the full since-2005
      accumulation. That is fine — delta_0 is a rate.
    - One line, four/five wells: a growing gradient is erosion-specific, but a
      flat one means erosion is not detectable HERE, not that it is absent.
    - Even a growing gradient cannot separate erosion from a time-varying
      substrate effect; it separates growing (erosion-like) from static
      (geometry-like). The cored SW-NE transect (Sec. 5.7) remains the
      mechanism-resolving test.
    - CEH40 and CEH41 both carry the Feb-2013 eastern-scrape offset; used for
      profile shape only, never in the coast-inland metric, and (from v1.1.0)
      never in the window-governance calc either.

Inputs (via utils.paths):
    INT_WELLS_CLEAN_MAOD   (01_wells_clean_maod.csv)   per-well monthly m AOD
    INT_LOCATIONS          (01_locations.csv)          well E/N
    OUT_25_FIT_PARAMETERS  (25_01_panel_fit_parameters.csv) live delta_0, L

Outputs (outputs/38_coastal_transect/):
    38_transect.csv                    per-year MAM levels per well + difference
    38_transect_profile.jpg            MAM head profile, coloured by year
    38_coast_inland_difference.jpg     Delta_coast_inland(t) + AR-corrected trend
    38_results.txt                     slope +/- CI, n, discriminator read, caveats

Version: 1.3.0 (2026-07-08)
  1.3.0 (2026-07-08): wired into run_analysis.py as PHASE_16's final entry
      (tier X, exec optin) — previously committed to src/ but standalone.
      No analysis/number change. Also fixed a figure-only cosmetic bug:
      the profile-plot well-label annotations (below panel b) used a fixed
      vertical offset for every well, so CEH40 and CEH41 — which sit close
      together along the transect (~840-970 m) and both carry the two-line
      "(scraped — profile only)" tag — overlapped illegibly. Labels now
      alternate vertical offset by transect position, which separates any
      two adjacent labels regardless of their along-transect spacing. No
      change to any number, window, fit, or the underlying figure data.
  1.2.0 (2026-07-07): profile figure extended to two stacked panels.
      (a) raw absolute MAM profile (as before); (b) climate-corrected profile,
      anchor-referenced to the inland anchor NW4 (h_well - h_NW4 per year). NW4
      is erosion-free (outside the L ~= 894 m drawdown band), so subtracting it
      removes common-mode climate model-free — the same logic as the headline
      CEH22-NW4 metric, drawn across all wells. Coastal-end ordering vs year
      tightens from Spearman rho ~ -0.32 (raw) to ~ -0.87 (referenced),
      surfacing the progressive coastal drawdown that panel (a) buries under
      wet/dry year swings. CEH40/CEH41 kept in both panels, annotated as
      scraped (they carry the Feb-2013 scrape offset, so sit off the clean
      line in panel b — shown for transparency, never in any metric). Headline
      difference metric, window, trend and CI unchanged. A CWB-regression
      cross-check (not built in) confirmed the correction is safe here: spring
      CWB does not trend over 2010-2023 (VIF ~ 1.0), and the CWB-corrected
      headline slope (-28.5 mm/yr) matches the raw (-28.2 mm/yr).
  1.1.1 (2026-07-07): plotting bug fix in make_difference_plot(). The CI band
      was pivoted on the trend intercept `a` (value at year = 0); with an
      absolute-year x-axis that intercept is ~+50 m, so the band rendered ~56 m
      above the data and forced the y-axis autoscale to [-6, +50], squashing
      the real -28 mm/yr trend into a visually flat strip. Now pivoted on the
      data centroid (x_bar, y_bar). Figure only — no change to any number,
      window, or the fitted trend/CI values themselves.
  1.1.0 (2026-07-07): window-governance fix. Dropped CEH41 from the
      window-start calculation (was max(CEH22, CEH41) first-valid MAM;
      now CEH22 first-valid MAM only, since the headline metric never
      reads CEH40/CEH41 anyway). Recovers 2010-2014 (5 extra years) for the
      headline CEH22-NW4 trend: n rises 9 -> 14, bootstrap 95% CI narrows
      from [-40.7, -13.6] to roughly half that width, AR p-value drops by
      several orders of magnitude. CEH40/CEH41 remain in the profile plot,
      annotated, for whichever years they have data (2015 on) — display
      role only, unchanged from v1.0.0.
  1.0.0 (2026-07-07): initial release. Build brief
      BUILD_BRIEF_coastal_transect_MAM_2026-07-07.md, sign-off as stated above.
      CEH41 folded in as a second scraped-slack profile corroborator alongside
      CEH40 (both from the same eastern-scrape episode), consistent with the
      brief's own use of CEH41 in the window-start computation.
"""

from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter

from utils import config, paths
from utils.data_utils import normalize_well_name
from utils.console_utils import banner, phase, step, info, note, result, saved, done, warn

__version__ = "1.3.0"
VERSION = __version__
SCRIPT_ID = "38"

# --- method constants (from utils.config) -----------------------------------------
SPRING_MONTHS      = config.MSL_SPRING_MONTHS         # (3, 4, 5) — MAM
PER_WELL_MIN_YEARS = config.ACT_PER_WELL_MIN_YEARS     # min years for a trend fit
BOOT_N             = config.DIFF_BOOT_N
BOOT_BLOCK         = config.DIFF_BOOT_BLOCK
BOOT_SEED          = config.DIFF_BOOT_SEED

# --- transect definition (sign-off settled; see module docstring) -----------------
COAST_ANCHOR   = "ceh22"
INLAND_ANCHOR  = "nw4"
INTERIOR_CLEAN = ["nw5"]                 # unscraped interior well, profile only
SCRAPED_PROFILE_ONLY = ["ceh40", "ceh41"]  # eastern-scrape corroborators, profile only

ALL_TRANSECT_WELLS = [COAST_ANCHOR] + INTERIOR_CLEAN + SCRAPED_PROFILE_ONLY + [INLAND_ANCHOR]

# Window-end hard cap: last MAM year strictly before the Oct-2023 CEH21/CEH18
# western scrape. MAM (Mar-May) always precedes an October event in the same
# year, so MAM <year_of_event> is included when present.
WESTERN_SCRAPE_YEAR = 2023

# --- output paths (from utils.paths) ----------------------------------------------
OUT_DIR       = paths.DIR_38
OUT_CSV       = paths.OUT_38_CSV
OUT_FIG_PROF  = paths.OUT_38_FIG_PROFILE
OUT_FIG_DIFF  = paths.OUT_38_FIG_DIFF
OUT_TXT       = paths.OUT_38_RESULTS


# =================================================================================
# Data
# =================================================================================

def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load MAOD levels, well locations, and Script 25's live delta_0/L fit.

    delta_0 is read from the forest_free / linear_capped row of
    OUT_25_FIT_PARAMETERS (the sign-off reference fit; ~-29 mm/yr, L ~894 m
    as of the last pipeline run) — never hardcoded.
    """
    maod = pd.read_csv(paths.INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    maod.columns = [normalize_well_name(c) for c in maod.columns]

    loc = pd.read_csv(paths.INT_LOCATIONS)
    loc["key"] = loc["Match_ID"].apply(normalize_well_name)

    fit = pd.read_csv(paths.OUT_25_FIT_PARAMETERS)
    row = fit[(fit["source"] == "forest_free") & (fit["model"] == "linear_capped")]
    if row.empty:
        warn("OUT_25_FIT_PARAMETERS has no forest_free/linear_capped row — "
             "delta_0 comparison will be omitted from results.txt")
        delta0 = {}
    else:
        r = row.iloc[0]
        delta0 = dict(
            delta_0_mm_yr=float(r["delta_0_mm_yr"]),
            delta_0_se=float(r["delta_0_se"]),
            delta_0_ci_lo=float(r["delta_0_ci_lo"]),
            delta_0_ci_hi=float(r["delta_0_ci_hi"]),
            L_m=float(r["L_m"]),
        )

    missing = [w for w in ALL_TRANSECT_WELLS if w not in maod.columns]
    if missing:
        raise SystemExit(f"Transect wells missing from {paths.INT_WELLS_CLEAN_MAOD.name}: {missing}")

    return maod, loc, delta0


def spring_year_table(levels: pd.DataFrame) -> pd.DataFrame:
    """Mean MAM level per well per year (rows = year, columns = well).

    Identical convention to Script 36's spring_year_table(): int64 index
    cast guards against dtype-mismatch silently emptying joins.
    """
    spring = levels[levels.index.month.isin(SPRING_MONTHS)]
    out = spring.groupby(spring.index.year).mean(numeric_only=True)
    out.index = out.index.astype("int64")
    return out


def first_valid_year(yr: pd.DataFrame, well: str) -> int:
    s = yr[well].dropna()
    if s.empty:
        raise SystemExit(f"No valid MAM observation for '{well}' — cannot compute window")
    return int(s.index.min())


def last_valid_year(yr: pd.DataFrame, well: str) -> int:
    s = yr[well].dropna()
    if s.empty:
        raise SystemExit(f"No valid MAM observation for '{well}' — cannot compute window")
    return int(s.index.max())


def transect_distances(loc: pd.DataFrame) -> dict[str, float]:
    """Distance (m) of each transect well projected onto the CEH22 -> NW4
    line, i.e. distance-along-transect rather than raw Euclidean distance
    from the coastal anchor (the four/five wells are not perfectly
    colinear)."""
    xy = {}
    for w in ALL_TRANSECT_WELLS:
        row = loc[loc["key"] == w]
        if row.empty:
            raise SystemExit(f"'{w}' not found in {paths.INT_LOCATIONS.name}")
        xy[w] = np.array([float(row.iloc[0]["E"]), float(row.iloc[0]["N"])])

    origin = xy[COAST_ANCHOR]
    axis = xy[INLAND_ANCHOR] - origin
    axis_len = float(np.linalg.norm(axis))
    unit = axis / axis_len

    dist = {}
    for w in ALL_TRANSECT_WELLS:
        dist[w] = float(np.dot(xy[w] - origin, unit))
    return dist


# =================================================================================
# Statistics — AR(1)-corrected slope, reused from Script 36 (_ar_corrected_slope)
# =================================================================================

def ar_corrected_slope(years: np.ndarray, vals: np.ndarray) -> dict | None:
    """OLS slope of vals vs years with AR(1)-corrected t-test and moving-block
    bootstrap CI. Identical machinery to Script 36's _ar_corrected_slope()
    (itself reused from Script 32) — reproduced here rather than imported
    since it is a private helper in a numbered pipeline script, not exported
    from utils.model_utils. Returns None if fewer than PER_WELL_MIN_YEARS
    valid observations."""
    mask = np.isfinite(vals)
    x = years[mask]
    y = vals[mask]
    n = len(x)
    if n < PER_WELL_MIN_YEARS:
        return None

    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    resid = y - yhat
    sxx = float(np.sum((x - x.mean()) ** 2))
    if sxx <= 0:
        return None
    s2 = float(np.sum(resid ** 2) / (n - 2))
    se_ols = float(np.sqrt(s2 / sxx)) if s2 > 0 else 0.0

    rho = float(np.corrcoef(resid[:-1], resid[1:])[0, 1]) if n > 3 else 0.0
    rho = 0.0 if not np.isfinite(rho) else float(max(0.0, min(rho, 0.99)))

    se_adj = se_ols * np.sqrt((1 + rho) / (1 - rho)) if rho < 1 else se_ols
    n_eff = max(n * (1 - rho) / (1 + rho), 3.0)
    t = b / se_adj if se_adj > 0 else 0.0
    p_ar = float(2 * stats.t.sf(abs(t), max(n_eff - 2, 1)))
    t_ols = b / se_ols if se_ols > 0 else 0.0
    p_ols = float(2 * stats.t.sf(abs(t_ols), max(n - 2, 1)))

    rng = np.random.default_rng(BOOT_SEED)
    starts_max = n - BOOT_BLOCK
    slopes = np.empty(BOOT_N)
    for i in range(BOOT_N):
        if starts_max <= 0:
            res_bs = rng.permutation(resid)[:n]
        else:
            idx: list[int] = []
            while len(idx) < n:
                s = int(rng.integers(0, starts_max + 1))
                idx.extend(range(s, s + BOOT_BLOCK))
            res_bs = resid[np.array(idx[:n])]
        slopes[i] = np.polyfit(x, yhat + res_bs, 1)[0]
    lo, hi = np.percentile(slopes, [2.5, 97.5])
    boot_sig = bool(lo > 0 or hi < 0)

    return dict(
        n=n, slope_m_yr=float(b), slope_mm_yr=float(b * 1000.0),
        rho=rho, n_eff=float(n_eff),
        p_ar=p_ar, p_ols=p_ols, sig=bool(p_ar < 0.05),
        boot_lo_mm_yr=float(lo * 1000.0), boot_hi_mm_yr=float(hi * 1000.0),
        boot_sig=boot_sig,
    )


# =================================================================================
# Plots
# =================================================================================

def make_profile_plot(yr: pd.DataFrame, years: list[int], dist: dict[str, float],
                       fig_path) -> None:
    """Two-panel coast-to-inland MAM head profile (m AOD vs distance-along-transect).

    Panel (a) — RAW absolute MAM level per well per year. Each year's whole
    line rides up/down with that year's wetness (common-mode climate), which is
    an order of magnitude larger than the ~28 mm/yr erosion signal, so the
    year-coloured lines do NOT stack in order — the erosion is buried.

    Panel (b) — CLIMATE-CORRECTED, anchor-referenced to the inland anchor NW4:
    h_well(t) - h_NW4(t). NW4 sits outside the L ~= 894 m drawdown band and is
    effectively erosion-free, so its year-to-year movement IS the climate
    signal; subtracting it removes common-mode climate model-free (same logic
    as the headline CEH22-NW4 metric, just drawn across all wells). The coastal
    end then shows its progressive relative drawdown, ordered by year.

    CEH40/CEH41 are kept in BOTH panels, annotated as scraped: they carry the
    Feb-2013 eastern-scrape offset, so in panel (b) they sit off the clean
    coast->inland line by roughly a constant amount — shown for transparency,
    not used in any metric.
    """
    order = sorted(ALL_TRANSECT_WELLS, key=lambda w: dist[w])
    xs = [dist[w] for w in order]

    cmap = plt.get_cmap("viridis")
    norm = plt.Normalize(vmin=min(years), vmax=max(years))

    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(8.2, 9.8), sharex=True)

    # ---- Panel (a): raw absolute profile ------------------------------------
    for y in years:
        row = yr.loc[y, order] if y in yr.index else None
        if row is None or row.isna().any():
            continue
        ax_a.plot(xs, row.values, "-o", color=cmap(norm(y)), lw=1.3, ms=4,
                  alpha=0.85, zorder=2)
    ax_a.set_ylabel("MAM mean water level (m AOD)")
    ax_a.set_title("(a) Raw absolute profile \u2014 dominated by common-mode climate",
                   fontsize=11, loc="left")
    ax_a.grid(alpha=0.3)

    # ---- Panel (b): climate-corrected (anchor-referenced to NW4) -------------
    for y in years:
        if y not in yr.index:
            continue
        row = yr.loc[y, order]
        if pd.isna(row.get(INLAND_ANCHOR)):
            continue
        ref = row - row[INLAND_ANCHOR]
        if ref.isna().any():
            continue
        ax_b.plot(xs, ref.values, "-o", color=cmap(norm(y)), lw=1.3, ms=4,
                  alpha=0.85, zorder=2)
    ax_b.axhline(0.0, color="dimgray", lw=0.8, ls="--", zorder=1)
    ax_b.set_ylabel("MAM level relative to inland anchor NW4 (m)")
    ax_b.set_title("(b) Climate-corrected profile \u2014 anchor-referenced to NW4",
                   fontsize=11, loc="left")
    ax_b.set_xlabel("Distance along transect, coast \u2192 inland (m)")
    ax_b.grid(alpha=0.3)

    # ---- shared well annotations (below panel b) ----------------------------
    # v1.3.0: alternate the vertical offset by transect position so that any
    # two adjacent wells' labels stay separated regardless of how close they
    # sit along the transect. Previously all labels used a single fixed
    # offset, which let CEH40 and CEH41 (~840-970 m apart, both carrying the
    # two-line "(scraped -- profile only)" tag) overlap illegibly.
    for i, w in enumerate(order):
        label = w.upper()
        if w == COAST_ANCHOR:
            label += "\n(coastal anchor)"
        elif w == INLAND_ANCHOR:
            label += "\n(inland anchor, =0 ref)"
        elif w in SCRAPED_PROFILE_ONLY:
            label += "\n(scraped \u2014 profile only)"
        y_offset = -34 if i % 2 == 0 else -52
        ax_b.annotate(label, (dist[w], ax_b.get_ylim()[0]), xytext=(0, y_offset),
                      textcoords="offset points", ha="center", fontsize=7.5,
                      color="dimgray")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=(ax_a, ax_b), pad=0.02)
    cbar.set_label("Year (MAM)")

    fig.suptitle("Coast-to-inland MAM head profile", fontsize=13, x=0.09, ha="left")
    fig.savefig(fig_path, dpi=150, bbox_inches="tight", pil_kwargs={"quality": 85})
    plt.close(fig)


def make_difference_plot(years: np.ndarray, diff: np.ndarray, fit: dict | None,
                          delta0: dict, fig_path) -> None:
    """Delta_coast_inland(t) time series with AR-corrected trend + CI band."""
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(years, diff, "o", color="#1f4e79", ms=6, zorder=3,
            label="Delta_coast_inland (CEH22 \u2212 NW4)")

    if fit is not None:
        b, a = np.polyfit(years, diff, 1)
        x_line = np.linspace(years.min(), years.max(), 50)
        y_line = a + b * x_line
        ax.plot(x_line, y_line, "-", color="#c0392b", lw=2, zorder=2,
                label=f"AR-corrected trend: {fit['slope_mm_yr']:+.1f} mm/yr "
                      f"[{fit['boot_lo_mm_yr']:+.1f}, {fit['boot_hi_mm_yr']:+.1f}]")
        # visual CI band from the bootstrap slope bounds, pivoted on the data
        # CENTROID (x_bar, y_bar) — the point every slope line passes through.
        # (v1.1.1 fix: was pivoted on `a`, the intercept at year = 0; since the
        # x-axis is absolute years (~2017) that intercept is ~+50 m, which drew
        # the band ~56 m above the data and blew the y-axis autoscale up to
        # [-6, +50], squashing the real trend into a flat-looking strip.)
        y_bar = float(np.mean(diff))
        y_lo = y_bar + (fit['boot_lo_mm_yr'] / 1000.0) * (x_line - x_line.mean())
        y_hi = y_bar + (fit['boot_hi_mm_yr'] / 1000.0) * (x_line - x_line.mean())
        ax.fill_between(x_line, y_lo, y_hi, color="#c0392b", alpha=0.12, zorder=1)

    if delta0:
        note_str = (f"Script 25 delta_0 (forest_free, linear_capped): "
                    f"{delta0['delta_0_mm_yr']:+.1f} mm/yr")
        ax.text(0.02, 0.02, note_str, transform=ax.transAxes, fontsize=8.5,
                color="dimgray", va="bottom", ha="left")

    ax.set_xlabel("Year")
    ax.set_ylabel("Coast \u2212 inland MAM head difference (m)")
    ax.set_title("Coast-inland MAM gradient over time", fontsize=13, loc="left")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8.5, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=150, bbox_inches="tight", pil_kwargs={"quality": 85})
    plt.close(fig)


# =================================================================================
# Main
# =================================================================================

def main() -> int:
    banner(SCRIPT_ID, "Coast-to-inland MAM transect (observational delta_0 test)", VERSION)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    phase(1, "Load inputs")
    maod, loc, delta0 = load_inputs()
    yr = spring_year_table(maod)
    info(f"spring-year table: {yr.shape[1]} wells x {yr.shape[0]} years "
         f"({int(yr.index.min())}\u2013{int(yr.index.max())})")
    dist = transect_distances(loc)
    for w in sorted(ALL_TRANSECT_WELLS, key=lambda w: dist[w]):
        info(f"  {w.upper():6s}  dist={dist[w]:6.1f} m")

    phase(2, "Compute window")
    start = first_valid_year(yr, COAST_ANCHOR)
    end_cap = min(last_valid_year(yr, COAST_ANCHOR), last_valid_year(yr, INLAND_ANCHOR),
                  WESTERN_SCRAPE_YEAR)
    end = end_cap
    result("window start (CEH22 first-valid MAM; CEH41 no longer gates this)", str(start))
    result("window end (last MAM before Oct-2023, capped by data)", str(end))
    if end <= start:
        raise SystemExit(f"Degenerate window [{start}, {end}] — check inputs")

    years_all = [y for y in range(start, end + 1) if y in yr.index]
    sub = yr.loc[years_all, [COAST_ANCHOR, INLAND_ANCHOR]].dropna()
    n_pts = len(sub)
    result("actual n of MAM points in window", str(n_pts))
    if n_pts < len(years_all):
        note(f"{len(years_all) - n_pts} candidate year(s) dropped for a missing "
             f"{COAST_ANCHOR.upper()} or {INLAND_ANCHOR.upper()} MAM observation")

    phase(3, "Fit AR-corrected trend on Delta_coast_inland(t)")
    years_arr = sub.index.to_numpy(dtype=float)
    diff_arr = (sub[COAST_ANCHOR] - sub[INLAND_ANCHOR]).to_numpy(dtype=float)
    fit = ar_corrected_slope(years_arr, diff_arr)

    lines: list[str] = []
    lines.append(f"=== Script 38 — coast-to-inland MAM transect ({start}\u2013{end}) ===")
    lines.append(f"Wells: coastal anchor {COAST_ANCHOR.upper()}, inland anchor "
                 f"{INLAND_ANCHOR.upper()}, interior {', '.join(w.upper() for w in INTERIOR_CLEAN)}, "
                 f"scraped profile-only {', '.join(w.upper() for w in SCRAPED_PROFILE_ONLY)}")
    lines.append(f"Window: {start}\u2013{end}  (n = {n_pts} MAM points)")
    lines.append("")

    if fit is None:
        warn(f"Fewer than PER_WELL_MIN_YEARS={PER_WELL_MIN_YEARS} valid points "
             f"(n={n_pts}) — trend not fit. Result reported as inconclusive.")
        lines.append(f"TREND: not fit — only {n_pts} MAM points, below the "
                     f"PER_WELL_MIN_YEARS={PER_WELL_MIN_YEARS} gate used elsewhere "
                     f"in the pipeline.")
        lines.append("DISCRIMINATOR READ: inconclusive (insufficient data).")
        discriminator = "inconclusive (insufficient data)"
    else:
        result("Delta_coast_inland trend", f"{fit['slope_mm_yr']:+.2f} mm/yr "
               f"(AR p={fit['p_ar']:.3f}, OLS p={fit['p_ols']:.3f})")
        result("bootstrap 95% CI", f"[{fit['boot_lo_mm_yr']:+.2f}, {fit['boot_hi_mm_yr']:+.2f}] mm/yr")
        lines.append(f"TREND (AR(1)-corrected OLS): {fit['slope_mm_yr']:+.2f} mm/yr")
        lines.append(f"  AR p-value: {fit['p_ar']:.4f}   OLS p-value: {fit['p_ols']:.4f}")
        lines.append(f"  rho (lag-1 residual autocorr): {fit['rho']:.3f}   n_eff: {fit['n_eff']:.1f}")
        lines.append(f"  Bootstrap 95% CI: [{fit['boot_lo_mm_yr']:+.2f}, {fit['boot_hi_mm_yr']:+.2f}] mm/yr "
                     f"({'significant' if fit['boot_sig'] else 'not significant'})")
        lines.append("")

        if delta0:
            lines.append(f"Comparison — Script 25 delta_0 (forest_free, linear_capped fit): "
                         f"{delta0['delta_0_mm_yr']:+.2f} mm/yr "
                         f"[{delta0['delta_0_ci_lo']:+.2f}, {delta0['delta_0_ci_hi']:+.2f}], "
                         f"L = {delta0['L_m']:.0f} m")
            result("Script 25 delta_0 (forest_free, linear_capped)",
                   f"{delta0['delta_0_mm_yr']:+.2f} mm/yr")
            lines.append("")

        # Discriminator read
        ci_excludes_zero = fit["boot_lo_mm_yr"] > 0 or fit["boot_hi_mm_yr"] < 0
        monotonic_negative = fit["slope_mm_yr"] < 0
        if monotonic_negative and ci_excludes_zero:
            discriminator = ("erosion-consistent growing gradient — the "
                             "coast-inland MAM head difference trends progressively "
                             "more negative, with the 95% CI excluding zero, consistent "
                             "with a moving coastal boundary rather than a static, "
                             "climate-wobbling offset.")
        elif not ci_excludes_zero:
            discriminator = ("delta_0 not detectable on this line — the coast-inland "
                             "MAM head difference does not show a trend distinguishable "
                             "from zero over this window (CI includes zero); this does "
                             "not mean coastal erosion is absent, only that this "
                             "particular four/five-well line and window cannot resolve "
                             "it observationally.")
        else:
            discriminator = ("unexpected sign — the coast-inland MAM head difference "
                             "trends progressively more POSITIVE with the CI excluding "
                             "zero. This does not match the erosion-consistent "
                             "prediction and warrants Martin's attention before use.")
            warn("Coast-inland trend is significantly POSITIVE — does not match the "
                 "erosion-consistent prediction. Flag for review before report use.")

        lines.append(f"DISCRIMINATOR READ: {discriminator}")

    # --- climate-corrected profile ordering diagnostic (panel b support) ------
    ce_raw = yr.loc[[y for y in yr.index if start <= y <= end], COAST_ANCHOR]
    ce_ref = (yr.loc[ce_raw.index, COAST_ANCHOR] - yr.loc[ce_raw.index, INLAND_ANCHOR]).dropna()
    if len(ce_ref) >= 3:
        rho_raw = stats.spearmanr(ce_raw.dropna().values, ce_raw.dropna().index.values).correlation
        rho_ref = stats.spearmanr(ce_ref.values, ce_ref.index.values).correlation
        lines.append("")
        lines.append("CLIMATE-CORRECTED PROFILE (figure panel b, anchor-referenced to NW4):")
        lines.append(f"  Coastal-end ordering vs year (Spearman rho):")
        lines.append(f"    raw absolute CEH22:            rho = {rho_raw:+.3f}")
        lines.append(f"    anchor-referenced CEH22-NW4:   rho = {rho_ref:+.3f}")
        lines.append("  Referencing to the erosion-free inland anchor removes common-mode "
                     "climate model-free; a rho closer to -1 means a cleaner monotonic "
                     "coastal drawdown through time.")

    lines.append("")
    lines.append("CAVEATS:")
    lines.append(f"  - Window opens {start}, after coastal drawdown was already "
                 f"underway; the slope is the {start}\u2013{end} ongoing rate, not "
                 f"the full since-2005 accumulation. This is fine — delta_0 is a rate.")
    lines.append("  - One line, four/five wells: a growing gradient is erosion-specific, "
                 "but a flat one means erosion is not detectable HERE, not that it is absent.")
    lines.append("  - Even a growing gradient cannot separate erosion from a "
                 "time-varying substrate effect; it separates growing (erosion-like) "
                 "from static (geometry-like). The cored SW-NE transect (Sec. 5.7) "
                 "remains the mechanism-resolving test.")
    lines.append("  - CEH40 and CEH41 both carry the Feb-2013 eastern-scrape offset; "
                 "used for profile shape only, never in the coast-inland metric.")
    lines.append("  - Clearfell (Dec 2017) is deliberately not excluded from the window: "
                 "the felled compartment is in the western forest (C4/C5), and forest "
                 "perturbations propagate south-westward toward Caernarfon Bay, not into "
                 "this open-dune line (site-geography convention) — a geographic "
                 "argument specific to this transect, not a general one.")

    phase(4, "Render figures")
    all_years_present = sorted(int(y) for y in yr.index
                                if not yr.loc[y, ALL_TRANSECT_WELLS].isna().any())
    profile_years = [y for y in all_years_present if start <= y <= end]
    if not profile_years:
        warn("No years with complete data across all transect wells in the window — "
             "widening profile plot to any year with full coverage")
        profile_years = all_years_present
    make_profile_plot(yr, profile_years, dist, OUT_FIG_PROF)
    saved(OUT_FIG_PROF)

    make_difference_plot(years_arr, diff_arr, fit, delta0, OUT_FIG_DIFF)
    saved(OUT_FIG_DIFF)

    phase(5, "Write outputs")
    out_df = yr.loc[[y for y in yr.index if start <= y <= end], ALL_TRANSECT_WELLS].copy()
    out_df["diff_coast_inland_m"] = out_df[COAST_ANCHOR] - out_df[INLAND_ANCHOR]
    out_df.index.name = "year"
    out_df.to_csv(OUT_CSV)
    saved(OUT_CSV, extra=f"{len(out_df)} years")

    OUT_TXT.write_text("\n".join(lines) + "\n")
    saved(OUT_TXT)

    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
