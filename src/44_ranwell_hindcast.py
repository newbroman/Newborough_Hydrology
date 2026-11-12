#!/usr/bin/env python3
"""
44_ranwell_hindcast.py — Ranwell's 1951–53 water-table record against the
modern network and the SSM hindcast (D-145)
==========================================================================

Ranwell (1959) read seventeen dipwells fortnightly from February 1951 to August
1953 and printed three of the series (Fig. 4: Sites 1, 4, 8) and seven sets of
monthly ranges (Fig. 7: Sites 1, 4, 11, 12, 13, 16, 18), each site levelled to
OD. Those figures were digitised on 2026-09-08 (data/RANWELL_PROVENANCE.md) and
this script asks three things of them, in decreasing order of what the data can
bear.

Q1 — Does the SSM hindcast 1951–53?  Each Ranwell site with a printed series is
  paired with the modern wells that share its DEM basin (Script 43 Route T) and
  lie within RANWELL_PAIR_MAX_M. Each paired well's committed Model A
  coefficients are driven by RAF Valley climate from the start of the record
  (utils.model_utils.simulate_ssm, exactly as Script 39), and the modelled
  mid-month level is set against Ranwell's monthly-mean reading AFTER REMOVING
  THE MEAN OFFSET — the two are not at the same point. r, NSE-after-offset and
  the seasonal range say whether the coefficients reproduce the dynamics of
  fifty-four years earlier. Those coefficients are fitted on the last 100 months
  of each well's record (2017-11 to 2026-02), NOT on 2005–26 as this docstring
  claimed before 2026-11-08; two further windows (pre-2018, whole record) are
  refitted and run alongside. The nearest paired well is the headline;
  every paired well is written (the spread is the sensitivity).
  Since 1.13.0 (D-332) the headline keys and figures are MODEL B, Script 03's
  free-intercept coefficients (03_16) run at DRAINAGE_DATUM - alpha/beta_3; Model A
  at the fixed floor and Model A at each well's depth to mean high water (ground less
  Script 01b's tide_mhw_m) are tested alternatives (keys *_model_a, *_mhw). The
  pairing, Q2's climate-only expectation, Q4's depth changes and Q5's pre-planting
  hindcast are Model B too, with Model A in *_model_a columns and keys (44_04 alone keeps
  its unsuffixed columns as Model A, because Script 50 reads them).

Q2 — Has the slack water table moved since 1951–53?  Ranwell's mean level (m OD)
  at each of the eight printed sites against the modern mean water-table
  surface at that point (Script 01b's kriged mean-state surface, D-205: the
  water table is kriged wherever it is sampled; until 2026-09-27 an IDW of
  per-well modern means), minus the climate-only expectation for the two spans from
  the Q1 hindcast at the headline well. Four error terms in quadrature per site:
  the leave-one-well-out error of the kriged surface at the site's nearby wells; the surface
  gradient times the positional uncertainty (Script 43 Route H); the sampling
  difference between a reading mean and a mid-range mean; and the datum offset's
  MAD (Route H). Sites combine by inverse variance, with the chi-square per
  degree of freedom reported so excess scatter is visible.

Q3 — The rate.  Delta over the interval between the record midpoints, per site
  and combined, and whether it is resolved (|Delta| > 2 sigma). Two combined
  rows: every site, and the sites whose modern surface is CONSTRAINED — a
  leave-one-out error at or below RANWELL_LOO_MAX_M — which is a property of
  the modern network, not of any site by name. Distance to the 2006 coastline
  and the measured 1899–2026 shoreline retreat (Script 40) travel with each
  site as context; Ranwell recorded the seaward ends of the open slacks as
  accreting, and the modern surface is thinnest there. Each site also carries
  the change Script 25's headline coastal-retreat fit (RANWELL_COASTAL_FIT) would
  give at its distance from the eroding shoreline over the interval
  (coastal_expectation_extrapolated_m: the 2005-2026 rate carried across 66
  years, which the fit does not cover), and a third combined row takes the
  sites beyond the fitted reach (COMBINED_BEYOND_REACH).

Q4 — Do the slack floors record a water table?  (T-71, D-208.)  Each classified
  reference well's floor (01_locations ground_elev_m) is set against the depths of
  its full-record mean, its spring level (Script 26 MSL_m_bg, D-189/D-207) and its
  annual minimum (MIN_m_bg) below it; the inland baseline is the median over the
  open-dune clusters (SLACK_FLOOR_BASELINE_CLUSTERS) at or beyond the coastal reach
  L, and each well's excess over it is set against the MODELLED retreat response
  (Script 20 coastal_h0_per_metre × Script 40's 1899–2026 frontage-median retreat,
  shaped by the same linear-capped form as Q2's coastal expectation; the
  exponential form is a flagged sensitivity column, quoted nowhere). Ranwell's
  sites carry his own floor, recovered as level + depth from the digitised
  readings, and the 1951–53 depths below it, so the depth change at each
  headline well is read floor-to-floor with no interpolation and no OD datum —
  a comparison that complements Q2 and does not replace it.

What it does NOT establish: a point-to-point comparison (the wells are not
where the pipes were); coefficient stationarity (Script 39's caveat applies,
so a beta_1-scaling envelope is written); anything about the BS slack, for
which Ranwell printed no series; anything under the forest canopy, where no
Ranwell site lies. Q5 (T-72) sets the forest wells' excess against the modelled canopy
drawdown, the felling history, the one drainage channel and the floor relief; it
writes what discriminates and what does not, and Martin rules before any text is
written. Under-canopy flooding it cannot see (T-78).

Registered tier A, default, after Script 43 (it reads 43_01 and 43_07). Reads
three raw inputs no pipeline step produces (D-145 records the exception, as
D-051 did for Script 39); SKIPS cleanly when they are absent.

Inputs (via utils.paths):
    RANWELL_LEVELS, RANWELL_RANGES, RANWELL_PARC_MAWR_RAIN   (data/, digitised)
    OUT_43_SITES, OUT_43_WELL_BASINS, OUT_43_DIAGNOSTIC     (Script 43 v2)
    INT_CLIMATE, INT_MASTER_DATA, INT_WELLS_CLEAN, INT_LOCATIONS
    INT_CLUSTER_STATS, OUT_26_ANNUAL_PER_WELL, OUT_20_REPORT_NUMBERS      (Q4)
    DATA_KML_COAST_2006, OUT_40_EPOCH_SERIES                  (coastal context)
    DATA_COASTLINE_ERODING, OUT_25_FIT_PARAMETERS              (coastal expectation)

Outputs (outputs/44_ranwell_hindcast/):
    44_01_ranwell_readings.csv        Fig. 4 readings joined to site, basin, headline well
    44_02_ranwell_monthly_ranges.csv  Fig. 7 ranges joined to site, basin, mid-range level
    44_03_hindcast_series.csv         monthly observed mean vs modelled, per site x paired well
    44_04_hindcast_metrics.csv        r, NSE after offset, ranges, timing, beta_1 envelope
    44_05_level_change.csv            per-site Delta with the four error terms; COMBINED rows
    44_06_climate_check.csv           Parc Mawr (Fig. 2) vs RAF Valley, 1950-53
    44_07_hindcast.png                the printed series against the hindcast (annotated; MS)
    44_07b_hindcast_report.png        the same, caption-free, for the report
    44_08_level_change.png            Ranwell mean vs modern surface, per site
    44_09_slack_floor_datum.csv       Q4: floor, depths, baseline, excess, retreat terms; Ranwell sites
    44_09_slack_floor_datum.png       Q4: annual minimum below the floor vs distance to the eroding shoreline
    44_10_forest_floor_excess.csv     Q5: the forest wells' excess against drawdown, felling, channel, relief
    44_10_forest_floor_excess.png     Q5: residual by felling history
    44_report_numbers.csv
"""

from __future__ import annotations

__version__ = "1.13.0"  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2a). Model B is the headline: the
#   ranwell_hindcast_* keys keep their names and now carry Model B (03_16 at DRAINAGE_DATUM - alpha/beta_3), with
#   Model A at 3.7 m as <key>_model_a and Model A at each well's depth to mean high water as <key>_mhw (Addendum 3,
#   Scenario 3); new ranwell_hindcast_nse_median_all_pairings* and n_pairings*. Bounded beta_3 fits (model_utils
#   1.14.0) are kept and counted (ranwell_model_b_bound_binds_n*); a well with no datum below ground is counted out
#   (ranwell_model_b_excluded_datum_n*). 44_04 gains B's beta_1 envelope, the MHW form's scores and B's climate-only
#   expectation (columns only: Q2 still uses A's); 44_03 gains model_mhw_level_m_od. 44_07/44_07b show B only, one
#   legend below the panels, each site's offset in its title. Existing 44_04 columns keep Model A (Script 50 reads them).
#   Then, on the coordinator's ruling (D-332, Martin 2026-11-12 "essentially everything moves to model B"): pairing rests
#   on Model B (03_16 defined), not on Model A's beta_3 (set unchanged); Q2's climate-only expectation, every delta,
#   the combined rows and Q4's depth changes (44_05, 44_09) are Model B with *_model_a columns and keys; Q5's
#   pre-planting hindcast uses 03_16's own coefficients/p-values and centroids at their implied datums (44_10 *_model_a
#   for the master store and 03_03 centroids). 03_03 is now read only for Q5's Model A sensitivity.
# 1.12.1  # Hollingham (2026) — 2026-11-10. Model B is looked up by the NORMALISED well name
#   (utils.data_utils.normalize_well_name), as Script 50 does. 03_16 spells l7 as L7, so the case-sensitive lookup
#   missed and the headline Model B Ranwell score rested on 10 pairings, not 11. Martin 2026-11-10.
# 1.12.0 — 2026-10-10 (T-122, D-254). The pre-planting sensitivity runs each
#   forest well on the open-dune analogue of its cluster (config.PRECANOPY_ANALOGUE: C3 for C4, C2 for C5), not
#   C2 for every forest well (Martin 2026-10-10 12:42, 17:11 "replace"). Columns *_c2_m become *_analogue_m with
#   preplant_analogue_cluster; the uncited key ..._min_median_C4_c2_m becomes ..._C4_analogue_m, and C5's
#   analogue keys are added. The own-coefficient keys (cited in report9) do not change.
# 1.11.0  # Hollingham (2026) — 2026-10-10. report9 SS4.14.2's "elevated" open-dune wells within the
#   coastal reach follow a stated rule: excess over the inland baseline above config.RANWELL_ELEVATED_K_SIGMA x the
#   combined 1951-53 standard error. Rows slack_floor_reach_* (counts, threshold, excess range). Emit-only.
# 1.10.0  # Hollingham (2026) — 2026-10-10. Emit-first (spec NRG_spec_emit_first_report9_2026-10-09):
#   report9 quotes the range of r over every same-basin pairing (not only the headline pairings) and the largest
#   climate-only expectation over the compared sites; new rows ranwell_hindcast_r_min_all_pairings,
#   ranwell_hindcast_r_max_all_pairings (44_04, all rows) and ranwell_climate_expectation_abs_max_m (44_05 site
#   rows, largest |climate_expectation_m|). Emit-only; nothing already emitted moves.
# 1.9.1  # Hollingham (2026) — 2026-10-03. A well recorded as open in 1989 in
#   data/canopy_history.csv is kept out of the felling groups (group open_1989) even where a felling outline takes
#   it in: NW9, broadleaf and never felled, sits about 5 m inside felling_1998_1 (Martin: "NW9 exclude from group").
# 1.9.0  # Hollingham (2026) — 2026-10-03. The felling group is named from the recorded
#   year in data/canopy_history.csv (felled 1993, replanted 1998 — Martin, 2026-10-03; it was a literal
#   "felled_1995"), and the forest-floor groups gain their ranges and a test of "does not differ" (Martin:
#   "write an output for does not differ"): forest_floor_felled_vs_canopy_mw_p / _differs, at
#   FOREST_FLOOR_GROUP_TEST_P. report9's sentence then binds to a committed value.
# 1.8.1  # Hollingham (2026) — 2026-10-02. compare() moved, unchanged, to
#   utils/hindcast_utils.compare_offset_censored() for Script 50 E9 (D-229); outputs identical.
# 1.8.0  # Hollingham (2026) — 2026-09-30. T-96 batch 3: emit the smallest and
#   largest distance to the nearest in_forest well over each of Ranwell's sketch_slack groups
#   (ranwell_dist_nearest_forest_well_m_{group}_min / _max, from the per-site rows 1.7.0 added;
#   report10 §5.7.9 "the Clwt Gwlyb sites, which lie 120-200 m from the nearest forest wells" is
#   the CG pair). Groups come from 43_01 sketch_slack, not typed site numbers. Nothing already
#   emitted moves.
# 1.7.0  # Hollingham (2026) — 2026-09-29. T-96: report numbers also carry
#   the 2-sigma bounds of each combined level change (ranwell_delta_lower_2sigma_m_{row},
#   ranwell_delta_upper_2sigma_m_{row}: delta -/+ 2 x its standard error, the same 2 sigma the
#   ranwell_resolved_* flag already uses; report10 §5.7.9 "a fall larger than about 0.3 m is
#   excluded ... a rise larger than about 0.1 m"), and each compared site's distance to the nearest
#   in_forest well (ranwell_dist_nearest_forest_well_m_site{n}, placed position against 01_locations
#   E/N; report10 §5.7.9 "the Clwt Gwlyb sites, which lie 120-200 m from the nearest forest wells").
#   Moved here from Script 43 (T-96): 43 carries no forest flag, 44 already holds both inputs.
#   Nothing already emitted moves.
# 1.6.0  # Hollingham (2026) — 2026-09-29. Q5 — the forest floors (T-72, D-209; Martin: one
#   drainage channel, the line along the village-to-beach road between ceh14 and ceh13 = Features.kml "Line 23";
#   no pre-planting map; ceh2 and ceh16 ploughed; a figure). 44_10_forest_floor_excess.csv: per in_forest
#   reference well the 44_09 excess/residual, the modelled canopy drawdown (Script 20 dd_mm) and the ratio, the
#   felling era (canopy_history) and ground preparation (data/forest_ground_prep.csv), distance to the channel
#   and its bed above the floor, floor microrelief within FLOOR_RELIEF_RADIUS_M, and the head against the
#   HEAD_DEM_HEADLINE_SMOOTHING_M-smoothed ground (for the record; does not resolve); the litter allowance
#   FOREST_LITTER_MAX_M as a lower bound on the mineral-floor excess; the climate-only hindcast of the
#   pre-planting window (PREPLANT_WINDOW, simulate_ssm from 1930 as Q1) and the retreat since it on two
#   bases (Martin: 1953-60; 1899-2006 rate with a sensitivity). 44_10 figure. Report
#   numbers forest_floor_*. Nothing already emitted moves.
# 1.5.0  # Hollingham (2026) — 2026-09-29. Q4: the modern floor at a Ranwell site is the
#   site's LOCAL FLOOR from Script 43 2.1.0 (43_01 local_floor_m: the RANWELL_FLOOR_PCT percentile within
#   RANWELL_FLOOR_WINDOW_M of the placed position), not the headline well's floor (Martin, 2026-09-29: the pipe
#   positions are not known to a well; "an average of the slack floor is probably the best we can do"; the
#   definition test in 43_report_numbers ranwell_floor_fit_* picks the local floor: lowest RMSE against his
#   levelled heights at the placed sites). Site rows: slack_floor_lowering_m (his floor minus the local floor),
#   modern_depth_local_cc_m (local floor minus the kriged mean level at the site, climate-adjusted as Q2) and
#   depth_change_m against his mean depth; the floor-mask mean carried as a sensitivity; the well-pairing
#   columns kept as pairedwell_* (diagnostic). Report numbers re-keyed: ranwell_floor_lowering_site{n}_m and
#   ranwell_depth_change_site{n}_m are now the local-floor quantities; inland medians and the inland-subset
#   fit test added; the well-pairing keys carry pairedwell in the name.
# 1.4.1  # Hollingham (2026) — 2026-09-29. Q4 fix: the cluster column stays integer (nullable
#   Int64) after the Ranwell site rows join the frame, so the per-cluster report-number keys read _C4_, not
#   _C4.0_, and 44_09 carries cluster as an integer. Values unchanged; keys renamed. Also paired_floor_lowering_m
#   (site rows) and ranwell_floor_lowering_site{n}_m: Ranwell's floor minus the modern well's, the number report10
#   §5.7.9 quotes for Site 8.
# 1.4.0  # Hollingham (2026) — 2026-09-29. Q4 — the slack floors as a former water
#   table (T-71, D-208; Martin's rulings 2026-09-29: baseline C1–C3 beyond L, medians, both retreat forms with
#   the exponential flagged as sensitivity, a figure). 44_09_slack_floor_datum.csv: per well the floor, the
#   depths of the full-record mean, the D-189/D-207 spring and the annual minimum below it, the inland
#   baseline and excess, the MODELLED retreat expectation (linear-capped, as Q2), the residual, the implied
#   retreat (ill-conditioned near L: its sigma is written beside it) and years; per Ranwell site his floor (level + depth) and 1951–53 depths, and the like-for-like
#   depth change at the headline well. 44_09_slack_floor_datum.png. Nothing already emitted moves.
# 1.3.0  # Hollingham (2026) — 2026-09-27. Coastal expectation (D-145, D-205; Martin: "We
#   should name site 8 - could it be affected by coastal erosion?", "go ahead"). Each site carries its distance
#   to the eroding shoreline (coastline_eroding_hwm.geojson, the Script 25 datum) and what Script 25's
#   headline fit (RANWELL_COASTAL_FIT) would give there over the interval: coastal_expectation_m, flagged in
#   its name as an extrapolation of the 2005-2026 rate across the whole interval. A third combined row,
#   COMBINED_BEYOND_REACH, takes the sites beyond the fitted reach L. Nothing already emitted moves.
# 1.2.0  # Hollingham (2026) — 2026-09-27. The modern water table at each Ranwell site
#   is read from Script 01b's kriged mean-state surface, and its uncertainty term is the RMSE of
#   that surface's leave-one-well-out errors at the site's nearby wells (D-205 extended; spec NRG_spec_water_table_kriged_everywhere rev 2; Martin:
#   "include all of them"). idw_at / loo_rmse retired; surface_gradient differences the kriged surface;
#   the kriging SE is recorded (kriging_se_m) but not used: on this network it overstates the
#   leave-one-out error several-fold; columns modern_idw_* -> modern_kriged_*, contributing_* -> nearby_* (RANWELL_NEAR_K / _RADIUS_M, kept for
#   the record and the climate-expectation fallback). The D-145 level changes move.
# 1.1.2  # Hollingham (2026) — 2026-09-08. Report render: legend on the
#   top panel only — on the lower panels it covered the August 1951 minimum.
#   1.1.1 (2026-09-08): Forcing check: restore the
#   "month" index name after the Parc Mawr / RAF Valley join — pandas 2.1 on the
#   L14 drops it and the span filter raised KeyError. No number moves.
#   1.1.0 (2026-09-08): Report render of the
#   hindcast figure: 44_07b_hindcast_report.png, the same three panels drawn by
#   the same function with report=True — no suptitle, panel titles name site,
#   slack and paired well only, legend without values (captions live in the
#   document text). 44_07 unchanged; no number moves.
#   1.0.0 (2026-09-08): first issue (D-145).

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from utils import config, paths  # noqa: E402
from utils.model_utils import (simulate_ssm,                           # noqa: E402
                               fit_ssm, fit_ssm_intercept,             # noqa: E402  (J-6)
                               dry_bounds)                             # noqa: E402  (1.13.0, MHW form)
from utils.hindcast_utils import compare_offset_censored  # noqa: E402
from utils.console_utils import banner, phase, step, info, warn, saved, note  # noqa: E402
from utils.render_utils import apply_house_style, render_figure  # noqa: E402
from utils.data_utils import normalize_well_name  # noqa: E402  (1.12.1)

SCRIPT_ID = "44"
VERSION = __version__
DATUM = config.DRAINAGE_DATUM
# J-6: minimum aligned months for an alternative-window refit. Matches Script 39.
MIN_FIT_OBS = 36
BETA_COLS = ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage")
SPAN = pd.Period(config.RANWELL_HINDCAST_SPAN[0], "M"), pd.Period(config.RANWELL_HINDCAST_SPAN[1], "M")
B3_MIN = config.MODEL_B_BETA3_MIN       # 1.13.0 (D-332): Model B's beta_3 lower bound (model_utils 1.14.0)


def mhw_level() -> float:
    """Mean high water (m OD), Script 01b's tide_mhw_m, as Scripts 39, 48 and 50 read it; NaN if absent."""
    try:
        rn = pd.read_csv(paths.OUT_01B_REPORT_NUMBERS)
        v = rn.loc[rn["Parameter"] == "tide_mhw_m", "Value"]
        return float(v.iloc[0]) if len(v) else np.nan
    except (OSError, KeyError, ValueError):
        return np.nan


def fixed_floor_fit(h: pd.Series, cl: pd.DataFrame, well: str, datum: float):
    """Model A at a given fixed floor, fitted as Script 03 fits the master store and Script 50's E16
    the mean-high-water form (D-322): dry months censored, the last LCSC_DATA_LIMIT calendar months."""
    db = dry_bounds(well)
    db = db if (db is not None and len(db)) else None
    try:
        return fit_ssm(h, cl, lag=config.HEADLINE_LAG, window=config.LCSC_DATA_LIMIT,
                       drainage_datum=float(datum), min_obs=config.RECLEN_MIN_FIT_MONTHS,
                       intercept=False, dry_bound=db)
    except Exception as e:                                       # noqa: BLE001
        warn(f"{well}: fixed-floor fit at {datum:.2f} m failed ({type(e).__name__}: {e})")
        return None


def _norm(w) -> str:
    return str(w).strip().lower()


# ── inputs ────────────────────────────────────────────────────────────────────
def load_inputs():
    lv = pd.read_csv(paths.RANWELL_LEVELS, parse_dates=["date"])
    rg = pd.read_csv(paths.RANWELL_RANGES)
    pm = pd.read_csv(paths.RANWELL_PARC_MAWR_RAIN)
    sites = pd.read_csv(paths.OUT_43_SITES)
    wb = pd.read_csv(paths.OUT_43_WELL_BASINS)
    wb["k"] = wb["well"].map(_norm)
    diag = pd.read_csv(paths.OUT_43_DIAGNOSTIC).iloc[0]
    cl = pd.read_csv(paths.INT_CLIMATE, index_col=0, parse_dates=True)
    cl = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    md = pd.read_csv(paths.INT_MASTER_DATA)
    md["k"] = md["Name_Original"].map(_norm)
    md = md.set_index("k")
    loc = pd.read_csv(paths.INT_LOCATIONS)
    loc["k"] = loc["Name"].map(_norm)
    loc = loc.set_index("k")
    wc = pd.read_csv(paths.INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wc.columns = [_norm(c) for c in wc.columns]
    return lv, rg, pm, sites, wb, diag, cl, md, loc, wc


def modern_surface(wc, loc, wb):
    """Per-well modern mean level (m OD), record span and basin, for wells with
    at least RANWELL_MIN_MODERN_N readings and a ground elevation."""
    rows = []
    for w in wc.columns:
        s = pd.to_numeric(wc[w], errors="coerce").dropna()
        if len(s) < config.RANWELL_MIN_MODERN_N or w not in loc.index:
            continue
        z = float(loc.loc[w, "ground_elev_m"])
        if not np.isfinite(z):
            continue
        b = wb.loc[wb["k"] == w, "basin_id"]
        rows.append(dict(well=w, E=float(loc.loc[w, "E"]), N=float(loc.loc[w, "N"]),
                         ground_m=z, level_m_od=float(s.mean()) + z, n=len(s),
                         first=s.index.min(), last=s.index.max(),
                         mid_year=float((s.index.min().year + s.index.max().year) / 2
                                        + (s.index.min().month + s.index.max().month) / 24),
                         basin_id=int(b.iloc[0]) if len(b) else -1))
    return pd.DataFrame(rows).set_index("well")


# ── the modern water table: Script 01b's kriged mean surface (D-205) ─────────
def _raster_at(path, e: float, n: float) -> float:
    """Bilinear value of a committed 01b raster at a point; NaN off it or on no-data."""
    import rasterio                                            # noqa: PLC0415
    from scipy.ndimage import map_coordinates                  # noqa: PLC0415
    with rasterio.open(path) as src:
        a = src.read(1).astype(float)
        if src.nodata is not None:
            a[a == src.nodata] = np.nan
        col, row = ~src.transform * (e, n)
    v = map_coordinates(a, [[row - 0.5], [col - 0.5]], order=1, mode="constant", cval=np.nan)[0]
    return float(v)


def modern_at(e: float, n: float):
    """The modern mean water table (m OD) and its kriging standard error (m) at a point,
    from Script 01b's committed mean-state surfaces (D-205 extended: the water table is
    kriged wherever it is sampled; this replaced the IDW of per-well means)."""
    return (_raster_at(paths.out_01b_surface("mean"), e, n),
            _raster_at(paths.out_01b_se("mean"), e, n))


def nearby_wells(ms: pd.DataFrame, e: float, n: float) -> pd.DataFrame:
    """The modern wells nearest a site (RANWELL_NEAR_K within RANWELL_NEAR_RADIUS_M), for the
    record and for the climate-expectation fallback; the surface itself uses every well."""
    d = np.hypot(ms["E"] - e, ms["N"] - n)
    sel = ms[d <= config.RANWELL_NEAR_RADIUS_M].copy()
    sel["d"] = d[sel.index]
    return sel.nsmallest(config.RANWELL_NEAR_K, "d")


def surface_loo(sel: pd.DataFrame, loo: pd.Series) -> float:
    """RMSE of the kriged surface's leave-one-well-out errors (01b, mean state) at a site's
    nearby wells: the empirical accuracy of the surface where the site is."""
    e = loo.reindex(sel.index).dropna()
    return float(np.sqrt(np.mean(np.square(e)))) if len(e) >= config.RANWELL_LOO_MIN_WELLS else np.nan


def surface_gradient(e: float, n: float) -> float:
    h = config.RANWELL_GRAD_STEP_M
    vx1, _ = modern_at(e + h, n)
    vx0, _ = modern_at(e - h, n)
    vy1, _ = modern_at(e, n + h)
    vy0, _ = modern_at(e, n - h)
    return float(np.hypot((vx1 - vx0) / (2 * h), (vy1 - vy0) / (2 * h)))


# ── hindcast ──────────────────────────────────────────────────────────────────
def hindcast_series(cl, betas, h0, beta1_scale=1.0, drainage_datum=None) -> pd.Series:
    """Default datum is DATUM, the project's fixed 3.7 m floor -- that IS Model A. Model B passes
    the datum its own fitted intercept implies (J-6, Martin 2026-11-07)."""
    b1, b2, b3 = betas
    h = simulate_ssm(h0, cl["P_m"].values, cl["PET"].values, b1 * beta1_scale, b2, b3,
                     drainage_datum=DATUM if drainage_datum is None else drainage_datum)
    return pd.Series(h, index=cl.index)


# compare() moved to utils/hindcast_utils.py as compare_offset_censored() (1.8.1, D-229), unchanged,
# so Script 50's E9 scores Ranwell exactly as this script does.
compare = compare_offset_censored


# ── coast ─────────────────────────────────────────────────────────────────────
def measured_retreat_1899_2026() -> float:
    """Median shoreline retreat 1899-2026 from Script 40's epoch series (m);
    NaN when the file or the row is absent. Context only — nothing here is
    derived from it."""
    try:
        df = pd.read_csv(paths.OUT_40_EPOCH_SERIES)
        row = df[(df["basis"] == "pair_extent") & (df["from_epoch"].astype(str) == "1899")
                 & (df["to_epoch"].astype(str) == "2026")]
        return float(row["median_m"].iloc[0]) if len(row) else np.nan
    except Exception:
        return np.nan


def coast_distance(e, n) -> float:
    """Distance (m) to the 2006 coastline; NaN if the KML cannot be read."""
    try:
        from shapely.geometry import Point
        from shapely.ops import unary_union
        try:
            from utils.kml_io import read_kml
            coast = unary_union(list(read_kml(paths.DATA_KML_COAST_2006).geometry))
        except Exception:
            import xml.etree.ElementTree as ET
            from pyproj import Transformer
            from shapely.geometry import LineString
            tr = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
            ns = "{http://www.opengis.net/kml/2.2}"
            lines = []
            for ls in ET.parse(paths.DATA_KML_COAST_2006).iter(f"{ns}LineString"):
                c = [tuple(map(float, x.split(",")[:2])) for x in ls.find(f"{ns}coordinates").text.split()]
                xs, ys = tr.transform([a for a, _ in c], [b for _, b in c])
                lines.append(LineString(zip(xs, ys)))
            coast = unary_union(lines)
        return float(Point(e, n).distance(coast))
    except Exception as exc:
        warn(f"coast distance unavailable ({exc})")
        return np.nan


# ── figures ───────────────────────────────────────────────────────────────────
SLACK_NAMES = {"PL": "Penlon slack", "CG": "Clwt Gwlyb", "AS": "the coastal slack", "BS": "the 2–15 slack"}


def plot_hindcast(series: pd.DataFrame, metrics: pd.DataFrame, fig_path, report: bool = False):
    """Ranwell's monthly means against Model B's offset-removed, surface-capped hindcast.

    report=False — the Methods Supplement / diagnostic render: panel titles carry
      r, NSE-after-offset, the ranges and the offset, a suptitle names the model.
    report=True — the report render: captions live in the document text (house
      rule), panel titles name the site, its slack, the paired well and the offset
      removed, and the legend names the series without values. Same data,
      same axes, same drawing code.

    1.13.0 (D-332, brief Phase 2 "Legends off the data"): Model B only -- Model A is a tested
    alternative, its scores in 44_04 -- and one figure legend below the panels in both renders
    (the report render's legend covered Site 1's 1951 minimum, and its labels carried Site 1's
    offsets as if they applied to all three sites); each site's own offset is in its panel title.
    """
    sites = sorted(series["site_no"].unique())
    fig, axes = plt.subplots(len(sites), 1, figsize=(10, 2.8 * len(sites) + 0.4), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, s in zip(axes, sites):
        sub = series[(series["site_no"] == s) & series["headline"]]
        m = metrics[(metrics["site_no"] == s) & metrics["headline"]].iloc[0]
        t = sub["month"].dt.to_timestamp()
        capped_b = None
        if "model_b_level_m_od" in sub and sub["model_b_level_m_od"].notna().any() \
                and np.isfinite(m.get("offset_m_modelB", np.nan)):
            capped_b = np.minimum(sub["model_b_level_m_od"] + m["offset_m_modelB"], m["ground_m_od"])
        _off = (f"offset {m['offset_m_modelB']:+.2f} m removed" if capped_b is not None
                else "Model B not defined at this well")
        if report:
            ax.plot(t, sub["obs_level_m_od"], "o-", ms=4, color="#1B9E77",
                    label="Ranwell 1951–53, monthly mean of readings")
            if capped_b is not None:
                ax.plot(t, capped_b, "-", lw=1.4, color="#2b6cb0",
                        label="Model B (fitted intercept), own offset removed, capped at the surface")
            ax.set_title(f"Ranwell Site {s} ({SLACK_NAMES.get(m['sketch_slack'], m['sketch_slack'])}), "
                         f"paired with {m['well']} \u2014 {_off}", fontsize=9, loc="left")
            ax.set_ylabel("Water-table level (m OD)", fontsize=9)
        else:
            ax.plot(t, sub["obs_level_m_od"], "o-", ms=4, color="#1B9E77", label="Ranwell (monthly mean of readings)")
            if capped_b is not None:
                ax.plot(t, capped_b, "-", lw=1.4, color="#2b6cb0",
                        label="Model B at the paired well (own offset removed, capped)")
                ax.set_title(f"Site {s} ({m['sketch_slack']}), {m['well']}: r {m['r_modelB']:.2f}, NSE after "
                             f"offset {m['nse_after_offset_modelB']:.2f}, range obs {m['range_obs_m_modelB']:.2f} "
                             f"vs model {m['range_model_m_modelB']:.2f} m; {_off}", fontsize=9, loc="left")
            else:
                ax.set_title(f"Site {s} ({m['sketch_slack']}), {m['well']}: {_off}", fontsize=9, loc="left")
            ax.set_ylabel("level (m OD)", fontsize=9)
        ax.axhline(m["ground_m_od"], color="grey", lw=0.7, ls=":")
        ax.grid(alpha=0.3)
    _h, _l = [], []
    for ax in axes:
        hh, ll = ax.get_legend_handles_labels()
        if len(ll) > len(_l):
            _h, _l = hh, ll
    fig.legend(_h, _l, loc="lower center", ncol=2, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 0.0))
    if not report:
        fig.suptitle("Ranwell's 1951\u201353 series driven by RAF Valley climate: Model B (fitted intercept), "
                     "coefficients fitted on the last 100 months\n(2017\u201311 to 2026\u201302); its own "
                     "offset removed, so only SHAPE is scored", fontsize=9)
    else:
        fig.suptitle("Ranwell's 1951\u201353 series: Model B (fitted intercept), coefficients fitted on the "
                     "last 100 months (2017\u201311 to 2026\u201302)\nits own offset removed \u2014 only "
                     "SHAPE is scored here", fontsize=9)
    fig.tight_layout(rect=(0, 0.45 / fig.get_size_inches()[1], 1, 1))
    render_figure(fig, fig_path)
    plt.close(fig)


def plot_level_change(lc: pd.DataFrame, fig_path):
    d = lc[lc["row"] == "site"].copy()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(d))
    ax.errorbar(x, d["delta_m"], yerr=2 * d["sigma_total_m"], fmt="o", color="#7570B3",
                capsize=3, label="Δ = modern − 1951–53 − climate expectation (±2σ)")
    ax.axhline(0, color="k", lw=0.8)
    comb = lc[lc["row"] == "COMBINED_CONSTRAINED"]
    if len(comb):
        c = comb.iloc[0]
        ax.axhspan(c["delta_m"] - 2 * c["sigma_total_m"], c["delta_m"] + 2 * c["sigma_total_m"],
                   color="#7570B3", alpha=0.12,
                   label=f"combined, constrained sites {c['delta_m']:+.2f} ± {2 * c['sigma_total_m']:.2f} m (2σ)")
    for i, r in enumerate(d.itertuples()):
        ax.annotate(f"R{int(r.site_no)} {r.sketch_slack}" + ("" if r.surface_constrained else " (unconstrained)"),
                    (i, r.delta_m), textcoords="offset points", xytext=(6, 4), fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(s)}" for s in d["site_no"]])
    ax.set_xlabel("Ranwell site")
    ax.set_ylabel("Δ (m)")
    ax.set_title("Slack water table, 2005–26 against 1951–53, climate-corrected (Model B)", fontsize=10, loc="left")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, framealpha=0.9)
    fig.tight_layout()
    render_figure(fig, fig_path)
    plt.close(fig)


# ── Q4 — the slack floors as a former water table (T-71, D-208) ──────────────
def _ranwell_floor_depths(lv: pd.DataFrame, rg: pd.DataFrame) -> pd.DataFrame:
    """Per Ranwell site: his floor (m OD, recovered as level + depth from the
    digitised readings) and the 1951–53 depths below it, m, POSITIVE DOWN.
    Fig. 4 sites carry reading statistics; Fig. 7 sites the monthly mid-range.
    Spring is the readings dated in the calendar months that D-189's bucketed
    MSL_SPRING_MONTHS stand for (bucketed month m is the reading dated m + 1)."""
    spring_cal = tuple(m + 1 for m in config.MSL_SPRING_MONTHS)
    rows = {}
    for s, g in lv.groupby("site_no"):
        dep = g["depth_below_surface_cm"] / 100.0
        rows[int(s)] = dict(
            ranwell_floor_m_od=float((g["level_m_od"] + dep).median()),
            ranwell_depth_mean_m=float(dep.mean()),
            ranwell_depth_spring_m=float(dep[g["date"].dt.month.isin(spring_cal)].mean()),
            ranwell_depth_max_m=float(dep.max()),
            ranwell_n=int(len(g)), ranwell_basis="fig4_readings")
    for s, g in rg.groupby("site_no"):
        if int(s) in rows:
            continue
        mid = (g["depth_min_cm"] + g["depth_max_cm"]) / 200.0
        rows[int(s)] = dict(
            ranwell_floor_m_od=float((g["level_max_m_od"] + g["depth_min_cm"] / 100.0).median()),
            ranwell_depth_mean_m=float(mid.mean()),
            ranwell_depth_spring_m=float(mid[g["month"].isin(spring_cal)].mean()),
            ranwell_depth_max_m=float(g["depth_max_cm"].max() / 100.0),
            ranwell_n=int(len(g)), ranwell_basis="fig7_midrange")
    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.name = "site_no"
    return out


def slack_floor_datum(wc, loc, clusters, msl, metrics, ranwell, eroding, cg_L, h0_per_metre_mm, retreat_m,
                      rate_recent_m_yr, rate_long_m_yr):
    """One row per classified reference well, then one per Ranwell site.

    Depths are m below the slack floor, positive down: the full-record mean, the
    median over hydrological years of Script 26's spring mean (MSL_m_bg, D-189/
    D-207, valid years) and of its annual minimum (MIN_m_bg, min_valid years).
    The inland baseline is the median of each over the open-dune clusters
    (SLACK_FLOOR_BASELINE_CLUSTERS) at or beyond the coastal reach L; the excess
    is depth minus baseline. The retreat expectation is MODELLED: the 2005–26
    coastal response per metre (Script 20 coastal_h0_per_metre, from the Script 25
    headline fit) times the 1899–2026 frontage-median retreat (Script 40), shaped
    by the same linear-capped form Q2 uses, max(1 − d/L, 0). The exponential
    form exp(−d/L) is written as a flagged sensitivity column and quoted nowhere
    (Martin, 2026-09-29). The implied retreat inverts the capped form inside L
    and is NaN beyond it, where the form has no response; the years are that
    retreat at Script 40's 2006–26 headline rate and at the 1899–2026 mean rate."""
    from shapely.geometry import Point as _Pt                    # noqa: PLC0415
    spring = msl[msl["valid"].astype(bool)].groupby("well")["MSL_m_bg"].median()
    n_spring = msl[msl["valid"].astype(bool)].groupby("well").size()
    amin = msl[msl["min_valid"].astype(bool)].groupby("well")["MIN_m_bg"].median()
    n_min = msl[msl["min_valid"].astype(bool)].groupby("well").size()
    hl = metrics[metrics["headline"]].set_index("well")["site_no"] if len(metrics) else pd.Series(dtype=float)
    k_per_m = h0_per_metre_mm / 1000.0
    rows = []
    for w, c in clusters.items():
        if w not in wc.columns or w not in loc.index:
            warn(f"Q4: {w} (C{c}) has no cleaned record or location; skipped")
            continue
        s = pd.to_numeric(wc[w], errors="coerce").dropna()
        d_er = float(eroding.distance(_Pt(float(loc.loc[w, "E"]), float(loc.loc[w, "N"]))))
        rows.append(dict(row="well", well=w, cluster=int(c),
                         floor_m_od=float(loc.loc[w, "ground_elev_m"]), ground_source=loc.loc[w, "ground_source"],
                         dist_eroding_hwm_m=d_er, within_coastal_reach=bool(d_er < cg_L),
                         n_months=int(len(s)), depth_mean_m=float(-s.mean()),
                         depth_spring_m=float(-spring[w]) if w in spring.index else np.nan,
                         depth_min_m=float(-amin[w]) if w in amin.index else np.nan,
                         n_years_spring=int(n_spring.get(w, 0)), n_years_min=int(n_min.get(w, 0)),
                         ranwell_site=int(hl[w]) if w in hl.index else np.nan,
                         ranwell_pairing="headline_well_of_site" if w in hl.index else ""))
    df = pd.DataFrame(rows)
    base_sel = df[df["cluster"].isin(config.SLACK_FLOOR_BASELINE_CLUSTERS) & ~df["within_coastal_reach"]]
    base = {}
    for stat in ("mean", "spring", "min"):
        v = base_sel[f"depth_{stat}_m"].dropna()
        base[stat] = (float(v.median()), float((v - v.median()).abs().median()), int(len(v)))
        df[f"baseline_depth_{stat}_m"] = base[stat][0]
        df[f"excess_{stat}_m"] = df[f"depth_{stat}_m"] - base[stat][0]
    shape_lin = np.clip(1.0 - df["dist_eroding_hwm_m"] / cg_L, 0.0, None)
    df["retreat_1899_2026_m"] = retreat_m
    df["coastal_h0_per_metre_mm"] = h0_per_metre_mm
    df["retreat_expectation_modelled_m"] = k_per_m * retreat_m * shape_lin
    df["retreat_expectation_exp_sensitivity_m"] = k_per_m * retreat_m * np.exp(-df["dist_eroding_hwm_m"] / cg_L)
    for stat in ("mean", "spring", "min"):
        df[f"residual_after_retreat_{stat}_m"] = df[f"excess_{stat}_m"] - df["retreat_expectation_modelled_m"]
    resp = k_per_m * shape_lin
    df["implied_retreat_m"] = np.where(resp > 0, df["excess_min_m"] / resp.replace(0, np.nan), np.nan)
    # the excess carries at least the baseline's spread, and the response vanishes at L, so the implied
    # retreat is ill-conditioned near L: its uncertainty (MAD of the baseline over the response) is
    # written beside it, and a value is "resolved" only when it exceeds twice that
    df["implied_retreat_sigma_m"] = np.where(resp > 0, base["min"][1] / resp.replace(0, np.nan), np.nan)
    df["implied_retreat_resolved"] = (df["implied_retreat_m"].abs() > 2 * df["implied_retreat_sigma_m"]).fillna(False)
    df["implied_years_at_2006_2026_rate"] = df["implied_retreat_m"] / rate_recent_m_yr
    df["implied_years_at_1899_2026_rate"] = df["implied_retreat_m"] / rate_long_m_yr
    return df, base


def _ranwell_site_rows(ranwell, sites, metrics, wells_df, eroding, cg_L, base, k_per_m, retreat_m, lc):
    """The Ranwell-site rows of 44_09: his floor and 1951–53 depths, and the modern
    floor and depth AT THE SITE on the average-floor basis: the modern floor is the
    site's local floor (Script 43 local_floor_m), the modern level is the kriged
    mean surface at the site (44_05), climate-adjusted as Q2. slack_floor_lowering_m
    is his floor minus the local floor (positive = lower now); depth_change_m is the
    modern depth below the local floor minus his mean depth below his (positive =
    deeper now). The floor-mask mean is carried as a sensitivity and the headline-
    well pairing as a diagnostic (pairedwell_*): a pipe is not at a well."""
    from shapely.geometry import Point as _Pt                    # noqa: PLC0415
    hl = metrics[metrics["headline"]].set_index("site_no")["well"] if len(metrics) else pd.Series(dtype=object)
    wd = wells_df.set_index("well")
    if "local_floor_m" not in sites.columns:
        raise RuntimeError(f"{paths.OUT_43_SITES.name} has no local_floor_m: run Script 43 2.1.0 first")
    lcs = lc[lc["row"] == "site"].set_index("site_no") if len(lc) else pd.DataFrame()
    rows = []
    for s, r in ranwell.iterrows():
        srow = sites.loc[s]
        d_er = float(eroding.distance(_Pt(float(srow["easting"]), float(srow["northing"]))))
        w = hl.get(s, "")
        row = dict(row="ranwell_site", well=w, cluster=int(wd.loc[w, "cluster"]) if w in wd.index else np.nan,
                   floor_m_od=np.nan, ground_source="", dist_eroding_hwm_m=d_er,
                   within_coastal_reach=bool(d_er < cg_L), ranwell_site=int(s),
                   ranwell_pairing="site_with_headline_well" if w else "site_unpaired",
                   retreat_1899_2026_m=retreat_m, coastal_h0_per_metre_mm=k_per_m * 1000.0,
                   retreat_expectation_modelled_m=k_per_m * retreat_m * max(1.0 - d_er / cg_L, 0.0),
                   retreat_expectation_exp_sensitivity_m=k_per_m * retreat_m * np.exp(-d_er / cg_L),
                   **{k: r[k] for k in r.index})
        for stat in ("mean", "spring", "min"):
            row[f"baseline_depth_{stat}_m"] = base[stat][0]
        # the average-floor basis (Script 43 Route F at the placed position)
        lf = float(srow["local_floor_m"]); fmm = float(srow.get("floor_mask_mean_m", np.nan))
        row["modern_local_floor_m_od"] = lf
        row["modern_floor_mask_mean_m_od"] = fmm
        row["slack_floor_lowering_m"] = float(r["ranwell_floor_m_od"] - lf)
        row["slack_floor_lowering_maskmean_m"] = float(r["ranwell_floor_m_od"] - fmm)
        if s in lcs.index:
            v_m = float(lcs.loc[s, "modern_kriged_m_od"])
            row["modern_level_kriged_m_od"] = v_m
            row["modern_depth_local_m"] = lf - v_m
            # 1.13.0 (D-332): Model B's climate-only expectation (44_05) under the existing columns,
            # Model A's beside them as *_model_a
            for sfx in ("", "_model_a"):
                ce = float(lcs.loc[s, f"climate_expectation_m{sfx}"]) if f"climate_expectation_m{sfx}" in lcs else np.nan
                ce = ce if np.isfinite(ce) else 0.0
                row[f"climate_expectation_m{sfx}"] = ce
                row[f"modern_depth_local_cc_m{sfx}"] = lf - (v_m - ce)
                row[f"depth_change_m{sfx}"] = (lf - (v_m - ce)) - float(r["ranwell_depth_mean_m"])
                row[f"depth_change_maskmean_m{sfx}"] = (fmm - (v_m - ce)) - float(r["ranwell_depth_mean_m"])
        if w in wd.index:
            row["pairedwell_floor_lowering_m"] = float(r["ranwell_floor_m_od"] - wd.loc[w, "floor_m_od"])
            row["pairedwell_depth_change_mean_m"] = float(wd.loc[w, "depth_mean_m"] - r["ranwell_depth_mean_m"])
            row["pairedwell_depth_change_spring_m"] = float(wd.loc[w, "depth_spring_m"] - r["ranwell_depth_spring_m"])
            row["pairedwell_depth_change_max_m"] = float(wd.loc[w, "depth_min_m"] - r["ranwell_depth_max_m"])
        rows.append(row)
    return pd.DataFrame(rows)


def plot_slack_floor_datum(df: pd.DataFrame, base: dict, cg_L: float, k_per_m: float, retreat_m: float, fig_path):
    """Depth of the annual minimum below the slack floor against distance to the
    eroding shoreline, by cluster; the inland baseline with its MAD; the modelled
    retreat expectation (capped form, solid) with the exponential sensitivity
    (dashed); Ranwell's 1951–53 deepest readings at his sites. Caption-free."""
    wells = df[df["row"] == "well"]
    sites_ = df[df["row"] == "ranwell_site"]
    fig, ax = plt.subplots(figsize=(9, 5))
    b, mad, n = base["min"]
    xmax = float(np.nanmax(df["dist_eroding_hwm_m"])) * 1.05
    ax.axhspan(b - mad, b + mad, color="0.8", alpha=0.5, lw=0,
               label=f"inland baseline, annual minimum (median ± MAD, n = {n})")
    ax.axhline(b, color="0.4", lw=1.0)
    x = np.linspace(0, xmax, 300)
    ax.plot(x, b + k_per_m * retreat_m * np.clip(1 - x / cg_L, 0, None), color="k", lw=1.5,
            label="baseline + modelled retreat response, capped at L")
    ax.plot(x, b + k_per_m * retreat_m * np.exp(-x / cg_L), color="k", lw=1.0, ls="--",
            label="exponential sensitivity (not quoted)")
    ax.axvline(cg_L, color="0.5", lw=0.8, ls=":")
    ax.annotate("L", (cg_L, ax.get_ylim()[0]), textcoords="offset points", xytext=(3, 4), fontsize=8, color="0.4")
    for c in sorted(wells["cluster"].unique()):
        g = wells[wells["cluster"] == c]
        ax.scatter(g["dist_eroding_hwm_m"], g["depth_min_m"], s=28, color=config.CLUSTER_COLOURS[int(c)],
                   edgecolor="white", linewidth=0.6, label=f"C{int(c)} wells", zorder=3)
    if len(sites_):
        ax.scatter(sites_["dist_eroding_hwm_m"], sites_["ranwell_depth_max_m"], marker="*", s=90, color="k",
                   zorder=4, label="Ranwell sites, deepest 1951–53 reading")
        for r in sites_.itertuples():
            ax.annotate(f"R{int(r.ranwell_site)}", (r.dist_eroding_hwm_m, r.ranwell_depth_max_m),
                        textcoords="offset points", xytext=(5, -9), fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, xmax)
    ax.set_xlabel("Distance to the eroding shoreline (m)")
    ax.set_ylabel("Annual minimum below the slack floor (m)")
    ax.set_title("Slack floor against the water table, by distance from the eroding shoreline", fontsize=10, loc="left")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.5, framealpha=0.9, loc="lower right")
    fig.tight_layout()
    render_figure(fig, fig_path)
    plt.close(fig)


# ── Q5 — the forest floors (T-72, D-209) ─────────────────────────────────────
def _channel_geoms(names):
    """The drainage-channel lines of Features.kml, by name (config.FOREST_CHANNEL_LINES)."""
    from utils.kml_io import read_kml                            # noqa: PLC0415
    gdf = read_kml(paths.DATA_KML_FEATURES)
    col = next((c for c in gdf.columns if c.lower() == "name"), None)
    if col is None:
        raise RuntimeError("Features.kml has no Name column")
    sel = gdf[gdf[col].astype(str).isin(list(names))]
    missing = set(names) - set(sel[col].astype(str))
    if missing:
        raise RuntimeError(f"Features.kml has no line(s) named {sorted(missing)}: check config.FOREST_CHANNEL_LINES")
    return {str(n): g for n, g in zip(sel[col], sel.geometry)}


def _preplant_hindcast(w, cluster, cl, md, cc, wc, mbq=None):
    """Climate-only change at a well since the pre-planting window (config
    PREPLANT_WINDOW): the well's SSM coefficients driven by RAF Valley climate from
    the start of the record (simulate_ssm, exactly as Q1 and Script 39), the
    window's mean / spring / annual-minimum level minus the same statistics over the
    well's own record. Own coefficients when beta_3 is identified (p below
    PREPLANT_BETA3_P_MAX); otherwise the cluster centroid's,
    because a near-zero beta_3 makes the steady state and the hindcast meaningless.
    The open-dune analogue of the well's cluster (config.PRECANOPY_ANALOGUE, D-254: C3 for
    C4, C2 for C5) is run beside it as the "pre-planting behaviour" sensitivity.
    Both windows come from one simulation.

    1.13.0 (D-332): Model B is the forecaster. Its own coefficients and p-value, and the
    cluster centroids, are Script 03's 03_16 (mbq: "own" {well: (betas, datum, p)}, "cent"
    {cluster: (betas, datum)}), each run at the datum its intercept implies; a beta_3 held at
    the bound has no p-value and so takes the centroid. Those go in the existing columns. Model A
    (master store, 03_03 centroids, the 3.7 m floor) follows as *_model_a columns."""
    rec = pd.to_numeric(wc[w], errors="coerce").dropna()
    h0 = float(rec.mean())
    a, b = config.PREPLANT_WINDOW
    analogue = config.PRECANOPY_ANALOGUE.get(int(cluster))

    def stats(h, lo, hi):
        s = h.loc[lo:hi]
        spring = s[s.index.month.isin(config.MSL_SPRING_MONTHS)].mean()
        amin = s.groupby(s.index.year).min()
        return float(s.mean()), float(spring), float(amin.median())

    # (betas, datum, basis) for the own-or-centroid run and the analogue, per form
    own_a = (w in md.index and float(md.loc[w, "beta_3_drainage"]) > 0
             and float(md.loc[w, "pvalue_beta_3"]) < config.PREPLANT_BETA3_P_MAX)
    if own_a:
        run_a = (tuple(float(md.loc[w, k]) for k in BETA_COLS), DATUM, "own")
    else:
        row = cc.loc[int(cluster)]
        run_a = (tuple(float(row[k]) for k in BETA_COLS), DATUM, f"cluster_C{int(cluster)}")
    alt_a = ((tuple(float(cc.loc[analogue, k]) for k in BETA_COLS), DATUM)
             if analogue is not None else None)
    run_b = alt_b = None
    if mbq is not None:
        ob = mbq["own"].get(normalize_well_name(w))
        if ob is not None and np.isfinite(ob[2]) and ob[2] < config.PREPLANT_BETA3_P_MAX:
            run_b = (ob[0], ob[1], "own")
        elif int(cluster) in mbq["cent"]:
            run_b = (*mbq["cent"][int(cluster)], f"cluster_C{int(cluster)}")
        alt_b = mbq["cent"].get(analogue) if analogue is not None else None

    out = {"preplant_analogue_cluster": analogue if analogue is not None else pd.NA}
    for sfx, run, alt in (("", run_b, alt_b), ("_model_a", run_a, alt_a)):
        out[f"preplant_coef_basis{sfx}"] = run[2] if run is not None else ""
        for lab, bt in (("", run[:2] if run is not None else None), ("_analogue", alt)):
            if bt is None:
                for k in ("mean", "spring", "min"):
                    out[f"climate_change_since_preplant_{k}{lab}_m{sfx}"] = np.nan
                continue
            h = hindcast_series(cl, bt[0], h0, drainage_datum=bt[1])
            pre = stats(h, pd.Timestamp(a), pd.Timestamp(b) + pd.offsets.MonthEnd(0))
            mod = stats(h, rec.index.min(), rec.index.max())
            for k, (x, y) in zip(("mean", "spring", "min"), zip(pre, mod)):
                out[f"climate_change_since_preplant_{k}{lab}_m{sfx}"] = x - y     # + = the window stood higher
    return out


def forest_floor_excess(sfd, loc, drawdown, canopy, ground_prep, channels, dem_src, dem, smooth,
                        cl=None, md=None, cc=None, wc=None, retreat_terms=None, mbq=None):
    """One row per reference well flagged in_forest (01_locations), carrying the
    44_09 excess and residual, the modelled canopy drawdown at the well (Script 20
    dd_mm, config.DRAWDOWN_H0_MM inside the forest), the felling era, the ground
    preparation Martin recorded, the distance to the nearest drainage channel and
    the channel bed's height above the well's floor (positive = the bed is higher than the floor), the floor's microrelief
    (SD and range of the DEM within FLOOR_RELIEF_RADIUS_M), and the mean head
    against the HEAD_DEM_HEADLINE_SMOOTHING_M-smoothed ground (the T-66 relation;
    it does not resolve a forest anomaly and is written for the record).
    Every modelled quantity carries 'modelled' in its name or note."""
    from shapely.geometry import Point as _Pt                    # noqa: PLC0415
    wells = sfd[sfd["row"] == "well"].set_index("well")
    forest = [w for w in wells.index if bool(loc.loc[w, "in_forest"])] if "in_forest" in loc.columns else []
    dd = drawdown.set_index(drawdown["well"].astype(str).map(_norm))
    can = canopy.set_index(canopy["well"].astype(str).map(_norm))
    gp = ground_prep.set_index(ground_prep["well"].astype(str).map(_norm)) if len(ground_prep) else pd.DataFrame()
    R = config.FLOOR_RELIEF_RADIUS_M
    rows = []
    for w in forest:
        r = wells.loc[w]
        e, n = float(loc.loc[w, "E"]), float(loc.loc[w, "N"])
        floor = float(r["floor_m_od"])
        # channel
        ch_name, ch_d, ch_bed = "", np.nan, np.nan
        if channels:
            d = {k: float(g.distance(_Pt(e, n))) for k, g in channels.items()}
            ch_name = min(d, key=d.get); ch_d = d[ch_name]
            near = channels[ch_name].interpolate(channels[ch_name].project(_Pt(e, n)))
            from utils.water_table import sample                 # noqa: PLC0415
            ch_bed = float(sample(dem_src, dem, [near.x], [near.y])[0])
        # microrelief
        c0, r0 = ~dem_src.transform * (e, n)
        i, j = int(r0), int(c0)
        k = int(np.ceil(R / dem_src.res[0]))
        win = dem[max(0, i - k):i + k + 1, max(0, j - k):j + k + 1]
        yy, xx = np.indices(win.shape)
        dist = np.hypot((yy - min(i, k)) * dem_src.res[0], (xx - min(j, k)) * dem_src.res[0])
        v = win[(dist <= R) & np.isfinite(win)]
        # head against the smoothed ground
        from utils.water_table import sample                     # noqa: PLC0415
        sm = float(sample(dem_src, smooth, [e], [n])[0])
        head = floor - float(r["depth_mean_m"])
        felled = can.loc[w, "felled_year"] if w in can.index else np.nan
        prep = str(gp.loc[w, "ground_prep"]) if len(gp) and w in gp.index else ""
        replant = loc.loc[w, "in_1998_replant"] if "in_1998_replant" in loc.columns else np.nan
        # 1.9.0: the felling group is named from the recorded year (data/canopy_history.csv), not a literal
        # 1.9.1: a well recorded as open in 1989 and never felled (NW9, broadleaf on the edge of the 1993 felling) is
        # kept out of the felling groups even where a felling outline takes it in (Martin, 2026-10-03)
        open89 = w in can.index and str(can.loc[w, "canopy_1989"]).strip().lower() == "open"
        group = ("clearfell_2017" if felled == 2017 else f"felled_{int(felled)}" if pd.notna(felled)
                 else "open_1989" if open89 else "replant_1998" if pd.notna(replant) else "canopy")
        ddm = float(dd.loc[w, "dd_mm"]) if w in dd.index else np.nan
        rows.append(dict(
            well=w, cluster=int(r["cluster"]) if pd.notna(r["cluster"]) else pd.NA, group=group,
            felled_year=felled, replant_block=replant, ground_prep=prep,
            dist_broadleaf_restock_m=loc.loc[w, "dist_broadleaf_restock_m"] if "dist_broadleaf_restock_m" in loc.columns else np.nan,
            floor_m_od=floor, dist_eroding_hwm_m=r["dist_eroding_hwm_m"], within_coastal_reach=r["within_coastal_reach"],
            depth_spring_m=r["depth_spring_m"], depth_min_m=r["depth_min_m"],
            excess_min_m=r["excess_min_m"], retreat_expectation_modelled_m=r["retreat_expectation_modelled_m"],
            residual_after_retreat_min_m=r["residual_after_retreat_min_m"],
            modelled_canopy_drawdown_m=ddm / 1000.0 if np.isfinite(ddm) else np.nan,
            residual_over_modelled_drawdown=(r["residual_after_retreat_min_m"] / (ddm / 1000.0)) if ddm else np.nan,
            litter_allowance_m=config.FOREST_LITTER_MAX_M,
            residual_less_litter_min_m=r["residual_after_retreat_min_m"] - config.FOREST_LITTER_MAX_M,
            channel_name=ch_name, dist_channel_m=ch_d, channel_bed_m_od=ch_bed,
            channel_bed_above_floor_m=(ch_bed - floor) if np.isfinite(ch_bed) else np.nan,
            floor_sd_m=float(v.std()) if len(v) else np.nan, floor_range_m=float(v.max() - v.min()) if len(v) else np.nan,
            floor_relief_radius_m=R, smoothed_ground_m_od=sm, head_mean_m_od=head,
            head_minus_smoothed_ground_m=head - sm, floor_minus_smoothed_ground_m=floor - sm))
        if cl is not None and w in wc.columns and pd.notna(r["cluster"]):
            rows[-1].update(_preplant_hindcast(w, r["cluster"], cl, md, cc, wc, mbq))
        if retreat_terms is not None:
            k_per_m, cg_L = retreat_terms["k_per_m"], retreat_terms["L"]
            shape = max(1.0 - float(r["dist_eroding_hwm_m"]) / cg_L, 0.0)
            for lab in ("steady", "modern"):
                rr = retreat_terms[lab]
                rows[-1][f"retreat_since_preplant_{lab}_m"] = rr
                rows[-1][f"retreat_expectation_since_preplant_{lab}_m"] = k_per_m * rr * shape
    df = pd.DataFrame(rows)
    if "climate_change_since_preplant_min_m" in df.columns:
        # the excess that neither climate nor retreat since the window accounts for:
        # excess is depth (positive down); a window that stood HIGHER (+) would explain part of it
        for lab in ("steady", "modern"):
            for sfx in ("", "_model_a"):              # 1.13.0 (D-332): B, then A
                if f"retreat_expectation_since_preplant_{lab}_m" in df.columns:
                    df[f"residual_after_climate_and_retreat_{lab}_min_m{sfx}"] = (
                        df["excess_min_m"] - df[f"climate_change_since_preplant_min_m{sfx}"]
                        - df[f"retreat_expectation_since_preplant_{lab}_m"])
    return df


def plot_forest_floor_excess(df: pd.DataFrame, fig_path):
    """Residual after retreat by felling group, wells coloured by cluster, ploughed
    wells open; the modelled canopy drawdown as a line. Caption-free."""
    felled = sorted(g for g in set(df["group"]) if g.startswith("felled_"))
    order = [g for g in ["canopy"] + felled + ["replant_1998", "clearfell_2017", "open_1989"] if g in set(df["group"])]
    label = {"canopy": "unfelled\ncanopy", "replant_1998": "1998 outline,\nno felling year",
             "open_1989": "open in 1989,\nnever felled",
             "clearfell_2017": "clearfell\n2017", **{g: f"clearfelled\n{g.split('_')[1]}" for g in felled}}
    fig, ax = plt.subplots(figsize=(8, 4.8))
    rng = np.random.default_rng(config.FOREST_FLOOR_FIG_SEED)
    for gi, g in enumerate(order):
        sub = df[df["group"] == g]
        x = gi + rng.uniform(-0.18, 0.18, len(sub))
        for k_, (xi, r) in enumerate(zip(x, sub.sort_values("residual_after_retreat_min_m").itertuples())):
            c = config.CLUSTER_COLOURS.get(int(r.cluster), "0.4") if pd.notna(r.cluster) else "0.4"
            ax.scatter(xi, r.residual_after_retreat_min_m, s=44, color=c if not r.ground_prep else "white",
                       edgecolor=c, linewidth=1.4, zorder=3)
            ax.annotate(r.well, (xi, r.residual_after_retreat_min_m), textcoords="offset points",
                        xytext=(7, 4 if k_ % 2 else -8), fontsize=7)
    dd = df["modelled_canopy_drawdown_m"].dropna()
    if len(dd):
        ax.axhline(float(dd.median()), color="k", lw=1.0, ls="--", label="modelled canopy drawdown at the wells (config)")
    ax.axhline(0, color="0.5", lw=0.8)
    for c in sorted(df["cluster"].dropna().unique()):
        ax.scatter([], [], s=44, color=config.CLUSTER_COLOURS.get(int(c), "0.4"), label=f"C{int(c)}")
    ax.scatter([], [], s=44, color="white", edgecolor="k", linewidth=1.4, label="ploughed before planting (open marker)")
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([label[g] for g in order])
    ax.set_ylabel("Excess depth of the annual minimum below the floor,\nless the modelled retreat response (m)")
    ax.set_title("Forest wells: floor excess over the open-dune baseline, by felling history", fontsize=10, loc="left")
    ax.grid(alpha=0.3, axis="y")
    ax.legend(fontsize=7.5, framealpha=0.9, loc="upper left")
    fig.tight_layout()
    render_figure(fig, fig_path)
    plt.close(fig)


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    apply_house_style()
    banner(SCRIPT_ID, "Ranwell's 1951–53 record against the modern network and the SSM hindcast", VERSION)
    paths.DIR_44.mkdir(parents=True, exist_ok=True)

    phase(1, "Load inputs")
    missing = [q for q in (paths.RANWELL_LEVELS, paths.RANWELL_RANGES, paths.RANWELL_PARC_MAWR_RAIN)
               if not q.exists()]
    if missing:
        warn("Ranwell digitised inputs not present: " + ", ".join(q.name for q in missing))
        note("skipping — a raw input no pipeline step produces; its absence is not a failure")
        return 0
    if not (paths.OUT_43_SITES.exists() and paths.OUT_43_WELL_BASINS.exists()):
        warn("Script 43 v2 outputs not present (43_01, 43_07); run Script 43 first")
        return 0
    lv, rg, pm, sites, wb, diag, cl, md, loc, wc = load_inputs()
    sites = sites.set_index("site_no")
    ms = modern_surface(wc, loc, wb)
    lo_ = pd.read_csv(paths.OUT_01B_LOO)
    lo_ = lo_[lo_["state"] == "mean"]
    loo_mean = pd.Series(lo_["error_m"].values, index=lo_["well"].map(_norm))   # 01b, mean state
    datum_mad = float(diag["datum_offset_mad_m"])
    info(f"{len(lv)} Fig. 4 readings at sites {sorted(int(x) for x in lv['site_no'].unique())}; "
         f"{len(rg)} Fig. 7 ranges at sites {sorted(int(x) for x in rg['site_no'].unique())}")
    info(f"modern surface: {len(ms)} wells with >= {config.RANWELL_MIN_MODERN_N} readings; "
         f"climate from {cl.index.min():%Y-%m}; datum-offset MAD {datum_mad:.3f} m (Script 43)")

    phase(2, "Q1 — hindcast at the same-basin wells")
    lv["month"] = lv["date"].dt.to_period("M")
    obs_month = lv.groupby(["site_no", "month"])["level_m_od"].mean()
    # J-6 (Martin, 2026-11-07: "Scenario 3 lets keep model B"). Model B is the same machinery at
    # the datum its own fitted intercept implies. Scenario 3 scores SHAPE -- the offset is removed
    # and the run capped at the surface -- so B's level cannot win here by construction. What it
    # CAN show is whether B needs a SMALLER OFFSET than A, which is evidence about level that this
    # scenario would otherwise discard. ceh14 is excluded: implied datum -9.39 m, a base above ground.
    # 1.13.0 (D-332): Model B is the forecaster and the headline. A bounded beta_3 fit is kept and
    # counted; a well whose implied datum is not below ground has no Model B and is counted out.
    mb, mb_undef, mb_binds = {}, {}, set()
    mbq = {"own": {}, "cent": {}}       # Q5's Model B: own (betas, datum, p) and cluster centroids
    try:
        _mb = pd.read_csv(paths.OUT_03_MODEL_B_PERSISTENCE)
        for _, _r in _mb[_mb["level"] == "centroid"].iterrows():
            _b3 = float(_r["beta_3_B"])
            _d = (float(_r["drainage_datum_m"]) - float(_r["alpha_B"]) / _b3
                  if np.isfinite(_b3) and _b3 > 0 else np.nan)
            if np.isfinite(_d) and _d > 0:
                mbq["cent"][int(_r["Cluster"])] = ((float(_r["beta_1_B"]), float(_r["beta_2_B"]), _b3), _d)
            else:
                warn(f"C{int(_r['Cluster'])} Model B centroid has no datum below ground ({_d:+.2f} m)")
        for _, _r in _mb[_mb["level"] == "well"].iterrows():
            _k = normalize_well_name(_r["well"])
            _b3 = float(_r["beta_3_B"])
            if (str(_r.get("beta_3_bound_binds", "")).strip().lower() in ("true", "1", "1.0")
                    or (np.isfinite(_b3) and _b3 <= B3_MIN * (1 + 1e-9))):
                mb_binds.add(_k)
            _d = (float(_r["drainage_datum_m"]) - float(_r["alpha_B"]) / _b3
                  if np.isfinite(_b3) and _b3 > 0 else np.nan)
            if not (np.isfinite(_d) and _d > 0):
                mb_undef[_k] = _d
                continue
            mb[_k] = ((float(_r["beta_1_B"]), float(_r["beta_2_B"]), _b3), _d)
            _pb = pd.to_numeric(_r.get("pvalue_beta_3_B", np.nan), errors="coerce")
            mbq["own"][_k] = (mb[_k][0], _d, float(_pb) if pd.notna(_pb) else np.nan)
        note(f"Model B for {len(mb)} well(s); {len(mb_binds)} with beta_3 at the bound; undefined at "
             + (", ".join(f"{k} ({v:+.2f} m)" for k, v in mb_undef.items()) or "none"))
    except Exception as _e:
        warn(f"Model B coefficients unavailable ({type(_e).__name__}); the headline has no Model B")
    mhw = mhw_level()
    if not np.isfinite(mhw):
        warn("tide_mhw_m not in Script 01b's report numbers: the mean-high-water form is skipped")
    # J-6, Martin 2026-11-08: "we should have a whole record trained model against the ccw data
    # and Ranwells". Same three fitting windows as Script 39 -- comparison (the master store,
    # the last 100 months), pre2018, and the whole record -- for both model forms.
    #
    # For Ranwell the question is narrower than at the CCW wells: this scenario removes the
    # offset and scores SHAPE, so a window that shifts the level cannot be penalised here. What
    # the windows can show is whether the SEASONAL DYNAMICS the coefficients encode depend on
    # which eight years they were fitted on -- fifty-four years before the period predicted.
    FIT_WINDOWS = ("pre2018", "whole")
    fits = {w: {} for w in FIT_WINDOWS}
    win_b_binds = {w: set() for w in FIT_WINDOWS}      # 1.13.0 (D-332): bounded fits kept, counted
    win_b_undef = {w: {} for w in FIT_WINDOWS}
    try:
        _split = pd.Timestamp(config.MODEL_AB_SPLIT_DATE)
        _wc = pd.read_csv(paths.INT_WELLS_CLEAN, index_col=0, parse_dates=True)
        # NOT _norm: that is a module-level function in this script, and assigning to the name
        # here made it local to main() and broke an unrelated call forty lines earlier.
        _wkey = lambda x: str(x).strip().lower().replace(" ", "")
        _cols = {_wkey(c): c for c in _wc.columns}
        for _w in list(md.index):
            _col = _cols.get(_wkey(_w))
            if _col is None:
                continue
            _h_all = pd.to_numeric(_wc[_col], errors="coerce").dropna()
            for _win in FIT_WINDOWS:
                _h = _h_all[_h_all.index < _split] if _win == "pre2018" else _h_all
                _c = cl[cl.index < _split] if _win == "pre2018" else cl
                if len(_h) < MIN_FIT_OBS:
                    continue
                _fa = fit_ssm(_h, _c, lag=0, min_obs=MIN_FIT_OBS)
                _fb = fit_ssm_intercept(_h, _c, lag=0, min_obs=MIN_FIT_OBS)
                if _fa and np.isfinite(_fa.get("beta_3_drainage", np.nan)) and _fa["beta_3_drainage"] > 0:
                    fits[_win].setdefault(_w, {})["A"] = (
                        (_fa["beta_1_recharge"], _fa["beta_2_atmospheric_draw"], _fa["beta_3_drainage"]),
                        DATUM)
                if _fb and np.isfinite(_fb.get("beta_3_drainage", np.nan)):
                    if _fb.get("beta_3_bound_binds", False):
                        win_b_binds[_win].add(_w)
                    _db2 = (DATUM - _fb.get("alpha", 0.0) / _fb["beta_3_drainage"]
                            if _fb["beta_3_drainage"] > 0 else np.nan)
                    if np.isfinite(_db2) and _db2 > 0:
                        fits[_win].setdefault(_w, {})["B"] = (
                            (_fb["beta_1_recharge"], _fb["beta_2_atmospheric_draw"], _fb["beta_3_drainage"]),
                            _db2)
                    else:                     # base at or above ground: Model B undefined here
                        win_b_undef[_win][_w] = _db2
        for _win in FIT_WINDOWS:
            note(f"{_win} fits: {sum('A' in v for v in fits[_win].values())} Model A, "
                 f"{sum('B' in v for v in fits[_win].values())} Model B ({len(win_b_binds[_win])} at the "
                 f"beta_3 bound, {len(win_b_undef[_win])} with no datum below ground), "
                 f"over {len(fits[_win])} well(s)")
    except Exception as _e:
        warn(f"window fits unavailable ({type(_e).__name__}: {_e}); "
             f"the window-comparison metrics stay empty")

    series_rows, metric_rows, climate_exp, climate_exp_a = [], [], {}, {}

    def _a_ok(w_):
        """Model A (the 3.7 m alternative) can be run: a complete master-store triple, beta_3 > 0."""
        return bool(w_ in md.index and all(np.isfinite(md.loc[w_, c_]) for c_ in BETA_COLS)
                    and md.loc[w_, BETA_COLS[2]] > 0)

    def _expectation(h_, first_, last_):
        """Climate-only expectation: modelled 1951-53 mean minus the modelled modern-span mean."""
        hp_ = h_.copy()
        hp_.index = hp_.index.to_period("M")
        return float(hp_.loc[SPAN[0]:SPAN[1]].mean() - hp_.loc[first_.to_period("M"):last_.to_period("M")].mean())
    for s in sorted(lv["site_no"].unique()):
        srow = sites.loc[s]
        d = np.hypot(ms["E"] - srow["easting"], ms["N"] - srow["northing"])
        cand = ms[(ms["basin_id"] == srow["basin_id"]) & (d <= config.RANWELL_PAIR_MAX_M)].copy()
        cand["d"] = d[cand.index]
        # 1.13.0 (D-332): a well pairs when Model B is defined there (03_16, implied datum below
        # ground; beta_3 bounded > 0), not on Model A's triple. Model A is run where it can be.
        _cand_a = cand[[_a_ok(w) for w in cand.index]]
        cand = cand[[normalize_well_name(w) in mb for w in cand.index]]
        if set(_cand_a.index) != set(cand.index):
            warn(f"site {s}: Model B pairing differs from Model A's: A {sorted(_cand_a.index)}, "
                 f"B {sorted(cand.index)}")
        if cand.empty:
            warn(f"site {s}: no same-basin well with committed coefficients within "
                 f"{config.RANWELL_PAIR_MAX_M:.0f} m")
            continue
        cand = cand.sort_values("d")
        om = obs_month.loc[s]
        for rank, (w, c) in enumerate(cand.iterrows()):
            a_ok = _a_ok(w)
            betas = tuple(float(md.loc[w, k]) for k in BETA_COLS) if a_ok else (np.nan,) * 3
            h0 = float(c["level_m_od"] - c["ground_m"])
            h, mid, met = None, None, {}
            if a_ok:
                h = hindcast_series(cl, betas, h0)
                mid = ((h + h.shift(1)) / 2 + c["ground_m"])
                mid.index = mid.index.to_period("M")
                met = compare(om, mid, float(srow["height_m_od"]))
            mid_b, met_b, kb = None, {}, normalize_well_name(w)
            met_b["datum_modelB_m"] = mb[kb][1] if kb in mb else mb_undef.get(kb, np.nan)
            met_b["beta_3_bound_binds_modelB"] = bool(kb in mb_binds)
            if kb in mb:
                _bb, _db = mb[kb]
                h_b = hindcast_series(cl, _bb, h0, drainage_datum=_db)
                mid_b = ((h_b + h_b.shift(1)) / 2 + c["ground_m"])
                mid_b.index = mid_b.index.to_period("M")
                met_b.update({f"{k}_modelB": v
                              for k, v in compare(om, mid_b, float(srow["height_m_od"])).items()})
                met_b.update(beta_1_modelB=_bb[0], beta_2_modelB=_bb[1], beta_3_modelB=_bb[2])
                # 1.13.0 (D-332): B's own beta_1 envelope, the same scalings as A's
                for sc in config.CCW_BETA1_SCALINGS:
                    _hs = hindcast_series(cl, _bb, h0, sc, drainage_datum=_db)
                    _ms = ((_hs + _hs.shift(1)) / 2 + c["ground_m"])
                    _ms.index = _ms.index.to_period("M")
                    met_b[f"nse_after_offset_modelB_b1x{sc:.2f}"] = compare(
                        om, _ms, float(srow["height_m_od"]))["nse_after_offset"]
                # the climate-only expectation under B, beside A's (Q2 still uses A's: see report)
                _hpb = h_b.copy()
                _hpb.index = _hpb.index.to_period("M")
                met_b["climate_expectation_modelB_m"] = float(
                    _hpb.loc[SPAN[0]:SPAN[1]].mean()
                    - _hpb.loc[c["first"].to_period("M"):c["last"].to_period("M")].mean())
            # 1.13.0 (D-332, Addendum 3 "Scenario 3"): Model A at the well's depth to mean high water
            mid_m, met_m = None, {}
            if np.isfinite(mhw) and w in wc.columns:
                _dm = float(c["ground_m"]) - mhw
                met_m["datum_mhw_m"] = _dm
                _fm = fixed_floor_fit(pd.to_numeric(wc[w], errors="coerce").dropna(), cl, w, _dm)
                if _fm is not None and _fm["beta_3_drainage"] > 0:
                    _bm = (_fm["beta_1_recharge"], _fm["beta_2_atmospheric_draw"], _fm["beta_3_drainage"])
                    h_m = hindcast_series(cl, _bm, h0, drainage_datum=_dm)
                    mid_m = ((h_m + h_m.shift(1)) / 2 + c["ground_m"])
                    mid_m.index = mid_m.index.to_period("M")
                    met_m.update({f"{k}_mhw": v
                                  for k, v in compare(om, mid_m, float(srow["height_m_od"])).items()})
                    met_m.update(beta_1_mhw=_bm[0], beta_2_mhw=_bm[1], beta_3_mhw=_bm[2])
            # J-6: the same two forms from the two alternative fitting windows, scored the same
            # way (offset removed). Keys are nse_after_offset_<window>_<form> so a reader can
            # compare them directly with the comparison-window nse_after_offset above.
            met_win = {}
            for _win in FIT_WINDOWS:
                for _form in ("A", "B"):
                    _ent = fits[_win].get(w, {}).get(_form)
                    if _ent is None:
                        continue
                    _bb, _dd = _ent
                    _hw = hindcast_series(cl, _bb, h0, drainage_datum=_dd)
                    _mw = ((_hw + _hw.shift(1)) / 2 + c["ground_m"])
                    _mw.index = _mw.index.to_period("M")
                    _cw = compare(om, _mw, float(srow["height_m_od"]))
                    met_win[f"nse_after_offset_{_win}_{_form}"] = _cw.get("nse_after_offset")
                    met_win[f"r_{_win}_{_form}"] = _cw.get("r")

            env = {}
            for sc in (config.CCW_BETA1_SCALINGS if a_ok else ()):
                hs = hindcast_series(cl, betas, h0, sc)
                ms_ = ((hs + hs.shift(1)) / 2 + c["ground_m"])
                ms_.index = ms_.index.to_period("M")
                env[f"nse_after_offset_b1x{sc:.2f}"] = compare(om, ms_, float(srow["height_m_od"]))["nse_after_offset"]
            # climate-only expectation: modelled 1951-53 mean minus modelled modern-span mean.
            # 44_04's climate_expectation_m stays Model A (its unsuffixed columns are A's, read by
            # Script 50); Q2 takes Model B's (climate_expectation_modelB_m) from 1.13.0 (D-332).
            exp = _expectation(h, c["first"], c["last"]) if a_ok else np.nan
            headline = rank == 0
            if headline:
                climate_exp[s] = (met_b.get("climate_expectation_modelB_m", np.nan), w)
                climate_exp_a[s] = (exp, w)
            metric_rows.append(dict(site_no=int(s), sketch_slack=srow["sketch_slack"], well=w,
                                    ground_m_od=float(srow["height_m_od"]),
                                    dist_m=float(c["d"]), headline=headline,
                                    beta_1=betas[0], beta_2=betas[1], beta_3=betas[2],
                                    **met, **met_b, **met_win,
                                    climate_expectation_m=exp, **env, **met_m))
            common = om.index.intersection((mid if mid is not None else mid_b).index)
            for mth in common:
                series_rows.append(dict(site_no=s, well=w, headline=headline, month=mth,
                                        obs_level_m_od=float(om.loc[mth]),
                                        model_level_m_od=(float(mid.loc[mth]) if mid is not None else np.nan),
                                        model_b_level_m_od=(float(mid_b.loc[mth])
                                                            if mid_b is not None and mth in mid_b.index
                                                            else np.nan),
                                        n_readings=int(lv[(lv["site_no"] == s) & (lv["month"] == mth)].shape[0]),
                                        # 1.13.0 (D-332): appended, so no existing column moves
                                        model_mhw_level_m_od=(float(mid_m.loc[mth])
                                                              if mid_m is not None and mth in mid_m.index
                                                              else np.nan)))
        hl = [m for m in metric_rows if m["site_no"] == s and m["headline"]][0]
        step(f"site {s} ({srow['sketch_slack']}): {len(cand)} paired well(s); headline {hl['well']} "
             f"({hl['dist_m']:.0f} m): Model B r {hl.get('r_modelB', np.nan):.2f}, NSE after offset "
             f"{hl.get('nse_after_offset_modelB', np.nan):.2f}; A at MHW NSE "
             f"{hl.get('nse_after_offset_mhw', np.nan):.2f}; Model A r {hl.get('r', np.nan):.2f}, NSE after offset "
             f"{hl.get('nse_after_offset', np.nan):.2f}; n {hl.get('n_modelB', np.nan)} "
             f"({hl.get('n_at_surface_modelB', np.nan)} at the surface); climate-only expectation "
             f"B {hl.get('climate_expectation_modelB_m', np.nan):+.3f} m, A {hl['climate_expectation_m']:+.3f} m")
    metrics = pd.DataFrame(metric_rows)
    series = pd.DataFrame(series_rows)

    # J-6: the window-and-form comparison, over EVERY paired well rather than the three headline
    # sites, because three sites is too few to read a median from. Shape only -- the offset is
    # removed before scoring, so none of this is about level.
    _pairs = [("comparison", "A", "nse_after_offset"), ("comparison", "B", "nse_after_offset_modelB"),
              ("comparison", "A_MHW", "nse_after_offset_mhw"),                 # 1.13.0 (D-332)
              ("pre2018", "A", "nse_after_offset_pre2018_A"), ("pre2018", "B", "nse_after_offset_pre2018_B"),
              ("whole", "A", "nse_after_offset_whole_A"), ("whole", "B", "nse_after_offset_whole_B")]
    step("NSE after offset over all paired wells, by fitting window and model form:")
    for _win, _form, _c in _pairs:
        if _c not in metrics.columns:
            continue
        _x = metrics[_c].dropna()
        if _x.empty:
            continue
        step(f"  {_win:10s} Model {_form}: n {len(_x):2d}  median {_x.median():+.3f}  "
             f"IQR {_x.quantile(.25):+.3f} to {_x.quantile(.75):+.3f}  min {_x.min():+.3f}")

    phase(3, "Q2 — 1951–53 level against the modern surface, with the four error terms")
    rg["level_mid_m_od"] = (rg["level_max_m_od"] + rg["level_min_m_od"]) / 2
    mid_mean = rg.groupby("site_no")["level_mid_m_od"].mean()
    read_mean = lv.groupby("site_no")["level_m_od"].mean()
    read_n = lv.groupby("site_no").size()
    modern_mid_year = float(ms["mid_year"].median())
    dt_years = modern_mid_year - config.RANWELL_MEAN_MID_YEAR
    retreat_1899_2026 = measured_retreat_1899_2026()
    info(f"interval {dt_years:.1f} y (modern record midpoint {modern_mid_year:.1f}); "
         f"shoreline retreat 1899-2026 (Script 40 median) {retreat_1899_2026:.0f} m for context")
    fit25 = pd.read_csv(paths.OUT_25_FIT_PARAMETERS)
    src_, mod_ = config.RANWELL_COASTAL_FIT
    frow = fit25[(fit25["source"] == src_) & (fit25["model"] == mod_)]
    if frow.empty:
        raise RuntimeError(f"no {src_}/{mod_} row in {paths.OUT_25_FIT_PARAMETERS.name}: run Script 25")
    cg_d0, cg_L = float(frow["delta_0_mm_yr"].iloc[0]), float(frow["L_m"].iloc[0])
    from utils.water_table import geojson_geom                 # noqa: PLC0415
    from shapely.geometry import Point as _Pt                    # noqa: PLC0415
    eroding = geojson_geom(paths.DATA_COASTLINE_ERODING)
    info(f"coastal expectation: Script 25 {src_} {mod_} fit, delta_0 {cg_d0:.2f} mm/yr, L {cg_L:.0f} m, "
         f"carried across {dt_years:.1f} y (an extrapolation of the 2005-2026 rate)")
    lc_rows = []
    for s in sorted(set(read_mean.index) | set(mid_mean.index)):
        srow = sites.loc[s]
        if s in read_mean.index:
            rmean, basis, n_r = float(read_mean[s]), "fig4_readings", int(read_n[s])
        else:
            rmean, basis, n_r = float(mid_mean[s]), "fig7_midrange", int((rg["site_no"] == s).sum())
        v_m, se_m = modern_at(srow["easting"], srow["northing"])
        v_r, _ = modern_at(srow["refined_easting"], srow["refined_northing"])
        sel = nearby_wells(ms, srow["easting"], srow["northing"])
        if not np.isfinite(v_m):
            warn(f"site {s}: outside the 01b kriged surface; no modern level")
            continue
        loo = surface_loo(sel, loo_mean)
        grad = surface_gradient(srow["easting"], srow["northing"])
        pos_sigma = (float(srow["refined_move_m"]) if srow["resolvability"] == "flank"
                     else config.RANWELL_POS_SIGMA_M)
        sig_pos = grad * pos_sigma
        sig_samp = config.RANWELL_SAMPLING_SIGMA_M
        sig_dat = datum_mad
        sig = float(np.sqrt(loo ** 2 + sig_pos ** 2 + sig_samp ** 2 + sig_dat ** 2))
        # climate-only expectation: from the headline hindcast where the site has one,
        # else from the nearest contributing well that has coefficients. 1.13.0 (D-332): Model B
        # (the forecaster) under the existing columns, Model A beside it as *_model_a.
        def _q2_exp(form):
            src_ = climate_exp if form == "B" else climate_exp_a
            if s in src_ and np.isfinite(src_[s][0]):
                return src_[s][0], "headline_hindcast"
            for w in sel.index:
                h0_ = float(ms.loc[w, "level_m_od"] - ms.loc[w, "ground_m"])
                if form == "B" and normalize_well_name(w) in mb:
                    _bb, _db = mb[normalize_well_name(w)]
                    h_ = hindcast_series(cl, _bb, h0_, drainage_datum=_db)
                elif form == "A" and _a_ok(w):
                    h_ = hindcast_series(cl, tuple(float(md.loc[w, k]) for k in BETA_COLS), h0_)
                else:
                    continue
                return _expectation(h_, ms.loc[w, "first"], ms.loc[w, "last"]), f"hindcast_at_{w}"
            return np.nan, ""
        exp, exp_src = _q2_exp("B")
        exp_a, exp_src_a = _q2_exp("A")
        delta = (v_m - rmean) - (exp if np.isfinite(exp) else 0.0)
        delta_a = (v_m - rmean) - (exp_a if np.isfinite(exp_a) else 0.0)
        dcoast = coast_distance(srow["easting"], srow["northing"])
        d_er = float(eroding.distance(_Pt(srow["easting"], srow["northing"])))
        inner = cg_d0 * (1.0 - d_er / cg_L)
        inner = min(inner, 0.0) if cg_d0 < 0 else max(inner, 0.0)
        coast_exp = inner * dt_years / 1000.0
        constrained = bool(np.isfinite(loo) and loo <= config.RANWELL_LOO_MAX_M)
        lc_rows.append(dict(
            row="site", site_no=s, sketch_slack=srow["sketch_slack"], ranwell_basis=basis,
            ranwell_n=n_r, ranwell_mean_m_od=rmean,
            modern_kriged_m_od=v_m, modern_kriged_refined_m_od=v_r,
            nearby_wells="; ".join(f"{w} ({r.d:.0f} m, {r.level_m_od:.2f})" for w, r in sel.iterrows()),
            n_nearby=len(sel), nearest_well_m=float(sel["d"].min()) if len(sel) else np.nan,
            nearby_min_m_od=float(sel["level_m_od"].min()) if len(sel) else np.nan,
            nearby_max_m_od=float(sel["level_m_od"].max()) if len(sel) else np.nan,
            sigma_loo_m=loo, kriging_se_m=se_m, surface_gradient=grad, position_sigma_m=pos_sigma, sigma_position_m=sig_pos,
            sigma_sampling_m=sig_samp, sigma_datum_m=sig_dat, sigma_total_m=sig,
            climate_expectation_m=exp, climate_expectation_source=exp_src,
            delta_m=delta, z=delta / sig if sig > 0 else np.nan, resolved=bool(abs(delta) > 2 * sig),
            interval_years=dt_years, rate_mm_per_year=delta / dt_years * 1000,
            dist_coast_2006_m=dcoast, shoreline_retreat_1899_2026_m=retreat_1899_2026,
            dist_eroding_hwm_m=d_er, within_coastal_reach=bool(d_er < cg_L),
            coastal_expectation_extrapolated_m=coast_exp,
            surface_constrained=constrained,
            climate_expectation_m_model_a=exp_a, climate_expectation_source_model_a=exp_src_a,
            delta_m_model_a=delta_a, z_model_a=delta_a / sig if sig > 0 else np.nan,
            resolved_model_a=bool(abs(delta_a) > 2 * sig), rate_mm_per_year_model_a=delta_a / dt_years * 1000))
        step(f"site {s} ({srow['sketch_slack']}, {basis}): Ranwell {rmean:.2f} m OD, modern {v_m:.2f} "
             f"(LOO {loo:.2f}, pos {sig_pos:.2f}, datum {sig_dat:.2f}) -> Δ {delta:+.2f} ± {sig:.2f} m "
             f"(Model A {delta_a:+.2f})"
             + ("" if constrained else f" [modern surface unconstrained: LOO > {config.RANWELL_LOO_MAX_M} m]"))
    lc = pd.DataFrame(lc_rows)

    def _combine(df, label):
        if df.empty:
            return None
        w = 1.0 / df["sigma_total_m"] ** 2
        se = float(np.sqrt(1.0 / w.sum()))
        dof = max(len(df) - 1, 1)
        out = dict(row=label, site_no=np.nan, sketch_slack="", ranwell_basis="", ranwell_n=int(df["ranwell_n"].sum()),
                   n_contributing=len(df), sigma_total_m=se, interval_years=dt_years,
                   sites="; ".join(str(int(s)) for s in df["site_no"]))
        # 1.13.0 (D-332): Model B under the existing columns, Model A as *_model_a
        for sfx in ("", "_model_a"):
            mean = float((df[f"delta_m{sfx}"] * w).sum() / w.sum())
            chi2 = float((((df[f"delta_m{sfx}"] - mean) / df["sigma_total_m"]) ** 2).sum() / dof)
            out.update({f"delta_m{sfx}": mean, f"z{sfx}": mean / se, f"resolved{sfx}": bool(abs(mean) > 2 * se),
                        f"chi2_per_dof{sfx}": chi2, f"rate_mm_per_year{sfx}": mean / dt_years * 1000})
        return out

    comb_all = _combine(lc, "COMBINED_ALL")
    comb_in = _combine(lc[lc["surface_constrained"]], "COMBINED_CONSTRAINED")
    comb_br = _combine(lc[~lc["within_coastal_reach"].astype(bool)], "COMBINED_BEYOND_REACH")
    for c in (comb_all, comb_in, comb_br):
        if c:
            lc = pd.concat([lc, pd.DataFrame([c])], ignore_index=True)
            step(f"{c['row']}: Δ {c['delta_m']:+.3f} ± {c['sigma_total_m']:.3f} m (Model A {c['delta_m_model_a']:+.3f}) "
                 f"over {c['n_contributing']} sites "
                 f"(χ²/dof {c['chi2_per_dof']:.2f}); {c['rate_mm_per_year']:+.1f} mm/yr over {dt_years:.0f} y; "
                 f"{'resolved' if c['resolved'] else 'not resolved'} at 2σ")

    phase(4, "Forcing check — Parc Mawr (Fig. 2) against RAF Valley")
    pm_idx = pd.PeriodIndex([f"{y}-{m:02d}" for y, m in zip(pm["year"], pm["month"])], freq="M")
    raf = (cl["P_m"] * 1000.0)
    raf.index = raf.index.to_period("M")
    cc = pd.DataFrame({"month": pm_idx, "parc_mawr_mm": pm["rain_mm"].values}).set_index("month")
    cc = cc.join(raf.rename("raf_valley_mm"), how="inner")
    cc.index.name = "month"  # the join drops the index name on some pandas builds
    cc["ratio"] = cc["parc_mawr_mm"] / cc["raf_valley_mm"]
    cc = cc.reset_index()
    in_span = cc[(cc["month"] >= SPAN[0]) & (cc["month"] <= SPAN[1])]
    ratio_span = float(in_span["parc_mawr_mm"].sum() / in_span["raf_valley_mm"].sum())
    r_span = float(np.corrcoef(in_span["parc_mawr_mm"], in_span["raf_valley_mm"])[0, 1])
    step(f"1951-02 to 1953-08: Parc Mawr / RAF Valley total {ratio_span:.3f}, monthly r {r_span:.2f} "
         f"({len(in_span)} months)")

    phase(5, "Q4 — the slack floors as a former water table (T-71)")
    clusters = pd.read_csv(paths.INT_CLUSTER_STATS)
    clusters = pd.Series(clusters["Cluster"].astype(int).values, index=clusters["Match_ID"].map(_norm))
    msl26 = pd.read_csv(paths.OUT_26_ANNUAL_PER_WELL)
    msl26["well"] = msl26["well"].map(_norm)
    rn20 = pd.read_csv(paths.OUT_20_REPORT_NUMBERS)
    h0row = rn20[rn20["Parameter"] == "coastal_h0_per_metre"]
    if h0row.empty:
        raise RuntimeError(f"no coastal_h0_per_metre row in {paths.OUT_20_REPORT_NUMBERS.name}: run Script 20")
    h0_per_metre = float(h0row["Value"].iloc[0])
    if not np.isfinite(retreat_1899_2026):
        raise RuntimeError(f"no 1899-2026 pair_extent row in {paths.OUT_40_EPOCH_SERIES.name}: run Script 40")
    rn40 = pd.read_csv(paths.OUT_40_REPORT_NUMBERS)
    r40 = rn40[rn40["Parameter"] == "headline_retreat_rate_2006_2026_m_yr"]
    rate_recent = float(r40["Value"].iloc[0]) if len(r40) else np.nan
    ep = pd.read_csv(paths.OUT_40_EPOCH_SERIES)
    ep = ep[(ep["basis"] == "pair_extent") & (ep["from_epoch"].astype(str) == "1899") & (ep["to_epoch"].astype(str) == "2026")]
    rate_long = retreat_1899_2026 / (float(ep["to_epoch"].iloc[0]) - float(ep["from_epoch"].iloc[0]))
    ranwell = _ranwell_floor_depths(lv, rg)
    sfd, base = slack_floor_datum(wc, loc, clusters, msl26, metrics, ranwell, eroding, cg_L, h0_per_metre,
                                  retreat_1899_2026, rate_recent, rate_long)
    sfd_sites = _ranwell_site_rows(ranwell, sites, metrics, sfd, eroding, cg_L, base, h0_per_metre / 1000.0,
                                   retreat_1899_2026, lc)
    sfd = pd.concat([sfd, sfd_sites], ignore_index=True)
    sfd["cluster"] = sfd["cluster"].astype("Int64")   # site rows may carry no cluster; keep the column integer
    info(f"inland baseline: C{'/'.join(str(c) for c in config.SLACK_FLOOR_BASELINE_CLUSTERS)} at >= L = {cg_L:.0f} m, "
         f"n {base['min'][2]}: depth below floor mean {base['mean'][0]:.3f}, spring {base['spring'][0]:.3f}, "
         f"annual minimum {base['min'][0]:.3f} m (MAD {base['min'][1]:.3f})")
    info(f"retreat term (MODELLED): {h0_per_metre:.2f} mm/m x {retreat_1899_2026:.0f} m, capped at L; "
         f"exponential written as sensitivity only")
    wells_q4 = sfd[sfd["row"] == "well"]
    for c, g in wells_q4.groupby("cluster"):
        c = int(c)
        step(f"C{c}: n {len(g)}, median excess (annual minimum) {g['excess_min_m'].median():+.3f} m, "
             f"modelled retreat {g['retreat_expectation_modelled_m'].median():.3f} m, "
             f"residual {g['residual_after_retreat_min_m'].median():+.3f} m; "
             f"{int(g['within_coastal_reach'].sum())} within L")
    for r in sfd_sites.itertuples():
        step(f"Ranwell site {r.ranwell_site}: his floor {r.ranwell_floor_m_od:.2f} m OD, local floor now "
             f"{r.modern_local_floor_m_od:.2f} (lowered {r.slack_floor_lowering_m:+.2f} m); depth below floor 1951-53 "
             f"{r.ranwell_depth_mean_m:.2f} m, now {getattr(r, 'modern_depth_local_cc_m', float('nan')):.2f} m "
             f"(change {getattr(r, 'depth_change_m', float('nan')):+.2f} m, climate-adjusted)")
    inland = sfd_sites[~sfd_sites["within_coastal_reach"].astype(bool)]
    info(f"inland sites (beyond L), n {len(inland)}: floor lowering median {inland['slack_floor_lowering_m'].median():+.3f} m, "
         f"depth change median {inland['depth_change_m'].median():+.3f} m")

    phase(6, "Q5 — the forest floors (T-72)")
    from utils.water_table import load_dem, drift_rasters       # noqa: PLC0415
    dem_src, dem = load_dem()
    smooth = drift_rasters(dem, float(dem_src.res[0]))["s"]
    drawdown = pd.read_csv(paths.OUT_20_DRAWDOWN_PERWELL)
    canopy = pd.read_csv(paths.CANOPY_HISTORY)
    ground_prep = pd.read_csv(paths.DATA_FOREST_GROUND_PREP) if paths.DATA_FOREST_GROUND_PREP.exists() else pd.DataFrame(columns=["well", "ground_prep", "source"])
    channels = _channel_geoms(config.FOREST_CHANNEL_LINES) if config.FOREST_CHANNEL_LINES else {}
    cc_tab = pd.read_csv(paths.OUT_03_MECHANISTIC_TABLE).set_index("Cluster")
    ep = pd.read_csv(paths.OUT_40_EPOCH_SERIES)
    ep = ep[ep["basis"] == "pair_extent"].set_index(["from_epoch", "to_epoch"])
    mid_year = (pd.Timestamp(config.PREPLANT_WINDOW[0]).year + pd.Timestamp(config.PREPLANT_WINDOW[1]).year) / 2.0
    r_1899_2006, r_2006_2026 = float(ep.loc[("1899", "2006"), "median_m"]), float(ep.loc[("2006", "2026"), "median_m"])
    total_1899_2026 = retreat_1899_2026
    # (a) the 1899-2006 epoch spread evenly across its years (an assumption: no 1950s shoreline exists)
    r_steady = r_1899_2006 * (2006 - mid_year) / (2006 - 1899) + r_2006_2026
    # (b) the modern 2006-2026 rate carried back, capped at the measured total since 1899 (sensitivity)
    r_modern = min(rate_recent * (2026 - mid_year), total_1899_2026) if np.isfinite(rate_recent) else np.nan
    retreat_terms = {"k_per_m": h0_per_metre / 1000.0, "L": cg_L, "steady": r_steady, "modern": r_modern}
    info(f"pre-planting window {config.PREPLANT_WINDOW[0]}..{config.PREPLANT_WINDOW[1]} (mid {mid_year:.0f}); retreat since it: "
         f"steady-epoch {r_steady:.0f} m, modern-rate {r_modern:.0f} m (capped at {total_1899_2026:.0f} m since 1899)")
    ffe = forest_floor_excess(sfd, loc, drawdown, canopy, ground_prep, channels, dem_src, dem, smooth,
                              cl=cl, md=md, cc=cc_tab, wc=wc, retreat_terms=retreat_terms, mbq=mbq)
    dem_src.close()
    info(f"{len(ffe)} reference wells under or at the forest; channel(s) {list(channels)}; "
         f"{int((ffe['ground_prep'] != '').sum())} recorded as prepared ground")
    for g, sub_ in ffe.groupby("group"):
        step(f"{g}: n {len(sub_)}, residual after retreat median {sub_['residual_after_retreat_min_m'].median():+.3f} m, "
             f"modelled canopy drawdown median {sub_['modelled_canopy_drawdown_m'].median():.3f} m")
    c4 = ffe[ffe["cluster"] == 4]
    info(f"C4: residual median {c4['residual_after_retreat_min_m'].median():+.3f} m over {len(c4)} wells; "
         f"channel bed above the floor at every C4 well except where within {config.FLOOR_RELIEF_RADIUS_M:.0f} m: "
         f"{int((c4['channel_bed_above_floor_m'] > 0).sum())}/{len(c4)}")

    phase(7, "Outputs")
    lv_out = lv.merge(sites[["sketch_slack", "basin_id"]], left_on="site_no", right_index=True, how="left")
    hl = metrics[metrics["headline"]][["site_no", "well"]].rename(columns={"well": "headline_well"})
    lv_out = lv_out.merge(hl, on="site_no", how="left").drop(columns=["month"])
    lv_out.to_csv(paths.OUT_44_READINGS, index=False)
    saved(paths.OUT_44_READINGS.name)
    rg_out = rg.merge(sites[["sketch_slack", "basin_id"]], left_on="site_no", right_index=True, how="left")
    rg_out.to_csv(paths.OUT_44_RANGES, index=False)
    saved(paths.OUT_44_RANGES.name)
    if len(series):
        series["month"] = series["month"].astype(str)
    series.to_csv(paths.OUT_44_SERIES, index=False)
    saved(paths.OUT_44_SERIES.name)
    metrics.to_csv(paths.OUT_44_METRICS, index=False)
    saved(paths.OUT_44_METRICS.name)
    lc.to_csv(paths.OUT_44_LEVEL_CHANGE, index=False)
    saved(paths.OUT_44_LEVEL_CHANGE.name)
    cc.assign(month=cc["month"].astype(str)).to_csv(paths.OUT_44_CLIMATE_CHECK, index=False)
    saved(paths.OUT_44_CLIMATE_CHECK.name)
    if len(series):
        series["month"] = pd.PeriodIndex(series["month"], freq="M")
        plot_hindcast(series, metrics, paths.OUT_44_HINDCAST_FIG)
        saved(paths.OUT_44_HINDCAST_FIG.name)
        plot_hindcast(series, metrics, paths.OUT_44_HINDCAST_REPORT_FIG, report=True)
        saved(paths.OUT_44_HINDCAST_REPORT_FIG.name)
    plot_level_change(lc, paths.OUT_44_CHANGE_FIG)
    saved(paths.OUT_44_CHANGE_FIG.name)
    sfd.to_csv(paths.OUT_44_SLACK_FLOOR_DATUM, index=False)
    saved(paths.OUT_44_SLACK_FLOOR_DATUM.name)
    plot_slack_floor_datum(sfd, base, cg_L, h0_per_metre / 1000.0, retreat_1899_2026, paths.OUT_44_SLACK_FLOOR_FIG)
    saved(paths.OUT_44_SLACK_FLOOR_FIG.name)
    ffe.to_csv(paths.OUT_44_FOREST_FLOOR, index=False)
    saved(paths.OUT_44_FOREST_FLOOR.name)
    plot_forest_floor_excess(ffe, paths.OUT_44_FOREST_FIG)
    saved(paths.OUT_44_FOREST_FIG.name)

    hlm = metrics[metrics["headline"]]
    rn = [
        ("ranwell_hindcast_sites", len(hlm), "count", "Ranwell sites with a printed series and a same-basin paired well"),
    ]
    # 1.13.0 (D-332): the hindcast keys keep their names and carry Model B (the forecaster); Model A at
    # the fixed floor follows as <key>_model_a and Model A at mean high water as <key>_mhw (Scenario 3).
    for sfx, csfx, lab in (("", "_modelB", "Model B"), ("_model_a", "", f"Model A at {DATUM:g} m"),
                           ("_mhw", "_mhw", "Model A at mean high water")):
        _r, _n = f"r{csfx}", f"nse_after_offset{csfx}"
        if _n not in metrics.columns:
            continue
        hl_ = hlm[hlm[_n].notna()]
        al_ = metrics[metrics[_n].notna()]
        rn += [
            (f"ranwell_hindcast_r_median{sfx}", float(hl_[_r].median()) if len(hl_) else np.nan, "-",
             f"{lab}: median r, headline pairing, offset removed"),
            (f"ranwell_hindcast_r_min{sfx}", float(hl_[_r].min()) if len(hl_) else np.nan, "-",
             f"{lab}: lowest r among the headline pairings"),
            # 1.10.0 (emit-first, report9): r over EVERY same-basin pairing, headline or not.
            (f"ranwell_hindcast_r_min_all_pairings{sfx}", float(al_[_r].min()) if len(al_) else np.nan, "-",
             f"{lab}: lowest r over the {len(al_)} same-basin site-well pairings in 44_04 it was run at "
             "(headline and alternates), offset removed"),
            (f"ranwell_hindcast_r_max_all_pairings{sfx}", float(al_[_r].max()) if len(al_) else np.nan, "-",
             f"{lab}: highest r over the {len(al_)} same-basin site-well pairings in 44_04 it was run at"),
            (f"ranwell_hindcast_nse_median{sfx}", float(hl_[_n].median()) if len(hl_) else np.nan, "-",
             f"{lab}: median NSE after offset, headline pairing ({len(hl_)} sites)"),
            (f"ranwell_hindcast_nse_median_all_pairings{sfx}", float(al_[_n].median()) if len(al_) else np.nan, "-",
             f"{lab}: median NSE after offset over the {len(al_)} same-basin pairings it was run at"),
            (f"ranwell_hindcast_n_pairings{sfx}", int(len(al_)), "count",
             f"{lab}: same-basin pairings scored (of {len(metrics)})"),
        ]
    if len(metrics):
        _kp = {normalize_well_name(w_) for w_ in metrics["well"]}
        rn += [
            ("ranwell_model_b_bound_binds_n", int(len(_kp & mb_binds)), "count",
             f"paired wells whose Model B beta_3 sits at the lower bound MODEL_B_BETA3_MIN ({B3_MIN:g}/month); fit kept"),
            ("ranwell_model_b_excluded_datum_n", int(len(_kp & set(mb_undef))), "count",
             "paired wells with no Model B: implied datum DRAINAGE_DATUM - alpha/beta_3 not below ground"),
        ]
        for _win in FIT_WINDOWS:
            _bk = {normalize_well_name(w_) for w_ in win_b_binds[_win]}
            _uk = {normalize_well_name(w_) for w_ in win_b_undef[_win]}
            rn += [(f"ranwell_model_b_bound_binds_n_{_win}", int(len(_kp & _bk)), "count",
                    f"paired wells whose {_win}-window Model B refit binds at the beta_3 bound (fit kept)"),
                   (f"ranwell_model_b_excluded_datum_n_{_win}", int(len(_kp & _uk)), "count",
                    f"paired wells whose {_win}-window Model B refit has no datum below ground (left out)")]
        if np.isfinite(mhw):
            rn.append(("ranwell_tide_mhw_m_used", mhw, "m OD", "mean high water the MHW form is run at (Script 01b tide_mhw_m)"))
    rn += [
        ("ranwell_sites_compared", int((lc["row"] == "site").sum()), "count", "sites with a Ranwell mean and a modern surface"),
        ("ranwell_interval_years", dt_years, "y", "modern record midpoint minus 1952"),
        ("ranwell_shoreline_retreat_1899_2026_m", retreat_1899_2026, "m", "Script 40 median shoreline retreat 1899-2026, context for the seaward sites"),
        ("ranwell_sites_surface_constrained", int(lc.loc[lc["row"] == "site", "surface_constrained"].sum()), "count",
         f"sites whose modern-surface leave-one-out error is <= {config.RANWELL_LOO_MAX_M} m"),
        ("ranwell_forcing_ratio_1951_53", ratio_span, "-", "Parc Mawr / RAF Valley rainfall over Ranwell's span"),
        ("ranwell_forcing_r_1951_53", r_span, "-", "monthly correlation of the two gauges over Ranwell's span"),
    ]
    # 1.13.0 (D-332): the climate-only expectation and everything built on it carry Model B; Model A's
    # values follow as <key>_model_a. The error terms do not depend on the model and have no twin.
    for sfx, lab in (("", "Model B"), ("_model_a", f"Model A at {DATUM:g} m")):
        _ce = lc.loc[lc["row"] == "site", f"climate_expectation_m{sfx}"].abs()
        rn.append((f"ranwell_climate_expectation_abs_max_m{sfx}", float(_ce.max()) if _ce.notna().any() else np.nan, "m",
                   f"{lab}: largest magnitude of the climate-only expectation (1951-53 against the modern hindcast) "
                   f"over the {int(_ce.notna().sum())} compared sites in 44_05"))
    for r in lc[lc["row"] == "site"].itertuples():
        rn.append((f"ranwell_delta_m_site{int(r.site_no)}", r.delta_m, "m", f"site {int(r.site_no)} ({r.sketch_slack}): modern minus 1951-53, climate-corrected (Model B)"))
        rn.append((f"ranwell_delta_m_site{int(r.site_no)}_model_a", r.delta_m_model_a, "m",
                   f"site {int(r.site_no)}: the same, climate-corrected with Model A at {DATUM:g} m"))
        rn.append((f"ranwell_sigma_m_site{int(r.site_no)}", r.sigma_total_m, "m", f"site {int(r.site_no)}: four-term error"))
    # T-96: each compared site's distance to the nearest in_forest well (placed position,
    # the easting/northing every other site distance here uses).
    if "in_forest" in loc.columns:
        fw = loc[loc["in_forest"].astype(bool)]
        d_by_group: dict[str, list[tuple[int, float]]] = {}
        for r in lc[lc["row"] == "site"].itertuples():
            srow = sites.loc[r.site_no]
            d_fw = np.hypot(fw["E"] - float(srow["easting"]), fw["N"] - float(srow["northing"]))
            rn.append((f"ranwell_dist_nearest_forest_well_m_site{int(r.site_no)}", float(d_fw.min()), "m",
                       f"site {int(r.site_no)} ({r.sketch_slack}): distance from the placed position to the nearest "
                       f"in_forest well (01_locations), {fw.loc[d_fw.idxmin(), 'Name']}; {len(fw)} forest wells"))
            d_by_group.setdefault(str(r.sketch_slack), []).append((int(r.site_no), float(d_fw.min())))
        # T-96 batch 3: the range over each sketch_slack group (43_01), so a sentence quoting
        # the span for a slack (Clwt Gwlyb = CG) cites a key, not a reading of per-site rows.
        for g, v in d_by_group.items():
            ids = ", ".join(str(s_) for s_, _ in sorted(v))
            for tag, fn in (("min", min), ("max", max)):
                s_, d_ = fn(v, key=lambda t: t[1])
                rn.append((f"ranwell_dist_nearest_forest_well_m_{g}_{tag}", d_, "m",
                           f"{g} (sites {ids}): {'smallest' if tag == 'min' else 'largest'} distance from a placed "
                           f"position to the nearest in_forest well (01_locations), at site {s_}"))
    rn += [("ranwell_coastal_fit_delta0_mm_yr", cg_d0, "mm/yr", f"Script 25 {src_} {mod_} delta_0 used for the coastal expectation"),
           ("ranwell_coastal_fit_L_m", cg_L, "m", f"Script 25 {src_} {mod_} reach L"),
           ("ranwell_sites_within_coastal_reach", int(lc.loc[lc["row"] == "site", "within_coastal_reach"].astype(bool).sum()), "count",
            "sites nearer the eroding shoreline than L")]
    for r in lc[lc["row"] == "site"].itertuples():
        rn.append((f"ranwell_coastal_expectation_m_site{int(r.site_no)}", r.coastal_expectation_extrapolated_m, "m",
                   f"site {int(r.site_no)}: Script 25 rate at {r.dist_eroding_hwm_m:.0f} m from the eroding shoreline, "
                   "carried across the interval (extrapolated)"))
    for c in (comb_all, comb_in, comb_br):
        if c:
            k = c["row"].lower()
            rn.append((f"ranwell_sigma_m_{k}", c["sigma_total_m"], "m", f"{c['row']}: standard error"))
            for sfx, lab in (("", "Model B"), ("_model_a", f"Model A at {DATUM:g} m")):
                rn += [(f"ranwell_delta_m_{k}{sfx}", c[f"delta_m{sfx}"], "m", f"{c['row']}: inverse-variance mean over {c['n_contributing']} sites ({lab})"),
                       (f"ranwell_chi2_dof_{k}{sfx}", c[f"chi2_per_dof{sfx}"], "-", f"{c['row']}: chi-square per degree of freedom ({lab})"),
                       (f"ranwell_rate_mm_yr_{k}{sfx}", c[f"rate_mm_per_year{sfx}"], "mm/yr", f"{c['row']}: delta over the interval ({lab})"),
                       (f"ranwell_resolved_{k}{sfx}", int(c[f"resolved{sfx}"]), "flag", f"{c['row']}: |delta| > 2 sigma ({lab})"),
                       (f"ranwell_delta_lower_2sigma_m_{k}{sfx}", c[f"delta_m{sfx}"] - 2 * c["sigma_total_m"], "m",
                        f"{c['row']}: delta - 2 x standard error; a fall larger than this is excluded ({lab})"),
                       (f"ranwell_delta_upper_2sigma_m_{k}{sfx}", c[f"delta_m{sfx}"] + 2 * c["sigma_total_m"], "m",
                        f"{c['row']}: delta + 2 x standard error; a rise larger than this is excluded ({lab})")]
    for stat, lab in (("mean", "full-record mean"), ("spring", "spring level (D-189/D-207)"), ("min", "annual minimum")):
        rn += [(f"slack_floor_baseline_depth_{stat}_m", base[stat][0], "m",
                f"inland baseline: median depth of the {lab} below the slack floor, C"
                + "/".join(str(c) for c in config.SLACK_FLOOR_BASELINE_CLUSTERS) + " wells at or beyond L"),
               (f"slack_floor_baseline_depth_{stat}_mad_m", base[stat][1], "m", f"inland baseline ({lab}): median absolute deviation")]
    rn.append(("slack_floor_baseline_n", base["min"][2], "count", "wells in the inland baseline"))
    # 1.11.0: which open-dune wells within the coastal reach stand ELEVATED above the inland baseline -
    # by more than config.RANWELL_ELEVATED_K_SIGMA standard errors of the combined 1951-53 comparison
    # (report9 SS4.14.2).
    if comb_all:
        _thr = config.RANWELL_ELEVATED_K_SIGMA * float(comb_all["sigma_total_m"])
        _od = wells_q4[~wells_q4["cluster"].isin(config.FOREST_CIDS) & wells_q4["within_coastal_reach"].astype(bool)]
        _ev = _od[_od["excess_min_m"] > _thr]
        _nev = _od[_od["excess_min_m"] <= _thr]
        _k = f"{config.RANWELL_ELEVATED_K_SIGMA:g} x ranwell_sigma_m_combined_all"
        rn += [("slack_floor_reach_open_dune_n", int(len(_od)), "count",
                "open-dune wells (clusters not in FOREST_CIDS) within the coastal reach"),
               ("slack_floor_reach_elevated_threshold_m", _thr, "m",
                f"ELEVATED threshold on the annual-minimum excess over the inland baseline: {_k}"),
               ("slack_floor_reach_elevated_n", int(len(_ev)), "count", f"of those, wells whose excess exceeds {_k}"),
               ("slack_floor_reach_not_elevated_n", int(len(_nev)), "count", f"of those, wells whose excess does not exceed {_k}")]
        if len(_ev):
            rn += [("slack_floor_reach_elevated_excess_min_m", float(_ev["excess_min_m"].min()), "m",
                    "smallest annual-minimum excess over the inland baseline among the elevated wells"),
                   ("slack_floor_reach_elevated_excess_max_m", float(_ev["excess_min_m"].max()), "m",
                    "largest annual-minimum excess over the inland baseline among the elevated wells")]
        if len(_nev):
            rn.append(("slack_floor_reach_not_elevated_excess_max_m", float(_nev["excess_min_m"].max()), "m",
                       "largest annual-minimum excess among the wells that are not elevated"))
    for c, g in wells_q4.groupby("cluster"):
        c = int(c)
        rn += [(f"slack_floor_depth_min_median_C{c}_m", float(g["depth_min_m"].median()), "m", f"C{c}: median depth of the annual minimum below the floor"),
               (f"slack_floor_depth_spring_median_C{c}_m", float(g["depth_spring_m"].median()), "m", f"C{c}: median depth of the spring level below the floor"),
               (f"slack_floor_excess_min_median_C{c}_m", float(g["excess_min_m"].median()), "m", f"C{c}: median excess of the annual-minimum depth over the inland baseline"),
               (f"slack_floor_retreat_expectation_median_C{c}_m", float(g["retreat_expectation_modelled_m"].median()), "m",
                f"C{c}: median MODELLED retreat response, coastal_h0_per_metre x 1899-2026 retreat, capped at L (extrapolated)"),
               (f"slack_floor_residual_min_median_C{c}_m", float(g["residual_after_retreat_min_m"].median()), "m", f"C{c}: median excess less the modelled retreat response"),
               (f"slack_floor_wells_within_reach_C{c}", int(g["within_coastal_reach"].sum()), "count", f"C{c}: wells nearer the eroding shoreline than L")]
    for r in sfd_sites.itertuples():
        s_ = int(r.ranwell_site)
        rn += [(f"ranwell_floor_m_od_site{s_}", r.ranwell_floor_m_od, "m OD", f"site {s_}: Ranwell's floor, level + depth from the digitised readings ({r.ranwell_basis})"),
               (f"ranwell_depth_mean_1951_53_site{s_}_m", r.ranwell_depth_mean_m, "m", f"site {s_}: 1951-53 mean depth below his floor"),
               (f"ranwell_depth_max_1951_53_site{s_}_m", r.ranwell_depth_max_m, "m", f"site {s_}: deepest 1951-53 reading below his floor"),
               (f"ranwell_local_floor_site{s_}_m_od", r.modern_local_floor_m_od, "m OD", f"site {s_}: the modern local floor at the placed position (Script 43 Route F)"),
               (f"ranwell_floor_lowering_site{s_}_m", r.slack_floor_lowering_m, "m", f"site {s_}: Ranwell's floor minus the modern local floor (positive = the floor is lower now)"),
               (f"ranwell_depth_change_site{s_}_m", getattr(r, "depth_change_m", np.nan), "m",
                f"site {s_}: modern depth below the local floor (kriged mean level, climate-adjusted with Model B) minus his 1951-53 mean depth below his floor (positive = deeper now)"),
               (f"ranwell_depth_change_site{s_}_m_model_a", getattr(r, "depth_change_m_model_a", np.nan), "m",
                f"site {s_}: the same, climate-adjusted with Model A at {DATUM:g} m")]
        if r.well:
            rn += [(f"ranwell_pairedwell_floor_lowering_site{s_}_m", r.pairedwell_floor_lowering_m, "m", f"site {s_} vs {r.well} (diagnostic): Ranwell's floor minus the headline well's floor"),
                   (f"ranwell_pairedwell_depth_change_mean_site{s_}_m", r.pairedwell_depth_change_mean_m, "m", f"site {s_} vs {r.well} (diagnostic): modern mean depth minus 1951-53 mean depth, floor to floor"),
                   (f"ranwell_pairedwell_depth_change_spring_site{s_}_m", r.pairedwell_depth_change_spring_m, "m", f"site {s_} vs {r.well} (diagnostic): spring depth change, floor to floor"),
                   (f"ranwell_pairedwell_depth_change_max_site{s_}_m", r.pairedwell_depth_change_max_m, "m", f"site {s_} vs {r.well} (diagnostic): modern annual minimum minus his deepest reading, floor to floor")]
    for col, key, lab, sfx in (("slack_floor_lowering_m", "ranwell_floor_lowering_inland", "floor lowering, his floor minus the local floor", ""),
                               ("depth_change_m", "ranwell_depth_change_inland", "depth change below the floor, climate-adjusted (Model B)", ""),
                               ("depth_change_m_model_a", "ranwell_depth_change_inland",
                                f"depth change below the floor, climate-adjusted with Model A at {DATUM:g} m", "_model_a")):
        v = inland[col].dropna()
        rn += [(f"{key}_median_m{sfx}", float(v.median()) if len(v) else np.nan, "m", f"median over the {len(v)} sites beyond L: {lab}"),
               (f"{key}_mad_m{sfx}", float((v - v.median()).abs().median()) if len(v) else np.nan, "m", f"median absolute deviation over the sites beyond L: {lab}"),
               (f"{key}_n{sfx}", len(v), "count", "sites beyond L in the median")]
    for name, col in (("local_floor", "modern_local_floor_m_od"), ("floor_mask_mean", "modern_floor_mask_mean_m_od")):
        rr = (inland[col] - inland["ranwell_floor_m_od"]).dropna()
        rn += [(f"ranwell_floor_fit_bias_inland_{name}_m", float(rr.mean()) if len(rr) else np.nan, "m", f"{name} minus Ranwell's floor, mean over the {len(rr)} reading sites beyond L"),
               (f"ranwell_floor_fit_rmse_inland_{name}_m", float(np.sqrt((rr ** 2).mean())) if len(rr) else np.nan, "m", f"{name} against Ranwell's floor, RMSE over the {len(rr)} reading sites beyond L")]
    for c_ in (4, 5):
        sub_ = ffe[ffe["cluster"] == c_]
        v = sub_["residual_after_retreat_min_m"]
        rn += [(f"forest_floor_residual_median_C{c_}_m", float(v.median()) if len(v) else np.nan, "m", f"C{c_}: median excess of the annual-minimum depth over the open-dune baseline, less the modelled retreat response"),
               (f"forest_floor_residual_min_C{c_}_m", float(v.min()) if len(v) else np.nan, "m", f"C{c_}: smallest residual"),
               (f"forest_floor_residual_max_C{c_}_m", float(v.max()) if len(v) else np.nan, "m", f"C{c_}: largest residual"),
               (f"forest_floor_n_C{c_}", len(v), "count", f"C{c_} wells in 44_10"),
               (f"forest_floor_residual_over_modelled_drawdown_median_C{c_}", float(sub_["residual_over_modelled_drawdown"].median()) if len(v) else np.nan, "-",
                f"C{c_}: median residual over the MODELLED canopy drawdown at the wells (Script 20 dd_mm)")]
    for g, sub_ in ffe.groupby("group"):
        v = sub_["residual_after_retreat_min_m"]
        rn += [(f"forest_floor_residual_median_{g}_m", float(v.median()), "m", f"{g}: median residual after retreat over {len(v)} forest wells"),
               (f"forest_floor_residual_min_{g}_m", float(v.min()), "m", f"{g}: smallest residual after retreat"),
               (f"forest_floor_residual_max_{g}_m", float(v.max()), "m", f"{g}: largest residual after retreat"),
               (f"forest_floor_n_{g}", len(v), "count", f"forest wells in the {g} group")]
    # 1.9.0 (Martin, 2026-10-03: "write an output for does not differ"): the felled wells against the unfelled
    # canopy, two-sided Mann-Whitney on the residual after retreat; "differs" at FOREST_FLOOR_GROUP_TEST_P
    from scipy.stats import mannwhitneyu                       # noqa: PLC0415
    fel = ffe[ffe["group"].str.startswith("felled_")]["residual_after_retreat_min_m"].dropna()
    can_ = ffe[ffe["group"] == "canopy"]["residual_after_retreat_min_m"].dropna()
    if len(fel) and len(can_):
        mw = mannwhitneyu(fel, can_, alternative="two-sided")
        rn += [("forest_floor_felled_vs_canopy_mw_p", float(mw.pvalue), "p",
                f"two-sided Mann-Whitney, felled wells (n {len(fel)}) against unfelled canopy (n {len(can_)}), residual after retreat"),
               ("forest_floor_felled_vs_canopy_differs", float(mw.pvalue < config.FOREST_FLOOR_GROUP_TEST_P), "flag",
                f"1 if the felled and canopy residuals differ at p < {config.FOREST_FLOOR_GROUP_TEST_P} (0: they do not)")]
    if "climate_change_since_preplant_min_m" in ffe.columns:
        c4 = ffe[ffe["cluster"] == 4]
        c5 = ffe[ffe["cluster"] == 5]
        rn.append(("forest_floor_preplant_window", f"{config.PREPLANT_WINDOW[0]} to {config.PREPLANT_WINDOW[1]}", "-", "the pre-planting window the climate-only hindcast is compared over (config)"))
        # 1.13.0 (D-332): Model B (03_16 own coefficients or centroids, each at its implied datum) under
        # the existing keys; Model A (master store, 03_03 centroids, the 3.7 m floor) as <key>_model_a
        for sfx, lab in (("", "Model B"), ("_model_a", f"Model A at {DATUM:g} m")):
            rn += [(f"forest_floor_climate_change_since_preplant_mean_median_C4_m{sfx}", float(c4[f"climate_change_since_preplant_mean_m{sfx}"].median()), "m",
                    f"C4: median climate-only change in the mean level, pre-planting window minus the well's record (own or cluster coefficients driven by RAF Valley from 1930; + = the window stood higher); {lab}"),
                   (f"forest_floor_climate_change_since_preplant_min_median_C4_m{sfx}", float(c4[f"climate_change_since_preplant_min_m{sfx}"].median()), "m", f"C4: the same for the annual minimum; {lab}"),
                   (f"forest_floor_climate_change_since_preplant_min_median_C4_analogue_m{sfx}", float(c4[f"climate_change_since_preplant_min_analogue_m{sfx}"].median()), "m",
                    f"C4: the same with its open-dune analogue's centroid coefficients (C{config.PRECANOPY_ANALOGUE[4]}; pre-planting behaviour sensitivity, D-254); {lab}"),
                   (f"forest_floor_climate_change_since_preplant_mean_median_C4_analogue_m{sfx}", float(c4[f"climate_change_since_preplant_mean_analogue_m{sfx}"].median()), "m",
                    f"C4: the mean-level change with its open-dune analogue's coefficients (C{config.PRECANOPY_ANALOGUE[4]}, D-254); {lab}"),
                   (f"forest_floor_climate_change_since_preplant_min_median_C5_analogue_m{sfx}", float(c5[f"climate_change_since_preplant_min_analogue_m{sfx}"].median()) if len(c5) else np.nan, "m",
                    f"C5: annual-minimum change with its open-dune analogue's coefficients (C{config.PRECANOPY_ANALOGUE[5]}, D-254); n = {len(c5)} wells; {lab}"),
                   (f"forest_floor_climate_change_since_preplant_mean_median_C5_analogue_m{sfx}", float(c5[f"climate_change_since_preplant_mean_analogue_m{sfx}"].median()) if len(c5) else np.nan, "m",
                    f"C5: mean-level change with its open-dune analogue's coefficients (C{config.PRECANOPY_ANALOGUE[5]}, D-254); n = {len(c5)} wells; {lab}"),
                   (f"forest_floor_residual_after_climate_and_retreat_steady_median_C4_m{sfx}", float(c4[f"residual_after_climate_and_retreat_steady_min_m{sfx}"].median()), "m", f"C4: median excess of the annual minimum after the climate-only change and the steady-epoch retreat term; {lab}"),
                   (f"forest_floor_residual_after_climate_and_retreat_modern_median_C4_m{sfx}", float(c4[f"residual_after_climate_and_retreat_modern_min_m{sfx}"].median()), "m", f"C4: the same with the modern-rate retreat sensitivity; {lab}"),
                   (f"forest_floor_wells_cluster_coefficients{sfx}", int((ffe[f"preplant_coef_basis{sfx}"] != "own").sum()), "count", f"forest wells hindcast with cluster coefficients because beta_3 is not identified (p >= {config.PREPLANT_BETA3_P_MAX}); {lab}")]
        rn += [("forest_floor_retreat_since_preplant_steady_m", float(ffe["retreat_since_preplant_steady_m"].iloc[0]), "m", "shoreline retreat since the window, the 1899-2006 epoch spread evenly (assumption) plus 2006-2026"),
               ("forest_floor_retreat_since_preplant_modern_m", float(ffe["retreat_since_preplant_modern_m"].iloc[0]), "m", "sensitivity: the 2006-2026 rate carried back over the interval, capped at the measured total since 1899")]
    rn += [("forest_floor_modelled_drawdown_at_wells_m", float(ffe["modelled_canopy_drawdown_m"].median()), "m", "median MODELLED canopy drawdown at the forest wells (Script 20 dd_mm; config.DRAWDOWN_H0_MM inside the forest)"),
           ("forest_floor_litter_allowance_m", config.FOREST_LITTER_MAX_M, "m", "upper bound on the litter above the mineral floor under the canopy (config, Martin 2026-09-29)"),
           ("forest_floor_residual_less_litter_median_C4_m", float((ffe.loc[ffe["cluster"] == 4, "residual_after_retreat_min_m"] - config.FOREST_LITTER_MAX_M).median()), "m", "C4: median residual after retreat less the litter allowance (lower bound on the mineral-floor excess)"),
           ("forest_floor_channel_lines", "; ".join(config.FOREST_CHANNEL_LINES), "-", "Features.kml line(s) taken as drainage channels (Martin, 2026-09-29)"),
           ("forest_floor_wells_channel_bed_above_floor", int((ffe["channel_bed_above_floor_m"] > 0).sum()), "count", "forest wells whose nearest channel bed lies above their floor"),
           ("forest_floor_wells_ploughed", int((ffe["ground_prep"] != "").sum()), "count", "forest wells on ground recorded as prepared before planting (data/forest_ground_prep.csv)")]
    pd.DataFrame(rn, columns=["key", "value", "unit", "note"]).to_csv(paths.OUT_44_REPORT_NUMBERS, index=False)
    saved(paths.OUT_44_REPORT_NUMBERS.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
