#!/usr/bin/env python3
"""
47_hindcast_film.py — the century hindcast film: a free-running SSM from 1930,
calibrated to the well period, through the wet-area model (T-39, D-178)
==========================================================================

WHAT THIS IS

  Today's reserve under the weather of every month since December 1930. The
  cluster state-space model is run forward from a seed, one month at a time, over
  the whole RAF Valley record; the modelled median water table is quantile-mapped
  onto the observed one over the years the dipwells exist; the calibrated level
  goes through D-178's two area curves; and each 10 m cell is lit at the level
  Sentinel-2 was seen to light it. It is a what-if, not a history: the ground,
  the forest and the model are today's.

  Display tier, ON DEMAND ONLY (`run_analysis.py --hindcast-film`). It renders
  over a thousand frames and needs the ffmpeg binary, so it is deliberately not
  part of `--full` or `--with-supplementary`.

WHY A FREE RUN CAN BE CALIBRATED AT ALL

  Martin, 2026-09-17: "surely the better way is to calibrate the runs through the
  SSM runs through the well record period and extend backwards?" The recurrence
  cannot be run backwards — it amplifies error by 1/(1-b3) a month — but a free
  run CAN be calibrated where wells exist and the calibration carried through the
  whole run. Empirical quantile mapping does that: ranks are kept, the mean bias
  goes, and the tails continue on the outer decile's slope.

WHAT IT IS NOT

  Not a flood map. Not a record of what happened. The cells say WHERE the classes
  have appeared at a given level, learned 2016-2026; the model says WHEN. The
  study area is the warren slack floor and nothing outside it is assessed.

INPUTS — all committed; nothing from the private store

  outputs/01_climate.csv .................. P and PET, 1930-12 on, in METRES
  outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv .. beta
  outputs/03_master_data.csv .............. well -> cluster
  outputs/01_wells_reference.csv .......... the reference network
  outputs/01_wells_clean.csv .............. observed monthly levels, for the seed
                                            and for the calibration target
  living/wet_area_model.json .............. the curves, the grid and the cells

  The background is a greyscale Copernicus Sentinel-2 scene of 2021-04-04,
  committed beside the outputs as 47_00_background_2021-04-04.png. Sentinel-2
  data are free and open under the Copernicus licence.

USAGE
  python3 run_analysis.py --hindcast-film
  python3 src/47_hindcast_film.py --no-film      # the CSVs only, no rendering
  python3 src/47_hindcast_film.py --check-phase27 PATH   # recurrence check only
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) - 2026-09-21. The int16 sentinel fallback was
#   the literal 32767; it is config.WET_AREA_CELL_NEVER (pipeline_lint --check literals).
# 1.0.0  # Hollingham (2026) - 2026-09-17. First cut: T-39, the
#   prototype tools/hindcast_calibrate.py 1.0.0 moved into the pipeline with its
#   quantile map, curves, renderer and slide text unchanged in substance. The
#   recurrence now comes from committed inputs (01_climate.csv, not
#   03_regional_averages.csv, which spans only the well years) and from the
#   shared model_utils.simulate_ssm; the cells come from living/wet_area_model.json
#   rather than the private npz; the study-area boundary is drawn and labelled.

import argparse
import base64
import json
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils.paths import (                                     # noqa: E402
    INT_CLIMATE, INT_MASTER_DATA, INT_WELLS_CLEAN, INT_WELLS_REFERENCE,
    LIVING_WET_AREA_MODEL, OUT_03_MECHANISTIC_TABLE,
    DIR_47, OUT_47_LEVEL_MONTHLY, OUT_47_CALIBRATION, OUT_47_QUANTILE_MAP,
    OUT_47_PRESENTATION, OUT_47_FILM, OUT_47_CAVEATS, OUT_47_BACKGROUND,
    out_47_still,
)
from utils.config import (                                    # noqa: E402
    WET_AREA_CELL_NEVER,
    DRAINAGE_DATUM, HINDCAST_SEED_MONTHS, HINDCAST_SPIN_UP_YEARS,
    QMAP_MIN_WELLS, QMAP_MIN_MONTHS, QMAP_TAIL_FRACTION,
    FILM_FPS, FILM_WORDS_PER_MINUTE, FILM_SLIDE_LEAD_S,
    FILM_QUALITY_PRESENTATION, FILM_QUALITY_FULL,
)
from utils.model_utils import simulate_ssm                    # noqa: E402
from utils.console_utils import (                             # noqa: E402
    banner, done, info, phase, progress, result, saved, step, warn,
)

WET_AREA_SCHEMA = "nw-wet-area-1"
COL_WATER, COL_FLOOR, COL_BEYOND = (0.04, 0.43, 0.56), (0.85, 0.68, 0.10), (0.95, 0.72, 0.55)


# ─────────────────────────────────────────────────────────────────────────────
# INPUTS
# ─────────────────────────────────────────────────────────────────────────────
def load_climate() -> pd.DataFrame:
    """The climate record, 1930-12 on, in its native METRES.

    `01_climate.csv`, NOT `03_regional_averages.csv`. That file is indexed on the
    cluster centroids, which exist only for months carrying a dipwell reading, so
    it spans the well years alone and silently drops unmeasured months — the T-33
    / D-171 defect that had phase 27 modelling the winter of 2022-23 with no
    December rainfall. It also carries the same quantities x1000 as P_mm/PET_mm,
    so mixing the two conventions is a factor of a thousand, in silence.
    """
    c = pd.read_csv(INT_CLIMATE, parse_dates=["Date"], float_precision="round_trip")
    c = c.sort_values("Date").reset_index(drop=True)
    c["month"] = c["Date"].dt.to_period("M").astype(str)
    c["climate_flagged"] = ~(c["P_m"].notna() & c["PET"].notna())
    n_bad = int(c["climate_flagged"].sum())
    step(f"climate {c['month'].iloc[0]} to {c['month'].iloc[-1]}, {len(c)} months, metres")
    if n_bad:
        # One month in the record — 1941-06, no rainfall. Phase 27 SKIPS such a
        # month and carries the recurrence over; run naively the NaN eats the
        # 1,017 months after it, measured 2026-09-17.
        warn(f"{n_bad} month(s) with no P or PET — the recurrence carries over them, "
             f"flagged climate_flagged: {', '.join(c.loc[c['climate_flagged'], 'month'])}")
    return c


def load_betas() -> dict:
    """{cluster id: (b1, b2, b3)} in the table's own units — m per mm of a climate
    series in mm, equivalently m per m of one in metres. The two cancel; the
    climate above is metres, so the coefficients are used as written."""
    B = pd.read_csv(OUT_03_MECHANISTIC_TABLE, float_precision="round_trip")
    out = {}
    for _, r in B.iterrows():
        cid = int(str(r["Cluster"]).replace("C", ""))
        b3 = float(r["beta_3_drainage"])
        if b3 < 0:
            warn(f"C{cid}: beta_3 = {b3:.4f} is negative (expected positive under the "
                 f"displacement formulation); magnitude used")
        out[cid] = (float(r["beta_1_recharge"]), float(r["beta_2_atmospheric_draw"]), abs(b3))
    step(f"beta for {len(out)} cluster(s) from {OUT_03_MECHANISTIC_TABLE.name}")
    return out


def load_wells(betas: dict) -> pd.DataFrame:
    """The reference network with its cluster and its seed.

    The seed is the well's mean August-September minimum over its own record
    (config.HINDCAST_SEED_MONTHS) — phase 27's seed, and deliberately NOT
    config.SUMMER_MINIMUM_MONTHS, which is Jun-Sep and means the reports' summer
    minimum. Seeding from the wider window would sit the century run lower than
    phase 27's and make the check against it a comparison of two constructions.
    """
    md = pd.read_csv(INT_MASTER_DATA, float_precision="round_trip")
    cl = {str(r["Name_Original"]): int(r["Cluster"]) for _, r in md.iterrows()}
    ref = pd.read_csv(INT_WELLS_REFERENCE, index_col=0, parse_dates=True,
                      float_precision="round_trip")
    obs = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True,
                      float_precision="round_trip")
    rows = []
    for w in ref.columns:
        cid = cl.get(w)
        if cid is None or cid not in betas or w not in obs.columns:
            continue
        s = obs[w].dropna()
        m = s[s.index.month.isin(HINDCAST_SEED_MONTHS)]
        if m.empty:
            continue
        rows.append({"well": w, "cluster": cid,
                     "seed_m": float(m.groupby(m.index.year).min().mean())})
    W = pd.DataFrame(rows)
    if W.empty:
        raise SystemExit("no reference well carries a seed — check 01_wells_clean.csv")
    step(f"{len(W)} reference well(s) seeded from their "
         f"{'/'.join(str(m) for m in HINDCAST_SEED_MONTHS)} minimum "
         f"(mean seed {W['seed_m'].mean():+.3f} m)")
    return W


def observed_median(wells: pd.DataFrame) -> pd.DataFrame:
    """The observed monthly median across the same wells, with its count — the
    calibration target, and the film's "wells measured" span."""
    obs = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True,
                      float_precision="round_trip")[list(wells["well"])]
    g = pd.DataFrame({"median_level_observed_m": obs.median(axis=1),
                      "n_wells_observed": obs.notna().sum(axis=1)})
    g["month"] = g.index.to_period("M").astype(str)
    return g.reset_index(drop=True)


def load_feed() -> dict:
    """living/wet_area_model.json — the curves, the grid and the cells. The
    private-store CSV and npz are never opened here; the feed is the contract."""
    if not LIVING_WET_AREA_MODEL.exists():
        raise SystemExit(f"no {LIVING_WET_AREA_MODEL}: run "
                         f"`python3 tools/sentinel_wet_floor.py --emit-feed` first")
    feed = json.loads(LIVING_WET_AREA_MODEL.read_text(encoding="utf-8"))
    if feed.get("schema") != WET_AREA_SCHEMA:
        raise SystemExit(f"{LIVING_WET_AREA_MODEL.name} is schema {feed.get('schema')!r}, "
                         f"not {WET_AREA_SCHEMA!r}")
    step(f"wet-area model {feed['source_hash']} ({feed['source']}), generated {feed['generated']}")
    return feed


def decode_cells(feed: dict):
    """(open-water level, dark-total level, floor mask), all (rows, cols), metres.

    int16 centimetres with 32767 for never/not-floor, and the floor mask packed
    with numpy.packbits — the feed's own encoding, stated in `cells.encoding` and
    `cells.floor_encoding`. NOTE the asymmetry D-178 records: `cells.wet_floor` is
    the DARK-TOTAL switching level, so it is drawn as the yellow layer with open
    water overdrawn in blue, and the wet-floor ring is the difference.
    """
    g, c = feed["grid"], feed["cells"]
    rows, cols = int(g["rows"]), int(g["cols"])
    never = int(c.get("never", WET_AREA_CELL_NEVER))   # the feed carries it; config is the fallback, not a retyping

    def lvl(key):
        a = np.frombuffer(base64.b64decode(c[key]), dtype="<i2").astype(np.float64)
        if a.size != rows * cols:
            raise SystemExit(f"cells.{key} is {a.size} values, grid says {rows * cols}")
        a[a == never] = np.inf
        return (a / 100.0).reshape(rows, cols)

    if "floor" not in c:
        raise SystemExit("the feed carries no cells.floor — regenerate it with "
                         "sentinel_wet_floor.py >= 1.10.0 (--emit-feed)")
    floor = np.unpackbits(np.frombuffer(base64.b64decode(c["floor"]), dtype=np.uint8),
                          count=rows * cols).astype(bool).reshape(rows, cols)
    step(f"cells {rows} x {cols} at {g['res']} m, {int(floor.sum())} on the floor "
         f"({float(floor.sum()) * 0.01:.1f} ha study area)")
    return lvl("open_water"), lvl("wet_floor"), floor


# ─────────────────────────────────────────────────────────────────────────────
# THE RECURRENCE
# ─────────────────────────────────────────────────────────────────────────────
def _simulate_across_holes(h0, P, E, ok, b1, b2, b3):
    """The recurrence over a climate record with holes in it.

    A hole takes NO STEP AT ALL: h(t) = h(t-1), and month t+1 continues from that
    same level. Phase 27's rule, and the distinction matters more than it looks.
    Zero-filling P and PET instead still applies the drainage term -b3*(D + h),
    which for C1 is about a quarter of a metre; masking the month afterwards hides
    that one value but leaves every later month on the stepped trajectory. Measured
    2026-09-17 on the first run of this script: whole-run RMSE against phase 27
    0.0147 m with a 0.163 m spike after 1941-06, against 0.0023 m / 0.040 m once
    the step is properly skipped. The 2005-on figure was 0.0003 m either way,
    because sixty-five years of (1 - b3) decay hide it exactly where anyone would
    look for it.

    Every real month still goes through the shared model_utils.simulate_ssm; only
    the segmentation is here.
    """
    n = len(P)
    h = np.empty(n, dtype=float)
    cur, i = float(h0), 0
    while i < n:
        if not ok[i]:
            h[i] = cur                       # skipped; the recurrence carries over
            i += 1
            continue
        j = i
        while j < n and ok[j]:
            j += 1
        seg = simulate_ssm(cur, P[i:j], E[i:j], b1, b2, b3, drainage_datum=DRAINAGE_DATUM)
        h[i:j] = seg
        cur = float(seg[-1])
        i = j
    return h


def run_recurrence(clim: pd.DataFrame, wells: pd.DataFrame, betas: dict) -> pd.DataFrame:
    """Per well, forward from its seed over the whole climate record; the monthly
    level is the MEDIAN across wells, matching phase 27's median_level_modelled_m.

    Seeded once and never re-seeded — phase 27's Mode C. A month with no P or PET
    is skipped and the recurrence carries over, which is phase 27's rule and is
    why `climate_flagged` exists.
    """
    P = clim["P_m"].to_numpy(float)
    E = clim["PET"].to_numpy(float)
    ok = np.isfinite(P) & np.isfinite(E)
    H = np.full((len(clim), len(wells)), np.nan)
    for j, (_, w) in enumerate(wells.iterrows()):
        b1, b2, b3 = betas[int(w["cluster"])]
        H[:, j] = _simulate_across_holes(-abs(w["seed_m"]), P, E, ok, b1, b2, b3)
    out = pd.DataFrame({
        "month": clim["month"],
        "median_level_modelled_m": np.nanmedian(H, axis=1),
        "n_wells_run": int(len(wells)),
        "climate_flagged": clim["climate_flagged"].to_numpy(),
    })
    # Two YEARS from the first month, not two calendar years: the record starts in
    # December, so the calendar reading gave 13 months where the guide slide says
    # "the first two years are the model settling from its starting guess".
    out["spin_up"] = np.arange(len(out)) < 12 * HINDCAST_SPIN_UP_YEARS
    step(f"recurrence over {len(out)} months x {len(wells)} wells; "
         f"first {int(out['spin_up'].sum())} months flagged spin_up")
    return out


def check_against_phase27(level: pd.DataFrame, path: Path) -> None:
    """The spec's pre-build control: this construction against phase 27's own
    from1930 Mode C run. Reported, never used to adjust anything."""
    if not path.exists():
        warn(f"no {path}; the phase 27 control is not run")
        return
    hc = pd.read_csv(path)
    g = hc[hc["mode"] == "C"].set_index("month")["median_level_modelled_m"]
    j = level.set_index("month")[["median_level_modelled_m"]].join(
        g.rename("phase27"), how="inner").dropna()
    if j.empty:
        warn("no overlapping month with the phase 27 run")
        return
    d = j["median_level_modelled_m"] - j["phase27"]
    late = j[j.index >= "2005-01"]
    dl = late["median_level_modelled_m"] - late["phase27"]
    result("phase 27 control",
           f"whole run n {len(j)} RMSE {np.sqrt((d ** 2).mean()):.4f} m "
           f"(max |d| {d.abs().max():.4f}); 2005 on n {len(late)} "
           f"RMSE {np.sqrt((dl ** 2).mean()):.4f} m")


# ─────────────────────────────────────────────────────────────────────────────
# THE CALIBRATION
# ─────────────────────────────────────────────────────────────────────────────
def quantile_map(model, observed):
    """f(x): the free run's level mapped onto the observed distribution.

    Verbatim from the prototype. Ranks are kept, so the ORDER of the century is
    the model's; the mean bias goes; and beyond either end of the fitted range
    the map continues on the outer decile's own slope rather than flattening.
    """
    m, o = np.sort(np.asarray(model, float)), np.sort(np.asarray(observed, float))
    k = max(5, int(len(m) * QMAP_TAIL_FRACTION))
    slo, shi = np.polyfit(m[:k], o[:k], 1)[0], np.polyfit(m[-k:], o[-k:], 1)[0]

    def f(x):
        x = np.asarray(x, float)
        q = np.interp(x, m, o)
        lo, hi = x < m[0], x > m[-1]
        q[lo] = o[0] + slo * (x[lo] - m[0])
        q[hi] = o[-1] + shi * (x[hi] - m[-1])
        return q
    return f, m, o


def calibrate(level: pd.DataFrame) -> tuple:
    """Fit the map on the months with wells, apply it to every month."""
    ok = (level["median_level_observed_m"].notna()
          & (level["n_wells_observed"] >= QMAP_MIN_WELLS))
    if int(ok.sum()) < QMAP_MIN_MONTHS:
        warn(f"{int(ok.sum())} month(s) with >= {QMAP_MIN_WELLS} wells — fewer than "
             f"{QMAP_MIN_MONTHS}; the run is left RAW and said so in 47_02")
        return level["median_level_modelled_m"].to_numpy(float), None, None
    qm, m, o = quantile_map(level.loc[ok, "median_level_modelled_m"],
                            level.loc[ok, "median_level_observed_m"])
    cal = qm(level["median_level_modelled_m"].to_numpy(float))
    d0 = (level.loc[ok, "median_level_modelled_m"] - level.loc[ok, "median_level_observed_m"])
    d1 = (pd.Series(cal, index=level.index)[ok] - level.loc[ok, "median_level_observed_m"])
    wet = level.loc[ok, "median_level_observed_m"] > -0.3
    stats = {
        "n_months": int(ok.sum()),
        "bias_raw": d0.mean(), "bias_mapped": d1.mean(),
        "rmse_raw": float(np.sqrt((d0 ** 2).mean())), "rmse_mapped": float(np.sqrt((d1 ** 2).mean())),
        "wet_end_bias_raw": d0[wet].mean(), "wet_end_bias_mapped": d1[wet].mean(),
        "level_max_raw": float(level["median_level_modelled_m"].max()),
        "level_max_mapped": float(cal.max()),
    }
    step(f"calibrated over {stats['n_months']} months: bias {stats['bias_raw']:+.3f} -> "
         f"{stats['bias_mapped']:+.3f} m; RMSE {stats['rmse_raw']:.3f} -> {stats['rmse_mapped']:.3f}; "
         f"wet-end bias {stats['wet_end_bias_raw']:+.3f} -> {stats['wet_end_bias_mapped']:+.3f}; "
         f"level max {stats['level_max_raw']:+.2f} -> {stats['level_max_mapped']:+.2f}")
    return cal, stats, pd.DataFrame({"model_quantile_m": m, "well_quantile_m": o})


def areas(level: pd.DataFrame, feed: dict, floor_ha: float) -> pd.DataFrame:
    """D-178's two curves on the calibrated level, and on the raw level beside it.

    Capped at the floor's own area: the curves are an exponential fit and have no
    knowledge of how much slack floor exists, so far above the fitted range they
    would otherwise exceed the ground they describe.
    """
    cur = feed["curves"]
    for cls in ("open_water", "wet_floor"):
        a, b = float(cur[cls]["a"]), float(cur[cls]["b"])
        for src, tag in (("median_level_calibrated_m", ""), ("median_level_modelled_m", "_raw_level")):
            level[f"{cls}_ha{tag}"] = np.minimum(a * np.exp(b * level[src].to_numpy(float)), floor_ha)
    level["wet_floor_ha"] = np.minimum(level["wet_floor_ha"], floor_ha - level["open_water_ha"])
    level["wet_floor_ha_raw_level"] = np.minimum(level["wet_floor_ha_raw_level"],
                                                 floor_ha - level["open_water_ha_raw_level"])
    return level


# ─────────────────────────────────────────────────────────────────────────────
# THE WORDS
# ─────────────────────────────────────────────────────────────────────────────
def build_text(feed: dict, floor_ha: float) -> tuple:
    """The caption and the slides, with every figure read from the feed.

    The prototype typed "41 clear winter pictures"; the committed model says 43,
    and D-178's prose says 41 with a dated Note recording the drift. A number the
    CSV carries does not belong in a sentence, so `n` and both sigmas come from
    the feed and move with a refit.
    """
    ow, wf = feed["curves"]["open_water"], feed["curves"]["wet_floor"]
    n = int(ow.get("n", 0))
    s_ow, s_wf = float(ow["sigma_factor"]), float(wf["sigma_factor"])
    rng = feed["fitted_range_m"]
    caption = (
        "Today's reserve under the\nweather of each past month. Not what actually\n"
        "happened: a what-if. The model's water table is\ncorrected to match the wells over 2005–2026.\n\n"
        "Blue: open water.  Yellow: wet floor.\n10 m squares from satellite pictures, 2016–2026.\n"
        "Not a flood map: puddles and margins are too\nsmall to show.\n\n"
        "The outline is the study area: the warren slack\nfloor. Nothing outside it is assessed.\n\n"
        f"Totals in the title are from the corrected water\ntable; open water is right to within a\n"
        f"factor of {s_ow:.1f}, wet floor to about {(s_wf - 1) * 100:.0f} %.")
    caption_beyond = (
        "\n\nTHIS MONTH IS BEYOND THE RECORD.\nThe water table is above the 2021 flood, the\n"
        "wettest ever measured. The totals are the curves\nrun past the end of the data; pale orange is\n"
        "slack floor never seen wet — wetter than\nanything on record, where exactly unknown.")
    before = [
        ("Newborough Warren under a century of weather",
         ["A film of how wet the dune slacks would have been, month by month, from 1930 to 2026 — if "
          "the reserve as it stands today had lived through the weather of each of those years.",
          "Newborough Warren is a sand-dune reserve on Anglesey. Between the dunes lie hundreds of low "
          "hollows called slacks. In a wet winter the water table rises into them: the ground goes "
          "damp, pools appear, and in a very wet spring whole slacks stand under water.",
          "Only the warren is modelled, not the forest. Everything here is about the open dune slacks "
          "of Newborough Warren — the study area outlined on the map. The planted forest beside them "
          "is not part of the model and is not assessed; absence of yellow and blue cells does not "
          "imply an absence of flooding, rather it has not been modelled."],
         "Newborough Warren hydrology study, 2026 · Martin Hollingham"),
        ("How to read the film",
         ["YELLOW is wet floor: saturated ground, or a thin sheet of water hidden in the grass.",
          "BLUE is open water: pools you could see from the air.",
          f"The outline on the map is the study area — {floor_ha:.0f} hectares of slack floor within "
          "the warren. Everything the film says is about the ground inside it. Blank ground outside "
          "the outline was not assessed; it is not a claim that it was dry.",
          "The title gives the total of each across the study area, in hectares (a hectare is a "
          "little larger than a rugby pitch).",
          "The line at the bottom is the water table — how far below or above the ground the "
          "groundwater sits, averaged over the reserve's monitoring wells. The red marker is where "
          "the film has got to. The clock runs at a year a second."], None),
        ("How it was made: three things joined together",
         ["1.  A weather-driven groundwater model. Since 2005 the reserve's dipwells have been read "
          "every month, and from them we learned a simple rule for how the water table rises with "
          "rain and falls with evaporation and drainage. RAF Valley has kept weather records since "
          "1930, so the rule can be run through the whole century, steered by nothing but the "
          "weather. Where the wells exist, the model's water table is corrected to match them, and "
          "that correction is carried back through the years before the wells.",
          f"2.  Satellite pictures. Sentinel-2 has photographed the warren every few days since 2016 "
          f"in 10 m squares. In the near-infrared, water is black and grass is bright, so a wet slack "
          f"floor is a dark patch. Counting the dark squares in {n} clear winter pictures and "
          f"comparing with the water table gives two smooth curves — one for open water, one for wet "
          f"floor.",
          "3.  Where the water goes. Each 10 m square has its own history in those pictures, so we "
          "know the water-table level at which it usually turns dark. The film lights each square "
          "when the model reaches that level. WHERE the colours appear was learned from the "
          "satellite; WHEN is the model."], None),
        ("Please read this before watching",
         ["It is today's warren, not the warren of the time. The rules were learned from 2005–2026 "
          "and the ground is the 2023 survey, with Newborough Forest at its present size. The forest "
          "was only planted between 1947 and 1965, and a forest lowers the water table around it. In "
          "1939 there was no forest. The film answers a what-if — what would the reserve as it is "
          "now have done under that weather — not what actually happened.",
          "The map covers the warren study area only; blank outside it means not assessed, not "
          "dry."], None),
        ("The biggest floods go beyond anything measured",
         [f"The wettest spring on record was 2021. In some months — 1939, 1959, 1961–62 and 2000–01 — "
          f"the model pushes the water table higher than that, above the {rng['max']:+.2f} m the "
          f"curves were fitted to.",
          "No picture has seen the warren like that. So those months are marked BEYOND THE RECORD, "
          "the totals are the curves run past the end of the data, and the rest of the slack floor "
          "turns PALE ORANGE: wetter than anything on record, where exactly we cannot say.",
          "The honest claim for those winters is that they were bigger than 2021, nothing finer."],
         None),
        ("And a little more",
         ["It is not a flood map. The squares are 10 m across; narrow margins, small pools and thin "
          "sheets over grass are invisible at that size — roughly a third of the water in a big "
          "flood. The moment a square lights is known only to within five or ten centimetres of "
          "water table.",
          f"The model's mistakes carry through. Even corrected to the wells, it reproduces the "
          f"measured water table to about twenty centimetres, and it still runs about ten "
          f"centimetres low in the wettest months. A ten-centimetre error changes the open-water "
          f"area by about half, because pools appear suddenly once the water nears the surface. "
          f"Yellow is the steadier colour, good to about {(s_wf - 1) * 100:.0f} %; blue is right to "
          f"within a factor of {s_ow:.1f}. The first two years are the model settling from its "
          f"starting guess.",
          "Winter rules all year. The curves come from November-to-March pictures; summer months "
          "show what the water table would imply, not what a summer photograph would show."], None),
    ]
    after = [
        ("What the film says, cautions attached",
         ["The 1960s were the wet decade, with several times the open water of an average winter in "
          "any other decade.",
          "The winters of 1961–62 and 2000–01 stand out as the two great floods of the century, with "
          "1938–39 and 1958–59 behind them; 2015–16 was the wettest of the satellite era after 2021.",
          "The 1970s and 1990s were the dry decades, with almost no open water in an average winter.",
          "All of it is the model's account of what the weather would do to the reserve as it stands "
          "today."], None),
        ("Credits and sources",
         ["Newborough Warren hydrology study, 2026 — Martin Hollingham.",
          "Weather: RAF Valley monthly record, 1930–2026. Water table: the reserve's dipwell "
          "network, 2005–2026. Imagery: Copernicus Sentinel-2, 2016–2026 (free and open under the "
          "Copernicus licence). Ground: 2023 survey.",
          "Model, code and data: github.com/newbroman/Newborough_Hydrology. The method is recorded "
          "as decision D-178; the full written guide accompanies this film."], None),
    ]
    return caption, caption_beyond, before, after


def write_caveats(caption, caption_beyond, before, after, feed, arrivals=None) -> None:
    """Every string the film shows, in one file, so the wording is lint-visible
    and diffable — a frame is not."""
    DIR_47.mkdir(parents=True, exist_ok=True)
    L = [f"# Frame text — 47_hindcast_film.py {__version__}",
         f"# wet-area model {feed['source_hash']} ({feed['source']})"]
    if arrivals:
        L.append("# the trace's arrival lines — the level at which each class first covers 1 ha "
                 "of the study area: " + ", ".join(
                     f"{k} {('%+.3f m' % v) if v is not None else 'never'}"
                     for k, v in sorted(arrivals.items())))
    L += ["",
         "## CAPTION (every frame)", caption, "",
         "## CAPTION, appended when the month is beyond the fitted range",
         caption_beyond.strip(), ""]
    for name, slides in (("SLIDES BEFORE THE FILM", before), ("SLIDES AFTER THE FILM", after)):
        L += [f"## {name}", ""]
        for title, paras, foot in slides:
            L += [f"### {title}"] + list(paras) + ([f"[footer] {foot}"] if foot else []) + [""]
    OUT_47_CAVEATS.write_text("\n".join(L) + "\n", encoding="utf-8")
    saved(OUT_47_CAVEATS.name)


# ─────────────────────────────────────────────────────────────────────────────
# THE RENDER
# ─────────────────────────────────────────────────────────────────────────────
def first_hectare_levels(cells, hectares: float = 1.0) -> dict:
    """The level at which each class first covers `hectares` of the study area.

    NOT the minimum switching level. One cell is 0.01 ha and invisible at this
    frame size, so a line drawn at the first cell would tell the viewer "yellow
    appears" while the map still looks empty. The level at which a hectare is lit
    is the level at which the colour actually arrives on screen (Martin,
    2026-09-17).

    `open_water` is the blue array directly. `wet_floor` is the RING, so it is the
    dark-total count less the open-water count at the same level — the same
    subtraction the frame draws, not the dark-total array on its own.
    """
    hb, hd, floor = cells
    need = int(round(hectares * 100))          # 10 m cells: 100 to the hectare
    ow = np.sort(hb[floor & np.isfinite(hb)])          # open-water switching levels
    dk = np.sort(hd[floor & np.isfinite(hd)])          # dark-total switching levels
    out = {"open_water": float(ow[need - 1]) if ow.size >= need else None}
    # The ring count at a level h is (dark <= h) - (open <= h). The count can only
    # change at a dark level, so evaluate it at each of those: the open-water count
    # there is a binary search, and the dark count is just the position in the
    # sorted array. Exact, and O(n log n) rather than a scan of every pair.
    if dk.size:
        ring_n = np.arange(1, dk.size + 1) - np.searchsorted(ow, dk, side="right")
        hit = np.flatnonzero(ring_n >= need)
        out["wet_floor"] = float(dk[hit[0]]) if hit.size else None
    else:
        out["wet_floor"] = None
    for k, v in out.items():
        if v is None:
            warn(f"no level reaches {hectares:.0f} ha of {k} anywhere in the record")
        else:
            step(f"{k}: first {hectares:.0f} ha at {v:+.3f} m")
    return out


def _background(shape):
    """The greyscale Sentinel-2 scene behind the cells, or a flat grey."""
    from PIL import Image                                     # noqa: PLC0415
    if OUT_47_BACKGROUND.exists():
        base = np.array(Image.open(OUT_47_BACKGROUND).convert("L")).astype(float) / 255.0
        if base.shape != shape:
            warn(f"{OUT_47_BACKGROUND.name} is {base.shape}, the grid is {shape}; flat grey used")
            base = np.full(shape, 0.6)
    else:
        warn(f"no {OUT_47_BACKGROUND.name}; flat grey behind the cells")
        base = np.full(shape, 0.6)
    return np.stack([base * 0.55 + 0.25] * 3, -1)


def render(level, cells, feed, floor_ha, text, arrivals, presentation, still_month=None):
    """The film. One frame a month, plus the guide slides on the presentation cut.

    Returns the still's frame when `still_month` is given, so the PNG and the film
    are the same render rather than two that might drift.
    """
    import imageio                                            # noqa: PLC0415
    import matplotlib                                         # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                           # noqa: PLC0415
    from PIL import Image                                     # noqa: PLC0415

    hb, hd, floor = cells
    caption, caption_beyond, before, after = text
    hmax = float(feed["fitted_range_m"]["max"])
    t = pd.PeriodIndex(level["month"], freq="M").to_timestamp()
    lvl = level["median_level_calibrated_m"].to_numpy(float)
    aw = level["open_water_ha"].to_numpy(float)
    af = level["wet_floor_ha"].to_numpy(float)
    rgb = _background(floor.shape)
    still = {}

    def even(a):
        return a[:a.shape[0] // 2 * 2, :a.shape[1] // 2 * 2].copy()

    def slide(title_, paras, foot=None):
        words = len(title_.split()) + sum(len(p.split()) for p in paras)
        seconds = FILM_SLIDE_LEAD_S + words / (FILM_WORDS_PER_MINUTE / 60.0)
        fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
        fig.patch.set_facecolor("#f7f5f0")
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); y = 0.91
        for line in textwrap.wrap(title_, 52):
            ax.text(0.06, y, line, fontsize=24, weight="bold", va="top", color="#1f1f1f")
            y -= 0.075
        y -= 0.03
        nl = sum(len(textwrap.wrap(p, 95)) for p in paras) + len(paras)
        fs = 15 if nl <= 11 else (13.5 if nl <= 14 else 12.5)
        lh = fs * 0.0034
        ww = int(1400 / fs)
        for p in paras:
            for line in textwrap.wrap(p, ww):
                ax.text(0.06, y, line, fontsize=fs, va="top", color="#2a2a2a")
                y -= lh
            y -= lh * 0.6
        if foot:
            ax.text(0.06, 0.05, foot, fontsize=11, color="#666")
        fig.canvas.draw()
        a = even(np.asarray(fig.canvas.buffer_rgba())[..., :3])
        plt.close(fig)
        return [a] * int(round(seconds * FILM_FPS))

    frames = []
    if presentation:
        for title_, paras, foot in before:
            frames += slide(title_, paras, foot)

    fig = plt.figure(figsize=(12.8, 7.2), dpi=100); fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.02, 0.30, 0.62, 0.62])
    ax2 = fig.add_axes([0.07, 0.09, 0.90, 0.16])
    axt = fig.add_axes([0.66, 0.30, 0.33, 0.62]); axt.set_axis_off()
    im = ax.imshow(rgb); ax.set_axis_off()
    # The study area, drawn once: the boundary of the floor mask itself. Without
    # it an unassessed cell and a dry cell are the same blank pixel.
    ax.contour(floor.astype(float), levels=[0.5], colors=["#1f1f1f"],
               linewidths=0.7, linestyles="dashed")
    title = ax.set_title("", fontsize=12, loc="left")
    obs = level["median_level_observed_m"]
    wells_from = t[obs.notna().to_numpy()].min() if obs.notna().any() else t.max()
    ax2.fill_between(t, -1.4, 0.4, where=t < wells_from, color="#eeeeee", zorder=0)
    ax2.plot(t, lvl, color="black", lw=0.6)
    ax2.axhline(0, color="grey", lw=0.6, ls=":")
    # Where each colour arrives. Drawn in its own colour so the line and the cells
    # it describes cannot be mixed up, and labelled, because an unlabelled
    # horizontal line on a hydrograph reads as a threshold someone chose.
    for cls, colour, label in (("wet_floor", COL_FLOOR, "wet floor appears"),
                               ("open_water", COL_WATER, "open water appears")):
        hv = arrivals.get(cls)
        if hv is None:
            continue
        ax2.axhline(hv, color=colour, lw=0.9, ls="-", alpha=0.9)
        ax2.text(t[len(t) - 1], hv, f"  {label} ({hv:+.2f} m)", fontsize=6.5,
                 color=colour, va="center", ha="left", clip_on=False)
    ax2.axhline(hmax, color="#0b6e8f", lw=0.6, ls="--")
    ax2.fill_between(t, hmax, 0.4, color="#e8734a", alpha=0.10)
    ax2.set_ylim(-1.4, 0.4)
    ax2.set_ylabel("water table, m (0 = ground)", fontsize=8)
    ax2.tick_params(labelsize=8)
    ax2.text(t[12], 0.26, "before the wells: model only, corrected to the well years",
             fontsize=7, color="#555")
    ax2.text(wells_from + pd.Timedelta(days=300), 0.26, "wells measured", fontsize=7, color="#555")
    ax2.text(t[len(t) // 3], hmax + 0.05, "above the 2021 flood: beyond anything measured",
             fontsize=6.5, color="#b5532a")
    marker = ax2.axvline(t[0], color="#c0504d", lw=1.4)
    txt = axt.text(0.0, 1.0, caption, fontsize=9.6, va="top", ha="left", linespacing=1.4)

    def frame(i):
        h = lvl[i]
        hc = min(h, hmax)
        img = rgb.copy()
        y, b = floor & (hd <= hc), floor & (hb <= hc)
        over = h > hmax
        if over:
            img[floor & ~y] = COL_BEYOND
        img[y] = COL_FLOOR
        img[b] = COL_WATER
        im.set_data(img)
        marker.set_xdata([t[i], t[i]])
        txt.set_text(caption + (caption_beyond if over else ""))
        txt.set_color("#7a2e0e" if over else "#222")
        title.set_text(f"{t[i].strftime('%B %Y')}   water table {h:+.2f} m   "
                       f"open water {aw[i]:.0f} ha   wet floor {af[i]:.0f} ha   "
                       f"(study area {floor_ha:.0f} ha)"
                       + ("   BEYOND THE RECORD" if over else ""))
        fig.canvas.draw()
        return even(np.asarray(fig.canvas.buffer_rgba())[..., :3])

    frames += [frame(0)] * FILM_FPS
    n = len(level)
    import time as _time                                      # noqa: PLC0415
    t0 = _time.time()
    for i in range(n):
        a = frame(i)
        frames.append(a)
        if still_month is not None and level["month"].iloc[i] == still_month:
            still[still_month] = a
        if i % 25 == 0 or i == n - 1:
            progress(i + 1, n, t[i].strftime("%Y-%m"), started=t0)
    print(flush=True)
    frames += [frames[-1]] * (2 * FILM_FPS)
    plt.close(fig)
    if presentation:
        for title_, paras, foot in after:
            frames += slide(title_, paras, foot)

    target = OUT_47_PRESENTATION if presentation else OUT_47_FILM
    quality = FILM_QUALITY_PRESENTATION if presentation else FILM_QUALITY_FULL
    imageio.mimwrite(target, frames, fps=FILM_FPS, codec="libx264", quality=quality,
                     macro_block_size=None)
    saved(target.name, f"{len(frames) / FILM_FPS:.0f} s, {len(frames)} frames, quality {quality}")
    if still:
        m, a = next(iter(still.items()))
        Image.fromarray(a).save(out_47_still(m))
        saved(out_47_still(m).name)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main(no_film: bool = False, check_phase27: str | None = None) -> int:
    banner("47", "The century hindcast film", version=__version__)
    phase(1, "Committed inputs")
    clim = load_climate()
    betas = load_betas()
    wells = load_wells(betas)
    feed = load_feed()

    phase(2, "The recurrence, 1930 on — Mode C, seeded once")
    level = run_recurrence(clim, wells, betas)
    if check_phase27:
        check_against_phase27(level, Path(check_phase27))

    phase(3, "Calibrating to the well period")
    level = level.merge(observed_median(wells), on="month", how="left")
    cal, stats, qmap = calibrate(level)
    level["median_level_calibrated_m"] = cal
    level["above_fitted_range"] = level["median_level_calibrated_m"] > float(
        feed["fitted_range_m"]["max"])

    phase(4, "Through the two curves")
    ow, wf, floor = decode_cells(feed)
    floor_ha = float(floor.sum()) * 0.01
    level = areas(level, feed, floor_ha)
    DIR_47.mkdir(parents=True, exist_ok=True)
    keep = ["month", "median_level_modelled_m", "median_level_calibrated_m", "n_wells_run",
            "median_level_observed_m", "n_wells_observed", "above_fitted_range", "spin_up",
            "climate_flagged", "open_water_ha", "wet_floor_ha",
            "open_water_ha_raw_level", "wet_floor_ha_raw_level"]
    level[keep].round(3).to_csv(OUT_47_LEVEL_MONTHLY, index=False)
    saved(OUT_47_LEVEL_MONTHLY.name)
    if stats is not None:
        pd.DataFrame([stats]).round(3).to_csv(OUT_47_CALIBRATION, index=False)
        saved(OUT_47_CALIBRATION.name)
        qmap.round(3).to_csv(OUT_47_QUANTILE_MAP, index=False)
        saved(OUT_47_QUANTILE_MAP.name)
    n_over = int(level["above_fitted_range"].sum())
    wettest = level.loc[level["open_water_ha"].idxmax(), "month"]
    result("beyond the fitted range", f"{n_over} of {len(level)} month(s); wettest {wettest} "
                                     f"at {level['open_water_ha'].max():.0f} ha open water")

    step("The level at which each colour arrives on the map")
    arrivals = first_hectare_levels((ow, wf, floor))

    phase(5, "The words")
    text = build_text(feed, floor_ha)
    write_caveats(*text, feed, arrivals)

    if no_film:
        info("--no-film: the CSVs and the text only")
        done("45")
        return 0

    phase(6, "Rendering — the presentation cut (tracked) and the bare cut")
    try:
        import imageio_ffmpeg                                 # noqa: PLC0415,F401
    except ImportError:
        warn("imageio-ffmpeg is not installed, so no MP4 can be written. "
             "`pip install imageio-ffmpeg` in the project venv; see MACHINE_SETUP.md. "
             "There is no GIF fallback here — the tracked artefact is an MP4.")
        return 1
    rc = render(level, (ow, wf, floor), feed, floor_ha, text, arrivals, presentation=True,
                still_month=wettest)
    rc |= render(level, (ow, wf, floor), feed, floor_ha, text, arrivals, presentation=False)
    done("45")
    return rc


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="The century hindcast film (T-39, D-178)")
    ap.add_argument("--no-film", action="store_true",
                    help="write the CSVs and the frame text, render nothing")
    ap.add_argument("--check-phase27", metavar="CSV", default=None,
                    help="also report this run against a phase 27 *_hindcast_monthly.csv")
    args = ap.parse_args()
    sys.exit(main(no_film=args.no_film, check_phase27=args.check_phase27))
