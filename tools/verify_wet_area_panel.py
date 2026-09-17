#!/usr/bin/env python3
"""
verify_wet_area_panel.py — does the forecaster's wet-area panel show what the
model says? (T-37, D-178)

WHAT IT CHECKS, AND WHY EACH CHECK IS WORTH MAKING

  1. THE PANEL'S NUMBERS, OFFLINE. The page's own JavaScript is extracted
     VERBATIM from the rendered outputs/11b_spatial_thresholds/forecaster.html
     — the block between /*__WA_CORE_START__*/ and /*__WA_CORE_END__*/ — and run
     under node against the page's own data bundle. The same three scenarios are
     then computed here in Python from living/wet_area_model.json. Two
     implementations, one set of inputs; they must agree. Reading the page's
     numbers off a screenshot is not verification, and neither is re-deriving
     them from the same code.

  2. THE RECURRENCE ITSELF, against the project's closed form. Both sides above
     iterate h(t) = (1-b3)h(t-1) + b1*lam*P - b2*PET - b3*D forward, so a shared
     sign error would pass check 1 unnoticed. So each well's projected h_n is
     handed BACK to utils.model_utils.pflood_lambda as h_target: the lambda it
     returns must be the lambda the projection ran at. That function is the
     pipeline's own Section 3.6.3 solution and was written for a different
     purpose, so it is an independent witness.

  3. THE CELL DECODE, against the array it came from. The page decodes base64
     int16 centimetres out of the feed; here the cell counts at a given level are
     taken straight from data/sentinel/cell_thresholds.npz. The
     encode/decode round trip must not move a single cell.

  4. THE CURVES AT A KNOWN MONTH. The two areas at February 2021's modelled Mode
     R level must reproduce outputs/45_wet_area/45_02_ssm_through_nir_curves.csv's own figures for
     that month — the film still W94_27_wet_area_frame_2021-02.png is the same
     month for the eye, but the CSV is what is compared.

  5. PROVENANCE. The feed carries schema, source, source_hash and generated, and
     the hash baked into the page is the hash of the feed on disk.

  6. THE HISTORY BLOCK, against the drive CSV. The page's history control draws
     the cell layer at a month from the record, taking that month's level from
     the feed. A transcription slip there would put the wrong month on the screen
     and nothing else would notice, so every month and mode is compared with
     outputs/45_wet_area/45_02_ssm_through_nir_curves.csv. A feed with no history is not a failure.

  7. THE MODES' FIT, recomputed. The page quotes each mode's RMSE and rho where it
     explains what Mode R and Mode C are, so a wrong figure is a wrong sentence on a
     public page. They are recomputed here from data/sentinel/well_fit.csv — and phase 27's
     own fail condition, that Mode R must beat Mode C, is asserted, because the page
     offers R as its default.

USAGE
  python3 tools/verify_wet_area_panel.py                  # all seven checks
  python3 tools/verify_wet_area_panel.py --ref 2026-09    # fix the reference month
  python3 tools/verify_wet_area_panel.py --markdown       # table for the handover

  Needs node (any version with Int16Array; v12+). numpy and pandas only.
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) - 2026-09-17. Check 7: the per-mode
#   RMSE and rho the feed carries, recomputed here from data/sentinel/well_fit.csv, and the
#   summary CSV's own fail condition (Mode R must beat Mode C) asserted. The page
#   quotes these where it explains the two modes, so a wrong one is a wrong sentence
#   on a public page.
# v1.1.0  # Hollingham (2026) - 2026-09-17. Check 6: the feed's
#   `history` block against outputs/45_wet_area/45_02_ssm_through_nir_curves.csv, month for month and
#   mode for mode. The page's history control draws the cell layer from it, so a
#   transcription slip there would put the wrong month on the screen silently.
# v1.0.0  # Hollingham (2026) - 2026-09-16. First cut, T-37.

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.console_utils import banner, phase, result, saved, step, warn  # noqa: E402

PAGE = REPO / "outputs" / "11b_spatial_thresholds" / "forecaster.html"
FEED = REPO / "living" / "wet_area_model.json"
NPZ = REPO / "data" / "sentinel" / "cell_thresholds.npz"
SSM_CSV = REPO / "outputs" / "45_wet_area" / "45_02_ssm_through_nir_curves.csv"
WELL_FIT = REPO / "data" / "sentinel" / "well_fit.csv"
STILL = REPO / "working" / "updates" / "W94_27_wet_area_frame_2021-02.png"
TOL_HA = 1e-6          # the two implementations run the same arithmetic in doubles
TOL_LAM = 1e-6


# ── the page ─────────────────────────────────────────────────────────────────
def _page_bundle_and_core(html: str) -> tuple[str, str]:
    """The injected bundle statement and the pure core block, as source text."""
    i = html.index("const DATA = ")
    j = html.index("\n};", i) + 3
    bundle = html[i:j]
    a = html.index("/*__WA_CORE_START__*/")
    b = html.index("/*__WA_CORE_END__*/") + len("/*__WA_CORE_END__*/")
    return bundle, html[a:b]


NODE_DRIVER = r"""
// The page's own core, verbatim, plus its own bundle. No DOM, no fetch.
__CORE__
__BUNDLE__
const FEED = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const SCEN = JSON.parse(process.argv[3]);
// The curves the PAGE draws with are the ones baked into its bundle; the feed's
// are what check 5 proves them equal to. Use the baked ones here, so a page
// built against a stale model fails check 1 as well as check 5.
const CURVES = (DATA.wet_area && DATA.wet_area.curves) ? DATA.wet_area.curves : FEED.curves;
const RANGE  = (DATA.wet_area && DATA.wet_area.fitted_range_m)
  ? DATA.wet_area.fitted_range_m : FEED.fitted_range_m;
function starts(refMonth){
  const out = {};
  for(const w of DATA.wells){
    const c = DATA.cluster_coeffs[w.cluster];
    if(!c) continue;
    let d = (c.monthly_clim && c.monthly_clim[refMonth] !== undefined)
      ? c.monthly_clim[refMonth] : w.default_h_prev;
    if(d === null || d === undefined || !isFinite(d)) continue;
    out[w.name] = -Math.abs(d);
  }
  return out;
}
const out = {scenarios: [], cells: null};
for(const sc of SCEN.scenarios){
  const months = waProject(DATA.wells, DATA.cluster_coeffs, starts(sc.ref_month), sc.lambda,
                           sc.ref_month, sc.ref_year, SCEN.horizon,
                           DATA.P_clim, DATA.PET_clim, DATA.drainage_datum);
  const rows = months.map(m => {
    const A = waAreas(CURVES, RANGE, m.median);
    return {ahead: m.ahead, label: m.label, n: m.n, median: m.median, h_used: A.h_used,
            held: A.held, open_water_ha: A.open_water.ha, open_water_lo: A.open_water.lo,
            open_water_hi: A.open_water.hi, wet_floor_ha: A.wet_floor.ha,
            wet_floor_lo: A.wet_floor.lo, wet_floor_hi: A.wet_floor.hi};
  });
  // every well's final level, for the closed-form cross-check
  const last = months[months.length - 1];
  out.scenarios.push({name: sc.name, lambda: sc.lambda, ref_month: sc.ref_month,
                      ref_year: sc.ref_year, rows: rows, final_levels: last.levels,
                      horizon_months: months.map(m => m.month)});
}
if(SCEN.cell_level !== null && SCEN.cell_level !== undefined){
  const ow = waDecodeCells(FEED.cells.open_water), wf = waDecodeCells(FEED.cells.wet_floor);
  out.cells = waCellCounts(ow, wf, SCEN.cell_level, FEED.cells.never);
  out.cells.level = SCEN.cell_level;
  out.cells.len = ow.length;
}
process.stdout.write(JSON.stringify(out));
"""


def run_page(core: str, bundle: str, scen: dict) -> dict:
    drv = NODE_DRIVER.replace("__CORE__", core).replace("__BUNDLE__", bundle)
    with tempfile.TemporaryDirectory() as td:
        js = Path(td) / "wa_page.js"
        js.write_text(drv, encoding="utf-8")
        r = subprocess.run(["node", str(js), str(FEED), json.dumps(scen)],
                           capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"node failed: {r.stderr.strip()[:400]}")
    return json.loads(r.stdout)


# ── the independent Python side ──────────────────────────────────────────────
def py_project(bundle: dict, feed: dict, lam: float, ref_month: int, ref_year: int,
               horizon: int) -> list[dict]:
    coeffs, P, E = bundle["cluster_coeffs"], bundle["P_clim"], bundle["PET_clim"]
    D = float(bundle["drainage_datum"])
    h = {}
    for w in bundle["wells"]:
        c = coeffs.get(w["cluster"])
        if c is None:
            continue
        mc = c.get("monthly_clim") or {}
        d = mc.get(str(ref_month), mc.get(ref_month, w["default_h_prev"]))
        if d is None or not np.isfinite(d):
            continue
        h[w["name"]] = -abs(float(d))
    rng, cur = feed["fitted_range_m"], feed["curves"]
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m, y, rows = ref_month, ref_year, []
    for k in range(horizon):
        m += 1
        if m > 12:
            m, y = 1, y + 1
        vals = []
        for w in bundle["wells"]:
            n = w["name"]
            if n not in h:
                continue
            c = coeffs[w["cluster"]]
            p, e = P.get(str(m), P.get(m)), E.get(str(m), E.get(m))
            h[n] = (1 - c["b3"]) * h[n] + c["b1"] * lam * p - c["b2"] * e - c["b3"] * D
            vals.append(h[n])
        med = float(np.median(vals)) if vals else float("nan")
        hc = min(rng["max"], max(rng["min"], med))
        held = "above" if med > rng["max"] else ("below" if med < rng["min"] else None)
        row = {"ahead": k + 1, "label": f"{names[m - 1]} {y}", "n": len(vals),
               "median": med, "h_used": hc, "held": held}
        for cls in ("open_water", "wet_floor"):
            a, b, s = cur[cls]["a"], cur[cls]["b"], cur[cls]["sigma_factor"]
            A = a * math.exp(b * hc)
            row[f"{cls}_ha"], row[f"{cls}_lo"], row[f"{cls}_hi"] = A, A / s, A * s
        rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", metavar="YYYY-MM", help="reference month (default: this month)")
    ap.add_argument("--horizon", type=int, default=12)
    ap.add_argument("--markdown", action="store_true", help="also print a handover table")
    args = ap.parse_args()
    banner("Forecaster wet-area panel — offline verification", __version__)
    for p in (PAGE, FEED):
        if not p.exists():
            warn(f"missing {p}")
            return 1
    if subprocess.run(["which", "node"], capture_output=True).returncode != 0:
        warn("node is not on PATH; this check runs the page's own JS and cannot proceed. "
             "sudo apt install nodejs")
        return 1

    ref = pd.Timestamp.today() if not args.ref else pd.Timestamp(args.ref + "-01")
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    html = PAGE.read_text(encoding="utf-8")
    bundle_src, core = _page_bundle_and_core(html)
    bundle = json.loads(bundle_src[len("const DATA = "):].rstrip().rstrip(";"))

    phase(1, "The page's own JS and this script, on the same three scenarios")
    scen = {"horizon": args.horizon, "cell_level": None, "scenarios": [
        {"name": "climatological", "lambda": 1.00, "ref_month": int(ref.month), "ref_year": int(ref.year)},
        {"name": "dry (0.60x)", "lambda": 0.60, "ref_month": int(ref.month), "ref_year": int(ref.year)},
        {"name": "exceptional (2.00x), from Sep 2020", "lambda": 2.00, "ref_month": 9, "ref_year": 2020},
    ]}
    ssm = pd.read_csv(SSM_CSV) if SSM_CSV.exists() else None
    if ssm is not None:
        r = ssm[(ssm["month"] == "2021-02") & (ssm["mode"] == "R")]
        scen["cell_level"] = float(r["median_level_modelled_m"].iloc[0]) if len(r) else None
    page = run_page(core, bundle_src, scen)

    worst, rows_md, failures = 0.0, [], 0
    for sc, pg in zip(scen["scenarios"], page["scenarios"]):
        py = py_project(bundle, feed, sc["lambda"], sc["ref_month"], sc["ref_year"], args.horizon)
        for a, b in zip(pg["rows"], py):
            for k in ("median", "open_water_ha", "open_water_lo", "open_water_hi",
                      "wet_floor_ha", "wet_floor_lo", "wet_floor_hi"):
                d = abs(a[k] - b[k])
                worst = max(worst, d)
                if d > TOL_HA:
                    failures += 1
                    warn(f"{sc['name']} {a['label']} {k}: page {a[k]!r} vs python {b[k]!r}")
            if a["held"] != b["held"]:
                failures += 1
                warn(f"{sc['name']} {a['label']}: held {a['held']!r} vs {b['held']!r}")
        first, last = pg["rows"][0], pg["rows"][-1]
        step(f"{sc['name']}: n={first['n']} wells; {first['label']} median {first['median']:+.3f} m "
             f"-> {last['label']} {last['median']:+.3f} m; open water "
             f"{first['open_water_ha']:.1f} -> {last['open_water_ha']:.1f} ha, wet floor "
             f"{first['wet_floor_ha']:.1f} -> {last['wet_floor_ha']:.1f} ha"
             + (f"  [held: {last['held']}]" if last["held"] else ""))
        rows_md.append((sc["name"], sc["lambda"], first, last))
    result("panel vs python",
           f"{'OK' if not failures else str(failures) + ' MISMATCH'} — worst absolute difference "
           f"{worst:.3e} over {len(scen['scenarios']) * args.horizon * 7} compared values")

    phase(2, "The recurrence against the pipeline's own closed form (pflood_lambda)")
    from utils.model_utils import pflood_lambda                # noqa: PLC0415
    P = {int(k): float(v) for k, v in bundle["P_clim"].items()}
    E = {int(k): float(v) for k, v in bundle["PET_clim"].items()}
    D = float(bundle["drainage_datum"])
    bad, checked, worst_lam = 0, 0, 0.0
    for sc, pg in zip(scen["scenarios"], page["scenarios"]):
        months = pg["horizon_months"]
        starts = {}
        for w in bundle["wells"]:
            c = bundle["cluster_coeffs"].get(w["cluster"])
            if c is None:
                continue
            mc = c.get("monthly_clim") or {}
            d = mc.get(str(sc["ref_month"]), mc.get(sc["ref_month"], w["default_h_prev"]))
            if d is None or not np.isfinite(d):
                continue
            starts[w["name"]] = -abs(float(d))
        for w in bundle["wells"]:
            n = w["name"]
            if n not in pg["final_levels"] or n not in starts:
                continue
            c = bundle["cluster_coeffs"][w["cluster"]]
            got = pflood_lambda(h_target=pg["final_levels"][n], h_0=starts[n],
                                b1=c["b1"], b2=c["b2"], b3=c["b3"],
                                months=months, P_clim=P, PET_clim=E, drainage_datum=D)["lam"]
            checked += 1
            worst_lam = max(worst_lam, abs(got - sc["lambda"]))
            if abs(got - sc["lambda"]) > TOL_LAM:
                bad += 1
                if bad < 4:
                    warn(f"{sc['name']} {n}: closed form returns lambda {got:.9f}, projection ran "
                         f"at {sc['lambda']:.2f}")
    result("closed-form inversion",
           f"{'OK' if not bad else str(bad) + ' of ' + str(checked) + ' FAILED'} — {checked} "
           f"well-scenarios, worst |dlambda| {worst_lam:.3e}")
    failures += bad

    phase(3, "The cell decode against data/sentinel/cell_thresholds.npz")
    if page["cells"] is None or not NPZ.exists():
        warn("skipped: no 2021-02 row in the SSM CSV, or no npz on this machine")
    else:
        z = np.load(NPZ)
        floor = z["floor"].astype(bool)
        lv = page["cells"]["level"]
        lvc = math.floor(lv * 100 + 0.5)      # JS Math.round, not banker's rounding
        n_ow = int((floor & np.isfinite(z["h_open_water"]) &
                    (np.rint(z["h_open_water"] * 100) <= lvc)).sum())
        n_dk = int((floor & np.isfinite(z["h_wet_floor"]) &
                    (np.rint(z["h_wet_floor"] * 100) <= lvc)).sum())
        ok = (n_ow == page["cells"]["open_water"] and n_dk == page["cells"]["dark_total"]
              and page["cells"]["len"] == floor.size)
        failures += 0 if ok else 1
        step(f"at h = {lv:+.3f} m (Feb 2021, SSM Mode R): page {page['cells']['open_water']} "
             f"open-water cells / {page['cells']['dark_total']} dark-total; npz {n_ow} / {n_dk}")
        step(f"areas from the cells: {page['cells']['open_water'] * 0.01:.1f} ha open water, "
             f"{page['cells']['wet_floor_ring'] * 0.01:.1f} ha wet-floor ring "
             f"(cells are floor-only and unscaled; the curves are whole-warren)")
        result("cell decode", ('OK — not one cell moved' if ok else 'MISMATCH')
               + (f"; the eye check is {STILL.name}" if STILL.exists() else ""))

    phase(4, "The curves at February 2021 against outputs/45_wet_area/45_02_ssm_through_nir_curves.csv")
    if ssm is None or scen["cell_level"] is None:
        warn("skipped: no SSM CSV")
    else:
        r = ssm[(ssm["month"] == "2021-02") & (ssm["mode"] == "R")].iloc[0]
        h = float(r["median_level_modelled_m"])
        bad4 = 0
        for cls, col in (("open_water", "open_water_ha_modelled"), ("wet_floor", "wet_floor_ha_modelled")):
            c = feed["curves"][cls]
            mine = c["a"] * math.exp(c["b"] * h)
            # the CSV is rounded to 3 dp by sentinel_wet_floor
            if abs(mine - float(r[col])) > 5e-3:
                bad4 += 1
                warn(f"{cls}: feed gives {mine:.3f} ha, CSV says {float(r[col]):.3f}")
            else:
                step(f"{cls} at {h:+.3f} m: {mine:.3f} ha, CSV {float(r[col]):.3f} ha")
        failures += bad4
        result("curves vs the committed drive", "OK" if not bad4 else "MISMATCH")

    phase(5, "Provenance")
    miss = [k for k in ("generated", "schema", "source", "source_hash", "decision")
            if not feed.get(k)]
    baked = (bundle.get("wet_area") or {}).get("source_hash")
    if miss:
        warn(f"the feed has no {', '.join(miss)}")
        failures += 1
    else:
        step(f"{feed['schema']} · {feed['source']} · model {feed['source_hash']} · "
             f"cells {feed.get('source_cells_hash')} · {feed['generated']} · {feed['decision']}")
    # The coverage boundary. If warren.kml ever goes missing, 11b logs a note and the
    # page draws the cells with no boundary at all — which is the exact misreading this
    # was added to prevent ("the forest is dry" for "the forest was never measured"),
    # so its absence is a failure here rather than a shrug.
    rings = (bundle.get("wet_area") or {}).get("mask_outline")
    if not rings:
        warn("the bundle carries no mask_outline: the cell layer will be drawn with no "
             "warren boundary, and absent cells become indistinguishable from dry ones. "
             "Check data/geo/warren.kml and re-run Script 11b.")
        failures += 1
    else:
        step(f"coverage boundary: {len(rings)} ring(s), "
             f"{sum(len(r) for r in rings)} vertices from data/geo/warren.kml")

    if baked != feed.get("source_hash"):
        warn(f"the page was built against model {baked}, the feed on disk is "
             f"{feed.get('source_hash')} — re-run Script 11b")
        failures += 1
    else:
        result("page vs feed", f"the same model ({baked})")

    phase(6, "The feed's history against outputs/45_wet_area/45_02_ssm_through_nir_curves.csv")
    H = feed.get("history")
    if H is None:
        warn("the feed carries no history block (phase 4 has not run); the page's history "
             "control will be hidden. Not a failure.")
    elif ssm is None:
        warn("skipped: no SSM CSV on this machine to check it against")
    else:
        bad6, checked6 = 0, 0
        months = list(H["months"])
        want = sorted(ssm["month"].astype(str).unique())
        if months != want:
            warn(f"history months differ from the CSV: {len(months)} vs {len(want)}")
            bad6 += 1
        idx = {m: i for i, m in enumerate(months)}
        for mode, g in ssm.groupby("mode"):
            col = H["level_m"].get(str(mode))
            if col is None:
                warn(f"history has no mode {mode}")
                bad6 += 1
                continue
            for _, r in g.iterrows():
                i = idx.get(str(r["month"]))
                v = r["median_level_modelled_m"]
                mine = col[i] if i is not None else None
                checked6 += 1
                if pd.isna(v):
                    if mine is not None:
                        bad6 += 1
                elif mine is None or abs(float(mine) - round(float(v), 3)) > 1e-9:
                    bad6 += 1
                    if bad6 < 4:
                        warn(f"{r['month']} mode {mode}: feed {mine!r}, CSV {float(v):.3f}")
        step(f"{len(months)} months {months[0]} to {months[-1]}, "
             f"modes {'/'.join(sorted(H['level_m']))}, {checked6} levels compared")
        n_obs = sum(1 for x in (H.get("level_observed_m") or []) if x is not None)
        step(f"{n_obs} month(s) carry an observed level as well")
        failures += bad6
        result("history vs the drive CSV", "OK" if not bad6 else f"{bad6} MISMATCH")

    phase(7, "The modes' fit, recomputed from data/sentinel/well_fit.csv")
    fit = (H or {}).get("fit") if H else None
    if fit is None:
        warn("the feed carries no mode fit; the page will explain the modes without numbers. "
             "Not a failure.")
    elif not WELL_FIT.exists():
        warn(f"skipped: no {WELL_FIT.name} on this machine")
    else:
        F = pd.read_csv(WELL_FIT)
        bad7 = 0
        for mode, g in F.groupby("mode"):
            mine = fit["modes"].get(str(mode))
            if mine is None:
                warn(f"the feed has no fit for mode {mode}")
                bad7 += 1
                continue
            d = g[["observed_h_m", "modelled_h_recurrence_m"]].dropna()
            err = (d["modelled_h_recurrence_m"].to_numpy(float)
                   - d["observed_h_m"].to_numpy(float))
            rmse = round(float(np.sqrt((err ** 2).mean())), 3)
            rho = round(float(d["modelled_h_recurrence_m"].rank()
                              .corr(d["observed_h_m"].rank())), 3)
            ok7 = (rmse == mine["rmse_m"] and rho == mine["rho"] and len(d) == mine["n"])
            bad7 += 0 if ok7 else 1
            step(f"mode {mode}: feed RMSE {mine['rmse_m']:.3f} rho {mine['rho']:+.3f} "
                 f"n {mine['n']}; recomputed {rmse:.3f} / {rho:+.3f} / {len(d)}"
                 + ("" if ok7 else "   <-- MISMATCH"))
        # The summary CSV's own fail condition, comparison 1: the annual restart has to
        # be buying something, or Mode R is not worth offering as the default.
        mR, mC = fit["modes"].get("R"), fit["modes"].get("C")
        if mR and mC:
            if mR["rmse_m"] < mC["rmse_m"] and mR["rho"] > mC["rho"]:
                step(f"Mode R beats Mode C on both, as phase 27 requires "
                     f"({mR['rmse_m']:.3f} < {mC['rmse_m']:.3f} m; "
                     f"{mR['rho']:+.3f} > {mC['rho']:+.3f})")
            else:
                warn("Mode R does NOT beat Mode C — phase 27's comparison 1 fail condition. "
                     "The page offers R as the default; that default is now unearned.")
                bad7 += 1
        failures += bad7
        result("mode fit vs the well table", "OK" if not bad7 else f"{bad7} MISMATCH")

    if args.markdown:
        print("\n| scenario | lambda | first month | median h | open water ha | wet floor ha | "
              "last month | median h | open water ha | wet floor ha |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for name, lam, f, l in rows_md:
            print(f"| {name} | {lam:.2f} | {f['label']} | {f['median']:+.3f} | "
                  f"{f['open_water_ha']:.1f} | {f['wet_floor_ha']:.1f} | {l['label']} | "
                  f"{l['median']:+.3f} | {l['open_water_ha']:.1f} | {l['wet_floor_ha']:.1f} |")

    print()
    if failures:
        warn(f"{failures} check(s) failed")
        return 1
    saved("every check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
