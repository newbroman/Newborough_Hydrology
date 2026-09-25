#!/usr/bin/env python3
"""
45_wet_area_model.py — the Sentinel-2 wet-area model: the two curves and the SSM
drive, fitted from the committed scene series (T-40, D-178)
==========================================================================

WHAT THIS IS

  The fit at the head of the wet-area line. Two Sentinel-2 NIR classes — open
  water (B8 <= 0.50 x the scene's clear-floor median) and wet floor (0.50-0.80) —
  are fitted a*exp(b*h) against the median dipwell level at each winter scene's
  date, no vet in the fit (D-178). The same curves are then run through phase 27's
  monthly SSM level so the model can be read against the record it is asked to
  hindcast.

  This step FITS: it estimates the four curve parameters (a, b and a log-space
  sigma) per class from the scene series. It reads nothing from a scene and needs
  no network — the series is the 43-row committed distillate of the scenes, which
  a re-runner regenerates from Copernicus via tools/sentinel_wet_floor.py
  --two-class. Step 46 turns these curves, the per-cell thresholds and the SSM
  drive into the public feed the forecaster and the film read.

INPUTS — all committed
  data/sentinel/two_class_series.csv .. per winter scene: h_scene and the class
                                        areas (open_water_ha, wet_floor_ha,
                                        dark_total_ha). The fit's whole input.
  data/sentinel/hindcast_monthly.csv .. phase 27's monthly SSM level (Modes R/C),
                                        modelled and observed; the SSM drive.

OUTPUTS — outputs/45_wet_area/
  45_01_wet_area_model.csv ............ the model: a, b, sigma_log, sigma_factor,
                                        rho, n, h_min, h_max, one row per class.
  45_01_wet_area_model.png ............ the fit figure.
  45_02_ssm_through_nir_curves.csv .... the two curves on phase 27's monthly
                                        level, modelled and observed; Step 46's
                                        history block reads this.
  45_02_ssm_through_nir_curves.png .... the SSM-through-curves figure.
  45_03_switching_levels_map.png ...... the per-cell switching levels from
                                        cell_thresholds.npz, two panels (wet floor,
                                        open water): the network-median level at
                                        which each floor cell first reads the class,
                                        never-wet floor in grey, site boundary and
                                        the reference wells overlaid (T-77).
  45_04_phase_hysteresis.csv .......... the wetting-versus-drying phase term and the
                                        scene-month rain term, one row per class:
                                        log(area) on h_scene alone, plus dh_month,
                                        plus the scene month's rainfall (T-77).
  45_report_numbers.csv ............... floor_mask_area_ha / _cells, wet_floor_ever_* and
                                        open_water_ever_*, fit_<class>_rho / _r2_log /
                                        _n_scenes, oos_<mode>_<class>_r2 / _n_months /
                                        _median_ratio / _ratio_p16 / _ratio_p84 (E16);
                                        hysteresis_ratio_<class>, hysteresis_dh_p_<class>
                                        and rain_term_p_<class> (T-77).

USAGE
  python3 run_analysis.py                     # runs under --full
  python3 src/45_wet_area_model.py            # standalone
  python3 src/45_wet_area_model.py --no-fig   # the CSVs only, no figures
"""
from __future__ import annotations

__version__ = "1.5.0"  # Hollingham (2026) - 2026-09-25. Figures 45_01 and 45_02 each
#   gain a sidecar, 45_01_wet_area_model_axes.json / 45_02_ssm_through_nir_curves_axes.json:
#   every axes' box as a fraction of the saved image plus its limits. The hindcast film
#   (Script 47 1.2.0) uses them to draw callouts from its satellite thumbnails onto the
#   report figures' own dots and dates. And 45_03 (report Figure 51) now draws its two
#   panels one above the other, labelled (a) and (b) as the caption reads them, with
#   the colour bar beneath (Martin: "the plots should be stacked", then "the report
#   figure should be stacked too"). No CSV or number changes.
# v1.4.0  # Hollingham (2026) - 2026-09-23 (T-77). Two new artefacts and
#   a new Phase 4 between the SSM drive and the report numbers. 45_03: the per-cell
#   switching levels in cell_thresholds.npz drawn as two map panels (wet floor, open
#   water) — the network-median level at which a floor cell first reads the class,
#   never-wet floor in grey, non-floor transparent, the site boundary (kml_io) and
#   the reference wells overlaid, E/N axes from map_utils. 45_04: the phase term —
#   per class, log(area) on h_scene alone (M0), with dh_month (M1) and with the
#   scene month's rainfall (M2; the calendar month containing the scene date, with
#   the field-convention month_bucket variant beside it), the wetting-versus-drying
#   ratio from M0's residuals, and n. Three report numbers per class join
#   45_report_numbers.csv (hysteresis_ratio_, hysteresis_dh_p_, rain_term_p_).
#   Existing outputs unchanged.
# 1.3.0  Hollingham (2026) - 2026-09-21. The slack-floor mask area is
#   emitted as floor_mask_area_ha / floor_mask_cells, not study_area_ha / _cells:
#   Script 12 emits study_area_ha for the 845.6 ha hydrological study area, and
#   build_number_ledger --check (gated today) rightly read the same key carrying
#   306.97 and 845.6 as a collision. Two quantities, two names. Values unchanged.
# 1.2.0  Hollingham (2026) - 2026-09-20 (E16). 45_report_numbers.csv:
#   every number the abstract and report9 §4.8.5 quote from this analysis had been
#   computed here and written into FIGURE LABELS only — the log-space fit R^2 per
#   class, the SSM-vs-observed R^2, n and median modelled:observed ratio per mode
#   and class — while the study area (306.97 ha, 30,697 floor cells), the cells
#   ever wet and ever open water were read off cell_thresholds.npz by hand and
#   typed. All of it is now a ReportNumbers table; the figure code reads the same
#   helpers. The model CSV, the curves CSV and the figures are unchanged.
# v1.1.0  Hollingham (2026) - 2026-09-17. Figures carry R^2: the
#   log-linear fit R^2 per class on 45_01, and the SSM-vs-observed area R^2 for
#   open water and wet floor in each mode (R, C) on 45_02, with observed open
#   water overlaid. Figure annotations only — the model CSV and the feed are
#   unchanged (R^2 is recomputed at render, not stored), so no re-emit is needed.
# v1.0.0  Hollingham (2026) - 2026-09-17. First cut: T-40, promoting
#   the Sentinel wet-area line into the pipeline. The fit (Phase 2) and the SSM
#   drive (Phase 4) of tools/sentinel_wet_floor.py --two-class, moved here
#   unchanged in substance and re-pointed at the committed data/sentinel/ inputs.
#   _fit_exp is the tool's log-linear fit verbatim; the model CSV and the
#   ssm-through-curves CSV carry the same columns and rounding, so the feed Step 46
#   builds from them is byte-identical to the tool's but for its `source` field.

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.paths import (                                     # noqa: E402
    DIR_45, OUT_45_MODEL, OUT_45_MODEL_FIG, OUT_45_SSM_CURVES, OUT_45_SSM_CURVES_FIG,
    OUT_45_MODEL_AXES, OUT_45_SSM_CURVES_AXES,
    OUT_45_REPORT_NUMBERS, OUT_45_SWITCHING_LEVELS_MAP, OUT_45_PHASE_HYSTERESIS,
    SENTINEL_TWO_CLASS_SERIES, SENTINEL_HINDCAST_MONTHLY, SENTINEL_CELL_THRESHOLDS,
    INT_CLIMATE, INT_LOCATIONS, INT_MASTER_DATA, DATA_KML_SITE_BOUNDARY,
)
from utils.config import WET_AREA_CLASSES, WET_AREA_GRID, CELL_MIN_SCENES   # noqa: E402
from utils.buckets import month_bucket                        # noqa: E402
from utils.data_utils import normalize_well_name              # noqa: E402
from utils.report_numbers_utils import ReportNumbers          # noqa: E402
from utils.console_utils import banner, done, info, phase, result, saved, step, warn  # noqa: E402

# The two classes the curves, the maps and the phase term are reported for;
# WET_AREA_CLASSES also carries dark_total, which is their sum.
CURVE_CLASSES = ("open_water", "wet_floor")


# ─────────────────────────────────────────────────────────────────────────────
# THE FIT
# ─────────────────────────────────────────────────────────────────────────────
def _fit_exp(y, h):
    """log-linear fit y = a*exp(b*h); returns a, b, sigma (log), Spearman rho.

    Verbatim from tools/sentinel_wet_floor.py: the clip at 0.3 ha keeps log() finite
    where a dry scene reads a hectare or less, and rho is done by ranks so the step
    runs on a host with no scipy.
    """
    ly = np.log(np.clip(y, 0.3, None))
    b, la = np.polyfit(h, ly, 1)
    sd = float((ly - (la + b * h)).std())
    rho = float(pd.Series(y).rank().corr(pd.Series(h).rank()))
    return float(np.exp(la)), float(b), sd, rho


def fit_r2_log(R: pd.DataFrame, f: dict, cls: str) -> float:
    """R^2 of the log-linear fit, in the space the curve is fitted in: the fraction
    of the scatter in ln(area) the exponential explains. Figure 45_01's label."""
    ly = np.log(np.clip(R[f"{cls}_ha"].values, 0.3, None))
    pred = np.log(f["a"]) + f["b"] * R["h_scene"].values
    ss_tot = float(((ly - ly.mean()) ** 2).sum())
    return 1.0 - float(((ly - pred) ** 2).sum()) / ss_tot if ss_tot else float("nan")


def r2_pearson(mod, obs) -> tuple[float, int]:
    """R^2 = squared Pearson correlation of the SSM-modelled area against the area
    the OBSERVED level gives, over the months carrying an observed level. Figure
    45_02's label, and the out-of-sample statistic the report quotes."""
    mod = np.asarray(mod, float); obs = np.asarray(obs, float)
    ok = np.isfinite(mod) & np.isfinite(obs)
    if ok.sum() < 2:
        return float("nan"), int(ok.sum())
    r = np.corrcoef(mod[ok], obs[ok])[0, 1]
    return float(r * r), int(ok.sum())


def load_series() -> pd.DataFrame:
    """The committed scene series — one row per winter scene that fed the D-178 fit."""
    if not SENTINEL_TWO_CLASS_SERIES.exists():
        raise SystemExit(f"no {SENTINEL_TWO_CLASS_SERIES} — regenerate it with "
                         f"tools/sentinel_wet_floor.py --two-class (needs the scenes)")
    R = pd.read_csv(SENTINEL_TWO_CLASS_SERIES, float_precision="round_trip")
    step(f"{len(R)} winter scene(s), median well level {R['h_scene'].min():+.2f} "
         f"to {R['h_scene'].max():+.2f} m")
    return R


def fit_curves(R: pd.DataFrame) -> dict:
    """Fit a*exp(b*h) for each class against the scene-date median well level."""
    fits = {}
    for cls in WET_AREA_CLASSES:
        a, b, sd, rho = _fit_exp(R[f"{cls}_ha"].values, R["h_scene"].values)
        fits[cls] = dict(cls=cls, a=a, b=b, sigma_log=sd, sigma_factor=float(np.exp(sd)),
                         rho=rho, n=len(R), h_min=float(R["h_scene"].min()),
                         h_max=float(R["h_scene"].max()))
        step(f"{cls}: {a:.1f} * exp({b:.2f} h) ha; sigma x/÷ {np.exp(sd):.2f}; "
             f"rho {rho:+.2f}; n {len(R)}")
    return fits


def write_model(fits: dict) -> None:
    pd.DataFrame(fits.values()).to_csv(OUT_45_MODEL, index=False)
    saved(OUT_45_MODEL.name)


def _write_axes(fig, axes, path) -> None:
    """The saved figure's axes geometry, for callouts drawn onto the PNG downstream.

    Positions are fractions of the figure, y measured from the BOTTOM (matplotlib's
    convention); the figure is saved without bbox_inches, so they are fractions of the
    PNG too. A date axis carries its limits as ISO dates as well as matplotlib numbers.
    """
    import json                                                # noqa: PLC0415
    import matplotlib.dates as mdates                          # noqa: PLC0415
    out = []
    for ax in axes:
        b = ax.get_position()
        x0, x1 = ax.get_xlim()
        is_date = isinstance(ax.xaxis.get_major_formatter(),
                             (mdates.AutoDateFormatter, mdates.ConciseDateFormatter,
                              mdates.DateFormatter))
        row = dict(box=[b.x0, b.y0, b.x1, b.y1], xlim=[x0, x1], ylim=list(ax.get_ylim()),
                   x_is_date=is_date, yscale=ax.get_yscale(), xscale=ax.get_xscale())
        if is_date:
            row["xlim_iso"] = [mdates.num2date(x0).strftime("%Y-%m-%d"),
                               mdates.num2date(x1).strftime("%Y-%m-%d")]
        out.append(row)
    path.write_text(json.dumps(dict(image=path.name.replace("_axes.json", ".png"),
                                    axes=out), indent=1), encoding="utf-8")
    saved(path.name)


def plot_model(R: pd.DataFrame, fits: dict) -> None:
    import matplotlib                                          # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                            # noqa: PLC0415
    hh = np.linspace(R["h_scene"].min() - 0.05, R["h_scene"].max() + 0.1, 60)
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for cls, c, lab in (("open_water", "#0b6e8f", "open water (B8 <= 0.5 x median)"),
                        ("wet_floor", "#d4a017", "wet floor (0.5-0.8)")):
        f = fits[cls]
        r2 = fit_r2_log(R, f, cls)
        ax.scatter(R["h_scene"], R[f"{cls}_ha"], s=24, color=c, alpha=0.85)
        ax.fill_between(hh, f["a"] * np.exp(f["b"] * hh - f["sigma_log"]),
                        f["a"] * np.exp(f["b"] * hh + f["sigma_log"]), color=c, alpha=0.12)
        ax.plot(hh, f["a"] * np.exp(f["b"] * hh), color=c, lw=2,
                label=f"{lab}: {f['a']:.0f}·exp({f['b']:.2f}·h) ha, rho {f['rho']:+.2f}, R² {r2:.2f}")
    ax.set_xlabel("median well level at the scene date, m (0 = ground)")
    ax.set_ylabel("area, ha (whole warren)")
    ax.set_title(f"The wet-area model — {fits['open_water']['n']} winter Sentinel-2 scenes, "
                 f"B8 alone, no vet (D-178)", fontsize=9.5)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT_45_MODEL_FIG, dpi=160)
    _write_axes(fig, [ax], OUT_45_MODEL_AXES)
    plt.close(fig)
    saved(OUT_45_MODEL_FIG.name)


# ─────────────────────────────────────────────────────────────────────────────
# THE SSM DRIVE — the curves on phase 27's monthly level
# ─────────────────────────────────────────────────────────────────────────────
def ssm_through_curves(fits: dict, make_fig: bool) -> dict:
    """Run the two curves through phase 27's monthly SSM level, modelled and
    observed. Downstream of the fit — the curves change, this tracks them — so it
    lives here rather than being a committed input. Optional: no hindcast_monthly,
    no ssm_curves, and Step 46's history block is simply omitted."""
    if not SENTINEL_HINDCAST_MONTHLY.exists():
        warn(f"no {SENTINEL_HINDCAST_MONTHLY.name}: the SSM drive needs phase 27's "
             f"levels; ssm_through_nir_curves not written and the feed will carry no history")
        return {}
    Hc = pd.read_csv(SENTINEL_HINDCAST_MONTHLY, float_precision="round_trip")
    for cls in ("open_water", "wet_floor"):
        f = fits[cls]
        Hc[f"{cls}_ha_modelled"] = f["a"] * np.exp(f["b"] * Hc["median_level_modelled_m"])
        Hc[f"{cls}_ha_observed"] = np.where(
            Hc["median_level_observed_m"].notna(),
            f["a"] * np.exp(f["b"] * Hc["median_level_observed_m"]), np.nan)
    keep = ["month", "mode", "median_level_modelled_m", "median_level_observed_m",
            "n_wells_observed", "open_water_ha_modelled", "wet_floor_ha_modelled",
            "open_water_ha_observed", "wet_floor_ha_observed", "sentinel_index"]
    Hc[keep].round(3).to_csv(OUT_45_SSM_CURVES, index=False)
    saved(OUT_45_SSM_CURVES.name)
    oos = {}
    for m, g in Hc.groupby("mode"):
        ok = g["median_level_observed_m"].notna() & (g["n_wells_observed"] >= 20)
        if not ok.any():
            continue
        for cls in ("open_water", "wet_floor"):
            e = np.log(g.loc[ok, f"{cls}_ha_modelled"]) - np.log(g.loc[ok, f"{cls}_ha_observed"])
            r2, n = r2_pearson(g.loc[ok, f"{cls}_ha_modelled"], g.loc[ok, f"{cls}_ha_observed"])
            oos[(m, cls)] = dict(r2=r2, n=n, median_ratio=float(np.exp(np.median(e))),
                                 ratio_p16=float(np.exp(np.percentile(e, 16))),
                                 ratio_p84=float(np.exp(np.percentile(e, 84))))
            step(f"Mode {m} {cls}: R² {r2:.2f}, median x{np.exp(np.median(e)):.2f}, 68 % range "
                 f"x{np.exp(np.percentile(e, 16)):.2f}-{np.exp(np.percentile(e, 84)):.2f} "
                 f"over {int(ok.sum())} months")
    if make_fig:
        _plot_ssm(Hc)
    return oos


def _plot_ssm(Hc: pd.DataFrame) -> None:
    import matplotlib                                          # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                            # noqa: PLC0415
    t = pd.to_datetime(Hc["month"])
    _r2 = r2_pearson

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for ax, m in zip(axes, ("R", "C")):
        g = Hc[Hc["mode"] == m]
        tt = t[g.index]
        o = g[g["median_level_observed_m"].notna() & (g["n_wells_observed"] >= 20)]
        r2_ow, n_ow = _r2(o["open_water_ha_modelled"], o["open_water_ha_observed"])
        r2_wf, n_wf = _r2(o["wet_floor_ha_modelled"], o["wet_floor_ha_observed"])
        ax.fill_between(tt, 0, g["open_water_ha_modelled"], color="#0b6e8f", alpha=0.85,
                        label=f"open water, SSM level  (R²={r2_ow:.2f} vs observed, n={n_ow})")
        ax.fill_between(tt, g["open_water_ha_modelled"],
                        g["open_water_ha_modelled"] + g["wet_floor_ha_modelled"],
                        color="#d4a017", alpha=0.55,
                        label=f"wet floor, SSM level  (R²={r2_wf:.2f} vs observed)")
        ax.plot(t[o.index], o["open_water_ha_observed"] + o["wet_floor_ha_observed"],
                color="black", lw=0.8, label="observed-level total")
        ax.scatter(t[o.index], o["open_water_ha_observed"], s=12, color="#0b6e8f",
                   edgecolor="white", linewidth=0.3, zorder=5, label="observed open water")
        ax.set_ylabel("ha (whole warren)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7.5, loc="upper left")
        ax.set_title(f"Mode {m} — SSM monthly level through the two curves", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(OUT_45_SSM_CURVES_FIG, dpi=150)
    _write_axes(fig, list(axes), OUT_45_SSM_CURVES_AXES)
    plt.close(fig)
    saved(OUT_45_SSM_CURVES_FIG.name)


# ─────────────────────────────────────────────────────────────────────────────
# THE SWITCHING-LEVEL MAPS — cell_thresholds.npz drawn (T-77)
# ─────────────────────────────────────────────────────────────────────────────
def _reference_well_points() -> pd.DataFrame:
    """E, N of the reference network: the wells in 03_master_data.csv, located
    through 01_locations.csv on the normalised name."""
    ref = {normalize_well_name(n) for n in pd.read_csv(INT_MASTER_DATA)["Name_Original"]}
    loc = pd.read_csv(INT_LOCATIONS)
    loc["Match_ID"] = loc["Match_ID"].map(normalize_well_name)
    pts = loc[loc["Match_ID"].isin(ref)]
    if len(pts) != len(ref):
        warn(f"{len(ref) - len(pts)} reference well(s) not found in {INT_LOCATIONS.name}")
    return pts[["E", "N"]]


def plot_switching_levels() -> None:
    """Two panels, one per class, of the per-cell switching level: the reference-
    network median level (m, 0 = ground) at which the cell first reads the class
    in the winter scene stack. Floor cells never in the class are light grey;
    cells off the floor are transparent. The site boundary is read through
    kml_io (never re-parsed here) and the reference wells are drawn as points.
    The grid is the npz's own: [left, bottom, right, top, res] in EPSG:27700
    with row 0 at the top, so the image is drawn origin='upper'. The panels are
    stacked, (a) above (b), with the colour bar beneath (1.5.0; they were side by side)."""
    if not SENTINEL_CELL_THRESHOLDS.exists():
        warn(f"no {SENTINEL_CELL_THRESHOLDS.name}: switching-level map not drawn")
        return
    import matplotlib                                          # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                            # noqa: PLC0415
    from matplotlib.colors import ListedColormap, Normalize    # noqa: PLC0415
    from matplotlib.lines import Line2D                        # noqa: PLC0415
    from matplotlib.patches import Patch                       # noqa: PLC0415
    from utils.kml_io import read_kml                          # noqa: PLC0415
    from utils.map_utils import add_en_axes                    # noqa: PLC0415

    z = np.load(SENTINEL_CELL_THRESHOLDS)
    floor = z["floor"].astype(bool)
    left, bottom, right, top, _res = (float(v) for v in z["grid"])
    extent = (left, right, bottom, top)
    ever = {cls: floor & np.isfinite(z[f"h_{cls}"]) for cls in CURVE_CLASSES}
    finite_levels = np.concatenate([z[f"h_{cls}"][ever[cls]] for cls in CURVE_CLASSES])
    norm = Normalize(vmin=float(finite_levels.min()), vmax=float(finite_levels.max()))
    wells = _reference_well_points()
    boundary = None
    if DATA_KML_SITE_BOUNDARY.exists():
        # site_boundary.kml is thousands of small polygons; dissolved and lightly
        # simplified into the one outline, as Script 20's load_site_polygon does.
        from shapely.ops import unary_union                    # noqa: PLC0415
        import geopandas as gpd                                # noqa: PLC0415
        pieces = [g for g in read_kml(DATA_KML_SITE_BOUNDARY, quiet=True).geometry if g is not None]
        boundary = gpd.GeoSeries([unary_union(pieces).simplify(20, preserve_topology=True)],
                                 crs="EPSG:27700")
    else:
        warn(f"no {DATA_KML_SITE_BOUNDARY.name}: map drawn without the site boundary")

    grey = ListedColormap(["#d9d9d9"])
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 10.2), sharex=True, sharey=True,
                             constrained_layout=True)
    im = None
    panels = (("wet_floor", "(a) wet floor", "wet"), ("open_water", "(b) open water", "open water"))
    for ax, (cls, title, state) in zip(axes, panels):
        h = z[f"h_{cls}"]
        never = floor & ~ever[cls]
        ax.imshow(np.ma.masked_where(~never, np.ones_like(h)), extent=extent, origin="upper",
                  cmap=grey, vmin=0, vmax=1, interpolation="nearest", zorder=1)
        im = ax.imshow(np.ma.masked_where(~ever[cls], h), extent=extent, origin="upper",
                       cmap="YlGnBu_r", norm=norm, interpolation="nearest", zorder=2)
        if boundary is not None:
            boundary.boundary.plot(ax=ax, color="black", linewidth=0.9, zorder=3)
        ax.scatter(wells["E"], wells["N"], s=7, color="black", linewidths=0, zorder=4)
        ax.set_title(f"{title}: {int(ever[cls].sum())} of {int(floor.sum())} floor cells ever {state}",
                     fontsize=10)
        add_en_axes(ax, apply_extent=False)
        ax.set_xlim(left, right)
        ax.set_ylim(bottom, top)
    axes[0].legend(handles=[Patch(facecolor="#d9d9d9", label="floor, never in the class"),
                            Line2D([0], [0], color="black", lw=0.9, label="site boundary"),
                            Line2D([0], [0], marker="o", color="black", lw=0, markersize=3,
                                   label="reference dipwells")],
                   fontsize=7.5, loc="upper left")
    fig.colorbar(im, ax=axes.tolist(), shrink=0.85, pad=0.015,
                 location="bottom",
                 label="switching level: network-median level at first wetting (m, 0 = ground)")
    fig.savefig(OUT_45_SWITCHING_LEVELS_MAP, dpi=160)
    plt.close(fig)
    saved(OUT_45_SWITCHING_LEVELS_MAP.name)


# ─────────────────────────────────────────────────────────────────────────────
# THE PHASE TERM — wetting versus drying at the same level, and the rain (T-77)
# ─────────────────────────────────────────────────────────────────────────────
def _scene_month_rain_mm(dates: pd.Series) -> dict[str, pd.Series]:
    """The scene month's rainfall in mm, two ways: the calendar month containing
    the scene date (the primary), and the field-convention month that
    month_bucket assigns the scene — the one its h_scene was joined on. The climate
    record can end before the last scenes; those carry NaN and drop out of M2."""
    C = pd.read_csv(INT_CLIMATE, float_precision="round_trip")
    P_mm = C.set_index(pd.to_datetime(C["Date"]))["P_m"] * 1000.0   # metres -> mm
    d = pd.to_datetime(dates)
    months = {"calendar": pd.DatetimeIndex(d.dt.to_period("M").dt.to_timestamp()),
              "field": month_bucket(d)}
    return {k: pd.Series(P_mm.reindex(m).values, index=dates.index) for k, m in months.items()}


def phase_hysteresis(R: pd.DataFrame) -> pd.DataFrame:
    """Per class: does a scene in a wetting month carry more area at the same
    level than one in a drying month, and does the scene month's rain add to it?
    M0 log(area) ~ h_scene; M1 + dh_month; M2 + P_scene_month_mm. The ratio is
    exp(mean M0 residual, wetting scenes − mean, drying scenes). statsmodels OLS,
    imported here so the fit and the SSM drive above still run without it."""
    import statsmodels.api as sm                               # noqa: PLC0415
    rain = _scene_month_rain_mm(R["date"])
    one_cell_ha = (WET_AREA_GRID["res"] ** 2) / 1e4
    wetting, drying = R["phase"] == "wetting", R["phase"] == "drying"
    rows = []
    for cls in CURVE_CLASSES:
        area = R[f"{cls}_ha"].astype(float)
        clipped = bool((area <= 0).any())
        if clipped:
            warn(f"{cls}: {(area <= 0).sum()} scene(s) with zero area clipped to one cell "
                 f"({one_cell_ha} ha) before the log")
            area = area.clip(lower=one_cell_ha)
        ly = np.log(area)
        m0 = sm.OLS(ly, sm.add_constant(R[["h_scene"]])).fit()
        m1 = sm.OLS(ly, sm.add_constant(R[["h_scene", "dh_month"]])).fit()
        row = {"class": cls, "n_scenes": int(len(R)),
               "R2_h_only": float(m0.rsquared), "R2_h_dh": float(m1.rsquared),
               "dh_coef": float(m1.params["dh_month"]), "dh_p": float(m1.pvalues["dh_month"]),
               "wetting_vs_drying_ratio": float(np.exp(m0.resid[wetting].mean() - m0.resid[drying].mean())),
               "n_wetting": int(wetting.sum()), "n_drying": int(drying.sum())}
        for key, suffix in (("calendar", ""), ("field", "_field_month")):
            X = R[["h_scene", "dh_month"]].assign(P_scene_month_mm=rain[key])
            ok = X["P_scene_month_mm"].notna()
            m2 = sm.OLS(ly[ok], sm.add_constant(X[ok])).fit()
            row[f"R2_h_dh_P{suffix}"] = float(m2.rsquared)
            row[f"P_coef_per_100mm{suffix}"] = float(m2.params["P_scene_month_mm"] * 100.0)
            row[f"P_p{suffix}"] = float(m2.pvalues["P_scene_month_mm"])
            row[f"n_scenes_P{suffix}"] = int(ok.sum())
        row["zero_area_clipped"] = clipped
        rows.append(row)
        step(f"{cls}: R² {row['R2_h_only']:.2f} -> {row['R2_h_dh']:.2f} with dh (coef "
             f"{row['dh_coef']:+.2f} per m/month, p {row['dh_p']:.3f}); wetting:drying x"
             f"{row['wetting_vs_drying_ratio']:.2f} ({row['n_wetting']} vs {row['n_drying']}); "
             f"rain {row['P_coef_per_100mm']:+.2f} per 100 mm, p {row['P_p']:.3f} "
             f"(n {row['n_scenes_P']}; field month p {row['P_p_field_month']:.3f})")
    short = int(rain["calendar"].isna().sum())
    if short:
        info(f"{short} scene(s) fall after the end of {INT_CLIMATE.name} and carry no rain: M2 is "
             f"fitted on the rest")
    H = pd.DataFrame(rows)
    H.to_csv(OUT_45_PHASE_HYSTERESIS, index=False)
    saved(OUT_45_PHASE_HYSTERESIS.name)
    return H


# ─────────────────────────────────────────────────────────────────────────────
# THE REPORT NUMBERS — what the documents quote from this analysis (E16)
# ─────────────────────────────────────────────────────────────────────────────
def floor_cells() -> dict:
    """The study area and the cells ever wet, from the phase-29 floor mask and the
    per-cell switching levels in cell_thresholds.npz. A cell is 'ever in the class'
    when it carries a finite switching level, which the tool assigns only to floor
    cells seen in at least CELL_MIN_SCENES scenes."""
    if not SENTINEL_CELL_THRESHOLDS.exists():
        warn(f"no {SENTINEL_CELL_THRESHOLDS.name}: study-area numbers not emitted")
        return {}
    z = np.load(SENTINEL_CELL_THRESHOLDS)
    floor = z["floor"].astype(bool)
    ha_per_cell = (WET_AREA_GRID["res"] ** 2) / 1e4
    out = {"floor_mask_cells": int(floor.sum()), "floor_mask_area_ha": float(floor.sum() * ha_per_cell)}
    for cls in ("wet_floor", "open_water"):
        ever = floor & np.isfinite(z[f"h_{cls}"])
        out[f"{cls}_ever_cells"] = int(ever.sum())
        out[f"{cls}_ever_ha"] = float(ever.sum() * ha_per_cell)
    return out


def write_report_numbers(R: pd.DataFrame, fits: dict, oos: dict, cells: dict,
                         hyst: pd.DataFrame | None = None) -> None:
    rr = ReportNumbers()
    if cells:
        rr.add("floor_mask_area_ha", cells["floor_mask_area_ha"], unit="ha",
               note=f"phase-29 slack-floor mask, forest excluded: {cells['floor_mask_cells']} cells of "
                    f"{WET_AREA_GRID['res']} m; the area the wet-area curves are scaled to (the report's "
                    f"'study area' for the Sentinel analysis; distinct from Script 12's study_area_ha)")
        rr.add("floor_mask_cells", cells["floor_mask_cells"], unit="cells", note="floor cells in cell_thresholds.npz")
        for cls in ("wet_floor", "open_water"):
            rr.add(f"{cls}_ever_cells", cells[f"{cls}_ever_cells"], unit="cells",
                   note=f"floor cells with a switching level for {cls} (seen in >= {CELL_MIN_SCENES} scenes)")
            rr.add(f"{cls}_ever_ha", cells[f"{cls}_ever_ha"], unit="ha", note=f"{cls}_ever_cells as hectares")
    for cls in ("open_water", "wet_floor"):
        f = fits[cls]
        rr.add(f"fit_{cls}_rho", f["rho"], unit="", note=f"Spearman rho of {cls} area against the scene-date median level, {f['n']} scenes")
        rr.add(f"fit_{cls}_r2_log", fit_r2_log(R, f, cls), unit="",
               note=f"R² of the log-linear fit a·exp(b·h) for {cls}, in ln(area); Figure 45_01's label")
        rr.add(f"fit_{cls}_n_scenes", f["n"], unit="scenes", note="winter Sentinel-2 scenes in the fit (D-178, no vet)")
    for (m, cls), s in sorted(oos.items()):
        era = f"mode {m}"
        rr.add(f"oos_{m}_{cls}_r2", s["r2"], unit="", era=era,
               note=f"R² of SSM-modelled {cls} area against the observed-level area, months with >= 20 reporting wells")
        rr.add(f"oos_{m}_{cls}_n_months", s["n"], unit="months", era=era, note="well-months in the out-of-sample comparison")
        rr.add(f"oos_{m}_{cls}_median_ratio", s["median_ratio"], unit="", era=era, note="median modelled:observed area ratio")
        rr.add(f"oos_{m}_{cls}_ratio_p16", s["ratio_p16"], unit="", era=era, note="16th percentile of the modelled:observed ratio")
        rr.add(f"oos_{m}_{cls}_ratio_p84", s["ratio_p84"], unit="", era=era, note="84th percentile of the modelled:observed ratio")
    if hyst is not None:
        for _, h in hyst.iterrows():
            cls = h["class"]
            clip_note = (" (zero-area scenes clipped to one cell before the log)"
                         if h["zero_area_clipped"] else "")
            rr.add(f"hysteresis_ratio_{cls}", h["wetting_vs_drying_ratio"], unit="",
                   note=f"factor by which a wetting-phase scene carries more {cls} area than a "
                        f"drying-phase scene at the same level: exp(mean residual of log(area) ~ "
                        f"h_scene, wetting minus drying), {int(h['n_wetting'])} wetting vs "
                        f"{int(h['n_drying'])} drying of {int(h['n_scenes'])} scenes{clip_note}")
            rr.add(f"hysteresis_dh_p_{cls}", h["dh_p"], unit="",
                   note=f"p of dh_month in log({cls} area) ~ h_scene + dh_month, coefficient "
                        f"{h['dh_coef']:+.3f} per m/month over {int(h['n_scenes'])} scenes{clip_note}")
            rr.add(f"rain_term_p_{cls}", h["P_p"], unit="",
                   note=f"p of the scene month's rainfall (calendar month containing the scene "
                        f"date) in log({cls} area) ~ h_scene + dh_month + P, coefficient "
                        f"{h['P_coef_per_100mm']:+.3f} per 100 mm over {int(h['n_scenes_P'])} scenes "
                        f"with a climate row; field-month variant p {h['P_p_field_month']:.3f}{clip_note}")
    n = rr.save(OUT_45_REPORT_NUMBERS)
    saved(f"{OUT_45_REPORT_NUMBERS.name} ({n} report numbers)")


def main(no_fig: bool = False) -> int:
    banner("45", "The Sentinel wet-area model", version=__version__)
    DIR_45.mkdir(parents=True, exist_ok=True)

    phase(1, "The committed scene series")
    R = load_series()

    phase(2, "Fitting the two curves on the scenes alone")
    fits = fit_curves(R)
    write_model(fits)
    if not no_fig:
        plot_model(R, fits)
    result("the model", f"open water {fits['open_water']['a']:.0f}·exp({fits['open_water']['b']:.2f}·h) ha, "
                        f"wet floor {fits['wet_floor']['a']:.0f}·exp({fits['wet_floor']['b']:.2f}·h) ha; "
                        f"fitted range {fits['open_water']['h_min']:+.2f} to {fits['open_water']['h_max']:+.2f} m")

    phase(3, "The SSM's monthly level through the two curves")
    oos = ssm_through_curves(fits, make_fig=not no_fig)

    phase(4, "The switching-level maps and the phase term (T-77)")
    if not no_fig:
        plot_switching_levels()
    hyst = phase_hysteresis(R)

    phase(5, "The report numbers (E16)")
    write_report_numbers(R, fits, oos, floor_cells(), hyst)

    done("45")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="The Sentinel wet-area model (T-40, D-178)")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figures")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
