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

  The presentation cut's slides also show report figures (read from outputs/, their
  numbers from tools/figure_map.csv), the 45_01/45_02 axes sidecars (callout
  geometry), outputs/45_wet_area/45_02_ssm_through_nir_curves.csv (the check's
  months), and data/sentinel/thumbs/ with two_class_series.csv (true-colour
  thumbnails and their scenes' levels and areas).

  The background is a greyscale Copernicus Sentinel-2 scene of 2021-04-04,
  committed beside the outputs as 47_00_background_2021-04-04.png. Sentinel-2
  data are free and open under the Copernicus licence.

USAGE
  python3 run_analysis.py --hindcast-film
  python3 src/47_hindcast_film.py --no-film      # the CSVs only, no rendering
  python3 src/47_hindcast_film.py --check-phase27 PATH   # recurrence check only
"""
from __future__ import annotations

__version__ = "1.4.0"  # Hollingham (2026) - 2026-09-26. Review of the 1.3.0 presentation
#   (Martin: "Review the film and how would you improve it. Implement the changes"),
#   recorded in NRG_spec_script47_v1_4_2026-09-26:
#   - the hydrograph is legible at 720p: taller (ax2 [0.07, 0.07, 0.78, 0.18]), fonts
#     9-10 pt, x-limits the record itself; the arrival-line labels, which ran off the
#     right edge, sit in a margin beside the axes; the era labels ("model only" / "wells
#     measured") head the axes instead of crowding the 2021 band, and "beyond anything
#     measured" sits inside that band;
#   - during the opening clip the hydrograph zooms to the clip's years, era labels
#     hidden, and is restored for the film;
#   - a "What you hear" slide, just before "Please read this before watching", says what
#     each voice of the Warren track follows (only when FILM_SOUND_TRACK is "warren"), and
#     Credits name the sound as synthesised by this script;
#   - Martin, same day ("lets include your proposed changes"): "And a little more" moves
#     after the film, behind "What the film says", so the film starts sooner; the
#     one-paragraph "How it was made" slide is folded into "How to read the film";
#   - Martin, same day, colours: the readout's open-water and wet-floor values are in the
#     map's colours (the yellow darkened, FILM_COL_FLOOR_TEXT); in the caption "Blue: open
#     water.", "Yellow: wet floor." and "pale orange" are in theirs and the beyond-the-
#     record line is bold; the water-table trace is blue above the open-water line and
#     ochre above the wet-floor line; slide titles are in FILM_COL_TITLE;
#   - Martin, same day, sound: the surf's stereo place follows the east-west centre of the
#     wetted cells (FILM_WASH_PAN_WIDTH); "What you hear" says so. A rain voice was tried
#     and withdrawn at Martin's request ("replace the patter with the original wash").
# v1.3.0  # Hollingham (2026) - 2026-09-25. Per the signed-off spec
#   NRG_spec_script47_v1_3_2026-09-25 (Martin: "a short title page, and a clip from
#   2015-2026 shortly after, then the full presentation with the new sound track"):
#   - the presentation cut opens with a short title page (FILM_OPEN_TITLE_S) and the
#     monthly frames from FILM_OPEN_CLIP_START to the last month, labelled
#     FILM_OPEN_CLIP_LABEL, before the title-and-contents page; two chapter markers added;
#   - the "Warren" sound track, sound_track_warren(): the ambient pad runs throughout and
#     opens with the water table (tremolo beyond the record); one note each January whose
#     pitch and loudness follow that year's largest open water; a wash, largely pitched
#     through resonators on the chord, whose loudness follows the wetted area; and a held
#     chord voice above each line drawn on the hydrograph (wet floor, open water, 2021).
#   - FILM_SOUND_TRACK selects it ("warren") or the 1.1.0 track ("classic"), which is kept.
# v1.2.0  # Hollingham (2026) - 2026-09-25. Presentation cut, per Martin's spec
#   NRG_spec_script47_v1_2_2026-09-25 (signed off the same day):
#   - a title page with a contents list and start times, which are also written into
#     the mp4 as chapter markers;
#   - "How it was made" split into steps. Step 1 sets report Figure 4 (the climate
#     record) beside Figure 16b (the 100-month CEH6 simulation, now saved on its own by
#     Script 08 1.6.0) and explains the link. The correction to the wells gets its own
#     slide;
#   - Figures 49 and 50 have four true-colour Sentinel-2 thumbnails beneath them
#     (tools/sentinel_thumbs.py), with callouts to each picture's points on Figure 49
#     and its month (peak or trough) on Figure 50, placed through the axes sidecars
#     that Script 45 1.5.0 writes;
#   - a new slide sets the driest and wettest thumbnail beside the film's map of the
#     same month, labelled as an illustration rather than a test. Copernicus credits
#     are on the slides and in "Please read this" and "Credits";
#   - slides are shaded (FILM_SLIDE_TOP to FILM_SLIDE_FOOT), and all slide text is
#     measured and fitted rather than wrapped by a character count;
#   - on the monthly frames the readout is fixed fields at a size fitted once, so
#     nothing moves between frames, and the caption is sized once;
#   - the dry end of the tone is an octave deeper (config FILM_TONE_F_LOW_HZ), with a
#     2nd harmonic (FILM_TONE_HARMONIC_GAIN).
#   done() now names step 47 (it said 45).
#   Same day, Martin's review of the preview: slide 1's right-hand chart is this film's
#   own weather-only run against the median of the reference wells (47_06; the CEH6
#   panel and the TLM are gone, and Script 08 is left at 1.5.1); the calibration slides'
#   thumbnails are the near-infrared band the method reads, each scaled to its own floor
#   median; slide 3's Figure 51 is now stacked in the report too (Script 45); and the
#   readout's year sits at
#   a fixed place. 47_02_calibration.csv gains r2_raw (additive). The frames are
#   streamed to the encoder instead of held in memory (the century took over 6 GB).
# 1.1.0  # Hollingham (2026) - 2026-09-25. The presentation cut gains (Martin,
#   2026-09-25) the three wet-area figures of report §4.8.5 among its opening slides,
#   each introduced in the words of the "How it was made" slide it illustrates, their
#   report numbers read from tools/figure_map.csv; and a sound track: a slow ambient
#   pad under the text and figure slides, and over the monthly frames a tone whose
#   pitch follows the calibrated water table, a second voice whose loudness follows
#   the flooded area, and a tremolo on the months beyond the record. Synthesised here
#   (numpy), muxed with the imageio-ffmpeg binary. The bare cut stays silent and
#   slide-free. No CSV output changes.
# 1.0.1  # Hollingham (2026) - 2026-09-21. The int16 sentinel fallback was
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
    out_47_still, FIGURE_MAP,
    OUT_45_MODEL_FIG, OUT_45_SSM_CURVES_FIG, OUT_45_SWITCHING_LEVELS_MAP,
    OUT_45_MODEL_AXES, OUT_45_SSM_CURVES_AXES, OUT_45_SSM_CURVES,
    OUT_00_CLIMATE_TIMESERIES_SHORT, OUT_47_FREE_RUN_FIG,
    SENTINEL_THUMBS_DIR, SENTINEL_THUMBS_MANIFEST, SENTINEL_TWO_CLASS_SERIES,
)
from utils.config import (                                    # noqa: E402
    WET_AREA_CELL_NEVER,
    DRAINAGE_DATUM, HINDCAST_SEED_MONTHS, HINDCAST_SPIN_UP_YEARS,
    QMAP_MIN_WELLS, QMAP_MIN_MONTHS, QMAP_TAIL_FRACTION,
    FILM_FPS, FILM_WORDS_PER_MINUTE, FILM_SLIDE_LEAD_S,
    FILM_QUALITY_PRESENTATION, FILM_QUALITY_FULL, FILM_FIGURE_VIEW_S,
    FILM_AUDIO_RATE_HZ, FILM_AUDIO_FADE_S, FILM_AMBIENT_ROOT_HZ, FILM_AMBIENT_GAIN,
    FILM_TONE_F_LOW_HZ, FILM_TONE_F_HIGH_HZ, FILM_TONE_GAIN, FILM_FLOOD_VOICE_GAIN,
    FILM_TREMOLO_HZ, FILM_TREMOLO_DEPTH, FILM_AUDIO_BITRATE,
    FILM_INDEX_VIEW_S, FILM_SLIDE_TOP, FILM_SLIDE_FOOT, FILM_TONE_HARMONIC_GAIN,
    FILM_SOUND_TRACK, FILM_OPEN_TITLE_S, FILM_OPEN_CLIP_START, FILM_OPEN_CLIP_LABEL,
    FILM_NOTE_F_LOW_HZ, FILM_NOTE_F_HIGH_HZ, FILM_NOTE_SCALE, FILM_NOTE_FLOOR, FILM_NOTE_DECAY_S,
    FILM_WASH_HARMONIC, FILM_WASH_SEMITONES, FILM_WASH_BANDWIDTH_HZ, FILM_WASH_SURGE_S,
    FILM_WASH_FLOOR_PCT, FILM_CHORD_SEMITONES, FILM_CHORD_RELEASE_S,
    FILM_MIX_PAD, FILM_MIX_NOTE, FILM_MIX_WASH, FILM_MIX_CHORD,
    FILM_COL_FLOOR_TEXT, FILM_COL_TITLE, FILM_WASH_PAN_WIDTH,
)
from utils.model_utils import simulate_ssm                    # noqa: E402
from utils.console_utils import (                             # noqa: E402
    banner, done, info, phase, progress, result, saved, step, warn,
)

WET_AREA_SCHEMA = "nw-wet-area-1"
COL_WATER, COL_FLOOR, COL_BEYOND = (0.04, 0.43, 0.56), (0.85, 0.68, 0.10), (0.95, 0.72, 0.55)
# The hydrograph's y-axis (m, 0 = ground). The tone's pitch spans the same axis, so the
# pitch and the trace the viewer is watching move together.
TRACE_LO_M, TRACE_HI_M = -1.4, 0.4

# Layout of the 1280 x 720 frame (rendering decisions, not results).
FRAME_W, FRAME_H, FRAME_DPI = 1280, 720, 100
LINE_EM, PARA_GAP = 1.42, 0.55            # line height (em) and paragraph gap (lines)
TEXT_SIZES = (13.0, 12.5, 12.0, 11.5, 11.0, 10.5, 10.0)          # figure-slide text, pt
TEXT_SIZES_WIDE = (16.0, 15.0, 14.0, 13.5, 13.0, 12.5, 12.0, 11.5)  # text-only slides, pt
TITLE_PT_MAX = 24.0
TITLE_SHADE = 1.8                          # the title page's shading, relative to a slide
READOUT_X0, READOUT_X1, READOUT_Y = 0.02, 0.98, 0.945
READOUT_PT_MAX, READOUT_GAP = 30.0, "     "
INDEX_ENTRY_S = 0.6                        # seconds of the title page per contents entry
CAPTION_PT_MAX = 13.0
FRAME_EDGE, CALLOUT = "#cfc8b8", "#b03a2e"
THUMB_STRETCH_PCT, THUMB_GAMMA = (2, 98), 0.8     # one stretch for every true-colour thumbnail
THUMB_NIR_TOP = 1.6                       # NIR thumbnails show 0 .. this x the scene's floor median
CHECK_EXTREMUM_HALF_WINDOW = 3            # months either side: a peak/trough is the max/min in it
FILM_TITLE = "Newborough Warren under a century of weather"
FILM_SUBTITLE = "Today's reserve under the weather of every month since 1930: a what-if, not a history"
FILM_BYLINE = "Newborough Warren hydrology study, 2026 · Martin Hollingham"


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
        "r2_raw": float(np.corrcoef(level.loc[ok, "median_level_modelled_m"],
                                    level.loc[ok, "median_level_observed_m"])[0, 1] ** 2),
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
def report_figure(source: Path) -> tuple:
    """(figure number, section) of a report figure, read from tools/figure_map.csv by
    its source image — never typed, since the report renumbers. (None, None) when the
    map is absent or does not carry the image."""
    import csv                                                # noqa: PLC0415
    if not FIGURE_MAP.exists():
        warn(f"{FIGURE_MAP.name} not found; figure slides carry no report number")
        return None, None
    with open(FIGURE_MAP, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if Path(r.get("source", "")).name == source.name:
                return r.get("number"), r.get("section")
    warn(f"{source.name} is not in {FIGURE_MAP.name}; its slide carries no report number")
    return None, None


def _foot(*sources) -> str:
    """'Report Figure 49, section 4.8.5', or 'Report Figures 4 (section 4.1.1) and 16b
    (section 4.4)' — each source a Path or (Path, panel suffix)."""
    parts = []
    for s in sources:
        src, panel = (s if isinstance(s, tuple) else (s, ""))
        num, sec = report_figure(src)
        if num:
            parts.append((f"{num}{panel}", sec))
    if not parts:
        return "Report figure"
    if len(parts) == 1:
        num, sec = parts[0]
        return f"Report Figure {num}" + (f", section {sec}" if sec else "")
    return "Report Figures " + " and ".join(
        f"{num}" + (f" (section {sec})" if sec else "") for num, sec in parts)


def load_thumbs(floor: np.ndarray | None = None) -> list:
    """The thumbnails (tools/sentinel_thumbs.py), driest to wettest, each with its
    scene's level and class areas from the committed scene series.

    True colour ("rgb", the comparison slide): one stretch for all of them, the 2nd to
    98th percentile of every pixel, so a darker picture is a wetter warren.
    Near-infrared ("nir", the calibration slides): each scene divided by its own median
    over the slack floor and shown on 0 .. THUMB_NIR_TOP x that median — the way the
    method reads it (open water is B8 <= NIR_BLACK_RATIO x the floor median), so the
    same grey means the same class in every picture. The stored PNGs are unstretched;
    both stretches are rendering decisions."""
    import hashlib                                            # noqa: PLC0415
    from PIL import Image                                     # noqa: PLC0415
    if not SENTINEL_THUMBS_MANIFEST.exists():
        warn(f"no {SENTINEL_THUMBS_MANIFEST.name}: the calibration slides carry no satellite "
             f"thumbnails (tools/sentinel_thumbs.py writes them)")
        return []
    M = pd.read_csv(SENTINEL_THUMBS_MANIFEST, comment="#")
    S = pd.read_csv(SENTINEL_TWO_CLASS_SERIES, float_precision="round_trip")
    M = M.merge(S[["date", "open_water_ha", "wet_floor_ha"]], on="date", how="left")
    out, arrs = [], []
    for r in M.itertuples(index=False):
        files = [(SENTINEL_THUMBS_DIR / r.file, r.sha256)]
        if "nir_file" in M.columns:
            files.append((SENTINEL_THUMBS_DIR / r.nir_file, r.nir_sha256))
        bad = [p.name for p, h in files
               if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h]
        if bad:
            warn(f"{', '.join(bad)} missing or not matching the manifest hash; scene left out")
            continue
        arrs.append(np.asarray(Image.open(files[0][0]).convert("RGB")).astype(float))
        d = dict(date=pd.Timestamp(r.date), month=str(r.date)[:7], h=float(r.h_scene),
                 ow=float(r.open_water_ha), wf=float(r.wet_floor_ha))
        if len(files) > 1:
            b8 = np.asarray(Image.open(files[1][0])).astype(float)
            ref = b8[floor] if floor is not None and floor.shape == b8.shape else b8[b8 > 0]
            g = np.clip(b8 / max(float(np.median(ref)), 1e-9) / THUMB_NIR_TOP, 0, 1)
            d["nir"] = np.repeat(g[..., None], 3, axis=-1)
        out.append(d)
    if not out:
        return []
    lo, hi = np.percentile(np.stack(arrs), THUMB_STRETCH_PCT)
    for d, a in zip(out, arrs):
        d["rgb"] = np.clip((a - lo) / max(hi - lo, 1e-9), 0, 1) ** THUMB_GAMMA
        d.setdefault("nir", d["rgb"])
    step(f"{len(out)} satellite thumbnail(s): " + ", ".join(d["month"] for d in out))
    return out


def plot_free_run(level: pd.DataFrame, stats: dict | None) -> None:
    """Slide 1's chart (Martin, 2026-09-25: "the average water level of the warren,
    rather than CEH6, and the TLM dropped"): the median of the reference dipwells
    against the model's own water table over the well years, the model having run on
    the weather alone since 1930 with nothing to correct it. Before the quantile map,
    so the bias the next slide removes is visible."""
    import matplotlib                                         # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                           # noqa: PLC0415
    ok = (level["median_level_observed_m"].notna()
          & (level["n_wells_observed"] >= QMAP_MIN_WELLS)).to_numpy()
    if not ok.any():
        warn("no well months to set the free run against; slide 1 chart not drawn")
        return
    t = pd.PeriodIndex(level["month"], freq="M").to_timestamp()
    span = (t >= t[ok].min()) & (t <= t[ok].max())
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.plot(t[span], level.loc[span, "median_level_modelled_m"], color=COL_WATER, lw=1.6,
            label="the model: weather only, running since 1930"
            + (f" (R² {stats['r2_raw']:.2f}, " + _minus(f"{stats['bias_raw'] * 100:+.0f}")
               + " cm on average)"
               if stats else ""))
    obs = level["median_level_observed_m"].where(ok)
    ax.plot(t[span], obs[span], color="black", lw=1.6,
            label=f"the dipwells: median of the reference network (months with "
                  f"{QMAP_MIN_WELLS}+ wells)")
    ax.axhline(0, color="grey", lw=0.6, ls=":")
    ax.set_ylabel("water table, m (0 = ground)")
    ax.set_title("The warren's water table: the model against the wells", fontsize=12,
                 weight="bold", loc="left")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, loc="lower left", framealpha=0.9)
    fig.tight_layout()
    DIR_47.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_47_FREE_RUN_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_47_FREE_RUN_FIG.name)


def _minus(s: str) -> str:
    return s.replace("-", "−")


def _thumb_label(d: dict) -> str:
    lvl = _minus(f"{d['h']:+.2f}")
    return d["date"].strftime("%d %b %Y").lstrip("0") + f" · wells {lvl} m"


def _check_targets(thumbs: list) -> list:
    """Each thumbnail's month on Figure 50's upper panel (Mode R), and whether that month
    is a peak or a trough of the modelled area. [] when the curves CSV is absent."""
    import matplotlib.dates as mdates                         # noqa: PLC0415
    if not OUT_45_SSM_CURVES.exists():
        warn(f"no {OUT_45_SSM_CURVES.name}: the check slide's callouts are left out")
        return []
    C = pd.read_csv(OUT_45_SSM_CURVES, float_precision="round_trip")
    g = C[C["mode"] == "R"].reset_index(drop=True)
    tot = (g["open_water_ha_modelled"] + g["wet_floor_ha_modelled"]).to_numpy(float)
    months = g["month"].astype(str).str[:7].tolist()
    hw = CHECK_EXTREMUM_HALF_WINDOW
    ext = []                  # (month index, "peak"/"trough"): the max/min of its window
    for j in range(len(tot)):
        w = tot[max(0, j - hw): j + hw + 1]
        if tot[j] >= w.max():
            ext.append((j, "peak"))
        elif tot[j] <= w.min():
            ext.append((j, "trough"))
    out = []
    for d in thumbs:
        if d["month"] not in months:
            out.append(None)
            continue
        i = months.index(d["month"])
        j, kind = min(ext, key=lambda e: abs(e[0] - i))
        when = pd.Timestamp(months[j] + "-01").strftime("%b %Y")
        rel = (f"the {kind}" if j == i else
               f"{abs(i - j)} mo {'after' if i > j else 'before'} the {when} {kind}")
        x = mdates.date2num(pd.Timestamp(d["month"] + "-01"))
        out.append(dict(points=[(x, float(tot[i]))],
                        label=f"{d['date'].strftime('%b %Y')}\n{rel}"))
    return out


def method_slides(n: int, rng: dict, thumbs: list, stats: dict | None = None) -> list:
    """'How it was made', step by step, each step beside the report figures that
    calibrate or test it. (title, paragraphs, footer, extra) — extra None for a text
    slide, else a dict naming the layout. Numbers from the feed; figure numbers from
    tools/figure_map.csv."""
    lo_s, hi_s = (_minus(f"{float(rng[k]):+.2f}") for k in ("min", "max"))
    cop = "Contains modified Copernicus Sentinel data"
    out = []

    if OUT_00_CLIMATE_TIMESERIES_SHORT.exists() and OUT_47_FREE_RUN_FIG.exists():
        n4, _ = report_figure(OUT_00_CLIMATE_TIMESERIES_SHORT)
        f4 = f"Figure {n4}" if n4 else "The climate figure"
        low = (f", on average {abs(stats['bias_raw']) * 100:.0f} cm "
               f"{'low' if stats['bias_raw'] < 0 else 'high'}" if stats else "")
        out.append((
            "1.  A weather-driven groundwater model",
            [f"Since 2005 the reserve's dipwells have been read every month. {f4} (left) sets them "
             f"beside the weather. Through runs of months when more rain falls than evaporates the "
             f"water table climbs, and through dry runs it falls: the running balance of rain minus "
             f"evaporation (panel c) and the network's water level (panel d) move together.",
             "From that link the study learned a simple monthly rule: the water table rises with "
             "the month's rain, falls with its evaporation, and drains back in proportion to how "
             "high it stands.",
             f"The chart above is the test this film depends on. The model has run on nothing but "
             f"RAF Valley's weather since 1930, with no well reading to correct it. Over the years "
             f"the wells have been read it follows the warren's wet and dry years{low}: the bias "
             f"the next slide removes."],
            _foot(OUT_00_CLIMATE_TIMESERIES_SHORT) + " · the model against the wells: this film's "
            "own run",
            dict(kind="model", left=OUT_00_CLIMATE_TIMESERIES_SHORT, right=OUT_47_FREE_RUN_FIG)))
    else:
        warn("the climate figure or the free-run chart is missing; slide 1 is text only")
    out.append((
        "Correcting the model to the wells",
        ["Run freely for a century, the model drifts: it has no wells to hold it. So it is "
         "corrected where the wells exist. Over 2005–2026 the model's months are ranked against "
         "the measured months, and each modelled level is replaced by the measured level of the "
         "same rank.",
         "The order of wet and dry months is the model's own; the correction only removes its "
         "bias. That same correction is then carried back through the years before the wells."],
        None, None))

    specs = (
        (OUT_45_MODEL_FIG, "2.  Satellite pictures: the first calibration",
         [f"Sentinel-2 has photographed the warren every few days since 2016, in 10 m squares. In "
          f"the near-infrared, water is black and grass is bright, so a wet slack floor shows as a "
          f"dark patch. {n} winter pictures were clear of cloud.",
          "In each one the dark squares on the slack floor are counted, split into open water "
          "(the darkest) and wet floor, and set against the water table the dipwells measured in "
          "the same month. Each pair of points on the figure is one picture. Four of them are "
          "shown below in that near-infrared band, driest to wettest, each scaled to its own "
          "slack-floor brightness as the method reads it; each line leads to its points.",
          "The points fall on two smooth curves. Wet floor grows gently as the water table rises; "
          "open water stays near nothing until the water is close to the surface, then climbs "
          "steeply. These curves turn the film's water table into the hectares in its title.",
          f"They are fitted between {lo_s} m and {hi_s} m, the range the pictures saw. Above "
          f"that, the film says BEYOND THE RECORD."],
         "fit", OUT_45_MODEL_AXES),
        (OUT_45_SSM_CURVES_FIG, "The check: the model against the satellite",
         ["Before the curves are trusted with the model, they are tested with it. Here the "
          "curves are driven by the model's water table instead of the wells, and the area they "
          "predict is compared, month by month, with the area the satellite actually measured.",
          "The satellite takes no part in the model, so this is an independent test of the water "
          "table itself, not of the curves alone. The same four near-infrared pictures are below; each "
          "line leads to its month on the upper panel and names the peak or trough it belongs "
          "to.",
          "Wet floor is reproduced closely. Open water, which appears suddenly as the water "
          "reaches the surface, is reproduced less well: a small error in the water table makes a "
          "large one in the area of pools. That is why the film's blue is the less certain colour."],
         "check", OUT_45_SSM_CURVES_AXES),
    )
    check = _check_targets(thumbs) if thumbs else []
    for src, title_, paras, which, axes_json in specs:
        if not src.exists():
            warn(f"{src.name} not found; its figure slide is left out")
            continue
        if thumbs:
            if which == "fit":
                targets = [dict(points=[(d["h"], d["ow"]), (d["h"], d["wf"])],
                                label=_thumb_label(d)) for d in thumbs]
            else:
                targets = check or [None] * len(thumbs)
            extra = dict(kind="thumbs", image=src, axes=axes_json, ax_index=0,
                         thumbs=thumbs, targets=targets, band="nir")
        else:
            extra = dict(kind="figure", image=src)
        out.append((title_, paras, _foot(src) + f" · {cop}", extra))

    if OUT_45_SWITCHING_LEVELS_MAP.exists():
        out.append((
            "3.  Where the water goes: the second calibration",
            ["The curves say how much of the floor is wet; they do not say where. For that, each "
             "10 m square's own history in the pictures is used: the water-table level at which it "
             "first read wet floor (a, upper map) and first read open water (b, lower map).",
             "The lowest hollows switch first, the higher margins last. Grey squares never switched "
             "within the range the pictures saw, and the forest is left out because under trees the "
             "satellite sees the canopy, not the ground.",
             "The film lights each square when the model's water table reaches its level. WHERE the "
             "colours appear was learned from the satellite; WHEN is the model."],
            _foot(OUT_45_SWITCHING_LEVELS_MAP) + f" · {cop}",
            dict(kind="figure", image=OUT_45_SWITCHING_LEVELS_MAP)))
    else:
        warn(f"{OUT_45_SWITCHING_LEVELS_MAP.name} not found; its figure slide is left out")

    if len(thumbs) >= 2:
        dry, wet = thumbs[0], thumbs[-1]
        out.append((
            "What the warren looks like from space",
            ["The driest and the wettest of those four pictures, each beside the film's own map "
             "of the same month.",
             "In the pictures the flooded slack floors are the dark patches between the pale dunes. "
             "The film lights its yellow and blue in the same hollows as its water table rises.",
             "This is an illustration, not a test. Where the colours appear was learned from these "
             "same pictures, so some of the likeness is built in. The independent test is the "
             "check two slides back, where the satellite takes no part in the model."],
            f"{cop} {dry['date'].year}, {wet['date'].year}",
            dict(kind="compare", pairs=[dry, wet])))
    return out


def build_text(feed: dict, floor_ha: float, thumbs: list | None = None,
               stats: dict | None = None) -> tuple:
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
    yrs = sorted({d["date"].year for d in (thumbs or [])})
    cop_years = ("Contains modified Copernicus Sentinel data " + ", ".join(map(str, yrs))
                 if yrs else "Contains modified Copernicus Sentinel data")
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
        ("About this film",
         ["A film of how wet the dune slacks would have been, month by month, from 1930 to 2026 — if "
          "the reserve as it stands today had lived through the weather of each of those years.",
          "Newborough Warren is a sand-dune reserve on Anglesey. Between the dunes lie hundreds of low "
          "hollows called slacks. In a wet winter the water table rises into them: the ground goes "
          "damp, pools appear, and in a very wet spring whole slacks stand under water.",
          "Only the warren is modelled, not the forest. Everything here is about the open dune slacks "
          "of Newborough Warren — the study area outlined on the map. The planted forest beside them "
          "is not part of the model and is not assessed; absence of yellow and blue cells does not "
          "imply an absence of flooding, rather it has not been modelled."],
         FILM_BYLINE, None),
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
          "the film has got to. The clock runs at a year a second.",
          "The slides that follow show how it was made: a groundwater model, satellite pictures "
          "and a map of where the water goes, joined together, each beside the report figures "
          "that calibrate and test it."], None, None),
        *method_slides(n, rng, thumbs or [], stats),
        *([("What you hear",
            ["The sound is made from the water, month by month. Nothing in it is recorded.",
             "A soft chord runs throughout. While the months play, its upper voices open as "
             "the water table rises, and in the months beyond the record it trembles.",
             "Each January a single note marks the year. The higher and louder the note, the "
             "more open water that year reached.",
             "The surf swells with the wet area, wet floor and open water together, and leans "
             "toward where the wetting is: right for the east of the warren, left for the west.",
             "Held notes sound while the water table is above the lines on the chart at the bottom: "
             "one above the yellow line, where wet floor appears; a higher one above the blue "
             "line, where open water appears; and the highest above the 2021 flood."],
            None, None)] if FILM_SOUND_TRACK == "warren" else []),
        ("Please read this before watching",
         ["It is today's warren, not the warren of the time. The rules were learned from 2005–2026 "
          "and the ground is the 2023 survey, with Newborough Forest at its present size. The forest "
          "was only planted between 1947 and 1965, and a forest lowers the water table around it. In "
          "1939 there was no forest. The film answers a what-if — what would the reserve as it is "
          "now have done under that weather — not what actually happened.",
          "The map covers the warren study area only; blank outside it means not assessed, not "
          "dry.",
          f"Satellite pictures: {cop_years}. Report figures are from the Newborough Warren "
          f"hydrology study."], None, None),
        ("The biggest floods go beyond anything measured",
         [f"The wettest spring on record was 2021. In some months — 1939, 1959, 1961–62 and 2000–01 — "
          f"the model pushes the water table higher than that, above the {rng['max']:+.2f} m the "
          f"curves were fitted to.",
          "No picture has seen the warren like that. So those months are marked BEYOND THE RECORD, "
          "the totals are the curves run past the end of the data, and the rest of the slack floor "
          "turns PALE ORANGE: wetter than anything on record, where exactly we cannot say.",
          "The honest claim for those winters is that they were bigger than 2021, nothing finer."],
         None, None),
    ]
    after = [
        ("What the film says, cautions attached",
         ["The 1960s were the wet decade, with several times the open water of an average winter in "
          "any other decade.",
          "The winters of 1961–62 and 2000–01 stand out as the two great floods of the century, with "
          "1938–39 and 1958–59 behind them; 2015–16 was the wettest of the satellite era after 2021.",
          "The 1970s and 1990s were the dry decades, with almost no open water in an average winter.",
          "All of it is the model's account of what the weather would do to the reserve as it stands "
          "today."], None, None),
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
          "show what the water table would imply, not what a summer photograph would show."], None,
         None),
        ("Credits and sources",
         ["Newborough Warren hydrology study, 2026 — Martin Hollingham.",
          "Weather: RAF Valley monthly record, 1930–2026. Water table: the reserve's dipwell "
          "network, 2005–2026. Ground: 2023 survey.",
          f"Imagery: Copernicus Sentinel-2, 2016–2026, free and open under the Copernicus "
          f"licence. {cop_years}.",
          "Model, code and data: github.com/newbroman/Newborough_Hydrology. The method is recorded "
          "as decision D-178; the full written guide accompanies this film.",
          "Sound: synthesised by the film's own code from the modelled water table and "
          "areas; no recordings."], None, None),
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
        for title, paras, foot, extra in slides:
            figs = [v.name for k, v in (extra or {}).items() if isinstance(v, Path)
                    and k in ("image", "left", "right")]
            thumbs = [d["month"] for d in (extra or {}).get("thumbs", []) + (extra or {}).get(
                "pairs", [])]
            L += ([f"### {title}"] + [f"[figure] {f}" for f in figs]
                  + ([f"[satellite] {', '.join(thumbs)}"] if thumbs else []) + list(paras)
                  + ([f"[footer] {foot}"] if foot else []) + [""])
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


# ─────────────────────────────────────────────────────────────────────────────
# THE SOUND TRACK — presentation cut only
# ─────────────────────────────────────────────────────────────────────────────
def _smooth(x: np.ndarray, seconds: float, sr: int) -> np.ndarray:
    """Moving average over `seconds` — the crossfades and the glides."""
    w = max(1, int(seconds * sr))
    c = np.cumsum(np.concatenate([[0.0], x]))
    y = (c[w:] - c[:-w]) / w
    pad = x.size - y.size
    return np.concatenate([np.full(pad // 2, y[0]), y, np.full(pad - pad // 2, y[-1])])


def sound_track(marks: list, lvl: np.ndarray, flooded_ha: np.ndarray, hmax: float) -> np.ndarray:
    """Stereo float track, sample-aligned to the frames.

    Under the slides (mark None): a slow ambient pad — a soft chord on
    FILM_AMBIENT_ROOT_HZ, each note slightly detuned against itself and breathing on
    its own slow cycle, with a faint filtered-noise swell.
    Over the monthly frames: a tone whose pitch rises with the calibrated water table
    across the hydrograph's axis (TRACE_LO_M..TRACE_HI_M -> FILM_TONE_F_LOW_HZ..HIGH),
    held at the top of the record beyond it; a brighter voice a fifth above whose
    loudness follows the flooded area (open water + wet floor), silent on a dry floor;
    and, in the months beyond the record, a tremolo. The two beds crossfade over
    FILM_AUDIO_FADE_S.
    """
    sr, fps = FILM_AUDIO_RATE_HZ, FILM_FPS
    nf = len(marks)
    ns = int(round(nf / fps * sr))
    fidx = np.minimum((np.arange(ns) * fps // sr).astype(int), nf - 1)
    t = np.arange(ns) / sr
    rng = np.random.default_rng(47)

    is_tone = np.array([m is not None for m in marks], float)
    mi = np.array([m if m is not None else 0 for m in marks], int)
    h_f = np.where(is_tone > 0, lvl[mi], np.nan)
    # carry the nearest month's level across the slides so the glide has no jump
    h_f = pd.Series(h_f).ffill().bfill().to_numpy()
    over_f = (h_f > hmax).astype(float) * is_tone
    fl = np.nan_to_num(flooded_ha[mi], nan=0.0) * is_tone
    fl_max = max(float(np.nanmax(flooded_ha)), 1e-9)

    w_tone = np.clip(_smooth(is_tone[fidx], FILM_AUDIO_FADE_S, sr), 0, 1)
    w_amb = 1.0 - w_tone

    # the tone: pitch from the level, gliding between months
    x = np.clip((np.minimum(h_f, hmax) - TRACE_LO_M) / (TRACE_HI_M - TRACE_LO_M), 0, 1)
    x_s = _smooth(x[fidx], 1.0 / fps, sr)
    f = FILM_TONE_F_LOW_HZ * (FILM_TONE_F_HIGH_HZ / FILM_TONE_F_LOW_HZ) ** x_s
    ph = 2 * np.pi * np.cumsum(f) / sr
    # The 2nd harmonic carries the dry end on speakers that cannot reproduce A1.
    tone = (np.sin(ph) + FILM_TONE_HARMONIC_GAIN * np.sin(2 * ph) + 0.10 * np.sin(3 * ph)) * (
        1.4 / (1.1 + FILM_TONE_HARMONIC_GAIN))
    flood_amp = np.sqrt(_smooth((fl / fl_max)[fidx], 2.0 / fps, sr))
    voice = sum(np.sin(k * 1.5 * ph) / k for k in range(1, 6))
    trem = 1.0 - FILM_TREMOLO_DEPTH * _smooth(over_f[fidx], 0.5, sr) * (
        0.5 + 0.5 * np.sin(2 * np.pi * FILM_TREMOLO_HZ * t))
    tone_bed = (FILM_TONE_GAIN * tone / 1.4 + FILM_FLOOD_VOICE_GAIN * flood_amp * voice / 2.3) * trem

    # the ambient pad: root, fifth, octave, tenth and ninth-above-octave
    left = np.zeros(ns); right = np.zeros(ns)
    for k, ratio in enumerate((1.0, 1.5, 2.0, 2.5, 4.5)):
        f0 = FILM_AMBIENT_ROOT_HZ * ratio
        period = 7.0 + 2.3 * k
        breath = 0.55 + 0.45 * np.sin(2 * np.pi * t / period + rng.uniform(0, 2 * np.pi))
        note = (np.sin(2 * np.pi * (f0 - 0.35) * t) + np.sin(2 * np.pi * (f0 + 0.35) * t)) / 2
        g = breath * note / (1.0 + 0.6 * k)
        pan = 0.5 + 0.35 * np.sin(2 * np.pi * t / (period * 1.7))
        left += g * (1 - pan); right += g * pan
    swell = _smooth(rng.standard_normal(ns), 0.004, sr)
    swell *= (0.5 + 0.5 * np.sin(2 * np.pi * t / 11.0)) / max(np.abs(swell).max(), 1e-9)
    amb_l = FILM_AMBIENT_GAIN * (left / 2.5 + 0.25 * swell)
    amb_r = FILM_AMBIENT_GAIN * (right / 2.5 + 0.25 * swell)

    out = np.stack([w_amb * amb_l + w_tone * tone_bed, w_amb * amb_r + w_tone * tone_bed], -1)
    edge = np.minimum(1.0, np.minimum(t / 2.0, (t[-1] - t) / 3.0))
    out *= edge[:, None]
    peak = float(np.abs(out).max())
    return out * (0.8 / peak) if peak > 0 else out


def sound_track_warren(marks: list, lvl: np.ndarray, aw: np.ndarray, af: np.ndarray,
                       months: list, hmax: float, arrivals: dict,
                       wet_pan: np.ndarray | None = None) -> np.ndarray:
    """The Warren track (1.3.0): stereo float32, sample-aligned to the frames.

    Pad: the slides' ambient chord on FILM_AMBIENT_ROOT_HZ runs under everything. Under a
    slide it sounds at rest; over the monthly frames its root and fifth always sound and
    its octave and upper voices open with the calibrated water table (0 at TRACE_LO_M, 1
    at the top of the record), with the tremolo on the months beyond the record.
    Annual note: on each January's first frame, one mallet note whose pitch (sqrt of the
    year's largest open water over the record's, snapped to FILM_NOTE_SCALE between
    FILM_NOTE_F_LOW_HZ and _HIGH_HZ) and loudness (FILM_NOTE_FLOOR to 1) follow the flooding.
    Wash: surf, FILM_WASH_HARMONIC of it through narrow resonators on the chord, whose
    loudness follows the wetted area (open water + wet floor) over the record's range.
    Chord: one held voice per line on the hydrograph (wet floor and open water arrival
    levels, the 2021 flood), struck as the level rises through it, held while above.
    The wash's stereo place (1.4.0) follows `wet_pan` (-1 west .. +1 east, per month).

    The presentation runs ~10 minutes (~26 M samples), so each layer is added into one
    float32 buffer and its temporaries released before the next is built.
    """
    from scipy.signal import lfilter                          # noqa: PLC0415
    sr, fps = FILM_AUDIO_RATE_HZ, FILM_FPS
    nf = len(marks)
    ns = int(round(nf / fps * sr))
    fidx = np.minimum((np.arange(ns, dtype=np.int64) * fps // sr), nf - 1).astype(np.int32)
    t = np.arange(ns) / sr
    rng = np.random.default_rng(47)
    sm = lambda x, sec: _smooth(x, sec, sr)                   # noqa: E731
    out = np.zeros((ns, 2), np.float32)

    def add(y, gain, pan=None):
        """Mix y (mono, or stereo (ns, 2)) into out at gain, optionally panned."""
        if y.ndim == 2:
            out[:] += (gain * y).astype(np.float32)
        elif pan is None:
            out[:] += (gain * y).astype(np.float32)[:, None]
        else:
            out[:, 0] += (gain * (0.5 - pan / 2) * y).astype(np.float32)
            out[:, 1] += (gain * (0.5 + pan / 2) * y).astype(np.float32)

    is_m = np.array([m is not None for m in marks], float)
    mi = np.array([m if m is not None else 0 for m in marks], int)
    h_m = pd.Series(np.where(is_m > 0, lvl[mi], np.nan)).ffill().bfill().to_numpy()  # per frame
    w_m = np.clip(sm(is_m[fidx], FILM_AUDIO_FADE_S), 0, 1)   # 1 over the months, 0 under slides

    # pad
    x = np.clip((np.minimum(h_m, hmax) - TRACE_LO_M) / (hmax - TRACE_LO_M), 0, 1)
    xo = sm(x[fidx], 0.5)
    for k, ratio in enumerate((1.0, 1.5, 2.0, 2.5, 4.5)):
        f0 = FILM_AMBIENT_ROOT_HZ * ratio
        period = 7.0 + 2.3 * k
        g = 0.55 + 0.45 * np.sin(2 * np.pi * t / period + rng.uniform(0, 2 * np.pi))
        g *= (np.sin(2 * np.pi * (f0 - 0.35) * t) + np.sin(2 * np.pi * (f0 + 0.35) * t)) / 2
        if k >= 2:
            g *= (1 - w_m) + w_m * (0.15 + 0.85 * xo) ** (1 + 0.6 * (k - 2))
        g /= 2.0 * (1.0 + 0.6 * k)
        pan = 0.5 + 0.35 * np.sin(2 * np.pi * t / (period * 1.7))
        out[:, 0] += (FILM_MIX_PAD * g * (1 - pan)).astype(np.float32)
        out[:, 1] += (FILM_MIX_PAD * g * pan).astype(np.float32)
        del g, pan
    del xo
    # the tremolo on the months beyond the record, applied to the pad alone
    over = sm(((h_m > hmax) * is_m)[fidx], 0.5)
    trem = (1.0 - FILM_TREMOLO_DEPTH * over
            * (0.5 + 0.5 * np.sin(2 * np.pi * FILM_TREMOLO_HZ * t))).astype(np.float32)
    out *= trem[:, None]
    del over, trem

    # annual note
    yr = np.array([int(m[:4]) for m in months])
    ow_max = float(np.nanmax(aw))
    oct_ = int(round(12 * np.log2(FILM_NOTE_F_HIGH_HZ / FILM_NOTE_F_LOW_HZ)))
    semis = np.array([o * 12 + d for o in range(oct_ // 12 + 1) for d in FILM_NOTE_SCALE
                      if o * 12 + d <= oct_])
    for j, k in enumerate(marks):
        if k is None or not months[k].endswith("-01") or (j > 0 and marks[j - 1] == k):
            continue
        xf = float(np.sqrt(max(np.nanmax(aw[yr == yr[k]]), 0.0) / ow_max))
        f = FILM_NOTE_F_LOW_HZ * 2 ** (semis[np.argmin(np.abs(semis - oct_ * xf))] / 12)
        a0 = int(j / fps * sr); b0 = min(ns, a0 + int(2.5 * FILM_NOTE_DECAY_S * sr))
        tt = np.arange(b0 - a0) / sr
        env = (1 - np.exp(-tt / 0.008)) * np.exp(-tt / FILM_NOTE_DECAY_S)
        tone = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) * np.exp(-tt / 0.2)
                + 0.12 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt / 0.08))
        y = FILM_MIX_NOTE * (FILM_NOTE_FLOOR + (1 - FILM_NOTE_FLOOR) * xf) * env * tone / 1.47
        out[a0:b0] += y.astype(np.float32)[:, None]

    # wash
    wet = aw + af
    lo, hi = np.nanpercentile(wet, FILM_WASH_FLOOR_PCT), np.nanmax(wet)
    wl = np.sqrt(sm((np.clip((np.nan_to_num(wet[mi], nan=lo) - lo) / (hi - lo), 0, 1) * is_m)[fidx],
                    2.0 / fps))
    r = np.exp(-np.pi * FILM_WASH_BANDWIDTH_HZ / sr)
    wp = None
    if wet_pan is not None:          # where the water is, eased in only over the months
        wp = sm((np.nan_to_num(np.asarray(wet_pan, float))[mi] * is_m)[fidx], 0.6)
        wp = np.clip(wp * w_m, -1, 1) * FILM_WASH_PAN_WIDTH
    for ch, seed in enumerate((1, 2)):
        z = np.random.default_rng(seed).standard_normal(ns)
        y = sm(z, 1 / 1500.) - sm(z, 1 / 250.)
        y *= (1 - FILM_WASH_HARMONIC) / np.abs(y).max()
        z = np.random.default_rng(seed + 10).standard_normal(ns)
        sung = np.zeros(ns)
        for k, st in enumerate(FILM_WASH_SEMITONES):
            th = 2 * np.pi * FILM_AMBIENT_ROOT_HZ * 2 ** (st / 12) / sr
            sung += lfilter([1 - r], [1, -2 * r * np.cos(th), r * r], z) / (1 + 0.5 * k)
        del z
        y += FILM_WASH_HARMONIC * sung / np.abs(sung).max()
        del sung
        y *= (0.65 + 0.35 * np.sin(2 * np.pi * t / FILM_WASH_SURGE_S + seed)) * wl
        if wp is not None:           # equal-power pan, unity at the centre
            y *= np.sqrt(2.0) * (np.cos if ch == 0 else np.sin)((wp + 1) * np.pi / 4)
        out[:, ch] += (FILM_MIX_WASH * y).astype(np.float32)
        del y
    del wl


    # chord: a held voice above each line on the hydrograph
    lines = [(arrivals.get("wet_floor"), FILM_CHORD_SEMITONES[0], -0.35),
             (arrivals.get("open_water"), FILM_CHORD_SEMITONES[1], 0.0),
             (hmax, FILM_CHORD_SEMITONES[2], 0.35)]
    for th, st, pan in lines:
        if th is None:
            continue
        f = FILM_AMBIENT_ROOT_HZ * 2 ** (st / 12)
        gate = ((h_m >= th) * is_m)[fidx]
        g_out = sm(gate, FILM_CHORD_RELEASE_S)
        env = np.where(np.gradient(g_out) >= 0, np.maximum(sm(gate, 0.03), g_out), g_out)
        del g_out
        ph = 2 * np.pi * np.cumsum(f * (1 + 0.003 * np.sin(2 * np.pi * 4.5 * t + f))) / sr
        y = 0.7 * env * (np.sin(ph) + 0.30 * np.sin(2 * ph) + 0.10 * np.sin(3 * ph)) / 1.4
        del ph, env
        for a0 in np.flatnonzero(np.diff(gate) > 0) + 1:
            tt = np.arange(min(ns - a0, int(0.6 * sr))) / sr
            y[a0:a0 + tt.size] += 0.5 * np.exp(-tt / 0.12) * np.sin(2 * np.pi * 2 * f * tt)
        add(y, FILM_MIX_CHORD, pan)
        del y, gate

    out *= np.minimum(1.0, np.minimum(t / 2.0, (t[-1] - t) / 3.0)).astype(np.float32)[:, None]
    peak = float(np.abs(out).max())
    return out * np.float32(0.85 / peak) if peak > 0 else out


def write_wav(path: Path, track: np.ndarray) -> None:
    import wave                                               # noqa: PLC0415
    pcm = (np.clip(track, -1, 1) * np.iinfo(np.int16).max).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(FILM_AUDIO_RATE_HZ)
        w.writeframes(pcm.tobytes())


def mux(video: Path, audio: Path, target: Path, chapters: Path | None = None) -> None:
    """Video copied as encoded, the track encoded to AAC, chapters (FFMETADATA) if
    given, into `target`."""
    import subprocess                                         # noqa: PLC0415
    import imageio_ffmpeg                                     # noqa: PLC0415
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-i", str(video), "-i", str(audio)]
    if chapters is not None:
        cmd += ["-i", str(chapters), "-map_metadata", "2", "-map_chapters", "2"]
    cmd += ["-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
            "-b:a", FILM_AUDIO_BITRATE, "-shortest", "-movflags", "+faststart", str(target)]
    subprocess.run(cmd, check=True)


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT — text measured in the font matplotlib draws with, not guessed
# ─────────────────────────────────────────────────────────────────────────────
_FONT100 = {}


def _text_w(s: str, fs: float, bold: bool = False) -> float:
    """Width in pixels of `s` at `fs` points on the FRAME_DPI frame (DejaVu Sans, the
    matplotlib default the frames are drawn in)."""
    if bold not in _FONT100:
        import matplotlib                                     # noqa: PLC0415
        from PIL import ImageFont                             # noqa: PLC0415
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        _FONT100[bold] = ImageFont.truetype(
            str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / name), 100)
    return _FONT100[bold].getlength(s) * (fs * FRAME_DPI / 72.0) / 100.0


def _wrap(p: str, fs: float, width_px: float) -> list:
    lines, cur = [], ""
    for w in p.split():
        t = f"{cur} {w}" if cur else w
        if cur and _text_w(t, fs) > width_px:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


def _text_block(ax, paras, x0, x1, y_top, y_bot, sizes=TEXT_SIZES, color="#2a2a2a") -> float:
    """The paragraphs, wrapped to x0..x1 (frame fractions), at the largest size in
    `sizes` whose lines fit between y_top and y_bot. Returns the size used."""
    width, avail = (x1 - x0) * FRAME_W, (y_top - y_bot) * FRAME_H
    for fs in sizes:
        lines = [_wrap(p, fs, width) for p in paras]
        lh = fs * FRAME_DPI / 72.0 * LINE_EM
        if sum(map(len, lines)) * lh + (len(paras) - 1) * PARA_GAP * lh <= avail:
            break
    else:
        warn(f"text does not fit its block even at {sizes[-1]} pt: {paras[0][:40]}...")
    y = y_top
    for block in lines:
        for line in block:
            ax.text(x0, y, line, fontsize=fs, va="top", color=color)
            y -= lh / FRAME_H
        y -= PARA_GAP * lh / FRAME_H
    return fs


def _title(ax, title_, x0, x1, y, fs_max=TITLE_PT_MAX):
    """One line, as large as fits x0..x1."""
    fs = min(fs_max, fs_max * (x1 - x0) * FRAME_W / max(_text_w(title_, fs_max, True), 1.0))
    ax.text(x0, y, title_, fontsize=fs, weight="bold", va="top", color=FILM_COL_TITLE)


def _shade(fig, strength: float = 1.0) -> None:
    """The slide background: FILM_SLIDE_TOP easing to FILM_SLIDE_FOOT. `strength` > 1
    moves both further from white (the title slide)."""
    from matplotlib.colors import to_rgb                      # noqa: PLC0415
    top, foot = (1 - (1 - np.array(to_rgb(c))) * strength for c in (FILM_SLIDE_TOP, FILM_SLIDE_FOOT))
    g = np.linspace(0, 1, 256)[:, None, None]
    axb = fig.add_axes([0, 0, 1, 1], zorder=-10)
    axb.imshow(np.clip(top * (1 - g) + foot * g, 0, 1), aspect="auto", extent=(0, 1, 0, 1))
    axb.set_axis_off()


def _place(fig, img, x0, y0, x1, y1, ha="center", va="center", border=True) -> list:
    """An image (Path or array) fitted inside the box x0..x1, y0..y1 (frame fractions)
    at its own aspect. Returns the rectangle it occupies [x, y, w, h]."""
    from matplotlib.patches import Rectangle                  # noqa: PLC0415
    from PIL import Image                                     # noqa: PLC0415
    a = np.asarray(Image.open(img).convert("RGB")) if isinstance(img, Path) else img
    h, w = a.shape[:2]
    s = min((x1 - x0) * FRAME_W / w, (y1 - y0) * FRAME_H / h)
    pw, ph = w * s / FRAME_W, h * s / FRAME_H
    x = {"left": x0, "right": x1 - pw}.get(ha, (x0 + x1 - pw) / 2)
    y = {"bottom": y0, "top": y1 - ph}.get(va, (y0 + y1 - ph) / 2)
    ax = fig.add_axes([x, y, pw, ph])
    ax.imshow(a, aspect="auto", interpolation="antialiased")
    ax.set_axis_off()
    if border:
        fig.add_artist(Rectangle((x, y), pw, ph, transform=fig.transFigure, fill=False,
                                 edgecolor=FRAME_EDGE, lw=0.8, zorder=5))
    return [x, y, pw, ph]


def _to_frame(rect: list, meta: dict, x: float, y: float) -> tuple:
    """A data point of a saved figure's axes -> frame fractions, through the axes
    sidecar Script 45 writes beside the figure (box and limits, y from the bottom)."""
    b, (x0, x1), (y0, y1) = meta["box"], meta["xlim"], meta["ylim"]
    u = b[0] + (x - x0) / (x1 - x0) * (b[2] - b[0])
    v = b[1] + (y - y0) / (y1 - y0) * (b[3] - b[1])
    return rect[0] + u * rect[2], rect[1] + v * rect[3]


def _fmt_time(frames: int) -> str:
    s = int(round(frames / FILM_FPS))
    return f"{s // 60}:{s % 60:02d}"


def write_chapters(path: Path, entries: list, total_frames: int) -> None:
    """ffmpeg FFMETADATA chapters: (title, start frame) in order."""
    L = [";FFMETADATA1"]
    for k, (title_, f0) in enumerate(entries):
        f1 = entries[k + 1][1] if k + 1 < len(entries) else total_frames
        L += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(f0 * 1000 / FILM_FPS)}",
              f"END={int(f1 * 1000 / FILM_FPS)}",
              "title=" + title_.replace("=", r"\=").replace(";", r"\;").replace("#", r"\#")]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def render(level, cells, feed, floor_ha, text, arrivals, presentation, still_month=None):
    """The film. One frame a month, plus the guide slides on the presentation cut.

    Returns the still's frame when `still_month` is given, so the PNG and the film
    are the same render rather than two that might drift.
    """
    import imageio                                            # noqa: PLC0415
    import matplotlib                                         # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.patheffects as pe                       # noqa: PLC0415
    import matplotlib.pyplot as plt                           # noqa: PLC0415
    from PIL import Image                                     # noqa: PLC0415

    hb, hd, floor = cells
    caption, caption_beyond, before, after = text
    # 1.4.0: the bold beyond-the-record heading on a line of its own (it is drawn bold, and
    # the reflow measures regular weight)
    head_b = "THIS MONTH IS BEYOND THE RECORD."
    caption_beyond = caption_beyond.replace(head_b, head_b + "\n\n", 1)
    hmax = float(feed["fitted_range_m"]["max"])
    t = pd.PeriodIndex(level["month"], freq="M").to_timestamp()
    months = level["month"].astype(str).str[:7].tolist()
    lvl = level["median_level_calibrated_m"].to_numpy(float)
    aw = level["open_water_ha"].to_numpy(float)
    af = level["wet_floor_ha"].to_numpy(float)
    # Where the water is (1.4.0): the east-west centre of the wetted cells each month,
    # scaled over the months' own range to -1 (west) .. +1 (east); 0 under 1 ha wet.
    thr = np.minimum(hd, hb)[floor]
    col = np.nonzero(floor)[1].astype(float)
    order = np.argsort(thr)
    thr_s, ccum = thr[order], np.cumsum(col[order])
    nwet = np.searchsorted(thr_s, np.minimum(lvl, hmax), side="right")
    cx = np.where(nwet >= 100, ccum[np.maximum(nwet, 1) - 1] / np.maximum(nwet, 1), np.nan)
    if np.isfinite(cx).sum() > 1:
        lo_x, hi_x = np.nanpercentile(cx, [5, 95])
        wet_pan = np.nan_to_num(np.clip(2 * (cx - lo_x) / max(hi_x - lo_x, 1e-9) - 1, -1, 1))
    else:
        wet_pan = np.zeros(len(lvl))
    rgb = _background(floor.shape)
    still = {}

    def paint(i: int) -> np.ndarray:
        """The map of month i: the cells lit at its level, the floor pale orange beyond
        the record. The film's frames and the comparison slide both draw with this."""
        h = lvl[i]
        hc = min(h, hmax)
        img = rgb.copy()
        y, b = floor & (hd <= hc), floor & (hb <= hc)
        if h > hmax:
            img[floor & ~y] = COL_BEYOND
        img[y] = COL_FLOOR
        img[b] = COL_WATER
        return img

    def even(a):
        return a[:a.shape[0] // 2 * 2, :a.shape[1] // 2 * 2].copy()

    def new_slide(strength=1.0):
        fig = plt.figure(figsize=(FRAME_W / FRAME_DPI, FRAME_H / FRAME_DPI), dpi=FRAME_DPI)
        _shade(fig, strength)
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        return fig, ax

    def grab(fig, seconds):
        fig.canvas.draw()
        a = even(np.asarray(fig.canvas.buffer_rgba())[..., :3])
        plt.close(fig)
        return [a] * int(round(seconds * FILM_FPS))

    def hold(title_, paras, figure=False, extra_s=0.0):
        words = len(title_.split()) + sum(len(p.split()) for p in paras)
        return (FILM_SLIDE_LEAD_S + words / (FILM_WORDS_PER_MINUTE / 60.0)
                + (FILM_FIGURE_VIEW_S if figure else 0.0) + extra_s)

    def text_slide(title_, paras, foot):
        fig, ax = new_slide()
        _title(ax, title_, 0.06, 0.94, 0.92)
        _text_block(ax, paras, 0.06, 0.94, 0.80, 0.10, sizes=TEXT_SIZES_WIDE)
        if foot:
            ax.text(0.06, 0.045, foot, fontsize=11, color="#666")
        return grab(fig, hold(title_, paras))

    def left_column(ax, title_, paras, foot, x1=0.36):
        _title(ax, title_, 0.035, 0.965, 0.955)
        _text_block(ax, paras, 0.035, x1, 0.855, 0.075)
        if foot:
            ax.text(0.035, 0.025, foot, fontsize=9.5, color="#666")

    def figure_slide(title_, paras, foot, image):
        """A report figure beside the words that explain it: text left, figure right."""
        fig, ax = new_slide()
        left_column(ax, title_, paras, foot)
        _place(fig, image, 0.385, 0.07, 0.99, 0.875)
        return grab(fig, hold(title_, paras, figure=True))

    def model_slide(title_, paras, foot, left, right):
        """Slide 1: the climate figure large on the left, the CEH6 simulation panel top
        right, the words beneath it."""
        fig, ax = new_slide()
        _title(ax, title_, 0.035, 0.965, 0.955)
        r = _place(fig, left, 0.02, 0.06, 0.47, 0.875, ha="left")
        x0 = r[0] + r[2] + 0.025
        rr = _place(fig, right, x0, 0.50, 0.985, 0.875, va="top")
        _text_block(ax, paras, x0, 0.985, rr[1] - 0.03, 0.075)
        if foot:
            ax.text(0.035, 0.025, foot, fontsize=9.5, color="#666")
        return grab(fig, hold(title_, paras, figure=True))

    def thumbs_slide(title_, paras, foot, ex):
        """A report figure with the satellite thumbnails beneath it, a callout from each
        thumbnail to the point or month it is on the figure."""
        fig, ax = new_slide()
        left_column(ax, title_, paras, foot)
        rect = _place(fig, ex["image"], 0.385, 0.33, 0.99, 0.875)
        meta = None
        if ex["axes"].exists():
            meta = json.loads(ex["axes"].read_text(encoding="utf-8"))["axes"][ex["ax_index"]]
        else:
            warn(f"no {ex['axes'].name}: thumbnails drawn without callouts "
                 f"(re-run Script 45 to write it)")
        th = ex["thumbs"]
        gap = 0.012
        cw = (0.99 - 0.385 - gap * (len(th) - 1)) / len(th)
        ov = fig.add_axes([0, 0, 1, 1], zorder=20); ov.set_axis_off()
        ov.set_xlim(0, 1); ov.set_ylim(0, 1)
        halo = [pe.withStroke(linewidth=2.6, foreground="white")]
        for k, (d, tg) in enumerate(zip(th, ex["targets"])):
            x0 = 0.385 + k * (cw + gap)
            r = _place(fig, (d[ex.get("band", "rgb")] * 255).astype(np.uint8), x0, 0.105,
                       x0 + cw, 0.265,
                       va="top")
            label = tg["label"] if tg else _thumb_label(d)
            ax.text(r[0] + r[2] / 2, r[1] - 0.008, label, fontsize=8.5, ha="center", va="top",
                    color="#333")
            if meta is None or tg is None:
                continue
            sx, sy = r[0] + r[2] / 2, r[1] + r[3]
            for (px, py) in tg["points"]:
                fx, fy = _to_frame(rect, meta, px, py)
                ov.plot([sx, fx], [sy, fy], color=CALLOUT, lw=1.0, alpha=0.9, path_effects=halo)
                ov.plot([fx], [fy], marker="o", ms=7, mfc="none", mec=CALLOUT, mew=1.4)
        return grab(fig, hold(title_, paras, figure=True))

    def compare_slide(title_, paras, foot, ex):
        """The driest and the wettest thumbnail, each beside the film's map of its month."""
        fig, ax = new_slide()
        left_column(ax, title_, paras, foot, x1=0.33)
        xs = (0.35, 0.6725, 0.995)
        ax.text((xs[0] + xs[1]) / 2, 0.855, "Sentinel-2, true colour", fontsize=11,
                ha="center", va="top", weight="bold", color="#333")
        ax.text((xs[1] + xs[2]) / 2, 0.855, "The film, the same month", fontsize=11,
                ha="center", va="top", weight="bold", color="#333")
        rows = ((0.47, 0.815), (0.08, 0.425))
        for d, (y0, y1) in zip(ex["pairs"], rows):
            if d["month"] not in months:
                warn(f"{d['month']} is not in the film's record; comparison row left out")
                continue
            i = months.index(d["month"])
            r1 = _place(fig, (d["rgb"] * 255).astype(np.uint8), xs[0] + 0.005, y0 + 0.035,
                        xs[1] - 0.005, y1)
            r2 = _place(fig, paint(i), xs[1] + 0.005, y0 + 0.035, xs[2] - 0.005, y1)
            ax.text(r1[0] + r1[2] / 2, r1[1] - 0.006, _thumb_label(d), fontsize=9.5,
                    ha="center", va="top", color="#333")
            ax.text(r2[0] + r2[2] / 2, r2[1] - 0.006,
                    f"{t[i].strftime('%b %Y')} · model {_minus(f'{lvl[i]:+.2f}')} m · "
                    f"{aw[i]:.0f} ha open water, {af[i]:.0f} ha wet floor",
                    fontsize=9.5, ha="center", va="top", color="#333")
        return grab(fig, hold(title_, paras, figure=True))

    def index_slide(entries):
        """The title page and the contents, each entry with its start time."""
        fig, ax = new_slide(strength=TITLE_SHADE)
        _title(ax, FILM_TITLE, 0.06, 0.94, 0.90, fs_max=34)
        ax.text(0.06, 0.80, FILM_SUBTITLE, fontsize=15, va="top", color="#2a2a2a")
        ax.plot([0.06, 0.94], [0.735, 0.735], color=COL_WATER, lw=2.2)
        ax.text(0.06, 0.69, "Contents", fontsize=15, weight="bold", va="top", color=FILM_COL_TITLE)
        half = (len(entries) + 1) // 2
        fs = 14.0
        lh = fs * FRAME_DPI / 72.0 * 1.55 / FRAME_H
        for k, (title_, f0) in enumerate(entries):
            col, row = divmod(k, half)
            x = 0.06 + col * 0.45
            y = 0.625 - row * lh
            ax.text(x + 0.05, y, _fmt_time(f0), fontsize=fs, va="top", ha="right",
                    color=COL_WATER, weight="bold")
            ax.text(x + 0.064, y, title_, fontsize=fs, va="top", color="#2a2a2a")
        ax.text(0.06, 0.045, FILM_BYLINE, fontsize=11, color="#666")
        # The contents are scanned, not read: a fixed glance per entry, not a word count.
        words = len(FILM_TITLE.split()) + len(FILM_SUBTITLE.split())
        return grab(fig, FILM_SLIDE_LEAD_S + words / (FILM_WORDS_PER_MINUTE / 60.0)
                    + INDEX_ENTRY_S * len(entries) + FILM_INDEX_VIEW_S)

    def open_title_slide():
        """The short opening page (1.3.0): title, subtitle and byline, no contents."""
        fig, ax = new_slide(strength=TITLE_SHADE)
        _title(ax, FILM_TITLE, 0.06, 0.94, 0.62, fs_max=34)
        ax.text(0.06, 0.52, FILM_SUBTITLE, fontsize=15, va="top", color="#2a2a2a")
        ax.plot([0.06, 0.94], [0.455, 0.455], color=COL_WATER, lw=2.2)
        ax.text(0.06, 0.045, FILM_BYLINE, fontsize=11, color="#666")
        return grab(fig, FILM_OPEN_TITLE_S)

    def build_slide(title_, paras, foot, extra):
        kind = (extra or {}).get("kind")
        if kind == "figure":
            return figure_slide(title_, paras, foot, extra["image"])
        if kind == "model":
            return model_slide(title_, paras, foot, extra["left"], extra["right"])
        if kind == "thumbs":
            return thumbs_slide(title_, paras, foot, extra)
        if kind == "compare":
            return compare_slide(title_, paras, foot, extra)
        return text_slide(title_, paras, foot)

    # The film is planned as segments and STREAMED to the encoder: a slide is one
    # image held for its length (the list repeats one array), the monthly frames are
    # drawn one at a time as they are written. Holding every monthly frame in memory
    # (1.2.0's first cut) took over 6 GB for the century.
    def slide_segments(slides):
        return [(title_, build_slide(title_, paras, foot, extra))
                for title_, paras, foot, extra in slides]
    seg_before = slide_segments(before) if presentation else []
    seg_after = slide_segments(after) if presentation else []

    fig = plt.figure(figsize=(FRAME_W / FRAME_DPI, FRAME_H / FRAME_DPI), dpi=FRAME_DPI)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.02, 0.30, 0.62, 0.60])
    ax2 = fig.add_axes([0.07, 0.07, 0.78, 0.18])
    axt = fig.add_axes([0.66, 0.30, 0.33, 0.60]); axt.set_axis_off()
    axr = fig.add_axes([0, 0, 1, 1], zorder=-1); axr.set_axis_off()
    axr.set_xlim(0, 1); axr.set_ylim(0, 1)
    im = ax.imshow(rgb); ax.set_axis_off()
    # The study area, drawn once: the boundary of the floor mask itself. Without
    # it an unassessed cell and a dry cell are the same blank pixel.
    ax.contour(floor.astype(float), levels=[0.5], colors=["#1f1f1f"],
               linewidths=0.7, linestyles="dashed")

    # The readout above the map (Martin, 2026-09-25: "the fields remained static and
    # the text as large as it can without running in to 2 lines"). Each field has a
    # fixed anchor: a static label, then its value right-aligned in a slot as wide as
    # the widest value in the record (DejaVu digits are all one width, so a value
    # never shifts inside its slot). The size is fitted ONCE, to the widest line the
    # record can produce, so nothing moves or re-wraps from frame to frame.
    fmt_level = [_minus(f"{v:+.2f} m") for v in lvl]
    fmt_ow = [f"{v:.0f} ha" for v in aw]
    fmt_wf = [f"{v:.0f} ha" for v in af]
    fmt_mname = [d.strftime("%B") for d in t]
    fmt_year = [d.strftime("%Y") for d in t]
    study = f"study area {floor_ha:.0f} ha"
    beyond = "BEYOND THE RECORD"
    # The month name is right-aligned in its slot and the year follows at a fixed
    # place, so the year never moves as the month names change length.
    fields = (("", fmt_mname), ("", fmt_year), ("water table", fmt_level),
              ("open water", fmt_ow), ("wet floor", fmt_wf))

    def line_width(fs):
        w = 0.0
        for k, (lab, vals) in enumerate(fields):
            w += (_text_w(lab + " ", fs) if lab else 0) + max(_text_w(v, fs, True) for v in vals)
            w += _text_w(" " if k == 0 else READOUT_GAP, fs)
        return w + _text_w(study, fs) + _text_w(READOUT_GAP, fs) + _text_w(beyond, fs, True)

    avail = (READOUT_X1 - READOUT_X0) * FRAME_W
    fs_r = min(READOUT_PT_MAX, READOUT_PT_MAX * avail / line_width(READOUT_PT_MAX))
    x = READOUT_X0
    slots = []
    for k, (lab, vals) in enumerate(fields):
        if lab:
            axr.text(x, READOUT_Y, lab, fontsize=fs_r, va="center", ha="left", color="#555")
            x += _text_w(lab + " ", fs_r) / FRAME_W
        vw = max(_text_w(v, fs_r, True) for v in vals) / FRAME_W
        left = k == 1                                  # the year: left-aligned after the month
        # 1.4.0: open water and wet floor in the map's colours, so the title is the legend
        col_v = {3: COL_WATER, 4: FILM_COL_FLOOR_TEXT}.get(k, "#1f1f1f")
        slots.append(axr.text(x if left else x + vw, READOUT_Y, "", fontsize=fs_r, va="center",
                              ha="left" if left else "right", weight="bold", color=col_v))
        x += vw + _text_w(" " if k == 0 else READOUT_GAP, fs_r) / FRAME_W
    axr.text(x, READOUT_Y, study, fontsize=fs_r, va="center", ha="left", color="#777")
    x += (_text_w(study, fs_r) + _text_w(READOUT_GAP, fs_r)) / FRAME_W
    over_txt = axr.text(x, READOUT_Y, "", fontsize=fs_r, va="center", ha="left",
                        weight="bold", color="#b5532a")

    obs = level["median_level_observed_m"]
    wells_from = t[obs.notna().to_numpy()].min() if obs.notna().any() else t.max()
    ax2.fill_between(t, TRACE_LO_M, TRACE_HI_M, where=t < wells_from, color="#eeeeee", zorder=0)
    # 1.4.0: the trace in the colour of what the map shows at that level
    from matplotlib.collections import LineCollection          # noqa: PLC0415
    from matplotlib.colors import to_rgb                        # noqa: PLC0415
    import matplotlib.dates as _md                              # noqa: PLC0415
    xs = _md.date2num(t)
    segs = np.stack([np.column_stack([xs[:-1], lvl[:-1]]), np.column_stack([xs[1:], lvl[1:]])], 1)
    mid = np.maximum(lvl[:-1], lvl[1:])
    ow_h, wf_h = arrivals.get("open_water", np.inf), arrivals.get("wet_floor", np.inf)
    seg_col = np.where(mid[:, None] >= ow_h, np.array([COL_WATER]),
                       np.where(mid[:, None] >= wf_h, np.array([to_rgb(FILM_COL_FLOOR_TEXT)]),
                                np.array([(0.0, 0.0, 0.0)])))
    ax2.add_collection(LineCollection(segs, colors=seg_col, linewidths=0.7))
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
        # 1.4.0: in the margin beside the axes (it ran off the frame's edge at 1.3.0)
        ax2.annotate(f"{label} {hv:+.2f} m".replace("-", "\u2212"),
                     xy=(1.0, hv), xycoords=("axes fraction", "data"),
                     xytext=(5, 0), textcoords="offset points", fontsize=8,
                     color=FILM_COL_FLOOR_TEXT if cls == "wet_floor" else colour,
                     va="center", ha="left", annotation_clip=False)
    ax2.axhline(hmax, color="#0b6e8f", lw=0.6, ls="--")
    ax2.fill_between(t, hmax, TRACE_HI_M, color="#e8734a", alpha=0.10)
    ax2.set_ylim(TRACE_LO_M, TRACE_HI_M)
    ax2.set_xlim(t[0], t[-1])
    xlim_full = ax2.get_xlim()
    ax2.set_ylabel("water table, m\n(0 = ground)", fontsize=9)
    ax2.tick_params(labelsize=9)
    ax2.margins(x=0)
    # The eras head the axes (1.4.0); inside, they crowded the 2021 band.
    era = [ax2.text(t[0], 1.03, "before the wells: model only, corrected to the well years",
                    transform=ax2.get_xaxis_transform(), fontsize=9, color="#555", va="bottom"),
           ax2.text(wells_from, 1.03, "wells measured", transform=ax2.get_xaxis_transform(),
                    fontsize=9, color="#555", va="bottom"),
           ax2.text(t[len(t) // 40], (hmax + TRACE_HI_M) / 2,
                    "above the 2021 flood: beyond anything measured",
                    fontsize=8.5, color="#b5532a", va="center")]
    marker = ax2.axvline(t[0], color="#c0504d", lw=1.4)
    # The opening clip's label (1.3.0), in the strip between the map and the hydrograph;
    # blank for the full film.
    clip_txt = axr.text(0.98, 0.275, "", fontsize=16, weight="bold", va="center", ha="right",
                        color=COL_WATER)

    # The caption, reflowed to its box and sized ONCE for its longest form (with the
    # beyond-the-record paragraphs), so it never changes size or re-wraps between frames.
    # The hand line breaks in build_text are joined; paragraph breaks are kept.
    def reflow(block, fs):
        paras = [" ".join(p.split()) for p in block.strip("\n").split("\n\n")]
        return "\n\n".join("\n".join(_wrap(p, fs, 0.33 * FRAME_W)) for p in paras)
    box_h = 0.60 * FRAME_H
    fs_c = CAPTION_PT_MAX
    while fs_c > 7.0:
        full = reflow(caption, fs_c) + "\n\n" + reflow(caption_beyond, fs_c)
        if (full.count("\n") + 1) * 1.4 * fs_c * FRAME_DPI / 72.0 <= box_h:
            break
        fs_c -= 0.25
    cap_now = reflow(caption, fs_c)
    cap_over = cap_now + "\n\n" + reflow(caption_beyond, fs_c)
    # 1.4.0: the caption is drawn line by line in runs, so its colour words carry the map's
    # colours. Redrawn only when the month crosses into or out of the beyond-the-record state.
    import re as _re                                            # noqa: PLC0415
    keys = [("Blue: open water.", COL_WATER, False), ("Yellow: wet floor.", FILM_COL_FLOOR_TEXT, False),
            ("pale orange", "#c0632a", False), (head_b, "#b5532a", True)]
    lh_c = 1.4 * fs_c * FRAME_DPI / 72.0 / (0.60 * FRAME_H)
    cap_art = []

    def draw_caption(block, base):
        for a_ in cap_art:
            a_.remove()
        cap_art.clear()
        cols = [(base, False)] * len(block)
        for key, colour, bold in keys:
            for m_ in _re.finditer(r"\s+".join(map(_re.escape, key.split())), block):
                cols[m_.start():m_.end()] = [(colour, bold)] * (m_.end() - m_.start())
        pos = 0
        for n_l, line in enumerate(block.split("\n")):
            x_, j = 0.0, 0
            while j < len(line):
                k_ = j
                while k_ < len(line) and cols[pos + k_] == cols[pos + j]:
                    k_ += 1
                colour, bold = cols[pos + j]
                run = line[j:k_]
                cap_art.append(axt.text(x_, 1.0 - n_l * lh_c, run, fontsize=fs_c, va="top",
                                        ha="left", color=colour,
                                        weight="bold" if bold else "normal"))
                x_ += _text_w(run, fs_c, bold) / (0.33 * FRAME_W)
                j = k_
            pos += len(line) + 1
    cap_state = [None]

    def frame(i):
        over = lvl[i] > hmax
        im.set_data(paint(i))
        marker.set_xdata([t[i], t[i]])
        if cap_state[0] != over:
            draw_caption(cap_over if over else cap_now, "#7a2e0e" if over else "#222")
            cap_state[0] = over
        for s_, v in zip(slots, (fmt_mname[i], fmt_year[i], fmt_level[i], fmt_ow[i], fmt_wf[i])):
            s_.set_text(v)
        over_txt.set_text(beyond if over else "")
        fig.canvas.draw()
        return even(np.asarray(fig.canvas.buffer_rgba())[..., :3])

    n = len(level)
    n_sim = FILM_FPS + n + 2 * FILM_FPS            # a second on the first month, two on the last
    # Per frame, for the sound track: None under a slide (the ambient bed), else the
    # index of the month the frame shows (the tone).
    sim_marks = [0] * FILM_FPS + list(range(n)) + [n - 1] * (2 * FILM_FPS)
    entries, pos = [], 0                           # (title, start frame) for the index
    for title_, fr in seg_before:
        entries.append((title_, pos)); pos += len(fr)
    entries.append((f"The film: {t[0].year}–{t[-1].year}", pos)); pos += n_sim
    for title_, fr in seg_after:
        entries.append((title_, pos)); pos += len(fr)
    idx, opening, clip = [], [], []
    if presentation:
        # 1.3.0: the opening, a short title page and the last decade, comes before the
        # title-and-contents page. Its length is known before the contents are drawn.
        opening = open_title_slide()
        c0 = int(np.searchsorted(np.array(months), FILM_OPEN_CLIP_START))
        clip = list(range(c0, n))
        n_open = len(opening) + len(clip) + 2 * FILM_FPS
        # The title page goes first; its length is fixed by its words and the number of
        # entries, not by the times it lists, so the times are known before it is drawn.
        shift = len(index_slide(entries))
        entries = [(e[0], e[1] + n_open + shift) for e in entries]
        idx = index_slide(entries)
        if len(idx) != shift:
            raise RuntimeError("the title page changed length between probe and render")
        entries[:0] = [("Opening", 0),
                       (f"{FILM_OPEN_CLIP_LABEL}: {t[c0].year}–{t[-1].year}", len(opening)),
                       ("Title and contents", n_open)]
    open_marks = ([None] * len(opening) + clip + [clip[-1]] * (2 * FILM_FPS)) if clip else []
    marks = (open_marks + [None] * len(idx) + [None] * sum(len(f) for _, f in seg_before)
             + sim_marks + [None] * sum(len(f) for _, f in seg_after))

    target = OUT_47_PRESENTATION if presentation else OUT_47_FILM
    quality = FILM_QUALITY_PRESENTATION if presentation else FILM_QUALITY_FULL
    import tempfile                                           # noqa: PLC0415
    import time as _time                                      # noqa: PLC0415
    with tempfile.TemporaryDirectory() as td:
        silent = Path(td) / "silent.mp4" if presentation else target
        w = imageio.get_writer(silent, fps=FILM_FPS, codec="libx264", quality=quality,
                               macro_block_size=None)
        n_written = 0

        def put(arrs):
            nonlocal n_written
            for a_ in arrs:
                w.append_data(a_)
                n_written += 1
        if clip:
            put(opening)
            clip_txt.set_text(FILM_OPEN_CLIP_LABEL)
            # 1.4.0: the hydrograph zooms to the clip's years; the eras are off-screen
            ax2.set_xlim(t[clip[0]], t[-1])
            for e_ in era:
                e_.set_visible(False)
            for i in clip:
                a = frame(i)
                put([a])
            put([a] * (2 * FILM_FPS))
            clip_txt.set_text("")
            ax2.set_xlim(*xlim_full)
            for e_ in era:
                e_.set_visible(True)
        put(idx)
        for _, fr in seg_before:
            put(fr)
        a = frame(0)
        put([a] * FILM_FPS)
        t0 = _time.time()
        for i in range(n):
            a = frame(i)
            put([a])
            if still_month is not None and level["month"].iloc[i] == still_month:
                still[still_month] = a
            if i % 25 == 0 or i == n - 1:
                progress(i + 1, n, t[i].strftime("%Y-%m"), started=t0)
        print(flush=True)
        put([a] * (2 * FILM_FPS))
        plt.close(fig)
        for _, fr in seg_after:
            put(fr)
        w.close()
        if n_written != len(marks):
            raise RuntimeError(f"wrote {n_written} frames against a plan of {len(marks)}")
        if presentation:
            wav, meta = Path(td) / "track.wav", Path(td) / "chapters.txt"
            if FILM_SOUND_TRACK == "classic":
                track = sound_track(marks, lvl, aw + af, hmax)
            else:
                track = sound_track_warren(marks, lvl, aw, af, months, hmax, arrivals,
                                           wet_pan=wet_pan)
            write_wav(wav, track)
            write_chapters(meta, entries, n_written)
            mux(silent, wav, target, meta)
            for title_, f0 in entries:
                info(f"{_fmt_time(f0):>6}  {title_}")
    saved(target.name, f"{n_written / FILM_FPS:.0f} s, {n_written} frames, quality {quality}"
          + (f", with sound and {len(entries)} chapters" if presentation else ""))
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
    plot_free_run(level, stats)
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
    thumbs = load_thumbs(floor)
    text = build_text(feed, floor_ha, thumbs, stats)
    write_caveats(*text, feed, arrivals)

    if no_film:
        info("--no-film: the CSVs and the text only")
        done("47")
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
    done("47")
    return rc


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="The century hindcast film (T-39, D-178)")
    ap.add_argument("--no-film", action="store_true",
                    help="write the CSVs and the frame text, render nothing")
    ap.add_argument("--check-phase27", metavar="CSV", default=None,
                    help="also report this run against a phase 27 *_hindcast_monthly.csv")
    args = ap.parse_args()
    sys.exit(main(no_film=args.no_film, check_phase27=args.check_phase27))
