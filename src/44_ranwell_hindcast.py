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
  the seasonal range say whether coefficients fitted 2005–26 reproduce the
  dynamics of fifty-four years earlier. The nearest paired well is the headline;
  every paired well is written (the spread is the sensitivity).

Q2 — Has the slack water table moved since 1951–53?  Ranwell's mean level (m OD)
  at each of the eight printed sites against the modern mean water-table
  surface interpolated to that point (IDW of per-well modern means; k, radius,
  power from config), minus the climate-only expectation for the two spans from
  the Q1 hindcast at the headline well. Four error terms in quadrature per site:
  leave-one-out RMSE of the IDW over the contributing wells; the surface
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
  accreting, and the modern surface is thinnest there.

What it does NOT establish: a point-to-point comparison (the wells are not
where the pipes were); coefficient stationarity (Script 39's caveat applies,
so a beta_1-scaling envelope is written); anything about the BS slack, for
which Ranwell printed no series; anything under the forest canopy, where no
Ranwell site lies.

Registered tier A, default, after Script 43 (it reads 43_01 and 43_07). Reads
three raw inputs no pipeline step produces (D-145 records the exception, as
D-051 did for Script 39); SKIPS cleanly when they are absent.

Inputs (via utils.paths):
    RANWELL_LEVELS, RANWELL_RANGES, RANWELL_PARC_MAWR_RAIN   (data/, digitised)
    OUT_43_SITES, OUT_43_WELL_BASINS, OUT_43_DIAGNOSTIC     (Script 43 v2)
    INT_CLIMATE, INT_MASTER_DATA, INT_WELLS_CLEAN, INT_LOCATIONS
    DATA_KML_COAST_2006, OUT_40_EPOCH_SERIES                  (coastal context)

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
    44_report_numbers.csv
"""

from __future__ import annotations

__version__ = "1.1.2"  # Hollingham (2026) — 2026-09-08. Report render: legend on the
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
from utils.model_utils import simulate_ssm  # noqa: E402
from utils.console_utils import banner, phase, step, info, warn, saved, note  # noqa: E402
from utils.render_utils import apply_house_style, render_figure  # noqa: E402

SCRIPT_ID = "44"
VERSION = __version__
DATUM = config.DRAINAGE_DATUM
BETA_COLS = ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage")
SPAN = pd.Period(config.RANWELL_HINDCAST_SPAN[0], "M"), pd.Period(config.RANWELL_HINDCAST_SPAN[1], "M")


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


# ── IDW with leave-one-out ────────────────────────────────────────────────────
def idw_at(ms: pd.DataFrame, e: float, n: float, exclude: str | None = None):
    d = np.hypot(ms["E"] - e, ms["N"] - n)
    sel = ms[(d <= config.RANWELL_IDW_RADIUS_M) & (ms.index != exclude)].copy()
    sel["d"] = d[sel.index]
    sel = sel.nsmallest(config.RANWELL_IDW_K, "d")
    if len(sel) < config.RANWELL_LOO_MIN_WELLS:
        return np.nan, sel
    w = 1.0 / np.maximum(sel["d"], config.RANWELL_IDW_MIN_DIST_M) ** config.RANWELL_IDW_POWER
    return float((sel["level_m_od"] * w).sum() / w.sum()), sel


def loo_rmse(ms: pd.DataFrame, contributing: pd.DataFrame) -> float:
    errs = []
    for w in contributing.index:
        v, _ = idw_at(ms, ms.loc[w, "E"], ms.loc[w, "N"], exclude=w)
        if np.isfinite(v):
            errs.append(ms.loc[w, "level_m_od"] - v)
    return float(np.sqrt(np.mean(np.square(errs)))) if errs else np.nan


def surface_gradient(ms: pd.DataFrame, e: float, n: float) -> float:
    h = config.RANWELL_GRAD_STEP_M
    vx1, _ = idw_at(ms, e + h, n)
    vx0, _ = idw_at(ms, e - h, n)
    vy1, _ = idw_at(ms, e, n + h)
    vy0, _ = idw_at(ms, e, n - h)
    return float(np.hypot((vx1 - vx0) / (2 * h), (vy1 - vy0) / (2 * h)))


# ── hindcast ──────────────────────────────────────────────────────────────────
def hindcast_series(cl, betas, h0, beta1_scale=1.0) -> pd.Series:
    b1, b2, b3 = betas
    h = simulate_ssm(h0, cl["P_m"].values, cl["PET"].values, b1 * beta1_scale, b2, b3,
                     drainage_datum=DATUM)
    return pd.Series(h, index=cl.index)


def compare(obs_month: pd.Series, model_mid: pd.Series, ground_m_od: float):
    """obs monthly means (m OD, PeriodIndex) vs modelled mid-month level (m OD,
    PeriodIndex) over their common months.

    Ranwell's pipe reads the free water surface, so a flooded slack reads at
    the ground: the observation is CENSORED at the surface. The offset is
    therefore fitted on the months that stand at least RANWELL_SURFACE_CENSOR_M
    below the ground, and the offset model is then capped at the ground before
    the metrics — the same instrument-matching cap the 2026-08-22 seasonal-range
    comparison applied to the modern network. Returns n, n censored, offset, r,
    NSE after offset (capped), ranges and the month of the 1951 minimum.
    """
    common = obs_month.index.intersection(model_mid.index)
    o = obs_month.loc[common].astype(float)
    p = model_mid.loc[common].astype(float)
    if len(common) < 3:
        return dict(n=len(common), n_at_surface=0, offset_m=np.nan, r=np.nan, nse_after_offset=np.nan,
                    range_obs_m=np.nan, range_model_m=np.nan, min_month_obs="", min_month_model="")
    free = o <= ground_m_od - config.RANWELL_SURFACE_CENSOR_M
    off = float((o[free] - p[free]).mean()) if free.sum() >= 3 else float((o - p).mean())
    pa = np.minimum(p + off, ground_m_od)
    nse = 1 - float(((o - pa) ** 2).sum() / ((o - o.mean()) ** 2).sum())
    r = float(np.corrcoef(o, pa)[0, 1])
    o51 = o[o.index.year == 1951]
    p51 = p[p.index.year == 1951]
    return dict(n=int(len(common)), n_at_surface=int((~free).sum()), offset_m=off, r=r,
                nse_after_offset=nse,
                range_obs_m=float(o.max() - o.min()), range_model_m=float(pa.max() - pa.min()),
                min_month_obs=str(o51.idxmin()) if len(o51) else "",
                min_month_model=str(p51.idxmin()) if len(p51) else "")


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
    """Ranwell's monthly means against the offset-removed, surface-capped hindcast.

    report=False — the Methods Supplement / diagnostic render: panel titles carry
      r, NSE-after-offset and the ranges, the legend carries the offset, a suptitle
      names the model.
    report=True — the report render: captions live in the document text (house
      rule), so no suptitle, panel titles name only the site, its slack and the
      paired well, and the legend names the series without values. Same data,
      same axes, same drawing code.
    """
    sites = sorted(series["site_no"].unique())
    fig, axes = plt.subplots(len(sites), 1, figsize=(10, 2.8 * len(sites)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, s in zip(axes, sites):
        sub = series[(series["site_no"] == s) & series["headline"]]
        m = metrics[(metrics["site_no"] == s) & metrics["headline"]].iloc[0]
        t = sub["month"].dt.to_timestamp()
        capped = np.minimum(sub["model_level_m_od"] + m["offset_m"], m["ground_m_od"])
        if report:
            ax.plot(t, sub["obs_level_m_od"], "o-", ms=4, color="#1B9E77",
                    label="Ranwell 1951–53, monthly mean of readings")
            ax.plot(t, capped, "-", color="#D95F02",
                    label="SSM hindcast, offset removed, capped at the ground surface")
            ax.set_title(f"Ranwell Site {s} ({SLACK_NAMES.get(m['sketch_slack'], m['sketch_slack'])}), "
                         f"paired with {m['well']}", fontsize=9, loc="left")
            ax.set_ylabel("Water-table level (m OD)", fontsize=9)
        else:
            ax.plot(t, sub["obs_level_m_od"], "o-", ms=4, color="#1B9E77", label="Ranwell (monthly mean of readings)")
            ax.plot(t, capped, "-", color="#D95F02",
                    label=f"SSM hindcast at {m['well']} ({m['offset_m']:+.2f} m offset, capped at the surface)")
            ax.set_title(f"Site {s} ({m['sketch_slack']}): r {m['r']:.2f}, NSE after offset "
                         f"{m['nse_after_offset']:.2f}, range obs {m['range_obs_m']:.2f} vs model "
                         f"{m['range_model_m']:.2f} m", fontsize=9, loc="left")
            ax.set_ylabel("level (m OD)", fontsize=9)
        ax.axhline(m["ground_m_od"], color="grey", lw=0.7, ls=":")
        ax.grid(alpha=0.3)
        if not report or ax is axes[0]:
            # one legend in the report render: on the lower panels it covers the 1951 minimum
            ax.legend(fontsize=8, loc="lower left", framealpha=0.9)
    if not report:
        fig.suptitle("Ranwell's 1951–53 series against the SSM driven by RAF Valley climate "
                     "(coefficients fitted 2005–26)", fontsize=10)
    fig.tight_layout()
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
    ax.set_title("Slack water table, 2005–26 against 1951–53, climate-corrected", fontsize=10, loc="left")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, framealpha=0.9)
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
    datum_mad = float(diag["datum_offset_mad_m"])
    info(f"{len(lv)} Fig. 4 readings at sites {sorted(int(x) for x in lv['site_no'].unique())}; "
         f"{len(rg)} Fig. 7 ranges at sites {sorted(int(x) for x in rg['site_no'].unique())}")
    info(f"modern surface: {len(ms)} wells with >= {config.RANWELL_MIN_MODERN_N} readings; "
         f"climate from {cl.index.min():%Y-%m}; datum-offset MAD {datum_mad:.3f} m (Script 43)")

    phase(2, "Q1 — hindcast at the same-basin wells")
    lv["month"] = lv["date"].dt.to_period("M")
    obs_month = lv.groupby(["site_no", "month"])["level_m_od"].mean()
    series_rows, metric_rows, climate_exp = [], [], {}
    for s in sorted(lv["site_no"].unique()):
        srow = sites.loc[s]
        d = np.hypot(ms["E"] - srow["easting"], ms["N"] - srow["northing"])
        cand = ms[(ms["basin_id"] == srow["basin_id"]) & (d <= config.RANWELL_PAIR_MAX_M)].copy()
        cand["d"] = d[cand.index]
        cand = cand[[w in md.index and all(np.isfinite(md.loc[w, c]) for c in BETA_COLS)
                     and md.loc[w, BETA_COLS[2]] > 0 for w in cand.index]]
        if cand.empty:
            warn(f"site {s}: no same-basin well with committed coefficients within "
                 f"{config.RANWELL_PAIR_MAX_M:.0f} m")
            continue
        cand = cand.sort_values("d")
        om = obs_month.loc[s]
        for rank, (w, c) in enumerate(cand.iterrows()):
            betas = tuple(float(md.loc[w, k]) for k in BETA_COLS)
            h0 = float(c["level_m_od"] - c["ground_m"])
            h = hindcast_series(cl, betas, h0)
            mid = ((h + h.shift(1)) / 2 + c["ground_m"])
            mid.index = mid.index.to_period("M")
            met = compare(om, mid, float(srow["height_m_od"]))
            env = {}
            for sc in config.CCW_BETA1_SCALINGS:
                hs = hindcast_series(cl, betas, h0, sc)
                ms_ = ((hs + hs.shift(1)) / 2 + c["ground_m"])
                ms_.index = ms_.index.to_period("M")
                env[f"nse_after_offset_b1x{sc:.2f}"] = compare(om, ms_, float(srow["height_m_od"]))["nse_after_offset"]
            # climate-only expectation: modelled 1951-53 mean minus modelled modern-span mean
            hp = h.copy()
            hp.index = hp.index.to_period("M")
            exp = float(hp.loc[SPAN[0]:SPAN[1]].mean() - hp.loc[c["first"].to_period("M"):c["last"].to_period("M")].mean())
            headline = rank == 0
            if headline:
                climate_exp[s] = exp
            metric_rows.append(dict(site_no=int(s), sketch_slack=srow["sketch_slack"], well=w,
                                    ground_m_od=float(srow["height_m_od"]),
                                    dist_m=float(c["d"]), headline=headline,
                                    beta_1=betas[0], beta_2=betas[1], beta_3=betas[2],
                                    **met, climate_expectation_m=exp, **env))
            common = om.index.intersection(mid.index)
            for mth in common:
                series_rows.append(dict(site_no=s, well=w, headline=headline, month=mth,
                                        obs_level_m_od=float(om.loc[mth]),
                                        model_level_m_od=float(mid.loc[mth]),
                                        n_readings=int(lv[(lv["site_no"] == s) & (lv["month"] == mth)].shape[0])))
        hl = [m for m in metric_rows if m["site_no"] == s and m["headline"]][0]
        step(f"site {s} ({srow['sketch_slack']}): {len(cand)} paired well(s); headline {hl['well']} "
             f"({hl['dist_m']:.0f} m): r {hl['r']:.2f}, NSE after offset {hl['nse_after_offset']:.2f}, "
             f"range obs {hl['range_obs_m']:.2f} vs model {hl['range_model_m']:.2f} m, "
             f"n {hl['n']} ({hl['n_at_surface']} at the surface); climate-only expectation {hl['climate_expectation_m']:+.3f} m")
    metrics = pd.DataFrame(metric_rows)
    series = pd.DataFrame(series_rows)

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
    lc_rows = []
    for s in sorted(set(read_mean.index) | set(mid_mean.index)):
        srow = sites.loc[s]
        if s in read_mean.index:
            rmean, basis, n_r = float(read_mean[s]), "fig4_readings", int(read_n[s])
        else:
            rmean, basis, n_r = float(mid_mean[s]), "fig7_midrange", int((rg["site_no"] == s).sum())
        v_m, sel = idw_at(ms, srow["easting"], srow["northing"])
        v_r, _ = idw_at(ms, srow["refined_easting"], srow["refined_northing"])
        if not np.isfinite(v_m):
            warn(f"site {s}: fewer than {config.RANWELL_LOO_MIN_WELLS} wells within "
                 f"{config.RANWELL_IDW_RADIUS_M:.0f} m; no modern surface")
            continue
        loo = loo_rmse(ms, sel)
        grad = surface_gradient(ms, srow["easting"], srow["northing"])
        pos_sigma = (float(srow["refined_move_m"]) if srow["resolvability"] == "flank"
                     else config.RANWELL_POS_SIGMA_M)
        sig_pos = grad * pos_sigma
        sig_samp = config.RANWELL_SAMPLING_SIGMA_M
        sig_dat = datum_mad
        sig = float(np.sqrt(loo ** 2 + sig_pos ** 2 + sig_samp ** 2 + sig_dat ** 2))
        # climate-only expectation: from the headline hindcast where the site has one,
        # else from the nearest contributing well that has coefficients
        if s in climate_exp:
            exp, exp_src = climate_exp[s], "headline_hindcast"
        else:
            exp, exp_src = np.nan, ""
            for w in sel.index:
                if w in md.index and md.loc[w, BETA_COLS[2]] > 0:
                    betas = tuple(float(md.loc[w, k]) for k in BETA_COLS)
                    h = hindcast_series(cl, betas, float(ms.loc[w, "level_m_od"] - ms.loc[w, "ground_m"]))
                    hp = h.copy()
                    hp.index = hp.index.to_period("M")
                    exp = float(hp.loc[SPAN[0]:SPAN[1]].mean()
                                - hp.loc[ms.loc[w, "first"].to_period("M"):ms.loc[w, "last"].to_period("M")].mean())
                    exp_src = f"hindcast_at_{w}"
                    break
        delta = (v_m - rmean) - (exp if np.isfinite(exp) else 0.0)
        dcoast = coast_distance(srow["easting"], srow["northing"])
        constrained = bool(np.isfinite(loo) and loo <= config.RANWELL_LOO_MAX_M)
        lc_rows.append(dict(
            row="site", site_no=s, sketch_slack=srow["sketch_slack"], ranwell_basis=basis,
            ranwell_n=n_r, ranwell_mean_m_od=rmean,
            modern_idw_m_od=v_m, modern_idw_refined_m_od=v_r,
            contributing_wells="; ".join(f"{w} ({r.d:.0f} m, {r.level_m_od:.2f})" for w, r in sel.iterrows()),
            n_contributing=len(sel), nearest_well_m=float(sel["d"].min()),
            contributing_min_m_od=float(sel["level_m_od"].min()), contributing_max_m_od=float(sel["level_m_od"].max()),
            sigma_loo_m=loo, surface_gradient=grad, position_sigma_m=pos_sigma, sigma_position_m=sig_pos,
            sigma_sampling_m=sig_samp, sigma_datum_m=sig_dat, sigma_total_m=sig,
            climate_expectation_m=exp, climate_expectation_source=exp_src,
            delta_m=delta, z=delta / sig if sig > 0 else np.nan, resolved=bool(abs(delta) > 2 * sig),
            interval_years=dt_years, rate_mm_per_year=delta / dt_years * 1000,
            dist_coast_2006_m=dcoast, shoreline_retreat_1899_2026_m=retreat_1899_2026,
            surface_constrained=constrained))
        step(f"site {s} ({srow['sketch_slack']}, {basis}): Ranwell {rmean:.2f} m OD, modern {v_m:.2f} "
             f"(LOO {loo:.2f}, pos {sig_pos:.2f}, datum {sig_dat:.2f}) -> Δ {delta:+.2f} ± {sig:.2f} m"
             + ("" if constrained else f" [modern surface unconstrained: LOO > {config.RANWELL_LOO_MAX_M} m]"))
    lc = pd.DataFrame(lc_rows)

    def _combine(df, label):
        if df.empty:
            return None
        w = 1.0 / df["sigma_total_m"] ** 2
        mean = float((df["delta_m"] * w).sum() / w.sum())
        se = float(np.sqrt(1.0 / w.sum()))
        dof = max(len(df) - 1, 1)
        chi2 = float((((df["delta_m"] - mean) / df["sigma_total_m"]) ** 2).sum() / dof)
        return dict(row=label, site_no=np.nan, sketch_slack="", ranwell_basis="", ranwell_n=int(df["ranwell_n"].sum()),
                    n_contributing=len(df), delta_m=mean, sigma_total_m=se, z=mean / se,
                    resolved=bool(abs(mean) > 2 * se), chi2_per_dof=chi2,
                    interval_years=dt_years, rate_mm_per_year=mean / dt_years * 1000,
                    sites="; ".join(str(int(s)) for s in df["site_no"]))

    comb_all = _combine(lc, "COMBINED_ALL")
    comb_in = _combine(lc[lc["surface_constrained"]], "COMBINED_CONSTRAINED")
    for c in (comb_all, comb_in):
        if c:
            lc = pd.concat([lc, pd.DataFrame([c])], ignore_index=True)
            step(f"{c['row']}: Δ {c['delta_m']:+.3f} ± {c['sigma_total_m']:.3f} m over {c['n_contributing']} sites "
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

    phase(5, "Outputs")
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

    hlm = metrics[metrics["headline"]]
    rn = [
        ("ranwell_hindcast_sites", len(hlm), "count", "Ranwell sites with a printed series and a same-basin paired well"),
        ("ranwell_hindcast_r_median", float(hlm["r"].median()) if len(hlm) else np.nan, "-", "median r, headline pairing, offset removed"),
        ("ranwell_hindcast_r_min", float(hlm["r"].min()) if len(hlm) else np.nan, "-", "lowest r among the headline pairings"),
        ("ranwell_hindcast_nse_median", float(hlm["nse_after_offset"].median()) if len(hlm) else np.nan, "-", "median NSE after offset, headline pairing"),
        ("ranwell_sites_compared", int((lc["row"] == "site").sum()), "count", "sites with a Ranwell mean and a modern surface"),
        ("ranwell_interval_years", dt_years, "y", "modern record midpoint minus 1952"),
        ("ranwell_shoreline_retreat_1899_2026_m", retreat_1899_2026, "m", "Script 40 median shoreline retreat 1899-2026, context for the seaward sites"),
        ("ranwell_sites_surface_constrained", int(lc.loc[lc["row"] == "site", "surface_constrained"].sum()), "count",
         f"sites whose modern-surface leave-one-out error is <= {config.RANWELL_LOO_MAX_M} m"),
        ("ranwell_forcing_ratio_1951_53", ratio_span, "-", "Parc Mawr / RAF Valley rainfall over Ranwell's span"),
        ("ranwell_forcing_r_1951_53", r_span, "-", "monthly correlation of the two gauges over Ranwell's span"),
    ]
    for r in lc[lc["row"] == "site"].itertuples():
        rn.append((f"ranwell_delta_m_site{int(r.site_no)}", r.delta_m, "m", f"site {int(r.site_no)} ({r.sketch_slack}): modern minus 1951-53, climate-corrected"))
        rn.append((f"ranwell_sigma_m_site{int(r.site_no)}", r.sigma_total_m, "m", f"site {int(r.site_no)}: four-term error"))
    for c in (comb_all, comb_in):
        if c:
            k = c["row"].lower()
            rn += [(f"ranwell_delta_m_{k}", c["delta_m"], "m", f"{c['row']}: inverse-variance mean over {c['n_contributing']} sites"),
                   (f"ranwell_sigma_m_{k}", c["sigma_total_m"], "m", f"{c['row']}: standard error"),
                   (f"ranwell_chi2_dof_{k}", c["chi2_per_dof"], "-", f"{c['row']}: chi-square per degree of freedom"),
                   (f"ranwell_rate_mm_yr_{k}", c["rate_mm_per_year"], "mm/yr", f"{c['row']}: delta over the interval"),
                   (f"ranwell_resolved_{k}", int(c["resolved"]), "flag", f"{c['row']}: |delta| > 2 sigma")]
    pd.DataFrame(rn, columns=["key", "value", "unit", "note"]).to_csv(paths.OUT_44_REPORT_NUMBERS, index=False)
    saved(paths.OUT_44_REPORT_NUMBERS.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
