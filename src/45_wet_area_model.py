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

USAGE
  python3 run_analysis.py                     # runs under --full
  python3 src/45_wet_area_model.py            # standalone
  python3 src/45_wet_area_model.py --no-fig   # the CSVs only, no figures
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-17. First cut: T-40, promoting
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
    SENTINEL_TWO_CLASS_SERIES, SENTINEL_HINDCAST_MONTHLY,
)
from utils.config import WET_AREA_CLASSES                     # noqa: E402
from utils.console_utils import banner, done, info, phase, result, saved, step, warn  # noqa: E402


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


def plot_model(R: pd.DataFrame, fits: dict) -> None:
    import matplotlib                                          # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                            # noqa: PLC0415
    hh = np.linspace(R["h_scene"].min() - 0.05, R["h_scene"].max() + 0.1, 60)
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for cls, c, lab in (("open_water", "#0b6e8f", "open water (B8 <= 0.5 x median)"),
                        ("wet_floor", "#d4a017", "wet floor (0.5-0.8)")):
        f = fits[cls]
        ax.scatter(R["h_scene"], R[f"{cls}_ha"], s=24, color=c, alpha=0.85)
        ax.fill_between(hh, f["a"] * np.exp(f["b"] * hh - f["sigma_log"]),
                        f["a"] * np.exp(f["b"] * hh + f["sigma_log"]), color=c, alpha=0.12)
        ax.plot(hh, f["a"] * np.exp(f["b"] * hh), color=c, lw=2,
                label=f"{lab}: {f['a']:.0f}·exp({f['b']:.2f}·h) ha, rho {f['rho']:+.2f}")
    ax.set_xlabel("median well level at the scene date, m (0 = ground)")
    ax.set_ylabel("area, ha (whole warren)")
    ax.set_title(f"The wet-area model — {fits['open_water']['n']} winter Sentinel-2 scenes, "
                 f"B8 alone, no vet (D-178)", fontsize=9.5)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT_45_MODEL_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_45_MODEL_FIG.name)


# ─────────────────────────────────────────────────────────────────────────────
# THE SSM DRIVE — the curves on phase 27's monthly level
# ─────────────────────────────────────────────────────────────────────────────
def ssm_through_curves(fits: dict, make_fig: bool) -> int:
    """Run the two curves through phase 27's monthly SSM level, modelled and
    observed. Downstream of the fit — the curves change, this tracks them — so it
    lives here rather than being a committed input. Optional: no hindcast_monthly,
    no ssm_curves, and Step 46's history block is simply omitted."""
    if not SENTINEL_HINDCAST_MONTHLY.exists():
        warn(f"no {SENTINEL_HINDCAST_MONTHLY.name}: the SSM drive needs phase 27's "
             f"levels; ssm_through_nir_curves not written and the feed will carry no history")
        return 0
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
    for m, g in Hc.groupby("mode"):
        ok = g["median_level_observed_m"].notna() & (g["n_wells_observed"] >= 20)
        if not ok.any():
            continue
        for cls in ("open_water", "wet_floor"):
            e = np.log(g.loc[ok, f"{cls}_ha_modelled"]) - np.log(g.loc[ok, f"{cls}_ha_observed"])
            step(f"Mode {m} {cls}: median x{np.exp(np.median(e)):.2f}, 68 % range "
                 f"x{np.exp(np.percentile(e, 16)):.2f}-{np.exp(np.percentile(e, 84)):.2f} "
                 f"over {int(ok.sum())} months")
    if make_fig:
        _plot_ssm(Hc)
    return 0


def _plot_ssm(Hc: pd.DataFrame) -> None:
    import matplotlib                                          # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                            # noqa: PLC0415
    t = pd.to_datetime(Hc["month"])
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for ax, m in zip(axes, ("R", "C")):
        g = Hc[Hc["mode"] == m]
        tt = t[g.index]
        ax.fill_between(tt, 0, g["open_water_ha_modelled"], color="#0b6e8f", alpha=0.85,
                        label="open water, SSM level")
        ax.fill_between(tt, g["open_water_ha_modelled"],
                        g["open_water_ha_modelled"] + g["wet_floor_ha_modelled"],
                        color="#d4a017", alpha=0.55, label="wet floor, SSM level")
        o = g[g["median_level_observed_m"].notna() & (g["n_wells_observed"] >= 20)]
        ax.plot(t[o.index], o["open_water_ha_observed"] + o["wet_floor_ha_observed"],
                color="black", lw=0.8, label="same curves on the observed level")
        ax.set_ylabel("ha (whole warren)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7.5, loc="upper left")
        ax.set_title(f"Mode {m} — SSM monthly level through the two curves", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(OUT_45_SSM_CURVES_FIG, dpi=150)
    plt.close(fig)
    saved(OUT_45_SSM_CURVES_FIG.name)


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
    ssm_through_curves(fits, make_fig=not no_fig)

    done("45")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="The Sentinel wet-area model (T-40, D-178)")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figures")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
