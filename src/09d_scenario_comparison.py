r"""
====================================================================================
09d — CEH36 SCENARIO COMPARISON
====================================================================================
Purpose
-------
Compares the observed scraping benefit at CEH36 against what alternative
interventions would have achieved at the same well.  Uses CEH36's own SSM
coefficients, Sy, and mean head displacement to compute the SUSTAINED level change
(as stored water, mm w.e.) for clearfell, thinning, broadleaf conversion, and UKCP18
climate scenarios, beside the observed scraping step (4.0.0, D-349 B2: every bar is a
sustained level, as D-239 says; before 4.0.0 the non-scraping bars were one-month fluxes).

This answers the management question: "was scraping a good choice for this
site compared to alternatives?"

Two figures:
  1. Sustained change in stored water (mm w.e.) at CEH36, annual-mean forcing
  2. The same under summer-mean forcing

All parameters read from upstream pipeline outputs (Scripts 01, 03, 17).
Forestry and climate scenario constants from config.py.

Outputs
-------
CSVs:
  09d_01_ceh36_scenario_comparison.csv  — monthly values
  09d_02_ceh36_summer_scenario.csv      — summer minimum values

Figures:
  09d_01_scenario_comparison.jpg        — monthly bar chart
  09d_02_summer_scenario_comparison.png — summer minimum bar chart

References
----------
Hollingham (2026), §4.5.  Part of the Script 09 scraping analysis suite.
====================================================================================
"""

__version__ = "4.0.0"  # 2026-11-27 (D-349 B2, B3, A15): every bar a sustained level change (D-239): the clearfell, thinning, broadleaf and climate bars go from a one-month flux change ("mm/month") to the sustained level on CEH36's beta_3 x Sy (mm w.e.), beside the scraping step, which was already a level; the match distance is level against level; the clearfell and thinning bars carry the anchor range (drift free / drift fixed / drift-free DiD) as columns, whiskers and report rows; f on WMC3's own fit. CSV columns renamed Delta_storage_sustained_mm / _summer_mm. Was "3.14.0"  # Hollingham (2026) - 2026-11-20 (T-209, D-333; changelog 2026-11-20b). The hypothetical Clearfell
#   and Thinning 50% bars at CEH36 return a share f of the interception (clearfell_common.clearfell_return_fraction,
#   calibrated on the observed BACI step at the felled well; thinning f/2) instead of a beta_2 multiplier. The D-333
#   flags, status column and count key are gone; CLEARFELL_MATCH_HINT (282 m, set against the old bar) is now
#   computed and emitted as scenario_clearfell_match_distance_m.
# 3.13.0  # Hollingham (2026) - 2026-11-12 (D-333, J-9 phase 2b). The hypothetical Clearfell and
#   Thinning 50% bars at CEH36 take a beta_2 multiplier of single-well era refits
#   (clearfell_common.load_clearfell_impact_b2_multiplier) and are WITHDRAWN under D-333 pending T-209. No value
#   changes: 09d_01 / 09d_02 gain a `status` column ("withdrawn (D-333)" on those rows), their tick labels say so,
#   one warn() names them, and a new 09d_report_numbers.csv (paths.OUT_09D_REPORT_NUMBERS; 09d had none) carries
#   the count scenario_n_rows_withdrawn_d333. The scraping bars here are the observed BACI step and the drain-cone
#   drawdown (no delta-beta_3), and Broadleaf and the climate bars use no era-refit multiplier: none is withdrawn.
# 3.12.0  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b). CEH36's betas from 03_master_data are
#   now Model B, so h_disp is measured from CEH36's implied datum (implied_datum_m = DRAINAGE_DATUM - alpha/beta_3)
#   rather than DRAINAGE_DATUM. Every bar is a difference of two fluxes at the same b3 and h_disp, so the datum (and
#   alpha) cancels exactly and no bar depends on it: the change is to the h_disp the console prints. Bars move only
#   with the Model B betas themselves.
# 3.11.0  # Hollingham (2026) — 2026-10-04 (D-239; Martin: "All five, then ship"). The hypothetical
#   forestry bars at CEH36 are on the D-239 basis: the felled well's measured beta_2 change
#   (clearfell_common.load_clearfell_impact_b2_multiplier; thinning half), and no interception recharge term -
#   the pine baseline's P is kept in every forestry scenario. Broadleaf keeps its summer beta_2 multiplier.
#   The observed scraping bar and the climate bars are unchanged.
# 3.10.2  # Hollingham (2026) — 2026-08-19. Reads the per-well
#   WTF Sy table from OUT_18_WELL_SY_TABLE; INT_WTF_WELL_SY is retired
#   (D-038). Pure path/symbol change, values identical.
#
# v3.10.1  # Hollingham (2026) -- 2026-08-18. Figure captions
#   built their distances from typed literals - "bar = 100 m", "= 250 m",
#   "at ~282 m" - beside a lambda already interpolated live. They now read
#   OFFSITE_DIST_M, OFFSITE_FAR_M and CLEARFELL_MATCH_HINT, so moving a
#   constant moves the caption with it.
#
# v3.10.0  # Hollingham (2026) — 2026-08-16
#
# 3.10.0 (2026-08-16): the "else -0.7" mean-depth fallback removed - it stood
#   in for a value that is always present, and would have silently shifted
#   h_disp had it fired. Missing CEH36 now raises. See DECISION_LOG D-014.
# 3.9.0 (2026-08-16): both Sy fallbacks now route through
#   pipeline_params.default_value("Sy"). The row-missing branch previously used
#   a hard-coded 0.30 predating that convention; it is now 0.25, the documented
#   default, so the two fallback paths cannot disagree. See DECISION_LOG D-014.
# 3.8.0 (2026-08-16): the per-well Sy read (OUT_18_WELL_SY_TABLE, produced at
# step 22 against this script's step 9) is now guarded and falls back to
# pipeline_params.default_value("Sy") with a warning, instead of hard-failing
# on a first pass.
# 3.7.0 (2026-07-02): prior state.
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.paths import (
    make_all_dirs, OUT_09D_SCENARIO, OUT_09D_SCENARIO_CSV,
    OUT_09D_SUMMER_SCENARIO, OUT_09D_SUMMER_SCENARIO_CSV, INT_MASTER_DATA,
    OUT_18_WELL_SY_TABLE, INT_WELLS_CLEAN,
    OUT_20_REPORT_NUMBERS,
)
from utils.site_observations import load_site_observation
from utils.scraping_common import (
    MPL_DEFAULTS,
    load_summer_climate,
    load_annual_climate,
)
from utils.config import (
    BW_MODE,
    FOREST_INTERCEPTION, BROADLEAF_B2_SUMMER,
    UKCP18_DRY_P_SUMMER, UKCP18_DRY_PET_SUMMER,
    UKCP18_WET_P_SUMMER, UKCP18_WET_PET_SUMMER,
    SCRAPE_RISE_BUFFER_M, SUMMER_MINIMUM_MONTHS,
)
from utils.clearfell_common import (clearfell_return_fraction_range,   # 4.0.0 (D-349 B3)
                                    CLEARFELL_ANCHORS, CLEARFELL_ANCHOR_LABELS)
from utils.model_utils import sustained_monthly_response           # 4.0.0 (D-349 B2)
from utils.paths import OUT_09D_REPORT_NUMBERS                # 3.13.0 (D-333)
from utils.report_numbers_utils import ReportNumbers          # 3.13.0 (D-333)

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import render_figure



# ============================================================================
# CONSTANTS
# ============================================================================
# The CEH36 Pure_Scraping BACI step is read from the pipeline site-
# observations registry (utils/site_observations.py).  The producer is
# Script 09a; the consumer here just loads it.  This replaces an earlier
# hardcoded value (0.131 m) which drifted from 09a's actual output as
# the analysis evolved (Item 9 in flags log).  If 09a has not yet been
# run on this clone, load_site_observation() returns the default and
# prints a one-line warning recommending a fresh pipeline run.
WELL = "ceh36"

# ----------------------------------------------------------------------------
# Off-site scraping drawdown (neighbour effect)
# ----------------------------------------------------------------------------
# The scrape acts as a local drain: the slack fills (measured on-site benefit)
# while the surrounding water table is drawn DOWN toward it. That neighbour
# drawdown is modelled by the same steady-state drain cone that feeds the
# Script 20 spatial maps:  dd_head(d) = H0 * exp(-(d - buffer) / λ), with
#   H0     = scrape-edge head drawdown = measured CEH36 response (mm),
#   λ      = leaky-aquifer decay length, read LIVE from 20_report_numbers.csv
#            (drawdown_lambda) so this script never re-derives it,
#   buffer = SCRAPE_RISE_BUFFER_M, radius of the rise (slack) zone.
# On the figures the head drawdown is rendered on the volumetric axis (× Sy),
# matching the on-site scraping bar's own head→volumetric conversion.
# 100 m is a representative near-field distance inside the band the 88-well
# network cannot resolve (nearest uphill well 247 m); the bar is therefore a
# MODELLED quantity, flagged as such in the captions.
OFFSITE_DIST_M       = 100.0
OFFSITE_FAR_M        = 250.0    # marker line inside the OFFSITE_DIST_M bar
                                # (near the nearest uphill well)
# SCRAPE_RISE_BUFFER_M now imported from config.py


def _load_drawdown_lambda():
    """Read leaky-aquifer decay length λ (m) live from Script 20 output.

    Falls back to the documented first-pass default (with a one-line warning)
    only if Script 20 has not been run on this clone, so a figure is still
    produced but flagged. The fallback is read from pipeline_params rather than
    typed here: a literal in this function drifted 3 m from the live value and
    still called itself the default.
    """
    try:
        df = pd.read_csv(OUT_20_REPORT_NUMBERS)
        row = df[df["Parameter"] == "drawdown_lambda"]
        if not row.empty:
            return float(row["Value"].iloc[0])
    except (FileNotFoundError, KeyError, ValueError):
        pass
    from utils.pipeline_params import default_value
    lam = float(default_value("drawdown_lambda_m"))
    warn(f"20_report_numbers.csv not found — using fallback λ = {lam:.1f} m. "
         "Run Script 20 for the live value.")
    return lam


def _offsite_scrape_head_mm(scrape_edge_head_mm, dist_m=OFFSITE_DIST_M):
    """Modelled neighbour head drawdown (mm, positive magnitude) at dist_m."""
    lam = _load_drawdown_lambda()
    d_eff = max(dist_m - SCRAPE_RISE_BUFFER_M, 0.0)
    return scrape_edge_head_mm * np.exp(-d_eff / lam)


# BW-mode scenario bar styling
_BW_SCENARIO_COLOURS = {
    "Scraping\n(observed)": "#bbbbbb",
    "Scraping\n(off-site 100 m)": "#dddddd",
    "Clearfell\n(hypothetical)": "#333333",
    "Thinning 50%\n(hypothetical)": "#666666",
    "Broadleaf\n(hypothetical)": "#999999",
    "Climate dry": "#444444",
    "Climate wet": "#cccccc",
}
_BW_SCENARIO_HATCHES = {
    "Scraping\n(observed)": "///",
    "Scraping\n(off-site 100 m)": "\\\\\\",
    "Clearfell\n(hypothetical)": "xxx",
    "Thinning 50%\n(hypothetical)": "///",
    "Broadleaf\n(hypothetical)": "...",
    "Climate dry": "\\\\\\",
    "Climate wet": "",
}


def _bar_style(name, colours, hatches):
    """Return (colour, hatch, edgecolor) respecting BW_MODE."""
    if BW_MODE:
        return (_BW_SCENARIO_COLOURS.get(name, "#999"),
                _BW_SCENARIO_HATCHES.get(name, ""),
                "black")
    return (colours.get(name, "#999"),
            hatches.get(name, ""),
            "black" if hatches.get(name) else colours.get(name, "#999"))


# ============================================================================
# DATA LOADING
# ============================================================================

def _load_ceh36_params():
    """Load CEH36's parameters from the shared cluster params loader."""
    # Get CEH36's cluster assignment
    master = pd.read_csv(INT_MASTER_DATA)
    master["match"] = master["Name_Original"].str.lower().str.replace(" ", "")
    row = master[master["match"] == WELL]
    if row.empty:
        raise ValueError(f"{WELL} not found in master data")
    row = row.iloc[0]
    cluster = int(row["Cluster"])

    # Get CEH36's own well-level Sy (more precise than cluster median).
    # 18_wtf_01_well_sy_estimates.csv is produced at step 22 and this script runs at step 9,
    # so on a first pass the file does not exist yet: read it if present, else
    # fall back to the documented default with a console warning, per the
    # first-pass convention used by 09b/09f. Previously this read was
    # unguarded and hard-failed the whole script on a cold run.
    from utils.pipeline_params import default_value
    if OUT_18_WELL_SY_TABLE.exists():
        sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
        sy_row = sy_df[sy_df["Well"].str.lower() == WELL]
        if sy_row.empty:
            well_sy = default_value("Sy")
            warn(f"{WELL} has no row in {OUT_18_WELL_SY_TABLE.name} - using the "
                 f"documented default Sy = {well_sy}")
        else:
            well_sy = float(sy_row["Sy_median"].iloc[0])
    else:
        well_sy = default_value("Sy")
        warn(f"{OUT_18_WELL_SY_TABLE.name} not present (produced at a later step) - "
             f"using the documented default Sy = {well_sy}; re-run after a full "
             "pipeline pass for the well-level value")

    # Get CEH36's own mean depth for h_disp.
    # No fallback: 01_wells_clean.csv is a step-1 output and this script runs at
    # step 9, so it always exists, and CEH36 is a permanently monitored well in
    # it. The former "else -0.7" was a rounded stand-in for a value that is
    # always available (-0.683) and could never be reached in a healthy run —
    # but had it ever fired it would have shifted h_disp by ~17 mm silently and
    # carried that into every scenario this script computes. A missing CEH36 is
    # a data-integrity failure, so say so, exactly as the master-data lookup
    # above already does.
    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells.columns = wells.columns.str.lower().str.replace(" ", "")
    if WELL not in wells.columns:
        raise ValueError(
            f"{WELL} not found in {INT_WELLS_CLEAN.name} - cannot compute its "
            "mean depth. This is a data-integrity failure, not a first-pass "
            "ordering problem: check Script 01's output.")
    mean_depth = float(wells[WELL].mean())

    params = {
        "b1": float(row["beta_1_recharge"]),
        "b2": float(row["beta_2_atmospheric_draw"]),
        "b3": float(row["beta_3_drainage"]),
        "Sy": well_sy,
        # 3.12.0 (D-332): from Model B's implied datum; it cancels in every bar
        "h_disp": float(row["implied_datum_m"]) + mean_depth,
        "cluster": cluster,
    }
    print(f"   CEH36: b1={params['b1']:.3f}  b2={params['b2']:.3f}  "
          f"b3={params['b3']:.4f}  Sy={params['Sy']:.3f}  "
          f"h_disp={params['h_disp']:.3f}m  cluster=C{params['cluster']}")
    return params


# ============================================================================
# MAIN
# ============================================================================

def main():
    make_all_dirs()
    plt.rcParams.update(MPL_DEFAULTS)

    banner("09d", "CEH36 SCENARIO COMPARISON", version=__version__)

    # ── 1. Load CEH36 parameters + both climate forcings ──────────────────
    phase(1, "Loading CEH36 parameters and climate forcings")
    params = _load_ceh36_params()
    annual_P, annual_PET = load_annual_climate()
    summer_P, summer_PET = load_summer_climate()
    print(f"   Annual-mean climate: P={annual_P:.6f}  PET={annual_PET:.6f} m/month")
    print(f"   Summer-mean climate: P={summer_P:.6f}  PET={summer_PET:.6f} m/month")

    # ── 2. Compute scenarios under each forcing ───────────────────────────
    phase(2, "Computing scenario responses at CEH36 (annual + summer forcing)")
    print("   Annual-mean forcing:")
    scen_annual = _compute_ceh36_scenarios(params, annual_P, annual_PET)
    print("   Summer forcing:")
    scen_summer = _compute_ceh36_scenarios(params, summer_P, summer_PET, summer=True)   # 4.0.0 (D-349 B2)

    # ── 3. Annual-forcing figure ──────────────────────────────────────────
    phase(3, "Plotting annual-mean forcing scenario comparison")
    _plot_scenarios(scen_annual, params, forcing="annual")

    # ── 4. Summer-forcing figure ──────────────────────────────────────────
    phase(4, "Plotting summer forcing scenario comparison")
    _plot_scenarios(scen_summer, params, forcing="summer")

    # ── 5. 3.14.0 (T-209): the clearfell match distance the annual caption quotes ──────────
    # 4.0.0 (D-349 B2, B3): every quantity on the sustained-level basis, and the clearfell over the anchor range.
    rr = ReportNumbers()
    _basis = ("sustained level x CEH36's Sy, both bars (D-349 B2: was a level against a one-month flux)")
    rr.add("scenario_clearfell_match_distance_m", scen_annual.get("_cf_match_m", float("nan")), unit="m",
           note="annual forcing: distance from the scrape at which the modelled off-site drawdown equals the "
                f"hypothetical clearfell bar in magnitude (09d_01 caption); {_basis}; anchor drift free")
    _scr = scen_annual["Scraping\n(observed)"]
    rr.add("scenario_ceh36_scraping_storage_mm", _scr, unit="mm", well="CEH36",
           note="annual forcing: the observed scraping BACI step x CEH36's Sy, mm w.e. (a sustained level)")
    for m in CLEARFELL_ANCHORS:
        tag = "" if m == "drift_free" else f"_anchor_{m}"
        cf = scen_annual["_cf_range"][m]
        why = f"anchor {m}: {CLEARFELL_ANCHOR_LABELS[m]}"
        rr.add(f"scenario_ceh36_clearfell_storage_mm{tag}", cf, unit="mm", well="CEH36",
               note=f"annual forcing: the hypothetical clearfell at CEH36, sustained change in storage (mm w.e.); {why}")
        rr.add(f"scenario_ceh36_scrape_to_clearfell_ratio{tag}",
               (_scr / cf) if (np.isfinite(cf) and cf != 0) else float("nan"), unit="-", well="CEH36",
               note=f"annual forcing: observed scraping storage / hypothetical clearfell storage, both sustained; {why}")
        if m != "drift_free":
            rr.add(f"scenario_clearfell_match_distance_m{tag}", scen_annual["_cf_match_range"][m], unit="m",
                   note=f"annual forcing: as scenario_clearfell_match_distance_m; {why}")
    rr.save(OUT_09D_REPORT_NUMBERS)
    step(f"{OUT_09D_REPORT_NUMBERS.name}")

    print("\nDone.")


# ============================================================================
# SCENARIO COMPUTATION — all at CEH36
# ============================================================================

def _compute_ceh36_scenarios(params, P_force, PET_force, summer=False):
    """Sustained change in stored water (mm w.e.) at CEH36 for each scenario under a given climate forcing
    (P_force, PET_force in m/month).

    4.0.0 (D-349 B2): EVERY bar is a sustained level change, as D-239 says, converted to stored water
    (x Sy x 1000). The scraping bars were already levels (the observed BACI step; the drain-cone drawdown). The
    clearfell, thinning, broadleaf and climate bars were the one-month change in the flux (a rate, "mm/month")
    set on the same axis; each is now carried to its sustained level by model_utils.sustained_monthly_response
    on CEH36's own beta_3: under annual-mean forcing the change is held in every month (so the level is the flux
    change / beta_3); under summer forcing (summer=True) it is applied in the summer months (SUMMER_MINIMUM_MONTHS)
    of every year and the bar is the periodic steady state's mean over those months.

    4.0.0 (D-349 B3): the clearfell (and thinning, f/2) bar is carried over the anchor range
    (clearfell_common.CLEARFELL_ANCHORS: drift free / drift fixed / drift-free DiD), stashed under
    "_cf_range" / "_thin_range"; the plotted bar is the drift-free headline.

    Called twice by main(): once with annual-mean climate (Figure 26) and once with summer-mean climate
    (Figure 27). CEH36 is in C3o (not forested), so the forestry scenarios show what would happen *if* CEH36's
    location had pine canopy and were then managed - a like-for-like comparison of intervention magnitudes at
    one hydrogeological setting.

    Returns dict {scenario_name: sustained change in storage, mm w.e.}.
    """
    b1, b2, b3 = params["b1"], params["b2"], params["b3"]
    h_disp = params["h_disp"]
    Sy = params["Sy"]

    # 3.14.0 (T-209, D-333): the clearfell returns a share f of the interception, calibrated on the observed
    # BACI step at the felled well (the flux sensitivity); thinning at most half. No beta_2 multiplier.
    # 4.0.0 (D-349): f over the anchor range; calibrated on WMC3's own fit (clearfell_common 1.18.0).
    f_range = clearfell_return_fraction_range(verbose=False)
    cf_frac = f_range["drift_free"]
    print("     clearfell interception-return fraction f (thinning f/2): "
          + "; ".join(f"{m} {v:.3f}" for m, v in f_range.items()))

    def _level_mm(dflux):
        """4.0.0 (D-349 B2): a one-month flux change (m/month) held in every month, carried to its sustained
        level on CEH36's beta_3 (the periodic steady state; = dflux / beta_3), as stored water in mm w.e."""
        f12 = np.array([float(dflux) if (not summer or m in SUMMER_MINIMUM_MONTHS) else 0.0 for m in range(1, 13)])
        ss = sustained_monthly_response(b3, f12)
        months = sorted(SUMMER_MINIMUM_MONTHS) if summer else list(range(1, 13))
        lvl = float(np.mean(ss[[m - 1 for m in months]]))
        return round(lvl * Sy * 1000, 1)

    # Baseline: CEH36 is unforested, so P_base = raw P
    P_base = P_force
    flux_base = b1 * P_base - b2 * PET_force - b3 * h_disp

    def _scenario_dh(P_eff_scen, b2_scen, PET_scen):
        flux_scen = b1 * P_eff_scen - b2_scen * PET_scen - b3 * h_disp
        return _level_mm(flux_scen - flux_base)

    scenarios = {}

    # Scraping: observed BACI step (a sustained level), converted to stored water
    scrape_baci_step = load_site_observation("ceh36_baci_pure_scraping")
    scenarios["Scraping\n(observed)"] = round(scrape_baci_step * Sy * 1000, 1)

    # Off-site (100 m) neighbour drawdown: the drain draws the surrounding
    # water table down. Modelled head drawdown (from the Script 20 drain
    # cone, anchored to the measured on-site response), then rendered on the
    # same volumetric axis (× Sy) as the on-site bar.
    onsite_edge_head_mm = scrape_baci_step * 1000
    offsite_head_mm = _offsite_scrape_head_mm(onsite_edge_head_mm)  # positive mag
    scenarios["Scraping\n(off-site 100 m)"] = round(
        -(offsite_head_mm / 1000) * Sy * 1000, 1)   # negative = drawdown

    # Far-distance (250 m) drawdown, stashed under a non-plotted key so the
    # plot can draw it as a reference line INSIDE the 100 m bar. Same drain
    # model, same volumetric conversion.
    far_head_mm = _offsite_scrape_head_mm(onsite_edge_head_mm, dist_m=OFFSITE_FAR_M)
    scenarios["_offsite_far_vol"] = round(-(far_head_mm / 1000) * Sy * 1000, 1)

    # Hypothetical: if CEH36 had pine and was clearfelled
    P_pine_base = P_force * (1 - FOREST_INTERCEPTION)
    flux_pine_base = b1 * P_pine_base - b2 * PET_force - b3 * h_disp

    def _cf_bar(frac):
        # Clearfell (3.14.0, T-209): a share f of the interception returned as recharge, the draw unchanged
        flux_cf = b1 * P_force * (1 - FOREST_INTERCEPTION * (1 - frac)) - b2 * PET_force - b3 * h_disp
        return _level_mm(flux_cf - flux_pine_base)
    scenarios["Clearfell\n(hypothetical)"] = _cf_bar(cf_frac)
    # Thinning 50%: at most half the clearfell's return
    scenarios["Thinning 50%\n(hypothetical)"] = _cf_bar(cf_frac / 2.0)
    scenarios["_cf_range"] = {m: (_cf_bar(v) if np.isfinite(v) else float("nan")) for m, v in f_range.items()}
    scenarios["_thin_range"] = {m: (_cf_bar(v / 2.0) if np.isfinite(v) else float("nan"))
                                for m, v in f_range.items()}

    # Broadleaf conversion — seasonal β₂ profile: deciduous canopy has
    # higher transpiration in summer (full leaf) than evergreen pine.
    flux_bl = b1 * P_pine_base - b2 * BROADLEAF_B2_SUMMER * PET_force - b3 * h_disp   # 3.11.0 (D-239)
    scenarios["Broadleaf\n(hypothetical)"] = _level_mm(flux_bl - flux_pine_base)

    # The distance at which the modelled off-site drawdown equals the clearfell bar in magnitude. 4.0.0 (D-349 B2):
    # both are sustained levels now (it was a level against a one-month flux: 504 m on the D-348 run), and the
    # distance is carried over the anchor range.
    _d = np.arange(OFFSITE_DIST_M, 2000.0, 1.0)
    _vol = np.array([_offsite_scrape_head_mm(onsite_edge_head_mm, dist_m=x) / 1000 * Sy * 1000 for x in _d])

    def _match(bar):
        bar = abs(bar)
        if not (np.isfinite(bar) and bar > 0):
            return float("nan")
        hit = _d[_vol <= bar]
        return float(hit[0]) if len(hit) else float("nan")
    scenarios["_cf_match_m"] = _match(scenarios["Clearfell\n(hypothetical)"])
    scenarios["_cf_match_range"] = {m: _match(v) for m, v in scenarios["_cf_range"].items()}

    # Climate scenarios — applied to CEH36's actual (unforested) state
    scenarios["Climate dry"] = _scenario_dh(
        P_force * UKCP18_DRY_P_SUMMER, b2, PET_force * UKCP18_DRY_PET_SUMMER)
    scenarios["Climate wet"] = _scenario_dh(
        P_force * UKCP18_WET_P_SUMMER, b2, PET_force * UKCP18_WET_PET_SUMMER)

    print("     scenario responses (sustained change in storage, mm w.e.):")
    for name, val in scenarios.items():
        if name.startswith("_"):
            continue
        print(f"       {name.replace(chr(10), ' '):30s}  {val:+.1f}")
    print("     clearfell over the anchor range: " + "; ".join(
        f"{m} {v:+.1f} mm (match {scenarios['_cf_match_range'][m]:.0f} m)" for m, v in scenarios["_cf_range"].items()))

    return scenarios



# ============================================================================
# FIGURE — VOLUMETRIC SCENARIO BAR CHART (annual or summer forcing)
# ============================================================================

_COLOURS = {
    "Scraping\n(observed)": "#DAA520",
    "Scraping\n(off-site 100 m)": "#E6B84D",
    "Clearfell\n(hypothetical)": "#8B4513",
    "Thinning 50%\n(hypothetical)": "#D2691E",
    "Broadleaf\n(hypothetical)": "#228B22",
    "Climate dry": "#FF6347",
    "Climate wet": "#4169E1",
}
_HATCHES = {"Scraping\n(observed)": "///"}


def _plot_scenarios(scenarios, params, forcing):
    """Volumetric scenario bar chart at CEH36 under a single climate forcing.

    forcing = "annual"  -> Figure 26 (annual-mean P and PET), output 09d_01
    forcing = "summer"  -> Figure 27 (summer Jun-Sep P and PET, SUMMER_MINIMUM_MONTHS), output 09d_02

    Both figures use ONE scale, the sustained change in stored water (mm water-equivalent;
    4.0.0, D-349 B2), so every bar on them is the same kind of quantity. Converting a bar to
    a water-table head change divides by CEH36's Sy again.
    """
    is_summer = (forcing == "summer")
    out_fig = OUT_09D_SUMMER_SCENARIO if is_summer else OUT_09D_SCENARIO
    out_csv = OUT_09D_SUMMER_SCENARIO_CSV if is_summer else OUT_09D_SCENARIO_CSV
    # 4.0.0 (D-349 B2): every bar is a sustained change in storage; the columns are renamed so no citation of the
    # old one-month flux values ("mm/month") keeps its meaning.
    col_name = ("Delta_storage_sustained_summer_mm" if is_summer
                else "Delta_storage_sustained_mm")

    # Pull the 250 m far-distance marker value out of the plotted set.
    far_vol = scenarios.get("_offsite_far_vol", None)
    plot_items = [(k, v) for k, v in scenarios.items() if not k.startswith("_")]
    names = [k for k, _ in plot_items]
    vals = [v for _, v in plot_items]
    display_names = list(names)
    offsite_idx = (names.index("Scraping\n(off-site 100 m)")
                   if "Scraping\n(off-site 100 m)" in names else None)

    fig, ax = plt.subplots(figsize=(12, 6.8), dpi=300)
    x = np.arange(len(names))

    for i, (name, val) in enumerate(zip(names, vals)):
        is_scrape = "Scraping" in name
        _col, _hatch, _ec = _bar_style(name, _COLOURS, _HATCHES)
        ax.bar(x[i], val, 0.65, color=_col, edgecolor=_ec,
               linewidth=1.5 if is_scrape else 0.5,
               hatch=_hatch, alpha=0.85, zorder=3)
        ax.text(x[i], val + (1.5 if val >= 0 else -1.5),
                f"{val:+.1f}",
                ha="center", va="bottom" if val >= 0 else "top",
                fontsize=11, fontweight="bold", color="#333")

    # 250 m reference line drawn ACROSS the 100 m off-site bar: shows the
    # milder, more-distant neighbour drawdown as a marker inside the near bar.
    if offsite_idx is not None and far_vol is not None:
        bar_half = 0.65 / 2
        ax.plot([x[offsite_idx] - bar_half, x[offsite_idx] + bar_half],
                [far_vol, far_vol],
                color="#7a4f00", lw=2.0, ls="-", zorder=5)
        ax.text(x[offsite_idx] + bar_half + 0.04, far_vol,
                f"250 m: {far_vol:+.1f}",
                ha="left", va="center", fontsize=8.5,
                fontweight="bold", color="#7a4f00")

    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(display_names, fontsize=10, ha="center")
    ax.set_ylabel("\u0394 stored water, sustained\n(mm water equiv.)",
                  fontsize=13)
    # 4.0.0 (D-349 B3): the clearfell and thinning bars carry the anchor range as a whisker
    for _nm, _rk in (("Clearfell\n(hypothetical)", "_cf_range"), ("Thinning 50%\n(hypothetical)", "_thin_range")):
        _rv = [v for v in scenarios.get(_rk, {}).values() if np.isfinite(v)]
        if _nm in names and len(_rv) > 1:
            ax.plot([x[names.index(_nm)]] * 2, [min(_rv), max(_rv)], color="black", lw=1.4, zorder=6)

    forcing_label = ("summer (Jun\u2013Sep) forcing" if is_summer
                     else "annual-mean forcing")
    ax.set_title(
        f"Scenario comparison at CEH36 (scraped site) \u2014 {forcing_label}\n"
        f"SSM coefficients: \u03b2\u2081={params['b1']:.2f}  "
        f"\u03b2\u2082={params['b2']:.2f}  "
        f"\u03b2\u2083={params['b3']:.3f}  "
        f"Sy={params['Sy']:.2f}",
        fontsize=13, fontweight="bold")

    ax.grid(axis="y", alpha=0.25, ls="--")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)

    # Shared caveat + forcing-specific note, placed BELOW the axis so it never
    # overlaps the bars (in particular the off-site drawdown bar).
    lam = _load_drawdown_lambda()
    caveat = (
        "Every bar is a SUSTAINED change in stored water (mm water-equiv.): the scraping bars are the observed "
        "step and the modelled drawdown; the others carry the forcing change to its sustained level on CEH36's "
        "\u03b2\u2083 (D-239), all \u00d7 CEH36's Sy.\n"
        "Scraping off-site: modelled neighbour drawdown from the drain cone "
        f"(\u03bb = {lam:.0f} m, live from Script 20); bar = "
        f"{OFFSITE_DIST_M:.0f} m, dark line across it = {OFFSITE_FAR_M:.0f} m "
        "(milder, more distant)."
    )
    if is_summer:
        caveat += (
            "\nSummer forcing = the change applied each summer (Jun\u2013Sep P and PET), carried to its "
            "periodic steady state and averaged over those months; NOT a summer minimum."
        )
    else:
        _m = scenarios.get("_cf_match_m", float("nan"))
        if np.isfinite(_m):
            caveat += (
                f"\nOff-site drawdown decays with distance; at ~{_m:.0f} m it equals the clearfell bar in magnitude.")
    caveat += ("\nClearfell: the share of the interception returned that reproduces the observed step at the felled "
               "well (its own fit); thinning at most half. Whisker: the anchor range \u2014 drift free / drift fixed / "
               "drift-free DiD; the central value depends on the drift model.")   # 3.14.0 (T-209); 4.0.0 (D-349 B3)
    ax.text(0.0, -0.16, caveat, transform=ax.transAxes, fontsize=8,
            ha="left", va="top", color="#555", style="italic")

    plt.tight_layout()
    fig.subplots_adjust(bottom=0.27)   # 3.13.0: room for the D-333 caveat line
    if is_summer:
        render_figure(fig, out_fig)
    else:
        render_figure(fig, out_fig, format="jpeg",
                      pil_kwargs={"quality": 85})
    plt.close(fig)
    step(f"{out_fig.name}")

    _rng = {"Clearfell\n(hypothetical)": scenarios.get("_cf_range", {}),
            "Thinning 50%\n(hypothetical)": scenarios.get("_thin_range", {})}
    rows = [{"Scenario": n.replace("\n", " "), col_name: v,
             **{f"anchor_{m}": _rng[n].get(m, np.nan) for m in CLEARFELL_ANCHORS if n in _rng}}
            for n, v in scenarios.items() if not n.startswith("_")]   # 4.0.0 (D-349 B3): the anchor range
    if far_vol is not None:
        rows.append({"Scenario": "Scraping (off-site 250 m)", col_name: far_vol})
    pd.DataFrame(rows).to_csv(out_csv, index=False, float_format="%.1f")
    step(f"{out_csv.name}")




# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
