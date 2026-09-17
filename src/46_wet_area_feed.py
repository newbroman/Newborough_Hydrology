#!/usr/bin/env python3
"""
46_wet_area_feed.py — the public wet-area feed the forecaster and the film read
(T-40, T-36 item 1, D-178)
==========================================================================

WHAT THIS IS

  living/wet_area_model.json: the two curves, the per-cell switching levels and
  the SSM history, published as ONE self-describing feed so every public reader
  (the scenario viewer, the century film) draws the same model without opening the
  private store. Assembles committed products; fits nothing (record_basis no_fit).

  Hash-gated (D-096): a run that moves nothing but `generated` rewrites nothing,
  so the file's timestamp stays a provenance claim rather than a byproduct of
  having run the step again.

INPUTS — all committed
  outputs/45_wet_area/45_01_wet_area_model.csv ......... the curves (Step 45)
  outputs/45_wet_area/45_02_ssm_through_nir_curves.csv . the SSM drive; the history
                                                         block (Step 45; optional)
  data/sentinel/cell_thresholds.npz .................... per-cell switching levels
                                                         and the phase-29 floor mask
  data/sentinel/well_fit.csv ........................... phase 27's per-well-month
                                                         fit; the mode block (optional)

OUTPUT
  living/wet_area_model.json ........................... schema nw-wet-area-1

USAGE
  python3 run_analysis.py                     # runs under --full, after Step 45
  python3 src/46_wet_area_feed.py             # standalone (needs Step 45's outputs)
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-17. First cut: T-40. The
#   write_wet_area_feed / _wet_area_history / _mode_fit / _sha16 of
#   tools/sentinel_wet_floor.py, moved here unchanged in substance and re-pointed:
#   the curves come from Step 45's outputs/45_wet_area/, the cell thresholds and
#   the mode fit from the committed data/sentinel/ inputs. Every field but `source`
#   (now this script) and both content hashes are identical to the tool's feed, so
#   the committed living/wet_area_model.json diffs only in `source` and `generated`.

import argparse
import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.paths import (                                     # noqa: E402
    LIVING_WET_AREA_MODEL, OUT_45_MODEL, OUT_45_SSM_CURVES,
    SENTINEL_CELL_THRESHOLDS, SENTINEL_WELL_FIT,
)
from utils.config import (                                    # noqa: E402
    WET_AREA_GRID as GRID, NIR_BLACK_RATIO, NIR_DARK_RATIO, CELL_MIN_SCENES,
    WET_AREA_CLASSES, WET_AREA_FEED_SCHEMA as FEED_SCHEMA,
    WET_AREA_CELL_NEVER as CELL_NEVER, WET_AREA_LEVEL_DEFINITION as LEVEL_DEFINITION,
)
from utils.console_utils import banner, done, info, phase, saved, step, warn  # noqa: E402


def _sha16(path) -> str:
    import hashlib                                            # noqa: PLC0415
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────────
# THE MODE FIT AND THE HISTORY BLOCK
# ─────────────────────────────────────────────────────────────────────────────
def _mode_fit():
    """Each hindcast mode's fit against the wells: RMSE and Spearman rho over every
    well-month with both an observed and a modelled level.

    COMPUTED, not scraped, and by ranks so it runs without scipy.
    """
    if not SENTINEL_WELL_FIT.exists():
        return None
    F = pd.read_csv(SENTINEL_WELL_FIT)
    need = {"mode", "observed_h_m", "modelled_h_recurrence_m"}
    if not need.issubset(F.columns):
        warn(f"{SENTINEL_WELL_FIT.name} has no {sorted(need - set(F.columns))}; mode fit omitted")
        return None
    out = {"source": SENTINEL_WELL_FIT.name, "source_hash": _sha16(SENTINEL_WELL_FIT),
           "definition": ("modelled_h_recurrence_m against observed_h_m over every "
                          "well-month carrying both; rho is Spearman"),
           "modes": {}}
    for mode, g in F.groupby("mode"):
        d = g[["observed_h_m", "modelled_h_recurrence_m"]].dropna()
        if len(d) < 2:
            continue
        err = d["modelled_h_recurrence_m"].to_numpy(float) - d["observed_h_m"].to_numpy(float)
        rho = float(d["modelled_h_recurrence_m"].rank().corr(d["observed_h_m"].rank()))
        out["modes"][str(mode)] = {"rmse_m": round(float(np.sqrt((err ** 2).mean())), 3),
                                   "rho": round(rho, 3), "n": int(len(d))}
    return out if out["modes"] else None


def _wet_area_history():
    """The SSM's monthly median level through the record, for the forecaster's
    history control — or None when Step 45 has not written the SSM drive.

    The cell layer is a function of the median level and nothing else, so a level
    series is the only thing that lets a page show a month that has already
    happened; and the film draws exactly these levels (Mode R), so a page fed from
    anywhere else could not be compared with it. The observed level travels with
    it, unrounded from the CSV's own 3 dp.
    """
    if not OUT_45_SSM_CURVES.exists():
        return None
    H = pd.read_csv(OUT_45_SSM_CURVES)
    need = {"month", "mode", "median_level_modelled_m"}
    if not need.issubset(H.columns):
        warn(f"{OUT_45_SSM_CURVES.name} has no {sorted(need - set(H.columns))}; history omitted")
        return None
    months = sorted(H["month"].astype(str).unique())
    idx = {m: i for i, m in enumerate(months)}
    level = {}
    for mode, g in H.groupby("mode"):
        col = [None] * len(months)
        for _, r in g.iterrows():
            v = r["median_level_modelled_m"]
            col[idx[str(r["month"])]] = None if pd.isna(v) else round(float(v), 3)
        level[str(mode)] = col
    obs = [None] * len(months)
    nobs = [None] * len(months)
    if "median_level_observed_m" in H.columns:
        for _, r in H.iterrows():
            i = idx[str(r["month"])]
            v = r["median_level_observed_m"]
            if obs[i] is None and not pd.isna(v):
                obs[i] = round(float(v), 3)
            if "n_wells_observed" in H.columns and nobs[i] is None and not pd.isna(r["n_wells_observed"]):
                nobs[i] = int(r["n_wells_observed"])
    fit = _mode_fit()
    return {"source": OUT_45_SSM_CURVES.name, "source_hash": _sha16(OUT_45_SSM_CURVES),
            "fit": fit,
            "definition": ("the SSM's monthly median well level (phase 27 recurrence) driving the "
                           "curves, D-178 item 3; mode R is the one the film animates"),
            "default_mode": "R" if "R" in level else sorted(level)[0],
            "months": months, "level_m": level,
            "level_observed_m": obs, "n_wells_observed": nobs}


# ─────────────────────────────────────────────────────────────────────────────
# THE FEED
# ─────────────────────────────────────────────────────────────────────────────
def write_wet_area_feed() -> int:
    """living/wet_area_model.json — the two curves and the per-cell switching
    levels, as a public feed for the forecaster and the film. Hash-gated."""
    model_csv = OUT_45_MODEL
    npz_path = SENTINEL_CELL_THRESHOLDS
    for p in (model_csv, npz_path):
        if not p.exists():
            warn(f"no {p.name} — run Step 45 (curves) and regenerate the cell "
                 f"thresholds (tools/sentinel_wet_floor.py --two-class); feed not written")
            return 1
    M = pd.read_csv(model_csv).set_index("cls")
    z = np.load(npz_path)
    floor = z["floor"].astype(bool)
    W = int((GRID["right"] - GRID["left"]) / GRID["res"])
    H = int((GRID["top"] - GRID["bottom"]) / GRID["res"])
    if floor.shape != (H, W):
        warn(f"{npz_path.name} is {floor.shape}, GRID says {(H, W)} — feed not written")
        return 1

    def _encode(a):
        """metres -> int16 centimetres, row-major, row 0 = NORTH (from_origin(left, top));
        CELL_NEVER where the cell is off the floor or was never seen in the class."""
        cm = np.rint(np.asarray(a, dtype="float64") * 100.0)
        out = np.full(cm.shape, CELL_NEVER, dtype="<i2")
        ok = floor & np.isfinite(cm) & (np.abs(cm) < CELL_NEVER)
        out[ok] = cm[ok].astype("<i2")
        return base64.b64encode(out.tobytes(order="C")).decode("ascii"), int(ok.sum())

    ow_b64, n_ow = _encode(z["h_open_water"])
    wf_b64, n_wf = _encode(z["h_wet_floor"])
    # The floor mask itself. A switching level says a cell HAS been seen in the
    # class; it cannot say a cell is floor that never was, so the film's "never
    # seen wet" fill needs the mask alongside the levels.
    floor_b64 = base64.b64encode(np.packbits(floor, axis=None).tobytes()).decode("ascii")
    curves = {}
    for cls in WET_AREA_CLASSES:
        if cls not in M.index:
            continue
        r = M.loc[cls]
        curves[cls] = {"a": float(r["a"]), "b": float(r["b"]),
                       "sigma_log": float(r["sigma_log"]),
                       "sigma_factor": float(r["sigma_factor"]),
                       "rho": float(r["rho"]), "n": int(r["n"])}
    hmin = float(M["h_min"].min())
    hmax = float(M["h_max"].max())
    history = _wet_area_history()
    body = {
        "schema": FEED_SCHEMA,
        "decision": "D-178",
        "source": f"46_wet_area_feed.py {__version__}",
        "source_hash": _sha16(model_csv),
        "source_cells_hash": _sha16(npz_path),
        "level_definition": LEVEL_DEFINITION,
        "area_definition": ("hectares on the slack floors, scaled to the whole warren by the "
                            "scene's clear fraction; NOT a flood map (D-177)"),
        "curves": curves,
        "curve_form": "area_ha = a * exp(b * h); sigma is a log-space factor (x/div sigma_factor)",
        "fitted_range_m": {"min": hmin, "max": hmax},
        "classes": {
            "open_water": f"B8 <= {NIR_BLACK_RATIO:.2f} x the scene's clear-floor median",
            "wet_floor": f"{NIR_BLACK_RATIO:.2f} < B8 <= {NIR_DARK_RATIO:.2f} x median",
        },
        "grid": {"left": GRID["left"], "bottom": GRID["bottom"], "right": GRID["right"],
                 "top": GRID["top"], "res": GRID["res"], "crs": "EPSG:27700",
                 "cols": W, "rows": H},
        "cells": {
            "dtype": "int16", "byte_order": "little",
            "order": "row-major, row 0 = NORTH edge (top), column 0 = WEST edge (left)",
            "units": "centimetres of median well level (0 = ground)",
            "never": CELL_NEVER,
            "encoding": (
                "base64 of an int16 array, one value per 10 m cell: the median well level at "
                f"which the cell switches into the class; {CELL_NEVER} = never seen in the class, "
                f"seen in fewer than {CELL_MIN_SCENES} scenes, or not on the phase 29 floor. "
                "NOTE the asymmetry with `curves`: `cells.wet_floor` is the DARK-TOTAL switching "
                "level (B8 <= 0.80 x median, i.e. open water OR wet floor), exactly as "
                "sentinel_wet_floor._animate uses it — draw it as the yellow layer and overdraw "
                "open water in blue; the wet-floor-only cells are (wet_floor <= h) AND NOT "
                "(open_water <= h). `curves.wet_floor` is the RING alone (0.50-0.80)."),
            "n_open_water": n_ow, "n_wet_floor": n_wf,
            "n_floor": int(floor.sum()), "floor_ha": round(float(floor.sum()) * 0.01, 2),
            "floor_encoding": ("base64 of numpy.packbits over the row-major boolean mask, "
                               "MSB first; unpack with numpy.unpackbits and reshape to "
                               "(rows, cols). True = on the phase 29 slack floor inside the "
                               "warren, which is the study area the whole model applies to"),
            "open_water": ow_b64, "wet_floor": wf_b64, "floor": floor_b64,
        },
        "history": history,
        "colours": {"open_water": "#0b6e8f", "wet_floor": "#d4a017"},
        "caveat": ("cells switch at the level Sentinel-2 saw them switch in 2016-2026; an "
                   "illustration of the area model on the Sentinel grid, not a prediction of "
                   "where water will stand (D-177)"),
    }
    if LIVING_WET_AREA_MODEL.exists():
        try:
            old = json.loads(LIVING_WET_AREA_MODEL.read_text(encoding="utf-8"))
            old.pop("generated", None)
            if old == json.loads(json.dumps(body)):
                info(f"{LIVING_WET_AREA_MODEL.name} unchanged (hash gate) — not rewritten")
                return 0
        except Exception:                                     # noqa: BLE001
            pass
    feed = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    feed.update(body)
    LIVING_WET_AREA_MODEL.parent.mkdir(parents=True, exist_ok=True)
    LIVING_WET_AREA_MODEL.write_text(json.dumps(feed, indent=1) + "\n", encoding="utf-8")
    if history:
        step(f"history: {len(history['months'])} months {history['months'][0]} to "
             f"{history['months'][-1]}, modes {'/'.join(sorted(history['level_m']))}")
        if history.get("fit"):
            for m, f in sorted(history["fit"]["modes"].items()):
                step(f"  mode {m}: RMSE {f['rmse_m']:.3f} m, rho {f['rho']:+.3f}, n {f['n']}")
        else:
            warn(f"no {SENTINEL_WELL_FIT.name}: the page will explain the modes without their fit")
    else:
        warn(f"no {OUT_45_SSM_CURVES.name}: the feed carries no history and the page's history "
             f"control will be hidden")
    step(f"{n_ow} cells with an open-water switching level, {n_wf} with a dark-total one, "
         f"of {int(floor.sum())} on the floor; {LIVING_WET_AREA_MODEL.stat().st_size / 1024:.0f} kB")
    saved(f"living/{LIVING_WET_AREA_MODEL.name}  (the public feed — D-178, T-36)")
    return 0


def main() -> int:
    banner("46", "The public wet-area feed", version=__version__)
    phase(1, "The public feed the forecaster and the film read")
    rc = write_wet_area_feed()
    done("46")
    return rc


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="The public wet-area feed (T-40, D-178)")
    ap.parse_args()
    sys.exit(main())
